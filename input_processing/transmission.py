#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import geopandas as gpd
import pandas as pd
from shapely import wkt
import numpy as np
import os
import sys
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
tic = datetime.datetime.now()

#%% Parse arguments
parser = argparse.ArgumentParser(description="Format and write climate inputs")
parser.add_argument('reeds_path', help='ReEDS directory')
parser.add_argument('inputs_case', help='output directory (inputs_case)')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing ###
# reeds_path = reeds.io.reeds_path
# inputs_case = os.path.join(reeds_path,'runs','v20250919_tscM0_Central','inputs_case')

#%%#################
### FIXED INPUTS ###

decimals = 5
drop_canmex = True
dollar_year = 2004
weight = 'cost'

costcol = f'USD{dollar_year}perMW'

#%% Set up logger
log = reeds.log.makelog(
    scriptname=__file__,
    logpath=os.path.join(inputs_case,'..','gamslog.txt'),
)
print('Starting transmission.py', flush=True)

#%% Inputs from switches
sw = reeds.io.get_switches(inputs_case)

## networksource must end in a 4-digit year indicating the year represented by the network
trans_init_year = int(sw.GSw_TransNetworkSource[-4:])

valid_regions = {}
for level in ['r','itlgrp','transgrp']:
    valid_regions[level] = pd.read_csv(
        os.path.join(inputs_case, f'val_{level}.csv'), header=None).squeeze(1).tolist()


#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================
def get_trancap_init(valid_regions, networksource='NARIS2024', level='r'):
    ### Get alias for level (e.g. rr, transgrpp)
    levell = level + level[-1]

    ### AC capacity is defined for each direction and calculated using the scripts at
    ### https://github.nrel.gov/pbrown/TSC
    trancap_init_ac = pd.read_csv(
        os.path.join(
            inputs_case,f'transmission_capacity_init_AC_{level}.csv'))
    trancap_init_ac['trtype'] = 'AC'

    # adjusting level for the ITLGRP constraints
    if level == 'itlgrp':
        trancap_init_ac= trancap_init_ac.rename(columns={'r':'itlgrp','rr':'itlgrpp'})

    ## DC capacity is only defined in one direction, so duplicate it for the opposite direction
    if level in ['r','itlgrp']:
        trancap_init_nonac_undup = pd.read_csv(
            os.path.join(inputs_case,'transmission_capacity_init_nonAC.csv'))
        if level == 'itlgrp':
            trancap_init_nonac_undup = pd.read_csv(
                os.path.join(inputs_case,'transmission_capacity_init_nonAC.csv')
            ).rename(columns = {'r':'itlgrp','rr':'itlgrpp'})

        trancap_init_nonac = pd.concat(
            [trancap_init_nonac_undup, trancap_init_nonac_undup.rename(columns={level:levell, levell:level})],
            axis=0
        )
        ### SPECIAL CASE: p19 is islanded with NARIS transmission data, so connect it manually
        if (
            (networksource == 'NARIS2024')
            and ('p19' in valid_regions['r']) and ('p20' in valid_regions['r'])
        ):
            trancap_init_ac = pd.concat([
                trancap_init_ac,
                pd.Series({
                    'interface':'p19||p20', 'r':'p19', 'rr':'p20',
                    'MW_f0':0.001, 'MW_r0':0.001, 'MW_f1':0, 'MW_r1':0, 'trtype':'AC'})
            ], ignore_index=True)
    else:
        trancap_init_nonac = pd.DataFrame(
            columns=[level, levell, 'trtype', 'MW', 'Project(s)', 'Notes'])

    ### Initial trading limit, using contingency levels specified by contingency level
    ### (but assuming full capacity of DC is available for both energy and capcity)
    trancap_init = {
        n: (pd.concat([
            ## AC
            pd.concat([
                ## Forward direction
                (trancap_init_ac[[level,levell,'trtype',f'MW_f{n}']]
                .rename(columns={f'MW_f{n}':'MW'})),
                ## Reverse direction
                (trancap_init_ac[[level,levell,'trtype',f'MW_r{n}']]
                .rename(columns={level:levell, levell:level, f'MW_r{n}':'MW'}))
            ], axis=0),
            ## DC
                trancap_init_nonac[[level,levell,'trtype','MW']]
        ## Drop entries with zero capacity
        ], axis=0).replace(0.,np.nan).dropna()
            .groupby([level,levell,'trtype']).sum().reset_index())
        for n in [0,1]
    }

    if level in ['itlgrp']:
        hierarchy = pd.read_csv(os.path.join(inputs_case, 'hierarchy_itlgrp.csv'))
        itl_d = dict(zip(hierarchy['*r'],hierarchy['itlgrp']))
        for n in [0,1]:
            for r in [level, levell]:
                trancap_init[n][r] = trancap_init[n][r].map(lambda x: itl_d.get(x,x))
    return trancap_init


