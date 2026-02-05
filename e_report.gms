$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$if not set case $setglobal case ref


sets
sys_costs /
  inv_co2_network_pipe
  inv_co2_network_spur
  inv_converter_costs
  inv_dac
  inv_h2_pipeline
  inv_h2_production
  inv_h2_storage
  inv_investment_capacity_costs
  inv_investment_refurbishment_capacity
  inv_investment_spurline_costs_rsc_technologies
  inv_investment_water_access
  inv_itc_payments_negative
  inv_itc_payments_negative_refurbishments
  inv_spurline_investment
  inv_transmission_interzone_ac_investment
  inv_transmission_interzone_dc_investment
  inv_transmission_intrazone_investment
  op_acp_compliance_costs
  op_co2_incentive_negative
  op_co2_network_fom_pipe
  op_co2_network_fom_spur
  op_co2_storage
  op_co2_transport_storage
  op_consume_fom
  op_consume_vom
  op_emissions_taxes
  op_fom_costs
  op_fuelcosts_objfn
  op_h2combustion_fuel_costs
  op_h2_fuel_costs
  op_h2_revenue_exog
  op_h2_transport
  op_h2_transport_intrareg
  op_h2_storage
  op_h2_vom
  op_h2_ptc_payments_negative
  op_operating_reserve_costs
  op_ptc_payments_negative
  op_rect_fuel_costs
  op_spurline_fom
  op_startcost
  op_transmission_fom
  op_transmission_intrazone_fom
  op_vom_costs
/,

sys_costs_inv(sys_costs) /
  inv_co2_network_pipe
  inv_co2_network_spur
  inv_converter_costs
  inv_dac
  inv_h2_pipeline
  inv_h2_production
  inv_h2_storage
  inv_investment_capacity_costs
  inv_investment_refurbishment_capacity
  inv_investment_spurline_costs_rsc_technologies
  inv_investment_water_access
  inv_itc_payments_negative
  inv_itc_payments_negative_refurbishments
  inv_spurline_investment
  inv_transmission_interzone_ac_investment
  inv_transmission_interzone_dc_investment
  inv_transmission_intrazone_investment
/,

sys_costs_op(sys_costs) /
  op_acp_compliance_costs
  op_co2_incentive_negative
  op_co2_network_fom_pipe
  op_co2_network_fom_spur
  op_co2_storage
  op_co2_transport_storage
  op_consume_fom
  op_consume_vom
  op_emissions_taxes
  op_fom_costs
  op_fuelcosts_objfn
  op_h2combustion_fuel_costs
  op_h2_fuel_costs
  op_h2_revenue_exog
  op_h2_transport
  op_h2_transport_intrareg
  op_h2_storage
  op_h2_ptc_payments_negative
  op_operating_reserve_costs
  op_ptc_payments_negative
  op_spurline_fom
  op_startcost
  op_transmission_fom
  op_transmission_intrazone_fom
  op_vom_costs
/,

rev_cat "categories for renvenue streams" /load, res_marg, oper_res, rps, charge /,

lcoe_cat "categories for LCOE calculation" /capcost, upgradecost, rsccost, fomcost, vomcost, gen /

loadtype "categories for types of load" / end_use, dist_loss, trans_loss, stor_charge, h2_prod, h2_network, dac /

h2_demand_type / "electricity", "cross-sector"/

;

* Parameter definitions in the following file are read from e_report_params.csv
* and parsed in copy_files.py.
* All output parameters should be defined in e_report_params.csv.
$include e_report_params.gms

* Restrict operational outputs to representative timeslices and seasons
h(h)$[not h_rep(h)] = no ;
szn(szn)$[not szn_rep(szn)] = no ;

*=================================================
* -- CAPACITY ABOVE INTERCONNECTION QUEUE LIMIT --
*=================================================

cap_above_limit(tg,r,t)$tmodel_new(t) = CAP_ABOVE_LIM.l(tg,r,t) ;

*=====================
* -- CO2 Reporting --
*=====================

CO2_CAPTURED_out(r,h,t)$tmodel_new(t) = CO2_CAPTURED.l(r,h,t) ;
CO2_CAPTURED_out_ann(r,t)$tmodel_new(t) = sum(h,hours(h) * CO2_CAPTURED.l(r,h,t) );
CO2_STORED_out(r,cs,h,t)$[tmodel_new(t)$csfeas(cs)] = CO2_STORED.l(r,cs,h,t) ;
CO2_STORED_out_ann(r,cs,t)$[tmodel_new(t)$csfeas(cs)] = sum(h,hours(h) * CO2_STORED.l(r,cs,h,t) );
CO2_TRANSPORT_INV_out(r,rr,t)$tmodel_new(t) = CO2_TRANSPORT_INV.l(r,rr,t) ;
CO2_SPURLINE_INV_out(r,cs,t)$[tmodel_new(t)$csfeas(cs)] = CO2_SPURLINE_INV.l(r,cs,t) ;

CO2_FLOW_out(r,rr,h,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = CO2_FLOW.l(r,rr,h,t) + CO2_FLOW.l(rr,r,h,t) ;
CO2_FLOW_out_ann(r,rr,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = sum{h, hours(h) * (CO2_FLOW.l(r,rr,h,t) + CO2_FLOW.l(rr,r,h,t)) } ;

CO2_FLOW_pos_out(r,rr,h,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = CO2_FLOW.l(r,rr,h,t) ;
CO2_FLOW_pos_out_ann(r,rr,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = sum{h, hours(h) * CO2_FLOW.l(r,rr,h,t) } ;

CO2_FLOW_neg_out(r,rr,h,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = -1 * CO2_FLOW.l(rr,r,h,t) ;
CO2_FLOW_neg_out_ann(r,rr,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = -1 * sum{h, hours(h) * CO2_FLOW.l(rr,r,h,t) } ;

CO2_FLOW_net_out(r,rr,h,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = CO2_FLOW.l(r,rr,h,t) - CO2_FLOW.l(rr,r,h,t) ;
CO2_FLOW_net_out_ann(r,rr,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = sum{h, hours(h) * (CO2_FLOW.l(r,rr,h,t) - CO2_FLOW.l(rr,r,h,t)) } ;

*=========================
* LCOE
*=========================

avg_avail(i,v,r) = sum{h, hours(h) * avail(i,r,h) * derate_geo_vintage(i,v) } / 8760 ;
avg_cf(i,v,r,t)$[CAP.l(i,v,r,t)$(not rsc_i(i))] =
    sum{h, GEN.l(i,v,r,h,t) * hours(h) }
    / sum{h,
          CAP.l(i,v,r,t)
          * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
          * hours(h) }
;

*non-rsc technologies do not face the grid supply curve
*and thus can be assigned to an individual bin

*LCOE calculation is appropriate for sequential solve mode only where annual energy production is the same in every year.
*In inter-temporal modes this isn't the case and energy production should be discounted appropriately.

lcoe(i,v,r,t,"bin1")$[(not rsc_i(i))$valcap_init(i,v,r,t)$ivt(i,v,t)$avg_avail(i,v,r)] =
* cost of capacity divided by generation
   ((crf(t) * cost_cap_fin_mult(i,r,t) * cost_cap(i,t)$newv(v)
     + cost_fom(i,v,r,t)
    ) / (avg_avail(i,v,r) * 8760))
*plus VOM costs
   + cost_vom(i,v,r,t)
* plus fuel costs - assuming constant fuel prices here (model prices might be different)
   + heat_rate(i,v,r,t) * fuel_price(i,r,t)
;

gen_rsc(i,v,r,t)$[valcap_init(i,v,r,t)$ivt(i,v,t)$rsc_i(i)] =
    sum{h, m_cf(i,v,r,h,t) * hours(h) } ;

lcoe(i,v,r,t,rscbin)$[valcap_init(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)] =
* cost of capacity divided by generation
    (crf(t)
     * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t)
* Spur-line costs embedded in supply curve for techs without explicitly-modeled spurlines
        + m_rsc_dat(r,i,rscbin,"cost")$[newv(v)$(not spur_techs(i))]
* Spur-line costs assuming 1:1 ratio between gen cap and spur cap (i.e. no overbuilding)
        + sum{x$[xfeas(x)$x_r(x,r)$spur_techs(i)], spurline_cost(x) * Sw_SpurCostMult}
     )
     + cost_fom(i,v,r,t)
    ) / gen_rsc(i,v,r,t)
*plus VOM costs
    + cost_vom(i,v,r,t)
;

lcoe_cf_act(i,v,r,t,rscbin)$[valcap_init(i,v,r,t)$rsc_i(i)] = lcoe(i,v,r,t,rscbin) ;
lcoe_cf_act(i,v,r,t,"bin1")$[(not rsc_i(i))$valcap_init(i,v,r,t)$ivt(i,v,t)$avg_cf(i,v,r,t)] =
* cost of capacity divided by generation
   ((crf(t) * cost_cap_fin_mult(i,r,t) * cost_cap(i,t)$newv(v)
     + cost_fom(i,v,r,t)
    ) / (avg_cf(i,v,r,t) * 8760)
   )
*plus VOM costs
   + cost_vom(i,v,r,t)
*plus fuel costs - assuming constant fuel prices here (model prices might be different)
   + heat_rate(i,v,r,t) * fuel_price(i,r,t)
;

lcoe_nopol(i,v,r,t,rscbin)$valcap_init(i,v,r,t) = lcoe(i,v,r,t,rscbin) ;
lcoe_nopol(i,v,r,t,rscbin)$[valcap_init(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)] =
* cost of capacity divided by generation
    (crf(t)
     * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t)
* Spur-line costs embedded in supply curve for techs without explicitly-modeled spurlines
        + m_rsc_dat(r,i,rscbin,"cost")$newv(v)$(not spur_techs(i)))
* Spur-line costs assuming 1:1 ratio between gen cap and spur cap (i.e. no overbuilding)
        + sum{x$[xfeas(x)$x_r(x,r)$spur_techs(i)], spurline_cost(x) * Sw_SpurCostMult}
     + cost_fom(i,v,r,t)
    ) / gen_rsc(i,v,r,t)
*plus VOM costs
    + cost_vom(i,v,r,t)
;

lcoe_fullpol(i,v,r,t,rscbin)$valcap_init(i,v,r,t) = lcoe(i,v,r,t,rscbin) ;
lcoe_fullpol(i,v,r,t,rscbin)$[valcap_init(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)] =
* cost of capacity divided by generation
    (crf(t)
     * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t)
* Spur-line costs embedded in supply curve for techs without explicitly-modeled spurlines
        + m_rsc_dat(r,i,rscbin,"cost")$newv(v)$(not spur_techs(i)))
* Spur-line costs assuming 1:1 ratio between gen cap and spur cap (i.e. no overbuilding)
        + sum{x$[xfeas(x)$x_r(x,r)$spur_techs(i)], spurline_cost(x) * Sw_SpurCostMult}
     + cost_fom(i,v,r,t))
    / gen_rsc(i,v,r,t)
*plus VOM costs
    + cost_vom(i,v,r,t)
;

lcoe_built(i,r,t)$[ [sum{(v,h)$[valinv(i,v,r,t)$INV.l(i,v,r,t)], GEN.l(i,v,r,h,t) * hours(h) }] or
                    [sum{(v,h)$[UPGRADES.l(i,v,r,t)$Sw_Upgrades], GEN.l(i,v,r,h,t) * hours(h) }] ] =
        (crf(t) * (
         sum{v$valinv(i,v,r,t),
             INV.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t) ) }
       + sum{v$[valinv(i,v,r,t)$battery(i)],
             INV_ENERGY.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) * cost_cap_energy(i,t) ) }
       + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
             UPGRADES.l(i,v,r,t) * (cost_upgrade(i,v,r,t) * cost_cap_fin_mult(i,r,t) ) }
       + sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)],
             INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) }
                 )
       + sum{v$valinv(i,v,r,t), cost_fom(i,v,r,t) * INV.l(i,v,r,t) }
       + sum{v$[valinv(i,v,r,t)$battery(i)], cost_fom_energy(i,v,r,t) * INV_ENERGY.l(i,v,r,t) }
       + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades], cost_fom(i,v,r,t) * UPGRADES.l(i,v,r,t) }
       + sum{(v,h)$[valinv(i,v,r,t)$INV.l(i,v,r,t)], (cost_vom(i,v,r,t)+ heat_rate(i,v,r,t) * fuel_price(i,r,t)) * GEN.l(i,v,r,h,t) * hours(h) }
       + sum{(v,h)$[UPGRADES.l(i,v,r,t)$Sw_Upgrades], (cost_vom(i,v,r,t)+ heat_rate(i,v,r,t) * fuel_price(i,r,t)) * GEN.l(i,v,r,h,t) * hours(h) }
        ) / (sum{(v,h)$[valinv(i,v,r,t)$INV.l(i,v,r,t)], GEN.l(i,v,r,h,t) * hours(h) }
            + sum{(v,h)$[UPGRADES.l(i,v,r,t)$Sw_Upgrades], GEN.l(i,v,r,h,t) * hours(h) })
;

lcoe_built_nat(i,t)$[sum{(v,r)$valinv(i,v,r,t), INV.l(i,v,r,t) }] =
                  sum{r, lcoe_built(i,r,t) * sum{v$valinv(i,v,r,t), INV.l(i,v,r,t) } }
                    / sum{(v,r)$valinv(i,v,r,t), INV.l(i,v,r,t) } ;

lcoe_pieces("capcost",i,r,t)$tmodel_new(t) = 
          sum{v$valinv(i,v,r,t), INV.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t) ) }
        + sum{v$[valinv(i,v,r,t)$battery(i)], INV_ENERGY.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) * cost_cap_energy(i,t) ) } ;

lcoe_pieces("upgradecost",i,r,t)$tmodel_new(t) =
                  sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
                    cost_upgrade(i,v,r,t) * cost_cap_fin_mult(i,r,t) * UPGRADES.l(i,v,r,t) }
                  + sum{(v,rscbin)$allow_cap_up(i,v,r,rscbin,t),
                    cost_cap_fin_mult(i,r,t) * INV_CAP_UP.l(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }
                  + sum{(v,rscbin)$allow_ener_up(i,v,r,rscbin,t),
                    cost_cap_fin_mult(i,r,t) * INV_ENER_UP.l(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) } ;

lcoe_pieces("rsccost",i,r,t)$tmodel_new(t) =
                  sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)],
                    INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) } ;

lcoe_pieces("fomcost",i,r,t)$tmodel_new(t) =
                  sum{v$valinv(i,v,r,t), cost_fom(i,v,r,t) * INV.l(i,v,r,t) }
                  + sum{v$[valinv(i,v,r,t)$battery(i)], cost_fom_energy(i,v,r,t) * INV_ENERGY.l(i,v,r,t) }
                  + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades], cost_fom(i,v,r,t) * UPGRADES.l(i,v,r,t) } ;

lcoe_pieces("vomcost",i,r,t)$tmodel_new(t) =
                  sum{(v,h)$[valinv(i,v,r,t)$INV.l(i,v,r,t)],
                    (cost_vom(i,v,r,t) + heat_rate(i,v,r,t) * fuel_price(i,r,t)) * GEN.l(i,v,r,h,t) * hours(h) }
                  + sum{(v,h)$[UPGRADES.l(i,v,r,t)$Sw_Upgrades],
                    (cost_vom(i,v,r,t) + heat_rate(i,v,r,t) * fuel_price(i,r,t)) * GEN.l(i,v,r,h,t) * hours(h)} ;

lcoe_pieces("gen",i,r,t)$tmodel_new(t) =
                         sum{(v,h)$[valinv(i,v,r,t)$INV.l(i,v,r,t)], GEN.l(i,v,r,h,t) * hours(h) }
                         + sum{(v,h)$[UPGRADES.l(i,v,r,t)$Sw_Upgrades], GEN.l(i,v,r,h,t) * hours(h) } ;

lcoe_pieces_nat(lcoe_cat,i,t)$tmodel_new(t) = sum{r, lcoe_pieces(lcoe_cat,i,r,t) } ;

*========================================
* REQUIREMENT PRICES AND QUANTITIES
*========================================

objfn_raw = z.l ;

load_frac_rt(r,t)$sum{(rr,h), LOAD.l(rr,h,t) } = sum{h, hours(h) * LOAD.l(r,h,t) }/ sum{(rr,h), hours(h) * LOAD.l(rr,h,t) } ;

*Load and operating reserve prices are $/MWh, and reserve margin price is $/MW/rep-day for
* capacity credit formulation and $/MW/stress-timeslice for stress period formulation.
reqt_price('load','na',r,h,t)$tmodel_new(t) =
    (1 / cost_scale) * (1 / pvf_onm(t)) * eq_supply_demand_balance.m(r,h,t) / hours(h) ;

reqt_price('oper_res',ortype,r,h,t)$tmodel_new(t) =
    (1 / cost_scale) * (1 / pvf_onm(t)) * eq_OpRes_requirement.m(ortype,r,h,t) / hours(h) ;

reqt_price('state_rps',RPSCat,r,'ann',t)$tmodel_new(t) =
    (1 / cost_scale) * (1 / pvf_onm(t)) * sum{st$r_st(r,st), eq_REC_Requirement.m(RPSCat,st,t) } ;

reqt_price('nat_gen','na',r,'ann',t)$tmodel_new(t) =
    (1 / cost_scale) * (1 / pvf_onm(t)) * eq_national_gen.m(t) ;

reqt_price('annual_cap',e,r,'ann',t)$tmodel_new(t) =
    (1 / cost_scale) * (1 / pvf_onm(t)) * eq_annual_cap.m(e,t) ;

