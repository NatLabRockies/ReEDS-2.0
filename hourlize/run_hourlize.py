"""
Sets up hourlize call(s) to load.py or resource.py.
See hourlize README for setup and details.
"""

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import argparse
import datetime
import json
import os
import pandas as pd
import re
import shutil
import subprocess
import sys
import traceback
from collections import OrderedDict

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def get_remote_path(local):
    """detect path to supply curve files either on the HPC or nrelnas01"""
    # remote path for supply curves
    hpc = True if ('NREL_CLUSTER' in os.environ) else False
    if hpc:
        #For running hourlize on the HPC link to shared-projects folder
        if os.environ.get('NREL_CLUSTER') == 'kestrel':
            remotepath = '/kfs2/shared-projects/reeds'
        elif os.environ.get('NREL_CLUSTER') == 'eagle':
            remotepath = '/shared-projects/reeds'
        else:
            raise Exception(f"Detected {os.environ.get('NREL_CLUSTER')} as NLR Cluster; "
                            "only 'eagle' and 'kestrel' are supported")
    else:
        # if not on the hpc running link to nrelnas01 and set local to true
        remotepath = os.path.join(
            ('/Volumes' if sys.platform == 'darwin' else '//nrelnas01'), 'ReEDS'
            )
        local = True

    # check remote connection
    if not os.path.exists(remotepath):
        print(
            f"Remote directory {remotepath} not detected. "
            "Check path and connection before running."
            )
        quit()

    # confirm local run if on hpc
    if hpc and local:
        print(
            "Note: you are on the HPC but are running locally on your current node. "
            "If you are on a login node the run may fail due to insufficient memory."
        )
        confirm_local = str(input('Proceed? [y]/n: ') or 'y')
        if confirm_local not in ['[y]', 'y','Y','yes','Yes','YES']:
            print("Exiting hourlize now.")
            quit()

    return remotepath, local


def make_output_dir(casename):
    """creates output case folder"""
    ## setup output directory
    outpath = os.path.join(hourlize_path, 'out', casename)
    if os.path.exists(outpath):
        if args.archive:
            time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            os.rename(outpath, outpath + '-archive-' + time)
        else:
            shutil.rmtree(outpath)
    os.makedirs(outpath, exist_ok=True)
    os.makedirs(os.path.join(outpath, 'inputs'), exist_ok=True)
    os.makedirs(os.path.join(outpath, 'results'), exist_ok=True)

    return outpath


def string_formatter(var, config, verbose=False):
    """
    helper function replace instances of {var} with the corresponding variable value
    for a given string, using either global variable or another config defintion.
    """
    # find string patterns to fill
    varout = var
    formatvars = re.findall("{.*?}", varout)
    newvals = {}
    # iterate over string patterns to replace
    for fv in formatvars:
        fvval = re.sub("{|}", "", fv)

        # check if this is an expression to evaluate
        if "eval_" in fvval:
            try:
                newval = eval(re.sub("eval_", "", fvval))
                if verbose:
                    print(f"Evaluating expression in {newval}.")
            except Exception as err:
                print(err)
                raise Exception("The expression could not be evaluated; check your config file.")
        # next check if there is a defined variable that can be used to fill in the value
        elif fvval in globals():
            newval = globals()[fvval]
        # after that check config definitions
        elif fvval in config.keys():
            newval = config[fvval]
        # if no definition is found raise error
        else:
            raise Exception(f"{fvval} is not a defined variable or expression; check your config file.")
        newvals.update([(f"{fvval}", newval)])

    # create formatted output
    if "eval_" in fvval and len(formatvars) == 1:
        varout = newvals[fvval]
    else:
        varout = varout.format(**newvals)
    if verbose:
        print(f"updated {var} --> {varout}")

    return varout


def config_string_formatter(config, verbose):
    """
    function to auto-format all instances {var} in config with the appropriate variable,
    using iterative calls to 'string_formatter
    """
    # loop over config variables
    for var in config:
        if isinstance(config[var], str) and bool(re.search("{.*}", config[var])):
            config[var] = string_formatter(config[var], config, verbose)
        # special treatment for lists within a variable
        elif isinstance(config[var], list):
            varlist = config[var]
            for i in range(0, len(varlist)):
                if isinstance(varlist[i], str) and bool(re.search("{.*}", varlist[i])):
                    varlist[i] = string_formatter(varlist[i], config, verbose)


