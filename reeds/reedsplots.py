### Imports
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import patheffects as pe
from glob import glob
import os
import sys
import re
from warnings import warn
import geopandas as gpd
import shapely
import cmocean
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from reeds import plots

os.environ['PROJ_NETWORK'] = 'OFF'

reeds_path = reeds.io.reeds_path

plots.plotparams()

###### Constants
### Map fiddles
zone_label_offset = {
    'SPP_South': (0.1e6, 0.1e6),
    'MISO_Central': (0.1e6, -0.1e6),
    'MISO_North': (0, -0.1e6),
}
techmarkers = {
    'upv': 'o',
    'distpv': 'o',
    'csp': 'o',
    'pvb': 'o',
    'dr_shed':'o',

    'wind-ons': '^',
    'wind-ofs': 'v',

    'pumped-hydro': (8,1,0),
    'battery_li': (4,1,0),

    'hydro': 's',
    'nuclear': 'p', # '☢️',
    'nuclear-smr': 'p',
    'biopower': (5,1,0),
    'lfill-gas': (5,1,0),
    'beccs_mod': (5,1,180),
    'geothermal': 'h',

    'h2-ct': '>',
    'h2-cc': '<',

    'gas-cc': '<',
    'gas-cc-ccs_mod': 'D',
    'gas-ct': '>',
    'o-g-s': 'd',
    'coal': 'X',
    'coal-ccs_mod': 'P',
}


### Functions
def simplify_techs(techs, condense_upgrades=True):
    """
    Notes
    -----
    * Always changes all entries to lower case
    """
    ### Load the map
    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).str.lower()
    tech_map = tech_map.drop_duplicates().set_index('raw').display.str.lower()

    ### Get the unique techs
    _techs = pd.Series(techs).str.lower()
    techs_unique = pd.Series(_techs).unique()

    direct_map = {}
    for i in techs_unique:
        out = i
        ### First try to map each tech to the direct match
        for raw, display in tech_map.items():
            if i == raw:
                out = display
                break
        ### Now redo it for any tech that wasn't matched
        if out not in tech_map.values:
            for raw, display in tech_map.items():
                if i.startswith(raw):
                    out = display
                    break
        ### Other cleanup
        if condense_upgrades:
            if out.endswith('_upgrade'):
                out = out[:-len('_upgrade')]
        direct_map[i] = out

    ### Get the new list of techs
    techs_renamed = _techs.map(lambda x: direct_map.get(x,x))
    return techs_renamed


def plotdiff(
        val, casebase, casecomp, 
        casebase_name=None, casecomp_name=None,
        onlytechs=None, titleshorten=0,
        yearmin=None, yearmax=2050, colors=None,
        **plot_kwds,
    ):
    """
    """
    ### Shared inputs
    ycol = {
        'Error Check': 'Value',
        'Generation (TWh)': 'Generation (TWh)',
        'Capacity (GW)': 'Capacity (GW)',
        'New Annual Capacity (GW)': 'Capacity (GW)',
        'Annual Retirements (GW)': 'Capacity (GW)',
        'Final Gen by timeslice (GW)': 'Generation (GW)',
        'Firm Capacity (GW)': 'Firm Capacity (GW)',
        'Curtailment Rate': 'Curt Rate',
        'Transmission (GW-mi)': 'Amount (GW-mi)',
        'Transmission (PRM) (GW-mi)': 'Trans cap, PRM (GW-mi)',
        'Bulk System Electricity Pric': '$',
        'National Average Electricity': 'Average cost ($/MWh)',
        '2022-2050 Present Value of S': 'Discounted Cost (Bil $)',
        'Present Value of System Cost': 'Discounted Cost (Bil $)',
        'Runtime (hours)': 'processtime',
        'Runtime by year (hours)': 'processtime',
        'NEUE (ppm)': 'neue',
    }
    xcol = {
        'Error Check': 'dummy',
        'Generation (TWh)': 'year',
        'Capacity (GW)': 'year',
        'New Annual Capacity (GW)': 'year',
        'Annual Retirements (GW)': 'year',
        'Final Gen by timeslice (GW)': 'timeslice',
        'Firm Capacity (GW)': 'year',
        'Curtailment Rate': 'year',
        'Transmission (GW-mi)': 'year',
        'Transmission (PRM) (GW-mi)': 'year',
        'Bulk System Electricity Pric': 'year',
        'National Average Electricity': 'year',
        '2022-2050 Present Value of S': 'dummy',
        'Present Value of System Cost': 'dummy',
        'Runtime (hours)': 'dummy',
        'Runtime by year (hours)': 'year',
        'NEUE (ppm)': 'year',
    }
    width = {
        'Error Check': 20,
        'Generation (TWh)': 2.9,
        'Capacity (GW)': 2.9,
        'New Annual Capacity (GW)': 2.9,
        'Annual Retirements (GW)': 2.9,
        'Final Gen by timeslice (GW)': 0.9,
        'Firm Capacity (GW)': 2.9,
        'Curtailment Rate': 2.9,
        'Transmission (GW-mi)': 2.9,
        'Transmission (PRM) (GW-mi)': 2.9,
        'Bulk System Electricity Pric': 2.9,
        'National Average Electricity': 0.9,
        '2022-2050 Present Value of S': 20,
        'Present Value of System Cost': 20,
        'Runtime (hours)': 20,
        'Runtime by year (hours)': 2.9,
        'NEUE (ppm)': 2.9,
    }
    colorcol = {
        'Error Check': 'dummy',
        'Generation (TWh)': 'tech',
        'Capacity (GW)': 'tech',
        'New Annual Capacity (GW)': 'tech',
        'Annual Retirements (GW)': 'tech',
        'Final Gen by timeslice (GW)': 'tech',
        'Firm Capacity (GW)': 'tech',
        'Curtailment Rate': 'dummy',
        'Transmission (GW-mi)': 'type',
        'Transmission (PRM) (GW-mi)': 'type',
        'Bulk System Electricity Pric': 'type',
        'National Average Electricity': 'cost_cat',
        '2022-2050 Present Value of S': 'cost_cat',
        'Present Value of System Cost': 'cost_cat',
        'Runtime (hours)': 'process',
        'Runtime by year (hours)': 'process',
        'NEUE (ppm)': 'dummy',
    }
    fixcol = {
        'Error Check': {'type':'z'},
        'Generation (TWh)': {},
        'Capacity (GW)': {},
        'New Annual Capacity (GW)': {},
        'Annual Retirements (GW)': {},
        'Final Gen by timeslice (GW)': {},
        'Firm Capacity (GW)': {'season':0},
        'Curtailment Rate': {},
        'Transmission (GW-mi)': {},
        'Transmission (PRM) (GW-mi)': {},
        'Bulk System Electricity Pric': {},
        'National Average Electricity': {},
        '2022-2050 Present Value of S': {},
        'Present Value of System Cost': {},
        'Runtime (hours)': {},
        'Runtime by year (hours)': {},
        'NEUE (ppm)': {},
    }
    tfix = {
        'Bulk System Electricity Pric': '16_Bulk System Electricity Price ($/MWh)',
        '$': 'Price ($/MWh)',
        '2022-2050 Present Value of S': '25_2022-2050 Present Value of System Cost (Bil $)',
        'Present Value of System Cost': '25_Present Value of System Cost through 2050 (Bil $)',
    }
    ylabel = {
        'Error Check': 'System cost error [fraction]',
        'Generation (TWh)': 'Generation [TWh]',
        'Capacity (GW)': 'Capacity [GW]',
        'New Annual Capacity (GW)': 'Capacity [GW]',
        'Annual Retirements (GW)': 'Capacity [GW]',
        'Final Gen by timeslice (GW)': 'Generation [GW]',
        'Firm Capacity (GW)': 'Firm Capacity [GW]',
        'Curtailment Rate': 'Curtailment [%]',
        'Transmission (GW-mi)': 'Transmission capacity [TW-mi]',
        'Transmission (PRM) (GW-mi)': 'Transmission capacity [TW-mi]',
        'Bulk System Electricity Pric': 'Marginal cost [$/MWh]',
        'National Average Electricity': 'Average cost [$/MWh]',
        '2022-2050 Present Value of S': '[$Billion]',
        'Present Value of System Cost': '[$Billion]',
        'Runtime (hours)': 'Runtime [hours]',
        'Runtime by year (hours)': 'Runtime [hours]',
        'NEUE (ppm)': 'NEUE [ppm]',
    }
    scaler = {
        'Error Check': 1,
        'Generation (TWh)': 1,
        'Capacity (GW)': 1,
        'New Annual Capacity (GW)': 1,
        'Annual Retirements (GW)': 1,
        'Final Gen by timeslice (GW)': 1,
        'Firm Capacity (GW)': 1,
        'Curtailment Rate': 100,
        'Transmission (GW-mi)': 0.001,
        'Transmission (PRM) (GW-mi)': 0.001,
        'Bulk System Electricity Pric': 1,
        'National Average Electricity': 1,
        '2022-2050 Present Value of S': 1,
        'Present Value of System Cost': 1,
        'Runtime (hours)': 1,
        'Runtime by year (hours)': 1,
        'NEUE (ppm)': 1,
    }

    colors_time = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','process_style.csv'),
        index_col='order',
    ).squeeze(1).to_dict()
    colors_tech = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order')['color']
    colors_cost = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','cost_cat_style.csv'),
        index_col='order')['color']
    colors_trans = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
        index_col='order')['color']
    colors_tech = {
        **colors_tech,
        **{'ac':'C0','dc':'C1','vsc':'C3'},
        **{'load':'C0', 'nat_gen':'C1', 'nat_rps':'C1', 'oper_res':'C2', 
           'res_marg':'C3', 'state_rps':'C4',},
        **{'Capital':'C0','PTC':'C2','O&M':'C3','Fuel':'C4','Trans':'C1'},
        'dummy':'C0',
        **colors_trans,
        **colors_cost,
        **colors_time,
    }
    if colors:
        colors_tech = colors

    ### Parse the sheet name
    val2sheet = reeds.io.get_report_sheetmap(casebase)
    val = val.split('_')[-1]
    sheet = val2sheet[val]

    ### Load the data
    dfbase = reeds.io.read_report(casebase, sheet, val2sheet).rename(columns={'trtype':'type'})

    if colorcol[val] == 'dummy':
        dfbase['dummy'] = 'dummy'
    for col in fixcol[val]:
        if isinstance(fixcol[val][col], int):
            fixval = dfbase[col].unique()[fixcol[val][col]]
        else:
            fixval = fixcol[val][col]
        dfbase = dfbase.loc[dfbase[col] == fixval].copy()

    dfcomp = reeds.io.read_report(casecomp, sheet, val2sheet).rename(columns={'trtype':'type'})
    
    if colorcol[val] == 'dummy':
        dfcomp['dummy'] = 'dummy'
    if xcol[val] == 'dummy':
        dfbase['dummy'] = 0
        dfcomp['dummy'] = 0
    for col in fixcol[val]:
        if isinstance(fixcol[val][col], int):
            fixval = dfcomp[col].unique()[fixcol[val][col]]
        else:
            fixval = fixcol[val][col]
        dfcomp = dfcomp.loc[dfcomp[col] == fixval].copy()

    ### Apply the scaler
    dfbase[ycol[val]] *= scaler[val]
    dfcomp[ycol[val]] *= scaler[val]

    ### Only keep shared x-axis values
    shared_x = [i for i in dfbase[xcol[val]].unique() if i in dfcomp[xcol[val]].unique()]
    dfbase = dfbase.loc[dfbase[xcol[val]].isin(shared_x)].copy()
    dfcomp = dfcomp.loc[dfcomp[xcol[val]].isin(shared_x)].copy()

    ### Take the diff
    dfdiff = dfbase.drop(['scenario'], axis=1, errors='ignore').merge(
        dfcomp.drop(['scenario'], axis=1, errors='ignore'),
        on=[colorcol[val],xcol[val]], how='outer',
        suffixes=('_base','_comp')).fillna(0)
    dfdiff['{}_diff'.format(ycol[val])] = (
        dfdiff['{}_comp'.format(ycol[val])] - dfdiff['{}_base'.format(ycol[val])])
    # techs = dfdiff.loc[dfdiff[xcol[val]]==indices[0],colorcol[val]].values
    techs = dfdiff[colorcol[val]].unique()
    if onlytechs is not None:
        techs = onlytechs
    for tech in techs:
        if tech not in colors_tech:
            colors_tech[tech] = 'k'

    ### Only keep analyzed years
    if val == 'National Average Electricity':
        dfdiff = dfdiff.loc[dfdiff.year <= 2050].copy()
    ### Use yearmin if using a time axis
    if yearmin and (xcol[val]=='year'):
        dfdiff = dfdiff.loc[dfdiff.year >= yearmin].copy()
    ### Use yearmax if using a time axis
    if yearmax and (xcol[val]=='year'):
        dfdiff = dfdiff.loc[dfdiff.year <= yearmax].copy()
    indices = dfdiff[xcol[val]].unique()

    ###### Plot it
    plt.close()
    if not len(plot_kwds):
        plot_kwds = {'figsize':(13,4), 'gridspec_kw':{'wspace':0.25}}
    f,ax=plt.subplots(1, 4, sharex=True, **plot_kwds)

    ### Base
    for index in indices:
        ### Negative
        negtechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_base']<0),colorcol[val]]
        negheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(negtechs)),
            ycol[val]+'_base'
        ].loc[negtechs.index]
        bottom = negheight.cumsum()
        ax[0].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-negheight.values,
            width=width[val], color=[colors_tech[i] for i in negtechs], lw=0, 
        )
        ### Positive
        postechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_base']>=0),colorcol[val]]
        posheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(postechs)),
            ycol[val]+'_base'
        ].loc[postechs.index]
        bottom = posheight.cumsum()
        ax[0].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-posheight.values,
            width=width[val], color=[colors_tech[i] for i in postechs], lw=0, 
        )
    printbase = negheight.sum() + posheight.sum()

    ### Comp
    for index in indices:
        ### Negative
        negtechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_comp']<0),colorcol[val]]
        negheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(negtechs)),
            ycol[val]+'_comp'
        ].loc[negtechs.index]
        bottom = negheight.cumsum()
        ax[1].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-negheight.values,
            width=width[val], color=[colors_tech[i] for i in negtechs], lw=0, 
        )
        ### Positive
        postechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_comp']>=0),colorcol[val]]
        posheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(postechs)),
            ycol[val]+'_comp'
        ].loc[postechs.index]
        bottom = posheight.cumsum()
        ax[1].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-posheight.values,
            width=width[val], color=[colors_tech[i] for i in postechs], lw=0, 
        )
    printcomp = negheight.sum() + posheight.sum()
    printstring = (
        f'{val}, final year: base = {printbase:.2f};  comp = {printcomp:.2f};  '
        f'comp/base = {printcomp/printbase:.4f};  comp–base = {printcomp-printbase:.2f}'
    )
    print(printstring)

    ### Diff
    for col in [2,3]:
        for index in indices:
            ### Negative
            negtechs = dfdiff.loc[
                (dfdiff[xcol[val]]==index)
                &(dfdiff[colorcol[val]].isin(techs))
                &(dfdiff[ycol[val]+'_diff']<0),colorcol[val]]
            negheight = dfdiff.loc[
                (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(negtechs)),
                ycol[val]+'_diff'
            ].loc[negtechs.index]
            bottom = negheight.cumsum()
            ax[col].bar(
                x=[index]*len(bottom), bottom=bottom.values, height=-negheight.values,
                width=width[val], color=[colors_tech[i] for i in negtechs], lw=0, 
            )
            ### Positive
            postechs = dfdiff.loc[
                (dfdiff[xcol[val]]==index)
                &(dfdiff[colorcol[val]].isin(techs))
                &(dfdiff[ycol[val]+'_diff']>=0),colorcol[val]]
            posheight = dfdiff.loc[
                (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(postechs)),
                ycol[val]+'_diff'
            ].loc[postechs.index]
            bottom = posheight.cumsum()
            ax[col].bar(
                x=[index]*len(bottom), bottom=bottom.values, height=-posheight.values,
                width=width[val], color=[colors_tech[i] for i in postechs], lw=0, 
            )
            ### Sum
            ax[col].plot(
                [index], [negheight.sum() + posheight.sum()], 
                marker='o', lw=0, markerfacecolor='w', markeredgecolor='k')
        ax[col].axhline(0,c='0.5',lw=0.75,ls=':')

    ### Legend
    handles = [
        mpl.patches.Patch(facecolor=colors_tech[i], edgecolor='none', label=i)
        for i in techs
    ]
    leg = ax[-1].legend(
        handles=handles[::-1], loc='center left', bbox_to_anchor=(1,0.5), 
        fontsize='large', ncol=len(techs)//15+1, 
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5, 
    )

    ### Formatting
    # ax[0].set_ylabel(tfix.get(ycol[val],ycol[val]))
    ax[0].set_ylabel(ylabel.get(val, val))

    ## axes 0 and 1 use the same y limits
    ymax = max(ax[0].get_ylim()[1], ax[1].get_ylim()[1])
    ymin = min(ax[0].get_ylim()[0], ax[1].get_ylim()[0])
    for col in range(2):
        ax[col].set_ylim(ymin,ymax)
    ## axis 2 uses the same y limits as 0 and 1; axis 3 uses its own limits
    ax[2].set_ylim(-(ymin+ymax)/2, (ymin+ymax)/2)
    ax3ymin = min(ax[3].get_ylim()[0]*0.95, ax[3].get_ylim()[0]*1.05)
    ax3ymax = max(ax[3].get_ylim()[1]*0.95, ax[3].get_ylim()[1]*1.05)
    ax[3].set_ylim(ax3ymin, ax3ymax)
    # for col in [2,3]:
    #     ax[col].ticklabel_format(axis='y', style='plain')
    ## draw a line on axis 2 showing the axis 3 limits
    ax[0].set_xlim(*ax[0].get_xlim())
    xmax = ax[0].get_xlim()[1] - (ax[0].get_xlim()[1] - ax[0].get_xlim()[0]) * 0.01
    ax[2].plot([xmax]*2, [ax3ymin, ax3ymax], c='k', lw=1)

    if xcol[val] == 'year':
        ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
        ax[0].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(5))
        if val == '19_National Average Electricity':
            for col in range(3):
                ax[col].set_xlim(None,2050)
    elif xcol[val] == 'timeslice':
        for col in range(3):
            ax[col].set_xticks(range(len(indices)))
            ax[col].set_xticklabels(
                indices, rotation=55, rotation_mode='anchor', ha='right', va='center', fontsize=10)
    elif xcol[val] == 'dummy':
        for col in range(3):
            ax[col].xaxis.set_visible(False)

    _casebase_name = (casebase_name if casebase_name else os.path.basename(casebase)[titleshorten:])
    _casecomp_name = (casecomp_name if casecomp_name else os.path.basename(casecomp)[titleshorten:])
    ax[0].set_title(_casebase_name, x=0, ha='left', size='large', weight='bold')
    ax[1].set_title(_casecomp_name, x=0, ha='left', size='large', weight='bold')
    for col in [2,3]:
        ax[col].set_title(
            f'{_casecomp_name}\n– {_casebase_name}',
            x=0, ha='left', size='large', weight='bold')
    ax[0].annotate(
        (tfix.get(val,val) 
         + (', ' if len(fixcol[val]) > 0 else '')
         + ', '.join(['{} = {}'.format(col,fixcol[val][col]) for col in fixcol[val]])),
        xy=(0,1.15),xycoords='axes fraction',size='xx-large',weight='bold')
    ax[2].annotate('shared y axis', (0.02,0.02), xycoords='axes fraction')
    ax[3].annotate('zoomed y axis', (0.02,0.02), xycoords='axes fraction')

    plots.despine(ax)
    return f,ax,leg, dfdiff, printstring


def plot_trans_diff(
        casebase, casecomp,
        level='r',
        pcalabel=False, wscale=0.0003,
        year='last', yearlabel=True,
        colors={'+':'C3', '-':'C0',
                'AC':'C2', 'DC':'C1', 'LCC':'C1', 'VSC':'C3', 'B2B':'C4'},
        alpha=0.75, dpi=None, drawzones=True, drawstates=True,
        simpletypes=None, subtract_baseyear=None,
        trtypes=['AC','B2B','LCC','VSC'],
        f=None, ax=None, scale=True, label_line_capacity=True,
        titleshorten=0,
        thickborders='none', thickness=0.5,
    ):
    """Plot difference map of interzonal transmission"""
    ### Load shapefiles
    dfmap = reeds.io.get_dfmap(casebase)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    hierarchy = reeds.io.get_hierarchy(casebase)
    for col in hierarchy:
        dfba[col] = dfba.index.map(hierarchy[col])
    hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()
    ## Aggregate zones if necessary
    dfzones = dfba.copy()
    if level not in ['r','rb']:
        dfzones.geometry = dfzones.buffer(0.)
        dfzones = dfzones.dissolve(level)
        dfzones['x'] = dfzones.centroid.x
        dfzones['y'] = dfzones.centroid.y
    ## Get thick borders if necessary
    if thickborders not in [None,'','none','None',False]:
        if thickborders in hierarchy:
            dfthick = dfba.copy()
            dfthick[thickborders] = hierarchy[thickborders]
            dfthick.geometry = dfthick.buffer(0.)
            dfthick = dfthick.dissolve(thickborders)
    
    cases = {'base': casebase, 'comp': casecomp}
    tran_out = {}
    for case in cases:
        tran_out[case] = reeds.io.read_output(cases[case], 'tran_out', valname='MW')
        if simpletypes is None:
            dicttran = {
                i: tran_out[case].loc[tran_out[case].trtype==i].set_index(['r','rr','t']).MW
                for i in trtypes}
            tran_out[case] = pd.concat(dicttran, axis=0, names=['trtype','r','rr','t']).reset_index()

        if subtract_baseyear:
            tran_out[case] = (
                tran_out[case].pivot(index=['r','rr','trtype'], columns='t', values='MW')
                .subtract(
                    tran_out[case].pivot(index=['r','rr','trtype'], columns='t', values='MW')
                    [subtract_baseyear].fillna(0), axis=0)
            ).stack('t').rename('MW').reset_index()

    dfplot = tran_out['base'].merge(
        tran_out['comp'], on=['r','rr','t','trtype'], suffixes=('_base','_comp'), how='outer').fillna(0)
    dfplot = dfplot.loc[dfplot.t==(dfplot.t.max() if year=='last' else year)].copy()
    dfplot['MW_diff'] = dfplot['MW_comp'] - dfplot['MW_base']


    dfplot['r_x'] = dfplot.r.map(dfba.x)
    dfplot['r_y'] = dfplot.r.map(dfba.y)
    dfplot['rr_x'] = dfplot.rr.map(dfba.x)
    dfplot['rr_y'] = dfplot.rr.map(dfba.y)

    ## Make figure if necessary
    justdiff = True
    if (not f) and (not ax):
        justdiff = False
        plt.close()
        f,ax=plt.subplots(
            1,3,sharex=True,sharey=True,figsize=(14,8),
            gridspec_kw={'wspace':-0.05, 'hspace':0.05},
            dpi=dpi,
        )

    ###### Just difference
    if justdiff:
        ### Boundaries
        if drawzones:
            dfba.plot(ax=ax, edgecolor='0.5', facecolor='none', lw=0.1)
        if drawstates:
            dfstates.plot(ax=ax, edgecolor='0.25', facecolor='none', lw=0.2)
        if thickborders not in [None,'','none','None',False]:
            dfthick.plot(ax=ax, edgecolor='0.75', facecolor='none', lw=thickness)
        ax.axis('off')
        ### Diff
        for i, row in dfplot.iterrows():
            ax.plot(
                [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
                color=(colors['+'] if row['MW_diff'] >= 0 else colors['-']), 
                lw=abs(wscale*row['MW_diff']), solid_capstyle='butt', alpha=alpha,
            )
            if label_line_capacity and (abs(row.MW_diff/1000) >= label_line_capacity):
                _label_line(row=row, ax=ax, wscale=wscale, cap='MW_diff', sign=True)
        ### Stop here
        return dfplot

    ###### Absolute and difference
    for col in range(3):
        ### Boundaries
        dfba.plot(ax=ax[col], edgecolor='0.5', facecolor='none', lw=0.1)
        dfstates.plot(ax=ax[col], edgecolor='0.5', facecolor='none', lw=0.2)
        ax[col].axis('off')

    for i, row in dfplot.iterrows():
        ### Base
        ax[0].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=colors[row['trtype']], lw=wscale*row['MW_base'], solid_capstyle='butt',
            alpha=alpha,
        )
        if label_line_capacity and (row.MW_base/1000 >= label_line_capacity):
            _label_line(row=row, ax=ax[0], wscale=wscale, cap='MW_base')
        ### Comp
        ax[1].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=colors[row['trtype']], lw=wscale*row['MW_comp'], solid_capstyle='butt',
            alpha=alpha,
        )
        if label_line_capacity and (row.MW_comp/1000 >= label_line_capacity):
            _label_line(row=row, ax=ax[1], wscale=wscale, cap='MW_comp')
        ### Diff
        ax[2].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=(colors['+'] if row['MW_diff'] >= 0 else colors['-']), 
            lw=abs(wscale*row['MW_diff']), solid_capstyle='butt', alpha=alpha,
        )
        if label_line_capacity and (abs(row.MW_diff/1000) >= label_line_capacity):
            _label_line(row=row, ax=ax[2], wscale=wscale, cap='MW_diff', sign=True)

    ###### Labels
    if pcalabel:
        for col in range(3):
            for r in dfba.index:
                ax[col].annotate(
                    r.replace('p',''), dfba.loc[r,['x','y']].values,
                    ha='center', va='center', fontsize=5, color='0.7')
    if yearlabel:
        ax[0].annotate(
            'Year: {}'.format(year), 
            (0.9,0.97), xycoords='axes fraction', fontsize=10, ha='right', va='top')
    ax[0].annotate(
        os.path.basename(cases['base'])[titleshorten:],
        (0.1,1), xycoords='axes fraction', fontsize=10)
    ax[1].annotate(
        os.path.basename(cases['comp'])[titleshorten:],
        (0.1,1), xycoords='axes fraction', fontsize=10)
    ax[2].annotate(
        '{}\n– {}'.format(
            os.path.basename(cases['comp'])[titleshorten:],
            os.path.basename(cases['base'])[titleshorten:]),
        (0.1,1), xycoords='axes fraction', fontsize=10)

    ###### Scale
    if scale:
        ax[0].plot(
            [-2.0e6,-1.5e6], [-1.0e6, -1.0e6],
            color='k', lw=wscale*10e3, solid_capstyle='butt'
        )
        ax[0].annotate(
            '10 GW', (-1.75e6, -1.1e6), ha='center', va='top', weight='bold')
        if subtract_baseyear:
            ax[0].annotate(
                f'(new since {subtract_baseyear})', (-1.75e6, -1.3e6), ha='center', va='top')

    return f, ax


def _label_line(row, ax, wscale, label_line_color='k', cap='MW', sign=False, minsize=1):
    """
    * only works when line thicknesses are in points (not data units)
    """
    ### Get the angle
    angle = np.arctan((row.rr_y - row.r_y) / (row.rr_x - row.r_x)) * 180 / np.pi
    ## Keep it upright
    if (90 < angle < 270) or (-90 > angle > -270):
        angle *= -1
    ### Get the font size in points
    size = max(abs(row[cap]) * wscale, minsize)
    ### Get the middle of the line
    xtext = (row.r_x + row.rr_x) / 2
    ytext = (row.r_y + row.rr_y) / 2

    ### Write it in GW
    ax.annotate(
        (f'{row[cap]/1000:+.0f}' if sign else f'{row[cap]/1000:.0f}'),
        (xtext, ytext), rotation=angle,
        size=size, color=label_line_color, ha='center', va='center',
    )


