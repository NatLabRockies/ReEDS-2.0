#%% Imports
import os
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import geopandas as gpd
import shapely
import argparse
import traceback
import cmocean

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from reeds import plots

plots.plotparams()


#%% Fixed inputs
interactive = False


#%% Globals
fuel_price_scenarios = {
    'Gas': {
        'low': 'ng_AEO_{datayear}_HOG.csv',
        'mid': 'ng_AEO_{datayear}_reference.csv',
        'high': 'ng_AEO_{datayear}_LOG.csv',
    },
    'Coal': {'mid': 'coal_AEO_{datayear}_reference.csv'},
    'Uranium': {'mid': 'uranium_AEO_{datayear}_reference.csv'},
}


#%% Plotting functions
def get_bokeh_colors():
    bokehcolors = pd.read_csv(
        os.path.join(
            reeds.io.reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv',
        ),
        index_col='order',
    ).squeeze(1)
    return bokehcolors


def plot_outage_scheduled(case, f=None, ax=None, color='C0', aspect=1):
    """Plot scheduled outage rate by month, one subplot for each tech"""
    sw = reeds.io.get_switches(case)

    outage_scheduled = reeds.io.get_outage_hourly(case, 'scheduled')

    techs = reeds.techs.get_techlist_after_bans(case)
    techs = [i.split('*')[0] for i in techs if i not in reeds.techs.ignore_techs]

    dfplot = outage_scheduled.loc[
        sw.GSw_HourlyWeatherYears.split('_')[0],
        [c for c in outage_scheduled if c in techs]
    ] * 100

    if (f is None) and (ax is None):
        nrows, ncols, coords = plots.get_coordinates(dfplot.columns, aspect=aspect)

        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(ncols*1.7, nrows*1.25), sharex=True, sharey=True,
            gridspec_kw={'hspace':0.5},
        )
    else:
        nrows = ax.shape[0]
        ncols = ax.shape[1]
        _, _, coords = plots.get_coordinates(dfplot.columns, nrows=nrows, ncols=ncols)

    for tech in dfplot:
        ax[coords[tech]].plot(dfplot.index, dfplot[tech], color=color)
        ax[coords[tech]].set_title(
            tech, y=1,
            path_effects=[pe.withStroke(linewidth=2.0, foreground='w', alpha=0.8)]
        )

    ax[-1,0].set_ylabel('Scheduled outage rate [%]', va='bottom', ha='left', y=0)
    ax[-1,0].yaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
    ax[-1,0].yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax[-1,0].xaxis.set_major_locator(mpl.dates.MonthLocator(bymonth=[1,4,7,10]))
    ax[-1,0].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    ax[-1,0].xaxis.set_minor_locator(mpl.dates.MonthLocator())
    ax[-1,0].set_xlim(dfplot.index[0]-pd.Timedelta('1D'), dfplot.index[-1])
    ax[-1,0].set_ylim(0)
    plots.despine(ax)
    plots.trim_subplots(ax, nrows, ncols, dfplot.shape[1])

    return f, ax, dfplot


def plot_profile(
    case,
    datum='demand',
    year=0,
    region=None,
    weatheryears=None,
    color='k',
    hourly=False,
    f=None,
    ax=None,
    figsize=(6,4),
    yscale_zero=True,
):
    """
    Plot daily electricity demand over all weather years.
    Dark line shows daily mean; filled area shows range from daily min to daily max.
    If `hourly == True`, also show the hourly demand (need to increase the figure width
    using the `figsize` parameter and set `weatheryears` to a single year to be able to
    discern the hourly values).
    """
    ## Parse inputs
    sw = reeds.io.get_switches(case)
    t = reeds.io.get_years(case)[-1] if year in [0, None, 'last'] else year
    rs = reeds.inputs.parse_regions((region if region else case), case)
    if weatheryears is None:
        weatheryears = sw.resource_adequacy_years_list
    elif isinstance(weatheryears, int):
        weatheryears = [weatheryears]

    ## Data
    if datum in ['demand', 'load']:
        ylabel = 'Electricity demand [GW]'
        dfprofile = reeds.io.read_file(
            os.path.join(case, 'inputs_case', 'load.h5'),
            parse_timestamps=True,
        ## Convert to GW
        ) / 1e3
        dfprofile = (
            dfprofile
            .loc[t, [r for r in dfprofile if r in rs]]
            .sum(axis=1)
        )
    elif datum in ['temperature']:
        ylabel = 'Temperature [°C]'
        ...
    else:
        recf = reeds.io.get_available_capacity_weighted_cf(case, level='country') * 100
        if datum in ['wind', 'wind-ons']:
            ylabel = 'Wind CF [%]'
            dfprofile = recf['wind-ons'].squeeze(1)
        elif datum in ['upv', 'pv', 'solar']:
            ylabel = 'PV CF [%]'
            dfprofile = recf['upv'].squeeze(1)

    dfprofile = dfprofile.loc[str(min(weatheryears)):str(max(weatheryears))].copy()
    ## Use a continuous set of datetimes to avoid interpolating over missing years
    full_timeseries = pd.date_range(dfprofile.index[0], dfprofile.index[-1], freq='H')
    dfprofile = dfprofile.reindex(full_timeseries)

    dayindex = pd.date_range(
        f'{min(weatheryears)}-01-01', f'{max(weatheryears)}-12-31', freq='D',
    )
    dfday = {
        agg: dfprofile.groupby(
            [dfprofile.index.year, dfprofile.index.month, dfprofile.index.day]
        ).agg(agg)
        for agg in ['min', 'max', 'mean']
    }
    ## Drop Dec 31 when plotting a single year to match recf data
    dfday = {k: v.set_axis(dayindex[:len(v)]) for k,v in dfday.items()}

    ## Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=figsize)
    dfday['mean'].plot(ax=ax, lw=0.5, color=color)
    if hourly:
        dfprofile.plot(ax=ax, lw=0.1, color=color)
    ax.fill_between(
        dfday['mean'].index, dfday['max'], dfday['min'],
        lw=0, alpha=0.25, color=color,
    )
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.set_ylabel(ylabel)
    ax.set_xlabel(None)
    if yscale_zero:
        ax.set_ylim(0)
    if len(weatheryears) > 1:
        ax.set_xlim(str(weatheryears[0]), str(weatheryears[-1]+1))
    if 1 < len(weatheryears) <= 7:
        ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(4))
    elif len(weatheryears) > 7:
        ax.xaxis.set_minor_locator(mpl.dates.YearLocator())
    reeds.plots.despine(ax)

    return f, ax, dfday


