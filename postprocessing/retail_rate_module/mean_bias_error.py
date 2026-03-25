"""
Main contact: Patrick.Brown@nrel.gov
This script calculates the mean bias error between the bottom-up retail rates
and reported state-level retail rates from EIA form 861 and writes the results
to ReEDS-2.0/postprocessing/retail_rate_module/inputs/state-meanbiaserror_rate-aggregation.csv.
The results are written in ¢/kWh in {out_dollar_year} dollars.
"""

###############
#%% Imports ###
import numpy as np
import pandas as pd
import os, sys, math, site
import io
import argparse

pd.options.display.max_columns = 200
pd.options.display.max_rows = 50


#######################
#%% Argument inputs ###
parser = argparse.ArgumentParser(description="Calculate retail rate bias errors")
parser.add_argument('-b', '--reeds_path', help='ReEDS directory')
parser.add_argument('-r', '--run_dir', help='ReEDS run directory')
parser.add_argument('-y', '--out_dollar_year', type=int, default=2019,
                    help='Dollar year in which to write results')

args = parser.parse_args()
reeds_path = args.reeds_path
run_dir = args.run_dir
out_dollar_year = args.out_dollar_year

# #%% Testing
# reeds_path = os.path.expanduser('~/github2/ReEDS-2.0/')
# run_dir = os.path.join(reeds_path,'runs','v20210716_main_Ref_2026')
# out_dollar_year = 2019

#%% Set up logger
site.addsitedir(os.path.join(reeds_path,'input_processing'))
from ticker import makelog
log = makelog(scriptname=__file__, logpath=os.path.join(run_dir,'gamslog.txt'))

##############
#%% Inputs ###

validationyears = list(range(2010,2020))
data_dollar_year = 2004

retailmodulepath = os.path.join(reeds_path,'postprocessing','retail_rate_module','')
inputs_default_path = retailmodulepath+'inputs_default.csv'

inflation = pd.read_csv(
    os.path.join(reeds_path,'inputs','financials','inflation_default.csv'),
    index_col=['t'])
inf_adjust = inflation.loc[
    data_dollar_year+1:out_dollar_year,
    'inflation_rate'
].cumprod()[out_dollar_year]

### Import the retail rate module
site.addsitedir(retailmodulepath)
import retail_rate_calculations


#################
#%% Functions ###

def getrate_state(retail_results, inf_adjust=inf_adjust):
    dfin = (
        retail_results
        .drop(['busbar_load','end_use_load'],axis=1)
        .set_index(['state','t'])
    )
    for col in dfin.columns:
        if col not in ['t','state','retail_load']:
            dfin[col] = dfin[col] * inf_adjust / dfin['retail_load'] / 10
    dfout = dfin.drop('retail_load', axis=1).sum(axis=1)
    return dfout

def getrevenue_state(retail_results, units='billions', inf_adjust=inf_adjust):
    if units in ['billion','billions','b','B','10**9','1E9','1e9',1E9,9]:
        unitifier = 1E9
    elif units in ['million','millions','m','M','10**6','1E6','1e6',1E6,6]:
        unitifier = 1E6
    dfin = (
        retail_results
        .drop(['busbar_load','end_use_load','retail_load'],axis=1)
        .set_index(['state','t'])
    )
    for col in dfin.columns:
        if col not in ['t','state','retail_load']:
            dfin[col] = dfin[col] * inf_adjust / unitifier
    dfout = dfin.sum(axis=1)
    return dfout

def getrate_usa(retail_results, inf_adjust=inf_adjust):
    dfin = (
        retail_results
        .drop(['state','busbar_load','end_use_load'],axis=1)
        .groupby('t').sum()
    )
    for col in dfin.columns:
        if col not in ['t','state','retail_load']:
            dfin[col] = dfin[col] * inf_adjust / dfin['retail_load'] / 10
    dfout = dfin.drop('retail_load', axis=1).sum(axis=1)
    return dfout

def getrevenue_usa(retail_results, units='billions', inf_adjust=inf_adjust):
    if units in ['billion','billions','b','B','10**9','1E9','1e9',1E9,9]:
        unitifier = 1E9
    elif units in ['million','millions','m','M','10**6','1E6','1e6',1E6,6]:
        unitifier = 1E6
    dfin = (
        retail_results
        .drop(['state','busbar_load','end_use_load','retail_load'],axis=1)
        .groupby('t').sum()
    )
    for col in dfin.columns:
        if col not in ['t','state','retail_load']:
            dfin[col] = dfin[col] * inf_adjust / unitifier
    dfout = dfin.sum(axis=1)
    return dfout

