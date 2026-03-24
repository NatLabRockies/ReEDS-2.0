### Imports
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from reeds import plots

os.environ['PROJ_NETWORK'] = 'OFF'

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
remotepath = '/Volumes/ReEDS/' if sys.platform == 'darwin' else r'//nrelnas01/ReEDS/'

plots.plotparams()


### Functions
def plot_interface_flows(
    case,
    year=2050,
    source='pras',
    iteration='last',
    samples=None,
    level='transreg',
    weatheryear=2012,
    decimals=0,
    flowcolors={'forward':'C0', 'reverse':'C3'},
    onlydata=False,
):
    """
    """
    sw = reeds.io.get_switches(case)
    timeindex = reeds.timeseries.get_timeindex(sw.resource_adequacy_years_list)
    hierarchy = reeds.io.get_hierarchy(case)

    if source.lower() == 'pras':
        infile, _iteration = reeds.io.get_last_iteration(
            case=case, year=year, datum='flow', samples=samples)
        dfflow = reeds.io.read_pras_results(infile).set_index(timeindex)
        ## Filter out AC/DC converters from scenarios with VSC
        dfflow = dfflow[[c for c in dfflow if '"DC_' not in c]].copy()
        ## Normalize the interface names
        renamer = {i: '→'.join(i.replace('"','').split(' => ')) for i in dfflow}
    else:
        raise NotImplementedError(f"source must be 'pras' but is '{source}'")

    ### Group by hierarchy level
    df = dfflow.rename(columns=renamer)
    aggcols = {c: '→'.join([hierarchy[level][i] for i in c.split('→')]) for c in df}
    df = df.rename(columns=aggcols).groupby(axis=1, level=0).sum()
    df = df[[c for c in df if c.split('→')[0] != c.split('→')[1]]].copy()
    if df.shape[1] == 0:
        raise NotImplementedError(
            "No interfaces to plot (expected if you're only modeling one hierarchy level)")
    ### Keep only a single direction
    dflevel = {}
    for c in df:
        r, rr = c.split('→')
        ## Sort alphabetically
        if r < rr:
            dflevel[f'{r}→{rr}'] = dflevel.get(f'{r}→{rr}', 0) + df[c]
        else:
            dflevel[f'{rr}→{r}'] = dflevel.get(f'{rr}→{r}', 0) - df[c]
    dflevel = pd.concat(dflevel, axis=1)
    ## Redefine the dominant direction as "forward"
    toswap = {}
    for c in dflevel:
        if dflevel[c].mean() < 0:
            dflevel[c] *= -1
            toswap[c] = '→'.join(c.split('→')[::-1])
    dfplot = dflevel.rename(columns=toswap)
    if onlydata:
        return dfplot

    ###### Plot it
    ## Sort interfaces by fraction of flow that is "forward"
    forward_fraction = (
        dfplot.clip(lower=0).sum() / dfplot.abs().sum()
    ).sort_values(ascending=False)
    interfaces = forward_fraction.index
    nrows = len(interfaces)
    if nrows == 0:
        raise NotImplementedError(
            "No interfaces to plot (expected if you're only modeling one hierarchy level)")
    elif nrows == 1:
        coords = {'distribution':{interfaces[0]: 0}, 'profile':{interfaces[0]: 1}}
    else:
        coords = {
            'distribution': {interface: (row,0) for row, interface in enumerate(interfaces)},
            'profile': {interface: (row,1) for row, interface in enumerate(interfaces)},
        }
    index = dfplot.loc[str(weatheryear)].index
    plt.close()
    f,ax = plt.subplots(
        nrows, 2, figsize=(10,nrows*0.5), sharex='col', sharey='row',
        gridspec_kw={'width_ratios':[0.06,1], 'wspace':0.1},
    )
    for interface in interfaces:
        ### Hourly
        ## Positive
        ax[coords['profile'][interface]].fill_between(
            index,
            dfplot.loc[str(weatheryear)][interface].clip(lower=0),
            color=flowcolors['forward'], lw=0.1, label='Forward')
        ## Negative
        ax[coords['profile'][interface]].fill_between(
            index,
            dfplot.loc[str(weatheryear)][interface].clip(upper=0),
            color=flowcolors['reverse'], lw=0.1, label='Reverse')
        ### Distribution
        ## Positive
        ax[coords['distribution'][interface]].fill_between(
            np.linspace(0,1,len(dfplot)),
            dfplot[interface].sort_values(ascending=False).clip(lower=0),
            color=flowcolors['forward'], lw=0,
        )
        ## Negative
        ax[coords['distribution'][interface]].fill_between(
            np.linspace(0,1,len(dfplot)),
            dfplot[interface].sort_values(ascending=False).clip(upper=0),
            color=flowcolors['reverse'], lw=0,
        )
        ### Formatting
        ax[coords['profile'][interface]].axhline(0,c='C7',ls=':',lw=0.5)
        ax[coords['distribution'][interface]].set_yticks([0])
        ax[coords['distribution'][interface]].set_yticklabels([])
        ax[coords['distribution'][interface]].set_ylabel(
            f'{interface}\n({forward_fraction[interface]*100:.{decimals}f}% →)',
            rotation=0, ha='right', va='center', fontsize='medium')
    ### Formatting
    ax[coords['distribution'][interfaces[-1]]].set_xticks([0,0.5,1])
    ax[coords['distribution'][interfaces[-1]]].set_xticklabels([0,'','100%'])
    ax[coords['profile'][interfaces[0]]].annotate(
        'Forward ', (0.5,1), xycoords='axes fraction', ha='right', annotation_clip=False,
        weight='bold', fontsize='large', color=flowcolors['forward'],
    )
    ax[coords['profile'][interfaces[0]]].annotate(
        ' Reverse', (0.5,1), xycoords='axes fraction', ha='left', annotation_clip=False,
        weight='bold', fontsize='large', color=flowcolors['reverse'],
    )
    ax[coords['profile'][interfaces[0]]].annotate(
        f'{os.path.basename(case)}\nsystem year: {year}i{iteration}\nweather year: {weatheryear}',
        (1,1), xycoords='axes fraction', ha='right', annotation_clip=False,
    )
    ## Full time range
    ax[coords['profile'][interfaces[-1]]].set_xlim(index[0]-pd.Timedelta('1D'), index[-1])
    ax[coords['profile'][interfaces[-1]]].xaxis.set_major_locator(mpl.dates.MonthLocator())
    ax[coords['profile'][interfaces[-1]]].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    plots.despine(ax)
    return f, ax, dfplot


