#%%### Imports
import pandas as pd
import numpy as np
import os
import sys
import datetime
import argparse
import h5py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
## Time the operation of this script
tic = datetime.datetime.now()

reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

#%%### Fixed inputs
tz_in = 'UTC'
tz_out = 'Etc/GMT+6'
temp_min = -50
temp_max = 60
## Only use during_quarters for techs without a monthly scheduled outage rate
during_quarters = ['spring', 'fall']
## Cap the extrapolation of forced outage rates at high/low temperatures to 0.4 because
## PJM uses a 60% capacity credit (40% = 0.4 derate) for gas CT:
## https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/2026-27-bra-elcc-class-ratings.pdf
max_extrapolated_outage_forced = 0.4

primemover2techgroup = {
    'combined_cycle': ['GAS_CC'],
    'combustion_turbine': ['GAS_CT', 'H2_COMBUSTION'],
    'diesel': ['OGS'],
    'hydro_and_psh': ['HYDRO', 'PSH'],
    'nuclear': ['NUCLEAR'],
    'steam': ['COAL', 'BIO'],
}

#%%### Functions
def extrapolate_forward_backward(
        dfin, xmin, xmax,
        numfitvals=2, polyfit_deg=1, ymin=0, ymax=1,
    ):
    """Extrapolate slopes forward and backward and fill gaps in integer steps.
    Parameters
    ----------
    dfin: pd.DataFrame
        Dataframe with x values to extrapolate as the index
    xmin: int
        Minimum x value to extrapolate to
    xmax: int
        Maximum x value to extrapolate to
    numfitvals: int, default 2
        Number of values from the beginning and end of the series to use to fit the
        backward and forward slopes, respectively
    polyfit_deg: int, default 1
        Degree of fitting polynomial to use in forward/backward extrapolations
    ymin: float, default 0
        Lower limit for extrapolated values
    ymax: float, default 1
        Upper limit for extrapolated values

    Returns
    -------
    pd.DataFrame
        Dataframe extrapolated forward and backward
    """
    xs_low = dfin.index[:numfitvals].values
    xs_high = dfin.index[-numfitvals:].values

    slope_low, intercept_low = np.polyfit(
        x=xs_low, y=dfin.loc[xs_low].values, deg=polyfit_deg)
    slope_high, intercept_high = np.polyfit(
        x=xs_high, y=dfin.loc[xs_high].values, deg=polyfit_deg)

    ## Combine back-casted, input, and forward-casted data into a single dataframe
    dfout = pd.concat([
        pd.DataFrame(
            {xmin: intercept_low + slope_low * xmin},
            index=dfin.columns,
        ).T,
        dfin,
        pd.DataFrame(
            {xmax: intercept_high + slope_high * xmax},
            index=dfin.columns,
        ).T,
    ]).reindex(range(xmin, xmax+1)).interpolate('linear').clip(upper=ymax, lower=ymin)

    return dfout


def pm_to_tech(df, inputs_case):
    """
    Broadcast prime mover timeseries data to techs.

    Parameters
    ----------
    df: pd.DataFrame
        index = timeseries
        top column level = prime movers
    inputs_case: str
        path to ReEDS-2.0/runs/{case}/inputs_case

    Returns
    -------
    pd.DataFrame
        Same format as df but with prime movers broadcasted to techs
    """
    tech_subset_table = reeds.techs.get_tech_subset_table(inputs_case)
    df_prefill = pd.concat(
        {
            i: df[pm]
            for pm in df.columns.get_level_values('prime_mover').unique()
            for i in tech_subset_table.loc[primemover2techgroup[pm]].unique()
        },
        axis=1, names=('i',)
    )

    return df_prefill


