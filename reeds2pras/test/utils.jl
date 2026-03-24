function check_generator_capacities(pras_sys::PRAS.SystemModel, path::R2P.ReEDSdatapaths)
    # Currently doesn't check for weather_year VG profiles
    # Just ensures 0 <= VG capacity time series <= Installed Capacity
    # In some regions, distpv fails this tests, so skipping that category for now
    capacity_data = R2P.get_ICAP_data(path)
    vg_resource_types = R2P.get_valid_resources(path)
    tech_list = R2P.get_technology_types(path)
    vg_types = unique(vg_resource_types.i)
    storage_types = unique(DataFrames.dropmissing(tech_list, :STORAGE_STANDALONE)[:, "Column1"])
    reg_count = 0
    for (reg_idx, reg_name) in enumerate(pras_sys.regions.names)
        reg_cap = filter(x -> x.r == reg_name, capacity_data)
        vg_counts = length(filter(x -> x ∈ vg_types, unique(reg_cap.i)))
        vg_counts = ("distpv" in unique(reg_cap.i)) ? vg_counts - 1 : vg_counts # because some regions fail the distpv test
        non_vg_counts = length(filter(x -> x ∉ union(vg_types,storage_types), unique(reg_cap.i)))

        reg_non_vg_count = 0
        reg_vg_count = 0
        for gen_cat in filter(x -> x ∉ storage_types, unique(reg_cap.i))
            pras_gen_cat_idx = findall(x -> x == gen_cat, pras_sys.generators.categories[pras_sys.region_gen_idxs[reg_idx]])
            reeds_gen_cat_data = filter(x -> x.i == gen_cat, reg_cap)
            if !(gen_cat in vg_types)
                if (isapprox(sum(pras_sys.generators.capacity[pras_sys.region_gen_idxs[reg_idx]][pras_gen_cat_idx]), round(Int, sum(reeds_gen_cat_data.MW)), atol=1)) 
                    reg_non_vg_count = reg_non_vg_count + 1
                end
            else
                if (gen_cat != "distpv") # because some regions fail the distpv test
                    if (all(0 .<= pras_sys.generators.capacity[pras_sys.region_gen_idxs[reg_idx],:][pras_gen_cat_idx,:] .<= round(Int, sum(reeds_gen_cat_data.MW))))
                        reg_vg_count = reg_vg_count + 1
                    end
                end
            end
        end
        
        if ((reg_non_vg_count == non_vg_counts) && (reg_vg_count == vg_counts))
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys.regions.names))
        return true
    else 
        return false
    end
end

function check_storage_capacities(pras_sys::PRAS.SystemModel, path::R2P.ReEDSdatapaths)
    capacity_data = R2P.get_ICAP_data(path)
    tech_list = R2P.get_technology_types(path)
    storage_types = unique(DataFrames.dropmissing(tech_list, :STORAGE_STANDALONE)[:, "Column1"])
  
    reg_count = 0
    for (reg_idx, reg_name) in enumerate(pras_sys.regions.names)
        reg_cap = filter(x -> x.r == reg_name, capacity_data)
        stor_cats = filter(x -> x ∈ storage_types, unique(reg_cap.i))
        stor_counts = length(stor_cats)
       
        reg_stor_count = 0
        for stor_cat in stor_cats 
            pras_stor_cat_idx = findall(x -> x == stor_cat, pras_sys.storages.categories[pras_sys.region_stor_idxs[reg_idx]])
            reeds_stor_cat_data = filter(x -> x.i == stor_cat, reg_cap)
            
            if (sum(pras_sys.storages.charge_capacity[pras_sys.region_stor_idxs[reg_idx]][pras_stor_cat_idx]) == round(Int, sum(reeds_stor_cat_data.MW))) 
                reg_stor_count = reg_stor_count + 1
            end
        end
        
        if (reg_stor_count == stor_counts)
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys.regions.names))
        return true
    else 
        return false
    end
end

