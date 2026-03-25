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
  inv_growth_penalty
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
  inv_transmission_intrazone_investment
  inv_transmission_line_investment
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
  op_h2ct_fuel_costs
  op_h2_fuel_costs
  op_h2_revenue_exog
  op_h2_transport
  op_h2_storage
  op_h2_vom
  op_operating_reserve_costs
  op_ptc_payments_negative
  op_rect_fuel_costs
  op_spurline_fom
  op_transmission_fom
  op_transmission_hurdle_rate
  op_transmission_intrazone_fom
  op_vom_costs
/,

sys_costs_inv(sys_costs) /
  inv_co2_network_pipe
  inv_co2_network_spur
  inv_converter_costs
  inv_dac
  inv_growth_penalty
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
  inv_transmission_intrazone_investment
  inv_transmission_line_investment
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
  op_h2ct_fuel_costs
  op_h2_fuel_costs
  op_h2_revenue_exog
  op_h2_transport
  op_h2_storage
  op_operating_reserve_costs
  op_ptc_payments_negative
  op_spurline_fom
  op_transmission_fom
  op_transmission_hurdle_rate
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

avg_avail(i,v) = sum{h, hours(h) * avail(i,h) * derate_geo_vintage(i,v) } / 8760 ;
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

lcoe(i,v,r,t,"bin1")$[(not rsc_i(i))$valcap(i,v,r,t)$ivt(i,v,t)$avg_avail(i,v)] =
* cost of capacity divided by generation
   ((crf(t) * cost_cap_fin_mult(i,r,t) * cost_cap(i,t)$newv(v)
     + cost_fom(i,v,r,t)
    ) / (avg_avail(i,v) * 8760))
*plus VOM costs
   + cost_vom(i,v,r,t)
* plus fuel costs - assuming constant fuel prices here (model prices might be different)
   + heat_rate(i,v,r,t) * fuel_price(i,r,t)
;

gen_rsc(i,v,r,t)$[valcap(i,v,r,t)$ivt(i,v,t)$rsc_i(i)] =
    sum{h, m_cf(i,v,r,h,t) * hours(h) } ;

lcoe(i,v,r,t,rscbin)$[valcap(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)] =
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

lcoe_cf_act(i,v,r,t,rscbin)$[valcap(i,v,r,t)$rsc_i(i)] = lcoe(i,v,r,t,rscbin) ;
lcoe_cf_act(i,v,r,t,"bin1")$[(not rsc_i(i))$valcap(i,v,r,t)$ivt(i,v,t)$avg_cf(i,v,r,t)] =
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

lcoe_nopol(i,v,r,t,rscbin)$valcap(i,v,r,t) = lcoe(i,v,r,t,rscbin) ;
lcoe_nopol(i,v,r,t,rscbin)$[valcap(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)] =
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

lcoe_fullpol(i,v,r,t,rscbin)$valcap(i,v,r,t) = lcoe(i,v,r,t,rscbin) ;
lcoe_fullpol(i,v,r,t,rscbin)$[valcap(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)] =
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
       + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
             UPGRADES.l(i,v,r,t) * (cost_upgrade(i,v,r,t) * cost_cap_fin_mult(i,r,t) ) }
       + sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)],
             INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) }
                 )
       + sum{v$valinv(i,v,r,t), cost_fom(i,v,r,t) * INV.l(i,v,r,t) }
       + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades], cost_fom(i,v,r,t) * UPGRADES.l(i,v,r,t) }
       + sum{(v,h)$[valinv(i,v,r,t)$INV.l(i,v,r,t)], (cost_vom(i,v,r,t)+ heat_rate(i,v,r,t) * fuel_price(i,r,t)) * GEN.l(i,v,r,h,t) * hours(h) }
       + sum{(v,h)$[UPGRADES.l(i,v,r,t)$Sw_Upgrades], (cost_vom(i,v,r,t)+ heat_rate(i,v,r,t) * fuel_price(i,r,t)) * GEN.l(i,v,r,h,t) * hours(h) }
        ) / (sum{(v,h)$[valinv(i,v,r,t)$INV.l(i,v,r,t)], GEN.l(i,v,r,h,t) * hours(h) }
            + sum{(v,h)$[UPGRADES.l(i,v,r,t)$Sw_Upgrades], GEN.l(i,v,r,h,t) * hours(h) })
;

lcoe_built_nat(i,t)$[sum{(v,r)$valinv(i,v,r,t), INV.l(i,v,r,t) }] =
                  sum{r, lcoe_built(i,r,t) * sum{v$valinv(i,v,r,t), INV.l(i,v,r,t) } }
                    / sum{(v,r)$valinv(i,v,r,t), INV.l(i,v,r,t) } ;

lcoe_pieces("capcost",i,r,t)$tmodel_new(t) = sum{v$valinv(i,v,r,t),
                  INV.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t) ) } ;

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
                  + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades], cost_fom(i,v,r,t) * UPGRADES.l(i,v,r,t)} ;

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

*Load and operating reserve prices are $/MWh, and reserve margin price is $/kW-yr
reqt_price('load','na',r,h,t)$[tmodel_new(t)$rb(r)] =
    (1 / cost_scale) * (1 / pvf_onm(t)) * eq_supply_demand_balance.m(r,h,t) / hours(h) ;

reqt_price('oper_res',ortype,r,h,t)$[tmodel_new(t)$rb(r)] =
    (1 / cost_scale) * (1 / pvf_onm(t)) * eq_OpRes_requirement.m(ortype,r,h,t) / hours(h) ;

reqt_price('state_rps',RPSCat,r,'ann',t)$[tmodel_new(t)$rb(r)] =
    (1 / cost_scale) * (1 / pvf_onm(t)) * sum{st$r_st(r,st), eq_REC_Requirement.m(RPSCat,st,t) } ;

reqt_price('nat_gen','na',r,'ann',t)$[tmodel_new(t)$rb(r)] =
    (1 / cost_scale) * (1 / pvf_onm(t)) * eq_national_gen.m(t) ;

reqt_price('annual_cap',e,r,'ann',t)$[tmodel_new(t)$rb(r)] =
    (1 / cost_scale) * (1 / pvf_onm(t)) * emit_scale(e) * eq_annual_cap.m(e,t) ;

* Capacity prices are in $/kW but constraints are in MW so divide by 1000
reqt_price('res_marg','na',r,allszn,t)$[tmodel_new(t)$rb(r)$szn_t(allszn,t)] =
    (1 / cost_scale) * (1 / pvf_onm(t)) / 1000 * (
* Capacity credit formulation
        eq_reserve_margin.m(r,allszn,t)$Sw_PRM_CapCredit
* Stress period formulation
        + smax{allh$[h_stress_t(allh,t)$h_szn_t(allh,allszn,t)],
               eq_supply_demand_balance.m(r,allh,t) }$[Sw_PRM_CapCredit=0]
    ) ;

reqt_price('res_marg_ann','na',r,'ann',t)$[tmodel_new(t)$rb(r)] =
    sum{allszn$szn_t(allszn,t), reqt_price('res_marg','na',r,allszn,t) } ;


