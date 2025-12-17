#%% =====================================================================================
### --- IMPORTS ---
### =====================================================================================
import argparse
import datetime
import itertools
import pandas as pd
import numpy as np
import gdxpds
import os
import sys
### Local imports
import ferc_distadmin
import calculate_historical_capex
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import reeds
from reeds import plots

#########################
### Shared properties ###

# Assign tracelabels here instead of inside the plotting function so
# that it can be easily imported in postprocess_for_tableau.py
tracelabels = {
    'bias_correction': 'State bias correction',
    'load_flow': 'Flow: Load',
    'oper_res_flow': 'Flow: Operating reserves',
    'res_marg_ann_flow': 'Flow: Planning reserves',
    'rps_flow': 'Flow: RPS',
    'op_emissions_taxes': 'Operation: Emissions taxes',
    'op_acp_compliance_costs': 'Operation: Alternative compliance payments',
    'op_vom_costs': 'Operation: Variable O&M',
    'op_operating_reserve_costs': 'Operation: Operating reserves',
    'op_fuelcosts_objfn': 'Operation: Fuel',
    'op_h2combustion_fuel_costs': 'Operation: H2-Combustion - Hydrogen',
    'op_h2_storage': 'Operation: Storage - Hydrogen',
    'op_h2_transport': 'Operation: Transport - Hydrogen',
    'op_h2_transport_intrareg': 'Operation: Intraregional Transport - Hydrogen',
    'op_h2_fuel_costs': 'Operation: Fuel - Hydrogen', 
    'op_h2_vom': 'Operation: Variable O&M - Hydrogen',
    'op_h2_45v_payment_dedelec': 'Operation: Incentives - 45V payments - Dedicated electrolyzer',
    'op_co2_transport_storage': 'Operation: Transport/storage - CO2',
    'op_co2_network_fom_pipe': 'Operation: Fixed O&M - CO2 pipe',
    'op_co2_network_fom_spur': 'Operation: Fixed O&M - CO2 spur',
    'op_fom_costs': 'Operation: Fixed O&M',
    'op_spurline_fom': 'Operation: Fixed O&M - Spur line',
    'op_transmission_intrazone_fom': 'Operation: Fixed O&M - Intrazone transmission',
    'op_co2_incentive_negative': 'Operation: Incentives - CO2 tax credits',
    'op_h2_ptc_payments_negative': 'Operation: Incentives - H2 PTC payments',
    'op_ptc_payments_negative': 'Operation: Incentives - PTC payments',
    'op_ptc_payments_negative_dedGen': 'Operation: Incentives - PTC payments - Dedicated electrolyzer',
    'op_startcost': 'Operation: Startup/ramping',
    'op_wc_debt_interest': 'Capital: Working capital debt interest',
    'op_wc_equity_return': 'Capital: Working capital equity return',
    'op_wc_income_tax': 'Capital: Working capital income tax',
    'op_dist': 'Operation: Distribution',
    'op_admin': 'Operation: Administration',
    'op_trans': 'Operation: Transmission',
    'op_transmission_fom': 'Operation: Transmission (ReEDS)',
    'cap_admin_dep_expense': 'Capital: Administration depreciation',
    'cap_admin_debt_interest': 'Capital: Administration debt interest',
    'cap_admin_equity_return': 'Capital: Administration equity return',
    'cap_admin_income_tax': 'Capital: Administration income tax',
    'cap_dist_dep_expense': 'Capital: Distribution depreciation',
    'cap_dist_debt_interest': 'Capital: Distribution debt interest',
    'cap_dist_equity_return': 'Capital: Distribution equity return',
    'cap_dist_income_tax': 'Capital: Distribution income tax',
    'cap_fom_dep_expense': 'Capital: Fixed O&M depreciation',
    'cap_fom_debt_interest': 'Capital: Fixed O&M debt interest',
    'cap_fom_equity_return': 'Capital: Fixed O&M equity return',
    'cap_fom_income_tax': 'Capital: Fixed O&M income tax',
    'cap_gen_dep_expense': 'Capital: Generator depreciation',
    'cap_gen_debt_interest': 'Capital: Generator debt interest',
    'cap_gen_equity_return': 'Capital: Generator equity return',
    'cap_gen_income_tax': 'Capital: Generator income tax',
    'cap_trans_FERC_dep_expense': 'Capital: Transmission (intra-region) depreciation',
    'cap_trans_FERC_debt_interest': 'Capital: Transmission (intra-region) debt interest',
    'cap_trans_FERC_equity_return': 'Capital: Transmission (intra-region) equity return',
    'cap_trans_FERC_income_tax': 'Capital: Transmission (intra-region) income tax',
    'cap_transmission_dep_expense': 'Capital: Transmission (inter-region) depreciation',
    'cap_transmission_debt_interest': 'Capital: Transmission (inter-region) debt interest',
    'cap_transmission_equity_return': 'Capital: Transmission (inter-region) equity return',
    'cap_transmission_income_tax': 'Capital: Transmission (inter-region) income tax',
    'cap_spurline_dep_expense': 'Capital: Spur line depreciation',
    'cap_spurline_debt_interest': 'Capital: Spur line debt interest',
    'cap_spurline_equity_return': 'Capital: Spur line equity return',
    'cap_spurline_income_tax': 'Capital: Spur line income tax',
    'cap_converter_dep_expense': 'Capital: Transmission AC/DC converter depreciation',
    'cap_converter_debt_interest': 'Capital: Transmission AC/DC converter debt interest',
    'cap_converter_equity_return': 'Capital: Transmission AC/DC converter equity return',
    'cap_converter_income_tax': 'Capital: Transmission AC/DC converter income tax',
}


#%% ===========================================================================
### --- UTILITY FUNCTIONS ---
### ===========================================================================

### Functions for interpolating between solve years
def interp_between_solve_years(
        df, value_name, modeled_years, non_modeled_years, 
        first_year, last_year, region_list, region_type):
    """
    """
    # If empty, return unchanged
    if df.empty:
        return df
    # Pivot for just the solve years first, so we can fill in zero-value years 
    df_pivot_solve_years = pd.DataFrame(index=modeled_years, columns=region_list)
    df_pivot_solve_years.update(df.pivot(index='t', columns=region_type, values=value_name))  
    df_pivot_solve_years = df_pivot_solve_years.fillna(0.0)
    
    # Then pivot all the years, filling in the values that we start with
    df_pivot = pd.DataFrame(index=np.arange(first_year,last_year+1,1), columns=region_list)
    df_pivot.update(df_pivot_solve_years)

    # Interpolate between solve years
    for year in non_modeled_years:
        preceding_model_year = np.max([x for x in modeled_years if x<year])
        following_model_year = np.min([x for x in modeled_years if x>year])
        interp_f = (year-preceding_model_year) / (following_model_year-preceding_model_year)
    
        df_pivot.loc[year,:] = (
            df_pivot.loc[preceding_model_year,:] 
            + interp_f * (df_pivot.loc[following_model_year,:] - df_pivot.loc[preceding_model_year,:])
            )
        
    # Melt the result back to the original tidy format
    df_pivot = df_pivot.reset_index().rename(columns={'index':'t'})
    df = df_pivot.melt(id_vars='t', value_name=value_name)
    df[value_name] = df[value_name].astype(float)  
    
    return df
    

def distribute_between_solve_years(df, value_col, modeled_years, years):
    """
    """
    first_year = np.min(modeled_years)

    year_expander = pd.DataFrame(index=years)
    year_expander['t_modeled'] = None
    year_expander['alloc_f'] = 0
    year_expander.loc[first_year, ['t_modeled', 'alloc_f']] = [first_year, 1.0]
    for year in year_expander.index[1:]:
        preceding_model_year = np.max([x for x in modeled_years if x<year])
        following_model_year = np.min([x for x in modeled_years if x>=year])
        if year in list(modeled_years):
            year_expander.loc[year,'t_modeled'] = year
        else:
            year_expander.loc[year,'t_modeled'] = following_model_year
        year_expander.loc[year, 'alloc_f'] = 1 / (following_model_year - preceding_model_year)
    
    year_expander = year_expander.reset_index().rename(columns={'index':'t'})
    
    df = df.merge(year_expander[['t', 't_modeled', 'alloc_f']], on='t_modeled', how='left')
    df[value_col] = df[value_col] * df['alloc_f']
        
    return df


def duplicate_between_solve_years(df, modeled_years, years):
    """
    """
    first_year = np.min(modeled_years)

    year_expander = pd.DataFrame(index=years)
    year_expander['t_modeled'] = None
    year_expander.loc[first_year, ['t_modeled']] = [first_year]
    for year in year_expander.index[1:]:
        following_model_year = np.min([x for x in modeled_years if x>=year])
        if year in list(modeled_years):
            year_expander.loc[year,'t_modeled'] = year
        else:
            year_expander.loc[year,'t_modeled'] = following_model_year
    
    year_expander = year_expander.reset_index().rename(columns={'index':'t'})
    
    df = df.merge(year_expander[['t', 't_modeled']], on='t_modeled', how='left')
        
    return df


### WACC (used for special excluded costs)
def get_wacc_nominal(
        debt_fraction=0.55, equity_return_nominal=0.096, 
        debt_interest_nominal=0.039, tax_rate=0.21):
    """
    Inputs
    ------
    debt_fraction: fraction
    equity_return_nominal: fraction
    debt_interest_nominal: fraction
    tax_rate: fraction
    
    Outputs
    -------
    float: nominal wacc

    Sources
    -------
    ATB2020 WACC Calc spreadsheet
    """
    wacc = (
        debt_fraction * debt_interest_nominal * (1 - tax_rate)
        + (1 - debt_fraction) * equity_return_nominal
    )
    return wacc


def get_wacc_real(wacc_nominal, inflation=0.025):
    """
    Inputs
    ------
    wacc_nominal: fraction
    inflation: fraction (without the 1)

    Outputs
    -------
    float: real wacc (fraction)

    Sources
    -------
    ATB2020 WACC Calc spreadsheet
    """
    wacc_real = (1 + wacc_nominal) / (1 + inflation) - 1
    return wacc_real


### CRF (used for special excluded costs)
def get_crf(wacc_real, lifetime):
    """
    Inputs
    ------
    wacc_real (float) : fraction
    lifetime (int) : years
    """
    crf = ((wacc_real * (1 + wacc_real) ** lifetime) 
           / ((1 + wacc_real) ** lifetime - 1))
    return crf


def read_file(filename):
    """
    Read input file of various types (for backwards-compatibility)
    """
    try:
        f = pd.read_hdf(filename+'.h5')
    except FileNotFoundError:
        try:
            f = pd.read_csv(filename+'.csv.gz')
        except FileNotFoundError:
            try:
                f = pd.read_pickle(filename+'.pkl')
            except ValueError:
                import pickle5
                with open(filename+'.pkl', 'rb') as p:
                    f = pickle5.load(p)
    return f


#%% =====================================================================================
### --- MAIN FUNCTION: RETAIL RATE CALCULATION ---
### =====================================================================================