def load_base_config(config_base=None):
    """loads specified config_base json file"""
    # first load base config
    if config_base is not None:
        config_base  = f"config_base_{config_base}.json"
    else:
        config_base = "config_base.json"
    cpathbase = os.path.join(hourlize_path, "inputs", "configs", config_base)
    with open(cpathbase, "r") as f:
        config = json.load(f, object_pairs_hook=OrderedDict)

    return config


def launch_batch_file(casename, configpath, outpath, args):
    """
    launches hourlize run, either by submitting jobs to the HPC or initiating
    a call to load.py or resource.py
    """
    # setup script to run each case
    ext = '.sh' if os.name == 'posix' else '.bat'
    with open(os.path.join(outpath, casename + "_run" + ext), 'w+') as OPATH:
        if os.environ.get('NREL_CLUSTER') == 'kestrel':
            OPATH.writelines("source /nopt/nrel/apps/env.sh \n")
            OPATH.writelines("module load anaconda3 \n")
            OPATH.writelines("conda activate reeds2 \n\n")
        elif os.environ.get('NREL_CLUSTER') == 'eagle':
            OPATH.writelines("module load conda \n")
            OPATH.writelines("conda activate reeds2 \n\n")
        # run hourlize
        OPATH.writelines(f"cd {hourlize_path}\n")
        if args.nolog:
            OPATH.writelines(f"python {args.mode}.py --config {configpath} --nolog\n")
        else:
            OPATH.writelines(f"python {args.mode}.py --config {configpath}\n")

    # launch run locally or submit to hpc
    if args.local:
        if args.nosubmit:
            print(f"Run script and output folder created for {casename} but run not submitted\n")
        else:
            print("Starting the run for case " + casename)
            if os.name!='posix':
                terminal_keep_flag = ' /k '
                os.system('start /wait cmd' + terminal_keep_flag + os.path.join(outpath, casename + "_run" + ext))
            if os.name=='posix':
                # Give execution rights to the shell script
                os.chmod(os.path.join(outpath, casename + "_run" + ext), 0o777)
                # Open it up - note the in/out/err will be written to the shellscript parameter
                shellscript = subprocess.Popen(
                    [os.path.join(outpath, casename + "_run" + ext)], shell=True)
                # Wait for it to finish before killing the thread
                shellscript.wait()
    else:
        # set up batch script
        shutil.copy(os.path.join(hourlize_path, "inputs", "configs", "srun_template.sh"),
                    os.path.join(outpath, casename+"_batch.sh"))

        # option for running on an hpc debug node
        if args.debugnode:
            writelines = []
            # comment out original time specification
            with open(os.path.join(outpath, casename+"_batch.sh"), 'r') as SPATH:
                for L in SPATH:
                    writelines.append(('# ' if '--time' in L else '') + L.strip())
            # rewrite file with new time and debug partition
            with open(os.path.join(outpath, casename+"_batch.sh"), 'w') as SPATH:
                for L in writelines:
                    SPATH.writelines(L + '\n')
                SPATH.writelines("#SBATCH --time=01:00:00\n")
                SPATH.writelines("#SBATCH --partition=debug\n")

        ## modify batch script for run
        with open(os.path.join(outpath, casename+"_batch.sh"), 'a') as SPATH:
            # Add the name for easy tracking of the case
            SPATH.writelines("#SBATCH --job-name=" + casename + "\n")
            SPATH.writelines("#SBATCH --output=" + os.path.join(outpath, "slurm-%j.out") + "\n")
            SPATH.writelines("\n. $HOME/.bashrc # load default settings\n\n\n")
            # Add the call to the sh file created throughout this function
            SPATH.writelines("sh " + os.path.join(outpath, casename + "_run.sh"))
        SPATH.close()

        ## launch job
        batchcom = "sbatch " + os.path.join(outpath, casename + "_batch.sh")
        if args.verbose:
            print(f"Batch command: {batchcom}")

        if args.nosubmit:
            print(f"Run script and output folder created for {casename} but run not submitted\n")
        else:
            subprocess.Popen(batchcom.split())
            print(f"Submitted {casename}\n")


