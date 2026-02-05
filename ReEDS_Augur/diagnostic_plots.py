#%%### Imports
import os
import sys
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
from glob import glob
import traceback
import gdxpds
import cmocean
### Local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from reeds import plots

plots.plotparams()


#%%### Fixed inputs
dpi = None
interactive = False
savefig = True


#%%### Functions
def delete_temporary_files(sw):
    """
    Delete temporary csv, pkl, and h5 files
    """
    dropfiles = (
        glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.pkl"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.h5"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.csv"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','PRAS',f"PRAS_{sw['t']}*.pras"))
    )

    for keyword in sw['keepfiles']:
        dropfiles = [f for f in dropfiles if not os.path.basename(f).startswith(keyword)]

    for f in dropfiles:
        os.remove(f)


def group_techs(dfin, dfs, technamecol='i'):
    """
    Aggregate techs using bokehpivot tables
    """
    ## Get the colors
    tech_map = dfs['tech_map']
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    ## Aggregate by type
    dfout = dfin.copy()
    if technamecol in ['column', 'columns', 'wide', None, 0, False]:
        def renamer(x):
            out = (x if x[0].startswith('battery')
                else (x[0].strip('_01234567890*').lower(), x[1]))
            return out
        dfout.columns = dfout.columns.map(renamer)
        dfout.columns = (
            dfout.columns
            .map(lambda x: ([i for i in tech_map.index if x[0].startswith(i)][0], x[1]))
            .map(lambda x: (tech_map.get(x[0],x[0]), x[1]))
        )
    else:
        def renamer(x):
            out = x if x.startswith('battery') else x.strip('_01234567890*').lower()
            return out
        dfout[technamecol] = dfout[technamecol].map(renamer)
        dfout[technamecol] = (
            dfout[technamecol]
            .map(lambda x: ([i for i in tech_map.drop('hyd').index if x.startswith(i)]+[x])[0])
            .map(lambda x: tech_map.get(x,x))
        )
    return dfout


#%% Input-loading function
def get_inputs(sw):
    ### Make savepath
    sw['savepath'] = os.path.join(sw['casedir'], 'outputs', 'Augur_plots')
    os.makedirs(sw['savepath'], exist_ok=True)

    ##### Load shared parameters
    fulltimeindex = reeds.timeseries.get_timeindex(sw.resource_adequacy_years)

    h_dt_szn = (
        pd.read_csv(os.path.join(sw['casedir'], 'inputs_case', 'rep', 'h_dt_szn.csv'))
        .assign(hr=(['hr{:>03}'.format(i+1) for i in range(sw['hoursperperiod'])]
                    * sw['periodsperyear'] * len(sw.resource_adequacy_years_list)))
        .assign(datetime=fulltimeindex)
    )
    h_dt_szn['d'] = h_dt_szn.datetime.dt.strftime('sy%Yd%j')

    gdxreeds = gdxpds.to_dataframes(
        os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f'reeds_data_{sw["t"]}.gdx'))

    techs = gdxreeds['i_subsets'].pivot(columns='i_subtech',index='i',values='Value')
    h2dac = techs['CONSUME'].dropna().index

    tech_map = pd.read_csv(
        os.path.join(sw['reeds_path'],'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).str.lower()
    tech_map = tech_map.drop_duplicates().set_index('raw').display.str.lower()
    tech_map['vre'] = 'vre'

    existinghydrotechs = [
        'hyded','hydend','hydend_hyded',
    ]
    newhydrotechs = [
        'hydd','hydnd','hydnpd','hydnpnd','hydsd','hydsnd','hydud','hydund',
    ]
    tech_map = pd.concat([
        tech_map,
        pd.Series(dict(zip(existinghydrotechs,['hydro_exist']*len(existinghydrotechs)))),
        pd.Series(dict(zip(newhydrotechs,['hydro_new']*len(newhydrotechs)))),
    ]).reset_index().drop_duplicates().set_index('index')[0].rename(None)

    tech_style = pd.read_csv(
        os.path.join(sw['reeds_path'],'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order',
    ).squeeze(1)
    tech_style.index = tech_style.index.str.lower()
    tech_style['vre'] = mpl.colors.to_hex('C1')
    tech_style['dropped'] = '#d62728'
    for i in ['hydro_exist', 'hydro_new']:
        tech_style[i] = tech_style['hydro']
    # ## Add some techs
    # for i in [1,2]:
    #     tech_style[f'csp{i}'] = tech_style['csp']
    # for i in [1,2,3]:
    #     tech_style[f'pvb{i}'] = tech_style['pvb']

    hierarchy = reeds.io.get_hierarchy(sw.casedir)

    resources = pd.read_csv(
        os.path.join(sw['casedir'],'inputs_case','resources.csv')
    ).set_index('resource')
    resources['tech'] = (
        resources.i.map(lambda x: x.split('|')[0])
        .map(lambda x: x if x.startswith('battery') else x.strip('_01234567890*')))

    resources['rb'] = resources.r

    ##### Hourly dispatch by month
    ### Load and aggregate the VRE generation profiles by tech group
    try:
        vre_gen = reeds.io.read_file(
            os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f'pras_vre_gen_{sw.t}.h5'),
            parse_timestamps=True,
        )
    except FileNotFoundError:
        vre_gen = None

    ### Get vre_gen by tech (only resource_adequacy_years)
    vre_gen_usa = (
        vre_gen
        .rename(columns=dict(zip(vre_gen.columns, vre_gen.columns.map(lambda x: x.split('|')[0]))))
        .groupby(axis=1, level=0).sum()
        .set_index(fulltimeindex)
    )
    if len(sw['resource_adequacy_years_list']) == 1:
        vre_gen_usa = vre_gen_usa.xs(int(sw['resource_adequacy_years_list'][0]), level='year', axis=0)

    ### Get vre_gen summed over tech by BA (full 7 years)
    vre_gen_r = (
        vre_gen
        .rename(columns=dict(zip(vre_gen.columns, vre_gen.columns.map(lambda x: x.split('|')[1]))))
        .groupby(axis=1, level=0).sum()
    )

    ### Load hourly demand
    try:
        load_r = pd.read_hdf(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',f'load_{sw.t}.h5')
        )
        load_r.index = fulltimeindex
    except FileNotFoundError:
        load_r = None

    ### Load PRAS load
    try:
        pras_load = reeds.io.read_file(
            os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f'pras_load_{sw.t}.h5'),
            parse_timestamps=True,
        )
    except FileNotFoundError:
        pras_load = None
    pras_load.index = fulltimeindex
    try:
        pras_h2dac_load = reeds.io.read_file(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',
                f"pras_h2dac_load_{sw['t']}.h5"),
            parse_timestamps=True,
        )
    except FileNotFoundError:
        pras_h2dac_load = pd.DataFrame(columns=pras_load.columns)
    pras_h2dac_load.index = fulltimeindex

    ### Load input capacity to PRAS
    try:
        max_cap = pd.read_csv(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',f"max_cap_{sw['t']}.csv"))
    except FileNotFoundError:
        max_cap = pd.DataFrame(columns=['i','v','r','MW'])

    ### Load LOLE/EUE/NEUE from PRAS
    try:
        pras = reeds.io.read_pras_results(
            os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS',
                         f"PRAS_{sw.t}i{sw.iteration}.h5")
        )
        pras.index = fulltimeindex
    except FileNotFoundError as err:
        print(f"Failed to load PRAS outputs: {err}")
        pras = pd.DataFrame({'USA_EUE':9999}, index=fulltimeindex)

    ### Load the PRAS system
    try:
        pras_system = reeds.io.get_pras_system(
            case=sw.casedir, year=sw.t, iteration=sw.iteration)
        for key in pras_system:
            pras_system[key].index = fulltimeindex
        for key in ['gencap', 'storcap', 'genstorcap', 'genfailrate', 'genrepairrate']:
            pras_system[key].columns = pras_system[key].columns.droplevel(['unit','name'])
    except FileNotFoundError as err:
        print(f"Failed to load .pras system: {err}")
        pras_system = dict()

    ###### Get net load profiles
    ### Get net load by BA
    net_load_r = load_r - vre_gen_r
    ### Get net load by ccreg
    net_load_ccreg = net_load_r.rename(columns=hierarchy.ccreg).groupby(axis=1, level=0).sum()
    ### Get net load for the USA
    net_load_usa = net_load_r.set_index(fulltimeindex).sum(axis=1)

    ###### Make combined dataframes for plotting
    ### Get top load hours by ccseason
    datetime2ccseason = h_dt_szn.set_index('datetime').ccseason
    ### Use seasons appropriate to resolution
    ccseasons = h_dt_szn.ccseason.unique()

    ccregs = sorted(net_load_ccreg.columns)
    peakhours = {}
    for ccseason in ccseasons:
        for ccreg in ccregs:
            peakhours[ccseason,ccreg] = (
                net_load_ccreg.loc[net_load_ccreg.index.map(datetime2ccseason)==ccseason][ccreg]
                .nlargest(int(sw['GSw_PRM_CapCreditHours']))
                .index
            )

    dfpeak = (
        pd.DataFrame(peakhours)
        .stack(level=0)
        .reorder_levels([1,0], axis=0)
        .stack()
        .rename('datetime').to_frame()
        .assign(peak=1)
        .reset_index(level=2).rename(columns={'level_2':'ccreg'})
        .pivot(index='datetime', columns='ccreg', values='peak')
        .reindex(fulltimeindex)
        .fillna(0).astype(int)
    )

    peakcolors = plots.rainbowmapper(ccregs, plt.cm.tab20)

    ###### Store them for later
    dfs = {}
    dfs['dfpeak'] = dfpeak
    dfs['fulltimeindex'] = fulltimeindex
    dfs['gdxreeds'] = gdxreeds
    dfs['h_dt_szn'] = h_dt_szn
    dfs['h2dac'] = h2dac
    dfs['hierarchy'] = hierarchy
    dfs['load_r'] = load_r
    dfs['max_cap'] = max_cap
    dfs['net_load_r'] = net_load_r
    dfs['net_load_usa'] = net_load_usa
    dfs['peakcolors'] = peakcolors
    dfs['pras_h2dac_load'] = pras_h2dac_load
    dfs['pras_load'] = pras_load
    dfs['pras_system'] = pras_system
    dfs['pras'] = pras
    dfs['resources'] = resources
    dfs['tech_map'] = tech_map
    dfs['tech_style'] = tech_style
    dfs['vre_gen_usa'] = vre_gen_usa
    dfs['vre_gen'] = vre_gen

    return dfs


