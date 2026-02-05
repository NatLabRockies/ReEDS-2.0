#%% Imports
import ArgParse
import DataFrames
import Logging
import LoggingExtras
import Dates
import PRAS
import HDF5

const DF = DataFrames

#%% Functions
"""
    Parse command line arguments for use with ReEDS2PRAS and PRAS
"""
function parse_commandline()
    s = ArgParse.ArgParseSettings()

    @ArgParse.add_arg_table s begin
        "--reeds_path"
            help = "Path to ReEDS-2.0 folder"
            arg_type = String
            required = true
        "--reedscase"
            help = "Path to ReEDS run (usually .../ReEDS-2.0/runs/{casename})"
            arg_type = String
            required = true
        "--solve_year"
            help = "ReEDS solve year (usually in [2020..2050])"
            arg_type = Int
            required = true
        "--weather_year"
            help = "The weather year to start from, in [2007..2013,2016..2023]"
            arg_type = Int
            default = 2007
            required = true
        "--samples"
            help = "Number of Monte Carlo samples to run in PRAS"
            arg_type = Int
            default = 10
            required = false
        "--timesteps"
            help = "Number of hourly timesteps to use"
            arg_type = Int
            default = 61320
            required = false
        "--hydro_energylim"
            help = "Model hydropower as an energy-limited resource"
            arg_type = Int
            default = 0
            required = false
        "--scheduled_outage"
            help = "Include monthly scheduled outage"
            arg_type = Int
            default = 0
            required = false            
        "--write_flow"
            help = "Write the hourly interface flows"
            arg_type = Int
            default = 0
            required = false
        "--write_surplus"
            help = "Write the hourly surplus"
            arg_type = Int
            default = 0
            required = false
        "--write_energy"
            help = "Write the hourly storage energy"
            arg_type = Int
            default = 0
            required = false
        "--write_shortfall_samples"
            help = "Write the sample-level shortfall"
            arg_type = Int
            default = 0
            required = false
        "--write_availability_samples"
            help = "Write the sample-level generator and storage availability"
            arg_type = Int
            default = 0
            required = false
        "--iteration"
            help = "Solve-year iteration number (only used in file label)"
            arg_type = Int
            default = 0
            required = false
        "--overwrite"
            help = "Overwrite an existing .pras file"
            arg_type = Int
            default = 1
            required = false
        "--include_samples"
            help = "Include the number of samples in the output .csv filename"
            arg_type = Int
            default = 0
            required = false
        "--pras_agg_ogs_lfillgas"
            help = "Aggregate existing o-g-s and landfill gas using size for new units"
            arg_type = Int
            default = 0
            required = false
        "--pras_existing_unit_size"
            help = "Use average existing unit size by (tech,region) when disaggregating new units"
            arg_type = Int
            default = 1
            required = false
        "--pras_max_unitsize_prm"
            help = "Cap the upper bound of disaggregated unit size by zone at the zonal PRM in MW"
            arg_type = Int
            default = 1
            required = false
        "--pras_seed"
            help = "Random seed for PRAS (positive integer; ignored and set randomly if 0)"
            arg_type = Int
            default = 1
            required = false
        "--debug"
            help = "Log debug-level messages"
            arg_type = Int
            default = 0
            required = false
    end
    return ArgParse.parse_args(s)
end

"""
    Set up logging to file and console
"""
function setup_logger(pras_system_path::String, args::Dict)
    if ~isnothing(pras_system_path)
        logfile = replace(pras_system_path, ".pras"=>".log")

        if args["debug"] == 1
            logfilehandle = LoggingExtras.MinLevelLogger(
                LoggingExtras.FileLogger(logfile; append=true),
                Logging.Debug)
        else
            logfilehandle = LoggingExtras.MinLevelLogger(
                LoggingExtras.FileLogger(logfile; append=true),
                Logging.Info)
        end

        logger = LoggingExtras.TeeLogger(
            Logging.global_logger(),
            logfilehandle
        )

        ### https://github.com/JuliaLogging/LoggingExtras.jl#add-timestamp-to-all-logging
        timestamp_logger(logger) = LoggingExtras.TransformerLogger(logger) do log
            merge(
                log,
                (; message = "$(Dates.format(Dates.now(), "yyyy-mm-dd HH:MM:SS")) | $(log.message)")
            )
        end

        Logging.global_logger(timestamp_logger(logger))
    end
