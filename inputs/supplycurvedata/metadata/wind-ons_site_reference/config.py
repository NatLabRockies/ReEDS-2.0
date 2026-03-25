#If individual_sites = False, run in this order: resource.py -> hourlize_to_reeds.py
#If individual_sites = True, run in this order: resource.py -> hourlize_to_reeds.py -> rev-site-aggregation.py -> update_indsites_rsmap.py.

import datetime
import numpy as np
import sys
import os
import pandas as pd

this_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'

#%% SHARED CONFIG
timeslice_path = this_dir_path + 'inputs/timeslices_hourend.csv' #The index will be the hour number of the year, ie the first entry is Jan 1, 12am. Timeslices assume this is end-of-hour, e.g. H9 ends at 6am, so this is its last entry per day.
agg_outputs_timezone = 'local' #This is for the aggregated (non-hourly) outputs. 'local' means convert to local standard time of the respective region. UTC is 0. EST is -5.
hourly_outputs_timezone = 'local' #'local' means convert to local time of the respective region. UTC is 0. EST is -5.
start_1am = True #False means start at 12am
select_year = 2012 #This is the year used for load and resource profile-derived inputs, although the profile outputs may still be multiyear (see multiyear)
hourly_out_years = list(range(2007,2014)) #e.g. [2012] for just 2012 or list(range(2007,2014)) for 2007-2013
remotepath = 'Volumes' if sys.platform == 'darwin' else '/nrelnas01'
logToTerminal = True

#%% RESOURCE CONFIG, used for resource.py
#Test Mode:
test_mode = False #This limits the regions considered to those listed below.
test_filters = {'region':['s270']}
# test_filters = {'region':['i' + str(i) for i in range(5)]}

### Main inputs: Enter the tech, supply curve path, and profile path.
tech = 'wind-ons' #e.g. 'wind-ons', 'wind-ofs', 'upv', 'dupv'
access_case = 'reference' #e.g. 'reference', 'open', 'limited'
individual_sites = True

df_rev = pd.read_csv(this_dir_path + '../inputs/supplycurvedata/metadata/rev_paths.csv')
df_rev = df_rev[(df_rev['tech'] == tech)&(df_rev['access_case'] == access_case)].squeeze()
rev_prefix = os.path.basename(df_rev['rev_path'])
# rev_cases_path should have files for each year with hourly generation data for each supply curve point or gen_gid, called [rev_prefix]_rep-profiles_[select_year].h5.
rev_cases_path = r'/{}/ReEDS/Supply_Curve_Data/{}'.format(remotepath,df_rev['rev_path'])
rev_sc_file_path = r'/{}/ReEDS/Supply_Curve_Data/{}'.format(remotepath,df_rev['sc_file'])
profile_dir = '' #Use '' if .h5 files are in same folder as metadata, else point to them, e.g. '../{}'.format(rev_prefix)
# choices for PV are '' (for AC), 'profiles_clipped_power', 'dc_profiles'
profile_dir = ''
# subtract_exog [default False]: Indicate whether to remove exogenous (pre-start_year) capacity from the supply curve
subtract_exog = False

### More consistent config: This may not need to change for different runs
resource_source_timezone = 0 #UTC would be 0, Eastern standard time would be -5
class_path = this_dir_path + 'inputs/resource/' + tech + '_resource_classes.csv'
reg_col = 'cnty_fips' #region from supply curve file (sc_path). 'cnty_fips' for county, could be 'model_region' if it is already in the supply curve. TODO: Add cnty_fips to pv supply curves so we map to regions with "p" in front.
reg_map_path = this_dir_path + 'inputs/resource/county_map.csv' #This file maps counties to reeds regions and bas.
existing_sites = this_dir_path + '../inputs/capacitydata/ReEDS_generator_database_final_EIA-NEMS.csv' #None or path to file with existing capacity
state_abbrev = this_dir_path + 'inputs/resource/state_abbrev.csv'
start_year = 2010 #The start year of the model, for existing and sites purposes.
bin_group_cols = ['region','class']
bin_method = 'equal_cap_cut' #'equal_cap_man', 'equal_cap_cut'. 'kmeans' currently commented out to prevent numpy depracation warnings from sklearn.
add_h17 = True #Add h17 timeslice as equal to h3
driver = 'H5FD_CORE' #'H5FD_CORE', None. H5FD_CORE will load the h5 into memory for better perforamnce, but None must be used for low-memory machines.
gather_method = 'smart' # 'list', 'slice', 'smart'. This setting will take a slice of profile ids from the min to max, rather than using a list of ids, for improved performance when ids are close together for each group.
if tech == 'wind-ons':
    min_cap = 5.5 #MW
    bin_col = 'combined_eos_trans' #'combined_eos_trans' is a computed column from economies of scale and transmission cost. To turn off economies of scale, use 'trans_cap_cost'
    transcost_col = 'trans_cap_cost_per_mw'
    distance_cols = ['dist_km']
    filter_cols = {'offshore':['=',0]} #This means filter the supply curve to rows for which offshore is 0.
    profile_dset = 'rep_profiles_0'
    profile_id_col = 'sc_point_gid'
    profile_weight_col = 'capacity'
    reg_out_col = 'reeds_region' #A column from reg_map_path that is desired for 'region' column, mapping from reg_col. If different than reg_col, make sure reg_col is unique in reg_map_path. Make the same as reg_col to use it directly.
