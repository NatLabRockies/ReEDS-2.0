'''
This script handles the modifications of static inputs for the first solve year. These inputs
include the 8760 renewable energy capacity factor (RECF) profiles. RECF and resource data for
various technologies are combined into single files for output:

Resources:
        - Creates a resource-to-(i,r,ccreg) lookup table for use in hourly_writesupplycurves.py 
          and Augur
        - Add the distributed PV resources
RECF:
        - Add the distributed PV recf profiles
        - Sort the columns in recf to be in the same order as the rows in resources
        - Scale distributed resource CF profiles by distribution loss factor and tiein loss factor
'''

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import datetime
import numpy as np
import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def csp_dispatch(cfcsp, sm=2.4, storage_duration=10):
    """
    Use a simple no-foresight heuristic to dispatch CSP.
    Excess energy from the solar field (i.e. energy above the max plant power output)
    is sent to storage, and energy in storage is dispatched as soon as possible.

    --- Inputs ---
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


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================
def main(reeds_path, inputs_case):
    print('Starting recf.py')
    
    # #%% Settings for testing
    # reeds_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
    # inputs_case = os.path.join(
    #     reeds_path,'runs','v20250129_cspfixM0_ISONE','inputs_case')

    #%% Inputs from switches
    sw = reeds.io.get_switches(inputs_case)
    GSw_CSP_Types = [int(i) for i in sw.GSw_CSP_Types.split('_')]
    GSw_PVB_Types = sw.GSw_PVB_Types
    GSw_PVB = int(sw.GSw_PVB)


    #%%### Load inputs
    ### Load the input parameters
    scalars = reeds.io.get_scalars(inputs_case)
    ### distloss
    distloss = scalars['distloss']

    ### Load spatial hierarchy
    hierarchy = pd.read_csv(
        os.path.join(inputs_case,'hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    hierarchy_original = (
        pd.read_csv(os.path.join(inputs_case, 'hierarchy_original.csv'))
        .rename(columns={'ba':'r'})
        .set_index('r')
    )
    ### Add ccreg column with the desired hierarchy level
    if sw['capcredit_hierarchy_level'] == 'r':
        hierarchy['ccreg'] = hierarchy.index.copy()
        hierarchy_original['ccreg'] = hierarchy_original.index.copy()
    else:
        hierarchy['ccreg'] = hierarchy[sw.capcredit_hierarchy_level].copy()
        hierarchy_original['ccreg'] = hierarchy_original[sw.capcredit_hierarchy_level].copy()
    ### Map regions to new ccreg's
    r2ccreg = hierarchy['ccreg']

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
                    if not n == len(temp2)-2:
                        temp_tech += '_'
                for c in range(temp_low,temp_high+1):
                    temp_save.append('{}_{}'.format(temp_tech,str(c)))
        for subset in temp_remove:
            techs[tech].remove(subset)
        techs[tech].extend(temp_save)
    vre_dist = techs['VRE_DISTRIBUTED']

    # ------- Read in the static inputs for this run -------

    ### Onshore Wind
    df_windons = reeds.io.read_file(
        os.path.join(inputs_case,'recf_wind-ons.h5'),
        parse_timestamps=True,
    )
    df_windons.columns = ['wind-ons_' + col for col in df_windons]
    ### Don't do aggregation in this case, so make a 1:1 lookup table
    lookup = pd.DataFrame({'ragg':df_windons.columns.values})
    lookup['r'] = lookup.ragg.map(lambda x: x.rsplit('|',1)[1])
    lookup['i'] = lookup.ragg.map(lambda x: x.rsplit('|',1)[0])

    ### Offshore Wind
    df_windofs = reeds.io.read_file(
        os.path.join(inputs_case,'recf_wind-ofs.h5'),
        parse_timestamps=True,
    )
    df_windofs.columns = ['wind-ofs_' + col for col in df_windofs]

    ### UPV
    df_upv = reeds.io.read_file(os.path.join(inputs_case,'recf_upv.h5'), parse_timestamps=True)
    df_upv.columns = ['upv_' + col for col in df_upv]

    # If DistPV is turned off, create an empty dataframe with the same index as df_upv to concat
    if int(sw['GSw_distpv']) == 0: 
        df_distpv = pd.DataFrame(index=df_upv.index)
    else:
        df_distpv = reeds.io.read_file(
            os.path.join(inputs_case, 'recf_distpv.h5'),
            parse_timestamps=True,
        )
        rename = {c: 'distpv|' + c for c in df_distpv if not c.startswith('distpv|')}
        df_distpv = df_distpv.rename(columns=rename)

    ### CSP
    # If CSP is turned off, create an empty dataframe with the same index as df_upv to concat
    if int(sw['GSw_CSP']) == 0:
        cspcf = pd.DataFrame(index=df_upv.index)
    else:
        cspcf = reeds.io.read_file(
            os.path.join(inputs_case, 'recf_csp.h5'),
            parse_timestamps=True,
        )

    ### Format PV+battery profiles
    # Get the PVB types
    pvb_ilr = pd.read_csv(
        os.path.join(inputs_case, 'pvb_ilr.csv'),
        header=0, names=['pvb_type','ilr'], index_col='pvb_type').squeeze(1)
    df_pvb = {}
    # Override GSw_PVB_Types if GSw_PVB is turned off
    GSw_PVB_Types = (
        [int(i) for i in GSw_PVB_Types.split('_')] if int(GSw_PVB)
        else []
    )
    for pvb_type in GSw_PVB_Types:
        ilr = int(pvb_ilr['pvb{}'.format(pvb_type)] * 100)
        # If PVB uses same ILR as UPV then use its profile
        infile = 'recf_upv' if ilr == scalars['ilr_utility'] * 100 else f'recf_upv_{ilr}AC'
        df_pvb[pvb_type] = reeds.io.read_file(
            os.path.join(inputs_case,infile+'.h5'),
            parse_timestamps=True,
        )
        df_pvb[pvb_type].columns = [f'pvb{pvb_type}_{c}'
                                    for c in df_pvb[pvb_type].columns]
        df_pvb[pvb_type].index = df_upv.index.copy()

    ### Concat RECF data
    recf = pd.concat(
        [df_windons, df_windofs, df_upv, df_distpv]
        + [df_pvb[pvb_type] for pvb_type in df_pvb],
        sort=False, axis=1, copy=False)
    
    ### Downselect RECF data to resource adequacy and weather years
    resource_adequacy_years = sw['resource_adequacy_years_list']
    hourly_weather_years = sw['GSw_HourlyWeatherYears'].split('_')
    re_years = [int(year) for year in set(resource_adequacy_years + hourly_weather_years)]
    recf = recf.loc[recf.index.year.isin(re_years)]

    ### Add the other recf techs to the resources lookup table
    toadd = pd.DataFrame({'ragg': [c for c in recf.columns if c not in lookup.ragg.values]})
    toadd['r'] = [c.rsplit('|', 1)[1] for c in toadd.ragg.values]
    toadd['i'] = [c.rsplit('|', 1)[0] for c in toadd.ragg.values]
    resources = (
        pd.concat([lookup, toadd], axis=0, ignore_index=True)
        .rename(columns={'ragg':'resource','r':'area','i':'tech'})
        .sort_values('resource').reset_index(drop=True)
    )

    #%%%#############################################
    #    -- Performing Resource Modifications --    #
    #################################################
    if int(sw['GSw_OfsWind']) == 0:
        wind_ofs_resource = ['wind-ofs_' + str(n) for n in range(1,16)]
        resources = resources[~resources['tech'].isin(wind_ofs_resource)]
    
    # Sorting profiles of resources to match the order of the rows in resources
    resources = resources.sort_values(['resource','area'])
    recf = recf.reindex(labels=resources['resource'].drop_duplicates(), axis=1, copy=False)

    ### Scale up distpv by 1/(1-distloss)
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
            'r': cspcf.columns.map(lambda x: x.split('|')[1]),
            'class': cspcf.columns.map(lambda x: x.split('|')[0]),
        })
        for tech in csptechs
    }, axis=0, names=('tech',)).reset_index(level='tech')

    csp_resources = (
        csp_resources
        .assign(i=csp_resources['tech'] + '_' + csp_resources['class'].astype(str))
        .assign(resource=csp_resources['tech'] + '_' + csp_resources['resource'])
        .assign(ccreg=csp_resources.r.map(r2ccreg))
        [['i','r','resource','ccreg']]
    )    
    ###### Simulate CSP dispatch for each design
    ### Get solar multiples
    sms = {tech: scalars[f'csp_sm_{tech.strip("csp")}'] for tech in csptechs}
    ### Get storage durations
    storage_duration = pd.read_csv(
        os.path.join(inputs_case,'storage_duration.csv'), header=None, index_col=0).squeeze(1)
    ## All CSP resource classes have the same duration for a given tech, so just take the first one
    durations = {tech: storage_duration[f'csp{tech.strip("csp")}_1'] for tech in csptechs}
    ### Run the dispatch simulation for modeled regions

    csp_system_cf = pd.concat({
        tech: csp_dispatch(cspcf, sm=sms[tech], storage_duration=durations[tech])
        for tech in csptechs
    }, axis=1)
    ## Collapse multiindex column labels to single strings
    csp_system_cf.columns = ['_'.join(c) for c in csp_system_cf.columns]

    ### Add CSP to RE output dataframes
    csp_system_cf = csp_system_cf.loc[recf.index]
    recf = pd.concat([recf, csp_system_cf], axis=1)
    resources = pd.concat([resources, csp_resources], axis=0)

    #%%###########################
    #    -- Data Write-Out --    #
    ##############################

    reeds.io.write_profile_to_h5(recf.astype(np.float16), 'recf.h5', inputs_case)
    resources.to_csv(os.path.join(inputs_case,'resources.csv'), index=False)
    ### Write the CSP solar field CF (no SM or storage) for hourly_writetimeseries.py
    cspcf = cspcf.rename(columns=dict(zip(cspcf.columns, [f'csp_{i}' for i in cspcf.columns])))
    reeds.io.write_profile_to_h5(cspcf.astype(np.float32), 'csp.h5', inputs_case)
    ### Overwrite the original hierarchy.csv based on capcredit_hierarchy_level
    hierarchy.rename_axis('*r').to_csv(
        os.path.join(inputs_case, 'hierarchy.csv'), index=True, header=True)
    pd.Series(hierarchy.ccreg.unique()).to_csv(
        os.path.join(inputs_case,'ccreg.csv'), index=False, header=False)


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == '__main__':
    # Time the operation of this script
    tic = datetime.datetime.now()

    ### Parse arguments
    parser = argparse.ArgumentParser(
        description='Create run-specific hourly profiles',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('reeds_path', help='ReEDS-2.0 directory')
    parser.add_argument('inputs_case', help='ReEDS-2.0/runs/{case}/inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    #%% Run it
    main(reeds_path=reeds_path, inputs_case=inputs_case)

    reeds.log.toc(tic=tic, year=0, process='input_processing/recf.py',
        path=os.path.join(inputs_case,'..'))
    
    print('Finished recf.py')
