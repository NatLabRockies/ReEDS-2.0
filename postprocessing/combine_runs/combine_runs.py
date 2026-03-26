# -*- coding: utf-8 -*-
"""
Created on Mon May 18 16:21:30 2024

@author: apham
"""

import shutil
import argparse
import os
import pandas as pd
import re
import site
import sys
import subprocess
import traceback
import matplotlib.pyplot as plt
from glob import glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import reeds
from reeds import reedsplots

# print list of cases to run
def print_cases(cases):
    print(f'\nCombining {len(cases)} runs according to the following scenarios:\n')
    print(cases[["full_name", "keyword", "scenario"]])
    print("\n" + "="*shutil.get_terminal_size()[0])

# when inferring runs to combine, check to make sure keywords don't 
# match multiple runs simultaneously
def check_keys(cases, keywords):
    # flag any cases with multiple matches
    multiple_matches = cases.loc[cases.keyword.apply(len) > 1]
    if len(multiple_matches) > 0:
        for i, mm in multiple_matches.iterrows():
            print(f'The run {mm["full_name"]} matches multiple keys: {mm["keyword"]}. '
                    'Please check keyword specifications.')
        error_msg = "Runs cannot be uniquely identified by keywords. Exiting now."
        raise Exception(error_msg)
    cases.keyword = cases.keyword.apply(lambda x: ', '.join(x))
    return cases

# check to make sure there are runs to combine
def check_cases(cases, keywords):
    cases = cases.sort_values(by=['scenario', 'keyword'], ignore_index=True)
    # summarize runs to be combined
    if len(cases) == 0:
        error_msg = ('No runs matched; '
                      'check batch_name and keyword specifications')
        raise Exception(error_msg)
    if len(cases) == len(cases.scenario.unique()):
        print_cases(cases)
        error_msg = ('No unique scenarios identified so there are no runs to be combined; '
                      'check keyword specifications')
        raise Exception(error_msg)
    return cases

def custom_run_file(runlist):
    # read in custom file
    try:
        cases = pd.read_csv(runlist)
    except FileNotFoundError:
        print(f"Error: could not find file {runlist}, check --runlist setting.")
        sys.exit(1)
    # check custom file for the correct columns 
    check_cols = ["full_name", "scenario", "keyword", "path"]
    missing_cols = [c for c in check_cols if c not in cases.columns]
    if len(missing_cols) > 0:
        print(f"Missing {missing_cols} from {runlist} file, please update.")
        sys.exit(1)
    # check that paths make sense
    bad_paths = []
    for path in cases.path:
        if not os.path.exists(path):
            bad_paths.append(path)
    if len(bad_paths) > 0:
        print(f"The following paths could not be found: {bad_paths} "
              f"Check your {runlist} file.")
        sys.exit(1)
    return cases

def get_runs(reeds_path, batch_name, keywords, folder_name_suffix):
    if batch_name is None:
        print("Please specify an argument for --batch_name.")
        sys.exit(1)
    # identify runs corresponding to batch name
    all_cases = glob(os.path.join(reeds_path,'runs',batch_name+'*'))

    # get full scenario names from base of paths
    full_scenario_name = [os.path.basename(c) for c in all_cases]

    # search for instances of the matching keywords in the names
    combine_string =  "_*(" + "|".join(keywords) + ")"
    matches = [re.findall(combine_string, c, flags=re.IGNORECASE) for c in full_scenario_name]
    # remove matches to create a 'base scenario' for each set of runs
    base_scenario = [re.sub(combine_string, "", c, flags=re.IGNORECASE) for c in full_scenario_name]
    
    # create data frame of matches
    cases = pd.DataFrame({'full_name':full_scenario_name, 'scenario': base_scenario, 'keyword': matches, 'path':all_cases})

    # drop rows with no matched keywords
    no_matches = cases.loc[cases.keyword.apply(len) == 0]
    cases = cases.loc[cases.keyword.apply(len) > 0]
    print(f'Detected {len(all_cases)} runs matching with the batch name {batch_name}.')
    if len(no_matches) > 0:
        print(f'Ignoring {len(no_matches)} folder(s) with no matching keyword from {keywords}.')

    # drop cases that have the folder suffix in them (these are previously combined runs)
    cases = cases.loc[~cases.scenario.str.contains(folder_name_suffix)]
    # check to make sure no scenario matches more than 1 keyword
    cases = check_keys(cases, keywords)
    return cases

# load file from a run
def read_file(filepath, header='infer'):
    if os.path.isfile(filepath):
        df = pd.read_csv(filepath, header=header)  
        return df
    else:
        print(f"\n...could not read {filepath}, skipping.", end="") 

