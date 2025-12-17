"""
This module performs the Monte Carlo sampling for ReEDS.
"""


#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import os
import sys
import numpy as np
import pandas as pd
import copy
import argparse
import yaml
import datetime
from typing import Tuple, List
from collections import defaultdict

# Local Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from input_processing import copy_files


#%% ===========================================================================
### --- CONSTANTS ---
### ===========================================================================
class MCSConstants:
    """
    Configuration constants for the Monte Carlo Sampling (MCS) process in ReEDS.
    Contains synonyms, file names for special treatment, and valid distribution identifiers.
    """
    ### --- Synonyms
    TECH_DESCRIPTOR = ['i', '*i', 'type', 'Tech', 'Geo class', 'Depth', 'Turbine', 'tech', '*tech', 'class']
    YEAR_SYNONYMS = ['t', 'Year', 'year']
    REGION_SYNONYMS = ['r', 'region', 'cendiv', 'sc_point_gid', 'FIPS']

    ### --- Fixed columns that should not be modified in most cases
    OTHER_INDICES = ['columns', 'p', '*p'] # 'p' is used in h2_exog_cap.csv
    NONMODIFIABLE_FINANCIAL_COLUMNS = ['debt_fraction', 'tax_rate']
    FIXED_COLUMN_NAMES = YEAR_SYNONYMS + TECH_DESCRIPTOR + OTHER_INDICES + NONMODIFIABLE_FINANCIAL_COLUMNS + REGION_SYNONYMS

    ### --- Files that require special treatment
    SUPPLY_CURVE_FILES = [
        "supplycurve_upv.csv",
        "supplycurve_wind-ofs.csv",
        "supplycurve_wind-ons.csv",
    ]
    EXOG_CAP_FILES = ["exog_cap_upv.csv", "exog_cap_wind-ons.csv"]
    PRESCRIBED_BUILDS_FILES = ["prescribed_builds_wind-ofs.csv", "prescribed_builds_wind-ons.csv"]
    RECF_FILES = ["recf_wind-ons.h5", "recf_wind-ofs.h5", "recf_upv.h5"]

    ### --- Switch-File(s) combinations hardcoded in copy_files.py
    # These files are explicitly handled in copy_files.py, bypassing the standard
    # runfiles.csv instructions. In these cases, the switch is often used as a filter
    # to select specific rows or columns within the file.
    HARD_CODED_SWITCH_TO_FILE_READ = {
        'GSw_H2_Demand_Case': ["h2_exogenous_demand.csv"],
    }

    SITING_SWITCHES = ["GSw_SitingUPV", "GSw_SitingWindOfs", "GSw_SitingWindOns"]

    ### --- Valid distributions
    VALID_DISTRIBUTIONS = ["dirichlet", "discrete", "uniform_multiplier", "triangular_multiplier"]
    MULTIPLICATIVE_DISTRIBUTIONS = ["uniform_multiplier", "triangular_multiplier"]


#%% ===========================================================================
### --- Auxiliary functions ---
### ===========================================================================
def max_decimal_places(data, columns: list = None) -> dict:
    """
    Calculate the maximum number of decimal places in a single number, specific columns, or all columns of a DataFrame.
    
    Args:
    data (pd.DataFrame or numeric): The input DataFrame or a single numeric value (float or int).
    columns (list or None): List of column names to analyze if data is a DataFrame. If None, all columns will be analyzed.
    
    Returns:
    int or dict: 
        - If data is a single number, returns the number of decimal places in the number.
        - If data is a DataFrame, returns a dictionary with column names as keys and their respective maximum number of decimal places as values.
    """
    # Function to count the number of decimals in a single number
    def count_decimals(data):
        if isinstance(data, (float, int, str)) and '.' in str(data):
            return len(str(data).split('.')[1])
        else:
            return 0

    # If we have a single number or a list of numbers
    if not isinstance(data, pd.DataFrame):
        if isinstance(data, (list, np.ndarray)):
            return max([count_decimals(val) for val in data])
        else:
            return count_decimals(data)

    else:
        # If columns is None, analyze all columns
        if columns is None:
            columns = data.keys()

    # Compute the maximum number of decimal places for each specified column
    return {col: data[col].apply(count_decimals).max() for col in columns}


def read_exception_file(sw_assignment: str, file_name: str, file_path: str) -> pd.DataFrame:
    """
    Handles exceptions for files that are hardcoded in copy_files.py
    and written directly without using runfiles.csv.

    This function allows you to manually support special cases where
    a switch-file combination is not automatically handled by the MCS module.
    If you encounter a new unsupported case, you can add it here.

    Args:
        sw_assignment (str): The switch assignment.
        file_name (str): Name of the file (output filename).
        file_path (str): Path to the reference file (inputs folder).

    Returns:
        pd.DataFrame: A DataFrame formatted as expected before being written 
        to the inputs_case folder (as in copy_files.py).
    """
    if file_name == 'h2_exogenous_demand.csv':
        # h2_exogenous_demand.csv has a path in runfiles.csv (considered a non-region file)
        df = pd.read_csv(file_path, index_col=['p', 't'])
        df = df[sw_assignment].round(3).rename_axis(['*p', 't']).reset_index()

        # Rename the value column to 'million_tons' to avoid issues in writecapdat.py
        df.rename(columns={sw_assignment: 'million_tons'}, inplace=True)
        return df

    return None


def read_csv_h5_file(sw_runfiles_csv, aux_files, reeds_path, inputs_case) -> pd.DataFrame:
    """
    This function reads a csv or h5 file based on a row of runfiles.csv and returns a dataframe with the data
    in the ReEDS format.

    Args:
        sw_runfiles_csv (pd.Series): A row of runfiles.csv with sw preassigned to the filepath.
        aux_files (dict): A dictionary with auxiliary information for the copy_files.py module.
        reeds_path (str): The path to the ReEDS directory.
        inputs_case (str): The path to the inputs case directory.

    Returns:
        pd.DataFrame: A DataFrame with the data in the ReEDS format.
    """
    # Obtain the data used by copy_files.py to filter regions and create tailored dataframes 
    nonregion_files = aux_files['nonregion_files']
    region_files = aux_files['region_files']
    file_name = sw_runfiles_csv['filename']
    file_path = os.path.join(reeds_path, sw_runfiles_csv['full_filepath'])

    # Try to read the file using the read_exception_file function first
    df = read_exception_file(sw_runfiles_csv['sw_assignment'], file_name, file_path)
    if df is not None:
        return df

    if file_name in region_files['filename'].values:
        # Regional file (works for both csv and h5)
        df = copy_files.subset_to_valid_regions(
            aux_files['sw'],
            sw_runfiles_csv,
            aux_files['agglevel_variables'],
            aux_files['regions_and_agglevel'],
            inputs_case,
            agg=False,
        )

    elif file_name in nonregion_files['filename'].values:
        files_not_supported = ['scalars.csv']
        if file_path.endswith('.csv') and file_name not in files_not_supported:
            #Read the csv file
            df = pd.read_csv(file_path)
        else:
            #File not implemented yet
            error_message = 'The file %s has not been implemented yet' % sw_runfiles_csv['filename']
            raise ValueError(error_message + ' improve function read_csv_h5_file')

    elif file_name in ['switches.csv']:
        df = pd.read_csv(os.path.join(inputs_case, file_name),
            header = None, index_col=0, dtype=str)

    else:
        error_message = (
            f"The file '{file_name}' is not classified under nonregion_files or region_files, "
            "and it is not currently handled by the read_exception_file function. "
            "If you want to use this switch-file combination in MCS, please update the read_exception_file function "
            "and add an entry to MCSConstants.HARD_CODED_SWITCH_TO_FILE_READ."
        )
        raise ValueError(error_message)

    return df


def get_hierarchy_file(inputs_case: str, ReEDS_resolution: str) -> pd.DataFrame:
    """
    The hierarchy file in `{inputs_case}/hierarchy.csv` does not contain a
    differentiation between "ba" and "aggreg" resolution. This function
    reconstructs the hierarchy file with all possible combinations relevant
    to the MCS.

    Args:
        inputs_case (str): Path to the inputs case directory.
        ReEDS_resolution (str): The spatial resolution used in ReEDS (e.g., 'ba', 'aggreg').

    Returns:
        pd.DataFrame: A DataFrame with the hierarchy information relevant to the regions
            considered in the inputs_casse run.
    """
    original_hierarchy_file = pd.read_csv(
        os.path.join(inputs_case, "hierarchy_original.csv")
    )

    valid_regions = pd.read_csv(
        os.path.join(inputs_case, "hierarchy.csv")
    )['*r'].values

    filtered_hierarchy  = original_hierarchy_file[
        original_hierarchy_file[ReEDS_resolution].isin(valid_regions)
    ].reset_index(drop=True)

    return filtered_hierarchy


