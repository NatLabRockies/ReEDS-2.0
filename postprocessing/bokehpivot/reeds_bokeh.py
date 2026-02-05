'''
ReEDS functions and globals for bokehpivot integration
'''
from __future__ import division

import os
import re
import copy
import platform
import pandas as pd
import collections
import bokeh.models.widgets as bmw
import sys
import reeds2 as rd2
import core
import datetime
import subprocess as sp
if sys.version_info[0] == 2:
    import gdx2py
import logging
from defaults import (DEFAULT_DOLLAR_YEAR, DEFAULT_PV_YEAR, DEFAULT_DISCOUNT_RATE, DEFAULT_END_YEAR)

this_dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(os.path.join(this_dir_path,'..','..')))
from reeds.io import read_output

logger = logging.getLogger('')
#ReEDS globals
#scenarios: each element is a dict with name of scenario and path to scenario
#result_dfs: keys are ReEDS result names. Values are dataframes for that result (with 'scenario' as one of the columns)
GL_REEDS = {'scenarios': [], 'result_dfs': {}}
GLRD = {}
GLDT = ''
reeds = None

def reeds_static(data_type, data_source, scenario_filter, diff, base, static_presets, report_path, report_format, html_num, output_dir, auto_open):
    '''
    Build static html and excel reports based on specified ReEDS presets
    Args:
        data_source (string): Path to ReEDS runs that will be included in report
        scenario_filter (string): either 'all' or a string of indices of chosen scenarios in scenario filter
        diff (string): Anything but 'No' will make additions/changes all results that lack the 'modify' key.
            E.g. 'Yes' means create additional sections for differences (for all results that lack the 'modify' key.)
        base (string): Identifier for base scenario, if making comparison charts
        static_presets (list of dicts): List of presets for which to make report. Each preset has these keys:
            'name' (required): Displayed name of the result
            'result' (optional): ReEDS result name in reeds.py.
            'preset' (optional): ReEDS result preset as defined in reeds.py
            'modify' (optional): Preset modifications. 'base_only' will show only the base case results, 'diff' will show the difference
                between each case and the base case, and any other string will simply leave the result as is (ignoring the diff argument)
            'config' (optional): Custom widget configuration. This configuration will be added on top of 'result', 'preset', 'modify', if they are present.
            'sheet_name' (optional): If specified, this is used for the excel sheet name for this preset. Must be unique.
            'download_full_source' (optional): If specified, this allows us to download the full data source, without creating a figure/view. If
                used, do not use 'preset', 'modify', or 'config'.
        report_path (string): The path to the report file.
        report_format (string): string that contains 'html', 'excel', 'csv', or a combination of these, specifying which reports to make.
        html_num (string): 'multiple' if we are building separate html reports for each section, and 'one' for one html report with all sections.
        output_dir (string): the directory into which the resulting reports will be saved.
        auto_open (string): either "Yes" to automatically open report files, or "No"
    Returns:
        Nothing: HTML and Excel files are created
    '''
    set_globs_by_type(data_type)
    core_presets = []

    #First, add difference sections to static_presets if diff is not 'No' and 'modify' is not already set for that preset
    if diff != 'No':
        i = 0
        while i < len(static_presets):
            if 'modify' not in static_presets[i]:
                if diff == 'Yes':
                    diff_preset = copy.deepcopy(static_presets[i])
                    diff_preset['name'] = diff_preset['name'] + ' - difference from ' + base
                    diff_preset['modify'] = 'diff'
                    if 'sheet_name' in diff_preset:
                        diff_preset['sheet_name'] += '_diff'
                    static_presets.insert(i+1,diff_preset)
                    i = i + 2
                elif diff == 'Base + Diff':
                    diff_preset = copy.deepcopy(static_presets[i])
                    static_presets[i]['name'] = static_presets[i]['name'] + ' - base'
                    static_presets[i]['modify'] = 'base_only'
                    if 'sheet_name' in static_presets[i]:
                        static_presets[i]['sheet_name'] += '_base'
                    diff_preset['name'] = diff_preset['name'] + ' - difference from ' + base
                    diff_preset['modify'] = 'diff'
                    if 'sheet_name' in diff_preset:
                        diff_preset['sheet_name'] += '_diff'
                    static_presets.insert(i+1,diff_preset)
                    i = i + 2
                elif diff == 'Diff Only':
                    static_presets[i]['name'] = static_presets[i]['name'] + ' - difference from ' + base
                    static_presets[i]['modify'] = 'diff'
                    if 'sheet_name' in static_presets[i]:
                        static_presets[i]['sheet_name'] += '_diff'
                    i = i + 1
            else:
                i = i + 1

    #Now convert each static_preset into a core_preset for use in core.static_report()
    for static_preset in static_presets:
        #build the full widget configuration for each preset.
        config = {'filter':{}}
        if 'result' in static_preset:
            config.update({'result': static_preset['result']})
            if 'preset' in static_preset:
                #deepcopy is needed to prevent 'filter', a key within the preset, from pointing to the same object in config as in the original preset dict in results_meta.
                preset_config = copy.deepcopy(reeds.results_meta[static_preset['result']]['presets'][static_preset['preset']])
                config.update(preset_config)
        if 'modify' in static_preset:
            if static_preset['modify'] == 'base_only':
                #if designated as base_only, filter to only include base scenario
                config['filter'].update({'scenario': [base]})
            elif static_preset['modify'] == 'diff':
                #find differences with base. First set x to 'None' to prevent updating, then reset x at the end of the widget updates.
                config.update({'adv_op3': 'Difference', 'adv_col3': 'scenario', 'adv_col_base3': base})
        if 'config' in static_preset:
            for key in static_preset['config']:
                if key == 'filter':
                    config['filter'].update(static_preset['config']['filter'])
                else:
                    config.update({key: static_preset['config'][key]})
        core_preset = {'name': static_preset['name'], 'config': config}
        if 'sheet_name' in static_preset:
            core_preset['sheet_name'] = static_preset['sheet_name']
        if 'download_full_source' in static_preset:
            core_preset['download_full_source'] = static_preset['download_full_source']
        core_presets.append(core_preset)

    #Now add variant wdg configurations:
    variant_wdg_config = []
    variant_wdg_config.append({'name':'var_dollar_year', 'val': str(DEFAULT_DOLLAR_YEAR), 'type': 'value'})
    variant_wdg_config.append({'name':'var_discount_rate', 'val': str(DEFAULT_DISCOUNT_RATE), 'type': 'value'})
    variant_wdg_config.append({'name':'var_pv_year', 'val': str(DEFAULT_PV_YEAR), 'type': 'value'})
    variant_wdg_config.append({'name':'var_end_year', 'val': str(DEFAULT_END_YEAR), 'type': 'value'})
    if scenario_filter != 'all':
        scenarios = list(map(int, scenario_filter.split(',')))
        variant_wdg_config.append({'name':'scenario_filter', 'val': scenarios, 'type': 'active'})
    core.static_report(data_type, data_source, core_presets, report_path, report_format, html_num, output_dir, auto_open, variant_wdg_config)

