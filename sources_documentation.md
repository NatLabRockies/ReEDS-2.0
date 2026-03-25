# ReEDS 2.0

## Table of Contents


  - ### [](#) 
    - #### [hourlize](#hourlize) 
      - ##### [inputs](#hourlize/inputs) 
      - ##### [plexos_to_reeds](#hourlize/plexos_to_reeds) 
      - ##### [tests](#hourlize/tests) 
    - #### [inputs](#inputs) 
      - ##### [canada_imports](#inputs/canada_imports) 
      - ##### [capacitydata](#inputs/capacitydata) 
      - ##### [carbonconstraints](#inputs/carbonconstraints) 
      - ##### [climate](#inputs/climate) 
      - ##### [consume](#inputs/consume) 
      - ##### [csapr](#inputs/csapr) 
      - ##### [ctus](#inputs/ctus) 
      - ##### [degradation](#inputs/degradation) 
      - ##### [demand](#inputs/demand) 
      - ##### [demand_response](#inputs/demand_response) 
      - ##### [dGen_Model_Inputs](#inputs/dGen_Model_Inputs) 
      - ##### [financials](#inputs/financials) 
      - ##### [fuelprices](#inputs/fuelprices) 
      - ##### [geothermal](#inputs/geothermal) 
      - ##### [growth_constraints](#inputs/growth_constraints) 
      - ##### [hydrodata](#inputs/hydrodata) 
      - ##### [loaddata](#inputs/loaddata) 
      - ##### [national_generation](#inputs/national_generation) 
      - ##### [plant_characteristics](#inputs/plant_characteristics) 
      - ##### [reserves](#inputs/reserves) 
      - ##### [RPSdata](#inputs/RPSdata) 
      - ##### [shapefiles](#inputs/shapefiles) 
      - ##### [state_policies](#inputs/state_policies) 
      - ##### [storagedata](#inputs/storagedata) 
      - ##### [supplycurvedata](#inputs/supplycurvedata) 
      - ##### [techs](#inputs/techs) 
      - ##### [transmission](#inputs/transmission) 
      - ##### [upgrades](#inputs/upgrades) 
      - ##### [userinput](#inputs/userinput) 
      - ##### [valuestreams](#inputs/valuestreams) 
      - ##### [variability](#inputs/variability) 
      - ##### [waterclimate](#inputs/waterclimate) 
    - #### [postprocessing](#postprocessing) 
      - ##### [air_quality](#postprocessing/air_quality) 
      - ##### [bokehpivot](#postprocessing/bokehpivot) 
      - ##### [documentation_tools](#postprocessing/documentation_tools) 
      - ##### [land_use](#postprocessing/land_use) 
      - ##### [plots](#postprocessing/plots) 
      - ##### [retail_rate_module](#postprocessing/retail_rate_module) 
      - ##### [tableau](#postprocessing/tableau) 
    - #### [preprocessing](#preprocessing) 
      - ##### [atb_updates_processing](#preprocessing/atb_updates_processing) 
    - #### [ReEDS_Augur](#ReEDS_Augur) 


## Input Files


## []() <a name=''></a>
  - [cases.csv](/cases.csv)
    - **File Type:** Switches file
    - **Description:** Contains the configuration settings for the ReEDS run(s).
    - **Dollar year:** 2004

    - **Citation:** [(https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/38e6610a8c6a92291804598c95c11b707bf187b9/cases.csv)]

---

  - [cases_hourly.csv](/cases_hourly.csv)
---

  - [cases_small.csv](/cases_small.csv)
---

  - [cases_smaller.csv](/cases_smaller.csv)
---

  - [cases_standardscenarios.csv](/cases_standardscenarios.csv)
    - **File Type:** StdScen Cases file
    - **Description:** Contains the configuration settings for the Standard Scenarios ReEDS runs.
---

  - [cases_test.csv](/cases_test.csv)
    - **Description:** Contains the configuration settings for a test ReEDS run using ERCOT.
    - **Dollar year:** 2007
---

  - [e_report_params.csv](/e_report_params.csv)
---

  - [runfiles.csv](/runfiles.csv)
    - **Description:** Contains the locations of input data that is copied from the repository into the runs folder for each respective case.
---

  - [sources.csv](/sources.csv)
    - **Description:** CSV file containing a list of all input files (csv, h5, csv.gz)
---


### [hourlize](hourlize) <a name='hourlize'></a>

#### [inputs](hourlize/inputs) <a name='hourlize/inputs'></a>

##### [load](hourlize/inputs/load) <a name='hourlize/inputs/load'></a>
  - [ba_timezone.csv](/hourlize/inputs/load/ba_timezone.csv)
---

  - [EIA_2010loadbystate.csv](/hourlize/inputs/load/EIA_2010loadbystate.csv)
---

  - [EIA_loadbystate.csv](/hourlize/inputs/load/EIA_loadbystate.csv)
---

  - [hierarchy.csv](/hourlize/inputs/load/hierarchy.csv)
---

  - [load_participation_factors_st_to_ba.csv](/hourlize/inputs/load/load_participation_factors_st_to_ba.csv)
---


##### [resource](hourlize/inputs/resource) <a name='hourlize/inputs/resource'></a>
  - [county_map.csv](/hourlize/inputs/resource/county_map.csv)
---

  - [state_abbrev.csv](/hourlize/inputs/resource/state_abbrev.csv)
---

  - [upv_resource_classes.csv](/hourlize/inputs/resource/upv_resource_classes.csv)
---

  - [wind-ofs_resource_classes.csv](/hourlize/inputs/resource/wind-ofs_resource_classes.csv)
---

  - [wind-ons_resource_classes.csv](/hourlize/inputs/resource/wind-ons_resource_classes.csv)
---


#### [plexos_to_reeds](hourlize/plexos_to_reeds) <a name='hourlize/plexos_to_reeds'></a>

##### [inputs](hourlize/plexos_to_reeds/inputs) <a name='hourlize/plexos_to_reeds/inputs'></a>
  - [month_to_season.csv](/hourlize/plexos_to_reeds/inputs/month_to_season.csv)
---

  - [plexos_node_monthly_lpf_ercot.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_monthly_lpf_ercot.csv)
---

  - [plexos_node_seasonal_lpf_wi.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_seasonal_lpf_wi.csv)
---

  - [plexos_node_to_reeds_ba.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_to_reeds_ba.csv)
---

  - [plexos_node_to_zone_ei.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_to_zone_ei.csv)
---


#### [tests](hourlize/tests) <a name='hourlize/tests'></a>

##### [data](hourlize/tests/data) <a name='hourlize/tests/data'></a>

###### [r2r_from_config](hourlize/tests/data/r2r_from_config) <a name='hourlize/tests/data/r2r_from_config'></a>

####### [expected_results](hourlize/tests/data/r2r_from_config/expected_results) <a name='hourlize/tests/data/r2r_from_config/expected_results'></a>

######## [multiple_priority_inputs](hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs) <a name='hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs'></a>
  - [df_sc_out_dupv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_dupv_reduced.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_wind-ons_reduced.csv)
---


######## [no_bin_constraint](hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint) <a name='hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint'></a>
  - [df_sc_out_dupv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_dupv_reduced.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_wind-ons_reduced.csv)
---


######## [priority_inputs](hourlize/tests/data/r2r_from_config/expected_results/priority_inputs) <a name='hourlize/tests/data/r2r_from_config/expected_results/priority_inputs'></a>
  - [df_sc_out_dupv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_dupv_reduced.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_wind-ons_reduced.csv)
---


###### [r2r_integration](hourlize/tests/data/r2r_integration) <a name='hourlize/tests/data/r2r_integration'></a>

####### [expected_results](hourlize/tests/data/r2r_integration/expected_results) <a name='hourlize/tests/data/r2r_integration/expected_results'></a>
  - [df_sc_out_dupv_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_dupv_reduced.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ons_reduced.csv)
---


####### [reeds](hourlize/tests/data/r2r_integration/reeds) <a name='hourlize/tests/data/r2r_integration/reeds'></a>

######## [inputs_case](hourlize/tests/data/r2r_integration/reeds/inputs_case) <a name='hourlize/tests/data/r2r_integration/reeds/inputs_case'></a>
  - [maxage.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/maxage.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/switches.csv)
---


######### [supplycurve_metadata](hourlize/tests/data/r2r_integration/reeds/inputs_case/supplycurve_metadata) <a name='hourlize/tests/data/r2r_integration/reeds/inputs_case/supplycurve_metadata'></a>
  - [rev_supply_curves.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/supplycurve_metadata/rev_supply_curves.csv)
---


