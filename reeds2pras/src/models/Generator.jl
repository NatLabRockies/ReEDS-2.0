abstract type Generator end

# Getter Functions
get_name(gen::Generator) = gen.name

get_legacy(gen::Generator) = gen.legacy

# Helper Functions
get_outage_rate(gen::Generator) = outage_to_rate(gen.FOR, gen.MTTR)

function get_λ(gen::Generator)
    λ = getfield(get_outage_rate(gen), :λ)
    if (isa(λ, Float64))
        out = fill(λ, 1, gen.timesteps)
    else
        out = reshape(λ, 1, :)
    end
    return out
end

get_μ(gen::Generator) = fill(getfield(get_outage_rate(gen), :μ), 1, gen.timesteps)

function get_generators_in_region(gens::Vector{<:Generator}, reg_name::String)
    reg_gens = filter(gen -> gen.region_name == reg_name, gens)
    if isempty(reg_gens)
        @warn "No generators in region: $(reg_name)"
        return Generator[]
    else
        return reg_gens
    end
end

get_generators_in_region(gens::Vector{<:Generator}, reg::Region) =
    get_generators_in_region(gens, reg.name)

function get_legacy_generators(gens::Vector{<:Generator}, leg::String)
    leg in ["Existing", "New"] || error("Unidentified legacy passed")

    leg_gens = filter(gen -> gen.legacy == leg, gens)
    if isempty(leg_gens)
        @warn "No generators with legacy: $(leg)"
        return Generator[]
    else
        return leg_gens
    end
end
