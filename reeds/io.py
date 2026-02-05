### Imports
import os
import sys
import re
import datetime
import h5py
import ctypes
import numpy as np
import pandas as pd
import geopandas as gpd
from glob import glob
from pathlib import Path
from pandas.api.types import is_float_dtype

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if 'runs' in reeds_path.split(os.path.sep):
    reeds_path = reeds_path[: reeds_path.index(os.sep + 'runs' + os.sep)]

hpc = True if ('NREL_CLUSTER' in os.environ) else False

#   ########  ########    ###    ########
#   ##     ## ##         ## ##   ##     ##
#   ##     ## ##        ##   ##  ##     ##
#   ########  ######   ##     ## ##     ##
#   ##   ##   ##       ######### ##     ##
#   ##    ##  ##       ##     ## ##     ##
#   ##     ## ######## ##     ## ########


### Read files from the repo
def inflatifier(inyear, outyear, inflation):
    if inyear < outyear:
        return inflation.loc[inyear + 1 : outyear, 'inflation_rate'].cumprod()[outyear]
    elif inyear > outyear:
        return 1 / inflation.loc[outyear + 1 : inyear, 'inflation_rate'].cumprod()[inyear]
    else:
        return 1


def get_inflatable(inflationpath=None, tmin=1960, tmax=2050):
    """Get an [inyear,outyear] lookup table for inflation"""
    if inflationpath is None:
        filepath = os.path.join(reeds_path, 'inputs', 'financials', 'inflation_default.csv')
    else:
        filepath = inflationpath
    inflation = pd.read_csv(filepath, index_col='t')
    assert tmin >= inflation.index.min()
    assert tmax <= inflation.index.max()
    ### Make the output table
    inflatable = {}
    for inyear in range(tmin, tmax + 1):
        for outyear in range(tmin, tmax + 1):
            inflatable[inyear, outyear] = inflatifier(inyear, outyear, inflation)
    inflatable = pd.Series(inflatable)
    return inflatable


### Read files from the repo or from a ReEDS case
def get_hierarchy(case=None, original=False, country='USA'):
    """Get hierarchy for ReEDs case if provided, or for country if case not provided"""
    if case:
        if original:
            filepath = os.path.join(case, 'inputs_case', 'hierarchy_original.csv')
        else:
            filepath = os.path.join(case, 'inputs_case', 'hierarchy.csv')
    else:
        filepath = os.path.join(reeds_path, 'inputs', 'hierarchy.csv')
    hierarchy = (
        pd.read_csv(filepath)
        .rename(columns={'*r': 'r', 'ba': 'r'})
        .set_index('r')
        .drop(columns=['st_interconnect'], errors='ignore')
    )
    hierarchy = hierarchy.loc[hierarchy.country.str.lower() == country.lower()].copy()
    return hierarchy

def get_county2zone(
    case: str | None = None, as_map: bool = True
) -> pd.DataFrame | pd.Series:
    """
    Read county2zone.csv from the inputs_case folder is {case} is provided
    or from the default set of inputs otherwise.

    Args:
        case: Path to a ReEDS case.
        as_map: If true, return county2zone as a pd.Series indexed by county.

    Returns:
        pd.DataFrame or pd.Series 
    """
    if case is None:
        fpath = os.path.join(reeds.io.reeds_path, 'inputs', 'county2zone.csv')
        r_col = 'ba'
    else:
        fpath = os.path.join(case, 'inputs_case', 'county2zone.csv')
        r_col = 'r'

    county2zone = pd.read_csv(
        fpath,
        dtype={'FIPS':str}
    )
    county2zone = county2zone.set_index('FIPS')[r_col] if as_map else county2zone

    return county2zone

def get_countymap(select_counties=None, exclude_water_areas=False):
    """Get geodataframe of US counties"""
    crs = 'ESRI:102008'
    dfcounty = gpd.read_file(
        os.path.join(reeds_path, 'inputs', 'shapefiles', 'US_COUNTY_2022')
    ).to_crs(crs)

    if select_counties:
        dfcounty = dfcounty[dfcounty['rb'].isin(select_counties)]

    if exclude_water_areas:
        dfmap = get_dfmap(levels=['country'])
        dfcounty['geometry'] = (
            dfcounty.intersection(dfmap['country'].loc['USA','geometry'])
        )

    return dfcounty