def get_wdg_reeds(path, init_load, wdg_config, wdg_defaults, custom_sorts, custom_colors):
    '''
    From data source path, fetch paths to scenarios and return dict of widgets for
    meta files, scenarios, and results

    Args:
        path (string): Path to a ReEDS run folder or a folder containing ReEDS runs folders.
        init_load (Boolean): True if this is the initial page load. False otherwise.
        wdg_config (dict): Initial configuration for widgets.
        wdg_defaults (dict): Keys are widget names and values are the default values of the widgets.
        custom_sorts (dict): Keys are column names. Values are lists of values in the desired sort order.
        custom_colors (dict): Keys are column names and values are dicts that map column values to colors (hex strings)

    Returns:
        topwdg (ordered dict): Dictionary of bokeh.model.widgets.
        scenarios (array of dicts): Each element is a dict with name of scenario and path to scenario.
    '''
    logger.info('***Fetching ReEDS scenarios...')
    topwdg = collections.OrderedDict()

    #Model Variables
    topwdg['reeds_vars'] = bmw.Button(label='Model Variables', css_classes=['reeds-vars-dropdown'], stylesheets=[core.DROPDOWN_CSS])
    topwdg['var_dollar_year'] = bmw.TextInput(title='Dollar Year', value=str(DEFAULT_DOLLAR_YEAR), css_classes=['wdgkey-dollar_year', 'reeds-vars-drop'], visible=False)
    topwdg['var_discount_rate'] = bmw.TextInput(title='Discount Rate', value=str(DEFAULT_DISCOUNT_RATE), css_classes=['wdgkey-discount_rate', 'reeds-vars-drop'], visible=False)
    topwdg['var_pv_year'] = bmw.TextInput(title='Present Value Reference Year', value=str(DEFAULT_PV_YEAR), css_classes=['wdgkey-pv_year', 'reeds-vars-drop'], visible=False)
    topwdg['var_end_year'] = bmw.TextInput(title='Present Value End Year', value=str(DEFAULT_END_YEAR), css_classes=['wdgkey-end_year', 'reeds-vars-drop'], visible=False)

    #Meta widgets
    topwdg['meta'] = bmw.Button(label='Meta', css_classes=['meta-dropdown'], stylesheets=[core.DROPDOWN_CSS])
    for col in reeds.columns_meta:
        if 'map' in reeds.columns_meta[col]:
            topwdg['meta_map_'+col] = bmw.TextInput(title='"'+col+ '" Map', value=reeds.columns_meta[col]['map'], css_classes=['wdgkey-meta_map_'+col, 'meta-drop'], visible=False)
        if 'join' in reeds.columns_meta[col]:
            topwdg['meta_join_'+col] = bmw.TextInput(title='"'+col+ '" Join', value=reeds.columns_meta[col]['join'], css_classes=['wdgkey-meta_join_'+col, 'meta-drop'], visible=False)
        if 'style' in reeds.columns_meta[col]:
            topwdg['meta_style_'+col] = bmw.TextInput(title='"'+col+ '" Style', value=reeds.columns_meta[col]['style'], css_classes=['wdgkey-meta_style_'+col, 'meta-drop'], visible=False)

    #Filter Scenarios widgets and Result widget
    scenarios = []
    runs_paths = path.split('|')
    for runs_path in runs_paths:
        runs_path = runs_path.replace('"', '')
        runs_path = runs_path.strip()
        if not os.path.exists(runs_path):
            raise FileNotFoundError(f"The specified path does not exist: {runs_path}")
        #if the path is pointing to a csv file, gather all scenarios from that file
        if os.path.isfile(runs_path) and runs_path.lower().endswith('.csv'):
            custom_sorts['scenario'] = []
            abs_path = str(os.path.abspath(runs_path))
            df_scen = pd.read_csv(abs_path)
            if 'color' in df_scen:
                custom_colors['scenario'] = {}
            for i_scen, scen in df_scen.iterrows():
                if os.path.isdir(scen['path']):
                    abs_path_scen = os.path.abspath(scen['path'])
                    if any(os.path.isfile(abs_path_scen + GLRD['output_subdir'] + test_file) for test_file in GLRD['test_file']):
                        custom_sorts['scenario'].append(scen['name'])
                        scenarios.append({'name': scen['name'], 'path': abs_path_scen})
                        if 'color' in df_scen:
                            custom_colors['scenario'][scen['name']] = scen['color']
        #Else if the path is pointing to a directory, check if the directory is a run folder
        #containing GLRD['output_subdir'] and use this as the lone scenario. Otherwise, it must contain
        #run folders, so gather all of those scenarios.
        elif os.path.isdir(runs_path):
            abs_path = str(os.path.abspath(runs_path))
            if any(os.path.isfile(abs_path + GLRD['output_subdir'] + test_file) for test_file in GLRD['test_file']):
                scenarios.append({'name': os.path.basename(abs_path), 'path': abs_path})
            else:
                subdirs = next(os.walk(abs_path))[1]
                for subdir in subdirs:
                    if any(os.path.isfile(abs_path + '/' + subdir + GLRD['output_subdir'] + test_file)
                            for test_file in GLRD['test_file']):
                        abs_subdir = str(os.path.abspath(abs_path+'/'+subdir))
                        scenarios.append({'name': subdir, 'path': abs_subdir})
    #If we have scenarios, build widgets for scenario filters and result.
    for key in ["scenario_filter_dropdown", "scenario_filter", "result"]:
        topwdg.pop(key, None)
    if scenarios:
        labels = [a['name'] for a in scenarios]
        topwdg['scenario_filter_dropdown'] = bmw.Button(label='Filter Scenarios', css_classes=['scenario-filter-dropdown'], stylesheets=[core.DROPDOWN_CSS])
        topwdg['scenario_filter_sel_all'] = bmw.Button(label='Select All', button_type='success', css_classes=['scenario-filter-drop','select-all-none'], visible=False)
        topwdg['scenario_filter_sel_none'] = bmw.Button(label='Select None', button_type='success', css_classes=['scenario-filter-drop','select-all-none'], visible=False)
        topwdg['scenario_filter'] = bmw.CheckboxGroup(labels=labels, active=list(range(len(labels))), css_classes=['scenario-filter-drop'], visible=False)
        #Add code to build report
        options = [o for o in os.listdir(this_dir_path+'/reports/templates'+GLRD['report_subdir']) if o.endswith(".py")]
        options = ['custom'] + options
        scenario_names = [i['name'] for i in scenarios]
        topwdg['report_dropdown'] = bmw.Button(label='Build Report', css_classes=['report-dropdown'], stylesheets=[core.DROPDOWN_CSS])
        topwdg['report_options'] = bmw.Select(title='Report', value=options[0], options=options, css_classes=['report-drop'], visible=False)
        topwdg['report_custom'] = bmw.TextInput(title='If custom, enter path to file', value='', css_classes=['report-drop'], visible=False)
        topwdg['report_format'] = bmw.TextInput(title='Enter type(s) of report (html,excel,csv)', value='html,excel', css_classes=['report-drop'], visible=False)
        topwdg['report_diff'] = bmw.Select(title='Add Differences', value='No', options=['No','Yes','Base + Diff','Diff Only'], css_classes=['report-drop'], visible=False)
        topwdg['report_base'] = bmw.Select(title='Base Case For Differences', value=scenario_names[0], options=scenario_names, css_classes=['report-drop'], visible=False)
        topwdg['report_debug'] = bmw.Select(title='Debug Mode', value='No', options=['Yes','No'], css_classes=['report-drop'], visible=False)
        topwdg['report_build'] = bmw.Button(label='Build Report', button_type='success', css_classes=['report-drop'], visible=False)
        topwdg['report_build_separate'] = bmw.Button(label='Build Separate Reports', button_type='success', css_classes=['report-drop'], visible=False)

        topwdg['result'] = bmw.Select(title='Result', value='None', options=['None']+list(reeds.results_meta.keys()), css_classes=['wdgkey-result'])
    # Attach dropdown behavior
    core.attach_dropdown_callbacks(topwdg)
    #save defaults
    core.save_wdg_defaults(topwdg, wdg_defaults)
    #set initial config
    if init_load:
        core.initialize_wdg(topwdg, wdg_config)
    #Add update functions
    for key in topwdg:
        if key.startswith('meta_'):
            topwdg[key].on_change('value', update_reeds_meta)
        elif key.startswith('var_'):
            topwdg[key].on_change('value', update_reeds_var)
    topwdg['scenario_filter_sel_all'].on_click(scenario_filter_select_all)
    topwdg['scenario_filter_sel_none'].on_click(scenario_filter_select_none)
    topwdg['report_build'].on_click(build_reeds_report)
    topwdg['report_build_separate'].on_click(build_reeds_report_separate)
    topwdg['result'].on_change('value', update_reeds_result)
    logger.info('***Done fetching ReEDS scenarios.')
    return (topwdg, scenarios)