def fill_empty_techs(df_prefill, inputs_case, fillvalues_tech=None, during_quarters='all'):
    """
    Parameters
    ----------
    fillvalues_tech: pd.Series or dict with average values with which to fill missing techs.
        keys = technologies.
    during_quarters: 'all' or list of quarters.
        If a list of quarters is provided, the annual fill values will be scaled and
        applied only during the provided quarters.

    Returns
    -------
    """
    ### Parse inputs
    quarters = pd.read_csv(
        os.path.join(inputs_case, 'sets', 'quarter.csv'),
        header=None,
    ).squeeze(1).map(lambda x: x[:4]).tolist()
    if isinstance(during_quarters, str):
        assert during_quarters == 'all'
    elif isinstance(during_quarters, list):
        during_quarters = [q[:4] for q in during_quarters]
        assert all([i in quarters for i in during_quarters])
    else:
        raise ValueError(
            f"during_quarters={during_quarters} but must be 'all' or a list of quarters"
        )

    ### Case inputs
    techlist = reeds.techs.get_techlist_after_bans(inputs_case)
    val_ba = (
        pd.read_csv(os.path.join(inputs_case, 'val_ba.csv'), header=None)
        .squeeze(1).values
    )

    ### Identify techs with nonzero values that are not yet included in dataframe
    keep_techs = [i for i in fillvalues_tech.index if i in techlist]

    included_techs = df_prefill.columns.get_level_values('i').unique()
    missing_techs = [
        c for c in fillvalues_tech.index
        if ((c.lower() not in included_techs) and (c.lower() in keep_techs))
    ]
    print(f"included ({len(included_techs)}): {' '.join(sorted(included_techs))}")
    print(f"missing ({len(missing_techs)}): {' '.join(sorted(missing_techs))}")

    ### Fill data for missing techs
    if len(missing_techs):
        if 'r' in df_prefill.columns.names:
            dfout_filled = pd.concat(
                {
                    (i,r): pd.Series(index=df_prefill.index, data=fillvalues_tech[i])
                    for i in missing_techs for r in val_ba
                },
                axis=1, names=('i','r'),
            )
        else:
            dfout_filled = pd.concat(
                {
                    i: pd.Series(index=df_prefill.index, data=fillvalues_tech[i])
                    for i in missing_techs
                },
                axis=1, names=('i'),
            )

        ## If during_quarters is provided, only apply outages during those quarters
        if isinstance(during_quarters, list):
            month2quarter = pd.read_csv(
                os.path.join(inputs_case, 'month2quarter.csv'),
                index_col='month',
            ).squeeze(1).map(lambda x: x[:4])
            total_hours = len(dfout_filled)
            outage_hours = (
                dfout_filled.index.month.map(month2quarter)
                .isin(during_quarters).sum()
            )
            dfout_filled *= (total_hours / outage_hours)
            dfout_filled.loc[
                ~dfout_filled.index.month.map(month2quarter).isin(during_quarters)
            ] = 0
            ## Make sure it worked
            assert (
                dfout_filled.mean().round(3)
                == fillvalues_tech.loc[dfout_filled.columns].round(3)
            ).all()

        dfout = pd.concat([df_prefill, dfout_filled], axis=1)
    else:
        dfout = df_prefill

    return dfout


