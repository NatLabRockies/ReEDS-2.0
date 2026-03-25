# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 10:45:39 2022

@author: wcole
"""
#%% Imports
import os
import numpy as np
import pandas as pd
import argparse
import shutil

# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()


#%% Argument Inputs

parser = argparse.ArgumentParser(description="Copy files needed for this run")
parser.add_argument('reeds_path', help='ReEDS directory')
parser.add_argument('inputs_case', help='output directory')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing ###
# reeds_path = os.getcwd()
# reeds_path = os.path.expanduser('~/github2/ReEDS-2.0/')
# inputs_case = os.path.join(reeds_path,'runs','v20230224_prmM0_WECC','inputs_case')

#%% Additional inputs
casedir = os.path.dirname(inputs_case)
NARIS = False
decimals = 6

#%% Functions

def scalar_csv_to_txt(path_to_scalar_csv):
    """
    Write a scalar csv to GAMS-readable text
    Format of csv should be: scalar,value,comment
    """
    ### Load the csv
    dfscalar = pd.read_csv(
        path_to_scalar_csv,
        header=None, names=['scalar','value','comment'], index_col='scalar').fillna(' ')
    ### Create the GAMS-readable string (comments can only be 255 characters long)
    scalartext = '\n'.join([
        'scalar {:<30} "{:<5.255}" /{}/ ;'.format(
            i, row['comment'], row['value'])
        for i, row in dfscalar.iterrows()
    ])
    ### Write it to a file, replacing .csv with .txt in the filename
    with open(path_to_scalar_csv.replace('.csv','.txt'), 'w') as w:
        w.write(scalartext)

    return dfscalar


def param_csv_to_txt(path_to_param_csv, writelist=True):
    """
    Write a parameter csv to GAMS-readable text
    Format of csv should be: parameter(indices),units,comment
    """
    ### Load the csv
    dfparams = pd.read_csv(
        path_to_param_csv,
        index_col='param', comment='#',
    )
    ### Create the GAMS-readable param definition string (comments must be ≤255 characters)
    paramtext = '\n'.join([
        f'parameter {i:<50} "--{row.units}-- {row.comment:.255}" ;'
        ## Don't define parameters with an input flag because they already exist
        for i, row in dfparams.loc[dfparams.input != 1].iterrows()
    ])
    ### Write it to a file, replacing .csv with .gms in the filename
    param_gms_path = path_to_param_csv.replace('.csv','.gms')
    with open(param_gms_path, 'w') as w:
        w.write(paramtext)
    ### Write the list of parameters if desired
    if writelist:
        ### Create the GAMS-readable list of parameters (without indices)
        paramlist = '\n'.join(dfparams.index.map(lambda x: x.split('(')[0]).tolist())
        param_list_path = (
            path_to_param_csv.replace('params','paramlist').replace('.csv','.txt'))
        with open(param_list_path, 'w') as w:
            w.write(paramlist)

    return dfparams


#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))
print('Starting copy_files.py')

#%% Identify files that have a region index versus those that do not

runfiles = (
    pd.read_csv(
        os.path.join(reeds_path, 'runfiles.csv'),
        dtype={'fix_cols':str}
    ).fillna({'fix_cols':''})
    .rename(columns={'filepath (for input files only)':'filepath',
                     'post_copy (files are created after copy_files)':'post_copy'})
    [['filename','filepath','filetype','region_col','fix_cols','post_copy']]
    )

# Non-region files that need copied either do not have an entry in region_col
# or have 'ignore' as the entry.  They also have a filepath specified.
nonregionFiles = (
    runfiles[
        ((runfiles['region_col'].isna()) | (runfiles['region_col'] == 'ignore'))
        & (~runfiles['filepath'].isna())]
    )

# Region files are those that have a region and do not specify 'ignore'
# Also ignore files that are created after this script runs (i.e., post_copy = 1)
regionFiles = (
    runfiles[
        (~runfiles['region_col'].isna())
        & (runfiles['region_col'] != 'ignore')
        & (runfiles['post_copy'] != 1)]
    )


#%% Copy relevant files from runfiles.csv that do not include regions

for filepath in nonregionFiles['filepath']:
    if filepath.split('/')[0] in ['inputs', 'postprocessing']:
        dir_dst = inputs_case
    else:
        dir_dst = casedir
    src_file = os.path.join(reeds_path, filepath)
    if os.path.exists(src_file):
        shutil.copy(src_file, dir_dst)
            
#%% Rewrite the scalar and switches tables as GAMS-readable definitions
scalar_csv_to_txt(os.path.join(inputs_case,'scalars.csv'))
scalar_csv_to_txt(os.path.join(inputs_case,'gswitches.csv'))
### Do the same for the e_report parameters
param_csv_to_txt(os.path.join(inputs_case,'..','e_report_params.csv'))

#%% Read inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

solveyears = pd.read_csv(
    os.path.join(reeds_path,'inputs','modeledyears.csv'),
    usecols=[sw['yearset_suffix']], squeeze=True,
).dropna().astype(int).tolist()
solveyears = [y for y in solveyears if y <= int(sw['endyear'])]


#%% Ingest regions

### Load the full regions list
hierarchy = pd.read_csv(
    os.path.join(reeds_path, 'inputs', 'hierarchy{}.csv'.format(
        '' if (sw['GSw_HierarchyFile'] == 'default')
        else '_'+sw['GSw_HierarchyFile']))
).rename(columns={'*r':'r'})
if not NARIS:
    hierarchy = hierarchy.loc[hierarchy.country.str.lower()=='usa'].copy()

#%% Parse the GSw_Region switch. If it includes a '/' character, it has the format
### {column of hierarchy.csv}/{comma-delimited entries to keep from that column}.
if '/' in sw['GSw_Region']:
    GSw_RegionLevel, GSw_Region = [c.lower() for c in sw['GSw_Region'].split('/')]
    val_r_in = hierarchy.loc[
        hierarchy[GSw_RegionLevel].str.lower().isin(GSw_Region.split(',')), 'r'].tolist()
### If it does not include a '/', then it indicates a column in modeled_regions.csv.
else:
    modeled_regions = pd.read_csv(
        os.path.join(reeds_path,'inputs','userinput','modeled_regions.csv'))
    modeled_regions.columns = modeled_regions.columns.str.lower()
    val_r_in = list(
        modeled_regions[~modeled_regions[sw['GSw_Region'].lower()].isna()]['r'].unique())

#%% subset the hierarchy file to just the rows with valid r regions
hier_sub = hierarchy[hierarchy['r'].isin(val_r_in)]

# populate val_st as unique states (not st_in) from the subsetted hierarchy table
# also include "voluntary" state for modeling voluntary market REC trading
val_st = list(hier_sub['st'].unique()) + ['voluntary']

# write out the unique values of each column in hier_sub to val_[column name].csv
# note the conversion to a pd Series is necessary to leverage the to_csv function
for i in hier_sub.columns:
    pd.Series(hier_sub[i].unique()).to_csv(
        os.path.join(inputs_case,'val_' + i + '.csv'),index=False,header=False)
    
# overwrite val_st with the val_st used here (which includes 'voluntary')
pd.Series(val_st).to_csv(
    os.path.join(inputs_case, 'val_st.csv'), header=False, index=False)

#rename columns and save as hierarchy.csv
hier_sub.rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case, 'hierarchy.csv'), index=False)

levels = list(hier_sub.columns)
valid_regions = {level: list(hier_sub[level].unique()) for level in levels}

#extract subsets for use in subsetting operations
val_cendiv = valid_regions['cendiv']
val_r = valid_regions['r']

# Export region files
pd.Series(val_r).to_csv(
    os.path.join(inputs_case, 'val_r.csv'), header=False, index=False)

# Create list of CS regions that are included in modeled regions
r_cs = pd.read_csv(os.path.join(reeds_path, 'inputs', 'ctus', 'r_cs.csv'))
r_cs = r_cs[r_cs['*r'].isin(val_r)]

#export valid cs files to val_cs.csv
val_cs = pd.Series(r_cs['cs'].unique())
val_cs.to_csv(os.path.join(inputs_case, 'val_cs.csv'), header=False, index=False)
#export filtered r_cs to r_cs.csv
r_cs.to_csv(os.path.join(inputs_case, 'r_cs.csv'), index=False)

            
#%% Write run-specific files
shutil.copy(os.path.join(reeds_path,'inputs','capacitydata',
                            f'wind-ons_prescribed_builds_{sw.GSw_SitingWindOns}.csv'),
            os.path.join(inputs_case,'wind-ons_prescribed_builds.csv'))
shutil.copy(os.path.join(reeds_path,'inputs','capacitydata',
                            f'wind-ofs_prescribed_builds_{sw.GSw_SitingWindOfs}.csv'),
            os.path.join(inputs_case,'wind-ofs_prescribed_builds.csv'))

### Specific versions of files
osprey_num_years = len(sw['osprey_years'].split('_'))
shutil.copy(
    os.path.join(
        reeds_path, 'inputs', 'variability', 'index_hr_map_{}.csv'.format(osprey_num_years)),
    os.path.join(inputs_case, 'index_hr_map.csv')
)
shutil.copy(
    os.path.join(
        reeds_path, 'inputs', 'variability', 'd_szn_{}.csv'.format(osprey_num_years)),
    os.path.join(inputs_case, 'd_szn.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','state_policies','offshore_req_{}.csv'.format(sw['GSw_OfsWindForceScen'])),
    os.path.join(inputs_case,'offshore_req.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','consume',f"dac_gas_{sw['GSw_DAC_Gas_Case']}.csv"),
    os.path.join(inputs_case,'dac_gas.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','carbonconstraints',f"capture_rates_{sw['GSw_CCS_Rate']}.csv"),
    os.path.join(inputs_case,'capture_rates.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','capacitydata',
        f"ReEDS_generator_database_final_{sw['unitdata']}.csv"),
    os.path.join(inputs_case,'unitdata.csv')
)
for f in ['distPVcap','distPVCF_hourly']:
    shutil.copy(
        os.path.join(
            reeds_path,'inputs','dGen_Model_Inputs','{s}','{f}_{s}.csv').format(
                f=f, s=sw['distpvscen']),
        os.path.join(inputs_case, f'{f}.csv')
    )
pd.read_csv(
    os.path.join(reeds_path,'inputs','loaddata',f"demand_{sw['demandscen']}.csv"),
).round(6).to_csv(os.path.join(inputs_case,'load_multiplier.csv'),index=False)

### Files defined from case inputs
pd.DataFrame(
    {'*pvb_type': ['pvb{}'.format(i) for i in range(1,4)],
     'ilr': [np.around(float(c) / 100, 2) for c in sw['GSw_PVB_ILR'].split('_')]}
).to_csv(os.path.join(inputs_case, 'pvb_ilr.csv'), index=False)

pd.DataFrame(
    {'*pvb_type': ['pvb{}'.format(i) for i in range(1,4)],
     'bir': [np.around(float(c) / 100, 2) for c in sw['GSw_PVB_BIR'].split('_')]}
).to_csv(os.path.join(inputs_case, 'pvb_bir.csv'), index=False)

### Constant value if input is float, otherwise named profile
try:
    rate = float(sw['GSw_MethaneLeakageScen'])
    pd.Series(index=range(2010,2051), data=rate, name='constant').rename_axis('*t').round(5).to_csv(
        os.path.join(inputs_case,'methane_leakage_rate.csv'))
except ValueError:
    pd.read_csv(
        os.path.join(reeds_path,'inputs','carbonconstraints','methane_leakage_rate.csv'),
        index_col='t',
    )[sw['GSw_MethaneLeakageScen']].rename_axis('*t').round(5).to_csv(
        os.path.join(inputs_case,'methane_leakage_rate.csv'))


### Single column from input table
pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','ng_crf_penalty.csv'), index_col='t',
)[sw['GSw_NG_CRF_penalty']].rename_axis('*t').to_csv(
    os.path.join(inputs_case,'ng_crf_penalty.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','co2_cap.csv'), index_col='t',
).loc[sw['GSw_AnnualCapScen']].rename_axis('*t').to_csv(
    os.path.join(inputs_case,'co2_cap.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','co2_tax.csv'), index_col='t',
)[sw['GSw_CarbTaxOption']].rename_axis('*t').round(2).to_csv(
    os.path.join(inputs_case,'co2_tax.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','reserves','prm_annual.csv'), index_col=['*nercr','t'],
)[sw['GSw_PRM_scenario']].round(5).to_csv(
    os.path.join(inputs_case,'prm_annual.csv')
)
pd.DataFrame(columns=solveyears).to_csv(
    os.path.join(inputs_case,'modeledyears.csv'), index=False)
pd.read_csv(
    os.path.join(reeds_path,'inputs','national_generation','gen_mandate_trajectory.csv'),
    index_col='GSw_GenMandateScen'
).loc[sw['GSw_GenMandateScen']].rename_axis('*t').round(5).to_csv(
    os.path.join(inputs_case,'gen_mandate_trajectory.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','national_generation','gen_mandate_tech_list.csv'),
    index_col='*i',
)[sw['GSw_GenMandateList']].to_csv(
    os.path.join(inputs_case,'gen_mandate_tech_list.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','climate','climate_heuristics_yearfrac.csv'),
    index_col='*t',
)[sw['GSw_ClimateHeuristics']].round(3).to_csv(
    os.path.join(inputs_case,'climate_heuristics_yearfrac.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','climate','climate_heuristics_finalyear.csv'),
    index_col='*parameter',
)[sw['GSw_ClimateHeuristics']].round(3).to_csv(
    os.path.join(inputs_case,'climate_heuristics_finalyear.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','capacitydata','upgrade_costs_ccs_coal.csv'),
    index_col='t',
)[sw['ccs_upgrade_cost_case']].round(3).rename_axis('*t').to_csv(
    os.path.join(inputs_case,'upgrade_costs_ccs_coal.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','capacitydata','upgrade_costs_ccs_gas.csv'),
    index_col='t',
)[sw['ccs_upgrade_cost_case']].round(3).rename_axis('*t').to_csv(
    os.path.join(inputs_case,'upgrade_costs_ccs_gas.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','consume','h2_exogenous_demand.csv'),
    index_col=['p','t']
)[sw['GSw_H2_Demand_Case']].round(3).rename_axis(['*p','t']).to_csv(
    os.path.join(inputs_case,'h2_exogenous_demand.csv')
)

#%% Filter and copy data for files with regions

for i, row in regionFiles.iterrows():
    filepath = row['filepath']
    filename = row['filename']
    filetype = row['filetype']
    region_col = row['region_col']
    fix_cols = row['fix_cols'].split(',')

    # If a filename isn't specified, that means it is already in the
    # inputs_case folder, otherwise use the filepath
    if filepath != filepath:
        full_path = os.path.join(inputs_case,filename)
    else:
        full_path = os.path.join(reeds_path,filepath)

    # Read if file that needs filtered
    if filetype == '.h5':
        df = pd.read_hdf(full_path)
    elif filetype == '.csv':
        df = pd.read_csv(full_path)
    else:
        raise('filetype for {} is not .csv or .h5'.format(full_path))

    # Filter data to valid regions
    if region_col == 'wide':
        # Check to see if the regions are listed in the columns. If they are,
        # then use those columns
        if df.columns.isin(val_r).any():
            df = df.loc[:,df.columns.isin(fix_cols + val_r)]
        # Otherwise just use a empty dataframe
        else:
            df = pd.DataFrame()

    # if there is a region to region mapping set
    elif region_col.strip('*') in ['r,rr']:
        # make sure both the r and rr regions are in val_r
        r,rr = region_col.split(',')
        df = df.loc[df[r].isin(val_r) & df[rr].isin(val_r)]

    #subset on the valid regions except for r regions
    #(r regions might also include s regions, which complicates things...)
    elif ((region_col.strip('*') in levels) & (region_col.strip('*') != 'r')):
        df = df.loc[df[region_col].isin(valid_regions[region_col.strip('*')])]
        
    elif (region_col == 'cs' or region_col == '*cs'):
        # subset to just cs regions
        df = df.loc[df[region_col].isin(val_cs)]

    #subset both column of 'st' and columns of state if st_st
    elif (region_col.strip('*') == 'st_st'):
        # make sure both the state regions are in val_st
        df = df.loc[df['st'].isin(val_st)]
        df = df.loc[:,df.columns.isin(fix_cols + val_st)]

    elif (region_col.strip('*') == 'r_cendiv'):
        # make sure both the r is in val_r and cendiv is in val_cendiv
        df = df.loc[df['r'].isin(val_r)]
        df = df.loc[:,df.columns.isin(["r"] + val_cendiv)]

    #subset on val_st if region_col == st
    elif region_col == 'wide_st':
        # Check to see if the states are listed in the columns. If they are,
        # then use those columns
        if df.columns.isin(val_st).any():
            df = df.loc[:,df.columns.isin(fix_cols + val_st)]
        # Otherwise just use a empty dataframe
        else:
            df = pd.DataFrame()

    # if region_col is not wide, st, or aliased..
    else:
        df = df.loc[df[region_col].isin(val_r)]
    
    # Write data to inputs_case folder
    if filetype == '.h5':
        df.to_hdf(
            os.path.join(inputs_case,filename), key='data', complevel=4, format='table')
    else:
        df.to_csv(
            os.path.join(inputs_case,filename), index=False)


### All files from the user input folder
userinputs = os.listdir(os.path.join(reeds_path,"inputs","userinput"))

for file_name in userinputs:
    full_file_name = os.path.join(reeds_path,"inputs","userinput", file_name)
    # ivt is now a special case written in calc_financial_inputs, so skip it here
    if (os.path.isfile(full_file_name) and (file_name != 'ivt.csv')):
        shutil.copy(full_file_name, inputs_case)

### Legacy files - no longer used
if sw['unitdata'] == 'ABB':
    nas = '//nrelnas01/ReEDS/FY18-ReEDS-2.0/data/'
    out = os.path.join(reeds_path,'inputs','capacitydata')
    shutil.copy(os.path.join(nas,'ExistingUnits_ABB.gdx'), out)
    shutil.copy(os.path.join(nas,'PrescriptiveBuilds_ABB.gdx'), out)
    shutil.copy(os.path.join(nas,'PrescriptiveRetirements_ABB.gdx'), out)
    shutil.copy(os.path.join(nas,'ReEDS_generator_database_final_ABB.gdx'), out)

### Make opt file change for value streams
if sw['GSw_ValStr'] != '0':
    if int(sw['GSw_gopt']) == 1:
        origOptExt = 'opt'
    elif int(sw['GSw_gopt']) < 10:
        origOptExt = 'op' + sw['GSw_gopt']
    else:
        origOptExt = 'o' + sw['GSw_gopt']
    #Add writemps statement to opt file
    with open(casedir + '/cplex.'+origOptExt, 'a') as file:
        file.write('\nwritemps ReEDSmodel.mps')

toc(tic=tic, year=0, process='input_processing/copy_files.py',
    path=os.path.join(inputs_case,'..'))

print('Finished copy_files.py')
