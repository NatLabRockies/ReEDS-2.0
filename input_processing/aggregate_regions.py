"""
prbrown 20220421
Notes to user:
--------------
* This script loops over files in runs/{}/inputs_case/ and agg/disaggregates
  them based on the directions given in runfiles.csv.
    * If new files have been added to inputs_case, you'll need to add rows with
      processing directions to runfiles.csv.
    * The column names should be self-explanatory; most likely there's also at least
      one similarly-formatted file in inputs_case that you can copy the settings for.
* Some files are agg/disaggregated in other scripts:
    * WriteHintage.py (these files are handled upstream since
      aggregation affects the clustering of generators into (b/h/v)intages):
        * hintage_data.csv
"""

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import numpy as np
import os
import pandas as pd
import gdxpds
import shutil
import sys
import datetime
from glob import glob
from warnings import warn
import h5py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
## Time the operation of this script
tic = datetime.datetime.now()


#%% ===========================================================================
### --- FUNCTIONS AND DICTIONARIES ---
### ===========================================================================

the_unnamer = {'Unnamed: {}'.format(i): '' for i in range(1000)}

aggfuncmap = {
    'mode': pd.Series.mode,
}

def logprint(filepath, message):
    print('{:-<45}> {}'.format(filepath+' ', message))


def refilter_regions(df, region_cols, region_col, val_r_all):
    '''
    This function is used to filter by region again for cases when only a subset of a model
    balancing area is represented
    '''
    dfout = df.copy()
    if ('*r' in region_cols) and ('rr' in region_cols):
        dfout = dfout.loc[dfout.index.get_level_values('*r').isin(val_r_all)]
        dfout = dfout.loc[dfout.index.get_level_values('rr').isin(val_r_all)]
    else:
        dfout = dfout.loc[dfout.index.get_level_values(region_col).isin(val_r_all)]

    return dfout