*Load and operating reserve quantities are MWh, and reserve margin quantity is kW
* Demand from production activities (H2 and DAC) doesn't count toward electricity demand
reqt_quant('load','na',r,h,t)$[tmodel_new(t)$rb(r)] =
    hours(h) * (
        LOAD.l(r,h,t)
        - sum{(p,i,v)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)$Sw_Prod],
              PRODUCE.l(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) }
*** Alternative formulation for the above three lines (following eq_loadcon):
*         load_exog_static(r,h,t)
*         + can_exports_h(r,h,t)$[Sw_Canada=1]
*         + EVLOAD.l(r,h,t)$Sw_EV
*         + sum{flex_type, FLEX.l(flex_type,r,h,t) }$Sw_EFS_flex
    ) ;

reqt_quant('res_marg','na',r,allszn,t)$[tmodel_new(t)$rb(r)$szn_t(allszn,t)] = (
* Capacity credit formulation
    [(peakdem_static_szn(r,allszn,t) + PEAK_FLEX.l(r,allszn,t)) * (1+prm(r,t))]$Sw_PRM_CapCredit
* Stress period formulation
    + smax{allh$[h_stress_t(allh,t)$h_szn_t(allh,allszn,t)],
           LOAD.l(r,allh,t) }$[Sw_PRM_CapCredit=0]
) * 1000 ;

reqt_quant('res_marg_ann','na',r,'ann',t)$[tmodel_new(t)$rb(r)] =
    sum{allszn$szn_t(allszn,t), reqt_quant('res_marg','na',r,allszn,t) } ;

reqt_quant('oper_res',ortype,r,h,t)$[tmodel_new(t)$rb(r)] =
    hours(h) * (
        orperc(ortype,"or_load") * LOAD.l(r,h,t)
      + orperc(ortype,"or_wind") * sum{(i,v)$[wind(i)$valgen(i,v,r,t)],
          GEN.l(i,v,r,h,t) }
      + orperc(ortype,"or_pv")   * sum{(i,v)$[pv(i)$valcap(i,v,r,t)],
           CAP.l(i,v,r,t) }$dayhours(h)
    ) ;
reqt_quant('state_rps',RPSCat,r,'ann',t)$[tmodel_new(t)$rb(r)] =
    sum{(st,h)$r_st_rps(r,st), RecPerc(RPSCat,st,t) * hours(h) *(
        ( (LOAD.l(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]
        - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) }) * (1.0 - distloss)
        )$(RecStyle(st,RPSCat)=0)

      + ( LOAD.l(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]
        - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) }
        )$(RecStyle(st,RPSCat)=1)

      + ( sum{(i,v)$[valgen(i,v,r,t)$(not storage_standalone(i))], GEN.l(i,v,r,h,t)
          - (distloss * GEN.l(i,v,r,h,t))$(distpv(i) or dupv(i))
          - (STORAGE_IN_PVB_G.l(i,v,r,h,t) * storage_eff_pvb_g(i,t))$[pvb(i)$Sw_PVB] }
          - can_exports_h(r,h,t)$[(Sw_Canada=1)$sameas(RPSCat,"CES")]
        )$(RecStyle(st,RPSCat)=2)
    )} ;

reqt_quant('nat_gen','na',r,'ann',t)$[tmodel_new(t)$rb(r)] =
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
reqt_quant('annual_cap',e,r,'ann',t)$[tmodel_new(t)$rb(r)] = emit_cap(e,t) * load_frac_rt(r,t) ;


load_rt(r,t)$[tmodel_new(t)$rb(r)] = sum{h, hours(h) * load_exog(r,h,t) } ;

co2_price(t)$tmodel_new(t) = (1 / cost_scale) * (1 / pvf_onm(t)) / emit_scale("CO2") * eq_annual_cap.m("CO2",t) ;

rggi_price(t)$tmodel_new(t) = (1 / cost_scale) * (1 / pvf_onm(t)) / emit_scale("CO2") * eq_RGGI_cap.m(t) ;
rggi_quant(t)$tmodel_new(t) = RGGI_cap(t) / emit_scale('CO2') ;

state_cap_and_trade_price(st,t)$[tmodel_new(t)] =
    (1 / cost_scale) * (1 / pvf_onm(t))
    * eq_state_cap.m(st,t) / emit_scale("CO2") ;
state_cap_and_trade_quant(st,t)$[tmodel_new(t)] =
    state_cap(st,t) / emit_scale('CO2') ;

*========================================
* RPS AND CES CREDIT OUTPUTS
*========================================

rec_outputs(RPSCat,i,st,ast,t)$[stfeas(st)$(stfeas(ast) or sameas(ast,"voluntary"))$tmodel_new(t)] = RECS.l(RPSCat,i,st,ast,t) ;

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

repgasprice_r(rb,t)$[(Sw_GasCurve = 0 or Sw_GasCurve = 2)$tmodel_new(t)] = sum{cendiv$r_cendiv(rb,cendiv), repgasprice(cendiv,t) } ;

repgasprice_r(rb,t)$[(Sw_GasCurve = 1)$tmodel_new(t)] =
              ( sum{(h,cendiv),
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(rb,cendiv) *
                   hours(h) } / sum{h, hours(h) }

              + smax((fuelbin,cendiv)$[VGASBINQ_REGIONAL.l(fuelbin,cendiv,t)$r_cendiv(rb,cendiv)], gasbinp_regional(fuelbin,cendiv,t) )

              + smax(fuelbin$VGASBINQ_NATIONAL.l(fuelbin,t), gasbinp_national(fuelbin,t) )
              ) ;

repgasprice(cendiv,t)$[(Sw_GasCurve = 1)$tmodel_new(t)$repgasquant(cendiv,t)] =
    sum{(i,rb)$r_cendiv(rb,cendiv), repgasprice_r(rb,t) * repgasquant_irt(i,rb,t) } / repgasquant(cendiv,t) ;

repgasprice_nat(t)$[tmodel_new(t)$sum{cendiv, repgasquant(cendiv,t) }] =
    sum{cendiv, repgasprice(cendiv,t) * repgasquant(cendiv,t) }
    / sum{cendiv, repgasquant(cendiv,t) } ;

*========================================
* NATURAL GAS FUEL COSTS
*========================================

gasshare_ba(r,cendiv,t)$[r_cendiv(r,cendiv)$tmodel_new(t)$repgasquant(cendiv,t)] =
                 sum{i$[sum{v,valgen(i,v,r,t)}$gas(i)],repgasquant_irt(i,r,t) / repgasquant(cendiv,t) } ;

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

* Calculate generation and include charging, pumping, DR shifted load, and production as negative values
gen_h(i,r,h,t)$[tmodel_new(t)$sum{v,valgen(i,v,r,t)}] =
  sum{v$valgen(i,v,r,t), GEN.l(i,v,r,h,t)
* less storage charging
  - STORAGE_IN.l(i,v,r,h,t)$[storage_standalone(i) or hyd_add_pump(i)]
* less DR shifting
  - sum{(hh)$[dr1(i)$DR_SHIFT.l(i,v,r,h,hh,t)], DR_SHIFT.l(i,v,r,h,hh,t) / hours(h) / storage_eff(i,t)} }
* less load from hydrogen production
  - sum{(v,p)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)], PRODUCE.l(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t)}$Sw_Prod
;
* Add net Canadian imports/exports if treating exogenously
gen_h('can-imports',r,h,t)$[(Sw_Canada=2)$tmodel_new(t)] = net_trade_can(r,h,t) ;
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