def scenario_filter_select_all():
    core.GL['widgets']['scenario_filter'].active = list(range(len(core.GL['widgets']['scenario_filter'].labels)))

def scenario_filter_select_none():
    core.GL['widgets']['scenario_filter'].active = []

def get_reeds_data(topwdg, scenarios, result_dfs):
    '''
    For a selected ReEDS result and set of scenarios, fetch gdx data,
    preprocess it, and add to global result_dfs dictionary if the data
    hasn't already been fetched.

    Args:
        topwdg (ordered dict): ReEDS widgets (meta widgets, scenarios widget, result widget)
        scenarios (array of dicts): Each element is a dict with name of scenario and path to scenario.
        result_dfs (dict): Keys are ReEDS result names. Values are dataframes for that result (with 'scenario' as one of the columns)

    Returns:
        Nothing: result_dfs is modified
    '''
    result = topwdg['result'].value
    logger.info('***Fetching ' + str(result) + ' for selected scenarios...')
    startTime = datetime.datetime.now()
    #A result has been selected, so either we retrieve it from result_dfs,
    #which is a dict with one dataframe for each result, or we make a new key in the result_dfs
    if result not in result_dfs:
        result_dfs[result] = None
        cur_scenarios = []
    else:
        cur_scenarios = result_dfs[result]['scenario'].unique().tolist() #the scenarios that have already been retrieved and stored in result_dfs
        #remove scenarios that are not ative
        active_scenarios = [scenarios[i]['name'] for i in topwdg['scenario_filter'].active]
        result_dfs[result] = result_dfs[result][result_dfs[result]['scenario'].isin(active_scenarios)]

    #For each selected scenario, retrieve the data from gdx if we don't already have it,
    #and update result_dfs with the new data.
    result_meta = reeds.results_meta[result]
    for i in topwdg['scenario_filter'].active:
        scenario_name = scenarios[i]['name']
        if scenario_name not in cur_scenarios:
            #get the gdx result and preprocess
            if 'sources' in result_meta:
                #If we have multiple parameters as data sources, we must gather them all, and the first preprocess
                #function (which is necessary) will accept a dict of dataframes and return a combined dataframe.
                df_scen_result = {}
                for src in result_meta['sources']:
                    df_scen_result[src['name']] = get_src(scenarios[i], src)
            else:
                #else we have only one parameter as a data source
                df_scen_result = get_src(scenarios[i], result_meta)
            #preprocess and return one dataframe
            if 'preprocess' in result_meta:
                for preprocess in result_meta['preprocess']:
                    df_scen_result = preprocess['func'](df_scen_result, **preprocess['args'])
            #preprocess columns in this dataframe
            for col in df_scen_result.columns.values.tolist():
                if col in reeds.columns_meta and 'preprocess' in reeds.columns_meta[col]:
                    for preprocess in reeds.columns_meta[col]['preprocess']:
                        df_scen_result[col] = preprocess(df_scen_result[col])
            df_scen_result['scenario'] = scenario_name
            if result_dfs[result] is None:
                result_dfs[result] = df_scen_result
            else:
                result_dfs[result] = pd.concat([result_dfs[result], df_scen_result]).reset_index(drop=True)
        logger.info('***Done fetching ' + str(result) + ' for ' + str(scenario_name) + '.')

    #fill missing values with 0:
    df = result_dfs[result]
    if 'index' in result_meta:
        idx_cols = ['scenario'] + result_meta['index']
        df =  df.groupby(idx_cols, sort=False, as_index =False).sum()
        full_idx = pd.MultiIndex.from_product([df[col].unique().tolist() for col in idx_cols], names=idx_cols)
        result_dfs[result] = df.set_index(idx_cols).reindex(full_idx).reset_index()
    logger.info('***Done fetching ' + str(result) + ': ' + str(datetime.datetime.now() - startTime))

