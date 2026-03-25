#%% IMPORTS
import os
import sys
import queue
import threading
import time
import shutil
import csv
import numpy as np
import pandas as pd
import subprocess
from datetime import datetime
import argparse
from builtins import input
from glob import glob

#############
#%% FUNCTIONS

def writeerrorcheck(checkfile, errorcode=17):
    """
    Inputs
    ------
    checkfile: Filename to check. If it does not exist, stop the run.
    errorcode: Value to return if check fails. Should be >0.
    """
    if os.name == 'posix':
        return f'if [ ! -f {checkfile} ]; then echo "missing {checkfile}"; exit {errorcode}; fi\n'
    else:
        return f'\nif not exist {checkfile} (\n echo file {checkfile} missing \n goto:eof \n) \n \n'

def writescripterrorcheck(script, errorcode=18):
    """
    """
    if os.name == 'posix':
        return f'if [ $? != 0 ]; then echo "{script} returned $?" >> gamslog.txt; exit {errorcode}; fi\n'
    else:
        return f'if not %errorlevel% == 0 (echo {script} returned %errorlevel%\ngoto:eof\n)\n'


def write_delete_file(checkfile, deletefile, PATH):
    if os.name=='posix':
        PATH.writelines(f"if [ -f {checkfile} ]; then rm {deletefile}; fi\n")
    else:
        PATH.writelines("if exist " + checkfile + " (del " + deletefile + ')\n' )


def comment(text, PATH):
    commentchar = '#' if os.name == 'posix' else '::'
    PATH.writelines(f'{commentchar} {text}\n')


def big_comment(text, PATH):
    commentchar = '#' if os.name == 'posix' else '::'
    PATH.writelines(f'\n{commentchar}\n')
    comment(text, PATH)
    PATH.writelines(f'{commentchar}\n')


def get_ivt_numclass(reeds_path, casedir, caseSwitches):
    """
    Extend ivt if necessary and calculate numclass
    """
    ivt = pd.read_csv(
        os.path.join(
            reeds_path, 'inputs', 'userinput', 'ivt_{}.csv'.format(caseSwitches['ivt_suffix'])),
        index_col=0)
    ivt_step = pd.read_csv(os.path.join(reeds_path, 'inputs', 'userinput', 'ivt_step.csv'),
                           index_col=0, squeeze=True)
    lastdatayear = max([int(c) for c in ivt.columns])
    addyears = list(range(lastdatayear + 1, int(caseSwitches['endyear']) + 1))
    num_added_years = len(addyears)
    ### Add v for the extra years
    ivt_add = {}
    for i in ivt.index:
        vlast = ivt.loc[i,str(lastdatayear)]
        if ivt_step[i] == 0:
            ### Use the same v forever
            ivt_add[i] = [vlast] * num_added_years
        else:
            ### Use the same spacing forever
            forever = [[vlast + 1 + x] * ivt_step[i] for x in range(1000)]
            forever = [item for sublist in forever for item in sublist]
            ivt_add[i] = forever[:num_added_years]
    ivt_add = pd.DataFrame(ivt_add, index=addyears).T
    ### Concat and resave
    ivtout = pd.concat([ivt, ivt_add], axis=1)
    ivtout.to_csv(os.path.join(casedir, 'inputs_case', 'ivt.csv'))
    ### Get numclass, which is used in b_inputs.gms
    numclass = ivtout.max().max()

    return numclass


def check_compatibility(sw):
    ### Hourly resolution
    if (
        (int(sw['endyear']) > 2050)
        or int(sw['GSw_ClimateHydro'])
        or int(sw['GSw_ClimateDemand'])
        or int(sw['GSw_ClimateWater'])
        or int(sw['GSw_EFS_Flex'])
        or (float(sw['GSw_HydroWithinSeasFrac']) < 1)
        or (float(sw['GSw_HydroPumpWithinSeasFrac']) < 1)
        or (int(sw['GSw_Canada']) == 2)
    ):
        raise NotImplementedError(
            'At least one of GSw_Canada, GSw_ClimateHydro, GSw_ClimateDemand, GSw_ClimateWater, '
            'endyear, GSw_EFS_Flex, GSw_HydroWithinSeasFrac, GSw_HydroPumpWithinSeasFrac '
            'are using a currently-unsupported setting.')

    if 24 % (int(sw['GSw_HourlyWindowOverlap']) * int(sw['GSw_HourlyChunkLengthRep'])):
        raise ValueError(
            ('24 must be divisible by GSw_HourlyWindowOverlap * GSw_HourlyChunkLengthRep:'
            '\nGSw_HourlyWindowOverlap = {}\nGSw_HourlyChunkLengthRep = {}'.format(
                sw['GSw_HourlyWindowOverlap'], sw['GSw_HourlyChunkLengthRep'])))

    if int(sw['GSw_HourlyWindow']) <= int(sw['GSw_HourlyWindowOverlap']):
        raise ValueError(
            ('GSw_HourlyWindow must be greater than GSw_HourlyWindowOverlap:'
            '\nGSw_HourlyWindow = {}\nGSw_HourlyWindowOverlap = {}'.format(
                sw['GSw_HourlyWindow'], sw['GSw_HourlyWindowOverlap'])))

    if ((sw['GSw_HourlyClusterAlgorithm'] not in ['hierarchical','optimized'])
        and ('user' not in sw['GSw_HourlyClusterAlgorithm'])
    ):
        raise ValueError(
            "GSw_HourlyClusterAlgorithm must be set to 'hierarhical' or 'optimized', or must "
            "contain the substring 'user' and match a scenario in "
            "inputs/variability/period_szn_user.csv"
        )

    if ('usa' not in sw['GSw_Region'].lower()) and (int(sw['GSw_GasCurve']) != 2):
        raise ValueError(
            'Should use GSw_GasCurve=2 (fixed prices) when running sub-nationally\n'
            f"GSw_Region={sw['GSw_Region']}, GSw_GasCurve={sw['GSw_GasCurve']}"
        )


    ### Aggregation
    if (not int(sw['GSw_AggregateRegions'])) and (
        (int(sw['GSw_NumCSPclasses']) != 12)
        or (int(sw['GSw_NumDUPVclasses']) != 7)
    ):
        raise NotImplementedError(
            'Aggregated CSP/DUPV classes only work with aggregated regions. '
            'At least one of GSw_NumCSPclasses and GSw_NumDUPVclasses are incompatible with '
            'GSw_AggregateRegions=0')


