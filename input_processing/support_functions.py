
import pandas as pd
import numpy as np
import csv
import os
import sys
import re
import itertools

# Turning off pandas' SettingWithCopyWarning for chained assignments 
# (which would otherwise be raised for an issue that isn't a problem). 
pd.options.mode.chained_assignment = None


#%%
class scen_settings():

    def __init__(self, dollar_year, tech_groups, input_dir, switches):
        self.dollar_year = dollar_year
        self.tech_groups = tech_groups
        self.input_dir = input_dir
        self.switches = switches


def calc_crf(discount_rate, financial_lifetime):
    '''
    discount_rate: fraction including 1 (i.e. 5% would be 1.05)
    financial_lifetime: years
    '''
    crf = (
        (discount_rate - 1)
        / (1 - (1 / discount_rate**financial_lifetime))
    )
    return crf


#%%
def import_tech_groups(file_path):
    ''' 
    Creates a dictionary of different tech groups from a csv. 
    Used during the import process -- if a particular assumption applies to a family of technologies, 
        this dictionary creates the mapping. 

    First column of the input csv is the dictionary key for that tech family. 
    There cannot be duplicate keys, and they must differ from a tech name. 
    '''


    tech_subset_table = pd.read_csv(file_path)
    tech_subset_table = tech_subset_table.rename(columns={'Unnamed: 0':'i'})

    tech_subset_table = expand_GAMS_tech_groups(tech_subset_table)

    tech_subset_table = tech_subset_table.set_index('i')
    tech_groups = {}
    for col in list(tech_subset_table.columns):
        tech_groups[col] = list(tech_subset_table[col][tech_subset_table[col]=='YES'].index) 


    return tech_groups

#%%
def ingest_years(inputs_case, sys_eval_years, end_year):
    '''
    modeled_years: The years that will be solved in the GAMS model. 
        Specified by the modeled_years input, cut off by the specified end year. 
    years: All years, not just solve years. Bounded by minimum solve year and 
        max solve year + however long the model looks ahead for evaluating technologies
    year_map: Mapping of each year to the solve year it is associated with

    '''
    modeled_years = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv')).columns.astype(int).values
    modeled_years = modeled_years[modeled_years<=end_year]

    # Determine the full range of years, based on modeled_years
    # Extend beyond the last modeled year by the evaluation horizon of the model
    years = np.arange(np.min(modeled_years), np.max(modeled_years)+sys_eval_years, 1)

    # Create the mapping between years and modeled_year 
    # (used for grouping values to their modeled year later), merge
    # Contains additional years beyond final year for handling termination year continuation 
    year_map = pd.DataFrame(data={'t':np.arange(np.min(modeled_years), np.max(years)+1, 1)})
    year_map['modeled_year'] = [np.max(modeled_years[year>=modeled_years]) for year in year_map['t']]

    return years, modeled_years, year_map