#%% ===========================================================================
### --- FILE PATHS & DISTRIBUTION INSTRUCTIONS ---
### ===========================================================================
def mcs_find_copy_paths(
    sw_name: str,
    sw_assignments: list,
    runfiles: pd.DataFrame,
    reeds_path: str,
    inputs_case: str,
    run_ReEDS: bool = True
) -> Tuple[list, pd.DataFrame]:
    """
    Find the paths where the MCS samples should be copied to and the associated runfiles.csv rows.

    Args:
        sw_name (str): The name of the switch being sampled.
        sw_assignments (list): The assignments for the switch.
        runfiles (pd.DataFrame): The runfiles.csv DataFrame.
        reeds_path (str): The path to the ReEDS directory.
        inputs_case (str): The path to the inputs case directory.
        run_ReEDS (bool): Whether to run the ReEDS model or not.

    Returns:
        save_path_list: A list of destination paths for the MCS samples.
        runfile_instructions: The runfiles.csv rows associated with the switch.
    """
    # Find if the switch name needs to be assigned to a specific file path in runfiles.csv
    rf_contains_sw = runfiles['filepath'].fillna('').str.contains('{' + sw_name + '}')
    if any(rf_contains_sw):
        runfile_instructions = runfiles[rf_contains_sw].reset_index(drop=True)
    elif sw_name in MCSConstants.HARD_CODED_SWITCH_TO_FILE_READ:
        # If the switch name is found in the hardcoded exceptions, fid the rows 
        # in runfiles.csv that contain all the files associated with the switch.
        runfile_instructions = runfiles[
            runfiles['filename'].isin(MCSConstants.HARD_CODED_SWITCH_TO_FILE_READ[sw_name])
        ].reset_index(drop=True)
    else:
        # If the switch name is not found in runfiles.csv, or in the hardcoded exceptions, 
        # assume it is only part of switches.csv
        runfile_instructions = runfiles[runfiles['filename'] == 'switches.csv'].reset_index(drop=True)

    # Reorder rows: if any filename has "supply_curve", place those rows first.
    # For siting data we need to sample the supply curve data first 
    # (CF,... is dependent on the supply curve data)
    if runfile_instructions['filename'].str.contains('supply_curve', na=False).any():
        supply_curve_rows = runfile_instructions[runfile_instructions['filename'].str.contains('supply_curve', na=False)]
        other_rows = runfile_instructions[~runfile_instructions['filename'].str.contains('supply_curve', na=False)]
        runfile_instructions = pd.concat([supply_curve_rows, other_rows], ignore_index=True)

    # Iterate through each instruction to determine the destination paths.
    # Since some switches point to multiple files, you can have multiple destination paths.
    save_path_list = []
    for _, row in runfile_instructions.iterrows():
        file_name = row['filename']

        if run_ReEDS:
            dest_path = os.path.join(inputs_case, file_name)
        else:
            # Save samples at runs/Sample_ for later use. Useful for checking the samples.
            dest_path = os.path.join(
                reeds_path, 'runs', 'Sample_{sample_n}', file_name
            )
        save_path_list.append(dest_path)
    
    # Supply curve files are used in other distributions, so they need to be first in the list.
    # This should be cleaned up.
    if any([os.path.basename(i).startswith('supplycurve') for i in save_path_list]):
        supplycurve_index = [
            i for (i,f) in enumerate(save_path_list)
            if os.path.basename(f).startswith('supplycurve')
        ][0]
        other_indices = [i for i in range(len(save_path_list)) if i != supplycurve_index]
        index_order = [supplycurve_index] + other_indices
        save_path_list = [save_path_list[i] for i in index_order]
        runfile_instructions = runfile_instructions.loc[index_order].reset_index(drop=True)

    return save_path_list, runfile_instructions


def general_mcs_dist_validation(reeds_path: str, mcs_dist_path: str, sw: pd.Series) -> None:
    """
    Validate the contents of mcs_distributions_{MCS_dist}.yaml used for Monte Carlo sampling.

    Args:
        reeds_path (str): Path to the ReEDS directory.
        mcs_dist_path (str): Path to the input .yaml file.
        sw (pd.Series): Case switches 

    Raises:
        ValueError: If any structure or content in the .yaml file is invalid.
    """
    print('Validating the input distribution information for Monte Carlo sampling...')

    with open(mcs_dist_path, 'r') as f:
        data = yaml.safe_load(f)
        df_input_dist = pd.DataFrame(data)

    mcs_dist_groups = sw['MCS_dist_groups'].split('.')

    # Read cases.csv to get the list of valid switches.
    cases_default = pd.read_csv(os.path.join(reeds_path, 'cases.csv'))
    valid_switches = cases_default.iloc[:, 0].values

    # Validate mandatory keys in df_input_dist
    required_keys = {'name', 'assignments_list', 'dist', 'dist_params', 'weight_r'}
    missing_keys = required_keys - set(df_input_dist.columns)
    if missing_keys:
        raise ValueError(f"Missing mandatory keys in mcs_distributions.yaml object: {missing_keys}")

    # Make sure that dist_params is a list
    if not all(isinstance(df_input_dist.at[i, 'dist_params'], list) for i in range(len(df_input_dist))):
        raise ValueError('The dist_params field must be a list')

    # Verify that all dist group names in mcs_distributions.yaml are unique.
    if df_input_dist['name'].nunique() != len(df_input_dist):
        raise ValueError('The distribution names in mcs_distributions.yaml are not unique. Please correct the file')

    # Ensure that we are not missing data for each row of the input distribution file.
    missing_data = df_input_dist.isnull().sum(axis=1)
    if missing_data.any():
        raise ValueError(f"The following dist names have missing data: {df_input_dist.loc[missing_data > 0, 'name'].values}. "
                        "Make sure you have all mandatory fields in the input distribution file")

    # Ignore all cases not in mcs_dist_groups
    df_input_dist = df_input_dist[df_input_dist['name'].isin(mcs_dist_groups)].reset_index(drop=True)
    
    # Ensure all MCS_dist_groups options are present in the input distribution names.
    missing = set(mcs_dist_groups) - set(df_input_dist['name'].unique())
    if missing:
        raise ValueError(f"The following MCS_dist_groups switch options are missing in mcs_distributions.yaml {missing}")

    for i, sample_group in df_input_dist.iterrows():
        distribution = sample_group['dist']

        switch_names = [next(iter(s)) for s in sample_group["assignments_list"]]
        sw_assignments = [next(iter(s.values())) for s in sample_group["assignments_list"]]

        for d in sample_group["assignments_list"]:
            if not (isinstance(d, dict) and len(d) == 1):
                raise ValueError("Each item in assignments_list must be a single-key dictionary")

            val = next(iter(d.values()))
            if not isinstance(val, list):
                raise ValueError("The value in each dictionary must be a list")

        if distribution not in ["dirichlet", "discrete"] and any(
            switch in MCSConstants.SITING_SWITCHES for switch in switch_names
        ):
            raise ValueError(
                "The siting related switches can only be sampled "
                "using a dirichlet or discrete distribution"
                )

        if distribution not in MCSConstants.VALID_DISTRIBUTIONS:
            raise ValueError(
                f"The distribution {distribution} is not supported."
                f"Please choose one of the following: {MCSConstants.VALID_DISTRIBUTIONS}")

        if distribution in MCSConstants.MULTIPLICATIVE_DISTRIBUTIONS:
            num_files = np.max([len(c) for c in sw_assignments])
            if num_files > 1:
                raise ValueError(
                    f"The distribution {distribution} can only have a single reference file/value per switch."
                )

        # Iterate over each switch in the instruction.
        for sw_name in switch_names:
            # Check if the switch is valid.
            if sw_name not in valid_switches:
                raise ValueError(f'The switch {sw_name} is not a valid switch. Please check cases.csv')


