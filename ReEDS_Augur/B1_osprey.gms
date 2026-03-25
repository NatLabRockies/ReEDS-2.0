$title 'Optimize Transmission Flows and Storage Dispatch'

*Setting the default directory separator
$setglobal ds \

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$eolcom \\

* --- supress .lst file printing ---
* equations listed per block
option limrow = 0 ;
* variables listed per block
option limcol = 0 ;
* solver's solution output printed
option solprint = off ;
* solver's system output printed
option sysout = off ;
*** Print to log file when running in parallel
* option AsyncSolLst = 1

option profile = 3
option profiletol = 0

*========================
* ---- Model Options ----
*========================

scalar
Sw_Solve        "switch to choose solve method: 1 is loop, 2 is GUSS, 3 is grid" / 3 /
;

*========================
* -- Set Declarations --
*========================

set i, v, r, rfeas, szn, routes, storage_standalone, hydro_d, hydro_nd, geo, nuclear, trtype, notvsc, Sw_VSC ;

*Load sets from ReEDS
$gdxin ReEDS_Augur%ds%augur_data%ds%reeds_data_%prev_year%.gdx
$loadr geo
$loadr hydro_d
$loadr hydro_nd
$loadr i
$loadr notvsc
$loadr nuclear
$loadr r
$loadr rfeas
$loadr storage_standalone
$loadr szn
$loadr trtype
$loadr v
$loadr Sw_VSC
$gdxin

Set hr "hours in a modeled period" / hr001*hr%hoursperperiod% / ;

alias (hr,hh) ;

set nexth(hr,hh) "next hour"
    priorh(hr,hh) "previous hour" ;

nexth(hr,hh)$(ord(hr) = ord(hh)-1) = yes ;
nexth(hr,hh)$[(ord(hr) = card(hr))$(ord(hh) = 1)] = yes ;

priorh(hr,hh)$(ord(hr) = ord(hh)+1) = yes ;
priorh(hr,hh)$[(ord(hh) = card(hh))$(ord(hr) = 1)] = yes ;

$onOrder
set d "day"
/
$offlisting
$include inputs_case%ds%d_osprey.csv
$onlisting
/ ;
$offOrder


set d_szn(d,szn) "mapping of days to seasons" /
$offlisting
$ondelim
$include inputs_case%ds%d_szn.csv
$offdelim
$onlisting
/ ;

alias (r, rr) ;
alias (trtype, intype, outtype) ;


*==============================
* -- Parameter Declarations --
*==============================


Parameter
    avail_day(d,i,v)           "--fraction-- Fraction of nameplate capacity available"
    avail(i,v)                 "--fraction-- Fraction of nameplate capacity available for modeled day"
    cap_converter(r)           "--MW-- VSC AC/DC converter capacity"
    cap_prod(r)                "--MW-- capacity for production activities"
    cap_trans(r,rr,trtype)     "--MW-- transmission line capacities",
    cap(i,v,r)                 "--MW-- Nameplate non-VRE generation capacity"
    converter_efficiency_vsc   "--fraction-- VSC AC/DC converter efficiency"
    cost_dropped_load          "--$/MWh-- Cost for dropped load"
    cost_flow                  "--$/MW-- Cost for using transmission lines"
    duration(i)                "--h-- storage duration in hours"
    energy_budget_feas(i,v,r)  "--MW-- Filter instances where energy budget applies"
    energy_budget(i,v,r)       "--MWh-- Energy budget for dispatchable hydro and hybrid resources for a given day"
    gen_cost(i,v,r)            "--$/MWh-- total variable generation costs (fuel + VOM)",
    net_load(hr,r)             "--MW-- Net load for a given day"
    prod_load_day(d,r)         "--MWh-- demand for production activities (H2, DAC) by day"
    prod_load(r)               "--MWh-- demand for production (used in model)"
    storage_eff(i)             "--fraction-- round-trip efficiency of storage technologies",
    tranloss(r,rr,trtype)      "--fraction-- transmission losses between r and rr"
;


* Load values from ReEDS
$gdxin ReEDS_Augur%ds%augur_data%ds%osprey_inputs_%prev_year%.gdx
$loadr avail_day
$loadr cap
$loadr cap_converter
$loadr cap_trans = trancap
$loadr converter_efficiency_vsc
$loadr duration
$loadr gen_cost
$loadr cap_prod
$loadr prod_load_day = prod_load
$loadr routes
$loadr storage_eff
$loadr tranloss
$gdxin
* Pare down a few
tranloss(r,rr,trtype)$(not routes(r,rr,trtype)) = 0 ;

