""" This script dumps outputs from gdx files to csvs
"""
# %% Imports
# System packages
import argparse
import ctypes
import datetime
import os
import site
import traceback
import sys

# Third-party packages
import numpy as np
import pandas as pd


# Note this will allow us the new gams once it is widely available.
try:
    import gams.transfer as gt

    gams_test = gt.Container()
except (AttributeError, ModuleNotFoundError):
    import gdxpds


#%% Generic functions
def get_dtype(col):
    if col.lower() == "value":
        return np.float32
    elif col in ["t", "allt"]:
        return np.uint16
    else:
        return "category"


def dfdict_to_csv(dfdict, filepath, symbol_list=None, rename=dict()):
    """
    Write dictionary of dataframes to individual .csv files

    Inputs
    ------
    * rename: dictionary of file names that are different from the variable name
    """
    # unless a subset is specified, iterate over all keys in dict
    _symbol_list = dfdict.keys() if symbol_list is None else symbol_list

    # iterate over symbols and save as csv
    for symbol in _symbol_list:
        file_out = rename.get(symbol, symbol)
        try:
            df_out = (
                dfdict[symbol].records
                if "gdxpds" not in sys.modules
                else dfdict[symbol]
            )
        except:
            print(f"Missing {symbol} in gdx, skipping.")
            continue

        print(f"Saving {symbol} as {file_out}.csv")

        # NOTE: Gams transfer appends junk to the end of the column name, this will
        # get rid of it. We can probably remove this if they change this
        # function in future versions.
        if "gdxpds" not in sys.modules and df_out is not None:
            df_out.columns = df_out.columns.str.replace(r"_\d+$", "", regex=True)

        # If df_out is empty just create an empty dataframe to save the data
        if df_out is None:
            df_out = pd.DataFrame()

        df_out.to_csv(os.path.join(filepath, f"{file_out}.csv"), index=False)


def dfdict_to_h5(
    dfdict,
    filepath,
    overwrite=True,
    symbol_list=None,
    rename=dict(),
    errors="warn",
    **kwargs,
):
    """
    Write dictionary of dataframes to one .h5 file
    """
    ### unless a subset is specified, iterate over all keys in dict
    _symbol_list = dfdict.keys() if symbol_list is None else symbol_list

    ### Check for existing file
    _filepath = filepath if filepath.endswith(".h5") else filepath + ".h5"
    if os.path.exists(_filepath):
        if overwrite:
            os.remove(_filepath)
        else:
            raise NameError(
                f"{_filepath} already exists; to overwrite set overwrite=True"
            )
    ### iterate over symbols and add to .h5 file

    for key in _symbol_list:
        try:
            df = dfdict[key].copy()
            ## Sets have `c_bool(True)` as the value for every entry, so just
            ## drop the Value column if it's a set
            if "Value" in df:
                if len(df) and (type(df.Value.values[0]) == ctypes.c_bool):
                    df = df.drop("Value", axis=1)
            df = df.astype({col: get_dtype(col) for col in df})
            df.to_hdf(
                _filepath,
                key=rename.get(key, key),
                mode="a",
                index=False,
                format="table",
                complevel=4,
                **kwargs,
            )
        except Exception as err:
            print(key)
            print(traceback.format_exc())
            if errors == "raise":
                raise Exception(err)


def dfdict_to_excel(
    dfdict,
    filepath,
    overwrite=True,
    symbol_list=None,
    rename=dict(),
    errors="warn",
    **kwargs,
):
    """
    Write dictionary of dataframes to one .xlsx file
    """
    ### unless a subset is specified, iterate over all keys in dict
    _symbol_list = dfdict.keys() if symbol_list is None else symbol_list

    ### Check for existing file
    _filepath = filepath if filepath.endswith(".xlsx") else filepath + ".xlsx"
    if os.path.exists(_filepath):
        if overwrite:
            os.remove(_filepath)
        else:
            raise NameError(
                f"{_filepath} already exists; to overwrite set overwrite=True"
            )
    ### iterate over symbols and add to .h5 file
    with pd.ExcelWriter(_filepath) as w:
        for key in _symbol_list:
            try:
                dfdict[key].to_excel(w, sheet_name=rename.get(key, key), index=False)
            except Exception as err:
                print(key)
                print(traceback.format_exc())
                if errors == "raise":
                    raise Exception(err)