#%%
def build_dfs(years, techs, vintage_definition, year_map):

    ''' Build df_ivt (for calculating various parameters at subscript [i,v,t])

    Notes:
     - available_for_build means that that [i,v] combo is specified as the vintage available 
       for investment in the given year, per the vintage_definition file. 
 
    '''


    # Expand for subtechs, melt
    # ivt_long is a melted version of the ivt input file
    vintage_definition = expand_GAMS_tech_groups(vintage_definition)
    vintage_definition_long = vintage_definition.melt(id_vars='i', var_name='t', value_name='v')
    vintage_definition_long['t'] = vintage_definition_long['t'].astype(int)

    # Determine the first and last year that each [i,v] combination appears
    iv_year_bounds = vintage_definition_long.groupby(by=['i', 'v']).min()
    iv_year_bounds.reset_index(inplace=True)
    iv_year_bounds = iv_year_bounds.rename(columns={'t':'first_year_v_available'})
    iv_last_year = vintage_definition_long.groupby(by=['i', 'v']).max()
    iv_last_year.reset_index(inplace=True)
    iv_last_year.rename(columns={'t':'last_year'}, inplace=True)
    iv_year_bounds = iv_year_bounds.merge(iv_last_year, on=['i', 'v'])

    itv_map = pd.DataFrame()
    for tech in techs['i']:
        max_c = np.max(vintage_definition_long[vintage_definition_long['i']==tech]['v'])
        tech_itv_df = pd.DataFrame(
            list(itertools.product(years, np.arange(1,max_c+1,1))), 
            columns=['t', 'v'])
        tech_itv_df['i'] = tech
        itv_map = pd.concat([itv_map, tech_itv_df], ignore_index=True)
    itv_map = itv_map.merge(iv_year_bounds, on=['i', 'v'])
    # drop all [i,v] combos before the year that v is first available
    itv_map = itv_map[itv_map['t']>=itv_map['first_year_v_available']]
    # Flag which vintages are available for building in any given year
    itv_map['available_for_build'] = np.where(itv_map['t']<=itv_map['last_year'], True, False)


    ########################### Build df_inv ##################################

    df_it = pd.DataFrame(list(itertools.product(techs['i'], years)),
                            columns=['i', 't'])

    # Since df_inv only contains generators available for build, filter itc map down
    itv_map_inv = itv_map[itv_map['available_for_build']==True]

    # Merge on itv_map_inv to expand by [v]
    # Expand for [v]
    df_ivt = df_it.merge(itv_map_inv[['i', 't', 'v', 'first_year_v_available']], on=['i', 't'])

    # Merge on year_map, for useful information later on
    df_ivt = df_ivt.merge(year_map, on='t', how='left')


    return df_ivt


#%%
def import_sys_financials(financials_sys_suffix, inflation_df, modeled_years, 
                          years, year_map, sys_eval_years, scen_settings,co2_incentive_length):
    '''
    Import system-wide financial parameters, and calculate discount rate from them

    '''

    # Import and merge on inflation rate data
    sys_financials = import_data(
        file_root='financials_sys', file_suffix=financials_sys_suffix, 
        indices=['t'], scen_settings=scen_settings) 
    sys_financials = sys_financials.merge(inflation_df, on='t', how='left')

    # Calculate system-wide discount rates, directly using WACC as discount rate   
    sys_financials['d_nom'] = (
        (1 - sys_financials['debt_fraction']) * (sys_financials['rroe_nom'] - 1) 
        + (sys_financials['debt_fraction']
           * (sys_financials['interest_rate_nom'] - 1)
           * (1 - sys_financials['tax_rate']))
        + 1
    )

    sys_financials['d_real'] = sys_financials['d_nom'] / sys_financials['inflation_rate']


    # Calculate present value factors. 
    # Treating as pvf at the beginning of the year, so the first year equals 1, 
    # all other years are discounted by cumulation of preceding year's discount rates
    sys_financials = sys_financials.set_index('t')

    # Calculate pvf_capital. 
    sys_financials['pvf_capital'] = 1
    for year in np.arange(np.min(modeled_years)+1, np.max(years)+1):
        sys_financials.loc[year,'pvf_capital'] = (
            sys_financials.loc[year-1,'pvf_capital'] / sys_financials.loc[year-1,'d_real'])

    # Calculate pvf_onm (only for intertemporal mode). 
    sys_financials.loc[np.min(modeled_years), 'pvf_onm'] = (
        1 / sys_financials.loc[np.min(modeled_years),'d_real'])
    for year in np.arange(np.min(modeled_years)+1, np.max(years)+1):
        sys_financials.loc[year,'pvf_onm'] = (
            sys_financials.loc[year-1,'pvf_onm'] / sys_financials.loc[year,'d_real'])

    sys_financials = sys_financials.reset_index()

    # Calculate the capital recovery factor for each year (for pvf_onm for sequential mode).
    sys_financials['crf'] = calc_crf(sys_financials['d_real'], sys_eval_years)

    sys_financials['crf_co2_incentive'] = calc_crf(sys_financials['d_real'], co2_incentive_length)

    # Merge on year_map for the model year column
    # As an inner merge, this removes any extraneous years, that weren't part of year_map
    sys_financials = sys_financials.merge(year_map, on='t')

    return sys_financials