* Do it again for stress periods
gen_h_stress(i,r,allh,t)$[tmodel_new(t)$sum{v,valgen(i,v,r,t)}$h_stress_t(allh,t)] =
  sum{v$valgen(i,v,r,t), GEN.l(i,v,r,allh,t)
* less storage charging
      - STORAGE_IN.l(i,v,r,allh,t)$[storage_standalone(i) or hyd_add_pump(i)] }
* less load from hydrogen production
  - sum{(v,p)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)],
        PRODUCE.l(p,i,v,r,allh,t) / prod_conversion_rate(i,v,r,t)}$Sw_Prod
;
* Add net Canadian imports/exports if treating exogenously
gen_h('can-imports',r,allh,t)$[(Sw_Canada=2)$tmodel_new(t)] = net_trade_can(r,allh,t) ;

gen_ann(i,r,t)$tmodel_new(t) = sum{h, gen_h(i,r,h,t) * hours(h) } ;

* Report generation without the charging, DR, and production included as above
gen_ivrt(i,v,r,t)$valgen(i,v,r,t) = sum{h, GEN.l(i,v,r,h,t) * hours(h) } ;
gen_ivrt_uncurt(i,v,r,t)$[(vre(i) or pvb(i))$valgen(i,v,r,t)] =
  sum{h, m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) * hours(h) } ;
stor_inout(i,v,r,t,"in")$[valgen(i,v,r,t)$storage(i)$[not pvb(i)]] = sum{h, STORAGE_IN.l(i,v,r,h,t) * hours(h) } ;
stor_inout(i,v,r,t,"out")$[valgen(i,v,r,t)$storage(i)] = gen_ivrt(i,v,r,t) ;
stor_in(i,v,r,h,t)$[storage(i)$valgen(i,v,r,t)$(not pvb(i))] = STORAGE_IN.l(i,v,r,h,t) ;
stor_out(i,v,r,h,t)$[storage(i)$valgen(i,v,r,t)] = GEN.l(i,v,r,h,t) ;
stor_level(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)] = STORAGE_LEVEL.l(i,v,r,h,t) ;


*=====================================================================
* WATER ACCOUNTING, CAPACITY, NEW CAPACITY, AND RETIRED CAPACITY
*=====================================================================
water_withdrawal_ivrt(i,v,r,t)$valgen(i,v,r,t) = sum{h$valgen(i,v,r,t), WAT.l(i,v,"with",r,h,t) } ;
water_consumption_ivrt(i,v,r,t)$valgen(i,v,r,t) = sum{h$valgen(i,v,r,t), WAT.l(i,v,"cons",r,h,t) } ;

watcap_ivrt(i,v,r,t)$valcap(i,v,r,t) = WATCAP.l(i,v,r,t) ;
watcap_out(i,r,t)$valcap_irt(i,r,t) = sum{v$valcap(i,v,r,t), WATCAP.l(i,v,r,t) } ;
watcap_new_ivrt(i,v,r,t)$valcap(i,v,r,t) =
    (8760/1E6) * sum{w$[i_w(i,w)], water_rate(i,w,r) * ( INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) ) }
  + WATCAP.L(i,v,r,t)$psh(i) ;
watcap_new_out(i,r,t)$valcap_irt(i,r,t) =
    (8760/1E6) * sum{(w,v)$[i_w(i,w)$valinv(i,v,r,t)], water_rate(i,w,r) * ( INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) ) }
  + sum{v$[psh(i)$valinv(i,v,r,t)], WATCAP.L(i,v,r,t)} ;
watcap_new_ann_out(i,v,r,t)$watcap_new_ivrt(i,v,r,t) = watcap_new_ivrt(i,v,r,t) / (yeart(t) - sum(tt$tprev(t,tt), yeart(tt))) ;

watret_out(i,v,r,t)$[(not tfirst(t))$valcap_irt(i,r,t)] = sum{tt$tprev(t,tt), watcap_ivrt(i,v,r,tt)} - watcap_ivrt(i,v,r,t) + watcap_new_ivrt(i,v,r,t) ;
watret_out(i,v,r,t)$[(abs(watret_out(i,v,r,t)) < 1e-6)] = 0 ;
watret_ann_out(i,v,r,t)$watret_out(i,v,r,t) = watret_out(i,v,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;

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

gen_new_uncurt(i,r,h,t)$[(vre(i) or pvb(i))$valcap_irt(i,r,t)] =
      sum{v$valinv(i,v,r,t), (INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)) * m_cf(i,v,r,h,t) * hours(h) }
;

* Formulation follows eq_curt_gen_balance(r,h,t); since it uses =g= there may be extra curtailment
* beyond CURT.l(r,h,t) so we recalculate as (availability - generation - operating reserves)
curt_h(r,h,t)$tmodel_new(t) =
      sum{(i,v)$[valcap(i,v,r,t)$(vre(i) or pvb(i))],
          m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) }
    - sum{(i,v)$[valgen(i,v,r,t)$vre(i)], GEN.l(i,v,r,h,t) }
    - sum{(i,v)$[valgen(i,v,r,t)$pvb(i)], GEN_PVB_P.l(i,v,r,h,t) }$Sw_PVB
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

curt_rate_tech(i,rb,t)$[tmodel_new(t)$vre(i)$curt_tech(i,rb,t)$gen_ann(i,rb,t)] =
    curt_tech(i,rb,t) / (gen_ann(i,rb,t) + curt_tech(i,rb,t))
;

curt_rate(t)$tmodel_new(t) = sum{r, curt_ann(r,t) } /
      (sum{(i,r)$[vre(i) or pvb(i)], gen_ann(i,r,t) } + sum{r, curt_ann(r,t) }) ;

losses_ann('storage',t)$tmodel_new(t) = sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)], STORAGE_IN.l(i,v,r,h,t) * hours(h) }
                          - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)], GEN.l(i,v,r,h,t) * hours(h) } ;

losses_ann('trans',t)$tmodel_new(t) =
  sum{(rr,r,h,trtype)$routes(rr,r,trtype,t),
      (tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) * hours(h)) } ;

losses_ann('curt',t)$tmodel_new(t) =  sum{r, curt_ann(r,t) } ;

losses_ann('load',t)$tmodel_new(t) = sum{(r,h), LOAD.l(r,h,t) * hours(h) }  ;

losses_tran_h(rr,r,h,trtype,t)$[routes(r,rr,trtype,t)$tmodel_new(t)]
    = tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) ;

*=========================
* CAPACTIY
*=========================

cap_deg_ivrt(i,v,r,t)$valcap(i,v,r,t) = CAP.l(i,v,r,t) / ilr(i) ;

cap_ivrt(i,v,r,t)$[(not (upv(i) or dupv(i) or wind(i)))$valcap(i,v,r,t)] = cap_deg_ivrt(i,v,r,t) ;
*upv, dupv, and wind have degradation, so use INV rather than CAP to get the reported capacity
cap_ivrt(i,v,r,t)$[(upv(i) or dupv(i) or wind(i))$valcap(i,v,r,t)] = (
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

* Exogenous capacity (used by reeds_to_rev)
cap_exog(i,v,r,t)$tmodel_new(t) = m_capacity_exog(i,v,r,t) ;

*=========================
* NEW CAPACITY
*=========================

cap_new_out(i,r,t)$[(not tfirst(t))$valcap_irt(i,r,t)] = [
  sum{v$valinv(i,v,r,t), INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) }
  + sum{v$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades], 
        (1 - upgrade_derate(i,v,r,t)) * UPGRADES.l(i,v,r,t)} ] / ilr(i) ;

