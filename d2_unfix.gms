* load variable - set equal to load_exog to compute holistic marginal price
  LOAD.lo(r,h,t)$tmodel(t) = 0 ;
    EVLOAD.lo(r,h,t)$tmodel(t) = 0 ;
    FLEX.lo(flex_type,r,h,t)$tmodel(t) = 0 ;
    PEAK_FLEX.lo(r,allszn,t)$tmodel(t) = 0 ;

* capacity and investment variables
  CAP_SDBIN.lo(i,v,r,allszn,sdbin,t)$tmodel(t) = 0 ;
    CAP.lo(i,v,r,t)$tmodel(t) = 0 ;
    INV.lo(i,v,r,t)$tmodel(t) = 0 ;
    EXTRA_PRESCRIP.lo(pcat,r,t)$tmodel(t) = 0 ;
    INV_CAP_UP.lo(i,v,r,rscbin,t)$tmodel(t) = 0 ;
    INV_ENER_UP.lo(i,v,r,rscbin,t)$tmodel(t) = 0 ;
    INV_REFURB.lo(i,v,r,t)$tmodel(t) = 0 ;
    INV_RSC.lo(i,v,r,rscbin,t)$tmodel(t) = 0 ;
    UPGRADES.lo(i,v,r,t)$tmodel(t) = 0 ;

* The units for  all of the operatinal variables are average MW or MWh/time-slice hours
* generation and storage variables
  GEN.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    GEN_PVB_P.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    GEN_PVB_B.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    CURT.lo(r,h,t)$tmodel(t) = 0 ;
    MINGEN.lo(r,allszn,t)$tmodel(t) = 0 ;
    STORAGE_IN.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    STORAGE_IN_PVB_P.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    STORAGE_IN_PVB_G.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    STORAGE_LEVEL.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    DR_SHIFT.lo(i,v,r,h,hh,t)$tmodel(t) = 0 ;
    DR_SHED.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    PRODUCE.lo(p,i,v,r,h,t)$tmodel(t) = 0 ;
    LAST_HOUR_SOC.lo(i,v,r,h,t)$tmodel(t) = 0 ;

* flexible CCS variables
  CCSFLEX_POW.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    CCSFLEX_POWREQ.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    CCSFLEX_STO_STORAGE_LEVEL.lo(i,v,r,h,t)$tmodel(t) = 0 ;
    CCSFLEX_STO_STORAGE_CAP.lo(i,v,r,t)$tmodel(t) = 0 ;

* trade variables
  FLOW.lo(r,rr,h,t,trtype)$tmodel(t) = 0 ;
    OPRES_FLOW.lo(ortype,r,rr,h,t)$tmodel(t) = 0 ;
    PRMTRADE.lo(r,rr,trtype,allszn,t)$tmodel(t) = 0 ;

* operating reserve variables
  OPRES.lo(ortype,i,v,r,h,t)$tmodel(t) = 0 ;

* variable fuel amounts
  GASUSED.lo(cendiv,gb,h,t)$tmodel(t) = 0 ;
    VGASBINQ_NATIONAL.lo(fuelbin,t)$tmodel(t) = 0 ;
    VGASBINQ_REGIONAL.lo(fuelbin,cendiv,t)$tmodel(t) = 0 ;
    BIOUSED.lo(bioclass,r,t)$tmodel(t) = 0 ;

* RECS variables
  RECS.lo(RPSCat,i,st,ast,t)$tmodel(t) = 0 ;
    ACP_Purchases.lo(RPSCat,st,t)$tmodel(t) = 0 ;

* transmission variables
  CAPTRAN_ENERGY.lo(r,rr,trtype,t)$tmodel(t) = 0 ;
  CAPTRAN_PRM.lo(r,rr,trtype,t)$tmodel(t) = 0 ;
    INVTRAN.lo(r,rr,trtype,t)$tmodel(t) = 0 ;
    CAP_CONVERTER.lo(r,t)$tmodel(t) = 0 ;
    INV_CONVERTER.lo(r,t)$tmodel(t) = 0 ;
    CONVERSION.lo(r,h,intype,outtype,t)$tmodel(t) = 0 ;
    CONVERSION_PRM.lo(r,allszn,intype,outtype,t)$tmodel(t) = 0 ;

* hydrogen-specific variables
  H2_FLOW.lo(r,rr,p,h,t)$tmodel(t) = 0 ;
    H2_TRANSPORT_INV.lo(r,rr,t)$tmodel(t) = 0 ;

* water climate variables
  WATCAP.lo(i,v,r,t)$tmodel(t) = 0 ;
    WAT.lo(i,v,w,r,h,t)$tmodel(t) = 0 ;
    WATER_CAPACITY_LIMIT_SLACK.lo(wst,r,t)$tmodel(t) = 0 ;

  emit.lo(e,r,t)$tmodel(t) = -inf ;


