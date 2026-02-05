#%% Imports
import argparse
import os
import sys
import subprocess
import datetime
import pandas as pd
import gdxpds

import reeds
import ReEDS_Augur.prep_data as prep_data
import ReEDS_Augur.capacity_credit as capacity_credit
import ReEDS_Augur.stress_periods as stress_periods


#%% Functions
def run_pras(
        casedir,
        t,
        iteration=0,
        recordtime=True,
        repo=False,
        overwrite=True,
        include_samples=False,
        write_flow=False,
        write_surplus=False,
        write_energy=False,
        write_shortfall_samples=False,
        write_availability_samples=False,
        **kwargs,
    ):
    """
    If additional keyword arguments are provided, they override values in the switches
    dictionary generated using `reeds.io.get_switches(casedir)`.
    Only keys in the switches dictionary are allowed, but we do not check types or
    self-consistency for the provided values, so review the allowed choices in cases.csv
    and use these additional arguments at your own risk.
    """
    ### Get the PRAS settings for this solve year
    print('Running ReEDS2PRAS and PRAS')
    sw = reeds.io.get_switches(casedir)
    ## If additional kwargs are provided, use them to override the switch values
    for key, val in kwargs.items():
        if key in sw:
            sw[key] = val
        else:
            raise ValueError(f'Provided {key}={val} but {key} is not in switches.csv')
    scriptpath = (sw['reeds_path'] if repo else casedir)
    start_year = min(sw['resource_adequacy_years_list'])
    ## ReEDS2PRAS runs at hourly resolution
    timesteps = sw['num_resource_adequacy_years'] * 8760
    command = ' '.join([
        "julia",
        f"--project={sw['reeds_path']}",
        ### As of 20231113 there seems to be a problem with multithreading in julia on
        ### mac M1 machines that causes multithreaded processes to hang
        ### without resolution. So disable multithreading on those systems.
        (
            '--threads=1' if (sys.platform == 'darwin')
            else f"--threads={sw['threads'] if sw['threads'] > 0 else 'auto'}"
        ),
        f"{os.path.join(scriptpath, 'ReEDS_Augur','run_pras.jl')}",
        f"--reeds_path={sw['reeds_path']}",
        f"--reedscase={casedir}",
        f"--solve_year={t}",
        f"--weather_year={start_year}",
        f"--timesteps={timesteps}",
        f"--hydro_energylim={sw['pras_hydro_energylim']}",
        f"--write_flow={int(write_flow)}",
        f"--write_surplus={int(write_surplus)}",
        f"--write_energy={int(write_energy)}",
        f"--write_shortfall_samples={int(write_shortfall_samples)}",
        f"--write_availability_samples={int(write_availability_samples)}",
        f"--iteration={iteration}",
        f"--samples={sw['pras_samples']}",
        f"--overwrite={int(overwrite)}",
        f"--include_samples={int(include_samples)}",
        f"--scheduled_outage={sw['pras_scheduled_outage']}",
        f"--pras_agg_ogs_lfillgas={int(sw['pras_agg_ogs_lfillgas'])}",
        f"--pras_existing_unit_size={int(sw['pras_existing_unit_size'])}",
        f"--pras_max_unitsize_prm={int(sw.get('pras_max_unitsize_prm',1))}",
        f"--pras_seed={int(sw['pras_seed'])}",
    ])
    print(command)
    print(f'vvvvvvvvvvvvvvv run_pras.jl {t}i{iteration} vvvvvvvvvvvvvvv')
    log = open(os.path.join(casedir, 'gamslog.txt'), 'a')
    result = subprocess.run(command, stdout=log, stderr=log, text=True, shell=True)
    log.close()
    print(f'^^^^^^^^^^^^^^^ run_pras.jl {t}i{iteration} ^^^^^^^^^^^^^^^')

    if recordtime:
        try:
            reeds.log.write_last_pras_runtime(year=t)
        except Exception as err:
            print(err)

    return result


