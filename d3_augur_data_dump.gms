$ontext
This file creates a gdx file with all of the data necessary for the Augur module to solve. This includes:
    - Generator capacities
    - Exogenous retirments (sequential solves only)
    - Wind capacity by build year (because wind CFs change by build year)
    - heat rates, fuel costs, and vom costs
    - capacity factors (hydro, wind)
    - availability rates (1 - outage rates)
    - transmission capacities and loss rates
    - technology sets
$offtext

$if not set start_year $setglobal start_year 2010

*===============================
* Set and parameter definitions
*===============================

set rfeas(r)                 "list of feasible r regions - for use in Augur only"
    trange(t)                "range from first year to current year"
    tcur(t)                  "current year"
    tnext(t)                 "next year"
    valcap_i_filt(i)         "subset of valcap"
    valcap_ir(i,r)           "subset of valcap"
    valcap_iv_filt(i,v)      "subset of valcap"
    routes_filt(r,rr,trtype) "set of transmission connections"
;

parameter
avail_filt(i,v,allszn)             "--fraction-- fraction of capacity available for generation by season"
can_exports_h_filt(r,allh)         "--MW-- Canada exports by region and timeslice filtered for the previous solve year"
can_imports_cap(i,v,r)             "--MW-- Canadian import max capacity"
can_imports_szn_filt(r,allszn)     "--MWh-- Canada imports by region and season filtered for the previous solve year"
cap_converter_filt(r)              "--MW-- VSC AC/DC converter capacity"
cap_exist_i(i)                     "--MW-- technologies with existing capacity in the current solve year"
cap_exist_ir(i,r)                  "--MW-- technology-region combinations with existing capacity in the current solve year"
cap_exist_iv(i,v)                  "--MW-- technology-vintage combinations with existing capacity in the current solve year"
cap_exist(i,v,r)                   "--MW-- capacity that exists in the current solve year"
cap_exog_filt(i,v,r)               "--MW-- exogenous capacity"
cap_hyd_szn_adj_filt(i,allszn,r)   "--fraction-- seasonal hydro CF adjustment filtered for the previous solve year"
cap_init(i,v,r)                    "--MW-- initial capacity"
cap_ivrt(i,v,r,t)                  "--MW-- generation capacity"
cap_pvb(i,v,r)                     "--MW-- Hybrid PV+battery capacity (PV)"
cap_trans_energy(r,rr,trtype)      "--MW-- transmission capacity for energy trading"
cap_trans_prm(r,rr,trtype)         "--MW-- transmission capacity for PRM trading"
cf_adj_t_filt(i,v,t)               "--fraction-- capacity factor adjustment for wind"
cost_cap_filt(i,t)                 "--2004$/MW-- technology capital costs"
cost_cap_fin_mult_filt(i,r,t)      "--unitless-- capital cost financial multipliers"
cost_vom_filt(i,v,r)               "--$/MWh-- VO&M costs filtered for the previous solve year and existing capacity"
ctt_i_ii_filt(i,ii)                "--set-- set linking watercooling techs i to numeraire techs ii filtered for existing watercooling techs"
ctt_i_ii_psh(i,ii)                 "--set-- set linking PSH techs with water i to numeraire techs ii filtered for valid capacity techs"
emissions_price(e,r)               "--2004$/ton-- combined emissions taxes and marginal prices for emissions caps"
emit_rate_filt(e,i,v,r)            "--ton/MWh-- emission rate for the previous solve year"
energy_price(r,allh)               "--2004$/MWh-- energy price from the previous solve year"
flex_load_opt(r,allh)              "--MW-- model results for optimizing flexible load"
flex_load(r,allh)                  "--MW-- total exogenously defined flexible load"
fuel_price_filt(i,r)               "--$/mmBTU-- fuel prices filtered for the previous solve year and existing capacity"
heat_rate_filt(i,v,r)              "--MMBtu/MWh-- heat rate"
h2_usage_regional(r,allh,t)        "--ton-- H2 usage by region"
inv_cond_filt(i,v,t)               "--set-- vintage-year mapping for investments by technology"
inv_ivrt(i,v,r,t)                  "--MW-- investments in generation capacity"
m_cf_filt(i,v,r,allh)              "--fraction-- capacity factor used in the model"
m_cf_szn_filt(i,v,r,allszn)        "--fraction-- modelled capacity factors filtered for hydro resources to set seasonal energy constraints"
minloadfrac_filt(r,i,allszn)       "--fraction-- modelled mingen fraction filtered for hydro resources to set mingen constraints"
prod_filt(i,v,r,allh)              "--MW-- power consumed for PRODUCE.l"
repbioprice_filt(r)                "--2004$/MWh-- marginal price for biofuel in region where biofuel was used"
repgasprice_filt(r)                "--$/mmBTU-- NG prices in ReEDS filtered for the previous solve year"
repgasprice_r(r,t)                 "--$/mmBTU-- NG prices in ReEDS, switch-dependent, at the BA level"
repgasprice(cendiv,t)              "--$/mmBTU-- NG prices in ReEDS, the calculation of which depends on what switch is used"
repgasquant(cendiv,t)              "--mmBTU-- NG fuel usage in ReEDS - used to determine NG price"
ret_ivrt(i,v,r,t)                  "--MW-- retirements of generation capacity"
ret(i,v,r)                         "--MW-- retirements of generation capacity"
rsc_dat_dr(i,r,sc_cat,rscbin)      "--varies-- resource supply curve data"
rsc_dat_filt(i,r,sc_cat,rscbin)    "--$/MW-- capital costs filtered for pumped-hydro so arbitrage value doesn't exceed capital costs"
storage_eff_filt(i)                "--fraction-- storage efficiency filtered for the next solve year"
upgrade_to_filt(i,ii)              "--set-- set linking upgrade techs to the tech the upgraded from filtered for existing upgrades"
;

