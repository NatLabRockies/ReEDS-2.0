# -*- coding: utf-8 -*-
"""
Created on Sun Jul 19 11:13:36 2020
@author: pgagnon

Notes 7-20-20 Pieter Gagnon:
This script generates a dataframe of capital expenditures for plants that were built
through 2010, which is the current starting year of ReEDS. We use a EIA-NEMS
generator database, and the cost assumptions from the 2019 Annual Technology
Baseline.

This script generates a df_capex_init.csv file, which is an input to the
retail rate calculation script. Because we do not expect historical capex estimates
to change (unless our data or methods change), this script is not called by the
retail rate script -- instead it is meant to produce the df_capex_init file
which is treated as a static input. If we ever update our estimates of historical
capital expenditures, that file should be updated.

There are a lot of shortcuts here, such as:
    - assuming all historical capital costs are 2010
    - dealing with resource supply curves for hydro (on average basis)
    - allocation of 's' techs equally within 'p' regions
    - a bunch of other stuff
"""

#%% Imports
import pandas as pd
import numpy as np
import os
import itertools
import site
site.addsitedir('..')
import ferc_distadmin

#%% Arguments
init_cap_file = os.path.join(
    '..', '..', 'inputs', 'capacitydata', 'ReEDS_generator_database_final_EIA-NEMS.csv')
### First year of the ReEDS model run. If this is changed from 2010, the user should 
### ensure that the init_cap_file contains all of the builds through the first year
first_year = 2010 
### Specify whether to overwrite a few EIA-NEMS entries to match EIA860
overwrite_online_year = True

#%% Get the s_to_r map
regions_map = pd.read_csv('regions_for_historical.csv').rename(columns={'p':'r'})
### Map and counts for allocating capacity down to 's' regions
s_to_r_map = regions_map[['s', 'r']].drop_duplicates()
s_counts = s_to_r_map.groupby(['r'], as_index=False).count().rename(columns={'s':'s_count'})


#%% Calculate generation plant depreciation expenses and return on rate base

# Ingest and reformat historical builds (initial capacity)
init_cap_in = pd.read_csv(init_cap_file)
init_cap = (
    ### Drop prescribed builds, because they will show up in the model's outputs
    init_cap_in
    .loc[init_cap_in['Commercial.Online.Year'] <= first_year]
    .sort_values('Commercial.Online.Year')
    ### Set (plant,unit) as index to simplify reassignments below
    .set_index(['PLANT_ID','UNIT_ID'])
).copy()

### Upon comparison with EIA Form 860 (2019, 3_1_Generator_Y2019.xlsx), 
### some plants in EIA-NEMS are listed with a commercial
### online year that is too recent; in some of these cases the commercial online year
### is actually the refurbishment year. For these specific plants we overwrite the 
### commercial online year (t) with the REFURB_YR.
if overwrite_online_year:
    refurb_overwrite = [
        # ( 2008, '1'), ### >= 201
        ( 2864, '4'),
        ( 2864, '5'),
        ( 2094, '1'),
        ( 2094, '2'),
        ( 2324, '1'),
        ( 3179, '1'),
        ( 3179, '2'),
        ( 2324, '2'),
        ( 2008, '4'),
        ( 3179, '3'),
        ( 1363, '5'),
        (  628, '3'),
        ( 2076, '2'),
    ]
    for plant_unit in refurb_overwrite:
        init_cap.loc[plant_unit,'Commercial.Online.Year'] = init_cap.loc[plant_unit, 'REFURB_YR']

#%% Switch back to integer index
init_cap.reset_index(inplace=True)

#############################
#%% Clean up the coal entries
### Get all the duplicate rows from init_cap_in
dfnems_alldup = init_cap.loc[
    init_cap.duplicated(subset=['PLANT_ID','UNIT_ID'], keep=False)].copy()
