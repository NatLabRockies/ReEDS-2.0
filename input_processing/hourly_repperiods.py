"""
The purpose of this script is to collect 8760 data as it is output by
hourlize and perform a temporal aggregation to produce load and capacity 
factor parameters for the representative days that will be read by ReEDS. 
The other outputs are the hours/seasons to be modeled in ReEDS and linking 
sets used in the model.

General notes:
* h: a timeslice with an h prefix, starting at h1
* hour: an hour of the full period, starting at 1 ([1-8760] for 1 year or [1-61320] for 7 years)
* dayhour: a clock hour starting at 1 [1-24]
* period: a day (if GSw_HourlyType=='day') or a wek (if GSw_HourlyType=='wek')
* wek: A consecutive 5-day period (365 is only divisible by 1, 5, 73, and 365)

This script is currently not compatible with:
* Climate impacts (climateprep.py)
* Beyond-2050 modeling (forecast.py)
* Flexible demand
"""

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import argparse
import json
import numpy as np
import os
import sys
import datetime
import pandas as pd
import scipy
import sklearn.cluster
import sklearn.neighbors
import traceback
import hourly_writetimeseries
import hourly_plots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
## Time the operation of this script
tic = datetime.datetime.now()


#%%#################
### FIXED INPUTS ###

decimals = 3
### Whether to show plots interactively [default False]
interactive = False
### Full possible collection of weather years
all_weatheryears = list(range(2007,2014)) + list(range(2016,2024))
### VRE techs considered for GSw_PRM_StressSeedMinRElevel and GSw_HourlyMinRElevel
techs_min_vre = ['upv', 'wind-ons']

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def szn2yearperiod(szn):
    """
    szn's are formatted as 'y{20xx}{d or w}{day of year or wek of year}'
    where a 'wek' is a 5-day period (5*73 = 365)
    """
    year, period = szn.split('d') if 'd' in szn else szn.split('w')
    return int(year.strip('y')), int(period)


def szn2period(szn):
    """
    szn's are formatted as 'y{20xx}{d or w}{day of year or wek of year}'
    where a 'wek' is a 5-day period (5*73 = 365)
    """
    year, period = szn.split('d') if 'd' in szn else szn.split('w')
    return int(period)


###############################
#    -- Load Processing --    #
###############################

def get_load(inputs_case, keep_modelyear=None, keep_weatheryears=[2012]):
    """
    """
    ### Subset to modeled regions
    load = reeds.io.read_file(os.path.join(inputs_case,'load.h5'), parse_timestamps=True)
    ### Subset to keep_modelyear if provided
    if keep_modelyear:
        load = load.loc[keep_modelyear].copy()
    ### load.h5 is busbar load, but b_inputs.gms ingests end-use load, so scale down by distloss
    scalars = reeds.io.get_scalars(inputs_case)
    load *= (1 - scalars['distloss'])

    ### Downselect to weather years if provided
    if isinstance(keep_weatheryears, list):
        load = load.loc[load.index.year.isin(keep_weatheryears)]

    return load


def optimize_period_weights(profiles_fitperiods, numclusters=100):
    """
    The optimization approach (minimizing sum of absolute errors) is described at
    https://optimization.mccormick.northwestern.edu/index.php/Optimization_with_absolute_values
    The general idea of optimizing period weights to reproduce regional variability is similar
    to the method used in the EPRI US-REGEN model, described at
    https://www.epri.com/research/products/000000003002016601
    """
    ### Imports
    import pulp

    ### Input processing
    profiles_day = (
        profiles_fitperiods.groupby(['property','region'], axis=1).mean())
    profiles_mean = profiles_day.mean()
    numdays = len(profiles_day)
    days = profiles_day.index.values

    ### Optimization: minimize sum of absolute errors
    m = pulp.LpProblem('LinearDaySelection', pulp.LpMinimize)
    ###### Variables
    ### day weights
    WEIGHT = pulp.LpVariable.dicts('WEIGHT', (d for d in days), lowBound=0, cat='Continuous')
    ### errors
    ERROR_POS = pulp.LpVariable.dicts(
        'ERROR_POS', (c for c in profiles_day.columns), lowBound=0, cat='Continuous')
    ERROR_NEG = pulp.LpVariable.dicts(
        'ERROR_NEG', (c for c in profiles_day.columns), lowBound=0, cat='Continuous')
    ###### Constraints
    ### weights must sum to 1
    m += pulp.lpSum([WEIGHT[d] for d in days]) == 1
    ### definition of errors
    for c in profiles_day.columns:
        m += (
            ### Full error for column (given by positive component minus negative component)...
            ERROR_POS[c] - ERROR_NEG[c]
            ### ...plus sum of values for weighted representative days...
            + pulp.lpSum([WEIGHT[d] * profiles_day[c][d] for d in days])
            ### ...equals the mean for that column
            == profiles_mean[c])
    ###### Objective: minimize the sum of absolute values of errors across all columns
    m += pulp.lpSum([
        ERROR_POS[c] + ERROR_NEG[c]
        for c in profiles_day.columns
    ])

    ### Solve it
    m.solve(solver=pulp.PULP_CBC_CMD(msg=True))

    ### Collect weights, scaled by total number of days
    weights = pd.Series({d:WEIGHT[d].varValue for d in days}) * numdays

    ### Truncate based on numclusters, scale appropriately, and convert to integers
    ### Keep the the 'numclusters' highest-weighted days
    rweights = (weights.sort_values(ascending=False)[:numclusters])
    ### Scale so that the weights sum to numdays (have to do if numclusters is small)
    rweights *= numdays / rweights.sum()
    ### Convert to integers
    iweights = rweights.round(0).astype(int)
    ### Scale all weights little by little until they sum to number of actual days
    sumweights = iweights.sum()
    diffweights = sumweights - numdays
    increment = 0.00001 * (1 if diffweights < 0 else -1)
    for i in range(1000000):
        iweights = (rweights * (1 + increment*i)).round(0).astype(int)
        if iweights.sum() == numdays:
            break

    iweights = iweights.replace(0,np.nan).dropna().astype(int)
    ### Make sure it worked
    if iweights.sum() != numdays:
        raise ValueError(f'Sum of rounded weights = {iweights.sum()} != {numdays}')

    return profiles_day, iweights, weights