######## [outputs](hourlize/tests/data/r2r_integration/reeds/outputs) <a name='hourlize/tests/data/r2r_integration/reeds/outputs'></a>
  - [cap.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [m_capacity_exog.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/m_capacity_exog.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/systemcost.csv)
---


####### [supply_curves](hourlize/tests/data/r2r_integration/supply_curves) <a name='hourlize/tests/data/r2r_integration/supply_curves'></a>
  - [dupv_sc_naris_scaled.csv](/hourlize/tests/data/r2r_integration/supply_curves/dupv_sc_naris_scaled.csv)
---


######## [upv_1_moderate_reference](hourlize/tests/data/r2r_integration/supply_curves/upv_1_moderate_reference) <a name='hourlize/tests/data/r2r_integration/supply_curves/upv_1_moderate_reference'></a>

######### [results](hourlize/tests/data/r2r_integration/supply_curves/upv_1_moderate_reference/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/upv_1_moderate_reference/results'></a>
  - [upv_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/upv_1_moderate_reference/results/upv_supply_curve_raw.csv)
---


######## [wind-ofs_0_open_moderate](hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate'></a>

######### [results](hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results'></a>
  - [wind-ofs_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results/wind-ofs_supply_curve_raw.csv)
---


######## [wind-ons_01_reference_moderate](hourlize/tests/data/r2r_integration/supply_curves/wind-ons_01_reference_moderate) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ons_01_reference_moderate'></a>

######### [results](hourlize/tests/data/r2r_integration/supply_curves/wind-ons_01_reference_moderate/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ons_01_reference_moderate/results'></a>
  - [wind-ons_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/wind-ons_01_reference_moderate/results/wind-ons_supply_curve_raw.csv)
---


### [inputs](inputs) <a name='inputs'></a>
  - [DebtFractionAdjustmentBounds.csv](/inputs/DebtFractionAdjustmentBounds.csv)
---

  - [deflator.csv](/inputs/deflator.csv)
    - **Description:** Annual price deflator
---

  - [hierarchy.csv](/inputs/hierarchy.csv)
---

  - [hierarchy_agg0.csv](/inputs/hierarchy_agg0.csv)
---

  - [hierarchy_agg2.csv](/inputs/hierarchy_agg2.csv)
---

  - [modeledyears.csv](/inputs/modeledyears.csv)
---

  - [orperc.csv](/inputs/orperc.csv)
---

  - [r_cendiv.csv](/inputs/r_cendiv.csv)
    - **Description:** Mapping for BA's to census regions
---

  - [region_country_map.csv](/inputs/region_country_map.csv)
    - **Description:** Mapping for BA's to countries
---

  - [scalars.csv](/inputs/scalars.csv)
---

  - [tech-subset-table.csv](/inputs/tech-subset-table.csv)
    - **Description:** Maps all technologies to specific subsets of technologies
---


#### [canada_imports](inputs/canada_imports) <a name='inputs/canada_imports'></a>
  - [can_exports.csv](/inputs/canada_imports/can_exports.csv)
    - **Description:** Annual exports to Canada by BA
---

  - [can_exports_szn_frac.csv](/inputs/canada_imports/can_exports_szn_frac.csv)
---

  - [can_imports.csv](/inputs/canada_imports/can_imports.csv)
    - **Description:** Annual imports from Canada by BA
---

  - [can_imports_szn_frac.csv](/inputs/canada_imports/can_imports_szn_frac.csv)
---

  - [can_trade_8760.h5](/inputs/canada_imports/can_trade_8760.h5)
---


#### [capacitydata](inputs/capacitydata) <a name='inputs/capacitydata'></a>
  - [cappayments.csv](/inputs/capacitydata/cappayments.csv)
---

  - [cappayments_ba.csv](/inputs/capacitydata/cappayments_ba.csv)
---

  - [coal_fom_adj.csv](/inputs/capacitydata/coal_fom_adj.csv)
---

  - [demonstration_plants.csv](/inputs/capacitydata/demonstration_plants.csv)
---

  - [firstyear.csv](/inputs/capacitydata/firstyear.csv)
    - **Description:** First year each technology is allowed to be built
---

  - [hydcf.csv](/inputs/capacitydata/hydcf.csv)
---

  - [maxage.csv](/inputs/capacitydata/maxage.csv)
    - **Description:** Maximum age allowed for each technology
---

  - [min_retire_age.csv](/inputs/capacitydata/min_retire_age.csv)
---

  - [nuke_fom_adj.csv](/inputs/capacitydata/nuke_fom_adj.csv)
---

  - [ReEDS_generator_database_final_EIA-NEMS.csv](/inputs/capacitydata/ReEDS_generator_database_final_EIA-NEMS.csv)
    - **Description:** EIA-NEMS database of existing generators
---

  - [rsmap.csv](/inputs/capacitydata/rsmap.csv)
    - **Description:** Mapping for BA's to resource regions
---

  - [SeaCapAdj_hy.csv](/inputs/capacitydata/SeaCapAdj_hy.csv)
---

  - [upgrade_costs_ccs_coal.csv](/inputs/capacitydata/upgrade_costs_ccs_coal.csv)
---

  - [upgrade_costs_ccs_gas.csv](/inputs/capacitydata/upgrade_costs_ccs_gas.csv)
---

  - [upv_exog_cap_limited.csv](/inputs/capacitydata/upv_exog_cap_limited.csv)
---

  - [upv_exog_cap_open.csv](/inputs/capacitydata/upv_exog_cap_open.csv)
---

  - [upv_exog_cap_reference.csv](/inputs/capacitydata/upv_exog_cap_reference.csv)
---

  - [upv_prescribed_builds_limited.csv](/inputs/capacitydata/upv_prescribed_builds_limited.csv)
---

  - [upv_prescribed_builds_open.csv](/inputs/capacitydata/upv_prescribed_builds_open.csv)
---

  - [upv_prescribed_builds_reference.csv](/inputs/capacitydata/upv_prescribed_builds_reference.csv)
---

  - [wind-ofs_prescribed_builds_limited.csv](/inputs/capacitydata/wind-ofs_prescribed_builds_limited.csv)
---

  - [wind-ofs_prescribed_builds_open.csv](/inputs/capacitydata/wind-ofs_prescribed_builds_open.csv)
---

  - [wind-ons_exog_cap_limited.csv](/inputs/capacitydata/wind-ons_exog_cap_limited.csv)
---

  - [wind-ons_exog_cap_open.csv](/inputs/capacitydata/wind-ons_exog_cap_open.csv)
---

  - [wind-ons_exog_cap_reference.csv](/inputs/capacitydata/wind-ons_exog_cap_reference.csv)
---

  - [wind-ons_prescribed_builds_limited.csv](/inputs/capacitydata/wind-ons_prescribed_builds_limited.csv)
---

  - [wind-ons_prescribed_builds_open.csv](/inputs/capacitydata/wind-ons_prescribed_builds_open.csv)
---

  - [wind-ons_prescribed_builds_reference.csv](/inputs/capacitydata/wind-ons_prescribed_builds_reference.csv)
---


##### [distpv](inputs/capacitydata/distpv) <a name='inputs/capacitydata/distpv'></a>
  - [distPVcap_Tariff_Final.csv](/inputs/capacitydata/distpv/distPVcap_Tariff_Final.csv)
---

  - [distPVCF_Tariff_Final.csv](/inputs/capacitydata/distpv/distPVCF_Tariff_Final.csv)
---


#### [carbonconstraints](inputs/carbonconstraints) <a name='inputs/carbonconstraints'></a>
  - [capture_rates_CCS_95.csv](/inputs/carbonconstraints/capture_rates_CCS_95.csv)
---

  - [capture_rates_CCS_99.csv](/inputs/carbonconstraints/capture_rates_CCS_99.csv)
---

  - [capture_rates_default.csv](/inputs/carbonconstraints/capture_rates_default.csv)
---

  - [ccs_link.csv](/inputs/carbonconstraints/ccs_link.csv)
---

  - [co2_cap.csv](/inputs/carbonconstraints/co2_cap.csv)
    - **Description:** Annual nationwide carbon cap
---

  - [co2_tax.csv](/inputs/carbonconstraints/co2_tax.csv)
    - **Description:** Annual co2 tax
---

  - [emit_scale.csv](/inputs/carbonconstraints/emit_scale.csv)
---

  - [emitrate.csv](/inputs/carbonconstraints/emitrate.csv)
    - **Description:** Emition rates for thermal generator for SO2, Nox, Hg, and CO2
---

  - [methane_leakage_rate.csv](/inputs/carbonconstraints/methane_leakage_rate.csv)
---

  - [ng_crf_penalty.csv](/inputs/carbonconstraints/ng_crf_penalty.csv)
---

  - [rggi_states.csv](/inputs/carbonconstraints/rggi_states.csv)
---

  - [rggicon.csv](/inputs/carbonconstraints/rggicon.csv)
    - **Description:** CO2 caps for RGGI states in metric tons
---

  - [state_cap.csv](/inputs/carbonconstraints/state_cap.csv)
---


#### [climate](inputs/climate) <a name='inputs/climate'></a>
  - [climate_heuristics_finalyear.csv](/inputs/climate/climate_heuristics_finalyear.csv)
---

  - [climate_heuristics_yearfrac.csv](/inputs/climate/climate_heuristics_yearfrac.csv)
---

  - [CoolSlopes.csv](/inputs/climate/CoolSlopes.csv)
---

  - [HeatSlopes.csv](/inputs/climate/HeatSlopes.csv)
---


##### [GFDL-ESM2M_RCP4p5_WM](inputs/climate/GFDL-ESM2M_RCP4p5_WM) <a name='inputs/climate/GFDL-ESM2M_RCP4p5_WM'></a>
  - [HDDCDD.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/HDDCDD.csv)
---

  - [hydadjann.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/hydadjann.csv)
---

  - [hydadjsea.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/hydadjsea.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_RCP2p6](inputs/climate/HadGEM2-ES_RCP2p6) <a name='inputs/climate/HadGEM2-ES_RCP2p6'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP2p6/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_rcp45_AT](inputs/climate/HadGEM2-ES_rcp45_AT) <a name='inputs/climate/HadGEM2-ES_rcp45_AT'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/HDDCDD.csv)
---

  - [hydadjann.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/hydadjann.csv)
---

  - [hydadjsea.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/hydadjsea.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_RCP4p5](inputs/climate/HadGEM2-ES_RCP4p5) <a name='inputs/climate/HadGEM2-ES_RCP4p5'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP4p5/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_rcp85_AT](inputs/climate/HadGEM2-ES_rcp85_AT) <a name='inputs/climate/HadGEM2-ES_rcp85_AT'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/HDDCDD.csv)
---

  - [hydadjann.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/hydadjann.csv)
---

  - [hydadjsea.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/hydadjsea.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_RCP8p5](inputs/climate/HadGEM2-ES_RCP8p5) <a name='inputs/climate/HadGEM2-ES_RCP8p5'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP8p5/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterSeaAnnDistr.csv)
---


##### [IPSL-CM5A-LR_RCP8p5_WM](inputs/climate/IPSL-CM5A-LR_RCP8p5_WM) <a name='inputs/climate/IPSL-CM5A-LR_RCP8p5_WM'></a>
  - [HDDCDD.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/HDDCDD.csv)
---

  - [hydadjann.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/hydadjann.csv)
---

  - [hydadjsea.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/hydadjsea.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/UnappWaterSeaAnnDistr.csv)
---


#### [consume](inputs/consume) <a name='inputs/consume'></a>
  - [consume_char_low.csv](/inputs/consume/consume_char_low.csv)
---

  - [consume_char_ref.csv](/inputs/consume/consume_char_ref.csv)
---

  - [dac_elec_BVRE_2021_high.csv](/inputs/consume/dac_elec_BVRE_2021_high.csv)
---

  - [dac_elec_BVRE_2021_low.csv](/inputs/consume/dac_elec_BVRE_2021_low.csv)
---

  - [dac_elec_BVRE_2021_mid.csv](/inputs/consume/dac_elec_BVRE_2021_mid.csv)
---

  - [dac_gas_BVRE_2021_high.csv](/inputs/consume/dac_gas_BVRE_2021_high.csv)
---

  - [dac_gas_BVRE_2021_low.csv](/inputs/consume/dac_gas_BVRE_2021_low.csv)
---

  - [dac_gas_BVRE_2021_mid.csv](/inputs/consume/dac_gas_BVRE_2021_mid.csv)
---

  - [dollaryear.csv](/inputs/consume/dollaryear.csv)
---

  - [h2_ba_share.csv](/inputs/consume/h2_ba_share.csv)
---

  - [h2_exogenous_demand.csv](/inputs/consume/h2_exogenous_demand.csv)
---

  - [h2_storage_rb.csv](/inputs/consume/h2_storage_rb.csv)
---

  - [h2_transport_and_storage_costs.csv](/inputs/consume/h2_transport_and_storage_costs.csv)
---

  - [pipeline_cost_mult.csv](/inputs/consume/pipeline_cost_mult.csv)
---


#### [csapr](inputs/csapr) <a name='inputs/csapr'></a>
  - [csapr_group1_ex.csv](/inputs/csapr/csapr_group1_ex.csv)
---

  - [csapr_group2_ex.csv](/inputs/csapr/csapr_group2_ex.csv)
---

  - [csapr_ozone_season.csv](/inputs/csapr/csapr_ozone_season.csv)
---


#### [ctus](inputs/ctus) <a name='inputs/ctus'></a>
  - [co2_site_char.csv](/inputs/ctus/co2_site_char.csv)
---

  - [cs.csv](/inputs/ctus/cs.csv)
---

  - [r_cs.csv](/inputs/ctus/r_cs.csv)
---

  - [r_cs_distance_mi.csv](/inputs/ctus/r_cs_distance_mi.csv)
---


#### [degradation](inputs/degradation) <a name='inputs/degradation'></a>
  - [degradation_annual_default.csv](/inputs/degradation/degradation_annual_default.csv)
---


#### [demand](inputs/demand) <a name='inputs/demand'></a>

##### [information](inputs/demand/information) <a name='inputs/demand/information'></a>
  - [Improvements log.xlsx](/inputs/demand/information/Improvements%20log.xlsx)
---


##### [processed data](inputs/demand/processed%20data) <a name='inputs/demand/processed data'></a>
  - [base-device-set.csv](/inputs/demand/processed%20data/base-device-set.csv)
---

  - [commercial-load.csv](/inputs/demand/processed%20data/commercial-load.csv)
---

  - [device-class-set.csv](/inputs/demand/processed%20data/device-class-set.csv)
---

  - [device-option-set.csv](/inputs/demand/processed%20data/device-option-set.csv)
---

  - [discount-rates.csv](/inputs/demand/processed%20data/discount-rates.csv)
---

  - [end-use-set.csv](/inputs/demand/processed%20data/end-use-set.csv)
---

  - [income-class-set.csv](/inputs/demand/processed%20data/income-class-set.csv)
---

  - [industrial-load.csv](/inputs/demand/processed%20data/industrial-load.csv)
---

  - [new-device-set.csv](/inputs/demand/processed%20data/new-device-set.csv)
---

  - [price-adders.csv](/inputs/demand/processed%20data/price-adders.csv)
---

  - [ref-consumption.csv](/inputs/demand/processed%20data/ref-consumption.csv)
---

  - [total-device-counts.csv](/inputs/demand/processed%20data/total-device-counts.csv)
---

  - [use-dvc-map.csv](/inputs/demand/processed%20data/use-dvc-map.csv)
---

  - [use-dvc-opt-map.csv](/inputs/demand/processed%20data/use-dvc-opt-map.csv)
---


##### [raw data](inputs/demand/raw%20data) <a name='inputs/demand/raw data'></a>
  - [AEO2017 browser data.xlsx](/inputs/demand/raw%20data/AEO2017%20browser%20data.xlsx)
---

  - [Area fractions.csv](/inputs/demand/raw%20data/Area%20fractions.csv)
---

  - [Commercial load shapes.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes.csv)
---

  - [Commercial sales.csv](/inputs/demand/raw%20data/Commercial%20sales.csv)
---

  - [County demographics.xlsx](/inputs/demand/raw%20data/County%20demographics.xlsx)
---

  - [EIA 2016 electricity prices.xlsx](/inputs/demand/raw%20data/EIA%202016%20electricity%20prices.xlsx)
---

  - [EIA 2016 electricity sales.xlsx](/inputs/demand/raw%20data/EIA%202016%20electricity%20sales.xlsx)
---

  - [EIA mapping sets.xlsx](/inputs/demand/raw%20data/EIA%20mapping%20sets.xlsx)
---

  - [EIA NEMS commercial.xlsx](/inputs/demand/raw%20data/EIA%20NEMS%20commercial.xlsx)
---

  - [EIA NEMS residential.xlsx](/inputs/demand/raw%20data/EIA%20NEMS%20residential.xlsx)
---

  - [files_in_NEMS_output_folder.xlsx](/inputs/demand/raw%20data/files_in_NEMS_output_folder.xlsx)
---

  - [Households.xlsx](/inputs/demand/raw%20data/Households.xlsx)
---

  - [Industrial load disaggregation.xlsx](/inputs/demand/raw%20data/Industrial%20load%20disaggregation.xlsx)
---

  - [Industrial load shapes.csv](/inputs/demand/raw%20data/Industrial%20load%20shapes.csv)
---

  - [Mapping sets.xlsx](/inputs/demand/raw%20data/Mapping%20sets.xlsx)
---

  - [NEMS industrial.xlsx](/inputs/demand/raw%20data/NEMS%20industrial.xlsx)
---

  - [NEMS price adders.xlsx](/inputs/demand/raw%20data/NEMS%20price%20adders.xlsx)
---

  - [NEMS residential - v2.xlsx](/inputs/demand/raw%20data/NEMS%20residential%20-%20v2.xlsx)
---

  - [NEMS-ReEDS Region Mapping.csv](/inputs/demand/raw%20data/NEMS-ReEDS%20Region%20Mapping.csv)
