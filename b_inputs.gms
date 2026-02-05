$title 'ReEDS 2.0'

* Note - all dollar values are in 2004$ unless otherwise indicated
* It is our intention that there are no hard-coded values in b_inputs.gms
* but you will note that we still have some work to do to make that happen...

*Setting the default directory separator
$setglobal ds \

$eolcom \\

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

*need to convert the 'unit' numhintage to some large value
$ifthen.unithintage %numhintage%=="unit"
$eval numhintage 300
$endif.unithintage

* Under the Clean Air Act, all coal plants are regulated individually. Therefore, we need a large value of hintages to represent these plants
$include inputs_case%ds%max_hintage_number.txt

$ifthen.unithintage %GSw_Clean_Air_Act%==1
$eval numhintage max_hintage_number
$endif.unithintage

*need to convert the 'group' numhintage to some large value
$ifthen.unithintage %numhintage%=="group"
$eval numhintage 300
$endif.unithintage

* there are numeraire hintages on either sides of the outer breaks
* when using calcmethod = 1, here adding two for safety
* NB this will not increase model size given conditions
* dictating valcap and valgen for initial classes
$eval numhintage %numhintage% + 2

*$ontext
* --- print timing profile ---
option profile = 3
option profiletol = 0

* --- suppress .lst file printing ---
* equations listed per block
option limrow = %debug% ;
* variables listed per block
option limcol = %debug% ;
* solver's solution output printed
option solprint = off ;
* solver's system output printed
option sysout = off ;
*$offtext

set dummy "set used for initialization of numerical sets" / 0*10000 / ;
alias(dummy,adummy) ;


*======================
* -- Local Switches --
*======================

* Following are scalars used to turn on or off various components of the model.
* For binary switches, [0] is off and [1] is on.
* These switches are generated from the cases file in runbatch.py.
$include inputs_case%ds%gswitches.txt

* Extra switches that are defined based on other switches
scalar Sw_Prod "Scalar value for whether Sw_H2 or Sw_DAC are enabled" ;
Sw_Prod$[Sw_H2 or Sw_DAC or Sw_DAC_Gas] = 1 ;

set timetype "Type of time method used in the model"
/ seq, win, int / ;

parameter Sw_Timetype(timetype) "Switch that specifies the type of time method used in the model" ;

Sw_Timetype("%timetype%") = 1 ;

* Sw_PCM is always 0 except when running d_solvepcm.gms, where it's set to 1
scalar Sw_PCM "Internal switch used when running PCM mode" / 0 / ;
* Sw_MGA is always 0 except when running the optimization a second time for MGA, where it's set to 1
scalar Sw_MGA "Internal switch used when running MGA mode" / 0 / ;

*============================
* --- Scalar Declarations ---
*============================

*year-related switches that define retirement and upgrade start dates
scalar retireyear  "first year to allow capacity to start retiring" /%GSw_Retireyear%/
       upgradeyear "first year to allow capacity to upgrade"        /%GSw_Upgradeyear%/
       climateyear "first year to apply climate impacts"            /%GSw_ClimateStartYear%/ ;

*** Scalars: copied from inputs/scalars.csv to inputs_case/scalars.txt in runbatch.py
$include inputs_case%ds%scalars.txt

*==========================
* --- Set Declarations ---
*==========================

*## Spatial sets (define first so case stays consistent)
* written by copy_files.py
$onOrder
set r "regions"
/
$offlisting
$include inputs_case%ds%val_r.csv
$onlisting
/ ;
$offOrder

$onempty
set offshore(r) "offshore zones"
/
$offlisting
$include inputs_case%ds%offshore.csv
$onlisting
/ ;
$offempty

set land(r) "land-based (not offshore) zones" ;
land(r)$[not offshore(r)] = yes ;

* written by copy_files.py
$onempty
set cs(*) "carbon storage sites"
/
$offlisting
$include inputs_case%ds%val_cs.csv
$onlisting
/ ;
$offempty

* created in and mapped to hierarchy in recf.py
set ccreg "capacity credit regions"
/
$offlisting
$include inputs_case%ds%ccreg.csv
$onlisting
/ ;

set eall "emission categories used in reporting"
/
$offlisting
$include inputs_case%ds%eall.csv
$onlisting
/ ;

set e(eall) "emission categories used in model"
/
$offlisting
$include inputs_case%ds%e.csv
$onlisting
/ ;

set etype "emission types used in model (upstream and process)"
/
$offlisting
$include inputs_case%ds%etype.csv
$onlisting
/ ;

Sets
nercr "NERC regions"
* https://www.nerc.com/pa/RAPA/ra/Reliability%20Assessments%20DL/NERC_LTRA_2021.pdf
/
* written by copy_files.py
$include inputs_case%ds%val_nercr.csv
/

