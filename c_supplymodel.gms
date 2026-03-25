*Setting the default slash
$setglobal ds \

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

*========================================
* -- Supply Side Variable Declaration --
*========================================

positive variables

* load variable - set equal to load_exog to compute holistic marginal price
  LOAD(r,allh,t)                  "--MW-- busbar load for each balancing region"
  EVLOAD(r,allh,t)                "--MW-- busbar load specific to EVs"
  FLEX(flex_type,r,allh,t)        "--MW-- flexible load shifted to each timeslice"
  PEAK_FLEX(r,allszn,t)           "--MW-- peak busbar load adjustment based on load flexibility"
  DROPPED(r,allh,t)               "--MW-- dropped load (only allowed before Sw_StartMarkets)"

* capacity and investment variables
  CAP_SDBIN(i,v,r,allszn,sdbin,t)  "--MW-- generation capacity by storage duration bin for relevant technologies"
  CAP(i,v,r,t)                     "--MW-- total generation capacity in MWac (MWdc for PV); PV capacity of hybrid PV+battery"
  CAP_RSC(i,v,r,rscbin,t)          "--MW-- total generation capacity in MWac (MWdc for PV) for wind-ons and upv"
  GROWTH_BIN(gbin,i,st,t)          "--MW-- total new (from INV) generation capacity in each growth bin by state and technology group"
  INV(i,v,r,t)                     "--MW-- generation capacity add in year t"
  EXTRA_PRESCRIP(pcat,r,t)         "--MW-- builds beyond those prescribed once allowed in firstyear(pcat) - exceptions for gas-ct, wind-ons, and wind-ofs"
  INV_CAP_UP(i,v,r,rscbin,t)       "--MW-- upsized generation capacity addition in year t"
  INV_ENER_UP(i,v,r,rscbin,t)      "--MW-- upsized energy addition in year t using capacity factor to convert to capacity units"
  INV_REFURB(i,v,r,t)              "--MW-- investment in refurbishments of technologies that use a resource supply curve"
  INV_RSC(i,v,r,rscbin,t)          "--MW-- investment in technologies that use a resource supply curve"
  UPGRADES(i,v,r,t)                "--MW-- investments in upgraded capacity from ii to i"
  UPGRADES_RETIRE(i,v,r,t)         "--MW-- upgrades that have been retired - used as a free slack variable in eq_cap_upgrade"

* The units for  all of the operatinal variables are average MW or MWh/time-slice hours
* generation and storage variables
  GEN(i,v,r,allh,t)                   "--MW-- electricity generation (post-curtailment) in hour h"
  GEN_PVB_P(i,v,r,allh,t)             "--MW-- average PV generation from hybrid PV+Battery in hour h"
  GEN_PVB_B(i,v,r,allh,t)             "--MW-- average Battery generation (discharge) from hybrid PV+Battery in hour h"
  AVAIL_SITE(x,allh,t)                "--MW-- available generation from all resources at reV site x"
  CURT(r,allh,t)                      "--MW-- curtailment from vre generators in hour h"
  MINGEN(r,allszn,t)                  "--MW-- minimum generation level in each season"
  STORAGE_IN(i,v,r,allh,t)            "--MW-- storage charging in hour h that is charging from a given source technology; not used for CSP-TES"
  STORAGE_IN_PVB_P(i,v,r,allh,t)      "--MW-- PV+Battery storage charging in hour h that is charging from a coupled PV technology"
  STORAGE_IN_PVB_G(i,v,r,allh,t)      "--MW-- PV+Battery storage charging in hour h that is charging from a source on the grid"
  STORAGE_LEVEL(i,v,r,allh,t)         "--MWh per day-- storage level in hour h"
  DR_SHIFT(i,v,r,allh,allhh,t)        "--MWh-- annual demand response load shifted to timeslice h from timeslice hh"
  DR_SHED(i,v,r,allh,t)               "--MWh-- annual demand response load shed from timeslice h"
  LAST_HOUR_SOC(i,v,r,allh,t)         "--MWh-- last hour state of charge when running flex without infinite loop"

* flexible CCS variables
  CCSFLEX_POW(i,v,r,allh,t)                "--avg MW-- average power consumed for CCS system"
  CCSFLEX_POWREQ(i,v,r,allh,t)             "--avg MW-- average power requirement for CCS system"
  CCSFLEX_STO_STORAGE_LEVEL(i,v,r,allh,t)  "--varies-- level of process storage (e.g., chemical solvent) in the CCS system"
  CCSFLEX_STO_STORAGE_CAP(i,v,r,t)         "--varies-- capacity of process storage (e.g., chemical solvent) in the CCS system"

* trade variables
  FLOW(r,rr,allh,t,trtype)        "--MW-- electricity flow on transmission lines in hour h"
  OPRES_FLOW(ortype,r,rr,allh,t)  "--MW-- interregional trade of operating reserves by operating reserve type"
  PRMTRADE(r,rr,trtype,allszn,t)  "--MW-- planning reserve margin capacity traded from r to rr"

* operating reserve variables
  OPRES(ortype,i,v,r,allh,t)      "--MW-- operating reserves by type"

* variable fuel amounts
  GASUSED(cendiv,gb,allh,t)             "--MMBtu/hour-- total gas used by gas bin",
  VGASBINQ_NATIONAL(fuelbin,t)          "--MMBtu-- National quantity of gas by bin"
  VGASBINQ_REGIONAL(fuelbin,cendiv,t)   "--MMBtu-- Regional (census divisions) quantity of gas by bin"
  BIOUSED(bioclass,r,t)                 "--MMBtu-- total biomass used by biomass class"

* RECS variables
  RECS(RPSCat,i,st,ast,t)               "--MWh-- renewable energy credits from state st to state ast",
  ACP_PURCHASES(RPSCat,st,t)            "--MWh-- purchases of ACP credits to meet the RPS constraints",

* transmission variables
  CAPTRAN_ENERGY(r,rr,trtype,t)                  "--MW-- capacity of transmission for energy trading"
  CAPTRAN_PRM(r,rr,trtype,t)                     "--MW-- capacity of transmission for PRM trading"
  CAPTRAN_GRP(transgrp,transgrpp,t)              "--MW-- capacity of groups of transmission interfaces"
  INVTRAN(r,rr,trtype,t)                         "--MW-- investment in transmission capacity"
  CAP_CONVERTER(r,t)                             "--MW-- VSC AC/DC converter capacity"
  INV_CONVERTER(r,t)                             "--MW-- investment in AC/DC converter capacity"
  CONVERSION(r,allh,intype,outtype,t)            "--MW-- conversion of AC->DC or DC->AC"
  CONVERSION_PRM(r,allszn,intype,outtype,t)      "--MW-- planning reserve margin capacity sent through VSC AC/DC converters"
  CAP_SPUR(x,t)                                  "--MW-- capacity of spur lines"
  INV_SPUR(x,t)                                  "--MW-- investment in spur line capacity"
  INV_POI(r,t)                                   "--MW-- investment in new POI capacity (for network reinforcement costs)"

* production-, CO2-, and hydrogen-specific variables
  PRODUCE(p,i,v,r,allh,t)               "--tonnes/hour-- production of hydrogen or DAC capture"
  CO2_CAPTURED(r,allh,t)                "--tonnes/hour-- amount of CO2 captured from DAC and CCS technologies"
  CO2_STORED(r,cs,allh,t)               "--tonnes/hour-- amount of CO2 stored underground"
  CO2_FLOW(r,rr,allh,t)                 "--tonnes/hour-- interregional flow of CO2"
  CO2_TRANSPORT_INV(r,rr,t)             "--tonnes/hour-- investment in interregional CO2 transport capacity"
  CO2_SPURLINE_INV(r,cs,t)              "--tonnes/hour-- spurline investment from r to carbon storage site (saline storage basin)"  
  H2_FLOW(r,rr,allh,t)                  "--tonnes/hour-- interregional flow of hydrogen"
  H2_TRANSPORT_INV(r,rr,t)              "--tonnes/hour-- investment in interregional hydrogen transmission capacity"
  H2_STOR_INV(h2_stor,r,t)              "--tonnes-- investment in hydrogen storage capacity"
  H2_STOR_CAP(h2_stor,r,t)              "--tonnes-- hydrogen storage capacity"
  H2_STOR_IN(h2_stor,r,allh,t)          "--tonnes/hour-- injection of H2 into storage in a given timeslice"
  H2_STOR_OUT(h2_stor,r,allh,t)         "--tonnes/hour-- widthdrawal of H2 from storage in a given timeslice"
  H2_STOR_LEVEL(h2_stor,r,allszn,allh,t) "--tonnes-- total storage level of H2 in a timeslice by storage type"
  H2_STOR_LEVEL_SZN(h2_stor,r,allszn,t)  "--tonnes-- total storage level of H2 in a period by storage type"

* water climate variables
  WATCAP(i,v,r,t)                        "--million gallons/year; Mgal/yr-- total water access capacity available in terms of withdraw/consumption per year"
  WAT(i,v,w,r,allh,t)                    "--Mgal-- quantity of water withdrawn or consumed in hour h"
  WATER_CAPACITY_LIMIT_SLACK(wst,r,t)    "--Mgal/yr-- insufficient water supply in region r, of water type wst, in year t "
;

Variables
* with negative emissions technologies (e.g. BECCS, DAC) - emissions
* can become negative thus not restricted to the positive domain
  EMIT(e,r,t)                            "----tons (thousand metric tons for CO2)-- total emissions in a region (note: units dependent on emit_scale)"
;

*========================================
* -- Supply Side Equation Declaration --
*========================================
EQUATION

* load constraint to compute proper marginal value
 eq_loadcon(r,allh,t)                    "--MW-- load constraint used for computing the marginal energy price"
 eq_evloadcon(r,allszn,t)                "--MWh-- mapping of seasonal EV load to each timeslice"

* load flexibility constraints
 eq_load_flex_day(flex_type,r,allszn,t)  "--MWh-- total flexible load in each season is equal to the exogenously-specified flexible load"
 eq_load_flex1(flex_type,r,allh,t)       "--MWh-- exogenously-specified flexible demand (load_exog_flex) must be served by flexible load (FLEX)"
 eq_load_flex2(flex_type,r,allh,t)       "--MWh-- flexible load (FLEX) can't exceed exogenously-specified flexible demand (load_exog_flex)"
 eq_load_flex_peak(r,allh,allszn,t)      "--MWh-- adjust peak demand as needed based on the load flexibility (FLEX)"

* capital stock constraints
 eq_cap_init_noret(i,v,r,t)               "--MW-- Existing capacity that cannot be retired is equal to exogenously-specified amount"
 eq_cap_init_retmo(i,v,r,t)               "--MW-- Existing capacity that can be retired must be monotonically decreasing"
 eq_cap_init_retub(i,v,r,t)               "--MW-- Existing capacity that can be retired is less than or equal to exogenously-specified amount"
 eq_cap_new_noret(i,v,r,t)                "--MW-- New capacity that cannot be retired is equal to sum of all previous years investment"
 eq_cap_new_retmo(i,v,r,t)                "--MW-- New capacity that can be retired must be monotonically decreasing unless increased by investment"
 eq_cap_new_retub(i,v,r,t)                "--MW-- New capacity that can be retired is less than or equal to all previous years investment"
 eq_cap_rsc(i,v,r,rscbin,t)               "--MW-- Capacity accounting for techs with exogenous capacity tracked by rscbin"
 eq_cap_up(i,v,r,rscbin,t)                "--MW-- limit on capacity upsizing"
 eq_cap_upgrade(i,v,r,t)                  "--MW-- All purchased upgrades are greater than or equal to the sum of upgraded capacity"
 eq_ener_up(i,v,r,rscbin,t)               "--MW-- limit on energy upsizing"
 eq_forceprescription(pcat,r,t)           "--MW-- total investment in prescribed capacity must equal amount from exogenous prescriptions"
 eq_refurblim(i,r,t)                      "--MW-- total refurbishments cannot exceed the amount of capacity that has reached the end of its life"

* renewable supply curves
 eq_rsc_inv_account(i,v,r,t)              "--MW-- INV for rsc techs is the sum over all bins of INV_RSC"
 eq_rsc_INVlim(r,i,rscbin,t)              "--MW-- total investment from each rsc bin cannot exceed the available investment"

* capacity growth limits
 eq_growthlimit_relative(i,st,t)          "--MW-- relative growth limit on technologies"
 eq_growthbin_limit(gbin,st,tg,t)         "--MW-- capacity limit for each growth bin"
 eq_growthlimit_absolute(tg,t)            "--MW-- absolute growth limit on technologies"

* storage capacity credit supply curves
 eq_cap_sdbin_balance(i,v,r,allszn,t)     "--MW-- total binned storage capacity must be equal to total storage capacity"
 eq_sdbin_limit(ccreg,allszn,sdbin,t)     "--MW-- binned storage capacity cannot exceed storage duration bin size"

* operation and reliability
 eq_site_cf(x,allh,t)                          "--MW-- generation at site x <= CF * capacity of constituent resources"
 eq_spurclip(x,allh,t)                         "--MW-- generation at site x <= spurline capacity to x"
 eq_spur_noclip(x,t)                           "--MW-- spurline capacity to x must equal total generation capacity at x"
 eq_capacity_limit(i,v,r,allh,t)               "--MW-- generation limited to available capacity"
 eq_capacity_limit_hybrid(r,allh,t)            "--MW-- generation from hybrid resources limited to available capacity"
 eq_capacity_limit_nd(i,v,r,allh,t)            "--MW-- generation limited to available capacity for non-dispatchable resources"
 eq_curt_gen_balance(r,allh,t)                 "--MW-- net generation and curtailment must equal gross generation"
 eq_dhyd_dispatch(i,v,r,allszn,t)              "--MWh-- dispatchable hydro seasonal energy constraint (when not allowing seasonal enregy shifting)"
 eq_dhyd_dispatch_ann(i,v,r,t)                 "--MWh-- dispatchable hydro annual energy constraint (only when allowing seasonal energy shifting)"
 eq_dhyd_dispatch_szn(i,v,r,allszn,t)          "--MWh-- dispatchable hydro seasonal energy constraint"
 eq_min_cf(i,r,t)                              "--MWh-- minimum capacity factor constraint for each generator fleet, applied to (i,r)"
 eq_mingen_lb(r,allh,allszn,t)                 "--MW-- lower bound on minimum generation level"
 eq_mingen_ub(r,allh,allszn,t)                 "--MW-- upper bound on minimum generation level"
 eq_minloading(i,v,r,allh,allhh,t)             "--MW-- minimum loading across same-season hours"
 eq_reserve_margin(r,allszn,t)                 "--MW-- planning reserve margin requirement"
 eq_supply_demand_balance(r,allh,t)            "--MW-- supply demand balance"
 eq_vsc_flow(r,allh,t)                         "--MW-- DC power flow"
 eq_transmission_limit(r,rr,allh,t,trtype)     "--MW-- transmission flow limit"

* operating reserve constraints
 eq_OpRes_requirement(ortype,r,allh,t)         "--MW-- operating reserve constraint"
 eq_ORCap_large_res_frac(ortype,i,v,r,allh,t)  "--MW-- operating reserve capacity availability constraint for generators with reserve_frac > 0.5"
 eq_ORCap_small_res_frac(ortype,i,v,r,allh,t)  "--MW-- operating reserve capacity availability constraint for generators with reserve_frac <= 0.5"

* regional and national policies
 eq_emit_accounting(e,r,t)                "--tons (metric for CO2)-- accounting for total emissions in a region"
 eq_emit_rate_limit(e,r,t)                "--tons per MWh (metric for CO2)-- emission rate limit"
 eq_annual_cap(e,t)                       "--tons (metric for CO2)-- annual (year-specific) emissions cap",
 eq_bankborrowcap(e)                      "--weighted tons (metric for CO2)-- flexible banking and borrowing cap (to be used w/intertemporal solve only"
 eq_RGGI_cap(t)                           "--metric tons CO2-- RGGI constraint -- Regions' emissions must be less than the RGGI cap"
 eq_state_cap(st,t)                       "--metric tons CO2-- state-level CO2 cap constraint -- used to represent California cap and trade program"
 eq_CSAPR_Budget(csapr_group,t)           "--MT NOx-- CSAPR trading group emissions cannot exceed the budget cap"
 eq_CSAPR_Assurance(st,t)                 "--MT NOx-- CSAPR state emissions cannot exceed the assurance cap"
 eq_BatteryMandate(st,t)                  "--MW-- Battery storage capacity must be greater than indicated level"
 eq_cdr_cap(t)                            "--metric tons CO2-- CO2 removal (DAC and BECCS) can only offset emissions from fossil+CCS and methane leakage"

* RPS Policy equations
 eq_REC_Generation(RPSCat,i,st,t)         "--RECs-- Generation of RECs by state"
 eq_REC_Requirement(RPSCat,st,t)          "--RECs-- RECs generated plus trade must meet the state's requirement"
 eq_REC_ooslim(RPSCat,st,t)               "--RECs-- RECs imported cannot exceed a fraction of total requirement for certain states",
 eq_REC_launder(RPSCat,st,t)              "--RECs-- RECs laundering constraint"
 eq_REC_BundleLimit(RPSCat,st,ast,t)      "--RECS-- trade in bundle recs must be less than interstate electricity transmission"
 eq_REC_unbundledLimit(RPScat,st,t)       "--RECS-- unbundled RECS cannot exceed some percentage of total REC requirements"
 eq_RPS_OFSWind(st,t)                     "--MW-- MW of offshore wind capacity must be greater than or equal to RPS amount"
 eq_national_gen(t)                       "--MWh-- e.g. a national RPS or CES. require a certain amount of total generation to be from specified sources."

* fuel supply curve equations
 eq_gasused(cendiv,allh,t)                "--MMBtu-- gas used must be from the sum of gas bins"
 eq_gasbinlimit(cendiv,gb,t)              "--MMBtu-- limit on gas from each bin"
 eq_gasbinlimit_nat(gb,t)                 "--MMBtu-- national limit on gas from each bin"
 eq_bioused(r,t)                          "--MMBtu-- bio used must be from the sum of bio bins"
 eq_biousedlimit(bioclass,usda_region,t)  "--MMBtu-- limit on bio from each bin in each USDA region"

