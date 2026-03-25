#%% IMPORTS
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import os, sys, site, importlib
import traceback

import geopandas as gpd
os.environ['PROJ_NETWORK'] = 'OFF'

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
site.addsitedir(os.path.join(reeds_path,'postprocessing'))
site.addsitedir(os.path.join(reeds_path,'input_processing'))
import plots
import reedsplots as rplots
from ticker import makelog
plots.plotparams()

##########
#%% INPUTS
## Note that if your case builds lots of transmission, wscale might
## need to be reduced to avoid too much overlap in the plotted routes
wscale_straight = 0.0004
wscale_routes = 1.5
wscale_h2 = 3
routes = False
## Note that if you change the CRS you'll probably need to change
## the position of the annotations
crs = 'ESRI:102008'
### For generation capacity map
cmap = plt.cm.gist_earth_r
# cmap = plt.cm.YlGnBu
# cmap = plt.cm.PuBuGn
ncols = 3
techs = [
    'Utility PV', 'Land-based wind', 'Offshore wind',
    'Nuclear', 'H2 turbine', 'Battery/PSH',
    'Fossil', 'Fossil+CCS', 'CO2 removal',
]
techmap = {
    **{f'upv_{i}':'Utility PV' for i in range(20)},
    **{f'dupv_{i}':'Utility PV' for i in range(20)},
    **{f'wind-ons_{i}':'Land-based wind' for i in range(20)},
    **{f'wind-ofs_{i}':'Offshore wind' for i in range(20)},
    **dict(zip(['nuclear','nuclear-smr'], ['Nuclear']*20)),
    **dict(zip(
        ['gas-cc_re-cc','gas-ct_re-ct','re-cc','re-ct',
         'gas-cc_h2-ct','gas-ct_h2-ct','h2-cc','h2-ct',],
        ['H2 turbine']*20)),
    **{f'battery_{i}':'Battery/PSH' for i in range(20)}, **{'pumped-hydro':'Battery/PSH'},
    **dict(zip(
        ['coal-igcc', 'coaloldscr', 'coalolduns', 'gas-cc', 'gas-ct', 'coal-new', 'o-g-s',],
        ['Fossil']*20)),
    **dict(zip(
        ['gas-cc_gas-cc-ccs_mod','gas-cc_gas-cc-ccs_max','gas-cc-ccs_mod','gas-cc-ccs_max',
         'gas-cc_gas-cc-ccs_mod','coal-igcc_coal-ccs_mod','coal-new_coal-ccs_mod',
        'coaloldscr_coal-ccs_mod','coalolduns_coal-ccs_mod','cofirenew_coal-ccs_mod',
        'cofireold_coal-ccs_mod','gas-cc_gas-cc-ccs_max','coal-igcc_coal-ccs_max',
        'coal-new_coal-ccs_max','coaloldscr_coal-ccs_max','coalolduns_coal-ccs_max',
        'cofirenew_coal-ccs_max','cofireold_coal-ccs_max',],
        ['Fossil+CCS']*50)),
    **dict(zip(['dac','beccs_mod','beccs_max'],['CO2 removal']*20)),
}
### For VRE siting & transmission maps
transalpha = 0.25
transcolor = 'k'
ms = 1.15
gen_cmap = {
    'wind-ons':plt.cm.Blues,
    'upv':plt.cm.Reds,
    'wind-ofs':plt.cm.Purples,
}
### For testing
interactive = False
write = True

###################
#%% ARGUMENT INPUTS

import argparse
parser = argparse.ArgumentParser(description='transmission maps')
parser.add_argument('--casedir', '-c', type=str,
                    help='path to ReEDS run folder')
parser.add_argument('--year', '-y', type=int, default=2050,
                    help='year to plot')
parser.add_argument('--routes', '-r', action='store_true',
                    help='if True, show actual transmission routes')

args = parser.parse_args()
casedir = args.casedir
year = args.year
routes = args.routes

