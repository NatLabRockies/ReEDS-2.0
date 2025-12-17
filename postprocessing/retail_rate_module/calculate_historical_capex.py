#### This file uses the capital costs and regional cost multipliers
#### from a given ReEDS run to calculate capital expenditures of
#### plants that were built through the start year of the run.

import gdxpds
import pandas as pd
import numpy as np
import sys
import argparse
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import reeds

def get_historical_units(inputs_case):
    # Read generator database and map units to the model regions for this run
    r_county = pd.read_csv(os.path.join(inputs_case, 'r_county.csv'))
    gendb = pd.read_csv(os.path.join(inputs_case, 'unitdata.csv'), low_memory=False)
    gendb = gendb.merge(r_county, left_on='FIPS', right_on='county', how='left')

    # Select units existing before or during the model start year
    sw = reeds.io.get_switches(inputs_case)
    startyear = int(sw['startyear'])
    init_cap = (
        gendb.loc[gendb['StartYear'] <= startyear]
        .rename(columns={
            'tech':'i',
            'r':'region',
            'summer_power_capacity_MW':'cap_new',
            'StartYear':'t'
        })
    )

    # Rename techs for consistency with capital cost data from inputs.gdx
    tech_name_map = {
        'coal-igcc': 'Coal-IGCC',
        'coaloldscr': 'CoalOldScr',
        'coalolduns': 'CoalOldUns',
        'csp-ns': 'csp1_1',
        'dupv': 'upv_1',
        'gas-cc': 'Gas-CC',
        'gas-ct': 'Gas-CT',
        'geohydro_allkm': 'geohydro_allkm_1',
        'hydED': 'hydND',
        'hydEND': 'hydND',
        'nuclear': 'Nuclear',
        'pvb': 'upv_1',
        'upv': 'upv_1',
        'wind-ons': 'wind-ons_1'
    }
    init_cap['i'] = init_cap['i'].replace(tech_name_map)

    return init_cap

def get_earliest_cap_costs(inputs_case):
    # Read national capital costs and get
    # the earliest values for each tech
    cost_cap = gdxpds.to_dataframe(
        os.path.join(inputs_case, 'inputs.gdx'),
        'cost_cap',
        old_interface=False
    )
    cost_cap_energy = gdxpds.to_dataframe(
        os.path.join(inputs_case, 'inputs.gdx'),
        'cost_cap_energy',
        old_interface=False
    )
    cost_cap = (
        pd.concat([cost_cap, cost_cap_energy])
        .groupby(['i', 't'], as_index=False)
        .sum()
    )
    cost_cap['t'] = cost_cap['t'].astype(int)
    cost_cap = cost_cap.rename(columns={'Value': 'cost_cap'})
    cost_cap_earliest = (
        cost_cap.sort_values('t', ascending=True)
        .drop_duplicates('i', keep='first')
        .drop(columns='t')
    )

    # Read regional capital cost multipliers and
    # get the earliest values for each tech and region
    cost_cap_mult = gdxpds.to_dataframe(
        os.path.join(inputs_case, 'inputs.gdx'),
        'cost_cap_fin_mult_out',
        old_interface=False
    )
    cost_cap_mult['t'] = cost_cap_mult['t'].astype(int)
    cost_cap_mult = cost_cap_mult.rename(
        columns={'Value': 'cap_cost_mult_for_ratebase'}
    )
    cost_cap_mult_earliest = (
        cost_cap_mult.sort_values('t', ascending=True)
        .drop_duplicates(['i', 'r'], keep='first')
        .drop(columns='t')
    )
    cost_cap_mult_earliest['i'] = cost_cap_mult_earliest['i'].replace(
        {'CoalOldUns_CoalOldScr': 'CoalOldUns'}
    )

    # Combine capital costs and multipliers
    cost_cap_earliest_with_mult = (
        cost_cap_earliest.merge(cost_cap_mult_earliest, on='i', how='left')
        .assign(cost_cap=lambda x: x['cost_cap'] * x['cap_cost_mult_for_ratebase'])
        .dropna(subset='cost_cap')
        [['i', 'r', 'cost_cap']]
    )

    # Read capital costs for technologies whose capital costs
    # are included in their supply curves and attach them
    # to the dataframe of all capital costs
    rsc_dat = gdxpds.to_dataframe(
        os.path.join(inputs_case, 'inputs.gdx'),
        'rsc_dat',
        old_interface=False
    )
    cost_cap_rsc = (
        rsc_dat.loc[~rsc_dat.i.isin(cost_cap_earliest['i'])]
        .pivot_table(
            values='sc_cat',
            columns='sc_cat',
            index=['r', 'i', 'rscbin']
        )
        .reset_index()
        .fillna(0.0)
    )
    cost_cap_rsc['cost_cap'] = (
        cost_cap_rsc['cost'] / cost_cap_rsc['cap'].replace(0, np.nan)
    )
    cost_cap_rsc = (
        cost_cap_rsc.sort_values('cost_cap', ascending=True)
        .drop_duplicates(subset=['r', 'i'], keep='first')
        .dropna(subset='cost_cap')
        [['r', 'i', 'cost_cap']]
    )

    cost_cap_earliest_regional = (
        pd.concat([cost_cap_earliest_with_mult, cost_cap_rsc], ignore_index=True)
        .rename(columns={'r': 'region'})
    )

    # To fill in capital costs for tech/region pairs where we
    # don't have regional data, use the national cost
    # (i.e., no multipliers applied) for the tech or the
    # average of all of the regional costs for the tech.
    cost_cap_earliest_national = (
        pd.concat([
            cost_cap_earliest,
            cost_cap_earliest_regional.groupby('i', as_index=False).mean(numeric_only=True)
        ])
        .drop_duplicates('i', keep='first')
    )

    return cost_cap_earliest_regional, cost_cap_earliest_national