#%%
def import_data(file_root, file_suffix, indices, scen_settings, inflation_df=[], 
                expand_tech_groups=True, adjust_units=True, check_for_dups=True):
    '''
    Description: General importer that does several useful things
        - If there are currency data inputs, this adjusts them to the model's dollar year
        - If there is an 'i' column, it will expand any tech groups to their full members 
            (making it easier to input data for groups)
        - Checks to make sure there wasn't duplicated entries for the specified indices 
            (could be a problem when expanding)

    Arguments:
        indices = column headers that indicate unique entries. 
            E.g. for [i,t,cap_cost,cost_mult], [i,t] would be the indices. 


    '''

    df = pd.read_csv(
        os.path.join(scen_settings.input_dir, 'financials', '%s_%s.csv' % (file_root, file_suffix)))

    # Expand tech groups, if there is an 'i' column and the argument is True
    if 'i' in df.columns and expand_tech_groups==True:
        for tech_group in scen_settings.tech_groups.keys():
            if tech_group in list(df['i']):

                df_subset = df[df['i']==tech_group] # Extract the tech group from the main df
                df = df[df['i'] != tech_group] # Drop the tech group from the main df

                df_list = []

                for tech in scen_settings.tech_groups[tech_group]:
                    df_expanded_single = df_subset.copy()
                    df_expanded_single['i'] = tech
                    df_list = df_list + [df_expanded_single]

                df = pd.concat([df]+df_list, ignore_index=True)


    # Check if a currency_file_root file exists - it should exist if there are 
    # any columns with currency data. If currency data exists, adjust the dollar
    # year of the input data to the scen_settings's dollar year
    if (os.path.isfile(os.path.join(scen_settings.input_dir, file_root, 'currency_%s.csv' % file_root))
        and (adjust_units==True)
    ):
        currency_meta = pd.read_csv(
            os.path.join(scen_settings.input_dir, file_root, 'currency_%s.csv' % file_root), 
            index_col='file')
        inflation_df = inflation_df.set_index('t')

        # Check if a row exists in file_root_currency, for the specified input data
        if file_suffix not in currency_meta.index:
            raise Exception(
                'The input data {0}_{1} has a currency input\nbut the currency type is not '
                'specified. In the {0} data\ndirectory, open the currency_{0}.csv and enter a '
                'new row with metadata\nfor dataset {0}_{1}.csv'.format(file_root, file_suffix))

        scenario_currency = currency_meta.loc[file_suffix, :]

        for col in scenario_currency.index:
            input_currency = scenario_currency[col]
            # Remove the USD. This should be generalized when other currencies are introduced.
            input_dollar_year = int(input_currency.replace('USD',''))

            if input_dollar_year < scen_settings.dollar_year:
                inflation_adjust = np.array(np.cumprod(inflation_df.loc[input_dollar_year+1:scen_settings.dollar_year]))[-1]
            elif input_dollar_year > scen_settings.dollar_year:
                inflation_adjust = 1.0 / np.array(np.cumprod(inflation_df.loc[scen_settings.dollar_year+1:input_dollar_year]))[-1]
            elif input_dollar_year == scen_settings.dollar_year:
                inflation_adjust = 1.0

            df[col] = df[col] * inflation_adjust

    # Check to see if there are any duplicate entries for the given indices
    if check_for_dups==True:
        df_index_check = df[indices].copy()
        if len(df_index_check) != len(df_index_check.drop_duplicates()):
            print('Error: Duplicate entries for', file_root, file_suffix, 'on indices', indices)
            sys.exit()


    return df
   