transreg "Transmission Planning Regions from FERC order 1000"
* (https://www.ferc.gov/sites/default/files/industries/electric/indus-act/trans-plan/trans-plan-map.pdf)
/
* written by copy_files.py
$include inputs_case%ds%val_transreg.csv
/,

transgrp "sub-FERC-1000 regions"
/
* written by copy_files.py
$include inputs_case%ds%val_transgrp.csv
/,

itlgrp "ReEDS zones for additional ITL constraints when doing a run that includes county resolution"
/
* written by copy_files.py
$include inputs_case%ds%val_itlgrp.csv
/,

cendiv "census divisions"
/
* written by copy_files.py
$include inputs_case%ds%val_cendiv.csv
/,

interconnect "interconnection regions"
/
* written by copy_files.py
$include inputs_case%ds%val_interconnect.csv
/,

country "country regions"
/
* written by copy_files.py
$include inputs_case%ds%val_country.csv
/,

st "US, Mexico, and/or Canadian States/Provinces"
/
* written by copy_files.py
$include inputs_case%ds%val_st.csv
/,

* biomass supply curves defined by USDA region
usda_region "Biomass supply curve regions"
/
* written by copy_files.py
$include inputs_case%ds%val_usda_region.csv
/,

h2ptcreg "Regions which enforce the H2 production incentive regulations, for the US these are the National Transmission Needs Study regions"
* https://www.energy.gov/sites/default/files/2023-12/National%20Transmission%20Needs%20Study%20Supplemental%20Material%20-%20Final_2023.12.1.pdf
/
* written by copy_files.py
$include inputs_case%ds%val_h2ptcreg.csv
/

* Hurdle rate regions
hurdlereg "Hurdle regions"
/
$include inputs_case%ds%val_hurdlereg.csv
/
;

* Written by copy_files.py
$include b_sets.gms

sets
*The following two sets:
*ban - will remove the technology from being considered, anywhere
*bannew - will remove the ability to invest in that technology
  ban(i) "ban from existing, prescribed, and new generation -- usually indicative of missing data or operational constraints"
  /
    ice
    upv_10
    mhkwave
    caes
* csp-ns is "CSP, no storage". There is ~1.3 GW existing capacity but we group it with UPV and
* don't allow new builds of csp-ns.
    csp-ns
    other
    unknown
    geothermal
    hydro
    csp3_1*csp3_12
    csp4_1*csp4_12
    pumped-hydro-flex
    hydED_pumped-hydro-flex
    CoalOldUns_CoalOldScr
    CoalOldUns_CofireOld
    CoalOldScr_CofireOld
$ifthene.hydup not %GSw_HydroCapEnerUpgradeType% == 1
    hydUD
    hydUND
$endif.hydup
$ifthene.hydup2 %GSw_HydroAddPumpDispUpgSwitch% == 0
    hydEND_hydED
    hydED_pumped-hydro
$endif.hydup2
  /,

  bannew(i) "banned from creating new capacity, usually due to lacking data or representation"
  /
    can-imports
    hydro
    distpv
    geothermal
    Ocean
    cofireold
    caes
    CoalOldScr
    CoalOldUns
    csp-ns
*you cannot build existing hydro...
    HydEND
    HydED
  /,

*Technologies with certain combinations of power technology, cooling technology, and
*water source are also banned from new capacity below after defining
*linking sets between i, ctt, and wst.

*Data is insufficient to characterize new pond cooling systems, regulations effectively
*prohibit new once-through cooling
  bannew_ctt(ctt) "banned ctt from creating new non-numeraire techs, usually due to lacking data or representation"
  /
    o
    p
  /,

  bannew_wst(wst) "banned wst from creating new non-numeraire techs, usually due to lacking data or representation"
  /
    fsl
    ss
  / ;

alias(i,ii,iii) ;

set i_water_nocooling(i) "technologies that use water, but are not differentiated by cooling tech and water source"
/
$offlisting
$ondelim
$include inputs_case%ds%i_water_nocooling.csv
$offdelim
$onlisting
/ ;

set i_water_cooling(i) "derived technologies from original technologies with cooling technologies other than just none",
*Hereafter numeraire techs in cooling-water context mean original technologies,
*like gas-CC, and non-numeraire techs mean techs that are derived from numeraire techs
*with cooling technology type and water source data appended to them, like gas-CC_r_fsa
*-- it is gas-CC with recirculating cooling and fresh surface appropriated water source.
  i_water(i) "set of all technologies that use water for any purpose",
  i_ii_ctt_wst(i,ii,ctt,wst) "linking set between non-numeraire techs, numeraire techs, cooling technology types, and water source types",
*linking sets extracted from i_ii_ctt_wst(i,ii,ctt,wst) that allow one-one mapping among dimensions
  i_ctt(i,ctt) "linking set between non-numeraire techs and cooling technology types",
  i_wst(i,wst) "linking set between non-numeraire techs and water source types",
  wst_i_ii(i,ii) "linking set between non-numeraire techs and numeraire techs",
  ctt_i_ii(i,ii) "linking set between non-numeraire techs and numeraire techs";

*input parameters for non-numeraire techs and linking set only if Sw_WaterMain is ON and start with a blank slate
i_water_cooling(i) = no ;
i_ii_ctt_wst(i,ii,ctt,wst) = no ;

$ifthen.coolingwatersets %GSw_WaterMain% == 1
set i_water_cooling_temp(i)
/
$offlisting
$include inputs_case%ds%i_coolingtech_watersource.csv
$include inputs_case%ds%i_coolingtech_watersource_upgrades.csv
$onlisting
/,

  i_ii_ctt_wst_temp(i,ii,ctt,wst)
/
$offlisting
$ondelim
$include inputs_case%ds%i_coolingtech_watersource_link.csv
$include inputs_case%ds%i_coolingtech_watersource_upgrades_link.csv
$offdelim
$onlisting
/ ;

i_water_cooling(i)$i_water_cooling_temp(i) = yes ;
i_ii_ctt_wst(i,ii,ctt,wst)$i_ii_ctt_wst_temp(i,ii,ctt,wst) = yes ;
$endif.coolingwatersets

i_water(i)$[i_water_cooling(i) or i_water_nocooling(i)] = yes ;

*linking sets between non-numeraire techs, numeraire techs, cooling tech, and water source
i_ctt(i,ctt)$[sum{(ii,wst)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = YES ;
i_wst(i,wst)$[sum{(ii,ctt)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = YES ;
*wst_i_ii(i,ii) and ctt_i_ii(i,ii) are identical linking set between non-numeraire and numeraire techs,
*kept both for clarity of use in cooling technology and water source related formulations
wst_i_ii(i,ii)$[sum{(wst,ctt)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = YES ;
ctt_i_ii(i,ii)$[sum{(wst,ctt)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = YES ;

set i_numeraire(i) "numeraire techs that need cooling" ;
*i_numeraire(i) will be removed from valcap set as these technologies are ultimately
*expanded to non-numeraire techs. valcap will have non-numeraire techs if Sw_WaterMain=1
*or will have numeraire techs otherwise.
i_numeraire(ii)$sum{(wst,ctt,i)$i_ii_ctt_wst(i,ii,ctt,wst), 1 } = yes ;

table ctt_hr_mult(i,ctt) "heatrate multipliers to differentiate cooling technology types"
$offlisting
$ondelim
$include inputs_case%ds%heat_rate_mult.csv
$offdelim
$onlisting
;

table ctt_cc_mult(i,ctt) "capital cost multipliers to differentiate cooling technology types"
$offlisting
$ondelim
$include inputs_case%ds%cost_cap_mult.csv
$offdelim
$onlisting
;

table ctt_cost_vom_mult(i,ctt) "VOM cost multipliers to differentiate cooling technology types"
$offlisting
$ondelim
$include inputs_case%ds%cost_vom_mult.csv
$offdelim
$onlisting
;

set allt "all potential years"
/
$offlisting
$include inputs_case%ds%allt.csv
$onlisting
/ ;

set i_geotech(i,geotech) "crosswalk between an individual geothermal technology and its category"
/
$offlisting
$ondelim
$include inputs_case%ds%i_geotech.csv
$offdelim
$onlisting
/ ;

set
*technology-specific subsets
  battery(i)           "battery storage technologies",
  beccs(i)             "Bio with CCS",
  bio(i)               "technologies that use only biofuel",
  boiler(i)            "technologies that use steam boilers"
  canada(i)            "Canadian imports",
  ccs(i)               "CCS technologies",
  ccs_mod(i)           "CCS technologies with moderate capture rate",
  ccs_max(i)           "CCS technologies with maximum capture rate",
  ccsflex_byp(i)       "Flexible CCS technologies with bypass",
  ccsflex_dac(i)       "Flexible CCS technologies with direct air capture",
  ccsflex_sto(i)       "Flexible CCS technologies with storage",
  ccsflex(i)           "Flexible CCS technologies",
  cf_tech(i)           "technologies that have a specified capacity factor"
  coal_ccs(i)          "technologies that use coal and have CCS",
  coal(i)              "technologies that use coal",
  cofire(i)            "cofire technologies",
  combined_cycle(i)    "combined cycle technologies",
  combustion_turbine(i)"combustion turbine technologies",
  consume(i)           "technologies that consume electricity and add to load",
  conv(i)              "conventional generation technologies",
  csp_storage(i)       "csp generation technologies with thermal storage",
  csp(i)               "csp generation technologies",
  csp1(i)              "csp-tes generation technologies 1",
  csp2(i)              "csp-tes generation technologies 2",
  csp3(i)              "csp-tes generation technologies 3",
  csp4(i)              "csp-tes generation technologies 4",
  dac(i)               "direct air capture technologies",
  distpv(i)            "distpv (i.e., rooftop PV) generation technologies",
  demand_flex(i)       "demand flexibility technologies (includes DR and EVMC)",
  dr_shed(i)           "DR shed technologies"
  evmc(i)              "ev flexibility technologies",
  evmc_storage(i)      "ev flexibility as direct load control",
  evmc_shape(i)        "ev flexibility as adoptable change to load from response to pricing",
  fossil(i)            "fossil technologies"
  gas_cc_ccs(i)        "techs that are gas combined cycle and have CCS",
  gas_cc(i)            "techs that are gas combined cycle",
  gas_ct(i)            "techs that are gas combustion turbine",
  gas(i)               "techs that use gas (but not o-g-s)",
  geo(i)               "geothermal technologies",
  geo_base(i)          "geothermal technologies typically considered in model runs",
  geo_hydro(i)         "geothermal hydrothermal technologies",
  geo_egs(i)           "geothermal enhanced geothermal systems technologies",
  geo_extra(i)         "geothermal technologies not typically considered in model runs",
  geo_egs_allkm(i)     "egs (covering deep egs depths of all km) technologies",
  geo_egs_nf(i)        "egs (near-field) technologies",
  h2_combustion(i)     "h2-ct and h2-cc technologies",
  h2_cc(i)             "h2-cc technologies"
  h2_ct(i)             "h2-ct technologies",
  h2(i)                "hydrogen-producing technologies",
  hyd_add_pump(i)      "hydro techs with an added pump",
  hydro_d(i)           "dispatchable hydro technologies",
  hydro_nd(i)          "non-dispatchable hydro technologies",
  hydro(i)             "hydro technologies",
  lfill(i)             "land-fill gas technologies",
  nondispatch(i)       "technologies that are not dispatchable"
  nuclear(i)           "nuclear technologies",
  ofswind(i)           "offshore wind technologies",
  ogs(i)               "oil-gas-steam technologies",
  onswind(i)           "onshore wind technologies",
  psh(i)               "pumped hydro storage technologies",
  pv(i)                "all PV generation technologies",
  pvb(i)               "hybrid pv+battery technologies",
  pvb1(i)              "pvb generation technologies 1",
  pvb2(i)              "pvb generation technologies 2",
  pvb3(i)              "pvb generation technologies 3",
  re(i)                "renewable energy technologies",
  refurbtech(i)        "technologies that can be refurbished",
  rsc_i(i)             "technologies based on Resource supply curves",
  smr(i)               "steam methane reforming technologies",
  storage_hybrid(i)    "hybrid VRE-storage technologies",
  storage_standalone(i) "stand alone storage technologies",
  storage(i)           "storage technologies",
  storage_interday(i)  "interday storage",
  thermal_storage(i)   "thermal storage technologies",
  upgrade(i)           "technologies that are upgrades from other technologies",
  upv(i)               "upv generation technologies",
  vre_distributed(i)   "distributed PV technologies",
  vre_no_csp(i)        "variable renewable energy technologies that are not csp",
  vre_utility(i)       "utility scale wind and PV technologies",
  vre(i)               "variable renewable energy technologies",
  wind(i)              "wind generation technologies",

t(allt) "full set of years" /%startyear%*%endyear%/,

* Each generation technology is broken out by class:
* 1. initial capacity: init-1, init-2, ..., init-n
* 2. prescribed capacity: prescribed
* 3. new capacity: new
* This allows us to distinguish between existing, prescribed, and model-chosen builds
* The number of classes is set by numhintage for initial capacity and numclass for new capacity
v "technology class"
    /
      init-1*init-%numhintage%,
      new1*new%numclass%
    /,

initv(v) "initial technologies" /init-1*init-%numhintage%/,

newv(v) "new tech set" /new1*new%numclass%/

;

* DAC == direct air capture
* H2 == hydrogen
* Note: no longer tracking H2 by color. This means ReEDS internalizes
* emissions for any H2 produced for non-power sector demands
set p "products produced"
/
$offlisting
$include inputs_case%ds%p.csv
$onlisting
/ ;


hyd_add_pump('hydED_pumped-hydro') = yes ;
hyd_add_pump('hydED_pumped-hydro-flex') = yes ;

* Sets involved with resource supply curve definitions
set sc_cat "supply curve categories (capacity and cost)"
/
$offlisting
$include inputs_case%ds%sc_cat.csv
$onlisting
/ ;

set rscbin "Resource supply curves bins" /bin1*bin%numbins%/,
    rscfeas(i,r,rscbin) "feasibility set for technologies that have resource supply curves" ;

alias(r,rr,n,nn) ;
alias(v,vv) ;
alias(t,tt,ttt) ;
alias(st,ast) ;
alias(allt,alltt) ;
alias(cendiv,cendiv2) ;
alias(rscbin,arscbin) ;
alias(nercr,nercrr) ;
alias(transgrp,transgrpp) ;
alias(itlgrp,itlgrpp) ;

parameter yeart(t) "numeric value for year",
          year(allt) "numeric year value for allt" ;

yeart(t) = t.val ;
year(allt) = allt.val ;

set att(allt,t) "mapping set between allt and t" ;
att(allt,t)$[year(allt) = yeart(t)] = yes ;

*the end year is defined dynamically
*if %end_year% < annual data, we are gonna get into trouble...
*if you aint first you're last
set tfirst(t) "first year",
    tlast(t) "last year" ;

*aint first you're last
tfirst(t)$[ord(t) = 1] = yes ;
tlast(t)$[ord(t) = smax(tt,ord(tt))] = yes ;


parameter deflator(allt) "Deflator values (for inflation) calculated from http://www.usinflationcalculator.com/inflation/consumer-price-index-and-annual-percent-changes-from-1913-to-2008/ using the Avg-Avg values"
/
$offlisting
$ondelim
$include inputs_case%ds%deflator.csv
$offdelim
$onlisting
/ ;

*various parameters needed for Present Value Factor (PVF) calculations before solving
*specifically these are used in the aggregating of the PVF of
*onm and capital when years are skipped
set yearafter "set to loop over for the final year calculation"
/
$offlisting
$include inputs_case%ds%yearafter.csv
$onlisting
/ ;

Set upgrade_to(i,ii)         "mapping set that allows for i to be upgraded to ii"
    upgrade_from(i,ii)       "mapping set that allows for i to be upgraded from ii"
    upgrade_link(i,ii,iii)   "indicates that tech i is upgradeable from ii with a delta base of iii"
/
$offlisting
$ondelim
$include inputs_case%ds%upgrade_link.csv
$ifthen.ctech %GSw_WaterMain% == 1
$include inputs_case%ds%upgradelink_water.csv
$endif.ctech
$offdelim
$onlisting
/ ;

upgrade(i)$[sum{(ii,iii), upgrade_link(i,ii,iii) }] = yes ;
upgrade_to(i,ii)$[sum{iii, upgrade_link(i,iii,ii) }] = yes ;
upgrade_from(i,ii)$[sum{iii, upgrade_link(i,ii,iii) }] = yes ;

set unitspec_upgrades(i) "upgraded technologies that get unit-specific characteristics"
/
$offlisting
$ondelim
$include inputs_case%ds%unitspec_upgrades.csv
$offdelim
$onlisting
/ ;

unitspec_upgrades(i)$[sum{ii$ctt_i_ii(i,ii), unitspec_upgrades(ii) }$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), unitspec_upgrades(ii) } ;

ban(i)$[upgrade(i)$(not Sw_Upgrades)] = yes ;
bannew(i)$[upgrade(i)$(not Sw_Upgrades)] = yes ;

* --- Read technology subset lookup table ---
Table i_subsets(i,i_subtech) "technology subset lookup table"
$offlisting
$ondelim
$include inputs_case%ds%tech-subset-table.csv
$offdelim
$onlisting
;

*approach in cooling water formulation is populating parameters of numeraire tech (e.g. gas-CC)
*for non-numeraire techs (e.g. gas-CC_r_fsa; r = recirculating cooling, fsa=fresh surface appropriated water source)
*e.g. populate i_subsets for non-numeraire techs from numeraire tech using a linking set ctt_i_ii(i,ii)
i_subsets(i,i_subtech)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), i_subsets(ii,i_subtech) } ;

*assign subtechs to each upgrade tech
*based on what they will be upgraded to
i_subsets(i,i_subtech)$[upgrade(i)$Sw_Upgrades] =
  sum{ii$upgrade_to(i,ii), i_subsets(ii,i_subtech) } ;

** define tech bans so that they are not defined in the technology subsets below **
* switch based gen tech bans (see cases file for details)
if(Sw_BECCS = 0,
  ban('beccs_mod') = yes ;
  ban('beccs_max') = yes ;
) ;

if(Sw_Biopower = 0,
  ban('biopower') = yes ;
) ;

if(Sw_Canada <> 1,
  ban('can-imports') = yes ;
) ;

if(Sw_CCS = 0,
  ban(i)$i_subsets(i,'ccs') = yes ;
) ;

if(Sw_CCSFLEX_BYP = 0,
  ban('Gas-CC-CCS-F1') = yes ;
  ban('coal-CCS-F1') = yes ;
) ;

if(Sw_CCSFLEX_STO = 0,
  ban('Gas-CC-CCS-F2') = yes ;
  ban('coal-CCS-F2') = yes ;
) ;

if(Sw_CCSFLEX_DAC = 0,
  ban('Gas-CC-CCS-F3') = yes ;
  ban('coal-CCS-F3') = yes ;
) ;

if(Sw_CSP = 0,
  ban(i)$i_subsets(i,'csp') = yes ;
) ;

if(Sw_CSP = 1,
  ban(i)$i_subsets(i,'csp2') = yes ;
) ;

if(Sw_CoalIGCC = 0,
  ban('Coal-IGCC') = yes ;
) ;

if(Sw_CoalNew = 0,
  ban('coal-new') = yes ;
) ;

if(Sw_CofireNew = 0,
  ban('CofireNew') = yes ;
) ;

if(Sw_DAC = 0,
  ban(i)$i_subsets(i,'dac') = yes ;
) ;

if(Sw_DAC_Gas = 0,
  ban("dac_gas") = yes ;
);

if(Sw_EVMC = 0,
  ban(i)$i_subsets(i,'evmc') = yes ;
) ;

if(Sw_GasCT_Aero = 0,
  ban('Gas-CT_aero') = yes ;
) ;

if(Sw_GasCC_H_1x1 = 0,
  ban('Gas-CC_H_1x1') = yes ;
  ban('Gas-CC_H_1x1-CCS_mod') = yes ;
  ban('Gas-CC_H_1x1-CCS_max') = yes ;
) ;

if(Sw_GasCC_H_2x1 = 0,
  ban('Gas-CC_H_2x1') = yes ;
  ban('Gas-CC_H_2x1-CCS_mod') = yes ;
  ban('Gas-CC_H_2x1-CCS_max') = yes ;
) ;

if(Sw_Geothermal = 0,
  ban(i)$i_subsets(i,'geo') = yes ;
) ;

if(Sw_Geothermal = 1,
  ban(i)$i_subsets(i,'geo_extra') = yes ;
) ;

if(Sw_H2 = 0,
  ban(i)$i_subsets(i,'h2') = yes ;
) ;

if(Sw_H2_SMR = 0,
  ban(i)$i_subsets(i,'smr') = yes ;
) ;

if(Sw_H2Combustion = 0,
  ban(i)$i_subsets(i,'h2_combustion') = yes ;
) ;

if(Sw_H2CombinedCycle = 0,
  ban(i)$i_subsets(i,'h2_cc') = yes ;
) ;

if(Sw_H2Combustionupgrade = 0,
  ban(i)$[i_subsets(i,'h2_combustion')$upgrade(i)] = yes ;
) ;

if(Sw_LfillGas = 0,
  ban('lfill-gas') = yes ;
) ;

if(Sw_MaxCaptureCCSTechs = 0,
  ban(i)$[i_subsets(i,'ccs_max')] = yes ;
) ;

if(Sw_Nuclear = 0,
  bannew(i)$i_subsets(i,'nuclear') = yes ;
) ;

if(Sw_NuclearSMR = 0,
  ban("Nuclear-SMR") = yes ;
) ;

if(Sw_OfsWind = 0,
  ban(i)$i_subsets(i,'ofswind') = yes ;
) ;

if(Sw_OnsWind6to10 = 0,
  bannew('wind-ons_6') = yes ;
  bannew('wind-ons_7') = yes ;
  bannew('wind-ons_8') = yes ;
  bannew('wind-ons_9') = yes ;
  bannew('wind-ons_10') = yes ;
) ;

if(Sw_DRShed = 0,
  ban(i)$i_subsets(i,'DR_SHED') = yes ; 
) ;

* always allow PSH to use fresh surface water (fsa, fsu)
* do not allow new PSH to use saline surface water
bannew(i)$[sum{wst_i_ii(i,ii)$i_subsets(i,'psh'), i_wst(i,'ss') }] = YES ;
$ifthen.pshwat %GSw_PSHwatertypes% == 0
* do not allow saline ground water or wastewater effluent
bannew(i)$[sum{wst_i_ii(i,ii)$i_subsets(i,'psh'), i_wst(i,'sg') }] = YES ;
bannew(i)$[sum{wst_i_ii(i,ii)$i_subsets(i,'psh'), i_wst(i,'ww') }] = YES ;
$elseif.pshwat %GSw_PSHwatertypes% == 1
* option to also prohibit fresh groundwater
bannew(i)$[sum{wst_i_ii(i,ii)$i_subsets(i,'psh'), i_wst(i,'sg') }] = YES ;
bannew(i)$[sum{wst_i_ii(i,ii)$i_subsets(i,'psh'), i_wst(i,'ww') }] = YES ;
bannew(i)$[sum{wst_i_ii(i,ii)$i_subsets(i,'psh'), i_wst(i,'fg') }] = YES ;
$elseif.pshwat %GSw_PSHwatertypes% == 2
* option 2 allows fresh/saline ground water and wastewater
$else.pshwat
$endif.pshwat

*** Ban hybrid storage techs based on Sw_HybridPlant switch
* 0: Ban all storage, including CSP
if(Sw_HybridPlant = 0,
 ban(i)$i_subsets(i,'storage_hybrid') = yes ;
) ;
* 1: Allow CSP, ban all other storage
if(Sw_HybridPlant = 1,
 ban(i)$[i_subsets(i,'storage_hybrid')$(not sameas(i,'csp_storage'))] = yes ;
 ban(i)$i_subsets(i,'csp_storage') = no ;
) ;
* 2: Allow hybrid plants, excluding CSP
if(Sw_HybridPlant = 2,
 ban(i)$[i_subsets(i,'storage_hybrid')$(not sameas(i,'csp_storage'))] = no ;
 ban(i)$i_subsets(i,'csp_storage') = yes ;
) ;
* 3: Allow CSP and all other hybrid plants (note csp_storage bans are controlled by Sw_CSP)
if(Sw_HybridPlant = 3,
 ban(i)$[i_subsets(i,'storage_hybrid')$(not sameas(i,'csp_storage'))] = no ;
) ;

*ban techs in hybrid PV+battery if the switch calls for it
if(Sw_PVB=0,
  ban(i)$i_subsets(i,'pvb') = yes ;
  bannew(i)$i_subsets(i,'pvb') = yes ;
) ;

* Ban PVB_Types that aren't included in the model
$ifthen.pvb123 %GSw_PVB_Types% == '1_2'
    ban(i)$i_subsets(i,'pvb3') = yes ;
$endif.pvb123
$ifthen.pvb12 %GSw_PVB_Types% == '1'
    ban(i)$i_subsets(i,'pvb2') = yes ;
    ban(i)$i_subsets(i,'pvb3') = yes ;
$endif.pvb12

*** Ban storage techs based on Sw_Storage switch
* 0: Ban all storage
if(Sw_Storage = 0,
 ban(i)$i_subsets(i,'storage_standalone') = yes ;
 Sw_BatteryMandate = 0 ;
) ;
* 1: Keep all storage

* option to ban upgrades
ban(i)$[upgrade(i)$(not Sw_Upgrades)] = yes ;
bannew(i)$[upgrade(i)$(not Sw_Upgrades)] = yes ;

if(Sw_WaterMain = 1,
*By default, ban new builds with bannew_ctt cooling techs for all i,
bannew(i)$[sum{ctt$bannew_ctt(ctt), i_ctt(i,ctt) }] = YES ;

* ban new builds of Nuclear and coal-CCS with dry cooling techs as cooling requirements
* of nuclear and coal-CCS make dry cooling impractical
bannew(i)$[sum{ctt_i_ii(i,'Nuclear'), i_ctt(i,'d') }] = YES ;
bannew(i)$[sum{ctt_i_ii(i,'coal-CCS_mod'), i_ctt(i,'d') }] = YES ;
bannew(i)$[sum{ctt_i_ii(i,'coal-CCS_max'), i_ctt(i,'d') }] = YES ;
bannew(i)$[sum{ctt_i_ii(i,'Nuclear-SMR'), i_ctt(i,'d') }] = YES ;

*ban and bannew all non-numeraire techs that are derived from ban numeraire techs
ban(i)$sum{ii$ban(ii), ctt_i_ii(i,ii) } = YES ;
bannew(i)$sum{ii$bannew(ii), ctt_i_ii(i,ii) } = YES ;

* ban new builds of water sources included in bannew_wst for all i
bannew(i)$[sum{wst$bannew_wst(wst), i_wst(i,wst) }] = YES ;
* end parentheses for Sw_WaterMain = 1
) ;

* Turn off canadian imports as an option when running NARIS
$ifthen.naris %GSw_Region% == "naris"
  ban(i)$i_subsets(i,'canada') = yes ;
$endif.naris

* Ban DUPV, CSP, and Geothermal resources that do not remain after aggregation
set resourceclass "renewable resource classes"
/
$offlisting
$include inputs_case%ds%resourceclass.csv
$onlisting
/ ;
parameter resourceclassnum(resourceclass) "numeric value for resource class" ;
resourceclassnum(resourceclass) = resourceclass.val ;
set tech_resourceclass(i,resourceclass) "map from CSP/DUPV techs to resource classes"
/
$offlisting
$ondelim
$include inputs_case%ds%tech_resourceclass.csv
$offdelim
$onlisting
/ ;
* There are 12 CSP resource classes by default. If Sw_NumCSPclasses < 12, we ban the
* CSP techs with resource class > Sw_NumCSPclasses
if(Sw_NumCSPclasses < 12,
ban(i)$[i_subsets(i,'csp')
      $sum{resourceclass$tech_resourceclass(i,resourceclass),
           resourceclassnum(resourceclass)>Sw_NumCSPclasses }] = yes ;
) ;
* If Sw_CSPRemoveLow is turned on, remove the last (worst) CSP class (which will be
* equal to Sw_NumCSPclasses)
if(Sw_CSPRemoveLow = 1,
ban(i)$[i_subsets(i,'csp')
      $sum{resourceclass$tech_resourceclass(i,resourceclass),
           resourceclassnum(resourceclass)=Sw_NumCSPclasses }] = yes ;
) ;

*Ban Geothermal resources that do not remain after aggregation
if(Sw_NumGeoclasses < 10,
ban(i)$[i_subsets(i,'geo')
      $sum{resourceclass$tech_resourceclass(i,resourceclass),
           resourceclassnum(resourceclass)>Sw_NumGeoclasses }] = yes ;
) ;

*Ingest list of new nuclear restricted BAs ('p' regions), ba list is consistent with NCSL restrictions.
*https://www.ncsl.org/research/environment-and-natural-resources/states-restrictions-on-new-nuclear-power-facility.aspx
$onempty
set nuclear_ba_ban(r) "List of  BAs where new nuclear builds are restricted"
/
$offlisting
$include inputs_case%ds%nuclear_ba_ban_list.csv
$onlisting
/ ;
$offempty

* techs banned by state (note that this only applies to valinv later)
$onempty
table tech_banned(i,r) "Banned technologies by model region"
$offlisting
$ondelim
$include inputs_case%ds%techs_banned.csv
$offdelim
$onlisting
;
$offempty

* --- define technology subsets ---
battery(i)$(not ban(i))             = yes$i_subsets(i,'battery') ;
beccs(i)$(not ban(i))               = yes$i_subsets(i,'beccs') ;
bio(i)$(not ban(i))                 = yes$i_subsets(i,'bio') ;
boiler(i)$(not ban(i))              = yes$i_subsets(i,'boiler') ;
canada(i)$(not ban(i))              = yes$i_subsets(i,'canada') ;
ccs(i)$(not ban(i))                 = yes$i_subsets(i,'ccs') ;
ccs_mod(i)$(not ban(i))             = yes$i_subsets(i,'ccs_mod') ;
ccs_max(i)$(not ban(i))             = yes$i_subsets(i,'ccs_max') ;
ccsflex_byp(i)$(not ban(i))         = yes$i_subsets(i,'ccsflex_byp') ;
ccsflex_dac(i)$(not ban(i))         = yes$i_subsets(i,'ccsflex_dac') ;
ccsflex_sto(i)$(not ban(i))         = yes$i_subsets(i,'ccsflex_sto') ;
ccsflex(i)$(not ban(i))             = yes$i_subsets(i,'ccsflex') ;
cf_tech(i)$(not ban(i))             = yes$i_subsets(i,'cf_tech') ;
coal_ccs(i)$(not ban(i))            = yes$i_subsets(i,'coal_ccs') ;
coal(i)$(not ban(i))                = yes$i_subsets(i,'coal') ;
cofire(i)$(not ban(i))              = yes$i_subsets(i,'cofire') ;
combined_cycle(i)$(not ban(i))      = yes$i_subsets(i,'combined_cycle') ;
combustion_turbine(i)$(not ban(i))  = yes$i_subsets(i,'combustion_turbine') ;
consume(i)$(not ban(i))             = yes$i_subsets(i,'consume') ;
conv(i)$(not ban(i))                = yes$i_subsets(i,'conv') ;
csp_storage(i)$(not ban(i))         = yes$i_subsets(i,'csp_storage') ;
csp(i)$(not ban(i))                 = yes$i_subsets(i,'csp') ;
csp1(i)$(not ban(i))                = yes$i_subsets(i,'csp1') ;
csp2(i)$(not ban(i))                = yes$i_subsets(i,'csp2') ;
csp3(i)$(not ban(i))                = yes$i_subsets(i,'csp3') ;
csp4(i)$(not ban(i))                = yes$i_subsets(i,'csp4') ;
dac(i)$(not ban(i))                 = yes$i_subsets(i,'dac') ;
distpv(i)$(not ban(i))              = yes$i_subsets(i,'distpv') ;
dr_shed(i)$(not ban(i))             = yes$i_subsets(i,'dr_shed') ;
demand_flex(i)$(not ban(i))         = yes$i_subsets(i,'demand_flex') ;
evmc(i)$(not ban(i))                = yes$i_subsets(i,'evmc') ;
evmc_storage(i)$(not ban(i))        = yes$i_subsets(i,'evmc_storage') ;
evmc_shape(i)$(not ban(i))          = yes$i_subsets(i,'evmc_shape') ;
fossil(i)$(not ban(i))              = yes$i_subsets(i,'fossil') ;
gas_cc_ccs(i)$(not ban(i))          = yes$i_subsets(i,'gas_cc_ccs') ;
gas_cc(i)$(not ban(i))              = yes$i_subsets(i,'gas_cc') ;
gas_ct(i)$(not ban(i))              = yes$i_subsets(i,'gas_ct') ;
gas(i)$(not ban(i))                 = yes$i_subsets(i,'gas') ;
geo(i)$(not ban(i))                 = yes$i_subsets(i,'geo') ;
geo_base(i)$(not ban(i))            = yes$i_subsets(i,'geo_base') ;
geo_hydro(i)$(not ban(i))           = yes$i_subsets(i,'geo_hydro') ;
geo_egs(i)$(not ban(i))             = yes$i_subsets(i,'geo_egs') ;
geo_extra(i)$(not ban(i))           = yes$i_subsets(i,'geo_extra') ;
geo_egs_allkm(i)$(not ban(i))       = yes$i_subsets(i,'geo_egs_allkm') ;
geo_egs_nf(i)$(not ban(i))          = yes$i_subsets(i,'geo_egs_nf') ;
h2_combustion(i)$(not ban(i))       = yes$i_subsets(i,'h2_combustion') ;
h2_cc(i)$(not ban(i))               = yes$i_subsets(i,'h2_cc') ;
h2_ct(i)$(not ban(i))               = yes$i_subsets(i,'h2_ct') ;
h2(i)$(not ban(i))                  = yes$i_subsets(i,'h2') ;
hydro_d(i)$(not ban(i))             = yes$i_subsets(i,'hydro_d') ;
hydro_nd(i)$(not ban(i))            = yes$i_subsets(i,'hydro_nd') ;
hydro(i)$(not ban(i))               = yes$i_subsets(i,'hydro') ;
lfill(i)$(not ban(i))               = yes$i_subsets(i,'lfill') ;
nondispatch(i)$(not ban(i))         = yes$i_subsets(i,'nondispatch') ;
nuclear(i)$(not ban(i))             = yes$i_subsets(i,'nuclear') ;
ofswind(i)$(not ban(i))             = yes$i_subsets(i,'ofswind') ;
ogs(i)$(not ban(i))                 = yes$i_subsets(i,'ogs') ;
onswind(i)$(not ban(i))             = yes$i_subsets(i,'onswind') ;
psh(i)$(not ban(i))                 = yes$i_subsets(i,'psh') ;
pv(i)$(not ban(i))                  = yes$i_subsets(i,'pv') ;
pvb(i)$(not ban(i))                 = yes$i_subsets(i,'pvb') ;
pvb1(i)$(not ban(i))                = yes$i_subsets(i,'pvb1') ;
pvb2(i)$(not ban(i))                = yes$i_subsets(i,'pvb2') ;
pvb3(i)$(not ban(i))                = yes$i_subsets(i,'pvb3') ;
re(i)$(not ban(i))                  = yes$i_subsets(i,'re') ;
refurbtech(i)$(not ban(i))          = yes$i_subsets(i,'refurbtech') ;
rsc_i(i)$(not ban(i))               = yes$i_subsets(i,'rsc') ;
smr(i)$(not ban(i))                 = yes$i_subsets(i,'smr') ;
storage_hybrid(i)$(not ban(i))      = yes$i_subsets(i,'storage_hybrid') ;
storage_interday(i)$(not ban(i))    = yes$i_subsets(i,'storage_interday') ;
storage_standalone(i)$(not ban(i))  = yes$i_subsets(i,'storage_standalone') ;
storage(i)$(not ban(i))             = yes$i_subsets(i,'storage') ;
thermal_storage(i)$(not ban(i))     = yes$i_subsets(i,'thermal_storage') ;
upv(i)$(not ban(i))                 = yes$i_subsets(i,'upv') ;
vre_distributed(i)$(not ban(i))     = yes$i_subsets(i,'vre_distributed') ;
vre_no_csp(i)$(not ban(i))          = yes$i_subsets(i,'vre_no_csp') ;
vre_utility(i)$(not ban(i))         = yes$i_subsets(i,'vre_utility') ;
vre(i)$(not ban(i))                 = yes$i_subsets(i,'vre') ;
wind(i)$(not ban(i))                = yes$i_subsets(i,'wind') ;

set coal_noccs(i) "technologies that use coal and do not have CCS, aka unabated coal" ;
coal_noccs(i)$[coal(i)$(not ccs(i))] = yes ; 

* Create mapping of technology groups to technologies
set tg_i(tg,i) "technologies that belong in tech group tg" ;
tg_i('wind-ons',i)$onswind(i) = yes ;
tg_i('wind-ofs',i)$ofswind(i) = yes ;
tg_i('pv',i)$[(pv(i) or pvb(i))$(not distpv(i))] = yes ;
tg_i('csp',i)$csp(i) = yes ;
tg_i('gas',i)$gas(i) = yes ;
tg_i('coal',i)$coal(i) = yes ;
tg_i('nuclear',i)$nuclear(i) = yes ;
tg_i('battery',i)$battery(i) = yes ;
tg_i('hydro',i)$hydro(i) = yes ;
tg_i('h2',i)$h2_combustion(i) = yes ;
tg_i('geothermal',i)$geo(i) = yes ;
tg_i('biomass',i)$bio(i) = yes ;
tg_i('pumped-hydro',i)$psh(i) = yes ;
tg_i('dr_shed',i)$dr_shed(i) = yes ;

*Hybrid pv+battery (PVB) configurations are defined by:
*  (1) inverter loading ratio (DC/AC) and
*  (2) battery capacity ratio (Battery/PV Array)
*Each configuration has ten resource classes
*The PV portion refers to "UPV", but not "DUPV"
*The battery portion refers to "battery_li"
set pvb_config "set of hybrid pv+battery configurations"
/
$offlisting
$include inputs_case%ds%pvb_config.csv
$onlisting
/ ;

set pvb_agg(pvb_config,i) "crosswalk between hybrid pv+battery configurations and technology options"
/
$offlisting
$ondelim
$include inputs_case%ds%pvb_agg.csv
$offdelim
$onlisting
/ ;

*add non-numeraire CSPs in index i of already defined set tg_i(tg,i)
tg_i("csp",i)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$Sw_WaterMain] = yes ;

*Offhsore wind turbine types
set ofstype "offshore types used in offshore requirement constraint (eq_RPS_OFSWind)"
/
$offlisting
$include inputs_case%ds%ofstype.csv
$onlisting
/ ;

set ofstype_i(ofstype,i) "crosswalk between ofstype and i"
/
$offlisting
$ondelim
$include inputs_case%ds%ofstype_i.csv
$offdelim
$onlisting
/ ;

storage_interday(i)$(Sw_InterDayLinkage = 0) = no ;

$onempty
parameter water_with_cons_rate(i,ctt,w) "--gal/MWh-- technology specific-cooling tech based water withdrawal and consumption data"
/
$offlisting
$ondelim
$include inputs_case%ds%water_with_cons_rate.csv
$offdelim
$onlisting
/
;
$offempty

$onempty
* Water requirement if all filling takes place in 1 year and minimum reservoir level is 15% of max volume
table water_req_psh(r,rscbin) "--Mgal/MW/yr-- required water for PSH during construction to fill reservoir"
$offlisting
$ondelim
$include inputs_case%ds%water_req_psh_10h_1_51.csv
$offdelim
$onlisting
;
$offempty

* Recalculate PSH water requirements based on user input filling time
scalar psh_fillyrs "number of years assumed to fill PSH reservoirs" /%GSw_PSHfillyears%/ ;
water_req_psh(r,rscbin) = round(water_req_psh(r,rscbin) / psh_fillyrs, 6) ;

*populate the water withdrawal and consumption data to non-numeraire technologies
*based on numeraire techs and cooling technologies types to avoid repetitive
*entry of data in the input data file and provide flexibility
*in populating data if new combinations come along the way
water_with_cons_rate(i,ctt,w)$i_water_cooling(i) =
  sum{(ii,wst)$i_ii_ctt_wst(i,ii,ctt,wst), water_with_cons_rate(ii,ctt,w) } ;

*CSP techs have same water withdrawal and consumption rates; populating all CSP data with the data of csp1_1
water_with_cons_rate(i,ctt,w)$[i_water_cooling(i)$(csp1(i) or csp2(i) or csp3(i) or csp4(i))] =
  sum{(ii,wst)$i_ii_ctt_wst(i,ii,ctt,wst), water_with_cons_rate("csp1_1",ctt,w) } ;

water_with_cons_rate(ii,ctt,w)$[sum{(wst,i)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = no ;

parameter water_rate(i,w) "--gal/MWh-- water withdrawal/consumption w rate by technology i" ;
* adding geothermal categories for water accounting
i_water(i)$geo(i) = yes ;
water_with_cons_rate(i,ctt,w)$geo(i) = water_with_cons_rate("geothermal",ctt,w) ;

* Till this point, i already has non-numeraire techs (e.g., gas-CC_o_fsa, gas-CC_r_fsa,
*and gas-CC_r_fg) instead of numeraire technology (e.g., gas-CC)
* The line below just removes ctt dimension, by summing over ctt.
water_rate(i,w)$i_water(i) = sum{ctt, water_with_cons_rate(i,ctt,w) } ;

water_rate(i,w)$upgrade(i) = sum{ii$upgrade_to(i,ii), water_rate(ii,w) } ;

set dispatchtech(i)                 "technologies that are dispatchable",
    noret_upgrade_tech(i)           "upgrade techs that do not retire",
    retiretech(i,v,r,t)             "combinations of i,v,r,t that can be retired",
    sccapcosttech(i)                "technologies that have their capital costs embedded in supply curves",
    inv_cond(i,v,r,t,tt)            "allows an investment in tech i of class v to be built in region r in year tt and usable in year t" ;

noret_upgrade_tech(i)$hyd_add_pump(i) = yes ;
noret_upgrade_tech(i)$[(coal_ccs(i) or gas_cc_ccs(i))$upgrade(i)$Sw_CCS_NoRetire] = yes ;
dispatchtech(i)$[not(vre(i) or hydro_nd(i) or ban(i))] = yes ;
sccapcosttech(i)$[hydro(i) or psh(i) or dr_shed(i)] = yes ;

*initialize sets to "no"
retiretech(i,v,r,t) = no ;
inv_cond(i,v,r,t,tt) = no ;

parameter min_retire_age(i) "minimum retirement age by technology"
/
$offlisting
$ondelim
$include inputs_case%ds%min_retire_age.csv
$offdelim
$onlisting
/ ;

min_retire_age(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), min_retire_age(ii) } ;
* if GSw_Clean_Air_Act is enabled, there is no minimum retire age for coal plants
min_retire_age(i)$[coal(i)$Sw_Clean_Air_Act] = no ;

parameter retire_penalty(allt) "--fraction-- penalty for retiring a power plant expressed as a fraction of FOM"
/
$offlisting
$ondelim
$include inputs_case%ds%retire_penalty.csv
$offdelim
$onlisting
 / ;


set prescriptivelink0(pcat,ii) "initial set of prescribed categories and their technologies - used in assigning prescribed builds"
/
$offlisting
$ondelim
$include inputs_case%ds%prescriptivelink0.csv
$offdelim
$onlisting
/ ;

*include non-numeraire CSPs and then exclude numeraire CSPs in ii dimension of
*prescriptivelink0(pcat,ii) set when Sw_WaterMain is ON
prescriptivelink0("csp-ws",ii)$[(csp1(ii) or csp2(ii) or csp3(ii) or csp4(ii))$Sw_WaterMain] = yes ;
prescriptivelink0("csp-ws",ii)$[csp(ii)$i_numeraire(ii)$Sw_WaterMain] = no ;

set prescriptivelink(pcat,i) "final set of prescribed categories and their technologies - used in the model" ;

prescriptivelink(pcat,i)$prescriptivelink0(pcat,i) = yes ;

alias(pcat,ppcat) ;

* active prescriptivelink for all techs not included in the table above
* but restrict out csp techs in this calculation - since they
* are indexed by a separate pcat (csp-ws) and have special considerations
prescriptivelink(pcat,i)$[sameas(pcat,i)$(not sum{ppcat, prescriptivelink(ppcat,i) })$(not csp1(i))] = yes ;
*only geo_hydro techs are considered to meet geothermal prescriptions
prescriptivelink(pcat,i)$[geo_extra(i)] = no ;


*upgrades have no prescriptions
prescriptivelink(pcat,i)$[upgrade(i)] = no ;

set rsc_agg(i,ii)   "rsc technologies that belong to the same class" ;

set tg_rsc_cspagg(i,ii) "csp technologies that belong to the same class"
/
$offlisting
$ondelim
$include inputs_case%ds%tg_rsc_cspagg.csv
$offdelim
$onlisting
/ ;

set tg_rsc_cspagg_tmp(i,ii) "expanded tg_rsc_cspagg(i,ii) to include new non-numeraire CSP techs" ;

*input parameters for linking set only when Sw_WaterMain is ON and start with a blank slate
tg_rsc_cspagg_tmp(i,ii) = no ;
$ifthen.coolingwatersets %GSw_WaterMain% == 1
set tg_rsc_cspagg_tmp_temp(i,ii)
/
$offlisting
$ondelim
$include inputs_case%ds%tg_rsc_cspagg_tmp.csv
$offdelim
$onlisting
/ ;
tg_rsc_cspagg_tmp(i,ii)$tg_rsc_cspagg_tmp_temp(i,ii) = yes ;
$endif.coolingwatersets

*include non-numeraire CSPs and then exclude numeraire CSPs in ii dimension
*of tg_rsc_cspagg(i,ii) set when Sw_WaterMain is ON
tg_rsc_cspagg(i,ii)$[tg_rsc_cspagg_tmp(i,ii)$Sw_WaterMain] = yes ;
tg_rsc_cspagg(i,ii)$[csp(ii)$i_numeraire(ii)$Sw_WaterMain] = no ;

$ontext
Replicating the construct for CSP to link Hybrid PV+battery and UPV for the resoruce supply curve constraints
  eq_rsc_invlim(i,bin).. sum{ii$rsc_agg(i,ii), INV_RSC(i,bin) } <= bin_capacity(i,bin) ;
  When i = "upv_1", this constraint looks like:
  eq_rsc_invlim("upv_1",bin).. INV_RSC("pvb1_1") + INV_RSC("upv_1") <= bin_capacity("upv_1",bin)
  Because the first index of rsc_agg is only a UPV technology the above constraint will never be generated when "i" is a pvb(i).
$offtext

set tg_rsc_upvagg(i,ii) "pv and pvb technologies that belong to the same class"
/
$offlisting
$ondelim
$include inputs_case%ds%tg_rsc_upvagg.csv
$offdelim
$onlisting
/ ;

*initialize rsc aggregation set for 'i'='ii'
*rsc_agg(i,ii)$[sameas(i,ii)$(not csp(i))$(not csp(ii))$rsc_i(i)$rsc_i(ii)] = yes ;
rsc_agg(i,ii)$[sameas(i,ii)$rsc_i(i)$rsc_i(ii)] = yes ;
*add csp to rsc aggregation set
rsc_agg(i,ii)$tg_rsc_cspagg(i,ii) = yes ;
*add upv to rsc aggregation set
rsc_agg(i,ii)$tg_rsc_upvagg(i,ii) = yes ;
*All PSH types use the same supply curve
rsc_agg('pumped-hydro',ii)$psh(ii) = yes ;
rsc_agg(i,ii)$[ban(i) or ban(ii)] = no ;

*============================
* -- Demand flexibility setup --
*============================

set flex_type "set of demand flexibility types: daily, previous, next, adjacent"
/
$offlisting
$include inputs_case%ds%flex_type.csv
$onlisting
/ ;

*======================================
*     --- Begin hierarchy ---
*======================================

set hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg) "hierarchy of various regional definitions"
/
$offlisting
$ondelim
$include inputs_case%ds%hierarchy.csv
$offdelim
$onlisting
/ ;


* Mappings between r and other region sets
set r_itlgrp(r,itlgrp)
    r_nercr(r,nercr)
    r_transreg(r,transreg)
    r_transgrp(r,transgrp)
    r_cendiv(r,cendiv)
    r_st(r,st)
    r_interconnect(r,interconnect)
    r_country(r,country)
    r_usda(r,usda_region)
    r_h2ptcreg(r,h2ptcreg)
    r_hurdlereg(r,hurdlereg)
    r_ccreg(r,ccreg)
;

r_nercr(r,nercr)                      $sum{(      transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_transreg(r,transreg)                $sum{(nercr,         transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_transgrp(r,transgrp)                $sum{(nercr,transreg,         cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_cendiv(r,cendiv)                    $sum{(nercr,transreg,transgrp,       st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_st(r,st)                            $sum{(nercr,transreg,transgrp,cendiv,   interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_interconnect(r,interconnect)        $sum{(nercr,transreg,transgrp,cendiv,st,             country,usda_region,h2ptcreg,hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_country(r,country)                  $sum{(nercr,transreg,transgrp,cendiv,st,interconnect,        usda_region,h2ptcreg,hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_usda(r,usda_region)                 $sum{(nercr,transreg,transgrp,cendiv,st,interconnect,country,            h2ptcreg,hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_h2ptcreg(r,h2ptcreg)                $sum{(nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,         hurdlereg,ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_hurdlereg(r,hurdlereg)              $sum{(nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,          ccreg) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;
r_ccreg(r,ccreg)                      $sum{(nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg      ) $hierarchy(r,nercr,transreg,transgrp,cendiv,st,interconnect,country,usda_region,h2ptcreg,hurdlereg,ccreg),1} = yes ;

set r_itlgrp(r,itlgrp) "mapping of r to itlgrp"
/
$offlisting
$ondelim
$include inputs_case%ds%hierarchy_itlgrp.csv
$offdelim
$onlisting
/ ;

* Region hierarchy level within which to site optimally sited load
alias(%GSw_LoadSiteReg%, loadsitereg) ;
set r_loadsitereg(r,loadsitereg) "Mapping from model zones to loadsite regions" ;
r_loadsitereg(r,%GSw_LoadSiteReg%) = r_%GSw_LoadSiteReg%(r,%GSw_LoadSiteReg%) ;


*================================
*sets that define model boundaries
*================================
set tmodel(t) "years to include in the model",
    tfix(t) "years to fix variables over when summing over previous years",
    tprev(t,tt) "previous modeled tt from year t",
    stfeas(st) "states to include in the model",
    tsolved(t) "years that have solved" ;

*following parameters get re-defined when the solve years have been declared
parameter mindiff(t) "minimum difference between t and all other tt that are in tmodel(t)" ;


tmodel(t) = no ;
tfirst(t) = no ;
tlast(t) = no ;
tfix(t) = no ;
stfeas(st) = no ;
tprev(t,tt) = no ;
tsolved(t) = no ;


*==============================
* Year specification
*==============================

* declared over allt to allow for external data files that extend beyond end_year
set tmodel_new(allt) "years to run the model"
/
$offlisting
$include inputs_case%ds%modeledyears.csv
$onlisting
/ ;

tmodel_new(allt)$[year(allt) > %endyear%]= no ;

*reset the first and last year indices of the model
tfirst(t)$[ord(t) = smin{tt$tmodel_new(tt), ord(tt) }] = yes ;
tlast(t)$[ord(t) = smax{tt$tmodel_new(tt), ord(tt) }] = yes ;

*now get rid of all non-immediately-previous values (it takes three steps to get there...)
tprev(t,tt)$[tmodel_new(t)$tmodel_new(tt)$(tt.val<t.val)] = yes ;
mindiff(t)$tmodel_new(t) = smin{tt$tprev(t,tt), t.val-tt.val} ;
tprev(t,tt)$[tmodel_new(t)$tmodel_new(tt)$(t.val-tt.val<>mindiff(t))] = no ;

* In order to fill all necessary dimensions of upgrade techs parameters, we require
* Sw_UpgradeYear in ban(i) to be a modeled year and thus we compute as either
* the GSw_UpgradeYear option or the next modeled years after GSw_UpgradeYear

* reset sw_upgradeyear
Sw_UpgradeYear = 0 ;

* if the upgradeyear is modeled set it to upgrade year
Sw_UpgradeYear$tmodel_new("%GSw_UpgradeYear%") = %GSw_UpgradeYear% ;

* if upgrade year is not modeled, set it to the next available upgrade year
Sw_UpgradeYear$[(not Sw_UpgradeYear)] =
  smin(tt$[(tt.val>=%GSw_UpgradeYear%)$tmodel_new(tt)],tt.val) ;


* if caa_coal_retire_year is not in the set of years being modeled, then set it to the first year that is modeled after caa_coal_retire_year
caa_coal_retire_year$[not sum{tt$[tt.val=caa_coal_retire_year], tmodel_new(tt) }] = 
  smin(tt$[(tt.val>=caa_coal_retire_year)$tmodel_new(tt)],tt.val) ;

* if Sw_Clean_Air_Act = 0, then set caa_coal_retire_year to the last solve year
caa_coal_retire_year$[Sw_Clean_Air_Act = 0] = smax(tmodel_new, tmodel_new.val) ;

*======================================
* ---------- Bintage Mapping ----------
*======================================
*following set is un-assumingly important
*it allows for the investment of bintage 'v' at time 't'

*table ivtmap(i,t)
* declared over allt to allow for external data files that extend beyond end_year
table ivt_num(i,allt) "number associated with bin for ivt calculation"
$offlisting
$ondelim
$include inputs_case%ds%ivt.csv
$offdelim
$onlisting
;


set ivt(i,v,t) "mapping set between i v and t - for new technologies" ;
ivt(i,newv,t)$[ord(newv) = ivt_num(i,t)] = yes ;

*Expand ivt to water techs
ivt(i,v,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), ivt(ii,v,t) } ;

*Also expand ivt_num to water techs for use in Augur
ivt_num(i,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), ivt_num(ii,t) } ;


*important assumption here that upgrade technologies
*receive the same binning assumptions as the technologies
*that they are upgraded to - this allows for easier translation
*and mapping of plant characteristics (cost_vom, cost_fom, heat_rate)
ivt(i,newv,t)$[(yeart(t)>=Sw_UpgradeYear)$upgrade(i)] =
   sum{ii$upgrade_to(i,ii), ivt(ii,newv,t) } ;


parameter countnc(i,newv) "number of years in each newv set" ;

*add 1 for each t item in the ct_corr set
countnc(i,newv) = sum{t$ivt(i,newv,t),1} ;

set one_newv(i) "technologies that only have one vintage for new plants" ;

* Only one vintage is present if there is a new1 for that technology...
one_newv(i)$[sum{t, ivt(i,"new1",t) }] = yes ;
* ...and there are no entries other than new1 for that technology
one_newv(i)$sum{(v,t)$[not sameas(v,"new1")], ivt(i,v,t) } = no ;

*=====================================
*--- basic parameter declarations ---
*=====================================

parameter crf(t) "--unitless-- capital recovery factor"
/
$offlisting
$ondelim
$include inputs_case%ds%crf.csv
$offdelim
$onlisting
/,
          crf_co2_incentive(t) "--unitless-- capital recovery factor using a 12-year economic lifetime"
/
$offlisting
$ondelim
$include inputs_case%ds%crf_co2_incentive.csv
$offdelim
$onlisting
/,

          crf_h2_incentive(t) "--unitless-- capital recovery factor using a 10-year economic lifetime"
/
$offlisting
$ondelim
$include inputs_case%ds%crf_h2_incentive.csv
$offdelim
$onlisting
/,

* pvf_capital and pvf_onm here are for intertemporal mode. These parameters
* are overwritten for sequential mode in d_solveprep.gms.
          pvf_capital(t) "--unitless-- present value factor for overnight capital costs"
/
$offlisting
$ondelim
$include inputs_case%ds%pvf_cap.csv
$offdelim
$onlisting
/,
          pvf_onm(t)"--unitless-- present value factor of operations and maintenance costs"
/
$offlisting
$ondelim
$include inputs_case%ds%pvf_onm_int.csv
$offdelim
$onlisting
/,
          tc_phaseout_mult(i,v,t)                 "--unitless-- multiplier that reduces the value of the PTC and ITC after the phaseout trigger has been hit",
          tc_phaseout_mult_t(i,t)                 "--unitless-- a single year's multiplier of tc_phaseout_mult",
          tc_phaseout_mult_t_load(i,t)            "--unitless-- a single year's multiplier of tc_phaseout_mult",
          co2_captured_incentive(i,v,r,allt)      "--$/tco2 stored-- incentive on CO2 captured dependent on technology"
          co2_captured_incentive_in(i,v,allt)     "--$/tco2 stored-- incentive on CO2 captured dependent on technology"
/
$offlisting
$ondelim
$include inputs_case%ds%co2_capture_incentive.csv
$offdelim
$onlisting
/,

          h2_ptc(i,v,r,allt)        "--2004$/kg h2 produced -- incentive on hydrogen production by electrolyzers which purchase Energy Attribute Credits"
          h2_ptc_in(i,v,allt)       "--2004$/kg h2 produced -- incentive on hydrogen production by electrolyzers which purchase Energy Attribute Credits, this parameter is used to build h2_ptc and is produced in input_processing/calc_financial_inputs.py"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_ptc.csv
$offdelim
$onlisting
/,

          ptc_value_scaled(i,v,allt) "--$/MWh-- value of the PTC incorporating adjustments for monetization costs, tax grossup benefits, and the difference between ptc duration and reeds evaluation period"
/
$offlisting
$ondelim
$include inputs_case%ds%ptc_value_scaled.csv
$offdelim
$onlisting
/,
          pvf_onm_undisc(t) "--unitless-- undiscounted present value factor of operations and maintenance costs"
;

ptc_value_scaled(i,v,t)$[i_water_cooling(i)$Sw_WaterMain] =
   sum{ii$ctt_i_ii(i,ii), ptc_value_scaled(ii,v,t) } ;

parameter firstyear_v(i,v) "flag for first year that a new new vintage can be built" ;
parameter lastyear_v(i,v) "flag for the last year that a new new vintage can be built" ;

firstyear_v(i,v) = sum{t$[yeart(t)=smin(tt$ivt(i,v,tt),yeart(tt))], yeart(t) } ;
lastyear_v(i,v) = sum{t$[yeart(t)=smax(tt$ivt(i,v,tt),yeart(tt))], yeart(t) } ;

* pvf_onm_undisc is based on intertemporal pvf_onm and pvf_capital,
* and is used for bulk system cost outputs
pvf_onm_undisc(t)$pvf_capital(t) = pvf_onm(t) / pvf_capital(t) ;

*==========================================
*     --- Technology start years ---
*==========================================

* Note that some techs have a dummy firstyear of 2500
parameter firstyear(i) "first year where new investment is allowed"
/
$offlisting
$ondelim
$include inputs_case%ds%firstyear.csv
$offdelim
$onlisting
/ ;

*---Add first year that capacity can be built:
firstyear(i)$[(firstyear(i) < firstyear_min)$firstyear(i)] = firstyear_min ;

scalar co2_detail_startyr "--year-- Year to start the detailed representation of CO2 capture/storage" ;
co2_detail_startyr = smin{i$[ccs(i)$firstyear(i)], firstyear(i) } ;

*==========================================

scalar model_builds_start_yr "--integer-- Start year allowing new generators to be built" ;

*Ignore gas units because gas-ct's are allowed in historical years
model_builds_start_yr = smin{i$[(not gas_ct(i))$(not distpv(i))$(not upgrade(i))$(not ban(i))$firstyear(i)], firstyear(i) } ;

firstyear(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), firstyear(ii) } ;

firstyear(i)$[not firstyear(i)] = model_builds_start_yr ;
firstyear(i)$[i_water_cooling(i)$(not Sw_WaterMain)] = NO ;
firstyear(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), firstyear(ii) } ;

parameter firstyear_pcat(pcat) ;
firstyear_pcat(pcat)$[sum{i$[sameas(i,pcat)$(not ban(i))], firstyear(i) }] = sum{i$sameas(i,pcat), firstyear(i) } ;
firstyear_pcat("upv") = firstyear("upv_1") ;
firstyear_pcat("wind-ons") = firstyear("wind-ons_1") ;
firstyear_pcat("wind-ofs") = firstyear("wind-ofs_1") ;
firstyear_pcat("csp-ws") = firstyear("csp2_1") ;
firstyear_pcat("geohydro_allkm") = firstyear("geohydro_allkm_1") ;
firstyear_pcat("egs_allkm") = firstyear("egs_allkm_1") ;


*==============================
* Region specification
*==============================

*set the state feasibility set
*determined by which regions are feasible
stfeas(st)$[sum{r$r_st(r,st), 1 }] = yes ;


*==========================
* -- existing capacity --
*==========================

*Begin loading of capacity data
parameter poi_cap_init(r) "--MW-- initial (pre-2010) capacity of all types"
/
$offlisting
$ondelim
$include inputs_case%ds%poi_cap_init.csv
$offdelim
$onlisting
/ ;

*created by /input_processing/writecapdat.py
table capnonrsc(i,r,*) "--MW-- raw power capacity data for non-RSC tech created by .\input_processing\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%capnonrsc.csv
$offdelim
$onlisting
;

*created by /input_processing/writecapdat.py
$onempty
table capnonrsc_energy(i,r,*) "--MWh-- raw energy capacity data for battery tech created by .\input_processing\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%capnonrsc_energy.csv
$offdelim
$onlisting
;
$offempty

*created by /input_processing/writecapdat.py
$onempty
table caprsc(pcat,r,*) "--MW-- raw RSC capacity data, created by .\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%caprsc.csv
$offdelim
$onlisting
;
$offempty

*created by /input_processing/writecapdat.py
* declared over allt to allow for external data files that extend beyond end_year
$onempty
table prescribednonrsc(allt,pcat,r,*) "--MW-- raw prescribed capacity data for non-RSC tech created by writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_nonRSC.csv
$offdelim
$onlisting
;
$offempty

$onempty
table prescribednonrsc_energy(allt,pcat,r,*) "--MWh-- raw prescribed energy capacity data for non-RSC tech created by writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_nonRSC_energy.csv
$offdelim
$onlisting
;
$offempty

*Created using input_processing\writecapdat.py
$onempty
table prescribedrsc(allt,pcat,r,*) "--MW-- raw prescribed capacity data for RSC tech created by .\input_processing\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_rsc.csv
$offdelim
$onlisting
;
$offempty

$onempty
*For onshore and offshore wind, use outputs of hourlize to override what is in prescribedrsc
table prescribed_wind_ons(r,allt,*) "--MW-- prescribed wind capacity, created by hourlize"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_builds_wind-ons.csv
$offdelim
$onlisting
;
$offempty

prescribedrsc(allt,"wind-ons",r,"value") = prescribed_wind_ons(r,allt,"capacity") ;

$onempty
table prescribed_wind_ofs(r,allt,*) "--MW-- prescribed wind capacity, created by hourlize"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_builds_wind-ofs.csv
$offdelim
$onlisting
;
$offempty

prescribedrsc(allt,"wind-ofs",r,"value") = prescribed_wind_ofs(r,allt,"capacity") ;

*created by /input_processing/writecapdat.py
*following does not include wind
*Retirements for techs binned by heatrates are handled in hintage_data.csv
$onempty
table prescribedretirements(allt,r,i,*) "--MW-- raw prescribed power capacity retirement data for non-RSC, non-heatrate binned tech created by /input_processing/writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%retirements.csv
$offdelim
$onlisting
;
$offempty

*created by /input_processing/writecapdat.py
*Retirements for techs binned by heatrates are handled in hintage_data.csv
$onempty
table prescribedretirements_energy(allt,r,i,*) "--MWh-- raw prescribed energy capacity retirement data for battery tech created by /input_processing/writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%retirements_energy.csv
$offdelim
$onlisting
;
$offempty

$onempty
parameter forced_retirements(i,st) "--integer-- year in which to force retirements of certain techs by state"
/
$offlisting
$ondelim
$include inputs_case%ds%forced_retirements.csv
$offdelim
$onlisting
/ ;
$offempty

set forced_retire(i,r,t) ;

forced_retire(i,r,t)$[sum{st$r_st(r,st), (yeart(t)>=forced_retirements(i,st))$forced_retirements(i,st) }] = yes ;
* If the technology you would upgrade to is part of forced_retire, then include the
* upgrade tech in forced_retire
forced_retire(i,r,t)$[upgrade(i)$(sum{ii$upgrade_to(i,ii), forced_retire(ii,r,t) })] = yes ;

set hintage_char "characteristics available in hintage_data"
/
$offlisting
$include inputs_case%ds%hintage_char.csv
$onlisting
/ ;

*created by /input_processing/writehintage.py
table hintage_data(i,v,r,allt,hintage_char) "table of existing unit characteristics written by writehintage.py"
$offlisting
$ondelim
$include inputs_case%ds%hintage_data.csv
$offdelim
$onlisting
;

* if not updating heat rate on upgrades, change to the default value
if((not Sw_UpgradeHeatRateAdj),
  hintage_data(i,initv,r,t,"wCCS_Retro_HR")$hintage_data(i,initv,r,t,"wCCS_Retro_HR")
          = hintage_data(i,initv,r,t,"wHR") ;
) ;

set upgrade_hintage_char(hintage_char) "sets to operate over in extension of hintage_data characteristics when sw_upgrades = 1"
/
$offlisting
$ondelim
$include inputs_case%ds%upgrade_hintage_char.csv
$offdelim
$onlisting
/ ;

* need to extend characteristics for years where a tech could still exist if it was upgraded in a previous year
* - ie a hintages characteristics would need to persist if it is upgraded and has a lifetime extension
if(Sw_Upgrades = 1,
* need to loop over the model years as we set values to the previous modeled year that will
* also need to be updated given the check for whether data exists in current year or not
  loop(tt$tmodel_new(tt),
* if there is still capacity for upgradeable units in Sw_UpgradeYear
* make sure to extend their characteristics out beyond Sw_UpgradeYear
    hintage_data(i,v,r,tt,upgrade_hintage_char)$[sum{ii,upgrade_from(ii,i) }
                                                $sum{ttt$[ttt.val = Sw_UpgradeYear],hintage_data(i,v,r,ttt,"cap") }
                                                $(not hintage_data(i,v,r,tt,upgrade_hintage_char))]

* set to the previous modeled year relative to the looped year
                = sum{ttt$tprev(tt,ttt), hintage_data(i,v,r,ttt,upgrade_hintage_char) } ;
  ) ;
) ;

*created by /input_processing/writecapdat.py
parameter binned_capacity(i,v,r,allt) "existing capacity (that is not rsc, but including distpv) binned by heat rates" ;

binned_capacity(i,v,r,allt) = hintage_data(i,v,r,allt,"cap") ;

parameter maxage(i) "--years-- maximum age for technologies"
/
$offlisting
$ondelim
$include inputs_case%ds%maxage.csv
$offdelim
$onlisting
/ ;
* generators not included in maxage.csv get maxage=100 years
maxage(i)$[not maxage(i)] = maxage_default ;
* upgrades and cooling-water techs inherit maxage from the base tech
maxage(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), maxage(ii) } ;
maxage(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), maxage(ii) } ;

*loading in capacity mandates here to avoid conflicts in calculation of valcap
* declared over allt to allow for external data files that extend beyond end_year
$onempty
parameter batterymandate(st,allt) "--MW-- cumulative battery mandate levels"
/
$offlisting
$ondelim
$include inputs_case%ds%storage_mandates.csv
$offdelim
$onlisting
/ ;
$offempty

scalar firstyear_battery "--year-- the first year battery technologies can be built, used to enforce storage mandate" ;
firstyear_battery = smin(i$battery(i),firstyear(i)) ;

$onempty
table offshore_cap_req(st,allt) "--MW-- offshore wind capacity requirement by state"
$offlisting
$ondelim
$include inputs_case%ds%offshore_req.csv
$offdelim
$onlisting
;
$offempty

parameter r_offshore(r,t) "regions where offshore wind is required by a mandate" ;
r_offshore(r,t)$[sum{st$r_st(r,st), offshore_cap_req(st,t) }] = 1 ;

* initial smr capacity to ensure that exogenous H2 demand can be supplied, csv is written by writecapdat.py
$onempty
parameter h2_existing_smr_cap(r,t) "--MW-- capacity of existing SMR - used for meeting H2 demand before new H2 producing tech deployment is allowed to begin"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_existing_smr_cap.csv
$offdelim
$onlisting
/ ;
$offempty

*==========================================
*     --- Canadian Imports/Exports ---
*==========================================

$ifthene.Canada %GSw_Canada% == 1
* declared over allt to allow for external data files that extend beyond end_year
$onempty
table can_imports(r,allt) "--MWh-- [Sw_Canada=1] Imports from Canada by year"
$offlisting
$ondelim
$include inputs_case%ds%can_imports.csv
$offdelim
$onlisting
;

parameter can_imports_capacity(r,allt) "--MW-- [Sw_Canada=1] Peak Canadian import capacity"
/
$offlisting
$ondelim
$include inputs_case%ds%can_imports_capacity.csv
$offdelim
$onlisting
/ ;

table can_exports(r,allt) "--MWh-- [Sw_Canada=1] Exports to Canada by year"
$offlisting
$ondelim
$include inputs_case%ds%can_exports.csv
$offdelim
$onlisting
;
$offempty

$endif.Canada



*=============================
* Resource supply curve setup
*=============================

* Written by writesupplycurves.py
parameter rsc_dat(i,r,sc_cat,rscbin) "--units vary-- resource supply curve data for renewables with capacity in MW and costs in $/MW (MW-DC and $/MW-AC for UPV)"
/
$offlisting
$ondelim
$include inputs_case%ds%rsc_combined.csv
$offdelim
$onlisting
/ ;

* Written by writesupplycurves.py
$onempty
parameter rsc_evmc(i,r,sc_cat,rscbin,t) "--units vary-- resource supply curve data for shape-like EVMC"
/
$offlisting
$ondelim
$include inputs_case%ds%rsc_evmc.csv
$offdelim
$onlisting
/ ;
$offempty

* Written by writesupplycurves.py
$onempty
parameter geo_discovery_factor(i,r) "--fraction-- factor representing undiscovered geothermal"
/
$offlisting
$ondelim
$include inputs_case%ds%geo_discovery_factor.csv
$offdelim
$onlisting
/ ;
$offempty

* Written by writesupplycurves.py
$onempty
parameter geo_discovery_rate(allt) "--fraction-- fraction of undiscovered geothermal that has been 'discovered'"
/
$offlisting
$ondelim
$include inputs_case%ds%geo_discovery_rate.csv
$offdelim
$onlisting
/ ;
$offempty

parameter geo_discovery(i,r,allt) "--fraction-- fraction of undiscovered geothermal that has been 'discovered'" ;
geo_discovery(i,r,t)$geo_hydro(i) = (1 - geo_discovery_factor(i,r)) * geo_discovery_rate(t) + geo_discovery_factor(i,r) ;

* read data defining increase in hydropower upgrade availability over time. should only exist for hydUD and hydUND
$onempty
table hyd_add_upg_cap(r,i,rscbin,allt) "--MW-- cumulative increase in available upgrade capacity relative to base year"
$offlisting
$ondelim
$include inputs_case%ds%hyd_add_upg_cap.csv
$offdelim
$onlisting
;
$offempty

parameter distance_spur(i,r,rscbin) "--miles-- Spur line distance"
/
$offlisting
$ondelim
$include inputs_case%ds%distance_spur.csv
$offdelim
$onlisting
/ ;

parameter distance_reinforcement(i,r,rscbin) "--miles-- Network reinforcement distance"
/
$offlisting
$ondelim
$include inputs_case%ds%distance_reinforcement.csv
$offdelim
$onlisting
/ ;

**rsc_dat adjustments (see additional adjustments to m_rsc_dat further below)

*need to adjust units for pumped hydro costs from $ / KW to $ / MW
rsc_dat("pumped-hydro",r,"cost",rscbin) = rsc_dat("pumped-hydro",r,"cost",rscbin) * 1000 ;

*need to adjust units for hydro costs from $ / KW to $ / MW
rsc_dat(i,r,"cost",rscbin)$hydro(i) = rsc_dat(i,r,"cost",rscbin) * 1000 ;

*To allow pumped-hydro-flex via rscfeas and m_rscfeas, we set its supply curve capacity equal to pumped-hydro fixed.
*Note however that they will share the same supply curve capacity (see rsc_agg).
rsc_dat("pumped-hydro-flex",r,"cap",rscbin) = rsc_dat("pumped-hydro",r,"cap",rscbin) ;

*Make pumped-hydro-flex more expensive than fixed pumped-hydro by a fixed percent
rsc_dat("pumped-hydro-flex",r,"cost",rscbin) = rsc_dat("pumped-hydro",r,"cost",rscbin) * %GSw_HydroVarPumpCostRatio% ;

$ontext
Replicate the UPV supply curve data for hybrid PV+battery
"rsc_data" for hybrid PV+battery is never used in the resource constraint (see note above about rsc_dat and tg_rsc_upvagg).
This copy is necessary to ensure the conditionals for the supply curve investment variables get created for pvb.
Example: "m_rscfeas(r,i,rscbin)" is created for "eq_rsc_inv_account"
$offtext

rsc_dat(i,r,sc_cat,rscbin)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], rsc_dat(ii,r,sc_cat,rscbin) } ;

*following set indicates which combinations of r and i are possible
*this is based on whether or not the bin has capacity available
rscfeas(i,r,rscbin)$rsc_dat(i,r,"cap",rscbin) = yes ;

rscfeas(i,r,rscbin)$[csp2(i)$sum{ii$[csp1(ii)$csp2(i)$tg_rsc_cspagg(ii,i)], rscfeas(ii,r,rscbin) }] = yes ;
rscfeas(i,r,rscbin)$[csp3(i)$sum{ii$[csp1(ii)$csp3(i)$tg_rsc_cspagg(ii,i)], rscfeas(ii,r,rscbin) }] = yes ;
rscfeas(i,r,rscbin)$[csp4(i)$sum{ii$[csp1(ii)$csp4(i)$tg_rsc_cspagg(ii,i)], rscfeas(ii,r,rscbin) }] = yes ;

*expand feasibility and supply curve data for water-enumerated PSH techs
*m_rsc_con will still require all PSH types to use the same resource base
rscfeas(i,r,rscbin)$[psh(i)$Sw_WaterMain$sum{ii$ctt_i_ii(i,ii), rsc_dat(ii,r,"cap",rscbin) }] = yes ;

rscfeas(i,r,rscbin)$ban(i) = no ;

*expand feasibility and supply curve data to include evmc techs
rscfeas(i,r,rscbin)$sum{t, rsc_evmc(i,r,"cap",rscbin,t) } = yes ;

* This flag will deactivate eq_rsc_INVLIM when the RHS is < 1e-6 and set INV_RSC
* to zero for the r,i,rscbin combination. Because INV_RSC is a positive variable
* and RHS < 1e-6, INV_RSC would have to be < 1e-6 (which is basically zero).
set flag_eq_rsc_INVlim(r,i,rscbin,t) "flag for when there are small numbers in the RHS of eq_rsc_INVlim" ;
parameter rhs_eq_rsc_INVlim(r,i,rscbin,t) "RHS value of eq_rsc_INVlim" ;

*Initialize values to 'no'
flag_eq_rsc_INVlim(r,i,rscbin,t) = no ;

parameter binned_heatrates(i,v,r,allt) "--MMBtu / MWh-- existing capacity binned by heat rates" ;
binned_heatrates(i,v,r,allt) = hintage_data(i,v,r,allt,"wHR") ;


*Created by hourlize
*declared over allt to allow for external data files that extend beyond end_year
* Written by writesupplycurves.py
$onempty
parameter exog_wind_ons_rsc(i,r,rscbin,allt) "exogenous (pre-tfirst) wind capacity binned by capacity factor and rscbin"
/
$offlisting
$ondelim
$include inputs_case%ds%exog_wind_ons_rsc.csv
$offdelim
$onlisting
/ ;
$offempty

parameter exog_wind_ons(i,r,allt) "exogenous (pre-tfirst) wind capacity binned by capacity factor" ;
exog_wind_ons(i,r,t) = sum{rscbin, exog_wind_ons_rsc(i,r,rscbin,t) } ;

*Created by hourlize
*declared over allt to allow for external data files that extend beyond end_year
* Written by writesupplycurves.py
$onempty
parameter exog_upv_rsc(i,r,rscbin,allt) "exogenous (pre-tfirst) upv capacity binned by capacity factor and rscbin"
/
$offlisting
$ondelim
$include inputs_case%ds%exog_upv_rsc.csv
$offdelim
$onlisting
/ ;
$offempty

parameter exog_upv(i,r,allt) "exogenous (pre-tfirst) upv capacity binned by capacity factor" ;
exog_upv(i,r,t) = sum{rscbin, exog_upv_rsc(i,r,rscbin,t) } ;

parameter avail_retire_exog_rsc(i,v,r,t) "--MW-- available retired capacity for refurbishments" ;
avail_retire_exog_rsc(i,v,r,t) = 0 ;

* declared over allt to allow for external data files that extend beyond end_year
$onempty
parameter capacity_exog(i,v,r,allt)             "--MW-- exogenously specified capacity",
          capacity_exog_energy(i,v,r,allt)      "--MWh-- exogenously specified energy capacity",
          capacity_exog_rsc(i,v,r,rscbin,allt)  "--MW-- exogenous (pre-tfirst) capacity for wind-ons and upv",
          m_capacity_exog(i,v,r,allt)           "--MW-- exogenous power capacity used in the model",
          m_capacity_exog_energy(i,v,r,allt)    "--MWh-- exogenous energy capacity used in the model",
          geo_cap_exog(i,r)                     "--MW-- existing geothermal capacity"
/
$offlisting
$ondelim
$include inputs_case%ds%geoexist.csv
$offdelim
$onlisting
/ ;
$offempty

set exog_rsc(i) "RSC techs whose exogenous (pre-tfirst) capacity is tracked by rscbin" ;
exog_rsc(i)$(onswind(i)) = yes ;
exog_rsc(i)$(upv(i)) = yes ;

*Created by hourlize
*declared over allt to allow for external data files that extend beyond end_year
* Written by writesupplycurves.py
$onempty
parameter exog_geohydro_allkm_rsc(i,r,rscbin,allt) "exogenous (pre-tfirst) geohydro_allkm capacity binned by temperature and rscbin"
/
$offlisting
$ondelim
$ifthene.readgeohydrorevexog ((%GSw_Geothermal%<>0)and(sameas(%geohydrosupplycurve%,reV)))
$include inputs_case%ds%exog_geohydro_allkm_rsc.csv
$endif.readgeohydrorevexog
$offdelim
$onlisting
/ ;
$offempty

*reset all geothermal exogenous capacity levels
capacity_exog(i,v,r,t)$geo(i) = 0 ;

$ifthen.geohydrorevexog %geohydrosupplycurve% == 'reV'
parameter exog_geohydro_allkm(i,r,allt) "exogenous (pre-tfirst) geohydro_allkm capacity binned by temperature" ;
exog_geohydro_allkm(i,r,t) = sum{rscbin, exog_geohydro_allkm_rsc(i,r,rscbin,t) } ;
exog_rsc(i)$(geo_hydro(i)) = yes ;
capacity_exog(i,"init-1",r,t)$geo_hydro(i) = exog_geohydro_allkm(i,r,t) ;
capacity_exog_rsc(i,"init-1",r,rscbin,t)$geo_hydro(i) = exog_geohydro_allkm_rsc(i,r,rscbin,t) ;
$else.geohydrorevexog
capacity_exog(i,"init-1",r,t)$geo_hydro(i) = geo_cap_exog(i,r) ;
$endif.geohydrorevexog

capacity_exog(i,"init-1",r,t)$geo_egs(i) = geo_cap_exog(i,r) ;

* existing capacity equals all 2010 capacity less retirements
* here we use the max of zero or that number to avoid any errors
* with variables that are gte to zero
* also have expiration of capital if t - tfirst is greater than the maximum age
* note the first conditional limits this calculation to units that
* do NOT have their capacity binned by heat rates (this include distpv for reasons explained below)
capacity_exog(i,"init-1",r,t)${[yeart(t)-sum{tt$tfirst(tt),yeart(tt) }<maxage(i)]} =
                                 max(0,capnonrsc(i,r,"value")
                                       - sum{allt$[allt.val <= t.val],  prescribedretirements(allt,r,i,"value") }
                                    ) ;

capacity_exog_energy(i,"init-1",r,t)${[yeart(t)-sum{tt$tfirst(tt),yeart(tt) }<maxage(i)]} =
                                 max(0,capnonrsc_energy(i,r,"value")
                                       - sum{allt$[allt.val <= t.val],  prescribedretirements_energy(allt,r,i,"value") }
                                    ) ;

*reset any exogenous capacity that is also specified in binned_capacity
*as these are computed based on bins specified by the numhintage global
*in the data-writing files
capacity_exog(i,v,r,t)$[initv(v)$(sum{(vv,rr)$[initv(vv)], binned_capacity(i,vv,rr,t) })] = 0 ;

capacity_exog("hydED","init-1",r,t) = caprsc("hydED",r,"value") ;
capacity_exog("hydEND","init-1",r,t) = caprsc("hydEND",r,"value") ;
capacity_exog(i,v,r,t)$[sum{allt, binned_capacity(i,v,r,allt) }] =
               sum{allt$att(allt,t), binned_capacity(i,v,r,allt) } ;

*reset all wind exogenous capacity levels
capacity_exog(i,v,r,t)$wind(i) = 0 ;

capacity_exog(i,"init-1",r,t)$onswind(i) = exog_wind_ons(i,r,t) ;
capacity_exog_rsc(i,"init-1",r,rscbin,t)$onswind(i) = exog_wind_ons_rsc(i,r,rscbin,t) ;

*reset all upv exogenous capacity levels
capacity_exog(i,v,r,t)$upv(i) = 0 ;

capacity_exog(i,"init-1",r,t)$upv(i) = exog_upv(i,r,t) ;
capacity_exog_rsc(i,"init-1",r,rscbin,t)$upv(i) = exog_upv_rsc(i,r,rscbin,t) ;

*capacity for geothermal is determined through forcing of prescribed builds
*geothermal is also not a valid technology and rather a placeholder
capacity_exog("geothermal",v,r,t) = 0 ;

*capacity for hydro is specified for technologies in RSC techs
*ie hydro has specific classes (e.g. HydEd) that are specified
*separately, therefore the general 'hydro' category is not needed
capacity_exog("hydro",v,r,t) = 0 ;

* set existing capacity for smr
capacity_exog("smr","init-1",r,t)$Sw_H2 = h2_existing_smr_cap(r,t) ;

$ifthene.Canada %GSw_Canada% == 1
*set Canadian imports as prescribed capacity
capacity_exog("can-imports","init-1",r,t) = can_imports_capacity(r,t) ;
$endif.Canada

*if you've declined in value
avail_retire_exog_rsc(i,v,r,t)$[refurbtech(i)$(capacity_exog(i,v,r,t-1) > capacity_exog(i,v,r,t))] =
    capacity_exog(i,v,r,t-1) - capacity_exog(i,v,r,t) ;

avail_retire_exog_rsc(i,v,r,t)$[not initv(v)] = 0 ;

m_capacity_exog(i,v,r,t)$capacity_exog(i,v,r,t) = capacity_exog(i,v,r,t) ;
m_capacity_exog_energy(i,v,r,t)$capacity_exog_energy(i,v,r,t) = capacity_exog_energy(i,v,r,t) ;
m_capacity_exog(i,"init-1",r,t)$geo(i) = geo_cap_exog(i,r) ;

* We assign the ~1.3 GW of exising csp-ns to upv throughout the model, but then
* convert 1.3 GW of upv back to csp-ns in the output processing.
$onempty
parameter cap_cspns(r,allt) "--MW-- csp-ns capacity"
/
$offlisting
$ondelim
$include inputs_case%ds%cap_cspns.csv
$offdelim
$onlisting
/ ;
$offempty


* with regional h2 demands, we assume capacity follows demand and thus load in
* national demand values, the shares of national demand by each BA
* we then convert those to MW of capacity using the conversion of tons / mw
*
parameter h2_exogenous_demand(p,allt) "--metric tons/yr-- exogenous demand for hydrogen"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_exogenous_demand.csv
$offdelim
$onlisting
/ ;
* h2_exogenous_demand.csv is in million tons so convert to tons
h2_exogenous_demand(p,t) = 1e6 * h2_exogenous_demand(p,t) ;

scalar h2_demand_start  "--year-- first year that h2 demand should be modeled"
       h2_gen_firstyear "--year-- first year that h2 generation technologies are available"
;

* Identify the first year that hydrogen generation technologies are allowed
h2_gen_firstyear = smin{i$[h2_combustion(i)$(not ban(i))], firstyear(i) } ;

* Set h2_demand_start to the first year that there is data
* in h2_exogenous_demand
h2_demand_start = smin{t$[sum{p, h2_exogenous_demand(p,t)}], yeart(t) } ;

* If h2_gen_firstyear is smaller than h2_demand_start, set h2_demand_start
* to be h2_gen_firstyear
h2_demand_start$[h2_gen_firstyear<h2_demand_start] = h2_gen_firstyear ;


parameter h2_share(r,allt) "--fraction-- regional share of national hydrogen demand"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_ba_share.csv
$offdelim
$onlisting
/ ;

*Units for electrolyzer:
*  Overnight Capital Cost ($/kW)
*  FOM  ($/kW-yr)
*  Elec Efficiency (kWh/kg)
*Units for SMR:
*  Overnight Capital Cost ($/(kg/day))
*  FOM  ($/(kg/day)-yr)
*  Elec Efficiency (kWh/kg)
*  NG Efficiency (MMBtu/kg)
parameter consume_char0(i,allt,*) "--units vary (see commented text above)-- input plant characteristics"
$offlisting
$ondelim
$offdigit
/
$include inputs_case%ds%consume_char.csv
/
$ondigit
$offdelim
$onlisting
;

parameter inv_distpv(r,t) "--MW-- capacity of distpv that is build in year t (i.e., INV for distpv)" ;

inv_distpv(r,t) = sum{(i,v)$distpv(i),
                      m_capacity_exog(i,v,r,t) - sum{tt$tprev(t,tt), m_capacity_exog(i,v,r,tt) }
                     } ;

set valcap(i,v,r,t)            "i, v, r, and t combinations that are allowed for capacity",
    valcap_init(i,v,r,t)       "Initialized i,v,r, and t combinations that are allowed for capacity, while valcap can change",
    valcap_remove(i,v,r,t,tt)  "i, v, r, t combination that are removed as the model progresses through time",
    valcap_irt(i,r,t)          "i, r, and t combinations that are allowed for capacity",
    valcap_i(i)                "i that are allowed for capacity",
    valcap_iv(i,v)             "i and v combinations that are allowed for capacity",
    valcap_ir(i,r)             "i and r combinations that are allowed for capacity",
    valcap_ivr(i,v,r)          "i, v, and r combinations that are allowed for capacity",
    valcap_h2ptc(i,v,r,t)      "i, v, r and t combinations that are allowed for capacity that can receive the hydrogen PTC",
    valgen_irt(i,r,t)          "i, r, and t combinations that are allowed for generation",
    valinv(i,v,r,t)            "i, v, r, and t combinations that are allowed for investments",
    valinv_init(i,v,r,t)       "Initialized i, v, r, and t combinations that are allowed for investments, while valinv can change",
    valinv_irt(i,r,t)          "i, r, and t combinations that are allowed for investments",
    valinv_tg(st,tg,t)         "valid technology groups for investments"
    valgen(i,v,r,t)            "i, v, r, and t combinations that are allowed for generation",
    valgen_h2ptc(i,v,r,t)        "i, v, r and t combinations that are allowed for generation that can receive the hydrogen PTC",
    m_refurb_cond(i,v,r,t,tt)  "i v r combinations that are built in tt that can be refurbished in t",
    m_rscfeas(r,i,rscbin)      "--qualifier-- feasibility conditional for investing in RSC techs"
;


* define qualifier for renewable supply curve investment variables
m_rscfeas(r,i,rscbin) = rscfeas(i,r,rscbin) ;
* CSP
m_rscfeas(r,i,rscbin)$[csp(i)$(not ban(i))$sum{ii$[(not ban(ii))$tg_rsc_cspagg(ii, i)], m_rscfeas(r,ii,rscbin) }] = yes ;
* Hybrid PV+battery
m_rscfeas(r,i,rscbin)$[pvb(i)$(not ban(i))$sum{ii$[(not ban(ii))$tg_rsc_upvagg(ii, i)], m_rscfeas(r,ii,rscbin) }] = yes ;

parameter m_required_prescriptions(pcat,r,t)        "--MW-- required power prescriptions by year (cumulative)" ;

parameter m_required_prescriptions_energy(pcat,r,t) "--MWh-- required energy prescriptions by year (cumulative)" ;

*following does not include wind
*conditional here is due to no prescribed retirements for RSC tech
*distpv is an rsc tech but is handled different via binned_capacity as explained above
m_required_prescriptions(pcat,r,t)$tmodel_new(t)
          = sum{tt$[yeart(t)>=yeart(tt)], prescribednonrsc(tt,pcat,r,"value") } ;


m_required_prescriptions(pcat,r,t)$[tmodel_new(t)
                                   $(sum{tt$[yeart(t)>=yeart(tt)], prescribedrsc(tt,pcat,r,"value") }
                                     or caprsc(pcat,r,"value"))]
        = sum{(tt)$[(yeart(t) >= yeart(tt))], prescribedrsc(tt,pcat,r,"value") }
        + caprsc(pcat,r,"value")
;

m_required_prescriptions_energy(pcat,r,t)$tmodel_new(t)
          = sum{tt$[yeart(t)>=yeart(tt)], prescribednonrsc_energy(tt,pcat,r,"value") } ;

parameter degrade(i,t,tt) "degradation factor by i"
          degrade_pcat(pcat,t,tt) "degradation factor by pcat" ;

parameter degrade_annual(i) "annual degredation rate"
/
$offlisting
$ondelim
$include inputs_case%ds%degradation_annual.csv
$offdelim
$onlisting
/ ;

* Hybrid degradation is initially defined as the battery degradation for calculating the ITC for the hybrid battery (degradation_annual_default.csv).
* Here, reassign hybrid PV+Battery to have the same value as UPV.
* Currently the degradation for the battery is zero, but if becomes non-zero, then two separate degradation factors should be defined
* (e.g., degrade_pvb_p, degrade_pvb_b) to allow for degradation to be applied to both the PV and battery.
degrade_annual(i)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], degrade_annual(ii) } ;

degrade_annual(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), degrade_annual(ii) } ;

degrade(i,t,tt)$[(yeart(tt)>=yeart(t))$(not ban(i))] = 1 ;
degrade(i,t,tt)$[(yeart(tt)>=yeart(t))$(not ban(i))] = (1-degrade_annual(i))**(yeart(tt)-yeart(t)) ;

set prescription_check(i,v,r,t) "check to see if prescriptive capacity comes online in a given year" ;

parameter noncumulative_prescriptions(pcat,r,t) "--MW-- prescribed capacity that comes online in a given year" ;
* need to fill in for unmodeled, gap years via tprev but
* tprev is not defined with tprev(t,tfirst)
noncumulative_prescriptions(pcat,r,t)$tmodel_new(t)
                                  = sum{tt$[(yeart(tt)<=yeart(t)
* this condition populates values of tt which exist between the
* previous modeled year and the current year
                                          $(yeart(tt)>sum{ttt$tprev(t,ttt), yeart(ttt) }))
                                          ],
                                        prescribednonrsc(tt,pcat,r,"value") + prescribedrsc(tt,pcat,r,"value")
                                      } ;

parameter noncumulative_prescriptions_energy(pcat,r,t) "--MWh-- prescribed energy capacity that comes online in a given year" ;
noncumulative_prescriptions_energy(pcat,r,t)$tmodel_new(t)
                                  = sum{tt$[(yeart(tt)<=yeart(t)
                                          $(yeart(tt)>sum{ttt$tprev(t,ttt), yeart(ttt) }))
                                          ],
                                        prescribednonrsc_energy(tt,pcat,r,"value")
                                      } ;

prescription_check(i,newv,r,t)$[sum{pcat$prescriptivelink(pcat,i), noncumulative_prescriptions(pcat,r,t) }
                                 $ivt(i,newv,t)$tmodel_new(t)$(not ban(i))] = yes ;

*Extend feasibility for prescribed rsc capacity where there is no supply curve data.
*Resource will be manualy added to supply curve in bin1 in these cases.
*Only enable for bin1 if there is no resource in any bins to keep parameter size down.
m_rscfeas(r,i,"bin1")$[sum{(pcat,t)$[sameas(pcat,i)$tmodel_new(t)], noncumulative_prescriptions(pcat,r,t) }$rsc_i(i)$(not bannew(i))$(sum{rscbin, rsc_dat(i,r,"cap",rscbin) }=0)] = yes ;

*==========================================================
*--- Interconnection queues (Capacity deployment limit) ---
*==========================================================
alias(tg,tgg) ;

$onempty
table cap_limit(tg,r,allt) "--MW-- capacity deployment limit by region and technology based on interconnection queues"
$offlisting
$ondelim
$include inputs_case%ds%cap_limit.csv
$offdelim
$onlisting
;
$offempty


parameter cap_penalty(tg) "--per MW-- cost penalty for capacity deployment above cap limit"
/
$offlisting
$ondelim
$include inputs_case%ds%cap_penalty.csv
$offdelim
$onlisting
/ ;

*=============================================
* -- Explicit spur-line capacity (if used) --
*=============================================

* Indicate which technologies have spur lines handled endogenously (none by default)
set spur_techs(i) "Generators with endogenous spur lines" ;
spur_techs(i) = no ;

* Written by writesupplycurves.py
$onempty
set x "reV resource sites"
/
$offlisting
$include inputs_case%ds%x.csv
$onlisting
/ ;

* Written by writesupplycurves.py
parameter spurline_cost(x) "--$/MW-- Spur-line cost for each reV site"
/
$offlisting
$ondelim
$include inputs_case%ds%spurline_cost.csv
$offdelim
$onlisting
/ ;

* Written by writesupplycurves.py
set spurline_sitemap(i,r,rscbin,x) "Mapping set from generators to reV sites"
/
$offlisting
$ondelim
$include inputs_case%ds%spurline_sitemap.csv
$offdelim
$onlisting
/ ;

* Written by writesupplycurves.py
set x_r(x,r) "Mapping set from reV sites to model regions"
/
$offlisting
$ondelim
$include inputs_case%ds%x_r.csv
$offdelim
$onlisting
/ ;
$offempty

* Include techs in spurline_sitemap in spur_techs (currently only wind-ons and upv)
$ifthene.spursites %GSw_SpurScen% == 1
spur_techs(i)$(onswind(i) or upv(i)) = yes ;

$ifthen.geohydrorev %geohydrosupplycurve% == 'reV'
spur_techs(i)$(geo_hydro(i)) = yes ;
$endif.geohydrorev

$ifthen.egsrev %egssupplycurve% == 'reV'
spur_techs(i)$(geo_egs_allkm(i)) = yes ;
$endif.egsrev

$endif.spursites

* Indicate which reV sites are included in the model
set xfeas(x) "Sites to include in the model" ;
xfeas(x)$sum{r$x_r(x,r), 1} = yes ;


*==========================================
* -- Initialize tc_phaseout_mult --
*==========================================
*initialize tc_phaseout_mult with full value
tc_phaseout_mult(i,v,t)$tmodel_new(t) = 1 ;
tc_phaseout_mult_t(i,t)$tmodel_new(t) = 1 ;

*==========================================
* -- Valid Capacity and Generation Sets --
*==========================================

* -- valcap specification --
* first all available techs are included
* then we remove those as specified

* start with a blank slate
valcap(i,v,r,t) = no ;

*existing plants are enabled if not in ban(i)
valcap(i,v,r,t)$[m_capacity_exog(i,v,r,t)$(not ban(i))$tmodel_new(t)] = yes ;

* if a plant is still available by upgrade year
* and it is able to be upgraded - keep that plant in the valcap set
valcap(i,v,r,t)$[sum{tt$[tt.val = Sw_UpgradeYear], m_capacity_exog(i,v,r,tt) }
                $(Sw_Upgrades = 1)$(t.val >= Sw_UpgradeYear)
                $(not ban(i))
                $sum{ii, upgrade_from(ii,i) }$tmodel_new(t)] = yes ;

*enable all new classes for balancing regions
*if available (via ivt) and if not an rsc tech
*and if it is not in ban or bannew
*the year also needs to be greater than the first year indicated
*for that specific class (this is the summing over tt portion)
*or it needs to be specified in prescriptivelink
valcap(i,newv,r,t)$[(not rsc_i(i))$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $(sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) })$(not upgrade(i))
                    ]  = yes ;

*for rsc technologies, enabled if m_rscfeas is populated
*similarly to non-rsc technologies and there is the additional
*condition that m_rscfeas must contain values in at least one rscbin
valcap(i,newv,r,t)$[rsc_i(i)$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $sum{rscbin, m_rscfeas(r,i,rscbin) }$(not upgrade(i))
                    $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) }
                    ]  = yes ;

* Include EVMC technologies
valcap(i,newv,r,t)
    $[evmc(i)$tmodel_new(t)$(not ban(i))$(not bannew(i))
    $sum{rscbin, rsc_evmc(i,r,'cap',rscbin,t) }$sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) }
    ] = yes ;

*enable capacity if there is a required prescription in that region
*first for non-rsc techs
valcap(i,newv,r,t)$[(not rsc_i(i))
                    $(sum{pcat$prescriptivelink(pcat,i), m_required_prescriptions(pcat,r,t) })
                    $sum{tt$[sum{pcat$prescriptivelink(pcat,i), m_required_prescriptions(pcat,r,tt) }
                           $(yeart(tt)<=yeart(t))], ivt(i,newv,tt) }
                    $(not ban(i))] = yes ;

*then for rsc techs
valcap(i,newv,r,t)$[rsc_i(i)
                    $(sum{pcat$prescriptivelink(pcat,i), m_required_prescriptions(pcat,r,t) })
                    $sum{tt$[sum{pcat$prescriptivelink(pcat,i), m_required_prescriptions(pcat,r,tt) }
                           $(yeart(tt)<=yeart(t))], ivt(i,newv,tt) }
                    $(not ban(i))
                    $sum{rscbin, m_rscfeas(r,i,rscbin) }] = yes ;

* Techs where new investment are banned: Start by removing from valcap
valcap(i,newv,r,t)$bannew(i) = no ;
* Then add back only if they have prescribed capacity in years with the appropriate i/v/t combination
valcap(i,newv,r,t)
    $[bannew(i)
    $(not ban(i))
    $sum{(tt,pcat)$[ivt(i,newv,tt)$prescriptivelink(pcat,i)],
         noncumulative_prescriptions(pcat,r,tt) }]
    = yes ;

*NEW capacity only valid in historical years if and only if it has required prescriptions
*logic here is that we don't want to populate the constraint with CAP <= 0 and instead
*want to simply remove the consideration for CAP altogether and make the constraint unnecessary
*note that the constraint itself is also conditioned on valcap

*therefore remove the consideration of valcap if...
valcap(i,newv,r,t)$[
*if there are no required prescriptions
                   (not sum{pcat$prescriptivelink(pcat,i),
                      m_required_prescriptions(pcat,r,t) } )
*if the year is before the first year the technology is allowed
                   $(yeart(t)<firstyear(i))
*if there is not a mandate for that technology in the region
                   $(not ([r_offshore(r,t) and ofswind(i)] or [sum{st$r_st(r,st), batterymandate(st,t) } and battery(i)]))
                  ] = no ;

*remove vintages that cannot be built because they only occur before firstyear
valcap(i,newv,r,t)$[
*if there are no required prescriptions before the last year of that vintage
                   (not sum{(pcat,tt)$[prescriptivelink(pcat,i)
                                      $(yeart(tt)<=lastyear_v(i,newv))],
                      m_required_prescriptions(pcat,r,tt) } )
*if the vintage is not allowed before the firstyear
                   $(lastyear_v(i,newv)<firstyear(i))
*if there is not a mandate for that technology in the region
                   $(not ([r_offshore(r,t) and ofswind(i)] or [sum{st$r_st(r,st), batterymandate(st,t) } and battery(i)]))
                  ] = no ;

*remove any non-prescriptive build capabilities if they are not prescribed
valcap(i,newv,r,t)$[(not sameas(i,'gas-ct'))$(yeart(t)<firstyear(i))
                   $(not sum{tt$(yeart(tt)<=yeart(t)), prescription_check(i,newv,r,tt) })
                   $(not ([r_offshore(r,t) and ofswind(i)] 
                      or [sum{st$r_st(r,st), batterymandate(st,t) }  and battery(i)] ) ) ] 
                   = no ;

*enable prescribed builds of technologies that are earlier listed in bannew when Sw_WaterMain is ON
valcap(i,newv,r,t)$[Sw_WaterMain$sum{ctt$bannew_ctt(ctt),i_ctt(i,ctt) }$tmodel_new(t)
                  $sum{(tt,pcat)$[(yeart(tt)<=yeart(t))$sameas(pcat,i)], m_required_prescriptions(pcat,r,tt) }
                  $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) }] = yes ;


valcap(i,v,r,t)$[not tmodel_new(t)] = no ;
valcap(i,newv,r,t)$[not sum{tt$ivt(i,newv,tt),tmodel_new(tt) }] = no ;

*PSH is excluded because it is a unique case where the numeraire 'pumped-hydro' technology must remain
* in valcap with water constraints active because the existing fleet is not differentiated by water source.
valcap(i,v,r,t)$[i_numeraire(i)$(not psh(i))$Sw_WaterMain] = no ;


*upgraded init capacity is available if the tech from which it is
*upgrading is in valcap and not banned
valcap(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$(yeart(t)>=Sw_UpgradeYear)
                    $(yeart(t)>=firstyear(i))
                    $sum{ii$upgrade_from(i,ii), valcap(ii,initv,r,t) }
                    $(not ban(i))
                    $(not sum{ii$upgrade_to(i,ii), ban(ii) })
                    ] = yes ;

*upgrades from new techs are included in valcap if...
* it is an upgrade tech, the switch is enabled, and past the beginning upgrade year
valcap(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$(yeart(t)>=Sw_UpgradeYear)
*if the capacity that it is upgraded to is available
                   $sum{ii$upgrade_to(i,ii), valcap(ii,newv,r,t) }
*if the technology is not banned
                   $(not ban(i))
*if the technology you upgrade to is not banned
                   $(not sum{ii$upgrade_to(i,ii), ban(ii) })
*if it is past the first year that technology is available
                   $(yeart(t)>=firstyear(i))
*if it is a valid ivt combination which is duplicated from upgrade_to
                   $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) }
                   $(yeart(t)>=Sw_UpgradeYear)
                   ] = yes ;

*remove any upgrade considerations if before the upgrade year
valcap(i,v,r,t)$[upgrade(i)$(yeart(t)<Sw_UpgradeYear)] = no ;

*this is more of a failsafe for potential capacity leakage
valcap(i,v,r,t)$[upgrade(i)$(not Sw_Upgrades)] = no ;

*remove capacity from valcap that is required to retire (and cannot be upgraded)
* -then- remove m_capacity_exog from consideration
valcap(i,v,r,t)$[forced_retire(i,r,t)
                $(not sum{ii$(not forced_retire(ii,r,t)), upgrade_from(ii,i) })] = no ;

* for any technologies that are forced to retire and cannot upgrade, remove m_capacity_exog
m_capacity_exog(i,v,r,t)$[forced_retire(i,r,t)
                         $(not sum{ii$(not forced_retire(ii,r,t)), upgrade_from(ii,i) })] = 0 ;

* for any technologies that are forced to retire, can upgrade, and are not unabated coal, remove m_capacity_exog
m_capacity_exog(i,v,r,t)$[forced_retire(i,r,t)$(not coal_noccs(i))
                         $(sum{ii$(not forced_retire(ii,r,t)), upgrade_from(ii,i) })] = 0 ;

* if Clean Air Act requirements are enabled, coal technologies that can be upgraded are allowed to stay in m_capacity_exog
* if Clean Air Act requirements are not enabled, coal technologies that can be upgraded are excluded from m_capacity_exog
m_capacity_exog(i,v,r,t)$[forced_retire(i,r,t)$(not Sw_Clean_Air_Act)$coal_noccs(i)
                         $(sum{ii$(not forced_retire(ii,r,t)) ,upgrade_from(ii,i) })] = 0 ;

* If, in the last year in which coal must either retire or upgrade, coal is upgraded, we can continue to 
* use that m_capacity_exog beyond caa_coal_retire_year. But unabated coal plants must not have capacity after caa_coal_retire_year.
* This is expanded in d_solveoneyear.gms.
m_capacity_exog(i,v,r,t)$[forced_retire(i,r,t)$coal_noccs(i)
                         $(t.val > caa_coal_retire_year)
                         $(sum{ii$(not forced_retire(ii,r,t)), upgrade_from(ii,i) }) ] = 0 ;

* remove upgrade technologies that are explicitly banned
valcap(i,v,r,t)$[upgrade(i)$ban(i)] = no ;

*Restrict valcap for nuclear in BAs that are impacted By state nuclear bans
if(Sw_NukeStateBan = 1,
  valcap(i,v,r,t)$[nuclear(i)$newv(v)$nuclear_ba_ban(r)] = no ;
) ;

$ifthene.hydEDban %GSw_hydED% == 0
* Only leave hydED, turn off remaining hydro technologies
valcap(i,v,r,t)$[hydro(i)$(not sameas(i,"hydED"))] = no ;
$endif.hydEDban

* Drop vintages in non-modeled future years
valcap(i,v,r,t)$[(not sum{tt$[tmodel_new(tt)], ivt(i,v,tt) })$newv(v)] = no ;

* remove considerations for upgrades if the upgrade-from tech is invalid
valcap(i,v,r,t)$[upgrade(i)$(not sum{ii$upgrade_from(i,ii),valcap(ii,v,r,t) })] = no ;

* Remove non-offshore resources from offshore zones
valcap(i,v,r,t)$[offshore(r)$(not ofswind(i))] = no ;

* Add aggregations of valcap
valcap_irt(i,r,t) = sum{v, valcap(i,v,r,t) } ;
valcap_iv(i,v)$sum{(r,t)$tmodel_new(t), valcap(i,v,r,t) } = yes ;
valcap_ir(i,r)$sum{(v,t)$tmodel_new(t), valcap(i,v,r,t) } = yes ;
valcap_i(i)$sum{v, valcap_iv(i,v) } = yes ;
valcap_ivr(i,v,r)$sum{t, valcap(i,v,r,t) } = yes ;

* -- valinv specification --
valinv(i,v,r,t) = no ;
valinv(i,v,r,t)$[valcap(i,v,r,t)$ivt(i,v,t)] = yes ;

* Do not allow investments in regions where that technology is banned, expect for prescribed builds
valinv(i,v,r,t)$[tech_banned(i,r)$(not sum{pcat$prescriptivelink(pcat,i), noncumulative_prescriptions(pcat,r,t) })] = no ;

*remove non-prescribed numeraire technologies that remain in valcap
valinv(i,newv,r,t)$[i_numeraire(i)$Sw_WaterMain$(not sum{pcat$prescriptivelink(pcat,i), noncumulative_prescriptions(pcat,r,t) })] = no ;

*upgrades are not allowed for the INV variable as they are the sum of UPGRADES
valinv(i,v,r,t)$upgrade(i) = no ;

valinv(i,v,r,t)$[(yeart(t)<firstyear(i))
* Allow investments before firstyear(i) in technologies with prescribed capacity
                 $(not sum{pcat$prescriptivelink(pcat,i), noncumulative_prescriptions(pcat,r,t) })
* Allow investments before firstyear(i) in mandated technologies
                 $(not [sum{st$r_st(r,st), batterymandate(st,t) }  and battery(i)])
                 $(not [sum{st$r_st(r,st), offshore_cap_req(st,t)} and ofswind(i)])
                 ] = no ;

* Add aggregations of valinv
valinv_irt(i,r,t) = sum{v, valinv(i,v,r,t) } ;
valinv_tg(st,tg,t)$sum{(i,r)$[tg_i(tg,i)$r_st(r,st)], valinv_irt(i,r,t) } = yes ;

* -- valgen specification --
* if the balancing area and/or its
* resource supply regions have valid capacity
*then you can generate from it

valgen(i,v,r,t) = no ;
valgen(i,v,r,t)$valcap(i,v,r,t) = yes ;

* consuming technologies are not allowed to generate
valgen(i,v,r,t)$consume(i) = no ;

* Remove technologies that are required to retire
valgen(i,v,r,t)$forced_retire(i,r,t) = no ;

valgen_irt(i,r,t)$[sum{v,valgen(i,v,r,t) }] = yes ;

* -- valcap_h2ptc specification --

* technologies which can receive the hydrogen production tax credit because they comply as clean enough to power electrolyzers
 valcap_h2ptc(i,v,r,t)$[
* if you are a new vintage and built after h2_ptc_firstyear (this ensures the additionality requirement of the tax credit)
    newv(v)$(firstyear_v(i,v)>=h2_ptc_firstyear)
* if the generating tech itself is available
    $valcap(i,v,r,t)
* if the technology has low enough of emissions to comply with the policy
    $i_h2_ptc_gen(i)
    ] = yes ;

* -- valgen_h2ptc specification --
* generators that can receive the hydrogen production tax credit are available based on valcap_h2ptc
valgen_h2ptc(i,v,r,t)$valcap_h2ptc(i,v,r,t) = yes ; 


* -- m_refurb_cond specification --

* technologies can be refurbished if...
*  they are part of refurbtech
*  the number of years from tt to t are beyond the expiration of the tech (via maxage)
*  it is valid capacity in t, the current solve year.
*  it was a valid investment in year tt, the initial investment year.
m_refurb_cond(i,newv,r,t,tt)$[refurbtech(i)
                              $(yeart(tt)<yeart(t))
                              $(yeart(t) - yeart(tt) > maxage(i))
                              $valcap(i,newv,r,t)$valinv(i,newv,r,tt)
                             ] = yes ;


* -- inv_cond specification --

*if there is a link between the bintage and the year
*all previous years
*if the unit we invested in is not retired...
inv_cond(i,newv,r,t,tt)$[(not ban(i))
                      $tmodel_new(t)$tmodel_new(tt)
                      $(yeart(tt) <= yeart(t))
                      $valinv(i,newv,r,tt)
                      $(ord(t)-ord(tt) < maxage(i))
                      ] = yes ;

inv_cond(i,newv,r,t,tt)$[Sw_WaterMain$sum{ctt$bannew_ctt(ctt),i_ctt(i,ctt) }$tmodel_new(t)$tmodel_new(tt)
                      $sum{(pcat)$[sameas(pcat,i)], noncumulative_prescriptions(pcat,r,tt) }
                      $(yeart(tt) <= yeart(t))
                      $valinv(i,newv,r,tt)
                      $(ord(t)-ord(tt) < maxage(i))
                      ] = yes ;



* cannot restrict by valcap here to maintain compatibility with water techs
co2_captured_incentive(i,v,r,t) = co2_captured_incentive_in(i,v,t) ;

* expand to water techs
co2_captured_incentive(i,v,r,t)$[i_water_cooling(i)$Sw_WaterMain] = 
   sum{ii$ctt_i_ii(i,ii), co2_captured_incentive(ii,v,r,t) } ; 

* expand to upgrade techs
co2_captured_incentive(i,v,r,t)$[upgrade(i)$valcap(i,v,r,t)] =
   sum{ii$upgrade_to(i,ii),co2_captured_incentive(ii,v,r,t) } ;
   
* incentive for captured co2 for initial plants set to the amount available
* as of upgradeyear, similar to other performance and cost characteristics
co2_captured_incentive(i,v,r,t)$[initv(v)$upgrade(i)
                                    $valcap(i,v,r,t)$(Sw_Upgrades = 1)
                                    $(yeart(t)>=Sw_UpgradeYear)
                                    $(yeart(t) <= co2_capture_incentive_last_year_)] =
* note we populate the incentive for all years and then trim the incentive for later years
* when the upgrade occurs - this is after the solve statement in d_solveoneyear
* we also cast this forward based on whether or not a plant was built in that year
* but remove the last year for consideration of that below via co2_capture_incentive_last_year_
  sum{(ii,vv,tt)$[upgrade_to(i,ii)$newv(vv)
                $(firstyear_v(ii,vv) = Sw_UpgradeYear)
                $(yeart(tt) = Sw_UpgradeYear)],
            co2_captured_incentive(ii,vv,r,tt) } ;

* plants can only receive the CO2 capture incentive for the length of the incentive 'co2_capture_incentive_length', starting in the first year of that tech, vintage combination
co2_captured_incentive(i,newv,r,t)$[(yeart(t) > firstyear_v(i,newv) + co2_capture_incentive_length)] = 0 ;
* vintages whose first year comes after 'co2_capture_incentive_last_year_' cannot receive the CO2 capture incentive because the incentive is no longer available
co2_captured_incentive(i,newv,r,t)$[(firstyear_v(i,newv) > co2_capture_incentive_last_year_)] = 0 ;

* remove any invalid values to shrink parameter
co2_captured_incentive(i,v,r,t)$[not valcap(i,v,r,t)] = 0 ;

* making h2_ptc for all regions
h2_ptc(i,v,r,t)$valcap(i,v,r,t) = h2_ptc_in(i,v,t) ;

* if Sw_H2_PTC = 1, then tech 'electrolyzer' can also receive the hydrogen PTC, as designated in h2_ptc.
* Otherwise, we assume it receives $0/kg because the cleanliness of its carbon cannot be proven
h2_ptc("electrolyzer",v,r,t)$[(not Sw_H2_PTC)] = 0;

set h2_ptc_years(t) "years in which the hydrogen production incentive is active";
h2_ptc_years(t) = tmodel_new(t)$[sum{(i,v,r),h2_ptc(i,v,r,t)}];


*==========================================
* --- Parameters for water constraints ---
*==========================================

set sw(wst) "surface water types where access is based on consumption not withdrawal"
/
$offlisting
$ondelim
$include inputs_case%ds%sw.csv
$offdelim
$onlisting
/ ;

set i_water_surf(i) "subset of technologies that uses surface water",
  i_w(i,w) "linking set between technology and water use type used in constraining water availability" ;

i_water_surf(i)$[sum{(sw,ctt,ii)$i_ii_ctt_wst(i,ii,ctt,sw), 1}] = yes ;
i_w(i,"cons")$[i_water(i)$i_water_surf(i)] = yes ;
i_w(i,"with")$[i_water(i)$(not i_water_surf(i))] = yes ;

parameter wat_supply_init(wst,r) "-- million gallons per year -- water supply allocated to initial fleet " ;

*WatAccessAvail - water access available (Mgal/year)
*WatAccessCost - cost of water access (2004$/Mgal)
$onempty
parameter wat_supply_new(wst,*,r)   "-- million gallons per year , $ per million gallons per year -- water supply curve for post-2010 capacity with *=cap,cost"
/
$offlisting
$ondelim
$include inputs_case%ds%wat_access_cap_cost.csv
$offdelim
$onlisting
/ ;
$offempty

parameter m_watsc_dat(wst,*,r,t)   "-- million gallons per year, $ per million gallons per year -- water supply curve data with *=cap,cost" ;

* UnappWaterSeaDistr - seasonal distribution factors for new unappropriated water access
$onempty
table watsa_temp(wst,r,quarter)   "fractional quarterly allocation of water"
$offlisting
$ondelim
$include inputs_case%ds%unapp_water_sea_distr.csv
$offdelim
$onlisting
;
$offempty

m_watsc_dat(wst,"cost",r,t)$tmodel_new(t) = wat_supply_new(wst,"cost",r) ;

*not allowed to invest in upgrade techs since they are a product of upgrades
inv_cond(i,v,r,t,tt)$upgrade(i) = no ;


*===============================================
* --- Climate change impacts: Cooling water ---
*===============================================

$ifthen.climatewater %GSw_ClimateWater% == 1

* Indicate which cooling techs are affected by climate change
set wst_climate(wst) "water sources affected by climate change"
/
$offlisting
$ondelim
$include inputs_case%ds%wst_climate.csv
$offdelim
$onlisting
/ ;


* Update seasonal distribution factors for fsu; other water types are unchanged
* declared over allt to allow for external data files that extend beyond end_year

* Update water supply curve with annually-varying water supply. Multiplier is applied to (wat_supply_new + wat_supply_init).
* NOTE: Only the capacity changes, not the cost
* Written by climateprep.py
table wat_supply_climate(wst,r,allt)  "time-varying annual water supply"
$offlisting
$ondelim
$include inputs_case%ds%climate_UnappWaterMultAnn.csv
$offdelim
$onlisting
;
m_watsc_dat(wst,"cap",r,t)$[wst_climate(wst)$r_country(r,"USA")$tmodel_new(t)$(yeart(t)>=Sw_ClimateStartYear)] $=
  sum{allt$att(allt,t), m_watsc_dat(wst,"cap",r,t) * wat_supply_climate(wst,r,allt) } ;
* If wst is in wst_climate but does not have data in input file, assign its multiplier to the fsu multiplier
m_watsc_dat(wst,"cap",r,t)$[wst_climate(wst)$r_country(r,"USA")$tmodel_new(t)
                           $(yeart(t)>=Sw_ClimateStartYear)$sum{allt$att(allt,t), (not wat_supply_climate(wst,r,allt)) }] $=
  sum{allt$att(allt,t), m_watsc_dat(wst,"cap",r,t) * wat_supply_climate('fsu',r,allt) } ;

$endif.climatewater


*=====================================
* --- Regional Carbon Constraints ---
*=====================================

$onempty
set RGGI_States(st) "states with RGGI regulation"
/
$offlisting
$include inputs_case%ds%rggi_states.csv
$onlisting
/
;
$offempty

Set RGGI_r(r) "BAs with RGGI regulation" ;

RGGI_r(r)$[sum{st$RGGI_States(st),r_st(r,st) }] = yes ;

* declared over allt to allow for external data files that extend beyond end_year
parameter RGGI_cap(allt) "--metric tons-- CO2 emissions cap for RGGI states"
/
$offlisting
$ondelim
$include inputs_case%ds%rggicon.csv
$offdelim
$onlisting
/ ;

* These values are based on 42 MMT trajectory from section 8.1 of the CPUC "Inputs & Assumptions:
* "2019-2020 Integrated Resource Planning." This document can be found at
* ftp://ftp.cpuc.ca.gov/energy/modeling/Inputs%20%20Assumptions%202019-2020%20CPUC%20IRP%202020-02-27.pdf
$onempty
parameter state_cap(st,allt) "--metric tons-- CO2 emissions cap for state cap and trade policies"
/
$offlisting
$ondelim
$include inputs_case%ds%state_cap.csv
$offdelim
$onlisting
/ ;
$offempty


*==========================
* -- Climate heuristics --
*==========================
parameter climate_heuristics_yearfrac(allt) "--fraction-- annual scaling factor for climate heuristics"
$onempty
/
$offlisting
$ondelim
$include inputs_case%ds%climate_heuristics_yearfrac.csv
$offdelim
$onlisting
/ ;
$offempty

set climate_param "parameters defined in climate_heuristics_finalyear"
/
$offlisting
$include inputs_case%ds%climate_param.csv
$onlisting
/ ;

parameter climate_heuristics_finalyear(climate_param) "--fraction-- climate heuristic adjustment in final year"
$onempty
/
$offlisting
$ondelim
$include inputs_case%ds%climate_heuristics_finalyear.csv
$offdelim
$onlisting
/ ;
$offempty

* hydro_capcredit_delta applies to dispatchable hydro.
* We don't apply it through cap_hyd_szn_adj because we only want to change cap credit, not energy dispatch.
parameter hydro_capcredit_delta(i,allt) "--fraction-- fractional adjustment to dispatchable hydro capacity credit from climate heuristics" ;
hydro_capcredit_delta(i,t)$hydro_d(i) =
    climate_heuristics_finalyear('hydro_capcredit_delta') * climate_heuristics_yearfrac(t)
;

*====================================
*         --- RPS data ---
*====================================

set RPSCat "RPS constraint categories, including clean energy standards"
/
$offlisting
$include inputs_case%ds%RPSCat.csv
$onlisting
/ ;

set RPSCat_i(RPSCat,i,st)     "mapping between rps category and technologies for each state",
    RecMap(i,RPSCat,st,ast,t) "Mapping set for technologies to RPS categories and indicates if credits can be sent from st to ast",
    RecStates(RPSCat,st,t)    "states that can generate RECS for their own or other states' requirements",
    RecTrade(RPSCat,st,ast,t) "mapping set between states that can trade RECs with each other (from st to ast)",
    RecTech(RPSCat,i,st,t)    "set to indicate which technologies and classes can contribute to a state's RPSCat",
    r_st_rps(r,st)            "mapping of eligible regions to each state for RPS/CES purposes" ;

Parameter RecPerc(RPSCat,st,t)     "--fraction-- fraction of total generation for each state that must be met by RECs for each category"
          RPSTechMult(RPSCat,i,st) "--fraction-- fraction of generation from each technology that counts towards the requirement for each category"
;

* Create a new r-to-state mapping set that allows voluntary purchases
r_st_rps(r,st) = r_st(r,st) ;
* All regions can create voluntary RECS
r_st_rps(r,"voluntary") = yes ;

$onempty
table techs_banned_rps(i,st) "Techs that are banned for serving RPS in a given state"
$offlisting
$ondelim
$include inputs_case%ds%techs_banned_rps.csv
$offdelim
$onlisting
;
$offempty

$onempty
parameter RecStyle(st,RPSCat) "--integer-- Indication for how to apply state requirement (0 = end-use sales, 1 = bus-bar sales, 2 = generation). Default is 0."
/
$offlisting
$ondelim
$include inputs_case%ds%recstyle.csv
$offdelim
$onlisting
/
;
$offempty

$onempty
table techs_banned_ces(i,st) "Techs that are banned for serving CES in a given state"
$offlisting
$ondelim
$include inputs_case%ds%techs_banned_ces.csv
$offdelim
$onlisting
;
$offempty

$onempty
* declared over allt to allow for external data files that extend beyond end_year
Table rps_fraction(allt,st,RPSCat) "--fraction-- requirement for state RPS"
$offlisting
$ondelim
$include inputs_case%ds%rps_fraction.csv
$offdelim
$onlisting
;
$offempty

$onempty
parameter ces_fraction(allt,st) "--fraction-- requirement for clean energy standard"
/
$offlisting
$ondelim
$include inputs_case%ds%ces_fraction.csv
$offdelim
$onlisting
/
;
$offempty

RecPerc(RPSCat,st,t) = sum{allt$att(allt,t), rps_fraction(allt,st,RPSCat) } ;
RecPerc(RPSCat,st,t)$[(Sw_StateRPS_Carveouts = 0)$(sameas(RPSCat, "RPS_solar") or sameas(RPSCat, "RPS_Wind"))] = 0;
RecPerc("CES",st,t) = ces_fraction(t,st) ;

* RE generation creates both CES and RPS credits, which can cause double-counting
* if a state has an RPS but not a CES. By setting each state's CES as the maximum
* of its RPS or CES, we prevent the double-counting.
RecPerc("CES",st,t) = max(RecPerc("CES",st,t), RecPerc("RPS_all",st,t)) ;

*Some links (value in RECtable = 2) restricted to bundled trading, while
*some (value in RECtable = 1) allowed to also trade unbundled RECs.
*Note the reversed set index order for rectable as compared to RecTrade, RecMap, and RECS.
$onempty
table rectable(st,ast) "Allowed credit trade from ast to st. [1] Unbundled allowed; [2] Only bundled allowed"
$offlisting
$ondelim
$include inputs_case%ds%rectable.csv
$offdelim
$onlisting
;
$offempty

table acp_price(st,allt) "$/REC - alternative compliance payment price for RPS constraint"
$offlisting
$ondelim
$include inputs_case%ds%acp_prices.csv
$offdelim
$onlisting
;

$onempty
parameter acp_disallowed(st,RPSCat) "--integer-- Indication for whether ACP purchases are disallowed (1) or allowed (0)."
/
$offlisting
$ondelim
$include inputs_case%ds%acp_disallowed.csv
$offdelim
$onlisting
/
;
$offempty

RecStates(RPSCat,st,t)$[RecPerc(RPSCat,st,t) or sum{ast, rectable(ast,st) }] = yes ;

*If both states have an RPS for the RPSCat and if they're allowed to trade, they can trade
RecTrade(RPSCat,st,ast,t)$((rectable(ast,st)=1)$RecStates(RPSCat,ast,t)) = yes ;

*If both states have an RPS for the RPSCat and if they're allowed to trade, they can trade
RecTrade("RPS_bundled",st,ast,t)$[(rectable(ast,st)=2)$RecStates("RPS_all",ast,t)] = yes ;
RecTrade("CES_bundled",st,ast,t)$[(rectable(ast,st)=2)$RecStates("CES",ast,t)] = yes ;

*Assign eligible techs for RPS_All
RPSCat_i("RPS_All",i,st)$[re(i)$(not techs_banned_rps(i,st))$valcap_i(i)] = yes ;

*Assign eligible techs for RPS_Wind
RPSCat_i("RPS_Wind",i,st)$[wind(i)$(not techs_banned_rps(i,st))$valcap_i(i)] = yes ;

*Assign eligible techs for RPS_Solar
RPSCat_i("RPS_Solar",i,st)$[(pv(i) or pvb(i))$(not techs_banned_rps(i,st))$valcap_i(i)] = yes ;

*We allow CCS techs and upgrades to be eligible for CES policies
*CCS contribution is limited based on the amount of emissions captured later on down
RPSCat_i("CES",i,st)$[(RPSCAT_i("RPS_All",i,st) or nuclear(i) or hydro(i) or ccs(i) or canada(i))
                     $(not techs_banned_ces(i,st))
                     $valcap_i(i)] = yes ;

RecTech(RPSCat,i,st,t)$(RPSCat_i(RPSCat,i,st)$RecStates(RPSCat,st,t)) = yes ;
RecTech(RPSCat,i,st,t)$(hydro(i)$RecTech(RPSCat,"hydro",st,t)$valcap_i(i)) = yes ;
RecTech("RPS_Bundled",i,st,t)$[RecTech("RPS_All",i,st,t)] = yes ;

RecTech("CES_Bundled",i,st,t)$[RecTech("CES",i,st,t)] = yes ;

*Voluntary market RECs can come from any RE tech
RecTech(RPSCat,i,"voluntary",t)$re(i) = yes ;

*Remove combinations that are not allowed by valgen
RecTech(RPSCat,i,st,t)$[not sum{(v,r)$r_st_rps(r,st), valgen(i,v,r,t) }] = no ;

*Remove CCS techs if explicitly disallowed
RecTech(RPSCat,i,st,t)$[ccs(i)$Sw_CCS_NotRecTech] = no ;

$onempty
table hydrofrac_policy(st,RPSCat) "fraction of hydro RPS or CES credits that can count towards policy targets"
$offlisting
$ondelim
$include inputs_case%ds%hydrofrac_policy.csv
$offdelim
$onlisting
;
$offempty

*initialize values to 1
RPSTechMult(RPSCat,i,st)$[sum{t, RecTech(RPSCat,i,st,t) }] = 1 ;
*reduce multipliers for hydro technologies based on eligibility fractions
RPSTechMult(RPSCat,i,st)$[hydro(i)$valcap_i(i)] = hydrofrac_policy(st,RPSCat) ;
RPSTechMult("RPS_bundled",i,st)$[hydro(i)$valcap_i(i)] = RPSTechMult("RPS_All",i,st) ;
RPSTechMult("CES_bundled",i,st)$[hydro(i)$valcap_i(i)] = RPSTechMult("CES",i,st) ;

*Reduce RPS/CES values for distributed PV based on distloss because we increase their generation to the busbar level
RPSTechMult(RPSCat,i,st)$[(distpv(i))$RPSTechMult(RPSCat,i,st)] = 1 - distloss ;

$onempty
table techs_banned_imports_rps(i,st) "Techs that are not allowed to be imported into a state to meet the RPS"
$offlisting
$ondelim
$include inputs_case%ds%techs_banned_imports_rps.csv
$offdelim
$onlisting
;
$offempty

*CCS technologies have a variety of capture rates, so we assign them below after reading in capture rates

RecMap(i,RPSCat,st,ast,t)$[
*if the receiving state has a requirement for RPSCat
      RecPerc(RPSCat,ast,t)
*if both states can use that technology
      $RecTech(RPSCat,i,st,t)
      $RecTech(RPSCat,i,ast,t)
*if the state can trade
      $RecTrade(RPSCat,st,ast,t)
               ] = yes ;

RecMap(i,"RPS_bundled",st,ast,t)$(
*if the receiving state has a requirement for RPSCat
      RecPerc("RPS_all",ast,t)
*if both states can use that technology
      $RecTech("RPS_bundled",i,st,t)
      $RecTech("RPS_bundled",i,ast,t)
*if the state can trade
      $RecTrade("RPS_bundled",st,ast,t)
               ) = yes ;


RecMap(i,"CES_bundled",st,ast,t)$(
*if the receiving state has a requirement for RPSCat
      RecPerc("CES",ast,t)
*if both states can use that technology
      $RecTech("CES_bundled",i,st,t)
      $RecTech("CES_bundled",i,ast,t)
*if the state can trade
      $RecTrade("CES_bundled",st,ast,t)
               ) = yes ;

*states can "import" their own RECs (except for "voluntary")
RecMap(i,RPSCat,st,ast,t)$[
    sameas(st,ast)
    $RecTech(RPSCat,i,st,t)
    $RecPerc(RPSCat,st,t)
    $(not sameas(st,"voluntary"))
      ] = yes ;

*states that allow hydro to fulfill their RPS requirements can trade hydro recs
RecMap(i,RPSCat,st,ast,t)$[
      hydro(i)
      $RPSTechMult(RPSCat,i,st)
      $RPSTechMult(RPSCat,i,ast)
      $RecMap("hydro",RPSCat,st,ast,t)
      $valcap_i(i)
      ] = yes ;

*Do not allow banned imports
RecMap(i,RPSCat,st,ast,t)$[
      (sameas(RPSCat,"RPS_All") or sameas(RPSCat,"RPS_bundled"))
      $(not sameas(st,ast))
      $techs_banned_imports_rps(i,ast)
      ] = no ;

*Only allow voluntary market to use renewable energy when consuming CES credits
RecMap(i,RPSCat,st,"voluntary",t)$[
      (not re(i))
      $(sameas(RPSCat,"CES") or sameas(RPSCat,"CES_bundled"))
      ] = no ;

*Do not allow voluntary market to use canadian imports
RecMap(i,RPSCat,st,"voluntary",t)$[
      (canada(i))
      ] = no ;

if(Sw_WaterMain=1,
  RecMap(i,RPSCat,st,ast,t)$[i_water_cooling(i)$(not RecMap(i,RPSCat,st,ast,t))]
     = sum{ii$ctt_i_ii(i,ii), RecMap(ii,RPSCat,st,ast,t) } ;
) ;

$onempty
parameter RPS_oosfrac(st) "fraction of RECs from out of state that can meet the RPS"
/
$offlisting
$ondelim
$include inputs_case%ds%oosfrac.csv
$offdelim
$onlisting
/ ;
$offempty

$onempty
table RPS_unbundled_limit_in(st,allt) "--fraction-- upper bound of state RPS that can be met with unbundled RECS"
$offlisting
$ondelim
$include inputs_case%ds%unbundled_limit_rps.csv
$offdelim
$onlisting
;
$offempty

$onempty
table CES_unbundled_limit_in(st,allt) "--fraction-- upper bound of state CES that can be met with unbundled RECS"
$offlisting
$ondelim
$include inputs_case%ds%unbundled_limit_ces.csv
$offdelim
$onlisting
;
$offempty

parameter REC_unbundled_limit(RPScat,st,allt) '--fraction-- portion for RPS/CES constraint that can be met with unbundled RECS' ;
set st_unbundled_limit(RPScat,st) "states that have a unbundled limit on RECs" ;

REC_unbundled_limit("RPS_All",st,t) = RPS_unbundled_limit_in(st,t) ;
REC_unbundled_limit("CES",st,t) = CES_unbundled_limit_in(st,t) ;

st_unbundled_limit(RPSCat,st)$sum{t, REC_unbundled_limit(RPSCat,st,t) } = yes ;

parameter national_gen_frac(allt) "--%-- national fraction of load + losses that must be met by RE"
/
$offlisting
$ondelim
$include inputs_case%ds%gen_mandate_trajectory.csv
$offdelim
$onlisting
/ ;

parameter nat_gen_tech_frac(i) "--fraction-- fraction of each tech generation that may be counted toward eq_national_gen"
/
$offlisting
$ondelim
$include inputs_case%ds%gen_mandate_tech_list.csv
$offdelim
$onlisting
/ ;
nat_gen_tech_frac(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), nat_gen_tech_frac(ii) } ;

*====================
* --- CSAPR Data ---
*====================

* a CSAPR budget indicates the cap for trading whereas
* assurance indicates the maximum amount a state can emit regardless of trading
set csapr_cat "CSAPR regulation categories"
/
$offlisting
$include inputs_case%ds%csapr_cat.csv
$onlisting
/ ;

*trading rules dictate there are two groups of states that can trade with each other
set csapr_group "CSAPR trading group"
/
$offlisting
$include inputs_case%ds%csapr_group.csv
$onlisting
/ ;

$onempty
table csapr_cap(st,csapr_cat,allt) "--metric tons-- maximum amount of NOX emissions during the ozone season (May-September)"
$offlisting
$ondelim
$include inputs_case%ds%csapr_ozone_season.csv
$offdelim
$onlisting
;
$offempty

$onempty
set csapr_group1_ex(st) "CSAPR states that cannot trade with those in group 2"
/
$offlisting
$include inputs_case%ds%csapr_group1_ex.csv
$onlisting
/
;
$offempty

$onempty
set csapr_group2_ex(st) "CSAPR states that cannot trade with those in group 1"
/
$offlisting
$include inputs_case%ds%csapr_group2_ex.csv
$onlisting
/
;
$offempty

set csapr_group_st(csapr_group,st) "final crosswalk set for use in modeling CSAPR trade relationships" ;

csapr_group_st("cg1",st)$[sum{t,csapr_cap(st,"budget",t) }$(not csapr_group1_ex(st))$stfeas(st)] = yes ;
csapr_group_st("cg2",st)$[sum{t,csapr_cap(st,"budget",t) }$(not csapr_group2_ex(st))$stfeas(st)] = yes ;

*assumption here is that the ozone season covers only 1/3 of the months
*in the spring and fall but the entire season in summer,
*therefore weighting each seasons emissions accordingly
parameter quarter_weight_csapr(quarter) "quarter weights for CSAPR ozone season constraints"
            / spri 0.333, summ 1, fall 0.333 /;



*==============================
* --- Transmission Inputs ---
*==============================

* --- transmission sets ---
set trtype "transmission capacity type"
/
$offlisting
$include inputs_case%ds%trtype.csv
$onlisting
/ ;

set aclike(trtype) "AC transmission capacity types"
/
$offlisting
$ondelim
$include inputs_case%ds%aclike.csv
$offdelim
$onlisting
/ ;

set notvsc(trtype) "transmission capacity types that are not VSC"
/
$offlisting
$ondelim
$include inputs_case%ds%notvsc.csv
$offdelim
$onlisting
/ ;

set lcclike(trtype) "transmission capacity types where lines are bundled with AC/DC converters"
/
$offlisting
$ondelim
$include inputs_case%ds%lcclike.csv
$offdelim
$onlisting
/ ;

set trancap_fut_cat "categories of near-term transmission projects that describe the likelihood of being completed"
/
$offlisting
$include inputs_case%ds%trancap_fut_cat.csv
$onlisting
/ ;

set routes(r,rr,trtype,t)     "final conditional on transmission feasibility"
    routes_inv(r,rr,trtype,t) "routes where new transmission investment is allowed"
    routes_prm(r,rr)          "routes where PRM trading is allowed"
    opres_routes(r,rr,t)      "final conditional on operating reserve flow feasibility"
;

alias(trtype,intype,outtype) ;

* Specify the transmission types that are limited by Sw_TransCapMax and Sw_TransCapMaxTotal
set trtypemax(trtype) "trtypes to limit" ;
trtypemax(trtype)$[(Sw_TransCapMaxTypes=0)] = no ;
trtypemax(trtype)$[(Sw_TransCapMaxTypes=1)] = yes ;
trtypemax(trtype)$[(Sw_TransCapMaxTypes=2)$sameas(trtype,'VSC')] = yes ;
trtypemax(trtype)$[(Sw_TransCapMaxTypes=3)$(not sameas(trtype,'AC'))] = yes ;

* --- initial transmission capacity ---
* transmission capacity input data are defined in both directions for each region-to-region pair
* Written by transmission.py
$onempty
parameter trancap_init_energy(r,rr,trtype) "--MW-- initial transmission capacity for energy trading"
/
$offlisting
$ondelim
$include inputs_case%ds%trancap_init_energy.csv
$offdelim
$onlisting
/ ;

parameter trancap_init_prm(r,rr,trtype) "--MW-- initial transmission capacity for capacity (PRM) trading"
/
$offlisting
$ondelim
$include inputs_case%ds%trancap_init_prm.csv
$offdelim
$onlisting
/ ;
$offempty

* --- future transmission capacity ---
* Transmission additions are defined in one direction for each region-to-region pair with the lowest region number listed first
* Written by transmission.py
$onempty
parameter trancap_fut(r,rr,trancap_fut_cat,trtype,allt) "--MW-- potential future transmission capacity by type (one direction)"
/
$offlisting
$ondelim
$include inputs_case%ds%trancap_fut.csv
$offdelim
$onlisting
/ ;
$offempty

* --- exogenously specified transmission capacity ---
* Transmission additions are defined in one direction for each region-to-region pair with the lowest region number listed first
parameter invtran_exog(r,rr,trtype,t) "--MW-- exogenous transmission capacity investment (one direction)" ;
* "certain" future transmission project capacity in the current year t
invtran_exog(r,rr,trtype,t)$trancap_fut(r,rr,"certain",trtype,t) = trancap_fut(r,rr,"certain",trtype,t) ;

* --- valid transmission routes ---

*transmission routes are enabled if:
* (1) there is transmission capacity between the two regions
routes(r,rr,trtype,t)$[
    trancap_init_energy(r,rr,trtype) or trancap_init_energy(rr,r,trtype)
    or trancap_init_prm(r,rr,trtype) or trancap_init_prm(rr,r,trtype)
    or invtran_exog(r,rr,trtype,t) or invtran_exog(rr,r,trtype,t)
] = yes ;
* (2) there is future capacity available between the two regions
routes(r,rr,trtype,t)$[sum{(tt,trancap_fut_cat)$(yeart(tt)<=yeart(t)),
                           trancap_fut(r,rr,trancap_fut_cat,trtype,tt) }] = yes ;
* (3) there exists a route (r,rr) that is in the opposite direction as (rr,r)
routes(rr,r,trtype,t)$(routes(r,rr,trtype,t)) = yes ;
* (4) the year is modeled
routes(r,rr,trtype,t)$(not tmodel_new(t)) = no ;

* disable AC routes that cross interconnect boundaries (only happens if aggregating regions across interconnects)
routes(r,rr,trtype,t)
    $[routes(r,rr,trtype,t)
    $aclike(trtype)
    $[(not sum{interconnect$[r_interconnect(r,interconnect)$r_interconnect(rr,interconnect)], 1 })]
    ] = no ;

* Disable links between offshore zones if specified
routes(r,rr,trtype,t)$[(not Sw_OffshoreBackbone)$offshore(r)$offshore(rr)] = no ;

* If any routes use VSC, activate the VSC constraints and variables
scalar Sw_VSC "Activate VSC constraints and variables" ;
Sw_VSC = sum{routes(r,rr,trtype,t)$sameas(trtype,'VSC'), 1} ;

* initialize all investment routes to no
routes_inv(r,rr,trtype,t) = no ;
* allow new investment along existing routes
routes_inv(r,rr,trtype,t)$[notvsc(trtype)$routes(r,rr,trtype,t)] = yes ;
* Do not allow transmission expansion on most interfaces until firstyear_trans_nearterm
routes_inv(r,rr,trtype,t)$[yeart(t)<firstyear_trans_nearterm] = no ;
* If not allowing near-term transmission, turn those off until firstyear_trans_longterm
routes_inv(r,rr,trtype,t)$[(not Sw_TransInvNearTerm)$(yeart(t)<firstyear_trans_longterm)] = no ;
* Do allow "possible" interfaces to be expanded
routes_inv(r,rr,trtype,t)
    $[sum{tt$[(yeart(tt)<=yeart(t))],
          trancap_fut(r,rr,"possible",trtype,tt) + trancap_fut(rr,r,"possible",trtype,tt) }
    $routes(r,rr,trtype,t)] = yes ;
routes_inv(rr,r,trtype,t)$[not routes_inv(r,rr,trtype,t)] = no ;

* Restrict transmission builds to the level indicated by GSw_TransRestrict
$ifthen.transrestrict %GSw_TransRestrict% == 'r'
    routes_inv(r,rr,trtype,t) = no ;
$else.transrestrict
    routes_inv(r,rr,trtype,t)
        $[(not sum{%GSw_TransRestrict%
                   $[r_%GSw_TransRestrict%(r,%GSw_TransRestrict%)
                   $r_%GSw_TransRestrict%(rr,%GSw_TransRestrict%)], 1 })
        $routes(r,rr,trtype,t)]
    = no ;
$endif.transrestrict

* Restrict PRM trading to the level indicated by Sw_PRMTRADE_level
routes_prm(r,rr)$sum{(trtype,t), routes(r,rr,trtype,t) } = yes ;
$ifthen.prmtradelevel %GSw_PRMTRADE_level% == 'r'
    routes_prm(r,rr) = no ;
$else.prmtradelevel
    routes_prm(r,rr)
        $[(not sum{%GSw_PRMTRADE_level%
                   $[r_%GSw_PRMTRADE_level%(r,%GSw_PRMTRADE_level%)
                   $r_%GSw_PRMTRADE_level%(rr,%GSw_PRMTRADE_level%)], 1 })
        $routes_prm(r,rr)]
    = no ;
$endif.prmtradelevel

* Create list of expandable AC interfaces (r < rr) for error-checking
set interfaces_inv(r,rr) "expandable AC transmission interfaces, which are defined only for r < rr" ;
interfaces_inv(r,rr)$[sum{t, routes_inv(r,rr,"AC",t)}$(ord(r) < ord(rr))] = yes ;

* operating reserve flows only allowed over AC lines
opres_routes(r,rr,t)$sum{trtype$aclike(trtype), routes(r,rr,trtype,t) } = yes ;

* Restrict operating reserve flows to the level indicated by Sw_OpResTradeLevel
$ifthen.oprestradelevel %GSw_OpResTradeLevel% == 'r'
    opres_routes(r,rr,t) = no ;
$else.oprestradelevel
    opres_routes(r,rr,t)
        $[(not sum{%GSw_OpResTradeLevel%
                   $[r_%GSw_OpResTradeLevel%(r,%GSw_OpResTradeLevel%)
                   $r_%GSw_OpResTradeLevel%(rr,%GSw_OpResTradeLevel%)], 1 })
        $opres_routes(r,rr,t)]
    = no ;
$endif.oprestradelevel

* Multiplier on opres flow. This multiplier increases the amount of transmission required
* to trade operating reserves (e.g. a value of 1.1 means that 1.1 MW of free transmission is needed
* to transfer 1 MW of operating reserves). Multiplier serves as a means of ensuring there is
* "extra" transmission available to reduce the potential for line overloading in the case of
* an outage/contingency in which spinning reserves would be deployed.
Scalar opres_mult "multiplier on opres flow in transmission constraint" ;
opres_mult = Sw_OpResTradeMult;

* Interfaces are collections of routes with an additional constraint on total flows
$onempty
parameter trancap_init_transgroup(transgrp,transgrpp,trtype) "--MW-- initial upper limit on interface AC flows"
/
$offlisting
$ondelim
$include inputs_case%ds%trancap_init_transgroup.csv
$offdelim
$onlisting
/ ;
$offempty

$onempty
parameter trancap_init_itlgrp(itlgrp,itlgrpp,trtype) "--MW-- initial upper limit on interface flows between itlgrps"
/
$offlisting
$ondelim
$include inputs_case%ds%trancap_init_itlgrp.csv
$offdelim
$onlisting
/ ;
$offempty

parameter routes_transgroup(transgrp,transgrpp,r,rr) "collection of routes between transgroups" ;
routes_transgroup(transgrp,transgrpp,r,rr)$[
    sum{t, routes(r,rr,"AC",t) }
    $r_transgrp(r,transgrp)
    $r_transgrp(rr,transgrpp)
    $(not sameas(transgrp,transgrpp))
    $(not sameas(r,rr))
] = yes ;

set routes_nercr(nercr,nercrr,r,rr) "collection of routes between nercrs" ;
routes_nercr(nercr,nercrr,r,rr)$[
    sum{(t,trtype), routes(r,rr,trtype,t) }
    $r_nercr(r,nercr)
    $r_nercr(rr,nercrr)
    $(not sameas(nercr,nercrr))
    $(not sameas(r,rr))
] = yes ;

parameter routes_itlgrp(itlgrp,itlgrpp,r,rr) "collection of routes between itlgrps" ;
routes_itlgrp(itlgrp,itlgrpp,r,rr)$[
    sum{(t,trtype), routes(r,rr,trtype,t) }
    $r_itlgrp(r,itlgrp)
    $r_itlgrp(rr,itlgrpp)
    $(not sameas(itlgrp,itlgrpp))
    $(not sameas(r,rr))
    $[not((sameas(itlgrp,r)) AND (sameas(itlgrpp,rr)))]
] = yes ;
* --- transmission cost ---

* Transmission line capex cost (generated from reV tables)
* Written by transmission.py
$onempty
parameter tsc_binwidth(r,rr,tscbin) "--$-- investment bin widths for transmission interfaces"
/
$offlisting
$ondelim
$include inputs_case%ds%tsc_binwidth.csv
$offdelim
$onlisting
/ ;

parameter tsc_forward(r,rr,tscbin) "--$/MW-- transmission upgrade cost for forward direction"
/
$offlisting
$ondelim
$include inputs_case%ds%tsc_forward.csv
$offdelim
$onlisting
/ ;

parameter tsc_reverse(r,rr,tscbin) "--$/MW-- transmission upgrade cost for reverse direction"
/
$offlisting
$ondelim
$include inputs_case%ds%tsc_reverse.csv
$offdelim
$onlisting
/ ;

parameter transmission_cost_nonac(r,rr,trtype) "--$/MW-- expansion cost for DC interfaces (only lines; converters handled separately)"
/
$offlisting
$ondelim
$include inputs_case%ds%transmission_cost_nonac.csv
$offdelim
$onlisting
/ ;

* Scale transmission line costs by Sw_TransCostMult (for sensitivity analysis)
tsc_binwidth(r,rr,tscbin) = tsc_binwidth(r,rr,tscbin) * Sw_TransCostMult ;
tsc_forward(r,rr,tscbin) = tsc_forward(r,rr,tscbin) * Sw_TransCostMult ;
tsc_reverse(r,rr,tscbin) = tsc_reverse(r,rr,tscbin) * Sw_TransCostMult ;
transmission_cost_nonac(r,rr,trtype) = transmission_cost_nonac(r,rr,trtype) * Sw_TransCostMult ;

* Transmission line FOM cost
* Written by transmission.py
parameter transmission_line_fom(r,rr,trtype) "--$/MW/year-- fixed O&M cost of transmission lines"
/
$offlisting
$ondelim
$include inputs_case%ds%transmission_line_fom.csv
$offdelim
$onlisting
/ ;
$offempty

parameter cost_hurdle(r,rr,allt) "--$ per MWh-- cost for transmission hurdle rate" ;
parameter cost_hurdle_regiongrp1(r,rr,allt) "--$ per MWh-- cost for transmission hurdle rate between regiongrp1" ;
parameter cost_hurdle_regiongrp2(r,rr,allt) "--$ per MWh-- cost for transmission hurdle rate between regiongrp2" ;

$onempty
parameter cost_hurdle_country(country) "--$ per MWh-- cost for transmission hurdle rate by country"
/
$offlisting
$ondelim
$include inputs_case%ds%cost_hurdle_country.csv
$offdelim
$onlisting
/ ;
$offempty

* Assign hurdle rates to chosen GSw_TransHurdLevel
$onempty
parameter cost_hurdle_rate1(allt) "--$ per MWh-- raw data cost for transmission hurdle rate for regiongrp1"
/
$offlisting
$ondelim
$include inputs_case%ds%cost_hurdle_rate1.csv
$offdelim
$onlisting
/ ;
$offempty

$onempty
parameter cost_hurdle_rate2(allt) "--$ per MWh-- raw data cost for transmission hurdle rate for regiongrp2"
/
$offlisting
$ondelim
$include inputs_case%ds%cost_hurdle_rate2.csv
$offdelim
$onlisting
/ ;
$offempty

* define hurdle rates across international lines
* first determine whether the regions are of different countries..
cost_hurdle_regiongrp1(r,rr,t)$[sum{country$r_country(r,country),ord(country) }
                   <> sum{country$r_country(rr,country),ord(country) }]
* then add the cost_hurdle by country (not defined for USA)
* for both the r and rr regions
    = sum{country$r_country(r,country),cost_hurdle_country(country) } +
      sum{country$r_country(rr,country),cost_hurdle_country(country) }  ;

cost_hurdle_regiongrp2(r,rr,t)$[sum{country$r_country(r,country),ord(country) }
                   <> sum{country$r_country(rr,country),ord(country) }]
    = sum{country$r_country(r,country),cost_hurdle_country(country) } +
      sum{country$r_country(rr,country),cost_hurdle_country(country) }  ;      


* define hurdle rates for intra-country lines
cost_hurdle_regiongrp1(r,rr,t)
    $[sum{country$[r_country(r,country)$r_country(rr,country)], 1 }
    $sum{trtype, routes(r,rr,trtype,t) }] = cost_hurdle_rate1(t) ;

cost_hurdle_regiongrp2(r,rr,t)
    $[sum{country$[r_country(r,country)$r_country(rr,country)], 1 }
    $sum{trtype, routes(r,rr,trtype,t) }] = cost_hurdle_rate2(t) ;    

* set hurdle rates for regions within the same GSw_TransHurdleLevel region to zero
$ifthen.hurdlelevel_regiongrp1 %GSw_TransHurdleLevel1% == 'r'
    ;
$else.hurdlelevel_regiongrp1
    cost_hurdle_regiongrp1(r,rr,t)
        $[sum{%GSw_TransHurdleLevel1%
              $[r_%GSw_TransHurdleLevel1%(r,%GSw_TransHurdleLevel1%)
              $r_%GSw_TransHurdleLevel1%(rr,%GSw_TransHurdleLevel1%)], 1 }
        $sum{trtype, routes(r,rr,trtype,t) }]
    = 0 ;
$endif.hurdlelevel_regiongrp1

$ifthen.hurdlelevel_regiongrp2 %GSw_TransHurdleLevel2% == 'r'
    ;
$else.hurdlelevel_regiongrp2
    cost_hurdle_regiongrp2(r,rr,t)
        $[sum{%GSw_TransHurdleLevel2%
              $[r_%GSw_TransHurdleLevel2%(r,%GSw_TransHurdleLevel2%)
              $r_%GSw_TransHurdleLevel2%(rr,%GSw_TransHurdleLevel2%)], 1 }
        $sum{trtype, routes(r,rr,trtype,t) }]
    = 0 ;
$endif.hurdlelevel_regiongrp2

* The final hurdle cost is the higher cost among regiongrp1 and regiongrp2, and hurdle_rate_floor
cost_hurdle(r,rr,t)$[sum{trtype, routes(r,rr,trtype,t) }] = max{cost_hurdle_regiongrp1(r,rr,t),cost_hurdle_regiongrp2(r,rr,t), hurdle_rate_floor} ;

* --- transmission distance ---

* The distance for a transmission interface is calculated in reV using the same "least-cost-path"
* algorithm and cost tables as for wind and solar spur lines.
* Distances are more representative of new greenfield lines than existing lines.
* Written by transmission.py
$onempty
parameter distance(r,rr,trtype) "--miles-- distance between BAs by line type"
/
$offlisting
$ondelim
$include inputs_case%ds%transmission_miles.csv
$offdelim
$onlisting
/ ;


* --- transmission losses ---
* Written by transmission.py
parameter tranloss(r,rr,trtype)    "--fraction-- transmission loss between r and rr"
/
$offlisting
$ondelim
$include inputs_case%ds%tranloss.csv
$offdelim
$onlisting
/ ;
$offempty


* --- VSC HVDC macrogrid ---
set val_converter(r,t) "BAs where VSC converter investment is allowed" ;
val_converter(r,t) = no ;

* VSC converters are allowed in BAs on either side of a valid VSC interface
val_converter(r,t)$[sum{rr, routes_inv(r,rr,"VSC",t) }] = yes ;
val_converter(r,t)$[sum{rr, routes_inv(rr,r,"VSC",t) }] = yes ;

* Use LCC DC per-MW costs for VSC (converters are handled separately)
transmission_line_fom(r,rr,"VSC")$sum{t, routes(r,rr,"VSC",t) } = transmission_line_fom(r,rr,"LCC") ;


* --- Transmission switches ---
* Sw_TransInvMax: According to
*    https://www.energy.gov/eere/wind/articles/land-based-wind-market-report-2021-edition-released
*    the maximum annual growth rate since 2009 was in 2013, with 543 miles of ≤230 kV,
*    3632 miles of 345 kV, and 466 miles of 500 kV. Using the WECC/TEPPC assumption of
*    1500 MW for 500 kV, 750 MW for 345 kV, and 400 MW for 230 kV (all single-circuit)
*    [https://www.wecc.org/Administrative/TEPPC_TransCapCostCalculator_E3_2019_Update.xlsx]
*    gives a maximum of 3.64 TWmile/year and an average of 1.36 TWmile/year.

parameter trans_inv_max(allt) "--TWmile/year-- annual limit on transmission investments" ;
trans_inv_max(t)$[
    tmodel_new(t)
    $(yeart(t) >= firstyear_trans_nearterm)
    $(yeart(t) < firstyear_trans_longterm)
] = Sw_TransInvMaxNearterm ;

trans_inv_max(t)$[
    tmodel_new(t)
    $(yeart(t) >= firstyear_trans_longterm)
] = Sw_TransInvMaxLongterm ;

*============================
*   --- Fuel Prices ---
*============================
*Note - NG supply curve has its own section

set f "fuel types"
/
$offlisting
$include inputs_case%ds%f.csv
$onlisting
/ ;

set fuel2tech(f,i) "mapping between fuel types and generations"
/
$offlisting
$ondelim
$include inputs_case%ds%fuel2tech.csv
$offdelim
$onlisting
/ ;

*double check in case any sets have been changed.
fuel2tech("coal",i)$coal(i) = yes ;
fuel2tech("naturalgas",i)$gas(i) = yes ;
fuel2tech("uranium",i)$nuclear(i) = yes ;
fuel2tech(f,i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), fuel2tech(f,ii) } ;
fuel2tech(f,i)$upgrade(i) = sum{ii$upgrade_to(i,ii), fuel2tech(f,ii) } ;

*===============================
*   Generator Characteristics
*===============================

set plantcat "categories for plant characteristics"
/
$offlisting
$include inputs_case%ds%plantcat.csv
$onlisting
/ ;

* declared over allt to allow for external data files that extend beyond end_year
parameter plant_char0(i,allt,plantcat) "--units vary-- input plant characteristics"
/
$offlisting
$ondelim
$include inputs_case%ds%plantcharout.csv
$offdelim
$onlisting
/ ;

parameter
  winter_cap_ratio(i,v,r) "--scalar-- ratio of winter capacity to summer capacity"
  winter_cap_frac_delta(i,v,r) "--scalar-- fractional change in winter compared to summer capacity"
  quarter_cap_frac_delta(i,v,r,quarter,allt) "--scalar-- fractional change in quarterly capacity compared to summer"
  ccseason_cap_frac_delta(i,v,r,ccseason,allt) "--scalar-- fractional change in ccseason capacity compared to summer"
;

parameter derate_geo_vintage(i,v) "--fraction-- fraction of capacity available for gen; only geo is <1" ;
derate_geo_vintage(i,v)$valcap_iv(i,v) = 1 ;

* Initialize values to one so that we do not accidentally zero out capacity
winter_cap_ratio(i,v,r)$valcap_ivr(i,v,r) = 1 ;
* Existing capacity is assigned the winter capacity ratio based on the value from the existing unit database
* Only hintage_data techs (which have a heat rate) are used here.  Hydro, CSP, and other techs that might have
* different winter capacities are not treated here.
* Don't filter by valcap because you need the full dataset for calculating new vintages
winter_cap_ratio(i,initv,r)$hintage_data(i,initv,r,'%startyear%','cap')
                            =  hintage_data(i,initv,r,'%startyear%','wintercap') / hintage_data(i,initv,r,'%startyear%','cap') ;
* New capacity is given the capacity-weighted average value from existing units
winter_cap_ratio(i,newv,r)$[valcap_ivr(i,newv,r)
                           $sum{(initv,rr), hintage_data(i,initv,rr,'%startyear%','wintercap') }]
                           =  sum{(initv,rr), winter_cap_ratio(i,initv,rr) * hintage_data(i,initv,rr,'%startyear%','wintercap') }
                              / sum{(initv,rr), hintage_data(i,initv,rr,'%startyear%','wintercap') } ;

* Assign H2-CT and H2-CC techs to have the same winter_cap_ratio as their corresponding gas techs
winter_cap_ratio(i,newv,r)$h2_ct(i) = winter_cap_ratio('gas-ct',newv,r) ;
winter_cap_ratio(i,newv,r)$h2_cc(i) = winter_cap_ratio('gas-cc',newv,r) ;

* Assign additional nuclear techs to have the same winter_cap_ratio as 'nuclear'
winter_cap_ratio(i,newv,r)$nuclear(i) = winter_cap_ratio('nuclear',newv,r) ;

* Upgraded plant have the same winter_cap_ratio as what they are upgraded from
winter_cap_ratio(i,newv,r)$upgrade(i) = sum{ii$upgrade_from(i,ii), winter_cap_ratio(ii,newv,r) } ;

* Remove entries where valcap is false
winter_cap_ratio(i,v,r)$[not valcap_ivr(i,v,r)] = 0 ;

* Calculate fractional change in winter capacity relative to summer capacity to avoid
* having lots of 1 values
winter_cap_frac_delta(i,v,r)$winter_cap_ratio(i,v,r) = round((winter_cap_ratio(i,v,r) - 1), 3) ;
* Seasonal capacity fraction delta is zero except in winter
quarter_cap_frac_delta(i,v,r,quarter,t)$[winter_cap_frac_delta(i,v,r)$sameas(quarter,'wint')] = winter_cap_frac_delta(i,v,r) ;
ccseason_cap_frac_delta(i,v,r,ccseason,t)$[winter_cap_frac_delta(i,v,r)$sameas(ccseason,'cold')] = winter_cap_frac_delta(i,v,r) ;

* Apply thermal_summer_cap_delta through seas_cap_frac_delta
quarter_cap_frac_delta(i,v,r,quarter,t)$[conv(i)$sameas(quarter,'summ')] =
    climate_heuristics_finalyear('thermal_summer_cap_delta') * climate_heuristics_yearfrac(t)
;
ccseason_cap_frac_delta(i,v,r,ccseason,t)$[conv(i)$sameas(ccseason,'hot')] =
    climate_heuristics_finalyear('thermal_summer_cap_delta') * climate_heuristics_yearfrac(t)
;



*============================================
* -- Consume technologies specification --
*============================================

$onempty
set routes_adjacent(r,rr) "all pairs of adjacent land-based BAs"
/
$offlisting
$ondelim
$include inputs_case%ds%routes_adjacent.csv
$offdelim
$onlisting
/ ;
$offempty
* Remove offshore zones
routes_adjacent(r,rr)$(offshore(r) or offshore(rr)) = no ;

set h2_routes(r,rr)       "set of feasible pipeline corridors for hydrogen"
    h2_routes_inv(r,rr)   "set of feasible investment pipeline corridors for hydrogen"
;
* First allow H2 pipelines between any two adjacent zones
h2_routes(r,rr)$[routes_adjacent(r,rr)$Sw_H2_Transport] = yes ;
* Restrict pipelines to the level indicated by GSw_H2_TransportLevel
$ifthen.h2transportlevel %GSw_H2_TransportLevel% == 'r'
    h2_routes(r,rr) = no ;
$else.h2transportlevel
    h2_routes(r,rr)
        $[(not sum{%GSw_H2_TransportLevel%
                   $[r_%GSw_H2_TransportLevel%(r,%GSw_H2_TransportLevel%)
                   $r_%GSw_H2_TransportLevel%(rr,%GSw_H2_TransportLevel%)], 1 })]
    = no ;
$endif.h2transportlevel

* Populate H2 pipeline investment routes
h2_routes_inv(r,rr) = h2_routes(r,rr) ;
* Only keep routes with r < rr for investment
h2_routes_inv(r,rr)$(ord(rr)<ord(r)) = no ;

parameter cost_prod(i,v,r,t)                  "--$/metric ton/hr-- cost or benefit of producing output from consuming technologies"
          dac_conversion_rate(i,t)            "--metric tons/MWh-- CO2 captured per MWh of electricity consumed"
          h2_conversion_rate(i,v,r,t)         "--metric tons/MWh-- H2 produced per MWh of electricity consumed"
          prod_conversion_rate(i,v,r,t)       "--metric tons/MWh-- amount of product produced (H2 or CO2) per MWh of electricity consumed"
;

scalar    h2_combustion_intensity              "--metric tons/MMBtu-- amount of hydrogen consumed per MMBtu of H2-Combustion fuel consumption" ;

parameter pipeline_distance(r,rr) "--miles-- distance between all adjacent BA centroids for pipeline investments" ;
pipeline_distance(r,rr) = distance(r,rr,"AC") ;

* For smr consume_char0 has capital costs in $/(kg/day) and "ele_efficiency" of kWh/kg
* convert to $/MW by [$/(kg/day)] / [kwh/kg] * [1000 kWh/MWh] * [24 hr/day]
* multiply by availability because the annual amount produced is a function of availability
* we multiply here instead of divide (as in the calculation of m_capacity_exog("smr","init-1",r,t)) since MW is in the denominator
* since we assume smrs only have forced_ourages (and no scheduled outages),
* this is equivalent to using avail(h), but we do it here in b_inputs before defining
* avail(h) to define these costs before we define h-dependent parameters 
* the same conversion applies to FOM
plant_char0(i,t,"capcost")$smr(i) = deflator("2018") * consume_char0(i,t,"cost_cap") / 
  consume_char0(i,t,"ele_efficiency") * (1000 * 24) * (1 - forced_outage_rate_h2_smr ) ;
plant_char0(i,t,"fom")$smr(i) = deflator("2018") * consume_char0(i,t,"fom") / 
  consume_char0(i,t,"ele_efficiency") * (1000 * 24) * (1 - forced_outage_rate_h2_smr ) ;

*electrolyzers capcost just need to go from $/kW to $/MW
plant_char0("electrolyzer",t,"capcost") = deflator("2022") * consume_char0("electrolyzer",t,"cost_cap") * 1000 ;
plant_char0("electrolyzer",t,"fom") = deflator("2022") * consume_char0("electrolyzer",t,"fom") * 1000 ;

set consumecat "categories for consuming facility characteristics"
/
$offlisting
$include inputs_case%ds%consumecat.csv
$onlisting
/ ;

* capcost        - $/(metric ton CO2/hr)
* fom            - $/(metric ton CO2/hr)/yr
* vom            - $/metric ton CO2
* conversionrate - tons CO2/MWh

parameter consume_char_dac(i,allt,consumecat) "--units vary-- input consuming facility characteristics"
/
$offlisting
$ondelim
$include inputs_case%ds%consumechardac.csv
$offdelim
$onlisting
/ ;

consume_char0("dac",t,"cost_cap") = consume_char_dac("dac",t,"capcost") ;
consume_char0("dac",t,"vom") = consume_char_dac("dac",t,"vom") ;
consume_char0("dac",t,"fom") = consume_char_dac("dac",t,"fom") ;

* conversionrate is already in tons/MWh in the BVRE input csv:
dac_conversion_rate(i,t)$[dac(i)$(not sameas(i,"dac_gas"))] = consume_char_dac("dac",t,"conversionrate") ;

* DAC capital cost goes from $ / metric ton / hr to $ / MW
* convert by ($ / metric ton / hr) * ( metric tons / MWh)
plant_char0("dac",t,"capcost") = consume_char0("dac",t,"cost_cap") * dac_conversion_rate("dac",t) ;
plant_char0("dac",t,"fom") = consume_char0("dac",t,"fom") * dac_conversion_rate("dac",t) ;

* Likewise, DAC VOM goes from $ / metric ton to $ / MWh
* convert by ($ / metric ton) * ( metric tons / MWh)
plant_char0("dac",t,"vom") = consume_char0("dac",t,"vom") * dac_conversion_rate("dac",t) ;

* Enable an FOM for DAC:
plant_char0("dac",t,"fom") = consume_char0("dac",t,"fom") ;

table dac_gas_char(i,allt,consumecat)
$ondelim
$offdigit
$include inputs_case%ds%dac_gas.csv
$ondigit
$offdelim
;

* fill in historical years that don't have data
* only for completeness given that we don't
* allow dac_gas builds until 2025
dac_gas_char(i,t,consumecat)$[yeart(t)<2020] = dac_gas_char(i,"2020",consumecat) ;

* capcost, VOM and FOM remain in the same units as consume_char_dac (as described above)
plant_char0("dac_gas",t,"capcost") = dac_gas_char("dac_gas",t,"capcost") ;
plant_char0("dac_gas",t,"vom") = dac_gas_char("dac_gas",t,"vom") ;
plant_char0("dac_gas",t,"fom") = dac_gas_char("dac_gas",t,"fom") ;

parameter dac_gas_cons_rate(i,v,t) "--mmBTU/metric ton CO2-- natural gas consumption by dac_gas technology";
* convert from conversionrate units (metric tons CO2/MWh) to (mmBTU/metric ton CO2):
dac_gas_cons_rate(i,newv,t)$[sameas(i,"dac_gas")$tmodel_new(t)$countnc(i,newv)] = sum{tt$ivt(i,newv,tt), 1 / dac_gas_char(i,tt,"conversionrate") / 0.293071 } / countnc(i,newv) ;

*plant_char cannot be conditioned with valcap or valgen here since the plant_char for unmodeled years is being
*used in calculations of heat_rate, cost_vom, and cost_fom and thus cannot be zeroed out
*plant_char is indexed with v since cooling cost/technology performance multipliers only apply to new builds
parameter plant_char(i,v,t,plantcat) "--various units-- plant characteristics such as cap, vom, fom costs and heat rates";
plant_char(i,v,t,plantcat) = plant_char0(i,t,plantcat) ;

* -- Consuming Technologies costs and demands --

set i_p(i,p) "mapping from technologies to the products they produce"
/
$offlisting
$ondelim
$include inputs_case%ds%i_p.csv
$offdelim
$onlisting
/ ;

* see note from earlier... converting from MT / MWh from kg / kWh does not require adjustment..
* but we still need to convert from MWh / MT to MT / MWh <- could choose either units
* just need to make sure we change signs throughout
h2_conversion_rate(i,newv,r,t)$[h2(i)$valcap(i,newv,r,t)] =
    1 / (sum{tt$ivt(i,newv,tt),consume_char0(i,tt,"ele_efficiency") } / countnc(i,newv) ) ;

h2_conversion_rate(i,initv,r,t)$[h2(i)$valcap(i,initv,r,t)] =
    1 / consume_char0(i,"%startyear%","ele_efficiency") ;

prod_conversion_rate(i,v,r,t)$[consume(i)$valcap(i,v,r,t)] =
    h2_conversion_rate(i,v,r,t)$h2(i) + dac_conversion_rate(i,t)$dac(i) ;

* H2 energy intensity is either 52,217 btu / lb
* (LHV, based on https://www.nrel.gov/docs/gen/fy08/43061.pdf)
* or 60,920 btu / lb (HHV, based on
* https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html)
* DOE H2 office recommends using the HHV value
* need to get from Btu / lb to metric ton / MMBtu
* (1/(btu/lb)) * (metric tons / lb) * (Btu / MMBtu) = metric ton / MMBtu
h2_combustion_intensity = (1/h2_energy_intensity) * (1/lb_per_tonne) * 1e6 ;

* -- H2 Transport network  --

set h2_st "defines investments needed to store and transport H2"
/
$offlisting
$include inputs_case%ds%h2_st.csv
$onlisting
/ ;

set h2_stor(h2_st) "H2 storage options"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_stor.csv
$offdelim
$onlisting
/ ;

* Units for H2 transport and storage
* See ReEDS_2.0_Input_Processing for formatting
*Pipelines
*  Overnight Capital Cost (cost_cap)              $/[(metric ton/hour)*mile]
*  FOM (fom)                                      $/[(metric ton/hour)*mile*year]
*  Electric load (electric_load)                  MWh/metric ton
*Compressors
*  Overnight Capital Cost (cost_cap)              $/(metric ton-hour)
*  FOM (fom)                                      $/[(metric ton/hour)*year)
*  Electric load (electric_load)                  MWh/metric ton
*Storage:
*  Overnight Capital Cost (cost_cap)              $/metric ton
*  FOM (fom)                                      $/(metric ton*year)
*  Electric load (electric_load)                  MWh/metric ton
parameter h2_cost_inputs(h2_st,allt,*) "--units vary (see commented text above)-- input h2 transport and storage characteristics"
$offlisting
$ondelim
$offdigit
/
$include inputs_case%ds%h2_transport_and_storage_costs.csv
/
$ondigit
$offdelim
$onlisting
;

* Above ground H2 storage can be built anywhere,
* salt cavern / hardrock storage are mapped to select BAs.
* We don't have limits on capacity by storage type, and the cost order is
* salt < rock < aboveground, so we only keep the cheapest type in each region.
set h2_stor_r(h2_stor,r) "viable BAs for H2 storage by storage tech"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_storage_rb.csv
$offdelim
$onlisting
/ ;


parameter cost_h2_transport_cap(r,rr,allt)          "--$/(metric ton/hour)-- capital cost of H2 inter-BA transport pipeline per metric ton-hour"
          cost_h2_transport_fom(r,rr,allt)          "--$/[(metric ton/hour)*yr]-- fixed OM cost of H2 inter-BA transport pipeline per metric ton-hour"
          cost_h2_storage_cap(h2_stor,allt)         "--$/metric ton-- capital cost of H2 storage per metric ton"
          cost_h2_storage_fom(h2_stor,allt)         "--$/(metric ton*yr)-- fixed OM cost of H2 storage per metric ton"
          h2_network_load(h2_st,allt)               "--MWh/metric ton-- electricity consumption of H2 network components"
;

* read in capital cost multiplier from financial processing script
parameter h2_cap_cost_mult_pipeline(allt) "capital cost multiplier for h2 pipelines"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_pipeline_cap_cost_mult.csv
$offdelim
$onlisting
/ ;

parameter h2_cap_cost_mult_compressor(allt) "capital cost multiplier for h2 compressors"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_compressor_cap_cost_mult.csv
$offdelim
$onlisting
/ ;

parameter h2_cap_cost_mult_storage(allt) "capital cost multiplier for h2 storage"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_storage_cap_cost_mult.csv
$offdelim
$onlisting
/ ;

$onempty
parameter pipeline_cost_mult(r,rr) "--fraction-- cost multiplier for H2 pipelines (will be added to 1)"
/
$offlisting
$ondelim
$include inputs_case%ds%pipeline_cost_mult.csv
$offdelim
$onlisting
/ ;
$offempty

* here computing capital and FOM costs as $/metric ton-hour for all possible routes
* including capital cost multipliers, which are different for pipelines and compressors
* note that pipeline distance is between BA centroids
cost_h2_transport_cap(r,rr,allt)$h2_routes_inv(r,rr) =
        h2_cost_inputs("h2_pipeline",allt,"cost_cap") * h2_cap_cost_mult_pipeline(allt)
        * pipeline_distance(r,rr) * (1 + pipeline_cost_mult(r,rr))
        + h2_cost_inputs("h2_compressor",allt,"cost_cap") * h2_cap_cost_mult_compressor(allt)
;

cost_h2_transport_fom(r,rr,allt)$h2_routes_inv(r,rr) =
        h2_cost_inputs("h2_pipeline",allt,"fom")
        * pipeline_distance(r,rr) * (1 + pipeline_cost_mult(r,rr))
        + h2_cost_inputs("h2_compressor",allt,"fom")
;

* for storage the cost is based on the storage capacity and already includes the cost of compressor
cost_h2_storage_cap(h2_stor,allt)$h2_stor(h2_stor) =
    h2_cost_inputs(h2_stor,allt,"cost_cap") * h2_cap_cost_mult_storage(allt) ;

cost_h2_storage_fom(h2_stor,allt)$h2_stor(h2_stor) =
    h2_cost_inputs(h2_stor,allt,"fom") ;

* electric load from compressors in the h2 network
h2_network_load(h2_st,allt) = h2_cost_inputs(h2_st,allt,"electric_load") ;


*==================================
* --- Flexible CCS Parameters ---
*==================================

set ccsflex_cat "flexible ccs performance parameter categories"
/
$offlisting
$include inputs_case%ds%ccsflex_cat.csv
$onlisting
/ ;

table ccsflex_perf(i,ccsflex_cat)  "--varies-- flexible ccs performance characteristics"
$offlisting
$ondelim
$include inputs_case%ds%ccsflex_perf.csv
$offdelim
$onlisting
;

Parameter
  ccsflex_powlim(i,allt)           "--fraction-- ratio of maximum CCS loading (MWh) per gross generation (MWh) (gen to grid + gen to ccs)"
  ccsflex_co2eff(i,allt)           "--metric tons/MWh-- CO2 removal rate from CCS per total loading on the CCS system during a time-slice"
  ccsflex_sto_storage_eff(i,allt)  "--unitless-- efficiency of flexible ccs process storage"
  ccsflex_sto_storage_duration(i)  "--hours-- duration of flexible ccs process storage"
;

ccsflex_powlim(i,t)$[ccsflex(i)$ccsflex_perf(i,"pow_lim")] = round(ccsflex_perf(i,"pow_lim"), 4);

$ifthen.ccsflexco2eff %GSw_CCSFLEX_cap_max%==90
  ccsflex_co2eff(i,t)$[ccsflex(i)$ccsflex_perf(i,"co2_eff_90")] = round(ccsflex_perf(i,"co2_eff_90"), 4) ;
$elseif.ccsflexco2eff %GSw_CCSFLEX_cap_max%==95
  ccsflex_co2eff(i,t)$[ccsflex(i)$ccsflex_perf(i,"co2_eff_95")] = round(ccsflex_perf(i,"co2_eff_95"), 4) ;
$endif.ccsflexco2eff

ccsflex_sto_storage_eff(i,t)$[ccsflex_sto(i)$ccsflex_perf(i,"stor_eff")] = ccsflex_perf(i,"stor_eff") ;

ccsflex_sto_storage_duration(i)$[ccsflex_sto(i)$ccsflex_perf(i,"stor_dur")] = ccsflex_perf(i,"stor_dur") ;

*======================================================
* -- Cooling water cost and performance adjustments --
*======================================================

*CSP with Storage costs assume dry cooling removing 5% cost adder
ctt_cost_vom_mult(i,ctt)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$i_numeraire(i)] = 1 ;
ctt_cc_mult(i,ctt)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$i_numeraire(i)] = 1 ;

*populating empty entries of cooling technology type specific multipliers to 1
ctt_cost_vom_mult(i,ctt)$[(not ctt_cost_vom_mult(i,ctt))$i_numeraire(i)] = 1 ;
ctt_cc_mult(i,ctt)$[(not ctt_cc_mult(i,ctt))$i_numeraire(i)] = 1 ;
ctt_hr_mult(i,ctt)$[(not ctt_hr_mult(i,ctt))$i_numeraire(i)] = 1 ;

*applying the cooling technologies dependent multipliers to plant_char
*note that these multipliers are only applied to new builds
*existing parameter definitions appropriately extend these to upgrade technologies.
if(Sw_WaterMain=1,

if(Sw_CoolingTechMults = 0,
  ctt_cost_vom_mult(i,ctt)$ctt_cost_vom_mult(i,ctt) = 1 ;
  ctt_cc_mult(i,ctt)$ctt_cc_mult(i,ctt) = 1 ;
  ctt_hr_mult(i,ctt)$ctt_hr_mult(i,ctt) = 1 ;
) ;

plant_char(i,v,t,"capcost")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],ctt_cc_mult(ii,ctt)*plant_char0(ii,t,"capcost") } ;
plant_char(i,v,t,"fom")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],plant_char0(ii,t,"fom") } ;
plant_char(i,v,t,"vom")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],ctt_cost_vom_mult(ii,ctt)*plant_char0(ii,t,"vom") } ;
plant_char(i,v,t,"heatrate")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],ctt_hr_mult(ii,ctt)*plant_char0(ii,t,"heatrate") } ;
plant_char(i,v,t,"rte")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],plant_char0(ii,t,"rte") } ;
) ;


