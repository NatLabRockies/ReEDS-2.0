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
  FLEX(flex_type,r,allh,t)        "--MW-- flexible load shifted to each timeslice"
*   PEAK_FLEX(r,ccseason,t)          "--MW-- peak busbar load adjustment based on load flexibility"
  DROPPED(r,allh,t)               "--MW-- dropped load (only allowed before Sw_StartMarkets)"
  EXCESS(r,allh,t)                "--MW-- excess load (only allowed before Sw_StartMarkets)"
  CAP_LOADSITE(r,t)               "--MW-- capacity of flexibly sited load"
  INV_LOADSITE(r,t)               "--MW-- capacity of flexibly sited load installed in model year"
  OP_LOADSITE(r,allh,t)           "--MW-- operations of flexibly sited load"

* capacity and investment variables
  CAP_SDBIN(i,v,r,ccseason,sdbin,t)        "--MW-- generation power capacity by storage duration bin for relevant technologies"
  CAP_SDBIN_ENERGY(i,v,r,ccseason,sdbin,t) "--MWh-- generation energy capacity by storage duration bin for relevant technologies"
  CAP(i,v,r,t)                             "--MW-- total generation capacity in MWac (MWdc for PV); PV capacity of hybrid PV+battery; max native, flexible EV load for EVMC"
  CAP_ENERGY(i,v,r,t)                      "--MWh-- battery capacity in terms of energy"
  CAP_ABOVE_LIM(tg,r,t)                    "--MW-- amount of capacity that is deployed above the interconnection queue limits"
  CAP_RSC(i,v,r,rscbin,t)                  "--MW-- total generation capacity in MWac (MWdc for PV) for wind-ons and upv"
  GROWTH_BIN(gbin,i,st,t)                  "--MW-- total new (from INV) generation capacity in each growth bin by state and technology group"
  INV(i,v,r,t)                             "--MW-- generation capacity additions in year t"
  INV_ENERGY(i,v,r,t)                      "--MWh-- generation energy capacity additions in year t"
  EXTRA_PRESCRIP(pcat,r,t)                 "--MW-- builds beyond those prescribed power capacity once allowed in firstyear(pcat) - exceptions for gas-ct, wind-ons, and wind-ofs"
  EXTRA_PRESCRIP_ENERGY(pcat,r,t)          "--MWh-- builds beyond those prescribed battery energy capacity once allowed in firstyear(pcat)"
  INV_CAP_UP(i,v,r,rscbin,t)               "--MW-- upsized generation capacity addition in year t"
  INV_ENER_UP(i,v,r,rscbin,t)              "--MW-- upsized energy addition in year t using capacity factor to convert to capacity units"
  INV_REFURB(i,v,r,t)                      "--MW-- investment in refurbishments of technologies that use a resource supply curve"
  INV_RSC(i,v,r,rscbin,t)                  "--MW-- investment in technologies that use a resource supply curve"
  UPGRADES(i,v,r,t)                        "--MW-- investments in upgraded capacity from ii to i"
  UPGRADES_RETIRE(i,v,r,t)                 "--MW-- upgrades that have been retired - used as a free slack variable in eq_cap_upgrade"

* The units for all of the operational variables are average MW or MWh/time-slice hours
* generation and storage variables
  GEN(i,v,r,allh,t)                      "--MW-- electricity generation (post-curtailment) in hour h"
  GEN_PLANT(i,v,r,allh,t)                "--MW-- average plant generation from hybrid generation/storage technologies in hour h"
  GEN_STORAGE(i,v,r,allh,t)              "--MW-- average generation from hybrid storage technologies in hour h"
  STORAGE_IN_PLANT(i,v,r,allh,t)         "--MW-- hybrid plant storage charging in hour h that is charging from a coupled technology"
  STORAGE_IN_GRID(i,v,r,allh,t)          "--MW-- hybrid plant storage charging in hour h that is charging from the grid"
  AVAIL_SITE(x,allh,t)                   "--MW-- available generation from all resources at reV site x"
  CURT(r,allh,t)                         "--MW-- curtailment from vre generators in hour h"
  MINGEN(r,allszn,t)                     "--MW-- minimum generation level in each season"
  STORAGE_IN(i,v,r,allh,t)               "--MW-- storage charging in hour h that is charging from a given source technology; not used for CSP-TES"
  STORAGE_LEVEL(i,v,r,allh,t)            "--MWh-- storage level in hour h"
  STORAGE_INTERDAY_LEVEL(i,v,r,allszn,t) "--MWh-- storage level at hour 0 of the partition"
  RAMPUP(i,r,allh,allhh,t)               "--MW-- upward change in generation from h to hh"

* flexible CCS variables
  CCSFLEX_POW(i,v,r,allh,t)                "--avg MW-- average power consumed for CCS system"
  CCSFLEX_POWREQ(i,v,r,allh,t)             "--avg MW-- average power requirement for CCS system"
  CCSFLEX_STO_STORAGE_LEVEL(i,v,r,allh,t)  "--varies-- level of process storage (e.g., chemical solvent) in the CCS system"
  CCSFLEX_STO_STORAGE_CAP(i,v,r,t)         "--varies-- capacity of process storage (e.g., chemical solvent) in the CCS system"

* trade variables
  FLOW(r,rr,allh,t,trtype)         "--MW-- electricity flow on transmission lines in hour h"
  OPRES_FLOW(ortype,r,rr,allh,t)   "--MW-- interregional trade of operating reserves by operating reserve type"
  PRMTRADE(r,rr,trtype,ccseason,t) "--MW-- planning reserve margin capacity traded from r to rr"

* operating reserve variables
  OPRES(ortype,i,v,r,allh,t)       "--MW-- operating reserves by type"

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
  CAPTRAN_ITL(itlgrp,itlgrpp,t)                  "--MW-- capacity of groups of transmission interfaces for county and mixed"
  INVTRAN(r,rr,trtype,t)                         "--MW-- investment in transmission capacity (defined for both directions)"
  INVTRAN_AC(r,rr,tscbin,t)                      "--MW-- transmission capacity added to transmission supply curve bin (defined for both directions)"
  CAP_CONVERTER(r,t)                             "--MW-- VSC AC/DC converter capacity"
  INV_CONVERTER(r,t)                             "--MW-- investment in AC/DC converter capacity"
  CONVERSION(r,allh,intype,outtype,t)            "--MW-- conversion of AC->DC or DC->AC"
  CONVERSION_PRM(r,ccseason,intype,outtype,t)    "--MW-- planning reserve margin capacity sent through VSC AC/DC converters"
  CAP_SPUR(x,t)                                  "--MW-- capacity of spur lines"
  INV_SPUR(x,t)                                  "--MW-- investment in spur line capacity"
  INV_POI(r,t)                                   "--MW-- investment in new POI capacity (for network reinforcement costs)"
  TRAN_CAPEX_BINS(r,rr,tscbin,t)                 "--$-- transmission capex cost bins (defined for r < rr)"

* production-, CO2-, and hydrogen-specific variables
  PRODUCE(p,i,v,r,allh,t)               "--metric tons per hour-- production of hydrogen or DAC capture"
  CO2_CAPTURED(r,allh,t)                "--metric tons per hour-- amount of CO2 captured from DAC and CCS technologies"
  CO2_STORED(r,cs,allh,t)               "--metric tons per hour-- amount of CO2 stored underground"
  CO2_FLOW(r,rr,allh,t)                 "--metric tons per hour-- interregional flow of CO2"
  CO2_TRANSPORT_INV(r,rr,t)             "--metric tons per hour-- investment in interregional CO2 transport capacity"
  CO2_SPURLINE_INV(r,cs,t)              "--metric tons per hour-- spurline investment from r to carbon storage site (saline storage basin)"  
  H2_FLOW(r,rr,allh,t)                  "--metric tons per hour-- interregional flow of hydrogen"
  H2_TRANSPORT_INV(r,rr,t)              "--metric tons per hour-- investment in interregional hydrogen transmission capacity"
  H2_STOR_INV(h2_stor,r,t)              "--metric tons-- investment in hydrogen storage capacity"
  H2_STOR_CAP(h2_stor,r,t)              "--metric tons-- hydrogen storage capacity"
  H2_STOR_IN(h2_stor,r,allh,t)          "--metric tons per hour-- injection of H2 into storage in a given timeslice"
  H2_STOR_OUT(h2_stor,r,allh,t)         "--metric tons per hour-- widthdrawal of H2 from storage in a given timeslice"
  H2_STOR_LEVEL(h2_stor,r,actualszn,allh,t) "--metric tons-- total storage level of H2 in a timeslice by storage type"
  H2_STOR_LEVEL_SZN(h2_stor,r,actualszn,t)  "--metric tons-- total storage level of H2 in a period by storage type"
  CREDIT_H2PTC(i,v,r,allh,t)              "--MW-- generation by resources which qualify for the hydrogen production tax credit, in hour h"

* water climate variables
  WATCAP(i,v,r,t)                        "--million gallons/year; Mgal/yr-- total water access capacity available in terms of withdraw/consumption per year"
  WAT(i,v,w,r,allh,t)                    "--Mgal-- quantity of water withdrawn or consumed in hour h"
  WATER_CAPACITY_LIMIT_SLACK(wst,r,t)    "--Mgal/yr-- insufficient water supply in region r, of water type wst, in year t "
;

Variables
* with negative emissions technologies (e.g. BECCS, DAC) - emissions
* can become negative thus not restricted to the positive domain
  EMIT(etype,eall,r,t)                            "--metric tons-- emissions (broken down to upstream and process) in a region"

* inter-day storage variables
  STORAGE_INTERDAY_DISPATCH(i,v,r,allh,t)         "--MW--  net dispatch for storage in hour h"
  STORAGE_INTERDAY_LEVEL_MAX_DAY(i,v,r,allszn,t)  "--MWh-- maximum relative state of charge on a representative period compared to hour 0 of the rep period"
  STORAGE_INTERDAY_LEVEL_MIN_DAY(i,v,r,allszn,t)  "--MWh-- minimum relative state of charge on a representative period compared to hour 0 of the rep period"
;

*========================================
* -- Supply Side Equation Declaration --
*========================================
EQUATION

* load constraint to compute proper marginal value
 eq_loadcon(r,allh,t)                    "--MW-- load constraint used for computing the marginal energy price"

* load flexibility constraints
 eq_load_flex_day(flex_type,r,allszn,t)  "--MWh-- total flexible load in each season is equal to the exogenously-specified flexible load"
 eq_load_flex1(flex_type,r,allh,t)       "--MWh-- exogenously-specified flexible demand (load_exog_flex) must be served by flexible load (FLEX)"
 eq_load_flex2(flex_type,r,allh,t)       "--MWh-- flexible load (FLEX) can't exceed exogenously-specified flexible demand (load_exog_flex)"
*  eq_load_flex_peak(r,allh,ccseason,t)    "--MWh-- adjust peak demand as needed based on the load flexibility (FLEX)"
 eq_loadsite_inv(r,t)                   "--MW-- CAP_LOADSITE accumulates INV_LOADSITE"
 eq_loadsite_cap(r,allh,t)              "--MW-- Realized load from optimally sited load must be less than optimally sited load capacity"
 eq_loadsite_op(r,t)                    "--MW-- Realized load from optimally sited load must sum to Sw_LoadSiteCF"
 eq_loadsite_siting(loadsitereg,t)      "--MW-- Optimally sited load capacity must sum to loadsite_annual"

* capital stock constraints
 eq_cap_init_noret(i,v,r,t)               "--MW-- Existing capacity that cannot be retired is equal to exogenously-specified amount"
 eq_cap_init_retmo(i,v,r,t)               "--MW-- Existing capacity that can be retired must be monotonically decreasing"
 eq_cap_init_retub(i,v,r,t)               "--MW-- Existing capacity that can be retired is less than or equal to exogenously-specified amount"
 eq_cap_new_noret(i,v,r,t)                "--MW-- New power capacity that cannot be retired is equal to sum of all previous years investment"
 eq_cap_energy_new_noret(i,v,r,t)         "--MWh-- New energy capacity that cannot be retired is equal to sum of all previous years investment"
 eq_cap_new_retmo(i,v,r,t)                "--MW-- New capacity that can be retired must be monotonically decreasing unless increased by investment"
 eq_cap_new_retub(i,v,r,t)                "--MW-- New capacity that can be retired is less than or equal to all previous years investment"
 eq_cap_rsc(i,v,r,rscbin,t)               "--MW-- Capacity accounting for techs with exogenous capacity tracked by rscbin"
 eq_cap_up(i,v,r,rscbin,t)                "--MW-- limit on capacity upsizing"
 eq_cap_upgrade(i,v,r,t)                  "--MW-- All purchased upgrades are greater than or equal to the sum of upgraded capacity"
 eq_ener_up(i,v,r,rscbin,t)               "--MW-- limit on energy upsizing"
 eq_forceprescription_power(pcat,r,t)     "--MW-- total power investment in prescribed capacity must equal amount from exogenous prescriptions"
 eq_forceprescription_energy(pcat,r,t)    "--MWh-- total energy investment in prescribed capacity must equal amount from exogenous prescriptions"
 eq_refurblim(i,r,t)                      "--MW-- total refurbishments cannot exceed the amount of capacity that has reached the end of its life"

* renewable supply curves
 eq_rsc_inv_account(i,v,r,t)              "--MW-- INV for rsc techs is the sum over all bins of INV_RSC"
 eq_rsc_INVlim(r,i,rscbin,t)              "--MW-- total investment from each rsc bin cannot exceed the available investment"

* capacity growth limits
 eq_growthlimit_relative(i,st,t)          "--MW-- relative growth limit on technologies"
 eq_growthbin_limit(gbin,st,tg,t)         "--MW-- capacity limit for each growth bin"
 eq_growthlimit_absolute(tg,t)            "--MW-- absolute growth limit on technologies"

eq_interconnection_queues(tg,r,t)         "--MW-- capacity deployment limit based on interconnection queues"  

* storage capacity credit supply curves
 eq_cap_sdbin_balance(i,v,r,ccseason,t)             "--MW-- total binned storage power capacity must be greater than total storage capacity"
 eq_cap_sdbin_energy_balance(i,v,r,ccseason,t)      "--MWh-- total binned storage energy capacity must be greater than total storage capacity"
 eq_sdbin_power_energy_link(i,v,r,ccseason,sdbin,t) "--MWh-- binned storage energy capacity equal to binned power storage capacity times bin duration"
 eq_sdbin_power_limit(ccreg,ccseason,sdbin,t)       "--MW-- binned storage power capacity cannot exceed storage duration bin size"

* operation and reliability
 eq_site_cf(x,allh,t)                          "--MW-- generation at site x <= CF * capacity of constituent resources"
 eq_spurclip(x,allh,t)                         "--MW-- generation at site x <= spurline capacity to x"
 eq_spur_noclip(x,t)                           "--MW-- spurline capacity to x must equal total generation capacity at x"
 eq_capacity_limit(i,v,r,allh,t)               "--MW-- generation limited to available capacity"
 eq_capacity_limit_hybrid(r,allh,t)            "--MW-- generation from hybrid resources limited to available capacity"
 eq_capacity_limit_nd(i,v,r,allh,t)            "--MW-- generation limited to available capacity for non-dispatchable resources"
 eq_curt_gen_balance(r,allh,t)                 "--MW-- net generation and curtailment must equal gross generation"
 eq_dhyd_dispatch(i,v,r,allszn,t)              "--MWh-- dispatchable hydro seasonal energy constraint (when not allowing seasonal enregy shifting)"
 eq_min_cf(i,r,t)                              "--MWh-- minimum capacity factor constraint for each generator fleet, applied to (i,r)"
 eq_max_daily_cf(i,r,allszn,t)                 "--MWh-- maximum daily capacity factor constraint for any technology with maxdailycf(i,t) specified"
 eq_mingen_fixed(i,v,r,allh,t)                 "--MW-- Generation in each timeslice must be greater than mingen_fixed * available capacity"
 eq_mingen_lb(r,allh,allszn,t)                 "--MW-- lower bound on minimum generation level"
 eq_mingen_ub(r,allh,allszn,t)                 "--MW-- upper bound on minimum generation level"
 eq_minloading(i,v,r,allh,allhh,t)             "--MW-- minimum loading across same-season hours"
 eq_ramping(i,r,allh,allhh,t)                  "--MW-- definition of RAMPUP"
 eq_reserve_margin(r,ccseason,t)               "--MW-- planning reserve margin requirement"
 eq_supply_demand_balance(r,allh,t)            "--MW-- supply demand balance"
 eq_vsc_flow(r,allh,t)                         "--MW-- DC power flow"
 eq_transmission_limit(r,rr,allh,t,trtype)     "--MW-- transmission flow limit"

* operating reserve constraints
 eq_OpRes_requirement(ortype,r,allh,t)         "--MW-- operating reserve constraint"
 eq_ORCap_large_res_frac(ortype,i,v,r,allh,t)  "--MW-- operating reserve capacity availability constraint for generators with reserve_frac > 0.5"
 eq_ORCap_small_res_frac(ortype,i,v,r,allh,t)  "--MW-- operating reserve capacity availability constraint for generators with reserve_frac <= 0.5"

