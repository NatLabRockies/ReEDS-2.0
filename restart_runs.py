#%% Imports
import os
import shutil
import subprocess
import argparse
import pandas as pd
from glob import glob
from runbatch import submit_slurm_parallel_jobs
from runstatus import get_run_status

#%% Argument inputs
parser = argparse.ArgumentParser(description='Restart failed runs on the HPC')
parser.add_argument('batch_name', type=str, help='batch name (case prefix) to search for')
parser.add_argument('--copy_cplex', '-c', type=int, default=0,
                    help='Which cplex.opt file to copy (or 0 for none)')
parser.add_argument('--copy_srun_template', '-s', action='store_true',
                    help='Copy current srun_template.sh to sbatch file')
parser.add_argument('--force', '-f', action='store_true',
                    help='Proceed without double-checking')
parser.add_argument('--more_copyfiles', '-m', type=str, default='',
                    help=',-delimited list of additional files to copy from reeds_path')
parser.add_argument('--include_finished', '-i', action='store_true',
                    help='Also restart finished runs (e.g. to redo postprocessing)')

args = parser.parse_args()
batch_name = args.batch_name
copy_cplex = args.copy_cplex
copy_srun_template = args.copy_srun_template
force = args.force
more_copyfiles = [i for i in args.more_copyfiles.split(',') if len(i)]
include_finished = args.include_finished

# #%% Inputs for debugging
# batch_name = 'v20231113_yamM0'
# copy_cplex = 1
# copy_srun_template = True
# force = True
# more_copyfiles = ['e_report.gms']
# include_finished = False

###### Procedure
#%% Shared parameters
reeds_path = os.path.dirname(os.path.abspath(__file__))
#%% Get all runs
dictruns = get_run_status(reeds_path, batch_name)

runs_unfinished = dictruns['running'] + dictruns['failed']
runs_failed = dictruns['failed']
runs_running = dictruns['running']

### Take a look
print('unfinished:', len(runs_unfinished))
print('running:', len(runs_running))
print('failed:', len(runs_failed))

#%% Double check
if not force:
    for i in runs_failed:
        print(os.path.basename(i))
    print(f'Restarting the {len(runs_failed)} runs listed above.')
    confirm_local = str(input('Proceed? [y]/n: ') or 'y')
    if confirm_local not in ['y','Y','yes','Yes','YES']:
        quit()


#%% Get the cplex file to copy
if copy_cplex:
    if copy_cplex == 1:
        cplex_file = os.path.join(reeds_path,'cplex.opt')
    else:
        cplex_file = os.path.join(reeds_path,f'cplex.op{copy_cplex}')
else:
    cplex_file = None

#%% Copy the header from the srun_template.sh file if desired
if copy_srun_template:
    srun_template = os.path.join(reeds_path,'srun_template.sh')
    writelines_srun = list()
    with open(srun_template, 'r') as f:
        for line in f:
            writelines_srun.append(line.strip())
else:
    writelines_srun = list()

#%%### Loop through runs, figure out when they failed, and restart
for case in runs_failed:
    casename = os.path.basename(case)

    #%% Copy the cplex file if desired
    if copy_cplex:
        shutil.copy(cplex_file, os.path.join(case,''))

    #%% Copy additional files if desired
    for f in more_copyfiles:
        shutil.copy(os.path.join(reeds_path,f), os.path.join(case,f))

    #%% Get solveyears
    solveyears = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')
    ).columns.astype(int).tolist()

    #%% Make a backup copy of the original bash and sbatch scripts
    callfile = os.path.join(case,f'call_{casename}.sh')
    shutil.copy(callfile, os.path.join(case,f'ORIGINAL_call_{casename}.sh'))

    sbatchfile = os.path.join(case,f'{casename}.sh')
    shutil.copy(sbatchfile, os.path.join(case,f'ORIGINAL_{casename}.sh'))

    #%% Get last .lst file and restart from there
    lstfiles = sorted(glob(os.path.join(case,'lstfiles','*.lst')))
    if any([os.path.basename(i).startswith('report') for i in lstfiles]):
        restart_tag = '# Output processing'
    elif len(lstfiles) == 2: 
        # If there are only 2 lst files, then one of them will be environment.csv and the other will be 1_inputs.lst so the run failed during the model compilation 
        restart_tag = '# Compile model'
    else:
        # Drop environment and inputs .lst files
        lstfiles = [l for l in lstfiles if ("environment.csv" not in l) and ('1_Inputs.lst' not in l)]
        lastfile = lstfiles[-1]
        restart_year = int(os.path.splitext(lastfile)[0].split('_')[-1].split('i')[0])
        restart_tag = f'# Year: {restart_year}'

    #%% Comment out the unnecessary lines
    writelines = []
    with open(callfile, 'r') as f:
        comment = 0
        for line in f:
            ## Start commenting at input processing
            if '# Input processing' in line:
                comment = 1
            ## Stop commenting at restart_tag
            if line.startswith(restart_tag):
                comment = 0
            ## Record it
            writelines.append(('# ' if comment else '') + line.strip())

    ### Write it
    with open(callfile, 'w') as f:
        for line in writelines:
            f.writelines(line + '\n')

# Check if we are going to run this in parallel or not
hpc = True if (int(os.environ.get('REEDS_USE_SLURM',0))) else False
if hpc and len(runs_failed) > 1:
    # On HPC with multiple cases 
    cases_per_node = int(input('Number of simultaneous runs per node [integer]: '))
else:
    cases_per_node = 1

if hpc and (cases_per_node > 1):
    # Write the slurm scripts for parallel runs and 
    # submit them to the HPC
    casenames = [os.path.basename(p).split(batch_name + "_", 1)[-1] for p in runs_failed]
    submit_slurm_parallel_jobs(
        reeds_path=reeds_path,
        BatchName=batch_name,
        casenames=casenames,
        cases_per_node=cases_per_node,
    )

else:
    # Run each case individually
    for case in runs_failed:
        casename = os.path.basename(case)
        callfile = os.path.join(case, f'call_{casename}.sh')
        sbatchfile = os.path.join(case, f'{casename}.sh')
        # It is a single case or we are not on HPC
        if copy_srun_template:
            writelines_srun_case = writelines_srun.copy()
            writelines_srun_case.append(f"\n#SBATCH --job-name={casename}\n")
            writelines_srun_case.append(f"sh {callfile}")
            with open(sbatchfile, 'w') as f:
                for line in writelines_srun_case:
                    f.writelines(line + '\n')

        #%% Run it
        sbatch = f'sbatch {sbatchfile}'
        sbatchout = subprocess.run(sbatch, capture_output=True, shell=True)

        if len(sbatchout.stderr):
            print(sbatchout.stderr.decode())
        print(f"{casename}: {sbatchout.stdout.decode()}")
