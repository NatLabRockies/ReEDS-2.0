"""
    This function takes in the attributes of a variable generator (Variable_Gen)
    and returns an object containing all its information. The input
    parameters are:

    Parameters
    ----------
    name : String
        Name of the Variable Generator.
    timesteps : Int64
        Number of timesteps for the PRAS model.
    region_name : String
        Name of the Region where Variable Generator's load area is present.
    installed_capacity : Float64
        Installed Capacity of the Variable Generator.
    capacity : Vector{Float64}
        Capacity factor time series data ('forecasted capacity' /
        'nominal capacity') for the PRAS Model.
    type : String
        Type of Variable Generator being passed.
    legacy : String
        State of the Variable Generator, i.e., existing or new.
    FOR : Float64
        Forced Outage Rate parameter of the Variable Generator.
    SOR : Float64
        Scheduled Outage Rate parameter of the Variable Generator.        
    MTTR : Int64
        Mean Time To Repair parameter of the Variable Generator.

    Returns
    -------
    Variable_Gen : Struct
        Returns a struct with all the given attributes.
"""
struct Variable_Gen <: Generator
    name::String
    timesteps::Int64
    region_name::String
    installed_capacity::Float64
    capacity::Vector{Float64}
    type::String
    legacy::String
    FOR::Vector{Float32}
    SOR::Vector{Float32}
    MTTR::Int64

    # Inner Constructors & Checks
    function Variable_Gen(;
        name = "init_name",
        timesteps = 8760,
        region_name = "init_name",
        installed_capacity = 10.0,
        capacity = zeros(Float64, timesteps),
        type = "wind-ons_init_name",
        legacy = "New",
        FOR = zeros(Float32, timesteps),
        SOR = zeros(Float32, timesteps),
        MTTR = 24,
    )
        all(0.0 .<= capacity .<= installed_capacity) || if ~(startswith(type, "hyd"))
            # We do not need to ensure that capacity is < installed capacity
            # for hydroelectric plants because we sometimes have 
            # capacity factors > 1
            error("$(name) time series has values < 0 or > installed capacity
            ($(installed_capacity))")
        end

        length(capacity) == timesteps ||
            error("The length of the $(name) capacity time series data is $(length(capacity))
                   but it should be should be equal to PRAS timesteps ($(timesteps))")

        legacy in ["Existing", "New"] ||
            error("$(name) has legacy $(legacy) which is not in [Existing, New]")

        all(0.0 .<= FOR .<= 1.0) || error("$(name) FOR value is < 0 or > 1")

        if !isnothing(SOR)
            length(SOR) == timesteps ||
                error("The length of the $(name) SOR time series data is $(length(SOR))
                but it should be should be equal to PRAS timesteps ($(timesteps))")
        end        

        MTTR > 0 || error("$(name) MTTR value is <= 0")

        return new(
            name,
            timesteps,
            region_name,
            installed_capacity,
            capacity,
            type,
            legacy,
            FOR,
            SOR,
            MTTR,
        )
    end
end

# Getter Functions

get_capacity(gen::Variable_Gen) =
    isnothing(gen.SOR) ?
    round.(Int, gen.capacity)' :
    round.(Int, gen.capacity .* (1 .-gen.SOR))'

get_category(gen::Variable_Gen) = "$(gen.legacy)|$(gen.type)"

get_type(gen::Variable_Gen) = gen.type