* Capacity credit formulation ($/MW/rep-day)
reqt_price('res_marg','na',r,ccseason,t)$[Sw_PRM_CapCredit$tmodel_new(t)] =
    eq_reserve_margin.m(r,ccseason,t) * (1 / cost_scale) * (1 / pvf_onm(t)) ;
* Stress period formulation ($/MW/stress-timeslice)
reqt_price('res_marg','na',r,allh,t)$[(Sw_PRM_CapCredit=0)$tmodel_new(t)$h_stress_t(allh,t)] =
    eq_supply_demand_balance.m(r,allh,t) * (1 / cost_scale) * (1 / pvf_onm(t)) ;

reqt_price('res_marg_ann','na',r,'ann',t)$tmodel_new(t) =
* Capacity credit formulation ($/MW-yr)
      sum{ccseason, reqt_price('res_marg','na',r,ccseason,t) }$Sw_PRM_CapCredit
* Stress period formulation ($/MW-yr)
    + sum{allh$h_stress_t(allh,t), reqt_price('res_marg','na',r,allh,t) }$(Sw_PRM_CapCredit=0)
;
*The marginal on the total load constraint, eq_loadcon is converted to $/MW-yr.
*We can't convert to $/MWh because stress periods have no hours.
reqt_price('eq_loadcon','na',r,allh,t)$[tmodel_new(t)$h_t(allh,t)] =
    (1 / cost_scale) * (1 / pvf_onm(t)) * eq_loadcon.m(r,allh,t) ;


*Load and operating reserve quantities are MWh, and reserve margin quantity is MW
* Demand from production activities (H2 and DAC) doesn't count toward electricity demand
reqt_quant('load','na',r,h,t)$tmodel_new(t) =
    hours(h) * (
        LOAD.l(r,h,t)
        - sum{(p,i,v)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)$Sw_Prod],
              PRODUCE.l(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) }
    ) ;

* Capacity credit formulation
reqt_quant('res_marg','na',r,ccseason,t)$[Sw_PRM_CapCredit$tmodel_new(t)] =
    (peakdem_static_ccseason(r,ccseason,t)
*      + PEAK_FLEX.l(r,ccseason,t)
    ) * (1 + prm(r,t)) ;
* Stress period formulation
reqt_quant('res_marg','na',r,allh,t)$[(Sw_PRM_CapCredit=0)$tmodel_new(t)$h_stress_t(allh,t)] =
    LOAD.l(r,allh,t) ;

* Annual res_marg quantity is defined as the max requirement level in the year.
reqt_quant('res_marg_ann','na',r,'ann',t)$tmodel_new(t) =
* Capacity credit formulation
      smax{ccseason, reqt_quant('res_marg','na',r,ccseason,t) }$Sw_PRM_CapCredit
* Stress period formulation
    + smax{allh$h_stress_t(allh,t), reqt_quant('res_marg','na',r,allh,t) }$(Sw_PRM_CapCredit=0)
;

reqt_quant('oper_res',ortype,r,h,t)$tmodel_new(t) =
    hours(h) * (
        orperc(ortype,"or_load") * LOAD.l(r,h,t)
      + orperc(ortype,"or_wind") * sum{(i,v)$[wind(i)$valgen(i,v,r,t)],
          GEN.l(i,v,r,h,t) }
      + orperc(ortype,"or_pv")   * sum{(i,v)$[pv(i)$valcap(i,v,r,t)],
           CAP.l(i,v,r,t) }$dayhours(h)
    ) ;
reqt_quant('state_rps',RPSCat,r,'ann',t)$tmodel_new(t) =
    sum{(st,h)$r_st_rps(r,st), RecPerc(RPSCat,st,t) * hours(h) *(
        ( (LOAD.l(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]
        - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) }) * (1.0 - distloss)
        )$(RecStyle(st,RPSCat)=0)

      + ( LOAD.l(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]
        - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) }
        )$(RecStyle(st,RPSCat)=1)

      + ( sum{(i,v)$[valgen(i,v,r,t)$(not storage_standalone(i))], GEN.l(i,v,r,h,t)
          - (distloss * GEN.l(i,v,r,h,t))$(distpv(i))
          - (STORAGE_IN_GRID.l(i,v,r,h,t) * storage_eff_pvb_g(i,t))$[storage_hybrid(i)$(not csp(i))$Sw_HybridPlant] }
          - can_exports_h(r,h,t)$[(Sw_Canada=1)$sameas(RPSCat,"CES")]
        )$(RecStyle(st,RPSCat)=2)
    )} ;

reqt_quant('nat_gen','na',r,'ann',t)$tmodel_new(t) =
    national_gen_frac(t) * (
* if Sw_GenMandate = 1, then apply the fraction to the bus bar load
    (
    sum{h, LOAD.l(r,h,t) * hours(h) }
    + sum{(rr,h,trtype)$routes(rr,r,trtype,t), (tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) * hours(h)) }
    )$[Sw_GenMandate = 1]

* if Sw_GenMandate = 2, then apply the fraction to the end use load
    + (sum{h,
        hours(h) *
        ( (LOAD.l(r,h,t) - can_exports_h(r,h,t)) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) })
       })$[Sw_GenMandate = 2]
    ) ;
reqt_quant('annual_cap',e,r,'ann',t)$tmodel_new(t) = emit_cap(e,t) * load_frac_rt(r,t) ;

*We keep quantity of eq_loadcon in MW
reqt_quant('eq_loadcon','na',r,allh,t)$[tmodel_new(t)$h_t(allh,t)] = LOAD.l(r,allh,t) ;

*System-wide quantities:
reqt_quant_sys('load','na',h,t)$tmodel_new(t) = sum{r, reqt_quant('load','na',r,h,t)} ;
reqt_quant_sys('oper_res',ortype,h,t)$tmodel_new(t) = sum{r, reqt_quant('oper_res',ortype,r,h,t)} ;
reqt_quant_sys('state_rps',RPSCat,'ann',t)$tmodel_new(t) = sum{r, reqt_quant('state_rps',RPSCat,r,'ann',t)} ;
reqt_quant_sys('nat_gen','na','ann',t)$tmodel_new(t) = sum{r, reqt_quant('nat_gen','na',r,'ann',t)} ;
reqt_quant_sys('annual_cap',e,'ann',t)$tmodel_new(t) = sum{r, reqt_quant('annual_cap',e,r,'ann',t)} ;
reqt_quant_sys('res_marg','na',ccseason,t)$[Sw_PRM_CapCredit$tmodel_new(t)] =
    sum{r, reqt_quant('res_marg','na',r,ccseason,t)} ;
reqt_quant_sys('res_marg','na',allh,t)$[(Sw_PRM_CapCredit=0)$h_stress_t(allh,t)$tmodel_new(t)] =
    sum{r, reqt_quant('res_marg','na',r,allh,t)} ;
reqt_quant_sys('res_marg_ann','na','ann',t)$tmodel_new(t) = sum{r, reqt_quant('res_marg_ann','na',r,'ann',t)} ;

*System-wide average prices:
reqt_price_sys('load','na',h,t)$reqt_quant_sys('load','na',h,t) =
    sum{r, reqt_price('load','na',r,h,t) * reqt_quant('load','na',r,h,t)}/
    reqt_quant_sys('load','na',h,t) ;

reqt_price_sys('oper_res',ortype,h,t)$reqt_quant_sys('oper_res',ortype,h,t) =
    sum{r, reqt_price('oper_res',ortype,r,h,t) * reqt_quant('oper_res',ortype,r,h,t)}/
    reqt_quant_sys('oper_res',ortype,h,t) ;

reqt_price_sys('state_rps',RPSCat,'ann',t)$reqt_quant_sys('state_rps',RPSCat,'ann',t) =
    sum{r, reqt_price('state_rps',RPSCat,r,'ann',t) * reqt_quant('state_rps',RPSCat,r,'ann',t)}/
    reqt_quant_sys('state_rps',RPSCat,'ann',t) ;

reqt_price_sys('nat_gen','na','ann',t)$reqt_quant_sys('nat_gen','na','ann',t) =
    sum{r, reqt_price('nat_gen','na',r,'ann',t) * reqt_quant('nat_gen','na',r,'ann',t)}/
    reqt_quant_sys('nat_gen','na','ann',t) ;

reqt_price_sys('annual_cap',e,'ann',t)$reqt_quant_sys('annual_cap',e,'ann',t) =
    sum{r, reqt_price('annual_cap',e,r,'ann',t) * reqt_quant('annual_cap',e,r,'ann',t)}/
    reqt_quant_sys('annual_cap',e,'ann',t) ;

reqt_price_sys('res_marg','na',ccseason,t)$[Sw_PRM_CapCredit$reqt_quant_sys('res_marg','na',ccseason,t)] =
    sum{r, reqt_price('res_marg','na',r,ccseason,t) * reqt_quant('res_marg','na',r,ccseason,t)}/
    reqt_quant_sys('res_marg','na',ccseason,t) ;
reqt_price_sys('res_marg','na',allh,t)$[(Sw_PRM_CapCredit=0)$h_stress_t(allh,t)$reqt_quant_sys('res_marg','na',allh,t)] =
    sum{r, reqt_price('res_marg','na',r,allh,t) * reqt_quant('res_marg','na',r,allh,t)}/
    reqt_quant_sys('res_marg','na',allh,t) ;

reqt_price_sys('res_marg_ann','na','ann',t)$reqt_quant_sys('res_marg_ann','na','ann',t) =
    sum{r, reqt_price('res_marg_ann','na',r,'ann',t) * reqt_quant('res_marg_ann','na',r,'ann',t)}/
    reqt_quant_sys('res_marg_ann','na','ann',t) ;

load_rt(r,t)$tmodel_new(t) = sum{h, hours(h) * load_exog(r,h,t) } ;

load_stress(r,allh,t)$[tmodel_new(t)$h_stress_t(allh,t)] = LOAD.l(r,allh,t) ;

co2_price(t)$tmodel_new(t) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_annual_cap.m("CO2",t) ;

rggi_price(t)$tmodel_new(t) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_RGGI_cap.m(t) ;
rggi_quant(t)$tmodel_new(t) = RGGI_cap(t) ;

state_cap_and_trade_price(st,t)$tmodel_new(t) =
    (1 / cost_scale) * (1 / pvf_onm(t))
    * eq_state_cap.m(st,t) ;

state_cap_and_trade_quant(st,t)$tmodel_new(t) =
    state_cap(st,t) ;

tran_hurdle_cost_ann(r,rr,trtype,t)$[tmodel_new(t)$routes(r,rr,trtype,t)$cost_hurdle(r,rr,t)] =
    sum{h, hours(h) * cost_hurdle(r,rr,t) * FLOW.l(r,rr,h,t,trtype) } ;

*========================================
* RPS, CES, AND TAX CREDIT OUTPUTS
*========================================

rec_outputs(RPSCat,i,st,ast,t)$[stfeas(st)$(stfeas(ast) or sameas(ast,"voluntary"))$tmodel_new(t)] = RECS.l(RPSCat,i,st,ast,t) ;
acp_purchases_out(rpscat,st,t) = ACP_PURCHASES.l(RPSCat,st,t) ;
ptc_out(i,v,t)$[tmodel_new(t)$ptc_value_scaled(i,v,t)] = ptc_value_scaled(i,v,t) * tc_phaseout_mult(i,v,t) ;

*========================================
* FUEL PRICES AND QUANTITIES
*========================================

* The marginal biomass fuel price is derived from the linear program constraint marginals
* Case 1: the resource of a biomass class is NOT exhausted, i.e., BIOUSED.l(bioclass) < biosupply(bioclass)
*    Marginal Biomass Price = eq_bioused.m
* Case 2: the resource of one or more biomass classes ARE exhausted, i.e., BIOUSED.l(bioclass) = biosupply(bioclass)
*    Marginal Biomass Price = maximum difference between eq_bioused.m and eq_biousedlimit.m(bioclass) across all biomass classes in a region

repbioprice(r,t)$tmodel_new(t) = max{0, smax{bioclass$BIOUSED.l(bioclass,r,t), eq_bioused.m(r,t) -
                                              sum{usda_region$r_usda(r,usda_region), eq_biousedlimit.m(bioclass,usda_region,t) } } } / pvf_onm(t) ;

* quantity of biomass used (convert from mmBTU to dry tons using biomass energy content)
bioused_out(bioclass,r,t)$tmodel_new(t) = BIOUSED.l(bioclass,r,t) / bio_energy_content ;
bioused_usda(bioclass,usda_region,t)$tmodel_new(t) = sum{r$r_usda(r,usda_region), bioused_out(bioclass,r,t) } ;

* 1e9 converts from MMBtu to Quads
repgasquant(cendiv,t)$[(Sw_GasCurve = 0 or Sw_GasCurve = 3)$tmodel_new(t)] =
    sum{(gb,h), GASUSED.l(cendiv,gb,h,t) * hours(h) } * gas_scale/ 1e9 ;

repgasquant(cendiv,t)$[(Sw_GasCurve = 1 or Sw_GasCurve = 2)$tmodel_new(t)] =
    ( sum{(i,v,r,h)$[r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t)}
    + sum{(v,r,h)$[valcap("dac_gas",v,r,t)$r_cendiv(r,cendiv)],
          hours(h) * dac_gas_cons_rate("dac_gas",v,t) * PRODUCE.l("DAC","dac_gas",v,r,h,t) }$Sw_DAC_Gas
    + sum{(p,i,v,r,h)$[r_cendiv(r,cendiv)$valcap(i,v,r,t)$smr(i)],
          hours(h) * smr_methane_rate * PRODUCE.l(p,i,v,r,h,t) }$Sw_H2
    ) / 1e9 ;

repgasquant_irt(i,r,t)$tmodel_new(t) =
    ( sum{(v,h)$[valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t)  }
    + sum{(v,h)$[valcap("dac_gas",v,r,t)],
          hours(h) * dac_gas_cons_rate("dac_gas",v,t) * PRODUCE.l("DAC","dac_gas",v,r,h,t) }$Sw_DAC_Gas
    + sum{(p,v,h)$[valcap(i,v,r,t)$smr(i)],
          hours(h) * smr_methane_rate * PRODUCE.l(p,i,v,r,h,t) }$Sw_H2
    ) / 1e9 ;

repgasquant_nat(t)$tmodel_new(t) = sum{cendiv, repgasquant(cendiv,t) } ;

*for reported gasprice (not that used to compute system costs)
*scale back to $ / mmbtu
repgasprice(cendiv,t)$[(Sw_GasCurve = 0)$tmodel_new(t)$repgasquant(cendiv,t)] =
    smax{gb$[sum{h, GASUSED.l(cendiv,gb,h,t) }], gasprice(cendiv,gb,t) } / gas_scale ;

repgasprice(cendiv,t)$[(Sw_GasCurve = 2)$tmodel_new(t)$repgasquant(cendiv,t)] =
    sum{(i,v,r,h)$[r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h)*heat_rate(i,v,r,t)*fuel_price(i,r,t)*GEN.l(i,v,r,h,t)
       } / (repgasquant(cendiv,t) * 1e9) ;

repgasprice_r(r,t)$[(Sw_GasCurve = 0 or Sw_GasCurve = 2)$tmodel_new(t)] = sum{cendiv$r_cendiv(r,cendiv), repgasprice(cendiv,t) } ;

repgasprice_r(r,t)$[(Sw_GasCurve = 1)$tmodel_new(t)] =
              ( sum{(h,cendiv),
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(r,cendiv) *
                   hours(h) } / sum{h, hours(h) }

              + smax((fuelbin,cendiv)$[VGASBINQ_REGIONAL.l(fuelbin,cendiv,t)$r_cendiv(r,cendiv)], gasbinp_regional(fuelbin,cendiv,t) )

              + smax(fuelbin$VGASBINQ_NATIONAL.l(fuelbin,t), gasbinp_national(fuelbin,t) )
              ) ;

repgasprice(cendiv,t)$[(Sw_GasCurve = 1)$tmodel_new(t)$repgasquant(cendiv,t)] =
    sum{(i,r)$r_cendiv(r,cendiv), repgasprice_r(r,t) * repgasquant_irt(i,r,t) } / repgasquant(cendiv,t) ;

repgasprice_nat(t)$[tmodel_new(t)$sum{cendiv, repgasquant(cendiv,t) }] =
    sum{cendiv, repgasprice(cendiv,t) * repgasquant(cendiv,t) }
    / sum{cendiv, repgasquant(cendiv,t) } ;

*========================================
* NATURAL GAS FUEL COSTS
*========================================

gasshare_ba(r,cendiv,t)$[r_cendiv(r,cendiv)$tmodel_new(t)$repgasquant(cendiv,t)] =
                 sum{i$[valgen_irt(i,r,t)$gas(i)],repgasquant_irt(i,r,t) / repgasquant(cendiv,t) } ;

gasshare_techba(i,r,cendiv,t)$[r_cendiv(r,cendiv)$tmodel_new(t)$repgasquant(cendiv,t)$gas(i)] =
                 repgasquant_irt(i,r,t) / repgasquant(cendiv,t) ;

gasshare_cendiv(cendiv,t)$[sum{cendiv2,repgasquant(cendiv2,t)}] = repgasquant(cendiv,t) / sum{cendiv2,repgasquant(cendiv2,t)} ;

