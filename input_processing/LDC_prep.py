#%% IMPORTS
import argparse
import os
import pandas as pd
import numpy as np
import h5py

#%% FUNCTIONS ###
def read_file(filename, index_columns=1):
    """
    Read input file of various types (for backwards-compatibility)
    """
    # Try reading a .h5 file written by pandas
    try:
        df = pd.read_hdf(filename+'.h5')
    # Try reading a .h5 file written by h5py
    except (ValueError, TypeError, FileNotFoundError, OSError):
        try:
            with h5py.File(filename+'.h5', 'r') as f:
                keys = list(f)
                datakey = 'data' if 'data' in keys else ('cf' if 'cf' in keys else 'load')
                ### If none of these keys work, we're dealing with EER-formatted load
                if datakey not in keys:
                    years = [int(y) for y in keys if y != 'columns']
                    df = pd.concat(
                        {y: pd.DataFrame(f[str(y)][...]) for y in years},
                        axis=0)
                    df.index = df.index.rename(['year','hour'])
                else:
                    df = pd.DataFrame(f[datakey][:])
                    df.index = pd.Series(f['index']).values
                df.columns = pd.Series(f['columns']).map(
                    lambda x: x if type(x) is str else x.decode('utf-8')).values
        # Fall back to .csv.gz
        except (FileNotFoundError, OSError):
            df = pd.read_csv(
                filename+'.csv.gz', index_col=list(range(index_columns)),
                float_precision='round_trip',
            )
    ### Some files are saved as float16, so convert to float32
    ### to prevent issues with large/small numbers
    return df.astype(np.float32)


def local_to_eastern(df, reeds_path, val_r, by_year=False):
    """
    Convert a wide dataframe from local to eastern time.
    The column names are assumed to end with _{r}.
    Inputs
    ------
    by_year: Indicate whether to roll by year (True) or to roll the whole
    dataset at once (False)
    """
    ### Get some inputs
    rb2tz = pd.read_csv(
        os.path.join(reeds_path,'inputs','variability','reeds_ba_tz_map.csv'),
        index_col='r')

    rb2tz['hourshift'] = rb2tz.tz.map({'PT':+3, 'MT':+2, 'CT':+1, 'ET':0})
    r2shift = pd.Series(val_r, name = 'r').map(rb2tz.hourshift).dropna().astype(int)
    r2shift.index = pd.Series(val_r)
    ### Roll the input columns according to the shift
    if by_year:
        dfout = pd.concat({
            year: pd.DataFrame(
                {col: np.roll(df.loc[year][col], r2shift[col.split('_')[-1]]) for col in df},
                index=df.loc[year].index)
            for year in df.index.get_level_values('year').unique()
        }, axis=0, names=('year',))
    else:
        dfout = pd.DataFrame(
            {col: np.roll(df[col], r2shift[col.split('_')[-1]]) for col in df},
            index=df.index)

    return dfout