### Sum the duplicates by 'COUNT'
dfcount = dfnems_alldup.groupby(['PLANT_ID','UNIT_ID'])['COUNT'].sum()
### Get the list of real (PLANT_ID,UNIT_ID) duplicates. Other duplicates are just split ownership.
realdups = dfcount.loc[dfcount >= 1.01].index.tolist()

### Get the coal rows that are real duplicates (not just split ownership)
dfcoal = init_cap.set_index(['PLANT_ID','UNIT_ID']).loc[realdups].copy()
dfcoal = dfcoal.loc[dfcoal.tech.map(lambda x: 'coal' in x.lower())]

### Get the unique coal (plant,unit)s with duplicate entries.
### These are the entries we'll overwrite in init_cap.
coaldup_plant_units = sorted(dfcoal.index.unique())

### Get the mean scrubber cost
SCRUB_COST_mean = dfcoal.loc[dfcoal['SCRUB_COST'] > 0, 'SCRUB_COST'].mean()
### Drop duplicates, aggregate the rest, and record scrubber cost.
### From inspection, there are some entries that have the same plant, unit, tech, and year,
### and thus must be duplicates; these are removed by drop_duplicates(subset=['tech','cap']).
### nems_clean keys are (plant,unit,[0/1]) where 0 is for the entry corresponding to the
### initial consruction of the plant and 1 is for the scrubber upgrade
nems_clean = {}
for plantunit in coaldup_plant_units:
    df = (
        dfcoal.loc[plantunit].sort_values(['Commercial.Online.Year','tech'])
        .drop_duplicates(subset=['tech','cap'],keep='first')
    )
    ### Get years and techs in order of year
    years = df[['Commercial.Online.Year','tech']].drop_duplicates()['Commercial.Online.Year'].values
    techs = df[['Commercial.Online.Year','tech']].drop_duplicates()['tech'].values

    if len(years) > 2:
        raise Exception('Too many years: {}'.format(','.join([str(x) for x in years])))

    elif len(years) == 1:
        ### Make sure there's only one tech if there's only one year
        if len(techs) > 1:
            raise Exception('too many techs ({}) and not enough years ({})'.format(
                ','.join(techs),','.join([str(x) for x in years])))
        ### Store the values
        nems_clean[(*(plantunit),0)] = {
            'tech': techs[0],
            ### Assume there's only one pca
            'pca': df.iloc[0]['pca'],
            'state': df.iloc[0]['STATE'],
            ### Since only one (tech,year), sum the capacity
            'cap': df.cap.sum(),
            ### Only one year
            'Commercial.Online.Year': years[0],
            'upgrade_cost': 0,
        }

    elif len(years) == 2:
        ### Make sure there are two techs
        if len(techs) != 2:
            raise Exception('mismatched techs ({}) and years ({})'.format(
                ','.join(techs), ','.join([str(x) for x in years])))
            
        ###### Make two entries: One for plant construction, one for upgrade
        initial_year = years[0]
        upgrade_year = years[1]
        ### Entry for initial construction
        nems_clean[(*(plantunit),0)] = {
            'tech': techs[0],
            'pca': df.iloc[0]['pca'],
            'state': df.iloc[0]['STATE'],
            'cap': df.groupby('tech')['cap'].sum()[techs[0]],
            'Commercial.Online.Year': years[0],
            'upgrade_cost': 0,
        }
        ### Entry for upgrade
        ### Made sure that df.groupby('tech')['SCRUB_COST'].std() is zero or nan
        SCRUB_COST = df.groupby('tech')['SCRUB_COST'].mean()[techs[1]]
        nems_clean[(*(plantunit),1)] = {
            'tech': techs[1],
            'pca': df.iloc[0]['pca'],
            'state': df.iloc[0]['STATE'],
            'cap': df.groupby('tech')['cap'].sum()[techs[1]],
            'Commercial.Online.Year': years[1],
            ### Filter out zero and low values
            'upgrade_cost': (SCRUB_COST if SCRUB_COST > 50 else SCRUB_COST_mean),
        }
