#%% IMPORTS
import os
import logging
import shutil
## Turn off logging for imported packages
for i in ['matplotlib']:
    logging.getLogger(i).setLevel(logging.CRITICAL)
import pandas as pd
import numpy as np
### Local imports
from LDC_prep import read_file
from writedrshift import get_dr_shifts

##% Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()


##########
#%% INPUTS
decimals = 3
### Indicate whether to show plots interactively [default False]
interactive = False
### Indicate whether to save the old h17 inputs for comparison
debug = True
### Indicate the full possible collection of weather years
all_weatheryears = list(range(2007,2014))


#############
#%% FUNCTIONS

def h2timestamp(h, tz='EST'):
    """
    Map ReEDS timeslice to actual timestamp
    """
    y = int(h.strip('sy').split('d')[0])
    hr = int(h.split('h')[1])-1
    if 'd' in h:
        d = int(h.split('d')[1].split('h')[0])
    else:
        w = int(h.split('w')[1].split('h')[0])
        d = w * 5 + hr // 24
    out = pd.to_datetime(f'y{y}d{d}h{hr}', format='y%Yd%jh%H').tz_localize(tz)
    return out


def timestamp2h(ts, GSw_HourlyType='day'):
    """
    Map actual timestamp to ReEDS period
    """
    # ts = pd.Timestamp(year=2007, month=3, day=28)
    y = ts.year
    d = int(ts.strftime('%j').strip('0'))
    if GSw_HourlyType == 'wek':
        w = d // 5
        h = (d % 5) * 24 + ts.hour + 1
        out = f'y{y}w{w:>03}h{h:>03}'
    else:
        h = ts.hour + 1
        out = f'y{y}d{d:>03}h{h:>03}'
    return out

def get_timeindex(firstyear=2007, lastyear=2013, tz='EST'):
    """
    ReEDS time indices are in EST, and leap years drop Dec 31 instead of Feb 29
    """
    timeindex = np.ravel([
        pd.date_range(
            f'{y}-01-01', f'{y+1}-01-01',
            freq='H', closed='left', tz=tz,
        )[:8760]
        for y in range(firstyear, lastyear+1)
    ])
    return timeindex


def make_8760_map(period_szn, sw):
    """
    """
    hoursperperiod = {'day':24, 'wek':120, 'year':24}[sw['GSw_HourlyType']]
    periodsperyear = {'day':365, 'wek':73, 'year':365}[sw['GSw_HourlyType']]
    ### Start with all weather years
    hmap_7yr = pd.DataFrame({
        'timestamp': get_timeindex(firstyear=2007, lastyear=2013),
        'year': np.ravel([[y]*8760 for y in all_weatheryears]),
        'yearperiod': np.ravel([
            [h+1 for d in range(365) for h in (d,)*24] if sw['GSw_HourlyType'] == 'year'
            else [h+1 for d in range(periodsperyear)
                  for h in (d,)*hoursperperiod]
            for y in all_weatheryears]),
        'hour': range(1, 8760*len(all_weatheryears) + 1),
        'hour0': range(8760*len(all_weatheryears)),
        'yearhour': np.ravel(list(range(1,8761))*len(all_weatheryears)),
        'periodhour': (
            list(range(1,25))*365*len(all_weatheryears)
            if sw['GSw_HourlyType'] == 'year'
            else list(range(1,hoursperperiod+1))*periodsperyear*len(all_weatheryears)),
    })
    hmap_7yr['actual_period'] = (
        'y' + hmap_7yr.year.astype(str)
        + ('w' if sw.GSw_HourlyType == 'wek' else 'd')
        + hmap_7yr.yearperiod.astype(str).map('{:>03}'.format)
    )
    hmap_7yr['actual_h'] = (
        hmap_7yr.actual_period
        + 'h' + hmap_7yr.periodhour.astype(str).map('{:>03}'.format)
    )
    hmap_7yr['season'] = hmap_7yr.actual_period.map(
        period_szn.set_index('actual_period').season)
    ### create the timestamp index: y{20xx}d{xxx}h{xx} (left-padded with 0)
    if sw['GSw_HourlyType'] == 'year':
        ### If using a chronological year (i.e. 8760) the day index uses actual days
        hmap_7yr['h'] = (
            'y' + hmap_7yr.year.astype(str)
            + 'd' + hmap_7yr.yearperiod.astype(str).map('{:>03}'.format)
            + 'h' + hmap_7yr.periodhour.astype(str).map('{:>03}'.format)
        )
    else:
        ### If using representative periods (days/weks) the period index uses
        ### representative periods, which are in the 'season' column
        hmap_7yr['h'] = (
            hmap_7yr.season
            + 'h' + hmap_7yr.periodhour.astype(str).map('{:>03}'.format)
        )
    ### hmap_myr (for "model years") only contains the actually-modeled periods
    hmap_myr = hmap_7yr.dropna(subset=['season']).copy()

    return hmap_7yr, hmap_myr