def plot_modelyears_weatheryears(case, startyear=2020, year_buffer=1):
    """
    Plot annual demand by model year for each weather year.
    """
    ## Parse inputs
    sw = reeds.io.get_switches(case)
    modelyears = [y for y in reeds.io.get_years(case) if y >= startyear]
    year_spacing = int(pd.Series(modelyears).diff().min())
    weatheryears = sw.resource_adequacy_years_list
    colors = {'demand':'k', 'upv':'C1', 'wind-ons':'C0'}
    ylabels = {'demand':'Electricity demand [GW]', 'upv':'PV', 'wind-ons':'Wind'}

    ## Data
    dfdemand_profile = reeds.io.read_file(
        os.path.join(case, 'inputs_case', 'load.h5'),
        parse_timestamps=True,
    ## Sum over country and convert to GW
    ).sum(axis=1) / 1e3

    recf = (
        reeds.io.get_available_capacity_weighted_cf(case, level='country')
        .xs('USA', 1, 'r')
        [['upv', 'wind-ons']]
    ) * 100

    ## Get the min, mean, and max by model year and weather year
    dfdemand = pd.concat({
        agg: (
            dfdemand_profile
            .groupby(['year', dfdemand_profile.index.get_level_values('datetime').year])
            .agg(agg)
            .rename_axis(['modelyear', 'weatheryear'])
        )
        for agg in ['min', 'mean', 'max']
    }, axis=1).loc[modelyears]
    ## For VRE, get the min/mean/max of the daily average CF
    dfvre = pd.concat({
        agg: (
            recf
            .groupby([recf.index.year, recf.index.month, recf.index.day]).mean()
            .rename_axis(['y','m','d'])
            .groupby('y').agg(agg)
            .rename_axis('weatheryear')
        )
        for agg in ['min', 'mean', 'max']
    }, axis=1, names=('agg','i'))

    ## Get weather year spacing for plots
    allweather = np.arange(min(weatheryears), max(weatheryears)+1, 1)
    weatherspan = max(weatheryears) - min(weatheryears)
    weathermid = (max(weatheryears) + min(weatheryears)) / 2
    xspan = (year_spacing - year_buffer) / weatherspan

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        1, 2, figsize=(7, 3.75),
        gridspec_kw={'width_ratios': [len(modelyears)+1, 2], 'wspace':0.3},
    )
    ## Demand
    _ax = ax[0]
    for modelyear in modelyears:
        df = dfdemand.loc[modelyear].copy()
        ## Use the next line if you want to include the gap (harder to interpret)
        # df = df.reindex(allweather)
        ## Plot the weather years centered around the model year
        x = {y: modelyear + (y - weathermid) * xspan for y in allweather}
        df.index = df.index.map(x)
        ## Plot it
        _ax.plot(
            df.index, df['mean'], lw=0, color=colors['demand'],
            marker='o', markersize=3, markeredgewidth=0,
        )
        _ax.fill_between(
            df.index, df['max'], df['min'],
            lw=0, alpha=0.25, color=colors['demand'],
        )
        for agg in ['min', 'max']:
            _ax.plot(
                df.index, df[agg], lw=0, color=colors['demand'],
                marker='o', markersize=1.5, markeredgewidth=0,
            )
        ## Label the min/mean/max and weather years
        if modelyear == modelyears[-1]:
            for i in [0, -1]:
                _ax.annotate(
                    weatheryears[i],
                    (df.index[i], df['min'].mean()),
                    xytext=(0, -20), textcoords='offset points',
                    ha='center', va='top', annotation_clip=False,
                    arrowprops={'arrowstyle':'-|>', 'color':colors['demand'], 'shrinkB':-3},
                )
            _ax.annotate(
                'weather year',
                (modelyear, df['min'].mean()),
                xytext=(0, -30), textcoords='offset points',
                ha='center', va='top', annotation_clip=False,
            )
        if modelyear == modelyears[-1]:
            for agg in df:
                _ax.annotate(
                    ('Annual\n'+agg if agg=='max' else agg),
                    (df.index.max(), df[agg].mean()),
                    xytext=(4, 0), textcoords='offset points',
                    ha='left', va='center', annotation_clip=False,
                )

    _ax.set_xlabel('Model year')
    _ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(year_spacing))
    _ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    _ax.set_ylim(0)
    _ax.set_title(ylabels['demand'], x=0, ha='left', weight='bold', fontsize='x-large')
    ## PV and wind
    _ax = ax[1]
    for col, tech in enumerate(['upv', 'wind-ons']):
        x = {y: col*year_spacing + (y - weathermid) * xspan for y in allweather}
        df = dfvre.xs(tech, 1, 'i')
        df.index = df.index.map(x)
        _ax.plot(
            df.index, df['mean'], lw=0, color=colors[tech],
            marker='o', markersize=3, markeredgewidth=0,
        )
        _ax.fill_between(
            df.index, df['max'], df['min'],
            lw=0, alpha=0.25, color=colors[tech],
        )
        for agg in ['min', 'max']:
            _ax.plot(
                df.index, df[agg], lw=0, color=colors[tech],
                marker='o', markersize=1.5, markeredgewidth=0,
            )
        _ax.annotate(
            ylabels[tech],
            (col*year_spacing, 0),
            xytext=(0, 1), textcoords='offset points',
            ha='center', va='bottom', color=colors[tech],
            weight='bold', fontsize='x-large',
        )
    _ax.set_title(
        'Daily CF [%]', weight='bold', fontsize='x-large',
    )
    _ax.set_xticks([])
    _ax.set_ylim(0)
    _ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))

    reeds.plots.despine(ax)

    return f, ax, {'demand': dfdemand, 'vre': dfvre}


