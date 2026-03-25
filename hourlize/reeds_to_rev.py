"""
This file is for converting back from ReEDS capacity results to reV sites.
"""
import argparse
import logging
import os
from pathlib import Path
import sys
import shutil
import traceback
from collections import OrderedDict

import h5py
import numpy as np
import pandas as pd

logger = logging.getLogger("reeds_to_rev")
VALID_TECHS = ["wind-ons", "wind-ofs", "upv", "dupv", "csp"]


def setup_logger(existing_logger, log_level=logging.INFO):
    """
    Sets up pre-existing ``logger`` with with a streamhandler
    and messaging foramtting.

    Parameters
    ----------
    existing_logger : logging.Logger
        Pre-existing logger which will be setup.
    log_level : int, optional
        Logging level. By default logging.INFO (=20). For other valid values
        see https://docs.python.org/3/library/logging.html#logging-levels

    Returns

    Returns
    -------
    logging.Logger
        Configured logger. Note: if your existing_logger is a global,
        this return variable can be discarded.
    """

    existing_logger.setLevel(log_level)
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    stream.setFormatter(formatter)
    existing_logger.addHandler(stream)

    return existing_logger


def set_log_levels(existing_logger, log_level=logging.DEBUG):
    """
    Sets the log level for all handlers of an existing logger.

    Parameters
    ----------
    existing_logger : logging.Logger
        Existing logger instance.
    log_level : int, optional
        Level to apply to existing logger handlers, by default logging.DEBUG.
    """
    for handler in existing_logger.handlers:
        handler.setLevel(log_level)


def add_filehandler(existing_logger, log_dir):
    """
    Adds a FileHanndler to an existing logger. This enables writing of log messages to
    a file named ``reeds_to_rev.log`` in the specified ``log_dir``.

    Parameters
    ----------
    existing_logger : logging.Logger
        Existing logger instance.
    log_dir : pathlib.Path
        Path to directory in which filehandler will write log.
    """
    log_file = log_dir.joinpath("reeds_to_rev.log")
    fh = logging.FileHandler(log_file, mode="w")
    fh.setLevel(existing_logger.handlers[0].level)
    fh.setFormatter(existing_logger.handlers[0].formatter)
    existing_logger.addHandler(fh)


def get_reeds_years(run_folder, first_year=2009):
    """
    Gets the list of years modeled by ReEDs for the specified model run.

    Parameters
    ----------
    run_folder : str
        Path to the folder containing the ReEDS run of interest. The following file
        must be present in this folder: outputs/systemcost.csv.
    first_year : int, optional
        The first year modeled by ReEDS, by default 2009. This value is pre-pended
        return list.

    Returns
    -------
    list[int]
        List of years that were modeled by ReEDS, in ascending order.
    """
    year_src = os.path.join(run_folder, "outputs", "systemcost.csv")
    df_yr = pd.read_csv(year_src, low_memory=False)
    if "Dim2" in df_yr.columns:
        year_col = "Dim2"
    elif "t" in df_yr.columns:
        year_col = "t"
    else:
        raise ValueError(f"Could not find identify year column in {year_src}")
    years = sorted(df_yr[year_col].unique().tolist())
    if years[0] > first_year:
        years.insert(0, first_year)
    return years


def expand_star(df, index=True, col=None):
    """
    Expands technologies according to GAMS syntax.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to be expanded.
    index : bool, optional
        If True (default), uses index as technology to expand. If False, uses the
        column specified by ``col``.
    col : str, optional
        If ``index = False``, this value is required and is used as the technology
        to expand. By default, this is None.

    Returns
    -------
    pandas.DataFrame
        DataFrame with the values in index or col expanded according to GAMS syntax.
    """

    def expand(df):
        df_new = pd.DataFrame(columns=df.columns)
        for subset in df.index:
            temp_save = []
            if "*" in subset:
                temp_remove = df.loc[[subset]]
                df.drop(subset, inplace=True)
                temp = subset.split("*")
                temp2 = temp[0].split("_")
                temp_low = pd.to_numeric(temp[0].split("_")[-1])
                temp_high = pd.to_numeric(temp[1].split("_")[-1])
                temp_tech = ""
                for n in range(0, len(temp2) - 1):
                    temp_tech += temp2[n]
                    if not n == len(temp2) - 2:
                        temp_tech += "_"
                for c in range(temp_low, temp_high + 1):
                    temp_save.append(f"{temp_tech}_{c}")
                df_new = pd.concat(
                    [
                        df_new,
                        pd.DataFrame(
                            np.repeat(temp_remove.values, len(temp_save), axis=0),
                            index=temp_save,
                            columns=df.columns,
                        ),
                    ]
                )
        return pd.concat([df, df_new])

    if index:
        return expand(df)

    tmp = expand(df.set_index(col))
    return tmp.reset_index().rename(columns={"index": col})


def get_reeds_tech_lifetimes(run_folder):
    """
    Helper function for prepare_data(). Finds the lifetime (in years) for each
    technology modeled by ReEDS.

    Parameters
    ----------
    run_folder : str
        Path to the folder containing the ReEDS run of interest. The following file
        must be present in this folder: inputs_case/maxage.csv.

    Returns
    -------
    pandas.DataFrame
        Defines the the lifetime (in years) for each technology modeled by ReEDS.
        Columns include: ["tech", "lifetime"].
    """
    lifetimes_src = os.path.join(run_folder, "inputs_case", "maxage.csv")
    lifetimes_df = pd.read_csv(lifetimes_src, names=["tech", "lifetime"])

    lifetimes_expanded_df = expand_star(lifetimes_df, index=False, col="tech")

    return lifetimes_expanded_df


def get_reeds_formatted_rev_supply_curve(sc_file, tech, run_folder):
    """
    Helper function for prepare_data(). Get reV supply curve and return as a DataFrame.
    Includes some augmentation of the source CSV by adding new columns.

    Parameters
    ----------
    sc_file : str
        Path to supply curve data.
    tech : str
        Technology associated with the supply curve. Expected values are:
        ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].
    run_folder : str
        Path to the folder containing the ReEDS run of interest. Must contain the
        following file: inputs_case/site_bin_map.csv.

    Returns
    -------
    pandas.DataFrame
        DataFrame comprising the supply curve for the given technology.
    """
    if os.path.splitext(sc_file)[1] == ".csv":
        try:
            in_sc_df = pd.read_csv(sc_file, low_memory=False)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.info(f"***Error reading {sc_file}...\n{traceback.format_exc()}")
            sys.exit(1)
        if "bin" not in in_sc_df.columns:
            df_site_bin_map = pd.read_csv(
                os.path.join(run_folder, "inputs_case", "site_bin_map.csv")
            )
            tech_site_bin_map = df_site_bin_map[df_site_bin_map["tech"] == tech].copy()
            tech_site_bin_map.drop(columns=["tech"], inplace=True)
            tech_site_bin_map.drop_duplicates(inplace=True)
            in_sc_df = in_sc_df.merge(tech_site_bin_map, on="sc_point_gid", how="inner")
            in_sc_df["bin"] = in_sc_df["bin"].astype(int)
    elif os.path.splitext(sc_file)[1] == ".h5":
        with h5py.File(sc_file, mode="r") as h:
            in_sc_df = pd.DataFrame(np.asarray(h["rev"]["supply_curve"]))
        in_sc_df.rename(
            columns={
                "gid": "sc_gid",
                "substation_gid": "sc_point_gid",
                "re_class": "class",
                "capacity_mw": "capacity",
            },
            inplace=True,
        )
        rname = "p" if tech in ["upv", "dupv"] else "s"
        in_sc_df["region"] = rname + in_sc_df["model_region"].map(str)
        in_sc_df["bin"] = None

    if tech == "dupv":
        in_sc_df["bin"] = None

    return in_sc_df


