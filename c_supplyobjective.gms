$ontext
No globals needed for this file
$offtext

scalar  cost_scale "scaling parameter for the objective function" /1/ ;

Equation
* objective function calculation
 eq_ObjFn                      "--$s-- Objective function calculation"
 eq_ObjFn_inv(t)               "--$s-- Calculation of investment component of the objective function"
 eq_Objfn_op(t)                "--$s-- Calculation of operations component of the objective function"
;

* note these are not restricited to positive domain
Variable    Z        "--$-- total cost of operations and investment, scale varies based on cost_scale"
            Z_op(t)  "--$-- total cost of operations",
            Z_inv(t)  "--$-- total cost of operations"
;

* objective function is the sum over modeled years of the investment
* and operations components
eq_ObjFn.. Z =e= cost_scale * sum{t$tmodel(t), Z_inv(t) + Z_op(t) } ;

*=======================================================
* -- Investment component of the objective function --
*=======================================================

eq_ObjFn_inv(t)$tmodel(t)..

         Z_inv(t)

         =e=

         pvf_capital(t) *

              (
* --- investment costs ---
                  + sum{(i,v,r)$valinv(i,v,r,t),
                       cost_cap_fin_mult(i,r,t) * cost_cap(i,t) * INV(i,v,r,t)
                      }

* --- growth penalties ---
                  + sum{(gbin,i,st)$[sum{r$[r_st(r,st)], valinv_irt(i,r,t) }$stfeas(st)],
                        cost_growth(i,st,t) * growth_penalty(gbin) * (yeart(t) - sum{tt$[tprev(t,tt)], yeart(tt) }) * GROWTH_BIN(gbin,i,st,t)
                       }$[(yeart(t)>=model_builds_start_yr)$Sw_GrowthRelCon$(yeart(t)<=Sw_GrowthConLastYear)]

* --- cost of upgrading---
                  + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
                         cost_upgrade(i,v,r,t) * cost_cap_fin_mult(i,r,t) * UPGRADES(i,v,r,t) }

* --- costs of resource supply curve spur line investment if not modeling explicitly---
*Note that cost_cap for hydro, pumped-hydro, and geo techs are zero
*but hydro and geo rsc_fin_mult is equal to the same value as cost_cap_fin_mult
                  + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$(not spur_techs(i))],
                      m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) * sum{ii$rsc_agg(i,ii), INV_RSC(ii,v,r,rscbin,t) } }

* ---cost of demand response---
                  + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$dr(i)],
                      rsc_dr(i,r,"cost",rscbin,t) * rsc_fin_mult(i,r,t) * INV_RSC(i,v,r,rscbin,t) }

* ---cost of spur lines modeled explicitly---
* NOTE: no rsc_fin_mult(i,r,t) here, but it's 1 for upv and wind-ons anyway
                  + sum{x$[Sw_SpurScen$xfeas(x)],
                        spurline_cost(x) * Sw_SpurCostMult * INV_SPUR(x,t) }

* --- cost of intra-zone network reinforcement (a.k.a. point-of-interconnection capacity or POI)
* Sw_TransIntraCost is in $/kW, so multiply by 1000 to convert to $/MW
                  + sum{r$[rb(r)$Sw_TransIntraCost],
                        trans_cost_cap_fin_mult(t) * Sw_TransIntraCost * 1000 * INV_POI(r,t) }

* --- cost of water access---
                  + [ (8760/1E6) * sum{ (i,v,w,r)$[i_w(i,w)$valinv(i,v,r,t)], sum{wst$i_wst(i,wst),
                                     m_watsc_dat(wst,"cost",r,t) } * water_rate(i,w,r) *
                                        ( INV(i,v,r,t) + INV_REFURB(i,v,r,t)$[refurbtech(i)$Sw_Refurb] ) }
                      + sum{(rscbin,i,v,r)$[m_rscfeas(r,i,rscbin)$psh(i)],
                              sum{wst$i_wst(i,wst), m_watsc_dat(wst,"cost",r,t) } *
                              ( INV_RSC(i,v,r,rscbin,t) * water_req_psh(r,rscbin) ) }$Sw_PSHwatercon
                    ]$Sw_WaterMain

*slack variable to update water source type (wst) in the unit database
*Note that existing wst data is not consistent with availability of water source in the region
                  + sum{(wst,r)$rb(r), 1E6 * WATER_CAPACITY_LIMIT_SLACK(wst,r,t) }$[Sw_WaterMain$Sw_WaterCapacity]

* --- cost of refurbishments of RSC tech---
                  + sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                      cost_cap_fin_mult(i,r,t) * cost_cap(i,t) * INV_REFURB(i,v,r,t)
                      }

* --- cost of transmission---
*costs of transmission lines
                  + sum{(r,rr,trtype)$routes_inv(r,rr,trtype,t),
                        trans_cost_cap_fin_mult(t) * transmission_line_capcost(r,rr,trtype) * INVTRAN(r,rr,trtype,t) }