def plot_storage_soc(
    case,
    year=2050,
    source='pras',
    samples=None,
    level='transgrp',
    onlydata=False,
):
    """Plot storage state of charge from PRAS"""
    sw = reeds.io.get_switches(case)
    timeindex = reeds.timeseries.get_timeindex(sw.resource_adequacy_years_list)
    hierarchy = reeds.io.get_hierarchy(case)

    ### Get storage state of charge
    if source.lower() == 'pras':
        infile, _iteration = reeds.io.get_last_iteration(
            case=case, year=year, datum='energy', samples=samples)
        dfenergy = reeds.io.read_pras_results(infile).set_index(timeindex)
    else:
        raise NotImplementedError(f"source must be 'pras' but is '{source}'")
    ## Sum by hierarchy level
    dfenergy_r = (
        dfenergy
        .rename(columns={c: c.split('|')[1] for c in dfenergy.columns})
        .groupby(axis=1, level=0).sum()
    )
    dfenergy_agg = (
        dfenergy_r.rename(columns=hierarchy[level])
        .groupby(axis=1, level=0).sum()
    )
    # dfheadspace_MWh = dfenergy_agg.max() - dfenergy_agg
    # dfheadspace_frac = dfheadspace_MWh / dfenergy_agg.max()
    dfsoc_frac = dfenergy_agg / dfenergy_agg.max()
    if onlydata:
        return dfsoc_frac

    ### Get stress periods
    set_szn = pd.read_csv(
        os.path.join(case, 'inputs_case', f'stress{year}i{_iteration}', 'set_szn.csv')
    ).rename(columns={'*szn':'szn'})
    set_szn['datetime'] = set_szn.szn.map(reeds.timeseries.h2timestamp)
    set_szn['date'] = set_szn.datetime.map(lambda x: x.strftime('%Y-%m-%d'))
    set_szn['year'] = set_szn.datetime.map(lambda x: x.year)

    ### Plot it
    years = sw.resource_adequacy_years_list
    colors = plots.rainbowmapper(dfsoc_frac.columns)
    numrows = len(years)
    plt.close()
    f,ax = plt.subplots(
        numrows, 1, sharey=True, figsize=(13.33,8),
        gridspec_kw={'hspace':1.0},
    )
    for row, y in enumerate(years):
        df = dfsoc_frac.loc[str(y)]
        for region, color in colors.items():
            (df-1)[region].plot.area(
                ax=ax[row], stacked=False, legend=False, lw=0.1, color=color, alpha=0.8,
            )
        for tstart in set_szn.loc[set_szn.year==y, 'datetime'].values:
            ax[row].axvspan(tstart, tstart + pd.Timedelta('1D'), lw=0, color='k', alpha=0.15)
        ax[row].set_ylim(-1,0)
        ax[row].set_ylabel(y, rotation=0, ha='right', va='center', weight='normal')
        if row < numrows - 1:
            ax[row].set_xticklabels([])
    ax[0].set_yticks([])
    ## Strip the year
    ax[-1].set_xticks(ax[-1].get_xticks())
    ax[-1].set_xticklabels([i._text.split('\n')[0] for i in ax[-1].get_xticklabels()])
    ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1),
        frameon=False, columnspacing=0.5, handlelength=0.7, handletextpad=0.3,
        title=f'Storage\nstate of charge\nby {level},\n{year}i{_iteration}\n[fraction]',
        title_fontsize=12,
    )
    plots.despine(ax, left=False)
    return f, ax, dfsoc_frac


