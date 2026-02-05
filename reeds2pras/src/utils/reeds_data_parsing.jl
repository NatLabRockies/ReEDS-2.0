"""
    Processes ReEDS data and loads the specified weather year and number of
    time steps.

    Parameters
    ----------
    ReEDS_data : ReEDSData
        ReEDSData object containing the load data.
    weather_year : Int
        The weather year to be loaded.
    timesteps : Int
        The number of time steps to be loaded.

    Returns
    -------
    List
        A list of Region objects containing the load data for the specified
        weather year and number of time steps.
"""
function process_regions_and_load(ReEDS_data)
    load_data = get_load_file(ReEDS_data)
    regions = names(load_data)

    return [
        Region(r, size(load_data, 1), Int.(round.(load_data[!, r])))
        for r in regions
    ]
end

"""
    This function takes in ReEDS data, a vector of regions, a year, and a
    number of time steps, and returns an array of Line objects. It first gets
    the line capacity data from the ReEDS data, then gets the converter
    capacity data from the ReEDS data. It then adds 0 converter capacity for
    regions that lack a converter. It then creates a system line naming
    dataframe, which is a subset of the line capacity dataframe, and combines
    the MW column by summing it. It then creates a Line object for each row in
    the system line naming dataframe, and adds it to the lines_array. If the
    line is a VSC line, it adds the converter capacity data to the Line object.

    Parameters
    ----------
    ReEDS_data : DataFrame
        DataFrame containing ReEDS line capacity data.
    regions : Vector{<:AbstractString}
        Vector of region names.
    timesteps : Int
        Number of timesteps.

    Returns
    -------
    lines_array : Vector{Line}
        Vector of Line objects.
"""
function process_lines(
    ReEDS_data,
    regions::Vector{<:AbstractString},
    timesteps::Int,
)
    #it is assumed this has prm line capacity data
    line_base_cap_data = get_line_capacity_data(ReEDS_data)

    converter_capacity_data = get_converter_capacity_data(ReEDS_data)
    converter_capacity_dict = Dict(
        convert.(String, converter_capacity_data[!, "r"]) .=>
            converter_capacity_data[!, "MW"],
    )

    #add 0 converter capacity for regions that lack a converter
    if length(keys(converter_capacity_dict)) > 0
        for reg in regions
            if !(reg in keys(converter_capacity_dict))
                @info("$reg does not have VSC converter capacity, so adding" * " a 0")
                converter_capacity_dict[reg] = 0.0
            end
        end
    end

    function keep_line(from_pca, to_pca)
        from_idx = findfirst(x -> x == from_pca, regions)
        to_idx = findfirst(x -> x == to_pca, regions)
        return !isnothing(from_idx) && !isnothing(to_idx) && (from_idx < to_idx)
    end
    system_line_naming_data =
        DataFrames.subset(line_base_cap_data, [:r, :rr] => DataFrames.ByRow(keep_line))
    # split-apply-combine b/c some lines have same name convention
    system_line_naming_data = DataFrames.combine(
        DataFrames.groupby(system_line_naming_data, ["r", "rr", "trtype"]),
        :MW => sum,
    )

    lines_array = Line[]
    for row in eachrow(system_line_naming_data)
        forward_cap = sum(
            line_base_cap_data[
                (line_base_cap_data.r .== row.r) .& (line_base_cap_data.rr .== row.rr) .& (line_base_cap_data.trtype .== row.trtype),
                "MW",
            ],
        )
        backward_cap = sum(
            line_base_cap_data[
                (line_base_cap_data.r .== row.rr) .& (line_base_cap_data.rr .== row.r) .& (line_base_cap_data.trtype .== row.trtype),
                "MW",
            ],
        )

        name = "$(row.r)|$(row.rr)|$(row.trtype)"
        @debug(
            "a line $name, with $forward_cap MW forward and $backward_cap" *
            " backward in $(row.trtype)"
        )
        if row.trtype != "VSC"
            push!(
                lines_array,
                Line(
                    name = name,
                    timesteps = timesteps,
                    category = row.trtype,
                    region_from = row.r,
                    region_to = row.rr,
                    forward_cap = forward_cap,
                    backward_cap = backward_cap,
                    legacy = "Existing",
                    # We do not model outages for lines so just use filler values
                    FOR = 0.0,
                    MTTR = 24,
                ),
            )
        else
            push!(
                lines_array,
                Line(
                    name = name,
                    timesteps = timesteps,
                    category = row.trtype,
                    region_from = row.r,
                    region_to = row.rr,
                    forward_cap = forward_cap,
                    backward_cap = backward_cap,
                    legacy = "Existing",
                    # We do not model outages for lines so just use filler values
                    FOR = 0.0,
                    MTTR = 24,
                    VSC = true,
                    converter_capacity = Dict(
                        row.r => converter_capacity_dict[string(row.r)],
                        row.rr => converter_capacity_dict[string(row.rr)],
                    ),
                ),
            )
        end
    end
    return lines_array