def solvestring_sequential(
        batch_case, caseSwitches,
        cur_year, next_year, prev_year, restartfile,
        toLogGamsString=' logOption=4 logFile=gamslog.txt appendLog=1 ',
        hpc=0, iteration=0, stress_year=None,
    ):
    """
    Typical inputs:
    * restartfile: batch_case if first solve year else {batch_case}_{prev_year}
    * caseSwitches: loaded from {batch_case}/inputs_case/switches.csv
    """
    savefile = f"{batch_case}_{cur_year}i{iteration}"
    _stress_year = f"{prev_year}i0" if stress_year == None else stress_year
    out = (
        "gams d_solveoneyear.gms"
        + (" license=gamslice.txt" if hpc else '')
        + " o=" + os.path.join("lstfiles", f"{savefile}.lst")
        + " r=" + os.path.join("g00files", restartfile)
        + " gdxcompress=1"
        + " xs=" + os.path.join("g00files", savefile)
        + toLogGamsString
        + f" --case={batch_case}"
        + f" --cur_year={cur_year}"
        + f" --next_year={next_year}"
        + f" --prev_year={prev_year}"
        + f" --stress_year={_stress_year}"
        + ''.join([f" --{s}={caseSwitches[s]}" for s in [
            'GSw_SkipAugurYear',
            'GSw_HourlyType', 'GSw_HourlyWrapLevel', 'GSw_ClimateWater',
            'GSw_Canada', 'GSw_ClimateHydro',
            'GSw_HourlyChunkLengthRep', 'GSw_HourlyChunkLengthStress',
            'GSw_StateCO2ImportLevel',
        ]])
        + '\n'
    )

    return out


def setup_sequential_year(
        cur_year, prev_year, next_year,
        caseSwitches, hpc,
        solveyears, casedir, batch_case, toLogGamsString, OPATH, ticker,
        restart_switches,
    ):
    ## Get save file (for this year) and restart file (from previous year)
    savefile = f"{batch_case}_{cur_year}i0"
    restartfile = batch_case if cur_year == min(solveyears) else f"{batch_case}_{prev_year}i0"

    ## Run the ReEDS LP
    if (
        (not restart_switches['restart'])
        or (cur_year > min(solveyears))
        or (restart_switches['restart'] and not restart_switches['restart_Augur'])
    ):
        ## solve one year
        OPATH.writelines(
            solvestring_sequential(
                batch_case, caseSwitches,
                cur_year, next_year, prev_year, restartfile,
                toLogGamsString, hpc,
            ))
        OPATH.writelines(writescripterrorcheck(f"d_solveoneyear.gms_{cur_year}"))
        OPATH.writelines('python {t} --year={y}\n'.format(t=ticker, y=cur_year))

        if int(caseSwitches['GSw_ValStr']):
            OPATH.writelines("python valuestreams.py" + '\n')

        ## check to see if the restart file exists
        OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))

    ## Run Augur if it not the final solve year and if not skipping Augur
    if ((
        (cur_year < max(solveyears))
        and (next_year > int(caseSwitches['GSw_SkipAugurYear']))
    ) or (
        (cur_year == max(solveyears)) and int(caseSwitches['osprey_finalyear'])
    )):
        OPATH.writelines(
            f"\npython Augur.py {next_year} {cur_year} {casedir}\n")
        ## Check to make sure Augur ran successfully; quit otherwise
        OPATH.writelines(
            writeerrorcheck(os.path.join(
                "ReEDS_Augur", "augur_data", f"ReEDS_Augur_{cur_year}.gdx")))

    ## delete the previous restart file unless we're keeping them
    if (cur_year > min(solveyears)) and (not int(caseSwitches['keep_g00_files'])):
        write_delete_file(
            checkfile=os.path.join("g00files", savefile + ".g00"),
            deletefile=os.path.join("g00files", restartfile + '.g00'),
            PATH=OPATH,
        )


def setup_sequential(
        caseSwitches, reeds_path, hpc,
        solveyears, casedir, batch_case, toLogGamsString, OPATH, ticker,
        restart_switches,
    ):
    ### loop over solve years
    for i in range(len(solveyears)):
        ## current year is the value in solveyears
        cur_year = solveyears[i]

        if cur_year < max(solveyears):
            ## next year becomes the next item in the solveyears vector
            next_year = solveyears[i+1]
        ## Get previous year if after first year
        if i:
            prev_year = solveyears[i-1]
        else:
            if restart_switches['restart']:
                prev_year = restart_switches['restart_year']
            else:
                prev_year = solveyears[i]

        ### make an indicator in the batch file for what year is being solved
        big_comment(f'Year: {cur_year}', OPATH)

        ### Write the tax credit phaseout call
        OPATH.writelines(f"python tc_phaseout.py {cur_year} {casedir}\n\n")

        ### Write the GAMS LP and Augur calls
        if (
            int(caseSwitches['GSw_PRM_StressIterateMax'])
            and int(caseSwitches['GSw_PRM_MaxStressPeriods'])
        ):
            OPATH.writelines(
                f"python d_solve_iterate.py {casedir} {cur_year}\n"
            )
            OPATH.writelines(writescripterrorcheck(f"d_solve_iterate.py_{cur_year}"))
        else:
            setup_sequential_year(
                cur_year, prev_year, next_year,
                caseSwitches, hpc,
                solveyears, casedir, batch_case, toLogGamsString, OPATH, ticker,
                restart_switches,
            )

        ### Run Augur plots in background
        OPATH.writelines(
            f"python {os.path.join('ReEDS_Augur','G_plots.py')} "
            f"--reeds_path={reeds_path} --casedir={casedir} --t={cur_year} &\n")