def append_pvb_parameters(dfin, tech_to_copy='battery_4', column_scaler=None, pvb_types=[1,2,3]):
    """
    Copies the parameters for tech_to_copy (typically standalone batteries, except for the ITC, 
    where we copy from UPV) for batteries in PV+battery systems and returns a copy of the input 
    dataframe with the PV+B parameters appended.

    Inputs
    ------
    dfin: Original inputs dataframe that includes standalone battery assumptions.
        Must have a column labeled i containing entries for tech_to_copy.
    tech_to_copy: default='battery_4'. Technology from which to copy parameters for PV+battery.
    column_scaler: None or dict. If dict, format should be {column_to_scale: scaler}.
    pvb_types: default=[1,2,3]. Set of pvb technology types.
        NOTE: If PV+B techs are added to set i "generation technologies" in b_inputs,
        make sure to adjust the pvb_types list here.

    Outputs
    -------
    dfout: pd.DataFrame consisting of PV+B parameters appended to input dataframe.
    """
    ### Get the PVB classes from upv
    pvb_classes = [i.split('_')[1] for i in dfin.i.unique() if i.startswith('upv')]
    ### Get values for tech_to_copy
    copy_params = dfin.set_index('i').loc[[tech_to_copy]].reset_index(drop=True).copy()
    ### Create output dataframe, copying tech_to_copy assumptions for PV batteries
    append_pvb_params = pd.concat({
        'pvb{}_{}'.format(pvb_type, pvb_class): copy_params
        for pvb_type in pvb_types for pvb_class in pvb_classes
    }).reset_index(level=0).rename(columns={'level_0':'i'})
    ### Scale the columns in columns_scaler if necessary
    if column_scaler is not None:
        for col, scaler in column_scaler.items():
            append_pvb_params[col] = (append_pvb_params[col] * scaler).round(5)
    ### Append to the original dataframe and return
    dfout = dfin.append(append_pvb_params, ignore_index=True)

    return dfout


