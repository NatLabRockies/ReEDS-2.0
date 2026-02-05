"""
Some useful snippets
--------------------
### Legends - boxes instead of lines
leg = ax[-1].legend(
    ncol=1, columnspacing=0.5, frameon=False,
    handletextpad=0.5, handlelength=0.8,
    loc='upper left', bbox_to_anchor=(1.02,1),
)
for legobj in leg.legendHandles:
    legobj.set_linewidth(8)
    legobj.set_solid_capstyle('butt')
leg.set_title('title', prop={'size':'large'})

### Legends - two legends

### Legend - reverse order
handles, labels = ax.get_legend_handles_labels()
leg = ax.legend(
    handles=handles[::-1], labels=labels[::-1],
    ncol=1, columnspacing=0.5, frameon=False,
    # handletextpad=0.5, handlelength=0.8,
    handletextpad=0.3, handlelength=0.7,
    loc='center left', bbox_to_anchor=(1.02, 0.4),
)

"""
import pandas as pd
import numpy as np
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import cmocean

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


def get_latlonlabels(df, lat=None, lon=None, columns=None):
    """Try to find latitude and longitude column names in a dataframe"""
    ### Specify candidate column names to look for
    lat_candidates = ['latitude', 'lat']
    lon_candidates = ['longitude', 'lon', 'long']
    if columns is None:
        columns = df.columns

    latlabel = None
    lonlabel = None

    if lat is not None:
        latlabel = lat
    else:
        for col in columns:
            if col.lower().strip() in lat_candidates:
                latlabel = col
                break

    if lon is not None:
        lonlabel = lon
    else:
        for col in columns:
            if col.lower().strip() in lon_candidates:
                lonlabel = col
                break

    return latlabel, lonlabel


def df2gdf(dfin, crs='ESRI:102008', lat=None, lon=None):
    """Convert a pandas dataframe with lat/lon columns to a geopandas dataframe of points"""
    ### Imports
    import os
    import geopandas as gpd
    import shapely
    os.environ['PROJ_NETWORK'] = 'OFF'

    ### Convert
    df = dfin.copy()
    latlabel, lonlabel = get_latlonlabels(df, lat=lat, lon=lon)
    df['geometry'] = df.apply(
        lambda row: shapely.geometry.Point(row[lonlabel], row[latlabel]), axis=1)
    df = gpd.GeoDataFrame(df, crs='EPSG:4326').to_crs(crs)

    return df