*==================================
* --- PV+Battery Configurations ---
*==================================

parameter ilr_pvb_config(pvb_config) "--unitless-- inverter loading ratio for each hybrid pv+battery configuration"
/
$offlisting
$ondelim
$include inputs_case%ds%pvb_ilr.csv
$offdelim
$onlisting
/ ;

parameter ilr(i) "--unitless-- inverter loading ratio - used to convert DC capacity to AC capacity for PV" ;
* assign a default value of 1.0 for every technology (used in e_report.gms)
ilr(i)$[valcap_i(i)] = 1 ;
ilr(i)$[upv(i)] = ilr_utility ;
ilr(i)$distpv(i) = ilr_dist ;
* assign an ILR to hybrid PV+battery technologies based on the ILR for the configurations
ilr(pvb) = sum{pvb_config$pvb_agg(pvb_config,pvb), ilr_pvb_config(pvb_config) } ;

parameter bir_pvb_config(pvb_config) "--unitless-- ratio of the battery capacity to the inverter capacity (MW_battery / MW_inverter) for each hybrid pv+battery configuration"
/
$offlisting
$ondelim
$include inputs_case%ds%pvb_bir.csv
$offdelim
$onlisting
/ ;

* Assign a battery capacity ratio to each hybrid PV+battery technology
parameter bcr(i) "--unitless-- ratio of the battery capacity to the PV DC capacity (battery capacity ratio)" ;
bcr(pvb) = sum{pvb_config$pvb_agg(pvb_config,pvb), bir_pvb_config(pvb_config) / ilr_pvb_config(pvb_config) } ;
bcr(i)$[storage_standalone(i) or csp_storage(i) or hyd_add_pump(i)] = 1 ;

