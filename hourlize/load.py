import pandas as pd
import numpy as np
from pdb import set_trace as pdbst
import datetime
import os
import sys
import shutil
import config_load as cf
import logging
import h5py

#Set load config in config_load.py. Then run 'python load.py' from the command prompt,
#and the output will be in out/

#Setup logger
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
if cf.logToTerminal:
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
logger.info('Load logger setup.')

def setup(this_dir_path, out_dir, paths):
    time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    #Create output directory, creating backup if one already exists.
    if os.path.exists(out_dir):
        os.rename(out_dir, os.path.dirname(out_dir) + '-archive-'+time)
    os.makedirs(out_dir)
    os.makedirs(out_dir + 'inputs/')
    os.makedirs(out_dir + 'results/')

    #Add output file for logger
    fh = logging.FileHandler(out_dir + 'log.txt', mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    #Copy inputs to outputs
    shutil.copy2(this_dir_path + 'load.py', out_dir + 'inputs/')
    shutil.copy2(this_dir_path + 'config_load.py', out_dir + 'inputs/')
    for key in paths:
        if paths[key] != False:
            shutil.copy2(paths[key], out_dir + 'inputs/')

def get_hourly_load(load_source, us_only):
    logger.info('Gathering and combining hourly inputs...')
    startTime = datetime.datetime.now()
    df = pd.read_csv(load_source, low_memory=False, index_col=0, parse_dates=True)
    if us_only:
        us_bas = ['p'+str(i+1) for i in range(134)]
        df = df[us_bas].copy()
    df = df.reindex(sorted(df.columns), axis=1)
    logger.info('Done gathering hourly inputs: '+ str(datetime.datetime.now() - startTime))
    return df

def process_hourly(df_hr_input, load_source_timezone, paths, hourly_out_years, select_year, output_timezone, 
                   truncate_leaps, calibrate_type, calibrate_year, use_default_before_yr, load_source_hr_type):
    logger.info('Processing hourly data...')
    startTime = datetime.datetime.now()
    df_hr = df_hr_input.copy()
    df_hr.index.rename('datetime', inplace=True)
    df_hr = df_hr.sort_index()

    #Add logic for testmode?

    #We remove years and last day of leap year before rolling to local to mimic what is done for resource, which gets us close, although resource is in UTC
    #First remove other years' data
    df_hr = df_hr[df_hr.index.year.isin(hourly_out_years)].copy()

    if truncate_leaps is True:
        #Remove December 31 for leap years
        df_hr = df_hr[~((df_hr.index.year % 4 == 0) & (df_hr.index.month == 12) & (df_hr.index.day == 31))].copy()

    if 'p19' not in df_hr:
        #Fill p19 with p20 and scale by guess of 1/6 (although calibration below will obviate this scaling)
        df_hr['p19'] = df_hr['p20'] / 6

    if paths['calibrate_path'] != False:
        #Scale the ba hourly profiles to state-level annual loads with state-to-ba participation factors
        #First, combine the calibrated state-level energy with ba participation factors to calculate the calibrated energy by BA
        df_st_energy = pd.read_csv(paths['calibrate_path'])
        df_ba_frac = pd.read_csv(paths['ba_frac_path'])
        df_hier = pd.read_csv(paths['hierarchy_path'], usecols=['n','st'])
        df_hier.drop_duplicates(inplace=True)
        df_ba_frac = pd.merge(left=df_ba_frac, right=df_hier, how='left', on=['n'], sort=False)
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
                df_ann = pd.melt(df_ann, id_vars=['year'], var_name='n', value_name='GWh')
                df_ann['GWh'] /= 1000
                df_scale = pd.merge(left=df_ann, right=df_ba_energy, on=['n', 'year'], how='left')
                #Add columns for latest year's original projected and historical loads
                df_temp = df_scale[df_scale['year']==year_cal
                                   ][['n', 'GWh', 'GWh_cal']].copy().drop_duplicates()
                df_scale = df_scale.merge(df_temp, on=['n'], how='left', 
                                          suffixes=('', f'_{year_cal}'))
                del df_temp
                # Get change in original projected load from latest year
                df_scale['GWh_diff'] = df_scale['GWh'] - df_scale['GWh_2022']
                # Add this difference to latest year actual historical load
                df_scale['GWh_cal_mod'] = df_scale['GWh_cal_2022'] + df_scale['GWh_diff']
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
                                var_name='n', value_name='load')
                #Merge hourly load with scaling factors
                df_hr = df_hr.merge(df_scale[['year', 'n', 'factor']], on=['year', 'n'], how='left')
                #Scale the profiles
                df_hr['load'] *= df_hr['factor']
                df_hr = df_hr[['datetime', 'n', 'load']]
                #Reformat hourly load back to wide format
                df_hr = df_hr.pivot_table(index=['datetime'], columns='n', values='load')
            else:
                df_hr_yr_ls = []
                for year in df_hr.index.year.unique().tolist():
                    df_hr_yr = df_hr[df_hr.index.year == year].copy()
                    df_hr_sum = df_hr_yr.sum()/1e3
                    df_hr_sum = df_hr_sum.reset_index().rename(columns={'index':'n', 0:'GWh_orig'})
                    df_scale = pd.merge(left=df_hr_sum, right=df_ba_energy, how='left', on=['n'], sort=False)
                    df_scale['factor'] = df_scale['GWh_cal'] / df_scale['GWh_orig']
                    scales = dict(zip(df_scale['n'], df_scale['factor']))
                    #Scale the profiles
                    for ba in df_hr:
                        df_hr_yr[ba] = df_hr_yr[ba] * scales[ba]
                    df_hr_yr_ls.append(df_hr_yr)
                df_hr = pd.concat(df_hr_yr_ls, sort=False)
        elif calibrate_type == 'one_year': #switch for calibrating to a single year and then using as coeffecient for additional years
            df_hr_yr = df_hr[df_hr.index.year == calibrate_year].copy()
            df_hr_sum = df_hr_yr.sum()/1e3
            df_hr_sum = df_hr_sum.reset_index().rename(columns={'index':'n', 0:'GWh_orig'})
            df_scale = pd.merge(left=df_hr_sum, right=df_ba_energy, how='left', on=['n'], sort=False)
            df_scale['factor'] = df_scale['GWh_cal'] / df_scale['GWh_orig']
            scales = dict(zip(df_scale['n'], df_scale['factor']))
            #Scale the profiles
            for ba in df_hr:
                df_hr[ba] = df_hr[ba] * scales[ba]

    df_hr = df_hr.reindex(sorted(df_hr.columns), axis=1)
    df_hr = df_hr.round()

    #Shift hourly data based on desired timezones. Shift each year independently.
    df_hr_ls = []
    for year in hourly_out_years:
        df_hr_yr = df_hr[df_hr.index.year == year].copy()
        df_hr_yr = roll_hourly_data(df_hr_yr, paths, load_source_timezone, output_timezone, load_source_hr_type)
        df_hr_ls.append(df_hr_yr)
    df_hr = pd.concat(df_hr_ls)

    #Splice in default data, for which the first entry is Jan 1, 1am hour ending, which is 12am-1am, which is 12am hour beginning.
    if use_default_before_yr != False:
        logger.info('Splicing in default load before ' + str(use_default_before_yr))
        #Read in hierarchy to map census division / state to BA
        df_hier = pd.read_csv('../inputs/hierarchy.csv')
        df_hier = df_hier.rename(columns= {'*r' : 'r'})
        #Read in load multipliers
        df_loadgrowth = pd.read_csv(cf.aeo_default)
        if 'cendiv' in df_loadgrowth.columns:
            #AEO multipliers at the census division level are in a wide format
            #Change AEO multipliers to a long format
            df_loadgrowth = pd.melt(df_loadgrowth, id_vars=['cendiv'], 
                                    var_name='year', value_name='multiplier')
            df_loadgrowth['year'] = df_loadgrowth['year'].astype(int)
            #Map census division multipliers to BAs
            cd2rb = df_hier[['r', 'cendiv']]
            df_loadgrowth = df_loadgrowth.merge(cd2rb, on=['cendiv'], how='outer'
                                                ).dropna(axis=0, how='any')
        else:
            #AEO multipliers at the state level are already in a long format
            #Map state multipliers to BAs
            st2rb = df_hier.reset_index(drop=False)[['r', 'st']]
            df_loadgrowth = df_loadgrowth.merge(st2rb, on=['st'], how='outer'
                                                ).dropna(axis=0, how='any')
        #Remove years >= use_default_before_yr
        df_loadgrowth = df_loadgrowth[df_loadgrowth['year']<use_default_before_yr
                                      ][['year', 'r', 'multiplier']]
        df_loadgrowth['year'] = df_loadgrowth['year'].astype(int)
        logger.info('Reading default load and selecting ' + str(select_year) + ' profiles')
        df_bau = pd.read_hdf('../inputs/loaddata/historic_load_hourly.h5')
        df_bau.index += -1 # Re-index to 0-8759 instead of 1-8760
        df_bau = df_bau[(df_bau.index >= 8760*(select_year-2007)) &
                        (df_bau.index < 8760*(select_year-2006))].reset_index(drop=True) #selecting select_year profiles, which have been scaled to 2010 totals
        if 'Unnamed: 0' in df_bau.columns:
            df_bau = df_bau.drop(columns=['Unnamed: 0'])
        #Since the default load data starts at 1am hour ending while our load source
        #data starts at 12 am hour ending, we need to roll to line them up.
        df_bau = df_bau.apply(np.roll, shift=1)
        df_bau['hour'] = df_bau.index + 1
        df_bau = pd.melt(df_bau, id_vars=['hour'], var_name='r', value_name= 'value')
        #Merge load growth multipliers to historical load
        df_loadgrowth = df_loadgrowth[df_loadgrowth['r'].isin(df_bau['r'].unique())]
        df_bau = df_bau.merge(df_loadgrowth, on=['r'], how='outer').reset_index(drop=True)
        logger.info('Growing default load')
        df_bau['value'] *= df_bau['multiplier']
        logger.info('Reshaping default load')
        df_bau = df_bau.pivot_table(index=['year','hour'], columns='r', values='value').reset_index()
        logger.info('Concatenating with default load')
        ls_df_bau = []
        for year in range(2010,use_default_before_yr):
            df_yr = df_bau[df_bau['year'] == year].copy()
            df_yr['year'] = year
            df_yr.drop(columns=['year','hour'], inplace=True)
            df_yr.index = pd.date_range('1/1/' + str(year) + ' 00:00', periods=8760, freq='1H')
            ls_df_bau.append(df_yr)
        df_bau = pd.concat(ls_df_bau).round().astype(int)
        df_bau.index.rename('datetime', inplace=True)
        df_hr = pd.concat([df_bau,df_hr])
        logger.info('Done splicing in default load')

    logger.info('Done processing hourly: '+ str(datetime.datetime.now() - startTime))
    return df_hr