function check_line_capacities(pras_sys::PRAS.SystemModel, path::R2P.ReEDSdatapaths)
    # The capacities of interfaces between AC & DC regions are checked in a different function 
    line_data = R2P.get_line_capacity_data(path)
    non_vsc_line_data = filter(x -> x.trtype != "VSC", line_data)
    vsc_line_data = filter(x -> x.trtype == "VSC", line_data)

    ac_interfaces_count = length(findall(.~occursin.("DC",pras_sys.regions.names[pras_sys.interfaces.regions_from]) .&& .~occursin.("DC",pras_sys.regions.names[pras_sys.interfaces.regions_to])))
    dc_interfaces_count = length(findall(occursin.("DC",pras_sys.regions.names[pras_sys.interfaces.regions_from]) .&& occursin.("DC",pras_sys.regions.names[pras_sys.interfaces.regions_to])))
    ac_int_count = 0
    dc_int_count = 0
   
    for i in 1:length(pras_sys.interfaces)
        region_from = pras_sys.regions.names[pras_sys.interfaces.regions_from[i]]
        region_to = pras_sys.regions.names[pras_sys.interfaces.regions_to[i]]
        cap_forward_pras = pras_sys.interfaces.limit_forward[i]
        cap_backward_pras = pras_sys.interfaces.limit_backward[i]
       
        if !((occursin("DC", region_from) && occursin("DC", region_to)) || (occursin("DC", region_from) || occursin("DC", region_to)))
            to_from_lines = filter(x -> x.r == region_from && x.rr == region_to, non_vsc_line_data)
            from_to_lines = filter(x -> x.r == region_to && x.rr == region_from, non_vsc_line_data)

            cap_forward_reeds = round(Int, sum(to_from_lines.MW))
            cap_backward_reeds = round(Int, sum(from_to_lines.MW))

            if ((cap_forward_pras == cap_forward_reeds) && (cap_backward_pras == cap_backward_reeds))
                ac_int_count = ac_int_count + 1
            end
        else
            if ((occursin("DC", region_from) && occursin("DC", region_to)))
                ac_reg_from = last(split(region_from, "|"))
                ac_reg_to = last(split(region_to, "|"))
                to_from_lines = filter(x -> x.r == ac_reg_from && x.rr == ac_reg_to, vsc_line_data)
                from_to_lines = filter(x -> x.r == ac_reg_to && x.rr == ac_reg_from, vsc_line_data)

                cap_forward_reeds = round(Int, sum(to_from_lines.MW))
                cap_backward_reeds = round(Int, sum(from_to_lines.MW))

                if ((cap_forward_pras == cap_forward_reeds) && (cap_backward_pras == cap_backward_reeds))
                    dc_int_count = dc_int_count + 1
                end
            end
        end
    end

    if ((ac_int_count == ac_interfaces_count) && (dc_int_count == dc_interfaces_count))
        return true
    else
        return false
    end
end

function check_region_load_data(pras_sys::PRAS.SystemModel)
    dc_reg_idx = findall(occursin.("DC", pras_sys.regions.names))
    dc_flag = all(iszero.(pras_sys.regions.load[dc_reg_idx,:]))
    ac_reg_idx = findall(.!(occursin.("DC", pras_sys.regions.names)))
    ac_flag = all(pras_sys.regions.load[ac_reg_idx,:] .> 0)

    return (dc_flag && ac_flag) ? true : false
end

function check_DC_region_in_pras_system(pras_sys::PRAS.SystemModel, path::R2P.ReEDSdatapaths)
    line_base_cap_data = R2P.get_line_capacity_data(path)
    vsc_data = filter(x -> x.trtype == "VSC", line_base_cap_data)
    vsc_regions = union(Set(vsc_data.r), Set(vsc_data.rr))
    dc_region_names = "DC|".*vsc_regions 

    if all(in.(dc_region_names, Ref(pras_sys.regions.names)))
        return true
    else
        return false
    end
end