*=========================================
* --- Capital costs ---
*=========================================

parameter cost_cap(i,t)           "--2004$/MW-- overnight capital costs",
          cost_cap_energy(i,t)    "--2004$/MWh-- overnight capital costs of energy storage capacity",
          cost_upgrade(i,v,r,t)   "--2004$/MW-- overnight costs of upgrading to tech i",
          upgrade_derate(i,v,r,t) "--unitless [0-1]-- reduction in capacity from nameplate when upgrading a unit given need to power CCS equipment"
;

cost_cap(i,t) = plant_char0(i,t,"capcost") ;
cost_cap_energy(i,t)$battery(i) = plant_char0(i,t,"capcost_energy") ;

* apply user-defined cost reduction to Flexible CCS uniformly in all years
cost_cap(i,t)$ccsflex(i) = cost_cap(i,t) * %GSw_CCSFLEX_cost_mult% ;

cost_cap(i,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)], ctt_cc_mult(ii,ctt)*plant_char0(ii,t,"capcost") } ;

* Assign hybrid PV+battery to have the same value as UPV
parameter cost_cap_pvb_p(i,t) "--2004$/MW-- overnight capital costs for PV portion of hybrid PV+battery" ;
cost_cap_pvb_p(i,t)$pvb(i) =  sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap(ii,t) } ;