#%%### Plotting functions
def plot_netload_profile(sw, dfs):
    """
    Net load profile
    """
    for y in sw['resource_adequacy_years_list']:
        savename = f"A-netload-profile-w{y}-{sw['t']}.png"

        dfpos = dfs['net_load_usa'].loc[str(y)].clip(lower=0)
        dfneg = dfs['net_load_usa'].loc[str(y)].clip(upper=0)
        plt.close()
        f,ax = plots.plotyearbymonth(
            dfpos, colors=['C3'], dpi=dpi,
        )
        plots.plotyearbymonth(
            dfneg, colors=['C0'],
            f=f, ax=ax,
        )
        if savefig:
            plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive:
            plt.show()
        plt.close()


def plot_dropped_load_timeseries_full(sw, dfs):
    """
    Dropped load timeseries
    """
    dropped = dfs['pras']['USA_EUE'].copy()
    timeindex_y = pd.date_range(
        f"{sw['t']}-01-01", f"{sw['t']+1}-01-01", inclusive='left', freq='H',
        tz='Etc/GMT+6')[:8760]
    savename = f"dropped_load-timeseries-wfull-{sw['t']}.png"
    weatheryears = sw.resource_adequacy_years_list
    plt.close()
    f,ax = plt.subplots(len(weatheryears), 1, sharex=True, sharey=True, figsize=(13.33,5))
    for row, y in enumerate(weatheryears):
        ax[row].fill_between(
            timeindex_y, dropped.loc[str(y)].values/1e3,
            lw=0.2, color='C3')
        ### Formatting
        ax[row].annotate(
            y, (0.01,1), xycoords='axes fraction',
            fontsize=14, weight='bold', va='top')
    ### Formatting
    ax[0].set_xlim(
        pd.Timestamp(f"{sw['t']}-01-01 00:00-05:00"),
        pd.Timestamp(f"{sw['t']}-12-31 23:59-05:00"))
    ax[0].set_ylim(0)
    ax[len(weatheryears)-1].set_ylabel('Dropped load [GW]', y=0, ha='left')
    plots.despine(ax)
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def plot_h2dac_load_timeseries(sw, dfs):
    """
    H2 and DAC load timeseries
    """

    dfplot = dfs['pras_h2dac_load'].sum(axis=1)
    if not dfplot.sum():
        return

    for y in sw['resource_adequacy_years_list']:
        savename = f"h2dac_load-timeseries-w{y}-{sw['t']}.png"

        plt.close()
        ## DAC and H2 demand
        f,ax = plots.plotyearbymonth(
            dfplot.loc[str(y)].rename('H2/DAC\ndemand').abs().to_frame(),
            colors=['C9'], dpi=dpi,
        )
        if savefig:
            plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive:
            plt.show()
        plt.close()