def copy_files(casename, configout, outpath, args):
    """function to copy relevant files to output folder"""
    # resource script
    shutil.copy2(os.path.join(hourlize_path, f'{args.mode}.py'),
                 os.path.join(os.path.join(outpath, 'inputs')))

    # inputs (specified by 'inputfiles' in base config)
    for input in configout['inputfiles']:
        if configout[input] is not None:
            shutil.copy(os.path.join(configout[input]), os.path.join(outpath, "inputs"))

    # add path info to final config
    configout.update({"casename": casename, "outpath":outpath,
                      "reeds_path": reeds_path, "hourlize_path": hourlize_path})

    # dump config file as json file
    configout = json.dumps(configout, indent=4, sort_keys=True)
    configpath = os.path.join(outpath, "inputs", "config.json")
    with open(configpath, "w") as outfile:
        outfile.write(configout)

    return configpath


def check_config_value(configs, entry, format=False, format_config={}):
    """
    helper function that will check for duplicate values for 'entry' across a list of
     config files and use the first one if finds
    """
    output = None
    for config in configs:
        # break loop after finding first matching value
        if entry in config.keys():
            output = config[entry]
            break

    if output is None:
        raise Exception(
            """Entry for 'subsetvars' not found in any config file. Please specify a list of variables
              from which to subset the rev supply curves before continuing"""
              )
    else:
        # option to format variable as needed
        if format:
            output = string_formatter(output, format_config, args.verbose)
        return output


def check_cols(sc_file, hourlize_path, req_cols=[], opt_cols=[]):
    """check rev supply curve for columns needed by hourlize"""
    # get supply curve columns
    if isinstance(sc_file, pd.DataFrame):
        sc_cols = sc_file.columns.tolist()
        sc_file = "provided"
    else:
        sc_cols = pd.read_csv(sc_file, nrows=0).columns.tolist()

    # for geothermal, create a mapping to change old column headers to new
    rev_sc_colnames = pd.read_csv(os.path.join(hourlize_path, "inputs", "resource", "rev_sc_columns.csv"))
    rev_cols_mapping = dict(zip(rev_sc_colnames['legacy_colname'], rev_sc_colnames['new_colname']))

    # update old column headers in sc_cols
    sc_cols = [rev_cols_mapping.get(col, col) for col in sc_cols]

    # create a list of columns to exclude these from missing columns check
    exclude_cols = {
        'mean_cf',
        'cost_spur_usd_per_mw',
        'cost_poi_usd_per_mw',
        'cost_export_usd_per_mw',
        'cost_reinforcement_usd_per_mw',
        'cost_total_trans_usd_per_mw',
        'multiplier_cc_eos',
        'multiplier_cc_regional',
        'dist_reinforcement_km',
        'dist_spur_km',
    }

    # these are columns that are required by hourlize; if the supply curve is missing one
    # of these an error will be thrown
    req_missing = [c for c in req_cols if c not in sc_cols and c not in exclude_cols]

    # these are columns that are used but for which hourlize can make reasonable default
    # assumption; if the supply curve is missing one of these warn the user but proceed
    opt_missing = [c for c in opt_cols if c not in sc_cols]

    if len(req_missing) > 0:
        error_msg = (f"The rev supply curve file {sc_file} is missing the following columns "
                     f"required by hourlize: {req_missing}. This run will not be executed; check supply curve file "
                      "and column specifications in your hourlize config files."
                    )
        raise Exception(error_msg)
    elif len(opt_missing) > 0:
        warn_msg = (f"Warning: the rev supply curve file {sc_file} is missing the following columns "
                    f"used by hourlize: {opt_missing}.\nThese columns can be filled in with default values "
                    "by hourlize, but if you are expecting values for these check your supply curve file."
                    )
        print(warn_msg)
    else:
        print("All columns needed by hourlize were found in the supply curve file.")

    return req_missing, opt_missing