* regional natural gas supply curves
 eq_gasaccounting_regional(cendiv,t)         "--MMBtu-- regional gas consumption cannot exceed the amount used in bins"
 eq_gasaccounting_national(t)                "--MMBtu-- national gas consumption cannot exceed the amount used in bins"
 eq_gasbinlimit_regional(fuelbin,cendiv,t)   "--MMBtu-- regional binned gas usage cannot exceed bin capacity"
 eq_gasbinlimit_national(fuelbin,t)          "--MMBtu-- national binned gas usage cannot exceed bin capacity"

* hydrogen supply and demand
 eq_prod_capacity_limit(i,v,r,allh,t)                 "--tonne-- production cannot exceeds its capacity"
 eq_h2_demand(p,t)                                    "--tonne-- production of hydrogen must meet exogenous demand plus H2-CT use"
 eq_h2_demand_regional(r,allh,t)                      "--tonne/hour-- regional hydrogen supply must equal demand net trade and storage"
 eq_h2_transport_caplimit(r,rr,allh,t)                "--tonne/hour-- H2 flow cannot exceed cumulative pipeline investment"
 eq_h2_storage_flowlimit(h2_stor,r,allh,t)            "--tonne/hour-- H2 storage injection or withdrawal cannot exceed cumulative storage investment"
 eq_h2_storage_capacity(h2_stor,r,t)                  "--tonnes-- H2 storage capacity is sum of H2 storage investments"
 eq_h2_min_storage_cap(r,t)                           "--tonnes-- H2 storage capacity must be ≥ Sw_H2_MinStorHours * H2 usage capacity"
 eq_h2_storage_caplimit(h2_stor,r,allszn,allh,t)      "--tonnes-- total H2 storage in a storage facility cannot exceed investment capacity"
 eq_h2_storage_level(h2_stor,r,allszn,allh,t)         "--tonnes-- tracks H2 storage level by storage type and BA within and across periods"
 eq_h2_storage_caplimit_szn(h2_stor,r,allszn,t)       "--tonnes-- total H2 storage in a storage facility cannot exceed investment capacity"
 eq_h2_storage_level_szn(h2_stor,r,allszn,t)          "--tonnes-- tracks H2 storage level by storage type and BA within and across periods"

* CO2 capture and storage
 eq_co2_capture(r,allh,t)                    "--tonne-- accounting of CO2 captured from DAC and CCS technologies"
 eq_co2_injection_limit(cs,allh,t)           "--tonnes/hour-- limit on CO2 injection for each carbon site as a rate"
 eq_co2_sink(r,allh,t)                       "--tonnes/hour-- co2 stored or used must exceed co2 captured plus net trade"
 eq_co2_transport_caplimit(r,rr,allh,t)      "--tonnes-- limit on interregional co2 trade"
 eq_co2_spurline_caplimit(r,cs,allh,t)       "--tonnes-- limit on transport of CO2 from BA to carbon storage site"
 eq_co2_cumul_limit(cs,t)                    "--cumulative tonnes-- total stored in a reservor cannot exceed capacity"

* transmission equations
 eq_CAPTRAN_ENERGY(r,rr,trtype,t)            "--MW-- capacity accounting for transmission capacity for energy trading"
 eq_CAPTRAN_PRM(r,rr,trtype,t)               "--MW-- capacity accounting for transmission capacity for PRM trading"
 eq_prescribed_transmission(r,rr,trtype,t)   "--MW-- investment in transmission up to first year allowed must be less than the exogenous possible transmission",
 eq_PRMTRADELimit(r,rr,trtype,allszn,t)      "--MW-- trading of PRM capacity cannot exceed the line's capacity"
 eq_transmission_investment_max(t)           "--MWmile-- investment in transmission must be <= Sw_TransInvMax"
 eq_CAPTRAN_max(r,rr,trtype,t)               "--MW-- upper limit for transmission capacity of each trtype across individual interfaces"
 eq_CAPTRAN_max_total(r,rr,t)                "--MW-- upper limit for transmission capacity of all trtypes across individual interfaces"
 eq_CAP_CONVERTER(r,t)                       "--MW-- capacity accounting for VSC AC/DC converters"
 eq_CAP_SPUR(x,t)                            "--MW-- capacity accounting for spur lines"
 eq_converter_max(r,t)                       "--MW-- upper limit for VSC AC/DC converter capacity in individual BAs"
 eq_CONVERSION_limit_energy(r,allh,t)        "--MW-- AC/DC energy conversion is limited to converter capacity"
 eq_CONVERSION_limit_prm(r,allszn,t)         "--MW-- AC/DC PRM conversion is limited to converter capacity"
 eq_PRMTRADE_VSC(r,allszn,t)                 "--MW-- PRM capacity can flow through VSC lines but doesn't directly contribute to PRM"
 eq_POI_cap(r,t)                             "--MW-- POI capacity accounting (for network reinforcement costs)"
 eq_CAPTRAN_GRP(transgrp,transgrpp,t)        "--MW-- combined flow capacity between transmission groups"
 eq_transgrp_limit_energy(transgrp,transgrpp,allh,t) "--MW-- limit on combined interface energy flows"
 eq_transgrp_limit_prm(transgrp,transgrpp,allszn,t) "--MW-- limit on combined interface PRM flows"

* storage-specific equations
 eq_storage_capacity(i,v,r,allh,t)                "--MW-- Second storage capacity constraint in addition to eq_capacity_limit"
 eq_storage_duration(i,v,r,allh,t)                "--MWh-- limit STORAGE_LEVEL based on hours of storage available"
 eq_storage_in_cap(i,v,r,allh,t)                  "--MW-- storage_in must be less than a given fraction of power output capacity"
 eq_storage_in_minloading(i,v,r,allh,allhh,t)     "--MW-- minimum level for storage_in across same-season hours"
 eq_storage_level(i,v,r,allh,t)                   "--MWh per day-- Storage level inventory balance from one time-slice to the next"
 eq_storage_opres(i,v,r,allh,t)                   "--MWh per day-- there must be sufficient energy in the storage to be able to provide operating reserves"
 eq_storage_seas_szn(i,v,r,allszn,t)              "--MWh-- GEN in a season must be greater than a certain percentage of STORAGE_IN in that season"
 eq_storage_seas(i,v,r,t)                         "--MWh-- total STORAGE_IN must balance GEN across all time-slices"
 eq_storage_thermalres(i,v,r,allh,t)              "--MW-- thermal storage contribution to operating reserves is store_in only"


* demand-response specific equations
 eq_dr_max_shed(i,v,r,allh,t)             "--MW-- total shed allowed by demand response technologies from timeslice h"
 eq_dr_max_shed_hrs(i,v,r,t)              "--MW-- total hours shed is allowed to operate over the year"
 eq_dr_max_shift(i,v,r,allh,allhh,t)      "--MW-- total shifting allowed by demand response technologies to timeslice h from timeslice hh"
 eq_dr_max_decrease(i,v,r,allh,t)         "--MW-- maximum allowed decrease of load from demand response in timeslice h"
 eq_dr_max_increase(i,v,r,allh,t)         "--MW-- maximum allowed increase of load from demand response in timeslice h"
 eq_dr_gen(i,v,r,allh,t)                  "--MW-- link demand response shifting to generation"

* hybrid PV+battery equations
 eq_pvb_total_gen(i,v,r,allh,t)          "--MW-- generation post curtailment = generation from pv (post curtailment) + generation from battery - charging from PV"
 eq_pvb_array_energy_limit(i,v,r,allh,t) "--MW-- PV energy to storage (no curtailment recovery) + PV energy to inverter <= PV resource"
 eq_pvb_inverter_limit(i,v,r,allh,t)     "--MW-- energy moving through the inverter cannot exceed the inverter capacity"
 eq_pvb_itc_charge_reqt(i,v,r,t)         "--MWh-- total energy charged from local PV >= ITC qualification fraction * total energy charged"

* Canadian imports balance
 eq_Canadian_Imports(r,allszn,t)          "--MWh-- Balance of Canadian imports by season"

* water usage accounting
 eq_water_accounting(i,v,w,r,allh,t)      "--Mgal-- water usage accounting"
 eq_water_capacity_total(i,v,r,t)         "--Mgal-- specify required water access based on generation capacity and water use rate"
 eq_water_capacity_limit(wst,r,t)         "--Mgal/yr-- total water access must not exceed supply by region and water type"
 eq_water_use_limit(i,v,w,r,allszn,t)     "--Mgal/yr-- water use must not exceed available access"

* flexible CCS constraints
 eq_ccsflex_byp_ccsenergy_limit(i,v,r,allh,t)        "--avg MW-- Limit the CCS power for a bypass system in each time-slice"
 eq_ccsflex_sto_ccsenergy_limit_szn(i,v,r,allszn,t)  "--MWh-- Limit the CCS power for a storage system across a characteristic day"
 eq_ccsflex_sto_ccsenergy_balance(i,v,r,allszn,t)    "--MWh-- Total CCS energy requirement can be distributed across a characteristic day"
 eq_ccsflex_sto_storage_level(i,v,r,allh,t)          "--varies-- Track the level of the CCS storage balance for each time-slice"
 eq_ccsflex_sto_storage_level_max(i,v,r,allh,t)      "--varies-- Limit the level of the CCS storage system"
;

*==========================
* --- LOAD CONSTRAINTS ---
*==========================

* ---------------------------------------------------------------------------

*the marginal off of this constraint allows you to
*determine the full price of electricity load
*i.e. the price of load with consideration to operating
*reserve and planning reserve margin considered
eq_loadcon(r,h,t)$[rb(r)$tmodel(t)]..

    LOAD(r,h,t)

    =e=

*[plus] the static, exogenous load
    + load_exog_static(r,h,t)

*[plus] exogenously defined exports to Canada
* note net canadian load (when Sw_Canada = 2) is included
* in eq_supply_demand since LOAD needs to stay positive
* while net_trade can be negative and cause infeasibilities
    + can_exports_h(r,h,t)$[Sw_Canada=1]

*[plus] load from EV charging
    + EVLOAD(r,h,t)$Sw_EV

*[plus] load shifted from other timeslices
    + sum{flex_type, FLEX(flex_type,r,h,t) }$Sw_EFS_flex

*[plus] Load created by production activities
    + sum{(p,i,v)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)$(not sameas(i,"dac_gas"))],
          PRODUCE(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) }$Sw_Prod

*[plus] load for compressors associated with hydrogen storage injections or withdrawals
* tonnes/hour * MWh/tonnes = MW
    + sum{h2_stor$h2_stor_r(h2_stor,r),
        h2_network_load(h2_stor,t)
        * ( H2_STOR_IN(h2_stor,r,h,t) + H2_STOR_OUT(h2_stor,r,h,t) ) }$Sw_H2_CompressorLoad

* [plus] load for hydrogen pipeline compressors
* tonnes/hour * MWh/tonnes = MW
    + sum{rr$h2_routes(r,rr),
        h2_network_load("h2_compressor",t)
        * (( H2_FLOW(r,rr,h,t) + H2_FLOW(rr,r,h,t) ) / 2) }$Sw_H2_CompressorLoad
;

* ---------------------------------------------------------------------------

eq_evloadcon(r,szn,t)$[rb(r)$tmodel(t)$Sw_EV]..

    sum{h$h_szn(h,szn),hours(h) * EVLOAD(r,h,t) }

    =e=

    ev_dynamic_demand(r,szn,t)
;

* ---------------------------------------------------------------------------

*======================================
* --- LOAD FLEXIBILITY CONSTRAINTS ---
*======================================

* ---------------------------------------------------------------------------

*The following 3 equations apply to the flexibility of load in ReEDS, originally developed
*as part of the EFS study in ReEDS heritage and adapted for ReEDS-2.0 here.

* Additional work has been done to represent flexible load as a generator + storage
* with boundaries on how many timeslices this generator may shift. See equations
* in the DR CONSTRAINTS section for that representation

* FLEX load in each season equals the total exogenously-specified flexible load in each season
eq_load_flex_day(flex_type,r,szn,t)$[rb(r)$tmodel(t)$Sw_EFS_flex]..

    sum{h$h_szn(h,szn), FLEX(flex_type,r,h,t) * hours(h) } / numdays(szn)

    =e=

    sum{h$h_szn(h,szn), load_exog_flex(flex_type,r,h,t) * hours(h) } / numdays(szn)
;

* ---------------------------------------------------------------------------

* for the "previous" flex type: the amount of exogenously-specified load in timeslice "h"
* must be served by FLEX load either in the timeslice h or the timeslice PRECEEDING h
*
* for the "next" flex type: the amount of exogenously-specified load in timeslice "h"
* must be served by FLEX load either in the timeslice h or the timeslice FOLLOWING h
*
* for the "adjacent" flex type: the amount of exogenously-specified load in timeslice "h"
* must be served by FLEX load either in the timeslice h or a timeslice ADJACENT to h

eq_load_flex1(flex_type,r,h,t)$[rb(r)$tmodel(t)$Sw_EFS_flex]..

    FLEX(flex_type,r,h,t) * hours(h)

    + sum{hh$flex_h_corr1(flex_type,h,hh), FLEX(flex_type,r,hh,t) * hours(hh) }

    =g=

    load_exog_flex(flex_type,r,h,t) * hours(h)
;

* ---------------------------------------------------------------------------

* for the "previous" flex type: FLEX load in timeslice "h" cannot exceed the sum of
* exogenously-specified load in timeslice h and the timeslice following h
*
* for the "next" flex type: FLEX load in timeslice "h" cannot exceed the sum of
* exogenously-specified load in timeslice h and the timeslice preceeding h
*
* for the "adjacent" flex type: FLEX load in timeslice "h" cannot exceed the sum of
* exogenously-specified load in timeslice h and the timeslices adjacent to h

eq_load_flex2(flex_type,r,h,t)$[rb(r)$tmodel(t)$Sw_EFS_flex]..

    load_exog_flex(flex_type,r,h,t) * hours(h)

    + sum{hh$flex_h_corr2(flex_type,h,hh), load_exog_flex(flex_type,r,hh,t) * hours(hh) }

    =g=

    FLEX(flex_type,r,h,t) * hours(h)
;

* ---------------------------------------------------------------------------

eq_load_flex_peak(r,h,szn,t)$[rb(r)$tmodel(t)$Sw_EFS_flex]..
*   peak demand EFS flexibility adjustment is greater than
    PEAK_FLEX(r,szn,t)$h_szn(h,szn)

    =g=

*   the static peak in each timeslice
    peakdem_static_h(r,h,t)$h_szn(h,szn)

*   PLUS the flexibile load served in each timeslice
    + sum{flex_type, FLEX(flex_type,r,h,t) }$h_szn(h,szn)

*   MINUS the static peak demand in the season corresponding to each timeslice
    - peakdem_static_szn(r,szn,t)$h_szn(h,szn)
;

* ---------------------------------------------------------------------------

*=========================================================
* --- EQUATIONS RELATING CAPACITY ACROSS TIME PERIODS ---
*=========================================================

*====================================
* -- existing capacity equations --
*====================================

$ontext

The following six equations dictate how capacity is represented in the model.

The first three equations handle init-X vintages (those that existed pre-2010)
which are bounded by m_capacity_exog. With retirements (in the second and third
equations), the constraints imply that capacity must be less than or
equal to m_capacity_exog and monotonically decreasing over time -
implying that if endogenous capacity was reduced in the previous year,
it cannot be brought back online.

New capacity, handled in equations four through six, is the sum of previous
years' greenfield investments and refurbishments. The same logic is present
for retiring capacity, the only difference being that contemporaneous
investment can increase the present-period's capacity.

Upgraded capacity reduces the total amount of capacity available to the
upgraded-from technology. For example, the model starts with 100MW of
coaloldscr (m_capacity_exog = 100) capacity then upgrades 10MW of that to
coaloldscr_coal-ccs capacity. The remaining amount of available coaloldscr
is thus 90 and coaloldscr_coal-ccs capacity is 10 but both are still less
than the 100 available. As time progresses and exogenous capacity declines,
the model chooses which units to take offline.

$offtext

* ---------------------------------------------------------------------------

eq_cap_init_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $(not retiretech(i,v,r,t))]..

    m_capacity_exog(i,v,r,t)

* Account for capacity upsizing within init vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)],
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =e=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) / (1 - upgrade_derate(ii,v,r,t))}$[Sw_Upgrades = 1]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)],
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]
;

* ---------------------------------------------------------------------------

eq_cap_init_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $retiretech(i,v,r,t)]..

    m_capacity_exog(i,v,r,t)

* Account for capacity upsizing within init vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)],
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) / (1 - upgrade_derate(ii,v,r,t))}$[Sw_Upgrades = 1]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)],
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]

;

* ---------------------------------------------------------------------------

eq_cap_init_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $retiretech(i,v,r,t)]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],

         CAP(i,v,r,tt)

         + sum{ii$[valcap(ii,v,r,tt)$upgrade_from(ii,i)],
               CAP(ii,v,r,tt) / (1 - upgrade_derate(ii,v,r,tt)) }$[Sw_Upgrades = 1]
        }

* Account for capacity upsizing within init vintages
    + sum{rscbin$allow_cap_up(i,v,r,rscbin,t), INV_CAP_UP(i,v,r,rscbin,t) }

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) / (1 - upgrade_derate(ii,v,r,t))}$[Sw_Upgrades = 1]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)],
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]
;

* ---------------------------------------------------------------------------

*==============================
* -- new capacity equations --
*==============================

* ---------------------------------------------------------------------------

eq_cap_new_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $(not retiretech(i,v,r,t))]..

    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
        }

* Account for capacity upsizing within new vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)],
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =e=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) / (1 - upgrade_derate(ii,v,r,t))}$[Sw_Upgrades = 1]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)],
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]

;

* ---------------------------------------------------------------------------

eq_cap_new_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $retiretech(i,v,r,t)]..

    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
      }

* Account for capacity upsizing within new vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)],
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) / (1 - upgrade_derate(ii,v,r,t))}$[Sw_Upgrades = 1]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)],
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]
;

* ---------------------------------------------------------------------------

eq_cap_new_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $retiretech(i,v,r,t)]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],
         degrade(i,tt,t) * CAP(i,v,r,tt)

         + sum{ii$[valcap(ii,v,r,tt)$upgrade_from(ii,i)],
               CAP(ii,v,r,tt) / (1 - upgrade_derate(ii,v,r,tt)) }$[Sw_Upgrades = 1]
        }

    + INV(i,v,r,t)$valinv(i,v,r,t)

    + INV_REFURB(i,v,r,t)$[valinv(i,v,r,t)$refurbtech(i)$Sw_Refurb]