### Sequential color dict
def rainbowmapper(iterable, colormap=None, explicitcolors=False, categorical=False):
    categoricalrainbow = [
        plt.cm.tab20(i) for i in [10,11,6,7,2,3,12,13,16,17,4,5,18,19,0,1,8,9,14,15,]
    ]
    if colormap is not None:
        if isinstance(colormap, list):
            colors=[colormap[i] for i in range(len(iterable))]
        else:
            colors=[colormap(i) for i in np.linspace(0,1,len(iterable))]
    elif len(iterable) == 1:
        colors=['C3']
    elif len(iterable) == 2:
        colors=['C3','C0']
    elif len(iterable) == 3:
        colors=['C3','C2','C0']
    elif len(iterable) == 4:
        colors=['C3','C1','C2','C0']
    elif len(iterable) == 5:
        colors=['C3','C1','C2','C0','C4']
    elif len(iterable) == 6:
        colors=['C5','C3','C1','C2','C0','C4']
    elif len(iterable) == 7:
        colors=['C5','C3','C1','C8','C2','C0','C4']
    elif len(iterable) == 8:
        colors=['C5','C3','C1','C8','C2','C0','C4','k']
    elif len(iterable) == 9:
        colors=['C5','C3','C1','C8','C2','C9','C0','C4','k']
    elif len(iterable) == 10:
        colors=['C5','C3','C1','C6','C8','C2','C9','C0','C4','k']
    elif len(iterable) <= 20:
        colors = categoricalrainbow[:len(iterable)]
    elif categorical:
        colors = categoricalrainbow * (len(iterable)//20 + 1)
    else:
        colors=[plt.cm.rainbow(i) for i in np.linspace(0,1,len(iterable))]
    out = dict(zip(iterable, colors))
    if explicitcolors:
        explicit = {
            'C0': '#1f77b4', 'C1': '#ff7f0e', 'C2': '#2ca02c', 'C3': '#d62728',
            'C4': '#9467bd', 'C5': '#8c564b', 'C6': '#e377c2', 'C7': '#7f7f7f',
            'C8': '#bcbd22', 'C9': '#17becf',
        }
        if len(iterable) <= 10:
            out = {c: explicit[out[c]] for c in iterable}
    return out

############
### Plotting

def addcolorbarhist(
    f, ax0, data,
    title=None,
    cmap=plt.cm.viridis,
    bins=None,
    nbins=201,
    vmin='default',
    vmax='default',
    cbarleft=1.05,
    cbarwidth=0.025,
    cbarheight=0.5,
    cbarbottom=None,
    cbarhoffset=0,
    histpad=0.005,
    histratio=3,
    labelpad=0.03,
    title_fontsize='large',
    title_alignment=None,
    title_weight='bold',
    ticklabel_fontsize='medium',
    log=False,
    histcolor='0.5',
    extend='neither',
    extendfrac=(0.05,0.05),
    orientation='vertical'):
    """
    Notes
    -----
    * All dimensions are in fraction of major axis size
    * cmap must a colormap object (e.g. plt.cm.viridis)
    * data should be of type np.array
    """

    ########################
    ### Imports and warnings
    import matplotlib as mpl
    ### Warnings
    #############
    ### Procedure

    ### Get bounds and make bins
    if vmin == 'default':
        vmin = data.min()
    if vmax == 'default':
        vmax = data.max()

    if bins is None:
        bins = np.linspace(vmin, vmax, nbins)
    elif type(bins) is np.ndarray:
        pass
    else:
        print(type(bins), bins)
        print(type(nbins, nbins))
        raise Exception('Specify bins as np.ndarray or nbins as int')
    ax0x0, ax0y0, ax0width, ax0height = ax0.get_position().bounds

    ### Defaults for colorbar position
    if (cbarbottom is None) and (orientation == 'horizontal'):
        cbarbottom = 1.05
    elif (cbarbottom is None) and (orientation == 'vertical'):
        cbarbottom = (1 - cbarheight) / 2

    ### If extending the colorbar, clip the ends of the data distribution so
    ### the extended values show up in the histogram
    if extend == 'neither':
        data_hist = data
    elif extend == 'max':
        data_hist = data.clip(upper=vmax)
    elif extend == 'min':
        data_hist = data.clip(lower=vmin)
    elif extend == 'both':
        data_hist = data.clip(lower=vmin, upper=vmax)

    ######### Add colorbar
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    ### Horizontal orientation
    if orientation in ['horizontal', 'h']:
        caxleft = ax0x0 + ax0width * (1 - cbarheight) / 2 * (1 + cbarhoffset)
        caxbottom = ax0y0 + ax0height * cbarbottom
        caxwidth = cbarheight * ax0width
        caxheight = cbarwidth * ax0height

        cax = f.add_axes([caxleft, caxbottom, caxwidth, caxheight])

        cbar = mpl.colorbar.ColorbarBase(
            cax, cmap=cmap, norm=norm, orientation='horizontal',
            extend=extend, extendfrac=extendfrac)
        cax.xaxis.set_ticks_position('bottom')

        ##### Add histogram, adjusting for extension length if necessary
        haxleft = caxleft + (
            (extendfrac[0] * caxwidth) if extend in ['min','both']
            else 0
        )
        haxbottom = caxbottom + (cbarwidth + histpad) * ax0height
        if extend == 'neither':
            haxwidth = caxwidth
        elif extend == 'max':
            haxwidth = caxwidth - extendfrac[1] * caxwidth
        elif extend == 'min':
            haxwidth = caxwidth - extendfrac[0] * caxwidth
        elif extend == 'both':
            haxwidth = caxwidth - sum(extendfrac) * caxwidth
        haxheight = histratio * cbarwidth * ax0height

        hax = f.add_axes([haxleft, haxbottom, haxwidth, haxheight])
        ### Plot the histogram
        hax.hist(data_hist, bins=bins, color=histcolor,
                 log=log, orientation='vertical')
        hax.set_xlim(vmin, vmax)
        hax.axis('off')

        if title is not None:
            if title_alignment is None:
                title_alignment = 'bottom center'

            xy = {
                'bottom': (0.5, -labelpad),
                'top': (0.5, 1+labelpad+histpad+histratio),
                'gap right': (1+labelpad, 1 + histpad/2),
                'gap left': (-labelpad, 1 + histpad/2),
                'both right': (1+labelpad, (1+histpad+histratio)/2),
                'both left': (-labelpad, (1+histpad+histratio)/2),
            }
            xy['bottom center'], xy['top center'] = xy['bottom'], xy['top']
            xy['center bottom'], xy['center top'] = xy['bottom'], xy['top']

            va = {
                'bottom': 'top',
                'top': 'bottom',
                'gap right': 'center',
                'gap left': 'center',
                'both right': 'center',
                'both left': 'center',
            }
            va['bottom center'], va['top center'] = va['bottom'], va['top']
            va['center bottom'], va['center top'] = va['bottom'], va['top']

            ha = {
                'bottom': 'center',
                'top': 'center',
                'gap right': 'left',
                'gap left': 'right',
                'both right': 'left',
                'both left': 'right'
            }
            ha['bottom center'], ha['top center'] = ha['bottom'], ha['top']
            ha['center bottom'], ha['center top'] = ha['bottom'], ha['top']

            cax.annotate(
                title, fontsize=title_fontsize, weight=title_weight,
                xycoords='axes fraction',
                va=va[title_alignment], xy=xy[title_alignment],
                ha=ha[title_alignment])

        ###### Relabel the first and last values if extending the colorbar
        cax.tick_params(labelsize=ticklabel_fontsize)
        plt.draw()
        xticks = cax.get_xticks()
        xticklabels = [c._text for c in cax.get_xticklabels()]
        if extend == 'neither':
            pass
        if extend in ['min','both']:
            xticklabels[0] = '≤' + xticklabels[0]
        if extend in ['max','both']:
            xticklabels[-1] += '+'
        if extend != 'neither':
            cax.set_xticks(xticks)
            cax.set_xticklabels(xticklabels)

    ### Vertical orientation
    elif orientation in ['vertical', 'vert', 'v', None]:
        caxleft = ax0width + ax0x0 + (ax0width * (cbarleft - 1))
        caxbottom = ax0y0 + ax0height * cbarbottom
        caxwidth = cbarwidth * ax0width
        caxheight = cbarheight * ax0height

        cax = f.add_axes([caxleft, caxbottom, caxwidth, caxheight])

        cbar = mpl.colorbar.ColorbarBase(
            cax, cmap=cmap, norm=norm, orientation='vertical',
            extend=extend, extendfrac=extendfrac)
        cax.yaxis.set_ticks_position('left')

        ##### Add histogram
        haxleft = caxleft + (cbarwidth + histpad) * ax0width
        haxbottom = caxbottom + (
            extendfrac[0] * caxheight if extend in ['min','both']
            else 0
        )
        haxwidth = histratio * cbarwidth * ax0width
        if extend == 'neither':
            haxheight = caxheight
        elif extend == 'max':
            haxheight = caxheight - extendfrac[1] * caxheight
        elif extend == 'min':
            haxheight = caxheight - extendfrac[0] * caxheight
        elif extend == 'both':
            haxheight = caxheight - sum(extendfrac) * caxheight

        hax = f.add_axes([haxleft, haxbottom, haxwidth, haxheight])

        hax.hist(data_hist, bins=bins, color=histcolor,
                 log=log, orientation='horizontal')
        hax.set_ylim(vmin, vmax)
        hax.axis('off')

        if title is not None:
            ## 'both center': align to center of cbar + hist
            ## 'cbar center': align to center of cbar
            ## 'cbar left': align to left of cbar
            if title_alignment is None:
                title_alignment = 'gap center'

            xy = {
                'both center': ((1 + histpad + histratio)/2, 1+labelpad),
                'cbar center': (0.5, 1+labelpad),
                'cbar left': (0,1+labelpad),
                'hist right': (histratio + histpad + 1, 1+labelpad),
                'gap center': (1 + histpad/2, 1+labelpad),
            }
            horizontalalignment = {
                'both center': 'center',
                'cbar center': 'center',
                'cbar left': 'left',
                'hist right': 'right',
                'gap center': 'center',
            }

            cax.annotate(
                title, fontsize=title_fontsize, weight=title_weight,
                xycoords='axes fraction',
                verticalalignment='bottom', xy=xy[title_alignment],
                horizontalalignment=horizontalalignment[title_alignment])

        ###### Relabel the first and last values if extending the colorbar
        cax.tick_params(labelsize=ticklabel_fontsize)
        plt.draw()
        yticks = cax.get_yticks()
        yticklabels = [c._text for c in cax.get_yticklabels()]
        if extend == 'neither':
            pass
        if extend in ['min','both']:
            yticklabels[0] = '≤' + yticklabels[0]
        if extend in ['max','both']:
            yticklabels[-1] = '≥' + yticklabels[-1]
        if extend != 'neither':
            cax.set_yticks(yticks)
            cax.set_yticklabels(yticklabels)

    ### Return axes
    return cax, hax, cbar


def plot2dhistarray(xdata, ydata, logcolor=True, bins=None,
    figsize=(5,7), gridspec_kw=None, sidehistcolor='0.5'):
    """
    Inputs
    ------
    bins: int (to use np.linstpace(datamin, datamax, 101) for both)
        or ((array of x bins), (array of y bins))
        or ((number of x bins), (number of y bins))

    Returns
    -------
    (f, ax): tuple of figure object and axes object
        * ax[(0,0)]: Upper x-axis histogram
        * ax[(1,0)]: Main 2d histogram
        * ax[(1,1)]: Right y-axis histogram
    """
    ### Format inputs
    if isinstance(bins, int):
        bins = [np.linspace(min(xdata), max(xdata), bins),
                np.linspace(min(ydata), max(ydata), bins)]
    elif isinstance(bins, tuple):
        if isinstance(bins[0], int) and isinstance(bins[1], int):
            bins = [np.linspace(min(xdata), max(xdata), bins[0]),
                    np.linspace(min(ydata), max(ydata), bins[1])]
        elif (isinstance(bins[0], np.ndarray) and (isinstance(bins[1], np.ndarray))):
            pass
    elif isinstance(bins, np.ndarray):
        bins = [bins, bins]
    elif bins is None:
        bins = [np.linspace(min(xdata), max(xdata), 101),
                np.linspace(min(ydata), max(ydata), 101)]

    if gridspec_kw is None:
        gridspec_kw = {'height_ratios': [1,6], 'width_ratios': [6,1],
                       'hspace':0.02, 'wspace': 0.02}
    ### Procedure
    f, ax = plt.subplots(
        2, 2, figsize=figsize, sharex='col', sharey='row', #dpi=300,
        gridspec_kw=gridspec_kw)

    ### Add horizontal histogram to top
    ax[(0,0)].hist(xdata, bins=bins[0], color=sidehistcolor)
    ax[(0,0)].axis('off')

    _,_,_,im = ax[(1,0)].hist2d(
        xdata, ydata, bins=bins, norm=mpl.colors.LogNorm())

    ### Add vertical histogram to right
    ax[(1,1)].hist(ydata, bins=bins[1], color=sidehistcolor, orientation='horizontal')
    ax[(1,1)].axis('off')

    ### Turn off the spare upper left axis
    ax[(0,1)].axis('off')

    ### Add bottom colorbar
    cb = plt.colorbar(im, ax=ax[(1,0)], orientation='horizontal', fraction=0.15)
    cb.set_label('Counts', fontsize='x-large')
    ### Shrink the right histogram in a dumb way
    cb = plt.colorbar(im, ax=ax[(1,1)], orientation='horizontal', fraction=0.15)
    cb.remove()

    return f, ax


def plotquarthist(
    ax, dfplot,
    histpad=0.1, quartpad=-0.1, pad=None,
    squeeze=0.7,
    plothist=True,
    number_of_bins=101,
    alpha=0.6,
    bootstrap=5000,
    direction='right',
    x_locations=None,
    hist_range=None,
    format_axes=True,
    flierprops=None,
    whiskerprops=None,
    medianfacecolor='none',
    medianedgecolor='k',
    medianmarker='o',
    mediansize=15,
    cicolor='0.75',
    ciwidth=3,
    histcolor=None,
    density=False,
    spines=['left', 'bottom'],
    xticklabelrotation=0,
    ):
    """
    Inputs
    ------

    Notes
    -----
    * x-axis values should be the column labels
    * pad, if not None, overwrites histpad and quartpad
    """
    ### Interpret inputs
    if flierprops is None:
        flierprops={'markersize': 2, 'markerfacecolor': 'none',
                    'markeredgewidth': 0.25, 'markeredgecolor': '0.5'}

    if hist_range is None:
        hist_range = (dfplot.min().min(), dfplot.max().max())
    else:
        assert (len(hist_range)==2 or type(hist_range) in [float, int])

    labels = list(dfplot.columns)
    data_sets = [dfplot[label].dropna().values for label in labels]

    if x_locations is None:
        x_locations = dfplot.columns.values
        if any([isinstance(col, str) for col in x_locations]):
            x_locations = range(len(x_locations))

    if (pad is not None) and (direction == 'right'):
        histpad, quartpad = pad, -pad
    elif (pad is not None) and (direction == 'left'):
        histpad, quartpad = -pad, pad

    ###### Some shared quantities between quarts and hists
    ### Minimum distance between x points in units of x scale
    xscale = min(np.diff(x_locations))

    ###### Histograms - data
    if plothist:
        ### Compute histograms
        binned_data_sets = [
            np.histogram(d, range=hist_range, bins=number_of_bins)[0]
            for d in data_sets]

        ###### WITHOUT normalization
        if density in [False, None]:
            ### Number of counts in most-filled bin --> sets x spacing of hists
            spacing = np.max(binned_data_sets)

            ### Scaled bins to xscale
            scaled_data_sets = [
                binned_data / spacing * squeeze
                for binned_data in binned_data_sets]
        ###### WITH normalization
        else:
            # ### Normalization factor
            # normfactor = [binned_data.sum() for binned_data in binned_data_sets]

            # ### Normalize bin filling to sum to 1
            # normed_data_sets = [
            #     binned_data_sets[i] / normfactor[i]
            #     for i in range(len(binned_data_sets))]

            # ### Scale them back up to fill the space

            ### Number of counts in most-filled bin in each col --> x spacing
            spacing = [binned_data.max() for binned_data in binned_data_sets]

            ### Scaled bins to xscale
            scaled_data_sets = [
                binned_data_sets[i] / spacing[i] * squeeze
                for i in range(len(binned_data_sets))]

        ### Set bin edges
        bin_edges = np.linspace(hist_range[0], hist_range[1], number_of_bins + 1)
        # centers = 0.5 * (bin_edges + np.roll(bin_edges, 1))[:-1]   ### WRONG!!!
        centers = 0.5 * (bin_edges + np.roll(bin_edges, 1))[1:]
        heights = np.diff(bin_edges)

    ###### Quartlines
    ### Calculate medians and confidence interals
    medians, cilos, cihis = [], [], []
    for i in range(len(data_sets)):
        medianstats = mpl.cbook.boxplot_stats(data_sets[i], bootstrap=bootstrap)[0]
        medians.append(medianstats['med'])
        cilos.append(medianstats['cilo'])
        cihis.append(medianstats['cihi'])

    ###### Combo plot
    if plothist:
        ### Histograms
        assert len(x_locations) == len(scaled_data_sets), "mismatched axes"
        for i in range(len(data_sets)):
            ### Set bar color
            if isinstance(histcolor, list):
                c = histcolor[i]
            elif isinstance(histcolor, dict):
                c = histcolor[labels[i]]
            else:
                c = histcolor
            ### Plot bars
            if direction == 'right':
                ## Bar z ordering
                zorders = list(range(len(data_sets)))[::-1] # Reversed for correct overlap
                lefts = x_locations[i] + histpad * xscale
                ax.barh(y=centers, width=scaled_data_sets[i], height=heights,
                        left=lefts, alpha=alpha, zorder=zorders[i], color=c)
            elif direction == 'left':
                zorders = list(range(len(data_sets)))
                lefts = x_locations[i] - scaled_data_sets[i] + histpad * xscale
                ax.barh(y=centers, width=scaled_data_sets[i], height=heights,
                        left=lefts, alpha=alpha, zorder=zorders[i], color=c)

    ### Quartlines
    ## Whiskers and outliers
    ax.boxplot(
        data_sets,
        positions=(x_locations + quartpad * xscale),
        showcaps=False, showbox=False,
        medianprops={'color': 'none', 'linewidth': 0},
        whiskerprops=whiskerprops,
        flierprops=flierprops,
        zorder=4998
    )
    ## Medians
    ax.scatter(x_locations + quartpad * xscale,
               medians,
               zorder=5000, marker=medianmarker, s=mediansize,
               c=medianfacecolor, edgecolor=medianedgecolor,
    )
    ## Botstrapped 95% confidence intervals for median
    for i in range(len(data_sets)):
        ### Set median range color
        if isinstance(cicolor, list):
            c = cicolor[i]
        else:
            c = cicolor
        ### Plot median bars
        ax.plot(np.array([x_locations[i], x_locations[i]]) + (quartpad * xscale),
                [cilos[i], cihis[i]],
                zorder=4999, solid_capstyle='butt',
                lw=ciwidth, c=c,
    )

    ### Axis formatting
    if format_axes:
        ax.set_xticks(x_locations)
        # ax.set_xticklabels(labels, rotation=60) # old version
        if (xticklabelrotation == 0) or (xticklabelrotation >= 60):
            ax.set_xticklabels(labels, rotation=xticklabelrotation)
        else:
            ax.set_xticklabels(labels, rotation=xticklabelrotation,
                ha='right', rotation_mode='anchor')
        if plothist and (direction == 'right'):
            ax.set_xlim(x_locations[0] - 5 * abs(quartpad) * xscale,
                        (x_locations[-1] + max(scaled_data_sets[-1])
                         + 1.5 * abs(histpad) * xscale)
                        )
        elif plothist and (direction == 'left'):
            ## Provide some extra padding on the left
            ax.set_xlim((x_locations[0] - max(scaled_data_sets[0])
                         - 1.5 * abs(histpad) * xscale),
                        x_locations[-1] + 3 * abs(quartpad) * xscale
                        )
        ax.tick_params(axis='both', direction='out', top=False, right=False)
        for which in ['left', 'right', 'bottom', 'top']:
            ax.spines[which].set_visible(False)
        if len(spines) >= 1:
            for which in spines:
                ax.spines[which].set_visible(True)


def plotquartiles(
    dfframe=None, ax=None,
    innerband=['25%','75%'],
    outerband=['2.5%','97.5%'],
    inner=True, outer=True, minmax=True, median=True,
    color='C0', alpha=0.2, labels=True, dfdescribe=None,
    lines=None, lws=None, linestyles=None):
    """
    """
    ### Input formatting
    if lines is None:
        lines = []
    percentiles = innerband + ['50%'] + outerband + lines
    percentiles = sorted(list(set(percentiles)))
    if lws is None:
        lws = dict(zip(lines, [1.5]*len(lines)))
    if linestyles is None:
        linestyles = dict(zip(lines, ['-']*len(lines)))
    fractions = [float(pct[:pct.find('%')])*.01 for pct in percentiles]
    if dfdescribe is None:
        dfdescribe = dfframe.describe(percentiles=fractions)
    if labels is True:
        labels = {
            'outer': 'central {:.0f}%'.format((fractions[-1]-fractions[-0])*100),
            'inner': 'central {:.0f}%'.format((fractions[-2]-fractions[1])*100),
            'median': 'median',
            'min': 'min/max',
            'max': '_nolabel_',
            'minmax': 'all nodes',
        }
    elif labels is False:
        labels = dict(zip(['outer','inner','median','min','max','minmax'],
                          ['_nolabel_']*6))
    else:
        labels = labels

    ### Inner band
    if inner is True:
        ax.fill_between(
            dfdescribe.columns.values,
            dfdescribe.loc[innerband[0]].values,
            dfdescribe.loc[innerband[1]].values,
            color=color, lw=0, alpha=alpha*2,
            label=labels.get('inner','_nolabel_'),
        )
    ### Outer band
    if outer is True:
        ax.fill_between(
            dfdescribe.columns.values,
            dfdescribe.loc[outerband[0]].values,
            dfdescribe.loc[outerband[1]].values,
            color=color, lw=0, alpha=alpha,
            label=labels.get('outer','_nolabel_'),
        )
    ### Median
    if median is True:
        ax.plot(
            dfdescribe.columns.values, dfdescribe.loc['50%'].values,
            color=color, label=labels.get('median','_nolabel_'))

    ### Min/Max band
    if minmax is True:
        ax.fill_between(
            dfdescribe.columns.values,
            dfdescribe.loc['min'].values,
            dfdescribe.loc['max'].values,
            color=color, lw=0, alpha=alpha/2,
            label=labels.get('minmax','_nolabel_'),
        )

    ### Extra lines
    for line in lines:
        ax.plot(
            dfdescribe.columns.values, dfdescribe.loc[line].values,
            color=color, label=labels.get(line,'_nolabel_'),
            lw=lws[line], ls=linestyles[line])


###### fill_between
def subplotpercentiles(ax, dfplot, datacolumn, tracecolumn, subplotcolumn=None,
    colordict=None, traceorder=None, ylimits=None, xdivs=2,
    plottype='line', fillto=0, ascending=True, **kwargs
    ):
    """
    """
    ### Get categorical variables
    if traceorder is None:
        tracevals = dfplot[tracecolumn].unique()
        tracevals.sort()
    else:
        tracevals = traceorder

    ### Get colors
    if colordict is None:
        colors = ['C{}'.format(i%10) for i in range(len(tracevals))]
        colordict = dict(zip(tracevals, colors))
    elif isinstance(colordict, list):
        colordict = dict(zip(tracevals, colordict))
    elif colordict in ['order', 'ordered', 'rainbow', 'sort']:
        colordict = rainbowmapper(tracevals)

    ### Cycle through tracevals
    for i, traceval in enumerate(tracevals):
        ### Get the data
        dfpanel = dfplot.loc[
            (dfplot[tracecolumn] == traceval)].copy()
        x = np.linspace(0,100,len(dfpanel))
        y = dfpanel[datacolumn].sort_values(ascending=ascending)

        ### Plot it
        if plottype in ['line', 'trace', 'plot']:
            ax.plot(x, y, label=traceval,
                    c=colordict[traceval], **kwargs)
        elif plottype in ['area', 'fillbetween', 'fill_between']:
            if i == 0:
                ax.fill_between(x, y, fillto, label=traceval,
                        color=colordict[traceval], **kwargs)
            else:
                y2 = dfplot.loc[
                    (dfplot[tracecolumn]==tracevals[i-1]), datacolumn
                ].sort_values(ascending=ascending)
                ax.fill_between(x, y, y2, label=traceval,
                        color=colordict[traceval], **kwargs)

        ax.set_xlim(0,100)
        ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(xdivs))
        ax.tick_params(axis='both', which='major', direction='in',
                       top=True, right=True, length=4)
        ax.tick_params(axis='x', which='minor', direction='in',
                       top=True, length=3, color='k')

    [line.set_zorder(10) for line in ax.lines] # lines on top of axes
    ax.set_ylabel(datacolumn, fontsize='x-large', weight='bold')

    ### Set y limits based on ymin, ymax
    if ylimits is not None:
        assert len(ylimits) == 2, 'len(ylimits) must be 2 but is {}'.format(len(ylimits))
        if isinstance(ylimits[0], str) and isinstance(ylimits[1], str):
            ymin = float(ylimits[0].replace('%','')) * 0.01
            ymax = float(ylimits[1].replace('%','')) * 0.01
            describe = dfplot[datacolumn].describe(percentiles=[ymin, ymax])
            ax.set_ylim(describe[ylimits[0]], describe[ylimits[1]])
        else:
            ax.set_ylim(ylimits[0], ylimits[1])


