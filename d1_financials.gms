* --- Ingest tax credit phaseout mult --- *

$gdxin outputs%ds%tc_phaseout_data%ds%tc_phaseout_mult_%cur_year%.gdx
$loaddcr tc_phaseout_mult_t_load = tc_phaseout_mult_t
$gdxin

tc_phaseout_mult_t(i,t)$tload(t) = tc_phaseout_mult_t_load(i,t) ;

* If tcphaseout is enabled, overwrite initialization
* This requires re-calculating cost_cap_fin_mult and its various permutations
if(Sw_TCPhaseout > 0,
* Apply the phaseout multiplier of the current level for current year
* and all future builds. Note that the value will remain the same for
* the cur_year-available vintage but can be updated for vintages whose
* first year hasn't solved yet. i.e. tc_phaseout_mult will remain constant for all
* current and historically-buildable plants but future plants may get updated.
tc_phaseout_mult(i,v,t)$[tload(t)$(firstyear_v(i,v)>=%cur_year%)] =
    tc_phaseout_mult_t(i,t) ;
);


* --- Start calculations of cost_cap_fin_mult family of parameters --- *

cost_cap_fin_mult(i,r,t) = ccmult(i,t) / (1.0 - tax_rate(t))
    * (1.0-tax_rate(t) * (1.0 - (itc_frac_monetized(i,t) * itc_energy_comm_bonus(i,r) * tc_phaseout_mult_t(i,t)/2.0) )
    * pv_frac_of_depreciation(i,t) - itc_frac_monetized(i,t) * tc_phaseout_mult_t(i,t))
    * degradation_adj(i,t) * financing_risk_mult(i,t) * (1 + reg_cap_cost_diff(i,r))
    * eval_period_adj_mult(i,t) ;

cost_cap_fin_mult_noITC(i,r,t) = ccmult(i,t) / (1.0 - tax_rate(t))
    * (1.0-tax_rate(t)*pv_frac_of_depreciation(i,t)) * degradation_adj(i,t)
    * financing_risk_mult(i,t) * (1 + reg_cap_cost_diff(i,r)) * eval_period_adj_mult(i,t) ;

cost_cap_fin_mult_no_credits(i,r,t) = ccmult(i,t) * (1 + reg_cap_cost_diff(i,r)) ;

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

* Assign "cost_cap_fin_mult" for nuclear_stor to be the weighted average of the nuclear and storage portions
* The weighting is based on:
*   (1) the cost of each portion: nuclear=cost_cap_nuclear_stor_p; storage=cost_cap_nuclear_stor_s
*   (2) the relative size of each portion: nuclear=1; storage=bcr
* The "-1" and "+1" values are needed because the multipliers are adjustments off of 1.0
* cost_cap_fin_mult(i,r,t)$nuclear_stor(i) =
*     ( (cost_cap_fin_mult_nuclear_stor_p(i,r,t) - 1) * cost_cap_nuclear_stor_p(i,t)
*     + bcr(i) * (cost_cap_fin_mult_nuclear_stor_s(i,r,t) - 1) * cost_cap_nuclear_stor_s(i,t) )
*     / (cost_cap_nuclear_stor_p(i,t) + bcr(i) * cost_cap_nuclear_stor_s(i,t)) + 1 ;

* cost_cap_fin_mult_noITC(i,r,t)$nuclear_stor(i) =
*     ( (cost_cap_fin_mult_nuclear_stor_p_noITC(i,r,t) - 1) * cost_cap_nuclear_stor_p(i,t)
*     + bcr(i) * (cost_cap_fin_mult_nuclear_stor_s_noITC(i,r,t) - 1) * cost_cap_nuclear_stor_s(i,t) )
*     / (cost_cap_nuclear_stor_p(i,t) + bcr(i) * cost_cap_nuclear_stor_s(i,t)) + 1 ;

* cost_cap_fin_mult_no_credits(i,r,t)$nuclear_stor(i) =
*     ((cost_cap_fin_mult_nuclear_stor_p_no_credits(i,r,t) - 1) * cost_cap_nuclear_stor_p(i,t)
*     + bcr(i) * (cost_cap_fin_mult_nuclear_stor_s_no_credits(i,r,t) - 1) * cost_cap_nuclear_stor_s(i,t))
*     / (cost_cap_nuclear_stor_p(i,t) + bcr(i) * cost_cap_nuclear_stor_s(i,t)) + 1 ;

* --- Upgrades ---
* Assign upgraded techs the same multipliers as the techs they are upgraded from
* This assignment must take place after expanding for water techs, if applicable.

if(Sw_WaterMain=1,
cost_cap_fin_mult(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult(ii,r,t) } ;

cost_cap_fin_mult_noITC(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_noITC(ii,r,t) } ;

cost_cap_fin_mult_no_credits(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_no_credits(ii,r,t) } ;
) ;

cost_cap_fin_mult(i,r,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_cap_fin_mult(ii,r,t) } ;
cost_cap_fin_mult_noITC(i,r,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_cap_fin_mult_noITC(ii,r,t) } ;