def setup_intertemporal(
        caseSwitches, startiter, niter, ccworkers,
        solveyears, endyear, batch_case, toLogGamsString, yearset_augur, OPATH,
    ):
    ### beginning year is passed to augurbatch
    begyear = min(solveyears)
    ### first save file from d_solveprep is just the case name
    savefile = batch_case
    ### if this is the first iteration
    if startiter == 0:
        ## restart file becomes the previous calls save file
        restartfile=savefile
        ## if this is not the first iteration...
    if startiter > 0:
        ## restart file is now the case name plus the iteration number
        restartfile = batch_case+"_"+startiter

    ### per the instructions, iterations are
    ### the number of iterations after the first solve
    niter = niter+1

    ### for the number of iterations we have...
    for i in range(startiter,niter):
        ## make an indicator in the batch file for what iteration is being solved
        big_comment(f'Iteration: {i}', OPATH)
        ## call the intertemporal solve
        savefile = batch_case+"_"+str(i)

        if i==0:
            ## check to see if the restart file exists
            ## only need to do this with the zeroth iteration
            ## as the other checks will all be after the solves
            OPATH.writelines(writeerrorcheck(os.path.join("g00files",restartfile + ".g*")))

        OPATH.writelines(
            "gams d_solveallyears.gms o="+os.path.join("lstfiles",batch_case + "_" + str(i) + ".lst")
            +" r="+os.path.join("g00files",restartfile)
            + " gdxcompress=1 xs="+os.path.join("g00files",savefile) + toLogGamsString
            + " --niter=" + str(i) + " --case=" + batch_case
            + " --demand=" + caseSwitches['demand']  + ' \n')

        ## check to see if the save file exists
        OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))

        ## start threads for cc/curt
        ## no need to run cc curt scripts for final iteration
        if i < niter-1:
            ## batch out calls to augurbatch
            OPATH.writelines(
                "python augurbatch.py " + batch_case + " " + str(ccworkers) + " "
                + yearset_augur + " " + savefile + " " + str(begyear) + " "
                + str(endyear) + " " + caseSwitches['distpvscen'] + " "
                + str(caseSwitches['calc_csp_cc']) + " "
                + str(caseSwitches['GSw_DR']) + " "
                + str(caseSwitches['timetype']) + " "
                + str(caseSwitches['GSw_WaterMain']) + " " + str(i) + " "
                + str(caseSwitches['marg_vre_mw']) + " "
                + str(caseSwitches['marg_stor_mw']) + " "
                + str(caseSwitches['marg_dr_mw']) + " "
                + '\n')
            ## merge all the resulting gdx files
            ## the output file will be for the next iteration
            nextiter = i+1
            gdxmergedfile = os.path.join(
                "ReEDS_Augur","augur_data","ReEDS_Augur_merged_" + str(nextiter))
            OPATH.writelines(
                "gdxmerge "+os.path.join("ReEDS_Augur","augur_data","ReEDS_Augur*")
                + " output=" + gdxmergedfile  + ' \n')
            ## check to make sure previous calls were successful
            OPATH.writelines(writeerrorcheck(gdxmergedfile+".gdx"))

        ## restart file becomes the previous save file
        restartfile=savefile

    if caseSwitches['GSw_ValStr'] != '0':
        OPATH.writelines( "python valuestreams.py" + '\n')


def setup_window(
        caseSwitches, startiter, niter, ccworkers, reeds_path,
        batch_case, toLogGamsString, yearset_augur, OPATH,
    ):
    ### load the windows
    win_in = list(csv.reader(open(
        os.path.join(
            reeds_path,"inputs","userinput",
            "windows_{}.csv".format(caseSwitches['windows_suffix'])),
        'r'), delimiter=","))

    restartfile = batch_case

    ### for windows indicated in the csv file
    for win in win_in[1:]:

        ## beginning year is the first column (start)
        begyear = win[1]
        ## end year is the second column (end)
        endyear = win[2]
        ## for the number of iterations we have...
        for i in range(startiter,niter):
            big_comment(f'Window: {win}', OPATH)
            comment(f'Iteration: {i}', OPATH)

            ## call the window solve
            savefile = batch_case+"_"+str(i)
            ## check to see if the save file exists
            OPATH.writelines(writeerrorcheck(os.path.join("g00files",restartfile + ".g*")))
            ## solve via the window solve file
            OPATH.writelines(
                "gams d_solvewindow.gms o=" + os.path.join("lstfiles",batch_case + "_" + str(i) + ".lst")
                +" r=" + os.path.join("g00files",restartfile)
                + " gdxcompress=1 xs=g00files\\"+savefile + toLogGamsString + " --niter=" + str(i)
                + " --maxiter=" + str(niter-1) + " --case=" + batch_case + " --window=" + win[0] + ' \n')
            ## start threads for cc/curt
            OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))
            OPATH.writelines(
                "python augurbatch.py " + batch_case + " " + str(ccworkers) + " "
                + yearset_augur + " " + savefile + " " + str(begyear) + " "
                + str(endyear) + " " + caseSwitches['distpvscen'] + " "
                + str(caseSwitches['calc_csp_cc']) + " "
                + str(caseSwitches['GSw_DR']) + " "
                + str(caseSwitches['timetype']) + " "
                + str(caseSwitches['GSw_WaterMain']) + " " + str(i) + " "
                + str(caseSwitches['marg_vre_mw']) + " "
                + str(caseSwitches['marg_stor_mw']) + " "
                + str(caseSwitches['marg_dr_mw']) + " "
                + '\n')
            ## merge all the resulting r2_in gdx files
            ## the output file will be for the next iteration
            nextiter = i+1
            ## create names for then merge the curt and cc gdx files
            gdxmergedfile = os.path.join(
                "ReEDS_Augur","augur_data","ReEDS_Augur_merged_" + str(nextiter))
            OPATH.writelines(
                "gdxmerge " + os.path.join("ReEDS_Augur","augur_data","ReEDS_Augur*")
                + " output=" + gdxmergedfile  + ' \n')
            ## check to make sure previous calls were successful
            OPATH.writelines(writeerrorcheck(gdxmergedfile+".gdx"))
            restartfile=savefile
        if caseSwitches['GSw_ValStr'] != '0':
            OPATH.writelines( "python valuestreams.py" + '\n')


#############
#%% PROCEDURE