*cost of LCC AC/DC converter stations (each LCC DC line implicitly has two, one on each end of the line)
                  + sum{(r,rr)$routes_inv(r,rr,"LCC",t),
                        trans_cost_cap_fin_mult(t) * cost_acdc_lcc * 2 * INVTRAN(r,rr,"LCC",t) }

*cost of VSC AC/DC converter stations
                  + sum{r$rb(r),
                        trans_cost_cap_fin_mult(t) * cost_acdc_vsc * INV_CONVERTER(r,t) }

* --- storage capacity credit---
*small cost penalty to incentivize solver to fill shorter-duration bins first
                  + sum{(i,v,r,szn,sdbin)$[valcap(i,v,r,t)$(storage(i) or hyd_add_pump(i))$(not csp(i))],
                         bin_penalty(sdbin) * CAP_SDBIN(i,v,r,szn,sdbin,t) }

* cost of capacity upsizing
                  + sum{(i,v,r,rscbin)$allow_cap_up(i,v,r,rscbin,t),
                            cost_cap_fin_mult(i,r,t) * INV_CAP_UP(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }

* cost of energy upsizing
                  + sum{(i,v,r,rscbin)$allow_ener_up(i,v,r,rscbin,t),
                            cost_cap_fin_mult(i,r,t) * INV_ENER_UP(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) }

* H2 transport network investment costs
                  + sum{(r,rr)$h2_routes_inv(r,rr), cost_h2_transport_cap(r,rr,t) * H2_TRANSPORT_INV(r,rr,t) }$(Sw_H2 = 2)

* H2 storage investment costs 
                  + sum{(h2_stor,r)$h2_stor_r(h2_stor,r), cost_h2_storage_cap(h2_stor,t) * H2_STOR_INV(h2_stor,r,t) }$(Sw_H2 = 2)

* CO2 pipeline investment costs
                  + sum{(r,rr)$co2_routes(r,rr), cost_co2_pipeline_cap(r,rr,t) * CO2_TRANSPORT_INV(r,rr,t)
                                                  }$[Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]

                  + sum{(r,cs)$[csfeas(cs)$r_cs(r,cs)], cost_co2_spurline_cap(r,cs,t) * CO2_SPURLINE_INV(r,cs,t)
                                                  }$[Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]

*end to multiplier by pvf_capital
            )
;

*=======================================================
* -- Operational component of the objective function --
*=======================================================

eq_Objfn_op(t)$tmodel(t)..

         Z_op(t)

         =e=

         pvf_onm(t) * (

* --- variable O&M costs---
* all technologies except hybrid PV+battery and DAC
              sum{(i,v,r,h)$[valgen(i,v,r,t)$cost_vom(i,v,r,t)$(not pvb(i))],
                   hours(h) * cost_vom(i,v,r,t) * GEN(i,v,r,h,t) }

* hybrid PV+battery (PV)
            + sum{(i,v,r,h)$[valgen(i,v,r,t)$cost_vom_pvb_p(i,v,r,t)$pvb(i)],
                   hours(h) * cost_vom_pvb_p(i,v,r,t) * GEN_PVB_P(i,v,r,h,t) }$Sw_PVB

* hybrid PV+battery (Battery)
            + sum{(i,v,r,h)$[valgen(i,v,r,t)$cost_vom_pvb_b(i,v,r,t)$pvb(i)],
                   hours(h) * cost_vom_pvb_b(i,v,r,t) * GEN_PVB_B(i,v,r,h,t) }$Sw_PVB

* --- fixed O&M costs---
* generation
              + sum{(i,v,r)$[valcap(i,v,r,t)],
                   cost_fom(i,v,r,t) * CAP(i,v,r,t) }

* transmission lines
              + sum{(r,rr,trtype)$routes(r,rr,trtype,t),
                    transmission_line_fom(r,rr,trtype) * CAPTRAN_ENERGY(r,rr,trtype,t) }

* LCC AC/DC converter stations
              + sum{(r,rr,trtype)$[lcclike(trtype)$routes(r,rr,trtype,t)],
                    cost_acdc_lcc * 2 * trans_fom_frac * CAPTRAN_ENERGY(r,rr,trtype,t) }

* VSC AC/DC converter stations
              + sum{r$rb(r),
                    cost_acdc_vsc * trans_fom_frac * CAP_CONVERTER(r,t) }

* spur lines modeled as part of supply curve
              + sum{(i,v,r,rscbin)
                    $[m_rscfeas(r,i,rscbin)$valcap(i,v,r,t)
                    $rsc_i(i)$(not spur_techs(i))$(not sccapcosttech(i))],
                    m_rsc_dat(r,i,rscbin,"cost_trans") * trans_fom_frac * CAP_RSC(i,v,r,rscbin,t) }

* spur lines modeled explicitly
              + sum{x$[Sw_SpurScen$xfeas(x)],
                    spurline_cost(x) * trans_fom_frac * CAP_SPUR(x,t) }

* intra-zone network reinforcement (only for new capacity; don't include it for existing POI
* capacity because it's not a great estimate of the actual FOM cost of all existing transmission)
              + sum{r$[rb(r)$Sw_TransIntraCost],
                    Sw_TransIntraCost * 1000 * trans_fom_frac
                    * sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))], INV_POI(r,tt) } }