def aggregate_regions(df, inputs_case):
    """
    Parameters
    ----------
    df: pd.DataFrame with (techcol, r) MultiIndex columns and timestamp rows
    inputs_case: string path to ReEDS-2.0/runs/{casename}/inputs_case

    Returns
    -------
    pd.DataFrame with regions dimension aggregated according to case settings
    """
    r2aggreg = pd.read_csv(
        os.path.join(inputs_case, 'hierarchy_original.csv')
    ).rename(columns={'ba':'r'}).set_index('r').aggreg
    agglevel_variables = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)
    county2zone = pd.read_csv(
        os.path.join(inputs_case, 'county2zone.csv'),
        dtype={'FIPS':str},
    )
    county2zone = (
        county2zone
        .assign(FIPS='p'+county2zone.FIPS)
        .set_index('FIPS')
        .ba.loc[agglevel_variables['county_regions']]
    )
    techcol = df.columns.names[0]

    dfout = df.copy()
    if 'aggreg' in agglevel_variables['agglevel']:
        county2zone = county2zone.map(r2aggreg)
        dfout.columns = dfout.columns.map(
            lambda x: (x[0], r2aggreg[x[1]]))
        dfout = dfout.groupby(axis=1, level=[techcol,'r']).mean()

    if 'county' in agglevel_variables['agglevel']:
        val_r = pd.read_csv(
            os.path.join(inputs_case, 'val_r.csv'),
            header=None,
        ).squeeze(1)
        dfout = pd.concat(
            {
                i: (
                    dfout[i]
                    ## Get the zone for each county, or if it's already a zone, keep the zone.
                    ## Every county in a zone thus gets the same profile.
                    [val_r.map(lambda x: county2zone.get(x,x))]
                    ## Set the actual regions (could be mix of zones and counties) as index
                    .set_axis(val_r.values, axis=1)
                )
                for i in dfout.columns.get_level_values(techcol).unique()
            },
            axis=1, names=(techcol,'r'),
        )

    return dfout


def calc_outage_forced(
    reeds_path,
    inputs_case,
    max_extrapolated_outage_forced=max_extrapolated_outage_forced,
):
    """
    """
    ### Derived inputs
    sw = reeds.io.get_switches(inputs_case)
    val_ba = (
        pd.read_csv(os.path.join(inputs_case, 'val_ba.csv'), header=None)
        .squeeze(1).values
    )
    ## Static forced outage rates (for filling empties)
    outage_forced_static = pd.read_csv(
        os.path.join(inputs_case, 'outage_forced_static.csv'),
        header=None, index_col=0,
    ).squeeze(1)
    outage_forced_static.index = outage_forced_static.index.str.lower()
    outage_forced_static = (
        outage_forced_static
        .drop(reeds.techs.ignore_techs, errors='ignore')
        .copy()
    )

    ### Load temperatures
    print('Load temperatures')
    temperatures = reeds.io.get_temperatures(inputs_case)

    ### Input data
    if sw.GSw_OutageScen.lower() == 'static':
        ### Fill static data for all techs and modeled regions
        df = pd.concat(
            {r: outage_forced_static for r in val_ba},
            axis=0,
            names=('r','i'),
        ).reorder_levels(['i','r']).sort_index()
        forcedoutage_prefill = pd.concat({i: df for i in temperatures.index}, axis=1).T
        fits_forcedoutage = pd.DataFrame()
        forcedoutage_pm = pd.DataFrame()

    else:
        fits_forcedoutage_in = pd.read_csv(
            os.path.join(inputs_case, 'outage_forced_temperature.csv'),
            comment='#',
        ).pivot(index='deg_celsius', columns='prime_mover', values='outage_frac')

        ### Extrapolate slopes and fill gaps in integer steps
        fits_forcedoutage = extrapolate_forward_backward(
            dfin=fits_forcedoutage_in, xmin=temp_min, xmax=temp_max,
            ymax=max_extrapolated_outage_forced,
        )

        ### Get temperature-dependent outage rate by prime mover and state
        forcedoutage_pm = pd.concat(
            {pm: temperatures.replace(fits_forcedoutage[pm]) for pm in fits_forcedoutage},
            axis=1, names=('prime_mover',),
        ).astype(np.float32)

        ### Map from prime movers to techs
        forcedoutage_prefill = pm_to_tech(df=forcedoutage_pm, inputs_case=inputs_case)

    ### Fill missing hourly data with tech-specific static values
    outage_forced_hourly = fill_empty_techs(
        df_prefill=forcedoutage_prefill,
        inputs_case=inputs_case,
        fillvalues_tech=outage_forced_static,
    )

    ### This file has a unique format so aggregate it now if necessary
    forcedoutage_pm = aggregate_regions(forcedoutage_pm, inputs_case)
    outage_forced_hourly = aggregate_regions(outage_forced_hourly, inputs_case)

    return {
        'fits_forcedoutage': fits_forcedoutage,
        'forcedoutage_pm': forcedoutage_pm,
        'outage_forced_hourly': outage_forced_hourly,
    }