def get_dist_instructions(reeds_path: str, inputs_case: str, run_ReEDS: bool = True) -> Tuple[pd.DataFrame, dict]:
    """
    Obtain the instructions to sample the distributions for each switch 
    and organize information to facilitate the Monte Carlo sampling process.

    Args:
        reeds_path (str): The path to the ReEDS directory.
        inputs_case (str): The path to the inputs case directory.
        run_ReEDS (bool): Whether to run the ReEDS model or not.

    Returns:
        df_input_dist_ex: A DataFrame with the distribution instructions for each switch.
        aux_files: A dictionary with auxiliary information (mostly used in the copy_files.py module).
    """
    print('Reading the input distribution information for Monte Carlo sampling')

    # Read yaml file with the input distribution information.
    mcs_dist_path = os.path.join(inputs_case, 'mcs_distributions.yaml')
    with open(mcs_dist_path, 'r') as f:
        data = yaml.safe_load(f)
        df_input_dist = pd.DataFrame(data)

    sw = reeds.io.get_switches(inputs_case)
    mcs_dist_groups = sw['MCS_dist_groups'].split('.')

    if not run_ReEDS:
        # Since you did not run using runbatch.py - check inputs here
        general_mcs_dist_validation(reeds_path, mcs_dist_path, sw)

    # Ignore all cases not in mcs_dist_groups
    df_input_dist = df_input_dist[df_input_dist['name'].isin(mcs_dist_groups)].reset_index(drop=True)

    # Expand df_input_dist with new information to facilitate the Monte Carlo sampling process.
    # Sample ID here is used to uniquely identify each sample-process.
    df_input_dist_ex = df_input_dist.copy(deep=True)
    for col in ['Sample_ID', 'switch_names', 'sw_assignments', 'file_names', 'save_paths', 'runfiles_csv']:
        df_input_dist_ex[col] = [[] for _ in range(len(df_input_dist))]

    # Save reeds_path and inputs_case for future use.
    df_input_dist_ex['reeds_path'] = reeds_path
    df_input_dist_ex['inputs_case'] = inputs_case

    agglevel_variables = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)
    # Read runfiles.csv to get instructions on how files must be copied.
    runfiles, nonregion_files, region_files = copy_files.read_runfiles(
        reeds_path, inputs_case, sw, agglevel_variables)

    ReEDS_resolution = sw['GSw_RegionResolution']
    # Process each distribution instruction.
    for i, input_dist_row in df_input_dist.iterrows():

        # If ReEDS_resolution is aggreg but weight_r is 'ba' change it to aggreg
        if ReEDS_resolution == 'aggreg' and input_dist_row['weight_r'] == 'ba':
            df_input_dist_ex.at[i, 'weight_r'] = 'aggreg'
            print(f"[Warning]: The weight_r for {input_dist_row['name']} was changed to 'aggreg'")

        # Iterate over each switch in the instruction.
        for sw_i, assignments_list in enumerate(input_dist_row['assignments_list']):

            sw_name, sw_assignments = next(iter(assignments_list.items()))

            filepaths, runfiles_csv = mcs_find_copy_paths(
                sw_name, sw_assignments, runfiles, reeds_path, inputs_case, run_ReEDS=run_ReEDS
            )

            # handle cases where a single switch assignment is associated with multiple files and cases
            # related to switches.csv, where multiple float switches may be associated with the same file.
            for j in range(len(filepaths)):
                file_name = runfiles_csv.iloc[j]['filename']
                df_input_dist_ex.at[i, 'switch_names'].append(sw_name)
                df_input_dist_ex.at[i, 'sw_assignments'].append(sw_assignments)
                df_input_dist_ex.at[i, 'save_paths'].append(filepaths[j])
                df_input_dist_ex.at[i, 'runfiles_csv'].append(runfiles_csv.iloc[j])
                df_input_dist_ex.at[i, 'file_names'].append(runfiles_csv.iloc[j]['filename'])

                if file_name != 'switches.csv':
                    df_input_dist_ex.at[i, 'Sample_ID'].append(f'{file_name}')
                else:
                    df_input_dist_ex.at[i, 'Sample_ID'].append(f'{sw_name}')

    # Obtain the data used by copy_files.py to filter regions and create tailored dataframes.
    regions_and_agglevel = copy_files.get_regions_and_agglevel(
        reeds_path, inputs_case, save_regions_and_agglevel=False)

    source_deflator_map = copy_files.get_source_deflator_map(reeds_path)

    hierarchy_file = get_hierarchy_file(inputs_case, sw['GSw_RegionResolution'])

    # Save the auxiliary info in a dictionary.
    aux_files = {
        'sw': sw,
        'nonregion_files': nonregion_files,
        'region_files': region_files,
        'source_deflator_map': source_deflator_map,
        'regions_and_agglevel': regions_and_agglevel,
        'agglevel_variables': agglevel_variables,
        'hierarchy_file': hierarchy_file,
    }

    return df_input_dist_ex, aux_files


#%% ===========================================================================
### --- WEIGHT CALCULATION ---
### ===========================================================================
def get_region_weights(distribution: str, dist_params: list, n_samples: int = 1) -> np.ndarray:
    """
    Generate weights for a single region based on the assigned distribution.

    Args:
        distribution (str): The distribution to use for sampling.
        dist_params (list): The parameters for the distribution.
        n_samples (int): The number of samples to generate.

    Returns:
        np.ndarray: The weights for the region-based sample ([n_samples, n_ref_files|values]).
    """
    if distribution == "dirichlet":
        r_weights = np.random.dirichlet(dist_params, n_samples)

    elif distribution == "discrete":
        prob = np.array(dist_params) / np.sum(dist_params)
        sampled_indices = np.random.choice(len(dist_params), n_samples, p=prob)
        r_weights = np.zeros((n_samples, len(dist_params)), dtype=int)
        r_weights[np.arange(n_samples), sampled_indices] = 1

    elif distribution == "uniform_multiplier":
        r_weights = np.random.uniform(dist_params[0], dist_params[1], n_samples)

    elif distribution == "triangular_multiplier":
        r_weights = np.random.triangular(dist_params[0], dist_params[1], dist_params[2], n_samples)

    # Make sure r_weights is a 2D array
    if r_weights.ndim == 1:
        r_weights = r_weights[:, np.newaxis]

    return r_weights


def get_all_region_weights(
    distribution: str,
    dist_params: list,
    hierarchy_file: pd.DataFrame,
    sample_hierarchy_lvl: str = 'country',
) -> dict:
    """
    Get the weights for all unique regions in sample_hierarchy_lvl and map them to the
    relevant BAs and cendivs, levels. Those may be adjusted later for supply curve files
    (in this case they may be combined with capacity data)

    Args:
        distribution (str): The distribution to use for sampling.
        dist_params (list): The parameters for the distribution.
        hierarchy_file (pd.DataFrame): DataFrame with the hierarchy information from get_hierarchy_file (.)
        sample_hierarchy_lvl (str): The hierarchy level which will be assigned unique weights.

    Returns:
        dict: Dictionary with the weights for each region.
    """

    # Only needs to map weights to 'ba', and 'cendiv'
    # levels since these are the only levels relevant to the files changed in the mcs sampling
    all_r_weights = {} 
    unique_sample_levels = hierarchy_file[sample_hierarchy_lvl].unique()

    for region in unique_sample_levels:
        # Generate region weights based on the specified distribution
        r_weights = get_region_weights(distribution, dist_params)

        # Retrieve all BAs linked to the current region
        bas = hierarchy_file.loc[hierarchy_file[sample_hierarchy_lvl] == region, "ba"].values

        # Assign weights to each BA, cendiv, and aggreg
        for ba in bas:
            all_r_weights[ba] = r_weights

        # Only save the cendiv weights if the sample_hierarchy_lvl is 'country' or 'cendiv'
        if sample_hierarchy_lvl in ["country", "cendiv"]:
            cendivs = hierarchy_file.loc[hierarchy_file[sample_hierarchy_lvl] == region, "cendiv"].unique()
            for cendiv in cendivs:
                all_r_weights[cendiv] = r_weights

    return all_r_weights