# load all files from runs to be combined
def read_all_files(combine_cases, filename, filerow):
    li_combined = []
    for __, caserow in combine_cases.iterrows():
        filepath = os.path.join(caserow.path,filerow.folder,filename + ".csv")
        if filerow.header == "none":
            df = read_file(filepath, header=None)
        else:
            df = read_file(filepath)
        if df is not None:
            li_combined.append(df)
    if len(li_combined) == 0:
        raise UserWarning
    else:
        df_combined = pd.concat(li_combined, axis=0)
        return df_combined

# combines csv files from runs
def combine_scenario_files(scenario, combine_cases, reeds_path, output_path):
    print(f"Combining {combine_cases.full_name.to_list()} into {os.path.basename(output_path)}\n")
    output_dir = os.path.join(output_path,'outputs')
    input_dir = os.path.join(output_path,'inputs_case')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)

    # get list of files to combine
    combinefiles = pd.read_csv(os.path.join(reeds_path, "postprocessing", "combine_runs",
                                            "combinefiles.csv"), index_col="filename")
    # iterate over file list
    for filename, filerow in combinefiles.iterrows():
        if pd.isna(filerow.method):
            print(f"No method implemented for {filename}, skipping.")
            continue
        else:
            print(filename + " --> " + filerow.method, end="")

        # handle empty folder as string (indicates root of run folder)
        if pd.isna(filerow.folder):
            filerow.folder = ""
        
        # merge files according to the method specified 
        try:
            if filerow.method == "concatenate":
                df_out = read_all_files(combine_cases, filename, filerow)
            elif filerow.method == "sum":
                df_combined = read_all_files(combine_cases, filename, filerow)
                # typically sum the 'Value' column and preserve the others
                sum_over_cols = df_combined.columns.drop(filerow.sumcol).to_list()
                df_out = df_combined.groupby(sum_over_cols, as_index=False)[filerow.sumcol].sum()
            elif filerow.method == "keepfirst":
                df_combined = read_all_files(combine_cases, filename, filerow)
                df_out = df_combined.drop_duplicates(keep="first")
            else:
                raise NotImplementedError(f"{filerow.method} not implemented")
            
            # write out file
            if filerow.header == 'none':
                df_out.to_csv(os.path.join(output_path, filerow.folder, 
                                                filename+".csv"),index=False,header=False)
            else:
                df_out.to_csv(os.path.join(output_path, filerow.folder, 
                                                filename+".csv"),index=False)            
        except UserWarning:
            print(f"\nCould not find any files named {filename}.csv. "
                   "Skipping, but check your run folder to verify runs have this file."
            )
    
    print(f"\nFinished processing {scenario}\n")

