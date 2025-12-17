'''
ReEDS 2.0 results metadata and preprocess functions.

When adding a new ReEDS result and associated presets, this should be the only file you need to modify.

There are three sections:
1. Preprocess functions: Only needed for a result if the gdx data needs to be manipulated
2. Columns metatdata: This allows column values from a result to be mapped to display categories, joined with other columns, and styled
3. Results metadata: This is where all result configuration happens
'''
from __future__ import division
import os
import pandas as pd
import numpy as np
import collections
import core
import copy
from itertools import product
## Inherit the default present value year to use in plot definitions
from defaults import DEFAULT_PV_YEAR

rb_globs = {'output_subdir':'/outputs/', 'test_file':['cap.csv','outputs.h5'], 'report_subdir':'/reeds2'}
this_dir_path = os.path.dirname(os.path.realpath(__file__))
df_deflator = pd.read_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'inputs/financials/deflator.csv')), index_col=0)
coststreams = ['eq_gasaccounting_regional','eq_gasaccounting_national','eq_bioused','eq_gasused','eq_objfn_inv','eq_objfn_op']
vf_valstreams = ['eq_supply_demand_balance','eq_reserve_margin','eq_opres_requirement','eq_rec_requirement','eq_curt_gen_balance','eq_curtailment','eq_storage_in_max','eq_storage_in_min']
# valuestreams = ['eq_supply_demand_balance','eq_reserve_margin','eq_opres_requirement','eq_rec_requirement','eq_national_gen','eq_annual_cap','eq_curt_gen_balance','eq_curtailment','eq_storage_in_max','eq_storage_in_min','eq_emit_accounting','eq_mingen_lb','eq_mingen_ub','eq_rps_ofswind']
energy_valstreams = ['eq_supply_demand_balance','eq_curt_gen_balance','eq_curtailment','eq_storage_in_max','eq_storage_in_min']
cc_techs = ['hydro','wind-ons','wind-ofs','csp','upv','pumped-hydro','pumped-hydro-flex','battery','battery_li','tes_ms']
battery_techs=['battery_li','tes_ms']
h2_techs = ['smr', 'smr-ccs', 'electrolyzer']
prod_techs = h2_techs + ['dac']
niche_techs =  ['hydro','csp','geothermal','beccs','lfill-gas','biopower']
price_types = ['load','res_marg','oper_res','state_rps','nat_gen']
ccs_techs = ['gas-cc-ccs_mod_upgrade','coal-ccs_mod_upgrade','gas-cc-ccs_max_upgrade','coal-ccs_max_upgrade','gas-cc-ccs_mod','gas-cc-ccs_max','coal-ccs_mod','coal-ccs_max','coal-ccs-nsp','coal-ccs-flex','gas-cc-ccs-flex']
water_techs = pd.read_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'postprocessing/bokehpivot/in/reeds2/tech_ctt_wst.csv')))['tech'].tolist()
water_techs = [x.lower() for x in water_techs]

#1. Preprocess functions for results_meta
def scale_column(df, **kw):
    df[kw['column']] = df[kw['column']] * kw['scale_factor']
    return df

def add_cooling_water(df, **kw):
    #load the tech mapping to ctt and wst
    df_tech_ctt_wst = pd.read_csv(this_dir_path + '/in/reeds2/tech_ctt_wst.csv')
    df_tech_ctt_wst['tech'] = df_tech_ctt_wst['tech'].str.lower()
    df = pd.merge(left=df, right=df_tech_ctt_wst, how='left', on=['tech'], sort=False)
    #fill na values
    df['wst'].fillna('other', inplace=True)
    df['ctt'].fillna('none', inplace=True)
    return df

def scale_column_filtered(df, **kw):
    cond = df[kw['by_column']].isin(kw['by_vals'])
    df.loc[cond, kw['change_column']] = df.loc[cond, kw['change_column']] * kw['scale_factor']
    return df

def sum_over_cols(df, **kw):
    if 'val_cols' in kw:
        drop_cols = [c for c in df.columns if c not in kw['group_cols']+kw['val_cols']]
    elif 'drop_cols' in kw:
        drop_cols = kw['drop_cols']
    df = df.drop(drop_cols, axis='columns', errors='ignore')
    df =  df.groupby(kw['group_cols'], sort=False, as_index =False).sum()
    return df

def apply_inflation(df, **kw):
    df[kw['column']] = inflate_series(df[kw['column']])
    return df

def inflate_series(ser_in):
    return ser_in * 1/df_deflator.loc[int(core.GL['widgets']['var_dollar_year'].value), 'Deflator']

def gather_cost_types(df):
    #Gather lists of capital and operation labels
    cost_cats_df = df['cost_cat'].unique().tolist()
    cost_cat_map = pd.read_csv(this_dir_path + '/in/reeds2/cost_cat_map.csv')
    if (~cost_cat_map.cost_type.isin(['Capital','Operation'])).any():
        error = (
            'Invalid values in cost_type column of cost_cat_map.csv. '
            'Only valid values are "Capital" and "Operation".'
        )
        raise KeyError(error)
    # Make sure all cost categories in df are in cost_cat_map and throw error if not
    if not set(cost_cats_df).issubset(cost_cat_map['raw'].values.tolist()):
        error = (
            'Not all cost categories have been mapped. Categories without a mapping are:\n'
            '\n'.join([c for c in cost_cats_df if c not in cost_cat_map['raw'].values.tolist()])
        )
        raise KeyError(error)
    cap_type_ls = [
        c for c in cost_cats_df
        if c in cost_cat_map[cost_cat_map['cost_type']=='Capital']['raw'].tolist()]
    op_type_ls = [
        c for c in cost_cats_df
        if c in cost_cat_map[cost_cat_map['cost_type']=='Operation']['raw'].tolist()]
    return cap_type_ls, op_type_ls

def pre_systemcost(dfs, **kw):
    df = dfs['sc'].copy()
    sw = dfs['sw'].set_index('switch')['value'].copy()
    scalars = dfs['scalars'].set_index('scalar')['value'].copy()
    sim_years = sorted(dfs['sc']['year'].unique()) #Years Optimized
    sys_eval_years = int(sw['sys_eval_years'])
    trans_crp = int(scalars['trans_crp'])
    addyears = max(sys_eval_years, trans_crp)
    
    #Sometimes we want costs by BA and year, but otherwise aggregate costs nationwide by year:
    if 'maintain_ba_index' in kw and kw['maintain_ba_index'] == True:
        id_cols = ['r','year']
    else:
        id_cols = ['year']
    
    # Get historical years (for historical capex)
    firstmodelyear, lastmodelyear = int(df.year.min()), int(df.year.max())
    historical_years = range(firstmodelyear-sys_eval_years, firstmodelyear)

    #apply inflation and adjust to billion dollars
    df['Cost (Bil $)'] = inflate_series(df['Cost (Bil $)']) * 1e-9
    d = float(core.GL['widgets']['var_discount_rate'].value)
    y0 = int(core.GL['widgets']['var_pv_year'].value)

    cap_type_ls, op_type_ls = gather_cost_types(df)
    ### Get the list of transmission investment categories (subset of cap_type_ls)
    trans_cap_type_ls = [
        c for c in cap_type_ls if c in [
            'inv_converter_costs',
            'inv_transmission_line_investment',
            'inv_transmission_interzone_ac_investment',
            'inv_transmission_interzone_dc_investment',
        ]
    ]
    nontrans_cap_type_ls = [c for c in cap_type_ls if c not in trans_cap_type_ls]

    #Calculate objective function system costs
    if 'objective' in kw and kw['objective'] is True:
        #Multiply all capital costs by pvf_capital and operation by pvf_onm
        df = pd.merge(left=df, right=dfs['pvf_cap'], how='left', on=['year'], sort=False)
        df = pd.merge(left=df, right=dfs['pvf_onm'], how='left', on=['year'], sort=False)
        cap_cond = df['cost_cat'].isin(cap_type_ls)
        onm_cond = df['cost_cat'].isin(op_type_ls)
        df.loc[cap_cond, 'Cost (Bil $)'] = df.loc[cap_cond, 'Cost (Bil $)'] * df.loc[cap_cond, 'pvfcap']
        df.loc[onm_cond, 'Cost (Bil $)'] = df.loc[onm_cond, 'Cost (Bil $)'] * df.loc[onm_cond, 'pvfonm']
        df.drop(['pvfcap','pvfonm'], axis='columns',inplace=True)
        #We don't add a discounted cost column
        return df

    #Annualize if specified
    if 'annualize' in kw and kw['annualize'] is True:
        #Turn each cost category into a column
        df = df.pivot_table(index=id_cols, columns='cost_cat', values='Cost (Bil $)').reset_index()
        if ('remove_existing' in kw) and (kw['remove_existing'] is True):
            df = df[df.year >= int(core.GL['widgets']['var_pv_year'].value)]
        #Add rows for all years (including extra years after end year for financial recovery)
        full_yrs = list(range(firstmodelyear - sys_eval_years, lastmodelyear + addyears + 1))

        if 'r' in df.columns:
            allyrs = pd.DataFrame(list(product(full_yrs,df.r.unique())), columns=['year','r'])
            df = pd.merge(allyrs,df,on=id_cols,how='left').set_index('year')
        else:
            df = df.set_index('year').reindex(full_yrs)

        ###### Add payments for pre-2010 capacity
        if ('remove_existing' not in kw) or (kw['remove_existing'] is False):
            ### Get modeled BAs
            val_r = dfs['val_r'][0].values
            ### Get total historical capex in modeled BAs
            df_capex_init = dfs['df_capex_init']
            if 'maintain_ba_index' in kw and kw['maintain_ba_index'] is True:
                ### Keep data up until the year before the first modeled year
                historical_capex = df_capex_init.rename(
                    columns={'t':'year'})
                historical_capex = historical_capex.loc[
                    df_capex_init.region.isin(val_r)
                ].groupby(['year','region']).capex.sum().loc[:firstmodelyear-1,:] / 1e9
                ### Convert to output dollar year
                historical_capex = inflate_series(historical_capex)
                historical_capex = pd.DataFrame(historical_capex)
                historical_capex.rename_axis(index={'region': 'r'}, inplace=True)
                ### Insert into full cost table
                df = df.set_index('r',append=True).join(historical_capex).reset_index('r')
                df.loc[:firstmodelyear-1,'inv_investment_capacity_costs'] = (
                    df.loc[:firstmodelyear-1,'capex'])
                df = df.drop('capex',axis=1)
            else:
                ### Keep data up until the year before the first modeled year
                historical_capex = df_capex_init.loc[
                    df_capex_init.region.isin(val_r)
                ].groupby('t').capex.sum().loc[:firstmodelyear-1] / 1e9
                ### Convert to output dollar year
                historical_capex = inflate_series(historical_capex)
                ### Insert into full cost table
                ### Fill any potential missing historical_capex year data with NaN
                missing_years = [x for x in historical_years if x not in historical_capex.index]
                for myr in missing_years:
                    historical_capex.at[myr] = np.nan
                df.loc[:firstmodelyear-1,'inv_investment_capacity_costs'] = (
                    historical_capex[historical_years].values)

        #For capital costs, multiply by CRF to annualize, and sum over previous 20 years.
        #This requires 20 years before 2010 to sum properly.
        if 'crf_from_user' in kw and kw['crf_from_user'] is True:
            crf = pd.DataFrame({
                'year': full_yrs,
                'crf': d*(1+d)**sys_eval_years / ((1+d)**sys_eval_years - 1)
            }).set_index('year')
        #otherwise use the crf from model run
        else:
            crf = dfs['crf']
            crf = crf.set_index('year').reindex(full_yrs)
            crf = crf.interpolate(method='linear')
            crf['crf'] = crf['crf'].fillna(method='bfill')

        if 'shift_capital' in kw and kw['shift_capital'] is True:
            #This means we start capital payments in the year of the investment, even though loan payments
            #typically start in the following year, so that investments made in 2050 are still reflected in 2050 capital payments.
            #This requires dividing the crf by discount rate to result in the same present value calculation.
            crf = crf/(1+d)
        else:
            #This method reflects typical loan payments that start in the year after the loan.
            if 'maintain_ba_index' in kw and kw['maintain_ba_index'] is True:
                df[cap_type_ls] = df.groupby('r')[cap_type_ls].shift()
            else:
                df[cap_type_ls] = df[cap_type_ls].shift()
        df = pd.merge(left=df, right=crf, how='left',on=['year'], sort=False)
        df[cap_type_ls] = df[cap_type_ls].fillna(0)
        df[cap_type_ls] = df[cap_type_ls].multiply(df["crf"], axis="index")

        if 'r' in df.columns:
            df = df.reset_index().set_index(['r','year']).sort_index() #Sort to ensure rolling sum is correct

            df[nontrans_cap_type_ls] = (df.groupby('r')[nontrans_cap_type_ls].rolling(sys_eval_years).sum()).reset_index(level=0, drop=True) 
            df[trans_cap_type_ls] = (df.groupby('r')[trans_cap_type_ls].rolling(trans_crp).sum()).reset_index(level=0, drop=True)  
            df = df.reset_index()
            
        else:
            df[nontrans_cap_type_ls] = df[nontrans_cap_type_ls].rolling(sys_eval_years).sum()
            df[trans_cap_type_ls] = df[trans_cap_type_ls].rolling(trans_crp).sum()
            df = df.reset_index()
            
        # Remove years before first modeled year
        keep_yrs = list(range(firstmodelyear, lastmodelyear + addyears + 1))
        df = df.loc[df.year.isin(keep_yrs)]

        #For operation costs, simply fill missing years with model year values.
        # Assuming sys_eval_years = 20, operation payments last for 20 yrs starting in the modeled
        # year, so fill 19 empty years after the modeled year.

        # Set NaN values to 0 for missing costs in simulation years. 
        # This approach prevents incorrect forward-filling from earlier years into years
        # where the cost is actually zero (since GAMS drops all zeros).
        df.loc[df['year'].isin(sim_years), op_type_ls] = df.loc[df['year'].isin(sim_years), op_type_ls].fillna(0)

        if 'r' in df.columns:
            df.loc[:,op_type_ls] = df.groupby('r')[op_type_ls].fillna(method='ffill', limit=sys_eval_years-1)
        else:
            df.loc[:,op_type_ls] = df[op_type_ls].fillna(method='ffill', limit=sys_eval_years-1)
        df = df.fillna(0)
        df = pd.melt(df.reset_index(), id_vars=id_cols, value_vars=cap_type_ls + op_type_ls, var_name='cost_cat', value_name= 'Cost (Bil $)')
        
    #Add Dicounted Cost column (including for annualized)
    df['Discounted Cost (Bil $)'] = df['Cost (Bil $)'] / (1 + d)**(df['year'] - y0)
    return df

