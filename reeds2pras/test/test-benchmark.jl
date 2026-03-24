@testset verbose = true "ReEDS2PRAS & PRAS Benchmark" begin
    # Running this benchmark:
    # Run this file first with the main branch and 
    # then the feature branch, record the reported mean time taken 
    # for both ReEDS2PRAS and PRAS, and the CONUS LOLE, nEUE output here 
    # while submitting pull request with the PR template

    # If making major changes to R2P model, increase number of MC samples used

    # Set up this test
    reedscase = joinpath(@__DIR__, "reeds_cases", "USA_VSC_2035")
    solve_year = 2035
    timesteps = 8760
    weather_year = 2007
    samples = 10
    seed = 1

    # ReEDS2PRAS Benchmarking
    bm_r2p = @btimed R2P.reeds_to_pras(reedscase, solve_year, timesteps, weather_year, hydro_energylim = true, scheduled_outage = true) setup = (reedscase=joinpath(@__DIR__, "reeds_cases", "USA_VSC_2035"); solve_year=2035; timesteps = 8760; weather_year = 2007);
    
    # PRAS Benchmarking
    bm_pras = @btimed assess(pras_sys, simulation, Shortfall()) setup = (pras_sys=R2P.reeds_to_pras(joinpath(@__DIR__, "reeds_cases", "USA_VSC_2035"), 2035, 8760, 2007, hydro_energylim = true, scheduled_outage = true); simulation = SequentialMonteCarlo(samples = 10, seed = 1));
    
    # Print Results
    pras_sys =  R2P.reeds_to_pras(reedscase, solve_year, timesteps, weather_year, hydro_energylim = true, scheduled_outage = true);
    simulation = SequentialMonteCarlo(samples = samples, seed = seed)
    shortfall = assess(pras_sys, simulation, Shortfall())

    LOLE = PRAS.LOLE(shortfall[1]).lole.estimate
    EUE = PRAS.EUE(shortfall[1]).eue.estimate
    nEUE = PRAS.NEUE(shortfall[1]).neue.estimate

    @show "ReEDS2PRAS Benchmark Time : time - $(bm_r2p.time), gctime - $(bm_r2p.gctime); PRAS Benchmark Time : time - $(bm_pras.time), gctime - $(bm_pras.gctime), LOLE: $(LOLE), EUE: $(EUE), NEUE :$(nEUE)"
   
end