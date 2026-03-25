#%% Imports
import os
import shutil
import subprocess
import argparse
import pandas as pd
from glob import glob

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
                    help=',-delimited list of additional files to copy from reedspath')

args = parser.parse_args()
batch_name = args.batch_name
copy_cplex = args.copy_cplex
copy_srun_template = args.copy_srun_template
force = args.force
more_copyfiles = [i for i in args.more_copyfiles.split(',') if len(i)]

# #%% Inputs for debugging
# batch_name = 'v20230524_ntpH0'
# copy_cplex = 1
# copy_srun_template = False
# force = True
# more_copyfiles = []

###### Procedure
#%% Shared parameters
reedspath = os.path.dirname(os.path.abspath(__file__))
#%% Get all runs
runs_all = sorted(glob(os.path.join(reedspath,'runs',batch_name+'*')))
### Identify finished runs
runs_finished = [
    i for i in runs_all
    if os.path.exists(os.path.join(i, 'outputs', 'reeds-report', 'report.xlsx'))
]
### Keep unfinished runs
runs_unfinished = [i for i in runs_all if i not in runs_finished]

### Get failed runs by identifying and excluding active runs
sq = f'squeue -u {os.environ["USER"]} -o "%.200j"'
sqout = subprocess.run(sq, capture_output=True, shell=True)
runs_running = [
    os.path.splitext(i.decode())[0] for i in sqout.stdout.split()
    if i.decode().startswith(batch_name)
]

runs_failed = [i for i in runs_unfinished if os.path.basename(i) not in runs_running]

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
    if not confirm_local in ['y','Y','yes','Yes','YES']:
        quit()


#%% Get the cplex file to copy
if copy_cplex:
    if copy_cplex == 1:
        cplex_file = os.path.join(reedspath,'cplex.opt')
    else:
        cplex_file = os.path.join(reedspath,f'cplex.op{copy_cplex}')
else:
    cplex_file = None

#%% Copy the header from the srun_template.sh file if desired
if copy_srun_template:
    srun_template = os.path.join(reedspath,'srun_template.sh')
    writelines_srun = list()
    with open(srun_template, 'r') as f:
        for l in f:
            writelines_srun.append(l.strip())
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
        shutil.copy(os.path.join(reedspath,f), os.path.join(case,f))

    #%% Get solveyears
    solveyears = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')
    ).columns.astype(int).tolist()

    #%% Get last .lst file and restart from there
    lastfile = sorted(glob(os.path.join(case,'lstfiles','*')))[-1]
    restart_year = int(os.path.splitext(lastfile)[0].split('_')[-1].split('i')[0])

    #%% Make a backup copy of the original bash and sbatch scripts
    callfile = os.path.join(case,f'call_{casename}.sh')
    shutil.copy(callfile, os.path.join(case,f'ORIGINAL_call_{casename}.sh'))

    sbatchfile = os.path.join(case,f'{casename}.sh')
    shutil.copy(sbatchfile, os.path.join(case,f'ORIGINAL_{casename}.sh'))

    #%% Comment out the unnecessary lines
    writelines = []
    with open(callfile, 'r') as f:
        comment = 0
        for l in f:
            ## Start commenting at input processing
            if '# Input processing' in l:
                comment = 1
            ## Stop commenting at restart_year
            if l.startswith(f'# Year: {restart_year}'):
                comment = 0
            ## Record it
            writelines.append(('# ' if comment else '') + l.strip())

    ### Write it
    with open(callfile, 'w') as f:
        for l in writelines:
            f.writelines(l + '\n')

    #%% Write the sbatch file with new header, if desired
    if copy_srun_template:
        writelines_srun_case = writelines_srun.copy()
        writelines_srun_case.append(f"\n#SBATCH --job-name={casename}\n")
        writelines_srun_case.append(f"sh {callfile}")
        with open(sbatchfile, 'w') as f:
            for l in writelines_srun_case:
                f.writelines(l + '\n')

    #%% Run it
    sbatch = f'sbatch {sbatchfile}'
    sbatchout = subprocess.run(sbatch, capture_output=True, shell=True)

    if len(sbatchout.stderr):
        raise Exception(sbatchout.stderr.decode())
    print(f"{casename}: {sbatchout.stdout.decode()}")