def plot_trans_onecase(
        case,
        dfin=None,
        level='r',
        pcalabel=False,
        wscale=0.0003,
        year='last',
        yearlabel=True,
        colors={'AC':'C2', 'LCC':'C1', 'VSC':'C3', 'B2B':'C4'},
        dpi=None,
        trtypes=['AC','B2B','LCC','VSC'],
        simpletypes={'AC_init':'AC','LCC_init':'LCC','B2B_init':'B2B'},
        zorders={'AC':1e3, 'VSC':3e3, 'LCC':4e3, 'B2B':7e3,},
        alpha=1,
        scalesize='x-large',
        f=None,
        ax=None,
        scale=True,
        title=True,
        routes=False,
        tolerance=1000,
        subtract_baseyear=None,
        show_overlap=True,
        drawzones=True,
        show_converters=0.5,
        crs='ESRI:102008',
        thickborders='none',
        thickness=0.5,
        thickcolor='0.75',
        drawstates=True,
        label_line_capacity=0,
        crossing_level='r',
    ):
    """
    Notes
    * If colors is a string instead of a dictionary, aggregate all transmission types
    """
    ### Load shapefiles
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    hierarchy = reeds.io.get_hierarchy(case)
    ## Aggregate zones if necessary
    dfzones = dfba.copy()
    if level not in ['r','rb']:
        dfzones.geometry = dfzones.buffer(0.)
        dfzones = dfzones.dissolve(level)
        dfzones['x'] = dfzones.centroid.x
        dfzones['y'] = dfzones.centroid.y
    ## Get thick borders if necessary
    if thickborders not in [None,'','none','None',False]:
        if thickborders in hierarchy:
            dfthick = dfmap[thickborders].copy()
    ## Get route linestrings if necessary
    if routes:
        transmission_routes = gpd.read_file(
            os.path.join(reeds_path,'inputs','shapefiles','transmission_routes-500kVac.gpkg')
        ).set_index(['r','rr']).to_crs(crs)

        if tolerance:
            transmission_routes['geometry'] = transmission_routes.simplify(tolerance)

    ### Load run-specific output data
    if dfin is None:
        tran_out = reeds.io.read_output(case, 'tran_out', valname='MW')
        ## If necessary, subset to interregional lines
        if crossing_level != 'r':
            tran_out = tran_out.loc[
                tran_out.r.map(hierarchy[crossing_level])
                != tran_out.rr.map(hierarchy[crossing_level])
            ].copy()
        if simpletypes is None:
            dicttran = {
                i: tran_out.loc[tran_out.trtype==i].set_index(['r','rr','t']).MW
                for i in trtypes}
            tran_out = pd.concat(dicttran, axis=0, names=['trtype','r','rr','t']).reset_index()
        else:
            ### Group initial and new capacity together and only plot with the simple name
            tran_out = (
                tran_out
                .assign(trtype=tran_out.trtype.replace(simpletypes))
                .groupby(['r','rr','trtype','t'], as_index=False).sum()
            )


        dfplot = tran_out.loc[
            (tran_out.t==(tran_out.t.max() if year=='last' else year))
            & (tran_out.trtype.isin(trtypes))
        ].copy()

        if subtract_baseyear:
            ### Currently only works for non-aggregated transmission
            dfplot = (dfplot.set_index(['r','rr','trtype']).MW - tran_out.loc[
                (tran_out.t==subtract_baseyear)
                & (tran_out.trtype.isin(trtypes))
            ].set_index(['r','rr','trtype']).MW.reindex(
                dfplot.set_index(['r','rr','trtype']).index).fillna(0)).clip(lower=0).reset_index()
            dfplot = dfplot.loc[dfplot.MW>0].copy()

        if level not in ['r','rb']:
            for col in ['r','rr']:
                dfplot[col] = dfplot[col].map(hierarchy[level])
            ## Only keep one direction
            for i, row in dfplot.iterrows():
                dfplot.loc[i,['r','rr']] = sorted(dfplot.loc[i,['r','rr']])
            ## Drop lines within the same level
            dfplot = dfplot.loc[dfplot.r != dfplot.rr].copy()
            ## Aggregate
            dfplot = dfplot.groupby(['r','rr','trtype'], as_index=False).MW.sum()

    ### Otherwise take the correctly-formatted dataframe passed as an input
    else:
        dfplot = dfin.copy()

    ### Aggregate types if colors is a string instead of a dictionary
    if isinstance(colors, str):
        dfplot = dfplot.groupby(['r','rr','t'], as_index=False).MW.sum()

    dfplot['r_x'] = dfplot.r.map(dfzones.x)
    dfplot['r_y'] = dfplot.r.map(dfzones.y)
    dfplot['rr_x'] = dfplot.rr.map(dfzones.x)
    dfplot['rr_y'] = dfplot.rr.map(dfzones.y)

    ## Load VSC converter capacity if necessary
    if show_converters and ('VSC' in dfplot.trtype.unique()):
        dfin = reeds.io.read_output(case, 'cap_converter_out', valname='MW')
        dfconverter = dfba.merge(
            dfin.loc[dfin.t==year], left_index=True, right_on='r'
        )

    ## Make figure if necessary
    if (not f) and (not ax):
        plt.close()
        f,ax = plt.subplots(figsize=(14,8), dpi=dpi,)

    ###### Shared
    ### Boundaries
    if drawzones:
        dfzones.plot(ax=ax, edgecolor='0.8', facecolor='none', lw=0.1)
    if drawstates:
        dfstates.plot(ax=ax, edgecolor='0.25', facecolor='none', lw=0.2)
    if thickborders not in [None,'','none','None',False]:
        dfthick.plot(ax=ax, edgecolor=thickcolor, facecolor='none', lw=thickness)
    ax.axis('off')
    ### Labels
    if pcalabel:
        for r in dfzones.index:
            ax.annotate(
                r, dfzones.loc[r,['x','y']].values,
                ha='center', va='center', fontsize=5, color='C7', alpha=0.8,
                bbox={'facecolor':'w', 'edgecolor':'none', 'alpha':0.8, 'pad':0.5},
            )

    if yearlabel and isinstance(case,str):
        ax.annotate(
            'Year: {}'.format(year), 
            (0.9,1), xycoords='axes fraction', fontsize=10, ha='right', va='top')


    ###### Lines
    if routes:
        if show_overlap:
            for i in dfplot.index:
                row = dfplot.loc[i]
                transmission_routes.loc[[(row.r,row.rr)]].buffer(wscale*row['MW']).plot(
                    ax=ax, alpha=alpha,
                    zorder=(1000 if isinstance(colors,str) else zorders[row['trtype']]),
                    color=(colors if isinstance(colors,str) else colors[row['trtype']]),
                )    
        else:
            if isinstance(colors,dict):
                for trtype in trtypes:
                    alllines = gpd.GeoDataFrame(
                        dfplot.loc[dfplot.trtype==trtype]
                        .merge(
                            transmission_routes[['geometry']],
                            left_on=['r','rr'], right_index=True)
                    )
                    alllines['dummy'] = 'dummy'
                    alllines['geometry'] = alllines.buffer(alllines.MW*wscale)
                    alllines = alllines.dissolve('dummy')
                    alllines.plot(ax=ax, alpha=alpha, color=colors[trtype], label=trtype)
            else:
                alllines = gpd.GeoDataFrame(
                    dfplot.merge(
                        transmission_routes[['geometry']],
                        left_on=['r','rr'], right_index=True)
                )
                alllines['dummy'] = 'dummy'
                alllines['geometry'] = alllines.buffer(alllines.MW*wscale)
                alllines = alllines.dissolve('dummy')
                alllines.plot(ax=ax, alpha=alpha, color=colors)

    else:
        if show_overlap:
            for i in dfplot.index:
                row = dfplot.loc[i]
                ax.plot(
                    [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
                    color=(colors if isinstance(colors, str) else colors[row['trtype']]),
                    lw=wscale*row['MW'], solid_capstyle='butt',
                    alpha=alpha,
                )
                if label_line_capacity and (row.MW/1000 >= label_line_capacity):
                    _label_line(row=row, ax=ax, wscale=wscale)
        else:
            alllines = []
            for i in dfplot.index:
                row = dfplot.loc[i]
                alllines.append(
                    shapely.geometry.LineString(
                        [(row.r_x, row.r_y), (row.rr_x, row.rr_y)]
                    ).buffer(row.MW*wscale)
                )
            alllines = shapely.ops.unary_union(alllines)
            alllines = gpd.GeoSeries([alllines]).set_crs(crs)
            alllines.plot(ax=ax, alpha=alpha, color=colors)

    ###### VSC converters (if necessary)
    if show_converters and ('VSC' in dfplot.trtype.unique()):
        ax.scatter(
            dfconverter.x.values, dfconverter.y.values,
            facecolor='none', edgecolor='k',
            s=((dfconverter.MW.values*wscale)**2 * 3.14 / 4),
            zorder=1E6, lw=show_converters,
        )
    
    ###### Scale
    if title and isinstance(case,str):
        ax.annotate(
            '{} ({}{})'.format(
                os.path.basename(case), year,
                f', additions since {subtract_baseyear}' if subtract_baseyear else ' total',
            ),
            (0.1,1), xycoords='axes fraction', fontsize=10)
    if scale:
        if routes or (not show_overlap):
            gpd.GeoSeries(
                shapely.geometry.LineString([(-1.9e6,-0.9e6),(-1.6e6,-0.9e6)])
            ).buffer(wscale*10e3).plot(
                ax=ax, color=(colors if isinstance(colors,str) else 'k'), alpha=alpha)
        else:
            ax.plot(
                [-1.9e6,-1.6e6], [-0.9e6, -0.9e6],
                color=(colors if isinstance(colors,str) else 'k'),
                lw=wscale*10e3, solid_capstyle='butt',
            )
        ax.annotate(
            '10 GW', (-1.75e6, -1.0e6), ha='center', va='top', weight='bold', fontsize=scalesize)

    return f, ax, dfplot


def plotdiffmaps(val, i_plot, year, casebase, casecomp, reeds_path, 
                 plot='diff', f=None, ax=None, cmap=plt.cm.Blues,
                 zmax=None, zlim=None,
                 legend_kwds=None, plot_kwds=None,):
    """
    Inputs
    ------
    plot: 'diff', 'base', 'comp'
    """
    ###### Shared inputs
    ycols = {
        'gen_h': ['i','r','h','t','GEN'],
        'gen_ann': ['i','r','t','GEN'],
        'cap': ['i','r','t','CAP'],
        'cap_avail': ['i','r','t','rscbin','CAP'],
    }
    units = {
        'gen_h': 'GWh/timeslice',
        'gen_ann': 'TWh/y',
        'cap': 'GW',
        'cap_avail': 'GW',
    }
    unitscaler = {
        'gen_h': 1E-3,
        'gen_ann': 1E-6,
        'cap': 1E-3,
        'cap_avail': 1E-3,
    }
    ### Get the vals
    valcol = ycols[val][-1]
    units = units[val]
    unitscaler = unitscaler[val]
    if legend_kwds is None:
        legend_kwds = {
            'shrink':0.6, 'pad':0,
            'label':'{} {} {} [{}]'.format(valcol,i_plot,year,units),
            'orientation':'horizontal',
        }
    if plot_kwds is None:
        plot_kwds = {'figsize':(10,7.5),'dpi':100,}
    ### Replace column names
    rep_i = {
        'coaloldscr':'coal', 'coalolduns':'coal', 'coal-igcc':'coal', 'coal-new':'coal',
        'csp2':'csp','csp-ns':'csp',
        'gas-cc':'gas-cc', 'gas-ct':'gas-ct',
        'beccs_mod':'beccs',
        'can-imports':'canada',
        'undisc':'geothermal',
        'hyded':'hydro', 'hydend':'hydro', 'hydnd':'hydro', 
        'hydnpnd':'hydro', 'hydud':'hydro', 'hydund':'hydro',
        'geohydro_pbinary':'geothermal', 'geohydro_pflash':'geothermal', 'undisc_pflash':'geothermal',
        'egs_allkm':'geothermal', 'geohydro_allkm':'geothermal', 'egs_nearfield':'geothermal',
        'gas-cc-ccs_mod':'gas-cc-ccs', 'gas-cc_gas-cc-ccs_mod':'gas-cc-ccs',
        'coal-new_coal-ccs_mod':'coal-ccs', 'coaloldscr_coal-ccs_mod':'coal-ccs',
        'coalolduns_coal-ccs_mod':'coal-ccs', 'coal-igcc_coal-ccs_mod':'coal-ccs',
        're-ct':'h2-ct', 'h2-ct_upgrade':'h2-ct',
        're-cc':'h2-ct', 'h2-cc':'hc-ct',
        'gas-cc_re-cc':'h2-ct', 'gas-ct_re-ct':'h2-ct', 'gas-cc_h2-cc':'h2-cc', 'h2-cc_upgrade':'h2-cc', 'gas-ct_h2-ct':'h2-ct', 
        ### Use if grouping onshore and offshore together
        # 'wind-ons':'wind', 'wind-ofs':'wind',
    }

    ### Get the maps
    dfmap = reeds.io.get_dfmap(casecomp)
    dfba = dfmap['r']
    dfstates = dfmap['st']

    ### Load the data, sum over hours
    dfbase = reeds.io.read_output(casebase, val, valname=valcol)
    dfcomp = reeds.io.read_output(casecomp, val, valname=valcol)

    ### Drop the tails
    dfbase.i = dfbase.i.str.strip('_0123456789').str.lower()
    dfcomp.i = dfcomp.i.str.strip('_0123456789').str.lower()

    ### Simplify the i names
    dfbase.i = dfbase.i.map(lambda x: rep_i.get(x.lower(),x.lower()))
    dfcomp.i = dfcomp.i.map(lambda x: rep_i.get(x.lower(),x.lower()))

    dfbase = dfbase.groupby(['i','r','t']).sum().reset_index().copy()
    dfcomp = dfcomp.groupby(['i','r','t']).sum().reset_index().copy()
    # print(dfbase.i.unique())
    # print(dfcomp.i.unique())

    ### Correct the units
    dfbase[valcol] *= unitscaler
    dfcomp[valcol] *= unitscaler

    ### Start the plot
    # plt.close()
    if (f is None) and (ax is None):
        f,ax=plt.subplots(**plot_kwds)
    else:
        pass

    ###### Calculate the diff
    dfdiff = dfbase.merge(
        dfcomp, on=['i','r','t'], how='outer', suffixes=('_base','_comp')).fillna(0)
    if plot in ['diff','pctdiff','pct_diff','diffpct','diff_pct','pct']:
        ### Percent difference
        dfdiff['{}_diff'.format(valcol)] = (
            (dfdiff['{}_comp'.format(valcol)] - dfdiff['{}_base'.format(valcol)])
            / dfdiff['{}_base'.format(valcol)] * 100
        ).replace(np.inf,np.nan)
    elif plot in ['absdiff', 'abs_diff', 'diffabs', 'diff_abs']:
        ### Difference
        dfdiff['{}_diff'.format(valcol)] = (
            dfdiff['{}_comp'.format(valcol)] - dfdiff['{}_base'.format(valcol)])
    
    if zmax is None:
        zmax = max(
            dfdiff.loc[(dfdiff.i.str.startswith(i_plot))&(dfdiff.t==year),valcol+'_base'].max(),
            dfdiff.loc[(dfdiff.i.str.startswith(i_plot))&(dfdiff.t==year),valcol+'_comp'].max(),
        )
    
    ###### Plot the base
    if plot == 'base':
        dfplot = dfba.merge(
            dfbase.loc[(dfbase.i.str.startswith(i_plot))&(dfbase.t==year),['r',valcol]],
            left_index=True, right_on='r', how='left'
        ).fillna(0).reset_index(drop=True)

        dfplot.plot(ax=ax, column=valcol, cmap=cmap, legend=True,
                    legend_kwds=legend_kwds, vmax=zmax)

    ###### Plot the comp
    elif plot == 'comp':
        dfplot = dfba.merge(
            dfcomp.loc[(dfcomp.i.str.startswith(i_plot))&(dfcomp.t==year),['r',valcol]],
            left_index=True, right_on='r', how='left'
        ).fillna(0).reset_index(drop=True)

        dfplot.plot(ax=ax, column=valcol, cmap=cmap, legend=True,
                    legend_kwds=legend_kwds, vmax=zmax)

    ###### Plot the pct diff
    elif plot in ['diff','pctdiff','pct_diff','diffpct','diff_pct','pct']:
        legend_kwds['label'] = '{} {} {}\n[% diff]'.format(valcol,i_plot,year)

        dfplot = dfba.merge(
            dfdiff.loc[(dfdiff.i.str.startswith(i_plot))&(dfdiff.t==year),['r',valcol+'_diff']],
            left_index=True, right_on='r', how='left'
        ).reset_index(drop=True)

        if zlim is None:
            zlim = max(
                abs(dfplot[valcol+'_pctdiff'].min()),
                abs(dfplot[valcol+'_pctdiff'].max()),
                0.1,
            )

        dfplot.plot(ax=ax, column=valcol+'_pctdiff', cmap=cmap, legend=True,
                    vmin=-zlim, vmax=+zlim, legend_kwds=legend_kwds)

    ###### Plot the absolute diff
    elif plot in ['absdiff', 'abs_diff', 'diffabs', 'diff_abs']:
        legend_kwds['label'] = '{}diff {} [{}]'.format(valcol,i_plot,units)

        dfplot = dfba.merge(
            dfdiff.loc[(dfdiff.i.str.startswith(i_plot))&(dfdiff.t==year),['r',valcol+'_diff']],
            left_index=True, right_on='r', how='left'
        ).reset_index(drop=True)

        if zlim is None:
            zlim = max(
                abs(dfplot[valcol+'_diff'].min()),
                abs(dfplot[valcol+'_diff'].max()),
                0.1,
            )

        dfplot.plot(ax=ax, column=valcol+'_diff', cmap=plt.cm.RdBu_r, legend=True,
                    vmin=-zlim, vmax=+zlim, legend_kwds=legend_kwds)

    ### Finish and return
    # ax.set_title(title, y=0.95)
    dfstates.plot(ax=ax, edgecolor='k', facecolor='none', lw=0.25)
    ax.axis('off')

    return f,ax,dfplot


def plot_trans_vsc(
        case, year=2050, wscale=0.4, alpha=1.0, miles=300,
        cmap=cmocean.cm.rain, scale=True, title=True,
        convertermax=None,
        f=None, ax=None,
    ):
    """
    """
    ### Get the BA map
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']

    ### Load converter capacity
    dfin = reeds.io.read_output(case, 'cap_converter_out', valname='MW')
    dfconverter = dfba.merge(
        dfin.loc[dfin.t==year], left_index=True, right_on='r'
    ).rename(columns={'MW':'GW'})
    dfconverter.GW /= 1000

    ### Load transmission capacity
    tran_out = reeds.io.read_output(case, 'tran_out', valname='MW')

    dfplot = tran_out.copy()
    dfplot = dfplot.loc[
        (dfplot.t==year) & (dfplot.trtype == 'VSC')
    ].copy()
    dfplot['GW'] = dfplot['MW'] / 1000

    dfplot['r_x'] = dfplot.r.map(dfba.x)
    dfplot['r_y'] = dfplot.r.map(dfba.y)
    dfplot['rr_x'] = dfplot.rr.map(dfba.x)
    dfplot['rr_y'] = dfplot.rr.map(dfba.y)

    if not len(dfplot):
        print('plot_trans_vsc(): No VSC lines, so no plot is generated')
        return None, None

    ### Plot it
    if (not f) and (not ax):
        plt.close()
        f,ax=plt.subplots(figsize=(14,8))

    ### Converter capacity
    if cmap:
        axheight = ax.get_window_extent().transformed(f.dpi_scale_trans.inverted()).height
        cbar_label = ('Converter capacity [GW]' if axheight > 2.5 else 'Converter\ncapacity [GW]')
        dfconverter.plot(
            ax=ax, column='GW', cmap=cmap,
            legend=True, 
            legend_kwds={
                'shrink':0.6, 'pad':0, 'orientation':'vertical',
                'label':cbar_label},
            vmin=0, vmax=(convertermax if convertermax else None),
            alpha=0.75,
        )
    ax.scatter(
        dfconverter.x.values, dfconverter.y.values,
        facecolor='none', edgecolor='k',
        s=((dfconverter.GW.values*wscale)**2 * 3.14 / 4),
        zorder=1E6,
    )

    ### Boundaries
    dfba.plot(ax=ax, edgecolor='0.5', facecolor='none', lw=0.1)
    dfstates.plot(ax=ax, edgecolor='0.25', facecolor='none', lw=0.2)

    ### Lines
    for i in dfplot.index:
        row = dfplot.loc[i]
        ax.plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color='C3', lw=wscale*row['GW'], solid_capstyle='butt',
            alpha=alpha,
        )
    if title:
        ax.annotate('{} ({})'.format(os.path.basename(case), year),
                    (0.1,1), xycoords='axes fraction', fontsize=10)

    ### Scale
    if scale:
        ax.plot(
            -1.75e6 + np.array([-1609/2*miles,1609/2*miles]),
            [-1.0e6, -1.0e6],
            color='C3', lw=wscale*10, solid_capstyle='butt'
        )
        ax.annotate(
            '10 GW\n{} miles'.format(miles), (-1.75e6, -1.1e6),
            ha='center', va='top', weight='bold', fontsize='x-large')

    ax.axis('off')

    return f,ax


def plot_transmission_utilization(
        case, year=2050, plottype='mean', network='trans',
        wscale=0.0004, alpha=1.0, cmap=cmocean.cm.rain,
        extent='modeled',
        f=None, ax=None,
        thicklevel='transreg',
    ):
    """
    # Inputs
    extent: 'modeled' for modeled area, 'usa' for contiguous US
    """
    sw = reeds.io.get_switches(case)
    ### Get the output data
    add_other_direction = False
    hcol = 'h'
    if any([k in network.lower() for k in ['h2','hydrogen']]):
        dftrans = {
            'trans_cap': reeds.io.read_output(case, 'h2_trans_cap'),
            'trans_flow_power': reeds.io.read_output(case, 'h2_trans_flow'),
        }
        title = f'{plottype.title()} utilization [fraction]'
        add_other_direction = True
    elif any([k in network.lower() for k in ['stress','prm','peak','resource adequacy']]):
        dftrans = {
            'trans_cap': reeds.io.read_output(case, 'tran_cap_prm'),
        }
        if int(sw.GSw_PRM_CapCredit):
            dftrans['trans_flow_power'] = reeds.io.read_output(case, 'captrade')
            hcol = 'ccseason'
        else:
            dftrans['trans_flow_power'] = reeds.io.read_output(case, 'tran_flow_stress')
        title = f'{plottype.title()} utilization\nfor RA [fraction]'
    else:
        dftrans = {
            'trans_cap': reeds.io.read_output(case, 'tran_cap_energy'),
            'trans_flow_power': reeds.io.read_output(case, 'tran_flow_rep'),
        }
        title = f'{plottype.title()} utilization [fraction]'
    if add_other_direction:
        ## Include both directions
        dftrans['trans_cap'] = pd.concat([
            dftrans['trans_cap'],
            dftrans['trans_cap'].rename(columns={'r':'rr','rr':'r'}),
        ], axis=0, ignore_index=True)
    else:
        ## Reorient negative values
        dftrans['trans_flow_power'].loc[dftrans['trans_flow_power'].Value < 0, ['r','rr']] = (
            dftrans['trans_flow_power'].loc[dftrans['trans_flow_power'].Value < 0, ['rr','r']].values
        )
        dftrans['trans_flow_power'].Value = dftrans['trans_flow_power'].Value.abs()
    val_r = pd.read_csv(
        os.path.join(case,'inputs_case','val_r.csv'), header=None,
    ).squeeze(1).values.tolist()
    ### Combine all transmission types
    for data in ['trans_flow_power','trans_cap']:
        dftrans[data]['trtype'] = 'all'
        dftrans[data] = (
            dftrans[data]
            .loc[dftrans[data].t==year]
            .groupby([c for c in dftrans[data] if c not in ['Value']], as_index=False)
            .sum()
            .drop('t', axis=1)
        ).rename(columns={'Value':'Val', 'MW':'Val', hcol:'h'})
    ### Get utilization by timeslice
    utilization = dftrans['trans_flow_power'].merge(
        dftrans['trans_cap'], on=['r','rr','trtype'], suffixes=('_flow','_cap'),
        how='right',
    ).fillna({'Val_flow':0})
    utilization['fraction'] = utilization.Val_flow.abs() / utilization.Val_cap
    ### Get annual fractional utilization
    ## First try the hourly version; if it doesn't exist load the h17 version
    try:
        hours = pd.read_csv(
            os.path.join(case,'inputs_case', 'rep', 'hours_hourly.csv'),
            header=0, names=['h','hours'], index_col='h').squeeze(1)
    except FileNotFoundError:
        hours = pd.read_csv(
            os.path.join(case,'inputs_case', 'rep', 'numhours.csv'),
            header=0, names=['h','hours'], index_col='h').squeeze(1)
    utilization['Valh'] = utilization.apply(
        lambda row: hours.get(row.get('h', 1), 1) * abs(row.Val_flow),
        axis=1
    )
    utilization_annual = (
        utilization.groupby(['r','rr','trtype']).Valh.sum()
        .divide(dftrans['trans_cap'].set_index(['r','rr','trtype']).Val)
        .fillna(0).rename('fraction')
        / utilization.h.drop_duplicates().map(lambda x: hours.get(x, 1)).sum()
    ).reset_index()

    ###### Plot max utilization
    dfplots = {
        'max': utilization.groupby(['r','rr','trtype'], as_index=False).fraction.max(),
        'mean': utilization_annual,
    }
    dfplot = dfplots[plottype.lower()]
    ### Only keep the direction with the higher fraction, since it presumably drives investment
    ### (if there is any)
    dfplot.loc[dfplot.r > dfplot.rr, ['r','rr']] = dfplot.loc[dfplot.r > dfplot.rr, ['rr','r']].values
    dfplot = dfplot.sort_values('fraction').drop_duplicates(subset=['r','rr'], keep='last')
    if (dfplot.fraction > 1.01).any():
        warn(f'Fractions greater than 1: {dfplot.loc[dfplot.fraction > 1]}')
    ### Load geographic data
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    if extent.lower() not in ['usa','full','nation','us','country','all']:
        dfba = dfba.loc[val_r]
    ### Plot it
    dfplot = dfplot.merge(dftrans['trans_cap'], on=['r','rr','trtype'], how='left')
    dfplot['r_x'] = dfplot.r.map(dfba.x)
    dfplot['r_y'] = dfplot.r.map(dfba.y)
    dfplot['rr_x'] = dfplot.rr.map(dfba.x)
    dfplot['rr_y'] = dfplot.rr.map(dfba.y)
    ### Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=(14,8))
    dfba.plot(ax=ax, edgecolor='0.75', facecolor='none', lw=0.1)
    if thicklevel:
        dfmap[thicklevel].plot(ax=ax, edgecolor='C7', facecolor='none', lw=0.2)
    dfmap['interconnect'].plot(ax=ax, edgecolor='k', facecolor='none', lw=0.3)
    for i, row in dfplot.iterrows():
        ax.plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=cmap(row.fraction), alpha=alpha,
            lw=wscale*row['Val'], solid_capstyle='butt',
        )
    plots.addcolorbarhist(
        f=f, ax0=ax, data=dfplot.fraction.values,
        title=title, cmap=cmap,
        vmin=0., vmax=1., nbins=51,
        orientation='horizontal', labelpad=2.5, histratio=1.,
        cbarwidth=0.025, cbarheight=0.25,
        cbarbottom=0.15, cbarhoffset=-0.8,
    )
    ax.set_title(f'{os.path.basename(case)} ({year})', fontsize=10)
    ax.axis('off')
    return f, ax, dfplot


def map_net_imports(
        case, level='r',
        cmap=plt.cm.RdBu_r, yearmin=2020, nrows=3,
        vlim='shared', trans=False,
    ):
    """
    """
    ### Get outputs
    net_import_ann_rep = reeds.io.read_output(case, 'net_import_ann_rep')
    ## Convert to TWh
    net_import_ann_rep.Value /= 1e6
    years = [y for y in sorted(net_import_ann_rep.t.unique()) if y >= yearmin]
    hierarchy = reeds.io.get_hierarchy(case)

    ### Aggregate if necessary
    if level not in ['r','rb','ba']:
        net_import_ann_rep.r = net_import_ann_rep.r.map(hierarchy[level])
    net_import_ann_rep = net_import_ann_rep.groupby(['r','t']).Value.sum().unstack('t').fillna(0)
    if vlim == 'shared':
        _vlim = max(net_import_ann_rep.max().max(), abs(net_import_ann_rep.min().min()))
        vmax = dict(zip(years, [_vlim]*len(years)))
    else:
        vmax = {
            y: max(net_import_ann_rep[y].max(), abs(net_import_ann_rep[y].min()))
            for y in years
        }

    ### Set up plot
    _nrows, ncols, coords = plots.get_coordinates(years, nrows=nrows)
    dfmap = reeds.io.get_dfmap(case)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(13.33, 6.88), sharex=True, sharey=True,
        gridspec_kw={'hspace':-0.05, 'wspace':-0.05},
    )
    for year in years:
        df = dfmap[level].copy()
        df['net_import'] = net_import_ann_rep[year]
        df.dropna(subset='net_import', inplace=True)
        ## Outlines
        df.plot(
            ax=ax[coords[year]],
            facecolor='none', edgecolor='k', lw=0.1, zorder=10000)
        ## Data
        df.plot(
            ax=ax[coords[year]], column='net_import', cmap=cmap,
            legend=False,
            vmin=-vmax[year], vmax=vmax[year],
        )
        ## Formatting
        ax[coords[year]].set_title(year, y=0.9)
        if vlim != 'shared':
            plots.addcolorbarhist(
                f=f, ax0=ax[coords[year]], data=df.net_import,
                cmap=cmap, vmin=-vmax[year], vmax=vmax[year], histratio=0,
                cbarbottom=0.525, cbarheight=0.9,
            )

    ## Formatting
    if vlim == 'shared':
        plots.addcolorbarhist(
            f=f, ax0=ax[coords[year]], data=df.net_import,
            cmap=cmap, vmin=-vmax[year], vmax=vmax[year], histratio=0,
            cbarbottom=0.1, cbarheight=0.8, cbarleft=1.1,
            title='Net imports\n– exports\n[TWh/year]',
        )
    for row in range(nrows):
        for col in range(ncols):
            ax[row,col].axis('off')

    return f, ax


def plot_max_imports(
        case, colors=None, casenames=None,
        level='nercr', units='%', tstart=2020,
        grid=False, draw_limit=True,
    ):
    """Plot max hourly stress period net imports over time"""
    ### Parse inputs
    levell = level + level[-1]
    cases = case.split(',') if isinstance(case, str) else case
    if casenames is None:
        casenames = dict(zip(cases, [os.path.basename(c) for c in cases]))
    elif isinstance(casenames, list):
        casenames = dict(zip(cases, casenames))
    elif isinstance(casenames, str):
        casenames = dict(zip(cases, casenames.split(',')))

    if colors is None:
        colors = plots.rainbowmapper(cases)
    elif isinstance(colors, list):
        colors = dict(zip(cases, colors))
    elif isinstance(colors, str):
        colors = dict(zip(cases, colors.split(',')))

    _draw_limit = draw_limit and (level == 'nercr') and (len(cases) == 1)

    ### Get inputs
    dfmap = reeds.io.get_dfmap(cases[0])
    hierarchy = reeds.io.get_hierarchy(cases[0])

    ## Sort regions west to east
    regions = dfmap[level].loc[hierarchy[level].unique()].bounds.minx.sort_values().index
    ncols = len(regions)

    ## Aggregate
    if level == 'r':
        r2agg = pd.Series(index=hierarchy.index, data=hierarchy.index)
    else:
        r2agg = hierarchy[level].copy()

    ### Get results
    dictplot = {}
    for c in cases:
        flow = reeds.io.read_output(c, 'tran_flow_all_stress', valname='MW')
        flow[level] = flow.r.map(r2agg)
        flow[levell] = flow.rr.map(r2agg)

        tranloss = pd.read_csv(
            os.path.join(c,'inputs_case','tranloss.csv')
        ).rename(columns={'*r':'r'}).set_index(['r','rr','trtype']).squeeze(1)

        peakload = (
            pd.read_csv(os.path.join(c,'inputs_case','peakload.csv'))
            .set_index(['level','region']).loc[level].stack()
            .rename_axis(['r','t']).rename('MW')
            .reset_index().astype({'t':int}).set_index(['r','t']).squeeze()
        )

        if _draw_limit:
            ## Fraction
            try:
                firm_import_limit = pd.read_csv(
                    os.path.join(c, 'inputs_case', 'firm_import_limit.csv')
                ).rename(columns={'*nercr':'nercr'}).set_index(['nercr','t']).squeeze()
            except FileNotFoundError:
                print("firm_import_limit.csv not found, so it won't be plotted")
                _draw_limit = False

        net_import_h_stress_agg = (
            (flow.loc[flow[level] != flow[levell]])
            .set_index(['r','rr','trtype','h','t'])
        ).copy()
        ## Imports with losses
        net_import_h_stress_agg['MWin'] = (net_import_h_stress_agg.MW * (1 - tranloss)).dropna()
        ## Minus exports
        net_import_h_stress_agg['MWout'] = net_import_h_stress_agg.MW.copy()
        ###
        _max_import_stress_agg = {}
        for region in regions:
            _max_import_stress_agg[region] = (
                ## Imports with losses
                net_import_h_stress_agg.loc[net_import_h_stress_agg[levell]==region].MWin
                ## minus exports without losses
                .subtract(
                    net_import_h_stress_agg.loc[net_import_h_stress_agg[level]==region].MWout,
                    fill_value=0)
            ).groupby(['h','t']).sum().groupby('t').max()
        max_import_stress_agg = pd.concat(_max_import_stress_agg, names=('r',))

        ## Calculate ratio if necessary
        if units.lower() in ['percent','%','pct']:
            dfplot = max_import_stress_agg / peakload * 100
            ymax = 100
            if _draw_limit:
                firm_import_limit *= 100
        elif units.lower() in ['fraction','ratio','.']:
            dfplot = max_import_stress_agg / peakload
            ymax = 1
        elif units.upper() in ['MW','GW','TW']:
            scale = {'MW':1, 'GW':1, 'TW':1}
            dfplot = max_import_stress_agg.rename(units) * scale[units.upper()]
            ymax = dfplot.max()
            if _draw_limit:
                firm_import_limit * peakload.rename_axis(['nercr','t'])
        else:
            raise NotImplementedError(f"Unsupported units: {units}")
        dictplot[c] = dfplot

    ###### Plot it
    plt.close()
    f,ax = plt.subplots(
        2, ncols, sharex='row', sharey='row', figsize=(1.35*ncols, 6),
        gridspec_kw={'hspace':0.1, 'height_ratios':[0.2,1]},
    )
    for c in cases:
        for col, region in enumerate(regions):
            ax[1,col].plot(
                dictplot[c].loc[region].index, dictplot[c].loc[region].values,
                color=colors[c], label=casenames[c],
            )
    ## Formatting
    for col, region in enumerate(regions):
        ax[1,col].set_title(region, weight='bold')
        ax[1,col].set_xlabel(None)
        ax[1,col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(20))
        ax[1,col].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
        ax[1,col].yaxis.set_major_locator(mpl.ticker.MultipleLocator(int(np.ceil(ymax/5))))
        ax[1,col].yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
        if grid:
            ax[1,col].grid(axis='y', which='major', ls=(0, (5, 5)), c='0.6', lw=0.3)
            ax[1,col].grid(axis='y', which='minor', ls=(0, (5, 10)), c='0.85', lw=0.3)

        ## Maps at top
        dfmap[level].plot(ax=ax[0,col], facecolor='0.99', edgecolor='0.75', lw=0.2)
        dfmap[level].loc[[region]].plot(ax=ax[0,col], facecolor='k', edgecolor='none')
        ax[0,col].axis('off')
        ax[0,col].patch.set_facecolor('none')

        ## Limit if required
        if _draw_limit and (region in firm_import_limit):
            ax[1,col].plot(
                firm_import_limit.loc[region].index, firm_import_limit.loc[region].values,
                color='k', ls='--', lw=0.75, label='_nolabel',
            )

    ### Custom legend
    handles = ([
        mpl.patches.Patch(
            facecolor=colors[c], edgecolor='none', label=casenames[c])
        for c in cases[::-1]
    ])

    if len(handles) > 1:
        _leg = ax[1,-1].legend(
            handles=handles,
            loc='upper left', bbox_to_anchor=(-0.05,1.02),
            fontsize='large', frameon=True, edgecolor='none', framealpha=1,
            handletextpad=0.3, handlelength=0.7,
            ncol=1, labelspacing=0.5,
        )

    ## Formatting
    ax[1,0].set_ylabel(f'Max net imports during stress periods [{units}]')
    _ymax = 1 if ((ymax is None) and (ax[1,0].get_ylim()[1] < 1)) else ymax
    ax[1,0].set_ylim(0, _ymax)
    ax[1,0].set_xlim(tstart, None)
    plots.despine(ax)
    plt.draw()
    plots.shorten_years(ax[1,0], start_shortening_in=2021)

    return f, ax, (pd.concat(dictplot, names=('case',)) if len(cases) > 1 else dfplot)


