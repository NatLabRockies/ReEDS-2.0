# -*- coding: utf-8 -*-
"""
@author: pbrown
@date: 20200812 11:56

Inputs
------

Outputs
-------

Notes
-----
Copied from ReEDS-1.0:
* PTS 04/25/14
    * POL37 is a warming scenario consistent with GHG stabilization at 3.7 W/m2.
    POL45 is the same but at 4.5 W/m2. Both are climate sensitivity of 3.
    * POL37 is an RCP3.7 (stabilization at 3.7W/m2 of radiative forcing by 2100) scenario
    * POL45 is an RCP4.5 (stabilization at 4.5W/m2 of radiative forcing by 2100) scenario
    * both include temperature changes and carbon caps consistent with that scenario
    (IGSM and GCAM-derived)
    * both POL scenarios override other CO2 caps (even if CO2switch is OFF).
* PTS 04/25/14
    * CS3REF and CS6REF are scenarios with no carbon signal, so lots of warming.
    The CS# is the climate sensitivity in degrees of warming per doubling of
    GHG concentration (from preindustrial levels).
    * CS3REF and CS6REF are no-policy (lots of warming) scenarios, with climate
    sensitivities of 3 and 6 degree increase for a doubling of emissions
* PTS 04/25/14
    * all inputs (temperature, carbon cap targets) are derived from IGSM-CAM and GCAM scenarios.
* SMC 08/18/14
    * New scenarios added based on CMIP5 climate data. These three scenarios include
    temperature impacts on load, generation, and transmission as well as water availability
    impacts on thermal cooling.  There are no changes to hydropower water availability.
    * MODNONE entails moderate warming and no changes to precipitation (water availability).
    * HOTWET entails significant warming and largely increased precipitation (water availability).
    * HOTDRY entails significant warming and largely decreased precipitation (water availability).
* YS 04/18/17
    * CIRA2.0 & NEWS Scenarios: Used data from CMIP5 Climate models, with a combination of
    different Representative Concentration Pathway (RCP)
    * Climate models for CIRA2.0: CanESM2, CCSM4, GISS-E2-R, HadGEM2-ES, MIROC5
    (HadGEM shows most climate impacts while GISS shows least)
    * Climate models for NEWS: HadGEM2-ES, GFDL-ESM2M, IPSL-CM5A, MIROC-ESM-CHEM,NorESM1-M
    * RCP Definition: four (2.6, 4.5, 6.0, 8.5 W/m2) greenhouse gas concentration
    (not emissions) trajectories adopted by IPCC AR5; 8.5 indicates super warm scenarios
    and 4.5 is a moderate warming scenario
    * Data includes temperature, heating/cooling degree days (HDDCDD) for calculating
    change in load, water availability & distribution adjustment factors,
    and hydro power adjustment factors
    * For CIRA2.0 work, two methods to calculate HDDCDD data:
    AT indicates using absolute temperature, and HI indicates DD data are based on heat index
    and temperature, and are adjusted for humidity. AT method was used for CIRA2.0 work

Sources
-------
Method derived from:
[1] Sullivan, P.; Colman, J.; Kalendra, E. "Predicting the response of electricity load to
climate change". Technical Report, National Renewable Energy Laboratory,
NREL/TP-6A20-64297. https://www.nrel.gov/docs/fy15osti/64297.pdf
"""

###########
#%% IMPORTS
import gdxpds
import pandas as pd
import numpy as np
import os
import argparse
import gzip, pickle
from forecast import forecast
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()


################
#%% FIXED INPUTS
verbose = 2
### Set rounding precision
decimals = 5
### Link between peak-timeslices and parent-timeslices (in case we add more peak-slices)
slicetree = {'h17': 'h3',}

###################
#%% ARGUMENT INPUTS

parser = argparse.ArgumentParser(description="Format and write climate inputs")
parser.add_argument('reeds_path', help='ReEDS directory')
parser.add_argument('inputs_case', help='output directory')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing ###
# reeds_path = os.path.expanduser('~/github/ReEDS-2.0/')
# inputs_case = os.path.expanduser(
#     '~/github/ReEDS-2.0/runs/v20201208_beyond2050_Climate2100step5/inputs_case/')
# reeds_path = os.getcwd()
# inputs_case = os.path.join('runs','a5_ercot_seq','inputs_case')

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

print('Starting climateprep.py')

#%% Inputs from switches
sw = pd.read_csv(os.path.join(inputs_case, 'switches.csv'), 
                 header=None, index_col=0).squeeze('columns')

