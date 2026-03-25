# -*- coding: utf-8 -*-
"""
Created on Thu Dec  2 16:36:48 2021

@author: pgagnon

This script ingests historical CO2 direct combustion trends, determines if the 
trigger for tax credit phasedown has been hit, and if so, outputs a tech-specific 
adjustment to tax credit (both PTC and ITC) value.

Based on the Inflation Reduction Act of 2022 

"""
###########
#%% IMPORTS
import argparse
import gdxpds
import pandas as pd
import numpy as np
import os
import sys
import input_processing.support_functions as sFuncs
from ReEDS_Augur.functions import makelog

##########
#%% INPUTS
use_historical = True

#############
#%% FUNCTIONS
def calc_tc_phaseout_mult(year, case, use_historical=use_historical):
    '''
    The TC phase down schedule starts the year after the trigger year.
    GSw_TCPhaseout_start is the earliest allowed trigger year.
    Example: If the conditions are met in 2033,
             then the 0th value of the specified tc phaseout schedule applies in 2034

    tc_phaseout_schedule: dataframe with ['n_yr_after_trigger', 'tc_phaseout_mult']
    Implicitly assumes that the tc value is zero after schedule is complete.
        If tc phases to non-zero value, either enter that in the schedule or adjust code
    '''
    # #%% Debugging
    # year = 2035
    # case = os.path.expanduser('~/github2/ReEDS-2.0/runs/v20230305_reccM0_ref_seq')

    #%% Get switches
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0, squeeze=True)
    GSw_TCPhaseout_trigger_f = float(sw.GSw_TCPhaseout_trigger_f)
    GSw_TCPhaseout_ref_year = int(sw.GSw_TCPhaseout_ref_year)
    GSw_TCPhaseout_start = int(sw.GSw_TCPhaseout_start)
    GSw_TCPhaseout_forceyear = int(sw.GSw_TCPhaseout_forceyear)

    ### Set input/output path
    tc_file_dir = os.path.join(case, 'outputs', 'tc_phaseout_data')

    # Import tech groups. Used to expand const_times
    # (e.g., 'UPV' expands to all of the upv subclasses, like upv_1, upv_2, etc)
    tech_groups = sFuncs.import_tech_groups(
        os.path.join(case, 'inputs_case', 'tech-subset-table.csv'))

    # The phasedown schedule is defined starting with the first year following the trigger year
    # This schedule is for projects "commencing construction"
    tc_phaseout = pd.read_csv(os.path.join(case, 'inputs_case', 'tc_phaseout_schedule.csv'))

    # The safe harbor window defines how long a project can be considered under construction. 
    # Note that even though we can specify incentive-level safe harbors in the inputs, we are
    # calculating the single phaseout mult with the maximum safe harbor. This is an expedient for
    # lack of time to create a phaseout for each incentive. 
    safe_harbors = pd.read_csv(
        os.path.join(case, 'inputs_case', 'safe_harbor_max.csv')
    ).rename(columns={'*i':'i', 't':'t_online'})

    const_times = pd.read_csv(
        os.path.join(case, 'inputs_case', 'construction_times.csv'))

    yearset = pd.read_csv(
        os.path.join(case, 'inputs_case', 'modeledyears.csv')
    ).columns.astype(int).values

    # Calc for all years that are covered by this modeled year, then avg the credit
    if year==yearset.min():
        covered_years = [year]
    else:
        covered_years = np.arange(yearset[yearset<year].max()+1, year+1, 1)

    const_times = const_times[const_times['t_online'].isin(covered_years)]

    # Expand construction times inputs from groups to actual techs
    for tech_group in tech_groups.keys():
        if tech_group in list(const_times['i']):

            # Extract the tech group from the main df
            df_subset = const_times[const_times['i']==tech_group]
            # Drop the tech group from the main df
            const_times = const_times[const_times['i'] != tech_group]

            df_list = []

            for tech in tech_groups[tech_group]:
                df_expanded_single = df_subset.copy()
                df_expanded_single['i'] = tech
                df_list = df_list + [df_expanded_single]

            const_times = pd.concat([const_times]+df_list, ignore_index=True, sort=False)

    # If groups overlapped, drop the resulting duplicates
    const_times = const_times.drop_duplicates(['i', 't_online'])   

    # Append pvb construction times, based on battery_4 construction times
    const_times = sFuncs.append_pvb_parameters(
        dfin=const_times, tech_to_copy='battery_4')

    const_times = const_times.merge(safe_harbors, on=['i', 't_online'])
    const_times['safe_harbor_max'] = const_times['safe_harbor_max'].fillna(0)
    const_times['t_start_build'] = (
        const_times['t_online']
        - const_times[['construction_time', 'safe_harbor_max']].max(axis=1)
    )

    if year > GSw_TCPhaseout_start:
        most_recent_year = max(yearset[yearset<year])

        # Read in the latest emit data
        gdx_filename = os.path.join(
            tc_file_dir, 'emit_for_tc_phaseout_calc_%s.gdx' % most_recent_year)
        emit_nat = gdxpds.to_dataframes(gdx_filename)['emit_nat_tc']
        if '*' in emit_nat.columns:
            emit_nat.rename(columns={'*':'t'}, inplace=True)
        emit_nat['t'] = emit_nat['t'].astype(int)
        emit_nat = emit_nat.set_index('t').rename(columns={'Value':'emit_nat'})
        emit_nat['emit_nat'] = emit_nat['emit_nat'].astype(float)

        # Interpolate the emissions and calc the fraction of the reference year's emissions
        df = pd.DataFrame(index=np.arange(2010, max(yearset), 1))
        df['emit_nat'] = emit_nat
        df['emit_nat'] = df['emit_nat'].interpolate()
        # Get historical emissions if desired
        if use_historical:
            scalars = pd.read_csv(
                os.path.join(case, 'inputs_case', 'scalars.csv'),
                header=None, usecols=[0,1], index_col=0, squeeze=True)
            ref_emissions = scalars['co2_emissions_2022'] * 1e6
        # Otherwise use modeled emissions
        else:
            ref_emissions = df.loc[GSw_TCPhaseout_ref_year, 'emit_nat']

        # Calculate fraction of reference emissions
        df['emit_f'] = df['emit_nat'] / ref_emissions

        print(f'ref_emissions: {ref_emissions}')
        print('emit_nat / ref_emissions:')
        print(df['emit_f'])

        # Identify which years fall below the trigger value
        df_qual = df.loc[
            (df['emit_f'] <= GSw_TCPhaseout_trigger_f)
            & (df.index >= int(sw['GSw_StartMarkets']))
        ].copy()

        # If at least one year fell below the trigger value,
        # identify it and find each tech's tc_phaseout_mult
        # OR if GSw_TCPhaseout_forceyear is nonzero, use it as the trigger year
        if (len(df_qual) > 0) or GSw_TCPhaseout_forceyear:
            if GSw_TCPhaseout_forceyear:
                trigger_year = GSw_TCPhaseout_forceyear
            else:
                trigger_year = max([min(df_qual.index), GSw_TCPhaseout_start])

            print(f'<><><> IRA tax credits start phasing out in {trigger_year} <><><>')

            const_times['n_yr_after_trigger'] = const_times['t_start_build'] - trigger_year

            const_times = const_times.merge(
                tc_phaseout[['n_yr_after_trigger', 'tc_phaseout_mult']],
                on='n_yr_after_trigger', how='left')

            const_times['tc_phaseout_mult'] = np.where(
                const_times['n_yr_after_trigger']<=0,
                1.0,
                const_times['tc_phaseout_mult'])
            const_times['tc_phaseout_mult'] = np.where(
                const_times['n_yr_after_trigger']>tc_phaseout['n_yr_after_trigger'].max(),
                0.0,
                const_times['tc_phaseout_mult'])

            tc_phaseout_mult = (
                const_times[['i', 'tc_phaseout_mult']]
                .groupby('i', as_index=False).mean()
            )

        # If no years fell below the trigger value, tc phaseout has not begun,
        # so just set tc_phaseout_mult to 1.0 for all techs
        else:
            tc_phaseout_mult = const_times[['i']].copy()
            tc_phaseout_mult['tc_phaseout_mult'] = 1.0

    # If the first allowable trigger year has not yet been reached, tc phaseout has not begun,
    # so just set tc_phaseout_mult to 1.0 for all techs
    else:
        tc_phaseout_mult = const_times[['i']].copy()
        tc_phaseout_mult['tc_phaseout_mult'] = 1.0

    # Round for GAMS
    tc_phaseout_mult['tc_phaseout_mult'] = np.round(tc_phaseout_mult['tc_phaseout_mult'], 3)
    tc_phaseout_mult['t'] = year

    data = {'tc_phaseout_mult_t':tc_phaseout_mult[['i', 't', 'tc_phaseout_mult']]}
    gdxpds.to_gdx(data, os.path.join(tc_file_dir, 'tc_phaseout_mult_%s.gdx' % year))


#############
#%% PROCEDURE
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""Running tc_phaseout.py""")
    parser.add_argument("year", help="ReEDS solve year", type=int)
    parser.add_argument("case", help="filepath for ReEDS case")
    args = parser.parse_args()
    year = args.year
    case = args.case

    ### Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(case,'gamslog.txt'))

    print(f'starting tc_phaseout.py for {year}')
    calc_tc_phaseout_mult(year, case, use_historical=use_historical)
    print(f'finished tc_phaseout.py for {year}')