* regional and national policies
 eq_emit_accounting(etype,e,r,t)                "--metric tons-- accounting for total emissions in a region"
 eq_emit_rate_limit(e,r,t)                "--metric tons per MWh-- emission rate limit"
 eq_annual_cap(eall,t)                    "--metric tons-- annual (year-specific) emissions cap",
 eq_bankborrowcap(e)                      "--weighted metric tons-- flexible banking and borrowing cap (to be used w/intertemporal solve only"
 eq_RGGI_cap(t)                           "--metric tons CO2-- RGGI constraint -- Regions' emissions must be less than the RGGI cap"
 eq_state_cap(st,t)                       "--metric tons CO2-- state-level CO2 cap constraint -- used to represent California cap and trade program"
 eq_CSAPR_Budget(csapr_group,t)           "--metric tons NOx-- CSAPR trading group emissions cannot exceed the budget cap"
 eq_CSAPR_Assurance(st,t)                 "--metric tons NOx-- CSAPR state emissions cannot exceed the assurance cap"
 eq_BatteryMandate(st,t)                  "--MW-- battery storage capacity must be greater than indicated level"
 eq_cdr_cap(t)                            "--metric tons CO2-- CO2 removal (DAC and BECCS) can only offset emissions from fossil+CCS and methane leakage"
 eq_caa_max_cf(i,v,r,t)                   "--MWh-- maximum capacity factors for new gas plants (CCs and CTs) under Clean Air Act Section 111 (BSER)"
 eq_caa_rate_standard(st,t)               "--metric tons CO2-- maximum coal emissions per state under Clean Air Act Section 111 (rate-based emissions standard)"
 
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
 eq_prod_capacity_limit(i,v,r,allh,t)                 "--metric tons-- production cannot exceeds its capacity"
 eq_h2_demand(p,t)                                    "--metric tons-- production of hydrogen must meet exogenous demand plus H2-CT/CC use"
 eq_h2_demand_regional(r,allh,t)                      "--metric tons per hour-- regional hydrogen supply must equal demand net trade and storage"
 eq_h2_transport_caplimit(r,rr,allh,t)                "--metric tons per hour-- H2 flow cannot exceed cumulative pipeline investment"
 eq_h2_storage_flowlimit(h2_stor,r,allh,t)            "--metric tons per hour-- H2 storage injection or withdrawal cannot exceed cumulative storage investment"
 eq_h2_storage_capacity(h2_stor,r,t)                  "--metric tons-- H2 storage capacity is sum of H2 storage investments"
 eq_h2_min_storage_cap(r,t)                           "--metric tons-- H2 storage capacity must be ≥ Sw_H2_MinStorHours * H2 usage capacity"
 eq_h2_ptc_region_balance(h2ptcreg,t)                 "--MWh-- clean generation for hydrogen production must be more than electricity required for electrolytic H2 production in that region and year"
 eq_h2_ptc_region_hour_balance(h2ptcreg,allh,t)       "--MWh-- clean generation for hydrogen production must be more than electricity required for electrolytic H2 production in that region, hour and year"
 eq_h2_ptc_creditgen(i,v,r,allh,t)                    "--MWh-- total generation must be greater than clean generation for hydrogen production"
 eq_h2_storage_caplimit(h2_stor,r,actualszn,allh,t)   "--metric tons-- total H2 storage in a storage facility cannot exceed investment capacity"
 eq_h2_storage_level(h2_stor,r,actualszn,allh,t)      "--metric tons-- tracks H2 storage level by storage type and BA within and across periods"
 eq_h2_storage_caplimit_szn(h2_stor,r,actualszn,t)    "--metric tons-- total H2 storage in a storage facility cannot exceed investment capacity"
 eq_h2_storage_level_szn(h2_stor,r,actualszn,t)       "--metric tons-- tracks H2 storage level by storage type and BA within and across periods"
 
* CO2 capture and storage
 eq_co2_capture(r,allh,t)                    "--metric tons-- accounting of CO2 captured from DAC and CCS technologies"
 eq_co2_injection_limit(cs,allh,t)           "--metric tons per hour-- limit on CO2 injection for each carbon site as a rate"
 eq_co2_sink(r,allh,t)                       "--metric tons per hour-- co2 stored or used must exceed co2 captured plus net trade"
 eq_co2_transport_caplimit(r,rr,allh,t)      "--metric tons-- limit on interregional co2 trade"
 eq_co2_spurline_caplimit(r,cs,allh,t)       "--metric tons-- limit on transport of CO2 from BA to carbon storage site"
 eq_co2_cumul_limit(cs,t)                    "--cumulative metric tons-- total stored in a reservor cannot exceed capacity"

* transmission equations
 eq_INVTRAN_DC(r,rr,trtype,t)                "--MW-- DC transmission additions are assumed to add the same capacity in both directions"
 eq_INVTRAN_AC_forward(r,rr,tscbin,t)        "--$-- Forward transmission capacity is determined by the cumulative capex invested in the interface"
 eq_INVTRAN_AC_reverse(r,rr,tscbin,t)        "--$-- Reverse transmission capacity is determined by the cumulative capex invested in the interface"
 eq_INVTRAN_AC(r,rr,t)                       "--MW-- Accumulate investment in tscbins into INVTRAN"
 eq_TRAN_CAPEX_BINS(r,rr,tscbin,t)           "--$-- Transmission investment bins are limited by the transmission upgrade supply curve"
 eq_invtran_exog(r,rr,trtype,t)              "--MW-- Exogenous transmission investments are included in INVTRAN"
 eq_CAPTRAN_ENERGY(r,rr,trtype,t)            "--MW-- capacity accounting for transmission capacity for energy trading"
 eq_CAPTRAN_PRM(r,rr,trtype,t)               "--MW-- capacity accounting for transmission capacity for PRM trading"
 eq_prescribed_transmission(r,rr,trtype,t)   "--MW-- investment in transmission up to first year allowed must be less than the exogenous possible transmission",
 eq_PRMTRADELimit(r,rr,trtype,ccseason,t)    "--MW-- trading of PRM capacity cannot exceed the line's capacity"
 eq_transmission_investment_max(t)           "--MWmile-- investment in transmission must be <= Sw_TransInvMax"
 eq_CAPTRAN_max(r,rr,trtype,t)               "--MW-- upper limit for transmission capacity of each trtype across individual interfaces"
 eq_CAPTRAN_max_total(r,rr,t)                "--MW-- upper limit for transmission capacity of all trtypes across individual interfaces"
 eq_CAP_CONVERTER(r,t)                       "--MW-- capacity accounting for VSC AC/DC converters"
 eq_CAP_SPUR(x,t)                            "--MW-- capacity accounting for spur lines"
 eq_converter_max(r,t)                       "--MW-- upper limit for VSC AC/DC converter capacity in individual BAs"
 eq_CONVERSION_limit_energy(r,allh,t)        "--MW-- AC/DC energy conversion is limited to converter capacity"
 eq_CONVERSION_limit_prm(r,ccseason,t)       "--MW-- AC/DC PRM conversion is limited to converter capacity"
 eq_PRMTRADE_VSC(r,ccseason,t)               "--MW-- PRM capacity can flow through VSC lines but doesn't directly contribute to PRM"
 eq_POI_cap(r,t)                             "--MW-- POI capacity accounting (for network reinforcement costs)"
 eq_CAPTRAN_GRP(transgrp,transgrpp,t)        "--MW-- combined flow capacity between transmission groups"
 eq_transgrp_limit_energy(transgrp,transgrpp,allh,t) "--MW-- limit on combined interface energy flows"
 eq_transgrp_limit_prm(transgrp,transgrpp,ccseason,t) "--MW-- limit on combined interface PRM flows"
 eq_CAPTRAN_ITL(itlgrp,itlgrpp,t)            "--MW-- combined flow capacity between ITL groups"
 eq_itlgrp_limit_energy(itlgrp,itlgrpp,allh,t) "--MW-- limit on combined interface energy flows for ITLs"
 eq_itlgrp_limit_prm(itlgrp,itlgrpp,ccseason,t) "--MW-- limit on combined interface PRM flows for ITLs"
 eq_firm_transfer_limit(nercr,allh,t)        "--MW-- limit net firm capacity imports into NERC regions when using stress periods"
 eq_firm_transfer_limit_cc(nercr,ccseason,t) "--MW-- limit net firm capacity imports into NERC regions when using capacity credit"
 eq_offshore_no_backflow(r,rr,trtype,allh,t) "--MW-- disallow transmission flows from land to offshore zones"

* storage-specific equations
 eq_storage_capacity(i,v,r,allh,t)                "--MW-- second storage capacity constraint in addition to eq_capacity_limit"
 eq_storage_duration(i,v,r,allh,t)                "--MWh-- limit STORAGE_LEVEL based on hours of storage available"
 eq_storage_in_cap(i,v,r,allh,t)                  "--MW-- storage_in must be less than a given fraction of power output capacity"
 eq_storage_in_minloading(i,v,r,allh,allhh,t)     "--MW-- minimum level for storage_in across same-season hours"
 eq_storage_level(i,v,r,allh,t)                   "--MWh-- storage level inventory balance from one time-slice to the next"
 eq_storage_interday_level_max_day(i,v,r,allszn,allh,t)   "--MWh-- define the maximum relative SOC on a representative period compared to hour 0 of the rep period"
 eq_storage_interday_level_min_day(i,v,r,allszn,allh,t)   "--MWh-- define the minimum relative SOC on a representative period compared to hour 0 of the rep period"
 eq_storage_interday_min_level_start(i,v,r,allszn,t)      "--MWh-- enforce minimun SOC at first period of each partition"
 eq_storage_interday_min_level_end(i,v,r,allszn,t)        "--MWh-- enforce minimun SOC at last period of each partition"
 eq_storage_interday_level(i,v,r,allszn,t)                "--MWh-- calculate SOC of each partition at its hour 0"
 eq_storage_interday_max_level_start(i,v,r,allszn,t)      "--MWh-- enforce maximum SOC at first period of each partition"
 eq_storage_interday_max_level_end(i,v,r,allszn,t)        "--MWh-- enforce maximum SOC at last period of each partition"
 eq_storage_opres(i,v,r,allh,t)                   "--MWh-- there must be sufficient energy in the storage to be able to provide operating reserves"
 eq_storage_thermalres(i,v,r,allh,t)              "--MW-- thermal storage contribution to operating reserves is store_in only"
 eq_battery_minduration(i,v,r,t)                  "--MWh-- when power capacity is built, energy capacity should have a minimum capacity"

* hybrid plant equations
 eq_plant_total_gen(i,v,r,allh,t)           "--MW-- generation post curtailment = generation from pv (post curtailment) + generation from battery - charging from PV"
 eq_hybrid_plant_energy_limit(i,v,r,allh,t) "--MW-- PV energy to storage (no curtailment recovery) + PV energy to inverter <= PV resource"
 eq_plant_capacity_limit(i,v,r,allh,t)      "--MW-- energy moving through the inverter cannot exceed the inverter capacity"
 eq_pvb_itc_charge_reqt(i,v,r,t)            "--MWh-- total energy charged from local PV >= ITC qualification fraction * total energy charged"

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
eq_loadcon(r,h,t)$tmodel(t)..

    LOAD(r,h,t)

    =e=

*[plus] the static, exogenous load
    + load_exog_static(r,h,t)

*[plus] exogenously defined exports to Canada
* note net canadian load (when Sw_Canada = 2) is included
* in eq_supply_demand since LOAD needs to stay positive
* while net_trade can be negative and cause infeasibilities
    + can_exports_h(r,h,t)$[Sw_Canada=1]

*[plus] load from EV charging (baseline/unmanaged)
    + evmc_baseline_load(r,h,t)$Sw_EVMC

*[plus] shifted load from adopted EVMC shape resources
    + sum{(i,v)$[evmc_shape(i)$valcap(i,v,r,t)], evmc_shape_load(i,r,h) * CAP(i,v,r,t)}

*[plus] load shifted from other timeslices
    + sum{flex_type, FLEX(flex_type,r,h,t) }$Sw_EFS_flex

*[plus] Load created by production activities - only tracked during representative hours
* [metric tons/hour] / [metric tons/MWh] = [MW]
    + sum{(p,i,v)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)$(not sameas(i,"dac_gas"))],
          PRODUCE(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) }$[Sw_Prod$h_rep(h)]

*[plus] load for compressors associated with hydrogen storage injections or withdrawals
* metric tons/hour * MWh/metric tons = MW
    + sum{h2_stor$h2_stor_r(h2_stor,r),
        h2_network_load(h2_stor,t)
        * ( H2_STOR_IN(h2_stor,r,h,t) + H2_STOR_OUT(h2_stor,r,h,t) ) }$Sw_H2_CompressorLoad

* [plus] load for hydrogen pipeline compressors
* metric tons/hour * MWh/metric tons = MW
    + sum{rr$h2_routes(r,rr),
        h2_network_load("h2_compressor",t)
        * (( H2_FLOW(r,rr,h,t) + H2_FLOW(rr,r,h,t) ) / 2) }$Sw_H2_CompressorLoad

* Operations of flexibly sited load:
* - OP_LOADSITE is used when 0 < Sw_LoadSiteCF < 1
* - CAP_LOADSITE is used when Sw_LoadSiteCF = 1 because OP_LOADSITE = CAP_LOADSITE
*   (the effect is the same but avoiding the h-indexed OP_LOADSITE reduces solve time)
    + OP_LOADSITE(r,h,t)$[Sw_LoadSiteCF$(Sw_LoadSiteCF<1)$val_loadsite(r)]
    + CAP_LOADSITE(r,t)$[(Sw_LoadSiteCF=1)$val_loadsite(r)]
;

* ---------------------------------------------------------------------------

*======================================
* --- LOAD FLEXIBILITY CONSTRAINTS ---
*======================================
* CAP_LOADSITE accumulates INV_LOADSITE
eq_loadsite_inv(r,t)
    $[tmodel(t)
    $Sw_LoadSiteCF
    $val_loadsite(r)
    $(not Sw_PCM)]..

    CAP_LOADSITE(r,t)

    =e=

    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))],
          INV_LOADSITE(r,tt) }
;

* ---------------------------------------------------------------------------
* Realized load from optimally sited load must be less than optimally sited load capacity
eq_loadsite_cap(r,h,t)
    $[tmodel(t)
    $Sw_LoadSiteCF
    $(Sw_LoadSiteCF<1)
    $val_loadsite(r)]..

    CAP_LOADSITE(r,t)

    =g=

    OP_LOADSITE(r,h,t)
;

* ---------------------------------------------------------------------------
* Realized load from optimally sited load must sum to Sw_LoadSiteCF
eq_loadsite_op(r,t)
    $[tmodel(t)
    $Sw_LoadSiteCF
    $(Sw_LoadSiteCF<1)
    $val_loadsite(r)]..

    sum{h, OP_LOADSITE(r,h,t) * hours(h) }

    =g=

    CAP_LOADSITE(r,t) * sum{h, hours(h) } * Sw_LoadSiteCF
;

* ---------------------------------------------------------------------------
* Optimally sited load capacity must sum to loadsite_annual
eq_loadsite_siting(loadsitereg,t)
    $[tmodel(t)
    $Sw_LoadSiteCF
    $(not Sw_PCM)]..

    sum{r$[r_loadsitereg(r,loadsitereg)$val_loadsite(r)], CAP_LOADSITE(r,t) }

    =e=

    loadsite_annual(loadsitereg,t)
;

* ---------------------------------------------------------------------------

*The following 3 equations apply to the flexibility of load in ReEDS, originally developed
*as part of the EFS study in ReEDS heritage and adapted for ReEDS-2.0 here.

* Additional work has been done to represent flexible load as a generator + storage
* with boundaries on how many timeslices this generator may shift. See equations
* in the DR CONSTRAINTS section for that representation

* FLEX load in each season equals the total exogenously-specified flexible load in each season
eq_load_flex_day(flex_type,r,szn,t)$[tmodel(t)$Sw_EFS_flex]..

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

eq_load_flex1(flex_type,r,h,t)$[tmodel(t)$Sw_EFS_flex]..

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

eq_load_flex2(flex_type,r,h,t)$[tmodel(t)$Sw_EFS_flex]..

    load_exog_flex(flex_type,r,h,t) * hours(h)

    + sum{hh$flex_h_corr2(flex_type,h,hh), load_exog_flex(flex_type,r,hh,t) * hours(hh) }

    =g=

    FLEX(flex_type,r,h,t) * hours(h)
;

* * ---------------------------------------------------------------------------
* This constraint and the associated PEAK_FLEX variable are not currently supported
* but are left in the model in case someone decides to revive them.
* eq_load_flex_peak(r,h,ccseason,t)$[tmodel(t)$Sw_EFS_flex]..
* *   peak demand EFS flexibility adjustment is greater than
*     PEAK_FLEX(r,ccseason,t)$h_ccseason(h,ccseason)

*     =g=

* *   the static peak in each timeslice
*     peakdem_static_h(r,h,t)$h_ccseason(h,ccseason)

* *   PLUS the flexibile load served in each timeslice
*     + sum{flex_type, FLEX(flex_type,r,h,t) }$h_ccseason(h,ccseason)

* *   MINUS the static peak demand in the season corresponding to each timeslice
*     - peakdem_static_ccseason(r,ccseason,t)$h_ccseason(h,ccseason)
* ;

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
                           $(not retiretech(i,v,r,t))$(not Sw_PCM)]..

    m_capacity_exog(i,v,r,t)

* Account for capacity upsizing within init vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)],
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =e=

    CAP(i,v,r,t)

    + sum{(ii,tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
                   $valcap(ii,v,r,tt)$upgrade_from(ii,i)],
                     UPGRADES(ii,v,r,tt) 
                     - (UPGRADES_RETIRE(ii,v,r,tt)$[not noret_upgrade_tech(ii)])}
                       $[(Sw_Upgrades = 1)]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)$(not sameas(ii,'hydEND_hydED'))], 
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)$sameas(ii,'hydEND_hydED')],
          CAP(ii,v,r,t) }$[Sw_Upgrades = 2]
;

* ---------------------------------------------------------------------------

eq_cap_init_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $retiretech(i,v,r,t)$(not Sw_PCM)]..

    m_capacity_exog(i,v,r,t)

* Account for capacity upsizing within init vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)],
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =g=

    CAP(i,v,r,t)

    + sum{(ii,tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
                   $valcap(ii,v,r,tt)$upgrade_from(ii,i)],
                     UPGRADES(ii,v,r,tt) 
                     - (UPGRADES_RETIRE(ii,v,r,tt)$[not noret_upgrade_tech(ii)])}
                       $[(Sw_Upgrades = 1)]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)$(not sameas(ii,'hydEND_hydED'))], 
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)$sameas(ii,'hydEND_hydED')],
          CAP(ii,v,r,t) }$[Sw_Upgrades = 2]

