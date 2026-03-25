#%% Imports
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from glob import glob
import os, sys, math, site

import geopandas as gpd
import shapely
os.environ['PROJ_NETWORK'] = 'OFF'
import pptx, io
from pptx.util import Inches

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
remotepath = '/Volumes/ReEDS/' if sys.platform == 'darwin' else r'//nrelnas01/ReEDS/'

### Format plots and load other convenience functions
site.addsitedir(os.path.join(reeds_path,'postprocessing'))
import plots
import reedsplots
plots.plotparams()


#%% User inputs
plotvals = [
    'Generation (TWh)',
    'Capacity (GW)',
    'New Annual Capacity (GW)',
    'Annual Retirements (GW)',
    'Final Gen by timeslice (GW)',
    'Firm Capacity (GW)',
    'Curtailment Rate',
    'Transmission (GW-mi)',
    'Transmission (PRM) (GW-mi)',
    'Bulk System Electricity Pric',
    'National Average Electricity',
    'Present Value of System Cost',
    'NEUE (ppm)',
    'Runtime (hours)',
    'Runtime by year (hours)',
]
onlytechs = None
yearmin = 2020
yearmax = 2050
i_plots = ['wind-ons','upv','battery','h2-ct','nuclear','gas-cc-ccs','coal-ccs',]
## mapdiff: 'cap' or 'gen_ann'
mapdiff = 'cap'
interactive = False


#%% Argument inputs
import argparse
parser = argparse.ArgumentParser(description='run ReEDS2PRAS')
parser.add_argument('casebase', type=str,
                    help='path to ReEDS run folder for base case')
parser.add_argument('casecomp', type=str,
                    help='path to ReEDS run folder for comparison case')
parser.add_argument('--year', '-y', type=int, default=0,
                    help='year to run')
parser.add_argument('--titleshorten', '-s', type=int, default=0,
                    help='characters to cut from start of case name')

args = parser.parse_args()
casebase = args.casebase
casecomp = args.casecomp
year = args.year
titleshorten = args.titleshorten

# #%% Inputs for testing
# casebase = os.path.join(reeds_path,'runs','v20230509_onelineM0_NEIAIL_No')
# casecomp = os.path.join(reeds_path,'runs','v20230509_onelineM0_NEIAIL_No_p39p80')
# casebase = (
#     '/Volumes/ReEDS/FY22-NTP/Candidates/Archive/ReEDSruns/'
#     '20230418/v20230418_prasH0_Xlim_DemHi_90by2035EP__core'
# )
# casecomp = (
#     '/Volumes/ReEDS/FY22-NTP/Candidates/Archive/ReEDSruns/'
#     '20230418/v20230418_prasH0_AC_DemHi_90by2035EP__core'
# )
# year = 0
# interactive = True

#%%### Procedure

#%% Set up powerpoint file and default figure-adding approach
prs = pptx.Presentation(os.path.join(reeds_path,'postprocessing','template.pptx'))
blank_slide_layout = prs.slide_layouts[3]

def add_to_pptx(title, left=0, top=0.62, width=13.33, height=None):
    ## Add current matplotlib figure to new powerpoint slide
    image = io.BytesIO()
    plt.savefig(image, format='png')
    slide = prs.slides.add_slide(blank_slide_layout)
    slide.shapes.title.text = title
    slide.shapes.add_picture(
        image,
        left=(None if left == None else Inches(left)),
        top=(None if top == None else Inches(top)),
        width=(None if width == None else Inches(width)),
        height=(None if height == None else Inches(height)),
    )
    return slide

#%% Get the switches, overwriting values as necessary
sw = pd.read_csv(
    os.path.join(casebase, 'inputs_case', 'switches.csv'),
    header=None, index_col=0, squeeze=True)
sw['reeds_path'] = reeds_path

### Get the solve years
years = pd.read_csv(
    os.path.join(casebase, 'inputs_case', 'modeledyears.csv')
).columns.astype(int).tolist()

### Parse the year input
t = year if (year in years) else years[-1]
sw['t'] = t

