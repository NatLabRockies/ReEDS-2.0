"""
    Creates a datapath for a given ReEDS model year. Used as a parameter for other
    functions in order to access correctly dated input files.

    Parameters
    ----------
    x : String
        Path to ReEDS case (e.g. "~/github/ReEDS-2.0/runs/name_of_reeds_case")
    y : Int
        ReEDS model year

    Returns
    -------
    A new object with filepath and valid year parameters
"""
struct ReEDSdatapaths
    ReEDSfilepath::String
    year::Int

    function ReEDSdatapaths(x, y)
        return new(x, y)
    end
end

"Includes functions used for loading ReEDS data"

"""
    Loop through the vector and replace any '*' present in the elements with
    the text between the asterisk, excluding the '_'.

    Parameters
    ----------
    input_vec : Vector{<:AbstractString}
        Vector of strings that need to be parsed

    Returns
    -------
    input_vec : Vector{<:AbstractString}
        Vector of strings which has been cleaned of '*'
"""
function clean_names!(input_vec::Vector{<:AbstractString})
    for (idx, a) in enumerate(input_vec)
        if occursin("*", a)
            input_vec[idx] = match(r"\*([a-zA-Z]+-*[a-zA-Z]*)_*", a)[1]
        end
    end
    return input_vec
end

"""
    Loads the EIA-NEMS Generator Database from a given ReEDS directory.

    Parameters
    ----------
  
    Returns
    -------
    unitdata : DataFrame
        A DataFrame containing the EIA-NEMS Generator Database data.
"""
function get_unitdata(data::ReEDSdatapaths)
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "unitdata.csv")
    return DataFrames.DataFrame(CSV.File(filepath))
end

"""
    Loads an .h5 file from the given file path, containing Electrical Demand
    data from the indicated year.

    Parameters
    ----------
    data : ReEDSdatapaths
        An instance of ReEDSdatapaths with the necessary arguments set.

    Returns
    -------
    HDF5.h5read(filepath, "data")
        A readout of the Augur load h5 file associated with the given ReEDS
        filepath and year.

"""
function get_load_file(data::ReEDSdatapaths)
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "pras_load_$(string(data.year)).h5",
    )
    columns = HDF5.h5read(filepath, "columns")
    data = HDF5.h5read(filepath, "data")
    df = DataFrames.DataFrame(transpose(data), columns)
    return df
end

"""
    This function reads a hdf5 file from the ReEDS Augur directory, based on
    the year provided in the ReEDSdatapaths struct.

    Parameters
    ----------
    data : ReEDSdatapaths
        Struct containing the `ReEDSfilepath` and a year, indicating which .h5
        file should be read.

    Returns
    -------
    The requested ``hdf5`` as a data frame.
"""
function get_vg_cf_data(data::ReEDSdatapaths)
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "pras_vre_gen_$(string(data.year)).h5",
    )
    columns = HDF5.h5read(filepath, "columns")
    data = HDF5.h5read(filepath, "data")
    df = DataFrames.DataFrame(transpose(data), columns)
    return df
end

"""
    Get tech-dependent MTTR.

    Parameters
    ----------
    data : ReEDSdatapaths
        Struct containing relevant datapaths and year from which to extract
        the data.

    Returns
    -------
    Dictionary
        tech => MTTR [hours]
"""
function get_MTTR_data(data::ReEDSdatapaths)
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "mttr.csv")
    df = DataFrames.DataFrame(CSV.File(filepath))
    return Dict(df[!, "tech"] .=> df[!, "hours"])
end


"""
    Get region-dependent max unit size [MW] as dictionary
"""
function get_max_unitsize(data::ReEDSdatapaths)
    filepath = joinpath(
        data.ReEDSfilepath, "ReEDS_Augur", "augur_data",
        "max_unitsize_$(string(data.year)).csv"
    )
    df = DataFrames.DataFrame(CSV.File(filepath))
    return Dict(df[!, "r"] .=> df[!, "mw"])
end