def get_season_peaks_hourly(load, sw, hierarchy, h2szn):
    ### Aggregate demand by GSw_PRM_hierarchy_level
    if sw['GSw_PRM_hierarchy_level'] == 'r':
        rmap = pd.Series(hierarchy.index, index=hierarchy.index)
    else:
        rmap = hierarchy[sw['GSw_PRM_hierarchy_level']]
    load_agg = (
        load
        .assign(region=load.r.map(rmap))
        .groupby(['h','region']).MW.sum()
        .unstack('region').reset_index()
    )
    ### Get the peak hour by season
    load_agg['szn'] = load_agg.h.map(h2szn)
    peakhour_agg_byseason = load_agg.set_index('h').groupby('szn').idxmax()
    ### Get the BA demand during the peak hour of the associated GSw_PRM_hierarchy_level
    seasons = h2szn.dropna().unique()
    peak_out = {}
    for r in load.r.unique():
        load_r = load.loc[load.r==r].set_index('h').MW
        peak_szn = peakhour_agg_byseason[rmap[r]]
        for szn in seasons:
            ### When running for stress periods we might not have data for the periods
            ### of interest, so allow for zeros
            if szn in peak_szn.index:
                peak_out[r,szn] = float(load_r[peak_szn[szn]])
            else:
                peak_out[r,szn] = 0
    peak_out = (
        pd.Series(peak_out).rename('MW')
        .reset_index().rename(columns={'level_0':'r','level_1':'szn'}))
    return peak_out


def append_csp_profiles(cf_rep, sw):
    ### Get the CSP profiles
    cfcsp = cf_rep[[c for c in cf_rep if c.startswith('csp')]].copy()
    ### As in cfgather.py, we duplicate the csp1 profiles for each CSP tech
    cfcsp_out = pd.concat((
        [cfcsp.rename(columns={c:c.replace('csp',f'csp{i}') for c in cfcsp.columns})
         for i in sw['GSw_CSP_Types']]
    ), axis=1)
    ### Drop the original 'csp' profiles and append the duplicated CSP profiles to rest of cf's
    cf_combined = pd.concat([
        cf_rep[[c for c in cf_rep if not c.startswith('csp')]],
        cfcsp_out], axis=1
    )

    return cf_combined


def get_minloading_windows(sw, h_szn, chunkmap):
    """
    Create combinations of h's within GSw_HourlyWindow of each other,
    beginning every GSw_HourlyWindowOverlap
    """
    ### Inputs for testing
    # sw['GSw_HourlyWindow'] = 2
    # sw['GSw_HourlyWindowOverlap'] = 1
    h_szn_chunked = h_szn.assign(h=h_szn.h.map(chunkmap)).drop_duplicates()
    seasons = h_szn_chunked.season.unique()
    hour_szn_group = set()
    for season in seasons:
        ## 2 copies so we can loop around the end
        timeslices = h_szn_chunked.loc[h_szn_chunked.season==season,'h'].tolist() * 2
        numslices = len(set(timeslices))
        all_combos = [
            (t1,t2) for (i,t1) in enumerate(timeslices) for (j,t2) in enumerate(timeslices)
            if (
                ## Drop duplicates
                (i != j)
                ## Must be within GSw_HourlyWindow steps of each other
                and (abs(i - j) < int(sw['GSw_HourlyWindow']))
                ## First index must be in the first pass
                and (i <= numslices)
                ## Only keep the windows that start from overlaps that are kept
                and not (i % (int(sw['GSw_HourlyWindowOverlap'])+1))
            )
        ]
        ### Add both polarities
        hour_szn_group.update(all_combos)
        hour_szn_group.update([(j,i) for (i,j) in all_combos])

    ### Format as dataframe and return
    hour_szn_group = pd.DataFrame(hour_szn_group, columns=['h','hh']).sort_values(['h','hh'])

    return hour_szn_group


def get_yearly_demand(
        sw, val_r, hmap_myr, hmap_7yr, inputs_case,
    ):
    """
    After clustering based on GSw_HourlyClusterYear and identifying the modeled days,
    reload the raw demand and extract the demand on the modeled days for each year.
    """
    ### Get original demand data, subset to cluster year
    load_in = read_file(os.path.join(inputs_case,'load'), index_columns=2)[val_r].unstack(level=0)
    load_in.columns = load_in.columns.rename(['r','t'])
    ### load.h5 is busbar load, but b_inputs.gms ingests end-use load, so scale down by distloss
    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, usecols=[0,1], index_col=0, squeeze=True)
    load_in *= (1 - scalars['distloss'])
    ### Keep hours being considered (only has an effect when periodtype != 'rep')
    load_in = load_in.loc[hmap_7yr.hour0].copy()

    ### Add time index
    load_in.index = hmap_7yr.actual_h.rename('h')

    load_out = load_in.copy()
    ### If using representative (i.e. medoid) periods, pull out the representative periods.
    if sw['GSw_HourlyType'] != 'year':
        load_out = load_out.loc[hmap_myr.h.unique()].copy()
    ### Otherwise, if using full year, we keep the modeled years
    else:
        load_out = load_out.loc[
            load_out.index.map(hmap_7yr.set_index('actual_h').year)
            .isin(sw['GSw_HourlyWeatherYears'])
        ].copy()

    ### Reshape for ReEDS
    load_out = load_out.stack('r').reorder_levels(['r','h'], axis=0).sort_index()

    return load_in, load_out


