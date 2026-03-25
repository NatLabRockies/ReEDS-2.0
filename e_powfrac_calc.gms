
* Author: Kelly Eurek
* Date: 2019/08/14
* Source Bialek (1996). Tracing the flow of electricity

* ======================
* Calculate Flow Factors
* ======================

* --- calculate inflows, outflows, and flows between BAs ---

parameter
  flow_in(rr,allh,t)      "--MW-- average flow of power into BA rr during time-slice h"
  flow_out(r,allh,t)      "--MW-- average flow of power out of BA r during time-slice h"
  flow_ba2ba(r,rr,allh,t) "--MW-- average flow of power out of BA r into BA rr during time-slice h"
;

flow_in(rr,h,t)$tmodel_new(t) = sum{(r,trtype)$routes(rr,r,trtype,t), FLOW.l(r,rr,h,t,trtype) } ;
flow_out(r,h,t)$tmodel_new(t) = sum{(rr,trtype)$routes(rr,r,trtype,t), FLOW.l(r,rr,h,t,trtype) } ;
flow_ba2ba(r,rr,h,t)$[tmodel_new(t)$sum{trtype,routes(rr,r,trtype,t) }] =
    sum{(trtype)$[routes(rr,r,trtype,t)], FLOW.l(r,rr,h,t,trtype) } ;

* --- calculate the "total load" ---

Parameter totload(r,allh,t) "--MW-- load modified to include charging of storage and transmission losses" ;

totload(r,h,t)$[tmodel_new(t)] =
    load_exog(r,h,t) + can_exports_h(r,h,t)
  + sum{(i,v)$[valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))], STORAGE_IN.l(i,v,r,h,t)}
  + sum{(rr,trtype)$routes(rr,r,trtype,t), tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype)}
;

* --- calcultate power flowing through a balancing area ---

Parameter flow_through(r,allh,t) "--MW-- flow through balancing area r during time-slice h: inflow + total generation" ;

flow_through(r,h,t)$tmodel_new(t) = totload(r,h,t) + flow_out(r,h,t)

* --- calculate total generation (including storage discharge) ---

Parameter totgen(r,allh,t) "--MW-- total generation in region r during time-slice h" ;

totgen(r,h,t)$tmodel_new(t) =
    load_exog(r,h,t) + can_exports_h(r,h,t)

  + sum{(i,v)$[valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))], STORAGE_IN.l(i,v,r,h,t) }

  + sum{(rr,trtype)$routes(rr,r,trtype,t),
      + FLOW.l(r,rr,h,t,trtype)
      - FLOW.l(rr,r,h,t,trtype)
  }

;

* --- define upstream and downstream power matricies ---

Parameter A_upstream(rr,r,allh,t) "upstream power distribution matrix" ;
* see equation (4) in Bialek (1996)
A_upstream(rr,r,h,t)$tmodel_new(t) = 0 ;
A_upstream(r,r,h,t)$[tmodel_new(t)$rb(r)] = 1 ;
A_upstream(rr,r,h,t)$[(flow_ba2ba(r,rr,h,t)>0)$(flow_through(r,h,t)>0)$tmodel_new(t)] = - flow_ba2ba(r,rr,h,t) / flow_through(r,h,t) ;

Parameter A_downstream(r,rr,allh,t) "downstream power distribution matrix" ;
* see equation (10) in Bialek (1996)
A_downstream(r,rr,h,t)$tmodel_new(t) = 0 ;
A_downstream(r,r,h,t)$[tmodel_new(t)$rb(r)] = 1 ;
A_downstream(r,rr,h,t)$[(flow_ba2ba(r,rr,h,t)>0)$(flow_through(rr,h,t)>0)$tmodel_new(t)] = -flow_ba2ba(r,rr,h,t) / flow_through(rr,h,t) ;

* --- calculate the inverse of the upstream and downstream power matricies ---

