import os
import sys
import pandas as pd
import geopandas as gpd
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import reeds


def get_agglevel_variables(reeds_path, inputs_case):
    '''
    This function produces a dictionary with an assortment of variables that are necessary for
    mixed resolution runs.

    ReEDS supports multiple agglevels
    The 'lvl' variable is set to 'mult' for instances where county is included as a desired resolution.
    This ensures that both BA and county data are copied to the inputs_case folder
    The 'lvl' variable also ensures that BA and larger spatial aggregations use BA data and procedure

    ###### variables output by function:   #######
    lvl - indicator if one of the desired resolutions in a mixed resolution run is county or not
    agglevel - single or multiple values to indicate resolution(s)
    ba_regions - list of regions in a mixed resolution run that use BA resolution data
    county_regions - list of regions in a mixed resolution run that use county resolution data
    county_regions2ba - map county resolution regions to their BA
    BA_county_list - list of counties that belong to regions being solved at BA
    BA_2_county - map counties that belong to BA resolution regions back to their BA
    ba_transgrp - list of transgroups associated with regions being solved at ba resolution
    county_transgrp - list of transgroups associated with regions being solved at ba resolution

    '''

    agglevel = pd.read_csv(os.path.join(inputs_case, 'agglevels.csv'))

    if len(agglevel) > 1:
        agglevel = agglevel.squeeze().tolist()
    else:
        agglevel = agglevel.squeeze().split()

    # Compile lists of regions in the run to be considered at ba level
    hierarchy = pd.read_csv(
        os.path.join(inputs_case, 'hierarchy_with_res.csv'), usecols=['*r', 'resolution']
    )
    hierarchy_org = pd.read_csv(os.path.join(inputs_case, 'hierarchy_original.csv'))
    rb_aggreg = pd.read_csv(os.path.join(inputs_case, 'rb_aggreg.csv'))
    ba_regions = hierarchy[hierarchy['resolution'] == 'ba']['*r'].to_list()
    aggreg_regions = hierarchy[hierarchy['resolution'] == 'aggreg']['*r'].to_list()
    aggreg_regions2ba = hierarchy_org[hierarchy_org['aggreg'].isin(aggreg_regions)]['ba'].to_list()
    ba_regions = list(set(ba_regions + aggreg_regions + aggreg_regions2ba))
    transgrp_regions_ba = list(set(hierarchy_org[hierarchy_org['ba'].isin(ba_regions)]['transgrp']))

    ### Procedure for handling mixed-resolution ReEDS runs
    if len(agglevel) > 1:
        if 'county' in agglevel:
            lvl = 'mult'
        else:
            lvl = 'ba'

        # Create dictionaries which map county resolution regions to their BAs and which map
        # the counties of BA resolution regions to their BA
        # These lists/dictionaries are necessary to filter county and BA resolution data correctly

        if 'county' in agglevel:
            county_regions = hierarchy[hierarchy['resolution'] == 'county']['*r'].to_list()
            r_ba = pd.read_csv(os.path.join(inputs_case, 'r_ba.csv'))
            r_ba_dict = r_ba.set_index('r')['ba'].to_dict()
            # List of BAs associated with county resolution regions
            county_regions2ba = pd.DataFrame(county_regions)[0].map(r_ba_dict).unique().tolist()
            # Need list of transgrps associated with regions being solved at county resolution
            transgrp_regions_county = list(
                set(hierarchy_org[hierarchy_org['ba'].isin(county_regions2ba)]['transgrp'])
            )
            # Need county2zone
            county2zone = pd.read_csv(os.path.join(reeds_path, 'inputs', 'county2zone.csv'))
            county2zone['FIPS'] = county2zone['FIPS'].astype(str).str.zfill(5)
            # Need to create mapping between aggreg and county
            if 'aggreg' in agglevel:
                county2zone = county2zone[county2zone['ba'].isin(rb_aggreg['ba'])]
                county2zone['ba'] = county2zone['ba'].map(
                    rb_aggreg.set_index('ba')['aggreg'].to_dict()
                )
                # Add BAs associated with aggreg regions to ba_regions list
                aggreg_regions_2_ba = [
                    x
                    for x in rb_aggreg['ba']
                    if x not in aggreg_regions and x not in county_regions2ba
                ]
                ba_regions = list(set(ba_regions + aggreg_regions_2_ba))
            # Create list of counties that belong to regions being solved at BA
            BA_county_list = county2zone[county2zone['ba'].isin(ba_regions)].copy()
            BA_county_list.loc[:,'FIPS'] = 'p' + BA_county_list['FIPS'].astype(str)
            # Map these counties to their BA
            BA_2_county = BA_county_list.set_index('FIPS')['ba'].to_dict()
            BA_county_list = BA_county_list['FIPS'].tolist()

    ### Procedure for handling single-resolution ReEDS runs
    else:
        agglevel = agglevel[0]
        lvl = 'ba' if agglevel in ['ba', 'aggreg'] else 'county'

        if lvl == 'county':
            county_regions = hierarchy[hierarchy['resolution'] == 'county']['*r'].to_list()
            r_ba = pd.read_csv(os.path.join(inputs_case, 'r_ba.csv'))
            r_ba_dict = r_ba.set_index('r')['ba'].to_dict()
            # List of BAs associated with county resolution regions
            county_regions2ba = pd.DataFrame(county_regions)[0].map(r_ba_dict).unique().tolist()
            transgrp_regions_county = list(
                set(hierarchy_org[hierarchy_org['ba'].isin(county_regions2ba)]['transgrp'])
            )

        else:
            county_regions = []
            county_regions2ba = []
            transgrp_regions_county = []

        BA_county_list = []
        BA_2_county = []

    return {
        'lvl': lvl,
        'agglevel': agglevel,
        'ba_regions': ba_regions,
        'county_regions': county_regions,
        'county_regions2ba': county_regions2ba,
        'BA_county_list': BA_county_list,
        'BA_2_county': BA_2_county,
        'ba_transgrp': transgrp_regions_ba,
        'county_transgrp': transgrp_regions_county,
    }


