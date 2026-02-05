import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


def get_timeindex(
    years=list(range(2007, 2014)) + list(range(2016, 2024)),
    tz='Etc/GMT+6',
):
    """
    ReEDS time indices are in Central Standard Time,
    and leap years drop Dec 31 instead of Feb 29
    """
    _years = [int(y) for y in years.split('_')] if isinstance(years, str) else years
    timeindex = np.ravel(
        [
            pd.date_range(
                f'{y}-01-01',
                f'{y + 1}-01-01',
                freq='H',
                inclusive='left',
                tz=tz,
            )[:8760]
            for y in _years
        ]
    )
    return timeindex


def h2timestamp(h, tz='Etc/GMT+6'):
    """
    Map ReEDS timeslice to actual timestamp
    """
    hr = int(h.split('h')[1]) - 1 if 'h' in h else 0
    if 'd' in h:
        y = int(h.strip('sy').split('d')[0])
        d = int(h.split('d')[1].split('h')[0])
    else:
        y = int(h.strip('sy').split('w')[0])
        w = int(h.split('w')[1].split('h')[0])
        d = (w - 1) * 5 + 1 + hr // 24
    out = pd.to_datetime(f'y{y}d{d}h{hr % 24}', format='y%Yd%jh%H').tz_localize(tz)
    return out


def timestamp2h(ts, GSw_HourlyType='day'):
    """
    Map actual timestamp to ReEDS period
    """
    y = ts.year
    d = int(ts.strftime('%j').lstrip('0'))
    if GSw_HourlyType == 'wek':
        w = d // 5
        h = (d % 5) * 24 + ts.hour + 1
        out = f'y{y}w{w:>03}h{h:>03}'
    else:
        h = ts.hour + 1
        out = f'y{y}d{d:>03}h{h:>03}'
    return out


def timeslice_to_timestamp(case, param):
    ### Load the timestamps and other ReEDS settings
    h_dt_szn = pd.read_csv(os.path.join(case, 'inputs_case', 'rep', 'h_dt_szn.csv'))
    sw = reeds.io.get_switches(case)
    sw['GSw_HourlyWeatherYears'] = [int(y) for y in sw['GSw_HourlyWeatherYears'].split('_')]
    ### Get the timestamps for the modeled weather yeras
    hs = h_dt_szn.loc[h_dt_szn.year.isin(sw['GSw_HourlyWeatherYears']), 'h'].to_frame()
    hs['timestamp'] = pd.concat(
        [
            pd.Series(
                pd.date_range(
                    f'{y}-01-01',
                    f'{y + 1}-01-01',
                    inclusive='left',
                    freq='H',
                    tz='Etc/GMT+6',
                )[:8760]
            )
            for y in sw['GSw_HourlyWeatherYears']
        ]
    ).values
    hs = hs.set_index('timestamp').h.tz_localize('UTC').tz_convert('Etc/GMT+6')
    ### Load the ReEDS output file
    rename = {'allh': 'h', 'allt': 't'}
    dfin_timeslice = reeds.io.read_output(case, param).rename(columns=rename)
    ## check if empty
    if dfin_timeslice.empty:
        raise Exception(f'{param}.csv is empty; skipping timestamp processing')
    indices = [c for c in dfin_timeslice if c != 'Value']
    if 'h' not in indices:
        raise Exception(f"{param} does not have an h index: {indices}")
    indices_fixed = [c for c in indices if c != 'h']
    ### Convert to an hourly timeseries
    dfout_h = (
        dfin_timeslice.pivot(index='h', columns=indices_fixed, values='Value')
        ## Create entries for each timestamp but labeled by timeslices
        .loc[hs]
        .fillna(0)
        ## Add the timestamp index
        .set_index(hs.index)
    )
    return dfout_h