def plot_dropped_load_duration(sw, dfs):
    """
    Dropped load duration
    """
    dropped = dfs['pras']['USA_EUE'].copy()

    savename = f"dropped_load-duration-{sw['t']}.png"
    plt.close()
    f,ax = plt.subplots(dpi=dpi)
    ## Dropped load
    ax.fill_between(
        range(len(dropped)),
        dropped.rename('Dropped').sort_values(ascending=False).values/1e3,
        color='C3', lw=0, label='Dropped',
    )
    ## Mark the extrema
    ax.plot(
        [0], [dropped.max()/1000],
        lw=0, marker=1, ms=5, c='C3',)
    ax.plot(
        [(dropped>0).sum()], [0],
        lw=0, marker=2, ms=5, c='C3',)
    ## Formatting
    ax.set_ylabel('Demand [GW]')
    ax.set_xlabel(
        f"Hours of dispatch period ({min(sw['resource_adequacy_years_list'])}–"
        f"{max(sw['resource_adequacy_years_list'])}) [h]")
    ax.set_xlim(0, max((dropped>0).sum(), 1))
    ax.set_ylim(0)
    ax.legend(
        # loc='upper left', bbox_to_anchor=(1,1.25),
        fontsize=11, frameon=True, ncol=1,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    plots.despine(ax)
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def map_dropped_load(sw, dfs, level='r'):
    """
    Annual EUE and NEUE by ReEDS zone
    """
    ### Get the inputs
    dfmap = reeds.io.get_dfmap(sw['casedir'])
    dfba = dfmap['r']
    dropped = dfs['pras'][
        [c for c in dfs['pras'] if c.endswith('_EUE') and (not c.startswith('USA'))]
    ].copy()
    dropped.columns = dropped.columns.map(lambda x: x.split('_')[0])
    units = {
        ('EUE','max'): ('MW',1), ('EUE','mean'): ('MW',1), ('EUE','sum'): ('GWh',1e-3),
        ('NEUE','max'): ('%',1e2), ('NEUE','sum'): ('ppm',1e6),
    }
    load = dfs['pras_load']

    ### Plot it
    for metric in ['EUE','NEUE']:
        ## Aggregate if necessary
        if level not in ['r','rb','ba']:
            dropped = (
                dropped.rename(columns=dfs['hierarchy'][level])
                .groupby(level=0, axis=1).sum().copy()
            )
            load = (
                load.rename(columns=dfs['hierarchy'][level])
                .groupby(level=0, axis=1).sum().copy()
            )
        for agg in ['max','sum','mean']:
            if (metric,agg) not in units:
                continue
            savename = f"dropped_load-map-{metric}_{agg}-{level}-{sw['t']}.png"

            dfplot = dfba.copy()
            if level not in ['r','rb','ba']:
                dfplot[level] = dfs['hierarchy'][level]
                dfplot = dfplot.dissolve(level)
                dfplot['centroid_x'] = dfplot.geometry.centroid.x
                dfplot['centroid_y'] = dfplot.geometry.centroid.y
            if metric == 'EUE':
                dfplot['val'] = dropped.agg(agg)
            elif (metric == 'NEUE') and (agg == 'max'):
                dfplot['val'] = (dropped / load).agg(agg)
            elif (metric == 'NEUE'):
                dfplot['val'] = dropped.agg(agg) / load.agg(agg)
            dfplot.val = (dfplot.val * units[metric,agg][1]).replace(0, np.nan)

            plt.close()
            f,ax = plt.subplots(figsize=(8,8/1.45), dpi=150)
            ### Background
            dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.2)
            ### Data
            dfplot.plot(ax=ax, column='val', cmap=cmocean.cm.rain)
            for r, row in dfplot.iterrows():
                if row.val > 0:
                    ax.annotate(
                        f'{row.val:,.0f} {units[metric,agg][0]}',
                        (row.centroid_x, row.centroid_y),
                        color='r', ha='center', va='top', fontsize=6, weight='bold')
            ### Formatting
            if level in ['r','rb','ba']:
                for r, row in dfba.iterrows():
                    ax.annotate(r, (row.centroid_x, row.centroid_y),
                                ha='center', va='bottom', fontsize=6, color='C7')
            ax.axis('off')
            if savefig:
                plt.savefig(os.path.join(sw['savepath'],savename))
            if interactive:
                plt.show()
            plt.close()


def plot_pras_ICAP(sw, dfs):
    """
    Plot the available capacity used in PRAS without any outages
    """
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    ### Collect the PRAS system capacities
    cap = pd.concat([
        dfs['pras_system']['gencap'].groupby(axis=1, level=0).sum(),
        dfs['pras_system']['storcap'].groupby(axis=1, level=0).sum(),
        dfs['pras_system']['genstorcap'].groupby(axis=1, level=0).sum(),
    ], axis=1)
    ## Drop any empties
    cap = cap.replace(0,np.nan).dropna(axis=1, how='all').fillna(0).astype(int)
    ## Get the colors
    tech_map = dfs['tech_map']
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    tech_style = dfs['tech_style']
    ## Aggregate by type
    cap.columns = cap.columns.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).str.lower()
    cap.columns = (
        cap.columns
        .map(lambda x: [i for i in tech_map.index if x.startswith(i)][0])
        .map(lambda x: tech_map.get(x,x))
    )
    cap.columns
    cap = cap.groupby(axis=1, level=0).sum()
    order = [c for c in tech_style.index if c in cap]
    cap = cap[order]
    if cap.shape[1] != len(order):
        raise Exception(f"missing colors: {cap.columns}, {tech_style}")
    ## Cumulate for plot
    cumcap = cap.cumsum(axis=1)[order[::-1]]
    load = dfs['pras_system']['load'].sum(axis=1)

    ### Plot it
    for y in sw.resource_adequacy_years_list:
        savename = f"PRAS-ICAP-w{y}-{sw['t']}.png"
        plt.close()
        f,ax = plots.plotyearbymonth(
            load.loc[str(y)],
            colors=['k'], style='line', lwforline=1,
        )
        plots.plotyearbymonth(
            cumcap.loc[str(y)], colors=[tech_style[c] for c in cumcap],
            f=f, ax=ax,
        )
        ## Legend
        leg = ax[0].legend(
            loc='upper left', bbox_to_anchor=(1,1.25),
            fontsize=11, frameon=False, ncol=1,
            columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        )
        leg.set_title(f'ICAP {y}', prop={'size':'large'})
        ## Save it
        if savefig:
            plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive:
            plt.show()
        plt.close()