def assign_to_offshore_zones(unitdata):
    """Map offshore wind units to offshore zones based on lat/lon and zone outlines"""
    ### Get offshore zones
    dfzones = gpd.read_file(
        os.path.join(reeds.io.reeds_path, 'inputs', 'shapefiles', 'offshore_zones.gpkg')
    ).set_index('zone')

    dfwind = unitdata.loc[unitdata.tech=='wind-ofs'].copy()
    dfwind['latitude'] = dfwind['T_LAT'].abs()
    dfwind['longitude'] = -dfwind['T_LONG'].abs()
    dfwind = reeds.plots.df2gdf(dfwind, crs=dfzones.crs)

    ## Only keep matches within 100 km since some areas only have radial sites
    index2offshorezone = dfwind.sjoin_nearest(dfzones, max_distance=1e5)['index_right']

    dfout = unitdata.copy()
    dfout.loc[index2offshorezone.index, 'reeds_ba'] = index2offshorezone.values

    return dfout


def get_map(resolution='county', source='tiger', crs='ESRI:102008'):
    """
    Download (if necessary) and read a U.S. map.

    Parent URL:
    https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
    or
    https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
    """
    urls = {
        'county': (
            'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_county_500k.zip'
            if source.lower() == 'census' else
            'https://www2.census.gov/geo/tiger/TIGER2022/COUNTY/tl_2022_us_county.zip'
        ),
        'country': 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_nation_5m.zip',
        'state': (
            'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_500k.zip'
            if source.lower() == 'census' else
            'https://www2.census.gov/geo/tiger/TIGER2025/STATE/tl_2025_us_state.zip'
        ),
        'urban': 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_ua10_500k.zip',
    }
    index = {
        'state': 'STUSPS',
        'country': 'GEOID',
        'county': 'GEOID',
        'urban': 'GEOID10',
    }
    drop = {
        'state': {'STUSPS': ['AK', 'AS', 'HI', 'VI', 'PR', 'MP', 'GU']},
        'county': {'STATEFP': ['02', '60', '15', '78', '72', '69', '66']}
    }
    aliases = {
        'state': ['st', 'states'],
        'county': ['counties', 'fips'],
        'country': ['nation', 'usa', 'u.s.a.'],
        'urban': ['city', 'cities'],
    }
    for key, val in aliases.items():
        for v in val:
            urls[v] = urls[key]
            if key in index:
                index[v] = index[key]
            if key in drop:
                drop[v] = drop[key]

    ## Parse and load it
    url = urls[resolution.lower()]
    cachepath = Path(reeds.io.reeds_path, 'inputs', 'shapefiles', 'cache')
    cachepath.mkdir(exist_ok=True, parents=True)
    fpath = Path(cachepath, Path(url).stem)
    try:
        df = gpd.read_file(fpath)
    except Exception:
        reeds.remote.download(url, fpath, unzip=True)
        df = gpd.read_file(fpath)
    df = df.to_crs(crs)
    ## Downselect if necessary
    for key, val in drop.get(resolution, {}).items():
        df = df.loc[~df[key].isin(val)].copy()
    if resolution in index:
        df = df.set_index(index[resolution]).copy()

    return df