def plot_units_existing(
    case=None,
    year=None,
    markers=None,
    scale=0.2,
    alpha=0.8,
    f=None,
    ax=None,
    figsize=(12,9),
    drawstates=0.75,
    drawzones=0.,
    onlytechs=None,
    gw_label=True,
    scalemw=[200, 500, 1000],
):
    """
    Scatter map of existing units, with marker size proportional to unit capacity.
    If case == None, use EIA-NEMS database from inputs/ folder.
    """
    ### Data cleaning (20250508: Offshore PV units)
    bad_locations = ['Hendry Isles', 'Georges Lake', 'Laurel Oaks Solar', 'Norton Creek']
    ### Get data
    if case is None:
        fpath = os.path.join(
            reeds.io.reeds_path, 'inputs', 'capacity_exogenous',
            'ReEDS_generator_database_final_EIA-NEMS.csv',
        )
    else:
        fpath = os.path.join(case, 'inputs_case', 'unitdata.csv')

    dfunits = pd.read_csv(fpath)
    dfunits = reeds.plots.df2gdf(
        dfunits.assign(T_LONG=-dfunits.T_LONG.abs()), lat='T_LAT', lon='T_LONG',
    )
    dfunits.tech = reeds.reedsplots.simplify_techs(dfunits.tech)
    rename = {
        **{'dupv':'upv'},
        **{f'battery_{i}':'battery' for i in range(101)},
    }
    dfunits.tech = dfunits.tech.map(lambda x: rename.get(x,x))
    ## Downselect to specified year
    if year is None:
        if case is None:
            year = int(
                pd.read_csv(
                    os.path.join(reeds.io.reeds_path, 'cases.csv'),
                    index_col=0,
                )['Default Value'].GSw_StartMarkets
            )
        else:
            year = int(reeds.io.get_switches(case).GSw_StartMarkets)
    dfunits = dfunits.loc[
        (dfunits.StartYear <= year)
        & (dfunits.RetireYear > year)
        & ~dfunits.T_PNM.isin(bad_locations)
    ].copy()
    ## Sort techs by installed capacity
    techs = dfunits.groupby('tech').summer_power_capacity_MW.sum().sort_values(ascending=False).index
    if onlytechs:
        if isinstance(onlytechs, str):
            techs = [onlytechs]
        elif isinstance(onlytechs, list):
            techs = [i for i in techs if i in onlytechs]

    ### Parse inputs
    if markers is None:
        techmarkers = reeds.reedsplots.techmarkers
    elif isinstance(markers, str):
        techmarkers = dict(zip(techs, markers(len(techs))))
    elif isinstance(markers, dict):
        techmarkers = markers
    else:
        raise ValueError(f'Invalid markers ({type(markers)}): {markers}')

    colors = pd.read_csv(
        os.path.join(
            reeds.io.reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order',
    ).squeeze(1)
    colors.index = colors.index.str.lower()

    dfmap = reeds.io.get_dfmap(case)

    ## Create scale
    dfscale = pd.DataFrame({'cap': scalemw}).sort_values('cap')
    dfscale['x'] = -0.8e6
    dfscale['y'] = -1.4e6 - np.arange(0, 0.1e6*len(dfscale), 0.1e6)
    dfscale['geometry'] = dfscale.apply(lambda row: shapely.geometry.Point(row.x, row.y), axis=1)
    dfscale = gpd.GeoDataFrame(dfscale)

    ### Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=figsize)
    ## Region outlines
    if drawzones:
        dfmap['r'].plot(ax=ax, facecolor='none', edgecolor='k', lw=drawzones, zorder=1e6)
    if drawstates:
        dfmap['st'].plot(ax=ax, facecolor='none', edgecolor='k', lw=drawstates, zorder=1e7)
    ## Units
    for tech in techs:
        df = dfunits.loc[dfunits.tech==tech]
        label = f'{tech} ({df.summer_power_capacity_MW.sum()/1e3:.0f})' if gw_label else tech
        df.plot(
            ax=ax, color=colors.get(tech,'k'), marker=techmarkers.get(tech,'o'),
            markersize=df.summer_power_capacity_MW*scale, lw=0, label=label, alpha=alpha,
        )
    ## Legend
    leg = ax.legend(
        loc='lower left', bbox_to_anchor=(0.04,0.04), ncol=2, frameon=False,
        handletextpad=0.3, handlelength=0.7, columnspacing=0.6, labelspacing=0.3,
        title=('Tech (GW)' if gw_label else 'Tech'),
        alignment='left', title_fontproperties={'weight':'bold', 'size':12},
    )
    for handle in leg.legend_handles:
        handle.set_sizes([50])
        handle.set_alpha(1)
    ## Scale
    if len(scalemw):
        dfscale.plot(ax=ax, color='k', marker='o', markersize=dfscale.cap*scale, lw=0)
        for i, row in dfscale.iterrows():
            ax.annotate(
                f'{row.cap/1e3:.1f}'+(' GW' if i == len(dfscale) - 1 else ''),
                (row.x+1e5, row.y), va='center', annotation_clip=False,
            )
    ## Formatting
    ax.axis('off')
    return f, ax, dfunits


def plot_existing_unitsize(
    case=None,
    level='transreg',
    techs=['gas-ct', 'gas-cc', 'nuclear'],
    year=2025,
    scale=1.5,
    binwidth=None,
    numbins=41,
):
    """
    """
    ### Parse inputs
    sw = reeds.io.get_switches(case)
    hierarchy = reeds.io.get_hierarchy(case)
    county2zone = reeds.io.get_county2zone(case)
    unitsize = pd.read_csv(
        os.path.join(
            reeds.io.reeds_path, 'inputs', 'plant_characteristics',
            f'unitsize_{sw.pras_unitsize_source}.csv'
        ),
        index_col='tech'
    ).MW.map(lambda x: [x])
    capcol = 'summer_power_capacity_MW'
    if case is None:
        dfunits = pd.read_csv(
            os.path.join(
                reeds.io.reeds_path, 'inputs', 'capacity_exogenous',
                'ReEDS_generator_database_final_EIA-NEMS.csv',
            )
        )
        dfunits['reeds_ba'] = dfunits.FIPS.str.strip('p').map(county2zone)
    else:
        dfunits = pd.read_csv(os.path.join(case, 'inputs_case', 'unitdata.csv'))

    ### Subset to year, techs, and regions
    dfplot = dfunits.loc[
        (dfunits.StartYear <= year)
        & (dfunits.RetireYear > year)
        & (dfunits.tech.isin(techs))
    ].copy()
    dfplot['region'] = dfplot.reeds_ba.map(hierarchy[level])

    ### Set up plot
    regions = hierarchy[level].unique()
    nrows, ncols, coords = reeds.reedsplots.layout_subplots(
        row_list=regions, col_list=techs,
    )
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(ncols*scale*1.5, nrows*scale*0.5), sharex='col',
        gridspec_kw={'wspace':0.4, 'hspace':0.3}
    )
    for tech in techs:
        xmax = dfplot.loc[dfplot.tech==tech][capcol].max()
        for region in regions:
            _ax = ax[coords[region, tech]]
            df = dfplot.loc[(dfplot.tech==tech)&(dfplot.region==region), capcol]
            if not len(df):
                continue
            if binwidth is not None:
                bins = np.arange(0, xmax+0.00001, binwidth)
            elif numbins is not None:
                bins = np.linspace(0, xmax+0.00001, numbins)
            else:
                raise ValueError('Only one of binwidth and numbins should be provided')
            _ax.hist(df, bins=bins, color='C0')
            ## ATB
            for x in unitsize[tech]:
                _ax.axvline(x, c='C3', ls='--', lw=0.75)
            ymax = max(_ax.get_ylim()[1], 1)
            _ax.set_ylim(0, ymax)
            # ymax = max(_ax.get_ylim()[1], 10)
            # _ax.set_yscale('log')
            # _ax.set_ylim(0.5, ymax)
            if len(coords[region, tech]) == 2:
                if coords[region, tech][0] == 0:
                    x = max(unitsize[tech])
                    _ax.annotate(
                        f"ATB: {', '.join(sorted(set([str(i) for i in unitsize[tech]])))}",
                        xy=(x, ymax),
                        xytext=(2,-2), textcoords='offset points',
                        ha='left', va='top', color='C3',
                    )
            ## Median
            mean = df.agg('mean')
            _ax.axvline(mean, c='k', ls=':', lw=0.75)
            if len(coords[region, tech]) == 2:
                _ax.annotate(
                    f'{mean:.0f}',
                    xy=(mean, 0),
                    # xy=(mean, 0.5),
                    xytext=(2,2), textcoords='offset points',
                    ha='left', va='bottom', color='k',
                    path_effects=[pe.withStroke(linewidth=2.0, foreground='w', alpha=0.95)]
                )
    ## Formatting
    if (nrows == 1) and (ncols == 1):
        ax.set_title(tech, fontsize='x-large', weight='bold')
        ax.set_xlim(0)
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(100))
        ax.set_ylabel(region, rotation=0, ha='right', va='center')
    elif (nrows > 1) and (ncols > 1):
        for col, tech in enumerate(techs):
            ax[0,col].set_title(tech, fontsize='x-large', weight='bold')
            ax[0,col].set_xlim(0)
            ax[0,col].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(100))
        for row, region in enumerate(regions):
            ax[row,0].set_ylabel(region, rotation=0, ha='right', va='center')
        ax[-1,0].set_xlabel('Capacity [MW]', x=0, ha='left')
    else:
        ...
    reeds.plots.despine(ax)
    return f, ax, dfplot