def aggreg_methods(
    df, row, aggfunc, region_cols, region_col,
    r2aggreg, r_ba, disagg_data, sw, indexnames, columns,
):
    df1 = df.copy()
    ### Pre-aggregation: Map old regions to new regions
    if aggfunc in ['sum','mean','first','min','sc_cat','resources']:
        # Exception for dr_shed_hourly becuase the wide column contains tech|region
        if 'dr_shed_hourly' in row.name:
            # Separate tech and region from the 'wide' column
            df1[['tech', 'region']] = df1['wide'].str.split('|', expand=True)
            # Map regions to aggregated regions
            df1['region'] = df1['region'].map(r2aggreg)
            # Recombine tech and aggregated region into the 'wide' column
            df1['wide'] = df1['tech'] + '|' + df1['region']   
        else:
            for c in region_cols:
                df1[c] = df1[c].map(lambda x: r2aggreg.get(x,x))
            if row.i_col:
                df1[row.i_col] = df1[row.i_col].map(lambda x: new_classes.get(x,x))

    if aggfunc == 'sc_cat':
        ## Weight cost by cap; if there's no cap, use 1 MW as weight
        for cost_type in sc_cost_types:
            ## Geothermal doesn't have all sc_cost_types
            if cost_type in df1:
                df1[f'cap_times_{cost_type}'] = df1['cap'].fillna(1).replace(0,1) * df1[cost_type]
        ## Sum everything
        df1 = df1.groupby(row.fix_cols+[region_col]).sum()
        ## Divide cost*cap by cap
        for cost_type in sc_cost_types:
            if cost_type in df1:
                df1[cost_type] = df1[f'cap_times_{cost_type}'] / df1['cap'].fillna(1).replace(0,1)
                df1.drop([f'cap_times_{cost_type}'], axis=1, inplace=True)
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
               .merge((rscweight_nobin.rename(columns={'i':'*i'}) if '*i' in row.fix_cols
                       else rscweight_nobin),
                       on=['r',('*i' if '*i' in row.fix_cols else 'i')], how='left')
            ## There are some nan's because we subtract existing capacity from the supply curve.
            ## Fill them with 1 MW for now, but it would be better to change that procedure.
            ## Note also that the weighting will be off
               .fillna(1)
            )
        ### Similar procedure as above for aggfunc == 'sc_cat'
        if row.i_col:
            df1[row.i_col] = df1[row.i_col].map(lambda x: new_classes.get(x,x))
        df1 = (
            df1.assign(r=df1.r.map(r_ba))
               .assign(cap_times_cf=df1.cf*df1.MW)
               .groupby(row.fix_cols+region_cols).sum()
            )
        df1.cf = df1.cap_times_cf / df1.MW
        df1 = df1.drop(['cap_times_cf','MW'], axis=1)
    elif aggfunc == 'resources':
        ### Special case: Rebuild the 'resources' column as {tech}|{region}
        df1 = (
            df1.assign(resource=df1.i+'|'+df1.r)
               .drop_duplicates()
            )
        ### Special case: If calculating capacity credit by r, replace ccreg with r
        if sw['capcredit_hierarchy_level'] == 'r':
            df1 = df1.assign(ccreg=df1.r).drop_duplicates()
    elif aggfunc in ['recf', 'csp', 'distpv']:
        ## Get correct rscweight_nobin tech value
        rsctech = os.path.splitext(row.name)[0].split('_')[1]
        rscweight_nobin_tech = rscweight_nobin.loc[rscweight_nobin['i'].str.contains(rsctech)]
        if aggfunc == 'distpv':
            df1['i'] = 'distpv'
            df1['r'] = df1['wide']
        else:
            ### Region is embedded in the 'resources' column as {tech}|{region}
            col2r = dict(zip(columns, [c.split('|')[-1] for c in columns]))
            col2i = dict(zip(columns, [c.split('|')[0] for c in columns]))
            df1 = df1.rename(columns={'value':'cf'})
            df1['r'] = df1[region_col].map(col2r)
            df1['i'] = df1[region_col].map(col2i)
            ## rscweight_nobin data from writesupplycurves.py has tech values of {rsctech}|{class}
            ## so replicate this in order to merge for capacities
            df1['i'] = f'{rsctech}_' + df1['i']

        ## Get capacities
        df1 = df1.merge(rscweight_nobin_tech, on=['r','i'], how='left')
        ## Similar procedure as above for aggfunc == 'sc_cat'
        df1['i'] = df1['i'].map(lambda x: new_classes.get(x,x))
        df1 = df1.rename(columns={'value':'cf'})
        df1 = (
            df1
            .assign(r=df1.r.map(r_ba))
            .assign(cap_times_cf=df1.cf*df1.MW)
            .groupby(indexnames + ['i','r']).sum()
        )
        df1.cf = df1.cap_times_cf / df1.MW
        df1 = df1.rename(columns={'cf':'value'}).reset_index()
        # Revert i column so rsctech is not included in the name.
        # This ensures the resource h5 files will be in the same format when read in recf.py
        # regardless of the spatial resolution
        df1['i'] = df1['i'].str.replace(f'{rsctech}_','')
        ### Remake the resources (column names) with new regions
        df1['wide'] = df1.i + '|' + df1.r
        df1 = df1.set_index(indexnames + ['wide'])[['value']].astype(np.float32)
    elif aggfunc in ['sum','mean','first','min']:
        # Exception for dr_shed_hourly becuase the wide column contains tech|region
        if 'dr_shed_hourly' in row.name : 
            # Group by relevant columns and aggregate values
            df1 = df1.groupby(['datetime', 'wide', 'year'], as_index=False).sum().drop(columns=['tech', 'region'])    
        else:
            df1 = df1.groupby(row.fix_cols+region_cols).agg(aggfunc)

    ### Disaggregation methods --------------------------------------------------------------------
    elif aggfunc == 'uniform':
        for rcol in region_cols:
            df1 = (
                df1.merge(r_ba, left_on=rcol, right_on='ba', how='inner')
                   .drop(columns=[rcol,'ba'])
                   .rename(columns={'FIPS':rcol})
                )
        # if the fixed column is wide, then 'wide' needs to be an index as well
        if (len(row.fix_cols) == 1) and (row.fix_cols[0] == 'wide'):
            df1.set_index([region_col,'wide'],inplace=True)
        else:
            df1.set_index(row.fix_cols+region_cols,inplace=True)
        df1 = refilter_regions(df1, region_cols,region_col, val_r_all)
    elif aggfunc in ['population','geosize','hydroexist']:
        if 'sc_cat' in columns:
            # Split cap and cost
            df1_cap = df1[df1['sc_cat']=='cap']
            df1_cost = df1[df1['sc_cat']=='cost']

            # Disaggregate cap using the selected aggfunc
            fracdata= disagg_data[aggfunc]
            rcol = region_cols[0]
            df1cols = (df1.columns)
            valcol = df1cols[-1]
            # Identify the columns to merge from the fracdata
            fracdata_mergecols = (['PCA_REG'] + [col for col in fracdata.columns
                                    if col not in ['PCA_REG','nonUS_PCA','FIPS','fracdata']])
            # Identify the columns to merge from the original data
            df1_mergecols = [rcol] + [col for col in df1cols if col in fracdata_mergecols]
            # Merge the datasets using PCA_REG
            df1_cap = pd.merge(fracdata, df1_cap, left_on='PCA_REG', right_on= df1_mergecols, how='inner')
            # Apply the weights to create a new value
            df1_cap['new_value'] = (df1_cap['fracdata'].multiply(df1_cap[valcol], axis='index'))
            # Clean up dataframe before grabbing final values
            df1_cap.drop(columns=[valcol]+[rcol],inplace=True)
            df1_cap.rename(columns={'new_value':valcol,'FIPS':rcol},inplace=True)
            new_index = df1cols[:-1]
            df1_cap = df1_cap.set_index(new_index.to_list())
            # Keep cost uniform, so map costs to all subregions with the PCA_REG
            df1_cost = pd.merge(fracdata, df1_cost, left_on='PCA_REG', right_on= df1_mergecols, how='inner')
            df1_cost['new_value'] = df1_cost[valcol]
            df1_cost.drop(columns=[valcol]+[rcol],inplace=True)
            df1_cost.rename(columns={'new_value':valcol,'FIPS':rcol},inplace=True)
            new_index = df1cols[:-1]
            df1_cost = df1_cost.set_index(new_index.to_list())
            # Combine cap and cost to get back into original format
            df1 = pd.concat([df1_cap, df1_cost])
            df1 = refilter_regions(df1, region_cols, region_col,val_r_all)

        elif row.name =='dr_shed_hourly.h5' :
            # separate tech | region
            rcol = df1.wide.str.split('|',expand=True)[1]
            fracdata = disagg_data[aggfunc]
            df1cols = (df1.columns)
            valcol = df1cols[-1]
            # Identify the columns to merge from the fracdata
            fracdata_mergecols = ['PCA_REG'] + [col for col in fracdata.columns
                                    if col not in ['PCA_REG','nonUS_PCA','FIPS','fracdata']]
            # Identify the columns to merge from the original data
            df1_mergecols = [rcol] + [col for col in df1cols if col in fracdata_mergecols]
            # Merge the datasets using PCA_REG
            df1 = pd.merge(fracdata, df1, left_on=fracdata_mergecols, right_on=df1_mergecols, how='inner')
            # Multiply BA shed by population fraction
            df1['new_value'] = (df1['fracdata'].multiply(df1[valcol], axis='index'))
            # Clean up dataframe   
            df1['wide'] = df1.wide.str.split('|',expand=True)[0] +'|' + df1['FIPS']         
            df1 = (df1.drop(columns=[valcol,'PCA_REG','fracdata','FIPS'])
                      .rename(columns={'new_value':valcol}))            
        else:
            # Disaggregate cap using the selected aggfunc
            fracdata = disagg_data[aggfunc]
            rcol = region_cols[0]
            df1cols = (df1.columns)
            valcol = df1cols[-1]
            # Identify the columns to merge from the fracdata
            fracdata_mergecols = ['PCA_REG'] + [col for col in fracdata.columns
                                    if col not in ['PCA_REG','nonUS_PCA','FIPS','fracdata']]
            # Identify the columns to merge from the original data
            df1_mergecols = [rcol] + [col for col in df1cols if col in fracdata_mergecols]
            # Merge the datasets using PCA_REG
            df1 = pd.merge(fracdata, df1, left_on=fracdata_mergecols, right_on=df1_mergecols, how='inner')
            # Clean up dataframe before grabbing final values
            df1['new_value'] = (df1['fracdata'].multiply(df1[valcol], axis='index'))
            df1 = (df1.drop(columns=[valcol]+[rcol])
                      .rename(columns={'new_value':valcol,'FIPS':rcol}))
            new_index = df1cols[:-1]
            df1 = df1.set_index(new_index.to_list())
            df1 = refilter_regions(df1, region_cols,region_col, val_r_all)

    else:
        raise ValueError(f'Invalid choice of aggfunc: {aggfunc} for {row.name}')

    ## Filter by regions again for cases when only a subset of a model balancing area is represented
    if agglevel == 'county':
        if ('*r' in region_cols) and ('rr' in region_cols):
            df1 = df1.loc[df1.index.get_level_values('*r').isin(val_r_all)]
            df1 = df1.loc[df1.index.get_level_values('rr').isin(val_r_all)]
        elif row.name =='dr_shed_hourly.h5':
            # separate tech | region to filter
            df1 = df1.loc[df1.wide.str.split('|',expand=True)[1].isin(val_r_all)]
        else:
            df1 = df1.loc[df1.index.get_level_values(region_col).isin(val_r_all)]

    ################################
    ### Put back in original format ###

    if row.name == 'dr_shed_hourly.h5':
        dfout = df1.set_index(['datetime','year','wide']).unstack('wide')['value'].reset_index()
    elif (aggfunc == 'sc_cat') and (not row.wide):
        dfout = df1.stack().rename(row.key).reset_index()[columns]
    elif (aggfunc == 'sc_cat') and row.wide and (len(row.fix_cols) == 1):
        dfout = df1.stack().rename('value').unstack('wide').reset_index()[columns].fillna(0)
    elif not row.wide:
        dfout = df1.reset_index()[columns]
    elif (row.wide) and (region_col != 'wide') and (len(row.fix_cols) == 1) and (row.fix_cols[0] == 'wide'):
        dfout = df1.unstack('wide')['value'].reset_index()
    elif (row.wide) and (region_col != 'wide') and (len(row.fix_cols) > 1) and ('wide' in row.fix_cols):
        # In some cases disaggregating to county level can lead to empty
        # dataframes, so address that here
        if df1.empty:
            dfout = pd.DataFrame(columns = columns)
        else:
            dfout = df1.unstack('wide')['value'].reset_index()[columns]
    elif row.wide and (region_col == 'wide') and len(row.fix_cols):
        if (len(row.fix_cols) == 1):
            dfout = (
                df1.reset_index()
                .set_index(row.fix_cols)
                .pivot(columns='wide', values='value')
                .reset_index()
            )
        else:
            dfout = df1.unstack('wide')['value'].reset_index()

    ### Drop rows where r and rr are the same
    if row.key == 'drop_dup_r':
        dfout = dfout.loc[dfout[region_cols[0]] != dfout[region_cols[1]]].copy()

    ### Other special-case processing
    if (row.name == 'hierarchy.csv') and (sw['capcredit_hierarchy_level'] == 'r'):
        dfout = dfout.assign(ccreg=dfout[region_col]).drop_duplicates()
        dfout['ccreg'].to_csv(os.path.join(inputs_case, 'ccreg.csv'), index=False)

    dfout.rename(columns=the_unnamer, inplace=True)

    return dfout