def assign_representative_days(profiles_day, rweights):
    """
    """
    ### Imports
    import pulp

    ### Input processing
    actualdays = profiles_day.index.values
    repdays = list(rweights.index)

    ### Optimization: minimize sum of absolute errors
    m = pulp.LpProblem('RepDayAssignment', pulp.LpMinimize)
    ###### Variables
    ### Weighting of rep days (r) for each actual day (a).
    ### Can only use whole days, so it's a binary variable.
    WEIGHT = pulp.LpVariable.dicts(
        'WEIGHT', ((a,r) for a in actualdays for r in repdays),
        lowBound=0, upBound=1, cat=pulp.LpInteger)
    ### Errors. These are defined for features (c) and for actual days (a).
    ERROR_POS = pulp.LpVariable.dicts(
        'ERROR_POS', ((a,c) for a in actualdays for c in profiles_day.columns),
        lowBound=0, cat='Continuous')
    ERROR_NEG = pulp.LpVariable.dicts(
        'ERROR_NEG', ((a,c) for a in actualdays for c in profiles_day.columns),
        lowBound=0, cat='Continuous')
    ###### Constraints
    ### Each actual day can only be assigned to one representative day
    for a in actualdays:
        m += pulp.lpSum([WEIGHT[a,r] for r in repdays]) == 1
    ### Each representative day must be used a number of times equal to its weight
    for r in repdays:
        m += pulp.lpSum([WEIGHT[a,r] for a in actualdays]) == rweights[r]
    ### Define the error variables
    for a in actualdays:
        for c in profiles_day.columns:
            m += (
                ### Full error for column on actual day (given by positive
                ### component minus negative component)...
                ERROR_POS[a,c] - ERROR_NEG[a,c]
                ### ...plus value for its representative day (since WEIGHT is binary)...
                + pulp.lpSum([WEIGHT[a,r] * profiles_day[c][r] for r in repdays])
                ### ...equals the actual value for that column and day
                == profiles_day[c][a])
    ###### Objective: minimize the sum of absolute values of errors
    m += pulp.lpSum([
        ERROR_POS[a,c] + ERROR_NEG[a,c]
        for a in actualdays for c in profiles_day.columns
    ])

    ### Solve it
    m.solve(solver=pulp.PULP_CBC_CMD(msg=True))

    ### Collect assignments
    assignments = pd.Series(
        {(a,r):WEIGHT[a,r].varValue for a in actualdays for r in repdays}).astype(int)
    assignments.index = assignments.index.rename(['act','rep'])
    a2r = assignments.replace(0,np.nan).dropna().reset_index(level='rep').rep

    return a2r


def identify_peak_containing_periods(df, hierarchy, level):
    """
    Identify the period containing the peak value.
    Set of (region,reason,year,yperiod), with yperiod starting from 1.
    """
    ### Map columns to level, then sum
    if level == 'r':
        rmap = pd.Series(hierarchy.index, index=hierarchy.index)
    else:
        rmap = hierarchy[level]
    dfmod = df.copy()
    dfmod.columns = dfmod.columns.map(lambda x: x.split('|')[-1]).map(rmap)
    dfmod = dfmod.groupby(axis=1, level=0).sum()
    ### Get the max value by (year,yperiod)
    dfmax = dfmod.groupby(['year','yperiod']).max()
    ### Get the max (year,yperiod) for each column
    forceperiods = set([(c, 'peak-containing', *dfmax[c].nlargest(1).index[0]) for c in dfmax])

    return forceperiods


def identify_min_periods(df, hierarchy, rmap1, level, prefix=''):
    """
    Identify the period with the minimum average value.
    Set of (region,reason,year,yperiod), with yperiod starting from 1.
    """
    ### Map columns to level, then sum
    if level == 'r':
        rmap2 = pd.Series(hierarchy.index, index=hierarchy.index)
    else:
        rmap2 = hierarchy[level]
    dfmod = df[[c for c in df if c.startswith(prefix)]].copy()
    dfmod.columns = dfmod.columns.map(lambda x: x.split('|')[-1]).map(rmap1).map(rmap2)
    dfmod = dfmod.groupby(axis=1, level=0).sum()
    ### Get the mean value by (year,yperiod)
    dfmean = dfmod.groupby(['year','yperiod']).mean()
    ### Get the min (year,yperiod) for each column
    forceperiods = set([(c, 'min average', *dfmean[c].nsmallest(1).index[0]) for c in dfmean])

    return forceperiods



