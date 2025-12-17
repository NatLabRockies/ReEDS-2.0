$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

Model ReEDSmodel /all/ ;

*=================================
* -- MODEL AND SOLVER OPTIONS --
*=================================

OPTION lp = %solver% ;
ReEDSmodel.optfile = %GSw_gopt% ;
*treat fixed variables as parameters
ReEDSmodel.holdfixed = 1 ;

$ifthen %solver%==CBC
* adjust the GAMS infeasibility tolerance to handle empty rows when using CBC
ReEDSmodel.tolinfeas = 1e-15 ;
$endif


$if not set loadgdx $setglobal loadgdx 0

$ifthen.gdxin %loadgdx% == 1
execute_loadpoint "gdxfiles%ds%%gdxfin%.gdx" ;
Option BRatio = 0.0 ;
$endif.gdxin

*================================================
* --- Parameters only used when loading data ---
*================================================

set tload(t) "years in which data is loaded" ;
tload(t) = no ;

parameter
    cc_old_load(i,r,ccreg,ccseason,t)        "--MW-- cc_old loading in from the cc_out gdx file"
    sdbin_size_load(ccreg,ccseason,sdbin,t)  "--MW-- bin_size power loading in from the cc_out gdx file"
    cc_mar_load(i,r,ccreg,ccseason,t)        "--fraction-- cc_mar loading in from the cc_out gdx file"
    cc_evmc_load(i,r,ccseason,t)               "--fraction--  cc_evmc loading in from the cc_out gdx file"
;


