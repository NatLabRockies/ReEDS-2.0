abstract type Storage end

# Getter Functions

get_name(stor::Storage) = stor.name

get_type(stor::Storage) = stor.type

get_legacy(stor::Storage) = stor.legacy

get_energy_capacity(stor::Storage) = permutedims(round.(Int, stor.energy_cap .* (1 .-stor.SOR)))

get_charge_efficiency(stor::Storage) = fill(stor.charge_eff, 1, stor.timesteps)

get_discharge_efficiency(stor::Storage) = fill(stor.discharge_eff, 1, stor.timesteps)

get_carryover_efficiency(stor::Storage) = fill(stor.carryover_eff, 1, stor.timesteps)

# Helper Functions
get_outage_rate(stor::Storage) = outage_to_rate(stor.FOR, stor.MTTR)

function get_λ(stor::Storage)
    λ = getfield(get_outage_rate(stor), :λ)
    if (isa(λ, Float64))
        out = fill(λ, 1, stor.timesteps)
    else
        out = reshape(λ, 1, :)
    end
    return out
end

get_μ(stor::Storage) = fill(getfield(get_outage_rate(stor), :μ), 1, stor.timesteps)

get_category(stor::Storage) = "$(stor.legacy)|$(stor.type)"

"""
    This function searches an array stors of type Vector{<:Storage} for
    storages located in a specific region reg_name. First, it filters the array
    for storages with a region_name field equal to the region name given. If no
    such storages exist, a warning is issued and an empty array of type
    Storage[] is returned. Otherwise, an array containing all the storages from
    this region is returned.

    Parameters
    ----------
    stors : Vector{<:Storage}
        An array of instances of type Storage.
    reg_name : String
        The name of the region to search for in storages.

    Returns
    -------
    reg_stors : Vector{<:Storage}
        An array of Storage instances found in the specified region reg_name.
"""
function get_storages_in_region(stors::Vector{<:Storage}, reg_name::String)
    reg_stors = filter(stor -> stor.region_name == reg_name, stors)
    if isempty(reg_stors)
        @debug "No storages in region: $(reg_name)"
        return Storage[]
    else
        return reg_stors
    end
end

get_storages_in_region(stors::Vector{<:Storage}, reg::Region) =
    get_storages_in_region(stors, reg.name)

"""
    Get the storage objects which match a given legacy ('Existing' or 'New').

    Parameters
    ----------
    stors: Vector{<:Storage}
        The array of storage objects.
    leg: str
        Legacy of the storage objects. Accepted values are 'Existing' and
        'New'.

    Returns
    -------
    leg_stors: <:Storage
        A subset of ``stors`` that has matching legacy.
        Returns an empty array if there is no match.
"""
function get_legacy_storages(stors::Vector{<:Storage}, leg::String)
    leg in ["Existing", "New"] || error("Unidentified legacy passed")

    leg_stors = filter(stor -> stor.legacy == leg, stors)
    if isempty(leg_stors)
        @debug "No storages with legacy: $(leg)"
        return Storage[]
    else
        return leg_stors
    end
end
