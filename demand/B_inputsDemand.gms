*!!! note, need to add network location of
*!!! "\\nrelqnap01d\ReEDS



$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix


set dflex(t) "set where demand is responsive to price and not fixed only the first year is inflexible to avoid infeasibilities";

*helps avoid infeasibilities that demand is greater than capacity
dflex(t)$(not tfirst(t)) = yes;

* native sets
set
         sec "demand sectors"
         /res,com,ind/
         y "income classes from American Community Survey"
$offlisting
/
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%income-class-set.csv
/
         u "end uses"
/
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%end-use-set.csv
/
         d "device class"
/
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%device-class-set.csv
/
         o "device options"
/
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%device-option-set.csv
/
$onlisting
;

* alias sets
alias(y,y2);
alias(u,u2);
alias(h,h2);
alias(d,d2);
alias(o,o2);
* vintages
alias(t,v);

* subsets sets
set
         onew(o) "new device options"
$offlisting
/
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%new-device-set.csv
/
         obase(o) "base stock device options"
/
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%base-device-set.csv
/
$onlisting
         demr(r) "demand model regions"
;

* mapping sets
demr(r) = yes ;


set      use2dev(u,d) "feasibility set for end-use and device class"
/
$ondelim offlisting
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%use-dvc-map.csv
$offdelim onlisting
/

         use2dev2opt(u,d,o) "feasibility set for end-use, device class, and technology options"
/
$ondelim offlisting
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%use-dvc-opt-map.csv
$offdelim onlisting
/
         validdem(y,r) "demand mapping set for testing"
;

* direct input parameters

parameter
         discrate(y) "discount rate for each income class class"
/
$ondelim offlisting
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%discount-rates.csv
$offdelim onlisting
/
;

* !!!! gives error, figure this out later...
*$if not exist "%gams.curdir%/inputs/demand/processed data/base-stock-counts.csv" $call 'copy \\nrelqnap01d\ReEDS\FY18-ReEDS-2.0\DemandData\base-stock-counts.csv %gams.curdir%\inputs\demand\processed data'


parameter
         base_stock(y,r,t,u,d,obase) "initial stock remaining in t"
/
$ondelim offlisting
$include '\\nrelnas01\ReEDS\%ds%FY18-ReEDS-2.0%ds%DemandData%ds%base-stock-counts.csv'
$offdelim onlisting
/

         tot_devices(y,r,t,u,d) "total number of devices"
/
$ondelim offlisting
$include '\\nrelnas01\ReEDS\%ds%FY18-ReEDS-2.0%ds%DemandData%ds%total-device-counts.csv'
$offdelim onlisting
/

         ref_serv_demand(y,r,t,h,u,d) "baseline service consumption"
/
$ondelim offlisting
$include '\\nrelnas01\ReEDS\%ds%FY18-ReEDS-2.0%ds%DemandData%ds%service-cons.csv'
$offdelim onlisting
/

         ref_eff(y,r,t,u,d) "reference efficiency level"
/
$ondelim offlisting
$include '\\nrelnas01\ReEDS\%ds%FY18-ReEDS-2.0%ds%DemandData%ds%ref-eff.csv'
$offdelim onlisting
/

         lambda(r,t,u,d,o) "device efficiency"
/
$ondelim offlisting
$include '\\nrelnas01\ReEDS\%ds%FY18-ReEDS-2.0%ds%DemandData%ds%device-efficiency.csv'
$offdelim onlisting
/

         cap_cost(r,t,u,d,o) "cost of investment capital"
/
$ondelim offlisting
$include '\\nrelnas01\ReEDS\%ds%FY18-ReEDS-2.0%ds%DemandData%ds%device-capital-cost.csv'
$offdelim onlisting
/

         ref_price(r,t,h) "reference price from the BAU solve of the supply side"
/
$ondelim offlisting
$include '\\nrelnas01\ReEDS\%ds%FY18-ReEDS-2.0%ds%DemandData%ds%ref-price-temp.csv'
$offdelim onlisting
/

         ref_cons(r,t,h) "reference consumption level"
/
$ondelim offlisting
$include '\\nrelnas01\ReEDS\%ds%FY18-ReEDS-2.0%ds%DemandData%ds%ref-consumption.csv'
$offdelim onlisting
/

         ref_com_cons(r,t,h) "reference commercial buildings consumption level"
/
$ondelim offlisting
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%commercial-load.csv
$offdelim onlisting
/

         ref_ind_cons(r,t,h) "reference industrial facilities consumption level"
/
$ondelim offlisting
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%industrial-load.csv
$offdelim onlisting
/
;

* calculated parameters
parameter
         res_elas(y,u) "residential demand elasticity"
         discfact(y,t) "discount factor (i.e. the resulting calculation from the discount rate)"
         ref_serv_dmd_use(y,r,t,h,u) "baseline service demand per use (exogenous)",
         ref_serv_dmd_device(y,r,t,h,u,d) "baseline service demand per device (exogenous)"
         net_dvc_req(y,r,t,u,d) "net device requirement (total requirement less remaining base stock)"
;

* other parameters
parameter
         com_elas
         / 0.5 /
         ind_elas
         / 0.5 /
;

* temporary: assign residential price elasticities
res_elas(y,u) = 0.5;