---

  - [nems_input_files.xlsx](/inputs/demand/raw%20data/nems_input_files.xlsx)
---

  - [Other technology options.xlsx](/inputs/demand/raw%20data/Other%20technology%20options.xlsx)
---

  - [Parameters.xlsx](/inputs/demand/raw%20data/Parameters.xlsx)
---

  - [Population.xlsx](/inputs/demand/raw%20data/Population.xlsx)
---

  - [Residential load shapes.csv](/inputs/demand/raw%20data/Residential%20load%20shapes.csv)
---


###### [Commercial load shapes](inputs/demand/raw%20data/Commercial%20load%20shapes) <a name='inputs/demand/raw%20data/Commercial load shapes'></a>
  - [2016-08-08 - Comm Load by End Use - AL.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20AL.csv)
---

  - [2016-08-08 - Comm Load by End Use - AR.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20AR.csv)
---

  - [2016-08-08 - Comm Load by End Use - AZ.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20AZ.csv)
---

  - [2016-08-08 - Comm Load by End Use - CA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20CA.csv)
---

  - [2016-08-08 - Comm Load by End Use - CO.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20CO.csv)
---

  - [2016-08-08 - Comm Load by End Use - CT.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20CT.csv)
---

  - [2016-08-08 - Comm Load by End Use - DC.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20DC.csv)
---

  - [2016-08-08 - Comm Load by End Use - DE.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20DE.csv)
---

  - [2016-08-08 - Comm Load by End Use - FL.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20FL.csv)
---

  - [2016-08-08 - Comm Load by End Use - GA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20GA.csv)
---

  - [2016-08-08 - Comm Load by End Use - HI.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20HI.csv)
---

  - [2016-08-08 - Comm Load by End Use - IA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20IA.csv)
---

  - [2016-08-08 - Comm Load by End Use - ID.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20ID.csv)
---

  - [2016-08-08 - Comm Load by End Use - IL.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20IL.csv)
---

  - [2016-08-08 - Comm Load by End Use - IN.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20IN.csv)
---

  - [2016-08-08 - Comm Load by End Use - KS.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20KS.csv)
---

  - [2016-08-08 - Comm Load by End Use - KY.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20KY.csv)
---

  - [2016-08-08 - Comm Load by End Use - LA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20LA.csv)
---

  - [2016-08-08 - Comm Load by End Use - MA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MA.csv)
---

  - [2016-08-08 - Comm Load by End Use - MD.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MD.csv)
---

  - [2016-08-08 - Comm Load by End Use - ME.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20ME.csv)
---

  - [2016-08-08 - Comm Load by End Use - MI.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MI.csv)
---

  - [2016-08-08 - Comm Load by End Use - MN.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MN.csv)
---

  - [2016-08-08 - Comm Load by End Use - MO.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MO.csv)
---

  - [2016-08-08 - Comm Load by End Use - MS.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MS.csv)
---

  - [2016-08-08 - Comm Load by End Use - MT.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MT.csv)
---

  - [2016-08-08 - Comm Load by End Use - NC.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NC.csv)
---

  - [2016-08-08 - Comm Load by End Use - ND.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20ND.csv)
---

  - [2016-08-08 - Comm Load by End Use - NE.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NE.csv)
---

  - [2016-08-08 - Comm Load by End Use - NH.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NH.csv)
---

  - [2016-08-08 - Comm Load by End Use - NJ.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NJ.csv)
---

  - [2016-08-08 - Comm Load by End Use - NM.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NM.csv)
---

  - [2016-08-08 - Comm Load by End Use - NV.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NV.csv)
---

  - [2016-08-08 - Comm Load by End Use - NY.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NY.csv)
---

  - [2016-08-08 - Comm Load by End Use - OH.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20OH.csv)
---

  - [2016-08-08 - Comm Load by End Use - OK.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20OK.csv)
---

  - [2016-08-08 - Comm Load by End Use - OR.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20OR.csv)
---

  - [2016-08-08 - Comm Load by End Use - PA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20PA.csv)
---

  - [2016-08-08 - Comm Load by End Use - RI.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20RI.csv)
---

  - [2016-08-08 - Comm Load by End Use - SC.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20SC.csv)
---

  - [2016-08-08 - Comm Load by End Use - SD.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20SD.csv)
---

  - [2016-08-08 - Comm Load by End Use - TN.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20TN.csv)
---

  - [2016-08-08 - Comm Load by End Use - TX.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20TX.csv)
---

  - [2016-08-08 - Comm Load by End Use - UT.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20UT.csv)
---

  - [2016-08-08 - Comm Load by End Use - VA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20VA.csv)
---

  - [2016-08-08 - Comm Load by End Use - VT.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20VT.csv)
---

  - [2016-08-08 - Comm Load by End Use - WA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20WA.csv)
---

  - [2016-08-08 - Comm Load by End Use - WI.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20WI.csv)
---

  - [2016-08-08 - Comm Load by End Use - WV.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20WV.csv)
---

  - [2016-08-08 - Comm Load by End Use - WY.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20WY.csv)
---


#### [demand_response](inputs/demand_response) <a name='inputs/demand_response'></a>
  - [dr_decrease_none.csv](/inputs/demand_response/dr_decrease_none.csv)
---

  - [dr_decrease_profile_Baseline.csv](/inputs/demand_response/dr_decrease_profile_Baseline.csv)
---

  - [dr_decrease_profile_Baseline_shed.csv](/inputs/demand_response/dr_decrease_profile_Baseline_shed.csv)
---

  - [dr_decrease_profile_Baseline_shift.csv](/inputs/demand_response/dr_decrease_profile_Baseline_shift.csv)
---

  - [dr_decrease_profile_none.csv](/inputs/demand_response/dr_decrease_profile_none.csv)
---

  - [dr_increase_none.csv](/inputs/demand_response/dr_increase_none.csv)
---

  - [dr_increase_profile_Baseline.csv](/inputs/demand_response/dr_increase_profile_Baseline.csv)
---

  - [dr_increase_profile_Baseline_shed.csv](/inputs/demand_response/dr_increase_profile_Baseline_shed.csv)
---

  - [dr_increase_profile_Baseline_shift.csv](/inputs/demand_response/dr_increase_profile_Baseline_shift.csv)
---

  - [dr_increase_profile_none.csv](/inputs/demand_response/dr_increase_profile_none.csv)
---

  - [dr_rsc_Baseline.csv](/inputs/demand_response/dr_rsc_Baseline.csv)
---

  - [dr_rsc_Baseline_shed.csv](/inputs/demand_response/dr_rsc_Baseline_shed.csv)
---

  - [dr_rsc_Baseline_shift.csv](/inputs/demand_response/dr_rsc_Baseline_shift.csv)
---

  - [dr_rsc_none.csv](/inputs/demand_response/dr_rsc_none.csv)
---

  - [dr_shed_Baseline.csv](/inputs/demand_response/dr_shed_Baseline.csv)
---

  - [dr_shed_Baseline_shed.csv](/inputs/demand_response/dr_shed_Baseline_shed.csv)
---

  - [dr_shed_Baseline_shift.csv](/inputs/demand_response/dr_shed_Baseline_shift.csv)
---

  - [dr_shed_none.csv](/inputs/demand_response/dr_shed_none.csv)
---

  - [dr_shifts_Baseline.csv](/inputs/demand_response/dr_shifts_Baseline.csv)
---

  - [dr_shifts_Baseline_shed.csv](/inputs/demand_response/dr_shifts_Baseline_shed.csv)
---

  - [dr_shifts_Baseline_shift.csv](/inputs/demand_response/dr_shifts_Baseline_shift.csv)
---

  - [dr_shifts_none.csv](/inputs/demand_response/dr_shifts_none.csv)
---

  - [dr_types_Baseline.csv](/inputs/demand_response/dr_types_Baseline.csv)
---

  - [dr_types_Baseline_shed.csv](/inputs/demand_response/dr_types_Baseline_shed.csv)
---

  - [dr_types_Baseline_shift.csv](/inputs/demand_response/dr_types_Baseline_shift.csv)
---

  - [dr_types_none.csv](/inputs/demand_response/dr_types_none.csv)
---


#### [dGen_Model_Inputs](inputs/dGen_Model_Inputs) <a name='inputs/dGen_Model_Inputs'></a>

##### [StScen2018_Mid_Case](inputs/dGen_Model_Inputs/StScen2018_Mid_Case) <a name='inputs/dGen_Model_Inputs/StScen2018_Mid_Case'></a>
  - [distPVcap_StScen2018_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2018_Mid_Case/distPVcap_StScen2018_Mid_Case.csv)
---

  - [distPVCF_hourly_StScen2018_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2018_Mid_Case/distPVCF_hourly_StScen2018_Mid_Case.csv)
---


##### [StScen2019_Carbon_cap](inputs/dGen_Model_Inputs/StScen2019_Carbon_cap) <a name='inputs/dGen_Model_Inputs/StScen2019_Carbon_cap'></a>
  - [distPVcap_StScen2019_Carbon_cap.csv](/inputs/dGen_Model_Inputs/StScen2019_Carbon_cap/distPVcap_StScen2019_Carbon_cap.csv)
---

  - [distPVCF_hourly_StScen2019_Carbon_cap.csv](/inputs/dGen_Model_Inputs/StScen2019_Carbon_cap/distPVCF_hourly_StScen2019_Carbon_cap.csv)
---


##### [StScen2019_High_NG_Price](inputs/dGen_Model_Inputs/StScen2019_High_NG_Price) <a name='inputs/dGen_Model_Inputs/StScen2019_High_NG_Price'></a>
  - [distPVcap_StScen2019_High_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2019_High_NG_Price/distPVcap_StScen2019_High_NG_Price.csv)
---

  - [distPVCF_hourly_StScen2019_High_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2019_High_NG_Price/distPVCF_hourly_StScen2019_High_NG_Price.csv)
---


##### [StScen2019_High_PV_Cost](inputs/dGen_Model_Inputs/StScen2019_High_PV_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_High_PV_Cost'></a>
  - [distPVcap_StScen2019_High_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_High_PV_Cost/distPVcap_StScen2019_High_PV_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_High_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_High_PV_Cost/distPVCF_hourly_StScen2019_High_PV_Cost.csv)
---


##### [StScen2019_High_RE_Cost](inputs/dGen_Model_Inputs/StScen2019_High_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_High_RE_Cost'></a>
  - [distPVcap_StScen2019_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_High_RE_Cost/distPVcap_StScen2019_High_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_High_RE_Cost/distPVCF_hourly_StScen2019_High_RE_Cost.csv)
---


##### [StScen2019_Low_Bat_Cost](inputs/dGen_Model_Inputs/StScen2019_Low_Bat_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_Low_Bat_Cost'></a>
  - [distPVcap_StScen2019_Low_Bat_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_Bat_Cost/distPVcap_StScen2019_Low_Bat_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_Low_Bat_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_Bat_Cost/distPVCF_hourly_StScen2019_Low_Bat_Cost.csv)
---


##### [StScen2019_Low_NG_Price](inputs/dGen_Model_Inputs/StScen2019_Low_NG_Price) <a name='inputs/dGen_Model_Inputs/StScen2019_Low_NG_Price'></a>
  - [distPVcap_StScen2019_Low_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_NG_Price/distPVcap_StScen2019_Low_NG_Price.csv)
---

  - [distPVCF_hourly_StScen2019_Low_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_NG_Price/distPVCF_hourly_StScen2019_Low_NG_Price.csv)
---


##### [StScen2019_Low_PV_Cost](inputs/dGen_Model_Inputs/StScen2019_Low_PV_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_Low_PV_Cost'></a>
  - [distPVcap_StScen2019_Low_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_PV_Cost/distPVcap_StScen2019_Low_PV_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_Low_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_PV_Cost/distPVCF_hourly_StScen2019_Low_PV_Cost.csv)
---


##### [StScen2019_Low_RE_Cost](inputs/dGen_Model_Inputs/StScen2019_Low_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_Low_RE_Cost'></a>
  - [distPVcap_StScen2019_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_RE_Cost/distPVcap_StScen2019_Low_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_RE_Cost/distPVCF_hourly_StScen2019_Low_RE_Cost.csv)
---


##### [StScen2019_Mid_Case](inputs/dGen_Model_Inputs/StScen2019_Mid_Case) <a name='inputs/dGen_Model_Inputs/StScen2019_Mid_Case'></a>
  - [distPVcap_StScen2019_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2019_Mid_Case/distPVcap_StScen2019_Mid_Case.csv)
---

  - [distPVCF_hourly_StScen2019_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2019_Mid_Case/distPVCF_hourly_StScen2019_Mid_Case.csv)
---


##### [StScen2019_National_RPS_80](inputs/dGen_Model_Inputs/StScen2019_National_RPS_80) <a name='inputs/dGen_Model_Inputs/StScen2019_National_RPS_80'></a>
  - [distPVcap_StScen2019_National_RPS_80.csv](/inputs/dGen_Model_Inputs/StScen2019_National_RPS_80/distPVcap_StScen2019_National_RPS_80.csv)
---

  - [distPVCF_hourly_StScen2019_National_RPS_80.csv](/inputs/dGen_Model_Inputs/StScen2019_National_RPS_80/distPVCF_hourly_StScen2019_National_RPS_80.csv)
---


