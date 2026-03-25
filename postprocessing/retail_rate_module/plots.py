"""
Some useful snippets
--------------------
### Legend: boxes instead of lines
leg = ax[-1].legend(columnspacing=0.5, handletextpad=0.5, handlelength=0.8)
for legobj in leg.legendHandles:
    legobj.set_linewidth(8)
    legobj.set_solid_capstyle('butt')
leg.set_title('title', prop={'size':'large'})

### Legend: reverse order
handles, labels = ax.get_legend_handles_labels()
leg = ax.legend(handles=handles[::-1], labels=labels[::-1])

"""
import pandas as pd
import numpy as np
import os
import matplotlib as mpl
import matplotlib.pyplot as plt

###################
### Plot formatting

def plotparams():
    """
    Format plots
    """
    plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['mathtext.rm'] = 'Arial'
    plt.rcParams['mathtext.it'] = 'Arial:italic'
    plt.rcParams['mathtext.bf'] = 'Arial:bold'
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['axes.labelsize'] = 'x-large'
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    plt.rcParams['xtick.labelsize'] = 'large'
    plt.rcParams['ytick.labelsize'] = 'large'
    plt.rcParams['xtick.top'] = True
    plt.rcParams['ytick.right'] = True
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['savefig.bbox'] = 'tight'
    # plt.rcParams['figure.figsize'] = 6.4, 4.8 # 1.33, matplotlib default
    # plt.rcParams['figure.figsize'] = 5.0, 4.0 # 1.25
    plt.rcParams['figure.figsize'] = 5.0, 3.75 # 1.33
    plt.rcParams['xtick.major.size'] = 4 # default 3.5
    plt.rcParams['ytick.major.size'] = 4 # default 3.5
    plt.rcParams['xtick.minor.size'] = 2.5 # default 2
    plt.rcParams['ytick.minor.size'] = 2.5 # default 2


### Percentages to hex values
percent2hex = {
    100: 'FF', 95: 'F2', 90: 'E6', 85: 'D9', 80: 'CC', 75: 'BF', 70: 'B3',
    65:  'A6', 60: '99', 55: '8C', 50: '80', 45: '73', 40: '66', 35: '59',
    30:  '4D', 25: '40', 20: '33', 15: '26', 10: '1A',  5: '0D',  0: '00',
}

#################
### FUNCTIONS ###
def _despine_sub(ax, 
    top=False, right=False, left=True, bottom=True,
    direction='out'):
    """
    Despine subplot
    """
    if not top: ax.spines['top'].set_visible(False)
    if not right: ax.spines['right'].set_visible(False)
    if not left: ax.spines['left'].set_visible(False)
    if not bottom: ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='both', which='both',
                   direction=direction, 
                   top=top, right=right, 
                   left=left, bottom=bottom)


def despine(ax=None, 
    top=False, right=False, left=True, bottom=True,
    direction='out'):
    """
    Despine all subplots
    """
    if ax is None:
        ax = plt.gca()
    if type(ax) is np.ndarray:
        for sub in ax:
            if type(sub) is np.ndarray:
                for subsub in sub:
                    _despine_sub(subsub, top, right, left, bottom, direction)
            else:
                _despine_sub(sub, top, right, left, bottom, direction)
    else:
        _despine_sub(ax, top, right, left, bottom, direction)
