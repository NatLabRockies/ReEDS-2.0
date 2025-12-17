# %% Imports
import os
import sys
import subprocess
import argparse
import json
from glob import glob
import gdxpds
import pandas as pd

## Local imports
import reeds
import e_report_dump
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'input_processing')))
import hourly_repperiods
import hourly_writetimeseries


# %% Inferred inputs
reeds_path = os.path.dirname(__file__)

# %% Default inputs
switch_mods_default = {
    'GSw_HourlyClusterAlgorithm': 'hierarchical',
    'GSw_HourlyNumClusters': 365,
    'GSw_HourlyType': 'day',
    'GSw_HourlyChunkLengthRep': 1,
    'GSw_HourlyChunkLengthStress': 1,
    'GSw_HourlyChunkAggMethod': 1,
    'GSw_PRM_CapCredit': 0,
}


# %% Functions
def check_slurm(forcelocal=False):
    """Check whether to submit slurm jobs (if on HPC) or run locally"""
    hpc = (
        False
        if forcelocal
        else (
            True
            if int(os.environ.get('REEDS_USE_SLURM', 0)) and ('NREL_CLUSTER' in os.environ)
            else False
        )
    )
    return hpc


def solvestring_pcm(
    batch_case,
    sw,
    t,
    restartfile,
    iteration=0,
    hpc=0,
    stress_year=0,
    label='',
):
    """
    Typical inputs:
    * restartfile: batch_case if first solve year else {batch_case}_{prev_year}
    * sw: loaded from {batch_case}/inputs_case/switches.csv
    """
    savefile = f"pcm_{label}_{batch_case}_{t}i{iteration}"
    _stress_year = f"{t}i{iteration}" if stress_year in ['keep', 'default'] else stress_year
    out = (
        "gams d_solvepcm.gms"
        + (" license=gamslice.txt" if hpc else '')
        + f" o={os.path.join('lstfiles', f'{savefile}.lst')}"
        + f" r={os.path.join('g00files', restartfile)}"
        + " gdxcompress=1"
        + f" xs={os.path.join('g00files', savefile)}"
        + ' logOption=4 appendLog=1'
        + f" logFile=gamslog_pcm_{label}_{t}.txt"
        + f" --case={batch_case}"
        + f" --cur_year={t}"
        + f" --stress_year={stress_year}"
        + f" --temporal_inputs=pcm_{label}"
        + ''.join(
            [
                f" --{s}={sw[s]}"
                for s in [
                    'GSw_SkipAugurYear',
                    'GSw_HourlyType',
                    'GSw_HourlyWrapLevel',
                    'GSw_ClimateWater',
                    'GSw_Canada',
                    'GSw_ClimateHydro',
                    'GSw_HourlyChunkLengthRep',
                    'GSw_HourlyChunkLengthStress',
                    'GSw_StateCO2ImportLevel',
                    'GSw_PVB_Dur',
                    'GSw_ValStr',
                    'GSw_gopt',
                    'solver',
                    'debug',
                    'startyear',
                ]
            ]
        )
        + '\n'
    )

    return out


def pcm_report_string(batch_case, sw, t, iteration=0, hpc=0, label=''):
    savefile = f"pcm_{label}_{batch_case}_{t}i{iteration}"
    out = (
        "gams e_report.gms"
        + (' license=gamslice.txt' if hpc else '')
        + f" o={os.path.join('lstfiles', f'report_pcm_{label}_{t}_{batch_case}.lst')}"
        + f" r={os.path.join('g00files', savefile)}"
        + ' gdxcompress=1'
        + ' logOption=4 appendLog=1'
        + f" logFile=gamslog_pcm_{label}_{t}.txt"
        + f" --fname=pcm_{label}_{t}_{batch_case}"
        + " --GSw_calc_powfrac=0 \n"
    )
    return out


def submit_job(casepath, command_string, jobname='', joblabel='', bigmem=0):
    """
    Create a slurm job submission script for `command_string` at `casepath`,
    then submit it.
    Uses the slurm settings from {reeds_path}/srun_template.sh.
    """
    ### Get the SLURM boilerplate
    commands_header, commands_sbatch, commands_other = [], [], []
    with open(os.path.join(reeds_path, 'srun_template.sh'), 'r') as f:
        for line in f:
            if bigmem and ('--mem=' in line):
                line = '#SBATCH --mem=500000'

            if line.strip().startswith('#!'):
                commands_header.append(line.strip())
            elif line.strip().startswith('#SBATCH'):
                commands_sbatch.append(line.strip())
            else:
                commands_other.append(line.strip())

    ### Add the command for this run
    slurm = (
        commands_header
        + commands_sbatch
        + ([f"#SBATCH --job-name={jobname}"] if len(jobname) else [])
        + [f"#SBATCH --output={os.path.join(casepath, 'slurm-%j.out')}"]
        + commands_other
        + ['']
        + [command_string]
    )
    ### Write the SLURM command
    callfile = os.path.join(casepath, f'submit_{joblabel}.sh')
    with open(callfile, 'w+') as f:
        for line in slurm:
            f.writelines(line + '\n')
    ### Submit the job
    batchcom = f'sbatch {callfile}'
    subprocess.Popen(batchcom.split())


