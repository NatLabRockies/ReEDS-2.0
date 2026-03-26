#%%### General imports
import os
import site
import traceback
import pandas as pd
import numpy as np
from glob import glob
import re
import matplotlib.pyplot as plt
### Local imports

## use this to import reeds when running locally for debugging
# import site
# this_dir_path = os.path.dirname(os.path.realpath(__file__))
# site.addsitedir(os.path.join(this_dir_path, ".."))

import reeds

# #%% Debugging
# sw['reeds_path'] = os.path.expanduser('~/github/ReEDS-2.0/')
# sw['casedir'] = os.path.join(sw['reeds_path'],'runs','v20230123_prmM3_Pacific_d7sIrh4sh2_y2')
# import importlib
# importlib.reload(functions)


#%%### Functions
def plot_eue_diagnostics(sw, t, iteration, high_eue_periods):
    try:
        dates = (
            pd.concat(high_eue_periods)
            .reset_index().actual_period.map(reeds.timeseries.h2timestamp)
            .dt.strftime('%Y-%m-%d')
            .tolist()
        )
        vmax = {'forced': 40, 'scheduled': 25, 'both': 50}
        aggfunc = 'max'
        for outage_type in vmax:
            savename = f'map-outage_{outage_type}_{aggfunc}-{t}i{iteration}.png'
            plt.close()
            f, ax, _ = reeds.reedsplots.map_outage_days(
                sw.casedir,
                dates=dates,
                outage_type=outage_type,
                aggfunc=aggfunc,
                vmax=vmax[outage_type],
            )
            plt.savefig(
                os.path.join(sw.casedir, 'outputs', 'Augur_plots', savename)
            )
            plt.close()
    except Exception as err:
        print(err)