*============================
* --- Round parameters ---
*============================
* As a general rule, costs or prices should be rounded to two decimal places
* and all other parameter should be rounded to no more than 3 decimal places
* Some exceptions might exist due to number scaling (e.g., emission rates)
acp_price(st,t)$acp_price(st,t) = round(acp_price(st,t),2) ;
avail_retire_exog_rsc(i,v,r,t)$valcap(i,v,r,t) = round(avail_retire_exog_rsc(i,v,r,t),3) ;
batterymandate(st,t)$batterymandate(st,t) = round(batterymandate(st,t),2) ;
bcr(i)$bcr(i) = round(bcr(i),4) ;
biosupply(usda_region,bioclass,"price") = round(biosupply(usda_region,bioclass,"price"),2) ;
biosupply(usda_region,bioclass,"cap") = round(biosupply(usda_region,bioclass,"cap"),3) ;
cc_storage(i,sdbin)$cc_storage(i,sdbin) = round(cc_storage(i,sdbin),3) ;
cendiv_weights(r,cendiv)$cendiv_weights(r,cendiv) = round(cendiv_weights(r,cendiv), 3) ;
cost_cap(i,t)$cost_cap(i,t) = round(cost_cap(i,t),2) ;
cost_cap_energy(i,t)$cost_cap_energy(i,t) = round(cost_cap_energy(i,t),2) ;
cost_co2_pipeline_fom(r,rr,t) =round(cost_co2_pipeline_fom(r,rr,t),2) ;
cost_co2_pipeline_cap(r,rr,t) =round(cost_co2_pipeline_cap(r,rr,t),2) ;
cost_co2_spurline_fom(r,cs,t) =  round(cost_co2_spurline_fom(r,cs,t),2) ;
cost_co2_spurline_cap(r,cs,t) =  round(cost_co2_spurline_cap(r,cs,t),2) ;
cost_co2_stor_bec(cs,t) = round(cost_co2_stor_bec(cs,t),2) ;
cost_fom(i,v,r,t)$cost_fom(i,v,r,t) = round(cost_fom(i,v,r,t),2) ;
cost_fom_energy(i,v,r,t)$cost_fom_energy(i,v,r,t) = round(cost_fom_energy(i,v,r,t),2) ;
cost_h2_storage_cap(h2_stor,t) = round(cost_h2_storage_cap(h2_stor,t), 2) ;
cost_h2_transport_cap(r,rr,t)$cost_h2_transport_cap(r,rr,t) = round(cost_h2_transport_cap(r,rr,t),2) ;
cost_h2_transport_fom(r,rr,t)$cost_h2_transport_fom(r,rr,t) = round(cost_h2_transport_fom(r,rr,t),2) ;
cost_opres(i,ortype,t)$cost_opres(i,ortype,t) = round(cost_opres(i,ortype,t),2) ;
cost_prod(i,v,r,t)$cost_prod(i,v,r,t) = round(cost_prod(i,v,r,t), 2) ;
cost_upgrade(i,v,r,t)$cost_upgrade(i,v,r,t) = round(cost_upgrade(i,v,r,t),2) ;
cost_vom(i,v,r,t)$cost_vom(i,v,r,t) = round(cost_vom(i,v,r,t),2) ;
cost_vom_pvb_b(i,v,r,t)$cost_vom_pvb_b(i,v,r,t) = round(cost_vom_pvb_b(i,v,r,t),2) ;
cost_vom_pvb_p(i,v,r,t)$cost_vom_pvb_p(i,v,r,t) = round(cost_vom_pvb_p(i,v,r,t),2) ;
cost_vom_nuclear_stor_s(i,v,r,t)$cost_vom_nuclear_stor_s(i,v,r,t) = round(cost_vom_nuclear_stor_s(i,v,r,t),2) ;
degrade(i,tt,t)$degrade(i,tt,t) = round(degrade(i,tt,t),3) ;
derate_geo_vintage(i,v)$derate_geo_vintage(i,v) = round(derate_geo_vintage(i,v),3) ;
distance(r,rr,trtype)$distance(r,rr,trtype) = round(distance(r,rr,trtype),3) ;
* non-CO2 emission/capture rates get small, here making sure accounting stays correct
emit_rate(etype,e,i,v,r,t)$valgen(i,v,r,t) = round(emit_rate(etype,e,i,v,r,t),10) ;
capture_rate(e,i,v,r,t)$valgen(i,v,r,t) = round(capture_rate(e,i,v,r,t),6) ;
fuel_price(i,r,t)$fuel_price(i,r,t) = round(fuel_price(i,r,t),2) ;
gasmultterm(cendiv,t)$gasmultterm(cendiv,t) = round(gasmultterm(cendiv,t),3) ;
heat_rate(i,v,r,t)$heat_rate(i,v,r,t) = round(heat_rate(i,v,r,t),2) ;
m_capacity_exog(i,v,r,t)$[valcap(i,v,r,t)$(not sameas(i,"smr"))] = round(m_capacity_exog(i,v,r,t),3) ;
m_capacity_exog_energy(i,v,r,t)$[valcap(i,v,r,t)] = round(m_capacity_exog_energy(i,v,r,t),3) ;
m_rsc_dat(r,i,rscbin,"cap")$m_rsc_dat(r,i,rscbin,"cap") = round(m_rsc_dat(r,i,rscbin,"cap"),3) ;
m_rsc_dat(r,i,rscbin,"cost")$m_rsc_dat(r,i,rscbin,"cost") = round(m_rsc_dat(r,i,rscbin,"cost"),2) ;
m_rsc_dat(r,i,rscbin,"cost_trans")$m_rsc_dat(r,i,rscbin,"cost_trans") = round(m_rsc_dat(r,i,rscbin,"cost_trans"),2) ;
prm(r,t)$prm(r,t) = round(prm(r,t),3) ;
prod_conversion_rate(i,v,r,t)$prod_conversion_rate(i,v,r,t) = round(prod_conversion_rate(i,v,r,t),6) ;
ptc_value_scaled(i,v,t)$ptc_value_scaled(i,v,t) = round(ptc_value_scaled(i,v,t),2) ;
recperc(rpscat,st,t)$recperc(rpscat,st,t) = round(recperc(rpscat,st,t),3) ;
rggi_cap(t)$rggi_cap(t) = round(rggi_cap(t),0) ;
state_cap(st,t)$state_cap(st,t) = round(state_cap(st,t),0) ;
storage_eff_pvb_g(i,t)$storage_eff_pvb_g(i,t) = round(storage_eff_pvb_g(i,t),3) ;
storage_eff_pvb_p(i,t)$storage_eff_pvb_p(i,t) = round(storage_eff_pvb_p(i,t),3) ;
storage_eff_nuclear_stor_g(i,t)$storage_eff_nuclear_stor_g(i,t) = round(storage_eff_nuclear_stor_g(i,t),3) ;
storage_eff_nuclear_stor_p(i,t)$storage_eff_nuclear_stor_p(i,t) = round(storage_eff_nuclear_stor_p(i,t),3) ;
tranloss(r,rr,trtype)$tranloss(r,rr,trtype) = round(tranloss(r,rr,trtype),3) ;
tsc_binwidth(r,rr,tscbin)$tsc_binwidth(r,rr,tscbin) = round(tsc_binwidth(r,rr,tscbin),2) ;
tsc_forward(r,rr,tscbin)$tsc_forward(r,rr,tscbin) = round(tsc_forward(r,rr,tscbin),2) ;
tsc_reverse(r,rr,tscbin)$tsc_reverse(r,rr,tscbin) = round(tsc_reverse(r,rr,tscbin),2) ;
transmission_cost_nonac(r,rr,trtype)$transmission_cost_nonac(r,rr,trtype) = round(transmission_cost_nonac(r,rr,trtype),2) ;
transmission_line_fom(r,rr,trtype)$transmission_line_fom(r,rr,trtype) = round(transmission_line_fom(r,rr,trtype),3) ;
trans_cost_cap_fin_mult(t) = round(trans_cost_cap_fin_mult(t),3) ;
trans_cost_cap_fin_mult_noITC(t) = round(trans_cost_cap_fin_mult_noITC(t),3) ;
upgrade_derate(i,v,r,t)$upgrade_derate(i,v,r,t) = round(upgrade_derate(i,v,r,t),3) ;
winter_cap_frac_delta(i,v,r)$winter_cap_frac_delta(i,v,r) = round(winter_cap_frac_delta(i,v,r),3) ;