def plot_vresites_transmission(
        case, year=2050, crs='ESRI:102008',
        routes=True, wscale=1.5, show_overlap=False,
        subtract_baseyear=None,
        alpha=0.25, colors='k',
        techs=['upv','wind-ons','wind-ofs'],
        cm={'wind-ons':plt.cm.Blues, 'upv':plt.cm.Reds, 'wind-ofs':plt.cm.Purples},
        zorder={'wind-ons':-20002,'upv':-20001,'wind-ofs':-20000},
        cbarhoffset={'wind-ons':-0.8, 'upv':0.0, 'wind-ofs':0.8},
        label={'wind-ons':'Land-based wind [GW]',
               'upv':'Photovoltaics [GW]',
               'wind-ofs':'Offshore wind [GW]'},
        vmax={'upv':0.4, 'wind-ons':0.4, 'wind-ofs':0.6},
        trans_scale=True,
        show_transmission=True,
        title=True,
    ):
    """
    """
    ### Get the BA map
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    ### Get the lakes
    try:
        lakes = gpd.read_file(
            os.path.join(reeds_path,'inputs','shapefiles','greatlakes.gpkg')).to_crs(crs)
    except FileNotFoundError as err:
        print(err)
    
    ### Get the reeds_to_rev.py outputs
    cap = {}
    for tech in techs:
        try:
            cap[tech] = (
                pd.read_csv(os.path.join(case, 'outputs', f'df_sc_out_{tech}_reduced.csv'))
                .rename(columns={'built_capacity':'capacity_MW'})
            )
            cap[tech]['geometry'] = cap[tech].apply(
                lambda row: shapely.geometry.Point(row.longitude, row.latitude),
                axis=1)
            cap[tech] = gpd.GeoDataFrame(cap[tech]).set_crs('EPSG:4326').to_crs(crs)
            ## Convert from point to polygons (raster is 11.52 km but include a little extra)
            cap[tech]['geometry'] = cap[tech].buffer(11530/2, cap_style='square')

        except FileNotFoundError as err:
            print(err)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(8,8), dpi=600)
    dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=0.1, zorder=100000)
    dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.25, zorder=100001)
    try:
        lakes.plot(ax=ax, edgecolor='#2CA8E7', facecolor='#D3EFFA', lw=0.2, zorder=-1)
    except NameError:
        pass

    for tech in cap:
        legend_kwds = {
            'shrink':0.5, 'pad':0.05,
            'label':label[tech],
            'orientation':'horizontal',
        }

        dfplot = cap[tech].loc[cap[tech].year==year].sort_values('capacity_MW')
        dfplot['GW'] = dfplot['capacity_MW'] / 1000

        dfplot.plot(
            ax=ax, column='GW', cmap=cm[tech],
            lw=0,
            legend=False, legend_kwds=legend_kwds,
            vmin=0, vmax=vmax[tech], zorder=zorder[tech],
        )

        plots.addcolorbarhist(
            f=f, ax0=ax, data=dfplot.GW.values, title=legend_kwds['label'], cmap=cm[tech],
            vmin=0., vmax=vmax[tech], nbins=101,
            orientation='horizontal', labelpad=2.25, cbarbottom=-0.01, histratio=1.,
            cbarwidth=0.025, cbarheight=0.25, cbarhoffset=cbarhoffset[tech],
        )

    ### Transmission
    if show_transmission:
        plot_trans_onecase(
            case=case, pcalabel=False, wscale=wscale,
            yearlabel=False, year=year,
            alpha=alpha, colors=colors,
            f=f, ax=ax,
            title=False, scale=False,
            routes=routes, tolerance=1000,
            subtract_baseyear=subtract_baseyear,
            show_overlap=show_overlap,
            crs=crs, show_converters=0,
        )
    ### Transmission scale
    if show_transmission and trans_scale:
        ymin = ax.get_ylim()[0]
        xmin = ax.get_xlim()[0]
        if routes or (not show_overlap):
            gpd.GeoSeries(
                shapely.geometry.LineString([(xmin*0.8,ymin*0.6),(xmin*0.6,ymin*0.6)])
            ).buffer(wscale*10e3).plot(
                ax=ax, color=(colors if isinstance(colors,str) else 'k'), alpha=alpha)
        else:
            ax.plot(
                [xmin*0.8,xmin*0.6], [ymin*0.6, ymin*0.6],
                color=(colors if isinstance(colors,str) else 'k'),
                lw=wscale*10e3, solid_capstyle='butt', alpha=alpha,
            )
        ax.annotate(
            'Transmission\n10 GW', (xmin*0.7, ymin*0.66),
            ha='center', va='top', weight='bold', fontsize='large')

    ### Formatting
    if title:
        ax.annotate(
            '{} ({})'.format(os.path.basename(case), year),
            (0.1,1), xycoords='axes fraction', fontsize=10)
    ax.axis('off')

    return f,ax


def plot_prmtrade(
        case, year=2050, vmax=10e3,
        cm=plt.cm.inferno_r, wscale=7, alpha=0.8,
        f=None, ax=None, dpi=150,
    ):
    """
    Plot PRM trading by ccseason (for capacity credit) or average flow during stress periods
    """
    sw = reeds.io.get_switches(case)

    ### Load results, aggregate over transmission types
    if int(sw.get('GSw_PRM_CapCredit', 1)):
        dfplot = reeds.io.read_output(case, 'captrade', valname='MW')
        dfplot = dfplot.loc[dfplot.t==year].groupby(['ccseason','r','rr'], as_index=False).MW.sum()
    else:
        ### For stress periods take the average flow over each period
        dfplot = reeds.io.read_output(case, 'tran_flow_stress', valname='MW')
        dfplot['ccseason'] = (
            dfplot.h.str.split('h', expand=True)[0]
            ## Convert to timestamp
            .map(lambda x: reeds.timeseries.h2timestamp(x+'h01').strftime('%Y-%m-%d'))
        )
        dfplot = (
            dfplot.loc[dfplot.t==year]
            ## Sum over trtypes
            .groupby(['r','rr','ccseason','h'], as_index=False).MW.sum()
            ## Average over h's in ccseason
            .groupby(['r','rr','ccseason'], as_index=False).MW.mean()
        )
    dfplot['primary_direction'] = 1

    ### Get the BA map
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    ## Downselect to modeled regions
    val_r = pd.read_csv(
        os.path.join(case,'inputs_case','val_r.csv'), header=None,
    ).squeeze(1).values.tolist()
    dfba = dfba.loc[val_r].copy()

    if sw.get('GSw_RegionResolution', 'ba') != 'county':
        endpoints = (
            gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','transmission_endpoints'))
            .set_index('ba_str'))
        endpoints['x'] = endpoints.centroid.x
        endpoints['y'] = endpoints.centroid.y
        dfba['x'] = dfba.index.map(endpoints.x)
        dfba['y'] = dfba.index.map(endpoints.y)

    ### Get scaling and layout
    _vmax = dfplot.MW.abs().max() if vmax in [None, 0, 0.] else vmax
    if int(sw.get('GSw_PRM_CapCredit', 1)):
        ccseasons = pd.read_csv(
            os.path.join(case, 'inputs_case', 'rep', 'h_dt_szn.csv')
        ).ccseason.unique()
    else:
        ccseasons = dfplot.ccseason.sort_values().unique()
    nrows, ncols, coords = plots.get_coordinates(ccseasons)
    
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(4*ncols,3*nrows), dpi=dpi,
        gridspec_kw={'wspace':0.0,'hspace':-0.05})
    for ccseason in ccseasons:
        ### Background
        dfba.plot(ax=ax[coords[ccseason]], edgecolor='0.5', facecolor='none', lw=0.1)
        dfstates.plot(ax=ax[coords[ccseason]], edgecolor='k', facecolor='none', lw=0.2)

        ### Average prmtrade
        dfszn = dfplot.loc[dfplot.ccseason==ccseason].copy()
        for i, row in dfszn.iterrows():
            lineflow, primary_direction = row[['MW','primary_direction']]
            if lineflow >= 0:
                startx, starty = dfba.loc[row.r,'x'], dfba.loc[row.r,'y']
                delx = (dfba.loc[row.rr,'x'] - dfba.loc[row.r,'x'])
                dely = (dfba.loc[row.rr,'y'] - dfba.loc[row.r,'y'])
            else:
                startx, starty = dfba.loc[row.rr,'x'], dfba.loc[row.rr,'y']
                delx = (dfba.loc[row.r,'x'] - dfba.loc[row.rr,'x'])
                dely = (dfba.loc[row.r,'y'] - dfba.loc[row.rr,'y'])
            arrow = mpl.patches.FancyArrow(
                startx, starty, delx, dely,
                width=abs(lineflow)*wscale,
                length_includes_head=True,
                head_width=abs(lineflow)*wscale*2.,
                head_length=abs(lineflow)*wscale*1.0,
                lw=0, color=cm(abs(lineflow)/_vmax), alpha=alpha,
                ## Plot the primary direction on bottom since it's thicker
                zorder=(1e6 if primary_direction else 2e6),
                clip_on=False,
            )
            ax[coords[ccseason]].add_patch(arrow)
        ax[coords[ccseason]].axis('off')
        ax[coords[ccseason]].set_title(ccseason, y=0.9, fontsize='large')

    plots.trim_subplots(ax=ax, nrows=nrows, ncols=ncols, nsubplots=len(ccseasons))
    return f, ax


def plot_average_flow(
        case, year=2050, network='trans',
        cm=plt.cm.inferno_r, wscale=7, alpha=0.8,
        trtypes=['AC','LCC','VSC','H2'],
        simpletypes={'AC_init':'AC','LCC_init':'LCC','B2B_init':'LCC','B2B':'LCC'},
        crs='ESRI:102008', scale=True,
        f=None, ax=None, extent='modeled',
        both_directions=True, debug=False, title=False,
        drawzones=True, thickborders='none', thickness=0.5, drawstates=True,
    ):
    """
    NOTE: Currently using max flow as max value but should instead
         plot as CF compared to line capacity (for both_directions = True and False).
    """
    ### Parse some inputs
    if ('h2' in network.lower()) or ('hydrogen' in network.lower()):
        label = 'kT/day'
        labelscale = 24/1000
    else:
        label = 'GW'
        labelscale = 0.001
    ### Get the BA map
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    val_r = pd.read_csv(
        os.path.join(case,'inputs_case','val_r.csv'), header=None,
    ).squeeze(1).values.tolist()
    if extent.lower() not in ['usa','full','nation','us','country','all']:
        dfba = dfba.loc[val_r]

    if thickborders not in [None,'','none','None',False]:
        hierarchy = reeds.io.get_hierarchy(case)
        if thickborders in hierarchy:
            dfthick = dfba.copy()
            dfthick[thickborders] = hierarchy[thickborders]
            dfthick.geometry = dfthick.buffer(0.)
            dfthick = dfthick.dissolve(thickborders)

    ### Load results
    hours = pd.read_csv(
        os.path.join(case,'inputs_case', 'rep', 'numhours.csv'),
        header=0, names=['h','hours'], index_col='h',
    ).squeeze(1)
    if both_directions:
        if ('h2' in network.lower()) or ('hydrogen' in network.lower()):
            flow = (
                reeds.io.read_output(case, 'h2_trans_flow', valname='Val')
            ).assign(trtype='H2')
        else:
            flow = reeds.io.read_output(case, 'tran_flow_rep', valname='Val')
        ## Convert to plot units, then sum over hours
        flow.Val *= labelscale
        flow['hours'] = flow.h.map(hours)
        flow['Valh'] = flow.Val * flow.hours
        ## Separate flow by positive and negative timeslices
        dfplot = {}
        dfplot['pos'] = (
            flow.loc[flow.Valh >= 0]
            .groupby(['r','rr','trtype','t'], as_index=False).Valh.sum())
        dfplot['neg'] = (
            flow.loc[flow.Valh < 0]
            .groupby(['r','rr','trtype','t'], as_index=False).Valh.sum())
        dfplot = pd.concat(dfplot, axis=0, names=['direction','index'])
        ## Convert back to MW using hours in year
        dfplot = (
            dfplot.groupby(['direction','r','rr','trtype','t']).Valh.sum()
            / hours.sum()
        ).rename('Val').reset_index()
        groupcols = ['direction','r','rr']

    else:
        dfplot = reeds.io.read_output(case, 'tran_flow_rep_ann', valname='Val')
        dfplot.Val /= hours.sum()
        groupcols = ['r','rr']

    ### Downselect
    dfplot.trtype = dfplot.trtype.replace(simpletypes)
    dfplot = (
        dfplot
        .loc[dfplot.trtype.isin(trtypes) & (dfplot.t==year)]
        .groupby(groupcols, as_index=False).Val.sum()
    )

    ### Get the primary direction
    if both_directions:
        primary_direction = []
        df = dfplot.set_index(['direction','r','rr']).Val
        for (direction,r,rr), val in df.items():
            other_direction = 'pos' if direction == 'neg' else 'neg'
            try:
                if abs(val) > abs(df.loc[other_direction,r,rr]):
                    primary_direction.append(1)
                else:
                    primary_direction.append(0)
            ### If the other direction doesn't exist, the current direction is primary
            except KeyError:
                primary_direction.append(1)

        dfplot['primary_direction'] = primary_direction
    else:
        dfplot['primary_direction'] = 1

    ### Get scaling
    maxflow = dfplot.Val.abs().max()

    ### Transmission capacity
    if (not f) or (not ax):
        plt.close()
        f,ax = plt.subplots(figsize=(12,8), dpi=150)

    if drawzones:
        dfba.plot(ax=ax, edgecolor='0.75', facecolor='none', lw=0.2)
    if drawstates:
        dfstates.plot(ax=ax, edgecolor='0.7', facecolor='none', lw=0.4)
    if thickborders not in [None,'','none','None',False]:
        dfthick.plot(ax=ax, edgecolor='C7', facecolor='none', lw=thickness)

    ### Average power flow
    for i, row in dfplot.iterrows():
        lineflow, primary_direction = row[['Val','primary_direction']]
        if lineflow >= 0:
            startx, starty = dfba.loc[row.r,'x'], dfba.loc[row.r,'y']
            delx = (dfba.loc[row.rr,'x'] - dfba.loc[row.r,'x'])
            dely = (dfba.loc[row.rr,'y'] - dfba.loc[row.r,'y'])
        else:
            startx, starty = dfba.loc[row.rr,'x'], dfba.loc[row.rr,'y']
            delx = (dfba.loc[row.r,'x'] - dfba.loc[row.rr,'x'])
            dely = (dfba.loc[row.r,'y'] - dfba.loc[row.rr,'y'])
        arrow = mpl.patches.FancyArrow(
            startx, starty, delx, dely,
            width=abs(lineflow)*wscale,
            length_includes_head=True,
            head_width=abs(lineflow)*wscale*2.,
            head_length=abs(lineflow)*wscale*1.0,
            lw=0, color=cm(abs(lineflow)/maxflow), alpha=alpha,
            ## Plot the primary direction on bottom since it's thicker
            zorder=(1e6 if primary_direction else 2e6),
            clip_on=False,
        )
        ax.add_patch(arrow)

    ### Scale
    if scale:
        (startx, starty, delx, dely) = (-2.0e6, -1.2e6, 0.5e6, 0e6)
        arrow = mpl.patches.FancyArrow(
            startx, starty, delx, dely,
            width=maxflow*wscale,
            length_includes_head=True,
            head_width=maxflow*wscale*2.,
            head_length=maxflow*wscale*1.0,
            lw=0, color=cm(maxflow/maxflow), alpha=alpha,
            clip_on=False,
        )
        ax.add_patch(arrow)
        ax.annotate(
            f'{maxflow:.0f} {label}',
            # (startx+delx/2, starty+dely/2), color='0.8', va='center',
            # (startx+delx/2, starty+dely/2+(maxflow*wscale/2)+0.08e6),
            (startx+delx+0.02e6, starty+dely/2), ha='left', va='center',
            color='k', fontsize=14,
            annotation_clip=False,
        )

    ### Formatting
    if title:
        ax.annotate(
            f'{os.path.basename(case)} {year} ({",".join(trtypes)})',
            (0.1,1.0), xycoords='axes fraction', ha='left', va='top')
    ax.axis('off')

    if debug:
        return f, ax, dfplot
    else:
        return f, ax


def get_transfer_peak_fraction(case, level='transreg', tstart=2020, everything=False):
    """Get ratio of interregional transfer capacity to peak demand by region level"""
    ### Implied inputs
    levell = level + level[-1]

    ### Shared inputs
    hierarchy = reeds.io.get_hierarchy(case)
    dfmap = reeds.io.get_dfmap(case)

    ## Plot regions from west to east
    regions = dfmap[level].bounds.minx.sort_values().index

    ### Run results
    dfin_trans_r = reeds.io.read_output(case, 'tran_out', valname='MW')
    dfin_trans_r[f'inter_{level}'] = (
        dfin_trans_r.r.map(hierarchy[level])
        != dfin_trans_r.rr.map(hierarchy[level])
    ).astype(int)

    dftrans = dfin_trans_r.loc[
        (dfin_trans_r.t >= tstart)
        & (dfin_trans_r[f'inter_{level}'] == 1)
    ].copy()
    dftrans[level] = dftrans.r.map(hierarchy[level])
    dftrans[levell] = dftrans.rr.map(hierarchy[level])

    ### Get import/export capacity
    transfercap = {}
    for region in regions:
        transfercap[region] = (
            dftrans.loc[
                (dftrans[level]==region) | (dftrans[levell]==region)
            ].groupby('t').MW.sum())
    transfercap = pd.concat(transfercap, axis=1)

    ### Get peak load from hourly demand
    dfpeak = pd.read_csv(
        os.path.join(case,'inputs_case','peakload.csv'),
        index_col=['level','region'],
    ).rename(columns=int).loc[level].T
    ### Get the fraction
    dfout = (transfercap / dfpeak.loc[tstart:])[regions]

    if everything:
        return {'fraction':dfout, 'transfercap':transfercap, 'peak':dfpeak.loc[tstart:]}
    else:
        return dfout


def plot_interreg_transfer_cap_ratio(
        case, colors=None, casenames=None,
        level='transreg', tstart=2020,
        f=None, ax=None,
        grid=True, ymax=None,
    ):
    """Plot interregional transfer capability / peak demand over time"""
    ### Inputs for debugging
    # case = (
    #     '/Users/pbrown/github2/ReEDS-2.0/runs/'
    #     'v20240212_transopM0_WECC_CPNP_GP1_TFY2035_PTL2035_TRc_MITCg0p3')
    # casenames = 'base'
    # level = 'transreg'; tstart=2020;
    # f=None; ax=None; grid=True; ymax=3; colors=None

    ### Parse inputs
    cases = case.split(',') if isinstance(case, str) else case
    if casenames is None:
        casenames = dict(zip(cases, [os.path.basename(c) for c in cases]))
    elif isinstance(casenames, list):
        casenames = dict(zip(cases, casenames))
    elif isinstance(casenames, str):
        casenames = dict(zip(cases, casenames.split(',')))

    if colors is None:
        colors = plots.rainbowmapper(cases)
    elif isinstance(colors, list):
        colors = dict(zip(cases, colors))
    elif isinstance(colors, str):
        colors = dict(zip(cases, colors.split(',')))

    ### Get results
    dfplot = {c: get_transfer_peak_fraction(c, level, tstart) for c in cases}
    dfmap = reeds.io.get_dfmap(cases[0])

    ### Implied inputs
    regions = dfplot[cases[0]].columns
    ncols = len(regions)
    if ncols == 1:
        raise NotImplementedError(
            "Only one region modeled so can't plot interregional transmission")

    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(
            2, ncols, sharex='row', sharey='row', figsize=(1.35*ncols, 6),
            gridspec_kw={'hspace':0.1, 'height_ratios':[0.2,1]},
        )
    for c in cases:
        for col, region in enumerate(regions):
            ax[1,col].plot(
                dfplot[c].index, dfplot[c][region].values, color=colors[c],
                label=casenames[c],
            )
    ## Formatting
    for col, region in enumerate(regions):
        ax[1,col].set_title(region, weight='bold')
        ax[1,col].set_xlabel(None)
        ax[1,col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(20))
        ax[1,col].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
        ax[1,col].yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5))
        ax[1,col].yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1))
        if grid:
            ax[1,col].grid(axis='y', which='major', ls=(0, (5, 5)), c='0.6', lw=0.3)
            ax[1,col].grid(axis='y', which='minor', ls=(0, (5, 10)), c='0.85', lw=0.3)

        ## Maps at top
        dfmap[level].plot(ax=ax[0,col], facecolor='0.99', edgecolor='0.75', lw=0.2)
        dfmap[level].loc[[region]].plot(ax=ax[0,col], facecolor='k', edgecolor='none')
        ax[0,col].axis('off')
        ax[0,col].patch.set_facecolor('none')

    ### Custom legend
    handles = ([
        mpl.patches.Patch(
            facecolor=colors[c], edgecolor='none', label=casenames[c])
        for c in cases[::-1]
    ])

    _leg = ax[1,-1].legend(
        handles=handles,
        loc='upper left', bbox_to_anchor=(-0.05,1.02),
        fontsize='large', frameon=True, edgecolor='none', framealpha=1,
        handletextpad=0.3, handlelength=0.7,
        ncol=1, labelspacing=0.5,
    )

    ## Formatting
    ax[1,0].set_ylabel('Transfer capability\n/ peak demand [fraction]')
    _ymax = 1 if ((ymax is None) and (ax[1,0].get_ylim()[1] < 1)) else ymax
    ax[1,0].set_ylim(0, _ymax)
    ax[1,0].set_xlim(dfplot[c].index.min(), dfplot[c].index.max())
    plots.despine(ax)
    plt.draw()
    plots.shorten_years(ax[1,0], start_shortening_in=2021)

    return f, ax, dfplot


###### Operations animation
def animate_dispatch(
        case, year=2050, chunklength=4, nodeloc='centroid',
        width=1e5, height=0.5e4, tscale=0.5, figpath=None,
        overwrite=False,
    ):
    """
    # Notes
    * The animation is created with ffmpeg (https://ffmpeg.org/).
      If you're on a mac and have brew, you can install it with `brew install ffmpeg`.
    # Inputs
    nodeloc: ['centroid','endpoint']
    width: bar width in meters
    height: bar height in [meters/GW]
    tscale: transmission linewidth in [points/GW]
    """
    import subprocess
    from tqdm import tqdm

    ###### Define tech aggregations and colors
    aggtechs = {
        **{f'battery_{i}': 'battery' for i in [2,4,6,8,10,12,24,48,72,100]},
        **{f'wind-ons_{i}': 'wind-ons' for i in range(1,11)},
        **{f'wind-ofs_{i}': 'wind-ofs' for i in range(1,11)},
        **{f'upv_{i}': 'pv' for i in range(1,11)},
        **{
            'battery_li':'battery',
            'distpv':'pv',
            'lfill-gas':'biopower',
            'Nuclear':'nuclear',
            'pumped-hydro':'pumped-hydro',
            'hydND':'hydro',
            'hydUD':'hydro',
            'hydUND':'hydro',
            'hydNPND':'hydro',
            'hydED':'hydro',
            'hydEND':'hydro',
            'H2-CT':'h2',
            'Gas-CT_H2-CT':'h2',
            'Gas-CC_H2-CC':'h2',
        },
    }
    try:
        bokehcolors = pd.read_csv(
            os.path.join(reeds_path,'bokehpivot','in','reeds2','tech_style.csv'),
            index_col='order').squeeze(1)
    except FileNotFoundError:
        bokehcolors = pd.read_csv(
            os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
            index_col='order').squeeze(1)
    plotcolors = {
        'nuclear': bokehcolors['nuclear'],
        'hydro': bokehcolors['hydro'],
        'biopower': bokehcolors['biopower'],
        'h2': bokehcolors['h2-ct'],
        'wind-ons': bokehcolors['wind-ons'],
        'wind-ofs': bokehcolors['wind-ofs'],
        'pv': bokehcolors['upv'],
        'battery_li': bokehcolors['battery_li'],
        'pumped-hydro': bokehcolors['pumped-hydro'],
    }

    ###### Make the figure path
    framepath = os.path.join(figpath,'animation')
    os.makedirs(framepath, exist_ok=True)

    ###### Create the index
    fulltimeindex = pd.date_range(
        '2012-01-01', '2013-01-01',
        inclusive='left', freq='h', tz='Etc/GMT+6',
    )[:8760]
    if chunklength == 4:
        timeindex = fulltimeindex[2::chunklength]
    elif chunklength == 3:
        timeindex = fulltimeindex[1::chunklength] + pd.Timedelta('30min')
    elif chunklength == 2:
        timeindex = fulltimeindex[1::chunklength]
    else:
        timeindex = fulltimeindex

    ###### Load the data
    ##### Map
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    rs = dfba.index.values

    ##### Generation
    gen = reeds.io.read_output(case, 'gen_h', valname='GW')
    gen = gen.loc[gen.t==year].copy()
    gen.GW /= 1000
    gen.i = gen.i.map(lambda x: aggtechs.get(x,x))
    gen = gen.groupby(['h','r','i']).GW.sum()

    ##### Demand
    demand = pd.read_csv(
        os.path.join(case,'inputs_case','load_h_hourly.csv'),
        index_col=['h','r']
    )[str(year)] / 1000

    ##### Transmission capacity
    transcap = reeds.io.read_output(case, 'tran_out', valname='GW')
    transcap = transcap.loc[transcap.t==year].copy()
    transcap.GW /= 1000
    transcap = transcap.groupby(['r','rr']).GW.sum()

    ##### Transmission flow
    flow = reeds.io.read_output(case, 'tran_flow_rep', valname='GW')
    flow = flow.loc[flow.t==year].copy()
    flow.GW /= 1000
    flow = flow.groupby(['h','r','rr']).GW.sum()

    ###### Define the plotting function
    def plotframe(h, overwrite=overwrite):
        """
        """
        savename = os.path.join(framepath,f"h{int(h.strip('h')):0>4}.png")
        if (not overwrite) and os.path.exists(savename):
            return None
        ###### Inputs
        tpre = 'centroid_' if nodeloc == 'centroid' else ''
        
        ###### Plot it
        ### Background map
        # https://stackoverflow.com/questions/
        # 28757348/how-to-clear-memory-completely-of-all-matplotlib-plots
        f,ax = plt.subplots(num=1, clear=True, figsize=(10,7))
        dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.5)
        ax.axis('off')

        ### Get limits (for plot placement)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        ###### Transmission
        for ((r,rr),GW) in transcap.items():
            ### Capacity
            ax.plot(
                [dfba.loc[r,tpre+'x'], dfba.loc[rr,tpre+'x']],
                [dfba.loc[r,tpre+'y'], dfba.loc[rr,tpre+'y']],
                lw=GW*tscale, solid_capstyle='butt', c='0.9',#c=plt.cm.tab20(5),#c='0.8',
                zorder=-10000,
            )
            ### Flow
            if (h,r,rr) in flow:
                GW = flow[h,r,rr]
            elif (h,rr,r) in flow:
                GW = -flow[h,rr,r]
            else:
                continue

            tail = (dfba.loc[r,tpre+'x'], dfba.loc[r,tpre+'y'])
            head = (dfba.loc[rr,tpre+'x'], dfba.loc[rr,tpre+'y'])
            pol = ('pos' if GW >= 0 else 'neg')
            ax.annotate(
                '', color='k',
                xy=(head if pol=='pos' else tail),
                xytext=(tail if pol=='pos' else head),
                arrowprops={
                    'width':abs(GW)*tscale, 'headwidth':abs(GW)*tscale,
                    'facecolor':'k', 'lw':0, 'edgecolor':'none',
                },
                zorder=-9000,
            )

        ###### Generation stacks
        for r in rs:
            try:
                df = gen[h][r].to_frame().T
            except KeyError:
                continue
            if df.empty:
                continue
            ### Get coordinates
            x0, bottom = dfba.loc[r,['centroid_x','centroid_y']]
            ### Scale it
            df = (df * height)
            df.index = [x0]
            ### Plot it
            plots.stackbar(
                df=df, ax=ax, colors=plotcolors, width=width, net=False,
                bottom=bottom,
            )
            ### Zero line
            ax.plot(
                [x0-width/2,x0+width/2], [bottom]*2,
                c='k',solid_capstyle='butt',lw=0.8,ls='--')
            ### Demand
            ax.bar(
                x=[x0], bottom=[bottom], height=demand[h,r]*height, width=width,
                color='k', alpha=0.2, zorder=10000,
            )
            ax.plot(
                [x0-width/2,x0+width/2], [bottom+demand[h,r]*height]*2,
                c='k',solid_capstyle='butt',lw=0.8,ls='-')

        ###### Label
        ax.annotate(
            timeindex[int(h.strip('h'))-1].strftime('%Y-%m-%d\n%H:%M:00 CST'),
            (-2e6, -1.2e6), ha='left', va='bottom', fontsize=12,
        )
        ax.set_xlim(xmin,xmax)
        ax.set_ylim(ymin,ymax)
        ###### Save it
        plt.savefig(savename)

    ###### Run it
    hs = [f'h{h+1}' for h in range(len(timeindex))]
    for h in tqdm(hs):
        plotframe(h)

    ###### Combine the frames into an animation
    command = (
        "ffmpeg "
        "-framerate {fps} "
        "-pattern_type glob "
        "-i {figpath}{sep}animation{sep}h*.png "
        "-c:v libx264 "
        "-pix_fmt yuv420p "
        "-vf crop=trunc(iw/2)*2:trunc(ih/2)*2 "
        "{figpath}{sep}animation.mp4"
    ).format(
        fps=24//chunklength, sep=os.sep, figpath=figpath,
    )
    subprocess.call(command.split())


def map_trans_agg(
        case, agglevel='transreg', startyear=2020,
        f=None, ax=None, dpi=None,
        wscale='auto', width_inter=3e5, width_intra_frac=0.5, width_step=3,
        drawstates=0., drawzones=0., scale_loc=(2.5,-1.5), scale_val=100,
        drawgrid=False, drawregions=1.,
    ):
    """
    # Notes
    * Currently only works for agglevel='transreg'; to use other agglevels, add the
      coordinates for the interface boundaries to
      postprocessing/plots/transmission-interface-coords.csv
    
    # TO CONSIDER
    * Would be neat to build a stacked bar chart where the length of each sub-bar is the
      length of the line it's associated with, and the width would be the GW. Sort by length
      so you get something like a population distribution.
    """
    ### Plot settings
    width_intra = width_inter * width_intra_frac

    ###### Get case inputs and outputs
    hierarchy = reeds.io.get_hierarchy(case)

    tran_out = reeds.io.read_output(case, 'tran_out', valname='GW')
    tran_out.GW /= 1000

    ### Map transmission capacity to agglevel
    tran_out['aggreg1'] = tran_out.r.map(hierarchy[agglevel])
    tran_out['aggreg2'] = tran_out.rr.map(hierarchy[agglevel])
    tran_out_agg = tran_out.copy()
    ## Sort aggreg's alphabetically
    for i, row in tran_out_agg.iterrows():
        if row.aggreg2 < row.aggreg1:
            tran_out_agg.loc[i,'aggreg1'], tran_out_agg.loc[i,'aggreg2'] = (
                tran_out_agg.loc[i,'aggreg2'], tran_out_agg.loc[i,'aggreg1'])
    tran_out_agg = tran_out_agg.groupby(
        ['aggreg1','aggreg2','trtype','t'], as_index=False).GW.sum()

    ### Get region map
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    dfba[agglevel] = dfba.index.map(hierarchy[agglevel])
    dfreg = dfba.copy()
    dfreg['geometry'] = dfreg.buffer(0.)
    dfreg = dfreg.dissolve(agglevel)
    dfreg['x'] = dfreg.centroid.x
    dfreg['y'] = dfreg.centroid.y

    ### Get transmission colors
    trtypes = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
        index_col='raw')['display']
    transcolors = pd.read_csv(
            os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
            index_col='order')['color']
    transcolors = pd.concat([transcolors, trtypes.map(transcolors)])

    rename = ['AC_init','B2B_init','LCC_init','AC','LCC','VSC']
    for c in rename:
        if c.lower() in transcolors:
            transcolors[c] = transcolors[c.lower()]

    ###### Get line drawing settings
    dfcorridors = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','plots','transmission-interface-coords.csv'),
        index_col=['level','region1','region2'],
    ).drop('drop',axis=1).loc[agglevel].reset_index()
    dfcorridors[['x','y']] *= 1e6
    ### Add reverse direction
    dfcorridors = pd.concat([
        dfcorridors,
        dfcorridors.assign(region1=dfcorridors.region2).assign(region2=dfcorridors.region1)
    ], axis=0).set_index(['region1','region2'])

    dfcorridors = dfcorridors.loc[~dfcorridors.index.duplicated()].copy()

    ### Aggregated
    dfplot = tran_out_agg.loc[tran_out_agg.t >= startyear].pivot(
        index=['aggreg1','aggreg2','t'],columns='trtype',values='GW'
    ).reindex(['B2B','AC','LCC','VSC'],axis=1).dropna(axis=1, how='all')

    ### Plot settings
    width_year = width_inter / len(tran_out_agg.t.unique())
    yearspan = tran_out_agg.t.max() - startyear
    if wscale in ['auto','scale','default',None,'','max']:
        df = dfplot.reset_index()
        capmax = max([
            (df.loc[df.aggreg1==df.aggreg2].groupby('t').sum().sum(axis=1).max()
             if width_intra else 0),
            df.loc[df.aggreg1!=df.aggreg2].groupby('t').sum().sum(axis=1).max(),
        ])
        _wscale = 3e6 / capmax * 0.95
    else:
        _wscale = wscale

    ###### Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=(12,8),dpi=dpi)
    ### Plot background
    if drawregions:
        dfreg.plot(ax=ax, facecolor='none', edgecolor='k', lw=drawregions)
        if drawstates:
            dfstates.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawstates)
        if drawzones:
            dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawzones)

    ### Transmission
    for (r1,r2), (x,y,angle) in dfcorridors.iterrows():
        if (r1 == r2) and (not width_intra_frac):
            continue
        try:
            df = dfplot.loc[r1].loc[r2] * _wscale
        except KeyError:
            try:
                df = dfplot.loc[r2].loc[r1] * _wscale
            except KeyError:
                continue
        df.index = (
            (df.index - startyear - yearspan/2)
            * width_year / width_step
            * (width_intra_frac if r1 == r2 else 1)
        )
        y -= df.sum(axis=1).max() / 2

        plots.stackbar(
            df=df,
            ax=ax, colors=transcolors,
            width=(width_year * (width_intra_frac if r1 == r2 else 1)),
            net=False, bottom=y, x0=x,
        )

    ### Scale
    if scale_loc:
        ### Get the total intra- and inter-zone capacity in GW
        dfscale = dfplot.reset_index()
        dfintra = (
            dfscale.loc[dfscale.aggreg1 == dfscale.aggreg2]
            .drop(['aggreg1','aggreg2'],axis=1).groupby('t').sum()
        ) * _wscale
        dfinter = (
            dfscale.loc[dfscale.aggreg1 != dfscale.aggreg2]
            .drop(['aggreg1','aggreg2'],axis=1).groupby('t').sum()
        ) * _wscale
        dfintra.index = (
            (dfintra.index - startyear - yearspan/2)
            * width_year / width_step * width_intra_frac)
        dfinter.index = (dfinter.index - startyear - yearspan/2) * width_year / width_step
        ### Get the bar locations
        gap = 0.06e6
        xintra = scale_loc[0]*1e6 + (width_inter * width_intra_frac)/2 + gap/2
        xinter = scale_loc[0]*1e6 - width_inter/2 - gap/2
        y0 = scale_loc[1]*1e6
        ### Plot and annotate them
        ## Intra
        if width_intra_frac:
            plots.stackbar(
                df=dfintra,
                ax=ax, colors=transcolors, width=width_year*width_intra_frac,
                net=False, bottom=y0, x0=xintra,
            )
            ax.annotate(
                'Intra', (xintra,y0-0.02e6), weight='bold', ha='center', va='top',
                fontsize='large', annotation_clip=False)
        ## Inter
        plots.stackbar(
            df=dfinter,
            ax=ax, colors=transcolors, width=width_year, net=False,
            bottom=y0, x0=xinter,
        )
        ax.annotate(
            'Inter', (xinter,y0-0.02e6), weight='bold', ha='center', va='top',
            fontsize='large', annotation_clip=False)
        ### Add scale
        if scale_val:
            xscale = xinter - width_inter/2 - gap
            plots.stackbar(
                pd.DataFrame({'scale':scale_val*_wscale}, index=[xscale]),
                ax=ax, colors={'scale':'k'}, width=width_intra/10, net=False, bottom=y0,
            )
            ax.annotate(
                f'{scale_val} GW', (xscale-gap/2,y0+scale_val*_wscale/2), weight='bold',
                ha='right', va='center', fontsize='large', annotation_clip=False)

    ax.axis('off')
    ### Grid
    if drawgrid:
        ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5e6))
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.grid(which='major', ls=':', lw=0.75)
        ax.grid(which='minor', ls=':', lw=0.25)
        ax.axis('on')

    return f, ax