# combines runs specified in cases list and runs any postprocessing,
# such as reedsplots and bokehpivot 
def run_combine_case(scen, reeds_path, output_path):
    ## Setup
    # logging
    site.addsitedir(reeds_path)
    from reeds.log import makelog
    makelog(scriptname=__file__, logpath=os.path.join(output_path,'combine_log.txt'))
    # read in details on cases to combine
    combine_case = pd.read_csv(os.path.join(output_path, 'cases_combined.csv'))

    ## Combine csv files
    combine_scenario_files(scen, combine_case, reeds_path, output_path)

    ## Run bokehpivot report of newly combined outputs
    bokeh_path =  os.path.join(reeds_path, 'postprocessing', 'bokehpivot')
    site.addsitedir(os.path.join(bokeh_path))
    site.addsitedir(os.path.join(bokeh_path, 'reports'))
    import interface_report_model as bokeh
    try:
        bokeh.run_report("ReEDS 2.0", output_path, "all", "No", "none",
                        os.path.join(bokeh_path, 'reports','templates','reeds2','standard_report_combined.py'),
                        "html,excel,csv", "one",
                        os.path.join(output_path, 'outputs', 'reeds-report-combined'), "No"
                        )   
    except Exception:
        print("Error running bokeh.")
        print(traceback.format_exc())

    # Map properties:
    wscale = 0.0003
    alpha = 0.8
    case=output_path
    nrows=1
    ncols=1
    
    # get end year from first run. assumes all runs were run with the same endyear.
    sw = reeds.io.get_switches(combine_case.path[0])
    yearend = int(sw.endyear)

    # Map colors:
    trtypes = pd.read_csv(os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
                          index_col='raw')['display']
    colors = pd.read_csv(os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
                         index_col='order')['color']
    colors = pd.concat([colors, trtypes.map(colors)])

    for subtract_baseyear in [None, 2020]:
        plt.close()
        f,ax = plt.subplots(nrows, ncols, figsize=(13.33, 6.88), gridspec_kw={'wspace':0.0,'hspace':-0.1},)
    
        try:
            reedsplots.plot_trans_onecase(case=case, level='r', pcalabel=False, wscale=wscale,
                                          yearlabel=True, year=yearend, simpletypes=None,
                                          alpha=alpha, scalesize='x-large',
                                          f=f, ax=ax, title=False,
                                          subtract_baseyear=subtract_baseyear,
                                          show_overlap=True, show_converters=0.5,
                                          crs='ESRI:102008', thickborders='transreg', 
                                          drawstates=True, drawzones=True,
                                          label_line_capacity=10, scale=True)
            
            ax.annotate('AC', (-1.75e6, -1.12e6), ha='center', va='top',
                        weight='bold', fontsize=15, color=colors['ac'])
            ax.annotate('LCC DC',(-1.75e6, -1.24e6), ha='center', va='top',
                        weight='bold', fontsize=15, color=colors['lcc'])
            ax.annotate('B2B',(-1.75e6, -1.36e6), ha='center', va='top',
                        weight='bold', fontsize=15, color=colors['b2b'])
            ax.annotate('VSC DC', (-1.75e6, -1.48e6), ha='center', va='top',
                        weight='bold', fontsize=15, color=colors['vsc'])
            ax.axis('off')

            ## Save map
            map_path = os.path.join(output_path, 'outputs', 'figures')
            if not os.path.exists(map_path):
                os.makedirs(map_path)
            
            end = '-since '+str(subtract_baseyear) if subtract_baseyear else ''
            mapname = f'map_translines_all-{yearend}{end}.png'
            maptitle = os.path.basename(os.path.normpath(output_path))+' ('+str(yearend)+ end + ')'
            ax.set_title(maptitle)
            plt.savefig(os.path.join(map_path, mapname), dpi=600, bbox_inches='tight')     
        except Exception:
            print('map_translines_all failed:')
            print(traceback.format_exc())
          
    ## Create combined VRE capacity + transmission maps
    transalpha = 0.25
    transcolor = 'k'
    ms = 1.15
    wscale_straight = 0.0004
    gen_cmap = {'wind-ons':plt.cm.Blues,
                'upv':plt.cm.Reds,
                'wind-ofs':plt.cm.Purples,
                }
    for show_transmission in [True, False]:
        plt.close()
        try:
            f,ax = reedsplots.plot_vresites_transmission(case=case, year=yearend, crs='ESRI:102008', cm=gen_cmap,
                                                         wscale=wscale_straight, show_overlap=True,
                                                         subtract_baseyear=None, show_transmission=show_transmission,
                                                         alpha=transalpha, colors=transcolor, ms=ms)
            
            ## Save map
            end = '-translines' if show_transmission is True else ''
            mapname = f'map_VREsites{end}-{yearend}.png'
            #maptitle = os.path.basename(os.path.normpath(output_path))+' ('+str(yearend)+ end + ')'
            #ax.set_title(maptitle)
            plt.savefig(os.path.join(map_path, mapname), dpi=600, bbox_inches='tight')

        except Exception:
            print('map_VREsite-translines failed:')
            print(traceback.format_exc())    


# writes submission script for the HPC
def write_hpc_file(scen, reeds_path, output_path, hpc_settings):
    hpc_file = os.path.join(output_path, scen+".sh")
    with open(hpc_file, 'w') as SPATH:
        SPATH.writelines("#!/bin/bash\n")
        SPATH.writelines(f"#SBATCH --account={hpc_settings['account']}\n")
        if hpc_settings['priority']:
            SPATH.writelines("#SBATCH --priority=high\n")
        if hpc_settings['debugnode']:
            SPATH.writelines("#SBATCH --partition=debug\n")
            SPATH.writelines("#SBATCH --time=1:00:00\n")
        else:
            SPATH.writelines(f"#SBATCH --time={hpc_settings['walltime']}\n")
        SPATH.writelines("#SBATCH --job-name=" + scen + "\n")
        SPATH.writelines("#SBATCH --output=" + os.path.join(output_path, "slurm-%j.out") + "\n\n")
        SPATH.writelines("#load your default settings\n")
        SPATH.writelines(". $HOME/.bashrc" + "\n\n")
        SPATH.writelines("conda activate reeds2 \n")  
        SPATH.writelines(f"cd {os.path.join(reeds_path, 'postprocessing', 'combine_runs')}\n")            
        SPATH.writelines(f"python hpc_runner.py {scen} {reeds_path} {output_path}")
    return hpc_file