def setup_resource_run(casename, case, args):
    """function to set up and submit each resource case to run"""
    if args.verbose:
        print(f"Setting up resource.py call for {casename}")

    ## load relevant config files
    # base config (can overwride default choice entry in cases json)
    if 'config_base' in case:
        config = load_base_config(case['config_base'])
    else:
        config = load_base_config()
    # tech config
    if 'config_tech' in case:
        configtech  = f"config_{case['tech']}_{case['config_tech']}.json"
    else:
        configtech = f"config_{case['tech']}.json"
    cpathtech = os.path.join(hourlize_path, "inputs", "configs", configtech)
    with open(cpathtech, "r") as f:
        configtech = json.load(f, object_pairs_hook=OrderedDict)

    ## make output folder
    outpath = make_output_dir(casename)

    ## get rev information
    rev_paths_file = check_config_value([case, configtech, config['resource']], 'rev_paths_file', format=True)
    if not os.path.exists(rev_paths_file):
        raise Exception(f"No 'rev_paths' file detected, check path in config: {rev_paths_file}")
    df_rev = pd.read_csv(rev_paths_file)

    ## subset to rev_paths file to the relevant rev path used for this run
    # typically this is based on tech/access case but users can specify additional options
    subsetvars = check_config_value([case, configtech, config['resource']], 'subsetvars')
    df_rev_case = df_rev
    for var in subsetvars:
        if var not in case:
            raise Exception(f"{var} not specified in cases dictionary")
        df_rev_case = df_rev_case[(df_rev_case[var] == case[var])]

    # check to make sure there is a valid rev_paths option and not more than 1 rev path has been matched
    if df_rev_case.shape[0] == 0:
        raise Exception("No rev_paths found; check definitions in rev_paths file and modify cases and subsetvars.")
    elif df_rev_case.shape[0] > 1:
        raise Exception("More than 1 rev_path found; check definitions in rev_paths file and add conditions to subsetvars.")
    else:
        dct_rev = df_rev_case.squeeze().to_dict()

    # update relevant categories with full rev path information
    # rev_cases_path should have files for each year with hourly generation data for each supply curve point
    # or gen_gid, called [rev_case]_rep-profiles_[select_year].h5.
    #for rev_info in ['rev_path', 'sc_path']:
    #    case[rev_info] = os.path.join(remotepath, "Supply_Curve_Data", dct_rev[rev_info])
    case['rev_case'] = dct_rev['rev_case']
    case['sc_path'] = os.path.join(remotepath, "Supply_Curve_Data", dct_rev['sc_path'])
    case['rev_path'] = os.path.join(remotepath, "Supply_Curve_Data", dct_rev['sc_path'], "reV", dct_rev['rev_case'])
    case['original_sc_file'] = os.path.join(remotepath, "Supply_Curve_Data", dct_rev['sc_path'], "reV", dct_rev['original_sc_file'])
    case['sc_file'] = os.path.join(outpath, 'results', case['tech'] + '_supply_curve_raw.csv')
    case['rev_paths_file'] = rev_paths_file

    # create combined config for run (add tech config later after additional processing)
    # order of dictionary merges here means that the precedence for overridding duplicated entries
    # is case > configtech > resource config > shared config
    configout = {**config['shared'], **config['resource'], **configtech, **case}
    config_string_formatter(configout, args.verbose)

    ## this section checks the supply curve file for columns needed by hourlize

    # first identify any columns specified as needed by the config files
    config_col_list = ['capacity_col', 'class_bin_col', 'profile_id_col', 'filter_cols']
    config_cols = []
    for cc in config_col_list:
        if isinstance(configout[cc], list):
            config_cols.extend(configout[cc])
        elif isinstance(configout[cc], OrderedDict):
            keys = configout[cc].copy()
            # don't check for capacity from filter list since we add that column in later
            if 'capacity' in keys:
                del keys['capacity']
            if len(keys) > 0:
                config_cols.extend(keys)
        else:
            config_cols.append(configout[cc])

    # next check for the coloumns that are always supposed to be present
    rev_cols = pd.read_csv(os.path.join(hourlize_path, "inputs", "resource", "rev_sc_columns.csv"))
    # subset to just the ones needed by hourlize or ReEDS
    req_cols_all = rev_cols.loc[rev_cols.used_by_hourlize == "X", "new_colname"].to_list()

    # now check for missing columns
    if(not (case['tech']=='egs' or case['tech']=='geohydro')):
        check_cols(case['original_sc_file'], hourlize_path, config_cols + req_cols_all)
    else:
        print(
            "Skipping column check for geothermal technologies as supply curve is "
            "aggregated from multiple files in resource.py"
        )

    ## copy input files to run folder
    configpath = copy_files(casename, configout, outpath, args)

    ## launch case
    launch_batch_file(casename, configpath, outpath, args)