def calculate_adjacent_routes(dfzones):
    routes_adjacent = dfzones.copy()
    routes_adjacent['r_adj'] = routes_adjacent.apply(
        axis=1,
        func=lambda x: (
            routes_adjacent.loc[(
                routes_adjacent.touches(x['geometry'])
                | routes_adjacent.overlaps(x['geometry'])
            )]
            .index
            .values
            .tolist()
        )
    )
    # Reformat so that each row represents a pair of regions
    routes_adjacent = (
        routes_adjacent.drop(columns='geometry')
        .explode('r_adj')
        .reset_index(names=['r'])
        .rename(columns={'r': '*r', 'r_adj': 'rr'})
        [['*r', 'rr']]
        .dropna()
    )

    return routes_adjacent


def calculate_co2_storage_routes(dfzones, co2_storage_sites):
    # Determine the storage sites that are within 200 miles
    # of each region's transmission endpoint
    region_centroids = (
        gpd.GeoDataFrame(
            dfzones[['x', 'y']],
            geometry=gpd.points_from_xy(dfzones.x, dfzones.y),
            crs=dfzones.crs
        )
        [['geometry']]
        .rename_axis(index='*r')
        .reset_index()
    )
    region_centroids['cs'] = region_centroids.apply(
        axis=1,
        func=lambda x: (
            co2_storage_sites.loc[(
                co2_storage_sites.distance(x['geometry']) / 1609.34 <= 200
            )]
            ['cs']
            .tolist()
        )
    )

    # Calculate the lengths of the spurlines between regions and storage sites,
    # excluding routes not completely within the U.S.
    routes_cs = (
        region_centroids.explode('cs')
        .merge(
            co2_storage_sites[['cs', 'geometry']],
            on='cs',
            suffixes=('_region', '_site')
        )
        .assign(
            geometry=lambda x: (
                gpd.GeoSeries(x['geometry_region'])
                .shortest_line(gpd.GeoSeries(x['geometry_site']))
            )
        )
        [['*r', 'cs', 'geometry']]
    )
    routes_cs = gpd.GeoDataFrame(routes_cs, geometry='geometry', crs=dfzones.crs)
    routes_cs = routes_cs.loc[(
        routes_cs.within(
            reeds.io.get_dfmap(levels=['country'])['country'].loc['USA','geometry']
        )
        | (routes_cs.length == 0)
    )]
    routes_cs['distance_m'] = routes_cs.length
    routes_cs['miles'] = (routes_cs['distance_m'] / 1609.34).round(2)

    return routes_cs


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

#%% Limits on PRMTRADE across nercr boundaries
if not int(sw.GSw_PRM_NetImportLimit):
    ## No limit
    firm_import_limit = pd.DataFrame(columns=['*nercr','t','fraction']).set_index(['*nercr','t'])
