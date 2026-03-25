$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

* globals needed for this file:
* case : name of case you're running
* cur_year : current year

*remove any load years
tload(t) = no ;

* --- reset tmodel ---
tmodel(t) = no ;
tmodel("%cur_year%") = yes ;

$log 'Solving sequential case for...'
$log '  Case: %case%'
$log '  Year: %cur_year%'


*** Define the h- and szn-dependent parameters
$onMultiR
$include d1_temporal_params.gms
$offMulti


* need to have values initialized before making adjustments
* thus cannot perform these adjustments until 2010 has solved
$ifthene.post2010 %cur_year%>2010
* adjust the m_rsc_dat capacity upward to avoid infeasibilities
* these are caused by floating point differences that occur in GAMS
* which will report the model as infeasible before sending to CPLEX
* whereas CPLEX will still attempt to solve the model if the infeasibilities
* are less than the eprhs option specified in cplex.opt (default 1e-6)
m_rsc_dat(r,i,rscbin,"cap")$[m_rsc_dat(r,i,rscbin,"cap")] =
    max(m_rsc_dat(r,i,rscbin,"cap"),
        sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) <= yeart("%cur_year%"))$rsc_agg(i,ii)],
            INV_RSC.l(ii,v,r,rscbin,tt) * resourcescaler(ii) }
    ) ;

* set m_capacity_exog to the maximum of either its original amount
* or the amount of upgraded capacity that has occurred in the past 20 years
* to avoid forcing recently upgraded capacity into retirement
if(Sw_Upgrades = 1,

    m_capacity_exog(i,v,r,t)$[valcap(i,v,r,t)$sameas(t,"%cur_year%")
                         $(sum{(ii,tt)$[(tt.val <= t.val)$(t.val - tt.val <= Sw_UpgradeLifespan)
                                       $valcap(ii,v,r,tt)$upgrade_from(ii,i)], UPGRADES.l(ii,v,r,tt) } ) ] =
* [maximum of] initial capacity recorded in d_solveprep
                    max( m_capacity_exog0(i,v,r,t),
* -or- capacity of upgrades that have occurred from this i v r t combination
                    sum{(ii,tt)$[(tt.val <= t.val)$(t.val - tt.val <= Sw_UpgradeLifespan)
                                 $valcap(ii,v,r,tt)$upgrade_from(ii,i)],
                                 UPGRADES.l(ii,v,r,tt) / (1-upgrade_derate(ii,v,r,tt)) }
    ) ;

) ;