def map_agg(
        case, data='cap', startyear=2022, agglevel='transreg',
        f=None, ax=None, dpi=None,
        wscale='auto', width_total=4e5, width_step=3,
        drawstates=0., drawzones=0., scale_loc=(2.3,-1.55), scale_val=1000,
        drawgrid=False, transmission=False, legend=True,
    ):
    """
    # Inputs
    * data: 'cap' or 'gen'
    # Notes
    * Currently only works for agglevel='transreg'; to use other agglevels, add the
      coordinates for the interface boundaries to
      postprocessing/plots/transmission-interface-coords.csv
    """
    ### Get inputs
    hierarchy = reeds.io.get_hierarchy(case)

    ### Get colors and simpler tech names
    capcolors = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*'))
    tech_map = tech_map.drop_duplicates().set_index('raw').display

    ### Get outputs
    if data in ['cap','Cap','capacity',None,'GW','']:
        val = reeds.io.read_output(case, 'cap', valname='Value')
        ### Convert capacity to GW
        val.Value /= 1000
        val.i = val.i.str.lower()
        val = val.loc[val.t >= startyear].copy()
        units = 'GW'
    elif data in ['gen','Gen','generation','TWh']:
        val = reeds.io.read_output(case, 'gen_ann', valname='Value')
        ### Convert generation to TWh
        val.Value /= 1e6
        val.i = val.i.str.lower()
        val = val.loc[val.t >= startyear].copy()
        units = 'TWh'

    ### Map capacity to agglevel
    val['aggreg'] = val.r.map(hierarchy[agglevel])
    val_agg = val.copy()
    ## Use reduced technology set
    val_agg.i = val_agg.i.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).map(tech_map)
    val_agg = val_agg.groupby(['i','aggreg','t'], as_index=False).Value.sum()

    ### Get region map
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    dfba[agglevel] = dfba.index.map(hierarchy[agglevel])
    dfreg = dfba.copy()
    dfreg['geometry'] = dfreg.buffer(0.)
    dfreg = dfreg.dissolve(agglevel)
    dfreg['x'] = dfreg.centroid.x
    dfreg['y'] = dfreg.centroid.y

    ###### Get coordinates of region centers
    dfcenter = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','plots','transmission-interface-coords.csv'),
        index_col=['level','region1','region2'],
    ).drop('drop',axis=1).loc[agglevel].reset_index()
    dfcenter[['x','y']] *= 1e6
    dfcenter = (
        dfcenter
        .loc[~dfcenter.index.duplicated()]
        .loc[dfcenter.region1 == dfcenter.region2]
        .rename(columns={'region1':'aggreg'})
        .drop(['region2','angle'], axis=1)
        .set_index('aggreg')
    )

    ### Aggregated
    dfplot = val_agg.pivot(
        index=['aggreg','t'],columns='i',values='Value'
    ).reindex(capcolors.index, axis=1).dropna(axis=1, how='all')

    ### Plot settings
    width_year = width_total / len(val.t.unique())
    yearspan = val.t.max() - startyear
    if wscale in ['auto','scale','default',None,'','max']:
        capmax = dfplot.groupby('t').sum().sum(axis=1).max()
        _wscale = 3e6 / capmax * 0.95
    else:
        _wscale = wscale

    ###### Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=(12,8),dpi=dpi)
    ### Plot background
    dfreg.plot(ax=ax, facecolor='none', edgecolor='k', lw=1.)
    if drawstates:
        dfstates.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawstates)
    if drawzones:
        dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawzones)

    ### Capacity
    for aggreg, (x,y) in dfcenter.iterrows():
        try:
            df = dfplot.loc[aggreg] * _wscale
        except KeyError:
            continue
        df.index = (df.index - startyear - yearspan/2) * width_year / width_step
        y -= df.sum(axis=1).max() / 2
        plots.stackbar(
            df=df,
            ax=ax, colors=capcolors, width=width_year, net=False,
            bottom=y, x0=x,
        )

    ### Scale
    if scale_loc:
        ### Get the total value
        dfscale = dfplot.groupby('t').sum() * _wscale
        dfscale.index = (dfscale.index - startyear - yearspan/2) * width_year / width_step
        ### Scale down scale value if necessary
        if capmax < scale_val*2:
            scale_val /= 10
        ### Get the bar locations
        gap = 3e4
        x0 = scale_loc[0]*1e6
        y0 = scale_loc[1]*1e6
        ### Plot and annotate them
        plots.stackbar(
            df=dfscale,
            ax=ax, colors=capcolors, width=width_year, net=False,
            bottom=y0, x0=x0,
        )
        ax.annotate(
            'Total', (x0,y0-0.02e6), weight='bold', ha='center', va='top',
            fontsize='large', annotation_clip=False)
        ### Add scale
        xscale = x0 - width_total/2 - width_year/2
        plots.stackbar(
            pd.DataFrame({'scale':scale_val*_wscale}, index=[xscale]),
            ax=ax, colors={'scale':'k'}, width=width_year/4, net=False, bottom=y0,
        )
        ax.annotate(
            f'{scale_val} {units}', (xscale-gap,y0+scale_val*_wscale/2), weight='bold',
            ha='right', va='center', fontsize='large', annotation_clip=False)

    ###### Inter-regional transmission, if requested
    if transmission:
        map_trans_agg(
            case=case, agglevel=agglevel, startyear=startyear,
            f=f, ax=ax, dpi=dpi, wscale=_wscale, width_step=width_step,
            width_intra_frac=0, drawregions=0, drawgrid=False,
            scale_val=0, width_inter=width_total,
            scale_loc=(scale_loc[0]+0.7, scale_loc[1]),
        )

    ###### Legend
    if legend:
        handles = [
            mpl.patches.Patch(facecolor=capcolors[i], edgecolor='none', label=i)
            for i in capcolors.index if i in dfplot.columns
        ]
        _leg = ax.legend(
            handles=handles[::-1], loc='upper left', fontsize=6, ncol=1, frameon=False,
            bbox_to_anchor=((0.875,0.95) if transmission else (0.955,0.95)),
            handletextpad=0.3, handlelength=0.7, columnspacing=0.5, 
        )

    ###### Formatting
    ax.axis('off')
    ### Grid
    if drawgrid:
        ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5e6))
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.grid(which='major', ls=':', lw=0.75)
        ax.grid(which='minor', ls=':', lw=0.25)
        ax.axis('on')

    return f, ax


def map_capacity_techs(
        case, year=2050,
        techs=[
            'Utility PV', 'Land-based wind', 'Offshore wind', 'Electrolyzer',
            'Battery', 'PSH', 'H2 turbine', 'Nuclear',
            'Gas CCS', 'Coal CCS', 'Gas', 'Coal',
        ],
        ncols=4,
        vmax='shared',
        cmap=cmocean.cm.rain,
    ):
    """
    """
    ### Tech simplifications
    techmap = {
        **{f'upv_{i}':'Utility PV' for i in range(20)},
        **{f'wind-ons_{i}':'Land-based wind' for i in range(20)},
        **{f'wind-ofs_{i}':'Offshore wind' for i in range(20)},
        **dict(zip(['nuclear','nuclear-smr'], ['Nuclear']*20)),
        **dict(zip(
            ['h2-cc', 'h2-ct', 'gas-cc_h2-cc', 'gas-ct_h2-ct'],
            ['H2 turbine']*20)),
        **{'electrolyzer':'Electrolyzer'},
        **{'battery_li':'Battery', 'pumped-hydro':'PSH'},
        **dict(zip(
            ['gas-cc_gas-cc-ccs_mod','gas-cc_gas-cc-ccs_max',
             'gas-cc-ccs_mod','gas-cc-ccs_max'],
            ['Gas CCS']*50)),
        **dict(zip(
            ['coal-igcc_coal-ccs_mod','coal-new_coal-ccs_mod',
             'coaloldscr_coal-ccs_mod','coalolduns_coal-ccs_mod','cofirenew_coal-ccs_mod',
             'cofireold_coal-ccs_mod','coal-igcc_coal-ccs_max',
             'coal-new_coal-ccs_max','coaloldscr_coal-ccs_max','coalolduns_coal-ccs_max',
             'cofirenew_coal-ccs_max','cofireold_coal-ccs_max'],
            ['Coal CCS']*50)),
        **dict(zip(
            ['coal-igcc', 'coaloldscr', 'coalolduns', 'coal-new',
             'gas-cc', 'gas-ct', 'o-g-s'],
            ['Fossil']*20)),
        **dict(zip(
            ['coal-igcc', 'coaloldscr', 'coalolduns', 'coal-new'],
            ['Coal']*20)),
        **dict(zip(
            ['gas-cc', 'gas-ct'],
            ['Gas']*20)),
        **dict(zip(['dac','beccs_mod','beccs_max'], ['CO2 removal']*20)),
    }
    ### Get maps
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    ### Case data
    dfcap = reeds.io.read_output(case, 'cap', valname='MW')
    dfcap.i = dfcap.i.str.lower().map(lambda x: techmap.get(x,x))
    ### Get the vmax
    if vmax == 'shared':
        _vmax = dfcap.loc[
            dfcap.i.isin(techs) & (dfcap.t.astype(int)==year)
        ].groupby(['i','r']).MW.sum().max() / 1e3
    else:
        _vmax = None
    ### Arrange the subplots
    nrows, _, coords = reeds.plots.get_coordinates(techs, ncols=ncols)
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(3*ncols, 3*nrows),
        gridspec_kw={'wspace':0.0,'hspace':-0.05}, dpi=150)
    for tech in techs:
        dfval = dfcap.loc[
            (dfcap.i==tech)
            & (dfcap.t.astype(int)==year)
        ].groupby('r').MW.sum().round(3)
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
        '{} ({})'.format(os.path.basename(case), year),
        x=0.1, ha='left', va='top')
    plots.trim_subplots(ax, nrows, ncols, len(techs))
    return f, ax


def map_capacity_markers(
        case, level='r', year=2050, ms=5,
        unitsize=1,
        f=None, ax=None,
        verbose=0,
    ):
    """
    Inputs
    ------
    level [str]: Hierarchy level at which to distribute markers
    unitsize [float]: GW capacity for each marker
    transmission_linesize [float]: GW capacity for each transmission line
        (if 0, do not plot transmission)
    """
    ### Additional settings
    decrement = 0.02
    drop = [
        'canada',
        'electrolyzer',
        'smr', 'smr-ccs',
    ]
    tech_style = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order',
    ).squeeze(1)
    tech_style.index = tech_style.index.str.lower()

    ###### All in one
    ### Load the data
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    hierarchy = reeds.io.get_hierarchy(case)

    cap = reeds.io.read_output(case, 'cap')
    cap = cap.loc[cap.t==year].copy()
    cap['GW'] = cap.Value / 1e3
    ### Aggregate and simplify tech classes and types
    cap.i = simplify_techs(cap.i)
    cap = cap.loc[~cap.i.isin(drop)].copy()
    techs = cap.i.unique()
    if any([i not in techmarkers for i in techs]):
        print([i for i in techs if i not in techmarkers])
    ### Group by region
    if level not in ['r','rb']:
        cap.r = cap.r.map(hierarchy[level])
    cap = cap.groupby(['r','i']).GW.sum() / unitsize

    ### Get the geometries
    regions = hierarchy.index if level in ['r','rb'] else hierarchy[level].unique()
    if level in ['r','rb']:
        dfzones = dfba.copy()
    else:
        dfzones = dfba.copy()
        dfzones['zone'] = dfba.index.map(hierarchy[level])
        dfzones = dfzones.dissolve('zone')

    ### Plot it
    draw_background = False
    if (not f) or (not ax):
        draw_background = True
        f,ax = plt.subplots(figsize=(12,9))
    ### Background
    if draw_background:
        if level in ['r','rb']:
            dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.1)
        dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.2)
    ### Units by zone
    for r in regions:
        ### Get the number of units per tech
        r_units = cap[r].round(0).astype(int).replace(0,np.nan).dropna().astype(int)
        total_units = r_units.sum()
        ### Sort them according to the typical order in tech_style
        r_units_sorted = r_units.reindex(tech_style.index).dropna().astype(int)
        ### Get list of units
        units = [[unit]*number for (unit, number) in r_units_sorted.items()]
        ### Flatten
        units = [item for sublist in units for item in sublist]

        ### Get rectangle containing zone
        geometry = dfzones.loc[r,'geometry']
        minx, miny, maxx, maxy = geometry.bounds
        
        ### Get grid of points
        step_0 = max(maxx-minx, maxy-miny)
        step = step_0
        for iteration in range(1000):
            step = step * (1 - decrement)
            xs = np.arange(minx, maxx+1, step)
            ys = np.arange(miny, maxy+1, step)
            coords = [(x,y) for y in ys for x in xs]
            points = [shapely.geometry.Point(p) for p in coords]
            inside_geometry = [p.within(geometry) for p in points]
            if sum(inside_geometry) >= total_units:
                break

        dfplot = gpd.GeoDataFrame(
            geometry=[shapely.geometry.Point(p) for (i,p) in enumerate(coords)
                      if inside_geometry[i]],
            crs='ESRI:102008'
        ).iloc[:len(units)]
        dfplot['tech'] = units

        ### Plot it
        for tech in dfplot.tech.unique():
            dfplot.loc[dfplot.tech==tech].plot(
                ax=ax, marker=techmarkers.get(tech,'o'),
                color=tech_style.get(tech,'k'),
                lw=0, markersize=ms)

    ### Legend
    handles = [
        mpl.lines.Line2D(
            [], [], marker=techmarkers[i], markerfacecolor=tech_style[i],
            markeredgewidth=0, lw=0, label=i)
        for i in tech_style.index if i in techs
    ][::-1]
    _leg = ax.legend(
        handles=handles, loc='center left', bbox_to_anchor=(0.95,0.5), 
        fontsize='medium', ncol=1, frameon=False,
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5,
        title=f'{unitsize} GW per marker',
    )

    ### Formatting
    ax.axis('off')

    return f, ax


def map_transmission_lines(
        case, level='r', year=2050, subtract_baseyear=None,
        transmission_linesize=2.5, radscale=35, lw=0.25,
        zorder=-1e6, alpha=1,
        f=None, ax=None,
    ):
    """
    Inputs
    ------
    transmission_linesize [float]: GW capacity for each line. Default of 2.5 GW
        is taken from the median of 500 kV lines in the NARIS dataset, rounded
        to the nearest 0.5 GW.
    """
    ### Get styles
    trtype_style = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2',
            'trtype_style.csv'),
        index_col='order',
    ).squeeze(1)
    linecolors = {
        'AC': trtype_style['AC'],
        'B2B': trtype_style['B2B'],
        'LCC': trtype_style['DC, LCC'],
        'VSC': trtype_style['DC, VSC'],
    }
    ### Get inputs
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']
    dfstates = dfmap['st']
    hierarchy = reeds.io.get_hierarchy(case)

    if level in ['r','rb']:
        dfzones = dfba.copy()
    else:
        dfzones = dfba.copy()
        dfzones['zone'] = dfba.index.map(hierarchy[level])
        dfzones = dfzones.dissolve('zone')

    tran_out = reeds.io.read_output(case, 'tran_out')
    if subtract_baseyear:
        tran_out = (
            tran_out.loc[tran_out.t==year].set_index(['r','rr','trtype']).Value
            - (
                tran_out
                .loc[(tran_out.t==subtract_baseyear)]
                .set_index(['r','rr','trtype']).Value
                .reindex(tran_out.loc[tran_out.t==year].set_index(['r','rr','trtype']).index)
                .fillna(0)
            )
        ).clip(lower=0).reset_index()
        tran_out = tran_out.loc[tran_out.Value>0].copy()
    else:
        tran_out = tran_out.loc[tran_out.t==year].copy()
    tran_out['lines'] = (
        ## Convert to GW
        tran_out.Value / 1e3
        ## Convert to lines
        / transmission_linesize
    )
    ### Group by region
    if level not in ['r','rb']:
        tran_out.r = tran_out.r.map(hierarchy[level])
        tran_out.rr = tran_out.rr.map(hierarchy[level])
    ### Group and round to lines
    tran_out = (
        tran_out.groupby(['r','rr','trtype']).lines.sum()
        .round(0).astype(int).replace(0,np.nan).dropna().astype(int).reset_index()
    )
    tran_out['interface'] = tran_out.r + '||' + tran_out.rr
    tran_out = tran_out.set_index(['interface','trtype']).lines

    trtypes = tran_out.index.get_level_values('trtype').unique()
    interfaces = tran_out.index.get_level_values('interface').unique()

    draw_background = False
    if (not f) or (not ax):
        draw_background = True
        f,ax = plt.subplots(figsize=(12,9))
    ### Background
    if draw_background:
        if level in ['r','rb']:
            dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.1, zorder=-1e8)
        dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.2, zorder=-1e8)
    ### Data
    for interface in interfaces:
        ## Get properties of interface
        df = tran_out.loc[interface]
        r,rr = interface.split('||')
        startx, starty = dfzones.loc[r,['x','y']]
        endx, endy = dfzones.loc[rr,['x','y']]
        distance = ((startx-endx)**2 + (starty-endy)**2)**0.5 / 1e3
        ## Get lines
        lines = [[trtype]*val for (trtype,val) in df.items()]
        lines = [item for sublist in lines for item in sublist]
        rads = np.arange(-len(lines)/2, len(lines)/2, 1)
        if not (len(rads) == len(lines)):
            raise ValueError(f'len(rads) = {len(rads)} but len(lines) = {len(lines)}')
        for (line, rad) in zip(lines, rads):
            ax.add_patch(
                mpl.patches.FancyArrowPatch(
                    (startx, starty), (endx, endy),
                    connectionstyle=f'Arc3, rad={rad/distance*radscale}',
                    shrinkA=0, shrinkB=0,
                    lw=lw, color=linecolors[line],
                    zorder=zorder, alpha=alpha,
                )
            )
    ### Legend
    handles = [
        mpl.lines.Line2D([], [], lw=2, label=i, color=linecolors[i])
        for i in linecolors if i in trtypes
    ]
    title = f'{transmission_linesize} GW lines, {year}'
    if subtract_baseyear:
        title += f'\n(new since {subtract_baseyear})'
    leg = ax.legend(
        handles=handles, loc='lower left', bbox_to_anchor=(0.1,0.1), 
        fontsize='medium', ncol=1,
        handletextpad=0.4, handlelength=1, columnspacing=0.5,
        frameon=True, edgecolor='none', framealpha=0.7,
        title=title,
    )
    ax.add_artist(leg)

    ### Formatting
    ax.axis('off')
    return f,ax


def get_colors(reeds_path):
    """
    """
    bokehcolors = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    bokehcolors = pd.concat([
        bokehcolors.loc['smr':'electrolyzer'],
        pd.Series('#D55E00', index=['dac'], name='color'),
        bokehcolors.loc[:'smr'],
    ]).reset_index().drop_duplicates().set_index('index').color
    bokehcolors['canada'] = bokehcolors['Canada']

    trtype_map = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
        index_col='raw')['display']
    transcolors = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
        index_col='order')['color']
    transcolors = pd.concat([transcolors, trtype_map.map(transcolors)])
    transcolors['LCC'] = transcolors['lcc']
    transcolors['VSC'] = transcolors['vsc']

    return bokehcolors, transcolors


def get_gen_capacity(case, year=2050, level='r', units='GW'):
    """Get zonal generation capacity from a ReEDS run.
    Returns:
        Dataframe with index=zones and columns=techs
    """
    ### Check inputs
    assert units in ['MW','GW','TW']

    ### Get data
    hierarchy = reeds.io.get_hierarchy(case)

    bokehcolors, transcolors = get_colors(reeds_path)

    dfcap_in = reeds.io.read_output(case, 'cap', valname='MW')
    dfcap_in.i = simplify_techs(dfcap_in.i)
    dfcap = dfcap_in.loc[
        (dfcap_in.t==year)
    ].groupby(['i','r']).MW.sum().unstack('i')
    if units != 'MW':
        dfcap *= {'GW':1e-3, 'TW':1e-6}[units]
    dfcap = (
        dfcap[[c for c in bokehcolors.index if c in dfcap]]
        .drop('electrolyzer', axis=1, errors='ignore')
    ).copy()
    ## Aggregate if necessary
    if level != 'r':
        dfcap.index = dfcap.index.map(hierarchy[level])
        dfcap = dfcap.groupby(axis=0, level='r').sum()

    return dfcap


def get_trans_capacity(case, year=2050, level='r', units='GW'):
    """Get zonal transmission capacity from a ReEDS run.
    Returns:
        Geodataframe with index=interfaces and geometry=linestrings
    """
    ### Check inputs
    assert units in ['MW','GW','TW']

    ### Get data
    hierarchy = reeds.io.get_hierarchy(case)
    dfmap = reeds.io.get_dfmap(case)

    for r in zone_label_offset:
        if r in dfmap[level].index:
            dfmap[level].loc[r, 'centroid_x'] += zone_label_offset[r][0]
            dfmap[level].loc[r, 'centroid_y'] += zone_label_offset[r][1]

    tran_out = reeds.io.read_output(case, 'tran_out', valname='MW')
    transmap = tran_out.loc[
        (tran_out.t==year)
    ][['r','rr','trtype','MW']].copy()
    if units != 'MW':
        transmap[units] = transmap.MW * {'GW':1e-3, 'TW':1e-6}[units]
    ## Aggregate if necessary
    if level != 'r':
        transmap.r = transmap.r.map(hierarchy[level])
        transmap.rr = transmap.rr.map(hierarchy[level])
        for i, row in transmap.iterrows():
            if row.r > row.rr:
                transmap.loc[i,['r','rr']] = transmap.loc[i,['rr','r']].values
        transmap = transmap.loc[
            transmap.r != transmap.rr
        ].groupby(['r','rr','trtype'], as_index=False)[units].sum()
    transmap.index = (transmap.r + '|' + transmap.rr).rename('interface')
    ## Add geographic data to the line capacity
    key = dfmap[level][['centroid_x','centroid_y']]
    for col in ['r','rr']:
        for i in ['x','y']:
            transmap[f'{col}_{i}'] = transmap.apply(
                lambda row: key.loc[row[col]]['centroid_'+i], axis=1)

    ## Convert the line capacity dataframe to a geodataframe with linestrings
    transmap['geometry'] = transmap.apply(
        lambda row: shapely.geometry.LineString([(row.r_x, row.r_y), (row.rr_x, row.rr_y)]),
        axis=1
    )
    transmap = gpd.GeoDataFrame(transmap).set_crs('ESRI:102008')

    return transmap


