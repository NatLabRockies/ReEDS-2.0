"""
The purpose of this script is to gather individual generator data from the
NEMS generator database and organize this data into various categories, such as:
    - Non-RSC Existing Capacity
    - Non-RSC Prescribed Capacity
    - RSC Existing Capacity
    - RSC Prescribed Capacity
    - Retirement Data
        - Generator Retirements
        - Wind Retirements
        - Non-RSC Retirements
    - Hydro Capacity Factors
The categorized datasets are then written out to various csv files for use
throughout the ReEDS model.

Some notes on the NEMS database:
* Capacity is assumed to retire at the BEGINNING of 'RetireYear'. So if a row's
  'RetireYear' is 2015, that capacity is assumed to retire at 2014-12-31T23:59:59.
"""

#%% IMPORTS
import pandas as pd
import os
import argparse
import numpy as np
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()
pd.options.display.max_columns = 200

#%% Fixed inputs
# Start year for ReEDS prescriptive builds (default: 2010):
Sw_startyear = 2010
# Generator database column seletions:
Sw_onlineyearcol = 'StartYear'

#%% Model Inputs
parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")
parser.add_argument("reeds_path", help="ReEDS directory")
parser.add_argument("inputs_case", help="path to runs/{case}/inputs_case")

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

#%% Testing inputs
# reeds_path = os.path.expanduser('~/github/ReEDS-2.0')
# reeds_path = os.getcwd()
# reeds_path = os.path.join('D:\\','Vincent','ReEDS-2.0')
# inputs_case = os.path.join(
#     reeds_path,'runs','hydroupdate_update_Pacific','inputs_case')

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
scalars = pd.read_csv(
    os.path.join(inputs_case, 'scalars.csv'),
    header=None, usecols=[0,1], index_col=0, squeeze=True)

unitdata = sw.unitdata
retscen = sw.retscen
GSw_WaterMain = int(sw.GSw_WaterMain)
GSw_DUPV = int(sw.GSw_DUPV)

#%% Functions
season2szn = {'spring':'spri','summer':'summ','fall':'fall','winter':'wint'}

val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'), squeeze=True, header=None).tolist()
years = pd.read_csv(os.path.join(inputs_case,'modeledyears.csv')).columns.astype(int).values

r_col = 'reeds_ba'

##=================================
#   --- Supplemental Data ---
#==================================
## Dictionaries ------------------
TECH = {
    'capnonrsc': [
        'coaloldscr', 'coalolduns', 'biopower', 'coal-igcc',
        'coal-new', 'gas-cc', 'gas-ct', 'geothermal', 'lfill-gas',
        'nuclear', 'o-g-s', 'battery_2', 'battery_4', 'battery_6',
        'battery_8', 'battery_10', 'pumped-hydro',
    ],
    'prescribed_nonRSC': [
        'coal-new', 'lfill-gas', 'gas-ct', 'o-g-s', 'gas-cc', 
        'hydED', 'hydEND', 'hydND', 'hydNPND', 'hydUD', 'hydUND',
        'geothermal', 'biopower', 'coal-igcc', 'nuclear',
        'battery_2', 'battery_4', 'battery_6', 'battery_8', 'battery_10', 'pumped-hydro',
        'coaloldscr',
    ],
    'storage': [
        'battery_2', 'battery_4', 'battery_6', 'battery_8', 'battery_10', 'pumped-hydro',
    ],
    'rsc_all': ['dupv','upv','pvb','csp-ns'],
    'rsc_csp': ['csp-ns'],
    'rsc_wsc': ['dupv','upv','pvb','csp-ns','csp-ws','wind-ons','wind-ofs'],
    'prsc_all': ['dupv','upv','pvb','csp-ns','csp-ws'],
    'prsc_upv': ['dupv','upv','pvb'],
    'prsc_w': ['wind-ons','wind-ofs'],
    'prsc_csp': ['csp-ns','csp-ws'],
    'retirements': [
        'coalolduns', 'o-g-s', 'hydED', 'hydEND', 'gas-ct', 'lfill-gas',
        'coaloldscr', 'biopower', 'gas-cc', 'coal-new',
        'battery_2','nuclear', 'pumped-hydro', 'coal-igcc',
    ],
    'windret': ['wind-ons'],
    # This is not all technologies that do not having cooling, but technologies
    # that are (or could be) in the plant database.
    'no_cooling': [
        'dupv', 'upv', 'pvb', 'gas-ct', 'geothermal',
        'battery_2', 'battery_4', 'battery_6', 'battery_8',
        'battery_10', 'pumped-hydro', 'pumped-hydro-flex', 'hydUD',
        'hydUND', 'hydD', 'hydND', 'hydSD', 'hydSND', 'hydNPD',
        'hydNPND', 'hydED', 'hydEND', 'wind-ons', 'wind-ofs', 'caes',
    ],
}
COLNAMES = {
    'capnonrsc': (
        ['tech','coolingwatertech',r_col,'ctt','wst','cap'],
        ['i','coolingwatertech','r','ctt','wst','value']
    ),
    'prescribed_nonRSC': (
        [Sw_onlineyearcol,r_col,'tech','coolingwatertech','ctt','wst','cap'],
        ['t','r','i','coolingwatertech','ctt','wst','value']
    ),
    'rsc': (
        ['tech',r_col,'ctt','wst','cap'],
        ['i','r','ctt','wst','value']
    ),
    'rsc_wsc': (
        [r_col,'tech','cap'],
        ['r','i','value']
    ),
    'prsc_upv': (
        [Sw_onlineyearcol,r_col,'tech','cap'],
        ['t','r','i','value']
    ),
    'prsc_w': (
        [Sw_onlineyearcol,r_col,'tech','cap'],
        ['t','r','i','value']
    ),
    'prsc_csp': (
        [Sw_onlineyearcol,r_col,'tech','ctt','wst','cap'],
        ['t','r','i','ctt','wst','value']
    ),
    'retirements': (
        [retscen,r_col,'tech','coolingwatertech','ctt','wst','cap'],
        ['t','r','i','coolingwatertech','ctt','wst','value']
    ),
    'windret': (
        [r_col,'tech','RetireYear','cap'],
        ['r','i','t','value']
    ),
}