def plot_regional_cost_difference(
    case=None,
    nicelabels={
        'CONSUME': 'Electrolyzer, DAC, steam methane reforming',
        'OGS': 'Oil-gas-steam',
        'LFILL': 'Landfill gas',
        'CSP': 'CSP',
        'PVB': '(including in PV/battery hybrid)',
    },
    cmap=plt.cm.RdBu_r,
    scale=4,
    vlim=30,
):
    dfmap = reeds.io.get_dfmap(case)
    ### Get data
    if case is None:
        ## County resolution
        fpath = os.path.join(
            reeds.io.reeds_path, 'inputs', 'financials', 'reg_cap_cost_diff_default.csv',
        )
        dfin = pd.read_csv(fpath, index_col='r') * 100
        dfcounty = gpd.read_file(
            os.path.join(reeds.io.reeds_path, 'inputs', 'shapefiles', 'US_county_2022')
        ).set_index('rb')
        dfcounty.geometry = dfcounty.intersection(dfmap['country'].geometry.squeeze()).simplify(1000)
        dfplot = dfcounty.merge(dfin, left_index=True, right_index=True)
    else:
        ## Model zone resolution
        fpath = os.path.join(case, 'inputs_case', 'regional_cap_cost_diff.csv')
        dfin = pd.read_csv(fpath, index_col='r') * 100
        dfplot = dfmap['r'].merge(dfin, left_index=True, right_index=True)
    ### Set up plot
    if vlim in [None, 0]:
        vlim = max(abs(dfin.min().min()), dfin.max().max())
    nrows, ncols, coords = reeds.plots.get_coordinates(dfin.columns, ncols=3)
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(ncols*scale, nrows*scale*0.8),
        sharex=True, sharey=True, gridspec_kw={'wspace':0},
    )
    for column in dfin:
        _ax = ax[coords[column]]
        ## Data
        dfplot.plot(
            ax=_ax, column=column, vmin=-vlim, vmax=vlim, cmap=cmap,
        )
        ## States
        dfmap['st'].plot(ax=_ax, facecolor='none', edgecolor='k', lw=0.3)
        ## Formatting
        _ax.axis('off')
        _ax.set_title(
            '\n'.join([nicelabels.get(i, i.title()).replace('_',' ') for i in column.split('|')]),
            y=0.92,
        )
    ## Colorbar
    reeds.plots.addcolorbarhist(
        f=f, ax0=ax[0,1], data=dfplot[column].values,
        histcolor='w', histratio=0.01, vmin=-vlim, vmax=vlim,
        orientation='horizontal', cbarwidth=0.05, cbarheight=0.9, cbarhoffset=10,
        cbarbottom=-0.075, labelpad=2,
        title='Cost difference [%]',
        cmap=cmap,
    )
    return f, ax, dfplot


