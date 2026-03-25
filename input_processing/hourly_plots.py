#%% IMPORTS
import os
import sys
import math
import argparse
import logging
## Turn off logging for imported packages
for i in ['matplotlib']:
    logging.getLogger(i).setLevel(logging.CRITICAL)
import json
import pandas as pd
import numpy as np
from LDC_prep import read_file
import hourly_repperiods

################
#%% SETTINGS ###
interactive = False

#################
#%% FUNCTIONS ###

def plot_unclustered_periods(profiles, sw, reeds_path, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()
    ### Overlapping days
    for label, dfin in [
        # ('unscaled',profiles),
        ('scaled',profiles),
    ]:
        properties = dfin.columns.get_level_values('property').unique()
        nhours = len(dfin.columns.get_level_values('region').unique())*(24 if sw['GSw_HourlyType']=='day' else 120)
        plt.close()
        f,ax = plt.subplots(1,len(properties),sharex=True,figsize=(nhours/12, 3.75))
        for col, prop in enumerate(properties):
            dfin[prop].T.reset_index(drop=True).plot(
                ax=ax[col], lw=0.2, legend=False)
            dfin[prop].mean(axis=0).reset_index(drop=True).plot(
                ax=ax[col], lw=1.5, color='k', legend=False)
            ax[col].set_title(prop)
            for x in np.arange(0,nhours+1,(24 if sw['GSw_HourlyType']=='day' else 120)):
                ax[col].axvline(x,c='k',ls=':',lw=0.3)
            ax[col].tick_params(labelsize=9)
            ax[col].set_ylim(0)
        ### Formatting
        title = ' | '.join(
            profiles.columns.get_level_values('region').drop_duplicates().tolist())
        ax[0].annotate(title,(0,1.12), xycoords='axes fraction', fontsize='large',)
        ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(12))
        ax[0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(6))
        ax[0].set_xlim(0, nhours)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-day_hourly-{}.png'.format(label)))
        if interactive: plt.show()
        plt.close()

    ### Sequential days, unscaled and scaled
    for label, dfin in [('unscaled',profiles)]:
        properties = dfin.columns.get_level_values('property').unique()
        regions = dfin.columns.get_level_values('region').unique()
        rows = [(p,r) for p in properties for r in regions]
        ### Hourly
        plt.close()
        f,ax = plt.subplots(len(rows),1,figsize=(12,12),sharex=True,sharey=False)
        for row, (p,r) in enumerate(rows):
            df = dfin[p][r].stack('h_of_period')
            ax[row].fill_between(range(len(df)), df.values, lw=0)
            ax[row].set_title('{} {}'.format(p,r),x=0.01,ha='left',va='top',pad=0)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-year_hourly-{}.png'.format(label)))
        if interactive: plt.show()
        plt.close()
        ### Daily
        plt.close()
        f,ax = plt.subplots(len(rows),1,figsize=(12,12),sharex=True,sharey=False)
        for row, (p,r) in enumerate(rows):
            df = dfin[p][r].mean(axis=1)
            ax[row].fill_between(range(len(df)), df.values, lw=0)
            ax[row].set_title('{} {}'.format(p,r),x=0.01,ha='left',va='top',pad=0)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-year_daily-{}.png'.format(label)))
        if interactive: plt.show()
        plt.close()


def plot_feature_scatter(profiles_fitperiods, reeds_path, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()
    ### Settings
    colors = plots.rainbowmapper(profiles_fitperiods.columns.get_level_values('region').unique())
    props = ['load','upv','wind-ons']
    ### Plot it
    plt.close()
    f,ax = plt.subplots(3,3,figsize=(7,7),sharex='col',sharey='row')
    for row, yax in enumerate(props):
        for col, xax in enumerate(props):
            for region, c in colors.items():
                ax[row,col].plot(
                    profiles_fitperiods[xax][region].values,
                    profiles_fitperiods[yax][region].values,
                    c=c, lw=0, markeredgewidth=0, ms=5, alpha=0.5, marker='o',
                    label=(region if (row,col)==(1,2) else '_nolabel'),
                )
    ### Formatting
    ax[1,-1].legend(
        loc='center left', bbox_to_anchor=(1,0.5), frameon=False, fontsize='large',
        handletextpad=0.3,handlelength=0.7,
    )
    for i, prop in enumerate(props):
        ax[-1,i].set_xlabel(prop)
        ax[i,0].set_ylabel(prop)

    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'feature_scatter.png'))
    if interactive: plt.show()
    plt.close()