def roll_hourly_data(df_hr, paths, source_timezone, output_timezone, load_source_hr_type):
    #If hour-beginning, we shift data down (+1) to convert to hour ending
    hour_end_shift = 1 if load_source_hr_type == 'begin' else 0
    #Shift timezone of hourly data
    if output_timezone != source_timezone:
        if output_timezone == 'local':
            #Shift from source timezone to local standard time
            df_tz = pd.read_csv(paths['ba_timezone_path'])
            timezones = dict(zip(df_tz['ba'], df_tz['timezone']))
            for ba in df_hr:
                df_hr[ba] = np.roll(df_hr[ba], timezones[ba] - source_timezone + hour_end_shift)
        else:
            #Shift from source timezone to output timezone
            for ba in df_hr:
                df_hr[ba] = np.roll(df_hr[ba], output_timezone - source_timezone + hour_end_shift)
    return df_hr

def shift_to_1am(df_hr):
    #to start at 1am instead of 12am, roll the data by -1
    df_hr_ls = []
    for year in df_hr.index.year.unique():
        df_hr_yr = df_hr[df_hr.index.year == year].copy()
        df_hr_yr = df_hr_yr.reindex(np.roll(df_hr_yr.index,-1))
        df_hr_ls.append(df_hr_yr)
    df_hr = pd.concat(df_hr_ls)
    return df_hr

