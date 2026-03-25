"""
prbrown 20220421
Notes to user:
--------------
* This script loops over files in runs/{}/inputs_case/ and aggregates them
  based on the directions given in runfiles.csv.
    * If new files have been added to inputs_case, you'll need to add rows with 
      processing directions to runfiles.csv. 
    * The column names should be self-explanatory; most likely there's also at least
      one similarly-formatted file in inputs_case that you can copy the settings for.
* Some files are aggregated in other scripts:
    * WriteHintage.py (these files are handled upstream since
      aggregation affects the clustering of generators into (b/h/v)intages):
        * hintage_data.csv 
TODO
* Decide whether to fix VRE supply curves. (Currently we're grouping over the old
  bins but would be better to create new bins at the aggregated resolution.)
"""

#%%########
### IMPORTS
import gdxpds
import pandas as pd
import numpy as np
import os, sys, csv, pickle, shutil
import argparse
from glob import glob
from warnings import warn
## Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%%#################
### FIXED INPUTS ###
decimals = 6
### anchortype: 'load' sets rb with largest 2010 load as anchor reg;
### 'size' sets largest rb as anchor reg
anchortype = 'size'

#%%###############################
### Functions and dictionaries ###
the_unnamer = {'Unnamed: {}'.format(i): '' for i in range(1000)}

aggfuncmap = {
    'mode': pd.Series.mode,
}

def logprint(filepath, message):
    print('{:-<45}> {}'.format(filepath+' ', message))


#%%####################
### ARGUMENT INPUTS ###
parser = argparse.ArgumentParser(description='Extend inputs to arbitrary future year')
parser.add_argument('reeds_path', help='path to ReEDS directory')
parser.add_argument('inputs_case', help='path to inputs_case directory')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = os.path.join(args.inputs_case)

# #%%#########################
# ### Settings for testing ###
# reeds_path = os.path.expanduser('~/github2/ReEDS-2.0')
# inputs_case = os.path.join(
#     reeds_path,'runs','v20230411_prasM0_ERCOT_agg1','inputs_case')

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
endyear = int(sw.endyear)
###### Inputs related to debugging
### Set debug == True to copy the original files to a new folder (inputs_case_original).
### If debug == False, the original files are overwritten.
debug = True
### missing: 'raise' or 'warn'
missing = 'raise'
### verbose: 0, 1, 2
verbose = 2

#%%###################
### Derived inputs ###

#%% Get the case name (ReEDS-2.0/runs/{casename}/inputscase/)
casename = inputs_case.split(os.sep)[-3]

#%% DEBUG: Copy the original inputs_case files
if debug and int(sw['GSw_AggregateRegions']):
    import distutils.dir_util
    os.makedirs(inputs_case+'_original', exist_ok=True)
    distutils.dir_util.copy_tree(inputs_case, inputs_case+'_original')

#%% Get the region hierarchy
hierarchy = pd.read_csv(
    os.path.join(inputs_case,'hierarchy.csv')
).rename(columns={'*r':'r'}).set_index('r')
r2aggreg = hierarchy.aggreg.copy()

#%% Write the full set of regions
pd.Series(hierarchy.index.values).to_csv(
    os.path.join(inputs_case, 'rb.csv'), index=False, header=False)
pd.Series(hierarchy.aggreg.unique()).to_csv(
    os.path.join(inputs_case, 'aggreg.csv'), index=False, header=False)

pd.Series(hierarchy.index.values).to_csv(
    os.path.join(inputs_case, 'r.csv'), index=False, header=False)

#%%##############################################
### If using default 134 regions, exit the script
if not int(sw['GSw_AggregateRegions']):
    print('GSw_AggregationRegions = 0, so skip aggregate_regions.py')
    quit()
else:
    print('Starting aggregate_regions.py', flush=True)

#%%### Get the "anchor" zone for each aggregation region
### For transmission we want to use the old endpoints to avoid requiring a new run of the
### reV least-cost-paths procedure.
if anchortype in ['load','demand','MW','MWh']:
    ### Take the "anchor" zone as the zone with the largest annual demand in 2010.
    ## Get annual average load
    load = pd.read_csv(
        os.path.join(reeds_path, 'inputs', 'variability', 'multi_year', 'load.csv.gz'),
        index_col=0,
    ).mean().rename_axis('r').rename('MW').to_frame()
    ## Add column for new regions
    load['aggreg'] = load.index.map(r2aggreg)
    ## Take the original zone with largest demand
    aggreg2anchorreg = load.groupby('aggreg').idxmax()['MW'].rename('rb')