* Assign hybrid PV+battery to have the same value as battery_li
parameter cost_cap_pvb_b(i,t) "--2004$/MW-- overnight capital costs for battery portion of hybrid PV+battery" ;
cost_cap_pvb_b(i,t)$pvb(i) = cost_cap("battery_li",t) + %GSw_PVB_Dur% * cost_cap_energy("battery_li",t) ;

* Written by plantcostprep.py
table hydrocapmult(allt,i) "--unitless-- hydropower capital cost multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%hydrocapcostmult.csv
$offdelim
$onlisting
;

* Written by plantcostprep.py
$onempty
table dr_shed_capmult(i,r,allt) "--unitless-- dr_shed capital cost multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%dr_shed_capcostmult.csv
$offdelim
$onlisting
;
$offempty

$onempty
table dr_shed_capacity_scalar(i,r,allt) "--unitless-- dr_shed capacity multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%dr_shed_capacity_scalar.csv
$offdelim
$onlisting
;
$offempty


*Written in copy_files.py
$onempty
table vom_dr_shed(i,r,allt) "--$/MWh-- dr_shed vom costs over time"
$offlisting
$ondelim
$include inputs_case%ds%plantchar_dr_shed_vom.csv
$offdelim
$onlisting
;
$offempty


*Written in copy_files.py
$onempty
table fom_dr_shed(i,r,allt) "--$/MWh-- dr_shed vom costs over time"
$offlisting
$ondelim
$include inputs_case%ds%plantchar_dr_shed_fom.csv
$offdelim
$onlisting
;
$offempty


* Written by plantcostprep.py
table ofswind_rsc_mult(allt,i) "--unitless-- multiplier by year for supply curve cost"
$offlisting
$ondelim
$include inputs_case%ds%ofswind_rsc_mult.csv
$offdelim
$onlisting
;



hydrocapmult(t,i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), hydrocapmult(t,ii) } ;

*====================
* --- Variable OM ---
*====================

parameter cost_vom(i,v,r,t) "--2004$/MWh-- variable OM" ;

cost_vom(i,initv,r,t)$[(not Sw_BinOM)$valgen(i,initv,r,t)] = plant_char(i,initv,"%startyear%",'vom') ;

*if binning historical plants cost_vom, still need to assign default values to new plants
cost_vom(i,newv,r,t)$[(Sw_BinOM)$valgen(i,newv,r,t)] = plant_char(i,newv,t,'vom') ;

*if binning VOM and FOM costs, use the values written by writehintage.py for existing plants
cost_vom(i,initv,r,t)$[Sw_BinOM$valgen(i,initv,r,t)] = sum{allt$att(allt,t), hintage_data(i,initv,r,allt,"wVOM") } ;

*use default values if they are missing from the writehintage outputs
*but still active via valgen
cost_vom(i,initv,r,t)$[Sw_BinOM$(not cost_vom(i,initv,r,t))$valgen(i,initv,r,t)] =
                            plant_char(i,initv,"%startyear%",'vom') ;

*VOM costs by v are averaged over the class's associated
*years divided by those values
cost_vom(i,newv,r,t)$[valgen(i,newv,r,t)$countnc(i,newv)] =
  sum{tt$ivt(i,newv,tt), plant_char(i,newv,tt,'vom') } / countnc(i,newv) ;

cost_vom(i,v,r,t)$[valcap(i,v,r,t)$hydro(i)] = vom_hyd ;

* Add VOM cost for dr shed resource to cost_vom
cost_vom(i,v,r,t)$[valcap(i,v,r,t)$dr_shed(i)] = vom_dr_shed(i,r,t) ;


* Assign hybrid PV+battery to have the same value as UPV
parameter cost_vom_pvb_p(i,v,r,t) "--2004$/MWh-- variable OM for the PV portion of hybrid PV+battery " ;
cost_vom_pvb_p(i,v,r,t)$pvb(i) =  sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_vom(ii,v,r,t) } ;

* Assign hybrid PV+battery to have the same value as Battery_li
parameter cost_vom_pvb_b(i,v,r,t) "--2004$/MWh-- variable OM for the battery portion of hybrid PV+battery " ;
cost_vom_pvb_b(i,v,r,t)$pvb(i) =  cost_vom("battery_li",v,r,t) ;

* Assign hybrid plant to have the same value as UPV
parameter cost_vom_hybrid_plant(i,v,r,t) "--2004$/MWh-- variable OM for the plant portion of hybrid" ;
cost_vom_hybrid_plant(i,v,r,t)$[storage_hybrid(i)$(not csp(i))] =  sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_vom(ii,v,r,t) } ;

* Assign hybrid storage to have the same value as Battery_li
parameter cost_vom_hybrid_storage(i,v,r,t) "--2004$/MWh-- variable OM for the storage portion of hybrid" ;
cost_vom_hybrid_storage(i,v,r,t)$[storage_hybrid(i)$(not csp(i))] = cost_vom("battery_li",v,r,t) ;

*upgrade vom costs for initial classes are the vom costs for that tech
*plus the delta between upgrade_to and upgrade_from for the initial year
cost_vom(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,initv,r,t)] =
  sum{(v,ii,tt)$[newv(v)$ivt(ii,v,tt)$upgrade_to(i,ii)$(tt.val=Sw_UpgradeChar_Year)],
      plant_char(ii,v,tt,"VOM") + vom_hyd$hydro(ii) }
;

*if available, set cost_vom for upgrades of CCS plants to those specified in hintage_data
cost_vom(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$ccs(i)$Sw_UpgradeVOM_Nems$unitspec_upgrades(i)
                      $sum{ii$upgrade_from(i,ii), valcap(ii,initv,r,t) }
                      $sum{ii$upgrade_from(i,ii), hintage_data(ii,initv,r,t,"wCCS_Retro_vom") }] =
       sum{ii$upgrade_from(i,ii), hintage_data(ii,initv,r,t,"wCCS_Retro_vom") }
;


*upgrade vom costs for new classes are the vom costs
*of the plant the upgrade is moving to - note that ivt
*for the upgrade and the upgrade_to plant are the same
cost_vom(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,newv,r,t)] =
        sum{ii$upgrade_to(i,ii), cost_vom(ii,newv,r,t) } ;

*=================
* --- Fixed OM ---
*=================

parameter cost_fom(i,v,r,t)           "--2004$/MW-yr-- fixed O&M",
          cost_fom_energy(i,v,r,t)    "--2004$/MWh-yr-- fixed O&M of the energy capacity of a storage system"
;

*previous calculation (without tech binning)
cost_fom(i,v,r,t)$[(not Sw_binOM)$valcap(i,v,r,t)] = plant_char(i,v,t,'fom') ;
cost_fom_energy(i,v,r,t)$[(battery(i))$valcap(i,v,r,t)] = plant_char(i,v,t,'fom_energy') ;

*if using binned costs, still need to assign default values to cost_fom for new plants
cost_fom(i,newv,r,t)$[(Sw_binOM)$valcap(i,newv,r,t)] = plant_char(i,newv,t,'fom') ;

cost_fom(i,initv,r,t)$[Sw_BinOM$valcap(i,initv,r,t)] = sum{allt$att(allt,t), hintage_data(i,initv,r,allt,"wFOM") } ;

*use default values if they are missing from the writehintage outputs
*but still active via valgen
cost_fom(i,initv,r,t)$[Sw_BinOM$(not cost_fom(i,initv,r,t))$valcap(i,initv,r,t)] =
                            plant_char(i,initv,"%startyear%",'fom') ;

*fom costs for a specific bintage is the average over that bintage's time frame
cost_fom(i,newv,r,t)$[valcap(i,newv,r,t)$countnc(i,newv)] =
  sum{tt$ivt(i,newv,tt), plant_char(i,newv,tt,'fom')  } / countnc(i,newv) ;

* If there is only one vintage, do not use the average over the vintages
* Just use the new1 vintage data instead
cost_fom(i,'new1',r,t)$[valcap(i,'new1',r,t)$one_newv(i)$plant_char(i,'new1',t,'fom')] = plant_char(i,'new1',t,'fom') ;

* Assign hybrid PV+battery to have the same value as UPV
parameter cost_fom_pvb_p(i,v,r,t) "--2004$/MW-yr-- fixed OM for the PV portion of hybrid PV+battery " ;
cost_fom_pvb_p(i,v,r,t)$pvb(i) =  sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_fom(ii,v,r,t) } ;

