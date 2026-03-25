"""
Simulate PV AC output and AC clipping profiles from representative DC profiles.
Example usage on bash:
# Calculate AC clipping with ILR=1.3:
for y in {2007..2013}; do python simulate-PV-AC.py -y $y -d 1.3 -o ACclipping; done
# Calculate AC output with ILR=1.7:
for y in {2007..2013}; do python simulate-PV-AC.py -y $y -d 1.7 -o AC; done
"""

###############
#%% IMPORTS ###
import numpy as np
import pandas as pd
import os, sys, math, site
import argparse
import h5py

##############
#%% INPUTS ###

### Filepaths
revpath = os.path.expanduser(os.path.join('~','Projects','reV',''))
reeds_path = os.path.expanduser(os.path.join('~','github2','ReEDS-2.0',''))
### reV scenario
path_sim = os.path.join(revpath,'scenarios_aux','scen_032_ed1','')
profile_sim = 'dc_profiles'
path_reference = os.path.join(revpath,'scenarios_aux','')
scenario_reference = 'scen_128_ed1'

### PV assumptions
inverter_offset = 0.00295
inverter_efficiency = 0.966
### Outputs
outpath = os.path.expanduser(os.path.join(
    '~','Projects','HybridVRE','io','synthetic_profiles',''))

#######################
#%% ARGUMENT INPUTS ###
parser = argparse.ArgumentParser(description='Generate synthetic PV AC / clipping profiles')
parser.add_argument('-y', '--year', default=2012, type=int, choices=list(range(2007,2014)))
parser.add_argument('-d', '--dcac', default=1.3, type=float, 
                    help='PV inverter-loading ratio (DC/AC)')
parser.add_argument('-o', '--outprofile', default='AC', choices=['AC','ACclipping'],
                    help='output: AC or ACclipping, both as MWac/MWdc_nameplate')
args = parser.parse_args()
year = args.year
dcac = args.dcac
outprofile = args.outprofile
# #%% Settings for testing
# year = 2007
# dcac = 1.3
# outprofile = 'ACclipping'

#################
#%% PROCEDURE ###

### Process inputs
savepath = '{:.0f}_{}'.format(dcac*100, outprofile)
savename = os.path.join(outpath,savepath,'{}_rep_profiles_{}.h5').format(
    savepath, year)
print('Starting {}_rep_profiles_{}.h5'.format(savepath, year))
os.makedirs(os.path.join(outpath, savepath), exist_ok=True)

#%% Load DC profiles
infile = os.path.join(
    path_sim,profile_sim, '{}_rep_profiles_{}.h5').format(profile_sim, year)
with h5py.File(infile, 'r') as f:
    dfdcrep = pd.DataFrame(f['rep_profiles_0'][:])

    time_index = pd.Series(f['time_index'])
    time_index = time_index.map(lambda x: pd.Timestamp(str(x).strip('b').strip("'")))
    dfdcrep.index = time_index

    ### Get the profile key
    dfprofilekey = pd.DataFrame(f['meta'][:])
    dfprofilekey.resolution_128_sc_point_gid = (
        dfprofilekey.resolution_128_sc_point_gid.astype(int))

    ### Label profile columns with reV gid
    dfdcrep.columns = dfdcrep.columns.map(dfprofilekey.resolution_128_sc_point_gid)

#%% Get the order of profiles to match the metadata in path_reference
dfkey = pd.read_csv(
    os.path.join(path_reference,'{s}','{s}_sc.csv').format(s=scenario_reference),
    dtype={'resolution_128_sc_point_gid':int},
    index_col='resolution_128_sc_point_gid',
)

#%% If any profiles are missing, take them from the nearest point
### Get the missing profiles
missing_gids = [
    gid for gid in dfkey.index
    if gid not in dfprofilekey.resolution_128_sc_point_gid.values]