def setupEnvironment(
        BatchName=False, cases_suffix=False, simult_runs=0,
        forcelocal=0, restart=False, skip_env_check=False):
    # #%% Inputs for debugging
    # BatchName = 'v20230508_prasM0_Pacific'
    # cases_suffix = 'test'
    # WORKERS = 1
    # forcelocal = 0
    # restart = False

    #%% Automatic inputs
    reeds_path = os.path.dirname(__file__)

    #%% User inputs
    print(" ")
    print("------------- ")
    print(" ")
    print("WINDOWS USERS - This script will open multiple command prompts, the number of which")
    print("is based on the number of simultaneous runs you've chosen")
    print(" ")
    print("MAC/LINUX USERS - Your cases will run in the background. All console output")
    print("is written to the cases' appropriate gamslog.txt file in the cases' runs folders")
    print(" ")
    print("------------- ")
    print(" ")
    print(" ")

    if not BatchName:
        print("-- Specify the batch prefix --")
        print(" ")
        print("The batch prefix is attached to the beginning of all cases' outputs files")
        print("Note - it must start with a letter and not a number or symbol")
        print(" ")
        print("A value of 0 will assign the date and time as the batch name (e.g. v20190520_072310)")
        print(" ")

        BatchName = str(input('Batch Prefix: '))

    if BatchName == '0':
        BatchName = 'v' + time.strftime("%Y%m%d_%H%M%S")

    if not cases_suffix:
        print("\n\nSpecify the suffix for the cases_suffix.csv file")
        print("A blank input will default to the cases.csv file\n")

        cases_suffix = str(input('Case Suffix: '))

    #%% Check whether to submit slurm jobs (if on HPC) or run locally
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

    #%% Check whether the ReEDS conda environment is activated
    if ('reeds' not in os.environ['CONDA_DEFAULT_ENV'].lower()) and not skip_env_check:
        print(
            "It looks like you haven't activated the 'reeds' conda environment from "
            "environment.yml, so the python and julia parts of ReEDS might not work. "
            "To build the environment for the first time, run: "
            "    `conda env create -f environment.yml`"
            "To activate the created environment, run: "
            "    `conda activate reeds` (or `activate reeds` on Windows) "
            "Do you want to continue without activating the environment?"
        )
        confirm_env = str(input("Continue? y/[n]: ") or 'n')
        if not confirm_env in ['y','Y','yes','Yes','YES']:
            quit()

    #%% Load specified case file, infer other settings from cases.csv
    df_cases = pd.read_csv(
        os.path.join(reeds_path, 'cases.csv'), dtype=object, index_col=0)
    cases_filename = 'cases.csv'

    #If we have a case suffix, use cases_[suffix].csv for cases.
    if cases_suffix not in ['','default']:
        df_cases = df_cases[['Choices', 'Default Value']]
        cases_filename = 'cases_' + cases_suffix + '.csv'
        df_cases_suf = pd.read_csv(
            os.path.join(reeds_path, cases_filename), dtype=object, index_col=0)

        #Check to make sure user-specified cases file has up-to-date switches
        missing_switches = [s for s in df_cases_suf.index if s not in df_cases.index]
        if len(missing_switches):
            error = ("The following switches are in {} but have changed names or are no longer "
                      "supported by ReEDS:\n\n{} \n\nPlease update your cases file; "
                      "for the full list of available switches see cases.csv."
                      "Note that switch names are case-sensitive."
                    ).format(cases_filename, '\n'.join(missing_switches))
            raise ValueError(error)

        #First use 'Default Value' from cases_[suffix].csv to fill missing switches
        #Later, we will also use 'Default Value' from cases.csv to fill any remaining holes.
        if 'Default Value' in df_cases_suf.columns:
            case_i = df_cases_suf.columns.get_loc('Default Value') + 1
            casenames = df_cases_suf.columns[case_i:].tolist()
            for case in casenames:
                df_cases_suf[case] = df_cases_suf[case].fillna(df_cases_suf['Default Value'])
        df_cases_suf.drop(['Choices','Default Value'], axis='columns',inplace=True, errors='ignore')
        df_cases = df_cases.join(df_cases_suf, how='outer')

    # initiate the empty lists which will be filled with info from cases
    caseList = []
    caseSwitches = [] #list of dicts, one dict for each case
    casenames = [c for c in df_cases.columns if not c in ['Description','Default Value','Choices']]
    # Get the list of switch choices
    choices = df_cases.Choices.copy()

    for case in casenames:
        #Fill any missing switches with the defaults in cases.csv
        df_cases[case] = df_cases[case].fillna(df_cases['Default Value'])
        # Ignore cases with ignore flag
        if int(df_cases.loc['ignore',case]) == 1:
            continue
        # Check to make sure the switch setting is valid
        for i, val in df_cases[case].iteritems():
            ### Split choices by either '; ' or ','
            if choices[i] in ['N/A',None,np.nan]:
                pass
            else:
                i_choices = [
                    str(j).strip() for j in
                    np.ravel([i.split(',') for i in choices[i].split(';')]).tolist()
                ]
                if str(val) not in i_choices:
                    error = (
                        'Invalid entry for "{}" for case "{}".\n'
                        'Entered "{}" but must be one of the following:\n\n{}'
                    ).format(i, case, val, '\n'.join(i_choices))
                    raise ValueError(error)
        # Add switch settings to list of options passed to GAMS
        shcom = ' --case=' + BatchName + "_" + case
        for i,v in df_cases[case].iteritems():
            #exclude certain switches that don't need to be passed to GAMS
            if i not in ['file_replacements','keep_run_terminal']:
                shcom = shcom + ' --' + i + '=' + v
        caseList.append(shcom)
        caseSwitches.append(df_cases[case].to_dict())

    # ignore cases with ignore flag
    casenames = [case for case in casenames if int(df_cases.loc['ignore',case]) != 1]
    df_cases.drop(
        df_cases.loc['ignore'].loc[df_cases.loc['ignore']=='1'].index, axis=1, inplace=True)

    # Make sure the run folders don't already exist
    outpaths = [os.path.join(reeds_path,'runs','{}_{}'.format(BatchName,case)) for case in casenames]
    existing_outpaths = [i for i in outpaths if os.path.isdir(i)]
    if len(existing_outpaths) and not restart:
        print(
            f'The following {len(existing_outpaths)} output directories already exist:\n'
            + '⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄\n'
            + '\n'.join([os.path.basename(i) for i in existing_outpaths])
            + '\n⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃\n'
        )
        overwrite = str(input('Do you want to overwrite them? y/[n]: ') or 'n')
        if overwrite in ['y','Y','yes','Yes','YES']:
            for outpath in existing_outpaths:
                shutil.rmtree(outpath)
        else:
            keep = [i for (i,c) in enumerate(outpaths) if c not in existing_outpaths]
            caseList = [caseList[i] for i in keep]
            casenames = [casenames[i] for i in keep]
            caseSwitches = [caseSwitches[i] for i in keep]
            print(
                f"\nThe following {(len(keep))} output directories don't exist:\n"
                + '⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄⌄\n'
                + '\n'.join([f'{BatchName}_{c}' for c in casenames])
                + '\n⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃⌃\n'
            )
            skip = str(input('Do you want to run them and skip the rest? y/[n]: ') or 'n')
            if not (skip in ['y','Y','yes','Yes','YES']):
                raise IsADirectoryError('\n'+'\n'.join(existing_outpaths))

    df_cases.drop(
        ['Choices','Description','Default Value'],
        axis='columns', inplace=True, errors='ignore')

    print("{} cases being run:".format(len(caseList)))
    for case in casenames:
        print(case)
    print(" ")

    reschoice = 0
    startiter = 0
    ccworkers = 5
    niter = 5
    #%% Set number of workers, with user input if necessary
    if len(caseList)==1:
        print("Only one case is to be run, therefore only one thread is needed")
        WORKERS = 1
    elif simult_runs < 0:
        WORKERS = len(caseList)
    elif simult_runs > 0:
        WORKERS = simult_runs
    else:
        WORKERS = int(input('Number of simultaneous runs [integer]: '))

    print(WORKERS)
    print("")

    if 'int' in df_cases.loc['timetype'].tolist() or 'win' in df_cases.loc['timetype'].tolist():
        ccworkers = int(input('Number of simultaneous CC/Curt runs [integer]: '))
        print("")
        print("The number of iterations defines the number of combinations of")
        print(" solving the model and computing capacity credit and curtailment")
        print(" Note this does not include the initial solve")
        print("")
        niter = int(input('How many iterations between the model and CC/Curt scripts: '))
        # reschoice = int(input('Do you want to restart from a previous convergence attempt (0=no, 1=yes): '))

        if reschoice==1:
            startiter = int(input('Iteration to start from (recall it starts at zero): '))


    envVar = {
        'WORKERS': WORKERS,
        'ccworkers': ccworkers,
        'casenames': casenames,
        'BatchName': BatchName,
        'caseList': caseList,
        'caseSwitches': caseSwitches,
        'reeds_path' : reeds_path,
        'niter' : niter,
        'startiter' : startiter,
        'cases_filename': cases_filename,
        'hpc': hpc,
        'restart': restart,
    }

    return envVar