end

"""
    Split generator types into thermal, storage, and variable generation
    resources

    Parameters
    ----------
    ReEDS_data : dict
        Raw ReEDS data as a dict
    year : Int
        Year of interest

    Returns
    -------
    DataFrames
        (thermal, storage, dispatchable hydro, nondispatchable hydro) capacity
"""
function split_generator_types(ReEDS_data::ReEDSdatapaths)
    ## Read {case}/inputs_case/tech-subset-table.csv
    tech_subset_table = get_technology_types(ReEDS_data)
    @debug "tech_subset_table is $(tech_subset_table)"
    ## Read {case}/ReEDS_Augur/augur_data/max_cap_{year}.csv
    capacity_data = get_ICAP_data(ReEDS_data)
    ## Read {case}/inputs_case/resources.csv
    resources = get_valid_resources(ReEDS_data)
    @debug "resources is $(resources)"
    vg_types = unique(resources.i)
    push!(vg_types, "vre")
    @debug "vg_types is $(vg_types)"

    hyd_disp_types =
        lowercase.(DataFrames.dropmissing(tech_subset_table, :HYDRO_D)[:, "Column1"])
    hyd_non_disp_types =
        lowercase.(DataFrames.dropmissing(tech_subset_table, :HYDRO_ND)[:, "Column1"])

    @debug "hd_types is $(union(hyd_disp_types,hyd_non_disp_types))"

    storage_types =
        unique(DataFrames.dropmissing(tech_subset_table, :STORAGE_STANDALONE)[:, "Column1"])

    @debug "storage type is $(storage_types)"

    # clean vg/storage capacity on a regex, though there might be a better way...
    clean_names!(vg_types)
    @debug "vg_types is $(vg_types)"
    clean_names!(storage_types)

    storage_capacity = filter(x -> x.i in storage_types, capacity_data)

    hyd_disp_capacity = filter(x -> x.i in hyd_disp_types, capacity_data)
    hyd_non_disp_capacity = filter(x -> x.i in hyd_non_disp_types, capacity_data)

    thermal_capacity = filter(
        x -> ~(x.i in union(vg_types, storage_types, hyd_disp_types, hyd_non_disp_types)),
        capacity_data,
    )

    @debug "thermal_capacity is $(thermal_capacity)"
    return thermal_capacity,
    storage_capacity,
    hyd_disp_capacity,
    hyd_non_disp_capacity
end

"""
    Process existing thermal capacities with disaggregation.

    Parameters
    ----------
    ReEDS_data : object
        The ReEDS data object
    thermal_builds : DataFrames.DataFrame
        Data frame containing the thermal build information
    FOR_dict : dict
        Dictionary of Forced Outage Rates (FORs) for each resource
    timesteps : int
        Number of slices to disaggregate the capacity
    year : int
        Year associated with the capacity
    scheduled_outage_hourly: Union{Nothing, DataFrames.DataFrame}
        a dataframe of hourly scheduled outage rates
        (if the scheduled_outage_rate file is read). If no file is read, a default 
        nothing is used. 
    Returns
    -------
    all_generators : Generator[]
        Array of Generator objects containing the disaggregated capacity for
        each resource
"""
function process_thermals_with_disaggregation(
    ReEDS_data,
    thermal_builds::DataFrames.DataFrame,
    FOR_dict::Dict,
    forcedoutage_hourly::DataFrames.DataFrame,
    unitsize_dict::Dict,
    timesteps::Int,
    year::Int,
    mttr_dict::Dict;
    scheduled_outage_hourly::Union{Nothing, DataFrames.DataFrame},
    pras_agg_ogs_lfillgas = false,
    pras_existing_unit_size = true,
    pras_max_unitsize_prm = true,
)
    all_generators = Generator[]
    # csp-ns is not a thermal; just drop in for now
    thermal_builds = thermal_builds[(thermal_builds.i .!= "csp-ns"), :]
    # split-apply-combine to handle differently vintaged entries
    thermal_builds =
        DataFrames.combine(DataFrames.groupby(thermal_builds, ["i", "r"]), :MW => sum)
    unitdata = get_unitdata(ReEDS_data)

    # Get the PRM [MW] in case we use it to set the max unit size
    if pras_max_unitsize_prm
        max_unitsize = get_max_unitsize(ReEDS_data)
    end

    # Get the FOR for each build/tech
    for row in eachrow(thermal_builds)
        tech = row.i
        i_r = "$tech|$(row.r)"

        if (i_r in DataFrames.names(forcedoutage_hourly))
            gen_for = forcedoutage_hourly[!, i_r]
        elseif lowercase(tech) in keys(FOR_dict)
            gen_for = fill(Float32(FOR_dict[lowercase(tech)]), timesteps)
            @info(
                "$tech ($(row.r)) was not found in forcedoutage_hourly so using " *
                "static value of $(FOR_dict[tech]) from outage_forced_static.csv"
            )
        else
            @error(
                "$(tech) ($(row.r)) was not found in forcedoutage_hourly or outage_forced_static.csv"
            )
        end

        gen_sor = zeros(Float32, timesteps)
        if !isnothing(scheduled_outage_hourly) && tech in DataFrames.names(scheduled_outage_hourly)
            gen_sor = scheduled_outage_hourly[!, tech]
        end

        mttr = Int64(mttr_dict[tech])

        generator_array = disagg_existing_capacity(
            unitdata,
            unitsize_dict,
            Int(round(row.MW_sum)),
            String(row.i),
            String(row.r),
            gen_for,
            timesteps,
            year,
            mttr,
            gen_sor,
            pras_agg_ogs_lfillgas = pras_agg_ogs_lfillgas,
            pras_existing_unit_size = pras_existing_unit_size,
            # Use PRM MW if pras_max_unitsize_prm switch is on; otherwise ignore by setting to 0
            max_unit_mw = (pras_max_unitsize_prm ? max_unitsize[row.r] : 0),
        )
        append!(all_generators, generator_array)
    end
    return all_generators
