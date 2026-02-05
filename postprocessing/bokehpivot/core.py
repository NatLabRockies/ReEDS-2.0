'''
Pivot chart maker core functionality and csv, gdx applications

'''
from __future__ import division
import os
import sys
import traceback
import shutil
import re
import math
import json
import numpy as np
import pandas as pd
import collections
import pathlib
import bokeh as bk
import bokeh.io as bio
import bokeh.layouts as bl
import bokeh.models as bm
import bokeh.models.widgets as bmw
import bokeh.models.sources as bms
import bokeh.models.tools as bmt
import bokeh.models.callbacks as bmc
import bokeh.plotting as bp
import bokeh.palettes as bpa
import bokeh.resources as br
import bokeh.embed as be
import datetime
import six.moves.urllib.parse as urlp
import subprocess as sp
import jinja2 as ji
import reeds_bokeh as rb
import logging
import requests
from defaults import (DEFAULT_DATA_TYPE, DATA_TYPE_OPTIONS)

#Setup logger
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
if not logger.hasHandlers():
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

#Defaults to configure:
DEFAULT_CUSTOM_SORTS = {} #Keys are column names and values are lists of values in the desired sort order
DEFAULT_CUSTOM_COLORS = {} #Keys are column names and values are dicts that map column values to colors (hex strings)
DATA_TYPE_OPTIONS = DATA_TYPE_OPTIONS + ['CSV']
WIDTH = 300
HEIGHT = 300
PLOT_FONT_SIZE = 10
PLOT_AXIS_LABEL_SIZE = 8
PLOT_LABEL_ORIENTATION = 45
OPACITY = 0.8
X_SCALE = 1
Y_SCALE = 1
CIRCLE_SIZE = 9
BAR_WIDTH = 0.8
LINE_WIDTH = 2
#colors taken from bpa.all_palettes['Category20'][20] and rearranged so that pairs are split
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5']*1000
#here are the colors from bpa.all_palettes['Category20c'][20] and rearranged so that quads are split
COLORS_QUAD = ['#3182bd','#e6550d','#31a354','#756bb1','#636363',
               '#6baed6','#fd8d3c','#74c476','#9e9ac8','#969696',
               '#9ecae1','#fdae6b','#a1d99b','#bcbddc','#bdbdbd',
               '#c6dbef','#fdd0a2','#c7e9c0','#dadaeb','#d9d9d9']*1000
HIST_NUM_BINS = 20
MAP_PALETTE = 'Blues' #See https://bokeh.pydata.org/en/latest/docs/reference/palettes.html for options
C_NORM = "#31AADE"
CHARTTYPES = ['Dot', 'Line', 'Dot-Line', 'Bar', 'Area', 'Area Map', 'Line Map']
STACKEDTYPES = ['Bar', 'Area']
AGGREGATIONS = ['None', 'sum(a)', 'ave(a)', 'sum(a)/sum(b)', 'sum(a*b)/sum(b)', '[sum(a*b)/sum(b)]/[sum(a*c)/sum(c)]']
ADV_BASES = ['Consecutive', 'Total']
MAP_FONT_SIZE = 10
MAP_NUM_BINS = 9
MAP_WIDTH = 500
MAP_OPACITY = 1
MAP_BOUNDARY_WIDTH = 0.1
MAP_LINE_WIDTH = 2
RANGE_OPACITY_MULT = 0.3
RANGE_GLYPH_MAP = {'Line': 'Area', 'Dot': 'Bar', 'Dot-Line': 'Area'}
NCOLS_DEFAULT = 4

#List of widgets that use columns as their selectors
WDG_COL = ['x', 'y', 'x_group', 'series', 'explode', 'explode_group']

#List of widgets that don't use columns as selector and share general widget update function
WDG_NON_COL = ['chart_type', 'range', 'y_agg', 'adv_op', 'explode_grid', 'adv_col_base',
    'adv_op2', 'adv_col_base2', 'adv_op3', 'adv_col_base3', 'plot_title', 'plot_title_size',
    'sort_data', 'width', 'height', 'opacity', 'sync_axes', 'num_cols', 'x_min', 'x_max', 'x_scale',
    'x_title', 'series_limit', 'x_title_size', 'x_major_label_size', 'x_major_label_orientation',
    'y_min', 'y_max', 'y_scale', 'y_title', 'y_title_size', 'y_major_label_size', 'hist_num_bins', 'hist_weight',
    'circle_size', 'bar_width', 'cum_sort', 'line_width', 'range_show_glyphs', 'net_levels', 'bokeh_tools',
    'map_bin', 'map_num', 'map_nozeros', 'map_min', 'map_max', 'map_manual',
    'map_arrows','map_arrow_size','map_arrow_loc','map_width', 'map_font_size', 'map_boundary_width',
    'map_line_width', 'map_opacity', 'map_palette', 'map_palette_2', 'map_palette_break']

#initialize globals dict for variables that are modified within update functions.
#custom_sorts (dict): Keys are column names and values are lists of values in the desired sort order
#custom_colors (dict): Keys are column names and values are dicts that map column values to colors (hex strings)
GL = {'df_source':None, 'df_plots':None, 'columns':None, 'data_source_wdg':None, 'variant_wdg':{},
      'widgets':None, 'wdg_defaults': collections.OrderedDict(), 'controls': None, 'plots':None, 'custom_sorts': DEFAULT_CUSTOM_SORTS,
      'custom_colors': DEFAULT_CUSTOM_COLORS}

#os globals
this_dir_path = os.path.dirname(os.path.realpath(__file__))
out_path = this_dir_path + '/out'

#Add styles.css text for use in layouts
DESCRIPTION_CSS = bm.InlineStyleSheet(css='''
    :host{
        font-size: 90%;
    }
''')
WIDGETS_CSS = bm.InlineStyleSheet(css='''
    :host{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        bottom: 0 !important;
        z-index: 10 !important;
        width: 225px !important;
        height: auto !important;
        overflow-y: scroll !important;
        padding: 5px !important;
    }
''')
PLOTS_CSS = bm.InlineStyleSheet(css='''
    :host{
        position: static !important;
        margin-left: 250px !important;
        width: auto !important;
        height: auto !important;
        display: inline-block !important;
        flex-shrink: 1 !important;
    }
''')
DROPDOWN_CSS = bm.InlineStyleSheet(css='''
    button {
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        font-weight: bold !important;
        color: blue !important;
        cursor: pointer !important;
        text-decoration: underline !important;
    }
''')
FILTER_CSS = bm.InlineStyleSheet(css='''
    button {
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        font-weight: bold !important;
        color: purple !important;
        cursor: pointer !important;
        text-decoration: underline !important;
    }
''')
legend_css_text = ('''
    .legend-drop{
        border: 1px solid lightgrey;
        padding: 10px;
    }
    .legend-color{
        width: 20px;
        height: 10px;
        display: inline-block;
        margin-right: 10px
    }

''')

config_css_text = ('''
    .config-display-title{
        font-weight: bold;
        text-decoration: underline;
    }
    .config-display-key{
        font-weight: bold;
    }
''')
def _new_legend_css():
    """Return a fresh InlineStyleSheet for legend blocks to avoid cross-document reuse errors."""
    return bm.InlineStyleSheet(css=legend_css_text)

def _new_config_css():
    """Return a fresh InlineStyleSheet for config blocks to avoid cross-document reuse errors."""
    return bm.InlineStyleSheet(css=config_css_text)

def _get_wdgs_from_classes(wdg, classes):
    """
    Return list of widgets from wdg that have any of the specified css classes.

    `wdg` is the OrderedDict of bokeh model widgets.
    `classes` is a list of css class strings.
    Returns `wdg_targets`, a list of bokeh model widgets from `wdg`

    """
    wdg_targets = []
    cls_set = set(classes)
    for model in wdg.values():
        css = getattr(model, "css_classes", []) or []
        if css and cls_set.intersection(css):
            wdg_targets.append(model)
    return wdg_targets

def attach_dropdown_callbacks(wdg):
    """
    Attach Bokeh callbacks to our '...-dropdown' headings so they
    show/hide their associated widgets.

    `wdg` is the OrderedDict returned by build_data_source_wdg or build_widgets.
    """

    toggle_visibility_wdgname_class_map = {
        'data_dropdown': ['data-drop'],
        'chart_type_dropdown': ['chart-drop'],
        'x_dropdown': ['x-drop'],
        'y_dropdown': ['y-drop'],
        'series_dropdown': ['series-drop'],
        'explode_dropdown': ['explode-drop'],
        'adv_dropdown': ['adv-drop'],
        'adjustments': ['adjust-drop'],
        'map_adjustments': ['map-drop'],
        'auto_update_dropdown': ['update-drop'],
        'download_dropdown': ['download-drop'],
        'legend_dropdown': ['legend-drop'],
        'reeds_vars': ['reeds-vars-drop'],
        'meta': ['meta-drop'],
        'scenario_filter_dropdown': ['scenario-filter-drop'],
        'report_dropdown': ['report-drop'],
        'filters': ['filter-head', 'filters-update'],
    }

    for name, model in wdg.items():
        if name in toggle_visibility_wdgname_class_map:
            # Add general toggle visibility callback
            targets = _get_wdgs_from_classes(wdg, toggle_visibility_wdgname_class_map[name])
            def _toggle_visibility(targets=targets):
                for m in targets:
                    m.visible = not m.visible
            model.on_click(_toggle_visibility)
        if name == 'filters':
            # When 'filters' is clicked, hide the 'filter-drop' classes (in addition to toggling the other widgets)
            filter_drop_targets = _get_wdgs_from_classes(wdg, ['filter-drop'])
            def _hide_filter_drop_targets(filter_drop_targets=filter_drop_targets):
                for m in filter_drop_targets:
                    m.visible = False
            model.on_click(_hide_filter_drop_targets)
        if name.startswith('heading_filter_'):
            # Per-column filter headings toggle their own controls
            filter_name = name.replace('heading_filter_', '')
            column_targets = []
            for prefix in ('filter_sel_all_', 'filter_sel_none_', 'filter_'):
                key = prefix + filter_name
                column_targets.append(wdg[key])
            def _toggle_filter_visibility(column_targets=column_targets):
                for m in column_targets:
                    m.visible = not m.visible
            model.on_click(_toggle_filter_visibility)

def initialize():
    '''
    On initial load, read 'widgets' parameter from URL query string and use to set data source (data_source)
    and widget configuration object (wdg_config). Initialize controls and plots areas of layout, and
    send data to opened browser.
    '''
    logger.info('***Initializing...')
    wdg_config = {}
    args = bio.curdoc().session_context.request.arguments
    wdg_arr = args.get('widgets')
    data_source = ''
    data_type = DEFAULT_DATA_TYPE
    reset_wdg_defaults()
    if wdg_arr is not None:
        wdg_config = json.loads(urlp.unquote(wdg_arr[0].decode('utf-8')))
        if 'data' in wdg_config:
            data_source = str(wdg_config['data'])
        if 'data_type' in wdg_config:
            data_type = str(wdg_config['data_type'])

    #build widgets and plots
    GL['data_source_wdg'] = build_data_source_wdg(data_type, data_source)
    GL['controls'] = bl.column(list(GL['data_source_wdg'].values()), css_classes=['widgets_section'], stylesheets=[WIDGETS_CSS])
    GL['plots'] = bl.column([], css_classes=['plots_section'], stylesheets=[PLOTS_CSS])
    layout = bl.row(GL['controls'], GL['plots'], css_classes=['full_layout'])

    if data_source != '':
        update_data_source(init_load=True, init_config=wdg_config)
        set_wdg_col_options()
        update_plots()

    bio.curdoc().add_root(layout)
    bio.curdoc().title = "Exploding Pivot Chart Maker"
    logger.info('***Done Initializing')

def reset_wdg_defaults():
    '''
    Set global GL['wdg_defaults']
    '''
    GL['wdg_defaults'] = collections.OrderedDict()
    GL['wdg_defaults']['data'] = ''
    GL['wdg_defaults']['data_type'] = DEFAULT_DATA_TYPE