##### [StScen2019_PTC_ITC_extension](inputs/dGen_Model_Inputs/StScen2019_PTC_ITC_extension) <a name='inputs/dGen_Model_Inputs/StScen2019_PTC_ITC_extension'></a>
  - [distPVcap_StScen2019_PTC_ITC_extension.csv](/inputs/dGen_Model_Inputs/StScen2019_PTC_ITC_extension/distPVcap_StScen2019_PTC_ITC_extension.csv)
---

  - [distPVCF_hourly_StScen2019_PTC_ITC_extension.csv](/inputs/dGen_Model_Inputs/StScen2019_PTC_ITC_extension/distPVCF_hourly_StScen2019_PTC_ITC_extension.csv)
---


##### [StScen2020_Carbon_cap](inputs/dGen_Model_Inputs/StScen2020_Carbon_cap) <a name='inputs/dGen_Model_Inputs/StScen2020_Carbon_cap'></a>
  - [distPVcap_StScen2020_Carbon_cap.csv](/inputs/dGen_Model_Inputs/StScen2020_Carbon_cap/distPVcap_StScen2020_Carbon_cap.csv)
---

  - [distPVCF_hourly_StScen2020_Carbon_cap.csv](/inputs/dGen_Model_Inputs/StScen2020_Carbon_cap/distPVCF_hourly_StScen2020_Carbon_cap.csv)
---


##### [StScen2020_High_NG_Price](inputs/dGen_Model_Inputs/StScen2020_High_NG_Price) <a name='inputs/dGen_Model_Inputs/StScen2020_High_NG_Price'></a>
  - [distPVcap_StScen2020_High_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2020_High_NG_Price/distPVcap_StScen2020_High_NG_Price.csv)
---

  - [distPVCF_hourly_StScen2020_High_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2020_High_NG_Price/distPVCF_hourly_StScen2020_High_NG_Price.csv)
---


##### [StScen2020_High_PV_Cost](inputs/dGen_Model_Inputs/StScen2020_High_PV_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_High_PV_Cost'></a>
  - [distPVcap_StScen2020_High_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_High_PV_Cost/distPVcap_StScen2020_High_PV_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_High_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_High_PV_Cost/distPVCF_hourly_StScen2020_High_PV_Cost.csv)
---


##### [StScen2020_High_RE_Cost](inputs/dGen_Model_Inputs/StScen2020_High_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_High_RE_Cost'></a>
  - [distPVcap_StScen2020_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_High_RE_Cost/distPVcap_StScen2020_High_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_High_RE_Cost/distPVCF_hourly_StScen2020_High_RE_Cost.csv)
---


##### [StScen2020_Low_Bat_Cost](inputs/dGen_Model_Inputs/StScen2020_Low_Bat_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_Low_Bat_Cost'></a>
  - [distPVcap_StScen2020_Low_Bat_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_Bat_Cost/distPVcap_StScen2020_Low_Bat_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_Low_Bat_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_Bat_Cost/distPVCF_hourly_StScen2020_Low_Bat_Cost.csv)
---


##### [StScen2020_Low_NG_Price](inputs/dGen_Model_Inputs/StScen2020_Low_NG_Price) <a name='inputs/dGen_Model_Inputs/StScen2020_Low_NG_Price'></a>
  - [distPVcap_StScen2020_Low_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_NG_Price/distPVcap_StScen2020_Low_NG_Price.csv)
---

  - [distPVCF_hourly_StScen2020_Low_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_NG_Price/distPVCF_hourly_StScen2020_Low_NG_Price.csv)
---


##### [StScen2020_Low_PV_Cost](inputs/dGen_Model_Inputs/StScen2020_Low_PV_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_Low_PV_Cost'></a>
  - [distPVcap_StScen2020_Low_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_PV_Cost/distPVcap_StScen2020_Low_PV_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_Low_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_PV_Cost/distPVCF_hourly_StScen2020_Low_PV_Cost.csv)
---


##### [StScen2020_Low_RE_Cost](inputs/dGen_Model_Inputs/StScen2020_Low_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_Low_RE_Cost'></a>
  - [distPVcap_StScen2020_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_RE_Cost/distPVcap_StScen2020_Low_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_RE_Cost/distPVCF_hourly_StScen2020_Low_RE_Cost.csv)
---


##### [StScen2020_Mid_Case](inputs/dGen_Model_Inputs/StScen2020_Mid_Case) <a name='inputs/dGen_Model_Inputs/StScen2020_Mid_Case'></a>
  - [distPVcap_StScen2020_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2020_Mid_Case/distPVcap_StScen2020_Mid_Case.csv)
---

  - [distPVCF_hourly_StScen2020_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2020_Mid_Case/distPVCF_hourly_StScen2020_Mid_Case.csv)
---


##### [StScen2020_National_RPS_80](inputs/dGen_Model_Inputs/StScen2020_National_RPS_80) <a name='inputs/dGen_Model_Inputs/StScen2020_National_RPS_80'></a>
  - [distPVcap_StScen2020_National_RPS_80.csv](/inputs/dGen_Model_Inputs/StScen2020_National_RPS_80/distPVcap_StScen2020_National_RPS_80.csv)
---

  - [distPVCF_hourly_StScen2020_National_RPS_80.csv](/inputs/dGen_Model_Inputs/StScen2020_National_RPS_80/distPVCF_hourly_StScen2020_National_RPS_80.csv)
---


##### [StScen2020_PTC_ITC_extension](inputs/dGen_Model_Inputs/StScen2020_PTC_ITC_extension) <a name='inputs/dGen_Model_Inputs/StScen2020_PTC_ITC_extension'></a>
  - [distPVcap_StScen2020_PTC_ITC_extension.csv](/inputs/dGen_Model_Inputs/StScen2020_PTC_ITC_extension/distPVcap_StScen2020_PTC_ITC_extension.csv)
---

  - [distPVCF_hourly_StScen2020_PTC_ITC_extension.csv](/inputs/dGen_Model_Inputs/StScen2020_PTC_ITC_extension/distPVCF_hourly_StScen2020_PTC_ITC_extension.csv)
---


##### [StScen2022_High_RE_Cost](inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost'></a>
  - [distPVcap_StScen2022_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost/distPVcap_StScen2022_High_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2022_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost/distPVCF_hourly_StScen2022_High_RE_Cost.csv)
---


##### [StScen2022_High_RE_Cost_LMI](inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_LMI) <a name='inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_LMI'></a>
  - [distPVcap_StScen2022_High_RE_Cost_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_LMI/distPVcap_StScen2022_High_RE_Cost_LMI.csv)
---

  - [distPVCF_hourly_StScen2022_High_RE_Cost_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_LMI/distPVCF_hourly_StScen2022_High_RE_Cost_LMI.csv)
---


##### [StScen2022_High_RE_Cost_noIRA](inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_noIRA) <a name='inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_noIRA'></a>
  - [distPVcap_StScen2022_High_RE_Cost_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_noIRA/distPVcap_StScen2022_High_RE_Cost_noIRA.csv)
---

  - [distPVCF_hourly_StScen2022_High_RE_Cost_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_noIRA/distPVCF_hourly_StScen2022_High_RE_Cost_noIRA.csv)
---


##### [StScen2022_Low_RE_Cost](inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost'></a>
  - [distPVcap_StScen2022_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost/distPVcap_StScen2022_Low_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2022_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost/distPVCF_hourly_StScen2022_Low_RE_Cost.csv)
---


##### [StScen2022_Low_RE_Cost_LMI](inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_LMI) <a name='inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_LMI'></a>
  - [distPVcap_StScen2022_Low_RE_Cost_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_LMI/distPVcap_StScen2022_Low_RE_Cost_LMI.csv)
---

  - [distPVCF_hourly_StScen2022_Low_RE_Cost_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_LMI/distPVCF_hourly_StScen2022_Low_RE_Cost_LMI.csv)
---


##### [StScen2022_Low_RE_Cost_noIRA](inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_noIRA) <a name='inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_noIRA'></a>
  - [distPVcap_StScen2022_Low_RE_Cost_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_noIRA/distPVcap_StScen2022_Low_RE_Cost_noIRA.csv)
---

  - [distPVCF_hourly_StScen2022_Low_RE_Cost_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_noIRA/distPVCF_hourly_StScen2022_Low_RE_Cost_noIRA.csv)
---


##### [StScen2022_Mid_Case](inputs/dGen_Model_Inputs/StScen2022_Mid_Case) <a name='inputs/dGen_Model_Inputs/StScen2022_Mid_Case'></a>
  - [distPVcap_StScen2022_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case/distPVcap_StScen2022_Mid_Case.csv)
---

  - [distPVCF_hourly_StScen2022_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case/distPVCF_hourly_StScen2022_Mid_Case.csv)
---


##### [StScen2022_Mid_Case_LMI](inputs/dGen_Model_Inputs/StScen2022_Mid_Case_LMI) <a name='inputs/dGen_Model_Inputs/StScen2022_Mid_Case_LMI'></a>
  - [distPVcap_StScen2022_Mid_Case_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case_LMI/distPVcap_StScen2022_Mid_Case_LMI.csv)
---

  - [distPVCF_hourly_StScen2022_Mid_Case_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case_LMI/distPVCF_hourly_StScen2022_Mid_Case_LMI.csv)
---


##### [StScen2022_Mid_Case_noIRA](inputs/dGen_Model_Inputs/StScen2022_Mid_Case_noIRA) <a name='inputs/dGen_Model_Inputs/StScen2022_Mid_Case_noIRA'></a>
  - [distPVcap_StScen2022_Mid_Case_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case_noIRA/distPVcap_StScen2022_Mid_Case_noIRA.csv)
---

  - [distPVCF_hourly_StScen2022_Mid_Case_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case_noIRA/distPVCF_hourly_StScen2022_Mid_Case_noIRA.csv)
---


#### [financials](inputs/financials) <a name='inputs/financials'></a>
  - [construction_schedules_default.csv](/inputs/financials/construction_schedules_default.csv)
---

  - [construction_times_default.csv](/inputs/financials/construction_times_default.csv)
---

  - [currency_incentives.csv](/inputs/financials/currency_incentives.csv)
---

  - [depreciation_schedules_default.csv](/inputs/financials/depreciation_schedules_default.csv)
---

  - [financials_hydrogen.csv](/inputs/financials/financials_hydrogen.csv)
---

  - [financials_sys_ATB2020.csv](/inputs/financials/financials_sys_ATB2020.csv)
---

  - [financials_sys_ATB2021.csv](/inputs/financials/financials_sys_ATB2021.csv)
---

  - [financials_sys_ATB2022.csv](/inputs/financials/financials_sys_ATB2022.csv)
---

  - [financials_sys_ATB2023.csv](/inputs/financials/financials_sys_ATB2023.csv)
---

  - [financials_tech_ATB2020.csv](/inputs/financials/financials_tech_ATB2020.csv)
---

  - [financials_tech_ATB2021.csv](/inputs/financials/financials_tech_ATB2021.csv)
---

  - [financials_tech_ATB2022.csv](/inputs/financials/financials_tech_ATB2022.csv)
---

  - [financials_tech_ATB2023.csv](/inputs/financials/financials_tech_ATB2023.csv)
---

  - [financials_transmission_30ITC_0pen_2022_2031.csv](/inputs/financials/financials_transmission_30ITC_0pen_2022_2031.csv)
---

  - [financials_transmission_default.csv](/inputs/financials/financials_transmission_default.csv)
---

  - [incentives_annual.csv](/inputs/financials/incentives_annual.csv)
---

  - [incentives_biennial.csv](/inputs/financials/incentives_biennial.csv)
---

  - [incentives_ext_ce_dir_solPTC_r02.csv](/inputs/financials/incentives_ext_ce_dir_solPTC_r02.csv)
---

  - [incentives_ira.csv](/inputs/financials/incentives_ira.csv)
---

  - [incentives_ira_hii.csv](/inputs/financials/incentives_ira_hii.csv)
---

  - [incentives_ira_lii.csv](/inputs/financials/incentives_ira_lii.csv)
---

  - [incentives_PTC_ITC_ext.csv](/inputs/financials/incentives_PTC_ITC_ext.csv)
---

  - [incentives_wind_PTC_PV_ITC_2050.csv](/inputs/financials/incentives_wind_PTC_PV_ITC_2050.csv)
---

  - [inflation_default.csv](/inputs/financials/inflation_default.csv)
---

  - [reg_cap_cost_mult_default.csv](/inputs/financials/reg_cap_cost_mult_default.csv)
---

  - [retire_penalty.csv](/inputs/financials/retire_penalty.csv)
---

  - [supply_chain_adjust.csv](/inputs/financials/supply_chain_adjust.csv)
---

  - [tc_phaseout_schedule_ira2022.csv](/inputs/financials/tc_phaseout_schedule_ira2022.csv)
---


#### [fuelprices](inputs/fuelprices) <a name='inputs/fuelprices'></a>
  - [alpha_AEO_2021_HOG.csv](/inputs/fuelprices/alpha_AEO_2021_HOG.csv)
---

  - [alpha_AEO_2021_LOG.csv](/inputs/fuelprices/alpha_AEO_2021_LOG.csv)
---

  - [alpha_AEO_2021_reference.csv](/inputs/fuelprices/alpha_AEO_2021_reference.csv)