* Account for capacity upsizing within new vintages
    + sum{rscbin$allow_cap_up(i,v,r,rscbin,t), INV_CAP_UP(i,v,r,rscbin,t) }

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
           CAP(ii,v,r,t) / (1 - upgrade_derate(ii,v,r,t))}$[Sw_Upgrades = 1]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)],
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]
;

* ---------------------------------------------------------------------------
* Capacity accounting for rsc techs
eq_cap_rsc(i,v,r,rscbin,t)
    $[tmodel(t)
    $rsc_i(i)$(not sccapcosttech(i))
    $valcap(i,v,r,t)]..

    sum{tt$[tfirst(tt)$exog_rsc(i)],
         capacity_exog_rsc(i,v,r,rscbin,tt) }

    + sum{tt$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))
          $m_rscfeas(r,i,rscbin)
          $valinv(i,v,r,tt)],
          INV_RSC(i,v,r,rscbin,tt)
    }

    =e=

    CAP_RSC(i,v,r,rscbin,t)
;

* ---------------------------------------------------------------------------

eq_cap_upgrade(i,v,r,t)$[valcap(i,v,r,t)$upgrade(i)$Sw_Upgrades$tmodel(t)]..

    (1 - upgrade_derate(i,v,r,t)) * (

* without peristent upgrades, all upgrades correspond to their original bintage
    sum{(tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))$(yeart(tt)>=Sw_Upgradeyear)
             $valcap(i,v,r,tt)],
        UPGRADES(i,v,r,tt) }$[Sw_Upgrades=1]

* all previous years upgrades converted to new bintages of the present year
* NOTE: the 'v' in ivt(i,v,tt) here is an important distinction -
*       although we're summing over 'vv' we still only want upgrades
*       to be included for the upgrade tech's vintage combination
    + sum{(tt,vv)$[(tfix(tt) or tmodel(tt))$(initv(vv) or sameas(v,vv))
              $(yeart(tt)<=yeart(t))$ivt(i,v,tt)
              $(yeart(tt)>=Sw_Upgradeyear)
              $valcap(i,v,r,tt)
              $sum(ii$upgrade_from(i,ii),valcap(ii,vv,r,tt))],
        UPGRADES(i,vv,r,tt) }$[Sw_Upgrades=2]

* end product on upgrade_derate
    ) 

    =e=

    CAP(i,v,r,t)

* note this is equivalent to the previous version that had a =g=
* sign in the corrolary equation but either assumes a retired upgrade
* can be brought back to life again...
    + UPGRADES_RETIRE(i,v,r,t)$[not noret_upgrade_tech(i)]
;

* ---------------------------------------------------------------------------

* Capacity upsizing limit
*   This uses rscbin to constrain hydropower upsizing using supply curve data.
eq_cap_up(i,v,r,rscbin,t)$[tmodel(t)$allow_cap_up(i,v,r,rscbin,t)]..

    cap_cap_up(i,v,r,rscbin,t)

    =g=

    sum{tt$[(tmodel(tt) or tfix(tt))], INV_CAP_UP(i,v,r,rscbin,tt) }
;

* ---------------------------------------------------------------------------

*Energy upsizing limit
*   This uses rscbin to constrain hydropower upsizing using supply curve data.
eq_ener_up(i,v,r,rscbin,t)$[tmodel(t)$allow_ener_up(i,v,r,rscbin,t)]..

    cap_ener_up(i,v,r,rscbin,t)

    =g=

    sum{tt$[(tmodel(tt) or tfix(tt))], INV_ENER_UP(i,v,r,rscbin,tt) }
;

* ---------------------------------------------------------------------------

eq_forceprescription(pcat,r,t)$[tmodel(t)$force_pcat(pcat,t)$Sw_ForcePrescription
                               $sum{(i,newv)$[prescriptivelink(pcat,i)], valinv(i,newv,r,t) }]..

*capacity built in the current period or prior
    sum{(i,newv,tt)$[valinv(i,newv,r,tt)$prescriptivelink(pcat,i)
                     $(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))],
        INV(i,newv,r,tt) + INV_REFURB(i,newv,r,tt)$[refurbtech(i)$Sw_Refurb]}

    =e=

*must equal the cumulative prescribed amount
    sum{tt$[(yeart(tt)<=yeart(t))
            $(tmodel(tt) or tfix(tt))],
            noncumulative_prescriptions(pcat,r,tt)}

* plus any extra buildouts (no penalty here - used as free slack)
* only on or after the first year the techs are available
    + EXTRA_PRESCRIP(pcat,r,t)$[yeart(t)>=firstyear_pcat(pcat)]

* or in regions where there is a offshore wind requirement
    + EXTRA_PRESCRIP(pcat,r,t)$[r_offshore(r,t)$sameas(pcat,'wind-ofs')]
;


* ---------------------------------------------------------------------------

*limit the amount of refurbishments available in specific year
*this is the sum of all previous year's investment that is now beyond the age
*limit (i.e. it has exited service) plus the amount of retired exogenous capacity
*that we begin with
eq_refurblim(i,r,t)$[tmodel(t)$refurbtech(i)$Sw_Refurb]..

*investments that meet the refurbishment requirement (i.e. they've expired)
    sum{(vv,tt)$[m_refurb_cond(i,vv,r,t,tt)$(tmodel(tt) or tfix(tt))],
         INV(i,vv,r,tt) }

*[plus] exogenous decay in capacity
*note here that the tfix or tmodel set does not apply
*since we'd want capital that expires in off-years to
*be included in this calculation as well
    + sum{(v,tt)$[yeart(tt)<=yeart(t)],
         avail_retire_exog_rsc(i,v,r,tt) }

    =g=

*must exceed the total sum of investments in refurbishments
*that have yet to expire - implying an investment can be refurbished more than once
*if the first refurbishment has exceed its age limit
    sum{(vv,tt)$[inv_cond(i,vv,r,t,tt)$(tmodel(tt) or tfix(tt))],
         INV_REFURB(i,vv,r,tt)
       }
;

* ---------------------------------------------------------------------------

eq_rsc_inv_account(i,v,r,t)$[tmodel(t)$valinv(i,v,r,t)$rsc_i(i)]..

  sum{rscbin$m_rscfeas(r,i,rscbin), INV_RSC(i,v,r,rscbin,t) }

  =e=

  INV(i,v,r,t)
;

* ---------------------------------------------------------------------------

*note that the following equation only restricts inv_rsc and not inv_refurb
*therefore, the capacity indicated by the supply curve may be limiting
*but the plant can still be refurbished
eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)]..
*With water constraints, some RSC techs are expanded to include cooling technologies
*but the combination of m_rsc_con and rsc_agg allows for those investments
*to be limited by the numeraire techs' m_rsc_dat

*capacity indicated by the resource supply curve (with undiscovered geo available
*at the "discovered" amount and hydro upgrade availability adjusted over time)
    m_rsc_dat(r,i,rscbin,"cap") * (
        1$[not geo_hydro(i)] + geo_discovery(i,r,t)$geo_hydro(i))
    + hyd_add_upg_cap(r,i,rscbin,t)$(Sw_HydroCapEnerUpgradeType=1)
* available DR capacity
    + rsc_dr(i,r,"cap",rscbin,t)

    =g=

*must exceed the cumulative invested capacity in that region/class/bin...
    sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) <= yeart(t))$rsc_agg(i,ii)$(not dr(i))],
         INV_RSC(ii,v,r,rscbin,tt) * resourcescaler(ii) }

*plus exogenous (pre-start-year) capacity, using its level in the first year (tfirst)
    + sum{(ii,v,tt)$[tfirst(tt)$rsc_agg(i,ii)$(not dr(i))$exog_rsc(i)],
         capacity_exog_rsc(ii,v,r,rscbin,tt) }

* in that year for DR (since DR investment is annual)
    +  sum{(ii,v)$[valinv(ii,v,r,t)$rsc_agg(i,ii)$dr(i)],
           INV_RSC(ii,v,r,rscbin,t) * resourcescaler(ii) }
;

* ---------------------------------------------------------------------------

eq_growthlimit_relative(i,st,t)$[sum{r$[r_st(r,st)], valinv_irt(i,r,t) }
                                $tmodel(t)
                                $stfeas(st)
                                $Sw_GrowthRelCon
                                $(yeart(t)<=Sw_GrowthConLastYear)
                                $(yeart(t)>=model_builds_start_yr)]..

*the annual growth limit
     (yeart(t) - sum{tt$[tprev(t,tt)], yeart(tt) })
     * sum{gbin, GROWTH_BIN(gbin,i,st,t) }

    =g=

* must exceed the current periods investment
    sum{(v,r)$[valinv(i,v,r,t)$r_st(r,st)],
         INV(i,v,r,t) }
;

eq_growthbin_limit(gbin,st,tg,t)$[valinv_tg(st,tg,t)
                                 $tmodel(t)
                                 $stfeas(st)
                                 $Sw_GrowthRelCon
                                 $(yeart(t)<=Sw_GrowthConLastYear)
                                 $(yeart(t)>=model_builds_start_yr)]..

*the growth bin limit
     growth_bin_limit(gbin,st,tg,t)

    =g=

* must exceed the value in the growth bin
     sum{i$tg_i(tg,i), GROWTH_BIN(gbin,i,st,t) }
;

* ---------------------------------------------------------------------------

eq_growthlimit_absolute(tg,t)$[growth_limit_absolute(tg)$tmodel(t)
                               $Sw_GrowthAbsCon$(yeart(t)<=Sw_GrowthConLastYear)
                               $(yeart(t)>=model_builds_start_yr)]..

* the absolute limit of growth (in MW)
     (sum{tt$[tprev(tt,t)], yeart(tt) } - yeart(t))
     * growth_limit_absolute(tg)

     =g=

* must exceed the total investment - same RHS as previous equation
     sum{(i,v,r,rscbin)$[valinv(i,v,r,t)$m_rscfeas(r,i,rscbin)$tg_i(tg,i)$rsc_i(i)],
          INV_RSC(i,v,r,rscbin,t) }
;

* ---------------------------------------------------------------------------
* If using hybrid generators with endogenous spur lines, the available power from
* a reV site is limited by the CF and capacity of constituent resources at that site
eq_site_cf(x,h,t)
    $[tmodel(t)
    $Sw_SpurScen
    $xfeas(x)]..

    sum{(i,v,r)
        $[spur_techs(i)
        $x_r(x,r)
        $valgen(i,v,r,t)],
* Capacity factor of techs with endogenously-modeled spur lines
        m_cf(i,v,r,h,t)
* multiplied by total capacity of those techs
        * sum{rscbin
              $[valcap(i,v,r,t)
              $m_rscfeas(r,i,rscbin)
              $spurline_sitemap(i,r,rscbin,x)],
              CAP_RSC(i,v,r,rscbin,t)
        }
    }

    =g=

    AVAIL_SITE(x,h,t)
;

* ---------------------------------------------------------------------------
* If using hybrid generators with endogenous spur lines, each wind and solar generator
* is associated with a specific reV site x. The available generation from all generators
* at site x is limited to the spur-line capacity built to site x.
eq_spurclip(x,h,t)
    $[Sw_SpurScen
    $xfeas(x)
    $tmodel(t)]..

* Capacity of spur line to reV site limits the available generation at that site
    CAP_SPUR(x,t)

    =g=

    AVAIL_SITE(x,h,t)
;

* ---------------------------------------------------------------------------
* If spur-line sharing is disabled, the capacity of the spur line for site x
* must be >= the capacity of the hybrid reosurces (wind and solar) installed at site x
eq_spur_noclip(x,t)
    $[Sw_SpurScen
    $(not Sw_SpurShare)
    $xfeas(x)
    $tmodel(t)]..

* Capacity of spur line to site x
    CAP_SPUR(x,t)

    =g=

* must be >= to the wind/solar capacity installed at x
* (Since PV capacity is in DC, we divide CAP_RSC [DC] by ILR [DC/AC] to get AC spur line capacity.
*  ILR is 1 for all non-PV techs.)
    sum{(i,v,r,rscbin)
        $[spurline_sitemap(i,r,rscbin,x)
        $valcap(i,v,r,t)],
        CAP_RSC(i,v,r,rscbin,t) / ilr(i)
    }
;

* ---------------------------------------------------------------------------

*capacity must be greater than supply
*dispatchable hydro is accounted for both in this constraint and in eq_dhyd_dispatch
*this constraint does not apply to storage nor hybrid PV+Battery
*  limits for storage (including storage of hybrid PV+Battery) are tracked in eq_storage_capacity
*  limits for PV of Hybrid PV+Battery are tracked in eq_pvb_energy_balance
* limits for hybrid techs with shared spur lines are treated in eq_capacity_limit_hybrid
eq_capacity_limit(i,v,r,h,t)
    $[tmodel(t)$valgen(i,v,r,t)
    $(not spur_techs(i))
    $(not storage_standalone(i))$(not pvb(i))$(not nondispatch(i))]..
    
*total amount of dispatchable, non-hydro capacity
    avail(i,h)$[dispatchtech(i)$(not hydro_d(i))]
    * derate_geo_vintage(i,v)
    * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
    * CAP(i,v,r,t)

*total amount of dispatchable hydro capacity
    + avail(i,h)$hydro_d(i)
      * CAP(i,v,r,t) 
      * sum{szn$h_szn(h,szn), cap_hyd_szn_adj(i,szn,r) }
      * (1 + hydro_capcredit_delta(i,t)$[h_stress(h)])

*sum of non-dispatchable capacity multiplied by its rated capacity factor,
*only vre technologies are curtailable.
* This term accounts for energy-only and capacity-only upsizing,
* which is initially implemented only for hydro.
    + (m_cf(i,v,r,h,t)
        * (CAP(i,v,r,t)
*add energy embedded in energy-only upsizing
            + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))],
                INV_ENER_UP(i,v,r,rscbin,tt)$allow_ener_up(i,v,r,rscbin,tt)
*subtract energy that would be embedded in a capacity-only upsizing
                - degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt)$allow_cap_up(i,v,r,rscbin,tt) })
      )$[not dispatchtech(i)]

    =g=

*must exceed generation
    GEN(i,v,r,h,t)

*[plus] sum of operating reserves by type
    + sum{ortype$[Sw_OpRes$reserve_frac(i,ortype)$opres_h(h)$opres_model(ortype)],
          OPRES(ortype,i,v,r,h,t) }

*[plus] power consumed for flexible ccs
    + CCSFLEX_POW(i,v,r,h,t) $[ccsflex(i)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)]
;

* ---------------------------------------------------------------------------
* For hybrid resources, the sum of generation from constituent resources is
* limited by the available generation at that site, which is defined in
* eq_site_cf and eq_spurclip.
eq_capacity_limit_hybrid(r,h,t)
    $[tmodel(t)
    $Sw_SpurScen]..

* Sum of available generation across reV sites in BA
    sum{x$[x_rb(x,r)$xfeas(x)], AVAIL_SITE(x,h,t)}

    =g=

* is >= the actual generation and operating reserves from all the hybrid resources in that BA
    sum{(i,v)
        $[spur_techs(i)
        $valgen(i,v,r,t)],
        GEN(i,v,r,h,t)
        + sum{ortype$[Sw_OpRes$opres_model(ortype)$reserve_frac(i,ortype)$opres_h(h)],
              OPRES(ortype,i,v,r,h,t)}
    }
;

* ---------------------------------------------------------------------------

eq_capacity_limit_nd(i,v,r,h,t)$[tmodel(t)$valgen(i,v,r,t)$nondispatch(i)]..

*sum of non-dispatchable capacity multiplied by its rated capacity factor,
    + m_cf(i,v,r,h,t) * CAP(i,v,r,t)

    =e=

*must be equal to generation
    GEN(i,v,r,h,t)

*[plus] sum of operating reserves by type
    + sum{ortype$[Sw_OpRes$opres_model(ortype)$reserve_frac(i,ortype)$opres_h(h)],
          OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

eq_curt_gen_balance(r,h,t)$[rb(r)$tmodel(t)]..

*total potential generation
    sum{(i,v)$[valcap(i,v,r,t)$(vre(i) or pvb(i))$(not nondispatch(i))],
         m_cf(i,v,r,h,t) * CAP(i,v,r,t) }

*[minus] curtailed generation
    - CURT(r,h,t)

    =g=

*must exceed realized generation; exclude hybrid PV+Batttery
    sum{(i,v)$[valgen(i,v,r,t)$vre(i)$(not nondispatch(i))], GEN(i,v,r,h,t) }

*[plus] realized PV generation from hybrid PV+Batttery
  + sum{(i,v)$[valgen(i,v,r,t)$pvb(i)$(not nondispatch(i))], GEN_PVB_P(i,v,r,h,t) }$Sw_PVB

*[plus] sum of operating reserves by type; exclude hybrid PV+Batttery because the PV does not provide reserves
    + sum{(ortype,i,v)$[Sw_OpRes$reserve_frac(i,ortype)$opres_h(h)$valgen(i,v,r,t)$vre(i)$(not nondispatch(i))$opres_model(ortype)],
          OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

eq_mingen_lb(r,h,szn,t)$[rb(r)$h_szn(h,szn)$(yeart(t)>=mingen_firstyear)
                        $tmodel(t)$Sw_Mingen]..

*minimum generation level in a season
    MINGEN(r,szn,t)

    =g=

*must be greater than the minimum generation level in each time slice in that season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)], GEN(i,v,r,h,t)  * minloadfrac(r,i,h) }
;

* ---------------------------------------------------------------------------

eq_mingen_ub(r,h,szn,t)$[rb(r)$h_szn(h,szn)$(yeart(t)>=mingen_firstyear)
                        $tmodel(t)$Sw_Mingen]..

*generation in each timeslice in a season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)], GEN(i,v,r,h,t)  }

    =g=

*must be greater than the minimum generation level
    MINGEN(r,szn,t)
;

* ---------------------------------------------------------------------------

*requirement for fleet of a given tech to have a minimum annual capacity factor
eq_min_cf(i,r,t)$[minCF(i,t)$tmodel(t)$valgen_irt(i,r,t)$Sw_MinCF]..

    sum{(v,h)$[valgen(i,v,r,t)], hours(h) * GEN(i,v,r,h,t) }

    =g=

    sum{v$valgen(i,v,r,t), CAP(i,v,r,t) } * sum{h, hours(h) } * minCF(i,t)
;

* ---------------------------------------------------------------------------