def reshape_to_long(
    dfin,
    filepath,
    row,
    indexnames,
    aggfunc,
    region_col,
    region_cols,
):
    if (aggfunc == 'sc_cat') and (not row.wide):
        ### Supply-curve format. Expect an sc_cat column with 'cap' and 'cost' values.
        ## 'cap' values are summed; 'cost' values use the 'cap'-weighted mean
        df = dfin.pivot(
            index=row.fix_cols+region_cols,
            columns='sc_cat',
            values=row.key,
        ).reset_index()
    elif (aggfunc == 'sc_cat') and row.wide and (len(row.fix_cols) == 1):
        ### Supply-curve format. Expect an sc_cat column with 'cap' and 'cost' values.
        ## Some value other than region is in wide format
        ## So turn region and the wide value into the index
        df = dfin.set_index(region_cols+['sc_cat']).stack().rename('value')
        df.index = df.index.rename(region_cols+['sc_cat','wide'])
        ## Make value columns for 'cap' and 'cost'
        df = df.unstack('sc_cat').reset_index()
    elif not row.wide:
        ### File is already long so don't do anything
        df = dfin.copy()
    elif (
        row.wide
        and (region_col != 'wide')
        and (len(row.fix_cols) == 1)
        and (row.fix_cols[0] == 'wide')
    ):
        ## Some value other than region is in wide format
        ## So turn region and the wide value into the index
        df = dfin.set_index(region_col).stack().rename('value')
        df.index = df.index.rename([region_col, 'wide'])
        ## Turn index into columns
        df = df.reset_index()
    elif (
        row.wide
        and (region_col != 'wide')
        and (len(row.fix_cols) > 1)
        and ('wide' in row.fix_cols)
    ):
        ## Some value other than region is in wide format
        ## So turn region, other fix_cols, and the wide value into the index
        df = (
            dfin
            .set_index([region_col]+[c for c in row.fix_cols if c != 'wide'])
            .stack()
            .rename('value')
        )
        df.index = df.index.rename([region_col]+row.fix_cols)
        ## Turn index into columns
        df = df.reset_index()
    elif row.wide and (region_col == 'wide') and len(row.fix_cols):
        ### File has some fixed columns and then regions in wide format
        df = (
            ## Turn all identifying columns into indices, with region as the last index
            dfin.set_index(row.fix_cols).stack()
            ## Name the region column 'wide'
            .rename_axis(row.fix_cols+['wide']).rename('value')
            ## Turn index into columns
            .reset_index()
        )

    return df


