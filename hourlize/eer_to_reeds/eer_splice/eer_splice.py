'''
This script develops BA-level load profiles for ReEDS (in GWh) based on EER state-level load profiles, load participation factors between states and BAs, and allows replacement of specified sectors with other data sources.

EER data starts at 12am hour beginning, EST. TEMPO data starts at 12am local time (hour beginning?). Building data starts at 1am hour ending EST, so no roll is needed for buidlings. Output data starts at 12am hour beginning EST.

Requires: pandas, h5py. It previously required pyarrow as well and I made a new 'parquet' conda environment with these three packages (along with dependencies)
'''
import os
import h5py
import pandas as pd
import numpy as np
import datetime
import shutil

#USER INPUTS
eer_case = 'ira_con' # Options: 'ira_con', 'central', 'baseline'
eer_base_path = '/projects/eerload/source_eer_load_profiles/20250512_eer_download/shape_outputs_2025-05-12'
weather_years = 'all' #Options: 'all' to use all weather years in eer source file; or use a list of years to subset, e.g. [2007, 2008,...]
model_years = [2021, 2025, 2030, 2035, 2040, 2045, 2050]
bas = [f'p{n}' for n in range(1,135)]
replace_sectors = False #If True, use the following parameters to remove and replace sectors
replace_type = 'Buildings' #Options: 'Transportation', 'Buildings', 'Data Centers'
replace_states = 'all' # Options: 'all' for all states in eer source file; or a list of lowercase states in which to replace load, e.g. ['massachusetts','vermont',...]
# share of sector load replaced, float between 0 (new load is added to all EER load) and 1 (EER sector load completely replaced)
replacement_share = {
    2021: 1.,
    2025: 1.,
    2030: 1.,
    2035: 1.,
    2040: 1.,
    2045: 1.,
    2050: 1.,
}

this_dir_path = os.path.dirname(os.path.realpath(__file__))

# add handling of different IRA con case names in hourlize vs. EER data
if eer_case == 'ira_con':
    eer_case_meta = 'IRA cons'
else:
    eer_case_meta = eer_case

if replace_type == 'Transportation':
    sectors_remove = {'transportation': ['buses', 'heavy duty trucks', 'light duty autos','light duty trucks', 'medium duty trucks']}
    years_remove = [2025, 2030, 2035]
    replace_dir = '/projects/drprojects/evmc/data/full_run_2024-10-14'
    replace_scen = 'mid_baseline'
elif replace_type == 'Buildings':
    sectors_remove = {
        'commercial': ['commercial air conditioning', 'commercial space heating', 'commercial ventilation'],
        'residential': ['residential air conditioning', 'residential furnace fans', 'residential secondary heating','residential space heating'],
    }
    years_remove = model_years
    # this csv contains 8760 rows (1 for every hour of the year) and 134 columns (1 for every ReEDS BA, labeled 'p{BA number}')
    # the first column is an index column, with no column name, from 0 through 8759.
    # The csv is populated with load values in units of GWh
    replace_files = [
        '/projects/eerload/mmowers/eer_splice/agg_res_eulp_hvac_elec_GWh_upgrade0.csv',
        '/projects/eerload/mmowers/eer_splice/agg_com_eulp_hvac_elec_GWh_upgrade0.csv',
    ]
elif replace_type == 'Data Centers':
    sectors_remove = {
        'commercial': ['data center cooling', 'data center it'],
    }
    years_remove = model_years
    # this csv contains 8760 rows (1 for every hour of the year) and 134 columns (1 for every ReEDS BA, labeled 'p{BA number}')
    # The csv is populated with load values in units of MWh
    # An example of this file is included here: hourlize\eer_to_reeds\eer_splice\dummy_agg_op_datacenters.csv
    # Note: this csv is dummy data purely for illustrative purposes and is not representative of data center assumptions in the EER profiles. Please bring your own data to use this feature.
    replace_files = [
        '/kfs2/projects/eerload/challoran/eer_splice/dummy_agg_op_datacenters.csv',
    ]

time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
output_dir = f'{this_dir_path}/{eer_case}_{time}'
os.makedirs(output_dir)
shutil.copy2(f'{this_dir_path}/eer_splice.py', output_dir)
shutil.copy2(f'{this_dir_path}/load_factors.csv', output_dir)
shutil.copy2(f'{this_dir_path}/ba_timezone.csv', output_dir)

df_load_factors = pd.read_csv(f'{this_dir_path}/load_factors.csv')
ba_timezone = pd.read_csv(f'{this_dir_path}/ba_timezone.csv', index_col=0)['timezone']
nonstate_columns = ['sector', 'subsector', 'dispatch_feeder', 'weather_datetime',]