* Seasonal energy constraint for dispatchable hydropower when all energy must be used within season (no seasonal energy shifting)
eq_dhyd_dispatch(i,v,r,szn,t)$[tmodel(t)$hydro_d(i)$valgen(i,v,r,t)$(within_seas_frac(i,v,r) = 1)]..

*seasonal hours [times] seasonal capacity factor [times] total hydro capacity [times] seasonal capacity adjustment
    sum{h$[h_szn(h,szn)], avail(i,h) * hours(h) }
    * (CAP(i,v,r,t) + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))],
               INV_ENER_UP(i,v,r,rscbin,tt)$allow_ener_up(i,v,r,rscbin,tt)
             - degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt)$allow_cap_up(i,v,r,rscbin,tt) })
    * cap_hyd_szn_adj(i,szn,r)
    * m_cf_szn(i,v,r,szn,t)

    =g=

*total seasonal generation plus fraction of energy for regulation
    sum{h$[h_szn(h,szn)],
        hours(h)
        * (GEN(i,v,r,h,t)
           + reg_energy_frac * (
               OPRES("reg",i,v,r,h,t)$[Sw_OpRes=1]
               + OPRES("combo",i,v,r,h,t)$[Sw_OpRes=2]
           )$[opres_h(h)]
        )
    }
;

* ---------------------------------------------------------------------------

* Annual energy constraint for dispatchable hydropower when seasonal shifting is allowed
eq_dhyd_dispatch_ann(i,v,r,t)$[tmodel(t)$hydro_d(i)$valgen(i,v,r,t)$(within_seas_frac(i,v,r) < 1)]..

    sum{szn,
* seasonal hours [times] seasonal capacity factor
        sum{h$[h_szn(h,szn)], avail(i,h) * hours(h) }
* [times] total hydro capacity
        * (CAP(i,v,r,t) + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))],
            INV_ENER_UP(i,v,r,rscbin,tt)$allow_ener_up(i,v,r,rscbin,tt)
            - degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt)$allow_cap_up(i,v,r,rscbin,tt) })
* [times] seasonal capacity adjustment
        * cap_hyd_szn_adj(i,szn,r)
        * m_cf_szn(i,v,r,szn,t) }
    =g=

    sum{szn,
*total seasonal generation plus fraction of energy for regulation
        sum{h$[h_szn(h,szn)],
            hours(h)
            * (GEN(i,v,r,h,t)
               + reg_energy_frac * (
                   OPRES("reg",i,v,r,h,t)$[Sw_OpRes=1]
                   + OPRES("combo",i,v,r,h,t)$[Sw_OpRes=2]
               )$[opres_h(h)]
            )
        } 
    }
;

* ---------------------------------------------------------------------------

* Required fraction of energy used within a season for dispatchable hydropower when seasonal shifting is allowed
eq_dhyd_dispatch_szn(i,v,r,szn,t)$[tmodel(t)$hydro_d(i)$valgen(i,v,r,t)$(within_seas_frac(i,v,r) < 1)]..

*total seasonal generation plus fraction of energy for regulation
    sum{h$[h_szn(h,szn)],
        hours(h)
        * (GEN(i,v,r,h,t)
           + reg_energy_frac * (
               OPRES("reg",i,v,r,h,t)$[Sw_OpRes=1]
               + OPRES("combo",i,v,r,h,t)$[Sw_OpRes=2]
           )$[opres_h(h)]
        )
    }

    =g=

*fractional in-season energy requirement
    within_seas_frac(i,v,r) * (
*seasonal hours [times] seasonal capacity factor [times] total hydro capacity [times] seasonal capacity adjustment
        sum{h$[h_szn(h,szn)], avail(i,h) * hours(h) }
        * (CAP(i,v,r,t) + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))],INV_ENER_UP(i,v,r,rscbin,tt)$allow_ener_up(i,v,r,rscbin,tt)
           - degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt)$allow_cap_up(i,v,r,rscbin,tt) })
        * cap_hyd_szn_adj(i,szn,r)
        * (m_cf_szn(i,v,r,szn,t)$(m_cf_szn(i,v,r,szn,t) <= 1) + 1$(m_cf_szn(i,v,r,szn,t) > 1))
    )
;

*===============================
* --- SUPPLY DEMAND BALANCE ---
*===============================

* ---------------------------------------------------------------------------

* The treatment of power flow along DC lines depends on the type of AC/DC converter used.
* LCC DC lines are single point-to-point lines connected to the AC grid on either end, and
* as such are treated like AC lines (with different costs/losses).
* VSC DC lines are part of a multi-terminal DC network; DC power can flow through a node
* without converting to AC and incurring DC/AC/DC losses. Power flow along VSC lines is
* therefore treated separately through the CONVERSION variable and eq_vsc_flow equation.
eq_supply_demand_balance(r,h,t)$[rb(r)$tmodel(t)]..

* generation from all sources, including storage discharge and DR
*  for DR - GEN represents the reduction in load from shifting away
*  from the focal timeslice load to another timeslice - this
*  included both DR_SHIFT and DR_SHED variables amounts
    sum{(i,v)$valgen(i,v,r,t), GEN(i,v,r,h,t) }

* [plus] net AC and LCC DC transmission with imports reduced by losses
    + sum{(trtype,rr)$[routes(rr,r,trtype,t)$notvsc(trtype)],
          (1-tranloss(rr,r,trtype)) * FLOW(rr,r,h,t,trtype) }
    - sum{(trtype,rr)$[routes(r,rr,trtype,t)$notvsc(trtype)],
          FLOW(r,rr,h,t,trtype) }

* [plus] net AC/DC conversion through VSC converter stations
* Note that we only need "AC" in the CONVERSION variable (not LCC, B2B, etc)
* since all it does here is act as a catch-all for "not VSC"
    + (CONVERSION(r,h,"VSC","AC",t) * converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]
    - (CONVERSION(r,h,"AC","VSC",t) / converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]

* [minus] storage charging; not Hybrid PV+Battery
    - sum{(i,v)$[valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))], STORAGE_IN(i,v,r,h,t) }

* [minus] energy into storage for hybrid pv+battery from grid
    - sum{(i,v)$[valcap(i,v,r,t)$pvb(i)], STORAGE_IN_PVB_G(i,v,r,h,t) }$Sw_PVB

* [minus] load shifting from demand response
    - sum{[i,v,hh]$[valgen(i,v,r,t)$dr1(i)$allowed_shifts(i,h,hh)],
                     DR_SHIFT(i,v,r,h,hh,t) / hours(h) / storage_eff(i,t) }$Sw_DR

    + net_trade_can(r,h,t)$[Sw_Canada=2]

* [plus] dropped load ONLY if before Sw_StartMarkets
    + DROPPED(r,h,t)$(yeart(t)<Sw_StartMarkets)

    =e=

* must equal demand
    LOAD(r,h,t)
;

* ---------------------------------------------------------------------------

eq_vsc_flow(r,h,t)
    $[rb(r)
    $tmodel(t)
    $Sw_VSC]..

* [plus] net VSC DC transmission with imports reduced by losses
    + sum{rr$routes(rr,r,"VSC",t), (1-tranloss(rr,r,"VSC")) * FLOW(rr,r,h,t,"VSC") }
    - sum{rr$routes(r,rr,"VSC",t), FLOW(r,rr,h,t,"VSC") }

* [plus] net VSC AC/DC conversion
    + (CONVERSION(r,h,"AC","VSC",t) * converter_efficiency_vsc)$val_converter(r,t)
    - (CONVERSION(r,h,"VSC","AC",t) / converter_efficiency_vsc)$val_converter(r,t)

    =e=

* no direct consumption of VSC
    0
;

* ---------------------------------------------------------------------------

*=======================================
* --- MINIMUM LOADING CONSTRAINTS ---
*=======================================

* ---------------------------------------------------------------------------

* the generation in any hour cannot exceed the minloadfrac times the
* supply from other hours within that hour correlation set (via hour_szn_group(h,hh))
* note that hour_szn_group does not include the same hour (i.e. h!=hh)
eq_minloading(i,v,r,h,hh,t)$[valgen(i,v,r,t)$minloadfrac(r,i,hh)
                            $(yeart(t)>=model_builds_start_yr)
                            $tmodel(t)$hour_szn_group(h,hh)$Sw_MinLoading]..

    GEN(i,v,r,h,t)

    =g=

    GEN(i,v,r,hh,t) * minloadfrac(r,i,hh)
;

*=======================================
* --- OPERATING RESERVE CONSTRAINTS ---
*=======================================

* ---------------------------------------------------------------------------

*generation must occur at some point during the szn (i.e., day)
*in order to procure operating reserves from that resource
*ORPRES for storage is limited by the storage capacity per the constraint "eq_storage_capacity"
eq_ORCap_large_res_frac(ortype,i,v,r,h,t)
    $[tmodel(t)$valgen(i,v,r,t)$Sw_OpRes$opres_model(ortype)$opres_h(h)
    $(reserve_frac(i,ortype)>0.5)$(not storage_standalone(i))$(not hyd_add_pump(i))]..

*the reserve_frac times...
    reserve_frac(i,ortype) * (
* the amount of committed capacity available for a season is assumed to be the amount
* of generation from the timeslice that has the highest demand
         sum{(szn,hh)$[h_szn(h,szn)$maxload_szn(r,hh,t,szn)],
              GEN(i,v,r,hh,t) })

    =g=

*note the reserve_frac applies to each opres by type
    OPRES(ortype,i,v,r,h,t)
;

* ---------------------------------------------------------------------------

*for plants with reserve_frac <= 0.5 (but nonzero), generation must occur during the timeslice
*in which reserves are provided
eq_ORCap_small_res_frac(ortype,i,v,r,h,t)
    $[tmodel(t)$valgen(i,v,r,t)$Sw_OpRes$opres_model(ortype)$opres_h(h)
    $(reserve_frac(i,ortype)<=0.5)$reserve_frac(i,ortype)]..

*generation
    GEN(i,v,r,h,t)

    =g=

*must be greater than the operating reserves procured
    OPRES(ortype,i,v,r,h,t)
;

* ---------------------------------------------------------------------------

*operating reserves must meet the operating reserves requirement (by ortype)
eq_OpRes_requirement(ortype,r,h,t)
    $[rb(r)$tmodel(t)$Sw_OpRes$opres_model(ortype)$opres_h(h)]..

*operating reserves from technologies that can produce them (i.e. those w/ramp rates)

    sum{(i,v)$[valgen(i,v,r,t)$reserve_frac(i,ortype)],
         OPRES(ortype,i,v,r,h,t) }

*[plus] net transmission of operating reserves (while including losses for imports)
    + sum{rr$opres_routes(rr,r,t), (1 - tranloss(rr,r,"AC")) * OPRES_FLOW(ortype,rr,r,h,t) }
    - sum{rr$opres_routes(r,rr,t), OPRES_FLOW(ortype,r,rr,h,t) }

* [plus] dropped load (operating reserves) ONLY if before Sw_StartMarkets
    + DROPPED(r,h,t)$(yeart(t)<Sw_StartMarkets)

    =g=

*must meet the demand for or type
*first portion is from load
    orperc(ortype,"or_load") * LOAD(r,h,t)

*next portion is from the wind generation
    + orperc(ortype,"or_wind") * sum{(i,v)$[wind(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) }

*final portion is from upv, dupv, and distpv capacity
*note that pv capacity is held at the balancing area
*include the hybrid PV+battery PV capacity here
    + orperc(ortype,"or_pv") * sum{(i,v)$[(pv(i) or pvb(i))$valcap(i,v,r,t)],
         CAP(i,v,r,t) }$dayhours(h)
;

* ---------------------------------------------------------------------------

*=================================
* --- PLANNING RESERVE MARGIN ---
*=================================

* ---------------------------------------------------------------------------

*trade of planning reserve margin capacity cannot exceed the transmission line's available capacity
eq_PRMTRADELimit(r,rr,trtype,szn,t)
    $[tmodel(t)
    $routes(r,rr,trtype,t)
    $routes_prm(r,rr)
    $Sw_PRM_CapCredit]..

*[plus] transmission capacity
    + CAPTRAN_PRM(r,rr,trtype,t) * sum{h$h_szn_prm(h,szn), (1 + trans_cap_delta(h,t)) }

    =g=

*[plus] firm capacity traded between regions
    + PRMTRADE(r,rr,trtype,szn,t)
;

* ---------------------------------------------------------------------------

eq_PRMTRADE_VSC(r,szn,t)
    $[rb(r)
    $tmodel(t)
    $Sw_PRM_CapCredit
    $Sw_VSC]..

*[plus] net VSC DC imports - exports of firm capacity with imports reduced by losses
    + sum{rr$[routes(rr,r,"VSC",t)$routes_prm(rr,r)], (1-tranloss(rr,r,"VSC")) * PRMTRADE(rr,r,"VSC",szn,t) }
    - sum{rr$[routes(r,rr,"VSC",t)$routes_prm(r,rr)], PRMTRADE(r,rr,"VSC",szn,t) }

* [plus] net VSC AC/DC conversion
    + (CONVERSION_PRM(r,szn,"AC","VSC",t) * converter_efficiency_vsc)$val_converter(r,t)
    - (CONVERSION_PRM(r,szn,"VSC","AC",t) / converter_efficiency_vsc)$val_converter(r,t)

    =e=

* no direct contribution of VSC
    0
;

* ---------------------------------------------------------------------------

* binned capacity for capacity credit must be the same as capacity
* (except for CSP, which is treated like VRE for capacity credit)
eq_cap_sdbin_balance(i,v,r,szn,t)
    $[tmodel(t)$valcap(i,v,r,t)$storage(i)$(not csp(i))]..

*total capacity in each region
    bcr(i) * CAP(i,v,r,t)

    =e=

*sum of all binned capacity within each region
    sum{sdbin, CAP_SDBIN(i,v,r,szn,sdbin,t) }
;

* ---------------------------------------------------------------------------

*binned capacity cannot exceed sdbin size
eq_sdbin_limit(ccreg,szn,sdbin,t)$tmodel(t)..

*sdbin size from CC script
    sdbin_size(ccreg,szn,sdbin,t)

    =g=

*standalone storage capacity in each sdbin adjusted by the appropriate CC value
    sum{(i,v,r)$[r_ccreg(r,ccreg)$valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))],
        CAP_SDBIN(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin)
        }

*[plus] hybrid storage capacity in each sdbin adjusted by the appropriate CC value and the hybrid derate factor
    + sum{(i,v,r)$[r_ccreg(r,ccreg)
                 $valcap(i,v,r,t)$storage_hybrid(i)$(not csp(i))],
          CAP_SDBIN(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin) * hybrid_cc_derate(i,r,szn,sdbin,t)
          }
;

* ---------------------------------------------------------------------------

eq_reserve_margin(r,szn,t)$[rb(r)$tmodel(t)$(yeart(t)>=model_builds_start_yr)$Sw_PRM_CapCredit]..

* forced_retire is used here because forced_retire capacity is removed from valgen 
* but not valcap. It remains in valcap to allow for upgrades, but if it is not upgraged
* it should not be allowed to provide capacity to meet the reserve margin constraint.
* Because it can provide no services, it will either upgrade or retire.

*[plus] sum of all non-rsc and non-storage capacity
    + sum{(i,v)$[valcap(i,v,r,t)$(not vre(i))$(not hydro(i))$(not storage(i))$(not dr(i))$(not consume(i))$(not forced_retire(i,r,t))],
          CAP(i,v,r,t)
          * (1 + seas_cap_frac_delta(i,v,r,szn,t))
         }

*[plus] firm capacity from existing VRE or CSP
*only used in sequential solve case (otherwise cc_old = 0)
    + sum{i$[(vre(i) or csp(i) or pvb(i))$(not forced_retire(i,r,t))],
          cc_old(i,r,szn,t)
         }

