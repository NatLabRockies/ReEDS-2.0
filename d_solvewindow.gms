* global needed for this file:
* case : name of case you're running
* niter : current iteration

$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$log 'Running window solve for...'
$log ' case == %case%'
$log ' iteration == %niter%'
$log ' window == %window%'

*remove any load years
tload(t) = no ;

$if not set niter $setglobal niter 0
$eval previter %niter%-1

tmodel(t) = no ;
*enable years that fall within the window range
tmodel(t)$[tmodel_new(t)$(yeart(t)>=solvewindows("%window%","start"))
                     $(yeart(t)<=solvewindows("%window%","stop"))] = yes ;


*reset tlast to the final modeled period for this window
*then re-compute the financial multiplier for pv
tlast(t) = no ;
tlast(t)$[ord(t)=smax(tt$tmodel(tt),ord(tt))] = yes ;

pvf_capital(t)$tmodel(t) = pvf_capital0(t) ;
pvf_onm(t) = pvf_onm0(t) ;
pvf_onm(t)$tlast(t) = round(pvf_capital0(t) / crf(t), 6) ;

*if this isn't the first iteration
$ifthene.notfirstiter %niter%>0

*============================
* --- CC and Curtailment ---
*============================

*indicate we're loading data
tload(t)$tmodel(t) = yes ;

$gdxin ReEDS_Augur%ds%augur_data%ds%ReEDS_Augur_merged_%niter%.gdx
$loaddcr loadset = merged_set_1
$loaddcr cc_old_load2 = cc_old
$loaddcr cc_mar_load2 = cc_mar
$loaddcr sdbin_size_load2 = sdbin_size
$gdxin

*collapse the set that came from merging the gdx files

cc_old_load(i,r,szn,t) = sum{loadset, sum{ccreg$r_ccreg(r,ccreg), cc_old_load2(loadset,i,r,ccreg,szn,t) } } ;
cc_mar_load(i,r,szn,t) = sum{loadset, sum{ccreg$r_ccreg(r,ccreg), cc_mar_load2(loadset,i,r,ccreg,szn,t) } } ;

sdbin_size_load(ccreg,szn,sdbin,t) = sum{loadset, sdbin_size_load2(loadset,ccreg,szn,sdbin,t) } ;

*===========================
* --- Begin Curtailment ---
*===========================

*Clear params before calculation
oldVREgen(r,h,t)$tload(t) = 0 ;
oldMINGEN(r,h,t)$tload(t) = 0 ;


oldVREgen(r,h,t)$tload(t) =
    sum{(i,v)$[vre(i)$valcap(i,v,r,t)],
          m_cf(i,v,r,h,t) * CAP.l(i,v,r,t)
       } ;

oldMINGEN(r,h,t)$[Sw_Mingen$tload(t)] = sum{h_szn(h,szn), MINGEN.l(r,szn,t) } ;

*===============================
* --- Begin Capacity Credit ---
*===============================

*Clear params before calculation
cc_int(i,v,r,szn,t) = 0 ;
cc_totmarg(i,r,szn,t) = 0 ;
cc_excess(i,r,szn,t) = 0 ;
cc_scale(i,r,szn,t) = 0 ;
sdbin_size(ccreg,szn,sdbin,t)$tload(t) = 0 ;

*Storage duration bin sizes by year
sdbin_size(ccreg,szn,sdbin,t)$tload(t) = sdbin_size_load(ccreg,szn,sdbin,t) ;

*Sw_Int_CC=0 means use average capacity credit for each tech, and don't differentiate vintages
*If there is no existing capacity to calculate average, use marginal capacity credit instead.
if(Sw_Int_CC=0,
    cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)$sum{(vv)$(valcap(i,vv,r,t)), CAP.l(i,vv,r,t) }] =
        cc_old_load(i,r,szn,t) / sum{(vv)$(valcap(i,vv,r,t)), CAP.l(i,vv,r,t) } ;
    cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)$(cc_old_load(i,r,szn,t)=0)] = m_cc_mar(i,r,szn,t) ;
) ;