def plot_augur_pras_capacity(sw, dfs):
    """
    Plot the nameplate capacity from Augur and PRAS to check consistency
    """
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    savename = f"PRAS-Augur-capacity-{sw['t']}.png"
    ### Get the colors
    tech_style = dfs['tech_style']
    ### Collect the PRAS system capacities
    cap = {}
    cap['pras'] = pd.concat([
        dfs['pras_system']['gencap'],
        dfs['pras_system']['storcap'],
        dfs['pras_system']['genstorcap'],
    ], axis=1) / 1e3
    ## Drop any empties
    cap['pras'] = cap['pras'].replace(0,np.nan).dropna(axis=1, how='all').fillna(0)
    ## Aggregate by type
    cap['pras'] = (
        group_techs(cap['pras'], dfs, technamecol='wide')
        .groupby(axis=1, level=[1,0]).sum().max().rename('MW')
    )

    ### Collect the Augur capacities
    cap['augur'] = dfs['max_cap'].groupby(['i','r'], as_index=False).MW.sum()
    ## Convert from s to p regions
    cap['augur'].r = cap['augur'].r
    ## Aggregate by type
    cap['augur'] = (
        group_techs(cap['augur'], dfs, technamecol='i')
        .replace({'i':{'hydro_new':'hydro', 'hydro_exist':'hydro'}})
        .groupby(['r','i']).MW.sum() / 1e3
    )

    ### Drop VRE since its capacity is handled differently
    for datum in cap:
        cap[datum] = (
            cap[datum].loc[
                ~cap[datum].index.get_level_values('i').isin(
                    dfs['vre_gen_usa'].columns.tolist())
            ]
        )

    ### Get coordinates
    zones = dfs['hierarchy'].index
    ncols = int(np.around(np.sqrt(len(zones)) * 1.618, 0))
    nrows = len(zones) // ncols + int(bool(len(zones) % ncols))
    coords = dict(zip(zones, [(row,col) for row in range(nrows) for col in range(ncols)]))

    ### Plot the capacities
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(1.2*ncols, 1.2*nrows), sharex=True,
        gridspec_kw={'wspace':0.6, 'hspace':0.5}
    )
    alltechs = set()
    for r in zones:
        df = pd.concat({'A':cap['augur'].get(r,pd.Series()), 'P':cap['pras'].get(r,pd.Series())}, axis=1).T
        order = [c for c in tech_style.index if c in df]
        missing = [c for c in df if c not in order]
        if len(missing):
            print(f'WARNING: Missing colors for these techs: {missing}')
        df = df[order].copy()
        alltechs.update(df.columns.tolist())
        plots.stackbar(df=df, ax=ax[coords[r]], colors=tech_style, net=False, width=0.8)
        ### Formatting
        ax[coords[r]].set_title(r)
        ax[coords[r]].set_xticks([0,1])
        ax[coords[r]].set_xticklabels(['A','P'])
        ### Legend
        if r == zones[-1]:
            handles = [
                mpl.patches.Patch(facecolor=tech_style[i], edgecolor='none', label=i)
                for i in [j for j in tech_style.index if j in alltechs]
            ][::-1]
            ax[coords[r]].legend(
                handles=handles, loc='center left', bbox_to_anchor=(1,0.5),
                frameon=False, columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
                ncol=len(alltechs)//3,
            )
    ### Formatting
    plots.trim_subplots(ax=ax, nrows=nrows, ncols=ncols, nsubplots=len(zones))
    ax[-1, 0].set_ylabel('Nameplate capacity [GW]', y=0, ha='left')
    plots.despine(ax)
    ## Save it
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def plot_pras_ICAP_regional(sw, dfs, numdays=5):
    """
    Plot the available capacity used in PRAS without any outages
    """
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    ### Get the peak dropped-load periods
    dropped = dfs['pras']['USA_EUE'].copy()
    dropped = dropped.groupby(
        [dropped.index.year, dropped.index.month, dropped.index.day]
    ).sum().nlargest(numdays).replace(0,np.nan).dropna()

    ### Collect the PRAS system capacities
    load = dfs['pras_system']['load'] / 1e3
    cap = pd.concat([
        dfs['pras_system']['gencap'],
        dfs['pras_system']['storcap'],
        dfs['pras_system']['genstorcap'],
    ], axis=1) / 1e3
    ## Drop any empties
    cap = cap.replace(0,np.nan).dropna(axis=1, how='all').fillna(0)
    ## Get the colors
    tech_map = dfs['tech_map']
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    tech_style = dfs['tech_style']
    ## Aggregate by type
    def renamer(x):
        out = (x if x[0].startswith('battery')
               else (x[0].strip('_01234567890*').lower(), *x[1:]))
        return out
    cap.columns = cap.columns.map(renamer)
    cap.columns = (
        cap.columns
        .map(lambda x: ([i for i in tech_map.index if x[0].startswith(i)][0], *x[1:]))
        .map(lambda x: (tech_map.get(x[0],x[0]), *x[1:]))
    )
    cap = cap.groupby(axis=1, level=[1,0]).sum()

    ### Get coordinates
    zones = dfs['hierarchy'].index
    ncols = int(np.around(np.sqrt(len(zones)) * 1.618, 0))
    nrows = len(zones) // ncols + int(bool(len(zones) % ncols))
    coords = dict(zip(zones, [(row,col) for row in range(nrows) for col in range(ncols)]))

    ### Plot the highest-EUE days
    for day in range(len(dropped)):
        date = '{}-{:>02}-{:>02}'.format(*dropped.index[day])
        savename = f"PRAS-ICAP-{sw['t']}-{date.replace('-','')}.png"
        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(1.2*ncols, 1.2*nrows), sharex=True,
            gridspec_kw={'wspace':0.6, 'hspace':0.5}
        )
        for r in zones:
            df = cap.loc[date][r].copy()
            ### Cumulate for plot
            order = [c for c in tech_style.index if c in df]
            df = df[order]
            ### Plot it
            plots.stackbar(
                df=df, ax=ax[coords[r]], colors=tech_style, net=False, align='edge',
                width=pd.Timedelta('1H'),
            )
            ax[coords[r]].plot(
                load.loc[date].index, load.loc[date][r].values, c='k', lw=1,
                path_effects=[pe.withStroke(linewidth=1.7, foreground='w', alpha=0.8)],
            )
            ### Formatting
            ax[coords[r]].set_title(r)
        ### Formatting
        plots.trim_subplots(ax=ax, nrows=nrows, ncols=ncols, nsubplots=len(zones))
        ax[coords[zones[0]]].set_xlim(df.index[0], df.index[-1] + pd.Timedelta('1H'))
        ax[coords[zones[0]]].set_xticks([])
        ax[-1, 0].set_xlabel(date, x=0, ha='left', labelpad=10)
        ax[-1, 0].set_ylabel('ICAP [GW]', y=0, ha='left')
        plots.despine(ax)
        ## Save it
        if savefig:
            plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive:
            plt.show()
        plt.close()