climatescen = sw.climatescen
climateloc = sw.climateloc
GSw_ClimateWater = int(sw.GSw_ClimateWater)
GSw_ClimateHydro = int(sw.GSw_ClimateHydro)
GSw_ClimateDemand = int(sw.GSw_ClimateDemand)
GSw_EFS1_AllYearLoad = sw.GSw_EFS1_AllYearLoad
endyear = int(sw.endyear)
GSw_ClimateStartYear = int(sw.GSw_ClimateStartYear)


#%% TEMPORARY: Don't allow climate impacts to be used with EFS load until we work out the bugs
if GSw_ClimateDemand and (GSw_EFS1_AllYearLoad != 'historic'):
    raise NotImplementedError("Climate impacts aren't yet compatible with EFS load")

if climateloc.startswith('inputs'):
    climateloc = os.path.join(reeds_path, *(os.path.split(climateloc)))
else:
    pass

### Get the directory for climate inputs
climatedir = os.path.join(climateloc, climatescen)

### Get modeled years
modelyears = pd.read_csv(os.path.join(inputs_case,'modeledyears.csv')).columns.astype(int).tolist()
allyears = list(range(2010, endyear+1))
### Get reeds_data_year
reeds_data_year = 2012

### Get valid regions
val_r = pd.read_csv(os.path.join(inputs_case, 'val_r.csv'), 
                    header=None).squeeze('columns').tolist()

### Get some other fixed inputs
distloss = pd.read_csv(os.path.join(inputs_case, 'scalars.csv'), 
                       header=None, usecols=[0,1], index_col=0
                       ).squeeze('columns')['distloss']

#############
#%% FUNCTIONS

#############################
### Cooling water, hydropower

def readwrite(
    infile, climatedir=climatedir, inputs_case=inputs_case, decimals=decimals, endyear=endyear):
    """
    Load modifiers, interpolate to all years, write GAMS-readable csv.
    """
    ### Indicate which indices to use
    index = {
        'UnappWaterMult': ['wst','r','szn'],
        'UnappWaterSeaAnnDistr': ['wst','r','szn'],
        'UnappWaterMultAnn': ['wst','r'],
        'hydadjann': ['r'],
        'hydadjsea': ['r','szn'],
    }
    ### Load the climate scenario data
    dfin = pd.read_csv(os.path.join(climatedir, infile+'.csv'))
    
    # Filter for valid regions
    dfin = dfin.loc[dfin['r'].isin(val_r)]
    
    ### Put in GAMS-readable format
    dfout = pd.pivot_table(dfin, values='Value', index=index[infile], columns=['t'])
    ### If data end before endyear, create a column for endyear so we can forward-fill to it
    lastdatayear = max([int(y) for y in dfout.columns])
    if endyear > lastdatayear:
        dfout[endyear] = dfout.loc[:,lastdatayear]
    ### If data start after 2010, add a column for 2010
    if (2010 not in dfout.columns) and all(dfout.columns.values > 2010):
        ### For UnappWaterSeaAnnDistr we give the new values directly rather than as a ratio,
        ### so we backfill with the earliest available data
        if infile == 'UnappWaterSeaAnnDistr':
            dfout[2010] = dfout.iloc[:,0]
        ### Otherwise we fill with 1 (i.e. no change). Note that since we interpolate to the
        ### next value, the years between 2010 and the first year with data will not be 1.
        else:
            dfout[2010] = 1.
        ### Move 2010 column to the front of the dataframe
        dfout.sort_index(axis=1, inplace=True)
    ### Interpolate to missing years
    dfinterp = (
        dfout
        ### Switch column names from integer years to timestamps
        .rename(columns={c: pd.Timestamp(str(c)) for c in dfout.columns})
        ### Add empty columns at year-starts between existing data (mean doesn't do anything)
        .resample('YS', axis=1).mean()
        ### Interpolate linearly to fill the new columns
        .T.interpolate('linear').T
    )
    dfout = (
        ### Switch back to integer year column names
        dfinterp.rename(columns={c: c.year for c in dfinterp.columns})
        ### Drop extra data after the model end year
        .loc[:,:endyear]
    )
    ### Write it to output folder
    dfout.round(decimals).to_csv(os.path.join(inputs_case, 'climate_'+infile+'.csv'))
    return dfout

################
#%% Demand delta

