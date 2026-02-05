# Check if you can open a file
function check_file(loc::String)
    io = try
        open(loc)
    catch
        nothing
    end

    if (isnothing(io))
        return nothing, false
    else
        return io, isopen(io)
    end
end

function run_checks(data::ReEDSdatapaths)
    augur_data_path = joinpath(data.ReEDSfilepath, "ReEDS_Augur", "augur_data")
    filepaths = [
        joinpath(augur_data_path, "cap_converter_$(string(data.year)).csv"),
        joinpath(augur_data_path, "charge_eff_$(string(data.year)).csv"),
        joinpath(augur_data_path, "discharge_eff_$(string(data.year)).csv"),
        joinpath(augur_data_path, "energy_cap_$(string(data.year)).csv"),
        joinpath(augur_data_path, "max_cap_$(string(data.year)).csv"),
        joinpath(augur_data_path, "max_unitsize_$(string(data.year)).csv"),
        joinpath(augur_data_path, "pras_load_$(string(data.year)).h5"),
        joinpath(augur_data_path, "pras_vre_gen_$(string(data.year)).h5"),
        joinpath(augur_data_path, "tran_cap_$(string(data.year)).csv"),
        joinpath(data.ReEDSfilepath, "inputs_case", "hydcapadj.csv"),
        joinpath(data.ReEDSfilepath, "inputs_case", "hydcf.csv"),
        joinpath(data.ReEDSfilepath, "inputs_case", "mttr.csv"),
        joinpath(data.ReEDSfilepath, "inputs_case", "outage_forced_hourly.h5"),
        joinpath(data.ReEDSfilepath, "inputs_case", "outage_forced_static.csv"),
        joinpath(data.ReEDSfilepath, "inputs_case", "outage_scheduled_hourly.h5"),
        joinpath(data.ReEDSfilepath, "inputs_case", "resources.csv"),
        joinpath(data.ReEDSfilepath, "inputs_case", "tech-subset-table.csv"),
        joinpath(data.ReEDSfilepath, "inputs_case", "unitdata.csv"),
        joinpath(data.ReEDSfilepath, "inputs_case", "unitsize.csv"),
    ]
    for filepath in filepaths
        io, file_exists = check_file(filepath)
        if (file_exists)
            close(io)
        else
            error("Missing required file for ReEDS2PRAS: $filepath")
        end
    end
end