def write_outages(df, h5path):
    names = df.columns.names
    namelengths = {
        name: df.columns.get_level_values(name).map(len).max()
        for name in names
    }
    column_level_type = f'S{max([len(i) for i in names])}'
    with h5py.File(h5path, 'w') as f:
        f.create_dataset('index', data=df.index, dtype='S29')
        ## Save both the individual column levels and the single-level delimited version
        for name in names:
            f.create_dataset(
                f'columns_{name}',
                data=df.columns.get_level_values(name),
                dtype=f'S{namelengths[name]}')
        f.create_dataset(
            'columns',
            data=(
                df.columns.map(lambda x: '|'.join(x)).rename('|'.join(names))
                if isinstance(df.columns, pd.MultiIndex)
                else df.columns
            ),
            dtype=f'S{sum(namelengths.values()) + 1}')
        f.create_dataset(
            'data', data=df, dtype=np.float32,
            compression='gzip', compression_opts=4,
        )
        
        f.create_dataset(
            'column_levels',
            data=np.array(names, dtype=column_level_type),
            dtype=column_level_type)


def plot_outage_forced(
    case,
    fits_forcedoutage,
    forcedoutage_pm,
    interactive=True,
):
    ### Prep plots
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    reeds.plots.plotparams()
    case = os.path.dirname(inputs_case.rstrip(os.sep))
    figpath = os.path.join(case,'outputs','hourly')
    os.makedirs(figpath, exist_ok=True)

    ### Plot the fits
    nicelabels = {
        'combined_cycle': 'Combined cycle',
        'combustion_turbine': 'Combustion turbine',
        'steam': 'Steam turbine',
        'nuclear': 'Nuclear',
        'hydro_and_psh': 'Hydro and PSH',
        'diesel': 'Diesel',
    }
    colors = dict(zip(nicelabels.values(), [f'C{i}' for i in range(10)]))
    fits_in = pd.read_csv(
        os.path.join(case, 'inputs_case', 'outage_forced_temperature.csv'),
        comment='#',
    )
    mintemp = fits_in.deg_celsius.min()
    maxtemp = fits_in.deg_celsius.max()

    temperatures = reeds.io.get_temperatures(case)

    plt.close()
    f,ax = plt.subplots()
    df = fits_forcedoutage.rename(columns=nicelabels)*100
    for k, v in nicelabels.items():
        df.loc[mintemp:maxtemp, v].plot(ax=ax, color=colors[v], label=v, ls='-')
        df.loc[:, v].plot(ax=ax, color=colors[v], ls='--', label='_nolabel')
    ax.legend(frameon=False, title=None, fontsize='large')
    ax.set_ylabel('Forced outage rate [%]')
    ax.set_xlabel('Temperature [°C]')
    ax.set_ylim(0)
    ax.set_xlim(temperatures.min().min(), temperatures.max().max())
    ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    reeds.plots.despine(ax)
    plt.savefig(os.path.join(figpath, 'FOR-fits.png'))
    if interactive:
        plt.show()
    else:
        plt.close()

    ### Plot forced outage rates
    dfmap = reeds.io.get_dfmap(case)
    dfzones = dfmap['r']
    aggfunc = 'mean'

    for pm in primemover2techgroup:
        dfdata = forcedoutage_pm[pm].copy() * 100

        plt.close()
        f, ax = reeds.plots.map_years_months(
            dfzones=dfzones, dfdata=dfdata, aggfunc=aggfunc,
            title=f"Monthly {aggfunc}\nforced outage rate,\n{nicelabels.get(pm,pm)} [%]",
        )
        plt.savefig(os.path.join(figpath, f'FOR_monthly-{aggfunc}-{pm}.png'))
        if interactive:
            plt.show()
        else:
            plt.close()