*================================================
* --- SEQUENTIAL SETUP ---
*================================================
$ifthen.seq %timetype%=="seq"

* -- upgrade capacity tracking --
m_capacity_exog0(i,v,r,t) = m_capacity_exog(i,v,r,t) ;

* remove cc_int as it is only used in the intertemporal setting
cc_int(i,v,r,ccseason,t) = 0 ;

*for the sequential solve, what matters is the relative ratio of the pvf for capital and the pvf for onm
*therefore, we set the pvf capital to one, and then pvf_onm to the relative 20 year present value by using the crf
pvf_capital(t) = 1 ;
pvf_onm(t)$tmodel_new(t) = round(1 / crf(t),6) ;

$endif.seq


*================================================
* --- INTERTEMPORAL AND WINDOW SETUP ---
*================================================

$ifthen.intwin ((%timetype%=="int") or (%timetype%=="win"))

set
    loadset "set used for loading in merged gdx files" / ReEDS_Augur_%startyear%*ReEDS_Augur_%endyear% /
;

parameter
    cc_evmc_load2(loadset,i,r,ccseason,t)  "--fraction--  cc_evmc loading in from the cc_out gdx file"
    cc_iter(i,v,r,ccseason,t,cciter)     "--fraction-- Actual capacity value in iteration cciter"
    cc_mar_load2(loadset,i,r,ccseason,t) "--fraction-- cc_mar loading in from the cc_out gdx file"
    cc_old_load2(loadset,i,r,ccseason,t) "--MW-- cc_old loading in from the cc_out gdx file"
    cc_scale(i,r,ccseason,t)             "--unitless-- scaling of marginal capacity value levels in intertemporal runs to equal total capacity value"
    cc_totmarg(i,r,ccseason,t)           "--MW-- original estimate of total capacity value for intertemporal, based on marginals"
    sdbin_size_load2(loadset,ccreg,ccseason,sdbin,t)  "--MW-- bin_size power loading in from the cc_out gdx file"
;