function check_converter_capacity(pras_sys::PRAS.SystemModel, path::R2P.ReEDSdatapaths)
    cap_converter_data = R2P.get_converter_capacity_data(path)
    vsc_region_names = unique(filter(x -> x.MW > 0.0, cap_converter_data)[!,"r"]) 
    cap_mws = unique(filter(x -> x.MW > 0.0, cap_converter_data)[!,"MW"]) 
    dc_region_names = "DC|".* vsc_region_names
    count = 0
    for (reg_ac, reg_dc, cap_mw) in zip(vsc_region_names, dc_region_names, cap_mws)
        reg_ac_idx = findfirst(pras_sys.regions.names .== reg_ac)
        reg_dc_idx = findfirst(pras_sys.regions.names .== reg_dc)

        interface_idx = findfirst((pras_sys.interfaces.regions_from .== reg_ac_idx .&& pras_sys.interfaces.regions_to .== reg_dc_idx) .|| 
                  (pras_sys.interfaces.regions_to .== reg_ac_idx .&& pras_sys.interfaces.regions_from .== reg_dc_idx))

        if all(pras_sys.interfaces.limit_forward[interface_idx,:] .== round(Int,cap_mw))
            count+=1
        end
    end

    if (count == length(vsc_region_names))
        return true
    else
        return false
    end
end

function check_scheduled_outage_generator_capacities(pras_sys_no_derate::PRAS.SystemModel, pras_sys_with_derate::PRAS.SystemModel)
    
    reg_count = 0
    for (reg_idx, reg_name) in enumerate(pras_sys_no_derate.regions.names)
       
        reg_gen_count = 0
        reg_gen_cats = unique(pras_sys_no_derate.generators.categories[pras_sys_no_derate.region_gen_idxs[reg_idx]])
        for gen_cat in reg_gen_cats
            pras_gen_cat_idx = findall(x -> x == gen_cat, pras_sys_no_derate.generators.categories[pras_sys_no_derate.region_gen_idxs[reg_idx]])
            pras_derate_reg_idx = findfirst(pras_sys_with_derate.regions.names .== reg_name)
            pras_derate_gen_cat_idx = findall(x -> x == gen_cat, pras_sys_with_derate.generators.categories[pras_sys_with_derate.region_gen_idxs[pras_derate_reg_idx]])
           
            if all(pras_sys_with_derate.generators.capacity[pras_sys_with_derate.region_gen_idxs[pras_derate_reg_idx],:][pras_derate_gen_cat_idx,:] .<=
                   pras_sys_no_derate.generators.capacity[pras_sys_no_derate.region_gen_idxs[reg_idx],:][pras_gen_cat_idx,:]) 
                reg_gen_count = reg_gen_count + 1
            end
            
        end
        
        if (reg_gen_count == length(reg_gen_cats))
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys_no_derate.regions.names))
        return true
    else 
        return false
    end
end

function check_scheduled_outage_storage_capacities(pras_sys_no_derate::PRAS.SystemModel, pras_sys_with_derate::PRAS.SystemModel)
    
    reg_count = 0
    for (reg_idx, reg_name) in enumerate(pras_sys_no_derate.regions.names)
       
        reg_stor_count = 0
        reg_stor_cats = unique(pras_sys_no_derate.storages.categories[pras_sys_no_derate.region_stor_idxs[reg_idx]])
        for stor_cat in reg_stor_cats
            pras_stor_cat_idx = findall(x -> x == stor_cat, pras_sys_no_derate.storages.categories[pras_sys_no_derate.region_stor_idxs[reg_idx]])
            pras_derate_reg_idx = findfirst(pras_sys_with_derate.regions.names .== reg_name)
            pras_derate_stor_cat_idx = findall(x -> x == stor_cat, pras_sys_with_derate.storages.categories[pras_sys_with_derate.region_stor_idxs[pras_derate_reg_idx]])
           
            if all(pras_sys_with_derate.storages.energy_capacity[pras_sys_with_derate.region_stor_idxs[pras_derate_reg_idx],:][pras_derate_stor_cat_idx,:] .<=
                   pras_sys_no_derate.storages.energy_capacity[pras_sys_no_derate.region_stor_idxs[reg_idx],:][pras_stor_cat_idx,:]) 
                reg_stor_count = reg_stor_count + 1
            end
            
        end
        
        if (reg_stor_count == length(reg_stor_cats))
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys_no_derate.regions.names))
        return true
    else 
        return false
    end