### NEMS costs are in 1987 USD, so inflate to 2004
inflatable = ferc_distadmin.get_inflatable(
    inflationpath=os.path.join('..','..','inputs','financials','inflation_default.csv'))
### Format as dataframe
dfnems_coal = pd.DataFrame(nems_clean).T
dfnems_coal.index.rename(['PLANT_ID','UNIT_ID','upgrade_flag'], inplace=True)
### Change the units for upgrade_cost from 1987 $/kW to 2004 $/MW
dfnems_coal['upgrade_cost_2004'] = dfnems_coal.upgrade_cost * inflatable[1987,2004] * 1000

#%% By inspection, many of the OGS entries are duplicated (not just split ownership).
### So drop those duplicates.
### Get the OGS rows that are real duplicates
dfogs = init_cap.set_index(['PLANT_ID','UNIT_ID']).loc[realdups].copy()
dfogs = dfogs.loc[dfogs.tech.map(lambda x: 'o-g-s' in x.lower())]
### Get the unique OGS (plant,unit)s
ogsdup_plant_units = sorted(dfogs.index.unique())
### Get the entries for duplicate OGS units
dfnems_ogs_clean = init_cap.set_index(['PLANT_ID','UNIT_ID']).loc[ogsdup_plant_units]
### Drop duplicates
dfnems_ogs_clean = dfnems_ogs_clean.reset_index().drop_duplicates(
    subset=(['PLANT_ID','UNIT_ID','tech','cap','Commercial.Online.Year','COUNT']),
    keep='first'
).set_index(['PLANT_ID','UNIT_ID'])
### Drop the duplicate entries from init_cap and add back the cleaned entries
init_cap = (
    init_cap.set_index(['PLANT_ID','UNIT_ID']).drop(ogsdup_plant_units)
    .append(dfnems_ogs_clean)
    .reset_index()
)

#%%### Add the cleaned-up coal entries back into init_cap
### Drop the duplicated coal entries and unused colums
init_cap_clean = init_cap.set_index(['PLANT_ID','UNIT_ID']).drop(coaldup_plant_units)[
    ['tech', 'pca', 'Commercial.Online.Year', 'cap']]
### Add a column for upgrade cost
init_cap_clean['upgrade_cost_2004'] = 0
### Append the cleaned-up coal rows
init_cap_clean = init_cap_clean.append(
    dfnems_coal.reset_index('upgrade_flag',drop=True)
    [['tech','pca','Commercial.Online.Year','cap','upgrade_cost_2004']]
)
### Drop the (plant,unit) index, rename columns, and overwrite init_cap
init_cap = init_cap_clean.reset_index(drop=True).rename(
    columns={'tech':'i', 'pca':'region', 'cap':'cap_new', 'Commercial.Online.Year':'t'}
)

#%% Set up tech-specific datasets
# Init wind cap is specified in 'r' regions, but I need it in 's' regions to merge with cap cost.
# Allocate the capacity equally to all 's' regions within a 'r' region.
init_wind = init_cap[init_cap['i']=='wind-ons']
init_cap = init_cap[init_cap['i']!='wind-ons']
init_wind['i'] = 'wind-ons_1'
init_wind = init_wind.merge(s_counts.rename(columns={'r':'region'}), on='region', how='left')
init_wind = init_wind.merge(s_to_r_map.rename(columns={'r':'region'}), on='region', how='left')
init_wind['cap_new'] = init_wind['cap_new'] / init_wind['s_count']
init_wind['region'] = init_wind['s']
init_cap = pd.concat(
    [init_cap, init_wind[['i', 't', 'region', 'cap_new']]], 
    ignore_index=True, sort=False)

## Init csp-ns is specified in 'r' regions, but I need it in 's' regions to merge with cap cost.
init_cspns = init_cap[init_cap['i']=='csp-ns']
init_cap = init_cap[init_cap['i']!='csp-ns']
init_cspns = (
    init_cspns
    .merge(s_counts.rename(columns={'r':'region'}), on='region', how='left')
    .merge(s_to_r_map.rename(columns={'r':'region'}), on='region', how='left')
)
init_cspns['cap_new'] = init_cspns['cap_new'] / init_cspns['s_count']
init_cspns['region'] = init_cspns['s']
init_cap = pd.concat(
    [init_cap, init_cspns[['i', 't', 'region', 'cap_new']]], 
    ignore_index=True, sort=False)

