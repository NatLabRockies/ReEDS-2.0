"""
@author: pbrown
@date: 20201104 14:47
* Adapted from input_processing/R/writesupplycurves.R
* All supply curves are organized by BA
"""

#%%########
### IMPORTS

import pandas as pd
import numpy as np
import os
import argparse

################
#%% FIXED INPUTS
### Number of bins used for everything other than wind and PV
numbins_other = 5
### Rounding precision
decimals = 7
### spur_cutoff [$/MW]: Cutoff for spur line costs; clip cost for sites with larger costs
spur_cutoff = 1e7

#%%##############
### FUNCTIONS ###

def concat_sc_point_gid(x):
    return x.astype(str).str.cat(sep=',')


def get_bin(df_in, bin_num, bin_method='equal_cap_cut', bin_col='supply_curve_cost_per_mw'):
    df = df_in.copy()
    ser = df[bin_col]
    #If we have less than or equal unique points than bin_num, we simply group the points with the same values.
    if ser.unique().size <= bin_num:
        bin_ser = ser.rank(method='dense')
        df['bin'] = bin_ser.values
    elif bin_method == 'equal_cap_man':
        #using a manual method instead of pd.cut because i want the first bin to contain the
        #first sc point regardless, even if its capacity is more than the capacity of the bin,
        #and likewise for other bins, so i don't skip any bins.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        cumcaps = df['capacity'].cumsum().tolist()
        totcap = df['capacity'].sum()
        vals = df[bin_col].tolist()
        bins = []
        curbin = 1
        for i,v in enumerate(vals):
            bins.append(curbin)
            if cumcaps[i] >= totcap*curbin/bin_num:
                curbin += 1
        df['bin'] = bins
        df = df.reindex(index=orig_index) #we need the same index ordering for apply to work.
    elif bin_method == 'equal_cap_cut':
        #Use pandas.cut with cumulative capacity in each class. This will assume equal capacity bins
        #to bin the data.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        df['cum_cap'] = df['capacity'].cumsum()
        bin_ser = pd.cut(df['cum_cap'], bin_num, labels=False)
        bin_ser = bin_ser.rank(method='dense')
        df['bin'] = bin_ser.values
        df = df.reindex(index=orig_index) #we need the same index ordering for apply to work.
    df['bin'] = df['bin'].astype(int)
    return df


def agg_supplycurve(
        scpath, numbins_tech, reeds_path, sw,
        bin_method='equal_cap_cut', bin_col='supply_curve_cost_per_mw',
        spur_cutoff=1e7):
    """
    """
    ### Get inputs
    dfin = pd.read_csv(scpath)

    ### If using aggregated regions, map to the new regions
    if int(sw.GSw_AggregateRegions):
        ### Get the rb-to-aggreg map
        hierarchy = pd.read_csv(
            os.path.join(inputs_case,'hierarchy.csv')
            ).rename(columns={'*r':'r'}).set_index('r')
        r2aggreg = hierarchy.aggreg.copy()
        ### Map old regions to new aggregated regions
        dfin.region = dfin.region.map(r2aggreg)
    ### Assign bins
    dfin = dfin.groupby(['region','class'], sort=False).apply(
        get_bin, numbins_tech, bin_method, bin_col
    ).reset_index(drop=True).sort_values('sc_point_gid')
    ###### Aggregate values by (region,class,bin)
    ### Define the aggregation settings
    distance_cols = [c for c in dfin if c in ['dist_km','reinforcement_dist_km','dist_mi','dist_to_coast']]
    cost_adder_cols = [c for c in dfin if c in ['trans_adder_per_MW', 'capital_adder_per_MW']]

    ### cost and distance are weighted averages, with capacity as the weighting factor
    def wm(x):
        out = np.average(
            x,
            weights=(
                dfin.loc[x.index, 'capacity']) if dfin.loc[x.index, 'capacity'].sum() > 0
                else 0)
        return out

    aggs = {
        **{
            'capacity': 'sum',
            'supply_curve_cost_per_mw': wm,
            'sc_point_gid': concat_sc_point_gid,
        },
        **dict(zip(distance_cols + cost_adder_cols, [wm]*len(distance_cols + cost_adder_cols))),
    }
    ### Aggregate it
    dfout = dfin.groupby(['region','class','bin']).agg(aggs)
    ### Clip negative costs and costs above cutoff
    ### TODO: Figure out why there are negative costs
    dfout.supply_curve_cost_per_mw = dfout.supply_curve_cost_per_mw.clip(
        lower=0, upper=spur_cutoff)

    return dfin, dfout

#%%