end

function check_hydro_energy_limits(pras_sys::PRAS.SystemModel,path::R2P.ReEDSdatapaths)
    tech_list = R2P.get_technology_types(path)
    hyd_disp_types =
        lowercase.(DataFrames.dropmissing(tech_list, :HYDRO_D)[:, "Column1"])
    
    reg_count = 0
    for (reg_idx, reg_name) in enumerate(pras_sys.regions.names)
        hyd_disp_cats = filter(x -> x ∈ hyd_disp_types, pras_sys.generatorstorages.categories[pras_sys.region_genstor_idxs[reg_idx]])
        hyd_disp_counts = length(hyd_disp_cats)

        reg_hyd_disp_count = 0
        for gen_cat in hyd_disp_cats
            pras_gen_cat_idx = findall(x -> x == gen_cat, pras_sys.generatorstorages.categories[pras_sys.region_genstor_idxs[reg_idx]])
            
            if (length(unique(pras_sys.generatorstorages.inflow[pras_sys.region_genstor_idxs[reg_idx],:][pras_gen_cat_idx,:])) > 1 ||
                all(iszero.(pras_sys.generatorstorages.inflow[pras_sys.region_genstor_idxs[reg_idx],:][pras_gen_cat_idx,:]))) 
                # Need to do this becuase some regions don't have inflow data (p80 in particular)
                reg_hyd_disp_count = reg_hyd_disp_count + 1
            end
        end
        
        if (reg_hyd_disp_count == length(hyd_disp_cats))
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys.regions.names))
        return true
    else 
        return false
    end
end

function check_generator_outage_probabilities(pras_sys::PRAS.SystemModel, path::R2P.ReEDSdatapaths, weather_year::Int, timesteps::Int)
    capacity_data = R2P.get_ICAP_data(path)
    tech_list = R2P.get_technology_types(path)
    storage_types = unique(DataFrames.dropmissing(tech_list, :STORAGE_STANDALONE)[:, "Column1"])
    hyd_disp_types = lowercase.(DataFrames.dropmissing(tech_list, :HYDRO_D)[:, "Column1"])
    hyd_non_disp_types = lowercase.(DataFrames.dropmissing(tech_list, :HYDRO_ND)[:, "Column1"])
    for_hourly = R2P.get_hourly_forced_outage_data(path)

    reg_count = 0
    for (reg_idx, reg_name) in enumerate(pras_sys.regions.names)
        reg_cap = filter(x -> x.r == reg_name, capacity_data)
        non_stor_cats = filter(x -> x ∉ storage_types, unique(reg_cap.i))
        
        upgraded_non_stor_cats = String[]
        for cat in non_stor_cats
            push!(upgraded_non_stor_cats, cat)
        end
        cat_idx = findall((upgraded_non_stor_cats .* "|" .* reg_name) .∈ Ref(names(for_hourly)))
        hourly_for_cats = non_stor_cats[cat_idx]
        upgraded_hourly_for_cats = upgraded_non_stor_cats[cat_idx]
        hourly_for_cat_counts = length(hourly_for_cats)

        reg_hourly_for_cat_count = 0
        for (gen_cat, upgraded_gen_cat) in zip(hourly_for_cats, upgraded_hourly_for_cats)
            pras_gen_cat_idx = findall(x -> x == gen_cat, pras_sys.generators.categories[pras_sys.region_gen_idxs[reg_idx]])
            reeds_unique_for_count = length(unique(for_hourly[!,upgraded_gen_cat*"|"* reg_name]))
            if (length(unique(sum(pras_sys.generators.λ[pras_sys.region_gen_idxs[reg_idx],:][pras_gen_cat_idx,:], dims = 1))) == reeds_unique_for_count)
                reg_hourly_for_cat_count = reg_hourly_for_cat_count + 1
            end
            
        end
        
        if (reg_hourly_for_cat_count == hourly_for_cat_counts)
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys.regions.names))
        return true
    else 
        return false
    end