def separate_wide_mixed_data(dfin,columns,fix_cols,agglevel_list):
    # Separate mixed BA and county data in wide format

    reg_cols =  [col for col in columns if col not in fix_cols]
    if all('|' in col for col in reg_cols):
        #Find columns with regions that are being solved at BA or aggreg resolution
        # Some inputs files have tech and regions combined as column header and
        # need to be filtered differently
        keep_col = []
        for col in dfin.columns:
            new_col = col.split('|')
            for part in new_col:
                if part in agglevel_list :
                    keep_col.append(col)

        df_sep_in = dfin[fix_cols + keep_col]

    else:
        col_list = fix_cols + agglevel_list
        #Check if data exists for all BAs in agglevel list
        #Loop through each ba in ba region list and add to region_list if it doesn't appear in input data
        regions_list = []
        for ba in  agglevel_list :
            if ba not in dfin.columns :
                regions_list.append(ba)
        #If there is a ba for which there is no data, exclude this ba from the column list
        if len(regions_list) >0 :
            reduced_ba_regions = [x for x in agglevel_list if x not in regions_list]
            df_sep_in = dfin[fix_cols +  reduced_ba_regions]
        #If not, rewrite col_list to exclude BAs for which there is no data
        else:
            df_sep_in = dfin[col_list]

    return df_sep_in