def plot_pras_unitsize_distribution(sw, dfs):
    """
    Distribution of PRAS unit sizes by tech
    """
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    savename = f"PRAS-unitcap-{sw['t']}.png"
    cap = (
        pd.concat([
            dfs['pras_system']['gencap'],
            dfs['pras_system']['storcap'],
            dfs['pras_system']['genstorcap'],
        ], axis=1)
        .max().rename('MW').reset_index()
    )
    ## Get the colors
    tech_map = dfs['tech_map'].copy()
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    tech_style = dfs['tech_style'].copy()
    toadd = tech_style.loc[tech_style.index.str.endswith('_mod')]
    toadd.index = toadd.index.str.replace('_mod','')
    tech_style = pd.concat([tech_style,toadd])
    ## Aggregate by type
    cap.i = cap.i.map(
        lambda x: x if x.startswith('battery') else (x.strip('_01234567890*').lower()))
    cap.i = (
        cap.i
        .map(lambda x: tech_map.get(x,x))
        .str.replace('_upgrade','')
        .str.replace('_mod','')
    )

    techs = cap.i.unique()
    nondisaggtechs = (
        dfs['vre_gen_usa'].columns.tolist()
        + ['hydro_exist']
        + [i for i in techs if i.startswith('battery')]
        + [i for i in techs if (('canada' in i.lower()) or ('can-imports' in i.lower()))]
    )
    order = [i for i in tech_style.index if i in techs]
    others = [i for i in techs if ((i not in order) and (i not in nondisaggtechs))]
    # for i in others:
    #     tech_style[i] = 'k'

    ylabel = {0: {'scale':1, 'units':'MW'}, 1: {'scale':1e-3, 'units':'GW'}}
    plt.close()
    f,ax = plt.subplots(1, 2, figsize=(7,3.75), gridspec_kw={'wspace':0.4})
    for i in (order+others)[::-1]:
        df = cap.loc[cap.i==i].copy()
        col = 1 if i in nondisaggtechs else 0
        df.MW = df.MW * ylabel[col]['scale']
        ax[col].plot(
            range(len(df)), df.MW.sort_values().values,
            c=tech_style.get(i,'k'), label=i)
        ax[col].annotate(
            f' {i}', (len(df)-1, df.MW.max()),
            fontsize=10, color=tech_style.get(i,'k'),
            path_effects=[pe.withStroke(linewidth=1.5, foreground='w', alpha=0.7)],
        )
    for col in range(2):
        ax[col].set_ylabel(f"Unit size [{ylabel[col]['units']}]")
        ax[col].set_xlabel('Number of units')
        ax[col].set_xlim(0)
        ax[col].set_ylim(0)
        ax[col].legend(
            ncol=1, columnspacing=0.5, frameon=False,
            handletextpad=0.3, handlelength=0.7,
            loc='upper center', bbox_to_anchor=(0.5,-0.2))
    ax[0].set_title('Disaggregated techs')
    ax[1].set_title('Aggregated techs (PRAS FOR=0)')
    plots.despine(ax)
    ## Save it
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def plot_pras_unitnumber(sw, dfs, level='country'):
    """Number of PRAS units by technology, grouped by region level"""
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    savename = f"PRAS-unitnumber-{level}-{sw['t']}.png"
    cap = (
        pd.concat([
            dfs['pras_system']['gencap'],
            dfs['pras_system']['storcap'],
            dfs['pras_system']['genstorcap'],
        ], axis=1)
        .max().rename('MW').reset_index()
    )
    ## Get the colors
    tech_map = dfs['tech_map'].copy()
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    tech_style = dfs['tech_style'].copy()
    toadd = tech_style.loc[tech_style.index.str.endswith('_mod')]
    toadd.index = toadd.index.str.replace('_mod','')
    tech_style = pd.concat([tech_style,toadd])
    ## Aggregate by type
    cap.i = cap.i.map(
        lambda x: x if x.startswith('battery') else (x.strip('_01234567890*').lower()))
    cap.i = (
        cap.i
        .map(lambda x: tech_map.get(x,x))
        .str.replace('_upgrade','')
        .str.replace('_mod','')
    )

    order = cap.i.value_counts().index
    colors = order.map(lambda x: tech_style.get(x, mpl.colors.to_hex('k')))

    ## Group by hierarchy level
    regions = sorted((
        dfs['hierarchy'].index if level == 'r' else dfs['hierarchy'][level]
    ).unique())
    nrows, ncols, coords = plots.get_coordinates(regions)

    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(max(ncols*2, 5), max(nrows*2, 3.75)),
        sharex=True, sharey=True,
    )
    for region in regions:
        _ax = (ax if nrows == ncols == 1 else ax[coords[region]])
        rs = (
            [region] if level == 'r'
            else dfs['hierarchy'].loc[dfs['hierarchy'][level]==region].index
        )
        df = cap.loc[cap.r.isin(rs)].i.value_counts().reindex(order).fillna(0)
        _ax.bar(
            df.index, df.values, color=colors,
        )
        _ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
        _ax.set_xticks(range(len(order)))
        _ax.set_xticklabels(order, rotation=90, fontsize=9)
        _ax.set_xlim(-0.5, len(order)-0.5)
        _ax.annotate(
            region.replace('_','\n') + f'\n{df.sum():.0f}',
            (0.95,0.95), xycoords='axes fraction', ha='right', va='top',
            fontsize='large', weight='bold',
        )
    labelax = (
        ax if (nrows == ncols == 1)
        else ax[0] if ((nrows == 1) or (ncols == 1))
        else ax[-1,0]
    )
    labelax.set_ylabel('Number of units', y=0, ha='left')
    plots.despine(ax)
    plots.trim_subplots(ax, nrows, ncols, len(regions))
    ## Save it
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def plot_pras_load_units(sw, dfs):
    """Histogram of net load and sorted unit sizes by model zone"""
    savename = f"PRAS-load_hist-units-{sw['t']}.png"
    ### Get inputs
    ## Capacity
    cap = (
        pd.concat([
            dfs['pras_system']['gencap'],
            dfs['pras_system']['storcap'],
            dfs['pras_system']['genstorcap'],
        ], axis=1)
        .max().rename('MW').reset_index()
    )
    ## Net demand
    vre_gen = dfs['vre_gen'].copy()
    vre_gen.columns = pd.MultiIndex.from_tuples(
        vre_gen.columns.map(lambda x: tuple(x.split('|'))),
        names=['i','r'],
    )
    net_demand = (dfs['pras_system']['load'] - vre_gen.groupby('r', axis=1).sum()) / 1e3
    ## Remaining unit capacity
    units = group_techs(
        cap.loc[
            ~cap.i.isin(vre_gen.columns.get_level_values('i').unique())
            & (cap.MW > 0)
        ],
        dfs
    )
    ## Get the colors
    tech_map = dfs['tech_map'].copy()
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    tech_style = dfs['tech_style'].copy()
    toadd = tech_style.loc[tech_style.index.str.endswith('_mod')]
    toadd.index = toadd.index.str.replace('_mod','')
    tech_style = pd.concat([tech_style,toadd])

    ## Only keep the 10 regions with highest neue
    regions = (
        dfs['pras'][[c for c in dfs['pras'] if c.endswith('_EUE') and not c.startswith('USA')]]
        .sum()
        .nlargest(10)
    ).index.map(lambda x: x[:-len('_EUE')])

    ## Maps
    dfmap = reeds.io.get_dfmap(sw['casedir'])

    ### Plot it
    ncols = len(regions)
    nrows = 3
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(ncols*1.25, 6),
        gridspec_kw={'height_ratios':[1,1,3], 'hspace':0.3},
    )
    for col, r in enumerate(regions):
        ## Net load
        ax[1,col].hist(net_demand[r], bins=101, color='C3')
        ## Units
        df = units.loc[units.r==r].sort_values('MW')
        df['GW'] = df.MW / 1e3
        df['GW_cumsum'] = df.GW.cumsum()
        df['left'] = df['GW_cumsum'].shift(1).fillna(0)
        ## Do it twice to get darker lines around the edges
        ax[-1,col].bar(
            x=df['left'],
            height=df['MW'],
            width=df['GW'],
            align='edge',
            color=df.i.map(lambda x: tech_style.get(x,'#000000')),
            alpha=0.7,
        )
        ax[-1,col].bar(
            x=df['left'],
            height=df['MW'],
            width=df['GW'],
            align='edge',
            color='none',
            edgecolor='k', lw=0.15,
        )
        ## Peak
        peak = net_demand[r].max()
        for row in [1, 2]:
            ax[row,col].axvline(peak, c='C3', lw=0.75, ls=':')
        ## Formatting
        reeds.plots.despine(ax[1,col], left=False)
        ax[1,col].set_yticks([])
        ax[1,col].set_xticklabels([])
        ## Ignore battery and hydro for the y limit since they're not disaggregated
        ax[-1,col].set_ylim(0, units.loc[~units.i.str.startswith(('battery','hydro')), 'MW'].max())
        if col > 0:
            ax[-1,col].set_yticklabels([])
        ## Share x axis for histograms
        xmax = max(ax[1,col].get_xlim()[1], ax[2,col].get_xlim()[1])
        for row in [1, 2]:
            ax[row,col].set_xlim(0, xmax)
        ## Maps
        dfmap['r'].loc[[r]].plot(ax=ax[0,col], facecolor='k', edgecolor='none', zorder=3)
        bounds = dfmap['r'].loc[[r]].bounds.squeeze()
        ax[0,col].set_xlim(bounds.minx-50e3, bounds.maxx+50e3)
        ax[0,col].set_ylim(bounds.miny-50e3, bounds.maxy+50e3)
        dfmap['st'].plot(ax=ax[0,col], facecolor='none', edgecolor='k', lw=0.5, zorder=2)
        dfmap['r'].plot(ax=ax[0,col], facecolor='0.9', edgecolor='w', lw=0.5, zorder=1)
        ax[0,col].axis('off')
        ax[1,col].set_title(r)
    ## Formatting
    ax[-1,0].set_xlabel('GW')
    ax[1,0].set_xlabel('Net load [GW]', x=0, ha='left', color='C3')
    ax[-1,0].set_ylabel('Unit size [MW]')
    ax[-1,0].set_xlabel('Installed capacity [GW]', x=0, ha='left')
    reeds.plots.despine(ax)
    ## Save it
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def plot_pras_augur_load(sw, dfs):
    """PRAS load against Augur load"""
    dfpras = dfs['pras_system']['load'].sum(axis=1).rename('PRAS')
    dfaugur = dfs['load_r'].set_axis(dfpras.index).sum(axis=1).rename('Augur')
    years = dfpras.index.year.unique()
    linecolors = {'Augur':'C0', 'PRAS':'C3'}
    for year in years:
        savename = f"demand_USA-Augur-PRAS-w{year}-{sw['t']}.png"
        plt.close()
        f,ax = plots.plotyearbymonth(
            dfaugur.loc[str(year)], style='line', colors=linecolors['Augur'])
        plots.plotyearbymonth(
            dfpras.loc[str(year)], style='line', colors=linecolors['PRAS'], f=f, ax=ax)
        ## Legend
        handles = [
            mpl.lines.Line2D([], [], color=linecolors[i], label=i, lw=2)
            for i in linecolors
        ]
        ax[0].legend(
            handles=handles, ncol=2, frameon=False,
            loc='lower right', bbox_to_anchor=(1,0.5),
            handlelength=1.0, handletextpad=0.3, labelspacing=0.5, columnspacing=0.5,
        )
        ax[0].annotate(year, (0.85, 1), xycoords='axes fraction', ha='right')
        ## Save it
        if savefig:
            plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive:
            plt.show()
        plt.close()