class WeightCalculator:
    """
    Computes region-based weights for Monte Carlo Sampling in ReEDS.

    Args:
        sample_group (pd.Series): a series with information about the sample group - from get_dist_instructions(.).
            This contains the distribution, dist_params, switch_names, sw_assignments, file_names, save_paths, ...
            It is a row of the df_input_dist_ex DataFrame.
        aux_files (dict): Dictionary with auxiliary information - from get_dist_instructions (.)
        n_samples (int): The number of samples
    """
    def __init__(
        self,
        sample_group: pd.Series,
        aux_files: dict,
        n_samples: int = 1,
    ):
        self.sample_group = sample_group
        self.aux_files = aux_files
        self.distribution = sample_group['dist']
        self.dist_params = sample_group['dist_params']
        self.sample_hierarchy_lvl = sample_group['weight_r'].lower()
        self.hierarchy_file = aux_files['hierarchy_file']
        self.n_samples = n_samples

        # Get all general region weights
        self.r_weights = get_all_region_weights(
            self.distribution, self.dist_params, self.hierarchy_file, self.sample_hierarchy_lvl)
        ## Include aggregated region weights
        if aux_files['sw']['GSw_RegionResolution'] == 'aggreg':
            self.r_weights = {
                **self.r_weights,
                **{
                    aux_files['hierarchy_file'].set_index('ba').aggreg.get(k,k): v
                    for k,v in self.r_weights.items()
                },
            }

        # Store the weights for the recf files (CF files)
        # Those are computed during the the supply curve file sampling 
        self.recf_weights_map = {}

        # Flag to validade that recf_weights_map was normalized
        self.flag_recf_normalization = defaultdict(lambda: False)

    def _validate_inputs(self, dist_files: list, sw_name: str, file_name: str) -> None:
        """
        Validate inputs

        Args:
            dist_files (list of pd.DataFrame): List of reference dataframes (ajusted to have the same # of rows)
            sw_name (str): Name of the switch we are getting the weights for.
            file_name (str): Name of the file we are getting the weights for.
        """
        # Identify relevant columns that exist in the hierarchy
        #Examples: p1, p2, New_England, ...(covers NG and LOAD)
        columns_in_hierarchy = [col for col in dist_files[0].keys() if col in set(self.r_weights.keys())]

        # Columns that start with region, r, ...
        generic_region_columns = [col for col in dist_files[0].keys() if col in MCSConstants.REGION_SYNONYMS]

        # We have as many unique weights as len(unique_sample_levels)
        unique_sample_levels = self.hierarchy_file[self.sample_hierarchy_lvl].unique()
        single_r_weight = len(unique_sample_levels) == 1

        # Group files that require special treatment
        except_files = MCSConstants.SUPPLY_CURVE_FILES + MCSConstants.EXOG_CAP_FILES + (
            MCSConstants.PRESCRIBED_BUILDS_FILES + MCSConstants.RECF_FILES)

        # Return an error if you have multiple weight assignments but the mcs_distributions.yaml object is
        # pointing to a set of switches that have no region columns
        # e.g. asking for a region-based sampling for swicthes.csv, or plantchar type files.
        if not single_r_weight and not columns_in_hierarchy and not generic_region_columns and ( 
            file_name not in except_files):
            raise ValueError(
                f"Invalid sampling configuration for file: {file_name}\n"
                f"Switch: {sw_name}\n"
                f"weight_r group: {self.sample_hierarchy_lvl}\n"
                "[Error] Either:\n"
                "  1. The file does not contain any regional columns but was assigned"
                " to a region-based sampling group different than country, or\n"
                "  2. The selected weight_r resolution is not valid for this file"
                " (e.g., BA for NG fuel prices, which are based on cendiv).\n\n"
                "Please review the `mcs_distributions.yaml` configuration."
            )

        # Check if all elements in dist_files have the same index
        if not all(df.index.equals(dist_files[0].index) for df in dist_files):
            raise ValueError(
                f"Invalid sampling configuration for file: {file_name}\n"
                f"Switch: {sw_name}\n"
                "All reference files must have the same indexes"
            )

        # Check if the distribution is multiplicative and the file has a year column
        if self.distribution in MCSConstants.MULTIPLICATIVE_DISTRIBUTIONS:
            if dist_files[0].columns.isin(MCSConstants.YEAR_SYNONYMS).any():
                raise ValueError(
                    "Files with year columns are not supported for multiplicative distributions. "
                    f"Change the distribution for switch {sw_name}"
                )

    def get_df_weights(
        self,
        dist_files: list,
        modifiable_columns: list,
        sw_name: str,
        file_name: str,
    ) -> dict:
        """
        Dispatch to the appropriate method based on file type.

        Args:
            dist_files (list of pd.DataFrame): List of reference dataframes (ajusted to have the same # of rows)
            modifiable_columns (list of str): List of columns that can be directly multiplied by the weights.
            sw_name (str): Name of the switch we are getting the weights for.
            file_name (str): Name of the file we are getting the weights for.

        Returns:
            dict: Dictionary with the weights for each reference file and sample.
        """

        self._validate_inputs(dist_files, sw_name, file_name)

        if file_name in MCSConstants.SUPPLY_CURVE_FILES:
            return self._get_weights_supply_curve(dist_files, modifiable_columns, sw_name)
        elif file_name in MCSConstants.RECF_FILES:
            return self._get_weights_recf(sw_name)
        elif file_name in MCSConstants.EXOG_CAP_FILES + MCSConstants.PRESCRIBED_BUILDS_FILES:
            return self._get_weights_exog_prescribed(dist_files)
        else:
            return self._get_weights_general(dist_files, modifiable_columns, sw_name, file_name)

    def _get_weights_general(
        self,
        dist_files: list,
        modifiable_columns: list,
        sw_name: str,
        file_name: str
    ) -> dict:  
        """
        Get weights for a general file that does not require special treatment.
        Files that require special treatment are those associated with 
        supply curve switches.

        Args:
            dist_files (list of pd.DataFrame): List of reference dataframes (ajusted to have the same # of rows)
            modifiable_columns (list of str): List of columns that can be directly multiplied by the weights.
            sw_name (str): Name of the switch we are getting the weights for.
            file_name (str): Name of the file we are getting the weights for.

        Returns:
            dict: Dictionary with the weights for each reference file and sample.
        """
        # Number of reference files/values. Sicne all sw_assignments
        # have the same number of files, we can use the first one.
        n_files = len(self.sample_group["sw_assignments"][0]) 

        # Identify relevant columns that exist in the hierarchy
        #Examples: p1, p2, New_England, ...(covers NG and LOAD)
        columns_in_hierarchy = [col for col in dist_files[0].keys() if col in set(self.r_weights.keys())]

        # We have as many unique weights as len(unique_sample_levels)
        unique_sample_levels = self.hierarchy_file[self.sample_hierarchy_lvl].unique()
        single_r_weight = len(unique_sample_levels) == 1

        # Dictionary to store computed weights for the modifiable columns
        # (sample, file) -> pd.DataFrame
        dict_df_weights = {}

        # Handle the simple case where there is only one weight for all regions 
        # (or no regions). 
        if single_r_weight:
            # Get the first region key
            first_region = next(iter(self.r_weights)) 
            weight_matrix = self.r_weights[first_region]

            if file_name == "switches.csv":
                for s in range(self.n_samples):
                    for f in range(n_files):
                        dict_df_weights[(s, f)] = weight_matrix[s, f]
            else:
                for s in range(self.n_samples):
                    for f in range(n_files):
                        dict_df_weights[(s, f)] = pd.DataFrame(
                                data=weight_matrix[s, f],
                                columns=modifiable_columns,
                                index=dist_files[0].index,
                        )

        # Cases that have regional columns from columns_in_hierarchy
        # and the weights are not the same for all regions
        elif not single_r_weight and len(columns_in_hierarchy) and file_name != "switches.csv" :
            for s in range(self.n_samples):
                for f in range(n_files):

                    w_df_tmp = pd.DataFrame(
                        {col: self.r_weights[col][s, f] for col in columns_in_hierarchy},  
                        index=dist_files[0].index 
                    )

                    dict_df_weights[(s, f)] = w_df_tmp

        return dict_df_weights

    def _get_weights_supply_curve(
        self,
        dist_files: list,
        modifiable_columns: list,
        sw_name: str
    ) -> dict:
        """
        Get the weights for supply curve files. These files require special treatment
        because some columns are dependent on the capacity of each sc_point_gid.

        Args:
            dist_files (list of pd.DataFrame): List of reference dataframes (ajusted to have the same # of rows)
            modifiable_columns (list of str): List of columns that can be directly multiplied by the weights.
            sw_name (str): Name of the switch we are getting the weights for.

        Returns:
            dict: Dictionary with the weights for each reference file and sample.
        """
        # Dictionary to store computed weights for the modifiable columns
        # (sample, file) -> pd.DataFrame
        dict_df_weights = {}

        # Store weights to use later in the recf files (CF files)
        self.recf_weights_map [sw_name] = {}

        # Create a new column with the class|region combination (like in the CF file)
        dist_files_copy = [copy.deepcopy(df) for df in dist_files] 

        for df in dist_files_copy:
            df["old c|r"] = (
                df["class"].astype(int).astype(str) + "|" + df["region"].astype(str)
            )

        for s in range(self.n_samples):
            for f, df in enumerate(dist_files_copy):
                # Initial skeleton of the weights DataFrame
                w_df_tmp = df[["region", "sc_point_gid", "old c|r"]]

                # Create a mapping from each unique region to its corresponding weight
                region_to_weight = {
                    r: self.r_weights[r][s, f]
                    for r in w_df_tmp["region"].unique()
                }

                # Compute the region weights for each row
                region_weights = w_df_tmp["region"].map(region_to_weight).values

                # Build a new DataFrame for the modifiable columns using a dict comprehension.
                # For "capacity", we assign the raw region weight; for others, multiply by capacity.
                modifiable_df = pd.DataFrame({
                    col: (region_weights if col == "capacity" else region_weights * df["capacity"])
                    for col in modifiable_columns
                }, index=w_df_tmp.index)

                # Join the modifiable columns back into the original DataFrame
                w_df_tmp = w_df_tmp.join(modifiable_df)

                # Save the intermediate weights for the recf files (These are weights multiplied by capacity)
                self.recf_weights_map [sw_name][(s, f)] = w_df_tmp[["old c|r","class"]].rename(columns={"class": "weight"})

                # Store in dictionary
                dict_df_weights[(s, f)] = w_df_tmp.drop(columns=["old c|r"])

            # Normalize the weights to sum to 1
            # Divide the weights by the sum of the weights across all files
            sum_weights = sum(dict_df_weights[(s, f)][modifiable_columns] for f in range(len(dist_files)))
            sum_weights[sum_weights == 0] = 1

            for f in range(len(dist_files)):
                dict_df_weights[(s, f)][modifiable_columns] /= sum_weights
                # recf_weights_map is not normalized here because it will be normalized later
                # values need to be aggregated according to the new c|r column from supply curves

        return dict_df_weights

    def _get_weights_exog_prescribed(self, dist_files: list) -> dict:
        """
        Get the weights for exogenous capacity and prescribed builds files.

        Args:
            dist_files (list of pd.DataFrame): List of reference dataframes (ajusted to have the same # of rows)

        Returns:
            dict: Dictionary with the weights for each reference file and sample.
        """
        dict_df_weights = {}
        for s in range(self.n_samples):
            for f, df in enumerate(dist_files):

                region_to_weight = {
                    r: self.r_weights[r][s, f]
                    for r in df["region"].unique()
                }

                dict_df_weights[(s, f)] = pd.DataFrame(
                    data=df["region"].map(region_to_weight).values,
                    columns=["capacity"],
                    index=df.index,
                )

        return dict_df_weights

    def _get_weights_recf(self, sw_name: str) -> dict:
        """
        Get the weights for the recf files (CF files). This file construction is 
        dependent on the new supply curve samples and therefore is computed after
        the supply curve files are sampled.

        Args:
            sw_name (str): Name of the switch we are getting the weights for.
        """
        # From get_dist_instructions(.) the supply curve file is deliberaly
        # placed before the recf files, so that recf_weights_map is already populated.

        # Check if recf_weights_map is not empty and that it was normalized.
        if not self.recf_weights_map[sw_name]:
            raise ValueError(
                f"The recf_weights_map for switch {sw_name} was not populated"
            )

        if not self.flag_recf_normalization[sw_name] :
            raise ValueError(
                f"The recf_weights_map for switch {sw_name} was not normalized"
            )

        return self.recf_weights_map[sw_name]

    def normalize_recf_weights_map(self, samples_sw: list, sw_name: str) -> None:
        """
        The recf map is responsible for informing how the old class/region data files
        need to be put together (weights) to form the new class/region data.
        After creating the new supply curve sample, we normalize the weights to sum to 1.

        Args:
            samples_sw (list of pd.DataFrame): List of samples for the supply curve files.
            sw_name (str): Name of the switch being sampled.

        Updates:
            self.recf_weights_map (dict): Dictionary with the normalized weights for the recf files.
                Each element of this dictionary is a pd.DataFrame (for the sample s and reference file f)
                with the normalized weights, indexed by new and old class|region (c|r).
        """
        n_files = len({key[1] for key in self.recf_weights_map[sw_name].keys()})

        for s in range(self.n_samples):
            # The normalization can change depending on the sample #
            for f in range(n_files):
                # Add a new column with the new class|region combination
                self.recf_weights_map[sw_name][(s, f)]["new c|r"] = (
                    samples_sw[s]["class"].astype(str) + "|" +
                    samples_sw[s]["region"].astype(str)
                )

                # Sum the weights for each new class|region combination
                self.recf_weights_map[sw_name][(s, f)] = self.recf_weights_map[sw_name][(s, f)].groupby(
                    ["new c|r","old c|r"], as_index=False).sum()

                # Remove cases with 0 weight (e.g  old c|r had no capacity -> class 0)
                self.recf_weights_map[sw_name][(s, f)] = self.recf_weights_map[sw_name][(s, f)][
                    self.recf_weights_map[sw_name][(s, f)]["weight"] > 0
                ]

            # Go over all files and obtain the total sum of weights for each new class|region
            sum_weights_recf_map = (
                pd.concat(
                    [self.recf_weights_map[sw_name][(s, f)] for f in range(n_files)]
                )
                .groupby("new c|r")["weight"]
                .sum()
                .to_dict()
            )

            for f in range(n_files):
                # Get current DataFrame
                df = self.recf_weights_map[sw_name][(s, f)]
                # Perform division using "new c|r" as the reference
                df["weight"] = df["weight"] / df["new c|r"].map(sum_weights_recf_map)
                # Assign back to original structure
                self.recf_weights_map[sw_name][(s, f)] = df.set_index(["new c|r", "old c|r"])   

        # Flag to validade that recf_weights_map was normalized
        self.flag_recf_normalization[sw_name] = True 


