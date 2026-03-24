#%% Imports
import os
import re
import datetime
import subprocess
import argparse
from glob import glob

# #%% Inputs for debugging
# batch_name = 'v20250812_mcK0'
# include_finished = False
# verbose = 0

#%%### Functions
def parse_multiple_runs_per_node(runs_running):
    expanded_runs = []
    for i in runs_running:
        ## Matches the form used for multiple runs per node: foo_(bar,baz[,etc])
        if re.match('^\w+_\(\w+,\w+(,\w+)*\)$', i):
            batch_ = i.split('(')[0]
            constituents = i.split('(')[1].strip(')').split(',')
            expanded_runs.extend([batch_+c for c in constituents])
        ## Otherwise it's a normal run
        else:
            expanded_runs.append(i)
    return sorted(expanded_runs)


def print_log_if_verbose(fullcase, verbose=0):
    if verbose:
        gamslog = os.path.join(fullcase, 'gamslog.txt')
        print('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvv')
        subprocess.run(f'tail {gamslog} -n {verbose}', shell=True)
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n')

def get_run_status(reeds_path, batch_name):
    #%% Get active runs
    sq = f'squeue -u {os.environ["USER"]} -o "%.200j"'
    sqout = subprocess.run(sq, capture_output=True, shell=True)
    runs_running_all = [os.path.splitext(i.decode())[0] for i in sqout.stdout.split()]

    #%% If no batch_name is provided, use the pre-underscore text from the last run
    if not len(batch_name):
        batch_name = sorted(runs_running_all)[-1].split('_')[0]
        print(f'Runs with batch_name = {batch_name}:')

    #%% Get all runs
    runs_all = sorted(glob(os.path.join(reeds_path,'runs',batch_name+'*')))
    ### Identify finished runs
    runs_finished = [
        i for i in runs_all
        if os.path.exists(os.path.join(i, 'outputs', 'reeds-report', 'report.xlsx'))
    ]
    ### Keep unfinished runs
    runs_unfinished = [i for i in runs_all if i not in runs_finished]

    ### Get failed runs by identifying and excluding active runs
    runs_running_unparsed = [i for i in runs_running_all if i.startswith(batch_name)]
    runs_running = parse_multiple_runs_per_node(runs_running_unparsed)

    # If a run is finished but on a shared node with another run still going, 
    # drop it from the running list 
    runs_running = [i for i in runs_running if os.path.join(reeds_path,'runs',i) not in runs_finished]
    runs_failed = [i for i in runs_unfinished if os.path.basename(i) not in runs_running]

    ### Store the runs
    dictruns = {
        'finished': [os.path.join(reeds_path,'runs',os.path.basename(i)) for i in runs_finished],
        'running': [os.path.join(reeds_path,'runs',os.path.basename(i)) for i in runs_running],
        'failed': [os.path.join(reeds_path,'runs',os.path.basename(i)) for i in runs_failed],
    }
    ## Only keep running runs in the current repo
    dictruns['running'] = [i for i in dictruns['running'] if os.path.isdir(i)]

    return dictruns

#%%### Procedure
if __name__ == '__main__':

    #%% Argument inputs
    parser = argparse.ArgumentParser(description='Print status of runs on the HPC')
    parser.add_argument('batch_name', type=str, nargs='?', default='',
                        help='batch name (case prefix) to search for')
    parser.add_argument('--include_finished', '-f', action='store_true',
                        help='Include finished runs in response')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='How many tail lines to print from gamslog.txt')

    args = parser.parse_args()
    batch_name = args.batch_name
    include_finished = args.include_finished
    verbose = args.verbose

    #%% Shared parameters
    reeds_path = os.path.dirname(os.path.abspath(__file__))
    dictruns = get_run_status(reeds_path, batch_name)

    #%%### Loop through categories and runs and report their status
    for key, runs in dictruns.items():
        text = f'{key}: {len(runs)}'
        print(f"\n{text}\n{'-'*len(text)}")
        ### Loop through runs
        try:
            longest = max([len(os.path.basename(i)) for i in runs])
        except ValueError:
            longest = 0
        for fullcase in runs:
            case = os.path.basename(fullcase)
            if (key == 'finished'):
                if include_finished:
                    import pandas as pd
                    duration = pd.read_csv(
                        os.path.join(fullcase,'meta.csv'), skiprows=3).processtime.sum()
                    print(f"{case:<{longest}}: {datetime.timedelta(seconds=int(duration))}")
            else:
                ### Get last .lst file
                lstfiles = sorted(glob(os.path.join(fullcase,'lstfiles','*')))
                if any([os.path.basename(i).startswith('report') for i in lstfiles]):
                    last_lst = 'e_report.gms'
                    penultimatefile = None
                else:
                    if len(lstfiles) > 1:
                        # Drop environment file
                        lstfiles = [
                            line for line in lstfiles if (
                                ('environment.csv' not in line)
                                and ('mcs_group_weights.csv' not in line)
                            )
                        ]
                    try:
                        lastfile = lstfiles[-1]
                    except IndexError:
                        print(f"{case:<{longest}}: failed in input_processing")
                        print_log_if_verbose(fullcase, verbose)
                        continue
                    try:
                        # Get time since previous lst file was modified
                        penultimatefile = lstfiles[-2]
                        penultimateyear = os.path.splitext(penultimatefile)[0].split('_')[-1]
                        lasttime = os.path.getmtime(penultimatefile)
                        nowtime = datetime.datetime.now().timestamp()
                        duration = datetime.timedelta(seconds=int((nowtime - lasttime)))
                    except IndexError:
                        penultimatefile = None
                    last_lst = os.path.splitext(lastfile)[0].split('_')[-1]

                if (key == 'running'):

                    # check if PRAS is stalled
                    logfile = os.path.join(fullcase,'gamslog.txt')
                    with open(logfile, "r") as file: 
                        gamslog = file.readlines()
                        # only look at last 5 lines in case there was a restart
                        gamslog = ''.join(gamslog[-5:])
                        if "signal (6): Aborted" in gamslog:
                            errortext = "(WARNING: PRAS may be stalled, check gamslog)"
                        else:
                            errortext = ""
                    if penultimatefile:
                        print(
                            f"{case:<{longest}}: running {last_lst} "
                            f"({duration} since {penultimateyear} finished) "
                            f"{errortext}"
                        )
                    else:
                        print(f"{case:<{longest}}: running {last_lst} {errortext}")
                elif (key == 'failed'):
                    # add some details on the runs that failed by reading the slurm file
                    slurmfile = sorted(glob(os.path.join(fullcase,'slurm*.out')))[-1]
                    with open(slurmfile, "r") as file: 
                        slurm = file.read()
                        # check if timed out
                        if "CANCELLED AT" in slurm and "DUE TO TIME LIMIT" in slurm:
                            errortext = "(timed out)"
                        # check if dual objective limit was reached
                        elif "dual objective limit exceeded" in slurm: 
                            errortext = "(hit dual obj. limit)"
                        # check if infeasible
                        elif "d_solveoneyear.gms failed with return code 3" in slurm:
                            errortext = "(infeasible)"
                        else:
                            errortext = ""
                    print(f"{case:<{longest}}: failed in {last_lst} {errortext}")
                else:
                    print(f"Unrecognized key for {case}: {key}")

                print_log_if_verbose(fullcase, verbose)