def inflatifier(inyear, outyear=2019, inflation=inflation):
    if inyear == outyear:
        return 1
    elif inyear > outyear:
        raise Exception("This simple function doesn't inflate past {}".format(outyear))
    else:
        return inflation.loc[inyear+1:outyear,'inflation_rate'].cumprod()[outyear]


#################
#%% Procedure ###
def main(write=True):
    #%%### Run the retail rate module with state, regional, and national aggregation of FERC data
    ### Load defaults
    inputs_default = pd.read_csv(os.path.join(retailmodulepath,'inputs_default.csv'))
    ### Loop over aggregation settings
    aggs = ['state','region','nation']
    dfretail = {}
    for agg in aggs:
        print('Calculating retail rate for {} aggregation...'.format(agg))
        inputs = inputs_default.set_index(['input_dict','input_key']).copy()
        inputs.loc[('input_daproj','aggregation'), 'input_value'] = agg
        ### Write it to a string stream that can be read by read_csv, since
        ### retail_rate_calculations.main() expects to read_csv the inputs dataframe from a file
        inputs_file = io.StringIO()
        inputs.reset_index().to_csv(inputs_file, index=False)
        ## Reset the read position to the beginning of the string
        inputs_file.seek(0)
        ### Run the retail rate calculation
        dfretail[agg] = retail_rate_calculations.main(
            run_dir=run_dir, inputpath=inputs_file, write=False, verbose=1)

    #%% Get EIA861 data for comparison
    df861 = pd.read_csv(
        os.path.join(retailmodulepath,'df_f861_contiguous.csv')
    ).set_index('year').loc[validationyears]

    df861['avg_retail_rate_2019'] = (
        df861.avg_retail_rate 
        * df861.index.map(lambda x: inflatifier(x,out_dollar_year)) * 100)
    df861['rev_2019'] = df861.rev * df861.index.map(lambda x: inflatifier(x,out_dollar_year))

    df861 = df861[['avg_retail_rate_2019','rev_2019']].copy()

    ### Get EIA861 by state
    df861_state = pd.read_csv(os.path.join(retailmodulepath,'df_f861_state.csv'))
    df861_state = df861_state.loc[df861_state.year.isin(validationyears)].copy()

    df861_state['avg_retail_rate_2019'] = (
        df861_state.avg_retail_rate 
        * df861_state.year.map(lambda x: inflatifier(x,out_dollar_year)) * 100)
    df861_state['rev_2019'] = (
        df861_state.rev
        * df861_state.year.map(lambda x: inflatifier(x,out_dollar_year)))

    df861_state = (
        df861_state.set_index(['state','year'])
        [['avg_retail_rate_2019','rev_2019']].copy())

    #%% Determine which aggregation level gives the best fit for each state
    dicterror = {}
    for agg in aggs:
        ### Get the data
        dfrate = getrate_state(dfretail[agg]).unstack()[validationyears].stack()
        dfcompare = pd.concat(
            [dfrate.rename('modeled'), df861_state.avg_retail_rate_2019.rename('EIA861')],
            axis=1)
        dicterror[agg] = (dfcompare['modeled'] - dfcompare['EIA861']).mean(level=0).dropna()
    dferror = pd.concat(dicterror, axis=1)
    ### Get the aggregation level with the lowest absolute bias error
    dferror['aggregation'] = dferror.apply(lambda row: row.abs().nsmallest(1).index[0], axis=1)
    ### For states in which region and state give same results and are best, keep region
    dferror.loc[
        ((dferror['state'] == dferror['region']) & (dferror['aggregation'] == 'state')),
        'aggregation'
    ] = 'region'
    ### Call the state index 'index' to avoid confusing with 'state' results column
    dferror.index.name = 'index'

    #%% Take a look
    print(dferror.round(2),'\n')
    print(dferror.aggregation.value_counts(),'\n')
    for level in ['nation','region','state']:
        print('{:<6} ({:>2}): {}'.format(
            level, 
            dferror.aggregation.value_counts()[level],
            ','.join(dferror.loc[dferror.aggregation==level].index.values.tolist())))

    #%% Save it
    savename = os.path.join(
        retailmodulepath, 'inputs', 'state-meanbiaserror_rate-aggregation.csv')
    print(savename)
    if write:
        dferror.round(6).to_csv(savename)


if __name__ == '__main__':
    main()
