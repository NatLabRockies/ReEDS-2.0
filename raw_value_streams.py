'''
This file can be used to combine an mps file (non-pre-solved) and associated marginals
from GAMS gdx solution file to produce value streams for the variables of the model.
'''

import gdxpds
import pandas as pd
from datetime import datetime
import logging
logger = logging.getLogger('')

def get_value_streams(solution_file, mps_file, var_list=None, con_list=None):
    '''
    Create dataframe of value streams for each variable of interest based on variable coefficients
    in an mps file and constraint and variable marginals in the associated GAMS gdx solution file.
    Note that all strings are lowercased because GAMS is case insensitive.
    Args:
        solution_file (string): Full path to GAMS gdx solution file.
        mps_file (string): Full path to the non-presolved mps file of the model associated with the solution file.
        var_list (list of strings): List of lowercased variable names that are of interest. If no list is given,
            value streams will be created for all variables. If a list is given, variables not on the list will be
            filtered out.
        con_list (list of strings): List of lowercased constraint names that are of interest. If no list is given,
            value streams will be created for all constraints. If a list is given, constraints not on the list will be
            filtered out.
    Returns:
        df (pandas dataframe): Value streams of variables with these columns:
            var_name (string): Name of variable.
            var_set (string): Period-seperated sets of the variable.
            con_name (string): Constraint name or '_obj' for objective coefficients.
            con_set (string): Period-seperated sets of the constraint.
            coeff (float): Coefficient of the variable in the constraint or objective.
            var_level (float): Level of the variable in the solution.
            var_marginal (float): Marginal of the variable in the solution.
            con_level (float): Level of the constraint in the solution.
            con_marginal (float): Marginal of the constraint in the solution or -1 for the objective (costs are negative).
            value_per_unit (float): Value per unit of the variable from that constraint (equal to coeff * var_marginal).
            value (float): Value that is produced by the variable from the constraint (equal to var_level * value_per_unit).
    '''
    df_mps = get_df_mps(mps_file, var_list, con_list)
    var_list_mps = df_mps['var_name'].unique()
    con_list_mps = df_mps['con_name'].unique()
    dfs_solution = get_df_solution(solution_file, var_list_mps, con_list_mps)
    df = pd.merge(left=df_mps, right=dfs_solution['vars'], how='left', on=['var_name', 'var_set'], sort=False)
    df = pd.merge(left=df, right=dfs_solution['cons'], how='left', on=['con_name', 'con_set'], sort=False)
    #The objective essentially has a con_marginal of -1
    df.loc[df['con_name']=='_obj','con_marginal'] = -1
    #When variable has a marginal, this marginal must be added as a new row
    df_var_marg = df[df['var_marginal'] != 0].copy()
    df_var_marg.drop_duplicates(inplace=True, subset=['var_name','var_set'])
    df_var_marg['con_name'] = 'var'
    df_var_marg['coeff'] = 1
    df_var_marg['con_marginal'] = df_var_marg['var_marginal']
    #concatenate back into original dataframe
    df = pd.concat([df, df_var_marg], ignore_index=True)
    #Calculate value streams
    df['value_per_unit'] = df['coeff']*df['con_marginal']
    df['value'] = df['value_per_unit']*df['var_level']
    return df

def get_df_mps(mps_file, var_list=None, con_list=None):
    '''
    Create dataframe of coefficients for each variable in each constraint and objective function. Note that all
    strings are lowercased because GAMS is case insensitive.
    Args:
        mps_file (string): Full path to the non-presolved mps file of the model associated with the solution file.
        var_list (list of strings): List of lowercased variable names that are of interest. If no list is given,
            value streams will be created for all variables. If a list is given, variables not on the list will be
            filtered out.
        con_list (list of strings): List of lowercased constraint names that are of interest. If no list is given,
            value streams will be created for all constraints. If a list is given, constraints not on the list will be
            filtered out.
    Returns:
        df (pandas dataframe): Value streams of variables with these columns:
            var_name (string): Name of variable.
            var_set (string): Period-seperated sets of the variable.
            con_name (string): Constraint name or '_obj' for objective coefficients.
            con_set (string): Period-seperated sets of the constraint.
            coeff (float): Coefficient of the variable in the constraint or objective.
    '''

    #First, gather all rows of mps between 'COLUMNS' and 'RHS' into a dataframe,
    #separating the set elements from the variable and constraint names, and separating
    #the coefficients into their own column
    start = datetime.now()
    mps_ls = []
    columns = False
    with open(mps_file) as mpsfile:
        for line in mpsfile:
            if columns:
                if line[:3] == 'RHS':
                    break
                if line[:8] == '    MARK':
                    continue
                #split on whitespace
                ls = line.split()
                if len(ls) > 3:
                    #This means there was whitespace in one of the set elements. We need to recombine list elements.
                    i = 0
                    while i < len(ls):
                        if '(' in ls[i] and ')' not in ls[i]:
                            j = i
                            while ')' not in ls[j]:
                                j = j + 1
                            ls[i:j+1] = [' '.join(ls[i:j+1])]
                        i = i + 1
                var_ls = ls[0].split('(')
                con_ls = ls[1].split('(')
                if (var_list == None or var_ls[0].lower() in var_list) and (con_list == None or con_ls[0].lower() in con_list + ['_obj']):
                    if len(var_ls) == 1:
                        var_ls.append('')
                    else:
                        var_ls[1] = var_ls[1][:-1].replace('"','').replace("'",'')
                    if len(con_ls) == 1:
                        con_ls.append('')
                    else:
                        con_ls[1] = con_ls[1][:-1].replace('"','').replace("'",'')
                    mps_ls.append(var_ls + con_ls + [float(ls[2])])
            elif line[:7] == 'COLUMNS':
                columns = True
    df_mps = pd.DataFrame(mps_ls)
    df_mps.columns = ['var_name','var_set','con_name','con_set', 'coeff']
    for col in ['var_name','var_set','con_name','con_set']:
        df_mps[col] = df_mps[col].str.lower()
    logger.info('mps read: ' + str(datetime.now() - start))
    return df_mps

