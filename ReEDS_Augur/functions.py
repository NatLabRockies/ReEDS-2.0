# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 19:31:59 2021

@author: afrazier
"""
#%%### Imports
import numpy as np
import os, sys, logging
import pandas as pd
import datetime
import re
from glob import glob

#%%### Functions

def makelog(scriptname, logpath):
    ### Set up logger
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    eh = logging.StreamHandler(sys.stderr)
    eh.setLevel(logging.CRITICAL)
    class StreamToLogger(object):
        """
        https://stackoverflow.com/questions/19425736/
        how-to-redirect-stdout-and-stderr-to-logger-in-python
        """
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level
            self.linebuf = ''

        def write(self, buf):
            for line in buf.rstrip().splitlines():
                self.logger.log(self.level, line.rstrip())
        
        def flush(self):
            pass

    logging.basicConfig(
        level=logging.INFO,
        format=(os.path.basename(scriptname)+' | %(asctime)s | %(levelname)s | %(message)s'),
        handlers=[logging.FileHandler(logpath, mode='a'), sh, eh],
    )
    log = logging.getLogger(__name__)
    sys.stdout = StreamToLogger(log, logging.INFO)
    sys.stderr = StreamToLogger(log, logging.ERROR)

    return log


def get_switches(casedir):
    """
    """
    ### ReEDS switches
    rsw = pd.read_csv(
        os.path.join(casedir, 'inputs_case', 'switches.csv'),
        index_col=0, header=None, squeeze=True)
    ### Augur-specific switches
    asw = pd.read_csv(
        os.path.join(casedir, 'ReEDS_Augur', 'augur_switches.csv'),
        index_col='key')
    for i, row in asw.iterrows():
        if row['dtype'] == 'list':
            row.value = row.value.split(',')
            try:
                row.value = [int(i) for i in row.value]
            except ValueError:
                pass
        elif row['dtype'] == 'boolean':
            row.value = False if row.value.lower() == 'false' else True
        elif row['dtype'] == 'str':
            row.value = str(row.value)
        elif row['dtype'] == 'int':
            row.value = int(row.value)
        elif row['dtype'] == 'float':
            row.value = float(row.value)
    ### Combine
    sw = pd.concat([rsw, asw.value])
    ### Format a few datatypes
    for key in ['osprey_years']:
        sw[key] = [int(y) for y in sw[key].split('_')]
    ### Get number of threads to use in Osprey/PRAS
    threads_pattern = re.compile(r'threads\s*=\s*(\d+)')
    with open(os.path.join(casedir,'cplex.opt')) as f:
        text = f.read()
    threads = int(threads_pattern.findall(text)[0])
    sw['threads'] = threads
    ### Determine whether run is on HPC
    sw['hpc'] = True if int(os.environ.get('REEDS_USE_SLURM',0)) else False
    ### Add the run location
    sw['casedir'] = casedir
    sw['reeds_path'] = os.path.dirname(os.path.dirname(casedir))
    ### Get the number of hours per period to use in Osprey
    sw['hoursperperiod'] = {'day':24, 'wek':120, 'year':24}[sw['GSw_HourlyType']]
    sw['periodsperyear'] = {'day':365, 'wek':73, 'year':365}[sw['GSw_HourlyType']]

    return sw


def h2timestamp(h):
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
    return pd.to_datetime(f'y{y}d{d}h{hr}', format='y%Yd%jh%H')


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


def delete_csvs(sw):
    """
    Delete temporary csv, pkl, and h5 files
    """
    dropfiles = (
        glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.pkl"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.h5"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.csv"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"osprey_outputs_{sw['t']}.gdx"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','PRAS',f"PRAS_{sw['t']}.pras"))
    )

    for keyword in sw['keepfiles']:
        dropfiles = [f for f in dropfiles if not os.path.basename(f).startswith(keyword)]

    for f in dropfiles:
        os.remove(f)


def toc(tic, year, process, path=''):
    """
    append timing data to meta file
    """
    now = datetime.datetime.now()
    try:
        with open(os.path.join(path,'meta.csv'), 'a') as METAFILE:
            METAFILE.writelines(
                '{},{},{},{},{}\n'.format(
                    year, process,
                    datetime.datetime.isoformat(tic), datetime.datetime.isoformat(now),
                    (now-tic).total_seconds()
                )
            )
    except:
        print('meta.csv not found or not writeable')
        pass


def dr_dispatch(poss_dr_changes, ts_length, hrs, eff=1):
    """
    Calculate the battery level and curtailment recovery profiles.
    Since everything here is in numpy, we can try using numba.jit to speed it up.
    """
    # Initialize some necessary arrays since numba can't do np.clip
    curt = np.where(poss_dr_changes > 0, poss_dr_changes, 0)
    avail = np.where(poss_dr_changes < 0, -poss_dr_changes, 0)
    # Initialize the dr shifting and curtailment recovery to be 0 in all hours
    curt_recovered = np.zeros((ts_length, poss_dr_changes.shape[1]))
    # Loop through all hours and identify how much curtailment that hour could
    # mitigate from the available load shifting
    for n in range(0, ts_length):
        n1 = max(0, n-hrs[0])
        n2 = min(ts_length, n+hrs[1])
        # maximum curtailment this hour can shift load into
        # calculated as the cumulative sum of curtailment across all hours
        # this hour can reach, identifying the max cumulative shifting allowed
        # and subtracting off the desired shifting that can't happen
        cum = np.cumsum(curt[n1:n2, :], axis=0)
        curt_shift = np.maximum(curt[n1:n2, :] - (cum - np.minimum(cum, avail[n, :] / eff)), 0)
        # Subtract realized curtailment reduction from appropriate hours
        curt[n1:n2, :] -= curt_shift
        # Record the amount of otherwise-curtailed energy that was
        # recovered during appropriate hours
        curt_recovered[n1:n2, :] += curt_shift
    return curt_recovered

def dr_capacity_credit(hrs, eff, ts_length, poss_dr_changes, marg_peak, cols,
                       maxhrs):
    """
    Determines the ratio of peak load that could be shifted by DR.
    """
    # Get the DR profiles
    # This is using the same function as curtailment, but with opposite meaning
    # ("how much can I increase load in this hour in order to reduce load in any
    # shiftable hours" instead of "how much can I decrease load in this hour
    # in order to increase load in any shiftable hours"), so the efficiency
    # gets applied to the opposite set of data. Hence the 1/eff.
    # If maxhrs is included, that is used as the total number of hours the
    # resource is able to be called. Really just for shed
    peak_shift = dr_dispatch(
        poss_dr_changes=poss_dr_changes,
        ts_length=ts_length, hrs=hrs, eff=1/eff
    )
    # Sort and only take maximum allowed hours
    sort_shift = np.sort(peak_shift, axis=0)[::-1]
    sort_shift = sort_shift[0:int(min(maxhrs, ts_length)), :]

    # Get the ratio of reduced peak to total peak
    results = pd.melt(
        pd.DataFrame(data=[np.round(sort_shift.sum(0) / marg_peak, decimals=5), ],
                     columns=cols)
        )
    return results
