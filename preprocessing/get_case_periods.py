#%% Imports
import os
import pandas as pd
import argparse

#%% Inferred inputs
reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#%% Argument inputs
parser = argparse.ArgumentParser(description='Write representative periods from a ReEDS run')
parser.add_argument('case', type=str, help='path to ReEDS case')
parser.add_argument('--rep', '-r', action='store_true',
                    help='run on representative periods')
parser.add_argument('--stress', '-s', action='store_true',
                    help='run on stress periods')
parser.add_argument('--name', '-n', default='',
                    help='name for resulting file (will use case if empty)')

args = parser.parse_args()
case = args.case
rep = args.rep
stress = args.stress
name = args.name
if not len(name):
    name = os.path.basename(case)

# #%% Inputs for debugging
# case = os.path.join(reeds_path,'runs','v20231116_prmtradeM0_stress_WECC')
# rep = True
# stress = True
# name = 'test'

#%%### Procedure
#%% Representative periods
if rep:
    period_szn = pd.read_csv(
        os.path.join(case, 'inputs_case', 'rep', 'period_szn.csv')
    )
    opres_periods = pd.read_csv(
        os.path.join(case, 'inputs_case', 'rep', 'opres_periods.csv')
    ).squeeze(1)
    period_szn['opres'] = period_szn.season.map(opres_periods).fillna('')

    period_szn.to_csv(
        os.path.join(reeds_path, 'inputs', 'temporal', f'period_szn_user_{name}.csv'),
        index=False,
    )

#%% Stress periods
if stress:
    szn_stress_t = pd.read_csv(
        os.path.join(case, 'outputs', 'szn_stress_t.csv')
    ).rename(columns={'allt':'t','allszn':'szn'})[['t','szn']].sort_values(['t','szn'])

    szn_stress_t.to_csv(
        os.path.join(reeds_path, 'inputs', 'temporal', f'stressperiods_user_{name}.csv'),
        index=False,
    )