def calculate_load_delta(
        reeds_path=reeds_path, inputs_case=inputs_case,
        climatedir=climatedir, decimals=decimals):
    """
    """
    #%% Load the heating and cooling slopes (curently same for all climate scenarios)
    slopes = {}
    for ddtype in ['hdd','cdd']:
        slopes[ddtype] = pd.read_csv(
            os.path.join(climateloc,'{}Slopes.csv'.format({'hdd':'Heat','cdd':'Cool'}[ddtype])),
            index_col=0)
        slopes[ddtype].index = slopes[ddtype].index.map(lambda x: 'p{}'.format(x)).rename('r')
        slopes[ddtype].columns.name = 'h'
        slopes[ddtype] = slopes[ddtype][slopes[ddtype].index.isin(val_r)]
    dfslopes = pd.concat(slopes, axis=0)
    dfslopes.rename(columns={c:'h{}'.format(c) for c in dfslopes.columns}, inplace=True)
    dfslopes.index.set_names(['ddtype','r'],inplace=True)
    dfslopes = dfslopes.stack()

    ### Load the heating/cooling-degree-days data (specific to climate scenario)
    hddcdd = pd.read_csv(os.path.join(climateloc,climatescen,'HDDCDD.csv')).fillna(0.)
    
    # Filter by valid regions
    hddcdd = hddcdd.loc[hddcdd['r'].isin(val_r)]
    
    hddcdd = pd.pivot_table(hddcdd, values='Value', index=['ddtype','r','szn'], columns=['t'])
    ### Interpolate to odd years
    hddcdd = (
        hddcdd
        .rename(columns={c: pd.Timestamp(str(c)) for c in hddcdd.columns})
        .resample('YS', axis=1).mean()
        ### Interpolate only works row-wise, so transpose, interpolate, and transpose again
        .T.interpolate('linear').T
    )
    hddcdd = hddcdd.rename(columns={c: c.year for c in hddcdd.columns})
    ### Calculate change from initial year
    hddcdd_delta = hddcdd.subtract(hddcdd[2010], axis='index')

    #%% Calculate hours per season
    #TODO: make compatible with hourly ReEDS
    hhours = pd.read_csv(
        os.path.join(reeds_path,'inputs','numhours.csv'),
        header=0, names=['h','hours'], index_col='h', squeeze=True)
    ### Get timeslice-to-season mapper
    h_dt_szn = (
        pd.read_csv(
            os.path.join(reeds_path,'inputs', 'variability','h_dt_szn.csv'),
            index_col='hour')
        .replace({'winter':'wint','spring':'spri','summer':'summ'})
        .rename(columns={'season':'szn','year':'t7',})
    )
    h2szn = h_dt_szn[['h','szn']].drop_duplicates().set_index('h')['szn'].to_dict()
    ## Add the peak timeslices
    for peakslice in slicetree:
        parentslice = slicetree[peakslice]
        h2szn[peakslice] = h2szn[parentslice]
    sznhours = pd.Series(index=hhours.index.map(h2szn), data=hhours.values)
    szndays = (sznhours.groupby(sznhours.index).sum()/24).astype(int).to_dict()

    #%% Normalize degree days by days per season
    hddcdd_delta_norm = (
        hddcdd_delta.T / hddcdd_delta.index.get_level_values('szn').map(szndays)).T

    ### Switch index from szn to h to match slopes,
    ### but drop peaks (e.g. h17) since not in slopes
    szn2h = pd.DataFrame(
        index=pd.Series(h2szn).drop(slicetree.keys()).values,
        data=pd.Series(h2szn).drop(slicetree.keys()).index, columns=['h'])
    hddcdd_delta_norm = (
        hddcdd_delta_norm
        .merge(szn2h, left_on='szn', right_index=True, how='left')
        .reset_index().drop('szn',axis=1)
        .groupby(['ddtype','r','h']).mean()
    )

    #%% Get delta load by multiplying HDD/CDD by slopes
    load_delta = (
        (hddcdd_delta_norm.T * dfslopes).T
        ### Sum over hdd and cdd, drop ddtype index
        .reset_index().drop('ddtype',axis=1).groupby(['r','h']).sum()
    )

    #%% Write the load delta at timeslice-resolution
    load_delta.round(decimals).to_csv(
        os.path.join(inputs_case, 'climate_loaddelta_timeslice.csv'))
    return load_delta

