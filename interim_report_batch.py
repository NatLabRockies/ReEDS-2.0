'''
This script allows for batch re-running of just the reporting 
functions (e_report.gms and e_report_dump.py) for a set of jobs 
with a common batch prefix, specified as a command line argument.
It will make new copies of e_report.gms/e_report_dump.py to 
each run folder, and can thus be useful to re-run reporting
for a large set of existing runs using new report scripts.

It calls `interim_report.py` so can also be useful for reporting
results from runs that have not completed all years.

author: bsergi
'''

import os, subprocess
import shutil
from glob import glob
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--batch_name', '-b', type=str, default='', help='Prefix for batch of runs')
args = parser.parse_args()
# check if on hpc
hpc = True if (int(os.environ.get('REEDS_USE_SLURM',0))) else False

# get list of cases with matching batch name
case_list = glob(os.path.join('runs', '*'))
case_list = [c for c in case_list if args.batch_name in os.path.basename(c)]
if len(case_list) == 0:
    sys.exit(f"No cases found with {args.batch_name} prefix.")
# list of new report files to copy
report_files = ["e_report.gms", "e_report_dump.py"]

# loop over cases to copy files and run 'interim_report.py' for each one
for case in case_list:
    # copy new report scripts into run folder
    for f in report_files:
        shutil.copy(f, os.path.join(case, f))
    # call runs
    case_name = os.path.basename(case)
    print(f"Running interim_report.py for {case_name}")
    interim_report = os.path.join(case, "interim_report.py")
    if os.name=='posix':
        if hpc:
            shutil.copy("srun_template.sh", os.path.join(case, "interim_report.sh"))
            with open(os.path.join(case, "interim_report.sh"), 'a') as SPATH:
                #add the name for easy tracking of the case
                SPATH.writelines("\n#SBATCH --job-name=" + case_name + "_interim_report" + "\n\n")

                # load environments 
                SPATH.writelines("\nmodule purge\n")
                SPATH.writelines("module load conda\n")
                SPATH.writelines("conda activate reeds\n")
                SPATH.writelines("module load gams\n\n\n")

                #add the call to the python file to run the report
                SPATH.writelines("python " + os.path.join(case, "interim_report.py"))
            #close the file
            SPATH.close()
            #call that file
            batchcom = "sbatch " + os.path.join(case, "interim_report.sh")
            subprocess.Popen(batchcom.split())
        else:
            os.chmod(interim_report, 0o777)
            shellscript = subprocess.Popen(["python", interim_report])
            shellscript.wait()
    else:
        os.system('start /wait cmd /c ' + interim_report)
