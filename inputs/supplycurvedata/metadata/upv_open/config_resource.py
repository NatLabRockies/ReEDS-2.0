'''Configuration file for resource.py'''

import datetime
import numpy as np
import sys
import os
import pandas as pd

this_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'

#%% SHARED CONFIG
output_timezone = 'local' #'local' means convert to local standard time of the respective region. UTC is 0. EST is -5.
start_1am = True #False means start at 12am
select_year = 2012 #This is the year used for load and resource profile-derived inputs, although the profile outputs may still be multiyear (see multiyear)
hourly_out_years = list(range(2007,2014)) #e.g. [2012] for just 2012 or list(range(2007,2014)) for 2007-2013
remotepath = 'Volumes' if sys.platform == 'darwin' else '/nrelnas01'
logToTerminal = True
###### Specify the settings for hourly profile files
### filetype: 'csv' or 'h5'. Note that load.py uses h5 regardless for default (historical) and EER load
filetype = 'h5'
### compression_opts: can select from 0-9: 0 is faster and larger, 9 is slower and smaller, 4 is default
compression_opts = 4

#%% RESOURCE CONFIG, used for resource.py
#Test Mode:
test_mode = False #This limits the regions considered to those listed below.
test_filters = {'region':['p97', 'p98']}
#test_filters = {'region':['i' + str(i) for i in range(5)]}

### Main inputs: Enter the tech, supply curve path, and profile path.
tech = 'upv' #e.g. 'wind-ons', 'wind-ofs', 'upv', 'dupv'
access_case = 'open' #e.g. 'reference', 'limited'
county_level = False  #change to 'True' for county-level supply curves (overwrites 'reg_out_col')
copy_to_reeds = True #Copy hourlize outputs to ReEDS inputs
copy_to_shared = True #Copy hourlize outputs to the shared drive

df_rev = pd.read_csv(this_dir_path + '../inputs/supplycurvedata/metadata/rev_paths.csv')
dct_rev = df_rev[(df_rev['tech'] == tech)&(df_rev['access_case'] == access_case)].squeeze().to_dict()
rev_prefix = os.path.basename(dct_rev['rev_path'])
#rev_cases_path should have files for each year with hourly generation data for each supply curve point or gen_gid, called [rev_prefix]_rep-profiles_[select_year].h5.
rev_cases_path = f'/{remotepath}/ReEDS/Supply_Curve_Data/{dct_rev["rev_path"]}'
rev_sc_file_path = f'/{remotepath}/ReEDS/Supply_Curve_Data/{dct_rev["sc_file"]}'

#subtract_exog [default False]: Indicate whether to remove exogenous (pre-start_year) capacity from the supply curve
subtract_exog = False