*[plus] marginal capacity credit of VRE and csp times new investment
*only used in sequential solve case (otherwise m_cc_mar = 0)
*Note: new distpv is included with cc_old
    + sum{(i,v)$[(vre(i) or csp(i) or pvb(i))$valinv(i,v,r,t)$(not forced_retire(i,r,t))],
          m_cc_mar(i,r,szn,t) * (INV(i,v,r,t) + INV_REFURB(i,v,r,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] firm capacity contribution from all binned storage capacity
*battery, pumped-hydro, and CAES
*excludes hydro upgraded to add pumps
    + sum{(i,v,sdbin)$[(storage_standalone(i) or hyd_add_pump(i))$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          cc_storage(i,sdbin) * CAP_SDBIN(i,v,r,szn,sdbin,t)
         }
*hybrid PV+battery
    + sum{(i,v,sdbin)$[storage_hybrid(i)$(not csp(i))$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          cc_storage(i,sdbin) * hybrid_cc_derate(i,r,szn,sdbin,t) * CAP_SDBIN(i,v,r,szn,sdbin,t)
         }
*[plus] firm capacity contribution from all DR
    + sum{(i,v)$[dr(i)$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          m_cc_dr(i,r,szn,t) * CAP(i,v,r,t)
         }

*[plus] average capacity credit times capacity of VRE and storage
*used in rolling window and full intertemporal solve (otherwise cc_int = 0)
    + sum{(i,v)$[(vre(i) or storage(i))$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          cc_int(i,v,r,szn,t) * CAP(i,v,r,t)
         }

*[plus] excess capacity credit
*used in rolling window and full intertemporal solve when using marginals for cc_int (otherwise cc_excess = 0)
    + sum{i$[(vre(i) or storage(i))$(not forced_retire(i,r,t))],
          cc_excess(i,r,szn,t)
         }

*[plus] firm capacity of non-dispatchable hydro
* nb: hydro_nd generation does not fluctuate
* within a seasons set of hours
    + sum{(i,v,h)$[hydro_nd(i)$valgen(i,v,r,t)$h_szn_prm(h,szn)],
          GEN(i,v,r,h,t)
         }

*[plus] dispatchable hydro firm capacity
* include hydro upgraded to add pumps
    + sum{(i,v)$[(hydro_d(i) or hyd_add_pump(i))$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          CAP(i,v,r,t) * cap_hyd_szn_adj(i,szn,r) * (1 + hydro_capcredit_delta(i,t))
         }

*[plus] imports of firm capacity through AC and LCC DC lines
    + sum{(rr,trtype)$[routes(rr,r,trtype,t)$routes_prm(rr,r)$notvsc(trtype)],
          (1 - tranloss(rr,r,trtype)) * PRMTRADE(rr,r,trtype,szn,t)
         }

*[minus] exports of firm capacity through AC and LCC DC lines
    - sum{(rr,trtype)$[routes(r,rr,trtype,t)$routes_prm(r,rr)$notvsc(trtype)],
          PRMTRADE(r,rr,trtype,szn,t)
         }

*[plus] net AC/DC conversion of firm capacity through VSC converters
    + (CONVERSION_PRM(r,szn,"VSC","AC",t) * converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]
    - (CONVERSION_PRM(r,szn,"AC","VSC",t) / converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]

    =g=

*[plus] the peak demand times the planning reserve margin
    + (
        peakdem_static_szn(r,szn,t)

        + PEAK_FLEX(r,szn,t)$Sw_EFS_flex

*[plus] only steam methane reforming technologies are assumed to increase peak demand
* contribution to peak demand based on weighted-average across timeslices in each season
     + (sum{(p,i,v,h)$[smr(i)$valcap(i,v,r,t)$h_szn(h,szn)
                     $(sameas(p,"H2"))$i_p(i,p)$(not sameas(i,"dac_gas"))$hours(h)],
               PRODUCE(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) * hours(h)}
        / sum{h$h_szn(h,szn), hours(h)}
     )$Sw_Prod

      ) * (1 + prm(r,t))
;

* ---------------------------------------------------------------------------

*================================
* --- TRANSMISSION CAPACITY  ---
*================================

* ---------------------------------------------------------------------------

*capacity transmission is equal to the exogenously-specified level of transmission
*plus the investment in transmission capacity
eq_CAPTRAN_ENERGY(r,rr,trtype,t)
    $[routes(r,rr,trtype,t)
    $tmodel(t)]..

    CAPTRAN_ENERGY(r,rr,trtype,t)

    =e=

* [plus] initial transmission capacity, which is defined separately for (r,rr) and (rr,r)
    + trancap_init_energy(r,rr,trtype)

* Unlike transmission capacity, transmission *investments* are only defined from the lower-numbered
* region to the higher-numbered region. But we add the investment to both directions.
* So if trancap_init_energy(r1,r2,AC) = 1 MW, trancap_init_energy(r2,r1,AC) = 2 MW, and
* INVTRAN(r1,r2,AC) = 0.5 MW, we get CAPTRAN_ENERGY(r1,r2,AC) = 1.5 MW and
* CAPTRAN_ENERGY(r2,r1,AC) = 2.5 MW.
* Because routes_inv and invtran_exog are only defined from the lower-numbered to the higher
* -numbered region, we can sum over both INVTRAN(r,rr) and INVTRAN(rr,r) without double-counting.

* [plus] "certain" transmission investments
    + sum{(tt)$[(yeart(tt) <= yeart(t))$routes(r,rr,trtype,tt)],
          invtran_exog(r,rr,trtype,tt) + invtran_exog(rr,r,trtype,tt) }

* [plus] all previous year's investments
    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))$routes(r,rr,trtype,tt)],
             INVTRAN(r,rr,trtype,tt)$routes_inv(r,rr,trtype,tt)
             + INVTRAN(rr,r,trtype,tt)$routes_inv(rr,r,trtype,tt) }
;

* ---------------------------------------------------------------------------

*capacity transmission is equal to the exogenously-specified level of transmission
*plus the investment in transmission capacity
eq_CAPTRAN_PRM(r,rr,trtype,t)
    $[routes(r,rr,trtype,t)
    $routes_prm(r,rr)
    $tmodel(t)]..

    CAPTRAN_PRM(r,rr,trtype,t)

    =e=

* [plus] initial transmission capacity, which is defined separately for (r,rr) and (rr,r)
    + trancap_init_prm(r,rr,trtype)

* See more detailed comments on the handling of INVTRAN vs CAPTRAN in eq_CAPTRAN_ENERGY.
* [plus] "certain" transmission investments
    + sum{(tt)$[(yeart(tt) <= yeart(t))$routes(r,rr,trtype,tt)],
          (invtran_exog(r,rr,trtype,tt) + invtran_exog(rr,r,trtype,tt))
          * (1 - Sw_TransInvPRMderate) }

* [plus] all previous year's investments
    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))$routes(r,rr,trtype,tt)],
          (INVTRAN(r,rr,trtype,tt)$routes_inv(r,rr,trtype,tt)
           + INVTRAN(rr,r,trtype,tt)$routes_inv(rr,r,trtype,tt))
          * (1 - Sw_TransInvPRMderate)
    }
;

* ---------------------------------------------------------------------------

eq_prescribed_transmission(r,rr,trtype,t)
    $[routes_inv(r,rr,trtype,t)$tmodel(t)$(yeart(t)<firstyear_trans_nearterm)]..

*all available transmission capacity expansion that is 'possible'
*note we allow for possible future transmission to accumulate
*hence the sum over all previous years
    sum{tt$[(tmodel(tt) or tfix(tt))$(yeart(tt)<=yeart(t))],
         trancap_fut(r,rr,"possible",trtype,tt) + trancap_fut(rr,r,"possible",trtype,tt) }

    =g=

*must exceed the bi-directional investment along that corridor
    sum{tt$[(tmodel(tt) or tfix(tt))$(yeart(tt)<=yeart(t))$routes(r,rr,trtype,tt)],
        INVTRAN(r,rr,trtype,tt)$routes_inv(r,rr,trtype,tt)
        + INVTRAN(rr,r,trtype,tt)$routes_inv(rr,r,trtype,tt) }
;

* ---------------------------------------------------------------------------

* New point-of-interconnection (POI) intra-zone transmission capacity must be
* added for new generation capacity
eq_POI_cap(r,t)
    $[rb(r)
    $tmodel(t)
    $Sw_TransIntraCost]..

* The sum of POI capacity...
    poi_cap_init(r)
    + sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))], INV_POI(r,tt) }

    =g=

* must be greater than the sum of all generation capacity [AC] without explicit spur lines...
    sum{(i,v)$[valcap(i,v,r,t)$(not spur_techs(i))], CAP(i,v,r,t) / ilr(i) }
* and spur-line capacity if explicitly tracked (use total capacity, not just new investments,
* to make sure we account for the existing spur line capacity already included in poi_cap_init)...
    + sum{x$[xfeas(x)$x_rb(x,r)$Sw_SpurScen], CAP_SPUR(x,t) }
* and AC/DC converter capacity for VSC...
    + CAP_CONVERTER(r,t)
* and LCC
    + sum{(rr,tt)$[routes(r,rr,"LCC",t)$(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))],
          INVTRAN(r,rr,"LCC",tt)$routes_inv(r,rr,"LCC",tt)
          + INVTRAN(rr,r,"LCC",tt)$routes_inv(rr,r,"LCC",tt) }
;

* ---------------------------------------------------------------------------

* flows cannot exceed the total transmission capacity
eq_transmission_limit(r,rr,h,t,trtype)$[tmodel(t)$routes(r,rr,trtype,t)]..

* Representative periods use the energy (n-0) capacity.
    (CAPTRAN_ENERGY(r,rr,trtype,t) * (1 + trans_cap_delta(h,t)))$h_rep(h)
* Stress periods use the PRM (n-1) capacity.
* Because these periods are assumed to be mutually exclusive, each timeslice should only
* have a single capacity applied.
    + (CAPTRAN_PRM(r,rr,trtype,t) * (1 + trans_cap_delta(h,t)))$[h_stress(h)$routes_prm(r,rr)]

    =g=

*[plus] energy flows
    + FLOW(r,rr,h,t,trtype)


*[plus] operating reserve flows (operating reserves can only be transferred across AC lines)
    + sum{ortype$[Sw_OpRes$opres_h(h)$aclike(trtype)$opres_routes(r,rr,t)],
          OPRES_FLOW(ortype,r,rr,h,t) * opres_mult }
;

* ---------------------------------------------------------------------------

*capacity transmission is equal to the exogenously-specified level of transmission
*plus the investment in transmission capacity
eq_CAPTRAN_GRP(transgrp,transgrpp,t)
    $[tmodel(t)
    $Sw_TransGroupContraint
    $sum{(r,rr), routes_transgroup(transgrp,transgrpp,r,rr) }]..

    CAPTRAN_GRP(transgrp,transgrpp,t)

    =e=

* [plus] initial transmission capacity, which is defined separately for each direction
    + trancap_init_transgroup(transgrp,transgrpp,"AC")

* See more detailed comments on the handling of INVTRAN vs CAPTRAN in eq_CAPTRAN_ENERGY.
* [plus] "certain" transmission investments
    + sum{(r,rr,tt)$[(yeart(tt) <= yeart(t))
                   $routes(r,rr,"AC",tt)
                   $routes_transgroup(transgrp,transgrpp,r,rr)],
          (invtran_exog(r,rr,"AC",tt) + invtran_exog(rr,r,"AC",tt))
          * (1 - Sw_TransGroupDerate) }

* [plus] all previous year's investments
    + sum{(r,rr,tt)$[(yeart(tt) <= yeart(t))
                   $(tmodel(tt) or tfix(tt))
                   $routes(r,rr,"AC",tt)
                   $routes_transgroup(transgrp,transgrpp,r,rr)],
          (INVTRAN(r,rr,"AC",tt)$routes_inv(r,rr,"AC",tt)
           + INVTRAN(rr,r,"AC",tt)$routes_inv(rr,r,"AC",tt))
          * (1 - Sw_TransGroupDerate)
    }
;

* ---------------------------------------------------------------------------

eq_transgrp_limit_energy(transgrp,transgrpp,h,t)
    $[tmodel(t)
    $Sw_TransGroupContraint
    $sum{(r,rr), routes_transgroup(transgrp,transgrpp,r,rr) }]..

    CAPTRAN_GRP(transgrp,transgrpp,t) * (1 + trans_cap_delta(h,t))

    =g=

    sum{(r,rr)$routes_transgroup(transgrp,transgrpp,r,rr),
        FLOW(r,rr,h,t,"AC") }
;

* ---------------------------------------------------------------------------

eq_transgrp_limit_prm(transgrp,transgrpp,szn,t)
    $[tmodel(t)
    $Sw_TransGroupContraint
    $sum{(r,rr), routes_transgroup(transgrp,transgrpp,r,rr) }]..

    CAPTRAN_GRP(transgrp,transgrpp,t)
    * sum{h$h_szn_prm(h,szn), (1 + trans_cap_delta(h,t)) }

    =g=

    sum{(r,rr)$routes_transgroup(transgrp,transgrpp,r,rr),
        PRMTRADE(r,rr,"AC",szn,t) }
;

* ---------------------------------------------------------------------------

* CAP_CONVERTER accumulates INV_CONVERTER from years <= t
eq_CAP_CONVERTER(r,t)
    $[rb(r)
    $tmodel(t)
    $val_converter(r,t)
    $Sw_VSC]..

    CAP_CONVERTER(r,t)

    =e=

    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))],
          INV_CONVERTER(r,tt) }
;

* ---------------------------------------------------------------------------

* CAP_SPUR accumulates INV_SPUR from years <= t
eq_CAP_SPUR(x,t)
    $[Sw_SpurScen
    $tmodel(t)]..
    CAP_SPUR(x,t)

    =e=

    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))],
          INV_SPUR(x,tt) }
;

* ---------------------------------------------------------------------------

* AC/DC conversion cannot exceed the converter capacity
eq_CONVERSION_limit_energy(r,h,t)
    $[rb(r)
    $tmodel(t)
    $val_converter(r,t)
    $Sw_VSC]..

    CAP_CONVERTER(r,t)

    =g=

    CONVERSION(r,h,"AC","VSC",t) + CONVERSION(r,h,"VSC","AC",t)
;

* ---------------------------------------------------------------------------

* AC/DC PRM conversion cannot exceed the converter capacity
eq_CONVERSION_limit_prm(r,szn,t)
    $[rb(r)
    $tmodel(t)
    $val_converter(r,t)
    $Sw_VSC]..

    CAP_CONVERTER(r,t)

    =g=

    CONVERSION_PRM(r,szn,"AC","VSC",t) + CONVERSION_PRM(r,szn,"VSC","AC",t)
;

* ---------------------------------------------------------------------------

* Limit the annual transmission investment to trans_inv_max
eq_transmission_investment_max(t)
    $[tmodel(t)
    $trans_inv_max(t)
    $Sw_TransInvMaxTypes]..

* Sw_TransInvMax [TWmile/year] * [1e6 MW / 1 TW] * [year/solvestep]
    trans_inv_max(t) * 1e6 * (yeart(t) - sum{tt$[tprev(t,tt)], yeart(tt) })

    =g=

* Interzonal transmission
    + sum{(r,rr,trtype)$routes_inv(r,rr,trtype,t),
          INVTRAN(r,rr,trtype,t) * distance(r,rr,trtype) }
* Spur lines + network reinforcement
    + sum{(i,v,r,rscbin)
          $[((Sw_TransInvMaxTypes=2) or (Sw_TransInvMaxTypes=3))
          $valinv(i,v,r,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)],
          INV_RSC(i,v,r,rscbin,t) * (
              distance_reinforcement(i,r,rscbin))
              + distance_spur(i,r,rscbin)$(Sw_TransInvMaxTypes=3)
    }
;

* ---------------------------------------------------------------------------

* Limit the total transmission capacity of each interface trtype to captran_max [MW]
eq_CAPTRAN_max(r,rr,trtype,t)
    $[tmodel(t)$Sw_TransCapMaxEachType
    $routes(r,rr,trtype,t)$trtypemax(trtype)]..

    Sw_TransCapMaxEachType * 1000

    =g=

    CAPTRAN_ENERGY(r,rr,trtype,t)
;

* ---------------------------------------------------------------------------

* Limit the total transmission capacity of each interface to captran_max,
* summed over all transmission types [MW]
eq_CAPTRAN_max_total(r,rr,t)
    $[tmodel(t)$Sw_TransCapMaxAllTypes
    $sum{trtype$trtypemax(trtype), routes(r,rr,trtype,t) }]..

    Sw_TransCapMaxAllTypes * 1000

    =g=

    sum{trtype$trtypemax(trtype), CAPTRAN_ENERGY(r,rr,trtype,t) }
;

* ---------------------------------------------------------------------------

* Limit the total VSC AC/DC converter capacity in each BA to captran_max
eq_converter_max(r,t)
    $[rb(r)
    $tmodel(t)
    $val_converter(r,t)
    $Sw_VSC
    $Sw_VSC_ConverterMax]..

    Sw_VSC_ConverterMax

    =g=

    CAP_CONVERTER(r,t)
;

* ---------------------------------------------------------------------------

*=========================
* --- EMISSION POLICIES ---
*=========================

* ---------------------------------------------------------------------------

eq_emit_accounting(e,r,t)$[rb(r)$tmodel(t)]..

    EMIT(e,r,t)

    =e=

    sum{(i,v,h)$[valgen(i,v,r,t)],
        hours(h) * emit_rate(e,i,v,r,t)
        * (GEN(i,v,r,h,t)
           + CCSFLEX_POW(i,v,r,h,t)$[ccsflex(i)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)])
       } / emit_scale(e)

* Plus emissions produced via production activities (SMR, SMR-CCS, DAC)
* The "production" of negative CO2 emissions via DAC is also included here
    + sum{(p,i,v,h)$[valcap(i,v,r,t)$i_p(i,p)],
          hours(h) * prod_emit_rate(e,i,t)
          * PRODUCE(p,i,v,r,h,t)
         } / emit_scale(e)

*[minus] co2 reduce from flexible CCS capture
*capture = capture per energy used by the ccs system * CCS energy

* Flexible CCS - bypass
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_byp(i)], ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POW(i,v,r,h,t) } / emit_scale(e)) $[sameas(e,"co2")]$Sw_CCSFLEX_BYP

* Flexible CCS - storage
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_sto(i)], ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POWREQ(i,v,r,h,t) } / emit_scale(e)) $[sameas(e,"co2")]$Sw_CCSFLEX_STO
;

* ---------------------------------------------------------------------------

eq_RGGI_cap(t)$[tmodel(t)$(yeart(t)>=RGGI_start_yr)$Sw_RGGI]..

    RGGI_cap(t) / emit_scale("CO2")

    =g=

    sum{r$RGGI_r(r), EMIT("CO2",r,t) }
;

* ---------------------------------------------------------------------------

eq_state_cap(st,t)
    $[tmodel(t)
    $(yeart(t)>=state_cap_start_yr)
    $sum{tt, state_cap(st,tt) }
    $Sw_StateCap]..

    state_cap(st,t) / emit_scale("CO2")

    =g=

    sum{r$r_st(r,st), EMIT("CO2",r,t) }

* Import emissions intensity is taken from the previous solve year.
* Here the receiving regions (r) are the cap regions and the sending
* regions (rr) are those that have connection with cap regions.
    + sum{(h,r,rr,trtype)
          $[r_st(r,st)$(not r_st(rr,st))$routes(rr,r,trtype,t)
* If there is a national zero-carbon cap in the present year,
* set emissions intensity of imports to zero.
          $(not (Sw_AnnualCap and not emit_cap("CO2",t)))],
          hours(h) * FLOW(rr,r,h,t,trtype)
          * sum{tt$tprev(t,tt), co2_emit_rate_r(rr,tt) }
    } / emit_scale("CO2")
;

* ---------------------------------------------------------------------------

* traded emissions among states in each trading group need
* to be less than the sum of all the state caps within that trading group
eq_CSAPR_Budget(csapr_group,t)$[Sw_CSAPR$tmodel(t)$(yeart(t)>=csapr_startyr)]..

*the accumulation of states csapr cap for the budget category
    sum{st$[stfeas(st)$csapr_group_st(csapr_group,st)], csapr_cap(st,"budget",t) } / emit_scale("NOX")

    =g=

*must exceed the summed-over-state hourly-weighted nox emissions by csapr group
    sum{st$csapr_group_st(csapr_group,st),
      sum{(i,v,h,r)$[r_st(r,st)$valgen(i,v,r,t)],
         h_weight_csapr(h) * hours(h) * emit_rate("NOX",i,v,r,t) * GEN(i,v,r,h,t)  / emit_scale("NOX")
       }
      }
;

* ---------------------------------------------------------------------------

* along with the cap on trading groups, each state has
* a maximum amount of NOX emissions during ozone season
eq_CSAPR_Assurance(st,t)$[stfeas(st)$(yeart(t)>=csapr_startyr)
                         $csapr_cap(st,"Assurance",t)$tmodel(t)]..

*the state level assurance cap
    csapr_cap(st,"assurance",t) / emit_scale("NOX")

    =g=