def plotpercentiles(dfplot, datacolumn, tracecolumn, subplotcolumn=None,
    colordict=None, figsize=None, unsubplot=False,
    traceorder=None, subplotorder=None, ylimits=None,
    xdivs=2, dpi=None,
    ):
    """
    """
    ### Get categorical variables
    if traceorder is None:
        tracevals = dfplot[tracecolumn].unique()
        tracevals.sort()
    else:
        tracevals = traceorder

    if subplotcolumn is None:
        ncols = 1
        subplotvals = None
    elif subplotorder is None:
        subplotvals = dfplot[subplotcolumn].unique()
        subplotvals.sort()
        ncols = len(subplotvals)
    else:
        ncols = len(subplotorder) + int(unsubplot)
        subplotvals = subplotorder

    if figsize is None:
        figsize = (ncols*2, 3)

    ### Check for overload
    if ncols >= 50:
        raise Exception('Whoooah too many columns: {}'.format(ncols))
    ### Get colors
    if colordict is None:
        colors = ['C{}'.format(i%10) for i in range(len(tracevals))]
        colordict = dict(zip(tracevals, colors))
    elif isinstance(colordict, list):
        colordict = dict(zip(tracevals, colordict))
    elif colordict in ['order', 'ordered', 'rainbow', 'sort']:
        colordict = rainbowmapper(tracevals)

    ### Plot it
    f, ax = plt.subplots(ncols=ncols, sharey=True, figsize=figsize, dpi=dpi)
    for i in range(len(tracevals)):
        if ncols > 1:
            for j in range(len(subplotvals)):
                dfpanel = dfplot.loc[
                    (dfplot[subplotcolumn] == subplotvals[j])
                    & (dfplot[tracecolumn] == tracevals[i])].copy()
                x = np.linspace(0,100,len(dfpanel))
                y = dfpanel[datacolumn].sort_values()
                ax[j].plot(x, y, label=tracevals[i],
                           c=colordict[tracevals[i]])
                ax[j].set_xlim(0,100)
                ax[j].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(xdivs))
                ax[j].set_title(subplotvals[j], weight='bold', fontname='Arial')
                ax[j].tick_params(
                    axis='both', which='major', direction='in',
                    top=True, right=True, length=4)
                ax[j].tick_params(
                    axis='x', which='minor', direction='in',
                    top=True, length=3, color='k')
                [line.set_zorder(10) for line in ax[j].lines] # lines on top of axes

            ### Plot the all-data subplot
            if unsubplot:
                dfpanel = dfplot.loc[
                    (dfplot[tracecolumn] == tracevals[i])].copy()
                x = np.linspace(0,100,len(dfpanel))
                y = dfpanel[datacolumn].sort_values()
                ax[-1].plot(x, y, label=tracevals[i],
                           c=colordict[tracevals[i]])
                ax[-1].set_xlim(0,100)
                ax[-1].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(xdivs))
                ax[-1].set_title('All', weight='bold', fontname='Arial')
                ax[-1].tick_params(
                    axis='both', which='major', direction='in',
                    top=True, right=True, length=4)
                ax[-1].tick_params(
                    axis='x', which='minor', direction='in',
                    top=True, length=3, color='k')
                [line.set_zorder(10) for line in ax[-1].lines] # lines on top of axes

            ### Label the leftmost axis
            ax[0].set_ylabel(datacolumn, fontsize='x-large', weight='bold')
        else:
            dfpanel = dfplot.loc[
                (dfplot[tracecolumn] == tracevals[i])].copy()
            x = np.linspace(0,100,len(dfpanel))
            y = dfpanel[datacolumn].sort_values()
            ax.plot(x, y, label=tracevals[i],
                       c=colordict[tracevals[i]])
            ax.set_xlim(0,100)
            ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(xdivs))
            ax.tick_params(
                axis='both', which='major', direction='in',
                top=True, right=True, length=4)
            ax.tick_params(
                axis='x', which='minor', direction='in',
                top=True, length=3, color='k')
            [line.set_zorder(10) for line in ax.lines] # lines on top of axes
            ax.set_ylabel(datacolumn, fontsize='x-large', weight='bold')

    ### Set y limits based on ymin, ymax
    if ylimits is not None:
        assert len(ylimits) == 2, 'len(ylimits) must be 2 but is {}'.format(len(ylimits))
        if isinstance(ylimits[0], str) and isinstance(ylimits[1], str):
            ymin = float(ylimits[0].replace('%','')) * 0.01
            ymax = float(ylimits[1].replace('%','')) * 0.01
            describe = dfplot[datacolumn].describe(percentiles=[ymin, ymax])
            plt.ylim(describe[ylimits[0]], describe[ylimits[1]])
        else:
            plt.ylim(ylimits[0], ylimits[1])

    # if xlabel:
    #     ### add big axis, hide frame, ticks, and labels
    #     f.add_subplot(111, frameon=False)
    #     plt.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
    #     plt.xlabel('Percentile [%]', fontsize='x-large', weight='bold', fontname='Arial')

    return f, ax


