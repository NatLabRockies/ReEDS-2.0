'''
This script can be run in one of two ways:
1. activate via GSw_HealthDamages (on by default) to call from runbatch.py as part of a ReEDS run, 
   in which case a single case folder is passed to the script 

2. call directly to post-process a set of completed runs, with a csv file 
   of scenarios to process

In either case, the script with calculate total annual health damages from NOx and SO2 emissions
by source of the emissions (not location of damanges!) and saves to each run's output folder.

Passed arguments: 
    - scenario to run (either path to a run folder or a csv of scenarios with paths)

Other input data:
    - 'marginal_damages_by_ReEDS_BA.csv': data on marginal damages. built by 'format_marginal_damages.py'
    - ReEDS deflator values

Output: 'health_damages_caused_by_r.csv'
    output dimensions: 
        - reeds_BA / state: source of the emissions that cause the health damage
        - year: year of emissions that incur health damages
        - model: air quality model used to estimate marginal damange (AP2, EASIUR, or InMAP)
        - cr: concentration-response function used to relate air quality to health impacts (ACS, H6C)
        - pollutant: pollutant causing damages (SO2, NOX)
    output values:
        - average marginal damage for the BA (2004$/tonne)
        - monetized annual health damages (2004$/year)
        - the mortality estimates (lives lost/year)

For more information on the marginal damages, see https://www.caces.us/data. 

Author: Brian Sergi 
Date Created: 2/22/2022
'''

import argparse
import os
import pandas as pd
import sys
import site

# Automatic inputs
reeds_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
site.addsitedir(os.path.join(reeds_path,'input_processing'))
from ticker import makelog

# Argument inputs
parser = argparse.ArgumentParser(
    description='Calculate health damages from the emissions outputs of one or more ReEDS runs')
parser.add_argument(
    'scenario',
    help='Either the folder for ReEDS run or a csv with a list of cases to post-process')
args = parser.parse_args()

print("Running 'health_damage_calculations.py' script.")

# check if scenario is a single run folder or a list of runs
scenarios = {}
try:
    # if passed .csv file of scenarios
    if args.scenario.endswith('.csv'):

        # read in scenarios to run
        scen_file = pd.read_csv(args.scenario)
        for i, row in scen_file.iterrows(): 
            scenarios[row["run"]] = row["path"]

        # load deflator and marginal damages
        deflator = pd.read_csv(os.path.join(reeds_path, 'inputs', 'deflator.csv'), index_col=0)
        mds = pd.read_csv(
            os.path.join(
                reeds_path, 'postprocessing', 'air_quality',
                'rcm_data', 'marginal_damages_by_ReEDS_BA.csv'))

    # if post-processing during a ReEDS run
    elif os.path.isdir(args.scenario):
        scenName = os.path.basename(args.scenario)
        scenarios[scenName] = args.scenario

        #%% Set up logger
        log = makelog(scriptname=__file__, logpath=os.path.join(args.scenario,'gamslog.txt'))

        # load deflator and marginal damages
        deflator = pd.read_csv(
            os.path.join(args.scenario, 'inputs_case', 'deflator.csv'),
            index_col=0)
        mds = pd.read_csv(
            os.path.join(
                reeds_path, 'postprocessing', 'air_quality', 'rcm_data',
                'marginal_damages_by_ReEDS_BA.csv'))

except Exception as err:
    print("Invalid run path or file name for calculating health damages.")
    print(err)

# load marginal damages 
try:
    mds.rename(columns={"damage":"md"}, inplace=True)

    # marginal damage start with VSL adjusted to 2017$, so deflate to 2004$ here to match ReEDS
    mds['md'] *=  deflator.loc[2017, 'Deflator']

    # using EPA VSL of $7.4 million in 2006$
    # (source: https://www.epa.gov/environmental-economics/mortality-risk-valuation#whatvalue)
    # deflated to 2004$ to match ReEDS / marginal damage $ value
    VSL = 7.4E6 * deflator.loc[2006, 'Deflator'] 

except Exception as err:
    print("Error loading marginal damage data.")
    print(err)


# iterate over scenarios
for scen in scenarios:
    print("Processing health damages for " + scen)

    try:
        # read emissions data by BA
        emit = pd.read_csv(os.path.join(scenarios[scen], "outputs", "emit_r.csv"), 
                            names=['pollutant','reeds_ba','year','tonnes'], header=0)
        
        # inner join with marginal damages to capture only pollutants that
        # have marginal damages and only marginal damages where there are emissions
        damages = emit.merge(mds, how="inner", on=['reeds_ba', 'pollutant'])

        # monetized damage ($) is marginal damage ($/tonne) x emissions (tonnes)
        damages['damage_$'] = damages['md'] * damages['tonnes']

        # mortality is monetized damages ($) / VSL ($/mortality risk)
        damages['mortality'] = damages['damage_$'] / VSL

        # organize and save
        damages = damages[[
            'reeds_ba', 'state_abbr', 'year', 'pollutant', 'tonnes',
            'model', 'cr', 'md', 'damage_$', 'mortality']].round(
                {'tonnes':2,'md':2,'damage_$':2,'mortality':4}
            )
        damages.to_csv(
            os.path.join(scenarios[scen], 'outputs', 'health_damages_caused_r.csv'),
            index=False)
    except Exception as err:
        print("Error when processing health damages for " + scen)
        print(err)


print("Completed 'health_damage_calculations.py' script.")
