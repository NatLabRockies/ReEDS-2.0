"""
Patrick.Brown@nrel.gov 20210520
"""

###############
#%% IMPORTS ###
import os
import pandas as pd
import numpy as np
import geopandas as gpd
import shapely
from tqdm import tqdm, trange
### Set up projection environment - needed for geopandas
os.environ['PROJ_NETWORK'] = 'OFF'
pd.options.display.max_rows = 20
pd.options.display.max_columns = 200

##############
#%% INPUTS ###
### Indicate whether to run for offshore
offshore, scen_base = False, 'upv_open'
# offshore, scen_base = True, 'windofs_open'
### Filepaths
if os.name == 'posix':
    scpath = '/Volumes/ReEDS/Supply_Curve_Data/'
else:
    scpath = '//nrelnas01/ReEDS/Supply_Curve_Data/'
### Get the ReEDS-2.0 path from this file's path (ReEDS-2.0/hourlize/rev-site-aggregation.py)
reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
outpath = os.path.join(reeds_path,'inputs','supplycurvedata')

### Indicate the scenarios to use
scpaths = pd.read_csv(
    os.path.join(reeds_path,'inputs','supplycurvedata','metadata','rev_paths.csv'),
    index_col=['tech','access_case'],
)
scens = {
    'windons_ref': os.path.join(scpath,scpaths.loc[('wind-ons','reference'),'sc_file']),
    'windons_lim': os.path.join(scpath,scpaths.loc[('wind-ons','limited'),'sc_file']),
    # 'windons_open': os.path.join(scpath,scpaths.loc[('wind-ons','open'),'sc_file']),
    'upv_ref': os.path.join(scpath,scpaths.loc[('upv','reference'),'sc_file']),
    'upv_lim': os.path.join(scpath,scpaths.loc[('upv','limited'),'sc_file']),
    'upv_open': os.path.join(scpath,scpaths.loc[('upv','open'),'sc_file']),
    'windofs_open': os.path.join(scpath,scpaths.loc[('wind-ofs','open'),'sc_file']),
    'windofs_lim': os.path.join(scpath,scpaths.loc[('wind-ofs','limited'),'sc_file']),
}
scens_use = ([i for i in scens.keys() if 'ofs' in i] if offshore
             else [i for i in scens.keys() if 'ofs' not in i])
print(scens_use)

### reV projection string
### (https://spatialreference.org/ref/esri/north-america-albers-equal-area-conic/)
projstring = 'ESRI:102008'

#################
#%% PROCEDURE ###

#%% Get full site-to-fips map
cols = ['sc_point_gid','state','county','cnty_fips','longitude','latitude']
dfkey = pd.read_csv(scens[scen_base], usecols=cols,)
print(scen_base + ' has ' + str(len(dfkey)) + ' sc_point_gids.')
for scen in tqdm([i for i in scens_use if i != scen_base]):
    dfcase = pd.read_csv(scens[scen], usecols=cols)
    #select only those rows where sc_point_gid is not in original
    dfcase = dfcase[~dfcase['sc_point_gid'].isin(dfkey['sc_point_gid'])].copy()
    print(scen + ' added ' + str(len(dfcase)) + ' more sc_point_gids.')
    dfkey = pd.concat([dfkey, dfcase])

dfkey = dfkey.set_index('sc_point_gid')
dfkey.cnty_fips = dfkey.cnty_fips.map(lambda x: '{:0>5}'.format(int(x)))

### Update to Oglala Lakota county, SD
dfkey.cnty_fips = dfkey.cnty_fips.replace('46113','46102')
dfkey.loc[dfkey.cnty_fips == '46102','county'] = 'Oglala Lakota'

#%% Get ReEDS regions from county map
reedsmap = pd.read_csv(
    os.path.join(reeds_path,'hourlize','inputs','resource','county_map.csv'),
)
reedsmap.cnty_fips = reedsmap.cnty_fips.map(lambda x: '{:0>5}'.format(int(x)))
reedsmap = reedsmap.set_index('cnty_fips')

#%% Map reV points to BAs
dfkey['rb'] = dfkey.cnty_fips.map(reedsmap.reeds_ba)

#%%### Write it
dfwrite = dfkey.copy()
dfwrite.latitude = dfwrite.latitude.astype(float).round(4)
dfwrite.longitude = dfwrite.longitude.astype(float).round(4)
### Save it
dfwrite[['latitude','longitude','state','county','cnty_fips','rb']].to_csv(
    os.path.join(outpath,'sitemap{}.csv'.format('_offshore' if offshore else ''))
)