def createmodelthreads(envVar):

    q = queue.Queue()
    num_worker_threads = envVar['WORKERS']

    def worker():
        while True:
            ThreadInit = q.get()
            if ThreadInit is None:
                break
            runModel(
                options=ThreadInit['scen'],
                caseSwitches=ThreadInit['caseSwitches'],
                niter=ThreadInit['niter'],
                reeds_path=ThreadInit['reeds_path'],
                ccworkers=ThreadInit['ccworkers'],
                startiter=ThreadInit['startiter'],
                BatchName=ThreadInit['BatchName'],
                case=ThreadInit['casename'],
                cases_filename=ThreadInit['cases_filename'],
                hpc=envVar['hpc'],
                restart=envVar['restart'],
            )
            print(ThreadInit['batch_case'] + " has finished \n")
            q.task_done()


    threads = []

    for i in range(num_worker_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for i in range(len(envVar['caseList'])):
        q.put({'scen': envVar['caseList'][i],
               'caseSwitches': envVar['caseSwitches'][i],
               'batch_case':envVar['BatchName']+'_'+envVar['casenames'][i],
               'niter':envVar['niter'],
               'reeds_path':envVar['reeds_path'],
               'ccworkers':envVar['ccworkers'],
               'startiter':envVar['startiter'],
               'BatchName':envVar['BatchName'],
               'casename':envVar['casenames'][i],
               'cases_filename':envVar['cases_filename'],
               'restart':envVar['restart'],
               })

    # block until all tasks are done
    q.join()

    # stop workers
    for i in range(num_worker_threads):
        q.put(None)

    for t in threads:
        t.join()


def runModel(options, caseSwitches, niter, reeds_path, ccworkers, startiter,
             BatchName, case, cases_filename, hpc=False, restart=False):
    ### For debugging
    # caseSwitches = caseSwitches[0]
    # options = caseList[0]
    ### Inferred inputs
    batch_case = '{}_{}'.format(BatchName,case)
    endyear = int(caseSwitches['endyear'])

    casedir = os.path.join(reeds_path,"runs",batch_case)
    inputs_case = os.path.join(casedir,"inputs_case")

    # indicate this run is a restart
    if restart:
        print("Restarting from previous run.")
    else:
        if os.path.exists(os.path.join(reeds_path,"runs",batch_case)):
            print("Caution, case " + batch_case + " already exists in runs \n")

        #%% Set up case-specific directory structure
        os.makedirs(os.path.join(reeds_path,"runs",batch_case), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,"runs",batch_case,"g00files"), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,"runs",batch_case,"lstfiles"), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,"runs",batch_case,"outputs"), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,"runs",batch_case,"outputs","tc_phaseout_data"), exist_ok=True)
        os.makedirs(inputs_case, exist_ok=True)

    #%% Stop now if any switches are incompatible
    check_compatibility(caseSwitches)

    #%% Write the GAMS switches
    gswitches = pd.Series(caseSwitches)
    ## Only keep switches that start with 'GSw' and have a numeric value
    def isnumeric(x):
        try:
            float(x)
            if '_' not in x:
                return True
        except:
            return False
    gswitches = gswitches.loc[
        gswitches.index.str.lower().str.startswith('gsw')
        & gswitches.map(isnumeric)
    ].copy()
    ## In GAMS we change 'GSw' to 'Sw'
    gswitches.index = gswitches.index.map(lambda x: x[1:])
    ## Add a 'comment' column and write to csv and GAMS-readable text
    gswitches.reset_index().assign(comment='').to_csv(
        os.path.join(inputs_case,'gswitches.csv'), header=False, index=False)

    #%% Information on reV supply curves associated with this run
    shutil.copytree(os.path.join(reeds_path,'inputs','supplycurvedata','metadata'),
                    os.path.join(inputs_case,'supplycurve_metadata'), dirs_exist_ok=True)
    revData = pd.read_csv(
            os.path.join(reeds_path,'inputs','supplycurvedata','metadata','rev_paths.csv')
        )

    # separate techs with no associated switch
    revDataSub = revData.loc[revData.access_switch == "none",:].copy()
    revData = revData.loc[revData.access_switch != "none",:]

    # match possible supply curves with switches from this run
    siteSwitches = pd.DataFrame.from_dict({s:caseSwitches[s] for s in revData.access_switch.unique()},
                                orient='index').reset_index().rename(columns={'index':'access_switch', 0:'access_case'})
    siteSwitches = siteSwitches.merge(revData, on=['access_switch', 'access_case'])
    siteSwitches = pd.concat([siteSwitches[revDataSub.columns.tolist()], revDataSub])

    # get bin information
    bins = {"wind-ons":"numbins_windons", "wind-ofs": "numbins_windofs", "upv":"numbins_upv"}
    binSwitches = pd.DataFrame.from_dict({b:caseSwitches[bins[b]] for b in bins},
                                orient='index').reset_index().rename(columns={'index':'tech', 0:'bins'})

    siteSwitches = siteSwitches.merge(binSwitches, on=['tech'], how='left')

    # expand on reV path based on where this run is happening
    # To DO: add functionality for AWS
    eagle_path = '/shared-projects/reeds/Supply_Curve_Data'
    if hpc:
        rev_prefix = eagle_path
    else:
        if os.name == 'posix':
            drive = '/Volumes/'
        else:
            drive = '//nrelnas01/'
        rev_prefix = os.path.join(drive,'ReEDS','Supply_Curve_Data')

    siteSwitches['rev_case'] = siteSwitches['rev_path'].apply(lambda row: os.path.basename(row))
    siteSwitches['eagle_path'] = siteSwitches['rev_path'].apply(lambda row: os.path.join(eagle_path, row))
    siteSwitches['rev_path'] = siteSwitches['rev_path'].apply(lambda row: os.path.join(rev_prefix, row))
    siteSwitches['sc_path'] = siteSwitches['sc_path'].apply(lambda row: os.path.join(rev_prefix, row))
    siteSwitches[['tech', 'access_switch', 'access_case', 'bins','rev_case', 
                  'rev_path', 'eagle_path', 'sc_path', 'eagle_sc_file', 'original_rev_folder']
                ].to_csv(os.path.join(inputs_case,'supplycurve_metadata','rev_supply_curves.csv'), index=False)

    #%% Set up the meta.csv file to track repo information and runtime
    ticker = os.path.join(reeds_path,'input_processing','ticker.py')
    with open(os.path.join(casedir,'meta.csv'), 'w+') as METAFILE:
        ### Write some git metadata
        METAFILE.writelines('computer,repo,branch,commit,description\n')
        try:
            import git
            import socket
            repo = git.Repo()
            try:
                branch = repo.active_branch.name
                description = repo.git.describe()
            except TypeError:
                branch = 'DETACHED_HEAD'
                description = ''
            METAFILE.writelines(
                '{},{},{},{},{}\n'.format(
                    socket.gethostname(),
                    repo.git_dir, branch, repo.head.object.hexsha, description))
        except:
            ### In case the user hasn't installed GitPython (conda install GitPython)
            ### or isn't in a git repo or anything else goes wrong
            METAFILE.writelines('None,None,None,None,None\n')

        ### Header for timing metadata
        METAFILE.writelines('#,#,#,#,#\n')
        METAFILE.writelines('year,process,starttime,stoptime,processtime\n')

    ### Copy over the cases file
    shutil.copy2(os.path.join(reeds_path, cases_filename), casedir)

    ### Get hpc setting (used in Augur)
    caseSwitches['hpc'] = int(hpc)
    options += f' --hpc={int(hpc)}'
    ### Get numclass from the max value in ivt
    caseSwitches['numclass'] = get_ivt_numclass(
        reeds_path=reeds_path, casedir=casedir, caseSwitches=caseSwitches)
    options += ' --numclass={}'.format(caseSwitches['numclass'])
    ### Get numbins from the max of individual technology bins
    caseSwitches['numbins'] = max(
        int(caseSwitches['numbins_windons']),
        int(caseSwitches['numbins_windofs']),
        int(caseSwitches['numbins_upv']),
        15)
    options += ' --numbins={}'.format(caseSwitches['numbins'])
    options += f' --reeds_path={reeds_path}{os.sep} --casedir={casedir}'

    #%% Record the switches for this run
    pd.Series(caseSwitches).to_csv(
        os.path.join(inputs_case,'switches.csv'), header=False)

    solveyears = pd.read_csv(
        os.path.join(reeds_path, 'inputs','modeledyears.csv'),
        usecols=[caseSwitches['yearset_suffix']],
    ).squeeze(1).dropna().astype(int).tolist()
    solveyears = [y for y in solveyears if y <= endyear]

    yearset_augur = os.path.join('inputs_case','modeledyears.csv')
    toLogGamsString = ' logOption=4 logFile=gamslog.txt appendLog=1 '

    if not restart:
        ## copy the ReEDS_Augur and input_processing folders
        shutil.copytree(
            os.path.join(reeds_path, 'ReEDS_Augur'),
            os.path.join(casedir, 'ReEDS_Augur'))
        shutil.copytree(
            os.path.join(reeds_path, 'input_processing'),
            os.path.join(casedir, 'input_processing'))

        #make the augur_data folder
        os.makedirs(os.path.join(casedir,'ReEDS_Augur','augur_data'), exist_ok=True)
        os.makedirs(os.path.join(casedir,'ReEDS_Augur','PRAS'), exist_ok=True)

    ###### Replace files according to 'file_replacements' in cases. Ignore quotes in input text.
    #<< is used to separate the file that is to be replaced from the file that is used
    #|| is used to separate multiple replacements.
    if caseSwitches['file_replacements'] != 'none':
        file_replacements = caseSwitches['file_replacements'].replace('"','').replace("'","").split('||')
        for file_replacement in file_replacements:
            replace_arr = file_replacement.split('<<')
            replaced_file = replace_arr[0].strip()
            replaced_file = os.path.join(casedir, replaced_file)
            if not os.path.isfile(replaced_file):
                raise FileNotFoundError('FILE REPLACEMENT ERROR: "' + replaced_file + '" was not found')
            used_file = replace_arr[1].strip()
            if not os.path.isfile(used_file):
                raise FileNotFoundError('FILE REPLACEMENT ERROR: "' + used_file + '" was not found')
            if os.path.isfile(replaced_file) and os.path.isfile(used_file):
                shutil.copy(used_file, replaced_file)
                print('FILE REPLACEMENT SUCCESS: Replaced "' + replaced_file + '" with "' + used_file + '"')

    ext = '.sh' if os.name == 'posix' else '.bat'

    restart_switches = {'restart':restart}
    if restart:
        ### If restarting, get the year from the most recent .g00 file
        g00files = glob(os.path.join(reeds_path,"runs",batch_case,"g00files",'*'))
        g00years = []
        for f in g00files:
            try:
                ### Keep it if it ends with _{year}
                g00years.append(int(os.path.splitext(f)[0].split('_')[-1]))
            except ValueError:
                ### If we can't turn the piece after the '_' into an int, it's not a year
                pass

        ### Keep the first year -- this will be the last solve with a completely saved g00 file
        restart_switches['restart_year'] = min(g00years)

        ### Also get last Augur solve
        Augurfiles = glob(os.path.join(reeds_path,"runs", batch_case, "ReEDS_Augur", "augur_data", "ReEDS_Augur_*.gdx"))
        auguryears = [int(os.path.basename(f).split("_")[-1].split(".")[0]) for f in Augurfiles]

        #  if there is an Augur solve for this year, start the model in next year after the restart
        if restart_switches['restart_year'] in auguryears:
            solveyears = [y for y in solveyears if y > restart_switches['restart_year']]
            restart_switches['restart_Augur'] = False
        else:
        # if there is no Augur solve for this year, start with Augur in the year of the restart
            solveyears = [y for y in solveyears if y >= restart_switches['restart_year']]
            restart_switches['restart_Augur'] = True
    else:
        restart_switches['restart_Augur'] = False

    # flag for a restart or an original one
    call = 'call_restart_' if restart else 'call_'

    #%% Write the call script
    with open(os.path.join(casedir, call + batch_case + ext), 'w+') as OPATH:
        OPATH.writelines(f"echo 'Running {batch_case}'\n")
        OPATH.writelines("cd " + casedir + '\n' + '\n' + '\n')

        if hpc:
            comment('Set up nodal environment for run', OPATH)
            OPATH.writelines(". $HOME/.bashrc \n")
            OPATH.writelines("module purge \n")
            OPATH.writelines("module use /nopt/nrel/apps/software/gams/modulefiles \n")
            OPATH.writelines("source /nopt/nrel/apps/env.sh \n")
            #OPATH.writelines("module load anaconda3 \n")            
            OPATH.writelines("conda activate reeds \n")
            OPATH.writelines("module load gams/34.3.0 \n")
            OPATH.writelines('export R_LIBS_USER="$HOME/rlib" \n\n\n')

        if restart:
            #%% skip input_processing and model creation if restarting, and set restart file to last available
            restartfile = f"{batch_case}_{restart_switches['restart_year']}"
        else:
            #%% Write the input_processing script calls
            big_comment('Input processing', OPATH)
            tolog = ''
            for s in [
                'copy_files',
                'calc_financial_inputs',
                'fuelcostprep',
                'writecapdat',
                'writesupplycurves',
                'writedrshift',
                'plantcostprep',
                'climateprep',
                'LDC_prep',
                'forecast',
                'WriteHintage',
                'transmission',
                'hourly_repperiods',
                'aggregate_regions',
            ]:
                OPATH.writelines(f"echo 'starting {s}.py'\n")
                OPATH.writelines(
                    f"python {os.path.join(casedir,'input_processing',s)}.py {reeds_path} {inputs_case} {tolog}\n")
                OPATH.writelines(writescripterrorcheck(s)+'\n')

            OPATH.writelines(
                "\ngams createmodel.gms gdxcompress=1 xs="+os.path.join("g00files",batch_case)
                + (' license=gamslice.txt' if hpc else '')
                + " o="+os.path.join("lstfiles","1_Inputs.lst") + options + " " + toLogGamsString + '\n')
            OPATH.writelines('python {t}\n'.format(t=ticker))
            restartfile = batch_case
            OPATH.writelines(writeerrorcheck(os.path.join('g00files',restartfile + '.g*')))

        ########################
        #%% Core model setup ###
        ########################
        if caseSwitches['timetype'] == 'seq':
            setup_sequential(
                caseSwitches, reeds_path, hpc,
                solveyears, casedir, batch_case, toLogGamsString, OPATH, ticker,
                restart_switches,
            )
        elif caseSwitches['timetype'] == 'int':
            setup_intertemporal(
                caseSwitches, startiter, niter, ccworkers,
                solveyears, endyear, batch_case, toLogGamsString, yearset_augur, OPATH,
            )
        elif caseSwitches['timetype'] == 'win':
            setup_window(
                caseSwitches, startiter, niter, ccworkers, reeds_path,
                batch_case, toLogGamsString, yearset_augur, OPATH,
            )

        ##########################
        # -- OUTPUT PROCESSING --
        ##########################

        #create reporting files
        big_comment('Output processing', OPATH)
        ### TODO: Figure out a way to only run e_report.gms for the last-completed
        ### iteration run. Currently it will run for both iteration 0 and 1 when using
        ### stress-period iterations, which is dumb.
        for iteration in range(int(caseSwitches['GSw_PRM_StressIterateMax'])+1):
            OPATH.writelines(
                "gams e_report.gms"
                + " o="+os.path.join("lstfiles","report_" + batch_case + ".lst")
                + (' license=gamslice.txt' if hpc else '')
                + ' r=' +os.path.join("g00files", f"{batch_case}_{max(solveyears)}i{iteration}")
                + ' gdxcompress=1'
                + toLogGamsString
                + "--fname=" + batch_case
                + ' --GSw_calc_powfrac={} \n'.format(caseSwitches['GSw_calc_powfrac'])
            )
        OPATH.writelines('python {t}\n'.format(t=ticker))
        OPATH.writelines('python e_report_dump.py {}\n\n'.format(casedir))


        ### Run the retail rate module
        OPATH.writelines(
            f"python {os.path.join(reeds_path,'postprocessing','retail_rate_module','retail_rate_calculations.py')} {batch_case} -p\n\n"
        )

        ## Run air-quality and health damages calculation script
        if int(caseSwitches['GSw_HealthDamages']):
            OPATH.writelines(
                f"python {os.path.join(reeds_path,'postprocessing','air_quality','health_damage_calculations.py')} {casedir}\n\n"
            )

        ## ReEDS_to_rev processing
        if caseSwitches['reeds_to_rev'] == '1':
            OPATH.writelines('cd {} \n\n'.format(reeds_path))
            OPATH.writelines(f'python hourlize/reeds_to_rev.py {reeds_path} {casedir} "cost" -r\n\n')

        if caseSwitches['land_use_analysis'] == '1':
            # run the land-used characterization module
            OPATH.writelines(
                f"python {os.path.join(reeds_path,'postprocessing','land_use','land_use_analysis.py')} {casedir}\n\n"
            )

        ## Run Bokeh
        bokehdir = os.path.join(reeds_path,"postprocessing","bokehpivot","reports")
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(reeds_path,"runs",batch_case) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","standard_report_reduced.py") + ' "html,excel,csv" one '
            + os.path.join(reeds_path,"runs",batch_case,"outputs","reeds-report-reduced") + ' no\n')
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(reeds_path,"runs",batch_case) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","standard_report_expanded.py") + ' "html,excel" one '
            + os.path.join(reeds_path,"runs",batch_case,"outputs","reeds-report") + ' no\n')
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(reeds_path,"runs",batch_case) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","state_report.py") + ' "csv" one '
            + os.path.join(reeds_path,"runs",batch_case,"outputs","reeds-report-state") + ' no\n\n')
        OPATH.writelines('python postprocessing/vizit/vizit_prep.py ' + '"{}"'.format(os.path.join(casedir,'outputs')) + '\n\n')

        # make script to unload all data to .gdx file
        command = (
            'gams dump_alldata.gms'
            + ' o='+os.path.join('lstfiles','dump_alldata_{}_{}.lst'.format(BatchName,case))
            + ' r='+os.path.join('g00files','{}_{}_{}i0'.format(BatchName,case,solveyears[-1])))
        with open(os.path.join(casedir,'dump_alldata'+ext),'w+') as datadumper:
            datadumper.writelines('cd ' + os.path.join(reeds_path,'runs','{}_{}'.format(BatchName,case)) + '\n')
            for l in [
                f"By default, this script dumps data for the first iteration of {solveyears[-1]}.",
                "If more iterations were needed, increase the number at the end of the",
                f"next line after 'i' (e.g. {solveyears[-1]}i0 -> {solveyears[-1]}i1)",
            ]:
                comment(l, datadumper)
            datadumper.writelines(command)
        if int(caseSwitches['dump_alldata']):
            OPATH.writelines(command+'\n')

        if int(caseSwitches['delete_big_files']):
            for file in [
                os.path.join(inputs_case, 'recf.h5'),
                os.path.join(inputs_case, 'load.h5'),
                os.path.join(inputs_case, 'csp_profiles.h5'),
                os.path.join(inputs_case, 'can_trade_8760.h5'),
                os.path.join(inputs_case, 'rsc_combined.csv'),
                ### Uncomment the following two lines to delete the .g00 files
                # os.path.join('g00files', restartfile + '.g00'),
                # os.path.join('g00files', restartfile.rstrip(str(cur_year)+'_') + '.g00'),
            ]:
                write_delete_file(checkfile=file, deletefile=file, PATH=OPATH)
            OPATH.writelines('')

        if int(caseSwitches['transmission_maps']):
            OPATH.writelines('python postprocessing/transmission_maps.py -c {} -y {}\n'.format(
                casedir, (
                    solveyears[-1]
                    if int(caseSwitches['transmission_maps']) > int(solveyears[-1])
                    else caseSwitches['transmission_maps'])
            ))

        ### Write the call to the R2X tests
        pipe = '2>&1 | tee -a' if os.name == 'posix' else '>>'
        OPATH.writelines(
            f"\npytest -v -l tests --casepath {casedir} "
            f"{pipe} {os.path.join(casedir,'gamslog.txt')}\n"
        )


    ##############################
    # Call the Created Batch File
    ##############################

    #if you're not running on eagle or AWS..
    if (not hpc) & (not int(caseSwitches['AWS'])):
        # start the command prompt similar to the sequential solve
        # - waiting for it to finish before starting a new thread
        if os.name!='posix':
            if int(caseSwitches['keep_run_terminal']) == 1:
                terminal_keep_flag = ' /k '
            else:
                terminal_keep_flag = ' /c '
            os.system('start /wait cmd' + terminal_keep_flag + os.path.join(casedir, call + batch_case + ext))
        if os.name=='posix':
            print("Starting the run for case " + batch_case)
            #give execution rights to the shell script
            os.chmod(os.path.join(casedir, call + batch_case + ext), 0o777)
            #open it up - note the in/out/err will be written to the shellscript parameter
            shellscript = subprocess.Popen(
                [os.path.join(casedir, call + batch_case + ext)], shell=True)
            #wait for it to finish before killing the thread
            shellscript.wait()

    elif hpc:
        # create a copy of srun_template in casedir as {batch_case}.sh
        if caseSwitches['timetype']=="int":
            shutil.copy("srun_template_int.sh", os.path.join(casedir, batch_case+".sh"))
        else:
            shutil.copy("srun_template.sh", os.path.join(casedir, batch_case+".sh"))
        with open(os.path.join(casedir, batch_case+".sh"), 'a') as SPATH:
            #add the name for easy tracking of the case
            SPATH.writelines("\n#SBATCH --job-name=" + batch_case + "\n\n")
            #add the call to the sh file created throughout this function
            SPATH.writelines("sh " + os.path.join(casedir, call + batch_case + ext))
        #close the file
        SPATH.close()
        #call that file
        batchcom = "sbatch " + os.path.join(casedir, batch_case + ".sh")
        subprocess.Popen(batchcom.split())

    elif int(caseSwitches['AWS']):
        print("Starting the run for case " + batch_case)
        #give execution rights to the shell script
        os.chmod(os.path.join(casedir, call + batch_case + ext), 0o777)
        #issue a nohup (no hangup) command and direct output to
        # case-specific txt files in the root of the repository
        shellscript = subprocess.Popen(
            ['nohup ' + os.path.join(casedir, call + batch_case + ext) + " > " +os.path.join(casedir,batch_case+ ".txt") ],
                stdin=open(os.path.join(casedir,batch_case+"_in.txt"),'w'),
                stdout=open(os.path.join(casedir,batch_case+"_out.txt"),'w'),
                stderr=open(os.path.join(casedir,batch_case+"_err.log"),'w'),
                shell=True,preexec_fn=os.setpgrp)
        # wait for it to finish before killing the thread
        shellscript.wait()

    ### Record the ending time
    now = datetime.isoformat(datetime.now())
    try:
        with open(os.path.join(casedir,'meta.csv'), 'a') as METAFILE:
            METAFILE.writelines('0,end,,{},\n'.format(now))
    except:
        print('meta.csv not found or not writeable')
        pass


