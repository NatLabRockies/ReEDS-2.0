"""
    This code defines a struct called Gen_Storage which is a subtype of
    Storage. The struct has 14 fields: name, timesteps, region_name, type,
    charge_cap, discharge_cap, energy_cap, inflow, grid_withdrawl_cap,
    grid_inj_cap, legacy, charge_eff, discharge_eff and carryover_eff. The
    code also contains an inner constructor and checks to ensure that the
    values passed are valid. Specifically, all capacity values must be 
    greater than or equal to 0.0,the legacy value must either be “Existing” 
    or “New”, all of the efficiency values must be between 0.0 and 1.0 (inclusive),
    FOR must be between 0.0 and 1.0 (inclusive) and MTTR must be greater than 0.
    Additionally, there is a commented out check that verifies that all of
    the time series data is of the same size. Finally, if any of these
    checks fail, an error will be thrown.

    Parameters
    ----------
    name : string
        Name of Gen_Storage
    timesteps : integer
        PRAS timesteps (timesteps)
    region_name : string
        Region name
    type : string
        Storage type
    charge_cap : float
        Charge capacity
    discharge_cap : float
        Discharge capacity
    energy_cap : float
        Energy capacity
    inflow : float
        Inflow time series data
    grid_withdrawl_cap : float
        Grid withdrawal capacity time series data
    grid_inj_cap : floating point
        Grid injection capacity time series data
    legacy : string
        Must be either "Existing" or "New"
    charge_eff : float
        Charge efficiency
    discharge_eff : float
        Discharge efficiency
    carryover_eff : float
        Carryover efficiency
    FOR : float
        Forced Outage Rate value
    SOR : Vector{Float32}
        Scheduled Outage Rate
    MTTR : integer
        Mean Time To Repair value

    Returns
    -------
    A new instance of Gen_Storage.
"""
struct Gen_Storage <: Storage
    name::String
    timesteps::Int64
    region_name::String
    type::String
    charge_cap::Vector{Float64}
    discharge_cap::Vector{Float64}
    energy_cap::Vector{Float64}
    inflow::Vector{Float64}
    grid_withdrawl_cap::Vector{Float64}
    grid_inj_cap::Vector{Float64}
    legacy::String
    charge_eff::Float64
    discharge_eff::Float64
    carryover_eff::Float64
    FOR::Vector{Float32} 
    SOR::Vector{Float32}
    MTTR::Int64

    # Inner Constructors & Checks
    function Gen_Storage(;
        name = "init_name",
        timesteps = 8760,
        region_name = "init_name",
        type = "init_type",
        charge_cap = zeros(Float64, timesteps),
        discharge_cap = zeros(Float64, timesteps),
        energy_cap = zeros(Float64, timesteps),
        inflow = zeros(Float64, timesteps),
        grid_withdrawl_cap = zeros(Float64, timesteps),
        grid_inj_cap = zeros(Float64, timesteps),
        legacy = "New",
        charge_eff = 1.0,
        discharge_eff = 1.0,
        carryover_eff = 1.0,
        FOR = zeros(Float32, timesteps),
        SOR = zeros(Float32, timesteps),
        MTTR = 24,
    )
        all(charge_cap .>= 0.0) || error(
            "Charge capacity passed is not allowed (should be >= 0.0) : $(name) - $(charge_cap) MW",
        )

        all(discharge_cap .>= 0.0) || error(
            "Discharge capacity passed is not allowed (should be >= 0.0) : $(name) - $(discharge_cap) MW",
        )

        all(energy_cap .>= 0.0) || error(
            "Energy capacity passed is not allowed (should be >= 0.0) : $(name) - $(energy_cap) MWh",
        )

        all(inflow .>= 0.0) || error(
            "Inflow passed is not allowed (should be >= 0.0) : $(name) - $(inflow) MW",
        )

        all(grid_withdrawl_cap .>= 0.0) || error(
            "Grid withdrawl capacity passed is not allowed (should be >= 0.0) : $(name) - $(grid_withdrawl_cap) MW",
        )

        all(grid_inj_cap .>= 0.0) || error(
            "Grid injection capacity passed is not allowed (should be >= 0.0) : $(name) - $(grid_inj_cap) MW",
        )

        legacy in ["Existing", "New"] ||
            error("$(name) has legacy $(legacy) which is not in [Existing, New]")

        all(0.0 .<= [charge_eff, discharge_eff, carryover_eff] .<= 1.0) ||
            error("$(name) charge/discharge/carryover efficiency value is < 0.0 or > 1.0")

        all(0.0 .<= FOR .<= 1.0) || error("$(name) FOR value is < 0 or > 1")

        MTTR > 0 || error("$(name) MTTR value is <= 0")

        return new(
            name,
            timesteps,
            region_name,
            type,
            charge_cap,
            discharge_cap,
            energy_cap,
            inflow,
            grid_withdrawl_cap,
            grid_inj_cap,
            legacy,
            charge_eff,
            discharge_eff,
            carryover_eff,
            FOR,
            SOR,
            MTTR,
        )
    end
end

# Getter Functions

#TODO: is SOR for grid injection enough? Do we need to derate energy capacity too?

get_charge_capacity(stor::Gen_Storage) = permutedims(round.(Int, stor.charge_cap))

get_discharge_capacity(stor::Gen_Storage) = permutedims(round.(Int, stor.discharge_cap))

get_inflow(stor::Gen_Storage) = permutedims(round.(Int, stor.inflow))

get_grid_withdrawl_capacity(stor::Gen_Storage) =
    permutedims(round.(Int, stor.grid_withdrawl_cap))


get_grid_injection_capacity(stor::Gen_Storage) = 
    permutedims(round.(Int, stor.grid_inj_cap .* (1 .-stor.SOR)))