def map_zone_capacity(
        case, year=2050, level='r',
        valscale=3e3, width=7e4,
        center=True, linealpha=0.6,
        scale=10, sideplots=True, legend=True,
        f=None, ax=None,
        drawstates=True, drawinterconnects=True,
    ):
    """
    Inputs
    ------
    scale: [float] scalebar size in GW; if zero, don't plot scalebar
    sideplots: Nationwide tranmsission, emissions, generation, and generation capacity
    """
    ###### Shared inputs
    sw = reeds.io.get_switches(case)
    years = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')).columns.astype(int).values
    yearstep = years[-1] - years[-2]

    bokehcolors, transcolors = get_colors(reeds_path)

    dfmap = reeds.io.get_dfmap(case)
    for r in zone_label_offset:
        if r in dfmap[level].index:
            dfmap[level].loc[r, 'centroid_x'] += zone_label_offset[r][0]
            dfmap[level].loc[r, 'centroid_y'] += zone_label_offset[r][1]

    ###### Case inputs
    dfcap = get_gen_capacity(case=case, year=year, level=level, units='GW')

    transmap = get_trans_capacity(case=case, year=year, level=level, units='GW')
    ## Buffer the lines into polygons
    transmap['geometry'] = transmap.apply(
        lambda row: row.geometry.buffer(row.GW*valscale/2), axis=1)

    ###### Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=(12, 9))
    ### Background
    if level == 'r':
        dfmap[level].plot(ax=ax, facecolor='none', edgecolor='0.8', lw=0.2)
    else:
        dfmap[level].plot(ax=ax, facecolor='none', edgecolor='0.3', lw=0.4)
    if drawstates:
        dfmap['st'].plot(ax=ax, facecolor='none', edgecolor='0.7', lw=0.4)
    if drawinterconnects:
        dfmap['interconnect'].plot(ax=ax, facecolor='none', edgecolor='k', lw=1)

    ### Plot transmission capacity
    for trtype in ['AC','B2B','LCC','VSC']:
        if trtype in transmap.trtype.unique():
            transmap.loc[transmap.trtype==trtype].dissolve().plot(
                ax=ax, facecolor=transcolors[trtype], edgecolor='none', alpha=linealpha,
            )

    ### Plot generation capacity
    plots.plot_region_bars(
        dfzones=dfmap[level], dfdata=dfcap, colors=bokehcolors,
        ax=ax, valscale=valscale, width=width, center=center,
        # zeroline={'c':'k', 'ls':':', 'lw':'0.5'},
    )

    ### Formatting
    ax.axis('off')
    if scale:
        ax.bar(
            x=[-1.8e6], height=[valscale * scale], bottom=[-1.05e6], width=3.0e5,
            align='center', color='k',
        )
        ax.annotate(
            f'{scale:.0f} GW', (-1.8e6, -1.1e6), fontsize=12,
            ha='center', va='top', weight='bold')

    ###### Side plots
    eax = None
    if sideplots:
        ###### Extra data
        renametechs = {
            'h2-cc_upgrade':'h2-cc',
            'h2-ct_upgrade':'h2-ct',
            'gas-cc-ccs_mod_upgrade':'gas-cc-ccs_mod',
            'coal-ccs_mod_upgrade':'coal-ccs_mod',
        }
        dfgen_in = reeds.io.read_report(case, 'Generation (TWh)')
        dfgen_in.tech = dfgen_in.tech.map(lambda x: renametechs.get(x,x))
        dfgen_in = (
            dfgen_in.groupby(['tech','year'], as_index=False)['Generation (TWh)'].sum())

        dfcap_nat = reeds.io.read_report(case, 'Capacity (GW)')
        dfcap_nat.tech = dfcap_nat.tech.map(lambda x: renametechs.get(x,x))
        dfcap_nat = (
            dfcap_nat.groupby(['tech','year'], as_index=False)['Capacity (GW)'].sum())

        emit_nat_tech = reeds.io.read_output(case, 'emit_nat_tech', valname='ton')
        if int(sw.get('GSw_Upstream', 0)):
            emit_nat_tech = emit_nat_tech.groupby(['e','i','t']).ton.sum()
        else:
            emit_nat_tech = (
                emit_nat_tech
                .set_index(['etype','e','i','t'])
                .drop(['precombustion', 'upstream'], level='etype', errors='ignore')
                .groupby(['e','i','t']).ton.sum()
            )

        dfin_trans = reeds.io.read_report(case, 'Transmission (GW-mi)')

        ###### Make the side plots
        alltechs = set()
        axbounds = {
            ## left, bottom, width, height
            'Trans [TW-mi]': [0.92, 0.62, 0.1, 0.17],
            'CO2 [MMT]': [0.92, 0.41, 0.1, 0.17],
            'Cap [GW]': [0.83, 0.2, 0.1, 0.17],
            'Gen [TWh]': [1.0, 0.2, 0.1, 0.17],
        }
        eax = {}
        for a in axbounds:
            eax[a] = f.add_axes(axbounds[a])
            eax[a].set_ylabel(a)
            plots.despine(eax[a])
            eax[a].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
            eax[a].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
            eax[a].set_xlim(2020-yearstep/2, 2050+yearstep/2)
        ### Side plot of generation capacity over time
        dfcapacity = dfcap_nat.pivot(index='year', columns='tech', values='Capacity (GW)')
        dfcapacity = (
            dfcapacity[[c for c in bokehcolors.index if c in dfcapacity]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all')
            .drop('electrolyzer', axis=1, errors='ignore')
            .loc[2020:]
        )
        alltechs.update(dfcapacity.columns)
        plots.stackbar(
            df=dfcapacity, ax=eax['Cap [GW]'],
            colors=bokehcolors, width=yearstep, net=False)

        ### Side plot of generation over time
        dfgen = dfgen_in.pivot(index='year', columns='tech', values='Generation (TWh)')
        dfgen = (
            dfgen[[c for c in bokehcolors.index if c in dfgen]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all')
            .loc[2020:]
        )
        alltechs.update(dfgen.columns)
        plots.stackbar(
            df=dfgen, ax=eax['Gen [TWh]'],
            colors=bokehcolors, width=yearstep, net=False)
        eax['Gen [TWh]'].axhline(0, c='k', ls=':', lw=0.75)

        ### Side plot of transmission capacity over time
        dftrans = dfin_trans.pivot(
            index='year', columns='trtype', values='Amount (GW-mi)') / 1e3
        dftrans = (
            dftrans[[c for c in transcolors.index if c in dftrans]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all')
            .loc[2020:]
        )
        plots.stackbar(
            df=dftrans, ax=eax['Trans [TW-mi]'],
            colors=transcolors, width=yearstep, net=False)

        ### Side plot of emissions over time
        dfco2 = (
            emit_nat_tech['CO2']
            .unstack('i') / 1e3
        )
        dfco2.columns = simplify_techs(dfco2.columns)
        dfco2 = dfco2.groupby(axis=1, level='i').sum()
        dfco2 = (
            dfco2[[c for c in bokehcolors.index if c in dfco2]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all').fillna(0)
            .loc[2020:]
        )
        plots.stackbar(
            df=dfco2, ax=eax['CO2 [MMT]'],
            colors=bokehcolors, width=yearstep, net=True,
            markerfacecolor=(1,1,1,0.8), markersize=4.5)
        eax['CO2 [MMT]'].axhline(0, c='k', ls=':', lw=0.75)

        plt.draw()
        for a in eax:
            plots.shorten_years(eax[a])

        ### Legend
        if legend:
            ### Generation
            handles = [
                mpl.patches.Patch(facecolor=bokehcolors[i], edgecolor='none', label=i)
                for i in bokehcolors.index if i in alltechs
            ]
            leg_gen = ax.legend(
                handles=handles[::-1], loc='lower left', fontsize=6.5, frameon=False,
                bbox_to_anchor=(1.16,0.332),
                handletextpad=0.3, handlelength=0.7, columnspacing=0.5,
            )
            ## Draw it
            ax.add_artist(leg_gen)
            ### Transmission
            handles = [
                mpl.patches.Patch(facecolor=transcolors[i], edgecolor='none', label=i)
                for i in transcolors.index if i in dftrans
            ]
            _leg_trans = ax.legend(
                handles=handles[::-1], loc='upper left', fontsize=6.5, frameon=False,
                bbox_to_anchor=(1.16,0.92),
                handletextpad=0.3, handlelength=0.7, columnspacing=0.5,
            )

    return f, ax, eax


def plot_retire_add(
        case, yearstart=2020, width=0.25, peak=True,
        plotyears=None, figsize=None,
    ):
    """
    """
    ### Colors
    bokehcolors = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    bokehcolors = pd.concat([
        bokehcolors.loc['smr':'electrolyzer'],
        pd.Series('#D55E00', index=['dac'], name='color'),
        bokehcolors.loc[:'Canada'],
    ])
    bokehcolors['canada'] = bokehcolors['Canada']
    bokehcolors = bokehcolors.to_dict()

    ### For this particular plot we put storage below VRE
    plotorder = (
        list(bokehcolors.keys())[:list(bokehcolors.keys()).index('wind-ons')]
        + list(bokehcolors.keys())[
            list(bokehcolors.keys()).index('battery'):list(bokehcolors.keys()).index('Canada')]
        + list(bokehcolors.keys())[
            list(bokehcolors.keys()).index('wind-ons'):list(bokehcolors.keys()).index('battery')]
        + list(bokehcolors.keys())[list(bokehcolors.keys()).index('Canada'):]
    )

    ### Case-specific inputs
    years = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')).columns.astype(int).values
    if not plotyears:
        _years = [y for y in years if y >= yearstart]
    else:
        _years = plotyears

    if not figsize:
        _figsize = (len(_years)*1.5, 5)
    else:
        _figsize = figsize

    ## Nationwide capacity
    dfcap_in = reeds.io.read_report(case, 'Capacity (GW)')
    ## Simplify techs
    renametechs = {
        'h2-cc_upgrade':'h2-cc',
        'h2-ct_upgrade':'h2-ct',
        'gas-cc-ccs_mod_upgrade':'gas-cc-ccs_mod',
        'coal-ccs_mod_upgrade':'coal-ccs_mod',
    }
    dfcap_in.tech = dfcap_in.tech.map(lambda x: renametechs.get(x,x))
    dfcap_in = dfcap_in.groupby(['tech','year'], as_index=False)['Capacity (GW)'].sum()

    ## Peak coincident demand
    if peak:
        dfpeak = pd.read_csv(
            os.path.join(case,'inputs_case','peakload.csv'),
            index_col=['level','region'],
        ).rename(columns=int).loc['country', _years].squeeze(0) / 1e3

    ### Calculate the retirements and additions
    dfcap = (
        dfcap_in
        .pivot(index='year', columns='tech', values='Capacity (GW)')
        .drop(columns=['Canada','electrolyzer'], errors='ignore')
    )
    dfcap = dfcap[[c for c in plotorder if c in dfcap]].copy()

    difference = {}
    retirements = {}
    additions = {}
    for i, year in enumerate(_years[:-1]):
        difference[year] = dfcap.loc[_years[i+1]] - dfcap.loc[year]
        retirements[year] = difference[year].loc[difference[year] < 0].copy()
        additions[year] = difference[year].loc[difference[year] > 0].copy()


    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=_figsize)
    for x, year in enumerate(_years[:-1]):
        ## First year
        df = dfcap.loc[[year]]
        df.index = [x]
        plots.stackbar(
            df=df, ax=ax, colors=bokehcolors, width=width, net=False,
        )
        bottom = df.sum().sum()
        ## Retirements
        df = retirements[year].rename(x+0.333).to_frame().T
        plots.stackbar(
            df=df, ax=ax, colors=bokehcolors, width=width, net=False, bottom=bottom,
        )
        bottom = bottom + df.sum().sum()
        ## Additions
        df = additions[year].rename(x+0.667).to_frame().T
        plots.stackbar(
            df=df, ax=ax, colors=bokehcolors, width=width, net=False, bottom=bottom,
        )

    ## Last year
    df = dfcap.loc[[_years[-1]]]
    df.index = [len(_years)-1]
    plots.stackbar(
        df=df, ax=ax, colors=bokehcolors, width=width, net=False,
    )

    ### US coincident peak demand
    if peak:
        ax.plot(
            range(len(_years)), dfpeak.values,
            marker='o', markerfacecolor='w', markeredgecolor='k', lw=0,
        )
        ax.annotate(
            va='center', ha='left', annotation_clip=False, fontsize=12,
            text='Peak\ndemand', xy=(0+width/3, dfpeak.iloc[0]),
            xytext=(0+width*1.2, dfpeak.iloc[0]),
            arrowprops={'arrowstyle':'-|>', 'color':'k'}
        )

    ### Legend
    handles = [
        mpl.patches.Patch(facecolor=bokehcolors[i], edgecolor='none', label=i)
        for i in plotorder if i in dfcap
    ]
    _leg = ax.legend(
        handles=handles[::-1], loc='center left', bbox_to_anchor=(1.0,0.5), 
        fontsize='large', ncol=1, frameon=False,
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5, labelspacing=0.1,
    )

    ### Formatting
    xlabels = [[str(year),'retire','add'] for year in _years]
    xlabels = [i for sublist in xlabels for i in sublist][:-2]
    # ## Try making the years bigger
    # xlabels[0] = mpl.text.Text(text='foo', fontsize='x-large', weight='bold')
    ax.set_ylabel('Capacity [GW]')
    ax.set_xticks(np.linspace(0, len(_years)-1, (len(_years)-1)*3 + 1))
    ax.set_xticklabels(xlabels, rotation=45, ha='right', rotation_mode='anchor')
    ax.set_xlim(-width/2 - 0.05, len(_years)-1 + width/2 + 0.05)
    ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(100))
    plots.despine(ax)

    return f, ax


def map_hybrid_pv_wind(
        case, val='site_cap', year=2050,
        tech=None, vmax=None,
        markersize=10.75, #stretch=1.2,
        cmap=cmocean.cm.rain,
        f=None, ax=None, figsize=(6,6), dpi=None,
    ):
    """
    # Inputs
    cmap: Suggestions:
        val=site_cap, tech=wind-ons: plt.cm.Blues
        val=site_cap, tech=upv: plt.cm.Oranges
        val=(site_hybridization,site_spurcap), tech=None: cmocean.cm.rain
        val=(site_pv_fraction,site_gir), tech=either: plt.cm.turbo
            or mpl.colors.LinearSegmentedColormap.from_list
                'turboclip', [plt.cm.turbo(c) for c in np.linspace(0.1,0.91,101)])
    """
    ###### Format inputs
    val2col = {
        'site_cap':'MW',
        'site_pv_fraction':'pv_fraction',
        'site_hybridization':'hybridization',
        'site_spurcap':'MW',
        'site_gir':'GIR',
    }
    column = val2col[val]
    label = {
        ('site_cap','upv'): f'{year} PV capacity [MW]',
        ('site_cap','wind-ons'): f'{year} wind capacity [MW]',
        ('site_pv_fraction',None): f'{year} PV fraction [.]',
        ('site_hybridization',None): f'{year} hybridization [.]',
        ('site_spurcap',None): f'{year} spur line capacity [MW]',
        ('site_gir','upv'): f'{year} PV gen:int ratio (GIR) [.]',
        ('site_gir','wind-ons'): f'{year} wind gen:int ratio (GIR) [.]',
    }[val, tech]
    ###### Load the data
    ### Model results
    dictin_hybrid = dict(
        site_cap=reeds.io.read_output(case, 'site_cap', valname='MW'),
        site_pv_fraction=reeds.io.read_output(case, 'site_pv_fraction', valname='pv_fraction'),
        site_hybridization=reeds.io.read_output(case, 'site_hybridization', valname='hybridization'),
        site_spurcap=reeds.io.read_output(case, 'site_spurcap', valname='MW'),
        site_gir=reeds.io.read_output(case, 'site_gir', valname='GIR'),
    )

    ### Other shared inputs
    sitemap = reeds.io.get_sitemap()
    sitemap.index = 'i' + sitemap.index.astype(str)

    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']

    ### Make the combined output dataframe
    df = dictin_hybrid[val].loc[dictin_hybrid[val].t==year].copy()
    df['longitude'] = df.x.map(sitemap.longitude)
    df['latitude'] = df.x.map(sitemap.latitude)
    # df['rb'] = df.x.map(sitemap.rb)
    # df['transreg'] = df.rb.map(hierarchy.transreg)
    ### Check for nulls
    if df.longitude.isnull().sum():
        df.dropna(subset=['longitude'], inplace=True)
    ### Geodataframify it
    dfplot = plots.df2gdf(df)
    ### Filter to single tech
    if tech:
        dfplot = dfplot.loc[dfplot.i.str.startswith(tech)].copy()

    if vmax in ['max','none',None]:
        zmax = dfplot[column].max()
    else:
        zmax = vmax

    ###### Plot it
    if (not f) and (not ax):
        plt.close()
        f,ax = plt.subplots(figsize=figsize, dpi=dpi)
    dfplot.plot(
        ax=ax, column=column, cmap=cmap, marker='s', lw=0, markersize=markersize,
        legend=False, vmin=0, vmax=zmax,
    )
    # xmin, xmax = ax.get_xlim()
    # ymin, ymax = ax.get_ylim()
    # xspan = xmax - xmin
    # yspan = ymax - ymin

    dfba.plot(ax=ax, facecolor='0.9', edgecolor='none', zorder=-1e6)
    dfba.plot(ax=ax, facecolor='none', edgecolor='w', lw=0.3, zorder=1e6)

    plots.addcolorbarhist(
        f=f, ax0=ax, data=dfplot[column].values,
        title=label, cmap=cmap,
        vmin=0., vmax=zmax,
        orientation='horizontal', labelpad=2.5, cbarbottom=-0.06,
        cbarheight=0.5, log=False, #title_fontsize=12,
        nbins=51, histratio=2,
        extend=('max' if tech == 'upv' else 'neither'),
        ticklabel_fontsize=10, title_fontsize=13,
    )

    # ax.set_xlim(xmin-xspan*(stretch-1), xmax+xspan*(stretch-1))
    # ax.set_ylim(ymin-yspan*(stretch-1), ymax+yspan*(stretch-1))
    ax.axis('off')
    return f, ax


def plot_dispatch_yearbymonth(
        case, t=2050, plottype='gen', periodtype='rep',
        techs=None, region=None,
        f=None, ax=None, figsize=(12,6), highlight_rep_periods=1,
    ):
    """
    Full year dispatch for final year with rep days mapped to actual days
    Inputs
    ------
    techs: None to plot all techs, or list of subset techs, or single tech string
    plottype: 'soc' for storage state of charge, anything else for dispatch
    """
    if (periodtype != 'rep') and not (periodtype.startswith('pcm')):
        raise ValueError(
            f"periodtype={periodtype}: must be 'rep' or start with 'pcm'. "
            "If it starts with 'pcm' it should be formatted as '{pcm}_{label}_{t} and "
            "match a folder of the same name in {case}/outputs."
        )
    inputs_path = os.path.join(case, 'inputs_case', periodtype)
    ### Load bokeh tech map and colors
    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*'))
    tech_map = tech_map.drop_duplicates().set_index('raw').display

    tech_style = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)

    ### Load run files
    sw = reeds.io.get_switches(case)
    hmap_myr = pd.read_csv(os.path.join(inputs_path, 'hmap_myr.csv'))
    hierarchy = reeds.io.get_hierarchy(case)
    output_path = (
        case if periodtype == 'rep'
        else os.path.join(case, 'outputs', f'{periodtype}_{t}', 'outputs.h5')
    )

    if plottype.lower() in ['soc', 'stateofcharge', 'energy_level', 'stor_level']:
        dfin = reeds.io.read_output(output_path, 'stor_level')
        dfin.i = dfin.i.str.lower().map(lambda x: tech_map.get(x,x))
    else:
        dfin = reeds.io.read_output(output_path, 'gen_h')
        dfin.i = dfin.i.map(
            lambda x: x if x.startswith('battery') else x.strip('_01234567890*')
        ).str.lower().map(lambda x: tech_map.get(x,x))

    if region is not None:
        err = (
                f"region = {region} but must be formatted as "
                + "{hierarchy level}/{.-delimited list of regions at that level}"
            )
        if (
            ('/' not in region)
            or (region.split('/')[0] not in hierarchy.columns.tolist() + ['r'])
        ):
            raise ValueError(err)
        level = region.split('/')[0]
        regions = region.split('/')[1].split('.')
        if level == 'r':
            keep_r = regions
        else:
            keep_r = hierarchy.loc[hierarchy[level].isin(regions)].index
        dfin = dfin.loc[dfin.r.isin(keep_r)].copy()

    dfyear = (
        dfin.loc[dfin.t==t]
        .groupby(['i','h']).Value.sum().round(3)
        .unstack('i').fillna(0)
        / 1e3
    )
    if techs is not None:
        if isinstance(techs, list):
            dfyear = dfyear[[c for c in techs if c in dfyear]].copy()
        else:
            dfyear = dfyear[[techs]].copy()

    if dfyear.empty:
        print(f"No values to plot for t={t}, region={region}, plottype={plottype}")
        return None, None, None

    ### Broadcast representative days to actual days
    if len(dfyear) != len(hmap_myr):
        dffull = (
            hmap_myr[['actual_h','h']]
            .merge(dfyear, left_on='h', right_index=True, how='left')
            .fillna(0)
            .sort_values('actual_h').set_index('actual_h').drop('h', axis=1)
        )
    else:
        dffull = dfyear.copy()

    dffull.index = dffull.index.map(reeds.timeseries.h2timestamp)

    ### Put negative parts of columns that go negative on bottom
    goes_negative = list(dffull.columns[(dffull < 0).any()])
    df = dffull.copy()
    for col in goes_negative:
        df[col+'_neg'] = df[col].clip(upper=0)
        df[col+'_off'] = df[col].clip(upper=0).abs()
        df[col+'_pos'] = df[col].clip(lower=0)
    df.drop(goes_negative, axis=1, inplace=True)

    negcols = [c+'_neg' for c in goes_negative]
    offsetcols = [c+'_off' for c in goes_negative]
    poscols = [c+'_pos' for c in goes_negative]
    plotorder = negcols + offsetcols + list(tech_style.index) + poscols
    dfplot = (
        df
        [[c for c in plotorder if c in df]].cumsum(axis=1)
        [[c for c in plotorder[::-1] if c in df]]
    )

    ### Read rep periods if necessary
    if highlight_rep_periods:
        period_szn = pd.read_csv(os.path.join(inputs_path, 'period_szn.csv'))
        period_szn['timestamp'] = (
            (period_szn.actual_period + 'h001')
            .map(reeds.timeseries.h2timestamp)
        )
        period_szn['rep'] = (period_szn.rep_period == period_szn.actual_period)
        repnum = dict(zip(
            sorted(period_szn.rep_period.unique()),
            range(1, len(period_szn.rep_period.unique())+1)
        ))
        period_szn['repnum'] = period_szn.rep_period.map(repnum)

    ### Plot it
    plt.close()
    f, ax = plots.plotyearbymonth(
        dfplot,
        colors=[
            tech_style[i.replace('_pos','').replace('_neg','').replace('_off','')]
            for i in dfplot],
        lwforline=0, f=f, ax=ax, figsize=figsize)

    if highlight_rep_periods:
        width = pd.Timedelta('5D') if sw['GSw_HourlyType'] == 'wek' else pd.Timedelta('1D')
        ylim = ax[0].get_ylim()
        for i, row in period_szn.iterrows():
            plottime = pd.Timestamp(2001, 1, row.timestamp.day)
            if row.rep:
                ## Draw an outline
                box = mpl.patches.Rectangle(
                    xy=(plottime, ylim[0]),
                    width=width, height=(ylim[1]-ylim[0]),
                    lw=0.75, edgecolor='k', facecolor='none', ls=':',
                    clip_on=False, zorder=2e6
                )
            else:
                ## Wash out the dispatch
                box = mpl.patches.Rectangle(
                    xy=(plottime, ylim[0]),
                    width=width, height=(ylim[1]-ylim[0]),
                    lw=0.75, edgecolor='none', facecolor='w', alpha=0.4,
                    clip_on=False, zorder=1e6
                )
            ax[row.timestamp.month-1].add_patch(box)
            ## Note the rep period
            ax[row.timestamp.month-1].annotate(
                row.repnum,
                (plottime+pd.Timedelta('30m'), ylim[1]*0.95),
                va='top', size=5, zorder=1e7,
                color=('k' if row.rep else 'C7'),
                weight=('normal' if row.rep else 'normal'),
            )

    return f, ax, dfplot


def plot_dispatch_weightwidth(
        case, val='Final Gen by timeslice (GW)', figsize=(13,4)):
    """
    Rep period dispatch for final year with period width given by period weight
    """
    ### Load run files
    hmap_myr = pd.read_csv(os.path.join(case, 'inputs_case', 'rep', 'hmap_myr.csv'))
    dispatch = (
        reeds.io.read_report(case, val)
        .drop(['scenario','Net Level Generation (GW)'], axis=1, errors='ignore')
        .pivot(index='timeslice',columns='tech',values='Generation (GW)'))
    bokehcolors = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    sw = reeds.io.get_switches(case)

    ### Get some settings
    GSw_HourlyChunkLength = int(sw.GSw_HourlyChunkLengthRep)
    hours_per_period = {'day':24, 'wek':120, 'year':24}[sw.GSw_HourlyType]
    dfplot = dispatch[[c for c in bokehcolors.index if c in dispatch]].copy()
    if sw.GSw_HourlyType == 'year':
        sznweights = hmap_myr['actual_period'].value_counts().sort_index() // hours_per_period
    else:
        sznweights = hmap_myr['season'].value_counts() // hours_per_period

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        1, len(sznweights), figsize=figsize, sharex=True, sharey=True,
        gridspec_kw={'wspace':0, 'width_ratios':sznweights.values},
    )
    for col, szn in enumerate(sznweights.index):
        date = reeds.timeseries.h2timestamp(szn).strftime('%Y-%m-%d')
        df = dfplot.loc[dfplot.index.str.startswith(szn)]
        plots.stackbar(df=df, ax=ax[col], colors=bokehcolors, align='edge', net=False)
        ax[col].axhline(0, c='k', ls=':', lw=0.75)
        if col:
            ax[col].axis('off')
        if sw.GSw_HourlyType != 'year':
            ax[col].axvline(0, c='w', lw=0.25)
            ax[col].annotate(f'{date} ({sznweights[szn]})', (0,1), xycoords='axes fraction', rotation=45)
    ### Formatting
    ax[0].set_xlim(0, hours_per_period / GSw_HourlyChunkLength)
    plots.despine(ax[0], bottom=False)
    ax[0].set_xticks([])
    ax[0].set_ylabel('Generation [GW]')

    return f, ax


def plot_interday_soc(
        case, t=2050, ba=None, tech=None, f=None, axes=None, figsize=(16,7), debug=False):
    """
    Plot inter-day storage state of charge.
    """
    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).str.lower()
    tech_map = tech_map.drop_duplicates().set_index('raw').display.str.lower()
    tech_style = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    sw = pd.read_csv(
        os.path.join(case,'inputs_case','switches.csv'), header=None, index_col=0).squeeze(1)
   
    # Read all necessary CSV files
    stor_interday_level = pd.read_csv(
        os.path.join(case,'outputs','stor_interday_level.csv'))
    stor_interday_dispatch = pd.read_csv(
        os.path.join(case,'outputs','stor_interday_dispatch.csv'))
    h_actualszn = pd.read_csv(
        os.path.join(case,'inputs_case','rep','h_actualszn.csv'))
    numpartitions = pd.read_csv(
        os.path.join(case,'inputs_case','rep','numpartitions.csv'))
    timestamps = pd.read_csv(
        os.path.join(case,'inputs_case','rep','timestamps.csv'))
   
    # Rename columns
    rename_rules = {
        'actual_period': 'allszn', '*h': 'allh', '*actual_period': 'allszn',
        'partition_count': 'Value', 'Value': 'Level'
    }
    for df in [stor_interday_level, stor_interday_dispatch, h_actualszn, numpartitions]:
        df.rename(columns={k: v for k, v in rename_rules.items() if k in df.columns}, inplace=True)
 
    # Create actualszn dataframe
    actualszn = h_actualszn[['allszn']].drop_duplicates()
    actualszn = actualszn.sort_values(by='allszn')
    actualszn = actualszn.reset_index(drop=True)
    data_dict = {}
 
    # Loop through all combinations of i, v, r, and t
    for idx, (i, r, t, v) in enumerate(stor_interday_level[['i', 'r', 't', 'v']].drop_duplicates().itertuples(index=False)):
        filtered_INTERDAY = stor_interday_level.query('r == @r & t == @t & i == @i & v == @v').reset_index(drop=True)
        filtered_DISPATCH = stor_interday_dispatch.query('r == @r & t == @t & i == @i & v == @v').reset_index(drop=True)
       
        # Convert dispatch from MW to MWh
        GSw_HourlyChunkLength = int(sw.GSw_HourlyChunkLengthRep)
        filtered_DISPATCH['Level'] = filtered_DISPATCH['Level'] * GSw_HourlyChunkLength
       
        # Merge the data to create actual hourly time series
        data = (actualszn.merge(filtered_INTERDAY, on='allszn', how='left')
                        .merge(numpartitions, on='allszn', how='left')
                        .merge(h_actualszn, on='allszn', how='left')
                        .merge(filtered_DISPATCH, on='allh', how='left'))
       
        # Create timestamp and merge with h_of_year
        data['timestamp'] = data["allszn"] + "h" + data["allh"].str.extract(r'h(\d{3})')[0]
        data = data.merge(timestamps[['h_of_year', 'timestamp']], on='timestamp', how='left')
       
        # Rename columns for clarity
        data.rename(columns={'Level_x': 'interday_level', 'Level_y': 'net_day_change', 'Value': 'partition'}, inplace=True)
       
        # Fill missing values
        data['interday_level'] = data['interday_level'].fillna(method='ffill').fillna(0)
        data['net_day_change'] = data['net_day_change'].fillna(0)
       
        # Sort by time to ensure proper ordering
        data = data.sort_values(['allszn', 'h_of_year']).reset_index(drop=True)
       
        # Calculate storage level using cumulative sum
        data['storage_level'] = data['interday_level'].iloc[0] + data['net_day_change'].cumsum()
       
        # Cleanup data frame
        data.drop(['i_x', 'v_x', 'r_x', 't_x'], axis=1, inplace=True, errors='ignore')
        data.rename(columns={'i_y': 'i', 'v_y': 'v', 'r_y': 'r', 't_y': 't'}, inplace=True)
        data[['i', 'v', 'r', 't']] = data[['i', 'v', 'r', 't']].ffill().bfill()
       
        # Append data to dictionary
        data_dict[idx] = data
   
    # Convert dictionary to data frame
    all_data = pd.concat(data_dict.values(), ignore_index=True)
 
    # Apply filters if specified
    if ba is not None:
        all_data = all_data[all_data['r'] == ba]
   
    if tech is not None:
        all_data = all_data[all_data['i'] == tech]
 
    # Aggregate all region storage levels
    all_data = all_data.groupby(['h_of_year', 'i', 'v', 't', 'allszn', 'allh']).agg({
        'storage_level': 'sum',
        'interday_level': 'sum',  
        'net_day_change': 'sum'  
    }).reset_index()
 
    # Assign year to plot
    t = int(all_data['t'].max())
    all_data = all_data[all_data['t'] == t]
   
    if debug:
        # Save the processed data for debugging
        all_data.to_csv(os.path.join(case, 'outputs', f'stor_interday_soc_{t}.csv'), index=False)
 
    # Assign colors based on technology
    all_data_simplified_techs = simplify_techs(all_data['i'])
    all_data['color'] = all_data_simplified_techs.map(tech_style)
 
    # Convert 'h_of_year' to datetime for plotting
    start_date = f"{t}-01-01"
    all_data['datetime'] = pd.to_datetime(start_date) + pd.to_timedelta(all_data['h_of_year'], unit='h')

    # Aggregate and sum over 'v' if multiple storage units of same tech exist
    all_data = all_data.groupby(['datetime', 'h_of_year', 'i']).agg({
        'storage_level': 'sum',
        'color': 'first'
    }).reset_index()
 
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
   
    for tech in all_data['i'].unique():
        tech_data = all_data[all_data['i'] == tech]
        ax.plot(
            tech_data['datetime'], tech_data['storage_level'],
            label=tech, color=tech_data['color'].iloc[0], linewidth=0.5
        )
 
    # Set datetime formatting for x-axis
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.set_ylabel('Storage Level (MWh)')
    ax.set_title(f'Inter-day Storage Level{" in " + ba if ba else ""} for Year {t}')
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
 
    return fig, ax, all_data


def get_stressperiods(case):
    """Get dataframe of stress periods sorted by year and iteration"""
    inpaths = [
        i for i in sorted(glob(os.path.join(case,'inputs_case','stress*')))
        if os.path.isdir(i)
    ]
    dictin_stressperiods = {
        tuple([int(x) for x in os.path.basename(f)[len('stress'):].split('i')]):
        pd.read_csv(os.path.join(f,'set_szn.csv'), index_col='*szn').squeeze(1)
        for f in inpaths
    }
    dfstress = pd.concat(dictin_stressperiods, names=['year','iteration']).sort_index()
    dfstress['date'] = dfstress.index.get_level_values('*szn').map(
        lambda x: reeds.timeseries.h2timestamp(x.strip('s')+'h01').strftime('%Y-%m-%d')
    )
    return dfstress


def plot_stressperiod_dispatch(case, tmin=2023, level='country', regions='USA'):
    """
    """
    ### Parse inputs
    if isinstance(regions, str):
        _regions = [regions.lower()]
    else:
        _regions = [r.lower() for r in regions]

    ### Get settings
    sw = reeds.io.get_switches(case)

    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*'))
    tech_map = tech_map.drop_duplicates().set_index('raw').display

    tech_style = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order',
    ).squeeze(1)

    hierarchy = reeds.io.get_hierarchy(case)
    keepr = hierarchy.loc[hierarchy[level].str.lower().isin(_regions)].index

    years = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')).columns.astype(int).values

    ### Get model outputs
    gen_h_stress = reeds.io.read_output(case, 'gen_h_stress', valname='GW')
    gen_h_stress.GW /= 1000
    gen_h_stress.i = gen_h_stress.i.str.lower()

    ### Get stress periods
    dfstress = get_stressperiods(case)

    ### Aggregate
    dispatch_agg = gen_h_stress.copy()
    dispatch_agg.i = dispatch_agg.i.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')
    ).str.lower().map(lambda x: tech_map.get(x,x))
    dispatch_agg = (
        dispatch_agg.loc[dispatch_agg.r.isin(keepr)]
        .groupby(['i','h','t'], as_index=False).GW.sum())

    dfplot = (
        dispatch_agg.pivot(index=['t','h'], columns='i', values='GW').fillna(0)
        .reindex(tech_style.index, axis=1).dropna(axis=1)
    )

    ### Get plot settings
    ncols = max([len(dfstress.loc[y].drop_duplicates()) for y in years])
    numh = (120 if sw.GSw_HourlyType == 'wek' else 24)//int(sw.GSw_HourlyChunkLengthStress)

    ts = sorted(dfplot.index.get_level_values('t').unique())
    ts = [t for t in ts if t > tmin]

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        len(ts), ncols, figsize=(1*ncols, 1*len(ts)), sharex=True, sharey=True,
        gridspec_kw={'hspace':0.5},
    )
    for row, t in enumerate(ts):
        dfyear = dfplot.loc[t]
        ### Plot "seed" stress periods first, then iteratively identified periods in order
        dfstress_year = dfstress.loc[t].drop_duplicates()
        stress_period_t = dfstress_year.index.get_level_values('*szn')
        for col in range(ncols):
            ### Turn off axis if unused
            if col >= len(stress_period_t):
                ax[row,col].axis('off')
                continue      
            ### Plot the dispatch for this stress period
            d = stress_period_t[col]
            dfday = dfyear.loc[dfyear.index.str.startswith(d)]
            plots.stackbar(dfday, ax[row,col], colors=tech_style, net=False, align='edge')
            ### Formatting
            ax[row,col].set_title(
                reeds.timeseries.h2timestamp(d+'h01').strftime('%Y-%m-%d'), y=0.92, fontsize=10)
        ### Formatting
        ax[row,0].annotate(
            t, (-0.8,0.5), xycoords='axes fraction', ha='right', va='center',
            weight='bold', fontsize=14)
        ### Draw a line between each iteration
        for col in range(dfstress_year.index.get_level_values('iteration').max()):
            ax[row,len(dfstress_year.loc[:col])-1].annotate(
                '', (1.075,0), xytext=(1.075,1), xycoords='axes fraction',
                annotation_clip=False,
                arrowprops={'arrowstyle':'-', 'color':'C7'},
            )
    ### Formatting
    ax[0,0].set_xlim(0, numh)
    ax[0,0].xaxis.set_major_locator(
        mpl.ticker.MultipleLocator(24//int(sw.GSw_HourlyChunkLengthStress)))
    ax[0,0].xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter(''))
    ax[0,0].annotate(
        'Stress period dispatch [GW]', (-0.5,1.5), xycoords='axes fraction',
        weight='bold', fontsize=14)
    plots.despine(ax)

    return f,ax


def plot_stressperiod_days(case, repcolor='k', sharey=False, figsize=(10,5)):
    """
    figsize [tuple]: Default to fill a ppt slide is (13.33,6.88)
    """
    ### Get shared parameters
    sw = reeds.io.get_switches(case)
    period_days = 5 if sw['GSw_HourlyType'] == 'wek' else 1
    yplot = 2012
    timeindex = pd.date_range(
        f'{yplot}-01-01', f'{yplot+1}-01-01', freq='H', tz='Etc/GMT+6')[:8760]
    ### Get rep periods
    szn_rep = pd.read_csv(
        os.path.join(case, 'inputs_case', 'rep', 'period_szn.csv')
    ).rep_period.sort_values()
    rep_starts = [reeds.timeseries.h2timestamp(d+'h01') for d in szn_rep]
    rep_hours = np.ravel([
        pd.date_range(h, h+pd.Timedelta(f'{period_days}D'), freq='H', inclusive='left')
        for h in rep_starts
    ])
    dfrep = pd.Series(
        index=timeindex,
        data=timeindex.map(lambda x: x.isin(rep_hours)).astype(int),
    )
    ### Want a dict of dataframes with 8760 index, columns for 'rep' + RA years,
    ### and keys for solve years
    dfplot = {}
    ### Get stress period IDs from output generation
    gen_h_stress = reeds.io.read_output(case, 'gen_h_stress', valname='MW')
    gen_h_stress['szn'] = gen_h_stress['h'].map(lambda x: x.split('h')[0])

    years = [
        y for y in sorted(gen_h_stress.t.unique())
        if int(y) >= int(sw.GSw_StartMarkets)
    ]
    colors = plots.rainbowmapper(sw.resource_adequacy_years_list)
    rep = f"rep ({sw.GSw_HourlyWeatherYears.replace('_',',')})"
    colors[rep] = repcolor

    t2periods = gen_h_stress.groupby('t').szn.unique()
    t2starts = t2periods.map(
        lambda row: [reeds.timeseries.h2timestamp(d+'h01') for d in row]
    )
    ## Use same procedure as dfpeak and diagnostic_plots.plot_netloadhours_timeseries()
    for t in years:
        if repcolor in ['none', None, False]:
            dictout = {}
        else:
            dictout = {rep: dfrep}
        for y in sw.resource_adequacy_years_list:
            yearstarts = [i for i in t2starts[t] if i.year == y]
            yearstarts_aligned = [
                pd.Timestamp(f'{yplot}-{i.month}-{i.day} 00:00', tz='Etc/GMT+6')
                for i in yearstarts
            ]
            yearhours = np.ravel([
                pd.date_range(
                    h, h+pd.Timedelta(f'{period_days}D'), freq='H', inclusive='left')
                for h in yearstarts_aligned
            ])
            dictout[y] = pd.Series(
                index=timeindex,
                data=timeindex.map(lambda x: x.isin(yearhours)).astype(int),
            )
        dfplot[t] = pd.concat(dictout, axis=1)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(len(years), 1, figsize=figsize, sharex=True, sharey=sharey)
    for row, t in enumerate(years):
        dfplot[t].plot.area(
            ax=ax[row], color=colors, lw=0,
            legend=(True if row == (len(years)-1) else False),
        )
        if row == (len(years) - 1):
            ax[row].legend(
                loc='upper right', bbox_to_anchor=(1,-0.3),
                ncols=dfplot[t].shape[1], frameon=False, fontsize='large',
                columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
            )
        ### Formatting
        ax[row].annotate(
            t,(0.005,0.95),xycoords='axes fraction',ha='left',va='top',
            weight='bold',fontsize='large')
        if not sharey:
            ax[row].set_ylim(0)
        ax[row].yaxis.set_major_locator(mpl.ticker.MultipleLocator(1))
        ax[row].yaxis.set_major_formatter(plt.NullFormatter())

    ### Formatting
    if sharey:
        ax[0].set_ylim(0)
    ylabel = (
        'Modeled stress periods' if repcolor in ['none', None, False]
        else 'Modeled periods (representative + stress)'
    )
    ax[-1].set_ylabel(ylabel, y=0, ha='left')
    plots.despine(ax)

    return f, ax


def plot_stressperiod_evolution(
        case, level=None, metric=None, threshold=None,
        figsize=None, scale_widths=False,
    ):
    """Plot NEUE by year and stress period iteration"""
    ### Parse inputs
    sw = reeds.io.get_switches(case)
    _level, _threshold, _, _metric = sw['GSw_PRM_StressThreshold'].split('/')[0].split('_')
    level = _level if level is None else level
    threshold = float(_threshold) if threshold is None else threshold
    metric = _metric if metric is None else metric
    ### Load NEUE results
    infiles = sorted(glob(os.path.join(case,'outputs','neue_*.csv')))
    dictin_neue = {
        tuple([int(x) for x in os.path.basename(f)[len('neue_'):-len('.csv')].split('i')]):
        pd.read_csv(f, index_col=['level','metric','region'])
        for f in infiles
    }
    ## Reshape to (year,iteration) x (region)
    dfplot = (
        pd.concat(dictin_neue, names=['year','iteration'])
        .xs(level,0,'level')
        .xs(metric,0,'metric')
        .NEUE_ppm.unstack('region')
    )
    ### Load stress periods for labels
    dfstress = get_stressperiods(case)
    ### Plot setup
    years = [
        y for y in dfplot.index.get_level_values('year').unique()
        if y >= int(sw.GSw_StartMarkets)
    ]
    ncols = len(years)
    regions = dfplot.columns
    colors = plots.rainbowmapper(regions)
    ### Plot it
    if figsize is None:
        figsize = (max(10, ncols*1.2), 3)
    width_ratios = dfstress.reset_index().groupby('year').iteration.max().loc[years].values + 1
    gridspec_kw = {'width_ratios':width_ratios} if scale_widths else None
    plt.close()
    f,ax = plt.subplots(
        1, ncols, sharey=True, figsize=figsize,
        gridspec_kw=gridspec_kw,
    )
    for col, year in enumerate(years):
        df = dfplot.loc[year]
        for region in regions:
            ax[col].plot(
                df.index, df[region],
                label=region, c=colors[region], marker='o', markersize=4,
            )
        ### Formatting
        ax[col].set_title(year)
        ax[col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(1))
        ax[col].axhline(threshold, lw=0.75, ls='--', c='0.7', zorder=-1e6)
        ax[col].set_xlim(-0.25, len(df)-0.75)
        ## Annotate the stress periods
        periods = dfstress.loc[year].drop_duplicates()
        note = '\n___________\n'.join([
            f'Iteration {i}:\n'
            + '\n'.join([
                f"{'+' if i else ''} {d}"
                for d in periods.loc[i].date.values
            ])
            for i in periods.index.get_level_values('iteration').unique()
        ])
        ax[col].annotate(
            note, (0,-0.15), xycoords='axes fraction',
            fontsize=10, va='top',
            annotation_clip=False,
        )
    ### Formatting
    ax[-1].legend(
        loc='upper left', bbox_to_anchor=(1,1), frameon=False,
        handletextpad=0.3, handlelength=0.7,
    )
    ax[0].set_ylabel('NEUE [ppm]')
    ax[0].set_ylim(0)
    plots.despine(ax)

    return f,ax


def plot_neue_bylevel(
        case, tmin=2023,
        levels=['country','interconnect','transreg','transgrp'],
        metrics=['sum','max'],
        onlydata=False,
    ):
    """Plot regional NEUE over time"""
    ### Get final iterations
    year2iteration = (
        pd.DataFrame([
            os.path.basename(i).strip('neue_.csv').split('i')
            for i in sorted(glob(os.path.join(case, 'outputs', 'neue_*.csv')))
        ], columns=['year','iteration']).astype(int)
        .drop_duplicates(subset='year', keep='last')
        .set_index('year').iteration
        .loc[tmin:]
    )
    ### Get NEUE
    sw = reeds.io.get_switches(case)
    sw['casedir'] = case
    dictin_neue = {}
    for t, iteration in year2iteration.items():
        try:
            dictin_neue[t] = (
                reeds.io.read_output(case, f'neue_{t}i{iteration}.csv')
                .set_index(['level','metric','region']).squeeze(1)
            )
        except FileNotFoundError:
            dictin_neue[t] = (
                reeds.io.read_output(case, f'neue_{t}i{iteration-1}.csv')
                .set_index(['level','metric','region']).squeeze(1)
            )
    dfin_neue = pd.concat(dictin_neue, axis=0, names=['year']).unstack('year')
    dfin_neue = dfin_neue[[c for c in dfin_neue if int(c) >= 2025]].copy()
    if onlydata:
        return dfin_neue
    ### Plot settings
    ncols = len(levels)
    nrows = len(metrics)
    colors = {
        level: plots.rainbowmapper(
            dfin_neue.xs(level,0,'level').reset_index().region.unique())
        for level in levels
    }
    norm = {'sum':1, 'max':1e-4}
    ylabel = {'sum': 'Sum of NEUE [ppm]', 'max':'Max NEUE [%]'}
    thresholds = {
        i.split('_')[0]: float(i.split('_')[1])
        for i in sw.GSw_PRM_StressThreshold.split('/')
    }
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(2*ncols, 3*nrows),
        sharex=True, sharey='row',
    )
    for row, metric in enumerate(metrics):
        for col, level in enumerate(levels):
            for region, c in colors[level].items():
                ax[row,col].plot(
                    dfin_neue.columns,
                    dfin_neue.loc[(level,metric,region)].values * norm[metric],
                    c=c, label=region, marker='o', markersize=2,
                )
        ## Formatting
        ax[row,0].set_ylabel(ylabel[metric])
    ## Formatting
    for col, level in enumerate(levels):
        ax[0,col].set_title(level)
        if (level in thresholds) and (not int(sw.GSw_PRM_CapCredit)):
            ax[0,col].axhline(thresholds[level], c='k', ls=':', lw=0.75)
        leg = ax[0,col].legend(
            loc='upper left', frameon=False, fontsize=8,
            handletextpad=0.3, handlelength=0.7, columnspacing=0.5, labelspacing=0.2,
            ncol=(2 if len(colors[level]) >= 10 else 1),
        )
        for legobj in leg.legend_handles:
            legobj.set_linewidth(6)
            legobj.set_solid_capstyle('butt')

    for row in range(2):
        ax[row,0].set_ylim(0)
    ax[0,0].set_ylim(0, min(ax[0,0].get_ylim()[1], 1000))
    plots.despine(ax)

    return f, ax, dfin_neue