gascost_cendiv(cendiv,t)$tmodel_new(t) =
*cost of natural gas for Sw_GasCurve = 2 (static natural gas prices)
              + sum{(i,v,r,h)$[r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)
                              $[not bio(i)]$[not cofire(i)]$[Sw_GasCurve = 2]],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN.l(i,v,r,h,t) }

*cost of natural gas for Sw_GasCurve = 0 (census division supply curves natural gas prices)
              + sum{gb, sum{h,hours(h) * GASUSED.l(cendiv,gb,h,t) } * gasprice(cendiv,gb,t)
                   }$[Sw_GasCurve = 0]

*cost of natural gas for Sw_GasCurve = 3 (national supply curve for natural gas prices with census division multipliers)
              + sum{(h,gb), hours(h) * GASUSED.l(cendiv,gb,h,t)
                   * gasadder_cd(cendiv,t,h) + gasprice_nat_bin(gb,t)
                   }$[Sw_GasCurve = 3]
*cost of natural gas for Sw_GasCurve = 1 (national and census division supply curves for natural gas prices)
*first - anticipated costs of gas consumption given last year's amount
              + (sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)],
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(r,cendiv) *
                   hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t) }
*second - adjustments based on changes from last year's consumption at the regional and national level
              + sum{(fuelbin),
                   gasbinp_regional(fuelbin,cendiv,t) * VGASBINQ_REGIONAL.l(fuelbin,cendiv,t) }

              + sum{(fuelbin),
                   gasbinp_national(fuelbin,t) * VGASBINQ_NATIONAL.l(fuelbin,t) } * gasshare_cendiv(cendiv,t)

              )$[Sw_GasCurve = 1];

*========================================
* BIOFUEL COSTS
*========================================

bioshare_techba(i,r,t)$[(cofire(i) or bio(i))$tmodel_new(t)] =
*  biofuel-based generation of tech i in the BA (biopower + cofire)
                ((   sum{(v,h)$[valgen(i,v,r,t)$bio(i)], hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t) }
                   + sum{(v,h)$[cofire(i)$valgen(i,v,r,t)], bio_cofire_perc * hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t) }
                 ) /
*  biofuel-based generation of all techs in the BA (biopower + cofire)
                 (   sum{(ii,v,h)$[valgen(ii,v,r,t)$bio(ii)], hours(h) * heat_rate(ii,v,r,t) * GEN.l(ii,v,r,h,t) }
                   + sum{(ii,v,h)$[cofire(ii)$valgen(ii,v,r,t)], bio_cofire_perc * hours(h) * heat_rate(ii,v,r,t) * GEN.l(ii,v,r,h,t) }
                 )
                )$[  sum{(ii,v,h)$[valgen(ii,v,r,t)$bio(ii)], hours(h) * heat_rate(ii,v,r,t) * GEN.l(ii,v,r,h,t) }
                   + sum{(ii,v,h)$[cofire(ii)$valgen(ii,v,r,t)], bio_cofire_perc * hours(h) * heat_rate(ii,v,r,t) * GEN.l(ii,v,r,h,t) }
                  ]
;

*=========================
* GENERATION
*=========================

* Calculate generation and include charging, pumping, and production as negative values
gen_h(i,r,h,t)$[tmodel_new(t)$valgen_irt(i,r,t)] =
  sum{v$valgen(i,v,r,t), GEN.l(i,v,r,h,t)
* less storage charging
  - STORAGE_IN.l(i,v,r,h,t)$[storage_standalone(i) or hyd_add_pump(i)]}
* less load from hydrogen production
  - sum{(v,p)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)], PRODUCE.l(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t)}$Sw_Prod
;
* A small amount of upv capacity is actually csp-ns, so convert it back now.
* UPV capacity is already in MWac at this point (matching csp-ns),
* so don't need to account for ILR.
gen_h("csp-ns",r,h,t)$[cap_cspns(r,t)$tmodel_new(t)]
    = cap_cspns(r,t) * m_cf("upv_6","new1",r,h,t) ;
* We have to take csp-ns generation from somewhere, so take it from upv_6 (which all the
* csp-ns-containing regions have)
gen_h("upv_6",r,h,t)$[cap_cspns(r,t)$tmodel_new(t)]
    = gen_h("upv_6",r,h,t) - gen_h("csp-ns",r,h,t) ;
* Make sure it doesn't go negative, just in case
gen_h("upv_6",r,h,t)$[cap_cspns(r,t)$tmodel_new(t)$(gen_h("upv_6",r,h,t) < 0)] = 0 ;
gen_h_nat(i,h,t)$tmodel_new(t) = sum{r, gen_h(i,r,h,t) } ;

* Do it again for stress periods
gen_h_stress(i,r,allh,t)$[tmodel_new(t)$valgen_irt(i,r,t)$h_stress_t(allh,t)] =
  sum{v$valgen(i,v,r,t), GEN.l(i,v,r,allh,t)
* less storage charging
      - STORAGE_IN.l(i,v,r,allh,t)$[storage_standalone(i) or hyd_add_pump(i)] }
* less load from hydrogen production
  - sum{(v,p)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)],
        PRODUCE.l(p,i,v,r,allh,t) / prod_conversion_rate(i,v,r,t)}$Sw_Prod
;
gen_h_stress_nat(i,allh,t)$[tmodel_new(t)$h_stress_t(allh,t)] = sum{r, gen_h_stress(i,r,allh,t) } ;

gen_ann(i,r,t)$tmodel_new(t) = sum{h, gen_h(i,r,h,t) * hours(h) } ;
gen_ann_nat(i,t)$tmodel_new(t) = sum{r, gen_ann(i,r,t) } ;

* Report generation without the charging and production included as above
gen_ivrt(i,v,r,t)$valgen(i,v,r,t) = sum{h, GEN.l(i,v,r,h,t) * hours(h) } ;
gen_ivrt_uncurt(i,v,r,t)$[(vre(i) or storage_hybrid(i)$(not csp(i)))$valgen(i,v,r,t)] =
  sum{h, m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) * hours(h) } ;

* Report generation that will be used as a denominator in outputs, where VRE uses uncurtailed gen and storage uses GEN
gen_uncurtailed(i,r,t)$[valgen_irt(i,r,t)$(not vre(i))] = sum{v, gen_ivrt(i,v,r,t) } ;
gen_uncurtailed(i,r,t)$[valgen_irt(i,r,t)$vre(i)] = sum{v, gen_ivrt_uncurt(i,v,r,t) } ;
gen_uncurtailed_nat(i,t)$tmodel_new(t) = sum{r, gen_uncurtailed(i,r,t) } ;

* Storage outputs
stor_inout(i,v,r,t,"in")$[valgen(i,v,r,t)$storage(i)$[not storage_hybrid(i)$(not csp(i))]] = sum{h, STORAGE_IN.l(i,v,r,h,t) * hours(h) } ;
stor_inout(i,v,r,t,"out")$[valgen(i,v,r,t)$storage(i)] = gen_ivrt(i,v,r,t) ;
stor_in(i,v,r,h,t)$[storage(i)$valgen(i,v,r,t)$(not storage_hybrid(i)$(not csp(i)))] = STORAGE_IN.l(i,v,r,h,t) ;
stor_out(i,v,r,h,t)$[storage(i)$valgen(i,v,r,t)] = GEN.l(i,v,r,h,t) ;
stor_level(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)] = STORAGE_LEVEL.l(i,v,r,h,t) ;
stor_interday_level(i,v,r,allszn,t)$[valgen(i,v,r,t)$storage_interday(i)] = STORAGE_INTERDAY_LEVEL.l(i,v,r,allszn,t) ;
stor_interday_dispatch(i,v,r,h,t)$[valgen(i,v,r,t)$storage_interday(i)] = STORAGE_INTERDAY_DISPATCH.l(i,v,r,h,t) ;

*=====================================================================
* WATER ACCOUNTING, CAPACITY, NEW CAPACITY, AND RETIRED CAPACITY
*=====================================================================
water_withdrawal_ivrt(i,v,r,t)$valgen(i,v,r,t) = sum{h$valgen(i,v,r,t), WAT.l(i,v,"with",r,h,t) } ;
water_consumption_ivrt(i,v,r,t)$valgen(i,v,r,t) = sum{h$valgen(i,v,r,t), WAT.l(i,v,"cons",r,h,t) } ;

watcap_ivrt(i,v,r,t)$valcap(i,v,r,t) = WATCAP.l(i,v,r,t) ;
watcap_out(i,r,t)$valcap_irt(i,r,t) = sum{v$valcap(i,v,r,t), WATCAP.l(i,v,r,t) } ;
watcap_new_out(i,r,t)$[valcap_irt(i,r,t)$i_water_cooling(i)] =
  sum{h$h_rep(h), 
    hours(h)
    * sum{w$[i_w(i,w)], 
      water_rate(i,w) } 
      * ( sum{v$valinv(i,v,r,t), INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)} 
        + sum{v$valcap(i,v,r,t), 
          (1-upgrade_derate(i,v,r,t)) * (UPGRADES.l(i,v,r,t) - UPGRADES_RETIRE.l(i,v,r,t))}$[upgrade(i)$Sw_Upgrades] ) 
    * (1 + sum{(v,szn), h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
  } / 1E6
  + sum{v$[psh(i)$valinv(i,v,r,t)], WATCAP.l(i,v,r,t)} ;

watcap_new_ivrt(i,v,r,t)$[valcap(i,v,r,t)$i_water_cooling(i)] =
  sum{h$h_rep(h), 
    hours(h)
    * sum{w$[i_w(i,w)], 
      water_rate(i,w) }
      * ( [INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)]$valinv(i,v,r,t) 
        + [(1-upgrade_derate(i,v,r,t)) * (UPGRADES.l(i,v,r,t) - UPGRADES_RETIRE.l(i,v,r,t))]$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades] )
    * (1 + sum{szn, h_szn(h,szn) * seas_cap_frac_delta(i,v,r,szn,t)})
  } / 1E6
  + WATCAP.l(i,v,r,t)$psh(i) ;

watcap_new_ann_out(i,v,r,t)$watcap_new_ivrt(i,v,r,t) = watcap_new_ivrt(i,v,r,t) / (yeart(t) - sum(tt$tprev(t,tt), yeart(tt))) ;

* --- Water Capacity Retirements ---*
watret_out(i,r,t)$[(not tfirst(t))] = sum{tt$tprev(t,tt), watcap_out(i,r,tt)} - watcap_out(i,r,t) + watcap_new_out(i,r,t) ;
watret_out(i,r,t)$[abs(watret_out(i,r,t)) < 1e-6] = 0 ;

watret_ivrt(i,v,r,t)$[(not tfirst(t))] = sum{tt$tprev(t,tt), watcap_ivrt(i,v,r,tt)} - watcap_ivrt(i,v,r,t) + watcap_new_ivrt(i,v,r,t) ;
watret_ivrt(i,v,r,t)$[(abs(watret_ivrt(i,v,r,t)) < 1e-6)] = 0 ;

watret_ann_out(i,v,r,t)$watret_ivrt(i,v,r,t) = watret_ivrt(i,v,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;

*=========================
* Operating Reserves
*=========================

opres_supply_h(ortype,i,r,h,t)$[tmodel_new(t)$reserve_frac(i,ortype)] =
      sum{v, OPRES.l(ortype,i,v,r,h,t) } ;


opres_supply(ortype,i,r,t)$[tmodel_new(t)$reserve_frac(i,ortype)] =
      sum{h, hours(h) * opRes_supply_h(ortype,i,r,h,t) } ;

* total opres trade
opres_trade(ortype,r,rr,t)$[opres_routes(r,rr,t)$tmodel_new(t)] =
      sum{h, hours(h) * OPRES_FLOW.l(ortype,r,rr,h,t) } ;

*=========================
* LOSSES AND CURTAILMENT
*=========================

gen_new_uncurt(i,r,h,t)$[(vre(i) or storage_hybrid(i)$(not csp(i)))$valcap_irt(i,r,t)] =
      sum{v$valinv(i,v,r,t), (INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)) * m_cf(i,v,r,h,t) * hours(h) }
;

* Formulation follows eq_curt_gen_balance(r,h,t); since it uses =g= there may be extra curtailment
* beyond CURT.l(r,h,t) so we recalculate as (availability - generation - operating reserves)
curt_h(r,h,t)$tmodel_new(t) =
      sum{(i,v)$[valcap(i,v,r,t)$(vre(i) or storage_hybrid(i)$(not csp(i)))],
          m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) }
    - sum{(i,v)$[valgen(i,v,r,t)$vre(i)], GEN.l(i,v,r,h,t) }
    - sum{(i,v)$[valgen(i,v,r,t)$storage_hybrid(i)$(not csp(i))], GEN_PLANT.l(i,v,r,h,t) }$Sw_HybridPlant
    - sum{(ortype,i,v)$[Sw_OpRes$opres_h(h)$reserve_frac(i,ortype)$valgen(i,v,r,t)$vre(i)],
          OPRES.l(ortype,i,v,r,h,t) }
;

curt_ann(r,t)$tmodel_new(t) = sum{h, curt_h(r,h,t) * hours(h) } ;

curt_tech(i,r,t)$[tmodel_new(t)$vre(i)] =
      sum{(v,h)$valcap(i,v,r,t),
          m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) * hours(h) }
    - sum{(v,h)$valgen(i,v,r,t),
          GEN.l(i,v,r,h,t) * hours(h) }
    - sum{(ortype,v,h)$[Sw_OpRes$opres_h(h)$reserve_frac(i,ortype)$valgen(i,v,r,t)],
          OPRES.l(ortype,i,v,r,h,t) * hours(h) }
;

curt_rate_tech(i,r,t)$[tmodel_new(t)$vre(i)$(gen_ann(i,r,t) + curt_tech(i,r,t))] =
    curt_tech(i,r,t) / (gen_ann(i,r,t) + curt_tech(i,r,t))
;

curt_rate(t)
    $[tmodel_new(t)
    $(sum{(i,r)$[vre(i) or storage_hybrid(i)$(not csp(i))], gen_ann(i,r,t) } + sum{r, curt_ann(r,t) })]
    = sum{r, curt_ann(r,t) }
      / (sum{(i,r)$[vre(i) or storage_hybrid(i)$(not csp(i))], gen_ann(i,r,t) } + sum{r, curt_ann(r,t) }) ;

losses_ann('storage',t)$tmodel_new(t) = sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)], STORAGE_IN.l(i,v,r,h,t) * hours(h) }
                          - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)], GEN.l(i,v,r,h,t) * hours(h) } ;

losses_ann('trans',t)$tmodel_new(t) =
  sum{(rr,r,h,trtype)$routes(rr,r,trtype,t),
      (tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) * hours(h)) 
      + ((CONVERSION.l(r,h,"AC","VSC",t) + CONVERSION.l(r,h,"VSC","AC",t))* (1 - converter_efficiency_vsc) * hours(h))$[val_converter(r,t)$Sw_VSC]
      } ;

losses_ann('curt',t)$tmodel_new(t) =  sum{r, curt_ann(r,t) } ;

losses_ann('load',t)$tmodel_new(t) = sum{(r,h), LOAD.l(r,h,t) * hours(h) }  ;

losses_tran_h(rr,r,h,trtype,t)$[routes(r,rr,trtype,t)$tmodel_new(t)]
    = tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) 
    + ((CONVERSION.l(r,h,"AC","VSC",t) + CONVERSION.l(r,h,"VSC","AC",t))* (1 - converter_efficiency_vsc))$[val_converter(r,t)$Sw_VSC] ;

*=========================
* CAPACITY
*=========================

cap_deg_ivrt(i,v,r,t)$valcap(i,v,r,t) = CAP.l(i,v,r,t) / ilr(i) ;

cap_ivrt(i,v,r,t)$[(not (upv(i) or wind(i)))$valcap(i,v,r,t)] = cap_deg_ivrt(i,v,r,t) ;
*upv, and wind have degradation, so use INV rather than CAP to get the reported capacity
cap_ivrt(i,v,r,t)$[(upv(i) or wind(i))$valcap(i,v,r,t)] = (
  m_capacity_exog(i,v,r,t)$tmodel_new(t)
  + sum{tt$[inv_cond(i,v,r,t,tt)$[tmodel(tt) or tfix(tt)]],
        INV.l(i,v,r,tt) + INV_REFURB.l(i,v,r,tt)$[refurbtech(i)$Sw_Refurb]}) / ilr(i) ;

cap_out(i,r,t)$[valcap_irt(i,r,t)$tmodel_new(t)] = sum{v$valcap(i,v,r,t), cap_ivrt(i,v,r,t) } ;
* A small amount of upv capacity is actually csp-ns, so convert it back now.
* UPV capacity is already in MWac at this point (matching csp-ns),
* so don't need to account for ILR
cap_out("csp-ns",r,t)$[cap_cspns(r,t)$tmodel_new(t)] = cap_cspns(r,t) ;
* We have to take csp-ns capacity from somewhere, so take it from upv_6 (which all the
* csp-ns-containing regions have)
cap_out("upv_6",r,t)$[cap_cspns(r,t)$tmodel_new(t)] = cap_out("upv_6",r,t) - cap_cspns(r,t) ;
* Make sure it doesn't go negative, just in case
cap_out("upv_6",r,t)$[cap_cspns(r,t)$tmodel_new(t)$(cap_out("upv_6",r,t) < 0)] = 0 ;
cap_nat(i,t)$tmodel_new(t) = sum{r, cap_out(i,r,t) } ;

* Exogenous capacity (used by reeds_to_rev)
cap_exog(i,v,r,t)$tmodel_new(t) = m_capacity_exog(i,v,r,t) ;