def main(run_dir, inputpath='inputs.csv', write=True, verbose=0):
    """
    """
    print('Starting retail_rate_calculations.py')
    # Run historical capex calculation
    calculate_historical_capex.main(run_dir)

    # Get module directory for relative paths
    mdir = os.path.dirname(os.path.abspath(__file__))

    # #%% Settings for testing/debugging
    # run_dir = os.path.join(reeds.io.reeds_path, 'runs', 'v20250806_tscM2_Pacific')
    # inputpath = 'inputs.csv'
    # write = True
    # verbose = 0

    #%% INPUTS
    ### Inputs (Retail Rate Module) - ingest and parse from retail_rate_module/inputs.csv
    dfinputs = pd.read_csv(inputpath)
    
    # Create a dictionary from the 'inputs' column of dfinputs
    inputs = dict(
        dfinputs.loc[dfinputs['input_dict']=='inputs', 
                     ['input_key','input_value']].values
        )
    # Ensure that dictionary values are of the proper type
    intkeys = [
        'working_capital_days', 'trans_timeframe', 'eval_period_overwrite', 'dollar_year', 
        'drop_pgesce_20182019', 'numslopeyears', 'numprojyears', 'current_t', 'cleanup',
        ]
    floatkeys = ['distloss','FOM_capitalization_rate']
    inputs = {key: (int(inputs[key]) if key in intkeys 
                    else float(inputs[key]) if key in floatkeys
                    else str(inputs[key]))
              for key in inputs}
    
    # Create a dictionary from the 'input_daproj' column of dfinputs
    input_daproj = dict(
        dfinputs.loc[dfinputs.input_dict=='input_daproj', 
                     ['input_key','input_value']].values
        )
    # Ensure that dictionary values are of the proper type
    input_daproj = {key: (int(input_daproj[key]) if key in intkeys else str(input_daproj[key]))
                    for key in input_daproj}

    # Create a dictionary from the 'input_eval_periods' column of dfinputs
    input_eval_periods = dict(
        dfinputs.loc[dfinputs.input_dict=='input_eval_periods', 
                     ['input_key','input_value']].values
        )
    # Ensure that dictionary values are of the proper type
    input_eval_periods = {key: int(input_eval_periods[key]) for key in input_eval_periods}

    # Create a dictionary from the 'input_depreciation_schedules' column of dfinputs
    input_depreciation_schedules = dict(
        dfinputs.loc[dfinputs.input_dict=='input_depreciation_schedules', 
                     ['input_key','input_value']].values
        )
    # Ensure that dictionary values are of the proper type
    input_depreciation_schedules = {
        key: str(int(input_depreciation_schedules[key])) for key in input_depreciation_schedules}

    ### Inputs (ReEDS regions)
    # Ingest hierarchy file
    regions_map = pd.read_csv(
        os.path.join(run_dir, 'inputs_case', 'hierarchy.csv')
        ).rename(columns={'*r':'r','st':'state'})

    stacked_regions_map = regions_map[['r', 'state']].drop_duplicates().rename(columns={'r':'region'})
    reedsregion2state = dict(zip(stacked_regions_map.region.values, stacked_regions_map.state.values))
    states = list(set(reedsregion2state.values()))
    # Ingest map to convert s regions to p regions
    rs_map = pd.read_csv(os.path.join(mdir, 'inputs', 'rsmap.csv'))
    s2r = dict(zip(rs_map['rs'], rs_map['r']))

    if verbose > 1:
        print(f'inputs: \n{inputs}')
        print(f'input_daproj: \n{input_daproj}')
        print(f'input_eval_periods: \n{input_eval_periods}')
        print(f'input_depreciation_schedules: \n{input_depreciation_schedules}')

    #%% Start calculations
    print(' - Gathering retail rate components')
    
    # Ingest load from ReEDS
    load_rt = (
        pd.read_csv(os.path.join(run_dir, 'outputs', 'load_cat.csv')
        ).rename(columns={'loadtype':'load_category', 'Dim1':'load_category', 
        'Dim2':'r', 'Dim3':'t', 'Value':'busbar_load', 'Val':'busbar_load'})
        )
    # Omit extra load categories that include losses; this leaves
    # only loads that will count toward electricity sales
    omit_list = ['stor_charge', 'trans_loss']
    overall_list = list(load_rt['load_category'].drop_duplicates())
    final_list = list(set(overall_list) - set(omit_list))
    load_rt = load_rt[load_rt['load_category'].isin(final_list)]
    load_rt = load_rt.groupby(['r', 't'], as_index=False).agg({'busbar_load':'sum'})

    # Use load to identify which regions and which years are covered. 
    r_list = load_rt['r'].drop_duplicates()
    regions_map = regions_map[regions_map['r'].isin(r_list)]
    state_list = regions_map['state'].drop_duplicates()
    ba_state_map = regions_map[['r', 'state']].drop_duplicates()

    # Use load to identify the year span and modeled vs non-modeled years
    first_year = load_rt['t'].min()
    last_year = load_rt['t'].max()
    modeled_years = load_rt['t'].drop_duplicates()
    non_modeled_years = list(set(np.arange(first_year,last_year,1)) - set(modeled_years))
    years_reeds = np.arange(first_year, last_year+1)

    # Ingest inflation
    inflation = pd.read_csv(
        os.path.join(run_dir, 'inputs_case', 'inflation.csv'), index_col='t'
        ).squeeze(1)

    #%% Derive loads, customer counts, energy intensities
    load_rt = interp_between_solve_years(
        load_rt, 'busbar_load', modeled_years, non_modeled_years, first_year, 
        last_year, r_list, 'r'
        )
    load_rt['end_use_load'] = load_rt['busbar_load'] * (1 - inputs['distloss'])
    load_rt = load_rt.merge(ba_state_map, on='r', how='left')

    load_by_state = load_rt.groupby(
        ['state', 't'], as_index=False
        ).agg({'busbar_load':'sum', 'end_use_load':'sum'})

    load_by_state_eia = pd.read_csv(os.path.join(mdir, 'load_by_state_eia.csv'))
    load_by_state_eia['busbar_load'] = (
        load_by_state_eia['end_use_load'] / (1 - inputs['distloss']))

    # Subset the historical years and append to the project load in ReEDS
    load_historical = load_by_state_eia[load_by_state_eia['t']<first_year]
    load_by_state = pd.concat([
        load_by_state,
        load_historical[['state', 't', 'busbar_load', 'end_use_load']]], 
        sort=False).reset_index(drop=True)
    first_hist_year = load_by_state['t'].min() # cutoff for historical calculations

    # Initialize the main dfall, which tracks outputs by [state, year]
    dfall = pd.DataFrame(
        list(itertools.product(state_list, np.arange(first_hist_year, last_year+1))), 
        columns=['state', 't'])
    dfall = dfall.merge(
        load_by_state[['state', 't', 'busbar_load', 'end_use_load']], 
        on=['state', 't'], how='left')

    #%% Ingest system_costs, which includes some capital expenditures and all operational expenditures
    # Note that the values can be either 'r' or 's' region type in this file
    system_costs = pd.read_csv(
        os.path.join(run_dir, 'outputs', 'systemcost_ba_retailrate.csv'))
    system_costs = system_costs.rename(
        columns={'sys_costs':'cost_type', 'r':'region', 't':'t', 'Value':'cost',
                 'Dim1':'cost_type','Dim2':'region','Dim3':'t','Val':'cost'})
    # Convert s regions to p regions if necessary
    system_costs.loc[system_costs['region'].str.contains('s'), 'region'] = (
        system_costs.loc[system_costs['region'].str.contains('s'), 'region'].map(s2r))
    system_costs = system_costs.groupby(
        by=['cost_type', 'region', 't'], as_index=False).agg({'cost':'sum'})

    system_costs['cost'] = system_costs['cost'].replace('Undf',0).astype(float)

    # Merge on state
    system_costs = system_costs.merge(
        stacked_regions_map[['region', 'state']], on='region', how='left')

    #%% Ingest capital financing assumptions
    # Note that these assumptions are for a regulated utility, whereas ReEDS uses 
    #   technology-specific financing from an IPP perspective. 
    financepath = inputs['financefile']
    if not os.path.exists(financepath):
        financepath = os.path.join(mdir, financepath)
    df_finance = pd.read_csv(financepath, index_col='t')

    #%%####################################
    #    -- State-Flow Expenditures --    #
    #######################################
    print('   - State-Flow Expenditures')
    # Digest State Expenditure flows
    state_flows = (
        pd.read_csv(os.path.join(run_dir, 'outputs', 'expenditure_flow.csv'))
        .rename(columns={
            '*':'price_type', 'r':'sending_region', 
            'rr':'receiving_region', 't':'t', 'Value':'expenditure_flow',
            'Dim1':'price_type', 'Dim2':'sending_region', 
            'Dim3':'receiving_region', 'Dim4':'t', 'Val':'expenditure_flow'})
        )
    state_rps_flows = (
        pd.read_csv(os.path.join(run_dir, 'outputs', 'expenditure_flow_rps.csv'))
        .rename(columns={
            'st':'sending_state', 'ast':'receiving_state', 'Value':'expenditure_flow',
            'Dim1':'sending_state', 'Dim2':'receiving_state', 
            'Dim3':'t',  'Val':'expenditure_flow'})
        )
    state_rps_flows['price_type'] = 'rps'

    ###### International flows
    state_international_flows = (
        pd.read_csv(os.path.join(run_dir, 'outputs', 'expenditure_flow_int.csv'))
        .rename(columns={
            'r':'receiving_region', 't':'t', 'Value':'expenditure_flow',
            'Dim1':'receiving_region','Dim2':'t','Val':'expenditure_flow'})
        )
    ### According to e_report.gms, all international flows are load to/from Canada 
    # (not capacity, reserves, rps, or Mexico)
    state_international_flows['price_type'] = 'load'
    state_international_flows['sending_state'] = 'Canada'
    ### International exports are negative expenditures, imports are positive
    state_international_flows['flowtype'] = state_international_flows['expenditure_flow'].map(
        lambda x: 'export' if x<0 else 'import')
    ### Map regions to states
    state_international_flows['receiving_state'] = (
        state_international_flows['receiving_region'].map(reedsregion2state))
    ### Change sign and sending/receiving state to match conventions for intra-US flows
    for i in state_international_flows.index:
        if state_international_flows.loc[i,'expenditure_flow'] < 0:
            (state_international_flows.loc[i,'sending_state'], 
            state_international_flows.loc[i,'receiving_state']) = (
                state_international_flows.loc[i,'receiving_state'], 
                state_international_flows.loc[i,'sending_state'])
            state_international_flows.loc[i,'expenditure_flow'] = (
                -state_international_flows.loc[i,'expenditure_flow'])

    # Map regions to states
    state_flows['sending_state'] = state_flows['sending_region'].map(reedsregion2state)
    state_flows['receiving_state'] = state_flows['receiving_region'].map(reedsregion2state)

    # Filter Intrastate Expenditure Flows
    state_flows = pd.concat([
        state_flows.loc[state_flows['sending_state'] != state_flows['receiving_state']],
        state_rps_flows,
        state_international_flows], 
        sort=False)

    # Aggregate imports and exports by year, type and state
    sent_expenditures = state_flows.groupby(
        by=['price_type','t', 'sending_state'], as_index=False
        ).agg({'expenditure_flow':'sum'}).rename(columns={
            'sending_state':'state', 'expenditure_flow':'expenditure_exports'})
    received_expenditures = state_flows.groupby(
        by=['price_type','t', 'receiving_state'], as_index=False
        ).agg({'expenditure_flow':'sum'}).rename(columns={
            'receiving_state':'state', 'expenditure_flow':'expenditure_imports'})
    state_flow_expenditures = sent_expenditures.merge(
        received_expenditures, on=['price_type', 't', 'state'], how='outer').fillna(0)

    # As costs are positive, subtract exports (revenue) from imports (costs)
    state_flow_expenditures['net_interstate_expenditures'] = (
        state_flow_expenditures['expenditure_imports'] 
        - state_flow_expenditures['expenditure_exports'])
    state_flow_expenditures = state_flow_expenditures.groupby(
        ['t', 'state', 'price_type'])['net_interstate_expenditures'].sum(
            ).unstack('price_type').reset_index()
    state_flow_expenditures = state_flow_expenditures.add_suffix('_flow').rename(
        columns={'t_flow':'t', 'state_flow':'state'})

    state_flow_expenditures_expanded = interp_between_solve_years(
        state_flow_expenditures, 'load_flow', modeled_years, non_modeled_years, 
        first_year, last_year, state_list, 'state')
    if 'oper_res_flow' in state_flow_expenditures:
        state_flow_expenditures_expanded = state_flow_expenditures_expanded.merge(
            interp_between_solve_years(
                state_flow_expenditures, 'oper_res_flow', modeled_years, 
                non_modeled_years, first_year, last_year, state_list, 'state'), 
            on=['t', 'state'])
    if 'rps_flow' in state_flow_expenditures:
        state_flow_expenditures_expanded = state_flow_expenditures_expanded.merge(
            interp_between_solve_years(
                state_flow_expenditures, 'rps_flow', modeled_years, 
                non_modeled_years, first_year, last_year, state_list, 'state'), 
            on=['t', 'state'])
    state_flow_expenditures_expanded = state_flow_expenditures_expanded.merge(
        interp_between_solve_years(
            state_flow_expenditures, 'res_marg_ann_flow', modeled_years, 
            non_modeled_years, first_year, last_year, state_list, 'state'), 
        on=['t', 'state'])

    ### Canada is dropped since we merge left
    dfall = dfall.merge(
        state_flow_expenditures_expanded, on = ['t','state'], how = 'left').fillna(0)

    #%%#############################################
    #    -- Operational (pass-through) costs --    #
    ################################################
    # All "op_" values in the systemcost_ba output file are assumed to be pass-through 
    # operational costs (i.e. not part of the rate base)
    print('   - Operational (pass-through) Expenditures')
    # Excluded costs
    op_costs_types_omitted = ['op_transmission_fom', 
                              'op_ptc_payments_negative',
                              'op_co2_incentive_negative',
                              'op_h2_ptc_payments_negative',
                              'op_h2_storage',
                              'op_h2_transport', 
                              'op_h2_fuel_costs', 
                              'op_h2_vom',
                              'op_consume_vom',
                              'op_consume_fom']
    # Identify operational costs (by the "op_" prefix) and extract
    op_cost_types = [i for i in system_costs['cost_type'].drop_duplicates() 
    # Leave out 'op_transmission_fom' for now since it's already accounted for
    # separately in 'op_trans' (using FERC data instead of ReEDS)
                     if (('op_' in i) and (i not in op_costs_types_omitted))]
    op_costs_modeled_years = system_costs[system_costs['cost_type'].isin(op_cost_types)].copy()
    
    # Group to states
    op_costs_modeled_years = op_costs_modeled_years.groupby(
        by=['cost_type', 't', 'state'], as_index=False).agg({'cost':'sum'})

    # Expand op_costs to include all years (not just model years), 
    # interpolating the costs between model years
    op_costs = pd.DataFrame()
    for op_cost_type in op_cost_types:
        op_costs_single = (
            op_costs_modeled_years[op_costs_modeled_years['cost_type']==op_cost_type]
            .rename(columns={'cost':op_cost_type}))
        op_costs_single = interp_between_solve_years(
            op_costs_single, op_cost_type, modeled_years, non_modeled_years, 
            first_year, last_year, state_list, 'state')
        op_costs_single['cost_type'] = op_cost_type
        op_costs_single = op_costs_single.rename(columns={op_cost_type:'cost'})
        op_costs = pd.concat([op_costs, op_costs_single], sort=False).reset_index(drop=True)

    op_costs_pivot = op_costs.pivot_table(
        index=['t', 'state'], columns='cost_type', values='cost', fill_value=0.0).reset_index()

    # Read regional emissions
    emissions_r = (
        pd.read_csv(os.path.join(run_dir, 'outputs', 'emit_r.csv'))
        .rename(columns={'Value':'emissions', 'Val':'emissions'})
    )
    # Consider only direct emissions
    emissions_r = emissions_r.loc[
        (emissions_r.etype == 'process')
        & (emissions_r.eall == 'CO2')
    ].drop(columns=['etype', 'eall'])
    # Create list of regions with emissions
    r_list_emissions = emissions_r['r'].drop_duplicates()
    # Interpolate emissions between solve years
    emissions_r = interp_between_solve_years(
        emissions_r,
        'emissions',
        modeled_years,
        non_modeled_years,
        first_year,
        last_year,
        r_list_emissions,
        'r',
    )
    # Remove negative emissions
    emissions_r.loc[emissions_r['emissions'] < 0, 'emissions'] = 0
    emissions_no_negative = emissions_r.copy()

    ### Redistribute the DAC op costs
    # DAC has negative CO2 emissions, which allows fossil generators to continue to operate.
    # This redistribution shares the cost of the DAC with any region that is still emitting CO2.
    # In this way, states with fossil units but no DAC still incur costs for the DAC.
    if 'op_co2_transport_storage' in op_costs_pivot.columns:
        # Match the BAs with the respective states
        regions_map_emissions = regions_map.copy()[['r','state']]
        regions_map_emissions = regions_map_emissions[regions_map_emissions['r'].isin(r_list_emissions)]
        ba_state_map_emissions = regions_map_emissions[['r', 'state']].drop_duplicates()
        
        # Consolidate emissions by state
        emissions_r = emissions_r.merge(ba_state_map_emissions, on='r', how='left')
        emissions_by_state = emissions_r.groupby(['state', 't'], as_index=False).agg({'emissions':'sum'})
        emissions_by_state = emissions_by_state.pivot_table(
                index='t', columns='state', values='emissions').fillna(0)
        
        # Fill in zero for states where no emissions info is available
        num_states = len(state_list)
        if num_states != emissions_by_state.shape[1]:
            col_list = list(emissions_by_state.columns)
            missing_states = list(set(state_list) - set(col_list))
            for state in missing_states:
                emissions_by_state[state] = 0
        
        # Calculate the fraction of emissions by state
        emissions_by_state['Total'] = emissions_by_state.sum(axis=1)
        emissions_by_state_fraction = emissions_by_state.copy()
        st_cols = [c for c in emissions_by_state.columns if c != 'Total']
        emissions_by_state_fraction[st_cols] = (
            emissions_by_state_fraction[st_cols].div(emissions_by_state_fraction['Total'], axis=0)
            )
        emissions_by_state_fraction.drop(columns=['Total'], inplace=True)
        del st_cols
        
        # Redistribute DAC costs by emissions fraction
        op_costs_dac_corrections = op_costs_pivot[['t','state','op_co2_transport_storage']].copy()
        op_costs_dac_corrections['op_co2_transport_storage'] = 0
        op_costs_dac_corrections = op_costs_dac_corrections.pivot_table(
            index='t', columns='state', values='op_co2_transport_storage')
    
        for i in range(op_costs_pivot.shape[0]):
            cost = op_costs_pivot.loc[i, 'op_co2_transport_storage']
            year = op_costs_pivot.loc[i, 't']
            multiplier = emissions_by_state_fraction.loc[year]
            assert(multiplier.shape[0]==num_states)
            op_costs_dac_corrections.loc[year] += (cost * multiplier)
        
        # Assign the redistributed DAC costs to the original dataframe
        op_costs_dac_corrections = op_costs_dac_corrections.T
        op_costs_dac_corrections_unstacked = op_costs_dac_corrections.unstack()
        ## Ensure all op values for DAC post-distribution are accounted for
        ## NOTE: near-zero values in op_costs_dac_corrections must be kept to ensure the assertion works,
        ## but technically can be removed/ignored afterwards
        assert(round(op_costs_pivot['op_co2_transport_storage'].values.sum(),2) 
               == round(op_costs_dac_corrections_unstacked.values.sum(),2))
        op_costs_pivot['op_co2_transport_storage'] = op_costs_dac_corrections_unstacked.values