def plot_fuel_prices(tstart=2010, tend=2050, figsize=(9, 3.75), datayear=2025, alpha=0.4):
    dollaryear = datayear - 1
    bokehcolors = get_bokeh_colors()
    colors = {
        'Gas': bokehcolors['gas-cc'],
        'Coal': bokehcolors['coal'],
        'Uranium': bokehcolors['nuclear'],
    }
    ## Get data
    dictin = {}
    for label in fuel_price_scenarios:
        for scen in fuel_price_scenarios[label]:
            dictin[label,scen] = pd.read_csv(
                os.path.join(
                    reeds.io.reeds_path, 'inputs', 'fuelprices',
                    fuel_price_scenarios[label][scen].format(datayear=datayear),
                ),
                index_col='year',
            ).mean(axis=1)

    ## Plot it
    plt.close()
    f,ax = plt.subplots(1, 3, figsize=figsize, sharex=True, sharey=True)
    for col, label in enumerate(fuel_price_scenarios.keys()):
        _ax = ax[col]
        scens = fuel_price_scenarios[label]
        if 'low' in scens and 'high' in scens:
            _ax.fill_between(
                dictin[label,'low'].index,
                dictin[label,'high'],
                dictin[label,'low'],
                lw=0, alpha=alpha, color=colors[label],
            )
        _ax.plot(
            dictin[label,'mid'].index,
            dictin[label,'mid'],
            color=colors[label],
        )
        ## Formatting
        _ax.annotate(
            label, (0.05, 0.98), xycoords='axes fraction', ha='left', va='top',
            weight='bold', color=colors[label], fontsize=14,
        )
        _ax.axvspan(tstart, datayear-1, color='0.95', zorder=-1)
        # _ax.axvline(datayear-1, c='C7', ls='--', lw=0.75)
    ## Formatting
    ax[0].set_ylabel(f'Fuel price [{dollaryear}$/MMBtu]')
    ax[0].set_ylim(0)
    ax[0].set_xlim(tstart, tend)
    ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
    ax[0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5))
    ax[0].yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    reeds.plots.despine(ax)
    return f, ax, dictin


