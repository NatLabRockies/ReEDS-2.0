#%% Imports
import os
import site
import argparse
import pandas as pd
import subprocess
from glob import glob
import reeds
import Augur


#%% Main function
def run_reeds(casepath, t, onlygams=False, iteration=0):
    """
    """
    # #%% Arguments for testing
    # casepath = os.path.expanduser('~/github/ReEDS-2.0/runs/v20230512_prasM0_ERCOT')
    # t = 2020
    # onlygams = 0
    # iteration = 0
    # os.chdir(casepath)

    #%% Inferred inputs
    site.addsitedir(casepath)
    import runbatch

    #%% Get the run settings
    sw = reeds.io.get_switches(casepath)
    years = pd.read_csv(
        os.path.join(casepath,'inputs_case','modeledyears.csv')
    ).columns.astype(int).values
    tprev = {**{years[0]:years[0]}, **dict(zip(years[1:], years))}
    tnext = {**dict(zip(years, years[1:])), **{years[-1]:years[-1]}}

    #%%### Run GAMS LP
    if not onlyaugur:
        #%% Get the command to run GAMS for this solve year
        batch_case = os.path.basename(casepath)
        stress_year = f"{t}i{iteration}"
        ### Get the restartfile (last iteration from previous year)
        if t == min(years):
            restartfile = batch_case
        else:
            restartfile = sorted(
                glob(os.path.join(casepath,'g00files',f"{batch_case}_{tprev[t]}i*"))
            )[-1]

        cmd_gams = runbatch.solvestring_sequential(
            batch_case=batch_case,
            caseSwitches=sw,
            cur_year=t,
            next_year=tnext[t],
            prev_year=tprev[t],
            stress_year=stress_year,
            restartfile=restartfile,
            hpc=int(sw['hpc']),
            iteration=iteration,
        )
        print(cmd_gams)

        ### Run GAMS LP
        result = subprocess.run(cmd_gams, shell=True)
        if result.returncode:
            raise Exception(f'd_solveoneyear.gms failed with return code {result.returncode}')

        #%% Add solve time to run metadata
        try:
            cmd_log = (
                f"python {os.path.join(casepath, 'reeds', 'log.py')}"
                f" --year={t}\n"
            )
            subprocess.run(cmd_log, shell=True)
        except Exception as err:
            print(err)

        #%% Check to see if the restart file exists
        savefile = f"{batch_case}_{t}i{iteration}"
        if not os.path.isfile(os.path.join("g00files", savefile+".g00")):
            raise Exception(f"Missing {savefile}.g00")


    #%%### Run Augur
    if (not onlygams) and (tnext[t] > int(sw.GSw_SkipAugurYear)):
        Augur.main(t=t, tnext=tnext[t], casedir=casepath, iteration=iteration)


#%% Driver function
def main(casepath, t, overwrite=False):
    """
    """
    ### Get the run settings
    sw = reeds.io.get_switches(casepath)
    for iteration in range(int(sw.GSw_PRM_StressIterateMax)):
        #%% If not overwriting, skip iterations that have already finished
        if (
            (not overwrite)
            ## Check if GAMS finished
            and os.path.isfile(
                os.path.join(
                    sw.casedir, 'g00files',
                    f"{os.path.basename(sw.casedir)}_{t}i{iteration}.g00"))
            ## Check if the output of hourly_writetimeseries.py for this year/iteration
            ## exists, indicating stress period calcluations finished (or that we're not
            ## using stress periods)
            and os.path.isfile(
                os.path.join(
                    sw.casedir, 'inputs_case', f'stress{t}i{iteration+1}', 'cf_vre.csv'))
            ## Check if Augur finished
            and os.path.isfile(
                os.path.join(
                    sw.casedir, 'ReEDS_Augur', 'augur_data', f'ReEDS_Augur_{t}.gdx'))
        ):
            print(f'Already ran {t}i{iteration} so continuing to next iteration')
            continue

        #%% Run ReEDS and Augur
        run_reeds(casepath, t, iteration=iteration)

        #%% Stop here if there's no stress period data for the next iteration
        ### (either because we're not iterating or because the threshold was met)
        if not os.path.isfile(
            os.path.join(
                sw.casedir, 'inputs_case', f'stress{t}i{iteration+1}', 'period_szn.csv')
        ):
            print('No new stress periods to add, so moving to next solve year')
            break
        ### Otherwise continue iterating
        else:
            print(f'NEUE threshold was not met, so performing iteration {iteration+1}')

    ### Delete old restart files if desired
    years = pd.read_csv(
        os.path.join(casepath,'inputs_case','modeledyears.csv')
    ).columns.astype(int).values
    tprev = {**{years[0]:years[0]}, **dict(zip(years[1:], years))}

    if ((not int(sw['keep_g00_files'])) and (not int(sw['debug']))) and (min(years) < t):
        g00files = glob(os.path.join(casepath, 'g00files', f'*{tprev[t]}i*.g00'))
        for i in g00files:
            os.remove(i)


#%% Procedure
if __name__ == '__main__':
    #%% Argument inputs
    import argparse
    parser = argparse.ArgumentParser(description='Sequential ReEDS')
    parser.add_argument('casepath', type=str,
                        help='path to ReEDS run folder')
    parser.add_argument('t', type=int,
                        help='year to run')
    parser.add_argument('--iteration', '-i', type=int, default=0,
                        help='iteration counter for this run')
    parser.add_argument('--onlygams', '-g', action='store_true',
                        help='Only run GAMS (skip Augur)')
    parser.add_argument('--onlyaugur', '-a', action='store_true',
                        help='Only run Augur (skip GAMS)')
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help='Overwrite iterations that have already finished')

    args = parser.parse_args()
    casepath = args.casepath
    t = args.t
    iteration = args.iteration
    onlygams = args.onlygams
    onlyaugur = args.onlyaugur
    overwrite = args.overwrite

    #%% Switch to run folder
    os.chdir(casepath)

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(casepath,'gamslog.txt'),
    )

    #%% Run it
    main(casepath=casepath, t=t, overwrite=overwrite)