def agg_disagg(filepath, r2aggreg_glob, r_ba_glob, runfiles_row):
    """
    filepath: input file to be aggregated/disaggregated/ignored
    r2aggreg_glob: ba to aggreg mapping needed for single resolution aggreg cases.
                   For mixed resolutions runs the r2aggreg parameter is re-defined separately
                   within the agg_disagg function for data that are being aggregated and disaggregated
    r_ba_glob: r to ba mapping for single resolution runs. For mixed resolution runs r_ba is re-defined
               separately within the agg_disagg function for data that are aggregated and disaggregated
    row : consists of data in runfiles.csv row that correspond with the filepath

    """
    #%% Continue loop
    row = runfiles_row.copy()
    filetic = datetime.datetime.now()
    filename = row.name
    if row['aggfunc']=='ignore' and row['disaggfunc']=='ignore':
        if verbose > 1:
            logprint(filepath, 'ignored')
        return
    ### Ensure the correct aggfunc/disaggfunc is chosen for the given agglevel
     # This will never be true for mixed resolution runs where agglevel is assigned more than one value
    elif ((agglevel in ['ba','aggreg'] and row['aggfunc']=='ignore')
        or (agglevel in ['county'] and row['disaggfunc']=='ignore')):
        if verbose > 1:
            logprint(filepath, 'ignored')
        return
    elif (row['aggfunc']!='ignore') or (row['disaggfunc']!='ignore'):
        pass

    # In mixed resolution runs, some of the inputfiles will contain mixed ba-county data
    # created in copy_files. This data does not need to be aggregated or disaggregated
    # if the resolution selected is ['ba','county'], so skip the file.
    if agglevel_variables['lvl'] == 'mult':
        list_check = ['county','ba']
        list_check= sorted(list_check)
        agglevel_check = sorted(agglevel)
        if list_check == agglevel_check :
            if row['disaggfunc']=='ignore':
                return

    # If the file isn't in inputs_case, skip it
    if filename not in inputfiles:
        if verbose > 1:
            logprint(filepath, 'skipped since not in inputs_case')
        return

    #%%##############
    ### Settings ###

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
    # Assign variable to track if region data exists in two columns
    two_col = False
    if region_col == '*r,rr' or region_col =='r,rr' or region_col == 'transgrp,transgrpp':
        two_col = True
        region_col = region_col.split(',')

    # If solving at mixed resolutions, both disagg and agg functions could be required
    # Check if one of the desired spatial resolutions is county
    if agglevel_variables['lvl'] == 'mult':
        for val in agglevel:
            if val in ['county']:
                aggfunc_agg = aggfuncmap.get(row['aggfunc'], row['aggfunc'])
                aggfunc_disagg = aggfuncmap.get(row['disaggfunc'], row['disaggfunc'])
    #Single resolution procedure
    else:
        ### Set aggfunc to the aggregation setting if using ba or aggreg,
        ### and set to the disaggregation setting if using county
        if agglevel in ['ba','aggreg']:
            aggfunc = aggfuncmap.get(row['aggfunc'], row['aggfunc'])
        elif agglevel in ['county']:
            aggfunc = aggfuncmap.get(row['disaggfunc'], row['disaggfunc'])

    ### wide: 1 if any parameters are in wide format, otherwise 0
    row.wide = int(row.wide)
    ### Get the filetype of the input file from the filename string
    filetype = os.path.splitext(filename)[1].strip('.')
    ### key: only used for gdx files, indicating the parameter name.
    ### gdx files need a separate line in runfiles.csv for each parameter.
    ### fix_cols: indicate columns to use as for fields that should be projected
    ### independently to future years (e.g. r, szn, tech)
    row.fix_cols = (
        [] if row.fix_cols in ['None', 'none', '', None, np.nan]
        else row.fix_cols.split(',')
    )
    ### i_col: indicate technology column. Only used/needed if aggregating techs.
    if row.i_col in ['None', 'none', '', np.nan]:
        row.i_col = None
    # indexnames will get overwritten for h5 files but needs to be defined for the aggreg_methods function
    indexnames = None


    #%%###################
    ### Load the file ###

    if filetype in ['csv', 'gz']:
        # Some csv files are empty and therefore cannot be opened.  If that is
        # the case, then skip them.
        try:
            dfin = pd.read_csv(
                os.path.join(inputs_case, filepath), header=header,
                dtype={'FIPS':str, 'fips':str, 'cnty_fips':str},
            )
        except pd.errors.EmptyDataError:
            return
    elif filetype == 'h5':
        # Skip empty files
        with h5py.File(os.path.join(inputs_case, filepath), 'r') as f:
            if len(f.keys()) == 0:
                return

        dfin = reeds.io.read_file(os.path.join(inputs_case, filepath)).copy()
        if header == 'keepindex':
            indexnames = (dfin.index.names)
            if (len(indexnames) == 1) and (not indexnames[0]):
                indexnames = ['index']
            dfin = dfin.reset_index()
    elif filetype == 'gdx':
        ### Read in the full gdx file, but only change the 'key' parameter
        ### given in runfiles. That's wasteful, but there are currently no
        ### active gdx files.
        dfall = gdxpds.to_dataframes(os.path.join(inputs_case, filepath))
        dfin = dfall[row.key]
    else:
        raise Exception(f'Unsupported filetype: {filepath}')

    dfin.rename(columns={c:str(c) for c in dfin.columns}, inplace=True)
    columns = dfin.columns.tolist()
    ### Stop now if it's empty
    if dfin.empty:
        if verbose > 1:
            logprint(filepath, 'empty')
        return


    #%%############################
    ### Reshape to long format ###

    ########## Mixed Resolution Procedure ##########
    if agglevel_variables['lvl'] == 'mult':
        ########## BA ##########
        # If desired resolution is ['county', 'ba'], then BA data are already in correct format
        # Filter dataframe to regions being solved at BA resolution
        for val in agglevel:
            if val in ['ba']:
                if region_col != 'wide':
                    if two_col :
                        df_agg_in = dfin[dfin[region_col[0]].isin(
                                            agglevel_variables['ba_regions'] + agglevel_variables['ba_transgrp'])]
                        df_agg_in =  df_agg_in[ df_agg_in[region_col[1]].isin(agglevel_variables['ba_regions'])]
                    else:
                        df_agg_in = dfin[dfin[region_col].isin(agglevel_variables['ba_regions'])]
                else:
                    col_list = row.fix_cols + agglevel_variables['ba_regions']
                    # Check if data exists for all BAs in agglevel_variables['ba_regions'] list
                    # Loop through each ba in ba region list and add to region_list if it doesn't appear in input data
                    regions_list = []
                    for ba in  agglevel_variables['ba_regions'] :
                        if ba not in dfin.columns :
                            regions_list.append(ba)
                    # If there is a ba for which there is no data, exclude this ba from the column list
                    if len(regions_list) >1 :
                        reduced_ba_regions = [x for x in agglevel_variables['ba_regions'] if x not in regions_list]
                        df_agg_in = dfin[row.fix_cols +  reduced_ba_regions]
                    #If not, rewrite col_list to exclude BAs for which there is no data
                    else:
                        df_agg_in = dfin[col_list]

                df_agg = df_agg_in

            elif val in ['aggreg']:
                # Subset to include regions being solved at Aggreg
                # If column headers are region names, need to filter after reformatting
                if region_col != 'wide':
                    if two_col :
                        df_agg_in = dfin[dfin[region_col[0]].isin(
                                            agglevel_variables['ba_regions'] + agglevel_variables['ba_transgrp'])]
                        df_agg_in =  df_agg_in[ df_agg_in[region_col[1]].isin(agglevel_variables['ba_regions'])]
                    else:
                        df_agg_in = dfin[dfin[region_col].isin(agglevel_variables['ba_regions'])]

                # Clause to separate mixed BA and county data in wide format
                elif region_col == 'wide':
                    df_agg_in = separate_wide_mixed_data(
                        dfin,
                        columns,
                        row.fix_cols,
                        agglevel_variables['ba_regions'],
                    )

                #Set aggfunc to aggregation function
                aggfunc = aggfunc_agg

                ##### Reformat BA Data ####
                df_agg = reshape_to_long(
                    df_agg_in,
                    filepath,
                    row,
                    indexnames,
                    aggfunc,
                    region_col,
                    region_cols,
                )

        ########## County ##########
        # When aggfunc_disagg is set to ignore the county-level data do not need to be reformatted.
        # Filter county data from BA data that will be aggregated to aggreg
        if aggfunc_disagg == 'ignore':
            if region_col != 'wide':
                if two_col:
                    # County transmission data will have county-ba interfaces created in copy_files
                    # To maintain these interfaces the filtering of the data needs to ensure that BA-BA interfaces
                    # are dropped but county-county and county-BA interfaces are kept
                    df_disagg_list = []
                    for idx, tx_row in dfin.iterrows():
                        cond1 = ((tx_row[region_col[0]] in agglevel_variables['ba_regions']+agglevel_variables['ba_transgrp'])
                                    and (tx_row[region_col[1]] in agglevel_variables['county_regions']+agglevel_variables['county_transgrp']))
                        cond2 = ((tx_row[region_col[1]] in agglevel_variables['ba_regions']+ agglevel_variables['ba_transgrp'])
                                    and (tx_row[region_col[0]] in agglevel_variables['county_regions']+agglevel_variables['county_transgrp']))
                        cond3 = ((tx_row[region_col[0]] in agglevel_variables['county_regions']+agglevel_variables['county_transgrp'])
                                    and (tx_row[region_col[1]] in agglevel_variables['county_regions']+agglevel_variables['county_transgrp']))

                        if cond1 or cond2 or cond3:
                            df_disagg_list.append(tx_row)

                    df_disagg_in = pd.DataFrame(df_disagg_list).drop_duplicates()

                elif filename == 'county2zone.csv':
                    df_disagg_in = dfin[dfin[region_col].isin(agglevel_variables['county_regions2ba'])]
                else:
                    df_disagg_in = dfin[dfin[region_col].isin(agglevel_variables['county_regions'])]
            # Clause to separate mixed BA and county data in wide format
            elif region_col == 'wide':
                df_disagg_in = separate_wide_mixed_data(
                    dfin,
                    columns,
                    row.fix_cols,
                    agglevel_variables['county_regions'],
                )

            # Files where aggfunc_disagg is 'ignore' but aggfunc_agg is NOT 'ignore'
            # indicate that the file will already have county-level data
            # (e.g. csp.h5, recf.h5, load.h5). Copy the separated county-level columns
            # to df_disagg so the script can add them back to dfout once the ba-level data
            # is aggregated
            if aggfunc_agg != 'ignore':
                df_disagg = df_disagg_in.copy()

        else:
            # Need to read in input data at BA level to be disaggregated
            # If column headers are region names, need to filter after reformatting
            if region_col != 'wide':
                if two_col :
                    df_disagg_in = dfin[dfin[region_col[0]].isin(agglevel_variables['county_regions2ba'])]
                    df_disagg_in = df_disagg_in[df_disagg_in[region_col[1]]
                                    .isin(agglevel_variables['county_regions2ba'])]
                else:
                    df_disagg_in = dfin[dfin[region_col].isin(agglevel_variables['county_regions2ba'])]
            else:
                col_list = row.fix_cols + agglevel_variables['county_regions2ba']
                # Check if data exists for all BAs in county_regions2ba list
                regions_list = []
                for ba in agglevel_variables['county_regions2ba']:
                    if ba not in dfin.columns :
                        regions_list.append(ba)
                # If there is a ba for which there is no data, exclude this ba from the column list
                if len(regions_list) >1 :
                    reduced_ba_regions = [x for x in agglevel_variables['county_regions2ba'] if x not in regions_list]
                    df_disagg_in = dfin[row.fix_cols + reduced_ba_regions]
                else:
                    df_disagg_in = dfin[col_list]

            #Set aggfunc to disaggregation function
            aggfunc = aggfunc_disagg

            #####Reformat county Data ####
            df_disagg = reshape_to_long(
                df_disagg_in,
                filepath,
                row,
                indexnames,
                aggfunc,
                region_col,
                region_cols,
            )

    ########### Single Resolution Procedure ###########
    else:
        df = reshape_to_long(
            dfin,
            filepath,
            row,
            indexnames,
            aggfunc,
            region_col,
            region_cols,
        )

        #If the file is empty, move on to the next one as there is nothing to aggregate
        if df.empty:
            if verbose > 1:
                logprint(filepath, 'empty')
            return

    #%%#######################################
    ### Aggregate/Dissaggregate by Region ###

    ########## Mixed Resolution Procedure ##########
    if agglevel_variables['lvl'] == 'mult':
        ########## BA, Aggreg ##########
        # If there are no BA level data, set BA addition to False
        # This will prevent appending an empty dataframe to the county level data below
        if df_agg.empty:
             ba_addition = False
        else:
            ba_addition = True
            # Set aggregation function to aggfunc column value (Done in Settings section above)
            aggfunc = aggfunc_agg
            # Check if solving at aggreg, otherwise aggregating BA data to lower resolution is not necessary
            if 'aggreg' in agglevel:
                r2aggreg = r_aggreg
                r_ba = r_aggreg

                # If aggfunc is not 'ignore', perform aggregation
                if aggfunc != 'ignore':
                    df_agg = aggreg_methods(
                        df_agg, row, aggfunc, region_cols, region_col,
                        r2aggreg, r_ba, disagg_data, sw, indexnames, columns,
                    )

        ########## County ##########

        # If there are no county level data, set county addition to False
        # This will prevent appending an empty dataframe to the BA level data below
        if df_disagg.empty:
             county_addition = False
        else:
            county_addition = True
            # Set aggregation function to aggfunc column value (Done in Settings section above)
            aggfunc = aggfunc_disagg
            # If aggfunc is not 'ignore', perform disaggregation
            if aggfunc != 'ignore':
                # Ensure correct r_ba is used
                r_ba = r_ba_for_county
                r2aggreg = r_ba

                # Disagg for county
                df_disagg = aggreg_methods(
                    df_disagg, row, aggfunc, region_cols, region_col,
                    r2aggreg, r_ba, disagg_data, sw, indexnames, columns,
                )

        # Combine aggregated and disaggregated data
        if ba_addition and county_addition:
            # Combined BA and county data
            if region_col == 'wide':
                dfout = pd.merge(df_agg, df_disagg, how='inner', on=row.fix_cols)
            else:
                dfout = pd.concat([df_agg,df_disagg])
        # Aggregated data only
        if ba_addition and not county_addition:
            dfout = df_agg.copy()
        # Disaggregated data only
        if not ba_addition and county_addition:
            dfout = df_disagg.copy()

        # If neither data exists, skip file
        if not ba_addition and not county_addition:
            if verbose > 1:
                logprint(filepath, 'empty')
            return


    ########## Single Resolution Procedure ##########
    else:
        if agglevel_variables['lvl'] == 'county':
            r2aggreg = r_county
        else:
            r2aggreg = r2aggreg_glob
        r_ba = r_ba_glob
        dfout = aggreg_methods(
            df, row, aggfunc, region_cols, region_col,
            r2aggreg, r_ba, disagg_data, sw, indexnames, columns,
        )

    #%%####################
    ### Data Write-Out ###

    if filetype in ['csv','gz']:
        dfout.round(decimals).to_csv(
            os.path.join(inputs_case, filepath),
            header=(False if header is None else True),
            index=False,
        )
    elif filetype == 'h5':
        if header == 'keepindex':
            dfwrite = dfout.sort_values(indexnames).set_index(indexnames)
            dfwrite.columns.name = None
        else:
            dfwrite = dfout
        reeds.io.write_profile_to_h5(dfwrite, filepath, inputs_case)
    elif filetype == 'gdx':
        ### Overwrite the projected parameter
        dfall[row.key] = dfout.round(decimals)
        ### Write the whole file
        gdxpds.to_gdx(dfall, inputs_case+filepath)

    if verbose > 1:
        now = datetime.datetime.now()
        logprint(
            filepath,
            'aggregated ({:.1f} seconds)'.format((now-filetic).total_seconds()))


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