def map_gas_price(
    plotyear=2035, datayear=2025, scale=3, cmap=cmocean.cm.rain,
    labelsize=8,
):
    dfmap = reeds.io.get_dfmap()
    ## Get data
    dictin = {}
    for scen in fuel_price_scenarios['Gas']:
        dictin[scen] = pd.read_csv(
            os.path.join(
                reeds.io.reeds_path, 'inputs', 'fuelprices',
                fuel_price_scenarios['Gas'][scen].format(datayear=datayear),
            ),
            index_col='year',
        ).loc[plotyear]
    vmin = min([df.min() for df in dictin.values()])
    vmax = max([df.max() for df in dictin.values()])

    ## Plot it
    plt.close()
    f,ax = plt.subplots(
        3, 1, figsize=(scale, scale*3*0.7), sharex=True, sharey=True,
        gridspec_kw={'hspace':-0.05},
    )
    for row, scen in enumerate(['high', 'mid', 'low']):
        _ax = ax[row]
        df = dfmap['cendiv'].copy()
        df['price'] = dictin[scen]
        dfmap['country'].plot(ax=_ax, facecolor='none', edgecolor='k', lw=0.8, zorder=1e7)
        df.plot(ax=_ax, facecolor='none', edgecolor='k', lw=0.2, zorder=1e6)
        df.plot(ax=_ax, column='price', vmin=vmin, vmax=vmax, cmap=cmap)
        ## Annotations
        for r, ds in df.iterrows():
            _ax.annotate(
                f'{ds.price:.1f}',
                (ds.geometry.centroid.x, ds.geometry.centroid.y),
                ha='center', va='center',
                fontsize=labelsize,
                # color=('k' if ds.price < vmid else 'w'),
                color='k',
                path_effects=[pe.withStroke(linewidth=1.8, foreground='w', alpha=0.8)],
                zorder=1e9,
            )
        _ax.annotate(
            f'{plotyear} {scen.title()}',
            (0.07, 0.1), xycoords='axes fraction',
            fontsize=labelsize*1.25,
        )
        ## Formatting
        _ax.axis('off')

    return f, ax, dictin