print('missing_gids: {}'.format('\n'.join(missing_gids)))
### Get the remaining sites to pull from
dfkey_withprofiles = dfkey.loc[
    ~dfkey.index.isin(missing_gids),
    ['longitude','latitude']
]
replacement_gids = {}
for gid in missing_gids:
    lat, lon = dfkey.loc[gid, ['latitude', 'longitude']]
    ### Get the closest point (Cartesian)
    replacement_gids[gid] = (
        (dfkey_withprofiles.longitude - lon)**2 
        + (dfkey_withprofiles.latitude - lat)**2
    ).nsmallest(1).index[0]

#%% Add the replacement profiles to dfdcrep
replacement_profiles = pd.DataFrame({
    gid: dfdcrep[replacement_gids[gid]].rename(gid) 
    for gid in replacement_gids})
dfdcrep = pd.concat([dfdcrep, replacement_profiles], axis=1)
### Make sure we have a profile for each supply-curve row
if len([gid for gid in dfkey.index if gid not in dfdcrep.columns]):
    raise Exception('Missing gids in dfkey')
### Subset to points in supply curve and match order
dfdcrep = dfdcrep[dfkey.index.values].copy()

###### Simulate desired output
#%% Always need AC profile
ac_synthetic = ((dfdcrep - inverter_offset) * inverter_efficiency).clip(0, 1/dcac)
#%% Calculate clipping if necessary
if 'clip' in outprofile:
    clipped_power = np.where(
        ### Clipping occurs when AC output is at the AC nameplate (1/dcac)
        (ac_synthetic == 1/dcac),
        ### When clipping, take the raw DC output
        ### Multiply by inverter efficiency to keep the treatment consistent for ReEDS
        (dfdcrep - 1/dcac) * inverter_efficiency,
        ### Otherwise clipping is zero
        0
    )
    clipped_power = pd.DataFrame(clipped_power, columns=dfdcrep.columns, index=dfdcrep.index)

#%% Save the synthetic hourly output file
writetime = np.array([str(pd.Timestamp(t, tz='UTC')).encode() for t in dfdcrep.index.values])
with h5py.File(savename, 'w') as f:
    f.create_dataset(
        'rep_profiles_0', data=(clipped_power if 'clip' in outprofile else ac_synthetic),
        dtype=np.float32, compression='gzip',
    )
    f.create_dataset(
        'time_index', data=writetime, dtype='S25',
        # dtype=h5py.special_dtype(vlen=str),
    )

print('Finished {}'.format(savename))

# #%% Look at raw reV outputs for comparison
# with h5py.File(
#         # '/Users/pbrown/Projects/reV/scenarios/scen_32_02_ref_rep/'
#         # 'profiles_clipped_power_032/profiles_clipped_power_032_rep_profiles_2010.h5', 
#         '/Users/pbrown/Projects/reV/scenarios/scen_128_02_ref_agg/'
#         'profiles_dc/profiles_dc_rep_profiles_2010.h5',
#         'r'
#     ) as f:
#     print(list(f))
#     print(f['time_index'].dtype)
#     # dftest = pd.DataFrame(f['rep_profiles_0'][:])

#     # time_index = pd.Series(f['time_index'])
#     # time_index = time_index.map(lambda x: pd.Timestamp(str(x).strip('b').strip("'")))
#     # dftest.index = time_index

# #%% Look at raw reV outputs for comparison
# with h5py.File(
#         '/Users/pbrown/Projects/HybridVRE/io/synthetic_profiles/'
#         # '130_ACclipping/ACclipping_rep_profiles_2010.h5',
#         '170_ACclipping/170_ACclipping_rep_profiles_2010.h5',
#         # '170_AC/AC_rep_profiles_2010.h5',
#         'r'
#     ) as f:
#     print(list(f))
#     print(f['time_index'].dtype)
#     # dftest = pd.DataFrame(f['rep_profiles_0'][:])

#     # time_index = pd.Series(f['time_index'])
#     # time_index = time_index.map(lambda x: pd.Timestamp(str(x).strip('b').strip("'")))
#     # dftest.index = time_index