def plot_clustered_days(
        profiles_fitperiods_hourly, profiles, rep_periods,
        forceperiods, sw, reeds_path, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()

    ### Input processing
    numclusters = int(sw['GSw_HourlyNumClusters'])
    centroids = profiles.loc[rep_periods]
    properties = profiles_fitperiods_hourly.columns.get_level_values('property').unique()
    nhours = (len(profiles_fitperiods_hourly.columns.get_level_values('region').unique())
              * (24 if sw['GSw_HourlyType']=='day' else 120))
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        len(properties), numclusters+len(forceperiods),
        sharey='row', sharex=True, figsize=(nhours/12*numclusters/3,6))
    for row, prop in enumerate(properties):
        for col in range(numclusters):
            profiles_fitperiods_hourly.loc[:,idx==col,:][prop].T.reset_index(drop=True).plot(
                ax=ax[row,col], lw=0.2, legend=False)
            centroids[prop].T[col].reset_index(drop=True).plot(
                ax=ax[row,col], lw=1.5, ls=':', c='k', legend=False)
            profiles_fitperiods_hourly.loc[:,nearest_period[col],:][prop].T.reset_index(drop=True).plot(
                ax=ax[row,col], lw=1.5, c='k', legend=False)
        for col, period in enumerate(forceperiods):
            profiles.loc[:,period,:][prop].T.reset_index(drop=True).plot(
                ax=ax[row,numclusters+col], lw=1.5, c='k', legend=False)
            ax[0,numclusters+col].set_title('{} (d{})'.format(numclusters+col, period))
        ax[row,0].set_ylabel(prop)
    ### Formatting
    label = ' | '.join(
        profiles.columns.get_level_values('region').drop_duplicates().tolist())
    ax[0,0].annotate(label,(0,1.25), xycoords='axes fraction', fontsize='large',)
    ax[0,0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(24))
    ax[0,0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(6))
    ax[0,0].set_xlim(0, nhours)
    for col in range(numclusters):
        ax[0,col].set_title('{} ({})'.format(col, pd.Series(idx).value_counts()[col]))
        ax[-1,col].tick_params(axis='x',labelsize=9)
    for row in range(len(properties)):
        ax[row,0].set_ylim(0)
        for col in range(numclusters+len(forceperiods)):
            for x in np.arange(0,nhours+1,24):
                ax[row,col].axvline(x,c='k',ls=':',lw=0.3)
    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'profiles-day_hourly-clustered.png'))
    if interactive: plt.show()
    plt.close()


def plot_clusters_pca(profiles_fitperiods_hourly, sw, reeds_path, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()
    import sklearn.decomposition

    pca = sklearn.decomposition.PCA(n_components=2)
    transformed = pd.DataFrame(pca.fit_transform(profiles_fitperiods_hourly))
    colors = plots.rainbowmapper(range(int(sw['GSw_HourlyNumClusters'])))

    plt.close()
    f,ax = plt.subplots()
    for y in colors:
        ax.scatter(
            transformed[0][idx==y], transformed[1][idx==y],
            color=colors[y], lw=0, s=10)
    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'clusters-pca-{}totaldays.png'.format(
        sw['GSw_HourlyNumClusters'])))
    if interactive: plt.show()
    plt.close()


