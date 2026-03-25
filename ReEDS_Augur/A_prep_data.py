#%% Notes
"""
This script writes inputs for three other processes:
* B1_osprey.gms (hourly dispatch)
* E_capacity_credit.py (existing and marginal capacity credit)
* run_pras.jl -> ReEDS2PRAS.jl -> PRAS.jl (probabilistic resource adequacy)

The files used by PRAS are:
* In {case}/ReEDS_Augur/augur_data:
    * cap_converter_{year}.csv
    * energy_cap_{year}.csv
    * forced_outage_{year}.csv
    * max_cap_{year}.csv
    * tran_cap_{year}.csv
    * pras_load_{year}.h5
    * pras_vre_gen_{year}.h5
* In {case}/inputs_case:
    * resources.csv
    * tech-subset-table.csv
    * unitdata.csv
    * unitsize.csv
"""

#%% General imports
import gdxpds
import os
import pandas as pd
import numpy as np
### Local imports
import ReEDS_Augur.functions as functions


#%%### Functions
def get_gen_cost(gdxreeds, sw):
    ### Get the emissions rate
    emit_rate = gdxreeds['emit_rate_filt']
    ### Include non-CO2 GHG emissions based on global warming potential if specified
    if int(sw.GSw_AnnualCapCO2e):
        emit_rate_co2e = emit_rate.loc[emit_rate.e=='CO2'].merge(
            emit_rate.loc[emit_rate.e=='CH4'].drop(['e'], axis=1),
            on=['i','v','r'], how='left', suffixes=('','_CH4')
        ).fillna(0)
        emit_rate_co2e.Value += (
            emit_rate_co2e.Value_CH4 * float(sw.GSw_MethaneGWP))
        emit_rate = pd.concat([
            emit_rate_co2e.drop(['Value_CH4'], axis=1),
            emit_rate.loc[emit_rate.e != 'CO2']
        ], axis=0)

    ### Get emissions price
    emit_cost = (
        emit_rate.set_index(['e','i','v','r']).Value
        .multiply(gdxreeds['emissions_price'].set_index(['e','r']).Value)
        .reset_index(level='e', drop=True)
        .dropna()
    )
    ### VOM cost
    vom_cost = gdxreeds['cost_vom_filt'].set_index(['i','v','r']).Value
    ### Fuel cost
    ## Bio
    fuel_price_bio = gdxreeds['repbioprice_filt'].assign(i='biopower').set_index(['i','r']).Value
    ## Fossil gas
    fuel_price_gas = gdxreeds['repgasprice_filt'].set_index('r').Value
    gastechs = (
        gdxreeds['fuel2tech'].loc[gdxreeds['fuel2tech'].f.str.lower()=='naturalgas','i']
        .str.lower().values)
    ### Static
    fuel_price_static = gdxreeds['fuel_price_filt']
    ## Overwrite static gas prices
    fuel_price_static.loc[fuel_price_static.i.isin(gastechs),'Value'] = (
        fuel_price_static.loc[fuel_price_static.i.isin(gastechs),'r'].map(fuel_price_gas)
    )
    ### Combine
    fuel_price = pd.concat([fuel_price_static.set_index(['i','r']).Value, fuel_price_bio])
    fuel_cost = (
        gdxreeds['heat_rate_filt'].set_index(['i','v','r']).Value
        .multiply(fuel_price)
    )
    ### Sum to get full gen cost
    gen_cost = (
        fuel_cost
        .add(emit_cost, fill_value=0)
        .add(vom_cost, fill_value=0)
    )
    return gen_cost