def plot_pras_eue_timeseries_full(
    case,
    year=2050,
    iteration='last',
    samples=None,
    level='transgrp',
    ymax=None,
    figsize=None,
):
    """
    Dropped load timeseries
    """
    sw = reeds.io.get_switches(case)
    if iteration == 'last':
        _, _iteration = reeds.io.get_last_iteration(
            case=case, year=year, samples=samples)
    else:
        _iteration = iteration
    infile = os.path.join(
        case, 'ReEDS_Augur', 'PRAS',
        f"PRAS_{year}i{_iteration}" + (f'-{samples}' if samples is not None else '') + '.h5'
    )
    dfpras = reeds.io.read_pras_results(infile)
    dfpras.index = reeds.timeseries.get_timeindex(sw.resource_adequacy_years)
    ## Only keep EUE
    dfpras = dfpras[[
        c for c in dfpras if (c.endswith('EUE') and not c.lower().startswith('usa'))
    ]].copy()

    ### Sum by hierarchy level
    hierarchy = reeds.io.get_hierarchy(case)
    dfpras_agg = (
        dfpras
        .rename(columns={c: c[:-len('_EUE')] for c in dfpras})
        .rename(columns=hierarchy[level])
        .groupby(axis=1, level=0).sum()
        / 1e3
    )

    wys = sw.resource_adequacy_years_list
    if figsize is None:
        figsize = (6, 0.7*len(wys))
    colors = plots.rainbowmapper(dfpras_agg.columns)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(len(wys), 1, sharex=False, sharey=True, figsize=figsize)
    for row, y in enumerate(wys):
        timeindex_y = pd.date_range(
            f"{y}-01-01", f"{y+1}-01-01", inclusive='left', freq='H',
            tz='Etc/GMT+6')[:8760]
        for region, color in colors.items():
            ax[row].fill_between(
                timeindex_y, dfpras_agg.loc[str(y),region:].sum(axis=1).values,
                lw=1, color=color, label=region)
        ### Formatting
        ax[row].annotate(
            y, (0.01,1), xycoords='axes fraction',
            fontsize=14, weight='bold', va='top')
        ax[row].set_xlim(
            pd.Timestamp(f"{y}-01-01 00:00-05:00"),
            pd.Timestamp(f"{y}-12-31 23:59-05:00"))
        ax[row].xaxis.set_major_locator(mpl.dates.MonthLocator(tz='Etc/GMT+6'))
        ax[row].xaxis.set_minor_locator(mpl.dates.WeekdayLocator(byweekday=mpl.dates.SU))
        if row == len(wys) - 1:
            ax[row].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
        else:
            ax[row].set_xticklabels([])
    ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1),
        frameon=False, columnspacing=0.5, handlelength=0.7, handletextpad=0.3,
    )
    ax[0].set_ylim(0, ymax)
    ax[len(wys)-1].set_ylabel('Expected unserved energy [GWh/h]', y=0, ha='left')
    plots.despine(ax)
    return f, ax, dfpras, _iteration


