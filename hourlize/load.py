### Converts EER hourly, state- and subsector-level load profiles to ReEDS
### inputs, allowing replacement of specified sectors with other data sources.
import argparse
from collections import OrderedDict
import datetime
import json
import numpy as np
import os
import pandas as pd
import site
from types import SimpleNamespace

def get_state_name_code_map(reeds_path: str) -> dict:
    """
    Read from the ReEDS directory a file containing the mapping from state
    names to codes for states in the contiguous U.S and convert it to a
    dictionary. For consistency with EER load profiles and with ReEDS,
    Washington D.C. is manually added to the mapping and mapped to
    Maryland's state code (MD).
    
    Args:
        reeds_path: Path to ReEDS directory.    

    Returns:
        dict
    """
    state_codes = pd.read_csv(
        os.path.join(
            reeds_path,
            'postprocessing',
            'bokehpivot',
            'in',
            'state_code.csv'
        )
    )
    state_name_code_map = dict(zip(
        state_codes['State'].str.lower(),
        state_codes['Code'].str.upper()
    ))
    state_name_code_map['district of columbia'] = 'MD'

    return state_name_code_map

def roll_hourly_data(
    df: pd.DataFrame,
    input_timezone: str,
    output_timezone: str
) -> pd.DataFrame:
    """
    Perform timezone shift to convert hourly data in the provided dataframe
    from 'input_timezone' to 'output_timezone'.
    
    Args:
        df: Dataframe containing hourly data.
        input_timezone: Timezone of the hourly data in "df". Should be
            formatted as "Etc/GMT+[number]" (e.g., Etc/GMT+6 for CST).
        output_timezone: Timezone of the output dataframe. Should be
            formatted as "Etc/GMT+[number]" (e.g., Etc/GMT+6 for CST).

    Returns:
        pd.DataFrame
    """
    #Extract the integer adjustment from UTC for source and output timezones
    source_tz_num = -1 * int(input_timezone.replace('Etc/GMT', ''))
    output_tz_num = -1 * int(output_timezone.replace('Etc/GMT', ''))
    #Shift timezone of hourly data
    shift = output_tz_num - source_tz_num
    if shift != 0:
        for col in df:
            df[col] = np.roll(df[col], shift)

    return df

def remove_sectoral_load(
    df_load: pd.DataFrame,
    sector_subsector_mapping: dict,
    replace_states: list[str],
    replacement_share: dict,
    model_year: int
) -> pd.DataFrame:
    """
    Remove load for the specified subsectors and states in the specified
    model year and according to the replacement share (percentage of
    endogenous sectoral load that should be replaced with exogenous load)
    for that year.
    
    Args:
        df_load: Hourly, state- and subsector-level load profiles.
        sector_subsector_mapping: Mapping between sectors and subsectors.
            Dictionary keys are sectors, and dictionary values are lists
            of subsectors.
        replace_states: List of states in the contiguous U.S. (or "all" to
            represent all CONUS states) whose sectoral load (using sectors
            specified in 'replace_sectors') should be replaced.
        replacement_share: The percentage (specified as a number from 0 to 1)
            of endogenous sectoral load (using sectors specified in
            'replace_sectors') that should be removed in each model year
            before adding exogenous sectoral load. Dictionary keys are
            the model years and dictionary values are the percentages.
        model_year: Model year for which sectoral load should be removed.

    Returns:
        pd.DataFrame
    """
    for sector, subsectors in sector_subsector_mapping.items():
        sector_mask = (
            (df_load['sector'] == sector)
            & (df_load['subsector'].isin(subsectors))
        )
        df_load.loc[sector_mask, replace_states] *= (
            1 - float(replacement_share[model_year])
        )

    return df_load