#%%### Make the annual difference bar plots
print('base:', casebase)
print('comp:', casecomp)
for val in plotvals:
    try:
        plt.close()
        f, ax, leg, dfdiff, printstring = reedsplots.plotdiff(
            val, casebase, casecomp, onlytechs=None, titleshorten=titleshorten,
            yearmin=yearmin, yearmax=yearmax,
            # plot_kwds={'figsize':(4,4), 'gridspec_kw':{'wspace':0.7}},
        )
        slide = add_to_pptx(val)
        textbox = slide.shapes.add_textbox(
            left=Inches(0), top=Inches(7),
            width=Inches(13.33), height=Inches(0.5))
        textbox.text_frame.text = printstring
        if interactive: plt.show()
    except Exception as err:
        print(err)


#%%### Transmission diff map
try:
    plt.close()
    f,ax = reedsplots.plot_trans_diff(
        casebase=casebase, casecomp=casecomp,
        pcalabel=False,
        wscale=0.0004,
        subtract_baseyear=2020,
        yearlabel=True,
        year=t,
        alpha=1, dpi=150,
        titleshorten=titleshorten,
    )
    # ax[0].set_xlim(-2.5e6,0.4e6)
    add_to_pptx(f'Transmission ({t})')
    if interactive: plt.show()
except Exception as err:
    print(err)


#%%### Capacity diff maps
try:
    ### Get the BA map
    dfba = reedsplots.get_zonemap(casebase)
    endpoints = (
        gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','transmission_endpoints'))
        .set_index('ba_str'))
    try:
        aggreg2anchorreg = pd.read_csv(
            os.path.join(casebase,'inputs_case','aggreg2anchorreg.csv'),
            index_col='aggreg'
        ).squeeze(1)
    except FileNotFoundError:
        aggreg2anchorreg = dict(zip(endpoints.index, endpoints.index))
    endpoints['x'] = endpoints.centroid.x
    endpoints['y'] = endpoints.centroid.y
    dfba['labelx'] = dfba.geometry.centroid.x
    dfba['labely'] = dfba.geometry.centroid.y
    dfba['x'] = dfba.index.map(aggreg2anchorreg).map(endpoints.x)
    dfba['y'] = dfba.index.map(aggreg2anchorreg).map(endpoints.y)
    dfba.st = dfba.st.str.upper()

    ### Aggregate to states
    dfstates = dfba.dissolve('st')

    ### Plot it
    for i_plot in i_plots:
        plt.close()
        f,ax=plt.subplots(
            1,3,sharex=True,sharey=True,figsize=(14,8),
            gridspec_kw={'wspace':-0.05, 'hspace':0.05},
            dpi=150,
        )

        _,_,dfplot = reedsplots.plotdiffmaps(
            val=mapdiff, i_plot=i_plot, year=t, casebase=casebase, casecomp=casecomp,
            reeds_path=reeds_path, plot='base', f=f, ax=ax[0], dfba=dfba, dfstates=dfstates,
            cmap=plt.cm.gist_earth_r,
        )
        ax[0].annotate(
            os.path.basename(casebase)[titleshorten:],
            (0.1,1), xycoords='axes fraction', fontsize=10)

        _,_,dfplot = reedsplots.plotdiffmaps(
            val=mapdiff, i_plot=i_plot, year=t, casebase=casebase, casecomp=casecomp,
            reeds_path=reeds_path, plot='comp', f=f, ax=ax[1], dfba=dfba, dfstates=dfstates,
            cmap=plt.cm.gist_earth_r,
        )
        ax[1].annotate(
            os.path.basename(casecomp)[titleshorten:],
            (0.1,1), xycoords='axes fraction', fontsize=10)

        _,_,dfplot = reedsplots.plotdiffmaps(
            val=mapdiff, i_plot=i_plot, year=t, casebase=casebase, casecomp=casecomp,
            reeds_path=reeds_path, plot='absdiff', f=f, ax=ax[2], dfba=dfba, dfstates=dfstates,
            cmap=plt.cm.bwr,
        )
        # print(dfplot.CAP_diff.min(), dfplot.CAP_diff.max())
        ax[2].annotate(
            '{}\n– {}'.format(
                os.path.basename(casecomp)[titleshorten:],
                os.path.basename(casebase)[titleshorten:]), 
            (0.1,1), xycoords='axes fraction', fontsize=10)

        add_to_pptx(f'Capacity ({t})')
        if interactive: plt.show()
except Exception as err:
    print(err)

#%% Save the powerpoint file
savename = os.path.join(
    casecomp, 'outputs', 'maps', f"diff-{os.path.basename(casebase)}.pptx"
)
prs.save(savename)
print(savename)