rfeas(r)$rb(r) = yes ;

trange(t) = no ;
loop(t$[(yeart(t)>%start_year%)$(yeart(t)<=%next_year%)],
trange(t) = yes ;
) ;
trange("%next_year%") = no ;
trange("%cur_year%") = yes ;

tcur(t) = no ;
tcur("%cur_year%") = yes ;

tnext(t) = no ;
tnext("%next_year%") = yes ;

*populate reduced-form sets
valcap_iv_filt(i,v) = sum{(r,t)$tcur(t), valcap(i,v,r,t)} ;
valcap_i_filt(i) = sum{v, valcap_iv_filt(i,v)} ;
valcap_ir(i,r) = sum{t$tcur(t), valcap_irt(i,r,t)} ;

*=======================================
* Removing banned technologies from sets
*=======================================

csp_sm(i) = csp_sm(i)$(not ban(i)) ;
geo(i) = geo(i)$(not ban(i)) ;
hydro_d(i) = hydro_d(i)$(not ban(i)) ;
hydro_nd(i) = hydro_nd(i)$(not ban(i)) ;
nuclear(i) = nuclear(i)$(not ban(i)) ;
dr1(i) = dr1(i)$(not ban(i)) ;
dr2(i) = dr2(i)$(not ban(i)) ;
storage_duration(i) = storage_duration(i)$(not ban(i)) ;
storage_eff(i,t) = storage_eff(i,t)$(not ban(i)) ;
storage_standalone(i) = storage_standalone(i)$(not ban(i)) ;

*==============================
* Get ReEDS generation capacity
*==============================

cap_exist(i,v,r)$valcap_ivr(i,v,r) = sum{t$tcur(t), CAP.l(i,v,r,t) } ;
cap_exist_ir(i,r)$valcap_ir(i,r) = sum{v, cap_exist(i,v,r) } ;
cap_exist_iv(i,v)$valcap_iv_filt(i,v) = sum{r, cap_exist(i,v,r) } ;
cap_exist_i(i)$valcap_i_filt(i) = sum{(r,v), cap_exist(i,v,r) } ;

cap_ivrt(i,v,r,t)$([not (upv(i) or dupv(i) or wind(i))]$valcap(i,v,r,t)$trange(t)) = CAP.l(i,v,r,t) ;
cap_ivrt(i,v,r,t)$([upv(i) or dupv(i) or wind(i)]$valcap(i,v,r,t)) =
    m_capacity_exog(i,v,r,t)$trange(t)
    + sum{tt$[inv_cond(i,v,r,t,tt)$trange(tt)],
          INV.l(i,v,r,tt) + INV_REFURB.l(i,v,r,tt)$[refurbtech(i)$Sw_Refurb]} ;
cap_init(i,v,r)$([not distpv(i)]$valcap_ivr(i,v,r)) = sum{t$tcur(t), cap_ivrt(i,v,r,t)$initv(v) } ;
cap_init(i,v,r)$(distpv(i)$valcap_ivr(i,v,r)) = sum{t$tfirst(t), cap_ivrt(i,v,r,t) } ;
inv_ivrt(i,v,r,t)$[valcap(i,v,r,t)$trange(t)] = [INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)]$valinv(i,v,r,t) + UPGRADES.l(i,v,r,t)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades] ;
inv_ivrt("distpv",v,r,t)$([trange(t)$(not tfirst(t))]$valcap("distpv",v,r,t)) = cap_ivrt("distpv",v,r,t) - sum{tt$tprev(t,tt), cap_ivrt("distpv",v,r,tt) } ;
inv_ivrt("distpv","init-1",r,"%next_year%") = inv_distpv(r,"%next_year%") ;

