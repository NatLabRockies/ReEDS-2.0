#%% Imports
import pandas as pd
import os, site
from glob import glob
import subprocess
### Local imports
reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


#%%### Functions
def check_slurm(forcelocal=False):
    """Check whether to submit slurm jobs (if on HPC) or run locally"""
    hpc = True if (int(os.environ.get('REEDS_USE_SLURM',0))) else False
    hpc = False if forcelocal else hpc
    ### If on NREL HPC but NOT submitting slurm job, ask for confirmation
    if ('NREL_CLUSTER' in os.environ) and (not hpc):
        print(
            "It looks like you're running on the NREL HPC but the REEDS_USE_SLURM environment "
            "variable is not set to 1, meaning the model will run locally rather than being "
            "submitted as a slurm job. Are you sure you want to run locally?"
        )
        confirm_local = str(input('Run job locally? y/[n]: ') or 'n')
        if not confirm_local in ['y','Y','yes','Yes','YES']:
            quit()
    return hpc


def submit_job(case, year=0, samples=0, repo=False, r2ppath='', overwrite=False):
    """
    """
    ### Make the run file
    jobname = f'PRAS-{os.path.basename(case)}-{samples}'
    ## Get the SLURM boilerplate
    boilerplate = []
    with open(os.path.join(reeds_path,'srun_template.sh'), 'r') as f:
        for l in f:
            boilerplate.append(l.strip())
    ## Add the command for this run
    slurm = boilerplate + [''] + [
        f"#SBATCH --job-name={jobname}",
        (
            f"python run_reeds2pras.py {case} -y {year} -s {samples} --local"
            + ' --repo' if repo else ''
            + f' --r2ppath={r2ppath}' if len(r2ppath) else ''
            + ' --overwrite' if overwrite else ''
        ),
    ]
    ### Write the SLURM command
    callfile = os.path.join(case, 'call_pras.sh')
    with open(callfile, 'w+') as f:
        for line in slurm:
            f.writelines(line+'\n')
    ### Submit the job
    batchcom = f'sbatch {callfile}'
    subprocess.Popen(batchcom.split())
    quit()


#%% Main function
def main(case, year=0, samples=0, repo=False, r2ppath='', overwrite=False):
    """
    Run A_prep_data, ReEDS2PRAS, and PRAS as necessary.
    If running PRAS, append the number of samples to the filename.
    """
    ### Import Augur scripts
    if repo:
        site.addsitedir(reeds_path)
    else:
        site.addsitedir(case)
    import Augur
    import ReEDS_Augur.A_prep_data as A_prep_data
    import ReEDS_Augur.functions as functions

    ### Get the switches, overwriting values as necessary
    sw = functions.get_switches(case)
    sw['reeds_path'] = reeds_path
    sw['pras_samples'] = samples
    if r2ppath:
        sw['reeds2pras_path'] = r2ppath

    ### Get the solve years
    years = pd.read_csv(
        os.path.join(case, 'inputs_case', 'modeledyears.csv')
    ).columns.astype(int).tolist()

    ### Parse the year input
    t = year if (year in years) else years[-1]
    sw['t'] = t

    ### Get the largest iteration and run on that system
    iteration = int(
        os.path.splitext(
            sorted(glob(os.path.join(case,'lstfiles',f'*{t}i*.lst')))[-1]
        )[0]
        .split(f'{t}i')[-1]
    )

    ### Check if A_prep_data.py outputs exist; if not, run it
    augur_data = os.path.join(case,'ReEDS_Augur','augur_data')
    files_expected = [
        f'cap_converter_{t}.csv',
        f'energy_cap_{t}.csv',
        f'forced_outage_{t}.csv',
        f'max_cap_{t}.csv',
        f'tran_cap_{t}.csv',
        f'pras_load_{t}.h5',
        f'pras_vre_gen_{t}.h5',
    ]
    if (
        any([not os.path.isfile(os.path.join(augur_data,f)) for f in files_expected])
        and overwrite
    ):
        augur_gdx, augur_csv, augur_h5 = A_prep_data.main(t, case)

    ### Run ReEDS2PRAS
    Augur.run_pras(
        case, t, sw, iteration=iteration,
        recordtime=False, repo=repo, overwrite=overwrite, include_samples=True)


#%%### Procedure
if __name__ == '__main__':
    #%% Argument inputs
    import argparse
    parser = argparse.ArgumentParser(description='run ReEDS2PRAS')
    parser.add_argument('case', type=str,
                        help='path to ReEDS run folder')
    parser.add_argument('--year', '-y', type=int, default=0,
                        help='year to run')
    parser.add_argument('--samples', '-s', type=int, default=0,
                        help='PRAS samples to run')
    parser.add_argument('--repo', '-r', action='store_true',
                        help=('Import Augur scripts from local repo '
                              '(instead of from the case being rerun)'))
    parser.add_argument('--r2ppath', '-p', type=str, default='',
                        help=('path to ReEDS2PRAS if different from that used in case'))
    parser.add_argument('--local', '-l', action='store_true',
                        help='Run locally (not as SLURM job)')
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help="Overwrite .pras file if it already exists")

    args = parser.parse_args()
    case = args.case
    year = args.year
    samples = args.samples
    repo = args.repo
    r2ppath = args.r2ppath
    local = args.local
    overwrite = args.overwrite

    # #%% Inputs for testing
    # case = '/Users/pbrown/github2/ReEDS-2.0/runs/v20230605_ntpM1_Pacific'
    # year = 2026
    # samples = 0
    # repo = True
    # r2ppath = ''
    # local = False
    # overwrite = False

    #%% Determine whether to submit SLURM job
    hpc = check_slurm(forcelocal=local)

    ### Run it
    if hpc:
        submit_job(
            case=case, year=year, samples=samples, repo=repo,
            r2ppath=r2ppath, overwrite=overwrite,
        )
    else:
        main(
            case=case, year=year, samples=samples, repo=repo,
            r2ppath=r2ppath, overwrite=overwrite,
        )