---

  - [alpha_AEO_2022_HOG.csv](/inputs/fuelprices/alpha_AEO_2022_HOG.csv)
---

  - [alpha_AEO_2022_LOG.csv](/inputs/fuelprices/alpha_AEO_2022_LOG.csv)
---

  - [alpha_AEO_2022_reference.csv](/inputs/fuelprices/alpha_AEO_2022_reference.csv)
---

  - [alpha_AEO_2023_HOG.csv](/inputs/fuelprices/alpha_AEO_2023_HOG.csv)
---

  - [alpha_AEO_2023_LOG.csv](/inputs/fuelprices/alpha_AEO_2023_LOG.csv)
---

  - [alpha_AEO_2023_reference.csv](/inputs/fuelprices/alpha_AEO_2023_reference.csv)
---

  - [cd_beta0.csv](/inputs/fuelprices/cd_beta0.csv)
---

  - [cd_beta0_allsector.csv](/inputs/fuelprices/cd_beta0_allsector.csv)
---

  - [cendivweights.csv](/inputs/fuelprices/cendivweights.csv)
---

  - [coal_AEO_2021_reference.csv](/inputs/fuelprices/coal_AEO_2021_reference.csv)
---

  - [coal_AEO_2022_reference.csv](/inputs/fuelprices/coal_AEO_2022_reference.csv)
---

  - [coal_AEO_2023_reference.csv](/inputs/fuelprices/coal_AEO_2023_reference.csv)
---

  - [dollaryear.csv](/inputs/fuelprices/dollaryear.csv)
    - **Description:** Dollar year mapping for each fuel price scenario
---

  - [h2-ct_10.csv](/inputs/fuelprices/h2-ct_10.csv)
---

  - [h2-ct_30.csv](/inputs/fuelprices/h2-ct_30.csv)
---

  - [h2-ct_reference.csv](/inputs/fuelprices/h2-ct_reference.csv)
---

  - [ng_AEO_2021_HOG.csv](/inputs/fuelprices/ng_AEO_2021_HOG.csv)
---

  - [ng_AEO_2021_LOG.csv](/inputs/fuelprices/ng_AEO_2021_LOG.csv)
---

  - [ng_AEO_2021_reference.csv](/inputs/fuelprices/ng_AEO_2021_reference.csv)
---

  - [ng_AEO_2022_HOG.csv](/inputs/fuelprices/ng_AEO_2022_HOG.csv)
---

  - [ng_AEO_2022_LOG.csv](/inputs/fuelprices/ng_AEO_2022_LOG.csv)
---

  - [ng_AEO_2022_reference.csv](/inputs/fuelprices/ng_AEO_2022_reference.csv)
---

  - [ng_AEO_2023_HOG.csv](/inputs/fuelprices/ng_AEO_2023_HOG.csv)
---

  - [ng_AEO_2023_LOG.csv](/inputs/fuelprices/ng_AEO_2023_LOG.csv)
---

  - [ng_AEO_2023_reference.csv](/inputs/fuelprices/ng_AEO_2023_reference.csv)
---

  - [ng_demand_AEO_2021_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2021_HOG.csv)
---

  - [ng_demand_AEO_2021_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2021_LOG.csv)
---

  - [ng_demand_AEO_2021_reference.csv](/inputs/fuelprices/ng_demand_AEO_2021_reference.csv)
---

  - [ng_demand_AEO_2022_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2022_HOG.csv)
---

  - [ng_demand_AEO_2022_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2022_LOG.csv)
---

  - [ng_demand_AEO_2022_reference.csv](/inputs/fuelprices/ng_demand_AEO_2022_reference.csv)
---

  - [ng_demand_AEO_2023_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2023_HOG.csv)
---

  - [ng_demand_AEO_2023_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2023_LOG.csv)
---

  - [ng_demand_AEO_2023_reference.csv](/inputs/fuelprices/ng_demand_AEO_2023_reference.csv)
---

  - [ng_tot_demand_AEO_2021_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2021_HOG.csv)
---

  - [ng_tot_demand_AEO_2021_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2021_LOG.csv)
---

  - [ng_tot_demand_AEO_2021_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2021_reference.csv)
---

  - [ng_tot_demand_AEO_2022_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_HOG.csv)
---

  - [ng_tot_demand_AEO_2022_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_LOG.csv)
---

  - [ng_tot_demand_AEO_2022_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_reference.csv)
---

  - [ng_tot_demand_AEO_2023_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_HOG.csv)
---

  - [ng_tot_demand_AEO_2023_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_LOG.csv)
---

  - [ng_tot_demand_AEO_2023_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_reference.csv)
---

  - [re-ct_40.csv](/inputs/fuelprices/re-ct_40.csv)
---

  - [uranium_AEO_2021_reference.csv](/inputs/fuelprices/uranium_AEO_2021_reference.csv)
---

  - [uranium_AEO_2022_reference.csv](/inputs/fuelprices/uranium_AEO_2022_reference.csv)
---

  - [uranium_AEO_2023_reference.csv](/inputs/fuelprices/uranium_AEO_2023_reference.csv)
---


#### [geothermal](inputs/geothermal) <a name='inputs/geothermal'></a>
  - [geo_rsc_ATB_2023.csv](/inputs/geothermal/geo_rsc_ATB_2023.csv)
---


#### [growth_constraints](inputs/growth_constraints) <a name='inputs/growth_constraints'></a>
  - [gbin_min.csv](/inputs/growth_constraints/gbin_min.csv)
---

  - [growth_bin_size_mult.csv](/inputs/growth_constraints/growth_bin_size_mult.csv)
---

  - [growth_limit_absolute.csv](/inputs/growth_constraints/growth_limit_absolute.csv)
---

  - [growth_penalty.csv](/inputs/growth_constraints/growth_penalty.csv)
---


#### [hydrodata](inputs/hydrodata) <a name='inputs/hydrodata'></a>
  - [hyd_fom.csv](/inputs/hydrodata/hyd_fom.csv)
    - **Description:** Regional FOM costs for hydro
---

  - [hydro_mingen.csv](/inputs/hydrodata/hydro_mingen.csv)
---


#### [loaddata](inputs/loaddata) <a name='inputs/loaddata'></a>
  - [Baseline_load_hourly.h5](/inputs/loaddata/Baseline_load_hourly.h5)
---

  - [cangrowth.csv](/inputs/loaddata/cangrowth.csv)
    - **Description:** Canada load growth multiplier
---

  - [Clean2035_load_hourly.h5](/inputs/loaddata/Clean2035_load_hourly.h5)
---

  - [Clean2035_LTS_load_hourly.h5](/inputs/loaddata/Clean2035_LTS_load_hourly.h5)
---

  - [Clean2035clip1pct_load_hourly.h5](/inputs/loaddata/Clean2035clip1pct_load_hourly.h5)
---

  - [demand_AEO_2021_high.csv](/inputs/loaddata/demand_AEO_2021_high.csv)
---

  - [demand_AEO_2021_low.csv](/inputs/loaddata/demand_AEO_2021_low.csv)
---

  - [demand_AEO_2021_reference.csv](/inputs/loaddata/demand_AEO_2021_reference.csv)
---

  - [demand_AEO_2022_high.csv](/inputs/loaddata/demand_AEO_2022_high.csv)
---

  - [demand_AEO_2022_low.csv](/inputs/loaddata/demand_AEO_2022_low.csv)
---

  - [demand_AEO_2022_reference.csv](/inputs/loaddata/demand_AEO_2022_reference.csv)
---

  - [demand_AEO_2023_high.csv](/inputs/loaddata/demand_AEO_2023_high.csv)
---

  - [demand_AEO_2023_low.csv](/inputs/loaddata/demand_AEO_2023_low.csv)
---

  - [demand_AEO_2023_reference.csv](/inputs/loaddata/demand_AEO_2023_reference.csv)
---

  - [demand_flat_2020_onward.csv](/inputs/loaddata/demand_flat_2020_onward.csv)
---

  - [EER_100by2050_load_hourly.h5](/inputs/loaddata/EER_100by2050_load_hourly.h5)
---

  - [EER_Baseline_AEO2022_load_hourly.h5](/inputs/loaddata/EER_Baseline_AEO2022_load_hourly.h5)
---

  - [EER_IRAlow_load_hourly.h5](/inputs/loaddata/EER_IRAlow_load_hourly.h5)
---

  - [EER_IRAmoderate_load_hourly.h5](/inputs/loaddata/EER_IRAmoderate_load_hourly.h5)
---

  - [EPHIGH_load_hourly.h5](/inputs/loaddata/EPHIGH_load_hourly.h5)
---

  - [EPMEDIUM_load_hourly.h5](/inputs/loaddata/EPMEDIUM_load_hourly.h5)
---

  - [EPMEDIUMStretch2040_load_hourly.h5](/inputs/loaddata/EPMEDIUMStretch2040_load_hourly.h5)
---

  - [EPMEDIUMStretch2046_load_hourly.h5](/inputs/loaddata/EPMEDIUMStretch2046_load_hourly.h5)
---

  - [EPREFERENCE_load_hourly.h5](/inputs/loaddata/EPREFERENCE_load_hourly.h5)
---

  - [ev_dynamic_demand.csv](/inputs/loaddata/ev_dynamic_demand.csv)
---

  - [historic_load_hourly.h5](/inputs/loaddata/historic_load_hourly.h5)
---

  - [mex_growth_rate.csv](/inputs/loaddata/mex_growth_rate.csv)
    - **Description:** Mexico load growth multiplier
---


#### [national_generation](inputs/national_generation) <a name='inputs/national_generation'></a>
  - [gen_mandate_tech_list.csv](/inputs/national_generation/gen_mandate_tech_list.csv)
---

  - [gen_mandate_trajectory.csv](/inputs/national_generation/gen_mandate_trajectory.csv)
---


#### [plant_characteristics](inputs/plant_characteristics) <a name='inputs/plant_characteristics'></a>
  - [battery_ATB_2020_advanced.csv](/inputs/plant_characteristics/battery_ATB_2020_advanced.csv)
---

  - [battery_ATB_2020_conservative.csv](/inputs/plant_characteristics/battery_ATB_2020_conservative.csv)
---

  - [battery_ATB_2020_moderate.csv](/inputs/plant_characteristics/battery_ATB_2020_moderate.csv)
---

  - [battery_ATB_2021_advanced.csv](/inputs/plant_characteristics/battery_ATB_2021_advanced.csv)
---

  - [battery_ATB_2021_conservative.csv](/inputs/plant_characteristics/battery_ATB_2021_conservative.csv)
---

  - [battery_ATB_2021_moderate.csv](/inputs/plant_characteristics/battery_ATB_2021_moderate.csv)
---

  - [battery_ATB_2022_advanced.csv](/inputs/plant_characteristics/battery_ATB_2022_advanced.csv)
---

  - [battery_ATB_2022_conservative.csv](/inputs/plant_characteristics/battery_ATB_2022_conservative.csv)
---

  - [battery_ATB_2022_moderate.csv](/inputs/plant_characteristics/battery_ATB_2022_moderate.csv)
---

  - [battery_ATB_2023_advanced.csv](/inputs/plant_characteristics/battery_ATB_2023_advanced.csv)
---

  - [battery_ATB_2023_conservative.csv](/inputs/plant_characteristics/battery_ATB_2023_conservative.csv)
---

  - [battery_ATB_2023_moderate.csv](/inputs/plant_characteristics/battery_ATB_2023_moderate.csv)
---

  - [beccs_BVRE_2021_high.csv](/inputs/plant_characteristics/beccs_BVRE_2021_high.csv)
---

  - [beccs_BVRE_2021_low.csv](/inputs/plant_characteristics/beccs_BVRE_2021_low.csv)
---

  - [beccs_BVRE_2021_mid.csv](/inputs/plant_characteristics/beccs_BVRE_2021_mid.csv)
---

  - [beccs_lowcost.csv](/inputs/plant_characteristics/beccs_lowcost.csv)
---

  - [beccs_reference.csv](/inputs/plant_characteristics/beccs_reference.csv)
---

  - [caes_reference.csv](/inputs/plant_characteristics/caes_reference.csv)
    - **Description:** Caes costs for the reference cost scenario
---

  - [ccsflex_ATB_2020_cost.csv](/inputs/plant_characteristics/ccsflex_ATB_2020_cost.csv)
---

  - [ccsflex_ATB_2020_perf.csv](/inputs/plant_characteristics/ccsflex_ATB_2020_perf.csv)
---

  - [conv_ATB_2020.csv](/inputs/plant_characteristics/conv_ATB_2020.csv)
    - **Description:** Convential generator costs from the 2020 ATB
---

  - [conv_ATB_2020_low_ccs_cost.csv](/inputs/plant_characteristics/conv_ATB_2020_low_ccs_cost.csv)
---

  - [conv_ATB_2020_low_nuclear_cost.csv](/inputs/plant_characteristics/conv_ATB_2020_low_nuclear_cost.csv)
---

  - [conv_ATB_2021.csv](/inputs/plant_characteristics/conv_ATB_2021.csv)
---

  - [conv_ATB_2021_CCS_95_max.csv](/inputs/plant_characteristics/conv_ATB_2021_CCS_95_max.csv)
---

  - [conv_ATB_2021_low_ccs_cost.csv](/inputs/plant_characteristics/conv_ATB_2021_low_ccs_cost.csv)