# #%% Inputs for testing
# casedir = os.path.expanduser('~/github/ReEDS-2.0/runs/v20230404_h2M2_EI_agg2')
# casedir = (
#     '/Volumes/ReEDS/FY22-NTP/Candidates/Archive/ReEDSruns/20230717/'
#     'v20230717_ntpsubfercH1_AC_DemMd_90by2035EP__core')
# year = 2050
# routes = False
# interactive = True
# importlib.reload(rplots)

#############
#%% PROCEDURE
#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(casedir,'gamslog.txt'))

#%% Make output directory
savepath = os.path.join(casedir,'outputs','maps')
os.makedirs(savepath, exist_ok=True)

#%% Load colors
trtypes = pd.read_csv(
    os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
    index_col='raw')['display']
colors = pd.read_csv(
    os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
    index_col='order')['color']
colors = colors.append(trtypes.map(colors))

#%% Load switches
sw = pd.read_csv(
    os.path.join(casedir, 'inputs_case', 'switches.csv'),
    header=None, index_col=0, squeeze=True)
years = pd.read_csv(
    os.path.join(casedir,'inputs_case','modeledyears.csv')
).columns.astype(int).values
yearstep = years[-1] - years[-2]
val_r = pd.read_csv(
    os.path.join(casedir, 'inputs_case', 'val_r.csv'), squeeze=True, header=None).tolist()

#%% Transmission line map with disaggregated transmission types
### Plot both total capacity (subtract_baseyear=None) and new (subtract_baseyear=2020)
for subtract_baseyear in [None, 2020]:
    try:
        plt.close()
        f,ax = rplots.plot_trans_onecase(
            case=casedir, pcalabel=False,
            routes=routes, simpletypes=None,
            wscale=(wscale_routes if routes else wscale_straight),
            yearlabel=False, year=year, alpha=1.0,
            subtract_baseyear=subtract_baseyear,
            label_line_capacity=1,
        )
        ### Add legend
        ax.annotate(
            'AC', (-1.75e6, -1.12e6), ha='center', va='top',
            weight='bold', fontsize=15, color=colors['ac'])
        ax.annotate(
            'LCC DC',
            (-1.75e6, -1.24e6), ha='center', va='top',
            weight='bold', fontsize=15, color=colors['lcc'])
        ax.annotate(
            'B2B',
            (-1.75e6, -1.36e6), ha='center', va='top',
            weight='bold', fontsize=15, color=colors['b2b'])
        ax.annotate(
            'VSC DC', (-1.75e6, -1.48e6), ha='center', va='top',
            weight='bold', fontsize=15, color=colors['vsc'])
        if write:
            end = f'-since{subtract_baseyear}' if subtract_baseyear else ''
            plt.savefig(
                os.path.join(savepath,f'map_translines_all-{year}{end}.png')
            )
        if interactive: plt.show()
        plt.close()
    except Exception as err:
        print('map_translines_all failed:')
        print(traceback.format_exc())


#%% Transmission utilization maps
try:
    for plottype in ['mean','max']:
        plt.close()
        f,ax = rplots.plot_transmission_utilization(
            case=casedir, year=year, plottype=plottype,
            wscale=wscale_straight, alpha=1.0, cmap=cmap,
        )
        if write:
            plt.savefig(os.path.join(savepath,f'map_transmission_utilization-{plottype}-{year}.png'))
        if interactive: plt.show()
        plt.close()
except Exception as err:
    print(f'map_transmission_utilization failed:')
    print(traceback.format_exc())

try:
    plt.close()
    f,ax = rplots.plot_average_flow(
        case=casedir, year=year, wscale=wscale_routes*8e3,
    )
    if write:
        plt.savefig(os.path.join(savepath,f'map_transmission_utilization-flowdirection-{year}.png'))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print(f'map_transmission_utilization-flowdirection failed:')
    print(traceback.format_exc())