* if the relative growth constraint is turned on, then calculate the growth
* limits for each growth bin
if(Sw_GrowthRelCon > 0,

* Calculate the maximum deployment that could have been achieved in the last modeled
* year. For example, if tmodel is 2023 and the prior two solve years were 2020 and 
* 2015, then we are calculating the maximum deployment that could have occured in
* 2020 at the growth rate specified in gbin1. This requires looking back to tprev
* and the solve year before tprev, hence the need for the yeart(ttt).
* The denominator is simply a discount term, and the multiplication is an associated
* compounding term.
    last_year_max_growth(st,tg,t)$tmodel(t) = 
        sum{(i,v,r,tt)$[valinv(i,v,r,tt)$r_st(r,st)$tg_i(tg,i)$tprev(t,tt)],
            INV.l(i,v,r,tt) } 
        / sum{allt$[(allt.val>sum{tt$tprev(t,tt), sum{ttt$tprev(tt,ttt), yeart(ttt) } })
                   $(allt.val<=sum{tt$tprev(t,tt), yeart(tt) })],
              (growth_bin_size_mult("gbin1") ** (allt.val - sum{tt$tprev(t,tt), sum{ttt$tprev(tt,ttt), yeart(ttt) } } - 1)) }
        * (growth_bin_size_mult("gbin1") ** ((sum{tt$tprev(t,tt), yeart(tt) - sum{ttt$tprev(tt,ttt), yeart(ttt) } }) - 1)) ;

* Now calculate the growth bin size for the current solve year, assuming that the 
* maximum growth allowed in gbin1 happens each year over the current solve period.
    growth_bin_limit("gbin1",st,tg,t)$tmodel(t) = 
        sum{allt$[(allt.val>sum{tt$tprev(t,tt), yeart(tt) })
                 $(allt.val<=yeart(t))],
            last_year_max_growth(st,tg,t) * growth_bin_size_mult("gbin1") ** (allt.val - sum{tt$tprev(t,tt), yeart(tt) }) }
        / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;

* Do not allow growth_bin_limit to decline over time (i.e., if a higher growth
* rate was achieved in the past, allow the model to start from that higher level)
    growth_bin_limit("gbin1",st,tg,t)$tmodel(t) = smax{tt, growth_bin_limit("gbin1",st,tg,tt) } ;
   
* If the calculated  gbin1 value is less than the minimum bin size, then set it to the minimum bin size
    growth_bin_limit("gbin1",st,tg,t)$[tmodel(t)$(growth_bin_limit("gbin1",st,tg,t) < gbin_min(tg))$stfeas(st)] = gbin_min(tg) ;

* Now set the size of the remaining bins
    growth_bin_limit(gbin,st,tg,t)$[tmodel(t)$(not sameas(gbin,"gbin1"))] = 
        growth_bin_limit("gbin1",st,tg,t) * (growth_bin_size_mult(gbin) - growth_bin_size_mult("gbin1")) ;

    growth_bin_limit(gbin,st,tg,t)$growth_bin_limit(gbin,st,tg,t) = round(growth_bin_limit(gbin,st,tg,t),0) ;

) ;

$endif.post2010

*load in results from the cc/curtailment scripts
$ifthene.tcheck %cur_year%>%GSw_SkipAugurYear%

*indicate we're loading data
tload("%cur_year%") = yes ;

*file written by ReEDS_Augur.py
* loaddcr = domain check (dc) + overwrite values storage previously (r)
$gdxin ReEDS_Augur%ds%augur_data%ds%ReEDS_Augur_%prev_year%.gdx
$loaddcr cc_old_load = cc_old
$loaddcr cc_mar_load = cc_mar
$loaddcr cc_dr_load = cc_dr
$loaddcr sdbin_size_load = sdbin_size
$gdxin

*Note: these values are rounded before they are written to the gdx file, so no need to round them here

* assign old and marginal capacity credit parameters to those
* corresponding to each balancing areas cc region
cc_old(i,r,szn,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] =
    sum{ccreg$r_ccreg(r,ccreg), cc_old_load(i,r,ccreg,szn,t) } ;

m_cc_mar(i,r,szn,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] =
    sum{ccreg$r_ccreg(r,ccreg), cc_mar_load(i,r,ccreg,szn,t) } ;

m_cc_dr(i,r,szn,t)$[tload(t)$dr(i)] = cc_dr_load(i,r,szn,t) ;

sdbin_size(ccreg,szn,sdbin,t)$tload(t) = sdbin_size_load(ccreg,szn,sdbin,t) ;

* --- Assign hybrid PV+battery capacity credit ---
$ontext
Limit the capacity credit of hybrid PV such that the total capacity credit from the PV and the battery do not exceed the inverter limit.
  Example: PV = 130 MWdc, Battery = 65MW, Inverter = 100 MW (PVdc/Battery=0.5; PVdc/INVac=1.3)
  Assuming the capacity credit of the Battery is 65MW, then capacity credit of the PV is limited to 35MW or 0.269 (35MW/130MW) on a relative basis.
  Max capacity credit PV [MWac/MWdc] = (Inverter - Battery capcity credit) / PV_dc
                                     = (P_dc / ILR - P_dc * BCR) / PV_dc
                                     = 1/ILR - BCR
$offtext
* marginal capacity credit
m_cc_mar(i,r,szn,t)$[tload(t)$pvb(i)] = min{ m_cc_mar(i,r,szn,t), 1 / ilr(i) - bcr(i) } ;