def get_src(scen, src):
    '''
    For a given scenario and data source, fetch gdx or csv data and do common
    pre-processing (remove Eps, coerce numeric columns to numeric, and lowercase everything)

    Args:
        scen (dict): Scenario dictionary. Keys are 'name' and 'path'.
        src (dict): Source Dictionary. Keys are 'file', 'param' (for gdx sources), and 'columns' (optional for csv sources)

    Returns:
        df_src (pandas dataframe): A dataframe of the source
    '''
    filepath = scen['path'] + GLRD['output_subdir'] + src['file']
    if src['file'].endswith('.gdx'):
        data = gdx2py.par2list(filepath, src['param'])
        df_src = pd.DataFrame(data)
        df_src.columns = src['columns']
    elif src['file'].endswith('.csv'):
        if 'header' in src and src['header'] == None:
            df_src = pd.read_csv(filepath, low_memory=False, header=None)
        else:
            df_src = pd.read_csv(filepath, low_memory=False)
    else:
        df_src = read_output(scen['path'], filepath)
    if 'transpose' in src and src['transpose'] is True:
        df_src = df_src.T
    if 'columns' in src:
        df_src.columns = src['columns']
    df_src.replace('Eps',0, inplace=True)
    df_src.replace('Undf',0, inplace=True)
    df_src = df_src.apply(pd.to_numeric, errors='ignore')
    df_src = df_to_lowercase(df_src)
    return df_src


