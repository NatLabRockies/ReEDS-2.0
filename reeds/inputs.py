### Imports
import os
import re
import sys
import numpy as np
import pandas as pd
import sklearn.cluster
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import reeds
from input_processing import mcs_sampler

### Functions
def parse_regions(case_or_string, case=None):
    """
    Inputs
    ------
    case_or_string: path to a ReEDS case or a parseable string in the format of GSw_Region
    case: path to a ReEDS case. Only used if case_or_string is not a ReEDS case. Should be
        used if you want to select a subset of model zones from a ReEDS case that used
        region aggregation.

    Returns
    -------
    np.array of zone names
        - If case_or_string is a case, return the regions modeled in the run
        - If case_or_string is a parseable string in the format of GSw_Region, return
          the regions that obey that string

    Examples
    --------
    parse_regions('transreg/NYISO') -> ['p127', 'p128']
    parse_regions('st/PA') -> ['p115', 'p119', 'p120', 'p122']
    parse_regions('st/PA', 'path/to/case/using/region/aggregation') -> ['p115', 'p120', 'z122']
    """
    if os.path.exists(case_or_string):
        sw = reeds.io.get_switches(case_or_string)
        hierarchy = reeds.io.get_hierarchy(case_or_string)
        GSw_Region = sw['GSw_Region']
    ## Provide case argument if using aggregated regions
    elif os.path.exists(str(case)):
        hierarchy = reeds.io.get_hierarchy(case)
        GSw_Region = case_or_string
    else:
        hierarchy = reeds.io.get_hierarchy()
        GSw_Region = case_or_string

    if '/' in GSw_Region:
        level, regions = GSw_Region.split('/')
        regions = regions.split('.')
        if level in ['r', 'ba']:
            rs = [r for r in hierarchy.index if r in regions]
        else:
            rs = hierarchy.loc[hierarchy[level].isin(regions)].index
    else:
        modeled_regions = pd.read_csv(
            os.path.join(reeds.io.reeds_path, 'inputs', 'userinput', 'modeled_regions.csv')
        )
        modeled_regions.columns = modeled_regions.columns.str.lower()
        rs = list(
            modeled_regions[
                ~modeled_regions[GSw_Region.lower()].isna()
            ]['r'].unique()
        )
    return rs


def parse_yearset(yearset:str) -> list:
    """
    Parses a ReEDS-formatted yearset and returns a list of integer years.

    Args:
        yearset (str): _-delimited list of individual years OR bash-formatted year ranges

    Returns:
        list of integer years (sorted)
    
    Examples:
        '2010' -> [2010]
        '2010_2015_2020' -> [2010, 2015, 2020]
        '2010..2020..5' -> [2010, 2015, 2020]
        '2010_2015_2020..2050..3' -> [
            2010, 2015,
            2020, 2023, 2026, 2029, 2032, 2035, 2038, 2041, 2044, 2047, 2050
        ]
        '2010..2035..5_2040..2100..10' -> [
            2010, 2015, 2020, 2025, 2030, 2035,
            2040, 2050, 2060, 2070, 2080, 2090, 2100
        ]
    """
    pattern = r'^2\d{3}(\.\.2\d{3}(\.\.\d+)?)?(_2\d{3}(\.\.2\d{3}(\.\.\d+)?)?)*$'
    helper = (
        "For formatting notes and examples, run the following commands:\n"
        "$ python\n"
        ">>> import reeds\n"
        ">>> help(reeds.inputs.parse_yearset)"
    )
    if not re.match(pattern, yearset):
        err = f"Invalid yearset ({yearset}); must match {pattern}. {helper}"
        raise ValueError(err)
    yearstrings = yearset.split('_')
    years = []
    for y in yearstrings:
        subyears = [int(i) for i in y.split('..')]
        if len(subyears) == 1:
            years.append(subyears[0])
        elif len(subyears) == 2:
            years.extend(range(subyears[0], subyears[1]+1))
        elif len(subyears) == 3:
            years.extend(range(subyears[0], subyears[1]+1, subyears[2]))
        else:
            err = f"Invalid subyears ({subyears}) in yearset {yearset}. {helper}"
            raise ValueError(err)
    out = sorted(set(years))
    return out