def map_neue(
        case, year=2050, iteration='last', samples=None, metric='sum',
        vmax=10., cmap=cmocean.cm.rain, label=True,
        over_vmax_mapcolor=None,
        over_threshold_textcolor='C3',
        highlight_over_threshold=True,
    ):
    """
    """
    ### Parse inputs
    assert metric in ['sum','max']
    cm = cmap.copy()
    if over_vmax_mapcolor:
        cm.set_over(over_vmax_mapcolor)

    ### Get data
    if iteration == 'last':
        _, _iteration = reeds.io.get_last_iteration(
            case=case, year=year, samples=samples)
    else:
        _iteration = iteration
    neue = reeds.io.read_output(case, f'neue_{year}i{_iteration}.csv')
    neue = neue.loc[neue.metric==metric].set_index(['level','region']).NEUE_ppm
    sw = reeds.io.get_switches(case)
    neue_threshold = float(sw.GSw_PRM_StressThreshold.split('_')[1])
    neue_threshold_level = sw.GSw_PRM_StressThreshold.split('_')[0]

    ### Set up plot
    levels = ['interconnect','nercr','transreg','transgrp','st','r']
    nrows, ncols, coords = plots.get_coordinates(levels, aspect=1.3)
    dfmap = reeds.io.get_dfmap(case)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(13.33, 6.88), sharex=True, sharey=True,
        gridspec_kw={'hspace':-0.05, 'wspace':-0.05},
    )
    for level in levels:
        ## Background
        dfmap['country'].plot(
            ax=ax[coords[level]], facecolor='none', edgecolor='k', lw=0.5, zorder=1e7)
        dfmap[level].plot(
            ax=ax[coords[level]], facecolor='none', edgecolor='k', lw=0.1, zorder=1e6)
        ax[coords[level]].set_title(level, y=0.9, weight='bold')
        ## Data
        df = dfmap[level].copy()
        df['NEUE_ppm'] = neue[level]
        df.plot(ax=ax[coords[level]], column='NEUE_ppm', cmap=cm, vmin=0, vmax=vmax)
        ## Labels
        # decimals = (0 if df.NEUE_ppm.max() >= 10 else 1)
        decimals = (0 if level in ['st','r'] else 1)
        for r, row in df.sort_values('NEUE_ppm').iterrows():
            if highlight_over_threshold:
                over_threshold = row.NEUE_ppm > neue_threshold
            else:
                over_threshold = False
            ax[coords[level]].annotate(
                f"{row.NEUE_ppm:.{decimals}f}",
                [row.centroid_x, row.centroid_y],
                ha='center', va='center',
                c=(over_threshold_textcolor if over_threshold else 'k'),
                weight=('bold' if over_threshold else 'normal'),
                fontsize={'r':5}.get(level,7),
                zorder=1e9,
                path_effects=[pe.withStroke(linewidth=1.5, foreground='w', alpha=0.7)],
            )
            if over_threshold and (level == neue_threshold_level):
                ax[coords[level]].set_title(
                    level, y=0.9, weight='bold', color=over_threshold_textcolor,
                )
    ### Formatting
    plots.addcolorbarhist(
        f=f, ax0=ax[coords[level]], data=df.NEUE_ppm,
        cmap=cm, vmin=0., vmax=vmax, histratio=0, extend='max',
        cbarbottom=0.525, cbarheight=0.9,
    )
    for row in range(nrows):
        for col in range(ncols):
            ax[row,col].axis('off')

    return f, ax, neue, _iteration


def map_h2_capacity(
        case, year=2050, wscale_h2=10, figheight=6, pipescale=0.1,
        legend_kwds={'shrink':0.6, 'pad':0, 'orientation':'horizontal', 'aspect':12},
        cmap=cmocean.cm.rain, 
    ):
    """
    H2 turbines, production (electrolyzer/SMR), pipelines, and storage
    """
    ### Inputs
    t2kt = 0.001
    disaggregate_types = False
    miles = 300

    if disaggregate_types:
        h2colors = {
            'h2_storage_saltcavern':'s', 'h2_storage_hardrock':'D', 'h2_storage_undergroundpipe':'o',
            'electrolyzer':'^', 'h2_turbine':'v',
        }
    else:
        h2colors = {'h2_storage': 'C1', 'electrolyzer': 'C0', 'h2_turbine': 'C3', 'h2_pipeline':'C9'}

    ### Get the BA map
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']

    scalars = reeds.io.get_scalars(case)
    h2_combustion_intensity = 1e6 / scalars['h2_energy_intensity'] / scalars['lb_per_tonne']

    ### Load storage capacity
    h2_storage_cap_in = reeds.io.read_output(case, 'h2_storage_cap')
    h2_storage_cap = (
        h2_storage_cap_in.loc[h2_storage_cap_in.t==year]
        .pivot(index='r', columns='h2_stor', values='Value').fillna(0)
        * t2kt
    )
    if not disaggregate_types:
        h2_storage_cap = h2_storage_cap.sum(axis=1).rename('h2_storage')
    cap_storage = dfba.merge(h2_storage_cap, left_index=True, right_index=True)

    ### Load H2 turbine capacity, convert to kT/day
    cap_ivrt_in = reeds.io.read_output(case, 'cap_ivrt')
    cap_ivrt = cap_ivrt_in.loc[
        cap_ivrt_in.i.map(lambda x: 'h2' in x.lower())
        & (cap_ivrt_in.t==year)
    ].set_index(['i','v','r']).Value
    heat_rate_in = reeds.io.read_output(case, 'heat_rate')
    heat_rate = heat_rate_in.loc[heat_rate_in.t==year].set_index(['i','v','r']).Value
    ## capacity [MW] * heat rate [MMBtu/MWh] * [metric ton/MMBtu] / 1000 * [24h/d] = [kT per day]
    cap_h2turbine = (
        cap_ivrt.multiply(heat_rate).dropna() * h2_combustion_intensity / 1000 * 24
    ).rename('kTperday').groupby('r').sum()
    ## Merge with zone map
    cap_h2turbine = dfba.merge(cap_h2turbine, left_index=True, right_index=True)

    ### Get H2 production capacity
    prod_cap_in = reeds.io.read_output(case, 'prod_cap')
    h2_prod_cap = prod_cap_in.loc[
        ~prod_cap_in.i.str.lower().isin(['dac'])
        & (prod_cap_in.t==year)
    ].groupby('r').Value.sum().rename('kTperday') / 1000 * 24
    ## Merge with zone map
    cap_h2prod = dfba.merge(h2_prod_cap, left_index=True, right_index=True)

    ### Load pipeline capacity
    h2_trans_cap_in = reeds.io.read_output(case, 'h2_trans_cap')
    h2_trans_cap = h2_trans_cap_in.loc[h2_trans_cap_in.t==year].rename(columns={'Value':'kTperday'})
    h2_trans_cap.kTperday *= 24 / 1000

    h2_trans_cap['r_x'] = h2_trans_cap.r.map(dfba.x)
    h2_trans_cap['r_y'] = h2_trans_cap.r.map(dfba.y)
    h2_trans_cap['rr_x'] = h2_trans_cap.rr.map(dfba.x)
    h2_trans_cap['rr_y'] = h2_trans_cap.rr.map(dfba.y)

    ### Plot as separate maps
    bounds = dfmap['country'].bounds.loc['USA']
    aspect = abs((bounds.maxx - bounds.minx) / (bounds.maxy - bounds.miny))
    plt.close()
    f,ax = plt.subplots(2,2,sharex=True,sharey=True,figsize=(figheight*aspect,figheight))
    ### Background
    for row in range(2):
        for col in range(2):
            dfba.plot(ax=ax[row,col], edgecolor='0.5', facecolor='none', lw=0.1, zorder=1e4)
            dfmap['st'].plot(ax=ax[row,col], edgecolor='0.25', facecolor='none', lw=0.2, zorder=1e4)
            ax[row,col].axis('off')
    ### H2 turbines
    if not cap_h2turbine.empty:
        cap_h2turbine.plot(
            ax=ax[0,0], column='kTperday', cmap=cmap, lw=0, vmin=0,
            legend=True, legend_kwds={**legend_kwds, **{'label':'Turbines [kT/day]'}})
    ### Electrolyzers
    if not cap_h2prod.empty:
        cap_h2prod.plot(
            ax=ax[0,1], column='kTperday', cmap=cmap, lw=0, vmin=0,
            legend=True, legend_kwds={**legend_kwds, **{'label':'Production [kT/day]'}})
    ### Storage
    if not cap_h2prod.empty:
        cap_storage.plot(
            ax=ax[1,0], column='h2_storage', cmap=cmap, lw=0, vmin=0,
            legend=True, legend_kwds={**legend_kwds, **{'label':'Storage [kT]'}})
    ### Pipelines
    if not h2_trans_cap.empty:
        for i,row in h2_trans_cap.iterrows():
            ax[1,1].plot(
                [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
                color=h2colors['h2_pipeline'], lw=wscale_h2*row['kTperday'], solid_capstyle='butt',
                alpha=0.7,
            )
    if pipescale:
        ax[1,1].plot(
            -1.75e6 + np.array([-1609/2*miles,1609/2*miles]),
            [-1.0e6, -1.0e6], solid_capstyle='butt',
            color=h2colors['h2_pipeline'], lw=wscale_h2*pipescale,
        )
        ax[1,1].annotate(
            f'Transport\n[{pipescale} kT/day]', (-1.75e6, -1.1e6),
            ha='center', va='top', weight='bold', fontsize='x-large')

    return f,ax


def plot_h2_timeseries(
        case, year=2050, agglevel='transreg', grid=0,
        figsize=(12,8),
    ):
    """
    """
    ### Load results in metric ton and metric ton/hour
    h2techs = ['electrolyzer','smr','smr_ccs']
    h2_storage_level = reeds.io.read_output(case, 'h2_storage_level')
    h2_storage_level_szn = reeds.io.read_output(case, 'h2_storage_level_szn')
    h2_inout = reeds.io.read_output(case, 'h2_inout')
    prod_produce = reeds.io.read_output(case, 'prod_produce')
    h2_usage = reeds.io.read_output(case, 'h2_usage')
    ### Timeseries data
    hmap_myr = pd.read_csv(os.path.join(case, 'inputs_case', 'rep', 'hmap_myr.csv'))

    ###### Total across modeled area
    hierarchy = reeds.io.get_hierarchy(case)
    if agglevel == 'r':
        rmap = pd.Series(hierarchy.index.values, index=hierarchy.index.values)
    else:
        rmap = hierarchy[agglevel]

    ### Combine into one dataframe
    dfall = {
        'production': prod_produce.assign(r=prod_produce.r.map(rmap)).loc[
            prod_produce.i.isin(h2techs) & (prod_produce.t==year)
        ].groupby(['r','h']).Value.sum(),
        'usage': -h2_usage.assign(r=h2_usage.r.map(rmap)).loc[
            (h2_usage.t==year)
        ].groupby(['r','h']).Value.sum(),
        ## Group over H2 storage techs
        'stor_charge': h2_inout.assign(r=h2_inout.r.map(rmap)).loc[
            (h2_inout['*'].str.lower() == 'in') & (h2_inout.t==year)
        ].groupby(['r','h']).Value.sum(),
        'stor_discharge': -h2_inout.assign(r=h2_inout.r.map(rmap)).loc[
            (h2_inout['*'].str.lower() == 'out') & (h2_inout.t==year)
        ].groupby(['r','h']).Value.sum(),
    }
    dfall = pd.concat(dfall, axis=1).fillna(0)
    dfall['stor_dispatch'] = dfall['stor_discharge'] + dfall['stor_charge']
    ### Broadcast representative to actual
    dffull = dfall.unstack('r').reindex(hmap_myr.h)
    dffull.index = (
        hmap_myr.rename(columns={'actual_period':'actualszn','actual_h':'allh'})
        .set_index(['actualszn','h']).index)
    dffull = dffull.reorder_levels(['r',None],axis=1)
    ### Include storage level
    if len(h2_storage_level):
        storstack = (
            h2_storage_level.assign(r=h2_storage_level.r.map(rmap))
            .loc[(h2_storage_level.t==year)]
            .groupby(['r','actualszn','h']).Value.sum()
            .rename('stor_level').to_frame().unstack('r')
            .reorder_levels(['r',None], axis=1)
        )
    else:
        storstack = (
            h2_storage_level_szn.assign(r=h2_storage_level_szn.r.map(rmap))
            .loc[(h2_storage_level_szn.t==year)]
            .groupby(['r','actualszn' ]).Value.sum()
            .rename('stor_level').to_frame().unstack('r')
            .reorder_levels(['r',None], axis=1)
            .reindex(hmap_myr.actual_period.values).fillna(0)
        )
    dffull[storstack.columns] = storstack.values
    dffull.columns = dffull.columns.rename(['r','datum'])
    ## Convert to kT
    dffull /= 1000

    ### Don't chunk it
    dfchunk = dffull.fillna(0).round(3).copy()
    timeindex = (hmap_myr.actual_h.map(reeds.timeseries.h2timestamp)).values

    ###### Plot it
    rows = {
        'production':0,
        'stor_charge':1,
        'stor_discharge':2,
        'usage':3,
        'stor_level':4,
    }
    ylabels = {
        'production':'Production\n[kT/day]',
        'stor_charge':'Injection\n[kT/day]',
        'stor_discharge':'Withdrawal\n[kT/day]',
        'usage':'Turbine use\n[kT/day]',
        'stor_level':'Reservoir\nlevel [kT]',
    }
    scale = {k: (24 if 'day' in v else 1) for k,v in ylabels.items()}
    colors = plots.rainbowmapper(dfchunk.columns.get_level_values('r').unique())
    if len(colors) == 1:
        colors[list(colors.keys())[0]] = 'C0'

    ###### Plot it
    plt.close()
    f,ax = plt.subplots(len(rows), 1, sharex=True, sharey=False, figsize=figsize)
    ## Stop here if there's no data
    if dfchunk.empty:
        return f, ax, dfchunk
    ### Data
    for datum, row in rows.items():
        df = dfchunk.xs(datum, axis=1, level='datum') * scale[datum]
        df.index = timeindex
        order = df.columns
        dfplot = df[order[::-1]].cumsum(axis=1)[order]
        dfplot.plot.area(
            ax=ax[row], color=colors, stacked=False, legend=(not row),
            lw=0, alpha=1,
        )
        ax[row].set_ylabel(ylabels[datum])
    ###### Formatting
    ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1), frameon=False,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        fontsize=12,
    )
    ### Scales
    ymax = (dfchunk.groupby(axis=1, level='datum').sum()
            [['production','stor_discharge']].sum(axis=1).max()) * 24
    ymin = (dfchunk.groupby(axis=1, level='datum').sum()
            [['usage','stor_charge']].sum(axis=1).min()) * 24
    scalerows = [v for k,v in rows.items() if 'level' not in k]
    for row in scalerows:
        ax[row].set_ylim(ymin, ymax)
        ax[row].axhline(0, c='k', ls=':', lw=0.5)
        if grid:
            ax[row].grid(which='minor', axis='x', c='C7', ls=':', lw=grid)
    ax[0].set_xlim(
        df.index[0].strftime('%Y-%m-%d'),
        df.index[-1].strftime('%Y-%m-%d') + ' 23:59'
    )
    plots.despine(ax)

    return f, ax, dfchunk


def get_import_export(region, df):
    """"""
    firsts = [c for c in df if c.startswith(region)]
    lasts = [c for c in df if c.endswith(region)]
    net = df[firsts].sum(axis=1) - df[lasts].sum(axis=1)
    exports = -net.clip(lower=0)
    imports = net.clip(upper=0).abs()
    return pd.concat({'net import':imports, 'net export':exports}, axis=1)


def map_period_dispatch(
        case, year=2050, level='transreg',
        period='max load',
        transmission=True, gen=True,
        wscale='auto', width_total=1e5,
        drawstates=0, drawzones=0, drawgrid=False, legend=True,
        onlydata=False,
        scale_val=100, scale_x=0.4e6, scale_y=-1.45e6,
    ):
    """
    Notes
    * Currently only works for stress periods
    """
    # ### Inputs for debugging
    # case = os.path.join(
    #     reeds_path,'runs',
    #     'v20240212_transopM0_WECC_CPNP_GP1_TFY2035_PTL2035_TRc_MITCg0p3')
    # case = (
    #     '/Volumes/ReEDS/Users/pbrown/ReEDSruns/20240115_transop/20240217/'
    #     'v20240217_transopK0_CPNP_GP1_TFY32_PTL32_TRc_TCa1p0_MTCg0p3'
    #     # 'v20240217_transopK1_CPNP_GP1_TFY35_PTL50_TRt_TCa1p15_MTCg0p0'
    # )
    # year = 2050
    # level = 'transreg'
    # transmission = False
    # gen = True
    # wscale='auto'
    # width_total=1e5
    # drawstates=0.
    # drawzones=0.
    # drawgrid=False
    # legend=True
    # periods = ['max gen','max load','min solar','min wind','min vre']
    # periods = ['2009-01-15','2012-09-15']
    # onlydata = False

    ### Shared inputs
    hierarchy = reeds.io.get_hierarchy(case)
    dfmap = reeds.io.get_dfmap(case)
    dfba = dfmap['r']

    ## Region centers
    _dfcenter = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','plots','transmission-interface-coords.csv'),
        index_col=['level','region1','region2'],
    ).drop('drop',axis=1)
    if level in _dfcenter.index.get_level_values('level'):
        _dfcenter = _dfcenter.loc[level].reset_index()
        _dfcenter[['x','y']] *= 1e6
        dfcenter = (
            _dfcenter
            .loc[~_dfcenter.index.duplicated()]
            .loc[_dfcenter.region1 == _dfcenter.region2]
            .rename(columns={'region1':'aggreg'})
            .drop(['region2','angle'], axis=1)
            .set_index('aggreg')
        )
        ## Transmission interfaces, with reverse direction
        dfcorridors = pd.concat([
            _dfcenter,
            _dfcenter.assign(region1=_dfcenter.region2).assign(region2=_dfcenter.region1)
        ], axis=0).set_index(['region1','region2'])
    else:
        dfcenter = dfmap[level][['centroid_x','centroid_y']].rename(columns={'centroid_x':'x','centroid_y':'y'})
        dfcorridors = pd.concat({
            r: pd.DataFrame({
                'x': (dfcenter.loc[r,'x'] + dfcenter['x']) / 2,
                'y': (dfcenter.loc[r,'y'] + dfcenter['y']) / 2,
                'angle': np.arctan(
                    (dfcenter.loc[r,'y'] - dfcenter['y'])
                    / (dfcenter.loc[r,'x'] - dfcenter['x'])
                ) * 180 / np.pi
            })
            for r in dfcenter.index
        }, names=['region1','region2']).dropna(subset='angle')

    dfcorridors = dfcorridors.loc[~dfcorridors.index.duplicated()].copy()

    ## Colors
    bokehcolors = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)

    # tech_map = pd.read_csv(
    #     os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'),
    #     index_col='raw').squeeze(1)
        
    bokehcolors = pd.concat([
        bokehcolors.loc['smr':'electrolyzer'],
        pd.Series('#D55E00', index=['dac'], name='color'),
        bokehcolors.loc[:'Canada'],
    ])

    bokehcolors['canada'] = bokehcolors['Canada']
    bokehcolors['net import'] = '0.7'
    bokehcolors = pd.concat([pd.Series({'net export':'0.7'}, name='color'), bokehcolors])

    ### Parse and check inputs
    if level == 'r':
        regions = hierarchy.index.values
        r2aggreg = dict(zip(regions,regions))
    else:
        regions = hierarchy[level].unique()
        r2aggreg = hierarchy[level].copy()
    if len(dfcenter.drop_duplicates('x')) != len(dfcenter):
        raise ValueError('Use unique x values in transmissioninterface-coords.csv')

    ### Get outputs
    gen_h_stress = reeds.io.read_output(case, 'gen_h_stress', valname='GW')
    gen_h_stress.GW /= 1000
    gen_h_stress.i = simplify_techs(gen_h_stress.i)

    ## Aggregate transmission flows
    tran_flow_stress = reeds.io.read_output(case, 'tran_flow_stress', valname='GW')
    tran_flow_stress.GW /= 1e3

    tran_flow_stress['aggreg'] = tran_flow_stress.r.map(r2aggreg)
    tran_flow_stress['aggregg'] = tran_flow_stress.rr.map(r2aggreg)
    tran_flow_stress['interface'] = tran_flow_stress.aggreg + '|' + tran_flow_stress.aggregg

    tran_flow_stress_agg = (
        tran_flow_stress
        .loc[tran_flow_stress.aggreg != tran_flow_stress.aggregg]
        .groupby(['t','h','interface']).GW.sum().unstack('interface').fillna(0)
    )

    ## Load
    load_stress = reeds.io.read_output(case, 'load_stress', valname='GW')
    load_stress.GW /= 1e3
    dfload_allperiods = (
        load_stress.assign(region=load_stress.r.map(r2aggreg))
        .groupby(['t','region','h']).GW.sum()
        .loc[year].unstack('region')
    )
    dfload_allperiods['szn'] = dfload_allperiods.index.map(lambda x: x.split('h')[0])
    dfload_allperiods = dfload_allperiods.reset_index().set_index(['szn','h'])

    sw = reeds.io.get_switches(case)
    numsteps = 24 // int(sw['GSw_HourlyChunkLengthStress']) * (5 if sw['GSw_HourlyType'] == 'wek' else 1)

    ### Map dispatch to level
    gen_h_stress['aggreg'] = gen_h_stress.r.map(r2aggreg)
    gen_h_stress_agg = (
        gen_h_stress.loc[gen_h_stress.t==year]
        .groupby(['aggreg','i','h'], as_index=False).GW.sum()
    )
    gen_h_stress_agg['szn'] = gen_h_stress_agg.h.str.split('h', expand=True)[0]
    gen_h_stress_agg = gen_h_stress_agg.set_index(['szn','aggreg','h','i']).GW.unstack(['i']).fillna(0)

    ### Keep a single day
    if period == 'max gen':
        top_periods = gen_h_stress_agg.groupby('szn').sum().sum(axis=1).sort_values(ascending=False)
        keep_period = top_periods.index[0]
    elif period == 'max load':
        keep_period = dfload_allperiods.sum(axis=1).groupby('szn').max().nlargest(1).index[0]
    elif period == 'min solar':
        keep_period = (
            gen_h_stress_agg
            [[c for c in gen_h_stress_agg if (('pv' in c) or ('csp' in c))]].sum(axis=1)
            .groupby('szn').sum()
            .nsmallest(1)
            .index[0]
        )
    elif period == 'min wind':
        keep_period = (
            gen_h_stress_agg
            [[c for c in gen_h_stress_agg if ('wind' in c)]].sum(axis=1)
            .groupby('szn').sum()
            .nsmallest(1)
            .index[0]
        )
    elif period == 'min vre':
        keep_period = (
            gen_h_stress_agg
            [[c for c in gen_h_stress_agg if (('pv' in c) or ('csp' in c) or ('wind' in c))]].sum(axis=1)
            .groupby('szn').sum()
            .nsmallest(1)
            .index[0]
        )
    ## Otherwise we're dealing with timestamps
    else:
        if period.startswith('sy'):
            keep_period = period
        else:
            timestamp = pd.Timestamp(period)
            keep_period = 's' + reeds.timeseries.timestamp2h(timestamp).split('h')[0]

    hours = sorted(list(set(sorted([i for i in gen_h_stress.h if i.startswith(keep_period)]))))
    dfgen = gen_h_stress_agg.loc[keep_period].reindex(bokehcolors.index, axis=1).dropna(axis=1, how='all')
    dfload = dfload_allperiods.loc[keep_period].copy()

    ### Add imports and exports
    if len(tran_flow_stress_agg.loc[year]):
        dfimportexport = {}
        for region in regions:
            dfimportexport[region] = get_import_export(
                region=region, df=tran_flow_stress_agg.loc[year].reindex(hours).fillna(0)
            )
        dfimportexport = pd.concat(dfimportexport)
        dfgen = pd.concat([dfgen, dfimportexport], axis=1)

    ### Get transmission flows from westmost to eastmost region of each interface
    if transmission:
        dftrans = tran_flow_stress_agg.loc[year].reindex(hours).fillna(0).copy()
        regions_sorted = dfcenter.sort_values('x').index.tolist()
        for interface in dftrans:
            r1, r2 = interface.split('|')
            if regions_sorted.index(r2) < regions_sorted.index(r1):
                dftrans[interface] *= -1
                dftrans = dftrans.rename(columns={interface:f'{r2}|{r1}'})
        dftrans = dftrans.groupby(axis=1, level='interface').sum()
    else:
        dftrans = pd.DataFrame()

    out = {'gen':dfgen, 'load':dfload, 'trans':dftrans}
    if onlydata:
        return out

    ### Plot settings
    width_step = width_total / numsteps * 2
    if wscale in ['auto','scale','default',None,'','max']:
        capmax = dfgen.groupby('h').sum().sum(axis=1).max()
        _wscale = 3e6 / capmax * 0.95
    else:
        _wscale = wscale

    ###### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(12,8))
    ### Plot background
    dfmap[level].plot(
        ax=ax, facecolor='none', edgecolor='k', lw=(0.25 if level == 'r' else 1),
    )
    if drawstates:
        dfmap['st'].plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawstates)
    if drawzones:
        dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawzones)

    if gen:
        for region in regions:
            x, y = dfcenter.loc[region]
            ### Dispatch stack
            _dfgen = dfgen.loc[region] * _wscale
            _dfgen.index = np.linspace(-1,1,numsteps+1)[:numsteps] * width_total
            y -= _dfgen.sum(axis=1).max() / 2
            plots.stackbar(
                df=_dfgen,
                ax=ax, colors=bokehcolors, width=width_step, net=False,
                bottom=y, x0=x,
            )
            ax.plot(
                x + _dfgen.index.values * (1 + width_step / width_total / 2),
                [y]*len(_dfgen),
                c='k', ls=':', lw=0.75)
            ### Demand
            _dfload = dfload[region] * _wscale
            _dfload.index = _dfgen.index + x
            for i, (x, val) in enumerate(_dfload.items()):
                ax.plot(
                    [x-width_step/2*0.85, x+width_step/2*0.85], [val+y]*2,
                    c='k', ls='-', lw=1,
                    solid_capstyle='butt',
                )

    if transmission:
        for interface in dftrans:
            r1, r2 = interface.split('|')
            x, y , angle = dfcorridors.loc[(r1, r2)]
            df = dftrans[interface] * _wscale
            df.index = np.linspace(-1,1,numsteps+1)[:numsteps] * width_total
            plots.stackbar(
                df=df.rename('trans').to_frame(),
                ax=ax, colors={'trans':'0.7'}, width=width_step, net=False,
                bottom=y, x0=x,
            )
            ax.plot(
                x + df.index.values * (1 + width_step / width_total / 2),
                [y]*len(df),
                c='k', ls=':', lw=0.75)

    ###### Legend
    if legend:
        handles = [
            mpl.patches.Patch(facecolor=bokehcolors[i], edgecolor='none', label=i)
            for i in bokehcolors.index if i in dfgen.columns
        ]
        _leg = ax.legend(
            handles=handles[::-1], loc='lower left', fontsize=9, ncol=1, frameon=False,
            bbox_to_anchor=(0.9,0.02),
            handletextpad=0.3, handlelength=0.7, columnspacing=0.5, 
        )
    ### Scale
    if scale_val:
        bottom = scale_y - (scale_val * _wscale / 2)
        ## -1.3e6, -1.3e6
        ax.bar(
            x=[scale_x], height=[scale_val * _wscale], bottom=[bottom],
            color='k', width=width_step,
        )
        ax.annotate(
            '',
            xy=(scale_x+0.06e6, bottom),
            xytext=(scale_x+0.06e6, bottom + scale_val * _wscale),
            arrowprops={'arrowstyle':'<->', 'color':'k', 'shrinkA':0, 'shrinkB':0},
        )
        ax.annotate(
            f" {scale_val} GW",
            (scale_x+0.04e6, scale_y), va='center', fontsize=16,
        )
        ax.annotate(
            '',
            xy=(scale_x-width_step, bottom-0.06e6),
            xytext=(scale_x+width_step, bottom-0.06e6),
            arrowprops={
                # 'arrowstyle':'|-|', 'color':'k', 'shrinkA':0, 'shrinkB':0, 'mutation_scale':2},
                'arrowstyle':'<->', 'color':'k', 'shrinkA':0, 'shrinkB':0},
            annotation_clip=False,
        )
        ax.annotate(
            f" {sw.GSw_HourlyChunkLengthStress} hours",
            (scale_x, bottom), va='top', fontsize=16,
        )

    ###### Formatting
    ax.axis('off')
    timestring = reeds.timeseries.h2timestamp(keep_period+'h01').strftime('%Y-%m-%d')
    ax.annotate(
        (timestring if period == timestring else f"{period}\n{timestring}"),
        (0.2,0.2), xycoords='axes fraction', ha='right', va='top', fontsize=18,
    )
    ### Grid
    if drawgrid:
        ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5e6))
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.grid(which='major', ls=':', lw=0.75)
        ax.grid(which='minor', ls=':', lw=0.25)
        ax.axis('on')

    return f, ax, out