def reaggregate_supply_curve_regions(df_sc_in, run_folder, reeds_path):
    """
    Helper function for prepare_data(). If the ReEDS run used aggregated regions, this
    function will map original supply curve regions to new aggregation regions.

    Parameters
    ----------
    df_sc_in : pandas.DataFrame
        Supply curve dataframe, typically from  get_reeds_formatted_rev_supply_curve().
        Must contain a column named "region".
    run_folder : str
        Path to the folder containing the ReEDS run of interest. Must contain the
        following file: inputs_case/switches.csv.
    reeds_path : str
        If the ReEDS run used aggregated regions, this folder must contain the following
        file: inputs/rsmap_sreg.csv.

    Returns
    -------
    pandas.DataFrame
        If the ReEDS run used aggregated regions, returns a modified version of
        ``df_sc_in`` where values of "region" are remapped to aggregated regions.
        If not, returns ``df_sc_in`` unchanged.
    """
    sw = pd.read_csv(
        os.path.join(run_folder, "inputs_case", "switches.csv"),
        header=None,
        index_col=0,
        squeeze=True,
    )
    if int(sw.get("GSw_AggregateRegions", 0)):
        ### Load original hierarchy file
        if sw["GSw_HierarchyFile"] == "default":
            file_suffix = ""
        else:
            file_suffix = f"_{sw['GSw_HierarchyFile']}"
        hierarchy = pd.read_csv(
            os.path.join(reeds_path, "inputs", f"hierarchy{file_suffix}.csv"),
            index_col="*r",
        )
        r2aggreg = hierarchy.aggreg.copy()

        ### Map original regions to new aggreg's
        df_sc_in["region"] = df_sc_in["region"].map(r2aggreg)

    return df_sc_in


def subset_supply_curve_columns(df_sc_in, tech, priority_cols):
    """
    Helper function for prepare_data(). Subsets the input supply curve DataFrame to only
    a select set of columns.

    Parameters
    ----------
    df_sc_in : pandas.DataFrame
        Supply curve dataframe, typically from get_reeds_formatted_rev_supply_curve()
        (via reaggregate_supply_curve_regions()). Must contain the following columns:
        ["sc_gid", "sc_point_gid", "latitude", "longitude", "region", "class", "bin",
        "capacity"] and, if ``tech="dupv"`, "compare".
    tech : str
        Technology associated with the supply curve. Expected values are:
        ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].
    priority_cols : list[str]
        List of priority columns that will be used downstream in
        disaggregate_reeds_to_rev(). This list has the effect of ensuring these
        columns are included in the output DataFrame.

    Returns
    -------
    pandas.DataFrame
        New DataFrame that is a subset of the columns from ``df_sc_in``. Output columns
        include: []"sc_gid", "sc_point_gid", "latitude", "longitude", "region", "class",
        "bin", "cap_avail"] plus the columns specified in the input ``priority_cols``.

    Raises
    ------
    KeyError
        _description_
    """
    missing_cols = list(set(priority_cols).difference(set(df_sc_in.columns)))
    if len(missing_cols) > 0:
        raise KeyError(
            "One or more columns specified in priority_cols cannot be found in "
            f"df_sc_in. Missing columns include: {missing_cols}"
        )

    subset_cols = [
        "sc_gid",
        "sc_point_gid",
        "latitude",
        "longitude",
        "region",
        "class",
        "bin",
        "capacity",
    ]
    if tech == "dupv":
        subset_cols.insert(-2, "compare")

    df_sc_subset = df_sc_in[subset_cols].copy()
    rename = {"capacity": "cap_avail"}
    df_sc_subset.rename(columns=rename, inplace=True)

    priority_cols_add = [c for c in priority_cols if c not in df_sc_subset.columns]
    df_sc_priority = df_sc_in[priority_cols_add].copy()

    df_sc_combined = pd.concat([df_sc_subset, df_sc_priority], axis=1)

    return df_sc_combined


def get_preexisting_capacity(df_sc_in, tech, first_model_year=2009):
    """
    Helper function for prepare_data(). If existing capacity is defined in the supply
    curve, this function finds the capacity existing prior to the first model year and
    treats it as an investment in the first model year.

    Parameters
    ----------
    df_sc_in : pandas.DataFrame
        Supply curve DataFrame. Must contain the following columns:
        ["existing_capacity", "online_year", "tech", "region", "year", "class", "bin",
        "MW"].
    tech : str
        Technology associated with the supply curve. Expected values are:
        ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].
    first_model_year : int, optional
        First year modeled by ReEDs, by default 2009.

    Returns
    -------
    pandas.DataFrame
        Returns a DataFrame summarizing the existing capacity by technology, region,
        year, and bin. Output columns include: ["tech", "region", "year", "bin", "MW"]

    Raises
    ------
    KeyError
        A KeyError will be raised if the input DataFrame has an "existing_capacity"
        column but does not have an "online_year" column.
    """
    # Find existing capacity by bin with raw supply curve.
    # Consider existing capacity as investment in 2009 to use the
    # same logic as inv_rsc when assigning to gid.
    exist_columns = ["tech", "region", "year", "bin", "MW"]
    if "existing_capacity" in df_sc_in:
        if "online_year" not in df_sc_in:
            raise KeyError(
                "online_year column not found. "
                "It is required for getting preexisting capacity."
            )
        df_bin_exist = df_sc_in[
            (df_sc_in["existing_capacity"] > 0)
            & (df_sc_in["online_year"] <= first_model_year)
        ].copy()
        df_bin_exist = df_bin_exist[
            ["region", "class", "bin", "existing_capacity"]
        ].copy()
        df_bin_exist = df_bin_exist.groupby(
            ["region", "class", "bin"], sort=False, as_index=False
        ).sum()
        df_bin_exist["raw_tech"] = tech
        df_bin_exist["tech"] = (
            df_bin_exist["raw_tech"] + "_" + df_bin_exist["class"].astype(str)
        )
        df_bin_exist["year"] = first_model_year
        df_bin_exist["bin"] = "bin" + df_bin_exist["bin"].astype(str)
        df_bin_exist["MW"] = df_bin_exist["existing_capacity"]
        df_bin_exist = df_bin_exist[exist_columns].copy()
    else:
        df_bin_exist = pd.DataFrame(columns=exist_columns)

    return df_bin_exist


def get_capacity_check_data(run_folder, tech):
    """
    Helper function for prepare_data(). Gets summary of capacity by year, region, and
    class that can be used to check capacity values at the end of disaggregation.

    Parameters
    ----------
    run_folder : str
        Path to the folder containing the ReEDS run of interest. Must contain the
        following file: outputs/cap.csv.
    tech : str
        Technology. Expected values are: ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].

    Returns
    -------
    pandas.DataFrame
        DataFrame defining deployed total capacity for the specified technology by
        year, region, and class. Output columns include: ["year", "region", "class",
        "MW"].
    """
    # Get check for capacity
    cap_chk = os.path.join(run_folder, "outputs", "cap.csv")
    df_cap_chk = pd.read_csv(
        cap_chk, low_memory=False, names=["tech", "region", "year", "MW"], header=0
    )
    df_cap_chk = df_cap_chk[df_cap_chk["tech"].str.startswith(tech)].copy()
    df_cap_chk[["tech_cat", "class"]] = df_cap_chk["tech"].str.split(
        "_", 1, expand=True
    )
    df_cap_chk = df_cap_chk[["year", "region", "class", "MW"]].dropna(subset=["class"])
    df_cap_chk["class"] = df_cap_chk["class"].astype("int")

    return df_cap_chk


def get_new_investments(run_folder, tech):
    """
    Helper function for prepare_data(). Produces a DataFrame summarizing the new
    capacity deployed by year to each region, year, class, and bin.

    Parameters
    ----------
    run_folder : str
        Path to the folder containing the ReEDS run of interest. Must contain the
        following file: outputs/cap_new_bin_out.csv.
    tech : str
        Technology. Expected values are: ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].

    Returns
    -------
    pandas.DataFrame
        DataFrame defining new deployed capacity by year for each region, class, and
        bin. Output columns include: ["tech", "region", "year", "bin", "MW"].
    """
    # Read in inv_rsc
    # source of New investments by reg/class/bin
    inv_rsc = os.path.join(run_folder, "outputs", "cap_new_bin_out.csv")
    df_inv_rsc = pd.read_csv(
        inv_rsc,
        low_memory=False,
        names=["tech", "vintage", "region", "year", "bin", "MW"],
        usecols=["tech", "region", "year", "bin", "MW"],
        header=0,
    )
    df_inv_rsc = df_inv_rsc[df_inv_rsc["tech"].str.startswith(tech)].copy()

    return df_inv_rsc


