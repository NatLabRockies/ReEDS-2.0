#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import pandas as pd
import numpy as np
import os
import sys
import datetime
# Time the operation of this script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def calc_financial_inputs(inputs_case):
    """
    Write the following files to runs/{batch_case}/inputs_case/:
    - cap_cost_mult_noITC.csv
    - co2_capture_incentive.csv
    - crf.csv
    - crf_co2_incentive.csv
    - crf_h2_incentive.csv
    - depreciation_schedules.csv
    - h2_ptc.csv
    - inflation.csv
    - itc_fractions.csv
    - ivt.csv
    - ptc_values.csv
    - ptc_value_scaled.csv
    - pvf_onm_int.csv
    - pvf_cap.csv
    - reg_cap_cost_diff.csv
    - retail_eval_period.h5
    - retail_depreciation_sch.h5
    """
    print('Starting calculation of financial parameters')

    # #%% Settings for testing
    # reeds_path = '/Users/pbrown/github/ReEDS-2.0/'
    # inputs_case = os.path.join(reeds_path,'runs','v20220621_NTPm0_ercot_seq_test','inputs_case')

    #%% Inputs from switches
    sw = reeds.io.get_switches(inputs_case)
    sw['endyear'] = int(sw['endyear'])
    sw['sys_eval_years'] = int(sw['sys_eval_years'])

    scalars = reeds.io.get_scalars(inputs_case)
    
    #%% Import some general data and maps

    # Import inflation (which includes both historical and future inflation). 
    # Used for adjusting currency inputs to the specified dollar year, and financial calculations. 
    inflation_df = pd.read_csv(os.path.join(inputs_case,'inflation.csv'))

    # Import tech groups. Used to expand data inputs 
    # (e.g., 'UPV' expands to all of the upv subclasses, like upv_1, upv_2, etc)
    tech_groups = reeds.techs.import_tech_groups(os.path.join(inputs_case, 'tech-subset-table.csv'))

    # Set up scen_settings object
    scen_settings = reeds.financials.scen_settings(
        dollar_year=int(sw['dollar_year']), tech_groups=tech_groups, inputs_case=inputs_case,
        sw=sw)


    #%% Ingest data, determine what regions have been specified, and build df_ivt
    # Build df_ivt (for calculating various parameters at subscript [i,v,t])

    techs = pd.read_csv(os.path.join(inputs_case,'techs.csv'))
    techs = reeds.techs.expand_GAMS_tech_groups(techs)
    vintage_definition = pd.read_csv(os.path.join(inputs_case, 'ivt.csv')).rename(columns={'Unnamed: 0':'i'})

    annual_degrade = pd.read_csv(os.path.join(inputs_case,'degradation_annual.csv'),
        header=None, names=['i','annual_degradation'])
    annual_degrade = reeds.techs.expand_GAMS_tech_groups(annual_degrade)
    ### Assign the PV+battery values to values for standalone batteries
    annual_degrade = reeds.financials.append_pvb_parameters(
        dfin=annual_degrade, 
        tech_to_copy='battery_li')
    
    for nukestoretype, storage_tech in enumerate(scen_settings.sw['GSw_NuclearStor_StorageTechs'].split('_')):
        storage_tech = storage_tech.replace('-', '_')
        annual_degrade = reeds.financials.append_nuclear_stor_parameters(
            dfin=annual_degrade, 
            tech_to_copy=storage_tech,
            nuclear_storage_types=[nukestoretype]
            )

    years, modeled_years, year_map = reeds.financials.ingest_years(
        inputs_case, sw['sys_eval_years'], sw['endyear'])

    df_ivt = reeds.financials.build_dfs(years, techs, vintage_definition, year_map)
    print('df_ivt created')

    #%% Import and merge data onto df_ivt

    # Import system-wide real discount rates, calculate present-value-factors, merge onto df's
    financials_sys = reeds.financials.import_sys_financials(
        sw['financials_sys_suffix'], inflation_df, modeled_years, 
        years, year_map, sw['sys_eval_years'], scen_settings, scalars['co2_capture_incentive_length'],scalars['h2_ptc_length'])
    financials_sys.to_csv(os.path.join(inputs_case,'financials_sys.csv'),index=False)
    df_ivt = df_ivt.merge(
        financials_sys[['t', 'pvf_capital', 'crf', 'crf_co2_incentive','crf_h2_incentive','d_real', 'd_nom', 'interest_rate_nom', 
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
    financials_tech = reeds.financials.import_data(
        file_root='financials_tech', file_suffix=sw['financials_tech_suffix'], 
        indices=['i','country','t'], scen_settings=scen_settings)
    # Apply the values for standalone batteries to PV+B batteries
    financials_tech = reeds.financials.append_pvb_parameters(
        dfin=financials_tech, 
        tech_to_copy='battery_li')
    # If the battery in PV+B gets the ITC, it gets 5-year MACRS depreciation as well
    if float(scen_settings.sw['GSw_PVB_BatteryITC']) >= 0.75:
        financials_tech.loc[
            financials_tech.i.str.startswith('pvb') & (financials_tech.country == 'usa'),
            'depreciation_sch'
        ] = 5

    ### Project financials_tech forward
    financials_tech_projected = financials_tech.pivot(
        index=['i','country','depreciation_sch','eval_period','construction_sch'], 
        columns=['t'])['finance_diff_real']
    lastdatayear = max(financials_tech_projected.columns)
    for addyear in range(lastdatayear+1, sw['endyear']+1):
        financials_tech_projected[addyear] = financials_tech_projected[lastdatayear]
    # Overwrite with projected values
    financials_tech = financials_tech_projected.stack().rename('finance_diff_real').reset_index()
    # Merge with df_ivt
    df_ivt = df_ivt.merge(financials_tech, on=['i', 't', 'country'], how='left')
    
    # Calculate multipliers to account for evaluation periods. If a tech's eval period is
    # the system-wide default, this will be 1. If not, the capital costs are adjusted accordingly. 
    financials_sys['sys_pvf_eval_period_sum'] = (1 - (1 / (financials_sys['d_real'])**(sw['sys_eval_years']-1))) / (financials_sys['d_real']-1.0) + 1
    df_ivt['pvf_eval_period_sum'] = (1 - (1 / (df_ivt['d_real'])**(df_ivt['eval_period']-1))) / (df_ivt['d_real']-1.0) + 1
    df_ivt = df_ivt.merge(financials_sys[['sys_pvf_eval_period_sum', 't']], on='t', how='left')
    df_ivt['eval_period_adj_mult'] = df_ivt['sys_pvf_eval_period_sum'] / df_ivt['pvf_eval_period_sum']

    #%% Process incentives
    
    # Import incentives, shift eligibility by safe harbor, merge incentives
    incentive_df = reeds.financials.import_and_mod_incentives(
        incentive_file_suffix=sw['incentives_suffix'],
        inflation_df=inflation_df, scen_settings=scen_settings)
    df_ivt = df_ivt.merge(incentive_df, on=['i', 't', 'country'], how='left')
    df_ivt['safe_harbor'] = df_ivt['safe_harbor'].fillna(0.0)
    df_ivt['co2_capture_value_monetized'] = df_ivt['co2_capture_value_monetized'].fillna(0.0) * (1 / (1 - df_ivt['tax_rate']))
    df_ivt['h2_ptc_value_monetized'] = df_ivt['h2_ptc_value_monetized'].fillna(0.0) * (1 / (1 - df_ivt['tax_rate']))
    
    ### Calculate the tax impacts of the PTC, and calculate the adjustment to reflect the 
    # difference between the PTC duration and ReEDS evaluation period
    df_ivt = reeds.financials.adjust_ptc_values(df_ivt)
    
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

    # Expand h2_ptc_value by the duration of the incentive. 
    h2_ptc_value = df_ivt[['i', 'v', 't', 'h2_ptc_value_monetized', 'h2_ptc_dur']].copy()
    h2_ptc_value = h2_ptc_value[h2_ptc_value['h2_ptc_value_monetized']>0]
    if len(h2_ptc_value) > 0:
        dur_list = [] # create year expander
        for n in list(h2_ptc_value['h2_ptc_dur'].drop_duplicates()):
            dur_df = pd.DataFrame()
            dur_df['year_adder'] = np.arange(0,n)
            dur_df['h2_ptc_dur'] = n
            dur_list += [dur_df.copy()]
        expander = pd.concat(dur_list, ignore_index=True, sort=False)
        h2_ptc_value = h2_ptc_value.merge(expander, on='h2_ptc_dur', how='left')
        h2_ptc_value['t'] = h2_ptc_value['t'] + h2_ptc_value['year_adder']
    else:
        h2_ptc_value = df_ivt[['i', 'v', 't', 'h2_ptc_value_monetized', 'h2_ptc_dur']].iloc[0:5,:]
    h2_ptc_value = h2_ptc_value.drop_duplicates(['i', 'v', 't'])
    h2_ptc_value['v'] = ['new%s' % v for v in h2_ptc_value['v']]
    h2_ptc_value['t'] = h2_ptc_value['t'].astype(int)
    
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
    construction_schedules = pd.read_csv(os.path.join(inputs_case,'construction_schedules.csv'))
    depreciation_schedules = pd.read_csv(os.path.join(inputs_case,'depreciation_schedules.csv'))

    ### Calculate financial multipliers
    print('Calculating financial multipliers...')
    df_ivt = reeds.financials.calc_financial_multipliers(
        df_ivt, construction_schedules, depreciation_schedules, sw['timetype'])
    

    #%%### Calculate financial multipliers for transmission
    ### Load transmission data
    dftrans = pd.read_csv(os.path.join(inputs_case,'financials_transmission.csv'))
    ### Get transmission capital recovery period (CRP) from input scalars
    dftrans['eval_period'] = int(scalars['trans_crp'])
    ### Get online year
    dftrans['t'] = dftrans.t_start_construction + dftrans.construction_time
    ### Get ITC monetization
    dftrans['itc_frac_monetized'] = dftrans.itc_frac * (1 - dftrans.itc_tax_equity_penalty)
    ### Get sys financials
    dftrans = dftrans.merge(financials_sys.dropna(how='any'), on='t', how='right')
    ### Get financial multipliers
    dftrans = reeds.financials.calc_financial_multipliers(
        df_inv=dftrans, construction_schedules=construction_schedules,
        depreciation_schedules=depreciation_schedules, timetype=sw['timetype'],
    )
        
    ### Get the CRF for transmission
    dftrans['crf_tech'] = reeds.financials.calc_crf(dftrans['d_real'], dftrans['eval_period'])

    ### Get the final capital cost multiplier (including the CRF scaler above)
    dftrans['cap_cost_mult'] = reeds.financials.calc_final_capital_cost_multiplier(dftrans)
    dftrans['cap_cost_mult_noITC'] = reeds.financials.calc_final_capital_cost_multiplier(dftrans, mult_type='finMult_noITC')

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
    dfhydrogen = pd.read_csv(os.path.join(inputs_case,'financials_hydrogen.csv'))
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
    dfhydrogen_pipeline = reeds.financials.calc_financial_multipliers(
        df_inv=dfhydrogen_pipeline, construction_schedules=construction_schedules,
        depreciation_schedules=depreciation_schedules, timetype=sw['timetype'],
    )
    dfhydrogen_compressor = dfhydrogen.copy().rename(columns={"eval_period_compressor":"eval_period"})
    dfhydrogen_compressor = reeds.financials.calc_financial_multipliers(
        df_inv=dfhydrogen_compressor, construction_schedules=construction_schedules,
        depreciation_schedules=depreciation_schedules, timetype=sw['timetype'],
    )
    dfhydrogen_storage = dfhydrogen.copy().rename(columns={"eval_period_storage":"eval_period"})
    dfhydrogen_storage = reeds.financials.calc_financial_multipliers(
        df_inv=dfhydrogen_storage, construction_schedules=construction_schedules,
        depreciation_schedules=depreciation_schedules, timetype=sw['timetype'],
    )
    
    ### Get the CRF for h2 pipelines
    dfhydrogen_pipeline['crf_tech'] = reeds.financials.calc_crf(dfhydrogen_pipeline['d_real'], dfhydrogen_pipeline['eval_period'])
    dfhydrogen_compressor['crf_tech'] = reeds.financials.calc_crf(dfhydrogen_compressor['d_real'], dfhydrogen_compressor['eval_period'])
    dfhydrogen_storage['crf_tech'] = reeds.financials.calc_crf(dfhydrogen_storage['d_real'], dfhydrogen_storage['eval_period'])

    ### Get the final capital cost multiplier (including the CRF scaler above)   
    dfhydrogen_pipeline["cap_cost_mult_pipeline"] = reeds.financials.calc_final_capital_cost_multiplier(dfhydrogen_pipeline)
    dfhydrogen_compressor["cap_cost_mult_compressor"] = reeds.financials.calc_final_capital_cost_multiplier(dfhydrogen_compressor)
    dfhydrogen_storage["cap_cost_mult_storage"] = reeds.financials.calc_final_capital_cost_multiplier(dfhydrogen_storage)
    
    ### Write it
    dfhydrogen_pipeline.rename(columns={'t':'*t'})[['*t','cap_cost_mult_pipeline']].round(6).to_csv(
        os.path.join(inputs_case, 'h2_pipeline_cap_cost_mult.csv'), index=False)
    dfhydrogen_compressor.rename(columns={'t':'*t'})[['*t','cap_cost_mult_compressor']].round(6).to_csv(
        os.path.join(inputs_case, 'h2_compressor_cap_cost_mult.csv'), index=False)    
    dfhydrogen_storage.rename(columns={'t':'*t'})[['*t','cap_cost_mult_storage']].round(6).to_csv(
        os.path.join(inputs_case, 'h2_storage_cap_cost_mult.csv'), index=False)

    #%% Import regional capital cost differences
    reg_cap_cost_diff = reeds.financials.import_data(
        file_root='regional_cap_cost_diff', file_suffix=sw['reg_cap_cost_diff_suffix'], 
        indices=['i','r'], scen_settings=scen_settings)

    # Trim down to just the techs in this run
    reg_cap_cost_diff = reg_cap_cost_diff.loc[reg_cap_cost_diff['i'].isin(list(techs['i']))].copy()


    #%% Before writing outputs, change "x" to "newx" in [v]
    df_ivt['v'] = ['new%s' % v for v in df_ivt['v']]

    ## get energy communities and itc bonus 
    energy_communities = pd.read_csv(os.path.join(inputs_case, 'energy_communities.csv'))
    temp_incentives = incentive_df[
       incentive_df['itc_energy_comm_bonus'] != 0
    ][['i','itc_energy_comm_bonus']].drop_duplicates()

    energy_communities['key'] = 1
    temp_incentives['key'] = 1
    e_df = pd.merge(energy_communities, temp_incentives, on='key').drop('key', axis=1)

    ## get nuclear energy communities and itc bonus 
    nuclear_energy_communities = pd.read_csv(
        os.path.join(inputs_case, 'nuclear_energy_communities.csv')
    )
    nuclear_temp_incentives = (
        incentive_df[
            (incentive_df['itc_energy_comm_bonus'] != 0)
            & (incentive_df['i'].isin(scen_settings.tech_groups['NUCLEAR']))
        ]
        [['i','itc_energy_comm_bonus']]
        .drop_duplicates()
    )

    nuclear_energy_communities['key'] = 1
    nuclear_temp_incentives['key'] = 1
    nuclear_e_df = (
        pd.merge(nuclear_energy_communities, nuclear_temp_incentives, on='key')
        .drop('key', axis=1)
    )
    e_df = pd.concat([e_df, nuclear_e_df], ignore_index=True)

    # Calculate the weighted energy community bonus: the 'itc_energy_comm_bonus' is initially set to 1 - the value from the incentives file.
    # To apply the bonus correctly, we reverse the adjustment, multiply it by the 'percentage_energy_communities',
    # and then adjust it back to the 1 - 'itc_energy_comm_bonus' format.
    e_df['itc_energy_comm_bonus'] = (
        1 - ((1 - e_df['itc_energy_comm_bonus']) * e_df['percentage_energy_communities'])
    ).round(4).drop(columns='percentage_energy_communities')

    # There are some regions that are eligible for both the energy communities and nuclear energy communities bonus
    # so choose the highest bonus for each region and tech (note that the bonus is formatted as 1 - 'itc_energy_comm_bonus',
    # meaning the lowest 'itc_energy_comm_bonus' value represents the highest bonus)
    e_df = (
        e_df.sort_values(by='itc_energy_comm_bonus', ascending=True)
        .drop_duplicates(subset=['r', 'i'], keep='first')
        .reset_index(drop=True)
    )

    #%% Write the scenario-specific output files
    
    # Write out the components of the financial multiplier
    reeds.financials.inv_param_exporter(
        df_ivt, modeled_years, 'CCmult', ['i', 't'], 
        'ccmult', inputs_case)
    reeds.financials.inv_param_exporter(
        df_ivt, modeled_years, 'tax_rate', ['t'], 
        'tax_rate', inputs_case)
    reeds.financials.inv_param_exporter(
        df_ivt, modeled_years, 'itc_frac_monetized', ['i', 't'], 
        'itc_frac_monetized', inputs_case)
    reeds.financials.inv_param_exporter(
        df_ivt, modeled_years, 'PV_fraction_of_depreciation', ['i', 't'], 
        'pv_frac_of_depreciation', inputs_case)
    reeds.financials.inv_param_exporter(
        df_ivt, modeled_years, 'Degradation_Adj', ['i', 't'], 
        'degradation_adj', inputs_case)  
    reeds.financials.inv_param_exporter(
        df_ivt, modeled_years, 'financing_risk_mult', ['i', 't'], 
        'financing_risk_mult', inputs_case) 
    reeds.financials.inv_param_exporter(
        reg_cap_cost_diff, None, 'reg_cap_cost_diff', ['i', 'r'], 
        'reg_cap_cost_diff', inputs_case)
    
    # Write out the energy community itc bonus
    reeds.financials.param_exporter(
        e_df[['i','r','itc_energy_comm_bonus']],
        'itc_energy_comm_bonus', 'itc_energy_comm_bonus', inputs_case
    )

    # Write out the adjustment multiplier for non-standard evaluation periods
    reeds.financials.param_exporter(
        df_ivt[['i', 't', 'eval_period_adj_mult']], 
        'eval_period_adj_mult', 'eval_period_adj_mult', inputs_case)
    
    # Write out the safe harbor window for each tech, for determining
    # the tax credit phaseout schedules
    reeds.financials.param_exporter(
        df_ivt[['i', 't', 'safe_harbor']], 
        'safe_harbor', 'safe_harbor', inputs_case)
    
    # Write out the carbon capture incentive values
    reeds.financials.param_exporter(
        co2_capture_value[['i', 'v', 't', 'co2_capture_value_monetized']], 
        'co2_capture_value_monetized', 'co2_capture_incentive', inputs_case)

    # Write out the H2 production incentive values
    reeds.financials.param_exporter(
        h2_ptc_value[['i', 'v', 't', 'h2_ptc_value_monetized']], 
        'h2_ptc_value_monetized', 'h2_ptc', inputs_case)   
    
    # Write out the ptc_value_scaled (which incorporates all the adjustments reeds expects)
    reeds.financials.param_exporter(
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
    reeds.financials.param_exporter(crf_df[['t', 'crf']], 'crf', 'crf', inputs_case)

    # 12-year crf used in sequential case for calculating 12-year payback time of co2_captured_incentive
    reeds.financials.param_exporter(crf_df[['t', 'crf_co2_incentive']], 'crf_co2_incentive', 'crf_co2_incentive', inputs_case)

    # 10-year crf used in sequential case for calculating 10-year payback time of h2_ptc
    reeds.financials.param_exporter(crf_df[['t', 'crf_h2_incentive']], 'crf_h2_incentive', 'crf_h2_incentive', inputs_case)

    # pvf_onm used in intertemporal
    pvf_onm_int = financials_sys[['modeled_year', 'pvf_onm']].groupby(by=['modeled_year']).sum()
    pvf_onm_int = pvf_onm_int.reset_index()
    pvf_onm_int = pvf_onm_int.rename(columns={'modeled_year':'t'})
    reeds.financials.param_exporter(pvf_onm_int, 'pvf_onm', 'pvf_onm_int', inputs_case)

    # pvf_cap (used in both seq and int modes)
    reeds.financials.inv_param_exporter(df_ivt, modeled_years, 'pvf_capital', ['t'], 'pvf_cap', inputs_case)

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


    #%% Write a dictionary of the results
    finance_dict = {
        'df_ivt': df_ivt,
        'financials_sys': financials_sys,
    }

    return finance_dict

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================
if __name__ == '__main__':

    #%% Parse arguments
    parser = argparse.ArgumentParser(description="calc_financial_inputs.py")
    parser.add_argument("reeds_path", help="ReEDS-2.0 directory")
    parser.add_argument("inputs_case", help="ReEDS-2.0/runs/{case}/inputs_case directory")
    
    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    #%% Run it
    tic = datetime.datetime.now()

    calc_financial_inputs(inputs_case)

    reeds.log.toc(tic=tic, year=0, process='input_processing/calc_financial_inputs.py', 
        path=os.path.join(inputs_case,'..'))
    
    print('Finished calc_financial_inputs.py')