def main(
        BatchName='', cases_suffix='', simult_runs=0,
        forcelocal=False, restart=False, skip_env_check=False):
    """
    Executes parallel solves based on cases in 'cases.csv'
    """
    print(" ")
    print(" ")
    print("--------------------------------------------------------------------------------------------------")
    print(" ")
    print("         MMM.  808   MMM;   BMW       rMM   @MMMMMMMM2     XM@MMMMMMMMMS   MM0         ")
    print("        iMMM@S,MMM;X@MMMZ   MMMM.     aMM   MMMW@MMMMMMM   BMMMW@M@M@MMX   MMM         ")
    print("         r2MMZ     SMMa;i   MMMMM;    SMM   MMB      7MMS  ZMM.            MMM         ")
    print("           Z         Z      MMZ7MM2   XMM   MMW       MM8  ZMM.            MMM         ")
    print("        .MMr         .MM7   MM8 rMMB  XMM   MM@     ,MMM   ZMMMMMMMMMM     MMM         ")
    print("        .MMr         ,MMr   MMB  :MMM :MM   MMW  MMMMMB    ZMMMWMMMMM@     MMM         ")
    print("           Z         Z      MMW    MMMaMM   MM@   MMMi     ZMM.            MMM         ")
    print("         XaMM8     aMMZXi   MMW     MMMMM   MM@    0MMr    ZMM.            MMW         ")
    print("        iMMMW7,MMM;;BMMMZ   MMM      8MMM   MMM     aMMB   0MMMWMMM@MMMZ   MMM@MMMMMMM ")
    print("         BZ0   SSS   0Z0.   ZBX       :0B   8BS      :BM7  ;8Z8WWWWWW@M2   BZZ0WWWWWWM ")
    print(" ")
    print("--------------------------------------------------------------------------------------------------")
    print(" ")
    print(" ")

    #gather user inputs before calling GAMS programs
    envVar = setupEnvironment(
        BatchName=BatchName, cases_suffix=cases_suffix, simult_runs=simult_runs,
        forcelocal=forcelocal, restart=restart, skip_env_check=skip_env_check)
    # threads are created which will handle each case individually
    createmodelthreads(envVar)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--BatchName', '-b', type=str, default='',
                        help='Name for batch of runs')
    parser.add_argument('--cases_suffix', '-c', type=str, default='',
                        help='Suffix for cases CSV file')
    parser.add_argument('--simult_runs', '-r', type=int, default=0,
                        help='Number of simultaneous runs. If negative, run all simultaneously.')
    parser.add_argument('--forcelocal', '-l', action='store_true',
                        help='Force model to run locally instead of submitting a slurm job')
    parser.add_argument('--restart', action="store_true",
                        help='Switch to restart existing ReEDS runs')
    parser.add_argument('--skip_env_check', '-e', action="store_true",
                        help="Don't check that the reeds environment is activated")

    args = parser.parse_args()

    main(
        BatchName=args.BatchName, cases_suffix=args.cases_suffix,
        simult_runs=args.simult_runs, forcelocal=args.forcelocal,
        restart=args.restart, skip_env_check=args.skip_env_check,
    )
    