cap_new_out("distpv",r,t)$[valcap_irt("distpv",r,t)$(not tfirst(t))] = cap_out("distpv",r,t) - sum{tt$tprev(t,tt), cap_out("distpv",r,tt) } ;
cap_new_ann(i,r,t)$cap_new_out(i,r,t) = cap_new_out(i,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;
cap_new_bin_out(i,v,r,t,rscbin)$[rsc_i(i)$valinv(i,v,r,t)] = INV_RSC.l(i,v,r,rscbin,t) / ilr(i) ;
cap_new_bin_out(i,v,r,t,"bin1")$[(not rsc_i(i))$valinv(i,v,r,t)] = INV.l(i,v,r,t) / ilr(i) ;
cap_new_ivrt(i,v,r,t)$[(not tfirst(t))$valcap(i,v,r,t)] = {
  [INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)]$valinv(i,v,r,t)
  + (1-upgrade_derate(i,v,r,t)) * UPGRADES.l(i,v,r,t)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades] } / ilr(i) ;
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
    + rsc_dr(i,r,"cap",rscbin,t)

- (
    sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) < yeart(t))$rsc_agg(i,ii)$(not dr(i))],
         INV_RSC.l(ii,v,r,rscbin,tt) * resourcescaler(ii) }

    + sum{(ii,v,tt)$[tfirst(tt)$rsc_agg(i,ii)$(not dr(i))$exog_rsc(i)],
         capacity_exog_rsc(ii,v,r,rscbin,tt) }
);

*=========================
* UPGRADED CAPACITY
*=========================

cap_upgrade(i,r,t)$[upgrade(i)$valcap_irt(i,r,t)] = sum{v, (1-upgrade_derate(i,v,r,t)) * UPGRADES.l(i,v,r,t) } ;
cap_upgrade_ivrt(i,v,r,t)$[valcap(i,v,r,t)$upgrade(i)$Sw_Upgrades] = (1-upgrade_derate(i,v,r,t)) * UPGRADES.l(i,v,r,t) ;

*=========================
* RETIRED CAPACITY
*=========================

ret_out(i,r,t)$[(not tfirst(t))] = sum{tt$tprev(t,tt), cap_out(i,r,tt)} - cap_out(i,r,t) + cap_new_out(i,r,t) ;
ret_out(i,r,t)$[abs(ret_out(i,r,t)) < 1e-6] = 0 ;
ret_ann(i,r,t)$ret_out(i,r,t) = ret_out(i,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;

ret_ivrt(i,v,r,t)$[(not tfirst(t))] = sum{tt$tprev(t,tt), cap_ivrt(i,v,r,tt)} - cap_ivrt(i,v,r,t) + cap_new_ivrt(i,v,r,t) ;
ret_ivrt(i,v,r,t)$[abs(ret_ivrt(i,v,r,t)) < 1e-6] = 0 ;

*==================================
* BINNED STORAGE CAPACITY
*==================================

cap_sdbin_out(i,r,szn,sdbin,t)$valcap_irt(i,r,t) = sum{v, CAP_SDBIN.l(i,v,r,szn,sdbin,t)} ;

* energy capacity of storage
stor_energy_cap(i,v,r,t)$[tmodel_new(t)$valcap(i,v,r,t)] =
        storage_duration(i) * CAP.l(i,v,r,t) * (1$CSP_Storage(i) + 1$psh(i) + bcr(i)$[battery(i) or pvb(i)]) ;

*==================================
* CAPACITY CREDIT AND FIRM CAPACITY
*==================================

cc_all_out(i,v,r,szn,t)$tmodel_new(t) =
    cc_int(i,v,r,szn,t)$[(vre(i) or csp(i) or storage(i) or pvb(i))$valcap(i,v,r,t)] +
    m_cc_mar(i,r,szn,t)$[(vre(i) or csp(i) or storage(i) or pvb(i))$valinv(i,v,r,t)]+
    m_cc_dr(i,r,szn,t)$[dr(i)$valinv(i,v,r,t)]
;

cap_new_cc(i,r,szn,t)$[(vre(i) or storage(i) or pvb(i))$valcap_irt(i,r,t)] = sum{v$ivt(i,v,t),cap_new_ivrt(i,v,r,t) } ;

cc_new(i,r,szn,t)$[valcap_irt(i,r,t)$cap_new_cc(i,r,szn,t)] = sum{v$ivt(i,v,t), cc_all_out(i,v,r,szn,t) } ;

cap_firm(i,r,szn,t)$[valcap_irt(i,r,t)$[not consume(i)]$tmodel_new(t)] =
      sum{v$[(not vre(i))$(not hydro(i))$(not storage(i))$(not pvb(i))$(not dr(i))$valcap(i,v,r,t)],
          CAP.l(i,v,r,t) * (1 + seas_cap_frac_delta(i,v,r,szn,t)) }
    + cc_old(i,r,szn,t)
    + sum{v$[(vre(i) or csp(i) or pvb(i))$valinv(i,v,r,t)],
         m_cc_mar(i,r,szn,t) * (INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)$[refurbtech(i)$Sw_Refurb]) }
    + sum{v$[(vre(i) or csp(i) or pvb(i))$valcap(i,v,r,t)],
            cc_int(i,v,r,szn,t) * CAP.l(i,v,r,t) }
    + sum{v$dr(i),
            m_cc_dr(i,r,szn,t) * CAP.l(i,v,r,t) }
    + cc_excess(i,r,szn,t)$[(vre(i) or csp(i) or pvb(i))]
    + sum{(v,h)$[hydro_nd(i)$valgen(i,v,r,t)$h_szn_prm(h,szn)],
         GEN.l(i,v,r,h,t) }
    + sum{v$[hydro_d(i)$valcap(i,v,r,t)],
         CAP.l(i,v,r,t) * cap_hyd_szn_adj(i,szn,r) * (1 + hydro_capcredit_delta(i,t)) }
    + sum{(v,sdbin)$[valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))], CAP_SDBIN.l(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin) }
    + sum{(v,sdbin)$[valcap(i,v,r,t)$storage_hybrid(i)], CAP_SDBIN.l(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin) * hybrid_cc_derate(i,r,szn,sdbin,t) } ;

* Capacity trading to meet PRM
captrade(r,rr,trtype,szn,t)$[routes(r,rr,trtype,t)$routes_prm(r,rr)$tmodel_new(t)] = PRMTRADE.l(r,rr,trtype,szn,t) ;

*========================================
* REVENUE LEVELS
*========================================

revenue('load',i,r,t)$valgen_irt(i,r,t) = sum{(v,h)$valgen(i,v,r,t),
  GEN.l(i,v,r,h,t) * hours(h) * reqt_price('load','na',r,h,t) } ;

*revenue from storage charging (storage charging from curtailment recovery does not have a cost)
revenue('charge',i,r,t)$[storage_standalone(i)$valgen_irt(i,r,t)] = - sum{(v,h)$valgen(i,v,r,t),
  STORAGE_IN.l(i,v,r,h,t) * hours(h) * reqt_price('load','na',r,h,t) } ;