def calc_outage_scheduled(reeds_path, inputs_case, during_quarters=during_quarters):
    sw = reeds.io.get_switches(inputs_case)
    ## Static scheduled outage rates (for filling empties)
    outage_scheduled_static = pd.read_csv(
        os.path.join(inputs_case, 'outage_scheduled_static.csv'),
        header=None, index_col=0,
    ).squeeze(1)
    outage_scheduled_static.index = outage_scheduled_static.index.str.lower()
    outage_scheduled_static = (
        outage_scheduled_static
        .drop(reeds.techs.ignore_techs, errors='ignore')
        .copy()
    )

    ### Monthly scheduled outage rates
    outage_scheduled_monthly = pd.read_csv(
        os.path.join(inputs_case, 'outage_scheduled_monthly.csv'),
        index_col=['prime_mover','month'],
    ).squeeze(1).unstack('prime_mover')

    timeindex = pd.Series(
        index=reeds.timeseries.get_timeindex(sw.resource_adequacy_years_list)
    )
    outage_scheduled_pm = pd.DataFrame(
        {
            pm: timeindex.index.month.map(outage_scheduled_monthly[pm]).values
            for pm in outage_scheduled_monthly
        },
        index=timeindex.index,
        dtype=np.float32,
    )
    outage_scheduled_pm.columns = outage_scheduled_pm.columns.rename('prime_mover')

    outage_scheduled_tech = pm_to_tech(outage_scheduled_pm, inputs_case)

    outage_scheduled_hourly = fill_empty_techs(
        df_prefill=outage_scheduled_tech,
        inputs_case=inputs_case,
        fillvalues_tech=outage_scheduled_static,
        during_quarters=during_quarters,
    )

    return outage_scheduled_hourly


#%%
def main(reeds_path, inputs_case, debug=0, interactive=False):
    ### Forced outages
    print('Get forced outage rates')
    dfforced = calc_outage_forced(reeds_path, inputs_case)
    print('Write forced outage rates')
    write_outages(
        df=dfforced['outage_forced_hourly'],
        h5path=os.path.join(inputs_case, 'outage_forced_hourly.h5'),
    )
    ## Make sure it worked
    reeds.io.get_outage_hourly(inputs_case, 'forced')
    if debug:
        plot_outage_forced(
            case=os.path.abspath(os.path.join(inputs_case, '..')),
            fits_forcedoutage=dfforced['fits_forcedoutage'],
            forcedoutage_pm=dfforced['forcedoutage_pm'],
            interactive=interactive,
        )

    ### Scheduled outages
    print('Get scheduled outage rates')
    outage_scheduled_hourly = calc_outage_scheduled(reeds_path, inputs_case)
    print('Write scheduled outage rates')
    write_outages(
        df=outage_scheduled_hourly,
        h5path=os.path.join(inputs_case, 'outage_scheduled_hourly.h5'),
    )
    ## Make sure it worked
    reeds.io.get_outage_hourly(inputs_case, 'scheduled')


#%%### Run it
if __name__ == '__main__':
    #%% Parse args
    parser = argparse.ArgumentParser(
        description='Calculate temperature-dependent forced-outage rates',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('reeds_path', help='ReEDS-2.0 directory')
    parser.add_argument('inputs_case', help='ReEDS-2.0/runs/{case}/inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    # #%% Settings for testing
    # reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # inputs_case = os.path.join(reeds_path, 'runs', 'v20250508_prasM0_Pacific', 'inputs_case')
    # interactive = True
    # debug = 1

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )
    print('Starting outage_rates.py')  
    #%% Run it
    main(reeds_path=reeds_path, inputs_case=inputs_case)

    #%% All done
    reeds.log.toc(
        tic=tic, year=0, process='input_processing/outage_rates.py', 
        path=os.path.join(inputs_case,'..'),
    )
    print('Finished outage_rates.py')