def write_dfdict(
    dfdict,
    filepath,
    filetype="csv",
    overwrite=True,
    symbol_list=None,
    rename=dict(),
    errors="warn",
    **kwargs,
):
    """
    Write dictionary of dataframes
    Notes
    * If filepath ends with .h5 or .xlsx, filetype will be overwritten to match
    * To read single dataframes from the resulting .h5 file, use:
      `pd.read_hdf('path/to/outputs.h5', 'cap')` (for example)
    """
    ### Overwrite filetype if necessary
    if filepath.endswith(".h5") or filepath.endswith(".xlsx"):
        _filetype = os.path.splitext(filepath)[1].strip(".")
    else:
        _filetype = filetype.strip(".")
    ### Format filepath
    _dotfiletype = "." + _filetype
    _filepath = filepath if filepath.endswith(_dotfiletype) else filepath + _dotfiletype

    ### Run it
    if _filetype == "csv":
        dfdict_to_csv(
            dfdict=dfdict,
            filepath=filepath,
            symbol_list=symbol_list,
            rename=rename,
        )
    elif _filetype == "h5":
        dfdict_to_h5(
            dfdict=dfdict,
            filepath=_filepath,
            overwrite=overwrite,
            symbol_list=symbol_list,
            rename=rename,
            errors=errors,
            **kwargs,
        )
    elif _filetype == "xlsx":
        dfdict_to_excel(
            dfdict=dfdict,
            filepath=_filepath,
            overwrite=overwrite,
            symbol_list=symbol_list,
            rename=rename,
            errors=errors,
            **kwargs,
        )


#%% Functions for extra postprocessing of particular outputs
def timeslice_to_timestamp(case, param):
    ### Load the timestamps and other ReEDS settings
    # timestamps = pd.read_csv(os.path.join(case,'inputs_case','timestamps.csv'))
    # h_szn = pd.read_csv(os.path.join(case,'inputs_case','h_szn.csv'))
    h_dt_szn = pd.read_csv(os.path.join(case,'inputs_case','h_dt_szn.csv'))
    sw = pd.read_csv(
        os.path.join(runname, 'inputs_case', 'switches.csv'), header=None, index_col=0
    ).squeeze(1)
    sw['GSw_HourlyWeatherYears'] = [int(y) for y in sw['GSw_HourlyWeatherYears'].split('_')]
    ### Get the timestamps for the modeled weather yeras
    hs = h_dt_szn.loc[
        h_dt_szn.year.isin(sw['GSw_HourlyWeatherYears']),
        'h'
    ].to_frame()
    hs['timestamp'] = pd.concat([
        pd.Series(
            pd.date_range(
                f'{y}-01-01',f'{y+1}-01-01',closed='left',freq='H',tz='EST'
            )[:8760])
        for y in sw['GSw_HourlyWeatherYears']
    ]).values
    hs = hs.set_index('timestamp').h.tz_localize('UTC').tz_convert('EST')
    ### Load the ReEDS output file
    rename = {'allh':'h', 'allt':'t'}
    dfin_timeslice = pd.read_csv(
        os.path.join(case,'outputs',f'{param}.csv')
    ).rename(columns=rename)
    indices = [c for c in dfin_timeslice if c != 'Value']
    if 'h' not in indices:
        raise Exception(f"{param} does not have an h index: {indices}")
    indices_fixed = [c for c in indices if c != 'h']
    ### Convert to an hourly timeseries
    dfout_h = (
        dfin_timeslice
        .pivot(index='h', columns=indices_fixed, values='Value')
        ## Create entries for each timestamp but labeled by timeslices
        .loc[hs]
        .fillna(0)
        ## Add the timestamp index
        .set_index(hs.index)
    )
    return dfout_h