def plot_pras_load(sw, dfs):
    """PRAS load over all weather years"""
    dfpras = dfs['pras_system']['load'].sum(axis=1).rename('PRAS')
    years = dfpras.index.year.unique()
    linecolors = plots.rainbowmapper(years, categorical=True)
    savename = f"demand_USA-PRAS-{sw['t']}.png"
    plt.close()
    f,ax = plots.plotyearbymonth(
        dfpras.loc[str(years[0])], style='line', colors=linecolors[years[0]])
    for year in years[1:]:
        plots.plotyearbymonth(
            dfpras.loc[str(year)], style='line', colors=linecolors[year], f=f, ax=ax)
    ## Legend
    handles = [
        mpl.lines.Line2D([], [], color=linecolors[y], label=y, lw=2)
        for y in years
    ]
    ax[0].legend(
        handles=handles, ncol=len(years), frameon=False,
        loc='lower right', bbox_to_anchor=(1,0.5),
        handlelength=1.0, handletextpad=0.3, labelspacing=0.5, columnspacing=0.5,
    )
    ## Save it
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def map_pras_failure_rate(sw, dfs, aggfunc='mean', repair=False):
    """
    Failure rates from PRAS, indicating the probability that an online unit will fail
    (which is different from the outage rate, which gives the average fraction of units
    that are on outage over time, including mean time to repair)."""
    dfmap = reeds.io.get_dfmap(sw['casedir'])
    dfzones = dfmap['r']

    failrate = (
        dfs['pras_system']['genfailrate']
        ## Only keep one copy of each (i,r)
        .T.reset_index().drop_duplicates().set_index(['i','r']).T
        * 100
    )
    failrate.index = dfs['pras_system']['genfailrate'].index

    failsum = failrate.sum()
    plottechs = failsum.loc[failsum != 0].index.get_level_values('i').unique()

    for tech in plottechs:
        savename = f"hourly_failure_rate-year,month-{aggfunc}-{tech.replace('-','')}-{sw['t']}"
        plt.close()
        f, ax = plots.map_years_months(
            dfzones=dfzones, dfdata=failrate[tech],
            title=f"Monthly {aggfunc}\nhourly failure rate,\n{tech} [%]",
        )
        ## Save it
        if savefig:
            plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive:
            plt.show()
        plt.close()

    if repair:
        repairrate = (
            dfs['pras_system']['genrepairrate']
            .T.reset_index().drop_duplicates().set_index(['i','r']).T
            * 100
        )
        repairrate.index = dfs['pras_system']['genrepairrate'].index
        for tech in plottechs:
            savename = f"hourly_repair_rate-year,month-{aggfunc}-{tech.replace('-','')}-{sw['t']}"
            plt.close()
            f, ax = plots.map_years_months(
                dfzones=dfzones, dfdata=repairrate[tech],
                title=f"Monthly {aggfunc}\nhourly repair rate,\n{tech} [%]",
            )
            ## Save it
            if savefig:
                plt.savefig(os.path.join(sw['savepath'],savename))
            if interactive:
                plt.show()
            plt.close()