parameter
  Ainv_upstream(r,rr,allh,t) "inverse of A_upstream"
  Ainv_downstream(r,rr,allh,t) "inverse of A_downstream"
  a(r,rr) temp matrix for A
  ainv(r,rr) temp matrix for A-inverse
;

Ainv_upstream(r,rr,h,t)$sum{trtype,routes(rr,r,trtype,t) } = 0 ;
Ainv_downstream(r,rr,h,t)$sum{trtype,routes(rr,r,trtype,t) } = 0 ;
a(r,rr) = 0 ;
ainv(r,rr) = 0 ;

Loop((h,t)$[tmodel_new(t)$Sw_calc_powfrac],
a(rr,r) = A_upstream(rr,r,h,t) ;
execute_unload 'outputs%ds%gdxforinverse_%case%.gdx' r, a ;
execute 'invert outputs%ds%gdxforinverse_%case%.gdx r a outputs%ds%gdxfrominverse_%case%.gdx ainv >> outputs%ds%invert1_%case%.log' ;
execute_load 'outputs%ds%gdxfrominverse_%case%.gdx', ainv ;
Ainv_upstream(rr,r,h,t) = ainv(rr,r) ;
) ;

Loop((h,t)$[tmodel_new(t)$Sw_calc_powfrac],
a(r,rr) = A_downstream(r,rr,h,t) ;
execute_unload 'outputs%ds%gdxforinverse_%case%.gdx' r, a ;
execute 'invert outputs%ds%gdxforinverse_%case%.gdx r a outputs%ds%gdxfrominverse_%case%.gdx ainv >> outputs%ds%invert2_%case%.log' ;
execute_load 'outputs%ds%gdxfrominverse_%case%.gdx', ainv ;
Ainv_downstream(r,rr,h,t) = ainv(r,rr) ;
) ;

* --- remove gdx files that were created to do the inverse calculation ---
execute 'rm outputs%ds%gdxforinverse_%case%.gdx' ;
execute 'rm outputs%ds%gdxfrominverse_%case%.gdx' ;
execute 'rm outputs%ds%invert1_%case%.log' ;
execute 'rm outputs%ds%invert2_%case%.log' ;

* --- calculate upsteram and downstream power fractions ---

parameter
  powerfrac_upstream(rr,r,allh,t)     "--unitless-- power fraction upstream  : fraction of power at BA rr that was generated at BA r during time-slice h"
  powerfrac_downstream(r,rr,allh,t)   "--unitless-- power fraction downstream: fraction of power generated at BA r that serves load at BA rr during time-slice h"
;

powerfrac_upstream(r,rr,h,t)$sum{trtype,routes(rr,r,trtype,t) } = 0 ;
powerfrac_downstream(r,rr,h,t)$sum{trtype,routes(rr,r,trtype,t) } = 0 ;

* see equation (6) in Bialek (1996)
if(Sw_calc_powfrac > 0,
powerfrac_upstream(rr,r,h,t)$[(flow_through(rr,h,t)>0)$tmodel_new(t)] = 1 / flow_through(rr,h,t) * Ainv_upstream(rr,r,h,t) * totgen(r,h,t) ;
powerfrac_upstream(rr,r,h,t)$[(powerfrac_upstream(rr,r,h,t)<1e-3)$tmodel_new(t)] = 0 ;

* see equation (12) in Bialek (1996)
powerfrac_downstream(r,rr,h,t)$[(flow_through(r,h,t)>0)$tmodel_new(t)] = 1 / flow_through(r,h,t) * Ainv_downstream(r,rr,h,t) * totload(rr,h,t) ;
powerfrac_downstream(r,rr,h,t)$[(powerfrac_downstream(r,rr,h,t)<1e-3)$tmodel_new(t)] = 0 ;
) ;

* --- write the outputs ---
execute_unload "outputs%ds%rep_powerfrac_%fname%.gdx" powerfrac_downstream, powerfrac_upstream ;