---

  - [conv_ATB_2021_low_nuclear_and_ccs_cost.csv](/inputs/plant_characteristics/conv_ATB_2021_low_nuclear_and_ccs_cost.csv)
---

  - [conv_ATB_2021_low_nuclear_cost.csv](/inputs/plant_characteristics/conv_ATB_2021_low_nuclear_cost.csv)
---

  - [conv_ATB_2021_low_smr.csv](/inputs/plant_characteristics/conv_ATB_2021_low_smr.csv)
---

  - [conv_ATB_2021_very_low_smr.csv](/inputs/plant_characteristics/conv_ATB_2021_very_low_smr.csv)
---

  - [conv_ATB_2022.csv](/inputs/plant_characteristics/conv_ATB_2022.csv)
---

  - [conv_ATB_2022_low_nuclear_and_ccs_cost.csv](/inputs/plant_characteristics/conv_ATB_2022_low_nuclear_and_ccs_cost.csv)
---

  - [conv_ATB_2023.csv](/inputs/plant_characteristics/conv_ATB_2023.csv)
---

  - [cost_opres_default.csv](/inputs/plant_characteristics/cost_opres_default.csv)
---

  - [cost_opres_market.csv](/inputs/plant_characteristics/cost_opres_market.csv)
---

  - [csp_ATB_2020_advanced.csv](/inputs/plant_characteristics/csp_ATB_2020_advanced.csv)
---

  - [csp_ATB_2020_conservative.csv](/inputs/plant_characteristics/csp_ATB_2020_conservative.csv)
---

  - [csp_ATB_2020_moderate.csv](/inputs/plant_characteristics/csp_ATB_2020_moderate.csv)
---

  - [csp_ATB_2021_advanced.csv](/inputs/plant_characteristics/csp_ATB_2021_advanced.csv)
---

  - [csp_ATB_2021_conservative.csv](/inputs/plant_characteristics/csp_ATB_2021_conservative.csv)
---

  - [csp_ATB_2021_moderate.csv](/inputs/plant_characteristics/csp_ATB_2021_moderate.csv)
---

  - [csp_ATB_2022_advanced.csv](/inputs/plant_characteristics/csp_ATB_2022_advanced.csv)
---

  - [csp_ATB_2022_conservative.csv](/inputs/plant_characteristics/csp_ATB_2022_conservative.csv)
---

  - [csp_ATB_2022_moderate.csv](/inputs/plant_characteristics/csp_ATB_2022_moderate.csv)
---

  - [csp_ATB_2023_advanced.csv](/inputs/plant_characteristics/csp_ATB_2023_advanced.csv)
---

  - [csp_ATB_2023_conservative.csv](/inputs/plant_characteristics/csp_ATB_2023_conservative.csv)
---

  - [csp_ATB_2023_moderate.csv](/inputs/plant_characteristics/csp_ATB_2023_moderate.csv)
---

  - [csp_SunShot2030.csv](/inputs/plant_characteristics/csp_SunShot2030.csv)
    - **Description:** Csp costs from the SunShot2030 cost scenario
---

  - [dollaryear.csv](/inputs/plant_characteristics/dollaryear.csv)
    - **Description:** Dollar year mapping for each plant cost scenario
---

  - [dr_Baseline.csv](/inputs/plant_characteristics/dr_Baseline.csv)
---

  - [dr_Baseline_shed.csv](/inputs/plant_characteristics/dr_Baseline_shed.csv)
---

  - [dr_Baseline_shift.csv](/inputs/plant_characteristics/dr_Baseline_shift.csv)
---

  - [dr_none.csv](/inputs/plant_characteristics/dr_none.csv)
---

  - [dr_test.csv](/inputs/plant_characteristics/dr_test.csv)
---

  - [geo_ATB_2023_advanced.csv](/inputs/plant_characteristics/geo_ATB_2023_advanced.csv)
---

  - [geo_ATB_2023_conservative.csv](/inputs/plant_characteristics/geo_ATB_2023_conservative.csv)
---

  - [geo_ATB_2023_moderate.csv](/inputs/plant_characteristics/geo_ATB_2023_moderate.csv)
---

  - [h2-ct_ATB_2020.csv](/inputs/plant_characteristics/h2-ct_ATB_2020.csv)
---

  - [h2-ct_ATB_2021.csv](/inputs/plant_characteristics/h2-ct_ATB_2021.csv)
---

  - [h2-ct_ATB_2022.csv](/inputs/plant_characteristics/h2-ct_ATB_2022.csv)
---

  - [h2-ct_ATB_2023.csv](/inputs/plant_characteristics/h2-ct_ATB_2023.csv)
---

  - [heat_rate_adj.csv](/inputs/plant_characteristics/heat_rate_adj.csv)
    - **Description:** Heat rate adjustment multiplier by technology
---

  - [heat_rate_penalty_spin.csv](/inputs/plant_characteristics/heat_rate_penalty_spin.csv)
---

  - [hydro_ATB_2019_constant.csv](/inputs/plant_characteristics/hydro_ATB_2019_constant.csv)
    - **Description:** Hydro costs from the 2019 ATB constant cost scenario
---

  - [hydro_ATB_2019_low.csv](/inputs/plant_characteristics/hydro_ATB_2019_low.csv)
    - **Description:** Hydro costs from the 2019 ATB low cost scenario
---

  - [hydro_ATB_2019_mid.csv](/inputs/plant_characteristics/hydro_ATB_2019_mid.csv)
    - **Description:** Hydro costs from the 2019 ATB mid cost scenario
---

  - [hydro_lowPSH.csv](/inputs/plant_characteristics/hydro_lowPSH.csv)
---

  - [ice_fom.csv](/inputs/plant_characteristics/ice_fom.csv)
    - **Description:** Fixed O&M for ice storage
---

  - [minCF.csv](/inputs/plant_characteristics/minCF.csv)
    - **Description:** minimum annual capacity factor for each tech fleet - applied to i-rto
---

  - [minloadfrac0.csv](/inputs/plant_characteristics/minloadfrac0.csv)
    - **Description:** characteristics/minloadfrac0 database of minloadbed generator cs
---

  - [ofs-wind_ATB_2020_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_advanced.csv)
---

  - [ofs-wind_ATB_2020_advanced_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_advanced_rsc_mult.csv)
---

  - [ofs-wind_ATB_2020_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_conservative.csv)
---

  - [ofs-wind_ATB_2020_conservative_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_conservative_rsc_mult.csv)
---

  - [ofs-wind_ATB_2020_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_moderate.csv)
---

  - [ofs-wind_ATB_2020_moderate_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_moderate_rsc_mult.csv)
---

  - [ofs-wind_ATB_2021_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_advanced.csv)
---

  - [ofs-wind_ATB_2021_advanced_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_advanced_rsc_mult.csv)
---

  - [ofs-wind_ATB_2021_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_conservative.csv)
---

  - [ofs-wind_ATB_2021_conservative_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_conservative_rsc_mult.csv)
---

  - [ofs-wind_ATB_2021_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_moderate.csv)
---

  - [ofs-wind_ATB_2021_moderate_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_moderate_rsc_mult.csv)
---

  - [ofs-wind_ATB_2022_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_advanced.csv)
---

  - [ofs-wind_ATB_2022_advanced_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_advanced_noFloating.csv)
---

  - [ofs-wind_ATB_2022_advanced_noFloating_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_advanced_noFloating_rsc_mult.csv)
---

  - [ofs-wind_ATB_2022_advanced_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_advanced_rsc_mult.csv)
---

  - [ofs-wind_ATB_2022_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_conservative.csv)
---

  - [ofs-wind_ATB_2022_conservative_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_conservative_noFloating.csv)
---

  - [ofs-wind_ATB_2022_conservative_noFloating_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_conservative_noFloating_rsc_mult.csv)
---

  - [ofs-wind_ATB_2022_conservative_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_conservative_rsc_mult.csv)
---

  - [ofs-wind_ATB_2022_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_moderate.csv)
---

  - [ofs-wind_ATB_2022_moderate_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_moderate_noFloating.csv)
---

  - [ofs-wind_ATB_2022_moderate_noFloating_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_moderate_noFloating_rsc_mult.csv)
---

  - [ofs-wind_ATB_2022_moderate_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_moderate_rsc_mult.csv)
---

  - [ofs-wind_ATB_2023_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_advanced.csv)
---

  - [ofs-wind_ATB_2023_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_conservative.csv)
---

  - [ofs-wind_ATB_2023_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_moderate.csv)
---

  - [ons-wind_ATB_2020_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2020_advanced.csv)
---

  - [ons-wind_ATB_2020_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2020_conservative.csv)
---

  - [ons-wind_ATB_2020_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2020_moderate.csv)
---

  - [ons-wind_ATB_2021_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2021_advanced.csv)
---

  - [ons-wind_ATB_2021_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2021_conservative.csv)
---

  - [ons-wind_ATB_2021_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2021_moderate.csv)
---

  - [ons-wind_ATB_2022_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2022_advanced.csv)
---

  - [ons-wind_ATB_2022_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2022_conservative.csv)
---

  - [ons-wind_ATB_2022_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2022_moderate.csv)
---

  - [ons-wind_ATB_2023_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_advanced.csv)
---

  - [ons-wind_ATB_2023_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_conservative.csv)
---

  - [ons-wind_ATB_2023_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_moderate.csv)
---

  - [outage_forced.csv](/inputs/plant_characteristics/outage_forced.csv)
    - **Description:** Forced outage rates by technology
---

  - [outage_planned.csv](/inputs/plant_characteristics/outage_planned.csv)
    - **Description:** Planned outage rate by technology
---

  - [pvb_benchmark2020.csv](/inputs/plant_characteristics/pvb_benchmark2020.csv)
---

  - [ramprate.csv](/inputs/plant_characteristics/ramprate.csv)
    - **Description:** Generator ramp rates by technology
---

  - [unitsize.csv](/inputs/plant_characteristics/unitsize.csv)
---

  - [upv_ATB_2020_advanced.csv](/inputs/plant_characteristics/upv_ATB_2020_advanced.csv)
---

  - [upv_ATB_2020_conservative.csv](/inputs/plant_characteristics/upv_ATB_2020_conservative.csv)
---

  - [upv_ATB_2020_moderate.csv](/inputs/plant_characteristics/upv_ATB_2020_moderate.csv)
---

  - [upv_ATB_2021_advanced.csv](/inputs/plant_characteristics/upv_ATB_2021_advanced.csv)
---

  - [upv_ATB_2021_conservative.csv](/inputs/plant_characteristics/upv_ATB_2021_conservative.csv)
---

  - [upv_ATB_2021_moderate.csv](/inputs/plant_characteristics/upv_ATB_2021_moderate.csv)
---

  - [upv_ATB_2022_advanced.csv](/inputs/plant_characteristics/upv_ATB_2022_advanced.csv)
---

  - [upv_ATB_2022_conservative.csv](/inputs/plant_characteristics/upv_ATB_2022_conservative.csv)
---

  - [upv_ATB_2022_moderate.csv](/inputs/plant_characteristics/upv_ATB_2022_moderate.csv)
---

  - [upv_ATB_2023_advanced.csv](/inputs/plant_characteristics/upv_ATB_2023_advanced.csv)
---

  - [upv_ATB_2023_conservative.csv](/inputs/plant_characteristics/upv_ATB_2023_conservative.csv)
---

  - [upv_ATB_2023_moderate.csv](/inputs/plant_characteristics/upv_ATB_2023_moderate.csv)
---


#### [reserves](inputs/reserves) <a name='inputs/reserves'></a>
  - [opres_periods.csv](/inputs/reserves/opres_periods.csv)
---

  - [prm_annual.csv](/inputs/reserves/prm_annual.csv)
    - **Description:** Annual planning reserve margin by NERC region
---

  - [ramptime.csv](/inputs/reserves/ramptime.csv)
---


#### [RPSdata](inputs/RPSdata) <a name='inputs/RPSdata'></a>
  - [national_rps_frac_allScen.csv](/inputs/RPSdata/national_rps_frac_allScen.csv)
---


#### [shapefiles](inputs/shapefiles) <a name='inputs/shapefiles'></a>
  - [ctus_cs_polygons_BVRE.csv](/inputs/shapefiles/ctus_cs_polygons_BVRE.csv)
---

  - [ctus_r_cs_spurlines_200mi.csv](/inputs/shapefiles/ctus_r_cs_spurlines_200mi.csv)
---

  - [r_rr_lines_to_25_nearest_neighbors.csv](/inputs/shapefiles/r_rr_lines_to_25_nearest_neighbors.csv)
---

  - [US_CAN_MEX_PCA_polygons.csv](/inputs/shapefiles/US_CAN_MEX_PCA_polygons.csv)
---

  - [US_transmission_endpoints_and_CAN_MEX_centroids.csv](/inputs/shapefiles/US_transmission_endpoints_and_CAN_MEX_centroids.csv)
---


##### [WKT_csvs](inputs/shapefiles/WKT_csvs) <a name='inputs/shapefiles/WKT_csvs'></a>
  - [cendiv_WKT.csv](/inputs/shapefiles/WKT_csvs/cendiv_WKT.csv)
---

  - [country_WKT.csv](/inputs/shapefiles/WKT_csvs/country_WKT.csv)