#%%    
    # Extrapolate FOM costs backwards using the constant normalized cost by load 
    # from first modeled year
    historical_years = np.arange(load_by_state['t'].min(), load_rt['t'].min() )
    df_extrapolate = pd.DataFrame(
        list(itertools.product(state_list, historical_years)), 
        columns=['state', 't'])
    op_costs_pivot = op_costs_pivot.merge(
        load_by_state[['state', 't', 'end_use_load']], 
        on=['state', 't'], how='left')
    op_costs_first_year = (
        op_costs_pivot.loc[op_costs_pivot['t'] == 2010, 
        ['state', 'end_use_load', 'op_fom_costs']])
    op_costs_first_year = op_costs_first_year.rename(
        columns={'end_use_load':'load_first_year', 'op_fom_costs':'op_fom_costs_first_year'})
    df_extrapolate = df_extrapolate.merge(op_costs_first_year, on=['state'], how='left')
    df_extrapolate = df_extrapolate.merge(load_by_state, on=['state', 't'], how='left')
    df_extrapolate['op_fom_costs']  = (
        df_extrapolate['end_use_load'] 
        / df_extrapolate['load_first_year'] 
        * df_extrapolate['op_fom_costs_first_year'])
    df_extrapolate = df_extrapolate[['t','state','op_fom_costs']]
    op_costs_pivot = pd.concat([op_costs_pivot, df_extrapolate], sort=False) 
    op_costs_pivot['op_fom_costs'] = (
        (1-inputs['FOM_capitalization_rate']) * op_costs_pivot['op_fom_costs'])

    # Merge on financing assumptions, for calculating return on working capital, 
    # which we consider an operating cost
    op_costs_pivot = op_costs_pivot.merge(df_finance, on='t', how='left')
    # Working capital is the net value of current assets minus current liabilities 
    # that the utility needs to conduct its operations. We estimate the total amount 
    # of working capital as the equivalent of 45 days of all operating expenses 
    # (i.e., 45/365 × annual operating expenses). 
    op_costs_pivot['wc'] = (
        (inputs['working_capital_days'] / 365) * op_costs_pivot[op_cost_types].sum(axis=1))

    op_costs_pivot['op_wc_debt_interest'] = (
        op_costs_pivot['wc'] * op_costs_pivot['debt_fraction'] 
        * op_costs_pivot['debt_interest_nominal'])
    op_costs_pivot['op_wc_equity_return'] = (
        op_costs_pivot['wc'] 
        * (1.0 - op_costs_pivot['debt_fraction']) 
        * op_costs_pivot['equity_return_nominal'])
    op_costs_pivot['op_wc_return_to_capital'] = (
        op_costs_pivot['op_wc_debt_interest'] + op_costs_pivot['op_wc_equity_return'])
    op_costs_pivot['op_wc_income_tax'] = (
        op_costs_pivot['op_wc_equity_return'] / (1.0 - op_costs_pivot['tax_rate']) 
        - op_costs_pivot['op_wc_equity_return'])

    dfall = dfall.merge(
        op_costs_pivot[
            op_cost_types 
            + ['t', 'state', 'op_wc_debt_interest', 'op_wc_equity_return', 'op_wc_income_tax']],
        on=['t', 'state'], how='left')

    #%%#################################
    #    -- Capital Expenditures --    #
    ####################################
    print('   - Capital Expenditures')
    # Calculate the portion of FOM costs that are capitalized, 
    # and use that to initialize the df_capex dataframe
    df_fom_capitalized = op_costs_pivot[['t', 'state', 'op_fom_costs']].copy()
    df_fom_capitalized['capex'] = (
        df_fom_capitalized['op_fom_costs'] 
        / (1.0 - inputs['FOM_capitalization_rate']) * inputs['FOM_capitalization_rate'])
    df_fom_capitalized.drop(columns=['op_fom_costs'], inplace=True)
    df_fom_capitalized['eval_period'] = input_eval_periods['fom_capitalized']
    df_fom_capitalized['depreciation_sch'] = input_depreciation_schedules['fom_capitalized']
    df_fom_capitalized['i'] = 'capitalized_fom'
    df_fom_capitalized['region'] = None
    df_fom_capitalized['cost_cat'] = 'cap_fom'

    # df_capex has all capital expenditures, including historical expenditures
    df_capex = df_fom_capitalized.copy()
    
    #%% Calculate capex for generators, add to df_capex
    
    # Note that it would be better to directly calculate the capital expenditures within ReEDS, 
    # but we have not implemented that approach yet. 

    # Ingest annual capacity builds (note that cap_new_ivrt includes refurbished capacity)
    cap_new_ivrt = pd.read_csv(
        os.path.join(run_dir, 'outputs', 'cap_new_ivrt.csv')
        ).rename(columns={
            'i':'i', 'r':'region', 't':'t_modeled', 'Value':'cap_new', 
            'Dim1':'i', 'Dim2':'v', 'Dim3':'region', 'Dim4':'t_modeled', 'Val':'cap_new'})
    # Convert s regions to p regions if necessary
    cap_new_ivrt.loc[cap_new_ivrt['region'].str.contains('s'), 'region'] = (
        cap_new_ivrt.loc[cap_new_ivrt['region'].str.contains('s'), 'region'].map(s2r))
    cap_new_ivrt = cap_new_ivrt.groupby(
        by=['i', 'region', 't_modeled'], as_index=False).agg({'cap_new':'sum'})
    
    # Equally distribute the capacity across the solve years. This is not exactly how ReEDS 
    # sees it, but smooths out some unrealistic periodicity in the expensing patterns that 
    # would otherwise appear.
    cap_new_ivrt_distributed = distribute_between_solve_years(
        cap_new_ivrt, 'cap_new', modeled_years, years_reeds)

    # Create dataframe from capacity additions to be merged later with capex
    df_gen_capex = cap_new_ivrt_distributed[['i', 'region', 't', 'cap_new']].copy()
    df_gen_capex = df_gen_capex.groupby(
        by=['i', 'region', 't'], as_index=False).agg({'cap_new':'sum'})
    
    # Read in generator capex
    # All costs except upgrades are calculated using cost_cap_fin_mult_no_credits
    # Upgrade costs are calculated using cost_cap_fin_mult_out (full ITC/PTC/depreciation)
    df_capex_irt = pd.read_csv(
        os.path.join(run_dir, 'outputs', 'capex_ivrt.csv')
        ).rename(columns={'r':'region', 't':'t_modeled', 'Value':'capex'})
    # Get rid of the v index
    df_capex_irt = df_capex_irt.groupby(
        by=['i', 'region', 't_modeled'], as_index=False).agg({'capex':'sum'})
    
    # Read in Tech|BA-Level system costs
    # Most costs are calculated using cost_cap_fin_mult_noITC
    # rsc tech costs are calculated using rsc_fin_mult or rsc_fin_mult_noITC
    invcapcosts = ['inv_dac', 'inv_h2_production', 'inv_investment_capacity_costs', 
                   'inv_investment_refurbishment_capacity',
                   'inv_investment_spurline_costs_rsc_technologies',]
    df_syscost_irt = pd.read_csv(
        os.path.join(run_dir, 'outputs', 'systemcost_techba.csv')
        ).rename(columns={'r':'region', 't':'t_modeled', 'Value':'capex'})
    df_syscost_irt = df_syscost_irt[df_syscost_irt['sys_costs'].isin(invcapcosts)]
    df_syscost_irt = df_syscost_irt.groupby(
        by=['i', 'region', 't_modeled'], as_index=False).agg({'capex':'sum'})
    
    # Merge and take maximum of two capex sources 
    df_capex_irt = df_capex_irt.merge(
        df_syscost_irt, on=['i', 'region', 't_modeled'], how='outer', 
        suffixes=('_capex','_syscost'))
    df_capex_irt['capex'] = df_capex_irt[['capex_capex', 'capex_syscost']].max(axis=1)
    df_capex_irt = df_capex_irt[['i', 'region', 't_modeled', 'capex']]
    
    # Distribute among all years / between solve years
    df_capex_irt_distributed = distribute_between_solve_years(
        df_capex_irt, 'capex', modeled_years, years_reeds)
    
    #%% Redistribute the DAC capex costs
    # Just as with DAC operating costs, DAC capex costs should be redistributed to where 
    # any region that is still emitting CO2 via operation of fossil units 
    # incurs the costs of DAC 
    if 'dac' in df_capex_irt_distributed['i'].unique():
        # Calculate the fraction of emissions by BA
        emissions_fraction = emissions_no_negative.pivot_table(
            index='t', columns='r', values='emissions').fillna(0)
        emissions_fraction['Total'] = emissions_fraction.sum(axis=1)
        ba_cols = [c for c in emissions_fraction.columns if c != 'Total']
        emissions_r_fraction = emissions_fraction.copy() 
        emissions_r_fraction[ba_cols] = (
            emissions_r_fraction[ba_cols].div(emissions_r_fraction['Total'], axis=0)
            )
        emissions_r_fraction.drop(columns=['Total'], inplace=True)
        del ba_cols
        
        # Redistribute DAC costs by emissions fraction
        dac_mask = df_capex_irt_distributed['i']=='dac'
        capex_dac = df_capex_irt_distributed[dac_mask].copy().fillna(0)
        capex_dac.drop(['i'], axis=1, inplace=True)
        capex_dac = capex_dac.rename(columns={'region':'r'})
        capex_dac = capex_dac.reset_index(drop=True)
        
        capex_dac_corrections = df_capex_irt_distributed.pivot_table(index='region',columns='t',values='capex')
        capex_dac_corrections.loc[:, :] = 0
        
        # Remove missing BAs where emissions info is not available
        missing_r = list(set(capex_dac_corrections.index) - set(emissions_r_fraction.columns))
        capex_dac_corrections.drop(missing_r, axis=0, inplace=True)
        
        num_r = capex_dac_corrections.shape[0]
        
        # Recalculate the DAC capex using fractional emissions
        for i, row in capex_dac.iterrows():
            cost = row['capex']
            year = row['t']
            if year <= last_year:
                multiplier = emissions_r_fraction.loc[year]
                assert(multiplier.shape[0]==num_r)
                capex_dac_corrections.loc[:,year] += (cost * multiplier)
        
        # Assign zero to missing BAs
        for r in missing_r:
            capex_dac_corrections.loc[r, :] = 0
        
        # Reformat capex_dac_corrections df to long format to merge back onto the original df
        ## Remove all years with zero total capex
        capex_dac_corrections = capex_dac_corrections.loc[:, (capex_dac_corrections.sum(axis=0) != 0)]
        capex_dac_corrections = capex_dac_corrections.reset_index().melt(id_vars='region', value_name='capex')
        capex_dac_corrections = capex_dac_corrections.assign(i='dac')
        ## Ensure all capex values for DAC post-distribution are accounted for
        ## NOTE: near-zero values in capex_dac_corrections must be kept to ensure the assertion works,
        ## but technically can be removed/ignored afterwards
        assert(round(capex_dac_corrections['capex'].sum(),2) == round(capex_dac['capex'].sum(),2))
        
        ## Add the corrected DAC capex onto original df and remove old DAC capex rows
        df_capex_irt_distributed = pd.concat([
            df_capex_irt_distributed[~dac_mask][['i','region','t','capex']],
            capex_dac_corrections[['i','region','t','capex']].sort_values(by=['region','t'])
            ])
        
    # Merge new capacity and capex
    df_gen_capex = df_gen_capex.merge(
        df_capex_irt_distributed[['i', 'region', 't', 'capex']], 
        on=['i', 'region', 't'], how='outer')