;

* ---------------------------------------------------------------------------

eq_cap_init_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $retiretech(i,v,r,t)$(not Sw_PCM)]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],

         CAP(i,v,r,tt)

         + sum{(ii,ttt)$[(tfix(ttt) or tmodel(ttt))$(yeart(ttt)<=yeart(tt))
                         $valcap(ii,v,r,ttt)$upgrade_from(ii,i)],
                          UPGRADES(ii,v,r,ttt) 
                          - (UPGRADES_RETIRE(ii,v,r,ttt)$[not noret_upgrade_tech(ii)])}
                            $[(Sw_Upgrades = 1)]

         + sum{ii$[valcap(ii,v,r,tt)$upgrade_from(ii,i)$sameas(ii,'hydEND_hydED')],
               CAP(ii,v,r,tt) }$[Sw_Upgrades = 2]
        }

* Account for capacity upsizing within init vintages
    + sum{rscbin$allow_cap_up(i,v,r,rscbin,t), INV_CAP_UP(i,v,r,rscbin,t) }

    =g=

    CAP(i,v,r,t)

    + sum{(ii,tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
                   $valcap(ii,v,r,tt)$upgrade_from(ii,i)],
                     UPGRADES(ii,v,r,tt) 
                     - (UPGRADES_RETIRE(ii,v,r,tt)$[not noret_upgrade_tech(ii)])}
                       $[(Sw_Upgrades = 1)]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)$(not sameas(ii,'hydEND_hydED'))], 
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)$sameas(ii,'hydEND_hydED')],
          CAP(ii,v,r,t) }$[Sw_Upgrades = 2]
;

* ---------------------------------------------------------------------------

*==============================
* -- new capacity equations --
*==============================

* ---------------------------------------------------------------------------

eq_cap_new_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $(not retiretech(i,v,r,t))$(not Sw_PCM)]..

    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))$valcap(i,v,r,tt)],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
        }

* Account for capacity upsizing within new vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)],
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =e=

    CAP(i,v,r,t)

    + sum{(ii,tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
                   $valcap(ii,v,r,tt)$upgrade_from(ii,i)],
                     UPGRADES(ii,v,r,tt) 
                     - (UPGRADES_RETIRE(ii,v,r,tt)$[not noret_upgrade_tech(ii)])}
                       $[(Sw_Upgrades = 1)]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)$(not sameas(ii,'hydEND_hydED'))], 
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)$sameas(ii,'hydEND_hydED')],
          CAP(ii,v,r,t) }$[Sw_Upgrades = 2]

;

* ---------------------------------------------------------------------------

eq_cap_energy_new_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$battery(i)$(not Sw_PCM)]..
    
    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))$valcap(i,v,r,tt)],
              degrade(i,tt,t) * INV_ENERGY(i,v,r,tt)
        }

    + m_capacity_exog_energy(i,v,r,t)

    =e=

    CAP_ENERGY(i,v,r,t)

;

* ---------------------------------------------------------------------------

eq_cap_new_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $retiretech(i,v,r,t)$(not Sw_PCM)]..

    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))$valcap(i,v,r,tt)],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
      }

* Account for capacity upsizing within new vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)],
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =g=

    CAP(i,v,r,t)

    + sum{(ii,tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
                   $valcap(ii,v,r,tt)$upgrade_from(ii,i)],
                     UPGRADES(ii,v,r,tt) 
                     - (UPGRADES_RETIRE(ii,v,r,tt)$[not noret_upgrade_tech(ii)])}
                       $[(Sw_Upgrades = 1)]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)$(not sameas(ii,'hydEND_hydED'))], 
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)$sameas(ii,'hydEND_hydED')],
          CAP(ii,v,r,t) }$[Sw_Upgrades = 2]
;

* ---------------------------------------------------------------------------

eq_cap_new_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $retiretech(i,v,r,t)$(not Sw_PCM)]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],
         degrade(i,tt,t) * CAP(i,v,r,tt)

         + sum{(ii,ttt)$[(tfix(ttt) or tmodel(ttt))$(yeart(ttt)<=yeart(tt))
                        $valcap(ii,v,r,ttt)$upgrade_from(ii,i)],
                         UPGRADES(ii,v,r,ttt) 
                         - (UPGRADES_RETIRE(ii,v,r,ttt)$[not noret_upgrade_tech(ii)])}
                           $[(Sw_Upgrades = 1)]

         + sum{ii$[valcap(ii,v,r,tt)$upgrade_from(ii,i)$sameas(ii,'hydEND_hydED')],
               CAP(ii,v,r,tt) }$[Sw_Upgrades = 2]

        }

    + INV(i,v,r,t)$valinv(i,v,r,t)

    + INV_REFURB(i,v,r,t)$[valinv(i,v,r,t)$refurbtech(i)$Sw_Refurb]

* Account for capacity upsizing within new vintages
    + sum{rscbin$allow_cap_up(i,v,r,rscbin,t), INV_CAP_UP(i,v,r,rscbin,t) }

    =g=

    CAP(i,v,r,t)

    + sum{(ii,tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
                   $valcap(ii,v,r,tt)$upgrade_from(ii,i)],
                   UPGRADES(ii,v,r,tt) 
                   - (UPGRADES_RETIRE(ii,v,r,tt)$[not noret_upgrade_tech(ii)])}
                      $[(Sw_Upgrades = 1)]

* include contemporaneous upgrades when they are intended to
* persist as new bintages with sw_upgrades = 2
    + sum{(ii)$[upgrade_from(ii,i)$valcap(ii,v,r,t)$(not sameas(ii,'hydEND_hydED'))], 
            UPGRADES(ii,v,r,t) }$[Sw_Upgrades = 2]

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)$sameas(ii,'hydEND_hydED')],
          CAP(ii,v,r,t) }$[Sw_Upgrades = 2]
;

* ---------------------------------------------------------------------------
* Capacity accounting for rsc techs
eq_cap_rsc(i,v,r,rscbin,t)
    $[tmodel(t)
    $rsc_i(i)$(not sccapcosttech(i))
    $valcap(i,v,r,t)
    $(not Sw_PCM)]..

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

eq_cap_upgrade(i,v,r,t)$[valcap(i,v,r,t)$upgrade(i)$Sw_Upgrades$tmodel(t)$(not Sw_PCM)]..

* without peristent upgrades, all upgrades correspond to their original bintage
    sum{(tt)$[(tfix(tt) or tmodel(tt))
               $(yeart(tt)<=yeart(t))
               $(yeart(tt)>=Sw_Upgradeyear)
               $valcap(i,v,r,tt)
               $sum{ii$upgrade_from(i,ii), valcap(ii,v,r,tt) }],
                    UPGRADES(i,v,r,tt) * (1 - upgrade_derate(i,v,r,tt))
            }$[(Sw_Upgrades = 1)$(not coal(i))]

* coal cannot upgrade after the retire year - ie no mothballing
    + sum{(tt)$[(tfix(tt) or tmodel(tt))
               $(yeart(tt)<=yeart(t))
               $(yeart(tt)>=Sw_Upgradeyear)
               $valcap(i,v,r,tt)
               $sum{ii$upgrade_from(i,ii), valcap(ii,v,r,tt) }
               $(yeart(tt)<=caa_coal_retire_year)],
                    UPGRADES(i,v,r,tt) * (1 - upgrade_derate(i,v,r,tt))
            }$[(Sw_Upgrades = 1)$coal(i)]

* all previous years upgrades converted to new bintages of the present year
* NOTE: the 'v' in ivt(i,v,tt) here is an important distinction -
*       although we're summing over 'vv' we still only want upgrades
*       to be included for the upgrade tech's vintage combination
    + sum{(tt,vv)$[(tfix(tt) or tmodel(tt))$(initv(vv) or sameas(v,vv))
              $(yeart(tt)<=yeart(t))$ivt(i,v,tt)
              $(yeart(tt)>=Sw_Upgradeyear)
              $valcap(i,v,r,tt)$(not sameas(i,'hydEND_hydED'))
              $sum{ii$upgrade_from(i,ii), valcap(ii,vv,r,tt) }],
                    UPGRADES(i,vv,r,tt) * (1 - upgrade_derate(i,vv,r,tt))
            }$[Sw_Upgrades = 2]

    + sum{(tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))$(yeart(tt)>=Sw_Upgradeyear)
              $valcap(i,v,r,tt)$sameas(i,'hydEND_hydED')],
                    UPGRADES(i,v,r,tt) * (1 - upgrade_derate(i,v,r,tt))
            }$[Sw_Upgrades = 2]        

    =e=

    CAP(i,v,r,t)

* note this is equivalent to the previous version that had a =g=
* sign in the corrolary equation
    + sum{tt$[(tfix(tt) or tmodel(tt))$valcap(i,v,r,tt)], 
        UPGRADES_RETIRE(i,v,r,tt)}$[not noret_upgrade_tech(i)]
;

* ---------------------------------------------------------------------------

* Capacity upsizing limit
*   This uses rscbin to constrain hydropower upsizing using supply curve data.
eq_cap_up(i,v,r,rscbin,t)$[tmodel(t)$allow_cap_up(i,v,r,rscbin,t)$(not Sw_PCM)]..

    cap_cap_up(i,v,r,rscbin,t)

    =g=

    sum{tt$[(tmodel(tt) or tfix(tt))], INV_CAP_UP(i,v,r,rscbin,tt) }
;

* ---------------------------------------------------------------------------

*Energy upsizing limit
*   This uses rscbin to constrain hydropower upsizing using supply curve data.
eq_ener_up(i,v,r,rscbin,t)$[tmodel(t)$allow_ener_up(i,v,r,rscbin,t)$(not Sw_PCM)]..

    cap_ener_up(i,v,r,rscbin,t)

    =g=

    sum{tt$[(tmodel(tt) or tfix(tt))], INV_ENER_UP(i,v,r,rscbin,tt) }
;

* ---------------------------------------------------------------------------

* Prescribe power capacity
eq_forceprescription_power(pcat,r,t)
    $[tmodel(t)$force_pcat(pcat,t)$Sw_ForcePrescription
    $sum{(i,newv)$[prescriptivelink(pcat,i)], valinv(i,newv,r,t) }
    $(not Sw_PCM)]..

*capacity built in the current period or prior
    sum{(i,newv,tt)$[valinv(i,newv,r,tt)$prescriptivelink(pcat,i)
                     $(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))],
        INV(i,newv,r,tt) + INV_REFURB(i,newv,r,tt)$[refurbtech(i)$Sw_Refurb]}

    =e=

*must equal the cumulative prescribed amount
    sum{tt$[(yeart(tt)<=yeart(t))
            $(tmodel(tt) or tfix(tt))],
            noncumulative_prescriptions(pcat,r,tt)}

* plus any extra power buildouts (no penalty here - used as free slack)
* only on or after the first year the techs are available
    + EXTRA_PRESCRIP(pcat,r,t)$[yeart(t)>=firstyear_pcat(pcat)]

* or in regions where there is a offshore wind requirement
    + EXTRA_PRESCRIP(pcat,r,t)$[r_offshore(r,t)$sameas(pcat,'wind-ofs')
                               $(yeart(t)>=firstyear_RPS)
                               $sum{st$r_st(r,st), offshore_cap_req(st,t) }]
;

* ---------------------------------------------------------------------------

* Prescribe energy capacity
eq_forceprescription_energy(pcat,r,t)
    $[tmodel(t)$force_pcat(pcat,t)$Sw_ForcePrescription
    $sum{(i,newv)$[prescriptivelink(pcat,i)], valinv(i,newv,r,t) }
    $(not Sw_PCM)]..

*energy capacity built in the current period or prior
    sum{(i,newv,tt)$[valinv(i,newv,r,tt)$prescriptivelink(pcat,i)
                     $(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))
                     $battery(i)],
        INV_ENERGY(i,newv,r,tt)}

    =e=

*must equal the cumulative prescribed energy amount
    sum{tt$[(yeart(tt)<=yeart(t))
            $(tmodel(tt) or tfix(tt))],
            noncumulative_prescriptions_energy(pcat,r,tt)}

* plus any extra energy buildouts (no penalty here - used as free slack)
* only on or after the first year the techs are available
    + EXTRA_PRESCRIP_ENERGY(pcat,r,t)$[yeart(t)>=firstyear_pcat(pcat)]
;

* ---------------------------------------------------------------------------

*limit the amount of refurbishments available in specific year
*this is the sum of all previous year's investment that is now beyond the age
*limit (i.e. it has exited service) plus the amount of retired exogenous capacity
*that we begin with
eq_refurblim(i,r,t)$[tmodel(t)$refurbtech(i)$Sw_Refurb$(not Sw_PCM)]..

*investments that meet the refurbishment requirement (i.e. they've expired)
    sum{(vv,tt)$[m_refurb_cond(i,vv,r,t,tt)$(tmodel(tt) or tfix(tt))$valinv(i,vv,r,tt)],
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
    sum{(vv,tt)$[inv_cond(i,vv,r,t,tt)$(tmodel(tt) or tfix(tt))$valinv(i,vv,r,tt)],
         INV_REFURB(i,vv,r,tt)
       }
;

* ---------------------------------------------------------------------------

eq_rsc_inv_account(i,v,r,t)$[tmodel(t)$valinv(i,v,r,t)$rsc_i(i)$(not Sw_PCM)]..

  sum{rscbin$m_rscfeas(r,i,rscbin), INV_RSC(i,v,r,rscbin,t) }

  =e=

  INV(i,v,r,t)
;

* ---------------------------------------------------------------------------

*note that the following equation only restricts inv_rsc and not inv_refurb
*therefore, the capacity indicated by the supply curve may be limiting
*but the plant can still be refurbished
*Also note the flag_eq_rsc_INVlim--its calculation needs to be updated if this equation
*is changed
eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)
                            $rsc_i(i)
                            $m_rscfeas(r,i,rscbin)
                            $m_rsc_con(r,i)
                            $(not flag_eq_rsc_INVlim(r,i,rscbin,t))
                            $(not Sw_PCM)]..
*With water constraints, some RSC techs are expanded to include cooling technologies
*but the combination of m_rsc_con and rsc_agg allows for those investments
*to be limited by the numeraire techs' m_rsc_dat

*capacity indicated by the resource supply curve (scaled by rsc_capacity_scalar)
    m_rsc_dat(r,i,rscbin,"cap")$[not evmc(i)] * (
        1$[not rsc_capacity_scalar_i(i)] + rsc_capacity_scalar(i,r,t)$rsc_capacity_scalar_i(i))
* available hydro upgrade capacity
    + hyd_add_upg_cap(r,i,rscbin,t)$(Sw_HydroCapEnerUpgradeType=1)
* available EVMC capacity
    + rsc_evmc(i,r,"cap",rscbin,t)

    =g=

*must exceed the cumulative invested capacity in that region/class/bin...
    sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) <= yeart(t))$rsc_agg(i,ii)],
         INV_RSC(ii,v,r,rscbin,tt) * resourcescaler(ii) }

*plus exogenous (pre-start-year) capacity, using its level in the first year (tfirst)
    + sum{(ii,v,tt)$[tfirst(tt)$rsc_agg(i,ii)$exog_rsc(i)],
         capacity_exog_rsc(ii,v,r,rscbin,tt) }

;

* ---------------------------------------------------------------------------

eq_growthlimit_relative(i,st,t)$[sum{r$[r_st(r,st)], valinv_irt(i,r,t) }
                                $tmodel(t)
                                $stfeas(st)
                                $Sw_GrowthPenalties
                                $(yeart(t)<=Sw_GrowthPenLastYear)
                                $(yeart(t)>=model_builds_start_yr)
                                $(not Sw_PCM)]..

*the annual growth limit
     (yeart(t) - sum{tt$[tprev(t,tt)], yeart(tt) })
     * sum{gbin, GROWTH_BIN(gbin,i,st,t) }

    =g=

* must exceed the current periods investment
    sum{(v,r)$[valinv(i,v,r,t)$r_st(r,st)],
         INV(i,v,r,t) }
;

* ---------------------------------------------------------------------------

eq_growthbin_limit(gbin,st,tg,t)$[valinv_tg(st,tg,t)
                                 $tmodel(t)
                                 $stfeas(st)
                                 $Sw_GrowthPenalties
                                 $(yeart(t)<=Sw_GrowthPenLastYear)
                                 $(yeart(t)>=model_builds_start_yr)
                                 $(not Sw_PCM)]..

*the growth bin limit
     growth_bin_limit(gbin,st,tg,t)

    =g=

* must exceed the value in the growth bin
     sum{i$tg_i(tg,i), GROWTH_BIN(gbin,i,st,t) }
;

* ---------------------------------------------------------------------------

eq_growthlimit_absolute(tg,t)$[growth_limit_absolute(tg)$tmodel(t)
                               $Sw_GrowthAbsCon$(yeart(t)<=Sw_GrowthConLastYear)
                               $(yeart(t)>=model_builds_start_yr)
                               $(not Sw_PCM)]..

* the absolute limit of growth (in MW)
     (sum{tt$[tprev(tt,t)], yeart(tt) } - yeart(t))
     * growth_limit_absolute(tg)

     =g=

* must exceed the total investment
     sum{(i,v,r)$[valinv(i,v,r,t)$tg_i(tg,i)],
          INV(i,v,r,t) }
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
* must be >= the capacity of the hybrid resources (wind and solar) installed at site x
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
*this constraint does not apply to storage nor hybrid plant
*  limits for storage (including storage of hybrid plants) are tracked in eq_storage_capacity
*  limits for plant of Hybrid Plant are tracked in eq_plant_energy_balance
*  limits for hybrid techs with shared spur lines are treated in eq_capacity_limit_hybrid
eq_capacity_limit(i,v,r,h,t)
    $[tmodel(t)$valgen(i,v,r,t)
    $(not spur_techs(i))
    $(not storage_standalone(i))$(not storage_hybrid(i)$(not csp(i)))$(not nondispatch(i))]..
    