try:
    plt.close()
    f,ax = rplots.plot_prmtrade(
        case=casedir, year=year, wscale=wscale_straight*8e3,
    )
    if write:
        plt.savefig(os.path.join(savepath,f'map_transmission_utilization-prmtrade-{year}.png'))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print(f'map_transmission_utilization-prmtrade failed:')
    print(traceback.format_exc())


#%% Macrogrid map
try:
    plt.close()
    f,ax = rplots.plot_trans_vsc(
        case=casedir, year=year, wscale=wscale_straight*1e3,
        alpha=1.0, miles=300,
    )
    if write:
        plt.savefig(os.path.join(savepath,'map_translines_vsc-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map_translines_vsc failed:')
    print(traceback.format_exc())


#%% Generation capacity maps
### Plot with tech-specific (vmax='each') and uniform (vmax='shared') color axis
for vmax in ['each', 'shared']:
    try:
        dfba = rplots.get_zonemap(casedir).loc[val_r]
        dfstates = dfba.dissolve('st')
        ### Case data
        dfcap = pd.read_csv(
            os.path.join(casedir,'outputs','cap.csv'),
            names=['i','r','t','MW'], header=0,
        )
        dfcap.i = dfcap.i.str.lower().map(lambda x: techmap.get(x,x))
        ### Get the vmax
        if vmax == 'shared':
            _vmax = dfcap.loc[
                dfcap.i.isin(techs) & (dfcap.t.astype(int)==year)
            ].groupby(['i','r']).MW.sum().max() / 1e3
        else:
            _vmax = None
        ### Arrange the subplots
        nrows = len(techs) // ncols
        coords = dict(zip(
            techs,
            [(row,col) for row in range(nrows) for col in range(ncols)]
        ))
        ### Plot it
        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(3*ncols,3*nrows),
            gridspec_kw={'wspace':0.0,'hspace':-0.05}, dpi=150)
        for tech in techs:
            dfval = dfcap.loc[
                (dfcap.i==tech)
                & (dfcap.t.astype(int)==year)
            ].groupby('r').MW.sum()
            dfplot = dfba.copy()
            dfplot['GW'] = (dfval / 1000).fillna(0)

            dfba.plot(
                ax=ax[coords[tech]],
                facecolor='none', edgecolor='k', lw=0.1, zorder=10000)
            dfstates.plot(
                ax=ax[coords[tech]],
                facecolor='none', edgecolor='k', lw=0.2, zorder=10001)
            dfplot.plot(
                ax=ax[coords[tech]], column='GW', cmap=cmap, legend=True,
                vmin=0, vmax=_vmax,
                legend_kwds={
                    'shrink':0.75, 'pad':0, 'orientation':'horizontal',
                    'label': '{} [GW]'.format(tech),
                }
            )
            ax[coords[tech]].axis('off')
        ax[0,0].set_title(
            '{} ({})'.format(os.path.basename(casedir), year),
            x=0.1, ha='left', va='top')
        if write:
            plt.savefig(os.path.join(savepath,f'map_capacity-{year}-{vmax}.png'))
        if interactive: plt.show()
        plt.close()
    except Exception as err:
        print('map_capacity failed:')
        print(traceback.format_exc())