$onempty
Parameter energy_budget_day(d,i,v,r) "--MWh-- Energy budget for dispatchable hydro and hybrid resources"
/
$offlisting
$ondelim
$include ReEDS_Augur%ds%augur_data%ds%daily_energy_budget_%prev_year%.csv
$offdelim
$onlisting
/ ;
$offempty

Table net_load_day(d,hr,r) "--MW-- Net load for 24-hour horizon"
$offlisting
$ondelim
$include ReEDS_Augur%ds%augur_data%ds%net_load_%prev_year%.csv
$offdelim
$onlisting
;

* Initialize parameters
set firstd(d) "first modeled period" ;
firstd(d) = yes$(ord(d) = 1) ;
avail(i,v) = sum{d$firstd(d), avail_day(d,i,v) } ;
net_load(hr,r) = sum{d$firstd(d), net_load_day(d,hr,r) } ;
energy_budget(i,v,r) = sum{d$firstd(d), energy_budget_day(d,i,v,r) } ;
energy_budget_feas(i,v,r) = sum{d$firstd(d), energy_budget_day(d,i,v,r) } ;
prod_load(r) = sum{d$firstd(d), prod_load_day(d,r) } ;

*The small value of cost_flow is used to reduce degeneracy in where curtailment occurs
cost_flow = 0.001 ;
* Add small cost for discharging storage in order to prevent degeneracy between storage losses and curtailment
* Use the same as used for cost_flow
gen_cost(i,v,r)$[cap(i,v,r)$storage_standalone(i)$(gen_cost(i,v,r) = 0)] = cost_flow ;

*Use the maximum cost and increase it by a fixed amount so that it is always higher than the highest generator cost
cost_dropped_load = smax((i,v,r)$cap(i,v,r), gen_cost(i,v,r) ) + 10000 ;

*=============================
* -- Variable Declarations --
*=============================

positive variables

GEN(hr,i,v,r)              "--MW-- Electricity generation in hour h"
PRODUCE(hr,r)              "--MW-- electricity generation for meeting production activities demand"
STORAGE_IN(hr,i,v,r)       "--MW-- Energy going into storage in hour h"
STORAGE_LEVEL(hr,i,v,r)    "--MWh-- storage level in hour h"
FLOW(hr,r,rr,trtype)       "--MW-- Electricity flow on transmission lines in hour h"
CONVERSION(hr,r,intype,outtype) "--MW-- conversion of AC->DC_VSC or DC_VSC->AC"
DROPPED_LOAD(hr,r)         "--MW-- Dropped load"
;

* initialize the upper bound
PRODUCE.up(hr,r)$cap_prod(r) = cap_prod(r) ;

Variable Z "--$-- Objective function value" ;

*=============================
* -- Equation Declarations --
*=============================

Equation

* objective function calculation
 eq_ObjFn                          "--$-- Objective function calculation"

* other equations
 eq_daily_load_balance(r)          "--MWh-- daily production balance for H2 and DAC"
 eq_energy_budget_balance(i,v,r)   "--MWh-- daily energy balance for hydropower resources"
 eq_flow_cap(hr,r,rr,trtype)       "--MW-- Transmission flows must not exceed max capacity"
 eq_gen_cap(hr,i,v,r)              "--MW-- Generation must not exceed max capacity"
 eq_load_balance(hr,r)             "--MW-- Load must be served"
 eq_storage_duration(hr,i,v,r)     "--MWh-- limit STORAGE_LEVEL based on hours of storage available"
 eq_storage_level(hr,i,v,r)        "--MWh-- Storage level inventory balance from one time-slice to the next"
 eq_vsc_flow(hr,r)                 "--MW-- VSC DC power flow"
 eq_conversion_limit(hr,r)         "--MW-- AC/DC energy conversion is limited to converter capacity"
;

* --- Capacity limits ---
eq_gen_cap(hr,i,v,r)$cap(i,v,r)..

    GEN(hr,i,v,r) + STORAGE_IN(hr,i,v,r)$[storage_standalone(i)]

    =l=

    cap(i,v,r) * avail(i,v)
;


eq_flow_cap(hr,r,rr,trtype)$routes(r,rr,trtype)..

    FLOW(hr,r,rr,trtype)

    =l=

    cap_trans(r,rr,trtype)