def get_zonemap(case=None, exclude_water_areas=False, crs='ESRI:102008'):
    """
    Get geodataframe of model zones, applying aggregation if necessary
    """
    sw = get_switches(case)
    ## Backwards compatibility
    if 'GSw_RegionResolution' not in sw:
        sw['GSw_RegionResolution'] = 'ba'

    if case:
        agglevel_variables = reeds.spatial.get_agglevel_variables(
            reeds_path,
            os.path.join(case, 'inputs_case'),
        )
    else:
        agglevel_variables = {'lvl': 'ba',
                              'agglevel': 'ba',
                              }

    # Mixed resolution procedure
    if agglevel_variables['lvl'] == 'mult':
        ### Model zones
        dfba = gpd.read_file(os.path.join(reeds_path, 'inputs', 'shapefiles', 'US_PCA'))
        ### Use transmission endpoints from reV
        endpoints = gpd.read_file(
            os.path.join(reeds_path, 'inputs', 'shapefiles', 'transmission_endpoints')
        ).set_index('ba_str')
        endpoints['x'] = endpoints.centroid.x
        endpoints['y'] = endpoints.centroid.y

        dfba['x'] = dfba['rb'].map(endpoints.x)
        dfba['y'] = dfba['rb'].map(endpoints.y)
        dfba['centroid_x'] = dfba.geometry.centroid.x
        dfba['centroid_y'] = dfba.geometry.centroid.y

        # Filter to regions being solved at BA resolution
        dfba = dfba[dfba['rb'].isin(agglevel_variables['ba_regions'])].set_index('rb')

        if 'aggreg' in agglevel_variables['agglevel']:
            r2aggreg = (
                pd.read_csv(os.path.join(case, 'inputs_case', 'hierarchy_original.csv'))
                .rename(columns={'ba': 'r'})
                .set_index('r')
                .aggreg
            )
            ### Take the "anchor" zone as the zone with the largest area [km2]
            dfba['km2'] = dfba.area / 1e6
            ## Add column for new regions
            dfba['aggreg'] = dfba.index.map(r2aggreg)
            ## Take the original zone with largest area
            aggreg2anchorreg = dfba.groupby('aggreg').km2.idxmax().rename('rb')
            ## Save it for plotting
            aggreg2anchorreg.to_csv(os.path.join(case,'inputs_case', 'aggreg2anchorreg.csv'))

            aggreg2anchorreg = aggreg2anchorreg.reset_index()
            aggreg2anchorreg = aggreg2anchorreg[aggreg2anchorreg
                ['aggreg'].isin(agglevel_variables['ba_regions'])
            ]
            dfba = dfba.reset_index()
            dfba.rb = dfba.rb.map(r2aggreg)
            dfba = dfba.dissolve('rb').loc[aggreg2anchorreg.aggreg].copy()

        ### Get the county map
        dfcounty = get_countymap(
            agglevel_variables['county_regions'], exclude_water_areas
        )
        dfcounty = dfcounty[['rb', 'NAMELSAD', 'STATE', 'geometry']]

        ## Use the centroid for both the transmission endpoint and centroid
        for prefix in ['', 'centroid_']:
            dfcounty[prefix + 'x'] = dfcounty.geometry.centroid.x
            dfcounty[prefix + 'y'] = dfcounty.geometry.centroid.y

        dfcounty = (
            dfcounty.rename(columns={'NAMELSAD': 'county', 'STCODE': 'st'})
            .set_index('rb')
            .drop(columns=['county'])
        )

        # Combine BA and County
        dfcounty = dfcounty.to_crs(dfba.crs)
        dfba = pd.concat([dfba, dfcounty])

        ### Include all hierarchy levels
        hierarchy = get_hierarchy(case)

        for col in hierarchy:
            dfba[col] = dfba.index.map(hierarchy[col])

    ######## Single Resolution Procedure ########
    else:
        ### Check if resolution is at county level
        if sw.GSw_RegionResolution != 'county':
            hierarchy = get_hierarchy(case, original=True)
            ### Model zones
            dfba = gpd.read_file(
                os.path.join(reeds_path, 'inputs', 'shapefiles', 'US_PCA')
            ).set_index('rb').to_crs(crs)[['geometry']].copy()
            ## Add transmission endpoints
            endpoints = (
                gpd.read_file(
                    os.path.join(reeds_path, 'inputs', 'shapefiles', 'transmission_endpoints')
                )
                .set_index('ba_str')
                .rename(columns={'lon':'node_longitude','lat':'node_latitude'})
                [['node_longitude','node_latitude','geometry']]
            )
            endpoints['x'] = endpoints.centroid.x
            endpoints['y'] = endpoints.centroid.y
            dfba = dfba.merge(endpoints.drop(columns='geometry'), left_index=True, right_index=True)
            ## Add offshore zones (transmission endpoints already included)
            if int(sw.GSw_OffshoreZones):
                offshore_zones = gpd.read_file(
                    os.path.join(reeds_path, 'inputs', 'shapefiles', 'offshore_zones.gpkg')
                ).set_index('zone').to_crs(crs).drop(columns=['zone_old'], errors='ignore')
                ## Get node x/y for consistency with land-based zones
                xy = reeds.plots.df2gdf(
                    offshore_zones.drop(columns='geometry'),
                    lat='node_latitude',
                    lon='node_longitude',
                    crs=crs,
                )
                offshore_zones['x'] = xy.geometry.x
                offshore_zones['y'] = xy.geometry.y
                ## Combine
                dfba = pd.concat([dfba.assign(offshore=0), offshore_zones.assign(offshore=1)])
            ## Filter to regions used in this run
            if 'ba_regions' in agglevel_variables:
                dfba = dfba.loc[(
                    dfba.index.intersection(agglevel_variables['ba_regions'])
                )]
            ## Record centroid locations for plot labels
            dfba['centroid_x'] = dfba.geometry.centroid.x
            dfba['centroid_y'] = dfba.geometry.centroid.y

            if 'aggreg' in agglevel_variables['agglevel']:
                r2aggreg = (
                    pd.read_csv(os.path.join(case, 'inputs_case', 'hierarchy_original.csv'))
                    .rename(columns={'ba': 'r'})
                    .set_index('r')
                    .aggreg
                    )
                ### Take the "anchor" zone as the zone with the largest area [km2]
                dfba['km2'] = dfba.area / 1e6
                ## Add column for new regions
                dfba['aggreg'] = dfba.index.map(r2aggreg)
                ## Take the original zone with largest area
                aggreg2anchorreg = dfba.groupby('aggreg').km2.idxmax().rename('rb')
                ## Save it for plotting
                aggreg2anchorreg.to_csv(os.path.join(case,'inputs_case', 'aggreg2anchorreg.csv'))

        else:
            hierarchy = (
                pd.read_csv(os.path.join(case, 'inputs_case', 'hierarchy.csv'))
                .rename(columns={'*r': 'r', 'ba': 'r'})
                .set_index('r')
            )
            ### Get the county map
            select_counties = agglevel_variables.get('county_regions')
            dfba = get_countymap(select_counties, exclude_water_areas)

            ### Add US state code and drop states outside of CONUS
            state_fips = pd.read_csv(
                os.path.join(reeds_path, 'inputs', 'shapefiles', "state_fips_codes.csv"),
                names=["STATE", "STCODE", "STATEFP", "CONUS"],
                dtype={"STATEFP": "string"},
                header=0,
            )
            state_fips = state_fips.loc[state_fips['CONUS'], :]
            dfba = dfba.merge(state_fips, on="STATEFP")
            dfba = dfba[['rb', 'NAMELSAD', 'STATE_x', 'geometry']].set_index('rb')

            ## Use the centroid for both the transmission endpoint and centroid
            for prefix in ['', 'centroid_']:
                dfba[prefix + 'x'] = dfba.geometry.centroid.x
                dfba[prefix + 'y'] = dfba.geometry.centroid.y

            dfba.rename(columns={'NAMELSAD': 'county', 'STATE_x': 'st'}, inplace=True)

        ### Include all hierarchy levels
        for col in hierarchy:
            dfba[col] = dfba.index.map(hierarchy[col])

    return dfba


def get_dfmap(case=None, levels=None, exclude_water_areas=False):
    """Get dictionary of maps at different hierarchy levels"""
    hierarchy = get_hierarchy(case, original=True).drop(columns=['aggreg'], errors='ignore')
    hierarchy_levels = list(hierarchy.columns)
    if levels:
        hierarchy_levels = [col for col in hierarchy_levels if col in levels]

    mapsfile = os.path.join(str(case), 'inputs_case', 'maps.gpkg')
    if os.path.exists(mapsfile):
        dfmap = {}
        for level in ['r'] + hierarchy_levels:
            dfmap[level] = gpd.read_file(mapsfile, layer=level).rename(columns={'rb': 'r'})
            dfmap[level] = dfmap[level].set_index(dfmap[level].columns[0]).rename_axis(level)
        return dfmap

    dfba = get_zonemap(case, exclude_water_areas)

    dfmap = {'r': dfba.dropna(subset='country').copy()}
    dfmap['r']['centroid_x'] = dfmap['r'].centroid.x
    dfmap['r']['centroid_y'] = dfmap['r'].centroid.y
    for col in hierarchy_levels:
        dfmap[col] = dfba.copy()
        dfmap[col]['geometry'] = dfmap[col].buffer(0.0)
        ## Exclude offshore zones from aggregated regions
        if 'offshore' not in dfmap[col]:
            dfmap[col]['offshore'] = 0
        dfmap[col] = dfmap[col].loc[dfmap[col].offshore == 0].dissolve(col)
        for prefix in ['', 'centroid_']:
            dfmap[col][prefix + 'x'] = dfmap[col].centroid.x
            dfmap[col][prefix + 'y'] = dfmap[col].centroid.y

    return dfmap