#%% # Ingest evaluation period and tax depreciation schedule info for generators
    eval_period = read_file(os.path.join(run_dir, 'inputs_case', 'retail_eval_period'))
    depreciation_sch = read_file(os.path.join(run_dir,'inputs_case','retail_depreciation_sch'))
    depreciation_sch['depreciation_sch'] = depreciation_sch['depreciation_sch'].astype(str)
    
    # Merge generator capex on eval_period and depreciation_sch
    df_gen_capex = df_gen_capex.merge(
        eval_period[['i', 't', 'eval_period']], 
        on=['i', 't'], how='left')
    # Fill in any missing eval_period with the default 20 years
    # This should apply to upgrades only
    df_gen_capex['eval_period'].fillna(20, inplace=True)
    df_gen_capex = df_gen_capex.merge(
        depreciation_sch[['i', 't', 'depreciation_sch']], 
        on=['i', 't'], how='left')
    # Fill in any missing eval_period with the default 20 years
    # This should also apply to upgrades only
    df_gen_capex['depreciation_sch'].fillna('20', inplace=True)
    
#%% # For historical capital expenditures, we use a pre-calculated result.
    #   The expenditures are based on a EIA-NEMS database of historical capacity 
    #   builds, using the earliest capital costs from the provided ReEDS run. 
    #   The values in this file are in 2004 dollars. This file is generated by 
    #   calculate_historical_capex.py
    df_gen_capex_init = pd.read_csv(
        os.path.join(run_dir, 'inputs_case', 'df_capex_init.csv'))
    df_gen_capex_init = df_gen_capex_init[df_gen_capex_init['t']<=first_year]
    df_gen_capex_init = df_gen_capex_init[df_gen_capex_init['t']>=first_hist_year]
    # Convert s regions to p regions
    df_gen_capex_init.loc[df_gen_capex_init['region'].str.contains('s'), 'region'] = (
        df_gen_capex_init.loc[df_gen_capex_init['region'].str.contains('s'), 'region'].map(s2r))
    df_gen_capex_init = df_gen_capex_init.groupby(
        by=['i', 'region', 't'], as_index=False).agg({'cap_new':'sum', 'capex':'sum'})
    
    # Find tech-region-year combos for historical builds, 
    # for expanding out eval_period and dep_schedules
    init_irt = df_gen_capex_init[['i', 'region', 't']].copy().drop_duplicates()

    # Expand eval_period for historical builds (assigning historical builds the earliest data)
    eval_period_init = init_irt.copy()
    eval_period_init = eval_period_init.merge(
        eval_period[eval_period['t']==first_year][['i', 'eval_period']], 
        on='i', how='left')
    eval_period_init = eval_period_init[eval_period_init['t']<=first_year]

    # Expand depreciation_sch for historical builds (assigning historical builds the earliest data)
    dep_sch_init = init_irt.copy()
    dep_sch_init = dep_sch_init.merge(
        depreciation_sch[depreciation_sch['t']==first_year][['i', 'depreciation_sch']], 
        on='i', how='left')
    dep_sch_init = dep_sch_init[dep_sch_init['t']<=first_year]

    # Merge on eval_period, depreciation_sch, state, and cost category for generator capex
    df_gen_capex_init = df_gen_capex_init.merge(
        eval_period_init[['i', 'region', 't', 'eval_period']], 
        on=['i', 'region', 't'], how='left')
    # Fill in any missing eval_period with the default 20 years
    df_gen_capex_init['eval_period'].fillna(20, inplace=True)
    df_gen_capex_init = df_gen_capex_init.merge(
        dep_sch_init[['i', 'region', 't', 'depreciation_sch']], 
        on=['i', 'region', 't'], how='left')
    df_gen_capex_init['depreciation_sch'].fillna('20', inplace=True)

