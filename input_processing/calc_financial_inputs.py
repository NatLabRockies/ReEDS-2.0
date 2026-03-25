#%% Imports
import pandas as pd
import numpy as np
import os
import support_functions as sFuncs
# Time the operation of this script
from ticker import toc, makelog
import datetime


#%% Functions
def calc_financial_inputs(reeds_path, inputs_case):
    """
    Write the following files to runs/{batch_case}/inputs_case/:
    - ivt.csv
    - ptc_values.csv
    - ptc_value_scaled.csv
    - itc_fractions.csv
    - depreciation_schedules.csv
    - inflation.csv
    - cap_cost_mult_noITC.csv
    - crf.csv
    - pvf_onm_int.csv
    - pvf_cap.csv
    - reg_cap_cost_mult.csv
    - retail_eval_period.h5
    - retail_depreciation_sch.h5
    """
    print('Starting calculation of financial parameters for', inputs_case)

    # #%% Inputs for testing
    # reeds_path = '/Users/pbrown/github/ReEDS-2.0/'
    # inputs_case = os.path.join(reeds_path,'runs','v20220621_NTPm0_ercot_seq_test','inputs_case')

    #%% Input processing
    switches = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True,
    )

    input_dir = os.path.join(reeds_path, 'inputs')
    switches['endyear'] = int(switches['endyear'])
    switches['sys_eval_years'] = int(switches['sys_eval_years'])

    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, names=['scalar','value','comment'], index_col='scalar')['value']

    #%% Import some general data and maps

    # Import inflation (which includes both historical and future inflation). 
    # Used for adjusting currency inputs to the specified dollar year, and financial calculations. 
    inflation_df = pd.read_csv(os.path.join(
        input_dir, 'financials', 'inflation_%s.csv' % switches['inflation_suffix']))

    # Import tech groups. Used to expand data inputs 
    # (e.g., 'UPV' expands to all of the upv subclasses, like upv_1, upv_2, etc)
    tech_groups = sFuncs.import_tech_groups(os.path.join(input_dir, 'tech-subset-table.csv'))

    # Set up scen_settings object
    scen_settings = sFuncs.scen_settings(
        dollar_year=int(switches['dollar_year']), tech_groups=tech_groups, input_dir=input_dir,
        switches=switches)


    #%% Ingest data, determine what regions have been specified, and build df_ivt
    # Build df_ivt (for calculating various parameters at subscript [i,v,t])

    techs = pd.read_csv(
        os.path.join(input_dir, 'techs', 'techs_%s.csv' % switches['techs_suffix']))
    techs = sFuncs.expand_GAMS_tech_groups(techs)
    vintage_definition = pd.read_csv(os.path.join(inputs_case, 'ivt.csv')).rename(columns={'Unnamed: 0':'i'})

    annual_degrade = pd.read_csv(
        os.path.join(input_dir,'degradation',
                     'degradation_annual_%s.csv' % switches['degrade_suffix']),
        header=None, names=['i','annual_degradation'])
    annual_degrade = sFuncs.expand_GAMS_tech_groups(annual_degrade)
    ### Assign the PV+battery values to values for standalone batteries
    annual_degrade = sFuncs.append_pvb_parameters(
        dfin=annual_degrade, 
        tech_to_copy='battery_{}'.format(scen_settings.switches['GSw_PVB_Dur']))

    years, modeled_years, year_map = sFuncs.ingest_years(
        inputs_case, switches['sys_eval_years'], switches['endyear'])

    val_r = pd.read_csv(os.path.join(inputs_case,'val_r.csv'), header = None)[0].tolist()

    df_ivt = sFuncs.build_dfs(years, techs, vintage_definition, year_map)
    print('df_ivt created for', inputs_case)


    #%% Import and merge data onto df_ivt

    # Import system-wide real discount rates, calculate present-value-factors, merge onto df's
    financials_sys = sFuncs.import_sys_financials(
        switches['financials_sys_suffix'], inflation_df, modeled_years, 
        years, year_map, switches['sys_eval_years'], scen_settings, scalars['co2_capture_incentive_length'])
    df_ivt = df_ivt.merge(
        financials_sys[['t', 'pvf_capital', 'crf', 'crf_co2_incentive', 'd_real', 'd_nom', 'interest_rate_nom', 
                        'tax_rate', 'debt_fraction', 'rroe_nom']], 
        on=['t'], how='left')

    # The script only works for USA currently. Something needs to be added here
    # to expand to other countries, if needed. 
    df_ivt['country'] = 'usa'


    # Merge inflation into investment df
    df_ivt = df_ivt.merge(inflation_df, on=['t'], how='left', )

    # Merge annual degradation into investment df
    df_ivt = df_ivt.merge(annual_degrade, on=['i'], how='left')
    df_ivt['annual_degradation'] = df_ivt['annual_degradation'].fillna(0.0)
    
    ### Import financial assumptions
    financials_tech = sFuncs.import_data(
        file_root='financials_tech', file_suffix=switches['financials_tech_suffix'], 
        indices=['i','country','t'], scen_settings=scen_settings)
    # Apply the values for standalone batteries to PV+B batteries
    financials_tech = sFuncs.append_pvb_parameters(
        dfin=financials_tech, 
        tech_to_copy='battery_{}'.format(scen_settings.switches['GSw_PVB_Dur']))
    # If the battery in PV+B gets the ITC, it gets 5-year MACRS depreciation as well
    if float(scen_settings.switches['GSw_PVB_ITC_Qual_Award']) >= 0.75:
        financials_tech.loc[
            financials_tech.i.str.startswith('pvb') & (financials_tech.country == 'usa'),
            'depreciation_sch'
        ] = 5

    ### Project financials_tech forward
    financials_tech_projected = financials_tech.pivot(
        index=['i','country','depreciation_sch','eval_period','construction_sch'], 
        columns=['t'])['finance_diff_real']
    lastdatayear = max(financials_tech_projected.columns)
    for addyear in range(lastdatayear+1, switches['endyear']+1):
        financials_tech_projected[addyear] = financials_tech_projected[lastdatayear]
    # Overwrite with projected values
    financials_tech = financials_tech_projected.stack().rename('finance_diff_real').reset_index()
    # Merge with df_ivt
    df_ivt = df_ivt.merge(financials_tech, on=['i', 't', 'country'], how='left')
    
    # Calculate multipliers to account for evaluation periods. If a tech's eval period is
    # the system-wide default, this will be 1. If not, the capital costs are adjusted accordingly. 
    financials_sys['sys_pvf_eval_period_sum'] = (1 - (1 / (financials_sys['d_real'])**(switches['sys_eval_years']-1))) / (financials_sys['d_real']-1.0) + 1
    df_ivt['pvf_eval_period_sum'] = (1 - (1 / (df_ivt['d_real'])**(df_ivt['eval_period']-1))) / (df_ivt['d_real']-1.0) + 1
    df_ivt = df_ivt.merge(financials_sys[['sys_pvf_eval_period_sum', 't']], on='t', how='left')
    df_ivt['eval_period_adj_mult'] = df_ivt['sys_pvf_eval_period_sum'] / df_ivt['pvf_eval_period_sum']

    #%% Process incentives
    
    # Import incentives, shift eligibility by safe harbor, merge incentives
    incentive_df = sFuncs.import_and_mod_incentives(
        incentive_file_suffix=switches['incentives_suffix'], 
        construction_times_suffix=switches['construction_times_suffix'],
        inflation_df=inflation_df, scen_settings=scen_settings)
    df_ivt = df_ivt.merge(incentive_df, on=['i', 't', 'country'], how='left')
    df_ivt['safe_harbor_max'] = df_ivt['safe_harbor_max'].fillna(0.0)
    df_ivt['co2_capture_value_monetized'] = df_ivt['co2_capture_value_monetized'].fillna(0.0) * (1 / (1 - df_ivt['tax_rate']))
    
    ### Calculate the tax impacts of the PTC, and calculate the adjustment to reflect the 
    # difference between the PTC duration and ReEDS evaluation period
    df_ivt = sFuncs.adjust_ptc_values(df_ivt)
    
    # Expand co2_capture_value by the duration of the incentive. 
    co2_capture_value = df_ivt[['i', 'v', 't', 'co2_capture_value_monetized', 'co2_capture_dur']].copy()
    co2_capture_value = co2_capture_value[co2_capture_value['co2_capture_value_monetized']>0]
    if len(co2_capture_value) > 0:
        dur_list = [] # create year expander
        for n in list(co2_capture_value['co2_capture_dur'].drop_duplicates()):
            dur_df = pd.DataFrame()
            dur_df['year_adder'] = np.arange(0,n)
            dur_df['co2_capture_dur'] = n
            dur_list += [dur_df.copy()]
        expander = pd.concat(dur_list, ignore_index=True, sort=False)
        co2_capture_value = co2_capture_value.merge(expander, on='co2_capture_dur', how='left')
        co2_capture_value['t'] = co2_capture_value['t'] + co2_capture_value['year_adder']
    else:
        co2_capture_value = df_ivt[['i', 'v', 't', 'co2_capture_value_monetized', 'co2_capture_dur']].iloc[0:5,:]
    co2_capture_value = co2_capture_value.drop_duplicates(['i', 'v', 't'])
    co2_capture_value['v'] = ['new%s' % v for v in co2_capture_value['v']]
    co2_capture_value['t'] = co2_capture_value['t'].astype(int)
    
    # Expand the various ptc values by the duration of the incentive. 
    # We are tracking various ptc_values (e.g. with and without tax grossups)
    # because different downstream processes require different forms of the ptc's value
    ptc_values_df = df_ivt[['i', 'v', 't', 'ptc_value', 'ptc_dur', 'ptc_value_monetized', 'ptc_tax_equity_penalty',
                            'ptc_value_monetized_posttax', 'ptc_grossup_value', 'ptc_value_scaled']].copy()
    ptc_values_df = ptc_values_df[ptc_values_df['ptc_value']>0]
    if len(ptc_values_df) > 0:
        dur_list = [] # create year expander
        for n in list(ptc_values_df['ptc_dur'].drop_duplicates()):
            dur_df = pd.DataFrame()
            dur_df['year_adder'] = np.arange(0,n)
            dur_df['ptc_dur'] = n
            dur_list += [dur_df.copy()]
        expander = pd.concat(dur_list, ignore_index=True, sort=False)
        ptc_values_df = ptc_values_df.merge(expander, on='ptc_dur', how='left')
        ptc_values_df['t'] = ptc_values_df['t'] + ptc_values_df['year_adder']
    else:
        ptc_values_df = df_ivt[['i', 'v', 't', 'ptc_value', 'ptc_dur', 'ptc_value_monetized', 'ptc_tax_equity_penalty',
                            'ptc_value_monetized_posttax', 'ptc_grossup_value', 'ptc_value_scaled']].iloc[0:5,:] # this is just a hack because pjg didn't know how to have gams handle empty files
    ptc_values_df = ptc_values_df.drop_duplicates(['i', 'v', 't'])
    ptc_values_df['v'] = ['new%s' % v for v in ptc_values_df['v']]
    ptc_values_df['t'] = ptc_values_df['t'].astype(int)
    
    

    #%%
    # Import schedules for financial calculations
    construction_schedules = pd.read_csv(os.path.join(
        input_dir, 'financials', 
        'construction_schedules_%s.csv' % switches['construction_schedules_suffix']))
    depreciation_schedules = pd.read_csv(os.path.join(
        input_dir, 'financials', 
        'depreciation_schedules_%s.csv' % switches['depreciation_schedules_suffix']))

    ### Calculate financial multipliers
    print('Calculating financial multipliers for', inputs_case, '...')
    df_ivt = sFuncs.calc_financial_multipliers(
        df_ivt, construction_schedules, depreciation_schedules, switches['timetype'])
    

    #%%### Calculate financial multipliers for transmission
    ### Load transmission data
    dftrans = pd.read_csv(
        os.path.join(
            input_dir, 'financials',
            'financials_transmission_{}.csv'.format(switches['financials_trans_suffix'])),
    )
    ### Get transmission capital recovery period (CRP) from input scalars
    dftrans['eval_period'] = int(scalars['trans_crp'])
    ### Get online year
    dftrans['t'] = dftrans.t_start_construction + dftrans.construction_time
    ### Get ITC monetization
    dftrans['itc_frac_monetized'] = dftrans.itc_frac * (1 - dftrans.itc_tax_equity_penalty)
    ### Get sys financials
    dftrans = dftrans.merge(financials_sys.dropna(how='any'), on='t', how='right')
    ### Get financial multipliers
    dftrans = sFuncs.calc_financial_multipliers(
        df_inv=dftrans, construction_schedules=construction_schedules,
        depreciation_schedules=depreciation_schedules, timetype=switches['timetype'],
    )
        
    ### Get the CRF for transmission
    dftrans['crf_tech'] = sFuncs.calc_crf(dftrans['d_real'], dftrans['eval_period'])

    ### Get the final capital cost multiplier (including the CRF scaler above)
    dftrans['cap_cost_mult'] = sFuncs.calc_final_capital_cost_multiplier(dftrans)
    dftrans['cap_cost_mult_noITC'] = sFuncs.calc_final_capital_cost_multiplier(dftrans, mult_type='finMult_noITC')

    ### The transmission ITC is not meant to apply to currently-planned transmission.
    ### So for years before firstyear_trans, use cap_cost_mult_noITC;
    ### i.e. only start applying the ITC once the model switches to endogenous transmission.
    firstyear_trans = int(scalars['firstyear_trans_longterm'])
    dftrans.loc[dftrans.t<firstyear_trans, 'cap_cost_mult'] = (
        dftrans.loc[dftrans.t<firstyear_trans, 'cap_cost_mult_noITC'])

    ### Write it
    dftrans.rename(columns={'t':'*t'})[['*t','cap_cost_mult']].round(6).to_csv(
        os.path.join(inputs_case, 'trans_cap_cost_mult.csv'), index=False)
    dftrans.rename(columns={'t':'*t'})[['*t','cap_cost_mult_noITC']].round(6).to_csv(
        os.path.join(inputs_case, 'trans_cap_cost_mult_noITC.csv'), index=False)
    dftrans.loc[
        dftrans.itc_frac != 0,
        ['t','itc_frac','itc_tax_equity_penalty','itc_frac_monetized']
    ].round(6).to_csv(
        os.path.join(inputs_case, 'trans_itc_fractions.csv'), index=False)

    #%%### Calculate financial multipliers for hydrogen network investments
    ### Load hydroge data
    dfhydrogen = pd.read_csv(
        os.path.join(
            input_dir, 'financials',
            'financials_hydrogen.csv'),
    )
    ### Get hydrogen capital recovery period (CRP) from input scalars
    # note that pipelines and compressors have different lifetimes
    dfhydrogen['eval_period_pipeline'] = int(scalars['h2_crp_pipeline'])
    dfhydrogen['eval_period_compressor'] = int(scalars['h2_crp_compressor'])
    dfhydrogen['eval_period_storage'] = int(scalars['h2_crp_storage'])

    ### Get online year
    dfhydrogen['t'] = dfhydrogen.t_start_construction + dfhydrogen.construction_time
    ### Get ITC monetization
    dfhydrogen['itc_frac_monetized'] = dfhydrogen.itc_frac * (1 - dfhydrogen.itc_tax_equity_penalty)
    ### Get sys financials
    dfhydrogen = dfhydrogen.merge(financials_sys.dropna(how='any'), on='t', how='right')
        
    ### Get financial multipliers
    dfhydrogen_pipeline = dfhydrogen.copy().rename(columns={"eval_period_pipeline":"eval_period"})
    dfhydrogen_pipeline = sFuncs.calc_financial_multipliers(
        df_inv=dfhydrogen_pipeline, construction_schedules=construction_schedules,
        depreciation_schedules=depreciation_schedules, timetype=switches['timetype'],
    )
    dfhydrogen_compressor = dfhydrogen.copy().rename(columns={"eval_period_compressor":"eval_period"})
    dfhydrogen_compressor = sFuncs.calc_financial_multipliers(
        df_inv=dfhydrogen_compressor, construction_schedules=construction_schedules,
        depreciation_schedules=depreciation_schedules, timetype=switches['timetype'],
    )
    dfhydrogen_storage = dfhydrogen.copy().rename(columns={"eval_period_storage":"eval_period"})
    dfhydrogen_storage = sFuncs.calc_financial_multipliers(
        df_inv=dfhydrogen_storage, construction_schedules=construction_schedules,
        depreciation_schedules=depreciation_schedules, timetype=switches['timetype'],
    )
    
    ### Get the CRF for h2 pipelines
    dfhydrogen_pipeline['crf_tech'] = sFuncs.calc_crf(dfhydrogen_pipeline['d_real'], dfhydrogen_pipeline['eval_period'])
    dfhydrogen_compressor['crf_tech'] = sFuncs.calc_crf(dfhydrogen_compressor['d_real'], dfhydrogen_compressor['eval_period'])
    dfhydrogen_storage['crf_tech'] = sFuncs.calc_crf(dfhydrogen_storage['d_real'], dfhydrogen_storage['eval_period'])

    ### Get the final capital cost multiplier (including the CRF scaler above)   
    dfhydrogen_pipeline["cap_cost_mult_pipeline"] = sFuncs.calc_final_capital_cost_multiplier(dfhydrogen_pipeline)
    dfhydrogen_compressor["cap_cost_mult_compressor"] = sFuncs.calc_final_capital_cost_multiplier(dfhydrogen_compressor)
    dfhydrogen_storage["cap_cost_mult_storage"] = sFuncs.calc_final_capital_cost_multiplier(dfhydrogen_storage)
    
    ### Write it
    dfhydrogen_pipeline.rename(columns={'t':'*t'})[['*t','cap_cost_mult_pipeline']].round(6).to_csv(
        os.path.join(inputs_case, 'h2_pipeline_cap_cost_mult.csv'), index=False)
    dfhydrogen_compressor.rename(columns={'t':'*t'})[['*t','cap_cost_mult_compressor']].round(6).to_csv(
        os.path.join(inputs_case, 'h2_compressor_cap_cost_mult.csv'), index=False)    
    dfhydrogen_storage.rename(columns={'t':'*t'})[['*t','cap_cost_mult_storage']].round(6).to_csv(
        os.path.join(inputs_case, 'h2_storage_cap_cost_mult.csv'), index=False)

    #%%
    # Import regional capital cost multipliers, create multipliers for csp configurations
    reg_cap_cost_mult = sFuncs.import_data(
        file_root='reg_cap_cost_mult', file_suffix=switches['reg_cap_cost_mult_suffix'], 
        indices=['i','r'], scen_settings=scen_settings)
    # Apply the values for standalone batteries to PV+B batteries
    reg_cap_cost_mult = sFuncs.append_pvb_parameters(
        dfin=reg_cap_cost_mult, 
        tech_to_copy='battery_{}'.format(scen_settings.switches['GSw_PVB_Dur']))

    reg_cap_cost_mult_csp = reg_cap_cost_mult[reg_cap_cost_mult['i'].str.contains('csp1_')].copy()
    # Read in techs subset table to determine number of csp configurations
    tech_subset_table = pd.read_csv(os.path.join(input_dir, 'tech-subset-table.csv'))
    csp_configs =  int(len(tech_subset_table.query('CSP == "YES" and STORAGE == "YES"')))
    del tech_subset_table
    for i in range(2, csp_configs + 1):
        configuration = 'csp' + str(i)
        mult_temp = reg_cap_cost_mult_csp.copy()
        mult_temp['i'] = mult_temp.i.replace({'csp1':configuration}, regex=True)
        reg_cap_cost_mult = reg_cap_cost_mult.append(mult_temp)
        del mult_temp
    del reg_cap_cost_mult_csp
    
    # Trim down to just the techs and regions in this run
    reg_cap_cost_mult = reg_cap_cost_mult[reg_cap_cost_mult['i'].isin(list(techs['i']))]
    reg_cap_cost_mult = reg_cap_cost_mult[reg_cap_cost_mult['r'].isin(val_r)]


    #%% Before writing outputs, change "x" to "newx" in [v]
    df_ivt['v'] = ['new%s' % v for v in df_ivt['v']]


    #%% Write the scenario-specific output files
    
    # Write out the components of the financial multiplier
    sFuncs.inv_param_exporter(
        df_ivt, modeled_years, 'CCmult', ['i', 't'], 
        'ccmult', inputs_case)
    sFuncs.inv_param_exporter(
        df_ivt, modeled_years, 'tax_rate', ['t'], 
        'tax_rate', inputs_case)
    sFuncs.inv_param_exporter(
        df_ivt, modeled_years, 'itc_frac_monetized', ['i', 't'], 
        'itc_frac_monetized', inputs_case)
    sFuncs.inv_param_exporter(
        df_ivt, modeled_years, 'PV_fraction_of_depreciation', ['i', 't'], 
        'pv_frac_of_depreciation', inputs_case)
    sFuncs.inv_param_exporter(
        df_ivt, modeled_years, 'Degradation_Adj', ['i', 't'], 
        'degradation_adj', inputs_case)  
    sFuncs.inv_param_exporter(
        df_ivt, modeled_years, 'financing_risk_mult', ['i', 't'], 
        'financing_risk_mult', inputs_case) 
    sFuncs.inv_param_exporter(
        reg_cap_cost_mult, None, 'reg_cap_cost_mult', ['i', 'r'], 
        'reg_cap_cost_mult', inputs_case)
    
    # Write out the adjustment multiplier for non-standard evaluation periods
    sFuncs.param_exporter(
        df_ivt[['i', 't', 'eval_period_adj_mult']], 
        'eval_period_adj_mult', 'eval_period_adj_mult', inputs_case)
    
    # Write out the maximum safe harbor window for each tech, for determining
    # the tax credit phaseout schedules
    sFuncs.param_exporter(
        df_ivt[['i', 't', 'safe_harbor_max']], 
        'safe_harbor_max', 'safe_harbor_max', inputs_case)
    
    # Write out the carbon capture incentive values
    sFuncs.param_exporter(
        co2_capture_value[['i', 'v', 't', 'co2_capture_value_monetized']], 
        'co2_capture_value_monetized', 'co2_capture_incentive', inputs_case)
    
    
    # Write out the ptc_value_scaled (which incorporates all the adjustments reeds expects)
    sFuncs.param_exporter(
        ptc_values_df[['i', 'v', 't', 'ptc_value_scaled']], 
        'ptc_value_scaled', 'ptc_value_scaled', inputs_case)

    # Write out the PTC's nominal value, grossup value, tax equity penalty, and duration. This is
    # used in the retail rate module.
    ptc_values_df[
        ['i', 'v', 't', 'ptc_value', 'ptc_grossup_value', 'ptc_dur', 'ptc_tax_equity_penalty']
    ].to_csv(os.path.join(inputs_case, 'ptc_values.csv'), index=False)

    # Write out the ITC fractions, for use in retail rate calculations
    itc_df = incentive_df[incentive_df['itc_frac']!=0]
    itc_df[
        ['i', 'country', 't', 'itc_frac', 'itc_tax_equity_penalty']
    ].to_csv(os.path.join(inputs_case, 'itc_fractions.csv'), index=False)


    # CRF used in sequential case for calculating pvf_onm values (pvf)
    crf_df = financials_sys[financials_sys['t']==financials_sys['modeled_year']].copy()
    sFuncs.param_exporter(crf_df[['t', 'crf']], 'crf', 'crf', inputs_case)

    # 12-year crf used in sequential case for calculating 12-year payback time of co2_captured_incentive
    crf_co2_df = financials_sys[financials_sys['t']==financials_sys['modeled_year']].copy()
    sFuncs.param_exporter(crf_df[['t', 'crf_co2_incentive']], 'crf_co2_incentive', 'crf_co2_incentive', inputs_case)

    # pvf_onm used in intertemporal
    pvf_onm_int = financials_sys[['modeled_year', 'pvf_onm']].groupby(by=['modeled_year']).sum()
    pvf_onm_int = pvf_onm_int.reset_index()
    pvf_onm_int = pvf_onm_int.rename(columns={'modeled_year':'t'})
    sFuncs.param_exporter(pvf_onm_int, 'pvf_onm', 'pvf_onm_int', inputs_case)


    # pvf_cap (used in both seq and int modes)
    sFuncs.inv_param_exporter(df_ivt, modeled_years, 'pvf_capital', ['t'], 'pvf_cap', inputs_case)

    # Copy input files into inputs_case
    depreciation_schedules.to_csv(
        os.path.join(inputs_case, 'depreciation_schedules.csv'), index=False)
    inflation_df.to_csv(os.path.join(inputs_case, 'inflation.csv'), index=False)

    # Copy construction_times into inputs_case
    pd.read_csv(
        os.path.join(input_dir, 'financials', 
                     'construction_times_%s.csv' % switches['construction_times_suffix'])
    ).to_csv(
        os.path.join(inputs_case, 'construction_times.csv'), index=False)

    # Copy tc_phaseout_schedule into inputs_case
    pd.read_csv(
        os.path.join(input_dir, 'financials', 
                     'tc_phaseout_schedule_%s.csv' % switches['GSw_TCPhaseout_schedule'])
    ).to_csv(
        os.path.join(inputs_case, 'tc_phaseout_schedule.csv'), index=False)


    # Output some values used in the retail rate module
    retail_eval_period = df_ivt[['i', 't', 'eval_period']].drop_duplicates(['i', 't'])
    retail_depreciation_sch = df_ivt[
        ['i', 't', 'depreciation_sch']].drop_duplicates(['i', 't'])
    retail_eval_period.astype({'i':'category'}).to_hdf(
        os.path.join(inputs_case, 'retail_eval_period.h5'),
        key='data', complevel=4, index=False, format='table')
    retail_depreciation_sch.astype({'i':'category'}).to_hdf(
        os.path.join(inputs_case, 'retail_depreciation_sch.h5'),
        key='data', complevel=4, index=False, format='table')


    print('Finished calculation of financial parameters for', inputs_case)

    #%% Write a dictionary of the results
    finance_dict = {
        'df_ivt': df_ivt,
        'financials_sys': financials_sys,
    }

    return finance_dict

#%% Procedure
if __name__ == '__main__':
    ###################
    #%% Argument inputs
    import argparse
    parser = argparse.ArgumentParser(description="calc_financial_inputs.py")
    parser.add_argument("reeds_path",
                        help="ReEDS-2.0 directory")
    parser.add_argument("inputs_case",
                        help="ReEDS-2.0/runs/{case}/inputs_case directory")
    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    ### Set up logger
    #log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    #%% Run it
    tic = datetime.datetime.now()

    calc_financial_inputs(reeds_path, inputs_case)

    toc(tic=tic, year=0, process='input_processing/calc_financial_inputs.py', 
        path=os.path.join(inputs_case,'..'))