elif anchortype in ['size','km2','area']:
    ### Take the "anchor" zone as the zone with the largest area [km2]
    import geopandas as gpd
    dfba = gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','US_PCA')).set_index('rb')
    dfba['km2'] = dfba.area / 1e6
    ## Add column for new regions
    dfba['aggreg'] = dfba.index.map(r2aggreg)
    ## Take the original zone with largest area
    aggreg2anchorreg = dfba.groupby('aggreg').km2.idxmax().rename('rb')
else:
    raise ValueError(f'Invalid choice of anchortype: {anchortype}')

anchorreg2aggreg = pd.Series(index=aggreg2anchorreg.values, data=aggreg2anchorreg.index)
## Save it for plotting
aggreg2anchorreg.to_csv(os.path.join(inputs_case, 'aggreg2anchorreg.csv'))

#%%### Get RSC VRE available capacity to use in capacity-weighted averages
### We need the original un-aggregated supply curves, so run writesupplycurves again
# rscweight = pd.read_csv(os.path.join(inputs_case, 'rsc_combined.csv'))
import writesupplycurves
rscweight = writesupplycurves.main(
    reeds_path, inputs_case, GSw_AggregateRegions=0, write=False)
rscweight = (
    rscweight.loc[(rscweight.sc_cat=='cap')]
    .rename(columns={'*i':'i'})
    .drop_duplicates(subset=['i','r','rscbin'])
    [['i','r','rscbin','value']].rename(columns={'value':'MW'})
).copy()

#%% Get distpv capacity to use in capacity-weighted averages
distpvcap = pd.read_csv(
    os.path.join(inputs_case, 'distPVcap.csv'), index_col=0
### TODO: Need a single year so arbitrarily use 2036
)['2036'].rename_axis('r').rename('MW')
## Add it to rscweight_nobin
rscweight_nobin = rscweight.groupby(['i','r'], as_index=False).sum()
rscweight_nobin = pd.concat([rscweight_nobin, distpvcap.reset_index().assign(i='distpv')], axis=0)

#%% Get the mapping to reduced-resolution technology classes
original_num_classes = {**{'dupv':7}, **{f'csp{i}':12 for i in range(1,5)}}
new_classes = {}
for tech in ['dupv'] + [f'csp{i}' for i in range(1,5)]:
    GSw_NumClasses = int(sw['GSw_Num{}classes'.format(tech.upper().strip('1234'))])
    ## Spread the new classes roughly evenly out over the old classes
    num_in_step = original_num_classes[tech] // GSw_NumClasses
    remainder = original_num_classes[tech] % GSw_NumClasses
    new_classes[tech] = sorted(
        list(np.ravel([[i]*num_in_step for i in range(1,GSw_NumClasses+1)]))
        + list(range(1,remainder+1))
    )
    new_classes[tech] = dict(zip(
        [f'{tech}_{i}' for i in range(1,original_num_classes[tech]+1)],
        [f'{tech}_{i}' for i in new_classes[tech]]
    ))
### Combine all the new classes into one dictionary
new_classes = {k:v for d in new_classes for k,v in new_classes[d].items()}

#%% Get the settings file
aggfiles = (
    pd.read_csv(
        os.path.join(reeds_path, 'runfiles.csv'),
        dtype={'fix_cols':str}, index_col='filename',
    ).fillna({'fix_cols':''})
    .rename(columns={'ignore when aggregating':'ignore',
                     'wide (1 if any parameters are in wide format)':'wide',
                     'header (0 if file has column labels)':'header'})
    )
#%% If any files are missing, stop and alert the user
inputfiles = sorted([
    f.split('inputs_case'+os.sep)[1]
    for f in glob(os.path.join(inputs_case,'**'), recursive=True)
    if 'metadata' not in f
])
## Drop the directories and backup h17 files
inputfiles = [f for f in inputfiles if (('.' in f) and not f.endswith('_h17.csv'))]
missingfiles = [
    f for f in inputfiles if (os.path.basename(f) not in aggfiles.index.values)
]
if any(missingfiles):
    if missing == 'raise':
        raise Exception(
            'Missing aggregation method for:\n{}\n'
            '>>> Need to add entries for these files to runfiles.csv'
            .format('\n'.join(missingfiles))
        )
    else:
        from warnings import warn
        warn(
            'Missing aggregation directions for:\n{}\n'
            '>>> For this run, these files are copied without modification'
            .format('\n'.join(missingfiles))
        )
        for f in missingfiles:
            shutil.copy(os.path.join(inputs_case, f), os.path.join(inputs_case, f))
            print(f'copied {f}, which is missing from runfiles.csv')