def process_reeds_data(topwdg, custom_sorts, custom_colors, result_dfs):
    '''
    Apply joins, mappings, ordering data to a selected result dataframe.
    Also categorize the columns of the dataframe and fill NA values.

    Args:
        topwdg (ordered dict): ReEDS widgets (meta widgets, scenarios widget, result widget)
        custom_sorts (dict): Keys are column names. Values are lists of values in the desired sort order.
        custom_colors (dict): Keys are column names and values are dicts that map column values to colors (hex strings)
        result_dfs (dict): Keys are ReEDS result names. Values are dataframes for that result (with 'scenario' as one of the columns)

    Returns:
        df (pandas dataframe): A dataframe of the ReEDS result, with filled NA values.
        cols (dict): Keys are categories of columns of df_source, and values are a list of columns of that category.
    '''
    logger.info('***Apply joins, maps, ordering to ReEDS data...')
    startTime = datetime.datetime.now()
    df = result_dfs[topwdg['result'].value].copy()
    #apply joins
    for col in df.columns.values.tolist():
        if 'meta_join_'+col in topwdg and topwdg['meta_join_'+col].value != '':
            join_file = topwdg['meta_join_'+col].value.replace('"','')
            if col in reeds.columns_meta and 'join_in_run' in reeds.columns_meta[col] and reeds.columns_meta[col]['join_in_run'] is True:
                join_file = f"{GL_REEDS['scenarios'][0]['path']}/{join_file}" #Using the first run's join file
            df_join = pd.read_csv(join_file)
            #reduce columns and rename if specified in model (called "reeds" currently)
            if col in reeds.columns_meta and 'join_keep_cols' in reeds.columns_meta[col]:
                keep_cols = [i for i in df_join.columns if i in reeds.columns_meta[col]['join_keep_cols']]
                df_join = df_join[keep_cols].copy()
            if col in reeds.columns_meta and 'join_col_rename' in reeds.columns_meta[col]:
                df_join = df_join.rename(columns=reeds.columns_meta[col]['join_col_rename'], errors='ignore')
            if col in reeds.columns_meta and 'join_col_lowercase' in reeds.columns_meta[col]:
                df_join[reeds.columns_meta[col]['join_col_lowercase']] = df_join[reeds.columns_meta[col]['join_col_lowercase']].apply(lambda x: x.str.lower())
            #remove duplicate rows. Note that we will have issues when the mapping is
            #many to many instead of many to one. For example, if the source data regionality is state, texas will be
            #assigned to just one rto after removing duplicates, even though it is truly part of multiple rtos.
            df_join.drop_duplicates(subset=col, inplace=True)
            #merge df_join into df (for which all values have been lowercased)
            df_join[col] = df_join[col].str.lower()
            df = pd.merge(left=df, right=df_join, on=col, how='left', sort=False)

    #Apply mappings, allowing wildcard *. Order matters here, the first match is used.
    for col in df.columns.values.tolist():
        if 'meta_map_'+col in topwdg and topwdg['meta_map_'+col].value != '':
            df_map = pd.read_csv(topwdg['meta_map_'+col].value.replace('"',''))
            #Use regex, replacing * with .*
            df_map['raw'] = '^' + df_map['raw'] + '$'
            df_map['raw'] = df_map['raw'].str.replace('*', '.*', regex=False)
            #now map from raw to display, but keep original column as "[column]_raw"
            df[col + '_raw'] = df[col]
            #Pre-compile regex patterns
            map_patterns = [(re.compile(pattern), display) for pattern, display in zip(df_map['raw'], df_map['display'])]
            #Define a function to match once
            def map_value(val):
                for pattern, display in map_patterns:
                    if pattern.match(str(val)):
                        return display
                return val  # if no match, keep original
            #Apply function
            df[col] = df[col].apply(map_value)

    #apply custom styling
    non_scen_col = [c for c in df.columns.values.tolist() if c != 'scenario']
    for col in non_scen_col:
        custom_sorts.pop(col, None)
        custom_colors.pop(col, None)
        if 'meta_style_'+col in topwdg and topwdg['meta_style_'+col].value != '':
            df_style = pd.read_csv(topwdg['meta_style_'+col].value.replace('"',''))
            custom_sorts[col] = df_style['order'].tolist()
            if 'color' in df_style:
                custom_colors[col] = dict(zip(df_style['order'],df_style['color']))
            #find values that aren't styled and set default color (hot pink) and order (at end) for these
            for val in df[col].unique().tolist():
                if val not in custom_sorts[col]:
                    custom_sorts[col] = custom_sorts[col] + [val]
                    if 'color' in df_style:
                        custom_colors[col][val] = '#ff69b4'

    #convert columns to specified type
    cols = {}
    cols['all'] = df.columns.values.tolist()
    for c in cols['all']:
        if c in reeds.columns_meta and 'type' in reeds.columns_meta[c]:
            if reeds.columns_meta[c]['type'] == 'number':
                df[c] = pd.to_numeric(df[c], errors='coerce')
            elif reeds.columns_meta[c]['type'] == 'string':
                df[c] = df[c].astype(str)

    #categorize columns
    cols['discrete'] = [x for x in cols['all'] if df[x].dtype == object]
    cols['continuous'] = [x for x in cols['all'] if x not in cols['discrete']]
    cols['y-axis'] = [x for x in cols['continuous'] if not (x in reeds.columns_meta and 'y-allow' in reeds.columns_meta[x] and reeds.columns_meta[x]['y-allow'] is False)]
    cols['x-axis'] = [x for x in cols['all'] if x not in cols['y-axis']]
    cols['filterable'] = ([x for x in cols['discrete'] if not (x in reeds.columns_meta and 'filterable' in reeds.columns_meta[x] and reeds.columns_meta[x]['filterable'] is False)]+
                         [x for x in cols['continuous'] if x in reeds.columns_meta and 'filterable' in reeds.columns_meta[x] and reeds.columns_meta[x]['filterable'] is True])
    cols['seriesable'] = ([x for x in cols['discrete'] if not (x in reeds.columns_meta and 'seriesable' in reeds.columns_meta[x] and reeds.columns_meta[x]['seriesable'] is False)]+
                         [x for x in cols['continuous'] if x in reeds.columns_meta and 'seriesable' in reeds.columns_meta[x] and reeds.columns_meta[x]['seriesable'] is True])

    #fill NA depending on column type
    df[cols['discrete']] = df[cols['discrete']].fillna('{BLANK}')
    df[cols['continuous']] = df[cols['continuous']].fillna(0)
    logger.info('***Done with joins, maps, ordering: ' + str(datetime.datetime.now() - startTime))
    return (df, cols)