#%% PROCEDURE ------------------------------------------------------------------------
print('Starting writecapdat.py')
cappath = os.path.join(reeds_path,'inputs','capacitydata')

print('Importing generator database:')
gdb_use = pd.read_csv(os.path.join(cappath,'ReEDS_generator_database_final_EIA-NEMS.csv'),
                      low_memory=False)

### Make some initial modifications to the generator database:
# Filter to modeled regions
gdb_use = gdb_use.loc[gdb_use[r_col].isin(val_r)]

# If DUPV is turned off, consider all DUPV as UPV for existing and prescribed builds.
if GSw_DUPV == 0:
    gdb_use['tech'] = gdb_use['tech'].replace('dupv','upv')

# Change tech category of hydro that will be prescribed to use upgrade tech
# This is a coarse assumption that all recent new hydro is upgrades
# Existing hydro techs (hydED/hydEND) specifically refer to hydro that exists in 2010
# Future work could incorporate this change into unit database creation and possibly
#    use data from ORNL HydroSource to assign a more accurate hydro category.
gdb_use.loc[
    (gdb_use['tech']=='hydEND') & (gdb_use[Sw_onlineyearcol] >= Sw_startyear), 'tech'
] = 'hydUND'
gdb_use.loc[
    (gdb_use['tech']=='hydED') & (gdb_use[Sw_onlineyearcol] >= Sw_startyear), 'tech'
] = 'hydUD'

# We model csp-ns (CSP No Storage) as upv throughout ReEDS, but switch it back for reporting.
# So save the csp-ns capacity separately, then rename it.
csp_units = (
    gdb_use.loc[(gdb_use['tech']=='csp-ns') & (gdb_use['RetireYear'] > Sw_startyear)]
    .groupby([r_col,'StartYear','RetireYear']).cap.sum()
    .reset_index()
)
if len(csp_units):
    cap_cspns = (
        pd.concat(
            {i: pd.Series(
                [row.cap]*(row.RetireYear - row.StartYear + 2),
                index=range(row.StartYear, row.RetireYear + 2)
            ) for (i,row) in csp_units.iterrows()},
            axis=1)
        .rename(columns=csp_units[r_col]).fillna(0)
        .groupby(axis=1, level=0).sum()
        .stack().replace(0,np.nan).dropna()
        .rename_axis(['t','*r']).reorder_levels(['*r','t']).rename('MWac')
    )
    cap_cspns = (
        cap_cspns.loc[cap_cspns.index.get_level_values('t') >= Sw_startyear].copy())
else:
    cap_cspns = pd.DataFrame(columns=['*r','t','MWac']).set_index(['*r','t'])
