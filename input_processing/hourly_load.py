'''
This script handles the modification of load data. Specifically, it converts
state-level hourly end-use load to model region-level busbar load by doing
the following:

- Allocate state load to model regions according to the method specified
    in GSw_LoadAllocationMethod
- Apply scenario-specific modifications:
    EER scenarios:
    - Append historical load for pre-2021 model years
    - Interpolate projected load for missing model years
    - Apply calibration factors to projected load based on the difference
        between historical and projected load in the latest year for which
        historical and projected load data exist
    Historical:
    - Apply annual load growth factors
    Other:
    - If needed, replicate the dataset to match the number of weather years
        specified for this run
- Apply a distribution loss factor

The script also calculates peak load for each region level.
'''

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import datetime
import numpy as np
import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def get_historical_state_load_for_model_year(
    historical_state_load_annual: pd.DataFrame,
    model_year: int
) -> pd.Series:
    """
    Get historical annual state loads in MWh for the model year.
    
    Args:
        historical_state_load_annual: Annual historical state loads in MWh.
        model_year: Year to retrieve load values for.

    Returns:
        pd.Series
    """
    return (
        historical_state_load_annual
        .loc[historical_state_load_annual.year == model_year]
        .set_index('st')
        ['MWh']
    )

def scale_historical_hourly_state_load_to_model_year(
    historical_state_load_hourly: pd.DataFrame,
    historical_state_load_annual: pd.DataFrame,
    model_year: int
) -> pd.DataFrame:
    """
    Scale historical hourly state load profiles to match historical
    annual totals for the specified model year.
    
    Args:
        historical_state_load_hourly: Hourly historical state load profiles
            in MWh.
        historical_state_load_annual: Annual historical state loads in MWh.
        model_year: Year of annual load to scale hourly load by.

    Returns:
        pd.DataFrame
    """
    historical_model_year_state_load = get_historical_state_load_for_model_year(
        historical_state_load_annual,
        model_year
    )
    # Calculate total state loads for each weather year
    # of the historical hourly state load profiles
    historical_weather_year_state_loads = (
        historical_state_load_hourly.groupby(
            historical_state_load_hourly.index.get_level_values('datetime').year
        )
        .transform('sum')
    )
    # Scale the historical hourly state load profiles so that total state
    # loads for each weather year match state loads for the model year
    historical_state_load_hourly_scaled = (
        historical_state_load_hourly
        / historical_weather_year_state_loads
        * historical_model_year_state_load
    )

    return historical_state_load_hourly_scaled

def interpolate_missing_model_years(
    load_hourly: pd.DataFrame,
    endyear: int
) -> pd.DataFrame:
    """
    Linearly interpolate hourly load values for missing model years between
    the first year of the load profiles and the specified end year.
    
    Args:
        load_hourly: Hourly load profiles.
        endyear: Final model year of resulting load profiles.

    Returns:
        pd.DataFrame
    """
    model_years = [
        year for year in
        range(load_hourly.index.get_level_values('year').min(), endyear + 1)
    ]
    known_model_years = [
        year for year in
        model_years if year in load_hourly.index.get_level_values('year')
    ]

    dictload = {}
    for model_year in model_years:
        #find known years that bound this year
        for i, known_model_year in enumerate(known_model_years):
            if(known_model_year > model_year):
                section_end_model_year = known_model_year
                section_start_model_year = known_model_years[i-1]
                break
        
        #grab dataframes for linear interpolation
        df_load_beg = load_hourly.loc[section_start_model_year]
        df_load_end = load_hourly.loc[section_end_model_year]
        
        #linear interpolation:
        # y = y1 + (y2-y1)/(x2-x1)*(x-x1). x is year; y is value
        df_load = (
            df_load_beg +
            (df_load_end - df_load_beg)
            / (section_end_model_year - section_start_model_year)
            * (model_year-section_start_model_year)
        )

        dictload[model_year] = df_load

    load_hourly = pd.concat(dictload, names=('year',))

    return load_hourly