else:
    limits = pd.Series(
        {int(i.split('_')[0]): i.split('_')[1] for i in sw.GSw_PRM_NetImportLimitScen.split('/')}
    )

    solveyears = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv')
    ).columns.astype(int).tolist()
    startyear = min(solveyears)
    endyear = max(solveyears)
    allyears = range(startyear, max(endyear, limits.index.max())+1)

    ## calculate the historical net_firm_import fraction for each region and drop negative values
    peak_net_imports = pd.read_csv(
        os.path.join(inputs_case,'peak_net_imports.csv'),
        index_col=['nercr']
    )
    net_firm_import_frac = (
        peak_net_imports.MW / peak_net_imports.MW_TotalDemand
    ).clip(lower=0)
    nercrs = net_firm_import_frac.index

    _dfout = {}
    for key, val in limits.items():
        ## If 'hist' is in GSw_PRM_NetImportLimitScen,
        ## all years up until that year use the historical regional max
        if val == 'hist':
            for y in range(startyear, key+1):
                _dfout[y] = net_firm_import_frac
        ## If 'histmax', all prior years use the historical max across all regions
        elif val == 'histmax':
            for y in range(startyear, key+1):
                _dfout[y] = net_firm_import_frac.clip(lower=net_firm_import_frac.max())
        else:
            ## Input values are percentages so convert to fractions
            _dfout[key] = pd.Series(index=nercrs, data=float(val) / 100)

    firm_import_limit = (
        pd.concat(_dfout, names=('t',)).unstack('nercr')
        ## Linear interpolation between values; flat projections before and after
        .reindex(allyears).interpolate('linear').bfill().ffill()
        .loc[solveyears]
        .unstack('t').rename('fraction').rename_axis(['*nercr','t'])
    )

firm_import_limit.to_csv(os.path.join(inputs_case, 'firm_import_limit.csv'))


#%% Load the transmission scalars
scalars = reeds.io.get_scalars(inputs_case)
### Get the contingency levels for energy and PRM trading
nlevel = {
    'energy': int(scalars['trans_contingency_level_energy']),
    'prm': int(scalars['trans_contingency_level_prm']),
    'transgroup': int(scalars['trans_contingency_level_transgroup']),
    'itlgrp': int(scalars['trans_contingency_level_itlgrp']),
}
### Put some in dicts for easier access
tranloss_permile = {
    'AC': scalars['tranloss_permile_ac'],
    ### B2B converters are AC-AC/DC-DC/AC-AC, so use AC per-mile losses
    'B2B': scalars['tranloss_permile_ac'],
    'LCC': scalars['tranloss_permile_dc'],
    'VSC': scalars['tranloss_permile_dc'],
}
tranloss_fixed = {
    'AC': 1 - scalars['converter_efficiency_ac'],
    'B2B': 1 - scalars['converter_efficiency_lcc'],
    'LCC': 1 - scalars['converter_efficiency_lcc'],
    'VSC': 1 - scalars['converter_efficiency_vsc'],
}


#%% Get single-link distances and losses
interface_params = pd.read_csv(
    os.path.join(inputs_case,'transmission_distance.csv'),
)
interface_params['r_rr'] = interface_params.r + '_' + interface_params.rr

# Apply the distance multiplier
interface_params['miles'] = interface_params['miles'] * float(sw.GSw_TransSquiggliness)

# Make sure there are no duplicates
if interface_params[['r','rr']].duplicated().sum():
    print(
        interface_params.loc[
            interface_params[['r','rr']].duplicated(keep=False)
        ].sort_values(['r','rr'])
    )
    raise Exception('Duplicate entries in transmission_distance.csv')

### Calculate losses
def getloss(row, trtype='AC'):
    """
    Fixed losses are entered as per-endpoint values (e.g. for each AC/DC converter station
    on a LCC DC line). There are two endpoints per line, so multiply fixed losses by 2.
    Note that this approach only applies for LCC DC lines; VSC AC/DC losses are applied later.
    """
    return row.miles * tranloss_permile[trtype] + tranloss_fixed[trtype] * 2

trtypes = ['AC', 'LCC', 'B2B', 'VSC']
interface_params = pd.concat(
    {
        trtype:
        interface_params.assign(loss=interface_params.apply(getloss, args=(trtype,), axis=1))
        for trtype in trtypes
    },
    axis=0,
    names=('trtype',),
).reset_index(level='trtype').set_index(['r','rr','trtype'])