#%% 
def import_and_mod_incentives(incentive_file_suffix, construction_times_suffix,
                              inflation_df, scen_settings):
    '''  

    This code assumes any generation policy (gen_pol) is a tax credit, 
        therefore needs to be adjusted later to get in pre-tax terms. 
        If a non-tax-credit generation policy is ever implemented, 
        it would be best to split tax and non-tax apart and sum them together later.

    Other assumptions:
        - All eligibility of incentives is assumed to be "start construction", as opposed to 
            "start operation". Therefore, all incentives are time shifted by construction times. 
            If a "start operation" incentive is implemented, a column to specify
            whether a given incentive is shifted or not should be added to the input file. 

    Notes:
        - Data handling for incentives are more difficult to generalize then other model inputs. 
            This code may be useful for new incentives, but the processed model inputs for any 
            new incentive should be examined and custom code may need to be written.
        - xx_monetized is the value (or fraction) of an incentive, after penalizing it for the 
            costs to monetize, either a time-value-of-money "penalty" due to having to wait until 
            tax burden is sufficient, or through the costs of monetizing through tax equity

    '''
    # Import construction times
    construction_times = import_data(
        file_root='construction_times', file_suffix=construction_times_suffix, 
        indices=['i', 't_online'], 
        scen_settings=scen_settings, adjust_units=False)
    ### Apply the standalone battery construction times to hybrid PV batteries
    construction_times = append_pvb_parameters(
        dfin=construction_times, 
        tech_to_copy='battery_{}'.format(scen_settings.switches['GSw_PVB_Dur']))

    construction_times['t_start_construction'] = (
        construction_times['t_online'].astype(int) 
        - construction_times['construction_time'].astype(int))
    construction_times = construction_times.rename(columns={'t_online':'t'})

    # Import incentives, determine the year the tech would be built based on construction times
    incentive_df = import_data(
        file_root='incentives', file_suffix=incentive_file_suffix, 
        indices=['i','country','t'], 
        inflation_df=inflation_df, scen_settings=scen_settings)
    ### Add the hybrid PV+battery incentives (in this case inherited from upv, not battery)
    incentive_df = append_pvb_parameters(
        dfin=incentive_df, tech_to_copy='upv_1', 
        column_scaler={'itc_frac': float(scen_settings.switches['GSw_PVB_ITC_Qual_Award'])}
    )
    
    # Calculate total PTC and ITC value, taking into account bonus
    # ptc_perc_bonus is a multiplicative increase of the base ptc value. E.g. a value of 0.1 on a $10 ptc value equates to $11
    # itc_percpt_bonus is a additive increase of the base itc value. E.g. a value of 0.1 on a 0.3 itc value equates to a 0.4 itc value. 
    incentive_df['ptc_value'] = incentive_df['ptc_value'] * (1.0 + incentive_df['ptc_perc_bonus']) 
    incentive_df['itc_frac'] = incentive_df['itc_frac'] + incentive_df['itc_percpt_bonus']

    # Merge with construction start years
    incentive_df = incentive_df.merge(construction_times, on=['i', 't'], how='left')

    # Because of changing construction durations, some incentives don't apply to any online years. Drop those rows. 
    incentive_df = incentive_df[incentive_df['t'].isnull()==False]
    
    # If the construction period exceeds the safe harbor, assume the safe harbor would be extended
    incentive_df['ptc_safe_harbor'] = incentive_df[['ptc_safe_harbor', 'construction_time']].max(axis=1)
    incentive_df['itc_safe_harbor'] = incentive_df[['itc_safe_harbor', 'construction_time']].max(axis=1)
    incentive_df['co2_capture_safe_harbor'] = incentive_df[['co2_capture_safe_harbor', 'construction_time']].max(axis=1)
        
    # create year expander
    year_list = []
    max_safe_harbor = np.max(incentive_df[['ptc_safe_harbor', 'itc_safe_harbor', 'co2_capture_safe_harbor']].max())
    for n in np.arange(0, max_safe_harbor+1):
        year_df = pd.DataFrame()
        year_df['safe_harbor_buffer'] = np.arange(0,n+1)
        year_df['safe_harbor'] = n
        year_list += [year_df.copy()]
    expander = pd.concat(year_list, ignore_index=True, sort=False)
    
    # For each year that an incentive was available, expand the years that a generator could have come online and
    # captured that incentive, given its safe harbor
    # for an incentive available in year t, the last year that a generator could come online having captured
    # that incentive is t+safe_harbor
    ptc_df = incentive_df[['i', 'country', 't', 'ptc_value', 'ptc_dur', 'ptc_tax_equity_penalty', 'ptc_safe_harbor', 'construction_time']].copy()
    ptc_df = ptc_df[ptc_df['ptc_value']!=0.0]
    ptc_df = ptc_df.merge(expander.rename(columns={'safe_harbor':'ptc_safe_harbor'}), on=['ptc_safe_harbor'], how='left')
    ptc_df['t'] = ptc_df['t'] + ptc_df['safe_harbor_buffer']
    ptc_df['value'] = ptc_df['ptc_value']
    
    itc_df = incentive_df[['i', 'country', 't', 'itc_frac', 'itc_tax_equity_penalty', 'itc_safe_harbor', 'construction_time']].copy()
    itc_df = itc_df[itc_df['itc_frac']!=0.0]
    itc_df = itc_df.merge(expander.rename(columns={'safe_harbor':'itc_safe_harbor'}), on=['itc_safe_harbor'], how='left')
    itc_df['t'] = itc_df['t'] + itc_df['safe_harbor_buffer']
    itc_df['value'] = itc_df['itc_frac']

    
    co2_df = incentive_df[['i', 'country', 't', 'co2_capture_value', 'co2_capture_dur', 'co2_capture_tax_equity_penalty', 'co2_capture_safe_harbor', 'construction_time']].copy()
    co2_df = co2_df[co2_df['co2_capture_value']!=0.0]
    co2_df = co2_df.merge(expander.rename(columns={'safe_harbor':'co2_capture_safe_harbor'}), on=['co2_capture_safe_harbor'], how='left')
    co2_df['t'] = co2_df['t'] + co2_df['safe_harbor_buffer']
    co2_df['value'] = co2_df['co2_capture_value']

    incentive_df = pd.concat([ptc_df[['i', 'country', 't', 'ptc_value', 'ptc_dur', 'ptc_tax_equity_penalty', 'ptc_safe_harbor', 'construction_time', 'value']],
                              itc_df[['i', 'country', 't', 'itc_frac', 'itc_tax_equity_penalty', 'itc_safe_harbor', 'construction_time', 'value']],
                              co2_df[['i', 'country', 't', 'co2_capture_value', 'co2_capture_dur', 'co2_capture_tax_equity_penalty', 'co2_capture_safe_harbor', 'construction_time', 'value']]], 
                            ignore_index=True, sort=False)
    
    # Because of the safe harbor windows or the input sheet, we can have multiple incentives available to a generator 
    # (even if no single year had more than one incentive available). As a simple expedient, we are just sorting by incentive value
    # and selecting the highest. This is not meant to select between competing incentives, as we do not have the operational data
    # at this point to estimate their value. It is just a simple approach implemented here for lack of time to develop a better one. 
    incentive_df = incentive_df.sort_values('value', ascending=False)
    incentive_df = incentive_df.drop_duplicates(['i', 'country', 't'], keep='first')
    
    incentive_df = incentive_df.fillna(0.0)

    # Apply a penalty for monetizing the tax credits through tax equity (or waiting to internally monetize them)
    # The simple reduction of credit value is a simple implementation - more sophisticated estimates of lost
    # value should be made for future analysis that is focused on tax credits. pgagnon 5-7-19
    incentive_df['ptc_value_monetized'] = incentive_df['ptc_value'] * (1 - incentive_df['ptc_tax_equity_penalty'])
    incentive_df['itc_frac_monetized'] = incentive_df['itc_frac'] * (1 - incentive_df['itc_tax_equity_penalty'])
    incentive_df['co2_capture_value_monetized'] = incentive_df['co2_capture_value'] * (1 - incentive_df['co2_capture_tax_equity_penalty'])

    incentive_df['safe_harbor_max'] = incentive_df[['ptc_safe_harbor', 'itc_safe_harbor', 'co2_capture_safe_harbor']].max(axis=1)

    return incentive_df[['i', 't', 'country', 'ptc_value', 'ptc_value_monetized', 'ptc_dur', 'ptc_tax_equity_penalty',
                         'itc_frac', 'itc_frac_monetized', 'itc_tax_equity_penalty',
                         'co2_capture_value', 'co2_capture_value_monetized', 'co2_capture_dur', 
                         'safe_harbor_max']]


