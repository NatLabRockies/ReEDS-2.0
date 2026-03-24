"""
    This function creates PRAS objects based on data from the ReEDS
    capacity expansion model. It processes regional load profiles,
    interregional transmission lines, thermal generators,
    storages, and GeneratorStorages into arrays suitable for creating
    a PRAS system.

    Parameters
    ----------
    ReEDS_data : ReEDSdatapaths
        data paths with specific ReEDS file paths
    timesteps : Int
        Number of timesteps
    solve_year : Int
        ReEDS solve year
    scheduled_outage : Bool,
        Flag to read the scheduled_outage_hourly file (if available)
    Returns
    -------
    lines : Array{Line}
        contains Line objects
    regions : Array{Region}
        contains Region objects
    gens_array : Array{VegGen}
        contains VG Gen objects
    storage_array : Array{Storage}
        contains Storage objects
    genstor_array : Array{GeneratorStorage}
        contains GeneratorStorage objects
"""
function parse_reeds_data(
    ReEDS_data::ReEDSdatapaths,
    timesteps::Int,
    solve_year::Int;
    hydro_energylim = false,
    scheduled_outage = false,
    pras_agg_ogs_lfillgas = false,
    pras_existing_unit_size = true,
    pras_max_unitsize_prm = true,
)
    @info "Processing regions and associating load profiles..."
    region_array = process_regions_and_load(ReEDS_data)

    @info "Processing lines and adding VSC-related regions, if applicable..."
    lines = process_lines(ReEDS_data, get_name.(region_array), timesteps)
    lines, regions = process_vsc_lines(lines, region_array)

    # Create Generator Objects
    # **TODO: Should 0 MW generators be allowed after disaggregation?
    # **TODO: is it important to also handle planned outages?
    @info(
        "splitting thermal, storage, variable and hydro generator types from installed " *
        "ReEDS capacities..."
    )
    thermal_builds, storage, hydro_disp_gens, hydro_non_disp_gens =
        split_generator_types(ReEDS_data)

    @info "reading in ReEDS generator-type forced outage data..."
    forced_outage_data = get_forced_outage_data(ReEDS_data)
    FOR_dict = Dict(forced_outage_data[!, "ResourceType"] .=> forced_outage_data[!, "FOR"])

    @info "reading hourly forced outage rates"
    forcedoutage_hourly = get_hourly_forced_outage_data(ReEDS_data)

    @info "reading in ATB unit size data for use with disaggregation..."
    unitsize_data = get_unitsize_mapping(ReEDS_data)
    unitsize_dict = Dict(unitsize_data[!, "tech"] .=> unitsize_data[!, "MW"])

    scheduled_outage_hourly = nothing
    # read the scheduled_outage CSV file if scheduled_outage
    if scheduled_outage
        @info "reading hourly scheduled outage rates..."
        scheduled_outage_hourly = get_hourly_scheduled_outage_data(ReEDS_data)
    end

    @info "reading MTTR data"
    mttr_dict = get_MTTR_data(ReEDS_data)

    @info "Processing conventional/thermal generators..."
    thermal_gens = process_thermals_with_disaggregation(
        ReEDS_data,
        thermal_builds,
        FOR_dict,
        forcedoutage_hourly,
        unitsize_dict,
        timesteps,
        solve_year,
        mttr_dict,
        scheduled_outage_hourly = scheduled_outage_hourly,
        pras_agg_ogs_lfillgas = pras_agg_ogs_lfillgas,
        pras_existing_unit_size = pras_existing_unit_size,
        pras_max_unitsize_prm = pras_max_unitsize_prm,
    )
    @info "Processing variable generation..."
    gens_array = process_vg(
        thermal_gens,
        ReEDS_data,
    )

    @info "Processing Storages..."
    @debug "storage is $(storage)"
    storage_array = process_storages(
        storage,
        FOR_dict,
        forcedoutage_hourly,
        unitsize_dict,
        ReEDS_data,
        timesteps,
        mttr_dict,
        scheduled_outage_hourly = scheduled_outage_hourly,
    )

    @info "Processing hydroelectric generators..."
    gens_array, genstor_array = process_hydro(
        gens_array,
        hydro_disp_gens,
        hydro_non_disp_gens,
        FOR_dict,
        forcedoutage_hourly,
        ReEDS_data,
        solve_year,
        timesteps,
        mttr_dict,
        unitsize_dict,
        scheduled_outage_hourly = scheduled_outage_hourly,
        hydro_energylim = hydro_energylim,
    )

    #@info "Processing GeneratorStorages"
    #genstor_array = process_genstors(genstor_array, get_name.(regions), timesteps)

    return lines, regions, gens_array, storage_array, genstor_array
end