end

"""
    We use this function if we want to process hydroelectric generators as fixed capacities.
    It is a replication of the process thermal functions to retain the older way of
    handling hydro plants, where we do not use hydro capacity factors, and distinguish
    dispatchable and non dispatchable hydroelectric generators.

    Parameters
    ----------
    all_generators : Generator[]
        Array of Generator objects containing the capacity for
        each resource, and it is modified in place.
    ReEDS_data : object
        The ReEDS data object
    hd_builds : DataFrames.DataFrame
        Data frame containing the hydro plant information
    FOR_dict : dict
        Dictionary of Forced Outage Rates (FORs) for each resource
    timesteps : int
        Number of slices to disaggregate the capacity
    year : int
        Year associated with the capacity
    scheduled_outage_hourly: Union{Nothing, DataFrames.DataFrame}
        a dataframe of hourly scheduled outage rates
        (if the scheduled_outage_rate file is read). If no file is read, a default 
        nothing is used. 
    Returns
    -------
"""
function process_hd_as_generator!(
    all_generators,
    ReEDS_data,
    hd_builds::DataFrames.DataFrame,
    FOR_dict::Dict,
    forcedoutage_hourly::DataFrames.DataFrame,
    unitsize_dict::Dict,
    timesteps::Int,
    year::Int,
    mttr_dict::Dict,
    scheduled_outage_hourly::Union{Nothing, DataFrames.DataFrame},
)

    # split-apply-combine to handle differently vintaged entries
    hd_builds = DataFrames.combine(DataFrames.groupby(hd_builds, ["i", "r"]), :MW => sum)
    unitdata = get_unitdata(ReEDS_data)

    # Get the FOR for each build/tech
    for row in eachrow(hd_builds)
        tech = row.i
        i_r = "$tech|$(row.r)"

        if (i_r in DataFrames.names(forcedoutage_hourly))
            gen_for = forcedoutage_hourly[!, i_r]
        elseif lowercase(tech) in keys(FOR_dict)
            gen_for = fill(Float32(FOR_dict[lowercase(tech)]), timesteps)
            @info(
                "$tech ($(row.r)) was not found in forcedoutage_hourly so using " *
                "static value of $(FOR_dict[tech]) from outage_forced_static.csv"
            )
        else
            @error(
                "$(tech) ($(row.r)) was not found in forcedoutage_hourly or outage_forced_static.csv"
            )
        end

        mttr = Int64(mttr_dict[tech])

        gen_sor = zeros(Float32, timesteps)
        if !isnothing(scheduled_outage_hourly) && tech in DataFrames.names(scheduled_outage_hourly)
            gen_sor = scheduled_outage_hourly[!, tech]
        end 

        generator_array = disagg_existing_capacity(
            unitdata,
            unitsize_dict,
            Int(round(row.MW_sum)),
            String(row.i),
            String(row.r),
            gen_for,
            timesteps,
            year,
            mttr,
            gen_sor,
        )
        append!(all_generators, generator_array)
    end
end