def get_aea_bounds(dfplot, buffer=1.05, lat_1=29.5, lat_2=45.5):
    """
    Purpose: Get bounds for use in plotusascattermap
    """
    import pyproj
    latlabel, lonlabel = get_latlonlabels(dfplot)


    bound = [
        dfplot[lonlabel].min(), dfplot[latlabel].min(),
        dfplot[lonlabel].max(), dfplot[latlabel].max()
    ]
    coords = [(bound[0],bound[1]), (bound[2],bound[1]),
              (bound[2],bound[3]), (bound[0],bound[3]),]

    ### Undo defaults if desired
    if lat_1 is None:
        lat1 = bound[1]
    else:
        lat1 = lat_1
    if lat_2 is None:
        lat2 = bound[3]
    else:
        lat2 = lat_2
    ### Get the other params from the center of the supplied points
    lat_0 = (bound[1]+bound[3])/2
    lon_0 = (bound[0]+bound[2])/2

    pa = pyproj.Proj(
        "+proj=aea +lat_1={} +lat_2={} +lat_0={} +lon_0={}".format(
            lat1, lat2, lat_0, lon_0))
    lon,lat = zip(*coords)
    x,y = pa(lon,lat)
    # cop = {'type':'Polygon','coordinates':[zip(x,y)]}
    width = 2 * max([abs(i) for i in x]) * buffer
    height = 2 * max([abs(i) for i in y]) * buffer

    bounds = {
        'lat_1': lat1, 'lat_2': lat2,
        'lon_0': lon_0, 'lat_0': lat_0,
        'width': width, 'height': height,
    }
    return bounds


def draw_screen_poly(poly, m,
    cvalue=0.5, cmap=plt.cm.viridis,
    facecolor=None, edgecolor='none',
    alpha=1, ax=None,
    linewidth=None,
    ):
    """
    Notes
    -----
    * 0.15 is a good linewidth to avoid gaps between polygons
    Sources
    -------
    https://stackoverflow.com/questions/12251189/how-to-draw-rectangles-on-a-basemap
    https://basemaptutorial.readthedocs.io/en/latest/shapefile.html
    """
    import shapely
    if facecolor is None:
        facecolor = cmap(cvalue)
    if edgecolor is None:
        edgecolor = facecolor
    if linewidth is None:
        linewidth = 0
    if type(poly) is shapely.geometry.multipolygon.MultiPolygon:
        for subpoly in poly:
            x,y = m(subpoly.exterior.coords.xy[0], subpoly.exterior.coords.xy[1])
            xy = list(zip(x,y))
            drawpoly = mpl.patches.Polygon(
                xy, facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, alpha=alpha)
            if ax is None:
                ax = plt.gca()
            ax.add_patch(drawpoly)
    else:
        x,y = m(poly.exterior.coords.xy[0], poly.exterior.coords.xy[1])
        xy = list(zip(x,y))
        drawpoly = mpl.patches.Polygon(
            xy, facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, alpha=alpha)
        if ax is None:
            ax = plt.gca()
        ax.add_patch(drawpoly)