def calc_degradation_adj(d_real,eval_period,annual_degradation):
    if(annual_degradation==0):   
        return 1.0
    else:
        pv_year = 0
        pv = 0
        pv_degraded= 0
        for i in range(0,int(eval_period)+1):
            pv_year = 1/(d_real)**i
            pv = pv + pv_year
            pv_degraded = pv_degraded+ pv_year*(1-annual_degradation)**i
        return pv/pv_degraded

#%%
def calc_financial_multipliers(df_inv, construction_schedules, depreciation_schedules, timetype):
    '''
    '''
    ###### Calculate the present value multiplier of financing differences for this tech  #########
    # This input is for deviations from the system-wide average financing. For example, a new
    # technology might have financers demanding higher expected dividends before investing,
    # which would result in a penalty here. Conversely, some type of government loan program
    # could result in overall cheaper financing, which would be represented as a benefit here. 

    df_inv['financing_risk_mult'] = (
        1.0
        + df_inv['finance_diff_real'] * (
            (1 - (1 / df_inv['d_real']**df_inv['eval_period']))
            / (df_inv['d_real'] - 1.0)
        )
    )

    #################### Calculate Financial Multiplier  ############################
    df_inv['itc_frac_monetized'] = df_inv['itc_frac_monetized'].fillna(0)

    # Calculate the construction financing cost multiplier. 
    #    This multiplier represents the relative increase in the cost basis as a result of paying
    #    interest to finance construction.
    #    Construction interest is capitalized and added to the cost basis rather than expensed
    # Calculation:  1 + sum{t, x[t] * ((1 + i)^t - 1)}
    #    t = years prior to the completion of the plant (also the years prior to the first year of operation)
    #    x[t] = fraction of capacity built in year t, where t represents years prior to year zero
    #    i = construction interest rate
    #    See the 2019 documentation for the derivation

    df_inv['CCmult'] = (
        1 + np.array(
            np.sum(
                construction_schedules[df_inv['construction_sch']].T
                * (
                    np.power.outer(
                        df_inv['interest_rate_nom'].values,
                        np.append([0],np.arange(0.5,10.5,1.)))
                    - 1
                ),
                axis=1
            )
        )
    )

    # Calculate the (fractional) present value of depreciation 
    df_inv['PV_fraction_of_depreciation'] = np.array(
        np.sum(
            depreciation_schedules[df_inv['depreciation_sch'].astype(str)].T
            / np.power.outer(
                df_inv['d_nom'].values,
                np.arange(1,22)), 
            axis=1
        )
    )

    # Calculate the Degradation_Adjustment
    ### Rather than calling calc_degradation_adj for millions of rows, we call it for each
    ##  unique set of (d_real, eval_period, annual_degradation), cache the results, then
    ##  look up the value for each row
    unique_inputs = df_inv[['d_real','eval_period','annual_degradation']].drop_duplicates().values
    lookup = pd.Series(
        {tuple(x): calc_degradation_adj(*x) for x in unique_inputs},
        name='Degradation_Adj')
    lookup.index = lookup.index.set_names(['d_real','eval_period','annual_degradation'])

    if(timetype == 'seq'):
        df_inv = df_inv.merge(lookup, on=['d_real','eval_period','annual_degradation'], how='left')
    else:
        df_inv['Degradation_Adj'] = 1.0

    # Calculate the financial multiplier
    df_inv['finMult'] = (
        df_inv['CCmult']
        / (1 - df_inv['tax_rate'])
        * (1 
            - df_inv['tax_rate'] * (1 - df_inv['itc_frac_monetized']/2) * df_inv['PV_fraction_of_depreciation'] 
            - df_inv['itc_frac_monetized'])
        * df_inv['Degradation_Adj']
    )
    df_inv['finMult_noITC'] = (
        df_inv['CCmult'] 
        / (1 - df_inv['tax_rate']) 
        * (1 - df_inv['tax_rate'] * df_inv['PV_fraction_of_depreciation'] ) 
        * df_inv['Degradation_Adj']
    )

    return df_inv