def get_disagg_data(case, disagg_variable='population'):
    """
    Get state/region-to-county disaggregation factors for the given variable.
    """
    return pd.read_csv(
        os.path.join(case, 'inputs_case', f'disagg_{disagg_variable}.csv')
    )


def get_co2_storage_sites():
    co2_storage_sites = gpd.read_file(
        os.path.join(
            reeds_path,
            'inputs',
            'shapefiles',
            'ctus_cs_polygons_BVRE.gpkg'
        )
    )
    return co2_storage_sites

def get_h2_storage_sites(h2_storage_type="salt"):
    """
    Read a layer from the H2 storage sites shapefile corresponding to the
    given H2 storage type. H2 storage type options are "salt" and "hardrock".
    """
    h2_storage_sites = gpd.read_file(
        os.path.join(
            reeds_path,
            'inputs',
            'shapefiles',
            'h2_storage_sites.gpkg'
        ),
        layer=h2_storage_type
    )

    return h2_storage_sites


### Read files from a ReEDS case
def read_output(
    case: str,
    filename: str,
    valname: str = None,
    low_memory: bool = False,
    r_filter: list = None,
) -> pd.DataFrame:
    """
    Read a ReEDS output csv file or a key from outputs.h5.
    If outputs.h5 doesn't exist, falls back to outputs/{filename}.csv file.

    Args:
        case: Path to a single ReEDS run folder
            OR path to an outputs.h5 file (used for plotting PCM results)
        filename: Name of a ReEDS output (e.g. 'cap', 'tran_out').
            If filename ends with '.csv', always read the .csv version.
            Otherwise, read the {filename} key from {case}/outputs/outputs.h5.
        valname (optional): If provided, rename 'Value' column to {valname}
        low_memory (optional): If True, reduce memory usage by changing datatypes
        r_filter (optional): List of regions to filter on

    Returns:
        pd.DataFrame
    """
    if case.endswith('.h5'):
        h5path = case
    else:
        h5path = os.path.join(case, 'outputs', 'outputs.h5')
    if os.path.exists(h5path) and not filename.endswith('.csv'):
        key = os.path.basename(filename)
        try:
            with h5py.File(h5path, 'r') as f:
                columns = [i.decode() for i in list(f[key]['columns'])]
                df = pd.DataFrame({col: f[key][col] for col in columns})
            for col in df:
                if df[col].dtype == 'O':
                    df[col] = df[col].str.decode('utf-8')
        except KeyError:
            ## Empty dataframes aren't written to h5 file, so make one ourselves
            e_report_params = pd.read_csv(
                os.path.join(case, 'e_report_params.csv'),
                comment='#',
            )
            _index = e_report_params.loc[
                e_report_params.param.map(lambda x: x.split('(')[0]) == key, 'param'
            ].squeeze()
            if not len(_index):
                raise KeyError(f"{filename} is not in {h5path}")
            index = _index.split('(')[-1].strip(')').split(',')
            df = pd.DataFrame(columns=index + ['Value'])
    else:
        _filename = filename if filename.endswith('.csv') else filename + '.csv'
        df = pd.read_csv(os.path.join(case, 'outputs', _filename))

    df = df.rename(columns={'allh':'h', 'allt':'t', 'eall':'e'})

    ## If desired, change datatypes to reduce memory use
    if low_memory:
        _newtypes = {'Value': np.float32, 't': np.int16}
        newtypes = {col: _newtypes.get(col, 'category') for col in df}
        df = df.astype(newtypes)

    if valname is not None:
        df = df.rename(columns={'Value': valname})

    ## If desired, filter for specific regions
    if r_filter is not None:
        # Only have a r column no rr column
        if 'r' in df.columns and 'rr' not in df.columns:
            df = df[df.r.isin(r_filter)].reset_index(drop=True)

        # Have both r and rr columns. Filter for cases
        # where either r or rr is in the list of regions
        elif 'r' in df.columns and 'rr' in df.columns:
            df = df[df.r.isin(r_filter) | df.rr.isin(r_filter)].reset_index(drop=True)

        else:
            raise ValueError(
                f"The region column was not found for {filename} file, "
                "but a region filter was requested."
            )

    return df


def get_report_sheetmap(case):
    """
    Create a dictionary of report.xlsx fields to excel sheet names
    """
    import openpyxl

    excel = openpyxl.load_workbook(
        os.path.join(case, 'outputs', 'reeds-report', 'report.xlsx'),
        read_only=True,
        keep_links=False,
    )
    sheets = excel.sheetnames
    val2sheet = dict(zip([sheet.split('_', maxsplit=1)[-1] for sheet in sheets], sheets))
    return val2sheet


def read_report(case, sheet=None, val2sheet=None, reportname='reeds-report'):
    """
    Read a ReEDS bokeh report.xlsx.

    Args:
        case: Path to a single ReEDS run folder
        sheet: Name of a sheet from report.xlsx (written by bokeh).
            If sheet is a sheet name (with or without leading number), return that sheet.
            If sheet is None, return a dictionary of all sheets.
        val2sheet: Dictionary produced by get_report_sheetmap(). Keys are sheet names
            without leading numbers; values are full sheet names.
        reportname: directory of bokeh outputs (e.g. 'reeds-report', 'reeds-report-reduced')

    Returns:
        pd.DataFrame (if sheet is not None) else dict of dataframes
    """
    if val2sheet is None:
        val2sheet = get_report_sheetmap(case)
    if sheet is None:
        dfout = {}
        for val, sheet in val2sheet.items():
            dfout[val] = pd.read_excel(
                os.path.join(case, 'outputs', reportname, 'report.xlsx'),
                sheet_name=sheet,
                engine='openpyxl',
            ).drop('scenario', axis=1, errors='ignore')
    else:
        _sheet = val2sheet.get(sheet, sheet)
        dfout = pd.read_excel(
            os.path.join(case, 'outputs', reportname, 'report.xlsx'),
            sheet_name=_sheet,
            engine='openpyxl',
        ).drop('scenario', axis=1, errors='ignore')
    return dfout


def get_param_value(opt_file, param_name, dtype=float, assert_exists=True):
    result = None
    with open(opt_file, mode="r") as f:
        line = f.readline()
        while line:
            if line.startswith(param_name):
                result = line
                break
            line = f.readline()
    if assert_exists:
        assert result, f"{param_name=} not found in {opt_file=}"
    return dtype(result.replace(param_name, "").replace("=", "").strip())


def standardize_case(case=None):
    """Remove inputs_case and trailing directory separator if present"""
    if case is None:
        pass
    elif 'inputs_case' in case:
        case = os.path.dirname(os.path.abspath(case))
    else:
        case = os.path.abspath(case)
    return case