def calibrate_hourly_state_load_to_historical_annuals(
    state_load_hourly: pd.DataFrame,
    historical_state_load_annual: pd.DataFrame
) -> pd.DataFrame:
    """
    For historical model years, scale hourly state load profiles to match
    historical annual totals. For post-historical model years, scale hourly
    state load profiles to increase the projected annual totals by the
    difference between historical and projected annual totals for the
    latest historical model year.
    
    Args:
        state_load_hourly: Hourly state load profiles in MWh.
        historical_state_load_annual: Annual historical state loads in MWh.

    Returns:
        pd.DataFrame
    """
    df_list = []

    # For the model years for which we have historical annual loads, scale
    # state_load_hourly so that its annual totals match each model year's
    # historical annual loads
    min_projected_model_year = (
        state_load_hourly.index.get_level_values('year').min()
    )
    max_historical_model_year = historical_state_load_annual['year'].max()
    for model_year in range(
        min_projected_model_year,
        max_historical_model_year + 1
    ):
        model_year_historical_load = get_historical_state_load_for_model_year(
            historical_state_load_annual,
            model_year
        )
        state_load_hourly_model_year = (
            state_load_hourly
            .loc[(
                state_load_hourly.index.get_level_values('year') == model_year
            )]
            .copy()
        )
        calibration_factors = model_year_historical_load.div(
            state_load_hourly_model_year
            .groupby(
                state_load_hourly_model_year.index
                .get_level_values('datetime')
                .year
            )
            .transform('sum')
        )
        state_load_hourly_model_year_scaled = (
            state_load_hourly_model_year.mul(calibration_factors)
        )
        df_list.append(state_load_hourly_model_year_scaled)

    # For the latest model year for which we have historical annual loads
    # (the calibration year), calculate the differences between
    # the historical annual loads and projected annual loads
    calibration_year_historical_load = (
        get_historical_state_load_for_model_year(
            historical_state_load_annual,
            max_historical_model_year
        )
    )
    state_load_hourly_calibration_year = (
        state_load_hourly.loc[max_historical_model_year]
    )
    calibration_diffs = calibration_year_historical_load.sub(
        state_load_hourly_calibration_year
        .groupby(
            state_load_hourly_calibration_year.index
            .get_level_values('datetime')
            .year
        )
        .transform('sum')
    )

    # For post-historical model years, scale state_load_hourly so that its
    # annual totals match the sum of each model year's projected annual loads
    # and the historical/projected load differences in the calibration year
    max_projected_model_year = (
        state_load_hourly.index.get_level_values('year').max()
    )
    for model_year in range(
        max_historical_model_year + 1,
        max_projected_model_year + 1
    ):
        state_load_hourly_model_year = state_load_hourly.loc[model_year]
        model_year_projected_load = (
            state_load_hourly_model_year
            .groupby(
                state_load_hourly_model_year.index
                .get_level_values('datetime')
                .year
            )
            .transform('sum')
        )
        calibration_factors = (
            model_year_projected_load.add(calibration_diffs)
            .div(model_year_projected_load)
        )
        state_load_hourly_model_year_scaled = (
            state_load_hourly_model_year
            .mul(calibration_factors)
            .assign(year=model_year)
            .set_index('year', append=True)
            .reorder_levels(['year', 'datetime'])
        )
        df_list.append(state_load_hourly_model_year_scaled)
    
    state_load_hourly = pd.concat(df_list)

    return state_load_hourly

def prepend_historical_hourly_state_load(
    state_load_hourly: pd.DataFrame,
    historical_state_load_hourly: pd.DataFrame,
    historical_state_load_annual: pd.DataFrame
) -> pd.DataFrame:
    """
    Create hourly state load profiles for historical model years and
    prepend them to state_load_hourly.
    
    Args:
        state_load_hourly: Hourly state load profiles in MWh.
        historical_state_load_hourly: Hourly historical state load profiles
            in MWh.
        historical_state_load_annual: Annual historical state loads in MWh.

    Returns:
        pd.DataFrame
    """
    historical_load_dict = {}
    
    # For historical model years with no projected load profiles, create load
    # profiles for each model year by scaling the historical load profiles to
    # match annual totals for the model year
    min_historical_model_year = historical_state_load_annual['year'].min()
    min_projected_model_year = (
        state_load_hourly.index.get_level_values('year').min()
    )
    for model_year in range(
        min_historical_model_year, min_projected_model_year
    ):
        historical_state_load_hourly_scaled = (
            scale_historical_hourly_state_load_to_model_year(
                historical_state_load_hourly,
                historical_state_load_annual,
                model_year
            )
        )
        historical_load_dict[model_year] = historical_state_load_hourly_scaled

    historical_state_load_hourly = pd.concat(
        historical_load_dict,
        names=('year',)
    )
    state_load_hourly = pd.concat([
        historical_state_load_hourly,
        state_load_hourly
    ])

    return state_load_hourly