ret_ivrt(i,v,r,t)$([trange(t)$(not tfirst(t))$newv(v)]$valcap(i,v,r,t)) = sum{tt$tprev(t,tt), cap_ivrt(i,v,r,tt)} - cap_ivrt(i,v,r,t) + inv_ivrt(i,v,r,t) ;
ret_ivrt(i,v,r,t)$([abs(ret_ivrt(i,v,r,t) < 1e-6)]$valcap(i,v,r,t)) = 0 ;

ret(i,v,r)$valcap_ivr(i,v,r) = sum{t, ret_ivrt(i,v,r,t) } ;

cap_exog_filt(i,v,r)$([not canada(i)]$valcap_ivr(i,v,r)) = sum{t$tnext(t), m_capacity_exog(i,v,r,t) } ;

*============================
* Fuel prices
*============================

fuel_price_filt(i,r)$cap_exist_ir(i,r) = sum{t$tcur(t), fuel_price(i,r,t) } ;

* populate the fuel price for H2-CT techs as the marginal off the
* hydrogen demand constraint (in $/[tonne/hour]) divided by hours and 
* times h2_ct_intensity (tonne / mmbtu) to get $ / mmbtu -- note there should
* always be a positive value here since if an H2-CT is built it consumes hydrogen 
* the equation from which we extract the marginal depends on whether
* we have the national (Sw_H2 = 1) or regional (Sw_H2 = 2) constraint
h2_usage_regional(r,h,t) =
    hours(h) * ( 
        h2_exogenous_demand_regional(r,'h2',h,t)
        + sum{(i,v)$[valgen(i,v,r,t)$h2_ct(i)],
            GEN.l(i,v,r,h,t) * h2_ct_intensity * heat_rate(i,v,r,t)}
    )
;

fuel_price_filt(i,r)$[Sw_H2$h2_ct(i)$(sum{t$tcur(t),yeart(t) } >= Sw_H2_Demand_Start)$cap_exist_ir(i,r)] = 
    sum{t$tcur(t),
        (1 / cost_scale) * (1 / pvf_onm(t)) * h2_ct_intensity * (
            eq_h2_demand.m('h2',t)$[Sw_H2=1]
* regional demand is now by hour, so calculate annual price as the weighted average of demand across hours
            + (sum{h, eq_h2_demand_regional.m(r,h,t) / hours(h) * h2_usage_regional(r,h,t) }
               / sum{h, h2_usage_regional(r,h,t) }
            )$[(Sw_H2=2)$(sum{h, h2_usage_regional(r,h,t) })]
        )
    }
;

* for regions that consumed biomass, use the cost of the last supply curve bin consumed
repbioprice_filt(r)$[sum{(t, bioclass), bioused.l(bioclass,r,t) }] =
    sum{t$tcur(t), smax{bioclass$[bioused.l(bioclass,r,t)],
      sum{usda_region$r_usda(r, usda_region), biosupply(usda_region,bioclass,"price")} } + bio_transport_cost } ;

* for regions with no biomass, assign biomass price as the cost of the cheapest available supply curve bin for that region
* also safeguard against outlying values (for some reason smax sometimes returns -INF for regions w/o biomass consumption)
repbioprice_filt(r)$[(repbioprice_filt(r) <= 0)] = rep_bio_price_unused(r) ;

repgasquant(cendiv,t)$[(Sw_GasCurve = 0 or Sw_GasCurve = 3)$tcur(t)] =
    sum{(gb,h), GASUSED.l(cendiv,gb,h,t) * hours(h) } ;

repgasquant(cendiv,t)$[(Sw_GasCurve = 1 or Sw_GasCurve = 2)$tcur(t)] =
    sum{(i,v,r,h)$[r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t)
       } ;

repgasprice(cendiv,t)$[(Sw_GasCurve = 0)$tcur(t)] =
    smax{gb$[sum{h, GASUSED.l(cendiv,gb,h,t) }], gasprice(cendiv,gb,t) } ;

repgasprice(cendiv,t)$[(Sw_GasCurve = 2)$tcur(t)$repgasquant(cendiv,t)] =
    sum{(i,v,r,h)$[r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h)*heat_rate(i,v,r,t)*fuel_price(i,r,t)*GEN.l(i,v,r,h,t)
       } / (repgasquant(cendiv,t)) ;