def aggregate_legacy_bas_to_states(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate a dataframe whose columns are legacy BAs to the state level
    using the legacy BA-to-state mapping file specified in the hourlize config.

    Args:
        df: Dataframe to aggregate.

    Returns:
        pd.DataFrame
    """
    legacy_ba_state_map = (
        pd.read_csv(cf.legacy_ba_state_map_file, index_col='ba')
        ['st']
    )
    df.columns = df.columns.map(legacy_ba_state_map)
    df = df.T.groupby(df.columns).sum().T

    return df

def get_sectoral_replacement_load(
    sector: str,
    sector_config: dict,
    model_year: int | None = None
) -> pd.DataFrame:
    """
    Get hourly, state-level load profiles for the specified sector and model
    year. The sector must have an entry in the provided sector config.

    Args:
        sector: Sector for which to retrieve exogenous load (using information
            specified in 'sector_config').
        sector_config: Configuration defining the subsectors of each
            sector, the model years for which sectoral load should be
            replaced, and information concerning the files containing
            exogenous sectoral load. For the expected format, see
            'hourlize/inputs/load/sector_config.json'.
        model_year: Model year for which exogenous sectoral load should be
            retrieved. Currently only relevant to the Transportation sector.

    Returns:
        pd.DataFrame
    """
    # Get information for the specified sector from the sector config
    sector_settings = sector_config[sector]

    # Read the file(s) containing exogenous sectoral load and
    # concatenate the results if there are multiple
    if sector == 'Transportation':
        df_list = []
        for fpath in sector_settings['filepaths']:
            df = pd.read_csv(
                fpath.format(model_year=model_year),
                index_col='datetime'
            )
    else:
        df_list = [
            pd.read_csv(fpath, index_col=0)
            for fpath
            in sector_settings['filepaths']
        ]
    df_load_replace = pd.concat(df_list).groupby(level=0).sum()

    # Multiply by the unit conversion factor to get load in MWh
    df_load_replace *= sector_settings['unit_conversion_factor']

    # Apply timezone shifts for consistency with the input load source
    # timezone specified in the hourlize config
    if sector_settings['timezone'] == 'local':
        if sector_settings['regional_scope'] == 'legacy_ba':
            legacy_ba_timezone_map = (
                pd.read_csv(cf.legacy_ba_timezone_file, index_col=0)
                ['timezone']
            )
            load_source_tz_num = (
                -1 * int(cf.load_source_timezone.replace('Etc/GMT', ''))
            )
            for ba in df.columns:
                df[ba] = np.roll(
                    df[ba],
                    load_source_tz_num - legacy_ba_timezone_map[ba]
                )
        else:
            raise NotImplementedError(
                "Converting from local timezones is only supported when "
                "the regional scope of the exogenous load source is "
                "'legacy_ba'."
            )
    else:
        df_load_replace = roll_hourly_data(
            df_load_replace,
            sector_settings['timezone'],
            cf.load_source_timezone
        )

    # If applicable, aggregate legacy BA profiles to the state level 
    if sector_settings['regional_scope'] == 'legacy_ba':
        df_load_replace = aggregate_legacy_bas_to_states(df_load_replace)

    return df_load_replace


def create_hourly_state_load_for_model_year(
    load_source_path: str,
    scenario: str,
    weather_years: list[int],
    model_year: int,
    output_fpath: str,
    state_name_code_map: dict,
    replace_sectors: list[str] = [],
    replace_states: list[str] | str = [],
    replacement_share: dict = {},
    sector_config: dict = {}
) -> None:
    """
    Create hourly, state-level load profiles for the specified load scenario,
    model year, and weather years and write them to the provided filepath.
    
    Args:
        load_source_path: Path to directory containing raw hourly, state- and
            subsector-level load profiles.
        scenario: Load scenario from 'load_source_path'.
        weather_years: List of weather years to include in exported
            load profiles.
        model_year: Model year to include in exported load profiles.
        output_fpath: File path to export load profiles to.
        state_name_code_map: Mapping from U.S. state names (in lowercase and
        including Washington D.C.) to their state codes. For consistency with
        ReEDS, Washington D.C. should be mapped to Maryland's state code (MD).
        replace_sectors: List of sectors for which endogenous (with respect to
            'load_source_path') sectoral load should be replaced with load
            from external load sources.
        replace_states: List of states in the contiguous U.S. (or "all" to
            represent all CONUS states) whose sectoral load (using sectors
            specified in 'replace_sectors') should be replaced.
        replacement_share: The percentage (specified as a number from 0 to 1)
            of endogenous sectoral load (using sectors specified in
            'replace_sectors') that should be removed in each model year
            before adding exogenous sectoral load. Dictionary keys are
            the model years and dictionary values are the percentages.
        sector_config: Configuration defining the subsectors of each
            sector, the model years for which sectoral load should be
            replaced, and information concerning the files containing
            exogenous sectoral load. For the expected format, see
            'hourlize/inputs/load/sector_config.json'.

    Returns:
        None
    """
    print(f"Creating load profile for model year {model_year}...")
    # Read raw hourly, state- and subsector-level load profiles
    df_load = pd.read_csv(
        f'{load_source_path}/{scenario}/{model_year}.csv.gz',
        compression='gzip',
        parse_dates=['weather_datetime']
    )
    # Downselect to specified weather years
    df_load = df_load.loc[df_load.weather_datetime.dt.year.isin(weather_years)]

    # If 'replace_states' is specified as "all", get all of the state names from
    # the provided state name-to-code mapping
    if replace_states == 'all':
        replace_states = [
            state for state in state_name_code_map.keys() if state in df_load.columns
        ]

    # For each sector specified in 'replace_sectors', remove endogenous
    # sectoral load from the raw load profiles
    replacement_load_list = []
    for sector in replace_sectors:
        print(f"Removing endogenous load for '{sector}' sector...")
        if sector not in sector_config:
            raise NotImplementedError(
                f"'{sector}' is not a recognized sector. "
                "Update 'hourlize/inputs/load/sector_config.json'."
            )

        sector_settings = sector_config[sector]
        if model_year in sector_settings['model_years']:
            df_load = remove_sectoral_load(
                df_load,
                sector_settings['subsectors'],
                replace_states,
                replacement_share,
                model_year
            )
        else:
            pass

    # Aggregate load across sectors to create state-level profiles
    df_load = (
        df_load.groupby(by=['weather_datetime'], sort=False, as_index=False)
        .sum(numeric_only=True)
        .rename(columns={'weather_datetime': 'datetime'})
    )

    # Apply a timezone shift to the profiles according to the input
    # and output timezones specified in the hourlize config
    df_load = (
        df_load.groupby(df_load['datetime'].dt.year, as_index=False)
        .apply(
            lambda x: roll_hourly_data(
                x,
                cf.load_source_timezone,
                cf.output_timezone
            )
        )
        .set_index('datetime')
        .tz_localize(tz=cf.output_timezone)
    )

    # Rename the columns to use state codes instead of state names
    # and take the sum of columns with the same name (needed because both
    # Washington D.C. and Maryland are mapped to the "MD" state code)
    df_load.columns = df_load.columns.map(state_name_code_map)
    df_load = df_load.drop(columns=['AK', 'HI'])
    df_load = df_load.T.groupby(df_load.columns).sum().T

    # Take only the first 8760 hours of each weather year (needed for
    # consistency with ReEDS) and round each value to the nearest whole number
    df_load = (
        df_load.groupby(df_load.index.get_level_values('datetime').year)
        .head(8760)
        .round(0)
        .astype(int)
    )

    # Read exogenous load files for the sectors specified in 'replace_sectors'
    replacement_load_list = [
        get_sectoral_replacement_load(
            sector,
            sector_config,
            model_year
        )
        for sector in replace_sectors
    ]

    # Aggregate the exogenous sectoral load to the state level and
    # add the result to each weather year of the load profiles
    if len(replacement_load_list) > 0:
        print("Adding exogenous sectoral load...")
        df_load_replace = pd.concat(replacement_load_list).groupby(level=0).sum()
        for weather_year in weather_years:
            weather_year_mask = (
                df_load.index.get_level_values('datetime').year == weather_year
            )
            df_load.loc[weather_year_mask] = (
                df_load.loc[weather_year_mask].add(
                    df_load_replace.set_index(
                        df_load.loc[weather_year_mask].index
                    )
                )
            )

    # Export the resulting profiles to the provided output filepath
    reeds.io.write_to_h5(
        dfwrite=df_load.reset_index(),
        key=str(model_year),
        filepath=output_fpath,
        attrs={'index': 'datetime'},
        overwrite=True,
        compression='gzip',
        compression_opts=4
    )

    return


def main(
    reeds_path: str,
    load_source_path: str,
    scenarios: list[str],
    weather_years: list[int],
    model_years: list[int],
    replace_sectors: list[str] = [],
    replace_states: list[str] | str = [],
    replacement_share: dict = {},
    sector_config: dict = {}
) -> None:
    """
    Create hourly, state-level load profiles for the specified model years
    and weather years and write them to the 'inputs/load' folder of the
    provided ReEDS directory.
    
    Args:
        reeds_path: Path to ReEDS directory.
        load_source_path: Path to directory containing raw hourly, state- and
            subsector-level load profiles.
        scenarios: List of load scenarios (of those listed as subdirectories
            in 'load_source_path') to include in exported load profiles.
        weather_years: List of weather years to include in exported
            load profiles.
        model_years: List of model years to include in exported load profiles.
        replace_sectors: List of sectors for which endogenous (with respect to
            'load_source_path') sectoral load should be replaced with load
            from external load sources.
        replace_states: List of states in the contiguous U.S. (or "all" to
            represent all CONUS states) whose sectoral load (using sectors
            specified in 'replace_sectors') should be replaced.
        replacement_share: The percentage (specified as a number from 0 to 1)
            of endogenous sectoral load (using sectors specified in
            'replace_sectors') that should be removed in each model year
            before adding exogenous sectoral load. Dictionary keys are
            the model years and dictionary values are the percentages.
        sector_config: Configuration defining the subsectors of each
            sector, the model years for which sectoral load should be
            replaced, and information concerning the files containing
            exogenous sectoral load. For the expected format, see
            'hourlize/inputs/load/sector_config.json'.

    Returns:
        None
    """
    scenario_outfile_prefix_map = {
        'IRA cons': 'EER_IRAlow',
        'central': 'EER_100by2050',
        'baseline': 'EER_Baseline_AEO2023'
    }
    valid_scenarios = list(scenario_outfile_prefix_map.keys())
    state_name_code_map = get_state_name_code_map(reeds_path)

    for scenario in scenarios:
        print(f"Processing load scenario {scenario}...")
        if scenario not in valid_scenarios:
            raise NotImplementedError(
                f"{scenario} is not a valid load scenario. "
                f"Choose from {valid_scenarios}."
            )

        output_fpath = os.path.join(
            reeds_path,
            "inputs",
            "load",
            f"{scenario_outfile_prefix_map[scenario]}_load_hourly.h5"
        )
        for model_year in model_years:
            create_hourly_state_load_for_model_year(
                load_source_path,
                scenario,
                weather_years,
                model_year,
                output_fpath,
                state_name_code_map,
                replace_sectors,
                replace_states,
                replacement_share,
                sector_config
            )
    
    return


if __name__== '__main__':
    #%% load arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        '-c',
        type=str,
        default='',
        help='path to config file for this run'
    )
    args = parser.parse_args()
    configpath = args.config
    startTime = datetime.datetime.now()

    #%% load config information
    with open(configpath, "r") as f:
        config = json.load(f, object_pairs_hook=OrderedDict)
    cf = SimpleNamespace(**config)

    #%% setup logging
    site.addsitedir(cf.reeds_path)
    import reeds
    from reeds.log import makelog

    makelog(
        scriptname=__file__,
        logpath=os.path.join(cf.outpath, f'log_{cf.casename}.txt')
    )

    with open(cf.sector_config_file, "r") as f:
        sector_config = json.load(f)    

    cf.replacement_share = {
        int(k): v for k,v in dict(cf.replacement_share).items()
    }
    main(
        cf.reeds_path,
        cf.load_source,
        cf.scenarios,
        cf.weather_years,
        cf.model_years,
        cf.replace_sectors,
        cf.replace_states,
        cf.replacement_share,
        sector_config
    )
    print('All done! total time: '+ str(datetime.datetime.now() - startTime))