def apply_load_growth_factors_to_historical_state_load(
    historical_state_load_hourly: pd.DataFrame,
    historical_state_load_annual: pd.DataFrame,
    inputs_case: str,
    solveyears: list[int] | None = None
) -> pd.DataFrame:
    """
    Multiply hourly historical load profiles (scaled to match historical
    annual totals for a baseline year) by annual load growth factors to
    create projected load profiles for each model year.
    
    Args:
        historical_state_load_hourly: Hourly historical state load
            profiles in MWh.
        historical_state_load_annual: Annual state loads in MWh
            for historical years.
        inputs_case: Path to the inputs case directory.
        solveyears: Optional list of model years to filter load
            multipliers down to.

    Returns:
        pd.DataFrame
    """
    # Read annual state multipliers representing projected load growth
    # from a baseline year
    load_multiplier = pd.read_csv(
        os.path.join(inputs_case, 'load_multiplier.csv')
    )
    # Scale the historical load profiles to match annual totals
    # for the baseline year
    load_multiplier_baseline_year = load_multiplier['year'].min()
    historical_state_load_hourly = (
        scale_historical_hourly_state_load_to_model_year(
            historical_state_load_hourly,
            historical_state_load_annual,
            load_multiplier_baseline_year
        )
    )
    # Subset load multipliers for solve years only 
    if solveyears is not None:
        load_multiplier = (
            load_multiplier[load_multiplier['year'].isin(solveyears)]
            [['year', 'r', 'multiplier']]
        )
    # Reformat hourly load profiles to merge with load multipliers
    historical_state_load_hourly.reset_index(drop=False, inplace=True)
    historical_state_load_hourly = pd.melt(
        historical_state_load_hourly,
        id_vars=['datetime'],
        var_name='r',
        value_name='load'
    )
    # Merge load multipliers into hourly load profiles
    state_load_hourly = historical_state_load_hourly.merge(
        load_multiplier,
        on=['r'],
        how='outer'
    )
    state_load_hourly.sort_values(
        by=['r', 'year'],
        ascending=True,
        inplace=True
    )
    state_load_hourly['load'] *= state_load_hourly['multiplier']
    state_load_hourly = state_load_hourly[['year', 'datetime', 'r', 'load']]
    # Reformat hourly load profiles for GAMS
    state_load_hourly = state_load_hourly.pivot_table(
        index=['year', 'datetime'], columns='r', values='load')
    # Convert 'year' index to integers
    state_load_hourly.index = (
        state_load_hourly.index
        .set_levels(
            [
                state_load_hourly.index.levels[0].astype(int),
                state_load_hourly.index.levels[1]
            ],
            level=['year', 'datetime']
        )
    )
    
    return state_load_hourly

def downselect_to_model_years(
    load_hourly: pd.DataFrame,
    model_years: list[int]
) -> pd.DataFrame:
    """
    Retrieve the subset of hourly load profiles corresponding
    to the given model years.
    
    Args:
        load_hourly: Hourly load profiles.
        model_years: List of model years used to filter load_hourly.
            These years should correspond to load_hourly's "year"
            index level.

    Returns:
        pd.DataFrame
    """
    return (
        load_hourly.loc[(
            load_hourly.index
            .get_level_values('year')
            .isin(model_years)
        )]
    )

def downselect_to_weather_years(
    load_hourly: pd.DataFrame,
    weather_years: list[int]
) -> pd.DataFrame:
    """
    Retrieve the subset of hourly load profiles corresponding
    to the given weather years.
    
    Args:
        load_hourly: Hourly load profiles.
        weather_years: List of weather years used to filter load_hourly.
            These years should correspond to the years of load_hourly's
            "datetime" index level.

    Returns:
        pd.DataFrame
    """
    return (
        load_hourly.loc[(
            load_hourly.index
            .get_level_values('datetime')
            .year
            .isin(weather_years)
        )]
    )