def pre_avgprice(dfs, **kw):
    #Depending on whether 'National' or 'BA'-level average cost if specified
    if kw['reg'] == 'National':
        df = pre_systemcost(dfs, annualize=True, shift_capital=kw['shift_capital'])
        #Read in load
        df_load = dfs['q']
        df_load_nat = df_load[df_load['type'] == 'load'].groupby('year')['q'].sum()
        df_load_nat = df_load_nat.to_frame()
        full_yrs = list(range(int(df['year'].min()), int(df['year'].max()) + 1))
        df_load_nat = df_load_nat.reindex(full_yrs)
        df_load_nat = df_load_nat.interpolate(method='ffill')

        df_natavgprice = pd.merge(left=df, right=df_load_nat, how='left',on=['year'], sort=False)
        df_natavgprice['Average cost ($/MWh)'] = df_natavgprice['Cost (Bil $)'] * 1e9 / df_natavgprice['q']

        return df_natavgprice

    elif kw['reg'] == 'BA':
        df = dfs['sc']
        #apply inflation and adjust to billion dollars
        df['Cost (Bil $)'] = inflate_series(df['Cost (Bil $)']) * 1e-9

        cap_type_ls, op_type_ls = gather_cost_types(df)

        df_hours_map = pd.read_csv(this_dir_path + '/in/reeds2/m_map.csv')
        df_hours_width = pd.read_csv(this_dir_path + '/in/reeds2/m_bar_width.csv')
        df_hours_map = pd.merge(left=df_hours_map, right=df_hours_width, how='left',on=['display'],sort=False)
        df_hours_map.dropna(inplace=True)
        df_hours_map = df_hours_map.drop(columns = ['display'])
        df_hours_map.columns = ["timeslice","hours"]

        #-------Capital and operational costs--------
        df = df.groupby(['cost_cat','rb','year',])['Cost (Bil $)'].sum().reset_index()

        region_ls = df['rb'].unique().tolist()

        #Turn each cost category into a column
        df = df.pivot_table(index=['year'], columns=['rb','cost_cat'], values='Cost (Bil $)')
        #Add rows for all years (including 20 years after end year) and fill
        full_yrs = list(range(df.index.min() - 19, df.index.max() + 21))
        df = df.reindex(full_yrs)
        #For capital costs, multiply by CRF to annualize, and sum over previous 20 years.
        #This requires 20 years before 2010 to sum properly, and we need to shift capital dataframe down
        #so that capital payments start in the year after the investment was made
        crf = dfs['crf']
        crf = crf.set_index('year').reindex(full_yrs)
        crf = crf.interpolate(method ='linear')
        crf['crf'] = crf['crf'].fillna(method='bfill')
        df = pd.merge(left=df, right=crf, how='left',on=['year'], sort=False)
        colname_ls = pd.MultiIndex.from_product([region_ls, cap_type_ls],names=['rb', 'cost_cat'])
        colname_ls = [c for c in colname_ls if c in df.columns.tolist()]
        df[colname_ls] = df[colname_ls].shift().fillna(0)
        df[colname_ls] = df[colname_ls].multiply(df["crf"], axis="index")
        df[colname_ls] = df[colname_ls].rolling(20).sum()
        df = df.drop(columns = ['crf'])
        #Remove years before 2010
        full_yrs = list(range(df.index.min() + 19, df.index.max() + 1))
        df = df.reindex(full_yrs)

        #For operation costs, simply fill missing years with model year values.
        colname_ls = pd.MultiIndex.from_product([region_ls, op_type_ls],names=['rb', 'cost_cat'])
        colname_ls = [c for c in colname_ls if c in df.columns.tolist()]
        df[colname_ls] = df[colname_ls].fillna(method='ffill')
        #The final year should only include capital payments because operation payments last for 20 yrs starting
        #in the model year, whereas capital payments last for 20 yrs starting in the year after the model year.
        df.loc[df.index.max(), colname_ls] = 0
        df = df.fillna(0)

        df = df.T
        df.index = pd.MultiIndex.from_tuples(df.index.values, names=('rb','cost_cat'))
        df = df.reset_index()
        df = pd.melt(df, id_vars=['rb','cost_cat'], value_vars=df.columns.tolist()[2:], var_name='year', value_name= 'Cost (Bil $)')
        df = df.pivot_table(index=['year','rb'], columns=['cost_cat'], values='Cost (Bil $)')
        df = df.reset_index(level='rb')

        #Add capacity payment for existing (pre-2010) generators (in billion $)
        df_existingpayment = dfs['existcap']
        df_existingpayment['existingcap'] = inflate_series(df_existingpayment['existingcap'])
        df = pd.merge(left=df, right=df_existingpayment, how='left',on=['year','rb'], sort=False)
        df = df.fillna(0)
        df['inv_investment_capacity_costs'] = df['inv_investment_capacity_costs']+df['existingcap']
        df = df.drop(columns = 'existingcap')
        df = pd.melt(df.reset_index(), id_vars=['year','rb'], value_vars=df.columns.tolist()[2:], var_name='cost_cat', value_name= 'Cost (Bil $)')

        #-------Capacity trading--------
        df_captrade = dfs['captrade']
        df_captrade = df_captrade.groupby(['rb_out', 'rb_in', 'season', 'year'])['Amount (MW)'].sum().reset_index()

        df_capprice = dfs['p']
        df_capprice = df_capprice.loc[df_capprice['type'] == 'res_marg'].reset_index()
        df_capprice = df_capprice[df_capprice.columns[3:]]
        df_capprice.columns = ['rb_out','season','year', 'p']

        df_captrade = pd.merge(left=df_captrade, right=df_capprice, how='left',on=['rb_out','season','year'], sort=False)
        df_captrade = df_captrade.dropna()
        df_captrade['cost_rb_out'] = df_captrade['p'] * df_captrade['Amount (MW)'] / 1e9  #in billion dollars

        df_capimportcost = df_captrade.groupby(['rb_in','year',])['cost_rb_out'].sum().reset_index()
        df_capexportcost = df_captrade.groupby(['rb_out','year',])['cost_rb_out'].sum().reset_index()
        df_capexportcost['cost_rb_out'] = -df_capexportcost['cost_rb_out']

        df_capimportcost['cost_cat'] = 'cap_trade_import_cost'
        df_capimportcost.columns = ['rb','year','Cost (Bil $)','cost_cat']
        df_capimportcost = df_capimportcost[['year','rb','cost_cat','Cost (Bil $)']]
        df_capexportcost['cost_cat'] = 'cap_trade_export_cost'
        df_capexportcost.columns = ['rb','year','Cost (Bil $)','cost_cat']
        df_capexportcost = df_capexportcost[['year','rb','cost_cat','Cost (Bil $)']]
        df_captradecost = pd.concat([df_capimportcost,df_capexportcost], sort=False)

        #-------Energy trading--------
        df_gen = dfs['gen']
        df_gen = df_gen.groupby(['r', 'timeslice', 'year'])['Generation (GW)'].sum().reset_index()

        df_energyprice = dfs['p']
        df_energyprice = df_energyprice.loc[df_energyprice['type'] == 'load'].reset_index()
        df_energyprice = df_energyprice[df_energyprice.columns[3:]]
        df_energyprice.columns = ['r', 'timeslice', 'year', 'p']

        df_powfrac_up = dfs['powerfrac_upstream']
        df_powfrac_down = dfs['powerfrac_downstream']
        df_powfrac_up = df_powfrac_up.loc[df_powfrac_up['r'] != df_powfrac_up['rr'] ].reset_index()
        df_powfrac_down = df_powfrac_down.loc[df_powfrac_down['r'] != df_powfrac_down['rr'] ].reset_index()

        df_energyimport = pd.merge(left=df_powfrac_up, right=df_gen, how='left',on=['r','timeslice','year'], sort=False)
        df_energyimport = pd.merge(left=df_energyimport, right=df_energyprice, how='left',left_on=['rr','timeslice','year'], right_on=['r','timeslice','year'], sort=False)
        df_energyimport = df_energyimport.drop(columns = 'r_y')
        df_energyimport.columns = ['index', 'r', 'rr', 'timeslice', 'year', 'frac', 'Generation (GW)','p']
        df_energyimport = pd.merge(left=df_energyimport, right=df_hours_map, how='left',on=['timeslice'], sort=False)
        df_energyimport['importcost (Bil $)'] = df_energyimport['frac'] *df_energyimport['Generation (GW)'] * df_energyimport['p'] * df_energyimport['hours'] / 1e9
        df_energyimportcost = df_energyimport.groupby(['r', 'year'])['importcost (Bil $)'].sum().reset_index()

        df_energyexport = df_powfrac_down.groupby(['rr', 'timeslice', 'year'])['frac'].sum().reset_index()
        df_energyexport.columns = ['r', 'timeslice', 'year','frac']
        df_energyexport= pd.merge(left=df_energyexport, right=df_gen, how='left',on=['r','timeslice','year'], sort=False)
        df_energyexport = pd.merge(left=df_energyexport, right=df_energyprice, how='left',on=['r','timeslice','year'], sort=False)
        df_energyexport = pd.merge(left=df_energyexport, right=df_hours_map, how='left',on=['timeslice'], sort=False)

        df_energyexport['exportcost (Bil $)'] = df_energyexport['frac'] *df_energyexport['Generation (GW)'] * df_energyexport['p'] * df_energyexport['hours'] / 1e9
        df_energyexportcost = df_energyexport.groupby(['r', 'year'])['exportcost (Bil $)'].sum().reset_index()
        df_energyexportcost['exportcost (Bil $)'] = -df_energyexportcost['exportcost (Bil $)']

        df_energyimportcost['cost_cat'] = 'energy_trade_import_cost'
        df_energyimportcost.columns = ['rb','year','Cost (Bil $)','cost_cat']
        df_energyimportcost = df_energyimportcost[['year','rb','cost_cat','Cost (Bil $)']]
        df_energyexportcost['cost_cat'] = 'energy_trade_export_cost'
        df_energyexportcost.columns = ['rb','year','Cost (Bil $)','cost_cat']
        df_energyexportcost = df_energyexportcost[['year','rb','cost_cat','Cost (Bil $)']]
        df_energytradecost = pd.concat([df_energyimportcost,df_energyexportcost], sort=False)

        #-------Combine with load to calculate average cost--------
        df = pd.concat([df,df_captradecost,df_energytradecost], sort=False)

        df_load = dfs['q']
        df_load_ba = df_load[df_load['type'] == 'load'].groupby(['year','rb'])['q'].sum().reset_index()
        df_load_ba.columns = ['year','rb','load (MWh)']

        df_baavgprice = pd.merge(left=df, right=df_load_ba, how='left',on=['year','rb'], sort=False)
        df_baavgprice = df_baavgprice.dropna()
        df_baavgprice['Average cost ($/MWh)'] = df_baavgprice['Cost (Bil $)'] * 1e9 / df_baavgprice['load (MWh)']

        return df_baavgprice

def pre_abatement_cost(dfs, **kw):
    if 'objective' in kw and kw['objective'] is True:
        #Preprocess costs
        df_sc = pre_systemcost(dfs, objective=True, shift_capital=kw['shift_capital'])
        df_sc['type'] = 'Cost (Bil $)'
        df_sc.rename(columns={'Cost (Bil $)':'val'}, inplace=True)
        #Preprocess emissions
        df_co2 = dfs['emit']
        df_co2.rename(columns={'CO2 (MMton)':'val'}, inplace=True)
        df_co2['val'] = df_co2['val'] * 1e-3 #converting to billion metric tons
        #Multiply by pvfonm to convert to total objective level of emissions for that year
        df_co2 = pd.merge(left=df_co2, right=dfs['pvf_onm'], how='left', on=['year'], sort=False)
        df_co2['val'] = df_co2['val'] * df_co2['pvfonm']
        df_co2.drop(['pvfonm'], axis='columns',inplace=True)
        #Add type and cost_cat columns so we can concatenate
        df_co2['type'] = 'CO2 (Bil metric tons)'
        df_co2['cost_cat'] = 'CO2 (Bil metric tons)'
        #Concatenate costs and emissions
        df = pd.concat([df_sc, df_co2],sort=False,ignore_index=True)

    elif 'annualize' in kw and kw['annualize'] is True:
        #Preprocess costs
        df_sc = pre_systemcost(dfs, annualize=True, crf_from_user=True, shift_capital=kw['shift_capital'])
        df_sc = sum_over_cols(df_sc, group_cols=['year','cost_cat'], drop_cols=['Discounted Cost (Bil $)'])
        df_sc['type'] = 'Cost (Bil $)'
        df_sc.rename(columns={'Cost (Bil $)':'val'}, inplace=True)
        #Preprocess emissions
        df_co2 = dfs['emit']
        df_co2.rename(columns={'CO2 (MMton)':'val'}, inplace=True)
        df_co2['val'] = df_co2['val'] * 1e-3 #converting to billion metric tons
        full_yrs = list(range(df_sc['year'].min(), df_sc['year'].max() + 1))
        df_co2 = df_co2.set_index('year').reindex(full_yrs).reset_index()
        df_co2['val'] = df_co2['val'].fillna(method='ffill')
        df_co2['type'] = 'CO2 (Bil metric tons)'
        df_co2['cost_cat'] = 'CO2 (Bil metric tons)'
        #Concatenate costs and emissions
        df = pd.concat([df_sc, df_co2],sort=False,ignore_index=True)
        #Add discounted value column
        d = float(core.GL['widgets']['var_discount_rate'].value)
        y0 = int(core.GL['widgets']['var_pv_year'].value)
        df['disc val'] = df['val'] / (1 + d)**(df['year'] - y0)
        #Add cumulative columns
        df['cum val'] = df.groupby('cost_cat')['val'].cumsum()
        df['cum disc val'] = df.groupby('cost_cat')['disc val'].cumsum()

    return df

def add_class(df, **kw):
    cond = df['tech'].str.contains('_', regex=False)
    #Assume class is at the end, after the final underscore:
    df.loc[cond, 'class']='class_' + df.loc[cond, 'tech'].str.split('_').str[-1]
    return df

def sort_timeslices(df, **kw):
    ### Use either h or timeslice as column name
    timeslice = 'timeslice' if 'timeslice' in df.columns else 'h'
    timeslices = df[timeslice].unique()
    ### If using h17, apply custom labels
    if len(timeslices) <= 17:
        replace = {
            'h1': 'h01 (Summer 10pm-6am)',
            'h2': 'h02 (Summer 6am-1pm)',
            'h3': 'h03 (Summer 1pm-5pm)',
            'h4': 'h04 (Summer 5pm-10pm)',
            'h5': 'h05 (Fall 10pm-6am)',
            'h6': 'h06 (Fall 6am-1pm)',
            'h7': 'h07 (Fall 1pm-5pm)',
            'h8': 'h08 (Fall 5pm-10pm)',
            'h9': 'h09 (Winter 10pm-6am)',
            'h10': 'h10 (Winter 6am-1pm)',
            'h11': 'h11 (Winter 1pm-5pm)',
            'h12': 'h12 (Winter 5pm-10pm)',
            'h13': 'h13 (Spring 10pm-6am)',
            'h14': 'h14 (Spring 6am-1pm)',
            'h15': 'h15 (Spring 1pm-5pm)',
            'h16': 'h16 (Spring 5pm-10pm)',
            'h17': 'h17 (Summer Peak)',
        }
        df = df.replace({timeslice:replace}).copy()
        return df
    ### Sort it
    df = df.sort_values(timeslice, ascending=True)
    return df

def pre_gen_w_load(dfs, **kw):
    #Aggregate results to national
    dfs['gen'] = sum_over_cols(dfs['gen'], drop_cols=['rb','vintage'], group_cols=['tech', 'year'])
    dfs['gen_uncurt'] = sum_over_cols(dfs['gen_uncurt'], drop_cols=['rb','vintage'], group_cols=['tech', 'year'])
    #Outer join generation, fill any missing gen with 0, and then fill missing gen_uncurt with gen
    df = pd.merge(left=dfs['gen'], right=dfs['gen_uncurt'], how='outer', on=['tech','year'], sort=False)
    df['Gen (TWh)'].fillna(0, inplace=True)
    df['Gen Uncurt (TWh)'].fillna(df['Gen (TWh)'], inplace=True)
    #Scale generation to TWh
    df[['Gen (TWh)','Gen Uncurt (TWh)']] = df[['Gen (TWh)','Gen Uncurt (TWh)']] * 1e-6
    #Scale Load to TWh
    dfs['load']['TWh'] = dfs['load']['TWh'] * 1e-6
    #pivot load out to include losses columns
    dfs['load'] = dfs['load'].pivot_table(index=['year'], columns='type', values='TWh').reset_index()
    #Join Load
    df = pd.merge(left=df, right=dfs['load'], how='left', on=['year'], sort=False)
    #Calculate Gen Fracs
    df['Gen Frac of Load'] = df['Gen (TWh)'] / df['load']
    df['Gen Frac of Load Plus Stor/Trans Loss'] = df['Gen (TWh)'] / (df['load'] + df['storage'] + df['trans'])
    df['Gen Uncurt Frac of Load'] = df['Gen Uncurt (TWh)'] / df['load']
    df['Gen Uncurt Frac of Load Plus All Losses'] = df['Gen Uncurt (TWh)'] / (df['load'] + df['storage'] + df['trans'] + df['curt'])
    return df

def pre_valnew(df, **kw):
    #Remove unused columns
    df = df[~df['output'].isin(['inv_cap_ratio'])].copy()
    #Apply inflate_series() to the 'value' column for all rows with 'output' starting with 'val_'
    val_cond = df['output'].str.startswith('val_')
    df.loc[val_cond, 'value'] = inflate_series(df.loc[val_cond, 'value'])
    df_bench = df[df['tech'] == 'benchmark'].copy().drop(columns=['tech'])
    df = df[df['tech'] != 'benchmark'].copy()
    df_bench['output'] = df_bench['output'] + '_bench'
    df_bench_loc = df_bench[df_bench['rb'] != 'sys'].copy()
    df_bench_sys = df_bench[df_bench['rb'] == 'sys'].copy()
    df_bench_sys = df_bench_sys.drop(columns=['rb'])
    df_bench_loc['output'] = df_bench_loc['output'] + '_loc'
    df_bench_sys['output'] = df_bench_sys['output'] + '_sys'
    #Pivot out the 'output' column
    df = df.pivot_table(index=['tech','rb','year'], columns='output', values='value').reset_index()
    df_bench_loc = df_bench_loc.pivot_table(index=['rb','year'], columns='output', values='value').reset_index()
    df_bench_sys = df_bench_sys.pivot_table(index=['year'], columns='output', values='value').reset_index()
    #Merge the benchmark data back in
    df = pd.merge(left=df, right=df_bench_loc, how='left', on=['rb','year'], sort=False)
    df = pd.merge(left=df, right=df_bench_sys, how='left', on=['year'], sort=False)
    df = df.fillna(0)
    val_cols_base = ['val_load','val_resmarg','val_opres','val_rps']
    val_cols = [c for c in val_cols_base if c in df]
    val_cols_sys = [c + '_sys' for c in val_cols_base if c + '_sys' in df]
    val_cols_bench_loc = [c + '_bench_loc' for c in val_cols_base if c + '_bench_loc' in df]
    val_cols_bench_sys = [c + '_bench_sys' for c in val_cols_base if c + '_bench_sys' in df]
    df['val_tot'] = df[val_cols].sum(axis=1)
    df['val_tot_sys'] = df[val_cols_sys].sum(axis=1)
    df['val_tot_bench_loc'] = df[val_cols_bench_loc].sum(axis=1)
    df['val_tot_bench_sys'] = df[val_cols_bench_sys].sum(axis=1)
    df['vf'] = (df['val_tot']/df['mwh']) / (df['val_tot_bench_sys']/df['mwh_bench_sys'])
    df['vf_temporal'] = (df['val_tot_sys']/df['mwh']) / (df['val_tot_bench_sys']/df['mwh_bench_sys'])
    df['vf_spatial'] = (df['val_tot_bench_loc']/df['mwh_bench_loc']) / (df['val_tot_bench_sys']/df['mwh_bench_sys'])
    df['vf_temporal_local'] = (df['val_tot']/df['mwh']) / (df['val_tot_bench_loc']/df['mwh_bench_loc'])
    df['vf_spatial_simult'] = (df['val_tot']/df['mwh']) / (df['val_tot_sys']/df['mwh'])
    df['vf_interaction'] = df['vf_spatial_simult'] / df['vf_spatial']
    df['vf_load'] = (df['val_load']/df['mwh']) / (df['val_load_bench_sys']/df['mwh_bench_sys'])
    df['vf_resmarg'] = (df['val_resmarg']/df['mwh']) / (df['val_resmarg_bench_sys']/df['mwh_bench_sys'])
    df['vf_resmarg_permw'] = (df['val_resmarg']/df['mw']) / (df['val_resmarg_bench_sys']/df['mw_bench_sys'])
    return df