#%% ===========================================================================
### --- MAIN SAMPLING CLASS ---
### ===========================================================================
class MCS_Sampler:
    """
    Monte Carlo Sampling Distribution Manager for ReEDS.

    This class allows enforcing sampling variability at different ReEDS regions
    (st, ba, ...) and enforcing correlation between samples from differen switches.

    The following sampling strategies have been implemented:

    1. Dirichlet Sampling:
       - Generates a Dirichlet sample (h1, ..., hn) ~ Dir(alpha1, ..., alphan).
       - Uses these weights to compute a weighted average of reference files:
           sample = h1*f1 + ... + hn*fn

    2. Discrete Sampling:
        - Chooses a single reference file based on a discrete probability distribution.

    3. Multiplicative Sampling:
       - Applies a random multiplier to a single reference file or switch.
       - The multiplier is drawn from a uniform or triangular distribution:
           sample = multiplier * f

    """
    def __init__(self, sample_group, aux_files, n_samples=1):
        self.sample_group = sample_group
        self.aux_files = aux_files
        self.n_samples = n_samples

        # Derive parameters from inputs
        self.reeds_path = sample_group['reeds_path']
        self.inputs_case = sample_group['inputs_case']
        self.distribution = sample_group['dist']
        self.dist_params = sample_group['dist_params']
        self.ReEDS_resolution = aux_files['sw']['GSw_RegionResolution']
        if self.ReEDS_resolution=='aggreg' and sample_group['weight_r']=='ba':
            self.sample_hierarchy_lvl = 'aggreg'
        else:
            self.sample_hierarchy_lvl = sample_group['weight_r']

        # Inputs that require special treatment
        self.hierarchy_file = get_hierarchy_file(self.inputs_case, self.ReEDS_resolution)

        # Store the samples for each switch (a single sw may have multiple files that is
        # why we refer to the switch by its adjusted name)
        self.samples = {sw_name: [] for sw_name in self.sample_group['Sample_ID']}

        # Instantiate WeightCalculator.
        self.weight_calc = WeightCalculator(sample_group, aux_files, n_samples)

    @staticmethod
    def prepare_ref_data(
        dist_files: list,
        file_name: str,
        sw_name: str | list,
        aux_files,
    ) -> Tuple[list, list, dict]:
        """
        This function prepares the reference dataframes for the Monte Carlo sampling.
        For some files like those related to supply curves we need to expand/modify
        the reference files to include additional rows/columns. 

        Args:
            dist_files (list of pd.DataFrame): List of reference dataframes to be modified.
            file_name (str): name given by reeds to the files in dist_files.
            sw_name (str or list): Name of the switch being sampled. For the special case
                of float switches, this will be a list of switch names.

        Returns:
            list of pd.DataFrame: List of modified reference dataframes.
            list of str: List of columns that can be directly multiplied by the weights.
            dict: Dictionary with the number of decimal places for columns we will modify
        """
        ### ===========================================================================
        ### --- Expand dist_files if necessary ---
        ### ===========================================================================
        # For each file map the columns we need to verify in the df expansion
        # (e.g For the supply curves we will make sure that all files are
        # ajusted to contain all regions and sc_point_gid combinations)
        map_files2ref_columns = {
            **{file: ["region", "sc_point_gid"] for file in MCSConstants.SUPPLY_CURVE_FILES},
            **{file: ["region", "year", "sc_point_gid"] for file in MCSConstants.EXOG_CAP_FILES},
            **{file: ["region", "year"] for file in MCSConstants.PRESCRIBED_BUILDS_FILES},
        }

        if file_name in map_files2ref_columns:
            ref_columns = map_files2ref_columns[file_name]

            # Get all unique combination for the reference columns
            unique_reg_gid_point = pd.concat(
                [df[ref_columns] for df in dist_files],
                ignore_index=True
            ).drop_duplicates().reset_index(drop=True)

            # Modify dfs in the dist_files list adding missing ref_columns combinations
            # and initializing the modifiable rows with 0
            for i, df in enumerate(dist_files):
                dist_files[i] = unique_reg_gid_point.merge(
                    df.reset_index(drop=True),
                    on=ref_columns,
                    how="left",
                ).fillna(0).sort_values(by=ref_columns).reset_index(drop=True)

        ### ===========================================================================
        ### --- Get a list of the columns we are allowed to apply weights directly ---
        ### ===========================================================================
        # Get the base set of general (modifiable) columns from dist_files[0]
        general_mult_columns = {
            col for col in dist_files[0].keys() if col not in MCSConstants.FIXED_COLUMN_NAMES
        }

        # Ensure all dist_files have the same set of general columns
        if file_name not in MCSConstants.RECF_FILES:
            for i, df in enumerate(dist_files[1:], start=1):
                current_cols = {col for col in df.keys() if col not in MCSConstants.FIXED_COLUMN_NAMES}
                if current_cols != general_mult_columns:
                    error_msg = (
                        f"Column mismatch between dist_files[0] and dist_files[i]:\n"
                        "This usually happens when you run MCS on a file whose columns "
                        "vary by switch assignment (e.g. RECF_FILES).\n If you really need to support "
                        f"'{file_name}' here, add the necessary handling in prepare_ref_data()."
                    )
                    raise ValueError(error_msg)

        exceptions_mult_col = {
            **{file: ["class"] + list(general_mult_columns) for file in MCSConstants.SUPPLY_CURVE_FILES},
            **{file: ["capacity"] for file in MCSConstants.EXOG_CAP_FILES},
            **{file: ["capacity"] for file in MCSConstants.PRESCRIBED_BUILDS_FILES},
            **{file: [] for file in MCSConstants.RECF_FILES}, # treated separately
        }
        modifiable_columns = exceptions_mult_col.get(file_name, list(general_mult_columns))

        ### ===========================================================================
        ### --- Map for the number of decimals in each column we will change
        ### ===========================================================================
        if file_name in ["switches.csv"]:
            n_decimals = max_decimal_places(dist_files[0].loc[sw_name,1])
        else:
            n_decimals_list = [
                max_decimal_places(df[modifiable_columns]) for df in dist_files
            ]

            # Take the max decimal count per column across all files, capped at 6
            n_decimals = {
                col: min(max(d[col] for d in n_decimals_list), 6)
                for col in n_decimals_list[0]
            }

        return dist_files, modifiable_columns, n_decimals

    def load_ref_files(self, sample_idx: int) -> List[pd.DataFrame]:
        """
        Load the reference files associated with the sample.

        Args:
            sample_idx (int): Index of the Sample_ID in sample_group.
            Some switches have multiple files associated with them that is why we
            track samples using Sample_ID in the sample_group.

        Returns:
            List[pd.DataFrame]: List of DataFrames with the switch files.
        """

        sw_name = self.sample_group['switch_names'][sample_idx]

        # Create a list of dataframes with the data related to the switch
        dist_files = []

        for sw_assignment in self.sample_group['sw_assignments'][sample_idx]:

            sw_runfiles_csv = self.sample_group['runfiles_csv'][sample_idx].copy(deep=True)
            sw_runfiles_csv['sw_assignment'] = sw_assignment

            if not pd.isna(sw_runfiles_csv['filepath']):
                sw_runfiles_csv['full_filepath'] = os.path.join(
                    self.reeds_path,
                    sw_runfiles_csv['filepath'].replace(f'{{{sw_name}}}', sw_assignment),
                )

            df = read_csv_h5_file(sw_runfiles_csv, self.aux_files, self.reeds_path, self.inputs_case)
            dist_files.append(df)

        return dist_files

    # ----------------------- Weight Application Helpers -----------------------
    def _adjust_supply_curve_sample(self, samples_sw: list, sw_name: str, sample_idx: int) -> list:
        """
        Adjust samples for supply curve files:
          - Convert the 'class' column to integers.
          - Normalize the weights map.
          - Remove rows with no capacity.

        Args:
            samples_sw (list of pd.DataFrame): List of samples for the supply curve files.
            sw_name (str): Name of the switch being sampled.
            sample_idx (int): Index of the Sample_ID in sample_group.

        Returns:
            list of pd.DataFrame: List of adjusted samples for the supply curve files.
        """

        for s in range(self.n_samples):
            # Convert class to integer
            samples_sw[s]["class"] = samples_sw[s]["class"].astype(int)

        # Update the recf weights map (weight_calc.recf_weights_map)
        self.weight_calc.normalize_recf_weights_map(samples_sw, sw_name)

        # Remove samples with no capacity. 
        # Need to do this after normalizing the recf weights
        samples_sw = [df[df["capacity"] > 0].copy() for df in samples_sw]
        
        return samples_sw

    def _adjust_exog_cap_samples(self, samples_sw: list, file_name: str) -> list:
        """
        Adjust samples for exogenous capacity files:
          - Remove rows with no capacity.
          - Adjust the tech classes based on available classes per sc_point_gid.

        Args:
            samples_sw (list of pd.DataFrame): List of samples for the exogenous capacity files.
            file_name (str): Name of the file being sampled.
        """
        # Remove samples with no capacity
        samples_sw = [df[df["capacity"] > 0].copy() for df in samples_sw]

        tech_mapping = {
            "exog_cap_upv.csv": ("upv", "supplycurve_upv.csv"),
            "exog_cap_wind-ons.csv": ("wind-ons", "supplycurve_wind-ons.csv"),
        }
        tech_name, Sample_ID = tech_mapping[file_name]

        for s in range(self.n_samples):
            # Get the class available for each sc_point_gid
            class_sc_point_map = self.samples[Sample_ID][s][["sc_point_gid", "class"]]
            class_sc_point_map = class_sc_point_map.set_index("sc_point_gid").to_dict()["class"]

            # Remove any rows from samples_sw[s] that cannot be mapped
            # These are cases with zero supply in the region
            valid_sc_point_gids = samples_sw[s]["sc_point_gid"].isin(class_sc_point_map.keys())
            samples_sw[s] = samples_sw[s][valid_sc_point_gids].copy()

            # Create a new tech name for each sc_point_gid
            new_tech_name = [tech_name + "_" + str(int(c)) for c in 
                samples_sw[s]["sc_point_gid"].map(class_sc_point_map).values]

            samples_sw[s]["*tech"] = new_tech_name

        return samples_sw

    def _apply_weights_general(
        self,
        dist_files: list,
        modifiable_columns: list,
        n_decimals: dict|int,
        dict_df_weights: dict,
        sample_idx: int
    ):
        """
        Apply the distribution weights to the reference files. 
        Applicable to all cases but recf files and switches.csv.

        Args:
            dist_files (List[pd.DataFrame]): List of input DataFrames for sampling.
            modifiable_columns (List[str]): List of columns that can be directly multiplied by the weights.
            n_decimals (Dict[str, int]): Dictionary with the number of decimal places for each column.
            dict_df_weights (Dict[Tuple[int, int], pd.DataFrame]): Dictionary with the weights for each reference file and sample.
            sample_idx (int): Index of the Sample_ID in sample_group.

        Update:
            self.samples (Dict[str, List[pd.DataFrame]]): Dictionary with the samples for each switch/file_name.
        """

        Sample_ID = self.sample_group['Sample_ID'][sample_idx]
        sw_name = self.sample_group['switch_names'][sample_idx]
        file_name = self.sample_group["runfiles_csv"][sample_idx]["filename"]

        # Initialize samples with zero values
        samples_sw = [dist_files[0].copy() for n in range(self.n_samples)]   

        for s in range(self.n_samples):
            # Initialize with zeros
            samples_sw[s][modifiable_columns] = 0  

            for f, df in enumerate(dist_files):
                samples_sw[s][modifiable_columns] += df[modifiable_columns] * dict_df_weights[s, f][modifiable_columns] 

            for col in modifiable_columns:
                samples_sw[s][col] = samples_sw[s][col].round(n_decimals[col]+1)

        if file_name in MCSConstants.SUPPLY_CURVE_FILES:
            adjusted_samples = self._adjust_supply_curve_sample(samples_sw, sw_name, sample_idx)

        elif file_name in MCSConstants.EXOG_CAP_FILES:
            adjusted_samples = self._adjust_exog_cap_samples(samples_sw, file_name)

        elif file_name in MCSConstants.PRESCRIBED_BUILDS_FILES:
            # Remove samples with no capacity
            adjusted_samples = [df[df["capacity"] > 0].copy() for df in samples_sw]

        else:
            # For all other files we can directly apply the weights
            adjusted_samples = samples_sw

        # Save the adjusted samples.
        self.samples[Sample_ID] = adjusted_samples

    def _apply_weights_recf(
        self,
        dist_files: list,
        sample_idx: int
    ):
        """
        Apply the distribution weights to the recf files.
        This file gets compleatly overwriten so need to be treated separately

        Args:
            dist_files (List[pd.DataFrame]): List of input DataFrames for sampling.
            sample_idx (int): Index of the Sample_ID in sample_group.

        Update:
            self.samples (Dict[str, List[pd.DataFrame]]): Dictionary with the samples for each switch/file_name.
        """

        Sample_ID = self.sample_group['Sample_ID'][sample_idx]
        sw_name = self.sample_group['switch_names'][sample_idx]

        # For the recf files we need to apply the weights to the old class|region combinations
        weights = self.weight_calc.recf_weights_map[sw_name]
        # Index is the same for all files (time)
        indexes = dist_files[0].index 

        samples_sw = []  

        for s in range(self.n_samples):
            sample_sw = defaultdict(int)

            for f, df in enumerate(dist_files):
                # Get the old and new class|region combinations from weights[(s, f)]
                for (new_c_r, old_c_r) in weights[(s, f)].index:
                    sample_sw[new_c_r] += df[old_c_r] * weights[(s, f)].loc[(new_c_r,old_c_r)].values[0]

            # Round numbers to 9 decimal places and allow a maxium values of 1
            for new_c_r in sample_sw.keys():
                sample_sw[new_c_r] = sample_sw[new_c_r].round(9).clip(0,1)
            
            samples_sw.append(pd.DataFrame(sample_sw, index=indexes))

        self.samples[Sample_ID] = samples_sw

    def _apply_weights_switches_csv(
        self,
        dist_files: list,
        n_decimals: dict,
        dict_df_weights: dict,
        sample_idx: int,
    ):
        """
        Apply the distribution weights to the switches.csv file.

        Args:
            dist_files (List[pd.DataFrame]): List of input DataFrames for sampling.
            n_decimals (Dict[str, int]): Dictionary with the number of decimal places for each column.
            dict_df_weights (Dict[Tuple[int, int], pd.DataFrame]): Dictionary with the weights for each reference file and sample.
            sample_idx (int): Index of the Sample_ID in sample_group.

        Update:
            self.samples (Dict[str, List[pd.DataFrame]]): Dictionary with the samples for each switch/file_name.
        """
        # Switches are saved only for the rows changed because this allow 
        # multiple json objects changing different switches using different distributions

        sw_name = self.sample_group['switch_names'][sample_idx]

        samples_sw = [None for n in range(self.n_samples)]
        sw_assignments = self.sample_group['sw_assignments'][sample_idx]

        for s in range(self.n_samples):
            for assingment_idx, sw_assignment in enumerate(sw_assignments):

                # The switch assignments case can be a int, a float or a string
                # If it is a str or int it must be used in a discrete distribution
                if isinstance(sw_assignment, (str, int)):
                    # Check if we have a discrete distribution
                    if self.distribution != "discrete":
                        raise ValueError(
                            f"You specified a str/int assignment for switch '{sw_name}', "
                            "but the distribution is not set to 'discrete'. "
                            "This file is likely hard-coded in `copy_files.py`.\n\n"
                            "To fix this, you can try to:\n"
                            "  - Change the distribution to 'discrete'\n"
                            "  - Use a float assignment instead, or\n"
                            "  - Add support for this switch's files\n\n"
                            "A good place to start is the `read_exception_file()` function."
                        )

                    if isinstance(sw_assignment, str) and dict_df_weights[s, assingment_idx]:
                        # dict_df_weights[s,f] is a one hot encoding of the sw_assignment options
                        samples_sw[s] = sw_assignment

                    elif isinstance(sw_assignment, int) and dict_df_weights[s, assingment_idx]:
                        # dict_df_weights[s,f] is a one hot encoding of the sw_assignment options
                        samples_sw[s] = str(sw_assignment)

                elif isinstance(sw_assignment, float):
                    if self.distribution == "discrete":
                        # dict_df_weights[s,f] is a one hot encoding of the sw_assignment options
                        samples_sw[s] = str(sw_assignment)

                    elif self.distribution in MCSConstants.MULTIPLICATIVE_DISTRIBUTIONS:
                        # We have a validation process that makes sure that we only have one file
                        samples_sw[s] = (
                            str(np.round(sw_assignment * dict_df_weights[s, 0], n_decimals+1))
                        )
                    else:
                        raise ValueError(
                            f"Float assignments can only be used with a discrete or multiplicative distribution. "
                            f"Check the distribution for switch '{sw_name}'."
                        )

        self.samples[sw_name] = samples_sw

    def record_group_weights(self, log_folder: str) -> None:
        """
        Record the weights for each distribution group in 
        lstfiles/mcs_group_weights.csv. Appends to the file if it exists.

        Args:
            mcs_sampler (MCS): The MCS object containing the distribution groups and weights.
            log_folder (str): Directory where the weights file will be stored.
        """
        os.makedirs(log_folder, exist_ok=True)
        save_path = os.path.join(log_folder, 'mcs_group_weights.csv')
        r_weights = self.weight_calc.r_weights
        group_name = self.sample_group["name"]
        assignments_list = self.sample_group["assignments_list"]

        # Get shape of any region’s weight array
        any_region = next(iter(r_weights))
        n_samples, n_assignments = r_weights[any_region].shape

        # Build column names
        columns = (
            ['group_name', 'switch_name', 'sw_assignment', 'r'] +
            [f"Weight Sample {i}" for i in range(1, n_samples + 1)]
        )

        data = []

        for switch_idx, switch_dict in enumerate(assignments_list):
            sw_name, sw_assignment = next(iter(switch_dict.items()))
            for r in r_weights.keys():
                for assignment_idx, assignment_value in enumerate(sw_assignment):
                    weights = list(r_weights[r][:, assignment_idx])  # column for this switch
                    row = [group_name, sw_name, assignment_value, r] + weights
                    data.append(row)

        weight_record_df = pd.DataFrame(data, columns=columns)

        # Append if file exists, else write with header
        if os.path.exists(save_path):
            weight_record_df.to_csv(save_path, mode='a', index=False, header=False)
        else:
            weight_record_df.to_csv(save_path, mode='w', index=False, header=True)
    # ----------------------- End of Weight Application Helpers -----------------------

    def get_samples(self, aux_files):
        """
        Generates Monte Carlo samples for each switch and applies the appropriate weight assignment.

        Returns:
            Dict[str, List[pd.DataFrame]]: Dictionary with the samples for each switch/file_name.
        """
        # Iterate over each switch file and apply the appropriate weight assignment method
        for sample_idx, sample_ID in enumerate(self.sample_group['Sample_ID']):

            sw_name = self.sample_group['switch_names'][sample_idx]
            file_name = self.sample_group["file_names"][sample_idx]
            dist_files = self.load_ref_files(sample_idx)

            #In some small cases all dist_files are empty
            if not all([len(df) for df in dist_files]):
                self.samples[sample_ID] = [dist_files[0] for s in range(self.n_samples)]
                continue

            # Extend/modify dist_files if necessary (e.g supply curve related data)
            dist_files, modifiable_columns, n_decimals = self.prepare_ref_data(
                dist_files, file_name, sw_name, aux_files,
            )

            # Get weights we will apply to the reference files
            dict_df_weights = self.weight_calc.get_df_weights(dist_files, modifiable_columns, sw_name, file_name)

            # Dispatch weight application based on file type.
            if file_name == "switches.csv":
                self._apply_weights_switches_csv(dist_files, n_decimals, dict_df_weights, sample_idx)
            elif file_name in MCSConstants.RECF_FILES:
                self._apply_weights_recf(dist_files, sample_idx)
            else:
                self._apply_weights_general(dist_files, modifiable_columns, n_decimals, dict_df_weights, sample_idx)

        return self.samples