---

  - [customreg_WKT.csv](/inputs/shapefiles/WKT_csvs/customreg_WKT.csv)
---

  - [interconnect_WKT.csv](/inputs/shapefiles/WKT_csvs/interconnect_WKT.csv)
---

  - [nerc_new_WKT.csv](/inputs/shapefiles/WKT_csvs/nerc_new_WKT.csv)
---

  - [nerc_WKT.csv](/inputs/shapefiles/WKT_csvs/nerc_WKT.csv)
---

  - [rto_WKT.csv](/inputs/shapefiles/WKT_csvs/rto_WKT.csv)
---

  - [st_WKT.csv](/inputs/shapefiles/WKT_csvs/st_WKT.csv)
---

  - [transreg_WKT.csv](/inputs/shapefiles/WKT_csvs/transreg_WKT.csv)
---

  - [usda_WKT.csv](/inputs/shapefiles/WKT_csvs/usda_WKT.csv)
---


#### [state_policies](inputs/state_policies) <a name='inputs/state_policies'></a>
  - [acp_disallowed.csv](/inputs/state_policies/acp_disallowed.csv)
---

  - [acp_prices.csv](/inputs/state_policies/acp_prices.csv)
---

  - [ces_fraction.csv](/inputs/state_policies/ces_fraction.csv)
    - **Description:** Annual compliance for states with a CES policy
---

  - [forced_retirements.csv](/inputs/state_policies/forced_retirements.csv)
    - **Description:** List of regions with mandatory retirement policies for certain technologies
---

  - [hydrofrac_policy.csv](/inputs/state_policies/hydrofrac_policy.csv)
---

  - [ng_crf_penalty_st.csv](/inputs/state_policies/ng_crf_penalty_st.csv)
---

  - [nuclear_ba_ban_list.csv](/inputs/state_policies/nuclear_ba_ban_list.csv)
---

  - [nuclear_subsidies.csv](/inputs/state_policies/nuclear_subsidies.csv)
---

  - [offshore_req_30by30.csv](/inputs/state_policies/offshore_req_30by30.csv)
---

  - [offshore_req_default.csv](/inputs/state_policies/offshore_req_default.csv)
---

  - [oosfrac.csv](/inputs/state_policies/oosfrac.csv)
---

  - [recstyle.csv](/inputs/state_policies/recstyle.csv)
---

  - [rectable.csv](/inputs/state_policies/rectable.csv)
    - **Description:** Table defining which states are allowed to trade RECs
---

  - [rps_fraction.csv](/inputs/state_policies/rps_fraction.csv)
---

  - [storage_mandates.csv](/inputs/state_policies/storage_mandates.csv)
    - **Description:** Energy storage mandates by region
---

  - [techs_banned.csv](/inputs/state_policies/techs_banned.csv)
    - **Description:** Table that bans certain technologies by state
---

  - [techs_banned_ces.csv](/inputs/state_policies/techs_banned_ces.csv)
---

  - [techs_banned_imports_rps.csv](/inputs/state_policies/techs_banned_imports_rps.csv)
---

  - [techs_banned_rps.csv](/inputs/state_policies/techs_banned_rps.csv)
---

  - [unbundled_limit_ces.csv](/inputs/state_policies/unbundled_limit_ces.csv)
---

  - [unbundled_limit_rps.csv](/inputs/state_policies/unbundled_limit_rps.csv)
---


#### [storagedata](inputs/storagedata) <a name='inputs/storagedata'></a>
  - [PSH_supply_curves_durations.csv](/inputs/storagedata/PSH_supply_curves_durations.csv)
---

  - [storage_duration.csv](/inputs/storagedata/storage_duration.csv)
---

  - [storage_duration_pshdata.csv](/inputs/storagedata/storage_duration_pshdata.csv)
---

  - [storinmaxfrac.csv](/inputs/storagedata/storinmaxfrac.csv)
---


#### [supplycurvedata](inputs/supplycurvedata) <a name='inputs/supplycurvedata'></a>
  - [bio_supplycurve.csv](/inputs/supplycurvedata/bio_supplycurve.csv)
    - **Description:** Regional biomass supply and costs by resource class
---

  - [csp_supply_curve-reference.csv](/inputs/supplycurvedata/csp_supply_curve-reference.csv)
---

  - [dollaryear.csv](/inputs/supplycurvedata/dollaryear.csv)
---

  - [DUPV_supply_curves_capacity_2018.csv](/inputs/supplycurvedata/DUPV_supply_curves_capacity_2018.csv)
---

  - [DUPV_supply_curves_capacity_NARIS.csv](/inputs/supplycurvedata/DUPV_supply_curves_capacity_NARIS.csv)
---

  - [DUPV_supply_curves_cost_2018.csv](/inputs/supplycurvedata/DUPV_supply_curves_cost_2018.csv)
---

  - [DUPV_supply_curves_cost_NARIS.csv](/inputs/supplycurvedata/DUPV_supply_curves_cost_NARIS.csv)
---

  - [geo_supply_curve_site-reference.csv](/inputs/supplycurvedata/geo_supply_curve_site-reference.csv)
---

  - [hyd_add_upg_cap.csv](/inputs/supplycurvedata/hyd_add_upg_cap.csv)
---

  - [hydcap.csv](/inputs/supplycurvedata/hydcap.csv)
---

  - [hydcost.csv](/inputs/supplycurvedata/hydcost.csv)
---

  - [PSH_supply_curves_capacity_10hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_10hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_capacity_10hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_10hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_capacity_10hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_10hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_capacity_10hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_10hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_capacity_12hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_12hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_capacity_12hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_12hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_capacity_12hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_12hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_capacity_12hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_12hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_capacity_8hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_8hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_capacity_8hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_8hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_capacity_8hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_8hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_capacity_8hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_8hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_capacity_vision.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_vision.csv)
---

  - [PSH_supply_curves_cost_10hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_10hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_cost_10hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_10hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_cost_10hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_10hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_cost_10hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_10hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_cost_12hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_12hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_cost_12hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_12hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_cost_12hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_12hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_cost_12hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_12hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_cost_8hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_8hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_cost_8hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_8hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_cost_8hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_8hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_cost_8hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_8hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_cost_vision.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_vision.csv)
---

  - [sitemap.csv](/inputs/supplycurvedata/sitemap.csv)
---

  - [sitemap_offshore.csv](/inputs/supplycurvedata/sitemap_offshore.csv)
---

  - [spurline_cost_1.csv](/inputs/supplycurvedata/spurline_cost_1.csv)
---

  - [trans_intra_cost_adder.csv](/inputs/supplycurvedata/trans_intra_cost_adder.csv)
---

  - [upv_supply_curve-limited.csv](/inputs/supplycurvedata/upv_supply_curve-limited.csv)
---

  - [upv_supply_curve-open.csv](/inputs/supplycurvedata/upv_supply_curve-open.csv)
---

  - [upv_supply_curve-reference.csv](/inputs/supplycurvedata/upv_supply_curve-reference.csv)
---

  - [wind-ofs_supply_curve-limited.csv](/inputs/supplycurvedata/wind-ofs_supply_curve-limited.csv)
---

  - [wind-ofs_supply_curve-open.csv](/inputs/supplycurvedata/wind-ofs_supply_curve-open.csv)
---

  - [wind-ons_supply_curve-limited.csv](/inputs/supplycurvedata/wind-ons_supply_curve-limited.csv)
---

  - [wind-ons_supply_curve-open.csv](/inputs/supplycurvedata/wind-ons_supply_curve-open.csv)
---

  - [wind-ons_supply_curve-reference.csv](/inputs/supplycurvedata/wind-ons_supply_curve-reference.csv)
---


##### [metadata](inputs/supplycurvedata/metadata) <a name='inputs/supplycurvedata/metadata'></a>
  - [rev_paths.csv](/inputs/supplycurvedata/metadata/rev_paths.csv)
---


#### [techs](inputs/techs) <a name='inputs/techs'></a>
  - [tech_resourceclass.csv](/inputs/techs/tech_resourceclass.csv)
---

  - [techs_default.csv](/inputs/techs/techs_default.csv)
    - **Description:** List of technologies to be used in the model
---

  - [techs_subsetForTesting.csv](/inputs/techs/techs_subsetForTesting.csv)
    - **Description:** Short list of technologies for testin
---


#### [transmission](inputs/transmission) <a name='inputs/transmission'></a>
  - [cost_hurdle_country.csv](/inputs/transmission/cost_hurdle_country.csv)
---

  - [r_rr_adj.csv](/inputs/transmission/r_rr_adj.csv)
---

  - [rev_transmission_basecost.csv](/inputs/transmission/rev_transmission_basecost.csv)
---

  - [routes_adjacent.csv](/inputs/transmission/routes_adjacent.csv)
---

  - [transmission_capacity_future_baseline.csv](/inputs/transmission/transmission_capacity_future_baseline.csv)
---

  - [transmission_capacity_future_default.csv](/inputs/transmission/transmission_capacity_future_default.csv)
---

  - [transmission_capacity_future_LCC_1500miles.csv](/inputs/transmission/transmission_capacity_future_LCC_1500miles.csv)
---

  - [transmission_capacity_future_LCC_20220808.csv](/inputs/transmission/transmission_capacity_future_LCC_20220808.csv)
---

  - [transmission_capacity_future_LCC_all.csv](/inputs/transmission/transmission_capacity_future_LCC_all.csv)
---

  - [transmission_capacity_future_LCC_SeamsD2b.csv](/inputs/transmission/transmission_capacity_future_LCC_SeamsD2b.csv)
---

  - [transmission_capacity_future_LCC_SeamsD3_certain.csv](/inputs/transmission/transmission_capacity_future_LCC_SeamsD3_certain.csv)
---

  - [transmission_capacity_future_LCC_SeamsD3_possible.csv](/inputs/transmission/transmission_capacity_future_LCC_SeamsD3_possible.csv)
---

  - [transmission_capacity_future_LCC_SeamsD3_possible_unconstrained.csv](/inputs/transmission/transmission_capacity_future_LCC_SeamsD3_possible_unconstrained.csv)
---

  - [transmission_capacity_future_VSC_all.csv](/inputs/transmission/transmission_capacity_future_VSC_all.csv)
---

  - [transmission_capacity_init_AC_NARIS2024-r.csv](/inputs/transmission/transmission_capacity_init_AC_NARIS2024-r.csv)
---

  - [transmission_capacity_init_AC_NARIS2024-transgrp.csv](/inputs/transmission/transmission_capacity_init_AC_NARIS2024-transgrp.csv)
---

  - [transmission_capacity_init_AC_REFS2009-r.csv](/inputs/transmission/transmission_capacity_init_AC_REFS2009-r.csv)
---

  - [transmission_capacity_init_nonAC.csv](/inputs/transmission/transmission_capacity_init_nonAC.csv)
---

  - [transmission_distance_cost_500kVac.csv](/inputs/transmission/transmission_distance_cost_500kVac.csv)
---

  - [transmission_distance_cost_500kVdc.csv](/inputs/transmission/transmission_distance_cost_500kVdc.csv)
---


#### [upgrades](inputs/upgrades) <a name='inputs/upgrades'></a>
  - [i_coolingtech_watersource_upgrades.csv](/inputs/upgrades/i_coolingtech_watersource_upgrades.csv)
---

  - [i_coolingtech_watersource_upgrades_link.csv](/inputs/upgrades/i_coolingtech_watersource_upgrades_link.csv)
---

  - [upgrade_link.csv](/inputs/upgrades/upgrade_link.csv)
---

  - [upgrade_mult.csv](/inputs/upgrades/upgrade_mult.csv)
---

  - [upgrade_mult_reduced.csv](/inputs/upgrades/upgrade_mult_reduced.csv)
---

  - [upgradelink_water.csv](/inputs/upgrades/upgradelink_water.csv)
---


#### [userinput](inputs/userinput) <a name='inputs/userinput'></a>
  - [futurefiles.csv](/inputs/userinput/futurefiles.csv)
---

  - [ivt_default.csv](/inputs/userinput/ivt_default.csv)
---

  - [ivt_small.csv](/inputs/userinput/ivt_small.csv)
---

  - [ivt_step.csv](/inputs/userinput/ivt_step.csv)
    - **Description:** ivt steps for endyears beyond 2050
---

  - [modeled_regions.csv](/inputs/userinput/modeled_regions.csv)
---

  - [windows_2100.csv](/inputs/userinput/windows_2100.csv)
    - **Description:** Window size for using window solve method to 2100
---

  - [windows_default.csv](/inputs/userinput/windows_default.csv)
    - **Description:** Window size for using window solve method
---

  - [windows_step10.csv](/inputs/userinput/windows_step10.csv)
    - **Description:** Window size for beyond2050step10
---

  - [windows_step5.csv](/inputs/userinput/windows_step5.csv)
    - **Description:** Window size for beyond2050step5
---


#### [valuestreams](inputs/valuestreams) <a name='inputs/valuestreams'></a>
  - [var_map.csv](/inputs/valuestreams/var_map.csv)
---


#### [variability](inputs/variability) <a name='inputs/variability'></a>
  - [d_szn_1.csv](/inputs/variability/d_szn_1.csv)
---

  - [d_szn_7.csv](/inputs/variability/d_szn_7.csv)
---

  - [h_dt_szn.csv](/inputs/variability/h_dt_szn.csv)