#%% Parse arguments
parser = argparse.ArgumentParser(description='Extend inputs to arbitrary future year')
parser.add_argument('reeds_path', help='path to ReEDS directory')
parser.add_argument('inputs_case', help='path to inputs_case directory')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = os.path.join(args.inputs_case)

# #%%## Settings for testing
# reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# inputs_case = os.path.join(
#     reeds_path,'runs','v20250301_hydroM0_Pacific','inputs_case')

#%% Settings for debugging
### Set debug == True to copy the original files to a new folder (inputs_case_original).
### If debug == False, the original files are overwritten.
debug = True
### missing: 'raise' or 'warn'
missing = 'raise'
### verbose: 0, 1, 2
verbose = 2

#%%#################
### FIXED INPUTS ###
decimals = 6
### anchortype: 'load' sets rb with largest 2010 load as anchor reg;
### 'size' sets largest rb as anchor reg
anchortype = 'size'
### Types of cost data in files that use sc_cat
sc_cost_types = ['cost', 'cost_cap', 'cost_trans']

######################
### DERIVED INPUTS ###
### Get the case name (ReEDS-2.0/runs/{casename}/inputscase/)
casename = inputs_case.split(os.sep)[-3]

#%% Set up logger
log = reeds.log.makelog(
    scriptname=__file__,
    logpath=os.path.join(inputs_case, '..', 'gamslog.txt'),
)

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0).squeeze(1)
endyear = int(sw.endyear)
GSw_CSP_Types = [int(i) for i in sw.GSw_CSP_Types.split('_')]