;


* --- Load balance ---
eq_load_balance(hr,r)$rfeas(r)..

    + sum{(i,v)$cap(i,v,r), GEN(hr,i,v,r) }

    + sum{(rr,trtype)$[routes(rr,r,trtype)$notvsc(trtype)],
          (1-tranloss(rr,r,trtype)) * FLOW(hr,rr,r,trtype) }
    - sum{(rr,trtype)$[routes(r,rr,trtype)$notvsc(trtype)],
          FLOW(hr,r,rr,trtype) }

    + (CONVERSION(hr,r,"VSC","AC") * converter_efficiency_vsc)$[cap_converter(r)$Sw_VSC]
    - (CONVERSION(hr,r,"AC","VSC") / converter_efficiency_vsc)$[cap_converter(r)$Sw_VSC]

    - sum{(i,v)$[storage_standalone(i)$cap(i,v,r)], STORAGE_IN(hr,i,v,r) }

    + DROPPED_LOAD(hr,r)

    =g=

    net_load(hr,r) + PRODUCE(hr,r)$cap_prod(r)
;


* --- VSC HVDC macrogrid ---
eq_vsc_flow(hr,r)$[rfeas(r)$Sw_VSC]..

* [plus] net VSC DC transmission with imports reduced by losses
    + sum{rr$routes(rr,r,"VSC"), (1-tranloss(rr,r,"VSC")) * FLOW(hr,rr,r,"VSC") }
    - sum{rr$routes(r,rr,"VSC"), FLOW(hr,r,rr,"VSC") }

* [plus] net VSC AC/DC conversion
    + (CONVERSION(hr,r,"AC","VSC") * converter_efficiency_vsc)$cap_converter(r)
    - (CONVERSION(hr,r,"VSC","AC") / converter_efficiency_vsc)$cap_converter(r)

    =e=

* no direct consumption of VSC
    0
;


eq_conversion_limit(hr,r)$[rfeas(r)$cap_converter(r)$Sw_VSC]..

    CONVERSION(hr,r,"AC","VSC") + CONVERSION(hr,r,"VSC","AC")

    =l=

    cap_converter(r)
;


* --- Hydrogen ---
eq_daily_load_balance(r)$[rfeas(r)$cap_prod(r)]..

    sum{hr, PRODUCE(hr,r)   }

    =e=

    prod_load(r)
;


* --- Dispatchable hydro and hybrids ---
eq_energy_budget_balance(i,v,r)$[energy_budget_feas(i,v,r)]..

   sum{hr, GEN(hr,i,v,r) }

   =l=

   energy_budget(i,v,r)
;


* --- Storage ---
eq_storage_level(hr,i,v,r)$[storage_standalone(i)$cap(i,v,r)]..

    sum{hh$[nexth(hr,hh)], STORAGE_LEVEL(hh,i,v,r) }

    =e=

    + STORAGE_LEVEL(hr,i,v,r)

    + storage_eff(i) * STORAGE_IN(hr,i,v,r)

    - GEN(hr,i,v,r)$[storage_standalone(i)$cap(i,v,r)]
;


eq_storage_duration(hr,i,v,r)$[storage_standalone(i)$cap(i,v,r)]..

    cap(i,v,r) * duration(i) * avail(i,v)

    =g=

    STORAGE_LEVEL(hr,i,v,r)
;


* --------------------------
* --- Objective function ---
* --------------------------
eq_ObjFn..

    Z

    =e=

    + sum{(hr,i,v,r)$[gen_cost(i,v,r)$cap(i,v,r)], gen_cost(i,v,r) * GEN(hr,i,v,r) }

    + sum{(hr,r)$rfeas(r), DROPPED_LOAD(hr,r) * cost_dropped_load }

    + sum{(hr,r,rr,trtype)$routes(r,rr,trtype), cost_flow * FLOW(hr,r,rr,trtype) }
;

* --------------------------
Model osprey /all/ ;

option lp=%solver%;

osprey.optfile = 1 ;
OPTION RESLIM = 500000 ;

*=============================
* ---- Output Parameters -----
*=============================