def main(reeds_path, inputs_case, write=True, **kwargs):
    #%% Inputs from switches
    sw = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
    ### Overwrite switches with keyword arguments
    for kw, arg in kwargs.items():
        sw[kw] = arg

    drscen = sw.drscen
    endyear = int(sw.endyear)
    geosupplycurve = sw.geosupplycurve
    pshsupplycurve = sw.pshsupplycurve
    GSw_Siting = {
        'upv':sw.GSw_SitingUPV,
        'wind-ons':sw.GSw_SitingWindOns,
        'wind-ofs':sw.GSw_SitingWindOfs}
    numbins = {'upv':int(sw.numbins_upv), 
               'wind-ons':int(sw.numbins_windons), 
               'wind-ofs':int(sw.numbins_windofs), 
               'csp':int(sw.numbins_csp)} 

    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, names=['scalar','value','comment'], index_col='scalar')['value']
    
    val_r = pd.read_csv(
            os.path.join(inputs_case, 'val_r.csv'), squeeze=True, header=None).tolist()

    #%%##############
    ### PROCEDURE ###

    ### Set inputs and supplycurvedata paths for convenience
    inputsdir = os.path.join(reeds_path,'inputs','')
    scdir = os.path.join(inputsdir,'supplycurvedata','')
    stordir = os.path.join(inputsdir, 'storagedata','')

    #%% Read in tech-subset-table.csv to determine number of csp configurations
    tech_subset_table = pd.read_csv(os.path.join(inputsdir, "tech-subset-table.csv"))
    csp_configs = tech_subset_table.loc[
        (tech_subset_table.CSP== 'YES' ) & (tech_subset_table.STORAGE == 'YES')].shape[0]

    # Read in dollar year conversions for RSC data
    dollaryear = pd.read_csv(os.path.join(scdir, 'dollaryear.csv'))
    deflator = pd.read_csv(os.path.join(inputsdir,"deflator.csv"))
    deflator.columns = ["Dollar.Year","Deflator"]
    deflate = dollaryear.merge(deflator,on="Dollar.Year",how="left").set_index('Scenario')['Deflator']

    #%% Load the existing RSC capacity (PV plants, wind, and CSP)
    rsc_wsc = pd.read_csv(os.path.join(inputs_case,'rsc_wsc.csv'))
    rsc_wsc = rsc_wsc.loc[rsc_wsc['r'].isin(val_r)]
    for j,row in rsc_wsc.iterrows():
        # Group CSP tech
        if row['i'] in ['csp-ws']:
            rsc_wsc.loc[j,'i'] = 'csp'
    rsc_wsc = rsc_wsc.groupby(['r','i']).sum().reset_index()
    rsc_wsc.i = rsc_wsc.i.str.lower()
    rsc_wsc.columns = ['r','tech','exist']
    ### Change the units
    rsc_wsc.exist /= 1000
    tout = rsc_wsc.copy()

    ###########################
    #%% Load supply curve files

    #%% Wind
    windin, wind = {}, {}
    for s in ['ons','ofs']:
        windin[s], wind[s] = agg_supplycurve(
            scpath=os.path.join(
                reeds_path,'inputs','supplycurvedata',
                f'wind-{s}_supply_curve-{GSw_Siting[f"wind-{s}"]}.csv'),
            numbins_tech=numbins[f'wind-{s}'], reeds_path=reeds_path,
            sw=sw, spur_cutoff=spur_cutoff,
        )
        # Aggregate regions will have already filtered to the aggregated regions
        if not int(sw.GSw_AggregateRegions):
            windin[s] = windin[s].loc[windin[s]['region'].isin(val_r)]
            wind[s] = wind[s][wind[s].index.get_level_values('region').isin(val_r)]

        # Convert dollar year
        cost_adder_cols = [c for c in wind[s] if c in ['trans_adder_per_MW', 'capital_adder_per_MW']]
        wind[s][['supply_curve_cost_per_mw'] + cost_adder_cols] *= deflate[f'wind-{s}_supply_curve']
        # Subtract GSw_TransIntraCost (converted to $/MW) to avoid double-counting
        for c in ['supply_curve_cost_per_mw', 'trans_adder_per_MW']:
            if c in wind[s]:
                wind[s][c] = (wind[s][c] - float(sw['GSw_TransIntraCost'])*1e3).clip(lower=0)


    #For onshore, save the trans vs cap components, and then concatenate them below just
    #before outputting rsc_combined.csv
    cost_components_wind = wind['ons'][['trans_adder_per_MW', 'capital_adder_per_MW']].round(2).reset_index()
    cost_components_wind = cost_components_wind.rename(columns={
        'region':'r','class':'*i','bin':'rscbin','trans_adder_per_MW':'cost_trans',
        'capital_adder_per_MW':'cost_cap'})
    cost_components_wind['*i'] = 'wind-ons_' + cost_components_wind['*i'].astype(str)
    cost_components_wind['rscbin'] = 'bin' + cost_components_wind['rscbin'].astype(str)
    cost_components_wind = pd.melt(
        cost_components_wind, id_vars=['*i','r','rscbin'], var_name='sc_cat', value_name= 'value')

    windall = (
        pd.concat(wind, axis=0)
        .reset_index(level=0).rename(columns={'level_0':'type'})
        .reset_index()
    )
    ### Normalize formatting
    windall['type'] = 'wind-' + windall['type']
    windall.supply_curve_cost_per_mw = windall.supply_curve_cost_per_mw.round(2)
    windall['class'] = 'class' + windall['class'].astype(str)
    windall['bin'] = 'wsc' + windall['bin'].astype(str)
    ### Pivot, with bins in long format
    windcost = (
        windall.pivot(index=['region','class','type'], columns='bin', values='supply_curve_cost_per_mw')
        .fillna(0).reset_index())
    windcap = (
        windall.pivot(index=['region','class','type'], columns='bin', values='capacity')
        .fillna(0).reset_index())
    ### Write the onshore sc_point_gid-to-(region,class,bin) map for writecapdat.py
    gid2irb_wind = wind['ons']['sc_point_gid'].reset_index().rename(columns={'region':'r','bin':'rscbin'})
    gid2irb_wind['i'] = 'wind-ons_' + gid2irb_wind['class'].astype(str)
    ## Unpack the sc_point_gid's
    out = []
    for i, row in gid2irb_wind.iterrows():
        for sc_point_gid in row.sc_point_gid.split(','):
            out.append([sc_point_gid, row.i, row.r, row.rscbin])
    gid2irb_wind = (
        pd.DataFrame(out, columns=['sc_point_gid','i','r','rscbin'])
        .astype({'sc_point_gid':int})
        .set_index('sc_point_gid'))

    #%% Write the onshore wind exogenous (pre-tstart) capacity
    ### Get the site-level builds
    dfwindexog = pd.read_csv(
        os.path.join(
            reeds_path,'inputs','capacitydata',
            f'wind-ons_exog_cap_{sw.GSw_SitingWindOns}.csv')
    ).rename(columns={'*tech':'*i','region':'r','year':'t','capacity':'MW'})
    dfwindexog = dfwindexog.loc[dfwindexog['r'].isin(val_r)]
    ### Aggregate if necessary
    if int(sw.GSw_AggregateRegions):
        ### Get the rb-to-aggreg map
        hierarchy = pd.read_csv(
            os.path.join(inputs_case,'hierarchy.csv')
            ).rename(columns={'*r':'r'}).set_index('r')
        r2aggreg = hierarchy.aggreg.copy()
        ### Map to the new regions
        dfwindexog.r = dfwindexog.r.map(r2aggreg)
    ### Get the rscbin, then sum by (i,r,rscbin,t)
    dfwindexog['rscbin'] = 'bin'+dfwindexog.sc_point_gid.map(gid2irb_wind.rscbin).astype(int).astype(str)
    dfwindexog = dfwindexog.groupby(['*i','r','rscbin','t']).MW.sum()

    #%% PV
    upvin, upv = agg_supplycurve(
        scpath=os.path.join(
            reeds_path,'inputs','supplycurvedata',
            f"upv_supply_curve-{GSw_Siting['upv']}.csv"),
        numbins_tech=numbins['upv'], reeds_path=reeds_path,
        sw=sw, spur_cutoff=spur_cutoff,
    )
    ## Aggregated regions are already filtered
    if not int(sw.GSw_AggregateRegions):
        upvin = upvin.loc[upvin['region'].isin(val_r)]
        upv = upv[upv.index.get_level_values('region').isin(val_r)]

    # Convert dollar year
    cost_adder_cols = [c for c in upv if c in ['trans_adder_per_MW', 'capital_adder_per_MW']]
    upv[['supply_curve_cost_per_mw'] + cost_adder_cols] *= deflate['UPV_supply_curves_cost_2018']
    # Subtract GSw_TransIntraCost (converted to $/MW) to avoid double-counting
    for c in ['supply_curve_cost_per_mw', 'trans_adder_per_MW']:
        upv[c] = (upv[c] - float(sw['GSw_TransIntraCost'])*1e3).clip(lower=0)

    #Similar to wind, save the trans vs cap components and then concatenate them below just
    #before outputting rsc_combined.csv
    cost_components_upv = upv[['trans_adder_per_MW', 'capital_adder_per_MW']].round(2).reset_index()
    cost_components_upv = cost_components_upv.rename(columns={
        'region':'r','class':'*i','bin':'rscbin','trans_adder_per_MW':'cost_trans',
        'capital_adder_per_MW':'cost_cap'})
    cost_components_upv['*i'] = 'upv_' + cost_components_upv['*i'].astype(str)
    cost_components_upv['rscbin'] = 'bin' + cost_components_upv['rscbin'].astype(str)
    cost_components_upv = pd.melt(
        cost_components_upv, id_vars=['*i','r','rscbin'], var_name='sc_cat', value_name= 'value')

    ### Write the upv sc_point_gid-to-(region,class,bin) map
    gid2irb_upv = upv['sc_point_gid'].reset_index().rename(columns={'region':'r','bin':'rscbin'})
    gid2irb_upv['i'] = 'upv_' + gid2irb_upv['class'].astype(str)
    ## Unpack the sc_point_gid's
    out = []
    for i, row in gid2irb_upv.iterrows():
        for sc_point_gid in row.sc_point_gid.split(','):
            out.append([sc_point_gid, row.i, row.r, row.rscbin])
    gid2irb_upv = (
        pd.DataFrame(out, columns=['sc_point_gid','i','r','rscbin'])
        .astype({'sc_point_gid':int})
        .set_index('sc_point_gid'))
    
    ### Normalize formatting
    upv = upv.reset_index()
    upv['class'] = 'class' + upv['class'].astype(str)
    upv['bin'] = 'upvsc' + upv['bin'].astype(str)
    ### Pivot, with bins in long format
    upvcost = (
        upv.pivot(columns='bin',values='supply_curve_cost_per_mw',index=['region','class'])
        .fillna(0)
        ### reV spur line and reinforcement costs are now in per MW-AC terms, so removing the 
        ### correction term that was applied. 
    ).reset_index()
    upvcap = (
        upv.pivot(columns='bin',values='capacity',index=['region','class'])
        .fillna(0).reset_index())
    
    #%% Write the upv exogenous (pre-tstart) capacity
    ### Get the site-level builds
    dfupvexog = pd.read_csv(
        os.path.join(
            reeds_path,'inputs','capacitydata',
            f'upv_exog_cap_{sw.GSw_SitingUPV}.csv')
    ).rename(columns={'*tech':'*i','region':'r','year':'t','capacity':'MW'})
    dfupvexog = dfupvexog.loc[dfupvexog['r'].isin(val_r)]
    ### Aggregate if necessary
    if int(sw.GSw_AggregateRegions):
        ### Map to the new regions (hierarchy loaded with wind above)
        dfupvexog.r = dfupvexog.r.map(r2aggreg)
    ### Get the rscbin, then sum by (i,r,rscbin,t)
    dfupvexog['rscbin'] = 'bin'+dfupvexog.sc_point_gid.map(gid2irb_upv.rscbin).astype(int).astype(str)
    dfupvexog = dfupvexog.groupby(['*i','r','rscbin','t']).MW.sum()
    
    #%% CSP
    cspin, csp = agg_supplycurve(
        scpath=os.path.join(
            reeds_path,'inputs','supplycurvedata',
            "csp_supply_curve-reference.csv"),
        numbins_tech=numbins['csp'], reeds_path=reeds_path,
        sw=sw, spur_cutoff=spur_cutoff,
    )

    ## Aggregated regions are already filtered
    if not int(sw.GSw_AggregateRegions):
        cspin = cspin.loc[cspin['region'].isin(val_r)]
        csp = csp[csp.index.get_level_values('region').isin(val_r)]

    ## Adjust dollar year and subtract GSw_TransIntraCost
    for c in ['supply_curve_cost_per_mw']:
        csp[c] *= deflate['CSP_supply_curves_cost_2018']
        csp[c] = (csp[c] - float(sw['GSw_TransIntraCost'])*1e3).clip(lower=0)

    ### Normalize formatting
    csp = csp.reset_index()
    csp['class'] = 'class' + csp['class'].astype(str)
    csp['bin'] = 'cspsc' + csp['bin'].astype(str)
    ### Pivot, with bins in long format
    cspcost = (
        csp.pivot(columns='bin',values='supply_curve_cost_per_mw',index=['region','class'])
        .fillna(0)
    ).reset_index()
    cspcap = (
        csp.pivot(columns='bin',values='capacity',index=['region','class'])
        .fillna(0).reset_index())
    
    ## Duplicate the CSP supply curve for each CSP configuration
    cspcap = (
        pd.concat({'csp{}'.format(i): cspcap for i in range(1,csp_configs+1)}, axis=0)
        .reset_index(level=0).rename(columns={'level_0':'tech'}).reset_index(drop=True))
    cspcost = (
        pd.concat({'csp{}'.format(i): cspcost for i in range(1,csp_configs+1)}, axis=0)
        .reset_index(level=0).rename(columns={'level_0':'tech'}).reset_index(drop=True))

    #%% Get supply-curve data for postprocessing
    spurout = pd.concat([
        (
            wind['ons'].reset_index()
            .assign(i='wind-ons_'+wind['ons'].reset_index()['class'].astype(str))
            .assign(rscbin='bin'+wind['ons'].reset_index()['bin'].astype(str))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_km','reinforcement_dist_km','supply_curve_cost_per_mw']]
        ),
        (
            upv
            .assign(i='upv_'+upv['class'].astype(str).str.strip('class'))
            .assign(rscbin='bin'+upv['bin'].str.strip('upvsc'))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_km','reinforcement_dist_km','supply_curve_cost_per_mw']]
        ),
        (
            csp
            .assign(i='csp_'+csp['class'].astype(str).str.strip('class'))
            .assign(rscbin='bin'+csp['bin'].str.strip('cspsc'))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_km','reinforcement_dist_km','supply_curve_cost_per_mw']]
        ),
    ]).round(2)

    ### Get spur-line and reinforcement distances if using in annual trans investment limit
    poi_distance = spurout.loc[spurout.r.isin(val_r)].copy()
    ## Duplicate CSP entries for each CSP system design
    poi_distance_csp = poi_distance.loc[poi_distance.i.str.startswith('csp')].copy()
    poi_distance_csp_broadcasted = pd.concat([
        poi_distance_csp.assign(i=poi_distance_csp.i.str.replace('csp_',f'csp{i}_'))
        for i in range(1,csp_configs+1)
    ], axis=0)
    poi_distance_out = (
        pd.concat([
            poi_distance.loc[~poi_distance.i.str.startswith('csp')],
            poi_distance_csp_broadcasted
        ], axis=0)
        ## Reformat to save for GAMS
        .rename(columns={'i':'*i'}).set_index(['*i','r','rscbin'])
    )
    ## Convert to miles
    distance_spur = (
        poi_distance_out.dist_km.rename('miles') / 1.609).round(3)
    distance_reinforcement = (
        poi_distance_out.reinforcement_dist_km.rename('miles') / 1.609).round(3)

    #%% Using 2018 version for everything else
    dupvcost = pd.read_csv(scdir + 'DUPV_supply_curves_cost_2018.csv')
    dupvcap = pd.read_csv(scdir + 'DUPV_supply_curves_capacity_2018.csv')
    
    dupvcost = dupvcost.loc[dupvcost['Unnamed: 0'].isin(val_r)]
    dupvcap = dupvcap.loc[dupvcap['Unnamed: 0'].isin(val_r)]

    # Convert dollar years
    dupvcost[dupvcost.select_dtypes(include=['number']).columns] *= deflate['DUPV_supply_curves_cost_2018']
    
    #%% Reformat the supply curve dataframes
    ### Non-wind bins
    bins = list(range(1, numbins_other + 1))
    ### Wind bins (flexible)
    bins_wind = list(range(1, max(numbins['wind-ons'], numbins['wind-ofs']) + 1))
    ### UPV bins (flexible)
    bins_upv = list(range(1, numbins['upv'] + 1))
    ### CSP bins (flexible)
    bins_csp = list(range(1, numbins['csp'] + 1))

    rcolnames = {'Unnamed: 0':'r', 'region':'r', 'Unnamed: 1':'class'}

    dupvcap.rename(
        columns={**rcolnames, **{'dupvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
    upvcap.rename(
        columns={**rcolnames, **{'upvsc{}'.format(i): 'bin{}'.format(i) for i in bins_upv}}, inplace=True)
    cspcap.rename(
        columns={**rcolnames, **{'cspsc{}'.format(i): 'bin{}'.format(i) for i in bins_csp}}, inplace=True)

    dupvcost.rename(
        columns={**rcolnames, **{'dupvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
    upvcost.rename(
        columns={**rcolnames, **{'upvsc{}'.format(i): 'bin{}'.format(i) for i in bins_upv}}, inplace=True)
    cspcost.rename(
        columns={**rcolnames, **{'cspsc{}'.format(i): 'bin{}'.format(i) for i in bins_csp}}, inplace=True)    

    ### Note: wind capacity and costs also differentiate between 'class' and 'tech'
    windcap.rename(
        columns={
            **{'region':'r', 'type':'tech',
            'Unnamed: 0':'r', 'Unnamed: 1':'class', 'Unnamed 2': 'tech'},
            **{'wsc{}'.format(i): 'bin{}'.format(i) for i in bins_wind}},
        inplace=True)
    windcost.rename(
        columns={
            **{'region':'r', 'type':'tech',
            'Unnamed: 0':'r', 'Unnamed: 1':'class', 'Unnamed 2': 'tech'},
            **{'wsc{}'.format(i): 'bin{}'.format(i) for i in bins_wind}},
        inplace=True)

    dupvcap['tech'] = 'dupv'
    upvcap['tech'] = 'upv'

    dupvcost['tech'] = 'dupv'
    upvcost['tech'] = 'upv'

    #%% Combine the supply curves
    alloutcap = pd.concat([windcap, cspcap, upvcap, dupvcap])
    alloutcost = (
        pd.concat([windcost, cspcost, upvcost, dupvcost])
        .set_index(['r','class','tech'])
        .reset_index())

    alloutcap['class'] = alloutcap['class'].map(lambda x: x.lstrip('cspclass'))
    alloutcap['class'] = alloutcap['class'].map(lambda x: x.lstrip('class'))
    alloutcost['class'] = alloutcost['class'].map(lambda x: x.lstrip('cspclass'))
    alloutcost['class'] = alloutcost['class'].map(lambda x: x.lstrip('class'))

    alloutcap['var'] = 'cap'
    alloutcost['var'] = 'cost'

    alloutcap['class'] = 'class' + alloutcap['class'].astype(str)
    t1 = alloutcap.pivot(
        index=['r','tech','var'], columns='class',
        values=[c for c in alloutcap.columns if c.startswith('bin')]).reset_index()
    ### Concat the multi-level column names to a single level
    t1.columns = ['_'.join(i).strip('_') for i in t1.columns.tolist()]

    t2 = t1.merge(tout, on=['r','tech'], how='outer').fillna(0)

    #%% Subset to single-tech curves
    wndonst2 = t2.loc[t2.tech=="wind-ons"].copy()
    wndofst2 = t2.loc[t2.tech=="wind-ofs"].copy()
    cspt2 = t2.loc[t2.tech.isin(['csp{}'.format(i) for i in range(1,csp_configs+1)])]
    upvt2 = t2.loc[t2.tech=="upv"].copy()
    dupvt2 = t2.loc[t2.tech=="dupv"].copy()

    #%% Get the combined outputs
    outcap = pd.concat([wndonst2, wndofst2, upvt2, dupvt2, cspt2])

    moutcap = pd.melt(outcap, id_vars=['r','tech','var'])
    moutcap = moutcap.loc[~moutcap.variable.isin(['exist','temp'])].copy()

    moutcap['bin'] = moutcap.variable.map(lambda x: x.split('_')[0])
    moutcap['class'] = moutcap.variable.map(lambda x: x.split('_')[1].lstrip('class'))
    outcols = ['r','tech','var','bin','class','value']
    moutcap = moutcap.loc[moutcap.value != 0, outcols].copy()

    outcapfin = moutcap.pivot(
        index=['r','tech','var','class'], columns='bin', values='value'
    ).fillna(0).reset_index()

    allout = pd.concat([outcapfin, alloutcost])
    allout['tech'] = allout['tech'] + '_' + allout['class'].astype(str)


    #%%###############
    ### Hydropower ###

    ### Adding hydro costs and capacity separate as it does not
    ### require the calculations to reduce capacity by existing amounts.
    ### Goal  here is to acquire a data frame that matches the format
    ### of alloutm so that we can simply stack the two.

    hydcap = pd.read_csv(scdir + 'hydcap.csv')[['tech','class'] + val_r]
    hydcost = pd.read_csv(scdir + 'hydcost.csv')[['tech','class'] + val_r]

    hydcap = (pd.melt(hydcap, id_vars=['tech','class'])
            .set_index(['tech','class','variable']).sort_index())
    hydcost = pd.melt(hydcost, id_vars=['tech','class'])

    # prescribed hydund in p33 does not have enough rsc_dat
    # capacity to meet prescribed amount - check with WC
    if 'p18' in val_r:
        hydcap.loc[('hydUND','hydclass1','p18'),'value'] += 27
        hydcap.loc[('hydNPND','hydclass1','p18'),'value'] += 3
    if 'p110' in val_r:
        hydcap.loc[('hydNPND','hydclass1','p110'),'value'] += 58
    if 'p33' in val_r:
        hydcap.loc[('hydUND','hydclass1','p33'),'value'] = 5
    hydcap = hydcap.reset_index()

    # Convert dollar year
    hydcost[hydcost.select_dtypes(include=['number']).columns] *= deflate['hydcost']

    hydcap['var'] = 'cap'
    hydcost['var'] = 'cost'

    hyddat = pd.concat([hydcap, hydcost])
    hyddat['bin'] = hyddat['class'].map(lambda x: x.replace('hydclass','bin'))
    hyddat['class'] = hyddat['class'].map(lambda x: x.replace('hydclass',''))

    hyddat.rename(columns={'variable':'r', 'bin':'variable'}, inplace=True)
    hyddat = hyddat[['tech','r','value','var','variable']].fillna(0)


    #%%#########################
    ### Pumped Storage Hydropower###
    # Input processing currently assumes that cost data in CSV file is in 2004$

    psh_cap = pd.read_csv(scdir + 'PSH_supply_curves_capacity_{}.csv'.format(pshsupplycurve))
    psh_cost = pd.read_csv(scdir + 'PSH_supply_curves_cost_{}.csv'.format(pshsupplycurve))
    psh_cap.rename(columns={psh_cap.columns[0]:'r'}, inplace=True)
    psh_cost.rename(columns={psh_cost.columns[0]:'r'}, inplace=True)
    psh_durs = pd.read_csv(stordir + 'PSH_supply_curves_durations.csv', header=0)
    
    # Filter for valid regions
    psh_cap = psh_cap.loc[psh_cap['r'].isin(val_r)]
    psh_cap = psh_cap.loc[psh_cap['r'].isin(val_r)]

    psh_cap = pd.melt(psh_cap, id_vars=['r'])
    psh_cost = pd.melt(psh_cost, id_vars=['r'])

    # Convert dollar year
    psh_cost[psh_cost.select_dtypes(include=['number']).columns] *= deflate['PHScostn']

    psh_cap['var'] = 'cap'
    psh_cost['var'] = 'cost'

    psh_out = pd.concat([psh_cap, psh_cost]).fillna(0)
    psh_out['tech'] = 'pumped-hydro'
    psh_out['variable'] = psh_out.variable.map(lambda x: x.replace('pshclass','bin'))
    psh_out = psh_out[hyddat.columns].copy()

    # Select storage duration correponding to the supply curve
    psh_dur_out = psh_durs[psh_durs['pshsupplycurve']==pshsupplycurve]['duration']

    #%%####################
    ### Demand Response ###

    dr_rsc = pd.read_csv(
        os.path.join(inputsdir,'demand_response','dr_rsc_{}.csv'.format(drscen)))
    
    # Filter for valid regions
    dr_rsc = dr_rsc.loc[dr_rsc['r'].isin(val_r)]

    
    dr_rsc['var'] = dr_rsc['var'].str.lower()
    # Convert dollar year
    dr_rsc.loc[dr_rsc['var']=='Cost', 'value'] *= deflate['dr_rsc_{}'.format(drscen)]

    # Duplicate or interpolate data for all years between start (assumed 2010) and
    # end year. Currently (as of 05-2021) only DR has yearly supply data
    yrs = pd.DataFrame(list(range(2010, endyear+1)), columns=['year'])
    yrs['tmp'] = 1

    # Get all years for all parts of data
    tmp = dr_rsc[[c for c in dr_rsc.columns if c not in ['year','value']]].drop_duplicates()
    tmp['tmp'] = 1
    tmp = pd.merge(tmp, yrs, on='tmp').drop('tmp',axis=1)
    tmp = pd.merge(tmp, dr_rsc, how='outer', on=list(tmp.columns))
    # Interpolate between years that exist using a linear spline interpolation
    # extrapolating any values at the beginning or end as required
    # Include all years here then filter later to get spline correct if data
    # covers more than the years modeled
    def grouper(group):
        return group.interpolate(
            limit_direction='both', method='slinear', fill_value='extrapolate')

    dr_rsc = (
        tmp
        .groupby([c for c in tmp.columns if c not in ['value','year']])
        .apply(grouper)
    )
    dr_rsc = (
        dr_rsc[dr_rsc.year.isin(yrs.year)]
        ### Reorder to match other supply curves
        [['tech','r','var','bin','year','value']]
        ### Rename the first column so GAMS reads the header as a comment
        .rename(columns={'tech':'*tech','var':'sc_cat','bin':'rscbin','year':'t'})
    )
    # Ensure no values are < 0
    dr_rsc['value'].clip(lower=0, inplace=True)


    #%%#######################
    ### Combine everything ###
    ### Stack the final versions
    alloutm = pd.melt(allout, id_vars=['r','tech','var'])
    alloutm = alloutm.loc[alloutm.variable != 'class'].copy()
    alloutm = pd.concat([alloutm, hyddat, psh_out])

    ### Drop the (cap,cost) entries with nan cost
    alloutm = (
        alloutm
        .pivot(index=['r','tech','variable'], columns=['var'], values=['value'])
        .dropna()['value']
        .reset_index()
        .melt(id_vars=['r','tech','variable'])
        [['tech','r','var','variable','value']]
        ### Rename the first column so GAMS reads the header as a comment
        .rename(columns={'tech':'*i','var':'sc_cat','variable':'rscbin'})
        .astype({'value':float})
        ### Drop 0 values
        .replace({'value':{0.:np.nan}}).dropna()
        .round(5)
    )

    ### Combine with cost components
    alloutm = pd.concat([alloutm,cost_components_wind,cost_components_upv], ignore_index=True)

    #%%############
    ### Biomass ###

    # Note that biomass is currently being handled directly in b_inputs.gms

    #%%###############
    ### Geothermal ###

    geo_disc_rate = pd.read_csv(
        os.path.join(inputsdir,'geothermal',f'geo_discovery_{sw.geodiscov}.csv'))
    
    geo_discovery_factor = pd.read_csv(
        os.path.join(inputsdir,'geothermal','geo_discovery_factor.csv')
    )
    geo_discovery_factor = geo_discovery_factor.loc[
        geo_discovery_factor.r.isin(val_r)].copy()
    geo_rsc = pd.read_csv(
        os.path.join(inputsdir,'geothermal','geo_rsc_{}.csv'.format(geosupplycurve)),
        header=0)
    
    # Filter by valid regions
    geo_rsc = geo_rsc.loc[geo_rsc['r'].isin(val_r)]
    
    # Convert dollar year
    geo_rsc.sc_cat = geo_rsc.sc_cat.str.lower()
    geo_rsc.loc[geo_rsc.sc_cat=='cost', 'value'] *= deflate['geo_rsc_{}'.format(geosupplycurve)]

    ##################################
    #%% Spur lines (disaggregated) ###
    ###### NOTE: In the upv and wind-ons supply curves from reV, a single site (indicated by
    ### a single sc_point_gid value) can be mapped to different BAs for upv and wind, depending
    ### on the distribution of tech-specific developable area within the reV cell.
    ### That could presumably lead to errors for site-specific spur lines indexed by sc_point_gid.
    ### Here we re-map each upv/wind-ons supply curve point based on the no-exclusions
    ### transmission table. But note that that will throw off the CF profiles, which are
    ### calculated as weighted averages over the available gid's within the reV cell.
    ### So it would be better to do this correction in hourlize (and even better to make the
    ### fix upstream in reV.)

    ### Get the fips-to-r map
    county_map = pd.read_csv(
        os.path.join(reeds_path,'hourlize','inputs','resource','county_map.csv')
    )
    county_map.cnty_fips = county_map.cnty_fips.map(lambda x: '{:0>5}'.format(x))
    fips2rb = county_map.set_index('cnty_fips').reeds_ba
    ### Aggregate if necessary
    if int(sw.GSw_AggregateRegions):
        fips2rb = fips2rb.map(r2aggreg)

    ###### Spur line costs
    spursites = pd.read_csv(
        os.path.join(inputsdir,'supplycurvedata','spurline_cost_1.csv')
    )
    ### Deflate to ReEDS dollar year
    spursites.trans_cap_cost_per_mw *= deflate['spur']
    spursites = (
        spursites
        .assign(x='i'+spursites['sc_point_gid'].astype(str))
        .assign(cnty_fips=(
            ### Format cnty_fips as 5-digit string left-filled with zeros
            spursites.cnty_fips.astype(str).map('{:0>5}'.format)
            ### Update Oglala Lakota county, SD
            .map(lambda x: {'46113':'46102'}.get(x,x)))
        )
        ### drop sites with too high of spur-line cost
        .loc[spursites.trans_cap_cost_per_mw < spur_cutoff]
        .round(2)
    )
    ### Map sites to rb's
    spursites['rb'] = spursites.cnty_fips.map(fips2rb)

    ### Filter for valid regions
    spursites.dropna(subset=['rb'], inplace=True)
    if not int(sw.GSw_AggregateRegions):
        spursites = spursites.loc[spursites['rb'].isin(val_r)]

    ###### Site maps
    ### UPV
    sitemap_upv = (
        upvin
        .assign(i='upv_'+upvin['class'].astype(str))
        .assign(rscbin='bin'+upvin['bin'].astype(str))
        .assign(x='i'+upvin['sc_point_gid'].astype(str))
    )
    sitemap_upv = (
        sitemap_upv
        ### Assign rb's based on the no-exclusions transmission table
        .assign(r=sitemap_upv.x.map(spursites.set_index('x').rb))
        [['i','r','rscbin','x']]
        .rename(columns={'i':'*i'})
    )
    ### wind-ons
    sitemap_windons = (
        windin['ons']
        .assign(i='wind-ons_'+windin['ons']['class'].astype(str))
        .assign(rscbin='bin'+windin['ons']['bin'].astype(str))
        .assign(x='i'+windin['ons']['sc_point_gid'].astype(str))
    )
    sitemap_windons = (
        sitemap_windons
        ### Assign rb's based on the no-exclusions transmission table
        .assign(r=sitemap_windons.x.map(spursites.set_index('x').rb))
        [['i','r','rscbin','x']]
        .rename(columns={'i':'*i'})
    )
    ### Combine, then only keep sites that show up in both supply curve and spur-line cost tables
    spurline_sitemap = pd.concat([sitemap_upv,sitemap_windons], ignore_index=True)
    spurline_sitemap = spurline_sitemap.loc[spurline_sitemap.x.isin(spursites.x.values)].copy()
    spursites = spursites.loc[spursites.x.isin(spurline_sitemap.x.values)].copy()

    ### Add mapping from sc_point_gid to bin for reeds_to_rev.py
    site_bin_map = pd.concat([
        windin['ons'].assign(tech='wind-ons')[['tech','sc_point_gid','bin']],
        windin['ofs'].assign(tech='wind-ofs')[['tech','sc_point_gid','bin']],
        upvin.assign(tech='upv')[['tech','sc_point_gid','bin']]
    ], ignore_index=True)

    #%%######################
    ### Write the outputs ###
    if write:
        ## Everything
        alloutm.to_csv(os.path.join(inputs_case, 'rsc_combined.csv'), index=False, header=True)
        ## Wind
        dfwindexog.round(3).to_csv(os.path.join(inputs_case,'wind-ons_exog_cap.csv'))
        ## UPV
        dfupvexog.round(3).to_csv(os.path.join(inputs_case,'upv_exog_cap.csv'))
        ## Geothermal
        geo_disc_rate.round(decimals).to_csv(os.path.join(inputs_case, 'geo_discovery_rate.csv'), index=False)
        geo_discovery_factor.round(decimals).to_csv(os.path.join(inputs_case, 'geo_discovery_factor.csv'), index=False)
        geo_rsc.round(decimals).to_csv(os.path.join(inputs_case, 'geo_rsc.csv'), index=False)
        ## DR
        dr_rsc.to_csv(inputs_case + 'rsc_dr.csv', index=False, header=True)
        ## Hybrids
        spursites[['x','trans_cap_cost_per_mw']].rename(columns={'x':'*x'}).to_csv(
            os.path.join(inputs_case,'spurline_cost.csv'), index=False)
        spursites['x'].to_csv(os.path.join(inputs_case,'x.csv'), index=False, header=False)
        spurline_sitemap.to_csv(
            os.path.join(inputs_case,'spurline_sitemap.csv'), index=False)
        spurline_sitemap[['x','r']].rename(columns={'x':'*x'}).drop_duplicates().to_csv(
            os.path.join(inputs_case,'x_r.csv'), index=False)
        ## Bin mapping
        site_bin_map.to_csv(os.path.join(inputs_case,'site_bin_map.csv'), index=False)
        ## Spurline and reinforcement distances and costs
        spurout.to_csv(os.path.join(inputs_case,'spur_parameters.csv'), index=False)
        distance_spur.to_csv(os.path.join(inputs_case,'distance_spur.csv'))
        distance_reinforcement.to_csv(os.path.join(inputs_case,'distance_reinforcement.csv'))
        ## Supply-Curve-Specific PSH Duration
        psh_dur_out.to_csv(os.path.join(inputs_case, 'psh_sc_duration.csv'), index=False, header=False)

    return alloutm

#%%##############
### PROCEDURE ###

if __name__ == '__main__':
    ### Time the operation of this script
    from ticker import toc, makelog
    import datetime
    tic = datetime.datetime.now()

    ### Parse arguments
    parser = argparse.ArgumentParser(description='Format and supply curves')
    parser.add_argument('reeds_path', help='path to ReEDS directory')
    parser.add_argument('inputs_case', help='path to inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = os.path.join(args.inputs_case, '')

    # #%% Testing inputs
    # reeds_path = os.path.expanduser('~/github2/ReEDS-2.0')
    # inputs_case = os.path.join(
    #     reeds_path,'runs','v20220807_spurM0_ERCOT_agg1','inputs_case')

    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    main(reeds_path=reeds_path, inputs_case=inputs_case)

    toc(tic=tic, year=0, process='input_processing/writesupplycurves.py',
        path=os.path.join(inputs_case,'..'))
    print('writesupplycurves.py completed successfully')