def main(run_dir):
    print("Calculating historical capital costs...")
    inputs_case = os.path.join(run_dir, 'inputs_case')
    init_cap = get_historical_units(inputs_case)
    cost_cap_earliest_regional, cost_cap_earliest_national = get_earliest_cap_costs(inputs_case)

    # Combine historical units with their corresponding capital cost estimates,
    # using regional costs where possible and filling in missing data with
    # national costs for the given tech
    init_capex = (
        init_cap.merge(cost_cap_earliest_regional, on=['i', 'region'], how='left')
        .merge(cost_cap_earliest_national, on='i', how='left')
        .assign(cost_cap=lambda x: x['cost_cap_x'].fillna(x['cost_cap_y']))
        .drop(columns=['cost_cap_x', 'cost_cap_y'])
    )
    no_capex_techs = init_capex.loc[init_capex.cost_cap.isna(), 'i'].unique().tolist()
    if len(no_capex_techs) > 0:
        raise ValueError(
            'The following technologies have no associated capital costs. You may '
            'need to update the `tech_name_map` dictionary in the `get_historical_units` '
            'function so that the historical unit technology names match those of the '
            'capital cost data from inputs.gdx:\n{}\n'
            .format('\n'.join(no_capex_techs))
        )

    # Calculate the capital expenditures associated with each capacity addition
    # and calculate the total capital expenditures for each tech/region/year
    init_capex['capex'] = init_capex['cost_cap'] * init_capex['cap_new']
    init_capex = (
        init_capex.groupby(['i', 'region', 't'], as_index=False)
        .sum()
        [['i', 'region', 't', 'cap_new', 'capex']]
    )

    out_fpath = os.path.join(run_dir, "inputs_case", "df_capex_init.csv")
    init_capex.round(4).to_csv(out_fpath, index=False)
    
    print(f"Finished calculate_historical_capex.py. See {out_fpath} for output.")
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Calculate capital costs for historical (pre-start year) units"
    )
    parser.add_argument(
        'rundir',
        type=str,
        help="name of run directory (leave out 'runs' and directory separators)"
    )
    
    args = parser.parse_args()
    
    thispath = os.path.dirname(os.path.realpath(__file__))
    run_dir = os.path.join(thispath, os.pardir, os.pardir, 'runs', args.rundir)
    
    main(run_dir)