def plotusascattermap(
    dfplot, colorcolumn=None, sizecolumn=None, filterdict=None, sort=True,
    basemap=None, cmap=cmocean.cm.rain, mappath=None,
    facecolor='w', edgecolor='w', latlonlabels=None,
    markersize=None, marker='o', figsize=(10,7.5), dpi=None,
    zrange=None, colors=None, maptype='scatter', contourlevels=100,
    colorbarhist=True, colorbarkwargs={}, colorbartitle=None,
    statelinewidths=0.25, bounds='usa', downloadmap=False,
    markeredgecolor=None, markerlw=None, f=None, ax=None,
    maskwater=False, masklakes=False, buffer=1.05,
    alpha=1, markerfacecolor='C3', **plotkwargs):
    """
    Inputs
    ------
    * bounds: 'usa', 'CA', or dict with keys in
    ['lat_1','lat_2','lon_0','lat_0','width','height']

    References
    ----------
    * Map: https://hifld-geoplatform.opendata.arcgis.com/datasets/political-boundaries-area
    * Canada/Mexico maps: https://gadm.org/download_country_v3.html
    """
    import geopandas as gpd
    import shapely
    ### Set the map bounds based on input
    if isinstance(bounds, dict):
        dictbounds = bounds
    elif isinstance(bounds, list):
        dictbounds = dict(zip(
            ['lat_1','lat_2','lon_0','lat_0','width','height'],
            bounds
        ))
    elif bounds in ['usa', 'USA', 'all', 'default', None]:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -96.5, 'lat_0': 38.5}
    elif bounds.lower() in ['ca', 'california', 'caiso','camx','egrid_camx']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -119, 'lat_0': 36}
    elif bounds.lower() in ['tx', 'texas', 'ercot','erct','egrid_erct']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -100, 'lat_0': 31}
    elif bounds.lower() in ['pjm']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -81.5, 'lat_0': 39}
    elif bounds.lower() in ['isone', 'new england','newe','egrid_newe']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -70.5, 'lat_0': 44}
    elif bounds.lower() in ['nyiso', 'ny', 'new york','nyup','egrid_nyup']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -76, 'lat_0': 43}
    elif bounds.lower() in ['miso', 'midwest']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -91, 'lat_0': 39}
    elif bounds.lower() in ['wecc']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -114, 'lat_0': 40}
    elif bounds.lower() in ['northeast']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -73.5, 'lat_0': 44}

    elif bounds.lower() in ['aznm','egrid_aznm','southwest']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -110, 'lat_0': 34.5}
    elif bounds.lower() in ['florida','fl','frcc','egrid_frcc']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -84, 'lat_0': 28}
    elif bounds.lower() in ['mroe','egrid_mroe','wi','wisconsin']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -89, 'lat_0': 45}
    elif bounds.lower() in ['mrow','egrid_mrow']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -98, 'lat_0': 44.5}
    elif bounds.lower() in ['long island','longisland','nyli','egrid_nyli',
                            'nycw','egrid_nycw']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -73, 'lat_0': 40.9}
    elif bounds.lower() in ['nwpp','egrid_nwpp','northwest']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -114, 'lat_0': 42}
    elif bounds.lower() in ['rfce','egrid_rfce']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -77., 'lat_0': 39.75}
    elif bounds.lower() in ['rfcm','egrid_rfcm','michigan','mi']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -84.5, 'lat_0': 43.7}
    elif bounds.lower() in ['rfcw','egrid_rfcw']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -83.8, 'lat_0': 42}
    elif bounds.lower() in ['rmpa','egrid_rmpa']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -106, 'lat_0': 41}
    elif bounds.lower() in['spno','egrid_spno','nebraska','ne']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -97.5, 'lat_0': 38.5}
    elif bounds.lower() in ['spso','egrid_spso']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -97.3, 'lat_0': 33.5}
    elif bounds.lower() in ['srmv','egrid_srmv']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -93, 'lat_0': 33}
    elif bounds.lower() in ['srmw','egrid_srmw']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -91, 'lat_0': 39.}
    elif bounds.lower() in ['srso','egrid_srso']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -86.5, 'lat_0': 32.5}
    elif bounds.lower() in ['srtv','egrid_srtv']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -86.3, 'lat_0': 35.5}
    elif bounds.lower() in ['srvc','egrid_srvc']:
        dictbounds = {'lat_1': 29.5, 'lat_2': 45.5, 'lon_0': -79.5, 'lat_0': 35.8}
    elif bounds in ['data','bounds','zoom','buffer']:
        dictbounds = get_aea_bounds(dfplot, buffer=buffer)

    projstring = '+proj=aea +lat_1={} +lat_2={} +lat_0={} +lon_0={}'.format(
        dictbounds['lat_1'], dictbounds['lat_2'], dictbounds['lat_0'], dictbounds['lon_0'])

    ### Load basemap if necessary
    if not basemap:

        ###### Download the map file if necessary
        if (not os.path.exists(mappath)) and (downloadmap is False):
            raise Exception("No file at {}; try setting downloadmap=True".format(mappath))
        if (not os.path.exists(mappath)) and (downloadmap is True):
            import urllib.request
            import zipfile
            ### Download it
            url = ('https://opendata.arcgis.com/datasets/bee7adfd918e4393995f64e155a1bbdf_0.zip?'
                   'outSR=%7B%22wkid%22%3A102100%2C%22latestWkid%22%3A3857%7D')
            os.makedirs(mappath, exist_ok=True)
            urllib.request.urlretrieve(url, mappath+'.zip')
            ### Unzip it
            zip_ref = zipfile.ZipFile(mappath+'.zip', 'r')
            zip_ref.extractall(os.path.join(mappath,''))
            zip_ref.close()

        ### Read the state outlines
        dfbasemap = gpd.read_file(mappath).to_crs(projstring)

    else:
        dfbasemap = basemap.copy()

    ### Get the state metadata
    dfbasemap = dfbasemap.loc[
        (dfbasemap.COUNTRY == 'USA')
        & (~dfbasemap.NAME.isin(
            ["water/agua/d'eau",'Navassa Island',
             'Puerto Rico','United States Virgin Islands',
             'Alaska', 'Hawaii']))
    ]

    ### Use passed axis, or draw new plot and axis
    if (f is None) or (ax is None):
        ### Draw the plot
        plt.close()
        f, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.axis('off')
    else:
        pass

    ### Plot the US states
    if edgecolor not in ['none',None]:
        dfbasemap.plot(ax=ax, lw=0.5, facecolor='none', edgecolor=edgecolor, zorder=1e6)
    if facecolor not in ['none',None]:
        dfbasemap.plot(ax=ax, lw=0.5, facecolor=facecolor, edgecolor='none', zorder=0)

    ### Filter data to plot
    dfmap = dfplot.copy()
    if filterdict is not None:
        for key in filterdict:
            dfmap = dfmap.loc[dfmap[key] == filterdict[key]]

    ### Order points and get zrange
    if colorcolumn is not None:
        if sort in [True,'ascending','ascend','positive','normal']:
            dfmap = dfmap.sort_values(colorcolumn).copy()
        elif sort in ['descending','reverse','descend','negative']:
            dfmap = dfmap.sort_values(colorcolumn, ascending=False).copy()
        else:
            pass

        datamin, datamax = dfmap[colorcolumn].min(), dfmap[colorcolumn].max()
        if zrange is None:
            zrangeplot = [datamin, datamax]
        else:
            assert len(zrange) == 2, "len(zrange) must be 2 but is {}".format(len(zrange))
            if isinstance(zrange[0], str) and isinstance(zrange[1], str):
                assert (zrange[0].endswith('%') and zrange[1].endswith('%')), "zrange != %"
                zmin = float(zrange[0].replace('%','')) * 0.01
                zmax = float(zrange[1].replace('%','')) * 0.01
                describe = dfmap[colorcolumn].describe(percentiles=[zmin, zmax])
                zrangeplot = [describe[zrange[0]], describe[zrange[1]]]
            else:
                zrangeplot = [zrange[0], zrange[1]]

    ### Get lat, lon labels
    latlabel, lonlabel = get_latlonlabels(dfmap, latlonlabels=latlonlabels)
    ### Convert to geodataframe
    dfmap['geometry'] = dfmap.apply(
        lambda row: shapely.geometry.Point(row[lonlabel], row[latlabel]),
        axis=1
    )
    dfmap = gpd.GeoDataFrame(dfmap).set_crs('EPSG:4326').to_crs(projstring)

    ### Set colors and sizes
    if colorcolumn is not None:
        if colors is None:
            colordata = dfmap[colorcolumn].values
        elif isinstance(colors, dict):
            colordata = dfmap[colorcolumn].map(lambda x: colors[x]).values
    elif colorcolumn is None:
        if colors is None:
            colordata = markerfacecolor
        else:
            colordata = colors

    if (sizecolumn is None) and (markersize is None):
        size = 2
    elif markersize is None:
        size = dfmap[sizecolumn].values
    elif sizecolumn is None:
        size = markersize
    else:
        size = dfmap[sizecolumn].values * markersize

    if (maptype == 'scatter') and (colorcolumn is not None):
        dfmap.plot(
            ax=ax, column=colorcolumn, marker=marker, markersize=size, cmap=cmap,
            vmin=zrangeplot[0], vmax=zrangeplot[1], alpha=alpha,
            edgecolor=markeredgecolor, lw=markerlw, **plotkwargs)
    elif (maptype == 'scatter') and (colorcolumn is None):
        dfmap.plot(
            ax=ax, marker=marker, color=markerfacecolor, markersize=size,
            edgecolor=markeredgecolor, lw=markerlw, alpha=alpha)
    # elif maptype == 'contour':
    #     m_in.contour(
    #         x, y, colordata, tri=True, cmap=cmap,
    #         levels=np.linspace(zrangeplot[0],zrangeplot[1],contourlevels),
    #         extend='both', ax=ax, **plotkwargs)
    # elif maptype == 'contourf':
    #     m_in.contourf(
    #         x, y, colordata, tri=True, cmap=cmap,
    #         levels=np.linspace(zrangeplot[0],zrangeplot[1],contourlevels),
    #         extend='both', ax=ax, **plotkwargs)
    # elif maptype in ['poly','polygon','vector']:
    #     for index in dfmap.index:
    #         # if type(colors) == dict:
    #         #     cvalue = colors[dfmap.loc[index,colorcolumn]]
    #         # else:
    #         #     if colorcolumn is not None:
    #         #         cvalue = (
    #         #             (dfmap.loc[index,colorcolumn] - zrangeplot[0])
    #         #             / (zrangeplot[1] - zrangeplot[0])
    #         #             #* (datamax - datamin) + datamin
    #         #         )
    #         #     else:
    #         #         cvalue = markerfacecolor
    #         if colorcolumn is not None:
    #             cvalue = (
    #                 (dfmap.loc[index,colorcolumn] - zrangeplot[0])
    #                 / (zrangeplot[1] - zrangeplot[0])
    #                 #* (datamax - datamin) + datamin
    #             )
    #         else:
    #             cvalue = markerfacecolor
    #         draw_screen_poly(
    #             dfmap.loc[index,'geometry'], m_in, ax=ax,
    #             cvalue=cvalue, alpha=alpha,
    #             facecolor=None if colorcolumn is not None else markerfacecolor,
    #             edgecolor=markeredgecolor,
    #             # cvalue=dfmap.loc[index,colorcolumn],
    #             cmap=cmap, linewidth=markerlw,
    #         )
    #     ### Plot one point; otherwise basemap won't work
    #     x,y = m_in([dfmap.loc[index, lonlabel]], [dfmap.loc[index, latlabel]])
    #     # x,y = m_in([dfmap.loc[0, lonlabel]], [dfmap.loc[0, latlabel]])
    #     # x,y = m_in([-100],[40])
    #     m_in.scatter(x, y, color='none', ax=ax)

    if (colorbarhist is True) and (colorcolumn is not None):
        ### Add legend if categorical
        if isinstance(colors, dict):
            patchlegend(colors, edgecolor=markeredgecolor, **colorbarkwargs)
        ### Add hist if not categorial
        else:
            _cax = addcolorbarhist(
                f=f, ax0=ax, data=colordata, title=colorbartitle, cmap=cmap,
                vmin=zrangeplot[0], vmax=zrangeplot[1],
                # title_fontsize='x-large',
                **colorbarkwargs)
            _returncax = True

    return f, ax
    # return f, ((ax, cax) if (returncax and colorbarhist) else ax)


def sparkline(ax, dsplot, endlabels=True,
    endlabelxpad=3, endlabelypad=0,
    xticks='default', minordivisions=None,
    ):
    """
    """
    dsplot.plot(ax=ax)

    ### Format axes
    ax.tick_params(axis='x', which='both', top='off')
    for which in ['left', 'bottom', 'right', 'top']:
        ax.spines[which].set_visible(False)
    ax.yaxis.set_visible(False)
    if xticks == 'default':
        ax.set_xticks([dsplot.index[0], dsplot.index[-1]])
    elif xticks is None:
        pass
    else:
        ax.set_xticks(xticks)

    if minordivisions is not None:
        ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(minordivisions))

    ### Annotate the ends
    if endlabels:
        ## Left
        ax.annotate(
            s='{:.1f}'.format(dsplot.iloc[0]),
            xy=(dsplot.index[0], dsplot.iloc[0]),
            xycoords='data', xytext=(-endlabelxpad,endlabelypad),
            textcoords='offset points',
            horizontalalignment='right', verticalalignment='center')
        ## Right
        ax.annotate(
            s='{:.1f}'.format(dsplot.iloc[-1]),
            xy=(dsplot.index[-1], dsplot.iloc[-1]),
            xycoords='data', xytext=(endlabelxpad,endlabelypad),
            textcoords='offset points',
            horizontalalignment='left', verticalalignment='center')