### More consistent config: This may not need to change for different runs
resource_source_timezone = 0 #UTC would be 0, Eastern standard time would be -5
class_bin_method = 'kmeans' #The bin method, either 'kmeans', 'equal_cap_cut', or 'equal_cap_man' (only used if class_bin = True)
reg_col = 'cnty_fips' #region from supply curve file (sc_path). 'cnty_fips' for county, could be 'model_region' if it is already in the supply curve. TODO: Add cnty_fips to pv supply curves so we map to regions with "p" in front.
reg_map_path = this_dir_path + 'inputs/resource/county_map.csv' #This file maps counties to reeds regions and bas.
existing_sites = this_dir_path + '../inputs/capacitydata/ReEDS_generator_database_final_EIA-NEMS.csv' #None or path to file with existing capacity
state_abbrev = this_dir_path + 'inputs/resource/state_abbrev.csv'
start_year = 2010 #The start year of the model, for existing and sites purposes.
bin_group_cols = ['region','class']
bin_method = 'equal_cap_cut' #'equal_cap_man', 'equal_cap_cut'. 'kmeans' currently commented out to prevent numpy depracation warnings from sklearn.
driver = 'H5FD_CORE' #'H5FD_CORE', None. H5FD_CORE will load the h5 into memory for better perforamnce, but None must be used for low-memory machines.
gather_method = 'smart' # 'list', 'slice', 'smart'. This setting will take a slice of profile ids from the min to max, rather than using a list of ids, for improved performance when ids are close together for each group.
if tech == 'wind-ons':
    class_path = None  #None or path to class definitions file
    class_bin = True #This will layer dynamic bins. If class_path != None, we add region-specific bins for each of the classes defined in class_path.
    class_bin_col = 'mean_cf' #The column to be binned (only used if class_bin = True)
    class_bin_num = 10 #The number of class bins (only used if class_bin = True)
    min_cap = 0 #MW
    capacity_col = 'capacity_mw'
    bin_col = 'combined_eos_trans' #'combined_eos_trans' is a computed column from economies of scale and transmission cost. To turn off economies of scale, use 'trans_cap_cost'
    distance_cols = ['dist_km','reinforcement_dist_km']
    cost_adder_components = ['trans_adder_per_MW', 'capital_adder_per_MW']
    filter_cols = {'offshore':['=',0]} #This means filter the supply curve to rows for which offshore is 0.
    profile_dir = '' #Use '' if .h5 files are in same folder as metadata, else point to them, e.g. f'../{rev_prefix}'
    profile_file_format = '' #Unused if single_profile=True
    profile_dset = 'rep_profiles_0'
    profile_id_col = 'sc_point_gid'
    profile_weight_col = 'capacity'
    reg_out_col = 'reeds_ba' #A column from reg_map_path that is desired for 'region' column, mapping from reg_col. If different than reg_col, make sure reg_col is unique in reg_map_path. Make the same as reg_col to use it directly.
    single_profile = True #single_profile has different columns and a single h5 profile file (for all years).
elif tech == 'wind-ofs':
    class_path = f'inputs/resource/{tech}_resource_classes.csv'
    class_bin = False
    class_bin_col = 'mean_cf'
    class_bin_num = 10
    min_cap = 15 #MW
    capacity_col = 'capacity'
    bin_col = 'combined_off_ons_trans' #'combined_off_ons_trans' is a computed column from offshore (array and export) as well as onshore transmission cost.
    distance_cols = ['dist_km','dist_to_coast','reinforcement_dist_km'] #dist_to_coast is currently in meters, so we convert to km in get_supply_curve_and_preprocess()
    cost_adder_components = []
    filter_cols = {'offshore': ['=',1], 'bathymetry': ['>',-1300]}
    profile_dir = ''
    profile_file_format = f'{rev_prefix}_rep-profiles'
    profile_dset = 'rep_profiles_0'
    profile_id_col = 'sc_point_gid'
    profile_weight_col = 'capacity'
    reg_out_col = 'reeds_ba' #A column from reg_map_path that is desired for 'region' column, mapping from reg_col. If different than reg_col, make sure reg_col is unique in reg_map_path. Make the same as reg_col to use it directly.
    single_profile = False #single_profile has different columns and a single h5 profile file (for all years).
elif tech in ['upv','dupv']:
    upv_type = 'dc' # type of UPV capacity and profiles to use; options are 'ac' and 'dc' 
    class_path = None
    class_bin = True
    class_bin_col = f'mean_cf_{upv_type}'
    class_bin_num = 5
    min_cap = 5 # MW (LBNL utility-scale solar report & NREL PV cost benchmarks define utility-scale as ≥5 MW)
    capacity_col = f'capacity_mw_{upv_type}'
    bin_col = 'combined_eos_trans'
    distance_cols = ['dist_km', 'reinforcement_dist_km']
    cost_adder_components = ['trans_adder_per_MW', 'capital_adder_per_MW']
    filter_cols = {} #this means use the full dataframe
    profile_dir = f'{access_case}_{upv_type}'
    profile_file_format = f'{access_case}_{upv_type}_rep-profiles'
    profile_dset = 'rep_profiles_0'
    profile_id_col = 'sc_point_gid'
    profile_weight_col = 'capacity'
    reg_out_col = 'reeds_ba'
    single_profile = False #single_profile has different columns and a single h5 profile file (for all years).

### dtype: np.float16 or np.float32
dtype = np.float16

#Resource output directory
tech_suffix = '_county' if county_level else ''

out_dir = tech + tech_suffix + '_' + access_case + '/'