def setup_resource(args):
    """procedure for setting up resource.py runs"""
    ## Cases to run
    # load cases from json using specified suffix (default: "cases_default.json")
    if args.cases == "default":
        print("Loading cases from cases.json")
        casepath = os.path.join(hourlize_path, "inputs", "configs", "cases.json")
    else:
        print(f"Loading cases from cases_{args.cases}.json")
        casepath = os.path.join(hourlize_path, "inputs", "configs", f"cases_{args.cases}.json")
    # confirm that cases file exists
    if not os.path.exists(casepath):
        raise Exception(f"Could not find cases json at {casepath}.")
    # load cases
    with open(casepath, "r") as f:
        cases = json.load(f, object_pairs_hook=OrderedDict)

    print("\nSetting up resource.py runs for the following cases:\n")
    for c in cases:
        print(c)
    print(f"\nTotal: {len(cases)} case(s)\n")

    ## Main loop for running cases
    for casename in cases:
        print("-"*65)
        print(casename + '\n')
        try:
            setup_resource_run(casename=casename, case=cases[casename], args=args)
        except Exception:
            print(f"Error running {casename}\n")
            traceback.print_exc()
            print(f"\nSkipping {casename}.")
            continue
    print("-"*65)
    print("All resource runs set up")


def setup_load(args):
    """procedure for setting up load.py runs"""

    # load config
    config = load_base_config()
    configout = {**config['load'], **config['shared']}
    config_string_formatter(configout, args.verbose)

    # setup run folder
    casename = os.path.basename(configout['load_source'])
    outpath = make_output_dir(casename)

    # copy input files to run folder
    configpath = copy_files(casename, configout, outpath, args)

    # launch case
    launch_batch_file(casename, configpath, outpath, args)


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================
if __name__== '__main__':
    ## Command line arguments to script
    parser = argparse.ArgumentParser(description='Sets up hourlize resource or load runs.')
    parser.add_argument('mode', type=str,
                        choices=['load', 'resource'],
                        help='Setup runs for load.py or resource.py?')
    parser.add_argument('--cases', '-c', type=str, default='default',
                    help='Suffix for cases json file (currently only used for resource.py)')
    parser.add_argument('--debugnode', '-d', default=False, action='store_true',
                    help='Run using debug specifications for slurm on an hpc system')
    parser.add_argument('--local', '-l', default=False, action='store_true',
                    help='Run all cases locally (if on HPC will run on current node)')
    parser.add_argument('--nosubmit', '-n', default=False, action='store_true',
                    help='Only create config and output folders without submitting to the HPC or running')
    parser.add_argument('--archive', '-a', action="store_true",
                    help='Archive existing hourlize output folder if it exists instead of overwriting')
    parser.add_argument('--verbose', '-v', default=False, action='store_true',
                    help='Prints more output to the console for setting up run (useful for debugging in run_hourlize.py)')
    parser.add_argument('--nolog', '-g', default=False, action='store_true', help='turn off logging for debugging')

    args = parser.parse_args()

    # #%% Settings for testing
    # class Args:
    #     def __init__(self):
    #         self.mode = 'resource'
    #         self.cases = 'default'
    #         self.debugnode = False
    #         self.local = True
    #         self.nosubmit = False
    #         self.archive = True
    #         self.verbose = True
    #         self.nolog = True
    # args = Args()

    #%% set paths
    hourlize_path = os.path.dirname(os.path.realpath(__file__))
    reeds_path = os.path.abspath(os.path.join(hourlize_path, ".."))
    remotepath, args.local = get_remote_path(args.local)

    #%% run setup
    print(f"\nSetting up hourlize calls to {args.mode}.py")
    if args.mode == "load":
        setup_load(args)
    elif args.mode == "resource":
        setup_resource(args)
    else:
        print("Unsupported method for hourlize")
    print(f"Hourlize setup for {args.mode}.py complete\n")