* --- Nuclear Ban ---
* Assign increased cost multipliers to regions with state nuclear bans
if(Sw_NukeStateBan = 2,
  cost_cap_fin_mult(i,r,t)$[nuclear(i)$nuclear_ba_ban(r)] =
    cost_cap_fin_mult(i,r,t) * nukebancostmult ;

  cost_cap_fin_mult_noITC(i,r,t)$[nuclear(i)$nuclear_ba_ban(r)] =
    cost_cap_fin_mult_noITC(i,r,t) * nukebancostmult ;
) ;

* Start by setting all multipliers to 1
rsc_fin_mult(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;
rsc_fin_mult_noITC(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;

* Hydro, pumped-hydro, and dr-shed have capital costs included in the supply curve,
* so change their multiplier to be the same as cost_cap_fin_mult adjusted by their
* capital cost multipliers.
rsc_fin_mult(i,r,t)$hydro(i) = cost_cap_fin_mult('hydro',r,t) * hydrocapmult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$hydro(i) = cost_cap_fin_mult_noITC('hydro',r,t) * hydrocapmult(t,i) ;
rsc_fin_mult(i,r,t)$psh(i) = cost_cap_fin_mult(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$psh(i) = cost_cap_fin_mult_noITC(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult(i,r,t)$dr_shed(i) = cost_cap_fin_mult(i,r,t)* dr_shed_capmult(i,r,t) ;
rsc_fin_mult_noITC(i,r,t)$dr_shed(i) = cost_cap_fin_mult_noITC(i,r,t)* dr_shed_capmult(i,r,t) ;

* Create a new parameter to hold capital financing multipliers with and without ITC for OSW transmission costs inside the resource supply curve cost
* Currently, OSW receives federal incentives in both its capital and transmission costs, hence this custom application for OSW
rsc_fin_mult(i,r,t)$ofswind(i) = cost_cap_fin_mult(i,r,t) * ofswind_rsc_mult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$ofswind(i) = cost_cap_fin_mult_noITC(i,r,t) ;

* Trim the cost_cap_fin_mult parameters to reduce file sizes
cost_cap_fin_mult(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                         $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                         $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

cost_cap_fin_mult_noITC(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                               $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                               $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

cost_cap_fin_mult_no_credits(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                                    $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                                    $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

* Round the cost_cap_fin_mult parameters, since they were re-calculated
cost_cap_fin_mult(i,r,t)$cost_cap_fin_mult(i,r,t)
  = round(cost_cap_fin_mult(i,r,t),3) ;

cost_cap_fin_mult_noITC(i,r,t)$cost_cap_fin_mult_noITC(i,r,t)
  = round(cost_cap_fin_mult_noITC(i,r,t),3) ;

cost_cap_fin_mult_no_credits(i,r,t)$cost_cap_fin_mult_no_credits(i,r,t)
  = round(cost_cap_fin_mult_no_credits(i,r,t),3) ;

rsc_fin_mult(i,r,t)$rsc_fin_mult(i,r,t) = round(rsc_fin_mult(i,r,t),3) ;

* Set cost_cap_fin_mult_out equal to cost_cap_fin_mult before we alter cost_cap_fin_mult
* for state fossil retirement policies and/or a full-region zero-carbon policy.
cost_cap_fin_mult_out(i,r,t) = cost_cap_fin_mult(i,r,t) ;

* Penalize new gas built within cost recovery period of 20 years for states that require 
* fossil retirements if Sw_StateRPS=1 and/or within 20 years of a zero-carbon policy
cost_cap_fin_mult(i,r,t)$[gas(i)$valcap_irt(i,r,t)] =
    cost_cap_fin_mult(i,r,t) 
    * max(sum{st$r_st(r,st), ng_crf_penalty_st(t,st) }$(not ccs(i))$Sw_StateRPS$(yeart(t)>=firstyear_RPS), 
          ng_crf_penalty_nat(i,t) ) ;


* Assign the nuclear portion of nuclear_stor the value of nuclear
cost_cap_fin_mult_nuclear_stor_p(i,r,t)$nuclear_stor(i) =
    cost_cap_fin_mult('nuclear',r,t) ;

cost_cap_fin_mult_nuclear_stor_p_noITC(i,r,t)$nuclear_stor(i) =
    cost_cap_fin_mult_noITC('nuclear',r,t) ;

cost_cap_fin_mult_nuclear_stor_p_no_credits(i,r,t)$nuclear_stor(i) =
    cost_cap_fin_mult_no_credits('nuclear',r,t) ;

* Assign the storage portion of nuclear_stor the storage tech multiplier
cost_cap_fin_mult_nuclear_stor_s(i,r,t)$nuclear_stor(i) = sum{ii$ nuclear_stor_stortech(i,ii), cost_cap_fin_mult(ii,r,t)};
cost_cap_fin_mult_nuclear_stor_s_noITC(i,r,t)$nuclear_stor(i) = sum{ii$ nuclear_stor_stortech(i,ii), cost_cap_fin_mult_noITC(ii,r,t)} ;
cost_cap_fin_mult_nuclear_stor_s_no_credits(i,r,t)$nuclear_stor(i) = sum{ii$ nuclear_stor_stortech(i,ii), cost_cap_fin_mult_no_credits(ii,r,t)} ;

* --- End calculations of cost_cap_fin_mult family of parameters --- *