def static_report(data_type, data_source, static_presets, report_path, report_format, html_num, output_dir, auto_open, variant_wdg_config=[]):
    '''
    Build static HTML and excel/csv reports based on specified presets.
    Args:
        data_type (string): Type of data.
        data_source (string): Path to data for which a report will be made
        static_presets (list of dicts): List of presets for which to make report. Each preset has these keys:
            'name' (required): name of preset
            'config' (required): a dict of widget configurations, where keys are keys of GL['widgets'] and values are values of those widgets. See preset_wdg()
            'sheet_name' (optional): If specified, this is used for the excel sheet name for this preset. Must be unique.
            'download_full_source' (optional): If specified, this allows us to download the full data source, without creating a figure/view.
        report_path (string): The path to the report file.
        report_format (string): string that contains 'html', 'excel', 'csv', or a combination of these, specifying which reports to make.
        html_num (string): 'multiple' if we are building separate html reports for each section, and 'one' for one html report with all sections.
        output_dir (string): the directory into which the resulting reports will be saved.
        auto_open (string): either "Yes" to automatically open report files, or "No"
        variant_wdg_config (list of dicts): After data source is set, this allows us to set any other variant_wdg values.
    Returns:
        Nothing: HTML and Excel files are created
    '''
    #build initial widgets and plots globals
    GL['data_source_wdg'] = build_data_source_wdg()
    GL['controls'] = bl.column(list(GL['data_source_wdg'].values()))
    GL['plots'] = bl.column([])
    #Update data source widget with input value
    GL['data_source_wdg']['data_type'].value = data_type
    GL['data_source_wdg']['data'].value = data_source
    #update any variant_wdg
    for vwc in variant_wdg_config:
        if vwc['type'] == 'active':
            GL['widgets'][vwc['name']].active = vwc['val']
        elif vwc['type'] == 'value':
            GL['widgets'][vwc['name']].value = vwc['val']
    time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if os.path.exists(output_dir):
        os.rename(output_dir, output_dir + '-archive-'+time)
    output_dir = output_dir + '/'
    os.makedirs(output_dir)
    fh = logging.FileHandler(output_dir + 'report.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    #copy report file to output_dir
    if report_path != '':
        shutil.copy2(report_path, output_dir)
    #copy csv data_source to output_dir if not a CSV data type.
    if data_type != 'CSV' and data_source.endswith('.csv'):
        shutil.copy2(data_source, output_dir)
    data_sources = data_source.split('|')
    if 'csv' in report_format:
        os.makedirs(output_dir + 'csvs')
    if 'excel' in report_format:
        excel_report_path = output_dir + 'report.xlsx'
        excel_report = pd.ExcelWriter(excel_report_path)
        excel_meta = []
        excel_meta.append('Build date/time: ' + time)
        excel_meta.append('Data Source(s):')
        for ds in data_sources:
            excel_meta.append(ds)
        excel_meta.append('Default Config:')
        for vwc in variant_wdg_config:
            excel_meta.append(vwc['name'] + ': ' + str(vwc['val']))
        pd.Series(excel_meta).to_excel(excel_report, 'meta', index=False, header=False)
    if 'html' in report_format:
        with open(this_dir_path + '/templates/index.html', 'r') as template_file:
            template_string=template_file.read()
        template = ji.Template(template_string)
        resources = br.Resources()
        header = '<h3>Build date/time:</h3><p>' + time + '</p>'
        header += '<h3>Data Source(s):</h3><ul>'
        for ds in data_sources:
            header += '<li>' + ds + '</li>'
        header += '</ul>'
        header += '<h3>Default Config:</h3><ul>'
        for vwc in variant_wdg_config:
            header += '<li>' + vwc['name'] + ': ' + str(vwc['val']) + '</li>'
        header += '</ul>'
        if html_num == 'one':
            header += '<h3>Section Links:</h3><ol>'
            sec_i = 1
            for static_preset in static_presets:
                sheet_name = ' [sheet="' + static_preset['sheet_name'] + '"]' if 'sheet_name' in static_preset else ''
                header += '<li><a href="#section-' + str(sec_i) + '">' + static_preset['name'] + sheet_name + '</a></li>'
                sec_i += 1
            header += '</ol>'
        header_row = bl.row(bmw.Div(text=header, css_classes=['header_section']))
        if html_num == 'one':
            static_plots = []
            static_plots.append(header_row)
        elif html_num == 'multiple':
            contents_str = '<h3>Contents:</h3><ul>'
    #for each preset, set the widgets in preset_wdg(). Gather plots into separate sections of the html report,
    #and gather data into separate sheets of excel report
    sec_i = 1
    vizit_data = []
    for static_preset in static_presets:
        name = static_preset['name']
        try:
            logger.info('***Building report section: ' + name + '...')
            preset = static_preset['config']
            download_full_source = False
            if 'download_full_source' in static_preset and (static_preset['download_full_source'] == True):
                download_full_source = True
            preset_wdg(preset, download_full_source)
            if 'html' in report_format and (download_full_source == False):
                title = bmw.Div(text='<h2 id="section-' + str(sec_i) + '">' + str(sec_i) + '. ' + name + '</h2>')
                legend = bmw.Div(text=GL['widgets']['legend'].text, stylesheets=[_new_legend_css()])
                display_config = bmw.Div(text=GL['widgets']['display_config'].text, stylesheets=[_new_config_css()])
                title_row = bl.row(title)
                content_row = bl.row(GL['plots'].children + [legend] + [display_config])
                if html_num == 'one':
                    static_plots.append(title_row)
                    static_plots.append(content_row)
                elif html_num == 'multiple':
                    html = be.file_html([title_row, content_row], resources=resources, template=template)
                    html_file_name = str(sec_i) + '_' + name
                    html_file_name = re.sub(r'[\\/:"*?<>|]', '-', html_file_name) #replace disallowed file name characters with dash
                    html_path = output_dir + html_file_name + '.html'
                    with open(html_path, 'w') as f:
                        f.write(html)
                    contents_str += '<li><a href="' + html_file_name + '.html">' + str(sec_i) + '. ' + name + '</a></li>'
            if 'html' in report_format:
                #Vizit-related outputs (allowing download_full_source as well)
                vizit_data.append({
                    'sec_i': sec_i,
                    'data': GL['df_source'] if download_full_source else GL['df_plots'],
                    'preset': static_preset
                })
            if 'excel' in report_format:
                sheet_name = static_preset['sheet_name'] if 'sheet_name' in static_preset else str(sec_i) + '_' + name
                sheet_name = re.sub(r"[\\/*\[\]:?]", '-', sheet_name) #replace disallowed sheet name characters with dash
                sheet_name = sheet_name[:31] #excel sheet names can only be 31 characters long
                if download_full_source:
                    GL['df_source'].to_excel(excel_report, sheet_name, index=False)
                else:
                    GL['df_plots'].to_excel(excel_report, sheet_name, index=False)
            if 'csv' in report_format:
                sheet_name = static_preset['sheet_name'] if 'sheet_name' in static_preset else str(sec_i) + '_' + name
                sheet_name = re.sub(r'[\\/:"*?<>|]', '-', sheet_name) #replace disallowed sheet name characters with dash
                if download_full_source:
                    GL['df_source'].to_csv(output_dir + 'csvs/' + sheet_name + '.csv', index=False)
                else:
                    GL['df_plots'].to_csv(output_dir + 'csvs/' + sheet_name + '.csv', index=False)
        except Exception:
            logger.info('***Error in section ' + str(sec_i) + '...\n' + traceback.format_exc())
            if html_num == 'one':
                static_plots.append(bl.row(bmw.Div(text='<h2 id="section-' + str(sec_i) + '" style="color:red;text-decoration:underline">' + str(sec_i) + '. ' + name + '. ERROR!</h2>')))
        sec_i += 1
    if 'excel' in report_format:
        excel_report.close()
    if 'html' in report_format:
        if html_num == 'one':
            html = be.file_html(static_plots, resources=resources, template=template)
            html_path = output_dir + 'report.html'
            with open(html_path, 'w') as f:
                f.write(html)
            if auto_open == 'Yes':
                sp.Popen(os.path.abspath(html_path), shell=True)
        elif html_num == 'multiple':
            contents_str += '</ul>'
            html = '<!DOCTYPE html><html><body>' + header + contents_str + '</body></html>'
            html_path = output_dir + 'contents.html'
            with open(html_path, 'w') as f:
                f.write(html)
            if auto_open == 'Yes':
                sp.Popen(os.path.abspath(html_path), shell=True)
        vizit_report(data_type, data_source, vizit_data, output_dir, auto_open)
    logger.info('***Done building report')

def vizit_report(data_type, data_source, vizit_data, output_dir, auto_open):
    vizit_config = {'fileNames': [], 'globalStyleFile': 'vizit_styles.csv', 'dashboards':[]}
    #map bokehpivot to vizit
    widget_map = {
        'explode': 'explode',
        'x': 'x',
        'y': 'y',
        'series': 'name',
    }
    style_map = {
        'width': 'Plot Width (px)',
        'height': 'Plot Height (px)',
        # 'x_major_label_size': 'X Tick Font Size (pt)',
    }
    chart_type_map = {
        'Dot': 'dot',
        'Line': 'line',
        'Dot-Line': 'line dot',
        'Bar': 'bar',
        'Area': 'bar',
        'Area Map': 'custom region map',
        'Line Map': 'lat/lon/width line map',
    }
    data_dict = {}
    for v in vizit_data:
        if v['data'].empty:
            continue
        v = v.copy() #So I don't edit the input itself
        #Remove Net Level column if it exists
        if v['data'].columns[-1].startswith('Net Level'):
            v['data'].drop(v['data'].columns[-1], axis=1, inplace=True)
        sheet_name = v['preset']['sheet_name'] if 'sheet_name' in v['preset'] else str(v['sec_i']) + '_' + v['preset']['name']
        sheet_name = re.sub(r'[\\/:"*?<>|]', '-', sheet_name) #replace disallowed sheet name characters with dash
        vizit_config['fileNames'].append(f'{sheet_name}.csv')
        if 'download_full_source' not in v['preset']:
            if 'chart_type' not in v['preset']['config']:
                v['preset']['config']['chart_type'] = 'Dot'
            trace_config = {
                'dataSource': f'{sheet_name}.csv',
                'type': chart_type_map[v['preset']['config']['chart_type']],
                'agg': 'sum',
            }
            style_config = {}
            for w in widget_map:
                if w in v['preset']['config']:
                    trace_config[widget_map[w]] = v['preset']['config'][w]
            for s in style_map:
                if s in v['preset']['config']:
                    style_config[style_map[s]] = v['preset']['config'][s]
            #vizit doesn't support 'explode_group', so make a new concatenated column and set 'explode' to that
            if 'explode_group' in v['preset']['config'] and v['preset']['config']['explode_group'] != 'None':
                new_col = v['preset']['config']['explode'] + ' - ' + v['preset']['config']['explode_group']
                cur_cols = v['data'].columns.tolist()
                v['data'][new_col] = (
                    v['data'][v['preset']['config']['explode']].astype(str) + ' - ' +
                    v['data'][v['preset']['config']['explode_group']].astype(str)
                )
                #Put new_col at the beginning
                v['data'] = v['data'][[new_col] + cur_cols].copy()
                trace_config['explode'] = new_col
            if v['preset']['config']['chart_type'] == 'Area Map':
                reg = v['preset']['config']['x']
                if reg == 'rb':
                    geojson = 'https://raw.githubusercontent.com/mmowers/vizitfiles/main/US_PCA.json'
                    featureidkey = 'properties.rb'
                elif reg == 'st':
                    geojson = 'https://raw.githubusercontent.com/mmowers/vizitfiles/main/us-states.json'
                    featureidkey = 'properties.code'
                #Replace 'y' key with 'z', and replace 'x' with 'locations'
                trace_config['z'] = trace_config.pop('y')
                trace_config['locations'] = trace_config.pop('x')
                trace_config['geojson'] = geojson
                trace_config['geojsonboundaries'] = geojson
                trace_config['featureidkey'] = featureidkey
                style_config['Map Zoom'] = '6'
                style_config['Map Center Latitude'] = '40'
                style_config['Map Center Longitude'] = '-96'
                style_config['Colorscale (region)'] = 'Reds'
            if 'sync_axes' not in v['preset']['config'] or v['preset']['config']['sync_axes'] == 'Yes':
                if v['preset']['config']['chart_type'] == 'Area Map':
                    style_config['Colorscale Min (region)'] = v['data'][trace_config['z']].min()
                    style_config['Colorscale Max (region)'] = v['data'][trace_config['z']].max()
                else:
                    val_col = trace_config['y']
                    if v['preset']['config']['chart_type'] in STACKEDTYPES and 'series' in v['preset']['config']:
                        #sum across series for y_min and y_max
                        ser_col = v['preset']['config']['series']
                        df_pos = v['data'][v['data'][val_col] > 0].copy()
                        df_neg = v['data'][v['data'][val_col] < 0].copy()
                        df_pos = df_pos.drop(columns=ser_col)
                        df_neg = df_neg.drop(columns=ser_col)
                        groupby_cols = [c for c in df_pos.columns if c != val_col]
                        df_pos = df_pos.groupby(groupby_cols, as_index=False)[val_col].sum()
                        df_neg = df_neg.groupby(groupby_cols, as_index=False)[val_col].sum()
                        y_min = df_neg[val_col].min() if df_neg[val_col].min() < 0 else 0
                        y_max = df_pos[val_col].max() if df_pos[val_col].max() > 0 else 0
                    else:
                        y_min = v['data'][val_col].min() if v['data'][val_col].min() < 0 else 0
                        y_max = v['data'][val_col].max() if v['data'][val_col].max() > 0 else 0
                    style_config['Y Min'] = y_min
                    style_config['Y Max'] = y_max
            dashboard = {'title': v['preset']['name'], 'charts':[{'traces':[trace_config], 'style':style_config}]}
            vizit_config['dashboards'].append(dashboard)
        #Add the data itself (even if we're downloading the full source, so we can make charts with the full data)
        data_dict[f'{sheet_name}.csv'] = v['data'].to_dict(orient='list')

    bpStyleDir = f'{this_dir_path}/in/reeds2'
    ls_df = []
    #Read in styles from bokehpivot
    for f in os.listdir(bpStyleDir):
        if f.endswith('_style.csv'):
            df = pd.read_csv(os.path.join(bpStyleDir,f))
            df['column_name'] = f.replace('_style.csv','')
            df = df.rename(columns={'order':'column_value'})
            ls_df.append(df)
    df_style = pd.concat(ls_df, ignore_index=True)
    df_style = df_style[['column_name','column_value','color']].copy()
    #Add styles from scenarios.csv if applicable
    if data_type != 'CSV' and data_source.endswith('.csv'):
        df_scen = pd.read_csv(data_source)
        df_scen['column_name'] = 'scenario'
        df_scen = df_scen.rename(columns={'name':'column_value'})
        cols = [c for c in ['column_name','column_value','color'] if c in df_scen.columns]
        df_scen = df_scen[cols].copy()
        df_style = pd.concat([df_style, df_scen],sort=False,ignore_index=True)
    data_dict['vizit_styles.csv'] = df_style.to_dict(orient='list')
    vizit_config['fileNames'].append('vizit_styles.csv')

    vizit_commit = '7011d363e40386264bedb3155629729b225fd22e'
    vizit_url = f'https://raw.githubusercontent.com/mmowers/vizit/{vizit_commit}/index.html'
    f_out_str = requests.get(vizit_url).text
    data_str = json.dumps(data_dict, separators=(',',':'))
    config_str = json.dumps(vizit_config, separators=(',',':'))
    f_out_str = re.sub('let config_load = .*;\n', f'let config_load = {config_str};\n', f_out_str, 1)
    f_out_str = re.sub('let rawData = .*;\n', f'let rawData = {data_str};\n', f_out_str, 1)
    with open(f'{output_dir}report_vizit.html', 'w') as f_out:
        f_out.write(f_out_str)
    if auto_open == 'Yes':
        sp.Popen(os.path.abspath(f'{output_dir}report_vizit.html'), shell=True)

def preset_wdg(preset, download_full_source=False):
    '''
    Reset widgets and then set them to that specified in input preset
    Args:
        preset (dict): keys are widget names, and values are the desired widget values. Filters are entered as a list of labels under the 'filter' key.
    Returns:
        Nothing: widget values are set.
    '''
    #First set all wdg_variant values, if they exist, in order that they appear in wdg_variant, an ordered dict.
    variant_presets = [key for key in list(GL['variant_wdg'].keys()) if key in preset]
    for key in variant_presets:
        if isinstance(GL['widgets'][key], bmw.groups.AbstractGroup):
            GL['widgets'][key].active = [GL['widgets'][key].labels.index(i) for i in preset[key]]
        elif isinstance(GL['widgets'][key], bmw.inputs.InputWidget):
            GL['widgets'][key].value = preset[key]
    if download_full_source:
        return
    #these variables are set after the variant_wdg presets because otherwise they diverge from the globals
    wdg = GL['widgets']
    wdg_variant = GL['variant_wdg']
    wdg_defaults = GL['wdg_defaults']
    #Now set x to none to prevent chart rerender
    wdg['x'].value = 'None'
    #gather widgets to reset
    wdg_resets = [i for i in wdg_defaults if i not in list(wdg_variant.keys())+['x', 'data', 'data_type', 'render_plots', 'auto_update']]
    #reset widgets if they are not default
    for key in wdg_resets:
        if isinstance(wdg[key], bmw.groups.AbstractGroup) and wdg[key].active != wdg_defaults[key]:
            wdg[key].active = wdg_defaults[key]
        elif isinstance(wdg[key], bmw.inputs.InputWidget) and wdg[key].value != wdg_defaults[key]:
            wdg[key].value = wdg_defaults[key]
    #set all presets except x and filter, in order that they appear in wdg, an ordered dict.
    #Filters are handled separately, after that. x will be set at end, triggering render of chart.
    common_presets = [key for key in list(wdg.keys()) if key in preset and key not in list(wdg_variant.keys())+['x', 'filter']]
    for key in common_presets:
        if isinstance(wdg[key], bmw.groups.AbstractGroup):
            wdg[key].active = [wdg[key].labels.index(i) for i in preset[key]]
        elif isinstance(wdg[key], bmw.inputs.InputWidget):
            wdg[key].value = preset[key]
    #filters are handled separately. We must deal with the active arrays of each filter
    if 'filter' in preset:
        for fil in preset['filter']:
            preset_filter = preset['filter'][fil]
            #find index of associated filter:
            for j, col in enumerate(GL['columns']['filterable']):
                if col == fil:
                    #get filter widget associated with found index
                    wdg_fil = wdg['filter_'+str(j)]
                    #build the new_active list, starting with zeros
                    #for each label given in the preset, set corresponding active to 1
                    if isinstance(preset_filter, str):
                        if preset_filter == 'last':
                            new_active = [len(wdg_fil.labels) - 1]
                    elif isinstance(preset_filter, dict):
                        new_active = list(range(len(wdg_fil.labels)))
                        start = 0 #Initiatlization of beginning index
                        end = len(wdg_fil.labels) - 1 #Initialization of final index
                        if 'start' in preset_filter:
                            #If preset_filter['start'] is a number, find the index of the smallest number that is greater than or equal to it
                            if isinstance(preset_filter['start'], (int, float)):
                                start = min([i for i in range(len(wdg_fil.labels)) if float(wdg_fil.labels[i]) >= preset_filter['start']])
                            else:
                                start = wdg_fil.labels.index(str(preset_filter['start']))
                        if 'end' in preset_filter:
                            if isinstance(preset_filter['end'], (int, float)):
                                end = max([i for i in range(len(wdg_fil.labels)) if float(wdg_fil.labels[i]) <= preset_filter['end']])
                            else:
                                end = wdg_fil.labels.index(str(preset_filter['end']))
                        new_active = list(range(start, end+1))
                        if 'exclude' in preset_filter:
                            new_active = [n for n in new_active if wdg_fil.labels[n] not in preset_filter['exclude']]
                    else: #we are using a list of labels
                        new_active = []
                        for lab in preset_filter:
                            if str(lab) in wdg_fil.labels:
                                index = wdg_fil.labels.index(str(lab))
                                new_active.append(index)
                    wdg_fil.active = new_active
                    break
    #finally, set x, which will trigger the data and chart updates.
    wdg['x'].value = preset['x']

def build_data_source_wdg(data_type=DEFAULT_DATA_TYPE, data_source=''):
    '''
    Return the initial data source widget, prefilled with an input data_source
    Args:
        data_type (string): 
        data_source (string): Path to data source
    Returns:
        wdg (ordered dict): ordered dictionary of bokeh.models.widgets (in this case only one) for data source.
    '''
    wdg = collections.OrderedDict()
    wdg['readme'] = bmw.Div(text='<a href="https://github.nrel.gov/ReEDS/bokehpivot" target="_blank">README</a>')
    wdg['data_dropdown'] = bmw.Button(label='Data Source (required)', css_classes=['data-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['data_type'] = bmw.Select(title='Type', value=data_type, options=DATA_TYPE_OPTIONS, css_classes=['wdgkey-data-type', 'data-drop'])
    wdg['data'] = bmw.TextInput(title='Path', value=data_source, css_classes=['wdgkey-data', 'data-drop'])
    wdg['data_type'].on_change('value', update_data_type)
    wdg['data'].on_change('value', update_data)

    # Attach dropdown behavior for Data Source header
    attach_dropdown_callbacks(wdg)

    return wdg

def get_df_csv(data_source):
    '''
    Read csv(s) into a pandas dataframe, and determine which columns of the dataframe
    are discrete (strings), continuous (numbers), able to be filtered (aka filterable),
    and able to be used as a series (aka seriesable). NA values are filled based on the type of column,
    and the dataframe and columns are returned.

    Args:
        data_source (string): Path to csv file or directory containing csv files with the same column structure

    Returns:
        df_source (pandas dataframe): A dataframe of the source, with filled NA values.
        cols (dict): Keys are categories of columns of df_source, and values are a list of columns of that category.
    '''

    logger.info('***Fetching csv(s)...')
    dfs = []
    sources = data_source.split('|')
    for src in sources:
        src = src.strip()
        if not os.path.exists(src):
            raise FileNotFoundError(f"The specified path does not exist: {src}")
        if os.path.isdir(src):
            #if this is a directory, get all csv within it, assuming they are structured the same way, and add a column for filename
            for file in os.listdir(src):
                if file.endswith(".csv"):
                    filepath = os.path.join(src,file)
                    df = pd.read_csv(filepath, low_memory=False)
                    filename = os.path.splitext(file)[0]
                    df['filename'] = filename
                    dfs.append(df)
        else:
            #This is a csv file, or pd.read_csv will show error if it isn't
            df = pd.read_csv(src, low_memory=False)
            if len(sources) > 1:
                filename = os.path.splitext(os.path.basename(src))[0]
                df['filename'] = filename
            dfs.append(df)
    df_source = pd.concat(dfs,sort=False,ignore_index=True)
    cols = {}
    cols['all'] = df_source.columns.values.tolist()
    cols['discrete'] = [x for x in cols['all'] if df_source[x].dtype == object]
    cols['continuous'] = [x for x in cols['all'] if x not in cols['discrete']]
    cols['x-axis'] = cols['all']
    cols['y-axis'] = cols['continuous']
    cols['filterable'] = cols['discrete']+[x for x in cols['continuous'] if len(df_source[x].unique()) < 500 and df_source[x].dtype != float]
    cols['seriesable'] = cols['filterable']
    df_source[cols['discrete']] = df_source[cols['discrete']].fillna('{BLANK}')
    df_source[cols['continuous']] = df_source[cols['continuous']].fillna(0)
    logger.info('***Done fetching csv(s).')
    return (df_source, cols)

def get_wdg_csv():
    '''
    Create report widgets for csv file.

    Returns:
        topwdg (ordered dict): Dictionary of bokeh.model.widgets.
    '''
    topwdg = collections.OrderedDict()
    topwdg['report_dropdown'] = bmw.Button(label='Build Report', css_classes=['report-dropdown'], stylesheets=[DROPDOWN_CSS])
    topwdg['report_custom'] = bmw.TextInput(title='Enter path to report file', value='', css_classes=['report-drop'], visible=False)
    topwdg['report_format'] = bmw.TextInput(title='Enter type(s) of report (html,excel,csv)', value='html,excel', css_classes=['report-drop'], visible=False)
    topwdg['report_debug'] = bmw.Select(title='Debug Mode', value='No', options=['Yes','No'], css_classes=['report-drop'], visible=False)
    topwdg['report_build'] = bmw.Button(label='Build Report', button_type='success', css_classes=['report-drop'], visible=False)
    topwdg['report_build_separate'] = bmw.Button(label='Build Separate Reports', button_type='success', css_classes=['report-drop'], visible=False)
    topwdg['report_build'].on_click(build_report)
    topwdg['report_build_separate'].on_click(build_report_separate)
    return topwdg

def build_report(html_num='one'):
    '''
    Build the chosen report.
    Args:
        html_num (string): 'multiple' if we are building separate html reports for each section, and 'one' for one html report with all sections.
    '''
    data_type = '"CSV"'
    report_path = GL['widgets']['report_custom'].value
    report_path = report_path.replace('"', '')
    report_path = '"' + report_path + '"'
    report_format = '"' + GL['widgets']['report_format'].value + '"'
    time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_dir = '"' + out_path + '/report-' + time + '"'
    data_source = '"' + GL['widgets']['data'].value.replace('"', '') + '"'
    if html_num == 'one':
        auto_open = '"Yes"'
    else:
        auto_open = '"No"'
    start_str = 'start python'
    if GL['widgets']['report_debug'].value == 'Yes':
        start_str = 'start cmd /K python -m pdb '
    sp.call(start_str + ' "' + this_dir_path + '/reports/interface_report.py" ' + data_type + ' ' + data_source + ' ' + report_path + ' ' + report_format + ' "' + html_num + '" ' + output_dir + ' ' + auto_open, shell=True)

def build_report_separate():
    '''
    Build the report with separate html files for each section of the report.
    '''
    build_report(html_num='multiple')

def get_wdg_gdx(data_source):
    '''
    Create a parameter select widget and return it.

    Args:
        data_source (string): Path to gdx file.

    Returns:
        topwdg (ordered dict): Dictionary of bokeh.model.widgets.
    '''
    return #need to implement!

def build_widgets(df_source, cols, init_load=False, init_config={}, wdg_defaults={}):
    '''
    Use a dataframe and its columns to set widget options. Widget values may
    be set by URL parameters via init_config.

    Args:
        df_source (pandas dataframe): Dataframe of the csv source.
        cols (dict): Keys are categories of columns of df_source, and values are a list of columns of that category.
        init_load (boolean, optional): If this is the initial page load, then this will be True, else False.
        init_config (dict): Initial widget configuration passed via URL.
        wdg_defaults (dict): Keys are widget names and values are the default values of the widgets.

    Returns:
        wdg (ordered dict): Dictionary of bokeh.model.widgets.
    '''
    #Add widgets
    logger.info('***Build main widgets...')

    wdg = collections.OrderedDict()
    wdg['chart_type_dropdown'] = bmw.Button(label='Chart', css_classes=['chart-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['chart_type'] = bmw.Select(title='Chart Type', value='Dot', options=CHARTTYPES, css_classes=['wdgkey-chart_type', 'chart-drop'], visible=False)
    wdg['range'] = bmw.Select(title='Add Ranges (Line and Dot only)', value='No', options=['No', 'Within Series', 'Between Series', 'Boxplot'], css_classes=['wdgkey-range', 'chart-drop'], visible=False)
    wdg['x_dropdown'] = bmw.Button(label='X-Axis (required)', css_classes=['x-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['x'] = bmw.Select(title='X-Axis (required)', value='None', options=['None'] + cols['x-axis'] + ['histogram_x'], css_classes=['wdgkey-x', 'x-drop'], visible=False)
    wdg['x_group'] = bmw.Select(title='Group X-Axis By', value='None', options=['None'] + cols['seriesable'], css_classes=['wdgkey-x_group', 'x-drop'], visible=False)
    wdg['y_dropdown'] = bmw.Button(label='Y-Axis (required)', css_classes=['y-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['y'] = bmw.Select(title='a (required)', value='None', options=['None'] + cols['y-axis'], css_classes=['wdgkey-y', 'y-drop'], visible=False)
    wdg['y_b'] = bmw.Select(title='b (optional, no update)', value='None', options=['None'] + cols['y-axis'], css_classes=['wdgkey-y_b', 'y-drop'], visible=False)
    wdg['y_c'] = bmw.Select(title='c (optional, no update)', value='None', options=['None'] + cols['y-axis'], css_classes=['wdgkey-y_c', 'y-drop'], visible=False)
    wdg['y_agg'] = bmw.Select(title='Y-Axis Aggregation', value='sum(a)', options=AGGREGATIONS, css_classes=['wdgkey-y_agg', 'y-drop'], visible=False)
    wdg['series_dropdown'] = bmw.Button(label='Series', css_classes=['series-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['series'] = bmw.Select(title='Separate Series By', value='None', options=['None'] + cols['seriesable'],
        css_classes=['wdgkey-series', 'series-drop'], visible=False)
    wdg['series_limit'] = bmw.TextInput(title='Number of series to show', value='All', css_classes=['wdgkey-series', 'series-drop'], visible=False)
    wdg['explode_dropdown'] = bmw.Button(label='Explode', css_classes=['explode-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['explode'] = bmw.Select(title='Explode By', value='None', options=['None'] + cols['seriesable'], css_classes=['wdgkey-explode', 'explode-drop'], visible=False)
    wdg['explode_group'] = bmw.Select(title='Group Exploded Charts By', value='None', options=['None'] + cols['seriesable'],
        css_classes=['wdgkey-explode_group', 'explode-drop'], visible=False)
    wdg['explode_grid'] = bmw.Select(title='Make Grid Plot', value='No', options=['Yes','No'], css_classes=['wdgkey-explode_grid', 'explode-drop'], visible=False)
    wdg['adv_dropdown'] = bmw.Button(label='Operations', css_classes=['adv-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['adv_op'] = bmw.Select(title='First Operation', value='None', options=['None', 'Difference', 'Ratio'], css_classes=['wdgkey-adv_op', 'adv-drop'], visible=False)
    wdg['adv_col'] = bmw.Select(title='Operate Across', value='None', options=['None'] + cols['all'], css_classes=['wdgkey-adv_col', 'adv-drop'], visible=False)
    wdg['adv_col_base'] = bmw.Select(title='Base', value='None', options=['None'], css_classes=['wdgkey-adv_col_base', 'adv-drop'], visible=False)
    wdg['adv_op2'] = bmw.Select(title='Second Operation', value='None', options=['None', 'Difference', 'Ratio'], css_classes=['wdgkey-adv_op', 'adv-drop'], visible=False)
    wdg['adv_col2'] = bmw.Select(title='Operate Across', value='None', options=['None'] + cols['all'], css_classes=['wdgkey-adv_col', 'adv-drop'], visible=False)
    wdg['adv_col_base2'] = bmw.Select(title='Base', value='None', options=['None'], css_classes=['wdgkey-adv_col_base', 'adv-drop'], visible=False)
    wdg['adv_op3'] = bmw.Select(title='Third Operation', value='None', options=['None', 'Difference', 'Ratio'], css_classes=['wdgkey-adv_op', 'adv-drop'], visible=False)
    wdg['adv_col3'] = bmw.Select(title='Operate Across', value='None', options=['None'] + cols['all'], css_classes=['wdgkey-adv_col', 'adv-drop'], visible=False)
    wdg['adv_col_base3'] = bmw.Select(title='Base', value='None', options=['None'], css_classes=['wdgkey-adv_col_base', 'adv-drop'], visible=False)
    wdg['filters'] = bmw.Button(label='Filters', css_classes=['filters-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['filters_update'] = bmw.Button(label='Update Filters', button_type='success', css_classes=['filters-update'], visible=False)
    for j, col in enumerate(cols['filterable']):
        val_list = [str(i) for i in sorted(df_source[col].unique().tolist())]
        wdg['heading_filter_'+str(j)] = bmw.Button(label=col, css_classes=['filter-head'], visible=False, stylesheets=[FILTER_CSS])
        wdg['filter_sel_all_'+str(j)] = bmw.Button(label='Select All', button_type='success', css_classes=['filter-drop'], visible=False)
        wdg['filter_sel_none_'+str(j)] = bmw.Button(label='Select None', button_type='success', css_classes=['filter-drop'], visible=False)
        wdg['filter_'+str(j)] = bmw.CheckboxGroup(labels=val_list, active=list(range(len(val_list))), css_classes=['wdgkey-filter_'+str(j), 'filter-drop'], visible=False)
        select_all_callback = bmc.CustomJS(args=dict(cb_wdg_fil=wdg['filter_'+str(j)]), code="""
            cb_wdg_fil.active = Array.from(Array(cb_wdg_fil.labels.length).keys())
            cb_wdg_fil.change.emit();
        """)
        select_none_callback = bmc.CustomJS(args=dict(cb_wdg_fil=wdg['filter_'+str(j)]), code="""
            cb_wdg_fil.active = []
            cb_wdg_fil.change.emit();
        """)
        wdg['filter_sel_all_'+str(j)].js_on_event(bk.events.ButtonClick, select_all_callback)
        wdg['filter_sel_none_'+str(j)].js_on_event(bk.events.ButtonClick, select_none_callback)
    wdg['adjustments'] = bmw.Button(label='Plot Adjustments', css_classes=['adjust-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['width'] = bmw.TextInput(title='Plot Width (px)', value=str(WIDTH), css_classes=['wdgkey-width', 'adjust-drop'], visible=False)
    wdg['height'] = bmw.TextInput(title='Plot Height (px)', value=str(HEIGHT), css_classes=['wdgkey-height', 'adjust-drop'], visible=False)
    wdg['plot_title'] = bmw.TextInput(title='Plot Title', value='', css_classes=['wdgkey-plot_title', 'adjust-drop'], visible=False)
    wdg['plot_title_size'] = bmw.TextInput(title='Plot Title Font Size', value=str(PLOT_FONT_SIZE), css_classes=['wdgkey-plot_title_size', 'adjust-drop'], visible=False)
    wdg['opacity'] = bmw.TextInput(title='Opacity (0-1)', value=str(OPACITY), css_classes=['wdgkey-opacity', 'adjust-drop'], visible=False)
    wdg['sync_axes'] = bmw.Select(title='Sync Axes', value='Yes', options=['Yes', 'No'], css_classes=['adjust-drop'], visible=False)
    wdg['num_cols'] = bmw.TextInput(title='Plots Per Row', value=str(NCOLS_DEFAULT), css_classes=['adjust-drop'], visible=False)
    wdg['x_scale'] = bmw.TextInput(title='X Scale', value=str(X_SCALE), css_classes=['wdgkey-x_scale', 'adjust-drop'], visible=False)
    wdg['x_min'] = bmw.TextInput(title='X Min', value='', css_classes=['wdgkey-x_min', 'adjust-drop'], visible=False)
    wdg['x_max'] = bmw.TextInput(title='X Max', value='', css_classes=['wdgkey-x_max', 'adjust-drop'], visible=False)
    wdg['x_title'] = bmw.TextInput(title='X Title', value='', css_classes=['wdgkey-x_title', 'adjust-drop'], visible=False)
    wdg['x_title_size'] = bmw.TextInput(title='X Title Font Size', value=str(PLOT_FONT_SIZE), css_classes=['wdgkey-x_title_size', 'adjust-drop'], visible=False)
    wdg['x_major_label_size'] = bmw.TextInput(title='X Labels Font Size', value=str(PLOT_AXIS_LABEL_SIZE), css_classes=['wdgkey-x_major_label_size', 'adjust-drop'], visible=False)
    wdg['x_major_label_orientation'] = bmw.TextInput(title='X Labels Degrees', value=str(PLOT_LABEL_ORIENTATION),
        css_classes=['wdgkey-x_major_label_orientation', 'adjust-drop'], visible=False)
    wdg['y_scale'] = bmw.TextInput(title='Y Scale', value=str(Y_SCALE), css_classes=['wdgkey-y_scale', 'adjust-drop'], visible=False)
    wdg['y_min'] = bmw.TextInput(title='Y  Min', value='', css_classes=['wdgkey-y_min', 'adjust-drop'], visible=False)
    wdg['y_max'] = bmw.TextInput(title='Y Max', value='', css_classes=['wdgkey-y_max', 'adjust-drop'], visible=False)
    wdg['y_title'] = bmw.TextInput(title='Y Title', value='', css_classes=['wdgkey-y_title', 'adjust-drop'], visible=False)
    wdg['y_title_size'] = bmw.TextInput(title='Y Title Font Size', value=str(PLOT_FONT_SIZE), css_classes=['wdgkey-y_title_size', 'adjust-drop'], visible=False)
    wdg['y_major_label_size'] = bmw.TextInput(title='Y Labels Font Size', value=str(PLOT_AXIS_LABEL_SIZE), css_classes=['wdgkey-y_major_label_size', 'adjust-drop'], visible=False)
    wdg['circle_size'] = bmw.TextInput(title='Circle Size (Dot Only)', value=str(CIRCLE_SIZE), css_classes=['wdgkey-circle_size', 'adjust-drop'], visible=False)
    wdg['bar_width'] = bmw.TextInput(title='Bar Width (Bar Only)', value=str(BAR_WIDTH), css_classes=['wdgkey-bar_width', 'adjust-drop'], visible=False)
    wdg['bar_width_desc'] = bmw.Div(text='<strong>Flags</strong> <em>w</em>: use csv file for widths, <em>c</em>: convert x axis to quantitative based on widths in csv file', css_classes=['adjust-drop'], stylesheets=[DESCRIPTION_CSS], visible=False)
    wdg['sort_data'] = bmw.Select(title='Sort Data', value='Yes', options=['Yes', 'No'], css_classes=['wdgkey-sort_data', 'adjust-drop'], visible=False)
    wdg['cum_sort'] = bmw.Select(title='Cumulative Sort', value='None', options=['None', 'Ascending', 'Descending'], css_classes=['wdgkey-cum_sort','adjust-drop'], visible=False)
    wdg['hist_num_bins'] = bmw.TextInput(title='Histogram # of bins', value=str(HIST_NUM_BINS), css_classes=['wdgkey-hist_num_bins', 'adjust-drop'], visible=False)
    wdg['hist_weight'] = bmw.Select(title='Weighted Histogram', value='Yes', options=['Yes', 'No'], css_classes=['wdgkey-hist_weight', 'adjust-drop'], visible=False)
    wdg['line_width'] = bmw.TextInput(title='Line Width (Line Only)', value=str(LINE_WIDTH), css_classes=['wdgkey-line_width', 'adjust-drop'], visible=False)
    wdg['range_show_glyphs'] = bmw.Select(title='Show Line/Dot (Range Only)', value='Yes', options=['Yes','No'], css_classes=['wdgkey-range_show_glyphs', 'adjust-drop'], visible=False)
    wdg['net_levels'] = bmw.Select(title='Add Net Levels to Stacked', value='Yes', options=['Yes','No'], css_classes=['wdgkey-net_levels', 'adjust-drop'], visible=False)
    wdg['bokeh_tools'] = bmw.Select(title='Show Bokeh Tools', value='Yes', options=['Yes','No'], css_classes=['wdgkey-bokeh_tools', 'adjust-drop'], visible=False)
    wdg['custom_styles'] = bmw.TextInput(title='Custom Styles CSV', value='', css_classes=['wdgkey-custom_styles', 'adjust-drop'], visible=False)
    wdg['map_adjustments'] = bmw.Button(label='Map Adjustments', css_classes=['map-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['map_bin'] = bmw.Select(title='Bin Type', value='Auto Equal Num', options=['Auto Equal Num', 'Auto Equal Width', 'Manual'], css_classes=['wdgkey-map_bin', 'map-drop'], visible=False)
    wdg['map_num'] = bmw.TextInput(title='# of bins (Auto Only)', value=str(MAP_NUM_BINS), css_classes=['wdgkey-map_num', 'map-drop'], visible=False)
    wdg['map_nozeros'] = bmw.Select(title='Ignore Zeros', value='Yes', options=['Yes', 'No'], css_classes=['wdgkey-map_nozeros', 'map-drop'], visible=False)
    wdg['map_palette'] = bmw.TextInput(title='Map Palette', value=MAP_PALETTE, css_classes=['wdgkey-map_palette', 'map-drop'], visible=False)
    wdg['map_palette_desc'] = bmw.Div(text='See <a href="https://bokeh.pydata.org/en/latest/docs/reference/palettes.html" target="_blank">palette options</a> or all_red, all_blue, all_green, all_gray. Palette must accommodate # of bins', css_classes=['map-drop'], stylesheets=[DESCRIPTION_CSS], visible=False)
    wdg['map_palette_2'] = bmw.TextInput(title='Map Palette 2 (Optional)', value='', css_classes=['wdgkey-map_palette_2', 'map-drop'], visible=False)
    wdg['map_palette_2_desc'] = bmw.Div(text='Bins will be split between palettes.', css_classes=['map-drop'], stylesheets=[DESCRIPTION_CSS], visible=False)
    wdg['map_palette_break'] = bmw.TextInput(title='Dual Palette Breakpoint (Optional)', value='', css_classes=['wdgkey-map_palette_break', 'map-drop'], visible=False)
    wdg['map_palette_break_desc'] = bmw.Div(text='The bin that contains this breakpoint will divide the palettes.', css_classes=['map-drop'], stylesheets=[DESCRIPTION_CSS], visible=False)
    wdg['map_min'] = bmw.TextInput(title='Minimum (Equal Width Only)', value='', css_classes=['wdgkey-map_min', 'map-drop'], visible=False)
    wdg['map_max'] = bmw.TextInput(title='Maximum (Equal Width Only)', value='', css_classes=['wdgkey-map_max', 'map-drop'], visible=False)
    wdg['map_manual'] = bmw.TextInput(title='Manual Breakpoints (Manual Only)', value='', css_classes=['wdgkey-map_manual', 'map-drop'], visible=False)
    wdg['map_manual_desc'] = bmw.Div(text='Comma separated list of values (e.g. -10,0,0.5,6), with one fewer value than # of bins', css_classes=['map-drop'], stylesheets=[DESCRIPTION_CSS], visible=False)
    wdg['map_width'] = bmw.TextInput(title='Map Width (px)', value=str(MAP_WIDTH), css_classes=['wdgkey-map_width', 'map-drop'], visible=False)
    wdg['map_font_size'] = bmw.TextInput(title='Title Font Size', value=str(MAP_FONT_SIZE), css_classes=['wdgkey-map_font_size', 'map-drop'], visible=False)
    wdg['map_boundary_width'] = bmw.TextInput(title='Boundary Line Width', value=str(MAP_BOUNDARY_WIDTH), css_classes=['wdgkey-map_boundary_width', 'map-drop'], visible=False)
    wdg['map_line_width'] = bmw.TextInput(title='Line Width', value=str(MAP_LINE_WIDTH), css_classes=['wdgkey-map_line_width', 'map-drop'], visible=False)
    wdg['map_opacity'] = bmw.TextInput(title='Opacity (0-1)', value=str(MAP_OPACITY), css_classes=['wdgkey-map_opacity', 'map-drop'], visible=False)
    wdg['map_arrows'] = bmw.Select(title='Add Arrows', value='No', options=['Yes','No'], css_classes=['wdgkey-map_arrows', 'map-drop'], visible=False)
    wdg['map_arrow_size'] = bmw.TextInput(title='Arrow Size (px)', value='7', css_classes=['wdgkey-map_arrow_size', 'map-drop'], visible=False)
    wdg['map_arrow_loc'] = bmw.TextInput(title='Arrow Location (0=start, 1=end)', value='0.8', css_classes=['wdgkey-map_arrow_loc', 'map-drop'], visible=False)
    wdg['auto_update_dropdown'] = bmw.Button(label='Auto/Manual Update', css_classes=['update-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['auto_update'] = bmw.Select(title='Auto Update (except filters)', value='Enable', options=['Enable', 'Disable'], css_classes=['update-drop'], visible=False)
    wdg['update'] = bmw.Button(label='Manual Update', button_type='success', css_classes=['update-drop'], visible=False)
    wdg['render_plots'] = bmw.Select(title='Render Plots', value='Yes', options=['Yes', 'No'], css_classes=['update-drop'], visible=False)
    wdg['download_dropdown'] = bmw.Button(label='Download/Export', css_classes=['download-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['download_date'] = bmw.Select(title='Add Date', value='Yes', options=['Yes', 'No'], css_classes=['download-drop'], visible=False)
    wdg['download_prefix'] = bmw.TextInput(title='Prefix', value='', css_classes=['download-drop'], visible=False)
    wdg['download_all'] = bmw.Button(label='All Files of View', button_type='success', css_classes=['download-drop'], visible=False)
    wdg['download_csv'] = bmw.Button(label='CSV of View', button_type='success', css_classes=['download-drop'], visible=False)
    wdg['download_html'] = bmw.Button(label='HTML of View', button_type='success', css_classes=['download-drop'], visible=False)
    wdg['download_url'] = bmw.Button(label='URL of View', button_type='success', css_classes=['download-drop'], visible=False)
    wdg['download_report'] = bmw.Button(label='Python Report of View', button_type='success', css_classes=['download-drop'], visible=False)
    wdg['download_preset'] = bmw.Button(label='Preset of View', button_type='success', css_classes=['download-drop'], visible=False)
    wdg['download_source'] = bmw.Button(label='CSV of Full Data Source', button_type='success', css_classes=['download-drop'], visible=False)
    wdg['legend_dropdown'] = bmw.Button(label='Legend', css_classes=['legend-dropdown'], stylesheets=[DROPDOWN_CSS])
    wdg['legend'] = bmw.Div(text='', css_classes=['legend-drop'], stylesheets=[_new_legend_css()])
    wdg['display_config'] = bmw.Div(text='', css_classes=['display-config'], stylesheets=[_new_config_css()])

    # Attach dropdown behavior for all main sections
    attach_dropdown_callbacks(wdg)

    #save defaults
    save_wdg_defaults(wdg, wdg_defaults)
    #use init_config (from 'widgets' parameter in URL query string) to configure widgets.
    if init_load:
        initialize_wdg(wdg, init_config)

    #Add update functions for widgets
    wdg['filters_update'].on_click(update_plots)
    wdg['update'].on_click(update_plots)
    wdg['download_all'].on_click(download_all)
    wdg['download_csv'].on_click(download_csv)
    wdg['download_html'].on_click(download_html)
    wdg['download_url'].on_click(download_url)
    wdg['download_report'].on_click(download_report)
    wdg['download_preset'].on_click(download_preset)
    wdg['download_source'].on_click(download_source)
    wdg['adv_col'].on_change('value', update_adv_col)
    wdg['adv_col2'].on_change('value', update_adv_col2)
    wdg['adv_col3'].on_change('value', update_adv_col3)
    wdg['custom_styles'].on_change('value', update_custom_styles)
    for name in WDG_COL:
        wdg[name].on_change('value', update_wdg_col)
    for name in WDG_NON_COL:
        wdg[name].on_change('value', update_wdg)
    logger.info('***Done with main widgets.')
    return wdg

def initialize_wdg(wdg, init_config):
    '''
    Set values of wdg based on init_config

    Args:
        wdg (ordered dict): Dictionary of bokeh.model.widgets.
        init_config (dict): Initial widget configuration passed via URL.

    Returns:
        Nothing: wdg is modified
    '''
    for key in init_config:
        if key in wdg:
            if hasattr(wdg[key], 'value'):
                wdg[key].value = str(init_config[key])
            elif hasattr(wdg[key], 'active'):
                wdg[key].active = init_config[key]

def save_wdg_defaults(wdg, wdg_defaults):
    '''
    Save wdg_defaults based on wdg

    Args:
        wdg (ordered dict): Dictionary of bokeh.model.widgets.
        wdg_defaults (dict): Keys are widget names and values are the default values of the widgets.

    Returns:
        Nothing: wdg_defaults is set for applicable keys in wdg
    '''
    for key in wdg:
        if isinstance(wdg[key], bmw.groups.AbstractGroup):
            wdg_defaults[key] = wdg[key].active
        elif isinstance(wdg[key], bmw.inputs.InputWidget):
            wdg_defaults[key] = wdg[key].value

def set_df_plots(df_source, cols, wdg, custom_sorts={}):
    '''
    Apply filters, scaling, aggregation, and sorting to source dataframe, and return the result.

    Args:
        df_source (pandas dataframe): Dataframe of the csv source.
        cols (dict): Keys are categories of columns of df_source, and values are a list of columns of that category.
        wdg (ordered dict): Dictionary of bokeh model widgets.
        custom_sorts (dict): Keys are column names. Values are lists of values in the desired sort order.

    Returns:
        df_plots (pandas dataframe): df_source after having been filtered, scaled, aggregated, and sorted.
    '''
    logger.info('***Filtering, Scaling, Aggregating, Adv Operations, Sorting...')
    startTime = datetime.datetime.now()
    df_plots = df_source.copy()

    #Apply filters
    for j, col in enumerate(cols['filterable']):
        active = [wdg['filter_'+str(j)].labels[i] for i in wdg['filter_'+str(j)].active]
        if col in cols['continuous']:
            active = np.asarray(active)
            active = active.astype(df_plots[col].dtype)
            active = active.tolist()
        df_plots = df_plots[df_plots[col].isin(active)]

    if df_plots.empty:
        return df_plots

    #Limit number of series if indicated
    if wdg['series'].value != 'None' and wdg['series_limit'].value.isdigit():
        df_top = df_plots[[wdg['series'].value, wdg['y'].value]].copy()
        df_top[wdg['y'].value] = df_top[wdg['y'].value].abs()
        df_top = df_top.groupby([wdg['series'].value], sort=False, as_index=False).sum()
        df_top = df_top.sort_values(by=[wdg['y'].value], ascending=False)
        top_series = df_top.head(int(wdg['series_limit'].value))[wdg['series'].value].tolist()
        df_plots.loc[~df_plots[wdg['series'].value].isin(top_series), wdg['series'].value] = 'Other'

    #Apply Aggregation
    if wdg['y'].value in cols['continuous'] and wdg['y_agg'].value != 'None' and wdg['x'].value != 'histogram_x':
        groupby_cols = [wdg['x'].value]
        if wdg['x_group'].value != 'None': 
            groupby_cols = [wdg['x_group'].value] + groupby_cols
        if wdg['series'].value != 'None': 
            groupby_cols = [wdg['series'].value] + groupby_cols
        if wdg['explode'].value != 'None':
            groupby_cols = [wdg['explode'].value] + groupby_cols
        if wdg['explode_group'].value != 'None':
            groupby_cols = [wdg['explode_group'].value] + groupby_cols
        df_grouped = df_plots.groupby(groupby_cols, sort=False)
        df_plots = df_grouped.apply(apply_aggregation, wdg['y_agg'].value, wdg['y'].value, wdg['y_b'].value, wdg['y_c'].value, wdg['range'].value).reset_index()
        #The index of each group's dataframe is added as another column it seems. So we need to remove it:
        df_plots.drop(df_plots.columns[len(groupby_cols)], axis=1, inplace=True)

    #Make histogram
    if wdg['x'].value == 'histogram_x':
        weights = df_plots[wdg['y'].value] if  wdg['hist_weight'].value == 'Yes' else None
        yhist, binedges = np.histogram(df_plots[wdg['y'].value], bins=int(wdg['hist_num_bins'].value), weights=weights)
        groupby_cols = []
        if wdg['series'].value != 'None': 
            groupby_cols = [wdg['series'].value] + groupby_cols
        if wdg['explode'].value != 'None':
            groupby_cols = [wdg['explode'].value] + groupby_cols
        if wdg['explode_group'].value != 'None':
            groupby_cols = [wdg['explode_group'].value] + groupby_cols
        if groupby_cols == []:
            bincenters = np.mean(np.vstack([binedges[0:-1],binedges[1:]]), axis=0)
            df_plots = pd.DataFrame({wdg['x'].value: bincenters, wdg['y'].value: yhist})
        else:
            def group_apply_hist(group, binedges):
                weights = group[wdg['y'].value] if  wdg['hist_weight'].value == 'Yes' else None
                if wdg['sync_axes'].value == 'Yes':
                    yhist, binedges = np.histogram(group[wdg['y'].value], bins=binedges, weights=weights)
                else:
                    yhist, binedges = np.histogram(group[wdg['y'].value], bins=int(wdg['hist_num_bins'].value), weights=weights)
                bincenters = np.mean(np.vstack([binedges[0:-1],binedges[1:]]), axis=0)
                return pd.DataFrame({wdg['x'].value: bincenters, wdg['y'].value: yhist})
            df_grouped = df_plots.groupby(groupby_cols, sort=False)
            df_plots = df_grouped.apply(group_apply_hist, binedges).reset_index()
            df_plots.drop(df_plots.columns[len(groupby_cols)], axis=1, inplace=True)
        groupby_cols += [wdg['x'].value]

    #Check for range chart
    range_cols = []
    if wdg['range'].value == 'Within Series':
        range_cols = ['range_min', 'range_max']

    #Do Advanced Operations
    df_plots = do_op(df_plots, wdg, cols, '')
    df_plots = do_op(df_plots, wdg, cols, '2')
    df_plots = do_op(df_plots, wdg, cols, '3')

    #For arrow maps, flip the x axis when there are negatives so that all values are positive in the correct direction.
    if wdg['chart_type'].value == 'Line Map' and wdg['map_arrows'].value == 'Yes':
        df_plots[['temp_from','temp_to']] = df_plots[wdg['x'].value].str.split('-',expand=True)
        idx_neg = df_plots[wdg['y'].value] < 0
        df_plots.loc[idx_neg, wdg['x'].value] = df_plots.loc[idx_neg, 'temp_to'] + '-' + df_plots.loc[idx_neg, 'temp_from']
        df_plots[wdg['y'].value] = df_plots[wdg['y'].value].abs()
        df_plots.drop(['temp_from','temp_to'], axis='columns',inplace=True)

    #Scale Axes
    if wdg['x_scale'].value != '' and wdg['x'].value in cols['continuous'] + ['histogram_x']:
        df_plots[wdg['x'].value] = df_plots[wdg['x'].value] * float(wdg['x_scale'].value)
    if wdg['y_scale'].value != '' and wdg['y'].value in cols['continuous']:
        df_plots[wdg['y'].value] = df_plots[wdg['y'].value] * float(wdg['y_scale'].value)

    #For cum_sort set to "Ascending" or "Descending" we will sort by cumulative y value.
    #If net levels are shown, we must also calculate cumulative y value.
    cum_sort_cond = wdg['cum_sort'].value != 'None'
    net_level_cond = wdg['net_levels'].value == 'Yes' and wdg['chart_type'].value in STACKEDTYPES
    net_level_col = []
    if cum_sort_cond or net_level_cond:
        #adjust groupby_cols from Aggregation section above, and remove series from group if it is there
        net_group_cols = [c for c in groupby_cols if c != wdg['series'].value]
        #group and sum across series to get the cumulative y for each x
        df_net_group = df_plots.groupby(net_group_cols, sort=False)
        df_net = df_net_group[wdg['y'].value].sum().reset_index()
        if cum_sort_cond:
            df_cum = df_net.rename(columns={wdg['y'].value: 'y_cumulative'})
            if wdg['cum_sort'].value == 'Descending':
                #multiply by -1 so that we sort from large to small instead of small to large
                df_cum['y_cumulative'] = df_cum['y_cumulative']*-1
            df_plots = df_plots.merge(df_cum, how='left', on=net_group_cols, sort=False)
        if net_level_cond:
            net_level_col_name = 'Net Level ' + wdg['y'].value
            net_level_col = [net_level_col_name]
            df_net_lev = df_net.rename(columns={wdg['y'].value: net_level_col_name})
            df_plots = df_plots.merge(df_net_lev, how='left', on=net_group_cols, sort=False)

    #Sort Dataframe
    sortby_cols = []
    if wdg['sort_data'].value == 'Yes':
        sortby_cols = [wdg['x'].value]
        if wdg['x_group'].value != 'None':
            sortby_cols = [wdg['x_group'].value] + sortby_cols
        if wdg['series'].value != 'None': 
            sortby_cols = [wdg['series'].value] + sortby_cols
        if cum_sort_cond: 
            sortby_cols = ['y_cumulative'] + sortby_cols
        if wdg['explode'].value != 'None':
            sortby_cols = [wdg['explode'].value] + sortby_cols
        if wdg['explode_group'].value != 'None':
            sortby_cols = [wdg['explode_group'].value] + sortby_cols
        #Add custom sort columns
        temp_sort_cols = sortby_cols[:]
        for col in custom_sorts:
            if col in sortby_cols:
                df_plots[col + '__sort_col'] = df_plots[col].map(lambda x: custom_sorts[col].index(x))
                temp_sort_cols[sortby_cols.index(col)] = col + '__sort_col'
        #Do sorting
        df_plots = df_plots.sort_values(temp_sort_cols).reset_index(drop=True)
        # Remove leading zeros (sometime used for sorting integers)
        for col in temp_sort_cols:
            original_dtype = df_plots[col].dtype
            try:
                df_plots[col] = df_plots[col].astype(str).str.lstrip('0').astype(original_dtype)
            except ValueError:
                pass
        #Remove custom sort columns
        for col in custom_sorts:
            if col in sortby_cols:
                df_plots = df_plots.drop(col + '__sort_col', axis=1)
        if cum_sort_cond:
            df_plots = df_plots.drop('y_cumulative', axis=1)
            sortby_cols.remove('y_cumulative')

    #Rearrange column order for csv download
    sorted_cols = sortby_cols + [wdg['y'].value] + range_cols + net_level_col
    unsorted_columns = [col for col in df_plots.columns if col not in sorted_cols]
    df_plots = df_plots[unsorted_columns + sorted_cols]
    logger.info('***Done Filtering, Scaling, Aggregating, Adv Operations, Sorting: '+ str(datetime.datetime.now() - startTime))
    if wdg['render_plots'].value == 'No':
        logger.info('***Ready for download!')
    return df_plots

def do_op(df_plots, wdg, cols, sfx):
    op = wdg['adv_op' + sfx].value
    col = wdg['adv_col' + sfx].value
    col_base = wdg['adv_col_base' + sfx].value
    y_val = wdg['y'].value
    y_agg = wdg['y_agg'].value
    if op != 'None' and col != 'None' and col in df_plots and col_base != 'None' and y_agg != 'None' and y_val in cols['continuous'] and wdg['range'].value == 'No':
        if col in cols['continuous'] and col_base not in ADV_BASES:
            col_base = float(col_base)
        #groupby all columns that are not the operating column and y axis column so we can do operations on y-axis across the operating column
        groupcols = [i for i in df_plots.columns.values.tolist() if i not in [col, y_val]]
        if groupcols != []:
            df_grouped = df_plots.groupby(groupcols, sort=False)
        else:
            #if we don't have other columns to group, make one, to prevent error
            df_plots['tempgroup'] = 1
            df_grouped = df_plots.groupby('tempgroup', sort=False)
        #Now do operations with the groups:
        df_plots = df_grouped.apply(op_with_base, op, col, col_base, y_val).reset_index(drop=True)
        df_plots = df_plots.replace([np.inf, -np.inf], np.nan)
        #Finally, clean up df_plots, dropping unnecessary columns, rows with the base value, and any rows with NAs for y_vals
        if 'tempgroup' in df_plots:
            df_plots.drop(['tempgroup'], axis='columns', inplace=True)
        df_plots = df_plots[~df_plots[col].isin([col_base])]
        df_plots = df_plots[pd.notnull(df_plots[y_val])]
    return df_plots

def create_figures(df_plots, wdg, cols, custom_colors):
    '''
    Create figures based on the data in a dataframe and widget configuration, and return figures in a list.
    The explode widget determines if there will be multiple figures.

    Args:
        df_plots (pandas dataframe): Dataframe of csv source after being filtered, scaled, aggregated, and sorted.
        wdg (ordered dict): Dictionary of bokeh model widgets.
        cols (dict): Keys are categories of columns of df_source, and values are a list of columns of that category.
        custom_colors (dict): Keys are column names and values are dicts that map column values to colors (hex strings)

    Returns:
        plot_list (list): List of bokeh.model.figures.
    '''
    logger.info('***Building Figures...')
    plot_list = []
    df_plots_cp = df_plots.copy()
    if wdg['explode'].value == 'None':
        plot_list.append(create_figure(df_plots_cp, df_plots, wdg, cols, custom_colors))
    else:
        if wdg['explode_group'].value == 'None':
            for explode_val in df_plots_cp[wdg['explode'].value].unique().tolist():
                df_exploded = df_plots_cp[df_plots_cp[wdg['explode'].value].isin([explode_val])].copy()
                plot_list.append(create_figure(df_exploded, df_plots, wdg, cols, custom_colors, explode_val))
        else:
            for explode_group in df_plots_cp[wdg['explode_group'].value].unique().tolist():
                df_exploded_group = df_plots_cp[df_plots_cp[wdg['explode_group'].value].isin([explode_group])]
                for explode_val in df_exploded_group[wdg['explode'].value].unique().tolist():
                    df_exploded = df_exploded_group[df_exploded_group[wdg['explode'].value].isin([explode_val])].copy()
                    plot_list.append(create_figure(df_exploded, df_plots, wdg, cols, custom_colors, explode_val, explode_group))
    set_axis_bounds(df_plots, plot_list, wdg, cols)
    if wdg['explode_grid'].value == 'Yes':
        ncols = len(df_plots_cp[wdg['explode'].value].unique())
    else:
        ncols = int(wdg['num_cols'].value)
    logger.info('***Done Building Figures.\n')
    return plot_list, ncols

def set_axis_bounds(df, plots, wdg, cols):
    '''
    Set minimums and maximums for x and y axes.

    Args:
        df (pandas dataframe): Dataframe of all data currently being viewed.
        plots (list): List of bokeh.model.figures.
        wdg (ordered dict): Dictionary of bokeh model widgets.
        cols (dict): Keys are categories of columns of df_source, and values are a list of columns of that category.

    Returns:
        Nothing. Axes of plots are modified.
    '''
    if wdg['x'].value in cols['continuous'] + ['histogram_x'] and wdg['x_group'].value == 'None':
        if wdg['chart_type'].value == 'Bar':
            if wdg['x'].value == 'histogram_x':
                bar_width_half = (df['histogram_x'].iloc[1] - df['histogram_x'].iloc[0])/2
            else:
                bar_width_half = float(wdg['bar_width'].value)/2
        if wdg['x_min'].value != '':
            for p in plots:
                p.x_range.start = float(wdg['x_min'].value)
        elif wdg['sync_axes'].value == 'Yes':
            min_x = df[wdg['x'].value].min()
            if wdg['chart_type'].value == 'Bar':
                min_x = min_x - bar_width_half
            for p in plots:
                p.x_range.start = min_x
        if wdg['x_max'].value != '':
            for p in plots:
                p.x_range.end = float(wdg['x_max'].value)
        elif wdg['sync_axes'].value == 'Yes':
            max_x = df[wdg['x'].value].max()
            if wdg['chart_type'].value == 'Bar':
                max_x = max_x + bar_width_half
            for p in plots:
                p.x_range.end = max_x
    elif wdg['chart_type'].value == 'Bar' and wdg['bar_width'].value == 'c':
        if wdg['x_min'].value != '':
            for p in plots:
                p.x_range.start = float(wdg['x_min'].value)
        if wdg['x_max'].value != '':
            for p in plots:
                p.x_range.end = float(wdg['x_max'].value)
    if wdg['y'].value in cols['continuous']:
        #find grouped cols for stacked manipulations
        col_names = df.columns.values.tolist()
        groupby_cols = [i for i in col_names if i not in [wdg['series'].value, wdg['y'].value]]
        if wdg['y_min'].value != '':
            for p in plots:
                p.y_range.start = float(wdg['y_min'].value)
        elif wdg['sync_axes'].value == 'Yes':
            if wdg['chart_type'].value in STACKEDTYPES:
                #sum negative values across series
                df_neg = df[df[wdg['y'].value] < 0]
                df_neg_sum = df_neg.groupby(groupby_cols, sort=False)[wdg['y'].value].sum().reset_index()
                min_y = df_neg_sum[wdg['y'].value].min()
            else:
                if wdg['range'].value == 'Within Series':
                    if wdg['range_show_glyphs'].value == 'Yes':
                        min_y = min(df['range_min'].min(), df[wdg['y'].value].min())
                    else:
                        min_y = df['range_min'].min()
                else:
                    min_y = df[wdg['y'].value].min()
            min_y = min(0, min_y)
            for p in plots:
                p.y_range.start = min_y
        if wdg['y_max'].value != '':
            for p in plots:
                p.y_range.end = float(wdg['y_max'].value)
        elif wdg['sync_axes'].value == 'Yes':
            if wdg['chart_type'].value in STACKEDTYPES:
                #sum postive values across series
                df_pos = df[df[wdg['y'].value] > 0]
                df_pos_sum = df_pos.groupby(groupby_cols, sort=False)[wdg['y'].value].sum().reset_index()
                max_y = df_pos_sum[wdg['y'].value].max()
            else:
                if wdg['range'].value == 'Within Series':
                    if wdg['range_show_glyphs'].value == 'Yes':
                        max_y = max(df['range_max'].max(), df[wdg['y'].value].max())
                    else:
                        max_y = df['range_max'].max()
                else:
                    max_y = df[wdg['y'].value].max()
            max_y = max(0, max_y)
            for p in plots:
                p.y_range.end = max_y


def create_figure(df_exploded, df_plots, wdg, cols, custom_colors, explode_val=None, explode_group=None):
    '''
    Create and return a figure based on the data in a dataframe and widget configuration.

    Args:
        df_exploded (pandas dataframe): Dataframe of just the data that will be plotted in this figure.
        df_plots (pandas dataframe): Dataframe of all plots data, used only for maintaining consistent series colors.
        wdg (ordered dict): Dictionary of bokeh model widgets.
        cols (dict): Keys are categories of columns of df_source, and values are a list of columns of that category.
        custom_colors (dict): Keys are column names and values are dicts that map column values to colors (hex strings)
        explode_val (string, optional): The value in the column designated by wdg['explode'] that applies to this figure.
        explode_group (string, optional): The value in the wdg['explode_group'] column that applies to this figure.

    Returns:
        p (bokeh.model.figure): A figure, with all glyphs added by the add_glyph() function.
    '''
    # If x_group has a value, create a combined column in the dataframe for x and x_group
    x_col = wdg['x'].value
    if wdg['x_group'].value != 'None':
        x_col = str(wdg['x_group'].value) + '_' + str(wdg['x'].value)
        df_exploded[x_col] = df_exploded[wdg['x_group'].value].map(str) + ' ' + df_exploded[wdg['x'].value].map(str)

    #Build x and y ranges and figure title
    kw = dict()
    chart_type = wdg['chart_type'].value
    #Set x and y ranges. When x is grouped, there is added complication of separating the groups
    xs = df_exploded[x_col].values.tolist()
    ys = df_exploded[wdg['y'].value].values.tolist()
    if not (chart_type == 'Bar' and wdg['bar_width'].value == 'c'):
        if wdg['x_group'].value != 'None':
            kw['x_range'] = []
            unique_groups = df_exploded[wdg['x_group'].value].unique().tolist()
            unique_xs = df_exploded[wdg['x'].value].unique().tolist()
            for i, ugr in enumerate(unique_groups):
                for uxs in unique_xs:
                    kw['x_range'].append(str(ugr) + ' ' + str(uxs))
                #Between groups, add entries that consist of spaces. Increase number of spaces from
                #one break to the next so that each entry is unique
                kw['x_range'].append(' ' * (i + 1))
        elif wdg['x'].value in cols['discrete']:
            kw['x_range'] = []
            for x in xs:
                if x not in kw['x_range']:
                    kw['x_range'].append(x)
        if wdg['y'].value in cols['discrete']:
            kw['y_range'] = []
            for y in ys:
                if y not in kw['y_range']:
                    kw['y_range'].append(y)

    #Set figure title
    kw['title'] = wdg['plot_title'].value
    seperator = '' if kw['title'] == '' else ', '
    if explode_val is not None:
        if explode_group is not None:
            kw['title'] = kw['title'] + seperator + str(explode_group)
        seperator = '' if kw['title'] == '' else ', '
        kw['title'] = kw['title'] + seperator + str(explode_val)

    #Add figure tools
    hover_tool = bmt.HoverTool(
            tooltips=[
                ("ser", "@ser_legend"),
                ("x", "@x_legend"),
                ("y", "@y_legend"),
            ]
    )
    pan_tool = bmt.PanTool()
    wheelzoom_tool = bmt.WheelZoomTool()
    reset_tool = bmt.ResetTool()
    save_tool = bmt.SaveTool()
    boxzoom_tool = bmt.BoxZoomTool()
    TOOLS = [boxzoom_tool, wheelzoom_tool, pan_tool, hover_tool, reset_tool, save_tool]

    #Create figure with the ranges, titles, and tools, and adjust formatting and labels
    p = bp.figure(height=int(wdg['height'].value), width=int(wdg['width'].value), tools=TOOLS, **kw)
    p.toolbar.active_drag = boxzoom_tool
    p.title.text_font_size = wdg['plot_title_size'].value + 'pt'
    p.xaxis.axis_label = wdg['x_title'].value
    p.yaxis.axis_label = wdg['y_title'].value
    p.xaxis.axis_label_text_font_size = wdg['x_title_size'].value + 'pt'
    p.yaxis.axis_label_text_font_size = wdg['y_title_size'].value + 'pt'
    p.xaxis.major_label_text_font_size = wdg['x_major_label_size'].value + 'pt'
    p.yaxis.major_label_text_font_size = wdg['y_major_label_size'].value + 'pt'
    p.xaxis.major_label_orientation = 'horizontal' if wdg['x_major_label_orientation'].value == '0' else math.radians(float(wdg['x_major_label_orientation'].value))
    if wdg['bokeh_tools'].value == 'No':
        p.toolbar.logo = None
        p.toolbar_location = None

    #Add glyphs to figure
    c = C_NORM
    if wdg['series'].value == 'None':
        if wdg['range'].value == 'Within Series':
            y_mins = df_exploded['range_min'].values.tolist()
            y_maxs = df_exploded['range_max'].values.tolist()
            add_glyph(RANGE_GLYPH_MAP[chart_type], wdg, p, xs, y_maxs, c, y_bases=y_mins, opacity_mult=RANGE_OPACITY_MULT)
        if wdg['range_show_glyphs'].value == 'Yes':
            add_glyph(chart_type, wdg, p, xs, ys, c)
    else:
        full_series = df_plots[wdg['series'].value].unique().tolist() #for colors only
        xs_full = df_exploded[x_col].unique().tolist()
        if chart_type in STACKEDTYPES: #We are stacking the series
            y_bases_pos = [0]*len(xs_full)
            y_bases_neg = [0]*len(xs_full)
        elif wdg['range'].value == 'Between Series':
            y_mins = []
            y_maxs = []
            for x_unique in xs_full:
                y_group = [ys[i] for i, x in enumerate(xs) if x == x_unique]
                y_mins.append(min(y_group))
                y_maxs.append(max(y_group))
            add_glyph(RANGE_GLYPH_MAP[chart_type], wdg, p, xs_full, y_maxs, c, y_bases=y_mins, opacity_mult=RANGE_OPACITY_MULT)
        for i, ser in enumerate(df_exploded[wdg['series'].value].unique().tolist()):
            if custom_colors and wdg['series'].value in custom_colors and ser in custom_colors[wdg['series'].value]:
                c = custom_colors[wdg['series'].value][ser]
            else:
                c = COLORS[full_series.index(ser)]
            df_series = df_exploded[df_exploded[wdg['series'].value].isin([ser])]
            xs_ser = df_series[x_col].values.tolist()
            ys_ser = df_series[wdg['y'].value].values.tolist()
            if chart_type not in STACKEDTYPES: #The series will not be stacked
                if wdg['range'].value == 'Within Series':
                    y_mins_ser = df_series['range_min'].values.tolist()
                    y_maxs_ser = df_series['range_max'].values.tolist()
                    add_glyph(RANGE_GLYPH_MAP[chart_type], wdg, p, xs_ser, y_maxs_ser, c, y_bases=y_mins_ser, series=ser, opacity_mult=RANGE_OPACITY_MULT)
                if wdg['range_show_glyphs'].value == 'Yes':
                    add_glyph(chart_type, wdg, p, xs_ser, ys_ser, c, series=ser)
            else: #We are stacking the series
                ys_pos = [ys_ser[xs_ser.index(x)] if x in xs_ser and ys_ser[xs_ser.index(x)] > 0 else 0 for i, x in enumerate(xs_full)]
                ys_neg = [ys_ser[xs_ser.index(x)] if x in xs_ser and ys_ser[xs_ser.index(x)] < 0 else 0 for i, x in enumerate(xs_full)]
                ys_stacked_pos = [ys_pos[i] + y_bases_pos[i] for i in range(len(xs_full))]
                ys_stacked_neg = [ys_neg[i] + y_bases_neg[i] for i in range(len(xs_full))]
                add_glyph(chart_type, wdg, p, xs_full, ys_stacked_pos, c, y_bases=y_bases_pos, series=ser)
                add_glyph(chart_type, wdg, p, xs_full, ys_stacked_neg, c, y_bases=y_bases_neg, series=ser)
                y_bases_pos = ys_stacked_pos
                y_bases_neg = ys_stacked_neg
        if wdg['net_levels'].value == 'Yes' and chart_type in STACKEDTYPES:
            ys_net = [ys_stacked_pos[i] + ys_stacked_neg[i] for i,x in enumerate(xs_full)]
            add_glyph('Dot', wdg, p, xs_full, ys_net, 'black', series='Net Level')
    return p

def add_glyph(glyph_type, wdg, p, xs, ys, c, y_bases=None, series=None, opacity_mult=1):
    '''
    Add a glyph to a Bokeh figure, depending on the chosen chart type.

    Args:
        glyph_type (str): Type of glyph (e.g. 'Dot', 'Line', 'Bar', 'Area')
        wdg (ordered dict): Dictionary of bokeh model widgets.
        p (bokeh.model.figure): Bokeh figure.
        xs (list): List of x-values. These could be numeric or strings.
        ys (list): List of y-values. These could be numeric or strings. If series data is stacked, these values include stacking.
        c (string): Color to use for this series.
        y_bases (list, optional): Only used when stacking series. This is the previous cumulative stacking level.
        series (string): Name of current series for this glyph.

    Returns:
        Nothing.
    '''
    alpha = float(wdg['opacity'].value)*opacity_mult
    y_unstacked = list(ys) if y_bases is None else [ys[i] - y_bases[i] for i in range(len(ys))]
    ser = ['None']*len(xs) if series is None else [series]*len(xs)
    if glyph_type in ['Dot', 'Dot-Line']:
        source = bms.ColumnDataSource({'x': xs, 'y': ys, 'x_legend': xs, 'y_legend': y_unstacked, 'ser_legend': ser})
        p.circle('x', 'y', source=source, color=c, size=int(wdg['circle_size'].value), fill_alpha=alpha, line_color=None, line_width=0)
    if glyph_type in ['Line', 'Dot-Line']:
        source = bms.ColumnDataSource({'x': xs, 'y': ys, 'x_legend': xs, 'y_legend': y_unstacked, 'ser_legend': ser})
        p.line('x', 'y', source=source, color=c, alpha=alpha, line_width=float(wdg['line_width'].value))
    if glyph_type == 'Bar' and y_unstacked != [0]*len(y_unstacked):
        if y_bases is None:
            y_bases = [0]*len(ys)
        centers = [(ys[i] + y_bases[i])/2 for i in range(len(ys))]
        heights = [abs(ys[i] - y_bases[i]) for i in range(len(ys))]
        xs_cp = list(xs) #we don't want to modify xs that are passed into function
        x_legend = list(xs)
        if wdg['x'].value == 'histogram_x':
            width = xs[1] - xs[0]
            x_legend = [str(x_legend[i] - width/2) + ' to ' + str(x_legend[i] + width/2) for i, x in enumerate(xs)]
            widths = [width]*len(xs)
        elif wdg['bar_width'].value == 'w': #this means we are looking for the mapping in the _bar_width file
            df_bar_width = pd.read_csv(this_dir_path + '/in/' + wdg['x'].value + '_bar_width.csv', index_col='display')
            max_width = df_bar_width['width'].max()
            widths = [df_bar_width.loc[x, 'width']/max_width for x in xs]
            x_legend = [str(x_legend[i]) + ' (width = ' + str(df_bar_width.loc[x, 'width']) + ')' for i, x in enumerate(xs)]
        elif wdg['bar_width'].value == 'c': #this means we are converting x axis to continuous and have no gaps between bars
            widths = []
            df_bar_width = pd.read_csv(this_dir_path + '/in/' + wdg['x'].value + '_bar_width.csv', index_col='display')
            xs_cum = 0
            for i, xo in enumerate(xs):
                width = df_bar_width.loc[xo, 'width']
                widths.append(width)
                xs_cp[i] = width/2 + xs_cum
                xs_cum = xs_cum + width
                x_legend[i] = str(x_legend[i]) + ' (width = ' + str(width) + ', ' + str(xs_cum) + ' cumulative)'
        else:
            widths = [float(wdg['bar_width'].value)]*len(xs)
        #bars have issues when height is 0, so remove elements whose height is 0 
        heights_orig = list(heights) #we make a copy so we aren't modifying the list we are iterating on.
        for i, h in reversed(list(enumerate(heights_orig))):
            #Ok this is getting absurd, but rects with near-zero heights also break the glyphs.
            #See https://github.com/bokeh/bokeh/issues/6583.
            if abs(h) <= 1e-13:
                del xs_cp[i], centers[i], heights[i], y_unstacked[i], ser[i], widths[i], x_legend[i]
        source = bms.ColumnDataSource({'x': xs_cp, 'y': centers, 'x_legend': x_legend, 'y_legend': y_unstacked, 'h': heights, 'w': widths, 'ser_legend': ser})
        p.rect('x', 'y', source=source, height='h', color=c, fill_alpha=alpha, width='w', line_color=None, line_width=0)
    if glyph_type =='Area' and y_unstacked != [0]*len(y_unstacked):
        if y_bases is None:
            y_bases = [0]*len(ys)
        xs_around = xs + xs[::-1]
        ys_around = y_bases + ys[::-1]
        source = bms.ColumnDataSource({'x': [xs_around], 'y': [ys_around], 'x_legend': [wdg['x'].value], 'y_legend': [wdg['y'].value], 'ser_legend': [series]})
        p.patches('x', 'y', source=source, alpha=alpha, fill_color=c, line_color=None, line_width=0)

    #Add boxplots
    if wdg['range'].value == 'Boxplot':
        df = pd.DataFrame({'x':xs,'y':ys})
        groups = df.groupby('x')
        q1 = groups.quantile(q=0.25)
        q2 = groups.quantile(q=0.5)
        q3 = groups.quantile(q=0.75)
        iqr = q3 - q1
        up = groups.quantile(q=0.95)
        lo = groups.quantile(q=0.05)
        box_centers = (q1 + q3)/2
        x_range = q2.index.tolist()
        quartile_legend = ['5%: ' + '{:.2e}'.format(lo['y'][r]) + ', 25%: ' + '{:.2e}'.format(q1['y'][r]) + ', 50%: ' + '{:.2e}'.format(q2['y'][r]) + ', 75%: ' + '{:.2e}'.format(q3['y'][r]) + ', 95%: ' + '{:.2e}'.format(up['y'][r]) for r in x_range]
        lw = float(wdg['line_width'].value)
        width = float(wdg['bar_width'].value)
        ser_box = ['None']*len(x_range) if series is None else [series]*len(x_range)
        #boxes
        src_q2 = bms.ColumnDataSource({'x': x_range, 'y': q2['y'].tolist(), 'x_legend': x_range, 'y_legend': q2['y'].tolist(), 'ser_legend': ser_box})
        p.rect('x', 'y', source=src_q2, height=lw, width=width, color=c, fill_alpha=alpha, line_color=None, line_width=0, height_units="screen")
        src_box = bms.ColumnDataSource({'x': x_range, 'y': box_centers['y'].tolist(), 'h': iqr['y'].tolist(), 'x_legend': x_range, 'y_legend': quartile_legend, 'ser_legend': ser_box})
        p.rect('x', 'y', source=src_box, height='h', width=width, color=None, line_alpha=alpha, line_color=c, line_width=lw)
        #whiskers
        src_lo = bms.ColumnDataSource({'x': x_range, 'y': lo['y'].tolist(), 'x_legend': x_range, 'y_legend': lo['y'].tolist(), 'ser_legend': ser_box})
        p.rect('x', 'y', source=src_lo, height=lw, width=0.9*width, color=c, fill_alpha=alpha, line_color=None, line_width=0, height_units="screen")
        src_up = bms.ColumnDataSource({'x': x_range, 'y': up['y'].tolist(), 'x_legend': x_range, 'y_legend': up['y'].tolist(), 'ser_legend': ser_box})
        p.rect('x', 'y', source=src_up, height=lw, width=0.9*width, color=c, fill_alpha=alpha, line_color=None, line_width=0, height_units="screen")
        #stems
        src_upstem = bms.ColumnDataSource({'x0': x_range, 'y0': up['y'].tolist(), 'x1': x_range, 'y1': q3['y'].tolist(), 'x_legend': x_range, 'y_legend': quartile_legend, 'ser_legend': ser_box})
        src_lostem = bms.ColumnDataSource({'x0': x_range, 'y0': lo['y'].tolist(), 'x1': x_range, 'y1': q1['y'].tolist(), 'x_legend': x_range, 'y_legend': quartile_legend, 'ser_legend': ser_box})
        p.segment('x0', 'y0', 'x1', 'y1', source=src_upstem, line_color=c, line_width=lw/2, line_alpha=alpha)
        p.segment('x0', 'y0', 'x1', 'y1', source=src_lostem, line_color=c, line_width=lw/2, line_alpha=alpha)

def create_maps(df, wdg, cols):
    '''
    Create maps based on an input dataframe.The second-to-last column of this
    dataframe is assumed to be the x-axis, or the column of regions that are to be mapped.
    The last column of this dataframe will be the y axis, or the values that correspond
    to the regions. Values are binned into ranges and then mapped to a color for each region.

    Args:
        df (pandas dataframe): input dataframe described above
        wdg (ordered dict): Dictionary of bokeh model widgets.
        cols (dict): Keys are categories of columns of df_source, and values are a list of columns of that category.
    Returns:
        maps (list of bokeh.plotting.figure): These maps are created by the create_map function.
        breakpoints (list of float): Breakpoints that separate the color-shaded bins.
    '''
    logger.info('***Building Maps...')
    maps = []
    breakpoints = []
    x_axis = df.iloc[:,-2]
    y_axis = df.iloc[:,-1]
    if y_axis.dtype == object:
        logger.info('***Error, your y-axis is a string.')
        return (maps, breakpoints) #empty list
    if wdg['chart_type'].value == 'Area Map':
        if not os.path.isfile(this_dir_path + '/in/gis_' + x_axis.name + '.csv'):
            logger.info('***Error. X-axis is not a supported region type for area maps.')
            return (maps, breakpoints) #empty list
        map_type = 'area'
        reg_name = x_axis.name
        full_rgs = x_axis.unique().tolist()
        centroids = None
    elif wdg['chart_type'].value == 'Line Map':
        reg_arr = x_axis.name.split('-')
        if not (len(reg_arr) == 2 and reg_arr[0] == reg_arr[1] and os.path.isfile(this_dir_path + '/in/gis_' + reg_arr[0] + '.csv') and os.path.isfile(this_dir_path + '/in/gis_centroid_' + reg_arr[0] + '.csv')):
            logger.info('***Error. X-axis is not supported for line maps.')
            return (maps, breakpoints) #empty list
        reg_name = reg_arr[0]
        map_type = 'line'
        centroids = pd.read_csv(this_dir_path + '/in/gis_centroid_' + reg_name + '.csv', sep=',', dtype={'id': object})
        #Add x and y columns to centroids and find x and y ranges
        centroids['x'] = centroids['long']*53
        centroids['y'] = centroids['lat']*69
        centroids = centroids[['id','x','y']]
        full_joint = x_axis.unique().tolist()
        full_rgs = [i.split('-')[0] for i in full_joint] + [i.split('-')[1] for i in full_joint]
        full_rgs = list(set(full_rgs))
    #find x and y ranges based on the mins and maxes of the regional boundaries for only regions that
    #are in the data
    filepath = this_dir_path + '/in/gis_' + reg_name + '.csv'
    region_boundaries = pd.read_csv(filepath, sep=',', dtype={'id': object, 'group': object})
    #Remove holes
    region_boundaries = region_boundaries[region_boundaries['hole'] == False]
    #keep only regions that are in df
    region_boundaries = region_boundaries[region_boundaries['id'].isin(full_rgs)]
    #Add x and y columns to region_boundaries and find x and y ranges
    region_boundaries['x'] = region_boundaries['long']*53
    region_boundaries['y'] = region_boundaries['lat']*69
    ranges = {
        'x_max': region_boundaries['x'].max(),
        'x_min': region_boundaries['x'].min(),
        'y_max': region_boundaries['y'].max(),
        'y_min': region_boundaries['y'].min(),
    }

    #Ignore zeros (happens after region_boundaries have been gathered to keep regions with zero)
    if wdg['map_nozeros'].value == 'Yes':
        df = df[y_axis != 0].copy()
        y_axis = df.iloc[:,-1]

    #set breakpoints depending on the binning strategy
    if wdg['map_bin'].value == 'Auto Equal Num': #an equal number of data ponts in each bin
        map_num_bins = int(wdg['map_num'].value)
        #with full list of values, find uniques with set, and return a sorted list of the uniques
        val_list = sorted(set(y_axis.tolist()))
        #bin indices, find index breakpoints, and convert into value breakpoints.
        index_step = (len(val_list) - 1)/map_num_bins
        indices = [int((i+1)*index_step) for i in range(map_num_bins - 1)]
        breakpoints = [val_list[i] for i in indices]
    elif wdg['map_bin'].value == 'Auto Equal Width': #bins of equal width
        map_num_bins = int(wdg['map_num'].value)
        if wdg['map_min'].value != '' and wdg['map_max'].value != '':
            map_min = float(wdg['map_min'].value)
            map_max = float(wdg['map_max'].value)
            bin_width = (map_max - map_min)/(map_num_bins - 2)
            breakpoints = [map_min + bin_width*i for i in range(map_num_bins - 1)]
        else:
            bin_width = float(y_axis.max() - y_axis.min())/map_num_bins
            map_min = y_axis.min() + bin_width
            map_max = y_axis.max() - bin_width
            breakpoints = [map_min + bin_width*i for i in range(map_num_bins - 1)]
    elif wdg['map_bin'].value == 'Manual':
        breakpoints = [float(bp) for bp in wdg['map_manual'].value.split(',')]

    colors_full = get_map_colors(wdg, breakpoints)

    df_maps = df.copy()
    #assign all y-values to bins
    df_maps['bin_index'] = y_axis.apply(get_map_bin_index, args=(breakpoints,))
    #If there are only 3 columns (x_axis, y_axis, and bin_index), that means we aren't exploding:
    if len(df_maps.columns) == 3:
        maps.append(create_map(map_type, df_maps, ranges, region_boundaries, centroids, wdg, colors_full))
        logger.info('***Done building map.\n')
        return (maps, breakpoints) #single map
    #Otherwise we are exploding.
    #find all unique groups of the explode columns.
    df_unique = df_maps.copy()
    #remove x, y, and bin_index
    df_unique = df_unique[df_unique.columns[0:-3]]
    df_unique.drop_duplicates(inplace=True)
    #Loop through rows of df_unique, filter df_maps based on values in each row,
    #and send filtered dataframe to mapping function
    for i, row in df_unique.iterrows():
        df_map = df_maps.copy()
        title = ''
        for col in df_unique:
            df_map = df_map[df_map[col] == row[col]]
            title = title + col + '=' + str(row[col]) + ', '
        #preserve just x axis, y axis, and bin index
        df_map = df_map[df_map.columns[-3:]]
        #remove final comma of title
        title = title[:-2]
        maps.append(create_map(map_type, df_map, ranges, region_boundaries, centroids, wdg, colors_full, title))
    logger.info('***Done building maps.\n')
    return (maps, breakpoints) #multiple maps

def create_map(map_type, df, ranges, region_boundaries, centroids, wdg, colors_full, title=''):
    '''
    Create either a line or area map.

    Args:
        map_type (string): 'area' or 'line'
        df (pandas dataframe): Input dataframe. First column is regions, second column is values, third column is bin indexes that have been assigned to values.
        region_boundaries (pandas dataframe): This dataframe has columns for region id, group (if the region has non-contiguous pieces), and x and y values of all boundary points.
        centroids (pandas dataframe): Only relevant for a line map, this df has the centroids of all the regions.
        wdg (ordered dict): Dictionary of bokeh model widgets.
        colors_full (list of strings): Colors to shade the map
        title (string): The displayed title for this map
    Returns:
        fig_map (bokeh.plotting.figure): the bokeh figure for the map.
    '''
    df_regions = df.iloc[:,0].tolist()
    df_values = df.iloc[:,1].tolist()
    df_bins = df.iloc[:,2].tolist()

    xs = [] #list of lists of x values of boundaries of regions
    ys = [] #list of lists of y values of boundaries of regions
    regions = []
    values = []
    colors = []
    for grp in region_boundaries['group'].unique().tolist():
        region_boundary = region_boundaries[region_boundaries['group'] == grp]
        xs.append(region_boundary['x'].values.tolist())
        ys.append(region_boundary['y'].values.tolist())
        reg = region_boundary['id'].iloc[0]
        regions.append(reg)
        if map_type == 'area' and reg in df_regions:
            index = df_regions.index(reg)
            value = df_values[index]
            values.append(value)
            bin_num = df_bins[index]
            colors.append(colors_full[int(bin_num)])
        else:
            values.append('NA')
            colors.append('#ffffff')

    source = bms.ColumnDataSource(data=dict(
        x=xs,
        y=ys,
        region=regions,
        value=values,
        color=colors,
    ))
    #Add figure tools
    hover_tool = bmt.HoverTool(
            tooltips=[
                ("reg", "@region"),
                ("val", "@value"),
            ],
            point_policy = "follow_mouse",
    )
    pan_tool = bmt.PanTool()
    wheelzoom_tool = bmt.WheelZoomTool()
    reset_tool = bmt.ResetTool()
    save_tool = bmt.SaveTool()
    boxzoom_tool = bmt.BoxZoomTool()
    TOOLS = [boxzoom_tool, wheelzoom_tool, pan_tool, hover_tool, reset_tool, save_tool]
    #find max and min of xs and ys to set aspect ration of map
    
    aspect_ratio = (ranges['y_max'] - ranges['y_min'])/(ranges['x_max'] - ranges['x_min'])
    width = wdg['map_width'].value
    height = aspect_ratio * float(width)
    fig_map = bp.figure(
        title=title,
        height=int(height),
        width=int(width),
        x_range=(ranges['x_min'], ranges['x_max']),
        y_range=(ranges['y_min'], ranges['y_max']),
        x_axis_location=None,
        y_axis_location=None,
        tools=TOOLS
    )
    fig_map.title.text_font_size = wdg['map_font_size'].value + 'pt'
    fig_map.toolbar.active_drag = boxzoom_tool
    if wdg['bokeh_tools'].value == 'No':
        fig_map.toolbar.logo = None
        fig_map.toolbar_location = None
    fig_map.grid.grid_line_color = None
    fig_map.patches('x', 'y', source=source, fill_color='color', fill_alpha=float(wdg['map_opacity'].value), line_color="black", line_width=float(wdg['map_boundary_width'].value))

    if map_type == 'line':
        #For line and arrow maps, note that data should be preprocessed so that reverse entries for x axis do not exist.
        #For example, if 'r4-r7' exists, then 'r7-r4' should not.
        df[['from','to']] = df.iloc[:,0].str.split('-',expand=True)
        df = df.merge(centroids, how='left', left_on='from', right_on='id', sort=False)
        df.rename(columns={'x':'from_x','y':'from_y'}, inplace=True)
        df = df.merge(centroids, how='left', left_on='to', right_on='id', sort=False)
        df.rename(columns={'x':'to_x','y':'to_y'}, inplace=True)
        xs = df[['from_x','to_x']].values.tolist()
        ys = df[['from_y','to_y']].values.tolist()
        colors = [colors_full[i] for i in df_bins]
        source = bms.ColumnDataSource(data=dict(
            x=xs,
            y=ys,
            region=df_regions,
            value=df_values,
            color=colors,
        ))
        lines = fig_map.multi_line('x', 'y', source=source, color='color', alpha=float(wdg['map_opacity'].value), line_width=float(wdg['map_line_width'].value))
        hover_tool.renderers = [lines]
        if wdg['map_arrows'].value == 'Yes':
            #For arrow maps, negative values in the data are converted into positives in the
            #opposite direction (in set_df_plots()), so negative values should no longer exist.
            for i,x in enumerate(xs):
                x_end = xs[i][0] + float(wdg['map_arrow_loc'].value)*(xs[i][1] - xs[i][0])
                y_end = ys[i][0] + float(wdg['map_arrow_loc'].value)*(ys[i][1] - ys[i][0])
                fig_map.add_layout(bm.Arrow(x_start=xs[i][0], y_start=ys[i][0], x_end=x_end, y_end=y_end, line_alpha=0,
                    end=bm.OpenHead(size=float(wdg['map_arrow_size'].value),line_color=colors[i], line_width=float(wdg['map_line_width'].value), line_alpha=float(wdg['map_opacity'].value)),
                ))
    return fig_map

def get_map_bin_index(val, breakpoints):
    '''
    Helper function for determining the bin number for a given value and set of breakpoints.
    This assumes that bin ranges are less than or equal to the upper value and
    strictly greater than the lower value.

    Args:
        val (float): The value that is to be binned
        breakpoints (list of float): Breakpoints that separate the color-shaded bins.
    Returns:
        bin index (int): the bin number that will determine the color of the region.
    '''
    for i, breakpoint in enumerate(breakpoints):
        if val <= breakpoint:
            return i
    return len(breakpoints)


def build_map_legend(wdg, breakpoints):
    '''
    Return html for map legend, based on supplied labels and global COLORS

    Args:
        wdg (ordered dict): Dictionary of bokeh model widgets.
        breakpoints (list of float): Breakpoints that separate the color-shaded bins.
    Returns:
        legend_string (string): full html to be used as legend.
    '''

    if wdg['map_bin'].value == 'Manual':
        breakpoint_strings = [str(bp) for bp in breakpoints]
    else:
        breakpoint_strings = prettify_numbers(breakpoints)

    labels = ['<= ' + breakpoint_strings[0]]
    labels += [breakpoint_strings[i] + ' - ' + breakpoint_strings[i+1] for i in range(len(breakpoint_strings) - 1)]
    labels += ['> ' + breakpoint_strings[-1]]

    colors = get_map_colors(wdg, breakpoints)
    legend_string = build_legend(labels, colors)
    return legend_string

def get_map_colors(wdg, breakpoints):
    '''
    Return list of map colors. If we have a second palette, we will reverse it and use it
    at the beginning. We also may have map_palette_break, which will be used as a breakpoint
    to separate the colors.

    Args:
        wdg (ordered dict): Dictionary of bokeh model widgets.
        breakpoints (list of float): Breakpoints that separate the color-shaded bins.
    Returns:
        List of hex strings that represent map colors
    '''

    palette = wdg['map_palette'].value
    palette_2 = wdg['map_palette_2'].value
    palette_break = wdg['map_palette_break'].value
    num = len(breakpoints) + 1

    if palette_2 == '':
        return get_palette(palette, num)
    else:
        if palette_break == '':
            if num % 2 == 0:
                #even number of bins, so we split num equally between the palettes
                return list(reversed(get_palette(palette_2, num/2))) + get_palette(palette, num/2)
            else:
                #odd number of bins, so the middle bin is white and we split the rest equally between the other palettes
                return list(reversed(get_palette(palette_2, (num-1)/2))) + ['#ffffff'] + get_palette(palette, (num-1)/2)
        else:
            palette_break = float(palette_break)
            bp_low = [bp for bp in breakpoints if bp < palette_break]
            num_low = len(bp_low)
            num_high = num - num_low - 1
            if palette_break in breakpoints:
                return list(reversed(get_palette(palette_2, num_low + 1))) + get_palette(palette, num_high)
            else:
                return list(reversed(get_palette(palette_2, num_low))) + ['#ffffff'] + get_palette(palette, num_high)


def get_palette(palette, num):
    '''
    Return list of colors in palette based on the palette name and number of bins.
    Most are taken from bokeh.palettes.all_palettes[palette][num], but 'all_red', 'all_green',
    'all_blue', and 'all_gray' are also allowed as names for palette, and are generated from
    bokeh.palettes.linear_palette().

    Args:
        palette (string): The name of the palette
        num (int): Number of colors to return
    Returns:
        List of hex strings in palette
    '''

    if num == 0:
        return []
    if palette.startswith('all_'):
        if palette == 'all_red':
            return bpa.linear_palette(['#%02x%02x%02x' % (255, 255-i, 255-i) for i in range(256)],num)
        elif palette == 'all_green':
            return bpa.linear_palette(['#%02x%02x%02x' % (255-i, 255, 255-i) for i in range(256)],num)
        elif palette == 'all_blue':
            return bpa.linear_palette(['#%02x%02x%02x' % (255-i, 255-i, 255) for i in range(256)],num)
        elif palette == 'all_gray':
            return bpa.linear_palette(['#%02x%02x%02x' % (255-i, 255-i, 255-i) for i in range(256)],num)
    else:
        pal = bpa.all_palettes[palette]
        if 2 not in pal:
            pal[2] = [pal[3][0], pal[3][2]]
        if 1 not in pal:
            pal[1] = [pal[3][0]]
        return list(reversed(pal[num]))

def build_plot_legend(df_plots, wdg, custom_sorts, custom_colors):
    '''
    Return html for series legend, based on values of column that was chosen for series, and global COLORS.

    Args:
        df_plots (pandas dataframe): Dataframe of all plots data.
        wdg (ordered dict): Dictionary of bokeh model widgets.
        custom_sorts (dict): Keys are column names. Values are lists of values in the desired sort order.
        custom_colors (dict): Keys are column names. Values are dicts that map column values to colors (hex strings)

    Returns:
        legend_string (string): html to be used as legend.
    '''
    series_val = wdg['series'].value
    if series_val == 'None':
        return ''
    labels = df_plots[series_val].unique().tolist()
    colors = [COLORS[i] for i, t in enumerate(labels)]
    if custom_colors and series_val in custom_colors:
        for i, lab in enumerate(labels):
             if lab in custom_colors[series_val]:
                 colors[i] = custom_colors[series_val][lab]
    #resort to abide by series custom ordering. This may have been disrupted by x-axis bar height sorting or explode sorting.
    if wdg['sort_data'].value == 'Yes' and custom_sorts and series_val in custom_sorts:
        label_color = dict(zip(labels, colors))
        labels_1 = [L for L in custom_sorts[series_val] if L in labels]
        labels_2 = [L for L in labels if L not in labels_1]
        labels = labels_1 + labels_2
        colors = [label_color[L] for L in labels]
    #reverse order of legend
    labels.reverse()
    colors.reverse()
    legend_string = build_legend(labels, colors)
    return legend_string

def build_legend(labels, colors):
    '''
    Return html for legend, based on list of labels and list of colors

    Args:
        labels(list of strings): Displayed labels for each legend entry
        colors (list of strings): List of color strings using hexidecimal format
    Returns:
        legend_string (string): html to be used as legend.
    '''
    legend_string = ''
    for i, txt in enumerate(labels):
        legend_string += '<div class="legend-entry"><span class="legend-color" style="background-color:' + str(colors[i]) + ';"></span>'
        legend_string += f'<span class="legend-text">' + str(txt) +'</span></div>'
    return legend_string

def display_config(wdg, wdg_defaults):
    '''
    Build HTML for displaying list of non-default widget configurations

    Args:
        wdg (ordered dict): Dictionary of bokeh model widgets.
        wdg_defaults (dict): Keys are widget names and values are the default values of the widgets.

    Returns:
        output: HTML of displayed list of widget configurations
    '''
    output = '<div class="config-display-title">Config Summary</div>'
    for key in wdg_defaults:
        if key not in ['data', 'chart_type']:
            label = key
            item_string = False
            if isinstance(wdg[key], bmw.groups.AbstractGroup) and wdg[key].active != wdg_defaults[key]:
                if key.startswith('filter_'):
                    label = 'filter-' + wdg['heading_'+key].label
                item_string = ''
                active_indices = wdg[key].active
                for i in active_indices:
                    item_string += wdg[key].labels[i] + ', '
            elif isinstance(wdg[key], bmw.inputs.InputWidget) and wdg[key].value != wdg_defaults[key]:
                item_string = wdg[key].value
            if item_string is not False:
                if item_string == '':
                    item_string = 'NONE'
                output += '<div class="config-display-item"><span class="config-display-key">' + label + ': </span>' + item_string + '</div>'
    return output

def apply_aggregation(group, agg_method, y_a, y_b, y_c, wdg_range):
    """
    Helper function for pandas dataframe groupby object with apply function.

    Args:
        group (pandas dataframe): This has the data required for aggregations.
        agg_method (string): The aggregation method to apply.
        y_a (string): Name of the primary (a) column for which an aggregation is calculated.
        y_b (string): Name of column used for b factor in aggregation method.
        y_c (string): Name of column used for c factor in aggregation method.
        wdg_range (string): If within-series ranges are to be added, this will be 'Within Series'.
    Returns:
        (dataframe): The returned aggregation result, including series min and max if within-series range is to be added.
    """
    a = group[y_a]
    agg_result = None
    try:
        if agg_method == 'sum(a)':
            agg_result = a.sum()
        elif agg_method == 'ave(a)':
            agg_result = a.mean()
        elif agg_method == 'sum(a)/sum(b)':
            b = group[y_b]
            agg_result = a.sum() / b.sum()
        elif agg_method == 'sum(a*b)/sum(b)':
            b = group[y_b]
            agg_result = (a * b).sum() / b.sum()
        elif agg_method == 'sum(a*b)/sum(c)':
            b = group[y_b]
            c = group[y_c]
            agg_result = (a * b).sum() / c.sum()
        elif agg_method == '[sum(a*b)/sum(b)]/[sum(a*c)/sum(c)]':
            b = group[y_b]
            c = group[y_c]
            agg_result = ((a * b).sum() / b.sum())/((a * c).sum() / c.sum())
    except ZeroDivisionError:
        return pd.DataFrame({y_a: [None]})
    if wdg_range == 'Within Series':
        return pd.DataFrame({y_a: [agg_result], 'range_min': [a.min()], 'range_max': [a.max()]})
    else:
        return pd.DataFrame({y_a: [agg_result]})

def op_with_base(group, op, col, col_base, y_val):
    """
    Helper function for pandas dataframe groupby object with apply function. This returns a pandas
    dataframe with an operation applied to one of the columns.

    Args:
        group (pandas dataframe): This has columns required for performing the operation
        op (string): The type of operation: 'Difference', 'Ratio'
        col (string): The column across which the operation is happening
        col_base (string): The value of col to be used as the base for the operation, or "Consecutive" or "Total"
        y_val (string): Name of column that will be modified according to the operation.
    Returns:
        group_out (pandas dataframe): A like-indexed dataframe with the specified operations.
    """
    group_out = group.copy()
    if col_base == 'Consecutive':
        if op == 'Difference':
            group_out[y_val] = group[y_val] - group[y_val].shift()
        elif op == 'Ratio':
            group_out[y_val] = group[y_val] / group[y_val].shift()
    elif col_base == 'Total':
        if op == 'Difference':
            group_out[y_val] = group[y_val] - group[y_val].sum()
        elif op == 'Ratio':
            group_out[y_val] = group[y_val] / group[y_val].sum()
    else:
        df_base = group[group[col]==col_base]
        if df_base.empty:
            y_base = 0
        else:
            y_base = df_base[y_val].iloc[0]
        if op == 'Difference':
            group_out[y_val] = group[y_val] - y_base
        elif op == 'Ratio':
            group_out[y_val] = group[y_val] / y_base if y_base else 0
    return group_out

def prettify_numbers(number_list):
    str_list = []
    for x in number_list:
        if abs(x) < .001 or abs(x) >= 100000:
            s = '%.2E' % x
        else:
            s = round_to_n(x, 3)
        s = str(s)
        if s.endswith('.0'):
            s = s[:-2]
        str_list.append(s)
    return str_list

def round_to_n(x, n):
    #https://stackoverflow.com/questions/3410976/how-to-round-a-number-to-significant-figures-in-python
    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))

def update_data_type(attr, old, new):
    '''
    When data type is updated, clear the data source field, triggering update_data
    '''
    GL['data_source_wdg']['data'].value = ''

def update_data(attr, old, new):
    '''
    When data source is updated, call update_data_source()
    '''
    update_data_source()

def update_data_source(init_load=False, init_config={}):
    '''
    When data source is updated (or on initial load), update the widgets
    section of the layout based on if the input path is a csv, gdx, or model result.

    Args:
        init_load (boolean): True if this is the initial load of the page
        init_config (dict): Initial configuration supplied by the URL.
    Returns:
        Nothing: All plots are cleared, and widgets are set to accept further configuration.
    '''
    GL['widgets'] = GL['data_source_wdg'].copy()
    GL['custom_sorts'] = DEFAULT_CUSTOM_SORTS
    GL['custom_colors'] = DEFAULT_CUSTOM_COLORS
    reset_wdg_defaults()
    data_type = GL['data_source_wdg']['data_type'].value
    path = GL['data_source_wdg']['data'].value
    path = path.replace('"', '')
    if path == '':
        pass
    elif data_type == 'CSV':
        GL['widgets'].update(get_wdg_csv())
        GL['df_source'], GL['columns'] = get_df_csv(path)
        GL['widgets'].update(build_widgets(GL['df_source'], GL['columns'], init_load, init_config, wdg_defaults=GL['wdg_defaults']))
    elif data_type == 'GDX':
        GL['widgets'].update(get_wdg_gdx(path, GL['widgets']))
    elif data_type in DATA_TYPE_OPTIONS:
        rb.update_data_source(path, init_load, init_config, data_type)
    GL['controls'].children = list(GL['widgets'].values())
    GL['plots'].children = []

def update_wdg(attr, old, new):
    '''
    When general widgets are updated (not in WDG_COL), update plots only.
    '''
    if GL['widgets']['auto_update'].value == 'Enable':
        update_plots()

def update_wdg_col(attr, old, new):
    '''
    When widgets in WDG_COL are updated, set the options of all WDG_COL widgets,
    and update plots.
    '''
    set_wdg_col_options()
    if GL['widgets']['auto_update'].value == 'Enable':
        update_plots()

def update_adv_col(attr, old, new):
    update_adv_col_common('')

def update_adv_col2(attr, old, new):
    update_adv_col_common('2')

def update_adv_col3(attr, old, new):
    update_adv_col_common('3')

def update_adv_col_common(sfx):
    '''
    When adv_col is set, find unique values of adv_col in dataframe, and set adv_col_base with those values.
    '''
    wdg = GL['widgets']
    df = GL['df_source']
    if wdg['adv_col' + sfx].value != 'None':
        wdg['adv_col_base' + sfx].options = ['None'] + ADV_BASES + [str(i) for i in sorted(df[wdg['adv_col' + sfx].value].unique().tolist())]

def update_custom_styles(attr, old, new):
    #Apply custom styling sheet if it exists
    custom_style_path = GL['widgets']['custom_styles'].value.replace('"', '').strip()
    if custom_style_path != '':
        df_custom_styles = pd.read_csv(custom_style_path, low_memory=False)
        cols = [c for c in df_custom_styles if not c.endswith('_custom_colors')]
        for col in cols:
            cleaned_vals = [v for v in df_custom_styles[col].tolist() if str(v) != 'nan']
            GL['custom_sorts'][col] = cleaned_vals
            if col + '_custom_colors' in df_custom_styles:
                cleaned_colors = [v for v in df_custom_styles[col + '_custom_colors'].tolist() if str(v) != 'nan']
                GL['custom_colors'][col] = dict(zip(cleaned_vals, cleaned_colors))
    if GL['widgets']['auto_update'].value == 'Enable':
        update_plots()

def set_wdg_col_options():
    '''
    Limit available options for WDG_COL widgets based on their selected values, so that users
    cannot select the same value for two different WDG_COL widgets.
    '''
    cols = GL['columns']
    wdg = GL['widgets']
    #get list of selected values and use to reduce selection options.
    sels = [str(wdg[w].value) for w in WDG_COL if str(wdg[w].value) !='None']
    for w in WDG_COL:
        val = str(wdg[w].value)
        none_append = [] if val == 'None' else ['None']
        if w == 'x':
            opt_reduced = [x for x in cols['x-axis'] + ['histogram_x'] if x not in sels]
        elif w == 'y':
            opt_reduced = [x for x in cols['y-axis'] if x not in sels]
        else:
            opt_reduced = [x for x in cols['seriesable'] if x not in sels]
        wdg[w].options = [val] + opt_reduced + none_append

def update_plots():
    '''
    Make sure x axis and y axis are set. If so, set the dataframe for the plots and build them.
    '''
    #show widget config
    GL['widgets']['display_config'].text = display_config(GL['widgets'], GL['wdg_defaults'])

    #Exit if we haven't set both x and y
    if GL['widgets']['x'].value == 'None' or GL['widgets']['y'].value == 'None':
        GL['plots'].children = []
        return

    GL['df_plots'] = set_df_plots(GL['df_source'], GL['columns'], GL['widgets'], GL['custom_sorts'])
    if GL['widgets']['render_plots'].value == 'Yes':
        ncols = int(GL['widgets']['num_cols'].value)
        if GL['widgets']['chart_type'].value in ['Line Map','Area Map']:
            figs, breakpoints = create_maps(GL['df_plots'], GL['widgets'], GL['columns'])
            legend_text = build_map_legend(GL['widgets'], breakpoints)
        else:
            figs, ncols = create_figures(GL['df_plots'], GL['widgets'], GL['columns'], GL['custom_colors'])
            legend_text = build_plot_legend(GL['df_plots'], GL['widgets'], GL['custom_sorts'], GL['custom_colors'])
        GL['widgets']['legend'].text = legend_text
        GL['plots'].children = [bl.gridplot(figs, ncols=ncols)]

def download_url(dir_path='', auto_open=True):
    '''
    Export configuration URL query string and python dict formats to text file
    '''
    wdg = GL['widgets']
    wdg_defaults = GL['wdg_defaults']
    non_defaults = {}
    for key in wdg_defaults:
        if isinstance(wdg[key], bmw.groups.AbstractGroup) and wdg[key].active != wdg_defaults[key]:
            non_defaults[key] = wdg[key].active
        elif isinstance(wdg[key], bmw.inputs.InputWidget) and wdg[key].value != wdg_defaults[key] and key not in ['auto_update','presets','report_options','report_custom','report_format','report_base']:
            non_defaults[key] = wdg[key].value
    json_string = json.dumps(non_defaults)
    url_query = '?widgets=' + urlp.quote(json_string)
    prefix, suffix = get_prefix_suffix()
    if dir_path == '':
        path = out_path + '/' + prefix + 'url' + suffix + '.txt'
    else:
        path = dir_path + '/' + prefix + 'url.txt'
    with open(path, 'w') as f:
        f.write('Paste this after "/bokehpivot" in the URL:\n' + url_query + '\n\n')
    if auto_open:
        sp.Popen(os.path.abspath(path), shell=True)

def download_config(dir_path, auto_open, format):
    '''
    Export report configuration to python file
    '''
    wdg = GL['widgets']
    wdg_defaults = GL['wdg_defaults']
    non_defaults = {}
    if format == 'report':
        config_string = "{'name': 'Section Name', 'config': {"
    elif format == 'preset':
        config_string = "('Preset Name', {"
    filter_string = "'filter': {"
    for key in wdg_defaults:
        if isinstance(wdg[key], bmw.groups.AbstractGroup) and wdg[key].active != wdg_defaults[key] and key not in ['scenario_filter']:
            if key.startswith('filter_'):
                title = wdg['heading_'+key].text
                labels = ["'" + wdg[key].labels[i] + "'" for i in wdg[key].active]
                filter_string += "'" + title + "':[" + ",".join(labels) + "], "
            else:
                labels = ["'" + wdg[key].labels[i] + "'" for i in wdg[key].active]
                config_string += "'" + key + "':[" + ",".join(labels) + "], "
        elif isinstance(wdg[key], bmw.inputs.InputWidget) and wdg[key].value != wdg_defaults[key] and key not in ['data','auto_update','presets','report_options','report_custom','report_format','report_base']:
            raw_flag = ''
            if isinstance(wdg[key], bmw.inputs.TextInput):
                raw_flag = 'r'
            if key != 'result' or format != 'preset':
                config_string += "'" + key + "':" + raw_flag + "'" + str(wdg[key].value) + "', "

    if format == 'report':
        config_string += filter_string + '}}},'
        file_name = 'report'
    elif format == 'preset':
        config_string += filter_string + '}}),'
        file_name = 'preset'
    prefix, suffix = get_prefix_suffix()
    if dir_path == '':
        path = out_path + '/' + prefix + file_name + suffix + '.py'
    else:
        path = dir_path + '/' + prefix + file_name + '.py'
    with open(path, 'w') as f:
        if format == 'report':
            f.write('static_presets = [\n' + config_string + '\n]\n')
            f.write('#This file may be used directly as a custom report in the Build Report section of the interface, or the section above may be added to another custom report.\n')
        elif format == 'preset':
            f.write(config_string + '\n')
            f.write('#Add this to the "presets" section of the appropriate result.\n')
    if auto_open:
        sp.Popen(os.path.abspath(path), shell=True)

def download_report(dir_path='', auto_open=True):
    download_config(dir_path, auto_open, 'report')

def download_preset(dir_path='', auto_open=True):
    download_config(dir_path, auto_open, 'preset')

def download_csv(dir_path='', auto_open=True):
    '''
    Download a csv file of the currently viewed data to the downloads/ directory,
    with the current timestamp.
    '''
    logger.info('***Downloading View...')
    prefix, suffix = get_prefix_suffix()
    if dir_path == '':
        path = out_path + '/' + prefix + 'view' + suffix + '.csv'
    else:
        path = dir_path + '/' + prefix + 'view.csv'
    GL['df_plots'].to_csv(path, index=False)
    logger.info('***Done downloading View to ' + path)
    if auto_open:
        sp.Popen(os.path.abspath(path), shell=True)

def download_html(dir_path='', auto_open=True):
    '''
    Download html file of the currently viewed data to the downloads/ directory,
    with the current timestamp.
    '''
    logger.info('***Downloading View...')
    try:
        prefix, suffix = get_prefix_suffix()
        if dir_path == '':
            html_path = out_path + '/' + prefix + 'view' + suffix + '.html'
        else:
            html_path = dir_path + '/' + prefix + 'view.html'
        static_plots = []
        #Use fresh stylesheets for each document to avoid duplicate ownership errors.
        legend = bmw.Div(text=GL['widgets']['legend'].text, stylesheets=[_new_legend_css()])
        display_config = bmw.Div(text=GL['widgets']['display_config'].text, stylesheets=[_new_config_css()])
        plots = GL['plots'].children
        GL['plots'].children = []
        static_plots.append(bl.row(plots + [legend] + [display_config]))
        with open(this_dir_path + '/templates/index.html', 'r') as template_file:
            template_string=template_file.read()
        template = ji.Template(template_string)
        resources = br.Resources()
        html = be.file_html(static_plots, resources=resources, template=template)
        with open(html_path, 'w') as f:
            f.write(html)
        if auto_open:
            sp.Popen(os.path.abspath(html_path), shell=True)
        GL['plots'].children = plots
    except Exception as e:
        logger.info('***Warning: ' + str(e))
    logger.info('***Done downloading View to ' + html_path)
    update_plots()

def download_all():
    '''
    Download all of the outputs of a view into a timestamped folder
    '''
    prefix, suffix = get_prefix_suffix()
    dir_path = out_path + '/' + prefix + 'view' + suffix
    os.makedirs(dir_path)
    download_html(dir_path, False)
    download_csv(dir_path, False)
    download_url(dir_path, False)
    download_report(dir_path, False)
    download_preset(dir_path, False)

def download_source(dir_path='', auto_open=True):
    '''
    Download a csv file of the full data source to the downloads/ directory,
    with the current timestamp.
    '''
    logger.info('***Downloading full source...')
    prefix, suffix = get_prefix_suffix()
    if dir_path == '':
        path = out_path + '/' + prefix + 'source' + suffix + '.csv'
    else:
        path = dir_path + '/' + prefix + 'source.csv'
    GL['df_source'].to_csv(path, index=False)
    logger.info('***Done downloading full source to ' + path)
    if auto_open:
        sp.Popen(os.path.abspath(path), shell=True)

def get_prefix_suffix():
    if GL['widgets']['download_date'].value == 'Yes':
        suffix = '-' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    else:
        suffix = ''
    if GL['widgets']['download_prefix'].value != '':
        prefix = GL['widgets']['download_prefix'].value + '-'
    else:
        prefix = ''
    return prefix, suffix