def plot_ldc(
        period_szn, profiles, rep_periods,
        forceperiods_write, sw, reeds_path, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()

    colors = plots.rainbowmapper(rep_periods, plt.cm.turbo)

    ### Get clustered load, repeating representative periods based on how many
    ### periods they represent
    numperiods = period_szn.value_counts().rename('numperiods').to_frame()
    numperiods['yearperiod'] = numperiods.index.map(hourly_repperiods.szn2yearperiod).values
    numperiods['year'] = numperiods.index.map(hourly_repperiods.szn2yearperiod).map(lambda x: x[0])
    numperiods['yperiod'] = numperiods.index.map(hourly_repperiods.szn2period)
    periods = [[row.yearperiod] * row.numperiods for (i,row) in numperiods.iterrows()]
    periods = [item for sublist in periods for item in sublist]

    #### Hourly
    hourly_in = (
        profiles
        .divide(sw['GSw_HourlyClusterWeights'], level='property')
        .stack('h_of_period')
        .loc[sw['GSw_HourlyWeatherYears']]
    ).copy()
    hourly_out = hourly_in.unstack('h_of_period').loc[periods].stack('h_of_period')

    #### Daily
    periodly_in = hourly_in.groupby('yperiod').mean()
    ## Index doesn't matter; replace it so we can take daily mean
    periodly_out = hourly_out.copy()
    hourly_out.index = hourly_in.index.copy()
    periodly_out = hourly_out.groupby('yperiod').mean()

    ### Get axis coordinates: properties = rows, regions = columns
    properties = periodly_out.columns.get_level_values('property').unique().values
    regions = periodly_out.columns.get_level_values('region').unique().values
    nrows, ncols = len(properties), len(regions)
    coords = {}
    if ncols == 1:
        coords = dict(zip(
            [(prop, regions[0]) for prop in properties],
            range(nrows)))
    elif nrows == 1:
        coords = dict(zip(
            [(properties[0], region) for region in regions],
            range(ncols)))
    else:
        coords = dict(zip(
            [(prop, reg) for prop in properties for reg in regions],
            [(row, col) for row in range(nrows) for col in range(ncols)],
        ))

    ###### Plot it
    for plotlabel, xlabel, dfin, dfout in [
        ('hourly','Hour',hourly_in,hourly_out),
        ('periodly','Period',periodly_in,periodly_out),
    ]:
        plt.close()
        f,ax = plt.subplots(
            nrows,ncols,figsize=(len(regions)*1.2,9),sharex=True,sharey='row',
            gridspec_kw={'hspace':0.1,'wspace':0.1},
        )
        for region in regions:
            for prop in properties:
                df = dfout[prop][region].sort_values(ascending=False)
                ax[coords[prop,region]].plot(
                    range(len(dfout)), df.values,
                    label='Clustered', c='C1')
                #     label='Clustered', c='C7', lw=0.25)
                # ax[coords[prop,region]].scatter(
                #     range(len(dfout)), df.values,
                #     c=df.index.map(yperiod2color), s=10, lw=0,
                # )
                ax[coords[prop,region]].plot(
                    range(len(dfin)),
                    dfin[prop][region].sort_values(ascending=False).values,
                    ls=':', label='Original', c='k')
        ### Formatting
        for region in regions:
            ax[coords[properties[0], region]].set_title(region)
        for prop in properties:
            ax[coords[prop, regions[0]]].set_ylabel(prop)
            ax[coords[prop, regions[0]]].set_ylim(0)
        ax[coords[properties[0], regions[0]]].annotate(
            '{} periods: {} forced, {} clustered'.format(
                sw['GSw_HourlyNumClusters'], len(forceperiods_write),
                int(sw['GSw_HourlyNumClusters']) - len(forceperiods_write)),
            (0,1.15), xycoords='axes fraction', fontsize='x-large',
        )
        ax[coords[properties[0], regions[-1]]].legend(
            loc='lower right', bbox_to_anchor=(1,1.1), ncol=2)
        ax[coords[properties[-1], regions[0]]].set_xlabel(
            '{} of year'.format(xlabel), x=0, ha='left')
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'ldc-{}-{}totaldays.png'.format(
            plotlabel, sw['GSw_HourlyNumClusters'])))
        if interactive: plt.show()
        plt.close()