* Assign hybrid PV+battery to have the same value as Battery_li
parameter cost_fom_pvb_b(i,v,r,t) "--2004$/MW-yr-- fixed OM for the battery portion of hybrid PV+battery " ;
cost_fom_pvb_b(i,v,r,t)$pvb(i) =  cost_fom("battery_li",v,r,t) + %GSw_PVB_Dur% * cost_fom_energy("battery_li",v,r,t) ;

cost_fom(i,v,r,t)$[valcap(i,v,r,t)$pvb(i)] = cost_fom_pvb_p(i,v,r,t) + bcr(i) * cost_fom_pvb_b(i,v,r,t) ;

* -- FOM adjustments for coal and nuclear plants
* The escalation factors are taken from NEMS and are roughly based on the
* "Endogenous plant retirement modeling" section of AEO2025's EMM Assumptions
* (https://www.eia.gov/outlooks/aeo/assumptions/pdf/EMM_Assumptions.pdf)

parameter plant_age(i,v,r,t) "--years-- plant age of existing units" ;
*a plants age is the difference between the current year and
*the year at which the plant came online
plant_age(i,v,r,t)$[valcap(i,v,r,t)$initv(v)] =
  max(0, yeart(t) - hintage_data(i,v,r,"%startyear%","wOnlineYear") ) ;

cost_fom(i,initv,r,t)$[Sw_BinOM$valcap(i,initv,r,t)$coal(i)] =
  cost_fom(i,initv,r,t) + coal_fom_adj * plant_age(i,initv,r,t) * Sw_NukeCoalFOM ;

cost_fom(i,initv,r,t)$[Sw_BinOM$valcap(i,initv,r,t)$nuclear(i)$(plant_age(i,initv,r,t) > nuke_fom_adj_age_threshold)] =
  cost_fom(i,initv,r,t) + nuke_fom_adj * Sw_NukeCoalFOM ;

table hyd_fom(i,r) "--$/MW-year -- Fixed O&M for hydro technologies"
$offlisting
$ondelim
$include inputs_case%ds%hyd_fom.csv
$offdelim
$onlisting
;

*note conditional here that will only replace fom
*for hydro techs if it is included in hyd_fom(i,r)
cost_fom(i,v,r,t)$[valcap(i,v,r,t)$hydro(i)$hyd_fom(i,r)] = hyd_fom(i,r) ;

* Add FOM cost for dr shed resource to cost_fom
cost_fom(i,v,r,t)$[valcap(i,v,r,t)$dr_shed(i)] = fom_dr_shed(i,r,t) ;

cost_fom(i,initv,r,t)$[(not Sw_BinOM)$valcap(i,initv,r,t)] = sum{tt$tfirst(tt), cost_fom(i,initv,r,tt) } ;

*upgrade fom costs for initial classes are the fom costs for that tech
*plus the delta between upgrade_to and upgrade_from for the initial year
cost_fom(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,initv,r,t)] =
  sum{(v,ii,tt)$[newv(v)$ivt(ii,v,tt)$upgrade_to(i,ii)$(tt.val=Sw_UpgradeChar_Year)],
      plant_char(ii,v,tt,"FOM") + hyd_fom(ii,r)$hydro(ii) }
;

*if available, set cost_fom for upgrades of CCS plants to those specified in hintage_data
cost_fom(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$ccs(i)$Sw_UpgradeFOM_Nems$unitspec_upgrades(i)
                      $sum{ii$upgrade_from(i,ii), valcap(ii,initv,r,t) }
                      $sum{ii$upgrade_from(i,ii), hintage_data(ii,initv,r,t,"wCCS_Retro_FOM") }] =
            1e3 * sum{ii$upgrade_from(i,ii), hintage_data(ii,initv,r,t,"wCCS_Retro_FOM") }
;

*upgrade fom costs for new classes are the fom costs
*of the plant that it is being upgraded to
cost_fom(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,newv,r,t)] =
      sum{ii$upgrade_to(i,ii), cost_fom(ii,newv,r,t) } ;

*====================
* --- Heat Rates ---
*====================

parameter heat_rate(i,v,r,t) "--MMBtu/MWh-- heat rate" ;

heat_rate(i,v,r,t)$valcap(i,v,r,t) = plant_char(i,v,t,'heatrate') ;

heat_rate(i,newv,r,t)$[valcap(i,newv,r,t)$countnc(i,newv)] =
      sum{tt$ivt(i,newv,tt), plant_char(i,newv,tt,'heatrate') } / countnc(i,newv) ;

* fill in heat rate for initial capacity that does not have a binned heatrate
heat_rate(i,initv,r,t)$[valcap(i,initv,r,t)$(not heat_rate(i,initv,r,t))] =  plant_char(i,initv,"%startyear%",'heatrate') ;

*note here conversion from btu/kwh to MMBtu/MWh
heat_rate(i,v,r,t)$[valcap(i,v,r,t)$sum{allt$att(allt,t), binned_heatrates(i,v,r,allt) }] =
                    sum{allt$att(allt,t), binned_heatrates(i,v,r,allt) } / 1000 ;


set prepost "set defining pre-2010 values versus post-2010 values"
/
$offlisting
$include inputs_case%ds%prepost.csv
$onlisting
/ ;

*part load heatrate adjust based on historical EIA generation and fuel use data
*this reflects the indescrepancy from the partial-loaded heat rate
*and the fully-loaded heat rate

table heat_rate_adj(i,prepost) "--unitless-- partial load heatrate adjuster based on historical EIA generation and fuel use data"
$offlisting
$ondelim
$include inputs_case%ds%heat_rate_adj.csv
$offdelim
$onlisting
;

heat_rate_adj(i,prepost)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), heat_rate_adj(ii,prepost) } ;

heat_rate_adj(i,prepost)$upgrade(i) = sum{ii$upgrade_to(i,ii), heat_rate_adj(ii,prepost) } ;

*upgrade heat rates for initial classes are the heat rates for that tech
*plus the delta between upgrade_to and upgrade_from for the initial year
heat_rate(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,initv,r,t)] =
      sum{(v,ii,tt)$[newv(v)$ivt(ii,v,tt)$upgrade_to(i,ii)$(tt.val=Sw_UpgradeChar_Year)],
            plant_char(ii,v,tt,"heatrate") }
;

*if available, set heat_rate for upgrades of CCS plants to those specified in hintage_data
heat_rate(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$ccs(i)
                      $sum{ii$upgrade_from(i,ii), valcap(ii,initv,r,t) }
                      $sum{ii$upgrade_from(i,ii), hintage_data(ii,initv,r,t,"wCCS_Retro_HR") }] =
            sum{ii$upgrade_from(i,ii), hintage_data(ii,initv,r,t,"wCCS_Retro_HR") / 1000 }
;

*upgrade heat rates for new classes are the heat rates for
*the bintage and technology for what it is being upgraded to
heat_rate(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,newv,r,t)] =
        sum{ii$upgrade_to(i,ii), heat_rate(ii,newv,r,t) } ;

heat_rate(i,v,r,t)$[heat_rate_adj(i,'pre2010')$initv(v)] = heat_rate_adj(i,'pre2010') * heat_rate(i,v,r,t) ;
heat_rate(i,v,r,t)$[heat_rate_adj(i,'post2010')$newv(v)] = heat_rate_adj(i,'post2010') * heat_rate(i,v,r,t) ;

*=========================================
* --- Fuel Prices ---
*=========================================

parameter fuel_price(i,r,t) "$/MMBtu - fuel prices by technology" ;


* Written by input_processing\fuelcostprep.py
* declared over allt to allow for external data files that extend beyond end_year
table fprice(allt,r,f) "--2004$/MMBtu-- fuel prices by fuel type"
$offlisting
$ondelim
$include inputs_case%ds%fprice.csv
$offdelim
$onlisting
;

fuel_price(i,r,t)$[sum{f$fuel2tech(f,i),1}] =
  sum{(f,allt)$[fuel2tech(f,i)$(year(allt)=yeart(t))], fprice(allt,r,f) } ;

fuel_price(i,r,t)$[sum{f$fuel2tech(f,i),1}$(not fuel_price(i,r,t))] =
  sum{rr$fuel_price(i,rr,t), fuel_price(i,rr,t) } / max(1,sum{rr$fuel_price(i,rr,t), 1 }) ;

fuel_price(i,r,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), fuel_price(ii,r,t) } ;



*=====================================================
* -- Climate impacts on nondispatchable hydropower --
*=====================================================

$ifthen.climatehydro %GSw_ClimateHydro% == 1
parameter climate_hydro_annual(r,allt)  "annual dispatchable hydropower availability" ;
$endif.climatehydro

*created by /input_processing/writecapdat.py
parameter cap_hyd_ccseason_adj(i,ccseason,r) "--fraction-- ccseason max capacity adjustment for dispatchable hydro"
/
$offlisting
$ondelim
$include inputs_case%ds%cap_hyd_ccseason_adj.csv
$offdelim
$onlisting
/ ; 

table wind_cf_adj_t(allt,i) "--unitless-- wind capacity factor adjustments by class, from ATB"
$offlisting
$ondelim
$include inputs_case%ds%windcfmult.csv
$offdelim
$onlisting
;

parameter pv_cf_improve(allt) "--unitless-- PV capacity factor improvement"
/
$offlisting
$ondelim
$include inputs_case%ds%pv_cf_improve.csv
$offdelim
$onlisting
/ ;

parameter cf_adj_t(i,v,t)        "--unitless-- capacity factor adjustment over time for RSC technologies" ;

cf_adj_t(i,v,t)$[(rsc_i(i) or hydro(i))$sum{r, valcap(i,v,r,t) }] = 1 ;

* Existing wind uses 2010 cf adjustment
cf_adj_t(i,initv,t)$[wind(i)$sum{r, valcap(i,initv,r,t) }] = wind_cf_adj_t("%startyear%",i) ;

cf_adj_t(i,newv,t)$[wind_cf_adj_t(t,i)$countnc(i,newv)$sum{r, valcap(i,newv,r,t) }] =
          sum{tt$ivt(i,newv,tt), wind_cf_adj_t(tt,i) } / countnc(i,newv) ;

* Apply PV capacity factor improvements
cf_adj_t(i,newv,t)$[(pv(i) or pvb(i))$countnc(i,newv)$sum{r, valcap(i,newv,r,t) }] =
          sum{tt$ivt(i,newv,tt), pv_cf_improve(tt) } / countnc(i,newv) ;



*========================================
*      --- OPERATING RESERVES ---
*========================================

set ortype "types of operating reserve constraints"
/
$offlisting
$include inputs_case%ds%ortype.csv
$onlisting
/ ;

set opres_model(ortype)       "operating reserve types modeled" ;

set orcat "operating reserve category for RHS calculations"
/
$offlisting
$include inputs_case%ds%orcat.csv
$onlisting
/ ;

* define elements in opres_model based on sw_opres
opres_model(ortype)$[not Sw_Opres] = no ;
opres_model(ortype)$[(Sw_Opres = 1)$(not sameas(ortype,"combo"))] = yes ;
opres_model("combo")$[(Sw_Opres = 2)] = yes ;


Parameter
  reserve_frac(i,ortype)  "--fraction-- fraction of a technology's online capacity that can contribute to a reserve type"
  ramptime(ortype)        "--minutes-- minutes for ramping limit constraint in operating reserves"
/
$offlisting
$ondelim
$include inputs_case%ds%ramptime.csv
$offdelim
$onlisting
/ ;


table orperc(ortype,orcat) "operating reserve percentage by type and category"
$offlisting
$ondelim
$include inputs_case%ds%orperc.csv
$offdelim
$onlisting
;

* for simplified combination, make the constraints as
* stringent as possible - ie sum over all requirements
orperc("combo",orcat) = sum{ortype,orperc(ortype,orcat) } ;

* combo ramptime is average across all ortypes where defined
ramptime("combo") = sum{ortype$ramptime(ortype) , ramptime(ortype) }
                    / sum{ortype$ramptime(ortype) , 1 } ;

* multiplier for reserves requirement
orperc(ortype,orcat) = orperc(ortype,orcat) * Sw_OpResReqMult ;

*ramp rates are used to limit a technology's contribution to Operating Reserve.
parameter ramprate(i) "--fraction/min-- ramp rate of dispatchable generators"
/
$offlisting
$ondelim
$include inputs_case%ds%ramprate.csv
$offdelim
$onlisting
/ ;

*dispatchable hydro is the only "hydro" technology that can provide operating reserves.
ramprate(i)$hydro_d(i) = ramprate("hydro") ;
ramprate(i)$geo(i) = ramprate("geothermal") ;

*if running with flexible nuclear, set ramp rate of nuclear to that of coal
ramprate(i)$[nuclear(i)$Sw_NukeFlex] = ramprate("coal-new") ;

ramprate(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), ramprate(ii) } ;

ramprate(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), ramprate(ii) } ;

* Do not allow the reserve fraction to exceed 100%, so use the minimum of 1 or the computed value.
reserve_frac(i,ortype) = min(1,ramprate(i) * ramptime(ortype)) ;

reserve_frac(i,ortype)$upgrade(i) = sum{ii$upgrade_to(i,ii), reserve_frac(ii,ortype) } ;

* input data for opres reserve costs by generator type (in $2004)
* current options are bottom up costs by generator type ("default") or estimates based on historical reserve prices ("market")
* market data based on national reserve prices in https://www.nrel.gov/docs/fy19osti/72578.pdf (converted from $2017)
table cost_opres_input(i,ortype)
$offlisting
$ondelim
$include inputs_case%ds%cost_opres_%GSw_OpResCost%.csv
$offdelim
$onlisting
;

parameter cost_opres(i,ortype,t) "--$ / MWh-- cost of reg operating reserves" ;
cost_opres(i,ortype,t) = cost_opres_input(i, ortype) ;

* assign reserve costs to all geothermal techs
cost_opres(i,ortype,t)$geo(i) = cost_opres("geothermal",ortype,t) ;

* Assign hybrid PV+battery the same value as battery_li
cost_opres(i,ortype,t)$pvb(i) = cost_opres("battery_li",ortype,t) ;

* add heat rate penalty for providing reserves (currently only applied to spin)
* input data calculated based on heat rates in the PLEXOS EI database as of Dec. 2020
parameter spin_hr_penalty(i) "--fraction-- heat rate penalty for providing spinning reserves"
/
$offlisting
$ondelim
$include inputs_case%ds%heat_rate_penalty_spin.csv
$offdelim
$onlisting
/ ;

* calculate average heat rate and fuel prices
parameter fuel_price_avg(i,t) ;
parameter heat_rate_avg(i,t) ;

* calculate average fuel price and heat rates
fuel_price_avg(i,t)$[sum{r, fuel_price(i,r,t) }] = sum{r, fuel_price(i,r,t) } / sum{r, 1$[fuel_price(i,r,t)] } ;

heat_rate_avg(i,t)$[sum{(v,r), heat_rate(i,v,r,t) }] =
  sum{(v,r), heat_rate(i,v,r,t) } / sum{(v,r), 1$[heat_rate(i,v,r,t)] } ;

* calculate penalty value, assign to cost_opres
* only assign penalty in instances where spin costs are not already defined
cost_opres(i,"spin",t)$[not cost_opres(i,"spin",t)] =
  spin_hr_penalty(i) * heat_rate_avg(i,t) * fuel_price_avg(i,t) ;

cost_opres(i,ortype,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), cost_opres(ii,ortype,t) } ;

cost_opres(i,ortype,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_opres(ii,ortype,t) } ;

* again - making the assumption that the combination
* operating reserve is the most stringent/costly
cost_opres(i,"combo",t) = smax{ortype, cost_opres(i,ortype,t) } ;


*======================================================
* --- MinLoading (only used if Sw_MinLoading != 0) ---
*======================================================

parameter minloadfrac0(i) "--fraction-- initial minimum loading fraction"
/
$offlisting
$ondelim
$include inputs_case%ds%minloadfrac0.csv
$offdelim
$onlisting
/ ;

minloadfrac0(i)$geo(i) = minloadfrac0("geothermal") ;

parameter hydmin_quarter(i,r,quarter) "minimum hydro loading factors by quarter and region"
/
$offlisting
$ondelim
$include inputs_case%ds%hydro_mingen.csv
$offdelim
$onlisting
/ ;

parameter startcost(i) "--$/MW-- linearized startup cost"
/
$offlisting
$ondelim
$include inputs_case%ds%startcost.csv
$offdelim
$onlisting
/ ;
startcost(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), startcost(ii) } ;
startcost(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), startcost(ii) } ;
* Turn off startcost for some techs based on GSw_StartCost
startcost(i)$[(Sw_StartCost=0)] = 0 ;
startcost(i)$[(Sw_StartCost=1)$(not nuclear(i))] = 0 ;
startcost(i)$[(Sw_StartCost=2)$(not nuclear(i))$(not ccs(i))$(not coal(i))] = 0 ;
startcost(i)$[(Sw_StartCost=3)$(not ccs(i))$(not coal(i))] = 0 ;
startcost(i)$[(Sw_StartCost=4)$(not ccs(i))$(not coal(i))$(not gas_cc(i))$(not h2_cc(i))] = 0 ;
startcost(i)$[(Sw_StartCost=5)$(nuclear(i))] = 0 ;

parameter mingen_fixed(i) "--fraction-- minimum generation level across all hours"
/
$offlisting
$ondelim
$include inputs_case%ds%mingen_fixed.csv
$offdelim
$onlisting
/ ;

*=========================================
*              --- Load ---
*=========================================

$onempty
parameter loadsite_annual(loadsitereg,allt) "--MW-- Load trajectory by loadsitereg"
/
$offlisting
$ondelim
$include inputs_case%ds%loadsite_annual.csv
$offdelim
$onlisting
/ ;
set val_loadsite(r) "Valid regions for load sites" ;
val_loadsite(r)
    $sum{(loadsitereg,t)$r_loadsitereg(r,loadsitereg),
         loadsite_annual(loadsitereg,t)
    } = yes ;

table can_growth_rate(st,allt) "growth rate for candadian demand by province"
$offlisting
$ondelim
$include inputs_case%ds%cangrowth.csv
$offdelim
$onlisting
;

parameter mex_growth_rate(allt) "growth rate for mexican demand - national"
/
$offlisting
$ondelim
$include inputs_case%ds%mex_growth_rate.csv
$offdelim
$onlisting
/ ;
$offempty


*==============================
* --- Planning Reserve Margin ---
*================================

* Written by input_processing\transmission.py
parameter prm_nt(nercr,allt) "--fraction-- planning reserve margin for NERC regions"
/
$offlisting
$ondelim
$include inputs_case%ds%prm_annual.csv
$offdelim
$onlisting
/ ;

parameter prm(r,t) "--fraction-- planning reserve margin by BA" ;
prm(r,t) = sum{nercr$r_nercr(r,nercr), prm_nt(nercr,t) } ;

$onempty
parameter firm_import_limit(nercr,allt) "--fraction-- limit on net firm imports into NERC regions"
/
$offlisting
$ondelim
$include inputs_case%ds%firm_import_limit.csv
$offdelim
$onlisting
/ ;

parameter peakload_nercr(nercr,allt) "--MW-- Peak exogenous demand across all weather years by NERC region"
/
$offlisting
$ondelim
$include inputs_case%ds%peakload_nercr.csv
$offdelim
$onlisting
/ ;
$offempty


* ===========================================================================
* Regional and temporal capital cost multipliers
* ===========================================================================
* Load scenario-specific capital cost multiplier components

parameter ccmult(i,allt) "construction cost multiplier"
/
$offlisting
$ondelim
$include inputs_case%ds%ccmult.csv
$offdelim
$onlisting
/ ;

parameter tax_rate(allt) "all-in tax rate"
/
$offlisting
$ondelim
$include inputs_case%ds%tax_rate.csv
$offdelim
$onlisting
/ ;

parameter itc_frac_monetized(i,allt) "fractional value of the ITC, after adjusting for the costs of monetization"
/
$offlisting
$ondelim
$include inputs_case%ds%itc_frac_monetized.csv
$offdelim
$onlisting
/ ;

$onempty
parameter itc_energy_comm_bonus(i,r) "energy community tax credit bonus factor"
/
$offlisting
$ondelim
$include inputs_case%ds%itc_energy_comm_bonus.csv
$offdelim
$onlisting
/ ;
$offempty

parameter pv_frac_of_depreciation(i,allt) "present value of depreciation, expressed as a fraction of the capital cost of the investment"
/
$offlisting
$ondelim
$include inputs_case%ds%pv_frac_of_depreciation.csv
$offdelim
$onlisting
/ ;

parameter degradation_adj(i,allt) "adjustment to reflect degradation over the lifetime of an asset"
/
$offlisting
$ondelim
$include inputs_case%ds%degradation_adj.csv
$offdelim
$onlisting
/ ;

parameter financing_risk_mult(i,allt) "multiplier to reflect higher financing costs for riskier assets"
/
$offlisting
$ondelim
$include inputs_case%ds%financing_risk_mult.csv
$offdelim
$onlisting
/ ;

parameter reg_cap_cost_diff(i,r) "regional capital cost difference [fraction] (note that wind-ons and upv have separate multiplers in the supply curve cost)"
/
$offlisting
$ondelim
$include inputs_case%ds%reg_cap_cost_diff.csv
$offdelim
$onlisting
/ ;

parameter eval_period_adj_mult(i,allt) "adjustment multiplier for the capital costs of techs with non-standard evaluation periods"
/
$offlisting
$ondelim
$include inputs_case%ds%eval_period_adj_mult.csv
$offdelim
$onlisting
/ ;

eval_period_adj_mult(i,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), eval_period_adj_mult(ii,t) } ;
eval_period_adj_mult(i,t)$[upgrade(i)] =
   sum{ii$upgrade_to(i,ii),eval_period_adj_mult(ii,t) } ;


* Define and calculate the scenario-specific capital cost multipliers
* If the ITC is phasing out dynamically, these will need to be re-calculated based on the phase-out
parameter
cost_cap_fin_mult(i,r,t) "final capital cost multiplier for regions and technologies - used in the objective function",
cost_cap_fin_mult_noITC(i,r,t) "final capital cost multiplier excluding ITC - used only in outputs",
cost_cap_fin_mult_no_credits(i,r,t) "final capital cost multiplier ITC/PTC/Depreciation (i.e. the actual expenditures) - used only in outputs",
cost_cap_fin_mult_out(i,r,t) "final capital cost multiplier for system cost outputs" ;

parameter trans_cost_cap_fin_mult(allt) "capital cost multiplier for transmission - used in the objective function"
/
$offlisting
$ondelim
$include inputs_case%ds%trans_cap_cost_mult.csv
$offdelim
$onlisting
/ ;

parameter trans_cost_cap_fin_mult_noITC(allt) "capital cost multiplier for transmission excluding ITC - used only in outputs"
/
$offlisting
$ondelim
$include inputs_case%ds%trans_cap_cost_mult_noITC.csv
$offdelim
$onlisting
/ ;


* --- Hybrid PV+Battery ---
* Hybrid PV+Battery: PV portion
parameter cost_cap_fin_mult_pvb_p(i,r,t)            "capital cost multiplier for the PV portion of hybrid PV+Battery"
          cost_cap_fin_mult_pvb_p_noITC(i,r,t)      "capital cost multiplier for the PV portion of hybrid PV+Battery, excluding ITC"
          cost_cap_fin_mult_pvb_p_no_credits(i,r,t) "capital cost multiplier for the PV portion of hybrid PV+Battery, excluding ITC/PTC/Depreciation"
;

* Hybrid PV+Battery: Battery portion
parameter cost_cap_fin_mult_pvb_b(i,r,t)            "capital cost multiplier for the battery portion of hybrid PV+Battery"
          cost_cap_fin_mult_pvb_b_noITC(i,r,t)      "capital cost multiplier for the battery portion of hybrid PV+Battery, excluding ITC"
          cost_cap_fin_mult_pvb_b_no_credits(i,r,t) "capital cost multiplier for the battery portion of hybrid PV+Battery, excluding ITC/PTC/Depreciation"
;


* --- Nuclear Ban ---
*Assign increased cost multipliers to regions with state nuclear bans
scalar nukebancostmult "--fraction-- penalty for constructing new nuclear in a restricted region" /%GSw_NukeStateBanCostMult%/ ;

* --- Renewable Supply Curves ---
* For offshore wind, rsc_fin_mult(i,r,t) also carries the ITC that is applied to the transmission costs in the resource supply curve cost, while rsc_fin_mult_no_ITC(i,r,t) carries financing multipliers for its transmission costs without the ITC
parameter rsc_fin_mult(i,r,t)       "--fraction-- financial cost multiplier for resource supply curve technologies that have their capital costs included in the supply curves (capital cost reduction multipliers are also included where relevant)"
          rsc_fin_mult_noITC(i,r,t) "--fraction-- financial cost multiplier excluding ITC for resource supply curve technologies that have their capital costs included in the supply curves"
;

*=========================================
* --- Emission Rate ---
*=========================================

* Emission rate by technology and etype (broken down to process and upstream)
* Note that CH4 upstream emission rate of natural gas is 0 here 
* as we will use CH4 methane leakage from GSw_MethaneLeakageScen for it later)
table emit_rate_fuel(i,etype,e)  "--metric tons per MMBtu-- emissions rate of fuel by technology and emission type"
$offlisting
$ondelim
$include inputs_case%ds%emitrate.csv
$offdelim
$onlisting
;

* this table links CCS techs with their uncontrolled tech counterpart (where such a tech exists)
set ccs_link(i,ii)    "links CCS techs with their uncontrolled tech counterpart (where such a tech exists)"
/
$offlisting
$ondelim
$include inputs_case%ds%ccs_link.csv
$ifthen.ctech %GSw_WaterMain% == 1
$include inputs_case%ds%ccs_link_water.csv
$endif.ctech
$offdelim
$onlisting
/ ;

parameter capture_rate_input(i,e) "--fraction-- fraction of emissions that are captured" ;

* Set CO2 capture rate for new CCS capacity
capture_rate_input(i,"CO2")$[ccs_mod(i)]=Sw_CCS_Rate_New_mod;
capture_rate_input(i,"CO2")$[ccs_max(i)]=Sw_CCS_Rate_New_max;

* Set CO2 capture rate for retrofit/upgrade CCS capacity
capture_rate_input(i,"CO2")$[upgrade(i)$(coal_ccs(i) or gas_cc_ccs(i))$ccs_mod(i)]=Sw_CCS_Rate_Upgrade_mod;
capture_rate_input(i,"CO2")$[upgrade(i)$(coal_ccs(i) or gas_cc_ccs(i))$ccs_max(i)]=Sw_CCS_Rate_Upgrade_max;

* emit_rate_fuel water expansion
emit_rate_fuel(i,etype,e)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), emit_rate_fuel(ii,etype,e) } ;
  
* Assign the appropriate % of generation for each technology to count toward CES requirements.
* Exclude capture rates of BECCS, which receive full credit in a CES and were already set to 1 above in the "RPS" section.
RPSTechMult(RPSCat,i,st)$[ccs(i)$(sameas(RPSCat,"CES") or sameas(RPSCat,"CES_Bundled"))$(not beccs(i))] = capture_rate_input(i,"CO2") ;

* calculate process emit rate for CCS techs (except beccs techs, which are defined directly in emitrate.csv)
emit_rate_fuel(i,"process",e)$[ccs(i)$(not beccs(i))] =
  (1 - capture_rate_input(i,e)) * sum{ii$ccs_link(i,ii), emit_rate_fuel(ii,"process",e) } ;

* calculate upstream emit rate for CCS techs (except beccs techs, which are defined directly in emitrate.csv)
emit_rate_fuel(i,"upstream",e)$[ccs(i)$(not beccs(i))] = sum{ii$ccs_link(i,ii), emit_rate_fuel(ii,"upstream",e) } ;

* assign flexible ccs the same process emission rate as the uncontrolled technology to allow variable CO2 removal (e.g., for gas-cc-ccs-f1, use gas-cc)
emit_rate_fuel(i,"process",e)$[ccsflex(i)] = sum{ii$ccs_link(i,ii), emit_rate_fuel(ii,"process",e) } ;

* set upgrade tech process emissions for non-CCS upgrades (e.g. gas-ct -> h2-ct); CCS upgrade emissions are handled above
emit_rate_fuel(i,"process",e)$[upgrade(i)$(not ccs(i))] = sum{ii$upgrade_to(i,ii), emit_rate_fuel(ii,"process",e) } ;

* set upgrade tech upstream emissions for upgrades
emit_rate_fuel(i,"upstream",e)$[upgrade(i)] = sum{ii$upgrade_to(i,ii), emit_rate_fuel(ii,"upstream",e) } ;

* parameters for calculating captured emissions
parameter capture_rate_fuel(i,e) "--metric tons per MMBtu-- emissions capture rate of fuel by technology type";
capture_rate_fuel(i,e) = capture_rate_input(i,e) * sum{ii$ccs_link(i,ii), emit_rate_fuel(ii,"process",e) } ;

* capture_rate_fuel is used to calculate how much CO2 is captured and stored;
* for beccs, the captured CO2 is the entire negative emissions rate
* since any uncontrolled emissions are assumed to be lifecycle net zero
capture_rate_fuel(i,"CO2")$beccs(i) = - emit_rate_fuel(i,"process","CO2")

parameter capture_rate(e,i,v,r,t) "--metric tons per MWh-- emissions capture rate" ;