"""
    Get the forced outage data from the augur files.

    Parameters
    ----------
    data : ReEDSdatapaths
        Struct containing relevant datapaths and year from which to extract
        the data.

    Returns
    -------
    DataFrames.DataFrame
        Dataframe containing the forced outage data.
"""
function get_forced_outage_data(data::ReEDSdatapaths)
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "outage_forced_static.csv")
    df = DataFrames.DataFrame(CSV.File(filepath, header = false))
    return DataFrames.rename!(df, ["ResourceType", "FOR"])
end

"""
    Get the valid resources from {case}/inputs_case/resources.csv

    Parameters
    ----------
    data : ReEDSdatapaths
        Struct containing ReEDS filepaths and year

    Returns
    -------
    DataFrames.DataFrame
        A DataFrame containing the valid resources of the ReEDS case
"""
function get_valid_resources(data::ReEDSdatapaths)
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "resources.csv")
    return DataFrames.DataFrame(CSV.File(filepath))
end

"""
    This function gets the technology types from {case}/inputs_case/tech-subset-table.csv

    Arguments
    ---------
    data : ReEDSdatapaths
        A struct containing paths and dates related to ReEDS analyses.

    Returns
    -------
    DataFrames.DataFrame
        The technology type table in the form of a DataFrames object.
"""
function get_technology_types(data::ReEDSdatapaths)
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "tech-subset-table.csv")
    return DataFrames.DataFrame(CSV.File(filepath))
end

"""
    Gets line capacity data for the given ReEDS database.

    Parameters
    ----------
    data : ReEDSdatapaths
        Contains the filepath of data and year of analysis

    Returns
    -------
    DataFrame
        A dataframe with transmission capacity data; assumes this file has been
        formatted by ReEDS
"""
function get_line_capacity_data(data::ReEDSdatapaths)
    #assumes this file has been formatted by ReEDS to be PRM line capacity data
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "tran_cap_$(string(data.year)).csv",
    )
    return DataFrames.DataFrame(CSV.File(filepath))
end

"""
    Get the converter capacity data associated with the given ReEDSdatapaths
    object.

    Parameters
    ----------
    data : ReEDSdatapaths)
        A ReEDSdatapaths object containing the relevant file paths and year.

    Returns
    -------
    DataFrames.DataFrame
        The DataFrame of the converter capacity data for the given year.
"""
function get_converter_capacity_data(data::ReEDSdatapaths)
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "cap_converter_$(string(data.year)).csv",
    )
    return DataFrames.DataFrame(CSV.File(filepath))
end

"""
    Returns a DataFrame containing the Annual Technology Baseline
    default unit size for the ReEDSdatapaths object.

    Parameters
    ----------
    data : ReEDSdatapaths
        An object containing the filepaths to the ReEDS input files.

    Returns
    -------
    DataFrame
        A DataFrame containing the default unit size mapping.

    Raises
    ------
    Error
        If no table of unit size mapping is found.

"""
function get_unitsize_mapping(data::ReEDSdatapaths)
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "unitsize.csv")
    return DataFrames.DataFrame(CSV.File(filepath))
end

"""
    Returns a DataFrame containing the installed capacity of generators for a
    given year, read from {case}/ReEDS_Augur/augur_data/max_cap_{year}.csv.

    Parameters
    ----------
    data : ReEDSdatapaths
        A ReEDSdatapaths object containing the year and filepath.

    Returns
    -------
    DataFrame
        A DataFrame containing the installed capacity data.

    Raises
    ------
    Error
        If the year does not have generator installed capacity data.
"""
function get_ICAP_data(data::ReEDSdatapaths)
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "max_cap_$(string(data.year)).csv",
    )
    return DataFrames.DataFrame(CSV.File(filepath))
end