def pre_val_streams(dfs, **kw):
    index_cols = ['tech', 'vintage', 'rb', 'year']
    inv_vars = ['inv','inv_refurb','upgrades','invtran','inv_rsc']
    cap_vars = ['cap','captran']
    cum_vars = ['gen','cap','opres','storage_in','captran','flow','opres_flow','prmtrade','storage_in_pvb_p','storage_in_pvb_g','cap_sdbin','storage_level','recs','gen_pvb_p','gen_pvb_b','produce']

    if 'remove_inv' in kw:
        dfs['vs'] = dfs['vs'][~dfs['vs']['var_name'].isin(inv_vars)].copy()

    if 'uncurt' in kw:
        #For techs that are in gen_uncurt, use gen_uncurt instead of gen
        dfs['gen'] = dfs['gen'][~dfs['gen']['tech'].isin(dfs['gen_uncurt']['tech'].unique())].copy()
        dfs['gen'] = pd.concat([dfs['gen'], dfs['gen_uncurt']],sort=False,ignore_index=True)

    if 'investment_only' in kw:
        #Analyze only investment years
        #First, use the capacity/investment linking equations with the investment and capacity variables to find the
        #scaling factors between investment and capacity value streams.
        linking_eqs = ['eq_cap_new_noret','eq_cap_new_retub','eq_cap_new_retmo','eq_cap_upgrade','eq_captran'] #eq_cap_new_retmo also includes previous year's CAP, is this bad?!
        df_vs_links = dfs['vs'][dfs['vs']['con_name'].isin(linking_eqs)].copy()
        df_vs_inv = df_vs_links[df_vs_links['var_name'].isin(inv_vars)].copy()
        df_vs_cap = df_vs_links[df_vs_links['var_name'].isin(cap_vars)].copy()
        df_vs_inv = sum_over_cols(df_vs_inv, group_cols=index_cols, drop_cols=['var_name','con_name'])
        df_vs_cap = sum_over_cols(df_vs_cap, group_cols=index_cols, drop_cols=['var_name','con_name'])
        #merge inner with df_vs_inv so that we're only looking at cumulative value streams in investment years.
        df_scale = pd.merge(left=df_vs_inv, right=df_vs_cap, how='inner', on=index_cols, sort=False)
        df_scale['mult'] = df_scale['$_x'] / df_scale['$_y'] * -1
        df_scale = df_scale[index_cols + ['mult']]
        #Gather cumulative value streams. NEED TO ADD TRANSMISSION
        df_cum = dfs['vs'][dfs['vs']['var_name'].isin(cum_vars)].copy()
        #Left merge with df_scale to keep only the cumulative streams in investment years
        df_cum = pd.merge(left=df_scale, right=df_cum, how='left', on=index_cols, sort=False)
        #Scale the cumulative value streams
        df_cum['$'] = df_cum['$'] * df_cum['mult']
        df_cum.drop(['mult'], axis='columns',inplace=True)
        #Concatenate modified cumulative value streams with the rest of the value streams
        dfs['vs'] = dfs['vs'][dfs['vs']['var_name'].isin(inv_vars)].copy()
        dfs['vs'] = pd.concat([dfs['vs'], df_cum],sort=False,ignore_index=True)
        #Adjust generation based on the same scaling factor. Not sure this is exactly right, but if
        #value streams for GEN have scaled, it makes sense to attribute this to quantity of energy being scaled,
        #rather than prices changing.
        dfs['gen'] = pd.merge(left=df_scale, right=dfs['gen'], how='left', on=index_cols, sort=False)
        dfs['gen']['MWh'] = dfs['gen']['MWh'] * dfs['gen']['mult']
        dfs['gen'].drop(['mult'], axis='columns',inplace=True)

    #apply inflation
    dfs['vs']['$'] = inflate_series(dfs['vs']['$'])

    if 'value_factors' in kw:
        #sum over vintage in both generation and value streams:
        df_gen = sum_over_cols(dfs['gen'], group_cols=['tech','rb','year'], val_cols=['MWh'])
        df = sum_over_cols(dfs['vs'], group_cols=['tech','rb','year','con_name'], val_cols=['$'])
        #Reduce value streams to only the ones we care about
        df = df[df['con_name'].isin(vf_valstreams)].copy()
        #Include all con_name options for each tech,rb,year combo and fill na with zero
        df = df.pivot_table(index=['tech','rb','year'], columns='con_name', values='$').reset_index()
        df = pd.melt(df, id_vars=['tech','rb','year'], var_name='con_name', value_name= '$')
        df['$'].fillna(0, inplace=True)
        #convert value streams from bulk $ as of discount year to annual as of model year
        df = pd.merge(left=df, right=dfs['pvf_onm'], how='left', on=['year'], sort=False)
        df['$'] = df['$'] / dfs['cost_scale'].iloc[0,0] / df['pvfonm']
        df.drop(['pvfonm'], axis='columns',inplace=True)

        #get requirement prices and quantities and build benchmark value streams
        dfs['p']['p'] = inflate_series(dfs['p']['p'])
        df_bm = pd.merge(left=dfs['q'], right=dfs['p'], how='left', on=['type', 'subtype', 'rb', 'timeslice', 'year'], sort=False)
        df_bm['p'].fillna(0, inplace=True)
        #Add con_name:
        types = ['load','res_marg','oper_res','state_rps','curt_realize','curt_cause'] #the curt ones don't exist, they are just placeholders for the mapping.
        df_bm = df_bm[df_bm['type'].isin(types)].copy()
        df_con_type = pd.DataFrame({'type':types,'con_name':vf_valstreams})
        df_bm = pd.merge(left=df_bm, right=df_con_type, how='left', on=['type'], sort=False)
        #drop type and subtype because we're using con_name from here on
        df_bm.drop(['type','subtype'], axis='columns', inplace=True)
        #columns of df_bm at this point are rb,timeslice,year,con_name,p,q

        #Calculate annual load for use in benchmarks
        df_load = dfs['q'][dfs['q']['type']=='load'].copy()
        df_load = sum_over_cols(df_load, group_cols=['rb', 'year'], val_cols=['q'])

        #All-in benchmarks. These assume the benchmark tech provides all value streams at requirement levels,
        #and prices are calculated by dividing value by load.
        df_bm_allin = df_bm.copy()
        df_bm_allin['$'] = df_bm_allin['p'] * df_bm_allin['q']
        df_bm_allin = sum_over_cols(df_bm_allin, group_cols=['con_name', 'rb', 'year'], val_cols=['$'])
        df_bm_allin = pd.merge(left=df_bm_allin, right=df_load, how='left', on=['rb', 'year'], sort=False)

        #local all-in (weighted) benchmark. First calculate prices as $ of requirement divided by MWh energy
        df_bm_allin_loc = df_bm_allin.copy()
        df_bm_allin_loc['$ all-in loc'] = df_bm_allin_loc['$'] / df_bm_allin_loc['q']
        df_bm_allin_loc.drop(['$','q'], axis='columns', inplace=True)
        df = pd.merge(left=df, right=df_bm_allin_loc, how='left', on=['year','rb','con_name'], sort=False)

        #system-wide all-in (weighted) benchmark
        df_bm_allin_sys = sum_over_cols(df_bm_allin, group_cols=['year','con_name'], val_cols=['$','q'])
        df_bm_allin_sys['$ all-in sys'] = df_bm_allin_sys['$'] / df_bm_allin_sys['q']
        df_bm_allin_sys.drop(['$','q'], axis='columns', inplace=True)
        df = pd.merge(left=df, right=df_bm_allin_sys, how='left', on=['year','con_name'], sort=False)

        #Flat-block benchmarks. These assume the tech provides energy + reserve margin only.
        flatblock_cons = ['eq_supply_demand_balance','eq_reserve_margin']
        df_bm_flat_loc = df_bm[df_bm['con_name'].isin(flatblock_cons)].copy()
        #Add hours
        df_hours = pd.read_csv(this_dir_path + '/in/reeds2/hours.csv')
        df_bm_flat_loc = pd.merge(left=df_bm_flat_loc, right=df_hours, how='left', on=['timeslice'], sort=False)
        #First we calculate p as annual $ for 1 MW flat-block tech,
        #so we need to multiply eq_supply_demand_balance price ($/MWh) by hours (eq_reserve_margin price is fine as is) and sum across timeslices
        load_cond = df_bm_flat_loc['con_name'] == 'eq_supply_demand_balance'
        df_bm_flat_loc.loc[load_cond, 'p'] = df_bm_flat_loc.loc[load_cond, 'p'] * df_bm_flat_loc.loc[load_cond, 'hours']
        df_bm_flat_loc = sum_over_cols(df_bm_flat_loc, group_cols=['year','rb','con_name'], val_cols=['p'])
        #Convert to $/MWh from $/MW: 1 MW flat block produces 8760 MWh annual energy.
        df_bm_flat_loc['$ flat loc'] = df_bm_flat_loc['p'] / 8760
        df_bm_flat_loc.drop(['p'], axis='columns', inplace=True)
        df = pd.merge(left=df, right=df_bm_flat_loc, how='left', on=['year','rb','con_name'], sort=False)

        #system flat benchmark. We weight the local prices by annual load
        df_bm_flat_sys = pd.merge(left=df_bm_flat_loc, right=df_load, how='left', on=['rb', 'year'], sort=False)
        df_bm_flat_sys['$'] = df_bm_flat_sys['$ flat loc'] * df_bm_flat_sys['q']
        df_bm_flat_sys = sum_over_cols(df_bm_flat_sys, group_cols=['con_name', 'year'], val_cols=['$','q'])
        df_bm_flat_sys['$ flat sys'] = df_bm_flat_sys['$'] / df_bm_flat_sys['q']
        df_bm_flat_sys.drop(['$','q'], axis='columns', inplace=True)
        df = pd.merge(left=df, right=df_bm_flat_sys, how='left', on=['year','con_name'], sort=False)

        #Merge with generation so we can calculate $ associated with all benchmarks
        df = pd.merge(left=df, right=df_gen, how='left', on=['tech','rb','year'], sort=False)
        #Now convert all prices to values
        vf_cols = ['$ all-in loc','$ all-in sys','$ flat loc','$ flat sys']
        df[vf_cols] = df[vf_cols].multiply(df['MWh'], axis="index")
        df.drop(['MWh'], axis='columns',inplace=True)
        df_gen['con_name'] = 'MWh'
        df_gen.rename(columns={'MWh': '$'}, inplace=True) #So we can concatenate
        for vf_col in vf_cols:
            df_gen[vf_col] = df_gen['$'] #Duplicating MWh across all the value columns
        df = pd.concat([df, df_gen],sort=False,ignore_index=True)
        df = df.fillna(0)
        return df

    #Use pvf_capital to convert to present value as of data year (model year for CAP and GEN but investment year for INV,
    #although i suppose certain equations, e.g. eq_cap_new_retmo also include previous year's CAP).
    df = pd.merge(left=dfs['vs'], right=dfs['pvf_cap'], how='left', on=['year'], sort=False)
    df['Bulk $'] = df['$'] / dfs['cost_scale'].iloc[0,0] / df['pvfcap']
    df.drop(['pvfcap', '$'], axis='columns',inplace=True)

    #Add total value and total cost
    # df_val = df[df['con_name'].isin(valuestreams)].copy()
    # df_val = sum_over_cols(df_val, group_cols=index_cols, drop_cols=['var_name','con_name'])
    # df_val['var_name'] = 'val_tot'
    # df_val['con_name'] = 'val_tot'
    # df_cost = df[df['con_name'].isin(coststreams)].copy()
    # df_cost = sum_over_cols(df_cost, group_cols=index_cols, drop_cols=['var_name','con_name'])
    # df_cost['var_name'] = 'cost_tot'
    # df_cost['con_name'] = 'cost_tot'
    # df = pd.concat([df, df_val, df_cost],sort=False,ignore_index=True)

    #Preprocess gen: convert from annual MWh to bulk MWh present value as of data year
    df_gen = dfs['gen'].groupby(index_cols, sort=False, as_index =False).sum()
    df_gen = pd.merge(left=df_gen, right=dfs['pvf_cap'], how='left', on=['year'], sort=False)
    df_gen = pd.merge(left=df_gen, right=dfs['pvf_onm'], how='left', on=['year'], sort=False)
    df_gen['MWh'] = df_gen['MWh'] * df_gen['pvfonm'] / df_gen['pvfcap'] #This converts to bulk MWh present value as of data year
    df_gen.rename(columns={'MWh': 'Bulk $'}, inplace=True) #So we can concatenate
    df_gen['var_name'] = 'MWh'
    df_gen['con_name'] = 'MWh'
    df_gen.drop(['pvfcap', 'pvfonm'], axis='columns',inplace=True)
    df = pd.concat([df, df_gen],sort=False,ignore_index=True)

    #Preprocess capacity: map i to n, convert from MW to kW, reformat columns to concatenate
    df_cap = dfs['cap']
    df_cap =  df_cap.groupby(index_cols, sort=False, as_index =False).sum()
    df_cap['MW'] = df_cap['MW'] * 1000 #Converting to kW
    df_cap.rename(columns={'MW': 'Bulk $'}, inplace=True) #So we can concatenate
    df_cap['var_name'] = 'kW'
    df_cap['con_name'] = 'kW'
    df = pd.concat([df, df_cap],sort=False,ignore_index=True)

    #Add discounted $ using interface year
    d = float(core.GL['widgets']['var_discount_rate'].value)
    y0 = int(core.GL['widgets']['var_pv_year'].value)
    df['Bulk $ Dis'] = df['Bulk $'] / (1 + d)**(df['year'] - y0) #This discounts $, MWh, and kW, important for NVOE, NVOC, LCOE, etc.

    #Add new columns
    df['tech, vintage'] = df['tech'] + ', ' + df['vintage']
    df['var, con'] = df['var_name'] + ', ' + df['con_name']
    #Make adjusted con_name column where all objective costs are replaced with var_name, con_name
    df['con_adj'] = df['con_name']
    df.loc[df['con_name'].isin(['eq_objfn_inv','eq_objfn_op']), 'con_adj'] = df.loc[df['con_name'].isin(['eq_objfn_inv','eq_objfn_op']), 'var, con']

    if 'competitiveness' in kw:
        df = df[index_cols+['Bulk $ Dis','con_name']]

        #Total cost for each tech
        df_cost = df[df['con_name'].isin(coststreams)].copy()
        df_cost.rename(columns={'Bulk $ Dis':'Cost $'}, inplace=True)
        df_cost = sum_over_cols(df_cost, group_cols=index_cols, drop_cols=['con_name'])
        df_cost['Cost $'] = df_cost['Cost $'] * -1

        #Total Value for each tech
        df_value = df[df['con_name'].isin(vf_valstreams)].copy()
        df_value.rename(columns={'Bulk $ Dis':'Value $'}, inplace=True)
        df_value = sum_over_cols(df_value, group_cols=index_cols, drop_cols=['con_name'])

        #Total energy for each tech
        df_energy = df[df['con_name'] == 'MWh'].copy()
        df_energy.rename(columns={'Bulk $ Dis':'MWh'}, inplace=True)
        df_energy = sum_over_cols(df_energy, group_cols=index_cols, drop_cols=['con_name'])

        #Benchmark price, excluding national_generation constraint, with the assumption that this constraint
        #represents a simple forcing function rather than a policy. If the constraint represents a CES or RPS policy e.g.,
        #we probably should use 'tot' rather than the sum of 'load','res_marg','oper_res', and 'state_rps'.
        df_benchmark = pre_prices(dfs)
        df_benchmark = df_benchmark[df_benchmark['type'].isin(['q_load','load','res_marg','oper_res','state_rps'])].copy()
        df_benchmark = sum_over_cols(df_benchmark, group_cols=['type','year'], val_cols=['$'])
        df_benchmark = df_benchmark.pivot_table(index=['year'], columns=['type'], values='$').reset_index()
        df_benchmark['P_b'] = (df_benchmark['load'] + df_benchmark['res_marg'] + df_benchmark['oper_res'] + df_benchmark['state_rps']) / df_benchmark['q_load']
        df_benchmark = df_benchmark[['year','P_b']].copy()

        #Merge all the dataframes
        df = pd.merge(left=df_cost, right=df_energy, how='left', on=index_cols, sort=False)
        df = pd.merge(left=df, right=df_value, how='left', on=index_cols, sort=False)
        df = pd.merge(left=df, right=df_benchmark, how='left', on=['year'], sort=False)

        #Build metrics
        df['LCOE'] = df['Cost $'] / df['MWh']
        df['LVOE'] = df['Value $'] / df['MWh']
        df['NVOE'] = df['LVOE'] - df['LCOE']
        df['BCR'] = df['Value $'] / df['Cost $']
        df['PLCOE'] = df['P_b'] * df['Cost $'] / df['Value $']
        df['value factor'] = df['LVOE'] / df['P_b']
        df['integration cost'] = df['P_b'] - df['LVOE']
        df['SLCOE'] = df['LCOE'] + df['integration cost']
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df

def pre_reduced_cost(df, **kw):
    df['irbv'] = df['tech'] + ' | ' + df['rb'] + ' | ' + df['bin'] + ' | ' + df['variable']
    return df

def pre_lcoe(dfs, **kw):
    #Apply inflation
    dfs['lcoe']['$/MWh'] = inflate_series(dfs['lcoe']['$/MWh'])
    #Merge with available capacity
    df = pd.merge(left=dfs['lcoe'], right=dfs['avail'], how='left', on=['tech', 'rb', 'year', 'bin'], sort=False)
    df['available MW'].fillna(0, inplace=True)
    df['available'] = 'no'
    df.loc[df['available MW'] > 0.001, 'available'] = 'yes'
    #Merge with chosen capacity
    df = pd.merge(left=df, right=dfs['inv'], how='left', on=['tech', 'vintage', 'rb', 'year', 'bin'], sort=False)
    df['chosen MW'].fillna(0, inplace=True)
    df['chosen'] = 'no'
    df.loc[df['chosen MW'] != 0, 'chosen'] = 'yes'
    #Add icrb column
    df['icrb'] = df['tech'] + ' | ' + df['vintage'] + ' | ' + df['rb'] + ' | ' + df['bin']
    return df

def pre_curt_new(dfs, **kw):
    df = pd.merge(left=dfs['gen_uncurt'], right=dfs['curt_rate'], how='left',on=['tech', 'rb', 'timeslice', 'year'], sort=False)
    df['Curt Rate']=df['Curt Rate'].fillna(0)
    if 'annual' in kw:
        df['MWh curt'] = df['Curt Rate'] * df['MWh uncurt']
        df = sum_over_cols(df, group_cols=['tech', 'rb', 'year'], drop_cols=['timeslice','Curt Rate'])
        df['Curt Rate'] = df['MWh curt'] / df['MWh uncurt']
        df['Curt Rate']=df['Curt Rate'].fillna(0)
    return df

def pre_cc_new(dfs, **kw):
    df = pd.merge(left=dfs['cap'], right=dfs['cc'], how='left',on=['tech', 'rb', 'season', 'year'], sort=False)
    df['CC Rate']=df['CC Rate'].fillna(0)
    return df

def pre_firm_cap(dfs, **kw):
    df_cap = dfs['cap']
    #Add seasons to capacity dataframe
    dftemp = pd.DataFrame({'season':dfs['firmcap']['season'].unique().tolist()})
    dftemp['temp'] = 1
    df_cap['temp'] = 1
    df_cap = pd.merge(left=df_cap, right=dftemp, how='left',on=['temp'], sort=False)
    df_cap.drop(columns=['temp'],inplace=True)
    df = pd.merge(left=df_cap, right=dfs['firmcap'], how='left',on=['tech', 'rb', 'year','season'], sort=False)
    df = df.fillna(0)
    df[['Capacity (GW)','Firm Capacity (GW)']] = df[['Capacity (GW)','Firm Capacity (GW)']] * 1e-3
    if 'ba' in kw and kw['ba'] is True:
        df['Capacity Credit'] = df['Firm Capacity (GW)'] / df['Capacity (GW)']
    return df

def pre_curt(dfs, **kw):
    df = pd.merge(left=dfs['gen_uncurt'], right=dfs['gen'], how='left',on=['tech', 'vintage', 'rb', 'year'], sort=False)
    df['MWh']=df['MWh'].fillna(0)
    df['Curt Rate'] = 1 - df['MWh']/df['MWh uncurt']
    df_re_n = sum_over_cols(dfs['gen_uncurt'], group_cols=['rb','year'], drop_cols=['tech','vintage'])
    df_re_nat = sum_over_cols(dfs['gen_uncurt'], group_cols=['year'], drop_cols=['tech','vintage','rb'])
    df_load_nat = sum_over_cols(dfs['load'], group_cols=['year'], drop_cols=['rb'])
    df_vrepen_n = pd.merge(left=dfs['load'], right=df_re_n, how='left',on=['rb', 'year'], sort=False)
    df_vrepen_n['VRE penetration n'] = df_vrepen_n['MWh uncurt'] / df_vrepen_n['MWh load']
    df_vrepen_n = df_vrepen_n[['rb','year','VRE penetration n']]
    df_vrepen_nat = pd.merge(left=df_load_nat, right=df_re_nat, how='left',on=['year'], sort=False)
    df_vrepen_nat['VRE penetration nat'] = df_vrepen_nat['MWh uncurt'] / df_vrepen_nat['MWh load']
    df_vrepen_nat = df_vrepen_nat[['year','VRE penetration nat']]
    df = pd.merge(left=df, right=df_vrepen_n, how='left',on=['rb', 'year'], sort=False)
    df = pd.merge(left=df, right=df_vrepen_nat, how='left',on=['year'], sort=False)
    return df

def pre_curt_iter(dfs, **kw):
    df_gen = dfs['gen_uncurt']
    df_curt = dfs['curt']
    df_gen = df_gen[df_gen['tech'].isin(df_curt['tech'].unique())].copy()
    df_gen['type'] = 'gen'
    df_curt['type'] = 'curt'
    df = pd.concat([df_gen, df_curt],sort=False,ignore_index=True)
    return df