elif tech == 'wind-ofs':
    min_cap = 15 #MW
    bin_col = 'combined_off_ons_trans' #'combined_off_ons_trans' is a computed column from offshore (array and export) as well as onshore transmission cost.
    transcost_col = 'trans_cap_cost_per_mw'
    distance_cols = ['dist_km','dist_to_coast'] #TODO: dist_to_coast is in miles, Travis Williams thinks. So we need conversion or reV needs to change.
    filter_cols = {'offshore': ['=',1], 'bathymetry': ['>',-1300]}
    profile_dset = 'rep_profiles_0'
    profile_id_col = 'sc_point_gid'
    profile_weight_col = 'capacity'
    reg_out_col = 'reeds_region' #A column from reg_map_path that is desired for 'region' column, mapping from reg_col. If different than reg_col, make sure reg_col is unique in reg_map_path. Make the same as reg_col to use it directly.
elif tech in ['upv','dupv']:
    min_cap = 5 # MW (LBNL utility-scale solar report & NREL PV cost benchmarks define utility-scale as ≥5 MW)
    bin_col = 'trans_cap_cost_per_mw'
    transcost_col = 'trans_cap_cost_per_mw'
    distance_cols = ['dist_km']
    filter_cols = {} #this means use the full dataframe
    profile_dset = 'rep_profiles_0'
    profile_id_col = 'sc_point_gid'
    profile_weight_col = 'capacity'
    reg_out_col = 'reeds_ba'
###### Specify the settings for hourly profile files
### filetype: 'csv' or 'h5'
filetype = 'h5'
### compression_opts: can select from 0-9: 0 is faster and larger, 9 is slower and smaller, 4 is default
compression_opts = 4
### dtype: np.float16 or np.float32
dtype = np.float16

#Resource output directory
tech_suffix = '_ind' if individual_sites else ''
out_dir = tech + tech_suffix + '_' + rev_prefix + '/'

#%% LOAD CONFIG, used for load.py
#Note that calcs assume UTC, although the current load source is in eastern time (delete this after updating)
load_source = this_dir_path + 'plexos_to_reeds/outputs/load_hourly_ba_EST.csv' #e.g. '//nrelnas01/ReEDS/PLEXOS_ReEDS_Load/combined/load_full.csv' This is a file (csv or compressed csv) with datetime as index and ba columns
load_source_timezone = -5 #UTC would be 0, Eastern standard time would be -5
calibrate_path = this_dir_path + 'inputs/load/EIA_2010loadbystate.csv' #Enter string to calibrate path or False to leave uncalibrated
calibrate_year = 2010 #This is the year that the outputs of load.py represent, based on the EIA calibration year
ba_frac_path = this_dir_path + 'inputs/load/load_participation_factors_st_to_ba.csv' #These are fractions of state load in each ba, unused if calibrate_path is False
hierarchy_path = this_dir_path + 'inputs/load/hierarchy.csv' #Used for both calibration and variability outputs
season_path = this_dir_path + 'inputs/load/seasons.csv' #These are fractions of state load in each ba, unused if calibrate_path is False
ba_timezone_path = this_dir_path + 'inputs/load/ba_timezone.csv' #Should this be used for resource too, rather than site timezone?
hourly_process = True #If False, skip all hourly processing steps
truncate_leaps = True #Truncate leap years
us_only = True #Only run US BAs.
