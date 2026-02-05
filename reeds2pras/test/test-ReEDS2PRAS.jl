reedscase = joinpath(@__DIR__, "reeds_cases", "USA_VSC_2035")
solve_year = 2035
timesteps = 8760
weather_year = 2007

# ReEDS2PRAS System Generation with no kwargs
pras_sys_1 = R2P.reeds_to_pras(reedscase, solve_year, timesteps, weather_year, hydro_energylim = false, scheduled_outage = false);
path = R2P.ReEDSdatapaths(reedscase, solve_year)

@testset verbose = true "SystemModel" begin
    @test pras_sys_1 isa PRAS.SystemModel

    @testset "Load" begin
        # Load
        @test check_region_load_data(pras_sys_1)
    end

    @testset "Lines" begin
        # VSC Lines
        @test check_DC_region_in_pras_system(pras_sys_1, path)
        @test check_converter_capacity(pras_sys_1, path)

        # Other Lines
        @test check_line_capacities(pras_sys_1, path)
    end
    @testset "Resource Capacity" begin
        # Generators
        @test check_generator_capacities(pras_sys_1, path)
        @test check_storage_capacities(pras_sys_1, path)
    end

    @testset "Transition Probabilities" begin
        # Generators
        @test check_generator_outage_probabilities(pras_sys_1, path, weather_year, timesteps)

        # Storages
        @test check_storage_outage_probabilities(pras_sys_1, path, weather_year, timesteps)
        @test check_storage_recovery_probabilities(pras_sys_1)
    end
    
end

# ReEDS2PRAS System Generation with only scheduled outages
pras_sys_2 = R2P.reeds_to_pras(reedscase, solve_year, timesteps, weather_year, hydro_energylim = false, scheduled_outage = true);

@testset verbose = true "SystemModel-ScheduledOutage" begin
    @testset "Generator Capacities" begin
        @test check_scheduled_outage_generator_capacities(pras_sys_1, pras_sys_2)
    end

    @testset "Storage Energy Capacities" begin
        @test check_scheduled_outage_storage_capacities(pras_sys_1, pras_sys_2)
    end
    
end

# ReEDS2PRAS System Generation with only hydro energy limits
pras_sys_3 = R2P.reeds_to_pras(reedscase, solve_year, timesteps, weather_year, hydro_energylim = true, scheduled_outage = false);

@testset verbose = true "SystemModel-HydroEnergyLimits" begin
    @test length(pras_sys_3.generatorstorages.names) > 0
    @test length(pras_sys_3.generators.names) < length(pras_sys_1.generators.names) # Because we don't disaggregate and we have GeneratorStorages

    @testset "Inflow" begin
        @test check_hydro_energy_limits(pras_sys_3, path)
    end 
    @testset "Outage Probability" begin
        @test check_generatorstorage_outage_probabilities(pras_sys_3, path, weather_year, timesteps)
    end 
    #TODO : Should we check others (discharge_capacity, etc.?)? 
end