def plot_pras_samples(
    case,
    tstart='2012-08-01',
    tend='2012-08-07',
    plottype='outage',
    drawload=False,
    region='country/USA',
    year=2050,
    iteration='last',
    samples=None,
    units_cap='GW',
):
    """
    """
    ### Parse inputs
    assert plottype.lower().startswith('avail') or plottype.lower().startswith('out')
    if isinstance(samples, int):
        if samples > 50:
            raise ValueError(f"samples={samples} but must be <50 for performance")

    ### Get shared case inputs
    sw = reeds.io.get_switches(case)
    timeindex = reeds.timeseries.get_timeindex(sw.resource_adequacy_years)
    t = reeds.io.get_years(case)[-1] if year in [0, None, 'last'] else year
    _iteration = (
        reeds.io.get_last_iteration(case, t) if iteration in [None, 'last']
        else iteration
    )
    rs = reeds.inputs.parse_regions(region, case)

    bokehcolors, plotorder = reeds.reedsplots.get_tech_colors_order(order='fuel_storage_vre')

    ### Get PRAS input data
    dfpras = reeds.io.get_pras_system(case=case, year=t, iteration=_iteration)
    for key in dfpras:
        dfpras[key].index = timeindex

    dfload = (
        dfpras['load']
        [[r for r in rs if r in dfpras['load']]]
    ).sum(axis=1)
    if units_cap.lower() in ['%', 'percent', 'load', 'peak', 'peakload']:
        peakload = dfpras['load'][[r for r in rs if r in dfpras['load']]].sum(axis=1).max()
        units_scale = 100 / peakload
        unitslabel = '% peak load'
    else:
        units_scale = {'MW': 1, 'GW': 1e-3, 'TW': 1e-6}[units_cap.upper()]
        unitslabel = units_cap.upper()
    dfload *= units_scale

    ### Get unit availability
    filebase = os.path.join(
        case, 'ReEDS_Augur', 'PRAS',
        f"PRAS_{t}i{_iteration}"
        f"{f'-{samples}' if isinstance(samples, int) else ''}"
    )
    dictavail = reeds.io.read_pras_results(filebase + '-avail.h5')
    for key in dictavail:
        dictavail[key].index = timeindex
        if plottype.lower().startswith('out'):
            dictavail[key] = 1 - dictavail[key]

    ### Get storage energy
    dictenergy = reeds.io.read_pras_results(filebase + '-energy_samples.h5')
    for key in dictenergy:
        dictenergy[key].index = timeindex

    ### Parse indices
    name2iru = {
        key: (
            dfpras[f'{key}cap'].columns.to_frame()
            .droplevel(['i','r','unit'])
            .drop(columns='name')
        )
        for key in ['gen','stor','genstor']
    }

    keeptimes = dfpras['gencap'].loc[tstart:tend].index

    ### Plot it
    nrows = samples if isinstance(samples, int) else int(sw.pras_samples)
    figsize = (len(keeptimes) / 20, nrows * 1)
    plt.close()
    f, ax = plt.subplots(
        nrows, 1, figsize=figsize, sharex=True, sharey=True,
    )
    for row, s in enumerate(range(1, nrows+1)):
        dfgen = (
            dfpras['gencap'].droplevel(['i','r','unit'], axis=1)
            * dictavail[s]
            * units_scale
        ).dropna(axis=1, how='all')
        dfgen.columns = pd.MultiIndex.from_frame(name2iru['gen'].loc[dfgen.columns])
        sample_regions = dfgen.columns.get_level_values('r').unique()

        dfenergy = (
            dfpras['storcap'].droplevel(['i','r','unit'], axis=1)
            .clip(upper=dictenergy[s])
            * dictavail[s][dictenergy[s].columns]
            * units_scale
        )
        dfenergy.columns = pd.MultiIndex.from_frame(name2iru['stor'].loc[dfenergy.columns])

        dfslice = (
            pd.concat([dfgen, dfenergy], axis=1)
            .loc[:, (slice(None), [r for r in rs if r in sample_regions])]
            .droplevel(['r','unit'], axis=1)
            .loc[tstart:tend]
        )
        ## Aggregate units
        dfslice.columns = reeds.reedsplots.simplify_techs(dfslice.columns)
        dfslice = dfslice.groupby('i', axis=1).sum()
        dfslice = dfslice[[c for c in plotorder if c in dfslice]].copy()

        ## Available capacity
        reeds.plots.stackbar(
            df=dfslice, ax=ax[row], colors=bokehcolors,
            width=pd.Timedelta('1H'), net=False, align='center',
        )
        ## Load
        if (not plottype.lower().startswith('out')) and drawload:
            ax[row].plot(
                dfload.loc[keeptimes].index,
                dfload.loc[keeptimes].values,
                lw=1.25, c='k',
                path_effects=[pe.withStroke(linewidth=2.5, foreground='w', alpha=0.8)],
            )

    ## Formatting
    locator = ax[-1].xaxis.get_major_locator()
    ax[-1].xaxis.set_major_formatter(mpl.dates.ConciseDateFormatter(locator))
    ax[0].set_xlim(
        keeptimes[0] - pd.Timedelta('1H'),
        keeptimes[-1] + pd.Timedelta('1H')
    )
    ax[-1].yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax[-1].set_ylabel(
        f"{'Outage' if plottype.lower().startswith('out') else 'Available'} capacity "
        f"[{unitslabel}]",
        y=0, va='bottom', ha='left',
    )
    reeds.plots.despine(ax)

    return f, ax, {'pras':dfpras, 'avail':dictavail, 'energy':dictenergy}