def get_and_write_neue(sw, write=True):
    """
    Write dropped load across all completed years to outputs
    so it can be plotted alongside other ReEDS outputs.

    Notes
    -----
    * The denominator of NEUE is exogenous electricity demand; it does not include
    endogenous load from losses or H2 production or exogenous H2 demand.
    """
    infiles = [
        i for i in sorted(glob(
            os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', 'PRAS_*.h5')))
        if re.match(r"PRAS_[0-9]+i[0-9]+.h5", os.path.basename(i))
    ]
    eue = {}
    for infile in infiles:
        year_iteration = os.path.basename(infile)[len('PRAS_'):-len('.h5')].split('i')
        year = int(year_iteration[0])
        iteration = int(year_iteration[1])
        eue[year,iteration] = reeds.io.read_pras_results(infile)['USA_EUE'].sum()
    eue = pd.Series(eue).rename('MWh')
    eue.index = eue.index.rename(['year','iteration'])

    load = reeds.io.read_file(os.path.join(sw['casedir'],'inputs_case','load.h5'))
    loadyear = load.sum(axis=1).groupby('year').sum()

    neue = (
        (eue / loadyear * 1e6).rename('NEUE [ppm]')
        .rename_axis(['t','iteration']).sort_index()
    )

    if write:
        neue.to_csv(os.path.join(sw['casedir'],'outputs','neue.csv'))
        eue.to_csv(os.path.join(sw['casedir'],'outputs','eue.csv'))
    return neue


def get_annual_neue(case, t, iteration=0):
    """
    """
    ### Get EUE from PRAS
    dfeue = reeds.ra.get_pras_eue(case=case, t=t, iteration=iteration)

    ### Get load (for calculating NEUE)
    dfload = reeds.io.read_h5py_file(
        os.path.join(
            case,'ReEDS_Augur','augur_data',f'pras_load_{t}.h5')
    )
    dfload.index = dfeue.index

    levels = ['country','interconnect','nercr','transreg','transgrp','st','r']
    _neue = {}
    for hierarchy_level in levels:
        ### Get the region aggregator
        rmap = reeds.io.get_rmap(case=case, hierarchy_level=hierarchy_level)
        ### Get NEUE summed over year
        _neue[hierarchy_level,'sum'] = (
            dfeue.rename(columns=rmap).groupby(axis=1, level=0).sum().sum()
            / dfload.rename(columns=rmap).groupby(axis=1, level=0).sum().sum()
        ) * 1e6
        ### Get max NEUE hour
        _neue[hierarchy_level,'max'] = (
            dfeue.rename(columns=rmap).groupby(axis=1, level=0).sum()
            / dfload.rename(columns=rmap).groupby(axis=1, level=0).sum()
        ).max() * 1e6

    ### Combine it
    neue = pd.concat(_neue, names=['level','metric','region']).rename('NEUE_ppm')

    return neue


def get_shoulder_periods(sw, criterion, dfenergy_r, high_eue_periods):
    ## Stop if not needed
    if sw.GSw_PRM_StressStorageCutoff.lower() in ['off', '0', 'false']:
        print(
            f"GSw_PRM_StressStorageCutoff={sw.GSw_PRM_StressStorageCutoff} "
            "so not adding shoulder stress periods based on storage level"
        )
        return {}
    if dfenergy_r.empty:
        print(
            "No storage capacity, so no shoulder stress periods will be added "
            "based on storage level"
        )
        return {}

    ## Parse inputs
    hierarchy = reeds.io.get_hierarchy(sw.casedir)
    timeindex = reeds.timeseries.get_timeindex(sw['resource_adequacy_years'])
    cutofftype, cutoff = sw.GSw_PRM_StressStorageCutoff.lower().split('_')
    periodhours = {'day':24, 'wek':24*5, 'year':24}[sw.GSw_HourlyType]
    (hierarchy_level, ppm, stress_metric, period_agg_method) = criterion.split('_')

    ## Aggregate storage energy to hierarchy_level
    dfenergy_agg = (
        dfenergy_r.rename(columns=hierarchy[hierarchy_level])
        .groupby(axis=1, level=0).sum()
    )
    dfheadspace_MWh = dfenergy_agg.max() - dfenergy_agg
    dfheadspace_frac = dfheadspace_MWh / dfenergy_agg.max()

    shoulder_periods = {}
    for i, row in high_eue_periods[criterion, f'high_{stress_metric}'].iterrows():
        if row.r not in dfheadspace_MWh:
            continue

        day = pd.Timestamp('-'.join(row[['y','m','d']].astype(str).tolist()))

        start_headspace_MWh = dfheadspace_MWh.loc[day.strftime('%Y-%m-%d'),row.r].iloc[0]
        end_headspace_MWh = dfheadspace_MWh.loc[day.strftime('%Y-%m-%d'),row.r].iloc[-1]

        start_headspace_frac = dfheadspace_frac.loc[day.strftime('%Y-%m-%d'),row.r].iloc[0]
        end_headspace_frac = dfheadspace_frac.loc[day.strftime('%Y-%m-%d'),row.r].iloc[-1]

        day_eue = high_eue_periods[criterion, f'high_{stress_metric}'].loc[i,'EUE']
        day_index = np.where(
            timeindex == dfenergy_agg.loc[day.strftime('%Y-%m-%d')].iloc[0].name
        )[0][0]

        day_before = timeindex[day_index - periodhours]
        day_after = timeindex[(day_index + periodhours) % len(timeindex)]

        if (
            ((cutofftype == 'eue') and (end_headspace_MWh / day_eue >= float(cutoff)))
            or ((cutofftype[:3] == 'cap') and (end_headspace_frac  >= float(cutoff)))
            or (cutofftype[:3] == 'abs')
        ):
            shoulder_periods[criterion, f'after_{row.name}'] = pd.Series({
                'actual_period':day_after.strftime('y%Yd%j'),
                'y':day_after.year, 'm':day_after.month, 'd':day_after.day, 'r':row.r,
            }).to_frame().T.set_index('actual_period')
            print(f"Added {day_after} as shoulder stress period after {day}")

        if (
            ((cutofftype == 'eue') and (start_headspace_MWh / day_eue >= float(cutoff)))
            or ((cutofftype[:3] == 'cap') and (start_headspace_frac  >= float(cutoff)))
            or (cutofftype[:3] == 'abs')
        ):
            shoulder_periods[criterion, f'before_{row.name}'] = pd.Series({
                'actual_period':day_before.strftime('y%Yd%j'),
                'y':day_before.year, 'm':day_before.month, 'd':day_before.day, 'r':row.r,
            }).to_frame().T.set_index('actual_period')
            print(f"Added {day_before} as shoulder stress period before {day}")

    return shoulder_periods


def get_eue_sorted_periods(sw, t, iteration):
    ### Get storage state of charge (SOC) to use in selection of "shoulder" stress periods
    dfenergy = reeds.io.read_pras_results(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', f"PRAS_{t}i{iteration}-energy.h5")
    )
    timeindex = reeds.timeseries.get_timeindex(sw['resource_adequacy_years'])
    dfenergy.index = timeindex
    ## Sum by region
    dfenergy_r = (
        dfenergy
        .rename(columns={c: c.split('|')[1] for c in dfenergy.columns})
        .groupby(axis=1, level=0).sum()
    )

    ### Get NEUE
    neue = pd.read_csv(
        os.path.join(sw.casedir, 'outputs', f'neue_{t}i{iteration}.csv'),
        index_col=['level', 'metric', 'region'],
    ).squeeze(1)

    ### Load this year's stress periods so we don't duplicate
    stressperiods_this_iteration = pd.read_csv(
        os.path.join(
            sw['casedir'], 'inputs_case', f'stress{t}i{iteration}', 'period_szn.csv')
    )

    ### Check all stress criteria; for regions that fail, add new stress periods
    _eue_sorted_periods = {}
    failed = {}
    high_eue_periods = {}
    shoulder_periods = {}
    for criterion in sw.GSw_PRM_StressThreshold.split('/'):
        ## Example: criterion = 'transgrp_10_EUE_sum'
        (hierarchy_level, ppm, stress_metric, period_agg_method) = criterion.split('_')

        eue_periods = reeds.ra.get_eue_periods(
            case=sw.casedir, t=t, iteration=iteration,
            hierarchy_level=hierarchy_level,
            stress_metric=stress_metric,
            period_agg_method=period_agg_method,
        )

        ### Sort in descending stress_metric order
        _eue_sorted_periods[criterion] = (
            eue_periods
            .sort_values(stress_metric, ascending=False)
            .reset_index().set_index('actual_period')
        )

        ### Get the threshold(s) and see if any of them failed
        this_test = neue[hierarchy_level][period_agg_method]

        if (this_test > float(ppm)).any():
            failed[criterion] = this_test.loc[this_test > float(ppm)]
            print(f"GSw_PRM_StressThreshold = {criterion} failed for:")
            print(failed[criterion])
            ###### Add GSw_PRM_StressIncrement periods to the list for the next iteration
            high_eue_periods[criterion, f'high_{stress_metric}'] = (
                _eue_sorted_periods[criterion].loc[
                    ## Only include new stress periods for the region(s) that failed
                    _eue_sorted_periods[criterion].r.isin(failed[criterion].index)
                    ## Don't repeat existing stress periods
                    & ~(_eue_sorted_periods[criterion].index.isin(
                        stressperiods_this_iteration.actual_period))
                ]
                ## Don't add dates more than once
                .drop_duplicates(subset=['y','m','d'])
                ## Keep the GSw_PRM_StressIncrement worst periods for each region.
                ## If you instead want to keep the GSw_PRM_StressIncrement worst periods
                ## overall, use .nlargest(int(sw.GSw_PRM_StressIncrement), stress_metric)
                .groupby('r').head(int(sw.GSw_PRM_StressIncrement))
            )
            for period, row in high_eue_periods[criterion, f'high_{stress_metric}'].iterrows():
                print(
                    f"Added {period} "
                    f"({reeds.timeseries.h2timestamp(period).strftime('%Y-%m-%d')}) "
                    f"as stress period for {row.r} "
                    f"({stress_metric} = {row[stress_metric]})"
                )

            ### Include "shoulder periods" before or after each period
            ### if the storage state of charge is low
            shoulder_periods = {
                **shoulder_periods,
                **get_shoulder_periods(sw, criterion, dfenergy_r, high_eue_periods)
            }

            ### Dealing with earlier criteria may also address later criteria, so stop here
            break

        else:
            print(f"GSw_PRM_StressThreshold = {criterion} passed")

    eue_sorted_periods = pd.concat(_eue_sorted_periods, names=['criterion'])

    ### Get lists of stress periods: new (added this iteration) and all
    if len(failed):
        new_stress_periods = pd.concat(
            {**high_eue_periods, **shoulder_periods}, names=['criterion','periodtype'],
        ).reset_index().drop_duplicates(subset='actual_period', keep='first')
    else:
        return failed, None, None

    ## Reproduce the format of inputs_case/stress_period_szn.csv
    p = 'w' if sw.GSw_HourlyType == 'wek' else 'd'
    new_stressperiods_write = pd.DataFrame({
        'rep_period': new_stress_periods.actual_period,
        'year': new_stress_periods.actual_period.map(
            lambda x: int(x.strip('sy').split(p)[0])),
        'yperiod': new_stress_periods.actual_period.map(
            lambda x: int(x.strip('sy').split(p)[1])),
        'actual_period': new_stress_periods.actual_period,
    })

    ### Add new stress periods to the stress periods used for this year/iteration, then write
    newstresspath = f'stress{t}i{iteration+1}'
    os.makedirs(os.path.join(sw['casedir'], 'inputs_case', newstresspath), exist_ok=True)
    outpath = os.path.join(sw['casedir'], 'inputs_case', newstresspath, 'period_szn.csv')

    combined_periods_write = pd.concat(
        [stressperiods_this_iteration, new_stressperiods_write],
        axis=0,
    ).drop_duplicates(keep='first')

    if int(sw.GSw_PRM_CapCredit):
        pd.DataFrame(columns=['rep_period','year','yperiod','actual_period']).to_csv(
            outpath,
            index=False,
        )
    else:
        combined_periods_write.to_csv(outpath, index=False)

    ### Tables and plots for debugging
    eue_sorted_periods.round(2).rename(columns={'EUE':'EUE_MWh','NEUE':'NEUE_ppm'}).to_csv(
        os.path.join(sw.casedir, 'inputs_case', newstresspath, 'eue_sorted_periods.csv')
    )
    new_stress_periods.round(2).rename(columns={'EUE':'EUE_MWh','NEUE':'NEUE_ppm'}).to_csv(
        os.path.join(sw.casedir, 'inputs_case', newstresspath, 'new_stress_periods.csv'),
        index=False,
    )
    plot_eue_diagnostics(sw, t, iteration, high_eue_periods)

    return failed, new_stressperiods_write, combined_periods_write


def prm_increment_pras(sw, t, iteration, combined_periods_write, failed_regions):
    try:
        hmap = pd.read_csv(
            os.path.join(sw.casedir, 'inputs_case', f'stress{t}i{iteration+1}', 'hmap_allyrs.csv')
        )
        stress_hours = hmap.loc[
            hmap.actual_period.str.contains('|'.join(combined_periods_write.actual_period))
        ]
    except FileNotFoundError:
        # if there are no stress periods being modeled, use dispatch year to
        # fill in for stress hours
        stress_hours = pd.read_csv(
            os.path.join(sw.casedir, 'inputs_case', 'rep', 'hmap_myr.csv')
        )

    ## shortfall data
    # read the net shortfall (positive) and net surplus (negative) results
    # by sample from PRAS run (MWh)
    filepath = os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS',
                            f'PRAS_{sw["t"]}i{iteration}-shortfall_samples.h5')
    net_short = reeds.io.read_pras_results(filepath)
    # get number of samples
    n_samples = len(net_short)
    # collapse dict of dataframes by sample in 1 dataframe (keep index to preserve hours)
    net_short = pd.concat(
        (df.assign(**{"sample": k}) for k, df in net_short.items()), ignore_index=False)
    # convert to long format with shortfall by sample, hour, and r
    net_short.index.names=['hour']
    net_short = net_short.reset_index().set_index(['sample','hour'])
    net_short = net_short.sort_index(level=['sample', 'hour'], ascending=[True, True])
    net_short = net_short.melt(
        ignore_index=False, var_name='r', value_name='net_short_mwh').reset_index()

    # zero-out negative values (net surplus) for determining regional unserved energy totals
    net_short['net_short_mwh'] = net_short['net_short_mwh'].clip(lower=0)
    # calaculate total regional net shortfall for all hours by sample
    net_short_crit = net_short.groupby(['r','sample'], as_index=False)['net_short_mwh'].sum()

    ## get load data
    dfload = reeds.io.read_file(
        os.path.join(
        sw['casedir'],'ReEDS_Augur','augur_data',f'pras_load_{t}.h5'),
        parse_timestamps=True
    )

    # add an index to represent each hour
    dfload = dfload.reset_index().reset_index().rename(columns={"index":"hour"})

    # melt to long
    dfload = dfload.melt(id_vars=['datetime', 'hour'], var_name='r', value_name='load_mwh')

    ## get regional load for (1) all hours (2) just the stress periods
    ## total load is used to translate the ppm target to EUE, whereas
    ## the stress period load is used to back-calculate the incremental prm
    ## needed to get to the target

    # total load by r
    dfload_all = dfload.groupby(['r'], as_index=False)['load_mwh'].sum()

    # total stress period load by r
    # note: use hour0 to subset to stress periods here since load data starts with hour index 0
    dfload_stress = dfload.loc[dfload.hour.isin(stress_hours.hour0)]
    dfload_stress = dfload_stress.groupby(['r'], as_index=False)['load_mwh'].sum()
    dfload_stress = dfload_stress.rename(columns={'load_mwh':'stress_load_mwh'})

    # combine
    dfload_all = dfload_all.merge(dfload_stress)

    # transform the reliability target criteria by region from ppm into
    # unserved energy (MWh)
    dfload_all = dfload_all.merge(failed_regions, on='r')
    dfload_all['target_eue_mwh'] = (
        dfload_all['ppm'] / 1e6 * dfload_all['load_mwh']
    )

    ## calculate piece-wise linear function (plf) that estimates the change in EUE
    ## across the samples as a function of the amount of surplus added added to address
    ## unserved energy in each sample each segment of the plf is defined by a slope and
    ## two points: (x1, y1) and (x2, y2)
    plfs = net_short_crit.loc[net_short_crit.net_short_mwh > 0].copy()
    ## y-intercept: initial EUE
    plfs['intercept'] = plfs.groupby('r')['net_short_mwh'].transform('sum') / n_samples
    ## slope: computed from the lolp based on the remaining periods with unserved energy
    ## as surplus is added sort unserved by descending first to calculate slopes
    plfs = plfs.sort_values(['r', 'net_short_mwh'], ascending=False)
    plfs['slope'] = -1
    plfs['slope'] = plfs.groupby(['r'])['slope'].transform('cumsum') / n_samples
    # resort in ascending order for later calculations
    plfs = plfs.sort_values(['r', 'net_short_mwh'], ascending=True)
    ## x1: surplus to add to eliminate unserved energy from previous sample
    plfs['x1'] = plfs.groupby('r')['net_short_mwh'].shift(1, fill_value=0)
    ## x2: surplus to add to eliminate unserved energy from this sample
    plfs['x2'] = plfs['net_short_mwh']
    # compute change in y value over each segment
    plfs['Dy'] = plfs['slope'] * (plfs['x2']-plfs['x1'])
    # check: Dy should never be positive
    assert plfs['Dy'].max() <= 0, "Error in Dy calculation"
    ## y1: intercept + cumulative change in unserved (Dy)
    plfs['y1'] = plfs['intercept'] + plfs.groupby('r')['Dy'].transform(
                                                lambda x: x.cumsum().shift(1, fill_value=0))
    ## y2: y1 + change over that segment (next y1 value)
    plfs['y2'] = plfs.groupby('r')['y1'].shift(-1, fill_value=0)

    # now merge load merge with plf functions to find the segment that captures the target
    plfs = plfs.merge(dfload_all, on='r')
    plfs['seg'] = 0
    plfs.loc[(plfs['target_eue_mwh']<=plfs['y1']) & (
        plfs['target_eue_mwh']>=plfs['y2']), 'seg'] = 1
    # calculate the energy surplus to add by backtracking from the target_eue on the
    # relevant segment(y): y=a+b*x => x=(y-a)/b
    prm_increment = plfs.loc[plfs['seg']==1].copy()
    prm_increment['surplus_mwh'] = prm_increment['x1'] + (
        prm_increment['target_eue_mwh'] - prm_increment['y1']) * (1 / prm_increment['slope'])
    # calculate the prm increase as the required surplus as a fraction of
    # load during stress periods
    prm_increment['fraction'] = (
        prm_increment['surplus_mwh'] / prm_increment['stress_load_mwh']
    )
    prm_increment = prm_increment[['r','fraction']].reset_index(drop=True)
    return prm_increment


def update_prm(sw, t, iteration, failed, combined_periods_write):
    """Update the energy reserve margin by region r for stress periods, either using a
    static increment (GSw_PRM_UpdateMethod=1) or based on the estimated surplus needed by PRAS
    to recover the desired reliabiliaty criteria (GSw_PRM_UpdateMethod>1).

    Args:
        sw (pd.series): ReEDS switches for this run.
        t (int): Model solve year.
        iteration (int): ReEDS-PRAS iteration
        failed (dict): Dictionary of regions with unserved energy at the hierarchy_level
                       and their criterion evaluations
        stress_hours (pd.DataFrame): data frame of stress periods

    Returns:
        pd.DataFrame: Table of prm levels for the next PRAS iteration
    """
    # Get regions that failed criteria
    _failed_regions = []
    for criterion in failed:
        # Example: criterion = 'transgrp_10_EUE_sum'
        (hierarchy_level, ppm, __, __) = criterion.split('_')
        # Recover regions where the PRM criterion failed
        rmap = reeds.io.get_rmap(sw['casedir'], hierarchy_level=hierarchy_level).reset_index()
        df = rmap.loc[
            rmap[hierarchy_level].isin(failed[criterion].index)
        ].rename(columns={hierarchy_level:'region'})
        df['hierarchy_level'] = hierarchy_level
        df['ppm'] = float(ppm)
        _failed_regions.append(df)
    # For zones that failed multiple criteria, use the most stringent (lowest EUE target)
    failed_regions = (
        pd.concat(_failed_regions)
        .sort_values(by=['ppm'])
        .drop_duplicates(subset='r', keep='first')
    )

    ## Fixed-increment update
    if int(sw.GSw_PRM_UpdateMethod) == 1:
        prm_increment = failed_regions.copy()
        prm_increment['fraction'] = float(sw['GSw_PRM_UpdateFraction'])
    ## PRAS-informed PRM update
    else:
        prm_increment = prm_increment_pras(
            sw,
            t,
            iteration,
            combined_periods_write,
            failed_regions,
        )
    prm_increment = (
        prm_increment.rename(columns={'r':'*r'})
        .set_index('*r').fraction
    )

    ## Add the PRM increment to last iteration's PRM
    prm = pd.read_csv(
        os.path.join(sw['casedir'], 'inputs_case', f'stress{t}i{iteration}', 'prm.csv'),
        index_col='*r',
    ).fraction
    prm_next_iteration = prm.add(prm_increment, fill_value=0).round(3)

    return prm_next_iteration


#%%### Procedure
def main(sw, t, iteration=0, logging=True):
    """
    """
    #%% More imports and settings
    site.addsitedir(os.path.join(sw['casedir'],'input_processing'))
    import hourly_writetimeseries
    newstresspath = f'stress{t}i{iteration+1}'

    #%% Write consolidated NEUE so far
    try:
        _neue_simple = get_and_write_neue(sw, write=True)
        neue = get_annual_neue(sw.casedir, t, iteration=iteration)
        neue.round(2).to_csv(
            os.path.join(sw.casedir, 'outputs', f"neue_{t}i{iteration}.csv")
        )

    except Exception as err:
        if int(sw['pras']) == 2:
            print(traceback.format_exc())
        if int(sw.GSw_PRM_StressIterateMax):
            raise Exception(err)

    #%% Stop here if not iterating or if before ReEDS can build new capacity
    if (not int(sw.GSw_PRM_StressIterateMax)) or (t < int(sw['GSw_StartMarkets'])):
        return

    #%% Identify and write new stress periods
    failed, new_stressperiods_write, combined_periods_write = get_eue_sorted_periods(
        sw=sw, t=t, iteration=iteration,
    )

    #%% Stop here if all thresholds pass or if there are no new stress periods
    if (
        (not len(failed))
        or ((len(new_stressperiods_write) == 0) and (int(sw.GSw_PRM_UpdateMethod) == 0))
    ):
        print('No new stress periods and no PRM update, so stopping here')
        return

    #%% Write timeseries data for stress periods for the next iteration of ReEDS
    hourly_writetimeseries.main(
        sw=sw, reeds_path=sw['reeds_path'],
        inputs_case=os.path.join(sw['casedir'], 'inputs_case'),
        periodtype=newstresspath,
        make_plots=0,
        logging=logging
    )

    #%% Write updated PRM values
    if (
        (int(sw.GSw_PRM_UpdateMethod) == 0)
        or (len(new_stressperiods_write) and (int(sw.GSw_PRM_UpdateMethod) == 3))
    ):
        ## Not updating PRM, so copy last year's
        prm_next_iteration = pd.read_csv(
            os.path.join(sw.casedir, 'inputs_case', f'stress{t}i{iteration}', 'prm.csv'),
            index_col='*r',
        )
    else:
        prm_next_iteration = update_prm(sw, t, iteration, failed, combined_periods_write)

    prm_next_iteration.to_csv(
        os.path.join(sw.casedir, 'inputs_case', newstresspath, 'prm.csv'),
    )

    #%% Done
    return


# if __name__ == '__main__':
#     #%%###  option to run script directly for debugging
#     casedir =  "/path/to/ReEDS-2.0/runs/runname"
#     t = 2030 # previous solve year
#     iteration = 0
#     # load switches
#     sw = reeds.io.get_switches(casedir)
#     sw['t'] = t
#     sw['GSw_PRM_UpdateMethod'] = 2
#     #%%###
#     main(sw, t, iteration, logging=False)