parameter methane_leakage_rate(allt) "--fraction-- methane leakage as fraction of gross production"
* best estimate for fixed leakage rate is 0.023 (Alvarez et al. 2018, https://dx.doi.org/10.1126/science.aar7204)
/
$offlisting
$ondelim
$include inputs_case%ds%methane_leakage_rate.csv
$offdelim
$onlisting
/ ;

scalar methane_tonperMMBtu "--metric tons per MMBtu-- methane content of natural gas" ;
* [ton CO2 / MMBtu] * [ton CH4 / ton CO2]
methane_tonperMMBtu = emit_rate_fuel("gas-CC","process","CO2") * molWeightCH4 / molWeightCO2 ;

* H2 leakage rate by technology and etype (broken down to process and upstream)
parameter h2_leakage_rate(i)  "--fraction-- h2 leakage rate as a fraction of total production by technology and emission type"
/
$offlisting
$ondelim
$include inputs_case%ds%h2_leakage_rate.csv
$offdelim
$onlisting
/ ;

parameter prod_emit_rate(etype,e,i,allt) "--metric tons emitted per metric ton product-- emissions rate per metric ton of product (e.g. tonCO2/tonH2 for SMR & SMR-CCS)" ;
* Steam methane reformer (SMR)'s process emission here refers to emissions from steam methane reforming process
prod_emit_rate("process","CO2","smr",t) = smr_co2_intensity ;
prod_emit_rate("process","CO2","smr_ccs",t) = smr_co2_intensity * (1 - smr_capture_rate) ;
prod_emit_rate("process","CO2","dac",t)$Sw_DAC = -1 ;
prod_emit_rate("process","CO2","dac_gas",t)$Sw_DAC_Gas = -1 ;

scalar smr_methane_rate  "--metric tons CH4 per metric ton H2-- methane used to produce a metric ton of H2 via SMR" ;
* NOTE that we don't yet include the impact of CCS on methane use
* [ton CH4 used / ton H2] = [ton CO2 emitted / ton H2] * [ton CH4 used / ton CO2 emitted], where
* [ton CH4 used / ton CO2 emitted] is the ratio of the molecular weight of CH4 to CO2
smr_methane_rate = smr_co2_intensity * molWeightCH4 / molWeightCO2 ;

* Upstream fuel emissions for SMR
*** [ton CH4 used / ton H2] * [ton CH4 leaked / ton CH4 produced] * [ton CH4 produced / ton CH4 used]
prod_emit_rate("upstream",e,i,t)
    $[sameas(e,"CH4")
    $smr(i)
    $methane_leakage_rate(t)]
    = smr_methane_rate * methane_leakage_rate(t) / (1 - methane_leakage_rate(t))
;

* Process H2 emissions for SMR, SMR-CC, and electrolyzer
*** [ton H2 leaked / ton H2 produced] * [ton H2 produced / ton H2 used]
prod_emit_rate("process",e,i,t)
    $[sameas(e,"H2")
    $h2(i) 
    $h2_leakage_rate(i)]
    = h2_leakage_rate(i) / (1 - h2_leakage_rate(i))
;

parameter
    emit_rate(etype,eall,i,v,r,t) "--metric tons per MWh-- emissions rate"
    emit_r_tc(r,t)  "--metric tons-- CO2 emissions, regional"
    emit_nat_tc(t)  "--metric tons-- CO2 emissions, national"
;

emit_rate(etype,e,i,v,r,t)$[emit_rate_fuel(i,etype,e)$valcap(i,v,r,t)]
  = round(heat_rate(i,v,r,t) * emit_rate_fuel(i,etype,e),10) ;

*only emissions from the coal portion of cofire plants are considered
emit_rate(etype,e,i,v,r,t)$[sameas(i,"cofire")$emit_rate_fuel("coal-new",etype,e)$valcap(i,v,r,t)]
  = round((1-bio_cofire_perc) * heat_rate(i,v,r,t) * emit_rate_fuel("coal-new",etype,e),10) ;

* Fill in CH4 upstream emission rate
*** [MMBtu/MWh] * [ton methane used / MMBtu] * [ton methane leaked / ton methane produced]
*** * [ton methane produced / ton methane used] = [ton methane leaked / MWh]
emit_rate("upstream",e,i,v,r,t)
    $[methane_leakage_rate(t)
    $gas(i)
    $sameas(e,"CH4")]
    = heat_rate(i,v,r,t) * methane_tonperMMBtu * methane_leakage_rate(t) / (1 - methane_leakage_rate(t))
;

* Fill in H2 process emission rates for H2 combustion techs (h2-ct and h2-cc) (and fuel cell later)
*** [heat rate (MMBtu/MWh)] * [h2 combustion intensity (metric ton h2 used / MMBtu)] * [h2 leakage rate (metric ton h2 leaked / ton h2 produced)]
*** * [ton h2 produced / ton h2 used] = [ton h2 leaked / MWh]
emit_rate("process",e,i,v,r,t)
    $[h2_leakage_rate(i)
    $sameas(e,"H2")]
    = heat_rate(i,v,r,t) * h2_combustion_intensity * h2_leakage_rate(i) / (1 - h2_leakage_rate(i))
;

* set upgraded H2 tech emissions
emit_rate("process","H2",i,v,r,t)$[upgrade(i)] = sum{ii$upgrade_to(i,ii), emit_rate("process","H2",ii,v,r,t) } ;

* Global warming potential of different pollutants
parameter gwp(e)   "--metric ton CO2-equivalents --global warming potential"
/
$ondelim
$include inputs_case%ds%gwp.csv
$offdelim
/ ;

* CO2(e) emissions rate (used in postprocessing only)
emit_rate(etype,"CO2e",i,v,r,t)$[Sw_AnnualCap=2]
  = round(sum{e, emit_rate(etype,e,i,v,r,t) * gwp(e)$[(not sameas(e, "H2"))]},10) ;

emit_rate(etype,"CO2e",i,v,r,t)$[Sw_AnnualCap<>2]
  = round(sum{e, emit_rate(etype,e,i,v,r,t) * gwp(e)},10) ;

* calculate emissions capture rates (same logic as emissions calc above)
capture_rate(e,i,v,r,t)$[capture_rate_fuel(i,e)$valcap(i,v,r,t)]
  = round(heat_rate(i,v,r,t) * capture_rate_fuel(i,e),10) ;

capture_rate(e,i,v,r,t)$[upgrade(i)$capture_rate_fuel(i,e)] = round(heat_rate(i,v,r,t) * capture_rate_fuel(i,e),10) ;

* Declare regional emissions rate (used in c_supplymodel, defined in d_solveoneyear)
parameter
    co2_emit_rate_r(r,t) "--metric tons per MWh-- CO2 emissions rate by ReEDS region, for use in state carbon caps"
    co2_emit_rate_regional(%GSw_StateCO2ImportLevel%,t) "--metric tons per MWh-- CO2 regional emissions rate, for use in state carbon caps"
;
co2_emit_rate_r(r,t) = 0 ;
co2_emit_rate_regional(%GSw_StateCO2ImportLevel%,t) = 0 ;

* ===========================================================================
* Regional emissions rate limit (currently unused)
* ===========================================================================

set emit_rate_con(e,r,t) "set to enable or disable emissions rate limits by pollutant and region" ;
emit_rate_con(e,r,t) = no ;

parameter emit_rate_limit(e,r,t)   "--metric tons per MWh-- emission rate limit" ;
emit_rate_limit(e,r,t) = 0 ;

*============================
* Growth limits and penalties
*============================

set gbin "growth bins"
/
$offlisting
$include inputs_case%ds%gbin.csv
$onlisting
/ ;
        
*absolute growth penalties based on greatest annual change of capacity for each tech group from 1990-2016
parameter growth_limit_absolute(tg) "--MW-- growth limit for technology groups in absolute terms"
/
$offlisting
$ondelim
$include inputs_case%ds%growth_limit_absolute.csv
$offdelim
$onlisting
/ ;

parameter growth_penalty(gbin) "--unitless-- multiplier penalty on the capital cost for growth in each bin"
/
$offlisting
$ondelim
$include inputs_case%ds%growth_penalty.csv
$offdelim
$onlisting
/ ;

* gbin_min is based on the representative plant size for a single plant in that tech group
parameter gbin_min(tg) "--MW-- minimum size of the first (zero cost) growth bin"
/
$offlisting
$ondelim
$include inputs_case%ds%gbin_min.csv
$offdelim
$onlisting
/ ;

parameter growth_bin_size_mult(gbin) "--unitless-- multiplier for each growth bin to be applied to the prior solve year's annual deployment"
/
$offlisting
$ondelim
$include inputs_case%ds%growth_bin_size_mult.csv
$offdelim
$onlisting
/ ;

parameter growth_bin_limit(gbin,st,tg,t) "--MW/yr-- size of each growth bin"
          last_year_max_growth(st,tg,t)  "--MW-- maximum growth that could have been achieved in the prior year (acutal year, not solve year)"
          cost_growth(i,st,t)            "--$/MW-- cost basis for growth penalties"
;

* Initialize values
growth_bin_limit(gbin,st,tg,tfirst)$stfeas(st) = gbin_min(tg) ;
cost_growth(i,st,t) = 0 ;

*====================================
* --- CES Gas supply curve setup ---
*====================================

set gb "gas price bin must be an odd number of bins, e.g. gb1*gb15"
/
$offlisting
$include inputs_case%ds%gb.csv
$onlisting
/ ;

alias(gb,gbb) ;

* gassupply scale determines how far the bins reference quantity should deviate from its reference price
* with gassupply scale = -0.5, the center of the reference price bin will be the reference quantity
* with gassupplyscale = 0, the end of the reference gas price's bin will the limit for that reference bin

*note that the supply curve is set up such that the edge of the bin pertaining to the reference
*price sits at its upper limit, we want to move the curve such that the reference price sits at the middle of the
*respective bin

parameter gasprice(cendiv,gb,t)   "--$/MMBtu-- price of each gas bin",
          gasquant(cendiv,gb,t)   "--MMBtu - natural gas quantity for each bin",
          gaslimit(cendiv,gb,t)   "--MMBtu-- gas limit by gas bin"
          gassupply_ele(cendiv,t) "--MMBtu-- reference gas consumption by the ELE sector"
          gassupply_tot(cendiv,t) "--MMBtu-- reference gas consumption by the ELE sector" ;

* declared over allt to allow for external data files that extend beyond end_year
table gasprice_ref(cendiv,allt)   "--2004$/MMBtu-- natural gas price by census division"
$offlisting
$ondelim
$include inputs_case%ds%gasprice_ref.csv
$offdelim
$onlisting
;

* fuel costs for H2 production
* starting units for gas efficiency are MMBtu / kg - need to express this in terms of
* $ / MT through MMBtu / kg * (kg / MT) * ($ / MMBtu)
* SMR production costs seem high given gas-intensity and units
* -- cost of production, for now, just gas_intensity times reference gas price, can revisit gas price assumptions --
parameter h2_fuel_cost(i,v,r,t) "--$ per metric ton-- fuel cost for hydrogen production" ;
h2_fuel_cost(i,newv,r,t)$[h2(i)$valcap(i,newv,r,t)] = 1000 * (sum{tt$ivt(i,newv,tt),consume_char0(i,tt,"gas_efficiency") } / countnc(i,newv))
                                                           * sum{cendiv$r_cendiv(r,cendiv),gasprice_ref(cendiv,t) } * industrialGasMult ;

* initial capacity gets charged at the initial NG efficiency
h2_fuel_cost(i,initv,r,t)$[h2(i)$valcap(i,initv,r,t)] = 1000 * consume_char0(i,"%startyear%","gas_efficiency")
                                                             * sum{cendiv$r_cendiv(r,cendiv),gasprice_ref(cendiv,t) } * industrialGasMult ;

* -- adding in $ / metric ton adder for transport and storage and h2 vom cost
parameter
    h2_stor_tran(i,t) "--$ per metric ton-- adder for the cost of hydrogen transport and storage"
    h2_vom(i,t)       "--$ per metric ton-- variable cost of hydrogen production"
;

* h2_stor_tran cost applies if running hydrogen nationally (Sw_H2=1)
* if running regionally (Sw_H2=2) the costs are endogenized in the h2 network
h2_stor_tran(i,t)$[Sw_H2=1] = deflator("2016") * consume_char0(i,t,"stortran_adder") ;

* option to apply a uniform H2 storage/transport cost that does not vary by tech or year
* note that this overrides input values from the consume_char input file
h2_stor_tran(i,t)$[(Sw_H2=1)$Sw_H2_TransportUniform$h2(i)$sum{(v,r), valcap(i,v,r,t) }] = Sw_H2_TransportUniform ;

* multiply vom by 1000 because input costs are in $/kg
h2_vom(i,t)$h2(i) = deflator("2016") * consume_char0(i,t,"vom") * 1000 ;

* total cost of h2 production activities ($ per metric ton)
cost_prod(i,v,r,t)$[h2(i)$valcap(i,v,r,t)] = h2_fuel_cost(i,v,r,t) + h2_vom(i,t) + h2_stor_tran(i,t) ;

* include VOM for DAC in cost_prod
cost_prod(i,v,r,t)$[dac(i)$valcap(i,v,r,t)] = consume_char0(i,t,"vom") ;


table gasquant_elec(cendiv,allt) "--Quads-- Natural gas consumption in the electricity sector"
$offlisting
$ondelim
$include inputs_case%ds%ng_demand_elec.csv
$offdelim
$onlisting
;

table gasquant_tot(cendiv,allt) "--Quads-- Total natural gas consumption"
$offlisting
$ondelim
$include inputs_case%ds%ng_demand_tot.csv
$offdelim
$onlisting
;

*need to convert from quadrillion btu to million btu
gassupply_ele(cendiv,t) = 1e9 * gasquant_elec(cendiv,t) ;
gassupply_tot(cendiv,t) = 1e9 * gasquant_tot(cendiv,t) ;


parameter
gassupply_ele_nat(t)       "--quads-- national reference gas supply for electricity " ,
gasprice_nat(t)            "--$/MMBtu-- national NG price",
gasquant_nat(t)            "--quads-- national NG usage",
gasquant_nat_bin(gb,t)     "--quads-- national NG quantity by bin",
gasprice_nat_bin(gb,t)     "--$/MMbtu-- price for each national NG bin",
gaslimit_nat(gb,t)         "--MMbtu-- national gas bin limit" ;

gassupply_ele_nat(t) = sum{cendiv$gassupply_ele(cendiv,t), gassupply_ele(cendiv,t) } ;

gasprice_nat(t) = sum{cendiv$gassupply_ele(cendiv,t), gassupply_ele(cendiv,t) * gasprice_ref(cendiv,t) }
                              / gassupply_ele_nat(t) ;

*now compute the amounts going into each gas bin
*this is computed as the amount relative to the reference amount based on the ordinal of the
*gas bin - e.g. gas bin 4 (with a central gas bin of 6 and bin width of 0.1)
*will be gassupply_ele * (1+4-6*0.1) = 0.8 * reference
gasquant(cendiv,gb,t)$gassupply_ele(cendiv,t) = gassupply_ele(cendiv,t) *
                          (1+(ord(gb)-(smax(gbb,ord(gbb)) / 2 + 0.5)) * 0.1) ;


gasquant_nat_bin(gb,t)$gassupply_ele_nat(t) = gassupply_ele_nat(t) *
                          (1+(ord(gb)-(smax(gbb,ord(gbb)) / 2 + 0.5)) * 0.1) ;


gasprice(cendiv,gb,t)$gassupply_ele(cendiv,t) =
          gas_scale * round(gasprice_ref(cendiv,t) *
               (
* numerator is the quantity in the bin
* [plus] all natural gas usage
* [minus] gas usage in the ele sector
                (gasquant(cendiv,gb,t) + gassupply_tot(cendiv,t) - gassupply_ele(cendiv,t))
                /(gassupply_tot(cendiv,t))
                ) ** (1 / gas_elasticity),4) ;


gasprice_nat_bin(gb,t)$sum{cendiv, gassupply_tot(cendiv,t) } =
          gas_scale * round(gasprice_nat(t) *
               (
                (gasquant_nat_bin(gb,t) + sum{cendiv, gassupply_tot(cendiv,t) } - gassupply_ele_nat(t))
                /(sum{cendiv, gassupply_tot(cendiv,t) })
                ) ** (1 / gas_elasticity),4) ;


*the quantity available in each bin is the quantity on the supply curve minus the previous bin's quantity supplied
gaslimit(cendiv,gb,t) = round((gasquant(cendiv,gb,t) - gasquant(cendiv,gb-1,t)),0) / gas_scale;


gaslimit(cendiv,"gb1",t) = gaslimit(cendiv,"gb1",t)
                            - gassupplyscale * sum{gb$[ord(gb)=(smax(gbb,ord(gbb)) / 2 + 0.5)],gaslimit(cendiv,gb,t) } ;

*final category gets a huge bonus so we make sure we do not run out of gas
gaslimit(cendiv,gb,t)$[ord(gb)=smax(gbb,ord(gbb))] = 5 * gaslimit(cendiv,gb,t) ;


gaslimit_nat(gb,t) = round((gasquant_nat_bin(gb,t) - gasquant_nat_bin(gb-1,t)),0) / gas_scale;

gaslimit_nat("gb1",t) = gaslimit_nat("gb1",t)
                            - gassupplyscale * sum{gb$[ord(gb)=(smax(gbb,ord(gbb)) / 2 + 0.5)],gaslimit_nat(gb,t) } ;

*final category gets a huge bonus so we make sure we do not run out of gas
gaslimit_nat(gb,t)$(ord(gb)=smax(gbb,ord(gbb))) = 5 * gaslimit_nat(gb,t) ;

*Penalizing new gas built within cost recovery period of 30 years for states that
* require fossil plants to retire in some future model period.
* This value is calculated as the ratio of CRF_X / CRF_30 where X is the number of
* years until the required retirement year.
$onempty
parameter ng_crf_penalty_st(allt,st) "--unitless-- cost adjustment for NG in states where all NG techs must be retired by a certain year"
/
$offlisting
$ondelim
$include inputs_case%ds%ng_crf_penalty_st.csv
$offdelim
$onlisting
/ ;
$offempty

parameter ng_carb_lifetime_cost_adjust(allt) "--unitless-- cost adjustment for NG with full-region zero-carbon policy"
/
$offlisting
$ondelim
$include inputs_case%ds%ng_crf_penalty.csv
$offdelim
$onlisting
/ ;

parameter ng_crf_penalty_nat(i,t) "--unitless-- cost adjustment for NG techs that must be retired by a certain year" ;
* Penalize new gas that can be upgraded to recover upgrade costs prior to upgrade within 20 years of a zero-carbon policy
ng_crf_penalty_nat(i,t)$[gas(i)$sum{r, valcap_irt(i,r,t) }] = ((ng_carb_lifetime_cost_adjust(t) - 1) * .2) + 1 ;
* Do not apply the penalty to CCS technologies
ng_crf_penalty_nat(i,t)$[gas(i)$ccs(i)$sum{r, valcap_irt(i,r,t) }] = 1 ;

*===========================================
* --- Regional Gas supply curve ---
*===========================================

set fuelbin "gas usage bracket"
/
$offlisting
$include inputs_case%ds%fuelbin.csv
$onlisting
/ ;

alias(fuelbin,afuelbin) ;

Scalar numfuelbins       "number of fuel bins",
       normfuelbinwidth  "typical fuel bin width",
       botfuelbinwidth   "bottom fuel bin width"
;

parameter cd_beta(cendiv,t)                      "--$/MMBtu per Quad-- beta value for census divisions' natural gas supply curves",
          nat_beta(t)                            "--$/MMBtu per Quad-- beta value for national natural gas supply curves",
          gasbinwidth_regional(fuelbin,cendiv,t) "--MMBtu-- census division's gas bin width",
          gasbinwidth_national(fuelbin,t)        "--MMBtu-- national gas bin width",
          gasbinp_regional(fuelbin,cendiv,t)     "--$/MMBtu-- price for each gas bin",
          gasusage_national(t)                   "--MMBtu-- reference national gas usage",
          gasbinqq_regional(fuelbin,cendiv,t)    "--MMBtu-- regional reference level for supply curve calculation of each gas bin",
          gasbinqq_national(fuelbin,t)           "--MMBtu-- national reference level for supply curve calculation of each gas bin",
          gasbinp_national(fuelbin,t)            "--$/MMBtu--price for each national gas bin",
          gasmultterm(cendiv,t)                  "parameter to be multiplied by total gas usage to compute the reference costs of gas consumption, from which the bins deviate" ;

*note these do not change over years, only exception
* is that the value in the first year is set to zero
parameter cd_beta0(cendiv) "--$/MMBtu per Quad-- reference census division beta levels electric sector"
/
$offlisting
$ondelim
$include inputs_case%ds%cd_beta0.csv
$offdelim
$onlisting
/ ;

parameter cd_beta0_allsector(cendiv) "--$/MMBtu per Quad-- reference census division beta levels all sectors"
/
$offlisting
$ondelim
$include inputs_case%ds%cd_beta0_allsector.csv
$offdelim
$onlisting
/ ;

$ifthen.gassector %GSw_GasSector% == 'energy_sector'

*beginning year value is zero (i.e., no elasticity)
cd_beta(cendiv,t)$[not tfirst(t)] = cd_beta0_allsector(cendiv) ;

nat_beta(t)$(not tfirst(t)) = nat_beta_energy ;

$else.gassector

*beginning year value is zero (i.e., no elasticity)
cd_beta(cendiv,t)$[not tfirst(t)] = cd_beta0(cendiv) ;

*see documentation for how value is calculated
nat_beta(t)$(not tfirst(t)) =  nat_beta_nonenergy ;

$endif.gassector

* Written by input_processing\fuelcostprep.py
* declared over allt to allow for external data files that extend beyond end_year
table cd_alpha(allt,cendiv) "--$/MMBtu-- alpha value for natural gas supply curves"
$offlisting
$ondelim
$include inputs_case%ds%alpha.csv
$offdelim
$onlisting
;

table cendiv_weights(r,cendiv) "--unitless-- weights to smooth gas prices between census regions to avoid abrupt price changes at the cendiv borders"
$offlisting
$ondelim
$include inputs_case%ds%cendivweights.csv
$offdelim
$onlisting
;


*number of fuel bins is just the sum of fuel bins
numfuelbins = sum{fuelbin, 1} ;

*note we subtract two here because top and bottom bins are not included
normfuelbinwidth = (normfuelbinmax - normfuelbinmin)/(numfuelbins - 2) ;

*set the bottom fuel bin width
botfuelbinwidth = normfuelbinmin ;

*national gas usage computed as sum over census divisions' gas usage
gasusage_national(t) = sum{cendiv, gassupply_ele(cendiv,t) } ;

*gas bin width is typically the reference gas usage times the bin width
gasbinwidth_regional(fuelbin,cendiv,t) = gassupply_ele(cendiv,t) * normfuelbinwidth ;

*bottom and top bins get special treatment
*in that they are expanded by botfuelbinwidth and topfuelbinwidth
gasbinwidth_regional(fuelbin,cendiv,t)$[ord(fuelbin) = 1] = gassupply_ele(cendiv,t) * botfuelbinwidth ;
gasbinwidth_regional(fuelbin,cendiv,t)$[ord(fuelbin) = smax(afuelbin,ord(afuelbin))] =
                                          gassupply_ele(cendiv,t) * topfuelbinwidth ;

*don't want any super small or zero values -- this follows the same calculations in heritage ReEDS
gasbinwidth_regional(fuelbin,cendiv,t)$[gasbinwidth_regional(fuelbin,cendiv,t) < 10] = 10 ;

*gas bin widths are defined similarly on the national level
gasbinwidth_national(fuelbin,t) = gasusage_national(t) * normfuelbinwidth ;
gasbinwidth_national(fuelbin,t)$[ord(fuelbin) = 1]   = gasusage_national(t) * botfuelbinwidth ;
gasbinwidth_national(fuelbin,t)$[ord(fuelbin)=smax(afuelbin,ord(afuelbin))]  = gasusage_national(t) * topfuelbinwidth ;

*comment from heritage reeds:
*gasbinqq is the centerpoint of each of the smaller bins and is used to determine the price of each bin. The first and last bin have
*gasbinqqs that are just one more step before and after the smaller bins.
gasbinqq_regional(fuelbin,cendiv,t) =
   gassupply_ele(cendiv,t)  * (normfuelbinmin
    + (ord(fuelbin) - 1)*normfuelbinwidth - normfuelbinwidth / 2) ;

gasbinqq_national(fuelbin,t) =  gasusage_national(t)  * (normfuelbinmin + (ord(fuelbin) - 1)*normfuelbinwidth - normfuelbinwidth / 2) ;

*bins' prices are those from the supply curves
*1e9 converts from MMBtu to Quads
gasbinp_regional(fuelbin,cendiv,t) =
   round((cd_beta(cendiv,t) * (gasbinqq_regional(fuelbin,cendiv,t) -  gassupply_ele(cendiv,t))) / 1e9,5) ;

gasbinp_national(fuelbin,t)= round(nat_beta(t)*(gasbinqq_national(fuelbin,t) - gasusage_national(t)) / 1e9,5) ;


*this is the reference price of gas given last year's gas usage levels
gasmultterm(cendiv,t) = (cd_alpha(t,cendiv)
                     + nat_beta(t) * gasusage_national(t-2) / 1e9
                     + cd_beta(cendiv,t) * gassupply_ele(cendiv,t-2) / 1e9
                        ) ;



*=================================
*       ---- Storage ----
*=================================

* --- Storage Efficiency ---

parameter storage_eff(i,t) "--fraction-- round-trip efficiency of storage technologies" ;

storage_eff(i,t)$storage(i) = 1 ;
storage_eff(i,t)$psh(i) = storage_eff_psh ;
storage_eff("ICE",t) = 1 ;
storage_eff(i,t)$[storage(i)$plant_char0(i,t,'rte')] = plant_char0(i,t,'rte') ;
storage_eff(i,t)$[evmc_storage(i)$plant_char0(i,t,'rte')] = plant_char0(i,t,'rte') ;
storage_eff(i,t)$pvb(i) = storage_eff("battery_li",t) ;

parameter storage_eff_pvb_p(i,t) "--fraction-- efficiency of hybrid PV+battery when charging from the coupled PV"
          storage_eff_pvb_g(i,t) "--fraction-- efficiency of hybrid PV+battery when charging from the grid" ;

*when charging from PV the pvb system will have a higher efficiency due to one less inverter conversion
storage_eff_pvb_p(i,t)$pvb(i) = storage_eff(i,t) / inverter_efficiency ;
*when charging from the grid the efficiency will be the same as standalone storage
storage_eff_pvb_g(i,t)$pvb(i) = storage_eff("battery_li",t) ;

*upgrade plants assume the same as what theyre upgraded to
storage_eff(i,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), storage_eff(ii,t) } ;

* --- Storage Input Capacity ---

parameter minstorfrac(i,v,r) "--fraction-- minimum storage_in as a fraction of total input capacity";
minstorfrac(i,v,r)$[valcap_ivr(i,v,r)$psh(i)] = %GSw_HydroStorInMinLoad% ;
* Expand for water technologies
minstorfrac(i,v,r)$[i_water_cooling(i)$valcap_ivr(i,v,r)$psh(i)$Sw_WaterMain]
  = sum{ii$ctt_i_ii(i,ii), minstorfrac(ii,v,r) } ;

parameter storinmaxfrac(i,v,r)  "--fraction-- max storage input capacity as a fraction of output capacity" ;

$onempty
parameter storinmaxfrac_data(i,v,r) "--fraction-- data for max storage input capacity as a fraction of capacity if data is available"
/
$offlisting
$ondelim
$include inputs_case%ds%storinmaxfrac.csv
$offdelim
$onlisting
/ ;
$offempty

$ifthen.storcap %GSw_HydroStorInMaxFrac% == "data"
* Use data file for available PSH data
storinmaxfrac(i,v,r)$[valcap_ivr(i,v,r)$psh(i)] = storinmaxfrac_data(i,v,r) ;
$else.storcap
* Use numerical value from case file for PSH only
storinmaxfrac(i,v,r)$[valcap_ivr(i,v,r)$psh(i)] = %GSw_HydroStorInMaxFrac% ;
$endif.storcap
* Fill any gaps with values of 1
storinmaxfrac(i,v,r)$[(storage_standalone(i) or hyd_add_pump(i))$(not storinmaxfrac(i,v,r))$valcap_ivr(i,v,r)] = 1 ;

* --- Hybrid PV+Battery ---

table pvbcapmult(allt,pvb_config) "PV+Battery capital cost multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%pvbcapcostmult.csv
$offdelim
$onlisting
;

* the capital cost for PVB includes both the PV and battery portions
* total cost = cost(PV) * cap(PV) + cost(B) * cap(B)
*            = cost(PV) * cap(PV) + cost(B) * bcr * cap(PV)
*            = [cost(PV) + cost(B) * bcr ] * cap(PV)
cost_cap(i,t)$pvb(i) = (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) * sum{pvb_config$pvb_agg(pvb_config,i), pvbcapmult(t,pvb_config) } ;

scalar pvb_itc_qual_frac "--fraction-- fraction of energy that must be charged from local PV for hybrid PV+battery" ;
pvb_itc_qual_frac = %GSw_PVB_Charge_Constraint% ;

* --- CSP with storage ---

* used in eq_rsc_INVlim
* csp: this include the SM for representative configurations, divided by the representative SM (2.4) for CSP supply curve;
* all other technologies are 1
parameter
  csp_sm(i) "--unitless-- solar multiple for configurations"
  resourcescaler(i) "--unitless-- resource scaler for rsc technologies"
;

csp_sm(i)$csp1(i) = csp_sm_1 ;
csp_sm(i)$csp2(i) = csp_sm_2 ;
csp_sm(i)$csp3(i) = csp_sm_3 ;
csp_sm(i)$csp4(i) = csp_sm_4 ;

resourcescaler(i)$[(not CSP_Storage(i))$(not ban(i))] = 1 ;
resourcescaler(i)$csp(i) = CSP_SM(i) / csp_sm_baseline ;

* --- Storage Duration ---

* For PSH, tech-specific storage duration sets a default value.
*   Then when when GSw_HydroPSHDurData = 1,
*   region- and vintage-specific durations are defined where data exists.
parameter storage_duration(i)   "--hours-- storage duration by tech"
/
$offlisting
$ondelim
$include inputs_case%ds%storage_duration.csv
$offdelim
$onlisting
/ ;

$onempty
scalar psh_sc_duration "--hours-- PSH storage duration corresponding to selected supply curve"
/
$offlisting
$ifthene.readpshscduration %GSw_Storage%<>0
$include inputs_case%ds%psh_sc_duration.csv
$endif.readpshscduration
$onlisting
/ ;
$offempty

* Note that this PSH duration overwrites what is contained in storage_duration.csv
storage_duration(i)$psh(i) = psh_sc_duration ;

storage_duration(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), storage_duration(ii) } ;

storage_duration(i)$pvb(i) = %GSw_PVB_Dur% ;

*upgrade plants assume the same as what they're upgraded to
storage_duration(i)$upgrade(i) = sum{ii$upgrade_to(i,ii),storage_duration(ii) } ;

parameter storage_duration_m(i,v,r)   "--hours-- storage duration by tech, vintage, and region"
          cc_storage(i,sdbin)         "--fraction-- capacity credit of storage by duration"
          bin_duration(sdbin)         "--hours-- duration of each storage duration bin"
          bin_penalty(sdbin)          "--$-- penalty to incentivize solve to fill the shorter duration bins first"
;
$onempty
parameter storage_duration_pshdata(i,v,r) "--hours-- storage duration data for PSH"
/
$offlisting
$ondelim
$include inputs_case%ds%storage_duration_pshdata.csv
$offdelim
$onlisting
/ ;
$offempty

* Initialize using generic tech-specific duration
storage_duration_m(i,v,r)$[storage_duration(i)$valcap_ivr(i,v,r)] = storage_duration(i) ;
* Overwrite storage duration for existing PSH capacity when using datafile
$ifthen %GSw_HydroPSHDurData% == 1
storage_duration_m(i,v,r)$[storage_duration_pshdata(i,v,r)$psh(i)$valcap_ivr(i,v,r)] = storage_duration_pshdata(i,v,r) ;
$endif

* set the duration of each storage duration bin
bin_duration(sdbin) = sdbin.val ;

* set the capacity credit of each storage technology for each storage duration bin.
* for example, 2-hour batteries get CC=1 for the 2-hour bin and CC=0.5 for the 4-hour bin
* likewise, 6-hour batteries get CC=1 for the 2-, 4-, and 6-hour bins, but only 0.75 for the 8-hour bin, etc.
* For capacity credit, CSP is treated like VRE rather than storage
cc_storage(i,sdbin)$[(not ban(i))$(not csp(i))] = storage_duration(i) / bin_duration(sdbin) ;
cc_storage(i,sdbin)$(cc_storage(i,sdbin) > 1) = 1 ;

* for battery, the capacity credit for each bin is always 1,
* since the duration of continuous battery will be automatically greater than the sdbin duration.
cc_storage(i,sdbin)$(battery(i)) = 1 ;

* The 8760 bin is included as a safety valve so that the model can build additional storage
* beyond what is available for diurnal peaking capacity
cc_storage(i,'8760') = 0 ;

bin_penalty(sdbin) = 0 ;
bin_penalty(sdbin)$Sw_StorageBinPenalty = 1e-5 * (ord(sdbin) - 1) ;

*upgrade plants assume the same as what they're upgraded to
cc_storage(i,sdbin)$upgrade(i) = sum{ii$upgrade_to(i,ii), cc_storage(ii,sdbin) } ;

* --- storage fixed OM cost ---

*fom and vom costs are constant for pumped-hydro
*values are taken from ATB
cost_fom(i,v,r,t)$[psh(i)$valcap(i,v,r,t)] = cost_fom_psh ;
cost_vom(i,v,r,t)$[psh(i)$valcap(i,v,r,t)] = cost_vom_psh ;

* Apply a minimum VOM cost for storage (to avoid degeneracy with curtailment)
* Only apply the value to storage that does not have a VOM value
cost_vom(i,v,r,t)$[storage(i)$valgen(i,v,r,t)$(not cost_vom(i,v,r,t))] = storage_vom_min ;

* declared over allt to allow for external data files that extend beyond end_year
parameter ice_fom(allt) "--$/MW-year -- Fixed O&M costs for ice storage"
/
$offlisting
$ondelim
$include inputs_case%ds%ice_fom.csv
$offdelim
$onlisting
/ ;

cost_fom("ICE",v,r,t)$valcap("ICE",v,r,t) = ice_fom(t) ;

* --- minimum capacity factor ----
parameter minCF(i,t)      "--fraction-- minimum annual capacity factor for each tech fleet, applied to (i,r)"
          maxdailycf(i,t) "--fraction-- maximum daily capacity factor" ;

* 6% for H2-CT and H2-CC is based on unpublished PLEXOS runs of 100% RE scenarios performed in summer 2019
parameter minCF_input(i) "--fraction-- minimum annual capacity factor for each tech fleet, applied to (i,r)"
/
$offlisting
$ondelim
$include inputs_case%ds%minCF.csv
$offdelim
$onlisting
/ ;
minCF(i,t) = minCF_input(i) ;
minCF(i,t)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), minCF(ii,t) } ;
minCF(i,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), minCF(ii,t) } ;

* adjust fleet mincf for nuclear when using flexible nuclear
minCF(i,t)$[nuclear(i)$Sw_NukeFlex] = minCF_nuclear_flex ;

parameter maxdailycf_input(i) "--fraction-- maximum daily capacity factor for a technology"
/
$offlisting
$ondelim
$include inputs_case%ds%maxdailycf.csv
$offdelim
$onlisting
/ ;

maxdailycf(i,t) = maxdailycf_input(i) ;
maxdailycf(i,t)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), maxdailycf(ii,t) } ;
maxdailycf(i,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), maxdailycf(ii,t) } ;

*=================================
*       ---- Upgrades ----
*=================================
*The last instance of cost_cap has already occurred, so now assign upgrade costs

*costs for upgrading are the difference in capital costs
*between the initial techs and the tech to which the unit is upgraded
cost_upgrade(i,v,r,t)$[upgrade(i)$valcap(i,v,r,t)] = sum{ii$upgrade_to(i,ii), cost_cap(ii,t) }
                               - sum{ii$upgrade_from(i,ii), cost_cap(ii,t) } ;

*increase cost_upgrade by 1% to prevent building and upgrading in the same year
*(otherwise there is a degeneracy between building new and building+upgrading in the same year)
cost_upgrade(i,v,r,t)$[upgrade(i)$valcap(i,v,r,t)] = cost_upgrade(i,v,r,t) * 1.01 ;

*Sets upgrade costs for H2-CT and H2-CC plants based relative to capital cost for H2-CT
*this is done because upgrade costs are higher than new build costs
cost_upgrade('Gas-CT_H2-CT',v,r,t)$[valcap('Gas-CT_H2-CT',v,r,t)] =
  cost_cap('gas-ct',t) * cost_upgrade_gasct2h2ct ;

*(The set of filters on cost_upgrades yields "Gas-CC_H2-CC", but does so in a way to capture
*water techs when the water switch is turned on)
cost_upgrade(i,v,r,t)$[h2_combustion(i)$upgrade(i)$(not ccs(i))$valcap(i,v,r,t)
                      $sum{ii$gas_cc(ii), upgrade_from(i,ii) }] = 
  cost_cap('gas-cc',t) * cost_upgrade_gascc2h2cc ;

*Override any upgrade costs computed above with exogenously specified retrofit costs
cost_upgrade(i,v,r,t)$[upgrade(i)$plant_char0(i,t,"upgradecost")$valcap(i,v,r,t)]
  = plant_char0(i,t,"upgradecost") ;

*the coal-CCS input from ATB 2021 and on is for a pulverized coal plant
*assume that the upgrade cost for coal-IGCC_coal-CCS is the same as for
*coal-new_coal-CCS
cost_upgrade('coal-IGCC_coal-CCS_mod',v,r,t)$valcap('coal-IGCC_coal-CCS_mod',v,r,t) =
  cost_upgrade('coal-new_coal-CCS_mod',v,r,t) ;

cost_upgrade('coal-IGCC_coal-CCS_max',v,r,t)$valcap('coal-IGCC_coal-CCS_max',v,r,t) =
  cost_upgrade('coal-new_coal-CCS_max',v,r,t) ;

* Assign upgrade costs for hydro technology upgrades using values from cases file
cost_upgrade('hydEND_hydED',v,r,t)$valcap('hydEND_hydED',v,r,t) = %GSw_HydroCostAddDispatch% ;
cost_upgrade('hydED_pumped-hydro',v,r,t)$valcap('hydED_pumped-hydro',v,r,t) = %GSw_HydroCostAddPump% ;
cost_upgrade('hydED_pumped-hydro-flex',v,r,t)$valcap('hydED_pumped-hydro-flex',v,r,t) = %GSw_HydroCostAddPump% ;

parameter ccs_upgrade_costs_coal(allt) "--$2004/kW-- CCS upgrade costs for coal techs"
/
$offlisting
$ondelim
$include inputs_case/upgrade_costs_ccs_coal.csv
$offdelim
$onlisting
/ ;

parameter ccs_upgrade_costs_gas(allt) "--$2004/kW-- CCS upgrade costs for gas techs"
/
$offlisting
$ondelim
$include inputs_case/upgrade_costs_ccs_gas.csv
$offdelim
$onlisting
/ ;

* update ccs retrofit costs with conversion from kw to mw
* based on selected ccs upgrade cost case
cost_upgrade(i,v,r,t)$[upgrade(i)$coal_ccs(i)$valcap(i,v,r,t)] = 1e3 * ccs_upgrade_costs_coal(t) ;
cost_upgrade(i,v,r,t)$[upgrade(i)$gas_cc_ccs(i)$valcap(i,v,r,t)] = 1e3 * ccs_upgrade_costs_gas(t) ;

* if specified, use the overnight retrofit
* costs specified in the EIA unit database
cost_upgrade(i,v,r,t)$[initv(v)$hintage_data(i,v,r,t,"wCCS_Retro_OvernightCost")$valcap(i,v,r,t)] =
* conversion from $ / kw to $ / mw
  upgrade_inflator * 1e3 * hintage_data(i,v,r,t,"wCCS_Retro_OvernightCost") ;

* set floor on the cost of an upgrade to prevent negative upgrade costs
cost_upgrade(i,v,r,t)$[valcap(i,v,r,t)$upgrade(i)] = max{0, cost_upgrade(i,v,r,t) } ;


*=============================================================
* ---------- Cost Adjustment for cost_upgrade Techs 
*=============================================================
table upgrade_mult(i,allt) "--fraction-- cost adjustment for cost_upgrade techs"
$offlisting
$ondelim
$include inputs_case%ds%upgrade_mult_final.csv
$offdelim
$onlisting
;

upgrade_mult(i,t)$[sum{ii$ctt_i_ii(i,ii), upgrade_mult(ii,t) }$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), upgrade_mult(ii,t) } ;

cost_upgrade(i,v,r,t)$[initv(v)$valcap(i,v,r,t)$sum{ii$upgrade_from(i,ii),cost_upgrade(ii,v,r,t) }$unitspec_upgrades(i)$(not Sw_UpgradeATBCosts)] = 
      upgrade_mult(i,t) * sum{ii$upgrade_from(i,ii),cost_upgrade(ii,v,r,t) } ;

* start with specifying upgrade_derate as zero
upgrade_derate(i,v,r,t) = 0 ;

upgrade_derate(i,initv,r,t)$[upgrade(i)$ccs(i)$unitspec_upgrades(i)$valcap(i,initv,r,t)
                            $sum{ii$upgrade_from(i,ii),hintage_data(ii,initv,r,t,"wCCS_Retro_HR") }] =
* following calculation is from NEMS/EIA - stating the derate is 1 - [the original heat_rate] / [new heat rate]
* take the max of it and zero
  max(0,1 - sum{ii$upgrade_from(i,ii), hintage_data(ii,initv,r,t,"wHR") / hintage_data(ii,initv,r,t,"wCCS_Retro_HR") });

* set upgrade derate for new plants and existing plants without data
* to the average across all values from NETL CCRD:
* https://www.osti.gov/servlets/purl/1887588
upgrade_derate(i,initv,r,t)$[upgrade(i)$ccs(i)$coal(i)
                            $(not upgrade_derate(i,initv,r,t))
                            $valcap(i,initv,r,t)] = 0.29 ;

upgrade_derate(i,initv,r,t)$[upgrade(i)$ccs(i)$gas(i)
                            $(not upgrade_derate(i,initv,r,t))
                            $valcap(i,initv,r,t)] = 0.14 ;

* same assumptions for new plants
upgrade_derate(i,newv,r,t)$[upgrade(i)$ccs(i)$coal(i)$valcap(i,newv,r,t)] = 0.29 ;
upgrade_derate(i,newv,r,t)$[upgrade(i)$ccs(i)$gas(i)$valcap(i,newv,r,t)] = 0.14 ;

* If a technology is not retired, its upgrade_derate value is zero.
upgrade_derate(i,v,r,t)$[upgrade(i)$(not noret_upgrade_tech(i))] = 0 ;

if((not Sw_UpgradeDerate),
 upgrade_derate(i,v,r,t) = 0
) ;


*==============================
* --- BIOMASS SUPPLY CURVES ---
*==============================

* supply curves defined by 21 price increments
set bioclass
/
$offlisting
$include inputs_case%ds%bioclass.csv
$onlisting
/ ;

set biofeas(r) "regions with biomass supply and biopower";

* supply curve derived from 2016 ORNL Billion Ton study
* annual supply of woody biomass available to the power sector (in million dry tons)
* by USDA region at price P (2015$ per dry ton)
table biosupply(usda_region,bioclass,*) "biomass supply (million dry tons) and biomass cost ($/dry ton)"
$offlisting
$ondelim
$include inputs_case%ds%bio_supplycurve.csv
$offdelim
$onlisting
;

* convert biomass supply from million dry tons to MMBtu
* assuming 13 MMBtu per dry ton based on 2016 ORNL Billion Ton Study
scalar bio_energy_content "MMBtu per dry ton of biomass" / 13 / ;
biosupply(usda_region,bioclass,"cap") = biosupply(usda_region, bioclass,"cap") * 1E6 * bio_energy_content ;

* multiplier for total biomass supply, set by user via input switch (default is 1)
biosupply(usda_region,bioclass,"cap") = biosupply(usda_region,bioclass,"cap") * Sw_BioSupply ;

* convert price into $ per MMBtu
* input price ($/ton) / (MMBtu/ton) = $/MMBtu
biosupply(usda_region,bioclass,"price") = biosupply(usda_region, bioclass,"price") / bio_energy_content ;

* regions with biomass supply
biofeas(r)$[sum{bioclass, sum{usda_region$r_usda(r, usda_region), biosupply(usda_region,bioclass,"cap") } } ] = yes ;