#%% # Combine both new and historical capital expenditures
    df_gen_capex = pd.concat(
        [df_gen_capex, df_gen_capex_init], sort=False).reset_index(drop=True)
    df_gen_capex = df_gen_capex.merge(
        stacked_regions_map[['region', 'state']], on=['region'], how='left')
    df_gen_capex['cost_cat'] = 'cap_gen'
    
    # Remove null capex values to remove distpv
    # Also removes 5 MW pumped-hydro built in p64 in 2012 (cap_new but no capex)
    df_gen_capex.dropna(
        axis=0, how='all', subset='capex', inplace=True, ignore_index=True)
    
    # Toggle to test for longer accounting depreciation periods. 
    if inputs['eval_period_overwrite'] != 0: 
        df_gen_capex['eval_period'] = inputs['eval_period_overwrite']

    # Add generator capex to df_capex
    df_capex = pd.concat(
        [df_capex, 
         df_gen_capex[
             ['i', 'region', 'state', 't', 'cost_cat', 'capex', 
              'eval_period', 'depreciation_sch']]], 
        sort=False).reset_index(drop=True)
    
    #%% Add non-generator, within-ReEDS capital expenditures to df_capex
    # Transmission, converter, and intertie capital expenditures
    # These could be wrapped into various other cost types (intra-BA transmission,
    # distribution and transmission infrastructure, etc).
    
    # Combine intrazone and interzone transmission
    system_costs.loc[system_costs['cost_type']=='inv_transmission_intrazone_investment', 
                     'cost_type'] = 'inv_transmission_interzone_ac_investment'
    system_costs = system_costs.copy().groupby(
        by=['cost_type', 'region', 't', 'state'], as_index=False).agg({'cost':'sum'})
    
    nongen_inv_eval_periods = pd.DataFrame(
        columns=['cost_type', 'eval_period'],
        data=[
            [x,input_eval_periods[x]]
            for x in [
                'inv_investment_spurline_costs_rsc_technologies',
                'inv_transmission_line_investment',
                'inv_transmission_interzone_ac_investment',
                'inv_transmission_interzone_dc_investment',
                'inv_converter_costs',
            ]
        ]
    )

    # Define and merge on the cost categories for these capital expenditures
    nongen_cost_cats = pd.DataFrame(
        columns=['i', 'cost_cat'],
        data = [['inv_investment_spurline_costs_rsc_technologies', 'cap_spurline'],
                ['inv_transmission_line_investment', 'cap_transmission'],
                ['inv_transmission_interzone_ac_investment', 'cap_transmission'],
                ['inv_transmission_interzone_dc_investment', 'cap_transmission'],
                ['inv_converter_costs', 'cap_converter']]
        )

    nongen_inv_cost_types = list(nongen_inv_eval_periods['cost_type'].drop_duplicates())
        
    nongen_capex = system_costs[system_costs['cost_type'].isin(nongen_inv_cost_types)]
    nongen_capex = nongen_capex.merge(nongen_inv_eval_periods, on='cost_type', how='left')
    nongen_capex['depreciation_sch'] = input_depreciation_schedules['nongen_capex']
    
    # Distributing the nongen capex evenly between solve years
    nongen_capex = nongen_capex.rename(columns={'t':'t_modeled'})
    nongen_capex_distributed = distribute_between_solve_years(
         nongen_capex, 'cost', modeled_years, years_reeds)
    
    # We're categorizing these as 'i's, even though they aren't thought of as a tech
    # within ReEDS. 
    nongen_capex_distributed.rename(columns={'cost_type':'i', 'cost':'capex'}, inplace=True)
    nongen_capex_distributed.drop(columns=['t_modeled', 'alloc_f'], inplace=True)
    # Merge on the cost_cat - just a shorter name for columns used elsewhere
    nongen_capex_distributed = nongen_capex_distributed.merge(nongen_cost_cats, on='i', how='left')

    # Add to the main df_capex
    df_capex = pd.concat([df_capex, nongen_capex_distributed], sort=False).reset_index(drop=True)

    #%% Estimate historical capital expenditures for existing transmission capacity
    ### by state and add to df_capex
    ### Note that we're leaving out the cost of converters for LCC and B2B lines
    inflatable = reeds.io.get_inflatable()
    existing_transmission_cost_bystate = pd.read_csv(
        os.path.join(
            mdir, 'calc_historical_capex',
            'existing_transmission_cost_bystate_USD2024.csv'),
        index_col='state',
    ).squeeze(1).rename('init_trans_capex') * inflatable[2024, 2004]
    # This approach assumes the existing transmission capacity was built evently 
    # over the trans_timeframe years prior to 2010
    init_trans_capex = pd.concat(
        {t: existing_transmission_cost_bystate
         for t in np.arange(first_year - inputs['trans_timeframe'], first_year)},
         names='t',
    ).reset_index()
    init_trans_capex['i'] = 'inv_transmission_interzone_ac_investment'
    init_trans_capex['capex'] = init_trans_capex['init_trans_capex'] / inputs['trans_timeframe']
    init_trans_capex['eval_period'] = input_eval_periods['init_trans_capex']
    init_trans_capex['depreciation_sch'] = input_depreciation_schedules['init_trans_capex']
    init_trans_capex['cost_cat'] = 'cap_transmission'

    df_capex = pd.concat(
        [df_capex, 
         init_trans_capex[
             ['i', 'state', 't', 'capex', 
              'eval_period', 'depreciation_sch', 'cost_cat']]], 
        sort=False).reset_index(drop=True)

    #%% Ingest operational and capital expenditures for both Distribution and Administration
    ### Returns historical values and forward projections based on assumptions provided
    dist_admin_costs_nation_in = ferc_distadmin.get_ferc_costs(
        numslopeyears=input_daproj['numslopeyears'], numprojyears=input_daproj['numprojyears'],
        current_t=input_daproj['current_t'], aggregation='nation',
        writeout=False,
        inflationpath=os.path.join(run_dir, 'inputs_case', 'inflation.csv'),
        drop_pgesce_20182019=input_daproj['drop_pgesce_20182019'],
        cleanup=input_daproj['cleanup'],
        )
    ### Duplicate national values for each state.
    ### We can do so because the costs we need are already in $/MWh (rather than $).
    dist_admin_costs_nation = (
        pd.concat({state: dist_admin_costs_nation_in for state in states
                   if state in ferc_distadmin.state2region.keys()}, axis=0)
        .reset_index(level=0).rename(columns={'level_0':'state'})
        .sort_values(['state','t']).set_index(['state','t'])
        .drop('nation',axis=1)
        )

    ### Load the region-specific version
    dist_admin_costs_region_in = ferc_distadmin.get_ferc_costs(
        numslopeyears=input_daproj['numslopeyears'], numprojyears=input_daproj['numprojyears'],
        current_t=input_daproj['current_t'], aggregation='region',
        writeout=False,
        inflationpath=os.path.join(run_dir, 'inputs_case', 'inflation.csv'),
        drop_pgesce_20182019=input_daproj['drop_pgesce_20182019'],
        cleanup=input_daproj['cleanup'],
        ).sort_values(['region','t']).set_index(['region','t'])
    ### Duplicate regional values for each state
    dist_admin_costs_region = (
        pd.concat(
            {state: dist_admin_costs_region_in.loc[ferc_distadmin.state2region[state]] 
            for state in states if state in ferc_distadmin.state2region.keys()},
            axis=0)
        .reset_index().rename(columns={'level_0':'state'})
        .sort_values(['state','t']).set_index(['state','t'])
        )

    ### Load the state-specific version if we need it
    if input_daproj['aggregation'] in ['state','best']:
        dist_admin_costs_state = ferc_distadmin.get_ferc_costs(
            numslopeyears=input_daproj['numslopeyears'], numprojyears=input_daproj['numprojyears'],
            current_t=input_daproj['current_t'], aggregation='state',
            writeout=False,
            inflationpath=os.path.join(run_dir, 'inputs_case', 'inflation.csv'),
            drop_pgesce_20182019=input_daproj['drop_pgesce_20182019'],
            cleanup=input_daproj['cleanup'],
            ).sort_values(['state','t']).set_index(['state','t'])
        ### NE is missing from dist_admin_costs_state, so assign it to the regional value
        if 'NE' in dist_admin_costs_region.index.get_level_values('state').unique():
            dist_admin_costs_state = pd.concat(
                [dist_admin_costs_state, dist_admin_costs_region.loc[['NE']]]
            )

    #%% Assign dist_admin_costs based on aggregation level
    if input_daproj['aggregation'] == 'nation':
        dist_admin_costs = dist_admin_costs_nation.copy()
    elif input_daproj['aggregation'] == 'region':
        dist_admin_costs = dist_admin_costs_region.copy()
    elif input_daproj['aggregation'] == 'state':
        dist_admin_costs = dist_admin_costs_state.copy()
    elif input_daproj['aggregation'] == 'best':
        ### Start with national values
        dist_admin_costs = dist_admin_costs_nation.copy()
        keepstates = dist_admin_costs.index.get_level_values('state').unique()
        ### Get the list of states where aggregation=='state' gives the lowest error
        best = pd.read_csv(
            os.path.join(mdir,'inputs','state-meanbiaserror_rate-aggregation.csv'),
            usecols=['index','aggregation'], index_col='index',
        ).squeeze(1).loc[keepstates]
        replacestates = best.loc[best=='state'].index.values
        replaceregions = best.loc[best=='region'].index.values
        ### Drop these states, then add back the state/region-specific values
        dist_admin_costs = pd.concat([
            pd.concat([
                ### Sub the states where state aggregation gives the closest fit
                dist_admin_costs.drop(replacestates, axis=0, level=0),
                dist_admin_costs_state.loc[replacestates]
                ### Sub the regions where region aggregation gives the closest fit
                ]).drop(replaceregions, axis=0, level=0),
            dist_admin_costs_region.loc[replaceregions],
            ])
    ### Go back to integer index
    dist_admin_costs.reset_index(inplace=True)

    ### Project backward to first year, backfilling missing values
    extrapolation_years = list(range(first_hist_year, dist_admin_costs.t.min()))
    insert = pd.DataFrame(
        {'t': extrapolation_years * len(states),
        'state': [item for sublist in [[s] * len(extrapolation_years) for s in states] 
                for item in sublist]}
        )
    dist_admin_costs = (
        pd.concat([dist_admin_costs, insert])
        .sort_values(['state','t']).reset_index(drop=True))
    ### Backward-fill for only the per_mwh columns
    bfillcols = [c for c in dist_admin_costs if c.endswith('_per_mwh')]
    dist_admin_costs[bfillcols] = dist_admin_costs[bfillcols].interpolate('bfill')
    dist_admin_costs.loc[dist_admin_costs.entry_type.isnull(), 'entry_type'] = 'bfill'

    #%% Add excluded costs back in with specialized amortization assumptions
    if input_daproj['drop_pgesce_20182019']:
        #% Get the excluded costs and sum by state
        excluded_costs = (
            ferc_distadmin.get_excluded_costs(
                inflationpath=os.path.join(run_dir, 'inputs_case', 'inflation.csv'),
                dollar_year=inputs['dollar_year'])
            .rename(columns={'Year':'t','State':'state'})
            .groupby(['t','state']).sum(numeric_only=True)
            ### Sum over columns (by t,state) in case we exclude multiple columns
            .sum(axis=1).rename('special_costs_year0')
            )

        #% Get the CRF for the excluded costs
        wacc = {
            t: get_wacc_nominal(
                debt_fraction=df_finance.loc[t,'debt_fraction'],
                equity_return_nominal=df_finance.loc[t,'equity_return_nominal'],
                debt_interest_nominal=df_finance.loc[t,'debt_interest_nominal'],
                tax_rate=df_finance.loc[t,'tax_rate'])
            for t in df_finance.index
            }
        wacc_real = {t: get_wacc_real(wacc[t], (inflation.loc[t] - 1)) for t in wacc}
        crf = {
            t: get_crf(wacc_real[t], input_eval_periods['special_costs'])
            for t in wacc_real
            }
        
        #% Get the annuities
        annuities = {
            (t,state):  excluded_costs.loc[(t,state)] * crf[t]
            for (t,state) in excluded_costs.index
            }
        
        #% Create the cost series. Apply for input_eval_periods['special_costs']
        ### starting in the year in which the cost is incurred.
        annuityprofile = pd.concat({
            (state,t): pd.Series(
                index=range(t,t+input_eval_periods['special_costs']),
                data=annuities[t,state])
            for (t,state) in annuities
            }, axis=1).fillna(0).stack(level=0).sum(axis=1).rename('special_costs')
        annuityprofile.index.rename(['t','state'],inplace=True)

        #% Store it
        dfall = dfall.merge(annuityprofile, on=['state','t'], how='left')


    #%% Add distribution and adminstrative capex to df_capex
    dist_admin_opex = load_by_state.merge(dist_admin_costs, on=['t','state'], how='inner') 

    ########## Operational costs for both Distribution and Admin ##############
    dist_admin_opex['op_dist'] = (
        dist_admin_opex['end_use_load'] * dist_admin_opex['dist_opex_per_mwh'])
    dist_admin_opex['op_admin'] = (
        dist_admin_opex['end_use_load'] * dist_admin_opex['admin_opex_per_mwh'])

    dfall = dfall.merge(
        dist_admin_opex[['t', 'state', 'op_dist', 'op_admin']], on=['t', 'state'], how='left')

    ########################### Distribution capex ############################
    dist_capex = dist_admin_costs[['t','state','dist_capex_per_mwh']].copy()
    dist_capex = load_by_state.merge(dist_capex, on=['t','state'], how='inner')

    dist_capex['capex'] = dist_capex['end_use_load'] * dist_capex['dist_capex_per_mwh']
    dist_capex['eval_period'] = input_eval_periods['dist_capex']
    dist_capex['depreciation_sch'] = input_depreciation_schedules['dist_capex']
    dist_capex['cost_cat'] = 'cap_dist'

    df_capex = pd.concat(
        [df_capex, 
         dist_capex[
             ['state', 't', 'capex', 'eval_period', 'depreciation_sch', 'cost_cat']]], 
        sort=False).reset_index(drop=True)

    ############################### Admin capex ###############################
    admin_capex = dist_admin_costs[['t','state','admin_capex_per_mwh']].copy()
    admin_capex = load_by_state.merge(admin_capex, on=['t','state'], how='inner') 

    admin_capex['capex'] = admin_capex['end_use_load'] * admin_capex['admin_capex_per_mwh']
    admin_capex['eval_period'] = input_eval_periods['admin_capex']
    admin_capex['depreciation_sch'] = input_depreciation_schedules['admin_capex']
    admin_capex['cost_cat'] = 'cap_admin'

    df_capex = pd.concat(
        [df_capex, 
         admin_capex[
             ['state', 't', 'capex', 'eval_period', 'depreciation_sch', 'cost_cat']]], 
        sort=False).reset_index(drop=True)

    #%%######################## Transmission capex ############################
    ### Special projection for transmission capex: FERC trans_capex minus ReEDS capex
    ### during overlap years. FERC trans_capex then roughly corresponds to intra-BA
    ### transmission, which isn't captured by ReEDS.

    ### Get the ReEDS transmission (transmission and spur lines)
    ### NOTE: cap_transmission has a 30-year eval_period,
    ### while cap_spurline has a 20-year eval_period.
    trans_capex_reeds = nongen_capex_distributed.groupby(
        ['state','t'])['capex'].sum().unstack('t').sort_index(axis=1).fillna(0)
        
    ### Distribute capex between solve years
    reedsyears = trans_capex_reeds.columns.values
    for column, reedsyear in enumerate(reedsyears[:-1]):
        numyears = reedsyears[column+1] - reedsyears[column]
        addyears = list(range(reedsyear+1, reedsyear+numyears))
        ### Divide the value in reedsyear by numyears and spread over addyears
        trans_capex_reeds[reedsyear] /= numyears
        for year in addyears:
            trans_capex_reeds[year] = trans_capex_reeds[reedsyear]
    ### Put back in original format and proceed
    trans_capex_reeds = (
        trans_capex_reeds.sort_index(axis=1).stack()
        .rename('trans_capex_reeds').reset_index())
    ### Add FERC region
    trans_capex_reeds['region_ferc'] = (
        trans_capex_reeds['state'].map(ferc_distadmin.state2region).values
        )
    ### Get the years where FERC and ReEDS data overlap
    years_overlap = list(range(
        trans_capex_reeds.t.min(),
        dist_admin_costs_region_in.loc[
            dist_admin_costs_region_in.entry_type=='historical'].reset_index()['t'].max() + 1
        ))
    ### Merge ReEDS and FERC trans capex on (ferc_region,t)
    ferc_trans_capex = (
        dist_admin_costs_region_in.reset_index()
        .rename(columns={'trans_capex':'trans_capex_ferc','region':'region_ferc'})
        .set_index(['region_ferc','t'])
        .merge(trans_capex_reeds.groupby(['region_ferc','t']).agg({'trans_capex_reeds':'sum'}), 
            left_index=True, right_index=True, how='outer')
        ### Downselect to overlap years and columns
        .loc[(slice(None), years_overlap), 
            ['energy_sales','trans_capex_ferc','trans_capex_per_mwh','trans_capex_reeds']]
        .fillna(0)
        )
    ### Double-check that FERC values are self-consistent
    assert not any(
        ferc_trans_capex['trans_capex_ferc'] / ferc_trans_capex['energy_sales'] 
        - ferc_trans_capex['trans_capex_per_mwh'])
    ### Corrected values given by FERC minus ReEDS
    ferc_trans_capex['trans_capex_per_mwh_ferconly'] = (
        (ferc_trans_capex['trans_capex_ferc'] 
        - ferc_trans_capex['trans_capex_reeds'])
        / ferc_trans_capex['energy_sales']
        )
    ### Project forward
    projcol = 'trans_capex_per_mwh_ferconly'
    forecasts = {}
    for region_ferc in ferc_trans_capex.reset_index()['region_ferc'].unique():
        ## Get the fit parameters
        slope, intercept = np.polyfit(
            ## Take the last input_daproj['numslopeyears'] years of years_overlap
            x=years_overlap[-input_daproj['numslopeyears']:],
            y=ferc_trans_capex.loc[
                (region_ferc, years_overlap[-input_daproj['numslopeyears']:]),
                projcol
                ].values, 
            deg=1,
            )
        ## Yearly delta decreases by 1/input_daproj['numprojyears'] each year
        if input_daproj['numprojyears'] == 0:
            slopes = [0 for t in range(trans_capex_reeds.t.max() - max(years_overlap))]
        else:
            slopes = [
                max(slope * (1 - t/input_daproj['numprojyears']), 0) if slope >= 0
                else min(slope * (1 - t/input_daproj['numprojyears']), 0)
                for t in range(trans_capex_reeds.t.max() - max(years_overlap))
                ]
        last_historical_fit = intercept + slope * max(years_overlap)
        forecasts[region_ferc] = pd.DataFrame(
            index=range(max(years_overlap) + 1, trans_capex_reeds.t.max() + 1),
            data={projcol: last_historical_fit + np.cumsum(slopes)})
    ferc_trans_capex = pd.concat([ferc_trans_capex[[projcol]], pd.concat(forecasts,axis=0)])
    ### Broadcast to states
    ferc_trans_capex = pd.concat(
        {state: ferc_trans_capex.loc[ferc_distadmin.state2region[state]]
        for state in states if state in ferc_distadmin.state2region.keys()},
        axis=0
        )
    ferc_trans_capex.index.set_names(['state','t'], inplace=True)
    ### Add historical FERC trans_capex from pre-overlap years back in
    ferc_trans_capex = ferc_trans_capex.merge(
        dist_admin_costs_region[['trans_capex_per_mwh']], 
        left_index=True, right_index=True, how='outer')
    ### Overwrite FERC trans_capex projections with the new corrected (-ReEDS) values
    ferc_trans_capex.loc[
        ferc_trans_capex['trans_capex_per_mwh_ferconly'].notnull(),
        'trans_capex_per_mwh'
        ] = ferc_trans_capex.loc[
        ferc_trans_capex['trans_capex_per_mwh_ferconly'].notnull(),
        'trans_capex_per_mwh_ferconly'
        ]

    ################################################################################
    ### Now follow same procedure as above for distribution and administration capex
    ferc_trans_capex = load_by_state.merge(
        ferc_trans_capex.reset_index(), on=['t','state'], how='inner'
        ).drop('trans_capex_per_mwh_ferconly',axis=1)

    ferc_trans_capex['capex'] = (
        ferc_trans_capex['end_use_load'] * ferc_trans_capex['trans_capex_per_mwh'])
    ferc_trans_capex['eval_period'] = input_eval_periods['init_trans_capex']
    ferc_trans_capex['depreciation_sch'] = input_depreciation_schedules['init_trans_capex']
    ferc_trans_capex['cost_cat'] = 'cap_trans_FERC'

    df_capex = pd.concat(
        [df_capex, 
         ferc_trans_capex[
             ['state', 't', 'capex', 'eval_period', 'depreciation_sch', 'cost_cat']]], 
        sort=False).reset_index(drop=True)

    #%%######################################################################
    ### Ingest and expand generation output (duplicating for non solve years)

    gen_ivrt = pd.read_csv(
        os.path.join(run_dir, 'outputs', 'gen_ivrt.csv')
        ).rename(columns={
            'i':'i', 'v':'v', 'r':'r', 't':'t_modeled', 'Value':'gen',
            'Dim1':'i', 'Dim2':'v', 'Dim3':'r', 'Dim4':'t_modeled', 'Val':'gen'})

    gen_ivrt = duplicate_between_solve_years(gen_ivrt, modeled_years, years_reeds)

    #%% Subtract distpv gen from end use load to get retail sales
    distpv_gen = gen_ivrt[gen_ivrt['i']=='distpv'].copy()
    distpv_gen = distpv_gen.merge(ba_state_map, on='r', how='left')
    # Group distpv gen by state
    distpv_gen_grouped = distpv_gen.groupby(
        ['t', 'state'], as_index=False
        ).agg({'gen':'sum'}).rename(columns={'gen':'distpv_gen'})
    # Merge with main dataframe
    dfall = dfall.merge(
        distpv_gen_grouped, on=['t', 'state'], how='left')
    # Fill nan values with zeros
    dfall['distpv_gen'] = dfall['distpv_gen'].fillna(0.0)
    # Calculate retail load
    dfall['retail_load'] = dfall['end_use_load'] - dfall['distpv_gen']

    # Note that this is essentially assuming that all distpv gen is self-consumed, 
    #   thus, it does not contribute to retail sales. Alternatively, some
    #   could be exported, but then we'd have to estimate sell rates. If we want 
    #   to be precise about the retail sales and revenue target (as opposed to just
    #   the $/kWh result), we may want to make this more sophisticated. 

    #%%#############################
    #    -- Transmission O&M --    #
    ################################
    print('   - Transmission O&M Expenditures')
    trans_cap = pd.read_csv(
        os.path.join(run_dir, 'outputs', 'tran_out.csv')
        ).rename(columns={
            'Value':'tran_cap', 
            'Dim1':'r', 'Dim2':'rr', 'Dim3':'trtype', 'Dim4':'t', 'Val':'tran_cap'}
            ).set_index(['r','rr','trtype','t'])
    trans_cap['state1'] = trans_cap.index.get_level_values('r').map(reedsregion2state)
    trans_cap['state2'] = trans_cap.index.get_level_values('rr').map(reedsregion2state)

    trans_dist = pd.read_csv(
        os.path.join(run_dir, 'inputs_case', 'transmission_distance.csv')
    ).rename(columns={'*r':'r'}).set_index(['r','rr']).miles

    trans_cap['MWmile'] = (trans_cap['tran_cap'] * trans_dist).reindex(trans_cap.index)
    ### Check for nulls
    if any(trans_cap.MWmile.isnull().values):
        raise Exception('Missing distances: {}'.format(trans_cap.loc[trans_cap.MWmile.isnull()]))
    trans_cap.reset_index(inplace=True)

    ### Assign each line to one region. 
    ### We get two rows for each line, so we need to divide by 2 when we use trans_om later.
    trans_om = pd.concat([
        trans_cap[['r', 't', 'MWmile']], 
        trans_cap[['rr', 't', 'MWmile']].rename(columns={'rr':'r'})], 
        ignore_index=True, sort=False)

    ### Assign regions to states
    trans_om['state'] = trans_om['r'].map(reedsregion2state)

    #%%### Derive transmission O&M/MW-mile from FERC O&M/MWh, then apply to each transmission line
    ### Single national O&M/MWh and O&M/MW-mile
    if input_daproj['aggregation'] == 'nation':
        ### Align trans_opex_per_mwh (projected from FERC Form 1) 
        ### with national MW-miles and retail load by year
        trans_df = (
            dist_admin_costs.drop('state',axis=1).drop_duplicates()[['t','trans_opex_per_mwh']]
            .merge(trans_cap.groupby('t')['MWmile'].sum(), on=['t'], how='left').dropna()
            .merge(dfall.groupby('t')['retail_load'].sum(), on=['t'], how='left').dropna()
            )
        ### Get total trans OM spending by year
        trans_df['trans_om'] = trans_df['trans_opex_per_mwh'] * trans_df['retail_load']
        ### Get OM/MW-mile by year (single value for nation)
        trans_df['trans_om_per_mw_mile'] = trans_df['trans_om'] / trans_df['MWmile']
        ### Merge with trans_om, which lists transmission capacity in/out of each region by t
        trans_om = trans_om.merge(
            trans_df[['t','trans_om_per_mw_mile']], on=['t'], how='left').dropna()
        ### Get total trans OM by region from national OM/MW-mile; divide by 2 since each region 
        ### is assigned half of each line connecting it to another region and we've duplicated each line
        trans_om['op_trans'] = trans_om['MWmile'] * trans_om['trans_om_per_mw_mile'] / 2
        ### Sum by state and year, then interpolate
        trans_om_state = trans_om.groupby(['t','state'], as_index=False)['op_trans'].sum()
        trans_om_state = interp_between_solve_years(
            trans_om_state, 'op_trans', modeled_years, non_modeled_years, 
            first_year, last_year, state_list, 'state'
            )
        ### Store it
        dfall = dfall.merge(
            trans_om_state[['t', 'state', 'op_trans']], on=['t', 'state'], how='left')
        dfall['op_trans'] = dfall['op_trans'].fillna(0.0)

    ### State-specific O&M/MWh and O&M/MW-mile
    else:
        ### Just take the transmission opex straight from FERC. Note that for 'best' (and for NE either
        ### way), the states that use national values will give different results from the case
        ### where aggregation=='nation'. In this case we use the national transmission O&M directly,
        ### while when aggregation=='nation' we get a national OM/MW-mile and apply that to each state.
        dfall = dfall.merge(
            (dist_admin_costs.set_index(['state','t'])['trans_opex_per_mwh'] 
                * dfall.set_index(['state','t'])['retail_load']).rename('op_trans'),
            left_on=['state','t'], right_index=True, how='left',
            )

        ### Align trans_opex_per_mwh (projected from FERC Form 1) with state MW-miles
        ### and retail load by year
        # trans_df = (
        #     dist_admin_costs[['t','state','trans_opex_per_mwh']]
        #     ### Here we use trans_om since it already has state info 
        #     ### (divide by 2 since lines are duplicated)
        #     .merge(trans_om.groupby(['t','state'])['MWmile'].sum()/2, 
        #            on=['t','state'], how='left').dropna()
        #     .merge(dfall.groupby(['t','state'])['retail_load'].sum(), 
        #            on=['t','state'], how='left').dropna()
        # )
        # ### Get total trans OM spending by year and state
        # trans_df['trans_om'] = trans_df['trans_opex_per_mwh'] * trans_df['retail_load']
        # ### Get OM/MW-mile by year and state
        # trans_df['trans_om_per_mw_mile'] = trans_df['trans_om'] / trans_df['MWmile']
        # ### Merge with trans_om, which lists transmission capacity in/out of each region by t
        # trans_om = trans_om.merge(
        #     trans_df[['t','state','trans_om_per_mw_mile']], 
        #     on=['t','state'], how='left').dropna()

    # ### Get total trans OM by region from national OM/MW-mile; divide by 2 since each region 
    ### is assigned half of each line connecting it to another region and we've duplicated each line
    # trans_om['op_trans'] = trans_om['MWmile'] * trans_om['trans_om_per_mw_mile'] / 2
    # ### Sum by state and year, then interpolate
    # trans_om_state = trans_om.groupby(['t','state'], as_index=False)['op_trans'].sum()
    # trans_om_state = interp_between_solve_years(
    #     trans_om_state, 'op_trans', modeled_years, non_modeled_years, 
    #     first_year, last_year, state_list, 'state')
    ### Store it
    # dfall = dfall.merge(trans_om_state[['t', 'state', 'op_trans']], on=['t', 'state'], how='left')
    # dfall['op_trans'] = dfall['op_trans'].fillna(0.0)

    #%%#####################################################################################
    #    -- Calculate generation plant depreciation expenses and return on rate base --    #
    ########################################################################################

    # Expand df_cap into df_capital_costs, which has a row for each year that capacity exists
    # A plant's age is year-beginning 
    unique_evals = df_capex['eval_period'].drop_duplicates()
    max_eval = np.max([unique_evals.max(), 100])
    plant_ages = pd.DataFrame(
        list(itertools.product(unique_evals, np.arange(0,max_eval,1))), 
        columns=['eval_period', 'plant_age'])
    plant_ages = plant_ages[plant_ages['plant_age']<plant_ages['eval_period']]
    ### Assume straight line depreciation for expense accounting for all plants
    plant_ages['accounting_dep_f'] = 1.0 / plant_ages['eval_period']
    plant_ages['accounting_dep_f_cum'] = (plant_ages['plant_age']+1)/(plant_ages['eval_period'])

    # df_capital_costs is the costs associated with cost recovery for capital investments
    #   (depreciation, return to capital, taxes)
    df_capital_costs = df_capex.merge(
        plant_ages, on='eval_period', how='left').rename(columns={'t':'t_online'})
    df_capital_costs['t'] = df_capital_costs['t_online'] + df_capital_costs['plant_age']

    ###############################################################################
    # dep_inflation_adj adjusts the real value of depreciation expenses over the 
    # lifetime of the plant to reflect the impacts of inflation on the rate base 
    # (which is in nominal terms)
    df_dep_years = df_capital_costs[['t','t_online']]
    df_dep_years = df_dep_years.drop_duplicates(['t','t_online']).reset_index(drop=True)
    for i in range(len(df_dep_years)) :
        year = df_dep_years.loc[i, "t"]
        base_year = df_dep_years.loc[i, "t_online"]
        if year == base_year:
            df_dep_years.loc[i, 'dep_inflation_adj'] = 1
        else:
            df_dep_years.loc[i, 'dep_inflation_adj'] = (
                1.0 / np.array(np.cumprod(inflation.loc[base_year + 1:year]))[-1])

    df_capital_costs = df_capital_costs.merge(
        df_dep_years, on=['t','t_online'], how='left' )

    # Merge on annual depreciation fraction onto the df_capital_costs
    depreciation_schedules = pd.read_csv(
        os.path.join(run_dir, 'inputs_case', 'depreciation_schedules.csv')
        ).drop(columns='Schedule')
    for age in np.arange(len(depreciation_schedules),100):
        # Extend schedules out to 100 years, to make sure we cover all plant ages
        depreciation_schedules.loc[age, :] = 0.0
    depreciation_schedules['plant_age'] = np.arange(0, 100)
    depreciation_schedules_cum = depreciation_schedules.copy()
    depreciation_schedules = depreciation_schedules.melt(
        id_vars='plant_age', var_name='depreciation_sch', value_name='tax_dep_f')
    depreciation_schedules['depreciation_sch'] = depreciation_schedules['depreciation_sch'].astype(str)
    df_capital_costs['depreciation_sch'] = df_capital_costs['depreciation_sch'].astype(str)
    df_capital_costs = df_capital_costs.merge(
        depreciation_schedules, on=['depreciation_sch', 'plant_age'], how='left')

    # Merge on the cumulative tax depreciation fraction, 
    # for calculating ADIT from accelerated depreciation
    schedules = list(depreciation_schedules_cum.columns)
    schedules.remove('plant_age')
    depreciation_schedules_cum[schedules] = depreciation_schedules_cum[schedules].cumsum()
    depreciation_schedules_cum = depreciation_schedules_cum.melt(
        id_vars='plant_age', var_name='depreciation_sch', value_name='tax_dep_f_cum')
    df_capital_costs = df_capital_costs.merge(
        depreciation_schedules_cum, on=['depreciation_sch', 'plant_age'], how='left')

    df_capital_costs = df_capital_costs.merge(df_finance, on='t', how='left')

    df_capital_costs['capex_inf_adj'] = (
        df_capital_costs['capex'] * df_capital_costs['dep_inflation_adj'])
    df_capital_costs['dep_expense'] = (
        df_capital_costs['accounting_dep_f'] * df_capital_costs['capex_inf_adj'])
    df_capital_costs['dep_tax_value'] = (
        df_capital_costs['tax_dep_f'] * df_capital_costs['capex_inf_adj'])
    # Accumulated deferred income taxes
    df_capital_costs['adit'] = np.clip(
        (df_capital_costs['tax_dep_f_cum'] - df_capital_costs['accounting_dep_f_cum']) 
        * df_capital_costs['capex_inf_adj'] * df_capital_costs['tax_rate'], 0.0, None)
    df_capital_costs['net_plant_in_service'] = (
        df_capital_costs['capex_inf_adj'] 
        - df_capital_costs['accounting_dep_f_cum'] * df_capital_costs['capex_inf_adj'])
    df_capital_costs['plant_rate_base'] = (
        df_capital_costs['net_plant_in_service'] - df_capital_costs['adit'])
    df_capital_costs['debt_interest'] = (
        df_capital_costs['plant_rate_base'] 
        * df_capital_costs['debt_fraction'] 
        * df_capital_costs['debt_interest_nominal'])
    df_capital_costs['equity_return'] = (
        df_capital_costs['plant_rate_base'] 
        * (1.0 - df_capital_costs['debt_fraction']) 
        * df_capital_costs['equity_return_nominal'])
    df_capital_costs['return_to_capital'] = (
        df_capital_costs['debt_interest'] + df_capital_costs['equity_return'])
    df_capital_costs['income_tax'] = (
        (df_capital_costs['equity_return'] + df_capital_costs['dep_expense'] - 
         df_capital_costs['dep_tax_value']) * (1.0 / (1.0 - df_capital_costs['tax_rate']) - 1.0)) 

    df_nulls = df_capital_costs[(df_capital_costs['debt_interest'].isnull()) |
                                (df_capital_costs['equity_return'].isnull()) |
                                (df_capital_costs['dep_expense'].isnull()) |
                                (df_capital_costs['income_tax'].isnull())]

    if verbose > 1:
        print('number of caps with null values:', len(df_nulls))

    df_capital_costs_by_state = df_capital_costs.groupby(
        by=['t', 'state', 'cost_cat'], as_index=False)[
            ['dep_expense', 'debt_interest', 'equity_return', 'income_tax']].sum()
        
    cap_cost_cats = list(df_capital_costs_by_state['cost_cat'].drop_duplicates())

    for cap_cost_cat in cap_cost_cats:
        df_cap_single = df_capital_costs_by_state[
            df_capital_costs_by_state['cost_cat']==cap_cost_cat]
        
        df_cap_single = df_cap_single[
            ['t', 'state', 'dep_expense', 'debt_interest', 'equity_return', 'income_tax']]

        dfall = dfall.merge(
            df_cap_single.rename(columns={
                'dep_expense':'%s_dep_expense' % cap_cost_cat,
                'debt_interest':'%s_debt_interest' % cap_cost_cat,
                'equity_return':'%s_equity_return' % cap_cost_cat,
                'income_tax':'%s_income_tax' % cap_cost_cat,}), 
            on=['t', 'state'], how='left')
        
        dfall['%s_dep_expense' % cap_cost_cat] = dfall['%s_dep_expense' % cap_cost_cat].fillna(0.0)    
        dfall['%s_debt_interest' % cap_cost_cat] = dfall['%s_debt_interest' % cap_cost_cat].fillna(0.0)    
        dfall['%s_equity_return' % cap_cost_cat] = dfall['%s_equity_return' % cap_cost_cat].fillna(0.0)    
        dfall['%s_income_tax' % cap_cost_cat] = dfall['%s_income_tax' % cap_cost_cat].fillna(0.0)    

    #%%########################################################################
    ### PTC Value Calculations
    print('   - PTC Values')
    '''
    ptc_values contains the $/MWh value of the credit (in $2004) and the duration of the 
        ptc, specified by [i,v,r,t]. We multiply that credit value by the observed
        generation from generators that were built in that window. 
    '''
    
    ptc_values = pd.read_csv(
        os.path.join(run_dir, 'inputs_case', 'ptc_values.csv'))
    ### Reduce the PTC value by the monetization cost penalty.
    if 'ptc_tax_equity_penalty' in ptc_values:
        ptc_values['ptc_value'] *= (1 - ptc_values['ptc_tax_equity_penalty'])
        ptc_values['ptc_grossup_value'] *= (1 - ptc_values['ptc_tax_equity_penalty'])
        
    # Read in tax credit phaseout adjustment
    gdx_filename = os.path.join(
        run_dir, 'outputs', 'tc_phaseout_data', 'tc_phaseout_mult_%s.gdx' % last_year)
    tc_phaseout_mult = gdxpds.to_dataframes(gdx_filename)['tc_phaseout_mult_t']
    # if '*' in emit_nat.columns: emit_nat.rename(columns={'*':'t'}, inplace=True)
    tc_phaseout_mult['t'] = tc_phaseout_mult['t'].astype(int)
    tc_phaseout_mult = tc_phaseout_mult.set_index('t').rename(columns={'Value':'tc_phaseout_mult'})
    tc_phaseout_mult['tc_phaseout_mult'] = tc_phaseout_mult['tc_phaseout_mult'].astype(float)
    tc_phaseout_mult.reset_index(drop=False, inplace=True)
    ptc_values = ptc_values.merge(tc_phaseout_mult, on=['i', 't'], how='left')
    ptc_values['tc_phaseout_mult'] = ptc_values['tc_phaseout_mult'].fillna(1.0)
    ptc_values['ptc_value'] = ptc_values['ptc_value'] * ptc_values['tc_phaseout_mult']
    ptc_values['ptc_grossup_value'] = ptc_values['ptc_grossup_value'] * ptc_values['tc_phaseout_mult']

    # There is also a row for each year that a [i,v] combo was able to be built, 
    #   but we can't apply each value to the full [i,v] generation each year. 
    #   Very crudely just dividing each row's value by total number of rows. 
    #   Implicitly assumes capacity is evenly built over the year range, and 
    #   also doesn't capture ramp-up properly. Absolutely should be fixed if 
    #   any serious work with PTC on retail rates is done. 
    
    ptc_values_count = (
        ptc_values[['i','v','ptc_value']]
        .groupby(['i', 'v'], as_index=False).count())
    ptc_values = ptc_values.merge(
        ptc_values_count.rename(columns={'ptc_value':'count'}), on=['i', 'v'], how='left')
    ptc_values['ptc_value'] = ptc_values['ptc_value'] / ptc_values['count']
    ptc_values['ptc_grossup_value'] = ptc_values['ptc_grossup_value'] / ptc_values['count']

    # Expand the ptc_values dfall over the duration of the ptc
    ptc_values = ptc_values.rename(columns={'t':'t_start'})
    unique_durs = ptc_values['ptc_dur'].drop_duplicates()
    max_dur = ptc_values['ptc_dur'].max()
    ptc_dur_expander = pd.DataFrame(
        list(itertools.product(unique_durs, np.arange(0,max_dur,1))), 
        columns=['ptc_dur', 'ptc_year'])
    ptc_dur_expander = ptc_dur_expander[ptc_dur_expander['ptc_year']<ptc_dur_expander['ptc_dur']]

    # Expand to cover all years, not just the initial available year
    ptc_values = ptc_values.merge(
        ptc_dur_expander[['ptc_dur', 'ptc_year']], on='ptc_dur', how='left')
    ptc_values['t'] = ptc_values['t_start'] + ptc_values['ptc_year']

    # Merge on the observed generation
    ptc_values = ptc_values.merge(gen_ivrt, on=['i', 'v', 't'], how='left')

    # Rows with nan's meant that there was a ptc available, but no [i,v] generation was there
    ptc_values = ptc_values[~ptc_values['gen'].isnull()]

    # Calculate the value of the credits ($), and the effective after-tax value for a 
    # regulated utility
    ptc_values['ptc_credits'] = ptc_values['ptc_value'] * ptc_values['gen']
    ptc_values['ptc_grossup'] = ptc_values['ptc_grossup_value'] * ptc_values['gen']

    # Group by state and year. 
    ptc_values = ptc_values.merge(ba_state_map, on='r', how='left')
    ptc_values_grouped = ptc_values.groupby(
        ['t', 'state'], as_index=False)[['ptc_credits', 'ptc_grossup']].sum()
    # At this point ptc_grossup is just the grossup portion, so add the base credit to it
    ptc_values_grouped['ptc_grossup'] += ptc_values_grouped['ptc_credits']

    dfall = dfall.merge(
        ptc_values_grouped[['t', 'state', 'ptc_grossup']], on=['t', 'state'], how='left')
    dfall['ptc_grossup'] = dfall['ptc_grossup'].fillna(0.0)
    # In the dfall, make it negative because it is a value instead of a cost
    dfall['ptc_grossup'] = -dfall['ptc_grossup']

    #%%########################################################################
    ### ITC Value Calculations
    print('   - ITC Values')
    '''
    We spread the value of the ITC over the lifetime of the asset. In practice there is a 
    normalization process that achieves this through ADIT, but we are simplifying it in
    this way for now. 
    '''
    
    ###### First calculate for transmission
    ### Load the ITC fraction
    trans_itc = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'trans_itc_fractions.csv'))
    ### Multiply ITC fraction by transmission spending
    ##! NOTE: We're only applying the transmission ITC to inter-regional transmission line
    ##! investment, because that's what is done in ReEDS. There's also 
    ##! converters, and FERC intra-regional transmission. Decide whether transmission ITC
    ##! should apply to those as well.
    if not len(trans_itc):
        trans_itc_value = pd.DataFrame(columns=['t','state','itc_trans'])
    else:
        trans_itc_value = (
            nongen_capex.loc[nongen_capex.i.isin([
                'inv_transmission_interzone_ac_investment',
                'inv_transmission_interzone_dc_investment',
            ])]
            [['t','state','eval_period','capex']]
            .merge(trans_itc, on='t', how='left')
            .rename(columns={'t':'t_online'})
            )
        trans_itc_value['tax_rate'] = trans_itc_value.t_online.map(df_finance.tax_rate)
        trans_itc_value['itc_base_value'] = (
            trans_itc_value['capex'] * trans_itc_value['itc_frac_monetized'])
        trans_itc_value.dropna(subset=['itc_frac'], inplace=True)
        ### Spread the ITC value over the lifetime of the asset
        ## Get the series of years (length = eval_period) over which the ITC is paid out
        itc_years = range(int(trans_itc_value.eval_period.unique()))
        ## Broadcast other values for each payout year
        trans_itc_value = (
            pd.concat({t: trans_itc_value for t in itc_years}, axis=0, names=['itc_year','drop'])
            .reset_index(level=0).reset_index(drop=True)
            )
        ## Get series of payout years
        trans_itc_value['t'] = trans_itc_value['t_online'] + trans_itc_value['itc_year']
        ## ITC is nominal for year of construction, so depreciate later years
        depreciation_lookup = (
            df_dep_years.dropna(subset=['t']).astype({'t':int})
            .set_index(['t','t_online']).dep_inflation_adj)
        trans_itc_value['dep_inflation_adj'] = trans_itc_value.apply(
            lambda row: depreciation_lookup[row.t, row.t_online], axis=1)
        ### Calculate the normalized, after-tax, inflation-adjusted annual value of the ITC 
        ### for each year of an asset's life (negative because it's a benefit)
        trans_itc_value['itc_trans'] = - (
            trans_itc_value['itc_base_value'] / (1.0 - trans_itc_value['tax_rate']) 
            / trans_itc_value['eval_period'] * trans_itc_value['dep_inflation_adj']
            )

    ###### Do it again for generation assets
    itc_df = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'itc_fractions.csv'))
    ### Reduce the ITC value by the tax equity penalty.
    ### Technically it would be more appropriate to treat the increased equity cost explicitly,
    ### but the final result is the same.
    if 'itc_tax_equity_penalty' in itc_df:
        itc_df['itc_frac'] *= (1 - itc_df['itc_tax_equity_penalty'])

    # Merge itc_fraction, country, and tax rate onto the dataframe of generator capex
    stacked_country_map = regions_map[
        ['r', 'country']].drop_duplicates().rename(columns={'r':'region'})
    stacked_country_map = pd.concat(
        [stacked_country_map, 
        regions_map[['r', 'country']].drop_duplicates().rename(columns={'r':'region'})], 
        ignore_index=True, sort=False)
    stacked_country_map['country'] = stacked_country_map['country'].str.lower()
    itc_value_df = df_gen_capex[['i', 'region', 't', 'capex', 'eval_period', 'state']].copy()
    itc_value_df = itc_value_df.merge(
        stacked_country_map[['region', 'country']], on='region', how='left')
    itc_value_df = itc_value_df.merge(
        itc_df[['i', 'country', 't', 'itc_frac']], on=['i', 'country', 't'], how='inner')
    itc_value_df = itc_value_df.merge(
        df_finance[['tax_rate']], on='t', how='left')

    # Calculate the value of the ITC credit in the year each asset is built. 
    # This is not the value we use, because we need to normalize and adjust for taxes
    itc_value_df['itc_base_value'] = itc_value_df['capex'] * itc_value_df['itc_frac']

    # Spread the ITC value over the lifetime of the asset 
    # (i.e. approximate the normalization of the value)
    itc_value_distributed = itc_value_df.rename(columns={'t':'t_online'})
    unique_durs = itc_value_distributed['eval_period'].drop_duplicates()
    max_dur = itc_value_distributed['eval_period'].max()
    itc_expander = pd.DataFrame(
        list(itertools.product(unique_durs, np.arange(0,max_dur,1))), 
        columns=['eval_period', 'itc_year'])
    itc_expander = itc_expander[itc_expander['itc_year']<itc_expander['eval_period']]
    itc_value_distributed = itc_value_distributed.merge(
        itc_expander[['eval_period', 'itc_year']], on='eval_period', how='left')
    itc_value_distributed['t'] = itc_value_distributed[['t_online','itc_year']].sum(axis=1)

    # Decrease the ongoing values of the credit, 
    # since they were in nominal terms for the year of construction
    itc_value_distributed = itc_value_distributed.merge(
        df_dep_years[['t', 't_online', 'dep_inflation_adj']], on=['t', 't_online'], how='left')

    # Calculate the normalized, after-tax, inflation-adjusted annual value of the ITC 
    # for each year of an asset's life. Negative because it's a credit not a cost
    itc_value_distributed['itc_normalized_value'] = - (
        itc_value_distributed['itc_base_value'] / (1.0 - itc_value_distributed['tax_rate']) 
        / itc_value_distributed['eval_period'] * itc_value_distributed['dep_inflation_adj'])

    # Group by [t, state]
    itc_value_grouped = itc_value_distributed.groupby(
        ['t', 'state']).sum()['itc_normalized_value']

    # Merge onto main dfall
    dfall = (
        dfall
        .merge(
            itc_value_grouped, left_on=['t', 'state'], right_index=True, how='left')
        .merge(
            trans_itc_value.groupby(
                ['t','state'], as_index=False
                )['itc_trans'].sum().reindex(['t','state','itc_trans'], axis=1), 
            on=['t', 'state'], how='left')
        .fillna({'itc_normalized_value':0, 'itc_trans':0})
        )
    
    #%%### Save results
    if write:
        outpath = os.path.join(run_dir, 'outputs', 'retail')
        os.makedirs(outpath, exist_ok=True)
        dfall.to_csv(os.path.join(outpath, 'retail_rate_components.csv'))
        if verbose > 0:
            print(os.path.join(outpath, 'retail_rate_components.csv'))
