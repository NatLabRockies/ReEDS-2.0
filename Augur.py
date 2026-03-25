# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:30:25 2020

@author: afrazier
"""

#%% Imports
import argparse
import gdxpds
import os
import sys
import subprocess
import datetime
import pandas as pd

import ReEDS_Augur.A_prep_data as A_prep_data
import ReEDS_Augur.E_capacity_credit as E_capacity_credit
import ReEDS_Augur.F_stress_periods as F_stress_periods
import ReEDS_Augur.functions as functions


#%% Functions
def run_osprey(casedir, t, sw):
    """
    """
    print('Running Osprey')
    tic = datetime.datetime.now()
    subprocess.call(
        [
            'gams', os.path.join(casedir, 'ReEDS_Augur', 'B1_osprey'),
            'o='+os.path.join(casedir, 'lstfiles', f'osprey_{t}.lst'),
            'logOption=0',
            'logfile='+os.path.join(casedir, 'gamslog.txt'),
            'appendLog=1',
            '--solver=cplex',
            f'--prev_year={t}',
            f"--hoursperperiod={sw['hoursperperiod']:>03}",
            f"--threads={sw['threads'] if sw['threads'] > 0 else 16}",
        ] + (['license=gamslice.txt'] if int(sw['hpc']) else []),
        cwd=os.getcwd()
    )
    functions.toc(tic=tic, year=t, process='ReEDS_Augur/B1_osprey.gms')

    ### Write Osprey results to csv files
    tic = datetime.datetime.now()
    subprocess.call(
        [
            'gams', os.path.join(casedir, 'ReEDS_Augur', 'B2_gdx_dump'),
            f"--prev_year={t}"
        ] + (['license=gamslice.txt'] if int(sw['hpc']) else []),
        cwd=os.getcwd()
    )
    functions.toc(tic=tic, year=t, process='ReEDS_Augur/B2_gdx_dump.gms')


def run_pras(
        casedir, t, sw, iteration=0, recordtime=True,
        repo=False, overwrite=True, include_samples=False):
    """
    """
    reeds2pras_path = os.path.expanduser(sw['reeds2pras_path'])
    ### Get the PRAS settings for this solve year
    print('Running ReEDS2PRAS and PRAS')
    tic = datetime.datetime.now()
    scriptpath = (sw['reeds_path'] if repo else casedir)
    try:
        result = subprocess.run([
            "julia",
            f"--project={sw['reeds_path']}",
            f"--threads={sw['threads'] if sw['threads'] > 0 else 'auto'}",
            f"{os.path.join(scriptpath, 'ReEDS_Augur','run_pras.jl')}",
            f"--reeds_path={sw['reeds_path']}",
            f"--reedscase={casedir}",
            f"--solve_year={t}",
            f"--weather_year=2007",
            f"--timesteps=61320",
            f"--iteration={iteration}",
            f"--samples={sw['pras_samples']}",
            f"--reeds2praspath={reeds2pras_path}",
            f"--overwrite={int(overwrite)}",
            f"--include_samples={int(include_samples)}",
        ], capture_output=True)
        for line in result.stderr.decode().split('\n'):
            print(line)
    except Exception as err:
        print(err)
    if recordtime:
        functions.toc(tic=tic, year=t, process='ReEDS_Augur/run_pras.jl')


#%% Main function
def main(t, tnext, casedir, iteration=0):

    # #%% To debug, uncomment these lines and update the run path
    # t = 2020
    # tnext = 2023
    # casedir = os.path.expanduser(
    #     '~/github/ReEDS-2.0/runs/v20230511_prasM1_ERCOT')
    # iteration = 0
    # assert tnext >= t
    # os.chdir(casedir)

    #%% Get switches from inputs_case/switches.csv and ReEDS_Augur/augur_switches.csv
    sw = functions.get_switches(casedir)
    sw['t'] = t

    #%% Prep data for Osprey and capacity credit
    print('Preparing data for Osprey, PRAS, and capacity credit calculation')
    tic = datetime.datetime.now()
    augur_gdx, augur_csv, augur_h5 = A_prep_data.main(t, casedir)
    functions.toc(tic=tic, year=t, process='ReEDS_Augur/A_prep_data.py')

    #%% Run Osprey if necessary
    if int(sw['osprey']) or (
        int(sw['GSw_PRM_MaxStressPeriods'])
        and (sw['GSw_PRM_StressModel'].lower() == 'osprey')
    ):
        run_osprey(casedir, t, sw)

    #%% Calculate capacity credit if necessary; otherwise bypass
    print('calculating capacity credit...')
    tic = datetime.datetime.now()

    if int(sw['GSw_PRM_CapCredit']):
        cc_results = E_capacity_credit.reeds_cc(t, tnext, casedir)
    else:
        cc_results = {
            'cc_mar': pd.DataFrame(columns=['i','r','ccreg','szn','t','Value']),
            'cc_old': pd.DataFrame(columns=['i','r','ccreg','szn','t','Value']),
            'cc_dr': pd.DataFrame(columns=['i','r','szn','t','Value']),
            'sdbin_size': pd.DataFrame(columns=['ccreg','szn','bin','t','Value']),
        }

    functions.toc(tic=tic, year=t, process='ReEDS_Augur/E_capacity_credit.py')

    #%% Run PRAS if necessary
    solveyears = pd.read_csv(
        os.path.join(casedir,'inputs_case','modeledyears.csv')
    ).columns.astype(int)
    pras_this_solve_year = {
        0: False,
        1: True if t == max(solveyears) else False,
        2: True,
    }[int(sw['pras'])]
    if pras_this_solve_year or (
        int(sw['GSw_PRM_MaxStressPeriods'])
        and (sw['GSw_PRM_StressModel'].lower() == 'pras')
    ):
        run_pras(casedir, t, sw, iteration=iteration)

    #%% Identify stress periods
    print('identifying new stress periods...')
    tic = datetime.datetime.now()
    keepdays_write = F_stress_periods.main(sw=sw, t=t, iteration=iteration)
    functions.toc(tic=tic, year=t, process='ReEDS_Augur/F_stress_periods.py')

    # Write gdx file explicitly to ensure that all entries
    # (even empty dataframes) are written as parameters, not sets
    with gdxpds.gdx.GdxFile() as gdx:
        for key in cc_results:
            gdx.append(
                gdxpds.gdx.GdxSymbol(
                    key, gdxpds.gdx.GamsDataType.Parameter,
                    dims=cc_results[key].columns[:-1].tolist(),
                )
            )
            gdx[-1].dataframe = cc_results[key]
        gdx.write(
            os.path.join('ReEDS_Augur', 'augur_data', f'ReEDS_Augur_{t}.gdx')
        )

    # #%% Uncomment to run G_plots (typically run from call_{}.sh script for parallelization)
    # try:
    #     import ReEDS_Augur.G_plots as G_plots
    #     G_plots.main(sw)
    # except Exception as err:
    #     print('G_plots.py failed with the following exception:')
    #     print(err)


#%% Procedure
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""Running ReEDS Augur""")

    parser.add_argument("tnext", help="Next ReEDS solve year", type=int)
    parser.add_argument("t", help="Previous ReEDS solve year", type=int)
    parser.add_argument("casedir", help="Path to ReEDS run")
    parser.add_argument('--iteration', '-i', default=0, type=int,
                        help='iteration number on this solve year')

    args = parser.parse_args()

    tnext = args.tnext
    t = args.t
    casedir = args.casedir
    iteration = args.iteration

    #%% Set up logger
    log = functions.makelog(
        scriptname=f'{__file__} {t}-{tnext}',
        logpath=os.path.join(casedir,'gamslog.txt'))

    main(t=t, tnext=tnext, casedir=casedir, iteration=iteration)
