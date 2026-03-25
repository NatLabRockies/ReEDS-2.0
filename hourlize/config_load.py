'''Configuration file for load.py'''

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
hourly_out_years = list(range(2021,2051)) #e.g. list(range(2021,2051)) for 2021-2050; must be a list even if only one year
remotepath = 'Volumes' if sys.platform == 'darwin' else '/nrelnas01'
logToTerminal = True
###### Specify the settings for hourly profile files
### filetype: 'csv' or 'h5'. Note that load.py uses h5 regardless for default (historical) and EER load
filetype = 'h5'
### compression_opts: can select from 0-9: 0 is faster and larger, 9 is slower and smaller, 4 is default
compression_opts = 4

#%% LOAD CONFIG, used for load.py
#Note that calcs assume UTC, although the current load source is in eastern time (delete this after updating)
#The load source file's first column should be datetime, starting at Jan 1, 12am, stepping by 1 hour, and one column for each BA. It should be a csv (or a compressed csv).
load_source = '//nrelnas01/ReEDS/Supply_Curve_Data/LOAD/2020_Update/plexos_to_reeds/outputs/load_hourly_ba_EST.csv' #This is a file (csv or compressed csv) with datetime as index and ba columns
load_source_timezone = -5 #UTC would be 0, Eastern standard time would be -5
load_source_hr_type = 'begin' #Use 'end' if load_source data hour-ending or 'begin' for hour-beginning. For instantaneous use 'end'. For EER load use 'begin'.
calibrate_path = os.path.join(this_dir_path,'inputs','load','EIA_loadbystate.csv') #Enter path to calibration file or 'False' to leave uncalibrated
calibrate_year = 2010 #This is the year that the outputs of load.py represent, based on the EIA calibration year. Unused if calibrate_path is False.
calibrate_type = 'all_years' #either 'one_year' or 'all_years'. Unused if calibrate_path is False. 'one_year' means to only calibrate one year to the EIA data and then apply the same scaling factor to all years. 'all_years' will calibrate all each year to the EIA data.
ba_frac_path = os.path.join(this_dir_path,'inputs','load','load_participation_factors_st_to_ba.csv') #These are fractions of state load in each ba, unused if calibrate_path is False
hierarchy_path = os.path.join(this_dir_path,'inputs','load','hierarchy.csv') #Used for both calibration and variability outputs
ba_timezone_path = os.path.join(this_dir_path,'inputs','load','ba_timezone.csv') #Should this be used for resource too, rather than site timezone?
hourly_process = True #If False, skip all hourly processing steps
truncate_leaps = True #Truncate leap years. This currently needs to be True for mapping properly to timeslices.
us_only = True #Run only US BAs.
use_default_before_yr = 2021 #Either False or a year. If set to a year, this will pull in ReEDS default load data before that year (2012 weather year)
aeo_default =  os.path.join('..','inputs','loaddata','demand_AEO_2023_reference.csv') #To calibrate data pre-use_default_before_yr

dtypeLoad = np.float32 #Use int if the file size ends up too large.