*total amount of dispatchable, non-hydro capacity
    avail(i,r,h)$[dispatchtech(i)$(not hydro_d(i))]
    * derate_geo_vintage(i,v)
    * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
    * CAP(i,v,r,t)

*total amount of dispatchable hydro capacity
    + avail(i,r,h)$hydro_d(i)
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
*add EVMC shape generation
    + (evmc_shape_gen(i,r,h) * CAP(i,v,r,t))

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
    sum{x$[x_r(x,r)$xfeas(x)], AVAIL_SITE(x,h,t)}

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

eq_curt_gen_balance(r,h,t)$tmodel(t)..

*total potential generation
    sum{(i,v)$[valcap(i,v,r,t)$(vre(i) or storage_hybrid(i)$(not csp(i)))$(not nondispatch(i))],
         m_cf(i,v,r,h,t) * CAP(i,v,r,t) }

*[minus] curtailed generation
    - CURT(r,h,t)$Sw_CurtMarket

    =g=

*must exceed realized generation; exclude hybrid plants
    sum{(i,v)$[valgen(i,v,r,t)$vre(i)$(not nondispatch(i))], GEN(i,v,r,h,t) }

*[plus] realized generation from hybrid plant
  + sum{(i,v)$[valgen(i,v,r,t)$storage_hybrid(i)$(not csp(i))$(not nondispatch(i))], GEN_PLANT(i,v,r,h,t) }$Sw_HybridPlant

*[plus] sum of operating reserves by type
    + sum{(ortype,i,v)$[Sw_OpRes$reserve_frac(i,ortype)$opres_h(h)$valgen(i,v,r,t)$vre(i)$(not nondispatch(i))$opres_model(ortype)],
          OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------
* Generation in each timeslice must be greater than mingen_fixed * available capacity
eq_mingen_fixed(i,v,r,h,t)
    $[Sw_MingenFixed$tmodel(t)$mingen_fixed(i)$valgen(i,v,r,t)
    $(yeart(t)>=Sw_StartMarkets)]..

    GEN(i,v,r,h,t)

    =g=

    mingen_fixed(i) * avail(i,r,h) *  CAP(i,v,r,t)
;

* ---------------------------------------------------------------------------

eq_mingen_lb(r,h,szn,t)$[h_szn(h,szn)$(yeart(t)>=this_year)
                        $tmodel(t)$Sw_Mingen]..

*minimum generation level in a season
    MINGEN(r,szn,t)

    =g=

*must be greater than the minimum generation level in each time slice in that season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)], GEN(i,v,r,h,t)  * minloadfrac(r,i,h) }
;

* ---------------------------------------------------------------------------

eq_mingen_ub(r,h,szn,t)$[h_szn(h,szn)$(yeart(t)>=this_year)
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

    sum{(v,h)$[valgen(i,v,r,t)$h_rep(h)], hours(h) * GEN(i,v,r,h,t) }

    =g=

    sum{v$valgen(i,v,r,t), CAP(i,v,r,t) } * sum{h$h_rep(h), hours(h) } * minCF(i,t)
;

* Maximum allowed daily capacity factor
eq_max_daily_cf(i,r,szn,t)$[maxdailycf(i,t)
                           $sum{h$h_szn(h,szn), avail(i,r,h)}
                           $tmodel(t)$valgen_irt(i,r,t)$Sw_MaxDailyCF]..

    sum{v$valgen(i,v,r,t), CAP(i,v,r,t) } * sum{h$h_szn(h,szn), hours(h) * avail(i,r,h) } * maxdailycf(i,t)

    =g=

    sum{(v,h)$[valgen(i,v,r,t)$h_szn(h,szn)], hours(h) * GEN(i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

* Seasonal energy constraint for dispatchable hydropower
eq_dhyd_dispatch(i,v,r,szn,t)
    $[tmodel(t)$hydro_d(i)$valgen(i,v,r,t)
    ]..

*seasonal hours [times] seasonal capacity factor [times] total hydro capacity [times] seasonal capacity adjustment
    sum{h$[h_szn(h,szn)], hours(h) }
    * (CAP(i,v,r,t) + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))],
               INV_ENER_UP(i,v,r,rscbin,tt)$allow_ener_up(i,v,r,rscbin,tt)
             - degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt)$allow_cap_up(i,v,r,rscbin,tt) })
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

* ---------------------------------------------------------------------------------------
* Limit near-term capacity deployments by tech and region based on interconnection queues
eq_interconnection_queues(tg,r,t)
    $[tmodel(t)$(yeart(t)>=model_builds_start_yr)
    $(sum{(tgg,rr), cap_limit(tgg,rr,t)})
    $sum{(i,newv)$tg_i(tg,i), valinv(i,newv,r,t)}
    $(not Sw_PCM)]..

* the capacity limit from the interconnection queue data
* (with CAP_ABOVE_LIM as a slack variable to address infeasibilities)
    cap_limit(tg,r,t) + CAP_ABOVE_LIM(tg,r,t)

    =g=

* must be greater than the total capacity deployed since the
* start of the interconnection queue data
    sum{(i,newv,tt)$[valinv(i,newv,r,tt)$tg_i(tg,i)
                                    $(yeart(tt)>=interconnection_start)
                                    $(tmodel(tt) or tfix(tt))],
        INV(i,newv,r,tt) + INV_REFURB(i,newv,r,tt)$[refurbtech(i)$Sw_Refurb] }
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
eq_supply_demand_balance(r,h,t)$tmodel(t)..

* generation from all land-based sources, including storage discharge
    sum{(i,v)$[valgen(i,v,r,t)$land(r)], GEN(i,v,r,h,t) }

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

* [minus] storage charging; not hybrid+storage
    - sum{(i,v)$[valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))], STORAGE_IN(i,v,r,h,t) }

* [minus] energy into storage for hybrid+storage from grid
    - sum{(i,v)$[valcap(i,v,r,t)$storage_hybrid(i)$(not csp(i))], STORAGE_IN_GRID(i,v,r,h,t) }$Sw_HybridPlant

* [plus] dropped/excess load ONLY if before Sw_StartMarkets
    + DROPPED(r,h,t)$[(yeart(t)<Sw_StartMarkets) or (Sw_PCM=1)]
    - EXCESS(r,h,t)$[(yeart(t)<Sw_StartMarkets) or (Sw_PCM=1)]

    =e=

* must equal demand
    LOAD(r,h,t)
;

* ---------------------------------------------------------------------------

eq_vsc_flow(r,h,t)
    $[tmodel(t)
    $Sw_VSC]..

* [plus] net VSC DC transmission with imports reduced by losses
    + sum{rr$routes(rr,r,"VSC",t), (1-tranloss(rr,r,"VSC")) * FLOW(rr,r,h,t,"VSC") }
    - sum{rr$routes(r,rr,"VSC",t), FLOW(r,rr,h,t,"VSC") }

* [plus] net VSC AC/DC conversion
    + (CONVERSION(r,h,"AC","VSC",t) * converter_efficiency_vsc)$val_converter(r,t)
    - (CONVERSION(r,h,"VSC","AC",t) / converter_efficiency_vsc)$val_converter(r,t)

* [plus] generation in offshore nodes/zones, which are assumed to use DC
* (Eventually it would be better to add an "energy carrier" index to directly represent
* DC generation.)
    + sum{(i,v)$[valgen(i,v,r,t)$offshore(r)], GEN(i,v,r,h,t) }

    =e=

* no direct consumption of DC power
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

* RAMPUP is used in the calculation of startup/ramping costs
* Because RAMPUP has a positive cost, RAMPUP will always either be 0
* when the RHS is negative, or will be exactly equal to the RHS when 
* the RHS is positive.
eq_ramping(i,r,h,hh,t)
    $[Sw_StartCost$tmodel(t)$startcost(i)$numhours_nexth(h,hh)$valgen_irt(i,r,t)]..

    RAMPUP(i,r,h,hh,t)

    =g=
    
    sum{v$valgen(i,v,r,t), GEN(i,v,r,hh,t) - GEN(i,v,r,h,t) }
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
    $[tmodel(t)$Sw_OpRes$opres_model(ortype)$opres_h(h)]..

*operating reserves from technologies that can produce them (i.e. those w/ramp rates)

    sum{(i,v)$[valgen(i,v,r,t)$reserve_frac(i,ortype)],
         OPRES(ortype,i,v,r,h,t) }

*[plus] net transmission of operating reserves (while including losses for imports)
    + sum{rr$opres_routes(rr,r,t), (1 - tranloss(rr,r,"AC")) * OPRES_FLOW(ortype,rr,r,h,t) }
    - sum{rr$opres_routes(r,rr,t), OPRES_FLOW(ortype,r,rr,h,t) }

*[plus] dropped load (operating reserves) ONLY if before Sw_StartMarkets
    + DROPPED(r,h,t)$[(yeart(t)<Sw_StartMarkets) or (Sw_PCM=1)]

    =g=

*must meet the demand for or type
*first portion is from load
    orperc(ortype,"or_load") * LOAD(r,h,t)

*next portion is from the wind generation
    + orperc(ortype,"or_wind") * sum{(i,v)$[wind(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) }

*final portion is from upv, and distpv capacity
*note that pv capacity is held at the balancing area
*include the hybrid PV+battery PV capacity here
    + orperc(ortype,"or_pv") * sum{(i,v)$[(pv(i) or pvb(i))$valcap(i,v,r,t)],
         CAP(i,v,r,t) / ilr(i) }$dayhours(h)
;

* ---------------------------------------------------------------------------

*=================================
* --- PLANNING RESERVE MARGIN ---
*=================================

* ---------------------------------------------------------------------------

*trade of planning reserve margin capacity cannot exceed the transmission line's available capacity
eq_PRMTRADELimit(r,rr,trtype,ccseason,t)
    $[tmodel(t)
    $routes(r,rr,trtype,t)
    $routes_prm(r,rr)
    $Sw_PRM_CapCredit
    $(not Sw_PCM)]..

*[plus] transmission capacity
    + CAPTRAN_PRM(r,rr,trtype,t) * sum{h$h_ccseason_prm(h,ccseason), (1 + trans_cap_delta(h,t)) }

    =g=

*[plus] firm capacity traded between regions
    + PRMTRADE(r,rr,trtype,ccseason,t)
;

* ---------------------------------------------------------------------------

eq_PRMTRADE_VSC(r,ccseason,t)
    $[tmodel(t)
    $Sw_PRM_CapCredit
    $Sw_VSC
    $(not Sw_PCM)]..

*[plus] net VSC DC imports - exports of firm capacity with imports reduced by losses
    + sum{rr$[routes(rr,r,"VSC",t)$routes_prm(rr,r)], (1-tranloss(rr,r,"VSC")) * PRMTRADE(rr,r,"VSC",ccseason,t) }
    - sum{rr$[routes(r,rr,"VSC",t)$routes_prm(r,rr)], PRMTRADE(r,rr,"VSC",ccseason,t) }

* [plus] net VSC AC/DC conversion
    + (CONVERSION_PRM(r,ccseason,"AC","VSC",t) * converter_efficiency_vsc)$val_converter(r,t)
    - (CONVERSION_PRM(r,ccseason,"VSC","AC",t) / converter_efficiency_vsc)$val_converter(r,t)

    =e=

* no direct contribution of VSC
    0
;

* ---------------------------------------------------------------------------

* binned power capacity for capacity credit must be the greater than power capacity
* (except for CSP, which is treated like VRE for capacity credit)
eq_cap_sdbin_balance(i,v,r,ccseason,t)
    $[tmodel(t)$valcap(i,v,r,t)$storage(i)$(not csp(i))$Sw_PRM_CapCredit$(not Sw_PCM)]..

*total capacity in each region
    bcr(i) * CAP(i,v,r,t)

    =g=

*sum of all binned capacity within each region
    sum{sdbin, CAP_SDBIN(i,v,r,ccseason,sdbin,t) }
;

* ---------------------------------------------------------------------------

* energy capacity must be greater than the binned value
eq_cap_sdbin_energy_balance(i,v,r,ccseason,t)
    $[tmodel(t)$valcap(i,v,r,t)$battery(i)$Sw_PRM_CapCredit]..

*total capacity in each region
    CAP_ENERGY(i,v,r,t)

    =g=

*sum of all binned capacity within each region
    sum{sdbin, CAP_SDBIN_ENERGY(i,v,r,ccseason,sdbin,t) }
;

* ---------------------------------------------------------------------------

* for each bin, binned energy capacity must equal to binned power capacity
* times bin duration
eq_sdbin_power_energy_link(i,v,r,ccseason,sdbin,t)
    $[tmodel(t)$valcap(i,v,r,t)$battery(i)$Sw_PRM_CapCredit]..

*binned energy capacity
    CAP_SDBIN_ENERGY(i,v,r,ccseason,sdbin,t)

    =e=

*binned power capacity times bin duration
    bin_duration(sdbin) * CAP_SDBIN(i,v,r,ccseason,sdbin,t)
;

* ---------------------------------------------------------------------------

*binned power capacity cannot exceed sdbin size
eq_sdbin_power_limit(ccreg,ccseason,sdbin,t)$[tmodel(t)$Sw_PRM_CapCredit]..

*sdbin size from CC script
    sdbin_size(ccreg,ccseason,sdbin,t)

    =g=

*standalone storage capacity in each sdbin adjusted by the appropriate CC value
    sum{(i,v,r)$[r_ccreg(r,ccreg)$valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))],
        CAP_SDBIN(i,v,r,ccseason,sdbin,t) * cc_storage(i,sdbin)
        }

*[plus] hybrid storage capacity in each sdbin adjusted by the appropriate CC value and the hybrid derate factor
    + sum{(i,v,r)$[r_ccreg(r,ccreg)
                 $valcap(i,v,r,t)$storage_hybrid(i)$(not csp(i))],
          CAP_SDBIN(i,v,r,ccseason,sdbin,t) * cc_storage(i,sdbin) * hybrid_cc_derate(i,r,ccseason,sdbin,t)
          }
;

* ---------------------------------------------------------------------------

eq_reserve_margin(r,ccseason,t)
    $[tmodel(t)$(yeart(t)>=model_builds_start_yr)
    $Sw_PRM_CapCredit
    $(not Sw_PCM)]..

* forced_retire is used here because forced_retire capacity is removed from valgen 
* but not valcap. It remains in valcap to allow for upgrades, but if it is not upgraged
* it should not be allowed to provide capacity to meet the reserve margin constraint.
* Because it can provide no services, it will either upgrade or retire.

*[plus] sum of all non-rsc and non-storage capacity
    + sum{(i,v)$[valcap(i,v,r,t)$(not vre(i))$(not hydro(i))$(not storage(i))$(not consume(i))$(not forced_retire(i,r,t))],
          CAP(i,v,r,t)
          * (1 + ccseason_cap_frac_delta(i,v,r,ccseason,t))
         }

*[plus] firm capacity from existing VRE or CSP
*only used in sequential solve case (otherwise cc_old = 0)
    + sum{i$[(vre(i) or csp(i) or pvb(i))$(not forced_retire(i,r,t))],
          cc_old(i,r,ccseason,t)
         }