*=========================
* NEW CAPACITY
*=========================

cap_new_out(i,r,t)$[(not tfirst(t))$valcap_irt(i,r,t)] = [
  sum{v$valinv(i,v,r,t), 
    INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) }
  + sum{v$valcap(i,v,r,t), 
    (1 - upgrade_derate(i,v,r,t)) * (UPGRADES.l(i,v,r,t) - UPGRADES_RETIRE.l(i,v,r,t))}$[upgrade(i)$Sw_Upgrades]
  ] / ilr(i) ;

cap_new_out("distpv",r,t)$[valcap_irt("distpv",r,t)$(not tfirst(t))] = cap_out("distpv",r,t) - sum{tt$tprev(t,tt), cap_out("distpv",r,tt) } ;
cap_new_ann(i,r,t)$cap_new_out(i,r,t) = cap_new_out(i,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;
cap_new_ann_nat(i,t)$tmodel_new(t) = sum{r, cap_new_ann(i,r,t) } ;
cap_new_bin_out(i,v,r,t,rscbin)$[rsc_i(i)$valinv(i,v,r,t)] = INV_RSC.l(i,v,r,rscbin,t) / ilr(i) ;
cap_new_bin_out(i,v,r,t,"bin1")$[(not rsc_i(i))$valinv(i,v,r,t)] = INV.l(i,v,r,t) / ilr(i) ;
cap_new_ivrt(i,v,r,t)$[(not tfirst(t))$valcap(i,v,r,t)] = [
  [INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)]$valinv(i,v,r,t)
  + [(1-upgrade_derate(i,v,r,t)) * (UPGRADES.l(i,v,r,t) - UPGRADES_RETIRE.l(i,v,r,t))]$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades] 
 ] / ilr(i) ;
cap_new_ivrt("distpv",v,r,t)$[not tfirst(t)$valcap("distpv",v,r,t)] = cap_ivrt("distpv",v,r,t) - sum{tt$tprev(t,tt), cap_ivrt("distpv",v,r,tt) } ;
cap_new_ivrt_refurb(i,v,r,t)$valinv(i,v,r,t) = INV_REFURB.l(i,v,r,t) / ilr(i) ;

*** Capacity by reV site
site_spurinv(x,t)$[tmodel_new(t)$xfeas(x)] = INV_SPUR.l(x,t) ;
site_spurcap(x,t)$[tmodel_new(t)$xfeas(x)] = CAP_SPUR.l(x,t) ;

site_cap(i,x,t)$[tmodel_new(t)$sum{(r,rscbin), spurline_sitemap(i,r,rscbin,x)}] =
  sum{(v,r,rscbin,tt)
      $[spurline_sitemap(i,r,rscbin,x)
      $cap_new_bin_out(i,v,r,tt,rscbin)
      $(yeart(tt) <= yeart(t))],
* Multiply by ILR to get DC capacity for PV
      cap_new_bin_out(i,v,r,tt,rscbin) * ilr(i)
  } ;

site_gir(i,x,t)$[site_cap(i,x,t)$site_spurcap(x,t)] = site_cap(i,x,t) / site_spurcap(x,t) ;

site_pv_fraction(x,t)$sum{i$spur_techs(i), site_cap(i,x,t)} =
  sum{i$upv(i), site_cap(i,x,t)} / (sum{i$spur_techs(i), site_cap(i,x,t)}) ;

site_hybridization(x,t)$site_pv_fraction(x,t) = abs(1 - 2 * abs(site_pv_fraction(x,t) - 0.5)) ;

*=========================
* AVAILABLE CAPACITY
*=========================
cap_avail(i,r,t,rscbin)$[tmodel_new(t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)] =
    m_rsc_dat(r,i,rscbin,"cap")
    + hyd_add_upg_cap(r,i,rscbin,t)$(Sw_HydroCapEnerUpgradeType=1)
    + rsc_evmc(i,r,"cap",rscbin,t)

- (
    sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) < yeart(t))$rsc_agg(i,ii)],
         INV_RSC.l(ii,v,r,rscbin,tt) * resourcescaler(ii) }

    + sum{(ii,v,tt)$[tfirst(tt)$rsc_agg(i,ii)$exog_rsc(i)],
         capacity_exog_rsc(ii,v,r,rscbin,tt) }
);

capacity_offline(i,r,allh,t)
    $[valcap_irt(i,r,t)$tmodel_new(t)$(h_stress_t(allh,t) or h_rep(allh))] =
    cap_out(i,r,t) * (1 - avail(i,r,allh)) ;

forced_outage(i) = sum{(r,h), outage_forced_h(i,r,h) * hours(h) } / sum{(r,h), hours(h) } ;
planned_outage(i) = sum{h, outage_scheduled_h(i,h) * hours(h) } / sum{h, hours(h) } ;

*=========================
* UPGRADED CAPACITY
*=========================

cap_upgrade(i,r,t)$[upgrade(i)$valcap_irt(i,r,t)] = sum{v, (1-upgrade_derate(i,v,r,t)) * UPGRADES.l(i,v,r,t) } ;
cap_upgrade_ivrt(i,v,r,t)$[valcap(i,v,r,t)$upgrade(i)$Sw_Upgrades] = (1-upgrade_derate(i,v,r,t)) * UPGRADES.l(i,v,r,t) ;

*=========================
* RETIRED CAPACITY
*=========================

ret_ivrt(i,v,r,t)$[(not tfirst(t))] = 
    sum{tt$tprev(t,tt), cap_ivrt(i,v,r,tt) } - cap_ivrt(i,v,r,t) + cap_new_ivrt(i,v,r,t) 
    - sum{ii$upgrade_from(ii,i), UPGRADES.l(ii,v,r,t) } ;
ret_ivrt(i,v,r,t)$[abs(ret_ivrt(i,v,r,t)) < 1e-6] = 0 ;

ret_out(i,r,t)$[(not tfirst(t))] = sum{v, ret_ivrt(i,v,r,t) } ;
ret_out(i,r,t)$[abs(ret_out(i,r,t)) < 1e-6] = 0 ;
ret_ann(i,r,t)$ret_out(i,r,t) = ret_out(i,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;
ret_ann_nat(i,t)$tmodel_new(t) = sum{r, ret_ann(i,r,t) } ;

*==================================
* BINNED STORAGE CAPACITY
*==================================

cap_sdbin_out(i,r,ccseason,sdbin,t)$valcap_irt(i,r,t) = sum{v, CAP_SDBIN.l(i,v,r,ccseason,sdbin,t)} ;

* energy capacity of storage
stor_energy_cap(i,v,r,t)$[tmodel_new(t)$valcap(i,v,r,t)] =
        storage_duration(i) * CAP.l(i,v,r,t) * (1$CSP_Storage(i) + 1$psh(i) + bcr(i)$[battery(i) or storage_hybrid(i)$(not csp(i))]) ;

* add PSH energy capacity to cap_energy_ivrt
cap_energy_ivrt(i,v,r,t)$[valcap(i,v,r,t)$psh(i)] = CAP.l(i,v,r,t) * storage_duration(i) ;

* battery storage duration
storage_duration_out(i,v,r,t)$[valcap(i,v,r,t)$battery(i)$CAP.l(i,v,r,t)] = 
        CAP_ENERGY.l(i,v,r,t) / CAP.l(i,v,r,t) ;

*==================================
* CAPACITY CREDIT AND FIRM CAPACITY
*==================================

cc_all_out(i,v,r,ccseason,t)$tmodel_new(t) =
    cc_int(i,v,r,ccseason,t)$[(vre(i) or csp(i) or storage(i) or storage_hybrid(i)$(not csp(i)))$valcap(i,v,r,t)] +
    m_cc_mar(i,r,ccseason,t)$[(vre(i) or csp(i) or storage(i) or storage_hybrid(i)$(not csp(i)))$valinv_init(i,v,r,t)]
;

cap_new_cc(i,r,ccseason,t)$[(vre(i) or storage(i) or storage_hybrid(i)$(not csp(i)))$valcap_irt(i,r,t)] = sum{v$ivt(i,v,t),cap_new_ivrt(i,v,r,t) } ;

cc_new(i,r,ccseason,t)$[valcap_irt(i,r,t)$cap_new_cc(i,r,ccseason,t)] = sum{v$ivt(i,v,t), cc_all_out(i,v,r,ccseason,t) } ;

cap_firm(i,r,ccseason,t)$[valcap_irt(i,r,t)$[not consume(i)]$tmodel_new(t)$Sw_PRM_CapCredit] =
      sum{v$[(not vre(i))$(not hydro(i))$(not storage(i))$(not storage_hybrid(i)$(not csp(i)))$valcap(i,v,r,t)],
          CAP.l(i,v,r,t) * (1 + ccseason_cap_frac_delta(i,v,r,ccseason,t)) }
    + cc_old(i,r,ccseason,t)
    + sum{v$[(vre(i) or csp(i) or storage_hybrid(i)$(not csp(i)))$valinv(i,v,r,t)],
         m_cc_mar(i,r,ccseason,t) * (INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)$[refurbtech(i)$Sw_Refurb]) }
    + sum{v$[(vre(i) or csp(i) or storage_hybrid(i)$(not csp(i)))$valcap(i,v,r,t)],
            cc_int(i,v,r,ccseason,t) * CAP.l(i,v,r,t) }
    + cc_excess(i,r,ccseason,t)$[(vre(i) or csp(i) or storage_hybrid(i)$(not csp(i)))]
    + sum{(v,h)$[hydro_nd(i)$valgen(i,v,r,t)$h_ccseason_prm(h,ccseason)],
         GEN.l(i,v,r,h,t) }
    + sum{v$[hydro_d(i)$valcap(i,v,r,t)],
         CAP.l(i,v,r,t) * cap_hyd_ccseason_adj(i,ccseason,r) * (1 + hydro_capcredit_delta(i,t)) }
    + sum{(v,sdbin)$[valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))], CAP_SDBIN.l(i,v,r,ccseason,sdbin,t) * cc_storage(i,sdbin) }
    + sum{(v,sdbin)$[valcap(i,v,r,t)$storage_hybrid(i)], CAP_SDBIN.l(i,v,r,ccseason,sdbin,t) * cc_storage(i,sdbin) * hybrid_cc_derate(i,r,ccseason,sdbin,t) } ;

* Capacity trading to meet PRM
captrade(r,rr,trtype,ccseason,t)$[routes(r,rr,trtype,t)$routes_prm(r,rr)$tmodel_new(t)] = PRMTRADE.l(r,rr,trtype,ccseason,t) ;

*========================================
* REVENUE LEVELS
*========================================

revenue('load',i,r,t)$valgen_irt(i,r,t) = sum{(v,h)$valgen(i,v,r,t),
  GEN.l(i,v,r,h,t) * hours(h) * reqt_price('load','na',r,h,t) } ;

*revenue from storage charging (storage charging from curtailment recovery does not have a cost)
revenue('charge',i,r,t)$[storage_standalone(i)$valgen_irt(i,r,t)] = - sum{(v,h)$valgen(i,v,r,t),
  STORAGE_IN.l(i,v,r,h,t) * hours(h) * reqt_price('load','na',r,h,t) } ;

revenue('res_marg',i,r,t)$[valgen_irt(i,r,t)$Sw_PRM_CapCredit] = sum{ccseason,
  cap_firm(i,r,ccseason,t) * reqt_price('res_marg','na',r,ccseason,t) } ;
revenue('res_marg',i,r,t)$[valgen_irt(i,r,t)$(Sw_PRM_CapCredit=0)] = sum{allh$h_stress_t(allh,t),
  gen_h_stress(i,r,allh,t) * reqt_price('res_marg','na',r,allh,t) } ;

revenue('oper_res',i,r,t)$valgen_irt(i,r,t) = sum{(ortype,v,h)$valgen(i,v,r,t),
  OPRES.l(ortype,i,v,r,h,t) * hours(h) * reqt_price('oper_res',ortype,r,h,t) } ;

revenue('rps',i,r,t)$valgen_irt(i,r,t) =
  sum{(v,h,RPSCat)$[valgen(i,v,r,t)$sum{st$r_st(r,st), RecTech(RPSCat,i,st,t) }],
      GEN.l(i,v,r,h,t) * sum{st$r_st(r,st), RPSTechMult(RPSCat,i,st) } * hours(h) * reqt_price('state_rps',RPSCat,r,'ann',t) } ;

revenue_nat(rev_cat,i,t)$tmodel_new(t) = sum{r, revenue(rev_cat,i,r,t) } ;

revenue_en(rev_cat,i,r,t)
    $[tmodel_new(t)
    $valgen_irt(i,r,t)
    $sum{h, gen_h(i,r,h,t) * hours(h) }
    $[not vre(i)]] =
    revenue(rev_cat,i,r,t) / sum{h, gen_h(i,r,h,t) * hours(h) } ;

revenue_en(rev_cat,i,r,t)
    $[tmodel_new(t)
    $sum{(v,h)$[valcap(i,v,r,t)], m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) }
    $vre(i)] =
    revenue(rev_cat,i,r,t) / sum{(v,h)$valcap(i,v,r,t),
      m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) * hours(h) } ;

revenue_en_nat(rev_cat,i,t)
    $[tmodel_new(t)
    $sum{(r,h)$valgen_irt(i,r,t), gen_h(i,r,h,t) * hours(h) }
    $[not vre(i)]] =
    revenue_nat(rev_cat,i,t) / sum{(r,h)$valgen_irt(i,r,t), gen_h(i,r,h,t) * hours(h) } ;

revenue_en_nat(rev_cat,i,t)
    $[tmodel_new(t)
    $sum{(v,r,h)$[valcap(i,v,r,t)], m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) }
    $vre(i)] =
    revenue_nat(rev_cat,i,t) / sum{(v,r,h)$valcap(i,v,r,t),
      m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) * hours(h) } ;

revenue_cap(rev_cat,i,r,t)$[tmodel_new(t)$cap_out(i,r,t)] =
  revenue(rev_cat,i,r,t) / cap_out(i,r,t) ;

revenue_cap_nat(rev_cat,i,t)$[tmodel_new(t)$sum{r$valcap_irt(i,r,t), cap_out(i,r,t) }] =
  revenue_nat(rev_cat,i,t) / cap_nat(i,t) ;

*========================================
* Value (Revenue) of new builds
*========================================

valnew('MW',i,r,t)$[(not tfirst(t))$valcap_irt(i,r,t)] =
  sum{v$valinv(i,v,r,t), INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) } / ilr(i) ;
valnew('inv_cap_ratio',i,r,t)$[valnew('MW',i,r,t)] =
    sum{v$[valinv(i,v,r,t)$CAP.l(i,v,r,t)], (INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t))
    / CAP.l(i,v,r,t) } ;
valnew('MWh',i,r,t)$[valnew('MW',i,r,t)] =
    sum{v$valinv(i,v,r,t), gen_ivrt(i,v,r,t)} * valnew('inv_cap_ratio',i,r,t) ;
* Use uncurtailed energy for VRE
valnew('MWh',i,r,t)$[valnew('MW',i,r,t)$sum{v$valinv(i,v,r,t), gen_ivrt_uncurt(i,v,r,t)}] =
    sum{v$valinv(i,v,r,t), gen_ivrt_uncurt(i,v,r,t)} * valnew('inv_cap_ratio',i,r,t) ;
valnew('MWh','benchmark',r,t)$tmodel_new(t) = sum{h, reqt_quant('load','na',r,h,t)} ;
valnew('MWh','benchmark','sys',t)$tmodel_new(t) = sum{(r,h), reqt_quant('load','na',r,h,t)} ;
valnew('MW','benchmark',r,t)$tmodel_new(t) = reqt_quant('res_marg_ann','na',r,'ann',t) ;
valnew('MW','benchmark','sys',t)$tmodel_new(t) = sum{r, reqt_quant('res_marg_ann','na',r,'ann',t)} ;

valnew('val_load',i,r,t)$valnew('MW',i,r,t) = sum{(v,h)$valinv(i,v,r,t),
    (GEN.l(i,v,r,h,t) - STORAGE_IN.l(i,v,r,h,t)$[storage_standalone(i) or hyd_add_pump(i)])
    * hours(h) * reqt_price('load','na',r,h,t) } * valnew('inv_cap_ratio',i,r,t) ;
*'val_load_sys' is the val our tech would have if valued at the system-average load price profile.
valnew('val_load_sys',i,r,t)$valnew('MW',i,r,t) = sum{(v,h)$valinv(i,v,r,t),
    (GEN.l(i,v,r,h,t) - STORAGE_IN.l(i,v,r,h,t)$[storage_standalone(i) or hyd_add_pump(i)])
    * hours(h) * reqt_price_sys('load','na',h,t) } * valnew('inv_cap_ratio',i,r,t) ;
*Annual-average price at each r:
valnew('val_load','benchmark',r,t)$tmodel_new(t) =
    sum{h, reqt_price('load','na',r,h,t) * reqt_quant('load','na',r,h,t)} ;
*Annual-average price of the system
valnew('val_load','benchmark','sys',t)$tmodel_new(t) =
    sum{(r,h), reqt_price('load','na',r,h,t) * reqt_quant('load','na',r,h,t)} ;

valnew('val_resmarg',i,r,t)$[(Sw_PRM_CapCredit=0)$valnew('MW',i,r,t)] =
    sum{(v,allh)$[h_stress_t(allh,t)$valinv(i,v,r,t)],
    (GEN.l(i,v,r,allh,t) - STORAGE_IN.l(i,v,r,allh,t)$[storage_standalone(i) or hyd_add_pump(i)])
    * reqt_price('res_marg','na',r,allh,t)} * valnew('inv_cap_ratio',i,r,t) ;
