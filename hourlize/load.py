"""
Functions for processing load data for use in ReEDS.
Run using "python run_hourlize.py load"
The output of this script is timestamped as hour-ending, e.g. 12am refers to 11pm-12am.
See README for setup and details.
"""

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import datetime
import json
import numpy as np
import os
import pandas as pd
import site
from collections import OrderedDict
from types import SimpleNamespace 

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def get_hourly_load(load_source, us_only):
    print('Gathering and combining hourly inputs...')
    startTime = datetime.datetime.now()
    df = pd.read_csv(load_source, low_memory=False, index_col=0, parse_dates=True)
    if us_only:
        us_bas = ['p'+str(i+1) for i in range(134)]
        df = df[us_bas].copy()
    df.index.rename('datetime', inplace=True)
    df = df.reindex(sorted(df.columns), axis=1)
    print('Done gathering hourly inputs: '+ str(datetime.datetime.now() - startTime))
    return df

def process_hourly(df_hr_input, load_source_timezone, paths, hourly_out_years, select_year, output_timezone, 
                   calibrate_type, calibrate_year, load_source_hr_type, outpath):
    print('Processing hourly data...')
    startTime = datetime.datetime.now()
    df_hr = df_hr_input.copy()
    df_hr = df_hr.sort_index()

    #Add logic for testmode?

    #We remove years and last day of leap year before rolling to local to mimic what is done for resource, which gets us close, although resource is in UTC
    #First remove other years' data
    df_hr = df_hr[df_hr.index.year.isin(hourly_out_years)].copy()

    #Remove December 31 for leap years
    df_hr = df_hr[~((df_hr.index.year % 4 == 0) & (df_hr.index.month == 12) & (df_hr.index.day == 31))].copy()

    if paths['calibrate_path'] is not False:
        #Scale the ba hourly profiles to state-level annual loads with state-to-ba participation factors
        #First, combine the calibrated state-level energy with ba participation factors to calculate the calibrated energy by BA
        df_st_energy = pd.read_csv(paths['calibrate_path'])
        df_ba_frac = pd.read_csv(paths['ba_frac_path'])
        df_hier = pd.read_csv(os.path.join(outpath, 'inputs', 'hierarchy.csv'), usecols=['ba','st'])
        df_hier.drop_duplicates(inplace=True)
        df_ba_frac = pd.merge(left=df_ba_frac, right=df_hier, how='left', on=['ba'], sort=False)
        df_ba_energy = pd.merge(left=df_ba_frac, right=df_st_energy, how='left', on=['st'], sort=False)
        df_ba_energy['GWh_cal'] = df_ba_energy['GWh'] * df_ba_energy['factor']
        df_ba_energy.drop(columns=['factor', 'st', 'GWh'], inplace=True)
        #Calculate the annual energy by ba from the hourly profile in GWh and 
        #use this to find scaling factors
        if calibrate_type == 'all_years': #switch for calibrating multiple years
            if 'year' in df_ba_energy.columns:
                #This calibration method matches load to EIA historical demand up to 'latest year,' 
                #maintaining the absolute increase in demand for each future year relative to 'latest year,' aka year_cal
                year_cal = df_ba_energy['year'].max()
                #Get annual load by BA
                df_ann = (df_hr.copy().groupby(df_hr.index.year).sum().reset_index()
                          .rename(columns={'datetime':'year'}))
                df_ann = pd.melt(df_ann, id_vars=['year'], var_name='ba', value_name='GWh')
                df_ann['GWh'] /= 1000
                df_scale = pd.merge(left=df_ann, right=df_ba_energy, on=['ba', 'year'], how='left')
                #Add columns for latest year's original projected and historical loads
                df_temp = df_scale[df_scale['year']==year_cal
                                   ][['ba', 'GWh', 'GWh_cal']].copy().drop_duplicates()
                if df_temp.empty:
                    raise Exception("Error: 'df_temp' is empty. Check calibration year and calibrate_type setting.")
                df_scale = df_scale.merge(df_temp, on=['ba'], how='left', 
                                          suffixes=('', f'_{year_cal}'))
                del df_temp
                # Get change in original projected load from latest year
                df_scale['GWh_diff'] = df_scale['GWh'] - df_scale['GWh_2024']
                # Add this difference to latest year actual historical load
                df_scale['GWh_cal_mod'] = df_scale['GWh_cal_2024'] + df_scale['GWh_diff']
                # Get new load projection
                df_scale['GWh_new'] = df_scale['GWh_cal']
                df_scale.loc[df_scale['GWh_new'].isnull(), 
                             'GWh_new'] = df_scale.loc[df_scale['GWh_new'].isnull(), 
                                                       'GWh_cal_mod']
                #Get multiplier to scale profiles
                df_scale['factor'] = df_scale['GWh_new'] / df_scale['GWh']
                #Reformat hourly load to long format to merge with scaling factors
                df_hr.insert(0, 'year', df_hr.index.year)                
                df_hr = pd.melt(df_hr.reset_index(), id_vars=['datetime', 'year'], 
                                var_name='ba', value_name='load')
                #Merge hourly load with scaling factors
                df_hr = df_hr.merge(df_scale[['year', 'ba', 'factor']], on=['year', 'ba'], how='left')
                #Scale the profiles
                df_hr['load'] *= df_hr['factor']
                df_hr = df_hr[['datetime', 'ba', 'load']]
                #Reformat hourly load back to wide format
                df_hr = df_hr.pivot_table(index=['datetime'], columns='ba', values='load')
            else:
                df_hr_yr_ls = []
                for year in df_hr.index.year.unique().tolist():
                    df_hr_yr = df_hr[df_hr.index.year == year].copy()
                    df_hr_sum = df_hr_yr.sum()/1e3
                    df_hr_sum = df_hr_sum.reset_index().rename(columns={'index':'ba', 0:'GWh_orig'})
                    df_scale = pd.merge(left=df_hr_sum, right=df_ba_energy, how='left', on=['ba'], sort=False)
                    df_scale['factor'] = df_scale['GWh_cal'] / df_scale['GWh_orig']
                    scales = dict(zip(df_scale['ba'], df_scale['factor']))
                    #Scale the profiles
                    for ba in df_hr:
                        df_hr_yr[ba] = df_hr_yr[ba] * scales[ba]
                    df_hr_yr_ls.append(df_hr_yr)
                df_hr = pd.concat(df_hr_yr_ls, sort=False)
        elif calibrate_type == 'one_year': #switch for calibrating to a single year and then using as coeffecient for additional years
            df_hr_yr = df_hr[df_hr.index.year == calibrate_year].copy()
            df_hr_sum = df_hr_yr.sum()/1e3
            df_hr_sum = df_hr_sum.reset_index().rename(columns={'index':'ba', 0:'GWh_orig'})
            df_scale = pd.merge(left=df_hr_sum, right=df_ba_energy, how='left', on=['ba'], sort=False)
            df_scale['factor'] = df_scale['GWh_cal'] / df_scale['GWh_orig']
            scales = dict(zip(df_scale['ba'], df_scale['factor']))
            #Scale the profiles
            for ba in df_hr:
                df_hr[ba] = df_hr[ba] * scales[ba]

    df_hr = df_hr.reindex(sorted(df_hr.columns), axis=1)
    df_hr = df_hr.round()
    #Shift hourly data based on desired timezones. Shift each year independently.
    df_hr_ls = []
    for year in hourly_out_years:
        df_hr_yr = df_hr[df_hr.index.year == year].copy()
        df_hr_yr = roll_hourly_data(df_hr_yr, load_source_timezone, output_timezone, load_source_hr_type)
        df_hr_ls.append(df_hr_yr)
    df_hr = pd.concat(df_hr_ls)

    #Convert format to multi-index with levels of 'year' and 'datetime', where 'year' is model year and datetime is weather year
    #Add the timezone to the index
    df_hr['year'] = df_hr.index.year
    for model_yr in df_hr['year'].unique():
        df_hr.loc[df_hr['year'] == model_yr, 'datetime'] = pd.date_range('1/1/' + str(select_year) + ' 00:00', periods=8760, freq='1H', tz=output_timezone)
    df_hr = df_hr.set_index(['year', 'datetime'])

    print('Done processing hourly: '+ str(datetime.datetime.now() - startTime))
    return df_hr