# csp-ns capacity is MWac measured at the power block, while PV capacity is MWdc,
# so multiply csp-ns capacity by the ILR [MWdc/MWac] of PV
gdb_use.loc[gdb_use['tech']=='csp-ns','cap'] *= scalars['ilr_utility']
# Rename csp-ns to upv
gdb_use.loc[gdb_use['tech']=='csp-ns','coolingwatertech'] = (
    gdb_use.loc[gdb_use['tech']=='csp-ns','coolingwatertech']
    .map(lambda x: x.replace('csp-ns','upv'))
)
gdb_use.loc[gdb_use['tech']=='csp-ns','tech'] = 'upv'

# If using cooling water, set the coolingwatertech of technologies with no
# cooling to be the same as the tech
if GSw_WaterMain == 1:
    gdb_use.loc[gdb_use['tech'].isin(TECH['no_cooling']),
                'coolingwatertech'] = gdb_use.loc[gdb_use['tech'].isin(TECH['no_cooling']),
                                                  'tech']

#=================================
#%% --- ALL EXISTING CAPACITY ---
#=================================
### Used as the starting point for intra-zone network reinforcement costs
poi_cap_init = gdb_use.loc[(gdb_use[Sw_onlineyearcol] < Sw_startyear) &
                           (gdb_use['RetireYear'] > Sw_startyear) 
].groupby(r_col).cap.sum().rename('MW').round(3)
poi_cap_init.index = poi_cap_init.index.rename('*r')

#=================================
#%% --- NONRSC EXISTING CAPACITY ---
#=================================
print('Gathering non-RSC Existing Capacity...')
capnonrsc = gdb_use.loc[(gdb_use['tech'].isin(TECH['capnonrsc'])) &
                        (gdb_use[Sw_onlineyearcol] < Sw_startyear) &
                        (gdb_use['RetireYear']     > Sw_startyear)
                        ]
capnonrsc = capnonrsc[COLNAMES['capnonrsc'][0]]
capnonrsc.columns = COLNAMES['capnonrsc'][1]
capnonrsc = capnonrsc.groupby(COLNAMES['capnonrsc'][1][:-1]).sum().reset_index()

# Create geoexist.csv and copy to inputs_case
geoexist = gdb_use.loc[(gdb_use['tech'] == 'geothermal') &
                       (gdb_use[Sw_onlineyearcol] < Sw_startyear) &
                       (gdb_use['RetireYear']     > Sw_startyear)
                       ]
geoexist = (geoexist[['tech',r_col,'cap']]
            .rename(columns={'tech':'*i',r_col:'r','cap':'MW'})
            )
geoexist = geoexist.groupby(['*i','r']).sum().reset_index()
# Rename generic geothermal tech category to geohydro_allkm_1
geoexist['*i'] = 'geohydro_allkm_1'
geoexist.to_csv(os.path.join(inputs_case,'geoexist.csv'),index=False)

#====================================
#%% --- NONRSC PRESCRIBED CAPACITY ---
#====================================
print('Gathering non-RSC Prescribed Capacity...')
prescribed_nonRSC = gdb_use.loc[(gdb_use['tech'].isin(TECH['prescribed_nonRSC'])) &
                                (gdb_use[Sw_onlineyearcol] >= Sw_startyear)
                                ]
prescribed_nonRSC = prescribed_nonRSC[COLNAMES['prescribed_nonRSC'][0]]
prescribed_nonRSC.columns = COLNAMES['prescribed_nonRSC'][1]
# Remove ctt and wst data from storage, set coolingwatertech to tech type ('i')
for j, row in prescribed_nonRSC.iterrows():
    if row['i'] in TECH['storage']:
        prescribed_nonRSC.loc[j,['ctt','wst','coolingwatertech']] = ['n','n',row['i']]

#GSw_WaterMain
if int(sw.GSw_NuclearDemo)==1:
    #load in demo data and stack it on prescribed non-RSC 
    demo = pd.read_csv(os.path.join(reeds_path,'inputs','capacitydata','demonstration_plants.csv'))
    demo = demo[demo['r'].isin(val_r)]
    prescribed_nonRSC = pd.concat([prescribed_nonRSC,demo],sort=False)

prescribed_nonRSC = (
    prescribed_nonRSC.groupby(COLNAMES['prescribed_nonRSC'][1][:-1]).sum().reset_index())

