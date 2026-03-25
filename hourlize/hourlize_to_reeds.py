###############
#%% IMPORTS ###
import os
import shutil
import pandas as pd

##############
#%% INPUTS ###

this_dir_path = os.path.dirname(os.path.realpath(__file__))
reeds_path = os.path.realpath(os.path.join(this_dir_path,'..'))
# reeds_path = os.path.expanduser('~/github/ReEDS-2.0/')

###### nrelnas01
### Note: Some runs are labeled as '2000bin' in hourlize outputs but '1300bin' for the ReEDS files.
### We use 2000 bins in hourlize to make sure we end up with no more than one site per bin,
### but we don't end up using all the bins. As of 20210822, the largest number of bins per
### region/class when using an upper limit of 2000 bins is 1300 (for upv), so we use numbins=1300
### to avoid creating more bins than we need in ReEDS.

###### VRE
# tech, scenario, hourlize_run, numbins = (
#    'wind-ons', 'open', 'wind-ons_00_open_moderate', None)
# tech, scenario, hourlize_run, numbins = (
#    'wind-ons', 'reference', 'wind-ons_01_reference_moderate', None)
# tech, scenario, hourlize_run, numbins = (
#    'wind-ons', 'limited', 'wind-ons_02_limited_moderate', None)
# tech, scenario, hourlize_run, numbins = (
#    'upv', 'open', 'upv_00_open', None)
# tech, scenario, hourlize_run, numbins = (
#    'upv', 'reference', 'upv_01_reference', None)
# tech, scenario, hourlize_run, numbins = (
#    'upv', 'limited', 'upv_02_limited', None)
# tech, scenario, hourlize_run, numbins = (
#    'wind-ofs', 'open', 'wind-ofs_0_open_moderate', None)
tech, scenario, hourlize_run, numbins = (
   'wind-ofs', 'limited', 'wind-ofs_1_limited_moderate', None)

###### Load
# tech, scenario, hourlize_run, numbins = (
#     'load', 'EERbaseClip40', 'load_EER_20220906_baseline_RegularClip40_NEclip0', None)
# tech, scenario, hourlize_run, numbins = (
#     'load', 'EERbaseClip80', 'load_EER_20220906_baseline_RegularClip80_NEclip80', None)
# tech, scenario, hourlize_run, numbins = (
#     'load', 'EERhighClip40', 'load_EER_20220906_central_RegularClip40_NEclip0', None)
# tech, scenario, hourlize_run, numbins = (
#     'load', 'EERhighClip80', 'load_EER_20220906_central_RegularClip80_NEclip80', None)

#################
#%% PROCEDURE ###

#%% Get the file locations
if os.name == 'posix':
    drive = '/Volumes/'
else:
    drive = '//nrelnas01/'


if tech == 'load':
    hourlize_base = os.path.join('ReEDS','Supply_Curve_Data','LOAD','2022_Update','')
else:
    # get supply curve path on nrelnas01 from supply curve metada file. 
    df_rev = pd.read_csv(os.path.join(this_dir_path, '../inputs/supplycurvedata/metadata/rev_paths.csv'))
    df_rev = df_rev[(df_rev['tech'] == tech)&(df_rev['access_case'] == scenario)].squeeze()
    hourlize_base = os.path.join('ReEDS','Supply_Curve_Data', df_rev['sc_path'])

### Overwrite to a different path if desired
# hourlize_base = '/Volumes/ReEDS/Users/pbrown/hourlize/'
# hourlize_base = '/Users/pbrown/github2/ReEDS-2.0/hourlize/out/'
# hourlize_base = '/Volumes/ReEDS/FY22-Bespoke/NTPS/EER_20220819_reeds_load_central_2022-09-05/'

hourlize_path = os.path.join(drive, hourlize_base, hourlize_run, 'results','')

# if running locally, first copy to nrelnas destination
copy_to_nrelnas = False
if copy_to_nrelnas:
    src = os.path.join(os.path.join(os.getcwd(), "out", hourlize_run))
    dest = os.path.join(drive, hourlize_base, hourlize_run)
    # if the run already exists on nrelnas01, remove and rewrite it
    if os.path.exists(dest): shutil.rmtree(dest)
    shutil.copytree(src, dest)