#%% Site VRE capacity
try:
    plt.close()
    f,ax = rplots.plot_vresites_transmission(
        casedir, year, crs=crs, cm=gen_cmap,
        routes=False, wscale=wscale_straight, show_overlap=False,
        subtract_baseyear=None, show_transmission=False,
        alpha=transalpha, colors=transcolor, ms=ms,
    )
    if write:
        plt.savefig(os.path.join(savepath,'map_VREsites-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map_VREsites failed:')
    print(traceback.format_exc())


#%% Site VRE capacity overlaid with transmission
try:
    plt.close()
    f,ax = rplots.plot_vresites_transmission(
        casedir, year, crs=crs, cm=gen_cmap,
        routes=routes, show_overlap=False,
        wscale=wscale_routes,
        subtract_baseyear=None, show_transmission=True,
        alpha=transalpha, colors=transcolor, ms=ms,
    )
    if write:
        plt.savefig(os.path.join(savepath,'map_VREsites-translines-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map_VREsites-translines failed:')
    print(traceback.format_exc())

#%% Aggregated capacity, generation, and transmission by FERC region
try:
    for val in ['cap','gen']:
        plt.close()
        f,ax = rplots.map_agg(case=casedir, data=val, width_step=yearstep)
        if write:
            plt.savefig(os.path.join(savepath,'map_agg-FERC-{}-{}.png'.format(val,year)))
        if interactive: plt.show()
        plt.close()

    plt.close()
    f,ax = rplots.map_trans_agg(case=casedir, wscale=1000, drawzones=0.05)
    if write:
        plt.savefig(os.path.join(savepath,'map_agg-FERC-trans-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()

    plt.close()
    f,ax = rplots.map_agg(case=casedir, data='cap', width_step=yearstep, transmission=True)
    if write:
        plt.savefig(os.path.join(savepath,'map_agg-FERC-cap,trans-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map_agg failed:')
    print(traceback.format_exc())

#%% Dispatch plots
### Specify techs to include (None = all techs)
# techs = [
#     'nuclear',
#     'coal-ccs_mod','coal-ccs_mod_upgrade',
#     'gas-cc-ccs_mod','gas-cc-ccs_mod_upgrade',
# ]
techs = None
try:
    for v in [0,1]:
        plt.close()
        f,ax = rplots.plot_dispatch_yearbymonth(
            case=casedir, t=year, highlight_rep_periods=v, techs=techs)
        if write:
            endname = '' if not techs else f"-{','.join(techs)}"
            plt.savefig(
                os.path.join(savepath,f'plot_dispatch-yearbymonth-{v}-{year}{endname}.png')
            )
        if interactive: plt.show()
        plt.close()
except Exception as err:
    print('plot_dispatch-yearbymonth failed:')
    print(traceback.format_exc())

try:
    plt.close()
    f,ax = rplots.plot_dispatch_weightwidth(case=casedir)
    if write:
        plt.savefig(os.path.join(savepath,f'plot_dispatch-weightwidth-{sw.endyear}.png'))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('plot_dispatch-weightwidth failed:')
    print(traceback.format_exc())


#%% H2 pipelines and storage
try:
    plt.close()
    f,ax = rplots.map_h2_capacity(
        case=casedir, year=year, cmap=plt.cm.gist_earth_r, wscale_h2=0.2)
    if write:
        plt.savefig(os.path.join(savepath,f'map_h2_capacity-{sw.endyear}.png'))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map_h2_capacity failed:')
    print(traceback.format_exc())


#%% H2 pipeline utilization
try:
    if int(sw['GSw_H2_Transport']):
        for plottype in ['mean','max']:
            plt.close()
            f,ax = rplots.plot_transmission_utilization(
                case=casedir, year=year, plottype=plottype, network='h2',
                wscale=wscale_h2/1000, alpha=1.0, cmap=cmap, extent='modeled',
            )
            if write:
                plt.savefig(os.path.join(savepath,f'map_pipeline_utilization-{plottype}-{year}.png'))
            if interactive: plt.show()
            plt.close()
except Exception as err:
    print(f'map_pipeline_utilization failed:')
    print(traceback.format_exc())

try:
    if int(sw['GSw_H2_Transport']):
        plt.close()
        f,ax = rplots.plot_average_flow(
            case=casedir, year=year, network='h2',
            cm=plt.cm.magma_r, extent='modeled', wscale=wscale_h2*1e4,
        )
        if write:
            plt.savefig(os.path.join(savepath,f'map_pipeline_utilization-flowdirection-{year}.png'))
        if interactive: plt.show()
        plt.close()
except Exception as err:
    print(f'map_pipeline_utilization-flowdirection failed:')
    print(traceback.format_exc())


#%% H2 storage level, production, and usage
## Can set grid=0.25 to visually line up subplots
try:
    if int(sw['GSw_H2']):
        agglevel = ('r' if len(val_r) <= 20 else ('st' if len(val_r) <= 30 else 'transreg'))
        plt.close()
        f,ax = rplots.plot_h2_timeseries(
            case=casedir, year=year, agglevel=agglevel, grid=0)
        if write:
            plt.savefig(os.path.join(savepath,f'plot_h2_timeseries-{year}.png'))
        if interactive: plt.show()
        plt.close()
except Exception as err:
    print(f'plot_h2_timeseries failed:')
    print(traceback.format_exc())


#%% Stress periods
try:
    if int(sw.GSw_PRM_MaxStressPeriods):
        plt.close()
        level, regions = 'country', ['USA']
        f,ax = rplots.plot_stressperiod_dispatch(case=casedir, level=level, regions=regions)
        if write:
            plt.savefig(
                os.path.join(savepath,f'plot-dispatch-stressperiods-{",".join(regions)}.png'))
        if interactive: plt.show()
        plt.close()

        plt.close()
        f,ax = rplots.plot_stressperiod_days(case=casedir)
        if write:
            plt.savefig(os.path.join(savepath,f'plot-stressperiod-dates.png'))
        if interactive: plt.show()
        plt.close()

except Exception as err:
    print('plot_stressperiod_dispatch failed:')
    print(traceback.format_exc())


#%% Capacity markers
try:
    ### Just capacity
    ms = {'r':5, 'st':7}
    for level in ['r','st']:
        plt.close()
        f,ax = rplots.map_capacity_markers(
            case=casedir, level=level, year=year, ms=ms[level])
        if write:
            plt.savefig(os.path.join(savepath,f'map_units-gencap-{level}.png'))
        if interactive: plt.show()
        plt.close()
    ### Just transmission
    for subtract_baseyear in [None, 2020]:
        end = f'-since{subtract_baseyear}' if subtract_baseyear else ''
        plt.close()
        f,ax = rplots.map_transmission_lines(
            case=casedir, level='r', year=year, subtract_baseyear=subtract_baseyear)
        if write:
            plt.savefig(os.path.join(savepath,f'map_units-transcap{end}.png'))
        if interactive: plt.show()
        plt.close()
    ### Both
    plt.close()
    f,ax = rplots.map_transmission_lines(
        case=casedir, level='r', year=year, alpha=0.35, lw=0.15)
    rplots.map_capacity_markers(case=casedir, level='r', year=year, f=f, ax=ax)
    if write:
        plt.savefig(os.path.join(savepath,f'map_units-gencap-transcap.png'))
    if interactive: plt.show()
    plt.close()


except Exception as err:
    print('map_capacity_markers failed:')
    print(traceback.format_exc())


#%% Hybrid-specific plots
try:
    if int(sw.GSw_SpurScen):
        for (val,tech,cmap,vmax) in [
            ('site_cap','upv',plt.cm.Oranges,400),
            ('site_cap','wind-ons',plt.cm.Blues,400),
            ('site_hybridization',None,plt.cm.gist_earth_r,1),
            ('site_pv_fraction',None,plt.cm.turbo,1),
            ('site_spurcap',None,plt.cm.gist_earth_r,400),
            ('site_gir','upv',plt.cm.turbo,2),
            ('site_gir','wind-ons',plt.cm.turbo,2),
        ]:
            f,ax = rplots.map_hybrid_pv_wind(
                case=casedir,
                year=year,
                val=val, tech=tech, cmap=cmap, vmax=vmax,
                markersize=10.75,
            )
            if write:
                plt.savefig(
                    os.path.join(
                        savepath, f"map_hybrid-{val.replace('site_','')}-{tech}-{year}.png"))
            if interactive: plt.show()
except Exception as err:
    print('map_hybrids failed:')
    print(traceback.format_exc())