end

"""
    Simple PRAS analysis.

    Parameters
    ----------

    Returns
    -------
"""
function run_pras(pras_system_path::String, args::Dict)
    #%% Load the system model
    @info "Parsing PRAS System ..."
    sys = PRAS.SystemModel(pras_system_path);

    #%% Specify the results to save
    resultspec = Dict{String,Any}("short" => PRAS.Shortfall())
    if args["write_flow"] == 1
        resultspec["flow"] = PRAS.Flow()
    end
    if args["write_surplus"] == 1
        resultspec["surplus"] = PRAS.Surplus()
    end
    if args["write_energy"] == 1
        resultspec["energy"] = PRAS.StorageEnergy()
    end
    if args["write_shortfall_samples"] == 1
        resultspec["short_samples"] = PRAS.ShortfallSamples()
    end
    if args["write_availability_samples"] == 1
        resultspec["avail_gen"] = PRAS.GeneratorAvailability()
        resultspec["avail_stor"] = PRAS.StorageAvailability()
        resultspec["avail_genstor"] = PRAS.GeneratorStorageAvailability()
        resultspec["energy_samples"] = PRAS.StorageEnergySamples()
    end

    #%% Run PRAS
    if args["pras_seed"] > 0
        method = PRAS.SequentialMonteCarlo(
            samples=args["samples"], threaded=true, verbose=true, seed=args["pras_seed"])
    else
        method = PRAS.SequentialMonteCarlo(
            samples=args["samples"], threaded=true, verbose=true)
    end
    results_tuple = PRAS.assess(sys, method, values(resultspec)...)
    results = Dict{String,Any}(zip(keys(resultspec), results_tuple))

    #%% Print some results for the entire modeled region to show it worked
    @info "$(PRAS.LOLE(results["short"])) event-h"
    @info "$(PRAS.EUE(results["short"])) MWh"
    @info "NEUE = $(1e6 * PRAS.EUE(results["short"]).eue.estimate / sum(sys.regions.load)) ppm"

    ## Filter out DC regions used for VSC HVDC transmission
    regions = [r for r in sys.regions.names if !(occursin("|", r))]

    #%% Print some more detailed results if debugging
    for (i, reg) in enumerate(regions)
        @debug "$reg: $(round(PRAS.LOLE(results["short"],reg).lole.estimate)) event-h"
        @debug "$reg: $(round(PRAS.EUE(results["short"],reg).eue.estimate)) MWh"
        @debug "$reg: NEUE = $(round(
            1e6 * PRAS.EUE(results["short"],reg).eue.estimate
            / sum(sys.regions.load[i,:])
        )) ppm\n\n"
    end

    #%% Record the EUE and LOLE outputs by region and timestep
    ## Units are:
    ## * LOLE: event-h
    ## * EUE: MWh
    ## First for the whole modeled area (labeled as "USA" but if modeling a smaller
    ## region (speicified by GSw_Region) it will be for that modeled region)
    dfout = DF.DataFrame(
        USA_LOLE=[PRAS.LOLE(results["short"],h).lole.estimate for h in sys.timestamps],
        USA_EUE=[PRAS.EUE(results["short"],h).eue.estimate for h in sys.timestamps],
    )
    ## Now for each constituent region
    for (i,r) in enumerate(regions)
        dfout[!, "$(r)_LOLE"] = [PRAS.LOLE(results["short"],r,h).lole.estimate for h in sys.timestamps]
        dfout[!, "$(r)_EUE"] = [PRAS.EUE(results["short"],r,h).eue.estimate for h in sys.timestamps]
    end

    #%% Write it
    if args["include_samples"] == 1
        outfile = replace(pras_system_path, ".pras"=>"-$(args["samples"]).h5")
    else
        outfile = replace(pras_system_path, ".pras"=>".h5")
    end
    HDF5.h5open(outfile, "w") do f
        for column in DF.names(dfout)
            f[column, compress=4] = convert(Array, dfout[!, column])
        end
    end
    @info("Wrote PRAS EUE and LOLE to $(outfile)")

    #%%### Record more operational details if desired

    ### Flow
    if args["write_flow"] == 1
        dfflow = DF.DataFrame()
        for i in results["flow"].interfaces
            ## Flow results are tuples of (mean, standard deviation). Keep the mean.
            dfflow[!, "$(i)"] = [results["flow"][i,h][1] for h in sys.timestamps]
        end
        ## Write it
        flowfile = replace(outfile, ".h5"=>"-flow.h5")
        HDF5.h5open(flowfile, "w") do f
            for column in DF._names(dfflow)
                f["$column", compress=4] = convert(Array, dfflow[!, column])
            end
        end
        @info("Wrote PRAS flow to $(flowfile)")
    end

    ### Surplus
    if args["write_surplus"] == 1
        dfsurplus = DF.DataFrame()
        for r in regions
            ## Surplus results are tuples of (mean, standard deviation). Keep the mean.
            dfsurplus[!, "$(r)"] = [results["surplus"][r,h][1] for h in sys.timestamps]
        end
        ## Write it
        surplusfile = replace(outfile, ".h5"=>"-surplus.h5")
        HDF5.h5open(surplusfile, "w") do f
            for column in DF._names(dfsurplus)
                f["$column", compress=4] = convert(Array, dfsurplus[!, column])
            end
        end
        @info("Wrote PRAS surplus to $(surplusfile)")
    end
    ### Storage energy
    if args["write_energy"] == 1
        dfenergy = DF.DataFrame()
        for i in sys.storages.names
            ## Energy results are tuples of (mean, standard deviation). Keep the mean.
            dfenergy[!, strip("$(i)", '_')] = [results["energy"][i,h][1] for h in sys.timestamps]
        end
        ## Write it
        energyfile = replace(outfile, ".h5"=>"-energy.h5")
        HDF5.h5open(energyfile, "w") do f
            for column in DF._names(dfenergy)
                f["$column", compress=4] = convert(Array, dfenergy[!, column])
            end
        end
        @info("Wrote PRAS storage energy to $(energyfile)")
    end

    ### Sample-level shortfall
    if args["write_shortfall_samples"] == 1
        dictshort = Dict(s => DF.DataFrame() for s = 1:args["samples"])
        for s in range(1, args["samples"])
            dictshort[s] = DF.DataFrame(
                transpose(getindex.(results["short_samples"][:, :], s)),
                sys.regions.names
            )
            # subset to regions (filter out DC regions) 
            dictshort[s] = dictshort[s][:,findall(regions .∈ Ref(sys.regions.names))]
        end
        ## Write it
        shortfile = replace(outfile, ".h5"=>"-shortfall_samples.h5")
        HDF5.h5open(shortfile, "w") do f
            ## Create a group for each sample. Within each group, write an array for each region.
            for s in range(1, args["samples"])
                HDF5.create_group(f, "$s")
                for column in DF._names(dictshort[s])
                    f["$s"]["$column", compress=4] = convert(Array, dictshort[s][!, column])
                end
            end
        end
        @info("Wrote PRAS shortfall by sample to $(shortfile)")
    end

    ### Sample-level generator and storage availability
    if args["write_availability_samples"] == 1
        dictavail = Dict(s => DF.DataFrame() for s = 1:args["samples"])
        for s in range(1, args["samples"])
            dictavail[s] = hcat(
                DF.DataFrame(
                    transpose(getindex.(results["avail_gen"][:, :], s)),
                    strip.(results["avail_gen"].generators, '_')
                ),
                DF.DataFrame(
                    transpose(getindex.(results["avail_stor"][:, :], s)),
                    strip.(results["avail_stor"].storages, '_')
                ),
                DF.DataFrame(
                    transpose(getindex.(results["avail_genstor"][:, :], s)),
                    strip.(results["avail_genstor"].generatorstorages, '_')
                ),
            )
        end
        ## Write it
        availabilityfile = replace(outfile, ".h5"=>"-avail.h5")
        HDF5.h5open(availabilityfile, "w") do f
            ## Create a group for each sample. Within each group, write an array for each unit.
            for s in range(1, args["samples"])
                HDF5.create_group(f, "$s")
                for column in DF._names(dictavail[s])
                    f["$s"]["$column", compress=4] = convert(Array, dictavail[s][!, column])
                end
            end
        end
        @info("Wrote PRAS unit availability to $(availabilityfile)")
        ### Same for storage energy by sample
        dictstoravail = Dict(s => DF.DataFrame() for s = 1:args["samples"])
        for s in range(1, args["samples"])
            dictstoravail[s] = DF.DataFrame(
                transpose(getindex.(results["energy_samples"][:, :], s)),
                strip.(results["energy_samples"].storages, '_')
            )
        end
        ## Write it
        energysamplesfile = replace(outfile, ".h5"=>"-energy_samples.h5")
        HDF5.h5open(energysamplesfile, "w") do f
            for s in range(1, args["samples"])
                HDF5.create_group(f, "$s")
                for column in DF._names(dictstoravail[s])
                    f["$s"]["$column", compress=4] = convert(Array, dictstoravail[s][!, column])
                end
            end
        end
        @info("Wrote PRAS storage energy by sample to $(energysamplesfile)")
    end

    #%%
    return dfout