def build_reeds_presets_wdg(preset_options):
    '''
    Build the presets widget

    Args:
        preset_options (list): List of strings for preset selections.

    Returns:
        wdg (ordered dict): Dictionary of bokeh.model.widgets, with 'presets' as the only key.
    '''
    wdg = collections.OrderedDict()
    wdg['presets'] = bmw.Select(title='Presets', value='None', options=['None'] + preset_options, css_classes=['wdgkey-presets'])
    wdg['presets'].on_change('value', update_reeds_presets)
    return wdg

def update_data_source(path, init_load, init_config, data_type):
    '''
    Respond to updates of data_source_wdg which are identified as ReEDS paths

    Args:
        path: The updated value of data_source_wdg
        init_load (boolean): True if this is the initial load of the page
        init_config (dict): Initial configuration supplied by the URL.

    Returns:
        Nothing: Core Globals are updated
    '''
    set_globs_by_type(data_type)
    GL_REEDS['result_dfs'] = {}
    GL_REEDS['scenarios'] = []
    core.GL['variant_wdg'], GL_REEDS['scenarios'] = get_wdg_reeds(path, init_load, init_config, core.GL['wdg_defaults'], core.GL['custom_sorts'], core.GL['custom_colors'])
    core.GL['widgets'].update(core.GL['variant_wdg'])
    #if this is the initial load, we need to build the rest of the widgets if we've selected a result.
    if init_load and core.GL['variant_wdg']['result'].value != 'None':
        get_reeds_data(core.GL['variant_wdg'], GL_REEDS['scenarios'], GL_REEDS['result_dfs'])
        core.GL['df_source'], core.GL['columns'] = process_reeds_data(core.GL['variant_wdg'], core.GL['custom_sorts'], core.GL['custom_colors'], GL_REEDS['result_dfs'])
        preset_options = []
        if 'presets' in reeds.results_meta[core.GL['variant_wdg']['result'].value]:
            preset_options = list(reeds.results_meta[core.GL['variant_wdg']['result'].value]['presets'].keys())
        core.GL['widgets'].update(build_reeds_presets_wdg(preset_options))
        core.GL['widgets'].update(core.build_widgets(core.GL['df_source'], core.GL['columns'], init_load, init_config, wdg_defaults=core.GL['wdg_defaults']))