def roll_hourly_data(df_hr, source_timezone, output_timezone, load_source_hr_type):
    #If hour-beginning, we shift data down (+1) to convert to hour ending
    hour_end_shift = 1 if load_source_hr_type == 'begin' else 0
    #Extract the integer adjustment from UTC for source and output timezones
    source_tz_num = -1 * int(source_timezone.replace('Etc/GMT', ''))
    output_tz_num = -1 * int(output_timezone.replace('Etc/GMT', ''))
    #Shift timezone of hourly data
    shift = output_tz_num - source_tz_num + hour_end_shift
    if shift != 0:
        for ba in df_hr:
            df_hr[ba] = np.roll(df_hr[ba], shift)
    return df_hr

def apply_multipliers_to_historical_load(
    load_historical,
    load_multiplier,
    hierarchy,
    solveyears=None
):
    # Multipliers from AEO 2022 and older are at Census Division level, while
    # multipliers from AEO 2023 are at state level.
    if all(r in hierarchy['cendiv'] for r in load_multiplier['r']):
        load_multiplier_agglevel = 'cendiv'
    else:
        load_multiplier_agglevel = 'st'
    # Map multipliers to BAs
    r2ba = hierarchy.reset_index(drop=False)[['r', load_multiplier_agglevel]]
    load_multiplier = load_multiplier.rename(columns={'r': load_multiplier_agglevel})
    load_multiplier = (
        load_multiplier.merge(r2ba, on=[load_multiplier_agglevel], how='outer')
        .dropna(axis=0, how='any')
    )
    if solveyears is not None:
        # Subset load multipliers for solve years only 
        load_multiplier = load_multiplier[load_multiplier['year'].isin(solveyears)
                                            ][['year', 'r', 'multiplier']]
    # Reformat hourly load profiles to merge with load multipliers
    load_historical.reset_index(drop=False, inplace=True)
    load_historical = pd.melt(load_historical, id_vars=['datetime'], 
                                var_name='r', value_name='load')
    # Merge load multipliers into hourly load profiles 
    load_historical = load_historical.merge(load_multiplier, on=['r'], how='outer')
    load_historical.sort_values(by=['r', 'year'], ascending=True, inplace=True)
    load_historical['load'] *= load_historical['multiplier']
    load_historical = load_historical[['year', 'datetime', 'r', 'load']]
    # Reformat hourly load profiles for GAMS
    load_profiles = load_historical.pivot_table(
        index=['year', 'datetime'], columns='r', values='load')
    # Convert 'year' index to integers
    load_profiles.index = (
        load_profiles.index
        .set_levels(
            [load_profiles.index.levels[0].astype(int), load_profiles.index.levels[1]],
            level=['year', 'datetime']
        )
    )
    
    return load_profiles

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__== '__main__':

    #%% load arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='', help='path to config file for this run')
    args = parser.parse_args()
    configpath = args.config
    startTime = datetime.datetime.now()

    #%% load config information
    with open(configpath, "r") as f:
        config = json.load(f, object_pairs_hook=OrderedDict)
    cf = SimpleNamespace(**config)

    #%% setup logging
    site.addsitedir(cf.reeds_path)
    import reeds
    from reeds.log import makelog

    makelog(scriptname=__file__, logpath=os.path.join(cf.outpath, f'log_{cf.casename}.txt'))

    # list of paths for passing to functions
    paths = {'calibrate_path':cf.calibrate_path,
             'ba_frac_path':cf.ba_frac_path,
             'hierarchy_path':cf.hierarchy_path,
             'load_default':cf.load_default,
             'load_multiplier': cf.load_multiplier,
            }
    
    #If load source is a directory (as it is for EER load), the csv files inside need to be labeled like w2007.csv.
    ls_df_hr = []
    weather_years = list(range(2007,2014)) + list(range(2016,2024))
    for year in weather_years:
        print('processing weather year ' + str(year) + '...')
        df_hr_input = get_hourly_load(os.path.join(cf.load_source,'w'+str(year)+'.csv'), cf.us_only)
        if cf.hourly_process is False:
            df_hr = df_hr_input.copy()
        else:
            df_hr = process_hourly(df_hr_input, cf.load_source_timezone, paths, 
                                    cf.hourly_out_years, year, cf.output_timezone, 
                                    cf.calibrate_type, cf.calibrate_year,
                                    cf.load_source_hr_type, cf.outpath)
        ls_df_hr.append(df_hr)
    df_multi = pd.concat(ls_df_hr)
    df_multi = df_multi.sort_index()
    #Splice in default data.
    if cf.use_default_before_yr is not False:
        print('Splicing in default load before ' + str(cf.use_default_before_yr))
        df_hist = reeds.io.read_file(paths['load_default'], parse_timestamps=True)
        load_multiplier = pd.read_csv(paths['load_multiplier'])
        df_hier = pd.read_csv(paths['hierarchy_path']).rename(columns={'ba': 'r'})
        df_hist = apply_multipliers_to_historical_load(
            df_hist,
            load_multiplier,
            df_hier,
            solveyears=range(cf.use_default_before_yr)
        )
        df_multi = pd.concat([df_hist,df_multi])
        print('Done splicing in default load')
    #Save output
    reeds.io.write_profile_to_h5(df_multi, 'load_hourly.h5', f'{cf.outpath}/results', compression_opts=cf.compression_opts)
    print('All done! total time: '+ str(datetime.datetime.now() - startTime))