def plot_cc_mar(sw, dfs):
    """
    Marginal capacity credit
    """
    param = 'cc_mar'
    savename = f"{param}-{sw['t']}.png"

    if not int(sw['GSw_PRM_CapCredit']):
        raise KeyError('No capacity credit values to plot')
    cc_results = gdxpds.to_dataframes(os.path.join(
        sw['casedir'],'ReEDS_Augur','augur_data',
        'ReEDS_Augur_{}.gdx'.format(sw['t'])
    ))

    dfplot = cc_results[param].drop('t',axis=1).copy()
    dfplot['tech'] = dfplot.i.map(lambda x: x.split('_')[0])
    techs = sorted(dfplot.tech.unique())
    numcols = len(techs)
    bootstrap = 5
    squeeze = 0.7
    ### Use seasons appropriate to resolution
    ccseasons = ['cold', 'hot']
    histcolor = ['C0', 'C1']
    xticklabels = ccseasons

    plt.close()
    f,ax = plt.subplots(
        1, numcols, figsize=(len(techs)*1.2, 3.75), sharex=True, sharey=True)
    for row, tech in enumerate(techs):
        df = dfplot.loc[(dfplot.tech==tech)].copy()
        ### Each observation in the histogram is a (i,r) pair
        df['i_r'] = df.i + '_' + df.r
        df = df.pivot(columns='ccseason',values='Value',index='i_r')[ccseasons]

        plots.plotquarthist(
            ax[row], df, histcolor=histcolor,
            bootstrap=bootstrap, density=True, squeeze=squeeze,
            pad=0.03,
        )

        ### Formatting
        ax[row].set_title(tech)
        ax[row].yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1))
        ax[row].yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.2))
        ax[row].set_ylim(0,1)
        ax[row].set_xticklabels(xticklabels, rotation=90)

    ax[0].set_ylabel(
        f'{sw.t} {param} [fraction]', weight='bold', fontsize='x-large')

    plots.despine(ax)
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def plot_netloadhours_timeseries(sw, dfs):
    """
    Peak net load hours by ccreg
    """
    savename = f"netloadhours-timeseries-{sw['t']}.png"

    ### Plot it
    years = sw.resource_adequacy_years_list
    ccregs = sorted(dfs['dfpeak'].columns)
    plt.close()
    f,ax = plt.subplots(len(years),1,sharex=False,sharey=True,figsize=(12,6))
    for row, year in enumerate(years):
        df = dfs['dfpeak'].loc[str(year)].cumsum(axis=1)[ccregs[::-1]]
        df.plot.area(
            ax=ax[row], color=dfs['peakcolors'], stacked=False, alpha=1,
            legend=False,
        )
        ax[row].annotate(
            year,(0.005,0.95),xycoords='axes fraction',ha='left',va='top',
            weight='bold',fontsize='large')
        if row < (len(years) - 1):
            ax[row].set_xticklabels([])
    handles, labels = ax[0].get_legend_handles_labels()
    ax[0].legend(
        handles[::-1], labels[::-1],
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        loc='upper left', bbox_to_anchor=(1,1), frameon=False, title='ccreg',
    )
    ax[3].set_ylabel('Net load peak instances [#]')
    # ax[-1].xaxis.set_major_locator(mpl.dates.MonthLocator())
    # ax[-1].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    plots.despine(ax)
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def plot_netloadhours_histogram(sw, dfs):
    """
    histograms of peak net load occurrence
    """
    savename = f"netloadhours-histogram-{sw['t']}.png"

    ### Plot it
    years = sw.resource_adequacy_years_list
    ccregs = sorted(dfs['dfpeak'].columns)
    plt.close()
    f,ax = plt.subplots(1,3,figsize=(12,3.75))
    ### hour
    dfs['dfpeak'].groupby(dfs['dfpeak'].index.hour).sum()[ccregs[::-1]].plot.bar(
        ax=ax[0], color=dfs['peakcolors'], stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[0].set_xlabel('Hour [CST]')
    ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(4))
    ax[0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))
    ax[0].tick_params(labelrotation=0)
    ### Month
    dfs['dfpeak'].groupby(dfs['dfpeak'].index.month).sum()[ccregs[::-1]].plot.bar(
        ax=ax[1], color=dfs['peakcolors'], stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[1].set_xlabel('Month')
    ax[1].tick_params(labelrotation=0)
    ### Year
    dfs['dfpeak'].groupby(dfs['dfpeak'].index.year).sum()[ccregs[::-1]].plot.bar(
        ax=ax[2], color=dfs['peakcolors'], stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[2].set_xlabel('Year')
    ax[2].set_xticks(range(len(years)))
    ax[2].set_xticklabels(
        years,
        rotation=35, ha='right', rotation_mode='anchor')
    # ax[2].tick_params(labelrotation=45)
    ### Formatting
    handles, labels = ax[2].get_legend_handles_labels()
    ax[2].legend(
        handles[::-1], labels[::-1],
        loc='center left', bbox_to_anchor=(1,0.5), frameon=False,
        title=sw['capcredit_hierarchy_level'],
        ncol=1, columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    ax[0].set_ylabel('Net peak load instances [#]')
    plots.despine(ax)
    if savefig:
        plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive:
        plt.show()
    plt.close()


def plot_stressors(sw, dfs):
    """
    Map demand/CF/FOR (organized differently to allow use outside of Augur)
    """
    for iteration in range(sw['iteration']):
        plot_generator = reeds.reedsplots.map_stressors(
            case=sw['casedir'], t=sw['t'], iteration=iteration,
            seed=(True if t == int(sw['endyear']) else False),
        )
        while True:
            try:
                f, ax, df, plotlabel = next(plot_generator)
                savename = (
                    f"stress{t}i{iteration}-"
                    + plotlabel.split(':')[0].replace('-','')
                )
                if savefig:
                    plt.savefig(os.path.join(sw['savepath'], f'{savename}.png'))
                if interactive:
                    plt.show()
            except StopIteration:
                break


#%%### Main function
def main(sw, debug=False):
    """
    debug: Make more plots for debugging if set to True
    """
    #%% Get the inputs
    dfs = get_inputs(sw)

    #%% Make the plots
    if (not int(sw.GSw_PRM_CapCredit)) or (int(sw.pras == 2)):
        try:
            plot_pras_ICAP_regional(sw, dfs)
        except Exception:
            print('plot_pras_ICAP_regional() failed:', traceback.format_exc())

        try:
            plot_pras_load_units(sw, dfs)
        except Exception:
            print('plot_pras_load_units() failed:', traceback.format_exc())

        try:
            plot_pras_unitsize_distribution(sw, dfs)
        except Exception:
            print('plot_pras_unitsize_distribution() failed:', traceback.format_exc())

        try:
            for level in ['country', 'transgrp', 'r']:
                plot_pras_unitnumber(sw, dfs, level)
        except Exception:
            print('plot_pras_unitnumber() failed:', traceback.format_exc())

        try:
            plot_augur_pras_capacity(sw, dfs)
        except Exception:
            print('plot_augur_pras_capacity() failed:', traceback.format_exc())

        try:
            plot_pras_load(sw, dfs)
        except Exception:
            print('plot_pras_load() failed:', traceback.format_exc())

        try:
            plot_stressors(sw, dfs)
        except Exception:
            print('plot_stressors() failed:', traceback.format_exc())

    try:
        plot_dropped_load_timeseries_full(sw, dfs)
    except Exception:
        print('plot_dropped_load_timeseries_full() failed:', traceback.format_exc())

    try:
        plot_dropped_load_duration(sw, dfs)
    except Exception:
        print('plot_dropped_load_duration() failed:', traceback.format_exc())

    try:
        for level in ['r', 'transgrp']:
            map_dropped_load(sw, dfs, level=level)
    except Exception:
        print('map_dropped_load() failed:', traceback.format_exc())

    if int(sw['GSw_PRM_CapCredit']):
        try:
            plot_cc_mar(sw, dfs)
        except Exception:
            print('plot_cc_mar() failed:', traceback.format_exc())

    try:
        plot_netloadhours_timeseries(sw, dfs)
    except Exception:
        print('plot_netloadhours_timeseries() failed:', traceback.format_exc())

    try:
        plot_netloadhours_histogram(sw, dfs)
    except Exception:
        print('plot_netloadhours_histogram() failed:', traceback.format_exc())

    if debug:
        try:
            plot_pras_augur_load(sw, dfs)
        except Exception:
            print('plot_pras_augur_load() failed:', traceback.format_exc())

        try:
            plot_pras_ICAP(sw, dfs)
        except Exception:
            print('plot_pras_ICAP() failed:', traceback.format_exc())

        try:
            plot_netload_profile(sw, dfs)
        except Exception:
            print('plot_netload_profile() failed:', traceback.format_exc())

        try:
            map_pras_failure_rate(sw, dfs)
        except Exception:
            print('map_pras_failure_rate() failed:', traceback.format_exc())


#%%### PROCEDURE
if __name__ == '__main__':
    #%%### ARGUMENT INPUTS
    import argparse
    parser = argparse.ArgumentParser(
        description='Create the necessary 8760 and capacity factor data for hourly resolution')
    parser.add_argument('--reeds_path', help='ReEDS-2.0 directory')
    parser.add_argument('--casedir', help='ReEDS-2.0/runs/{case} directory')
    parser.add_argument('--t', type=int, default=2050, help='solve year to plot')
    parser.add_argument('--iteration', '-i', type=int, default=-1,
                        help='iteration to plot (default of -1 means latest iteration)')
    parser.add_argument('--debug', '-d', action='store_true', help='Make more plots')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    casedir = args.casedir
    t = args.t
    iteration = args.iteration
    debug = args.debug

    # #%%### Inputs for debugging
    # reeds_path = reeds.io.reeds_path
    # casedir = os.path.join(reeds_path, 'runs', 'v20251111_15M0_Pacific')
    # t = 2026
    # interactive = True
    # iteration = 0
    # debug = True

    #%%### INPUTS
    ### Switches
    sw = reeds.io.get_switches(casedir)
    sw['t'] = t
    ## Debugging
    # sw['reeds_path'] = reeds_path
    # sw['casedir'] = casedir

    ### Run for the latest iteration
    if iteration < 0:
        sw['iteration'] = int(
            os.path.splitext(
                sorted(glob(os.path.join(sw.casedir,'lstfiles',f'*{sw.t}i*.lst')))[-1]
            )[0]
            .split(f'{sw.t}i')[-1]
        )
    else:
        sw['iteration'] = iteration

    ### Make the plots
    print('plotting intermediate Augur results...')
    try:
        main(sw, debug)
    except Exception as _err:
        print('diagnostic_plots.py failed with the following exception:')
        print(traceback.format_exc())

    ### Remove intermediate csv files to save drive space
    if (not int(sw['keep_augur_files'])) and (not int(sw['debug'])):
        delete_temporary_files(sw)