"""
    Returns DataFrames containing hydroelectric plants capacity factors

    Parameters
    ----------
    data : ReEDSdatapaths
        A ReEDSdatapaths object containing the year and filepath.

    Returns
    -------
    hydcf: DataFrame
        A DataFrame containing the seasonal capacity factors for both 
        dispatchable and non-dispatchable hydroelectric plants, subsetted
        to the required output year. 
    
    hydcapadj: DataFrame
        A DataFrame containing seasonal capacity adjustment factors for
        dispatchable hydroelectric plants which limits the maximum hourly 
        dispatch (MW) in each season.

    Raises
    ------
    Error
        If the filepath for the for the two files do not exist.
"""
function get_hydro_data(data::ReEDSdatapaths)
    filepath_cf = joinpath(data.ReEDSfilepath, "inputs_case", "hydcf.csv")
    hydcf = DataFrames.DataFrame(CSV.File(filepath_cf))

    # Rename plant types as techtypes and capacity are lowercase
    DataFrames.rename!(hydcf, [:"*i"] .=> [:i])
    hydcf.i = lowercase.(hydcf.i)
    # Subset to ReEDS model year
    hydcf = filter(x -> x.t == data.year, hydcf)

    filepath_capadj = joinpath(data.ReEDSfilepath, "inputs_case", "hydcapadj.csv")

    hydcapadj = DataFrames.DataFrame(CSV.File(filepath_capadj))

    # Rename plant types as techtypes and capacity are lowercase
    DataFrames.rename!(hydcapadj, [:"*i"] .=> [:i])
    hydcapadj.i = lowercase.(hydcapadj.i)

    return hydcf, hydcapadj
end

"""
    Returns a DataFrame containing the installed storage energy capacity data
    for the year specified in the ReEDSdatapaths object.

    Parameters
    ----------
    data : ReEDSdatapaths
        An object containing paths to ReEDS data.

    Returns
    -------
    DataFrame
        DataFrame containing storage energy capacity data

    Raises
    ------
    Error
        If the filepath for the specified year does not exist.
"""
function get_storage_energy_capacity_data(data::ReEDSdatapaths)
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "energy_cap_$(string(data.year)).csv",
    )
    return DataFrames.DataFrame(CSV.File(filepath))
end

"""
    Returns a DataFrame containing the hourly planned outage data,
    read from reeds2pras/test/reeds_cases/Pacific/inputs_case

    Parameters
    ----------
    data : ReEDSdatapaths
        An object containing paths to ReEDS data.

    Returns
    -------
    DataFrame
        DataFrame the hourly scheduled outages

    Raises
    ------
    Error
        If the filepath for the specified year does not exist.
"""
function get_hourly_scheduled_outage_data(data::ReEDSdatapaths)
    filepath = joinpath(
        data.ReEDSfilepath,
        "inputs_case",
        "outage_scheduled_hourly.h5",
    )

    return DataFrames.DataFrame(
        HDF5.h5read(filepath, "data")',
        HDF5.h5read(filepath, "columns"),
    )
end

"""
    Get the hourly forced outage data from the augur files.

    Parameters
    ----------
    data : ReEDSdatapaths
        Struct containing relevant datapaths and year from which to extract
        the data.

    Returns
    -------
    DataFrames.DataFrame
        Dataframe containing the hourly forced outage data.
"""
function get_hourly_forced_outage_data(data::ReEDSdatapaths)
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "outage_forced_hourly.h5")
    forcedoutage_hourly = DataFrames.DataFrame(
        HDF5.h5read(filepath, "data")',
        HDF5.h5read(filepath, "columns"),
    )
    return forcedoutage_hourly
end

# Struct to define monthhour values
mutable struct monthhour
    month::String
    numhrs::Int64
    cumsum::Int64
    slice::UnitRange{Int64}

    # Inner Constructors & Checks
    function monthhour(
        month = "month",
        numhrs = 10,
        cumsum = 0,
        slice = range(1, length = 10),
    )
        return new(month, numhrs, cumsum, slice)
    end
end

# Functions to augment collection of monthour
function cumsum!(collection::Vector{monthhour})
    sum = 0
    for element in collection
        sum = sum + element.numhrs
        element.cumsum = sum
    end
end

function addslices!(collection::Vector{monthhour})
    for element in collection
        element.slice = (element.cumsum - element.numhrs + 1):(element.cumsum)
    end
end

# Generating necessary data 
function monhours()
    monthours = monthhour[]
    start_date = Dates.Date("2021-01", "yyyy-mm")
    for i in range(0, length = 12)
        new_date = start_date + Dates.Month(i)
        push!(
            monthours,
            monthhour(
                uppercase(Dates.monthabbr(i + 1)),
                Dates.daysinmonth(new_date) * 24,
            ),
        )
    end

    cumsum!(monthours)
    addslices!(monthours)

    return monthours
end