def calc_final_capital_cost_multiplier(df, mult_type='finMult'):
    final_cap_cost_mult = (
        df[mult_type] * df['financing_risk_mult']
        ## Scale the cost multiplier by the ratio of CRF(trans_crp) / CRF (sys_eval_years)
        * df["crf_tech"] / df['crf']
    )
    return final_cap_cost_mult


#%%
def adjust_ptc_values(df_ivt):
    '''
    '''
    # Calculate the PTC's tax value
    #   Since the PTC reduces income taxes (which are levied on a utility's 
    #   return on their rate base), the actual value of the PTC higher than its
    #   nominal value by 1/(1-taxRate). This component is the grossup value. 
    #   Note that this effect is already included for the ITC when financial
    #   multipliers are calculated.
    df_ivt[['ptc_value_monetized', 'ptc_dur', 'ptc_value']].fillna(0, inplace=True)
    df_ivt['ptc_value_monetized_posttax'] = df_ivt['ptc_value_monetized'] * (1 / (1 - df_ivt['tax_rate']))
    df_ivt['ptc_grossup_value'] = df_ivt['ptc_value'] * ( 1 / (1 - df_ivt['tax_rate']) - 1.0)

    # ptc_value_scaled is the ptc value that incorporates everything expected by 
    # reeds: monetization costs, tax grossup value, and an adjustment to reflect
    # the difference between the ptc_dur and system evaluation period
    df_ivt['ptc_dur_pvf_sum'] = (1 - (1 / (df_ivt['d_real'])**(df_ivt['ptc_dur']-1))) / (df_ivt['d_real']-1.0) + 1
    df_ivt['ptc_value_scaled'] = df_ivt['ptc_value_monetized_posttax'] * df_ivt['ptc_dur_pvf_sum'] / df_ivt['sys_pvf_eval_period_sum']

    return df_ivt