repgasprice_r(r,t)$[(Sw_GasCurve = 0 or Sw_GasCurve = 2)$tcur(t)] = sum{cendiv$r_cendiv(r,cendiv), repgasprice(cendiv,t) } ;

repgasprice_r(r,t)$[(Sw_GasCurve = 1)$tcur(t)] =
              ( sum{(h,cendiv),
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(r,cendiv) *
                   hours(h) } / sum{h, hours(h) }

              + smax((fuelbin,cendiv)$[VGASBINQ_REGIONAL.l(fuelbin,cendiv,t)$r_cendiv(r,cendiv)], gasbinp_regional(fuelbin,cendiv,t) )

              + smax(fuelbin$VGASBINQ_NATIONAL.l(fuelbin,t), gasbinp_national(fuelbin,t) )
              ) ;

* catch any infinite values, assign to reference gas price
repgasprice_r(r,t)$[(repgasprice_r(r,t) = -inf or repgasprice_r(r,t) = inf)$tcur(t)] =
    smax{cendiv$r_cendiv(r,cendiv), gasprice_ref(cendiv,t) } ;

repgasprice_filt(r)$rb(r) = sum{t$tcur(t), repgasprice_r(r,t) } ;

*============================
* Filter necessary input data
*============================

avail_filt(i,v,szn)$[cap_exist_iv(i,v)$(not vre(i))] = smax{h$h_szn(h,szn), avail(i,h) * derate_geo_vintage(i,v) } ;

can_exports_h_filt(r,h) = sum{t$tcur(t), can_exports_h(r,h,t)} ;

can_imports_cap(i,v,r)$canada(i) = sum{t$tcur(t), m_capacity_exog(i,v,r,t) } ;

can_imports_szn_filt(r,szn) = sum{t$tcur(t), can_imports_szn(r,szn,t)} ;

*can_exports_h_filt(r,h)$[Sw_Canada = 2] = 0 ;
*can_imports_cap(i,v,r)$[Sw_Canada = 2] = 0 ;
*can_imports_szn_filt(r,szn)$[Sw_Canada = 2] = 0 ;

cap_hyd_szn_adj_filt(i,szn,r)$[cap_exist_ir(i,r)$hydro_d(i)] = cap_hyd_szn_adj(i,szn,r) ;

cost_cap_filt(i,t)$[storage_standalone(i) or dr(i)] = cost_cap(i,t)$tnext(t) ;

cost_cap_fin_mult_filt(i,r,t)$([storage_standalone(i) or dr(i)]) = cost_cap_fin_mult(i,r,t)$tnext(t) ;

cost_vom_filt(i,v,r)$cap_exist(i,v,r) = sum{t$tcur(t), cost_vom(i,v,r,t) } ;

cf_adj_t_filt(i,v,t)$[cap_exist_iv(i,v)$trange(t)] = cf_adj_t(i,v,t) ;
cf_adj_t_filt(i,v,"%next_year%") = cf_adj_t(i,v,"%next_year%")$(vre(i) or pvb(i)) ;

ctt_i_ii_filt(i,ii) = ctt_i_ii(i,ii)$cap_exist_i(i) ;

ctt_i_ii_psh(i,ii) = ctt_i_ii(i,ii)$[valcap_i_filt(i)$psh(i)] ;

emit_rate_filt(e,i,v,r)$cap_exist(i,v,r) = sum{t$tcur(t), emit_rate(e,i,v,r,t) } ;

heat_rate_filt(i,v,r)$cap_exist(i,v,r) = sum{t$tcur(t), heat_rate(i,v,r,t) } ;

inv_cond_filt(i,v,t)$[(vre(i) or pvb(i))$tnext(t)] = sum{(tt,r), inv_cond(i,v,r,tt,t) } ;

m_cf_filt(i,v,r,h)$[(vre(i) or pvb(i))$cap_exist(i,v,r)] = sum{t$tnext(t), m_cf(i,v,r,h,t) } ;

m_cf_szn_filt(i,v,r,szn)$[hydro(i)$cap_exist(i,v,r)] = sum{t$tcur(t), m_cf_szn(i,v,r,szn,t) } ;

minloadfrac_filt(r,i,szn)$[hydro(i)$cap_exist_ir(i,r)$szn_rep(szn)] =
    sum{h$h_szn(h,szn), minloadfrac(r,i,h) * hours(h) } / sum{h$h_szn(h,szn), hours(h) } ;

rsc_dat_filt(i,r,"cost",rscbin)$[storage_standalone(i)$cap_exist_ir(i,r)] = rsc_dat(i,r,"cost",rscbin) ;

