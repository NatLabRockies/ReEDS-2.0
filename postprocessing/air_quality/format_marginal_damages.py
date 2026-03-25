'''
This script takes in raw marginal damage estimates from the reduced complexity models
and processes them for use in ReEDS in calculating health damages, namely converting
from county to ReEDS BA. 

This script only needs to be once when new marginal damage data is downloaded.

Marginal damage data and documentation available from https://www.caces.us/data.
(last downloaded January 27, 2022)

Author: Brian Sergi 
Date Created: 2/22/2022
'''

import os
import pandas as pd

print("Formatting marginal damages.")
print("Note that VSL assumption of current data is 2017$.")

# load marginal damage information from RCMs
mds_acs = pd.read_csv(os.path.join("rcm_data", "counties_ACS_high_stack_2017.csv"))
mds_h6c = pd.read_csv(os.path.join("rcm_data", "counties_H6C_high_stack_2017.csv"))

# assign concentration-response function information and combine
mds_acs['cr'] = "ACS"
mds_h6c['cr'] = "H6C"
mds = pd.concat([mds_acs, mds_h6c],axis=0)

# only EASIUR has estimates that vary by season, so take annual values for now
mds = mds.loc[mds['season'] == "annual", :]

# now map from counties to ReEDS BAs

# first load mapping from hourlize
cnty_ba_map = pd.read_csv(os.path.join("..", "..", "hourlize", "inputs", "resource", "county_map.csv"))
cnty_ba_map = cnty_ba_map.loc[:, ["county", "state", "cnty_fips", "reeds_ba"]]
mds_mapped = mds.merge(cnty_ba_map, how="outer", left_on="fips", right_on="cnty_fips")

# now take average marginal damange by ReEDS BA
# this probably underestimates damages since there more counties with low populations
# alternative approaches might be to take the weighted-average based on load by county or by historical emissions 
mds_avg = mds_mapped.groupby(['reeds_ba', 'state_abbr', 'model', 'cr', 'pollutant'])['damage'].mean()
mds_avg = mds_avg.reset_index()

# match formatting for pollutants in ReEDS
mds_avg['pollutant'] = mds_avg['pollutant'].map({'so2':"SO2", "nox":"NOX", "voc":"VOC", "nh3":"NH3", "pm25":"PM25"})

# save output
mds_avg.to_csv(os.path.join("rcm_data", "marginal_damages_by_ReEDS_BA.csv"), index=False, float_format='%.6f')

print("Formatting marginal damages complete.")