def pre_cc_iter(dfs, **kw):
    df_cap = dfs['cap']
    df_cap_firm = dfs['cap_firm']
    df_cap = df_cap[df_cap['tech'].isin(df_cap_firm['tech'].unique())].copy()
    df_cap['type'] = 'cap'
    df_cap_firm['type'] = 'cap_firm'
    seasons = list(df_cap_firm['season'].unique())
    df_season = pd.DataFrame({'season':seasons,'temp':[1]*len(seasons)})
    df_cap['temp'] = 1
    df_cap = pd.merge(left=df_cap, right=df_season, how='left',on=['temp'], sort=False)
    df_cap.drop(['temp'], axis='columns',inplace=True)
    df = pd.concat([df_cap, df_cap_firm],sort=False,ignore_index=True)
    return df

def pre_cf(dfs, **kw):
    index_cols = ['tech', 'vintage', 'rb', 'year']
    dfs['cap'] =  dfs['cap'].groupby(index_cols, sort=False, as_index=False).sum()
    df = pd.merge(left=dfs['cap'], right=dfs['gen'], how='left',on=index_cols, sort=False)
    df['MWh']=df['MWh'].fillna(0)
    df['CF'] = df['MWh']/(df['MW']*8760)
    return df

def pre_duration(dfs, **kw):
    index_cols = ['tech', 'vintage', 'rb', 'year']
    dfs['duration'] =  dfs['duration'].groupby(index_cols, sort=False, as_index=False).sum()
    df = pd.merge(left=dfs['duration'], right=dfs['energy_capacity_MWh'], how='left',on=index_cols, sort=False)
    return df

def pre_h2_cf(dfs, **kw):
    index_cols = ['tech', 'rb', 'year']
    dfs['cap'] =  dfs['cap'].groupby(index_cols, sort=False, as_index=False).sum()
    df = pd.merge(left=dfs['cap'], right=dfs['prod'], how='left',on=index_cols, sort=False)
    df['Production (metric tons)']=df['Production (metric tons)'].fillna(0)
    df['CF'] = df['Production (metric tons)']/(df['Capacity (metric tons)']*8760)
    return df

def pre_neue(dfs, **kw):
    df = dfs.drop_duplicates('year', keep='last')
    return df

def pre_new_vre_cf(dfs, **kw):
    index_cols = ['tech', 'r', 'year']
    dfs['gen_new_uncurt'] = sum_over_cols(dfs['gen_new_uncurt'], group_cols=index_cols, val_cols=['MWh'])
    df = pd.merge(left=dfs['gen_new_uncurt'], right=dfs['cap_new'], how='inner',on=index_cols, sort=False)
    df['CF'] = df['MWh']/(df['MW']*8760)
    return df

def pre_vre_vs_stor(dfs, **kw):
    df_gen = dfs['gen'].copy()
    df_stor = dfs['stor'].copy()
    df_stor = df_stor[df_stor['type'] == 'in'].copy()
    df_gen = sum_over_cols(df_gen, group_cols=['technology', 'year'], val_cols=['Generation (TWh)'])
    df_stor = sum_over_cols(df_stor, group_cols=['technology', 'year'], val_cols=['Storage (TWh)'])
    df_gen['Generation (TWh)'] = df_gen['Generation (TWh)']/1e6
    df_stor['Storage (TWh)'] = df_stor['Storage (TWh)']/1e6
    df_wind = df_gen[df_gen['technology'].str.startswith('wind')].copy()
    df_pv = df_gen[df_gen['technology'].str.contains('upv|distpv')].copy()
    df_bat = df_stor[df_stor['technology'].str.startswith('battery')].copy()
    df_wind = sum_over_cols(df_wind, group_cols=['year'], val_cols=['Generation (TWh)'])
    df_pv = sum_over_cols(df_pv, group_cols=['year'], val_cols=['Generation (TWh)'])
    df_bat = sum_over_cols(df_bat, group_cols=['year'], val_cols=['Storage (TWh)'])
    df_storall = sum_over_cols(df_stor, group_cols=['year'], val_cols=['Storage (TWh)'])
    df_wind = df_wind.rename(columns={'Generation (TWh)': 'Wind (TWh)'}).set_index('year')
    df_pv = df_pv.rename(columns={'Generation (TWh)': 'PV (TWh)'}).set_index('year')
    df_bat = df_bat.rename(columns={'Storage (TWh)': 'Battery (TWh)'}).set_index('year')
    df_storall = df_storall.set_index('year')
    df = pd.concat([df_wind, df_pv, df_storall, df_bat], axis=1).fillna(0).reset_index().sort_values('year')
    df['VRE (TWh)'] = df['Wind (TWh)'] + df['PV (TWh)']
    return df

def pre_prices(dfs, **kw):
    #Apply inflation
    dfs['p']['p'] = inflate_series(dfs['p']['p'])
    #Join prices and quantities
    merge_cols = [c for c in ['type', 'subtype', 'rb', 'timeslice', 'year'] if c in dfs['q'].columns]
    df = pd.merge(left=dfs['q'], right=dfs['p'], how='left', on=merge_cols, sort=False)
    df['p'].fillna(0, inplace=True)
    #Calculate $
    df['$'] = df['p'] * df['q']
    df.drop(['p', 'q'], axis='columns',inplace=True)
    #Calculate total $
    df_tot = df[df['type'].isin(price_types)].copy()
    df_tot = df_tot.drop(columns=['type','subtype'])
    group_cols = [c for c in ['rb', 'timeslice', 'year'] if c in df_tot.columns]
    df_tot = df_tot.groupby(group_cols, sort=False, as_index=False).sum()
    df_tot['type'] = 'tot'
    df_tot['subtype'] = 'na'
    #Reformat quantities
    df_q = dfs['q']
    df_q.rename(columns={'q':'$'}, inplace=True)
    df_q['type'] = 'q_' + df_q['type']
    #Concatenate all dataframes
    df = pd.concat([df, df_tot, df_q],sort=False,ignore_index=True)
    return df

def pre_quants(dfs, **kw):
    df_q = dfs['q']
    df_hours = pd.read_csv(this_dir_path + '/in/reeds2/hours.csv')
    df_hours.rename(columns={'timeslice':'ts'}, inplace=True)
    df = pd.merge(left=df_q, right=df_hours, how='left', on='ts', sort=False)
    df.loc[df['type'] == 'load' , 'q'] = df['q'] / df['hours']
    return df

def pre_revenue(dfs, **kw):
    df = dfs['revenue']
    #Rename 'charge' to 'load' in 'rev_cat' column, and sum results
    df['rev_cat'] = df['rev_cat'].replace({'charge': 'load'})
    group_cols = [c for c in ['rev_cat', 'tech', 'rb', 'year'] if c in df.columns]
    df = df.groupby(group_cols, sort=False, as_index=False).sum()
    #Add 'total' rev_cat by summing all rev_cat
    cols = [c for c in ['tech', 'rb', 'year'] if c in df.columns]
    df_tot = df.groupby(cols, sort=False, as_index=False).sum()
    df_tot['rev_cat'] = 'total'
    df = pd.concat([df, df_tot], sort=False, ignore_index=True)
    #Apply inflation
    df['$/yr'] = inflate_series(df['$/yr'])
    #Convert to billions
    df['Bil$/yr'] = df['$/yr'] * 1e-9
    #Marge with capacity and generation
    df = df.merge(dfs['cap'], how='left', on=cols)
    df = df.merge(dfs['gen'], how='left', on=cols)
    #Calculate $/kW-yr and $/MWh
    df['$/kW-yr'] = df['$/yr'] / (df['MW'] * 1000)
    df['$/MWh'] = df['$/yr'] / df['MWh/yr']
    return df

def pre_ng_price(dfs, **kw):
    #Apply inflation
    dfs['p']['p'] = inflate_series(dfs['p']['p'])
    #Join prices and quantities
    df = pd.merge(left=dfs['q'], right=dfs['p'], how='left', on=['census', 'year'], sort=False)
    df['p'].fillna(0, inplace=True)
    return df

# calculate storage power (GW) and energy (GWh) capacity
def calc_storage_cap(dfs, **kw):
    cap = dfs['cap'].copy()
    bcr = dfs['bcr'].copy()
    energy = dfs['energy'].copy()
    # aggregate vintages
    energy = energy.groupby(['tech', 'rb', 'year'])['Energy (GWh)'].sum().reset_index()
    # convert from MWh to GWh
    energy['Energy (GWh)'] =  energy['Energy (GWh)'] / 1e3
    # subset to storage techs
    cap_stor = cap.loc[cap['tech'].isin(energy['tech'].unique()),:].copy()
    # merge storage cap and battery/capacity ratio for relevant techs
    cap_stor = cap_stor.merge(bcr, on="tech", how='left')
    # assume missing bcr are 1 (mostly CSP)
    cap_stor['bcr'] = cap_stor['bcr'].fillna(1)
    # calculate storage power capacity using bcr, and convert from MW to GW
    cap_stor['Capacity (GW)'] = cap_stor['Capacity (GW)'] * cap_stor['bcr'] / 1e3
    # merge in storage duration
    cap_stor = cap_stor.merge(energy, on=['tech', 'rb', 'year'])
    return cap_stor

def add_joint_locations_col(df, **kw):
    df[kw['new']] = df[kw['col1']] + '-' + df[kw['col2']]
    return df

def rgba2hex(rgba):
    """
    Input should be in fraction, not [0,255]
    """
    if len(rgba) == 4:
        r,g,b = rgba[:3]
    else:
        r,g,b = rgba

    ### r,g,b could be integers in [0,255] or floats in [0,1]
    if type(r) is int:
        scaler = 1
    else:
        scaler = 255

    hexcolor = '#{:02x}{:02x}{:02x}'.format(
        int(np.round(r*scaler)),
        int(np.round(g*scaler)),
        int(np.round(b*scaler)),
    ).upper()

    return hexcolor

def pre_runtime(dictin, **kw):
    """
    ### Use the code below to redefine the colormap when new scripts are added
    augur_start = df.index.tolist().index('ReEDS_Augur/prep_data.py')
    for i, row in enumerate(df.index):
        if i < augur_start:
            colors[row.lower()] = rgba2hex(plt.cm.tab20b(i))
        elif i < augur_start + 20:
            colors[row.lower()] = rgba2hex(plt.cm.tab20c(i-augur_start))
        else:
            colors[row.lower()] = rgba2hex(plt.cm.tab20(i-augur_start-20))
    """
    df = dictin['runtime'].copy()

    # Drop the git metadata columns
    df.columns = df.loc[2].values
    df.drop([0,1,2], inplace=True)

    # Drop blanks (end column)
    df = df[df.processtime.notnull()].copy()

    #Change dtypes
    df.processtime = df.processtime.astype(float)
    df.year = df.year.astype(int)

    #Reduce columns
    df = df[['year','process','processtime']].copy()

    #Convert from seconds to hours
    df['processtime'] = df['processtime']/3600

    #All processes with year 0 will be year 2000
    df['year'] = df['year'].replace(0, 2000)

    return df

def net_co2(dfs, **kw):
    co2 = dfs['emit'].copy()
    co2 = co2[co2['e']=='CO2e']
    co2['Cumulative CO2e (MMton)'] = co2.groupby(['e','tech'])['CO2e (MMton)'].cumsum()
    print(co2['Cumulative CO2e (MMton)'])
    # scale to million metric tons
    co2['CO2e (MMton)'] /= 1e6
    co2['Cumulative CO2e (MMton)'] /= 1e6
    return co2

# function to process health damage estimates
def process_health_damage(df, **kw):
    # convert to billion $ and inflate series
    df['Health damages (billion $)'] = inflate_series(df['Health damages (billion $)']) * 1e-9

    # convert emissions to thousand metric tons
    df['Emissions (thousand metric tons)'] = df['Emissions (thousand metric tons)'] * 1e-3

    # add column for discounted damages
    d = float(core.GL['widgets']['var_discount_rate'].value)
    y0 = int(core.GL['widgets']['var_pv_year'].value)
    df['Discounted health damages (billion $)'] = df['Health damages (billion $)'] / (1 + d)**(df['year'] - y0) 
    
    # add rows for any years missing data
    full_yrs = list(range(int(df['year'].min()), int(df['year'].max()) + 1))
    allRows = {'model': df['model'].unique().tolist(),
               'cr': df['cr'].unique().tolist(),
               'e': df['e'].unique().tolist(), 
               'year': full_yrs, 
               'rb': df['rb'].unique().tolist()}

    rows = product(*allRows.values())
    df_all = pd.DataFrame.from_records(rows, columns=allRows.keys())
    df_new = df.merge(df_all, how='outer', on=['model', 'cr', 'e', 'rb', 'year'])
    df_new['st'] = df_new['st'].interpolate(method="ffill")
    
    # sort by category and year
    df_new = df_new.sort_values(['model', 'cr', 'e', 'rb', 'year'])

    # interpolate any missing values 
    df_new = df_new.groupby(['model', 'cr', 'e', 'rb']).apply(lambda group: group.interpolate(method='ffill'))

    # sum over rb
    df_out = df_new.groupby(['model', 'cr', 'e', 'year'])[
            'Emissions (thousand metric tons)', 'Health damages (billion $)', 
            'Health damages (lives)', 'Discounted health damages (billion $)'
        ].sum().reset_index()

    # also sum over pollutant   
    df_poll_agg = df_new.groupby(['model', 'cr', 'year'])[
            'Health damages (billion $)', 'Health damages (lives)', 'Discounted health damages (billion $)'
        ].sum().reset_index()

    df_poll_agg.rename(columns={'Health damages (billion $)' : 'Total health damages (billion $)', 
                                'Health damages (lives)' : 'Total health damages (lives)',
                                'Discounted health damages (billion $)': 'Total discounted health damages (billion $)'}, inplace=True)

    df_out = df_out.merge(df_poll_agg, how="outer", on=["model", "cr", "year"])

    return df_out 

def process_social_costs(dfs, **kw):
    # get annual health damages
    health_costs = process_health_damage(dfs['health_damages'])

    # calculate national average electricity price
    system_costs = pre_avgprice(dfs, reg='National', shift_capital=True)

    # aggregate both costs types by year
    system_costs_agg = system_costs.groupby(['year']).agg({'Cost (Bil $)': 'sum', 'Discounted Cost (Bil $)': 'sum', 'q': 'mean'}).reset_index()
    system_costs_agg.rename(columns={'Cost (Bil $)' : 'Cost (Bil $)-system', 
                                    'Discounted Cost (Bil $)' : 'Discounted Cost (Bil $)-system'}, inplace=True)

    health_costs_agg = health_costs.groupby(['year', 'model', 'cr'])['Health damages (billion $)', 'Discounted health damages (billion $)'].sum().reset_index()
    health_costs_agg.rename(columns={'Health damages (billion $)' : 'Cost (Bil $)-health', 
                                    'Discounted health damages (billion $)' : 'Discounted Cost (Bil $)-health'}, inplace=True)

    # combine costs and melt
    costs_agg = system_costs_agg.merge(health_costs_agg, on="year", how="outer")
    cost_values = {'Cost (Bil $)-system': 'System cost', 'Discounted Cost (Bil $)-system': 'System cost', 'Cost (Bil $)-health':'System cost + health', 'Discounted Cost (Bil $)-health':'System cost + health'}

    costs_agg_long = pd.melt(costs_agg, id_vars=['year', 'model', 'cr', 'q'], value_vars=cost_values.keys(), var_name='cost', value_name= 'Cost (Bil $)')
    costs_agg_long['cost_type'] = costs_agg_long['cost'].map(cost_values)
    costs_agg_long['cost'] = costs_agg_long['cost'].str.replace('-.*', '', regex=True)
    costs_out = costs_agg_long.pivot(index=['year', 'model', 'cr', 'q', 'cost_type'], columns='cost', values='Cost (Bil $)').reset_index()

    # calculate average in $/MWh
    costs_out['Average cost ($/MWh)'] = costs_out['Cost (Bil $)'] * 1e9 / costs_out['q']
    costs_out['Discounted average cost ($/MWh)'] = costs_out['Discounted Cost (Bil $)'] * 1e9 / costs_out['q']

    return costs_out


def pre_spur(dfs, **kw):
    """
    Load spur-line parameters written by writesupplycurves.py and include spur
    and reinforcement capacity in total transmission capacity.
    """
    ### Load the inter-BA transmission MW-miles and convert to GW-miles
    tran_mi_out = dfs['tran_mi_out'].merge(
        dfs['tran_prm_mi_out'], on=['trtype','year'], how='outer')
    for col in ['Amount (GW-mi)', 'Trans cap, PRM (GW-mi)']:
        tran_mi_out[col] /= 1000
    ### If not including spur lines in total, stop here
    if ('ignore_spur' in kw) and kw['ignore_spur']:
        return tran_mi_out
    ### Load the spur-line distance for each PV/wind investment category
    spur_parameters = dfs['spur_parameters'].copy()
    ### Load the PV/wind investment, combine with spur-line distance
    cap_new_bin_out = (
        dfs['cap_new_bin_out']
        .groupby(['i','r','rscbin','year'], as_index=False).MW.sum()
    )
    ### cap_new_bin_out is in MW_AC, but spur-line costs and distances are in MW_DC
    ### for use in ReEDS, so switch back to MW_DC
    scalars = dfs['scalars'].set_index('scalar')['value'].copy()
    cap_new_bin_out.loc[
        cap_new_bin_out.i.map(lambda x: 'upv' in x), 'MW'
    ] *= float(scalars['ilr_utility'])
    cap_new_bin_out = (
        cap_new_bin_out
        .loc[cap_new_bin_out.i.str.startswith('wind')
            | cap_new_bin_out.i.str.startswith('upv')
            | cap_new_bin_out.i.str.startswith('csp')
        ]
        .merge(spur_parameters, on=['i','r','rscbin'], how='left')
    )
    spur = (cap_new_bin_out[['year','MW','dist_spur_km']]
        .rename(columns={'dist_spur_km':'dist'})
        .assign(trtype='spur'))
    reinforcement = (cap_new_bin_out[['year','MW','dist_reinforcement_km']]
        .rename(columns={'dist_reinforcement_km':'dist'})
        .assign(trtype='reinforcement'))
    tech_trans = pd.concat([spur, reinforcement], ignore_index=True)
    ### Sum total spur-line GW-mi by year
    tech_trans['Amount (GW-mi)'] = (
        tech_trans['MW'] * tech_trans['dist']
        ### Convert from km to mi, and from MW to GW
        / 1.60934 / 1000
    )
    years = sorted(tran_mi_out.year.unique())
    full_idx = pd.MultiIndex.from_product(
        [years, ['spur','reinforcement']], names=['year','trtype'])
    tech_trans_out = (
        tech_trans
        .groupby(['year','trtype'])['Amount (GW-mi)'].sum()
        ### cap_new_bin_out is new additions, so fill missing years with zero
        ### then cumsum to get capacity
        .reindex(full_idx).fillna(0)
        .groupby(['trtype']).cumsum()
        .reset_index()
    )
    ### Add spur lines to inter-BA transmission results
    tran_mi_out = pd.concat([tran_mi_out, tech_trans_out], axis=0)

    return tran_mi_out

#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------