def plotyearbymonth(dfs, plotcols=None, colors=None,
    style='fill', lwforline=1, ls='-', figsize=(12,6), dpi=None,
    normalize=False, alpha=1, f=None, ax=None):
    """
    """
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def monthifier(x):
        return pd.Timestamp('2001-01-{} {:02}:00'.format(x.day, x.hour))

    if (f is None) and (ax is None):
        f,ax=plt.subplots(12,1,figsize=figsize,sharex=True,sharey=True, dpi=dpi)
    else:
        pass

    for i, month in enumerate(months):
        if isinstance(dfs, pd.Series):
            plotcols = str(dfs.name)
            dfs = pd.DataFrame(dfs.rename(plotcols))

        if isinstance(dfs, pd.DataFrame):
            if plotcols is None:
                plotcols = dfs.columns.tolist()

            if isinstance(plotcols, str):
                dfplot = dfs.loc['{} {}'.format(month, dfs.index[0].year)][[plotcols]]
                if normalize:
                    dfplot = dfplot / dfplot.max()
                dfplot.index = dfplot.index.map(monthifier)

                if style in ['fill', 'fill_between', 'f']:
                    ax[i].fill_between(
                        dfplot.index, dfplot[plotcols].values, lw=0, alpha=alpha,
                        color=(colors if isinstance(colors, (str, mpl.colors.ListedColormap, tuple))
                               else ('C0' if colors is None else colors[0])))
                elif style in ['line', 'l']:
                    ax[i].plot(
                        dfplot.index, dfplot[plotcols].values, lw=lwforline, alpha=alpha, ls=ls,
                        color=(colors if isinstance(colors, (str, mpl.colors.ListedColormap, tuple))
                               else ('C0' if colors is None else colors[0])))

            elif isinstance(plotcols, list):
                if isinstance(colors, str):
                    colors = [colors]*len(plotcols)
                elif colors is None:
                    colors = ['C{}'.format(i%10) for i in range(len(plotcols))]
                for j, plotcol in enumerate(plotcols):
                    dfplot = dfs.loc['{} {}'.format(month, dfs.index[0].year)][[plotcol]]
                    if normalize:
                        dfplot = dfplot / dfplot.max()
                    dfplot.index = dfplot.index.map(monthifier)

                    if style in ['fill', 'fill_between', 'f']:
                        ax[i].fill_between(dfplot.index, dfplot[plotcol].values,
                                           lw=0, alpha=alpha, color=colors[j], label=plotcol)
                    elif style in ['line', 'l']:
                        ax[i].plot(dfplot.index, dfplot[plotcol].values,
                                   lw=lwforline, alpha=alpha, ls=ls, color=colors[j], label=plotcol)

        ax[i].set_ylabel(month, rotation=0, ha='right', va='top')
        for which in ['left', 'right', 'top', 'bottom']:
                     ax[i].spines[which].set_visible(False)
        ax[i].tick_params(left=False,right=False,top=False,bottom=False)
        ax[i].set_yticks([])
        ax[i].set_xticks([])

    ax[0].set_xlim(pd.to_datetime('2001-01-01 00:00'), pd.to_datetime('2001-02-01 00:00'))
    if normalize:
        ax[0].set_ylim(0, 1)
    else:
        pass
        # ax[0].set_ylim(0,dfs[plotcols].max())

    return f, ax


def add_parasite_axis_converter(
    ax, converter, side='right', converterparams={},
    offset=0.1, tickdirection='out', ylabel=False,
    minor=True,
    ticks=None, ticklabels=None,
    ):
    """
    Add a parasite axis, modeled on
    'https://matplotlib.org/gallery/ticks_and_spines/'
    'multiple_yaxis_with_spines.html'.
    The ticks are taken directily from the primary axis, with
    new values generated by the converter function.

    Inputs
    ------
    ax: axis to parasitize
    converter: function, where first argument takes a float (which
        will be the tick values from the primay axis to copy)
    converterparams: dict of additional keywordparameters to
        pass to converter function
    """
    ### Some cleanup
    offset = 1 + offset if side == 'right' else -offset

    ### Input formatting
    if ticklabels is None:
        ticklabels = ticks

    ### Get parasite axis properties
    if ticks is None:
        oldticks = ax.get_yticks()
        newticks = [converter(oldtick,**converterparams)
                    for oldtick in oldticks]
        ticklabels = newticks
    else:
        newticks = ticks

    oldlim = ax.get_ylim()
    newlim = [converter(oldend,**converterparams)
              for oldend in oldlim]

    ### Add the parasite
    par = ax.twinx()
    par.spines[side].set_position(('axes',offset))
    par.set_frame_on(True)
    par.patch.set_visible(False)
    for sp in par.spines.values():
        sp.set_visible(False)
        par.spines[side].set_visible(True)
    par.set_yticks(newticks)
    par.set_yticklabels(ticklabels)
    par.set_ylim(*newlim)
    if minor:
        minorlocator = ax.yaxis.get_minor_locator()
        par.yaxis.set_minor_locator(minorlocator)
    if side == 'left':
        par.yaxis.set_label_position('left')
        par.yaxis.set_ticks_position('left')
    if ylabel:
        par.set_ylabel(ylabel)
    par.tick_params(axis='y', which='both', direction=tickdirection)

    return par


def _despine_sub(ax,
    top=False, right=False, left=True, bottom=True,
    direction='out'):
    """
    """
    if not top:
        ax.spines['top'].set_visible(False)
    if not right:
        ax.spines['right'].set_visible(False)
    if not left:
        ax.spines['left'].set_visible(False)
    if not bottom:
        ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='both', which='both',
                   direction=direction,
                   top=top, right=right,
                   left=left, bottom=bottom)