*must exceed the csapr-hourly-weighted nox emissions by state
    sum{(i,v,h,r)$[r_st(r,st)$valgen(i,v,r,t)],
      h_weight_csapr(h) * hours(h) * emit_rate("NOX",i,v,r,t) * GEN(i,v,r,h,t) / emit_scale("NOX")
    }
;

* ---------------------------------------------------------------------------

eq_emit_rate_limit(e,r,t)$[(yeart(t)>=CarbPolicyStartyear)$emit_rate_con(e,r,t)
                          $tmodel(t)]..

    emit_rate_limit(e,r,t) * (
         sum{(i,v,h)$[valgen(i,v,r,t)],  hours(h) * GEN(i,v,r,h,t) }
    ) / emit_scale(e)

    =g=

    EMIT(e,r,t)
;

* ---------------------------------------------------------------------------

eq_annual_cap(e,t)$[sum{tt, emit_cap(e,tt) }$tmodel(t)$sameas(e,"CO2")$Sw_AnnualCap]..

*exogenous cap
    emit_cap(e,t) / emit_scale(e)

    =g=

*must exceed annual endogenous emissions
* Direct CO2 emissions
    sum{r$rb(r), EMIT(e,r,t) }
* Methane emissions * global warming potential
* [ton CH4] * [ton CO2 / ton CH4] * [emit scale CH4 / cmit scale CO2]
    + sum{r$[rb(r)$Sw_AnnualCapCO2e],
          EMIT("CH4",r,t) * Sw_MethaneGWP * emit_scale("CH4") / emit_scale("CO2") }
;

* ---------------------------------------------------------------------------

eq_bankborrowcap(e)$[Sw_BankBorrowCap$sum{t, emit_cap(e,t) }]..

*weighted exogenous emissions
    sum{t$[tmodel(t)$emit_cap(e,t)],
        yearweight(t) * emit_cap(e,t) } / emit_scale(e)

    =g=

* must exceed weighted endogenous emissions
    sum{(r,t)$[rb(r)$tmodel(t)$emit_cap(e,t)],
        yearweight(t) * EMIT(e,r,t) }
;

* ---------------------------------------------------------------------------

eq_cdr_cap(t)
    $[tmodel(t)
    $Sw_AnnualCap
    $Sw_NoFossilOffsetCDR]..

*** CO2 emissions from fossil CCS...
    + sum{(i,v,r,h)$[valgen(i,v,r,t)$ccs(i)$(not beccs(i))],
        hours(h) * emit_rate("CO2",i,v,r,t) * GEN(i,v,r,h,t) / emit_scale("CO2") }

*** ...and methane leakage from fossil CCS (if included in national policy)...
* Methane emissions * global warming potential
* [ton CH4] * [ton CO2 / ton CH4] * [emit scale CH4 / cmit scale CO2]
    + sum{(i,v,r,h)$[valgen(i,v,r,t)$ccs(i)$(not beccs(i))$Sw_AnnualCapCO2e],
        hours(h) * emit_rate("CH4",i,v,r,t) * GEN(i,v,r,h,t) * Sw_MethaneGWP / emit_scale("CO2") }

    =g=

*** ...must be greater than emissions offset by CDR (negative emissions so negative signs here)
** DAC
    - sum{(p,i,v,r,h)$[valcap(i,v,r,t)$i_p(i,p)$dac(i)$sameas(p,"DAC")],
          hours(h) * prod_emit_rate("CO2",i,t) * PRODUCE(p,i,v,r,h,t) / emit_scale("CO2") }
** BECCS
    - sum{(i,v,r,h)$[valgen(i,v,r,t)$beccs(i)],
        hours(h) * emit_rate("CO2",i,v,r,t) * GEN(i,v,r,h,t) / emit_scale("CO2") }
;

*==========================
* --- RPS CONSTRAINTS ---
*==========================

* ---------------------------------------------------------------------------

eq_REC_Generation(RPSCat,i,st,t)$[stfeas(st)$(not tfirst(t))$tmodel(t)
                                 $Sw_StateRPS$(yeart(t)>=RPS_StartYear)
                                 $(not sameas(RPSCat,"RPS_Bundled"))
                                 $(not sameas(RPSCat,"CES_Bundled"))
                                 $RecTech(RPSCat,i,st,t)]..

*RECS are computed as the total annual generation from a technology
*hydro is the only technology adjusted by RPSTechMult
*because GEN from pvb(i) includes grid charging, subtract out its grid charging
    + sum{(v,r,h)$[valgen(i,v,r,t)$r_st(r,st)],
          RPSTechMult(RPSCat,i,st) * hours(h)
          * (GEN(i,v,r,h,t) - (STORAGE_IN_PVB_G(i,v,r,h,t) * storage_eff_pvb_g(i,t))$[pvb(i)$Sw_PVB] )
         }

     =g=

* Generation must be greater than RECS sent to all states that can trade
    + sum{ast$[RecMap(i,RPSCat,st,ast,t)$(stfeas(ast) or sameas(ast,"voluntary"))],
          RECS(RPSCat,i,st,ast,t) }
* RPS_Bundled RECS and RPS_All RECS can meet the same requirement
* therefore lumping them together to avoid double-counting
    + sum{ast$[RecMap(i,"RPS_Bundled",st,ast,t)$stfeas(ast)],
          RECS("RPS_Bundled",i,st,ast,t) }$[sameas(RPSCat,"RPS_All")]

*same logic as bundled RPS RECS is applied to the bundled CES RECS
    + sum{ast$[RecMap(i,"CES_Bundled",st,ast,t)$stfeas(ast)],
          RECS("CES_Bundled",i,st,ast,t) }$[sameas(RPSCat,"CES")]
;

* ---------------------------------------------------------------------------

* note that the bundled rpscat can be included
* to comply with the RPS_All categeory
* but it is not in itself explicit requirement
eq_REC_Requirement(RPSCat,st,t)$[RecPerc(RPSCat,st,t)$(not tfirst(t))
                                $tmodel(t)$Sw_StateRPS$(yeart(t)>=RPS_StartYear)
                                $(stfeas(st) or sameas(st,"voluntary"))
                                $(not sameas(RPSCat,"RPS_Bundled"))
                                $(not sameas(RPSCat,"CES_Bundled"))]..

* RECs owned (i.e. imported and generated/used in state)
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)],
         RECS(RPSCat,i,ast,st,t) }

* bundled RECS can also be used to meet the RPS_All requirements
    + sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(ast,st))],
         RECS("RPS_Bundled",i,ast,st,t) }$[sameas(RPSCat,"RPS_All")]

* bundled CES credits can also be used to meet the CES requirements
    + sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(ast,st))],
         RECS("CES_Bundled",i,ast,st,t) }$[sameas(RPSCat,"CES")]

* ACP credits can also be purchased
    + ACP_PURCHASES(rpscat,st,t)$(not acp_disallowed(st,RPSCat))

* Exports to Canada are assumed to be clean, and therefore consume CES credits
    - sum{(r,h)$[rb(r)$r_st(r,st)], can_exports_h(r,h,t) * hours(h) }$[(Sw_Canada=1)$sameas(RPSCat,"CES")]

    =g=

* note here we do not pre-define the rec requirement since load_exog(r,h,t)
* changes when sent to/from the demand side
    RecPerc(RPSCat,st,t) * sum{(r,h)$[rb(r)$r_st_rps(r,st)], hours(h) *(
* RecStyle(st,RPSCat)=0 means end-use sales.
        ( (LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]
        - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) }) * (1.0 - distloss)
        )$(RecStyle(st,RPSCat)=0)

* RecStyle(st,RPSCat)=1 means bus-bar sales.
      + ( LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]
        - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) }
        )$(RecStyle(st,RPSCat)=1)

* RecStyle(st,RPSCat)=2 means generation (including distPV), but subtracting canadian exports
*for CES (similar to the left-hand-side). Also, because GEN from pvb(i) includes grid charging,
*subtract out its grid charging (see eq_REC_Generation above).
      + ( sum{(i,v)$[valgen(i,v,r,t)$(not storage_standalone(i))], GEN(i,v,r,h,t)
          - (distloss * GEN(i,v,r,h,t))$(distpv(i) or dupv(i))
          - (STORAGE_IN_PVB_G(i,v,r,h,t) * storage_eff_pvb_g(i,t))$[pvb(i)$Sw_PVB] }
          - can_exports_h(r,h,t)$[(Sw_Canada=1)$sameas(RPSCat,"CES")]
        )$(RecStyle(st,RPSCat)=2)
    )}
;

* ---------------------------------------------------------------------------

eq_REC_BundleLimit(RPSCat,st,ast,t)$[stfeas(st)$stfeas(ast)$tmodel(t)
                              $(not sameas(st,ast))$Sw_StateRPS
                              $(sum{i,RecMap(i,RPSCat,st,ast,t) })
                              $(sameas(RPSCat,"RPS_Bundled") or sameas(RPSCat,"CES_Bundled"))
                              $(yeart(t)>=RPS_StartYear)]..

*amount of net transmission flows from state st to state ast
    sum{(h,r,rr,trtype)$[r_st(r,st)$r_st(rr,ast)$routes(r,rr,trtype,t)],
          hours(h) * FLOW(r,rr,h,t,trtype)
      }

    =g=
* must be greater than bundled RECS
    sum{i$RecMap(i,RPSCat,st,ast,t),
        RECS(RPSCat,i,st,ast,t) }
;

* ---------------------------------------------------------------------------

eq_REC_unbundledLimit(RPSCat,st,t)$[st_unbundled_limit(RPScat,st)$tmodel(t)$stfeas(st)
                            $(yeart(t)>=RPS_StartYear)$Sw_StateRPS
                            $(sameas(RPSCat,"RPS_All") or sameas(RPSCat,"CES"))]..
*the limit on unbundled RECS times the REC requirement (based on end-use sales)
      REC_unbundled_limit(RPSCat,st,t) * RecPerc(RPSCat,st,t) *
        sum{(r,h)$r_st(r,st),
            hours(h) *
            (LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1] - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) }) * (1.0 - distloss)
           }
      =g=

*needs to be greater than the unbundled recs
*NB unbundled RECS are computed as all imported RECS minus bundled RECS
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS(RPSCat,i,ast,st,t) }

    - sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("RPS_Bundled",i,ast,st,t) }$sameas(RPSCat,"RPS_All")

    - sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("CES_Bundled",i,ast,st,t) }$sameas(RPSCat,"CES")
;

* ---------------------------------------------------------------------------

eq_REC_ooslim(RPSCat,st,t)$[RecPerc(RPSCat,st,t)$(yeart(t)>=RPS_StartYear)
                           $RPS_oosfrac(st)$stfeas(st)$tmodel(t)$Sw_StateRPS
                           $(not sameas(RPSCat,"RPS_Bundled"))
                           $(not sameas(RPSCat,"CES_Bundled"))]..

*the fraction of imported recs times the requirement (based on end-use sales)
    RPS_oosfrac(st) * RecPerc(RPSCat,st,t) *
        sum{(r,h)$r_st(r,st),
            hours(h) *
            (LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1] - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) }) * (1.0 - distloss)
           }
    =g=

*imported RECs - note that the not sameas(st,ast) indicates they are not generated in-state
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS(RPSCat,i,ast,st,t)
       }

    + sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("RPS_Bundled",i,ast,st,t)
       }$sameas(RPSCat,"RPS_All")

    + sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("CES_Bundled",i,ast,st,t)
       }$sameas(RPSCat,"CES")
;

* ---------------------------------------------------------------------------

*exports must be less than RECS generated
eq_REC_launder(RPSCat,st,t)$[RecStates(RPSCat,st,t)$(not tfirst(t))$(yeart(t)>=RPS_StartYear)
                               $tmodel(t)$stfeas(st)$Sw_StateRPS
                               $(not sameas(RPSCat,"RPS_Bundled"))
                               $(not sameas(RPSCat,"CES_Bundled"))]..

*in-state REC generation
    sum{(i,v,r,h)$(valgen(i,v,r,t)$RecTech(RPSCat,i,st,t)$r_st(r,st)),
         hours(h) * GEN(i,v,r,h,t) }

    =g=

*exported RECS - NB the conditional that st!=ast
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$(stfeas(ast) or sameas(ast,"voluntary"))$(not sameas(st,ast))],
         RECS(RPSCat,i,st,ast,t) }

    + sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("RPS_Bundled",i,ast,st,t)
       }$sameas(RPSCat,"RPS_All")

    + sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("CES_Bundled",i,ast,st,t)
       }$sameas(RPSCat,"CES")

;

* ---------------------------------------------------------------------------

eq_RPS_OFSWind(st,t)$[tmodel(t)$stfeas(st)$offshore_cap_req(st,t)$Sw_StateRPS
                      $sum{(i,v,r)$[r_st(r,st)$ofswind(i)], valcap(i,v,r,t) }]..

* existing capacity of wind
    sum{(i,v,r)$[r_st(r,st)$ofswind(i)], m_capacity_exog(i,v,r,t) }

* investments over time
    + sum{(i,v,r,tt)$[r_st(r,st)$ofswind(i)$inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
          INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb] }

    =g=

*exogenously-specified requirement for offshore wind capacity
    offshore_cap_req(st,t)
;

* ---------------------------------------------------------------------------

eq_batterymandate(st,t)$[tmodel(t)$batterymandate(st,t)$(yeart(t)>=firstyear_battery)
                        $Sw_BatteryMandate]..
*battery capacity
    sum{(i,v,r)$[r_st(r,st)$valcap(i,v,r,t)$(battery(i) or pvb(i))], bcr(i) * CAP(i,v,r,t) }

    =g=

*must be greater than the required level
    batterymandate(st,t)
;

* ---------------------------------------------------------------------------

eq_national_gen(t)$[tmodel(t)$national_gen_frac(t)$Sw_GenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[nat_gen_tech_frac(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h) * nat_gen_tech_frac(i) }

    =g=

*must exceed the mandated percentage [times]
    national_gen_frac(t) * (

* if Sw_GenMandate = 1, then apply the fraction to the bus bar load
    (
* load
    sum{(r,h)$rb(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$routes(rr,r,trtype,t), (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)], STORAGE_IN(i,v,r,h,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)], GEN(i,v,r,h,t) * hours(h) }
    )$[Sw_GenMandate = 1]

* if Sw_GenMandate = 2, then apply the fraction to the end use load
    + (sum{(r,h)$rb(r),
        hours(h) *
        ( (LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
       })$[Sw_GenMandate = 2]
    )
;

* ---------------------------------------------------------------------------

*====================================
* --- FUEL SUPPLY CURVES ---
*====================================

* ---------------------------------------------------------------------------

*gas used from each bin is the sum of all gas used
eq_gasused(cendiv,h,t)$[tmodel(t)$((Sw_GasCurve=0) or (Sw_GasCurve=3))$hours(h)]..

    sum{gb,GASUSED(cendiv,gb,h,t) }

    =e=

    sum{(i,v,r)$[valgen(i,v,r,t)$gas(i)$r_cendiv(r,cendiv)],
         heat_rate(i,v,r,t) * (GEN(i,v,r,h,t) + CCSFLEX_POW(i,v,r,h,t)$[ccsflex(i)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)]) } / gas_scale

    + (sum{(v,r)$[valcap("dac_gas",v,r,t)$r_cendiv(r,cendiv)],
         dac_gas_cons_rate("dac_gas",v,t) * PRODUCE("DAC","dac_gas",v,r,h,t) } / gas_scale)$Sw_DAC_Gas

;

* ---------------------------------------------------------------------------

* gas from each bin needs to less than its capacity
eq_gasbinlimit(cendiv,gb,t)$[tmodel(t)$(Sw_GasCurve=0)]..

    gaslimit(cendiv,gb,t)

    =g=

    sum{h, hours(h) * GASUSED(cendiv,gb,h,t) }
;

* ---------------------------------------------------------------------------

eq_gasbinlimit_nat(gb,t)$[tmodel(t)$(Sw_GasCurve=3)]..

   gaslimit_nat(gb,t)

   =g=

   sum{(h,cendiv),
       hours(h) * GASUSED(cendiv,gb,h,t)
      }
;

* ---------------------------------------------------------------------------

eq_gasaccounting_regional(cendiv,t)$[tmodel(t)$(Sw_GasCurve=1)]..

    sum{fuelbin,VGASBINQ_REGIONAL(fuelbin,cendiv,t) }

    =e=

    sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)$r_cendiv(r,cendiv)],
         hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t)
       }
;

* ---------------------------------------------------------------------------

eq_gasaccounting_national(t)$[tmodel(t)$(Sw_GasCurve=1)]..

    sum{fuelbin,VGASBINQ_NATIONAL(fuelbin,t) }

    =e=

    sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)],
         hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t)
       }
;

* ---------------------------------------------------------------------------

eq_gasbinlimit_regional(fuelbin,cendiv,t)$[tmodel(t)$(Sw_GasCurve=1)]..

    Gasbinwidth_regional(fuelbin,cendiv,t)

    =g=

    VGASBINQ_REGIONAL(fuelbin,cendiv,t)
;

* ---------------------------------------------------------------------------

eq_gasbinlimit_national(fuelbin,t)$[tmodel(t)$(Sw_GasCurve=1)]..

    Gasbinwidth_national(fuelbin,t)

    =g=

    VGASBINQ_NATIONAL(fuelbin,t)
;

* ---------------------------------------------------------------------------

*==============================
* -- Bioenergy Supply Curve --
*==============================

* ---------------------------------------------------------------------------

eq_bioused(r,t)$[sum{(i,v)$(bio(i) or cofire(i)), valgen(i,v,r,t) }$tmodel(t)]..

    sum{bioclass, BIOUSED(bioclass,r,t) }

    =e=

*biopower generation
    + sum{(i,v,h)$[valgen(i,v,r,t)$bio(i)],
        hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }


*portion of cofire generation that is from bio resources
    + sum{(i,v,h)$[cofire(i)$valgen(i,v,r,t)],
         bio_cofire_perc * hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

* biomass consumption limit is annual
eq_biousedlimit(bioclass,usda_region,t)$tmodel(t)..

    biosupply(usda_region,bioclass,"cap")

    =g=

    sum{r$[r_usda(r,usda_region)$sum{(i,v)$(bio(i) or cofire(i)), valgen(i,v,r,t) }], BIOUSED(bioclass,r,t) }
;

* ---------------------------------------------------------------------------

*============================
* --- STORAGE CONSTRAINTS ---
*============================

* ---------------------------------------------------------------------------

*storage use cannot exceed capacity
*this constraint does not apply to CSP+TES or hydro pump upgrades
eq_storage_capacity(i,v,r,h,t)$[valgen(i,v,r,t)$(storage_standalone(i) or pvb(i))$tmodel(t)]..

* [plus] Capacity of all storage technologies
    (CAP(i,v,r,t) * bcr(i) * avail(i,h)
       * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
    )$valcap(i,v,r,t)

    =g=

* [plus] Generation from storage, excluding hybrid PV+Battery
    GEN(i,v,r,h,t)$(not pvb(i))

* [plus] Generation from battery of hybrid PV+Battery
    + GEN_PVB_B(i,v,r,h,t)$[pvb(i)$Sw_PVB]

* [plus] Storage charging
* not hybrid PV+Battery
    + STORAGE_IN(i,v,r,h,t)$[not pvb(i)]
* hybrid PV+Battery: PV
    + STORAGE_IN_PVB_P(i,v,r,h,t)$[pvb(i)$dayhours(h)$Sw_PVB]
* hybrid PV+Battery: Grid
    + STORAGE_IN_PVB_G(i,v,r,h,t)$[pvb(i)$Sw_PVB]

* [plus] Operating reserves
    + sum{ortype$[Sw_OpRes$opres_model(ortype)$opres_h(h)],
          reserve_frac(i,ortype) * OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

* The daily storage level in the next time-slice (h+1) must equal the
*  daily storage level in the current time-slice (h)
*  plus daily net charging in the current time-slice (accounting for losses).
*  CSP with storage energy accounting is also covered by this constraint.
*  Does not apply for storage technologies that allow cross-season energy arbitrage.
eq_storage_level(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)$(within_seas_frac(i,v,r) = 1)$tmodel(t)]..

*[plus] storage level in h+1
    sum{(hh)$[nexth(h,hh)], STORAGE_LEVEL(i,v,r,hh,t) }

*When flex is enabled but there is no infinite loop, we still need to enforce this
* constraint but there is no next-period storage_level that corresponds to this final hour
* Thus we can add a slack variable that allows the end-of-day/week/etc energy balance
* to be positive - avoiding certain errors and infeasibilities mainly with storage_in_min
* associated with storage_in_min. final_hour also depends on Sw_HourlyWrap
    + LAST_HOUR_SOC(i,v,r,h,t)$[final_hour_nowrap(h)]

    =e=

* only want to include storage_level from periods that have had a previous storage_level
* otherwise it becomes a free variable, implying you can charge storage without bound
    STORAGE_LEVEL(i,v,r,h,t)

*[plus] storage charging
    + storage_eff(i,t) *  hours_daily(h) * (
*energy into stand-alone storage (not CSP-TES) and hydropower that adds pumping
          STORAGE_IN(i,v,r,h,t)$[storage_standalone(i) or hyd_add_pump(i)]

*energy into storage from CSP field
        + (CAP(i,v,r,t) * csp_sm(i) * m_cf(i,v,r,h,t)
          )$[CSP_Storage(i)$valcap(i,v,r,t)]
      )
*[plus] water inflow energy available for hydropower that adds pumping
    + (CAP(i,v,r,t) * avail(i,h) * hours_daily(h) *
        sum{szn$h_szn(h,szn), cap_hyd_szn_adj(i,szn,r) * m_cf_szn(i,v,r,szn,t) }
        )$hyd_add_pump(i)

*[plus] energy into hybrid PV+battery storage
*hybrid pv+battery: PV charging
    + storage_eff_pvb_p(i,t) * hours_daily(h)
      * STORAGE_IN_PVB_P(i,v,r,h,t)$[pvb(i)$dayhours(h)$Sw_PVB]

*hybrid pv+battery: grid charging
    + storage_eff_pvb_g(i,t) * hours_daily(h) * STORAGE_IN_PVB_G(i,v,r,h,t)$[pvb(i)$Sw_PVB]

*[minus] generation from stand-alone storage (discharge) and CSP
*exclude hybrid PV+Battery because GEN refers to output from both the PV and the battery
    - hours_daily(h) * GEN(i,v,r,h,t)$[not pvb(i)]

*[minus] Generation from Battery (dicharge) of hybrid PV+Battery
    - hours_daily(h) * GEN_PVB_B(i,v,r,h,t) $[pvb(i)$Sw_PVB]

*[minus] losses from reg reserves (only half because only charging half
*the time while providing reg reserves)
    - (hours_daily(h)
       * (OPRES("reg",i,v,r,h,t)$[Sw_OpRes=1] + OPRES("combo",i,v,r,h,t)$[Sw_OpRes=2])
       * (1 - storage_eff(i,t)) / 2 * reg_energy_frac
    )$[opres_h(h)]
;

* ---------------------------------------------------------------------------

* Annual energy balance for storage that can shift energy across seasons
eq_storage_seas(i,v,r,t)
    $[valgen(i,v,r,t)$storage(i)
    $(within_seas_frac(i,v,r) < 1)$tmodel(t)]..

    sum{h,
*[plus] annual storage charging
        storage_eff(i,t) * hours(h) * (
*energy into stand-alone storage (not CSP-TES) and hydropower that adds pumping
           STORAGE_IN(i,v,r,h,t)$(storage_standalone(i) or hyd_add_pump(i))

*** vvv within_seas_frac(i,v,r) is 1 for all techs besides PSH and dispatchable hydro,
*** so these lines are never executed
*energy into storage from CSP field
           + (CAP(i,v,r,t) * csp_sm(i) * m_cf(i,v,r,h,t)
             )$[CSP_Storage(i)$valcap(i,v,r,t)]
      )

*[plus] energy into hybrid PV+battery storage
*hybrid pv+battery: PV charging
    + storage_eff_pvb_p(i,t) * hours(h)
      * STORAGE_IN_PVB_P(i,v,r,h,t)$[pvb(i)$dayhours(h)$Sw_PVB]

*hybrid pv+battery: grid charging
    + storage_eff_pvb_g(i,t) * hours(h) * STORAGE_IN_PVB_G(i,v,r,h,t)$[pvb(i)$Sw_PVB]
*** ^^^

*[plus] annual water inflow energy available for hydropower that adds pumping
    + (CAP(i,v,r,t) * avail(i,h) * hours(h) *
            sum{szn$h_szn(h,szn), cap_hyd_szn_adj(i,szn,r) * m_cf_szn(i,v,r,szn,t) }
            )$hyd_add_pump(i)
    }

    =e=
*[plus] annual generation
    sum{h, hours(h) * GEN(i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

* Minimum amount of storage input in a season to be used for generation in that season,
* when cross-season energy shifting is available
eq_storage_seas_szn(i,v,r,szn,t)
    $[valgen(i,v,r,t)$storage(i)
    $(within_seas_frac(i,v,r) < 1)$tmodel(t)]..

*[plus] seasonal generation
    sum{h$h_szn(h,szn), hours(h) * GEN(i,v,r,h,t) }

=g=

*fractional in-season energy requirement
    within_seas_frac(i,v,r) *
*[plus] seasonal storage charging
    sum{h$h_szn(h,szn),
        storage_eff(i,t) * hours(h) *
*energy into stand-alone storage (not CSP-TES) and hydropower that adds pumping
        (   STORAGE_IN(i,v,r,h,t)$(storage_standalone(i) or hyd_add_pump(i))

*** vvv within_seas_frac(i,v,r) is 1 for all techs besides PSH and dispatchable hydro,
*** so these lines are never executed
*energy into storage from CSP field
            + (CAP(i,v,r,t) * csp_sm(i) * m_cf(i,v,r,h,t)
              )$[CSP_Storage(i)$valcap(i,v,r,t)]
        )

*[plus] energy into hybrid PV+battery storage
*hybrid pv+battery: PV charging
    + storage_eff_pvb_p(i,t) * hours(h)
      * STORAGE_IN_PVB_P(i,v,r,h,t)$[pvb(i)$dayhours(h)$Sw_PVB]
*hybrid pv+battery: grid charging
    + storage_eff_pvb_g(i,t) * hours(h) * STORAGE_IN_PVB_G(i,v,r,h,t)$[pvb(i)$Sw_PVB]
*** ^^^

*[plus] seasonal water inflow energy available for hydropower that adds pumping
    + (CAP(i,v,r,t) * avail(i,h) * hours(h)
            * cap_hyd_szn_adj(i,szn,r)
            * m_cf_szn(i,v,r,szn,t)
        )$hyd_add_pump(i)
    }
;

* ---------------------------------------------------------------------------

*there must be sufficient energy in storage to provide operating reserves
eq_storage_opres(i,v,r,h,t)
    $[valgen(i,v,r,t)$tmodel(t)$Sw_OpRes$opres_h(h)
    $(storage_standalone(i) or pvb(i) or hyd_add_pump(i))]..

*[plus] initial storage level
    STORAGE_LEVEL(i,v,r,h,t)

*[minus] generation that occurs during this timeslice
    - hours_daily(h) * GEN(i,v,r,h,t) $[not pvb(i)]

*[minus] generation that occurs during this timeslice
    - hours_daily(h) * GEN_PVB_B(i,v,r,h,t) $[pvb(i)$Sw_PVB]

*[minus] losses from reg reserves (only half because only charging half
*the time while providing reg reserves)
    - hours_daily(h) * (OPRES("reg",i,v,r,h,t)$[Sw_OpRes = 1] + OPRES("combo",i,v,r,h,t)$[Sw_OpRes = 2])  
    * (1 - storage_eff(i,t)) / 2 * reg_energy_frac

    =g=

*[plus] energy reserved for operating reserves
    + hours_daily(h) * sum{ortype$opres_model(ortype), OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

*storage charging must exceed OR contributions for thermal storage
eq_storage_thermalres(i,v,r,h,t)
    $[valgen(i,v,r,t)$Thermal_Storage(i)
    $tmodel(t)$Sw_OpRes$opres_h(h)]..

    STORAGE_IN(i,v,r,h,t)

    =g=

    sum{ortype$[opres_model(ortype)],
        reserve_frac(i,ortype) * OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

*batteries and CSP-TES are limited by their duration for each normalized hour per season
*seas_cap_frac_delta is not applied here because we assume that the storage energy capacity is
*constant across the year.
eq_storage_duration(i,v,r,h,t)$[valgen(i,v,r,t)$valcap(i,v,r,t)
                               $(battery(i) or CSP_Storage(i) or pvb(i) or psh(i))
                               $tmodel(t)]..

* [plus] storage duration times storage capacity
    storage_duration(i) * CAP(i,v,r,t) * (1$CSP_Storage(i) + 1$psh(i) + bcr(i)$(battery(i) or pvb(i)))

    =g=

    STORAGE_LEVEL(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

* Charging power must be less than a specified fraction of power output capacity
* This is required in addition to eq_storage_capacity for facilities where input capacity < output capacity.
* If storinmaxfrac were applied to CAP in eq_storage_capacity, it would also limit output capacity.
eq_storage_in_cap(i,v,r,h,t)$[(storage_standalone(i) or hyd_add_pump(i))$valgen(i,v,r,t)$valcap(i,v,r,t)
                              $tmodel(t)$(storinmaxfrac(i,v,r) < 1)]..

*[plus] maximum storage input capacity as a fraction of output capacity and accounting for availability
    avail(i,h) * storinmaxfrac(i,v,r)
    * CAP(i,v,r,t)
    * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})

    =g=

*[plus] storage input
    STORAGE_IN(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

* the charging power in any time slice cannot exceed the minstorfrac times the
* charging power from any other hour within the same season (via hour_szn_group(h,hh))
eq_storage_in_minloading(i,v,r,h,hh,t)$[(storage_standalone(i) or hyd_add_pump(i))$tmodel(t)
                                            $minstorfrac(i,v,r)$valgen(i,v,r,t)$hour_szn_group(h,hh)$Sw_MinLoading]..

    STORAGE_IN(i,v,r,h,t)

    =g=

    STORAGE_IN(i,v,r,hh,t) * minstorfrac(i,v,r)
;

* ---------------------------------------------------------------------------

*===============================
* --- Hybrid PV+Battery ---
*===============================

* ---------------------------------------------------------------------------

* Generation post curtailment =
*    + generation from pv (post curtailment)
*    + generation from battery
*    - storage charging from PV
eq_pvb_total_gen(i,v,r,h,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$Sw_PVB]..

    + GEN_PVB_P(i,v,r,h,t)

    + GEN_PVB_B(i,v,r,h,t)

* [minus] charging from PV (1) for curtailment recovery and (2) not for curtailment recovery
    - STORAGE_IN_PVB_P(i,v,r,h,t)$dayhours(h)

    =e=

    GEN(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

* Energy to storage from PV (not for curtailment recovery) + PV generation (post curtailment) <= PV resource
* capacity factor is adjusted to include inverter losses, clipping losses, and low voltage losses
eq_pvb_array_energy_limit(i,v,r,h,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$valcap(i,v,r,t)$Sw_PVB]..

* [plus] PV output
    m_cf(i,v,r,h,t) * CAP(i,v,r,t)

    =g=

* [plus] charging from PV (no curtailment recovery)
    + STORAGE_IN_PVB_P(i,v,r,h,t)$dayhours(h)

* [plus] generation from PV (post curtailment)
    + GEN_PVB_P(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

* Energy moving through the inverter cannot exceed the inverter capacity
eq_pvb_inverter_limit(i,v,r,h,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$valcap(i,v,r,t)$Sw_PVB]..

* [plus] inverter capacity [AC] = panel capacity [DC] / ILR [DC/AC]
    + CAP(i,v,r,t) / ilr(i)

    =g=

* [plus] Output from PV
    + GEN_PVB_P(i,v,r,h,t)

* [plus] Output form battery
    + GEN_PVB_B(i,v,r,h,t)

* [plus] Battery charging from grid
    + STORAGE_IN_PVB_G(i,v,r,h,t)

* [plus] Battery operating reserves
    + sum{ortype$[Sw_OpRes$opres_h(h)$opres_model(ortype)], OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

* total energy charged from local PV >= ITC qualification fraction * total energy charged

eq_pvb_itc_charge_reqt(i,v,r,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$pvb_itc_qual_frac$Sw_PVB]..

* [plus] Battery charging from PV
    + sum{h$dayhours(h), STORAGE_IN_PVB_P(i,v,r,h,t) * hours(h) }

    =g=

    + pvb_itc_qual_frac * (

* [plus] Battery charging from PV
    + sum{h$dayhours(h), STORAGE_IN_PVB_P(i,v,r,h,t) * hours(h) }

* [plus] Battery charging from Grid
    + sum{h, STORAGE_IN_PVB_G(i,v,r,h,t) * hours(h) }
    )
;

* ---------------------------------------------------------------------------

*============================
* --- DEMAND RESPONSE CONSTRAINTS ---
*============================

*maximum energy shifted to timeslice h from timeslice hh
eq_dr_max_shift(i,v,r,h,hh,t)$[allowed_shifts(i,h,hh)$valgen(i,v,r,t)$valcap(i,v,r,t)$dr1(i)$tmodel(t)$Sw_DR]..

    CAP(i,v,r,t) * dr_dec(i,r,hh) * hours(hh) * allowed_shifts(i,h,hh)

    =g=

    DR_SHIFT(i,v,r,h,hh,t)
;

*total allowable load decrease in timeslice h
eq_dr_max_decrease(i,v,r,h,t)$[valgen(i,v,r,t)$valcap(i,v,r,t)$dr1(i)$tmodel(t)$Sw_DR]..

    CAP(i,v,r,t) * dr_dec(i,r,h) * hours(h)

    =g=

    sum{hh$[allowed_shifts(i,hh,h)], DR_SHIFT(i,v,r,hh,h,t) }
;

*total allowable load increase in timeslice h
* DR efficiency applied to the load increase, so shows up here and not in above
* DR Shift tracks the total energy decreased, so the increase will be proportionally
* larger, requiring division here to ensure it doesn't exceed allowed increase
eq_dr_max_increase(i,v,r,h,t)$[valgen(i,v,r,t)$valcap(i,v,r,t)$dr1(i)$tmodel(t)$Sw_DR]..

    CAP(i,v,r,t) * dr_inc(i,r,h) * hours(h)

    =g=

    sum{hh$[allowed_shifts(i,h,hh)], DR_SHIFT(i,v,r,h,hh,t) }

    / storage_eff(i,t)
;

* tie load reductions from demand response to generation
eq_dr_gen(i,v,r,h,t)$[valgen(i,v,r,t)$dr(i)$tmodel(t)$SW_DR]..
* [plus] DR shift types reduction in load
    sum{hh$[allowed_shifts(i,hh,h)$dr1(i)], DR_SHIFT(i,v,r,hh,h,t) / hours(h) }$Sw_DR

* [plus] DR shed types reduction in load
    + DR_SHED(i,v,r,h,t)$dr2(i) / hours(h)

    =e=

    GEN(i,v,r,h,t)
;

*total allowable load decrease in timeslice h from shed types DR
eq_dr_max_shed(i,v,r,h,t)$[valgen(i,v,r,t)$valcap(i,v,r,t)$dr2(i)$tmodel(t)$Sw_DR]..

    CAP(i,v,r,t) * dr_dec(i,r,h) * hours(h)

    =g=

    DR_SHED(i,v,r,h,t)
;

eq_dr_max_shed_hrs(i,v,r,t)$[valgen(i,v,r,t)$valcap(i,v,r,t)$dr2(i)$tmodel(t)$Sw_DR]..

    CAP(i,v,r,t) * allowed_shed(i)

    =g=

    sum{h$dr_dec(i,r,h), DR_SHED(i,v,r,h,t) / dr_dec(i,r,h) }
;


*===================================
* --- CANADIAN IMPORTS EQUATIONS ---
*===================================

* ---------------------------------------------------------------------------

eq_Canadian_Imports(r,szn,t)$[can_imports_szn(r,szn,t)$tmodel(t)$(Sw_Canada=1)]..

    can_imports_szn(r,szn,t)

    =g=

    sum{(i,v,h)$[canada(i)$valgen(i,v,r,t)$h_szn(h,szn)], GEN(i,v,r,h,t) * hours(h) }
;

* ---------------------------------------------------------------------------

*==========================
* --- WATER CONSTRAINTS ---
*==========================

* ---------------------------------------------------------------------------

*water accounting for all valid power plants for generation where usage is both for cooling and/or non-cooling purposes
eq_water_accounting(i,v,w,r,h,t)$[i_water(i)$valgen(i,v,r,t)$tmodel(t)$Sw_WaterMain]..

    WAT(i,v,w,r,h,t)

    =e=

*division by 1E6 to convert gal of water_rate(i,w,r) to Mgal
    GEN(i,v,r,h,t) * hours(h) * water_rate(i,w,r) / 1E6
;

* ---------------------------------------------------------------------------

*total water access is determined by total capacity
eq_water_capacity_total(i,v,r,t)$[tmodel(t)$valcap(i,v,r,t)
                                 $(i_water_cooling(i) or psh(i))$Sw_WaterMain$Sw_WaterCapacity]..

    WATCAP(i,v,r,t)

    =e=

*require enough water capacity to allow 100% capacity factor (8760 hour operation)
*division by 1E6 to convert gal of water_rate(i,w,r) to Mgal
    sum{h, hours(h)
    * sum{w$i_w(i,w),
           CAP(i,v,r,t) * water_rate(i,w,r) }
    * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
    } / 1E6

*require enough water capacity to fill PSH reservoir.
*uses investment so that term is only applied in the single investment year
*   as a proxy for water needs during construction phase.
    + sum{rscbin$[m_rscfeas(r,i,rscbin)$psh(i)], INV_RSC(i,v,r,rscbin,t) * water_req_psh(r,rscbin) }$Sw_PSHwatercon
;

* ---------------------------------------------------------------------------

*total water access must not exceed supply
eq_water_capacity_limit(wst,r,t)$[rb(r)$tmodel(t)$Sw_WaterMain$Sw_WaterCapacity]..

    m_watsc_dat(wst,"cap",r,t)

    + WATER_CAPACITY_LIMIT_SLACK(wst,r,t)

    =g=

    sum{(i,v)$[i_wst(i,wst)$valcap(i,v,r,t)], WATCAP(i,v,r,t) }
;

* ---------------------------------------------------------------------------

*water use must not exceed available access
eq_water_use_limit(i,v,w,r,szn,t)$[i_water_cooling(i)$valgen(i,v,r,t)$tmodel(t)
                                  $i_w(i,w)$Sw_WaterMain$Sw_WaterCapacity$Sw_WaterUse]..

    WATCAP(i,v,r,t) *sum{wst$i_wst(i,wst), watsa(wst,r,szn,t) }

    =g=

    sum{h$h_szn(h,szn), WAT(i,v,w,r,h,t) }
;

* ---------------------------------------------------------------------------

*==============================
* -- H2 and DAC Constraints --
*==============================

* ---------------------------------------------------------------------------

eq_prod_capacity_limit(i,v,r,h,t)$[tmodel(t)$consume(i)$valcap(i,v,r,t)$Sw_Prod]..

* available capacity [times] the conversion rate of tonne / MW
    CAP(i,v,r,t) * avail(i,h)
            * (prod_conversion_rate(i,v,r,t)$[not sameas(i,"dac_gas")]
                + 1$sameas(i,"dac_gas"))
            * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})

    =g=

* production in that timeslice
    sum{p$i_p(i,p), PRODUCE(p,i,v,r,h,t) }
;

* H2 demand balance; national and annual. Active only when Sw_H2=1.
eq_h2_demand(p,t)$[(sameas(p,"H2"))$tmodel(t)$(yeart(t)>=Sw_H2_Demand_Start)$(Sw_H2=1)]..

* annual tonnes of production
    sum{(i,v,r,h)$[h2(i)$valcap(i,v,r,t)$i_p(i,p)],
        PRODUCE(p,i,v,r,h,t) * hours(h) }

    =g=

* annual demand
    h2_exogenous_demand(p,t)

* assuming here that h2 production and use in H2_CT can be temporally asynchronous
* that is, the hydrogen does not need to produced in the same hour it is consumed by h2-ct's
    + sum{(i,v,r,h)$[valgen(i,v,r,t)$h2_ct(i)],
            GEN(i,v,r,h,t) * hours(h) * h2_ct_intensity * heat_rate(i,v,r,t)
    }
;

* ---------------------------------------------------------------------------

* H2 demand balance; regional and by timeslice w/ H2 transport network and storage.
* Active only when Sw_H2=2 [tonne/hour]
eq_h2_demand_regional(r,h,t)
    $[tmodel(t)$(Sw_H2=2)$(yeart(t)>=Sw_H2_Demand_Start)$hours(h)]..

* endogenous supply of hydrogen
    sum{(i,v,p)$[h2(i)$valcap(i,v,r,t)$i_p(i,p)],
        PRODUCE(p,i,v,r,h,t) }
    
* net hydrogen trade with imports reduced by H2 transmission losses
    + sum(rr$h2_routes(rr,r), H2_FLOW(rr,r,h,t)) * (1 - h2_tranloss)
    - sum(rr$h2_routes(r,rr), H2_FLOW(r,rr,h,t))
        
* net storage injections / withdrawls in a BA
    + sum(h2_stor, H2_STOR_OUT(h2_stor,r,h,t)$[h2_stor_r(h2_stor,r)])
    - sum(h2_stor, H2_STOR_IN(h2_stor,r,h,t)$[h2_stor_r(h2_stor,r)])

    =g=

* annual demand in [tonnes/hour]
    sum(p, h2_exogenous_demand_regional(r,p,h,t) )

* region-specific H2 consumption from H2-CTs
* [MW] * [tonne/MMBtu] * [MMBtu/MWh] = [tonnes/hour]
    + sum{(i,v)$[valgen(i,v,r,t)$h2_ct(i)],
            GEN(i,v,r,h,t) * h2_ct_intensity * heat_rate(i,v,r,t)
       }
;

* ---------------------------------------------------------------------------

eq_h2_transport_caplimit(r,rr,h,t)$[h2_routes(r,rr)$(Sw_H2=2)
                                    $tmodel(t)$(yeart(t)>=Sw_H2_Demand_Start)]..

*capacity computed as cumulative investments of h2 pipelines up to the current year
    sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))
           $(yeart(tt)>=Sw_H2_Demand_Start)],
        H2_TRANSPORT_INV(r,rr,tt)$h2_routes_inv(r,rr) 
        + H2_TRANSPORT_INV(rr,r,tt)$h2_routes_inv(rr,r) }

    =g=

*bi-directional flow of h2
    H2_FLOW(rr,r,h,t) + H2_FLOW(r,rr,h,t)
;

* ---------------------------------------------------------------------------

* link H2 storage level between timeslices of actual periods, or hours when running a chronological year
eq_h2_storage_level(h2_stor,r,actualszn,h,t)
    $[tmodel(t)$(yeart(t)>=Sw_H2_Demand_Start)$(Sw_H2_StorTimestep=2)
    $h2_stor_r(h2_stor,r)$(Sw_H2=2)$h_actualszn(h,actualszn)]..

*[plus] H2 storage level in next timeslice
    sum{(hh,actualsznn)$[nexth_actualszn(actualszn,h,actualsznn,hh)],
        H2_STOR_LEVEL(h2_stor,r,actualsznn,hh,t) }

    =e=

* H2 storage level in current timeslice
    H2_STOR_LEVEL(h2_stor,r,actualszn,h,t)

*[plus] h2 storage injection minus withdrawal (currently assumed to be lossless)
    + hours_daily(h) * (H2_STOR_IN(h2_stor,r,h,t) - H2_STOR_OUT(h2_stor,r,h,t))
;

* ---------------------------------------------------------------------------

* link H2 storage level between seasons 
eq_h2_storage_level_szn(h2_stor,r,actualszn,t)
    $[tmodel(t)$(yeart(t)>=Sw_H2_Demand_Start)$(Sw_H2_StorTimestep=1)
    $h2_stor_r(h2_stor,r)$(Sw_H2=2)]..

*[plus] H2 storage level at start of next season
    sum{actualsznn$[nextszn(actualszn,actualsznn)],
        H2_STOR_LEVEL_SZN(h2_stor,r,actualsznn,t) }

    =e=

* H2 storage level at start of current season
    H2_STOR_LEVEL_SZN(h2_stor,r,actualszn,t)

*[plus] h2 storage injection minus withdrawal (currently assumed to be lossless)
    + sum{h$h_actualszn(h,actualszn),
          hours_daily(h) * (H2_STOR_IN(h2_stor,r,h,t) - H2_STOR_OUT(h2_stor,r,h,t)) }
;

* ---------------------------------------------------------------------------

* H2 storage capacity [tonnes]
eq_h2_storage_capacity(h2_stor,r,t)
    $[tmodel(t)$(Sw_H2=2)
    $h2_stor_r(h2_stor,r)$(yeart(t)>=Sw_H2_Demand_Start)]..

* [tonnes]
    sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))],
        H2_STOR_INV(h2_stor,r,tt)}

    =e=