*removal of bio techs that are not in biofeas(r)
valcap(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;
valgen(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;
valinv(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;

valgen(i,v,r,t)$[not valcap(i,v,r,t)] = no ;
valinv(i,v,r,t)$[not valcap(i,v,r,t)] = no ;

scalar bio_transport_cost ;
* biomass transport cost enter in $ per ton, convert to $ per MMBtu
bio_transport_cost = Sw_BioTransportCost / bio_energy_content ;

* get price of cheapest supply curve bin that has resources (needed for Augur)
* price includes any transport costs for biomass
parameter rep_bio_price_unused(r) "--2004$/MWh-- marginal price of lowest cost available supply curve bin for biofuel" ;
rep_bio_price_unused(r)$[sum{usda_region, 1$r_usda(r,usda_region) }] =
    smin{bioclass$[sum{usda_region$r_usda(r, usda_region), biosupply(usda_region,bioclass,"cap") }],
        sum{usda_region$r_usda(r, usda_region), biosupply(usda_region,bioclass,"price") } } + bio_transport_cost ;

parameter cost_curt(t) "--$/MWh-- price paid for curtailed VRE" ;

cost_curt(t)$[yeart(t)>=model_builds_start_yr] = Sw_CurtMarket ;

*======================
* Emissions cap and tax
*======================

parameter emit_cap(eall,t)    "--metric tons per year-- annual CO2 emissions cap",
          yearweight(t)       "--unitless-- weights applied to each solve year for the banking and borrowing cap - updated in d_solveprep.gms",
          emit_tax(e,r,t)     "--$ per metric ton-- tax applied to emissions" ;

emit_cap(e,t) = 0 ;
emit_tax(e,r,t) = 0 ;

yearweight(t) = 0 ;
yearweight(t)$tmodel_new(t) = sum{tt$tprev(tt,t), yeart(tt) } - yeart(t) ;
yearweight(t)$tlast(t) = 1 + smax{yearafter, yearafter.val } ;

* declared over allt to allow for external data files that extend beyond end_year
parameter co2_cap(allt)      "--metric tons-- CO2 emissions cap used when Sw_AnnualCap is on"
/
$offlisting
$ondelim
$include inputs_case%ds%co2_cap.csv
$offdelim
$onlisting
/ ;
if(Sw_AnnualCap = 1,
    emit_cap("CO2",t) = co2_cap(t) ;
) ;

if(Sw_AnnualCap > 1,
    emit_cap("CO2e",t) = co2_cap(t) ;
) ;

parameter co2_tax(allt)      "--$/metric ton-- CO2 tax used when Sw_CarbTax is on"
/
$offlisting
$ondelim
$include inputs_case%ds%co2_tax.csv
$offdelim
$onlisting
/ ;


* set the carbon tax based on switch arguments
if(Sw_CarbTax = 1,
emit_tax("CO2",r,t) = co2_tax(t) ;
) ;

* All emissions are included in reported, but not all emissions need to be modeled
* This set captures only the emissions that need to be included in the model
set emit_modeled(e,r,t) "set of emissions that are necessary to include in the model" ;

* CO2 for RGGI regions and years
emit_modeled("CO2",r,t)$[
  (yeart(t)>=RGGI_start_yr)
  $RGGI_r(r)
  $Sw_RGGI] = yes ;

* CO2 for state cap regions and years
emit_modeled("CO2",r,t)$[
  (yeart(t)>=state_cap_start_yr)
  $sum{(tt,st)$r_st(r,st), state_cap(st,tt) }
  $Sw_StateCap] = yes ;

* Emissions with an emission rate limit constraint
emit_modeled(e,r,t)$emit_rate_con(e,r,t) = yes ;

* Model all emissions with global warming potential
emit_modeled(e,r,t)$gwp(e) = yes ;

* Emissions associated with bankbarrowcap
emit_modeled(e,r,t)$[
  Sw_BankBorrowCap
  $sum{tt, emit_cap(e,tt) }] = yes ;

* Emissions subject to an emissions tax
emit_modeled(e,r,t)$emit_tax(e,r,t) = yes ;

* Remove years not modeled
emit_modeled(e,r,t)$[not tmodel_new(t)] = no ;

* Set of emissions that are being capped
set emit_capped(e) "set of emissions that are included in emission cap depending on Sw_AnnualCap setting" ;
emit_capped(e)$[Sw_AnnualCap=0] = no ;
emit_capped("CO2")$[Sw_AnnualCap=1] = yes ;
emit_capped(e)$[gwp(e)$(not sameas(e, "H2"))$(Sw_AnnualCap=2)] = yes ;
emit_capped(e)$[gwp(e)$(Sw_AnnualCap=3)] = yes ;

*====================================
* --- Endogenous Retirements ---
*====================================

set valret(i,v) "technologies and classes that can be retired" ;

set noretire(i) "technologies that will never be retired"
/
$offlisting
$ondelim
$include inputs_case%ds%noretire.csv
$offdelim
$onlisting
/ ;

* storage technologies are not appropriately attributing capacity value to CAP variable
* therefore not allowing them to endogenously retire
noretire(i)$[(storage_standalone(i) or hyd_add_pump(i))] = yes ;

*all existings plants of any technology can be retired if Sw_Retire = 1
valret(i,v)$[(Sw_Retire=1)$initv(v)$(not noretire(i))] = yes ;

*only existing coal and gas are retirable if Sw_Retire = 2
valret(i,v)$[(Sw_Retire=2)$initv(v)$(not noretire(i))
            $(coal(i) or gas(i) or ogs(i))] = yes ;

*All new and existing nuclear, coal, gas, and hydrogen are retirable if Sw_Retire = 3
*Existing plants have to meet the min_retire_age before retiring
valret(i,v)$[((Sw_Retire=3) or (Sw_Retire=5))$(not noretire(i))
            $(coal(i) or gas(i) or nuclear(i) or ogs(i) or h2_combustion(i) or h2(i))] = yes ;

*new and existings plants of any technology can be retired if Sw_Retire = 4
valret(i,v)$[(Sw_Retire=4)$(not noretire(i))] = yes ;

retiretech(i,v,r,t)$[valret(i,v)$valcap(i,v,r,t)] = yes ;

* when Sw_Retire = 3 ensure that plants do not retire before their minimum age
retiretech(i,v,r,t)$[((Sw_Retire=3) or (Sw_Retire=5))$initv(v)$(not noretire(i))$(plant_age(i,v,r,t) <= min_retire_age(i))
                    $(coal(i) or gas(i) or nuclear(i) or ogs(i) or h2_combustion(i) or h2(i))] = no ;

* for sw_retire=5, don't allow nuclear to retire until 2030
retiretech(i,v,r,t)$[(Sw_Retire=5)$nuclear(i)$(yeart(t)<=2030)] = no ;

*several states have subsidies for nuclear power, so do not allow nuclear to retire in these states
*before the year specified (see https://www.eia.gov/todayinenergy/detail.php?id=41534)
*Note that Ohio has since repealed their nuclear subsidy, so is no longer included
$onempty
parameter nuclear_subsidies(st) '--year-- the year a nuclear subsidy ends in a given state'
/
$offlisting
$ondelim
$include inputs_case%ds%nuclear_subsidies.csv
$offdelim
$onlisting
/
;
$offempty

retiretech(i,initv,r,t)$[(yeart(t) < sum{st$r_st(r,st), nuclear_subsidies(st) })$valcap(i,initv,r,t)$nuclear(i)] = no ;

* if Sw_NukeNoRetire is enabled, don't allow nuclear to retire through Sw_NukeNoRetireYear
if(Sw_NukeNoRetire = 1,
         retiretech(i,v,r,t)$[nuclear(i)$(yeart(t)<=Sw_NukeNoRetireYear)] = no ;
) ;


*Do not allow retirements before they are allowed
retiretech(i,v,r,t)$[(yeart(t)<Sw_Retireyear)] = no ;

*Need to enable endogenous retirements for plants that can have persistent upgrades
retiretech(i,v,r,t)$[(yeart(t)>=Sw_Upgradeyear)$(yeart(t)>=Sw_Retireyear)$(Sw_Upgrades = 2)
                     $sum{ii$[upgrade_from(ii,i)$valcap(ii,v,r,t)], 1 }] = yes ;

*=========================================
* BEGIN MODEL SPECIFIC PARAMETER CREATION
*=========================================

parameter m_rsc_dat(r,i,rscbin,sc_cat)     "--MW or $/MW-- resource supply curve attributes" ;

m_rsc_dat(r,i,rscbin,sc_cat)
    $[sum{(ii,t)$[rsc_agg(i,ii)$tmodel_new(t)], valcap_irt(ii,r,t) }]
    = rsc_dat(i,r,sc_cat,rscbin) ;

parameter m_rsc_dat_original(r,i,rscbin,sc_cat) "--MW or $/MW-- resource supply curve attributes before any adjustments" ;
*m_rsc_dat_original is used to compare the magnitude of possible adjustments in supply curves. 
*It is only used for model validation and debugging purposes. 
m_rsc_dat_original(r,i,rscbin,sc_cat) = m_rsc_dat(r,i,rscbin,sc_cat) ;

*=========================================
* Reduced Resource Switch
*=========================================

parameter rsc_reduct_frac(pcat,r)   "--unitless-- fraction of renewable resource that is reduced from the supply curve"
          prescrip_rsc_frac(pcat,r) "--unitless-- fraction of prescribed builds to the resource available"
          rsc_capacity_scalar(i,r,t)    "--unitless-- resource scalar for any technology that has a change in the supply curve capacity over time"
;

set rsc_capacity_scalar_i(i) "technologies that have a capacity resource scalar" ;

rsc_reduct_frac(pcat,r) = 0 ;
prescrip_rsc_frac(pcat,r) = 0 ;
rsc_capacity_scalar(i,r,t) = 0 ;
rsc_capacity_scalar_i(i) = no ;

* if the Sw_ReducedResource is on, reduce the available resource by reduced_resource_frac
if (Sw_ReducedResource = 1,
*Calculate the fraction of prescribed builds to the available resource
* 2021-05-05 the prescriptions are being applied across all years until we decide a better way to do this
  prescrip_rsc_frac(pcat,r)$[sum{(i,rscbin)$prescriptivelink(pcat,i), m_rsc_dat(r,i,rscbin,"cap") } > 0] =
      smax(tt,m_required_prescriptions(pcat,r,tt)) / sum{(i,rscbin)$prescriptivelink(pcat,i), m_rsc_dat(r,i,rscbin,"cap") } ;
*Set the default resource reduction fraction
  rsc_reduct_frac(pcat,r) = reduced_resource_frac ;
*If the resource reduction fraction will reduce the resource to the point that prescribed builds will be infeasible,
*then replace the resource reduction fraction with the maximum that the resource can be reduced to still have a feasible solution
  rsc_reduct_frac(pcat,r)$[prescrip_rsc_frac(pcat,r) > (1 - rsc_reduct_frac(pcat,r))] = 1 - prescrip_rsc_frac(pcat,r) ;

*In order to avoid small number issues, round down at the 3rd decimal place
*Because the floor function returns an integer, we multiply and divide by 1000 to get proper rounding
  rsc_reduct_frac(pcat,r) = rsc_reduct_frac(pcat,r) * 1000 ;
  rsc_reduct_frac(pcat,r) = floor(rsc_reduct_frac(pcat,r)) ;
  rsc_reduct_frac(pcat,r) = rsc_reduct_frac(pcat,r) / 1000 ;

*Now reduce the resource by the updated resource reduction fraction
*(only do this for hydro, geothermal, PSH, and CSP; PV and wind have limited resource supply curves)
  m_rsc_dat(r,i,rscbin,"cap")$[rsc_i(i)$(csp(i) or hydro(i) or psh(i) or geo(i))] =
          m_rsc_dat(r,i,rscbin,"cap") * (1 - sum{pcat$prescriptivelink(pcat,i), rsc_reduct_frac(pcat,r) }) ;
) ;

*Currently only geothermal and dr_shed have supply curve capacities that change over time
rsc_capacity_scalar(i,r,t) = geo_discovery(i,r,t) + dr_shed_capacity_scalar(i,r,t) ;
rsc_capacity_scalar_i(i)$[sum{(r,t), rsc_capacity_scalar(i,r,t) }] = yes ;

*convert UPV and PVB interconnection costs from $/MW-AC to $/MW-DC using ILR
m_rsc_dat(r,i,rscbin,"cost")$[m_rsc_dat(r,i,rscbin,"cap")$(upv(i) or pvb(i))] = m_rsc_dat(r,i,rscbin,"cost") / ilr(i) ; 

*Fill in cost_trans for outputs.
m_rsc_dat(r,i,rscbin,"cost_trans")$[m_rsc_dat(r,i,rscbin,"cost")$[not sccapcosttech(i)]] =
    m_rsc_dat(r,i,rscbin,"cost") - m_rsc_dat(r,i,rscbin,"cost_cap") ;

*Ensure sufficient resource is available to cover existing capacity rsc_i capacity
m_rsc_dat(r,i,rscbin,"cap")$[rsc_i(i)
                            $(m_rsc_dat(r,i,rscbin,"cap") * (1$[not rsc_capacity_scalar_i(i)] + sum{t$tfirst(t), rsc_capacity_scalar(i,r,t) }$rsc_capacity_scalar_i(i))
                              < sum{(ii,v,tt)$[tfirst(tt)$rsc_agg(i,ii)$exog_rsc(i)], capacity_exog_rsc(ii,v,r,rscbin,tt) })] =
*Use ceiling function to three decimal places so that we don't run into infeasibilities due to rounding later on
  ceil(1000 * sum{(ii,v,tt)$[tfirst(tt)$rsc_agg(i,ii)$exog_rsc(i)], capacity_exog_rsc(ii,v,r,rscbin,tt)
      / (1$[not rsc_capacity_scalar_i(ii)] + rsc_capacity_scalar(ii,r,tt)$rsc_capacity_scalar_i(ii)) } ) / 1000 ;

*Ensure sufficient resource availability to cover prescribed builds
*while considering existing capacity (capacity_exog_rsc) 
*and prescribed capacity (noncumulative_prescriptions).

*Two types of adjustments:
*1- If at least one element of m_rsc_dat(r,i,rscbin,"cap") is nonzero within a technology group (pcat), 
*   apply a multiplier to all associated i-classes so that the total available capacity 
*   meets or exceeds prescribed capacity.
*2- If m_rsc_dat(r,i,rscbin,"cap") is zero for all i-classes within the technology group, 
*   but prescribed capacity exists, assign prescribed capacity to the first bin at zero cost.

*Define auxiliary parameters to organize the computation
parameter cap_existing(i,r)     "--MW-- amount of existing resource supply curve (rsc) capacity in each region"
          cap_prescribed(i,r)   "--MW-- amount of prescribed (required builds) rsc capacity in each region"
          available_supply(i,r) "--MW-- amount of available rsc supply in each region"
;

*Initialize the available supply to zero
available_supply(i,r) = 0 ;

*Get existing capacity
cap_existing(i,r)$exog_rsc(i) = sum{(v,t,rscbin)$[tfirst(t)], capacity_exog_rsc(i,v,r,rscbin,t) } ;

*Get prescribed capacity
cap_prescribed(i,r)$rsc_i(i) = sum{(pcat,t)$[(sameas(pcat,i) or prescriptivelink(pcat,i))
                                            $tmodel_new(t)], 
                                noncumulative_prescriptions(pcat,r,t) } ;

*Loop over all regions
loop(r,
*Loop over non-geothermal rsc technologies
  loop(i$[rsc_i(i)$sum{(v,t)$newv(v), valcap(i,v,r,t) }$(not prescriptivelink("geothermal",i))],

*Get total available supply for all ii associated with pcat of i.
*For example, if i = {upv_2}, then ii = {upv_2, upv_3, ...} and pcat = {UPV}.
    available_supply(i,r) = sum{(pcat,ii,rscbin)$[prescriptivelink(pcat,i)
                                                  $prescriptivelink(pcat,ii)], 
                              m_rsc_dat(r,ii,rscbin,"cap") } ;

*Apply multiplier if prescribed capacity exceeds available supply
    if ([((cap_existing(i,r) + cap_prescribed(i,r)) > available_supply(i,r))$(available_supply(i,r))],
        m_rsc_dat(r,ii,rscbin,"cap")$[sum{pcat$(prescriptivelink(pcat,i)$prescriptivelink(pcat,ii)), 1 }]
            = m_rsc_dat(r,ii,rscbin,"cap") * ((cap_existing(i,r) + cap_prescribed(i,r)) / available_supply(i,r)) ;
    ) ;

*Assign prescribed capacity to first bin at no cost if no supply is available
    if ([(cap_prescribed(i,r) > 0)$(not available_supply(i,r))] ,
      m_rsc_dat(r,i,"bin1","cap") = cap_prescribed(i,r) ;
    ) ;
  ) ; 
) ;

*Compute the difference between m_rsc_dat_original and m_rsc_dat
parameter rsc_cap_diff(r,i,rscbin) "--MW or $/MW-- total supply added to m_rsc_dat to adjust for prescriptions" ;
rsc_cap_diff(r,i,rscbin) = m_rsc_dat(r,i,rscbin,"cap") - m_rsc_dat_original(r,i,rscbin,"cap") ;

*Round up to the nearest 3rd decimal place
m_rsc_dat(r,i,rscbin,"cap")$m_rsc_dat(r,i,rscbin,"cap") = ceil(m_rsc_dat(r,i,rscbin,"cap") * 1000) / 1000 ;

*Geothermal is not a tech with sameas(i,pcat), so handle it separately here
*Loop over regions that have geothermal prescribed builds
loop(r$sum{(i,t)$[prescriptivelink("geothermal",i)$tmodel_new(t)], noncumulative_prescriptions("geothermal",r,t) },
*Then loop over eligible geothermal technologies
  loop(i$[prescriptivelink("geothermal",i)$sum{(v,t)$newv(v), valcap(i,v,r,t) }$geo_discovery(i,r,"%startyear%")],
*If capacity is insufficient, add enough capacity to make the model feasible
*Use the 2010 geothermal discovery (geo_discovery) rate for the calculation. That will slightly
*overestimate geothermal resource for any prescribed builds happening after the discovery rate
*begins to increase (currently after 2021)
    m_rsc_dat(r,i,"bin1","cap")$[((sum{(rscbin), m_rsc_dat(r,i,rscbin,"cap") } * (1$[not geo_hydro(i)] + geo_discovery(i,r,"%startyear%")$geo_hydro(i))) < sum{t$tmodel_new(t), noncumulative_prescriptions("geothermal",r,t) })
                                $(1$[not geo_hydro(i)] + geo_discovery(i,r,"%startyear%")$geo_hydro(i))] =
      (sum{t$tmodel_new(t), noncumulative_prescriptions("geothermal",r,t) }
       - sum{(rscbin), m_rsc_dat(r,i,rscbin,"cap") }
       + m_rsc_dat(r,i,"bin1","cap")
      ) / (1$[not geo_hydro(i)] + geo_discovery(i,r,"%startyear%")$geo_hydro(i)) ;
    break ;
  ) ;
) ;

* * Apply spur-line cost multiplier for relevant technologies
* m_rsc_dat(r,i,rscbin,"cost")$(pv(i) or pvb(i) or wind(i) or csp(i)) =
*     m_rsc_dat(r,i,rscbin,"cost") * Sw_SpurCostMult ;
set m_rsc_con(r,i) "set to detect numeraire rsc techs that have capacity value" ;
m_rsc_con(r,i)$sum{rscbin, m_rsc_dat(r,i,rscbin,"cap") } = yes ;
m_rsc_con(r,i)$sum{rscbin, sum{t,rsc_evmc(i,r,"cap",rscbin,t)} } = yes ;

m_rscfeas(r,i,rscbin) = no ;
m_rscfeas(r,i,rscbin)$m_rsc_dat(r,i,rscbin,"cap") = yes ;
m_rscfeas(r,i,rscbin)$sum{t, rsc_evmc(i,r,"cap",rscbin,t) } = yes;
m_rscfeas(r,i,rscbin)$[sum{ii$tg_rsc_cspagg(ii, i),m_rscfeas(r,ii,rscbin) }
                      $sum{t$tmodel_new(t), valcap_irt(i,r,t) }] = yes ;
m_rscfeas(r,i,rscbin)$[sum{ii$rsc_agg(ii,i),m_rscfeas(r,ii,rscbin) }$sum{t$tmodel_new(t),valcap_irt(i,r,t) }$psh(i)$Sw_WaterMain] = yes ;
m_rsc_dat(r,i,rscbin,sc_cat)$[sum{ii$rsc_agg(ii,i), m_rsc_dat(r,ii,rscbin,sc_cat) }
                             $sum{t$tmodel_new(t), valcap_irt(i,r,t) }
                             $(psh(i) or csp(i))
                             $Sw_WaterMain] =
  sum{ii$rsc_agg(ii,i), m_rsc_dat(r,ii,rscbin,sc_cat) } ;


set force_pcat(pcat,t) "conditional to indicate whether the force prescription equation should be active for pcat" ;

force_pcat(pcat,t)$[yeart(t) < firstyear_pcat(pcat)] = yes ;
force_pcat(pcat,t)$[sum{r, noncumulative_prescriptions(pcat,r,t) }] = yes ;

*=========================================
* Decoupled Capacity/Energy Upgrades for hydropower
*=========================================
Parameter
cost_cap_up(i,v,r,rscbin,t)     "--2004$/MW-- capacity upgrade costs",
cost_ener_up(i,v,r,rscbin,t)    "--2004$/MW-- energy upgrade costs.",
cap_cap_up(i,v,r,rscbin,t)      "--MW-- capacity of capacity upgrades",
cap_ener_up(i,v,r,rscbin,t)     "--MW-- capacity of energy upgrades",
allow_cap_up(i,v,r,rscbin,t)    "i, v, r, and t combinations that are allowed for capacity upsizing",
allow_ener_up(i,v,r,rscbin,t)   "i, v, r, and t combinations that are allowed for energy upsizing"
;

* Adjust available capacity and costs for hydropower upgrades using switch input.
m_rsc_dat(r,'hydUD',rscbin,"cap") = m_rsc_dat(r,'hydUD',rscbin,"cap") * %GSw_HydroUpgradeCapMult% ;
m_rsc_dat(r,'hydUND',rscbin,"cap") = m_rsc_dat(r,'hydUND',rscbin,"cap") * %GSw_HydroUpgradeCapMult% ;
m_rsc_dat(r,'hydUD',rscbin,"cost") = m_rsc_dat(r,'hydUD',rscbin,"cost") * %GSw_HydroUpgradeCostMult% ;
m_rsc_dat(r,'hydUND',rscbin,"cost") = m_rsc_dat(r,'hydUND',rscbin,"cost") * %GSw_HydroUpgradeCostMult% ;

* Use hydropower upgrade supply curves and multiplier from switch input to define decoupled capacity/energy upgrade costs.
cost_cap_up('hydED','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUD',rscbin,"cost") * %GSw_HydroCostFracCapUp% ;
cost_cap_up('hydEND','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUND',rscbin,"cost") * %GSw_HydroCostFracCapUp% ;
cost_ener_up('hydED','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUD',rscbin,"cost") * %GSw_HydroCostFracEnerUp% ;
cost_ener_up('hydEND','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUND',rscbin,"cost") * %GSw_HydroCostFracEnerUp% ;

* Initialize available capacity/energy upgrades to zero to avoid double counting if using coupled capacity/energy upgrades.
cap_cap_up(i,v,r,rscbin,t) = 0 ;
cap_ener_up(i,v,r,rscbin,t) = 0 ;

* If decoupling hydropower capacity/energy upgrades, use upgrade supply curves to define upgrade resource availability.
$ifthene.hydup2 %GSw_HydroCapEnerUpgradeType% == 2
* Need to re-multiply by 1000 because inclusion of hydUD and hydUND in the ban(i) set with this setting
*   prevents correct scaling of hydro costs.
cost_cap_up(i,v,r,rscbin,t)$cost_cap_up(i,v,r,rscbin,t) = cost_cap_up(i,v,r,rscbin,t) * 1000 ;
cost_ener_up(i,v,r,rscbin,t)$cost_ener_up(i,v,r,rscbin,t) = cost_ener_up(i,v,r,rscbin,t) * 1000 ;

cap_cap_up('hydED','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUD',rscbin,"cap") + hyd_add_upg_cap(r,'hydUD',rscbin,t) ;
cap_cap_up('hydEND','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUND',rscbin,"cap") + hyd_add_upg_cap(r,'hydUND',rscbin,t) ;
cap_ener_up('hydED','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUD',rscbin,"cap")  + hyd_add_upg_cap(r,'hydUD',rscbin,t) ;
cap_ener_up('hydEND','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUND',rscbin,"cap") + hyd_add_upg_cap(r,'hydUND',rscbin,t) ;
$endif.hydup2

* Use available decoupled upgrade resource to define sets for allowable decoupled capacity/energy upgrades.
allow_cap_up(i,v,r,rscbin,t)$[valcap(i,v,r,t)$cap_cap_up(i,v,r,rscbin,t)$(t.val>=Sw_UpgradeYear)] = yes ;
allow_ener_up(i,v,r,rscbin,t)$[valcap(i,v,r,t)$cap_ener_up(i,v,r,rscbin,t)$(t.val>=Sw_UpgradeYear)] = yes ;


* Track the initial amount of m_rsc_dat capacity to compare in e_report
* We adjust upwards by small amounts given potential for infeasibilities
* in very tiny amounts and thus track the extent of the adjustments
parameter m_rsc_dat_init(r,i,rscbin) "--MW-- Initial amount of resource supply curve capacity to compare with final amounts after adjustments" ;
m_rsc_dat_init(r,i,rscbin)$m_rsc_dat(r,i,rscbin,"cap") = m_rsc_dat(r,i,rscbin,"cap") ;


*========================================
* -- CO2 Capture and Storage Network --
*========================================
$onempty
set csfeas(cs)         "carbon storage sites with available capacity"
    r_cs(r,cs)         "mapping from BA to carbon storage sites"
/
$offlisting
$ondelim
$include inputs_case%ds%r_cs.csv
$offdelim
$onlisting
/ ,
    co2_routes(r,rr)   "set of available inter-ba co2 trade relationships" ;

parameter co2_storage_limit(cs)         "--metric tons-- total cumulative storage capacity per carbon storage site",
          co2_injection_limit(cs)       "--metric tons/hr-- co2 site injection rate upper bound",
          cost_co2_pipeline_cap(r,rr,t) "--$2004/(metric ton-mi/hr)-- capital costs associated with investing in co2 pipeline infrastructure",
          cost_co2_pipeline_fom(r,rr,t) "--$2004/((metric ton-mi/hr)-yr)-- FO&M costs associated with maintaining co2 pipeline infrastructure",
          cost_co2_stor_bec(cs,t)       "--$2004/metric ton-- breakeven cost for storing carbon - CF determined by GSw_CO2_BEC",
          cost_co2_spurline_cap(r,cs,t) "--$2004/(metric ton-mi/hr)-- capital costs associated with investing in spur lines to injection sites",
          cost_co2_spurline_fom(r,cs,t) "--2004/((metric ton-mi/hr)-yr)-- FO&M costs associated with maintaining co2 spurline infrastructure",
          r_cs_distance(r,cs)           "--mi-- euclidean distance between BA transmission endpoints and storage formations"
/
$offlisting
$offdigit
$ondelim
$include inputs_case%ds%r_cs_distance_mi.csv
$offdelim
$ondigit
$onlisting
/ ,
          min_co2_spurline_distance     "--mi-- minimum distance for a spur line (used to provide a floor for pipeline distances in r_cs_distance)"
;
$offempty

* Wherever BA centroids fall within formation boundaries, assume some average spur line distance to connect a CCS or DAC plant with an injection site
min_co2_spurline_distance = 20 ;
r_cs_distance(r,cs)$[r_cs_distance(r,cs) < min_co2_spurline_distance] = min_co2_spurline_distance ;

* Assign spurline costs
cost_co2_spurline_cap(r,cs,t)$[r_cs(r,cs)$tmodel_new(t)] = Sw_CO2_spurline_cost * r_cs_distance(r,cs) ;

* CO2 pipelines can be build between any two adjacent BAs
cost_co2_pipeline_cap(r,rr,t)$[routes_adjacent(r,rr)$tmodel_new(t)] = Sw_CO2_pipeline_cost * pipeline_distance(r,rr) ;
cost_co2_pipeline_fom(r,rr,t)$[routes_adjacent(r,rr)$tmodel_new(t)] = Sw_CO2_pipeline_fom * pipeline_distance(r,rr) ;

co2_routes(r,rr)$routes_adjacent(r,rr) = yes ;

$onempty
table co2_char(cs,*) "co2 site characteristics including injection rate limit, total storage limit, and break even cost"
$ondelim
$include inputs_case%ds%co2_site_char.csv
$offdelim
;
$offempty

*note that original units Mton == 'million tons'
co2_storage_limit(cs)   = 1e6 * co2_char(cs,"max_stor_cap") ;
co2_injection_limit(cs) = co2_char(cs,"max_inj_rate") ;
cost_co2_stor_bec(cs,t) = co2_char(cs,"bec_%GSw_CO2_BEC%");

* only want to consider storage sites that have both available capacity and injection limits
csfeas(cs)$[co2_storage_limit(cs)$co2_injection_limit(cs)] = yes ;
* only want to consider r_cs pairs which have available capacity
r_cs(r,cs)$[not csfeas(cs)] = no ;

cost_co2_spurline_fom(r,cs,t)$[r_cs(r,cs)$tmodel_new(t)] = Sw_CO2_spurline_fom * r_cs_distance(r,cs) ;

cost_co2_pipeline_cap(r,rr,t) =  %GSw_CO2_CostAdj% * cost_co2_pipeline_cap(r,rr,t);
cost_co2_pipeline_fom(r,rr,t) =  %GSw_CO2_CostAdj% * cost_co2_pipeline_fom(r,rr,t);
cost_co2_stor_bec(cs,t) =        %GSw_CO2_CostAdj% * cost_co2_stor_bec(cs,t) ;
cost_co2_spurline_fom(r,cs,t) =  %GSw_CO2_CostAdj% * cost_co2_spurline_fom(r,cs,t) ;
cost_co2_spurline_cap(r,cs,t) =  %GSw_CO2_CostAdj% * cost_co2_spurline_cap(r,cs,t) ;


* Parameter tracking for sequential solve
parameter
    m_capacity_exog0(i,v,r,t) "--MW-- original value of m_capacity_exog used in d_solveoneyear to make sure upgraded capacity isnt forced into retirement"
    z_rep(t)      "--$-- objective function value by year"
    z_rep_inv(t)  "--$-- investment component of objective function by year"
    z_rep_op(t)   "--$-- operation component of objective function by year"
;
z_rep_inv(t) = 0 ;
z_rep_op(t) = 0 ;


*================================================================================================
*== h- and szn-dependent sets and parameters (declared here, populated in d1_temporal_params) ===
*================================================================================================

* allh and allszn need to be populated here so they can be used in c_supplymodel and c_supplyobjective
Set allh "all potentially modeled hours"
/
$offlisting
$include inputs_case%ds%set_allh.csv
$onlisting
/ ;

Set allszn "all potentially modeled seasons (used as representative days/weks for hourly resolution)"
/
$offlisting
$include inputs_case%ds%set_allszn.csv
$onlisting
/ ;

Set
* Timeslices
    h(allh)                                "representative and stress timeslices"
    h_preh(allh, allh)                     "mapping set between one timeslice and all other timeslices earlier in that period"
    h_rep(allh)                            "representative timeslices"
    h_stress(allh)                         "stress timeslices"
    h_t(allh,allt)                         "representative and stress timeslices by model year"
    h_stress_t(allh,allt)                  "stress timeslices by model year"
* "Seasons" (both seasons and representative days/weks)
    szn(allszn)                            "representative and stress periods"
    szn_rep(allszn)                        "representative periods, or seasons if modeling full year"
    szn_stress(allszn)                     "stress periods"
    szn_t(allszn,allt)                     "representative and stress periods by model year"
    szn_stress_t(allszn,allt)              "stress periods by model year"
    szn_actualszn(allszn,allszn)           "mapping from rep periods to actual periods"
    actualszn(allszn)                      "actual periods (each is described by a representative period)"
* Mapping between timeslices and "seasons"
    h_szn(allh,allszn)                     "mapping of hour blocks to seasons"
    h_szn_start(allszn,allh)               "starting hour of each season"
    h_szn_end(allszn,allh)                 "ending hour of each season"
    h_szn_t(allh,allszn,allt)              "mapping of hour blocks to seasons by model year"
    h_actualszn(allh,allszn)               "mapping from rep timeslices to actual periods"
    nexth_actualszn(allszn,allh,allszn,allh) "mapping between one timeslice and the next for actual periods (szns)"
* Chronology
    nexth(allh,allh)                       "Mapping set between one timeslice (first) and the following (second)"
    starting_hour_nowrap(allh)             "Flag for whether allh is the first chronological hour by day type"
    final_hour(allh)                       "Flag for whether allh is the last chronological hour in a day type" 
    final_hour_nowrap(allh)                "Flag for whether allh is the last chronological hour in a day type"
    nextszn(allszn,allszn)                 "Mapping between one actual period (allszn) and the next"
    nextpartition(allszn,allszn)           "Mapping between one partition (allszn) and the next"
* Peak demand
    maxload_szn(r,allh,t,allszn)           "hour with highest load within each szn"
    h_ccseason_prm(allh,ccseason)          "peak-load hour for the entire modeled system by ccseason"
* Operating reserves
    opres_periods(allszn)                  "Periods within which the operating reserve constraint applies"
    opres_h(allh)                          "Timeslices within which the operating reserve constraint applies"
    dayhours(allh)                         "daytime hours, used to limit PV capacity to the daytime hours"
* Demand flexibility
    flex_h_corr1(flex_type,allh,allh)      "correlation set for hours referenced in flexibility constraints"
    flex_h_corr2(flex_type,allh,allh)      "correlation set for hours referenced in flexibility constraints"
* Minloading
    hour_szn_group(allh,allh)              "h and hh in the same season - used in minloading constraint"
;

Parameter
* Hour/period weighting
    hours(allh)                            "--hours-- number of hours in each time block"
    numdays(allszn)                        "--days-- number of days for each season"
    numpartitions(allszn)                  "--days-- number of partitions for each season in timeseries"
    hours_daily(allh)                      "--hours-- number of hours represented by time-slice 'h' during one day"
    numhours_nexth(allh,allh)              "--hours-- number of times hh follows h throughout year"
* Mapping to quarters
    frac_h_quarter_weights(allh,quarter)   "--fraction-- fraction of timeslice associated with each quarter"
    frac_h_ccseason_weights(allh,ccseason) "--fraction-- fraction of timeslice associated with each ccseason"
    szn_quarter_weights(allszn,quarter)    "--fraction-- fraction of season associated with each quarter"
    szn_ccseason_weights(allszn,ccseason)  "--fraction-- fraction of season associated with each ccseason"
* Capacity factor
    cf_rsc(i,v,r,allh,t)                   "--fraction-- capacity factor for rsc tech - t index included for use in CC/curt calculations"
    m_cf(i,v,r,allh,t)                     "--fraction-- modeled capacity factor"
    m_cf_szn(i,v,r,allszn,t)               "--fraction-- modeled capacity factor, averaged by season"
    cf_in(i,r,allh)                        "--fraction-- capacity factors for renewable technologies"
* Hydropower
    cf_hyd(i,allszn,r,allt)                "--fraction-- hydro capacity factors by season and year"
    climate_hydro_seasonal(r,allszn,allt)  "annual/seasonal nondispatchable hydropower availability"
    cap_hyd_szn_adj(i,allszn,r)            "--fraction-- seasonal max capacity adjustment for dispatchable hydro"
    hydmin(i,r,allszn)                     "minimum hydro loading factors by season and region"
* Availability (forced and scheduled outage rates)
    outage_forced_h(i,r,allh)              "--fraction-- forced outage rate"
    outage_scheduled_h(i,allh)             "--fraction-- scheduled outage rate"
    avail(i,r,allh)                        "--fraction-- fraction of capacity available for generation by hour"
    seas_cap_frac_delta(i,v,r,allszn,allt) "--scalar-- fractional change in seasonal capacity compared to summer"
* Demand
    load_exog(r,allh,t)                               "--MW-- busbar load"
    load_exog0(r,allh,t)                              "--MW-- original load by region hour and year - unchanged by demand side"
    load_allyear(r,allh,allt)                         "--MW-- end-use load by region, timeslice, and year"
    h2_exogenous_demand_regional(r,p,allh,allt)       "--metric tons per hour-- exogenous demand for hydrogen at the BA level"
* Peak demand
    peak_static_frac(r,ccseason,t)         "--fraction-- fraction of peak demand that is static"
    peakdem_static_ccseason(r,ccseason,t)  "--MW-- busbar peak demand by ccseason"
    peak_ccesason(r,ccseason,allt)         "--MW-- end-use peak demand by region, ccseason, year"
    peakdem_static_h(r,allh,t)             "--MW-- busbar peak demand by timeslice"
    peak_h(r,allh,allt)                    "--MW-- busbar peak demand by timeslice"
* Canada and Mexico demand
    canmexload(r,allh)                     "load for canadian and mexican regions"
* Demand flexibility
    flex_frac_load(flex_type,r,allh,allt)
    flex_demand_frac(flex_type,r,allh,t)   "fraction of load able to be considered flexible"
    load_exog_flex(flex_type,r,allh,t)     "the amount of exogenous load that is flexible"
    load_exog_static(r,allh,t)             "the amount of exogenous load that is static"
    dr_shed_out(i,r,allh)                  "--fraction-- dr shed capacity availability"
* EVMC storage
    evmc_storage_discharge_frac(i,r,allh,allt) "--fraction-- fraction of adopted EV storage discharge capacity that can be discharged (deferred charging) in each timeslice h"
    evmc_storage_charge_frac(i,r,allh,allt)    "--fraction-- fraction of adopted EV storage discharge capacity that can be charged (add back deferred charging) in each timeslice h"
    evmc_storage_energy_hours(i,r,allh,allt)    "--hours-- Allowable EV storage SOC (quantity deferred EV charge) [MWh] divided by nameplate EVMC discharge capacity [MW]"
* EVMC load
    evmc_baseline_load(r,allh,allt)        "--MW-- baseline electricity load from EV charging by timeslice h and year t"
    evmc_shape_load(i,r,allh)              "--fraction-- fraction of adopted price-responsive (shaped) EV load added by timeslice"
    evmc_shape_gen(i,r,allh)               "--fraction-- fraction of adopted price-responsive (shaped) EV load subtracted by timeslice"
* Flexible Canadian imports/exports [Sw_Canada=1]
    can_imports_szn(r,allszn,t)            "--MWh-- [Sw_Canada=1] seasonal imports from Canada by year"
    can_imports_szn_frac(allszn)           "--fraction-- [Sw_Canada=1] fraction of annual imports that occur in each season"
    can_exports_h(r,allh,t)                "--MW-- [Sw_Canada=1] timeslice exports to Canada by year"
    can_exports_h_frac(allh)               "--fraction-- [Sw_Canada=1] fraction of annual exports by timeslice"
* Capacity credit
    sdbin_size(ccreg,ccseason,sdbin,t)     "--MW-- available power capacity by storage duration bin - used to bin the peaking power capacity contribution of storage by duration"
    cc_old(i,r,ccseason,t)                 "--MW-- capacity credit for existing capacity - used in sequential solve similar to heritage reeds"
    cc_mar(i,r,ccseason,t)                 "--fraction--  cc_mar loading initialized to some reasonable value for the 2010 solve"
    cc_int(i,v,r,ccseason,t)               "--fraction--  average fractional capacity credit - used in intertemporal solve"
    cc_excess(i,r,ccseason,t)              "--MW-- this is the excess capacity credit when assuming marginal capacity credit in intertemporal solve"
    vre_gen_last_year(r,allh,t)            "--MW-- generation from VRE generators in the prior solve year"
    hybrid_cc_derate(i,r,ccseason,sdbin,t) "--fraction-- derate factor for hybrid PV+battery storage capacity credit"
    m_cc_mar(i,r,ccseason,t)               "--fraction-- marginal capacity credit",
* Heuristic climate impacts
    trans_cap_delta(allh,allt)             "--fraction-- fractional adjustment to transmission capacity from climate heuristics"
* Emissions and policies
    h_weight_csapr(allh)                   "hour weights for CSAPR ozone season constraints"
* Water access
    watsa(wst,r,allszn,t)                  "--fraction-- seasonal distribution factors for new water access by year"
    watsa_climate(wst,r,allszn,allt)       "--fraction-- time-varying fractional seasonal allocation of water"
* Minloading
    minloadfrac(r,i,allh)                  "--fraction-- minimum loading fraction - final used in model"
* Fossil gas supply curve
    gasadder_cd(cendiv,t,allh)             "--$/MMbtu-- adder for NG census division"
    szn_adj_gas(allh)                      "--fraction-- seasonal adjustment for gas prices"
;

alias(allh,allhh,allhhh) ;
alias(h,hh,hhh) ;
alias(allszn,allsznn) ;
alias(actualszn,actualsznn,actualsznnn) ;
alias(szn,sznn) ;

* Initialize some parameters
sdbin_size(ccreg,ccseason,sdbin,"%startyear%") = 1000 ;
cc_int(i,v,r,ccseason,t) = 0 ;
cc_excess(i,r,ccseason,t) = 0 ;
cc_old(i,r,ccseason,t) = 0 ;
m_cc_mar(i,r,ccseason,t) = 0 ;
hybrid_cc_derate(i,r,ccseason,sdbin,t)$[pvb(i)$valcap_irt(i,r,t)] = 1 ;

* Trim some of the largest matrices to reduce file sizes
cost_vom(i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
cost_fom(i,v,r,t)$[not valcap(i,v,r,t)] = 0 ;
heat_rate(i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
m_capacity_exog(i,v,r,t)$[not valcap(i,v,r,t)] = 0 ;
emit_rate(etype,e,i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;

*============================================================
* -- Initial state of parameters that change as model runs --
*============================================================

valinv_init(i,v,r,t) = valinv(i,v,r,t) ;
valcap_init(i,v,r,t) = valcap(i,v,r,t) ;
