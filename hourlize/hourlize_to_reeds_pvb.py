###############
#%% IMPORTS ###
import os
import shutil
import pandas as pd

##############
#%% INPUTS ###

reeds_path = os.path.expanduser('~/github/ReEDS-2.0/')
scenario = 'reference'

### Synthetic AC profiles with varying ILR
# ilr, clip, hourlize_run = (
#     140, False, 'upv_140AC_scen_128_ed1_2021-08-23-15-28-51-255459')
# ilr, clip, hourlize_run = (
#     140, True, 'upv_140ACclip_scen_128_ed1_2021-08-23-17-04-01-944895')
# ilr, clip, hourlize_run = (
#     150, False, 'upv_150AC_scen_128_ed1_2021-08-23-17-14-05-486674')
# ilr, clip, hourlize_run = (
#     150, True, 'upv_150ACclip_scen_128_ed1_2021-08-23-17-21-32-272765')
# ilr, clip, hourlize_run = (
#     160, False, 'upv_160AC_scen_128_ed1_2021-08-23-17-28-02-380101')
# ilr, clip, hourlize_run = (
#     160, True, 'upv_160ACclip_scen_128_ed1_2021-08-23-17-35-08-904615')
# ilr, clip, hourlize_run = (
#     180, False, 'upv_180AC_scen_128_ed1_2021-08-23-17-40-51-409940')
# ilr, clip, hourlize_run = (
#     180, True, 'upv_180ACclip_scen_128_ed1_2021-08-23-17-48-55-954596')
# ilr, clip, hourlize_run = (
#     200, False, 'upv_200AC_scen_128_ed1_2021-08-23-15-06-58-119913')
# ilr, clip, hourlize_run = (
#     200, True, 'upv_200ACclip_scen_128_ed1_2021-08-23-15-17-06-641848')
# ilr, clip, hourlize_run = (
#     220, False, 'upv_220AC_scen_128_ed1_2021-08-23-17-55-55-538674')
# ilr, clip, hourlize_run = (
#     220, True, 'upv_220ACclip_scen_128_ed1_2021-08-23-18-14-20-737136')
ilr, clip, hourlize_run = (
    240, False, 'upv_240AC_scen_128_ed1_2021-08-23-18-20-48-188863')
# ilr, clip, hourlize_run = (
#     240, True, 'upv_240ACclip_scen_128_ed1_2021-08-23-18-39-40-185662')
# ilr, clip, hourlize_run = (
#     260, False, 'upv_260AC_scen_128_ed1_2021-08-24-08-04-42-756328')
# ilr, clip, hourlize_run = (
#     260, True, 'upv_260ACclip_scen_128_ed1_2021-08-24-08-12-12-732778')
# ilr, clip, hourlize_run = (
#     280, False, 'upv_280AC_scen_128_ed1_2021-08-24-08-45-52-267227')
# ilr, clip, hourlize_run = (
#     300, False, 'upv_300AC_scen_128_ed1_2021-08-24-10-01-43-691120')
# ilr, clip, hourlize_run = (
#     300, True, 'upv_300ACclip_scen_128_ed1_2021-08-24-10-45-51-887548')

#################
#%% PROCEDURE ###

#%% Get the file locations
if os.name == 'posix':
    drive = '/Volumes/'
else:
    drive = '//nrelnas01/'

hourlize_base = os.path.join('ReEDS','Users','pbrown','hourlize','synthetic','')
# hourlize_base = '/Volumes/ReEDS/Users/pbrown/hourlize/'
hourlize_path = os.path.join(drive, hourlize_base, hourlize_run, 'results','')

#################
#%% PROCEDURE ###

#%% Capacity factor
pd.read_csv(
    os.path.join(hourlize_path,'upv_cf_ts.csv')
).drop('cfsigma', axis=1, errors='ignore').round({'cfmean':5}).to_csv(
    os.path.join(
        reeds_path,'inputs','cf','upv{}{}_cf_ts-{}.csv'.format(
            ilr, 'clip' if clip else '', scenario)),
    index=False,
)

#%% Hourly profiles
if not clip:
    shutil.copy(
        os.path.join(hourlize_path,'upv.csv.gz'),
        os.path.join(
            reeds_path,'inputs','variability','multi_year','upv_{}AC-{}.csv.gz'.format(
                ilr, scenario))
    )