rsc_dat_dr(i,r,"cost",rscbin)$dr(i)  = sum{t$tnext(t), rsc_dr(i,r,"cost",rscbin,t) };

storage_eff_filt(i)$storage(i) = sum{t$tnext(t), storage_eff(i,t) } ;

upgrade_to_filt(i,ii) = upgrade_to(i,ii)$cap_exist_i(i) ;

*============================
* Get ReEDS transmission data
*============================

cap_trans_energy(r,rr,trtype) = sum{t$tcur(t), CAPTRAN_ENERGY.l(r,rr,trtype,t) } ;
cap_trans_prm(r,rr,trtype) = sum{t$tcur(t), CAPTRAN_PRM.l(r,rr,trtype,t) } ;

cap_converter_filt(r) = sum{t$tcur(t), CAP_CONVERTER.l(r,t) } ;

* In Augur, trtype="AC" includes everything except for VSC
routes_filt(r,rr,trtype) = sum{t$tcur(t), routes(r,rr,trtype,t) } ;

*============================
* Flexible load data
*============================

flex_load(r,h) = sum{(flex_type,t)$tcur(t), load_exog_flex(flex_type,r,h,t) } ;

flex_load_opt(r,h) = sum{(flex_type,t)$tcur(t), FLEX.l(flex_type,r,h,t) } ;

*============================
* Extra consumption data
*============================

prod_filt(i,v,r,h)$[sum{t$tcur(t), valcap(i,v,r,t)}$consume(i)] =
                sum{(p,t)$[i_p(i,p)$tcur(t)], PRODUCE.l(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) } ;

*============================
* Get ReEDS emissions prices [$/ton]
*============================
* NOT included: eq_emit_rate_limit (disabled by default), eq_CSAPR_Budget, eq_CSAPR_Assurance
emissions_price(e,r) =
    (1 / cost_scale / emit_scale(e))
    * sum{t$tcur(t),
        (1 / pvf_onm(t)) * eq_annual_cap.m(e,t)
        + emit_tax(e,r,t)
    } ;

* Add marginal prices from CO2-specific constraints
emissions_price("CO2",r) =
    emissions_price("CO2",r)
    + (1 / cost_scale / emit_scale("CO2"))
        * sum{t$tcur(t),
            (1 / pvf_onm(t)) * [
                eq_RGGI_cap.m(t)$RGGI_R(r)
                + sum{st$r_st(r,st), eq_state_cap.m(st,t) }
            ]
        } ;

*===================================
* Get ReEDS energy prices ($/MWh)
*===================================

energy_price(r,h)$hours(h) =
    sum{t$tcur(t),
        (1 / cost_scale) * (1 / pvf_onm(t)) * eq_supply_demand_balance.m(r,h,t) / hours(h) } ;

*=======================================
* Unload all relevant data to a gdx file
*=======================================

execute_unload 'ReEDS_Augur%ds%augur_data%ds%reeds_data_%cur_year%.gdx'
    allowed_shed
    avail_filt
    bcr
    bir_pvb_config
    can_exports_h_filt
    can_imports_cap
    can_imports_szn_filt
    cap_converter_filt
    cap_exog_filt
    cap_hyd_szn_adj_filt
    cap_init
    cap_ivrt
    cap_trans_energy
    cap_trans_prm
    cf_adj_t_filt
    converter_efficiency_vsc
    cost_cap_filt
    cost_cap_fin_mult_filt
    cost_vom_filt
    csp_sm
    ctt_i_ii_filt
    ctt_i_ii_psh
    degrade_annual
    dr1
    dr2
    emissions_price
    emit_rate_filt
    energy_price
    flex_load
    flex_load_opt
    forced_outage
    fuel_price_filt
    fuel2tech
    geo
    h_szn
    heat_rate_filt
    hierarchy
    hydro_d
    hydro_nd
    hours
    hydmin
    i
    ilr
    ilr_pvb_config
    i_subsets
    inv_cond_filt
    inv_ivrt
    ivt_num
    m_cf_filt
    m_cf_szn_filt
    maxage
    minloadfrac_filt
    notvsc
    nuclear
    prm
    prod_filt
    pvf_onm
    r
    rfeas
    r_cendiv
    repbioprice_filt
    repgasprice_filt
    ret
    ret_ivrt
    routes_filt
    rsc_dat_dr
    rsc_dat_filt
    sdbin
    storage_duration
    storage_eff_filt
    storage_standalone
    Sw_VSC
    szn
    tfirst
    tmodel_new
    tranloss
    trtype
    upgrade_to_filt
    v
    vom_hyd
;