* --- penalty for retiring a technology (represents friction in retirements)---
              - sum{(i,v,r)$[valcap(i,v,r,t)$retiretech(i,v,r,t)],
                   cost_fom(i,v,r,t) * retire_penalty(t) *
                   (CAP(i,v,r,t)
                    - INV(i,v,r,t)$valinv(i,v,r,t)
                    - INV_REFURB(i,v,r,t)$[valinv(i,v,r,t)$refurbtech(i)$Sw_Refurb] )
                   }

* ---operating reserve costs---
              + sum{(i,v,r,h,ortype)$[Sw_OpRes$valgen(i,v,r,t)$cost_opres(i,ortype,t)$opres_model(ortype)$opres_h(h)],
                   hours(h) * cost_opres(i,ortype,t) * OpRes(ortype,i,v,r,h,t) }

* --- cost of coal, nuclear, and other fuels (except coal used for cofiring)---
* includes H2 fuel costs when using exogenous fuel price (Sw_H2 = 0 and Sw_H2CT = 1)
              + sum{(i,v,r,h)$[valgen(i,v,r,t)$(not gas(i))$heat_rate(i,v,r,t)
                              $(not bio(i))$(not cofire(i))],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN(i,v,r,h,t) }

* --cofire coal consumption---
* cofire bio consumption already accounted for in accounting of BIOUSED
              + sum{(i,v,r,h)$[valgen(i,v,r,t)$cofire(i)$heat_rate(i,v,r,t)],
                   (1-bio_cofire_perc) * hours(h) * heat_rate(i,v,r,t)
                   * fuel_price("coal-new",r,t) * GEN(i,v,r,h,t) }

* --- cost of natural gas---
*Sw_GasCurve = 2 (static natural gas prices)
*first - gas consumed for electricity generation
              + sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)$(Sw_GasCurve = 2)],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN(i,v,r,h,t) }

*second - gas consumed by gas-powered DAC
              + sum{(v,r,h)$[valcap("dac_gas",v,r,t)$(Sw_GasCurve = 2)],
                   hours(h) * dac_gas_cons_rate("dac_gas",v,t) * PRODUCE("DAC","dac_gas",v,r,h,t) }$Sw_DAC_Gas

*Sw_GasCurve = 0 (census division supply curves natural gas prices)
              + sum{(cendiv,gb), sum{h,hours(h) * GASUSED(cendiv,gb,h,t) }
                   * gasprice(cendiv,gb,t)
                   }$(Sw_GasCurve = 0)

*Sw_GasCurve = 3 (national supply curve for natural gas prices with census division multipliers)
              + sum{(h,cendiv,gb), hours(h) * GASUSED(cendiv,gb,h,t)
                   * gasadder_cd(cendiv,t,h) + gasprice_nat_bin(gb,t)
                   }$(Sw_GasCurve = 3)

*Sw_GasCurve = 1 (national and census division supply curves for natural gas prices)
*first - anticipated costs of gas consumption given last year's amount
              + (sum{(i,r,v,cendiv,h)$[valgen(i,v,r,t)$gas(i)],
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(r,cendiv) *
                   hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }

*second - adjustments based on changes from last year's consumption at the regional and national level
              + sum{(fuelbin,cendiv),
                   gasbinp_regional(fuelbin,cendiv,t) * VGASBINQ_REGIONAL(fuelbin,cendiv,t) }

              + sum{(fuelbin),
                   gasbinp_national(fuelbin,t) * VGASBINQ_NATIONAL(fuelbin,t) }

              )$[Sw_GasCurve = 1]

* ---cost of biofuel consumption and biomass transport---
              + sum{(r,bioclass)$[sum{(i,v)$(bio(i) or cofire(i)), valgen(i,v,r,t) }],
                   BIOUSED(bioclass,r,t) *
                   (sum{usda_region$r_usda(r,usda_region), biosupply(usda_region, bioclass, "price") } + bio_transport_cost) }

* --- hurdle costs for transmission flow ---
              + sum{(r,rr,h,trtype)$[routes(r,rr,trtype,t)$cost_hurdle(r,rr)],
                   cost_hurdle(r,rr) * FLOW(r,rr,h,t,trtype) * hours(h) }