def plot_maps(sw, inputs_case, reeds_path, figpath):
    """
    """
    ### Imports
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    import geopandas as gpd
    import shapely
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()
    ### Settings
    cmaps = {
        'cf_full':'turbo', 'cf_hourly':'turbo', 'cf_diff':'coolwarm',
        'GW_full':'gist_earth_r', 'GW_hourly':'gist_earth_r',
        'GW_diff':'coolwarm', 'GW_frac':'coolwarm', 'GW_pct':'coolwarm', 
    }
    vm = {
        'wind-ons':{'cf_full':(0,0.8),'cf_hourly':(0,0.8),'cf_diff':(-0.05,0.05)},
        'upv':{'cf_full':(0,0.4),'cf_hourly':(0,0.4),'cf_diff':(-0.05,0.05)},
    }
    vlimload = 0.05
    title = (
        'Algorithm={}, NumClusters={}, RegionLevel={},\n'
        'PeakLevel={}, MinRElevel={}, ClusterWeights={}'
    ).format(
        sw['GSw_HourlyClusterAlgorithm'],
        sw['GSw_HourlyNumClusters'], sw['GSw_HourlyClusterRegionLevel'],
        sw['GSw_HourlyPeakLevel'], sw['GSw_HourlyMinRElevel'],
        '__'.join(['_'.join([
            str(i),str(v)]) for (i,v) in sw['GSw_HourlyClusterWeights'].iteritems()]))
    techs = ['wind-ons','upv']
    colors = {'cf_full':'k', 'cf_hourly':'C1'}
    lss = {'cf_full':':', 'cf_hourly':'-'}
    zorders = {'cf_full':10, 'cf_hourly':9}

    ### Get the CF data over all years, take the mean
    recf = pd.read_hdf(os.path.join(inputs_case,'recf.h5')).mean()

    ### Get supply curves
    dfsc = {}
    for tech in techs:
        #Why is GSw_SitingWindOns used for all techs below??
        dfsc[tech] = pd.read_csv(
            os.path.join(
                reeds_path,'inputs','supplycurvedata',
                '{}_supply_curve-{}.csv'.format(
                    tech,sw['GSw_SitingWindOns']))
        ).rename(columns={'region':'r'})
        dfsc[tech]['i'] = tech + '_' + dfsc[tech]['class'].astype(str)

    dfsc = pd.concat(dfsc, axis=0, names=('tech',)).drop(
        ['dist_km','dist_mi','supply_curve_cost_per_mw'], errors='ignore', axis=1)

    ### Add geographic and CF information
    sitemap = pd.read_csv(
        os.path.join(reeds_path,'inputs','supplycurvedata','sitemap.csv'),
        index_col='sc_point_gid',
    )

    dfsc['latitude'] = dfsc.sc_point_gid.map(sitemap.latitude)
    dfsc['longitude'] = dfsc.sc_point_gid.map(sitemap.longitude)
    dfsc = plots.df2gdf(dfsc)
    dfsc['resource'] = dfsc.i + '_' + dfsc.r
    dfsc['cf_full'] = dfsc.resource.map(recf)

    ### Get the BA map
    dfba = gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','US_PCA')).set_index('rb')
    dfba['x'] = dfba.geometry.centroid.x
    dfba['y'] = dfba.geometry.centroid.y
    ### Aggregate to states
    dfstates = dfba.dissolve('st')

    ### Get the hourly data
    hours = pd.read_csv(
        os.path.join(inputs_case,'numhours.csv')
    ).rename(columns={'*h':'h'}).set_index('h').numhours
    dfcf = pd.read_csv(os.path.join(inputs_case,'cf_vre.csv')).rename(columns={'*i':'i'})

    for tech in techs:
        ### Get the annual average CF of the hourly-processed data
        cf_hourly = dfcf.loc[dfcf.i.str.startswith(tech)].pivot(
            index=['i','r'],columns='h',values='cf')
        cf_hourly = (
            (cf_hourly * cf_hourly.columns.map(hours)).sum(axis=1) / hours.sum()
        ).rename('cf_hourly').reset_index()
        cf_hourly['resource'] = cf_hourly.i + '_' + cf_hourly.r

        ### Merge with supply curve, take the difference
        cfmap = dfsc.assign(
            cf_hourly=dfsc.resource.map(cf_hourly.set_index('resource').cf_hourly)).loc[tech].copy()
        cfmap['cf_diff'] = cfmap.cf_hourly - cfmap.cf_full

        ### Plot the difference map
        plt.close()
        f,ax = plt.subplots(1,3,figsize=(13,4),gridspec_kw={'wspace':-0.05})
        for col in range(3):
            dfstates.plot(ax=ax[col], facecolor='none', edgecolor='k', lw=0.25, zorder=10000)
        for x,col in enumerate(['cf_full','cf_hourly','cf_diff']):
            cfmap.plot(
                ax=ax[x], column=col, cmap=cmaps[col],
                marker='s', markersize=0.4, lw=0, legend=True,
                legend_kwds={'shrink':0.75,'orientation':'horizontal',
                            'label':'{} {}'.format(tech,col), 'pad':0},
                vmin=vm[tech][col][0], vmax=vm[tech][col][1],
            )
            ax[x].axis('off')
        ax[0].set_title(title, y=0.95, x=0.05, ha='left', fontsize=10)
        plt.savefig(os.path.join(figpath,'cfmap-{}-{}totaldays.png'.format(
            tech.replace('-',''), sw['GSw_HourlyNumClusters'])))
        if interactive: plt.show()
        plt.close()

        ### Plot the distribution of capacity factors
        plt.close()
        f,ax = plt.subplots()
        for col in ['cf_full','cf_hourly']:
            ax.plot(
                np.linspace(0,100,len(cfmap)),
                cfmap.sort_values('cf_full', ascending=False)[col].values,
                label=col.split('_')[1],
                color=colors[col], ls=lss[col], zorder=zorders[col],
            )
        ax.set_ylim(0)
        ax.set_xlim(-1,101)
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
        ax.legend(fontsize='large', frameon=False)
        ax.set_ylabel('{} capacity factor [.]'.format(tech))
        ax.set_xlabel('Percent of sites [%]')
        ax.set_title(title.replace(' ','\n').replace(',',''), x=0, ha='left', fontsize=10)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'cfmapdist-{}-{}totaldays.png'.format(
            tech.replace('-',''), sw['GSw_HourlyNumClusters'])))
        if interactive: plt.show()
        plt.close()

    ###### Do it again for load
    ### Get the full hourly data, take the mean for the cluster year
    load_raw = pd.read_hdf(os.path.join(inputs_case, 'load.h5'))
    loadyears = load_raw.index.get_level_values('year').unique()
    keepyear = (
        int(sw['GSw_HourlyClusterYear']) if int(sw['GSw_HourlyClusterYear']) in loadyears
        else max(loadyears))
    load_raw = load_raw.loc[keepyear].mean() / 1000
    ## load.h5 is busbar load, but b_inputs.gms ingests end-use load, so scale down by distloss
    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, usecols=[0,1], index_col=0, squeeze=True)
    load_raw *= (1 - scalars['distloss'])
    ### Get the representative data, take the mean for the cluster year
    load_allyear = (
        pd.read_csv(os.path.join(inputs_case, 'load_allyear.csv')).rename(columns={'*r':'r'})
        .set_index(['t','r','h']).MW.loc[keepyear]
        .multiply(hours).groupby('r').sum()
        / hours.sum()
    ) / 1000
    ### Map it
    dfmap = dfba.copy()
    dfmap['GW_full'] = load_raw
    dfmap['GW_hourly'] = load_allyear
    dfmap['GW_diff'] = dfmap.GW_hourly - dfmap.GW_full
    dfmap['GW_frac'] = dfmap.GW_hourly / dfmap.GW_full - 1

    ### Plot the difference map
    plt.close()
    f,ax = plt.subplots(1,3,figsize=(13,4),gridspec_kw={'wspace':-0.05})
    for col in range(3):
        dfstates.plot(ax=ax[col], facecolor='none', edgecolor='k', lw=0.25, zorder=10000)
    for x,col in enumerate(['GW_full','GW_hourly','GW_frac']):
        dfmap.plot(
            ax=ax[x], column=col, cmap=cmaps[col], legend=True,
            legend_kwds={'shrink':0.75,'orientation':'horizontal',
                        'label':'load {}'.format(col), 'pad':0},
            vmin=(0 if col != 'GW_frac' else -vlimload),
            vmax=(dfmap[['GW_full','GW_hourly']].max().max() if col != 'GW_frac' else vlimload),
        )
        ax[x].axis('off')
    ax[0].set_title(title, y=0.95, x=0.05, ha='left', fontsize=10)
    plt.savefig(os.path.join(figpath,'loadmap-{}totaldays.png'.format(
        sw['GSw_HourlyNumClusters'])))
    if interactive: plt.show()
    plt.close()

    ### Plot the distribution of load by region
    colors = {'GW_full':'k', 'GW_hourly':'C1'}
    lss = {'GW_full':':', 'GW_hourly':'-'}
    zorders = {'GW_full':10, 'GW_hourly':9}
    plt.close()
    f,ax = plt.subplots()
    for col in ['GW_full','GW_hourly']:
        ax.plot(
            range(1,len(dfmap)+1),
            dfmap.sort_values('GW_full', ascending=False)[col].values,
            label='{} ({:.1f} GW mean)'.format(col.split('_')[1], dfmap[col].sum()),
            color=colors[col], ls=lss[col], zorder=zorders[col],
        )
    ax.set_ylim(0)
    ax.set_xlim(0,len(dfmap)+1)
    ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
    ax.legend(fontsize='large', frameon=False)
    ax.set_ylabel('Average load [GW]')
    ax.set_xlabel('Number of BAs')
    ax.set_title(title.replace(' ','\n').replace(',',''), x=0, ha='left', fontsize=10)
    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'loadmapdist-{}totaldays.png'.format(
        sw['GSw_HourlyNumClusters'])))
    if interactive: plt.show()
    plt.close()