* New VRE for the CapCredit formulation is a special case in that new is distinct from old of the same vintage
valnew('val_resmarg',i,r,t)$[(Sw_PRM_CapCredit=1)$vre(i)$valnew('MW',i,r,t)] =
    sum{ccseason, m_cc_mar(i,r,ccseason,t) * valnew('MW',i,r,t) * reqt_price('res_marg','na',r,ccseason,t)};
valnew('val_resmarg_sys',i,r,t)$[(Sw_PRM_CapCredit=0)$valnew('MW',i,r,t)] =
    sum{(v,allh)$[h_stress_t(allh,t)$valinv(i,v,r,t)],
    (GEN.l(i,v,r,allh,t) - STORAGE_IN.l(i,v,r,allh,t)$[storage_standalone(i) or hyd_add_pump(i)])
    * reqt_price_sys('res_marg','na',allh,t)} * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_resmarg_sys',i,r,t)$[(Sw_PRM_CapCredit=1)$vre(i)$valnew('MW',i,r,t)] =
    sum{ccseason, m_cc_mar(i,r,ccseason,t) * valnew('MW',i,r,t) * reqt_price_sys('res_marg','na',ccseason,t)} ;
* Note: val_resmarg and val_resmarg_sys are missing for the capacity credit formulation for non-VRE.
* These would need cap_firm() but with vintage...
valnew('val_resmarg','benchmark',r,t)$[(Sw_PRM_CapCredit=0)$tmodel_new(t)] =
    sum{allh$h_stress_t(allh,t), reqt_price('res_marg','na',r,allh,t) * reqt_quant('res_marg','na',r,allh,t)} ;
valnew('val_resmarg','benchmark','sys',t)$[(Sw_PRM_CapCredit=0)$tmodel_new(t)] =
    sum{(r,allh)$h_stress_t(allh,t), reqt_price('res_marg','na',r,allh,t) * reqt_quant('res_marg','na',r,allh,t)} ;
valnew('val_resmarg','benchmark',r,t)$[(Sw_PRM_CapCredit=1)$tmodel_new(t)] =
    sum{ccseason, reqt_price('res_marg','na',r,ccseason,t) * reqt_quant('res_marg','na',r,ccseason,t)} ;
valnew('val_resmarg','benchmark','sys',t)$[(Sw_PRM_CapCredit=1)$tmodel_new(t)] =
    sum{(r,ccseason), reqt_price('res_marg','na',r,ccseason,t) * reqt_quant('res_marg','na',r,ccseason,t)} ;

valnew('val_opres',i,r,t)$[(not (wind(i) or pv(i) or pvb(i)))$valnew('MW',i,r,t)] = sum{(ortype,v,h)$valinv(i,v,r,t),
  OPRES.l(ortype,i,v,r,h,t) * hours(h) * reqt_price('oper_res',ortype,r,h,t) } * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_opres',i,r,t)$[wind(i)$valnew('MW',i,r,t)] =
    -1 * sum{(ortype,v,h)$[Sw_OpRes$opres_model(ortype)$opres_h(h)$valinv(i,v,r,t)],
    orperc(ortype,"or_wind") * GEN.l(i,v,r,h,t) * hours(h) * reqt_price('oper_res',ortype,r,h,t) }
    * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_opres',i,r,t)$[(pv(i) or pvb(i))$valnew('MW',i,r,t)] =
    -1 * sum{(ortype,v,h)$[Sw_OpRes$opres_model(ortype)$opres_h(h)$dayhours(h)],
    orperc(ortype,"or_pv") * CAP.l(i,v,r,t) / ilr(i) * hours(h) * reqt_price('oper_res',ortype,r,h,t) }
    * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_opres_sys',i,r,t)$[(not (wind(i) or pv(i) or pvb(i)))$valnew('MW',i,r,t)] = sum{(ortype,v,h)$valinv(i,v,r,t),
  OPRES.l(ortype,i,v,r,h,t) * hours(h) * reqt_price_sys('oper_res',ortype,h,t) } * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_opres_sys',i,r,t)$[wind(i)$valnew('MW',i,r,t)] =
    -1 * sum{(ortype,v,h)$[Sw_OpRes$opres_model(ortype)$opres_h(h)$valinv(i,v,r,t)],
    orperc(ortype,"or_wind") * GEN.l(i,v,r,h,t) * hours(h) * reqt_price_sys('oper_res',ortype,h,t) }
    * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_opres_sys',i,r,t)$[(pv(i) or pvb(i))$valnew('MW',i,r,t)] =
    -1 * sum{(ortype,v,h)$[Sw_OpRes$opres_model(ortype)$opres_h(h)$dayhours(h)],
    orperc(ortype,"or_pv") * CAP.l(i,v,r,t) / ilr(i) * hours(h) * reqt_price_sys('oper_res',ortype,h,t) }
    * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_opres','benchmark',r,t)$tmodel_new(t) =
    sum{(ortype,h), reqt_price('oper_res',ortype,r,h,t) * reqt_quant('oper_res',ortype,r,h,t)} ;
valnew('val_opres','benchmark','sys',t)$tmodel_new(t) =
    sum{(ortype,r,h), reqt_price('oper_res',ortype,r,h,t) * reqt_quant('oper_res',ortype,r,h,t)} ;

valnew('val_rps',i,r,t)$valnew('MW',i,r,t) =
  sum{(v,h,RPSCat)$[valinv(i,v,r,t)$sum{st$r_st(r,st), RecTech(RPSCat,i,st,t) }],
      GEN.l(i,v,r,h,t) * sum{st$r_st(r,st), RPSTechMult(RPSCat,i,st) } * hours(h) * reqt_price('state_rps',RPSCat,r,'ann',t) }
  * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_rps_sys',i,r,t)$valnew('MW',i,r,t) =
  sum{(v,h,RPSCat)$[valinv(i,v,r,t)$sum{st$r_st(r,st), RecTech(RPSCat,i,st,t) }],
      GEN.l(i,v,r,h,t) * sum{st$r_st(r,st), RPSTechMult(RPSCat,i,st) } * hours(h) * reqt_price_sys('state_rps',RPSCat,'ann',t) }
  * valnew('inv_cap_ratio',i,r,t) ;
valnew('val_rps','benchmark',r,t)$tmodel_new(t) =
    sum{RPSCat, reqt_price('state_rps',RPSCat,r,'ann',t) * reqt_quant('state_rps',RPSCat,r,'ann',t)} ;
*Annual-average price of the system
valnew('val_rps','benchmark','sys',t)$tmodel_new(t) =
    sum{(r,RPSCat), reqt_price('state_rps',RPSCat,r,'ann',t) * reqt_quant('state_rps',RPSCat,r,'ann',t)} ;

*=========================
* EMISSIONS
*=========================
* emit_r is calculated the same as the EMIT variable in the model. We do not use
* EMIT.l here because the emissions are only modeled for those in the emit_modeled
* set.
emit_r(etype,e,r,t)$tmodel_new(t) = 

* Emissions from generation
    sum{(i,v,h)$[valgen(i,v,r,t)$h_rep(h)],
        hours(h) * emit_rate(etype,e,i,v,r,t)
        * (GEN.l(i,v,r,h,t)
           + CCSFLEX_POW.l(i,v,r,h,t)$[ccsflex(i)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)])
       }

* Plus emissions produced via production activities (SMR, SMR-CCS, DAC)
* The "production" of negative CO2 emissions via DAC is also included here
    + sum{(p,i,v,h)$[valcap(i,v,r,t)$i_p(i,p)$h_rep(h)],
          hours(h) * prod_emit_rate(etype,e,i,t)
          * PRODUCE.l(p,i,v,r,h,t)
         }

*[minus] co2 reduce from flexible CCS capture
*capture = capture per energy used by the ccs system * CCS energy

* Flexible CCS - bypass
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_byp(i)$h_rep(h)],
        ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POW.l(i,v,r,h,t) })$[sameas(e,"co2")]$Sw_CCSFLEX_BYP

* Flexible CCS - storage
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_sto(i)$h_rep(h)],
        ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POWREQ.l(i,v,r,h,t) })$[sameas(e,"co2")]$Sw_CCSFLEX_STO
; 

* Apply global warming potential to include CH4 and N2O in CO2(e)
emit_r(etype,"CO2e",r,t)$tmodel_new(t) = sum{e,emit_r(etype,e,r,t)*gwp(e)} ;
emit_nat(etype,eall,t)$tmodel_new(t) = sum{r, emit_r(etype,eall,r,t) } ;

* Generation emissions by tech and region
emit_irt(etype,e,i,r,t)$[tmodel_new(t)$(not sameas(e,"CO2"))$valgen_irt(i,r,t)] = 
    sum{(v,h)$[valgen(i,v,r,t)],
         hours(h) * emit_rate(etype,e,i,v,r,t) * GEN.l(i,v,r,h,t) } ;
* Production-related emissions by tech and region
emit_irt(etype,e,i,r,t)$[tmodel_new(t)$(not sameas(e,"CO2"))$sum{p, i_p(i,p)}] =
         sum{(p,v,h)$i_p(i,p),
         hours(h) * prod_emit_rate(etype,e,i,t) * PRODUCE.l(p,i,v,r,h,t) } ;
* CO2 generation emissions by tech and region
emit_irt(etype,"CO2",i,r,t)$[tmodel_new(t)$valgen_irt(i,r,t)] = sum{(v,h)$[valgen(i,v,r,t)],
         hours(h) * emit_rate(etype,"CO2",i,v,r,t) * GEN.l(i,v,r,h,t) } ;
* CO2 production-related emissions by tech and region
emit_irt(etype,"CO2",i,r,t)$[tmodel_new(t)$sum{p, i_p(i,p)}] =
         sum{(p,v,h)$i_p(i,p),
         hours(h) * prod_emit_rate(etype,"CO2",i,t) * PRODUCE.l(p,i,v,r,h,t) } ;
* Apply global warming potential to include other GHGs in CO2(e)
emit_irt(etype,"CO2e",i,r,t)$tmodel_new(t) = sum{e,emit_irt(etype,e,i,r,t) * gwp(e)} ;

emit_nat_tech(etype,eall,i,t) = sum{r, emit_irt(etype,eall,i,r,t)} ;

emit_weighted(etype,eall) = sum{t$tmodel(t), emit_nat(etype,eall,t) * pvf_onm(t) } ;

emit_rate_regional(r,t)$tmodel_new(t) = co2_emit_rate_r(r,t) ;

* captured CO2 emissions from CCS and DAC
emit_captured_irt(i,r,t)$tmodel_new(t) =
  sum{(v,h)$[valgen(i,v,r,t)], hours(h) * capture_rate("CO2",i,v,r,t) * GEN.l(i,v,r,h,t) } ;

emit_captured_irt("smr_ccs",r,t)$tmodel_new(t) =
  sum{(v,h,p)$[valcap("smr_ccs",v,r,t)$i_p("smr_ccs",p)], smr_capture_rate * hours(h)
    * smr_co2_intensity * PRODUCE.l(p,"smr_ccs",v,r,h,t) } ;

emit_captured_irt(i,r,t)$[tmodel_new(t)$dac(i)] =
  sum{(v,h,p)$[dac(i)$valcap(i,v,r,t)$i_p(i,p)], hours(h) * PRODUCE.l(p,i,v,r,h,t)} ;

emit_captured_nat(i,t)$tmodel_new(t) = sum{r, emit_captured_irt(i,r,t) } ;


*==================================
* National RE Constraint Marginals
*==================================

RE_gen_price_nat(t)$tmodel_new(t) = (1/cost_scale) * crf(t) * eq_national_gen.m(t) ;

*=========================
* [i,v,r,t]-level capital expenditures (for retail rate calculations)
*=========================

capex_ivrt(i,v,r,t)$valcap(i,v,r,t) =
                      INV.l(i,v,r,t) * (cost_cap_fin_mult_no_credits(i,r,t) * cost_cap(i,t) )
                      + INV_ENERGY.l(i,v,r,t) * (cost_cap_fin_mult_no_credits(i,r,t) * cost_cap_energy(i,t) )
                      + sum{(rscbin)$m_rscfeas(r,i,rscbin),INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * cost_cap_fin_mult_no_credits(i,r,t) }
                      + (INV_REFURB.l(i,v,r,t) * (cost_cap_fin_mult_no_credits(i,r,t) * cost_cap(i,t)))$[refurbtech(i)$Sw_Refurb]
                      + UPGRADES.l(i,v,r,t) * (cost_upgrade(i,v,r,t) * cost_cap_fin_mult_no_credits(i,r,t))$[upgrade(i)$Sw_Upgrades] ;

*=========================
* Tech|BA-Level SYSTEM COST: Capital
*=========================

* REPLICATION OF THE OBJECTIVE FUNCTION
* DOES NOT INCLUDE COSTS NOT INDEXED BY TECH (e.g., TRANSMISSION)

systemcost_techba("inv_investment_capacity_costs",i,r,t)$tmodel_new(t) =
*investment costs (without the subtraction of any ITC/PTC value)
              sum{v$valinv(i,v,r,t),
                   INV.l(i,v,r,t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t) ) }
*plus investment energy costs (without the subtraction of any ITC/PTC value)
              + sum{v$[valinv(i,v,r,t)$battery(i)],
                   INV_ENERGY.l(i,v,r,t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap_energy(i,t) ) }
*plus supply curve adjustment to capital cost (separated in outputs but part of m_rsc_dat(r,i,rscbin,"cost"))
              + sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$[not sccapcosttech(i)]$(not spur_techs(i))],
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost_cap") * rsc_fin_mult_noITC(i,r,t) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
              + sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$sccapcosttech(i)],
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult_noITC(i,r,t) }
*plus cost of upgrades
              + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
                   cost_upgrade(i,v,r,t) * cost_cap_fin_mult_noITC(i,r,t) * UPGRADES.l(i,v,r,t) }
*cost of capacity upsizing
              + sum{(v,rscbin)$allow_cap_up(i,v,r,rscbin,t),
                   cost_cap_fin_mult_noITC(i,r,t) * INV_CAP_UP.l(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }
*cost of energy upsizing
              + sum{(v,rscbin)$allow_ener_up(i,v,r,rscbin,t),
                   cost_cap_fin_mult_noITC(i,r,t) * INV_ENER_UP.l(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) }
;

systemcost_techba("inv_investment_spurline_costs_rsc_technologies",i,r,t)$tmodel_new(t) =
*costs of rsc spur line investment
*Note that cost_cap for hydro, pumped-hydro, and geo techs are zero
*but hydro and geo rsc_fin_mult is equal to the same value as cost_cap_fin_mult
*(Note that exclusions of geo and hydro here deviates from the objective function structure)
              sum{(v,rscbin)
                  $[m_rscfeas(r,i,rscbin)
                  $valinv(i,v,r,t)
                  $rsc_i(i)
                  $[not sccapcosttech(i)]
                  $(not spur_techs(i))
                  ],
*investment in resource supply curve technologies
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost_trans") * rsc_fin_mult_noITC(i,r,t) }
;

systemcost_techba("inv_itc_payments_negative",i,r,t)$tmodel_new(t) =
*investment costs (including reduction from ITC)
                sum{v$valinv(i,v,r,t),
                   INV.l(i,v,r,t) * (cost_cap_fin_mult_out(i,r,t) * cost_cap(i,t) ) }
*energy investment costs (including reduction from ITC)
              + sum{v$[valinv(i,v,r,t)$battery(i)],
                   INV_ENERGY.l(i,v,r,t) * (cost_cap_fin_mult_out(i,r,t) * cost_cap_energy(i,t) ) }
*plus supply curve adjustment to capital cost (separated in outputs but part of m_rsc_dat(r,i,rscbin,"cost"))
              + sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$[not sccapcosttech(i)]$(not spur_techs(i))],
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost_cap") * rsc_fin_mult(i,r,t) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
              + sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$sccapcosttech(i)],
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) }
*plus cost of upgrades
              + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
                   cost_upgrade(i,v,r,t) * cost_cap_fin_mult_out(i,r,t) * UPGRADES.l(i,v,r,t) }
*cost of capacity upsizing
              + sum{(v,rscbin)$allow_cap_up(i,v,r,rscbin,t),
                   cost_cap_fin_mult_out(i,r,t) * INV_CAP_UP.l(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }
*cost of energy upsizing
              + sum{(v,rscbin)$allow_ener_up(i,v,r,rscbin,t),
                   cost_cap_fin_mult_out(i,r,t) * INV_ENER_UP.l(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) }
*minus capacity costs without ITC
              - systemcost_techba("inv_investment_capacity_costs",i,r,t)
*plus supply curve transmission costs (including cost reductions from the ITC for applicable techs)
              +sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$[not sccapcosttech(i)]$(not spur_techs(i))],
                    INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost_trans") * rsc_fin_mult(i,r,t) }
*minus rsc transmission costs without ITC
              - systemcost_techba("inv_investment_spurline_costs_rsc_technologies",i,r,t)
;

*assign consume techs to their own category and then zero it out
systemcost_techba("inv_dac",i,r,t)$[tmodel_new(t)$dac(i)] = systemcost_techba("inv_investment_capacity_costs",i,r,t) ;
systemcost_techba("inv_h2_production",i,r,t)$[tmodel_new(t)$h2(i)] = systemcost_techba("inv_investment_capacity_costs",i,r,t) ;
systemcost_techba("inv_investment_capacity_costs",i,r,t)$[tmodel_new(t)$consume(i)] = 0 ;

