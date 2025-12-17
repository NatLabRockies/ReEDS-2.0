* Includes these scripts, in order:
* - d1_temporal_params.gms
* - d1_financials.gms
* - * solves the model *
* - d2_post_solve_adjustments.gms
* - d2_varfix.gms
* - d3_data_dump.gms

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
$ifthene.post_startyear %cur_year%>%startyear%
* Here we calculate the RHS value of eq_rsc_INVlim because floating point
* differences can cause small number issues that either make the model
* infeasible or result in very tiny number (order 1e-16) in the matrix
rhs_eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)] = 

*capacity indicated by the resource supply curve (with undiscovered geo available
*at the "discovered" amount and hydro upgrade availability adjusted over time)
    m_rsc_dat(r,i,rscbin,"cap") * (
        1$[not geo_hydro(i)] + geo_discovery(i,r,t)$geo_hydro(i))
    + hyd_add_upg_cap(r,i,rscbin,t)$(Sw_HydroCapEnerUpgradeType=1)
* available EVMC capacity
    + rsc_evmc(i,r,"cap",rscbin,t)
*minus the cumulative invested capacity in that region/class/bin...
*Note that yeart(tt) is stricly < here, while it is <= in eq_rsc_INVlim. That is because
*values where yeart(tt)==yeart(t) are variables rather than parameters because they are not
*values from prior solve years.
    - sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) < yeart(t))$rsc_agg(i,ii)],
         INV_RSC.l(ii,v,r,rscbin,tt) * resourcescaler(ii) }
*minus exogenous (pre-start-year) capacity, using its level in the first year (tfirst)
    - sum{(ii,v,tt)$[tfirst(tt)$rsc_agg(i,ii)$exog_rsc(i)],
         capacity_exog_rsc(ii,v,r,rscbin,tt) }
;


flag_eq_rsc_INVlim(r,i,rscbin,t)$tmodel(t) = no ;

* Identify instances when the RHS values are within rhs_tolerance of zero
flag_eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)
                                 $(rhs_eq_rsc_INVlim(r,i,rscbin,t) > -rhs_tolerance)
                                 $(rhs_eq_rsc_INVlim(r,i,rscbin,t) < rhs_tolerance)] = yes ;

* When RHS is 0 (or close enough), the eq_rsc_INVlim equation says that all relevant INV_RSC are 0.
* Therefore we can set the INV_RSC variable to zero anywhere the flag_eq_rsc_INVlim is true
loop(i$rsc_i(i),
    INV_RSC.fx(ii,v,r,rscbin,t)$[tmodel(t)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)
                                $(flag_eq_rsc_INVlim(r,i,rscbin,t))$(valinv(ii,v,r,t)$rsc_agg(i,ii))] = 0 ;
) ;

* set m_capacity_exog to the maximum of either its original amount
* or the amount of upgraded capacity that has occurred in the past "Sw_UpgradeLifespan" years
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
                                 UPGRADES.l(ii,v,r,tt) }
    ) ;

) ;

* if the relative growth constraint is turned on, then calculate the growth
* limits for each growth bin
if(Sw_GrowthPenalties > 0,

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

$endif.post_startyear

* Load capacity credit results
$ifthene.tcheck %cur_year%>%GSw_SkipAugurYear%

*indicate we're loading data
tload("%cur_year%") = yes ;

*file written by ReEDS_Augur.py
* loaddcr = domain check (dc) + overwrite values storage previously (r)
$gdxin ReEDS_Augur%ds%augur_data%ds%ReEDS_Augur_%prev_year%.gdx
$loaddcr cc_old_load = cc_old
$loaddcr cc_mar_load = cc_mar
$loaddcr cc_evmc_load = cc_evmc
$loaddcr sdbin_size_load = sdbin_size
$gdxin

*Note: these values are rounded before they are written to the gdx file, so no need to round them here

* assign old and marginal capacity credit parameters to those
* corresponding to each balancing areas cc region
cc_old(i,r,ccseason,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] =
    sum{ccreg$r_ccreg(r,ccreg), cc_old_load(i,r,ccreg,ccseason,t) } ;

m_cc_mar(i,r,ccseason,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] =
    sum{ccreg$r_ccreg(r,ccreg), cc_mar_load(i,r,ccreg,ccseason,t) } ;

sdbin_size(ccreg,ccseason,sdbin,t)$tload(t) = sdbin_size_load(ccreg,ccseason,sdbin,t) ;

* --- Assign hybrid PV+battery capacity credit ---
* Limit the capacity credit of hybrid PV such that the total capacity credit from the
* PV and the battery do not exceed the inverter limit.
* Example: * PV = 130 MWdc, Battery = 65 MW, Inverter = 100 MW (PVdc/Battery=0.5; PVdc/INVac=1.3)
* Assuming the capacity credit of the Battery is 65 MW, then capacity credit of the PV
* is limited to 35 MW or 0.269 (35MW/130MW) on a relative basis.
* Max capacity credit PV [MWac/MWdc] = (Inverter - Battery capacity credit) / PV_dc
*                                    = (PV_dc / ILR - PV_dc * BCR) / PV_dc
*                                    = 1/ILR - BCR
* marginal capacity credit
m_cc_mar(i,r,ccseason,t)$[tload(t)$pvb(i)] = min{ m_cc_mar(i,r,ccseason,t), 1 / ilr(i) - bcr(i) } ;

* old capacity credit
* (1) convert cc_old from MW to a fractional basis
* (2) adjust the fractional value to be less than 1/ILR - BCR
* (3) multiply by CAP to convert back to MW
cc_old(i,r,ccseason,t)$[tload(t)$pvb(i)$sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)}] =
    min{ cc_old(i,r,ccseason,t) / sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)}, 1 / ilr(i) - bcr(i) }
    * sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)};