---

  - [hourly_operational_characteristics.csv](/inputs/variability/hourly_operational_characteristics.csv)
---

  - [index_hr_map_1.csv](/inputs/variability/index_hr_map_1.csv)
---

  - [index_hr_map_7.csv](/inputs/variability/index_hr_map_7.csv)
---

  - [period_szn_user.csv](/inputs/variability/period_szn_user.csv)
---

  - [reeds_ba_tz_map.csv](/inputs/variability/reeds_ba_tz_map.csv)
---

  - [set_allszn.csv](/inputs/variability/set_allszn.csv)
---

  - [set_szn.csv](/inputs/variability/set_szn.csv)
---


##### [multi_year](inputs/variability/multi_year) <a name='inputs/variability/multi_year'></a>
  - [csp-reference.h5](/inputs/variability/multi_year/csp-reference.h5)
---

  - [dupv.h5](/inputs/variability/multi_year/dupv.h5)
---

  - [upv-limited.h5](/inputs/variability/multi_year/upv-limited.h5)
---

  - [upv-open.h5](/inputs/variability/multi_year/upv-open.h5)
---

  - [upv-reference.h5](/inputs/variability/multi_year/upv-reference.h5)
---

  - [upv_140AC-reference.h5](/inputs/variability/multi_year/upv_140AC-reference.h5)
---

  - [upv_220AC-reference.h5](/inputs/variability/multi_year/upv_220AC-reference.h5)
---

  - [wind-ofs-limited.h5](/inputs/variability/multi_year/wind-ofs-limited.h5)
---

  - [wind-ofs-open.h5](/inputs/variability/multi_year/wind-ofs-open.h5)
---

  - [wind-ons-limited.h5](/inputs/variability/multi_year/wind-ons-limited.h5)
---

  - [wind-ons-open.h5](/inputs/variability/multi_year/wind-ons-open.h5)
---

  - [wind-ons-reference.h5](/inputs/variability/multi_year/wind-ons-reference.h5)
---


#### [waterclimate](inputs/waterclimate) <a name='inputs/waterclimate'></a>
  - [cost_cap_mult.csv](/inputs/waterclimate/cost_cap_mult.csv)
---

  - [cost_vom_mult.csv](/inputs/waterclimate/cost_vom_mult.csv)
---

  - [heat_rate_mult.csv](/inputs/waterclimate/heat_rate_mult.csv)
---

  - [i_coolingtech_watersource.csv](/inputs/waterclimate/i_coolingtech_watersource.csv)
---

  - [i_coolingtech_watersource_link.csv](/inputs/waterclimate/i_coolingtech_watersource_link.csv)
---

  - [tg_rsc_cspagg_tmp.csv](/inputs/waterclimate/tg_rsc_cspagg_tmp.csv)
---

  - [unapp_water_sea_distr.csv](/inputs/waterclimate/unapp_water_sea_distr.csv)
---

  - [wat_access_cap_cost.csv](/inputs/waterclimate/wat_access_cap_cost.csv)
---

  - [water_req_psh_10h_1_51.csv](/inputs/waterclimate/water_req_psh_10h_1_51.csv)
---

  - [water_with_cons_rate.csv](/inputs/waterclimate/water_with_cons_rate.csv)
---


### [postprocessing](postprocessing) <a name='postprocessing'></a>

#### [air_quality](postprocessing/air_quality) <a name='postprocessing/air_quality'></a>
  - [scenarios.csv](/postprocessing/air_quality/scenarios.csv)
---


##### [rcm_data](postprocessing/air_quality/rcm_data) <a name='postprocessing/air_quality/rcm_data'></a>
  - [counties_ACS_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/counties_ACS_high_stack_2017.csv)
---

  - [counties_H6C_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/counties_H6C_high_stack_2017.csv)
---

  - [marginal_damages_by_ReEDS_BA.csv](/postprocessing/air_quality/rcm_data/marginal_damages_by_ReEDS_BA.csv)
---

  - [states_ACS_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/states_ACS_high_stack_2017.csv)
---

  - [states_H6C_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/states_H6C_high_stack_2017.csv)
---


#### [bokehpivot](postprocessing/bokehpivot) <a name='postprocessing/bokehpivot'></a>

##### [in](postprocessing/bokehpivot/in) <a name='postprocessing/bokehpivot/in'></a>
  - [example_custom_styles.csv](/postprocessing/bokehpivot/in/example_custom_styles.csv)
---

  - [example_data_US_electric_power_generation.csv](/postprocessing/bokehpivot/in/example_data_US_electric_power_generation.csv)
---

  - [example_reeds_scenarios.csv](/postprocessing/bokehpivot/in/example_reeds_scenarios.csv)
---

  - [gis_centroid_rb.csv](/postprocessing/bokehpivot/in/gis_centroid_rb.csv)
---

  - [gis_nercr.csv](/postprocessing/bokehpivot/in/gis_nercr.csv)
---

  - [gis_nercr_new.csv](/postprocessing/bokehpivot/in/gis_nercr_new.csv)
---

  - [gis_rb.csv](/postprocessing/bokehpivot/in/gis_rb.csv)
---

  - [gis_rs.csv](/postprocessing/bokehpivot/in/gis_rs.csv)
---

  - [gis_rto.csv](/postprocessing/bokehpivot/in/gis_rto.csv)
---

  - [gis_st.csv](/postprocessing/bokehpivot/in/gis_st.csv)
---

  - [state_code.csv](/postprocessing/bokehpivot/in/state_code.csv)
---


###### [reeds2](postprocessing/bokehpivot/in/reeds2) <a name='postprocessing/bokehpivot/in/reeds2'></a>
  - [class_map.csv](/postprocessing/bokehpivot/in/reeds2/class_map.csv)
---

  - [class_style.csv](/postprocessing/bokehpivot/in/reeds2/class_style.csv)
---

  - [con_adj_map.csv](/postprocessing/bokehpivot/in/reeds2/con_adj_map.csv)
---

  - [con_adj_style.csv](/postprocessing/bokehpivot/in/reeds2/con_adj_style.csv)
---

  - [cost_cat_map.csv](/postprocessing/bokehpivot/in/reeds2/cost_cat_map.csv)
---

  - [cost_cat_style.csv](/postprocessing/bokehpivot/in/reeds2/cost_cat_style.csv)
---

  - [cost_cat_type.csv](/postprocessing/bokehpivot/in/reeds2/cost_cat_type.csv)
---

  - [ctt_map.csv](/postprocessing/bokehpivot/in/reeds2/ctt_map.csv)
---

  - [ctt_style.csv](/postprocessing/bokehpivot/in/reeds2/ctt_style.csv)
---

  - [hours.csv](/postprocessing/bokehpivot/in/reeds2/hours.csv)
---

  - [m_bar_width.csv](/postprocessing/bokehpivot/in/reeds2/m_bar_width.csv)
---

  - [m_map.csv](/postprocessing/bokehpivot/in/reeds2/m_map.csv)
---

  - [m_style.csv](/postprocessing/bokehpivot/in/reeds2/m_style.csv)
---

  - [process_style.csv](/postprocessing/bokehpivot/in/reeds2/process_style.csv)
---

  - [tech_ctt_wst.csv](/postprocessing/bokehpivot/in/reeds2/tech_ctt_wst.csv)
---

  - [tech_map.csv](/postprocessing/bokehpivot/in/reeds2/tech_map.csv)
---

  - [tech_style.csv](/postprocessing/bokehpivot/in/reeds2/tech_style.csv)
---

  - [trtype_map.csv](/postprocessing/bokehpivot/in/reeds2/trtype_map.csv)
---

  - [trtype_style.csv](/postprocessing/bokehpivot/in/reeds2/trtype_style.csv)
---

  - [wst_map.csv](/postprocessing/bokehpivot/in/reeds2/wst_map.csv)
---

  - [wst_style.csv](/postprocessing/bokehpivot/in/reeds2/wst_style.csv)
---


#### [documentation_tools](postprocessing/documentation_tools) <a name='postprocessing/documentation_tools'></a>
  - [local_sources_files_added.csv](/postprocessing/documentation_tools/local_sources_files_added.csv)
---

  - [sources_files_added.csv](/postprocessing/documentation_tools/sources_files_added.csv)
---

  - [sources_files_deleted.csv](/postprocessing/documentation_tools/sources_files_deleted.csv)
---

  - [sources_untracked_files.csv](/postprocessing/documentation_tools/sources_untracked_files.csv)
---


#### [land_use](postprocessing/land_use) <a name='postprocessing/land_use'></a>

##### [inputs](postprocessing/land_use/inputs) <a name='postprocessing/land_use/inputs'></a>
  - [federal_land_lookup.csv](/postprocessing/land_use/inputs/federal_land_lookup.csv)
---

  - [field_definitions.csv](/postprocessing/land_use/inputs/field_definitions.csv)
---

  - [nlcd_classifications.csv](/postprocessing/land_use/inputs/nlcd_classifications.csv)
---


#### [plots](postprocessing/plots) <a name='postprocessing/plots'></a>
  - [transmission-interface-coords.csv](/postprocessing/plots/transmission-interface-coords.csv)
---


#### [retail_rate_module](postprocessing/retail_rate_module) <a name='postprocessing/retail_rate_module'></a>
  - [capital_financing_assumptions.csv](/postprocessing/retail_rate_module/capital_financing_assumptions.csv)
---

  - [df_f861_contiguous.csv](/postprocessing/retail_rate_module/df_f861_contiguous.csv)
---

  - [df_f861_state.csv](/postprocessing/retail_rate_module/df_f861_state.csv)
---

  - [inputs.csv](/postprocessing/retail_rate_module/inputs.csv)
---

  - [inputs_default.csv](/postprocessing/retail_rate_module/inputs_default.csv)
---

  - [load_by_state_eia.csv](/postprocessing/retail_rate_module/load_by_state_eia.csv)
---

  - [map_i_to_tech.csv](/postprocessing/retail_rate_module/map_i_to_tech.csv)
---


##### [calc_historical_capex](postprocessing/retail_rate_module/calc_historical_capex) <a name='postprocessing/retail_rate_module/calc_historical_capex'></a>
  - [cap_cost_mult_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/cap_cost_mult_for_historical.csv)
---

  - [cost_cap_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/cost_cap_for_historical.csv)
---

  - [df_capex_init.csv](/postprocessing/retail_rate_module/calc_historical_capex/df_capex_init.csv)
---

  - [geo_cap_cost_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/geo_cap_cost_for_historical.csv)
---

  - [regions_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/regions_for_historical.csv)
---

  - [rsc_dat_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/rsc_dat_for_historical.csv)
---


##### [inputs](postprocessing/retail_rate_module/inputs) <a name='postprocessing/retail_rate_module/inputs'></a>
  - [Electric O & M Expenses-IOU-1993-2019.csv](/postprocessing/retail_rate_module/inputs/Electric%20O%20&%20M%20Expenses-IOU-1993-2019.csv)
---

  - [Electric Operating Revenues-IOU-1993-2019.csv](/postprocessing/retail_rate_module/inputs/Electric%20Operating%20Revenues-IOU-1993-2019.csv)
---

  - [Electric Plant in Service-IOU-1993-2019.csv](/postprocessing/retail_rate_module/inputs/Electric%20Plant%20in%20Service-IOU-1993-2019.csv)
---

  - [f861_cust_counts.csv](/postprocessing/retail_rate_module/inputs/f861_cust_counts.csv)
---

  - [overwrite-utility-energy_sales.csv](/postprocessing/retail_rate_module/inputs/overwrite-utility-energy_sales.csv)
---

  - [state-meanbiaserror_rate-aggregation.csv](/postprocessing/retail_rate_module/inputs/state-meanbiaserror_rate-aggregation.csv)
---

  - [Table_9.8_Average_Retail_Prices_of_Electricity.xlsx](/postprocessing/retail_rate_module/inputs/Table_9.8_Average_Retail_Prices_of_Electricity.xlsx)
---


#### [tableau](postprocessing/tableau) <a name='postprocessing/tableau'></a>
  - [tables_to_aggregate.csv](/postprocessing/tableau/tables_to_aggregate.csv)
---


### [preprocessing](preprocessing) <a name='preprocessing'></a>

#### [atb_updates_processing](preprocessing/atb_updates_processing) <a name='preprocessing/atb_updates_processing'></a>

##### [input_files](preprocessing/atb_updates_processing/input_files) <a name='preprocessing/atb_updates_processing/input_files'></a>
  - [batt_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/batt_plant_char_format.csv)
---

  - [conv_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/conv_plant_char_format.csv)
---

  - [csp_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/csp_plant_char_format.csv)
---

  - [geo_fom_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/geo_fom_plant_char_format.csv)
---

  - [h2-ct_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/h2-ct_plant_char_format.csv)
---

  - [ofs-wind_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ofs-wind_plant_char_format.csv)
---

  - [ofs-wind_rsc_mult_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ofs-wind_rsc_mult_plant_char_format.csv)
---

  - [ons-wind_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ons-wind_plant_char_format.csv)
---

  - [upv_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/upv_plant_char_format.csv)
---


### [ReEDS_Augur](ReEDS_Augur) <a name='ReEDS_Augur'></a>
  - [augur_switches.csv](/ReEDS_Augur/augur_switches.csv)
---