def combine_preexisting_and_new_investments(df_bin_exist, df_inv_rsc):
    """
    Helper function for prepare_data(). Combines pre-existing and new deployed capacity
    into a single DataFrame.

    Parameters
    ----------
    df_bin_exist : pandas.DataFrame
        DataFrame defining pre-existing deployed capacity. Typically from
        get_preexisting_capacity() .
    df_inv_rsc : _type_
        DataFrame defining new deployed capacity. Typically from
        get_new_investments() .

    Returns
    -------
    pandas.DataFrame
        Returns consolidated pre-existing and new deployed capacity by year, region,
        class, and bin. Output columns are: ["year", "region", "class",  bin", "MW"].
    """
    # Concatenate existing and inv_rsc
    df_inv = pd.concat([df_bin_exist, df_inv_rsc], sort=False, ignore_index=True)
    # Split tech from class
    df_inv[["tech_cat", "class"]] = df_inv["tech"].str.split("_", 1, expand=True)
    df_inv = df_inv[["year", "region", "class", "bin", "MW"]]
    df_inv["class"] = df_inv["class"].astype("int")
    df_inv["bin"] = df_inv["bin"].str.replace("bin", "", regex=False).astype("int")
    df_inv = df_inv.sort_values(by=["year", "region", "class", "bin"])

    return df_inv


def get_input_refurbishments(run_folder, tech):
    """
    Helper function for prepare_data(). Loads refurbishment capacities to DataFrame.

    Parameters
    ----------
    run_folder : str
        Path to the folder containing the ReEDS run of interest. Must contain the
        following file: outputs/cap_new_ivrt_refurb.csv.
    tech : str
        Technology. Expected values are: ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].

    Returns
    -------
    pandas.DataFrame
        Returns refurbishments for the given technology, in their raw format as output
        by ReEDS. Output columns include: ["tech", "region", "year", "MW"].
    """
    # Refurbishments
    # source of Refurbishments by reg/class/bin
    inv_refurb = os.path.join(run_folder, "outputs", "cap_new_ivrt_refurb.csv")
    df_inv_refurb_in = pd.read_csv(
        inv_refurb,
        low_memory=False,
        names=["tech", "vintage", "region", "year", "MW"],
        header=0,
        usecols=["tech", "region", "year", "MW"],
    )
    df_inv_refurb_in = df_inv_refurb_in[
        df_inv_refurb_in["tech"].str.startswith(tech)
    ].copy()

    return df_inv_refurb_in


def amend_refurbishments(df_inv_refurb_in):
    """
    Helper function for prepare_data(). Amends and reformats refurbishment capacities.

    Parameters
    ----------
    df_inv_refurb_in : pandas.DataFrame
        Refurbishment capacities, sourced from get_input_refurbishments().
        Required columns are ["tech", "region", "year", "MW"].

    Returns
    -------
    pandas.DataFrame
        Returns refurbishments for the given technology, by year, region, and class.
        Output columns include: ["year", "region", "class", "MW"]
    """
    # Split tech from class
    df_inv_refurb = df_inv_refurb_in.copy()
    if df_inv_refurb.empty:
        df_inv_refurb[["tech_cat", "class"]] = ""
    else:
        df_inv_refurb[["tech_cat", "class"]] = df_inv_refurb["tech"].str.split(
            "_", 1, expand=True
        )
    df_inv_refurb = df_inv_refurb[["year", "region", "class", "MW"]]
    df_inv_refurb["class"] = df_inv_refurb["class"].astype("int")
    df_inv_refurb = df_inv_refurb.sort_values(by=["year", "region", "class"])

    return df_inv_refurb


def get_retirements_of_new(df_new_investments, lifetimes, years):
    """
    Helper function for prepare_data(). Produces a DataFrame summarizing the amount
    of capacity from new deployments retired by year, region, and class.

    Parameters
    ----------
    df_new_investments : pandas.DataFrame
        DataFrame defining new deployed capacity by year, region, bin, and class.
        Typically sourced from get_new_investments().
    lifetimes : pandas.DataFrame
        DataFrame defining lifetimes of ReEDS technologies. Typically sourced from
        get_reeds_tech_lifetimes().
    years : list[int]
        Model years to run. Typically sourced from get_reeds_years()

    Returns
    -------
    pandas.DataFrame
        DataFrame summarizing the amount of capacity from new deployments retired by
        year, region, and class. Output columns include: ["tech", "region", "year",
        "bin", "MW"].
    """
    # Retirements of inv_rsc
    df_ret_inv_rsc = df_new_investments.drop(columns=["bin"])
    df_ret_inv_rsc = pd.merge(df_ret_inv_rsc, lifetimes, on="tech")
    df_ret_inv_rsc["year"] += df_ret_inv_rsc["lifetime"]
    # Ensure lifetime retirements hit on a year in years
    # Set each year to the first year greater than or equal to it in years
    yr_idx = df_ret_inv_rsc["year"] <= max(years)
    df_ret_inv_rsc.loc[yr_idx, "year"] = df_ret_inv_rsc.loc[yr_idx, "year"].apply(
        lambda x: years[
            next(
                (
                    index
                    for index, value in enumerate([y - x for y in years])
                    if value >= 0
                ),
                None,
            )
        ]
    )

    return df_ret_inv_rsc


def get_retirements_of_refurbishments(df_refurb_investments_in, lifetimes, years):
    """
    Helper function for prepare_data(). Produces a DataFrame summarizing the amount
    of capacity from refurbishments retired by year, region, and class.

    Parameters
    ----------
    df_refurb_investments_in : pandas.DataFrame
        DataFrame defining refurbished capacity by year, region, bin, and class.
        Typically sourced from get_input_refurbishments().
    lifetimes : pandas.DataFrame
        DataFrame defining lifetimes of ReEDS technologies. Typically sourced from
        get_reeds_tech_lifetimes().
    years : list[int]
        Model years to run. Typically sourced from get_reeds_years()

    Returns
    -------
    pandas.DataFrame
        DataFrame summarizing the amount of capacity from refurbishments retired by
        year, region, and class. Output columns include: ["tech", "region", "year",
        "MW"].
    """

    # Retirements of inv_refurb:
    df_ret_inv_refurb = pd.merge(df_refurb_investments_in, lifetimes, on="tech")
    df_ret_inv_refurb["year"] += df_ret_inv_refurb["lifetime"]
    # Ensure refurbishments hit on a year in years
    # Set each year to the first year greater than or equal to it in years
    yr_idx = df_ret_inv_refurb["year"] <= max(years)
    df_ret_inv_refurb.loc[yr_idx, "year"] = df_ret_inv_refurb.loc[yr_idx, "year"].apply(
        lambda x: years[
            next(
                (
                    index
                    for index, value in enumerate([y - x for y in years])
                    if value >= 0
                ),
                None,
            )
        ]
    )

    return df_ret_inv_refurb


def get_exogenous_capacity(run_folder, tech):
    """
    Loads exogenous capacity by region, year, and class from ReEDS outputs.

    Parameters
    ----------
    run_folder : str
        Path to the folder containing the ReEDS run of interest. Must contain the
        following file: outputs/cap_exog.csv.
    tech : str
        Technology. Expected values are: ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].

    Returns
    -------
    pandas.DataFrame
        Exogenous capacity by year, region, and class. Output columns include:
        ["tech", "region", "year", "MW"].
    """

    # Source of Existing capacity over time. Used for retirements of existing capacity.
    cap_exog = os.path.join(run_folder, "outputs", "cap_exog.csv")
    df_cap_exog = pd.read_csv(
        cap_exog,
        low_memory=False,
        names=["tech", "vintage", "region", "year", "MW"],
        header=0,
        usecols=["tech", "region", "year", "MW"],
    )
    df_cap_exog = df_cap_exog[df_cap_exog["tech"].str.startswith(tech)].copy()

    return df_cap_exog


