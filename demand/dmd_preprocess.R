# 
# Initially written 2018-01-08
# Dave Bielen
# NREL

###################################################
#################### OVERVIEW #####################
###################################################

system.time({

######################################################
#################### PRELIMINARY #####################
######################################################
  
#---------------------------
# Read switches
  
if(!exists("Args")) Args=commandArgs(TRUE)

cur.dir = Args[1]
  
setwd(cur.dir)
rm(list=ls())

#---------------------------
# Load packages
list.of.packages <- c("doBy","ggplot2","reshape2","ggthemes","plyr","RColorBrewer","scales","grid","gdxrrw","gtools","dtplyr","dplyr","xtable","data.table",
                      "zoo","openxlsx","doParallel","iterators","lpSolve","stringr","taRifx","MASS","rlang")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages, repos = "http://cran.us.r-project.org")



library(doBy)         #
library(ggplot2)      # nice plotting functionality
library(reshape2)     #
library(ggthemes)     #
library(plyr)         #
library(RColorBrewer) # 
library(scales)       #
library(grid)         #
library(gdxrrw)       # read and write GDX files
library(gtools)       #
library(dtplyr)       # helpful for applying dplyr to data tables
library(dplyr)        # convenient data frame operations (including faster merging)
library(xtable)       #
library(data.table)   # faster, more intuitive data frame operations
library(zoo)          # 
library(openxlsx)     # better Excel read and write operations
library(doParallel)   # parallelize operations in foreach
library(iterators)    # create fancy iterators for loops
library(lpSolve)      # linear program solver
library(stringr)      # faster string manipulation
library(taRifx)       # remove factors function
igdx("C:/gams/win64/24.7")

#---------------------------
# Parameters

#---------------------------
# Functions

#################################################
################### READ SETS ###################
#################################################

#---------------------------
# CSV

new.dvc.vec = fread("inputs/demand/processed data/new-device-set.csv", header = F, col.names = c("dvc.opt"))[[1]]

#################################################
################### READ DATA ###################
#################################################

#---------------------------
# CSV

disc.rate = fread("inputs/demand/processed data/discount-rates.csv", header = F, 
                  col.names = c("inc.lvl", "disc.rate"))

surv.rates = fread("//nrelnas01/ReEDS/FY18-ReEDS-2.0/DemandData/surv-rates.csv", header = F, 
                   col.names = c("ba", "vint", "year", "end.use","dvc.cls","dvc.opt", "surv.rate", "exp.life"))

cap.cost = fread("//nrelnas01/ReEDS/FY18-ReEDS-2.0/DemandData/device-capital-cost.csv", header = F, 
                 col.names = c("ba", "vint", "end.use", "dvc.cls", "dvc.opt", "cap.cost"))
cap.cost = cap.cost[dvc.opt %in% new.dvc.vec]

#---------------------------
# GDX
# (Note: The end-use "DRY" appears as lower case in the exported GAMS data.
# We use "toupper" to adjust this to facilitate merges with our outside
# data mapping sets.)

ref.dmd = setDT(rgdx.param("temp_dmd/dmd_preprocess.gdx", "ref_serv_dmd_device",
                                        names=c("inc.lvl","ba","year","time.slice","end.use","dvc.cls","ref.dmd"),
                                        compress=T, squeeze=F))

net.dvc.req = setDT(rgdx.param("temp_dmd/dmd_preprocess.gdx", "net_dvc_req",
                                       names=c("inc.lvl","ba","year","end.use","dvc.cls","net.dvc.req"),
                                       compress=T, squeeze=F))

lambda = setDT(rgdx.param("temp_dmd/dmd_preprocess.gdx", "lambda_test",
                                  names=c("ba","vint","end.use","dvc.cls", "dvc.opt", "eff"),
                                  compress=T, squeeze=F))

ref.eff = setDT(rgdx.param("temp_dmd/dmd_preprocess.gdx", "ref_eff_test", 
                                   names=c("inc.lvl","ba","year","end.use","dvc.cls", "ref.eff"),
                                   compress=T, squeeze=F))

res.elas = setDT(rgdx.param("temp_dmd/dmd_preprocess.gdx", "res_elas",
                                    names=c("inc.lvl","end.use", "elas"),
                                    compress=T, squeeze=F))

###################################################
################### FORMAT DATA ###################
###################################################

#---------------------------
# 

# remove factors
lambda = remove.factors(lambda)
net.dvc.req = remove.factors(net.dvc.req)
ref.dmd = remove.factors(ref.dmd)
ref.eff = remove.factors(ref.eff)
res.elas = remove.factors(res.elas)

# standardize end use cases
ref.dmd[, end.use := toupper(end.use)]
net.dvc.req[, end.use := toupper(end.use)]
ref.eff[, end.use := toupper(end.use)]
lambda[, end.use := toupper(end.use)]
res.elas[, end.use := toupper(end.use)]

# set year variables to integer type
ref.dmd[, year := as.integer(year)]
net.dvc.req[, year := as.integer(year)]
lambda[, vint := as.integer(vint)]
ref.eff[, year := as.integer(year)]

###########################################################
################### PRELIMINARY MERGING ###################
###########################################################

# This only needs to be done in the first iteration.

#---------------------------
# Service demand component

# merge reference efficiency with elasticities and discount rates
ref.effic = inner_join(inner_join(ref.eff, res.elas), disc.rate)

# merge reference demand with device purchases and reference efficiencies
ref.dmd = inner_join(ref.dmd, ref.effic)

#---------------------------
# Efficiency component

# merge efficiency with discount factors and capital costs
effic = inner_join(lambda, cap.cost)

############################################################
################### STRIP AND ORDER DATA ###################
############################################################

#---------------------------
# 

# remove prefixes (faster sorting and merging)
ref.dmd[, `:=` (ba = as.integer(str_extract(ba, "[[:digit:]]+")),
                inc.lvl = as.integer(str_extract(inc.lvl, "[[:digit:]]+")),
                time.slice = as.integer(str_extract(time.slice, "[[:digit:]]+")))]
effic[, ba := as.integer(str_extract(ba, "[[:digit:]]+"))]
surv.rates[, ba := as.integer(str_extract(ba, "[[:digit:]]+"))]
net.dvc.req[, `:=` (ba = as.integer(str_extract(ba, "[[:digit:]]+")),
                    inc.lvl = as.integer(str_extract(inc.lvl, "[[:digit:]]+")))]

# order by BA and income class (this is necessary for parallelization)
setorderv(ref.dmd, c("ba", "inc.lvl"))
setorderv(effic, c("ba"))
setorderv(surv.rates, c("ba"))
setorderv(net.dvc.req, c("ba", "inc.lvl"))

##################################################
################### WRITE TEST ###################
##################################################

#---------------------------
# 

save(ref.dmd, file = "temp_dmd/ref_dmd_preprocess.Rdata", compress = F)
save(effic, file = "temp_dmd/effic_preprocess.Rdata", compress = F)
save(surv.rates, file = "temp_dmd/surv_rate_preprocess.Rdata", compress = F)
save(net.dvc.req, file = "temp_dmd/net_dvc_req_preprocess.Rdata", compress = F)

})