* old capacity credit
* (1) convert cc_old from MW to a fractional basis, (2) adjust the fractional value to be less than 1/ILR - BCR, (3) multiply by CAP to convert back to MW
cc_old(i,r,szn,t)$[tload(t)$pvb(i)$sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)}] =
    min{ cc_old(i,r,szn,t) / sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)}, 1 / ilr(i) - bcr(i) }
    * sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)};

$endif.tcheck

* --- Ingest tax credit phaseout mult --- *

$gdxin outputs%ds%tc_phaseout_data%ds%tc_phaseout_mult_%cur_year%.gdx
$loaddcr tc_phaseout_mult_t_load = tc_phaseout_mult_t
$gdxin

tc_phaseout_mult_t(i,t)$tload(t) = tc_phaseout_mult_t_load(i,t) ;

*if tcphaseout is enabled, overwrite initialization
*this requires re-calculating cost_cap_fin_mult and its various permutations
if(Sw_TCPhaseout > 0,
* apply the phaseout multiplier of the current level for current year
* and all future builds. Note that the value will remain the same for
* the cur_year-available vintage but can be updated for vintages whose
* first year hasn't solved yet. i.e. tc_phaseout_mult will remain constant for all
* current and historically-buildable plants but future plants may get updated.
tc_phaseout_mult(i,v,t)$[tload(t)$(firstyear_v(i,v)>=%cur_year%)] =
    tc_phaseout_mult_t(i,t) ;
);

* --- Start calculations of cost_cap_fin_mult family of parameters --- *
* These are calculated here because the ITC phaseout can influence these parameters,
* and the timing of the phaseout is not known beforehand.
cost_cap_fin_mult(i,r,t) = ccmult(i,t) / (1.0 - tax_rate(t))
    * (1.0-tax_rate(t) * (1.0 - (itc_frac_monetized(i,t) * tc_phaseout_mult_t(i,t)/2.0) )
    * pv_frac_of_depreciation(i,t) - itc_frac_monetized(i,t) * tc_phaseout_mult_t(i,t))
    * degradation_adj(i,t) * financing_risk_mult(i,t) * reg_cap_cost_mult(i,r)
    * eval_period_adj_mult(i,t) ;

cost_cap_fin_mult_noITC(i,r,t) = ccmult(i,t) / (1.0 - tax_rate(t))
    * (1.0-tax_rate(t)*pv_frac_of_depreciation(i,t)) * degradation_adj(i,t)
    * financing_risk_mult(i,t) * reg_cap_cost_mult(i,r) * eval_period_adj_mult(i,t) ;

cost_cap_fin_mult_no_credits(i,r,t) = ccmult(i,t) * reg_cap_cost_mult(i,r) ;

* Assign the PV portion of PVB the value of UPV
cost_cap_fin_mult_pvb_p(i,r,t)$pvb(i) =
    sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult(ii,r,t) } ;

cost_cap_fin_mult_pvb_p_noITC(i,r,t)$pvb(i) =
    sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult_noITC(ii,r,t) } ;

cost_cap_fin_mult_pvb_p_no_credits(i,r,t)$pvb(i) =
    sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult_no_credits(ii,r,t) } ;

* In the financing module (python), PVB refers to the battery portion of the hybrid.
* This convention is used to estimate the ITC benefit for the battery.
* Assign the battery portion of PVB the value computed in the financing module for PVB
cost_cap_fin_mult_pvb_b(i,r,t)$pvb(i) = cost_cap_fin_mult(i,r,t) ;
cost_cap_fin_mult_pvb_b_noITC(i,r,t)$pvb(i) = cost_cap_fin_mult_noITC(i,r,t) ;
cost_cap_fin_mult_pvb_b_no_credits(i,r,t)$pvb(i) = cost_cap_fin_mult_no_credits(i,r,t) ;