def add_intermediate_switches(dfcases:pd.DataFrame) -> pd.DataFrame:
    """Determine some switch settings from other switches"""
    ignore_columns = ['Choices', 'Default Value']
    cases = [i for i in dfcases if i not in ignore_columns]
    new_switches = {}
    for case in cases:
        sw = dfcases[case]
        new_switches[case] = {}
        new_switches[case]['GSw_itlgrpConstraint'] = str(int(
            sw['GSw_RegionResolution'] in ['county', 'mixed']
        ))
        new_switches[case]['GSw_OffshoreFiles'] = (
            'meshed' if int(sw['GSw_OffshoreZones']) else 'radial'
        )
        ## Load site region level (GSw_LoadSiteReg) is embedded in GSw_LoadSiteTrajectory
        new_switches[case]['GSw_LoadSiteReg'] = sw['GSw_LoadSiteTrajectory'].split('_')[0]
        ## Get numbins from the max of individual technology bins
        new_switches[case]['numbins'] = str(max(
            int(sw['numbins_windons']),
            int(sw['numbins_windofs']),
            int(sw['numbins_upv']),
            15,
        ))
    dfcases_out = pd.concat([dfcases, pd.DataFrame(new_switches)])
    return dfcases_out


def parse_cases(
    cases_filename:str='cases_test.csv',
    single:str='',
    skip_checks:bool=False,
) -> pd.DataFrame:
    """
    Read a ReEDS cases file, look up empty switch values from "Default Value" or cases.csv,
    and return a dataframe of all switches and values.

    Args:
        cases_filename (str): 'cases_{something}.csv' or 'cases.csv'
        single (str): If not '', specifies a single column to keep from cases_filename
        skip_checks (bool): Skip case validation (not recommended)

    Returns:
        pd.DataFrame
    """
    dfcases = pd.read_csv(
        os.path.join(reeds.io.reeds_path, 'cases.csv'), dtype=object, index_col=0)

    # If we have a case suffix, use cases_[suffix].csv for cases.
    if cases_filename != 'cases.csv':
        dfcases = dfcases[['Choices', 'Default Value']]
        dfcases_suf = pd.read_csv(
            os.path.join(reeds.io.reeds_path, cases_filename), dtype=object, index_col=0)
        # Replace periods and spaces in case names with _
        dfcases_suf.columns = [
            c.replace(' ','_').replace('.','_') if c != 'Default Value' else c
            for c in dfcases_suf.columns]

        # Check to make sure user-specified cases file has up-to-date switches
        missing_switches = [s for s in dfcases_suf.index if s not in dfcases.index]
        if len(missing_switches):
            error = (
                "The following switches are in {} but have changed names or are no longer "
                "supported by ReEDS:\n\n{} \n\nPlease update your cases file; "
                "for the full list of available switches see cases.csv. "
                "Note that switch names are case-sensitive."
            ).format(cases_filename, '\n'.join(missing_switches))
            raise ValueError(error)

        # First use 'Default Value' from cases_[suffix].csv to fill missing switches
        # Later, we will also use 'Default Value' from cases.csv to fill any remaining holes.
        if 'Default Value' in dfcases_suf.columns:
            case_i = dfcases_suf.columns.get_loc('Default Value') + 1
            casenames = dfcases_suf.columns[case_i:].tolist()
            for case in casenames:
                dfcases_suf[case] = dfcases_suf[case].fillna(dfcases_suf['Default Value'])
        dfcases_suf.drop(['Choices','Default Value'], axis='columns',inplace=True, errors='ignore')
        dfcases = dfcases.join(dfcases_suf, how='outer')

    casenames = [c for c in dfcases.columns if c not in ['Description','Default Value','Choices']]
    # Get the list of switch choices
    choices = dfcases.Choices.copy()

    for case in casenames:
        # Fill any missing switches with the defaults in cases.csv
        dfcases[case] = dfcases[case].fillna(dfcases['Default Value'])

        # If --single/-s was passed, only keep those cases (regardless of ignore)
        # otherwise, drop any case marked ignore
        if single:
            if case not in single.split(','):
                continue
        else:
            if int(dfcases.loc['ignore', case]) == 1:
                continue

        # Check to make sure the switch setting is valid
        for i, val in dfcases[case].items():
            if skip_checks:
                continue
            # check that the switch isn't duplicated
            if isinstance(choices[i], pd.Series) and len(choices[i]) > 1:
                error = (
                        f'Duplicate entries for "{i}", delete one and restart.'
                        )
                raise ValueError(error)
            ### Split choices by either '; ' or ','
            if choices[i] in ['N/A',None,np.nan]:
                pass
            elif choices[i].lower() in ['int','integer']:
                try:
                    int(val)
                except ValueError:
                    error = (
                        f'Invalid entry for "{i}" for case "{case}".\n'
                        f'Entered "{val}" but must be an integer.'
                    )
                    raise ValueError(error)
            elif choices[i].lower() in ['float','numeric','number','num']:
                try:
                    float(val)
                except ValueError:
                    error = (
                        f'Invalid entry for "{i}" for case "{case}".\n'
                        f'Entered "{val}" but must be a float (number).'
                    )
                    raise ValueError(error)
            else:
                i_choices = [
                    str(j).strip() for j in
                    np.ravel([i.split(',') for i in choices[i].split(';')]).tolist()
                ]
                matches = [re.match(choice, str(val)) for choice in i_choices]
                if not any(matches): 
                    error = (
                        f'Invalid entry for "{i}" for case "{case}".\n'
                        f'Entered "{val}" but must match one of the following:\n> '
                        + '\n> '.join(i_choices)
                        + f'\nOr, if "{val}" is intended, it must be added to the '
                        '"Choices" column in cases.csv.'
                    )
                    raise ValueError(error)

        # Check GSw_Region switch and ask user to correct if commas are used instead of
        # periods to list multiple regions
        if ',' in (dfcases[case].loc['GSw_Region']) :
            print("Please change the delimeter in the GSw_Region switch from ',' to '.'")
            quit()

    # If doing a Monte Carlo run, modify dfcases by adding new columns
    # for each scenario run. Also validate the distribution file.
    warned_about_cluster_alg = False
    if 'MCS_runs' in dfcases.index:
        for c in dfcases.columns:
            if (
                c not in ['Description','Default Value','Choices']
                and (int(dfcases.loc['MCS_runs',c]) > 0)
                and (not int(dfcases.loc['ignore',c]))
            ):
                # Warn user if the hourly clustering algorithm is not fixed for Monte Carlo runs
                if (
                    not dfcases.at['GSw_HourlyClusterAlgorithm', c].startswith('user')
                    and not warned_about_cluster_alg
                ):
                    print(f"\n[Warning] Case Column: '{c}'")
                    print(
                        "You are attempting to run a Monte Carlo simulation with "
                        "`GSw_HourlyClusterAlgorithm` set to a value other than 'user'.\n"
                        "This may result in inconsistent representative days across MCS runs.\n\n"
                        "To ensure consistency, we strongly recommend setting "
                        "`GSw_HourlyClusterAlgorithm = user` in your switch configuration.\n"
                        "Do you want to proceed with the current setup?"
                    )
                    user_input = input("Type 'yes' to proceed, or 'no' to exit: ").strip().lower()
                    if user_input not in ['yes', 'y']:
                        print("\nPlease update the `GSw_HourlyClusterAlgorithm` switch and restart.")
                        quit()
                    warned_about_cluster_alg = True
                    print()

                # Validate the distribution file
                sw = dfcases[c].fillna(dfcases['Default Value'])
                mcs_dist_path = os.path.join(
                    reeds.io.reeds_path, 'inputs', 'userinput',
                    'mcs_distributions_{}.yaml'.format(sw.MCS_dist)
                )
                mcs_sampler.general_mcs_dist_validation(reeds.io.reeds_path, mcs_dist_path, sw)

                # c (column) is a case with monte carlo runs.
                # replicate this column N (NumMonteCarloRuns) times
                NumMonteCarloRuns = int(dfcases.loc['MCS_runs',c])
                NewColumnNames = [
                    f"{c}_MC{i:0>4}"
                    for i in range(1, NumMonteCarloRuns + 1)
                ]

                # Each new column is a copy of the original column with name c_{MC1,MC2,...}
                dfcases_MC = pd.DataFrame(
                    data=np.array([dfcases[c].values]*NumMonteCarloRuns).T,
                    index=dfcases.index,
                    columns=NewColumnNames,
                )
                dfcases = pd.concat([dfcases, dfcases_MC], axis=1)
                # drop the original column
                dfcases.drop(c, axis=1, inplace=True)

    ## Add switches determined from other switches and remove unnecessary columns
    dfcases_out = (
        add_intermediate_switches(dfcases)
        .drop(columns=['Choices', 'Description', 'Default Value'], errors='ignore')
    )

    return dfcases_out