*[plus] marginal capacity credit of VRE and csp times new investment
*only used in sequential solve case (otherwise m_cc_mar = 0)
*Note: new distpv is included with cc_old
    + sum{(i,v)$[(vre(i) or csp(i) or pvb(i))$valinv(i,v,r,t)$(not forced_retire(i,r,t))],
          m_cc_mar(i,r,ccseason,t) * (INV(i,v,r,t) + INV_REFURB(i,v,r,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] firm capacity contribution from all binned storage capacity
*battery, pumped-hydro, and CAES
*excludes hydro upgraded to add pumps
    + sum{(i,v,sdbin)$[(storage_standalone(i) or hyd_add_pump(i))$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          cc_storage(i,sdbin) * CAP_SDBIN(i,v,r,ccseason,sdbin,t)
         }
*hybrid PV+battery
    + sum{(i,v,sdbin)$[storage_hybrid(i)$(not csp(i))$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          cc_storage(i,sdbin) * hybrid_cc_derate(i,r,ccseason,sdbin,t) * CAP_SDBIN(i,v,r,ccseason,sdbin,t)
         }

*[plus] average capacity credit times capacity of VRE and storage
*used in rolling window and full intertemporal solve (otherwise cc_int = 0)
    + sum{(i,v)$[(vre(i) or storage(i))$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          cc_int(i,v,r,ccseason,t) * CAP(i,v,r,t)
         }

*[plus] excess capacity credit
*used in rolling window and full intertemporal solve when using marginals for cc_int (otherwise cc_excess = 0)
    + sum{i$[(vre(i) or storage(i))$(not forced_retire(i,r,t))],
          cc_excess(i,r,ccseason,t)
         }

*[plus] firm capacity of non-dispatchable hydro
* nb: hydro_nd generation does not fluctuate
* within a seasons set of hours
    + sum{(i,v,h)$[hydro_nd(i)$valgen(i,v,r,t)$h_ccseason_prm(h,ccseason)],
          GEN(i,v,r,h,t)
         }

*[plus] dispatchable hydro firm capacity
* include hydro upgraded to add pumps
    + sum{(i,v)$[(hydro_d(i) or hyd_add_pump(i))$valcap(i,v,r,t)$(not forced_retire(i,r,t))],
          CAP(i,v,r,t) * cap_hyd_ccseason_adj(i,ccseason,r) * (1 + hydro_capcredit_delta(i,t))
         }

*[plus] imports of firm capacity through AC and LCC DC lines
    + sum{(rr,trtype)$[routes(rr,r,trtype,t)$routes_prm(rr,r)$notvsc(trtype)],
          (1 - tranloss(rr,r,trtype)) * PRMTRADE(rr,r,trtype,ccseason,t)
         }

*[minus] exports of firm capacity through AC and LCC DC lines
    - sum{(rr,trtype)$[routes(r,rr,trtype,t)$routes_prm(r,rr)$notvsc(trtype)],
          PRMTRADE(r,rr,trtype,ccseason,t)
         }

*[plus] net AC/DC conversion of firm capacity through VSC converters
    + (CONVERSION_PRM(r,ccseason,"VSC","AC",t) * converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]
    - (CONVERSION_PRM(r,ccseason,"AC","VSC",t) / converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]

    =g=

*[plus] the peak demand times the planning reserve margin
    + (
        peakdem_static_ccseason(r,ccseason,t)

*         + PEAK_FLEX(r,ccseason,t)$Sw_EFS_flex

* [plus] only steam methane reforming technologies are assumed to increase peak demand
* contribution to peak demand based on weighted-average across timeslices in each ccseason
* [metric tons/hour] / [metric tons/MWh] * [hours] / [hours] = [MW]
     + (sum{(p,i,v,h)$[smr(i)$valcap(i,v,r,t)$frac_h_ccseason_weights(h,ccseason)
                     $(sameas(p,"H2"))$i_p(i,p)$(not sameas(i,"dac_gas"))$h_rep(h)],
            PRODUCE(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t)
            * hours(h) * frac_h_ccseason_weights(h,ccseason) }
        / sum{h$[frac_h_ccseason_weights(h,ccseason)$h_rep(h)],
              hours(h) * frac_h_ccseason_weights(h,ccseason) }
     )$Sw_Prod

      ) * (1 + prm(r,t))
;

* ---------------------------------------------------------------------------

*================================
* --- TRANSMISSION CAPACITY  ---
*================================

* DC transmission additions are assumed to add the same capacity in both directions
eq_INVTRAN_DC(r,rr,trtype,t)
    $[routes_inv(r,rr,trtype,t)
    $(not aclike(trtype))
    $tmodel(t)
    $(not Sw_PCM)]..

    INVTRAN(r,rr,trtype,t)

    =e=

    INVTRAN(rr,r,trtype,t)
;

* ---------------------------------------------------------------------------
* Added AC transmission capacity (INVTRAN) is determined by the cumulative capex invested
* in the interface (TRAN_CAPEX_BINS). This backwards approach is used because investment
* in the interface (corresponding to a particular upgraded line or transformer) can add a different
* amount of MW to the forward and reverse directions, and because the bins must be filled
* in order.
* This approach is only used for AC capacity; DC and B2B capacity additions are tracked directly.
* Defined only for interfaces (r < rr)
eq_INVTRAN_AC_forward(r,rr,tscbin,t)
    $[routes_inv(r,rr,"AC",t)
    $tmodel(t)
    $tsc_binwidth(r,rr,tscbin)
    $(not Sw_PCM)]..
* Transmission capacity additions [MW] times bin cost [$/MW] = [$]
    sum{tt
        $[(yeart(tt) <= yeart(t))
        $(tmodel(tt) or tfix(tt))
        $routes_inv(r,rr,"AC",tt)],
        INVTRAN_AC(r,rr,tscbin,tt) * tsc_forward(r,rr,tscbin)
    }

    =e=
* Cumulative transmission capacity investments: [$]
    TRAN_CAPEX_BINS(r,rr,tscbin,t)
;

* ---------------------------------------------------------------------------
* Defined only for interfaces (r < rr)
eq_INVTRAN_AC_reverse(r,rr,tscbin,t)
    $[routes_inv(r,rr,"AC",t)
    $tmodel(t)
    $tsc_binwidth(r,rr,tscbin)
    $(not Sw_PCM)]..
* Transmission capacity additions [MW] times bin cost [$/MW] = [$]
    sum{tt
        $[(yeart(tt) <= yeart(t))
        $(tmodel(tt) or tfix(tt))
        $routes_inv(r,rr,"AC",tt)],
        INVTRAN_AC(rr,r,tscbin,tt) * tsc_reverse(r,rr,tscbin)
    }

    =e=
* Cumulative transmission capacity investments: [$]
    TRAN_CAPEX_BINS(r,rr,tscbin,t)
;

* ---------------------------------------------------------------------------
* Defined for both directions (r < rr and r > rr)
eq_INVTRAN_AC(r,rr,t)
    $[routes_inv(r,rr,"AC",t)
    $tmodel(t)
    $(not Sw_PCM)]..

    INVTRAN(r,rr,"AC",t)

    =e=

    sum{tscbin, INVTRAN_AC(r,rr,tscbin,t) }
;

* ---------------------------------------------------------------------------
* AC transmission investment bins are limited by the transmission upgrade supply curve
* Defined only for interfaces (r < rr)
eq_TRAN_CAPEX_BINS(r,rr,tscbin,t)
    $[routes_inv(r,rr,"AC",t)
    $tmodel(t)
    $tsc_binwidth(r,rr,tscbin)
    $(not Sw_PCM)]..

    tsc_binwidth(r,rr,tscbin)

    =g=

    TRAN_CAPEX_BINS(r,rr,tscbin,t)
;

* ---------------------------------------------------------------------------
* Exogenous transmission investments are included in INVTRAN
* Defined for both directions (r < rr and r > rr)
eq_invtran_exog(r,rr,trtype,t)
    $[routes_inv(r,rr,trtype,t)
    $tmodel(t)
    $invtran_exog(r,rr,trtype,t)
    $(not Sw_PCM)]..

    INVTRAN(r,rr,trtype,t)

    =g=

    invtran_exog(r,rr,trtype,t)
;

* ---------------------------------------------------------------------------
* Transmission capacity accumulates capacity investments from years up to present
* Defined for both directions (r < rr and r > rr)
eq_CAPTRAN_ENERGY(r,rr,trtype,t)
    $[routes(r,rr,trtype,t)
    $tmodel(t)
    $(not Sw_PCM)]..

    CAPTRAN_ENERGY(r,rr,trtype,t)

    =e=

* [plus] initial transmission capacity
    + trancap_init_energy(r,rr,trtype)

* [plus] capacity additions up to and including the present year
    + sum{tt
          $[(yeart(tt) <= yeart(t))
          $(tmodel(tt) or tfix(tt))
          $routes_inv(r,rr,trtype,tt)],
          INVTRAN(r,rr,trtype,tt)
    }
;

* ---------------------------------------------------------------------------
* Transmission capacity for PRM trading (derated by Sw_TransInvPRMderate)
* accumulates capacity investments from years up to present.
* Defined for both directions (r < rr and r > rr)
eq_CAPTRAN_PRM(r,rr,trtype,t)
    $[routes(r,rr,trtype,t)
    $routes_prm(r,rr)
    $tmodel(t)
    $(not Sw_PCM)]..

    CAPTRAN_PRM(r,rr,trtype,t)

    =e=

* [plus] initial transmission capacity
    + trancap_init_prm(r,rr,trtype)

* [plus] capacity additions up to and including the present year,
* derated by Sw_TransInvPRMderate
    + sum{tt
          $[(yeart(tt) <= yeart(t))
          $(tmodel(tt) or tfix(tt))
          $routes_inv(r,rr,trtype,tt)],
          INVTRAN(r,rr,trtype,tt)
          * (1 - Sw_TransInvPRMderate)
    }
;

* ---------------------------------------------------------------------------

eq_prescribed_transmission(r,rr,trtype,t)
    $[routes_inv(r,rr,trtype,t)
    $tmodel(t)$(yeart(t)<firstyear_trans_nearterm)
    $(not Sw_PCM)]..

*all available transmission capacity expansion that is 'possible'
*note we allow for possible future transmission to accumulate
*hence the sum over all previous years
    sum{tt
        $[(tmodel(tt) or tfix(tt))
        $(yeart(tt)<=yeart(t))],
        trancap_fut(r,rr,"possible",trtype,tt)
    }

    =g=

*must exceed the additions for that interface
    sum{tt
        $[(tmodel(tt) or tfix(tt))
        $(yeart(tt)<=yeart(t))
        $routes_inv(r,rr,trtype,tt)],
        INVTRAN(r,rr,trtype,tt)
    }
;

* ---------------------------------------------------------------------------

* New point-of-interconnection (POI) intra-zone transmission capacity must be
* added for new generation capacity
eq_POI_cap(r,t)
    $[tmodel(t)
    $Sw_TransIntraCost
    $(not Sw_PCM)]..

* The sum of POI capacity...
    poi_cap_init(r)
    + sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))], INV_POI(r,tt) }

    =g=

* must be greater than the sum of all generation capacity [AC] without explicit spur lines...
    sum{(i,v)$[valcap(i,v,r,t)$(not spur_techs(i))], CAP(i,v,r,t) / ilr(i) }
* and spur-line capacity if explicitly tracked (use total capacity, not just new investments,
* to make sure we account for the existing spur line capacity already included in poi_cap_init)...
    + sum{x$[xfeas(x)$x_r(x,r)$Sw_SpurScen], CAP_SPUR(x,t) }
* and AC/DC converter capacity for VSC...
    + CAP_CONVERTER(r,t)
* and LCC (INVTRAN(r,rr) == INVTRAN(rr,r) for DC so only need to add one direction)
    + sum{(rr,tt)$[routes_inv(r,rr,"LCC",t)$(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))],
          INVTRAN(r,rr,"LCC",tt)
    }
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
    + sum{ortype$[Sw_OpRes$opres_h(h)$aclike(trtype)$opres_routes(r,rr,t)$opres_model(ortype)],
          OPRES_FLOW(ortype,r,rr,h,t) * opres_mult }
;

* ---------------------------------------------------------------------------

*capacity transmission is equal to the exogenously-specified level of transmission
*plus the investment in transmission capacity
eq_CAPTRAN_GRP(transgrp,transgrpp,t)
    $[tmodel(t)
    $Sw_TransGroupContraint
    $sum{(r,rr), routes_transgroup(transgrp,transgrpp,r,rr) }
    $(not Sw_PCM)]..

    CAPTRAN_GRP(transgrp,transgrpp,t)

    =e=

* [plus] initial transmission capacity, which is defined separately for each direction
    + trancap_init_transgroup(transgrp,transgrpp,"AC")

* [plus] capacity additions up to and including the present year,
* derated by Sw_TransGroupDerate
    + sum{(r,rr,tt)
          $[(yeart(tt) <= yeart(t))
          $(tmodel(tt) or tfix(tt))
          $routes_inv(r,rr,"AC",tt)
          $routes_transgroup(transgrp,transgrpp,r,rr)],
          INVTRAN(r,rr,"AC",tt)
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

eq_transgrp_limit_prm(transgrp,transgrpp,ccseason,t)
    $[tmodel(t)
    $Sw_PRM_CapCredit
    $Sw_TransGroupContraint
    $sum{(r,rr), routes_transgroup(transgrp,transgrpp,r,rr) }
    $(not Sw_PCM)]..

    CAPTRAN_GRP(transgrp,transgrpp,t)
    * sum{h$h_ccseason_prm(h,ccseason), (1 + trans_cap_delta(h,t)) }

    =g=

    sum{(r,rr)$routes_transgroup(transgrp,transgrpp,r,rr),
        PRMTRADE(r,rr,"AC",ccseason,t) }
;

* ---------------------------------------------------------------------------

*capacity transmission is equal to the exogenously-specified level of transmission
*plus the investment in transmission capacity between ITL groups for county/mixed
eq_CAPTRAN_ITL(itlgrp,itlgrpp,t)
    $[tmodel(t)
    $Sw_itlgrpConstraint
    $sum{(r,rr), routes_itlgrp(itlgrp,itlgrpp,r,rr) }
    $(not Sw_PCM)]..

    CAPTRAN_ITL(itlgrp,itlgrpp,t)

    =e=

* [plus] initial transmission capacity (from bas), which is defined separately for each direction
    + trancap_init_itlgrp(itlgrp,itlgrpp,"AC")

* [plus] capacity additions up to and including the present year
    + sum{(r,rr,tt)
          $[(yeart(tt) <= yeart(t))
          $(tmodel(tt) or tfix(tt))
          $routes_inv(r,rr,"AC",tt)
          $routes_itlgrp(itlgrp,itlgrpp,r,rr)],
          INVTRAN(r,rr,"AC",tt)
    }
;

* ---------------------------------------------------------------------------

eq_itlgrp_limit_energy(itlgrp,itlgrpp,h,t)
    $[tmodel(t)
    $Sw_itlgrpConstraint
    $sum{(r,rr), routes_itlgrp(itlgrp,itlgrpp,r,rr)}]..

    CAPTRAN_ITL(itlgrp,itlgrpp,t) * (1 + trans_cap_delta(h,t))

    =g=

    sum{(r,rr)$routes_itlgrp(itlgrp,itlgrpp,r,rr),
        FLOW(r,rr,h,t,"AC") }
;

* ---------------------------------------------------------------------------

eq_itlgrp_limit_prm(itlgrp,itlgrpp,ccseason,t)
    $[tmodel(t)
    $Sw_PRM_CapCredit
    $Sw_itlgrpConstraint
    $sum{(r,rr), routes_itlgrp(itlgrp,itlgrpp,r,rr) }
    $(not Sw_PCM)]..

    CAPTRAN_ITL(itlgrp,itlgrpp,t)
    * sum{h$h_ccseason_prm(h,ccseason), (1 + trans_cap_delta(h,t)) }

    =g=

    sum{(r,rr)$routes_itlgrp(itlgrp,itlgrpp,r,rr),
        PRMTRADE(r,rr,"AC",ccseason,t) }
;

* ---------------------------------------------------------------------------

* NERC regions are only allowed to import firm capacity up to their limit
eq_firm_transfer_limit(nercr,h,t)
    $[tmodel(t)
    $Sw_PRM_NetImportLimit
    $h_stress(h)]..

* max net import fraction [.] * peak demand by NERC region [MW]
    firm_import_limit(nercr,t) * peakload_nercr(nercr,t)

    =g=

* net transmission imports (i.e. minus exports) accounting for losses on imports
* imports [MW]
    + sum{(r,rr,trtype,nercrr)
          $[routes(rr,r,trtype,t)$routes_prm(rr,r)$routes_nercr(nercrr,nercr,rr,r)],
          FLOW(rr,r,h,t,trtype) * (1 - tranloss(rr,r,trtype)) }
* exports [MW]
    - sum{(r,rr,trtype,nercrr)
          $[routes(r,rr,trtype,t)$routes_prm(r,rr)$routes_nercr(nercr,nercrr,r,rr)],
          FLOW(r,rr,h,t,trtype) }
;

* ---------------------------------------------------------------------------

* NERC regions are only allowed to import firm capacity up to their limit
eq_firm_transfer_limit_cc(nercr,ccseason,t)
    $[tmodel(t)
    $Sw_PRM_NetImportLimit
    $Sw_PRM_CapCredit
    $(not Sw_PCM)]..

* max net import fraction [.] * peak demand by ccseason [MW]
    firm_import_limit(nercr,t)
    * sum{r$r_nercr(r,nercr), peakdem_static_ccseason(r,ccseason,t) }

    =g=

* net transmission imports (i.e. minus exports) accounting for losses on imports
* imports [MW]
    + sum{(r,rr,trtype,nercrr)
          $[routes(rr,r,trtype,t)$routes_prm(rr,r)$routes_nercr(nercrr,nercr,rr,r)],
          PRMTRADE(rr,r,trtype,ccseason,t) * (1 - tranloss(rr,r,trtype)) }
* exports [MW]
    - sum{(r,rr,trtype,nercrr)
          $[routes(r,rr,trtype,t)$routes_prm(r,rr)$routes_nercr(nercr,nercrr,r,rr)],
          PRMTRADE(r,rr,trtype,ccseason,t) }
;

* ---------------------------------------------------------------------------

* CAP_CONVERTER accumulates INV_CONVERTER from years <= t
eq_CAP_CONVERTER(r,t)
    $[tmodel(t)
    $val_converter(r,t)
    $Sw_VSC
    $(not Sw_PCM)]..

    CAP_CONVERTER(r,t)

    =e=

    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))],
          INV_CONVERTER(r,tt) }
;

* ---------------------------------------------------------------------------

* CAP_SPUR accumulates INV_SPUR from years <= t
eq_CAP_SPUR(x,t)
    $[Sw_SpurScen
    $tmodel(t)
    $(not Sw_PCM)]..

    CAP_SPUR(x,t)

    =e=

    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))],
          INV_SPUR(x,tt) }
;

* ---------------------------------------------------------------------------

* AC/DC conversion cannot exceed the converter capacity
eq_CONVERSION_limit_energy(r,h,t)
    $[tmodel(t)
    $val_converter(r,t)
    $Sw_VSC]..

    CAP_CONVERTER(r,t)

    =g=

    CONVERSION(r,h,"AC","VSC",t) + CONVERSION(r,h,"VSC","AC",t)
;

* ---------------------------------------------------------------------------

* AC/DC PRM conversion cannot exceed the converter capacity
eq_CONVERSION_limit_prm(r,ccseason,t)
    $[tmodel(t)
    $val_converter(r,t)
    $Sw_PRM_CapCredit
    $Sw_VSC
    $(not Sw_PCM)]..

    CAP_CONVERTER(r,t)

    =g=

    CONVERSION_PRM(r,ccseason,"AC","VSC",t) + CONVERSION_PRM(r,ccseason,"VSC","AC",t)
;

* ---------------------------------------------------------------------------

* Limit the annual transmission investment to trans_inv_max
eq_transmission_investment_max(t)
    $[tmodel(t)
    $trans_inv_max(t)
    $Sw_TransInvMaxTypes
    $(not Sw_PCM)]..

* Sw_TransInvMax [TWmile/year] * [1e6 MW / 1 TW] * [year/solvestep]
    trans_inv_max(t) * 1e6 * (yeart(t) - sum{tt$[tprev(t,tt)], yeart(tt) })

    =g=

* Interzonal transmission: Average the forward and reverse directions
    + sum{(r,rr,trtype)$routes_inv(r,rr,trtype,t),
          (INVTRAN(r,rr,trtype,t) + INVTRAN(rr,r,trtype,t)) / 2
          * distance(r,rr,trtype) }
