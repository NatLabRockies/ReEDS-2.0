## Summary

## Technical Details
### Implementation notes

### Additional changes (if any)

### Switches added/removed/changed (if any)

### Issues resolved (if any)

### Known incompatibilities (if any)

### Relevant sources or documentation (if any)

### Is the model cleaner/better/faster/smaller than before? If so, how?

## Validation / Comparison Report
### Link to report and/or example plots

### (if pertinent) How big is the default run folder (runs/{base}_ref_seq/) before and after the change?

### (if pertinent) What is the run time for ref_seq on the same machine before and after the change?

## Review
### Charge code for review

### Was a subject-matter review from outside the ReEDS team performed?

### Make sure you followed the [coding conventions](https://github.nrel.gov/ReEDS/ReEDS-2.0/wiki/Coding-Conventions) for ReEDS.

### Remember to tag the new version after merging. See the [wiki](https://github.nrel.gov/ReEDS/ReEDS-2.0/wiki/Versioning) for instructions.

### Remember to generate and update the sources.csv and sources_documentation.md files before merging. Instructions and tools for completing this process can be found in [documentation_tools](/postprocessing/documentation_tools/).

### Was anything relevant to the ReEDS-to-PLEXOS conversion changed? If yes, please @ or notify Luke Lavin and Pedro Sanchez Perez.
<!-- For reference, a list of parameters and files relevant to ReEDS-to-PLEXOS (as of 2022-11-07) is given below:
# Properties read from GDX inputs.gdx file
bcr
can_exports
can_exports_h_frac
can_imports
can_imports_szn_frac
cap_hyd_szn_adj
cf_adj_t
cf_hyd
cfhist_hyd
co2_tax
converter_efficiency_vsc
cost_vom
csp_sm
degrade_annual
e
emit_rate
forced_outage
fuel_price
h_szn
heat_rate
hierarchy
hours
hydmin
ilr
initv
m_cf_szn
maxage
newv
planned_outage
r
storage_duration
storage_eff
SW_OpResTradeLevel
tranloss
 
# CSVs read in
inputs_case/flex_frac_all.csv
inputs_case/load_multiplier.csv
inputs_case/reeds_ba_tz_map.csv
outputs/cap_converter_out.csv
outputs/cap_ivrt.csv
outputs/cap_new_ivrt.csv
outputs/cap.csv
outputs/co2_price.csv
outputs/gen_h.csv
outputs/invtran_out.csv
outputs/losses_ann.csv
outputs/repgasprice_r.csv
outputs/ret_ivrt.csv
outputs/tran_out.csv
 
# H5 etc read in
inputs_case/csp.h5
inputs_case/load.h5
inputs_case/recf.h5
-->

### Was anything relevant to ReEDS2PRAS changed? If yes, please @ or notify Surya Dhulipala.
<!-- Files used by ReEDS2PRAS (as of 2023-04-21) are:
* In {case}/ReEDS_Augur/augur_data:
    * cap_converter_{year}.csv
    * energy_cap_{year}.csv
    * forced_outage_{year}.csv
    * max_cap_{year}.csv
    * tran_cap_{year}.csv
    * pras_load_{year}.h5
    * pras_vre_gen_{year}.h5
* In {case}/inputs_case:
    * resources.csv
    * tech-subset-table.csv
    * unitdata.csv
    * unitsize.csv
-->