#%%### Procedure
def main(t, casedir):
    #%%### Inputs for debugging
    # t = 2020
    # reeds_path = os.path.expanduser('~/github2/ReEDS-2.0')
    # casedir = os.path.join(reeds_path,'runs','v20230214_PRMaugurM0_Pacific_d7fIrh4_CC_y2012')

    #%%### Get inputs from ReEDS
    gdxreeds = gdxpds.to_dataframes(
        os.path.join(casedir,'ReEDS_Augur','augur_data',f'reeds_data_{t}.gdx'))
    ### Use indices as multiindex
    for key in gdxreeds:
        # try:
        if 'i' in gdxreeds[key]:
            gdxreeds[key].i = gdxreeds[key].i.str.lower()
        if 'ii' in gdxreeds[key]:
            gdxreeds[key].ii = gdxreeds[key].ii.str.lower()
        if 't' in gdxreeds[key]:
            gdxreeds[key].t = gdxreeds[key].t.astype(int)

    #%% Load other inputs from ReEDS
    inputs_case = os.path.join(casedir, 'inputs_case')

    sw = functions.get_switches(casedir)
    sw['t'] = t

    h_dt_szn = pd.read_csv(os.path.join(inputs_case, 'h_dt_szn.csv'))
    hmap_7yr = pd.read_csv(os.path.join(inputs_case, 'hmap_7yr.csv'))
    hmap_7yr['szn'] = h_dt_szn['season'].copy()
    d_szn = pd.read_csv(os.path.join(inputs_case, 'd_szn.csv')).rename(columns={'*d':'d'})

    load = pd.read_hdf(os.path.join(inputs_case, 'load.h5'))

    resources = pd.read_csv(os.path.join(inputs_case, 'resources.csv'))

    recf = pd.read_hdf(os.path.join(inputs_case, 'recf.h5')).astype(np.float32)
    recf.columns = recf.columns.map(
        resources.set_index('resource')[['i','r']].apply(lambda row: tuple(row), axis=1)
    ).rename(('i','r'))

    techs = gdxreeds['i_subsets'].pivot(columns='i_subtech',index='i',values='Value')


    #%%### Set up the output containers and a few other inputs
    gdxout, csvout, h5out =  {}, {}, {}


    #%%### Transmission routes, capacity, and losses
    gdxout['routes'] = gdxreeds['routes_filt']
    gdxout['cap_converter'] = gdxreeds['cap_converter_filt']

    if int(sw.pras_trans_contingency):
        gdxout['trancap'] = gdxreeds['cap_trans_prm']
    else:
        gdxout['trancap'] = gdxreeds['cap_trans_energy']

    gdxout['tranloss'] = gdxreeds['tranloss']


    #%%### Efficiencies and storage parameters
    gdxout['storage_eff'] = gdxreeds['storage_eff_filt']
    gdxout['converter_efficiency_vsc'] = gdxreeds['converter_efficiency_vsc']
    gdxout['duration'] = gdxreeds['storage_duration'].loc[
        gdxreeds['storage_duration'].i.isin(gdxreeds['storage_standalone'].i)].copy()


    #%%### Generation cost
    gen_cost = (
        get_gen_cost(gdxreeds=gdxreeds, sw=sw)
        .dropna().reorder_levels(['i','v','r']).reset_index()
    )
    ### Reset the vintages of all storage units to 'new1' to reduce model size.
    ### Also done below for gdxout['cap'] and gdxout['avail_day'].
    gen_cost.loc[gen_cost.i.isin(gdxreeds['storage_standalone'].i), 'v'] = 'new1'
    gdxout['gen_cost'] = gen_cost.drop_duplicates()


    #%%### Nameplate capacity
    cap_ivr_realvint = (
        gdxreeds['cap_ivrt'].loc[gdxreeds['cap_ivrt'].t==t].drop('t', axis=1)
        .groupby(['i','v','r'], as_index=False).Value.sum()
    )
    ### Reset the vintages of all storage units to 'new1' to reduce model size
    cap_storage_devint = cap_ivr_realvint.loc[
        cap_ivr_realvint.i.isin(gdxreeds['storage_standalone'].i)].copy()
    cap_storage_devint['v'] = 'new1'
    cap_storage_devint = (
        cap_storage_devint.groupby(['i','v','r'], as_index=False).Value.sum())

    def _devint_storage(dfin):
        dfout = pd.concat([
            dfin.loc[~dfin.i.isin(gdxreeds['storage_standalone'].i)],
            cap_storage_devint
        ], axis=0)
        return dfout

    cap_ivr = _devint_storage(cap_ivr_realvint)

    #%% Remove VRE techs (i.e. techs with profiles in recf) and H2 production / DAC
    vretechs_i = resources.i.str.lower().unique()
    cap_nonvre = cap_ivr.loc[~cap_ivr.i.str.lower().isin(vretechs_i)].copy()

    h2dac = techs['CONSUME'].dropna().index
    cap_nonh2dac = cap_ivr.loc[~cap_ivr.i.isin(h2dac)].copy()
    cap_nonvreh2dac = (
        cap_nonvre.loc[~cap_nonvre.i.isin(h2dac)].copy())

    ### Save it for Osprey, which only dispatches non-VRE generation capacity
    gdxout['cap'] = cap_nonvreh2dac

    cap_vre = (
        cap_ivr.loc[cap_ivr.i.str.lower().isin(vretechs_i)]
        .set_index(['i','v','r']).Value.copy()
    )

    #%%### VRE generation, accounting for generation
    ### Apply CF adjustment to capacity (the resulting df is not meaningful but it's only a step
    ### toward the generation df).
    ### Some RE techs, like CSP, don't have cf_adj_t defined in all years,
    ### so fill missing values with 1, then drop rows with missing region (indicating no capacity)
    cf_adj_iv = (
        gdxreeds['cf_adj_t_filt'].loc[gdxreeds['cf_adj_t_filt'].t==t].drop('t', axis=1)
        .set_index(['i','v']).Value
    )
    cap_vre_derated = cap_vre.multiply(cf_adj_iv, fill_value=1).reset_index().dropna()
    if len(cap_vre) != len(cap_vre_derated):
        raise Exception(
            "CF adjustment didn't work; probably missing values in cf_adj_t_filt. "
            f"len(cap_vre) = {len(cap_vre)}; len(cap_vre_derated) = {(len(cap_vre_derated))}."
        )
    cap_vre_derated = cap_vre_derated.groupby(['i','r']).Value.sum()

    ### Multiply derated capacity by CF to get generation
    gen_vre_ir = recf.multiply(cap_vre_derated, axis=1).dropna(axis=1)
    if gen_vre_ir.shape[1] != cap_vre_derated.shape[0]:
        raise Exception("Mismatch between VRE capacity and available CF data")
    ### Aggregate by model zone
    gen_vre_r = gen_vre_ir.copy()
    gen_vre_r = gen_vre_r.groupby(axis=1, level='r').sum()

    ### Store generation by (i,r) for E_capacity_credit.py
    vre_gen_exist = gen_vre_ir.reindex(resources[['i','r']], axis=1).fillna(0)
    vre_gen_exist.columns = resources.resource
    vre_gen_exist.index = h_dt_szn.set_index(['season','year','h','hour']).index
    h5out['vre_gen_exist'] = vre_gen_exist

    ### Store generation by r for PRAS
    h5out['pras_vre_gen'] = vre_gen_exist


    ###### Store marginal CF by (i,r) for E_capacity_credit.py
    ## Use the cf_adj_iv for the latest available vintage
    cf_adj_i = cf_adj_iv.reset_index()
    ## Temporarily reformat the vintage so we can select the last one
    def intify(v):
        try:
            return int(v)
        except ValueError:
            return v
    cf_adj_i.v = (
        cf_adj_i.v.str.replace('new','')
        .map(intify)
        .map(lambda x: x if str(x).startswith('init') else f'new{x:>03}')
    )
    cf_adj_i = (
        cf_adj_i.sort_values(['i','v']).drop_duplicates('i', keep='last')
        .set_index('i').Value
        .reindex(recf.columns.get_level_values('i').unique()).fillna(1)
    )

    ### Multiply [CF] * [CF adjustment] to get marginal CF
    vre_cf_marg = (
        recf.multiply(cf_adj_i, level='i', axis=1)
        .reindex(resources[['i','r']], axis=1)
    )
    vre_cf_marg.columns = resources.resource
    vre_cf_marg.index = h_dt_szn.set_index(['season','year','h','hour']).index
    h5out['vre_cf_marg'] = vre_cf_marg


    #%%### Availability
    avail_filt = gdxreeds['avail_filt']
    ## Reset the vintages of all storage units to 'new1' to reduce model size
    avail_filt.loc[avail_filt.i.isin(gdxreeds['storage_standalone'].i), 'v'] = 'new1'
    avail_filt = avail_filt.drop_duplicates()
    ## Reshape to [allszn, (i,v)]
    avail_ivszn_all = avail_filt.pivot(columns=['i','v'], index='allszn', values='Value')
    ### Only keep values for existing cpacity
    iv = list(cap_nonvre[['i','v']].drop_duplicates().itertuples(index=False, name=None))
    ## avail is only used for gen techs, so filter out H2 production and DAC 
    iv = [x for x in iv if x[0] not in h2dac]
    avail_ivszn = avail_ivszn_all[[c for c in avail_ivszn_all if c in iv]].copy()
    ## In keeping with the formulation of eq_reserve_margin, if running Osprey in PRM mode,
    ## availability is captured via the PRM instead of the gen-specific availability factor.
    ## So set availability to 1 for consistency, UNLESS GSw_PRM_StressOutages == 1.
    if int(sw['osprey_prm']) and not int(sw['GSw_PRM_StressOutages']):
        avail_ivszn.iloc[:,:] = 1
    #%% Broadcast to days
    avail_ivd = avail_ivszn.loc[d_szn.season].copy()
    avail_ivd.index = d_szn.d
    avail_div = avail_ivd.stack(['i','v'])
    gdxout['avail_day'] = avail_div.rename('Value').reset_index()

    ### For H2 production and DAC, include the seasonally-invariant availability in the capacity
    ### Filter out H2 and DAC capacity and report it separately
    cap_prod = cap_nonvre.loc[cap_nonvre.i.isin(h2dac)].set_index(['i','v','r']).Value
    ## Expand it a little to prevent infeasibilities trying to exactly match ReEDS usage
    avail_h2dac = avail_ivszn_all[cap_prod.index.get_level_values('i').unique()].mean() * 1.01
    cap_prod = cap_prod.multiply(avail_h2dac).groupby('r').sum().rename('MW').reset_index()
    gdxout['cap_prod'] = cap_prod


    #%%### Energy budget
    ### Dispatchable hydro and Canadian imports have seasonal MWh budgets; we spread them out
    ### equally over the constituent days
    ### Output is MWh
    hydro_avemw_ivrszn = (
        gdxreeds['cap_hyd_szn_adj_filt'].set_index(['i','allszn','r']).Value
        .multiply(gdxreeds['m_cf_szn_filt'].set_index(['i','v','r','allszn']).Value)
        .multiply(cap_nonvre.set_index(['i','v','r']).Value)
        .dropna()
        .unstack(['i','v','r'])
    )
    ### Do the same for Canadian imports
    ## Get hours per szn (i.e. rep period)
    sznhours = (
        gdxreeds['h_szn'].drop('Value', axis=1)
        .merge(gdxreeds['hours'], on='allh').groupby('allszn').Value.sum())
    ## Make sure the number of hours makes sense
    assert int(np.around(sznhours.sum(), 0)) % 8760 == 0
    ## [MWh] / [h] = [MW] (average)
    can_imports_avemw_rszn = (
        gdxreeds['can_imports_szn_filt'].pivot(index='allszn',columns='r',values='Value')
        .divide(sznhours, axis=0)
    )
    ## Reshape to match
    can_imports_avemw_ivrszn = can_imports_avemw_rszn.copy()
    can_imports_avemw_ivrszn.columns = can_imports_avemw_ivrszn.columns.map(
        lambda x: ('can-imports','init-1',x)
    ).rename(('i','v','r'))
    ### Merge together
    avemw_ivrszn = pd.concat([hydro_avemw_ivrszn, can_imports_avemw_ivrszn], axis=1)
    ### Broadcast to the actual days represented by each szn
    mwh_ivrd = avemw_ivrszn.loc[d_szn.season] * sw['hoursperperiod']
    mwh_ivrd.index = d_szn.d.rename('*d')
    if not mwh_ivrd.empty:
        mwh_divr = mwh_ivrd.stack(['i','v','r']).rename('MWh')
    else:
        mwh_divr = pd.DataFrame(columns=['i','v','r','MWh']).set_index(['i','v','r'])
    ### Store it
    csvout['daily_energy_budget'] = mwh_divr


    #%%### H2 and DAC load
    ### First just make it all inflexible (necessary for PRAS)
    load_h2dac_all_hourly = (
        gdxreeds['prod_filt']
        .groupby(['r','allh']).Value.sum().unstack('r')
        ## Broadcast to hours in timeslice
        .reindex(h_dt_szn.h).fillna(0).reset_index(drop=True)
    )
    ### For Osprey, we split it into flexible and inflexible based on the value of
    ### flex_consume_techs in augur_switches.csv.
    ### Start with flexible load
    load_h2dac_flex_daily = (
        gdxreeds['prod_filt'].loc[
            gdxreeds['prod_filt'].i.str.lower().isin(sw['flex_consume_techs'])]
        .groupby(['r','allh']).Value.sum().unstack('r')
        ## Broadcast to hours in timeslice
        .reindex(h_dt_szn.h).fillna(0)
        ## Convert to days and sum
        .set_index('s'+hmap_7yr.actual_period)
        .groupby(axis=0, level=0).sum()
        ## Convert to long format for Osprey
        .stack('r').rename('MWh').rename_axis(['d','r']).reset_index()
    )
    gdxout['prod_load'] = load_h2dac_flex_daily

    ### Inflexible H2/DAC load gets added to the net load profile below
    load_h2dac_inflex_hourly = (
        gdxreeds['prod_filt'].loc[
            ~gdxreeds['prod_filt'].i.str.lower().isin(sw['flex_consume_techs'])]
        .groupby(['r','allh']).Value.sum().unstack('r')
        ## Broadcast to hours in timeslice
        .reindex(h_dt_szn.h).fillna(0).reset_index(drop=True)
    )


    #%%### Total load and net load
    ### Get Candian exports and add to this solve year's load
    can_exports = (
        gdxreeds['can_exports_h_filt'].pivot(index='allh',columns='r',values='Value')
        .reindex(h_dt_szn.h).reset_index(drop=True)
    )
    load_year = load.loc[t].add(can_exports, fill_value=0)

    ### PRAS doesn't yet handle flexible load, so include all H2/DAC load in the
    ### version we write for PRAS
    if int(sw['pras_include_h2dac']):
        pras_load = load_year.add(load_h2dac_all_hourly, fill_value=0)
    else:
        pras_load = load_year.copy()
    pras_load.index = h_dt_szn.set_index(['season','year','h','hour']).index
    h5out['pras_load'] = pras_load
    ## Include the hourly H2/DAC load for debugging
    h5out['pras_h2dac_load'] = load_h2dac_all_hourly

    ### Store load with the appropriate index for E_capacity_credit.py
    h5out['load'] = load_year.set_index(
        h_dt_szn.set_index(['season','year','h','hour']).index)

    ### If using osprey_prm, scale up by PRM
    if int(sw['osprey_prm']):
        prm = gdxreeds['prm'].pivot(index='t', columns='r', values='Value').loc[t]
    else:
        prm = 0
    ### Net load (only used in Osprey) is load (scaled up by PRM if necessary)
    ### plus inflexible H2/DAC load minus VRE generation
    net_load = (
        (load_year * (1 + prm))
        .add(load_h2dac_inflex_hourly, fill_value=0)
        .subtract(gen_vre_r, fill_value=0)
    )
    ### Add (d,hr) index for Osprey
    index_dhr = pd.concat([d_szn]*sw['hoursperperiod'], axis=0).sort_values('d')
    index_dhr['hr'] = [f'hr{h+1:>03}' for h in range(sw['hoursperperiod'])] * len(d_szn)
    net_load_dhr = net_load.copy()
    net_load_dhr.index  = index_dhr.set_index(['d','hr']).index
    csvout['net_load'] = net_load_dhr


    #%%### Collect some csv's for ReEDS2PRAS
    csvout['cap_converter'] = (
        gdxreeds['cap_converter_filt'].set_index('r').rename(columns={'Value':'MW'}))
    csvout['forced_outage'] = (
        gdxreeds['forced_outage'].set_index('i').rename(columns={'Value':'fraction'}))
    csvout['tran_cap'] = (
        gdxout['trancap'].set_index(['r','rr','trtype']).rename(columns={'Value':'MW'}))
    max_cap = cap_nonh2dac.set_index(['i','v','r']).Value.rename('MW')
    ### Storage energy capacity [MWh] = power capacity [MW] * duration [h]
    energy_cap = (
        cap_storage_devint
        .set_index(['i','v','r']).Value
        .multiply(gdxout['duration'].set_index('i').Value)
        .rename('MWh')
    )
    ## Drop storage with energy or power capacity below the PRAS cutoff
    too_small_storage = list(set(
        energy_cap.loc[energy_cap < sw['storcap_cutoff']].index.tolist()
        + max_cap.loc[energy_cap.index].loc[
            max_cap.loc[energy_cap.index] < sw['storcap_cutoff']].index.tolist(),
    ))
    csvout['energy_cap'] = energy_cap.drop(too_small_storage)
    csvout['max_cap'] = max_cap.drop(too_small_storage)


    #%%### Write it
    #%% .gdx file
    with gdxpds.gdx.GdxFile() as gdxwrite:
        for key in gdxout:
            gdxwrite.append(
                gdxpds.gdx.GdxSymbol(
                    key, gdxpds.gdx.GamsDataType.Parameter,
                    dims=gdxout[key].columns[:-1].tolist(),
                )
            )
            gdxwrite[-1].dataframe = gdxout[key].round(int(sw['decimals']))
        gdxwrite.write(
            os.path.join(casedir, 'ReEDS_Augur', 'augur_data', f'osprey_inputs_{t}.gdx')
        )
    #%% .csv files
    for key in csvout:
        csvout[key].round(int(sw['decimals'])).to_csv(
            os.path.join(casedir,'ReEDS_Augur','augur_data',f'{key}_{t}.csv'),
        )
    #%% .h5 files
    for key in h5out:
        h5out[key].astype(np.float32).to_hdf(
            os.path.join(casedir,'ReEDS_Augur','augur_data',f'{key}_{t}.h5'),
            key='data', complevel=4, mode='w',
        )

    #%%### Return outputs for debugging
    return gdxout, csvout, h5out
