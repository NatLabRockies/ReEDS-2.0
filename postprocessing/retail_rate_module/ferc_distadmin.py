# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:14:07 2020

@author: pgagnon
"""
###########
#%% IMPORTS

import pandas as pd
import numpy as np
import os


#################
#%% SHARED INPUTS

### Specify the column to subtract and the parent column to subtract it from
excludecells = {
    ###### ('utility name', year): {'col to subtract': 'parent col'}
    ### Wildfire lawsuit exclusions
    ('Pacific Gas & Electric Co', 2018): {
        'A&G Oper Injuries & Damages $': 'Total Admin & General Expenses $'},
    ('Pacific Gas & Electric Co', 2019): {
        'A&G Oper Injuries & Damages $': 'Total Admin & General Expenses $'},
    ('Southern California Edison Co', 2018): {
        'A&G Oper Injuries & Damages $': 'Total Admin & General Expenses $'},
    ('Southern California Edison Co', 2019): {
        'A&G Oper Injuries & Damages $': 'Total Admin & General Expenses $'},
    ### (Additional special exclusions can be added here)
}

### Specify the state-to-region mapping to use for regional projections
### None of the region breakdowns in hierarchy.csv are completely aligned with state borders.
### So do census divisions by hand from Figure 36 in ReEDS version 2019 documentation
### (https://www.nrel.gov/docs/fy20osti/74111.pdf)
# state2region = {
#     'WA': 'Pacific',
#     'OR': 'Pacific',
#     'CA': 'Pacific',
#     'AK': 'Pacific',
#     'HI': 'Pacific',
#     'MT': 'Mountain',
#     'ID': 'Mountain',
#     'WY': 'Mountain',
#     'NV': 'Mountain',
#     'UT': 'Mountain',
#     'CO': 'Mountain',
#     'AZ': 'Mountain',
#     'NM': 'Mountain',
#     'ND': 'West North Central',
#     'MN': 'West North Central',
#     'SD': 'West North Central',
#     'NE': 'West North Central',
#     'IA': 'West North Central',
#     'KS': 'West North Central',
#     'MO': 'West North Central',
#     'OK': 'West South Central',
#     'AR': 'West South Central',
#     'TX': 'West South Central',
#     'LA': 'West South Central',
#     'WI': 'East North Central',
#     'MI': 'East North Central',
#     'IL': 'East North Central',
#     'IN': 'East North Central',
#     'OH': 'East North Central',
#     'KY': 'East South Central',
#     'TN': 'East South Central',
#     'MS': 'East South Central',
#     'AL': 'East South Central',
#     'VT': 'New England',
#     'NH': 'New England',
#     'ME': 'New England',
#     'MA': 'New England',
#     'CT': 'New England',
#     'RI': 'New England',
#     'NY': 'Middle Atlantic',
#     'PA': 'Middle Atlantic',
#     'NJ': 'Middle Atlantic',
#     'MD': 'South Atlantic',
#     'DE': 'South Atlantic',
#     'DC': 'South Atlantic',
#     'WV': 'South Atlantic',
#     'VA': 'South Atlantic',
#     'NC': 'South Atlantic',
#     'SC': 'South Atlantic',
#     'GA': 'South Atlantic',
#     'FL': 'South Atlantic',
# }
### Approximate ISOs from ISO and FERC maps.
state2region = {
    'WA': 'BPA',
    'OR': 'BPA',
    'ID': 'BPA',
    'CA': 'CAISO',
    'AK': 'Pacific',
    'HI': 'Pacific',
    'MT': 'Mountain',
    'WY': 'Mountain',
    'UT': 'Mountain',
    'CO': 'Mountain',
    'NV': 'Mountain', # 'Southwest',
    'AZ': 'Mountain', # 'Southwest',
    'NM': 'Mountain', # 'Southwest',
    'NE': 'SPP',
    'KS': 'SPP',
    'OK': 'SPP',
    'TX': 'ERCOT',
    'SD': 'MISO-N',
    'ND': 'MISO-N',
    'IA': 'MISO-N',
    'MN': 'MISO-N',
    'MO': 'MISO-N',
    'WI': 'MISO-N',
    'MI': 'MISO-N',
    'IL': 'MISO-N',
    'IN': 'MISO-N',
    'AR': 'MISO-S',
    'LA': 'MISO-S',
    'MS': 'MISO-S',
    'KY': 'PJM',
    'OH': 'PJM',
    'PA': 'PJM',
    'NJ': 'PJM',
    'MD': 'PJM',
    'DE': 'PJM',
    'DC': 'PJM',
    'WV': 'PJM',
    'VA': 'PJM',
    'TN': 'Southeast',
    'AL': 'Southeast',
    'NC': 'Southeast',
    'SC': 'Southeast',
    'GA': 'Southeast',
    'FL': 'Southeast',
    'NY': 'NYISO',
    'VT': 'ISONE',
    'NH': 'ISONE',
    'ME': 'ISONE',
    'MA': 'ISONE',
    'CT': 'ISONE',
    'RI': 'ISONE',
}

### Fill missing states based on utility name
missingstates = {
    'CalPeco LLC': 'CA',
    'New York Transco LLC': 'NY',
    'Pioneer Transmission LLC': 'IN',
    'Prairie Wind Transmission LLC': 'KS',
}

#%% Sub-functions
def get_inflatable(inflationpath=None):
    """
    Get an [inyear,outyear] lookup table for inflation
    """
    inflation = pd.read_csv(inflationpath, index_col='t')
    ### Make the single-pair function
    def inflatifier(inyear, outyear=2019, inflation=inflation):
        if inyear < outyear:
            return inflation.loc[inyear+1:outyear,'inflation_rate'].cumprod()[outyear]
        elif inyear > outyear:
            return 1 / inflation.loc[outyear+1:inyear,'inflation_rate'].cumprod()[inyear]
        else:
            return 1
    ### Make the output table
    inflatable = {}
    for inyear in range(1960,2051):
        for outyear in range(1960,2051):
            inflatable[inyear,outyear] = inflatifier(inyear,outyear)
    inflatable = pd.Series(inflatable)
    return inflatable

def get_excluded_costs(excludecells=excludecells, inflationpath=None, dollar_year=2004):
    """
    Get subtracted cells so we can add them back in with special treatment.
    Returns monetary values in dollar_year dollars.
    """
    #%% Get module directory for relative paths
    mdir = os.path.dirname(os.path.abspath(__file__))

    #%% Get inflation table
    inflatable = get_inflatable(inflationpath)

    #%% Load FERC input data
    df_opex = pd.read_csv(
        os.path.join(mdir, 'inputs', 'Electric O & M Expenses-IOU-1993-2019.csv'),
        encoding='latin1')

    #%% Loop over the excluded cells and save them
    out = []
    for (utility, year) in excludecells:
        outcols = list(excludecells[utility,year].keys())
        out.append(df_opex.loc[
            (df_opex['Utility Name']==utility) & (df_opex['Year']==year),
            ['Utility Name', 'Year', 'State',] + outcols
        ])
    dfout = pd.concat(out, axis=0)

    #%% Inflate values to dollar_year
    for col in outcols:
        dfout[col] = dfout.apply(lambda row: inflatable[row.Year, dollar_year] * row[col], axis=1)

    return dfout


#%% Main functionality
def get_ferc_costs(
    numslopeyears=10, numprojyears=10, current_t=2020, aggregation='nation', writeout='csv',
    inflationpath=None, drop_pgesce_20182019=True, excludecells=excludecells,
    dollar_year=2004, cleanup=True):
    """
    Parameters
    ------
    numslopeyears : int
        Number of years to use to determine slope for projection of future D&A costs
        (default = 10)
    numprojyears : int
        Number of years until future D&A costs level out (default = 10)
    current_t : int
        Cutoff between historical and projected years (default = 20)
    aggregation: str in ['nation','state','census']
        Indicate whether to group D/A/T costs by nation, state, or census division
    writeout : str or False
        Indicate whether to write results as csv or pickle (default = csv), or enter False
        to skip writing of results
    inflationpath : str
        Filepath to ReEDS-2.0/runs/{casename}/inputs_case/inflation.csv
        (required)
    drop_pgesce_20182019 : bool
        Indicate whether to drop 2018 and 2019 values for 'A&G Oper Injuries & Damages $'
        for PG&E and SCE. The entries are outliers, so default is True.
    cleanup : bool
        Specify whether to overwrite energy sales for three utilities (Central Maine Power Co,
        Dixie Escalante Rural Electric Association Inc, Salmon River Electric Coop Inc)
        with values from EIA Form 861. Should be left True.

    Returns
    -------
    dfout : pd.DataFrame
        Historical and projected future distribution & administration costs
    """
    # #%%##### DEBUG
    # numslopeyears = 10
    # numprojyears = 10
    # current_t = 2020
    # aggregation = 'state'
    # writeout = False
    # inflationpath = os.path.join(
    #     os.path.expanduser('~/Projects/Retail/ReEDS-2.0/runs/v20200824_retail100_Ref/'),
    #     'inputs_case', 'inflation.csv')
    # drop_pgesce_20182019 = True
    # dollar_year = 2004
    # cleanup = True

    #%% Clean up inputs
    if aggregation not in ['nation','state','region']:
        raise Exception("aggregation must be in ['nation','state','region']")

    #%% Get module directory for relative paths
    mdir = os.path.dirname(os.path.abspath(__file__))

    #%% Load FERC input data
    df_opex = pd.read_csv(
        os.path.join(mdir, 'inputs', 'Electric O & M Expenses-IOU-1993-2019.csv'),
        encoding='latin1')
    df_capex = pd.read_csv(
        os.path.join(mdir, 'inputs', 'Electric Plant in Service-IOU-1993-2019.csv'),
        encoding='latin1')
    df_sales = pd.read_csv(
        os.path.join(mdir, 'inputs', 'Electric Operating Revenues-IOU-1993-2019.csv'),
        encoding='latin1')

    #%% Mangle the PG&E and SCE data for 2018/2019
    ### These costs are from wildfire lawsuits and aren't immediately passed through to
    ### ratepayers, so we exclude them from the fitted admin rates and then add them
    ### back in retail_rate_calculations.py using get_excluded_costs() and
    ### special amortization assumptions.
    if drop_pgesce_20182019 == True:
        ### Loop over the exclusions and subtract them
        for (utility, year) in excludecells:
            ### Get the row number to modify and make sure it's unique
            rows = df_opex.loc[(df_opex['Utility Name']==utility) & (df_opex['Year']==year)].index
            if len(rows) > 1:
                raise Exception('Non-unique (utility, year) in excludecells')
            row = rows[0]
            ### Loop over the child:parent pairs and subtract child from parent
            for child in excludecells[utility,year]:
                parent = excludecells[utility,year][child]
                df_opex.loc[row,parent] -= df_opex.loc[row,child]

    #%% Remove unnecessary columns and merge
    df_opex.drop(
        df_opex.columns.difference([
            'Year', 'Utility Name', 'State',
            'Trn Total Operation Expenses $',
            'Trn Total Maintenance Expenses $',
            'Dis Total Maintenance Expenses $',
            'Dis Total Operation Expenses $',
            'Total Sales Expenses $',
            'Total Customer Srv & Information Expenses $',
            'CAE Total Customer Accounts Expenses $',
            'Total Admin & General Expenses $',
            'Total Regional Trans & Mark Operation Exps  $',
            'A&G Total Operation Expenses $',
        ]), 1, inplace=True)

    df_capex = df_capex[df_capex['Account Classification'] == 'Additions']
    df_capex.drop(
        df_capex.columns.difference([
            'Year', 'Utility Name', 'State',
            'Trn - Total Transmission Plant',
            'Dis - Total Distribution Plant',
            'Gen - Total General Plant',
        ]), 1, inplace=True)

    df_sales.drop(
        df_sales.columns.difference([
            'Year', 'Utility Name', 'State',
            'Total Retail Sales MWh',
            'Total Electricity Customers'
        ]), 1, inplace=True)

    dfall = df_capex.merge(df_opex, on=[ 'Year', 'Utility Name', 'State'], how='outer')
    dfall = dfall.merge(df_sales, on=[ 'Year', 'Utility Name', 'State'], how='outer')

    #%%  calculate an adjustment factor to get the nominal $ inputs into stated dollar years (2004)
    dfall.rename(columns={'Year':'t'}, inplace=True)
    dfall.rename(columns={
        'Trn - Total Transmission Plant':  'Trn - Total Transmission Plant $',
        'Dis - Total Distribution Plant' : 'Dis - Total Distribution Plant $' ,
        'Gen - Total General Plant':       'Gen - Total General Plant $'}, inplace=True)
    dfall.rename(columns={
        'Total Retail Sales MWh':'energy_sales',
        'Total Electricity Customers':'cust'}, inplace=True)

    inflation = pd.read_csv(inflationpath)
    inflation = inflation.set_index('t')
    inflation['inflation_adj'] = 1.0
    for input_dollar_year in inflation.index:
        if input_dollar_year < dollar_year:
            inflation.loc[input_dollar_year, 'inflation_adj'] = np.array(
                np.cumprod(inflation.loc[input_dollar_year+1:dollar_year,'inflation_rate'])
            )[-1]
        elif input_dollar_year > dollar_year:
            inflation.loc[input_dollar_year, 'inflation_adj'] = (
                1.0 / np.array(np.cumprod(
                    inflation.loc[dollar_year+1:input_dollar_year,'inflation_rate']
                ))[-1])

    inflation = inflation.reset_index()
    dfall = dfall.merge(inflation[['t', 'inflation_adj']], on='t')

    #%% apply inlfation adjustemnt to any column that has a $ in its name
    dollar_cols = [col for col in dfall.columns if '$' in col]
    for dollar_col in dollar_cols:
        dfall[dollar_col] = dfall[dollar_col] * dfall['inflation_adj']

    dfall = dfall.drop(columns='inflation_adj')

    #%% Consolidate costs in dfall and remove 1993 due to low number of entries
    dfall['trans_opex'] = dfall[[
        'Trn Total Operation Expenses $',
        'Trn Total Maintenance Expenses $'
    ]].sum(axis=1)
    dfall['dist_opex'] = dfall[[
        'Dis Total Operation Expenses $',
        'Dis Total Maintenance Expenses $'
    ]].sum(axis=1)
    dfall['admin_opex'] = dfall[[
        'Total Admin & General Expenses $', # 'A&G Total Operation Expenses $',
        'Total Sales Expenses $',
        'Total Customer Srv & Information Expenses $',
        'CAE Total Customer Accounts Expenses $',
        'Total Regional Trans & Mark Operation Exps  $',
    ]].sum(axis=1)
    dfall['trans_capex'] = dfall['Trn - Total Transmission Plant $']
    dfall['dist_capex']  = dfall['Dis - Total Distribution Plant $']
    dfall['admin_capex']  = dfall['Gen - Total General Plant $']

    #%% Apply the optional cleanup steps to overwrite energy sales with values from EIA form 861
    if cleanup:
        ### Index on (utility name, t)
        dfall.set_index(['Utility Name','t'], inplace=True)
        ### Load the overwrite values
        overwrite = (
            pd.read_csv(os.path.join(mdir,'inputs','overwrite-utility-energy_sales.csv'))
            .rename(columns={'utility_name':'Utility Name', 'year':'t'})
            .set_index(['Utility Name','t'])
        )
        dfreplace = dfall.merge(
            overwrite, left_index=True, right_index=True, how='inner',
            suffixes=('_old','_new'))['energy_sales_new']
        dfall.loc[dfreplace.index, 'energy_sales'] = dfreplace
        ### Back to previous index
        dfall.reset_index(inplace=True)

    #%% Create output dataframes with different levels of aggregation
    dfall.rename(columns={'State':'state'}, inplace=True)
    keepcols = [
        't', 'state', 'region', 'nation',
        'energy_sales', 'cust',
        'dist_opex', 'dist_capex',
        'admin_opex', 'admin_capex',
        'trans_opex', 'trans_capex',
    ]
    ### Drop AK, HI, and 1993
    dfall = dfall.drop(dfall.loc[
        (dfall.t == 1993) | (dfall.state.isin(['AK','HI']))
    ].index).reset_index(drop=True)
    ### Assign DC to MD (since that's how ReEDS treats it)
    dfall.state.replace({'DC':'MD'}, inplace=True)
    ### Fill missing states
    dfall.state = dfall.apply(lambda row: missingstates.get(row['Utility Name'],row.state), axis=1)
    ### Add a column for region
    dfall['region'] = dfall.state.map(state2region)
    dfall['nation'] = 'USA'
    ### Aggregate at different scales
    zones = dfall[aggregation].unique().tolist()
    ### Make the output dataframe
    dfout = dfall[keepcols].groupby(['t',aggregation], as_index=False).sum()
    ### Number of years to project forward
    extend = {zone: 2050 - dfout.loc[dfout[aggregation]==zone,'t'].max() for zone in zones}

    #%% calculate normalized costs on a per-MWh and per-customer basis
    values = ['dist_opex', 'admin_opex', 'trans_opex', 'dist_capex', 'admin_capex', 'trans_capex']
    for val in values:
        # dfout['%s_per_cust' % val] = dfout[val] / dfout['cust']
        dfout['%s_per_mwh' % val] =  dfout[val] / dfout['energy_sales']

    #%% Interpolate missing values: UT is missing 1994,1995,1996
    if aggregation == 'state':
        dfout.drop(dfout.loc[(dfout.state=='UT')&(dfout.t==1996)].index, inplace=True)
        insert = pd.DataFrame(
            {'t':[1994,1995,1996],
            'state':['UT','UT','UT'],
            'entry_type':['backfilled','backfilled','backfilled']})
        dfout = dfout.append(insert).sort_values(['state','t']).reset_index(drop=True)
        dfout.loc[(dfout.state=='UT')] = dfout.loc[dfout.state=='UT'].interpolate('bfill')
        # dfout.loc[(dfout.state=='MT')] = dfout.loc[dfout.state=='MT'].interpolate('linear')

    #%% Shared parameters for projection
    dropcols = [
        # 'energy_sales',
        'cust',
        'dist_opex', 'dist_capex',
        'admin_opex', 'admin_capex',
        'trans_opex',
        # 'trans_capex',
    ]
    dfout.drop(dropcols, axis=1, inplace=True)

    values_normalized = [
        # 'dist_opex_per_cust',
        # 'admin_opex_per_cust',
        # 'trans_opex_per_cust',
        # 'dist_capex_per_cust',
        # 'admin_capex_per_cust',
        # 'trans_capex_per_cust',
        'dist_opex_per_mwh',
        'admin_opex_per_mwh',
        'trans_opex_per_mwh',
        'dist_capex_per_mwh',
        'admin_capex_per_mwh',
        'trans_capex_per_mwh'
    ]

    #%% generate dataframe for future years and create 'index' dummy variable
    ### to set up diminishing trend
    for zone in zones:
        df_loop = dfout[dfout[aggregation] == zone]
        df_extrapolate_dim = pd.DataFrame(index=np.arange(extend[zone]))
        df_extrapolate_dim[aggregation] = zone
        df_extrapolate_dim['index'] = np.arange(len(df_extrapolate_dim))
        df_extrapolate_dim['t'] = df_extrapolate_dim['index'] + df_loop['t'].max() + 1

        df_extrapolate_dim['index'] = numprojyears - df_extrapolate_dim['index']
        df_extrapolate_dim['index'].values[df_extrapolate_dim['index'].values < 0] = 0

        #list the years of historical data used for extrapolation
        slopeyears = np.array(df_loop['t'].tail(numslopeyears))

        #project data forward
        for value in values_normalized:
            if numprojyears == 0:
                df_extrapolate_dim[value] = df_loop[value].iloc[-1]
            else:
                slopevalues = np.array(df_loop[value].tail(numslopeyears))
                trend = np.polyfit(x=slopeyears, y=slopevalues, deg=1)
                df_extrapolate_dim.loc[0, value] = (
                    trend[0] * df_extrapolate_dim.loc[0, 't'] + trend[1])
                for i in range(1, len(df_extrapolate_dim)):
                    df_extrapolate_dim.loc[i, value] = (
                        df_extrapolate_dim.loc[i-1, value]
                        + trend[0] * (df_extrapolate_dim.loc[i, 'index'] / numprojyears))

        #drop absolute columns that were not extrapolated
        df_extrapolate_dim = df_extrapolate_dim.drop(['index'], axis=1)

        #append projected data to historical data
        dfout = dfout.append(df_extrapolate_dim, sort=False)

    #Assign rows as historical or projected
    dfout.loc[dfout['t'] < current_t, 'entry_type'] = 'historical'
    dfout.loc[dfout['t'] >= current_t, 'entry_type'] = 'projected'
    # dfout = dfout[~dfout.isin([np.nan, np.inf, -np.inf]).any(1)]

    #%% Write outputs
    dfout.reset_index(drop=True, inplace=True)
    if writeout in ['.csv','csv','CSV']:
        dfout.to_csv('dist_admin_costs_{}.csv'.format(aggregation), index=False)
    elif writeout in ['.p','p','.pkl','pkl','pickle']:
        dfout.to_pickle('dist_admin_costs_{}.pkl'.format(aggregation), index=False)
    else:
        pass

    return dfout


#%% If run on its own, create some plots
if __name__ == '__main__':
    ### Extra imports
    import argparse
    import os
    import matplotlib.pyplot as plt
    plot = False

    ### Get inputs
    parser = argparse.ArgumentParser(description="write historical and projected future D&A costs")
    parser.add_argument('-s', '--numslopeyears', type=int, default=10,
                        help='number of yeras to use to determine slope')
    parser.add_argument('-p', '--numprojyears', type=int, default=10,
                        help='number of years until future D&A costs level out')
    parser.add_argument('-w', '--writeout', type=str, default='csv',
                        help='indicate whether to write as pickle or csv')
    parser.add_argument('-i', '--inflationpath', type=str, help='path to inflation.csv')
    parser.add_argument('-a', '--aggregation', type=str, choices=['nation','state','region'],
                        default='nation', help='level at which to aggregate FERC data')
    parser.add_argument('-c', '--cleanup', action='store_true', help='apply utility cleanup steps')

    args = parser.parse_args()
    numslopeyears = args.numslopeyears
    numprojyears = args.numprojyears
    writeout = args.writeout
    inflationpath = args.inflationpath
    aggregation = args.aggregation
    cleanup = args.cleanup

    ### National
    dfout = get_ferc_costs(
        numslopeyears=numslopeyears, numprojyears=numprojyears,
        aggregation=aggregation, inflationpath=inflationpath, writeout=writeout,
        cleanup=cleanup)

    ### Plot it
    #%% Stacked Trend plots per MWh Diminished (national)
    if plot:
        plt.style.use('ggplot')
        years = list(dfout.sort_values('t')['t'].drop_duplicates())
        plt.close()
        fig = plt.stackplot(
            years, dfout['admin_opex_per_mwh'], dfout['admin_capex_per_mwh'],
            dfout['dist_opex_per_mwh'], dfout['dist_capex_per_mwh'],
            labels=['Administration Opex','Administration CapEx',
                    'Distribution Opex','Distribution Capex'])
        plt.legend(bbox_to_anchor=(1.5, 0.75))
        plt.ylabel("Dollars ($)/MWh", size = 14)
        plt.xlabel("Years", size = 14)
        plt.title("National D&A", size = 14)
        plt.grid(zorder = 10)
        plt.savefig(
            os.path.join(
                'figures',
                'dist_admin_stacked_mwh_ABB_{}slope_{}proj.jpeg'.format(numprojyears, numslopeyears)),
            bbox_inches='tight', dpi=150)
        plt.show()

        #%% Stacked Trend plots per MWh Diminished (single state)
        ### Single state (CA)
        dfout_state = get_ferc_costs(
            numslopeyears=numslopeyears, numprojyears=numprojyears,
            aggregation='state', writeout=writeout)
        test_state = 'CA'
        df_state_test = dfout_state[dfout_state['state'] == test_state]
        years = list(df_state_test.sort_values('t')['t'].drop_duplicates())
        plt.close()
        fig = plt.stackplot(
            years, df_state_test['admin_opex_per_mwh'], df_state_test['admin_capex_per_mwh'],
            df_state_test['dist_opex_per_mwh'], df_state_test['dist_capex_per_mwh'],
            labels=['Administration Opex','Administration CapEx',
                    'Distribution Opex','Distribution Capex'])
        plt.legend(bbox_to_anchor=(1.5, 0.75))
        plt.ylabel("Dollars ($/MWh)", size = 14)
        plt.xlabel("Years", size = 14)
        plt.xlabel("Years", size = 14)
        plt.title(test_state + " D&A", size = 14)
        plt.grid(zorder = 10)
        plt.savefig(
            os.path.join('figures', 'dist_admin_stacked_mwh_ABB_{}slope_{}proj_{}.jpeg'.format(
                numprojyears, numslopeyears, test_state)),
            bbox_inches='tight', dpi=150)
        plt.show()