def set_globs_by_type(data_type):
    global GLDT, reeds, GLRD
    GLDT = data_type
    reeds = rd2
    GLRD = reeds.rb_globs

def update_reeds_var(attr, old, new):
    '''
    When ReEDS var fields are updated, call update_reeds_wdg with the 'vars' flag
    '''
    update_reeds_wdg(wdg_type='vars')

def update_reeds_meta(attr, old, new):
    '''
    When ReEDS meta fields are updated, call update_reeds_wdg with the 'meta' flag
    '''
    update_reeds_wdg(wdg_type='meta')

def update_reeds_result(attr, old, new):
    '''
    When ReEDS Result field is updated, call update_reeds_wdg with the 'result' flag
    '''
    update_reeds_wdg(wdg_type='result')

def build_reeds_report(html_num='one'):
    '''
    Build the chosen ReEDS report. Note that Base Case is irrelevant for certain reports, but necessary for others.
    Args:
        html_num (string): 'multiple' if we are building separate html reports for each section, and 'one' for one html report with all sections.
    '''
    data_type = '"' + GLDT + '"'
    diff = '"' + core.GL['widgets']['report_diff'].value + '"'
    base = '"' + core.GL['widgets']['report_base'].value + '"'
    if core.GL['widgets']['report_options'].value == 'custom':
        report_path = core.GL['widgets']['report_custom'].value
        report_path = report_path.replace('"', '')
    else:
        report_path = this_dir_path + '/reports/templates'+GLRD['report_subdir']+'/'+ core.GL['widgets']['report_options'].value
    report_path = '"' + report_path + '"'
    report_format = '"' + core.GL['widgets']['report_format'].value + '"'
    time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_dir = '"' + core.out_path + '/report-' + time + '"'
    data_source = '"' + core.GL['widgets']['data'].value.replace('"', '') + '"'
    scenario_filter_str = ','.join(str(e) for e in core.GL['widgets']['scenario_filter'].active)
    scenario_filter_str = '"' + scenario_filter_str + '"'
    if html_num == 'one':
        auto_open = '"Yes"'
    else:
        auto_open = '"No"'

    if platform.system() == 'Windows':
        start_str = 'start python'
    else:
        start_str = 'python'
    if core.GL['widgets']['report_debug'].value == 'Yes':
        if platform.system() == 'Windows':
            start_str = 'start cmd /K python -m pdb '
        else:
            start_str = 'python -m pdb '
    sp.call(start_str + ' "' + this_dir_path + '/reports/interface_report_model.py" ' + data_type + ' ' + data_source + ' ' + scenario_filter_str + ' ' + diff + ' ' + base + ' ' + report_path + ' ' + report_format + ' "' + html_num + '" ' + output_dir + ' ' + auto_open, shell=True)