###########################
#    -- Clustering --     #
###########################

def cluster_profiles(profiles_fitperiods, sw, forceperiods_yearperiod):
    """
    Cluster the load and (optionally) RE profiles to find representative days for dispatch in ReEDS.

    Args:
        GSw_HourlyClusterRegionLevel: Level of inputs/hierarchy.csv at which to aggregate
        profiles for clustering. VRE profiles are converted to available-capacity-weighted
        averages. That's not the best - it would be better to weight sites that are more likely
        to be developed more strongly - but it's better than not weighting at all.

    Returns:
        cf_representative - hourly profile of centroid or medoid capacity factor values
                            for all regions and technologies
        load_representative - hourly profile of centroid or medoid load values for all regions
    period_szn - day indices of each cluster center
    """
    ###### Run the clustering
    print(f"Performing {sw.GSw_HourlyClusterAlgorithm} clustering")
    if (
        sw['GSw_HourlyClusterAlgorithm'].startswith('hierarchical')
        or sw['GSw_HourlyClusterAlgorithm'].lower().startswith('kme')
    ):
        if sw['GSw_HourlyClusterAlgorithm'].startswith('hierarchical'):
            args = sw['GSw_HourlyClusterAlgorithm'].split('_')
            if len(args) > 1:
                metric = args[1]
                linkage = args[2]
            else:
                metric = 'euclidean'
                linkage = 'ward'
            clusters = sklearn.cluster.AgglomerativeClustering(
                n_clusters=int(sw['GSw_HourlyNumClusters']),
                metric=metric, linkage=linkage,
            )
        elif sw['GSw_HourlyClusterAlgorithm'].lower().startswith('kmeans'):
            clusters = sklearn.cluster.KMeans(
                n_clusters=int(sw['GSw_HourlyNumClusters']),
                random_state=0, n_init='auto', max_iter=1000,
            )
        elif sw['GSw_HourlyClusterAlgorithm'].lower().startswith('kmedoids'):
            import sklearn_extra.cluster
            args = sw['GSw_HourlyClusterAlgorithm'].split('_')
            if len(args) > 1:
                metric = args[1]
                init = args[2]
            else:
                metric = 'euclidean'
                init = 'heuristic'
            clusters = sklearn_extra.cluster.KMedoids(
                n_clusters=int(sw['GSw_HourlyNumClusters']),
                metric=metric, init=init, method='pam',
                max_iter=1000, random_state=0,
            )
        ### Generate the fits
        idx = clusters.fit_predict(profiles_fitperiods)
        ### Get nearest period to each centroid
        centroids = pd.DataFrame(
            sklearn.neighbors.NearestCentroid().fit(profiles_fitperiods, idx).centroids_,
            columns=profiles_fitperiods.columns,
        )
        nearest_period = {
            i:
            profiles_fitperiods.loc[:,idx==i,:].apply(
                lambda row: scipy.spatial.distance.euclidean(row, centroids.loc[i]),
                axis=1
            ).nsmallest(1).index[0]
            for i in range(int(sw['GSw_HourlyNumClusters']))
        }

        period_szn = pd.DataFrame({
            'period': profiles_fitperiods.index.values,
            'szn': [f"y{i[0]}{sw['GSw_HourlyType'][0]}{i[1]:>03}"
                       for i in pd.Series(idx).map(nearest_period)]
        ### Add the force-include periods to the end of the list of seasons
        })
        period_szn = pd.concat([
            period_szn,
            pd.DataFrame({
                'period': list(forceperiods_yearperiod),
                'szn': [f"y{i[0]}{sw['GSw_HourlyType'][0]}{i[1]:>03}"
                        for i in forceperiods_yearperiod]
            })
        ]).sort_values('period').set_index('period').szn

    elif sw['GSw_HourlyClusterAlgorithm'] in ['opt','optimized','optimize']:
        ### Optimize the weights of representative days
        profiles_day, rweights, weights = optimize_period_weights(
            profiles_fitperiods=profiles_fitperiods, numclusters=int(sw['GSw_HourlyNumClusters']))
        ### Optimize the assignment of actual days to representative days
        a2r = assign_representative_days(profiles_day=profiles_day.round(4), rweights=rweights)

        if len(rweights) < int(sw['GSw_HourlyNumClusters']):
            print(
                'Asked for {} representative periods but only needed {}'.format(
                    sw['GSw_HourlyNumClusters'], len(rweights)))

        period_szn = pd.concat([
            a2r.reset_index().rename(columns={'act':'period','rep':'szn'}),
            pd.DataFrame({'period':list(forceperiods_yearperiod),
                          'szn':list(forceperiods_yearperiod)})
            if len(forceperiods_yearperiod) else None
        ]).sort_values('period').set_index('period').szn
        period_szn = period_szn.map(lambda x: f'y{x[0]}{sw.GSw_HourlyType[0]}{x[1]:>03}')

    elif 'user' in sw['GSw_HourlyClusterAlgorithm'].lower():
        print('Using user-defined representative period weights')
        period_szn = pd.read_csv(
            os.path.join(inputs_case,'period_szn_user.csv')
        ).set_index('actual_period').rep_period.rename('szn')
        period_szn.index = period_szn.index.map(szn2yearperiod).values
        period_szn.index = period_szn.index.rename('period')


    ### Get the list of representative periods for convenience
    rep_periods = sorted(period_szn.map(szn2yearperiod).unique())

    return rep_periods, period_szn