* [tonnes]
    H2_STOR_CAP(h2_stor,r,t)
;

* ---------------------------------------------------------------------------

eq_h2_min_storage_cap(r,t)$[tmodel(t)$(Sw_H2=2)$Sw_H2_MinStorHours]..

* [tonnes]
    sum{h2_stor$h2_stor_r(h2_stor,r), H2_STOR_CAP(h2_stor,r,t) }

    =g=

* [MW] * [MMBtu/MWh] * [tonne/MMBtu] * [hours] = [tonnes]
    sum{(i,v)$[h2_ct(i)$valcap(i,v,r,t)],
        CAP(i,v,r,t) * heat_rate(i,v,r,t) * h2_ct_intensity * Sw_H2_MinStorHours
    }
;

* ---------------------------------------------------------------------------

* H2 storage investment capacity
* [tonnes/hour]
eq_h2_storage_flowlimit(h2_stor,r,h,t)$[h2_stor_r(h2_stor,r)$(yeart(t)>=Sw_H2_Demand_Start)
                                     $tmodel(t)$(Sw_H2=2)]..

*storage capacity computed as cumulative investments of H2 storage up to the current year
*H2 storage costs estimated for a fixed duration, so using this to link storage capacity and injection rates
* [tonnes] / [hours] = [tonnes/hour]
    H2_STOR_CAP(h2_stor,r,t) / h2_storage_duration

    =g=

*H2 storage injection [tonnes/hour]
    H2_STOR_IN(h2_stor,r,h,t)

*[plus] H2 storage withdrawal [tonnes/hour]
    + H2_STOR_OUT(h2_stor,r,h,t)
;

* ---------------------------------------------------------------------------

* total level of H2 storage cannot exceed storage investment for all days 
* [tonnes]
eq_h2_storage_caplimit(h2_stor,r,actualszn,h,t)
    $[tmodel(t)$(yeart(t)>=Sw_H2_Demand_Start)$(Sw_H2_StorTimestep=2)
    $h2_stor_r(h2_stor,r)$(Sw_H2=2)$h_actualszn(h,actualszn)]..

* total storage investment [tonnes]
    H2_STOR_CAP(h2_stor,r,t)

    =g=

* storage level of H2 [tonnes]
    H2_STOR_LEVEL(h2_stor,r,actualszn,h,t)
;

* ---------------------------------------------------------------------------

* total level of H2 storage at the beginning of the day cannot exceed storage investment
* [tonnes]
eq_h2_storage_caplimit_szn(h2_stor,r,actualszn,t)
    $[tmodel(t)$(yeart(t)>=Sw_H2_Demand_Start)$(Sw_H2_StorTimestep=1)
    $h2_stor_r(h2_stor,r)$(Sw_H2=2)]..

* total storage investment [tonnes]
    H2_STOR_CAP(h2_stor,r,t)

    =g=

* storage level of H2 [tonnes]
    H2_STOR_LEVEL_SZN(h2_stor,r,actualszn,t)
;

* ---------------------------------------------------------------------------

*=================================
* -- CO2 transport and storage --
*=================================


eq_co2_capture(r,h,t)$[rb(r)$tmodel(t)$Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]..

    CO2_CAPTURED(r,h,t)

    =e=

*capture from CCS technologies
    sum{(i,v)$[capture_rate("CO2",i,v,r,t)$valgen(i,v,r,t)], capture_rate("CO2",i,v,r,t)
                                           * GEN(i,v,r,h,t) }

*capture from SMR CCS for H2 production
    + sum{(p,i,v)$[i_p("smr_ccs",p)$valcap("smr_ccs",v,r,t)], smr_capture_rate * smr_co2_intensity
                                                              * PRODUCE(p,"smr_ccs",v,r,h,t) }$Sw_H2

* capture from DAC
    + sum{(i,v)$[dac(i)$valcap(i,v,r,t)$i_p(i,"DAC")], PRODUCE("DAC",i,v,r,h,t) }$Sw_DAC
;

* ---------------------------------------------------------------------------

eq_co2_transport_caplimit(r,rr,h,t)$[co2_routes(r,rr)$Sw_CO2_Detail
                                    $tmodel(t)$(yeart(t)>=co2_detail_startyr)]..

*capacity computed as cumulative investments of co2 pipelines up to the current year
    sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))
           $(yeart(tt)>=co2_detail_startyr)],
        CO2_TRANSPORT_INV(r,rr,tt) + CO2_TRANSPORT_INV(rr,r,tt) }

    =g=

*bi-directional flow of co2
    CO2_FLOW(rr,r,h,t) + CO2_FLOW(r,rr,h,t)
;

* ---------------------------------------------------------------------------

eq_co2_spurline_caplimit(r,cs,h,t)$[Sw_CO2_Detail$r_cs(r,cs)$tmodel(t)$(yeart(t)>=co2_detail_startyr)]..

*capacity computed as cumulative investments of co2 spurlines up to the current year
    sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))$(yeart(tt)>=co2_detail_startyr)],
            CO2_SPURLINE_INV(r,cs,tt) }

    =g=

    CO2_STORED(r,cs,h,t)
;

* ---------------------------------------------------------------------------

eq_co2_sink(r,h,t)$[rb(r)$tmodel(t)$Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]..

*the amount of co2 stored from r in all of its cs sites
    sum{cs$r_cs(r,cs), CO2_STORED(r,cs,h,t) }

    =e=

* local CO2 entering storage
* note we can substitute the equation above into here
* and avoid the creation of a new variable
* -but- it is nice to have this for reporting/tracking
    CO2_CAPTURED(r,h,t)

* net trade
    + sum{rr$co2_routes(r,rr), CO2_FLOW(rr,r,h,t) - CO2_FLOW(r,rr,h,t) }
;

* ---------------------------------------------------------------------------

eq_co2_injection_limit(cs,h,t)$[Sw_CO2_Detail$tmodel(t)$(yeart(t)>=co2_detail_startyr)$csfeas(cs)]..

* exogenously defined injection limit
    co2_injection_limit(cs)

    =g=

* must exceed tonnes per hour entering storage
    sum{r$r_cs(r,cs), CO2_STORED(r,cs,h,t) }
;

* ---------------------------------------------------------------------------

eq_co2_cumul_limit(cs,t)$[tmodel(t)$Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)$csfeas(cs)]..

*capacity by co2 bin for injections
    co2_storage_limit(cs)

    =g=

*cumulative amount stored over time
    sum{(r,h,tt)$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))$(yeart(tt)>=co2_detail_startyr)$r_cs(r,cs)],
        yearweight(tt) * hours(h) * CO2_STORED(r,cs,h,tt) }
;
* ---------------------------------------------------------------------------

*===================
* -- FLEXIBLE CCS --
*===================

* ---------------------------------------------------------------------------

eq_ccsflex_byp_ccsenergy_limit(i,v,r,h,t)$[tmodel(t)$valgen(i,v,r,t)$ccsflex_byp(i)$Sw_CCSFLEX_BYP]..
  CCSFLEX_POW(i,v,r,h,t) =l= ccsflex_powlim(i,t) * (GEN(i,v,r,h,t) + CCSFLEX_POW(i,v,r,h,t))
;

* ---------------------------------------------------------------------------

eq_ccsflex_sto_ccsenergy_limit_szn(i,v,r,szn,t)$[tmodel(t)$valgen(i,v,r,t)$ccsflex_sto(i)$Sw_CCSFLEX_STO]..
  sum{h$h_szn(h,szn), hours(h) * CCSFLEX_POW(i,v,r,h,t)} =l= ccsflex_powlim(i,t) * sum{h$h_szn(h,szn), hours(h) * (GEN(i,v,r,h,t) + CCSFLEX_POW(i,v,r,h,t))}
;

* ---------------------------------------------------------------------------

eq_ccsflex_sto_ccsenergy_balance(i,v,r,szn,t)$[valgen(i,v,r,t)$ccsflex_sto(i)$tmodel(t)$Sw_CCSFLEX_STO$(Sw_CCSFLEX_STO_LEVEL=0)]..
  sum{h$h_szn(h,szn), hours(h) * CCSFLEX_POWREQ (i,v,r,h,t) } =e= sum{h$h_szn(h,szn), hours(h) * CCSFLEX_POW(i,v,r,h,t) } ;
;

* ---------------------------------------------------------------------------

eq_ccsflex_sto_storage_level(i,v,r,h,t)$[valgen(i,v,r,t)$ccsflex_sto(i)$tmodel(t)$Sw_CCSFLEX_STO$(Sw_CCSFLEX_STO_LEVEL=1)]..

*[plus] storage level in h+1
    sum{(hh)$[nexth(h,hh)], CCSFLEX_STO_STORAGE_LEVEL(i,v,r,hh,t) }

    =e=

* only want to include storage_level from periods that have had a previous storage_level
* otherwise it becomes a free variable, implying you can charge storage without bound
    CCSFLEX_STO_STORAGE_LEVEL(i,v,r,h,t)

*[plus] storage charging
    + ccsflex_sto_storage_eff(i,t) * hours_daily(h) * CCSFLEX_POWREQ(i,v,r,h,t)

*[minus] storage discharge
*exclude hybrid PV+Battery because GEN refers to output from both the PV and the battery
    - hours_daily(h) * CCSFLEX_POW(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

eq_ccsflex_sto_storage_level_max(i,v,r,h,t)$[valgen(i,v,r,t)$valcap(i,v,r,t)$ccsflex(i)$tmodel(t)$Sw_CCSFLEX_STO$(Sw_CCSFLEX_STO_LEVEL=1)]..

* [plus] storage duration times storage capacity
    ccsflex_sto_storage_duration(i) * CCSFLEX_STO_STORAGE_CAP(i,v,r,t)

    =g=

    CCSFLEX_STO_STORAGE_LEVEL(i,v,r,h,t)
;

* ---------------------------------------------------------------------------