revenue('res_marg',i,r,t)$valgen_irt(i,r,t) = sum{szn,
  cap_firm(i,r,szn,t) * reqt_price('res_marg','na',r,szn,t) * 1000 } ;

revenue('oper_res',i,r,t)$valgen_irt(i,r,t) = sum{(ortype,v,h)$valgen(i,v,r,t),
  OPRES.l(ortype,i,v,r,h,t) * hours(h) * reqt_price('oper_res',ortype,r,h,t) } ;

revenue('rps',i,r,t)$valgen_irt(i,r,t) =
  sum{(v,h,RPSCat)$[valgen(i,v,r,t)$sum{st$r_st(r,st), RecTech(RPSCat,i,st,t) }],
      GEN.l(i,v,r,h,t) * sum{st$r_st(r,st), RPSTechMult(RPSCat,i,st) } * hours(h) * reqt_price('state_rps',RPSCat,r,'ann',t) } ;

revenue_nat(rev_cat,i,t)$tmodel_new(t) = sum{r, revenue(rev_cat,i,r,t) } ;

revenue_en(rev_cat,i,r,t)$[tmodel_new(t)$sum{(v,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t)}$[not vre(i)]] =
  revenue(rev_cat,i,r,t) / sum{(v,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t) * hours(h) } ;

revenue_en(rev_cat,i,r,t)$[tmodel_new(t)$sum{(v,h)$[valcap(i,v,r,t)], m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) }$vre(i)] =
  revenue(rev_cat,i,r,t) / sum{(v,h)$valcap(i,v,r,t),
      m_cf(i,v,r,h,t) * CAP.l(i,v,r,t) * hours(h) } ;

revenue_en_nat(rev_cat,i,t)$[tmodel_new(t)$sum{(v,r,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t) }] =
  revenue_nat(rev_cat,i,t) / sum{(v,r,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t) * hours(h) } ;

revenue_cap(rev_cat,i,r,t)$[tmodel_new(t)$cap_out(i,r,t)] =
  revenue(rev_cat,i,r,t) / cap_out(i,r,t) ;

revenue_cap_nat(rev_cat,i,t)$[tmodel_new(t)$sum{r$valcap_irt(i,r,t), cap_out(i,r,t) }] =
  revenue_nat(rev_cat,i,t) / sum{r$valcap_irt(i,r,t), cap_out(i,r,t) } ;

gen_ann_nat(i,t)$tmodel_new(t) = sum{r, gen_ann(i,r,t) } ;

*=========================
* EMISSIONS
*=========================
emit_r(e,r,t)$tmodel_new(t) = EMIT.l(e,r,t) * emit_scale(e) ;
* Apply global warming potential to include methane in CO2(e)
emit_r("CO2e",r,t)$tmodel_new(t) = emit_r("CO2",r,t) + emit_r("CH4",r,t) * Sw_MethaneGWP ;
emit_nat(eall,t)$tmodel_new(t) = sum{r, emit_r(eall,r,t) } ;

* Generation emissions by tech and region
emit_irt(e,i,r,t)$[tmodel_new(t)$(not sameas(e,"CO2"))] = sum{(v,h)$[valgen(i,v,r,t)],
         hours(h) * emit_rate(e,i,v,r,t) * GEN.l(i,v,r,h,t) } ;
* Production-related emissions by tech and region
emit_irt(e,i,r,t)$[tmodel_new(t)$(not sameas(e,"CO2"))$sum{p, i_p(i,p)}] =
         sum{(p,v,h)$i_p(i,p),
         hours(h) * prod_emit_rate(e,i,t) * PRODUCE.l(p,i,v,r,h,t) } ;
* CO2 generation emissions by tech and region
emit_irt("CO2",i,r,t)$tmodel_new(t) = sum{(v,h)$[valgen(i,v,r,t)],
         hours(h) * emit_rate("CO2",i,v,r,t) * GEN.l(i,v,r,h,t) } / emit_scale("CO2") ;
* CO2 production-related emissions by tech and region
emit_irt("CO2",i,r,t)$[tmodel_new(t)$sum{p, i_p(i,p)}] =
         sum{(p,v,h)$i_p(i,p),
         hours(h) * prod_emit_rate("CO2",i,t) * PRODUCE.l(p,i,v,r,h,t) }  / emit_scale("CO2") ;
* Apply global warming potential to include methane in CO2(e)
emit_irt("CO2e",i,r,t)$tmodel_new(t) = emit_irt("CO2",i,r,t) + emit_irt("CH4",i,r,t) * Sw_MethaneGWP ;

emit_nat_tech(e,i,t) = sum{r, emit_irt(e,i,r,t)} ;

emit_weighted(eall) = sum{t$tmodel(t), emit_nat(eall,t) * pvf_onm(t) } ;

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
                      + sum{(rscbin)$m_rscfeas(r,i,rscbin),INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * cost_cap_fin_mult_no_credits(i,r,t) }
                      + (INV_REFURB.l(i,v,r,t) * (cost_cap_fin_mult_no_credits(i,r,t) * cost_cap(i,t)))$[refurbtech(i)$Sw_Refurb]
                      + UPGRADES.l(i,v,r,t) * (cost_upgrade(i,v,r,t) * cost_cap_fin_mult_out(i,r,t))$[upgrade(i)$Sw_Upgrades] ;

*=========================
* Tech|BA-Level SYSTEM COST: Capital
*=========================

* REPLICATION OF THE OBJECTIVE FUNCTION
* DOES NOT INCLUDE COSTS NOT INDEXED BY TECH (e.g., TRANSMISSION)

systemcost_techba("inv_investment_capacity_costs",i,r,t)$tmodel_new(t) =
*investment costs (without the subtraction of any ITC/PTC value)
              sum{v$valinv(i,v,r,t),
                   INV.l(i,v,r,t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t) ) }
*plus supply curve adjustment to capital cost (separated in outputs but part of m_rsc_dat(r,i,rscbin,"cost"))
              + sum{(v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$[not sccapcosttech(i)]$(not spur_techs(i))],
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost_cap") * rsc_fin_mult(i,r,t) }
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

systemcost_techba("inv_itc_payments_negative",i,r,t)$tmodel_new(t) =
*investment costs (including reduction from ITC)
                sum{v$valinv(i,v,r,t),
                   INV.l(i,v,r,t) * (cost_cap_fin_mult_out(i,r,t) * cost_cap(i,t) ) }
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
;

*assign consume techs to their own category and then zero it out
systemcost_techba("inv_dac",i,r,t)$[tmodel_new(t)$dac(i)] = systemcost_techba("inv_investment_capacity_costs",i,r,t) ;
systemcost_techba("inv_h2_production",i,r,t)$[tmodel_new(t)$h2(i)] = systemcost_techba("inv_investment_capacity_costs",i,r,t) ;
systemcost_techba("inv_investment_capacity_costs",i,r,t)$[tmodel_new(t)$consume(i)] = 0 ;

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
                  $(not spur_techs(i))],