def make_timestamps(sw):
    ### Get some useful constants
    hoursperperiod = {'day':24, 'wek':120, 'year':24}
    periodsperyear = {'day':365, 'wek':73, 'year':365}

    ### Get map from yperiod, hour, and h_of_period to timestamp
    timestamps = pd.DataFrame({
        'year': np.ravel([[y]*8760 for y in all_weatheryears]),
        'h_of_year': np.ravel([list(range(1,8761)) * len(all_weatheryears)]),
        'h_of_period': np.ravel(
            [f'{h+1:>03}' for h in range(hoursperperiod[sw['GSw_HourlyType']])]
            * periodsperyear[sw['GSw_HourlyType']] * len(all_weatheryears)),
        'yperiod': np.ravel(
            [p+1 for p in range(periodsperyear[sw['GSw_HourlyType']])
             for h in range(hoursperperiod[sw['GSw_HourlyType']])]
            * len(all_weatheryears)),
        'h_of_day': np.ravel(
            [f'{h+1:>03}' for h in range(hoursperperiod['day'])]
            * periodsperyear['day'] * len(all_weatheryears)),
        'yday': np.ravel(
            [p+1 for p in range(periodsperyear['day'])
             for h in range(hoursperperiod['day'])]
            * len(all_weatheryears)),
        'h_of_wek': np.ravel(
            [f'{h+1:>03}' for h in range(hoursperperiod['wek'])]
            * periodsperyear['wek'] * len(all_weatheryears)),
        'ywek': np.ravel(
            [p+1 for p in range(periodsperyear['wek'])
             for h in range(hoursperperiod['wek'])]
            * len(all_weatheryears)),
    })
    timestamps['timestamp'] = (
        'y' + timestamps.year.astype(str)
        ## d for day and w for wek 
        + ('w' if sw.GSw_HourlyType == 'wek' else 'd')
        + timestamps.yperiod.astype(str).map('{:>03}'.format)
        + 'h' + timestamps.h_of_period
    )
    timestamps['period'] = timestamps['timestamp'].map(lambda x: x.split('h')[0])
    timestamps['day'] = (
        'y' + timestamps.year.astype(str)
        + 'd' + timestamps.yday.astype(str).map('{:>03}'.format)
    )
    timestamps['wek'] = (
        'y' + timestamps.year.astype(str)
        + 'w' + timestamps.ywek.astype(str).map('{:>03}'.format)
    )
    timestamps.index = np.ravel([
        pd.date_range(
            f'{y}-01-01', f'{y+1}-01-01',
            freq='H', inclusive='left', tz='Etc/GMT+6',
        )[:8760]
        for y in all_weatheryears
    ])

    return timestamps


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================