systemcost_techba("inv_investment_refurbishment_capacity",i,r,t)$tmodel_new(t) =
*costs of refurbishments of RSC tech (without the subtraction of any ITC/PTC value)
              + sum{v$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                        (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t)) * INV_REFURB.l(i,v,r,t) }
;

systemcost_techba("inv_itc_payments_negative_refurbishments",i,r,t)$tmodel_new(t) =
*costs of refurbishments of RSC tech (including reduction from ITC)
              + sum{v$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                   (cost_cap_fin_mult_out(i,r,t) * cost_cap(i,t)) * INV_REFURB.l(i,v,r,t) }
*minus capacity costs without ITC
              - systemcost_techba("inv_investment_refurbishment_capacity",i,r,t)
;

systemcost_techba("inv_investment_water_access",i,r,t)$tmodel_new(t) =
*cost of water access
              + (8760/1E6) * sum{ (v,w)$[i_w(i,w)$valinv(i,v,r,t)], sum{wst$i_wst(i,wst), m_watsc_dat(wst,"cost",r,t)} * water_rate(i,w) *
                        ( INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)$[refurbtech(i)$Sw_Refurb] ) }
              + sum{(rscbin,v)$[m_rscfeas(r,i,rscbin)$psh(i)], sum{wst$i_wst(i,wst), m_watsc_dat(wst,"cost",r,t) } *
                        ( INV_RSC.l(i,v,r,rscbin,t) * water_req_psh(r,rscbin) ) }
;

*===============
* Tech|BA-Level SYSTEM COST: Operational (the op_ prefix is used by the retail rate module to identify which costs are operational costs)
*===============

* DOES NOT INCLUDE COSTS NOT INDEXED BY TECH (e.g., ACP COMPLIANCE)

systemcost_techba("op_vom_costs",i,r,t)$tmodel_new(t)  =
*variable O&M costs
              sum{(v,h)$[valgen(i,v,r,t)$cost_vom(i,v,r,t)],
                   hours(h) * cost_vom(i,v,r,t) * GEN.l(i,v,r,h,t) }

* include production costs from production technologies
              + sum{(p,v,h)$[(h2(i) or dac(i))$valcap(i,v,r,t)$i_p(i,p)],
                    hours(h) * cost_prod(i,v,r,t) * PRODUCE.l(p,i,v,r,h,t) }$Sw_Prod
;

systemcost_techba("op_consume_vom",i,r,t)$[tmodel_new(t)$consume(i)] = systemcost_techba("op_vom_costs",i,r,t)$tmodel_new(t) ;
systemcost_techba("op_vom_costs",i,r,t)$[tmodel_new(t)$consume(i)] = 0 ;

systemcost_techba("op_fom_costs",i,r,t)$tmodel_new(t)  =
*fixed O&M costs for generation capacity
              + sum{v$[valcap(i,v,r,t)$((not one_newv(i)) or retiretech(i,v,r,t))],
                   cost_fom(i,v,r,t) * cap_ivrt(i,v,r,t) * ilr(i) }
*for technologies with only one newv that are not allowed to retire,
*use the investments rather than the capacity to calculate FOM costs
              + sum{(v,tt)$[inv_cond(i,v,r,t,tt)$one_newv(i)$(not retiretech(i,v,r,tt))],
                   INV.l(i,v,r,tt) * cost_fom(i,v,r,tt) * ilr(i) }
              + sum{(v,tt)$[inv_cond(i,v,r,t,tt)$one_newv(i)$(not retiretech(i,v,r,tt))],
                   INV_ENERGY.l(i,v,r,tt) * cost_fom_energy(i,v,r,tt) * ilr(i) }
;

systemcost_techba("op_consume_fom",i,r,t)$[tmodel_new(t)$consume(i)] = systemcost_techba("op_fom_costs",i,r,t)$tmodel_new(t) ;
systemcost_techba("op_fom_costs",i,r,t)$[tmodel_new(t)$consume(i)] = 0 ;

systemcost_techba("op_operating_reserve_costs",i,r,t)$tmodel_new(t)  =
*operating reserve costs
              + sum{(v,h,ortype)$[valgen(i,v,r,t)$cost_opres(i,ortype,t)],
                   hours(h) * cost_opres(i,ortype,t) * OpRes.l(ortype,i,v,r,h,t) }
;

systemcost_techba("op_fuelcosts_objfn",i,r,t)$tmodel_new(t)  =
*cost of coal and nuclear fuel (except coal used for cofiring)
              + sum{(v,h)$[valgen(i,v,r,t)$heat_rate(i,v,r,t)
                         $(not gas(i))$(not bio(i))$(not cofire(i))
                         $((not h2_combustion(i)) or h2_combustion(i)$[(Sw_H2=0) or h_stress(h)])],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN.l(i,v,r,h,t) }

*cofire coal consumption - cofire bio consumption already accounted for in accounting of BIOUSED
              + sum{(v,h)$[valgen(i,v,r,t)$cofire(i)$heat_rate(i,v,r,t)],
                   (1-bio_cofire_perc) * hours(h) * heat_rate(i,v,r,t)
                   * fuel_price("coal-new",r,t) * GEN.l(i,v,r,h,t) }

*cost of natural gas fuel
              + sum{cendiv$r_cendiv(r,cendiv), gascost_cendiv(cendiv,t) * gasshare_techba(i,r,cendiv,t) }

*cost biofuel consumption by the tech in the BA
              + bioshare_techba(i,r,t) * sum{bioclass, BIOUSED.l(bioclass,r,t) *
                        (sum{usda_region$r_usda(r,usda_region), biosupply(usda_region, bioclass, "price") } + bio_transport_cost) }

;

systemcost_techba("op_emissions_taxes",i,r,t)$tmodel_new(t)  =
*plus any taxes on emissions
              sum{(e,v,h)$[valgen(i,v,r,t)],
                    hours(h) * (emit_rate("process",e,i,v,r,t) + emit_rate("upstream",e,i,v,r,t)$Sw_Upstream) * GEN.l(i,v,r,h,t) * emit_tax(e,r,t) }
;

systemcost_techba("op_h2_fuel_costs",i,r,t)$tmodel_new(t)  =
* H2 production costs 
              sum{(v,h,p)$[h2(i)$valcap(i,v,r,t)],
                  hours(h) * h2_fuel_cost(i,v,r,t) * PRODUCE.l(p,i,v,r,h,t) }
;

systemcost_techba("op_h2combustion_fuel_costs",i,r,t)$[tmodel_new(t)$h2_combustion(i)$Sw_H2]  =
* fuel costs for H2-CT/CC techs
              + (1 / cost_scale) * (1 / pvf_onm(t))
* when using national demand, calculate total annual demand and multiply by national average price
* [MW] * [hours] * [MMBTU/MWh] * [metric tons/MMBTU] * [$/metric ton] = [$]
              * ( (sum{(v,h), GEN.l(i,v,r,h,t) * hours(h) * heat_rate(i,v,r,t) * h2_combustion_intensity  } 
                    *  eq_h2_demand.m("H2",t) 
                  )$[Sw_H2 = 1]
* when using regional demand by hour, apply price to each hour and then sum total costs
* [MW] * [hours] * [MMBTU/MWh] * [metric tons/MMBTU] * [$/[metric tons/hour]] / [hours] = [$]
                + (sum{(v,h), GEN.l(i,v,r,h,t) * hours(h) * heat_rate(i,v,r,t) * h2_combustion_intensity 
                    *  eq_h2_demand_regional.m(r,h,t) / hours(h) }
                  )$[Sw_H2 = 2] 
                )
;
  
systemcost_techba("op_h2_vom",i,r,t)$tmodel_new(t)  =
* vom costs from H2 production
              sum{(v,h,p)$[h2(i)$valcap(i,v,r,t)],
                  hours(h) * h2_vom(i,t) * PRODUCE.l(p,i,v,r,h,t) }
;

* transport and storage cost of captured CO2
systemcost_techba("op_co2_transport_storage",i,r,t)$[tmodel_new(t)$(not Sw_CO2_Detail)] =
              emit_captured_irt(i,r,t) * Sw_CO2_Storage
;

systemcost_techba("op_co2_incentive_negative",i,r,t)$tmodel_new(t) =
              - sum{(v,h)$[valgen(i,v,r,t)$co2_captured_incentive(i,v,r,t)],
                              (crf(t) / crf_co2_incentive(t)) * co2_captured_incentive(i,v,r,t) * hours(h) * capture_rate("CO2",i,v,r,t) * GEN.l(i,v,r,h,t)}

              - sum{(p,v,h)$[dac(i)$valcap(i,v,r,t)],
                              (crf(t) / crf_co2_incentive(t)) * co2_captured_incentive(i,v,r,t) * hours(h) * PRODUCE.l(p,i,v,r,h,t)}
;

* PTC for generation
systemcost_techba('op_ptc_payments_negative',i,r,t)$tmodel_new(t) =
    - sum{(v,h)$[valgen(i,v,r,t)$ptc_value_scaled(i,v,t)],
          hours(h) * ptc_value_scaled(i,v,t) * tc_phaseout_mult(i,v,t) * GEN.l(i,v,r,h,t) }
;

* PTC value for hydrogen production
* Note: all electrolyzers which produce H2 are assuming to be receiving hydrogen production credits during eligible years  
systemcost_techba('op_h2_ptc_payments_negative','electrolyzer',r,t)$[tmodel_new(t)] =
      - (sum{(p,v,h)$[valcap("electrolyzer",v,r,t)$(sameas(p,"H2"))$h2_ptc("electrolyzer",v,r,t)$h_rep(h)],
          hours(h) * PRODUCE.l(p,"electrolyzer",v,r,h,t) *
            (crf(t) / crf_h2_incentive(t)) * h2_ptc("electrolyzer",v,r,t) * 1e3} )
            $[Sw_H2_PTC$Sw_H2$h2_ptc_years(t)$(yeart(t) >= h2_demand_start)]
;

* Startup/ramping costs
systemcost_techba('op_startcost',i,r,t)$[tmodel_new(t)$Sw_StartCost$startcost(i)] =
    sum{(h,hh)$[numhours_nexth(h,hh)$valgen_irt(i,r,t)],
        startcost(i) * numhours_nexth(h,hh) * RAMPUP.l(i,r,h,hh,t) }
;


*For bulk system costs present value as of model year, capital costs are unchanged,
*while operation costs use pvf_onm_undisc
systemcost_techba_bulk(sys_costs,i,r,t) = systemcost_techba(sys_costs,i,r,t) ;
systemcost_techba_bulk(sys_costs_op,i,r,t) = systemcost_techba(sys_costs_op,i,r,t) * pvf_onm_undisc(t) ;

systemcost_techba_bulk_ew(sys_costs,i,r,t) = systemcost_techba_bulk(sys_costs,i,r,t) ;
systemcost_techba_bulk_ew(sys_costs_op,i,r,t)$tlast(t) = systemcost_techba(sys_costs_op,i,r,t) ;

* Sum across technologies to get BA-level costs for all applicable categories
systemcost_ba(sys_costs,r,t) = sum{i,systemcost_techba(sys_costs,i,r,t)} ;

*=========================
* BA-Level SYSTEM COST: Capital
*=========================

* REPLICATION OF THE OBJECTIVE FUNCTION

* Interzonal transmission: Split costs between the two connected zones
* DC: INVTRAN is defined (and is equal) in both directions, so just include (r,rr) and divide by 2
systemcost_ba("inv_transmission_interzone_dc_investment",r,t)$tmodel_new(t) =
    sum{(rr,trtype)$[routes_inv(r,rr,trtype,t)$(not aclike(trtype))],
        trans_cost_cap_fin_mult(t)
        * transmission_cost_nonac(r,rr,trtype)
        * INVTRAN.l(r,rr,trtype,t)
        / 2 }
;

* AC: TRAN_CAPEX_BINS is only defined for r < rr, so add (r,rr) + (rr,r) and divide by 2
* First get the cumulative investment cost, split across zones
parameter capex_transmission_interzone_ac(r,t) "Cumulative interzonal AC transmission capex" ;
capex_transmission_interzone_ac(r,t)$tmodel_new(t) =
    sum{(rr,tscbin)$[routes_inv(r,rr,"AC",t)$tsc_binwidth(r,rr,tscbin)],
        trans_cost_cap_fin_mult(t) * TRAN_CAPEX_BINS.l(r,rr,tscbin,t) / 2 }
    + sum{(rr,tscbin)$[routes_inv(rr,r,"AC",t)$tsc_binwidth(rr,r,tscbin)],
        trans_cost_cap_fin_mult(t) * TRAN_CAPEX_BINS.l(rr,r,tscbin,t) / 2 }
;
* Loop over each year and keep the capex difference to get model-year investment
loop(t$[tmodel_new(t)$(not tfirst(t))],
    systemcost_ba("inv_transmission_interzone_ac_investment",r,t)
    =
    capex_transmission_interzone_ac(r,t)
    - sum{tt$tprev(t, tt),
        capex_transmission_interzone_ac(r,tt)
    } ;
) ;

systemcost_ba("inv_transmission_intrazone_investment",r,t)$[tmodel_new(t)$Sw_TransIntraCost] =
* cost of intra-zone network reinforcement
              trans_cost_cap_fin_mult(t) * Sw_TransIntraCost * 1000 * INV_POI.l(r,t)
;

systemcost_ba("op_transmission_fom",r,t)$tmodel_new(t) =
*fixed O&M costs for transmission lines
              sum{(rr,trtype)$routes(r,rr,trtype,t),
                    transmission_line_fom(r,rr,trtype) * CAPTRAN_ENERGY.l(r,rr,trtype,t) }
*fixed O&M costs for LCC AC/DC converters
              + sum{(rr,trtype)$[lcclike(trtype)$routes(r,rr,trtype,t)],
                    cost_acdc_lcc * 2 * trans_fom_frac * CAPTRAN_ENERGY.l(r,rr,trtype,t) }
*fixed O&M costs for VSC AC/DC converters
              + cost_acdc_vsc * trans_fom_frac * CAP_CONVERTER.l(r,t)
;

systemcost_ba("op_transmission_intrazone_fom",r,t)$[tmodel_new(t)$Sw_TransIntraCost] =
* FOM cost for intra-zone network reinforcement
              Sw_TransIntraCost * 1000 * trans_fom_frac
              * sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))], INV_POI.l(r,tt) }
;

systemcost_ba("inv_converter_costs",r,t)$tmodel_new(t)  =
* LCC and B2B AC/DC converter stations: each interface has two, one on either side of the interface,
* but each interface shows up in both INVTRAN(r,rr) and INVTRAN(rr,r) so don't multiply by 2
              sum{(rr,trtype)$[lcclike(trtype)$routes_inv(r,rr,trtype,t)],
                  trans_cost_cap_fin_mult(t) * cost_acdc_lcc * INVTRAN.l(r,rr,trtype,t) }
* VSC AC/DC converter stations
              + trans_cost_cap_fin_mult(t) * cost_acdc_vsc * INV_CONVERTER.l(r,t)
;

systemcost_ba("inv_spurline_investment",r,t)$[tmodel_new(t)$Sw_SpurScen] =
* capital cost of spur lines modeled explicitly
              sum{x$[xfeas(x)$x_r(x,r)], spurline_cost(x) * Sw_SpurCostMult * INV_SPUR.l(x,t) }
;

systemcost_ba("op_spurline_fom",r,t)$tmodel_new(t) =
* fixed O&M cost of spur lines modeled explicitly
    sum{x$[Sw_SpurScen$xfeas(x)$x_r(x,r)], spurline_cost(x) * trans_fom_frac * CAP_SPUR.l(x,t) }
* fixed O&M cost of spur lines modeled as part of supply curve
    + sum{(i,v,rscbin)
          $[m_rscfeas(r,i,rscbin)$valcap(i,v,r,t)
          $rsc_i(i)$(not spur_techs(i))$(not sccapcosttech(i))],
          m_rsc_dat(r,i,rscbin,"cost_trans") * trans_fom_frac * CAP_RSC.l(i,v,r,rscbin,t)
    }
;

systemcost_ba("inv_co2_network_pipe",r,t)$[tmodel_new(t)$Sw_CO2_Detail]  =
*costs of co2 trunk pipeline investment (cost_co2_pipeline_cap already includes distance; see b_inputs)
              + sum{rr$co2_routes(r,rr), cost_co2_pipeline_cap(r,rr,t) *
              ( (CO2_TRANSPORT_INV.l(r,rr,t) + CO2_TRANSPORT_INV.l(rr,r,t)  ) / 2 ) }
;

systemcost_ba("inv_co2_network_spur",r,t)$[tmodel_new(t)$Sw_CO2_Detail]  =
*costs of co2 spurline investment (cost_co2_spurline_cap already includes distance; see b_inputs)
              + sum{cs$r_cs(r,cs), cost_co2_spurline_cap(r,cs,t) * CO2_SPURLINE_INV.l(r,cs,t) }
;

systemcost_ba("inv_h2_pipeline",r,t)$[tmodel_new(t)$(Sw_H2 = 2)] = 
* H2 transport network investment costs (investments defined only for r < rr)
  sum{rr$h2_routes_inv(r,rr), 
    cost_h2_transport_cap(r,rr,t) * H2_TRANSPORT_INV.l(r,rr,t) }
;

systemcost_ba("inv_h2_storage",r,t)$[tmodel_new(t)$(Sw_H2 = 2)] = 
* H2 storage investment costs
    + sum{h2_stor$h2_stor_r(h2_stor,r), cost_h2_storage_cap(h2_stor,t) * H2_STOR_INV.l(h2_stor,r,t) }