Parameter
    cf_output(i,r)                           "--fraction-- capacity factor of dispatchable generators"
    CONVERSION_output(d,hr,r,intype,outtype) "--MW-- conversion of AC->DC_VSC or DC_VSC->AC"
    dropped_load_output(d,hr,r)              "--MW-- Dropped load"
    flows_output(d,hr,r,rr,trtype)           "--MW-- transmission flows"
    gen_output(d,hr,i,v,r)                   "--MW-- generation"
    prices(d,hr,r)                           "--$/MWh-- energy prices"
    PRODUCE_output(d,hr,r)                   "--MW-- additional generation for the production of produce"
    storage_in_output(d,hr,i,v,r)            "--MW-- Energy going into storage"
    storage_level_output(d,hr,i,v,r)         "--MWh-- storage level"
;

*=============================
* ------- Loop Solution ------
*=============================
if(Sw_Solve = 1,
  Loop(d,
    net_load(hr,r) = net_load_day(d,hr,r) ;
    avail(i,v) = avail_day(d,i,v) ;
    energy_budget(i,v,r) = energy_budget_day(d,i,v,r) ;
    prod_load(r) = prod_load_day(d,r) ;
    Solve osprey using LP minimizing Z ;
    prices(d,hr,r) =  eq_load_balance.m(hr,r) ;
    flows_output(d,hr,r,rr,trtype)$routes(r,rr,trtype) = FLOW.l(hr,r,rr,trtype) ;
    gen_output(d,hr,i,v,r) = GEN.l(hr,i,v,r) ;
    storage_in_output(d,hr,i,v,r) = STORAGE_IN.l(hr,i,v,r) ;
    storage_level_output(d,hr,i,v,r) = STORAGE_LEVEL.l(hr,i,v,r) ;
    dropped_load_output(d,hr,r) = DROPPED_LOAD.l(hr,r) ;
    PRODUCE_output(d,hr,r) = PRODUCE.l(hr,r) ;
    CONVERSION_output(d,hr,r,intype,outtype) = CONVERSION.l(hr,r,intype,outtype) ;
  ) ;
) ;

*=============================
* ------- GUSS Solution ------
*=============================

set gd(d) "days per GUSS run" ;

set dict / gd.                  scenario.  ''
           net_load.            param.     net_load_day
           avail.               param.     avail_day
           energy_budget.       param.     energy_budget_day
           prod_load.           param.     prod_load_day
           eq_load_balance.     marginal.  prices
           FLOW.                level.     flows_output
           GEN.                 level.     gen_output
           STORAGE_IN.          level.     storage_in_output
           STORAGE_LEVEL.       level.     storage_level_output
           DROPPED_LOAD.        level.     dropped_load_output
           PRODUCE.             level.     PRODUCE_output
           CONVERSION.          level.     CONVERSION_output
         / ;

if(Sw_Solve = 2,
  gd(d) = yes ;
  Solve osprey using LP minimizing Z scenario dict ;
) ;

*=============================
* ------- Grid Solution ------
*=============================

set thread "grid jobs to run - only used if Sw_Solve=3" / 1*%threads% /
    thread_days(thread,d) "map days to threads"
/
$offlisting
$ondelim
$include inputs_case%ds%threads.csv
$offdelim
$onlisting
/ ;

parameter h(thread) "model handles" ;

if(Sw_Solve = 3,
  osprey.solveLink = %solveLink.AsyncThreads% ;
  loop(thread,
    gd(d) = thread_days(thread,d) ;
    Solve osprey using LP minimizing Z scenario dict ;
    h(thread) = osprey.handle ;
  ) ;
* Collect the solutions
  repeat
    loop(thread$handlecollect(h(thread)),
      display$handledelete(h(thread)) "trouble deleting handles" ;
      h(thread) = 0 ;
    ) ;
    display$sleep(card(h)*5/%threads%) "waiting for solver" ;
  until card(h) = 0 or timeelapsed > 7200 ;
) ;

*=============================
* ------- Write results ------
*=============================
cf_output(i,r)$sum{v, cap(i,v,r) } =
    sum{(d,hr,v), gen_output(d,hr,i,v,r) }
    / (sum{v, cap(i,v,r) } * 24 * sum{d, 1} ) ;

execute_unload "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx"
*     prices
*     flows_output
*     gen_output
*     storage_in_output
*     dr_inc_output
*     net_load_day
*     dropped_load_output
*     PRODUCE_output
*     storage_level_output
*     energy_budget_day
*     gen_cost
*     cap_feas
*     cost_dropped_load
*     energy_budget_feas
*     CONVERSION_output
*     cf_output
;