def main(
    sw,
    reeds_path,
    inputs_case,
    periodtype='rep',
    minimal=0,
):
    """
    """
    #%% Parse inputs if necessary
    if not isinstance(sw['GSw_HourlyClusterWeights'], pd.Series):
        sw['GSw_HourlyClusterWeights'] = pd.Series(json.loads(
            '{"'
            + (':'.join(','.join(sw['GSw_HourlyClusterWeights'].split('/')).split('_'))
            .replace(':','":').replace(',',',"'))
            +'}'
        ))
        sw['GSw_HourlyClusterWeights'].index = sw['GSw_HourlyClusterWeights'].index.rename('property')
        sw['GSw_HourlyClusterWeights'] = (
            sw['GSw_HourlyClusterWeights'].loc[sw['GSw_HourlyClusterWeights'] != 0]
        ).copy()
    if not isinstance(sw['GSw_HourlyWeatherYears'], list):
        sw['GSw_HourlyWeatherYears'] = [int(y) for y in sw['GSw_HourlyWeatherYears'].split('_')]
    if not isinstance(sw['GSw_CSP_Types'], list):
        sw['GSw_CSP_Types'] = [int(i) for i in sw['GSw_CSP_Types'].split('_')]
    ## VRE techs that can be used for profiles
    techs_vre = ['upv', 'wind-ons', 'wind-ofs'] if int(sw.GSw_OfsWind) else ['upv', 'wind-ons']

    #%% Direct plots to outputs folder
    figpath = os.path.join(inputs_case,'..', 'outputs', 'figures')
    os.makedirs(figpath, exist_ok=True)
    os.makedirs(os.path.join(inputs_case, periodtype), exist_ok=True)

    val_r_all = pd.read_csv(
        os.path.join(inputs_case, 'val_r_all.csv'), header=None).squeeze(1).tolist()
    modelyears = pd.read_csv(
        os.path.join(inputs_case, 'modeledyears.csv')).columns.astype(int)
    # Use agglevel_variables function to obtain spatial resolution variables 
    agglevel_variables  = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)

    #%% Get map from yperiod, hour, and h_of_period to timestamp
    timestamps = make_timestamps(sw)
    timestamps_myr = timestamps.loc[timestamps.year.isin(sw['GSw_HourlyWeatherYears'])].copy()

    ### Get region hierarchy for use with GSw_HourlyClusterRegionLevel
    hierarchy = pd.read_csv(
        os.path.join(inputs_case,'hierarchy.csv')).rename(columns={'*r':'r'}).set_index('r')
    hierarchy_orig = pd.read_csv(
        os.path.join(inputs_case,'hierarchy_original.csv'))
    
    if sw.GSw_HourlyClusterRegionLevel == 'r':
        rmap = pd.Series(hierarchy_orig.index, index=hierarchy_orig.index)
    elif agglevel_variables['agglevel'] == 'county' or 'county' in agglevel_variables['agglevel']:
        rmap = hierarchy[sw['GSw_HourlyClusterRegionLevel']]
    elif agglevel_variables['agglevel'] in ['ba','aggreg']:
        rmap = (hierarchy_orig.loc[hierarchy_orig['ba'].isin(val_r_all)]
                [['aggreg',sw['GSw_HourlyClusterRegionLevel']]]
                .drop_duplicates().set_index('aggreg')).squeeze(1)
    ### Get r-to-county map
    r_county = pd.read_csv(
        os.path.join(inputs_case,'r_county.csv'), index_col='county').squeeze(1)
    ### Get r-to-ba map
    r_ba = pd.read_csv(
        os.path.join(inputs_case,'r_ba.csv'), index_col='ba').squeeze(1)

    #%% Load supply curves to use for available capacity weighting
    sc = {
        tech: pd.read_csv(
            os.path.join(inputs_case, f'supplycurve_{tech}.csv')
        ).groupby(['region','class'], as_index=False).capacity.sum()
        for tech in techs_vre
    }
    sc = (
        pd.concat(sc, names=['tech','drop'], axis=0)
        .reset_index(level='drop', drop=True).reset_index())
    ### Downselect to modeled regions
    sc = sc.loc[sc.region.isin(val_r_all)].copy()
    sc['i'] = sc.tech+'_'+sc['class'].astype(str)
    sc['resource'] = sc.i + '|' + sc.region
    sc['aggreg'] = sc.region.map(rmap)

    #%%### Load RE CF data, then take available-capacity-weighted average by (tech,region)
    print("Collecting 8760 capacity factor data")
    recf = reeds.io.read_file(os.path.join(inputs_case, 'recf.h5'), parse_timestamps=True)
    ### Downselect to techs used for rep-period selection
    recf = recf[[c for c in recf if any([c.startswith(p) for p in techs_vre])]].copy()
    ### Multiply by available capacity for weighted average
    recf *= sc.set_index('resource')['capacity']
    ### Downselect to modeled years, add descriptive time index
    recf = recf.loc[recf.index.year.isin(sw['GSw_HourlyWeatherYears'])]
    recf.index = timestamps_myr.set_index(['year','yperiod','h_of_period']).index

    # rmap1 is used in conjuntion with rmap2 (created in identify_min_periods) 
    # to map regional data from BA/county (depending on desired spatial aggregation) 
    # to the spatial aggregation defined by sw['GSw_HourlyMinRElevel']
    if agglevel_variables['agglevel'] in ['ba','aggreg']:
        rmap1 = r_ba
    elif agglevel_variables['agglevel'] == 'county':
        rmap1 = r_county
    elif agglevel_variables['lvl'] == 'mult':
        rmap1 = r_county

    ### Identify outlying periods if using capacity credit instead of stress periods
    if (int(sw.GSw_PRM_CapCredit)
        and (sw['GSw_HourlyMinRElevel'].lower() not in ['false','none'])):
        forceperiods_minre = {
            tech: identify_min_periods(
                df=recf, hierarchy=hierarchy, rmap1=rmap1,
                level=sw['GSw_HourlyMinRElevel'], prefix=tech)
            for tech in techs_min_vre
        }
    else:
        forceperiods_minre = {tech: set() for tech in techs_min_vre}

    ### Aggregate to (tech,GSw_HourlyClusterRegionLevel)
    recf_agg = recf.copy()
    tmp = (
        pd.DataFrame({'resource':recf.columns}).set_index('resource')
        .merge(sc.set_index('resource')[['tech','region']], left_index=True, right_index=True)
        )
    columns = tmp.loc[tmp.index.isin(recf.columns)]
    recf_agg = recf_agg[tmp.index]
    columns['region'] = columns.region.map(rmap)
    recf_agg.columns = pd.MultiIndex.from_frame(columns[['tech','region']])
    recf_agg = recf_agg.groupby(axis=1, level=['tech','region']).sum()

    ### Divide by aggregated capacity to get back to CF
    recf_agg /= sc.groupby(['tech','aggreg']).capacity.sum().rename_axis(['tech','region'])

    ### Load load data (Eastern time)
    print("Collecting 8760 load data")
    load = get_load(
        inputs_case=inputs_case,
        keep_modelyear=(int(sw['GSw_HourlyClusterYear'])
                  if int(sw['GSw_HourlyClusterYear']) in modelyears
                  else max(modelyears)),
        keep_weatheryears=sw.GSw_HourlyWeatherYears,
    )
    ## Add descriptive index
    load.index = timestamps_myr.set_index(['year','yperiod','h_of_period']).index

    ### Identify outlying periods if using capacity credit instead of stress periods
    if (int(sw.GSw_PRM_CapCredit)
        and (sw['GSw_HourlyPeakLevel'].lower() not in ['false','none'])
    ):
        forceperiods_load = identify_peak_containing_periods(
            df=load, hierarchy=hierarchy, level=sw['GSw_HourlyPeakLevel'])
    else:
        forceperiods_load = set()

    ### Aggregate to GSw_HourlyClusterRegionLevel
    load_agg = load.copy()
    load_agg.columns = load_agg.columns.map(rmap)
    load_agg = load_agg.groupby(axis=1, level=0).sum()
    match sw.GSw_HourlyClusterLoadNorm:
        case 'none':
            ## Don't normalize load
            pass
        case 'regionmax':
            ## Normalize each region to [0,1]
            load_agg /= load_agg.max()
        case 'maxmax':
            ## Divide each region by largest regional max across all regions
            load_agg /= load_agg.max().max()
        case 'maxmin':
            ## Divide each region by smallest regional max across all regions
            load_agg /= load_agg.max().min()
        case _:
            ## Like 'maxmin' but scaled by the provided numeric value
            load_agg /= load_agg.max().min() * float(sw.GSw_HourlyClusterLoadNorm)

    ### Get the full list of forced periods
    forceperiods = forceperiods_load.copy()
    for tech in forceperiods_minre:
        forceperiods.update(forceperiods_minre[tech])
    ## Make a simpler list without the metadata to use for indexing below
    ## (use list(set()) to drop duplicate force-periods)
    forceperiods_yearperiod = list(set([(i[2], i[3]) for i in forceperiods]))
    ### Add number of force-include periods to GSw_HourlyNumClusters for total number of periods
    num_rep_periods = int(sw['GSw_HourlyNumClusters']) + len(forceperiods)
    ### Record the force-included periods
    print('representative periods: {}'.format(sw['GSw_HourlyNumClusters']))
    print('force-include periods: {}'.format(len(forceperiods)))
    print('    peak-load periods: {}'.format(len(forceperiods_load)))
    for tech in forceperiods_minre:
        print('    min-{} periods: {}'.format(tech, len(forceperiods_minre[tech])))
    print('total periods: {}'.format(num_rep_periods))


    forceperiods_write = pd.DataFrame(
        [['load'] + list(i) for i in forceperiods_load]
        + [[k]+list(i) for k,v in forceperiods_minre.items() for i in v],
        columns=['property','region','reason','year','yperiod'],
    )
    forceperiods_write['szn'] = (
        'y' + forceperiods_write.year.astype(str)
        + ('d' if sw.GSw_HourlyType=='year' else sw.GSw_HourlyType[0])
        + forceperiods_write.yperiod.map('{:>03}'.format)
    )
    forceperiods_write.drop_duplicates('szn', inplace=True)

    ### Package profiles into one dataframe
    profiles = pd.concat({
        **{'load': load_agg},
        **{tech: recf_agg[tech] for tech in techs_vre if tech in recf_agg}
    },
        axis=1,
        names=('property', 'region'),
    ).unstack('h_of_period')

    ### Drop forceperiods for clustering
    profiles_fitperiods_hourly = profiles.loc[~profiles.index.isin(forceperiods_yearperiod)].copy()
    ## Normalize the profiles if desired
    if int(sw.GSw_HourlyNormProfiles):
        profiles_fitperiods_hourly /= profiles_fitperiods_hourly.stack('h_of_period').max()

    ### Aggregate from hours to periods if necessary
    if sw.GSw_HourlyClusterTimestep in ['period','day','wek','week']:
        profiles_fitperiods = (
            profiles_fitperiods_hourly.groupby(axis=1, level=['property','region']).mean())
    else:
        profiles_fitperiods = profiles_fitperiods_hourly.copy()

    #%% Plots
    if int(sw.debug):
        try:
            hourly_plots.plot_unclustered_periods(profiles, sw, reeds_path, figpath)
        except Exception as err:
            print('plot_unclustered_periods failed with the following error:\n{}'.format(err))

        try:
            hourly_plots.plot_feature_scatter(profiles_fitperiods, reeds_path, figpath)
        except Exception as err:
            print('plot_feature_scatter failed with the following error:\n{}'.format(err))


    #%%### Determine representative periods
    print("Identify and weight representative periods")
    ## First weight the profiles
    profiles_fitperiods_weighted = (
        profiles_fitperiods
        .multiply(sw.GSw_HourlyClusterWeights, axis=1, level='property')
        .dropna(axis=1, how='all')
    )

    ## Representative days or weeks
    if sw['GSw_HourlyType'] in ['day','wek']:
        rep_periods, period_szn = cluster_profiles(
            profiles_fitperiods=profiles_fitperiods_weighted,
            sw=sw,
            forceperiods_yearperiod=forceperiods_yearperiod,
        )
        print("Clustering complete")

    ## 8760
    elif sw['GSw_HourlyType']=='year':
        ### For 8760 we use the original seasons
        month2quarter = pd.read_csv(
            os.path.join(inputs_case, 'month2quarter.csv'),
            index_col='month',
        ).squeeze(1).map(lambda x: x[:4])

        period_szn = pd.Series(
            index=timestamps_myr.drop_duplicates('yperiod').yperiod.values,
            data=timestamps_myr.drop_duplicates('yperiod').index.month.map(month2quarter),
            name='szn',
        ).rename_axis('period')

        rep_periods = period_szn.index.tolist()
        forceperiods_write = pd.DataFrame(columns=['property','region','reason','year','yperiod'])


    #%%### Identify a (potentially different) collection of periods to use as initial stress periods
    if ((not int(sw.GSw_PRM_CapCredit))
        and (sw['GSw_PRM_StressSeedMinRElevel'].lower() not in ['false','none'])
    ):
        stressperiods_minre = {
            tech: identify_min_periods(
                df=recf, hierarchy=hierarchy, rmap1 = rmap1, level=sw['GSw_PRM_StressSeedMinRElevel'], prefix=tech)
            for tech in techs_min_vre}
    else:
        stressperiods_minre = {tech: set() for tech in techs_min_vre}

    if ((not int(sw.GSw_PRM_CapCredit))
        and (sw['GSw_PRM_StressSeedLoadLevel'].lower() not in ['false','none'])
    ):
        ## Get load for all model and weather years
        load_allyears = get_load(inputs_case, keep_weatheryears='all').loc[modelyears]
        ## Add descriptive index
        load_allyears = load_allyears.merge(
            timestamps[['year', 'yperiod', 'h_of_period']], left_on='datetime', right_index=True)
        load_allyears = load_allyears.droplevel('datetime')
        load_allyears.index.names = ['modelyear']
        load_allyears = load_allyears.set_index(['year', 'yperiod', 'h_of_period'], append=True)
        stressperiods_load = {
            y: identify_peak_containing_periods(
                df=load_allyears.loc[y], hierarchy=hierarchy,
                level=sw['GSw_PRM_StressSeedLoadLevel'])
            for y in modelyears
        }
    else:
        stressperiods_load = {y: set() for y in modelyears}

    ## Combine dicts of load and min-wind/solar stress periods into a dataframe with
    ## (modelyear, property, region, reason) index and (weatheryear, period of year, szn)
    ## values.
    stressperiods_write = pd.concat(
        {y: pd.DataFrame(
            [['load'] + list(i) for i in stressperiods_load[y]]
            + [[k]+list(i) for k,v in stressperiods_minre.items() for i in v],
            columns=['property','region','reason','year','yperiod']
         ).drop_duplicates(subset=['year','yperiod'])
         for y in modelyears},
        axis=0, names=['modelyear','index'],
    ).reset_index(level='index', drop=True)
    stressperiods_write['szn'] = (
        'y' + stressperiods_write.year.astype(str)
        + ('d' if sw.GSw_HourlyType=='year' else sw.GSw_HourlyType[0])
        + stressperiods_write.yperiod.map('{:>03}'.format)
    )


    #%%### Get the representative and force periods
    period_szn_write = period_szn.rename('season').reset_index()
    if sw['GSw_HourlyType'] == 'year':
        period_szn_write['year'] = sorted(sw['GSw_HourlyWeatherYears']*365)
        period_szn_write['yperiod'] = period_szn_write.period
    else:
        period_szn_write['rep_period'] = period_szn_write['season'].copy()
        period_szn_write['year'] = period_szn_write.period.map(lambda x: x[0])
        period_szn_write['yperiod'] = period_szn_write.period.map(lambda x: x[1])
    period_szn_write['actual_period'] = (
        'y' + period_szn_write.year.astype(str)
        + ('w' if sw.GSw_HourlyType == 'wek' else 'd')
        + period_szn_write.yperiod.astype(str).map('{:>03}'.format)
    )
    if sw['GSw_HourlyType'] == 'year':
        period_szn_write['rep_period'] = period_szn_write['actual_period'].copy()


    #%% Get some other convenience sets
    timestamps_day = make_timestamps(sw=pd.Series({**sw, **{'GSw_HourlyType':'day'}}))
    timestamps_wek = make_timestamps(sw=pd.Series({**sw, **{'GSw_HourlyType':'wek'}}))
    ## Include all possible seasons so dispatch mode can be rerun with any of them
    quarters = pd.read_csv(
        os.path.join(inputs_case, 'sets', 'quarter.csv'),
        header=None,
    ).squeeze(1).tolist()
    set_allszn = pd.Series(
        list(timestamps_day.period.unique())
        + list(timestamps_wek.period.unique())
        + quarters
    )
    ## Include stress periods
    set_allszn = pd.concat([set_allszn, 's'+set_allszn])

    set_allh = pd.concat([
        timestamps_day['timestamp'],
        timestamps_wek['timestamp'],
        's'+timestamps_day['timestamp'],
        's'+timestamps_wek['timestamp'],
    ])

    set_actualszn = (
        period_szn_write['season'].drop_duplicates() if sw['GSw_HourlyType'] == 'year'
        else period_szn_write['actual_period'])

    stress_period_szn = (
        stressperiods_write.assign(rep_period=stressperiods_write.szn)
        [['rep_period','year','yperiod','szn']].rename(columns={'szn':'actual_period'})
    )

    stressperiods_seed = (
        stressperiods_write
        .assign(szn='s'+stressperiods_write.szn)
        .reset_index().rename(columns={'modelyear':'t'})
        [['t','szn']]
    )


    #%%### Plot some stuff
    try:
        hourly_plots.plot_ldc(
            period_szn, profiles, rep_periods,
            forceperiods_write, sw, reeds_path, figpath)
    except Exception:
        print('plot_ldc failed:')
        print(traceback.format_exc())

    if int(sw.debug):
        try:
            hourly_plots.plot_load_days(profiles, rep_periods, period_szn, sw, reeds_path, figpath)
        except Exception:
            print('plot_load_days failed:')
            print(traceback.format_exc())

        try:
            hourly_plots.plot_8760(profiles, period_szn, sw, reeds_path, figpath)
        except Exception:
            print('plot_8760 failed:')
            print(traceback.format_exc())


    #%%### Write the outputs
    period_szn_write.drop('period', axis=1).to_csv(
        os.path.join(inputs_case, periodtype, 'period_szn.csv'), index=False)

    if 'user' not in sw['GSw_HourlyClusterAlgorithm']:
        forceperiods_write.to_csv(
            os.path.join(inputs_case, periodtype, 'forceperiods.csv'), index=False)

    timestamps.to_csv(
        os.path.join(inputs_case, periodtype, 'timestamps.csv'), index=False)

    set_actualszn.to_csv(
        os.path.join(inputs_case, periodtype, 'set_actualszn.csv'), header=False, index=False)

    if minimal:
        return period_szn_write

    #%% Write the sets over all possible periods (representative and stress)
    set_allszn.to_csv(
        os.path.join(inputs_case, 'set_allszn.csv'), header=False, index=False)

    set_allh.to_csv(
        os.path.join(inputs_case, 'set_allh.csv'), header=False, index=False)

    #%% Write the seed stress periods to use for the PRM constraint
    if 'user' in sw.GSw_PRM_StressModel:
        stressperiods_seed = pd.read_csv(os.path.join(inputs_case, 'stressperiods_user.csv'))
        stressperiods_seed.to_csv(os.path.join(inputs_case, 'stressperiods_seed.csv'), index=False)
        _missing = [t for t in modelyears if t not in stressperiods_seed.t.unique()]
        if len(_missing):
            raise Exception(f"Missing user-defined stress periods for {','.join(map(str, _missing))}")
        for t in modelyears:
            ## Write the period_szn file
            szns = stressperiods_seed.loc[stressperiods_seed.t==t, 'szn'].values
            dfwrite = pd.DataFrame({
                'rep_period': [i.strip('s') for i in szns],
                'year': [int(i.strip('sy')[:4]) for i in szns],
                'yperiod': [int(i[-3:]) for i in szns],
                'actual_period': [i.strip('s') for i in szns],
            })
            os.makedirs(os.path.join(inputs_case, f'stress{t}i0'), exist_ok=True)
            dfwrite.to_csv(os.path.join(inputs_case, f'stress{t}i0', 'period_szn.csv'), index=False)
    else:
        stressperiods_seed.to_csv(os.path.join(inputs_case, 'stressperiods_seed.csv'), index=False)
        for t in modelyears:
            os.makedirs(os.path.join(inputs_case, f'stress{t}i0'), exist_ok=True)
            if stressperiods_write.empty:
                pd.DataFrame(columns=['property','region','reason','year','yperiod','szn']).to_csv(
                    os.path.join(inputs_case, f'stress{t}i0', 'forceperiods.csv'), index=False)
            else:
                stressperiods_write.loc[[t]].to_csv(
                    os.path.join(inputs_case, f'stress{t}i0', 'forceperiods.csv'), index=False)
            if stress_period_szn.empty:
                pd.DataFrame(columns=['rep_period','year','yperiod','actual_period']).to_csv(
                    os.path.join(inputs_case, f'stress{t}i0', 'period_szn.csv'), index=False)
            else:
                stress_period_szn.loc[[t]].to_csv(
                    os.path.join(inputs_case, f'stress{t}i0', 'period_szn.csv'), index=False)

    return period_szn_write


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == '__main__':

    #%% Parse arguments
    parser = argparse.ArgumentParser(
        description='Create the necessary 8760 and capacity factor data for hourly resolution')
    parser.add_argument('reeds_path', help='ReEDS-2.0 directory')
    parser.add_argument('inputs_case', help='ReEDS-2.0/runs/{case}/inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    # #%% Settings for testing
    # reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # inputs_case = os.path.join(
    #     reeds_path,'runs',
    #     'v20251209_scM0_USA_defaults','inputs_case','')
    # interactive = True

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )
    print('Starting hourly_repperiods.py')
    #%% Inputs from switches
    sw = reeds.io.get_switches(inputs_case)

    #######################################
    #%% Identify the representative periods
    main(sw=sw, reeds_path=reeds_path, inputs_case=inputs_case)

    ####################################################
    #%% Write timeseries data for representative periods
    hourly_writetimeseries.main(
        sw=sw, reeds_path=reeds_path, inputs_case=inputs_case,
        periodtype='rep',
        make_plots=1,
    )

    ############################################
    #%% Write timeseries data for stress periods
    modelyears = pd.read_csv(
        os.path.join(inputs_case, 'modeledyears.csv')).columns.astype(int)
    for t in modelyears:
        print(f'Writing seed stress periods for {t}')
        hourly_writetimeseries.main(
            sw=sw, reeds_path=reeds_path, inputs_case=inputs_case,
            periodtype=f'stress{t}i0',
            make_plots=0,
        )

    #%% All done
    reeds.log.toc(tic=tic, year=0, process='input_processing/hourly_repperiods.py', 
        path=os.path.join(inputs_case,'..'))
    print('Finished hourly_repperiods.py')