"""
    Add generators for each tech/region in pras_vre_gen_{year}.h5.
    Capacity is taken as the maximum of the hourly generation profile.
    VRE outages are already included in VRE profiles, so we do not disaggregate
    VRE or apply outages in PRAS.

    Parameters
    ----------
    generators_array : Vector{<:ReEDS2PRAS.Generator}
        Vector of ReEDS Generators
    ReEDS_data : DataFrames.DataFrame
        A dataset from the ReEDS Program
    scheduled_outage_hourly: Union{Nothing, DataFrames.DataFrame}
        a dataframe of hourly scheduled outage rates
        (if the scheduled_outage_rate file is read). If no file is read, a default 
        nothing is used. 
    Returns
    -------
    generators_array : Vector{<:ReEDS2PRAS.Generator}
        An array of the VG generators
"""
function process_vg(
    generators_array::Vector{<:ReEDS2PRAS.Generator},
    ReEDS_data,
)
    vg_profiles = get_vg_cf_data(ReEDS_data)
    timesteps = size(vg_profiles, 1)

    for name in names(vg_profiles)
        tech, region = split(name, "|")
        profile = vg_profiles[!, name]
        push!(
            generators_array,
            Variable_Gen(
                name = name,
                timesteps = timesteps,
                region_name = region,
                installed_capacity = maximum(profile),
                capacity = profile,
                type = tech,
                legacy = "New",
                FOR = zeros(Float32, timesteps),
                MTTR = 24,
            ),
        )
    end
    return generators_array
end