# Cleaning up tech names
init_cap['i'] = np.where(init_cap['i']=='gas-CT',    'Gas-CT',    init_cap['i'])
init_cap['i'] = np.where(init_cap['i']=='gas-CC',    'Gas-CC',    init_cap['i'])
init_cap['i'] = np.where(init_cap['i']=='nuclear',   'Nuclear',   init_cap['i'])
init_cap['i'] = np.where(init_cap['i']=='UPV',       'upv_1',     init_cap['i'])
init_cap['i'] = np.where(init_cap['i']=='DUPV',      'dupv_1',    init_cap['i'])
init_cap['i'] = np.where(init_cap['i']=='coal-IGCC', 'Coal-IGCC', init_cap['i'])

# These are just labelled as generic 'hydro', so assigning them a middle-cost hydro tech
init_cap['i'] = np.where(init_cap['i']=='hydro', 'hydND', init_cap['i']) 
# These are just labelled as generic 'geo', so assigning them a middle-cost hydro tech
init_cap['i'] = np.where(init_cap['i']=='geothermal', 'geohydro_pbinary_1', init_cap['i']) 


########################
#%% Ingest capital costs

# Ingest capital costs, adjust for multipliers
# capital costs used for historical builds, 2004$, derived from ATB 2019 
cost_cap = pd.read_csv('cost_cap_for_historical.csv', dtype={'t':int})
# capital cost multipliers for historical builds, derived from StScen 2019
cap_cost_mult = pd.read_csv('cap_cost_mult_for_historical.csv') 
cost_cap = cap_cost_mult.merge(cost_cap, on=['i'], how='left')
cost_cap['cost_cap'] = cost_cap['cost_cap'] * cost_cap['cap_cost_mult_for_ratebase']

### Ingest and concat geothermal capital costs
# geo costs used for historical builds, 2004$, derived from StScen 2019 
geo_cap_cost = pd.read_csv('geo_cap_cost_for_historical.csv') 
cost_cap = pd.concat(
    [cost_cap, geo_cap_cost[['i', 'region', 't', 'cost_cap']]], 
    ignore_index=True, sort=False)

### Ingest and add hydro capital costs
# hydro costs used for historical builds, 2004$, derived from StScen 2019 
rsc_dat = pd.read_csv('rsc_dat_for_historical.csv') 
rsc_dat = rsc_dat.rename(
    columns={'Dim1':'i', 'Dim2':'r', 'Dim3':'dat_type', 'Dim4':'bin', 'Val':'dat_value'})
hydro_cap_cost = rsc_dat[rsc_dat['i'].isin(
    ['pumped-hydro', 'hydND', 'hydUD', 'hydUND', 'hydNPND'])]
hydro_cap_cost_pivot = hydro_cap_cost.pivot_table(
    values='dat_value', columns='dat_type', index=['r', 'i', 'bin']
    ).reset_index().fillna(0.0)
hydro_cap_cost_pivot['weight'] = hydro_cap_cost_pivot['cap'] * hydro_cap_cost_pivot['cost']
hydro_cap_cost_grouped = hydro_cap_cost_pivot.groupby(by=['r', 'i'], as_index=False).sum()
hydro_cap_cost_grouped['cost_cap'] = (
    hydro_cap_cost_grouped['weight'] / hydro_cap_cost_grouped['cap'])
hydro_cap_cost_grouped = hydro_cap_cost_grouped[
    hydro_cap_cost_grouped['cost_cap'].isnull()==False]