LOAD.up(r,h,t)$tmodel(t) = +inf ;
EVLOAD.up(r,h,t)$tmodel(t) = +inf ;
FLEX.up(flex_type,r,h,t)$tmodel(t) = +inf ;
PEAK_FLEX.up(r,allszn,t)$tmodel(t) = +inf ;
GROWTH_BIN(gbin,i,st,t).up$tmodel(t) = +inf ;
CAP_SDBIN.up(i,v,r,allszn,sdbin,t)$tmodel(t) = +inf ;
CAP.up(i,v,r,t)$tmodel(t) = +inf ;
INV.up(i,v,r,t)$tmodel(t) = +inf ;
EXTRA_PRESCRIP.up(pcat,r,t)$tmodel(t) = +inf ;
INV_CAP_UP.up(i,v,r,rscbin,t)$tmodel(t) = +inf ;
INV_ENER_UP.up(i,v,r,rscbin,t)$tmodel(t) = +inf ;
INV_REFURB.up(i,v,r,t)$tmodel(t) = +inf ;
INV_RSC.up(i,v,r,rscbin,t)$tmodel(t) = +inf ;
UPGRADES.up(i,v,r,t)$tmodel(t) = +inf ;
GEN.up(i,v,r,h,t)$tmodel(t) = +inf ;
GEN_PVB_P.up(i,v,r,h,t)$tmodel(t) = +inf ;
GEN_PVB_B.up(i,v,r,h,t)$tmodel(t) = +inf ;
CURT.up(r,h,t)$tmodel(t) = +inf ;
MINGEN.up(r,allszn,t)$tmodel(t) = +inf ;
STORAGE_IN.up(i,v,r,h,t)$tmodel(t) = +inf ;
STORAGE_IN_PVB_P.up(i,v,r,h,t)$tmodel(t) = +inf ;
STORAGE_IN_PVB_G.up(i,v,r,h,t)$tmodel(t) = +inf ;
STORAGE_LEVEL.up(i,v,r,h,t)$tmodel(t) = +inf ;
DR_SHIFT.up(i,v,r,h,hh,t)$tmodel(t) = +inf ;
DR_SHED.up(i,v,r,h,t)$tmodel(t) = +inf ;
PRODUCE.up(p,i,v,r,h,t)$tmodel(t) = +inf ;
LAST_HOUR_SOC.up(i,v,r,h,t)$tmodel(t) = +inf ;
CCSFLEX_POW.up(i,v,r,h,t)$tmodel(t) = +inf ;
CCSFLEX_POWREQ.up(i,v,r,h,t)$tmodel(t) = +inf ;
CCSFLEX_STO_STORAGE_LEVEL.up(i,v,r,h,t)$tmodel(t) = +inf ;
CCSFLEX_STO_STORAGE_CAP.up(i,v,r,t)$tmodel(t) = +inf ;
FLOW.up(r,rr,h,t,trtype)$tmodel(t) = +inf ;
OPRES_FLOW.up(ortype,r,rr,h,t)$tmodel(t) = +inf ;
PRMTRADE.up(r,rr,trtype,allszn,t)$tmodel(t) = +inf ;
OPRES.up(ortype,i,v,r,h,t)$tmodel(t) = +inf ;
GASUSED.up(cendiv,gb,h,t)$tmodel(t) = +inf ;
VGASBINQ_NATIONAL.up(fuelbin,t)$tmodel(t) = +inf ;
VGASBINQ_REGIONAL.up(fuelbin,cendiv,t)$tmodel(t) = +inf ;
BIOUSED.up(bioclass,r,t)$tmodel(t) = +inf ;
RECS.up(RPSCat,i,st,ast,t)$tmodel(t) = +inf ;
ACP_Purchases.up(RPSCat,st,t)$tmodel(t) = +inf ;
CAPTRAN_ENERGY.up(r,rr,trtype,t)$tmodel(t) = +inf ;
CAPTRAN_PRM.up(r,rr,trtype,t)$tmodel(t) = +inf ;
INVTRAN.up(r,rr,trtype,t)$tmodel(t) = +inf ;
CAP_CONVERTER.up(r,t)$tmodel(t) = +inf ;
INV_CONVERTER.up(r,t)$tmodel(t) = +inf ;
CONVERSION.up(r,h,intype,outtype,t)$tmodel(t) = +inf ;
CONVERSION_PRM.up(r,allszn,intype,outtype,t)$tmodel(t) = +inf ;
H2_FLOW.up(r,rr,p,h,t)$tmodel(t) = +inf ;
H2_TRANSPORT_INV.up(r,rr,t)$tmodel(t) = +inf ;
WATCAP.up(i,v,r,t)$tmodel(t) = +inf ;
WAT.up(i,v,w,r,h,t)$tmodel(t) = +inf ;
WATER_CAPACITY_LIMIT_SLACK.up(wst,r,t)$tmodel(t) = +inf ;
emit.up(e,r,t)$tmodel(t) = +inf ;
  