* Spur lines + network reinforcement
    + sum{(i,v,r,rscbin)
          $[((Sw_TransInvMaxTypes=2) or (Sw_TransInvMaxTypes=3))
          $valinv(i,v,r,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)],
          INV_RSC(i,v,r,rscbin,t) * (
              distance_reinforcement(i,r,rscbin)
              + distance_spur(i,r,rscbin)$(Sw_TransInvMaxTypes=3)
          )
    }
;

* ---------------------------------------------------------------------------

* Limit the total transmission capacity of each interface trtype to captran_max [MW]
eq_CAPTRAN_max(r,rr,trtype,t)
    $[tmodel(t)$Sw_TransCapMaxEachType
    $routes(r,rr,trtype,t)$trtypemax(trtype)
    $(not Sw_PCM)]..

    Sw_TransCapMaxEachType * 1000

    =g=

    CAPTRAN_ENERGY(r,rr,trtype,t)
;

* ---------------------------------------------------------------------------

* Limit the total transmission capacity of each interface to captran_max,
* summed over all transmission types [MW]
eq_CAPTRAN_max_total(r,rr,t)
    $[tmodel(t)$Sw_TransCapMaxAllTypes
    $sum{trtype$trtypemax(trtype), routes(r,rr,trtype,t) }
    $(not Sw_PCM)]..

    Sw_TransCapMaxAllTypes * 1000

    =g=

    sum{trtype$trtypemax(trtype), CAPTRAN_ENERGY(r,rr,trtype,t) }
;

* ---------------------------------------------------------------------------

* Limit the total VSC AC/DC converter capacity in each BA to captran_max
eq_converter_max(r,t)
    $[tmodel(t)
    $val_converter(r,t)
    $Sw_VSC
    $Sw_VSC_ConverterMax
    $(not Sw_PCM)]..

    Sw_VSC_ConverterMax

    =g=

    CAP_CONVERTER(r,t)
;

* ---------------------------------------------------------------------------
* Disallow transmission flows from land to offshore zones
eq_offshore_no_backflow(r,rr,trtype,h,t)
    $[tmodel(t)
    $routes(r,rr,trtype,t)
    $land(r)
    $offshore(rr)
    $(not Sw_OffshoreBackflow)]..

    FLOW(r,rr,h,t,trtype) =e= 0 ;

* ---------------------------------------------------------------------------

*=========================
* --- EMISSION POLICIES ---
*=========================

* ---------------------------------------------------------------------------

* Because EMIT is only evaluated for emit_modeled, the full emissions need to be
* calculated in the e_report rather than relying on the EMIT variable
eq_emit_accounting(etype,e,r,t)$[emit_modeled(e,r,t)$tmodel(t)]..

    EMIT(etype,e,r,t)

    =e=

    sum{(i,v,h)$[valgen(i,v,r,t)$h_rep(h)],
        hours(h) * emit_rate(etype,e,i,v,r,t)
        * (GEN(i,v,r,h,t)
           + CCSFLEX_POW(i,v,r,h,t)$[ccsflex(i)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)])
       }

* Plus emissions produced via production activities (SMR, SMR-CCS, DAC)
* The "production" of negative CO2 emissions via DAC is also included here
    + sum{(p,i,v,h)$[valcap(i,v,r,t)$i_p(i,p)$h_rep(h)],
          hours(h) * prod_emit_rate(etype,e,i,t)
          * PRODUCE(p,i,v,r,h,t)
         }

*[minus] co2 reduce from flexible CCS capture
*capture = capture per energy used by the ccs system * CCS energy

* Flexible CCS - bypass
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_byp(i)$h_rep(h)],
        ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POW(i,v,r,h,t) }) $[sameas(e,"co2")]$Sw_CCSFLEX_BYP

* Flexible CCS - storage
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_sto(i)$h_rep(h)],
        ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POWREQ(i,v,r,h,t) }) $[sameas(e,"co2")]$Sw_CCSFLEX_STO
;

* ---------------------------------------------------------------------------

eq_RGGI_cap(t)$[tmodel(t)$(yeart(t)>=RGGI_start_yr)$Sw_RGGI]..

    RGGI_cap(t)

    =g=

    sum{r$RGGI_r(r), EMIT("process","CO2",r,t) } 
;

* ---------------------------------------------------------------------------

eq_state_cap(st,t)
    $[tmodel(t)
    $(yeart(t)>=state_cap_start_yr)
    $sum{tt, state_cap(st,tt) }
    $Sw_StateCap]..

    state_cap(st,t)

    =g=

    sum{r$r_st(r,st), EMIT("process","CO2",r,t) }

* Import emissions intensity is taken from the previous solve year.
* Here the receiving regions (r) are the cap regions and the sending
* regions (rr) are those that have connection with cap regions.
    + sum{(h,r,rr,trtype)
          $[r_st(r,st)$(not r_st(rr,st))$routes(rr,r,trtype,t)
          $h_rep(h)
* If there is a national zero-carbon cap in the present year,
* set emissions intensity of imports to zero.
          $(not ((Sw_AnnualCap>0) and not emit_cap("CO2",t) and not emit_cap("CO2e",t)))],
          hours(h) * FLOW(rr,r,h,t,trtype)
          * sum{tt$tprev(t,tt), co2_emit_rate_r(rr,tt) }
    }
;

* ---------------------------------------------------------------------------

* traded emissions among states in each trading group need
* to be less than the sum of all the state caps within that trading group
eq_CSAPR_Budget(csapr_group,t)$[Sw_CSAPR$tmodel(t)$(yeart(t)>=csapr_startyr)]..

*the accumulation of states csapr cap for the budget category
    sum{st$[stfeas(st)$csapr_group_st(csapr_group,st)], csapr_cap(st,"budget",t) }

    =g=

*must exceed the summed-over-state hourly-weighted nox emissions by csapr group
    sum{st$csapr_group_st(csapr_group,st),
      sum{(i,v,h,r)$[r_st(r,st)$valgen(i,v,r,t)$h_rep(h)],
         h_weight_csapr(h) * hours(h) * emit_rate("process","NOX",i,v,r,t) * GEN(i,v,r,h,t)
       }
      }
;

* ---------------------------------------------------------------------------

* along with the cap on trading groups, each state has
* a maximum amount of NOX emissions during ozone season
eq_CSAPR_Assurance(st,t)$[stfeas(st)$(yeart(t)>=csapr_startyr)
                         $csapr_cap(st,"Assurance",t)$tmodel(t)]..

*the state level assurance cap
    csapr_cap(st,"assurance",t)

    =g=

*must exceed the csapr-hourly-weighted nox emissions by state
    sum{(i,v,h,r)$[r_st(r,st)$valgen(i,v,r,t)$h_rep(h)],
      h_weight_csapr(h) * hours(h) * emit_rate("process","NOX",i,v,r,t) * GEN(i,v,r,h,t)
    }
;

* ---------------------------------------------------------------------------
* This constraint has no input data and is currently unused
eq_emit_rate_limit(e,r,t)$[emit_rate_con(e,r,t)$tmodel(t)]..

    emit_rate_limit(e,r,t) * (
         sum{(i,v,h)$[valgen(i,v,r,t)$h_rep(h)],  hours(h) * GEN(i,v,r,h,t) }
    )

    =g=

    EMIT("process",e,r,t) + EMIT("upstream",e,r,t)$Sw_Upstream
;

* ---------------------------------------------------------------------------
* This equation enforces emission caps for both the CO2 (Sw_AnnualCap = 1) 
* and CO2e emission (Sw_AnnualCap =2 or Sw_AnnualCap =3) scenarios 
eq_annual_cap(eall,t)$[sum{tt, emit_cap(eall,tt) }$tmodel(t)$(Sw_AnnualCap>0)]..

* exogenous CO2 cap (Sw_AnnualCap = 1) or CO2e cap (Sw_AnnualCap > 1)
    emit_cap(eall,t)

    =g=

* must exceed annual endogenous emissions by CO2 pollutant (when Sw_AnnualCap=1) or CO2e pollutants (CO2, CH4, NO2 pollutants when Sw_AnnualCap=2 and additional H2 leakage when Sw_AnnualCap=3)
    sum{(e,r)$emit_capped(e), (EMIT("process",e,r,t) + EMIT("upstream",e,r,t)$Sw_Upstream) * gwp(e) }    
;

* ---------------------------------------------------------------------------

eq_bankborrowcap(e)$[Sw_BankBorrowCap$sum{t, emit_cap(e,t) }]..

*weighted exogenous emissions
    sum{t$[tmodel(t)$emit_cap(e,t)],
        yearweight(t) * emit_cap(e,t) }

    =g=

* must exceed weighted endogenous emissions
    sum{(r,t)$[tmodel(t)$emit_cap(e,t)],
        yearweight(t) * (EMIT("process",e,r,t) + EMIT("upstream",e,r,t)$Sw_Upstream)}
;

* ---------------------------------------------------------------------------

eq_cdr_cap(t)
    $[tmodel(t)
    $(Sw_AnnualCap>0)
    $Sw_NoFossilOffsetCDR]..

*** GHG emissions from fossil CCS...
* CO2 emissions from fossil CCS...
    + sum{(i,v,r,h)$[valgen(i,v,r,t)$ccs(i)$(not beccs(i))$h_rep(h)$(Sw_AnnualCap<2)],
            hours(h) * GEN(i,v,r,h,t) * (emit_rate("process","CO2",i,v,r,t) + emit_rate("upstream","CO2",i,v,r,t)$Sw_Upstream) }
* GHG emissions * global warming potential
    + sum{(i,v,r,h)$[valgen(i,v,r,t)$ccs(i)$(not beccs(i))$h_rep(h)$(Sw_AnnualCap>=2)],
        hours(h) * GEN(i,v,r,h,t) * sum{e, (emit_rate("process",e,i,v,r,t) + emit_rate("upstream",e,i,v,r,t)$Sw_Upstream) * gwp(e) } }      
    =g=

*** ...must be greater than emissions offset by CDR (negative emissions so negative signs here)
** DAC
    - sum{(p,i,v,r,h)$[valcap(i,v,r,t)$i_p(i,p)$dac(i)$sameas(p,"DAC")$h_rep(h)],
          hours(h) * (prod_emit_rate("process","CO2",i,t) + prod_emit_rate("upstream","CO2",i,t)$Sw_Upstream) * PRODUCE(p,i,v,r,h,t) }
** BECCS
    - sum{(i,v,r,h)$[valgen(i,v,r,t)$beccs(i)$h_rep(h)],
        hours(h) * (emit_rate("process","CO2",i,v,r,t) + emit_rate("upstream","CO2",i,v,r,t)$Sw_Upstream) * GEN(i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

*Under the Clean Air Act Section 111, new gas plants (CCs or CTs) can operate above caa_gas_max_cf percent before caa_coal_retire_year 
*During and after caa_coal_retire_year, they need to either A) operate at <= caa_gas_max_cf percent CF, B) upgrade with CCS or C) retire
eq_caa_max_cf(i,v,r,t)$[tmodel(t)$valgen(i,v,r,t)
                        $gas(i)$(not ccs(i))
                        $heat_rate(i,v,r,t)
                        $(firstyear_v(i,v)>=caa_first_year)
                        $(yeart(t)>=caa_coal_retire_year)
                        $Sw_Clean_Air_Act]..

*fraction of annual generation capacity
    sum{h$h_rep(h), hours(h)} * caa_gas_max_cf * CAP(i,v,r,t)


    =g=

*must exceed total annual generation
    sum{h$h_rep(h), hours(h) * GEN(i,v,r,h,t)}
;

* ---------------------------------------------------------------------------

*Under the Clean Air Act Section 111, the emissions from existing coal plants per state must be less than or equal to a rate-based emissions standard

*The rate is equivalent to average coal CCS emissions assuming 90% capture rate [metric tons CO2 / MWh]
eq_caa_rate_standard(st,t)$[tmodel(t)
                        $(yeart(t)>=caa_coal_retire_year)
                        $Sw_Clean_Air_Act]..

*rate equivalent to average coal CCS emissions assuming 90% capture rate [metric tons CO2 / MWh]
    caa_rate_emis_standard 

*coal generation in that state [MWh]
    * sum{(i,v,r,h)$[valgen(i,v,r,t)$coal(i)$(not cofire(i))$r_st(r,st)], 
         GEN(i,v,r,h,t)}
    =g= 

*coal emissions in that state [metric tons CO2]
    sum{(i,v,r,h)$[valgen(i,v,r,t)$coal(i)$(not cofire(i))$r_st(r,st)], 
         GEN(i,v,r,h,t) * emit_rate("process","CO2",i,v,r,t)}
;

*==========================
* --- RPS CONSTRAINTS ---
*==========================

* ---------------------------------------------------------------------------

eq_REC_Generation(RPSCat,i,st,t)$[stfeas(st)$(not tfirst(t))$tmodel(t)
                                 $Sw_StateRPS$(yeart(t)>=firstyear_RPS)
                                 $(not sameas(RPSCat,"RPS_Bundled"))
                                 $(not sameas(RPSCat,"CES_Bundled"))
                                 $RecTech(RPSCat,i,st,t)
                                 ]..

*RECS are computed as the total annual generation from a technology
*hydro is the only technology adjusted by RPSTechMult
*because GEN can only generate a H2 PTC credit or a REC, not both, subtract out the generation which produces a hydrogen PTC credit
*because GEN from pvb(i) includes grid charging, subtract out its grid charging
    + sum{(v,r,h)$[valgen(i,v,r,t)$r_st(r,st)$h_rep(h)],
          RPSTechMult(RPSCat,i,st) * hours(h)
          * (GEN(i,v,r,h,t) 
          - CREDIT_H2PTC(i,v,r,h,t)$[valgen_h2ptc(i,v,r,t)$Sw_H2_PTC] 
          - (STORAGE_IN_GRID(i,v,r,h,t) * storage_eff_pvb_g(i,t))$[storage_hybrid(i)$(not csp(i))$Sw_HybridPlant] )
         }

     =g=

* Generation must be greater than RECS sent to all states that can trade
    + sum{ast$[RecMap(i,RPSCat,st,ast,t)$(stfeas(ast) or sameas(ast,"voluntary"))],
          RECS(RPSCat,i,st,ast,t) }
* RPS_Bundled RECS and RPS_All RECS can meet the same requirement
* therefore lumping them together to avoid double-counting
    + sum{ast$[RecMap(i,"RPS_Bundled",st,ast,t)$stfeas(ast)$(not sameas(st,ast))],
          RECS("RPS_Bundled",i,st,ast,t) }$[sameas(RPSCat,"RPS_All")]

*same logic as bundled RPS RECS is applied to the bundled CES RECS
    + sum{ast$[RecMap(i,"CES_Bundled",st,ast,t)$stfeas(ast)$(not sameas(st,ast))],
          RECS("CES_Bundled",i,st,ast,t) }$[sameas(RPSCat,"CES")]
;

* ---------------------------------------------------------------------------

* note that the bundled rpscat can be included
* to comply with the RPS_All categeory
* but it is not in itself explicit requirement
eq_REC_Requirement(RPSCat,st,t)$[RecPerc(RPSCat,st,t)$(not tfirst(t))
                                $tmodel(t)$Sw_StateRPS$(yeart(t)>=firstyear_RPS)
                                $(stfeas(st) or sameas(st,"voluntary"))
                                $(not sameas(RPSCat,"RPS_Bundled"))
                                $(not sameas(RPSCat,"CES_Bundled"))]..

* RECs owned (i.e. imported and generated/used in state minus exports)
    + sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)],
         RECS(RPSCat,i,ast,st,t) }
    - sum{(i,ast)$[RecMap(i,RPSCat,st,ast,t)$stfeas(ast)$(not sameas(st,ast))],
         RECS(RPSCat,i,st,ast,t) }

* bundled RECS can also be used to meet the RPS_All requirements (imports minus exports)
    + sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(ast,st))],
         RECS("RPS_Bundled",i,ast,st,t) }$[sameas(RPSCat,"RPS_All")]
    - sum{(i,ast)$[RecMap(i,"RPS_Bundled",st,ast,t)$stfeas(ast)$(not sameas(st,ast))],
         RECS("RPS_Bundled",i,st,ast,t) }$[sameas(RPSCat,"RPS_All")]

* bundled CES credits can also be used to meet the CES requirements (imports minus exports)
    + sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(ast,st))],
         RECS("CES_Bundled",i,ast,st,t) }$[sameas(RPSCat,"CES")]
    - sum{(i,ast)$[RecMap(i,"CES_Bundled",st,ast,t)$stfeas(ast)$(not sameas(st,ast))],
         RECS("CES_Bundled",i,st,ast,t) }$[sameas(RPSCat,"CES")]

* ACP credits can also be purchased
    + ACP_PURCHASES(rpscat,st,t)$(not acp_disallowed(st,RPSCat))

* Exports to Canada are assumed to be clean, and therefore consume CES credits
    - sum{(r,h)$[r_st(r,st)$h_rep(h)],
          can_exports_h(r,h,t) * hours(h) }$[(Sw_Canada=1)$sameas(RPSCat,"CES")]

    =g=

* note here we do not pre-define the rec requirement since load_exog(r,h,t)
* changes when sent to/from the demand side
    RecPerc(RPSCat,st,t) * sum{(r,h)$[r_st_rps(r,st)$h_rep(h)], hours(h) * (
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
          - (distloss * GEN(i,v,r,h,t))$(distpv(i))
          - (STORAGE_IN_GRID(i,v,r,h,t) * storage_eff_pvb_g(i,t))$[storage_hybrid(i)$(not csp(i))$Sw_HybridPlant] }
          - can_exports_h(r,h,t)$[(Sw_Canada=1)$sameas(RPSCat,"CES")]
        )$(RecStyle(st,RPSCat)=2)
    )}
;

* ---------------------------------------------------------------------------