* calculate discount factor associated with discount rate
discfact(y,t) = 1/((1+discrate(y))**(ord(t)-1));

$ontext
* calculate survival rates
* (note: new devices only. Currently, these are calculated in R and read into
* GAMS directly from CSV. To calculate in GAMS, make sure an empty parameter is
* declared above.)
survrate(r,v,t,u,d,onew)$(ord(t) >= ord(v) and device_map(u,d,onew)) = (exp(-((ord(t)-ord(v))/scale(r,v,u,d,onew))**shape(r,v,u,d,onew)));
survrate(r,v,t,u,d,onew)$(survrate(r,v,t,u,d,onew)<1e-3) = 0;
$offtext

set demr(r);
demr(r)$(ord(r)<=134) = yes;

* calculate service demand per device
* (note: currently, this is calculated at the device class level. Eventually, we
* will want to expand this to the end-use level for some, if not all, end uses.)
ref_serv_dmd_use(y,r,t,h,u)$demr(r)
      = sum(d$use2dev(u,d), ref_serv_demand(y,r,t,h,u,d))
      / sum(d$use2dev(u,d), tot_devices(y,r,t,u,d));

ref_serv_dmd_device(y,r,t,h,u,d)$(use2dev(u,d) and tot_devices(y,r,t,u,d) and demr(r))
      = ref_serv_demand(y,r,t,h,u,d) / tot_devices(y,r,t,u,d);

ref_serv_dmd_device(y,r,t,h,u,d)$(use2dev(u,d)$(tot_devices(y,r,t,u,d) = 0)$demr(r))
      = ref_serv_dmd_use(y,r,t,h,u);

ref_serv_dmd_device(y,r,t,h,u,d)$(use2dev(u,d) and (ref_serv_demand(y,r,t,h,u,d) = 0) and demr(r))
      = ref_serv_dmd_use(y,r,t,h,u);

* calculate net device requirement after subtracting out base stock
net_dvc_req(y,r,t,u,d)$(use2dev(u,d) and demr(r)) = tot_devices(y,r,t,u,d) - sum(obase$use2dev2opt(u,d,obase), base_stock(y,r,t,u,d,obase));

* reference levels and supply module prices
parameter
         psupply "price from the supply side model"
         psupply0 "reference price from the supply side model"
         ref_rtl_price_avg(sec,r,t) "reference average retail price"
         ref_rtl_price(sec,r,t,h) "reference retail price"
;

*psupply(s,r,t,h)$(tmodel(t)$pvf(t)) = 1;
*psupply0(s,r,t,h)$(tmodel(t)$pvf(t)) = 1;

*demand side setup and assumptions
parameter
         dmd_conv(sec) "residential is mmBtu to MWh conversion"
         / res 0.293071083333, com 1, ind 1 /
*         retail_adder(s) "retail price adder ($/MWh)"
*         / res 80, com 45, ind 20 /
         retail_adder(r,sec) "retail price adder ($/MWh)"
         retail_adder_(sec,r) "retail price adder ($/MWh)"
/
$ondelim offlisting
$include %gams.curdir%%ds%inputs%ds%demand%ds%processed data%ds%price-adders.csv
$offdelim onlisting
/
;

retail_adder(r,sec) = retail_adder_(sec,r);

ref_rtl_price_avg(sec,r,t)$demr(r) = sum(h, ref_price(r,t,h)*ref_cons(r,t,h))/sum(h, ref_cons(r,t,h)) + retail_adder(r,sec);
ref_rtl_price(sec,r,t,h)$demr(r) = ref_price(r,t,h) + retail_adder(r,sec);

* convert prices from $/MWh to $/mmBtu for residential sector and assign initial price values
psupply0(sec,r,t,h)$demr(r) = dmd_conv(sec)*ref_rtl_price_avg(sec,r,t);


* demand parameters calculated as part of the demand-side model
Parameter
        ResDmdNew(r,t,h,u)      "total residential electricity demand from new devices"
        ResDmdBase(r,t,h)     "total residential electricity demand from base stock devices"
        DmdSec(sec,r,t,h)     "total electricity demand by sector"
;

* testing data
parameter
         lambda_test(r,t,u,d,o)
         ref_eff_test(y,r,t,u,d)
;

* update parameters to reflect subsetted data
lambda_test(r,t,u,d,o)$(use2dev2opt(u,d,o) and demr(r)) = lambda(r,t,u,d,o);
ref_eff_test(y,r,t,u,d)$(use2dev(u,d) and demr(r)) = ref_eff(y,r,t,u,d)

* export preprocessing data for R
Execute_Unload "%gams.curdir%/temp_dmd/dmd_preprocess.gdx", demr, net_dvc_req, ref_serv_dmd_device, lambda_test, ref_eff_test, res_elas, r;

Execute 'Rscript %gams.curdir%%ds%demand%ds%dmd_preprocess.R %gams.curdir%';


*!!!!
*!!!!
lmnt(r,h,t)$(SwI_Load = 2) = ref_cons(r,t,h) / hours(h);
lmnt0(r,h,t)$(SwI_Load = 2) = lmnt(r,h,t);

peakdem_h17_ratio(r,szn,t)$(lmnt(r,"h17",t)) = peakdem(r,szn,t) / lmnt(r,"h17",t);