# %%
def main(casepath, t, switch_mods=switch_mods_default, label='', overwrite=False):
    """
    Args:
        kwargs: Passed to hourly_reppreiods.main()
    """
    # %% Switch to run folder
    os.chdir(casepath)

    # %% Get the run settings
    sw = reeds.io.get_switches(casepath)
    years = (
        pd.read_csv(os.path.join(casepath, 'inputs_case', 'modeledyears.csv'))
        .columns.astype(int)
        .values
    )
    _t = t if t > 0 else max(years)

    # %% Set up logger
    reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(casepath, f'gamslog_pcm_{label}_{_t}.txt'),
    )
    

    # %% Get and modify the switch settings
    sw_pcm = sw.copy()
    for key, val in switch_mods.items():
        sw_pcm[key] = val

    # %% Write the inputs for PCM
    if (not os.path.isdir(os.path.join(casepath, 'inputs_case', f'pcm_{label}'))) or overwrite:
        hourly_repperiods.main(
            sw=sw_pcm,
            reeds_path=reeds_path,
            inputs_case=os.path.join(casepath, 'inputs_case'),
            periodtype=f'pcm_{label}',
            minimal=1,
        )
        hourly_writetimeseries.main(
            sw=sw_pcm,
            reeds_path=reeds_path,
            inputs_case=os.path.join(casepath, 'inputs_case'),
            periodtype=f'pcm_{label}',
            make_plots=0,
        )
    ## Write a set of empty "stress0" inputs to turn off stress periods for PCM
    stresspath = os.path.join(casepath, 'inputs_case', 'stress0')
    if (not os.path.isdir(stresspath)) or overwrite:
        os.makedirs(stresspath, exist_ok=True)
        pd.DataFrame(columns=['rep_period', 'year', 'yperiod', 'actual_period']).to_csv(
            os.path.join(stresspath, 'period_szn.csv'),
            index=False,
        )
        hourly_writetimeseries.main(
            sw=sw_pcm,
            reeds_path=reeds_path,
            inputs_case=os.path.join(casepath, 'inputs_case'),
            periodtype='stress0',
            make_plots=0,
        )

    # %% Get ReEDS LP for specified year
    batch_case = os.path.basename(casepath)
    ### Get the restartfile and get the last year/iteration if t=0 and iteration='last'
    if _t == min(years):
        restartfile = batch_case
        _iteration = 0
    elif iteration == 'last':
        restartfile = sorted(glob(os.path.join(casepath, 'g00files', f"{batch_case}_{_t}i*")))[-1]
        _iteration = int(restartfile[: -len('.g00')].split('i')[-1])
    else:
        _iteration = iteration
        restartfile = os.path.join(casepath, 'g00files', f"{batch_case}_{_t}i{_iteration}.g00")

    cmd_gams = solvestring_pcm(
        batch_case=batch_case,
        sw=sw_pcm,
        t=_t,
        restartfile=restartfile,
        iteration=_iteration,
        hpc=int(sw['hpc']),
        label=label,
    )
    print(cmd_gams)

    ### Run GAMS LP
    result = subprocess.run(cmd_gams, shell=True)
    if result.returncode:
        raise Exception(f'd_solvepcm.gms failed with return code {result.returncode}')

    # %% Dump results to gdx
    cmd_report = pcm_report_string(
        batch_case=batch_case,
        sw=sw_pcm,
        t=_t,
        iteration=_iteration,
        hpc=int(sw['hpc']),
        label=label,
    )
    print(cmd_report)

    result = subprocess.run(cmd_report, shell=True)
    if result.returncode:
        raise Exception(f'e_report.gms failed with return code {result.returncode}')
    
    # cmd_dump = f"python e_report_dump.py {casepath} -c"
    # print(cmd_dump)
    # subprocess.run(cmd_dump, shell=True)

    # %% Dump gdx to h5
    ## Get new file names if applicable
    dfparams = pd.read_csv(
        os.path.join(casepath, "e_report_params.csv"),
        comment="#",
        index_col="param",
    )
    rename = dfparams.loc[~dfparams.output_rename.isnull(), "output_rename"].to_dict()
    rename = {k.split("(")[0]: v for k, v in rename.items()}
    print(f"renamed parameters: {rename}")

    print("Loading outputs gdx")
    dict_out = gdxpds.to_dataframes(
        os.path.join(casepath, 'outputs', f"rep_pcm_{label}_{_t}_{batch_case}.gdx")
    )
    print("Finished loading outputs gdx")

    outputs_path = os.path.join(casepath, 'outputs', f'pcm_{label}_{_t}')
    os.makedirs(outputs_path, exist_ok=True)
    e_report_dump.write_dfdict(
        dfdict=dict_out,
        outputs_path=outputs_path,
        rename=rename,
    )

    #%% Dump all variaables in e_report_params.csv to their own csv files
    e_report_dump.dfdict_to_csv(
        dict_out,
        filepath=outputs_path,
        rename=rename,
    )