cc_scale(i,r,ccseason,t) = 0 ;
cc_totmarg(i,r,ccseason,t) = 0 ;

$endif.intwin


*================================================
* --- INTERTEMPORAL SETUP ---
*================================================

$ifthen.int %timetype%=="int"

* Iteration tracking
set cciter "placeholder for iteration number for tracking CC" /0*20/ ;
parameter cap_iter(i,v,r,t,cciter)                      "--MW-- Power apacity by iteration"
          cap_energy_iter(i,v,r,t,cciter)               "--MWh-- Energy capacity by iteration"
          gen_iter(i,v,r,t,cciter)                      "--MWh-- Annual uncurtailed generation by iteration"
          cap_firm_iter(i,v,r,ccseason,t,cciter)        "--MW-- VRE Firm capacity by iteration"
          cap_energy_firm_iter(i,v,r,ccseason,t,cciter) "--MWh-- VRE Firm energy capacity by iteration"
;
cap_iter(i,v,r,t,cciter) = 0 ;
cap_energy_iter(i,v,r,t,cciter) = 0 ;
gen_iter(i,v,r,t,cciter) = 0 ;


*Assign csp3 and csp4 to use the same initial values as csp2_1
cc_int(i,v,r,ccseason,t)$[csp3(i) or csp4(i)] = cc_int('csp2_1',v,r,ccseason,t) ;

tmodel(t) = no ;
tmodel(t)$[tmodel_new(t)$(yeart(t)<=%endyear%)] = yes ;


*Cap the maximum CC in the first solve iteration
cc_int(i,v,r,ccseason,t)$[rsc_i(i)$(cc_int(i,v,r,ccseason,t)>0.4)$wind(i)] = 0.4 ;
cc_int(i,v,r,ccseason,t)$[rsc_i(i)$(cc_int(i,v,r,ccseason,t)>0.6)$pv(i)] = 0.6 ;


*set objective function to millions of dollars
cost_scale = 1 ;

*marginal capacity value not used in intertemporal case
m_cc_mar(i,r,ccseason,t) = 0 ;
*static capacity value for existing capacity not used in intertemporal case
cc_old(i,r,ccseason,t) = 0 ;

*sets needed for the demand side
*following sets are needed for linear interpolation of price
*that determine the year before the non-solved year and the year after
set t_before, t_after ;
alias(t,ttt) ;
t_before(t,tt)$[tprev(t,tt)$(ord(tt) = smax{ttt, ord(ttt)$tprev(t,ttt) })] = yes ;
t_after(t,tt)$tprev(tt,t) = yes ;

* intentionally not declaring all indices to make these flexibile
* rep only used when running the demand side
parameter rep                  "reporting for all sectors/timeslices/regions"
          repannual(t,*,*)     "national and annual reporting"
;

$endif.int


*=======================
* --- WINDOW SETUP ---
*=======================

$ifthen.win %timetype%=="win"

parameter pvf_capital0(t) "original pvf_capital used for calculating pvf_capital in window solve",
          pvf_onm0(t)     "original pvf_onm used for calculating pvf_capital in window solve";

pvf_capital0(t) = pvf_capital(t) ;
pvf_onm0(t) = pvf_onm(t) ;

cost_scale = 1e-3 ;

*Assign csp3 and csp4 to use the same initial values as csp2_1
cc_int(i,v,r,ccseason,t)$[csp3(i) or csp4(i)] = cc_int('csp2_1',v,r,ccseason,t) ;

*marginal capacity value not used in intertemporal case
m_cc_mar(i,r,ccseason,t) = 0 ;
*static capacity value for existing capacity not used in intertemporal case
cc_old(i,r,ccseason,t) = 0 ;

tmodel(t) = no ;

set windows /1*40/ ;
set blocks /start,stop/ ;


table solvewindows(windows,blocks)
$ondelim
$include inputs_case%ds%windows.csv
$offdelim
;

$endif.win


*======================
* --- Unload all inputs ---
*======================

execute_unload 'inputs_case%ds%inputs.gdx' ;