$endif.tcheck


*** Calculate financial multipliers
* These are calculated here because the ITC phaseout can influence these parameters,
* and the timing of the phaseout is not known beforehand.
$include d1_financials.gms


$ifthene %cur_year%==%startyear%
*initialize CAP.l for 2010 because it has not been defined yet
CAP.l(i,v,r,"%startyear%")$[m_capacity_exog(i,v,r,"%startyear%")] = m_capacity_exog(i,v,r,"%startyear%") ;
$endif

$ifthene %cur_year%==%startyear%
*initialize CAP_ENERGY.l for 2010 because it has not been defined yet
CAP_ENERGY.l(i,v,r,"%startyear%")$[m_capacity_exog_energy(i,v,r,"%startyear%")] = m_capacity_exog_energy(i,v,r,"%startyear%") ;
$endif

* Now that cost_cap_fin_mult is done, calculate cost_growth, which is
* the minimum cost of that technology within a state
if(Sw_GrowthPenalties > 0,
*rsc_fin_mult holds the multipliers for sccapcosttech, so don't include them here
    cost_growth(i,st,t)$[tmodel(t)$sum{r$[r_st(r,st)], valinv_irt(i,r,t) }$stfeas(st)$(not sccapcosttech(i))] = 
        smin{r$[valinv_irt(i,r,t)$r_st(r,st)$cost_cap_fin_mult(i,r,t)],
            cost_cap_fin_mult(i,r,t) * cost_cap(i,t) } ;

*rsc_fin_mult holds the capital costs for sccapcosttech
    cost_growth(i,st,t)$[tmodel(t)$sum{r$[r_st(r,st)], valinv_irt(i,r,t) }$stfeas(st)$sccapcosttech(i)] = 
        smin{(r,rscbin)$[valinv_irt(i,r,t)$r_st(r,st)$rsc_fin_mult(i,r,t)],
            rsc_fin_mult(i,r,t) * m_rsc_dat(r,i,rscbin,"cost") } ;

    cost_growth(i,st,t)$cost_growth(i,st,t) = round(cost_growth(i,st,t),3) ;
) ;

* Write the inputs for debugging and error checks:
* Always write data for the first solve year (currently always 2010).
* Overwrites the versions written by d_solveprep.gms and d1_temporal_params.gms.
$ifthene.write %cur_year%=%startyear%
execute_unload 'inputs_case%ds%inputs.gdx' ;
$endif.write

* If using debug mode, write the inputs for every solve year
$ifthene.debug %debug%>0
execute_unload 'alldata_%stress_year%.gdx' ;
$endif.debug


* --- diagnoses gdx dump settings ---
$ifthene.diagnose %diagnose%=1
$ifthene.diagnose_2 %diagnose_year%<=%cur_year%
$include inputs_case%ds%diagnose.gms
$endif.diagnose_2
$endif.diagnose


* ------------------------------
* Solve the Model
* ------------------------------
$ifthen.valstr %GSw_ValStr% == 1
OPTION lp = convert ;
ReEDSmodel.optfile = 1 ;
$echo dumpgdx ReEDSmodel_jacobian.gdx > convert.opt
solve ReEDSmodel minimizing z using lp ;
OPTION lp = %solver% ;
ReEDSmodel.optfile = %GSw_gopt% ;
OPTION savepoint = 1 ;
$endif.valstr

solve ReEDSmodel minimizing z using lp ;
tsolved(t)$tmodel(t) = yes ;

* record objective function values right after solve
z_rep(t)$tmodel(t) = Z.l ;
z_rep_inv(t)$tmodel(t) = Z_inv.l(t) ;
z_rep_op(t)$tmodel(t) = Z_op.l(t) ;


* ---------------------------------
* Modeling to Generate Alternatives
* ---------------------------------
$ifthene.mga %GSw_MGA_CostDelta%>0
$ifthene.mga1 %cur_year%>=%GSw_StartMarkets%
*## Activate MGA mode
Sw_MGA = 1 ;
solve ReEDSmodel %GSw_MGA_Direction%imizing MGA_OBJ using lp ;
*## Deactivate MGA mode
Sw_MGA = 0 ;
$endif.mga1
$endif.mga


*** Adjust some parameters based on the solution for this solve year
$include d2_post_solve_adjustments.gms

*** Fix decision variables to their optimized levels for this solve year
tfix("%cur_year%") = yes ;
$include d2_varfix.gms

*** Dump data used in calculations between solve years
$include d3_data_dump.gms

*** Abort if the solver returns an error
if (ReEDSmodel.modelStat > 1,
    abort "Model did not solve to optimality",
    ReEDSmodel.modelStat) ;