#%% Main function
def main(t, tnext, casedir, iteration=0):

    # #%% To debug, uncomment these lines and update the run path
    # t = 2026
    # tnext = 2029
    # reeds_path = reeds.io.reeds_path
    # casedir = os.path.join(
    #     reeds_path,'runs','v20250521_prasM0_Pacific')
    # iteration = 0
    # assert tnext >= t
    # os.chdir(casedir)
    # ## Copy reeds2pras from repo to run folder
    # import shutil
    # shutil.rmtree(os.path.join(casedir, 'reeds2pras'))
    # shutil.copytree(
    #     os.path.join(reeds_path, 'reeds2pras'),
    #     os.path.join(casedir, 'reeds2pras'),
    #     ignore=shutil.ignore_patterns('test'),
    # )

    #%% Get run settings
    sw = reeds.io.get_switches(casedir)
    sw['t'] = t

    #%% Prep data for resource adequacy
    print('Preparing data for resource adequacy calculations')
    tic = datetime.datetime.now()
    augur_csv, augur_h5 = prep_data.main(t, casedir, iteration)
    reeds.log.toc(tic=tic, year=t, process='ReEDS_Augur/prep_data.py')

    #%% Calculate capacity credit if necessary; otherwise bypass
    print('calculating capacity credit...')
    tic = datetime.datetime.now()

    if int(sw['GSw_PRM_CapCredit']):
        cc_results = capacity_credit.reeds_cc(t, tnext, casedir)
    else:
        cc_results = {
            'cc_mar': pd.DataFrame(columns=['i','r','ccreg','szn','t','Value']),
            'cc_old': pd.DataFrame(columns=['i','r','ccreg','szn','t','Value']),
            'cc_evmc': pd.DataFrame(columns=['i','r','szn','t','Value']),
            'sdbin_size': pd.DataFrame(columns=['ccreg','szn','bin','t','Value']),
        }

    reeds.log.toc(tic=tic, year=t, process='ReEDS_Augur/capacity_credit.py')

    #%% Run PRAS if necessary
    solveyears = pd.read_csv(
        os.path.join(casedir,'inputs_case','modeledyears.csv')
    ).columns.astype(int)
    pras_this_solve_year = {
        0: False,
        1: True if t == max(solveyears) else False,
        2: True,
    }[int(sw['pras'])]
    if pras_this_solve_year or (not int(sw.GSw_PRM_CapCredit)):
        result = run_pras(
            casedir, t,
            iteration=iteration,
            write_flow=(True if t == max(solveyears) else False),
            write_energy=True,
            write_shortfall_samples=(True if int(sw.GSw_PRM_StressUpdate) > 1 else False),
        )
        if result.returncode:
            raise Exception(
                f"run_pras.jl returned code {result.returncode}. Check gamslog.txt for error trace."
            )

    #%% Identify stress periods
    print('identifying new stress periods...')
    tic = datetime.datetime.now()
    if 'user' not in sw['GSw_PRM_StressModel'].lower():
        _eue_sorted_periods = stress_periods.main(sw=sw, t=t, iteration=iteration)
    reeds.log.toc(tic=tic, year=t, process='ReEDS_Augur/stress_periods.py')

    #%% Write gdx file explicitly to ensure that all entries
    ### (even empty dataframes) are written as parameters, not sets
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

    # #%% Uncomment to run diagnostic_plots
    # ### (typically run from call_{}.sh script for parallelization)
    # try:
    #     import ReEDS_Augur.diagnostic_plots as diagnostic_plots
    #     diagnostic_plots.main(sw)
    # except Exception as err:
    #     print('diagnostic_plots.py failed with the following exception:')
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
    reeds.log.makelog(
        scriptname=f'{__file__} {t}-{tnext}',
        logpath=os.path.join(casedir,'gamslog.txt'),
    )

    main(t=t, tnext=tnext, casedir=casedir, iteration=iteration)