def duplicate_weather_years(load_hourly, weather_years):
    """
    Replicate hourly load profiles to match the number of weather years.
    
    Args:
        load_hourly: Hourly load profiles with only one weather year of data.
        weather_years: List of weather years to replicate load profiles for.

    Returns:
        pd.DataFrame
    """
    # Copy the load profiles n times for the number of weather years and
    # concatenate them
    num_years = len(weather_years)
    load_hourly_wide = load_hourly.unstack('year')

    if len(load_hourly_wide) != 8760:
        raise ValueError(
            "The provided dataframe has more than one weather year of data."
        )

    load_hourly = (
        pd.concat([load_hourly_wide] * num_years, axis=0, ignore_index=True)
        .rename_axis('hour').stack('year')
        .reorder_levels(['year','hour']).sort_index(axis=0, level=['year','hour'])
    )
    # Update the time index of the concatenated load profile to contain
    # the hours of each weather year
    fulltimeindex = pd.Series(reeds.timeseries.get_timeindex(weather_years))
    load_hourly['datetime'] = (
        load_hourly.index.get_level_values('hour').map(fulltimeindex)
    )
    load_hourly = load_hourly.set_index('datetime', append=True).droplevel('hour')

    return load_hourly

def apply_regional_load_adjustments(
    regional_load_hourly: pd.DataFrame,
    inputs_case: str, 
    GSw_LoadAdjust_Profiles: str,
    GSw_LoadAdjust_Adoption: str
) -> pd.DataFrame:
    """
    Adjust hourly regional load profiles by adding hourly regional
    load adjustment profiles, weighted by annual adoption rates.
    
    Args:
        regional_load_hourly: Hourly regional load profiles in MWh.
        inputs_case: Path to the inputs case directory.
        GSw_LoadAdjust_Profiles: "__"-separated suffixes for files containing
            hourly regional load adjustment profiles in MWh.
        GSw_LoadAdjust_Adoption: "__"-separated suffixes for files containing
            annual adoption rates for load adjustment profiles.

    Returns:
        pd.DataFrame
    """
    # Splitting load adjustment profiles and adoption rates
    LoadAdjust_Profiles = GSw_LoadAdjust_Profiles.split("__")
    LoadAdjust_Adoption = GSw_LoadAdjust_Adoption.split("__")
    # Checking for an equal # of load adjustment profiles and adoption rates
    if len(LoadAdjust_Adoption) != len(LoadAdjust_Profiles):
        sys.exit(
            "Number of GSw load adjustment profiles does not equal the "
            "same number of adoption rate profiles"
        )
    # Creating a list of load profile years and regions
    regional_load_hourly_years = (
        regional_load_hourly.reset_index()
        .year
        .unique()
        .tolist()
    )
    regional_load_hourly_regions = regional_load_hourly.columns.tolist()
    # Creating a load profile with specified adoption rates
    for i in range(len(GSw_LoadAdjust_Profiles)):
        # Reading in the load adjustment profiles and adoption rates
        profile = pd.read_csv(
            os.path.join(
                inputs_case,
                f'ghp_delta_{GSw_LoadAdjust_Profiles[i]}.csv'
            )
        )
        adoption = pd.read_csv(
            os.path.join(
                inputs_case,
                f'adoption_trajectories_{GSw_LoadAdjust_Adoption[i]}.csv'
            )
        )
        # Drop Years from adoption rates that are not in load profiles
        adoption = adoption[adoption["year"].isin(regional_load_hourly_years)]
        # Reshape load adjustment profiles and adoption rates
        profile = pd.melt(
            profile, id_vars=["hour"], var_name="Regions", value_name="Amount"
        )
        adoption = pd.melt(
            adoption,
            id_vars=["year"],
            var_name="Regions",
            value_name="Adoption Rate",
        )
        # Merge adoption rates and load adjustment profiles on "Regions"
        adoption_by_profile = pd.merge(adoption, profile, on="Regions")

        # Calculate regional load adjustment (weighted by adoption rate)
        adoption_by_profile["Load Value"] = (
            adoption_by_profile["Adoption Rate"]
            * adoption_by_profile["Amount"]
        )
        #Drop unnecessary columns, filter regions, and create pivot table
        adoption_by_profile = adoption_by_profile.drop(
            columns=["Adoption Rate", "Amount"]
        )
        adoption_by_profile = adoption_by_profile[
            adoption_by_profile["Regions"].isin(regional_load_hourly_regions)
        ]
        adoption_by_profile = pd.pivot(
            adoption_by_profile,
            index=["year", "hour"],
            columns="Regions",
            values="Load Value",
        )
        # Shaping the data to match the 7-year VRE profiles
        adoption_by_profile_wide = adoption_by_profile.unstack("year")
        if len(adoption_by_profile_wide) == 8760:
            adoption_by_profile = (
                pd.concat(
                    [adoption_by_profile_wide] * 7,
                    axis=0,
                    ignore_index=True
                )
                .rename_axis("hour")
                .stack("year")
                .reorder_levels(["year", "hour"])
                .sort_index(axis=0, level=["year", "hour"])
            )
        # Adding the regional load adjustment to regional_load_hourly
        regional_load_hourly = pd.concat(
            [regional_load_hourly, adoption_by_profile]
        )
        regional_load_hourly = (
            regional_load_hourly.groupby(["year", "hour"])
            .sum()
        )

    return regional_load_hourly

