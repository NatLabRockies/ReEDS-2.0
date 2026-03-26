#%% Imports
import os
import argparse
import shutil
from glob import glob
import re


#%% Functions
file_levels = {
    ## Just duplicates and uncommonly used files
    0: [
        'inputs_case_original',
        os.path.join('inputs_case', 'load_hourly.h5'),
        os.path.join('inputs_case', 'recf_csp.h5'),
        os.path.join('inputs_case', 'recf_distpv.h5'),
        os.path.join('inputs_case', 'recf_upv_140AC.h5'),
        os.path.join('inputs_case', 'recf_upv_220AC.h5'),
        os.path.join('inputs_case', 'recf_upv.h5'),
        os.path.join('inputs_case', 'recf_wind-ofs.h5'),
        os.path.join('inputs_case', 'recf_wind-ons.h5'),
    ],
    ## Intermediate input files plus more duplicates
    1: [
        os.path.join('inputs_case', 'csp.h5'),
        os.path.join('inputs_case', 'temperature_celsius-st.h5'),
        ## The following regex matches the outputs/*.csv files
        ## except for neue*.csv, health*.csv, and h2_price_month.csv.
        ## All the other outputs/*.csv files are duplicates of data in outputs.h5.
        os.path.join('outputs', r'^((?!(neue|health|h2_price_month)).)*csv$'),
    ],
    ## Large input files. Would need to rerun input_processing to recreate.
    2: [
        os.path.join('inputs_case', 'inputs.gdx'),
        os.path.join('inputs_case', 'unitdata.csv'),
        os.path.join('inputs_case', 'hydcf.csv'),
        os.path.join('inputs_case', 'set_allh.csv'),
        os.path.join('inputs_case', 'hintage_data.csv'),
        os.path.join('inputs_case', 'recf.h5'),
        os.path.join('inputs_case', 'load.h5'),
        os.path.join('inputs_case', 'outage_forced_hourly.h5'),
        os.path.join('inputs_case', 'outage_scheduled_hourly.h5'),
    ],
    ## Large output files. Can be regenerated without rerunning the case.
    3: [
        os.path.join('outputs', 'Augur_plots'),
        os.path.join('outputs', 'hourly'),
        os.path.join('outputs', 'figures'),
    ],
    ## Largest output files. Would need to rerun the case to regenerate.
    4: [
        'g00files',
        'ReEDS_Augur',
        ## The following regex matches the rep_{casename}.gdx file written by
        ## e_report.gms (which contains the same data as outputs.h5)
        os.path.join('outputs', '^rep_.*\.gdx$'),
    ]
}


def delete_files(case, file_list, dryrun=0):
    """
    Deletes files in file_list from case
    (unless dryrun is True; then the files that would be deleted are printed instead)
    """
    for file in file_list:
        filepath = os.path.join(case, file)
        if os.path.isdir(filepath):
            if dryrun:
                print(f'Would delete directory: {filepath}')
            else:
                shutil.rmtree(filepath)
        elif '*' in filepath:
            candidate_paths = sorted(glob(os.path.join(os.path.dirname(filepath), '*')))
            candidate_files = [i for i in candidate_paths if os.path.isfile(i)]
            final_files = [
                i for i in candidate_files
                if re.match(os.path.basename(filepath), os.path.basename(i))
            ]
            for f in final_files:
                if dryrun:
                    print(f'Would delete file: {f}')
                else:
                    os.remove(f)
        else:
            if os.path.isfile(filepath):
                if dryrun:
                    print(f'Would delete file: {filepath}')
                else:
                    os.remove(filepath)


def parse_caselist(caselist):
    """Turn a list of globs into a flat list of filepaths"""
    outlist = []
    for caseprefix in caselist:
        outlist.extend(glob(caseprefix))
    return sorted(outlist)


def main(caselist, level=0, dryrun=0, force=0, quiet=0, file_levels=file_levels):
    """
    Deletes files specified by level and file_levels from cases in caselist

    Args:
        caselist (list): List of paths to ReEDS cases
        level (int): Level of file_levels up to which to delete files
        dryrun (bool): If True, print files but don't delete (default False)
        force (bool): If True, proceed without prompting user to confirm (default False)
        file_levels (dict): Map from level to list of filenames

    Returns:
        None
    """
    cases = parse_caselist(caselist)
    if not len(cases):
        print(f'No cases matching "{" ".join(caselist)}"')
        quit()

    file_list = sorted(
        sum([v for k,v in file_levels.items() if k <= level], [])
    )

    if not quiet:
        print('\nDeleting these files:')
        for f in file_list:
            print(f'- {f}')
        print('\nFrom these cases:')
        for c in cases:
            print(f'> {c}')
        if level >= 1:
            print(
                f'WARNING: cleanup level {level} removes files used by R2X, '
                'so do not proceed if you plan to run R2X.'
            )

    if not force:
        confirm = str(input('\nProceed? y/[n]: ') or 'n')
        if confirm.lower() not in ['y', 'yes', 'yeah', 'yup', '1', 'true']:
            quit()

    for case in cases:
        delete_files(case, file_list, dryrun=dryrun)


#%% Procedure
parser = argparse.ArgumentParser(
    description='Remove files from completed ReEDS cases',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    'caselist',
    type=str,
    nargs='+',
    help=(
        'Path to a ReEDS case folder '
        'OR space-delimited list of case folders '
        'OR glob prefix (including *) for a group of case folders'
    ),
)
parser.add_argument(
    '--level',
    '-l',
    type=int,
    default=0,
    help='How aggressively to remove files (larger number = more files)',
)
parser.add_argument('--force', '-f', action='store_true', help='Proceed without double-checking')
parser.add_argument('--dryrun', '-d', action='store_true', help="Print files but don't delete")
parser.add_argument('--quiet', '-q', action='store_true', help="Don't print file/case lists")

args = parser.parse_args()
caselist = args.caselist
level = args.level
force = args.force
dryrun = args.dryrun
quiet = args.quiet

# #%% Inputs for testing
# caselist = [os.path.abspath(os.path.join('..', 'runs', 'v20250221_commonM2_Pacific'))]
# level = 0
# force = 0
# dryrun = 1
# quiet = 0

if __name__ == '__main__':
    main(caselist, level=level, dryrun=dryrun, force=force, quiet=quiet)