#%% Loop it
for filepath in inputfiles:
    ### For debugging: Specify a file
    # filepath = 'stress2010/peak_szn.csv'
    ### Get the appropriate row from aggfiles
    row = aggfiles.loc[os.path.basename(filepath)]
    #%% continue loop
    filetic = datetime.datetime.now()
    filename = row.name
    if row['ignore'] == 0:
        pass
    ### if ignore == 1, just copy the file to inputs_case and skip the rest
    elif int(row['ignore']):
        if verbose > 1:
            logprint(filepath, 'ignored')
        continue

    #%% If the file isn't in inputs_case, skip it
    if filename not in inputfiles:
        if verbose > 1:
            logprint(filepath, 'skipped since not in inputs_case')
        continue

    #%% Settings
    ### header: 0 if file has column labels, otherwise 'None'
    header = (None if row['header'] in ['None','none','',None,np.nan]
              else 'keepindex' if row['header'] == 'keepindex'
              else int(row['header']))
    ### region_col: usually 'r', 'rb', or 'region', or 'wide' if file uses regions as columns
    region_col = row['region_col']
    # Some datasets have both rb regions and cendiv regions.  Only use the r
    # regions for these datasets
    if region_col == 'r_cendiv':
        region_col = 'r'
    region_cols = region_col.split(',')
    ### aggfunc: usually 'sum' or 'mean', with special cases defined above
    aggfunc = aggfuncmap.get(row['aggfunc'], row['aggfunc'])
    ### wide: 1 if any parameters are in wide format, otherwise 0
    wide = int(row['wide'])
    filetype = row['filetype']
    ### key: only used for gdx files, indicating the parameter name. 
    ### gdx files need a separate line in runfiles.csv for each parameter.
    key = row['key']
    ### fix_cols: indicate columns to use as for fields that should be projected
    ### independently to future years (e.g. r, szn, tech)
    fix_cols = row['fix_cols']
    fix_cols = (list() if fix_cols in ['None','none','',None,np.nan] else fix_cols.split(','))
    ### i_col: indicate technology column. Only used/needed if aggregating techs.
    i_col = row['i_col']
    i_col = None if i_col in ['None','none','',None,np.nan] else i_col


    #%%### Load it
    if filetype in ['.csv', '.csv.gz']:
        # Some csv files are empty and therefore cannot be opened.  If that is
        # the case, then skip them.
        try:
            dfin = pd.read_csv(os.path.join(inputs_case, filepath), header=header)
        except:
            continue
    elif filetype == '.h5':
        dfin = pd.read_hdf(os.path.join(inputs_case, filepath))
        if header == 'keepindex':
            indexnames = list(dfin.index.names)
            if (len(indexnames) == 1) and (not indexnames[0]):
                indexnames = ['index']
            dfin.reset_index(inplace=True)
    elif filetype == '.gdx':
        ### Read in the full gdx file, but only change the 'key' parameter
        ### given in aggfiles. That's wasteful, but there are currently no
        ### active gdx files.
        dfall = gdxpds.to_dataframes(os.path.join(inputs_case, filepath))
        dfin = dfall[key]
    else:
        raise Exception('Unsupported filetype: {}'.format(filepath))

    dfin.rename(columns={c:str(c) for c in dfin.columns}, inplace=True)
    columns = dfin.columns.tolist()
    ### Stop now if it's empty
    if dfin.empty:
        if verbose > 1:
            logprint(filepath, 'empty')
        continue


    #%%### Reshape to long format
    if (aggfunc == 'sc_cat') and (not wide):
        ### Supply-curve format. Expect an sc_cat column with 'cap' and 'cost' values.
        ## 'cap' values are summed; 'cost' values use the 'cap'-weighted mean
        df = dfin.pivot(index=fix_cols+region_cols,columns='sc_cat',values=key).reset_index()
    elif (aggfunc == 'sc_cat') and wide and (len(fix_cols) == 1):
        ### Supply-curve format. Expect an sc_cat column with 'cap' and 'cost' values.
        ## Some value other than rb is in wide format
        ## So turn rb and the wide value into the index
        df = dfin.set_index(region_cols+['sc_cat']).stack().rename('value')
        df.index = df.index.rename(region_cols+['sc_cat','wide'])
        ## Make value columns for 'cap' and 'cost'
        df = df.unstack('sc_cat').reset_index()
    elif not wide:
        ### File is already long so don't do anything
        df = dfin.copy()
    elif wide and (region_col != 'wide') and (len(fix_cols) == 1) and (fix_cols[0] == 'wide'):
        ## Some value other than rb is in wide format
        ## So turn rb and the wide value into the index
        df = dfin.set_index(region_col).stack().rename('value')
        df.index = df.index.rename([region_col, 'wide'])
        ## Turn index into columns
        df = df.reset_index()
    elif wide and (region_col != 'wide') and (len(fix_cols) > 1) and ('wide' in fix_cols):
        ## Some value other than rb is in wide format
        ## So turn rb, other fix_cols, and the wide value into the index
        df = dfin.set_index([region_col]+[c for c in fix_cols if c != 'wide']).stack().rename('value')
        df.index = df.index.rename([region_col]+fix_cols)
        ## Turn index into columns
        df = df.reset_index()
    elif wide and (region_col == 'wide') and len(fix_cols):
        ### File has some fixed columns and then regions in wide format
        df = (
            ## Turn all identifying columns into indices, with rb as the last index
            dfin.set_index(fix_cols).stack()
            ## Name the rb column 'wide'
            .rename_axis(fix_cols+['wide']).rename('value')
            ## Turn index into columns
            .reset_index()
        )
        
    # If the file is empty, move on to the next one as there is nothing to aggregate
    if df.empty:
        if verbose > 1:
            logprint(filepath, 'empty')
        continue


    #%%### Aggregate by region
    df1 = df.copy()
    ### Map old regions to new regions
    if aggfunc not in ['trans_lookup','mean_cap','recf']:
        for c in region_cols:
            df1[c] = df1[c].map(lambda x: r2aggreg.get(x,x))
        if i_col:
            df1[i_col] = df1[i_col].map(lambda x: new_classes.get(x,x))

    ### Group according to aggfunc
    if aggfunc == 'sc_cat':
        ## Weight cost by cap
        df1['cap_times_cost'] = df1['cap'] * df1['cost']
        ## Sum everything
        df1 = df1.groupby(fix_cols+[region_col]).sum()
        ## Divide cost*cap by cap
        df1['cost'] = df1['cap_times_cost'] / df1['cap']
        df1.drop(['cap_times_cost'], axis=1, inplace=True)
    elif aggfunc == 'trans_lookup':
        ## Get data for anchor zones
        for c in region_cols:
            df1 = df1.loc[df1[c].isin(aggreg2anchorreg)].copy()
        ## Map to aggregated regions
        for c in region_cols:
            df1[c] = df1[c].map(anchorreg2aggreg)
    elif aggfunc == 'mean_cap':
        df1 = (
            df1.rename(columns={'value':columns[-1]})
            .merge(
                (rscweight_nobin.rename(columns={'i':'*i'}) if '*i' in fix_cols
                else rscweight_nobin),
                on=['r',('*i' if '*i' in fix_cols else 'i')], how='left')
            ## There are some nan's because we subtract existing capacity from the supply curve.
            ## Fill them with 1 MW for now, but it would be better to change that procedure.
            ## Note also that the weighting will be off
            .fillna(1)
        )
        ### Similar procedure as above for aggfunc == 'sc_cat'
        if i_col:
            df1[i_col] = df1[i_col].map(lambda x: new_classes.get(x,x))
        df1 = (
            df1
            .assign(r=df1.r.map(r2aggreg))
            .assign(cap_times_cf=df1.cf*df1.MW)
            .groupby(fix_cols+region_cols).sum()
        )
        df1.cf = df1.cap_times_cf / df1.MW
        df1 = df1.drop(['cap_times_cf','MW'], axis=1)
    elif aggfunc == 'resources':
        ### Special case: Rebuild the 'resources' column as {tech}_{region}
        df1 = (
            df1
            .assign(resource=df1.i+'_'+df1.r)
            .drop_duplicates()
        )
        ### Special case: If calculating capacity credit by r, replace ccreg with r
        if sw['capcredit_hierarchy_level'] == 'r':
            df1 = df1.assign(ccreg=df1.r).drop_duplicates()
    elif aggfunc == 'recf':
        ### Special case: Region is embedded in the 'resources' column as {tech}_{region}
        col2r = dict(zip(columns, [c.split('_')[-1] for c in columns]))
        col2i = dict(zip(columns, ['_'.join(c.split('_')[:-1]) for c in columns]))
        df1 = df1.rename(columns={'value':'cf'})
        df1['r'] = df1[region_col].map(col2r)
        df1['i'] = df1[region_col].map(col2i)
        ## Get capacities
        df1 = df1.merge(rscweight_nobin, on=['r','i'], how='left')
        ## Similar procedure as above for aggfunc == 'sc_cat'
        df1['i'] = df1['i'].map(lambda x: new_classes.get(x,x))
        df1 = (
            df1
            .assign(r=df1.r.map(r2aggreg))
            .assign(cap_times_cf=df1.cf*df1.MW)
            .groupby(['index','i','r']).sum()
        )
        df1.cf = df1.cap_times_cf / df1.MW
        df1 = df1.rename(columns={'cf':'value'}).reset_index()
        ## Remake the resources (column names) with new regions
        df1['wide'] = df1.i + '_' + df1.r
        df1 = df1.set_index(['index','wide'])[['value']].astype(np.float16)
    else:
        df1 = df1.groupby(fix_cols+region_cols).agg(aggfunc)


    #%%### Put back in original format
    if (aggfunc == 'sc_cat') and (not wide):
        dfout = df1.stack().rename(key).reset_index()[columns]
    elif (aggfunc == 'sc_cat') and wide and (len(fix_cols) == 1):
        dfout = df1.stack().rename('value').unstack('wide').reset_index()[columns].fillna(0)
    elif not wide:
        dfout = df1.reset_index()[columns]
    elif (wide) and (region_col != 'wide') and (len(fix_cols) == 1) and (fix_cols[0] == 'wide'):
        dfout = df1.unstack('wide')['value'].reset_index()
    elif (wide) and (region_col != 'wide') and (len(fix_cols) > 1) and ('wide' in fix_cols):
        dfout = df1.unstack('wide')['value'].reset_index()[columns]
    elif wide and (region_col == 'wide') and len(fix_cols):
        dfout = df1.unstack('wide')['value'].reset_index()

    ### Drop rows where r and rr are the same
    if key == 'drop_dup_r':
        dfout = dfout.loc[dfout[region_cols[0]] != dfout[region_cols[1]]].copy()

    ### Other special-case processing
    if (filename == 'hierarchy.csv') and (sw['capcredit_hierarchy_level'] == 'r'):
        dfout = dfout.assign(ccreg=dfout[region_col]).drop_duplicates()
        dfout['ccreg'].to_csv(os.path.join(inputs_case, 'ccreg.csv'), index=False)

    #%% Unname any unnamed columns
    dfout.rename(columns=the_unnamer, inplace=True)

    #%%### Write it
    if filetype in ['.csv','.csv.gz']:
        dfout.round(decimals).to_csv(
            os.path.join(inputs_case, filepath),
            header=(False if header is None else True),
            index=False,
        )
    elif filetype == '.h5':
        if header == 'keepindex':
            dfwrite = dfout.sort_values(indexnames).set_index(indexnames)
            dfwrite.columns.name = None
        else:
            dfwrite = dfout
        dfwrite.to_hdf(
            os.path.join(inputs_case, filepath), key='data', complevel=4, format='table')
    elif filetype == '.gdx':
        ### Overwrite the projected parameter
        dfall[key] = dfout.round(decimals)
        ### Write the whole file
        gdxpds.to_gdx(dfall, inputs_case+filepath)

    if verbose > 1:
        now = datetime.datetime.now()
        logprint(
            filepath,
            'aggregated ({:.1f} seconds)'.format((now-filetic).total_seconds()))


#%% Finish
toc(tic=tic, year=0, process='input_processing/aggregate_regions.py', 
    path=os.path.join(inputs_case,'..'))
print('Finished aggregate_regions.py')