### TODO TEMPORARY BUGFIX: Remove problem capacity
prescribed_nonRSC.loc[
    (prescribed_nonRSC.i=='geothermal') & (prescribed_nonRSC.r=='p31'),
    'value'
] = 0

#===============================
#%% --- RSC EXISTING CAPACITY ---
#===============================
'''
The following are RSC tech that are treated differently in the model
'''
print('Gathering RSC Existing Capacity...')
# DUPV and UPV values are collected at the same time here:
caprsc = gdb_use.loc[(gdb_use['tech'].isin(TECH['rsc_all'][:2])) &
                     (gdb_use[Sw_onlineyearcol] < Sw_startyear)  &
                     (gdb_use['RetireYear']     > Sw_startyear)
                     ]
caprsc = caprsc[COLNAMES['rsc'][0]]
caprsc.columns = COLNAMES['rsc'][1]
caprsc = caprsc.groupby(COLNAMES['rsc'][1][:-2]).sum().reset_index()
# Multiply all PV capacities by ILR
caprsc['value'] = caprsc['value'] * scalars['ilr_utility']

# Add existing CSP builds:
#   Note: Since CSP data is affected by GSw_WaterMain, it must be dealt with
#       separate from the other RSC tech (UPV, DUPV, wind, etc)
csp = gdb_use.loc[(gdb_use['tech'].isin(TECH['rsc_csp']))    &
                  (gdb_use[Sw_onlineyearcol] < Sw_startyear) &
                  (gdb_use['RetireYear']     > Sw_startyear)
                  ]
csp = csp[COLNAMES['rsc'][0]]
csp.columns = COLNAMES['rsc'][1]
csp = csp.groupby(COLNAMES['rsc'][1][:-1]).sum().reset_index()
if GSw_WaterMain == 1:
    csp['i'] = csp['i'] + '_' + csp['ctt'] + '_' + csp['wst']
csp.drop('wst', axis=1, inplace=True)

# Add existing hydro builds:
gendb = gdb_use[["tech", r_col, "cap"]]
gendb = gendb[(gendb.tech == 'hydED') | (gendb.tech == 'hydEND')]

hyd = gendb.groupby(['tech', r_col]).sum() \
           .reset_index() \
           .rename({"tech": "i", r_col: "r", "cap": "value"}, axis=1)

hyd['ctt'] = 'n'

# Concat all RSC Existing Data to one dataframe:
caprsc = pd.concat([caprsc, csp, hyd])

# Export Existing RSC data specifically used in writesupplycurves.py
rsc_wsc = gdb_use.loc[(gdb_use['tech'].isin(TECH['rsc_wsc'])) &
                      (gdb_use[Sw_onlineyearcol] < Sw_startyear) &
                      (gdb_use['RetireYear']     > Sw_startyear)
                      ]
rsc_wsc = rsc_wsc[COLNAMES['rsc_wsc'][0]]
rsc_wsc.columns = COLNAMES['rsc_wsc'][1]
    # Multiply all PV capacities by ILR
for j,row in rsc_wsc.iterrows():
    if row['i'] in ['DUPV','UPV']:
        rsc_wsc.loc[j,'value'] *= scalars['ilr_utility']

#=================================
#%% --- RSC PRESCRIBED CAPACITY ---
#=================================
print('Gathering RSC Prescribed Capacity...')
# DUPV and UPV values are collected at the same time here:
pupv = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_upv'])) &
                   (gdb_use[Sw_onlineyearcol] >= Sw_startyear)
                   ]
pupv = pupv[COLNAMES['prsc_upv'][0]]
pupv.columns = COLNAMES['prsc_upv'][1]
pupv = pupv.groupby(['t','r','i']).sum().reset_index()
# Multiply all PV capacities by ILR
pupv['value'] = pupv['value'] * scalars['ilr_utility']

# Load in wind builds:
pwind = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_w'])) &
                    (gdb_use[Sw_onlineyearcol] >= Sw_startyear)
                    ]
pwind = pwind[COLNAMES['prsc_w'][0]]
pwind.columns = COLNAMES['prsc_w'][1]

pwind = pwind.groupby(['t','r','i']).sum().reset_index()
pwind.sort_values(['t','r'], inplace=True)

# Add prescribed csp builds:
#   Note: Since csp is affected by GSw_WaterMain, it must be dealt with separate
#         from the other RSC tech (dupv, upv, wind, etc)
pcsp = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_csp'])) &
                   (gdb_use[Sw_onlineyearcol] >= Sw_startyear)
                   ]