def plot_8760(profiles, period_szn, rep_periods, sw, reeds_path, figpath):
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()

    def get_profiles(regions, year):
        """Assemble 8760 profiles from original and representative days"""
        timeindex = pd.date_range(f'{year}-01-01',f'{year+1}-01-01',freq='H',closed='left')[:8760]
        props = profiles.columns.get_level_values('property').unique()
        ### Original profiles
        dforig = {}
        for prop in props:
            df = profiles[prop].loc[year].stack('h_of_period')[regions].sum(axis=1)
            dforig[prop] = df / df.max()
            dforig[prop].index = timeindex
        dforig = pd.concat(dforig, axis=1)

        ### Representative profiles
        periodmap = period_szn.map(hourly_repperiods.szn2yearperiod).to_frame()
        periodmap['year'] = periodmap.index.map(lambda x: x[0])
        periodmap['yperiod'] = periodmap.index.map(lambda x: x[1])
        periodmap = periodmap.loc[periodmap.year==year].yperiod

        dfrep = {}
        for prop in props:
            df = (
                profiles[prop].loc[year].loc[periodmap.values]
                .stack('h_of_period')[regions].sum(axis=1))
            dfrep[prop] = df / df.max()
            dfrep[prop].index = timeindex
        dfrep = pd.concat(dfrep, axis=1)

        return dforig, dfrep

    ###### All regions
    for year in sw['GSw_HourlyWeatherYears']:
        props = profiles.columns.get_level_values('property').unique()
        regions = profiles.columns.get_level_values('region').unique()
        dforig, dfrep = get_profiles(regions, year)

        ### Original vs representative
        plt.close()
        f,ax = plt.subplots(38,1,figsize=(12,16),sharex=True,sharey=True)
        for i, prop in enumerate(props):
            plots.plotyearbymonth(
                dfrep[prop].rename('Representative').to_frame(),
                style='line', colors=['C1'], ls='-', f=f, ax=ax[i*12+i:(i+1)*12+i])
            plots.plotyearbymonth(
                dforig[prop].rename('Original').to_frame(),
                style='line', colors=['k'], ls=':', f=f, ax=ax[i*12+i:(i+1)*12+i])
        for i in [12,25]:
            ax[i].axis('off')
        for i, prop in list(zip(range(len(props)), props)):
            ax[i*12+i].set_title(
                '{}: {}'.format(prop,' | '.join(regions)),x=0,ha='left',fontsize=12)
        ax[0].legend(loc='lower left', bbox_to_anchor=(0,1.5), ncol=2, frameon=False)
        plt.savefig(os.path.join(figpath,f'8760-allregions-{year}.png'))
        if interactive: plt.show()
        plt.close()

        ### Load, wind, solar together; original
        plt.close()
        f,ax = plots.plotyearbymonth(
            dforig[['wind-ons','upv']], colors=['#0064ff','#ff0000'], alpha=0.5)
        plots.plotyearbymonth(dforig['load'], f=f, ax=ax, style='line', colors='k')
        plt.savefig(os.path.join(figpath,f'8760-allregions-original-{year}.png'))
        if interactive: plt.show()
        plt.close()

        ### Load, wind, solar together; representative
        plt.close()
        f,ax = plots.plotyearbymonth(
            dfrep[['wind-ons','upv']], colors=['#0064ff','#ff0000'], alpha=0.5)
        plots.plotyearbymonth(dfrep['load'], f=f, ax=ax, style='line', colors='k')
        plt.savefig(os.path.join(figpath,f'8760-allregions-representative-{year}.png'))
        if interactive: plt.show()
        plt.close()

        ###### Individual regions, original vs representative
        for region in profiles.columns.get_level_values('region').unique():
            dforig, dfrep = get_profiles([region], year)

            plt.close()
            f,ax = plt.subplots(38,1,figsize=(12,16),sharex=True,sharey=True)
            for i, prop in enumerate(props):
                plots.plotyearbymonth(
                    dfrep[prop].rename('Representative').to_frame(),
                    style='line', colors=['C1'], ls='-', f=f, ax=ax[i*12+i:(i+1)*12+i])
                plots.plotyearbymonth(
                    dforig[prop].rename('Original').to_frame(),
                    style='line', colors=['k'], ls=':', f=f, ax=ax[i*12+i:(i+1)*12+i])
            for i in [12,25]:
                ax[i].axis('off')
            for i, prop in list(zip(range(len(props)), props)):
                ax[i*12+i].set_title('{}: {}'.format(prop,region),x=0,ha='left',fontsize=12)
            ax[0].legend(loc='lower left', bbox_to_anchor=(0,1.5), ncol=2, frameon=False)
            plt.savefig(os.path.join(figpath,f'8760-{region}-{year}.png'))
            if interactive: plt.show()