#%% Export parameters for the model. General exporter for most, some need custom exporters. 

def inv_param_exporter(df, modeled_years, parameter, indices, file_name, output_dir):
    ''' 
    General exporter for investment parameters, to be used in the GAMS model. 

    Collapses parameter down to the indicated indices, throwing an error if 
        the parameter varied over another index that wasn't given. 
    Currently only exports the values during the modeled_years (as opposed to, 
        for example, averaging over the years associated with a solve year). 
    '''

    # For investment parameters we only care about modeled_year values 
    # Skip this step if there is no 't' index, inducated by modeled_years=None
    if 't' in indices:
        df = df[df['t'].isin(modeled_years)]
    

    df_param = df[indices+[parameter]].drop_duplicates()
    df_check_size = df[indices].drop_duplicates()

    if len(df_param) != len(df_check_size):
        print('Attempting to collapse parameter down, but it varies across a non-specified '
              'index\nParameter:', parameter)
        print('To debug, use df_param.duplicated(indices), pick something that is duplicated, '
              'then filter down to that\nin the larger df, looking for reasons why it would '
              'vary across the indices given.')
        sys.exit()

    df_param[parameter] = np.round(df_param[parameter], 6)
    #%% Add '*' to first column name so GAMS reads it as a comment
    df_param = df_param.rename(
        columns={c: (f'*{c}' if not i else c) for i,c in enumerate(df_param.columns)})
    df_param.to_csv(os.path.join(output_dir, f'{file_name}.csv'), index=False, header=True)


#%% Export parameters

def param_exporter(df, parameter, file_name, output_dir):
   
    df[parameter] = np.round(df[parameter], 5)
    #%% Add '*' to first column name so GAMS reads it as a comment
    df = df.rename(
        columns={c: (f'*{c}' if not i else c) for i,c in enumerate(df.columns)})
    df.to_csv(os.path.join(output_dir, f'{file_name}.csv'), index=False, header=True)


#%%
def expand_GAMS_tech_groups(df):
    '''
    GAMS has a convention for expanding rows (e.g. upv_1*upv_10 is expanded to upv_1, upv_2,..., upv_10)
    This function expands a df with the same convention, for the instances where a file is ingested
    by both python and GAMS. We assume the numbers we would like to enumerate occur at the end.
    '''

    tech_groups = [group for group in df['i'] if '*' in group]

    for tech_group in tech_groups:
        tech_group_ls = tech_group.split('*')
        num_start = int(re.search(r'(\d+)\s*$', tech_group_ls[0]).group(1))
        num_end = int(re.search(r'(\d+)$', tech_group_ls[1]).group(1))
        tech_group_root = re.sub(r'\d+\s*$', '', tech_group_ls[0])
        techs = [f'{tech_group_root}{num}' for num in range(num_start,num_end+1)]

        df_subset = df[df['i']==tech_group] # Extract the tech group from the main df
        df = df[df['i'] != tech_group] # Drop the tech group from the main df

        df_list = []

        for tech in techs:
            df_expanded_single = df_subset.copy()
            df_expanded_single['i'] = tech
            df_list = df_list + [df_expanded_single]

        df = pd.concat([df]+df_list, ignore_index=True)

    return df