def plot_seed_stressperiods(
    case, cmap=cmocean.cm.phase, startfrom=200,
    alpha=0.7, fontsize=5, pealpha=0.8, pelinewidth=1.5,
):
    """
    """
    sys.path.append(os.path.join(reeds.io.reeds_path, 'input_processing'))
    import hourly_repperiods

    sw = reeds.io.get_switches(case)
    hierarchy = reeds.io.get_hierarchy(case)
    dfmap = reeds.io.get_dfmap(case)

    years = pd.read_csv(
        os.path.join(os.path.join(case,'inputs_case','modeledyears.csv'))
    ).columns.astype(int).values
    years = [y for y in years if y >= int(sw.GSw_StartMarkets)]

    ### Get seed Stress periods
    dictin_seed = {}
    for year in years:
        dictin_seed[year] = pd.read_csv(
            os.path.join(case, 'inputs_case', f'stress{year}i0', 'forceperiods.csv')
        )
        dictin_seed[year]['timestamp'] = dictin_seed[year].szn.map(reeds.timeseries.h2timestamp)
        dictin_seed[year]['date'] = dictin_seed[year].timestamp.map(lambda x: x.strftime('%Y-%m-%d'))
        dictin_seed[year]['monthday'] = dictin_seed[year].timestamp.map(lambda x: x.strftime('%m-%d'))

    days_of_year = pd.date_range('2004-01-01','2004-12-31',freq='D')
    monthdays = days_of_year.strftime('%m-%d')

    ### Recalculate peak load days since we dropped duplicates above
    load_allyears = hourly_repperiods.get_load(
        os.path.join(case, 'inputs_case'),
        keep_weatheryears='all').loc[years]
    timestamps = pd.read_csv(os.path.join(case, 'inputs_case', 'rep', 'timestamps.csv'))
    resource_adequacy_years = [int(y) for y in sw.resource_adequacy_years.split('_')]
    timestamps = timestamps.loc[timestamps.year.isin(resource_adequacy_years)].copy()
    ## Add descriptive index
    load_allyears.index = (
        pd.concat(
            {y: timestamps for y in years},
            axis=0, names=['modelyear','h_of_modelyear']).reset_index()
        .set_index(['modelyear','year','yperiod','h_of_period']).index
    )
    stressperiods_load = {
        y: hourly_repperiods.identify_peak_containing_periods(
            df=load_allyears.loc[y], hierarchy=hierarchy,
            level=sw['GSw_PRM_StressSeedLoadLevel'])
        for y in years
    }

    ### Put cold colors in winter
    colorvals = (
        list(np.linspace(0,1,len(monthdays))[startfrom:])
        + list(np.linspace(0,1,len(monthdays))[:startfrom])
    )
    monthday2val = dict(zip(monthdays, colorvals))

    # ### Test it
    # step = 5
    # plt.close()
    # f,ax = plt.subplots(figsize=(12,3))
    # for x, monthday in enumerate(monthdays[::step]):
    #     color = cmap(monthday2val[monthday])
    #     ax.plot([x], [0], color=color, marker='o')
    #     ax.annotate(monthday, (x, 0.015), rotation=90, ha='center', va='center', color=color)
    # ax.set_title(startfrom)
    # plots.despine(ax)
    # plt.show()


    ### Plot it
    ncols = 3
    nrows = len(years) // ncols + bool(len(years) % ncols) + 1
    loadcoords = dict(zip(years, [(row+1,col) for row in range(nrows) for col in range(ncols)]))
    minrecoords = {
        'upv': (0, 1),
        'wind-ons': (0, 2)
    }
    title = {'upv':'Solar','wind-ons':'Wind'}

    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(2.9*ncols, 2*nrows),
        gridspec_kw={'hspace':0, 'wspace':0},
    )
    ### Min RE
    for tech, (row, col) in minrecoords.items():
        ax[row,col].set_title(f'Min {title[tech]}', va='top', y=0.95, fontsize=11)
        df = dfmap[sw.GSw_PRM_StressSeedMinRElevel].copy()
        dates = (
            dictin_seed[years[0]].loc[dictin_seed[years[0]].property==tech]
            .set_index('region')
        )
        df['date'] = dates.date
        df['monthday'] = dates.monthday
        df['val'] = df.monthday.map(monthday2val)
        df.plot(
            ax=ax[row,col], facecolor='none', edgecolor='k', lw=0.2, zorder=1e6,
        )
        df.plot(
            ax=ax[row,col], column='val', edgecolor='none', lw=0, cmap=cmap, alpha=alpha,
            vmin=0, vmax=1,
        )
        for i, _row in df.iterrows():
            ax[row,col].annotate(
                _row.date, (_row.centroid_x, _row.centroid_y),
                ha='center', va='center', color='k', fontsize=fontsize,
                path_effects=[pe.withStroke(linewidth=pelinewidth, foreground='w', alpha=pealpha)],
            )


    ### Max load
    for year in years:
        row, col = loadcoords[year]
        ax[row,col].set_title(f'Peak load {year}', va='top', y=0.95, fontsize=11)
        df = dfmap[sw.GSw_PRM_StressSeedLoadLevel].copy()
        dates = (
            dictin_seed[year].loc[dictin_seed[year].property=='load']
            .set_index('region')
        )
        ## Look up missing values
        lookup_days = pd.DataFrame(list(stressperiods_load[year])).set_index(0)
        lookup_days['szn'] = 'y' + lookup_days[2].astype(str) + 'd' + lookup_days[3].map(lambda x: f'{x:0>3}')
        lookup_days['timestamp'] = lookup_days.szn.map(reeds.timeseries.h2timestamp)
        lookup_days['date'] = lookup_days.timestamp.map(lambda x: x.strftime('%Y-%m-%d'))
        lookup_days['monthday'] = lookup_days.timestamp.map(lambda x: x.strftime('%m-%d'))

        df = df.merge(lookup_days[['date','monthday']], left_index=True, right_index=True)
        # df['date'] = dates.date
        # df['monthday'] = dates.monthday
        df['val'] = df.monthday.map(monthday2val)

        df.plot(
            ax=ax[row,col], facecolor='none', edgecolor='k', lw=0.2,
        )
        df.plot(
            ax=ax[row,col], column='val', edgecolor='none', lw=0, cmap=cmap, alpha=alpha,
            vmin=0, vmax=1,
        )
        for i, _row in df.iterrows():
            ax[row,col].annotate(
                _row.date, (_row.centroid_x, _row.centroid_y),
                ha='center', va='center', color='k', fontsize=fontsize,
                path_effects=[pe.withStroke(linewidth=pelinewidth, foreground='w', alpha=pealpha)],
            )

    ### Colorbar
    row, col = 0, 0
    for x, monthday in enumerate(monthdays):
        color = cmap(monthday2val[monthday])
        ax[row,col].plot([x], [0], color=color, marker='|', lw=0.1)
        if monthday.endswith('15'):
            ax[row,col].annotate(
                days_of_year[x].strftime('%b'),
                # monthday,
                (x, 0.008), rotation=90, ha='center', va='bottom', color=color)

    ### Formatting
    for row in range(nrows):
        for col in range(ncols):
            ax[row,col].axis('off')

    return f, ax


def plot_repdays(case, cmap=cmocean.cm.phase, alpha=0.7, startfrom=200):
    """Plot representative days in (12month)x(monthdays) format"""
    ### Setup
    months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ]
    ### Get color map
    days_of_year = pd.date_range('2004-01-01','2004-12-31',freq='D')
    monthdays = days_of_year.strftime('%m/%d')
    colorvals = (
        list(np.linspace(0,1,len(monthdays))[startfrom:])
        + list(np.linspace(0,1,len(monthdays))[:startfrom])
    )
    monthday2val = dict(zip(monthdays, colorvals))

    ### Data
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'), header=None, index_col=0
    ).squeeze(1)

    hmap_myr = pd.read_csv(
        os.path.join(case, 'inputs_case', 'rep', 'hmap_myr.csv'),
        index_col='*timestamp', parse_dates=True,
    )

    hmap_myr['timestamp_rep'] = hmap_myr.h.map(reeds.timeseries.h2timestamp)
    hmap_myr['repday'] = hmap_myr.season.map(reeds.timeseries.h2timestamp)

    actualday2repday = hmap_myr.drop_duplicates('yearperiod', keep='first').timestamp_rep
    repdaycounts = actualday2repday.value_counts()

    ### Plot it
    plt.close()
    f, ax = plt.subplots(12, 1, figsize=(12,6), sharex=True, sharey=True)
    ax[0].set_xlim(0,31)
    for row, month in enumerate(months):
        ## Formatting
        ax[row].set_ylabel(month, rotation=0, ha='right', va='center')
        for which in ['left', 'right', 'top', 'bottom']:
                    ax[row].spines[which].set_visible(False)
        ax[row].tick_params(left=False,right=False,top=False,bottom=False)
        ax[row].set_yticks([])
        ax[row].set_xticks([])
    ### Data
    for actualday, repday in actualday2repday.items():
        row = actualday.month - 1
        xstart = actualday.day - 1
        xend = xstart + (5 if sw.GSw_HourlyType == 'wek' else 1)
        monthday = repday.strftime('%m/%d')
        ## Background color
        ax[row].axvspan(xstart, xend, color=cmap(monthday2val[monthday]), alpha=alpha, lw=0)
        ## Date
        ax[row].annotate(
            repday.strftime('%-m/%-d' if os.name == 'posix' else '%#m/%#d'),
            (xstart+0.5, 0.5), ha='center', va='center', fontsize=8,
            path_effects=[pe.withStroke(linewidth=2.1, foreground='w', alpha=1)],
        )
        ## Box
        if (actualday.month == repday.month) and (actualday.day == repday.day):
            ax[row].axvspan(xstart, xend, facecolor='none', edgecolor='k', zorder=1e6, clip_on=False)
            ax[row].annotate(
                f'×{repdaycounts[repday]}', (xend-0.03, 0.05), ha='right', fontsize=7,
            )

    return f, ax, actualday2repday


def get_tech_colors_order(order='fuel_storage_vre'):
    ### Colors
    bokehcolors = pd.read_csv(
        os.path.join(
            reeds_path, 'postprocessing', 'bokehpivot', 'in', 'reeds2', 'tech_style.csv'),
        index_col='order').squeeze(1)
    bokehcolors = pd.concat([
        bokehcolors.loc['smr':'electrolyzer'],
        pd.Series('#D55E00', index=['dac'], name='color'),
        bokehcolors.loc[:'Canada'],
    ])
    bokehcolors['canada'] = bokehcolors['Canada']
    bokehcolors = bokehcolors.to_dict()

    for i in [f'battery_{d}' for d in [2,4,6,8,10]]+['battery_li','pumped-hydro']:
        for j in ['charge','discharge']:
            if i in bokehcolors:
                bokehcolors[f'{i}|{j}'] = bokehcolors[i]

    ### For this particular plot we put storage below VRE
    if order == 'fuel_storage_vre':
        plotorder = (
            list(bokehcolors.keys())[:list(bokehcolors.keys()).index('wind-ons')]
            + ['canada','Canada']
            + [
                k for k in bokehcolors.keys()
                if any([j in k for j in ['battery','pump','evmc']])
            ]
        )
        plotorder += [c for c in bokehcolors.keys() if c not in plotorder]
    else:
        plotorder = list(bokehcolors.keys())

    return bokehcolors, plotorder


def scale_outputs(df, scale='percent'):
    if scale == 'percent':
        out = df / df.clip(lower=0).sum() * 100
    else:
        out = df * scale
    return out


def separate_charge_discharge(df):
    """
    Renames entries in a technology (i) column to {original}|charge
    if generation (MW) is negative and {original}|discharge otherwise.
    Acts in-place on a dataframe.
    """
    assert 'i' in df, "df must have an `i` column"
    assert 'MW' in df, "df must have a `MW` column"
    storage_techs = [
        i for i in df.i.unique()
        if i.startswith('battery') or i.startswith('pumped-hydro')
    ]
    df.loc[
        df.i.isin(storage_techs) & (df.MW.round(3) < 0),
        'i'
    ] += '|charge'
    df.loc[df.i.isin(storage_techs), 'i'] += '|discharge'


def get_cap_rep_stress_mix(
    case,
    years=None,
    level='transreg',
    units='GW',
    metrics=[
        'cap',
        'rep_mean',
        'stress_mean',
        'stress_top5_load',
        'stress_top5_netload',
        'stress_bottom5_vregen',
        'stress_max_load',
        'stress_max_price',
    ],
    order='fuel_storage_vre',
):
    ### Check inputs
    allowed = (
        r'(cap|rep_mean|stress_(mean|(max|min|top\d+|bottom\d+)_(gen|load|netload|price|vregen)))'
    )
    for key in metrics:
        if not re.match(allowed, key):
            raise ValueError(f"{key} in metrics must match {allowed}")

    ### Parse inputs
    allyears = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')).columns.astype(int).tolist()
    if isinstance(years, (int, np.int64)):
        years = [years]
    elif years is None:
        years = allyears
    assert all([y in allyears for y in years]), f"years={years} but must be in {allyears}"
    if units.lower() in ['%', 'percent', 'fraction', 'share', 'mix']:
        scale = 'percent'
    else:
        scale = {'MW':1, 'GW':1e-3, 'TW':1e-6}[units.upper()]
    ## Replace 'max' with 'top1' since they're handled the same
    keys = [key.replace('max','top1').replace('min','bottom1') for key in metrics]

    ### Standard inputs
    bokehcolors, plotorder = get_tech_colors_order(order)
    numhours = pd.read_csv(
        os.path.join(case,'inputs_case', 'rep', 'numhours.csv'),
    ).rename(columns={'*h':'h'}).set_index('h').squeeze(1)

    dfmap = reeds.io.get_dfmap(case)
    hierarchy = reeds.io.get_hierarchy(case)

    techs_vre = simplify_techs(
        reeds.techs.expand_GAMS_tech_groups(
            reeds.techs.get_tech_subset_table(case).loc[['VRE']].reset_index()
        ).i
    ).unique()

    ## Sort regions west to east
    regions = dfmap[level].loc[hierarchy[level].unique()].bounds.minx.sort_values().index

    ## Aggregate
    if level == 'r':
        r2agg = pd.Series(index=hierarchy.index, data=hierarchy.index)
    else:
        r2agg = hierarchy[level].copy()

    ### Rep generation
    gen_h = reeds.io.read_output(case, 'gen_h', valname='MW')
    gen_h = gen_h.loc[gen_h.t.isin(years)].copy()
    gen_h.i = simplify_techs(gen_h.i)
    gen_h.r = gen_h.r.map(r2agg)
    gen_h = gen_h.groupby(['t','i','r','h'], as_index=False).MW.sum()
    separate_charge_discharge(gen_h)

    ### Stress generation
    gen_h_stress = reeds.io.read_output(case, 'gen_h_stress', valname='MW')
    gen_h_stress = gen_h_stress.loc[gen_h_stress.t.isin(years)].copy()
    gen_h_stress.i = simplify_techs(gen_h_stress.i)
    gen_h_stress.r = gen_h_stress.r.map(r2agg)
    gen_h_stress = gen_h_stress.groupby(['t','i','r','h'], as_index=False).MW.sum()
    separate_charge_discharge(gen_h_stress)

    ### Load hours
    load_stress = reeds.io.read_output(case, 'load_stress')
    load_stress = load_stress.loc[load_stress.t.isin(years)].copy()
    load_stress.r = load_stress.r.map(r2agg)
    load_stress = load_stress.groupby(['t','r','h']).Value.sum().unstack('r')

    ### Price hours
    reqt_price = reeds.io.read_output(case, 'reqt_price')
    price_stress = reqt_price.loc[
        (reqt_price['*'] == 'res_marg')
        & (reqt_price.t.isin(years))
    ].rename(columns={'*.2':'h'}).copy()
    price_stress.r = price_stress.r.map(r2agg)
    price_stress = price_stress.groupby(['t','r','h']).Value.max().unstack('r')

    ### VRE generation hours
    vregen_stress = (
        gen_h_stress.loc[gen_h_stress.i.isin(techs_vre)]
        .groupby(['t','r','h']).MW.sum().unstack('r')
    )

    ### Net load hours
    netload_stress = load_stress - vregen_stress

    ### Collect results
    dictout = {}
    for key in keys:
        ### Capacity by region
        if key == 'cap':
            df = reeds.io.read_output(case, 'cap')
            df = df.loc[df.t.isin(years)].copy()
            df.i = simplify_techs(df.i)
            df.r = df.r.map(r2agg)
            df = df.groupby(['t','i','r']).Value.sum().unstack('r').fillna(0)
            df = df.loc[
                ~df.index.get_level_values('i').isin(['electrolyzer','smr','smr-ccs','canada'])
            ].copy()

        ### Timeslice generation by region
        elif key == 'rep_mean':
            ## Average generation
            gen_h_energy = gen_h.copy()
            gen_h_energy['MWh'] = gen_h_energy['MW'] * gen_h_energy['h'].map(numhours)
            gen_h_energy = gen_h_energy.groupby(['t','i','r']).MWh.sum().unstack('r').fillna(0)
            ## Convert back to power
            df = gen_h_energy / numhours.sum()

        ## Stress period dispatch
        elif key.startswith('stress'):
            if key == 'stress_mean':
                df = (
                    ## Assuming stress periods are all weighted equally; if not, should
                    ## multiply by numhours
                    gen_h_stress.groupby(['t','i','r']).MW.sum()
                    .unstack('r').fillna(0)
                    .divide(gen_h_stress.groupby('t').h.unique().map(len), axis=0)
                )

            ## Generation during regional max hours
            elif key.startswith('stress'):
                direction = ('top' if 'top' in key else 'bottom')
                numslices = int(key.split(direction)[1].split('_')[0])
                if key.split('_')[-1] == 'load':
                    dfindex = load_stress.stack('r').reorder_levels(['t','r','h'])
                elif key.split('_')[-1] == 'gen':
                    dfindex = gen_h_stress.groupby(['t','r','h']).MW.sum()
                elif key.split('_')[-1] == 'price':
                    dfindex = price_stress.stack('r').reorder_levels(['t','r','h'])
                elif key.split('_')[-1] == 'vregen':
                    dfindex = vregen_stress.stack('r').reorder_levels(['t','r','h'])
                elif key.split('_')[-1] == 'netload':
                    dfindex = netload_stress.stack('r').reorder_levels(['t','r','h'])
                else:
                    raise KeyError(f'Invalid key: {key}')
                idhours = (
                    dfindex
                    .sort_values(ascending=(False if 'top' in key else True))
                    .groupby(['t','r']).head(numslices)
                    .reset_index()
                    .groupby(['t','r']).h.apply(list)
                )
                ## Get generation
                df = pd.concat(
                    {
                        (t,r):
                        gen_h_stress.loc[
                            (gen_h_stress.r==r)
                            & (gen_h_stress.t==t)
                            & (gen_h_stress.h.isin(idhours[t,r]))
                        ].groupby('i').MW.mean()
                        for r in regions for t in years
                    }, axis=1, names=('t','r')
                ).fillna(0).stack('t').reorder_levels(['t','i'])
                ## Also include average load and net load
                for loadkey, dfload in [
                    (f'load_{key}', load_stress),
                    (f'netload_{key}', netload_stress),
                ]:
                    dictout[loadkey] = (
                        dfload
                        .stack('r')
                        .reorder_levels(['t','r','h'])
                        .reindex(idhours.explode().reset_index().set_index(['t','r','h']).index)
                        .fillna(0)
                        .groupby(['t','r']).mean()
                        .unstack('r')
                    )

        dfwide = df.unstack('t').reorder_levels(['t','r'], axis=1)
        dfplot = dfwide.loc[[c for c in plotorder if c in dfwide.index]].copy()
        if len(dfplot) != len(dfwide):
            print('Before sorting by plotorder:\n', dfwide.columns)
            print('After sorting by plotorder:\n', dfplot.columns)
            err = f"{key}: {len(dfwide)} -> {len(dfplot)} after sorting by plotorder"
            raise ValueError(err)
        dictout[key] = scale_outputs(dfplot, scale)

    return dictout


def stress_mix_label(case, metric):
    sw = reeds.io.get_switches(case)
    if metric == 'cap':
        xlabel = 'Capacity'
    elif metric.startswith('rep'):
        xlabel = f"Rep {metric.split('_')[1]} gen"
    elif metric == 'stress_mean':
        xlabel = 'Stress mean gen'
    elif ('top' in metric) or ('bottom' in metric):
        direction = ('top' if 'top' in metric else 'bottom')
        xlabel = "Stress: {} {} {} hours".format(
            direction,
            int(metric.split(direction)[1].split('_')[0])
            * int(sw.GSw_HourlyChunkLengthStress),
            metric.split('_')[-1],
        )
    else:
        raise ValueError(f'Could not parse metric: {metric}')
    return xlabel


def stress_metrics_shorten(metrics):
    shortmetrics = (
        (','.join(metrics))
        .replace('rep', 'r')
        .replace('stress', 's')
        .replace('cap', 'c')
        .replace('netload', 'nl')
        .replace('load', 'l')
        .replace('price', 'p')
        .replace('vregen', 'vg')
    )
    return shortmetrics


def plot_cap_rep_stress_mix(
    case,
    year=2050,
    level='transreg',
    units='GW',
    metrics=[
        'cap',
        'rep_mean',
        'stress_mean',
        'stress_top5_load',
        'stress_top5_netload',
        'stress_bottom5_vregen',
        'stress_max_load',
        'stress_max_price',
    ],
    drawpeak=True,
    drawgrid=True,
):
    """
    Plot stacked tech bars for each region for the outputs specified by `metrics`:
    - 'cap': Nameplate capacity
    - '(rep|stress)_mean': Representative or stress period mean generation
    - 'stress_(max|min)_(gen|load|netload|vregen|price)': Stress period max/min
        generation, load, net load, VRE generation, or price
    - 'stress_(top|bottom){integer}_(gen|load|netload|vregen|price)': Stress period
        top/bottom {integer} (gen|load|netload|vregen|price) timeslices
        (number of hours is GSw_HourlyChunkLengthStress * {integer})

    Other arguments:
    - units: 'MW' or 'GW' or 'TW' for absolute, or '%' or 'percent' for relative

    Returns:
    tuple (f, ax, dictout). Keys of dictout are the provided metrics.
    """
    ### Parse inputs
    if units.lower() in ['%', 'percent', 'fraction', 'share', 'mix']:
        scale = 'percent'
        ylabel = 'Technology mix [%]'
        _drawpeak = False
    else:
        scale = {'MW':1, 'GW':1e-3, 'TW':1e-6}[units.upper()]
        ylabel = f'Capacity or generation [{units}]'
        _drawpeak = drawpeak

    dfmap = reeds.io.get_dfmap(case)
    hierarchy = reeds.io.get_hierarchy(case)
    bokehcolors, plotorder = get_tech_colors_order('fuel_storage_vre')
    ## Replace 'max' with 'top1' since they're handled the same
    keys = [key.replace('max','top1').replace('min','bottom1') for key in metrics]
    ## Sort regions west to east
    regions = dfmap[level].loc[hierarchy[level].unique()].bounds.minx.sort_values().index
    ncols = len(regions)
    ## x axis labels
    xlabels = {key: stress_mix_label(case, key) for key in keys}

    ### Peak load
    peakload = pd.read_csv(
        os.path.join(case,'inputs_case','peakload.csv'),
        index_col=['level','region'],
    ).loc[level][str(year)]
    if scale != 'percent':
        peakload *= scale

    ### Get results
    dictout = get_cap_rep_stress_mix(
        case=case,
        years=year,
        level=level,
        units=units,
        metrics=metrics,
    )
    dictout = {key: dictout[key][year] for key in keys}

    ###### Plot it
    ymin = min([
        df.loc[df.index.map(lambda x: '|charge' in x)].sum().min()
        for df in dictout.values()
    ])

    ymax = max([
        df.loc[~df.index.map(lambda x: '|charge' in x)].sum().max()
        for df in dictout.values()
    ])

    plt.close()
    f,ax = plt.subplots(
        2, ncols, sharex='row', sharey='row', figsize=(len(xlabels)*0.4*ncols, 6),
        gridspec_kw={'hspace':0.1, 'height_ratios':[0.2,1]},
    )
    for col, r in enumerate(regions):
        ### Shared formatting
        ax[1,col].set_xticks(range(len(xlabels)))
        ax[1,col].set_xticklabels(
            xlabels.values(), rotation=45, ha='right', rotation_mode='anchor')
        ax[1,col].axhline(0, c='k', ls=':', lw=0.75)

        ### Data
        no_more_grids = 0
        for x, (key, df) in enumerate(dictout.items()):
            plots.stackbar(
                df=df[r].rename(x).to_frame().T,
                ax=ax[1,col], colors=bokehcolors, net=False, width=0.8)
            if (key == 'cap') and drawgrid:
                ax[1,col].axvline(x+0.5, c='k', ls=':', lw=0.5)
            if (key.startswith('stress')) and drawgrid and not no_more_grids:
                ax[1,col].axvline(x-0.5, c='k', ls=':', lw=0.5)
                no_more_grids = 1

        ### Peak load
        if _drawpeak:
            try:
                ax[1,col].axhline(peakload[r], c='k', ls='--', lw=0.75)
            except KeyError as err:
                print(err)

        ### Maps at top
        dfmap[level].plot(ax=ax[0,col], facecolor='0.99', edgecolor='0.75', lw=0.2)
        dfmap[level].loc[[r]].plot(ax=ax[0,col], facecolor='k', edgecolor='none')
        ax[0,col].axis('off')
        ax[0,col].patch.set_facecolor('none')
        ax[1,col].set_title(r, weight='bold')

    ### Legend
    indices = [df.index.tolist() for df in dictout.values()]
    flat_indices = [i for sublist in indices for i in sublist]
    handles = [
        mpl.patches.Patch(facecolor=bokehcolors[i], edgecolor='none', label=i.split('|')[0])
        for i in plotorder if (
            (i in flat_indices)
            and (not (i.endswith('|charge') or i.endswith('|discharge')))
        )
    ]
    ax[1,-1].legend(
        handles=handles[::-1],
        loc='upper left', bbox_to_anchor=(1,1.03),
        ncol=1, labelspacing=0.1,
        handletextpad=0.3, handlelength=0.7,
        columnspacing=0.5, frameon=False,
    )
    ### Formatting
    ax[1,0].set_ylabel(ylabel)
    ax[1,0].set_ylim(ymin, ymax)
    ax[1,0].set_xlim(-0.5, len(xlabels)-0.5)
    ax[1,0].yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    plots.despine(ax)

    return f, ax, dictout


def plot_stress_mix(
    case,
    level='transreg',
    units='GW',
    metric='stress_max_price',
    drawload=False,
    startyear=2022,
    figwidth=1.5,
    figheight=6,
    order='fuel_storage_vre',
    moreticks=False,
):
    ### Parse inputs
    allowed = (
        r'(cap|rep_mean|stress_(mean|(max|min|top\d+|bottom\d+)_(gen|load|netload|price|vregen)))'
    )
    if not re.match(allowed, metric):
        raise ValueError(f"metric={metric} must match {allowed}")
    ## Replace 'max' with 'top1' since they're handled the same
    metric = metric.replace('max','top1').replace('min','bottom1')

    if units.lower() in ['%', 'percent', 'fraction', 'share', 'mix']:
        scale = 'percent'
        ylabel = 'Technology mix [%]'
        _drawload = False
    else:
        scale = {'MW':1, 'GW':1e-3, 'TW':1e-6}[units.upper()]
        ylabel = f'Generation [{units}]'
        _drawload = drawload
    ylabel = f"{stress_mix_label(case, metric)} [{'%' if scale == 'percent' else units}]"
    ### Get results
    dictout = get_cap_rep_stress_mix(
        case=case,
        level=level,
        units=units,
        metrics=[metric],
        order=order,
    )
    dfout = dictout[metric].copy()

    years = [y for y in dfout.columns.get_level_values('t').unique() if y >= startyear]
    yearstep = int(pd.Series(years).diff().max())

    loadmetric = f'netload_{metric}' if 'netload' in metric else f'load_{metric}'
    if loadmetric in dictout:
        dfload = dictout[loadmetric]
        dfload = dfload.loc[years].copy()
        if scale != 'percent':
            dfload *= scale
    else:
        _drawload = False

    ### Shared settings
    bokehcolors, plotorder = get_tech_colors_order('fuel_storage_vre')
    dfmap = reeds.io.get_dfmap(case)
    hierarchy = reeds.io.get_hierarchy(case)
    ## Plot settings
    regions = dfmap[level].loc[hierarchy[level].unique()].bounds.minx.sort_values().index
    ncols = len(regions)
    ymin = dfout[dfout < 0].sum().min()
    #%% Plot it
    plt.close()
    f,ax = plt.subplots(
        2, ncols, sharex='row', sharey='row', figsize=(ncols*figwidth, figheight),
        gridspec_kw={'hspace':0.1, 'height_ratios':[0.2,1]},
    )
    for col, r in enumerate(regions):
        _ax = ax[1,col] if ncols > 1 else ax[1]
        ### Data
        df = dfout.xs(r, 1, 'r')[years].T
        plots.stackbar(
            df=df,
            ax=_ax,
            colors=bokehcolors,
            net=False,
            width=yearstep*0.9,
        )
        ### Peak load
        if _drawload:
            _ax.plot(
                dfload.index,
                dfload[r].values,
                c='k', ls='--', lw=1.5
            )
        ### Formatting
        _ax.axhline(0, c='k', ls=':', lw=0.75)
        _ax.set_title(r, weight='bold')
        if col == 0:
            _ax.set_ylabel(ylabel)
        if moreticks:
            _ax.set_xlim(2020)
            _ax.set_xticks(years)
            _ax.set_xticklabels(years, rotation=45, rotation_mode='anchor', ha='right')
            _ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(5))
        ### Maps at top
        _max = ax[0,col] if ncols > 1 else ax[0]
        dfmap[level].plot(ax=_max, facecolor='0.99', edgecolor='0.75', lw=0.2)
        dfmap[level].loc[[r]].plot(ax=_max, facecolor='k', edgecolor='none')
        _max.axis('off')
        _max.patch.set_facecolor('none')
    ### Formatting
    _ax.set_ylim(ymin)
    plots.despine(ax)

    return f, ax, dfout