eq_REC_BundleLimit(RPSCat,st,ast,t)$[stfeas(st)$stfeas(ast)$tmodel(t)
                              $(not sameas(st,ast))$Sw_StateRPS
                              $(sum{i,RecMap(i,RPSCat,st,ast,t) })
                              $(sameas(RPSCat,"RPS_Bundled") or sameas(RPSCat,"CES_Bundled"))
                              $(yeart(t)>=firstyear_RPS)]..

*amount of net transmission flows from state st to state ast
    sum{(h,r,rr,trtype)$[r_st(r,st)$r_st(rr,ast)$routes(r,rr,trtype,t)$h_rep(h)],
          hours(h) * FLOW(r,rr,h,t,trtype)
      }

    =g=
* must be greater than bundled RECS
    sum{i$RecMap(i,RPSCat,st,ast,t),
        RECS(RPSCat,i,st,ast,t) }
;

* ---------------------------------------------------------------------------

eq_REC_unbundledLimit(RPSCat,st,t)$[st_unbundled_limit(RPScat,st)$tmodel(t)$stfeas(st)
                            $(yeart(t)>=firstyear_RPS)$Sw_StateRPS
                            $(sameas(RPSCat,"RPS_All") or sameas(RPSCat,"CES"))]..
*the limit on unbundled RECS times the REC requirement (based on end-use sales)
      REC_unbundled_limit(RPSCat,st,t) * RecPerc(RPSCat,st,t) *
        sum{(r,h)$[r_st(r,st)$h_rep(h)],
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

eq_REC_ooslim(RPSCat,st,t)$[RecPerc(RPSCat,st,t)$(yeart(t)>=firstyear_RPS)
                           $RPS_oosfrac(st)$stfeas(st)$tmodel(t)$Sw_StateRPS
                           $(not sameas(RPSCat,"RPS_Bundled"))
                           $(not sameas(RPSCat,"CES_Bundled"))]..

*the fraction of imported recs times the requirement (based on end-use sales)
    RPS_oosfrac(st) * RecPerc(RPSCat,st,t) *
        sum{(r,h)$[r_st(r,st)$h_rep(h)],
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
eq_REC_launder(RPSCat,st,t)$[RecStates(RPSCat,st,t)$(not tfirst(t))$(yeart(t)>=firstyear_RPS)
                               $tmodel(t)$stfeas(st)$Sw_StateRPS
                               $(not sameas(RPSCat,"RPS_Bundled"))
                               $(not sameas(RPSCat,"CES_Bundled"))]..

*in-state REC generation
    + sum{(i,v,r,h)$[valgen(i,v,r,t)$RecTech(RPSCat,i,st,t)$r_st(r,st)$h_rep(h)],
          hours(h) * (GEN(i,v,r,h,t) - CREDIT_H2PTC(i,v,r,h,t)$[valgen_h2ptc(i,v,r,t)$Sw_H2_PTC])
         }

*minus ACP_PURCHASES with a 10x multiplier (the multiplier discourages the model from
*exporting RECs when it is buying ACP credits)
    - ACP_PURCHASES(RPSCat,st,t)$(not acp_disallowed(st,RPSCat)) * 10

    =g=

*exported RECS - NB the conditional that st!=ast
    + sum{(i,ast)$[RecMap(i,RPSCat,st,ast,t)$(stfeas(ast) or sameas(ast,"voluntary"))$(not sameas(st,ast))],
          RECS(RPSCat,i,st,ast,t) }

    + sum{(i,ast)$[RecMap(i,"RPS_Bundled",st,ast,t)$stfeas(ast)$(not sameas(st,ast))],
          RECS("RPS_Bundled",i,st,ast,t)
       }$sameas(RPSCat,"RPS_All")

    + sum{(i,ast)$[RecMap(i,"CES_Bundled",st,ast,t)$stfeas(ast)$(not sameas(st,ast))],
          RECS("CES_Bundled",i,st,ast,t)
       }$sameas(RPSCat,"CES")

;

* ---------------------------------------------------------------------------

eq_RPS_OFSWind(st,t)$[tmodel(t)$stfeas(st)$offshore_cap_req(st,t)$Sw_StateRPS
                      $sum{(i,v,r)$[r_st(r,st)$ofswind(i)], valcap(i,v,r,t) }
                      $(yeart(t)>=firstyear_RPS)$(not Sw_PCM)]..

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

eq_batterymandate(st,t)
    $[tmodel(t)$batterymandate(st,t)$(yeart(t)>=firstyear_battery)
    $Sw_BatteryMandate
    $(not Sw_PCM)]..
*battery capacity
    sum{(i,v,r)$[r_st(r,st)$valcap(i,v,r,t)$(battery(i) or pvb(i))], bcr(i) * CAP(i,v,r,t) }

    =g=

*must be greater than the required level
    batterymandate(st,t)
;

* ---------------------------------------------------------------------------

eq_national_gen(t)$[tmodel(t)$national_gen_frac(t)$Sw_GenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[nat_gen_tech_frac(i)$valgen(i,v,r,t)$h_rep(h)],
        GEN(i,v,r,h,t) * hours(h) * nat_gen_tech_frac(i) }

    =g=

*must exceed the mandated percentage [times]
    national_gen_frac(t) * (

* if Sw_GenMandate = 1, then apply the fraction to the bus bar load
    (
* load
    sum{(r,h)$h_rep(h), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[routes(rr,r,trtype,t)$h_rep(h)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)$h_rep(h)], STORAGE_IN(i,v,r,h,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)$h_rep(h)], GEN(i,v,r,h,t) * hours(h) }
    )$[Sw_GenMandate = 1]

* if Sw_GenMandate = 2, then apply the fraction to the end use load
    + (sum{(r,h)$h_rep(h),
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
eq_gasused(cendiv,h,t)$[tmodel(t)$((Sw_GasCurve=0) or (Sw_GasCurve=3))]..

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

    sum{fuelbin, VGASBINQ_REGIONAL(fuelbin,cendiv,t) }

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
eq_storage_capacity(i,v,r,h,t)$[valgen(i,v,r,t)
    $(storage_standalone(i)$(not evmc_storage(i))
        or evmc_storage(i)
            $[evmc_storage_charge_frac(i,r,h,t)$evmc_storage_discharge_frac(i,r,h,t)]
        or storage_hybrid(i)$(not csp(i)))
    $tmodel(t)]..

* [plus] Capacity of all storage technologies
    (CAP(i,v,r,t) * bcr(i) * avail(i,r,h)
       * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
    )$valcap(i,v,r,t)

    =g=

* [plus] Generation from storage, excluding hybrid+storage and adjusting evmc_storage for time-varying discharge (deferral) availability
    GEN(i,v,r,h,t)$(not storage_hybrid(i)$(not csp(i))) / (1$(not evmc_storage(i)) + evmc_storage_discharge_frac(i,r,h,t)$evmc_storage(i))

* [plus] Generation from battery of hybrid+storage
    + GEN_STORAGE(i,v,r,h,t)$[storage_hybrid(i)$(not csp(i))$Sw_HybridPlant]

* [plus] Storage charging
* excludes hybrid plant+storage and adjusting evmc_storage for time-varying charge (add back deferred EV load) availability
    + STORAGE_IN(i,v,r,h,t)$[not storage_hybrid(i)$(not csp(i))] / (1$(not evmc_storage(i)) + evmc_storage_charge_frac(i,r,h,t)$evmc_storage(i)) 
   
* hybrid+storage plant: plant generation
    + STORAGE_IN_PLANT(i,v,r,h,t)$[storage_hybrid(i)$(not csp(i))$dayhours(h)$Sw_HybridPlant]
* hybrid+storage plant: Grid generation
    + STORAGE_IN_GRID(i,v,r,h,t)$[storage_hybrid(i)$(not csp(i))$Sw_HybridPlant]

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
*  When inter-day linkage is used, the nexth will be disabled, and this equation will
*  be used to calculate intra-day storage dispatch for further inter-day linkage use.
eq_storage_level(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)$tmodel(t)]..

*[plus] storage level in h+1
    sum{(hh)$[nexth(h,hh)], STORAGE_LEVEL(i,v,r,hh,t)}$(not storage_interday(i))

*[plus] the net dispatch of inter-day storage technologies
    + STORAGE_INTERDAY_DISPATCH(i,v,r,h,t)$(storage_interday(i)) * hours_daily(h)

    =e=

* only want to include storage_level from periods that have had a previous storage_level
* otherwise it becomes a free variable, implying you can charge storage without bound
    STORAGE_LEVEL(i,v,r,h,t)$(not storage_interday(i))

*[plus] storage charging
    + storage_eff(i,t) *  hours_daily(h) * (
*energy into stand-alone storage (not CSP-TES) and hydropower that adds pumping
          STORAGE_IN(i,v,r,h,t)$[storage_standalone(i) or hyd_add_pump(i)]

*energy into storage from CSP field
        + (CAP(i,v,r,t) * csp_sm(i) * m_cf(i,v,r,h,t)
          )$[CSP_Storage(i)$valcap(i,v,r,t)]
      )
*[plus] water inflow energy available for hydropower that adds pumping
    + (CAP(i,v,r,t) * avail(i,r,h) * hours_daily(h) *
        sum{szn$h_szn(h,szn), m_cf_szn(i,v,r,szn,t) }
        )$hyd_add_pump(i)

*[plus] energy into hybrid plant storage
*hybrid+storage plant: plant charging
    + storage_eff_pvb_p(i,t) * hours_daily(h)
      * STORAGE_IN_PLANT(i,v,r,h,t)$[storage_hybrid(i)$(not csp(i))$dayhours(h)$Sw_HybridPlant]

*hybrid+storage plant: grid charging
    + storage_eff_pvb_g(i,t) * hours_daily(h) 
      * STORAGE_IN_GRID(i,v,r,h,t)$[storage_hybrid(i)$(not csp(i))$Sw_HybridPlant]

*[minus] generation from stand-alone storage (discharge) and CSP
*exclude hybrid+storage plant because GEN refers to output from both the plant and the battery
    - hours_daily(h) * GEN(i,v,r,h,t)$[not storage_hybrid(i)$(not csp(i))]

*[minus] Generation from Battery (discharge) of hybrid+storage plant
    - hours_daily(h) * GEN_STORAGE(i,v,r,h,t) $[storage_hybrid(i)$(not csp(i))$Sw_HybridPlant]

*[minus] losses from reg reserves (only half because only charging half
*the time while providing reg reserves)
    - (hours_daily(h)
       * (OPRES("reg",i,v,r,h,t)$[Sw_OpRes=1] + OPRES("combo",i,v,r,h,t)$[Sw_OpRes=2])
       * (1 - storage_eff(i,t)) / 2 * reg_energy_frac
    )$[opres_h(h)]
;

* ---------------------------------------------------------------------------

*there must be sufficient energy in storage to provide operating reserves
eq_storage_opres(i,v,r,h,t)
    $[valgen(i,v,r,t)$tmodel(t)$Sw_OpRes$opres_h(h)
    $(storage_standalone(i) or storage_hybrid(i)$(not csp(i)) or hyd_add_pump(i))]..

*[plus] initial storage level
    STORAGE_LEVEL(i,v,r,h,t)

*[minus] generation that occurs during this timeslice
    - hours_daily(h) * GEN(i,v,r,h,t) $[not storage_hybrid(i)$(not csp(i))]

*[minus] generation that occurs during this timeslice
    - hours_daily(h) * GEN_STORAGE(i,v,r,h,t) $[storage_hybrid(i)$(not csp(i))$Sw_HybridPlant]

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
                               $storage(i)
                               $tmodel(t)
                               $(not storage_interday(i))]..

* [plus] storage duration times storage capacity for fixed-duration techs
    storage_duration(i) * CAP(i,v,r,t) * (1$CSP_Storage(i) + 1$psh(i) + bcr(i)$pvb(i))

* [plus] EVMC storage has time-varying energy capacity
    + evmc_storage_energy_hours(i,r,h,t) * CAP(i,v,r,t) * (bcr(i)$evmc_storage(i))

* [plus] battery storage capacity
    + CAP_ENERGY(i,v,r,t)$battery(i)

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
* for evmc_storage this adjust for time-varying availability of charging (add back deferred EV load)
    avail(i,r,h) * storinmaxfrac(i,v,r)
    * CAP(i,v,r,t)
    * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
    * (1$(not evmc_storage(i)) + evmc_storage_charge_frac(i,r,h,t)$evmc_storage(i))

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
* for batteries
* when power capacity is built, energy capacity must be greater than the minimum duration
eq_battery_minduration(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$battery(i)]..

    CAP_ENERGY(i,v,r,t)

    =g=

    minbatteryduration * CAP(i,v,r,t)
;

* ---------------------------------------------------------------------------

* Constraints for building inter-day storage linkage
* The storage level at hour 0 of next partition
* equals to the storage level at hour 0 of current partition
* plus number of period of current partition multiply by storage net change of the rep period
eq_storage_interday_level(i,v,r,allszn,t)$[valgen(i,v,r,t)$storage_interday(i)$tmodel(t)$numpartitions(allszn)]..
    
    sum{allsznn$[nextpartition(allszn,allsznn)],STORAGE_INTERDAY_LEVEL(i,v,r,allsznn,t)}

    =e=

    STORAGE_INTERDAY_LEVEL(i,v,r,allszn,t) 
    
    + numpartitions(allszn)
    * sum{(szn)$[szn_actualszn(szn,allszn)$numpartitions(allszn)],
          sum{h$[h_szn(h,szn)], (STORAGE_INTERDAY_DISPATCH(i,v,r,h,t) * hours_daily(h))}}
;

* ---------------------------------------------------------------------------

* Constraints for building inter-day storage linkage
* Define the maximum relative soc on a representative period compared to its hour 0
* It's noted that STORAGE_INTERDAY_LEVEL_MAX_DAY can be nagative since it represent a relative value
eq_storage_interday_level_max_day(i,v,r,szn,h,t)$[valgen(i,v,r,t)$storage_interday(i)$tmodel(t)$h_szn(h,szn)]..
    
    STORAGE_INTERDAY_LEVEL_MAX_DAY(i,v,r,szn,t)

    =g=

    sum{(hh)$[h_preh(h,hh)], (STORAGE_INTERDAY_DISPATCH(i,v,r,hh,t) * hours_daily(h))}
;

* ---------------------------------------------------------------------------

* Constraints for building inter-day storage linkage
* Define the minimum relative soc on a representative period compared to its hour 0
* It's noted that STORAGE_INTERDAY_LEVEL_MIN_DAY can be nagative since it represent a relative value
eq_storage_interday_level_min_day(i,v,r,szn,h,t)$[valgen(i,v,r,t)$storage_interday(i)$tmodel(t)$h_szn(h,szn)]..
    
    sum{(hh)$[h_preh(h,hh)], (STORAGE_INTERDAY_DISPATCH(i,v,r,hh,t) * hours_daily(h))}

    =g=

    STORAGE_INTERDAY_LEVEL_MIN_DAY(i,v,r,szn,t)
;

* ---------------------------------------------------------------------------

* Constraints for building inter-day storage linkage
* For all partitions, the soc at their hour 0 plus minimum soc of first period should greater than 0
* This is to make sure not only their hour 0 but also the lowest point of the first period of each partition is greater than 0
eq_storage_interday_min_level_start(i,v,r,allszn,t)$[valgen(i,v,r,t)$storage_interday(i)$tmodel(t)$numpartitions(allszn)]..

    STORAGE_INTERDAY_LEVEL(i,v,r,allszn,t)
    
    + sum{(szn)$[szn_actualszn(szn,allszn)], STORAGE_INTERDAY_LEVEL_MIN_DAY(i,v,r,szn,t)}

    =g=

    0
;

* ---------------------------------------------------------------------------

* Constraints for building inter-day storage linkage
* For all partitions, the soc at their hour 0 plus minimum soc of last period should greater than 0
* This is to make sure not only their hour 0 but also the lowest point of the last period of each partition is greater than 0
eq_storage_interday_min_level_end(i,v,r,allszn,t)$[valgen(i,v,r,t)$storage_interday(i)$tmodel(t)$numpartitions(allszn)]..

    STORAGE_INTERDAY_LEVEL(i,v,r,allszn,t)

    + (numpartitions(allszn) - 1) 
    * sum{(szn)$[szn_actualszn(szn,allszn)], 
        sum{h$[h_szn(h,szn)], (STORAGE_INTERDAY_DISPATCH(i,v,r,h,t) * hours_daily(h))}}
    
    + sum{(szn)$[szn_actualszn(szn,allszn)], STORAGE_INTERDAY_LEVEL_MIN_DAY(i,v,r,szn,t)}

    =g=

    0
;

* ---------------------------------------------------------------------------

* Constraints for building inter-day storage linkage
* For all partitions, the soc at their hour 0 plus maximum soc of first period should lower than total storage capacity
* This is to make sure not only their hour 0 but also the highest point of the first period of each partition is lower than maximum capacity
eq_storage_interday_max_level_start(i,v,r,allszn,t)$[valgen(i,v,r,t)$storage_interday(i)$tmodel(t)$numpartitions(allszn)]..
    
* Fixed-duration storage
    storage_duration(i) * CAP(i,v,r,t)$(not battery(i))
* Variable-duration storage
    + CAP_ENERGY(i,v,r,t)$battery(i)

    =g=
    
    STORAGE_INTERDAY_LEVEL(i,v,r,allszn,t)
    
    + sum{(szn)$[szn_actualszn(szn,allszn)], STORAGE_INTERDAY_LEVEL_MAX_DAY(i,v,r,szn,t)}
;

* ---------------------------------------------------------------------------

* Constraints for building inter-day storage linkage
* For all partitions, the soc at their hour 0 plus maximum soc of last period should lower than total storage capacity
* This is to make sure not only their hour 0 but also the highest point of the last period of each partition is greater than maximum capacity
eq_storage_interday_max_level_end(i,v,r,allszn,t)$[valgen(i,v,r,t)$storage_interday(i)$tmodel(t)$numpartitions(allszn)]..
    
    storage_duration(i) * CAP(i,v,r,t)$(not battery(i))

    + CAP_ENERGY(i,v,r,t)$battery(i)

    =g=
    
    STORAGE_INTERDAY_LEVEL(i,v,r,allszn,t)

    + (numpartitions(allszn) - 1) 
    * sum{(szn)$[szn_actualszn(szn,allszn)], 
        sum{h$[h_szn(h,szn)], (STORAGE_INTERDAY_DISPATCH(i,v,r,h,t) * hours_daily(h))}}
    
    + sum{(szn)$[szn_actualszn(szn,allszn)], STORAGE_INTERDAY_LEVEL_MAX_DAY(i,v,r,szn,t)}
;

* ---------------------------------------------------------------------------

*===============================
* --- Hybrid Plant ---
*===============================

* ---------------------------------------------------------------------------

*Generation post curtailment =
*   + generation from hybrid storage plant + generation from storage - storage charging from hybrid storage plant
eq_plant_total_gen(i,v,r,h,t)$[storage_hybrid(i)$(not csp(i))$tmodel(t)$valgen(i,v,r,t)$Sw_HybridPlant]..

    + GEN_PLANT(i,v,r,h,t)

    + GEN_STORAGE(i,v,r,h,t)

*[minus] charging from hybrid storage plant
    - STORAGE_IN_PLANT(i,v,r,h,t)$dayhours(h)

    =e=

    GEN(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

*Energy to storage from hybrid storage palnt + hybrid storage plant generation <= hybrid storage plant maximum production for a resource
*capacity factor is adjusted to include inverter losses, clipping losses, and low voltage losses
eq_hybrid_plant_energy_limit(i,v,r,h,t)$[storage_hybrid(i)$(not csp(i))$tmodel(t)$valgen(i,v,r,t)$valcap(i,v,r,t)$Sw_HybridPlant]..

* [plus] plant output
    m_cf(i,v,r,h,t) * CAP(i,v,r,t)

    =g=

*[plus] charging from hybrid plant
    + STORAGE_IN_PLANT(i,v,r,h,t)$dayhours(h)

*[plus] generation from hybrid plant
    + GEN_PLANT(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

*Energy moving through the inverter cannot exceed the inverter capacity
eq_plant_capacity_limit(i,v,r,h,t)$[storage_hybrid(i)$(not csp(i))$tmodel(t)$valgen(i,v,r,t)$valcap(i,v,r,t)$Sw_HybridPlant]..

*[plus] inverter capacity [AC] = panel capacity [DC] / ILR [DC/AC]
    + CAP(i,v,r,t) / ilr(i)

    =g=

* [plus] Output from plant
    + GEN_PLANT(i,v,r,h,t)

* [plus] Output form storage
    + GEN_STORAGE(i,v,r,h,t)

*[plus] battery charging from grid
    + STORAGE_IN_GRID(i,v,r,h,t)

*[plus] battery operating reserves
    + sum{ortype$[Sw_OpRes$opres_h(h)$opres_model(ortype)], OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

*Total energy charged from local PV >= ITC qualification fraction * total energy charged

eq_pvb_itc_charge_reqt(i,v,r,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$pvb_itc_qual_frac$Sw_PVB]..

* [plus] battery charging from PV
    + sum{h$[dayhours(h)$h_rep(h)], STORAGE_IN_PLANT(i,v,r,h,t) * hours(h) }

    =g=

    + pvb_itc_qual_frac * (

* [plus] battery charging from PV
    + sum{h$[dayhours(h)$h_rep(h)], STORAGE_IN_PLANT(i,v,r,h,t) * hours(h) }

* [plus] battery charging from Grid
    + sum{h$h_rep(h), STORAGE_IN_GRID(i,v,r,h,t) * hours(h) }
    )
;

* ---------------------------------------------------------------------------

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
eq_water_accounting(i,v,w,r,h,t)$[i_water(i)$valgen(i,v,r,t)$h_rep(h)$tmodel(t)$Sw_WaterMain]..

    WAT(i,v,w,r,h,t)

    =e=

*division by 1E6 to convert gal of water_rate(i,w) to Mgal
    GEN(i,v,r,h,t) * hours(h) * water_rate(i,w) / 1E6
;

* ---------------------------------------------------------------------------

*total water access is determined by total capacity
eq_water_capacity_total(i,v,r,t)$[tmodel(t)$valcap(i,v,r,t)
                                 $(i_water_cooling(i) or psh(i))$Sw_WaterMain$Sw_WaterCapacity]..

    WATCAP(i,v,r,t)

    =e=

*require enough water capacity to allow 100% capacity factor (8760 hour operation)
*division by 1E6 to convert gal of water_rate(i,w) to Mgal
    sum{h$h_rep(h), hours(h)
    * sum{w$i_w(i,w),
           CAP(i,v,r,t) * water_rate(i,w) }
    * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
    } / 1E6

*require enough water capacity to fill PSH reservoir.
*uses investment so that term is only applied in the single investment year
*   as a proxy for water needs during construction phase.
    + sum{rscbin$[m_rscfeas(r,i,rscbin)$psh(i)], INV_RSC(i,v,r,rscbin,t) * water_req_psh(r,rscbin) }$Sw_PSHwatercon
;

* ---------------------------------------------------------------------------

*total water access must not exceed supply
eq_water_capacity_limit(wst,r,t)$[tmodel(t)$Sw_WaterMain$Sw_WaterCapacity]..

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

eq_prod_capacity_limit(i,v,r,h,t)
    $[tmodel(t)
    $consume(i)
    $valcap(i,v,r,t)
    $Sw_Prod
    $h_rep(h)]..

* available capacity [times] the conversion rate of metric ton / MW
    CAP(i,v,r,t) * avail(i,r,h)
            * (prod_conversion_rate(i,v,r,t)$[not sameas(i,"dac_gas")]
                + 1$sameas(i,"dac_gas"))
            * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})

    =g=

* production in that timeslice
    sum{p$i_p(i,p), PRODUCE(p,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

* H2 demand balance; national and annual. Active only when Sw_H2=1.
eq_h2_demand(p,t)$[(sameas(p,"H2"))$tmodel(t)$(yeart(t)>=h2_demand_start)$(Sw_H2=1)]..

* annual metric tons of production
    sum{(i,v,r,h)$[h2(i)$valcap(i,v,r,t)$i_p(i,p)$h_rep(h)],
        PRODUCE(p,i,v,r,h,t) * hours(h) }

    =e=

* annual demand
    h2_exogenous_demand(p,t)

* assuming here that h2 production and use in H2_COMBUSTION can be temporally asynchronous
* that is, the hydrogen does not need to produced in the same hour it is consumed by h2-ct/cc's
    + sum{(i,v,r,h)$[valgen(i,v,r,t)$h2_combustion(i)$h_rep(h)],
            GEN(i,v,r,h,t) * hours(h) * h2_combustion_intensity * heat_rate(i,v,r,t)
    }
;

* ---------------------------------------------------------------------------

* H2 demand balance; regional and by timeslice w/ H2 transport network and storage.
* Active only when Sw_H2=2 [metric tons/hour]
eq_h2_demand_regional(r,h,t)
    $[tmodel(t)$(Sw_H2=2)$(yeart(t)>=h2_demand_start)$h_rep(h)]..

* endogenous supply of hydrogen
    sum{(i,v,p)$[h2(i)$valcap(i,v,r,t)$i_p(i,p)],
        PRODUCE(p,i,v,r,h,t) }
    
* net hydrogen trade with imports reduced by H2 transmission losses
    + sum{rr$h2_routes(rr,r), H2_FLOW(rr,r,h,t) } * (1 - h2_tranloss)
    - sum{rr$h2_routes(r,rr), H2_FLOW(r,rr,h,t) }
        
* net storage injections / withdrawls in a BA
    + sum{h2_stor$[h2_stor_r(h2_stor,r)], H2_STOR_OUT(h2_stor,r,h,t)}
    - sum{h2_stor$[h2_stor_r(h2_stor,r)], H2_STOR_IN(h2_stor,r,h,t)}

    =e=

* annual demand in [metric tons/hour]
    sum{p, h2_exogenous_demand_regional(r,p,h,t) }

* region-specific H2 consumption from H2-CT/CCs
* [MW] * [metric ton/MMBtu] * [MMBtu/MWh] = [metric tons/hour]
    + sum{(i,v)$[valgen(i,v,r,t)$h2_combustion(i)],
            GEN(i,v,r,h,t) * h2_combustion_intensity * heat_rate(i,v,r,t)
       }
;

* ---------------------------------------------------------------------------

eq_h2_transport_caplimit(r,rr,h,t)$[h2_routes(r,rr)$(Sw_H2=2)
                                    $tmodel(t)$(yeart(t)>=h2_demand_start)]..

*capacity computed as cumulative investments of h2 pipelines up to the current year
    sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))
           $(yeart(tt)>=h2_demand_start)],
        H2_TRANSPORT_INV(r,rr,tt)$h2_routes_inv(r,rr) 
        + H2_TRANSPORT_INV(rr,r,tt)$h2_routes_inv(rr,r) }

    =g=