def map_supplycurves(
    case=None,
    tech=None,
    access='reference',
    cmap=cmocean.cm.rain,
    crs='EPSG:5070',
    include_techneutral_adder=True,
    dollaryear=2023,
    figsize=(12,9),
    draw_lakes=True,
    draw_stats=True,
    dpi=None,
    markers=False,
):
    """
    Returns an iterator over supply-curve columns. Use as follows:
        ```python
        plot_generator = map_supplycurves()
        while True:
            try:
                f, ax, df, setting = next(plot_generator)
                plt.savefig(figpath)
            except StopIteration:
                break
        ```

    Inputs:
    - case: If None, read defaults and use access; otherwise read from ReEDS case
    - tech: If None, read tech-neutral interconnection parameters
    - include_technuetral_adder: Adds inflation-adjusted GSw_TransIntraCost
    - draw_lakes: Include Great Lakes
    - draw_stats: Include supply-curve filepath and descriptive statistics
    - markers: Scatter plot if True (faster but looks worse, especially for sub-US)
    """
    ### Get inputs
    sw = reeds.io.get_switches(case)
    dfmap = reeds.io.get_dfmap(case=case)
    for key in dfmap:
        if dfmap[key].crs != crs:
            dfmap[key] = dfmap[key].to_crs(crs)
    ## If no tech, just plot transmission
    if tech in [None, 'land']:
        scpath = os.path.join(
            reeds.io.reeds_path, 'inputs', 'supply_curve',
            'interconnection_land.h5'
        )
        dfsc = reeds.io.read_h5_groups(scpath)
    elif tech == 'offshore':
        scpath = os.path.join(
            reeds.io.reeds_path, 'inputs', 'supply_curve',
            'interconnection_offshore.h5'
        )
        dfsc = reeds.io.read_h5_groups(scpath)
    else:
        if case is None:
            scpath = os.path.join(
                reeds.io.reeds_path, 'inputs', 'supply_curve',
                f'supplycurve_{tech}-{access}.csv'
            )
        else:
            scpath = os.path.join(case, 'inputs_case', f'supplycurve_{tech}.csv')
        dfsc = reeds.io.assemble_supplycurve(scpath, case=case, drop_extra=False)
        if 'latitude' not in dfsc:
            sitemap = reeds.io.get_sitemap(geo=True).to_crs(crs)
            dfsc = gpd.GeoDataFrame(
                dfsc.merge(sitemap, left_index=True, right_index=True, how='left'),
                crs=crs,
            )
        # dfsc = reeds.plots.df2gdf(
        #     reeds.io.assemble_supplycurve(scpath, case=case, drop_extra=False),
        #     crs=crs,
        # )
    if 'geometry' not in dfsc:
        dfsc = reeds.plots.df2gdf(dfsc, crs=crs)
    ## Extra plot settings
    if draw_lakes:
        greatlakes = gpd.read_file(
            os.path.join(reeds.io.reeds_path, 'inputs', 'shapefiles', 'greatlakes.gpkg'),
        ).to_crs(crs)
    if include_techneutral_adder:
        inflatable = reeds.io.get_inflatable()
        costadder = float(sw.GSw_TransIntraCost) * inflatable[2004, dollaryear]
    else:
        costadder = 0
    ## Convert from point to polygons if desired (raster is 11.52 km but include a little extra)
    if not markers:
        dfsc.geometry = dfsc.buffer(11530/2, cap_style='square')

    ###### Format inputs
    ## Use 4.5 for limited access wind-ofs
    ms = {
        ('wind-ofs', 'open'): 4.1,
        ('wind-ofs', 'reference'): 4.1,
        ('wind-ofs', 'limited'): 4.5,
    }.get((tech, access), 2.65)

    defaults = {'vmin':0., 'vmax':2000., 'scale':1, 'background':True, 'nbins':101, 'costadder':0}
    settings = {
        'capacity': {
            'label':'Capacity [MW]',
            'vmax':{
                'upv':5700., 'wind-ons':342., 'wind-ofs':530.,
                'geohydro':700., 'egs':4000., 'csp':4900.,
            }.get(tech, 1000.),
            'background':False,
            ## For onshore wind, align nbins with number of 6 MW turbines
            'nbins': {'wind-ons':342 // 6 + 1}.get(tech, 101),
        },
        'capital_adder_per_mw': {'label':'Site cost adder [$/kW]', 'scale':1e-3},
        'cf': {'label':'Capacity factor (AC) [%]', 'scale':100, 'vmax':55},
        'class': {'label':'Resource class [.]', 'vmax':10.},
        'cost_poi_usd_per_mw': {'label':'Substation cost [$/kW]', 'scale':1e-3},
        'cost_reinforcement_usd_per_mw': {'label':'Reinforcement cost [$/kW]', 'scale':1e-3},
        'cost_spur_usd_per_mw': {'label':'Spur cost [$/kW]', 'scale':1e-3},
        'cost_total_trans_usd_per_mw': {
            'label':'Interconnection cost [$/kW]',
            'scale':1e-3,
            'costadder':costadder,
        },
        'supply_curve_cost_per_mw': {
            'label':'Supply-curve cost [$/kW]',
            'scale':1e-3,
            'costadder':costadder,
        },
        'dist_reinforcement_km': {'label':'Reinforcement distance [km]', 'vmax':900.},
        'dist_spur_km': {'label':'Spur distance [km]', 'vmax':900.},
        ## Specific to offshore
        'cost_export_usd_per_mw': {'label':'Export cable cost [$/kW]', 'scale':1e-3},
        'dist-export_km': {'label':'Export cable distance [km]'},
    }

    for col in settings:
        setting = {**defaults, **settings[col]}
        if col not in dfsc:
            print(f"{col} is not in the supply curve table")
            continue
        ## Scale if necessary
        dfplot = dfsc.copy()
        dfplot[col] = dfplot[col] * setting['scale'] + setting['costadder']
        ### Plot it
        plt.close()
        f,ax = plt.subplots(figsize=figsize, dpi=dpi)
        ## Background
        if setting['background']:
            dfmap['r'].plot(ax=ax, facecolor='C7', edgecolor='none', lw=0.3, zorder=-1e6)
        dfmap['r'].plot(ax=ax, facecolor='none', edgecolor='k', lw=0.3, zorder=1e6)
        dfmap['st'].plot(ax=ax, facecolor='none', edgecolor='k', lw=0.5, zorder=2e6)
        if draw_lakes:
            greatlakes.plot(ax=ax, edgecolor='#2CA8E7', facecolor='#D3EFFA', lw=0.2, zorder=-1)
        ## Map of data
        dfplot.plot(
            ax=ax,
            column=col,
            cmap=cmap,
            marker=('s' if markers else None),
            markersize=(ms if markers else None),
            lw=0,
            legend=False,
            vmin=setting['vmin'],
            vmax=setting['vmax'],
        )
        ## Annotation
        if draw_stats:
            ax.set_title(scpath, fontsize='small', y=0.97)
            note = str(dfplot[col].describe().round(1))
            note = note[:note.index('\nName')]
            ax.annotate(
                note, (0.06, 0.06), xycoords='axes fraction',
                ha='left', va='bottom', fontsize=10, fontfamily='monospace',
            )
        ## Colorbar-histogram
        plots.addcolorbarhist(
            f=f, ax0=ax, data=dfplot[col].values,
            title=setting['label'], cmap=cmap,
            vmin=setting['vmin'], vmax=setting['vmax'],
            orientation='horizontal', labelpad=2.1, cbarbottom=-0.06,
            cbarheight=0.7, log=False,
            nbins=setting['nbins'],
            histratio=2,
            ticklabel_fontsize=20, title_fontsize=24,
            extend='neither',
        )
        ## Formatting
        ax.axis('off')
        yield f, ax, dfplot, col


#%%### Procedure
if __name__ == '__main__':
    #%% Argument inputs
    parser = argparse.ArgumentParser(
        description='Check inputs.gdx parameters against objective_function_params.yaml',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('case', help='ReEDS-2.0/runs/{case} directory')
    parser.add_argument(
        '--write', '-w', choices=['png', 'ppt', 'pptx'], default='png',
        help='Output format (png or pptx)')
    args = parser.parse_args()
    case = args.case
    write = args.write

    # #%% Inputs for testing
    # case = os.path.join(reeds.io.reeds_path, 'runs', 'v20251209_scM0_USA_defaults')
    # interactive = True
    # write = 'png'

    #%% Create output container
    if write.strip('.') == 'png':
        savepath = os.path.join(case, 'outputs', 'figures', 'inputs')
        os.makedirs(savepath, exist_ok=True)

        def saveit(savename):
            outpath = os.path.join(savepath, savename.lower().replace(' ', '-') + '.png')
            plt.savefig(outpath)
            print(os.path.basename(outpath))
            if interactive:
                plt.show()

    elif write.strip('.') in ['ppt', 'pptx']:
        savepath = os.path.join(case, 'outputs', 'figures', 'inputs.pptx')
        prs = reeds.report_utils.init_pptx()
        def saveit(savename, **kwargs):
            reeds.report_utils.add_to_pptx(savename, prs=prs, **kwargs)
            if interactive:
                plt.show()


    #%% Plots
    sw = reeds.io.get_switches(case)

    ### Scheduled outage rates
    try:
        f, ax, df = plot_outage_scheduled(case)
        saveit('outage_scheduled')
    except Exception:
        print(traceback.format_exc())

    ### Demand, PV, and wind profiles
    colors = {'demand':'k', 'pv':'C1', 'wind':'C0'}
    for datum in colors:
        ## Daily max/mean/min for all RA weather years for a single datum
        try:
            f, ax, df = plot_profile(case, datum=datum, color=colors[datum])
            saveit(f"{datum}{'_lastyear' if datum in ['demand','load'] else ''}_ra")
        except Exception:
            print(traceback.format_exc())

        ## Daily max/mean/min plus hourly squiggle for the representative year(s)
        try:
            f, ax, df = plot_profile(
                case,
                datum=datum,
                color=colors[datum],
                hourly=True,
                weatheryears=[int(y) for y in sw.GSw_HourlyWeatherYears.split('_')],
                figsize=(13.33, 4),
            )
            saveit(f"{datum}{'_lastyear' if datum in ['demand','load'] else ''}_rep")
        except Exception:
            print(traceback.format_exc())

    ## Daily max/mean/min for all RA weather years for demand, PV, and wind
    try:
        plt.close()
        f,ax = plt.subplots(len(colors), 1, figsize=(5, 3.75), sharex=True)
        for row, (datum, color) in enumerate(colors.items()):
            plot_profile(case, datum=datum, color=color, ax=ax[row], yscale_zero=False)
        ## Formatting
        ax[0].set_ylabel('Demand\n[GW]', color=colors['demand'])
        ax[1].set_ylabel('PV CF\n[%]', color=colors['pv'])
        ax[2].set_ylabel('Wind CF\n[%]', color=colors['wind'])
        cfmax = max(ax[1].get_ylim()[1], ax[2].get_ylim()[1])
        for row in [1, 2]:
            ax[row].set_ylim(0, cfmax)
        saveit(f"{','.join(colors.keys())}_ra")
    except Exception:
        print(traceback.format_exc())

    ## Weather years and model years for demand
    try:
        f, ax, df = plot_modelyears_weatheryears(case)
        saveit('demand,pv,wind_modelyears_weatheryears')
    except Exception:
        print(traceback.format_exc())

    ### Existing units
    ## Scatter map
    try:
        f, ax, df = plot_units_existing(case=case)
        saveit('Existing capacity')
    except Exception:
        print(traceback.format_exc())

    ## Size distribution
    try:
        f, ax, df = plot_existing_unitsize(case=case)
        saveit('Unit size distribution')
    except Exception:
        print(traceback.format_exc())

    ### Regional cost differences
    try:
        f, ax, df = plot_regional_cost_difference(case=case)
        saveit('Regional cost differences')
    except Exception:
        print(traceback.format_exc())

    ### Fuel prices
    try:
        f, ax, df = plot_fuel_prices()
        saveit('Fuel prices')
    except Exception:
        print(traceback.format_exc())

    try:
        f, ax, df = map_gas_price()
        saveit('Gas prices')
    except Exception:
        print(traceback.format_exc())

    ### Supply curves
    extras = (True if 'usa' in sw.GSw_Region.lower() else False)
    try:
        for tech in ['upv', 'wind-ons', 'wind-ofs', 'egs']:
            plot_generator = map_supplycurves(
                case=case,
                tech=tech,
                draw_lakes=extras,
                draw_stats=extras,
            )
            while True:
                try:
                    f, ax, df, col = next(plot_generator)
                    saveit(f"Supplycurve {tech} {col}")
                except StopIteration:
                    break
    except Exception:
        print(traceback.format_exc())


    #%% Save the powerpoint file if necessary
    if write.strip('.') in ['ppt', 'pptx']:
        print(f'\ninput_plots.py results saved to:\n{savepath}')
        prs.save(savepath)