def plot_capacity_offline(
        case, year=2050, level='transgrp',
        capwidth='5D', tempcolor='C7', temp_front=True,
        drawgrid=True, plot_for=False,
    ):
    """Plot capacity offline and temperature for rep and stress periods"""
    ### Get temperatures
    temperatures = reeds.io.get_temperatures(case)

    ## Aggregate if necessary
    sw = reeds.io.get_switches(case)

    if sw['GSw_RegionResolution'] == 'aggreg':
        r2aggreg = pd.read_csv(
            os.path.join(case, 'inputs_case', 'hierarchy_original.csv')
        ).rename(columns={'ba':'r'}).set_index('r').aggreg
        temperatures = temperatures.rename(columns=r2aggreg)

    hierarchy = reeds.io.get_hierarchy(case)
    r2level = hierarchy[level]

    bokehcolors = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order',
    ).squeeze(1).drop(['electrolyzer','smr','smr-ccs','Canada'], errors='ignore')

    dftemp = pd.concat({
        which: (
            temperatures.rename(columns=hierarchy[level]).T.groupby(level='r').agg(which)
            .T.groupby([
                temperatures.index.year,
                temperatures.index.month,
                temperatures.index.day,
            ]).agg(which)
        )
        for which in ['min', 'max']
    }, axis=1)
    dftemp.index = pd.to_datetime(
        temperatures.index.strftime('%Y-%m-%d').drop_duplicates())
    ## Include all weather years so we don't interpolate the gap
    dftemp = dftemp.reindex(pd.date_range(dftemp.index[0], dftemp.index[-1], freq='D'))

    ### Get GW capacity offline, with same index as temperatures
    capacity_offline = reeds.io.read_output(case, 'capacity_offline')
    capacity_offline = (
        capacity_offline.assign(i=simplify_techs(capacity_offline.i))
        .loc[capacity_offline.t==year]
        .groupby(['i','r','h']).Value.sum().unstack(['r','i'])
        / 1e3
    )
    ## Aggregate
    capacity_offline.columns = capacity_offline.columns.map(
        lambda x: (r2level[x[0]], x[1]))
    capacity_offline = capacity_offline.T.groupby(['r','i']).sum().T
    ## Convert index to datetimes
    capacity_offline.index = capacity_offline.index.map(reeds.timeseries.h2timestamp)
    capacity_offline = capacity_offline.groupby([
        capacity_offline.index.year,
        capacity_offline.index.month,
        capacity_offline.index.day,
    ]).max()
    capacity_offline.index = capacity_offline.index.map(
        lambda x: pd.Timestamp(year=x[0], month=x[1], day=x[2]))

    ### Get outage rates
    if plot_for:
        outage_forced_hourly = (
            reeds.io.get_outage_hourly(case, 'forced')
            .reorder_levels(['r','i'], axis=1))
        outage_forced_hourly.columns = outage_forced_hourly.columns.map(
            lambda x: (r2level[x[0]], x[1])
        )
        ## Get max by region, convert to percent
        outage_forced_hourly = outage_forced_hourly.T.groupby(['r','i']).max().T
        for_techs = ['nuclear','coaloldscr','gas-cc','gas-ct','hydro']
        rename = {'coaloldscr':'coal'}
        for_techs_rename = [rename.get(i,i) for i in for_techs]
        outage_forced_hourly = (
            outage_forced_hourly[[c for c in outage_forced_hourly if c[1] in for_techs]]
            .rename(columns=rename, level='i')
            * 100
        )
        outage_forced_hourly = outage_forced_hourly.groupby([
            outage_forced_hourly.index.year,
            outage_forced_hourly.index.month,
            outage_forced_hourly.index.day,
        ]).max()
        outage_forced_hourly.index = outage_forced_hourly.index.map(
            lambda x: pd.Timestamp(year=x[0], month=x[1], day=x[2]))
    else:
        outage_forced_hourly = None

    dictout = {
        'temperature_minmax': dftemp,
        'capacity_offline': capacity_offline,
        'outage_forced_hourly': outage_forced_hourly,
    }

    ### Plot it
    regions = dftemp['min'].columns.tolist()
    nrows = len(regions)

    plt.close()
    f,ax = plt.subplots(nrows, 1, sharex=True, sharey=True, figsize=(12, 1.5*nrows))
    topax = ax if nrows == 1 else ax[0]
    botax = ax if nrows == 1 else ax[-1]
    pars = []
    for row, region in enumerate(regions):
        _ax = ax if nrows == 1 else ax[row]
        if drawgrid:
            _ax.grid(which='major', axis='y', c='k', lw=0.15, ls=(10, (10, 10)))
        _ax.annotate(
            region, (0.005, 1.05), xycoords='axes fraction', va='top',
            weight='bold', fontsize=12,
        )
        ## Temperatures
        _ax.fill_between(
            dftemp.index, dftemp['max'][region], dftemp['min'][region],
            label=region, color=tempcolor, alpha=0.8, lw=0, zorder=1e6,
        )
        ## Parasite y axis
        par = _ax.twinx()
        pars.append(par)
        par.spines['top'].set_visible(False)
        par.tick_params(which='both', direction='out')
        if temp_front:
            _ax.set_zorder(1)
            _ax.set_frame_on(False)
        ## Capacity offline
        df = capacity_offline[region][
            [c for c in bokehcolors.index if c in capacity_offline[region]]
        ].copy()
        if not plot_for:
            plots.stackbar(
                df=df, ax=par, colors=bokehcolors,
                width=pd.Timedelta(capwidth), x0=pd.Timedelta(0), net=False,
            )
        ## Forced outage rates
        else:
            dff = outage_forced_hourly[region][
                [c for c in outage_forced_hourly[region] if c in df]].copy()
            for col in dff:
                par.plot(
                    dff.index, dff[col].values, color=bokehcolors[col],
                    lw=1.0, alpha=0.9, label='_nolabel')

    ## Legend
    if not plot_for:
        par.set_ylabel('Capacity offline [GW]', y=0, ha='left')
        handles = [
            mpl.patches.Patch(facecolor=bokehcolors[i], edgecolor='none', label=i)
            for i in bokehcolors.index if i in capacity_offline.columns.get_level_values('i')
        ]
        botax.legend(
            handles=handles[::-1], loc='lower left', bbox_to_anchor=(1.07, -0.15),
            ncol=1, frameon=False,
            labelspacing=0.1, handletextpad=0.3, handlelength=0.7, columnspacing=0.5,
        )
    else:
        par.set_ylabel('Forced outage rate [%]', y=0, ha='left')
        handles = [
            mpl.patches.Patch(facecolor=bokehcolors[i], edgecolor='none', label=i)
            for i in for_techs_rename
        ]
        botax.legend(
            handles=handles[::-1], loc='lower left', bbox_to_anchor=(1.07, -0.15),
            ncol=1, frameon=False,
            labelspacing=0.1, handletextpad=0.3, handlelength=0.7, columnspacing=0.5,
        )
        ymax = max([par.get_ylim()[1] for par in pars])
        for row in range(nrows):
            pars[row].set_ylim(0,ymax)
            pars[row].yaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))

    ## Formatting
    topax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(20))
    topax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    botax.set_ylabel('Daily temperature range [°C]', y=0, ha='left', color=tempcolor)
    topax.set_xlim(
        pd.Timestamp(f'{sw.resource_adequacy_years_list[0]}-01-01'),
        pd.Timestamp(f'{sw.resource_adequacy_years_list[-1]}-12-31 23:00')
    )
    topax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(4))
    plots.despine(ax)

    return f, ax, dictout


def map_outage_days(
    case,
    dates=['2008-12-16', '2009-01-15'],
    techs=['gas-cc', 'gas-ct', 'coaloldscr', 'nuclear', 'hyded'],
    outage_type='forced',
    aggfunc='max',
    cmap=cmocean.cm.rain,
    vmin=0,
    vmax='auto',
    fontsize=4,
    scale=2,
):
    ### Outage rates
    if outage_type == 'both':
        outage_hourly = reeds.io.get_outage_hourly(case, 'forced').add(
            reeds.io.get_outage_hourly(case, 'scheduled'),
            fill_value=0,
        )
    else:
        outage_hourly = reeds.io.get_outage_hourly(case, outage_type)
    dtype = type(outage_hourly.columns)

    ### Region map
    dfba = reeds.io.get_dfmap(case)['r']
    outage_dates = (
        pd.concat(
            {date: outage_hourly.loc[date].agg(aggfunc, axis=0) for date in dates},
            axis=1, names=('date',)
        )
        .loc[techs]
        .unstack('i')
    ## Convert to percent
    ) * 100

    ### Plot setup
    if vmax in ['auto', 'max', 'data', 'scale']:
        vmax = (outage_dates.max().max() if dtype == pd.MultiIndex else outage_dates.max())
    nrows = len(techs)
    ncols = len(dates)
    coords = {
        (tech, date): (row, col)
        for col, date in enumerate(dates) for row, tech in enumerate(techs)
    }
    nicelabels = {
        'gas-cc': 'Gas CC',
        'gas-ct': 'Gas CT',
        'coaloldscr': 'Coal',
        'nuclear': 'Nuclear',
        'hyded': 'Hydro',
    }
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(ncols*scale, nrows*scale*0.8), sharex=True, sharey=True,
    )
    ## Data
    index = outage_dates.columns if dtype == pd.MultiIndex else outage_dates.index
    for date, tech in index:
        _ax = ax[coords[tech, date]]
        dfplot = dfba.copy()
        dfplot['outage_pct'] = outage_dates[date][tech]
        dfplot.plot(ax=_ax, column='outage_pct', cmap=cmap, vmin=vmin, vmax=vmax)
        ## Data values
        if fontsize:
            for r, row in dfplot.sort_values('outage_pct').iterrows():
                _ax.annotate(
                    f"{row.outage_pct:.0f}",
                    [row.centroid_x, row.centroid_y],
                    ha='center', va='center', c='k',
                    fontsize=fontsize,
                    path_effects=[pe.withStroke(linewidth=1.4, foreground='w', alpha=0.7)],
                )
        _ax.axis('off')
        ## Formatting
        if date == dates[0]:
            _ax.annotate(
                nicelabels.get(tech,tech), (0, 0.5), xycoords='axes fraction',
                ha='right', va='center', fontsize=14, weight='bold',
            )
        if tech == techs[0]:
            _ax.annotate(
                date, (0.5, 1.0), xycoords='axes fraction',
                ha='center', va='bottom', fontsize=14, weight='bold',
            )

    return f, ax, outage_dates


def get_cf_map(case, tech='wind-ons', timestamp=None, recf=None):
    """
    Map (r,class)-resolution CF

    Arguments
    ---------
    case (str): Path to a ReEDS case
    tech: 'wind-ons', 'upv', or 'wind-ofs'
    timestamp: If provided, report average CF over the timestamp; if None, report average
        CF over full weather range. Can be any time string parseable by pandas, for example:
        '2010', 'July 2011', '2012-10-31'
    recf: CF dataframe loaded from recf.h5. Optional, for speed; if not provided, will
        be read from {case}/inputs_case/recf.h5.

    Returns
    -------
    pd.DataFrame: Supply curve dataframe with a 'cf' column and 'sc_point_gid' index
    """
    scalars = reeds.io.get_scalars(case)
    if recf is None:
        ## Get CF
        recf = reeds.io.read_file(
            os.path.join(case, 'inputs_case', 'recf.h5'), parse_timestamps=True,
        )
    if not isinstance(recf.columns, pd.core.indexes.multi.MultiIndex):
        recf.columns = pd.MultiIndex.from_tuples(
            recf.columns.map(lambda x: tuple(x.split('|'))),
            names=['i','r'],
        )
    ## Downselect to time range and technology of interest
    if timestamp is None:
        cf = recf.mean()
    else:
        try:
            cf = recf.loc[timestamp].mean()
        except (ValueError, IndexError):
            cf = recf.loc[reeds.timeseries.h2timestamp(timestamp)].mean()
    cf = cf.loc[cf.index.get_level_values('i').str.startswith(tech)].copy()
    ## UPV is AC_out/DC_cap = CF_DC, so multiply by ILR to get CF_AC
    if tech == 'upv':
        cf *= scalars.ilr_utility

    ## Get mapping from sites to region/class
    dfsc = pd.read_csv(
        os.path.join(case, 'inputs_case', f'supplycurve_{tech}.csv'),
        index_col='sc_point_gid',
    ).rename(columns={'region':'r'})
    dfsc['i'] = tech + '_' + dfsc['class'].astype(str)
    sitemap = reeds.io.get_sitemap(offshore=(True if tech == 'wind-ofs' else False))
    dfsc['geometry'] = dfsc.index.map(sitemap.geometry)
    dfsc = gpd.GeoDataFrame(dfsc)
    dfsc['cf'] = dfsc[['i','r']].merge(cf.rename('cf'), on=['i','r'], how='left').cf.values

    ## Convert to polygons
    dfsc['geometry'] = dfsc.buffer(11530/2, cap_style='square')

    return dfsc


def label_region_value(df, ax, column, fmt='{:.2f}', color='k', fontsize=8, **kwargs):
    """kwargs are passed to patheffects.withStroke()"""
    pe_kwargs = {**{'linewidth':1.5, 'foreground':'w', 'alpha':1}, **kwargs}
    for r, row in df.iterrows():
        ax.annotate(
            fmt.format(row[column]),
            (row.geometry.centroid.x, row.geometry.centroid.y),
            ha='center', va='center', fontsize=fontsize,
            color=color,
            path_effects=[pe.withStroke(**pe_kwargs)],
            zorder=1e9,
        )


def map_stressors(case, t, iteration=0, seed=True, outage_type='forced', debug=False):
    """
    Map demand, wind/PV CF, and outage rate for stress periods.
    Returns an iterator over stress periods. Use as follows:
        ```python
        plot_generator = map_stressors()
        while True:
            try:
                f, ax, df, plotlabel = next(plot_generator)
                plt.savefig(plotlabel)
            except StopIteration:
                break
        ```

    Notes
    -----
    Maps: wind CF (daily mean), PV CF (daily mean), load (daily max),
    temperature (min or max).
    Show the percentage ranking of that day for that region out of whole weather sample.
    Could also include profiles for (that region, that + neighbors, or all regions?)
    for the day and the days before and after.
    Same for outage rates (not actual outages).
    """
    ### Plot setup
    cmaps = {
        'load': cmocean.cm.rain,
        # 'load': plt.cm.turbo,
        # 'wind-ons': cmocean.cm.ice_r,
        'wind-ons': cmocean.cm.ice,
        'upv': cmocean.cm.solar,
        'temperature': cmocean.cm.balance,
        'rank': plt.cm.turbo,
        'outage': cmocean.cm.amp,
    }
    labels = {
        'wind-ons':'Wind', 'upv':'PV',
        'forced':'Forced', 'scheduled':'Scheduled', 'both':'Total',
    }
    outage_techs = {
        'Combined cycle': 'gas-cc',
        'Combustion turbine': 'gas-ct',
        'Steam turbine': 'coal-new',
        'Nuclear': 'nuclear',
    }
    kwargs_colorbarhist = {
        'nbins': 41,
        'histratio': 1.25,
        'orientation': 'horizontal',
        'cbarhoffset': -1,
        'cbarheight': 0.35,
        'cbarwidth': 0.05,
        'cbarbottom': 0.05,
    }

    ### Shared inputs
    sw = reeds.io.get_switches(case)
    hierarchy = reeds.io.get_hierarchy(case)
    dfmap = reeds.io.get_dfmap(case)

    ### Derived inputs
    criterion = sw.GSw_PRM_StressThreshold.split('/')[0]
    level = criterion.split('_')[0]
    regions = hierarchy[level].unique()
    region2rs = {
        region: hierarchy.loc[hierarchy[level] == region].index
        for region in regions
    }
    dfba = dfmap['r'].copy()
    dflevel = dfmap[level].copy()

    ### Get the data
    augur_files = {
        'vre_gen': os.path.join(case, 'ReEDS_Augur', 'augur_data', f'pras_vre_gen_{t}.h5'),
        'load': os.path.join(case, 'ReEDS_Augur', 'augur_data', f'pras_load_{t}.h5'),
    }
    if any([not os.path.exists(fpath) for fpath in augur_files.values()]):
        import ReEDS_Augur.prep_data as prep_data
        prep_data.main(t, case, iteration)

    vre_gen = reeds.io.read_file(augur_files['vre_gen'], parse_timestamps=True)
    vre_gen.columns = pd.MultiIndex.from_tuples(
        vre_gen.columns.map(lambda x: tuple(x.split('|'))),
        names=['i','r'],
    )

    load = reeds.io.read_file(augur_files['load'], parse_timestamps=True)

    recf = reeds.io.read_file(
        os.path.join(case, 'inputs_case', 'recf.h5'),
        parse_timestamps=True,
    )
    recf.columns = pd.MultiIndex.from_tuples(
        recf.columns.map(lambda x: tuple(x.split('|'))),
        names=['i','r'],
    )

    temperatures = reeds.io.get_temperatures(case)
    ## Would be better to fix region aggregation upstream
    hierarchy_original = reeds.io.get_hierarchy(case, original=True)
    r2aggreg = hierarchy_original.aggreg
    temperatures = temperatures.rename(columns=r2aggreg).groupby('r', axis=1).mean()
    temperature_region = pd.concat({
        region: temperatures[region2rs[region]].mean(axis=1)
        for region in regions
    }, axis=1)
    temperature_region_day = {
        agg:
        temperature_region.groupby(
            [temperature_region.index.year, temperature_region.index.month, temperature_region.index.day]
        )
        .agg(agg)
        for agg in ['min', 'max', 'mean']
    }

    ### Daily generation
    load_region = {
        region:
        load[region2rs[region]].sum(axis=1)
        .groupby([load.index.year, load.index.month, load.index.day])
        .max()
        .sort_values()
        for region in regions
    }
    ranks = np.linspace(0,100,len(load_region[list(load_region.keys())[0]]))
    load_rank = pd.concat({
        region: pd.Series(index=load_region[region].index, data=ranks)
        for region in regions
    }, axis=1)

    vre_gen_region = {
        (tech, region):
        (
            vre_gen[tech][region2rs[region]].sum(axis=1)
            .groupby([vre_gen.index.year, vre_gen.index.month, vre_gen.index.day])
            .sum()
            .sort_values()
        )
        for tech in ['upv', 'wind-ons']
        for region in regions
    }
    vre_gen_rank = pd.concat({
        key: pd.Series(index=vre_gen_region[key].index, data=ranks)
        for key in vre_gen_region
    }, axis=1)

    temperature_rank = pd.concat({
        region: pd.Series(
            index=temperature_region_day['mean'].loc[load_region[region].index][region].sort_values().index,
            data=ranks,
        )
        for region in regions
    }, axis=1)

    ### Outage rates
    if outage_type == 'both':
        outage_hourly = reeds.io.get_outage_hourly(case, 'forced').add(
            reeds.io.get_outage_hourly(case, 'scheduled'),
            fill_value=0,
        )
    else:
        outage_hourly = reeds.io.get_outage_hourly(case, outage_type)
    ## Downselect to modeled techs and convert to percent
    outage_hourly = outage_hourly[list(outage_techs.values())].copy() * 100
    outage_daily = outage_hourly.groupby(
        [outage_hourly.index.year, outage_hourly.index.month, outage_hourly.index.day]
    ).mean()

    outage_region = outage_daily.copy()
    outage_region.columns = outage_daily.columns.map(lambda x: (x[0], hierarchy[level][x[1]]))
    outage_region = outage_region.groupby(['i','r'], axis=1).mean()

    ### Set up the plot
    nrows, ncols = 3, 4
    vmin = {
        'load': (pd.concat(load_region, axis=1).min() / pd.concat(load_region, axis=1).max()).min(),
        'wind-ons': 0,
        'upv': 0,
        'temperature': reeds.units.c2f(-20),
        'outage': 0,
    }
    vmax = {
        'load': 1,
        'wind-ons': 0.8,
        'upv': 0.5,
        'temperature': reeds.units.c2f(40),
        'outage': 40,
    }

    ### Get the days to run
    _plot_days = []
    if seed:
        forceperiods = (
            pd.read_csv(
                os.path.join(case, 'inputs_case', f'stress{t}i{iteration}', 'forceperiods.csv')
            )
            .drop(columns=['reason', 'yperiod'], errors='ignore')
            .rename(columns={'region':'r', 'year':'y', 'property':'reason'})
        )
        forceperiods['datetime'] = forceperiods.szn.map(reeds.timeseries.h2timestamp)
        # forceperiods['timestamp'] = forceperiods.datetime.dt.strftime('%Y-%m-%d')
        forceperiods['m'] = forceperiods.datetime.dt.month
        forceperiods['d'] = forceperiods.datetime.dt.day
        forceperiods['reason'] = 'seed_' + forceperiods['reason']
        _plot_days.append(forceperiods)
    ## If this iteration didn't meet the reliability threshold, include the added stress periods
    fpath_new_stress_periods = os.path.join(
        case, 'inputs_case', f'stress{t}i{iteration+1}', 'new_stress_periods.csv'
    )
    if os.path.exists(fpath_new_stress_periods):
        new_stress_periods = (
            pd.read_csv(fpath_new_stress_periods)
            .drop(columns=['Unnamed: 0', 'criterion'], errors='ignore')
            .rename(columns={'periodtype':'reason', 'actual_period':'szn'})
        )
        _plot_days.append(new_stress_periods)

    if not len(_plot_days):
        return None, None, None, None

    plot_days = (
        pd.concat(_plot_days, axis=0, ignore_index=True)
        .drop(columns=['datetime'], errors='ignore')
    )
    plot_days['timestamp'] = plot_days.apply(lambda row: f'{row.y}-{row.m:02}-{row.d:02}', axis=1)

    ### Loop over days
    for i, day in plot_days.iterrows():
        y, m, d = day.y, day.m, day.d
        timestamp = day.timestamp
        focus_region = day.r
        if 'EUE' in day.reason:
            highlight_level = level
            plotlabel = f'{timestamp}: {focus_region}, EUE = {day.EUE_MWh/1e3:.1f} GWh'
        elif ('before' in day.reason) or ('after' in day.reason):
            highlight_level = level
            plotlabel = f"{timestamp}: {focus_region}, shoulder ({day.reason.split('_')[0]})"
        elif day.reason == 'seed_load':
            highlight_level = sw.GSw_PRM_StressSeedLoadLevel
            plotlabel = f'{timestamp}: {focus_region}, peak load'
        elif day.reason.startswith('seed'):
            highlight_level = sw.GSw_PRM_StressSeedMinRElevel
            plotlabel = f"{timestamp}: {focus_region}, minumum {labels[day.reason.split('_')[1]]}"
        else:
            print(f'Invalid stress period: {day.reason}')
            continue

        ### Plot it
        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(13.33, 6.88), sharex=True, sharey=True,
        )
        ### First row: Daily load, PV CF, wind CF, temperature
        ## Load
        dfba['load'] = load.loc[timestamp].max() / load.max()
        dfba.plot(
            ax=ax[0,0], column='load',
            cmap=cmaps['load'], vmin=vmin['load'], vmax=vmax['load'],
        )
        ax[0,0].set_title('Demand [% of peak]', y=0.9)
        plots.addcolorbarhist(
            f, ax[0,0], dfba['load'],
            cmap=cmaps['load'], vmin=vmin['load'], vmax=vmax['load'],
            **kwargs_colorbarhist,
        )
        ## Wind, PV
        if not debug:
            for tech, col in [('wind-ons', 1), ('upv', 2)]:
                dfmap['country'].plot(ax=ax[0,col], facecolor='k', edgecolor='none', zorder=-1e3)
                dfsc = reeds.reedsplots.get_cf_map(
                    case, tech=tech, timestamp=timestamp, recf=recf,
                )
                dfsc.plot(
                    ax=ax[0,col], column='cf',
                    cmap=cmaps[tech], vmin=vmin[tech], vmax=vmax[tech],
                )
                ax[0,col].set_title(f'{labels.get(tech,tech)} CF [%]', y=0.9)
                plots.addcolorbarhist(
                    f, ax[0,col], dfsc['cf'],
                    cmap=cmaps[tech], vmin=vmin[tech], vmax=vmax[tech],
                    **kwargs_colorbarhist,
                )
        ## Temperature
        dfba['temperature'] = temperatures.loc[timestamp].mean().map(reeds.units.c2f)
        dfba.plot(
            ax=ax[0,3], column='temperature',
            cmap=cmaps['temperature'], vmin=vmin['temperature'], vmax=vmax['temperature'],
        )
        ax[0,3].set_title('Temperature [°F]', y=0.9)
        plots.addcolorbarhist(
            f, ax[0,3], dfba['temperature'],
            cmap=cmaps['temperature'], vmin=vmin['temperature'], vmax=vmax['temperature'],
            **kwargs_colorbarhist,
        )

        ### Second row: Load/PV/wind/temp percentile out of all weather years
        ## Load
        dflevel['load_rank'] = load_rank.loc[(y,m,d)]
        dflevel.plot(
            ax=ax[1,0], column='load_rank', cmap=cmaps['rank'], vmin=0, vmax=100,
        )
        label_region_value(
            df=dflevel, ax=ax[1,0], column='load_rank', fmt='{:.0f}%',
            linewidth=2.0, alpha=0.8,
        )
        ax[1,0].set_title('Demand', y=0.9)
        plots.addcolorbarhist(
            f, ax[1,0], dflevel['load_rank'],
            cmap=cmaps['rank'], vmin=0, vmax=100, **kwargs_colorbarhist,
        )
        ## Wind, PV
        for tech, col in [('wind-ons', 1), ('upv', 2)]:
            dflevel[f'{tech}_rank'] = vre_gen_rank[tech].loc[(y,m,d)]
            dflevel.plot(
                ax=ax[1,col], column=f'{tech}_rank', cmap=cmaps['rank'], vmin=0, vmax=100,
            )
            label_region_value(
                df=dflevel, ax=ax[1,col], column=f'{tech}_rank', fmt='{:.0f}%',
                linewidth=2.0, alpha=0.8,
            )
            ax[1,col].set_title(labels.get(tech,tech), y=0.9)
            plots.addcolorbarhist(
                f, ax[1,col], dflevel[f'{tech}_rank'],
                cmap=cmaps['rank'], vmin=0, vmax=100, **kwargs_colorbarhist,
            )
        ## Temperature
        dflevel['temperature_rank'] = temperature_rank.loc[(y,m,d)]
        dflevel.plot(
            ax=ax[1,3], column='temperature_rank', cmap=cmaps['rank'], vmin=0, vmax=100,
        )
        label_region_value(
            df=dflevel, ax=ax[1,3], column='temperature_rank', fmt='{:.0f}%',
            linewidth=2.0, alpha=0.8,
        )
        ax[1,3].set_title('Temperature', y=0.9)
        plots.addcolorbarhist(
            f, ax[1,3], dflevel['temperature_rank'],
            cmap=cmaps['rank'], vmin=0, vmax=100, **kwargs_colorbarhist,
        )

        ### Third row: CC/CT/ST/NU outage rate
        for col, (label, tech) in enumerate(outage_techs.items()):
            dfba[f'outage_{tech}'] = outage_daily.loc[(y,m,d), tech]
            dfba.plot(
                ax=ax[2,col], column=f'outage_{tech}',
                cmap=cmaps['outage'], vmin=vmin['outage'], vmax=vmax['outage'],
            )
            dflevel[f'outage_{tech}'] = outage_region.loc[(y,m,d), tech]
            label_region_value(
                df=dflevel, ax=ax[2,col], column=f'outage_{tech}', fmt='{:.0f}%',
                linewidth=2.0, alpha=0.8,
            )
            ax[2,col].set_title(label, y=0.9)
            plots.addcolorbarhist(
                f, ax[2,col], dfba[f'outage_{tech}'],
                cmap=cmaps['outage'], vmin=vmin['outage'], vmax=vmax['outage'],
                **kwargs_colorbarhist,
            )

        ### Formatting
        ax[0,0].annotate(
            plotlabel,
            (0.05, 1.1), xycoords='axes fraction',
            fontsize='xx-large', annotation_clip=False,
        )
        ax[1,0].annotate(
            f'{sw.num_resource_adequacy_years}-year\npercentile',
            (-0.06, 0.5), xycoords='axes fraction',
            rotation=90, va='center', ha='center',
            fontsize='x-large', weight='bold',
        )
        ax[2,0].annotate(
            f'{labels.get(outage_type,outage_type)}\noutage rate',
            (-0.06, 0.5), xycoords='axes fraction',
            rotation=90, va='center', ha='center',
            fontsize='x-large', weight='bold',
        )
        for row in range(nrows):
            for col in range(ncols):
                ax[row,col].axis('off')
                dflevel.plot(ax=ax[row,col], facecolor='none', edgecolor='k', lw=0.25, zorder=1e7)
                ## Highlight the focus region
                for i, (c, lw) in enumerate([('w', 2.0), ('k', 1.0)]):
                    dfmap[highlight_level].loc[[focus_region]].plot(
                        ax=ax[row,col], facecolor='none', edgecolor=c, lw=lw, zorder=(1e7+i),
                    )
        ## Keep the data for debugging
        dfout = {'dfba':dfba, 'dflevel':dflevel}
        yield f, ax, dfout, plotlabel


def layout_subplots(row_list, col_list, oneaxis='columns'):
    """
    Lay out series of row_list (e.g. cases) and col_list (e.g. years) into array of subplots,
    even if one of the lists has only one element.

    Returns:
        tuple: (nrows, ncols, coords) [int, int, dict]
        - coords: {(row_label, col_label): (row, col)}
          or {(row_label, col_label): row} or {(row_label, col_label): col} if one axis
    """
    numcols = len(col_list)
    numrows = len(row_list)
    if (len(row_list) == 1) or (numcols == 1):
        if oneaxis in ['column', 'columns', 1, 'wide']:
            nrows, ncols = 1, max(numrows, numcols)
        else:
            nrows, ncols = max(numrows, numcols), 1
    else:
        nrows, ncols = numrows, numcols
    nrows, ncols, coords = reeds.plots.get_coordinates(
        [(r, c) for r in row_list for c in col_list],
        nrows=nrows, ncols=ncols,
    )
    return nrows, ncols, coords


def map_output_byyear(
    case,
    param,
    years=[2050],
    oneaxis='columns',
    yearaxis='rows',
    mapscale=4,
    cmap=cmocean.cm.rain,
    vscale=1,
    vmin=None,
    vmax=None,
    **kwargs,
):
    ### Parse inputs
    if isinstance(case, dict):
        plotcases = list(case.values())
        titles = list(case.keys())
    else:
        if isinstance(case, str):
            plotcases = [case]
        elif isinstance(case, list):
            plotcases = case
        titles = [os.path.basename(c) for c in plotcases]

    ### Get results
    dfmap = reeds.io.get_dfmap(plotcases[0])
    dictin = {
        title: reeds.io.read_output(case, param).astype({'t':int})
        for title, case in zip(titles, plotcases)
    }
    ## Filter to plot years and reshape to [r × t]
    dictplot = {
        k: v.loc[v.t.isin(years)].pivot(index='r', columns='t', values='Value') * vscale
        for k,v in dictin.items()
    }
    ## Get limits
    dfall = pd.concat(dictplot)
    _vmin = float(dfall.min().min() if vmin is None else vmin)
    _vmax = float(dfall.max().max() if vmax is None else vmax)
    ## Arrange subplots
    nrows, ncols, coords = layout_subplots(
        row_list=titles,
        col_list=years,
        oneaxis=oneaxis,
    )
    ## Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(ncols*mapscale, nrows*mapscale*0.8), sharex=True, sharey=True,
        gridspec_kw={'hspace':0, 'wspace':0},
    )
    for title, case in zip(titles, plotcases):
        for year in years:
            _ax = (ax if len(coords) == 1 else ax[coords[title, year]])
            ## Background
            dfmap['country'].plot(ax=_ax, facecolor='none', edgecolor='k', lw=0.5, zorder=1e9)
            dfmap['r'].plot(ax=_ax, facecolor='none', edgecolor='C7', lw=0.2, zorder=1e8)
            ## Data
            dfplot = dfmap['r'].copy()
            dfplot['value'] = dictplot[title][year]
            # dfplot['value'] = dfplot['value'].fillna(0)
            dfplot.plot(
                ax=_ax, column='value', cmap=cmap,
                vmin=_vmin, vmax=_vmax,
            )
            _ax.axis('off')
            ## Formatting
            _ax.set_title(f'{title} {year}', y=0.95)
            ## Colorbar
            plots.addcolorbarhist(
                f=f, ax0=_ax, data=dictplot[title][year].values,
                vmin=_vmin, vmax=_vmax, cmap=cmap, nbins=21,
                orientation='horizontal',
                cbarheight=0.35, cbarhoffset=-0.8, cbarbottom=0.07, labelpad=3.5,
                **kwargs,
            )
    return f, ax, dictplot