*investment in resource supply curve technologies
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost_trans") * rsc_fin_mult(i,r,t) }
;

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
              + (8760/1E6) * sum{ (v,w)$[i_w(i,w)$valinv(i,v,r,t)], sum{wst$i_wst(i,wst), m_watsc_dat(wst,"cost",r,t)} * water_rate(i,w,r) *
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
              + sum{v$[valcap(i,v,r,t)],
                   cost_fom(i,v,r,t) * cap_ivrt(i,v,r,t) * ilr(i) }
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
              + sum{(v,h)$[valgen(i,v,r,t)$[not gas(i)]$heat_rate(i,v,r,t)
                              $[not bio(i)]$[not cofire(i)]],
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
                    hours(h) * emit_rate(e,i,v,r,t) * GEN.l(i,v,r,h,t) / emit_scale(e) * emit_tax(e,r,t) }
;

systemcost_techba("op_h2_fuel_costs",i,r,t)$tmodel_new(t)  =
* H2 production costs 
              sum{(v,h,p)$[h2(i)$valcap(i,v,r,t)],
                  hours(h) * h2_fuel_cost(i,v,r,t) * PRODUCE.l(p,i,v,r,h,t) }
;

systemcost_techba("op_h2ct_fuel_costs",i,r,t)$[tmodel_new(t)$h2_ct(i)$Sw_H2]  =
* fuel costs for H2-CT techs
              + (1 / cost_scale) * (1 / pvf_onm(t))
* when using national demand, calculate total annual demand and multiply by national average price
* [MW] * [hours] * [MMBTU/MWh] * [tonnes/MMBTU] * [$/tonne] = [$]
              * ( (sum{(v,h), GEN.l(i,v,r,h,t) * hours(h) * heat_rate(i,v,r,t) * h2_ct_intensity  } 
                    *  eq_h2_demand.m("h2",t) 
                  )$[Sw_H2 = 1]
* when using regional demand by hour, apply price to each hour and then sum total costs
* [MW] * [hours] * [MMBTU/MWh] * [tonnes/MMBTU] * [$/[tonne/hour]] / [hours] = [$]
                + (sum{(v,h), GEN.l(i,v,r,h,t) * hours(h) * heat_rate(i,v,r,t) * h2_ct_intensity 
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
              emit_captured_irt(i,r,t) * CO2_storage_cost
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

systemcost_ba("inv_growth_penalty",r,t)$[tmodel_new(t)$(yeart(t)>=model_builds_start_yr)]  =
*costs of growth penalties
              sum{(gbin,i,st)$[valinv_irt(i,r,t)$stfeas(st)$r_st(r,st)],
                        cost_growth(i,st,t) * growth_penalty(gbin) * GROWTH_BIN.l(gbin,i,st,t)
                        * sum{h, reqt_quant('load','na',r,h,t) * hours(h) }
                        / sum{(rr,h)$r_st(rr,st), reqt_quant('load','na',rr,h,t) * hours(h) }
                 }
;

systemcost_ba("inv_transmission_line_investment",r,t)$tmodel_new(t)  =
*costs of transmission lines
              sum{(rr,trtype)$[routes(r,rr,trtype,t)$routes_inv(r,rr,trtype,t)],
                    trans_cost_cap_fin_mult(t) * transmission_line_capcost(r,rr,trtype)
                    * (INVTRAN.l(r,rr,trtype,t) + trancap_fut(r,rr,"certain",trtype,t))  }
;

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
*cost of LCC AC/DC converter stations (each LCC DC line implicitly has two, one on each end of the line)
              sum{(rr,trtype)$[lcclike(trtype)$routes_inv(r,rr,trtype,t)],
                  trans_cost_cap_fin_mult(t) * cost_acdc_lcc * 2 * INVTRAN.l(r,rr,trtype,t) }
*cost of VSCC AC/DC converter stations
              + trans_cost_cap_fin_mult(t) * cost_acdc_vsc * INV_CONVERTER.l(r,t)
;

systemcost_ba("inv_spurline_investment",rb,t)$[tmodel_new(t)$Sw_SpurScen] =
* capital cost of spur lines modeled explicitly
              sum{x$[xfeas(x)$x_rb(x,rb)], spurline_cost(x) * Sw_SpurCostMult * INV_SPUR.l(x,t) }
;

systemcost_ba("op_spurline_fom",rb,t)$[tmodel_new(t)] =
* fixed O&M cost of spur lines modeled explicitly
    sum{x$[Sw_SpurScen$xfeas(x)$x_rb(x,rb)], spurline_cost(x) * trans_fom_frac * CAP_SPUR.l(x,t) }
* fixed O&M cost of spur lines modeled as part of supply curve
    + sum{(i,v,rscbin)
          $[m_rscfeas(rb,i,rscbin)$valcap(i,v,rb,t)
          $rsc_i(i)$(not spur_techs(i))$(not sccapcosttech(i))],
          m_rsc_dat(rb,i,rscbin,"cost_trans") * trans_fom_frac * CAP_RSC.l(i,v,rb,rscbin,t)
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

systemcost_ba("op_transmission_hurdle_rate",r,t)$[tmodel_new(t)]  =
*plus hurdle costs for transmission flow
              sum{(rr,h,trtype)$[routes(r,rr,trtype,t)$cost_hurdle(r,rr)],
                   cost_hurdle(r,rr) * hours(h) * FLOW.l(r,rr,h,t,trtype)  }
;


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

systemcost_ba("op_h2_storage",r,t)$[tmodel_new(t)$(Sw_H2 = 2)] = 
    sum{h2_stor$h2_stor_r(h2_stor,r),
        cost_h2_storage_fom(h2_stor,t) * H2_STOR_CAP.l(h2_stor,r,t) }
;

systemcost_ba("op_acp_compliance_costs",r,t)$[tmodel_new(t)$(yeart(t)>=RPS_StartYear)]  =
*plus ACP purchase costs, attributed to bas based on fraction of state requirement
              + sum{(st,RPSCat)$[stfeas(st)$r_st(r,st)$RecPerc(RPSCat,st,t)],
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


*If the op_rect_fuel_costs are included in the systemcost_ba it will lead to double-counting
*but these fuel costs are needed for the retail rate module. We therefore zero them out here.
systemcost_ba_retailrate(sys_costs,r,t) = systemcost_ba(sys_costs,r,t) ;
systemcost_ba("op_h2ct_fuel_costs",r,t) = 0 ;

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

error_check('z') = (z.l - sum{t$tmodel(t), cost_scale *
                             (pvf_capital(t) * raw_inv_cost(t) + pvf_onm(t) * raw_op_cost(t))
*minus small penalty to move storage into shorter duration bins
                             - pvf_capital(t) * sum{(i,v,r,szn,sdbin)$[valcap(i,v,r,t)$[storage(i) or hyd_add_pump(i)]], bin_penalty(sdbin) * CAP_SDBIN.l(i,v,r,szn,sdbin,t) }
*minus retirement penalty
                             - pvf_onm(t) * sum{(i,v,r)$[valcap(i,v,r,t)$retiretech(i,v,r,t)],
                                  cost_fom(i,v,r,t) * retire_penalty(t) * (CAP.l(i,v,r,t) - INV.l(i,v,r,t) - INV_REFURB.l(i,v,r,t)$[refurbtech(i)$Sw_Refurb]) }
*minus revenue from purchases of curtailed VRE
                             - pvf_onm(t) * sum{(r,h), CURT.l(r,h,t) * hours(h) * cost_curt(t) }$Sw_CurtMarket
* Minus penalty cost for dropped load before Sw_StartMarkets
                             - pvf_onm(t) * sum{(r,h), DROPPED.l(r,h,t) * hours(h) * cost_dropped_load }
*Account for difference in fixed O&M between model (CAP.l(i,v,r,t)) and outputs (cap_ivrt(i,v,r,t) * ilr(i))
                             + pvf_onm(t) * sum{(i,v,r)$[valcap(i,v,r,t)], cost_fom(i,v,r,t) * (CAP.l(i,v,r,t) - cap_ivrt(i,v,r,t) * ilr(i)) }
*Account for difference in capital costs of objective, which use cost_cap_fin_mult, and outputs, which use cost_cap_fin_mult_out
                             + pvf_capital(t) * (
                                   sum{(i,v,r)$[valinv(i,v,r,t)], cost_cap(i,t) * INV.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }
                                 + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades], cost_upgrade(i,v,r,t) * UPGRADES.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }
                                 + sum{(i,v,r,rscbin)$allow_cap_up(i,v,r,rscbin,t), cost_cap_up(i,v,r,rscbin,t) * INV_CAP_UP.l(i,v,r,rscbin,t) * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }
                                 + sum{(i,v,r,rscbin)$allow_ener_up(i,v,r,rscbin,t), cost_ener_up(i,v,r,rscbin,t) * INV_ENER_UP.l(i,v,r,rscbin,t) * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }
                                 + sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)], cost_cap(i,t) * INV_REFURB.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) - cost_cap_fin_mult_out(i,r,t)) }
                             )
                            }
)/z.l;