def plots_original(
        profiles, rep_periods, period_szn,
        sw, reeds_path, figpath, make_plots,
    ):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()

    ### Input processing
    idx_reedsyr = period_szn.map(hourly_repperiods.szn2yearperiod)
    medoid_profiles = profiles.loc[rep_periods]
    centroids = profiles.loc[rep_periods]
    centroid_profiles = centroids * profiles.stack('h_of_period').max()

    colors = plots.rainbowmapper(list(set(idx_reedsyr)), plt.cm.turbo)
    hoursperperiod = {'day':24, 'wek':120, 'year':24}[sw['GSw_HourlyType']]
    periodsperyear = {'day':365, 'wek':73, 'year':365}[sw['GSw_HourlyType']]

    ### plot a dendrogram
    if make_plots >= 3:
        plt.close()
        plt.figure(figsize=(12,9))
        plt.title("Dendrogram of Time Clusters")
        import scipy
        dend = scipy.cluster.hierarchy.dendrogram(
            scipy.cluster.hierarchy.linkage(profiles, method='ward'),
            color_threshold=7,
        )
        plt.gcf().savefig(os.path.join(figpath,'dendrogram.png'))
        if interactive: plt.show()
        plt.close()

    ### PLOT ALL DAYS ON SAME X AXIS:
    try:
        ## Map days to axes
        ncols = len(colors)
        nrows = 1
        coords = dict(zip(
            colors.keys(),
            [col for col in range(ncols)]
        ))
        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(1.5*ncols,2.5*nrows), sharex=True, sharey=True)
        for day in range(len(idx_reedsyr)):
            szn = idx_reedsyr[day]
            this_profile = profiles.load.iloc[day].groupby('h_of_period').sum()
            ax[coords[szn]].plot(
                range(len(this_profile)), this_profile.values/1e3, color=colors[szn], alpha=0.5)
        ## add centroids and medoids to the plot:
        for szn in colors:
            ## centroids - only for clustered days, not force-included days
            try:
                ax[coords[szn]].plot(
                    range(len(this_profile)),
                    centroid_profiles['load'].loc[szn].groupby('h_of_period').sum().values/1e3,
                    color='k', alpha=1, linewidth=2, label='centroid',
                )
            except IndexError:
                pass
            ## medoids
            ax[coords[szn]].plot(
                range(len(this_profile)),
                medoid_profiles['load'].loc[szn].groupby('h_of_period').sum().values/1e3,
                ls='--', color='0.7', alpha=1, linewidth=2, label='medoid',
            )
            ## title
            ax[coords[szn]].set_title(
                '{}, {} days'.format(szn, idx_reedsyr.value_counts()[szn]), size=9)

        ax[0].legend(loc='upper left', frameon=False, fontsize='small')
        ax[0].set_xlabel('Hour')
        ax[0].set_ylabel('Conterminous\nUS Load [GW]', y=0, ha='left')
        ax[0].xaxis.set_major_locator(
            mpl.ticker.MultipleLocator(6 if sw['GSw_HourlyType']=='day' else 24))
        ax[0].xaxis.set_minor_locator(
            mpl.ticker.MultipleLocator(3 if sw['GSw_HourlyType']=='day' else 12))
        ax[0].annotate(
            'Cluster Comparison (All Days in {} Shown)'.format(
                '2007–2013' if len(profiles.index.unique(level='year')) > 1 else '2012' ),
            xy=(0,1.2), xycoords='axes fraction', ha='left',
        )
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'day_comparison_all.png'))
        if interactive: plt.show()
        plt.close()
    except Exception as err:
        print('day_comparison_all.png failed with the following error:\n{}'.format(err))


    ### PLOT LOAD FOR THE ENTIRE ReEDS YEAR COLORED BY CLUSTER AND MEDOID:
    if make_plots >= 3:
        try:
            for year in sw['GSw_HourlyWeatherYears']:
                plt.close()
                f,ax = plt.subplots(figsize=(14,3.5))
                plotted = [False for i in range(int(sw['GSw_HourlyNumClusters']))]
                nationwide_reedsyr_load = profiles_long[
                    (profiles_long['year']==year) & (profiles_long['property']=='load')
                ].groupby(['year','yperiod','hour'],as_index=False).sum()
                nationwide_reedsyr_load['hour_numeric'] = pd.to_numeric(
                    nationwide_reedsyr_load['hour'].str.lstrip('h'))
                nationwide_reedsyr_load.sort_values(['year','hour_numeric'],inplace=True)
                for this_yperiod in nationwide_reedsyr_load.yperiod.unique():
                    ax.fill_between(
                        nationwide_reedsyr_load.loc[
                            nationwide_reedsyr_load['yperiod']==this_yperiod,'hour_numeric'].to_numpy(),
                        nationwide_reedsyr_load.loc[
                            nationwide_reedsyr_load['yperiod'] == this_yperiod,'value'].to_numpy()/1e3,
                        ls='-', color=colors[idx_reedsyr[this_yperiod-1]], lw=0, alpha=0.5,
                        label=(
                            '{} ({} periods)'.format(
                                period_szn.loc[period_szn['period']==this_yperiod,'season'].iloc[0],
                                sum(idx_reedsyr == idx_reedsyr[this_yperiod-1]))
                            if not plotted[idx_reedsyr[this_yperiod-1]]
                            else '_nolabel'
                        )
                    )
                    plotted[idx_reedsyr[this_yperiod-1]] = True
                ### Plot the medoid profiles
                for i, (yperiod, row) in enumerate(medoid_profiles.iterrows()):
                    ax.plot(
                        list(range((yperiod-1)*hoursperperiod+1,(yperiod)*hoursperperiod+1)),
                        row['load'].groupby('h_of_period').sum().values/1e3,
                        color=colors[i], alpha=1, linewidth=1.5,
                        label='{} Medoid'.format(period_szn.set_index('period').season[int(yperiod)])
                    )
                ax.set_xlim(0,8760)
                ax.set_ylim(0)
                ax.legend(
                    loc='upper left', bbox_to_anchor=(1,1), ncol=len(colors)//9+1)
                ax.set_ylabel('Conterminous US Load (GW)')
                ax.set_title('Cluster and Medoid Definitions')
                plots.despine(ax)
                plt.savefig(os.path.join(figpath,f'year_clusters-load-{year}.png'))
                if interactive: plt.show()
                plt.close()
        except Exception as err:
            print('year_clusters.png failed with the following error:\n{}'.format(err))


    ### Plot daily profile for the US colored by representative period
    try:
        ## TODO: Switch to actual months...
        nrows, ncols = (12, 31) if sw['GSw_HourlyType'] in ['day','year'] else (13,6)
        coords = dict(zip(
            range(1,periodsperyear+1),
            [(row,col) for row in range(nrows) for col in range(ncols)]
        ))
        for year in sw['GSw_HourlyWeatherYears']:
            for prop in ['load','upv','wind-ons']:
                dfplot = profiles_long[
                    (profiles_long['year']==year) & (profiles_long['property']==prop)
                ].groupby(['year','yperiod','hour'],as_index=False).sum()
                dfplot['hour_numeric'] = pd.to_numeric(
                    dfplot['hour'].str.lstrip('h'))
                dfplot.sort_values(['year','hour_numeric'],inplace=True)

                plt.close()
                f,ax = plt.subplots(
                    nrows, ncols, sharex=True, sharey=True,
                    gridspec_kw={'wspace':0, 'hspace':0,},
                    figsize=(12,6),
                )
                for this_yperiod in range(1,periodsperyear+1):
                    ax[coords[this_yperiod]].fill_between(
                        range(hoursperperiod),
                        dfplot.loc[
                            dfplot['yperiod'] == this_yperiod,'value'].to_numpy()/1e3,
                        ls='-', color=colors[idx_reedsyr[this_yperiod]], alpha=0.35,
                    )
                    ### Label the szn
                    ax[coords[this_yperiod]].annotate(
                        int(period_szn[this_yperiod][6:]),
                        (0.5,0), xycoords='axes fraction', va='bottom', ha='center',
                        fontsize=8, color=colors[idx_reedsyr[this_yperiod]],
                    )
                ### Plot the medoid profiles
                for i, (yperiod, row) in enumerate(medoid_profiles.iterrows()):
                    ax[coords[yperiod]].plot(
                        range(hoursperperiod), row[prop].groupby('h_of_period').sum().values/1e3,
                        color=colors[yperiod], alpha=1, linewidth=2,
                    )
                for row in range(nrows):
                    for col in range(ncols):
                        ax[row,col].axis('off')
                ax[0,0].set_title('Cluster and Medoid Definitions', x=0, ha='left')
                ax[0,0].set_ylim(0)
                ax[0,0].set_xlim(-1,hoursperperiod+1)
                plots.despine(ax)
                plt.savefig(os.path.join(figpath,f'year_clusters_daily-{prop}.png'))
                if interactive: plt.show()
                plt.close()
    except Exception as err:
        print('year_clusters_daily.png failed with the following error:\n{}'.format(err))