* Assign "cost_cap_fin_mult" for PVB to be the weighted average of the PV and battery portions
* The weighting is based on:
*   (1) the cost of each portion: PV=cost_cap_pvb_p; Battery=cost_cap_pvb_b
*   (2) the relative size of each portion: PV=1; Battery=bcr
* The "-1" and "+1" values are needed because the multipliers are adjustments off of 1.0
cost_cap_fin_mult(i,r,t)$pvb(i) =
    ( (cost_cap_fin_mult_pvb_p(i,r,t) - 1) * cost_cap_pvb_p(i,t)
    + bcr(i) * (cost_cap_fin_mult_pvb_b(i,r,t) - 1) * cost_cap_pvb_b(i,t) )
    / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_noITC(i,r,t)$pvb(i) =
    ( (cost_cap_fin_mult_pvb_p_noITC(i,r,t) - 1) * cost_cap_pvb_p(i,t)
    + bcr(i) * (cost_cap_fin_mult_pvb_b_noITC(i,r,t) - 1) * cost_cap_pvb_b(i,t) )
    / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_no_credits(i,r,t)$pvb(i) =
    ((cost_cap_fin_mult_pvb_p_no_credits(i,r,t) - 1) * cost_cap_pvb_p(i,t)
    + bcr(i) * (cost_cap_fin_mult_pvb_b_no_credits(i,r,t) - 1) * cost_cap_pvb_b(i,t))
    / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

* --- Upgrades ---
*Assign upgraded techs the same multipliers as the techs they are upgraded from
cost_cap_fin_mult(i,r,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_cap_fin_mult(ii,r,t) } ;
cost_cap_fin_mult_noITC(i,r,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_cap_fin_mult_noITC(ii,r,t) } ;

if(Sw_WaterMain=1,
cost_cap_fin_mult(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult(ii,r,t) } ;

cost_cap_fin_mult_noITC(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_noITC(ii,r,t) } ;

cost_cap_fin_mult_no_credits(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_no_credits(ii,r,t) } ;
) ;

* --- Nuclear Ban ---
*Assign increased cost multipliers to regions with state nuclear bans
if(Sw_NukeStateBan = 2,
  cost_cap_fin_mult(i,r,t)$[nuclear(i)$nuclear_ba_ban(r)] =
    cost_cap_fin_mult(i,r,t) * nukebancostmult ;

  cost_cap_fin_mult_noITC(i,r,t)$[nuclear(i)$nuclear_ba_ban(r)] =
    cost_cap_fin_mult_noITC(i,r,t) * nukebancostmult ;
) ;