*Round error_check for z because of small number differences that always show up due to machine rounding and tolerances
error_check('z') = round(error_check('z'), 5) ;

* Check to see is any generation or capacity from dissallowed resources
error_check("gen") = sum{(i,v,r,h,t)$[not valgen(i,v,r,t)], GEN.l(i,v,r,h,t) } ;
error_check("cap") = sum{(i,v,r,t)$[not valcap(i,v,r,t)], CAP.l(i,v,r,t) } ;
error_check("RPS") = sum{(RPSCat,i,st,ast,t)$[(not RecMap(i,RPSCat,st,ast,t))$[(not stfeas(ast)) or not sameas(ast,"voluntary")]], RECS.l(RPSCat,i,st,ast,t) } ;
error_check("OpRes") = sum{(ortype,i,v,r,h,t)$[not valgen(i,v,r,t)], OPRES.l(ortype,i,v,r,h,t) } ;
error_check("m_rsc_dat") = sum{(r,i,rscbin)$m_rsc_dat(r,i,rscbin,"cap"), m_rsc_dat_init(r,i,rscbin) - m_rsc_dat(r,i,rscbin,"cap") } ;

* Check to make sure there's no dropped load in or after Sw_StartMarkets
error_check("dropped") = sum{(r,h,t)$[yeart(t)>=Sw_StartMarkets], DROPPED.l(r,h,t) } ;


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

tran_flow_out_ann(r,rr,trtype,t)$[(ord(r) < ord(rr))$tmodel_new(t)$routes(rr,r,trtype,t)] =
  sum{h, hours(h) * (FLOW.l(r,rr,h,t,trtype) + FLOW.l(rr,r,h,t,trtype)) } ;

tran_flow_out(r,rr,h,trtype,t)$[(ord(r) < ord(rr))$tmodel_new(t)$routes(rr,r,trtype,t)] =
  hours(h) * (FLOW.l(r,rr,h,t,trtype) + FLOW.l(rr,r,h,t,trtype)) ;

tran_flow_all(r,rr,h,trtype,t)$[tmodel_new(t)$routes(r,rr,trtype,t)] = FLOW.l(r,rr,h,t,trtype) ;

tran_flow_pos_out(r,rr,h,trtype,t)$[(ord(r) < ord(rr))$tmodel_new(t)$routes(rr,r,trtype,t)] = FLOW.l(r,rr,h,t,trtype) ;
tran_flow_pos_out_ann(r,rr,trtype,t)$[(ord(r) < ord(rr))$tmodel_new(t)$routes(rr,r,trtype,t)] = sum{h, hours(h) * FLOW.l(r,rr,h,t,trtype) } ;

tran_flow_neg_out(r,rr,h,trtype,t)$[(ord(r) < ord(rr))$tmodel_new(t)$routes(rr,r,trtype,t)] = -1 * FLOW.l(rr,r,h,t,trtype) ;
tran_flow_neg_out_ann(r,rr,trtype,t)$[(ord(r) < ord(rr))$tmodel_new(t)$routes(rr,r,trtype,t)] = -1 * sum{h, hours(h) * FLOW.l(rr,r,h,t,trtype) } ;

tran_util_out(r,rr,trtype,t)$[tmodel_new(t)$tran_out(r,rr,trtype,t)] =
  tran_flow_out_ann(r,rr,trtype,t)
  / sum{h, hours(h) * tran_out(r,rr,trtype,t) * (1 + trans_cap_delta(h,t)) } ;

tran_util_nat_out(t,trtype)$[tmodel_new(t)$sum{(r,rr)$routes(r,rr,trtype,t), tran_out(r,rr,trtype,t) }] =
         sum{(r,rr)$routes(r,rr,trtype,t), tran_flow_out_ann(r,rr,trtype,t) }
         / sum{(r,rr,h)$routes(r,rr,trtype,t),
               hours(h) * tran_out(r,rr,trtype,t) * (1 + trans_cap_delta(h,t)) } ;

tran_util_nat2_out(t)$[tmodel_new(t)$sum{(r,rr,trtype)$routes(r,rr,trtype,t), tran_out(r,rr,trtype,t) }] =
         sum{(r,rr,trtype)$routes(r,rr,trtype,t), tran_flow_out_ann(r,rr,trtype,t) }
         / sum{(r,rr,h,trtype)$routes(r,rr,trtype,t),
               hours(h) * tran_out(r,rr,trtype,t) * (1 + trans_cap_delta(h,t)) } ;

tran_flow_power(r,rr,h,trtype,t)
  $[(ord(r) < ord(rr))$tmodel_new(t)$routes(r,rr,trtype,t)] =
  (FLOW.l(r,rr,h,t,trtype) - FLOW.l(rr,r,h,t,trtype))
;

tran_flow_power_ann(r,rr,trtype,t)
  $[sum{h, tran_flow_power(r,rr,h,trtype,t)}] =
  sum{h, hours(h) * tran_flow_power(r,rr,h,trtype,t) }
  / sum{h, hours(h) }
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
*res_marg prices are in $/kW-yr but captrade is in MW, so multiply by 1000
expenditure_flow('res_marg_ann',r,rr,t)$[tmodel_new(t)$sum{trtype, routes(r,rr,trtype,t) }] =
  sum{szn, reqt_price('res_marg','na',r,szn,t) * 1000 * sum{trtype, captrade(r,rr,trtype,szn,t) } } ;
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
reduced_cost(i,v,r,t,"nobin","CAP")$valinv(i,v,r,t) = CAP.m(i,v,r,t)/(1000*cost_scale*pvf_capital(t)) ;
reduced_cost(i,v,r,t,"nobin","INV")$valinv(i,v,r,t) = INV.m(i,v,r,t)/(1000*cost_scale*pvf_capital(t)) ;
reduced_cost(i,v,r,t,rscbin,"INV_RSC")$[rsc_i(i)$valinv(i,v,r,t)$m_rscfeas(r,i,rscbin)] = INV_RSC.m(i,v,r,rscbin,t)/(1000*cost_scale*pvf_capital(t)) ;

