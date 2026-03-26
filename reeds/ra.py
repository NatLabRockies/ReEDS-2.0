### Imports
import os
import sys
import numpy as np
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


### Functions
def get_pras_eue(case, t, iteration=0):
    """
    """
    ### Get PRAS outputs
    dfpras = reeds.io.read_pras_results(
        os.path.join(case, 'ReEDS_Augur', 'PRAS', f"PRAS_{t}i{iteration}.h5")
    )
    ### Create the time index
    sw = reeds.io.get_switches(case)
    dfpras.index = reeds.timeseries.get_timeindex(sw['resource_adequacy_years'])

    ### Keep the EUE columns by zone
    eue_tail = '_EUE'
    dfeue = dfpras[[
        c for c in dfpras
        if (c.endswith(eue_tail) and not c.startswith('USA'))
    ]].copy()
    ## Drop the tailing _EUE
    dfeue = dfeue.rename(
        columns=dict(zip(dfeue.columns, [c[:-len(eue_tail)] for c in dfeue])))

    return dfeue


def get_eue_periods(
        case, t, iteration=0,
        hierarchy_level='transgrp',
        stress_metric='EUE',
        period_agg_method='sum',
    ):
    """_summary_

    Args:
        sw (pd.series): ReEDS switches for this run.
        t (int): Model solve year.
        iteration (int, optional): Iteration number of this solve year. Defaults to 0.
        hierarchy_level (str, optional): column of hierarchy.csv specifying the spatial
            level over which to calculate stress_metric. Defaults to 'country'.
        stress_metric (str, optional): 'EUE' or 'NEUE'. Defaults to 'EUE'.
        period_agg_method (str, optional): 'sum' or 'max', indicating how to aggregate
            over the hours in each period. Defaults to 'sum'.

    Raises:
        NotImplementedError: if invalid value for stress_metric or GSw_PRM_StressModel

    Returns:
        pd.DataFrame: Table of periods sorted in descending order by stress metric.
    """
    sw = reeds.io.get_switches(case)
    ### Get the region aggregator
    rmap = reeds.io.get_rmap(case=case, hierarchy_level=hierarchy_level)

    ### Get EUE from PRAS
    dfeue = get_pras_eue(case=case, t=t, iteration=iteration)
    ## Aggregate to hierarchy_level
    dfeue = (
        dfeue
        .rename_axis('r', axis=1).rename_axis('h', axis=0)
        .rename(columns=rmap).groupby(axis=1, level=0).sum()
    )

    ###### Calculate the stress metric by period
    if stress_metric.upper() == 'EUE':
        ### Aggregate according to period_agg_method
        dfmetric_period = (
            dfeue
            .groupby([dfeue.index.year, dfeue.index.month, dfeue.index.day])
            .agg(period_agg_method)
            .rename_axis(['y','m','d'])
        )
    elif stress_metric.upper() == 'NEUE':
        ### Get load at hierarchy_level
        dfload = reeds.io.read_h5py_file(
            os.path.join(
                case,'ReEDS_Augur','augur_data',f'pras_load_{t}.h5')
        ).rename(columns=rmap).groupby(level=0, axis=1).sum()
        dfload.index = dfeue.index

        ### Recalculate NEUE [ppm] and aggregate appropriately
        if period_agg_method == 'sum':
            dfmetric_period = (
                dfeue
                .groupby([dfeue.index.year, dfeue.index.month, dfeue.index.day])
                .agg(period_agg_method)
                .rename_axis(['y','m','d'])
            ) / (
                dfload
                .groupby([dfload.index.year, dfload.index.month, dfload.index.day])
                .agg(period_agg_method)
                .rename_axis(['y','m','d'])
            ) * 1e6
        elif period_agg_method == 'max':
            dfmetric_period = (
                (dfeue / dfload)
                .groupby([dfeue.index.year, dfeue.index.month, dfeue.index.day])
                .agg(period_agg_method)
                .rename_axis(['y','m','d'])
            ) * 1e6

    ### Sort and drop zeros and duplicates
    dfmetric_top = (
        dfmetric_period.stack('r')
        .sort_values(ascending=False)
        .replace(0,np.nan).dropna()
        .reset_index().drop_duplicates(['y','m','d'], keep='first')
        .set_index(['y','m','d','r']).squeeze(1).rename(stress_metric)
        .reset_index('r')
    )
    ## Convert to timestamp, then to ReEDS period
    dfmetric_top['actual_period'] = [
        reeds.timeseries.timestamp2h(pd.Timestamp(*d), sw['GSw_HourlyType']).split('h')[0]
        for d in dfmetric_top.index.values
    ]

    return dfmetric_top