def get_switches(case=None, **kwargs):
    """
    Get pd.Series of switch values from switches.csv, augur_switches.csv,
    and CPLEX opt file.
    Accepts either {case} or {case}/inputs_case as input.

    If {case} is None, the default switch values listed in cases.csv are retrieved.

    If additional keyword arguments are provided, they replace the values specified
    in {case}. This behavior can be used to read all the switches for a case (or all
    the default settings) but change a single switch to a different value (when
    making plots for different input settings, for example). If a key is provided
    that is not a valid switch name, it is ignored.
    """
    case = standardize_case(case)
    ### If no case is provided, return the defaults; otherwise return case-specific values
    if case is None:
        sw = pd.read_csv(
            os.path.join(reeds.io.reeds_path, 'cases.csv'),
            index_col=0,
        )['Default Value']
    else:
        sw = pd.read_csv(
            os.path.join(case, 'inputs_case', 'switches.csv'),
            index_col=0,
            header=None,
        ).squeeze(1)
    ### Augur-specific switches
    try:
        fpath_asw = os.path.join(
            (case if case is not None else reeds_path),
            'ReEDS_Augur', 'augur_switches.csv',
        )
        asw = pd.read_csv(fpath_asw, index_col='key')
        for i, row in asw.iterrows():
            if row['dtype'] == 'list':
                row.value = row.value.split(',')
                try:
                    row.value = [int(i) for i in row.value]
                except ValueError:
                    pass
            elif row['dtype'] == 'boolean':
                row.value = False if row.value.lower() == 'false' else True
            elif row['dtype'] == 'str':
                row.value = str(row.value)
            elif row['dtype'] == 'int':
                row.value = int(row.value)
            elif row['dtype'] == 'float':
                row.value = float(row.value)
        sw = pd.concat([sw, asw.value])
    except FileNotFoundError:
        print(f"{fpath_asw} not found so leaving out Augur switches")
    ### Add derivative switches
    sw['resource_adequacy_years_list'] = [int(y) for y in sw['resource_adequacy_years'].split('_')]
    sw['num_resource_adequacy_years'] = len(sw['resource_adequacy_years_list'])
    ### Get number of threads to use in PRAS
    opt_file = 'cplex.opt' if int(sw.GSw_gopt) == 1 else f'cplex.op{sw.GSw_gopt}'
    try:
        threads = get_param_value(os.path.join(case, opt_file), "threads", dtype=int)
    except (FileNotFoundError, TypeError):
        threads = get_param_value(os.path.join(reeds_path, opt_file), "threads", dtype=int)
    sw['threads'] = threads
    ### Determine whether run is on HPC
    sw['hpc'] = True if int(os.environ.get('REEDS_USE_SLURM', 0)) else False
    ### Add the run location
    sw['casedir'] = case
    sw['reeds_path'] = reeds_path if case is None else os.path.dirname(os.path.dirname(case))
    ### Get the number of hours per period to use in plots
    sw['hoursperperiod'] = {'day': 24, 'wek': 120, 'year': 24}[sw['GSw_HourlyType']]
    sw['periodsperyear'] = {'day': 365, 'wek': 73, 'year': 365}[sw['GSw_HourlyType']]

    for key, value in kwargs.items():
        if key in sw.keys():
            sw[key] = value

    return sw


def get_scalars(case=None, full=False):
    """
    Read the scalars.csv file and return:
        - the full dataframe if full = True
        - a pd.Series if full = False (default)
    """
    if case is None:
        filepath = os.path.join(reeds_path, 'inputs', 'scalars.csv')
    else:
        filepath = os.path.join(standardize_case(case), 'inputs_case', 'scalars.csv')

    if full:
        scalars = pd.read_csv(
            filepath,
            header=None,
            names=['name', 'value', 'comment'],
            index_col='name',
        )
    else:
        scalars = pd.read_csv(
            filepath,
            header=None,
            usecols=[0, 1],
            index_col=0,
        ).squeeze(1)

    return scalars


def read_h5py_file(filename, decode_strings=False):
    """Return dataframe object for a h5py file.

    This function returns a pandas dataframe of a h5py file. If the file has multiple dataset on it
    means it has yearly index.

    Parameters
    ----------
    filename
        File path to read

    Returns
    -------
    pd.DataFrame
        Pandas dataframe of the file
    """

    valid_data_keys = ["data", "cf", "load", "evload"]

    with h5py.File(filename, "r") as f:
        # Identify keys in h5 file and check for overlap with valid key set
        keys = list(f.keys())
        datakey = list(set(keys).intersection(valid_data_keys))

        # Adding safety check to validate that it only returns one key
        assert len(datakey) <= 1, f"Multiple keys={datakey} found for {filename}"
        datakey = datakey[0] if datakey else None

        if datakey in keys:
            # load data
            df = pd.DataFrame(f[datakey][:])
        else:
            df = pd.DataFrame()

        # add columns to data if supplied
        if 'columns' in keys:
            df.columns = (
                pd.Series(f["columns"])
                .map(lambda x: x if isinstance(x, str) else x.decode("utf-8"))
                .values
            )

        # add any index values
        idx_cols = [c for c in keys if re.match('index_[0-9]', c)]
        if len(idx_cols) > 0:
            idx_cols.sort()
            for idx_col in idx_cols:
                df[idx_col] = pd.Series(f[idx_col]).values
                if str(df[idx_col].dtype).startswith('|S') and decode_strings:
                    df[idx_col] = df[idx_col].str.decode('utf-8')
            df = df.set_index(idx_cols)

        # add index and column names if supplied
        if 'index_names' in keys:
            df.index.names = (
                pd.Series(f["index_names"])
                .map(lambda x: x if isinstance(x, str) else x.decode("utf-8"))
                .values
            )
        if 'column_names' in keys:
            df.columns.names = (
                pd.Series(f["column_names"])
                .map(lambda x: x if isinstance(x, str) else x.decode("utf-8"))
                .values
            )

    return df


def read_file(filename, parse_timestamps=False, decode_strings=False):
    """Return dataframe object of input file for multiple file formats.

    This function read multiple file formats for h5 file sand returns a dataframe from the file.

    Parameters
    ----------
    filename
        File path to read

    Returns
    -------
    pd.DataFrame
        Pandas dataframe of the file

    Raises
    ------
    FileNotFoundError
        If the file does not exists
    """
    if isinstance(filename, str):
        filename = Path(filename)

    if not filename.exists():
        raise FileNotFoundError(f"Mandatory file {filename} does not exist.")

    # We have two cases, either the data is contained as a single dataframe or we have multiple
    # datasets that composes the h5 file. For a single dataset we use pandas (since it is the most
    # convenient) and h5py for the custom h5 file.
    try:
        df = read_h5py_file(filename, decode_strings=decode_strings)
    except TypeError:
        df = pd.read_hdf(filename)

    # parse timestamps if specified and if there is a datetime index
    if (
        parse_timestamps
        and ('datetime' in df.index.names)
        and (isinstance(df.index.get_level_values('datetime')[0], bytes))
    ):
        df = decode_h5_timestamps(df)

    # All values being NaN indicates that the region filtering in copy_files.py removed all
    # data, leaving an empty dataframe.
    # Return an empty dataframe with the original file's index if all values are NaN
    if all(df.isnull().all()):
        df = df.drop(columns=df.columns)
        return df

    # NOTE: Some files are saved as float16, so we cast to float32 to prevent issues with
    # large/small numbers
    numeric_cols = [c for c in df if is_float_dtype(df[c].dtype)]
    df = df.astype({column: np.float32 for column in numeric_cols})

    return df