*=========================
* Flexible load
*=========================
flex_load_out(flex_type,r,h,t) = FLEX.l(flex_type,r,h,t) ;
peak_load_adj(r,szn,t) = PEAK_FLEX.l(r,szn,t) ;

dr_out(i,v,r,h,hh,t)$[dr1(i)$valgen(i,v,r,t)$allowed_shifts(i,h,hh)] = DR_SHIFT.l(i,v,r,h,hh,t) ;

dr_net(i,v,r,h,t)$[valgen(i,v,r,t)$dr(i)] =
  sum{hh$DR_SHIFT.l(i,v,r,h,hh,t), DR_SHIFT.l(i,v,r,hh,h,t) / hours(h)}
  - sum{hh$DR_SHIFT.l(i,v,r,h,hh,t), DR_SHIFT.l(i,v,r,h,hh,t) / hours(h) / storage_eff(i,t)}
  + DR_SHED.l(i,v,r,h,t) / hours(h) ;

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

*"--tonnes-- production capacity, note unit change from MW to tonnes"
* [MW] * [tonne/MWh] = [tonne/h]
prod_cap(i,v,r,t)$[consume(i)$valcap(i,v,r,t)$Sw_Prod] =
  CAP.l(i,v,r,t) * prod_conversion_rate(i,v,r,t) ;

*"--tonne/hour-- production activities by technology, BA, and timeslice"
prod_produce(i,r,h,t)$[valcap_irt(i,r,t)$Sw_Prod$consume(i)$tmodel_new(t)] =
  sum{(p,v)$[i_p(i,p)$valcap(i,v,r,t)], PRODUCE.l(p,i,v,r,h,t) } ;

*"--tonne/year-- annual production by technology and BA"
prod_produce_ann(i,r,t)$[consume(i)$tmodel_new(t)$Sw_Prod] =
  sum{h, hours(h) * prod_produce(i,r,h,t) } ;

*"--$2004/tonne-- national average marginal cost of producing H2"
* NB subsetting only on Sw_H2 here and not broader Sw_Prod
prod_h2_price(p,t)$[tmodel_new(t)$Sw_H2$sameas(p,"H2")] =
  (1 / cost_scale) * (1 / pvf_onm(t))
* price when using national demand
    * ( eq_h2_demand.m(p,t)$[Sw_H2=1] 
* price when using regional demand; varies by hour and region, so calculate annual price as the weighted average of demand
* divide by hours to get from $/[tonnes/hour] to $/tonne
        + ( sum{(h,r), eq_h2_demand_regional.m(r,h,t) / hours(h) * h2_usage_regional(r,h,t) } 
            / sum{(h,r), h2_usage_regional(r,h,t) }
          )$[(Sw_H2=2)$(sum{(h,r), h2_usage_regional(r,h,t) })]
      )        
;

*"--$2004/mmbtu-- marginal cost of fuels used for H2-CT combustion"
* NB2 - h2_ct_intensity is in tonne/mmbtu
*     - thus going from ($ / tonne) * (tonne / mmbtu) = $ / mmbtu
prod_h2ct_cost("H2",t)$[tmodel_new(t)$Sw_H2] =
  prod_h2_price("H2",t) * h2_ct_intensity ;

*"--$2004-- BA- and tech-specific investment and operation costs associated with production activities"
*prod_syscosts(sys_costs,i,r,t)
prod_syscosts(sys_costs,i,r,t)$[tmodel_new(t)$consume(i)$Sw_Prod] =
  systemcost_techba(sys_costs,i,r,t) ;

prod_SMR_emit(e,r,t)$tmodel_new(t) =
  sum{(p,i,v,h)$[valcap(i,v,r,t)$smr(i)$i_p(i,p)],
      prod_emit_rate(e,i,t) * hours(h) * PRODUCE.l(p,i,v,r,h,t) } ;

* calculate exogenous H2 supply and H2-CT consumption
h2_demand_by_sector("cross-sector",t) = sum{p, h2_exogenous_demand(p,t) } ;
h2_demand_by_sector("electricity",t) = sum{(i,v,r,h)$[valgen(i,v,r,t)$h2_ct(i)],
        GEN.l(i,v,r,h,t) * hours(h) * h2_ct_intensity * heat_rate(i,v,r,t) } ;

* Marginal cost of H2 production by timeslice [$/kg]
* eq_h2_demand_regional is in [tonnes/hour], just like eq_supply_demand_balance
* is in [MW] (or [MWh/hour]). So divide by hours(h) and kg/tonne:
* [($·hour)/tonne] / [hour] / [1000 kg/tonne] = [$/kg]
h2_price_h(r,h,t)$[tmodel_new(t)] =
    (1 / cost_scale) * (1 / pvf_onm(t))
    * eq_h2_demand_regional.m(r,h,t)
    / hours(h) / 1000
;

* Marginal cost of H2 production by season [$/kg]
h2_price_szn(r,szn,t)$[tmodel_new(t)] =
    sum{h$h_szn(h,szn), h2_price_h(r,h,t) * hours(h) }
    / sum{h$h_szn(h,szn), hours(h) }
;

*========================================
* LOAD TYPES
*========================================

load_cat("end_use",r,t)$tmodel_new(t) = sum{h, hours(h) * load_exog(r,h,t) * (1.0 - distloss) } ;
load_cat("dist_loss",r,t)$tmodel_new(t)  = sum{h, hours(h) * load_exog(r,h,t) * distloss } ;
load_cat("trans_loss",r,t)$tmodel_new(t) = sum{(rr,h,trtype)$routes(r,rr,trtype,t), (tranloss(r,rr,trtype) * FLOW.l(r,rr,h,t,trtype) * hours(h)) } ;
load_cat("stor_charge",r,t)$tmodel_new(t) = sum{(i,v), stor_inout(i,v,r,t,"in") } ;
load_cat("h2_prod",r,t)$tmodel_new(t) = sum{i$h2(i), prod_load_ann(i,r,t) } ;
load_cat("h2_network",r,t)$[tmodel_new(t)] = 
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
h2_storage_level(h2_stor,r,allszn,h,t)
    $[(Sw_H2=2)$tmodel_new(t)$h_actualszn(h,allszn)$h2_stor_r(h2_stor,r)]
    = H2_STOR_LEVEL.l(h2_stor,r,allszn,h,t) ;

h2_storage_level_szn(h2_stor,r,allszn,t)
    $[(Sw_H2=2)$tmodel_new(t)$h2_stor_r(h2_stor,r)]
    = H2_STOR_LEVEL_SZN.l(h2_stor,r,allszn,t) ;

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
* [MW] * [tonne/MMBtu] * [MMBtu/MWh] = [tonne/h]
    + sum{(i,v)$[valgen(i,v,r,t)$h2_ct(i)],
          GEN.l(i,v,r,h,t) * h2_ct_intensity * heat_rate(i,v,r,t) } ;

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