ls_df_eer = []
for model_year in model_years:
    print(f'Loading eer load: {model_year}')
    #Read csv.gz
    df_eer = pd.read_csv(f'{eer_base_path}/{eer_case_meta}/{model_year}.csv.gz', compression='gzip')
    if replace_states == 'all':
        replace_states = df_eer.columns.drop(nonstate_columns).tolist()
    #Strip out specified sectors/subsectors (allow all subsectors of a sector to be removed)
    if replace_sectors and model_year in years_remove:
        for sector, subsectors in sectors_remove.items():
            remove_criteria = (df_eer['sector'] == sector)&(df_eer['subsector'].isin(subsectors))
            # reduce subsector load by replacement share
            df_eer.loc[remove_criteria, replace_states] = (
                (1 - float(replacement_share[model_year])) * df_eer.loc[remove_criteria, replace_states])
    #Sum over sectors, subsectors, and dispatch feeders
    df_eer = df_eer.groupby(by=['weather_datetime'], sort=False).sum(numeric_only=True)
    df_eer = (df_eer/1000).reset_index()  # Convert from MWh to GWh and reset index
    df_eer['model_year'] = model_year
    #Add to list
    ls_df_eer.append(df_eer)
#Concatenate
df_eer = pd.concat(ls_df_eer, ignore_index=True)
df_eer['weather_datetime'] = pd.to_datetime(df_eer['weather_datetime'])
df_eer['weather_year'] = df_eer['weather_datetime'].dt.year
if weather_years == 'all':
    weather_years = df_eer['weather_year'].unique().tolist()

for weather_year in weather_years:
    print(f'weather year: {weather_year}')
    df_eer_w = df_eer[df_eer['weather_year'] == weather_year].copy()
    hourly_timestamps = pd.date_range(start=f'1/1/{weather_year}  12:00:00 AM', end=f'12/31/{weather_year}  11:00:00 PM', freq='h')
    for model_year in model_years:
        print(f'model year: {model_year}')
        df_ba_load = pd.DataFrame({'timestamp': hourly_timestamps})
        df_ba_load['timestamp'] = df_ba_load['timestamp'].dt.strftime('%-m/%-d/%Y  %-I:%M:%S %p')
        df_ba_load.insert(0, 'year', int(model_year))
        df_ba_zeros = pd.DataFrame(np.zeros((len(df_ba_load), len(bas))), columns=bas)
        df_ba_load = pd.concat([df_ba_load, df_ba_zeros], axis='columns')
        df_eer_wm = df_eer_w[df_eer_w['model_year'] == model_year].copy().reset_index(drop=True)
        for ba in bas:
            for idx, ba_row in df_load_factors[df_load_factors['ba'] == ba].iterrows():
                #I really only need to iterate through rows because of DC and p123
                df_ba_load[ba] = df_ba_load[ba] + df_eer_wm[ba_row['state']] * ba_row['load_factor']
        if replace_sectors and model_year in years_remove:
            #Sector replacement
            if replace_type == 'Transportation':
                #TODO: Confirm units of ev-ws-immediatecharging-hourly-weighted-sum-kWh-{model_year}.csv. Currently assuming Wh even though its labeled as kWh.
                df_load_r_ldv = pd.read_csv(f'{replace_dir}/scenario={replace_scen}/segment=ldv/year={model_year}/summaries/ev-ws-immediatecharging-hourly-weighted-sum-kWh-{model_year}.csv', index_col='datetime')
                df_load_r_mhdv = pd.read_csv(f'{replace_dir}/scenario={replace_scen}/segment=ldv/year={model_year}/summaries/ev-ws-immediatecharging-hourly-weighted-sum-kWh-{model_year}.csv', index_col='datetime')
                df_load_r = df_load_r_ldv + df_load_r_mhdv
                #Convert from Wh to GWh
                df_load_r = df_load_r/1e9
                #Duplicate the final day of TEMPO data for leap years, since EER data includes all hours but TEMPO EV data does not.
                if weather_year % 4 == 0:
                    df_load_r = pd.concat([df_load_r, df_load_r.iloc[-24:]])
                #Convert from local to EST
                for ba in bas:
                    df_load_r[ba] = np.roll(df_load_r[ba], -5 - ba_timezone[ba])
            elif replace_type == 'Buildings':
                #No rolling needed because EER data starts at 12am hour beginning and building data starts at 1am hour ending
                ls_df = [pd.read_csv(f, index_col=0) for f in replace_files]
                df_load_r = pd.concat(ls_df).groupby(level=0).sum()
                #Duplicate the final day of Building data for leap years, since EER data includes all hours but Building data does not.
                if weather_year % 4 == 0:
                    df_load_r = pd.concat([df_load_r, df_load_r.iloc[-24:]])
            elif replace_type == 'Data Centers':
                ls_df = [pd.read_csv(f, index_col=0) for f in replace_files]
                df_load_r = pd.concat(ls_df).groupby(level=0).sum()
                #Convert from MWh to GWh
                df_load_r = df_load_r/1e3
                #Duplicate the final day of Data center data for leap years, since EER data includes all hours but Data center data does not.
                if weather_year % 4 == 0:
                    df_load_r = pd.concat([df_load_r, df_load_r.iloc[-24:]])
            #Adjust df_ba_load with new load
            for ba in bas:
                # only replace if ba is in replacement states (use any because p123 includes both DC and MD)
                if ba in df_load_r and df_load_factors[df_load_factors['ba'] == ba]['state'].isin(replace_states).any():
                    df_ba_load[ba] = df_ba_load[ba] + df_load_r[ba].values
        for ba in bas:
            df_ba_load[ba] = df_ba_load[ba].round(4)
        df_ba_load.to_csv(f'{output_dir}/{eer_case}_e{model_year}_w{weather_year}.csv', index=False)
print('eer_splice.py Done!')