pcsp = pcsp[COLNAMES['prsc_csp'][0]]
pcsp.columns = COLNAMES['prsc_csp'][1]
if GSw_WaterMain == 1:
    pcsp['i'] = np.where(pcsp['i']=='csp-ws',pcsp['i']+'_'+pcsp['ctt']+'_'+pcsp['wst'],'csp-ws')


# Concat all RSC Existing Data to one dataframe:
prescribed_rsc = pd.concat([pupv,pwind,pcsp],sort=False)

#------------------------------------------------------------------------------
#=================================
#   --- Retirements Data ---
#=================================
print('Gathering Retirement Data...')
rets = gdb_use.loc[(gdb_use['tech'].isin(TECH['retirements'])) &
                   (gdb_use[retscen]>Sw_startyear)
                   ]
rets = rets[COLNAMES['retirements'][0]]
rets.columns = COLNAMES['retirements'][1]
rets.sort_values(by=COLNAMES['retirements'][1],inplace=True)
rets = rets.groupby(COLNAMES['retirements'][1][:-1]).sum().reset_index()

#================================
#   --- Wind Retirements ---
#================================
print('Gathering Wind Retirement Data...')
wind_rets = gdb_use.loc[(gdb_use['tech'].isin(TECH['windret'])) &
                        (gdb_use[Sw_onlineyearcol] <= Sw_startyear) &
                        (gdb_use['RetireYear']     >  Sw_startyear) &
                        (gdb_use['RetireYear']     <  Sw_startyear + 30)
                        ]
wind_rets = wind_rets[COLNAMES['windret'][0]]
wind_rets.columns = COLNAMES['windret'][1]
wind_rets['v'] = 'init-1'
wind_rets = wind_rets.groupby(['i','v','r','t']).sum().reset_index()

wind_rets = (wind_rets.pivot_table(index = ['i','v','r'], columns = 't', values='value')
                      .reset_index()
                      .fillna(0)
            )

#------------------------------------------------------------------------------
#=================================
#%% --- HYDRO Capacity Factor ---
#=================================
hydcf = pd.read_csv(os.path.join(cappath, "hydcf.csv"))
# filter down to modeled regions
hydcf = hydcf[hydcf['r'].isin(val_r)]
hydcf['value'] = hydcf['value'].round(6)
hydcf.szn = hydcf.szn.map(season2szn)

#hydro cf adjustment by szn
hydcfadj = pd.read_csv(os.path.join(cappath, "SeaCapAdj_hy.csv"))
# filter down to modeled regions
hydcfadj = hydcfadj[hydcfadj['r'].isin(val_r)]
hydcfadj['value'] = hydcfadj['value'].round(6)
hydcfadj.szn = hydcfadj.szn.map(season2szn)

#%%
#=================================
# --- waterconstraint indexing ---
#=================================

rets['i'] = rets['i'].str.lower()
prescribed_nonRSC['i'] = prescribed_nonRSC['i'].str.lower()

# When water constraints are enabled, retirements are also indexed by cooling technology
# and cooling water source. otherwise, they only have the indices of year, region, and tech
if GSw_WaterMain == 1:
    ### Group by all cols except 'value'
    rets = rets.groupby(COLNAMES['retirements'][1][:-1]).sum().reset_index()
    rets.columns = COLNAMES['retirements'][1]

    capnonrsc = capnonrsc.groupby(COLNAMES['capnonrsc'][1][:-1]).sum().reset_index()
    capnonrsc.columns = COLNAMES['capnonrsc'][1]

    prescribed_nonRSC = (
        prescribed_nonRSC
        .groupby(COLNAMES['prescribed_nonRSC'][1][:-1]).sum().reset_index())
    prescribed_nonRSC.columns = COLNAMES['prescribed_nonRSC'][1]

    rets['i'] = rets['coolingwatertech']
    rets = rets.groupby(['t','r','i']).sum().reset_index()
    rets.columns = ['t','r','i','value']

    capnonrsc['i'] = capnonrsc['coolingwatertech']
    capnonrsc = capnonrsc.groupby(['i','r']).sum().reset_index()
    capnonrsc.columns = ['i','r','value']

    prescribed_nonRSC['i'] = prescribed_nonRSC['coolingwatertech']
    prescribed_nonRSC = prescribed_nonRSC.groupby(['t','r','i']).sum().reset_index()
    prescribed_nonRSC.columns = ['t','r','i','value']
