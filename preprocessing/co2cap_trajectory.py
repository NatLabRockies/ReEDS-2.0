###############
#%% IMPORTS ###
import os, time, site
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import matplotlib as mpl
from tqdm.notebook import tqdm

reeds_path = os.path.join(os.path.sep, *(os.path.abspath(__file__).split(os.sep)[:-3]))
site.addsitedir(os.path.join(reeds_path,'postprocessing'))
import plots
plots.plotparams()

pd.options.display.max_columns = 200

##################
#%% PROCEDURES ###

##################################################################################
#%% Method 1: Define caps relative to simulated ReEDS emissions in historical year
##################################################################################

#%% Settings
e = 'CO2'
level = 'transreg'
refyear = 2018
firstyear = 2023
### Set the case to load historical emissions from
case = '/Volumes/ReEDS/Users/pbrown/ReEDSruns/20220411_prm/v20220408_mainM0_ref_seq'
### Set the cap trajectory parameters as multiple of refyear emissions
kinks = {
    refyear: 1,
    firstyear-1: 1,
    # 2035: 0.05,
    # 2050: 0.0,
    2040: 0.0,
}

#%% Load emissions for case
emit_r = pd.read_csv(
    os.path.join(case,'outputs','emit_r.csv'),
    header=0, names=['e','r','t','tonne'],
)

#%% Load static ReEDS inputs
hierarchy = pd.read_csv(
    os.path.join(reeds_path,'inputs','hierarchy.csv')
).rename(columns={'*r':'r'}).set_index('r')
hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()

#%% Loop over all regions in level and create the trajectories
dfout = []
for region in sorted(hierarchy[level].unique()):
    ### Get BAs to sum
    r = hierarchy.loc[hierarchy[level]==region].index.values
    ### Get past emissions
    emissions = emit_r.loc[
        emit_r.r.isin(r) & (emit_r.e==e),
    ].groupby('t').tonne.sum() / 1e6
    ### Make the label
    targetyears = list(kinks.keys())[2:]
    title = '{}_{}_ref{}_start{}_{}'.format(
        level, region, refyear, firstyear,
        '_'.join([
            '{:.0f}pct{}'.format(100-kinks[y]*100, y)
            for y in targetyears
        ])
    )
    print(title)

    ### Make the cap trajectory
    capyears = range(min(list(kinks.keys())), max(list(kinks.keys()))+1)
    mults = pd.Series(kinks).reindex(capyears).interpolate('linear')
    ## Before the cap is activated, set cap higher than historical emissions
    mults.loc[:firstyear-1] = 3
    ## Multiply by reference year emissions to get the cap
    caps = (mults * emissions[refyear]).rename(title)

    #%% Take a look
    plt.close()
    f,ax = plt.subplots(figsize=(6,6))
    ax.plot(
        emissions.index, emissions.values,
        marker='o', markerfacecolor='w', markeredgecolor='k', lw=0,
        label='historical'
    )
    ax.axhline(emissions[refyear], c='C1')
    ax.plot(
        caps.index, caps.values, color='C2', label='cap',
        marker='o', markersize=3,
    )
    ax.set_ylim(0)
    ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))
    ax.grid(axis='x', which='major', c='0.2', lw=0.5, ls='--')
    ax.grid(axis='x', which='minor', c='0.7', lw=0.25, ls='--')
    ax.grid(axis='y', which='major', c='0.2', lw=0.5, ls='--')
    ax.set_title(title)
    ax.legend()
    plt.show()

    dfout.append(caps)

dfout = pd.concat(dfout, axis=1)

#%% Write it to CO2 caps file in ReEDS
## ReEDS CO2 caps are in metric tonnes so multiply by 1E6
dfwrite = pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','co2_cap.csv'),
    index_col=0,
)
dfwrite.columns = dfwrite.columns.astype(int)
dfwrite = (
    dfwrite.T
    .merge((dfout*1e6), left_index=True, right_index=True, how='left')
    .interpolate('bfill')
    .round(0).fillna(0).astype(int)
).T
dfwrite.index = dfwrite.index.rename('t')
dfwrite.to_csv(os.path.join(reeds_path,'inputs','carbonconstraints','co2_cap.csv'))