"""
    Parameters
    ----------
    generators_array : Vector{<:Generator}
        a vector of strings of distinct regions in the model
    hydro_disp_capacities : DataFrame
        a dataframe containing details of dispatchable (reservoir)
        HD generators
    hydro_non_disp_capacities : DataFrame
        a dataframe containing details of non-dispatchable 
        (run-of-river) HD generators
    FOR_dict : Dict
        a dictionary of forced outage rates, not applied to HD 
        devices for now
    ReEDS_data
        input data from ReEDS
    timesteps : Int
        number of timesteps
    year : Int64
        ReEDS target simulation year
    scheduled_outage_hourly: Union{Nothing, DataFrames.DataFrame}
        a dataframe of hourly scheduled outage rates
        (if the scheduled_outage_rate file is read). If no file is read, a default 
        nothing is used. 
    hydro_energylim : Bool
        a flag which allows users to choose whether to model HD 
        devices as flat generators, or as variable generator for 
        run-of-river plants and generatorstorage for reservoir 
        plants
    unitsize_dict = nothing,
    Returns
    -------
    generators_array : Vector{<:Generator}
        Generators array updated with hydro generators, either all 
        generators as static capacity, or run-of-river generators
        as variable generators
    gen_stors : Gen_Storage
        Generator_storages array returned as empty if we don't 
        process energy limits, or returned with reservoir hydro
        plants (dispatchable type)
"""
function process_hydro(
    generators_array::Vector{<:Generator},
    hydro_disp_capacities::DataFrames.DataFrame,
    hydro_non_disp_capacities::DataFrames.DataFrame,
    FOR_dict::Dict,
    forcedoutage_hourly::DataFrames.DataFrame,
    ReEDS_data,
    year::Int64,
    timesteps::Int,
    mttr_dict::Dict,
    unitsize_dict;
    scheduled_outage_hourly::Union{Nothing, DataFrames.DataFrame},
    hydro_energylim = false,
)

    # If we do not impose energy limits on hydro and model it as fixed capacity
    if !(hydro_energylim)
        @info "Processing HD generators as generator with fixed capacities..."

        process_hd_as_generator!(
            generators_array,
            ReEDS_data,
            hydro_disp_capacities,
            FOR_dict,
            forcedoutage_hourly,
            unitsize_dict,
            timesteps,
            year,
            mttr_dict,
            scheduled_outage_hourly,
        )

        process_hd_as_generator!(
            generators_array,
            ReEDS_data,
            hydro_non_disp_capacities,
            FOR_dict,
            forcedoutage_hourly,
            unitsize_dict,
            timesteps,
            year,
            mttr_dict,
            scheduled_outage_hourly
        )
        genstor_array = Gen_Storage[]

        return generators_array, genstor_array
    end

    hydcf, hydcapadj = get_hydro_data(ReEDS_data)
    monthhours = monhours()

    timesteps_year = 8760
    num_years = Int(timesteps // timesteps_year)

    # Combine all plant vintages for each region and plant type for dispatchable plants
    disp_combined_caps =
        DataFrames.combine(DataFrames.groupby(hydro_disp_capacities, [:i, :r]), :MW => sum)

    genstor_array = Gen_Storage[]

    # We need the dispatch limit for each hour from each asset and each month's energy budget
    # applied as an exogenous limit using inflow. We have monthly capacity factors for energy budget
    # and monthly capacity adjustment factor on the nameplate capacity for dispatch limits. 
    # For each month, (i) energy budget is calculated based on number of hours in the month
    # and (ii) dispatch limit is calculated based on the month.
    for (idx, row) in enumerate(DataFrames.eachrow(disp_combined_caps))
        reg_plant_subset =
            filter(x -> (x.r == row.r && x.i == row.i), hydcf)[:, [:month, :value]]
        monthly_energy = zeros(timesteps_year)
        dispatch_limit = zeros(timesteps_year)
        energy_cap = zeros(timesteps_year)
        for monhr in monthhours
            try
                reqd_slice = monhr.slice
                monthly_energy[first(reqd_slice)] =
                    (monhr.numhrs * filter(x -> (x.month == monhr.month), reg_plant_subset)[
                        :,
                        :value,
                    ] * row.MW_sum)[1]

                energy_cap[reqd_slice] .=
                    (monhr.numhrs * filter(x -> (x.month == monhr.month), reg_plant_subset)[
                        :,
                        :value,
                    ] * row.MW_sum)[1]

                capacity_adjust = hydcapadj[
                    (hydcapadj.i .== row.i) .&& (hydcapadj.r .== row.r),
                    [:month, :value],
                ]
                dispatch_limit[reqd_slice] .=
                    (filter(x -> (x.month == monhr.month), capacity_adjust)[
                        :,
                        :value,
                    ] * row.MW_sum)[1]
            catch e
                if isa(e, BoundsError)
                    @error "$(row.r),$(row.i),$(e)"
                else
                    error()
                end
            end
        end

        category = string(row.i)
        name = "$(category)_$(string(row.r))"
        region = string(row.r)

        gen_sor = zeros(Float32, timesteps)
        if !isnothing(scheduled_outage_hourly) && category in DataFrames.names(scheduled_outage_hourly)
            gen_sor = scheduled_outage_hourly[!, category]
        end

        mttr = Int64(mttr_dict[category])
        
        # - Charging to genstore is limited by charge_capacity whether from grid or from 
        # inflows. So, that charge_capacity should be equal to the genflow timeseries.
        # - Powerflow into grid is limited by grid_injection, which can come from discharge
        # and/or exogenous inflow. So discharge capacity can be the dispatch limit or 
        # arbitrarily high, while the grid_injection cap has to the dispatch limit.
        # - Energy capacity can be arbitrarily high in the absense of reservoir limit to 
        # ensure month to month energy energy carryover.
        push!(
            genstor_array,
            Gen_Storage(
                name = name,
                timesteps = timesteps,
                region_name = region,
                charge_cap = repeat(monthly_energy, num_years),
                discharge_cap = repeat(dispatch_limit, num_years),
                energy_cap = repeat(energy_cap, num_years),
                inflow = repeat(monthly_energy, num_years),
                grid_withdrawl_cap = zeros(timesteps),
                grid_inj_cap = repeat(dispatch_limit, num_years),
                type = category,
                legacy = "New",
                FOR = zeros(Float32, timesteps), 
                SOR = gen_sor,
                MTTR = mttr,
            ),
        )
    end

    # Non-dispatchable hydro power plants
    non_disp_combined_caps = DataFrames.combine(
        DataFrames.groupby(hydro_non_disp_capacities, [:i, :r]),
        :MW => sum,
    )

    # For non dispatchable hydro plants, the monthly capacity factor is used to determine
    # hourly capacity time series in each month. 
    for (idx, row) in enumerate(DataFrames.eachrow(non_disp_combined_caps))
        reg_type = hydcf[
            findall(x -> (x.r == row.r && x.i == row.i), eachrow(hydcf)),
            [:month, :value],
        ]
        hourly_capacity = zeros(timesteps_year)
        for monhr in monthhours
            try
                reqd_slice = monhr.slice
                hourly_capacity[reqd_slice] .=
                    (filter(x -> (x.month == monhr.month), reg_type)[
                        :,
                        :value,
                    ] * row.MW_sum)[1]
            catch e
                @error "$(row.r),$(row.i),$(e)"
            end
        end

        category = string(row.i)
        name = "$(category)_$(string(row.r))"
        region = string(row.r)
        gen_sor = zeros(Float32, timesteps)
        if !isnothing(scheduled_outage_hourly) && category in DataFrames.names(scheduled_outage_hourly)
            gen_sor = scheduled_outage_hourly[!, category]
        end
        mttr = Int64(mttr_dict[category])

        push!(
            generators_array,
            Variable_Gen(
                name = name,
                timesteps = timesteps,
                region_name = region,
                installed_capacity = row.MW_sum,
                capacity = repeat(hourly_capacity, num_years),
                type = category,
                legacy = "New",
                FOR = zeros(Float32, timesteps),
                SOR = gen_sor,
                MTTR = mttr,
            ),
        )
    end

    return generators_array, genstor_array
end

"""
    Process data associated with the regional storage build for modeled time
    period

    Parameters
    ----------
    storage_builds : DataFrames.DataFrame
        Data construct containing regional storage build information
    FOR_dict : Dict
        dictionary of Forced Outage Rates (FOR) associated with storage types
    ReEDS_data
        input data from ReEDS
    timesteps : Int
        Number of timesteps
    year : Int64
        simulated time period
    scheduled_outage_hourly: Union{Nothing, DataFrames.DataFrame}
        a dataframe of hourly scheduled outage rates
        (if the scheduled_outage_rate file is read). If no file is read, a default 
        nothing is used. 
    Returns
    -------
    storages_array : Storage[]
        array of modeled storages
"""
function process_storages(
    storage_builds::DataFrames.DataFrame,
    FOR_dict::Dict,
    forcedoutage_hourly::DataFrames.DataFrame,
    unitsize_dict::Dict,
    ReEDS_data,
    timesteps::Int,
    mttr_dict::Dict;
    scheduled_outage_hourly::Union{Nothing, DataFrames.DataFrame}
)
    storage_energy_capacity_data = get_storage_energy_capacity_data(ReEDS_data)
    @debug "storage_energy_capacity_data is $(storage_energy_capacity_data)"
    # split-apply-combine to handle differently vintaged entries
    energy_capacity_df = DataFrames.combine(
        DataFrames.groupby(storage_energy_capacity_data, ["i", "r"]),
        :MWh => sum,
    )

    efficiency_in = Dict(
        polarity => DataFrames.DataFrame(CSV.File(joinpath(
            ReEDS_data.ReEDSfilepath,
            "ReEDS_Augur",
            "augur_data",
            "$(polarity)_eff_$(ReEDS_data.year).csv"
        )))
        for polarity in ["charge", "discharge"]
    )
    efficiency = Dict(
        polarity => Dict(zip(efficiency_in[polarity][!,"i"], efficiency_in[polarity][!,"fraction"]))
        for polarity in keys(efficiency_in)
    )

    ## Read {case}/inputs_case/tech-subset-table.csv
    tech_subset_table = get_technology_types(ReEDS_data)
    battery_types = DataFrames.dropmissing(tech_subset_table, :BATTERY)[:, "Column1"]

    storages_array = Storage[]
    for (idx, row) in enumerate(eachrow(storage_builds))
        gen_sor = zeros(Float32, timesteps)
        storage_type = string(row.i)
        if !isnothing(scheduled_outage_hourly) && storage_type in DataFrames.names(scheduled_outage_hourly)
            gen_sor = scheduled_outage_hourly[!, storage_type]
        end

        name = "$(string(row.i))|$(string(row.r))"

        gen_for = nothing
        if (name in DataFrames.names(forcedoutage_hourly))
            gen_for = forcedoutage_hourly[!, name]
        else
            gen_for = fill(Float32(FOR_dict[lowercase(storage_type)]), timesteps)
            @info(
                "$name was not found in forcedoutage_hourly so using " *
                "static value of $(FOR_dict[storage_type]) from outage_forced_static.csv")
        end

        name = "$(name)|"#append for later matching
        mttr = Int64(mttr_dict[string(row.i)])

        storage_duration = energy_capacity_df[idx, "MWh_sum"] / row.MW
        if string(row.i) in battery_types
            push!(
                storages_array,
                Battery(
                    name = name,
                    timesteps = timesteps,
                    region_name = string(row.r),
                    type = string(row.i),
                    charge_cap = row.MW,
                    discharge_cap = row.MW,
                    ## Battery FOR is applied to energy capacity, not power capacity
                    energy_cap = row.MW * storage_duration * (1 .- gen_for),
                    legacy = "New",
                    charge_eff = efficiency["charge"][string(row.i)],
                    discharge_eff = efficiency["discharge"][string(row.i)],
                    carryover_eff = 1.0,
                    FOR = zeros(Float32, timesteps),
                    SOR = gen_sor,
                    MTTR = mttr,
                ),
            )
        else
            add_new_capacity!(
                storages_array,
                round(Int, row.MW),
                storage_duration,
                efficiency["charge"][string(row.i)],
                efficiency["discharge"][string(row.i)],
                # Always use the characteristic unit size
                unitsize_dict[row.i],
                row.i,
                row.r,
                gen_for,
                timesteps,
                mttr,
                gen_sor, 
            )
        end
    end
    return storages_array
end

"""
    Disaggregates the existing capacity of a thermal generator given a certain
    year, by taking into account its technology and associated balancing
    authority.

    Parameters
    ----------
    unitdata : DataFrames.DataFrame
        DataFrame containing Expected Information Administration (EIA) data.
    unitsize_dict: Dict
        Map from techs to characteristic unit size [MW]
    built_capacity : int
        The current built capacity for the thermal generator.
    tech : str
        The technology for the thermal generator.
    pca : str
        The associated balancing authority (PCA).
    gen_for : float
        The forced outage rate associated with the generator.
    gen_sor : float
        The scheduled outage rate associated with the generator.        
    timesteps : Int
        Number of timesteps.
    year : int
        The year.
    mttr : int
        mean time to repaire (mttr)
    pras_agg_ogs_lfillgas : bool
        If true, aggregate existing o-g-s and landfill gas using size for new units.
        Applies to existing o-g-s and landfill gas capaity, so does not interact with
        pras_existing_unit_size, which only affects new capacity.
    pras_existing_unit_size : bool
        If true, use average existing unit size by (tech,region) when disaggregating new
        capacity. Applies to new capacity so does not interact with pras_agg_ogs_lfillgas.
    max_unit_mw: int
        If nonzero, caps the upper bound of disaggregated unit size

    Returns
    -------
    generators_array : array
        An array composed of thermal generator objects created with the
        disaggregated existing capacities.
"""
function disagg_existing_capacity(
    unitdata::DataFrames.DataFrame,
    unitsize_dict::Dict,
    built_capacity::Int,
    tech::String,
    pca::String,
    gen_for::Vector{Float32},
    timesteps::Int,
    year::Int,
    mttr::Int,
    gen_sor::Union{Nothing, Vector{Float32}} = nothing;
    pras_agg_ogs_lfillgas = false,
    pras_existing_unit_size = true,
    max_unit_mw = 0,
)
    if pras_agg_ogs_lfillgas == true
        group_existing_techs = ["lfill-gas", "o-g-s"]
    else
        group_existing_techs = []
    end

    tech_ba_year_existing = DataFrames.subset(
        unitdata,
        :tech => DataFrames.ByRow(==(tech)),
        :reeds_ba => DataFrames.ByRow(==(pca)),
        :RetireYear => DataFrames.ByRow(>(year)),
        :StartYear => DataFrames.ByRow(<=(year)),
    )

    generators_array = []
    # If there is no existing capacity, use the characteristic unit size
    if size(tech_ba_year_existing, 1) == 0 && gen_for != 0.0
        add_new_capacity!(
            generators_array,
            built_capacity,
            # If max_unit_mw is provided and is smaller than the characteristic unit size,
            # use max_unit_mw; otherwise use the characteristic unit size from unitsize_dict
            ((max_unit_mw > 0) ? min(max_unit_mw, unitsize_dict[tech]) : unitsize_dict[tech]),
            tech,
            pca,
            gen_for,
            timesteps,
            mttr,
            gen_sor,
        )
        return generators_array
    # If the FOR is zero, no need to disaggregate, so put all capacity in one unit
    elseif size(tech_ba_year_existing, 1) == 0 && gen_for == 0.0
        return [
            Thermal_Gen(
                name = "$(tech)|$(pca)|1",
                timesteps = timesteps,
                region_name = pca,
                capacity = built_capacity,
                fuel = tech,
                legacy = "New",
                FOR = gen_for,
                SOR = gen_sor,
                MTTR = mttr,
            ),
        ]
    end

    remaining_capacity = built_capacity
    if tech in group_existing_techs
        existing_capacity_total = sum(tech_ba_year_existing[!, "summer_power_capacity_MW"])
        num_whole = Int(existing_capacity_total ÷ unitsize_dict[tech])
        remainder = existing_capacity_total % unitsize_dict[tech]
        existing_capacity = vcat(ones(num_whole) * unitsize_dict[tech], remainder)
    else
        existing_capacity = tech_ba_year_existing[!, "summer_power_capacity_MW"]
    end

    if pras_existing_unit_size == true
        # If the average integer unit size rounds to 0 MW, use 1 MW
        unit_capacity = max(Int(round(Statistics.mean(existing_capacity))), 1)
        # If max_unit_mw is provided and is smaller than the mean, use max_unit_mw instead
        if max_unit_mw > 0
            unit_capacity = min(unit_capacity, max_unit_mw)
        end
    else
        unit_capacity = 0
    end

    @info "$tech $pca: unit capacity = $unit_capacity MW"

    for (idx, built_cap) in enumerate(existing_capacity)
        int_built_cap = Int(round(built_cap))
        if int_built_cap < remaining_capacity
            gen_cap = int_built_cap
            remaining_capacity -= int_built_cap
        else
            gen_cap = remaining_capacity
            remaining_capacity = 0
        end
        gen = Thermal_Gen(
            name = "$(tech)|$(pca)|$(idx)",
            timesteps = timesteps,
            region_name = pca,
            capacity = gen_cap,
            fuel = tech,
            legacy = "Existing",
            FOR = gen_for,
            SOR = gen_sor,
            MTTR = mttr,
        )
        push!(generators_array, gen)
    end

    #whatever remains, we want to build as new capacity
    if remaining_capacity > 0
        add_new_capacity!(
            generators_array,
            remaining_capacity,
            (if (unit_capacity > 0) unit_capacity else unitsize_dict[tech] end),
            tech,
            pca,
            gen_for,
            timesteps,
            mttr,
            gen_sor,
        )
    end

    return generators_array
end

"""
    This function adds new capacity to an existing list of generators. The
    unit_capacity parameter is used to determine how many generators
    must be constructed to create the total new_capacity. If there are no
    existing units, a single generator is built with all of the new_capacity.
    For fixed unit_capacity values, the remaining capacity is divided
    evenly among the new generators, adding additional capacity to each one,
    then a small remainder may be created and added as a separate generator to
    get the desired total new_capacity. The output of this function is the
    updated generators_array containing all of the newly added generators.

    Parameters
    ----------
    generators_array : Vector{<:Any}
        a vector or list of existing generators
    new_capacity : int
        specified new capacity to be added
    unit_capacity : int
        target capacity for the units to be added
    tech : string
        type of technology used for the generator unit
    pca : string
        power control authority of the generator unit
    gen_for : float
        generation forecast
    gen_sor : float
        The scheduled outage rate associated with the generator.
    timesteps : Int
        number of timesteps
    MTTR : int
        mean time to repair for the generator unit

    Returns
    -------
    generators_array: Vector{<:Any}
        updated vector or list of generators containing the new capacity
"""
function add_new_capacity!(
    generators_array::Vector{<:Any},
    new_capacity::Int,
    unit_capacity::Int,
    tech::AbstractString,
    pca::AbstractString,
    gen_for::Vector{Float32},
    timesteps::Int,
    MTTR::Int,
    gen_sor::Union{Nothing, Vector{Float32}} = nothing,
)
    n_gens = floor(Int, new_capacity / unit_capacity)
    if n_gens == 0
        return push!(
            generators_array,
            Thermal_Gen(
                name = "$(tech)|$(pca)|new|1",
                timesteps = timesteps,
                region_name = pca,
                capacity = new_capacity,
                fuel = tech,
                legacy = "New",
                FOR = gen_for,
                SOR = gen_sor,
                MTTR = MTTR,
            ),
        )
    end

    for i in range(1, n_gens)
        push!(
            generators_array,
            Thermal_Gen(
                name = "$(tech)|$(pca)|new|$(i)",
                timesteps = timesteps,
                region_name = pca,
                capacity = unit_capacity,
                fuel = tech,
                legacy = "New",
                FOR = gen_for,
                SOR = gen_sor,
                MTTR = MTTR,
            ),
        )
    end

    remainder = new_capacity - (n_gens * unit_capacity)
    if remainder > 0
        # integer remainder is made into a tiny gen
        push!(
            generators_array,
            Thermal_Gen(
                name = "$(tech)|$(pca)|new|$(n_gens+1)",
                timesteps = timesteps,
                region_name = pca,
                capacity = remainder,
                fuel = tech,
                legacy = "New",
                FOR = gen_for,
                SOR = gen_sor,
                MTTR = MTTR,
            ),
        )
    end

    return generators_array
end

"""
    This function is the same as above but takes an additional arg
    new_duration, which will be picked up by multiple dispatch
    and leading to Battery{} model handling
"""
function add_new_capacity!(
    generators_array::Vector{<:Any},
    new_capacity::Int,
    new_duration::Float64,
    charge_eff::Float64,
    discharge_eff::Float64,
    unit_capacity::Int,
    tech::AbstractString,
    pca::AbstractString,
    gen_for::Vector{Float32},
    timesteps::Int,
    MTTR::Int,
    gen_sor::Union{Nothing, Vector{Float32}} = nothing,
)
    n_gens = floor(Int, new_capacity / unit_capacity)
    if n_gens == 0
        return push!(
            generators_array,
            Battery(
                name = "$(tech)|$(pca)|new|1",
                timesteps = timesteps,
                region_name = pca,
                type = tech,
                charge_cap = new_capacity,
                discharge_cap = new_capacity,
                energy_cap = fill(Float64(new_capacity * new_duration), timesteps),
                legacy = "New",
                charge_eff = charge_eff,
                discharge_eff = discharge_eff,
                carryover_eff = 1.0,
                FOR = gen_for,
                SOR = gen_sor,
                MTTR = MTTR,
            ),
        )
    end

    for i in range(1, n_gens)
        push!(
            generators_array,
            Battery(
                name = "$(tech)|$(pca)|new|$(i)",
                timesteps = timesteps,
                region_name = pca,
                type = tech,
                charge_cap = unit_capacity,
                discharge_cap = unit_capacity,
                energy_cap = fill(Float64(unit_capacity * new_duration), timesteps),
                legacy = "New",
                charge_eff = charge_eff,
                discharge_eff = discharge_eff,
                carryover_eff = 1.0,
                FOR = gen_for,
                SOR = gen_sor,
                MTTR = MTTR,
            ),
        )
    end

    remainder = new_capacity - (n_gens * unit_capacity)
    if remainder > 0
        # integer remainder is made into a tiny gen
        push!(
            generators_array,
            Battery(
                name = "$(tech)|$(pca)|new|$(n_gens+1)",
                timesteps = timesteps,
                region_name = pca,
                type = tech,
                charge_cap = remainder,
                discharge_cap = remainder,
                energy_cap = fill(Float64(remainder * new_duration), timesteps),
                legacy = "New",
                charge_eff = charge_eff,
                discharge_eff = discharge_eff,
                carryover_eff = 1.0,
                FOR = gen_for,
                SOR = gen_sor,
                MTTR = MTTR,
            ),
        )
    end

    return generators_array
end