def save_outputs(df_hr, out_dir, compression_opts, dtypeLoad):
    logger.info('Saving outputs...')
    startTime = datetime.datetime.now()
    df_hr = df_hr.copy()
    #Reformat df_hr for outputting to h5 file
    df_hr['year'] = df_hr.index.year
    df_hr['hour'] = df_hr.groupby('year').cumcount() + 1
    df_hr = df_hr.reset_index(drop=True)
    new_cols = ['year','hour'] + [c for c in df_hr.columns if c not in ['year','hour']]
    df_hr = df_hr[new_cols].copy().sort_values(['year','hour'])

    #Write df_hr to h5 file with each table (year) being 8760 (hours) x 134 (regions)
    f = h5py.File(os.path.join(out_dir, 'results', 'load_hourly.h5'), 'w')
    f.create_dataset('columns', data=df_hr.columns[2:], dtype=h5py.special_dtype(vlen=str))
    for year in df_hr['year'].unique():
        df_h = df_hr[df_hr['year'] == year].copy()
        df_h.drop(columns=['year','hour'], inplace=True)
        f.create_dataset(str(year), data=df_h, dtype=dtypeLoad, compression='gzip')
    f.close()
    logger.info('Done saving outputs: '+ str(datetime.datetime.now() - startTime))