#%% ===========================================================================
### --- OUTPUT FUNCTIONS ---
### ===========================================================================
def write_samples(
    sample_group: pd.Series,
    samples_dict: dict,
    aux_files: dict,
    run_ReEDS: bool = True,
):
    """
    Write the samples to the appropriate locations

    Args:
        sample_group (pd.Series): Row of the input file with the sampling instructions.
        samples_dict (dict): Dictionary with the samples for each switch/file_name.
        aux_files (dict): Dictionary with the auxiliary files needed for sampling.
        run_ReEDS (bool): If True, the script is being used to run ReEDS. 
            If False, the script is being used to test the samples before running ReEDS.
    """

    inputs_case = sample_group['inputs_case']

    for sample_idx, sample_ID in enumerate(samples_dict.keys()):
        samples = samples_dict[sample_ID]
        sw_name = sample_group['switch_names'][sample_idx]
        save_path_structure = sample_group['save_paths'][sample_idx]  # Where the samples will be copied to
        file_name = sample_group["file_names"][sample_idx]

        for n, sample in enumerate(samples):
            save_path = save_path_structure.replace('{sample_n}', str(n))
            folder_path = os.path.dirname(save_path)  # Folder path without the file name
            file_termination = os.path.splitext(save_path)[-1]  # File termination (.csv, .h5, etc.)

            # For run_ReEDS==False, create folder if it does not exist
            if (not run_ReEDS):
                os.makedirs(folder_path, exist_ok=True)

            # If we have a region-indexed file
            if file_name in aux_files['region_files']['filename'].values:
                # Get destination directory instead of save_path
                dir_dst = os.path.dirname(save_path)
                # Get the row of the region-indexed file
                region_files_row = aux_files['region_files'].query('filename == @file_name').iloc[0]
                copy_files.write_region_indexed_file(sample, dir_dst, aux_files['source_deflator_map'],
                                                        aux_files['sw'], region_files_row,
                                                        aux_files['regions_and_agglevel'],
                                                        aux_files['agglevel_variables'])

            elif file_termination == '.csv':
                # Not a region-indexed file but it is a CSV file
                if file_name != 'switches.csv':
                    sample.to_csv(save_path, index=False)
                else:
                    # Read the original switches.csv file
                    original_switches = pd.read_csv(save_path, header=None, index_col=0)
                    # Update the original switches.csv file with the new samples
                    original_switches.loc[sw_name] = sample
                    original_switches.to_csv(save_path, header=False)
                    if run_ReEDS:
                        # Create gswitches.csv and .txt files 
                        gswitches_path = reeds.io.write_gswitches(original_switches, inputs_case)
                        copy_files.scalar_csv_to_txt(gswitches_path)
                        
                  
            if run_ReEDS:  # Only print if running ReEDS optimization
                reduced_path = os.sep.join(save_path.strip(os.sep).split(os.sep)[-3:])
                print(f"...Sample related to switch {sw_name} was copied to {reduced_path}")


