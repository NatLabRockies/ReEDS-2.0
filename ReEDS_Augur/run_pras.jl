#%% Imports
import ArgParse
import CSV
import DataFrames as DF
import Logging
import LoggingExtras
import Dates
import PRAS
try
    using Revise
catch e
    @warn "Error initializing Revise" exception=(e, catch_backtrace())
end

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
            help = "The weather year to start from, in [2007..2013]"
            arg_type = Int
            default = 2007
            required = true
        "--reeds2praspath"
            help = "Path to ReEDS2PRAS folder"
            arg_type = String
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
    sys = PRAS.SystemModel(pras_system_path)

    #%% Run PRAS
    short, flow, util, surplus = PRAS.assess(
        sys,
        PRAS.SequentialMonteCarlo(
            samples=args["samples"], threaded=true, verbose=true, seed=1),
        PRAS.Shortfall(),
        PRAS.Flow(),
        PRAS.Utilization(),
        PRAS.Surplus()
    )

    #%% Print some results for the entire modeled region to show it worked
    @info "LOLE is $(PRAS.LOLE(short)) event-h"
    @info "EUE is $(PRAS.EUE(short)) MWh"
    @info "NEUE is $(1e6 * PRAS.EUE(short).eue.estimate / sum(sys.regions.load)) ppm"

    #%% Print some more detailed results if debugging
    for (i, reg) in enumerate(sys.regions.names)
        @debug "$reg: LOLE is $(round(PRAS.LOLE(short,reg).lole.estimate)) event-h"
        @debug "$reg: EUE  is $(round(PRAS.EUE(short,reg).eue.estimate)) MWh"
        @debug "$reg: NEUE is $(round(
            1e6 * PRAS.EUE(short,reg).eue.estimate
            / sum(sys.regions.load[i,:])
        )) ppm\n\n"
    end

    #%% Record the outputs by region and timestep
    ## Units are:
    ## * LOLE: event-h
    ## * EUE: MWh
    ## * NEUE: fraction
    ## First for the whole modeled area (labeled as "USA" but if modeling a smaller
    ## region (speicified by GSw_Region) it will be for that modeled region)
    dfout = DF.DataFrame(
        h=sys.timestamps,
        USA_LOLE=[PRAS.LOLE(short,h).lole.estimate for h in sys.timestamps],
        USA_EUE=[PRAS.EUE(short,h).eue.estimate for h in sys.timestamps],
        USA_NEUE=[PRAS.EUE(short,h).eue.estimate / sum(sys.regions.load[:,j])
                  for (j,h) in enumerate(sys.timestamps)],
    )
    ## Now for each constituent region
    for (i,r) in enumerate(sys.regions.names)
        dfout[!, "$(r)_LOLE"] = [PRAS.LOLE(short,r,h).lole.estimate for h in sys.timestamps]
        dfout[!, "$(r)_EUE"] = [PRAS.EUE(short,r,h).eue.estimate for h in sys.timestamps]
        dfout[!, "$(r)_NEUE"] = [PRAS.EUE(short,r,h).eue.estimate / sum(sys.regions.load[i,j])
                                 for (j,h) in enumerate(sys.timestamps)]
    end

    #%% Write it
    if args["include_samples"] == 1
        outfile = replace(pras_system_path, ".pras"=>"-$(args["samples"]).csv")
    else
        outfile = replace(pras_system_path, ".pras"=>".csv")
    end
    CSV.write(outfile, dfout)
    @info("Wrote PRAS output to $(outfile)")

    #%%
    return dfout
end


#%% Main function
"""
    Run ReEDS2PRAS and PRAS
"""
function main(args::Dict)
    #%% Define some intermediate filenames
    if args["timesteps"] == 8760
        pras_system_path = joinpath(
            args["reedscase"],"ReEDS_Augur","PRAS",
            "PRAS_m$(args["solve_year"])i$(args["iteration"])_w$(args["weather_year"]).pras"
        )
    else
        pras_system_path = joinpath(
            args["reedscase"],"ReEDS_Augur","PRAS",
            "PRAS_$(args["solve_year"])i$(args["iteration"]).pras"
        )
    end

    #%% Set up the logger
    setup_logger(pras_system_path, args)
    @info "Running ReEDS2PRAS with the following inputs:"
    for (arg, val) in args
        @info "$arg  =>  $val"
    end

    #%% Run ReEDS2PRAS
    if (args["overwrite"] == 1) | ~isfile(pras_system_path)
        pras_system = ReEDS2PRAS.reeds_to_pras(
            args["reedscase"],
            args["solve_year"],
            args["timesteps"],
            args["weather_year"],
        )
        ### Save the PRAS system
        PRAS.savemodel(pras_system, pras_system_path)
        @info "PRAS model saved to $(pras_system_path)"
    end

    #%% Run PRAS
    if args["samples"] > 0
        @info "Running PRAS"
        dfout = run_pras(pras_system_path, args)
        #%%
        return dfout
    end
end


#%% Procedure
if abspath(PROGRAM_FILE) == @__FILE__
    # #%% Inputs for debugging
    # args = Dict(
    #     "reeds_path" => "/Users/pbrown/github2/ReEDS-2.0",
    #     "reedscase" => (
    #         "/Users/pbrown/github2/ReEDS-2.0/runs/"
    #         *"v20230328_prasM0_WECC_SP_sh4msp30_so1smPslaM"),
    #     "solve_year" => 2050,
    #     "weather_year" => 2007,
    #     "reeds2praspath" => "/Users/pbrown/github/ReEDS2PRAS",
    #     "samples" => 10,
    #     # "timesteps" => 8760,
    #     "timesteps" => 61320,
    #     "overwrite" => 1,
    #     "debug" => 0,
    # )

    #%% Parse the command line arguments
    args = parse_commandline()

    #%% Include ReEDS2PRAS
    include(joinpath(args["reeds2praspath"], "src", "ReEDS2PRAS.jl"))

    #%% Run it
    main(args)

    #%%
end