#############################################################
#%% Method 2: Define caps relative to historical US emissions
#############################################################

#%% Trajectory settings
refyear = 2005
fityears = np.array(list(range(2007,2022)))
firstyear = 2024

#%% Get historical emissions from EIA
### Parent site: https://www.eia.gov/totalenergy/data/monthly/#environment
dfin = pd.read_csv('https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T11.06')
description = 'Total Energy Electric Power Sector CO2 Emissions'
df = dfin.loc[
    (dfin.Description==description)
    & (dfin.YYYYMM.astype(str).str.endswith('13'))
].copy()
df['year'] = ((dfin.YYYYMM - 13) / 100).astype(int)
emissions = df.set_index('year').Value.rename('MMTCO2').astype(float)

#%% Define emissions trajectories
### Get the current trajectory
slope, intercept = np.polyfit(
    fityears, emissions.loc[fityears].values, deg=1)
current_trajectory = pd.Series(
    index=np.arange(refyear, 2031, 1),
    data=(intercept + slope * np.arange(refyear,2031,1)),
    name='current_trajectory',
)

### Set the cap trajectory parameters
kinks = {
    2005: 1,
    firstyear-1: current_trajectory.loc[firstyear-1] / emissions.loc[refyear],
    # 2030: 0.20,
    # 2035: 0.,
    2035: 0.1,
    2045: 0.,
}


### Make the label
targetyears = list(kinks.keys())[2:]
title = 'start{}_{}'.format(
    firstyear,
    '_'.join([
        '{:.0f}pct{}'.format(100-kinks[y]*100, y)
        for y in targetyears
    ])
)
print(title)

### Make the cap trajectory
capyears = range(min(list(kinks.keys())), max(list(kinks.keys()))+1)
mults = pd.Series(kinks).reindex(capyears).interpolate('linear')
## Reset the fix years
mults.loc[:firstyear-1] = 2
## Multiply by reference year emissions to get the cap
caps = (mults * emissions.loc[refyear]).rename(title)

#%% Take a look
plt.close()
f,ax = plt.subplots(figsize=(6,6))
ax.plot(
    emissions.index, emissions.values,
    marker='o', markerfacecolor='w', markeredgecolor='k', lw=0,
    label='historical'
)
ax.plot(
    current_trajectory.index, current_trajectory.values,
    color='C1', marker='o', markersize=3,
    label='current trajectory',
)
ax.plot(
    caps.index, caps.values, color='C2', label='cap',
    marker='o', markersize=3,
)
ax.set_ylim(0,3000)
ax.set_xlim(2000,)
ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))
ax.grid(axis='x', which='major', c='0.2', lw=0.5, ls='--')
ax.grid(axis='x', which='minor', c='0.7', lw=0.25, ls='--')
ax.grid(axis='y', which='major', c='0.2', lw=0.5, ls='--')
ax.set_title(title)
ax.legend()
plt.show()

#%% Write it to CO2 caps file in ReEDS
## ReEDS CO2 caps are in tonnes so multiply by 1E6
dfwrite = pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','co2_cap.csv'),
    index_col=0,
)
dfwrite.columns = dfwrite.columns.astype(int)
dfwrite = (
    dfwrite.T
    .merge((caps*1e6), left_index=True, right_index=True, how='left')
    .interpolate('bfill')
    .round(0).fillna(0).astype(int)
).T
dfwrite.index = dfwrite.index.rename('t')
dfwrite.to_csv(os.path.join(reeds_path,'inputs','carbonconstraints','co2_cap.csv'))



###################################################################
#%% Method 3: Define caps relative to historical emissions by state
###################################################################

#%% Setup
### Request your own key at https://www.eia.gov/opendata/register.cfm and paste it here
apikey = 'mNmSVErE65JjTWMjAh6v0io2PoDdfQ8s2apfhE0D'
### Download everything so we have it (not actually necessary)
states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC',
]
### Trajectory settings
state = 'TX'
refyear = 2005
## fityears: ending in 2019 would be best but only have till 2018
fityears = np.array(list(range(2007,2019)))
firstyear = 2023