def get_yearly_flexDR(
        sw, period_szn, rep_periods,
        hmap_1yr, set_szn, inputs_case):
    """
    After clustering based on GSw_HourlyClusterYear and identifying the modeled days,
    reload the raw flexible demand response and extract for the modeled days of each year
    """
    hoursperperiod = {'day':24, 'wek':120, 'year':np.nan}[sw['GSw_HourlyType']]
    ### Get the set of szn's and h's
    szn_h = (
        hmap_1yr
        .drop_duplicates(['h','season'])
        .sort_values(['season','hour']).reset_index(drop=True)
        [['season','h']]
        .assign(periodhour=np.ravel(
            ([range(1,25)] * 365 if sw['GSw_HourlyType']=='year'
                else [range(1,hoursperperiod+1)] * len(set_szn))
        ))
        .set_index(['season','periodhour']).h
    ).copy()

    #original demand response data
    dr_inc = pd.read_csv(os.path.join(inputs_case,'dr_inc.csv'))
    dr_dec = pd.read_csv(os.path.join(inputs_case,'dr_dec.csv'))

    unique_inc_techs = len(dr_inc.i.unique())
    ### Add time indices ("season" is the identifier for modeled periods)
    dr_inc['period'] = (
        np.ravel([[d]*24 for d in range(1,366)]*unique_inc_techs)
        if sw['GSw_HourlyType'] == 'year'
        else np.ravel([[d]*hoursperperiod for d in period_szn.index.values]*unique_inc_techs))
    dr_inc['periodhour'] = (
        np.ravel([range(1,25) for d in range(365)]*unique_inc_techs)
        if sw['GSw_HourlyType'] == 'year'
        else np.ravel([range(1,hoursperperiod+1) for d in period_szn.index.values]*unique_inc_techs)
    )
    dr_inc['season'] = dr_inc.period.map(period_szn)

    unique_dec_techs = len(dr_dec.i.unique())
    ### Add time indices ("season" is the identifier for modeled periods)
    dr_dec['period'] = (
        np.ravel([[d]*24 for d in range(1,366)]*unique_dec_techs)
        if sw['GSw_HourlyType'] == 'year'
        else np.ravel([[d]*hoursperperiod for d in period_szn.index.values]*unique_dec_techs))
    dr_dec['periodhour'] = (
        np.ravel([range(1,25) for d in range(365)]*unique_dec_techs)
        if sw['GSw_HourlyType'] == 'year'
        else np.ravel([range(1,hoursperperiod+1) for d in period_szn.index.values]*unique_dec_techs)
    )
    dr_dec['season'] = dr_dec.period.map(period_szn)


    ### If modeling a full year, keep everything
    if sw['GSw_HourlyType'] == 'year':
        dr_inc_out = dr_inc.drop(['period','periodhour','season'], axis=1)
        dr_inc_out.index = hmap_1yr.h #this is probably wrong bc index needs to be multiplied out?
        dr_dec_out = dr_dec.drop(['period','periodhour','season'], axis=1)
        dr_dec_out.index = hmap_1yr.h
    ### If using representative (i.e. medoid) periods, pull out the representative periods
    else:
        dr_inc_out = (
            dr_inc.loc[dr_inc.period.isin(rep_periods)]
            .drop(['period','hour','year'],axis=1)
            .set_index(['season','periodhour']).sort_index()
        )
        dr_inc_out.index = dr_inc_out.index.map(szn_h).rename('h')
        dr_dec_out = (
            dr_dec.loc[dr_dec.period.isin(rep_periods)]
            .drop(['period','hour','year'],axis=1)
            .set_index(['season','periodhour']).sort_index()
        )
        dr_dec_out.index = dr_dec_out.index.map(szn_h).rename('h')

    dr_inc_out = (
        dr_inc_out.reset_index().set_index(['h','i']).stack().reset_index()
        .rename(columns={'i':'*i','level_2':'r',0:'Values'})[['*i','r','h','Values']])
    dr_dec_out = (
        dr_dec_out.reset_index().set_index(['h','i']).stack().reset_index()
        .rename(columns={'i':'*i','level_2':'r',0:'Values'})[['*i','r','h','Values']])

    return dr_inc_out,dr_dec_out


# #%% Inputs for testing
# reeds_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
# inputs_case = os.path.join(reeds_path, 'runs', 'v20230210_prmM0_ERCOT_d10sIrh4sh2_y2012', 'inputs_case')
# sw = pd.read_csv(
#     os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
# periodtype = 'stress2010'
# periodtype = 'rep'
# make_plots = int(sw.hourly_cluster_plots)
# make_plots = 0
# figpathtail = ''