def get_df_solution(solution_file, var_list_mps, con_list_mps):
    '''
    Create dataframes of marginals and levels of variables and constraints of interest.
    Note that all strings are lowercased because GAMS is case insensitive.
    Args:
        solution_file (string): Full path to GAMS gdx solution file.
        var_list_mps (list of strings): List of lowercased variable names that are of interest.
        con_list_mps (list of strings): List of lowercased constraint names that are of interest.
    Returns:
        dict of two pandas dataframes, one for variables ('vars'), and one for constraints ('cons').
        Columns in the 'vars' dataframe:
            var_name (string): Name of variable.
            var_set (string): Period-seperated sets of the variable.
            var_level (float): Level of the variable in the solution.
            var_marginal (float): Marginal of the variable in the solution.
        Columns in the 'cons' dataframe
            con_name (string): Constraint name.
            con_set (string): Period-seperated sets of the constraint.
            con_level (float): Level of the constraint in the solution.
            con_marginal (float): Marginal of the constraint in the solution.
    '''
    start = datetime.now()
    dfs = gdxpds.to_dataframes(solution_file)
    logger.info('solution read: ' + str(datetime.now() - start))
    start = datetime.now()
    dfs = {k.lower(): v for k, v in list(dfs.items())}
    df_vars = get_df_symbols(dfs, var_list_mps)
    df_vars = df_vars.rename(columns={"Level": "var_level", "Marginal": "var_marginal", 'sym_name':'var_name', 'sym_set': 'var_set'})
    df_cons = get_df_symbols(dfs, con_list_mps)
    df_cons = df_cons.rename(columns={"Level": "con_level", "Marginal": "con_marginal", 'sym_name':'con_name', 'sym_set': 'con_set'})
    logger.info('solution reformatted: ' + str(datetime.now() - start))
    return {'vars':df_vars, 'cons':df_cons}

def get_df_symbols(dfs, symbols):
    '''
    Create dataframes of marginals and levels of symbols of interest.
    Note that all strings are lowercased because GAMS is case insensitive.
    Args:
        dfs (dict of pandas dataframes): A result of gdxpds.to_dataframes(), with keys lowercased.
            Dataframes of gdxpds.to_dataframes() always have separate columns for each set,
            followed by Level, Marginal, Lower, Upper, and Scale columns.
        symbols (list of strings): List of lowercased symbol names that are of interest.
    Returns:
        df_syms (pandas dataframe): dataframe of symbol levels and marginals with these columns:
            sym_name (string): Name of symbol, lowercased
            sym_set (string): Period-seperated sets of the symbol, lowercased
            Level (float): Level of the symbol in the solution.
            Marginal (float): Marginal of the symbol in the solution.
    '''
    df_syms = []
    for sym_name in symbols:
        if sym_name not in dfs:
            continue
        df_sym = dfs[sym_name]
        df_sym['sym_name'] = sym_name
        #concatenate all the set columns into one column
        level_col = df_sym.columns.get_loc('Level')
        df_sym['sym_set'] = ''
        for s in range(level_col):
            set_col = df_sym.iloc[:,s]
            if set_col.str.contains(r'[.\'"()]|  ').any():
                logger.info('Warning: Invalid character (dot, quote, parens, double space) found in column #' + str(s) + ' of ' + sym_name)
            df_sym['sym_set'] = df_sym['sym_set'] + set_col
            if s < level_col - 1:
                df_sym['sym_set'] = df_sym['sym_set'] + '.'
        #reduce to only the columns of interest
        df_sym = df_sym[['sym_name','sym_set','Level','Marginal']]
        df_syms.append(df_sym)
    df_syms = pd.concat(df_syms).reset_index(drop=True)
    for col in ['sym_name','sym_set']:
        df_syms[col] = df_syms[col].str.lower()
    return df_syms