def get_bin(
    df_in,
    bin_num,
    bin_method='equal_cap_cut',
    bin_col='capacity_factor_ac',
    bin_out_col='bin',
    weight_col='capacity',
):
    """
    bin supply curve points based on a specified bin column. Used in hourlize to create 'bins'
    for the resource classes (typically using capacity factor) and then used by
    writesupplycurves.py to create bins based on supply curve cost.
    """
    df = df_in.copy()
    ser = df[bin_col]
    # If we have less than or equal unique points than bin_num,
    # we simply group the points with the same values.
    if ser.unique().size <= bin_num:
        bin_ser = ser.rank(method='dense')
        df[bin_out_col] = bin_ser.values
    elif bin_method == 'kmeans':
        nparr = ser.to_numpy().reshape(-1,1)
        weights = df[weight_col].to_numpy()
        kmeans = (
            sklearn.cluster.KMeans(n_clusters=bin_num, random_state=0, n_init=10)
            .fit(nparr, sample_weight=weights)
        )
        bin_ser = pd.Series(kmeans.labels_)
        # but kmeans doesn't necessarily label in order of increasing value because it is 2D,
        # so we replace labels with cluster centers, then rank
        kmeans_map = pd.Series(kmeans.cluster_centers_.flatten())
        bin_ser = bin_ser.map(kmeans_map).rank(method='dense')
        df[bin_out_col] = bin_ser.values
    elif bin_method == 'equal_cap_man':
        # using a manual method instead of pd.cut because i want the first bin to contain the
        # first sc point regardless, even if its weight_col value is more than the capacity
        # of the bin, and likewise for other bins, so i don't skip any bins.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        cumcaps = df[weight_col].cumsum().tolist()
        totcap = df[weight_col].sum()
        vals = df[bin_col].tolist()
        bins = []
        curbin = 1
        for i, _v in enumerate(vals):
            bins.append(curbin)
            if cumcaps[i] >= totcap*curbin/bin_num:
                curbin += 1
        df[bin_out_col] = bins
        # we need the same index ordering for apply to work
        df = df.reindex(index=orig_index)
    elif bin_method == 'equal_cap_cut':
        # Use pandas.cut with cumulative capacity in each class. This will assume equal capacity bins
        # to bin the data.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        df['cum_cap'] = df[weight_col].cumsum()
        bin_ser = pd.cut(df['cum_cap'], bin_num, labels=False)
        bin_ser = bin_ser.rank(method='dense')
        df[bin_out_col] = bin_ser.values
        # we need the same index ordering for apply to work
        df = df.reindex(index=orig_index)
    df[bin_out_col] = df[bin_out_col].astype(int)
    return df