def timestamp_to_month(dfin_timestamp):
    """
    Index should be a DateTimeIndex
    Output is average over month
    """
    dfout_month = (
        dfin_timestamp.groupby(dfin_timestamp.index.month).mean()
        .rename_axis('month')
        .T.stack('month').rename('Value')
        .reset_index()
    )
    ## Convert format of month for plexos
    dfout_month['month'] = dfout_month['month'].astype(str).map('M{:0>2}'.format)
    return dfout_month


#%% Procedure
if __name__ == '__main__':
    tic = datetime.datetime.now()
    # parse arguments
    parser = argparse.ArgumentParser(
        description="Convert ReEDS run results from gdx to specified filetype"
    )
    parser.add_argument("runname", help="ReEDS scenario name")
    parser.add_argument(
        "--filetype",
        "-f",
        type=str,
        default="csv",
        choices=["csv", "h5", "xlsx"],
        help="filetype to write",
    )

    args = parser.parse_args()
    runname = args.runname
    filetype = args.filetype

    # #%% Inputs for debugging
    # runname = os.path.expanduser('~/github/ReEDS-2.0/runs/v20230620_ereportM0_USA')
    # runname = (
    #     '/Volumes/ReEDS/FY22-NTP/Candidates/Archive/ReEDSruns/20230719/'
    #     'v20230719_ntpH0_AC_DemMd_90by2035EP__core')
    # filetype = 'csv'

    #%% Set up logger
    reeds_path = os.path.abspath(os.path.dirname(__file__))
    site.addsitedir(os.path.join(reeds_path, 'input_processing'))
    try:
        from ticker import toc, makelog
        log = makelog(scriptname=__file__, logpath=os.path.join(runname, "gamslog.txt"))
    except ModuleNotFoundError:
        print("ticker.py not found, so not logging output")

    print("Starting e_report_dump.py")

    # %%### Parse inputs and get switches
    outpath = os.path.join(runname, "outputs")

    ### Get switches
    sw = pd.read_csv(
        os.path.join(runname, "inputs_case", "switches.csv"), header=None, index_col=0
    ).squeeze(1)

    ### Get new file names if applicable
    dfparams = pd.read_csv(
        os.path.join(runname, "e_report_params.csv"),
        comment="#",
        index_col="param",
    )
    rename = dfparams.loc[~dfparams.output_rename.isnull(), "output_rename"].to_dict()
    ## drop the indices
    rename = {k.split("(")[0]: v for k, v in rename.items()}
    print(f"renamed parameters: {rename}")

    # %%### Write results for each gdx file
    ### outputs gdx
    print("Loading outputs gdx")
    if "gdxpds" not in sys.modules:
        dict_out = gt.Container(
            os.path.join(outpath, f"rep_{os.path.basename(runname)}.gdx")
        ).data
    else:
        dict_out = gdxpds.to_dataframes(
            os.path.join(outpath, f"rep_{os.path.basename(runname)}.gdx")
        )
    print("Finished loading outputs gdx")

    write_dfdict(
        dict_out,
        filepath=(outpath if filetype == "csv" else os.path.join(outpath, "outputs")),
        filetype=filetype,
        rename=rename,
    )

    ### powerfrac results
    if int(sw.GSw_calc_powfrac):
        print("Loading powerfrac gdx")
        dict_powerfrac = gdxpds.to_dataframes(
            os.path.join(outpath, f"rep_powerfrac_{os.path.basename(runname)}.gdx")
        )
        print("Finished loading powerfrac gdx")

        dfdict_to_csv(
            dict_powerfrac,
            (outpath if filetype == "csv" else os.path.join(outpath, "rep_powerfrac")),
            filetype=filetype,
            rename=rename,
        )

    #%% Special handling of particular outputs
    ## Hydrogen prices by month
    try:
        dfin_timestamp = timeslice_to_timestamp(runname, 'h2_price_h')
        dfout_month = timestamp_to_month(dfin_timestamp)
        dfout_month.rename(columns={'Value':'$2004/kg'}).to_csv(
            os.path.join(outpath, 'h2_price_month.csv'), index=False)
    except Exception as err:
        print(traceback.format_exc())

    #%% All done
    print("Completed e_report_dump.py")
    try:
        toc(tic=tic, year=0, path=runname, process="e_report_dump.py")
    except NameError:
        print("ticker.py not found, so not logging output")