if __name__== '__main__':
    startTime = datetime.datetime.now()
    this_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    out_dir = this_dir_path + 'out/load_' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + '/'
    paths = {'ba_timezone_path':cf.ba_timezone_path,
             'calibrate_path':cf.calibrate_path,
             'ba_frac_path':cf.ba_frac_path,
             'hierarchy_path':cf.hierarchy_path,
             'aeo_multipliers':cf.aeo_default,
            }
    setup(this_dir_path, out_dir, paths)
    #If load source is a directory (as it is for EER load), the csv files inside need to be labeled like w2007.csv.
    if os.path.isdir(cf.load_source):
        #TODO: Should we move the following to a separate function, e.g. process_eer_style_load(out_dir, paths)?
        f = h5py.File(os.path.join(out_dir,'results','load_hourly_multi.h5'), 'w')
        ls_df_hr = []
        for year in list(range(2007,2014)):
            logger.info('processing weather year ' + str(year) + '...')
            df_hr_input = get_hourly_load(os.path.join(cf.load_source,'w'+str(year)+'.csv'), cf.us_only)
            if cf.hourly_process == False:
                df_hr = df_hr_input.copy()
            else:
                df_hr = process_hourly(df_hr_input, cf.load_source_timezone, paths, 
                                       cf.hourly_out_years, year, cf.output_timezone, 
                                       cf.truncate_leaps, cf.calibrate_type, 
                                       cf.calibrate_year, cf.use_default_before_yr, 
                                       cf.load_source_hr_type)
            if year == cf.select_year:
                if cf.start_1am:
                    df_hr = shift_to_1am(df_hr)
                save_outputs(df_hr, out_dir, cf.compression_opts, cf.dtypeLoad)
            else:
                if cf.start_1am:
                    df_hr = shift_to_1am(df_hr)
            df_hr['weather_year'] = year
            df_hr['model_year'] = df_hr.index.year
            ls_df_hr.append(df_hr)
        df_multi = pd.concat(ls_df_hr, ignore_index=True)
        #Save ba columns. Remove the final two columns (weather_year and model_year).
        f.create_dataset('columns', data=df_multi.columns[:-2], dtype=h5py.special_dtype(vlen=str))
        #Create h5 datasets, one for each model year
        for year in df_multi['model_year'].unique():
            df_h = df_multi[df_multi['model_year'] == year].copy()
            df_h.drop(columns=['weather_year','model_year'], inplace=True)
            f.create_dataset(str(year), data=df_h, dtype=cf.dtypeLoad, compression='gzip')
        f.close()
    else:
        df_hr_input = get_hourly_load(cf.load_source, cf.us_only)
        if cf.hourly_process == False:
            df_hr = df_hr_input.copy()
        else:
            df_hr = process_hourly(df_hr_input, cf.load_source_timezone, paths, 
                                   cf.hourly_out_years, cf.select_year, cf.output_timezone, 
                                   cf.truncate_leaps, cf.calibrate_type, cf.calibrate_year, 
                                   cf.use_default_before_yr, cf.load_source_hr_type)
        #Compare df_hr and df_hr_input to see the combined effect of all the processing steps.
        if cf.start_1am:
            df_hr = shift_to_1am(df_hr)
        save_outputs(df_hr, out_dir, cf.compression_opts, cf.dtypeLoad)
    logger.info('All done! total time: '+ str(datetime.datetime.now() - startTime))