* --- taxes on emissions---
              + sum{(e,r)$rb(r), EMIT(e,r,t) * emit_tax(e,r,t) }

* --cost of CO2 transport and storage from CCS--
              + sum{(i,v,r,h)$[valgen(i,v,r,t)],
                              hours(h) * capture_rate("CO2",i,v,r,t) * GEN(i,v,r,h,t) * CO2_storage_cost }$[not Sw_CO2_Detail]

* --cost of CO2 transport and storage from SMR CCS--
              + sum{(p,v,r,h)$[i_p("smr_ccs",p)$valcap("smr_ccs",v,r,t)],
                              hours(h) * smr_capture_rate * smr_co2_intensity * PRODUCE(p,"smr_ccs",v,r,h,t) * CO2_storage_cost }$[Sw_H2$(not Sw_CO2_Detail)]

* --cost of CO2 transport and storage from DAC--
              + sum{(p,i,v,r,h)$[dac(i)$valcap(i,v,r,t)],
                              hours(h) * PRODUCE(p,i,v,r,h,t) * CO2_storage_cost }$[Sw_DAC$(not Sw_CO2_Detail)]

* ---State RPS alternative compliance payments---
              + sum{(RPSCat,st)$(stfeas(st) or sameas(st,"voluntary")), acp_price(st,t) * ACP_PURCHASES(RPSCat,st,t)
                   }$[(yeart(t)>=RPS_StartYear)$Sw_StateRPS]

* --- revenues from purchases of curtailed VRE---
              - sum{(r,h)$rb(r), CURT(r,h,t) * hours(h) * cost_curt(t) }$Sw_CurtMarket

* --- dropped load (ONLY if before Sw_StartMarkets)
              + sum{(r,h)$[rb(r)$(yeart(t)<Sw_StartMarkets)], DROPPED(r,h,t) * hours(h) * cost_dropped_load }

* --- costs from producing products (for now DAC and/or H2)---
              + sum{(p,i,v,r,h)$[(h2(i) or dac(i))$valcap(i,v,r,t)$i_p(i,p)],
                    hours(h) * cost_prod(i,v,r,t) * PRODUCE(p,i,v,r,h,t) }$Sw_Prod

* --- H2 transport network fixed OM costs (compute cumulative sum of investments to get total capacity)
               + sum{(r,rr)$h2_routes_inv(r,rr), cost_h2_transport_fom(r,rr,t) 
                              * sum{tt$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))],
                                   H2_TRANSPORT_INV(r,rr,t) } }$(Sw_H2 = 2)

* --- H2 storage fixed OM costs (compute cumulative sum of investments to get total capacity)
               + sum{(h2_stor,r)$h2_stor_r(h2_stor,r),
                     cost_h2_storage_fom(h2_stor,t) * H2_STOR_CAP(h2_stor,r,t) }$(Sw_H2=2)

* --- CO2 pipeline fixed OM costs
              + sum{(r,rr)$co2_routes(r,rr), cost_co2_pipeline_fom(r,rr,t)
                              * sum{tt$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))],
                                   CO2_TRANSPORT_INV(r,rr,tt) } }$[Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]

* --- CO2 spurline fixed OM costs
              + sum{(r,cs)$[csfeas(cs)$r_cs(r,cs)], cost_co2_spurline_fom(r,cs,t)
                              * sum{tt$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))],
                                   CO2_SPURLINE_INV(r,cs,tt) } }$[Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]

* --- CO2 injection break even costs
              + sum{(r,cs,h)$r_cs(r,cs), hours(h) * CO2_STORED(r,cs,h,t) * cost_co2_stor_bec(cs,t) }$[Sw_CO2_Detail$(yeart(t)>=co2_detail_startyr)]

* --- Tax credit for CO2 stored ---
* note conversion to 12-year CRF given length of CO2 captured incentive payments
              - sum{(i,v,r,h)$[valgen(i,v,r,t)$co2_captured_incentive(i,v,r,t)],
                              (crf(t) / crf_co2_incentive(t)) * co2_captured_incentive(i,v,r,t) * hours(h) * capture_rate("CO2",i,v,r,t) * GEN(i,v,r,h,t)}

* --- Tax credit for CO2 stored for DAC ---
              - sum{(p,i,v,r,h)$[dac(i)$valcap(i,v,r,t)$i_p(i,p)],
                              (crf(t) / crf_co2_incentive(t)) * co2_captured_incentive(i,v,r,t) * hours(h) * PRODUCE(p,i,v,r,h,t)}

* --- PTC value ---
              - sum{(i,v,r,h)$[valgen(i,v,r,t)$ptc_value_scaled(i,v,t)],
                              hours(h) * ptc_value_scaled(i,v,t) * tc_phaseout_mult(i,v,t) * GEN(i,v,r,h,t) }

*end multiplier for pvf_onm
         )
;