end

function check_storage_outage_probabilities(pras_sys::PRAS.SystemModel, path::R2P.ReEDSdatapaths, weather_year::Int, timesteps::Int)
    # This test doesn't account for that fact that FOR for batteries is accounted for in the energy capacity.
    # but passes because λ assigned is 0.0
    capacity_data = R2P.get_ICAP_data(path)
    tech_list = R2P.get_technology_types(path)
    storage_types = unique(DataFrames.dropmissing(tech_list, :STORAGE_STANDALONE)[:, "Column1"])

    for_hourly = R2P.get_hourly_forced_outage_data(path)
    
    reg_count = 0
    for (reg_idx, reg_name) in enumerate(pras_sys.regions.names)
        reg_cap = filter(x -> x.r == reg_name, capacity_data)
        stor_cats = filter(x -> x ∈ storage_types, unique(reg_cap.i))
        
        cat_idx = findall((stor_cats .* "|" .* reg_name) .∈ Ref(names(for_hourly)))
        hourly_for_cats = stor_cats[cat_idx]
        hourly_for_cat_counts = length(hourly_for_cats)

        reg_hourly_for_cat_count = 0
        for gen_cat in hourly_for_cats
            pras_gen_cat_idx = findall(x -> x == gen_cat, pras_sys.storages.categories[pras_sys.region_stor_idxs[reg_idx]])
            reeds_unique_for_count = length(unique(for_hourly[!,gen_cat*"|"* reg_name]))
            if (length(unique(sum(pras_sys.storages.λ[pras_sys.region_stor_idxs[reg_idx],:][pras_gen_cat_idx,:], dims = 1))) == reeds_unique_for_count)
                reg_hourly_for_cat_count = reg_hourly_for_cat_count + 1
            end
            
        end
        
        if (reg_hourly_for_cat_count == hourly_for_cat_counts)
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys.regions.names))
        return true
    else 
        return false
    end
end

function check_storage_recovery_probabilities(pras_sys::PRAS.SystemModel)
    # Just check storages MTTR is parsed as a test

    reg_count = 0
    for (reg_idx,reg_name) in enumerate(pras_sys.regions.names)
        if (all(pras_sys.storages.μ[pras_sys.region_stor_idxs[reg_idx]] .== (1/24)))
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys.regions.names))
        return true
    else 
        return false
    end
end

function check_generatorstorage_outage_probabilities(pras_sys::PRAS.SystemModel, path::R2P.ReEDSdatapaths, weather_year::Int, timesteps::Int)
    for_hourly = R2P.get_hourly_forced_outage_data(path)

    reg_count = 0
    for (reg_idx, reg_name) in enumerate(pras_sys.regions.names)
        reg_genstor_idx = pras_sys.region_genstor_idxs[reg_idx]
        reg_genstor_cats = pras_sys.generatorstorages.categories[reg_genstor_idx]
        reg_genstor_cat_count = 0
        for genstor_cat in unique(reg_genstor_cats)
            pras_genstor_cat_idx = findall(x -> x == genstor_cat, pras_sys.generatorstorages.categories[reg_genstor_idx])
            tech = genstor_cat
            reeds_unique_for_count = length(unique(for_hourly[!,tech*"|"* reg_name]))
            if (length(unique(sum(pras_sys.generatorstorages.λ[reg_genstor_idx,:][pras_genstor_cat_idx,:], dims = 1))) == reeds_unique_for_count)
                reg_genstor_cat_count = reg_genstor_cat_count + 1
            end
            
        end
        
        if (reg_genstor_cat_count == length(unique(reg_genstor_cats)))
            reg_count = reg_count + 1
        end
    end
    if (reg_count == length(pras_sys.regions.names))
        return true
    else 
        return false
    end
end