def decode_h5_timestamps(df):
    """
    Decode a dataframe's "datetime" index whose index values are stored as bytes.
    """
    unique_indices = df.index.get_level_values('datetime').unique()
    index2datetime = dict(zip(
        unique_indices,
        pd.to_datetime(unique_indices.str.decode('utf-8'), format='ISO8601')
    ))
    df['datetime'] = df.index.get_level_values('datetime').map(index2datetime)
    if isinstance(df.index, pd.MultiIndex):
        df = df.droplevel('datetime').set_index('datetime', append=True)
    else:
        df = df.set_index('datetime')

    return df


def read_h5_groups(filepath, parse_timestamps=False):
    """
    Read a .h5 file with the following format,
    where r = numrows and c = numcols for each group (r and c can vary across groups):
    - {group1} (attrs: {'index': {indexname}})
        - columns (dtype: str) [1 x c]
        - {column1} [r x 1]
        - {column2} [r x 1] etc.
    - {group2} etc.

    Returns (depends on number of groups):
    - {group: pd.DataFrame [r x c]} if more than one group
    - pd.DataFrame [r x c] if only one group

    Notes:
    - Compatible with reeds.io.write_to_h5()
    - String-formatted columns are automatically decoded; otherwise, types are preserved.
      The resulting dataframe can have mixed types across columns.
    - Only supports single-depth columns and indices.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)
    with h5py.File(filepath, 'r') as f:
        dictout = {}
        for group in f:
            _columns = pd.Index(f[group]['columns']).str.decode('utf-8')
            indexname = f[group].attrs['index']
            index = pd.Index(f[group][indexname], name=indexname)
            columns = [i for i in _columns if i != f[group].attrs['index']]
            _dfout = {}
            for c in columns:
                _dfout[c] = pd.Series(f[group][c])
                if str(_dfout[c].dtype).startswith('|S'):
                    _dfout[c] = _dfout[c].str.decode('utf-8')
            dfout = pd.concat(_dfout, axis=1)
            dfout.index = index
            dfout.columns = columns
            # parse timestamps if specified and if there is a datetime index
            if (
                parse_timestamps
                and ('datetime' in dfout.index.names)
                and (isinstance(dfout.index.get_level_values('datetime')[0], bytes))
            ):
                dfout = decode_h5_timestamps(dfout)

            dictout[group] = dfout
                
        if len(dictout) == 1:
            return dfout
        else:
            return dictout


def read_pras_results(filepath):
    """
    Read a run_pras.jl output file.
    If results are grouped by sample, return a dictionary of dataframes;
    otherwise return a dataframe.
    """
    with h5py.File(filepath, 'r') as f:
        keys = list(f)
        if len(keys):
            ## If all the keys are integers, we have groups labeled by sample
            if all([s.isdigit() for s in keys]):
                df = {}
                for s in keys:
                    skeys = list(f[s])
                    df[int(s)] = pd.concat({c: pd.Series(f[s][c][...]) for c in skeys}, axis=1)
            else:
                df = pd.concat({c: pd.Series(f[c][...]) for c in keys}, axis=1)
        else:
            df = pd.DataFrame()
        return df


def get_temperatures(case, tz_in='UTC', tz_out='Etc/GMT+6', subset_years=True):
    ### Derived inputs
    inputs_case = case if 'inputs_case' in case else os.path.join(case, 'inputs_case')
    h5path = os.path.join(inputs_case, 'temperature_celsius-ba.h5')
    sw = reeds.io.get_switches(inputs_case)
    ## Add one more year on either end of weather years to allow for timezone conversion
    weather_years = sw.resource_adequacy_years_list
    read_years = [min(weather_years) - 1] + weather_years + [max(weather_years) + 1]
    val_ba = (
        pd.read_csv(os.path.join(inputs_case, 'val_ba.csv'), header=None)
        .squeeze(1).values
    )
    ### Load temperatures
    _temperatures = {}
    with h5py.File(h5path, 'r') as f:
        years = read_years if subset_years else [int(i) for i in list(f) if i.isdigit()]
        for year in years:
            timeindex = pd.to_datetime(
                pd.Series(f[f"index_{year}"][:])
                .str.decode('utf-8')
            )
            _temperatures[year] = pd.DataFrame(
                index=timeindex,
                columns=pd.Series(f['columns']).map(lambda x: x.decode()),
                data=f[str(year)],
            )

    temperatures = (
        pd.concat(_temperatures, names=('year','timestamp')).rename_axis(columns='r')
        ## Round to integers for lookup
        .round(0).astype(int)
        .reset_index('year', drop=True)
        .tz_localize(tz_in)
        .tz_convert(tz_out)
        ## Subset to weather years used in ReEDS
        .loc[str(min(weather_years)):str(max(weather_years))]
    )
    ### On leap years, drop Dec 31
    leap_year = temperatures.iloc[:,:1].groupby(temperatures.index.year).count().squeeze(1) == 8784
    for year in weather_years:
        if leap_year[year]:
            temperatures.drop(temperatures.loc[f'{year}-12-31'].index, inplace=True)
    if len(temperatures) != len(weather_years) * 8760:
        raise ValueError(
            f'len(temperatures) = {len(temperatures)} but should be {len(weather_years) * 8760}'
        )
    ### Subset to states used in this run
    temperatures = temperatures[[c for c in temperatures if c in val_ba]].copy()

    return temperatures


def get_outage_hourly(
    case,
    outage_type='forced',
    tz='Etc/GMT+6',
    multilevel=True,
):
    assert outage_type in ['forced', 'scheduled']
    inputs_case = case if 'inputs_case' in case else os.path.join(case, 'inputs_case')
    with h5py.File(os.path.join(inputs_case, f'outage_{outage_type}_hourly.h5'), 'r') as f:
        column_levels = [x.decode() for x in list(f['column_levels'])]
        if multilevel:
            columns = {
                c: pd.Series(f[f'columns_{c}']).map(lambda x: x.decode())
                for c in column_levels
            }
            columns = pd.MultiIndex.from_arrays(list(columns.values()), names=columns.keys())
        else:
            columns = pd.Series(f['columns']).map(lambda x: x.decode())
        dfout = pd.DataFrame(
            index=pd.to_datetime(pd.Series(f['index']).map(lambda x: x.decode())),
            columns=columns,
            data=f['data'],
        ).tz_localize('UTC').tz_convert(tz)
    ## If the columns only have one level, collapse the MultiIndex
    if len(column_levels) == 1:
        dfout.columns = dfout.columns.get_level_values(0)
    return dfout

def get_load_hourly(case=None, **kwargs):
    """
    Get state-level hourly load profiles from the ReEDS directory or
    model region-level hourly load profiles from {case} if {case} is
    provided and {case}/inputs_case/load.h5 exists.
    Accepts either {case} or {case}/inputs_case as input.

    In general, if a switch name/value pair is provided as a keyword
    argument, it replaces the switch value specified in {case}.
    Therefore, the "GSw_LoadProfiles" switch value either specified as a
    keyword argument or specified in {case} determines which load scenario
    is retrieved, with the former taking precedence.    

    If {case} is None and "GSw_LoadProfiles" is not provided,
    the profiles corresponding to the default load
    scenario specified in cases.csv are retrieved.
    """
    if case is None:
        inputs_case = case
        use_cache = False
    else:
        inputs_case = (
            case
            if 'inputs_case' in case
            else os.path.join(case, 'inputs_case')
        )
        h5path = os.path.join(inputs_case, 'load.h5')
        use_cache = os.path.exists(h5path)

    if not use_cache:
        sw = reeds.io.get_switches(inputs_case, **kwargs)
        h5path = os.path.join(
            reeds_path,
            'inputs',
            'load',
            f'{sw.GSw_LoadProfiles}_load_hourly.h5'
        )

    try:
        load_hourly = pd.concat(read_h5_groups(h5path, parse_timestamps=True))
        load_hourly = load_hourly.set_index(
            load_hourly.index.set_levels(
                [int(i) for i in load_hourly.index.levels[0]],
                level=0
            )
            .rename("year", level=0)
        )
    except ValueError:
        load_hourly = read_file(h5path, parse_timestamps=True)

    return load_hourly

def get_historical_state_load_annual():
    """
    Get annual state loads for historical years.
    """
    return pd.read_csv(
        os.path.join(reeds_path, 'inputs', 'load', 'EIA_loadbystate.csv')
    )

def get_years(case):
    return pd.read_csv(
        os.path.join(case, 'inputs_case', 'modeledyears.csv')
    ).columns.astype(int).values


def get_last_iteration(case, year=2050, datum=None, samples=None):
    """Get the last iteration of PRAS for a given case/year"""
    if datum not in [None,'flow','energy']:
        raise ValueError(f"datum must be in [None,'flow','energy'] but is {datum}")
    infile = sorted(glob(
        os.path.join(
            case, 'ReEDS_Augur', 'PRAS',
            f"PRAS_{year}i*"
            + (f'-{samples}' if samples is not None else '')
            + (f'-{datum}' if datum is not None else '')
            + '.h5'
        )
    ))[-1]
    iteration = int(
        os.path.splitext(os.path.basename(infile))[0]
        .split('-')[0].split('_')[1].split('i')[1]
    )
    return infile, iteration


def get_pras_system(case, year=None, iteration='last', verbose=0):
    """
    Read a .pras .h5 file and return a dict of dataframes
    """
    ### Read all the tables in the .pras file
    t = get_years(case)[-1] if year in [0, None, 'last'] else year
    _iteration = (
        get_last_iteration(case, t)[1] if iteration in [None, 'last']
        else iteration
    )
    infile = os.path.join(case, 'ReEDS_Augur', 'PRAS', f"PRAS_{t}i{_iteration}.pras")
    if not os.path.exists(infile):
        raise FileNotFoundError(
            f'{infile} does not exist; run postprocessing/run_reeds2pras.py or rerun '
            'the ReEDS case with keep_augur_files=1'
        )
    pras = {}
    with h5py.File(infile,'r') as f:
        keys = list(f)
        if verbose:
            print(keys)
        vals = {}
        for key in keys:
            vals[key] = list(f[key])
            if verbose:
                print(f"{key}:\n    {','.join(vals[key])}\n")
            for val in vals[key]:
                pras[key,val] = pd.DataFrame(f[key][val][...])
                if verbose:
                    print(f"{key}/{val}: {pras[key,val].shape}")
            if verbose:
                print('\n')

    def get_pras_unit(name):
        unit = name.split('|')[-1]
        try:
            return int(unit)
        except ValueError:
            return 0

    ### Combine into more easily-usable dataframes
    dfpras = {}
    ## Generation and storage
    keys = {
        ## our name: [pras key, pras capacity table name]
        'storcap': ['storages', 'dischargecapacity'],
        'gencap': ['generators', 'capacity'],
        'genfailrate': ['generators', 'failureprobability'],
        'genrepairrate': ['generators', 'repairprobability'],
        'genstorcap': ['generatorstorages', 'gridinjectioncapacity'],
    }
    for key, val in keys.items():
        dfpras[key] = pras[val[0], val[1]]
        dfpras[key].columns = pd.MultiIndex.from_arrays(
            [
                pras[val[0],'_core'].category.str.decode('UTF-8'),
                pras[val[0],'_core'].region.str.decode('UTF-8'),
                pras[val[0],'_core'].name.str.decode('UTF-8').map(get_pras_unit),
                pras[val[0],'_core'].name.str.decode('UTF-8').str.strip('_'),
            ],
            names=['i', 'r', 'unit', 'name'],
        )
        if verbose:
            print(key)
            print(dfpras[key].columns.get_level_values('i').unique())

    ## Transmission (use 'lines' but 'interfaces' should be the same)
    keys = {
        'trans_forward': ['lines', 'forwardcapacity'],
        'trans_backward': ['lines', 'backwardcapacity'],
    }
    for key, val in keys.items():
        dfpras[key] = pras[val[0], val[1]]
        dfpras[key].columns = pd.MultiIndex.from_arrays(
            [
                pras[val[0],'_core'].category.str.decode('UTF-8'),
                pras[val[0],'_core'].region_from.str.decode('UTF-8'),
                pras[val[0],'_core'].region_to.str.decode('UTF-8'),
                pras[val[0],'_core'].name.str.decode('UTF-8'),
            ],
            names=['trtype', 'r', 'rr', 'name'],
        )

    ## Load
    dfpras['load'] = pras['regions','load'].rename(
        columns=pras['regions','_core'].name.str.decode('UTF-8'))

    return dfpras


def get_available_capacity_weighted_cf(case, level='country'):
    """
    Get hourly wind and solar CF and take available-capacity-weighted-average across
    specified region hierarchy level.
    Convert PV from DC CF to AC CF.
    """
    hierarchy = reeds.io.get_hierarchy(case)
    if level in ['r', 'rb', 'ba']:
        r2region = dict(zip(hierarchy.index, hierarchy.index))
    else:
        r2region = hierarchy[level]
    ## Get available capacity from supply curves
    sc = {
        i: pd.read_csv(
            os.path.join(case, 'inputs_case', f'supplycurve_{i}.csv')
        ).groupby(['region', 'class'], as_index=False).capacity.sum()
        for i in ['upv', 'wind-ons', 'wind-ofs']
    }
    sc = (
        pd.concat(sc, names=['tech', 'drop'], axis=0)
        .reset_index(level='drop', drop=True).reset_index()
    )
    sc['i'] = sc.tech+'_'+sc['class'].astype(str)
    sc['resource'] = sc.i + '|' + sc.region
    sc['aggreg'] = sc.region.map(r2region)
    ## Get CF
    recf = reeds.io.read_file(
        os.path.join(case, 'inputs_case', 'recf.h5'),
        parse_timestamps=True,
    )
    ## CF * cap / cap = available-capacity-weighted-average CF
    recapcf = (recf * sc.set_index('resource')['capacity']).dropna(axis=1, how='all')
    recapcf.columns = pd.MultiIndex.from_arrays([
        recapcf.columns.map(lambda x: x.split('|')[0].strip('_0123456789')),
        recapcf.columns.map(lambda x: r2region[x.split('|')[1]]),
    ], names=['i', 'r'])
    dfout = (
        recapcf.groupby(['i','r'], axis=1).sum()
        / sc.groupby(['tech','aggreg']).capacity.sum().rename_axis(['i','r'])
    )
    ## UPV is AC_out/DC_cap = CF_DC, so multiply by ILR to get CF_AC
    scalars = reeds.io.get_scalars(case)
    dfout['upv'] *= scalars.ilr_utility

    return dfout


def get_sitemap(offshore=False, geo=True):
    """
    Get mapping from sc_point_gid to geographic points and counties.
    """
    fpath = os.path.join(
        reeds_path, 'inputs', 'supply_curve',
        'interconnection_offshore.h5' if offshore else 'interconnection_land.h5'
    )
    sitemap = read_h5_groups(fpath)[
        ['latitude', 'longitude', 'FIPS']
        + (['ba', 'always_radial'] if offshore else [])
    ]
    if geo:
        crs = 'EPSG:5070' if offshore else 'ESRI:102008'
        sitemap = reeds.plots.df2gdf(sitemap, crs=crs)
    return sitemap


def assemble_supplycurve(scfile=None, case=None, drop_extra=True, agg=True, skip_if_complete=False):
    """
    Join on sc_point_gid column:
    - Generator supply curve (indicated by scfile input)
    - County FIPS code and model zone
    - Interconnection costs and distances

    Returns: pd.DataFrame with sc_point_gid index

    Notes:
    - Does not adjust dollar years. Interconnection costs use the dollar year specified by the
    'dollaryear' attribute in the interconnection cost file; capital adders use the tech-specific
    dollar year from the supply curve data folder. If these don't match, supply_curve_cost_per_mw
    will be ill-defined.

    Inputs for testing:
    scfile = os.path.join(reeds_path, 'inputs', 'supply_curve', 'supplycurve_upv-reference.csv')
    scfile = os.path.join(reeds_path, 'inputs', 'supply_curve', 'supplycurve_wind-ofs-reference.csv')
    """
    ### Parse inputs
    sw = get_switches(case)
    if scfile is None:
        offshore = False
    else:
        offshore = (
            True if ('wind-ofs' in os.path.basename(scfile)) or (scfile == 'offshore')
            else False
        )
    ### Get interconnection cost
    fpath_interconnection = os.path.join(
        reeds_path, 'inputs', 'supply_curve',
        ('interconnection_offshore.h5' if offshore else 'interconnection_land.h5')
    )
    interconnection_cost = reeds.io.read_h5_groups(fpath_interconnection)
    if scfile is None:
        return interconnection_cost

    ### Get supply curve
    dfin = pd.read_csv(scfile, index_col='sc_point_gid')
    ## If derived columns are already in file, it's already been assembled, so stop here
    if 'supply_curve_cost_per_mw' in dfin:
        ## Rebuild it if not aggregating
        if skip_if_complete:
            return dfin
        else:
            dfin = dfin[['class', 'capacity', 'capital_adder_per_mw']].copy()

    county2zone = reeds.io.get_county2zone(case if agg else None)

    ### Combine
    dfout = dfin.copy()
    dfout = dfout.merge(interconnection_cost, how='left', left_index=True, right_index=True)
    dfout['region'] = dfout.FIPS.map(county2zone)
    ## Keep either meshed or radial data for offshore
    if offshore:
        keep = '|meshed' if int(sw.GSw_OffshoreZones) else '|radial'
        drop = '|radial' if int(sw.GSw_OffshoreZones) else '|meshed'

        cols_keep = [c for c in dfout if c.endswith(keep)]
        cols_drop = [c for c in dfout if c.endswith(drop)]

        dfout = (
            dfout
            .drop(columns=cols_drop)
            .rename(columns={c: c.replace(keep,'') for c in cols_keep})
        )
        if int(sw.GSw_OffshoreZones):
            offshore_zones = dfout.always_radial == 0
            dfout.loc[offshore_zones, 'region'] = dfout.loc[offshore_zones, 'ba'].copy()
        else:
            dfout['ba'] = dfout['region'].copy()

    ## Drop reinforcement cost for counties
    if case is not None:
        agglevel_variables = reeds.spatial.get_agglevel_variables(
            reeds_path, os.path.join(case, 'inputs_case')
        )
        counties = agglevel_variables['county_regions']
    else:
        counties = []
    if len(counties):
        zerocols = ['cost_reinforcement_usd_per_mw', 'dist_reinforcement_km']
        dfout.loc[dfout.region.isin(counties), zerocols] = 0
        dfout.loc[dfout.region.isin(counties), 'cost_total_trans_usd_per_mw'] = dfout.loc[
            dfout.region.isin(counties),
            ['cost_spur_usd_per_mw', 'cost_poi_usd_per_mw']
        ].sum(axis=1)
    ## Supply curve cost includes generation capex adder plus interconnection cost
    dfout['supply_curve_cost_per_mw'] = dfout[[
        'capital_adder_per_mw',
        'cost_total_trans_usd_per_mw',
    ]].sum(axis=1)

    if drop_extra:
        dfout = dfout.drop(
            columns=[
                'latitude',
                'longitude',
                'latitude_poi',
                'longitude_poi',
                'latitude_reinforcement_poi',
                'longitude_reinforcement_poi',
                'trans_gid',
                'trans_type',
                'node_latitude',
                'node_longitude',
                'always_radial',
                'ba',
            ],
            errors='ignore',
        )
    return dfout


def assemble_exog_cap(exogpath, case=None):
    """
    Join on sc_point_gid column:
    - Exogenous capacity (indicated by exogpath input)
    - Model zone

    Returns: pd.DataFrame with [*tech, region, year, sc_point_gid] index and capacity data

    Inputs for testing:
    exogpath = os.path.join(reeds_path, 'inputs', 'capacity_exogenous', 'exog_cap_upv_reference.csv')
    """
    ## Get inputs
    dfin = pd.read_csv(exogpath, index_col='sc_point_gid')
    offshore = True if 'wind-ofs' in os.path.basename(exogpath) else False
    sitemap = get_sitemap(offshore=offshore, geo=False)
    county2zone = reeds.io.get_county2zone(case)
    ## Add region column
    dfout = dfin.copy()
    dfout['region'] = dfin.index.map(sitemap.FIPS).map(county2zone)
    ## Drop nulls because they represent capacity outside the model area (since not in county2zone)
    dfout = dfout.dropna(subset='region')
    return dfout.reset_index()[['*tech','region','year','sc_point_gid','capacity']]


#   ##      ## ########  #### ######## ########
#   ##  ##  ## ##     ##  ##     ##    ##
#   ##  ##  ## ##     ##  ##     ##    ##
#   ##  ##  ## ########   ##     ##    ######
#   ##  ##  ## ##   ##    ##     ##    ##
#   ##  ##  ## ##    ##   ##     ##    ##
#    ###  ###  ##     ## ####    ##    ########


### Write files
def get_dtype(col, df=None):
    if col.lower() == "value":
        return np.float32
    elif col in ["t", "allt"]:
        return np.uint16
    else:
        maxlength = df[col].str.len().max()
        return f"S{maxlength}"


def make_columns_unique(df):
    """
    Rename columns in place to avoid duplicates.
    Example: [*,*,r,*,t,Value] becomes [*,*.1,r,*.2,t,Value].
    """
    duplicated = df.columns.duplicated()
    if any(duplicated):
        columns_old = df.columns
        columns_new = []
        times_used = {}
        for i, column in enumerate(columns_old):
            if not duplicated[i]:
                columns_new.append(column)
            else:
                times_used[column] = times_used.get(column, 1)
                columns_new.append(f'{column}.{times_used[column]}')
                times_used[column] += 1
        df.columns = columns_new


def write_to_h5(
    dfwrite,
    key,
    filepath,
    attrs={},
    overwrite=False,
    compression='gzip',
    compression_opts=4,
    **kwargs,
):
    """ """
    with h5py.File(filepath, 'a') as f:
        if key in list(f):
            if overwrite:
                del f[key]
            else:
                raise ValueError(f'{key} is already used in {filepath}')

        group = f.create_group(key)
        ## Write columns to maintain order
        group.create_dataset(
            'columns',
            data=dfwrite.columns,
            dtype=f"S{dfwrite.columns.str.len().max()}",
        )
        if len(attrs):
            for key, val in attrs.items():
                group.attrs[key] = val
        ## Write data
        if len(dfwrite):
            for col in dfwrite:
                if col in ['datetime', 'timestamp']:
                    dtype = 'S30'
                    data = dfwrite[col].astype(str).str.encode('utf-8')
                else:
                    data = dfwrite[col]
                    dtype = (
                        f"S{data.str.len().max()}"
                        if dfwrite.dtypes[col] == 'O'
                        else dfwrite.dtypes[col]
                    )

                group.create_dataset(
                    col,
                    data=data,
                    dtype=dtype,
                    compression=compression,
                    compression_opts=compression_opts,
                    **kwargs,
                )


def write_output_to_h5(
    df,
    key,
    filepath,
    drop_ctypes=False,
    verbose=0,
    **kwargs,
):
    """
    Write a dataframe of GAMS outputs to a .h5 file.
    This function only works for long dataframes where the single column
    of numeric data is named "Value".
    A group of name {key} is created in the .h5 file at {filepath} and each column
    in {df} is written to its own dataset.
    String columns need to be decoded when read.
    """
    dfwrite = df.copy()
    if not len(dfwrite):
        if verbose:
            print(f'{key} dataframe is empty, so it was not written to {filepath}')
        return dfwrite
    ## Sets have `c_bool(True)` as the value for every entry, so just
    ## drop the Value column if it's a set
    if drop_ctypes and ("Value" in dfwrite) and isinstance(dfwrite.Value.values[0], ctypes.c_bool):
        dfwrite.drop("Value", axis=1, inplace=True)
    ## Make column names unique (necessary if '*' is overused)
    make_columns_unique(dfwrite)
    ## Normalize column data types
    dfwrite = dfwrite.astype({col: get_dtype(col, dfwrite) for col in dfwrite})
    ### Write to .h5 file
    write_to_h5(dfwrite, key, filepath, **kwargs)

    return dfwrite


def write_profile_to_h5(df, filename, outfolder, compression_opts=4):
    """Writes dataframe to h5py file format used by ReEDS. Used in ReEDS and hourlize

    This function takes a pandas dataframe and saves to a h5py file. Data is saved to h5 file as follows:
        - the data itself is saved to a dataset named "data"
        - column names are saved to a dataset named "columns"
        - the index of the data is saved to a dataset named "index"; in the case of a multindex,
          each index is saved to a separate dataset with the format "index_{index order}"
        - the names of the index (or multindex) are saved to a dataset named "index_names"

    Parameters
    ----------
    df
        pandas dataframe to save to h5
    filename
        Name of h5 file
    outfolder
        Path to folder to save the file (in ReEDS this is usually the inputs_case folder)

    Returns
    -------
    None
    """
    outfile = os.path.join(outfolder, filename)
    with h5py.File(outfile, 'w') as f:
        # save index or multi-index in the format 'index_{index order}')
        for i in range(df.index.nlevels):
            # get values for specified index level
            indexvals = df.index.get_level_values(i)
            # save index
            if isinstance(indexvals[0], bytes):
                # if already formatted as bytes keep that way
                f.create_dataset(f'index_{i}', data=indexvals, dtype='S30')
            elif indexvals.name in ['datetime', 'timestamp']:
                # if we have a formatted datetime index that isn't bytes, save as such
                timeindex = (
                    indexvals.to_series().apply(datetime.datetime.isoformat).reset_index(drop=True)
                )
                f.create_dataset(f'index_{i}', data=timeindex.str.encode('utf-8'), dtype='S30')
            elif indexvals.dtype == 'O':
                f.create_dataset(f'index_{i}', data=indexvals, dtype=f'S{indexvals.map(len).max()}')
            else:
                # Other indices can be saved using their data type
                f.create_dataset(f'index_{i}', data=indexvals, dtype=indexvals.dtype)

        # save index and column names
        index_names = pd.Index(df.index.names)
        if len(index_names):
            f.create_dataset(
                'index_names', data=index_names, dtype=f'S{index_names.map(len).max()}'
            )

        column_names = pd.Index(df.columns.names)
        if len(column_names) and not all([i is None for i in column_names]):
            f.create_dataset(
                'column_names',
                data=column_names.map(lambda x: {None:''}.get(x,x)),
                dtype=f'S{column_names.map(len).max()}',
            )

        # save column names as string type
        if len(df.columns):
            f.create_dataset('columns', data=df.columns, dtype=f'S{df.columns.map(len).max()}')

        # save data if it exists
        if df.empty:
            pass
        elif len(df.dtypes.unique()) == 1:
            dtype = df.dtypes.unique()[0]
            f.create_dataset(
                'data',
                data=df.values,
                dtype=dtype,
                compression='gzip',
                compression_opts=compression_opts,
            )
        else:
            types = df.dtypes.unique()
            print(df)
            raise ValueError(f"{outfile} can only contain one datatype but it contains {types}")

        return df


def write_gswitches(sw_df: pd.DataFrame, inputs_case: str) -> str:
    """
    Write GAMS switches by filtering those that start with 'GSw' and have a numeric value.
    Converts the filtered switches to a CSV and saves it in the inputs_case directory.

    Args:
        sw_df (pd.DataFrame): A DataFrame with the switches.
        inputs_case (str): The path to the inputs case directory.

    Returns:
        str: The path to the generated CSV file.
    """
    switches = sw_df.squeeze()

    def is_numeric(val):
        try:
            float(val)
            return '_' not in str(val)
        except (ValueError, TypeError):
            return False

    gswitches = switches.loc[
        switches.index.str.lower().str.startswith('gsw') & switches.map(is_numeric)
    ].copy()

    # Change 'GSw' to 'Sw' by removing the initial 'G'
    gswitches.index = gswitches.index.map(lambda x: x[1:])

    # Add a 'comment' column and save to CSV
    csv_path = os.path.join(inputs_case, 'gswitches.csv')
    gswitches.reset_index().assign(comment='').to_csv(
        csv_path, header=False, index=False)

    return csv_path