end


#%% Main function
"""
    Run ReEDS2PRAS and PRAS
"""
function main(args::Dict)
    #%% Define some intermediate filenames
    pras_system_path = joinpath(
        args["reedscase"],"ReEDS_Augur","PRAS",
        "PRAS_$(args["solve_year"])i$(args["iteration"]).pras"
    )

    #%% Set up the logger
    setup_logger(pras_system_path, args)
    @info "Julia version: $(VERSION)"
    @info "Julia executable: $(joinpath(Sys.BINDIR, "julia"))"
    @info "Running ReEDS2PRAS with the following inputs:"
    for (arg, val) in args
        @info "$arg  =>  $val"
    end

    #%% Run ReEDS2PRAS
    if (args["overwrite"] == 1) | ~isfile(pras_system_path)
        ### Create and save the PRAS system
        ## Could use compression_level={integer} here but it doesn't really help
        PRAS.savemodel(
            ReEDS2PRAS.reeds_to_pras(
                args["reedscase"],
                args["solve_year"],
                args["timesteps"],
                args["weather_year"],
                # Boolean switches: == to convert from integer to boolean
                args["scheduled_outage"] == 1,
                args["hydro_energylim"] == 1,
                args["pras_agg_ogs_lfillgas"] == 1,
                args["pras_existing_unit_size"] == 1,
                args["pras_max_unitsize_prm"] == 1,
            ),
            pras_system_path,
            verbose=true,
        )
        @info "Finished ReEDS2PRAS"
    end

    #%% Run PRAS
    if args["samples"] > 0
        @info "Running PRAS"
        dfout = run_pras(pras_system_path, args)
        @info "Finished PRAS"
        #%%
        return dfout
    end
