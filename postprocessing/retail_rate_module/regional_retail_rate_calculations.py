import argparse
import datetime
import itertools
import os
import sys
import numpy as np
import pandas as pd
import gdxpds

# Local imports
import calculate_historical_capex
import ferc_distadmin

# Allow importing ReEDS utilities
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import reeds


# Shared labels (kept consistent with retail_rate_calculations.py)
tracelabels = {
    'bias_correction': 'Region bias correction',
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


# Utility functions (copied and minimally adapted from retail_rate_calculations.py)
def interp_between_solve_years(
        df, value_name, modeled_years, non_modeled_years,
        first_year, last_year, region_list, region_type):
    if df.empty:
        return df
    df_pivot_solve_years = pd.DataFrame(index=modeled_years, columns=region_list)
    df_pivot_solve_years.update(df.pivot(index='t', columns=region_type, values=value_name))
    df_pivot_solve_years = df_pivot_solve_years.fillna(0.0)

    df_pivot = pd.DataFrame(index=np.arange(first_year, last_year + 1, 1), columns=region_list)
    df_pivot.update(df_pivot_solve_years)

    for year in non_modeled_years:
        preceding_model_year = np.max([x for x in modeled_years if x < year])
        following_model_year = np.min([x for x in modeled_years if x > year])
        interp_f = (year - preceding_model_year) / (following_model_year - preceding_model_year)
        df_pivot.loc[year, :] = (
            df_pivot.loc[preceding_model_year, :]
            + interp_f * (df_pivot.loc[following_model_year, :] - df_pivot.loc[preceding_model_year, :])
        )

    df_pivot = df_pivot.reset_index().rename(columns={'index': 't'})
    df = df_pivot.melt(id_vars='t', value_name=value_name)
    df[value_name] = df[value_name].astype(float)
    return df


def distribute_between_solve_years(df, value_col, modeled_years, years):
    first_year = np.min(modeled_years)
    year_expander = pd.DataFrame(index=years)
    year_expander['t_modeled'] = None
    year_expander['alloc_f'] = 0
    year_expander.loc[first_year, ['t_modeled', 'alloc_f']] = [first_year, 1.0]
    for year in year_expander.index[1:]:
        preceding_model_year = np.max([x for x in modeled_years if x < year])
        following_model_year = np.min([x for x in modeled_years if x >= year])
        if year in list(modeled_years):
            year_expander.loc[year, 't_modeled'] = year
        else:
            year_expander.loc[year, 't_modeled'] = following_model_year
        year_expander.loc[year, 'alloc_f'] = 1 / (following_model_year - preceding_model_year)

    year_expander = year_expander.reset_index().rename(columns={'index': 't'})
    df = df.merge(year_expander[['t', 't_modeled', 'alloc_f']], on='t_modeled', how='left')
    df[value_col] = df[value_col] * df['alloc_f']
    return df


def duplicate_between_solve_years(df, modeled_years, years):
    first_year = np.min(modeled_years)
    year_expander = pd.DataFrame(index=years)
    year_expander['t_modeled'] = None
    year_expander.loc[first_year, ['t_modeled']] = [first_year]
    for year in year_expander.index[1:]:
        following_model_year = np.min([x for x in modeled_years if x >= year])
        if year in list(modeled_years):
            year_expander.loc[year, 't_modeled'] = year
        else:
            year_expander.loc[year, 't_modeled'] = following_model_year
    year_expander = year_expander.reset_index().rename(columns={'index': 't'})
    df = df.merge(year_expander[['t', 't_modeled']], on='t_modeled', how='left')
    return df


def get_wacc_nominal(
        debt_fraction=0.55, equity_return_nominal=0.096,
        debt_interest_nominal=0.039, tax_rate=0.21):
    return (
        debt_fraction * debt_interest_nominal * (1 - tax_rate)
        + (1 - debt_fraction) * equity_return_nominal
    )


def get_wacc_real(wacc_nominal, inflation=0.025):
    return (1 + wacc_nominal) / (1 + inflation) - 1


def get_crf(wacc_real, lifetime):
    return ((wacc_real * (1 + wacc_real) ** lifetime) / ((1 + wacc_real) ** lifetime - 1))


def read_file(filename):
    try:
        f = pd.read_hdf(filename + '.h5')
    except FileNotFoundError:
        try:
            f = pd.read_csv(filename + '.csv.gz')
        except FileNotFoundError:
            try:
                f = pd.read_pickle(filename + '.pkl')
            except ValueError:
                import pickle5
                with open(filename + '.pkl', 'rb') as p:
                    f = pickle5.load(p)
    return f


def main(run_dir, inputpath='inputs.csv', write=True, verbose=0):
    """Calculate retail rate components for each ReEDS BA region (r) and year.

    Outputs a dataframe with columns including:
    ['r','t','busbar_load','end_use_load','distpv_gen','retail_load', ... components ...]
    and optionally writes to outputs/retail/regional_retail_rate_components.csv
    """
    print('Starting regional_retail_rate_calculations.py')

    # Ensure historical capex is available
    calculate_historical_capex.main(run_dir)

    mdir = os.path.dirname(os.path.abspath(__file__))

    # Read inputs
    dfinputs = pd.read_csv(inputpath)
    inputs = dict(dfinputs.loc[dfinputs['input_dict'] == 'inputs', ['input_key', 'input_value']].values)
    intkeys = [
        'working_capital_days', 'trans_timeframe', 'eval_period_overwrite', 'dollar_year',
        'drop_pgesce_20182019', 'numslopeyears', 'numprojyears', 'current_t', 'cleanup',
    ]
    floatkeys = ['distloss', 'FOM_capitalization_rate']
    inputs = {key: (int(inputs[key]) if key in intkeys
                    else float(inputs[key]) if key in floatkeys
                    else str(inputs[key]))
              for key in inputs}

    input_daproj = dict(
        dfinputs.loc[dfinputs.input_dict == 'input_daproj', ['input_key', 'input_value']].values
    )
    input_daproj = {key: (int(input_daproj[key]) if key in intkeys else str(input_daproj[key]))
                    for key in input_daproj}

    input_eval_periods = dict(
        dfinputs.loc[dfinputs.input_dict == 'input_eval_periods', ['input_key', 'input_value']].values
    )
    input_eval_periods = {key: int(input_eval_periods[key]) for key in input_eval_periods}

    input_depreciation_schedules = dict(
        dfinputs.loc[dfinputs.input_dict == 'input_depreciation_schedules', ['input_key', 'input_value']].values
    )
    input_depreciation_schedules = {key: str(int(input_depreciation_schedules[key])) for key in input_depreciation_schedules}

    # Regions and mappings
    regions_map = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'hierarchy.csv')).rename(columns={'*r': 'r', 'st': 'state'})
    ba_state_map = regions_map[['r', 'state']].drop_duplicates()
    r_list = regions_map['r'].drop_duplicates()

    # s->r mapping for outputs that use s regions
    rs_map = pd.read_csv(os.path.join(mdir, 'inputs', 'rsmap.csv'))
    s2r = dict(zip(rs_map['rs'], rs_map['r']))

    # Load ReEDS load and get modeled/non-modeled years
    load_rt = (
        pd.read_csv(os.path.join(run_dir, 'outputs', 'load_cat.csv'))
        .rename(columns={'loadtype': 'load_category', 'Dim1': 'load_category', 'Dim2': 'r', 'Dim3': 't', 'Value': 'busbar_load', 'Val': 'busbar_load'})
    )
    omit_list = ['stor_charge', 'trans_loss']
    overall_list = list(load_rt['load_category'].drop_duplicates())
    final_list = list(set(overall_list) - set(omit_list))
    load_rt = load_rt[load_rt['load_category'].isin(final_list)]
    load_rt = load_rt.groupby(['r', 't'], as_index=False).agg({'busbar_load': 'sum'})

    first_year = int(load_rt['t'].min())
    last_year = int(load_rt['t'].max())
    modeled_years = load_rt['t'].drop_duplicates()
    non_modeled_years = list(set(np.arange(first_year, last_year, 1)) - set(modeled_years))
    years_reeds = np.arange(first_year, last_year + 1)

    # Inflation
    inflation = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'inflation.csv'), index_col='t').squeeze(1)

    # Region loads and end-use
    load_rt = interp_between_solve_years(load_rt, 'busbar_load', modeled_years, non_modeled_years, first_year, last_year, r_list, 'r')
    load_rt['end_use_load'] = load_rt['busbar_load'] * (1 - inputs['distloss'])

    # Initialize dfall at region-level
    dfall = pd.DataFrame(list(itertools.product(r_list, np.arange(first_year, last_year + 1))), columns=['r', 't'])
    dfall = dfall.merge(load_rt[['r', 't', 'busbar_load', 'end_use_load']], on=['r', 't'], how='left')

    # Generation outputs for distpv and retail load (needed before transmission O&M)
    gen_ivrt = pd.read_csv(os.path.join(run_dir, 'outputs', 'gen_ivrt.csv')).rename(columns={'i': 'i', 'v': 'v', 'r': 'r', 't': 't_modeled', 'Value': 'gen', 'Dim1': 'i', 'Dim2': 'v', 'Dim3': 'r', 'Dim4': 't_modeled', 'Val': 'gen'})
    gen_ivrt = duplicate_between_solve_years(gen_ivrt, modeled_years, years_reeds)
    distpv_gen = gen_ivrt[gen_ivrt['i'] == 'distpv'].copy()
    distpv_gen_grouped = distpv_gen.groupby(['t', 'r'], as_index=False).agg({'gen': 'sum'}).rename(columns={'gen': 'distpv_gen'})
    dfall = dfall.merge(distpv_gen_grouped, on=['t', 'r'], how='left')
    dfall['distpv_gen'] = dfall['distpv_gen'].fillna(0.0)
    dfall['retail_load'] = dfall['end_use_load'] - dfall['distpv_gen']

    # System costs (region-level)
    system_costs = pd.read_csv(os.path.join(run_dir, 'outputs', 'systemcost_ba_retailrate.csv'))
    system_costs = system_costs.rename(columns={'sys_costs': 'cost_type', 'r': 'region', 't': 't', 'Value': 'cost', 'Dim1': 'cost_type', 'Dim2': 'region', 'Dim3': 't', 'Val': 'cost'})
    system_costs.loc[system_costs['region'].str.contains('s'), 'region'] = system_costs.loc[system_costs['region'].str.contains('s'), 'region'].map(s2r)
    system_costs = system_costs.groupby(by=['cost_type', 'region', 't'], as_index=False).agg({'cost': 'sum'})
    system_costs['cost'] = system_costs['cost'].replace('Undf', 0).astype(float)

    # Financing assumptions
    financepath = inputs['financefile']
    if not os.path.exists(financepath):
        financepath = os.path.join(mdir, financepath)
    df_finance = pd.read_csv(financepath, index_col='t')

    # Regional expenditure flows (imports - exports per region)
    state_flows = (
        pd.read_csv(os.path.join(run_dir, 'outputs', 'expenditure_flow.csv'))
        .rename(columns={'*': 'price_type', 'r': 'sending_region', 'rr': 'receiving_region', 't': 't', 'Value': 'expenditure_flow', 'Dim1': 'price_type', 'Dim2': 'sending_region', 'Dim3': 'receiving_region', 'Dim4': 't', 'Val': 'expenditure_flow'})
    )
    # Filter intra-region
    state_flows = state_flows[state_flows['sending_region'] != state_flows['receiving_region']]

    # International flows: treat as region-level imports/exports
    state_international_flows = (
        pd.read_csv(os.path.join(run_dir, 'outputs', 'expenditure_flow_int.csv'))
        .rename(columns={'r': 'receiving_region', 't': 't', 'Value': 'expenditure_flow', 'Dim1': 'receiving_region', 'Dim2': 't', 'Val': 'expenditure_flow'})
    )
    state_international_flows['price_type'] = 'load'
    state_international_flows['sending_region'] = 'Canada'
    state_international_flows['flowtype'] = state_international_flows['expenditure_flow'].map(lambda x: 'export' if x < 0 else 'import')
    # Normalize sign and sides for exports (make positive and flip)
    for i in state_international_flows.index:
        if state_international_flows.loc[i, 'expenditure_flow'] < 0:
            (state_international_flows.loc[i, 'sending_region'], state_international_flows.loc[i, 'receiving_region']) = (
                state_international_flows.loc[i, 'receiving_region'], 'Canada')
            state_international_flows.loc[i, 'expenditure_flow'] = -state_international_flows.loc[i, 'expenditure_flow']

    # Combine flows
    flows_all = pd.concat([state_flows, state_international_flows], sort=False)

    sent_expenditures = flows_all.groupby(by=['price_type', 't', 'sending_region'], as_index=False).agg({'expenditure_flow': 'sum'}).rename(columns={'sending_region': 'region', 'expenditure_flow': 'expenditure_exports'})
    received_expenditures = flows_all.groupby(by=['price_type', 't', 'receiving_region'], as_index=False).agg({'expenditure_flow': 'sum'}).rename(columns={'receiving_region': 'region', 'expenditure_flow': 'expenditure_imports'})
    region_flow_expenditures = sent_expenditures.merge(received_expenditures, on=['price_type', 't', 'region'], how='outer').fillna(0)
    region_flow_expenditures['net_interregional_expenditures'] = region_flow_expenditures['expenditure_imports'] - region_flow_expenditures['expenditure_exports']
    region_flow_expenditures = region_flow_expenditures.groupby(['t', 'region', 'price_type'])['net_interregional_expenditures'].sum().unstack('price_type').reset_index()
    region_flow_expenditures = region_flow_expenditures.add_suffix('_flow').rename(columns={'t_flow': 't', 'region_flow': 'r'})

    # Interpolate flow components across years
    region_flow_expenditures_expanded = interp_between_solve_years(region_flow_expenditures, 'load_flow', modeled_years, non_modeled_years, first_year, last_year, r_list, 'r')
    if 'oper_res_flow' in region_flow_expenditures:
        region_flow_expenditures_expanded = region_flow_expenditures_expanded.merge(
            interp_between_solve_years(region_flow_expenditures, 'oper_res_flow', modeled_years, non_modeled_years, first_year, last_year, r_list, 'r'),
            on=['t', 'r'])
    if 'rps_flow' in region_flow_expenditures:
        region_flow_expenditures_expanded = region_flow_expenditures_expanded.merge(
            interp_between_solve_years(region_flow_expenditures, 'rps_flow', modeled_years, non_modeled_years, first_year, last_year, r_list, 'r'),
            on=['t', 'r'])
    region_flow_expenditures_expanded = region_flow_expenditures_expanded.merge(
        interp_between_solve_years(region_flow_expenditures, 'res_marg_ann_flow', modeled_years, non_modeled_years, first_year, last_year, r_list, 'r'),
        on=['t', 'r'])

    dfall = dfall.merge(region_flow_expenditures_expanded, on=['t', 'r'], how='left').fillna(0)

    # Operational costs (pass-through)
    op_costs_types_omitted = ['op_transmission_fom', 'op_ptc_payments_negative', 'op_co2_incentive_negative', 'op_h2_ptc_payments_negative', 'op_h2_storage', 'op_h2_transport', 'op_h2_fuel_costs', 'op_h2_vom', 'op_consume_vom', 'op_consume_fom']
    op_cost_types = [i for i in system_costs['cost_type'].drop_duplicates() if (('op_' in i) and (i not in op_costs_types_omitted))]
    op_costs_modeled_years = system_costs[system_costs['cost_type'].isin(op_cost_types)].copy()
    op_costs_modeled_years = op_costs_modeled_years.rename(columns={'region': 'r'})
    op_costs_modeled_years = op_costs_modeled_years.groupby(by=['cost_type', 't', 'r'], as_index=False).agg({'cost': 'sum'})

    op_costs = pd.DataFrame()
    for op_cost_type in op_cost_types:
        op_costs_single = (op_costs_modeled_years[op_costs_modeled_years['cost_type'] == op_cost_type].rename(columns={'cost': op_cost_type}))
        op_costs_single = interp_between_solve_years(op_costs_single, op_cost_type, modeled_years, non_modeled_years, first_year, last_year, r_list, 'r')
        op_costs_single['cost_type'] = op_cost_type
        op_costs_single = op_costs_single.rename(columns={op_cost_type: 'cost'})
        op_costs = pd.concat([op_costs, op_costs_single], sort=False).reset_index(drop=True)

    op_costs_pivot = op_costs.pivot_table(index=['t', 'r'], columns='cost_type', values='cost', fill_value=0.0).reset_index()

    # Emissions by BA region
    emissions_r = (pd.read_csv(os.path.join(run_dir, 'outputs', 'emit_r.csv')).rename(columns={'Value': 'emissions', 'Val': 'emissions'}))
    emissions_r = emissions_r.loc[(emissions_r.etype == 'process') & (emissions_r.eall == 'CO2')].drop(columns=['etype', 'eall'])
    r_list_emissions = emissions_r['r'].drop_duplicates()
    emissions_r = interp_between_solve_years(emissions_r, 'emissions', modeled_years, non_modeled_years, first_year, last_year, r_list_emissions, 'r')
    emissions_r.loc[emissions_r['emissions'] < 0, 'emissions'] = 0
    emissions_no_negative = emissions_r.copy()

    # Redistribute DAC op costs by BA emissions share
    if 'op_co2_transport_storage' in op_costs_pivot.columns:
        emissions_fraction = emissions_no_negative.pivot_table(index='t', columns='r', values='emissions').fillna(0)
        emissions_fraction['Total'] = emissions_fraction.sum(axis=1)
        ba_cols = [c for c in emissions_fraction.columns if c != 'Total']
        emissions_r_fraction = emissions_fraction.copy()
        emissions_r_fraction[ba_cols] = (emissions_r_fraction[ba_cols].div(emissions_r_fraction['Total'], axis=0))
        emissions_r_fraction.drop(columns=['Total'], inplace=True)
        cap_corrections = op_costs_pivot[['t', 'r', 'op_co2_transport_storage']].copy()
        cap_corrections['op_co2_transport_storage'] = 0
        cap_corrections = cap_corrections.pivot_table(index='t', columns='r', values='op_co2_transport_storage')
        for i in range(op_costs_pivot.shape[0]):
            cost = op_costs_pivot.loc[i, 'op_co2_transport_storage']
            year = op_costs_pivot.loc[i, 't']
            multiplier = emissions_r_fraction.loc[year] if year in emissions_r_fraction.index else None
            if multiplier is not None:
                cap_corrections.loc[year] += (cost * multiplier)
        cap_corrections = cap_corrections.T.unstack().reset_index().rename(columns={0: 'op_co2_transport_storage', 'level_0': 'r', 'level_1': 't'})
        assert round(op_costs_pivot['op_co2_transport_storage'].values.sum(), 2) == round(cap_corrections['op_co2_transport_storage'].values.sum(), 2)
        op_costs_pivot = op_costs_pivot.drop(columns=['op_co2_transport_storage']).merge(cap_corrections, on=['t', 'r'], how='left').fillna({'op_co2_transport_storage': 0})

    # Extrapolate FOM costs backward to historical years using normalized cost by load from first modeled year
    historical_years = np.arange(int(load_rt['t'].min()), first_year)
    df_extrapolate = pd.DataFrame(list(itertools.product(r_list, historical_years)), columns=['r', 't'])
    tmp = op_costs_pivot.merge(load_rt[['r', 't', 'end_use_load']], on=['r', 't'], how='left')
    first_model_year = int(modeled_years.min())
    op_costs_first_year = tmp.loc[tmp['t'] == first_model_year, ['r', 'end_use_load', 'op_fom_costs']].rename(columns={'end_use_load': 'load_first_year', 'op_fom_costs': 'op_fom_costs_first_year'})
    df_extrapolate = df_extrapolate.merge(op_costs_first_year, on=['r'], how='left').merge(load_rt[['r', 't', 'end_use_load']], on=['r', 't'], how='left')
    df_extrapolate['op_fom_costs'] = (df_extrapolate['end_use_load'] / df_extrapolate['load_first_year'] * df_extrapolate['op_fom_costs_first_year'])
    df_extrapolate = df_extrapolate[['t', 'r', 'op_fom_costs']]
    op_costs_pivot = pd.concat([op_costs_pivot, df_extrapolate], sort=False)
    op_costs_pivot['op_fom_costs'] = ((1 - inputs['FOM_capitalization_rate']) * op_costs_pivot['op_fom_costs'])

    # Working capital
    op_costs_pivot = op_costs_pivot.merge(df_finance, on='t', how='left')
    op_cols = [c for c in op_costs_pivot.columns if c.startswith('op_')]
    op_costs_pivot['wc'] = (inputs['working_capital_days'] / 365) * op_costs_pivot[op_cols].sum(axis=1)
    op_costs_pivot['op_wc_debt_interest'] = (op_costs_pivot['wc'] * op_costs_pivot['debt_fraction'] * op_costs_pivot['debt_interest_nominal'])
    op_costs_pivot['op_wc_equity_return'] = (op_costs_pivot['wc'] * (1.0 - op_costs_pivot['debt_fraction']) * op_costs_pivot['equity_return_nominal'])
    op_costs_pivot['op_wc_return_to_capital'] = (op_costs_pivot['op_wc_debt_interest'] + op_costs_pivot['op_wc_equity_return'])
    op_costs_pivot['op_wc_income_tax'] = (op_costs_pivot['op_wc_equity_return'] / (1.0 - op_costs_pivot['tax_rate']) - op_costs_pivot['op_wc_equity_return'])

    dfall = dfall.merge(op_costs_pivot[[*op_cols, 't', 'r', 'op_wc_debt_interest', 'op_wc_equity_return', 'op_wc_income_tax']], on=['t', 'r'], how='left')

    # Capital expenditures: capitalized FOM
    df_fom_capitalized = op_costs_pivot[['t', 'r', 'op_fom_costs']].copy()
    df_fom_capitalized['capex'] = df_fom_capitalized['op_fom_costs'] / (1.0 - inputs['FOM_capitalization_rate']) * inputs['FOM_capitalization_rate']
    df_fom_capitalized.drop(columns=['op_fom_costs'], inplace=True)
    df_fom_capitalized['eval_period'] = input_eval_periods['fom_capitalized']
    df_fom_capitalized['depreciation_sch'] = input_depreciation_schedules['fom_capitalized']
    df_fom_capitalized['i'] = 'capitalized_fom'
    df_fom_capitalized['region'] = None
    df_fom_capitalized['cost_cat'] = 'cap_fom'

    df_capex = df_fom_capitalized.copy()

    # Generator capex and capacity builds
    cap_new_ivrt = pd.read_csv(os.path.join(run_dir, 'outputs', 'cap_new_ivrt.csv')).rename(columns={'i': 'i', 'r': 'region', 't': 't_modeled', 'Value': 'cap_new', 'Dim1': 'i', 'Dim2': 'v', 'Dim3': 'region', 'Dim4': 't_modeled', 'Val': 'cap_new'})
    cap_new_ivrt.loc[cap_new_ivrt['region'].str.contains('s'), 'region'] = cap_new_ivrt.loc[cap_new_ivrt['region'].str.contains('s'), 'region'].map(s2r)
    cap_new_ivrt = cap_new_ivrt.groupby(by=['i', 'region', 't_modeled'], as_index=False).agg({'cap_new': 'sum'})
    cap_new_ivrt_distributed = distribute_between_solve_years(cap_new_ivrt, 'cap_new', modeled_years, years_reeds)
    df_gen_capex = cap_new_ivrt_distributed[['i', 'region', 't', 'cap_new']].copy().groupby(by=['i', 'region', 't'], as_index=False).agg({'cap_new': 'sum'})

    df_capex_irt = pd.read_csv(os.path.join(run_dir, 'outputs', 'capex_ivrt.csv')).rename(columns={'r': 'region', 't': 't_modeled', 'Value': 'capex'})
    df_capex_irt = df_capex_irt.groupby(by=['i', 'region', 't_modeled'], as_index=False).agg({'capex': 'sum'})

    invcapcosts = ['inv_dac', 'inv_h2_production', 'inv_investment_capacity_costs', 'inv_investment_refurbishment_capacity', 'inv_investment_spurline_costs_rsc_technologies']
    df_syscost_irt = pd.read_csv(os.path.join(run_dir, 'outputs', 'systemcost_techba.csv')).rename(columns={'r': 'region', 't': 't_modeled', 'Value': 'capex'})
    df_syscost_irt = df_syscost_irt[df_syscost_irt['sys_costs'].isin(invcapcosts)].groupby(by=['i', 'region', 't_modeled'], as_index=False).agg({'capex': 'sum'})

    df_capex_irt = df_capex_irt.merge(df_syscost_irt, on=['i', 'region', 't_modeled'], how='outer', suffixes=('_capex', '_syscost'))
    df_capex_irt['capex'] = df_capex_irt[['capex_capex', 'capex_syscost']].max(axis=1)
    df_capex_irt = df_capex_irt[['i', 'region', 't_modeled', 'capex']]
    df_capex_irt_distributed = distribute_between_solve_years(df_capex_irt, 'capex', modeled_years, years_reeds)

    # Redistribute DAC capex by BA emissions fraction
    if 'dac' in df_capex_irt_distributed['i'].unique():
        emissions_fraction = emissions_no_negative.pivot_table(index='t', columns='r', values='emissions').fillna(0)
        emissions_fraction['Total'] = emissions_fraction.sum(axis=1)
        ba_cols = [c for c in emissions_fraction.columns if c != 'Total']
        emissions_r_fraction = emissions_fraction.copy()
        emissions_r_fraction[ba_cols] = (emissions_r_fraction[ba_cols].div(emissions_r_fraction['Total'], axis=0))
        emissions_r_fraction.drop(columns=['Total'], inplace=True)
        dac_mask = df_capex_irt_distributed['i'] == 'dac'
        capex_dac = df_capex_irt_distributed[dac_mask].copy().fillna(0)
        capex_dac = capex_dac.rename(columns={'region': 'r'})
        capex_dac_corrections = df_capex_irt_distributed.pivot_table(index='region', columns='t', values='capex')
        capex_dac_corrections.loc[:, :] = 0
        missing_r = list(set(capex_dac_corrections.index) - set(emissions_r_fraction.columns))
        capex_dac_corrections.drop(missing_r, axis=0, inplace=True)
        num_r = capex_dac_corrections.shape[0]
        for _, row in capex_dac.iterrows():
            cost = row['capex']
            year = row['t']
            if year <= last_year and year in emissions_r_fraction.index:
                multiplier = emissions_r_fraction.loc[year]
                assert (multiplier.shape[0] == num_r)
                capex_dac_corrections.loc[:, year] += (cost * multiplier)
        for r_missing in missing_r:
            capex_dac_corrections.loc[r_missing, :] = 0
        capex_dac_corrections = capex_dac_corrections.loc[:, (capex_dac_corrections.sum(axis=0) != 0)]
        capex_dac_corrections = capex_dac_corrections.reset_index().melt(id_vars='region', value_name='capex')
        capex_dac_corrections = capex_dac_corrections.assign(i='dac')
        assert round(capex_dac_corrections['capex'].sum(), 2) == round(capex_dac['capex'].sum(), 2)
        df_capex_irt_distributed = pd.concat([
            df_capex_irt_distributed[~dac_mask][['i', 'region', 't', 'capex']],
            capex_dac_corrections[['i', 'region', 't', 'capex']].sort_values(by=['region', 't'])
        ])

    df_gen_capex = df_gen_capex.merge(df_capex_irt_distributed[['i', 'region', 't', 'capex']], on=['i', 'region', 't'], how='outer')

    # Eval period and depreciation schedules
    eval_period = read_file(os.path.join(run_dir, 'inputs_case', 'retail_eval_period'))
    depreciation_sch = read_file(os.path.join(run_dir, 'inputs_case', 'retail_depreciation_sch'))
    depreciation_sch['depreciation_sch'] = depreciation_sch['depreciation_sch'].astype(str)

    df_gen_capex = df_gen_capex.merge(eval_period[['i', 't', 'eval_period']], on=['i', 't'], how='left')
    df_gen_capex['eval_period'].fillna(20, inplace=True)
    df_gen_capex = df_gen_capex.merge(depreciation_sch[['i', 't', 'depreciation_sch']], on=['i', 't'], how='left')
    df_gen_capex['depreciation_sch'].fillna('20', inplace=True)

    # Historical generator capex
    df_gen_capex_init = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'df_capex_init.csv'))
    df_gen_capex_init = df_gen_capex_init[df_gen_capex_init['t'] <= first_year]
    first_hist_year = int(load_rt['t'].min())
    df_gen_capex_init = df_gen_capex_init[df_gen_capex_init['t'] >= first_hist_year]
    df_gen_capex_init.loc[df_gen_capex_init['region'].str.contains('s'), 'region'] = df_gen_capex_init.loc[df_gen_capex_init['region'].str.contains('s'), 'region'].map(s2r)
    df_gen_capex_init = df_gen_capex_init.groupby(by=['i', 'region', 't'], as_index=False).agg({'cap_new': 'sum', 'capex': 'sum'})

    init_irt = df_gen_capex_init[['i', 'region', 't']].copy().drop_duplicates()
    eval_period_init = init_irt.merge(eval_period[eval_period['t'] == first_year][['i', 'eval_period']], on='i', how='left')
    eval_period_init = eval_period_init[eval_period_init['t'] <= first_year]
    dep_sch_init = init_irt.merge(depreciation_sch[depreciation_sch['t'] == first_year][['i', 'depreciation_sch']], on='i', how='left')
    dep_sch_init = dep_sch_init[dep_sch_init['t'] <= first_year]
    df_gen_capex_init = df_gen_capex_init.merge(eval_period_init[['i', 'region', 't', 'eval_period']], on=['i', 'region', 't'], how='left')
    df_gen_capex_init['eval_period'].fillna(20, inplace=True)
    df_gen_capex_init = df_gen_capex_init.merge(dep_sch_init[['i', 'region', 't', 'depreciation_sch']], on=['i', 'region', 't'], how='left')
    df_gen_capex_init['depreciation_sch'].fillna('20', inplace=True)

    df_gen_capex = pd.concat([df_gen_capex, df_gen_capex_init], sort=False).reset_index(drop=True)
    df_gen_capex['cost_cat'] = 'cap_gen'
    df_gen_capex = df_gen_capex.dropna(axis=0, how='all', subset='capex').reset_index(drop=True)
    if inputs['eval_period_overwrite'] != 0:
        df_gen_capex['eval_period'] = inputs['eval_period_overwrite']
    df_capex = pd.concat([df_capex, df_gen_capex[['i', 'region', 't', 'cost_cat', 'capex', 'eval_period', 'depreciation_sch']]], sort=False).reset_index(drop=True)

    # Non-generator ReEDS capex
    system_costs_ng = system_costs.copy()
    system_costs_ng.loc[system_costs_ng['cost_type'] == 'inv_transmission_intrazone_investment', 'cost_type'] = 'inv_transmission_interzone_ac_investment'
    system_costs_ng = system_costs_ng.groupby(by=['cost_type', 'region', 't'], as_index=False).agg({'cost': 'sum'})
    nongen_inv_eval_periods = pd.DataFrame(columns=['cost_type', 'eval_period'], data=[[x, input_eval_periods[x]] for x in ['inv_investment_spurline_costs_rsc_technologies', 'inv_transmission_line_investment', 'inv_transmission_interzone_ac_investment', 'inv_transmission_interzone_dc_investment', 'inv_converter_costs']])
    nongen_cost_cats = pd.DataFrame(columns=['i', 'cost_cat'], data=[['inv_investment_spurline_costs_rsc_technologies', 'cap_spurline'], ['inv_transmission_line_investment', 'cap_transmission'], ['inv_transmission_interzone_ac_investment', 'cap_transmission'], ['inv_transmission_interzone_dc_investment', 'cap_transmission'], ['inv_converter_costs', 'cap_converter']])
    nongen_inv_cost_types = list(nongen_inv_eval_periods['cost_type'].drop_duplicates())
    nongen_capex = system_costs_ng[system_costs_ng['cost_type'].isin(nongen_inv_cost_types)].merge(nongen_inv_eval_periods, on='cost_type', how='left')
    nongen_capex['depreciation_sch'] = input_depreciation_schedules['nongen_capex']
    nongen_capex = nongen_capex.rename(columns={'t': 't_modeled'})
    nongen_capex_distributed = distribute_between_solve_years(nongen_capex, 'cost', modeled_years, years_reeds)
    nongen_capex_distributed.rename(columns={'cost_type': 'i', 'cost': 'capex', 'region': 'r'}, inplace=True)
    nongen_capex_distributed.drop(columns=['t_modeled', 'alloc_f'], inplace=True)
    nongen_capex_distributed = nongen_capex_distributed.merge(nongen_cost_cats, on='i', how='left')
    df_capex = pd.concat([df_capex, nongen_capex_distributed.rename(columns={'r': 'region'})], sort=False).reset_index(drop=True)

    # Existing transmission historical capex: allocate state totals to BA regions by load share
    inflatable = reeds.io.get_inflatable()
    existing_transmission_cost_bystate = pd.read_csv(os.path.join(mdir, 'calc_historical_capex', 'existing_transmission_cost_bystate_USD2024.csv'), index_col='state').squeeze(1).rename('init_trans_capex') * inflatable[2024, 2004]
    init_trans_state_years = pd.DataFrame({t: existing_transmission_cost_bystate for t in np.arange(first_year - inputs['trans_timeframe'], first_year)}).T
    init_trans_state_years.index.name = 't'
    init_trans_state_years = init_trans_state_years.reset_index().melt(id_vars='t', var_name='state', value_name='init_trans_capex')
    # Compute BA load shares per state using first modeled year
    ba_load_first = load_rt.merge(ba_state_map, on='r', how='left')
    ba_load_first = ba_load_first[ba_load_first['t'] == first_year]
    ba_load_first = ba_load_first.groupby(['state', 'r'], as_index=False)['end_use_load'].sum()
    ba_load_first['state_total'] = ba_load_first.groupby('state')['end_use_load'].transform('sum')
    ba_load_first['share'] = ba_load_first.apply(lambda row: (row['end_use_load'] / row['state_total']) if row['state_total'] else 0, axis=1)
    # Allocate per BA
    init_trans_capex = init_trans_state_years.merge(ba_load_first[['state', 'r', 'share']], on='state', how='left')
    init_trans_capex['capex'] = (init_trans_capex['init_trans_capex'] * init_trans_capex['share'] / inputs['trans_timeframe'])
    init_trans_capex = init_trans_capex[['t', 'r', 'capex']]
    init_trans_capex['i'] = 'inv_transmission_interzone_ac_investment'
    init_trans_capex['eval_period'] = input_eval_periods['init_trans_capex']
    init_trans_capex['depreciation_sch'] = input_depreciation_schedules['init_trans_capex']
    init_trans_capex['cost_cat'] = 'cap_transmission'
    df_capex = pd.concat([df_capex, init_trans_capex.rename(columns={'r': 'region'})], sort=False).reset_index(drop=True)

    # Distribution and Administrative costs per region
    # Get FERC-derived series at desired aggregation
    dist_admin_costs_nation_in = ferc_distadmin.get_ferc_costs(numslopeyears=input_daproj['numslopeyears'], numprojyears=input_daproj['numprojyears'], current_t=input_daproj['current_t'], aggregation='nation', writeout=False, inflationpath=os.path.join(run_dir, 'inputs_case', 'inflation.csv'), drop_pgesce_20182019=input_daproj['drop_pgesce_20182019'], cleanup=input_daproj['cleanup'])
    dist_admin_costs_region_in = ferc_distadmin.get_ferc_costs(numslopeyears=input_daproj['numslopeyears'], numprojyears=input_daproj['numprojyears'], current_t=input_daproj['current_t'], aggregation='region', writeout=False, inflationpath=os.path.join(run_dir, 'inputs_case', 'inflation.csv'), drop_pgesce_20182019=input_daproj['drop_pgesce_20182019'], cleanup=input_daproj['cleanup']).sort_values(['region', 't']).set_index(['region', 't'])
    # Prepare BA->FERC region mapping via state
    ba_region_ferc = ba_state_map.copy()
    ba_region_ferc['region_ferc'] = ba_region_ferc['state'].map(ferc_distadmin.state2region)
    ba_region_ferc = ba_region_ferc.dropna(subset=['region_ferc'])

    # Select aggregation level series and broadcast to BA regions
    agg = input_daproj['aggregation']
    if agg == 'nation':
        # Duplicate national series for each BA region
        dist_admin_costs = pd.concat({r: dist_admin_costs_nation_in for r in r_list if r in ba_region_ferc['r'].values}, axis=0).reset_index(level=0).rename(columns={'level_0': 'r'}).sort_values(['r', 't']).set_index(['r', 't']).drop('nation', axis=1)
    elif agg == 'region':
        # Use FERC region series and broadcast to BA regions within each state
        dist_admin_costs = pd.concat({r: dist_admin_costs_region_in.loc[ba_region_ferc.set_index('r').loc[r, 'region_ferc']] for r in ba_region_ferc['r'].unique()}, axis=0).reset_index().rename(columns={'level_0': 'r'}).sort_values(['r', 't']).set_index(['r', 't'])
    elif agg in ['state', 'best']:
        # State-specific series; broadcast to BA regions using state
        dist_admin_costs_state = ferc_distadmin.get_ferc_costs(numslopeyears=input_daproj['numslopeyears'], numprojyears=input_daproj['numprojyears'], current_t=input_daproj['current_t'], aggregation='state', writeout=False, inflationpath=os.path.join(run_dir, 'inputs_case', 'inflation.csv'), drop_pgesce_20182019=input_daproj['drop_pgesce_20182019'], cleanup=input_daproj['cleanup']).sort_values(['state', 't']).set_index(['state', 't'])
        dist_admin_costs = pd.concat({r: dist_admin_costs_state.loc[ba_state_map.set_index('r').loc[r, 'state']] for r in ba_state_map['r'].unique() if ba_state_map.set_index('r').loc[r, 'state'] in dist_admin_costs_state.index.get_level_values('state')}, axis=0).reset_index().rename(columns={'level_0': 'r'}).sort_values(['r', 't']).set_index(['r', 't'])
        if agg == 'best':
            # For best, keep national default and replace with region/state best choice
            best = pd.read_csv(os.path.join(mdir, 'inputs', 'state-meanbiaserror_rate-aggregation.csv'), usecols=['index', 'aggregation'], index_col='index').squeeze(1)
            # Broadcast best choices to BA via state mapping
            replacestates = best.loc[best == 'state'].index.values
            replaceregions = best.loc[best == 'region'].index.values
            # Build a hybrid: start with national per BA, then replace by chosen series
            dist_admin_costs_nation = pd.concat({r: dist_admin_costs_nation_in for r in r_list if r in ba_region_ferc['r'].values}, axis=0).reset_index(level=0).rename(columns={'level_0': 'r'}).sort_values(['r', 't']).set_index(['r', 't']).drop('nation', axis=1)
            dist_admin_costs_region = pd.concat({r: dist_admin_costs_region_in.loc[ba_region_ferc.set_index('r').loc[r, 'region_ferc']] for r in ba_region_ferc['r'].unique()}, axis=0).reset_index().rename(columns={'level_0': 'r'}).sort_values(['r', 't']).set_index(['r', 't'])
            # Keep BA in states without replacement; then apply replacements
            dist_admin_costs = dist_admin_costs_nation.copy()
            # Replace state-selected
            for st in replacestates:
                rs_in_state = ba_state_map[ba_state_map['state'] == st]['r'].unique()
                for r in rs_in_state:
                    if (st, dist_admin_costs_state.index.get_level_values('t').min()) in dist_admin_costs_state.index:
                        dist_admin_costs.loc[(r, slice(None)), :] = dist_admin_costs_state.loc[(st, slice(None)), :].values
            # Replace region-selected
            for st in replaceregions:
                rs_in_state = ba_state_map[ba_state_map['state'] == st]['r'].unique()
                fercreg = ferc_distadmin.state2region.get(st, None)
                if fercreg is None:
                    continue
                for r in rs_in_state:
                    dist_admin_costs.loc[(r, slice(None)), :] = dist_admin_costs_region.loc[(r, slice(None)), :].values
    else:
        dist_admin_costs = pd.concat({r: dist_admin_costs_nation_in for r in r_list if r in ba_region_ferc['r'].values}, axis=0).reset_index(level=0).rename(columns={'level_0': 'r'}).sort_values(['r', 't']).set_index(['r', 't']).drop('nation', axis=1)

    # Backfill per_mwh columns to earliest year
    dist_admin_costs = dist_admin_costs.reset_index()
    extrapolation_years = list(range(first_year, dist_admin_costs.t.min()))
    insert = pd.DataFrame({'t': extrapolation_years * len(r_list), 'r': [item for sublist in [[ri] * len(extrapolation_years) for ri in r_list] for item in sublist]})
    dist_admin_costs = pd.concat([dist_admin_costs, insert]).sort_values(['r', 't']).reset_index(drop=True)
    bfillcols = [c for c in dist_admin_costs if c.endswith('_per_mwh')]
    if len(bfillcols):
        dist_admin_costs[bfillcols] = dist_admin_costs[bfillcols].interpolate('bfill')
        dist_admin_costs.loc[dist_admin_costs.entry_type.isnull(), 'entry_type'] = 'bfill'

    # Distribution/Admin operational costs per BA region
    dist_admin_opex = load_rt[['t', 'r', 'end_use_load']].merge(dist_admin_costs[['t', 'r', 'dist_opex_per_mwh', 'admin_opex_per_mwh']], on=['t', 'r'], how='inner')
    dist_admin_opex['op_dist'] = (dist_admin_opex['end_use_load'] * dist_admin_opex['dist_opex_per_mwh'])
    dist_admin_opex['op_admin'] = (dist_admin_opex['end_use_load'] * dist_admin_opex['admin_opex_per_mwh'])
    dfall = dfall.merge(dist_admin_opex[['t', 'r', 'op_dist', 'op_admin']], on=['t', 'r'], how='left')

    # Distribution/Admin capex per BA region
    dist_capex = load_rt[['t', 'r', 'end_use_load']].merge(dist_admin_costs[['t', 'r', 'dist_capex_per_mwh']], on=['t', 'r'], how='inner')
    dist_capex['capex'] = dist_capex['end_use_load'] * dist_capex['dist_capex_per_mwh']
    dist_capex['eval_period'] = input_eval_periods['dist_capex']
    dist_capex['depreciation_sch'] = input_depreciation_schedules['dist_capex']
    dist_capex['cost_cat'] = 'cap_dist'
    df_capex = pd.concat([df_capex, dist_capex[['r', 't', 'capex', 'eval_period', 'depreciation_sch', 'cost_cat']].rename(columns={'r': 'region'})], sort=False).reset_index(drop=True)

    admin_capex = load_rt[['t', 'r', 'end_use_load']].merge(dist_admin_costs[['t', 'r', 'admin_capex_per_mwh']], on=['t', 'r'], how='inner')
    admin_capex['capex'] = admin_capex['end_use_load'] * admin_capex['admin_capex_per_mwh']
    admin_capex['eval_period'] = input_eval_periods['admin_capex']
    admin_capex['depreciation_sch'] = input_depreciation_schedules['admin_capex']
    admin_capex['cost_cat'] = 'cap_admin'
    df_capex = pd.concat([df_capex, admin_capex[['r', 't', 'capex', 'eval_period', 'depreciation_sch', 'cost_cat']].rename(columns={'r': 'region'})], sort=False).reset_index(drop=True)

    # Transmission O&M
    trans_cap = pd.read_csv(os.path.join(run_dir, 'outputs', 'tran_out.csv')).rename(columns={'Value': 'tran_cap', 'Dim1': 'r', 'Dim2': 'rr', 'Dim3': 'trtype', 'Dim4': 't', 'Val': 'tran_cap'}).set_index(['r', 'rr', 'trtype', 't'])
    trans_dist = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'transmission_distance.csv')).rename(columns={'*r': 'r'}).set_index(['r', 'rr']).miles
    trans_cap['MWmile'] = (trans_cap['tran_cap'] * trans_dist).reindex(trans_cap.index)
    if any(trans_cap.MWmile.isnull().values):
        raise Exception('Missing distances: {}'.format(trans_cap.loc[trans_cap.MWmile.isnull()]))
    trans_cap.reset_index(inplace=True)
    trans_om = pd.concat([trans_cap[['r', 't', 'MWmile']], trans_cap[['rr', 't', 'MWmile']].rename(columns={'rr': 'r'})], ignore_index=True, sort=False)
    # Nation aggregation: derive OM/MW-mile nationally then apply per BA (divide by 2 for duplication)
    if input_daproj['aggregation'] == 'nation':
        trans_df = (dist_admin_costs.drop('r', axis=1).drop_duplicates()[['t', 'trans_opex_per_mwh']].merge(trans_om.groupby('t')['MWmile'].sum(), on=['t'], how='left').dropna().merge(dfall.groupby('t')['retail_load'].sum(), on=['t'], how='left').dropna())
        trans_df['trans_om'] = trans_df['trans_opex_per_mwh'] * trans_df['retail_load']
        trans_df['trans_om_per_mw_mile'] = trans_df['trans_om'] / trans_df['MWmile']
        trans_om = trans_om.merge(trans_df[['t', 'trans_om_per_mw_mile']], on=['t'], how='left').dropna()
        trans_om['op_trans'] = trans_om['MWmile'] * trans_om['trans_om_per_mw_mile'] / 2
        trans_om_r = trans_om.groupby(['t', 'r'], as_index=False)['op_trans'].sum()
        trans_om_r = interp_between_solve_years(trans_om_r, 'op_trans', modeled_years, non_modeled_years, first_year, last_year, r_list, 'r')
        dfall = dfall.merge(trans_om_r[['t', 'r', 'op_trans']], on=['t', 'r'], how='left')
        dfall['op_trans'] = dfall['op_trans'].fillna(0.0)
    else:
        # Non-nation aggregation: directly use trans_opex_per_mwh times retail load per BA
        dfall = dfall.merge((dist_admin_costs.set_index(['r', 't'])['trans_opex_per_mwh'] * dfall.set_index(['r', 't'])['retail_load']).rename('op_trans'), left_on=['r', 't'], right_index=True, how='left')

    # Calculate capital recovery streams
    unique_evals = df_capex['eval_period'].drop_duplicates()
    max_eval = np.max([unique_evals.max(), 100])
    plant_ages = pd.DataFrame(list(itertools.product(unique_evals, np.arange(0, max_eval, 1))), columns=['eval_period', 'plant_age'])
    plant_ages = plant_ages[plant_ages['plant_age'] < plant_ages['eval_period']]
    plant_ages['accounting_dep_f'] = 1.0 / plant_ages['eval_period']
    plant_ages['accounting_dep_f_cum'] = (plant_ages['plant_age'] + 1) / (plant_ages['eval_period'])

    df_capital_costs = df_capex.merge(plant_ages, on='eval_period', how='left').rename(columns={'t': 't_online'})
    df_capital_costs['t'] = df_capital_costs['t_online'] + df_capital_costs['plant_age']

    df_dep_years = df_capital_costs[['t', 't_online']].drop_duplicates(['t', 't_online']).reset_index(drop=True)
    for i in range(len(df_dep_years)):
        year = df_dep_years.loc[i, 't']
        base_year = df_dep_years.loc[i, 't_online']
        if year == base_year:
            df_dep_years.loc[i, 'dep_inflation_adj'] = 1
        else:
            df_dep_years.loc[i, 'dep_inflation_adj'] = (1.0 / np.array(np.cumprod(inflation.loc[base_year + 1:year]))[-1])
    df_capital_costs = df_capital_costs.merge(df_dep_years, on=['t', 't_online'], how='left')

    depreciation_schedules = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'depreciation_schedules.csv')).drop(columns='Schedule')
    for age in np.arange(len(depreciation_schedules), 100):
        depreciation_schedules.loc[age, :] = 0.0
    depreciation_schedules['plant_age'] = np.arange(0, 100)
    depreciation_schedules_cum = depreciation_schedules.copy()
    depreciation_schedules = depreciation_schedules.melt(id_vars='plant_age', var_name='depreciation_sch', value_name='tax_dep_f')
    depreciation_schedules['depreciation_sch'] = depreciation_schedules['depreciation_sch'].astype(str)
    df_capital_costs['depreciation_sch'] = df_capital_costs['depreciation_sch'].astype(str)
    df_capital_costs = df_capital_costs.merge(depreciation_schedules, on=['depreciation_sch', 'plant_age'], how='left')
    schedules = list(depreciation_schedules_cum.columns)
    schedules.remove('plant_age')
    depreciation_schedules_cum[schedules] = depreciation_schedules_cum[schedules].cumsum()
    depreciation_schedules_cum = depreciation_schedules_cum.melt(id_vars='plant_age', var_name='depreciation_sch', value_name='tax_dep_f_cum')
    df_capital_costs = df_capital_costs.merge(depreciation_schedules_cum, on=['depreciation_sch', 'plant_age'], how='left')
    df_capital_costs = df_capital_costs.merge(df_finance, on='t', how='left')

    df_capital_costs['capex_inf_adj'] = (df_capital_costs['capex'] * df_capital_costs['dep_inflation_adj'])
    df_capital_costs['dep_expense'] = (df_capital_costs['accounting_dep_f'] * df_capital_costs['capex_inf_adj'])
    df_capital_costs['dep_tax_value'] = (df_capital_costs['tax_dep_f'] * df_capital_costs['capex_inf_adj'])
    df_capital_costs['adit'] = np.clip((df_capital_costs['tax_dep_f_cum'] - df_capital_costs['accounting_dep_f_cum']) * df_capital_costs['capex_inf_adj'] * df_capital_costs['tax_rate'], 0.0, None)
    df_capital_costs['net_plant_in_service'] = (df_capital_costs['capex_inf_adj'] - df_capital_costs['accounting_dep_f_cum'] * df_capital_costs['capex_inf_adj'])
    df_capital_costs['plant_rate_base'] = (df_capital_costs['net_plant_in_service'] - df_capital_costs['adit'])
    df_capital_costs['debt_interest'] = (df_capital_costs['plant_rate_base'] * df_capital_costs['debt_fraction'] * df_capital_costs['debt_interest_nominal'])
    df_capital_costs['equity_return'] = (df_capital_costs['plant_rate_base'] * (1.0 - df_capital_costs['debt_fraction']) * df_capital_costs['equity_return_nominal'])
    df_capital_costs['return_to_capital'] = (df_capital_costs['debt_interest'] + df_capital_costs['equity_return'])
    df_capital_costs['income_tax'] = ((df_capital_costs['equity_return'] + df_capital_costs['dep_expense'] - df_capital_costs['dep_tax_value']) * (1.0 / (1.0 - df_capital_costs['tax_rate']) - 1.0))

    df_capital_costs_by_r = df_capital_costs.groupby(by=['t', 'region', 'cost_cat'], as_index=False)[['dep_expense', 'debt_interest', 'equity_return', 'income_tax']].sum()
    cap_cost_cats = list(df_capital_costs_by_r['cost_cat'].drop_duplicates())
    for cap_cost_cat in cap_cost_cats:
        df_cap_single = df_capital_costs_by_r[df_capital_costs_by_r['cost_cat'] == cap_cost_cat][['t', 'region', 'dep_expense', 'debt_interest', 'equity_return', 'income_tax']]
        dfall = dfall.merge(df_cap_single.rename(columns={'region': 'r', 'dep_expense': f'{cap_cost_cat}_dep_expense', 'debt_interest': f'{cap_cost_cat}_debt_interest', 'equity_return': f'{cap_cost_cat}_equity_return', 'income_tax': f'{cap_cost_cat}_income_tax'}), on=['t', 'r'], how='left')
        for suffix in ['dep_expense', 'debt_interest', 'equity_return', 'income_tax']:
            dfall[f'{cap_cost_cat}_{suffix}'] = dfall[f'{cap_cost_cat}_{suffix}'].fillna(0.0)


    # PTC values
    ptc_values = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'ptc_values.csv'))
    if 'ptc_tax_equity_penalty' in ptc_values:
        ptc_values['ptc_value'] *= (1 - ptc_values['ptc_tax_equity_penalty'])
        ptc_values['ptc_grossup_value'] *= (1 - ptc_values['ptc_tax_equity_penalty'])
    gdx_filename = os.path.join(run_dir, 'outputs', 'tc_phaseout_data', f'tc_phaseout_mult_{last_year}.gdx')
    tc_phaseout_mult = gdxpds.to_dataframes(gdx_filename)['tc_phaseout_mult_t']
    tc_phaseout_mult['t'] = tc_phaseout_mult['t'].astype(int)
    tc_phaseout_mult = tc_phaseout_mult.set_index('t').rename(columns={'Value': 'tc_phaseout_mult'})
    tc_phaseout_mult['tc_phaseout_mult'] = tc_phaseout_mult['tc_phaseout_mult'].astype(float)
    tc_phaseout_mult.reset_index(drop=False, inplace=True)
    ptc_values = ptc_values.merge(tc_phaseout_mult, on=['i', 't'], how='left')
    ptc_values['tc_phaseout_mult'] = ptc_values['tc_phaseout_mult'].fillna(1.0)
    ptc_values['ptc_value'] = ptc_values['ptc_value'] * ptc_values['tc_phaseout_mult']
    ptc_values['ptc_grossup_value'] = ptc_values['ptc_grossup_value'] * ptc_values['tc_phaseout_mult'] if 'tc_phaseout_mult' in ptc_values.columns else ptc_values['ptc_grossup_value']
    ptc_values_count = (ptc_values[['i', 'v', 'ptc_value']].groupby(['i', 'v'], as_index=False).count())
    ptc_values = ptc_values.merge(ptc_values_count.rename(columns={'ptc_value': 'count'}), on=['i', 'v'], how='left')
    ptc_values['ptc_value'] = ptc_values['ptc_value'] / ptc_values['count']
    ptc_values['ptc_grossup_value'] = ptc_values['ptc_grossup_value'] / ptc_values['count']
    ptc_values = ptc_values.rename(columns={'t': 't_start'})
    unique_durs = ptc_values['ptc_dur'].drop_duplicates()
    max_dur = ptc_values['ptc_dur'].max()
    ptc_dur_expander = pd.DataFrame(list(itertools.product(unique_durs, np.arange(0, max_dur, 1))), columns=['ptc_dur', 'ptc_year'])
    ptc_dur_expander = ptc_dur_expander[ptc_dur_expander['ptc_year'] < ptc_dur_expander['ptc_dur']]
    ptc_values = ptc_values.merge(ptc_dur_expander[['ptc_dur', 'ptc_year']], on='ptc_dur', how='left')
    ptc_values['t'] = ptc_values['t_start'] + ptc_values['ptc_year']
    ptc_values = ptc_values.merge(gen_ivrt, on=['i', 'v', 't'], how='left')
    ptc_values = ptc_values[~ptc_values['gen'].isnull()]
    ptc_values['ptc_credits'] = ptc_values['ptc_value'] * ptc_values['gen']
    ptc_values['ptc_grossup'] = ptc_values['ptc_grossup_value'] * ptc_values['gen']
    ptc_values_grouped = ptc_values.groupby(['t', 'r'], as_index=False)[['ptc_credits', 'ptc_grossup']].sum()
    ptc_values_grouped['ptc_grossup'] += ptc_values_grouped['ptc_credits']
    dfall = dfall.merge(ptc_values_grouped[['t', 'r', 'ptc_grossup']], on=['t', 'r'], how='left')
    dfall['ptc_grossup'] = dfall['ptc_grossup'].fillna(0.0)
    dfall['ptc_grossup'] = -dfall['ptc_grossup']

    # ITC values (generation and transmission)
    trans_itc = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'trans_itc_fractions.csv'))
    if len(trans_itc):
        trans_itc_value = (nongen_capex_distributed.loc[nongen_capex_distributed.i.isin(['inv_transmission_interzone_ac_investment', 'inv_transmission_interzone_dc_investment'])][['t', 'r', 'eval_period', 'capex']].rename(columns={'t': 't_online'}).merge(trans_itc, on='t', how='left'))
        trans_itc_value['tax_rate'] = trans_itc_value.t_online.map(df_finance.tax_rate)
        trans_itc_value['itc_base_value'] = (trans_itc_value['capex'] * trans_itc_value['itc_frac_monetized'])
        trans_itc_value.dropna(subset=['itc_frac'], inplace=True)
        itc_years = range(int(trans_itc_value.eval_period.unique()))
        trans_itc_value = (pd.concat({t: trans_itc_value for t in itc_years}, axis=0, names=['itc_year', 'drop']).reset_index(level=0).reset_index(drop=True))
        trans_itc_value['t'] = trans_itc_value['t_online'] + trans_itc_value['itc_year']
        df_dep_years_lookup = df_dep_years.dropna(subset=['t']).astype({'t': int}).set_index(['t', 't_online']).dep_inflation_adj
        trans_itc_value['dep_inflation_adj'] = trans_itc_value.apply(lambda row: df_dep_years_lookup[row.t, row.t_online], axis=1)
        trans_itc_value['itc_trans'] = -(trans_itc_value['itc_base_value'] / (1.0 - trans_itc_value['tax_rate']) / trans_itc_value['eval_period'] * trans_itc_value['dep_inflation_adj'])
    else:
        trans_itc_value = pd.DataFrame(columns=['t', 'r', 'itc_trans'])

    itc_df = pd.read_csv(os.path.join(run_dir, 'inputs_case', 'itc_fractions.csv'))
    if 'itc_tax_equity_penalty' in itc_df:
        itc_df['itc_frac'] *= (1 - itc_df['itc_tax_equity_penalty'])
    stacked_country_map = regions_map[['r', 'country']].drop_duplicates()
    stacked_country_map['country'] = stacked_country_map['country'].str.lower()
    itc_value_df = df_gen_capex[['i', 'region', 't', 'capex', 'eval_period']].copy().rename(columns={'region': 'r'})
    itc_value_df = itc_value_df.merge(stacked_country_map[['r', 'country']], on='r', how='left')
    itc_value_df = itc_value_df.merge(itc_df[['i', 'country', 't', 'itc_frac']], on=['i', 'country', 't'], how='inner')
    itc_value_df = itc_value_df.merge(df_finance[['tax_rate']], on='t', how='left')
    itc_value_df['itc_base_value'] = itc_value_df['capex'] * itc_value_df['itc_frac']
    itc_value_distributed = itc_value_df.rename(columns={'t': 't_online'})
    unique_durs = itc_value_distributed['eval_period'].drop_duplicates()
    max_dur = itc_value_distributed['eval_period'].max()
    itc_expander = pd.DataFrame(list(itertools.product(unique_durs, np.arange(0, max_dur, 1))), columns=['eval_period', 'itc_year'])
    itc_expander = itc_expander[itc_expander['itc_year'] < itc_expander['eval_period']]
    itc_value_distributed = itc_value_distributed.merge(itc_expander[['eval_period', 'itc_year']], on='eval_period', how='left')
    itc_value_distributed['t'] = itc_value_distributed[['t_online', 'itc_year']].sum(axis=1)
    itc_value_distributed = itc_value_distributed.merge(df_dep_years[['t', 't_online', 'dep_inflation_adj']], on=['t', 't_online'], how='left')
    itc_value_distributed['itc_normalized_value'] = -(itc_value_distributed['itc_base_value'] / (1.0 - itc_value_distributed['tax_rate']) / itc_value_distributed['eval_period'] * itc_value_distributed['dep_inflation_adj'])
    itc_value_grouped = itc_value_distributed.groupby(['t', 'r']).sum()['itc_normalized_value']
    dfall = (dfall.merge(itc_value_grouped, left_on=['t', 'r'], right_index=True, how='left').merge(trans_itc_value.groupby(['t', 'r'], as_index=False)['itc_trans'].sum().reindex(['t', 'r', 'itc_trans'], axis=1), on=['t', 'r'], how='left').fillna({'itc_normalized_value': 0, 'itc_trans': 0}))

    # Write outputs
    if write:
        outpath = os.path.join(run_dir, 'outputs', 'retail')
        os.makedirs(outpath, exist_ok=True)
        dfall.to_csv(os.path.join(outpath, 'regional_retail_rate_components.csv'), index=False)
        if verbose > 0:
            print(os.path.join(outpath, 'regional_retail_rate_components.csv'))
    return dfall


if __name__ == '__main__':
    mdir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description='run regional retail rate module')
    parser.add_argument('rundir', type=str, help="name of run directory (leave out 'runs' and directory separators)")
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()
    run_dir = os.path.join(mdir, os.pardir, os.pardir, 'runs', args.rundir)
    tic = datetime.datetime.now()
    log = reeds.log.makelog(scriptname=__file__, logpath=os.path.join(run_dir, 'gamslog.txt'))
    main(run_dir=run_dir, inputpath=os.path.join(mdir, 'inputs.csv'), write=True, verbose=args.verbose)
    reeds.log.toc(tic=tic, year=0, process='regional_retail_rate_calculations.py', path=run_dir)
    print('Finished regional_retail_rate_calculations.py')