* Start by setting all multipliers to 1
rsc_fin_mult(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;
rsc_fin_mult_noITC(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;

*Hydro and pumped-hydrohave capital costs included in the supply curve,
* so change their multiplier to be the same as cost_cap_fin_mult
rsc_fin_mult(i,r,t)$hydro(i) = cost_cap_fin_mult('hydro',r,t) ;
rsc_fin_mult(i,r,t)$psh(i) = cost_cap_fin_mult(i,r,t) ;
rsc_fin_mult_noITC(i,r,t)$hydro(i) = cost_cap_fin_mult_noITC('hydro',r,t) ;
rsc_fin_mult_noITC(i,r,t)$psh(i) = cost_cap_fin_mult_noITC(i,r,t) ;

* Apply cost reduction multipliers for geothermal hydro and offshore wind
rsc_fin_mult(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult_noITC(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult(i,r,t)$ofswind(i) = rsc_fin_mult(i,r,t) * ofswind_rsc_mult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$ofswind(i) = rsc_fin_mult_noITC(i,r,t) * ofswind_rsc_mult(t,i) ;

*trimming the cost_cap_fin_mult parameters to reduce file sizes
cost_cap_fin_mult(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                         $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                         $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

cost_cap_fin_mult_noITC(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                               $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                               $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

cost_cap_fin_mult_no_credits(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                                    $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                                    $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

*round the cost_cap_fin_mult parameters, since they were re-calculated
cost_cap_fin_mult(i,r,t)$cost_cap_fin_mult(i,r,t)
  = round(cost_cap_fin_mult(i,r,t),3) ;

cost_cap_fin_mult_noITC(i,r,t)$cost_cap_fin_mult_noITC(i,r,t)
  = round(cost_cap_fin_mult_noITC(i,r,t),3) ;

cost_cap_fin_mult_no_credits(i,r,t)$cost_cap_fin_mult_no_credits(i,r,t)
  = round(cost_cap_fin_mult_no_credits(i,r,t),3) ;

rsc_fin_mult(i,r,t)$rsc_fin_mult(i,r,t) = round(rsc_fin_mult(i,r,t),3) ;

*Set cost_cap_fin_mult_out equal to cost_cap_fin_mult before we alter cost_cap_fin_mult for Virginia policy
*and zero carbon policy.
cost_cap_fin_mult_out(i,r,t) = cost_cap_fin_mult(i,r,t) ;

*Penalizing new gas built within cost recovery period of 20 years for states that require fossil retirements
cost_cap_fin_mult(i,r,t)$[gas(i)$valcap_irt(i,r,t)$sum{st$r_st(r,st), ng_crf_penalty_st(t,st) }] =
    cost_cap_fin_mult(i,r,t) * sum{st$r_st(r,st), ng_crf_penalty_st(t,st) } ;

*Penalizing new gas that can be upgraded to recover upgrade costs prior to upgrade within 20 years of a zero carbon policy
cost_cap_fin_mult(i,r,t)$[gas(i)$(not ccs(i))] =
    cost_cap_fin_mult(i,r,t) * (((ng_carb_lifetime_cost_adjust(t) - 1) * .2) + 1) ;

* --- End calculations of cost_cap_fin_mult family of parameters --- *

* --- Estimate curtailment from "old" hybrid PV+battery ---

$ifthene %cur_year%==2010
*initialize CAP.l for 2010 because it has not been defined yet
CAP.l(i,v,r,"2010")$[m_capacity_exog(i,v,r,"2010")] = m_capacity_exog(i,v,r,"2010") ;
$endif

* Now that cost_cap_fin_mult is done, calculate cost_growth, which is
* the minimum cost of that technology within a state
if(Sw_GrowthRelCon > 0,
*rsc_fin_mult holds the multipliers for hydro, psh, and geo techs, so don't include them here
    cost_growth(i,st,t)$[tmodel(t)$sum{r$[r_st(r,st)], valinv_irt(i,r,t) }$stfeas(st)$(not (geo(i) or hydro(i) or psh(i)))] = 
        smin{r$[valinv_irt(i,r,t)$r_st(r,st)$cost_cap_fin_mult(i,r,t)$cost_cap(i,t)],
            cost_cap_fin_mult(i,r,t) * cost_cap(i,t) } ;

*rsc_fin_mult holds the multipliers for hydro, psh, and geo techs
    cost_growth(i,st,t)$[tmodel(t)$sum{r$[r_st(r,st)], valinv_irt(i,r,t) }$stfeas(st)$(geo(i) or hydro(i) or psh(i))] = 
        smin{(r,rscbin)$[valinv_irt(i,r,t)$r_st(r,st)$rsc_fin_mult(i,r,t)$m_rsc_dat(r,i,rscbin,"cost")],
            rsc_fin_mult(i,r,t) * m_rsc_dat(r,i,rscbin,"cost") } ;

    cost_growth(i,st,t)$cost_growth(i,st,t) = round(cost_growth(i,st,t),3) ;
) ;

* --- report data immediately before the solve statement---
*execute_unload "data_%cur_year%.gdx" ;

* ------------------------------
* Solve the Model
* ------------------------------

solve ReEDSmodel minimizing z using lp ;

*record objective function values right after solve
z_rep(t)$tmodel(t) = Z.l ;
z_rep_inv(t)$tmodel(t) = Z_inv.l(t) ;
z_rep_op(t)$tmodel(t) = Z_op.l(t) ;

if(Sw_Upgrades = 1,
* note sum over tt required here as we want to only remove the incentive
* from years beyond the current year if upgrades occurred in this solve year

* extend the current-year incentive beyond current date to expiration date - only needed
* when needing to specify beyond current amounts
    co2_captured_incentive(i,v,r,t)$[sum{tt$tmodel(tt),upgrades.l(i,v,r,tt) }
                                    $(not sum{tt$tfix(tt),upgrades.l(i,v,r,tt)})
                                    $(year(t) < %cur_year% + co2_capture_incentive_length)
                                    $(yeart(t) >= %cur_year%)
                                    $valcap(i,v,r,t) ] = co2_captured_incentive(i,v,r,"%cur_year%") ;

* remove co2 captured incentive after the length of time if upgrades occurred in this year
    co2_captured_incentive(i,v,r,t)$[sum{tt$tmodel(tt),upgrades.l(i,v,r,tt) }
                                    $(year(t) >= %cur_year% + co2_capture_incentive_length)
                                    $valcap(i,v,r,t) ] = 0 ;

* adjust fom of upgraded-from plant to updated cost for maintaining the CCS equipment
    cost_fom(i,v,r,t)$[sum{(ii,tt)$[tmodel(tt)$upgrade_from(ii,i)],upgrades.l(ii,v,r,tt) }
                                    $(year(t) >= %cur_year%)
                                    $valcap(i,v,r,t) ] =
        max(cost_fom(i,v,r,t),
            sum{ii$upgrade_from(ii,i),cost_fom(ii,v,r,t) }
           ) ;
) ;

*add the just-solved year to tfix and fix variables for next solve year
tfix("%cur_year%") = yes ;
$include d2_varfix.gms

*dump data to be used by Augur
$include d3_augur_data_dump.gms

*dump data for tax credit phaseout calculations
parameter
  emit_r_tc(r,t)  "--million metric tons CO2-- co2 emissions, regional (note: units dependent on emit_scale)"
  emit_nat_tc(t)  "--million metric tons CO2-- co2 emissions, national (note: units dependent on emit_scale)"
;

emit_r_tc(r,t)$tmodel_new(t) = EMIT.l("CO2",r,t) * emit_scale("CO2") ;
emit_nat_tc(t)$tmodel_new(t) = sum{r, emit_r_tc(r,t) } ;
* [kilotonne] * [1000 tonne / kilotonne] / ([MW] * [hours]) = [tonne/MWh]
$ifthen.stateco2 %GSw_StateCO2ImportLevel% == 'r'
    co2_emit_rate_r(r,t)$tmodel(t) = (
        EMIT.l("CO2",r,t) * emit_scale("CO2")
        / sum{(i,v,h)$[valgen(i,v,r,t)], hours(h) * GEN.l(i,v,r,h,t) }
* Avoid division-by-zero errors
    )$sum{(i,v,h)$[valgen(i,v,r,t)], hours(h) * GEN.l(i,v,r,h,t) } ;
$else.stateco2
* sum emissions and generation within the region
    co2_emit_rate_regional(%GSw_StateCO2ImportLevel%,t)$tmodel(t) = (
        sum{rr$r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%),
            EMIT.l("CO2",rr,t) } * emit_scale("CO2")
        / sum{(i,v,rr,h)$[valgen(i,v,rr,t)
                        $r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%)],
              hours(h) * GEN.l(i,v,rr,h,t) }
* Avoid division-by-zero errors
    )$sum{(i,v,rr,h)$[valgen(i,v,rr,t)
                    $r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%)],
          hours(h) * GEN.l(i,v,rr,h,t) }
    ;
* broadcast the regional emissions rate to each r in the region
    co2_emit_rate_r(r,t)$tmodel(t) =
        sum{%GSw_StateCO2ImportLevel%
            $r_%GSw_StateCO2ImportLevel%(r,%GSw_StateCO2ImportLevel%),
            co2_emit_rate_regional(%GSw_StateCO2ImportLevel%,t) }
    ;
$endif.stateco2


execute_unload "outputs%ds%tc_phaseout_data%ds%emit_for_tc_phaseout_calc_%cur_year%.gdx"
  emit_nat_tc, emit_r_tc
;

* Abort if the solver returns an error
if (ReEDSmodel.modelStat > 1,
    abort "Model did not solve to optimality",
    ReEDSmodel.modelStat) ;