#%% Include distances for existing lines
transmission_distance = interface_params.miles.copy()

#%% Write the line-specific transmission FOM costs [$/MW/year]
trans_fom_region_mult = int(scalars['trans_fom_region_mult'])
trans_fom_frac = scalars['trans_fom_frac']

### For simplicity we just take the unweighted average base cost across
### the four regions for which we have transmission cost data.
### Future work should identify a better assumption.
rev_transcost_base = pd.read_csv(
    os.path.join(inputs_case,'rev_transmission_basecost.csv'),
    header=[0], skiprows=[1],
).replace({'500ACsingle':'AC','500DCbipole':'LCC'}).set_index('Voltage')

transfom_USDperMWmileyear = {
    trtype: (
        rev_transcost_base.loc[trtype][['TEPPC','SCE','MISO','Southeast']].mean()
        * trans_fom_frac
    )
    for trtype in ['AC','LCC']
}
### B2B is treated like (AC line)-(AC/DC converter)-(AC/DC converter)-(AC line) so uses AC line FOM
transfom_USDperMWmileyear['B2B'] = transfom_USDperMWmileyear['AC']
transfom_USDperMWmileyear['VSC'] = transfom_USDperMWmileyear['LCC']

if trans_fom_region_mult:
    ### Multiply line-specific $/MW by FOM fraction to get $/MW/year
    transmission_line_fom = interface_params[costcol] * trans_fom_frac
    ### Use regional average * distance_initial for existing lines
    append = transmission_distance.loc[
        transmission_distance.reset_index().trtype.isin(
            ['AC','LCC','B2B','VSC']).set_axis(transmission_distance.index)
    ]
else:
    ### Multiply $/MW/mile/year by distance [miles] to get $/MW/year for ALL lines
    transmission_line_fom = (
        transmission_distance.reset_index().trtype.map(transfom_USDperMWmileyear)
        * transmission_distance.values
    ).set_axis(transmission_distance.index).rename('USDperMWyear')


#%%### Write files for ReEDS (adding * to make GAMS read column names as comment)
### transmission_distance
transmission_distance.round(3).reset_index().rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'transmission_miles.csv'), index=False)

### tranloss
tranloss = interface_params['loss'].reset_index()
tranloss.round(decimals).rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'tranloss.csv'), index=False, header=True)

### transmission_line_fom
transmission_line_fom.round(2).rename_axis(('*r','rr','trtype')).to_csv(
    os.path.join(inputs_case,'transmission_line_fom.csv'))

#%% Write the initial capacities
for captype, level in [
    ('energy', 'r'),
    ('prm', 'r'),
    ('transgroup', 'transgrp'),
    ('itlgrp','itlgrp'),
]:
    trancap_init = get_trancap_init(
        valid_regions=valid_regions, networksource=sw.GSw_TransNetworkSource, level=level)
    trancap_init[nlevel[captype]].rename(columns={level:'*'+level}).round(3).to_csv(
        os.path.join(inputs_case,f'trancap_init_{captype}.csv'),
        index=False,
    )


#%%### Future transmission capacity
## note that '0' is used as a filler value in the t column for firstyear_trans, which is defined
## in inputs/scalars.csv. So we replace it whenever we load a transmission_capacity_future file.
trancap_fut = (
    pd.concat(
        [
            pd.read_csv(
                os.path.join(inputs_case, 'transmission_capacity_future_baseline.csv'),
                comment='#',
            ),
            pd.read_csv(
                os.path.join(inputs_case, 'transmission_capacity_future.csv'),
                comment='#',
            )
        ],
        axis=0,
        ignore_index=True,
    )
    .astype({'t': int})
    .drop(['Notes', 'notes', 'Note', 'note'], axis=1, errors='ignore')
    .replace({'t': {0: int(scalars['firstyear_trans_longterm'])}})
)

### Drop prospective AC lines from years <= trans_init_year
trancap_fut = trancap_fut.drop(
    trancap_fut.loc[
        (trancap_fut.t <= trans_init_year)
        & (trancap_fut.trtype == 'AC')
    ].index,
).copy()