scalars = pd.read_csv(
        os.path.join(inputs_case, 'scalars.csv'),
        header=None, usecols=[0,1], index_col=0).squeeze(1)

# Use agglevel_variables function to obtain spatial resolution variables
agglevel_variables = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)
agglevel = agglevel_variables['agglevel']
# Regions present in the current run
val_r_all = sorted(
    pd.read_csv(
         os.path.join(inputs_case, 'val_r_all.csv'), header=None,
    ).squeeze(1).tolist()
)
#%%
#DEBUG: Copy the original inputs_case files
if debug and (agglevel != 'ba'):
    print('Copying original inputs_case file...')
    import distutils.dir_util
    os.makedirs(inputs_case+'_original', exist_ok=True)
    distutils.dir_util.copy_tree(inputs_case, inputs_case+'_original', verbose=0)
#%%
### Mixed Resolution Procedure ###
if agglevel_variables['lvl'] == 'mult' :
    # Get the various region maps created in copy_files.py
    #Need to store separate r_ba values for county and BA data
    r_county = pd.read_csv(os.path.join(inputs_case,'r_county.csv'), index_col='county').squeeze()
    r_ba = pd.read_csv(os.path.join(inputs_case,'r_ba.csv'))
    r_ba_for_county = pd.read_csv(os.path.join(inputs_case,'r_ba.csv')).rename(columns={'r':'FIPS'})
    r_ba_for_ba = pd.read_csv(os.path.join(inputs_case,'r_ba.csv')).set_index('ba').squeeze()

    for val in agglevel_variables['agglevel'] :
        if val == 'aggreg':
            ### Get map from BA to aggreg
            r_aggreg = pd.read_csv(os.path.join(inputs_case,'rb_aggreg.csv')).set_index('ba')['aggreg'].to_dict()


### Single Resolution Procedure ###
else:
    # Get the various region maps created in copy_files.py
    r_county = pd.read_csv(os.path.join(inputs_case,'r_county.csv'), index_col='county').squeeze()
    r_ba = pd.read_csv(os.path.join(inputs_case,'r_ba.csv'))
    # r_ba needs to be in different formats depending on whether you are aggregating
    # or disaggregating
    if agglevel in ['county']:
        r_ba.rename(columns={'r':'FIPS'}, inplace=True)
    elif agglevel in ['ba','aggreg']:
        r_ba = r_ba.set_index('ba').squeeze()
        ### Make all-regions-to-aggreg map
        r2aggreg = pd.concat([r_county, r_ba])

#####################################################
### If using default 134 regions, exit the script ###

if agglevel == 'ba':
    print('all valid regions are BA, so skip aggregate_regions.py')
    quit()
else:
    print('Starting aggregate_regions.py', flush=True)
    ## Read in disaggregation data
    disagg_data = {
        'population': pd.read_csv(
            os.path.join(inputs_case,'disagg_population.csv'),
            header=0,
            dtype={'fracdata':np.float32},
            usecols=["PCA_REG", "FIPS", "fracdata"]
        ),
        'geosize': pd.read_csv(
            os.path.join(inputs_case,'disagg_geosize.csv'),
            header=0,
            usecols=["PCA_REG", "FIPS", "fracdata"]
        ),
        'hydroexist': pd.read_csv(
            os.path.join(inputs_case,'disagg_hydroexist.csv'),
            header=0,
            usecols=["PCA_REG", "FIPS", "i", "fracdata"]
        )
    }

#%%######################################################
### Get the "anchor" zone for each aggregation region ###

# For transmission we want to use the old endpoints to avoid requiring a new run of the
# reV least-cost-paths procedure.