#%% Main function
def main(sw, reeds_path, inputs_case, periodtype='rep', make_plots=1, figpathtail=''):
    """
    """
    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    ### Parse some switches
    if not isinstance(sw['GSw_HourlyWeatherYears'], list):
        sw['GSw_HourlyWeatherYears'] = [int(y) for y in sw['GSw_HourlyWeatherYears'].split('_')]
    ## Hard-code a GSw_CSP_Types switch as in LDC_prep.py
    sw['GSw_CSP_Types'] = [1,2]
    ## Designate where to write the outputs, and prefix for timestamps
    if 'rep' in periodtype.lower():
        prefix = ''
        tprefix = ''
    else:
        os.makedirs(os.path.join(inputs_case, periodtype), exist_ok=True)
        prefix = os.path.join(periodtype, '')
        tprefix = 's'

    ### Direct plots to outputs folder
    figpath = os.path.join(inputs_case,'..','outputs',f'hourly{figpathtail}')
    os.makedirs(figpath, exist_ok=True)

    #%%### Load shared files
    val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'), squeeze=True, header=None).tolist()
    hierarchy = pd.read_csv(
        os.path.join(inputs_case, 'hierarchy.csv')).rename(columns={'*r':'r'}).set_index('r')

    #%%### Load period-szn map, get representative and stress periods
    period_szn = pd.read_csv(os.path.join(inputs_case, prefix+'period_szn.csv'))
    try:
        forceperiods = pd.read_csv(os.path.join(inputs_case, prefix+'forceperiods.csv'))
    except FileNotFoundError:
        forceperiods = pd.DataFrame(
            columns=['property','region','reason','year','yperiod','szn'])
    ### Strip off prefix to start with a fresh slate
    for col in ['rep_period','actual_period']:
        period_szn[col] = period_szn[col].str.strip(tprefix)
        if len(forceperiods):
            for col in ['szn']:
                forceperiods[col] = forceperiods[col].str.strip(tprefix)
    if 'season' not in period_szn:
        period_szn['season'] = period_szn['rep_period'].copy()


    #%%### If there are no periods, write empty dataframes and stop here
    if not len(period_szn):
        write = {
            'set_h': ['*h'],
            'set_szn': ['*szn'],
            'h_szn': ['*h','season'],
            'h_dt_szn': ['h','season','year','hour'],
            'numhours': ['*h','numhours'],
            'frac_h_quarter_weights': ['*h','quarter','weight'],
            'd_szn': ['*period','szn'],
            'h_szn_start': ['*season','h'],
            'h_szn_end': ['*season','h'],
            'hour_szn_group': ['*h','hh'],
            'opres_periods': ['*szn'],
            'h_szn_prm': ['*h','season'],
            'load_allyear': ['*r','h','t','MW'],
            'peak_szn': ['*r','szn','t','MW'],
            'cf_vre': ['*i','r','h','cf'],
            'net_trade_can': ['*r','h','t','MWh'],
            'can_exports_h_frac': ['*h','frac_weighted'],
            'can_imports_szn_frac': ['*szn','frac_weighted'],
            'period_weights': ['*szn','rep_period'],
            'hmap_myr': ['*year','yearperiod','hour','hour0','yearhour',
                         'periodhour','actual_period','actual_h','season','h'],
            'periodmap_1yr': ['*actual_period','season'],
            'canmexload': ['*r','h'],
            'dr_increase': ['*i','r','h'],
            'dr_decrease': ['*i','r','h'],
            'dr_shifts': ['*i','h','hh'],
            'dr_shed': ['*i'],
            'ev_static_demand': ['*r','h','t'],
            'flex_frac_all': ['*flex_type','r','h','t'],
            'peak_h': ['*r','h','t','MW'],
        }
        for f, columns in write.items():
            pd.DataFrame(columns=columns).to_csv(
                os.path.join(inputs_case, prefix+f+'.csv'), index=False)

        return write


    #%%### Process the representative period weights
    #%% Generate map from actual to representative periods
    hmap_7yr, hmap_myr = make_8760_map(period_szn=period_szn, sw=sw)
    ### Add prefix if necessary
    if tprefix:
        for col in ['actual_period','actual_h','season','h']:
            hmap_myr[col] = tprefix + hmap_myr[col]
            hmap_7yr[col] = tprefix + hmap_7yr[col]
        for col in ['rep_period','actual_period']:
            period_szn[col] = tprefix + period_szn[col]
        if sw['GSw_HourlyType'] != 'year':
            period_szn['season'] = tprefix + period_szn['season']
        if len(forceperiods):
            for col in ['szn']:
                forceperiods[col] = tprefix + forceperiods[col]

    #%%### Load full hourly RE CF, for downselection below
    #%% VRE
    recf = pd.read_hdf(os.path.join(inputs_case,'recf.h5'))
    resources = pd.read_csv(os.path.join(inputs_case,'resources.csv'))
    ### Overwrite CSP CF (which in recf.h5 is post-storage) with solar field CF
    cspcf = pd.read_hdf(os.path.join(inputs_case,'csp.h5'))
    recf = (
        recf.drop([c for c in recf if c.startswith('csp')], axis=1)
        .merge(cspcf, left_index=True, right_index=True)
    ).loc[hmap_7yr.hour0]
    recf.index = hmap_7yr.actual_h

    #%% Get data for representative periods
    rep_periods = sorted(period_szn.rep_period.unique())

    ### Broadcast CSP values for all techs
    cf_rep = recf.loc[
        recf.index.map(lambda x: any([x.startswith(i) for i in rep_periods]))]
    cf_rep = append_csp_profiles(cf_rep=cf_rep, sw=sw)

    cf_out = cf_rep.rename_axis('h').copy()
    i = cf_rep.columns.map(resources.set_index('resource').i)
    r = cf_rep.columns.map(resources.set_index('resource').r)
    cf_out.columns = pd.MultiIndex.from_arrays([i,r], names=['i','r'])
    cf_out = cf_out.stack(['i','r']).reorder_levels(['i','r','h']).rename('cf').reset_index()


    #%%### Create the temporal sets used by ReEDS
    ### Calculate number of hours represented by each timeslice
    hours = (
        hmap_myr.groupby('h').season.count().rename('numhours')
        / (len(sw['GSw_HourlyWeatherYears']) if periodtype == 'rep' else 1))
    # hours = hmap_myr.groupby('h').season.count().rename('numhours')
    # ## Representative periods are normalized by the number of modeled years (so that we can
    # ## still act like we're modeling over a single year in ReEDS),
    # ## but force-included periods are not; they're always treated as full single periods
    # hours.loc[
    #     ## exclude the hours that belong to force-included periods
    #     hours.index.map(lambda x: not any([x.startswith(p) for p in forceperiods_prefix]))
    # ] /= len(sw['GSw_HourlyWeatherYears'])
    ### Make sure it lines up
    if periodtype == 'rep':
        assert int(np.around(hours.sum(), 0)) % 8760 == 0
    else:
        assert int(np.around(hours.sum(), 0)) % len(hmap_myr) == 0

    # create the timeslice-to-season mapping
    h_szn = hmap_myr[['h','season']].drop_duplicates().reset_index(drop=True)

    ### create the set of szn's modeled in ReEDS
    set_szn = pd.DataFrame({'szn':period_szn.season.sort_values().unique()})

    ### create the set of timeslicess modeled in ReEDS
    hset = h_szn.h.sort_values().reset_index(drop=True)


    ### List of periods in which to apply operating reserve constraints
    if 'user' in sw['GSw_HourlyClusterAlgorithm']:
        period_szn_user = pd.read_csv(
            os.path.join(reeds_path,'inputs','variability','period_szn_user.csv')
        )
        opres_periods = period_szn_user.loc[
            (period_szn_user.scenario==sw['GSw_HourlyClusterAlgorithm'])
            & (~period_szn_user.opres.isnull())
        ].rep_period.drop_duplicates().rename('szn').to_frame()
    elif (sw['GSw_OpResPeriods'] == 'all') or (sw['GSw_HourlyType'] == 'year'):
        opres_periods = set_szn
    elif sw['GSw_OpResPeriods'] == 'representative':
        opres_periods =  set_szn.loc[~set_szn.szn.isin(forceperiods.szn)]
    elif sw['GSw_OpResPeriods'] == 'stress':
        opres_periods =  set_szn.loc[set_szn.szn.isin(forceperiods.szn)]
    elif sw['GSw_OpResPeriods'] in ['peakload','peak_load','peak','load','demand']:
        opres_periods =  set_szn.loc[
            set_szn.szn.isin(forceperiods.loc[forceperiods.property=='load'].szn)]
    elif sw['GSw_OpResPeriods'] in ['minre','re','vre','min_re']:
        opres_periods =  set_szn.loc[
            set_szn.szn.isin(forceperiods.loc[forceperiods.property!='load'].szn)]

    ### Calculate the fraction of each h associated with each ReEDS quarter, for compatibility
    ### with model inputs that are defined by quarter
    ## Get a map from hour-of-year to ReEDS quarter
    h_dt_szn_h17 = pd.read_csv(os.path.join(reeds_path,'inputs','variability','h_dt_szn.csv'))
    quarters = (
        h_dt_szn_h17.iloc[:8760]
        .replace({'season':{'winter':'wint','spring':'spri','summer':'summ'}})
        .rename(columns={'season':'quarter'})
        .set_index('hour').quarter
    )

    #%% Calculate the fraction of hours of each timeslice associated with each quarter
    if periodtype == 'rep':
        frac_h_quarter_weights = hmap_myr.copy()
        frac_h_quarter_weights['quarter'] = hmap_myr.yearhour.map(quarters)
        frac_h_quarter_weights = (
            ## Count the number of days in each szn that are part of each quarter
            frac_h_quarter_weights.groupby(['h','quarter']).season.count()
            ## Normalize by the total number of hours per timeslice
            / hours
            / len(sw['GSw_HourlyWeatherYears'])
        ).rename('weight')
        frac_h_quarter_weights = frac_h_quarter_weights.reset_index()
    else:
        frac_h_quarter_weights = hmap_7yr.copy()
        frac_h_quarter_weights['quarter'] = hmap_7yr.yearhour.map(quarters)
        frac_h_quarter_weights = (
            frac_h_quarter_weights.groupby(['actual_h','quarter']).actual_period.count()
        ).rename_axis(['h','quarter']).rename('weight').reset_index()

    ### Make sure it lines up
    assert (frac_h_quarter_weights.groupby('h').weight.sum().round(5) == 1).all()


    #%%### Net trade with Canada for GSw_Canada=2
    ### Read the 8760 net trade [MW], which is described at
    ## https://github.nrel.gov/ReEDS/ReEDS-2.0_Input_Processing/tree/master/Exogenous_Canadian_Trade
    can_8760 = (
        pd.read_hdf(os.path.join(reeds_path,'inputs','canada_imports','can_trade_8760.h5'))
        .rename(columns={'h':'hour'}).astype({'r':str}))
    ## Drop the h
    can_8760.hour = can_8760.hour.str.strip('h').astype('int')

    ## Concat for each weather year
    can_weatheryears = can_8760.pivot(index='hour', columns=['t','r'], values='net')
    can_weatheryears = pd.concat(
        {y: can_weatheryears for y in all_weatheryears},
        axis=0, ignore_index=True).loc[hmap_myr.hour0]
    ## Map 8760 hours to modeled hours
    can_weatheryears.index = hmap_myr.h

    ### Sum by (r,h,t) to get net trade in MWh during modeled hours
    can_out = (
        can_weatheryears.stack(['r','t']).groupby(['r','h','t']).sum().rename('MWh')
        ## Divide by number of weather years since we concatted that number of weather years
        / (len(sw['GSw_HourlyWeatherYears']) if periodtype == 'rep' else 1)
    ).reset_index()
    ## Only keep modeled regions
    can_out = can_out.loc[can_out.r.isin(val_r)].copy()


    #%%### Seasonal Canadian imports/exports for GSw_Canada=1
    #%% Exports: Spread equally over hours by quarter.
    can_exports_szn_frac = pd.read_csv(
        os.path.join(reeds_path, 'inputs', 'canada_imports', 'can_exports_szn_frac.csv'),
        header=0, names=['season','frac'], index_col='season', squeeze=True,
    )
    df = (
        frac_h_quarter_weights.astype({'h':'str','quarter':'str'})
        .replace({'weight':{0:np.nan}}).dropna(subset=['weight']).copy()
    )
    df = (
        df.assign(frac_exports=df.quarter.map(can_exports_szn_frac))
        .assign(season=df.h.map(h_szn.set_index('h').season))
        .assign(hours=df.h.map(hours))
    )
    df['quarter_hours'] = df.hours * df.weight
    df['hours_per_quarter'] = df.quarter.map(quarters.value_counts())
    df['frac_weighted'] = df.frac_exports * df.quarter_hours / df.hours_per_quarter
    can_exports_h_frac = df.groupby('h', as_index=False).frac_weighted.sum()
    ### Make sure it sums to 1
    if periodtype == 'rep':
        assert can_exports_h_frac.frac_weighted.sum().round(5) == 1

    #%% Imports: Spread over seasons by quarter.
    can_imports_quarter_frac = pd.read_csv(
        os.path.join(reeds_path, 'inputs', 'canada_imports', 'can_imports_szn_frac.csv'),
        header=0, names=['season','frac'], index_col='season', squeeze=True,
    )
    hours_per_season = hmap_myr.season.value_counts()
    df = hmap_myr.assign(quarter=hmap_myr.yearhour.map(quarters))
    hours_per_quarter = df['quarter'].value_counts()
    ## Fraction of quarter made up by each season (typically rep period)
    quarter_season_weights = (
        df.groupby(['quarter','season']).year.count()
        .divide(hours_per_quarter, axis=0, level='quarter'))
    can_imports_szn_frac = (
        quarter_season_weights
        .multiply(can_imports_quarter_frac, level='quarter')
        .groupby('season').sum()
        .rename('frac_weighted').reset_index().rename(columns={'season':'szn'}))
    ### Make sure it sums to 1
    if periodtype == 'rep':
        assert can_imports_szn_frac.frac_weighted.sum().round(5) == 1

    # =============================================================================
    # Hour, Region, and Timezone Mapping
    # =============================================================================

    period_weights = (
        period_szn.rep_period.value_counts() / len(sw['GSw_HourlyWeatherYears'])
    ).reset_index().rename(columns={'index':'szn','szn':'weight'})

    ###### Mapping from hourly resolution to GSw_HourlyChunkLength resolution
    ### Aggregation is performed as an average over the hours to be aggregated
    ### For simplicity, midnight is always a boundary between chunks

    ### First make sure the number of hours is divisible by the chunk length
    GSw_HourlyChunkLength = int(
        sw[f"GSw_HourlyChunkLength{periodtype.strip('i0123456789').title()}"])
    assert not len(hset) % GSw_HourlyChunkLength, (
        'Hours are not divisible by chunk length:'
        '\nlen(hset) = {}\nGSw_HourlyChunkLength = {}'
    ).format(len(hset), GSw_HourlyChunkLength)

    ### Map hours to chunks. Chunks are formatted as hour-ending.
    ## If GSw_HourlyChunkLength == 2,
    ## h1-h2-h3-h4-h5-h6 is mapped to h2-h2-h4-h4-h6-h6.
    outchunks = hset[GSw_HourlyChunkLength-1::GSw_HourlyChunkLength]
    chunkmap = dict(zip(
        hset.values,
        np.ravel([[c]*GSw_HourlyChunkLength for c in outchunks])
    ))

    #%%### h_dt_szn for Augur
    if not len(hmap_myr) % 8760:
        ## Important: When modeling a single weather year, rep periods in the 7-year
        ## h_dt_szn table are just the single-year periods concatenated 7 times.
        ## In that case electrolyzer demand (optimized for GSw_HourlyWeatherYears, usually
        ## 2012) won't line up with optimal operation times (low demand / high wind/solar)
        ## outside of the single reprsentative year.
        h_dt_szn = pd.concat(
            {y: hmap_myr.drop_duplicates(['yearhour']).drop('year', axis=1)
            for y in range(2007,2014)}, names=('year',),
            axis=0,
        ).reset_index(level='year').reset_index(drop=True)
        h_dt_szn['hour'] = (h_dt_szn.year-2007)*8760 + h_dt_szn.yearhour
        h_dt_szn['hour0'] = h_dt_szn.hour - 1
        for col in ['actual_period', 'actual_h']:
            h_dt_szn[col] = 'y' + h_dt_szn.year.astype(str) + h_dt_szn[col].str[5:]
    ## If hmap_myr contains less than a full year (e.g. for stress periods),
    ## just use hmap_myr as-is.
    else:
        h_dt_szn = hmap_myr.copy()

    # =============================================================================
    # Season starting and ending hours
    # =============================================================================

    ### Start hour is the lowest-numbered h in each season
    ## End up with a series mapping season to start hour: {'szn1':'h1', ...}
    szn2starth = hmap_myr.drop_duplicates('season', keep='first').set_index('season').h

    ### End hour is the highest-numbered h in each season
    szn2endh = hmap_myr.drop_duplicates('season', keep='last').set_index('season').h

    ### next timeslice
    nexth_actualszn = (
        hmap_myr.assign(h=hmap_myr.h.map(chunkmap))
        [[('season' if sw.GSw_HourlyType == 'year' else 'actual_period'),'h']]
        .drop_duplicates()
        .rename(columns={'actual_period':'allszn', 'season':'allszn'})
    ).copy()
    ## Roll to make a lookup table for GAMS
    nexth_actualszn['allsznn'] = np.roll(nexth_actualszn['allszn'], -1)
    nexth_actualszn['hh'] = np.roll(nexth_actualszn['h'], -1)

    ### h-to-actual-period mapping for inter-period storage
    h_actualszn = (
        hmap_myr.assign(h=hmap_myr.h.map(chunkmap))
        [['h',('season' if sw.GSw_HourlyType == 'year' else 'actual_period')]]
        .drop_duplicates())

    # =============================================================================
    # Hour groups for eq_minloading
    # =============================================================================

    hour_szn_group = get_minloading_windows(sw=sw, h_szn=h_szn, chunkmap=chunkmap)

    # =============================================================================
    # Yearly demand
    # =============================================================================

    load_in, load_h = get_yearly_demand(
        sw=sw, val_r=val_r, hmap_myr=hmap_myr, hmap_7yr=hmap_7yr, inputs_case=inputs_case)

    ###### Get the peak demand in each (r,szn,modelyear) for GSw_HourlyWeatherYears
    load_full_yearly = load_in.loc[
        load_in.index.map(hmap_7yr.set_index('actual_h').year.isin(sw['GSw_HourlyWeatherYears']))
    ].stack('r').reset_index()

    h2szn = hmap_7yr.set_index('actual_h').season
    years = pd.read_csv(os.path.join(inputs_case,'modeledyears.csv')).columns.astype(int).values

    peak_all = {}
    for year in years:
        peak_all[year] = get_season_peaks_hourly(
            load=load_full_yearly[['r','h',year]].rename(columns={year:'MW'}),
            sw=sw, hierarchy=hierarchy, h2szn=h2szn)
        print(f'determined season peaks for {year}')
    peak_all = (
        pd.concat(peak_all, names=['t','drop']).reset_index().drop('drop', axis=1)
        [['r','szn','t','MW']]
    ).copy()

    #%% Calculate the peak demand timeslice of each season.
    ### Used for hydro_nd PRM constraint.
    h_szn_prm = (
        pd.merge(load_h[max(years)].groupby('h').sum().rename('MW'), h_szn, on='h')
        .sort_values('MW').drop_duplicates('season', keep='last')
        .drop('MW', axis=1).sort_values('season')
    )

    # =============================================================================
    # Demand response
    # =============================================================================

    if int(sw.GSw_DR):
        dr_inc, dr_dec = get_yearly_flexDR(
            sw=sw,  period_szn=period_szn, rep_periods=rep_periods,
            hmap_1yr=hmap_myr, set_szn=set_szn, 
            inputs_case=inputs_case)
        shift_out, dr_shifts = get_dr_shifts(
            sw=sw, reeds_path=reeds_path, inputs_case=inputs_case,
            native_data=False, hmap_7yr=hmap_7yr, hours=hours, chunkmap=chunkmap)
    else:
        dr_inc = pd.DataFrame(columns=['*i','r','h'])
        dr_dec = pd.DataFrame(columns=['*i','r','h'])
        shift_out = pd.DataFrame(columns=['dr_type','shifted_h','h','shift_frac'])


    # =============================================================================
    ### Write outputs, aggregating hours to GSw_HourlyChunkLength if necessary
    # =============================================================================
    write = {
        ### Contents are [dataframe, header, index]
        ## h set for representative timeslices
        'set_h': [hset.map(chunkmap).drop_duplicates().to_frame(), False, False],
        ## szn set for representative periods
        'set_szn': [set_szn, False, False],
        ## Hours to season mapping (h,szn)
        'h_szn': [
            h_szn.assign(h=h_szn.h.map(chunkmap)).drop_duplicates(),
            False, False],
        ## 8760 hour linkage set for Augur (h,szn,year,hour)
        'h_dt_szn': [
            h_dt_szn[['h','season','year','hour']].assign(h=h_dt_szn.h.map(chunkmap)),
            True, False],
        ## Number of hours represented by each timeslice (h)
        'numhours': [
            (hours.reset_index().assign(h=hours.index.map(chunkmap)).groupby('h').numhours.sum()
             .reset_index().round(decimals+3)),
            False, False],
        ## Quarterly season weights for assigning summer/winter dependent parameters (h,szn)
        'frac_h_quarter_weights': [
            (frac_h_quarter_weights.assign(h=frac_h_quarter_weights.h.map(chunkmap))
             .groupby(['h','quarter'], as_index=False).weight.mean()
             .round(decimals+3)),
            False, False],
        ## Hours to actual season mapping (h,allszn)
        'h_actualszn': [h_actualszn, False, False],
        ## mapping from one timeslice to the next for actual periods
        'nexth_actualszn': [nexth_actualszn, False, False],
        ## Day to season mapping for Osprey (day,szn)
        'd_szn': [
            (h_dt_szn.assign(d='s'+h_dt_szn.actual_period.str.strip('s'))
             [['d','season']].drop_duplicates()),
            False, False],
        ## first timeslice in season (szn,h)
        'h_szn_start': [szn2starth.map(chunkmap).reset_index(), False, False],
        ## last timeslice in season (szn,h)
        'h_szn_end': [szn2endh.map(chunkmap).reset_index(), False, False],
        ## minload hour windows with overlap (h,h)
        'hour_szn_group': [hour_szn_group, False, False],
        ## periods in which to apply operating reserve constraints (szn)
        'opres_periods': [opres_periods, False, False],
        ## Season-peak demand hour for each szn's representative day (h,szn)
        'h_szn_prm': [
            h_szn_prm.assign(h=h_szn_prm.h.map(chunkmap)),
            False, False],
        ## Annual timeslice demand
        'load_allyear': [
            (load_h.reset_index().assign(h=load_h.reset_index().h.map(chunkmap))
             .groupby(['r','h'])
             .agg((sw['GSw_PRM_StressLoadAggMethod'] if 'stress' in periodtype else 'mean'))
             .stack('t').rename('MW')
             .round(decimals).reset_index()),
            False, False],
        ## Seasonal peak demand
        'peak_szn': [peak_all.round(decimals), False, False],
        ## Capacity factors (i,r,h)
        'cf_vre': [
            (cf_out.assign(h=cf_out.h.map(chunkmap))
             .groupby(['i','r','h'], as_index=False).cf.mean().round(5)),
            False, False],
        ## Static Canadian trade [MWh] (r,h,t)
        'net_trade_can': [
            (can_out.assign(h=can_out.h.map(chunkmap))
             .groupby(['r','h','t'], as_index=False).MWh.sum()
             .round(decimals)),
            False, False],
        ## Exports to Canada [fraction] (h)
        'can_exports_h_frac': [
            (can_exports_h_frac.assign(h=can_exports_h_frac.h.map(chunkmap))
             .groupby('h', as_index=False).sum().round(6)),
            False, False],
        ## Imports from Canada [fraction] (szn)
        'can_imports_szn_frac': [can_imports_szn_frac.round(6), False, False],
        ## Demand response
        'dr_increase': [
            (dr_inc.assign(h=dr_inc.h.map(chunkmap))
             .groupby(['*i','r','h']).mean()
             .round(decimals).reset_index()),
             False, False],
        'dr_decrease': [
            (dr_dec.assign(h=dr_dec.h.map(chunkmap))
             .groupby(['*i','r','h']).mean()
             .round(decimals).reset_index()),
             False, False],
        'dr_shifts': [
            (shift_out[['dr_type', 'shifted_h', 'h', 'shift_frac']]
             .rename(columns={'dr_type':'*dr_type'})),
             False, False],
        ##################################################################################
        ###### The next parameters are just diagnostics and are not actually used in ReEDS
        ## Representative period weights for postprocessing (szn)
        'period_weights': [period_weights, False, False],
        ## Mapping from representative h to actual h
        'hmap_myr': [
            hmap_myr.assign(h=hmap_myr.h.map(chunkmap)),
            False, False],
        ## Mapping from representative h to actual h for full 7 years
        'hmap_7yr': [
            hmap_7yr.assign(h=hmap_7yr.h.map(chunkmap)),
            False, False],
        ## Mapping from representative period to actual period
        'periodmap_1yr': [
            hmap_myr[['actual_period','season']].drop_duplicates(),
            False, False],
        ###################################################################
        ###### The folowing parameters don't yet work for hourly resolution
        ## Canada/Mexico
        'canmexload': [pd.DataFrame(columns=['*r','h']), True, False],
        ## GSw_EV
        'ev_static_demand': [pd.DataFrame(columns=['*r','h','t']), True, False],
        ## GSw_EFS_Flex
        'flex_frac_all': [pd.DataFrame(columns=['*flex_type','r','h','t']), True, False],
        'peak_h': [pd.DataFrame(columns=['*r','h','t','MW']), True, False],
    }


    print("Writing data CSVs")
    for f in write:
        ### Rename first column so GAMS reads it as a comment
        if not write[f][1]:
            write[f][0].rename(
                columns={write[f][0].columns[0]: '*'+str(write[f][0].columns[0])},
                inplace=True
            )
        ### If the file already exists and we're creating representative period data,
        ### add a '_h17' to the filename and save it as a backup
        if (debug
            and os.path.isfile(os.path.join(inputs_case, f+'.csv'))
            and ('rep' in periodtype)):
            shutil.copy(
                os.path.join(inputs_case, f+'.csv'),
                os.path.join(inputs_case, f+'_h17.csv'))
        ### Write the new hourly parameters
        write[f][0].to_csv(
            os.path.join(inputs_case, prefix+f+'.csv'),
            # os.path.join(inputs_case, f+f'{figpathtail}.csv'),
            index=write[f][2])


    ###############################################################
    ### Map resulting annual capacity factor and deviation from h17
    if make_plots >= 1:
        try:
            import hourly_plots as plots_h
            plots_h.plot_maps(sw, inputs_case, reeds_path, figpath)
        except Exception as err:
            print('plot_maps failed with the following error:\n{}'.format(err))

    return write
