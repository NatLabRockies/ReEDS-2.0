"""
prbrown 20201109 16:22

Notes to user:
--------------
* This script loops over files in runs/{}/inputs_case/ and projects them forward
based on the directions given in inputs/userinput/futurefiles.csv.
If new files have been added to inputs_case, you'll need to add rows with 
processing directions to futurefiles.csv. 
The column names should be self-explanatory; most likely there's also at least
one similarly-formatted file in inputs_case that you can copy the settings for.
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
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%%#################
### FIXED INPUTS ###
decimals = 6

#%%###############################
### Functions and dictionaries ###
the_unnamer = {'Unnamed: {}'.format(i): '' for i in range(1000)}

def interpolate_missing_years(df, method='linear'):
    """
    Inputs
    ------
    df : pd.DataFrame with columns as integer years
    method : interpolation method [default = 'linear']
    """
    dfinterp = (
        df
        ### Switch column names from integer years to timestamps
        .rename(columns={c: pd.Timestamp(str(c)) for c in df.columns})
        ### Add empty columns at year-starts between existing data 
        ### (mean doesn't do anything)
        .resample('YS', axis=1).mean()
        ### Interpolate linearly to fill the new columns
        ### (interpolate only works on rows, so pivot, interpolate, pivot again)
        .T.interpolate(method).T
    )
    ### Switch back to integer-year column names
    dfout = dfinterp.rename(columns={c: c.year for c in dfinterp.columns})
    return dfout

def forecast(
        dfi, lastdatayear, addyears, forecast_fit,
        clip_min=None, clip_max=None):
    """
    Project additional year columns and add to df based on directions in forecast_fit.
    forecast_fit can be in ['constant','linear_X','yoy_X','cagr_X','log_X'],
    where 'X' is the number of years to use for the fit.
    'linear' projects linearly, while 'yoy','cagr','log' (all the same) projects
    a constant compound annual growth rate.
    """
    dfo = dfi.copy()
    if forecast_fit == 'constant':
        ### Assign each future year to last data year
        for addyear in addyears:
            dfo[addyear] = dfo[lastdatayear].copy()
    elif forecast_fit.startswith('linear'):
        ### Get the number of years to fit from the futurefiles entry
        fitlength = int(forecast_fit.split('_')[1])
        fityears = list(range(lastdatayear-fitlength, lastdatayear+1))
        ### Fit each row individually
        slope, intercept = {}, {}
        for row in dfo.index:
            slope[row], intercept[row] = np.polyfit(
                x=fityears, y=dfo.loc[row, fityears].values, deg=1)
        ### Apply the row-specific fits
        for addyear in addyears:
            ### Clip if desired, otherwise just project the fit
            if (clip_min is not None) or (clip_max is not None):
                dfo[addyear] = (
                    dfo.index.map(intercept) + dfo.index.map(slope) * addyear
                ).values.clip(clip_min,clip_max)
            else:
                dfo[addyear] = dfo.index.map(intercept) + dfo.index.map(slope) * addyear
    elif (forecast_fit.startswith('cagr') 
            or forecast_fit.startswith('yoy') 
            or forecast_fit.startswith('log')):
        ### Get the number of years to fit from the futurefiles entry
        fitlength = int(forecast_fit.split('_')[1])
        fityears = list(range(lastdatayear-fitlength, lastdatayear+1))
        ### Fit each row individually. By taking the exp() of the fit to log(y)
        ### we get the compound annual growth rate (cagr) + 1.
        cagr = {}
        for row in dfo.index:
            cagr[row] = np.exp(np.polyfit(
                x=fityears, y=np.log(dfo.loc[row, fityears].values), deg=1)[0])
        ### Apply the row-specific fits
        for addyear in addyears:
            ### Clip if desired, otherwise just project the fit
            if (clip_min is not None) or (clip_max is not None):
                dfo[addyear] = (
                    dfo[lastdatayear] * (dfo.index.map(cagr) ** (addyear - lastdatayear))
                ).values.clip(clip_min,clip_max)
            else:
                dfo[addyear] = (
                    dfo[lastdatayear] * (dfo.index.map(cagr) ** (addyear - lastdatayear)))
    else:
        raise Exception(
            'forecast_fit == {} is not implemented; try constant, linear, or cagr'.format(
                forecast_fit))
    return dfo

#%%##############
### PROCEDURE ###
if __name__ == '__main__':

    #%%####################
    ### ARGUMENT INPUTS ###
    parser = argparse.ArgumentParser(description='Extend inputs to arbitrary future year')
    parser.add_argument('reeds_path', help='path to ReEDS directory')
    parser.add_argument('inputs_case', help='path to inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = os.path.join(args.inputs_case, '')

    # #%%#########################
    # ### Settings for testing ###
    # reeds_path = os.path.expanduser('~/github/ReEDS-2.0')
    # inputs_case = os.path.join(reeds_path,'runs','v20220411_prmM0_USA2060','inputs_case')

    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    #%% Inputs from switches
    sw = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
    endyear = int(sw.endyear)
    distpvscen = sw.distpvscen
    ###### Inputs related to debugging
    ### Set debug == True to write to a new folder (inputs_case/future/), leaving original files
    ### intact. If debug == False (default), the original files are overwritten.
    debug = False
    ### missing: 'raise' or 'warn'
    missing = 'raise'
    ### verbose: 0, 1, 2
    verbose = 2

    #%%####################################
    ### If endyear <= 2050, exit the script
    if endyear <= 2050:
        print('endyear = {} <= 2050, so skip forecast.py'.format(endyear))
        quit()
    else:
        print('Starting forecast.py', flush=True)

    #%%###################
    ### Derived inputs ###

    ### Get the case name (ReEDS-2.0/runs/{casename}/inputscase/)
    casename = inputs_case.split(os.sep)[-3]

    ### DEBUG: Make the outputs directory
    if debug:
        outpath = os.path.join(inputs_case, 'future', '')
        os.makedirs(outpath, exist_ok=True)
    else:
        outpath = inputs_case
    ### Get the modeled years
    tmodel_new = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv')).columns.astype(int).values

    ### Get the settings file
    futurefiles = pd.read_csv(
        os.path.join(reeds_path, 'inputs', 'userinput', 'futurefiles.csv'),
        dtype={
            'header':'category', 'ignore':int, 'wide':int,
            'year_col':str, 'fix_cols':str, 'clip_min':str, 'clip_max':str,
        }
    )
    ### Fill in the missing parts of filenames
    futurefiles.filename = futurefiles.filename.map(
        lambda x: x.format(casename=casename, distpvscen=distpvscen)
    )
    ### If any files are missing, stop and alert the user
    inputfiles = [os.path.basename(f) for f in glob(os.path.join(inputs_case,'*'))]
    missingfiles = [
        f for f in inputfiles if ((f not in futurefiles.filename.values) and ('.' in f))]
    if any(missingfiles):
        if missing == 'raise':
            raise Exception(
                'Missing future projection method for:\n{}\n'
                '>>> Need to add entries for these files to futurefiles.csv'
                .format('\n'.join(missingfiles))
            )
        else:
            from warnings import warn
            warn(
                'Missing future directions for:\n{}\n'
                '>>> For this run, these files are copied without modification'
                .format('\n'.join(missingfiles))
            )
            for filename in missingfiles:
                shutil.copy(os.path.join(inputs_case, filename), os.path.join(outpath, filename))
                print('copied {}, which is missing from futurefiles.csv'.format(filename),
                    flush=True)

    #%% Loop it
    for i in futurefiles.index:
        filename = futurefiles.loc[i, 'filename']
        if futurefiles.loc[i,'ignore'] == 0:
            pass
        ### if ignore == 1, just copy the file to outpath and skip the rest
        elif futurefiles.loc[i, 'ignore'] == 1:
            if debug:
                shutil.copy(os.path.join(inputs_case, filename), os.path.join(outpath, filename))
            if verbose > 1:
                print('ignored: {}'.format(filename), flush=True)
            continue
        ### if ignore == 2, need to project for EFS or copy otherwise
        elif futurefiles.loc[i, 'ignore'] == 2:
            ### Read the file to determine if it's formatted for default or EFS load
            dftest = pd.read_csv(os.path.join(inputs_case, filename), header=0, nrows=20)
            ### If it has more than 10 columns (indicating EFS), follow the directions
            if dftest.shape[1] > 10:
                pass
            ### Otherwise (indicating default), just copy it
            else:
                if debug:
                    shutil.copy(os.path.join(inputs_case, filename), os.path.join(outpath, filename))
                if verbose > 1:
                    print('EFS special case: {}'.format(filename), flush=True)
                continue

        ### If the file isn't in inputs_case, skip it
        if filename not in inputfiles:
            if verbose > 1:
                print('skipped since not in inputs_case: {}'.format(filename))
            continue

        #%% Settings
        ### header: 0 if file has column labels, otherwise 'None'
        header = (None if futurefiles.loc[i,'header'] == 'None'
                    else 'keepindex' if futurefiles.loc[i,'header'] == 'keepindex'
                    else int(futurefiles.loc[i,'header']))
        ### year_col: usually 't' or 'year', or 'wide' if file uses years as columns
        year_col = futurefiles.loc[i, 'year_col']
        ### forecast_fit: '{method}_{fityears}' or 'constant', with method in 
        ### ['linear','cagr'] and fityears indicating the number of historical years
        ### (counting backwards from the last data year) to use for the projection.
        ### If set to 'constant', will use the value from the last data year for
        ### all future years.
        forecast_fit = futurefiles.loc[i, 'forecast_fit']
        ### fix_cols: indicate columns to use as for fields that should be projected
        ### independently to future years (e.g. r, szn, tech)
        fix_cols = futurefiles.loc[i, 'fix_cols']
        fix_cols = (list() if fix_cols == 'None' else fix_cols.split(','))
        ### wide: 1 if any parameters are in wide format, otherwise 0
        wide = futurefiles.loc[i, 'wide']
        ### clip_min, clip_max: Indicate min and max values for projected data.
        ### In general, costs should have clip_min = 0 (so they don't go negative)
        clip_min, clip_max = futurefiles.loc[i,['clip_min','clip_max']]
        clip_min = (None if clip_min.lower()=='none' else int(clip_min))
        clip_max = (None if clip_max.lower()=='none' else int(clip_max))
        filetype = futurefiles.loc[i, 'filetype']
        ### key: only used for gdx files, indicating the parameter name. 
        ### gdx files need a separate line in futurefiles.csv for each parameter.
        key = futurefiles.loc[i, 'key']
        efs = False

        ### Load it
        if filetype in ['.csv', '.csv.gz']:
            dfin = pd.read_csv(os.path.join(inputs_case, filename), header=header,)
        elif filetype == '.h5':
            ### Currently load.h5 is the only h5 file we need to project forward, so the
            ### procedure is currently specific to that file
            dfin = pd.read_hdf(os.path.join(inputs_case, filename))
            if header == 'keepindex':
                indexnames = list(dfin.index.names)
                dfin.reset_index(inplace=True)
            ### We only need to do the projection for load.h5 if we're using EFS load,
            ### which has a (year,hour) multiindex (which we reset above to columns). 
            ### If dfin doesn't have 'year' and 'hour' columns, we can therefore skip this file.
            if (('year' in dfin.columns) and ('hour' in dfin.columns)):
                efs = True
            else:
                if debug:
                    shutil.copy(os.path.join(inputs_case, filename), os.path.join(outpath, filename))
                if verbose > 1:
                    print('ignored: {}'.format(filename), flush=True)
                continue
        elif filetype == '.txt':
            dfin = pd.read_csv(os.path.join(inputs_case, filename), header=header, sep=' ')
            ### Remove parentheses and commas
            for col in [0,1]:
                dfin[col] = dfin[col].map(
                    lambda x: x.replace('(','').replace(')','').replace(',',''))
            ### Split the index column on periods
            num_indices = len(dfin.loc[0,0].split('.'))
            indexcols = ['i{}'.format(index) for index in range(num_indices)]
            for index in range(num_indices):
                dfin['i{}'.format(index)] = dfin[0].map(lambda x: x.split('.')[index])
            ### Make the data column numeric
            dfin[1] = dfin[1].astype(float)
            ### Reorder and rename the columns
            dfin = dfin[indexcols + [1]].copy()
            dfin.columns = list(range(num_indices+1))
        elif filetype == '.gdx':
            ### Read in the full gdx file, but only change the 'key' parameter
            ### given in futurefiles. That's wasteful, but there are currently no
            ### active gdx files.
            dfall = gdxpds.to_dataframes(os.path.join(inputs_case, filename))
            dfin = dfall[key]
        else:
            raise Exception('Unsupported filetype: {}'.format(filename))

        dfin.rename(columns={c:str(c) for c in dfin.columns}, inplace=True)
        columns = dfin.columns.tolist()

        #%% Reshape to wide format with year as column
        if (len(fix_cols) == 0) and (wide == 0):
            ### File is simply (year,data)
            ### So just set year as index and transpose
            df = dfin.set_index(year_col).T
        elif (len(fix_cols) > 0) and (year_col == 'wide'):
            ### File has some fixed columns and then years in wide format
            ### Easy - just set the fix_cols as indices and keep years as columns
            df = dfin.set_index(fix_cols)
        elif (wide) and (year_col != 'wide') and (len(fix_cols) == 0):
            ### Some value other than year is in wide format
            ### So set years as index and transpose
            df = dfin.set_index(year_col).T
        elif (wide) and (year_col != 'wide') and (len(fix_cols) > 0):
            ### Some value other than year is in wide format
            ### So set years (and other fix_cols) as index and transpose
            df = (dfin.melt(id_vars=[year_col]+fix_cols, ignore_index=False)
                .set_index([year_col]+fix_cols+['variable'])
                .unstack(year_col))
            ### Get the value name (in this case for the non-year wide column), then drop it
            valuename = df.columns.get_level_values(0).unique().tolist()
            if len(valuename) > 1:
                raise Exception('Too many data columns: {}'.format(valuename))
            valuename = valuename[0]
            df = df[valuename].copy()
        elif (len(fix_cols) > 0) and (year_col != 'wide') and (not wide):
            ### Tidy format - fix the fix_cols and unstack the year_col
            ### same as `df = dfin.pivot(index=fix_cols, columns=year_col)`, but 
            ### pivot modifies fix_cols for some reason
            df = dfin.set_index(fix_cols+[year_col]).unstack(year_col)#.droplevel(0, axis=1)
            ### Get the value name, then drop it
            valuename = df.columns.get_level_values(0).unique().tolist()
            if len(valuename) > 1:
                raise Exception('Too many data columns: {}'.format(valuename))
            valuename = valuename[0]
            df = df[valuename].copy()
        else:
            raise Exception('Unknown data type for {}'.format(filename))

        #%% All columns should now be years
        df.rename(columns={c: int(c) for c in df.columns}, inplace=True)
        lastdatayear = max([int(c) for c in df.columns])
        ### Interpolate to make sure we have data at yearly frequency
        df = interpolate_missing_years(df)
        ### Get indices for projection
        addyears = list(range(lastdatayear+1, endyear+1))
        ### If file is for EFS hourlyload, only project for years in tmodel_new to save time
        if efs:
            addyears = [y for y in addyears if y in tmodel_new]

        #%% Do the projection
        df = forecast(
            dfi=df, lastdatayear=lastdatayear, addyears=addyears, 
            forecast_fit=forecast_fit, clip_min=clip_min, clip_max=clip_max)

        ## #%% Would be nice to keep only the years in tmodel_new, but
        ## #%% createmodel breaks when the following line is active (not sure why)
        ## df.drop([y for y in df.columns if y not in tmodel_new], axis=1, inplace=True)

        #%% Put back in original format
        if (len(fix_cols) == 0) and (wide == 0):
            dfout = df.T.reset_index()
        elif (len(fix_cols) > 0) and (year_col == 'wide'):
            dfout = df.reset_index()
        elif (wide) and (year_col != 'wide') and (len(fix_cols) == 0):
            dfout = df.T.reset_index()
        elif (wide) and (year_col != 'wide') and (len(fix_cols) > 0):
            dfout = df.stack().unstack('variable').reset_index()[columns]
        elif (len(fix_cols) > 0) and (year_col != 'wide') and (not wide):
            dfout = df.stack().rename(valuename).dropna().reset_index()

        ### Unname any unnamed columns
        dfout.rename(columns=the_unnamer, inplace=True)

        #%% Write it
        if filetype in ['.csv','.csv.gz']:
            dfout.round(decimals).to_csv(
                os.path.join(outpath, filename),
                header=(False if header is None else True),
                index=False,
            )
        elif filetype == '.h5':
            if header == 'keepindex':
                dfwrite = dfout.sort_values(indexnames).set_index(indexnames)
                dfwrite.columns.name = None
            else:
                dfwrite = dfout
            dfwrite.round(decimals).to_hdf(os.path.join(outpath, filename), key='data', complevel=4)
        elif filetype == '.txt':
            dfwrite = dfout.sort_index(axis=1)
            ### Make the GAMS-readable index
            dfwrite.index = dfwrite.apply(
                lambda row: '(' + '.'.join([str(row[str(c)]) for c in range(num_indices)]) + ')',
                axis=1
            )
            ### Downselect to data column
            dfwrite = dfwrite[str(num_indices)].round(decimals)
            ### Add commas to data column, remove from last entry
            dfwrite = dfwrite.astype(str) + ','
            dfwrite.iloc[-1] = dfwrite.iloc[-1].replace(',','')
            ### Write it
            dfwrite.to_csv(
                os.path.join(outpath, filename),
                header=(False if header is None else True),
                index=True, sep=' ',
            )
        elif filetype == '.gdx':
            ### Overwrite the projected parameter
            dfall[key] = dfout.round(decimals)
            ### Write the whole file
            gdxpds.to_gdx(dfall, outpath+filename)

        if verbose > 1:
            print(
                'projected from {} to {}: {}'.format(lastdatayear, endyear, filename), 
                flush=True)

    toc(tic=tic, year=0, process='input_processing/forecast.py', 
        path=os.path.join(inputs_case,'..'))
    print('Finished forecast.py')

## ##############################
## ### Initial one-time setup ###
## infiles = pd.DataFrame(
##     {'filename': [os.path.basename(f) for f in glob(os.path.join(inputs_case,'*'))]})
## infiles['filetype'] = infiles.filename.map(lambda x: os.path.splitext(x)[1])
## infiles.sort_values(['filetype','filename'], inplace=True)
## infiles.to_csv(
##     os.path.join(reeds_path, 'inputs', 'userinput', 'futurefiles.csv'),
##     index=False
## )