if 'aggreg' in agglevel:
    if agglevel_variables['lvl'] == 'mult':
        r_ba = r_aggreg

    # Written in reeds.io.get_zonemap()
    aggreg2anchorreg = pd.read_csv(os.path.join(inputs_case, 'aggreg2anchorreg.csv'))
    aggreg2anchorreg = aggreg2anchorreg.set_index('aggreg')
    aggreg2anchorreg = aggreg2anchorreg.squeeze()
    anchorreg2aggreg = pd.Series(index=aggreg2anchorreg.values, data=aggreg2anchorreg.index)    
    
    ### Get RSC VRE available capacity to use in capacity-weighted averages
    ### We need the original un-aggregated supply curves, so run writesupplycurves again
    # rscweight = pd.read_csv(os.path.join(inputs_case, 'rsc_combined.csv'))

    # Read generator database and create rsc_wsc (for use in writesupplycurves function call below)
    gendb = pd.read_csv(os.path.join(inputs_case,'unitdata.csv'))
    import writecapdat
    from writecapdat import create_rsc_wsc
    # Set the 'r' column for the generator database
    # Create the 'r_col' column
    gendb = gendb.assign(r=gendb.reeds_ba.map(r_ba))
    startyear = int(sw.startyear)
    rsc_wsc = create_rsc_wsc(gendb, TECH=writecapdat.TECH, scalars=scalars,startyear=startyear)

    import writesupplycurves
    rscweight = writesupplycurves.main(
        reeds_path, inputs_case, AggregateRegions=0, rsc_wsc_dat=rsc_wsc, write=False)
    rscweight = (
        rscweight.loc[(rscweight.sc_cat=='cap')]
        .rename(columns={'*i':'i'})
        .drop_duplicates(subset=['i','r','rscbin'])
        [['i','r','rscbin','value']].rename(columns={'value':'MW'})
    ).copy()

    ### Get distpv capacity to use in capacity-weighted averages
    distpvcap = pd.read_csv(
        os.path.join(inputs_case, 'distpvcap.csv'), index_col=0
    )
    ## Keep a single year
    distpvcap = distpvcap[
        sw.GSw_HourlyClusterYear if sw.GSw_HourlyClusterYear in distpvcap
        else str(int(sw.GSw_HourlyClusterYear) + 1)
    ].rename_axis('r').rename('MW').copy()
    ## Add it to rscweight_nobin
    rscweight_nobin = rscweight.groupby(['i','r'], as_index=False).sum(numeric_only=True)
    rscweight_nobin = pd.concat([rscweight_nobin, distpvcap.reset_index().assign(i='distpv')], axis=0)
    ## Add PVB values in case we need them
    pvbtechs = [f'pvb{i}' for i in sw.GSw_PVB_Types.split('_')]
    tocopy = rscweight_nobin.loc[rscweight_nobin.i.str.startswith('upv')].copy()
    rscweight_nobin = pd.concat(
        [rscweight_nobin]
        + [tocopy.assign(i=tocopy.i.str.replace('upv',pvbtech)) for pvbtech in pvbtechs]
    )
    ## Remove duplicate CSP values for different solar multiples
    rscweight_nobin.i.replace(
        {f'csp{i+1}_{c+1}': f'csp_{c+1}'
         for i in GSw_CSP_Types
         for c in range(int(sw.GSw_NumCSPclasses))},
        inplace=True
    )
    rscweight_nobin.drop_duplicates(['i','r'], inplace=True)

# rscweight_nobin required to be defined for aggreg_methods function call to work
else:
    rscweight_nobin=None

#%% Get the mapping to reduced-resolution technology classes
original_num_classes = {**{f'csp{i}':12 for i in range(1,5)}}
new_classes = {}
for tech in [f'csp{i}' for i in range(1,5)]:
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
runfiles = (
    pd.read_csv(
        os.path.join(reeds_path, 'runfiles.csv'),
        dtype={'fix_cols':str}, index_col='filename',
        comment='#',
    ).fillna({'fix_cols':''})
    .rename(columns={'wide (1 if any parameters are in wide format)':'wide',
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
missingfiles = [f for f in inputfiles if (os.path.basename(f) not in runfiles.index.values)
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

#%% Maps (special case)
mapsfile = os.path.join(inputs_case, 'maps.gpkg')
if os.path.exists(mapsfile):
    os.remove(mapsfile)
dfmap = reeds.io.get_dfmap(os.path.dirname(inputs_case))
for level in dfmap:
    dfmap[level].rename_axis(level).to_file(mapsfile, layer=level)

dfmap = reeds.io.get_dfmap(os.path.dirname(inputs_case))

### Aggregate or disaggregate the 'r' map; none of the rest should change
# Mixed resolution maps are patched together in the get_zonemap() function
if agglevel_variables['lvl'] == 'mult' :
    pass

#Single resolution procedure
else:
    match agglevel:
        case 'aggreg':
            r2aggreg = pd.read_csv(
                os.path.join(inputs_case, 'hierarchy_original.csv')
            ).rename(columns={'ba':'r'}).set_index('r').aggreg
        case 'county':
            aggreg2anchorreg = r2aggreg = r_county.copy()


    dfmap_r_agg = dfmap['r'].reset_index().rename(columns={'rb':'r', 'ba':'r'})
    dfmap_r_agg.r = dfmap_r_agg.r.map(r2aggreg)
    dfmap_r_agg = dfmap_r_agg.dissolve('r').loc[aggreg2anchorreg.index].copy()

    ## Map endpoints to anchor regions
    for j in ['x','y']:
        dfmap_r_agg[j] = dfmap['r'][j].loc[dfmap_r_agg[j].index.map(aggreg2anchorreg)].values
        dfmap_r_agg[f'centroid_{j}'] = dfmap_r_agg.centroid.x if j == 'x' else dfmap_r_agg.centroid.y

    ## Overwrite the non-aggregated zone map
    dfmap['r'] = dfmap_r_agg.drop(columns='county', errors='ignore')

    ## Write the aggregated maps
    mapsfile = os.path.join(inputs_case, 'maps.gpkg')
    if os.path.exists(mapsfile):
        os.remove(mapsfile)
    for level in dfmap:
        (
            dfmap[level]
            .drop(columns='aggreg', errors='ignore')
            .rename_axis(level)
            .to_file(mapsfile, layer=level)
        )

#%%
if agglevel_variables['lvl'] == 'mult' or agglevel == 'county':
    r2aggreg_glob = None
else:
    r2aggreg_glob = r2aggreg
r_ba_glob = r_ba

# loop over inputfiles from runfiles and call aggregation/disaggregation function
for filepath in inputfiles:
    ### For debugging: Specify a file
    # filepath = ''
    ### Get the appropriate row from runfiles
    row = runfiles.loc[os.path.basename(filepath)]
    try:
        agg_disagg(filepath, r2aggreg_glob, r_ba_glob, row)
    except Exception as err:
        print(f"Error processing {filepath}")
        raise Exception(err)

#%% Finish
reeds.log.toc(tic=tic, year=0, process='input_processing/aggregate_regions.py',
    path=os.path.join(inputs_case,'..'))

print('Finished aggregate_regions.py')