#%% Download state emissions from https://www.eia.gov/opendata/qb.php?category=2251670
### Get the category ids
category_id = 2251670
url = f'https://api.eia.gov/category/?api_key={apikey}&category_id={category_id}'
r = requests.get(url)
statecategories = pd.Series({
    i['name']: i['category_id']
    for i in r.json()['category']['childcategories']
})
### Example query:
### https://www.eia.gov/opendata/qb.php?category=2251714&sdid=EMISS.CO2-TOTV-EC-TO-TX.A

### Download it
emissions = {}
for st in tqdm(states):
    url = f'https://api.eia.gov/series/?api_key={apikey}&series_id=EMISS.CO2-TOTV-EC-TO-{st}.A'
    r = requests.get(url)
    emissions[st] = pd.DataFrame(
        r.json()['series'][0]['data'],
        columns=['year','CO2_MMT'],
    ).astype({'year':int, 'CO2_MMT':float}).set_index('year').CO2_MMT
    ### Sleep a bit so they don't shut us down
    time.sleep(0.1)

emissions = pd.DataFrame(emissions).sort_index()

#%% Plot emissions for each state (optional)
startyear = 2000
nrows, ncols = 5,10
coords = dict(zip(states[:50], [(row,col) for row in range(nrows) for col in range(ncols)]))
plt.close()
f,ax = plt.subplots(nrows,ncols,figsize=(14,6),sharex=True,gridspec_kw={'wspace':0.5})
for st in states[:50]:
    ax[coords[st]].plot(
        emissions.loc[startyear:].index, emissions.loc[startyear:][st].values
    )
    ax[coords[st]].annotate(st,(2000,0),weight='bold',fontsize='large')
    ax[coords[st]].set_ylim(0)

ax[-1,0].set_ylabel('Electricity-sector CO2 emissions\n[million metric tonnes CO2]', y=0, ha='left')
plots.despine(ax)
plt.show()

#%% Define emissions trajectories
### Get the current trajectory
slope, intercept = np.polyfit(
    fityears, emissions.loc[fityears,state].values, deg=1)
current_trajectory = pd.Series(
    index=np.arange(refyear, 2031, 1),
    data=(intercept + slope * np.arange(refyear,2031,1)),
    name='current_trajectory',
)
### Set the cap trajectory parameters
kinks = {
    2005: 1,
    firstyear-1: current_trajectory.loc[firstyear-1] / emissions.loc[refyear,state],
    2035: 0.05,
    2050: 0.,
}

### Make the label
targetyears = list(kinks.keys())[2:]
title = '{}_start{}_{}'.format(
    state, firstyear,
    '_'.join([
        '{:.0f}pct{}'.format(100-kinks[y]*100, y)
        for y in targetyears
    ])
)
print(title)

### Make the cap trajectory
capyears = range(min(list(kinks.keys())), max(list(kinks.keys()))+1)
mults = pd.Series(kinks).reindex(capyears).interpolate('linear')
## Reset the fix years
mults.loc[:firstyear-1] = 2
## Multiply by reference year emissions to get the cap
caps = (mults * emissions.loc[refyear,state]).rename(title)

#%% Take a look
plt.close()
f,ax = plt.subplots(figsize=(6,6))
ax.plot(
    emissions.index, emissions[state].values,
    marker='o', markerfacecolor='w', markeredgecolor='k', lw=0,
    label='historical'
)
ax.plot(
    current_trajectory.index, current_trajectory.values,
    color='C1', marker='o', markersize=3,
    label='current trajectory',
)
ax.plot(
    caps.index, caps.values, color='C2', label='cap',
    marker='o', markersize=3,
)
ax.set_ylim(0)
ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))
ax.grid(axis='x', which='major', c='0.2', lw=0.5, ls='--')
ax.grid(axis='x', which='minor', c='0.7', lw=0.25, ls='--')
ax.grid(axis='y', which='major', c='0.2', lw=0.5, ls='--')
ax.set_title(title)
ax.legend()
plt.show()

#%% Write it to CO2 caps file in ReEDS
## ReEDS CO2 caps are in tonnes so multiply by 1E6
dfout = pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','co2_cap.csv'),
    index_col='t',
)
dfout[title] = (caps.loc[dfout.index]*1E6).round(0).astype(int)
dfout.to_csv(os.path.join(reeds_path,'inputs','carbonconstraints','co2_cap.csv'))