# %% Procedure
if __name__ == '__main__':
    # %% Argument inputs
    parser = argparse.ArgumentParser(
        description='Run ReEDS in PCM mode',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('casepath', type=str, help='ReEDS-2.0/runs/{case} directory')
    parser.add_argument(
        '--year',
        '-t',
        type=int,
        default=0,
        help='Year to run (must have the corresponding .g00 file), or 0 for last year',
    )
    parser.add_argument(
        '--iteration',
        '-i',
        type=str,
        default='last',
        help="Iteration to run, or 'last' for last iteration",
    )
    parser.add_argument(
        '--switch_mods',
        '-s',
        type=json.loads,
        default=json.dumps(switch_mods_default),
        help=(
            'Dictionary-formated string of switch arguments for PCM. '
            'Use single quotes outside the dictionary and double quotes for keys, as in:\n'
            '`-s \'{"GSw_HourlyChunkLengthRep":4}\'`'
        ),
    )
    parser.add_argument('--label', '-l', type=str, default='', help='Label for PCM outputs')
    parser.add_argument(
        '--overwrite',
        '-o',
        action='store_true',
        help="Overwrite input files if they already exist (otherwise don't rewrite them)",
    )
    parser.add_argument(
        '--forcelocal',
        '-f',
        action='store_true',
        help='Run locally (including on a compute node as part of a job)',
    )
    parser.add_argument('--bigmem', '-b', action='store_true', help='Use bigmem node')

    args = parser.parse_args()
    casepath = args.casepath
    t = args.year
    iteration = args.iteration
    switch_mods = args.switch_mods
    label = args.label
    if not len(label):
        label = f"{switch_mods['GSw_HourlyType'][0]}{switch_mods['GSw_HourlyChunkLengthRep']}h"
    overwrite = args.overwrite
    forcelocal = args.forcelocal
    bigmem = args.bigmem

    # #%% Inputs for debugging
    # casepath = os.path.join(reeds_path, 'runs', 'v20250206_pcmM0_Pacific')
    # t = 0
    # iteration = 'last'
    # switch_mods = switch_mods_default
    # switch_mods = {
    #     'GSw_HourlyClusterAlgorithm': 'hierarchical',
    #     'GSw_HourlyType': 'day', 'GSw_HourlyNumClusters': 365,
    #     # 'GSw_HourlyType': 'wek', 'GSw_HourlyNumClusters': 73,
    #     'GSw_HourlyChunkLengthRep': 4,
    # }
    # label = f"{switch_mods['GSw_HourlyType'][0]}{switch_mods['GSw_HourlyChunkLengthRep']}h"
    # forcelocal = False
    # overwrite = False
    # bigmem = True

    # %% Set up logger
    log = reeds.log.makelog(scriptname=__file__, logpath=os.path.join(casepath, "gamslog.txt"))

    # %% Determine whether to submit slurm job
    hpc = check_slurm(forcelocal=forcelocal)
    print(f'Running pcm {"on HPC" if hpc else "locally"}')

    ### Run it
    if not hpc:
        main(casepath=casepath, t=t, switch_mods=switch_mods, label=label, overwrite=overwrite)
    else:
        command_string = (
            f"python run_pcm.py {casepath} "
            f"--year={t} "
            f"--iteration={iteration} "
            f"--switch_mods='{json.dumps(switch_mods)}' "
            f"--label={label} "
            "--forcelocal "
        ) + ("--overwrite " if overwrite else "")
        joblabel = f"pcm_{label}_{t}"
        jobname = f"{os.path.basename(casepath)}-{joblabel}"
        submit_job(
            casepath=casepath,
            command_string=command_string,
            jobname=jobname,
            joblabel=joblabel,
            bigmem=bigmem,
        )
    
    print('PCM run complete')