trancap_fut.rename(columns={'r':'*r'}).astype({'t':int}).round(3).to_csv(
    os.path.join(inputs_case,'trancap_fut.csv'), index=False)


#%%### Transmission upgrade supply curve
transmission_cost_ac = pd.read_csv(
    os.path.join(inputs_case, 'transmission_cost_ac.csv')
)
### Interfaces are always defined with the zones sorted in lexicographic order
reverse_interfaces = transmission_cost_ac.loc[
    transmission_cost_ac.apply(lambda row: row.r > row.rr, axis=1)
]
for i, row in reverse_interfaces.iterrows():
    transmission_cost_ac.loc[i, ['r', 'rr']] = transmission_cost_ac.loc[i, ['rr', 'r']].values
    transmission_cost_ac.loc[i, ['USD2004perMW_forward', 'USD2004perMW_reverse']] = (
        transmission_cost_ac.loc[i, ['USD2004perMW_reverse', 'USD2004perMW_forward']].values
    )

_test = transmission_cost_ac.apply(lambda row: row.r < row.rr, axis=1)
if not _test.all():
    print(transmission_cost_ac.loc[~_test])
    err = (
        "Must have r < rr in AC transmission cost inputs but the interfaces "
        "listed above are out of order"
    )
    raise ValueError(err)

labels = {
    'binwidth_USD2004': 'binwidth',
    'USD2004perMW_forward': 'forward',
    'USD2004perMW_reverse': 'reverse',
}
for col, label in labels.items():
    transmission_cost_ac[['r','rr','tscbin',col]].rename(columns={'r':'*r'}).round(2).to_csv(
        os.path.join(inputs_case, f'tsc_{label}.csv'),
        index=False,
    )
transmission_cost_ac.tscbin.drop_duplicates().to_csv(
    os.path.join(inputs_case, 'tscbin.csv'),
    index=False,
    header=False,
)


#%% DC and B2B transmission cost
## Get DC line cost
transmission_cost_dc = pd.read_csv(os.path.join(inputs_case, 'transmission_cost_dc.csv'))

## B2B is: (zone center)--------(AC/DC converter)(DC/AC converter)--------(zone center)
##                         ^ AC line                                 ^ AC line
## so use AC per-mile costs.
trancap_init = get_trancap_init(
    valid_regions=valid_regions,
    networksource=sw.GSw_TransNetworkSource,
)[0]
b2b_links = trancap_init.loc[
    (trancap_init.trtype=='B2B')
    & (trancap_init.r < trancap_init.rr)
].set_index(['r','rr']).index
## Take the weighted average of the whole supply curve (for the default 500 kV assumption
## the supply curve only has one bin per interface, so it doesn't matter; when we add the
## full supply curve, we'll need to include entries for these B2B-containing interfaces).
df = transmission_cost_ac.set_index(['r','rr']).loc[b2b_links].copy()
df['cost_weighted'] = (
    df.binwidth_USD2004
    * df.USD2004perMW_forward
)
transmission_cost_b2b = (
    df.groupby(['r','rr','tscbin']).cost_weighted.sum()
    / df.groupby(['r','rr','tscbin']).binwidth_USD2004.sum()
).reset_index(level='tscbin', drop=True).rename('USD2004perMW').reset_index()
## Add the reverse direction and write it
transmission_cost_b2b = pd.concat([
    transmission_cost_b2b,
    transmission_cost_b2b.rename(columns={'r':'rr', 'rr':'r'})
])

### Write the combined cost table
transmission_cost_nonac = (
    pd.concat({
        'LCC': transmission_cost_dc,
        'B2B': transmission_cost_b2b,
        'VSC': transmission_cost_dc,
    }, names=('trtype','drop'))
    .reset_index('drop', drop=True)
    .reset_index()
    .rename(columns={'r':'*r'})
    [['*r','rr','trtype','USD2004perMW']]
)
transmission_cost_nonac.round(2).to_csv(
    os.path.join(inputs_case, 'transmission_cost_nonac.csv'),
    index=False,
)