#%% ===========================================================================
### --- MAIN PROCEDURE ---
### ===========================================================================
def main(
    reeds_path: str,
    inputs_case: str,
    n_samples: int = 1,
    seed: int = 0,
    run_ReEDS: bool = True,
):
    """
    Create samples for the Monte Carlo Simulation (MCS).

    Args:
        reeds_path (str): Path to the ReEDS directory.
        inputs_case (str): Path to the inputs_case directory.
        n_samples (int): Number of samples to generate.
        seed (int): Seed for the random number generator.
        run_ReEDS (bool): If True, the script is being used to run ReEDS. 
            If False, the script is being used to test the samples before running ReEDS.

    Notes:
        If run_ReEDS=False inputs_case only needs to be a folder containing switches.csv so 
        we can perform any spatial filtering needed to get the samples
    """

    if run_ReEDS:
        # Set random seed as the (MCS run number + seed) to allow reproducibility without having
        # the same sample for each MCS-ReEDS call
        runs_folder_name = os.path.basename(os.path.dirname(inputs_case.rstrip(os.path.sep)))
        mcs_run_number = int((runs_folder_name.split('_')[-1]).replace('MC', ''))
        seed += mcs_run_number
        np.random.seed(seed)
    else:
        # The script is being used to test the samples before running ReEDS
        np.random.seed(seed)

    # Obtain instructions to sample the distributions for each switch
    df_input_dist_instructions, aux_files = get_dist_instructions(reeds_path, inputs_case, run_ReEDS=run_ReEDS)

    print('Sampling...')
    for _, sample_group in df_input_dist_instructions.iterrows():
        dist_switches = sample_group['switch_names']
        unique_switches = set(dist_switches)

        print(f"Sampling for switch(es): {unique_switches}")
        # Create Samples
        mcs_sampler = MCS_Sampler(sample_group, aux_files, n_samples)
        samples_dict = mcs_sampler.get_samples(aux_files)

        # Record the weights of each sample group
        mcs_sampler.record_group_weights(
            os.path.join(os.path.dirname(inputs_case), 'lstfiles')
        )
        # Write Samples
        write_samples(sample_group, samples_dict, aux_files, run_ReEDS=run_ReEDS)