def apply_distribution_loss_factor(
    load_hourly: pd.DataFrame,
    distloss: float = 0.05
) -> pd.DataFrame:
    """
    Adjust hourly end-use load profiles to account for energy
    lost during transmission and distribution.
    
    Args:
        load_hourly: Hourly load profiles.
        distloss: Percentage of busbar load lost during
            transmission and distribution.

    Returns:
        pd.DataFrame
    """
    return load_hourly / (1 - distloss)

def calculate_peak_load(
    load_hourly: pd.DataFrame,
    hierarchy: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate coincident peak demand at all region hierarchy levels.
    
    Args:
        load_hourly: Hourly load profiles.
        hierarchy: Model region hierarchy levels.

    Returns:
        pd.DataFrame
    """
    _peakload = {}
    for _level in hierarchy.columns:
        _peakload[_level] = (
            ## Aggregate to level
            load_hourly.rename(columns=hierarchy[_level])
            .groupby(axis=1, level=0).sum()
            ## Calculate peak
            .groupby(axis=0, level='year').max()
            .T
        )

    ## Also calculate it at r level
    _peakload['r'] = load_hourly.groupby(axis=0, level='year').max().T
    peakload = pd.concat(_peakload, names=['level','region']).round(3)

    return peakload

def reaggregate_to_model_regions(
    state_load_hourly: pd.DataFrame,
    inputs_case: str,
    GSw_LoadAllocationMethod: str
) -> pd.DataFrame:
    """
    Allocate hourly state load to model regions according to the provided
    load allocation method (e.g., according to each region's share of 
    state population).
    
    Args:
        state_load_hourly: Hourly state load profiles.
        inputs_case: Path to the inputs case directory.
        GSw_LoadAllocationMethod: Method by which to allocate state
            load to model regions.

    Returns:
        pd.DataFrame
    """
    # Get state/region-to-county disaggregation factors
    disagg_data = reeds.io.get_disagg_data(
        os.path.dirname(inputs_case),
        disagg_variable=GSw_LoadAllocationMethod
    )
    # Calculate state-to-region aggregation/disaggregation factors
    state_region_factors = (
        disagg_data.groupby(['state', 'r'], as_index=False)
        ['state_frac']
        .sum()
        .pivot(index='state', columns='r', values='state_frac')
        .rename_axis(None, axis=1)
        .fillna(0)
    )
    # Identify regions with aggregation/disaggregation factors of 0
    # and raise an error if any exist 
    if state_region_factors.sum().min() == 0:
        regional_factors = state_region_factors.sum()
        no_load_regions = (
            regional_factors.loc[regional_factors == 0].index.tolist()
        )
        raise ValueError(
            f"Load allocation method {GSw_LoadAllocationMethod} produced the "
            "following regions with 0 load. Update GSw_LoadAllocationMethod "
            "in your cases file:\n{}\n"
            .format('\n'.join(no_load_regions))
        )

    # Multiply the hourly state load profiles by the state-to-region factors
    regional_load_hourly = (
        state_load_hourly[state_region_factors.index]
        .dot(state_region_factors)
    )

    return regional_load_hourly


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================
def main(reeds_path, inputs_case):
    print('Starting hourly_load.py')

    #%%### Load inputs
    ### Load the input parameters
    sw = reeds.io.get_switches(inputs_case)
    weather_years = sw.resource_adequacy_years_list
    scalars = reeds.io.get_scalars(inputs_case)
    solveyears = reeds.io.get_years(os.path.dirname(inputs_case))
    hierarchy = reeds.io.get_hierarchy(os.path.dirname(inputs_case))

    #%%%#########################################
    #    -- Get load profiles --    #
    #############################################

    state_load_hourly = reeds.io.get_load_hourly(inputs_case)
    state_load_hourly = downselect_to_weather_years(
        state_load_hourly,
        weather_years
    )
    historical_state_load_annual = reeds.io.get_historical_state_load_annual()

    match sw.GSw_LoadProfiles:
        case _ if 'EER_' in sw.GSw_LoadProfiles:
            endyear = int(sw.endyear)
            state_load_hourly = interpolate_missing_model_years(
                state_load_hourly,
                endyear
            )
            state_load_hourly = (
                calibrate_hourly_state_load_to_historical_annuals(
                    state_load_hourly,
                    historical_state_load_annual
                )
            )
            historical_state_load_hourly = reeds.io.get_load_hourly(
                GSw_LoadProfiles='historic'
            )
            historical_state_load_hourly = downselect_to_weather_years(
                historical_state_load_hourly,
                weather_years
            )
            state_load_hourly = prepend_historical_hourly_state_load(
                state_load_hourly,
                historical_state_load_hourly,
                historical_state_load_annual
            )
            state_load_hourly = downselect_to_model_years(
                state_load_hourly,
                solveyears
            )
        case 'historic':
            state_load_hourly = (
                apply_load_growth_factors_to_historical_state_load(
                    state_load_hourly,
                    historical_state_load_annual,
                    inputs_case,
                    solveyears
                )
            )
        case _:
            state_load_hourly = downselect_to_model_years(
                state_load_hourly,
                solveyears
            )
            if len(state_load_hourly.unstack('year')) == 8760:
                state_load_hourly = duplicate_weather_years(
                    state_load_hourly,
                    weather_years
                )

    regional_load_hourly = reaggregate_to_model_regions(
        state_load_hourly,
        inputs_case,
        sw.GSw_LoadAllocationMethod
    )

    #%%%#########################################
    #    -- Performing Load Modifications --    #
    #############################################

    if int(sw.GSw_LoadAdjust):
        regional_load_hourly = apply_regional_load_adjustments(
            regional_load_hourly,
            inputs_case,
            sw.GSw_LoadAdjust_Profiles,
            sw.GSw_LoadAdjust_Adoption
        )

    regional_load_hourly = apply_distribution_loss_factor(
        regional_load_hourly,
        scalars['distloss']
    )
    regional_load_hourly = regional_load_hourly.astype(np.float32)

    #%%%#########################################
    #    -- Peak Load Calculation --    #
    #############################################

    peakload = calculate_peak_load(regional_load_hourly, hierarchy)

    #%%###########################
    #    -- Data Write-Out --    #
    ##############################

    reeds.io.write_profile_to_h5(regional_load_hourly, 'load.h5', inputs_case)
    peakload.to_csv(os.path.join(inputs_case,'peakload.csv'))
    ### Write peak demand by NERC region to use in firm net import constraint
    (
        peakload.loc['nercr']
        .stack('year')
        .rename_axis(['*nercr','t'])
        .rename('MW')
        .to_csv(os.path.join(inputs_case,'peakload_nercr.csv'))
    )


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == '__main__':
    # Time the operation of this script
    tic = datetime.datetime.now()

    ### Parse arguments
    parser = argparse.ArgumentParser(
        description='Create run-specific hourly profiles',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('reeds_path', help='ReEDS-2.0 directory')
    parser.add_argument('inputs_case', help='ReEDS-2.0/runs/{case}/inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    #%% Run it
    main(reeds_path=reeds_path, inputs_case=inputs_case)

    reeds.log.toc(tic=tic, year=0, process='input_processing/hourly_load.py',
        path=os.path.join(inputs_case,'..'))
    
    print('Finished hourly_load.py')