def despine(ax=None,
    top=False, right=False, left=True, bottom=True,
    direction='out'):
    """
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


def get_coordinates(keys, aspect=None, nrows=None, ncols=None):
    """
    Get a grid of subplots from a list of plot keys, with an aspect ratio
    roughly defined by the `aspect` input.

    Outputs
    -------
    tuple: (nrows [int], ncols [int], coords [dict])
    """
    if (not aspect) and (not nrows) and (not ncols):
        aspect = 1.618

    if ncols:
        _ncols = ncols
    else:
        if nrows:
            _ncols = len(keys) // nrows + bool(len(keys) % nrows)
        else:
            _ncols = max(min(int(np.around(np.sqrt(len(keys)) * aspect, 0)), len(keys)), 1)

    if nrows:
        _nrows = nrows
    else:
        _nrows = len(keys) // _ncols + int(bool(len(keys) % _ncols))

    if (_ncols == 1) or (_nrows == 1):
        coords = dict(zip(keys, range(max(_nrows, _ncols))))
    else:
        coords = dict(zip(keys, [(row,col) for row in range(_nrows) for col in range(_ncols)]))

    return _nrows, _ncols, coords


def trim_subplots(ax, nrows, ncols, nsubplots):
    """
    When using a 2d grid of subplots, trim off the empty subplots from the bottom right.
    The number of rows (nrows) is assumed to be defined as a function of ncols as:
    `nrows = nsubplots // ncols + (1 if nsubplots % ncols else 0)`
    """
    for col in range(nrows * ncols - nsubplots):
        ax[-1, -1-col].axis('off')


def patchlegend(colors, edgecolor='none', alpha=1, reverse=False, **kwargs):
    patches = [mpl.patches.Patch(
                   facecolor=colors[i],
                   edgecolor=edgecolor,
                   alpha=alpha,
                   label=i)
               for i in colors.keys()]
    if reverse is True:
        leg = plt.legend(handles=patches[::-1], **kwargs)
    else:
        leg = plt.legend(handles=patches, **kwargs)
    return leg


def _differentiate_lines_sub(ax, cycle=10, linestyles=['--',':','-.']):
    """
    """
    if isinstance(linestyles, str):
        ls = [linestyles,linestyles,linestyles]
    else:
        ls = linestyles
    lines = ax.get_lines()
    if len(lines) > 1*cycle:
        for line in lines[1*cycle:]:
            line.set_linestyle(ls[0])
    if len(lines) > 2*cycle:
        for line in lines[2*cycle:]:
            line.set_linestyle(ls[1])
    if len(lines) > 3*cycle:
        for line in lines[3*cycle:]:
            line.set_linestyle(ls[2])

def differentiate_lines(ax, cycle=10, linestyles=['--',':','-.']):
    """
    Notes
    -----
    * Use before calling the legend constructor
    """
    if ax is None:
        ax = plt.gca()
    if type(ax) is np.ndarray:
        for sub in ax:
            if type(sub) is np.ndarray:
                for subsub in sub:
                    _differentiate_lines_sub(subsub, cycle, linestyles)
            else:
                _differentiate_lines_sub(sub, cycle, linestyles)
    else:
        _differentiate_lines_sub(ax, cycle, linestyles)


def shorten_years(ax, start_shortening_in=2021):
    """
    Notes
    -----
    * Run plt.draw() first
    * Only run once (not for every subplot) if sharing x axis
    """
    xmin, xmax = ax.get_xlim()
    oldxticklabels = [c._text for c in ax.get_xticklabels()]
    newxticks = []
    newxticklabels = []
    for i, year in enumerate(oldxticklabels):
        if year == '':
            continue
        if (int(year) >= xmin) and (int(year) <= xmax):
            newxticks.append(float(year))
            if int(year) < start_shortening_in:
                newxticklabels.append(year)
            else:
                newxticklabels.append(f"'{year[2:]}")
    ax.set_xticks(newxticks)
    ax.set_xticklabels(newxticklabels)


def annotate(ax, label, x, offset, decimals=0, tail='', **kwargs):
    """
    Annotate a point on a line.

    Inputs
    ------
    * ax: matplotlib axis object
    * label: label of trace to annotate
    * x: x value to annotate
    * offset (tuple): (x,y) label offset in points
    * decimals: decimals to show in annotated value
    * **kwargs: additional keyword arguments for ax.annotate()

    Outputs
    -------
    None
    """
    ### Get the point to plot
    lineindex = [line._label for line in ax.get_lines()].index(label)
    try:
        pointindex = ax.get_lines()[lineindex]._xorig.tolist().index(x)
    except ValueError:
        pointindex = ax.get_lines()[lineindex]._x.tolist().index(x)
    except ValueError:
        raise ValueError('Need to specify an x value in the plotted trace')
    y = ax.get_lines()[lineindex]._yorig[pointindex]
    color = ax.get_lines()[lineindex]._color

    ### Get kwargs
    noteprops = {
        'fontsize':'medium',
        'arrowprops':{'arrowstyle':'-|>', 'color':color},
    }
    for key in kwargs:
        noteprops[key] = kwargs[key]

    ### Annotate it
    if isinstance(decimals, int):
        _decimals = decimals
    else:
        _decimals = 0 if y < 100 else -1

    ax.annotate(
        f'{np.around(y, _decimals):.{max(_decimals, 0)}f}'+tail,
        xy=(x,y),
        textcoords='offset points',
        xytext=offset,
        ha='left' if offset[0] > 0 else 'right' if offset[0] < 0 else 'center',
        va='bottom' if offset[1] > 0 else 'top' if offset[1] < 0 else 'center',
        **noteprops,
    )


def optimize_label_positions(
        ydata, mindistance, ypad=0, extend='above',
        msg=False, debug=False,
    ):
    """Position non-overlapping y labels while minimizing difference from actual values

    Args:
        ydata (array): actual y data values for points to label
        mindistance (numeric): minimum distance between labels, in data units
        ypad (numeric): factor by which to expand the y data bounds to fit the y labels.
            If 0, the label positions will all fall between the minimum and maximum values
            of the data (or the optimization will be infeasible).
            If extend=='above', labels can extend above the data by the specified factor.
            If extend=='below', labels can extend below the data by the specified factor.
            If extend=='both', labels can extend above and below the data by the specified factor.
            For example, if set to -1.5, the highest label can be 25% higher than the
            highest y value and the lowest label can be 25% lower.
        msg (boolean): whether to print optimizer log
        debug (boolean): return full model output as dictionary
    """
    if any([np.isnan(i) for i in ydata]):
        raise ValueError("There are NaN entries in ydata")
    import pulp
    m = pulp.LpProblem("OptimizeLabelPositions", pulp.LpMinimize)

    ### Sets
    index = range(len(ydata))

    ### Parameters
    if ypad != 0 and extend not in ['above','up','below','down','both']:
        raise ValueError(f"extend={extend} but must be in ['above','up','below','down','both']")
    yspan = (max(ydata) - min(ydata)) * (1 + ypad)
    if (ypad == 0) or (extend in ['above','up']):
        ymax = min(ydata) + yspan
        ymin = min(ydata)
    elif extend in ['below','down']:
        ymax = max(ydata)
        ymin = max(ydata) - yspan
    elif extend == 'both':
        ymax = (max(ydata) + min(ydata))/2 + yspan/2
        ymin = (max(ydata) + min(ydata))/2 - yspan/2

    ### Variables
    YLABEL = pulp.LpVariable.dicts(
        'YLABEL', (i for i in index), lowBound=ymin, upBound=ymax, cat='Continuous')
    ERROR_POS = pulp.LpVariable.dicts(
        'ERROR_POS', (i for i in index), lowBound=0, cat='Continuous')
    ERROR_NEG = pulp.LpVariable.dicts(
        'ERROR_NEG', (i for i in index), lowBound=0, cat='Continuous')

    ### Constraints
    for i in index:
        for j in index:
            if i == j:
                continue
            ## ylabel positions can't be within mindistance of each other
            if ydata[i] >= ydata[j]:
                m += (YLABEL[i] - YLABEL[j] >= mindistance)
            else:
                m += (YLABEL[j] - YLABEL[i] >= mindistance)

    ## Define the error terms
    for i in index:
        m += ERROR_POS[i] - ERROR_NEG[i] + YLABEL[i] == ydata[i]

    ### Objective: Minimize the sum of absolute values of errors
    m += pulp.lpSum([ERROR_POS[i] + ERROR_NEG[i] for i in index])

    ### Solve it
    m.solve(solver=pulp.PULP_CBC_CMD(msg=msg))

    if m.status != 1:
        raise ValueError('optimize_label_positions is infeasible; try a smaller mindistance')

    ylabel = [YLABEL[i].varValue for i in index]

    if debug:
        out = {
            'ylabel': ylabel,
            'error_pos': [ERROR_POS[i].varValue for i in index],
            'error_neg': [ERROR_NEG[i].varValue for i in index],
            'm': m,
        }
        return out
    else:
        return ylabel


def label_last(
        dfplot, ax,
        mindistance=None, colors=None, extend='below', line=0.5,
        head=' ', tail='', ha='left', path_effects=None,
        fontsize='medium', xpad=1, decimals=0,
        value=True, name=False,
    ):
    """
    dfplot: dataframe with years as index and cases as columns
    """
    lastyear = dfplot.index[-1]
    if colors is None:
        colors = dict(zip(dfplot.columns, ['C7']*dfplot.shape[1]))

    vals = dfplot.loc[lastyear].sort_values(ascending=False).rename('val').to_frame()

    if mindistance is None:
        mindistance = dfplot.max().max() * 0.033
    _xpad = xpad if ha == 'left' else -xpad

    try:
        vals['ylabel'] = optimize_label_positions(
            vals.values, mindistance=mindistance, ypad=1000, extend=extend,
        )
    except Exception as err:
        print(err)
        vals['ylabel'] = vals.val
        line = False
    for case, row in vals.iterrows():
        ## line
        if line:
            ax.annotate(
                '',
                xy=(lastyear+_xpad/2, row.val),
                xytext=(lastyear+_xpad, row.ylabel),
                arrowprops={
                    'arrowstyle':'-', 'shrinkA':0, 'shrinkB':0,
                    'color':colors[case], 'lw':line},
                annotation_clip=False,
            )
        ## label
        if isinstance(decimals, int):
            _decimals = decimals
        else:
            _decimals = 0 if row.val < 100 else -1
        val = f'{np.around(row.val, _decimals):.{max(_decimals, 0)}f}'
        text = ' '.join([str(val) if value else '', str(case) if name else '']).strip()
        ax.annotate(
            head+text+tail,
            (lastyear+_xpad, row.ylabel), ha=ha, va='center',
            color=colors[case], fontsize=fontsize, annotation_clip=False,
            path_effects=path_effects,
        )


def stackbar(df, ax, colors, width=1, net=True, align='center', bottom=0, x0=0, **netargs):
    """
    Inputs
    -----
    df: [pd.DataFrame] should have x-axis values as the index and component bars as the columns.
    ax: [matplotlib axis]
    colors: [dict] should include an entry for each column in df
    width: [float] bar width
    net: [boolean] indicate whether to plot the summed value for each bar
    align: [str] 'center' or 'edge' (passed to plt.bar)
    **netargs: additional keyword arguments sent to the net-value plot
    """
    for i, (index, row) in enumerate(df.iterrows()):
        ### Separate into positive and negative columns
        negcols = (row < 0).loc[(row < 0) > 0].index
        poscols = [c for c in row.index if c not in negcols]
        dfneg = row[negcols]
        dfpos = row[poscols]
        x = index if isinstance(index, (int,float,pd.Timestamp)) else i
        if isinstance(x, pd.Timestamp) and isinstance(x0, (int, float, str)):
            x0 = pd.Timedelta(x0)
        ### Positive
        if len(dfpos):
            ax.bar(
                x=[x0+x]*len(dfpos),
                height=dfpos.cumsum()[::-1],
                bottom=bottom,
                color=[colors[c] for c in dfpos.index][::-1],
                width=width, align=align,
            )
        ### Negative
        if len(dfneg):
            ax.bar(
                x=[x0+x]*len(dfneg),
                height=dfneg.cumsum()[::-1],
                bottom=bottom,
                color=[colors[c] for c in dfneg.index][::-1],
                width=width, align=align,
            )
        ### Net
        if net:
            netargs = {
                **{'marker':'o','markerfacecolor':'w','markeredgecolor':'k','lw':0.,'color':'k'},
                **netargs
            }
            ax.plot([x0+x], [row.sum()], **netargs)

    return ax


def waterfall(
        data, ax, bottom=None, colors=None,
        width=0.8,
        positive_color='C0', negative_color='C3',
        zero_width=1, zero_style='--', zero_color='k',
        expand_ylim=0.05,
        debug=False,
        xlabel=False, xticklabelrotation=90,
        bararrow=False, bararrowcolor='C7',
        barannotate='', barannotateround=1, barannotatecolor='C7', barannotatesize=10,
    ):
    """
    barannotate: string format for bar annotation. e.g. {:+.1f}, {:,.0f}, etc.
    """
    ### Check inputs
    if bottom:
        assert len(bottom) == len(data)
    if colors:
        assert len(colors) == len(data)
    ### Create working dataframe
    if isinstance(data, list) or isinstance(data, np.ndarray):
        dfplot = pd.Series(data).rename('input').to_frame()
    elif isinstance(data, pd.Series):
        dfplot = pd.DataFrame({'index':data.index, 'input':data.values})

    dfplot['cumsum'] = dfplot['input'].cumsum()

    if not bottom:
        dfplot['bottom_index'] = -1
        dfplot.loc[0,'bottom_index'] = 0
    else:
        dfplot['bottom_index'] = bottom

    ### Get the bottom value according to the index
    dfplot['bottom'] = 0
    for i, row in dfplot.iterrows():
        dfplot.loc[i,'bottom'] = dfplot.loc[i + row['bottom_index'], 'cumsum']
    ## Always starts at 0
    dfplot.loc[0, 'bottom'] = 0

    ### Make the colors
    if colors:
        dfplot['color'] = colors
    else:
        dfplot['color'] = positive_color
        dfplot.loc[dfplot['input'] < 0, 'color'] = negative_color

    ### Get the axis span
    span = dfplot['cumsum'].max() - dfplot['cumsum'].min()

    ### Plot it
    for x, row in dfplot.iterrows():
        ### Bar
        ax.bar(
            x=[x], bottom=[row.bottom], height=[row.input],
            color=row['color'],
        )
        ### Joining lines
        if not x:
            pass
        else:
            ax.plot(
                [x-1-width/2, x+width/2],
                [row.bottom]*2,
                solid_capstyle='butt',
                color='k'
            )
        ### Bar arrow
        if bararrow:
            ax.annotate(
                '', (x, row.bottom+row.input), xytext=(x, row.bottom),
                arrowprops={'arrowstyle':'-|>', 'color':bararrowcolor, 'shrinkA':0, 'shrinkB':0},
            )
        ### Bar annotation
        if barannotate != '':
            extra = span * 0.02 if (row.input > 0) else span * -0.02
            ax.annotate(
                barannotate.format(np.around(row.input, barannotateround)),
                (x, row.bottom+row.input+extra),
                color=(row['color'] if barannotatecolor=='color' else barannotatecolor),
                ha='center', va=('bottom' if (row.input > 0) else 'top'),
                annotation_clip=False, fontsize=barannotatesize,
            )


    ### Formatting
    if zero_width:
        ax.axhline(0, c=zero_color, ls=zero_style, lw=zero_width)

    if expand_ylim:
        ax.set_ylim(
            dfplot['cumsum'].min() - span * expand_ylim,
            dfplot['cumsum'].max() + span * expand_ylim
        )

    if xlabel:
        ax.set_xticks(range(len(dfplot)))
        if (xticklabelrotation == 0) or (xticklabelrotation >= 75):
            ax.set_xticklabels(
                dfplot['index'].values, rotation=xticklabelrotation)
        else:
            ax.set_xticklabels(
                dfplot['index'].values, rotation=xticklabelrotation,
                ha='right', rotation_mode='anchor')

    ### All done
    if debug:
        return dfplot, ax
    else:
        return ax


def waterfall_span(
        df, ax, colors=None, width=0.7, alpha=0.8,
        zero_width=1, zero_style='--', zero_color='k',
        bararrow=True, bararrowcolor='k',
        xticklabelrotation=60,
    ):
    """
    # Inputs
    df [pd.DataFrame]: rows = observations, columns = value categories
    """
    ### Check inputs
    assert isinstance(df, pd.DataFrame)
    arrowprops = {'arrowstyle':'-|>', 'color':bararrowcolor, 'shrinkA':0, 'shrinkB':0}
    xticklabels = df.columns
    ### Make the colors
    if colors:
        pass
    else:
        colors = dict(zip(df.columns, ['C7']*df.shape[1]))

    ###### Plot it
    vmin, vmax = {}, {}
    for x, col in enumerate(df.columns):
        vmin[col], vmax[col] = df.loc[:,:col].sum(axis=1).min(), df.loc[:,:col].sum(axis=1).max()
        ax.bar(
            [x], bottom=[vmin[col]], height=[vmax[col]-vmin[col]],
            color=colors[col], width=width, alpha=0.8,
        )
        ###### Arrows
        if not bararrow:
            continue
        ### First value
        if x == 0:
            ax.annotate(
                '', xy=(x, (vmin[col]+vmax[col])/2),
                xytext=(x,0),
                arrowprops=arrowprops,
            )
        ### Later values start from prior values
        else:
            colprev = df.columns[x-1]
            ## Arrow
            ax.annotate(
                '', xy=(x, (vmin[col]+vmax[col])/2),
                xytext=(x, (vmin[colprev]+vmax[colprev])/2),
                arrowprops=arrowprops,
            )
            ## Linking line from center of previous distribution
            ax.plot(
                [x-1,x], [(vmin[colprev]+vmax[colprev])/2]*2,
                c='k', lw=1, ls=':',
            )

    ###### Formatting
    ax.set_xticks(range(len(xticklabels)))
    if (xticklabelrotation == 0) or (xticklabelrotation >= 75):
        ax.set_xticklabels(
            xticklabels, rotation=xticklabelrotation)
    else:
        ax.set_xticklabels(
            xticklabels, rotation=xticklabelrotation,
            ha='right', rotation_mode='anchor')

    if zero_width:
        ax.axhline(0, c=zero_color, ls=zero_style, lw=zero_width)

    return ax


def plot_region_bars(
        dfzones, dfdata, colors, ax=None,
        valscale=3e3, width=5e4, center=False,
        zeroline=None,
    ):
    """
    Inputs
    ------
    dfzones: gpd.GeoDataFrame of zones or points labeled as (centroid_x, centroid_y)
    dfdata: pd.DataFrame with index matching the index of dfzones and columns matching
        the keys of colors
    colors: dict or pd.Series with keys matching the columns of dfdata
    valscale: [meters / (units of dfdata)]
    width: [meters]
    center: If True, bar center will be at centroid_y; otherwise bar base will be
    zeroline: dictionary of kwargs to pass to ax.plot() for a zero line
    """
    ### Plot it
    for r in dfzones.index:
        if r not in dfdata.index:
            continue
        ### Get coordinates
        x0, bottom = dfzones.loc[r, ['centroid_x', 'centroid_y']]
        ### Scale it
        df = dfdata.loc[r].to_frame().T * valscale
        df.index = [x0]
        if center:
            bottom -= df.sum().sum()/2
        ### Plot it
        stackbar(
            df=df, ax=ax, colors=colors, width=width, net=False, bottom=bottom,
        )
        if isinstance(zeroline, dict):
            ax.plot(
                [x0-width/2, x0+width/2], [bottom]*2,
                **zeroline,
            )


def map_years_months(
        dfzones, dfdata, cmap=cmocean.cm.rain, aggfunc='mean',
        colwidth=1.2, rowheight=1.0, simplify=10000, mapbuffer=1.08,
        vmin=0., vmax=None, outline=0.25, labels=True,
        **colorbarkwargs,
    ):
    """Array of small maps with years as rows and months as columns.
    Index of dfzones must match columns of dfdata.
    """
    import geopandas as gpd
    import shapely
    monthlabels = dict(zip(
        range(1,13),
        ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    ))
    ### Process input data
    dfyearmonth = dfdata.groupby(
        [dfdata.index.year, dfdata.index.month]
    ).agg(aggfunc).rename_axis(['year','month'])
    years = dfyearmonth.index.get_level_values('year').unique()
    months = dfyearmonth.index.get_level_values('month').unique()
    nrows = len(years)
    ncols = len(months)
    _vmin = dfyearmonth.min().min() if vmin is None else vmin
    _vmax = dfyearmonth.max().max() if vmax is None else vmax
    ### Process spatial data
    r_base = dfzones.copy()
    xstep = r_base.dissolve().bounds.loc[0,['minx','maxx']].diff().dropna().squeeze() * mapbuffer
    ystep = -r_base.dissolve().bounds.loc[0,['miny','maxy']].diff().dropna().squeeze() * mapbuffer
    r_base['geometry'] = r_base['geometry'].simplify(simplify)

    outline_base = dfzones.dissolve().copy()
    outline_base['geometry'] = outline_base['geometry'].buffer(0.).simplify(simplify)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(colwidth*ncols, rowheight*nrows))
    for row, year in enumerate(years):
        for col, month in enumerate(months):
            if outline:
                _outline = outline_base.copy()
                _outline.geometry = gpd.GeoSeries([
                    shapely.affinity.translate(outline_base.loc[r,'geometry'], col*xstep, row*ystep)
                    for r in _outline.index
                ]).values
                _outline.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.25, zorder=1e6)
            ## Data
            dfplot = r_base.copy()
            dfplot['data'] = dfyearmonth.loc[(year,month)]
            dfplot.geometry = gpd.GeoSeries([
                shapely.affinity.translate(r_base.loc[r,'geometry'], col*xstep, row*ystep)
                for r in dfplot.index
            ]).values
            dfplot.plot(ax=ax, column='data', lw=0, cmap=cmap, vmin=_vmin, vmax=_vmax)
            ## Formatting
            if labels:
                if col == 0:
                    ax.annotate(
                        year, (-xstep*0.55, row*ystep), ha='right', va='center',
                        fontsize=12, weight='bold',
                    )
                if row == 0:
                    ax.annotate(
                        monthlabels[month], (col*xstep, -ystep*0.45), ha='center', va='bottom',
                        fontsize=12, weight='bold',
                    )
    ## Colorbar
    colorbarkwargs = {
        **{
            'nbins': 101,
            'cbarleft': 1.025,
            'cbarheight': 0.7,
            'cbarbottom': 0.08,
            'cbarwidth': 0.02,
            'histratio': 2,
        },
        **colorbarkwargs,
    }
    addcolorbarhist(
        f=f, ax0=ax, data=dfyearmonth.stack(), cmap=cmap, vmin=_vmin, vmax=_vmax,
        **colorbarkwargs,
    )
    ax.axis('off')
    return f, ax


def plot_segmented_arrow(
        ax,
        reversefrac=0.4, forwardfrac=0.3,
        reversewidth=1e5, forwardwidth=2e5, midwidth=3e5,
        reversecolor='C3', forwardcolor='C0', midcolor='0.7',
        startx=-3e5, endx=3e5,
        starty=1e5, endy=-2e5,
        alpha=1, zorder=2e6,
        headlengthfrac=0.25, headwidthfrac=1,
        label='', labelweight='bold', labelfontsize=12,
        labelborderlw=2.0, labelborderalpha=0.7,
    ):
    """Plot a three-segment arrow (usually on a map)
    Examples inputs:
        label=f"←{75.3257:.0f}%→",
    """
    ### Check inputs
    if np.around(reversefrac + forwardfrac, -3) > 1:
        raise ValueError(f"reversefrac + forwardfrac = {reversefrac + forwardfrac}")

    ### Calculate intermediate values
    delx = endx - startx
    dely = endy - starty
    hypotenuse = (delx**2 + dely**2)**0.5
    midx = (startx + endx) / 2
    midy = (starty + endy) / 2
    anglerad = np.arctan((endy - starty) / (endx - startx))
    angle = anglerad * 180 / np.pi
    midfrac = np.around(1 - reversefrac - forwardfrac, -3)

    tailxforward = endx - delx * forwardfrac
    tailyforward = endy - dely * forwardfrac
    lenxforward = delx * forwardfrac
    lenyforward = dely * forwardfrac

    tailxreverse = startx + delx * reversefrac
    tailyreverse = starty + dely * reversefrac
    lenxreverse = delx * reversefrac
    lenyreverse = dely * reversefrac

    ### Draw it
    ## Forward
    arrow = mpl.patches.FancyArrow(
        tailxforward, tailyforward, lenxforward, lenyforward,
        width=forwardwidth,
        length_includes_head=True,
        head_width=forwardwidth*headwidthfrac,
        head_length=hypotenuse*forwardfrac*headlengthfrac,
        alpha=alpha,
        color=forwardcolor, lw=0,
        zorder=zorder,
        clip_on=False,
    )
    ax.add_patch(arrow)

    ## Reverse
    arrow = mpl.patches.FancyArrow(
        tailxreverse, tailyreverse, -lenxreverse, -lenyreverse,
        width=reversewidth,
        length_includes_head=True,
        head_width=reversewidth*headwidthfrac,
        head_length=hypotenuse*reversefrac*headlengthfrac,
        alpha=alpha,
        color=reversecolor, lw=0,
        zorder=zorder,
        clip_on=False,
    )
    ax.add_patch(arrow)

    ## Middle
    if midwidth and (midfrac > 0):
        arrow = mpl.patches.FancyArrow(
            tailxreverse, tailyreverse,
            (tailxforward - tailxreverse),
            (tailyforward - tailyreverse),
            width=midwidth,
            length_includes_head=True,
            head_width=midwidth,
            head_length=0,
            alpha=alpha,
            color=midcolor, lw=0,
            zorder=zorder,
            clip_on=False,
        )
        ax.add_patch(arrow)

    ## Label
    if len(label):
        ax.annotate(
            label,
            (midx, midy), rotation=angle,
            ha='center', va='center',
            zorder=1e7, weight=labelweight, fontsize=labelfontsize,
            path_effects=[pe.withStroke(
                linewidth=labelborderlw, foreground='w', alpha=labelborderalpha)],
        )


def wraptext(text, width, fontsize=14):
    """
    Inputs
    width: Maximum text length in inches
    """
    numchars = int(np.around(width / fontsize * 90, 0))
    numlines = len(text) // numchars + bool(len(text) % numchars)
    outlist = [text[i*numchars:(i+1)*numchars] for i in range(numlines)]
    out = '\n'.join(outlist)
    return out