if __name__ == '__main__' and not hasattr(sys, 'ps1'):
    parser = argparse.ArgumentParser(description='Copy files needed for this run')
    parser.add_argument('reeds_path', help='ReEDS directory')
    parser.add_argument('inputs_case', help='Output directory')

    args = parser.parse_args()
    reeds_path = os.path.abspath(args.reeds_path)
    inputs_case = os.path.abspath(args.inputs_case)

    # ---- Settings for testing ----
    # reeds_path = reeds.io.reeds_path
    # inputs_case = os.path.join(reeds_path,'runs','v20250825_revM2_MonteCarlo_MC1','inputs_case')
    # n_samples = 1
    # seed = 0
    # run_ReEDS = True

    # Set up logger
    tic = datetime.datetime.now()
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(os.path.dirname(inputs_case), 'gamslog.txt'),
    )

    # Read switches and check if MCS_runs is enabled.
    sw = reeds.io.get_switches(inputs_case)
    MCS_Runs = int(sw.get('MCS_runs', 0))
    if MCS_Runs >= 1:
        print('Starting mcs_sampler.py')
        main(reeds_path, inputs_case, n_samples=1)
    else:
        print('MCS_runs switch is set to 0 or not found. No Monte Carlo sampling will be performed')

    # Final log/timing update.
    reeds.log.toc(
        tic=tic, 
        year=0, 
        process='input_processing/mcs_sampler.py',
        path=os.path.join(os.path.dirname(inputs_case))
    )