def get_retirements_of_preexisting(df_cap_exog, years):
    """
    Helper function for prepare_data(). Produces a DataFrame summarizing the amount
    of capacity from pre-existing investments retired by year, region, and class.

    Parameters
    ----------
    df_cap_exog : pandas.DataFrame
        DataFrame defining exogenous capacity by year, region, and class.
        Typically sourced from get_exogenous_capacity().
    years : list[int]
        Model years to run. Typically sourced from get_reeds_years().

    Returns
    -------
    pandas.DataFrame
        DataFrame summarizing the amount of capacity from pre-existing investments
        retired by year, region, and class. Output columns include: ["tech", "region",
        "year", "MW"].
    """

    # Retirements of existing by taking year-to-year difference of cap_exog.
    if not df_cap_exog.empty:
        # Filter to years of cap_new_bin_out
        df_cap_exog = df_cap_exog[df_cap_exog["year"].isin(years)].copy()
        # pivot out table, add another year and fill with zeros, then melt back
        df_cap_exog = df_cap_exog.pivot_table(
            index=["tech", "region"], columns=["year"], values="MW"
        ).reset_index()
        df_cap_exog.fillna(0, inplace=True)
        # This finds the next year in years and sets it equal to zero.
        # If there are more years in df_cap_exog, latest year + 1 is
        # set equal to 0. This only happens if run is only through 2020s
        if years.index(df_cap_exog.columns[-1]) == (len(years) - 1):
            yr = df_cap_exog.columns[-1] + 1
        else:
            yr = years[years.index(df_cap_exog.columns[-1]) + 1]
        df_cap_exog[yr] = 0
        # Melt back and diff
        df_cap_exog = pd.melt(
            df_cap_exog,
            id_vars=["tech", "region"],
            value_vars=df_cap_exog.columns.tolist()[2:],
            var_name="year",
            value_name="MW",
        )
        df_ret_exist = df_cap_exog.copy()
        df_ret_exist["MW"] = df_ret_exist.groupby(["tech", "region"])["MW"].diff()
        df_ret_exist["MW"].fillna(0, inplace=True)
        df_ret_exist["MW"] = df_ret_exist["MW"] * -1
    else:
        df_ret_exist = pd.DataFrame()

    return df_ret_exist


def combine_retirements(
    df_ret_preexist, df_ret_new_investments, df_ret_refurbishments, years
):
    """
    Combines various retirement DataFrames (pre-existing, new, and refurbishments) into
    a single retirement DataFrame.

    Parameters
    ----------
    df_ret_preexist : pandas.DataFrame
        Summary of retirements of pre-existing capacity. Typically sourced from
        get_retirements_of_preexisting().
    df_ret_new_investments : pandas.DataFrame
        Summary of retirements of new deployed capacity. Typically sourced from
        get_retirements_of_new().
    df_ret_refurbishments : pandas.DataFrame
        Summary of retirements of refurbished capacity. Typically sourced from
        get_retirements_of_refurbishments().
    years : list[int]
        Model years to run. Typically sourced from get_reeds_years().

    Returns
    -------
    pandas.DataFrame
        Summary of all retirements by year, region, and class. Output columns include:
        ["year", "region", "class", "MW"].
    """

    # Concatenate retirements of existing, inv_rsc, and inv_refurb
    df_ret = pd.concat(
        [df_ret_preexist, df_ret_new_investments, df_ret_refurbishments],
        sort=False,
        ignore_index=True,
    )
    # remove zeros
    df_ret = df_ret[df_ret["MW"] != 0].copy()
    # Remove retirements in later years
    df_ret = df_ret[df_ret["year"].isin(years)].copy()
    # Split tech from class
    if not df_ret.empty:
        df_ret[["tech_cat", "class"]] = df_ret["tech"].str.split("_", 1, expand=True)
        df_ret = df_ret[["year", "region", "class", "MW"]]
        df_ret["class"] = df_ret["class"].astype("int")
        df_ret = df_ret.sort_values(by=["year", "region", "class"])
    else:
        df_ret["class"] = 0
        df_ret = df_ret[["year", "region", "class", "MW"]]

    return df_ret


def prepare_data(
    reeds_path, run_folder, sc_file, tech, priority_cols, check_results=True
):
    # pylint: disable=too-many-branches,too-many-statements
    """
    Prepares a number of DataFrames required to run disaggregate_reeds_to_rev().
    These DataFrames are created from a combination of the ReEDS model run outputs and
    the ReEDS-formatted supply curve associated with that model run.

    Parameters
    ----------
    reeds_path : str
        Path to ReEDS directory. This should typically be the parent directory of the
        run_folder.
    run_folder : str
        Path to the folder containing the ReEDS run of interest. This folder is
        expected to contain `inputs_case` and `outputs` subfolders. Required files
        in this folder include:
            - inputs_case/supplycurve_metadata/rev_supply_curves.csv
            - inputs_case/maxage.csv
            - inputs_case/site_bin_map.csv
            - inputs_case/switches.csv
            - outputs/cap_new_bin_out.csv
            - outputs/cap_new_ivrt_refurb.csv
            - outputs/cap.csv
            - outputs/cap_exog.csv
            - outputs/systemcost.csv
    sc_file : str
        Path to supply curve file used by this ReEDS model run.
    tech : str
        Name of the technology that was run through ReEDs to rev. Expected values are:
        ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].
    priority_cols : list[str]
        List of priority columns that will be used in downstream disaggregation. This
        list has the effect of ensuring that these columns are included in the output
        DataFrame ``df_sc_in``.
    check_results : bool, optional
        If True (default), derive and include the ``df_cap_chk`` DataFrame in the
        outputs. If False, the ``df_cap_chk`` output will be ``None``.

    Returns
    -------
    dict
        Returns a dictionary with the following keys and values:
            - "df_sc_in": pandas.DataFrame consisting of a modified version of the
                input technology supply curve. All supply curve rows are present but
                only a subset of the columns are present, including:
                ["sc_gid", "sc_point_gid", "latitude", "longitude", "region", "class",
                "bin", "cap_avail"] plus any priority columns specified by the input
                ``priority_cols`` (e.g., "supply_curve_cost_per_mw").
            - "df_ret": pandas.DataFrame defining the retirements of capacity by
                year, region, and class. Columns include: ["year", "region", "class",
                "MW"].
            - "df_refurbishments": pandas.DataFrame defining the refurbishments of
                capacity by year, region, and class. Columns include: ["year", "region",
                 "class", "MW"].
            - "df_new_and_preexisting_investments": pandas.DataFrame defining the new
                and pre-existing deployments of capacity by year, region, class, and
                resource bin. Columns include: ["year", "region", "class", "bin", "MW"].
            - "df_cap_chk": If ``check_results == True``, this is a pandas.DataFrame
                with data for each model year, defining the aggregate capacity by region
                and class. Columns include: ["year", "region", "class", "MW"]. If
                ``check_results == False``, this is ``None``.
            - "years": list of the years modeled by ReEDS, in ascending order
    """

    # load required data
    years = get_reeds_years(run_folder)
    lifetimes = get_reeds_tech_lifetimes(run_folder)
    df_cap_exog = get_exogenous_capacity(run_folder, tech)
    if check_results:
        df_cap_chk = get_capacity_check_data(run_folder, tech)
    else:
        df_cap_chk = None

    # Load and prepare supply curve data and pre-existing capacity
    input_sc_df = get_reeds_formatted_rev_supply_curve(sc_file, tech, run_folder)
    input_sc_df = reaggregate_supply_curve_regions(input_sc_df, run_folder, reeds_path)

    df_bin_exist = get_preexisting_capacity(input_sc_df, tech, first_model_year=2009)

    df_sc_in = subset_supply_curve_columns(input_sc_df, tech, priority_cols)

    # Prepare Capital Stock Data
    # new and existing investments
    df_new_investments = get_new_investments(run_folder, tech)
    df_new_and_preexisting_investments = combine_preexisting_and_new_investments(
        df_bin_exist, df_new_investments
    )
    # refurbishments
    df_refurbishments_in = get_input_refurbishments(run_folder, tech)
    df_refurbishments = amend_refurbishments(df_refurbishments_in)
    # retirements
    df_ret_preexist = get_retirements_of_preexisting(df_cap_exog, years)
    df_ret_new_investments = get_retirements_of_new(
        df_new_investments, lifetimes, years
    )
    df_ret_refurbishments = get_retirements_of_refurbishments(
        df_refurbishments_in, lifetimes, years
    )
    df_ret = combine_retirements(
        df_ret_preexist, df_ret_new_investments, df_ret_refurbishments, years
    )

    reeds_to_rev_data = {
        "df_sc_in": df_sc_in,
        "df_ret": df_ret,
        "df_refurbishments": df_refurbishments,
        "df_new_and_preexisting_investments": df_new_and_preexisting_investments,
        "df_cap_chk": df_cap_chk,
        "years": years,
    }

    return reeds_to_rev_data