noresolutionlabel = ''
binlabel = '{}bin'.format(numbins) if numbins else ''
resolutionlabel = '_{}'.format(binlabel) if numbins else ''

#################
#%% PROCEDURE ###

#%% Load
if tech == 'load':
    shutil.copy(
        os.path.join(hourlize_path,'load_hourly_multi.h5'),
        os.path.join(
            reeds_path,'inputs','variability',
            ('multi_year' if scenario in ['default','AEO'] else 'EFS_Load'),
            f'{scenario}_load_hourly.h5')
    )
    quit()

#%% Supply curve
shutil.copy(
    os.path.join(hourlize_path,'{}_supply_curve.csv'.format(tech)),
    os.path.join(reeds_path,'inputs','supplycurvedata','{}_supply_curve{}-{}.csv'.format(
        tech, resolutionlabel, scenario))
)

#%% Hourly profiles
try:
    shutil.copy(
        os.path.join(hourlize_path,'{}.csv.gz'.format(tech)),
        os.path.join(
            reeds_path,'inputs','variability','multi_year','{}-{}.csv.gz'.format(
                tech, scenario))
    )
except FileNotFoundError:
    shutil.copy(
        os.path.join(hourlize_path,'{}.h5'.format(tech)),
        os.path.join(
            reeds_path,'inputs','variability','multi_year','{}-{}.h5'.format(
                tech, scenario))
    )

#%% Prescribed and exogenous capacity
if tech == 'wind-ons':
    shutil.copy(
        os.path.join(hourlize_path,'{}_prescribed_builds.csv'.format(tech)),
        os.path.join(reeds_path,'inputs','capacitydata','{}_prescribed_builds{}_{}.csv'.format(
            tech, noresolutionlabel, scenario))
    )

    df = pd.read_csv(os.path.join(hourlize_path,'{}_exog_cap.csv'.format(tech)))
    if 'bin' in df:
        df['bin'] = 'bin' + df['bin'].astype(str)
    df.rename(columns={df.columns[0]: '*'+str(df.columns[0])}, inplace=True)
    df.to_csv(
        os.path.join(reeds_path,'inputs','capacitydata','{}_exog_cap{}_{}.csv'.format(
            tech, noresolutionlabel, scenario)),
        index=False
    )

elif tech == 'wind-ofs':
    shutil.copy(
        os.path.join(hourlize_path,'{}_prescribed_builds.csv'.format(tech)),
        os.path.join(reeds_path,'inputs','capacitydata','{}_prescribed_builds{}_{}.csv'.format(
            tech, noresolutionlabel, scenario))
    )
    # shutil.copy(
    #     os.path.join(hourlize_path,'{}_exog_cap.csv'.format(tech)),
    #     os.path.join(reeds_path,'inputs','capacitydata','{}_exog_cap{}_{}.csv'.format(
    #         tech, noresolutionlabel, scenario))
    # )

#%% Metadata
metafiles = [
    'config.py',
    'config_aggregation.json', 'config_pipeline.json',
    'config_rep-profiles.json', 'config_supply-curve.json',
    ### These two files are only included for PV, so don't worry about them for wind
    'config_rep-profiles_aggprof.json', 'config_rep-profiles_repprof.json',
]
outpath = os.path.join(
    reeds_path,'inputs','supplycurvedata','metadata',
    '{}{}_{}'.format(tech, resolutionlabel, scenario))
os.makedirs(outpath, exist_ok=True)

for metafile in metafiles:
    try:
        shutil.copy(
            os.path.join(hourlize_path,'..','inputs',metafile),
            os.path.join(reeds_path,'inputs','supplycurvedata','metadata',outpath,''),
        )
    except FileNotFoundError as err:
        print(err)

### Copy the readme file if there is one
for ext in ['.yaml', '.yml', '.md', '.txt', '']:
    try:
        shutil.copy2(
            os.path.join(hourlize_path,'..','inputs','readme'+ext),
            os.path.join(reeds_path,'inputs','supplycurvedata','metadata',outpath,''),
        )
    except:
        pass
