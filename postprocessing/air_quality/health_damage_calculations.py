'''
This script can be run in one of two ways:
1. called automatically from runbatch.py as part of a ReEDS run,
   in which case a single case folder is passed to the script 

2. call directly to post-process a set of completed runs, with a csv file 
   of scenarios to process

In either case, the script with calculate total annual health damages from NOx and SO2 emissions
by source of the emissions (not location of damanges!) and saves to each run's output folder.

Passed arguments: 
    - scenario to run (either path to a run folder or a csv of scenarios with paths)

Other input data:
    - ReEDS deflator values

Output: 'health_damages_caused_by_r.csv'
    output dimensions: 
        - reeds_BA / state: source of the emissions that cause the health damage
        - year: year of emissions that incur health damages
        - model: air quality model used to estimate marginal damange (AP2, EASIUR, or InMAP)
        - cr: concentration-response function used to relate air quality to health impacts (ACS, H6C)
        - pollutant: pollutant causing damages (SO2, NOX)
    output values:
        - average marginal damage for the BA (2004$/metric ton)
        - monetized annual health damages (2004$/year)
        - the mortality estimates (lives lost/year)

For more information on the marginal damages, see https://www.caces.us/data. 

Author: Brian Sergi 
Date Created: 2/22/2022
'''
#%% Imports
import argparse
import os
import sys
import pandas as pd
import traceback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import reeds

reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

### Functions
def get_marginal_damage_rates(casepath):
    '''
    This function loads raw marginal damage estimates from the reduced complexity models
    and processes them for use in ReEDS in calculating health damages, converting
    from county to ReEDS BA. 

    Marginal damage data and documentation are available from https://www.caces.us/data
    (last downloaded January 27, 2022).
    Note that the VSL assumption of current data is 2017$.
    '''
    # load marginal damage information from RCMs
    mds_acs = pd.read_csv(
        os.path.join(
            reeds_path, 'postprocessing', 'air_quality', 'rcm_data',
            'counties_ACS_high_stack_2017.csv'))
    mds_h6c = pd.read_csv(
        os.path.join(
            reeds_path, 'postprocessing', 'air_quality', 'rcm_data',
            'counties_H6C_high_stack_2017.csv'))

    # assign concentration-response function information and combine
    mds_acs['cr'] = "ACS"
    mds_h6c['cr'] = "H6C"
    mds = pd.concat([mds_acs, mds_h6c], axis=0)
    mds.fips = mds.fips.map(lambda x: f"{x:0>5}")

    # only EASIUR has estimates that vary by season, so take annual values for now
    mds = mds.loc[mds['season'] == "annual"].copy()

    ### Map from counties to ReEDS BAs
    county2zone = reeds.io.get_county2zone(casepath)
    mds_mapped = (
        mds
        .assign(ba=mds.fips.map(county2zone))
        .dropna(subset=['ba'])
    )

    ### Take average marginal damange by ReEDS BA
    # this probably underestimates damages since there more counties with low populations
    # alternative approaches might be to take the weighted-average based on load by county or by historical emissions 
    mds_avg = mds_mapped.groupby(['ba', 'state_abbr', 'model', 'cr', 'pollutant'])['damage'].mean()
    mds_avg = mds_avg.reset_index()

    # match formatting for pollutants in ReEDS
    mds_avg['pollutant'] = mds_avg['pollutant'].str.upper()

    return mds_avg

#%% Argument inputs
parser = argparse.ArgumentParser(
    description='Calculate health damages from the emissions outputs of one or more ReEDS runs',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    'scenario', type=str,
    help='Either the folder for ReEDS run or a csv with a list of cases to post-process')
args = parser.parse_args()
scenario = args.scenario

# #%% Inputs for debugging
# scenario = os.path.join(reeds_path, 'runs', 'v20240719_agg0M1_PJM')
# casepath = scenario
# casename = os.path.basename(scenario)

#%% Procedure
print("Running 'health_damage_calculations.py' script.")

# check if scenario is a single run folder or a list of runs
casepaths = {}
# if passed .csv file of casepaths
if scenario.endswith('.csv'):
    # read in casepaths to run
    scen_file = pd.read_csv(scenario)
    for i, row in scen_file.iterrows(): 
        casepaths[row["run"]] = row["path"]

# if post-processing during a ReEDS run
elif os.path.isdir(scenario):
    scenName = os.path.basename(scenario)
    casepaths[scenName] = scenario

#%% Iterate over casepaths
for casename, casepath in casepaths.items():
    print("Processing health damages for " + casename)
    try:
        # Set up logger
        log = reeds.log.makelog(
            scriptname=__file__,
            logpath=os.path.join(casepath,'gamslog.txt'),
        )

        # get deflator
        deflator = pd.read_csv(
            os.path.join(casepath, 'inputs_case', 'deflator.csv'),
            index_col=0)
        # using EPA VSL of $7.4 million in 2006$
        # (source: https://www.epa.gov/environmental-economics/mortality-risk-valuation#whatvalue)
        # deflated to 2004$ to match ReEDS / marginal damage $ value
        VSL = 7.4E6 * deflator.loc[2006, 'Deflator'] 

        # get marginal damage rates
        mds = get_marginal_damage_rates(casepath).rename(columns={"damage":"md"})

        # marginal damage start with VSL adjusted to 2017$, so deflate to 2004$ here to match ReEDS
        mds['md'] *=  deflator.loc[2017, 'Deflator']

        # read emissions data by BA
        emit = (
            reeds.io.read_output(casepath, 'emit_r', valname='tons')
            .rename(columns={'e':'pollutant', 'etype':'type', 'r':'ba', 't':'year'})
        )
        emit = emit[emit['type']=='process']
        # inner join with marginal damages to capture only pollutants that
        # have marginal damages and only marginal damages where there are emissions
        damages = emit.merge(mds, how="inner", on=['ba', 'pollutant'])

        # monetized damage ($) is marginal damage ($/metric ton) x emissions (metric tons)
        damages['damage_$'] = damages['md'] * damages['tons']

        # mortality is monetized damages ($) / VSL ($/mortality risk)
        damages['mortality'] = damages['damage_$'] / VSL

        # organize and save
        damages = damages[[
            'ba', 'state_abbr', 'year', 'pollutant', 'tons',
            'model', 'cr', 'md', 'damage_$', 'mortality'
        ]].round({'tons':2,'md':2,'damage_$':2,'mortality':4})

        damages.to_csv(
            os.path.join(casepath, 'outputs', 'health_damages_caused_r.csv'),
            index=False)

    except Exception:
        print("Error when processing health damages for " + casename)
        print(traceback.format_exc())

print("Completed health_damage_calculations.py")