;

*===============
* BA-Level SYSTEM COST: Operational (the op_ prefix is used by the retail rate module to identify which costs are operational costs)
*===============

systemcost_ba("op_co2_storage",r,t)$[tmodel_new(t)$Sw_CO2_Detail] =
              + sum{(h,cs)$r_cs(r,cs), hours(h) * CO2_STORED.l(r,cs,h,t) * cost_co2_stor_bec(cs,t) }
;

* here following same logic of transmission pipelines
systemcost_ba("op_co2_network_fom_pipe",r,t)$[tmodel_new(t)$Sw_CO2_Detail] =
              sum{(rr)$[co2_routes(r,rr)], cost_co2_pipeline_fom(r,rr,t)
                              * sum{tt$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))],
                                   (CO2_TRANSPORT_INV.l(r,rr,tt) + CO2_TRANSPORT_INV.l(rr,r,tt) ) / 2 }
                    }$[Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]
;

systemcost_ba("op_co2_network_fom_spur",r,t)$[tmodel_new(t)$Sw_CO2_Detail] =
              sum{(cs)$r_cs(r,cs), cost_co2_spurline_fom(r,cs,t)
                              * sum{tt$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))],
                                   CO2_SPURLINE_INV.l(r,cs,tt) }
                    }$[Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]
;

systemcost_ba("op_co2_network_fom_spur",r,t)$[tmodel_new(t)$Sw_CO2_Detail] = 
              sum{(cs)$r_cs(r,cs), cost_co2_spurline_fom(r,cs,t)
                              * sum{tt$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))],
                                   CO2_SPURLINE_INV.l(r,cs,tt) } 
                    }$[Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]
;

* same for H2 pipelines and storage
systemcost_ba("op_h2_transport",r,t)$[tmodel_new(t)$(Sw_H2 = 2)] = 
              sum{rr$h2_routes_inv(r,rr), 
                cost_h2_transport_fom(r,rr,t) * 
                sum{tt$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))],
                    H2_TRANSPORT_INV.l(r,rr,t) } }
;

systemcost_ba("op_h2_transport_intrareg",r,t)$[tmodel_new(t)$Sw_H2] = 
* H2 transport and storage intra-regional investment costs
    sum{(i,v,h)$[valcap(i,v,r,t)$newv(v)$i_p(i,"H2")], 
        hours(h) * PRODUCE.l("H2",i,v,r,h,t) * (Sw_H2_IntraReg_Transport * 1e3) }
;

systemcost_ba("op_h2_storage",r,t)$[tmodel_new(t)$(Sw_H2 = 2)] = 
    sum{h2_stor$h2_stor_r(h2_stor,r),
        cost_h2_storage_fom(h2_stor,t) * H2_STOR_CAP.l(h2_stor,r,t) }
;

systemcost_ba("op_acp_compliance_costs",r,t)$[tmodel_new(t)$(yeart(t)>=firstyear_RPS)]  =
*plus ACP purchase costs, attributed to bas based on fraction of state requirement
              + sum{(st,RPSCat)
                    $[stfeas(st)$r_st(r,st)$RecPerc(RPSCat,st,t)
                    $sum{rr$r_st(rr,st), reqt_quant('state_rps',RPSCat,rr,'ann',t) }],
                       acp_price(st,t) * ACP_PURCHASES.l(RPSCat,st,t) * reqt_quant('state_rps',RPSCat,r,'ann',t)
                       / sum{rr$r_st(rr,st), reqt_quant('state_rps',RPSCat,rr,'ann',t) }
                   }
* spread voluntary purchase costs based on BA load frac
              + sum{RPSCat$RecPerc(RPSCat,"voluntary",t), acp_price("voluntary",t) * ACP_PURCHASES.l(RPSCat,"voluntary",t) }
                * load_frac_rt(r,t)

;

systemcost_ba("op_co2_incentive_negative",r,t)$tmodel_new(t)  =
              - sum{(i,v,h)$[valgen(i,v,r,t)$co2_captured_incentive(i,v,r,t)],
                              (crf(t) / crf_co2_incentive(t)) * co2_captured_incentive(i,v,r,t) * hours(h) * capture_rate("CO2",i,v,r,t) * GEN.l(i,v,r,h,t)}

              - sum{(i,p,v,h)$[dac(i)$valcap(i,v,r,t)],
                              (crf(t) / crf_co2_incentive(t)) * co2_captured_incentive(i,v,r,t) * hours(h) * PRODUCE.l(p,i,v,r,h,t)}
;


*If the op_h2combustion_fuel_costs are included in the systemcost_ba it will lead to double-counting
*but these fuel costs are needed for the retail rate module. We therefore zero them out here.
systemcost_ba_retailrate(sys_costs,r,t) = systemcost_ba(sys_costs,r,t) ;
systemcost_ba("op_h2combustion_fuel_costs",r,t) = 0 ;

*For bulk system costs present value as of model year, capital costs are unchanged,
*while operation costs use pvf_onm_undisc
systemcost_ba_bulk(sys_costs,r,t) = systemcost_ba(sys_costs,r,t) ;
systemcost_ba_bulk(sys_costs_op,r,t) = systemcost_ba(sys_costs_op,r,t) * pvf_onm_undisc(t) ;

systemcost_ba_bulk_ew(sys_costs,r,t) = systemcost_ba_bulk(sys_costs,r,t) ;
systemcost_ba_bulk_ew(sys_costs_op,r,t)$tlast(t) = systemcost_ba(sys_costs_op,r,t) ;


*=========================
* National System Cost
*=========================

systemcost(sys_costs,t) = sum{r, systemcost_ba(sys_costs,r,t) } ;
systemcost_bulk(sys_costs,t) = systemcost(sys_costs,t) ;
systemcost_bulk(sys_costs_op,t) = systemcost(sys_costs_op,t) * pvf_onm_undisc(t) ;

systemcost_bulk_ew(sys_costs,t) = systemcost_bulk(sys_costs,t) ;
systemcost_bulk_ew(sys_costs_op,t)$tlast(t) = systemcost(sys_costs_op,t) ;

* Federal tax expenditure calculation
tax_expenditure_itc(t) = systemcost("inv_itc_payments_negative",t)
                       + systemcost("inv_itc_payments_negative_refurbishments",t) ;

tax_expenditure_ptc(t) = systemcost("op_ptc_payments_negative",t)
                       + systemcost("op_co2_incentive_negative",t) ;

raw_inv_cost(t) = sum{sys_costs_inv, systemcost(sys_costs_inv,t) } ;
raw_op_cost(t) = sum{sys_costs_op, systemcost(sys_costs_op,t) } ;

*======================
* Error Check
*======================
* Objective function cost - reported system cost, adjusted for intentional differences
error_check('z') = (
    z.l
    - sum{t$tmodel(t),
* Start with the system cost, then make adjustments for objective function values that are
* not intended to be in the system costs
        cost_scale * (pvf_capital(t) * raw_inv_cost(t) + pvf_onm(t) * raw_op_cost(t))
* Cost of growth penalties
* (Note: adjustments should have the same sign (+/-) as they do in the objective function)
        + pvf_capital(t) * sum{(gbin,i,st)$[sum{r$[r_st(r,st)], valinv_irt(i,r,t) }$stfeas(st)],
              cost_growth(i,st,t) * growth_penalty(gbin) * GROWTH_BIN.l(gbin,i,st,t)
              * (yeart(t) - sum{tt$[tprev(t,tt)], yeart(tt) })
        }$[(yeart(t)>=model_builds_start_yr)$Sw_GrowthPenalties$(yeart(t)<=Sw_GrowthPenLastYear)]
* Small penalty to move storage into shorter duration bins
        + pvf_capital(t) * sum{(i,v,r,ccseason,sdbin)$[valcap(i,v,r,t)$(storage(i) or hyd_add_pump(i))$(not csp(i))$Sw_PRM_CapCredit$Sw_StorageBinPenalty],
            bin_penalty(sdbin) * CAP_SDBIN.l(i,v,r,ccseason,sdbin,t) }
* Retirement penalty
        - pvf_onm(t) * sum{(i,v,r)$[valcap(i,v,r,t)$retiretech(i,v,r,t)$Sw_RetirePenalty],
            cost_fom(i,v,r,t) * retire_penalty(t)
            * (CAP.l(i,v,r,t) - INV.l(i,v,r,t) - INV_REFURB.l(i,v,r,t)$[refurbtech(i)$Sw_Refurb] - UPGRADES.l(i,v,r,t)$[upgrade(i)$Sw_Upgrades]) }
* Revenue from purchases of curtailed VRE
        - pvf_onm(t) * sum{(r,h), CURT.l(r,h,t) * hours(h) * cost_curt(t) }$Sw_CurtMarket
* Hurdle costs
        + pvf_onm(t) * sum{(r,rr,trtype)$cost_hurdle(r,rr,t), tran_hurdle_cost_ann(r,rr,trtype,t) }
* Penalty cost for dropped/excess load before Sw_StartMarkets
        + pvf_onm(t) * sum{(r,h), (DROPPED.l(r,h,t) + EXCESS.l(r,h,t)) * hours(h) * cost_dropped_load }
* Retail adder for electricity consuming technologies
        + pvf_onm(t) * sum{(p,i,v,r,h)$[valcap(i,v,r,t)$i_p(i,p)$h_rep(h)$Sw_RetailAdder$Sw_Prod],
              hours(h) * Sw_RetailAdder * PRODUCE.l(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) }
* Account for difference in fixed O&M between model (CAP.l(i,v,r,t))
* and outputs (cap_ivrt(i,v,r,t) * ilr(i)) for techs with more than one newv
        + pvf_onm(t) * sum{(i,v,r)$[valcap(i,v,r,t)$((not one_newv(i)) or retiretech(i,v,r,t))],
            cost_fom(i,v,r,t) * (CAP.l(i,v,r,t) - cap_ivrt(i,v,r,t) * ilr(i)) }
* Account for difference in fixed O&M between model (CAP.l(i,v,r,t))
* and outputs (based on INV.l) for techs with more only one newv that cannot retire
        + pvf_onm(t) * sum{(i,v,r)$[valcap(i,v,r,t)$(one_newv(i))$(not retiretech(i,v,r,t))],
            cost_fom(i,v,r,t) * CAP.l(i,v,r,t)
            - sum{(tt)$[inv_cond(i,v,r,t,tt)$(not retiretech(i,v,r,tt))],
                INV.l(i,v,r,tt) * cost_fom(i,v,r,tt) * ilr(i) } }
* Account for difference in fixed O&M between model (CAP_ENERGY.l(i,v,r,t))
* and outputs (based on INV_ENERGY.l) for techs with more only one newv that cannot retire
        + pvf_onm(t) * sum{(i,v,r)$[valcap(i,v,r,t)$(one_newv(i))$(not retiretech(i,v,r,t))],
            cost_fom_energy(i,v,r,t) * CAP_ENERGY.l(i,v,r,t)
            - sum{(tt)$[inv_cond(i,v,r,t,tt)$(not retiretech(i,v,r,tt))],
                INV_ENERGY.l(i,v,r,tt) * cost_fom_energy(i,v,r,tt) * ilr(i) } }
* Objective function uses cumulative interzonal transmission capex but we report
* model-year investment, so subtract the difference between the two
        - (
            sum{r, systemcost_ba("inv_transmission_interzone_ac_investment",r,t) }
            - sum{r, capex_transmission_interzone_ac(r,t) }
        )
* Account for difference in capital costs of objective, which use cost_cap_fin_mult,
* and outputs, which use cost_cap_fin_mult_out
        + pvf_capital(t) * (
              sum{(i,v,r)$[valinv(i,v,r,t)],
                  cost_cap(i,t) * INV.l(i,v,r,t)
                  * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }

            + sum{(i,v,r)$[valinv(i,v,r,t)$battery(i)],
                  cost_cap_energy(i,t) * INV_ENERGY.l(i,v,r,t)
                  * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }
                  
            + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
                  cost_upgrade(i,v,r,t) * UPGRADES.l(i,v,r,t)
                  * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }

            + sum{(i,v,r,rscbin)$allow_cap_up(i,v,r,rscbin,t),
                  cost_cap_up(i,v,r,rscbin,t) * INV_CAP_UP.l(i,v,r,rscbin,t)
                  * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }

            + sum{(i,v,r,rscbin)$allow_ener_up(i,v,r,rscbin,t),
                  cost_ener_up(i,v,r,rscbin,t) * INV_ENER_UP.l(i,v,r,rscbin,t)
                  * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }

            + sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                  cost_cap(i,t) * INV_REFURB.l(i,v,r,t)
                  * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }
        )
* account for penalty paid to deploy capacity beyond interconnection queue limits        
        + sum{(tg,r), cap_penalty(tg) * CAP_ABOVE_LIM.l(tg,r,t) }  
    }
) / z.l ;

*Round error_check for z because of small number differences that always show up due to machine rounding and tolerances
error_check('z') = round(error_check('z'), 6) ;

* Check to see is any generation or capacity from dissallowed resources
error_check("gen") = sum{(i,v,r,allh,t)$[not valgen(i,v,r,t)], GEN.l(i,v,r,allh,t) } ;
error_gen(i,v,r,allh,t)$[not valgen(i,v,r,t)] = GEN.l(i,v,r,allh,t) ;
error_check("cap") = sum{(i,v,r,t)$[not valcap(i,v,r,t)], CAP.l(i,v,r,t) } ;
error_check("RPS") = sum{(RPSCat,i,st,ast,t)$[(not RecMap(i,RPSCat,st,ast,t))$[(not stfeas(ast)) or not sameas(ast,"voluntary")]], RECS.l(RPSCat,i,st,ast,t) } ;
error_check("OpRes") = sum{(ortype,i,v,r,h,t)$[not valgen(i,v,r,t)], OPRES.l(ortype,i,v,r,h,t) } ;
error_check("m_rsc_dat") = sum{(r,i,rscbin)$m_rsc_dat(r,i,rscbin,"cap"), m_rsc_dat_init(r,i,rscbin) - m_rsc_dat(r,i,rscbin,"cap") } ;

* Check to make sure there's no dropped/excess load in or after Sw_StartMarkets
error_check("dropped") = sum{(r,h,t)$[yeart(t)>=Sw_StartMarkets], DROPPED.l(r,h,t) } ;
error_check("excess") = sum{(r,h,t)$[yeart(t)>=Sw_StartMarkets], EXCESS.l(r,h,t) } ;

* Report DROPPED and EXCESS variable levels
dropped_load(r,h,t) = DROPPED.l(r,h,t) ;
excess_load(r,h,t) = EXCESS.l(r,h,t) ;

*======================
* Transmission
*======================

invtran_out(r,rr,trtype,t)$routes_inv(r,rr,trtype,t) = INVTRAN.l(r,rr,trtype,t) ;

tran_cap_energy(r,rr,trtype,t)$routes(r,rr,trtype,t) = CAPTRAN_ENERGY.l(r,rr,trtype,t) ;
tran_cap_prm(r,rr,trtype,t)$routes(r,rr,trtype,t) = CAPTRAN_PRM.l(r,rr,trtype,t) ;
tran_cap_grp(transgrp,transgrpp,t)$trancap_init_transgroup(transgrp,transgrpp,"AC")
    = CAPTRAN_GRP.l(transgrp,transgrpp,t) ;

tran_out(r,rr,trtype,t)$[(ord(r)<ord(rr))$routes(r,rr,trtype,t)] =
  (tran_cap_energy(r,rr,trtype,t) + tran_cap_energy(rr,r,trtype,t)) / 2 ;

tran_prm_out(r,rr,trtype,t)$[(ord(r)<ord(rr))$routes(r,rr,trtype,t)] =
  (tran_cap_prm(r,rr,trtype,t) + tran_cap_prm(rr,r,trtype,t)) / 2 ;

tran_mi_out_detail(r,rr,trtype,t)$routes(r,rr,trtype,t) = tran_out(r,rr,trtype,t) * distance(r,rr,trtype) ;

tran_mi_out(trtype,t)$tmodel_new(t) =
  sum{(r,rr)$routes(r,rr,trtype,t), tran_mi_out_detail(r,rr,trtype,t) } ;
tran_prm_mi_out(trtype,t)$tmodel_new(t) =
  sum{(r,rr)$routes(r,rr,trtype,t), tran_prm_out(r,rr,trtype,t) * distance(r,rr,trtype) } ;

cap_converter_out(r,t)$tmodel_new(t) = CAP_CONVERTER.l(r,t) ;

tran_flow_all_rep(r,rr,h,trtype,t)
    $[tmodel_new(t)$routes(r,rr,trtype,t)] = FLOW.l(r,rr,h,t,trtype) ;

tran_flow_all_stress(r,rr,allh,trtype,t)
    $[tmodel_new(t)$routes(r,rr,trtype,t)$h_stress_t(allh,t)] = FLOW.l(r,rr,allh,t,trtype) ;

tran_flow_rep(r,rr,h,trtype,t)
    $[tmodel_new(t)$routes(r,rr,trtype,t)$(ord(r) < ord(rr))] =
    FLOW.l(r,rr,h,t,trtype) - FLOW.l(rr,r,h,t,trtype)
;

tran_flow_stress(r,rr,allh,trtype,t)
    $[tmodel_new(t)$routes(r,rr,trtype,t)$(ord(r) < ord(rr))$h_stress_t(allh,t)] =
    FLOW.l(r,rr,allh,t,trtype) - FLOW.l(rr,r,allh,t,trtype)