def add_accounting_columns(df_sc_in):
    """
    Adds columns to supply curve data frame that that are needed for accounting purposes
    during capacity disaggregation.

    Parameters
    ----------
    df_sc_in : pandas.DataFrame
        Modified/simplified version of the technology supply curve.
        Typically includes all supply curve rows and a subset of the columns, including:
        ["sc_gid", "sc_point_gid", "latitude", "longitude", "region", "class", "bin",
        "cap_avail", "cap_expand", "cap_left", "cap", "inv_rsc", "ret", "refurb",
        "expanded"] plus any priority columns to be used during disaggregation.

    Returns
    -------
    pandas.DataFrame
        Version of input DataFrame ``df_sc_in`` with the following columns added:
        ["cap_expand", "cap_left", "cap", "inv_rsc", "ret", "refurb", "expanded"].
    """
    df_sc = df_sc_in.copy()
    df_sc["cap_expand"] = df_sc["cap_avail"]
    df_sc["cap_left"] = df_sc["cap_avail"]
    df_sc["cap"] = 0
    df_sc["inv_rsc"] = 0
    df_sc["ret"] = 0
    df_sc["refurb"] = 0
    df_sc["expanded"] = "no"

    return df_sc


def sort_sites_by_priority(df_sc, priority):
    """
    Helper function for disaggregate_reeds_to_rev(). Sorts input supply curve DataFrame
    by the specified priority columns.

    Parameters
    ----------
    df_sc : pandas.DataFrame
        Modified/simplified version of the technology supply curve.
        Typically includes all supply curve rows and a subset of the columns, including:
        ["sc_gid", "sc_point_gid", "latitude", "longitude", "region", "class", "bin",
        "cap_avail", "cap_expand", "cap_left", "cap", "inv_rsc", "ret", "refurb",
        "expanded"] plus any priority columns specified by the input keys of
        ``priority`` (e.g., "supply_curve_cost_per_mw").
    priority : dictionary
        Dictionary specifying which columns will be used to prioritize sites for
        disaggregation within each region/class/bin. Keys should be column names, values
        should be either "ascending" or "descending". For example, to prioritize on
        cheapest sites first, the input would be
        ``{"supply_curve_cost_per_mw": "ascending"}``.

    Returns
    -------
    pandas.DataFrame
        Sorted version of input dataframe ``dc_sc``.
    """

    sort_columns = OrderedDict({"region": True, "class": True})
    for column, sort_order in priority.items():
        sort_columns[column] = sort_order == "ascending"
    expected_column_order = ["region", "class"] + list(priority.keys())

    # make sure the order of columns is still correct
    if list(sort_columns.keys()) != expected_column_order:
        raise ValueError("sort columns are not in the correct order.")

    sorted_df = df_sc.sort_values(
        by=list(sort_columns.keys()), ascending=list(sort_columns.values())
    )

    return sorted_df


