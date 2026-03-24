"""
    This function is used to define a thermal generator in the model. It
    contains one struct and an inner constructor to check if the inputs are
    valid.

    Parameters
    ----------
    name : String
        The name of the generator.
    timesteps : Int64
        Number of timesteps in the PRAS problem.
    region_name : String
        Name of the region associated with this generator.
    capacity : Float64
        Capacity of the generator.
    fuel : String
        Fuel type of the generator (default "OT").
    legacy : String
        Existing or New generator (default "New").
    FOR : Vector{Float32}
        Forced Outage Rate (default 0.0).
    SOR : Vector{Float32}
        Scheduled Outage Rate (default 0.0).
    MTTR : Int64
        Mean Time To Repair/Replace (default 24).

    Returns
    -------
    An instance of a Thermal_Gen.
"""
struct Thermal_Gen <: Generator
    name::String
    timesteps::Int64
    region_name::String
    capacity::Float64
    fuel::String
    legacy::String
    FOR::Vector{Float32}
    SOR::Vector{Float32}
    MTTR::Int64

    # Inner Constructors & Checks
    function Thermal_Gen(;
        name = "init_name",
        timesteps = 8760,
        region_name = "init_name",
        capacity = 10.0,
        fuel = "OT",
        legacy = "New",
        FOR = zeros(Float32, timesteps), 
        SOR = zeros(Float32, timesteps),
        MTTR = 24,
    )
        capacity >= 0.0 || error("$(name) capacity value passed is < 0")

        legacy in ["Existing", "New"] ||
            error("$(name) has legacy $(legacy) which is not in [Existing, New]")

        length(FOR) == timesteps ||
            error("The length of the $(name) FOR time series data is $(length(FOR))
                but it should be should be equal to PRAS timesteps ($(timesteps))")

        if !isnothing(SOR)
            length(SOR) == timesteps ||
                error("The length of the $(name) SOR time series data is $(length(SOR))
                but it should be should be equal to PRAS timesteps ($(timesteps))")
        end

        MTTR > 0 || error("$(name) MTTR value is <= 0")

        return new(name, timesteps, region_name, capacity, fuel, legacy, FOR, SOR, MTTR)
    end
end

# Getter Functions
get_capacity(gen::Thermal_Gen) = round.(Int, gen.capacity * (1 .-gen.SOR)')

get_fuel(gen::Thermal_Gen) = gen.fuel

get_category(gen::Thermal_Gen) = "$(gen.legacy)_Thermal|$(gen.fuel)"

get_type(gen::Thermal_Gen) = gen.fuel