*For the remaining options we initially use marginal values for cc_int, differentiated by vintage based on seasonal capacity factors.
if(Sw_Int_CC=1 or Sw_Int_CC=2,
    cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)$sum{vv$ivt(i,vv,t), m_cf_szn(i,vv,r,szn,t) }] =
        m_cc_mar(i,r,szn,t) * m_cf_szn(i,v,r,szn,t) / sum{vv$ivt(i,vv,t), m_cf_szn(i,vv,r,szn,t) } ;
    cc_totmarg(i,r,szn,t)$[tload(t)$(vre(i) or storage(i))] = sum{v$valcap(i,v,r,t), cc_int(i,v,r,szn,t) * CAP.l(i,v,r,t) } ;
) ;

*Sw_Int_CC=1 means use average capacity credit for each tech, but differentiate based on vintage.
*Start with marginal capacity credit with seasonal vintage-based capacity factor adjustment,
*and scale with cc_old_load to result in the correct total capacity credit.
if(Sw_Int_CC=1,
    cc_scale(i,r,szn,t)$[tload(t)$(vre(i) or storage(i))] = 1 ;
    cc_scale(i,r,szn,t)$[tload(t)$(vre(i) or storage(i))$cc_totmarg(i,r,szn,t)] = cc_old_load(i,r,szn,t) / cc_totmarg(i,r,szn,t) ;
    cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)] = cc_int(i,v,r,szn,t) * cc_scale(i,r,szn,t) ;
) ;

*Sw_Int_CC=2 means use marginal capacity credit, adjusted by seasonal capacity factors by vintage
if(Sw_Int_CC=2,
    cc_excess(i,r,szn,t)$[tload(t)$cc_totmarg(i,r,szn,t)] = cc_old_load(i,r,szn,t) - cc_totmarg(i,r,szn,t) ;
) ;


*no longer want m_cc_mar since it should not enter the planning reserve margin constraint
m_cc_mar(i,r,szn,t) = 0 ;

cc_int(i,v,r,szn,t)$[cc_int(i,v,r,szn,t) > 1] = 1 ;
cc_int(i,v,r,szn,t)$[tload(t)$csp_storage(i)$valcap(i,v,r,t)] = 1 ;

*=======================================
* --- Begin Averaging of CC/Curt ---
*=======================================

$ifthene.afterseconditer %niter%>1

*when set to 1 - it will take the average over all previous iterations
if(Sw_AVG_iter=1,
        cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)] = round((cc_int(i,v,r,szn,t) + cc_iter(i,v,r,szn,t,"%previter%")) / 2 ,4) ;
    ) ;

$endif.afterseconditer

*Remove very small numbers to make it easier for the solver
cc_int(i,v,r,szn,t)$[cc_int(i,v,r,szn,t) < 0.001] = 0 ;

cc_iter(i,v,r,szn,t,"%niter%")$cc_int(i,v,r,szn,t) = cc_int(i,v,r,szn,t) ;

execute_unload 'ReEDS_Augur%ds%augur_data%ds%curtout_%case%_%niter%.gdx' cc_int, oldVREgen ;

*following line will load in the level values if the switch is enabled
*note that this is still within the conditional that we are now past the first iteration
*and thus a loadpoint is enabled
if(Sw_Loadpoint = 1,
execute_loadpoint 'gdxfiles%ds%%case%_load.gdx' ;
%case%.optfile = 8 ;
) ;

$endif.notfirstiter

*==============================
* --- Solve Supply Side ---
*==============================

solve ReEDSmodel using lp minimizing z ;

*add years to tfix(t) if this is the last iteration
$ifthene.lastiter %niter%=%maxiter%

$eval nextwindow %window% + 1
tfix(t)$(tmodel(t)$(yeart(t)<solvewindows("%nextwindow%","start"))) = yes ;
$include d2_varfix.gms

$endif.lastiter