#%%### Hurdle rates
hurdle_levels = [1, 2]
cost_hurdle_intra = (
    pd.read_csv(os.path.join(inputs_case, 'cost_hurdle_intra.csv'))
    .rename(columns={'t':'*t'}).set_index('*t').round(3)
)
cost_hurdle_rate = {
    i: (
        cost_hurdle_intra[sw[f'GSw_TransHurdleLevel{i}']] if int(sw.GSw_TransHurdleRate)
        else pd.Series(name='region').rename_axis('*t')
    )
    for i in hurdle_levels
}
for i in hurdle_levels:
    cost_hurdle_rate[i].to_csv(os.path.join(inputs_case, f'cost_hurdle_rate{i}.csv'))


#%%### H2 pipeline cost multipliers
# Calculate H2 pipeline cost multipliers by dividing the [$/mile] cost of DC transmission
# between each pair of regions by the minimum interface [$/mile] cost for DC transmission
# and subtracting 1 to get a fractional adder (which is then added to 1 in b_inputs.gms)
fpath = os.path.join(inputs_case, 'pipeline_cost_mult.csv')
if len(transmission_cost_nonac):
    dc_cost_permile = (
        transmission_cost_nonac.rename(columns={'*r':'r'})
        .set_index(['trtype','r','rr']).loc['LCC'].squeeze(1)
        / interface_params.xs('LCC', 0, 'trtype').miles
    )
    pipeline_cost_mult = dc_cost_permile.rename('multiplier') / dc_cost_permile.min() - 1

    pipeline_cost_mult.reset_index().rename(columns={'r':'*r'}).round(3).to_csv(
        fpath,
        index=False,
    )
else:
    pd.DataFrame(columns=['*r','rr','multiplier']).to_csv(fpath, index=False)


# Get model regions
dfzones = reeds.io.get_dfmap(
    os.path.dirname(inputs_case),
    levels=['r'],
    exclude_water_areas=True
)['r']

#%%### Adjacent regions
# Determine which pairs of model regions are adjacent to each other
routes_adjacent = calculate_adjacent_routes(dfzones)
routes_adjacent.to_csv(
    os.path.join(inputs_case,'routes_adjacent.csv'),
    index=False
)

#%%### CO2 storage sites
# Determine spurline routes from model regions to carbon storage sites
co2_storage_sites = reeds.io.get_co2_storage_sites()
routes_cs = calculate_co2_storage_routes(dfzones, co2_storage_sites)
routes_cs[['*r', 'cs']].to_csv(
    os.path.join(inputs_case, 'r_cs.csv'), index=False
)
routes_cs[['*r', 'cs', 'miles']].to_csv(
    os.path.join(inputs_case,'r_cs_distance_mi.csv'),
    index=False
)

# Determine sites that have valid routes to model regions
val_cs = pd.Series(routes_cs['cs'].unique())
val_cs.to_csv(os.path.join(inputs_case, 'val_cs.csv'), header=False, index=False)

# Subset CO2 site characteristics data to valid sites
co2_site_char = pd.read_csv(os.path.join(inputs_case, 'co2_site_char.csv'))
co2_site_char = co2_site_char.loc[co2_site_char['cs'].isin(val_cs)]
co2_site_char.to_csv(os.path.join(inputs_case, 'co2_site_char.csv'), index=False)

# Create WKT file of region-to-site spurlines
r_cs_spurlines = (
    routes_cs.loc[routes_cs['distance_m'] > 0]
    .rename(columns={'*r': 'ba_str', 'cs': 'FmnID'})
    .to_crs('EPSG:4326')
    .assign(WKT=lambda x: x['geometry'].to_wkt())
    [['ba_str', 'FmnID', 'distance_m', 'WKT']]
)
r_cs_spurlines.to_csv(
    os.path.join(inputs_case,'ctus_r_cs_spurlines_200mi.csv'),
    index=False
)

#%% Finish the timer
reeds.log.toc(tic=tic, year=0, process='input_processing/transmission.py',
    path=os.path.join(inputs_case,'..'))
print('Finished transmission.py', flush=True)
