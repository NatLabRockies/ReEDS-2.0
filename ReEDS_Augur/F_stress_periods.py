#%%### General imports
import os
import site
import traceback
import pandas as pd
import numpy as np
from glob import glob
from distutils.dir_util import copy_tree
### Local imports
import ReEDS_Augur.functions as functions

# #%% Debugging
# sw['reeds_path'] = os.path.expanduser('~/github/ReEDS-2.0/')
# sw['casedir'] = os.path.join(sw['reeds_path'],'runs','v20230123_prmM3_Pacific_d7sIrh4sh2_y2')
# import importlib
# importlib.reload(functions)


#%%### Functions
def write_last_years_periods(t, sw, outpath):
    """
    Copy the stress periods from the last model year and use them for the next model year.
    Used if there is no unmet PRM / dropped load.
    """
    last_stressperiod = sorted(glob(
        os.path.join(sw['casedir'], 'inputs_case', 'stress*')))[-1]
    copy_tree(
        last_stressperiod,
        os.path.join(sw['casedir'], 'inputs_case', outpath)
    )


def get_and_write_neue(sw, write=True):
    """
    Write dropped load across all completed years to outputs
    so it can be plotted alongside other ReEDS outputs
    """
    infiles = sorted(glob(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', 'PRAS_*.csv')))
    eue = {}
    for infile in infiles:
        year_iteration = os.path.basename(infile).strip('PRAS_.csv').split('i')
        y = int(year_iteration[0])
        i = int(year_iteration[1])
        eue[y,i] = pd.read_csv(infile)['USA_EUE'].sum()
    eue = pd.Series(eue).rename('MWh')
    eue.index = eue.index.rename(['year','iteration'])

    site.addsitedir(os.path.join(sw['reeds_path'], 'input_processing'))
    import LDC_prep
    load = LDC_prep.read_file(os.path.join(sw['casedir'],'inputs_case','load'))
    loadyear = load.sum(axis=1).groupby('year').sum()

    neue = (eue / loadyear * 1e6).rename('NEUE [ppm]').rename_axis(['t','iteration'])

    if write:
        neue.to_csv(os.path.join(sw['casedir'],'outputs','neue.csv'))
    return neue


def get_pras_eue(sw, t, iteration=0):
    dfpras = pd.read_csv(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', f"PRAS_{t}i{iteration}.csv"),
        index_col='h', parse_dates=True,
    )
    ### Overwrite the index (drop once it's fixed in ReEDS2PRAS)
    fulltimeindex = np.ravel([
        pd.date_range(
            '{}-01-01'.format(y), '{}-01-01'.format(y+1),
            freq='H', closed='left', tz='EST',
        )[:8760]
        for y in range(2007,2014)
    ])
    dfpras.index = fulltimeindex
    ## Only keep nonzero rows and columns
    dfeue = (
        dfpras.replace(0.,np.nan).dropna(axis=0, how='all')
        .dropna(axis=1, how='all').fillna(0))
    ## Keep EUE by zone
    dfeue = dfeue[
        [c for c in dfeue if (c.endswith('_EUE') and not c.startswith('USA'))]].copy()
    dfeue = (
        dfeue
        .rename(columns=dict(zip(dfeue.columns, [c.split('_')[0] for c in dfeue])))
        .rename_axis('r', axis=1).rename_axis('h', axis=0)
    )
    return dfeue


def get_osprey_eue(sw, t):
    dfosprey = pd.read_csv(
        os.path.join(
            sw['casedir'], 'ReEDS_Augur', 'augur_data', f"dropped_load_{t}.csv")
    ).rename(columns={'Val':'MW'})
    ## Parse the day/hour indices
    dfosprey['h'] = (
        (dfosprey.d + dfosprey.hr.map(lambda x: x.replace('hr','h')))
        .map(functions.h2timestamp)
    )
    dfeue = (
        dfosprey.set_index('h')
        .pivot(columns='r', values='MW').fillna(0)
    )
    return dfeue


def get_stress_periods(sw, t, iteration=0):
    ### Make the region aggregator
    hierarchy = pd.read_csv(
        os.path.join(sw['casedir'], 'inputs_case', 'hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()

    if sw['stress_hierarchy_level'] == 'r':
        rmap = pd.Series(hierarchy.index, index=hierarchy.index)
    else:
        rmap = hierarchy[sw['stress_hierarchy_level']]

    ### Get the dropped-PRM or dropped-load profile
    if sw['GSw_PRM_StressModel'].lower() == 'pras':
        dfeue = get_pras_eue(sw, t=t, iteration=iteration)
    else:
        dfeue = get_osprey_eue(sw, t=t)

    ### Map to stress_hierarchy_level and sum
    if sw['stress_hierarchy_level'] != 'country':
        raise NotImplementedError(
            "only stress_hierarchy_level=country is currently supported")
    dfsum = dfeue.rename(columns=rmap).groupby(axis=1, level=0).sum().sum(axis=1)

    ### Write out the stress period data for the dropped-load days
    dropped_load_day = (
        dfsum.groupby([dfsum.index.year, dfsum.index.month, dfsum.index.day])
        .agg(sw['GSw_PRM_StressMetric'])
        .rename_axis(['y','m','d']).rename('value').to_frame()
    )
    ## Convert to timestamp, then to ReEDS period
    dropped_load_day['actual_period'] = [
        functions.timestamp2h(pd.Timestamp(*d), sw['GSw_HourlyType']).split('h')[0]
        for d in dropped_load_day.index.values
    ]

    ### Aggregate and sort (descending) by EUE
    stress_periods = (
        dropped_load_day
        .groupby('actual_period').value.agg(sw['GSw_PRM_StressMetric'])
        .sort_values(ascending=False)
    )

    return stress_periods


#%%### Procedure
def main(sw, t, iteration=0):
    """
    """
    #%% More imports and settings
    site.addsitedir(os.path.join(sw['reeds_path'],'input_processing'))
    import hourly_writetimeseries

    savepath = os.path.join(sw['casedir'], 'outputs', 'Augur_plots')
    os.makedirs(savepath, exist_ok=True)
    outpath = f'stress{t}i{iteration}'

    #%% Write consolidated NEUE so far
    try:
        neue = get_and_write_neue(sw)
    except Exception as err:
        if int(sw['GSw_PRM_MaxStressPeriods']):
            raise Exception(err)
        print(traceback.format_exc())

    #%% Stop here if not using stress periods
    if not int(sw['GSw_PRM_MaxStressPeriods']):
        return None

    #%% Get EUE for the last GSw_PRM_StressPrevYears solve years
    solveyears = pd.read_csv(
        os.path.join(sw['casedir'],'inputs_case','modeledyears.csv')
    ).columns.astype(int)
    thisyear = list(solveyears).index(sw['t'])
    keepyears = solveyears[thisyear-int(sw['GSw_PRM_StressPrevYears'])+1:thisyear+1]

    infiles = sorted(glob(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', 'PRAS_*.csv')))
    keepfiles = [
        i for i in infiles
        if int(os.path.basename(i).split('_')[1].split('i')[0]) in keepyears]

    stress_periods = {}
    for infile in keepfiles:
        year_iteration = os.path.basename(infile).strip('PRAS_.csv').split('i')
        y = int(year_iteration[0])
        i = int(year_iteration[1])
        try:
            stress_periods[y,i] = get_stress_periods(sw, y, iteration=i)
        except FileNotFoundError:
            pass
    stress_periods = (
        pd.concat(stress_periods, names=['t','i','actual_period'])
        .rename('MWh'))

    #%% If there are no days with dropped load, stop here and use last year's days
    if not len(stress_periods):
        write_last_years_periods(t, sw, outpath)
        return None

    #%% Keep the highest-EUE periods across all iterations
    keep_periods = (
        stress_periods
        .sort_values(ascending=False)
        ## Drop duplicate periods from different years, keeping the worst year
        .reset_index().drop_duplicates('actual_period', keep='first')
        .set_index('actual_period').MWh
        .nlargest(int(sw['GSw_PRM_MaxStressPeriods'])).index
    )

    ## Reproduce the format of inputs_case/stress_period_szn.csv
    keepperiods_write = pd.DataFrame({
        'rep_period': keep_periods,
        'year': keep_periods.map(
            lambda x: int(x.strip('sy').split(sw['GSw_HourlyType'][0])[0])),
        'yperiod': keep_periods.map(
            lambda x: int(x.strip('sy').split(sw['GSw_HourlyType'][0])[1])),
        'actual_period': keep_periods,
    })

    #%% Write the stress periods
    os.makedirs(os.path.join(sw['casedir'], 'inputs_case', outpath), exist_ok=True)
    keepperiods_write.to_csv(
        os.path.join(sw['casedir'], 'inputs_case', outpath, 'period_szn.csv'),
        index=False,
    )
    #%% Write timeseries data for stress periods for the next iteration of ReEDS
    write_timeseries = hourly_writetimeseries.main(
        sw=sw, reeds_path=sw['reeds_path'],
        inputs_case=os.path.join(sw['casedir'], 'inputs_case'),
        periodtype=outpath,
        make_plots=0, figpathtail='',
    )

    return keepperiods_write