#%%
    return dfall


#%% ===========================================================================
### --- PLOTS ---
### ===========================================================================

def get_dfplot(run_dir, inputpath, plot_dollar_year, tableau_export=False):
    """
    Get the retail outputs as a dataframe, apply bias-correction factor,
    and group some similar columns
    """
    ### Get module directory for relative paths
    mdir = os.path.dirname(os.path.abspath(__file__))
    
    #%% Get the bias correction factor
    dferror = pd.read_csv(
        os.path.join(mdir, 'inputs','state-meanbiaserror_rate-aggregation.csv'),
        index_col='index')
    dferror['best'] = dferror.apply(lambda row: row[row['aggregation']], axis=1)
    ### Convert from bias error to correction factor
    dferror[['nation','state','region','best']] = (
        -dferror[['nation','state','region','best']].copy())

    ### Get the input settings
    inputs = pd.read_csv(inputpath, index_col=('input_dict','input_key')).squeeze(1)
    data_dollar_year = int(inputs['inputs','dollar_year'])

    ### Get the inflation adjustment
    inflatable = ferc_distadmin.get_inflatable(
        os.path.join(run_dir, 'inputs_case', 'inflation.csv'))
    inf_adjust = inflatable[data_dollar_year,plot_dollar_year]

    ### Load the pre-calculated outputs
    dfin = pd.read_csv(
        os.path.join(run_dir,'outputs','retail','retail_rate_components.csv'), 
        index_col=0)
    ### Apply state bias correction
    dfin['bias_correction'] = (
        dfin.state.map(dferror[inputs['input_daproj','aggregation']]) 
        * dfin['retail_load'] * 10 / inf_adjust
        )

    if tableau_export:
        dfplot = dfin.groupby(['state','t']).sum()
    else:
        ### Group by year and drop extra columns
        sumcols = dfin.columns.difference(
            ['state', 't', 'busbar_load', 'end_use_load', 'distpv_gen'])
        dfplot = dfin.groupby('t')[sumcols].sum()

    ### Post-processing
    dfplot = post_processing(dfplot)
    
    ### Convert to ¢/kWh
    exclude_cols = ['state', 'retail_load', 'busbar_load', 'end_use_load', 'distpv_gen']
    for col in [c for c in dfplot.columns if c not in exclude_cols]:
        dfplot[col] = dfplot[col] / dfplot['retail_load'] * inf_adjust / 10
    if not tableau_export:
        dfplot.drop('retail_load', axis=1, inplace=True)
    
    return dfplot