# sets up call to run_combine_case function, either locally 
# or submitted to the HPC, with arguments specified via command line
def main(reeds_path, batch_name, folder_name_suffix, runlist, keywords, local, dryrun, hpc_settings):
    print("="*shutil.get_terminal_size()[0])
    print("Running combine_runs.py.")

    ## get list of the runs with files to be combined
    # option 1: user-specified file
    if runlist is not None:
        cases = custom_run_file(runlist)
        keywords = list(cases.keyword.unique())
    # option 2: infer runs in ReEDS runs folder based on batch name and keywords
    else:
        cases = get_runs(reeds_path, batch_name, keywords, folder_name_suffix)
    
    # check and print
    cases = check_cases(cases, keywords)
    print_cases(cases)

    # end here if only conducting a dry-run
    if dryrun:
        print("dry-run; exiting script now.")
        sys.exit(0)

    # if we're on the hpc and the local flag isn't on assume we're submitting to slurm 
    # iterate over the scenarios
    scens = cases.scenario.unique()
    for scen in scens:
        # Create folders for combined outputs 
        folder_name = scen + "_" + folder_name_suffix
        output_path = os.path.join(reeds_path, "runs", folder_name)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        else:
            print(f"{output_path} already exists, will overwrite")
            shutil.rmtree(output_path)
            os.makedirs(output_path)
        # save case mapping
        combine_case = cases.loc[cases.scenario == scen].copy()
        combine_case.to_csv(os.path.join(output_path, 'cases_combined.csv'), index=False)
        # check if run should be submitted to HPC or run directly
        hpc = True if ('NREL_CLUSTER' in os.environ) else False
        if hpc and local:
            print(
                "Note: you are on the HPC but are running locally on your current node. "
                "If you are on a login node the run may fail due to insufficient memory."
            )
            confirm_local = str(input('Proceed? [y]/n: ') or 'y')
            if confirm_local not in ['[y]', 'y','Y','yes','Yes','YES']:
                print("Quitting combine_runs.py now.")
                quit()
        ## HPC
        if hpc and not local:
            # check for allocation account
            if hpc_settings['account'] is None:
                hpc_settings['account'] = str(
                    input('Specify hpc allocation account ("q" to quit): '))
                if hpc_settings['account'] == 'q':
                    sys.exit(0)
            # write hpc file
            hpc_file = write_hpc_file(scen, reeds_path, output_path, hpc_settings)
            # call file
            batchcom = "sbatch " + hpc_file
            subprocess.Popen(batchcom.split())
        ## LOCAL
        else:
            if 'reeds2' not in os.environ['CONDA_DEFAULT_ENV'].lower():
                print('Caution: you are running locally but have not activated '
                      'the "reeds2" environment.'
                      )
            run_combine_case(scen, reeds_path, output_path)                    
        
    print("Completed combine_runs.py")

if __name__ == '__main__':
    reeds_path = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
     
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(
        description='Combine regional runs into one national run',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--batch_name', '-b', type=str,
                        help='''Batch name common across all runs. Runs will be combined based on 
                        scenario name, which is the part of the run left after removing the 
                        batch name and any matched keywords.''')
    parser.add_argument('--folder_name_suffix', '-f', type=str, default='combined',
                        help='''Suffix to append to scenario name to create the name 
                        of the output folder that stores the combined outputs. 
                        Default of "combined" results in where scenario + "_combined", where 
                        scenario is the  part of the run name shared across the runs being joined.''')
    parser.add_argument('--runlist', '-r', type=str, default=None,
                        help='''optional path to csv file that specifies runs to combine and their paths; 
                        useful if you are trying to combine runs from different ReEDS folder.
                        See 'runlist.csv' file for format and description of required entries.''')
    parser.add_argument('--keywords', '-k', nargs='+', default=['east','west','ercot'],
                        help='1 or more strings with keywords for runs that should be combined.')
    parser.add_argument('--time', '-t', type=str, default='4:00:00',
                        help='Walltime to request for HPC run.')
    parser.add_argument('--account', '-a', type=str,
                        help='Account to use for HPC run.')
    parser.add_argument('--priority', '-p', default=False, action='store_true',
                        help='Use high priority for HPC run.')
    parser.add_argument('--debugnode', '-d', default=False, action='store_true',
                        help='Use debug node for HPC run.')
    parser.add_argument('--local', '-l', default=False, action='store_true',
                        help='Force all cases to run locally (if on HPC will run on login node).')
    parser.add_argument('--dryrun', default=False, action='store_true',
                        help='''Look at runs to combine with combining; useful for previewing set of
                        runs to be combined without actually running.''')

    args = parser.parse_args()
    batch_name = args.batch_name
    folder_name_suffix = args.folder_name_suffix
    runlist = args.runlist    
    keywords = args.keywords
    local = args.local
    dryrun = args.dryrun

    ## For debugging:
    #batch_name = '20240607_splicetest'
    #keywords = ['ERCOT', 'Pacific']

    hpc_settings = {"account": args.account,
                    "walltime": args.time,
                    "priority" : args.priority,
                    "debugnode": args.debugnode,
                    }   
    
    main(reeds_path, batch_name, folder_name_suffix, runlist, keywords, local, dryrun, hpc_settings)