def disaggregate_reeds_to_rev(
    df_sc_in,
    df_ret,
    df_refurbishments,
    df_new_and_preexisting_investments,
    df_cap_chk,
    priority,
    years,
    constrain_to_bins=True,
):
    # pylint: disable=too-many-branches,too-many-statements
    """
    Performs the actual disaggregation of capacity from ReEDS regions to reV supply
    curve project sites. Loops through years and determins the investment
    in each supply curve point in each year. Investments in are determined by filling up
    the supply curve point  capacities in the associated region, class, and (optionally)
    bin using the user-specified prioritization.

    Parameters
    ----------
    df_sc_in : pandas.DataFrame
        Modified/simplified version of the technology supply curve.
        All supply curve rows are present but only a subset of the columns are present,
        including: ["sc_gid", "sc_point_gid", "latitude", "longitude", "region",
        "class", "bin", "cap_avail"] plus any priority columns specified by the input
        ``priority`` (e.g., "supply_curve_cost_per_mw").
    df_ret : pandas.DataFrame
        Defines the retirements of capacity by year, region, and class.
        Columns include: ["year", "region", "class", "MW"].
    df_refurbishments : pandas.DataFrame
        Defines the refurbishments of capacity by year, region, and class.
        Columns include: ["year", "region", "class", "MW"].
    df_new_and_preexisting_investments : pandas.DataFrame
        Defines the new and pre-existing deployments of capacity by year, region, class,
        and resource bin. Columns include: ["year", "region", "class", "bin", "MW"].
    df_cap_chk : pandas.DataFrame
        Defines the aggregate capacity by year, region and class.
        Columns include: ["year", "region", "class", "MW"]. Used for a soft check of
        the disaggregation results. If ``None``, the soft check will not be performed.
    priority : dictionary
        Dictionary specifying which columns will be used to prioritize sites for
        disaggregation within each region/class/bin. Keys should be column names, values
        should be either "ascending" or "descending". For example, to prioritize on
        cheapest sites first, the input would be
        ``{"supply_curve_cost_per_mw": "ascending"}``.
    years : list[int]
        Years to disaggregate. Typically from get_reeds_years().
    constrain_to_bins : bool, optional
        If True (default), disaggregation of new and pre-exising capacity will be
        constrained by region, class, and bin. If False, disaggregation will only be
        constrained by region and class. The latter option will result in greater
        flexibility of the disaggregation, but less fidelity to the ReEDS results, and
        is intended primarily for sensitivity testing or bounding scenarios.

    Returns
    -------
    pandas.DataFrame
        Results of disaggregation. Each row represents a reV supply curve project site
        for a given year. Columns describe input information about the project site and
        capacity deployed to that project site. Output columns  include input
        attributes (["sc_gid", "sc_point_gid", "latitude", "longitude",  "region",
        "class", "bin", "cap_avail", "supply_curve_cost_per_mw"]) and outputs from
        disaggregation (["cap_expand", "cap_left", "cap", "inv_rsc", "ret",  "refurb",
        "expanded", "year"]).
    """

    df_sc = add_accounting_columns(df_sc_in)
    df_sc_sorted = sort_sites_by_priority(df_sc, priority)

    df_sc_out = pd.DataFrame()
    for year in years:
        logger.info(f"Starting {year}")
        df_sc_sorted["year"] = year

        # First retirements
        # reset retirements associated with gids for each year.
        df_sc_sorted["ret"] = 0
        df_ret_yr = df_ret[df_ret["year"] == year].copy()

        for _, r in df_ret_yr.iterrows():
            # This loops through all the retirements
            df_sc_rc = df_sc_sorted[
                (df_sc_sorted["region"] == r["region"])
                & (df_sc_sorted["class"] == r["class"])
            ].copy()
            rcy = str(r["region"]) + "_" + str(r["class"]) + "_" + str(year)
            ret_left = r["MW"]
            for sc_i, sc_r in df_sc_rc.iterrows():
                # This loops through each gid of the supply curve for this
                # ReEDS region and class
                # Floor is to ensure rounding doesn't lead to small overbuilds
                if np.floor(ret_left * 100) / 100 > np.floor(sc_r["cap"] * 100) / 100:
                    # retirement is too large for just this gid. Fill up this
                    # gid and move to the next.
                    df_sc_sorted.loc[sc_i, "ret"] = sc_r["cap"]
                    ret_left = ret_left - sc_r["cap"]
                    df_sc_sorted.loc[sc_i, "cap"] = 0
                else:
                    # Remaining retirement is smaller than capacity in this gid
                    # so assign remaining retirement to this gid and break the
                    # loop through gids to move to the next retirement by
                    # ReEDS region and class.
                    df_sc_sorted.loc[sc_i, "ret"] = ret_left
                    df_sc_sorted.loc[sc_i, "cap"] = sc_r["cap"] - ret_left
                    ret_left = 0
                    break
            if np.floor(ret_left * 100) / 100 != 0:
                logger.info(
                    "ERROR at rcy=%s: ret_left should be 0 and it is:%s",
                    rcy,
                    str(ret_left),
                )

        df_sc_sorted["cap_left"] = df_sc_sorted["cap_expand"] - df_sc_sorted["cap"]

        # Then refurbishments
        # reset refurbishments associated with gids for each year.
        df_sc_sorted["refurb"] = 0
        df_inv_refurb_yr = df_refurbishments[df_refurbishments["year"] == year].copy()

        for _, r in df_inv_refurb_yr.iterrows():
            # This loops through all the refurbishments
            df_sc_rc = df_sc_sorted[
                (df_sc_sorted["region"] == r["region"])
                & (df_sc_sorted["class"] == r["class"])
            ].copy()
            rcy = str(r["region"]) + "_" + str(r["class"]) + "_" + str(year)
            inv_left = r["MW"]
            for sc_i, sc_r in df_sc_rc.iterrows():
                # This loops through each gid of the supply curve for this
                # ReEDS region and class
                if round(inv_left, 2) > round(sc_r["cap_left"], 2):
                    # refurbishment is too large for just this gid. Fill up
                    # this gid and move to the next.
                    # capacity left can be negative for expanded sites, so don't make
                    # negative investment
                    refurb_investment = max(sc_r["cap_left"], 0)
                    df_sc_sorted.loc[sc_i, "refurb"] = refurb_investment
                    inv_left = inv_left - refurb_investment
                    df_sc_sorted.loc[sc_i, "cap_left"] = (
                        sc_r["cap_left"] - refurb_investment
                    )
                else:
                    # Remaining refurbishment is smaller than capacity in this
                    # gid, so assign remaining refurb to this gid and break the
                    # loop through gids to move to the next refurbishment by
                    # ReEDS region and class.
                    df_sc_sorted.loc[sc_i, "refurb"] = inv_left
                    df_sc_sorted.loc[sc_i, "cap_left"] = max(
                        0, sc_r["cap_left"] - inv_left
                    )
                    inv_left = 0
                    break
            if round(inv_left, 2) != 0:
                logger.info(
                    f"ERROR at rcy={rcy}: inv_left for refurb should be 0 "
                    "and it is {inv_left}"
                )

        df_sc_sorted["cap"] = df_sc_sorted["cap_expand"] - df_sc_sorted["cap_left"]

        # Finally, new site investments
        # reset investments associated with gids for each year.
        df_sc_sorted["inv_rsc"] = 0

        if constrain_to_bins:
            df_inv_yr = df_new_and_preexisting_investments[
                df_new_and_preexisting_investments["year"] == year
            ].copy()
        else:
            # need to aggregate results to just year, region, and class before iterating
            # otherwise the investment_bool results may not be correct in cases
            # where a given year+region+class has investments for multiple bins
            df_inv_yr = (
                df_new_and_preexisting_investments[
                    df_new_and_preexisting_investments["year"] == year
                ]
                .groupby(["year", "region", "class"])["MW"]
                .sum()
                .reset_index()
            )

        for _, r in df_inv_yr.iterrows():
            # This loops through all the investments
            # old h5 files don't include bin, so only filter on bin if constrain_to_bins
            # is True and the bin col exists
            df_sc_rc_filter = (df_sc_sorted["region"] == r["region"]) & (
                df_sc_sorted["class"] == r["class"]
            )
            if constrain_to_bins:
                df_sc_filter = df_sc_rc_filter & (
                    (df_sc_sorted["bin"] == r["bin"]) | df_sc_sorted["bin"].isnull()
                )
                bin_label = f"{r['bin']}_"
            else:
                df_sc_filter = df_sc_rc_filter
                bin_label = ""
            df_sc_rcb = df_sc_sorted[df_sc_filter].copy()
            rcby = f"{r['region']}_{r['class']}_{bin_label}{year}"
            inv_left = r["MW"]
            for sc_i, sc_r in df_sc_rcb.iterrows():
                # This loops through each gid of the supply curve for this
                # combination of region/class/bin
                if inv_left - sc_r["cap_left"] > 0.001:
                    # invesment is too large for just this gid.
                    if sc_i == df_sc_rcb.index[-1]:
                        # This is the final supply curve row, so we are
                        # building more capacity than is available in the supply curve.
                        # In this case, we should add the remainder to the
                        # first row, expanding that gids capacity
                        logger.info(
                            f"WARNING at rcby={rcby}. We are building {inv_left} but "
                            f"only have {sc_r['cap_left']}"
                        )
                        df_sc_sorted.loc[sc_i, "inv_rsc"] = sc_r["cap_left"]
                        df_sc_sorted.loc[sc_i, "cap_left"] = 0
                        df_sc_sorted.loc[df_sc_rcb.index[0], "inv_rsc"] += (
                            inv_left - sc_r["cap_left"]
                        )
                        # decrement the capacity left as well (it will go negative)
                        # since cap_left is needed to correctly calculate the "cap"
                        # (aka built_capacity)
                        df_sc_sorted.loc[df_sc_rcb.index[0], "cap_left"] -= (
                            inv_left - sc_r["cap_left"]
                        )
                        df_sc_sorted.loc[df_sc_rcb.index[0], "expanded"] = "yes"
                        inv_left = 0
                        break
                    else:
                        # This is the normal logic. Fill up this gid and move
                        # to the next.
                        df_sc_sorted.loc[sc_i, "inv_rsc"] = sc_r["cap_left"]
                        inv_left = inv_left - sc_r["cap_left"]
                        df_sc_sorted.loc[sc_i, "cap_left"] = 0
                else:
                    # Remaining investment is smaller than available capacity
                    # in this gid, so assign remaining investment to this gid
                    # And break the loop through gids to move to the next
                    # investment by region/class/bin.
                    df_sc_sorted.loc[sc_i, "inv_rsc"] = inv_left
                    df_sc_sorted.loc[sc_i, "cap_left"] = max(
                        0, sc_r["cap_left"] - inv_left
                    )
                    inv_left = 0
                    break
                if inv_left < 0:
                    logger.info(
                        f"ERROR at rcby={rcby}: inv_left is negative: {inv_left}"
                    )
            if round(inv_left, 2) != 0:
                logger.info(
                    f"ERROR at rcby={rcby}: inv_left should be zero "
                    f"and it is: {inv_left}"
                )
        df_sc_sorted["cap"] = df_sc_sorted["cap_expand"] - df_sc_sorted["cap_left"]
        # now that cap is updated, fix any values of cap_left that are negative
        # by changing them to zero. this fixes any other potential issues that could
        # occur due to cap_left being negative
        if (df_sc_sorted["cap_left"] < 0).sum() > 0:
            df_sc_sorted.loc[df_sc_sorted["cap_left"] < 0, "cap_left"] = 0

        df_sc_out = pd.concat([df_sc_out, df_sc_sorted], sort=False)

    if df_cap_chk is not None:
        final_year = years[-1]
        check_reeds_to_rev(
            df_sc_sorted,
            df_new_and_preexisting_investments,
            df_refurbishments,
            df_ret,
            df_cap_chk,
            final_year,
        )

    return df_sc_out