#################
#%% Calculate and write demand files
def write_load_files(
        reeds_path=reeds_path, inputs_case=inputs_case, decimals=decimals,
        modelyears=modelyears, endyear=endyear, allyears=allyears,
        GSw_ClimateStartYear=GSw_ClimateStartYear,
        GSw_EFS1_AllYearLoad=GSw_EFS1_AllYearLoad,):
    """
    """
    ###### Load the necessary inputs
    #%% Get the hour-mapper
    h_dt_szn = (
        pd.read_csv(os.path.join(reeds_path,'inputs', 'variability','h_dt_szn.csv'), index_col='hour')
        .replace({'winter':'wint','spring':'spri','summer':'summ'})
        .rename(columns={'season':'szn','year':'t7',})
    )

    #%% Get numhours
    #TODO: remove numhours
    numhours = pd.read_csv(
        os.path.join(inputs_case,'numhours.csv'),
        header=0, names=['h','numhours'], index_col='h', squeeze=True)

    #%% Get the load-growth factors
    load_multiplier_r = pd.read_csv(
        os.path.join(inputs_case,'load_multiplier_r.csv'), index_col=['r','t'], squeeze=True,
    ).unstack('t').loc[val_r]

    #%% If running beyond the last year of data in load_multiplier.csv we need to project to
    ### future years. That's done in forecast.py, but forecast.py also needs to project the
    ### outputs of the present script. So we need to duplicate the projection here (not ideal).
    lastdatayear = max(load_multiplier_r.columns)
    if endyear > lastdatayear:
        futurefiles = pd.read_csv(
            os.path.join(reeds_path, 'inputs', 'userinput', 'futurefiles.csv'),
            dtype={'header':'category', 'ignore':int, 'wide':int,
                'year_col':str, 'fix_cols':str,
                'clip_min':str, 'clip_max':str,}
        ).set_index('filename')
        filename = 'load_multiplier.csv'
        clip_min, clip_max = futurefiles.loc[filename,['clip_min','clip_max']]
        clip_min = (None if clip_min.lower()=='none' else int(clip_min))
        clip_max = (None if clip_max.lower()=='none' else int(clip_max))
        load_multiplier_r = forecast(
            dfi=load_multiplier_r, lastdatayear=lastdatayear,
            addyears=list(range(lastdatayear+1, endyear+1)),
            forecast_fit=futurefiles.loc[filename,'forecast_fit'],
            clip_min=clip_min, clip_max=clip_max)

    #%% Get the hourly demand
    from LDC_prep import read_file
    ### Default
    if GSw_EFS1_AllYearLoad == 'historic':
        load_hourly_base = pd.read_hdf(
            os.path.join(reeds_path,'inputs','loaddata','historic_load_hourly.h5')
        )[val_r]
    ### EFS - only available for a single year, so concatenate it
    else:
        load_hourly_base = read_file(
            os.path.join(reeds_path,'inputs','loaddata', f'{GSw_EFS1_AllYearLoad}_load_hourly'),
            index_columns=2)[val_r]
    load_hourly_base.columns.name = 'r'

    #%% Get the climate-induced load delta
    load_delta = pd.read_csv(
        os.path.join(inputs_case,'climate_loaddelta_timeslice.csv'),
        index_col=['r','h'])
    load_delta.rename(columns={i:int(i) for i in load_delta.columns}, inplace=True)
    ### Get the lastdatayear from the climate projection.
    ### If endyear > lastdatayear we need to project load_delta_hourly forward.
    lastdatayear = max(load_delta.columns)
    if endyear > lastdatayear:
        ### futurefiles will already be loaded from above
        filename = 'climate_loaddelta_timeslice.csv'
        clip_min, clip_max = futurefiles.loc[filename,['clip_min','clip_max']]
        clip_min = (None if clip_min.lower()=='none' else int(clip_min))
        clip_max = (None if clip_max.lower()=='none' else int(clip_max))
        load_delta = forecast(
            dfi=load_delta, lastdatayear=lastdatayear,
            addyears=list(range(lastdatayear+1, endyear+1)),
            forecast_fit=futurefiles.loc[filename,'forecast_fit'],
            clip_min=clip_min, clip_max=clip_max)
    ### Switch from timeslice to hour index
    load_delta_hourly = h_dt_szn[['h']].merge(
        load_delta.unstack('r').loc[:,:endyear], left_on='h', right_index=True
    ).drop('h',axis=1).sort_index()
    ### Clean up the column names
    load_delta_hourly.columns = (
        pd.MultiIndex.from_tuples(load_delta_hourly.columns)
        .rename('t',level=0).rename('r',level=1)
    )

    #%% Make some additional inputs
    ### Make the Augur io path
    augurpath = os.path.join(inputs_case,'..','ReEDS_Augur','augur_data')
    os.makedirs(augurpath, exist_ok=True)
    ### Get the one-year hours for default
    if GSw_EFS1_AllYearLoad == 'historic':
        hours_oneyear = h_dt_szn.loc[h_dt_szn.t7==reeds_data_year].index.tolist()
    ### EFS only uses one year so it always uses hours 1-8760
    else:
        hours_oneyear = range(1,8761)

    #%%### Make the output dicts and loop over years
    dict_sznpeak_allyear, dict_load_allyear, dict_hpeak_allyear = {}, {}, {}
    ### Make an additional dict for EFS (no effect otherwise)
    dict_load_hourlybyyear = {}
    for t in allyears:
        ### Get un-modified load, averaged by (year,timeslice)
        load_hourly_timeslice_mean = (
            load_hourly_base
            ## Get the (year,timeslice) info and take mean
            .merge(h_dt_szn[['t7','h']], left_index=True, right_index=True)
            .groupby(['h','t7']).mean()
            ## Broadcast back to hourly resolution
            .merge(h_dt_szn[['h','t7']], left_index=True, right_on=['h','t7'])
            .drop(['h','t7'], axis=1)
            .sort_index(axis=0)
        )
        ### Get the ratio between hourly load and (year,timeslice) mean load
        load_hourly_ratio = load_hourly_base / load_hourly_timeslice_mean

        ##### Apply climate deltas
        #### Note that we scale the hourly load delta by the ratio between
        #### the hourly load and (year,timeslice) load, thus smoothing out
        #### the edges of the climate deltas and accentuating the peaks
        ### Default: Also apply load-growth multipliers
        if GSw_EFS1_AllYearLoad == 'historic':
            load_out = (
                load_hourly_base * load_multiplier_r.loc[val_r,t]
                + (load_delta_hourly[t] * load_hourly_ratio
                    if t >= GSw_ClimateStartYear else 0))
        ### EFS: Read from the year directly
        else:
            load_out = (
                load_hourly_base.loc[t]
                + (load_delta_hourly[t].loc[hours_oneyear] * load_hourly_ratio.loc[hours_oneyear]
                    if t >= GSw_ClimateStartYear else 0))
        load_out.index.name = 'hour'
        #%% Downselect to single year (no effect for EFS)
        ### load_oneyear is in the same format for EFS and default
        load_oneyear = load_out.loc[hours_oneyear].copy()
        ### Add season and timeslice
        load_oneyear['szn'] = load_oneyear.index.map(h_dt_szn.szn)
        load_oneyear['h'] = load_oneyear.index.map(h_dt_szn.h)

        #%% Get the peak load by (region,season) and store it
        dict_sznpeak_allyear[t] = (
            load_oneyear.drop('h',axis=1).groupby('szn').max()
            .stack().reorder_levels(['r','szn']))

        #%% Get the mean load by timeslice
        load_timeslice = (
            load_oneyear.drop('szn',axis=1).groupby('h').mean()
            ### Add peak row(s) (e.g. h17), which we'll fill below
            .append(pd.DataFrame(index=list(slicetree.keys()))))
        load_timeslice.index.name = 'h'
        load_timeslice.columns.name = 'r'
        for r in load_timeslice.columns:
            for peakslice in slicetree:
                parentslice = slicetree[peakslice]
                ### Take peak (e.g. h17) from the top hours of parent (e.g. h3)
                load_timeslice.loc[peakslice,r] = (
                    load_oneyear.loc[load_oneyear.h==parentslice,r]
                    .nlargest(numhours[peakslice]).mean())
                ### Take parent value from the remaining hours in parent
                ### Note that numhours already includes the correct number of
                ### hours in parent; e.g. for h3, 268 - 40 = 228
                load_timeslice.loc[parentslice,r] = (
                    load_oneyear.loc[load_oneyear.h==parentslice,r]
                    .nsmallest(numhours[parentslice]).mean()
                )
        #%% Store it
        dict_load_allyear[t] = load_timeslice.stack().reorder_levels(['r','h'])

        #%% Get the peak load by (region,timeslice)
        peak_timeslice = (
            load_oneyear.drop('szn',axis=1).groupby('h').max()
            ### Add peak row(s), which we'll fill below
            .append(pd.DataFrame(index=list(slicetree.keys()))))
        peak_timeslice.index.name = 'h'
        peak_timeslice.columns.name = 'r'
        for r in peak_timeslice.columns:
            for peakslice in slicetree:
                parentslice= slicetree[peakslice]
                ### Take peak from the top hours of parent
                peak_timeslice.loc[peakslice,r] = (
                    load_oneyear.loc[load_oneyear.h==parentslice,r]
                    .nlargest(numhours[peakslice]).max())
                ### Take parent from the remaining hours in parent
                peak_timeslice.loc[parentslice,r] = (
                    load_oneyear.loc[load_oneyear.h==parentslice,r]
                    .nsmallest(numhours[parentslice]).max()
                )
        #%% Store it
        dict_hpeak_allyear[t] = peak_timeslice.stack().reorder_levels(['r','h'])

        #%%### If default, write the 7-year hourly load for Augur,
        ###### with normalization and distribution losses as in LDC_prep.py
        if GSw_EFS1_AllYearLoad == 'historic':
            if t in modelyears:
                ### Get the year label
                load_write = load_out.merge(h_dt_szn['t7'], on='hour')
                ### Get the yearly normalization factor
                load_yearly = load_write.groupby('t7').sum()
                norm = load_yearly.loc[reeds_data_year] / load_yearly
                ### Normalize the load
                load_write = load_write.set_index('t7') * norm
                load_write.index = h_dt_szn.index
                ### Scale up by distribution losses
                load_write /= (1 - distloss)
                ### Write it
                savename = os.path.join(augurpath, 'load_7year_{}.h5'.format(t))
                load_write[val_r].to_hdf(savename, key='data', complevel=4)
                if verbose >= 2:
                    print(os.path.basename(savename))
        ##### Otherwise no normalize, but apply distloss and store for concat
        else:
            load_write = load_out / (1 - distloss)
            dict_load_hourlybyyear[t] = load_write

    #%% Concat and save peak_allyear
    peak_allyear = (
        pd.concat(dict_sznpeak_allyear, axis=0, names=('t','r','szn')).rename('MW')
        .reset_index().rename(columns={'r':'*r'})
        [['*r','szn','t','MW']]
    )
    peak_allyear.round(decimals).to_csv(
        os.path.join(inputs_case, 'peak_szn.csv'), index=False)
    ### Concat and save load_allyear
    load_allyear = pd.concat(dict_load_allyear, axis=1)
    load_allyear.round(decimals).to_csv(os.path.join(inputs_case, 'load_allyear.csv'))
    ### Concat and save h_peak_all
    h_peak_all = pd.concat(dict_hpeak_allyear, axis=1)
    h_peak_all.round(decimals).to_csv(os.path.join(inputs_case, 'peak_h.csv'))
    #%% Concat and save hourly-by-year load file if necessary
    if GSw_EFS1_AllYearLoad != 'historic':
        df_load_hourlybyyear = pd.concat(dict_load_hourlybyyear, axis=0)
        df_load_hourlybyyear.index.set_names(['year','hour'],inplace=True)
        savename = os.path.join(augurpath, 'load_allyears.h5')
        df_load_hourlybyyear.to_hdf(savename, key='data', complevel=4)
        if verbose >= 2:
            print(savename)
    #%% Return for debugging
    return {
        'load_allyear': load_allyear,
        'peak_allyear': peak_allyear,
        'h_peak_all': h_peak_all,
        'load_out_final': load_out,
        'load_write_final': load_write,
    }


#############
#%% PROCEDURE

if GSw_ClimateWater:
    print('Writing annual and seasonal water climate multipliers')
    for infile in ['UnappWaterMult','UnappWaterMultAnn','UnappWaterSeaAnnDistr']:
        readwrite(infile=infile)

if GSw_ClimateHydro:
    print('Writing annual and seasonal hydro climate multipliers')
    for infile in ['hydadjann','hydadjsea']:
        readwrite(infile=infile)

if GSw_ClimateDemand:
    print('Writing climate-induced demand delta')
    calculate_load_delta()
    print('Writing ReEDS and Augur load and peak inputs')
    write_load_files()

if not any([GSw_ClimateWater,GSw_ClimateHydro,GSw_ClimateDemand]):
    print("All climate switches are off. We stopped climate change!")

toc(tic=tic, year=0, process='input_processing/climateprep.py',
    path=os.path.join(inputs_case,'..'))
print('Finished climateprep.py')