;

tran_flow_rep_ann(r,rr,trtype,t)
  $[sum{h, tran_flow_rep(r,rr,h,trtype,t)}] =
  sum{h, hours(h) * tran_flow_rep(r,rr,h,trtype,t) }
;

tran_util_h_rep(r,rr,h,trtype,t)
    $[tmodel_new(t)$routes(r,rr,trtype,t)$tran_cap_energy(r,rr,trtype,t)] =
    FLOW.l(r,rr,h,t,trtype) / tran_cap_energy(r,rr,trtype,t)
;

tran_util_h_stress(r,rr,allh,trtype,t)
    $[tmodel_new(t)$routes(r,rr,trtype,t)$tran_cap_prm(r,rr,trtype,t)$h_stress_t(allh,t)] =
    FLOW.l(r,rr,allh,t,trtype) / tran_cap_prm(r,rr,trtype,t)
;

tran_util_ann_rep(r,rr,trtype,t)
    $[tmodel_new(t)$routes(r,rr,trtype,t)$tran_cap_energy(r,rr,trtype,t)] =
    sum{h, FLOW.l(r,rr,h,t,trtype) * hours(h) / tran_cap_energy(r,rr,trtype,t) }
    / sum{h, hours(h) }
;

tran_util_ann_stress(r,rr,trtype,t)
    $[tmodel_new(t)
    $routes(r,rr,trtype,t)$tran_cap_prm(r,rr,trtype,t)
    $sum{allh$h_stress_t(allh,t), hours(allh)}] =
    sum{allh$h_stress_t(allh,t),
        FLOW.l(r,rr,allh,t,trtype) * hours(allh) / tran_cap_prm(r,rr,trtype,t) }
    / sum{allh$h_stress_t(allh,t), hours(allh) }
;

import_h_rep(r,h,t)
    $[tmodel_new(t)] =
* Imports with losses
    sum{(rr,trtype)$routes(rr,r,trtype,t),
        FLOW.l(rr,r,h,t,trtype) * (1 - tranloss(rr,r,trtype)) }
;

export_h_rep(r,h,t)
    $[tmodel_new(t)] =
* Exports
    sum{(rr,trtype)$routes(r,rr,trtype,t), FLOW.l(r,rr,h,t,trtype) }
;

import_ann_rep(r,t)$[tmodel_new(t)] = sum{h, import_h_rep(r,h,t) * hours(h) } ;

export_ann_rep(r,t)$[tmodel_new(t)] = sum{h, export_h_rep(r,h,t) * hours(h) } ;

net_import_h_rep(r,h,t)
    $[tmodel_new(t)] =
* Imports with losses
    sum{(rr,trtype)$routes(rr,r,trtype,t),
        FLOW.l(rr,r,h,t,trtype) * (1 - tranloss(rr,r,trtype)) }
* Exports
    - sum{(rr,trtype)$routes(r,rr,trtype,t), FLOW.l(r,rr,h,t,trtype) }
;

net_import_h_stress(r,allh,t)
    $[tmodel_new(t)$h_stress_t(allh,t)] =
* Imports with losses
    sum{(rr,trtype)$routes(rr,r,trtype,t),
        FLOW.l(rr,r,allh,t,trtype) * (1 - tranloss(rr,r,trtype)) }
* Exports
    - sum{(rr,trtype)$routes(r,rr,trtype,t), FLOW.l(r,rr,allh,t,trtype) }
;

net_import_ann_rep(r,t)
    $[tmodel_new(t)] =
    sum{h, net_import_h_rep(r,h,t) * hours(h) }
;

net_import_ann_stress(r,t)
    $[tmodel_new(t)] =
    sum{allh$h_stress_t(allh,t), net_import_h_stress(r,allh,t) * hours(allh) }
;

poi_capacity(r,t)$tmodel_new(t) =
  poi_cap_init(r)
  + sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))], INV_POI.l(r,tt) }
;

*==========================
* Expenditures Exchanged
*==========================

expenditure_flow('load',r,rr,t)$[tmodel_new(t)$sum{trtype, routes(r,rr,trtype,t) }] =
  sum{h, hours(h) * reqt_price('load','na',r,h,t) * sum{trtype, FLOW.l(r,rr,h,t,trtype) } } ;
expenditure_flow('res_marg_ann',r,rr,t)$[tmodel_new(t)$Sw_PRM_CapCredit$sum{trtype, routes(r,rr,trtype,t) }] =
  sum{ccseason, reqt_price('res_marg','na',r,ccseason,t) * sum{trtype, captrade(r,rr,trtype,ccseason,t) } } ;
expenditure_flow('res_marg_ann',r,rr,t)$[tmodel_new(t)$(Sw_PRM_CapCredit=0)$routes_prm(r,rr)] =
  sum{allh$h_stress_t(allh,t), reqt_price('res_marg','na',r,allh,t) * sum{trtype, FLOW.l(r,rr,allh,t,trtype) } } ;
expenditure_flow('oper_res',r,rr,t)$[tmodel_new(t)$sum{trtype, routes(r,rr,trtype,t) }] =
  sum{(h,ortype), hours(h) * reqt_price('oper_res',ortype,r,h,t) * OPRES_FLOW.l(ortype,r,rr,h,t) } ;
*unlike for the three services above, use the destination price rather than the sending price for calculating RPS expenditure flows
expenditure_flow_rps(st,ast,t)$[tmodel_new(t)$[not sameas(st,ast)]] =
  (1 / cost_scale) * (1 / pvf_onm(t)) * sum{RPSCat, eq_REC_Requirement.m(RPSCat,ast,t) * sum{i, RECS.l(RPSCat,i,st,ast,t) } } ;
*International exports are negative expenditures, imports are positive. Use prices from the region where the imports/exports occur.
expenditure_flow_int(r,t)$tmodel_new(t) =
  sum{(i,v,h)$[canada(i)$valgen(i,v,r,t)], GEN.l(i,v,r,h,t) * hours(h) * reqt_price('load','na',r,h,t) }  - sum{h, hours(h) * reqt_price('load','na',r,h,t) * can_exports_h(r,h,t) } ;

*=========================
* Reduced Cost
*=========================
reduced_cost(i,v,r,t,"nobin","CAP")$valinv_init(i,v,r,t) = CAP.m(i,v,r,t)/(1000*cost_scale*pvf_capital(t)) ;
reduced_cost(i,v,r,t,"nobin","INV")$valinv_init(i,v,r,t) = INV.m(i,v,r,t)/(1000*cost_scale*pvf_capital(t)) ;
reduced_cost(i,v,r,t,rscbin,"INV_RSC")$[rsc_i(i)$valinv_init(i,v,r,t)$m_rscfeas(r,i,rscbin)] = INV_RSC.m(i,v,r,rscbin,t)/(1000*cost_scale*pvf_capital(t)) ;

*=========================
* Flexible load
*=========================
flex_load_out(flex_type,r,h,t) = FLEX.l(flex_type,r,h,t) ;
* peak_load_adj(r,ccseason,t) = PEAK_FLEX.l(r,ccseason,t) ;

loadsite_cap(r,t)$[Sw_LoadSiteCF$val_loadsite(r)] = CAP_LOADSITE.l(r,t) ;
loadsite_op(r,h,t)$[Sw_LoadSiteCF$(Sw_LoadSiteCF<1)$val_loadsite(r)] = OP_LOADSITE.l(r,h,t) ;
loadsite_op(r,h,t)$[(Sw_LoadSiteCF=1)$val_loadsite(r)] = CAP_LOADSITE.l(r,t) ;

*=========================
* Production activities
*=========================

* "--MW-- additional load from production activities"
prod_load(i,r,h,t)$[tmodel_new(t)$Sw_Prod$consume(i)] =
  sum{(p,v)$[valcap(i,v,r,t)$i_p(i,p)],
      PRODUCE.l(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) } ;

* "--MWh/year-- additional load from production activities"
prod_load_ann(i,r,t)$[tmodel_new(t)$Sw_Prod] =
  sum{h, hours(h) * prod_load(i,r,h,t) } ;

*"--metric tons/hour-- production capacity, note unit change from MW to metric tons/hour"
* [MW] * [metric tons/MWh] = [metric tons/h]
prod_cap(i,v,r,t)$[consume(i)$valcap(i,v,r,t)$Sw_Prod] =
  CAP.l(i,v,r,t) * prod_conversion_rate(i,v,r,t) ;

*"--metric tons/hour-- production activities by technology, BA, and timeslice"
prod_produce(i,r,h,t)$[valcap_irt(i,r,t)$Sw_Prod$consume(i)$tmodel_new(t)] =
  sum{(p,v)$[i_p(i,p)$valcap(i,v,r,t)], PRODUCE.l(p,i,v,r,h,t) } ;

*"--metric tons/year-- annual production by technology and BA"
prod_produce_ann(i,r,t)$[consume(i)$tmodel_new(t)$Sw_Prod] =
  sum{h, hours(h) * prod_produce(i,r,h,t) } ;

*"--$2004/metric ton-- national average marginal cost of producing H2"
* NB subsetting only on Sw_H2 here and not broader Sw_Prod
prod_h2_price(p,t)$[tmodel_new(t)$Sw_H2$sameas(p,"H2")] =
  (1 / cost_scale) * (1 / pvf_onm(t))
* price when using national demand
    * ( eq_h2_demand.m(p,t)$[Sw_H2=1] 
* price when using regional demand; varies by hour and region, so calculate annual price as the weighted average of demand
* divide by hours to get from $/[metric tons/hour] to $/metric ton
        + ( sum{(h,r), eq_h2_demand_regional.m(r,h,t) / hours(h) * h2_usage_regional(r,h,t) } 
            / sum{(h,r), h2_usage_regional(r,h,t) }
          )$[(Sw_H2=2)$(sum{(h,r), h2_usage_regional(r,h,t) })]
      )        
;

*"--$2004/mmbtu-- marginal cost of fuels used for H2-CT/CC combustion"
* NB2 - h2_combustion_intensity is in metric tons/mmbtu
*     - thus going from ($ / metric ton) * (metric tons / mmbtu) = $ / mmbtu
prod_h2comb_cost("H2",t)$[tmodel_new(t)$Sw_H2] =
  prod_h2_price("H2",t) * h2_combustion_intensity ;

*"--$2004-- BA- and tech-specific investment and operation costs associated with production activities"
*prod_syscosts(sys_costs,i,r,t)
prod_syscosts(sys_costs,i,r,t)$[tmodel_new(t)$consume(i)$Sw_Prod] =
  systemcost_techba(sys_costs,i,r,t) ;

prod_SMR_emit(e,r,t)$tmodel_new(t) =
  sum{(p,i,v,h)$[valcap(i,v,r,t)$smr(i)$i_p(i,p)],
      prod_emit_rate("process",e,i,t) * hours(h) * PRODUCE.l(p,i,v,r,h,t) } ;

* calculate exogenous H2 supply and H2-CT/CC consumption
h2_demand_by_sector("cross-sector",t) = sum{p, h2_exogenous_demand(p,t) } ;
h2_demand_by_sector("electricity",t) = sum{(i,v,r,h)$[valgen(i,v,r,t)$h2_combustion(i)],
        GEN.l(i,v,r,h,t) * hours(h) * h2_combustion_intensity * heat_rate(i,v,r,t) } ;

* Marginal cost of H2 production by timeslice [$/kg]
* eq_h2_demand_regional is in [metric tons/hour], just like eq_supply_demand_balance
* is in [MW] (or [MWh/hour]). So divide by hours(h) and kg/metric ton:
* [($·hour)/metric ton] / [hour] / [1000 kg/metric ton] = [$/kg]
h2_price_h(r,h,t)$tmodel_new(t) =
    (1 / cost_scale) * (1 / pvf_onm(t))
    * eq_h2_demand_regional.m(r,h,t)
    / hours(h) / 1000
;

* Marginal cost of H2 production by season [$/kg]
h2_price_szn(r,szn,t)$tmodel_new(t) =
    sum{h$h_szn(h,szn), h2_price_h(r,h,t) * hours(h) }
    / sum{h$h_szn(h,szn), hours(h) }
;

* generation that receives the hydrogen production tax credit for powering electrolyzers
h2_ptc_generation(i,v,r,h,t)$[tmodel_new(t)$Sw_H2_PTC] =
    CREDIT_H2PTC.l(i,v,r,h,t) * hours(h)
;

* marginal cost of producing an Energy Attribute Credit with regional and annual matching
h2_ptc_marginal_region(h2ptcreg,t)$[tmodel_new(t)$Sw_H2_PTC] =
  (1 / cost_scale) * (1 / pvf_onm(t))
  * eq_h2_ptc_region_balance.m(h2ptcreg,t)
;

* marginal cost of producing an Energy Attribute Credit with regional, hourly and annual matching
h2_ptc_marginal_region_hour(h2ptcreg,h,t)$[tmodel_new(t)$Sw_H2_PTC] =
  (1 / cost_scale) * (1 / pvf_onm(t))
  * eq_h2_ptc_region_hour_balance.m(h2ptcreg,h,t)
;

*========================================
* LOAD TYPES
*========================================

load_cat("end_use",r,t)$tmodel_new(t) = sum{h, hours(h) * load_exog(r,h,t) * (1.0 - distloss) } ;
load_cat("dist_loss",r,t)$tmodel_new(t)  = sum{h, hours(h) * load_exog(r,h,t) * distloss } ;
load_cat("trans_loss",r,t)$tmodel_new(t) = sum{(rr,h,trtype)$routes(r,rr,trtype,t), (tranloss(r,rr,trtype) * FLOW.l(r,rr,h,t,trtype) * hours(h)) } ;
load_cat("stor_charge",r,t)$tmodel_new(t) = sum{(i,v), stor_inout(i,v,r,t,"in") } ;
load_cat("h2_prod",r,t)$tmodel_new(t) = sum{i$h2(i), prod_load_ann(i,r,t) } ;
load_cat("h2_network",r,t)$tmodel_new(t) = 
    sum{h, hours(h) * 
    (
      sum{h2_stor$h2_stor_r(h2_stor,r),
          h2_network_load(h2_stor,t) * ( H2_STOR_IN.l(h2_stor,r,h,t) + H2_STOR_OUT.l(h2_stor,r,h,t) ) } 
      + sum{rr$h2_routes(r,rr),
            h2_network_load("h2_compressor",t) * (( H2_FLOW.l(r,rr,h,t) + H2_FLOW.l(rr,r,h,t) ) / 2) }
    )}$Sw_H2_CompressorLoad
;
load_cat("dac",r,t)$tmodel_new(t) = sum{i$dac(i), prod_load_ann(i,r,t) } ;

*========================================
* H2 NETWORK
*========================================

* flow of H2 in and out of storage; also include the change in level across representative periods
h2_inout(h2_stor,r,h,t,"in")$[(Sw_H2=2)$tmodel_new(t)$h2_stor_r(h2_stor,r)]
    = H2_STOR_IN.l(h2_stor,r,h,t) ;
h2_inout(h2_stor,r,h,t,"out")$[(Sw_H2=2)$tmodel_new(t)$h2_stor_r(h2_stor,r)]
    = H2_STOR_OUT.l(h2_stor,r,h,t) ;

* H2 storage level
h2_storage_level(h2_stor,r,actualszn,h,t)
    $[(Sw_H2=2)$tmodel_new(t)$h_actualszn(h,actualszn)$h2_stor_r(h2_stor,r)]
    = H2_STOR_LEVEL.l(h2_stor,r,actualszn,h,t) ;

h2_storage_level_szn(h2_stor,r,actualszn,t)
    $[(Sw_H2=2)$tmodel_new(t)$h2_stor_r(h2_stor,r)]
    = H2_STOR_LEVEL_SZN.l(h2_stor,r,actualszn,t) ;

* transport flow between BAs
h2_trans_flow(r,rr,h,t)
    $[(ord(r) < ord(rr))$tmodel_new(t)$h2_routes(r,rr)]
    = H2_FLOW.l(r,rr,h,t) - H2_FLOW.l(rr,r,h,t) ;

h2_trans_flow_all(r,rr,h,t)$[tmodel_new(t)$h2_routes(r,rr)] = H2_FLOW.l(r,rr,h,t) ;

* H2 storage capacity
h2_storage_cap(h2_stor,r,t)$tmodel_new(t) = H2_STOR_CAP.l(h2_stor,r,t) ;

* H2 transport capacity 
h2_trans_cap(r,rr,t)$[(ord(r) < ord(rr))$tmodel_new(t)] = sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))],
    H2_TRANSPORT_INV.l(r,rr,tt) + H2_TRANSPORT_INV.l(rr,r,tt) } ;

h2_usage(r,h,t)$tmodel_new(t) =
    h2_exogenous_demand_regional(r,'h2',h,t)
* [MW] * [metric tons/MMBtu] * [MMBtu/MWh] = [metric tons/h]
    + sum{(i,v)$[valgen(i,v,r,t)$h2_combustion(i)],
          GEN.l(i,v,r,h,t) * h2_combustion_intensity * heat_rate(i,v,r,t) } ;

*========================================
* Calculate powfrac
*========================================

$ifthene.powerfrac %GSw_calc_powfrac% == 1
$include e_powfrac_calc.gms
$endif.powerfrac

*========================================
* Dump results
*========================================

* The parameter list in the following file is read from e_report_params.csv
* and parsed in copy_files.py
execute_unload "outputs%ds%rep_%fname%.gdx"
$include e_report_paramlist.txt
;