else:
# Group by [year, region, tech]
    rets = rets.groupby(['t','r','i']).sum().reset_index()
    rets.columns = ['t','r','i','value']

    capnonrsc = capnonrsc.groupby(['i','r']).sum().reset_index()
    capnonrsc.columns = ['i','r','value']

    prescribed_nonRSC = prescribed_nonRSC.groupby(['t','r','i']).sum().reset_index()
    prescribed_nonRSC.columns = ['t','r','i','value']

# Final Groupby step for capacity groupings not affected by GSw_WaterMain:
caprsc = caprsc.groupby(['i','r']).sum().reset_index()
prescribed_rsc = prescribed_rsc.groupby(['t','i','r']).sum().reset_index()

#=================================
#%% --- Canadian imports ---
#=================================

can_imports_year_mwh = pd.read_csv(
    os.path.join(reeds_path,'inputs','canada_imports','can_imports.csv'),
    index_col='r').reindex(val_r).dropna()
can_imports_year_mwh.columns = can_imports_year_mwh.columns.astype(int)
can_imports_year_mwh = can_imports_year_mwh.reindex(years, axis=1).dropna(axis=1)

h_dt_szn = pd.read_csv(os.path.join(reeds_path,'inputs','variability','h_dt_szn.csv'))
sznhours = h_dt_szn.loc[h_dt_szn.year==2012].groupby('season').year.count()
sznhours.index = sznhours.index.map(season2szn).rename('szn')

can_imports_szn_frac = pd.read_csv(
    os.path.join(reeds_path,'inputs','canada_imports','can_imports_szn_frac.csv'),
    header=0, names=['szn','frac'], index_col='szn', squeeze=True)

can_imports_capacity = (
    ## Start with annual imports in MWh
    pd.concat({szn: can_imports_year_mwh for szn in season2szn.values()}, axis=0, names=['szn','r'])
    ## Multiply by season frac to get MWh per season
    .multiply(can_imports_szn_frac, axis=0, level='szn')
    ## Divide by hours per season to get average MW by season
    .divide(sznhours, axis=0, level='szn')
    ## Keep the max value across seasons
    .groupby('r', axis=0).max()
    ## Reshape for GAMS
    .stack().rename_axis(['*r','t']).rename('MW').round(3)
)


#%%
#=================================
# --- Data Write-Out ---
#=================================

#Round outputs before writing out
for df in [rets, capnonrsc, prescribed_nonRSC, caprsc, prescribed_rsc]:
    df['value'] = df['value'].round(6)
    # Set all years to integer datatype
    if 't' in df.columns:
        df['t'] = (df
                   .t
                   .astype(float)
                   .round()
                   .astype(int)
                   )

#%% Write it
print('Writing out capacity data')
capnonrsc[['i','r','value']].to_csv(
    os.path.join(inputs_case,'capnonrsc.csv'),index=False)
rets[['t','r','i','value']].to_csv(
    os.path.join(inputs_case,'retirements.csv'),index=False)
prescribed_nonRSC[['t','i','r','value']].to_csv(
    os.path.join(inputs_case,'prescribed_nonRSC.csv'),index=False)
caprsc[['i','r','value']].to_csv(
    os.path.join(inputs_case,'caprsc.csv'),index=False)
prescribed_rsc[['t','i','r','value']].to_csv(
    os.path.join(inputs_case,'prescribed_rsc.csv'),index=False)
wind_rets.to_csv(
    os.path.join(inputs_case,'wind_retirements.csv'),index=False)
poi_cap_init.to_csv(os.path.join(inputs_case,'poi_cap_init.csv'))
cap_cspns.to_csv(os.path.join(inputs_case,'cap_cspns.csv'))
rsc_wsc.to_csv(os.path.join(inputs_case,'rsc_wsc.csv'),index=False)
### Add '*' to first column name so GAMS reads it as a comment
hydcf[['i','szn','r','t','value']] \
    .rename(columns={'i': '*i'}) \
    .to_csv(os.path.join(inputs_case,'hydcf.csv'), index=False)
hydcfadj[['i','szn','r','value']] \
    .rename(columns={'i': '*i'}) \
    .to_csv(os.path.join(inputs_case,'hydcfadj.csv'), index=False)
can_imports_capacity.to_csv(os.path.join(inputs_case,'can_imports_capacity.csv'))

toc(tic=tic, year=0, process='input_processing/writecapdat.py',
    path=os.path.join(inputs_case,'..'))
print('Finished writecapdat.py')