hydro_cap_cost_grouped['t'] = 2010
hydro_cap_cost_grouped = hydro_cap_cost_grouped.rename(columns={'r':'region'})
cost_cap = pd.concat(
    [cost_cap, hydro_cap_cost_grouped[['i', 'region', 't', 'cost_cap']]], 
    ignore_index=True, sort=False)

cost_cap_earliest = (
    cost_cap.sort_values('t', ascending=True)
    .drop_duplicates(['i', 'region'], keep='first'))

#%% Merge into init_cap
init_capex = init_cap.merge(
    cost_cap_earliest[['i', 'region', 'cap_cost_mult_for_ratebase', 'cost_cap']], 
    on=['i', 'region'], how='left')

# There are some historical 'hydro' and 'geothermal' techs. Just taking as average
hydro_mean = hydro_cap_cost_grouped['cost_cap'].mean()
init_capex['cost_cap'] = np.where(
    (init_capex['i']=='hydND') & (init_capex['cost_cap'].isnull()), 
    hydro_mean, init_capex['cost_cap'])
init_capex['cost_cap'] = np.where(
    (init_capex['i']=='geohydro_pbinary_1') & (init_capex['cost_cap'].isnull()), 
    15000.0, init_capex['cost_cap'])

#%% For the entries where upgrade_cost_2004 != 0, we overwrite cost_cap with upgrade_cost_2004
### since these entries correspond to upgrades, not new plants
init_capex.loc[init_capex.upgrade_cost_2004.fillna(0) > 0, 'cost_cap'] = (
    init_capex.loc[init_capex.upgrade_cost_2004.fillna(0) > 0, 'upgrade_cost_2004'])

#%% Calculate the capital expenditures associated with each capacity addition
init_capex['capex'] = init_capex['cost_cap'] * init_capex['cap_new']

#################################################################
#%% Write out the CSV that will be used by the retail rate script
init_capex[
    ['i', 'region', 't', 'cap_new', 'capex']
].round(4).to_csv('df_capex_init.csv', index=False)

#%%

# cap_cost_mult = pd.read_pickle('retail_cap_cost_mult.pkl').rename(columns={'r':'region'})
# cap_cost_mult = cap_cost_mult[cap_cost_mult['t']==2010]
# cap_cost_mult = cap_cost_mult[['i', 'region', 'cap_cost_mult_for_ratebase']]
# cap_cost_mult.to_csv('cap_cost_mult_for_historical.csv', index=False)

### Ingest geothermal capital costs
# geo_cap_cost = pd.read_csv(
#     os.path.join(run_dir, 'inputs_case', 'geo_rsc.csv'),
#     header=None, names=['i', 'region', 'data_type', 'base_cost'])
# geo_cap_cost = geo_cap_cost[geo_cap_cost['data_type']=='Cost']
# geo_cost_traj = pd.read_csv(
#     os.path.join(run_dir, 'inputs_case', 'geocapcostmult.csv')
# ).rename(columns={'Unnamed: 0':'t'})
# geo_cost_traj = geo_cost_traj.melt(id_vars='t', var_name='tech', value_name='cost_scalar')
# geo_techs = geo_cost_traj['tech'].drop_duplicates()
# geo_tech_expander = pd.DataFrame(
#     list(itertools.product(geo_techs, np.arange(1,9))), 
#     columns=['tech', 'bin'])
# geo_tech_expander['i'] = geo_tech_expander['tech'] + '_' + geo_tech_expander['bin'].astype(str)
# geo_cost_traj = geo_cost_traj.merge(
#     geo_tech_expander[['tech', 'i']], on='tech', how='left')
# geo_cap_cost = geo_cap_cost.merge(
#     geo_cost_traj[['i', 't', 'cost_scalar']], on=['i'], how='outer')
# geo_cap_cost['cost_cap'] = geo_cap_cost['base_cost'] * geo_cap_cost['cost_scalar']
# geo_cap_cost = geo_cap_cost[geo_cap_cost['cost_cap'].isnull()==False]
# geo_cap_cost[['i', 'region', 't', 'cost_cap']].to_csv('geo_cap_cost.csv', index=False)