def csp_dispatch(cfcsp, sm=2.4, storage_duration=10):
    """
    Use a simple no-foresight heuristic to dispatch CSP.
    Excess energy from the solar field (i.e. energy above the max plant power output)
    is sent to storage, and energy in storage is dispatched as soon as possible.

    Inputs
    ------
    cfcsp: hourly energy output of solar field [fraction of max field output]
    sm: solar multiple [solar field max output / plant max power output]
    storage_duration: hours of storage as multiple of plant max power output
    """
    ### Calculate derived dataframes
    ## Field energy output as fraction of plant max output
    dfcf = cfcsp * sm
    ## Excess energy as fraction of plant max output
    clipped = (dfcf - 1).clip(lower=0)
    ## Remaining generator capacity after direct dispatch (can be used for storage dispatch)
    headspace = (1 - dfcf).clip(lower=0)
    ## Direct generation from solar field
    direct_dispatch = dfcf.clip(upper=1)

    ### Numpy arrays
    clipped_val = clipped.values
    headspace_val = headspace.values
    hours = range(len(clipped_val))
    storage_dispatch = np.zeros(clipped_val.shape)
    ## Need one extra storage hour at the end, though it doesn't affect dispatch
    storage_energy_hourstart = np.zeros((len(hours)+1, clipped_val.shape[1]))

    ### Loop over all hours and simulate dispatch
    for h in hours:
        ### storage dispatch is...
        storage_dispatch[h] = np.where(
            clipped_val[h],
            ## zero if there's clipping in hour
            0,
            ## otherwise...
            np.where(
                headspace_val[h] > storage_energy_hourstart[h],
                ## storage energy at start of hour if more headspace than energy
                storage_energy_hourstart[h],
                ## headspace if more storage energy than headspace
                headspace_val[h]
            )
        )
        ### storage energy at start of next hour is...
        storage_energy_hourstart[h+1] = np.where(
            clipped_val[h],
            ## storage energy in current hour plus clipping if clipping
            storage_energy_hourstart[h] + clipped_val[h],
            ## storage energy in current hour minus dispatch if not clipping
            storage_energy_hourstart[h] - storage_dispatch[h]
        )
        storage_energy_hourstart[h+1] = np.where(
            storage_energy_hourstart[h+1] > storage_duration,
            ## clip storage energy to storage duration if energy > duration
            storage_duration,
            ## otherwise no change
            storage_energy_hourstart[h+1]
        )

    ### Format as dataframe and calculate total plant dispatch
    storage_dispatch = pd.DataFrame(
        index=clipped.index, columns=clipped.columns, data=storage_dispatch)

    total_dispatch = direct_dispatch + storage_dispatch

    return total_dispatch


def get_distpv_profiles(inputs_case, recf):
    """
    We only have one year's profile (2012) for distributed PV. Because we want to
    maintain weather coincidence between distpv and upv, we start with the lowest-cf
    upv profile in each region, scale it by its CF ratio with distributed PV in that
    region, and take that scaled profile as the distpv profile.
    """
    ### Get average CF (used to scale down UPV profiles to generate distpv profiles)
    distpv_meancf = (
        pd.read_csv(os.path.join(inputs_case,'distPVCF_hourly.csv'), index_col=0)
        .mean(axis=1).rename_axis('r').rename('cf')
    )

    ### Get the worst upv resource in each region and use its profile for distpv,
    ### scaled by the distpv/upv CF ratio
    upv_cf = (
        recf[[c for c in recf if c.startswith('upv')]].mean()
        .rename_axis('resource').rename('cf').reset_index()
    )
    upv_cf['r'] = upv_cf.resource.map(lambda x: x.split('_')[-1])

    worst_upv = (
        upv_cf.sort_values(['r','cf'])
        .drop_duplicates('r', keep='first').set_index('r').resource)

    ### Get the distpv/upv CF ratio for those UPV resources
    distpv_upv_cf_ratio = (
        distpv_meancf / upv_cf.set_index('resource').loc[worst_upv].set_index('r').cf)

    ### Scale UPV Profiles by distpv/upv CF ratio
    distpv_profiles = (
        recf[worst_upv].rename(columns=dict(zip(worst_upv,worst_upv.index)))
        * distpv_upv_cf_ratio
    ).clip(upper=1)
    distpv_profiles.columns = 'distpv_' + distpv_profiles.columns

    return distpv_profiles