*bi-directional flow of h2
    H2_FLOW(rr,r,h,t) + H2_FLOW(r,rr,h,t)
;

* ---------------------------------------------------------------------------

* link H2 storage level between timeslices of actual periods, or hours when running a chronological year
eq_h2_storage_level(h2_stor,r,actualszn,h,t)
    $[tmodel(t)$(yeart(t)>=h2_demand_start)$(Sw_H2_StorTimestep=2)
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
    $[tmodel(t)$(yeart(t)>=h2_demand_start)$(Sw_H2_StorTimestep=1)
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

* H2 storage capacity [metric tons]
eq_h2_storage_capacity(h2_stor,r,t)
    $[tmodel(t)$(Sw_H2=2)
    $h2_stor_r(h2_stor,r)$(yeart(t)>=h2_demand_start)
    $(not Sw_PCM)]..

* [metric tons]
    sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))],
        H2_STOR_INV(h2_stor,r,tt)}

    =e=

* [metric tons]
    H2_STOR_CAP(h2_stor,r,t)
;

* ---------------------------------------------------------------------------

eq_h2_min_storage_cap(r,t)$[tmodel(t)$(Sw_H2=2)$Sw_H2_MinStorHours$(not Sw_PCM)]..

* [metric tons]
    sum{h2_stor$h2_stor_r(h2_stor,r), H2_STOR_CAP(h2_stor,r,t) }

    =g=

* [MW] * [MMBtu/MWh] * [metric tons/MMBtu] * [hours] = [metric tons]
    sum{(i,v)$[h2_combustion(i)$valcap(i,v,r,t)],
        CAP(i,v,r,t) * heat_rate(i,v,r,t) * h2_combustion_intensity * Sw_H2_MinStorHours
    }
;

* ---------------------------------------------------------------------------

* H2 storage investment capacity
* [metric tons/hour]
eq_h2_storage_flowlimit(h2_stor,r,h,t)
    $[tmodel(t)
    $(Sw_H2=2)
    $h2_stor_r(h2_stor,r)
    $(yeart(t)>=h2_demand_start)
    $h_rep(h)]..

*storage capacity computed as cumulative investments of H2 storage up to the current year
*H2 storage costs estimated for a fixed duration, so using this to link storage capacity and injection rates
* [metric tons] / [hours] = [metric tons/hour]
    H2_STOR_CAP(h2_stor,r,t) / h2_storage_duration

    =g=

*H2 storage injection [metric tons/hour]
    H2_STOR_IN(h2_stor,r,h,t)

*[plus] H2 storage withdrawal [metric tons/hour]
    + H2_STOR_OUT(h2_stor,r,h,t)
;

* ---------------------------------------------------------------------------

* total level of H2 storage cannot exceed storage investment for all days 
* [metric tons]
eq_h2_storage_caplimit(h2_stor,r,actualszn,h,t)
    $[tmodel(t)$(yeart(t)>=h2_demand_start)$(Sw_H2_StorTimestep=2)
    $h2_stor_r(h2_stor,r)$(Sw_H2=2)$h_actualszn(h,actualszn)]..

* total storage investment [metric tons]
    H2_STOR_CAP(h2_stor,r,t)

    =g=

* storage level of H2 [metric tons]
    H2_STOR_LEVEL(h2_stor,r,actualszn,h,t)
;

* ---------------------------------------------------------------------------

* total level of H2 storage at the beginning of the day cannot exceed storage investment
* [metric tons]
eq_h2_storage_caplimit_szn(h2_stor,r,actualszn,t)
    $[tmodel(t)$(yeart(t)>=h2_demand_start)$(Sw_H2_StorTimestep=1)
    $h2_stor_r(h2_stor,r)$(Sw_H2=2)]..

* total storage investment [metric tons]
    H2_STOR_CAP(h2_stor,r,t)

    =g=

* storage level of H2 [metric tons]
    H2_STOR_LEVEL_SZN(h2_stor,r,actualszn,t)
;

* ---------------------------------------------------------------------------

* Hydrogen production tax credit - before h2_ptc_temporal_match_year, electric generation must occur in the same 
* region ('h2ptcreg' level) and year that the electrolyzer produces the hydrogen, to qualify for the credit
eq_h2_ptc_region_balance(h2ptcreg,t)$[tmodel(t)
                            $h2_ptc_years(t)
                            $(yeart(t)>=h2_demand_start)
                            $(Sw_H2_PTC)
                            $(yeart(t)<h2_ptc_temporal_match_year)
                            ]..

* generation from clean technologies which qualify to receive hydrogen production tax credits [MW]
    sum{(i,v,r,h)$[r_h2ptcreg(r,h2ptcreg)$hours(h)$h_rep(h)$valgen_h2ptc(i,v,r,t)], CREDIT_H2PTC(i,v,r,h,t)}

    =e=

* amount of generation needed to produce hydrogen via electrolysis in that year [MW]
    sum{(v,r,h)$[r_h2ptcreg(r,h2ptcreg)$valcap("electrolyzer",v,r,t)$hours(h)$prod_conversion_rate("electrolyzer",v,r,t)],
        PRODUCE("H2","electrolyzer",v,r,h,t) / prod_conversion_rate("electrolyzer",v,r,t) }
;

* ---------------------------------------------------------------------------

* Hydrogen production tax credit - after and in h2_ptc_temporal_match_year, electric generation must occur in the same 
* region ('h2ptcreg' level), hour and year that the electrolyzer produces the hydrogen, to qualify for the credit
eq_h2_ptc_region_hour_balance(h2ptcreg,h,t)$[hours(h)$tmodel(t)
                                $h_rep(h)
                                $h2_ptc_years(t)
                                $(yeart(t)>=h2_demand_start)
                                $(Sw_H2_PTC)
                                $(yeart(t)>=h2_ptc_temporal_match_year)
                                ]..

* generation from clean technologies which qualify to receive hydrogen production tax credits [MW]
    sum{(i,v,r)$[r_h2ptcreg(r,h2ptcreg)$valgen_h2ptc(i,v,r,t)], CREDIT_H2PTC(i,v,r,h,t)}

    =e=

* amount of generation needed to produce hydrogen via electrolysis [MW]
    sum{(v,r)$[r_h2ptcreg(r,h2ptcreg)$valcap("electrolyzer",v,r,t)$prod_conversion_rate("electrolyzer",v,r,t)],
       PRODUCE("H2","electrolyzer",v,r,h,t) / prod_conversion_rate("electrolyzer",v,r,t) }
;

* ---------------------------------------------------------------------------

* Hydrogen production tax credit - total generation must be greater than generation going towards electrolyzers to receive the tax credit
eq_h2_ptc_creditgen(i,v,r,h,t)$[valgen_h2ptc(i,v,r,t)
                            $h_rep(h)
                            $tmodel(t)
                            $Sw_H2_PTC
                            $h2_ptc_years(t)
                            $(yeart(t)>=h2_demand_start)]..

* total generation [MW]
    GEN(i,v,r,h,t)

    =g=

* generation going towards electrolyzers to receive the tax credit [MW]
    CREDIT_H2PTC(i,v,r,h,t)     
;

* ---------------------------------------------------------------------------


*=================================
* -- CO2 transport and storage --
*=================================


eq_co2_capture(r,h,t)
    $[tmodel(t)
    $Sw_CO2_Detail
    $(yeart(t)>=co2_detail_startyr)
    $h_rep(h)]..

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

eq_co2_sink(r,h,t)$[tmodel(t)$Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]..

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

* must exceed metric tons per hour entering storage
    sum{r$r_cs(r,cs), CO2_STORED(r,cs,h,t) }
;

* ---------------------------------------------------------------------------

eq_co2_cumul_limit(cs,t)$[tmodel(t)$Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)$csfeas(cs)]..

*capacity by co2 bin for injections
    co2_storage_limit(cs)

    =g=

*cumulative amount stored over time
    sum{(r,h,tt)
        $[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))$(yeart(tt)>=co2_detail_startyr)
        $r_cs(r,cs)$h_rep(h)],
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

eq_ccsflex_sto_ccsenergy_limit_szn(i,v,r,szn,t)$[tmodel(t)$valgen(i,v,r,t)$ccsflex_sto(i)$szn_rep(szn)$Sw_CCSFLEX_STO]..
  sum{h$h_szn(h,szn), hours(h) * CCSFLEX_POW(i,v,r,h,t)} =l= ccsflex_powlim(i,t) * sum{h$h_szn(h,szn), hours(h) * (GEN(i,v,r,h,t) + CCSFLEX_POW(i,v,r,h,t))}
;

* ---------------------------------------------------------------------------

eq_ccsflex_sto_ccsenergy_balance(i,v,r,szn,t)$[valgen(i,v,r,t)$ccsflex_sto(i)$tmodel(t)$szn_rep(szn)$Sw_CCSFLEX_STO$(Sw_CCSFLEX_STO_LEVEL=0)]..
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
*exclude hybrid PV+battery because GEN refers to output from both the PV and the battery
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
