# -*- coding: utf-8 -*-
"""
Code to process allowed shifting hours for demand response into
fraction of hours that can be shifted into each time slice
At some point, it may be nice to instead read in the actual DR
shifting potential and change to fraction of load that can be shifted
but haven't done that yet.

Created on Feb 24 2021
@author: bstoll
"""
#%% Imports
import os
import argparse
import sys
import shutil
import pandas as pd
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%% Inputs
decimals = 4

#%% Functions
def get_dr_shifts(sw, reeds_path, inputs_case, native_data=True,
                  hmap_7yr=None, chunkmap=None, hours=None):
    """
    part of shift demand response handling compatible both with h17 and hourly ReEDS
    hours, hmap_7yr, and chunkmap are needed for mapping hourly because there is no
    fixed assumption for temporal structure of run
    """

    dr_hrs = pd.read_csv(
        os.path.join(
            reeds_path, 'inputs', 'demand_response', f"dr_shifts_{sw['drscen']}.csv")
    )
    
    # write out dr_hrs for Augur
    dr_hrs.to_csv(os.path.join(inputs_case, 'dr_hrs.csv'), index=False)

    dr_pos = dr_hrs[['dr_type', 'pos_hrs']].reindex(dr_hrs.index.repeat(dr_hrs.pos_hrs))
    dr_pos['shift'] = dr_pos['pos_hrs'] - dr_pos.groupby(['dr_type']).cumcount()

    dr_neg = dr_hrs[['dr_type', 'neg_hrs']].reindex(dr_hrs.index.repeat(-1*dr_hrs.neg_hrs))
    dr_neg['shift'] = dr_neg['neg_hrs'] + dr_neg.groupby(['dr_type']).cumcount()

    dr_shifts = pd.concat([dr_pos.rename({'pos_hrs': 'hrs'}, axis=1),
                           dr_neg.rename({'neg_hrs': 'hrs'}, axis=1)])
    
    if native_data: #### native_data reads in inputs directly
        hr_ts = pd.read_csv(
            os.path.join(reeds_path, 'inputs', 'variability', 'h_dt_szn.csv'))
        hr_ts = hr_ts.loc[(hr_ts['hour'] <= 8760), ['h', 'hour', 'season']]
        num_hrs = pd.read_csv(
            os.path.join(reeds_path, 'inputs', 'numhours.csv'),
            header=0, names=['h', 'numhours'], index_col='h', squeeze=True)
        hr_ts = pd.read_csv(
            os.path.join(inputs_case, 'h_dt_szn.csv'))
        hr_ts = hr_ts.loc[(hr_ts['hour'] <= 8760), ['h', 'hour', 'season']]
        num_hrs = pd.read_csv(
            os.path.join(inputs_case, 'numhours.csv'),
            header=0, names=['h', 'numhours'], index_col='h', squeeze=True)
    else: #otherwise reformat to hourly timeslice subsets
        hr_ts = hmap_7yr[['h','season','year','hour']].assign(h=hmap_7yr.h.map(chunkmap))
        hr_ts = hr_ts.loc[(hr_ts['hour'] <= 8760), ['h', 'hour', 'season']]
        num_hrs = (
            hours.reset_index().assign(h=hours.index.map(chunkmap))
            .groupby('h').numhours.sum().reset_index())

    #### after here the rest is the same
    dr_shifts['key'] = 1
    hr_ts['key'] = 1
    hr_shifts = pd.merge(dr_shifts, hr_ts, on='key').drop('key', axis=1)
    hr_shifts['shifted_hr'] = hr_shifts['hour'] + hr_shifts['shift']
    # Adjust hrs to be between 1 and 8760
    lt0 = hr_shifts.shifted_hr <= 0
    gt8760 = hr_shifts.shifted_hr > 8760
    hr_shifts.loc[lt0, 'shifted_hr'] += 8760
    hr_shifts.loc[gt8760, 'shifted_hr'] -= 8760

    # Merge on hr_ts again to the shifted hours to see what timeslice DR
    # can move load into
    hr_shifts = pd.merge(hr_shifts,
                         hr_ts.rename({'h': 'shifted_h', 'hour': 'shifted_hr',
                                       'season': 'shifted_season'}, axis=1),
                         on='shifted_hr').drop('key', axis=1)
    # Only allow shifts within the same season
    hr_shifts = hr_shifts[hr_shifts.season == hr_shifts.shifted_season]
    hr_shifts.drop(['shifted_season'], axis=1, inplace=True)

    hr_shifts2 = (
        hr_shifts[['dr_type', 'h', 'hour', 'shifted_h']]
        .drop_duplicates()
        .groupby(['dr_type', 'h', 'shifted_h'])
        .size()
        .reset_index()
    )

    ts_shifts = pd.merge(hr_shifts2, num_hrs, on='h')
    ts_shifts['shift_frac'] = ts_shifts[0] / ts_shifts['numhours']

    shift_out = ts_shifts.loc[ts_shifts['h'] != ts_shifts['shifted_h'], :]
    shift_out = shift_out.round(4)

    return shift_out, dr_shifts


#%% Procedure
if __name__ == "__main__":

    # Argument inputs
    parser = argparse.ArgumentParser(
        description="""This file produces the DR shiftability inputs""")

    parser.add_argument("reeds_path", help="ReEDS directory")
    parser.add_argument("inputs_case", help="output directory")

    args = parser.parse_args()
    inputs_case = args.inputs_case
    reeds_path = args.reeds_path

    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    #%% Inputs from switches
    sw = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

    drscen = sw.drscen

    ### Read in DR shed for specified scenario
    dr_shed = pd.read_csv(
        os.path.join(args.reeds_path, 'inputs', 'demand_response', f'dr_shed_{drscen}.csv'))

    ### Profiles
    dr_profile_increase = pd.read_csv(
        os.path.join(reeds_path,'inputs','demand_response',f'dr_increase_profile_{sw.drscen}.csv'))
    dr_profile_decrease = pd.read_csv(
        os.path.join(reeds_path,'inputs','demand_response',f'dr_decrease_profile_{sw.drscen}.csv'))

    ### Filter by regions
    val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'), squeeze=True, header=None).tolist()
    dr_profile_increase = (
        dr_profile_increase.loc[:,dr_profile_increase.columns.isin(['i','hour','year'] + val_r)])
    dr_profile_decrease = (
        dr_profile_decrease.loc[:,dr_profile_decrease.columns.isin(['i','hour','year'] + val_r)])


    dr_shed[['dr_type', 'yr_hrs']].to_csv(
        os.path.join(inputs_case, 'dr_shed.csv'), index=False, header=False)

    dr_profile_increase.to_csv(
        os.path.join(inputs_case,'dr_inc.csv'),index=False)
    dr_profile_decrease.to_csv(
        os.path.join(inputs_case,'dr_dec.csv'),index=False)

    # Copy DR types
    shutil.copy(
        os.path.join(args.reeds_path,'inputs','demand_response',f'dr_types_{drscen}.csv'),
        os.path.join(inputs_case, 'dr_types.csv'))
    
    toc(tic=tic, year=0, process='input_processing/writedrshift.py', 
        path=os.path.join(inputs_case,'..'))