def check_reeds_to_rev(
    df_sc_sorted_final_year,
    df_new_and_preexisting_investments,
    df_refurbishments,
    df_ret,
    df_cap_chk,
    final_year,
):
    """
    Helper function for disaggregate_reeds_to_rev(). Validates the results of
    disaggregation to evaluate consistency with aggregate capacity in the final model
    year. This is a soft check that simply logs information -- no errors are raised if
    values do not meet certain thresholds.

    Parameters
    ----------
    df_sc_sorted_final_year : pandas.DataFrame
        Results of disaggregation in the final year. Each row represents a reV supply
        curve project site for the final year. Columns describe input information about
        the project site and capacity deployed to that project site. Output columns
        include input attributes (["sc_gid", "sc_point_gid", "latitude", "longitude",
        "region", "class", "bin", "cap_avail", "supply_curve_cost_per_mw"]) and outputs
        from disaggregation (["cap_expand", "cap_left", "cap", "inv_rsc", "ret",
        "refurb", "expanded", "year"]).
    df_new_and_preexisting_investments : pandas.DataFrame
        Defines the new and pre-existing deployments of capacity by year, region, class,
        and resource bin. Columns include: ["year", "region", "class", "bin", "MW"].
    df_refurbishments : pandas.DataFrame
        Defines the refurbishments of capacity by year, region, and class.
        Columns include: ["year", "region", "class", "MW"].
    df_ret : pandas.DataFrame
        Defines the retirements of capacity by year, region, and class.
        Columns include: ["year", "region", "class", "MW"].
    df_cap_chk : pandas.DataFrame
        Defines the aggregate capacity by year, region and class.
        Columns include: ["year", "region", "class", "MW"]. Used for a soft check of
        the disaggregation results. If ``None``, the soft check will not be performed.
    final_year : int
        Final model year. Typically 2050.
    """
    cap_fin_df_sc = df_sc_sorted_final_year["cap"].sum()
    inv_rsc_cum = df_new_and_preexisting_investments["MW"].sum()
    inv_refurb_cum = df_refurbishments["MW"].sum()
    ret_cum = df_ret["MW"].sum()
    cap_fin_calc = inv_rsc_cum + inv_refurb_cum - ret_cum
    cap_csv_fin = df_cap_chk[df_cap_chk["year"] == final_year]["MW"].sum()

    logger.info("Final Capacity check (MW):")
    logger.info(f"Final cap in df_sc: {cap_fin_df_sc}")
    logger.info(f"Final cap.csv: {cap_csv_fin}")
    logger.info(f"Difference (error): {cap_fin_df_sc - cap_csv_fin}")
    logger.info(
        f"Calculated capacity from investment and retirement input: {cap_fin_calc}"
    )
    logger.info(f"Cumulative inv_rsc: {inv_rsc_cum}")
    logger.info(f"Cumulative retirements: {ret_cum}")
    logger.info(f"Cumulative inv_refurb: {inv_refurb_cum}")


def format_outputs(reeds_to_rev_df, priority_cols, reduced_only=False):
    """
    Format DataFrame from overall ReEDS to reV process for outputting.

    Parameters
    ----------
    reeds_to_rev_df : pandas.DataFrame
        Output DataFrame from overall ReEDS to reV process. Typically should be the
        output of disaggregate_reeds_to_rev().
    priority_cols : list
        List of columns used in prioritization of the disaggregation.
    reduced_only : bool, optional
        If True, remove extra columns from DataFrame that do not fit the reduced
        format and will also remove any rows that do not have any built capacity.
        By default False, which will return all columns.

    Returns
    -------
    pandas.DataFrame
        Input DataFrame reformatted for output to CSV.
    """

    reeds_to_rev_df.rename(columns={"cap": "built_capacity"}, inplace=True)
    reeds_to_rev_df["investment_bool"] = 0
    has_investments = (reeds_to_rev_df["inv_rsc"] > 1e-3) | (
        reeds_to_rev_df["refurb"] > 1e-3
    )
    reeds_to_rev_df.loc[has_investments, "investment_bool"] = 1
    if not reduced_only:
        return reeds_to_rev_df

    reduced_cols = (
        [
            "year",
            "sc_gid",
            "sc_point_gid",
            "latitude",
            "longitude",
            "region",
            "class",
            "bin",
        ]
        + priority_cols
        + [
            "built_capacity",
            "investment_bool",
        ]
    )
    has_built_capacity = reeds_to_rev_df["built_capacity"] > 1e-3
    reeds_to_rev_w_builds_df = reeds_to_rev_df.loc[has_built_capacity, reduced_cols]

    return reeds_to_rev_w_builds_df


def save_outputs(out_df, out_dir_path, tech, reduced_only):
    """
    Saves output DataFrame from overall ReEDS to reV process to CSV with a standard
    file name.

    Parameters
    ----------
    out_df : pandas.DataFrame
        Output DataFrame from overall ReEDS to reV process. Typically should be the
        output of format_outputs().
    out_dir_path : pathlib.Path
        Path to the output directory where the CSV will be saved.
    tech : str
        Name of the technology that was run through ReEDs to rev. Expected values are:
        ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].
    reduced_only : bool
        If True, the output will be saved with a suffix of "_reduced". If False,
        this suffix will not be included in the output file name. Should correspond to
        whether or not the actual data are reduced format.
    """

    out_suffix = "_reduced" if reduced_only else ""
    out_csv = f"df_sc_out_{tech}{out_suffix}.csv"
    out_csv_path = out_dir_path.joinpath(out_csv)
    out_df.to_csv(out_csv_path, index=False)


def get_sc_file_path(row):
    """
    Helper function for get_supply_curve_info(). Builds the full file path for a given
    row of the (amended) supply curve metadata.

    For most technologies, the path is built dynamically from the attributes of the
    row. For DUPV and CSP, the path is built dynamically but the file name is
    hard-coded.

    Note that paths are not validated to ensure the supply curve file actually exists.

    Parameters
    ----------
    row : pandas.Series
        Input row from supply curve metadata DataFrame. Must contain the following
        attributes: "tech", "sc_path", "rev_case". Technically, a dictionary with these
        required keys could also be passed as input though that is not the standard use
        case.

    Returns
    -------
    str
        Returns the path to the supply curve dataset for the input row.
    """

    # Pre 2020 update, hdf5 files were used, with a different file structure
    # DUPV is special and somewhat janky on the reV side, so gets its own thing
    # DUPV profiles should be updated to be more consistent across reV and ReEDS

    # NOTE: use os.path.join rather than Path().joinpath() here because the latter
    #   cannot correctly handle the slash and backslash pattern in the row["sc_path"]
    #   and will mistakenly strip one of the leading backslashes from the fileserver
    #   path
    if row["tech"] == "dupv":
        sc_file = os.path.join(row["sc_path"], "dupv_sc_naris_scaled.csv")
    elif row.tech == "csp":
        sc_file = os.path.join(row["sc_path"], "vision_sn2_csp_conus_2012.h5")
    elif row.tech == "wind-ofs":
        sc_file = os.path.join(
            row["sc_path"],
            f"{row['tech']}_{row['rev_case']}",
            "results",
            f"{row['tech']}_supply_curve_raw.csv",
        )
    else:
        sc_file = os.path.join(
            row["sc_path"],
            f"{row['tech']}_{row['access_case']}",
            "results",
            f"{row['tech']}_supply_curve_raw.csv",
        )

    return sc_file


def get_cost_col(tech, sc_file):
    """
    Identifies the standard name of the cost column used in the supply curve data
    for the given technology. Note that no validation or verification of the cost
    column is performed - it is identified based on hard-coded logic based on the
    technology and the file format of the supply curve data.

    Typically this function is used as a helper function for get_supply_curve_info().

    Parameters
    ----------
    tech : str
        Name of the technology for which to determine the cost columns.
        Allowable values are: ["upv", "wind-ofs", "wind-ons", "dupv", "csp"].
    sc_file : str
        Path to supply curve file. This is typically a full file path but just passing a
        filename will also work.

    Returns
    -------
    str
        Name of the cost column used in the supply curve for the given CSV.
    """

    # transmission cost column of supply curve data frame
    if tech in ["wind-ons", "wind-ofs", "upv"]:
        cost_col = "supply_curve_cost_per_mw"
    elif os.path.splitext(sc_file)[1] == ".csv":
        cost_col = "trans_cap_cost"
    elif os.path.splitext(sc_file)[1] == ".h5":
        cost_col = "cap_cost_transmission"

    return cost_col