#%% Main function
def main(reeds_path, inputs_case):
    # #%% Settings for debugging ###
    # reeds_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
    # inputs_case = os.path.join(
    #     reeds_path,'runs','v20230227_augurM1_WECC','inputs_case')

    #%% Fixed inputs
    GSw_CSP_Types = '1_2'

    #%% Inputs from switches
    sw = pd.read_csv(os.path.join(inputs_case, 'switches.csv'), 
                     header=None, index_col=0).squeeze('columns')
    GSw_EFS1_AllYearLoad = sw.GSw_EFS1_AllYearLoad
    GSw_SitingWindOns = sw.GSw_SitingWindOns
    GSw_SitingWindOfs = sw.GSw_SitingWindOfs
    GSw_SitingUPV = sw.GSw_SitingUPV
    GSw_PVB_Types = sw.GSw_PVB_Types
    GSw_PVB = int(sw.GSw_PVB)

    #%%### Load inputs
    ### Override GSw_PVB_Types if GSw_PVB is turned off
    GSw_PVB_Types = (
        [int(i) for i in GSw_PVB_Types.split('_')] if int(GSw_PVB)
        else []
    )
    GSw_CSP_Types = [int(i) for i in GSw_CSP_Types.split('_')]

    # -------- Define the file paths --------
    folder = 'multi_year'
    path_variability = os.path.join(reeds_path,'inputs','variability')

    # -------- Datetime mapper --------
    hdtmap = pd.read_csv(os.path.join(inputs_case, 'h_dt_szn.csv'))

    ###### Load the input parameters
    scalars = pd.read_csv(os.path.join(inputs_case,'scalars.csv'), 
                          header=None, usecols=[0,1], index_col=0
                          ).squeeze('columns')
    ### distloss
    distloss = scalars['distloss']

    ### BAs present in the current run
    val_r = sorted(pd.read_csv(os.path.join(inputs_case, 'val_r.csv'), 
                               header=None).squeeze('columns').tolist())
    ### Years in the current run
    solveyears = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv'),
        header=0
    ).columns.astype(int).values

    ### Load spatial hierarchy
    hierarchy = pd.read_csv(
        os.path.join(inputs_case,'hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    ### Add ccreg column with the desired hierarchy level
    if sw['capcredit_hierarchy_level'] == 'r':
        hierarchy['ccreg'] = hierarchy.index.copy()
    else:
        hierarchy['ccreg'] = hierarchy[sw.capcredit_hierarchy_level].copy()
    ### Map regions to new ccreg's
    r2ccreg = hierarchy['ccreg']
    # Map BAs to states and census divisions for use with AEO load multipliers
    st2rb = hierarchy.reset_index(drop=False)[['r', 'st']]
    cd2rb = hierarchy.reset_index(drop=False)[['r', 'cendiv']]
    
    # Get technology subsets
    tech_table = pd.read_csv(
        os.path.join(inputs_case,'tech-subset-table.csv'), index_col=0).fillna(False).astype(bool)
    techs = {tech:list() for tech in list(tech_table)}
    for tech in techs.keys():
        techs[tech] = tech_table[tech_table[tech]].index.values.tolist()
        techs[tech] = [x.lower() for x in techs[tech]]
        temp_save = []
        temp_remove = []
        # Interpreting GAMS syntax in tech-subset-table.csv
        for subset in techs[tech]:
            if '*' in subset:
                temp_remove.append(subset)
                temp = subset.split('*')
                temp2 = temp[0].split('_')
                temp_low = pd.to_numeric(temp[0].split('_')[-1])
                temp_high = pd.to_numeric(temp[1].split('_')[-1])
                temp_tech = ''
                for n in range(0,len(temp2)-1):
                    temp_tech += temp2[n]
                    if not n == len(temp2)-2: temp_tech += '_'
                for c in range(temp_low,temp_high+1):
                    temp_save.append('{}_{}'.format(temp_tech,str(c)))
        for subset in temp_remove:
            techs[tech].remove(subset)
        techs[tech].extend(temp_save)
    vre_dist = techs['VRE_DISTRIBUTED']

    #HANDLING STATIC INPUTS FOR THE FIRST SOLVE YEAR
    # Load
    #       - Filter out load profiles not included in this run
    #       - Scale load profiles by distribution loss factor and load calibration factor
    # Resources:
    #       - Filter out all resources not included in this run
    #       - Add the distributed PV resources
    # RECF:
    #       - Add the distributed PV profiles
    #       - Filter out all resources not included in this run
    #       - Sort the columns in recf to be in the same order as the rows in resources
    #       - Scale distributed resource CF profiles by distribution loss factor and tiein loss factor
    # ------- Read in the static inputs for this run -------

    df_windons = read_file(
        os.path.join(path_variability, folder, 'wind-ons-{}'.format(GSw_SitingWindOns)))
    df_windons.columns = ['wind-ons_' + col for col in df_windons]
    ### Don't do aggregation in this case, so make a 1:1 lookup table
    lookup = pd.DataFrame({'ragg':df_windons.columns.values})
    lookup['r'] = lookup.ragg.map(lambda x: x.rsplit('_',1)[1])
    lookup['i'] = lookup.ragg.map(lambda x: x.rsplit('_',1)[0])

    ### Offshore
    df_windofs = read_file(
        os.path.join(path_variability, folder, 'wind-ofs-{}'.format(GSw_SitingWindOfs)))
    df_windofs.columns = ['wind-ofs_' + col for col in df_windofs]

    df_upv = read_file(
        os.path.join(path_variability, folder, 'upv-{}'.format(GSw_SitingUPV)))
    df_upv.columns = ['upv_' + col for col in df_upv]

    df_dupv = read_file(os.path.join(path_variability, folder, 'dupv'))
    df_dupv.columns = ['dupv_' + col for col in df_dupv]

    cspcf = read_file(
        os.path.join(path_variability, folder, 'csp-reference'))
    
    keep = [c for c in cspcf if c.split('_')[1] in val_r]
    cspcf = cspcf[keep]

    #%% Format PV+battery profiles
    ### Get the PVB types
    pvb_ilr = pd.read_csv(os.path.join(inputs_case, 'pvb_ilr.csv'), 
                          header=0, names=['pvb_type','ilr'], 
                          index_col='pvb_type').squeeze('columns')
    df_pvb = {}
    for pvb_type in GSw_PVB_Types:
        ilr = int(pvb_ilr['pvb{}'.format(pvb_type)] * 100)
        ### UPV uses ILR = 1.3, so use its profile if ILR = 1.3
        infile = 'upv' if ilr == 130 else 'upv_{}AC'.format(ilr)
        df_pvb[pvb_type] = read_file(
            os.path.join(path_variability, 'multi_year', '{}-{}'.format(infile, GSw_SitingUPV)))
        df_pvb[pvb_type].columns = ['pvb{}_{}'.format(pvb_type, c)
                                    for c in df_pvb[pvb_type].columns]
        df_pvb[pvb_type].index = df_upv.index.copy()

    recf = pd.concat(
        [df_windons, df_windofs, df_upv, df_dupv]
        + [df_pvb[pvb_type] for pvb_type in df_pvb],
        sort=False, axis=1, copy=False)

    toadd = pd.DataFrame({'ragg': [c for c in recf.columns if c not in lookup.ragg.values]})
    toadd['r'] = [c.rsplit('_', 1)[1] for c in toadd.ragg.values]
    toadd['i'] = [c.rsplit('_', 1)[0] for c in toadd.ragg.values]
    resources = (
        pd.concat([lookup, toadd], axis=0, ignore_index=True)
        .rename(columns={'ragg':'resource','r':'area','i':'tech'})
        .sort_values('resource').reset_index(drop=True)
    )

    # ------- Performing load modifications -------
    if GSw_EFS1_AllYearLoad == 'historic':
        load_historical = read_file(os.path.join(basedir, 'inputs', 'loaddata',
                                                 'historic_load_hourly'))[val_r]
        # Read load multipliers
        load_multiplier = pd.read_csv(os.path.join(inputs_case, 'load_multiplier.csv'))
        
        if 'cendiv' in load_multiplier.columns:
            # AEO multipliers at the Census division level are in a wide format so
            # need to be changed to a long format
            load_multiplier = pd.melt(load_multiplier, id_vars=['cendiv'], 
                                      var_name='year', value_name='multiplier')
            load_multiplier['year'] = load_multiplier['year'].astype(int)
            # Map census division multipliers to BAs
            load_multiplier = load_multiplier.merge(cd2rb, on=['cendiv'], how='outer'
                                                    ).dropna(axis=0, how='any')
        else:
            # AEO multipliers at the state level are already in a long format
            # Map state multipliers to BAs
            load_multiplier = load_multiplier.merge(st2rb, on=['st'], how='outer'
                                                    ).dropna(axis=0, how='any')
        # Subset load multipliers for solve years only 
        load_multiplier = load_multiplier[load_multiplier['year'].isin(solveyears)
                                          ][['year', 'r', 'multiplier']]
        # Reformat hourly load profiles to merge with load multipliers
        load_historical.index = pd.MultiIndex.from_frame(hdtmap[['year','hour']])
        load_historical.reset_index(drop=False, inplace=True)
        load_historical = pd.melt(load_historical, id_vars=['year', 'hour'], 
                                  var_name='r', value_name='load')
        # Merge load multipliers into hourly load profiles 
        load_historical = load_historical.merge(load_multiplier, on=['r'], 
                                                how='outer', suffixes=('_w', '')
                                                ).reset_index(drop=True)
        load_historical.sort_values(by=['r', 'year'], ascending=True, inplace=True)
        load_historical['load'] *= load_historical['multiplier']
        load_historical = load_historical[['year', 'hour', 'r', 'load']]
        # Hours should be 0-8759 (not 1-8760) for later use with hourly_repperiods.py
        load_historical['hour'] -= 1
        # Reformat hourly load profiles for GAMS
        load_profiles = load_historical.pivot_table(index=['year', 'hour'], 
                                                    columns='r', values='load'
                                                    ).reset_index()
        load_profiles = load_profiles.set_index(['year', 'hour'])
        
    else:
        load_profiles = read_file(
            os.path.join(reeds_path,'inputs','loaddata',(GSw_EFS1_AllYearLoad+'_load_hourly')),
            index_columns=2,
        ).loc[solveyears,val_r]
        ### If using EFS-style demand with only a single 2012 weather year, concat each profile
        ### 7 times to match the 7-year VRE profiles
        load_profiles_wide = load_profiles.unstack('year')
        if len(load_profiles_wide) == 8760:
            load_profiles = (
                pd.concat([load_profiles_wide]*7, axis=0, ignore_index=True)
                .rename_axis('hour').stack('year')
                .reorder_levels(['year','hour']).sort_index(axis=0, level=['year','hour'])
            )

    # Adjusting load profiles by distribution loss factor and load calibration factor
    load_profiles /= (1 - distloss)


    # ------- Performing resource modifications -------
    #%%### Distributed PV (distpv)
    ### Get distpv profiles
    distpv_profiles = get_distpv_profiles(inputs_case, recf)
    ### Get distpv resources and include in list of resources
    distpv_resources = pd.DataFrame({'resource':distpv_profiles.columns, 'tech':'distpv'})
    distpv_resources['area'] = distpv_resources.resource.map(lambda x: x.split('_')[-1])

    # Resetting indices before merging to assure there are no issues in the merge
    resources = pd.concat([resources, distpv_resources], sort=False, ignore_index=True)
    recf = pd.merge(
        left=recf.reset_index(drop=True), right=distpv_profiles.reset_index(drop=True),
        left_index=True, right_index=True, copy=False)

    # Filtering out profiles of resources not included in this run
    # and sorting to match the order of the rows in resources
    resources = resources[
        resources['area'].isin(val_r)
    ].sort_values(['resource','area'])
    recf = recf.reindex(labels=resources['resource'].drop_duplicates(), axis=1, copy=False)

    ### Scale up dupv and distpv by 1/(1-distloss)
    recf.loc[
        :, resources.loc[resources.tech.isin(vre_dist),'resource'].values
    ] /= (1 - distloss)

    # Set the column names for resources to match ReEDS-2.0
    resources['ccreg'] = resources.area.map(r2ccreg)
    resources.rename(columns={'area':'r','tech':'i'}, inplace=True)
    resources = resources[['r','i','ccreg','resource']]


    #%%### Concentrated solar thermal power (CSP)
    ### Create CSP resource label for each CSP type (labeled by "tech" as csp1, csp2, etc)
    csptechs = [f'csp{c}' for c in GSw_CSP_Types]
    csp_resources = pd.concat({
        tech:
        pd.DataFrame({
            'resource': cspcf.columns,
            'r': cspcf.columns.map(lambda x: x.split('_')[1]),
            'class': cspcf.columns.map(lambda x: x.split('_')[0])})
        for tech in csptechs
    }, axis=0, names=('tech',)).reset_index(level='tech')

    csp_resources = (
        csp_resources
        .assign(i=csp_resources['tech'] + '_' + csp_resources['class'].astype(str))
        .assign(resource=csp_resources['tech'] + '_' + csp_resources['resource'])
        .assign(ccreg=csp_resources.r.map(r2ccreg))
        .loc[csp_resources.r.isin(val_r)]
        [['i','r','resource','ccreg']]
    )

    ###### Simulate CSP dispatch for each design
    ### Get solar multiples
    sms = {tech: scalars[f'csp_sm_{tech.strip("csp")}'] for tech in csptechs}
    ### Get storage durations
    storage_duration = pd.read_csv(
        os.path.join(inputs_case,'storage_duration.csv'), header=None, index_col=0).squeeze()
    ## All CSP resource classes have the same duration for a given tech, so just take the first one
    durations = {tech: storage_duration[f'csp{tech.strip("csp")}_1'] for tech in csptechs}
    ### Run the dispatch simulation for modeled regions
    
    csp_system_cf = pd.concat({
        tech: csp_dispatch(cspcf, sm=sms[tech], storage_duration=durations[tech])
        for tech in csptechs
    }, axis=1)
    ## Collapse column labels to single strings
    csp_system_cf.columns = ['_'.join(c) for c in csp_system_cf.columns]

    ### Add CSP to RE output dataframes
    recf = pd.concat([recf, csp_system_cf.reset_index(drop=True)], axis=1)
    resources = pd.concat([resources, csp_resources], axis=0)


    #%%### Convert from local time to Eastern time
    recf_eastern = local_to_eastern(recf, reeds_path, val_r, by_year=False)
    load_eastern = local_to_eastern(load_profiles, reeds_path, val_r, by_year=True)
    cspcf_eastern = local_to_eastern(cspcf, reeds_path, val_r, by_year=False)


    #%%### Write outputs
    load_eastern.astype(np.float32).to_hdf(
        os.path.join(inputs_case,'load.h5'), key='data', complevel=4, index=True)
    recf_eastern.astype(np.float16).to_hdf(
        os.path.join(inputs_case,'recf.h5'), key='data', complevel=4, index=True)
    resources.to_csv(os.path.join(inputs_case,'resources.csv'), index=False)
    ### Write the CSP solar field CF (no SM or storage) for hourly_writetimeseries.py
    (cspcf_eastern[keep].rename(columns=dict(zip(keep, [f'csp_{i}' for i in keep])))
     .astype(np.float32).reset_index(drop=True)
    ).to_hdf(
        os.path.join(inputs_case,'csp.h5'), key='data', complevel=4, index=False)
    ### Overwrite the original hierarchy.csv based on capcredit_hierarchy_level
    hierarchy.rename_axis('*r').to_csv(
        os.path.join(inputs_case, 'hierarchy.csv'), index=True, header=True)
    pd.Series(hierarchy.ccreg.unique()).to_csv(
        os.path.join(inputs_case,'ccreg.csv'), index=False, header=False)


#%% PROCEDURE ###
if __name__ == '__main__':
    # Time the operation of this script
    from ticker import toc, makelog
    import datetime
    tic = datetime.datetime.now()

    ### Mandatory arguments
    parser = argparse.ArgumentParser(description='Create run-specific pickle files for capacity value')
    parser.add_argument('reeds_path', type=str, help='Base directory for all batch runs')
    parser.add_argument('inputs_case', help='path to inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    ### Run it
    print('Starting LDC_prep.py')
    main(reeds_path, inputs_case)

    toc(tic=tic, year=0, process='input_processing/LDC_prep.py',
        path=os.path.join(inputs_case,'..'))
    print('Finished LDC_prep.py')