#2. Columns metadata. These are columns that are referenced in the Results section below.
#This is where joins, maps, and styles are applied for the columns.
#For 'style', colors are in hex, but descriptions are given (see http://www.color-hex.com/color-names.html).
#raw and display tech mappings for appending in tech_map.csv for coolingwatertech are given in:
#(https://github.nrel.gov/ReEDS/NEMS_Unit_Database_Water_Sources/blob/master/coolingtech/append2tech_map.csv)
columns_meta = {
    'tech':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/tech_map.csv',
        'style': this_dir_path + '/in/reeds2/tech_style.csv',
    },
    'class':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/class_map.csv',
        'style': this_dir_path + '/in/reeds2/class_style.csv',
    },
    'region':{
        'type':'string',
    },
    'rb':{
        'type':'string',
        'join': 'inputs_case/hierarchy.csv',
        'join_in_run': True, #Get the join file from the first run folder
        'join_keep_cols': ['*r','st','cendiv','interconnect','custreg'], #Allow an arbitrary 'custreg' column if desired.
        'join_col_rename': {'*r':'rb'},
        'join_col_lowercase': ['st'],
    },
    'ts':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/m_map.csv',
        'style': this_dir_path + '/in/reeds2/m_style.csv',
    },
    'year':{
        'type':'number',
        'filterable': True,
        'seriesable': True,
        'y-allow': False,
    },
    'iter':{
        'type':'string',
    },
    'icrb':{
        'type': 'string',
        'filterable': False,
        'seriesable': False,
    },
    'irbv':{
        'type': 'string',
        'filterable': False,
        'seriesable': False,
    },
    'cost_cat':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/cost_cat_map.csv',
        'style': this_dir_path + '/in/reeds2/cost_cat_style.csv',
    },
    'con_adj':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/con_adj_map.csv',
        'style': this_dir_path + '/in/reeds2/con_adj_style.csv',
    },
    'wst':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/wst_map.csv',
        'style': this_dir_path + '/in/reeds2/wst_style.csv',
    },
    'ctt':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/ctt_map.csv',
        'style': this_dir_path + '/in/reeds2/ctt_style.csv',
    },
    'process':{
        'type':'string',
        'style': this_dir_path + '/in/reeds2/process_style.csv',
    },
    'trtype':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/trtype_map.csv',
        'style': this_dir_path + '/in/reeds2/trtype_style.csv',
    },
}

#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------