end


#%% Procedure
if abspath(PROGRAM_FILE) == @__FILE__
    #%% Inputs for debugging
    # julia --project=/path/to/ReEDS-2.0 --threads=1
    # args = Dict(
    #     "reeds_path" => "/path/to/ReEDS-2.0",
    #     "reedscase" => (
    #         "/path/to/ReEDS-2.0/runs/"
    #         *"runname"),
    #     "solve_year" => 2035,
    #     "weather_year" => 2007,
    #     "samples" => 10,
    #     "iteration" => 0,
    #     "timesteps" => 131400,
    #     "hydro_energylim" => 1,
    #     "write_flow" => 0,
    #     "write_surplus" => 0,
    #     "write_energy" => 0,
    #     "write_shortfall_samples" => 1,
    #     "write_availability_samples" => 0,
    #     "overwrite" => 1,
    #     "debug" => 0,
    #     "include_samples" => 0,
    #     "scheduled_outage" => 0,
    #     "pras_agg_ogs_lfillgas" => 0,
    #     "pras_existing_unit_size" => 1,
    #     "pras_max_unitsize_prm" => 1,
    #     "pras_seed" => 1,
    # )
    # reedscase = args["reedscase"]
    # solve_year = args["solve_year"]
    # timesteps = args["timesteps"]
    # weather_year = args["weather_year"]
    # include(joinpath(args["reeds_path"], "reeds2pras", "src", "ReEDS2PRAS.jl"))

    #%% Parse the command line arguments
    args = parse_commandline()

    #%% Include ReEDS2PRAS
    include(joinpath(args["reedscase"], "reeds2pras", "src", "ReEDS2PRAS.jl"))

    #%% Run it
    main(args)

    #%%
end
