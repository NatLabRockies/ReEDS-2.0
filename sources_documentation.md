## Table of Contents


  - [hourlize](#hourlize)
    - [eer_to_reeds](#hourlize-eer-to-reeds)
      - [eer_load_participation_factors](#hourlize-eer-to-reeds-eer-load-participation-factors)
      - [eer_splice](#hourlize-eer-to-reeds-eer-splice)
    - [inputs](#hourlize-inputs)
      - [load](#hourlize-inputs-load)
      - [resource](#hourlize-inputs-resource)
    - [plexos_to_reeds](#hourlize-plexos-to-reeds)
      - [inputs](#hourlize-plexos-to-reeds-inputs)
    - [tests](#hourlize-tests)
      - [data](#hourlize-tests-data)
        - [r2r_expanded](#hourlize-tests-data-r2r-expanded)
        - [r2r_from_config](#hourlize-tests-data-r2r-from-config)
        - [r2r_integration](#hourlize-tests-data-r2r-integration)
        - [r2r_integration_geothermal](#hourlize-tests-data-r2r-integration-geothermal)
  - [inputs](#inputs)
    - [canada_imports](#inputs-canada-imports)
    - [capacity_exogenous](#inputs-capacity-exogenous)
    - [climate](#inputs-climate)
      - [GFDL-ESM2M_RCP4p5_WM](#inputs-climate-gfdl-esm2m-rcp4p5-wm)
      - [HadGEM2-ES_RCP2p6](#inputs-climate-hadgem2-es-rcp2p6)
      - [HadGEM2-ES_rcp45_AT](#inputs-climate-hadgem2-es-rcp45-at)
      - [HadGEM2-ES_RCP4p5](#inputs-climate-hadgem2-es-rcp4p5)
      - [HadGEM2-ES_rcp85_AT](#inputs-climate-hadgem2-es-rcp85-at)
      - [HadGEM2-ES_RCP8p5](#inputs-climate-hadgem2-es-rcp8p5)
      - [IPSL-CM5A-LR_RCP8p5_WM](#inputs-climate-ipsl-cm5a-lr-rcp8p5-wm)
    - [consume](#inputs-consume)
    - [ctus](#inputs-ctus)
    - [degradation](#inputs-degradation)
    - [demand_response](#inputs-demand-response)
    - [dgen_model_inputs](#inputs-dgen-model-inputs)
      - [stscen2023_electrification](#inputs-dgen-model-inputs-stscen2023-electrification)
      - [stscen2023_highng](#inputs-dgen-model-inputs-stscen2023-highng)
      - [stscen2023_highre](#inputs-dgen-model-inputs-stscen2023-highre)
      - [stscen2023_lowng](#inputs-dgen-model-inputs-stscen2023-lowng)
      - [stscen2023_lowre](#inputs-dgen-model-inputs-stscen2023-lowre)
      - [stscen2023_mid_case](#inputs-dgen-model-inputs-stscen2023-mid-case)
      - [stscen2023_mid_case_95_by_2035](#inputs-dgen-model-inputs-stscen2023-mid-case-95-by-2035)
      - [stscen2023_mid_case_95_by_2050](#inputs-dgen-model-inputs-stscen2023-mid-case-95-by-2050)
      - [stscen2023_taxcredit_extended2050](#inputs-dgen-model-inputs-stscen2023-taxcredit-extended2050)
    - [disaggregation](#inputs-disaggregation)
    - [emission_constraints](#inputs-emission-constraints)
    - [financials](#inputs-financials)
    - [fuelprices](#inputs-fuelprices)
    - [geothermal](#inputs-geothermal)
    - [growth_constraints](#inputs-growth-constraints)
    - [hydro](#inputs-hydro)
    - [load](#inputs-load)
    - [national_generation](#inputs-national-generation)
    - [plant_characteristics](#inputs-plant-characteristics)
    - [reserves](#inputs-reserves)
    - [sets](#inputs-sets)
    - [shapefiles](#inputs-shapefiles)
      - [WKT_csvs](#inputs-shapefiles-wkt-csvs)
    - [state_policies](#inputs-state-policies)
    - [storage](#inputs-storage)
    - [supply_curve](#inputs-supply-curve)
    - [techs](#inputs-techs)
    - [transmission](#inputs-transmission)
    - [upgrades](#inputs-upgrades)
    - [userinput](#inputs-userinput)
    - [valuestreams](#inputs-valuestreams)
    - [variability](#inputs-variability)
      - [multi_year](#inputs-variability-multi-year)
    - [waterclimate](#inputs-waterclimate)
  - [postprocessing](#postprocessing)
    - [air_quality](#postprocessing-air-quality)
      - [rcm_data](#postprocessing-air-quality-rcm-data)
    - [bokehpivot](#postprocessing-bokehpivot)
      - [in](#postprocessing-bokehpivot-in)
        - [reeds2](#postprocessing-bokehpivot-in-reeds2)
      - [out](#postprocessing-bokehpivot-out)
        - [report-2025-03-21-13-05-27](#postprocessing-bokehpivot-out-report-2025-03-21-13-05-27)
        - [report-2025-06-03-11-55-40](#postprocessing-bokehpivot-out-report-2025-06-03-11-55-40)
        - [report-2025-06-03-11-59-51](#postprocessing-bokehpivot-out-report-2025-06-03-11-59-51)
        - [report-2025-06-03-12-06-11](#postprocessing-bokehpivot-out-report-2025-06-03-12-06-11)
        - [report-2025-06-03-12-06-21](#postprocessing-bokehpivot-out-report-2025-06-03-12-06-21)
        - [report-2025-06-05-12-38-18](#postprocessing-bokehpivot-out-report-2025-06-05-12-38-18)
        - [view](#postprocessing-bokehpivot-out-view)
    - [combine_runs](#postprocessing-combine-runs)
    - [land_use](#postprocessing-land-use)
      - [inputs](#postprocessing-land-use-inputs)
    - [plots](#postprocessing-plots)
    - [retail_rate_module](#postprocessing-retail-rate-module)
      - [inputs](#postprocessing-retail-rate-module-inputs)
    - [reValue](#postprocessing-revalue)
    - [tableau](#postprocessing-tableau)
  - [preprocessing](#preprocessing)
    - [atb_updates_processing](#preprocessing-atb-updates-processing)
      - [input_files](#preprocessing-atb-updates-processing-input-files)
  - [reeds2pras](#reeds2pras)
    - [test](#reeds2pras-test)
      - [reeds_cases](#reeds2pras-test-reeds-cases)
        - [Pacific](#reeds2pras-test-reeds-cases-pacific)
        - [USA_VSC_2035](#reeds2pras-test-reeds-cases-usa-vsc-2035)
  - [ReEDS_Augur](#reeds-augur)
  - [tests](#tests)
    - [data](#tests-data)
      - [county](#tests-data-county)


## Input Files
- [cases.csv](/cases.csv)
  - **File Type:** Switches file
  - **Description:** Contains the configuration settings for the ReEDS run(s).
  - **Dollar year:** 2004
  - **Citation:** [https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/38e6610a8c6a92291804598c95c11b707bf187b9/cases.csv](https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/38e6610a8c6a92291804598c95c11b707bf187b9/cases.csv)
---

- [cases_examples.csv](/cases_examples.csv)
---

- [cases_small.csv](/cases_small.csv)
  - **Description:** Contains settings to run ReEDS at a smaller scale to test operability of the ReEDS model. Turns off several technologies and reduces the model size to significantly improve solve times.
---

- [cases_standardscenarios.csv](/cases_standardscenarios.csv)
  - **File Type:** StdScen Cases file
  - **Description:** Contains the configuration settings for the Standard Scenarios ReEDS runs.
---

- [cases_test.csv](/cases_test.csv)
  - **Description:** Contains the configuration settings for doing test runs including the default Pacific census division test case.
---

- [e_report_params.csv](/e_report_params.csv)
  - **Description:** Contains a parameter list used in the model along with descriptions of what they are and units used.
---

- [runfiles.csv](/runfiles.csv)
  - **Description:** Contains the locations of input data that is copied from the repository into the runs folder for each respective case.
---

- [sources.csv](/sources.csv)
  - **Description:** CSV file containing a list of all input files (csv, h5, csv.gz)
---


<a id='hourlize'></a>
### hourlize


<a id='hourlize-eer-to-reeds'></a>
#### hourlize/eer_to_reeds


<a id='hourlize-eer-to-reeds-eer-load-participation-factors'></a>
##### hourlize/eer_to_reeds/eer_load_participation_factors

  - [ba_state_map.csv](/hourlize/eer_to_reeds/eer_load_participation_factors/ba_state_map.csv)
---


<a id='hourlize-eer-to-reeds-eer-splice'></a>
##### hourlize/eer_to_reeds/eer_splice

  - [ba_timezone.csv](/hourlize/eer_to_reeds/eer_splice/ba_timezone.csv)
---

  - [load_factors.csv](/hourlize/eer_to_reeds/eer_splice/load_factors.csv)
---


<a id='hourlize-inputs'></a>
#### hourlize/inputs


<a id='hourlize-inputs-load'></a>
##### hourlize/inputs/load

  - [ba_timezone.csv](/hourlize/inputs/load/ba_timezone.csv)
    - **Description:** Contains timezone information for BAs with respect to GMT.
    - **Indices:** r
---

  - [EIA_2010loadbystate.csv](/hourlize/inputs/load/EIA_2010loadbystate.csv)
    - **Description:** Contains 2010 EIA load information (GWh) with respect to each state in the US.
    - **Indices:** r
---

  - [EIA_loadbystate.csv](/hourlize/inputs/load/EIA_loadbystate.csv)
    - **Description:** Contains historical (2010-2022) EIA load information (GWh) with respect to each state in the US.
    - **Indices:** t,r
---

  - [load_participation_factors_st_to_ba.csv](/hourlize/inputs/load/load_participation_factors_st_to_ba.csv)
    - **Description:** Contains load participation factors for each of the BAs
    - **Indices:** r
---


<a id='hourlize-inputs-resource'></a>
##### hourlize/inputs/resource

  - [egs_resource_classes.csv](/hourlize/inputs/resource/egs_resource_classes.csv)
---

  - [fair_market_value.csv](/hourlize/inputs/resource/fair_market_value.csv)
    - **Description:** Contains estimates of fair market land value in $ per hectare for each reV supply curve site
    - **Citation:** Provided by Anthony Lopez in June 2023
---

  - [geohydro_resource_classes.csv](/hourlize/inputs/resource/geohydro_resource_classes.csv)
---

  - [rev_sc_columns.csv](/hourlize/inputs/resource/rev_sc_columns.csv)
---

  - [state_abbrev.csv](/hourlize/inputs/resource/state_abbrev.csv)
    - **Description:** Contains state names and codesfor the US.
---

  - [upv_resource_classes.csv](/hourlize/inputs/resource/upv_resource_classes.csv)
    - **Description:** Contains information related to UPV class segregation based on mean irradiance levels.
---

  - [wind-ofs_resource_classes.csv](/hourlize/inputs/resource/wind-ofs_resource_classes.csv)
    - **File Type:** supply curve input
    - **Description:** Contains information related to Offshore wind class segregation and turbine type (fixed vs floating) based on water depth and site lcoe
    - **Indices:** n/a
---

  - [wind-ons_resource_classes.csv](/hourlize/inputs/resource/wind-ons_resource_classes.csv)
    - **Description:** Contains information related to Onshore wind class segregation based on mean wind speeds.
---


<a id='hourlize-plexos-to-reeds'></a>
#### hourlize/plexos_to_reeds


<a id='hourlize-plexos-to-reeds-inputs'></a>
##### hourlize/plexos_to_reeds/inputs

  - [month_to_season.csv](/hourlize/plexos_to_reeds/inputs/month_to_season.csv)
    - **Description:** Maps the season to month in a year
---

  - [plexos_node_monthly_lpf_ercot.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_monthly_lpf_ercot.csv)
---

  - [plexos_node_seasonal_lpf_wi.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_seasonal_lpf_wi.csv)
---

  - [plexos_node_to_reeds_ba.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_to_reeds_ba.csv)
---

  - [plexos_node_to_zone_ei.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_to_zone_ei.csv)
---


<a id='hourlize-tests'></a>
#### hourlize/tests


<a id='hourlize-tests-data'></a>
##### hourlize/tests/data


<a id='hourlize-tests-data-r2r-expanded'></a>
###### hourlize/tests/data/r2r_expanded


<a id='hourlize-tests-data-r2r-expanded-upv-case-1'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_1


<a id='hourlize-tests-data-r2r-expanded-upv-case-1-expected-results'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_1/expected_results

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/expected_results/df_sc_out_upv_reduced.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-1-reeds'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_1/reeds


<a id='hourlize-tests-data-r2r-expanded-upv-case-1-reeds-inputs-case'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case

  - [hierarchy_original.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/switches.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-1-reeds-outputs'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs

  - [cap.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/systemcost.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-1-supply-curves'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_1/supply_curves

  - [upv_supply_curve_raw_unpacked.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/supply_curves/upv_supply_curve_raw_unpacked.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-2'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_2


<a id='hourlize-tests-data-r2r-expanded-upv-case-2-expected-results'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_2/expected_results

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/expected_results/df_sc_out_upv_reduced.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-2-reeds'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_2/reeds


<a id='hourlize-tests-data-r2r-expanded-upv-case-2-reeds-inputs-case'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case

  - [hierarchy_original.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/switches.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-2-reeds-outputs'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs

  - [cap.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/systemcost.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-2-supply-curves'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_2/supply_curves

  - [upv_supply_curve_raw_unpacked.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/supply_curves/upv_supply_curve_raw_unpacked.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-3'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_3


<a id='hourlize-tests-data-r2r-expanded-upv-case-3-expected-results'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_3/expected_results

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/expected_results/df_sc_out_upv_reduced.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-3-reeds'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_3/reeds


<a id='hourlize-tests-data-r2r-expanded-upv-case-3-reeds-inputs-case'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case

  - [hierarchy_original.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/switches.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-3-reeds-outputs'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs

  - [cap.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/systemcost.csv)
---


<a id='hourlize-tests-data-r2r-expanded-upv-case-3-supply-curves'></a>
###### hourlize/tests/data/r2r_expanded/upv_case_3/supply_curves

  - [upv_supply_curve_raw_unpacked.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/supply_curves/upv_supply_curve_raw_unpacked.csv)
---


<a id='hourlize-tests-data-r2r-expanded-wind-ons-case-1'></a>
###### hourlize/tests/data/r2r_expanded/wind-ons_case_1


<a id='hourlize-tests-data-r2r-expanded-wind-ons-case-1-expected-results'></a>
###### hourlize/tests/data/r2r_expanded/wind-ons_case_1/expected_results

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/expected_results/df_sc_out_wind-ons_reduced.csv)
---


<a id='hourlize-tests-data-r2r-expanded-wind-ons-case-1-reeds'></a>
###### hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds


<a id='hourlize-tests-data-r2r-expanded-wind-ons-case-1-reeds-inputs-case'></a>
###### hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case

  - [hierarchy_original.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/switches.csv)
---


<a id='hourlize-tests-data-r2r-expanded-wind-ons-case-1-reeds-inputs-case-supplycurve-metadata'></a>
###### hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/supplycurve_metadata

  - [rev_supply_curves.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/supplycurve_metadata/rev_supply_curves.csv)
---


<a id='hourlize-tests-data-r2r-expanded-wind-ons-case-1-reeds-outputs'></a>
###### hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs

  - [cap.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/systemcost.csv)
---


<a id='hourlize-tests-data-r2r-expanded-wind-ons-case-1-supply-curves'></a>
###### hourlize/tests/data/r2r_expanded/wind-ons_case_1/supply_curves

  - [wind-ons_supply_curve_raw.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/supply_curves/wind-ons_supply_curve_raw.csv)
---


<a id='hourlize-tests-data-r2r-from-config'></a>
###### hourlize/tests/data/r2r_from_config


<a id='hourlize-tests-data-r2r-from-config-expected-results'></a>
###### hourlize/tests/data/r2r_from_config/expected_results


<a id='hourlize-tests-data-r2r-from-config-expected-results-multiple-priority-inputs'></a>
###### hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_wind-ons_reduced.csv)
---


<a id='hourlize-tests-data-r2r-from-config-expected-results-no-bin-constraint'></a>
###### hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_wind-ons_reduced.csv)
---


<a id='hourlize-tests-data-r2r-from-config-expected-results-priority-inputs'></a>
###### hourlize/tests/data/r2r_from_config/expected_results/priority_inputs

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_wind-ons_reduced.csv)
---


<a id='hourlize-tests-data-r2r-integration'></a>
###### hourlize/tests/data/r2r_integration


<a id='hourlize-tests-data-r2r-integration-expected-results'></a>
###### hourlize/tests/data/r2r_integration/expected_results

  - [df_sc_out_upv.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_upv.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_upv_reduced_simul_fill.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_upv_reduced_simul_fill.csv)
---

  - [df_sc_out_wind-ofs.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ofs.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ons.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ons_reduced.csv)
---


<a id='hourlize-tests-data-r2r-integration-reeds'></a>
###### hourlize/tests/data/r2r_integration/reeds


<a id='hourlize-tests-data-r2r-integration-reeds-inputs-case'></a>
###### hourlize/tests/data/r2r_integration/reeds/inputs_case

  - [hierarchy_original.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/switches.csv)
---


<a id='hourlize-tests-data-r2r-integration-reeds-outputs'></a>
###### hourlize/tests/data/r2r_integration/reeds/outputs

  - [cap.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/systemcost.csv)
---


<a id='hourlize-tests-data-r2r-integration-supply-curves'></a>
###### hourlize/tests/data/r2r_integration/supply_curves


<a id='hourlize-tests-data-r2r-integration-supply-curves-upv-reference'></a>
###### hourlize/tests/data/r2r_integration/supply_curves/upv_reference


<a id='hourlize-tests-data-r2r-integration-supply-curves-upv-reference-results'></a>
###### hourlize/tests/data/r2r_integration/supply_curves/upv_reference/results

  - [upv_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/upv_reference/results/upv_supply_curve_raw.csv)
---


<a id='hourlize-tests-data-r2r-integration-supply-curves-wind-ofs-0-open-moderate'></a>
###### hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate


<a id='hourlize-tests-data-r2r-integration-supply-curves-wind-ofs-0-open-moderate-results'></a>
###### hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results

  - [wind-ofs_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results/wind-ofs_supply_curve_raw.csv)
---


<a id='hourlize-tests-data-r2r-integration-supply-curves-wind-ons-reference'></a>
###### hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference


<a id='hourlize-tests-data-r2r-integration-supply-curves-wind-ons-reference-results'></a>
###### hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference/results

  - [wind-ons_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference/results/wind-ons_supply_curve_raw.csv)
---


<a id='hourlize-tests-data-r2r-integration-geothermal'></a>
###### hourlize/tests/data/r2r_integration_geothermal


<a id='hourlize-tests-data-r2r-integration-geothermal-expected-results'></a>
###### hourlize/tests/data/r2r_integration_geothermal/expected_results

  - [df_sc_out_egs_allkm.csv](/hourlize/tests/data/r2r_integration_geothermal/expected_results/df_sc_out_egs_allkm.csv)
---

  - [df_sc_out_egs_allkm_reduced.csv](/hourlize/tests/data/r2r_integration_geothermal/expected_results/df_sc_out_egs_allkm_reduced.csv)
---

  - [df_sc_out_geohydro_allkm.csv](/hourlize/tests/data/r2r_integration_geothermal/expected_results/df_sc_out_geohydro_allkm.csv)
---

  - [df_sc_out_geohydro_allkm_reduced.csv](/hourlize/tests/data/r2r_integration_geothermal/expected_results/df_sc_out_geohydro_allkm_reduced.csv)
---


<a id='hourlize-tests-data-r2r-integration-geothermal-reeds'></a>
###### hourlize/tests/data/r2r_integration_geothermal/reeds


<a id='hourlize-tests-data-r2r-integration-geothermal-reeds-inputs-case'></a>
###### hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case

  - [hierarchy_original.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/switches.csv)
---


<a id='hourlize-tests-data-r2r-integration-geothermal-reeds-outputs'></a>
###### hourlize/tests/data/r2r_integration_geothermal/reeds/outputs

  - [cap.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/systemcost.csv)
---


<a id='hourlize-tests-data-r2r-integration-geothermal-supply-curves'></a>
###### hourlize/tests/data/r2r_integration_geothermal/supply_curves

  - [egs_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration_geothermal/supply_curves/egs_supply_curve_raw.csv)
---

  - [geohydro_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration_geothermal/supply_curves/geohydro_supply_curve_raw.csv)
---


<a id='inputs'></a>
### inputs

  - [county2zone.csv](/inputs/county2zone.csv)
---

  - [hierarchy.csv](/inputs/hierarchy.csv)
---

  - [hierarchy_agg125.csv](/inputs/hierarchy_agg125.csv)
---

  - [hierarchy_agg54.csv](/inputs/hierarchy_agg54.csv)
---

  - [hierarchy_agg69.csv](/inputs/hierarchy_agg69.csv)
---

  - [modeledyears.csv](/inputs/modeledyears.csv)
---

  - [scalars.csv](/inputs/scalars.csv)
---

  - [tech-subset-table.csv](/inputs/tech-subset-table.csv)
    - **Description:** Maps all technologies to specific subsets of technologies
---


<a id='inputs-canada-imports'></a>
#### inputs/canada_imports

  - [can_exports.csv](/inputs/canada_imports/can_exports.csv)
    - **File Type:** Input
    - **Description:** Annual exports to Canada by BA
    - **Indices:** r,t
    - **Units:** MWh

---

  - [can_exports_szn_frac.csv](/inputs/canada_imports/can_exports_szn_frac.csv)
    - **File Type:** Input
    - **Description:** Fraction of annual exports to Canada by season
    - **Indices:** N/A
    - **Units:** rate (unitless)

---

  - [can_imports.csv](/inputs/canada_imports/can_imports.csv)
    - **File Type:** Input
    - **Description:** Annual imports from Canada by BA
    - **Indices:** r,t
    - **Units:** MWh

---

  - [can_imports_quarter_frac.csv](/inputs/canada_imports/can_imports_quarter_frac.csv)
    - **File Type:** Input
    - **Description:** Fraction of annual imports from Canada by season
    - **Indices:** N/A
    - **Units:** rate (unitless)

---


<a id='inputs-capacity-exogenous'></a>
#### inputs/capacity_exogenous

  - [cappayments.csv](/inputs/capacity_exogenous/cappayments.csv)
---

  - [cappayments_ba.csv](/inputs/capacity_exogenous/cappayments_ba.csv)
---

  - [demonstration_plants.csv](/inputs/capacity_exogenous/demonstration_plants.csv)
    - **File Type:** Prescribed capacity
    - **Description:** Nuclear-smr demonstration plants; active when GSw_NuclearDemo=1
    - **Indices:** t,r,i,coolingwatertech,ctt,wst,value
    - **Citation:** See 'notes' column in the file and https://www.energy.gov/oced/advanced-reactor-demonstration-projects-0
    - **Units:** MW

---

  - [exog_cap_geohydro_allkm_reference.csv](/inputs/capacity_exogenous/exog_cap_geohydro_allkm_reference.csv)
---

  - [exog_cap_geohydro_reference.csv](/inputs/capacity_exogenous/exog_cap_geohydro_reference.csv)
---

  - [exog_cap_upv_limited.csv](/inputs/capacity_exogenous/exog_cap_upv_limited.csv)
---

  - [exog_cap_upv_open.csv](/inputs/capacity_exogenous/exog_cap_upv_open.csv)
---

  - [exog_cap_upv_reference.csv](/inputs/capacity_exogenous/exog_cap_upv_reference.csv)
---

  - [exog_cap_wind-ons_limited.csv](/inputs/capacity_exogenous/exog_cap_wind-ons_limited.csv)
---

  - [exog_cap_wind-ons_open.csv](/inputs/capacity_exogenous/exog_cap_wind-ons_open.csv)
---

  - [exog_cap_wind-ons_reference.csv](/inputs/capacity_exogenous/exog_cap_wind-ons_reference.csv)
---

  - [interconnection_queues.csv](/inputs/capacity_exogenous/interconnection_queues.csv)
---

  - [prescribed_builds_geohydro_allkm_reference.csv](/inputs/capacity_exogenous/prescribed_builds_geohydro_allkm_reference.csv)
---

  - [prescribed_builds_geohydro_reference_ba.csv](/inputs/capacity_exogenous/prescribed_builds_geohydro_reference_ba.csv)
---

  - [prescribed_builds_geohydro_reference_county.csv](/inputs/capacity_exogenous/prescribed_builds_geohydro_reference_county.csv)
---

  - [prescribed_builds_upv_limited_ba.csv](/inputs/capacity_exogenous/prescribed_builds_upv_limited_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with limited siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_upv_limited_county.csv](/inputs/capacity_exogenous/prescribed_builds_upv_limited_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with limited siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_upv_open_ba.csv](/inputs/capacity_exogenous/prescribed_builds_upv_open_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with open siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_upv_open_county.csv](/inputs/capacity_exogenous/prescribed_builds_upv_open_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with open siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_upv_reference_ba.csv](/inputs/capacity_exogenous/prescribed_builds_upv_reference_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with reference siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_upv_reference_county.csv](/inputs/capacity_exogenous/prescribed_builds_upv_reference_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with reference siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ofs_limited_ba.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ofs_limited_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ofs prescribed builds with limited siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ofs_limited_county.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ofs_limited_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ofs prescribed builds with limited siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ofs_open_ba.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ofs_open_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ofs prescribed builds with open siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ofs_open_county.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ofs_open_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ofs prescribed builds with open siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ofs_reference_ba.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ofs_reference_ba.csv)
---

  - [prescribed_builds_wind-ofs_reference_county.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ofs_reference_county.csv)
---

  - [prescribed_builds_wind-ons_limited_ba.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ons_limited_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with limited siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ons_limited_county.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ons_limited_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with limited siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ons_open_ba.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ons_open_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with open siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ons_open_county.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ons_open_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with open siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ons_reference_ba.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ons_reference_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with reference siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [prescribed_builds_wind-ons_reference_county.csv](/inputs/capacity_exogenous/prescribed_builds_wind-ons_reference_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with reference siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [ReEDS_generator_database_final_EIA-NEMS.csv](/inputs/capacity_exogenous/ReEDS_generator_database_final_EIA-NEMS.csv)
    - **File Type:** Input
    - **Description:** EIA-NEMS database of existing generators
---


<a id='inputs-climate'></a>
#### inputs/climate

  - [climate_heuristics_finalyear.csv](/inputs/climate/climate_heuristics_finalyear.csv)
---

  - [climate_heuristics_yearfrac.csv](/inputs/climate/climate_heuristics_yearfrac.csv)
---

  - [CoolSlopes.csv](/inputs/climate/CoolSlopes.csv)
---

  - [HeatSlopes.csv](/inputs/climate/HeatSlopes.csv)
---


<a id='inputs-climate-gfdl-esm2m-rcp4p5-wm'></a>
##### inputs/climate/GFDL-ESM2M_RCP4p5_WM

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


<a id='inputs-climate-hadgem2-es-rcp2p6'></a>
##### inputs/climate/HadGEM2-ES_RCP2p6

  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP2p6/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterSeaAnnDistr.csv)
---


<a id='inputs-climate-hadgem2-es-rcp45-at'></a>
##### inputs/climate/HadGEM2-ES_rcp45_AT

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


<a id='inputs-climate-hadgem2-es-rcp4p5'></a>
##### inputs/climate/HadGEM2-ES_RCP4p5

  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP4p5/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterSeaAnnDistr.csv)
---


<a id='inputs-climate-hadgem2-es-rcp85-at'></a>
##### inputs/climate/HadGEM2-ES_rcp85_AT

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


<a id='inputs-climate-hadgem2-es-rcp8p5'></a>
##### inputs/climate/HadGEM2-ES_RCP8p5

  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP8p5/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterSeaAnnDistr.csv)
---


<a id='inputs-climate-ipsl-cm5a-lr-rcp8p5-wm'></a>
##### inputs/climate/IPSL-CM5A-LR_RCP8p5_WM

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


<a id='inputs-consume'></a>
#### inputs/consume

  - [consume_char_low.csv](/inputs/consume/consume_char_low.csv)
    - **File Type:** Inputs
    - **Description:** Cost (capex, FOM, VOM) and efficiency (gas and electrical) as well as storage and transmission adder (stortran_adder) inputs for various H2 producing technologies, under Conservative assumptions.
    - **Indices:** i,t
    - **Dollar year:** Units vary based on the parameter - see commented text in b_inputs.gms.
    - **Citation:** N/A
---

  - [consume_char_ref.csv](/inputs/consume/consume_char_ref.csv)
    - **File Type:** Inputs
    - **Description:** Cost (capex, FOM, VOM) and efficiency (gas and electrical) as well as storage and transmission adder (stortran_adder) inputs for various H2 producing technologies, under Reference assumptions.
    - **Indices:** i,t
    - **Dollar year:** Units vary based on the parameter - see commented text in b_inputs.gms.
    - **Citation:** N/A
---

  - [dac_elec_BVRE_2021_high.csv](/inputs/consume/dac_elec_BVRE_2021_high.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using High assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear
    - **Citation:** [https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a](https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a)
---

  - [dac_elec_BVRE_2021_low.csv](/inputs/consume/dac_elec_BVRE_2021_low.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using Low assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear
    - **Citation:** [https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a](https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a)
---

  - [dac_elec_BVRE_2021_mid.csv](/inputs/consume/dac_elec_BVRE_2021_mid.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using Mid assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear
    - **Citation:** [https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a](https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a)
---

  - [dac_gas_BVRE_2021_high.csv](/inputs/consume/dac_gas_BVRE_2021_high.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using High assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear
    - **Citation:** [https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987](https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987)
---

  - [dac_gas_BVRE_2021_low.csv](/inputs/consume/dac_gas_BVRE_2021_low.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using Low assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear
    - **Citation:** [https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987](https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987)
---

  - [dac_gas_BVRE_2021_mid.csv](/inputs/consume/dac_gas_BVRE_2021_mid.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using Mid assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear
    - **Citation:** [https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987](https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987)
---

  - [dollaryear.csv](/inputs/consume/dollaryear.csv)
    - **File Type:** Inputs
    - **Description:** Dollar year for various Beyond VRE scenarios. 
    - **Indices:** N/A
    - **Dollar year:** Stated in document.
    - **Citation:** N/A
---

  - [h2_demand_county_share.csv](/inputs/consume/h2_demand_county_share.csv)
    - **File Type:** Inputs
    - **Description:** The fraction of national hydrogen demand in that year that corresponds to each county. Demand estimates come from https://data.openei.org/submissions/5655. 2021 demand shares correspond to the "Reference" scenario with light-duty vehicles / biofuels / methanol demand removed and 2050 shares correspond to the "Low Cost Electrolysis" scenario.
    - **Indices:** r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [h2_exogenous_demand.csv](/inputs/consume/h2_exogenous_demand.csv)
    - **File Type:** Inputs
    - **Description:** Exogenous hydrogen demand by industries other than the power sector per year
    - **Indices:** t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [h2_storage_ba.csv](/inputs/consume/h2_storage_ba.csv)
    - **File Type:** Inputs
    - **Description:** Cheapest H2 storage type that exists in each ReEDS BA. Storage locations come from https://www.sciencedirect.com/science/article/pii/S0360319914021223.
    - **Indices:** r
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [h2_storage_county.csv](/inputs/consume/h2_storage_county.csv)
    - **File Type:** Inputs
    - **Description:** Cheapest H2 storage type that exists in each county. Storage locations come from https://www.sciencedirect.com/science/article/pii/S0360319914021223.
    - **Indices:** r
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [h2_transport_and_storage_costs.csv](/inputs/consume/h2_transport_and_storage_costs.csv)
    - **File Type:** Inputs
    - **Description:** Transport and storage costs of hydrogen per year
    - **Indices:** t
    - **Dollar year:** 2004
    - **Citation:** N/A
---


<a id='inputs-ctus'></a>
#### inputs/ctus

  - [co2_site_char.csv](/inputs/ctus/co2_site_char.csv)
    - **Dollar year:** 2018
---

  - [cs.csv](/inputs/ctus/cs.csv)
---


<a id='inputs-degradation'></a>
#### inputs/degradation

  - [degradation_annual_default.csv](/inputs/degradation/degradation_annual_default.csv)
---


<a id='inputs-demand-response'></a>
#### inputs/demand_response

  - [ev_load_Baseline.h5](/inputs/demand_response/ev_load_Baseline.h5)
    - **File Type:** inputs
    - **Description:** Baseline electricity load from EV charging by timeslice h and year t
    - **Units:** MW

---

  - [evmc_rsc_Baseline.csv](/inputs/demand_response/evmc_rsc_Baseline.csv)
---

  - [evmc_shape_decrease_profile_Baseline.h5](/inputs/demand_response/evmc_shape_decrease_profile_Baseline.h5)
---

  - [evmc_shape_increase_profile_Baseline.h5](/inputs/demand_response/evmc_shape_increase_profile_Baseline.h5)
---

  - [evmc_storage_decrease_profile_Baseline.h5](/inputs/demand_response/evmc_storage_decrease_profile_Baseline.h5)
---

  - [evmc_storage_energy_Baseline.h5](/inputs/demand_response/evmc_storage_energy_Baseline.h5)
---

  - [evmc_storage_increase_profile_Baseline.h5](/inputs/demand_response/evmc_storage_increase_profile_Baseline.h5)
---


<a id='inputs-dgen-model-inputs'></a>
#### inputs/dgen_model_inputs


<a id='inputs-dgen-model-inputs-stscen2023-electrification'></a>
##### inputs/dgen_model_inputs/stscen2023_electrification

  - [distpvcap_stscen2023_electrification.csv](/inputs/dgen_model_inputs/stscen2023_electrification/distpvcap_stscen2023_electrification.csv)
---


<a id='inputs-dgen-model-inputs-stscen2023-highng'></a>
##### inputs/dgen_model_inputs/stscen2023_highng

  - [distpvcap_stscen2023_highng.csv](/inputs/dgen_model_inputs/stscen2023_highng/distpvcap_stscen2023_highng.csv)
    - **File Type:** distribution PV inputs 
    - **Description:** Setting for distpv scenario capacity - from standard scenarios 2023 with high NG (including distpv) costs
---


<a id='inputs-dgen-model-inputs-stscen2023-highre'></a>
##### inputs/dgen_model_inputs/stscen2023_highre

  - [distpvcap_stscen2023_highre.csv](/inputs/dgen_model_inputs/stscen2023_highre/distpvcap_stscen2023_highre.csv)
    - **File Type:** distribution PV inputs 
    - **Description:** Setting for distpv scenario capacity - from standard scenarios 2023 with high RE (including distpv) costs
---


<a id='inputs-dgen-model-inputs-stscen2023-lowng'></a>
##### inputs/dgen_model_inputs/stscen2023_lowng

  - [distpvcap_stscen2023_lowng.csv](/inputs/dgen_model_inputs/stscen2023_lowng/distpvcap_stscen2023_lowng.csv)
    - **File Type:** distribution PV inputs 
    - **Description:** Setting for distpv scenario capacity - from standard scenarios 2023 with low NG (including distpv) costs
---


<a id='inputs-dgen-model-inputs-stscen2023-lowre'></a>
##### inputs/dgen_model_inputs/stscen2023_lowre

  - [distpvcap_stscen2023_lowre.csv](/inputs/dgen_model_inputs/stscen2023_lowre/distpvcap_stscen2023_lowre.csv)
    - **File Type:** distribution PV inputs 
    - **Description:** Setting for distpv scenario capacity - from standard scenarios 2023 with low RE (including distpv) costs
---


<a id='inputs-dgen-model-inputs-stscen2023-mid-case'></a>
##### inputs/dgen_model_inputs/stscen2023_mid_case

  - [distpvcap_stscen2023_mid_case.csv](/inputs/dgen_model_inputs/stscen2023_mid_case/distpvcap_stscen2023_mid_case.csv)
    - **File Type:** distribution PV inputs 
---


<a id='inputs-dgen-model-inputs-stscen2023-mid-case-95-by-2035'></a>
##### inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2035

  - [distpvcap_stscen2023_mid_case_95_by_2035.csv](/inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2035/distpvcap_stscen2023_mid_case_95_by_2035.csv)
    - **File Type:** distribution PV inputs 
---


<a id='inputs-dgen-model-inputs-stscen2023-mid-case-95-by-2050'></a>
##### inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2050

  - [distpvcap_stscen2023_mid_case_95_by_2050.csv](/inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2050/distpvcap_stscen2023_mid_case_95_by_2050.csv)
    - **File Type:** distribution PV inputs 
---


<a id='inputs-dgen-model-inputs-stscen2023-taxcredit-extended2050'></a>
##### inputs/dgen_model_inputs/stscen2023_taxcredit_extended2050

  - [distpvcap_stscen2023_taxcredit_extended2050.csv](/inputs/dgen_model_inputs/stscen2023_taxcredit_extended2050/distpvcap_stscen2023_taxcredit_extended2050.csv)
    - **File Type:** distribution PV inputs 
---


<a id='inputs-disaggregation'></a>
#### inputs/disaggregation

  - [county_population.csv](/inputs/disaggregation/county_population.csv)
    - **Description:** The population of each county, relative values are used as multipliers for downselecting data. Data come from the U.S. Census Bureau 2021 county population estimates (https://www.census.gov/data/tables/time-series/demo/popest/2020s-counties-total.html).
    - **Indices:** FIPS
---

  - [disagg_hydroexist.csv](/inputs/disaggregation/disagg_hydroexist.csv)
    - **Description:** The hydropower capacity fraction of each county within a given ReEDS BA, used as multipliers for downselecting data
    - **Indices:** r
---


<a id='inputs-emission-constraints'></a>
#### inputs/emission_constraints

  - [ccs_link.csv](/inputs/emission_constraints/ccs_link.csv)
---

  - [ccs_link_water.csv](/inputs/emission_constraints/ccs_link_water.csv)
---

  - [co2_cap.csv](/inputs/emission_constraints/co2_cap.csv)
    - **Description:** Annual nationwide carbon cap
---

  - [co2_tax.csv](/inputs/emission_constraints/co2_tax.csv)
    - **Description:** Annual co2 tax
---

  - [county_co2_share_egrid_2022.csv](/inputs/emission_constraints/county_co2_share_egrid_2022.csv)
---

  - [csapr_group1_ex.csv](/inputs/emission_constraints/csapr_group1_ex.csv)
---

  - [csapr_group2_ex.csv](/inputs/emission_constraints/csapr_group2_ex.csv)
---

  - [csapr_ozone_season.csv](/inputs/emission_constraints/csapr_ozone_season.csv)
---

  - [emitrate.csv](/inputs/emission_constraints/emitrate.csv)
    - **Description:** Emition rates for thermal generator for SO2, NOx, and CO2
    - **Indices:** i,e
---

  - [gwp.csv](/inputs/emission_constraints/gwp.csv)
---

  - [methane_leakage_rate.csv](/inputs/emission_constraints/methane_leakage_rate.csv)
---

  - [ng_crf_penalty.csv](/inputs/emission_constraints/ng_crf_penalty.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment for NG techs in scenarios with national decarbonization targets
    - **Indices:** allt
    - **Dollar year:** N/A
    - **Citation:** [https://github.nrel.gov/ReEDS/ReEDS-2.0/pull/1220](https://github.nrel.gov/ReEDS/ReEDS-2.0/pull/1220)
    - **Units:** rate (unitless)

---

  - [rggi_states.csv](/inputs/emission_constraints/rggi_states.csv)
    - **Description:** Participating RGGI states
    - **Citation:** [https://www.rggi.org/program-overview-and-design/elements](https://www.rggi.org/program-overview-and-design/elements)
---

  - [rggicon.csv](/inputs/emission_constraints/rggicon.csv)
    - **Description:** CO2 caps for RGGI states in metric tons
    - **Citation:** [https://www.rggi.org/allowance-tracking/allowance-distribution](https://www.rggi.org/allowance-tracking/allowance-distribution)
---

  - [state_cap.csv](/inputs/emission_constraints/state_cap.csv)
---


<a id='inputs-financials'></a>
#### inputs/financials

  - [cap_penalty.csv](/inputs/financials/cap_penalty.csv)
---

  - [construction_schedules_default.csv](/inputs/financials/construction_schedules_default.csv)
---

  - [construction_times_default.csv](/inputs/financials/construction_times_default.csv)
---

  - [currency_incentives.csv](/inputs/financials/currency_incentives.csv)
---

  - [deflator.csv](/inputs/financials/deflator.csv)
    - **Description:** Dollar year deflator to convert values to 2004$
---

  - [depreciation_schedules_default.csv](/inputs/financials/depreciation_schedules_default.csv)
---

  - [energy_communities.csv](/inputs/financials/energy_communities.csv)
---

  - [financials_hydrogen.csv](/inputs/financials/financials_hydrogen.csv)
---

  - [financials_sys_ATB2023.csv](/inputs/financials/financials_sys_ATB2023.csv)
---

  - [financials_sys_ATB2024.csv](/inputs/financials/financials_sys_ATB2024.csv)
---

  - [financials_tech_ATB2023.csv](/inputs/financials/financials_tech_ATB2023.csv)
---

  - [financials_tech_ATB2023_CRP20.csv](/inputs/financials/financials_tech_ATB2023_CRP20.csv)
---

  - [financials_tech_ATB2024.csv](/inputs/financials/financials_tech_ATB2024.csv)
---

  - [financials_transmission_30ITC_0pen_2022_2031.csv](/inputs/financials/financials_transmission_30ITC_0pen_2022_2031.csv)
---

  - [financials_transmission_default.csv](/inputs/financials/financials_transmission_default.csv)
---

  - [incentives_annual.csv](/inputs/financials/incentives_annual.csv)
---

  - [incentives_biennial.csv](/inputs/financials/incentives_biennial.csv)
---

  - [incentives_ira.csv](/inputs/financials/incentives_ira.csv)
---

  - [incentives_ira_45q_45v_extension.csv](/inputs/financials/incentives_ira_45q_45v_extension.csv)
---

  - [incentives_noira.csv](/inputs/financials/incentives_noira.csv)
---

  - [incentives_none.csv](/inputs/financials/incentives_none.csv)
---

  - [incentives_obbba.csv](/inputs/financials/incentives_obbba.csv)
---

  - [incentives_obbba_conservative.csv](/inputs/financials/incentives_obbba_conservative.csv)
---

  - [inflation_default.csv](/inputs/financials/inflation_default.csv)
    - **Description:** Annual inflation factors from 1914 through 2200; historical values use the avg-avg values from https://www.usinflationcalculator.com/inflation/consumer-price-index-and-annual-percent-changes-from-1913-to-2008/
    - **Indices:** t
---

  - [nuclear_energy_communities.csv](/inputs/financials/nuclear_energy_communities.csv)
    - **File Type:**  LLNL
    - **Description:** Counties belonging to metropolitan statistical areas (MSAs) for which at least 0.17 percent of direct employment has been related to nuclear power at any point since 2010. These are determined partly by following the process described in Section 2.6 of https://home.treasury.gov/system/files/8861/EnergyCommunities_Data_Documentation.pdf and substituing in the NAICS code for nuclear electric power generation (221113) and partly by determining counties that belong to MSAs where the number of people employed by national labs engaged in nuclear research and development (PNNL
    - **Indices:**  INL
    - **Dollar year:**  ORNL
    - **Citation:**  SNL
    - **Units:**  Argonne

---

  - [reg_cap_cost_diff_default.csv](/inputs/financials/reg_cap_cost_diff_default.csv)
    - **File Type:** parameter
    - **Description:** region-specific differences for capital cost of all resources. Add to 1 to produce a multiplier
    - **Indices:** i,r
---

  - [retire_penalty.csv](/inputs/financials/retire_penalty.csv)
---

  - [supply_chain_adjust.csv](/inputs/financials/supply_chain_adjust.csv)
---

  - [tc_phaseout_schedule_ira2022.csv](/inputs/financials/tc_phaseout_schedule_ira2022.csv)
---


<a id='inputs-fuelprices'></a>
#### inputs/fuelprices

  - [alpha_AEO_2023_HOG.csv](/inputs/fuelprices/alpha_AEO_2023_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas Resource and Technology scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004
    - **Citation:** AEO 2023
---

  - [alpha_AEO_2023_LOG.csv](/inputs/fuelprices/alpha_AEO_2023_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas Resource and Technology scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004
    - **Citation:** AEO 2023
---

  - [alpha_AEO_2023_reference.csv](/inputs/fuelprices/alpha_AEO_2023_reference.csv)
    - **File Type:** Input
    - **Description:** reference census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004
    - **Citation:** AEO 2023
---

  - [alpha_AEO_2025_HOG.csv](/inputs/fuelprices/alpha_AEO_2025_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas Resource and Technology scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004
    - **Citation:** AEO 2025
---

  - [alpha_AEO_2025_LOG.csv](/inputs/fuelprices/alpha_AEO_2025_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas Resource and Technology scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004
    - **Citation:** AEO 2025
---

  - [alpha_AEO_2025_reference.csv](/inputs/fuelprices/alpha_AEO_2025_reference.csv)
    - **File Type:** Input
    - **Description:** reference census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004
    - **Citation:** AEO 2025
---

  - [cd_beta0.csv](/inputs/fuelprices/cd_beta0.csv)
    - **File Type:** Input
    - **Description:** reference census division beta levels electric sector
    - **Indices:** cendiv
    - **Dollar year:** 2004
---

  - [cd_beta0_allsector.csv](/inputs/fuelprices/cd_beta0_allsector.csv)
    - **File Type:** Input
    - **Description:** reference census division beta levels all sectors
    - **Indices:** cendiv
    - **Dollar year:** 2004
---

  - [cendivweights.csv](/inputs/fuelprices/cendivweights.csv)
    - **Description:** weights to smooth gas prices between census regions to avoid abrupt price changes at the cendiv borders
    - **Indices:** r,cendiv
---

  - [coal_AEO_2023_reference.csv](/inputs/fuelprices/coal_AEO_2023_reference.csv)
    - **Description:** reference case census division fuel price of coal
    - **Indices:** t,cendiv
    - **Dollar year:** 2022
---

  - [coal_AEO_2025_reference.csv](/inputs/fuelprices/coal_AEO_2025_reference.csv)
    - **Description:** reference case census division fuel price of coal with missing values forward-filled from earlier years
    - **Indices:** t,cendiv
    - **Dollar year:** 2024
---

  - [dollaryear.csv](/inputs/fuelprices/dollaryear.csv)
    - **Description:** Dollar year mapping for each fuel price scenario
---

  - [h2-combustion_10.csv](/inputs/fuelprices/h2-combustion_10.csv)
    - **Description:** price of hydrogen for combustion technologies (h2-ct and cc) at $10/MMBtu for all years
---

  - [h2-combustion_30.csv](/inputs/fuelprices/h2-combustion_30.csv)
    - **Description:** price of hydrogen for combustion technologies (h2-ct and cc) at $30/MMBtu for all years
---

  - [h2-combustion_reference.csv](/inputs/fuelprices/h2-combustion_reference.csv)
    - **Description:** price of hydrogen for combustion technologies (h2-ct and cc) at $20/MMBtu for all years
---

  - [ng_AEO_2023_HOG.csv](/inputs/fuelprices/ng_AEO_2023_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas Resource and Technology scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2023_LOG.csv](/inputs/fuelprices/ng_AEO_2023_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas Resource and Technology scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2023_reference.csv](/inputs/fuelprices/ng_AEO_2023_reference.csv)
    - **File Type:** Input
    - **Description:** Reference scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2025_HOG.csv](/inputs/fuelprices/ng_AEO_2025_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas Resource and Technology scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2025_LOG.csv](/inputs/fuelprices/ng_AEO_2025_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas Resource and Technology scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2025_reference.csv](/inputs/fuelprices/ng_AEO_2025_reference.csv)
    - **File Type:** Input
    - **Description:** Reference scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** 2004$/MMBtu

---

  - [ng_demand_AEO_2023_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2023_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas Resource and Technology census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_demand_AEO_2023_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2023_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas Resource and Technology census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_demand_AEO_2023_reference.csv](/inputs/fuelprices/ng_demand_AEO_2023_reference.csv)
    - **File Type:** Input
    - **Description:** Reference census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_demand_AEO_2025_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2025_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas Resource and Technology census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_demand_AEO_2025_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2025_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas Resource and Technology census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_demand_AEO_2025_reference.csv](/inputs/fuelprices/ng_demand_AEO_2025_reference.csv)
    - **File Type:** Input
    - **Description:** Reference census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2023_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas Resource and Technology census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2023_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas Resource and Technology census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2023_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_reference.csv)
    - **File Type:** Input
    - **Description:** Reference census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2023: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2025_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2025_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas Resource and Technology census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2025_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2025_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas Resource and Technology census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2025_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2025_reference.csv)
    - **File Type:** Input
    - **Description:** Reference census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t
    - **Citation:** AEO2025: https://www.eia.gov/outlooks/aeo/
    - **Units:** Quads

---

  - [uranium_AEO_2023_reference.csv](/inputs/fuelprices/uranium_AEO_2023_reference.csv)
---

  - [uranium_AEO_2025_reference.csv](/inputs/fuelprices/uranium_AEO_2025_reference.csv)
---


<a id='inputs-geothermal'></a>
#### inputs/geothermal

  - [geo_discovery_BAU.csv](/inputs/geothermal/geo_discovery_BAU.csv)
---

  - [geo_discovery_factor_ATB_2023.csv](/inputs/geothermal/geo_discovery_factor_ATB_2023.csv)
---

  - [geo_discovery_factor_reV.csv](/inputs/geothermal/geo_discovery_factor_reV.csv)
---

  - [geo_discovery_TI.csv](/inputs/geothermal/geo_discovery_TI.csv)
---

  - [geo_rsc_ATB_2023.csv](/inputs/geothermal/geo_rsc_ATB_2023.csv)
---


<a id='inputs-growth-constraints'></a>
#### inputs/growth_constraints

  - [gbin_min.csv](/inputs/growth_constraints/gbin_min.csv)
---

  - [growth_bin_size_mult.csv](/inputs/growth_constraints/growth_bin_size_mult.csv)
---

  - [growth_limit_absolute.csv](/inputs/growth_constraints/growth_limit_absolute.csv)
    - **Description:** Maximum expected annual builds for wind, batteries, and UPV from 2024-2026 using observed record builds.
    - **Units:** MW/year

---

  - [growth_penalty.csv](/inputs/growth_constraints/growth_penalty.csv)
---


<a id='inputs-hydro'></a>
#### inputs/hydro

  - [hyd_fom.csv](/inputs/hydro/hyd_fom.csv)
    - **Description:** Regional FOM costs for hydro
---

  - [hydcf_ba.h5](/inputs/hydro/hydcf_ba.h5)
---

  - [hydcf_county.h5](/inputs/hydro/hydcf_county.h5)
---

  - [hydro_mingen.csv](/inputs/hydro/hydro_mingen.csv)
---

  - [SeaCapAdj_hy.csv](/inputs/hydro/SeaCapAdj_hy.csv)
---


<a id='inputs-load'></a>
#### inputs/load

  - [Adoption_Trajectories_Commercial.csv](/inputs/load/Adoption_Trajectories_Commercial.csv)
---

  - [Adoption_Trajectories_Residential.csv](/inputs/load/Adoption_Trajectories_Residential.csv)
---

  - [Baseline_load_hourly.h5](/inputs/load/Baseline_load_hourly.h5)
---

  - [cangrowth.csv](/inputs/load/cangrowth.csv)
    - **Description:** Canada load growth multiplier
---

  - [Clean2035_load_hourly.h5](/inputs/load/Clean2035_load_hourly.h5)
---

  - [Clean2035_LTS_load_hourly.h5](/inputs/load/Clean2035_LTS_load_hourly.h5)
---

  - [Clean2035clip1pct_load_hourly.h5](/inputs/load/Clean2035clip1pct_load_hourly.h5)
---

  - [Commercial_GHP_Delta.csv](/inputs/load/Commercial_GHP_Delta.csv)
---

  - [demand_AEO_2023_high.csv](/inputs/load/demand_AEO_2023_high.csv)
---

  - [demand_AEO_2023_low.csv](/inputs/load/demand_AEO_2023_low.csv)
---

  - [demand_AEO_2023_reference.csv](/inputs/load/demand_AEO_2023_reference.csv)
---

  - [EER_100by2050_load_hourly.h5](/inputs/load/EER_100by2050_load_hourly.h5)
---

  - [EER_Baseline_AEO2022_load_hourly.h5](/inputs/load/EER_Baseline_AEO2022_load_hourly.h5)
---

  - [EER_IRAlow_load_hourly.h5](/inputs/load/EER_IRAlow_load_hourly.h5)
---

  - [EER_IRAmoderate_load_hourly.h5](/inputs/load/EER_IRAmoderate_load_hourly.h5)
---

  - [EPHIGH_load_hourly.h5](/inputs/load/EPHIGH_load_hourly.h5)
---

  - [EPMEDIUM_load_hourly.h5](/inputs/load/EPMEDIUM_load_hourly.h5)
---

  - [EPMEDIUMStretch2040_load_hourly.h5](/inputs/load/EPMEDIUMStretch2040_load_hourly.h5)
---

  - [EPMEDIUMStretch2046_load_hourly.h5](/inputs/load/EPMEDIUMStretch2046_load_hourly.h5)
---

  - [EPREFERENCE_load_hourly.h5](/inputs/load/EPREFERENCE_load_hourly.h5)
---

  - [historic_load_hourly.h5](/inputs/load/historic_load_hourly.h5)
---

  - [mex_growth_rate.csv](/inputs/load/mex_growth_rate.csv)
    - **Description:** Mexico load growth multiplier
---

  - [Residential_GHP_Delta.csv](/inputs/load/Residential_GHP_Delta.csv)
---


<a id='inputs-national-generation'></a>
#### inputs/national_generation

  - [gen_mandate_tech_list.csv](/inputs/national_generation/gen_mandate_tech_list.csv)
---

  - [gen_mandate_trajectory.csv](/inputs/national_generation/gen_mandate_trajectory.csv)
---

  - [national_rps_frac_allScen.csv](/inputs/national_generation/national_rps_frac_allScen.csv)
---


<a id='inputs-plant-characteristics'></a>
#### inputs/plant_characteristics

  - [battery_ATB_2024_advanced.csv](/inputs/plant_characteristics/battery_ATB_2024_advanced.csv)
    - **Dollar year:** 2021
---

  - [battery_ATB_2024_conservative.csv](/inputs/plant_characteristics/battery_ATB_2024_conservative.csv)
    - **Dollar year:** 2021
---

  - [battery_ATB_2024_moderate.csv](/inputs/plant_characteristics/battery_ATB_2024_moderate.csv)
    - **Dollar year:** 2021
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

  - [biopower_ATB_2024_moderate.csv](/inputs/plant_characteristics/biopower_ATB_2024_moderate.csv)
---

  - [caes_reference.csv](/inputs/plant_characteristics/caes_reference.csv)
    - **Description:** CAES costs for the reference cost scenario
---

  - [ccsflex_ATB_2020_cost.csv](/inputs/plant_characteristics/ccsflex_ATB_2020_cost.csv)
---

  - [ccsflex_ATB_2020_perf.csv](/inputs/plant_characteristics/ccsflex_ATB_2020_perf.csv)
---

  - [coal-ccs_ATB_2024_advanced.csv](/inputs/plant_characteristics/coal-ccs_ATB_2024_advanced.csv)
---

  - [coal-ccs_ATB_2024_conservative.csv](/inputs/plant_characteristics/coal-ccs_ATB_2024_conservative.csv)
---

  - [coal-ccs_ATB_2024_moderate.csv](/inputs/plant_characteristics/coal-ccs_ATB_2024_moderate.csv)
---

  - [coal_ATB_2024_moderate.csv](/inputs/plant_characteristics/coal_ATB_2024_moderate.csv)
---

  - [cost_opres_default.csv](/inputs/plant_characteristics/cost_opres_default.csv)
---

  - [cost_opres_market.csv](/inputs/plant_characteristics/cost_opres_market.csv)
---

  - [csp_ATB_2023_advanced.csv](/inputs/plant_characteristics/csp_ATB_2023_advanced.csv)
---

  - [csp_ATB_2023_conservative.csv](/inputs/plant_characteristics/csp_ATB_2023_conservative.csv)
---

  - [csp_ATB_2023_moderate.csv](/inputs/plant_characteristics/csp_ATB_2023_moderate.csv)
---

  - [csp_ATB_2024_advanced.csv](/inputs/plant_characteristics/csp_ATB_2024_advanced.csv)
---

  - [csp_ATB_2024_conservative.csv](/inputs/plant_characteristics/csp_ATB_2024_conservative.csv)
---

  - [csp_ATB_2024_moderate.csv](/inputs/plant_characteristics/csp_ATB_2024_moderate.csv)
---

  - [csp_SunShot2030.csv](/inputs/plant_characteristics/csp_SunShot2030.csv)
    - **Description:** Csp costs from the SunShot2030 cost scenario
---

  - [dollaryear.csv](/inputs/plant_characteristics/dollaryear.csv)
    - **Description:** Dollar year mapping for each plant cost scenario
---

  - [evmc_shape_Baseline.csv](/inputs/plant_characteristics/evmc_shape_Baseline.csv)
---

  - [evmc_storage_Baseline.csv](/inputs/plant_characteristics/evmc_storage_Baseline.csv)
---

  - [gas-ccs_ATB_2024_advanced.csv](/inputs/plant_characteristics/gas-ccs_ATB_2024_advanced.csv)
---

  - [gas-ccs_ATB_2024_conservative.csv](/inputs/plant_characteristics/gas-ccs_ATB_2024_conservative.csv)
---

  - [gas-ccs_ATB_2024_moderate.csv](/inputs/plant_characteristics/gas-ccs_ATB_2024_moderate.csv)
---

  - [gas_ATB_2024_moderate.csv](/inputs/plant_characteristics/gas_ATB_2024_moderate.csv)
---

  - [geo_ATB_2023_advanced.csv](/inputs/plant_characteristics/geo_ATB_2023_advanced.csv)
---

  - [geo_ATB_2023_conservative.csv](/inputs/plant_characteristics/geo_ATB_2023_conservative.csv)
---

  - [geo_ATB_2023_moderate.csv](/inputs/plant_characteristics/geo_ATB_2023_moderate.csv)
---

  - [geo_ATB_2024_advanced.csv](/inputs/plant_characteristics/geo_ATB_2024_advanced.csv)
---

  - [geo_ATB_2024_conservative.csv](/inputs/plant_characteristics/geo_ATB_2024_conservative.csv)
---

  - [geo_ATB_2024_moderate.csv](/inputs/plant_characteristics/geo_ATB_2024_moderate.csv)
---

  - [h2-combustion_ATB_2024.csv](/inputs/plant_characteristics/h2-combustion_ATB_2024.csv)
    - **Description:** Hydrogen CT and CC plant costs generated in preprocessing from moderate case NLR ATB 2024 data
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

  - [ice_fom.csv](/inputs/plant_characteristics/ice_fom.csv)
    - **Description:** Fixed O&M for ice storage
---

  - [maxage.csv](/inputs/plant_characteristics/maxage.csv)
    - **Description:** Maximum age allowed for each technology
---

  - [maxdailycf.csv](/inputs/plant_characteristics/maxdailycf.csv)
    - **Description:** maximum daily capacity factor--dr_shed input supply curves are based on one 4-hour event per day
---

  - [min_retire_age.csv](/inputs/plant_characteristics/min_retire_age.csv)
    - **Description:** Minimum retirement age for given technology
---

  - [minCF.csv](/inputs/plant_characteristics/minCF.csv)
    - **Description:** minimum annual capacity factor for each tech fleet - applied to i-rto
---

  - [mingen_fixed.csv](/inputs/plant_characteristics/mingen_fixed.csv)
---

  - [minloadfrac0.csv](/inputs/plant_characteristics/minloadfrac0.csv)
    - **Description:** characteristics/minloadfrac0 database of minloadbed generator cs
---

  - [nuclear-smr_ATB_2024_advanced.csv](/inputs/plant_characteristics/nuclear-smr_ATB_2024_advanced.csv)
---

  - [nuclear-smr_ATB_2024_conservative.csv](/inputs/plant_characteristics/nuclear-smr_ATB_2024_conservative.csv)
---

  - [nuclear-smr_ATB_2024_moderate.csv](/inputs/plant_characteristics/nuclear-smr_ATB_2024_moderate.csv)
---

  - [nuclear_ATB_2024_advanced.csv](/inputs/plant_characteristics/nuclear_ATB_2024_advanced.csv)
---

  - [nuclear_ATB_2024_conservative.csv](/inputs/plant_characteristics/nuclear_ATB_2024_conservative.csv)
---

  - [nuclear_ATB_2024_moderate.csv](/inputs/plant_characteristics/nuclear_ATB_2024_moderate.csv)
---

  - [ofs-wind_ATB_2023_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 advanced ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2023_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 conservative ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2023_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 moderate ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2023_moderate_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_moderate_noFloating.csv)
---

  - [ofs-wind_ATB_2024_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2024_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 advanced ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2022
---

  - [ofs-wind_ATB_2024_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2024_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 conservative ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2022
---

  - [ofs-wind_ATB_2024_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2024_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 moderate ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2022
---

  - [ofs-wind_ATB_2024_moderate_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2024_moderate_noFloating.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 moderate_noFloating ofs-wind capital (5x floating capital cost), fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year
    - **Dollar year:** 2022
---

  - [ons-wind_ATB_2023_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_advanced.csv)
---

  - [ons-wind_ATB_2023_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_conservative.csv)
---

  - [ons-wind_ATB_2023_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_moderate.csv)
---

  - [ons-wind_ATB_2024_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2024_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** Advanced cost and performance inputs from the 2024 Annual Technology Baseline for land-based wind
    - **Dollar year:** 2022
---

  - [ons-wind_ATB_2024_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2024_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** Conservative cost and performance inputs from the 2024 Annual Technology Baseline for land-based wind
    - **Dollar year:** 2022
---

  - [ons-wind_ATB_2024_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2024_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** Moderate cost and performance inputs from the 2024 Annual Technology Baseline for land-based wind
    - **Dollar year:** 2022
---

  - [other_plantchar.csv](/inputs/plant_characteristics/other_plantchar.csv)
---

  - [outage_forced_static.csv](/inputs/plant_characteristics/outage_forced_static.csv)
    - **File Type:** Inputs file
    - **Description:** Forced outage rates by technology
---

  - [outage_forced_temperature_murphy2019.csv](/inputs/plant_characteristics/outage_forced_temperature_murphy2019.csv)
---

  - [outage_scheduled_monthly.csv](/inputs/plant_characteristics/outage_scheduled_monthly.csv)
---

  - [outage_scheduled_static.csv](/inputs/plant_characteristics/outage_scheduled_static.csv)
    - **Description:** Scheduled outage rate by technology
---

  - [pvb_benchmark2020.csv](/inputs/plant_characteristics/pvb_benchmark2020.csv)
---

  - [ramprate.csv](/inputs/plant_characteristics/ramprate.csv)
    - **Description:** Generator ramp rates by technology
---

  - [startcost.csv](/inputs/plant_characteristics/startcost.csv)
---

  - [unitsize.csv](/inputs/plant_characteristics/unitsize.csv)
---

  - [upv_ATB_2023_advanced.csv](/inputs/plant_characteristics/upv_ATB_2023_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 advanced UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2023_conservative.csv](/inputs/plant_characteristics/upv_ATB_2023_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 conservative UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2023_moderate.csv](/inputs/plant_characteristics/upv_ATB_2023_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 moderate UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2024_advanced.csv](/inputs/plant_characteristics/upv_ATB_2024_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 advanced UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2024_conservative.csv](/inputs/plant_characteristics/upv_ATB_2024_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 conservative UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2024_moderate.csv](/inputs/plant_characteristics/upv_ATB_2024_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 moderate UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [years_until_endogenous.csv](/inputs/plant_characteristics/years_until_endogenous.csv)
---


<a id='inputs-reserves'></a>
#### inputs/reserves

  - [opres_periods.csv](/inputs/reserves/opres_periods.csv)
---

  - [orperc.csv](/inputs/reserves/orperc.csv)
---

  - [peak_net_imports.csv](/inputs/reserves/peak_net_imports.csv)
---

  - [prm_annual.csv](/inputs/reserves/prm_annual.csv)
    - **Description:** Annual planning reserve margin by NERC region
---

  - [ramptime.csv](/inputs/reserves/ramptime.csv)
---


<a id='inputs-sets'></a>
#### inputs/sets

  - [aclike.csv](/inputs/sets/aclike.csv)
    - **File Type:** GAMS set
    - **Description:** set of AC transmission capacity types
---

  - [allt.csv](/inputs/sets/allt.csv)
    - **File Type:** GAMS set
    - **Description:** set of all potential years
---

  - [bioclass.csv](/inputs/sets/bioclass.csv)
    - **File Type:** GAMS set
    - **Description:** set of bio tech classes
---

  - [ccseason.csv](/inputs/sets/ccseason.csv)
    - **File Type:** GAMS set
---

  - [ccsflex_cat.csv](/inputs/sets/ccsflex_cat.csv)
    - **File Type:** GAMS set
    - **Description:** set of flexible ccs performance parameter categories
---

  - [climate_param.csv](/inputs/sets/climate_param.csv)
    - **File Type:** GAMS set
    - **Description:** set of parameters defined in climate_heuristics_finalyear
---

  - [consumecat.csv](/inputs/sets/consumecat.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories for consuming facility characteristics
---

  - [csapr_cat.csv](/inputs/sets/csapr_cat.csv)
    - **File Type:** GAMS set
    - **Description:** set of CSAPR regulation categories
---

  - [csapr_group.csv](/inputs/sets/csapr_group.csv)
    - **File Type:** GAMS set
    - **Description:** set of CSAPR trading groups
---

  - [ctt.csv](/inputs/sets/ctt.csv)
    - **File Type:** GAMS set
    - **Description:** set of cooling technology types
---

  - [e.csv](/inputs/sets/e.csv)
    - **File Type:** GAMS set
    - **Description:** set of emission categories used in model
---

  - [eall.csv](/inputs/sets/eall.csv)
    - **File Type:** GAMS set
    - **Description:** set of emission categories used in reporting
---

  - [etype.csv](/inputs/sets/etype.csv)
---

  - [f.csv](/inputs/sets/f.csv)
    - **File Type:** GAMS set
    - **Description:** set of fuel types
---

  - [flex_type.csv](/inputs/sets/flex_type.csv)
    - **File Type:** GAMS set
    - **Description:** set of demand flexibility types
---

  - [fuel2tech.csv](/inputs/sets/fuel2tech.csv)
    - **File Type:** GAMS set
    - **Description:** mapping between fuel types and generations
---

  - [fuelbin.csv](/inputs/sets/fuelbin.csv)
    - **File Type:** GAMS set
    - **Description:** set of gas usage brackets
---

  - [gb.csv](/inputs/sets/gb.csv)
    - **File Type:** GAMS set
    - **Description:** set of gas price bins
---

  - [gbin.csv](/inputs/sets/gbin.csv)
    - **File Type:** GAMS set
    - **Description:** set of growth bins
---

  - [geotech.csv](/inputs/sets/geotech.csv)
    - **File Type:** GAMS set
    - **Description:** set of geothermal technology categories
---

  - [h2_st.csv](/inputs/sets/h2_st.csv)
    - **File Type:** GAMS set
    - **Description:** defines investments needed to store and transport H2
---

  - [h2_stor.csv](/inputs/sets/h2_stor.csv)
    - **File Type:** GAMS set
    - **Description:** set of H2 storage options
---

  - [hintage_char.csv](/inputs/sets/hintage_char.csv)
    - **File Type:** GAMS set
    - **Description:** set of characteristics available in hintage_data
---

  - [i.csv](/inputs/sets/i.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies
---

  - [i_geotech.csv](/inputs/sets/i_geotech.csv)
    - **File Type:** GAMS set
    - **Description:** crosswalk between an individual geothermal technology and its category
---

  - [i_h2_ptc_gen.csv](/inputs/sets/i_h2_ptc_gen.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies which can produce energy for electrolyzers claiming the hydrogen production tax credit due to their low lifecycle carbon emissions
---

  - [i_p.csv](/inputs/sets/i_p.csv)
    - **File Type:** GAMS set
    - **Description:** mapping from technologies to the products they produce
---

  - [i_subtech.csv](/inputs/sets/i_subtech.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories for subtechs
---

  - [i_water_nocooling.csv](/inputs/sets/i_water_nocooling.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies that use water, but are not differentiated by cooling tech and water source
---

  - [lcclike.csv](/inputs/sets/lcclike.csv)
    - **File Type:** GAMS set
    - **Description:** set of transmission capacity types where lines are bundled with AC/DC converters
---

  - [month.csv](/inputs/sets/month.csv)
    - **File Type:** GAMS set
---

  - [noretire.csv](/inputs/sets/noretire.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies that will never be retired
---

  - [notvsc.csv](/inputs/sets/notvsc.csv)
    - **File Type:** GAMS set
    - **Description:** set of transmission capacity types that are not VSC
---

  - [ofstype.csv](/inputs/sets/ofstype.csv)
    - **File Type:** GAMS set
    - **Description:** set of offshore types used in offshore requirement constraint (eq_RPS_OFSWind)
---

  - [ofstype_i.csv](/inputs/sets/ofstype_i.csv)
    - **File Type:** GAMS set
    - **Description:** crosswalk between ofstype and i
---

  - [orcat.csv](/inputs/sets/orcat.csv)
    - **File Type:** GAMS set
    - **Description:** set of operating reserve categories
---

  - [ortype.csv](/inputs/sets/ortype.csv)
    - **File Type:** GAMS set
    - **Description:** set of types of operating reserve constraints
---

  - [p.csv](/inputs/sets/p.csv)
    - **File Type:** GAMS set
    - **Description:** set of products produced
---

  - [pcat.csv](/inputs/sets/pcat.csv)
    - **File Type:** GAMS set
    - **Description:** set of prescribed technology categories
---

  - [plantcat.csv](/inputs/sets/plantcat.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories for plant characteristics
---

  - [prepost.csv](/inputs/sets/prepost.csv)
    - **File Type:** GAMS set
---

  - [prescriptivelink0.csv](/inputs/sets/prescriptivelink0.csv)
    - **File Type:** GAMS set
    - **Description:** initial set of prescribed categories and their technologies - used in assigning prescribed builds
---

  - [pvb_agg.csv](/inputs/sets/pvb_agg.csv)
    - **File Type:** GAMS set
    - **Description:** crosswalk between hybrid pv+battery configurations and technology options
---

  - [pvb_config.csv](/inputs/sets/pvb_config.csv)
    - **File Type:** GAMS set
    - **Description:** set of hybrid pv+battery configurations
---

  - [quarter.csv](/inputs/sets/quarter.csv)
    - **File Type:** GAMS set
---

  - [resourceclass.csv](/inputs/sets/resourceclass.csv)
    - **File Type:** GAMS set
    - **Description:** set of renewable resource classes
---

  - [RPSCat.csv](/inputs/sets/RPSCat.csv)
    - **File Type:** GAMS set
    - **Description:** set of RPS constraint categories, including clean energy standards
---

  - [sc_cat.csv](/inputs/sets/sc_cat.csv)
    - **File Type:** GAMS set
    - **Description:** set of supply curve categories (capacity and cost)
---

  - [sdbin.csv](/inputs/sets/sdbin.csv)
    - **File Type:** GAMS set
    - **Description:** set of storage durage bins
---

  - [sw.csv](/inputs/sets/sw.csv)
    - **File Type:** GAMS set
    - **Description:** set of surface water types where access is based on consumption not withdrawal
---

  - [tg.csv](/inputs/sets/tg.csv)
    - **File Type:** GAMS set
    - **Description:** set of technology groups
---

  - [tg_rsc_cspagg.csv](/inputs/sets/tg_rsc_cspagg.csv)
    - **File Type:** GAMS set
    - **Description:** set of csp technologies that belong to the same class
---

  - [tg_rsc_upvagg.csv](/inputs/sets/tg_rsc_upvagg.csv)
    - **File Type:** GAMS set
    - **Description:** set of pv and pvb technologies that belong to the same class
---

  - [trancap_fut_cat.csv](/inputs/sets/trancap_fut_cat.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories of near-term transmission projects that describe the likelihood of being completed
---

  - [trtype.csv](/inputs/sets/trtype.csv)
    - **File Type:** GAMS set
    - **Description:** set of transmission capacity types
---

  - [unitspec_upgrades.csv](/inputs/sets/unitspec_upgrades.csv)
    - **File Type:** GAMS set
    - **Description:** set of upgraded technologies that get unit-specific characteristics
---

  - [upgrade_hintage_char.csv](/inputs/sets/upgrade_hintage_char.csv)
    - **File Type:** GAMS set
    - **Description:** set to operate over in extension of hintage_data characteristics when sw_upgrades = 1
---

  - [w.csv](/inputs/sets/w.csv)
    - **File Type:** GAMS set
    - **Description:** set of water withdrawal or consumption options for water techs
---

  - [wst.csv](/inputs/sets/wst.csv)
    - **File Type:** GAMS set
    - **Description:** set of water source types
---

  - [wst_climate.csv](/inputs/sets/wst_climate.csv)
    - **File Type:** GAMS set
    - **Description:** set of water sources affected by climate change
---

  - [yearafter.csv](/inputs/sets/yearafter.csv)
    - **File Type:** GAMS set
    - **Description:** set to loop over for the final year calculation
---


<a id='inputs-shapefiles'></a>
#### inputs/shapefiles

  - [ctus_cs_polygons_BVRE.csv](/inputs/shapefiles/ctus_cs_polygons_BVRE.csv)
---

  - [ctus_r_cs_spurlines_200mi.csv](/inputs/shapefiles/ctus_r_cs_spurlines_200mi.csv)
---

  - [r_rr_lines_to_25_nearest_neighbors.csv](/inputs/shapefiles/r_rr_lines_to_25_nearest_neighbors.csv)
---

  - [state_fips_codes.csv](/inputs/shapefiles/state_fips_codes.csv)
    - **Description:** Mapping of states to FIPS codes and postcal code abbreviations
---

  - [US_CAN_MEX_PCA_polygons.csv](/inputs/shapefiles/US_CAN_MEX_PCA_polygons.csv)
---

  - [US_transmission_endpoints_and_CAN_MEX_centroids.csv](/inputs/shapefiles/US_transmission_endpoints_and_CAN_MEX_centroids.csv)
---


<a id='inputs-shapefiles-wkt-csvs'></a>
##### inputs/shapefiles/WKT_csvs

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


<a id='inputs-state-policies'></a>
#### inputs/state_policies

  - [acp_disallowed.csv](/inputs/state_policies/acp_disallowed.csv)
    - **Description:** List of states which do not allow alternative compliance payments in place of meeting RPS or CES requirements 
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
    - **File Type:** Inputs
    - **Description:** Cost adjustment for NG techs in states where all NG techs must be retired by a certain year
    - **Indices:** allt,st
    - **Dollar year:** N/A
    - **Citation:** [https://github.nrel.gov/ReEDS/ReEDS-2.0/pull/1220](https://github.nrel.gov/ReEDS/ReEDS-2.0/pull/1220)
    - **Units:** rate (unitless)

---

  - [nuclear_subsidies.csv](/inputs/state_policies/nuclear_subsidies.csv)
---

  - [offshore_req_default.csv](/inputs/state_policies/offshore_req_default.csv)
    - **File Type:** Inputs
    - **Description:** default state mandates of offshore wind capacity
    - **Indices:** st,allt
---

  - [oosfrac.csv](/inputs/state_policies/oosfrac.csv)
    - **Description:** Defines the fraction of renewable and clean energy credits can be purchased from out of state (oos). Applied for RPS and CES
---

  - [recstyle.csv](/inputs/state_policies/recstyle.csv)
    - **Description:** Indication for how to apply state requirement (0 = end-use sales, 1 = bus-bar sales, 2 = generation). Default is 0.
---

  - [rectable.csv](/inputs/state_policies/rectable.csv)
    - **Description:** Table defining which states are allowed to trade RECs
---

  - [rps_fraction.csv](/inputs/state_policies/rps_fraction.csv)
    - **Description:** Indicates what fraction of sales or generation (based on recstyle.csv) must be from renewable energy 
---

  - [storage_mandates.csv](/inputs/state_policies/storage_mandates.csv)
    - **Description:** Energy storage mandates by region
---

  - [techs_banned_ces.csv](/inputs/state_policies/techs_banned_ces.csv)
    - **Description:** Indicates which technolgies are not eligible to contribute to CES 
---

  - [techs_banned_imports_rps.csv](/inputs/state_policies/techs_banned_imports_rps.csv)
---

  - [techs_banned_rps.csv](/inputs/state_policies/techs_banned_rps.csv)
    - **Description:** Indicates which technolgies are not eligible to contribute to RPS
---

  - [unbundled_limit_ces.csv](/inputs/state_policies/unbundled_limit_ces.csv)
    - **Description:** Limit on fraction of credits towards CES which can be purchased unbundled from other states 
---

  - [unbundled_limit_rps.csv](/inputs/state_policies/unbundled_limit_rps.csv)
    - **Description:** Limit on fraction of credits towards RPS which can be purchased unbundled from other states 
---


<a id='inputs-storage'></a>
#### inputs/storage

  - [PSH_supply_curves_durations.csv](/inputs/storage/PSH_supply_curves_durations.csv)
---

  - [storage_duration.csv](/inputs/storage/storage_duration.csv)
---

  - [storage_duration_pshdata.csv](/inputs/storage/storage_duration_pshdata.csv)
---

  - [storinmaxfrac.csv](/inputs/storage/storinmaxfrac.csv)
---


<a id='inputs-supply-curve'></a>
#### inputs/supply_curve

  - [bio_supplycurve.csv](/inputs/supply_curve/bio_supplycurve.csv)
    - **Description:** Regional biomass supply and costs by resource class
    - **Dollar year:** 2015
---

  - [dollaryear.csv](/inputs/supply_curve/dollaryear.csv)
---

  - [dr_shed_cap.csv](/inputs/supply_curve/dr_shed_cap.csv)
---

  - [dr_shed_cost.csv](/inputs/supply_curve/dr_shed_cost.csv)
---

  - [hyd_add_upg_cap.csv](/inputs/supply_curve/hyd_add_upg_cap.csv)
---

  - [hydcap.csv](/inputs/supply_curve/hydcap.csv)
---

  - [hydcost.csv](/inputs/supply_curve/hydcost.csv)
---

  - [interconnection_land.h5](/inputs/supply_curve/interconnection_land.h5)
---

  - [interconnection_offshore.h5](/inputs/supply_curve/interconnection_offshore.h5)
---

  - [PSH_supply_curves_capacity_10hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_ref_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_10hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_ref_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_10hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_10hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_10hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_10hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_12hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_ref_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_12hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_ref_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_12hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_12hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_12hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_12hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_8hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_ref_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_8hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_ref_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_8hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_8hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_8hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_capacity_8hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_10hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_ref_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_10hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_ref_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_10hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_10hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_10hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_10hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_12hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_ref_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_12hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_ref_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_12hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_12hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_12hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_12hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_8hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_ref_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_8hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_ref_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_8hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_8hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_8hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [PSH_supply_curves_cost_8hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004
    - **Citation:** [https://www.nrel.gov/gis/psh-supply-curves.html](https://www.nrel.gov/gis/psh-supply-curves.html)
---

  - [rev_paths.csv](/inputs/supply_curve/rev_paths.csv)
---

  - [sc_point_gid_old2new.csv](/inputs/supply_curve/sc_point_gid_old2new.csv)
---

  - [sitemap.h5](/inputs/supply_curve/sitemap.h5)
---

  - [spurline_cost.csv](/inputs/supply_curve/spurline_cost.csv)
---

  - [supplycurve_csp-reference.csv](/inputs/supply_curve/supplycurve_csp-reference.csv)
---

  - [supplycurve_egs-reference.csv](/inputs/supply_curve/supplycurve_egs-reference.csv)
---

  - [supplycurve_geohydro-reference.csv](/inputs/supply_curve/supplycurve_geohydro-reference.csv)
---

  - [supplycurve_upv-limited.csv](/inputs/supply_curve/supplycurve_upv-limited.csv)
---

  - [supplycurve_upv-open.csv](/inputs/supply_curve/supplycurve_upv-open.csv)
---

  - [supplycurve_upv-reference.csv](/inputs/supply_curve/supplycurve_upv-reference.csv)
---

  - [supplycurve_wind-ofs-limited.csv](/inputs/supply_curve/supplycurve_wind-ofs-limited.csv)
---

  - [supplycurve_wind-ofs-open.csv](/inputs/supply_curve/supplycurve_wind-ofs-open.csv)
---

  - [supplycurve_wind-ofs-reference.csv](/inputs/supply_curve/supplycurve_wind-ofs-reference.csv)
---

  - [supplycurve_wind-ons-limited.csv](/inputs/supply_curve/supplycurve_wind-ons-limited.csv)
---

  - [supplycurve_wind-ons-open.csv](/inputs/supply_curve/supplycurve_wind-ons-open.csv)
---

  - [supplycurve_wind-ons-reference.csv](/inputs/supply_curve/supplycurve_wind-ons-reference.csv)
---

  - [trans_intra_cost_adder.csv](/inputs/supply_curve/trans_intra_cost_adder.csv)
---


<a id='inputs-techs'></a>
#### inputs/techs

  - [tech_resourceclass.csv](/inputs/techs/tech_resourceclass.csv)
---

  - [techs_default.csv](/inputs/techs/techs_default.csv)
    - **Description:** List of technologies to be used in the model
---

  - [techs_subsetForTesting.csv](/inputs/techs/techs_subsetForTesting.csv)
    - **Description:** Short list of technologies for testin
---


<a id='inputs-transmission'></a>
#### inputs/transmission

  - [cost_hurdle_country.csv](/inputs/transmission/cost_hurdle_country.csv)
    - **File Type:** GAMS set
    - **Description:** Cost for transmission hurdle rate by country
    - **Indices:** country
    - **Dollar year:** 2004
---

  - [cost_hurdle_intra.csv](/inputs/transmission/cost_hurdle_intra.csv)
---

  - [rev_transmission_basecost.csv](/inputs/transmission/rev_transmission_basecost.csv)
    - **File Type:** inputs
    - **Description:** Unweighted average base cost across the four regions for which we have transmission cost data.
    - **Indices:** Transreg
    - **Dollar year:** 2004
---

  - [transmission_capacity_future_ba_baseline.csv](/inputs/transmission/transmission_capacity_future_ba_baseline.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the baseline case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_default.csv](/inputs/transmission/transmission_capacity_future_ba_default.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the default case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_all.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_all.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_all case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_SeamsD2b.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_SeamsD2b.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_SeamsD2B case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_SeamsD3_certain.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_SeamsD3_certain.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_SeamsD3_certain case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_SeamsD3_possible.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_SeamsD3_possible.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_SeamsD3_possible case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_SeamsD3_possible_unconstrained.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_SeamsD3_possible_unconstrained.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_SeamsD3_possible_unconstrained case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_VSC_all.csv](/inputs/transmission/transmission_capacity_future_ba_VSC_all.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the VSC_all_case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_county_baseline.csv](/inputs/transmission/transmission_capacity_future_county_baseline.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the baseline case at county resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_county_default.csv](/inputs/transmission/transmission_capacity_future_county_default.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the default case at county resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_LCC_1000miles_demand1_wind1_subferc_20230629.csv](/inputs/transmission/transmission_capacity_future_LCC_1000miles_demand1_wind1_subferc_20230629.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_1000miles_demand1_wind1_subferc_20230629 case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_init_AC_ba_NARIS2024.csv](/inputs/transmission/transmission_capacity_init_AC_ba_NARIS2024.csv)
    - **Description:** Initial AC transmission capacity from the NARIS 2024 system at the BA resolution - 'NARIS2024' is a better starting point for future-oriented studies, but it becomes increasingly inaccurate for years earlier than 2024
---

  - [transmission_capacity_init_AC_ba_REFS2009.csv](/inputs/transmission/transmission_capacity_init_AC_ba_REFS2009.csv)
    - **Description:** Initial AC transmission capacity from the 2009 transmission system for ReEDS at the BA resolution - 'REFS2009' does not inclue direction-dependent capacities or differentiated capacities for energy and PRM trading but it better represents historical additions between 2010-2024
---

  - [transmission_capacity_init_AC_county_NARIS2024.csv](/inputs/transmission/transmission_capacity_init_AC_county_NARIS2024.csv)
    - **Description:** Initial AC transmission capacity modified from the NARIS 2024 file to eliminate most supply (with county transmission) demand mismatches for the 2024 solve year
---

  - [transmission_capacity_init_AC_county_NARIS2024_base.csv](/inputs/transmission/transmission_capacity_init_AC_county_NARIS2024_base.csv)
    - **Description:** Initial AC transmission capacity from the NARIS 2024 system at the county resolution
---

  - [transmission_capacity_init_AC_transgrp_NARIS2024.csv](/inputs/transmission/transmission_capacity_init_AC_transgrp_NARIS2024.csv)
    - **Description:** Initial AC transmission capacity from the NARIS 2024 system at the transgrp resolution
---

  - [transmission_capacity_init_nonAC_ba.csv](/inputs/transmission/transmission_capacity_init_nonAC_ba.csv)
    - **Description:** Initial non-AC transmission capacity at the BA resolution
---

  - [transmission_capacity_init_nonAC_county.csv](/inputs/transmission/transmission_capacity_init_nonAC_county.csv)
    - **Description:** Initial non-AC transmission capacity at the county resolution
---

  - [transmission_cost_ac_500kv_ba.h5](/inputs/transmission/transmission_cost_ac_500kv_ba.h5)
    - **Description:** Transmission costs for new 500 kV AC at BA resolution
---

  - [transmission_cost_ac_500kv_county.h5](/inputs/transmission/transmission_cost_ac_500kv_county.h5)
    - **Description:** Transmission costs for new 500 kV AC at county resolution
---

  - [transmission_cost_dc_ba.csv](/inputs/transmission/transmission_cost_dc_ba.csv)
    - **Description:** Transmission costs for new 500 kV DC at BA resolution
---

  - [transmission_cost_dc_county.csv](/inputs/transmission/transmission_cost_dc_county.csv)
    - **Description:** Transmission costs for new 500 kV DC at county resolution
---

  - [transmission_distance_ba.h5](/inputs/transmission/transmission_distance_ba.h5)
    - **Description:** Length of least-cost transmission paths between zones at BA resolution
---

  - [transmission_distance_county.h5](/inputs/transmission/transmission_distance_county.h5)
    - **Description:** Length of least-cost transmission paths between zones at county resolution
---


<a id='inputs-upgrades'></a>
#### inputs/upgrades

  - [i_coolingtech_watersource_upgrades.csv](/inputs/upgrades/i_coolingtech_watersource_upgrades.csv)
    - **File Type:** Inputs
    - **Description:** List of cooling technologies for water sources that can be upgraded.
    - **Indices:** i
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [i_coolingtech_watersource_upgrades_link.csv](/inputs/upgrades/i_coolingtech_watersource_upgrades_link.csv)
    - **File Type:** Inputs
    - **Description:** List of cooling technologies for water sources that can be upgraded + their to, from, ctt (cooling technology type) and wst (water source type)
    - **Indices:** i, ctt, wst
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [upgrade_costs_ccs_coal.csv](/inputs/upgrades/upgrade_costs_ccs_coal.csv)
---

  - [upgrade_costs_ccs_gas.csv](/inputs/upgrades/upgrade_costs_ccs_gas.csv)
---

  - [upgrade_link.csv](/inputs/upgrades/upgrade_link.csv)
    - **File Type:** Inputs
    - **Description:** Techs that can be upgraded including the original technology, the technology it is upgrading to, and the delta.
    - **Indices:** i
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [upgrade_mult_atb23_ccs_adv.csv](/inputs/upgrades/upgrade_mult_atb23_ccs_adv.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment (advanced) over various years for upgrade technologies
    - **Indices:** i,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [upgrade_mult_atb23_ccs_con.csv](/inputs/upgrades/upgrade_mult_atb23_ccs_con.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment (conservative) over various years for upgrade technologies
    - **Indices:** i,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [upgrade_mult_atb23_ccs_mid.csv](/inputs/upgrades/upgrade_mult_atb23_ccs_mid.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment (Mid) over various years for upgrade technologies
    - **Indices:** i,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [upgradelink_water.csv](/inputs/upgrades/upgradelink_water.csv)
    - **File Type:** Inputs
    - **Description:** Water techs that can be upgraded including the original technology, the technology it is upgrading to, and the delta
    - **Indices:** i
    - **Dollar year:** N/A
    - **Citation:** N/A
---


<a id='inputs-userinput'></a>
#### inputs/userinput

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
    - **Description:** Sets of BA regions that a user can model in a run. Each column is a different region option and can be specified in cases using GSw_Region.
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


<a id='inputs-valuestreams'></a>
#### inputs/valuestreams

  - [var_map.csv](/inputs/valuestreams/var_map.csv)
---


<a id='inputs-variability'></a>
#### inputs/variability

  - [ccseason_dates.csv](/inputs/variability/ccseason_dates.csv)
---

  - [month2quarter.csv](/inputs/variability/month2quarter.csv)
---

  - [period_szn_user.csv](/inputs/variability/period_szn_user.csv)
---

  - [stressperiods_user.csv](/inputs/variability/stressperiods_user.csv)
---


<a id='inputs-variability-multi-year'></a>
##### inputs/variability/multi_year

  - [csp-none_ba.h5](/inputs/variability/multi_year/csp-none_ba.h5)
    - **Description:** Concentrated Solar Power resource supply curve. Data is a capacity factor i.e. a fraction.
---

  - [distpv-reference_ba.h5](/inputs/variability/multi_year/distpv-reference_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Distributed photovoltaics resource supply curve. Data is a capacity factor i.e. a fraction.
    - **Indices:** r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [temperature_celsius-ba.h5](/inputs/variability/multi_year/temperature_celsius-ba.h5)
---

  - [upv-limited_ba.h5](/inputs/variability/multi_year/upv-limited_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve using Limited access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [upv-open_ba.h5](/inputs/variability/multi_year/upv-open_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve using Open access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [upv-reference_ba.h5](/inputs/variability/multi_year/upv-reference_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve using Reference access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [wind-ofs-limited_ba.h5](/inputs/variability/multi_year/wind-ofs-limited_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Offshore wind resource supply curve using Limited access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [wind-ofs-open_ba.h5](/inputs/variability/multi_year/wind-ofs-open_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Offshore wind resource supply curve using Open access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [wind-ofs-reference_ba.h5](/inputs/variability/multi_year/wind-ofs-reference_ba.h5)
---

  - [wind-ons-limited_ba.h5](/inputs/variability/multi_year/wind-ons-limited_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Land-based wind resource supply curve using Limited access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [wind-ons-open_ba.h5](/inputs/variability/multi_year/wind-ons-open_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Land-based wind resource supply curve using Open access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---

  - [wind-ons-reference_ba.h5](/inputs/variability/multi_year/wind-ons-reference_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Land-based wind resource supply curve using Reference access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A
    - **Citation:** N/A
---


<a id='inputs-waterclimate'></a>
#### inputs/waterclimate

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


<a id='postprocessing'></a>
### postprocessing

  - [example.csv](/postprocessing/example.csv)
---


<a id='postprocessing-air-quality'></a>
#### postprocessing/air_quality

  - [scenarios.csv](/postprocessing/air_quality/scenarios.csv)
---


<a id='postprocessing-air-quality-rcm-data'></a>
##### postprocessing/air_quality/rcm_data

  - [counties_ACS_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/counties_ACS_high_stack_2017.csv)
---

  - [counties_H6C_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/counties_H6C_high_stack_2017.csv)
---

  - [states_ACS_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/states_ACS_high_stack_2017.csv)
---

  - [states_H6C_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/states_H6C_high_stack_2017.csv)
---


<a id='postprocessing-bokehpivot'></a>
#### postprocessing/bokehpivot

  - [reeds_scenarios.csv](/postprocessing/bokehpivot/reeds_scenarios.csv)
    - **Description:** Example data for ReEDS scenarios, each scenario with a custom style 
---


<a id='postprocessing-bokehpivot-in'></a>
##### postprocessing/bokehpivot/in

  - [example_custom_styles.csv](/postprocessing/bokehpivot/in/example_custom_styles.csv)
    - **Description:** Examples of custom styles used for bokehpivot
---

  - [example_data_US_electric_power_generation.csv](/postprocessing/bokehpivot/in/example_data_US_electric_power_generation.csv)
    - **Description:** Example data for US electric power generation
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
    - **Description:** Abbreviation and code for each state
---


<a id='postprocessing-bokehpivot-in-reeds2'></a>
###### postprocessing/bokehpivot/in/reeds2

  - [class_map.csv](/postprocessing/bokehpivot/in/reeds2/class_map.csv)
    - **Description:** Class mapping for bokehpivot postprocessing
---

  - [class_style.csv](/postprocessing/bokehpivot/in/reeds2/class_style.csv)
    - **Description:** Custom styles for classes in bokehpivot 
---

  - [con_adj_map.csv](/postprocessing/bokehpivot/in/reeds2/con_adj_map.csv)
---

  - [con_adj_style.csv](/postprocessing/bokehpivot/in/reeds2/con_adj_style.csv)
---

  - [cost_cat_map.csv](/postprocessing/bokehpivot/in/reeds2/cost_cat_map.csv)
---

  - [cost_cat_style.csv](/postprocessing/bokehpivot/in/reeds2/cost_cat_style.csv)
---

  - [ctt_map.csv](/postprocessing/bokehpivot/in/reeds2/ctt_map.csv)
---

  - [ctt_style.csv](/postprocessing/bokehpivot/in/reeds2/ctt_style.csv)
---

  - [hours.csv](/postprocessing/bokehpivot/in/reeds2/hours.csv)
    - **Description:** Hours for each of the 17 timeslices
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
    - **Description:** Custom colors for each technology used by bokehpivot
---

  - [trtype_map.csv](/postprocessing/bokehpivot/in/reeds2/trtype_map.csv)
---

  - [trtype_style.csv](/postprocessing/bokehpivot/in/reeds2/trtype_style.csv)
---

  - [wst_map.csv](/postprocessing/bokehpivot/in/reeds2/wst_map.csv)
---

  - [wst_style.csv](/postprocessing/bokehpivot/in/reeds2/wst_style.csv)
---


<a id='postprocessing-bokehpivot-out'></a>
##### postprocessing/bokehpivot/out

  - [main vs PR diff.csv](/postprocessing/bokehpivot/out/main%20vs%20PR%20diff.csv)
---

  - [main-view.csv](/postprocessing/bokehpivot/out/main-view.csv)
---

  - [PR-view.csv](/postprocessing/bokehpivot/out/PR-view.csv)
---

  - [view.csv](/postprocessing/bokehpivot/out/view.csv)
---


<a id='postprocessing-bokehpivot-out-report-2025-03-21-13-05-27'></a>
###### postprocessing/bokehpivot/out/report-2025-03-21-13-05-27

  - [report.xlsx](/postprocessing/bokehpivot/out/report-2025-03-21-13-05-27/report.xlsx)
---


<a id='postprocessing-bokehpivot-out-report-2025-06-03-11-55-40'></a>
###### postprocessing/bokehpivot/out/report-2025-06-03-11-55-40

  - [report.xlsx](/postprocessing/bokehpivot/out/report-2025-06-03-11-55-40/report.xlsx)
---


<a id='postprocessing-bokehpivot-out-report-2025-06-03-11-59-51'></a>
###### postprocessing/bokehpivot/out/report-2025-06-03-11-59-51

  - [report.xlsx](/postprocessing/bokehpivot/out/report-2025-06-03-11-59-51/report.xlsx)
---


<a id='postprocessing-bokehpivot-out-report-2025-06-03-12-06-11'></a>
###### postprocessing/bokehpivot/out/report-2025-06-03-12-06-11

  - [report.xlsx](/postprocessing/bokehpivot/out/report-2025-06-03-12-06-11/report.xlsx)
---


<a id='postprocessing-bokehpivot-out-report-2025-06-03-12-06-21'></a>
###### postprocessing/bokehpivot/out/report-2025-06-03-12-06-21

  - [report.xlsx](/postprocessing/bokehpivot/out/report-2025-06-03-12-06-21/report.xlsx)
---


<a id='postprocessing-bokehpivot-out-report-2025-06-05-12-38-18'></a>
###### postprocessing/bokehpivot/out/report-2025-06-05-12-38-18

  - [report.xlsx](/postprocessing/bokehpivot/out/report-2025-06-05-12-38-18/report.xlsx)
---


<a id='postprocessing-bokehpivot-out-view'></a>
###### postprocessing/bokehpivot/out/view

  - [view.csv](/postprocessing/bokehpivot/out/view/view.csv)
---


<a id='postprocessing-combine-runs'></a>
#### postprocessing/combine_runs

  - [combinefiles.csv](/postprocessing/combine_runs/combinefiles.csv)
---

  - [runlist.csv](/postprocessing/combine_runs/runlist.csv)
---


<a id='postprocessing-land-use'></a>
#### postprocessing/land_use


<a id='postprocessing-land-use-inputs'></a>
##### postprocessing/land_use/inputs

  - [federal_land_categories.csv](/postprocessing/land_use/inputs/federal_land_categories.csv)
---

  - [field_definitions.csv](/postprocessing/land_use/inputs/field_definitions.csv)
---

  - [nlcd_categories.csv](/postprocessing/land_use/inputs/nlcd_categories.csv)
---

  - [nlcd_combined_categories.csv](/postprocessing/land_use/inputs/nlcd_combined_categories.csv)
---

  - [usgs_categories.csv](/postprocessing/land_use/inputs/usgs_categories.csv)
---

  - [usgs_combined_categories.csv](/postprocessing/land_use/inputs/usgs_combined_categories.csv)
---


<a id='postprocessing-plots'></a>
#### postprocessing/plots

  - [scghg_annual.csv](/postprocessing/plots/scghg_annual.csv)
---

  - [transmission-interface-coords.csv](/postprocessing/plots/transmission-interface-coords.csv)
---


<a id='postprocessing-retail-rate-module'></a>
#### postprocessing/retail_rate_module

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
    - **Description:** End use load by state since 1960
---

  - [map_i_to_tech.csv](/postprocessing/retail_rate_module/map_i_to_tech.csv)
    - **Description:** Maps i to tech with custom coloring for each
---


<a id='postprocessing-retail-rate-module-inputs'></a>
##### postprocessing/retail_rate_module/inputs

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

  - [rsmap.csv](/postprocessing/retail_rate_module/inputs/rsmap.csv)
    - **Description:** Mapping for BAs to resource regions
    - **Indices:** r,rs
---

  - [state-meanbiaserror_rate-aggregation.csv](/postprocessing/retail_rate_module/inputs/state-meanbiaserror_rate-aggregation.csv)
---

  - [Table_9.8_Average_Retail_Prices_of_Electricity.xlsx](/postprocessing/retail_rate_module/inputs/Table_9.8_Average_Retail_Prices_of_Electricity.xlsx)
    - **Description:** Historical EIA861 rates (annual and monthly)
---


<a id='postprocessing-revalue'></a>
#### postprocessing/reValue

  - [scenarios.csv](/postprocessing/reValue/scenarios.csv)
---


<a id='postprocessing-tableau'></a>
#### postprocessing/tableau

  - [tables_to_aggregate.csv](/postprocessing/tableau/tables_to_aggregate.csv)
---


<a id='preprocessing'></a>
### preprocessing


<a id='preprocessing-atb-updates-processing'></a>
#### preprocessing/atb_updates_processing


<a id='preprocessing-atb-updates-processing-input-files'></a>
##### preprocessing/atb_updates_processing/input_files

  - [batt_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/batt_plant_char_format.csv)
---

  - [conv_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/conv_plant_char_format.csv)
---

  - [csp_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/csp_plant_char_format.csv)
---

  - [geo_fom_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/geo_fom_plant_char_format.csv)
---

  - [h2-combustion_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/h2-combustion_plant_char_format.csv)
    - **Description:** Plant characteristics for which the H2-CC and CT ATB estimates are made using Gas-CC and CT data in preprocessing
---

  - [ofs-wind_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ofs-wind_plant_char_format.csv)
---

  - [ofs-wind_rsc_mult_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ofs-wind_rsc_mult_plant_char_format.csv)
---

  - [ons-wind_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ons-wind_plant_char_format.csv)
---

  - [upv_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/upv_plant_char_format.csv)
---


<a id='reeds2pras'></a>
### reeds2pras


<a id='reeds2pras-test'></a>
#### reeds2pras/test


<a id='reeds2pras-test-reeds-cases'></a>
##### reeds2pras/test/reeds_cases


<a id='reeds2pras-test-reeds-cases-pacific'></a>
###### reeds2pras/test/reeds_cases/Pacific


<a id='reeds2pras-test-reeds-cases-pacific-inputs-case'></a>
###### reeds2pras/test/reeds_cases/Pacific/inputs_case

  - [hydcf.csv](/reeds2pras/test/reeds_cases/Pacific/inputs_case/hydcf.csv)
---

  - [outage_forced_hourly.h5](/reeds2pras/test/reeds_cases/Pacific/inputs_case/outage_forced_hourly.h5)
---

  - [outage_forced_static.csv](/reeds2pras/test/reeds_cases/Pacific/inputs_case/outage_forced_static.csv)
---

  - [outage_scheduled_hourly.h5](/reeds2pras/test/reeds_cases/Pacific/inputs_case/outage_scheduled_hourly.h5)
---

  - [outage_scheduled_static.csv](/reeds2pras/test/reeds_cases/Pacific/inputs_case/outage_scheduled_static.csv)
---

  - [resources.csv](/reeds2pras/test/reeds_cases/Pacific/inputs_case/resources.csv)
---

  - [tech-subset-table.csv](/reeds2pras/test/reeds_cases/Pacific/inputs_case/tech-subset-table.csv)
---

  - [unitdata.csv](/reeds2pras/test/reeds_cases/Pacific/inputs_case/unitdata.csv)
---

  - [unitsize.csv](/reeds2pras/test/reeds_cases/Pacific/inputs_case/unitsize.csv)
---

  - [upgrade_link.csv](/reeds2pras/test/reeds_cases/Pacific/inputs_case/upgrade_link.csv)
---


<a id='reeds2pras-test-reeds-cases-pacific-reeds-augur'></a>
###### reeds2pras/test/reeds_cases/Pacific/ReEDS_Augur


<a id='reeds2pras-test-reeds-cases-pacific-reeds-augur-augur-data'></a>
###### reeds2pras/test/reeds_cases/Pacific/ReEDS_Augur/augur_data

  - [cap_converter_2032.csv](/reeds2pras/test/reeds_cases/Pacific/ReEDS_Augur/augur_data/cap_converter_2032.csv)
---

  - [energy_cap_2032.csv](/reeds2pras/test/reeds_cases/Pacific/ReEDS_Augur/augur_data/energy_cap_2032.csv)
---

  - [max_cap_2032.csv](/reeds2pras/test/reeds_cases/Pacific/ReEDS_Augur/augur_data/max_cap_2032.csv)
---

  - [pras_load_2032.h5](/reeds2pras/test/reeds_cases/Pacific/ReEDS_Augur/augur_data/pras_load_2032.h5)
---

  - [pras_vre_gen_2032.h5](/reeds2pras/test/reeds_cases/Pacific/ReEDS_Augur/augur_data/pras_vre_gen_2032.h5)
---

  - [tran_cap_2032.csv](/reeds2pras/test/reeds_cases/Pacific/ReEDS_Augur/augur_data/tran_cap_2032.csv)
---


<a id='reeds2pras-test-reeds-cases-usa-vsc-2035'></a>
###### reeds2pras/test/reeds_cases/USA_VSC_2035

  - [cases_USA_VSC_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/cases_USA_VSC_2035.csv)
---

  - [meta.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/meta.csv)
---


<a id='reeds2pras-test-reeds-cases-usa-vsc-2035-inputs-case'></a>
###### reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case

  - [forcedoutage_hourly.h5](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/forcedoutage_hourly.h5)
---

  - [hydcf.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/hydcf.csv)
---

  - [outage_forced_static.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/outage_forced_static.csv)
---

  - [resources.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/resources.csv)
---

  - [tech-subset-table.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/tech-subset-table.csv)
---

  - [unitdata.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/unitdata.csv)
---

  - [unitsize.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/unitsize.csv)
---

  - [upgrade_link.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/upgrade_link.csv)
---


<a id='reeds2pras-test-reeds-cases-usa-vsc-2035-reeds-augur'></a>
###### reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur


<a id='reeds2pras-test-reeds-cases-usa-vsc-2035-reeds-augur-augur-data'></a>
###### reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data

  - [cap_converter_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/cap_converter_2035.csv)
---

  - [energy_cap_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/energy_cap_2035.csv)
---

  - [max_cap_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/max_cap_2035.csv)
---

  - [pras_load_2035.h5](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/pras_load_2035.h5)
---

  - [pras_vre_gen_2035.h5](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/pras_vre_gen_2035.h5)
---

  - [tran_cap_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/tran_cap_2035.csv)
---


<a id='reeds-augur'></a>
### ReEDS_Augur

  - [augur_switches.csv](/ReEDS_Augur/augur_switches.csv)
---


<a id='tests'></a>
### tests


<a id='tests-data'></a>
#### tests/data


<a id='tests-data-county'></a>
##### tests/data/county

  - [csp.h5](/tests/data/county/csp.h5)
    - **Description:** Subset of county-level data for the github runner county test
---

  - [distpv.h5](/tests/data/county/distpv.h5)
    - **Description:** Subset of county-level data for the github runner county test
---

  - [upv.h5](/tests/data/county/upv.h5)
    - **Description:** Subset of county-level data for the github runner county test
---

  - [wind-ofs.h5](/tests/data/county/wind-ofs.h5)
    - **Description:** Subset of county-level data for the github runner county test
---

  - [wind-ons.h5](/tests/data/county/wind-ons.h5)
    - **Description:** Subset of county-level data for the github runner county test
---


## Files 

- [cases.csv](/cases.csv)
  - **File Type:** Switches file
  - **Description:** Contains the configuration settings for the ReEDS run(s).
  - **Dollar year:** 2004
  - **Citation:** [https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/38e6610a8c6a92291804598c95c11b707bf187b9/cases.csv](https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/38e6610a8c6a92291804598c95c11b707bf187b9/cases.csv)
---

- [cases_examples.csv](/cases_examples.csv)
---

- [cases_small.csv](/cases_small.csv)
  - **Description:** Contains settings to run ReEDS at a smaller scale to test operability of the ReEDS model. Turns off several technologies and reduces the model size to significantly improve solve times.
---

- [cases_standardscenarios.csv](/cases_standardscenarios.csv)
  - **File Type:** StdScen Cases file
  - **Description:** Contains the configuration settings for the Standard Scenarios ReEDS runs.
---

- [cases_test.csv](/cases_test.csv)
  - **Description:** Contains the configuration settings for doing test runs including the default Pacific census division test case.
---

- [e_report_params.csv](/e_report_params.csv)
  - **Description:** Contains a parameter list used in the model along with descriptions of what they are and units used.
---

- [runfiles.csv](/runfiles.csv)
  - **Description:** Contains the locations of input data that is copied from the repository into the runs folder for each respective case.
---

- [sources.csv](/sources.csv)
  - **Description:** CSV file containing a list of all input files (csv, h5, csv.gz)
---