def build_reeds_report_separate():
    '''
    Build the chosen ReEDS report with separate html files for each section of the report.
    '''
    build_reeds_report(html_num='multiple')

def update_reeds_wdg(wdg_type):
    '''
    When ReEDS result field or meta field are updated, build core widgets accordingly
    
    Args:
        wdg_type (string): 'meta' or 'result'. Indicates the type of widget that was changed.
    '''
    core.GL['widgets'] = core.GL['data_source_wdg'].copy()
    core.GL['widgets'].update(core.GL['variant_wdg'])
    if wdg_type == 'vars':
        GL_REEDS['result_dfs'] = {}
    for key in list(core.GL['wdg_defaults'].keys()):
        if key not in list(core.GL['variant_wdg'].keys()) + ['data']:
            core.GL['wdg_defaults'].pop(key, None)
    if 'result' in core.GL['variant_wdg'] and core.GL['variant_wdg']['result'].value != 'None':
        preset_options = []
        if wdg_type in ['result','vars']:
            get_reeds_data(core.GL['variant_wdg'], GL_REEDS['scenarios'], GL_REEDS['result_dfs'])
        if 'presets' in reeds.results_meta[core.GL['variant_wdg']['result'].value]:
            preset_options = list(reeds.results_meta[core.GL['variant_wdg']['result'].value]['presets'].keys())
        core.GL['df_source'], core.GL['columns'] = process_reeds_data(core.GL['variant_wdg'], core.GL['custom_sorts'], core.GL['custom_colors'], GL_REEDS['result_dfs'])
        core.GL['widgets'].update(build_reeds_presets_wdg(preset_options))
        core.GL['widgets'].update(core.build_widgets(core.GL['df_source'], core.GL['columns'], wdg_defaults=core.GL['wdg_defaults']))
    core.GL['controls'].children = list(core.GL['widgets'].values())
    core.GL['plots'].children = []

def update_reeds_presets(attr, old, new):
    '''
    When ReEDS preset is selected, clear all filter and main selectors, and set them
    to the state specified in the preset in reeds.py
    '''
    wdg = core.GL['widgets']
    preset = reeds.results_meta[wdg['result'].value]['presets'][wdg['presets'].value]
    core.preset_wdg(preset)

def df_to_lowercase(df):
    for col in df:
        if df[col].dtype == object:
            df[col] = df[col].str.lower()
    return df