def get_supply_curve_info(
    reeds_run_path, filter_tech=None, rev_case=None, sc_path=None, bins=None
):
    """
    Get information about supply curves to use in the analysis. Supply curve information
    is sourced from the inputs_case/supplycurve_metadata/rev_supply_curves.csv. It is
    amended based on the optional inputs and then the full supply curve paths are
    resolved and the cost column for each is identified.

    Parameters
    ----------
    reeds_run_path : pathlib.Path
        Path to the folder containing the ReEDS run of interest. This folder must
        contain the following file:
            `inputs_case/supplycurve_metadata/rev_supply_curves.csv`.
    filter_tech : str, optional
        Optional technology to run (e.g., `wind-ons`). If None, all applicable
        technologies will be run. Allowable values are: ["upv", "wind-ofs", "wind-ons",
        "dupv", "csp"].
    rev_case : str, optional
        Optional name of the rev_case, which is used to look up the actual supply curve
        files. If None, the rev_case in the supply curve metadata will be used.  Will
        have no effect if specified but filter_tech is None.
    sc_path : str, optional
        Optional path to supply curve files where the specified version resides. If not
        specified (i.e., None), the sc_path will in the supply curve metadata will
        be used. Will have no effect if specified but filter_tech is None.
    bins : int, optional
        Number of bins used in the supply curve bins. This has no effect, but is
        maintained for compatibility with legacy ReEDS to reV options.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing attributes about the supply curve source data for each
        applicable technology. Notably includes `sc_file` and `cost_col` attributes
        needed in downstream steps of ReEDS to reV.
    """

    source_path = reeds_run_path.joinpath(
        "inputs_case", "supplycurve_metadata", "rev_supply_curves.csv"
    )
    sc_info_df = pd.read_csv(source_path)

    if bins is not None:
        logger.warning("bins option is deprecated and has no effect.")

    if filter_tech is not None:
        filtered_sc_info_df = sc_info_df[sc_info_df["tech"] == filter_tech].copy()
        if rev_case is not None:
            filtered_sc_info_df["rev_case"] = rev_case
        if sc_path is not None:
            filtered_sc_info_df["sc_path"] = sc_path
    else:
        filtered_sc_info_df = sc_info_df
        if rev_case is not None:
            logger.warning(
                "rev_case specified but filter_tech is None. "
                "rev_case will have no effect."
            )
        if sc_path is not None:
            logger.warning(
                "sc_path specified but filter_tech is None. "
                "rev_case will have no effect."
            )

    filtered_sc_info_df["sc_file"] = filtered_sc_info_df.apply(get_sc_file_path, axis=1)
    filtered_sc_info_df["cost_col"] = filtered_sc_info_df.apply(
        lambda row: get_cost_col(row["tech"], row["sc_file"]), axis=1
    )

    return filtered_sc_info_df


def run(
    reeds_path,
    run_folder,
    priority,
    reduced_only,
    tech=None,
    bins=None,
    rev_case=None,
    sc_path=None,
):
    """
    Top-level function for running ReEDs to reV disaggregation. Includes the following
    functionalit steps:
    1. Get information about the supply curves to be used.
    2. Loop over each technology.
    3. Format and prepare data from supply curve and reeds results for running
        disaggregation.
    4. Run the disaggregation.
    5. Format and save outputs.

    Parameters
    ----------
    reeds_path : str
        Path to ReEDS directory. This should typically be the parent directory of the
        run_folder.
    run_folder : str
        Path to the folder containing the ReEDS run of interest. This folder is
        expected to contain `inputs_case` and `outputs` subfolders. Required files
        in this folder include:
            - inputs_case/supplycurve_metadata/rev_supply_curves.csv
            - inputs_case/maxage.csv
            - inputs_case/site_bin_map.csv
            - inputs_case/switches.csv
            - outputs/cap_new_bin_out.csv
            - outputs/cap_new_ivrt_refurb.csv
            - outputs/cap.csv
            - outputs/cap_exog.csv
            - outputs/systemcost.csv
    priority : str
        Priority option to use for disaggregation. The only priority option currently
        supported is "cost".
    reduced_only : bool
        If True, save a simpler/reduced format of outputs. If False, save full outputs.
    tech : str, optional
        Optional technology to run (e.g., `wind-ons`). If None, all applicable
        technologies will be run.  Allowable values are: ["upv", "wind-ofs", "wind-ons",
        "dupv", "csp"].
    bins : int, optional
        Number of bins used in the supply curve bins. This has no effect, but is
        maintained for compatibility with legacy ReEDS to reV options.
    rev_case : str, optional
        Optional name of the rev_case, which is used to look up the actual supply curve
        files. If None, the rev_case in the supply curve metadata will be used.  Will
        have no effect if specified but tech is None.
    sc_path : str, optional
        Optional path to supply curve files where the specified version resides. If not
        specified (i.e., None), the sc_path will in the supply curve metadata will
        be used. Will have no effect if specified but tech is None.

    Raises
    ------
    ValueError
        A ValueError will be raised if the input priority is not set to "cost".
    """

    logger.info("Starting reeds_to_rev")

    if priority != "cost":
        raise ValueError(
            f"Invalid input for priority: '{priority}'. "
            "The only allowable options are: ['cost']."
        )

    logger.info("Getting supply curve information")
    run_folder_path = Path(run_folder)
    sc_info_df = get_supply_curve_info(
        run_folder_path,
        filter_tech=tech,
        rev_case=rev_case,
        bins=bins,
        sc_path=sc_path,
    )

    logger.info("Creating output directory")
    out_dir_path = Path(run_folder).joinpath("outputs")
    out_dir_path.mkdir(exist_ok=True)

    logger.info("Adding log to output directory")
    add_filehandler(logger, out_dir_path)

    logger.info("Copying source code to output directory")
    source_code_path = Path(__file__)
    shutil.copy(source_code_path, out_dir_path)

    # iterate over technologies
    for _, rev_row in sc_info_df.iterrows():
        try:
            sc_file = rev_row["sc_file"]
            cost_col = rev_row["cost_col"]
            tech = rev_row["tech"]

            logger.info(
                "Preparing required data to disaggregate built capacity "
                f"for {rev_row['tech']}."
            )
            reeds_to_rev_data = prepare_data(
                reeds_path, run_folder, sc_file, tech, priority_cols=[cost_col]
            )

            # Save a copy of the input supply curve to the output directory
            reeds_to_rev_data["df_sc_in"].to_csv(
                out_dir_path.joinpath(f"df_sc_in_{tech}.csv"), index=False
            )

            logger.info(
                f"Disaggregating built capacity to reV sites for {rev_row['tech']}"
            )

            disagg_df = disaggregate_reeds_to_rev(
                priority={cost_col: "ascending"}, **reeds_to_rev_data
            )

            logger.info(f"Formatting and saving output data for {tech}")
            df_sc_out = format_outputs(
                disagg_df, priority_cols=[cost_col], reduced_only=reduced_only
            )
            save_outputs(df_sc_out, out_dir_path, tech, reduced_only)

        except Exception:  # pylint: disable=broad-exception-caught
            logger.info(f"***Error for {rev_row.tech}...\n{traceback.format_exc()}")

    logger.info("Completed reeds_to_rev!")


def build_parser():
    """
    Build argument parser which can be used for parsing inputs provided by user at the
    command line.

    Returns
    -------
    argparse.ArgumentParser
        Argument parser for parsing user inputs from the command line.
    """
    # Argument inputs
    parser = argparse.ArgumentParser(
        description="Disaggregates ReEDS capacity to reV sites."
    )

    parser.add_argument("reeds_path", help="path to ReEDS directory")
    parser.add_argument("run_folder", help="Folder containing ReEDS run")
    parser.add_argument(
        "priority",
        default="cost",
        choices=["cost"],
        help="How to rank reV sites. "
        + "    cost = Assign capacity to supply curve points based on lowest cost",
    )
    parser.add_argument(
        "-r",
        "--reduced_only",
        action="store_true",
        help="Switch if you only want the reduced outputs",
    )

    # these arguments are typically only passed when debugging
    # as a standalone script for a single tech
    parser.add_argument(
        "-t",
        "--tech",
        default=None,
        help="technology to get supply curve data for",
        choices=VALID_TECHS,
    )
    parser.add_argument(
        "-b",
        "--bins",
        default=None,
        help=(
            "Number of bins used.  This has no effect, but is maintained for "
            "compatibility with legacy ReEDS to reV inputs."
        ),
    )
    parser.add_argument(
        "--rev_case",
        default=None,
        help="Which version of data to use. Default uses "
        + "most updated data available for each type. Note that"
        + "the script will fill in tech and bin information, so"
        + "this only needs to be the rev scenario name",
    )
    parser.add_argument(
        "--sc_path",
        default=None,
        help="Path to supply curve files where the specified version"
        + " resides. Does not need to be specified if the path is the same"
        + " as the current default.",
    )

    return parser


def main():
    """
    Runs legacy ReEDS to reV command line interface
    """
    parser = build_parser()
    args = parser.parse_args()
    run(**args.__dict__)


setup_logger(logger, logging.DEBUG)

if __name__ == "__main__":
    logger.info("Resource logger setup.")
    main()