def post_processing(dfplot):
    ### Group special into op_admin
    if 'special_costs' in dfplot:
        dfplot['op_admin'] += dfplot['special_costs']
        dfplot.drop('special_costs', axis=1, inplace=True)
    ### Group 'op_h2combustion_fuel_costs' into 'op_fuelcosts_objfn'
    if 'op_h2combustion_fuel_costs' in dfplot.columns:
        dfplot['op_fuelcosts_objfn'] += dfplot['op_h2combustion_fuel_costs']
        dfplot.drop('op_h2combustion_fuel_costs', axis=1, inplace=True)
    subcols = [
        'cap_{}_dep_expense', 'cap_{}_debt_interest',
        'cap_{}_equity_return', 'cap_{}_income_tax']

    for subcol in subcols:
        ### Put AC/DC converters into transmission
        if subcol.format('converter') in dfplot:
            dfplot[subcol.format('transmission')] += dfplot[subcol.format('converter')]
            dfplot.drop(subcol.format('converter'), axis=1, inplace=True)
    
    return dfplot

def retail_plots(run_dir, inputpath='inputs.csv', startyear=2010,
                 plot_dollar_year=2022):
    
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    ### Local imports
    plots.plotparams()
    ### Get module directory for relative paths
    mdir = os.path.dirname(os.path.abspath(__file__))
    print('Creating Plots:')

    #%%######################################################
    #    -- Plot #1a: Full retail rate disaggregation --    #
    #########################################################

    print(' - Plot 1a: Full retail rate disaggregation')

    ### Load the pre-calculated outputs
    dfplot = get_dfplot(run_dir=run_dir, inputpath=inputpath, plot_dollar_year=plot_dollar_year)
    endyear = dfplot.index.max()

    ### Get all value columns
    plotcols = sorted([c for c in dfplot.columns if c != 'retail_load'])
    taxcredits = ['ptc_grossup', 'itc_normalized_value', 'ptc_h2', 'itc_trans']

    ### Colors
    costcategories = [
        '_gen_', '_admin', '_dist', '_fuel', '_fom', '_flow', 
        '_spurline', '_trans_FERC', '_transmission', 'op_', 'bias_correction',
        ]
    print(
        "The only entries in the following list should be related to the PTC and ITC."
        "\nIf there are additional entries, add them to "
        "\npostprocessing/retail_rate_module/retail_rate_calculations.retail_plots().")
    print([c for c in plotcols if not (any([i in c for i in costcategories]))])

    ### Get column categories, colors, and alphas
    costcols = {costcat: [] for costcat in costcategories}
    for col in plotcols:
        for costcat in costcategories:
            if costcat in col:
                costcols[costcat].append(col)
                break
      
    ### Move op_trans from op to transmission
    costcols['_transmission'] += ['op_trans']
    costcols['op_'] = [c for c in costcols['op_'] if c != 'op_trans']
                
    catcolors = {costcat: plt.cm.tab10(i) 
                 if (not costcat.startswith('bias')) else plt.cm.binary_r(0)
                 for i,costcat in enumerate(costcategories)}
    alphas = {}
    for costcat in costcategories:
        numcols = len(costcols[costcat])
        for i, col in enumerate(costcols[costcat]):
            alphas[col] = (i + 1) / numcols

    colors = {}
    for costcat in costcategories:
        for col in costcols[costcat]:
            colors[col] = (*catcolors[costcat][:3],alphas[col])

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(7.5,6))
    for t in range(startyear,endyear+1):
        start = dfplot.loc[t].reindex(taxcredits).fillna(0).sum()
        height = dfplot.loc[t,list(colors)][::-1]
        bottom = height.cumsum() + start
        ax.bar(
            x=[t]*len(bottom), bottom=bottom.values, height=-height.values, 
            width=1, color=bottom.index.map(colors).values,
            )
    ax.axhline(0,c='k',lw=0.75,ls='--')
    ax.set_xlim(startyear-0.5, endyear+0.5)
    ax.set_xlabel('Year')
    ax.set_ylabel('Retail rate [{}¢/kWh]'.format(plot_dollar_year))
    ax.set_ylim(
        dfplot.reindex(taxcredits, axis=1).fillna(0).sum(axis=1).min()*1.5,
        max(ax.get_ylim()[1],12)
        )
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ### Legend
    handles = [
        mpl.patches.Patch(facecolor=colors[col], edgecolor='none', label=tracelabels[col])
        for col in list(colors)
        ]
    ax.legend(
        handles=handles, loc='upper left', bbox_to_anchor=(1.05,1.05),
        ncol=3, handletextpad=0.3, handlelength=0.7, fontsize='large',
        frameon=False
    )
    plots.despine(ax)
    savename = os.path.join(run_dir,'outputs','retail','retail_rate_USA_components_all.png')
    plt.savefig(savename)
    plt.close()

    ###########################################################
    #    -- Plot #1b: Aggregate rates by financial type --    #
    ###########################################################
    
    print(' - Plot 1b: Aggregate rates by financial type')
    
    alpha = 0.7
    costcategories = [
        'bias_correction',
        'equity_return',
        'debt_interest',
        'dep_expense',
        'income_tax',
        'op_',
        'flow',
        ][::-1]
    titles = {
        'bias_correction': 'State bias correction',
        'income_tax': 'Income tax',
        'equity_return': 'Equity return',
        'debt_interest': 'Debt interest',
        'dep_expense': 'Depreciation',
        'op_': 'Operations',
        'flow': 'Inter-state flows',
        }

    ### Get column categories, colors, and alphas
    costcols = {costcat: [] for costcat in costcategories}
    for col in plotcols:
        for costcat in costcategories:
            if costcat in col:
                costcols[costcat].append(col)
                break

    catcolors = {costcat: plt.cm.Dark2(i) 
                if (not costcat.startswith('bias')) else plt.cm.binary_r(0)
                for i,costcat in enumerate(costcategories)}

    colors = {}
    for costcat in costcategories:
        for col in costcols[costcat]:
            colors[col] = (catcolors[costcat])
    colors['bias_correction'] = 'k'

    ### Plot it
    plt.close()
    f,ax=plt.subplots(figsize=(5,4))
    for t in range(2010,dfplot.index.max()+1):
        start = dfplot.loc[t].reindex(taxcredits).fillna(0).sum()
        height = dfplot.loc[t,list(colors)][::-1]
        bottom = height.cumsum() + start
        ax.bar(
            x=[t]*len(bottom), bottom=bottom.values, height=-height.values, 
            width=1, color=bottom.index.map(colors).values, alpha=alpha, 
            )
    ax.axhline(0,c='k',lw=0.75,ls='--')
    ax.set_xlim(startyear-0.5, dfplot.index.max()+0.5)
    ax.set_xlabel('Year')
    ax.set_ylabel('Retail rate [{}¢/kWh]'.format(plot_dollar_year))
    ax.set_ylim(
        dfplot.reindex(taxcredits, axis=1).fillna(0).sum(axis=1).min()*1.5,
        max(ax.get_ylim()[1],12)
        )
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ### Legend
    handles = [
        mpl.patches.Patch(
            facecolor=catcolors[costcat], edgecolor='none', alpha=alpha, label=titles[costcat])
        for costcat in costcategories
        ]
    ax.legend(
        handles=handles, loc='upper left', bbox_to_anchor=(1,1),
        ncol=1, handletextpad=0.3, handlelength=0.7, fontsize='large',
        frameon=False
    )
    plots.despine(ax)
    savename = os.path.join(run_dir,'outputs','retail','retail_rate_USA_components_financial.png')
    plt.savefig(savename)
    plt.close()

    ###########################################################
    #    -- Plot #1c: Aggregate rates by model category --    #
    ###########################################################
    
    print(' - Plot 1c: Aggregate rates by model category')
    
    fuel_list = ['op_fuelcosts_objfn']
    if 'op_co2_transport_storage' in dfplot.columns:
        fuel_list.append('op_co2_transport_storage')
    
    costcols = {
        '_gen_': [
            'cap_gen_debt_interest', 
            'cap_gen_dep_expense', 
            'cap_gen_equity_return', 
            'cap_gen_income_tax'],
        '_admin': [
            'cap_admin_debt_interest',
            'cap_admin_dep_expense',
            'cap_admin_equity_return',
            'cap_admin_income_tax',
            'op_admin'],
        '_dist': [
            'cap_dist_debt_interest',
            'cap_dist_dep_expense',
            'cap_dist_equity_return',
            'cap_dist_income_tax',
            'op_dist'],
        '_fuel': fuel_list,
        '_fom': [
            'cap_fom_debt_interest',
            'cap_fom_dep_expense',
            'cap_fom_equity_return',
            'cap_fom_income_tax',
            'op_fom_costs',
            'op_operating_reserve_costs',
            'op_vom_costs'],
        '_spurline': [
            'cap_spurline_debt_interest',
            'cap_spurline_dep_expense',
            'cap_spurline_equity_return',
            'cap_spurline_income_tax'
            'op_spurline_fom'],
        '_flow': ['load_flow', 'oper_res_flow', 'res_marg_ann_flow', 'rps_flow'],
        '_trans_FERC': [
            'op_trans',
            'cap_trans_FERC_debt_interest',
            'cap_trans_FERC_dep_expense',
            'cap_trans_FERC_equity_return',
            'cap_trans_FERC_income_tax'],
        '_transmission': [
            'cap_transmission_debt_interest',
            'cap_transmission_dep_expense',
            'cap_transmission_equity_return',
            'cap_transmission_income_tax'],
        'op_': [
            'op_wc_debt_interest',
            'op_wc_equity_return',
            'op_wc_income_tax']
        }
    costcategories_ordered = [
        '_flow',
        'op_',
        '_admin',
        '_dist',
        '_trans_FERC',
        '_spurline',
        '_transmission',
        '_fom',
        '_fuel',
        '_gen_'
        ]
    titles = {
        '_gen_': 'Generation capacity',
        '_fuel': 'Fuel',
        '_admin': 'Administration',
        '_dist': 'Distribution',
        '_fom': 'Generation O&M,\noperating reserves',
        '_spurline': 'Spur lines',
        '_trans_FERC': 'Transmission:\nintra-region + O&M',
        '_transmission': 'Transmission: inter-region\n+ wind/solar spur lines',
        '_flow': 'Inter-state flows,\nworking capital',
        'op_': '_nolabel_',
        }
    catcolors = {
        '_flow': plt.cm.RdYlBu(0.625),
        'op_': plt.cm.RdYlBu(0.625),
        '_admin': plt.cm.RdYlBu(0.75),
        '_dist': plt.cm.RdYlBu(0.875),
        '_trans_FERC': plt.cm.RdYlBu(1.),
        '_spurline': plt.cm.RdYlBu(0.375),
        '_transmission': plt.cm.RdYlBu(0.375),
        '_fom': plt.cm.RdYlBu(0.25),
        '_fuel': plt.cm.RdYlBu(0.125),
        '_gen_': plt.cm.RdYlBu(0.),
        }
    ratecolors = {'bias_correction':(0.,0.,0.,1.)}
    for costcat in costcategories_ordered:
        for col in costcols[costcat]:
            ratecolors[col] = (catcolors[costcat])

    ### Plot it
    plt.close()
    f,ax=plt.subplots(figsize=(5,4))
    cols = [c for c in ratecolors if c in dfplot.columns]
    for t in range(2010,dfplot.index.max()+1):
        start = dfplot.loc[t].reindex(taxcredits).fillna(0).sum()
        height = dfplot.loc[t,cols][::-1]
        bottom = height.cumsum() + start
        ax.bar(
            x=[t]*len(bottom), bottom=bottom.values, height=-height.values, 
            width=1, color=bottom.index.map(ratecolors).values,
            )
    ax.axhline(0,c='k',lw=0.75,ls='--')
    ax.set_xlim(startyear-0.5, dfplot.index.max()+0.5)
    ax.set_xlabel('Year')
    ax.set_ylabel('Retail rate [{}¢/kWh]'.format(plot_dollar_year))
    ax.set_ylim(
        dfplot.reindex(taxcredits, axis=1).fillna(0).sum(axis=1).min()*1.5,
        max(ax.get_ylim()[1],12)
        )
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ### Legend
    handles = (
        [mpl.patches.Patch(facecolor=ratecolors['bias_correction'], edgecolor='none', label='Bias correction')]
        + [
            mpl.patches.Patch(facecolor=catcolors[costcat], edgecolor='none', label=titles[costcat])
            for costcat in costcategories_ordered
            if costcat not in ['_spurline', 'op_']
            ]
        )
    ax.legend(
        handles=handles, loc='upper left', bbox_to_anchor=(1,1),
        ncol=1, handletextpad=0.3, handlelength=0.7, fontsize='large',
        frameon=False
    )
    plots.despine(ax)
    savename = os.path.join(run_dir,'outputs','retail','retail_rate_USA_components_model.png')
    plt.savefig(savename)
    plt.close()

    #%%#############################################
    #    -- Plot #2: Compare to EIA861 rates --    #
    ################################################
    
    print(' - Plot 2: EIA861 Historic vs ReEDS rates')
    
    ### Get the historical EIA861 rates
    dfeia = pd.read_excel(
        os.path.join(mdir,'inputs','Table_9.8_Average_Retail_Prices_of_Electricity.xlsx'),
        engine='openpyxl', sheet_name='Annual Data',
        skiprows=list(range(10))+[11], index_col=0, na_values=['Not Available'],
        )
    inflatable = ferc_distadmin.get_inflatable(
        os.path.join(run_dir, 'inputs_case', 'inflation.csv'))
    dfeia['inflator'] = dfeia.index.map(lambda x: inflatable[x,plot_dollar_year])
    dfeia['RetailTotal_real'] = (
        dfeia['Average Retail Price of Electricity, Total'] * dfeia.inflator)
    ### Write the rates to facilitate plot recreation
    pd.concat([
        (dfeia.RetailTotal_real.rename('retailrate')
         .rename_axis('t').to_frame().assign(source='EIA861')),
        (dfplot.loc[startyear:].sum(axis=1,numeric_only=True).rename('retailrate')
         .rename_axis('t').to_frame().assign(source='ReEDS')),
    ]).to_csv(
        os.path.join(run_dir,'outputs','retail','retail_rate_USA_centsperkWh.csv'))

    ### Load the pre-calculated outputs
    dfplot = get_dfplot(run_dir=run_dir, inputpath=inputpath, plot_dollar_year=plot_dollar_year)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(7,3.75))
    ### EIA
    ax.plot(dfeia.index, dfeia.RetailTotal_real, c='C0', ls='-', label='Historical (EIA)')
    ### Calculated
    ax.plot(dfplot.loc[startyear:].index, 
            dfplot.loc[startyear:].sum(axis=1,numeric_only=True).values,
            label='Projected (with bias correction)', color='C3', ls='--')
    ax.plot(dfplot.loc[startyear:].index, 
            dfplot.drop('bias_correction',axis=1).loc[startyear:].sum(axis=1,numeric_only=True).values,
            label='Projected (no bias correction)', color='C3', ls=':')
    ### Formatting
    ax.set_xlim(1960,endyear)
    ax.set_xlabel('Year')
    ax.set_ylabel('Retail rate [{}¢/kWh]'.format(plot_dollar_year))
    ax.set_ylim(0)
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(4))
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(4))
    ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.legend(frameon=False, fontsize='large',loc='lower right')

    plots.despine(ax)
    savename = os.path.join(run_dir,'outputs','retail','retail_rate_USA_EIA.png')
    plt.savefig(savename)
    plt.close()

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == '__main__':
    mdir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(description='run retail rate module')
    parser.add_argument('rundir', type=str,
                        help="name of run directory (leave out 'runs' and directory separators)")
    parser.add_argument('-p', '--plots', action='store_true', default=True,
                        help='indicate whether to generate plots')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('-y', '--plot_dollar_year', type=int, default=2022,
                        help='dollar year in which to plot outputs')
    parser.add_argument('-s', '--startyear', type=int, default=2010,
                        help='first year to include in results')
    args = parser.parse_args()
    run_dir = os.path.join(mdir, os.pardir, os.pardir, 'runs', args.rundir)
    plot_dollar_year = args.plot_dollar_year
    startyear = args.startyear

    #%% Time the operation of this script
    tic = datetime.datetime.now()
    log = reeds.log.makelog(scriptname=__file__, logpath=os.path.join(run_dir,'gamslog.txt'))

    #%% Get and write the component revenues
    main(
        run_dir=run_dir, 
        inputpath=os.path.join(mdir,'inputs.csv'),
        write=True, verbose=args.verbose,
        )

    #%% Get and write the US-average retail rate components and summed rate
    print('Getting US-average retail rates')
    dfrate = get_dfplot(
        run_dir=run_dir, inputpath=os.path.join(mdir,'inputs.csv'),
        plot_dollar_year=plot_dollar_year)
    dfrate.loc[startyear:].to_csv(
        os.path.join(run_dir,'outputs','retail','retail_rate_USA_centsperkWh_allcomponents.csv'))

    if args.plots:
        retail_plots(run_dir=run_dir, inputpath=os.path.join(mdir,'inputs.csv'))

    reeds.log.toc(tic=tic, year=0, process='retail_rate_calculations.py', path=run_dir)
    print('Finished retail_rate_calculations.py')