#3. Results metadata. This is where all ReEDS results are defined. Parameters are read from gdx files, and
#are converted into pandas dataframes for pivoting. Preprocess functions may be used to perform additional manipulation.
#Note that multiple parameters may be read in for the same result (search below for 'sources')
#Presets may also be defined.
results_meta = collections.OrderedDict((
    ('Capacity National (GW)',
        {'file':'cap_nat',
        'columns': ['tech', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars Cap Frac',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'tech', 'adv_col_base':'Total'}),
            ('Stacked Bars - CCS',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'filter':{'tech':ccs_techs}}),
            ('Stacked Bars - No H2',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'filter':{'tech':{'exclude':prod_techs}}}),
            ('Stacked Bars - Only H2',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'filter':{'tech':prod_techs}}),
            ('Stacked Bars - Niche techs',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'filter':{'tech':niche_techs}}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),
    
    ('Capacity BA (GW)',
        {'file':'cap',
        'columns': ['tech', 'rb', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars by State',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'st', 'chart_type':'Bar', 'bar_width':'1.75', 'sync_axes':'No'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('Regional Cap Final',{'x':'cendiv', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'filter': {'year':'last'}}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('PCA Map Final by Tech - CCS',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last','tech':ccs_techs}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Capacity BA by class (GW)',
        {'file':'cap',
        'columns': ['tech', 'rb', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': add_class, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
        )),
        }
    ),

    ('Capacity ivrt (GW)',
        {'file':'cap_ivrt',
        'columns': ['tech', 'vintage', 'rb', 'year','Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars WaterTechs',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'filter':{'tech_raw':water_techs}}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Energy Capacity ivrt (GWh)',
        {'file':'cap_energy_ivrt',
        'columns': ['tech', 'vintage', 'rb', 'year','Energy Capacity (GWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Energy Capacity (GWh)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Energy Capacity (GWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Energy Capacity (GWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Energy Capacity (GWh)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Energy Capacity (GWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Energy Capacity (GWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Battery Duration (h)',
        {'sources': [
            {'name': 'duration', 'file': 'storage_duration_out', 'columns': ['tech', 'vintage', 'rb', 'year','Storage Duration (h)']},
            {'name': 'energy_capacity_MWh', 'file': 'cap_energy_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year','Energy Capacity (GWh)']},
        ],
        'preprocess': [
            {'func': pre_duration, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'Storage Duration (h)', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'y_min':'0', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('Weighted Average',{'chart_type':'Line', 'x':'year', 'y':'Storage Duration (h)', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Energy Capacity (GWh)', 'explode':'tech', 'series':'scenario', 'y_min':'0', 'filter':{'tech':{'exclude':prod_techs}}}),
        )),
        }
    ),

    ('Storage Capacity (GW or GWh)',

        {'sources': [
            {'name': 'cap', 'file': 'cap', 'columns': ['tech', 'rb', 'year', 'Capacity (GW)']},
            {'name': 'energy', 'file': 'stor_energy_cap', 'columns': ['tech', 'vintage', 'rb', 'year', 'Energy (GWh)']},
            {'name': 'bcr', 'file': '../inputs_case/bcr.csv', 'columns': ['tech', 'bcr']},
        ],
        'preprocess': [
            {'func': calc_storage_cap, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('National Stacked Bars - Power Capacity',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('National Stacked Bars - Energy Capacity',{'x':'year', 'y':'Energy (GWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
        )),
        }
    ),

    ('New Annual Capacity National (GW)',
        {'file':'cap_new_ann_nat',
        'columns': ['tech', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars WaterTechs',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'filter':{'tech_raw':water_techs}}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('New Annual Capacity BA (GW)',
        {'file':'cap_new_ann',
        'columns': ['tech', 'rb', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars by State',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'st', 'chart_type':'Bar', 'bar_width':'1.75', 'sync_axes':'No'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Annual Retirements National (GW)',
        {'file':'ret_ann_nat',
        'columns': ['tech', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars WaterTechs',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'filter':{'tech_raw':water_techs}}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Annual Retirements BA (GW)',
        {'file':'ret_ann',
        'columns': ['tech', 'rb', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars by State',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'st', 'chart_type':'Bar', 'bar_width':'1.75', 'sync_axes':'No'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Exogenous capacity (GW)',
        {'file':'cap_exog',
        'columns': ['tech', 'vintage', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Generation National (TWh)',
        {'file':'gen_ann_nat',
        'columns': ['tech', 'year', 'Generation (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Generation (TWh)'}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars - CCS',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75','filter':{'tech':ccs_techs}}),
            ('Stacked Bars Gen Frac',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'tech', 'adv_col_base':'Total'}),
            ('Explode By Tech',{'x':'year', 'y':'Generation (TWh)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Generation National with Uncurt and Load (TWh)',
        {'sources': [
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'Gen (TWh)']},
            {'name': 'gen_uncurt', 'file': 'gen_ivrt_uncurt', 'columns': ['tech', 'vintage', 'rb', 'year', 'Gen Uncurt (TWh)']},
            {'name': 'load', 'file': 'losses_ann', 'columns': ['type', 'year','TWh']},
        ],
        'preprocess': [
            {'func': pre_gen_w_load, 'args': {}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Bars Gen Frac of Load',{'x':'year', 'y':'Gen Frac of Load', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars Gen Frac of Load Plus Stor/Trans Loss',{'x':'year', 'y':'Gen Frac of Load Plus Stor/Trans Loss', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars Gen Uncurt Frac of Load',{'x':'year', 'y':'Gen Uncurt Frac of Load', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars Gen Uncurt Frac of Load Plus All Losses',{'x':'year', 'y':'Gen Uncurt Frac of Load Plus All Losses', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
        )),
        }
    ),

    ('Generation BA (TWh)',
        {'file':'gen_ann',
        'columns': ['tech', 'rb', 'year', 'Generation (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Generation (TWh)'}},
        ],
        'index': ['tech', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars by State',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'explode_group':'st', 'chart_type':'Bar', 'bar_width':'1.75', 'sync_axes':'No'}),
            ('Stacked Bars Gen Frac',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'tech', 'adv_col_base':'Total'}),
            ('Regional Gen Final',{'x':'cendiv', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'filter': {'year':'last'}}),
            ('Regional Gen Frac Final',{'x':'cendiv', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'tech', 'adv_col_base':'Total', 'filter': {'year':'last'}}),
            ('State Gen Final',{'x':'st', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'0.99', 'width':'600', 'filter': {'year':'last'}}),
            ('State Gen Frac Final',{'x':'st', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'tech', 'adv_col_base':'Total', 'bar_width':'0.99', 'width':'600', 'filter': {'year':'last'}}),
            ('BA Gen Final',{'x':'rb', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'0.99', 'width':'1000', 'filter': {'year':'last'}}),
            ('BA Gen Frac Final',{'x':'rb', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'0.99', 'width':'1000', 'adv_op':'Ratio', 'adv_col':'tech', 'adv_col_base':'Total', 'filter': {'year':'last'}}),
            ('Explode By Tech',{'x':'year', 'y':'Generation (TWh)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Generation (TWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Generation (TWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Generation ivrt (TWh)',
        {'file':'gen_ivrt',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Generation (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Generation (TWh)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Generation (TWh)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Generation (TWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Generation (TWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Water Withdrawal ivrt (Bgal)',
        {'file':'water_withdrawal_ivrt',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Water Withdrawal (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'Water Withdrawal (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Water Withdrawal (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Water Withdrawal (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars by Cooling Tech Type',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'ctt', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('Explode By State Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'wst', 'explode':'st', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Water Withdrawal (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Water Withdrawal (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Water Consumption ivrt (Bgal)',
        {'file':'water_consumption_ivrt',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Water Consumption (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'Water Consumption (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Water Consumption (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Water Consumption (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars by Cooling Tech Type',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'ctt', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('Explode By State Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'wst', 'explode':'st', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Water Consumption (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Water Consumption (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Water Capacity ivrt (Bgal)',
        {'file':'watcap_ivrt',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Water Capacity (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'Water Capacity (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Water Capacity by Region irt (Bgal)',
        {'file':'watcap_out',
        'columns': ['tech', 'rb', 'year', 'Water Capacity by Region (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'Water Capacity by Region (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('Explode By State',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'st', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('New Water Capacity (Bgal)',
        {'file':'watcap_new_ivrt',
        'columns': ['tech', 'vintage', 'rb', 'year', 'New Water Capacity (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'New Water Capacity (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'New Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'New Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'New Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'New Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('New Water Capacity by Region irt (Bgal)',
        {'file':'watcap_new_out',
        'columns': ['tech', 'rb', 'year', 'New Water Capacity by Region (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'New Water Capacity by Region (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'New Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'New Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('Explode By State',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'st', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'New Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'New Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('New Annual Water Capacity by Region ivrt (Bgal)',
        {'file':'watcap_new_ann_out',
        'columns': ['tech', 'vintage', 'rb', 'year', 'New Annual Water Capacity by Region (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'New Annual Water Capacity by Region (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'New Annual Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'New Annual Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('Explode By State',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'st', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'New Annual Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'New Annual Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Retired Water Capacity (Bgal)',
        {'file':'watret_ivrt',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Retired Water Capacity (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-9, 'column':'Retired Water Capacity (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Retired Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Retired Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Retired Water Capacity (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Retired Water Capacity(Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Retired Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Retired Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Retired Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Retired Water Capacity (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Retired Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Retired Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Annual Retired Water Capacity (Bgal)',
        {'file':'watret_ann_out',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Annual Retired Water Capacity (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-9, 'column':'Annual Retired Water Capacity (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Annual Retired Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Annual Retired Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Annual Retired Water Capacity (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Annual Retired Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Annual Retired Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Annual Retired Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Annual Retired Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Annual Retired Water Capacity (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Annual Retired Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Annual Retired Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Gen by timeslice national (GW)',
        {'file':'gen_h_nat',
        'columns': ['tech', 'timeslice', 'year', 'Generation (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Generation (GW)'}},
            {'func': sort_timeslices, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Final',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'width':'1000', 'x_major_label_size':'0', 'net_levels':'No', 'filter': {'year':'last'}}),
            ('Stacked Area Final',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area', 'width':'1000', 'x_major_label_size':'0', 'net_levels':'No', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Gen by timeslice regional (GW)',
        {'file':'gen_h',
        'columns': ['tech', 'rb', 'timeslice', 'year', 'Generation (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Generation (GW)'}},
            {'func': sort_timeslices, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Final',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'filter': {'year':'last'}}),
            ('Stacked Bars Final by State',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'st', 'chart_type':'Bar', 'sync_axes':'No', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Gen by stress timeslice national (GW)',
        {'file':'gen_h_stress_nat',
        'columns': ['tech', 'timeslice', 'year', 'Generation (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Generation (GW)'}},
            {'func': sort_timeslices, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Final',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'width':'1000', 'x_major_label_size':'0', 'net_levels':'No', 'filter': {'year':'last'}}),
            ('Stacked Area Final',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area', 'width':'1000', 'x_major_label_size':'0', 'net_levels':'No', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Gen by stress timeslice regional (GW)',
        {'file':'gen_h_stress',
        'columns': ['tech', 'rb', 'timeslice', 'year', 'Generation (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Generation (GW)'}},
            {'func': sort_timeslices, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Final',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'filter': {'year':'last'}}),
            ('Stacked Bars Final by State',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'st', 'chart_type':'Bar', 'sync_axes':'No', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Capacity Factor ivrt',
        {'sources': [
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year','MWh']},
            {'name': 'cap', 'file': 'cap_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year','MW']},
        ],
        'preprocess': [
            {'func': pre_cf, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('CF Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'CF', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'y_min':'0','y_max':'1', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('CF weighted ave',{'chart_type':'Line', 'x':'year', 'y':'CF', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MW', 'explode':'tech', 'series':'scenario', 'y_min':'0','y_max':'1', 'filter':{'tech':{'exclude':prod_techs}}}),
        )),
        }
    ),

    ('Capacity Factor H2 Production',
        {'sources': [
            {'name': 'prod', 'file': 'prod_produce_ann', 'columns': ['tech', 'rb', 'year','Production (metric tons)']},
            {'name': 'cap', 'file': 'prod_cap', 'columns': ['tech', 'vintage', 'rb', 'year','Capacity (metric tons)']},
        ],
        'preprocess': [
            {'func': pre_h2_cf, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('CF Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'CF', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'y_min':'0','y_max':'1', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('CF weighted ave',{'chart_type':'Line', 'x':'year', 'y':'CF', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Capacity (metric tons)', 'explode':'tech', 'series':'scenario', 'y_min':'0','y_max':'1',}),
        )),
        }
    ),

    ('New VRE CF uncurt',
        {'sources': [
            {'name': 'gen_new_uncurt', 'file': 'gen_new_uncurt', 'columns': ['tech', 'r', 'timeslice', 'year', 'MWh']},
            {'name': 'cap_new', 'file':'cap_new_out', 'columns': ['tech', 'r', 'year', 'MW']},
        ],
        'preprocess': [
            {'func': pre_new_vre_cf, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('CF weighted ave',{'chart_type':'Line', 'x':'year', 'y':'CF', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MW', 'explode':'tech', 'series':'scenario', 'y_min':'0','y_max':'1', }),
            ('CF Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'CF', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'y_min':'0','y_max':'1', 'circle_size':r'3', 'bar_width':r'1.75', }),
        )),
        }
    ),

    ('Storage Charge/Discharge (TWh)',
        {'file':'stor_inout',
        'columns': ['tech', 'vintage', 'rb', 'year', 'type', 'TWh'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'TWh'}},
        ],
        'presets': collections.OrderedDict((
            ('Explode By Tech',{'x':'year', 'y':'TWh', 'series':'scenario', 'explode':'type', 'explode_group':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Operating Reserves (TW-h)',
        {'file':'opRes_supply',
        'columns': ['ortype', 'tech', 'rb', 'year', 'Reserves (TW-h)'],
        'index': ['ortype', 'tech', 'year', 'rb'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Reserves (TW-h)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'Reserves (TW-h)', 'series':'tech', 'explode':'scenario', 'explode_group':'ortype', 'chart_type':'Bar', 'bar_width':'1.75', }),
            ('Stacked Bars by transreg',{'x':'year', 'y':'Reserves (TW-h)', 'series':'tech', 'explode':'ortype', 'explode_group':'transreg', 'chart_type':'Bar', 'bar_width':'1.75', }),
        )),
        }
    ),

    ('Operating Reserves by Timeslice National (GW)',
        {'file':'opRes_supply_h',
        'columns': ['ortype', 'tech', 'rb', 'timeslice', 'year', 'Reserves (GW)'],
        'index': ['ortype', 'tech', 'year', 'timeslice'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Reserves (GW)'}},
            {'func': sort_timeslices, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Final',{'x':'timeslice', 'y':'Reserves (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'ortype', 'chart_type':'Bar', 'filter': {'year':'last'}}),
            ('Stacked Area Final',{'x':'timeslice', 'y':'Reserves (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'ortype', 'chart_type':'Area', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Firm Capacity National (GW)',
        {'sources': [
            {'name': 'firmcap', 'file': 'cap_firm', 'columns': ['tech', 'rb', 'season', 'year', 'Firm Capacity (GW)']},
            {'name': 'cap', 'file': 'cap', 'columns': ['tech', 'rb', 'year', 'Capacity (GW)']},
        ],
        'index': ['tech', 'season', 'year'],
        'preprocess': [
            {'func': pre_firm_cap, 'args': {}},
            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['tech', 'season', 'year']}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'Firm Capacity (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'season', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Average Capacity Credit',{'x':'year', 'y':'Firm Capacity (GW)', 'y_agg':'sum(a)/sum(b)', 'y_b':'Capacity (GW)', 'series':'scenario', 'explode':'season', 'explode_group':'tech', 'chart_type':'Line'}),
            ('Average Capacity Credit CC Techs',{'x':'year', 'y':'Firm Capacity (GW)', 'y_agg':'sum(a)/sum(b)', 'y_b':'Capacity (GW)', 'series':'scenario', 'explode':'season', 'explode_group':'tech', 'chart_type':'Line', 'filter':{'tech':cc_techs}}),
        )),
        }
    ),

    ('Firm Capacity BA (GW)',
        {'sources': [
            {'name': 'firmcap', 'file': 'cap_firm', 'columns': ['tech', 'rb', 'season', 'year', 'Firm Capacity (GW)']},
            {'name': 'cap', 'file': 'cap', 'columns': ['tech', 'rb', 'year', 'Capacity (GW)']},
        ],
        'index': ['tech', 'rb', 'season', 'year'],
        'preprocess': [
            {'func': pre_firm_cap, 'args': {'ba':True}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'Firm Capacity (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'season', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Regional Stacked Bars',{'x':'cendiv', 'y':'Firm Capacity (GW)', 'series':'tech', 'explode':'scenario',
                            'explode_group':'season', 'chart_type':'Bar', 'bar_width':'1.75', 'filter':{'year':'last'}}),
            ('Average Capacity Credit',{'x':'year', 'y':'Capacity Credit', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Capacity (GW)', 'series':'scenario', 'explode':'season', 'explode_group':'tech', 'chart_type':'Line'}),
            ('Average Capacity Credit CC Techs',{'x':'year', 'y':'Capacity Credit', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Capacity (GW)', 'series':'scenario', 'explode':'season', 'explode_group':'tech', 'chart_type':'Line', 'filter':{'tech':cc_techs}}),
        )),
        }
    ),

    ('Emissions National (metric tons)',
        {'file':'emit_nat',
        'columns': ['etype', 'e', 'year', 'Emissions (metric tons)'],
        'preprocess': [
        ],
        'index': ['etype', 'e', 'year'],
        'presets': collections.OrderedDict((
            ('Scenario Lines Over Time',{'x':'year', 'y':'Emissions (metric tons)', 'series':'scenario', 'explode':'e', 'chart_type':'Line', 'sync_axes':'No'}),
        )),
        }
    ),

    ('CO2 Emissions BA (metric tons)',
        {'file':'emit_r',
        'columns': ['etype', 'e', 'rb', 'year', 'Emissions (metric tons)'],
        'preprocess': [
        ],
        'index': ['etype', 'e', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Scenario Lines Over Time',{'x':'year', 'y':'Emissions (metric tons)', 'series':'scenario', 'explode':'e', 'chart_type':'Line', 'sync_axes':'No', 'filter': {'e':['co2']}}),
            ('Scenario Lines Over Time by State',{'x':'year', 'y':'Emissions (metric tons)', 'series':'scenario', 'explode':'e', 'explode_group':'st', 'chart_type':'Line', 'sync_axes':'No', 'filter': {'e':['co2']}}),
            ('Final BA Map',{'x':'rb', 'y':'Emissions (metric tons)', 'explode':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last', 'e':['co2']}}),
        )),
        }
    ),

    ('Net CO2e Emissions National (MMton)',
        {'sources': [
            {'name': 'emit', 'file': 'emit_nat_tech', 'columns': ['etype', 'e', 'tech', 'year', 'CO2e (MMton)']},
        ],
        'preprocess': [
            {'func': net_co2, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Over Time',{'x':'year', 'y':'CO2e (MMton)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'0.75', 'filter':{'e':['co2e']}}),
            ('Cumulative Stacked Bars Over Time',{'x':'year', 'y':'Cumulative CO2e (MMton)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'0.75', 'filter':{'e':['co2e']}}),
        )),
        }
    ),

    ('Net CO2 Emissions National (MMton)',
        {'sources': [
            {'name': 'emit', 'file': 'emit_nat_tech', 'columns': ['tech', 'etype', 'year', 'CO2 (MMton)']},
        ],
        'preprocess': [
            {'func': net_co2, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Over Time',{'x':'year', 'y':'CO2 (MMton)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'0.75', 'filter':{'e':['co2']}}),
            ('Cumulative Stacked Bars Over Time',{'x':'year', 'y':'Cumulative CO2 (MMton)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'0.75', 'filter':{'e':['co2']}}),
        )),
        }
    ),

    ('Health Damages from Emissions',
        {'file':'health_damages_caused_r.csv',
        'columns': ['rb', 'st', 'year', 'e', 'Emissions (thousand metric tons)', 'model', 'cr', 'Marginal damage ($/metric ton)', 'Health damages (billion $)', 'Health damages (lives)'],
        'preprocess': [
            {'func': process_health_damage, 'args':{}},
        ],
        'presets': collections.OrderedDict((
            ('Monetized health damages over time',{'x':'year', 'y':'Total health damages (billion $)', 'series':'scenario', 'explode': 'model', 'explode_group':'cr', 'chart_type':'Line'}),
            ('Mortality over time',{'x':'year', 'y':'Total health damages (lives)', 'series':'scenario', 'explode': 'model', 'explode_group':'cr', 'chart_type':'Line'}),
            ('Total undiscounted health damages through 2050',{'x':'scenario','y':'Health damages (billion $)', 'series':'e', 'explode': 'model', 'explode_group':'cr','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR, 'end':2050}}}),
            ('Total discounted health damages through 2050',{'x':'scenario','y':'Discounted health damages (billion $)', 'series':'e', 'explode': 'model', 'explode_group':'cr','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR, 'end':2050}}}),
            ('Total mortality through 2050',{'x':'scenario','y':'Health damages (lives)', 'series':'e', 'explode': 'model', 'explode_group':'cr','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR, 'end':2050}}}),
        )),
        }
    ),

    ('Total Social Costs',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'columns': ['year', 'crf']},
            {'name': 'val_r', 'file': '../inputs_case/val_r.csv', 'header':None},
            {'name': 'df_capex_init', 'file': '../inputs_case/df_capex_init.csv'},
            {'name': 'sw', 'file': '../inputs_case/switches.csv', 'header':None, 'columns': ['switch', 'value']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
            {'name': 'health_damages', 'file': 'health_damages_caused_r.csv', 'columns': ['rb', 'st', 'year', 'e', 'Emissions (thousand metric tons)', 'model', 'cr', 'Marginal damage ($/metric ton)', 'Health damages (billion $)', 'Health damages (lives)']},
        ],  
        'preprocess': [
            {'func': process_social_costs, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('System cost + health damages: ACS CR',{'x':'year', 'y':'Average cost ($/MWh)', 'series':'cost_type', 'explode':'scenario', 'explode_group':'model', 'chart_type':'Bar', 'filter':{'cr':['acs']}  }),    
            ('System cost + health damages: H6C CR',{'x':'year', 'y':'Average cost ($/MWh)', 'series':'cost_type', 'explode':'scenario', 'explode_group':'model', 'chart_type':'Bar', 'filter':{'cr':['h6c']}  }),    
        )),
        }
    ),

    ('Natural Gas Price ($/MMBtu)',
        {'sources': [
            {'name': 'p', 'file': 'repgasprice', 'columns': ['census', 'year', 'p']},
            {'name': 'q', 'file': 'repgasquant', 'columns': ['census', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_ng_price, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'p', 'y_agg':'None', 'range':'Boxplot', 'explode':'scenario', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('Weighted Average',{'chart_type':'Line', 'x':'year', 'y':'p', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'q', 'series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('Requirement Prices and Quantities National',
        {'sources': [
            {'name': 'p', 'file': 'reqt_price_sys', 'columns': ['type', 'subtype', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant_sys', 'columns': ['type', 'subtype', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_prices, 'args': {}},
            {'func': sort_timeslices, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Energy Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load']}}),
            ('OpRes Price Lines ($/MW-h)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'subtype', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res']}}),
            ('ResMarg Price Lines ($/kW-yr)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg_ann', 'y_scale':'1e-3', 'filter': {'type':['res_marg_ann','q_res_marg_ann']}}),
            ('ResMarg Season Price Lines ($/kW-szn)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'timeslice', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg', 'y_scale':'1e-3', 'filter': {'type':['res_marg','q_res_marg']}}),
            ('National RPS Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_nat_gen', 'filter': {'type':['nat_gen','q_nat_gen']}}),
            ('CO2 Price Lines ($/metric ton)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_annual_cap', 'y_scale':'1e-6', 'filter': {'type':['annual_cap','q_annual_cap'],'subtype':['co2']}}),
            ('Energy Price by Timeslice Final ($/MWh)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('OpRes Price by Timeslice Final ($/MW-h)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'subtype', 'explode_group':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res'], 'year':'last'}}),
            ('Energy Price Area by Timeslice Final ($/MWh)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'scenario', 'chart_type':'Area', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('OpRes Price Area by Timeslice Final ($/MW-h)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'subtype', 'explode_group':'scenario', 'chart_type':'Area', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res'], 'year':'last'}}),
            ('Bulk System Electricity Price ($/MWh)',{'x':'year', 'y':'$', 'series':'type', 'explode': 'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': price_types+['q_load'], 'year': {'start':DEFAULT_PV_YEAR}}}),
            ('Total Bulk System Electricity Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': ['tot', 'q_load']}}),
        )),
        }
    ),

    ('Requirement Prices and Quantities National Annual',
        {'sources': [
            {'name': 'p', 'file': 'reqt_price_sys', 'columns': ['type', 'subtype', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant_sys', 'columns': ['type', 'subtype', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_prices, 'args': {}},
            {'func': sum_over_cols, 'args': {'drop_cols': ['timeslice'], 'group_cols': ['type', 'subtype', 'year']}},
        ],
        'presets': collections.OrderedDict((
            ('Energy Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load']}}),
            ('OpRes Price Lines ($/MW-h)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'subtype', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res']}}),
            ('ResMarg Price Lines ($/kW-yr)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg_ann', 'y_scale':'1e-3', 'filter': {'type':['res_marg_ann','q_res_marg_ann']}}),
            ('National RPS Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_nat_gen', 'filter': {'type':['nat_gen','q_nat_gen']}}),
            ('CO2 Price Lines ($/metric ton)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_annual_cap', 'y_scale':'1e-6', 'filter': {'type':['annual_cap','q_annual_cap'],'subtype':['co2']}}),
            ('Bulk System Electricity Price ($/MWh)',{'x':'year', 'y':'$', 'series':'type', 'explode': 'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': price_types+['q_load'], 'year': {'start':DEFAULT_PV_YEAR}}}),
            ('Total Bulk System Electricity Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': ['tot', 'q_load']}}),
        )),
        }
    ),

    ('Requirement Prices and Quantities BA',
        {'sources': [
            {'name': 'p', 'file': 'reqt_price', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_prices, 'args': {}},
            {'func': sort_timeslices, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Energy Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load']}}),
            ('OpRes Price Lines ($/MW-h)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'subtype', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res']}}),
            ('ResMarg Price Lines ($/kW-yr)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg_ann', 'y_scale':'1e-3', 'filter': {'type':['res_marg_ann','q_res_marg_ann']}}),
            ('ResMarg Season Price Lines ($/kW-szn)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'timeslice', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg', 'y_scale':'1e-3', 'filter': {'type':['res_marg','q_res_marg']}}),
            ('National RPS Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_nat_gen', 'filter': {'type':['nat_gen','q_nat_gen']}}),
            ('CO2 Price Lines ($/metric ton)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_annual_cap', 'y_scale':'1e-6', 'filter': {'type':['annual_cap','q_annual_cap'],'subtype':['co2']}}),
            ('Energy Price by Timeslice Final ($/MWh)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('OpRes Price by Timeslice Final ($/MW-h)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'subtype', 'explode_group':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res'], 'year':'last'}}),
            ('Energy Price Area by Timeslice Final ($/MWh)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'scenario', 'chart_type':'Area', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('OpRes Price Area by Timeslice Final ($/MW-h)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'subtype', 'explode_group':'scenario', 'chart_type':'Area', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res'], 'year':'last'}}),
            ('Energy Price Final BA Map ($/MWh)',{'x':'rb', 'y':'$', 'explode': 'scenario', 'explode_group': 'type', 'chart_type':'Area Map', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('Bulk System Electricity Price ($/MWh)',{'x':'year', 'y':'$', 'series':'type', 'explode': 'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': price_types+['q_load'], 'year': {'start':DEFAULT_PV_YEAR}}}),
            ('Bulk System Electricity Price by State ($/MWh)',{'x':'year', 'y':'$', 'series':'type', 'explode': 'scenario', 'explode_group': 'st', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': price_types+['q_load']}}),
            ('Total Bulk System Electricity Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': ['tot', 'q_load']}}),
        )),
        }
    ),

    ('Requirement Prices and Quantities BA Annual',
        {'sources': [
            {'name': 'p', 'file': 'reqt_price', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_prices, 'args': {}},
            {'func': sum_over_cols, 'args': {'drop_cols': ['timeslice'], 'group_cols': ['type', 'subtype', 'rb','year']}},
        ],
        'presets': collections.OrderedDict((
            ('Energy Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load']}}),
            ('OpRes Price Lines ($/MW-h)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'subtype', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res']}}),
            ('ResMarg Price Lines ($/kW-yr)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg_ann', 'y_scale':'1e-3', 'filter': {'type':['res_marg_ann','q_res_marg_ann']}}),
            ('National RPS Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_nat_gen', 'filter': {'type':['nat_gen','q_nat_gen']}}),
            ('CO2 Price Lines ($/metric ton)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_annual_cap', 'y_scale':'1e-6', 'filter': {'type':['annual_cap','q_annual_cap'],'subtype':['co2']}}),
            ('Energy Price Final BA Map ($/MWh)',{'x':'rb', 'y':'$', 'explode': 'scenario', 'explode_group': 'type', 'chart_type':'Area Map', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('Bulk System Electricity Price ($/MWh)',{'x':'year', 'y':'$', 'series':'type', 'explode': 'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': price_types+['q_load'], 'year': {'start':DEFAULT_PV_YEAR}}}),
            ('Bulk System Electricity Price by State ($/MWh)',{'x':'year', 'y':'$', 'series':'type', 'explode': 'scenario', 'explode_group': 'st', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': price_types+['q_load']}}),
            ('Total Bulk System Electricity Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': ['tot', 'q_load']}}),
        )),
        }
    ),

    ('Requirement Quantitites BA',
        {'sources': [
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'ts', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_quants, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Load by Timeslice 2020', {'chart_type':'Line', 'x':'ts', 'y':'q', 'series':'scenario', 'filter': {'type':['load'], 'year':['2020'], }}),
            ('Load by BA & Timeslice 2020', {'chart_type':'Line', 'x':'ts', 'y':'q', 'series':'scenario', 'explode':'rb', 'sync_axes': 'No', 'filter': {'type':['load'], 'year':['2020'], }}),
            ('Load by State & Timeslice 2020', {'chart_type':'Line', 'x':'ts', 'y':'q', 'series':'scenario', 'explode':'st', 'sync_axes': 'No', 'filter': {'type':['load'], 'year':['2020'], }}),
            ('2050 Load by State & Timeslice', {'chart_type':'Line', 'x':'ts', 'y':'q', 'series':'scenario', 'explode':'st', 'sync_axes': 'No', 'filter': {'type':['load'], 'year':['2050'], }}),
            ('Load by Region & Timeslice 2020', {'chart_type':'Line', 'x':'ts', 'y':'q', 'series':'scenario', 'explode':'custreg', 'sync_axes': 'No', 'filter': {'type':['load'], 'year':['2020'], }}),
            ('Load by State & Timeslice for each Region 2020', {'chart_type':'Line', 'x':'ts', 'y':'q', 'series':'st', 'explode':'scenario', 'explode_group':'custreg', 'sync_axes': 'No', 'filter': {'type':['load'], 'year':['2020'], }}),
            ('Load by BA & Timeslice for each Region 2020', {'chart_type':'Line', 'x':'ts', 'y':'q', 'series':'rb', 'explode':'scenario', 'explode_group':'custreg', 'sync_axes': 'No', 'filter': {'type':['load'], 'year':['2020'], }}),
        )),
        }
    ),

    ('Annual Revenue National',
        {'sources': [
            {'name': 'revenue', 'file': 'revenue_nat', 'columns': ['rev_cat', 'tech', 'year', '$/yr']},
            {'name': 'cap', 'file': 'cap_nat', 'columns': ['tech', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_uncurtailed_nat', 'columns': ['tech', 'year', 'MWh/yr']},
        ],
        'preprocess': [
            {'func': pre_revenue, 'args': {}},
        ],
        # 'index': ['rev_cat','tech', 'year'],
        'presets': collections.OrderedDict((
            #All results below need to separate out rev_cat (otherwise totals and weighted averages won't work). A 'total' rev_cat has been added.
            ('Bil$/yr Stack Techs Explode Services',{'x':'year', 'y':'Bil$/yr', 'series':'tech', 'explode': 'rev_cat', 'explode_group': 'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'sync_axes':'No', 'filter': {'year': {'start':DEFAULT_PV_YEAR}}}),
            ('$/kW-yr Tech Lines Explode Services',{'x':'year', 'y':'$/kW-yr', 'y_b':'MW', 'y_agg':'sum(a*b)/sum(b)', 'series':'tech', 'explode': 'rev_cat', 'explode_group': 'scenario', 'chart_type':'Dot-Line', 'sync_axes':'No', 'filter': {'year': {'start':DEFAULT_PV_YEAR}}}),
            ('$/MWh Tech Lines Explode Services',{'x':'year', 'y':'$/MWh', 'y_b':'MWh/yr', 'y_agg':'sum(a*b)/sum(b)', 'series':'tech', 'explode': 'rev_cat', 'explode_group': 'scenario', 'chart_type':'Dot-Line', 'sync_axes':'No', 'filter': {'year': {'start':DEFAULT_PV_YEAR}}}),
        )),
        }
    ),

    ('Sys Cost Objective (Bil $)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
            {'name': 'sw', 'file': '../inputs_case/switches.csv', 'header':None, 'columns': ['switch', 'value']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
        ],
        'index': ['cost_cat', 'year'],
        'preprocess': [
            {'func': pre_systemcost, 'args': {'objective':True, 'shift_capital':True}},
        ],
        'presets': collections.OrderedDict((
            ('Cost by Year',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75'}),
        )),
        }
    ),

    ('Sys Cost beyond final year (Bil $)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost_bulk', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'sw', 'file': '../inputs_case/switches.csv', 'header':None, 'columns': ['switch', 'value']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
        ],
        'index': ['cost_cat', 'year'],
        'preprocess': [
            {'func': pre_systemcost, 'args': {'shift_capital':True}},
        ],
        'presets': collections.OrderedDict((
            ('Total Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar'}),
            (f'{DEFAULT_PV_YEAR}-end Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR}}}),
            ('Discounted by Year',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75'}),
            ('Undiscounted by Year',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75'}),
        )),
        }
    ),

    ('Sys Cost Annualized (Bil $)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'columns': ['year', 'crf']},
            {'name': 'val_r', 'file': '../inputs_case/val_r.csv', 'header':None},
            {'name': 'df_capex_init', 'file': '../inputs_case/df_capex_init.csv'},
            {'name': 'sw', 'file': '../inputs_case/switches.csv', 'header':None, 'columns': ['switch', 'value']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
        ],
        'index': ['cost_cat', 'year'],
        'preprocess': [
            {'func': pre_systemcost, 'args': {'annualize':True, 'shift_capital':True}},
        ],
        'presets': collections.OrderedDict((
            ('Total Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar'}),
            ('Discounted through 2050',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR, 'end':2050}}}),
            (f'{DEFAULT_PV_YEAR}-end Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR}}}),
            ('Discounted by Year',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75'}),
            ('Total Undiscounted',{'x':'scenario','y':'Cost (Bil $)','series':'cost_cat','chart_type':'Bar'}),
            ('Undiscounted by Year',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'0.95'}),
        )),
        }
    ),

     ('Sys Cost Annualized BA/State (Bil $)', 
        {'sources': [
            {'name': 'sc', 'file': 'systemcost_ba', 'columns': ['cost_cat', 'r', 'year', 'Cost (Bil $)']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'columns': ['year', 'crf']},
            {'name': 'val_r', 'file': '../inputs_case/val_r.csv', 'header':None},
            {'name': 'df_capex_init', 'file': '../inputs_case/df_capex_init.csv'},
            {'name': 'sw', 'file': '../inputs_case/switches.csv', 'header':None, 'columns': ['switch', 'value']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
        ],
        'index': ['cost_cat', 'r', 'year'],
        'preprocess': [
            {'func': pre_systemcost, 'args': {'annualize':True, 'shift_capital':True, 'maintain_ba_index':True}},
        ],
        'presets': collections.OrderedDict((
            ('Total Discounted - BA',{'x':'r','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar'}),
            ('Discounted through 2050 - BA',{'x':'r','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR, 'end':2050}}}),
            (f'{DEFAULT_PV_YEAR}-end Discounted - BA',{'r':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR}}}),
            ('Discounted by Year - BA',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','explode_group':'r','chart_type':'Bar', 'bar_width':'1.75'}),
            ('Total Undiscounted - BA',{'x':'r','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar'}),
            ('Undiscounted by Year - BA',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','explode_group':'r','chart_type':'Bar', 'bar_width':'0.95'}),
            ('Total Discounted - State',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'st','chart_type':'Bar'}),
            ('Discounted through 2050 - State',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'st','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR, 'end':2050}}}),
            (f'{DEFAULT_PV_YEAR}-end Discounted - State',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'st','chart_type':'Bar', 'filter': {'year': {'start':DEFAULT_PV_YEAR}}}),
            ('Discounted by Year - State',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','explode_group':'st','chart_type':'Bar', 'bar_width':'1.75'}),
            ('Total Undiscounted - State',{'x':'scenario','y':'Cost (Bil $)','series':'cost_cat','explode':'st','chart_type':'Bar'}),
            ('Undiscounted by Year - State',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','explode_group':'st','chart_type':'Bar', 'bar_width':'0.95'}),        
        )),
        }
    ),

    ('National Average Electricity Cost ($/MWh)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']}, 
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'columns': ['year', 'crf']},
            {'name': 'val_r', 'file': '../inputs_case/val_r.csv', 'header':None},
            {'name': 'df_capex_init', 'file': '../inputs_case/df_capex_init.csv'},
            {'name': 'sw', 'file': '../inputs_case/switches.csv', 'header':None, 'columns': ['switch', 'value']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
        ],
        'preprocess': [
            {'func': pre_avgprice, 'args': {'reg':'National', 'shift_capital':True}},
        ],
        'presets': collections.OrderedDict((
            ('Average Electricity Cost by Year ($/MWh)',{'x':'year','y':'Average cost ($/MWh)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'0.95', 'filter': {'year': {'start':2010, 'end':2050}}}),
        )),
        }
    ),

    ('BA-level Average Electricity Cost ($/MWh)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost_ba', 'columns': ['cost_cat','rb', 'year', 'Cost (Bil $)']},
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
            {'name': 'p', 'file': 'reqt_price', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'gen', 'file': 'gen_h', 'columns': ['tech', 'r', 'timeslice', 'year', 'Generation (GW)']},
            {'name': 'existcap', 'file': '../inputs_case/cappayments_ba.csv', 'columns': ['rb', 'year','existingcap']},
            {'name': 'captrade', 'file': 'captrade', 'columns': ['rb_out', 'rb_in', 'type', 'season', 'year', 'Amount (MW)']},
            {'name': 'powerfrac_downstream', 'file': 'powerfrac_downstream', 'columns': ['rr', 'r', 'timeslice', 'year', 'frac']},
            {'name': 'powerfrac_upstream', 'file': 'powerfrac_upstream', 'columns': ['r', 'rr', 'timeslice', 'year', 'frac']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'columns': ['year', 'crf']},
            {'name': 'val_r', 'file': '../inputs_case/val_r.csv', 'header':None},
            {'name': 'df_capex_init', 'file': '../inputs_case/df_capex_init.csv'},
            {'name': 'sw', 'file': '../inputs_case/switches.csv', 'header':None, 'columns': ['switch', 'value']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
        ],
        'preprocess': [
            {'func': pre_avgprice, 'args': {'reg':'BA', 'shift_capital':True}},
        ],
        'presets': collections.OrderedDict((
            ('Average BA-level Electricity Cost by Year ($/MWh)',{'x':'year','y':'Average cost ($/MWh)','series':'cost_cat','explode':'rb','explode_group':'scenario','chart_type':'Bar', 'bar_width':'1.75'}),
            ('Average state-level Electricity Cost by Year ($/MWh)',{'x':'year','y':'Cost (Bil $)', 'y_b':'load (MWh)', 'y_agg':'sum(a*b)/sum(b)', 'series':'cost_cat','explode':'st','explode_group':'scenario','chart_type':'Bar', 'bar_width':'1.75'}),
        )),
        }
    ),

    ('CO2 Abatement Cost ($/metric ton)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'emit', 'file': 'emit_nat', 'columns': ['year', 'CO2 (MMton)']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'columns': ['year', 'crf']},
            {'name': 'val_r', 'file': '../inputs_case/val_r.csv', 'header':None},
            {'name': 'df_capex_init', 'file': '../inputs_case/df_capex_init.csv'},
            {'name': 'sw', 'file': '../inputs_case/switches.csv', 'header':None, 'columns': ['switch', 'value']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
        ],
        'preprocess': [
            {'func': pre_abatement_cost, 'args': {'annualize':True, 'shift_capital':True}},
        ],
        'presets': collections.OrderedDict((
            #To work properly, these presets require selecting the correct scenario for the Advanced Operation base.
            ('Cumulative Undiscounted Over Time',{'x':'year','y':'cum val','series':'scenario','chart_type':'Line', 'explode':'type', 'adv_op':'Difference', 'adv_col':'scenario', 'adv_col_base':'None', 'adv_op2': 'Ratio', 'adv_col2': 'type', 'adv_col_base2': 'CO2 (Bil metric tons)', 'y_scale':'-1'}),
            ('Cumulative Discounted Over Time',{'x':'year','y':'cum disc val','series':'scenario','chart_type':'Line', 'explode':'type', 'adv_op':'Difference', 'adv_col':'scenario', 'adv_col_base':'None', 'adv_op2': 'Ratio', 'adv_col2': 'type', 'adv_col_base2': 'CO2 (Bil metric tons)', 'y_scale':'-1'}),
        )),
        }
    ),

    ('CO2 Abatement Cost Objective ($/metric ton)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'emit', 'file': 'emit_nat', 'columns': ['year', 'CO2 (MMton)']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
        ],
        'preprocess': [
            {'func': pre_abatement_cost, 'args': {'objective':True, 'shift_capital':True}},
        ],
        'presets': collections.OrderedDict((
            #To work properly, these presets require selecting the correct scenario for the Advanced Operation base.
            ('Abatement Cost By Year',{'x':'year','y':'val','series':'scenario','chart_type':'Line', 'explode':'type', 'adv_op':'Difference', 'adv_col':'scenario', 'adv_col_base':'None', 'adv_op2': 'Ratio', 'adv_col2': 'type', 'adv_col_base2': 'CO2 (Bil metric tons)', 'y_scale':'-1'}),
        )),
        }
    ),
    ('Value New Techs',
        {'file':'valnew',
        'columns': ['output', 'tech', 'rb', 'year', 'value'],
        'preprocess': [
            {'func': pre_valnew, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            #Total value factor by year, with separate charts for each tech and scenarios as different lines
            ('VF by Year', {'x':'year','y':'vf','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            #Total value factor by year, with separate charts for each scenario and techs as different lines
            ('VF by Year Explode Scenario', {'x':'year','y':'vf','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'tech','explode':'scenario','chart_type':'Dot-Line', 'sync_axes':'No', 'y_min':'0','y_max':'2'}),
            #Value factor of energy alone, that is, energy value per MWh of a tech compared to that of the benchmark
            ('VF Energy by Year', {'x':'year','y':'vf_load','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            #Value factor of firm capacity alone, that is, capacity value per MWh of a tech compared to that of the benchmark
            ('VF Firm Capacity by Year', {'x':'year','y':'vf_resmarg','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            #Value factor of firm capacity alone, that is, capacity value per MW of a tech compared to that of the benchmark
            ('VF Firm Capacity per MW by Year', {'x':'year','y':'vf_resmarg_permw','y_b':'mw','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            #Temporal, spatial, and interaction value factors
            ('VF Spatial by Year', {'x':'year','y':'vf_spatial','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            ('VF Temporal by Year', {'x':'year','y':'vf_temporal','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            ('VF Interaction by Year', {'x':'year','y':'vf_interaction','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            ('VF Spatial Simultaneous by Year', {'x':'year','y':'vf_spatial_simult','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            ('VF Temporal Local by Year', {'x':'year','y':'vf_temporal_local','y_b':'mwh','y_agg':'sum(a*b)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            #LVOE and LVOE components
            ('LVOE by Year', {'x':'year','y':'val_tot','y_b':'mwh','y_agg':'sum(a)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            ('LVOE Energy by Year', {'x':'year','y':'val_load','y_b':'mwh','y_agg':'sum(a)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            ('LVOE Firm Capacity by Year', {'x':'year','y':'val_resmarg','y_b':'mwh','y_agg':'sum(a)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            ('LVOE Operating Reserves by Year', {'x':'year','y':'val_opres','y_b':'mwh','y_agg':'sum(a)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
            ('LVOE State RPS by Year', {'x':'year','y':'val_rps','y_b':'mwh','y_agg':'sum(a)/sum(b)','series':'scenario','explode':'tech','chart_type':'Dot-Line', 'sync_axes':'No'}),
        )),
        }
    ),

    ('Value Streams Sequential New Techs',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True}},
        ],
        'presets': collections.OrderedDict((
            ('NVOE over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOE final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOE final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOE final nat tech explode', {'x':'scenario','y':'Bulk $ Dis','series':'con_adj','explode':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOC over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['MWh']}}}),
            ('NVOC final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('NVOC final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('NVOC final nat tech explode', {'x':'scenario','y':'Bulk $ Dis','series':'con_adj','explode':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('LCOE over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'con_name':coststreams+['MWh']}}),
            ('LCOE final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'year':'last','con_name':coststreams+['MWh']}}),
            ('LCOE final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'year':'last','con_name':coststreams+['MWh']}}),
            ('NVOE var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'MWh, MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'kW, kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['MWh']}}}),
        )),
        }
    ),

    ('Competitiveness Sequential New Techs',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale', 'columns': ['cs']},
            {'name': 'p', 'file': 'reqt_price', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True, 'competitiveness':True}},
        ],
        'presets': collections.OrderedDict((
            ('LCOE boxplot over time', {'x':'year','y':'LCOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('LCOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'LCOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('LVOE boxplot over time', {'x':'year','y':'LVOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('LVOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'LVOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('NVOE boxplot over time', {'x':'year','y':'NVOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('NVOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'NVOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('value factor boxplot over time', {'x':'year','y':'value factor','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('value factor weighted ave',{'chart_type':'Line', 'x':'year', 'y':'value factor', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('integration cost boxplot over time', {'x':'year','y':'integration cost','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('integration cost weighted ave',{'chart_type':'Line', 'x':'year', 'y':'integration cost', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('BCR boxplot over time', {'x':'year','y':'BCR','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('BCR weighted ave',{'chart_type':'Line', 'x':'year', 'y':'BCR', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Cost $', 'explode':'tech', 'series':'scenario'}),
            ('PLCOE boxplot over time', {'x':'year','y':'PLCOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('PLCOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'PLCOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Value $', 'explode':'tech', 'series':'scenario'}),
            ('SLCOE boxplot over time', {'x':'year','y':'SLCOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('SLCOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'SLCOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('Benchmark price ($/MWh)',{'chart_type':'Line', 'x':'year', 'y':'P_b', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Cost $', 'series':'scenario'}),
        )),
        }
    ),

    ('LCOE ($/MWh) Sequential New Techs (uncurt MWh)',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_ivrt_uncurt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True, 'competitiveness':True, 'uncurt':True}},
        ],
        'presets': collections.OrderedDict((
            ('LCOE boxplot over time', {'x':'year','y':'LCOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('LCOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'LCOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('Value Streams Sequential Existing Techs',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'remove_inv':True}},
        ],
        'presets': collections.OrderedDict((
            ('NVOE', {'x':'tech, vintage','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC', {'x':'tech, vintage','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'filter': {'con_name':{'exclude':['MWh']}}}),
            ('NVOE var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'MWh, MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'kW, kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'filter': {'con_name':{'exclude':['MWh']}}}),
            ('Cost Val over time', {'x':'year','y':'Bulk $','series':'con_adj', 'explode': 'scenario', 'explode_group':'tech', 'chart_type':'Bar', 'sync_axes': 'No', 'bar_width':r'1.75', 'filter': {'con_adj':{'exclude':['MWh', 'kW']}}}),
            ('NVOC over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'explode_group':'tech', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'sync_axes': 'No', 'bar_width':r'1.75', 'filter': {'con_adj':{'exclude':['MWh']}}}),
        )),
        }
    ),

    ('Value Streams Intertemporal',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('NVOE', {'x':'tech, vintage','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC', {'x':'tech, vintage','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'filter': {'con_name':{'exclude':['MWh']}}}),
            ('NVOE var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'MWh, MWh', 'chart_type':'Bar', 'width':'600', 'height':'600', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'kW, kW', 'chart_type':'Bar', 'width':'600', 'height':'600', 'filter': {'con_name':{'exclude':['MWh']}}}),
        )),
        }
    ),
    ('Value Factors Sequential New Techs',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_ivrt_uncurt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale', 'columns': ['cs']},
            {'name': 'p', 'file': 'reqt_price', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True, 'uncurt':True, 'value_factors':True}},
        ],
        'presets': collections.OrderedDict((
            ('LVOE', {'chart_type':'Bar', 'x':'year', 'y':'$', 'series':'con_name', 'explode':'scenario', 'explode_group':'tech', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'sync_axes':'No', 'filter': {}}),
            ('Total price flat benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ flat sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {}}),
            ('Total price all-in weighted benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ all-in sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {}}),
            ('Total value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Total value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Local value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Local value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Spatial value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ flat loc','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Spatial value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ all-in loc','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),

            ('Energy LVOE', {'chart_type':'Bar', 'x':'year', 'y':'$', 'series':'con_name', 'explode':'scenario', 'explode_group':'tech', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams+['MWh']}}),
            ('Energy price flat benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ flat sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {'con_name':energy_valstreams+['MWh']}}),
            ('Energy price with all-in weighted benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ all-in sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {'con_name':energy_valstreams+['MWh']}}),
            ('Energy total value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy total value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy local value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy local value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy spatial value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ flat loc','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy spatial value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ all-in loc','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),

            ('ResMarg LVOE', {'chart_type':'Bar', 'x':'year', 'y':'$', 'series':'con_name', 'explode':'scenario', 'explode_group':'tech', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin','MWh']}}),
            ('ResMarg price flat benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ flat sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {'con_name':['eq_reserve_margin','MWh']}}),
            ('ResMarg price all-in weighted benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ all-in sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {'con_name':['eq_reserve_margin','MWh']}}),
            ('ResMarg total value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg total value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg local value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg local value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg spatial value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ flat loc','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg spatial value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ all-in loc','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
        )),
        }
    ),

    ('Value Factors Sequential Existing Techs (curtailment caused missing)',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_ivrt_uncurt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale', 'columns': ['cs']},
            {'name': 'p', 'file': 'reqt_price', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'remove_inv':True, 'uncurt':True, 'value_factors':True}},
        ],
        'presets': collections.OrderedDict((
            ('Total value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Total value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Local value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Local value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Spatial value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ flat loc','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Spatial value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ all-in loc','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
        )),
        }
    ),

    ('Reduced Cost ($/kW)',
        {'file':'reduced_cost',
        'columns': ['tech', 'vintage', 'rb', 'year','bin','variable','$/kW'],
        'preprocess': [
            {'func': pre_reduced_cost, 'args': {}},
            {'func': apply_inflation, 'args': {'column': '$/kW'}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'irbv', 'y':'$/kW', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'irbv', 'y':'$/kW', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
        )),
        }
    ),

    ('LCOE ($/MWh)',
        {'sources': [
            {'name': 'lcoe', 'file': 'lcoe', 'columns': ['tech', 'vintage', 'rb', 'year', 'bin','$/MWh']},
            {'name': 'inv', 'file': 'cap_new_bin_out', 'columns': ['tech', 'vintage', 'rb', 'year', 'bin','chosen MW']},
            {'name': 'avail', 'file': 'cap_avail', 'columns': ['tech', 'rb', 'year', 'bin','available MW']},
        ],
        'preprocess': [
            {'func': pre_lcoe, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
            ('Final supply curves chosen', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'chosen':['yes']}}),
            ('Final supply curves chosen p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'chosen':['yes'], 'rb':['p1']}}),
        )),
        }
    ),

    ('LCOE cf_act ($/MWh)',
        {'sources': [
            {'name': 'lcoe', 'file': 'lcoe_cf_act', 'columns': ['tech', 'vintage', 'rb', 'year', 'bin','$/MWh']},
            {'name': 'inv', 'file': 'cap_new_bin_out', 'columns': ['tech', 'vintage', 'rb', 'year', 'bin','chosen MW']},
            {'name': 'avail', 'file': 'cap_avail', 'columns': ['tech', 'rb', 'year', 'bin','available MW']},
        ],
        'preprocess': [
            {'func': pre_lcoe, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
            ('Final supply curves chosen', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'chosen':['yes']}}),
            ('Final supply curves chosen p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'chosen':['yes'], 'rb':['p1']}}),
        )),
        }
    ),

    ('LCOE nopol ($/MWh)',
        {'sources': [
            {'name': 'lcoe', 'file': 'lcoe_nopol', 'columns': ['tech', 'vintage', 'rb', 'year', 'bin','$/MWh']},
            {'name': 'inv', 'file': 'cap_new_bin_out', 'columns': ['tech', 'vintage', 'rb', 'year', 'bin','chosen MW']},
            {'name': 'avail', 'file': 'cap_avail', 'columns': ['tech', 'rb', 'year', 'bin','available MW']},
        ],
        'preprocess': [
            {'func': pre_lcoe, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
            ('Final supply curves chosen', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'chosen':['yes']}}),
            ('Final supply curves chosen p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'chosen':['yes'], 'rb':['p1']}}),
        )),
        }
    ),

    ('LCOE fullpol ($/MWh)',
        {'sources': [
            {'name': 'lcoe', 'file': 'lcoe_fullpol', 'columns': ['tech', 'vintage', 'rb', 'year', 'bin','$/MWh']},
            {'name': 'inv', 'file': 'cap_new_bin_out', 'columns': ['tech', 'vintage', 'rb', 'year', 'bin','chosen MW']},
            {'name': 'avail', 'file': 'cap_avail', 'columns': ['tech', 'rb', 'year', 'bin','available MW']},
        ],
        'preprocess': [
            {'func': pre_lcoe, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
            ('Final supply curves chosen', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'chosen':['yes']}}),
            ('Final supply curves chosen p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'width':'600', 'height':'600', 'filter': {'year':'last', 'chosen':['yes'], 'rb':['p1']}}),
        )),
        }
    ),

    ('Losses (TWh)',
        {'file':'losses_ann',
        'columns': ['type', 'year', 'Amount (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .000001, 'column':'Amount (TWh)'}},
        ],
        'index': ['type', 'year'],
        'presets': collections.OrderedDict((
            ('Total Losses Over Time',{'x':'year', 'y':'Amount (TWh)', 'series':'scenario', 'chart_type':'Line', 'filter': {'type':{'exclude':['load']} }}),
            ('Losses by Type Over Time',{'x':'year', 'y':'Amount (TWh)', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'filter': {'type':{'exclude':['load']} }}),
            ('Fractional Losses by Type Over Time',{'x':'year', 'y':'Amount (TWh)', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'load'}),
        )),
        }
    ),

    ('Resource adequacy',
        {'file':'neue.csv',
        'columns': ['year', 'iteration', 'neue'],
        'index': ['year', 'iteration'],
        'preprocess': [
            {'func': pre_neue, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Normalized expected unserved energy [%]', {'x':'year', 'y':'neue', 'chart_type':'Bar', 'explode':'scenario', 'bar_width':'1.75'}),
        )),
        }
    ),

    ('Average VRE Curtailment',
        {'file':'curt_rate',
        'columns': ['year', 'Curt Rate'],
        'index': ['year'],
        'presets': collections.OrderedDict((
            ('Curt Rate Over Time',{'x':'year', 'y':'Curt Rate', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

	('Time Slice Curtailment',
        {'file':'curt_h',
        'columns': ['r','timeslice','year','Curt Energy'],
        'index': ['year','timeslice'],
        'presets': collections.OrderedDict((
            ('Curt Rate Over Time',{'x':'year', 'y':'Curt Energy', 'series':'scenario', 'explode':'timeslice','chart_type':'Line'}),
        )),
        }
    ),

    ('Curtailment Rate ivrt (Realized)',
        {'sources': [
            {'name': 'gen', 'file': 'gen_ivrt', 'columns': ['tech', 'vintage', 'rb', 'year','MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_ivrt_uncurt', 'columns': ['tech', 'vintage', 'rb', 'year','MWh uncurt']},
            {'name': 'load', 'file': 'load_rt', 'columns': ['rb', 'year','MWh load']},
        ],
        'preprocess': [
            {'func': pre_curt, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Curt Rate Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'Curt Rate', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('Curt Rate weighted ave',{'chart_type':'Line', 'x':'year', 'y':'Curt Rate', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh uncurt', 'explode':'tech', 'series':'scenario', 'sync_axes':'No', }),
            ('Curt Rate weighted ave vs penetration',{'chart_type':'Line', 'x':'VRE penetration nat', 'y':'Curt Rate', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh uncurt', 'explode':'tech', 'series':'scenario', 'sync_axes':'No', }),
            ('VRE penetration',{'chart_type':'Line', 'x':'year', 'y':'VRE penetration nat', 'y_agg':'ave(a)','series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('New Tech Curtailment Frac (Caused)',
        {'sources': [
            {'name': 'gen_uncurt', 'file': 'gen_new_uncurt', 'columns': ['tech', 'rb', 'timeslice', 'year', 'MWh uncurt']},
            {'name': 'curt_rate', 'file': 'curt_new', 'columns': ['tech', 'rb', 'timeslice', 'year', 'Curt Rate']},
        ],
        'preprocess': [
            {'func': pre_curt_new, 'args': {'annual':True}},
        ],
        'presets': collections.OrderedDict((
            ('Curt Rate Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'Curt Rate', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('Curt Rate weighted ave',{'chart_type':'Line', 'x':'year', 'y':'Curt Rate', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh uncurt', 'explode':'tech', 'series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('New Tech Capacity Credit',
        {'sources': [
            {'name': 'cap', 'file': 'cap_new_cc', 'columns': ['tech', 'rb', 'season', 'year', 'MW']},
            {'name': 'cc', 'file': 'cc_new', 'columns': ['tech', 'rb', 'season', 'year', 'CC Rate']},
        ],
        'preprocess': [
            {'func': pre_cc_new, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('CC Rate Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'CC Rate', 'y_agg':'None', 'range':'Boxplot', 'explode':'season', 'explode_group':'tech', 'series':'scenario', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('CC Rate weighted ave',{'chart_type':'Line', 'x':'year', 'y':'CC Rate', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MW', 'explode':'season', 'explode_group':'tech', 'series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('Transmission (GW-mi)',
        {'sources': [
            {'name':'tran_mi_out', 'file':'tran_mi_out', 'columns':['trtype', 'year', 'Amount (GW-mi)']},
            {'name':'tran_prm_mi_out', 'file':'tran_prm_mi_out', 'columns':['trtype', 'year', 'Trans cap, PRM (GW-mi)']},
            {'name':'spur_parameters', 'file':'../inputs_case/spur_parameters.csv'},
            {'name':'cap_new_bin_out', 'file':'cap_new_bin_out', 'columns':['i','v','r','year','rscbin','MW']},
            {'name': 'scalars', 'file': '../inputs_case/scalars.csv', 'header':None, 'columns': ['scalar', 'value', 'comment']},
        ],
        'preprocess': [
            {'func': pre_spur, 'args': {'ignore_spur': False}},
        ],
        'index': ['trtype', 'year'],
        'presets': collections.OrderedDict((
            ('Transmission Capacity',{'x':'year', 'y':'Amount (GW-mi)', 'series':'scenario', 'explode':'trtype', 'chart_type':'Line'}),
            ('Transmission Capacity Agg by type',{'x':'year', 'y':'Amount (GW-mi)', 'series':'scenario', 'chart_type':'Line'}),
            ('Transmission Capacity stacked bars',{'x':'year', 'y':'Amount (GW-mi)', 'series':'trtype', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Transmission Capacity (PRM) stacked bars',{'x':'year', 'y':'Trans cap, PRM (GW-mi)', 'series':'trtype', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
        )),
        }
    ),

    ('Transmission Capacity Network (GW)',
        {'file':'tran_out',
        'columns': ['rb_out', 'rb_in', 'type', 'year', 'Amount (GW)'],
        'preprocess': [
            {'func': add_joint_locations_col, 'args': {'col1':'rb_out','col2':'rb_in','new':'rb-rb'}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Amount (GW)'}},
        ],
        'index': ['rb-rb', 'year', 'type'],
        'presets': collections.OrderedDict((
            ('Map Final', {'x':'rb-rb', 'y':'Amount (GW)', 'series':'scenario', 'explode':'year', 'chart_type':'Line Map', 'filter': {'year': 'last'}}),
            ('Map Final AC/DC', {'x':'rb-rb', 'y':'Amount (GW)', 'series':'scenario', 'explode':'type', 'explode_group':'year', 'chart_type':'Line Map', 'filter': {'year': 'last'}}),
            ('Map minus 2018', {'x':'rb-rb', 'y':'Amount (GW)', 'series':'scenario', 'explode':'year', 'chart_type':'Line Map', 'adv_op':'Difference', 'adv_col':'year', 'adv_col_base':'2018', 'filter': {'year': ['2018','2050']}}),
        )),
        }
    ),

    ('RE Generation Price ($/MWh)',
        {'file':'RE_gen_price_nat',
        'columns': ['year', 'Price ($/MWh)'],
        'preprocess': [
            {'func': apply_inflation, 'args': {'column':'Price ($/MWh)'}},
        ],
        #'index': ['year'],
        'presets': collections.OrderedDict((
            ('Scenario Lines Over Time',{'x':'year', 'y':'Price ($/MWh)', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('RE Capacity Price ($/kW-yr)',
        {'file':'RE_cap_price_nat',
        'columns': ['season', 'year', 'Price ($/kW-yr)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Price ($/kW-yr)'}},
            {'func': apply_inflation, 'args': {'column':'Price ($/kW-yr)'}},
        ],
        'index': ['season', 'year'],
        'presets': collections.OrderedDict((
            ('Seasonal RE Capacity Price Over Time',{'x':'year', 'y':'Price ($/kW-yr)', 'series':'scenario', 'explode':'season', 'chart_type':'Line'}),
            ('Total RE Capacity Price Over Time',{'x':'year', 'y':'Price ($/kW-yr)', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('RE Capacity Price BA ($/kW-yr)',
        {'file':'RE_cap_price_r',
        'columns': ['rb', 'season', 'year', 'Price ($/kW-yr)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Price ($/kW-yr)'}},
            {'func': apply_inflation, 'args': {'column':'Price ($/kW-yr)'}},
        ],
        'index': ['rb', 'season', 'year'],
        'presets': collections.OrderedDict((
            ('RE Cap Price by BA',{'x':'rb', 'y':'Price ($/kW-yr)', 'explode':'scenario', 'explode_group':'season', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('CO2 Price ($/metric ton)',
        {'file':'co2_price',
        'columns': ['year', '$/metric ton'],
        'preprocess': [
            {'func': apply_inflation, 'args': {'column':'$/metric ton'}},
        ],
        'index': ['year'],
        'presets': collections.OrderedDict((
            ('CO2 price over time',{'chart_type':'Line', 'x':'year', 'y':'$/metric ton', 'series':'scenario', }),
        )),
        }
    ),

    ('CO2 Capture National (million metric tons)',
        {'file':'CO2_CAPTURED_out_ann',
        'columns': ['rb', 'year', 'CO2 Captured (million metric tons)'],
        'preprocess': [
            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['year']}},
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'CO2 Captured (million metric tons)'}},
        ],
        'index': ['year'],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'CO2 Captured (million metric tons)', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
        )),
        }
    ),

    ('CO2 Stored (million metric tons)',
        {'file':'CO2_STORED_out_ann',
        'columns': ['rb', 'reservoir_name','year', 'CO2 Stored (million metric tons)'],
        'preprocess': [
            {'func': sum_over_cols, 'args': {'drop_cols': ['reservoir_name'], 'group_cols': ['rb','year']}},
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'CO2 Stored (million metric tons)'}},
        ],
        'index': ['rb','year'],
        'presets': collections.OrderedDict((
            ('PCA Map Final by Tech - CCS',{'x':'rb', 'y':'CO2 Stored (million metric tons)', 'explode':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('VRE (TWh) vs Stor In (TWh)',
        {'sources': [
            {'name': 'stor', 'file': 'stor_inout', 'columns': ['technology', 'vintage', 'rb', 'year', 'type', 'Storage (TWh)']},
            {'name': 'gen', 'file': 'gen_ann', 'columns': ['technology', 'rb', 'year', 'Generation (TWh)']},
        ],
        'preprocess': [
            {'func': pre_vre_vs_stor, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('PV vs Bat',{'x':'PV (TWh)', 'y':'Battery (TWh)', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Error Check',
        {'file':'error_check',
        'columns': ['type', 'Value'],
        'presets': collections.OrderedDict((
            ('Errors',{'x':'scenario', 'y':'Value', 'explode':'type', 'chart_type':'Bar', 'sync_axes':'No'}),
        )),
        }
    ),

    ('Capacity Iteration (GW)',
        {'file':'cap_iter',
        'columns': ['tech', 'vintage', 'r', 'year', 'iter', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Generation Iteration (TWh)',
        {'file':'gen_iter',
        'columns': ['tech', 'vintage', 'r', 'year', 'iter', 'Gen (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Gen (TWh)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Gen (TWh)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Gen (TWh)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Gen (TWh)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Gen (TWh)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Gen (TWh)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Firm Capacity Iteration (GW)',
        {'file':'cap_firm_iter',
        'columns': ['tech', 'vintage', 'r', 'season', 'year', 'iter', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Capacity Credit Iteration (GW)',
        {'sources': [
            {'name': 'cap_firm', 'file': 'cap_firm_iter', 'columns': ['tech', 'vintage', 'r', 'season', 'year', 'iter', 'GW']},
            {'name': 'cap', 'file': 'cap_iter', 'columns': ['tech', 'vintage', 'r', 'year', 'iter', 'GW']},
        ],
        'preprocess': [
            {'func': pre_cc_iter, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'GW'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'GW', 'series':'tech', 'explode':'iter', 'explode_group':'type', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'cap'}),
            ('Explode By Tech',{'x':'year', 'y':'GW', 'series':'iter', 'explode':'tech', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'cap'}),
        )),
        }
    ),

    ('Curtailment Iteration (TWh)',
        {'sources': [
            {'name': 'curt', 'file': 'curt_tot_iter', 'columns': ['tech', 'vintage', 'r', 'year', 'iter', 'TWh']},
            {'name': 'gen_uncurt', 'file': 'gen_iter', 'columns': ['tech', 'vintage', 'r', 'year', 'iter', 'TWh']},
        ],
        'preprocess': [
            {'func': pre_curt_iter, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'TWh'}},
        ],
        'presets': collections.OrderedDict((
            ('Explode By Tech',{'x':'year', 'y':'TWh', 'series':'iter', 'explode':'tech', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'gen', }),
        )),
        }
    ),

    ('Curtailment by BA (TWh)',
        {'file':'curt_ann',
        'columns': ['rb','year','TWh'],
        'preprocess': [
                {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column': 'TWh'}},
        ],
        'index': ['rb', 'year'],
        'presets': collections.OrderedDict((
            ('PCA Map Final',{'x':'rb', 'y':'TWh', 'explode':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),
    ('Upgraded Capacity (GW)',
        {'file':'cap_upgrade',
        'columns': ['tech', 'rb', 'year', 'Capacity (GW)'],
        'preprocess': [
#            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['tech', 'year']}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
			('Stacked Bars', {'chart_type':'Bar', 'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'filter': {}}),
#            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
#            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
#            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),
    ('Load (TWh)',
        {'file':'load_rt',
        'columns': ['rb', 'year', 'Load (TWh)'],
        'preprocess': [
            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['year']}},
            {'func': scale_column, 'args': {'scale_factor': .000001, 'column':'Load (TWh)'}},
        ],
        'presets': collections.OrderedDict((
            ('Lines',{'x':'year', 'y':'Load (TWh)', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Production Load (TWh)',
        {'file':'prod_load_ann',
        'columns': ['rb', 'year', 'Load (TWh)'],
        'preprocess': [
            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['year']}},
            {'func': scale_column, 'args': {'scale_factor': .000001, 'column':'Load (TWh)'}},
        ],
        'presets': collections.OrderedDict((
            ('Lines',{'x':'year', 'y':'Load (TWh)', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Production (Million metric tons)',
        {'file':'prod_produce_ann',
        'columns': ['tech', 'rb', 'year', 'Production (Million metric tons)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .000001, 'column':'Production (Million metric tons)'}},
        ],
        'presets': collections.OrderedDict((
			('H2 Stacked Bars', {'chart_type':'Bar', 'x':'year', 'y':'Production (Million metric tons)', 'series':'tech', 'explode':'scenario', 'bar_width':'1.75', 'filter':{'tech':h2_techs}}),
			('DAC CO2 Capture Lines', {'chart_type':'Line', 'x':'year', 'y':'Production (Million metric tons)', 'series':'scenario', 'filter':{'tech':['dac']}}),
        )),
        }
    ),

    ('Hydrogen Price ($/kg)',
        {'file':'prod_h2_price',
        'columns': ['product', 'year', 'Price ($/kg)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Price ($/kg)'}},
            {'func': apply_inflation, 'args': {'column': 'Price ($/kg)'}},
        ],
        'presets': collections.OrderedDict((
			('Lines',{'x':'year', 'y':'Price ($/kg)', 'series':'scenario', 'explode':'product', 'chart_type':'Line'}),
        )),
        }
    ),

    ('H2-CT Fuel Price ($/mmBTU)',
        {'file':'prod_h2comb_cost',
        'columns': ['product', 'year', 'Price ($/mmBTU)'],
        'preprocess': [
            {'func': apply_inflation, 'args': {'column': 'Price ($/mmBTU)'}},
        ],
        'presets': collections.OrderedDict((
			('Lines',{'x':'year', 'y':'Price ($/mmBTU)', 'series':'scenario', 'explode':'product', 'chart_type':'Line', 'filter': {'product':['h2']}}),
        )),
        }
    ),

    ('Retail rate (¢/kWh)',
        {'file': 'retail/retail_rate_USA_centsperkWh.csv',
        'columns': ['t', 'retailrate', 'source'],
        'presets': collections.OrderedDict((
            ('Lines',{'x':'t', 'y':'retailrate', 'series':'source', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Runtime',
        {'sources': [
            {'name':'runtime', 'file':'../meta.csv', 'columns':['computer', 'repo', 'branch', 'commit', 'Unnamed: 4']},
        ],
        'preprocess': [
            {'func': pre_runtime, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'scenario', 'y':'processtime', 'series':'process', 'chart_type':'Bar'}),
            ('Stacked Bars by Year',{'x':'year', 'y':'processtime', 'series':'process', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
        )),
        }
    ),

    ("UPV land area (sq. km.)",
        {'file':'land_use_total.csv',
        'columns': ['year', 'built_capacity_gw', 'built_area_sq_km', 'area_developable_sq_km'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'built_capacity_gw'}},
        ],
        'presets': collections.OrderedDict((
            ('Total UPV land area',{'x':'year', 'y':'built_area_sq_km', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }    
    ),

))

#Add results that are close copies of others
new_result = 'Value Streams Sequential New Techs (uncurt MWh)'
results_meta[new_result] = copy.deepcopy(results_meta['Value Streams Sequential New Techs'])
results_meta[new_result]['sources'].append({'name': 'gen_uncurt', 'file': 'gen_ivrt_uncurt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']})
results_meta[new_result]['preprocess'][0]['args']['uncurt'] = True

new_result = 'Value Streams Sequential Existing Techs (National)'
results_meta[new_result] = copy.deepcopy(results_meta['Value Streams Sequential Existing Techs'])
results_meta[new_result]['preprocess'].append({'func': sum_over_cols, 'args': {'group_cols': ['tech','year','con_adj'], 'val_cols': ['Bulk $ Dis','Bulk $']}})

new_result = 'Competitiveness Sequential New Techs (uncurt MWh)'
results_meta[new_result] = copy.deepcopy(results_meta['Competitiveness Sequential New Techs'])
results_meta[new_result]['sources'].append({'name': 'gen_uncurt', 'file': 'gen_ivrt_uncurt', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']})
results_meta[new_result]['preprocess'][0]['args']['uncurt'] = True

new_result = 'Sys Cost truncated at final year (Bil $)'
results_meta[new_result] = copy.deepcopy(results_meta['Sys Cost beyond final year (Bil $)'])
results_meta[new_result]['sources'][0]['file'] = 'systemcost_bulk_ew'

# new_result = 'Sys Cost Annualized Including Existing (Bil $)'
# results_meta[new_result] = copy.deepcopy(results_meta['Sys Cost Annualized (Bil $)'])
# del results_meta[new_result]['preprocess'][0]['args']['remove_existing']

new_result = 'Capacity BA (GW) [no-index]'
results_meta[new_result] = copy.deepcopy(results_meta['Capacity BA (GW)'])
del results_meta[new_result]['index']

new_result = 'Generation BA (TWh) [no-index]'
results_meta[new_result] = copy.deepcopy(results_meta['Generation BA (TWh)'])
del results_meta[new_result]['index']

new_result = 'New Annual Capacity BA (GW) [no-index]'
results_meta[new_result] = copy.deepcopy(results_meta['New Annual Capacity BA (GW)'])
del results_meta[new_result]['index']

new_result = 'Annual Retirements BA (GW) [no-index]'
results_meta[new_result] = copy.deepcopy(results_meta['Annual Retirements BA (GW)'])
del results_meta[new_result]['index']

#Sort alphabetically
results_meta = collections.OrderedDict(sorted(results_meta.items()))
