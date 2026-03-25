# 
# Initially written 2018-01-08
# Dave Bielen
# NREL

###################################################
#################### OVERVIEW #####################
###################################################

# Note: there are commented lines of code in this document
# that can be used for testing purposes.

system.time({

######################################################
#################### PRELIMINARY #####################
######################################################
  
#---------------------------
# Clear global environment

rm(list=ls())

#---------------------------
# Read switches
  
if(!exists("Args")) Args=commandArgs(TRUE)

cur.dir = Args[1]
ncores = as.integer(Args[2])
conv.stat = as.integer(Args[3])
firstrun= Args[4]
ref.price = Args[5]
output.lvl = Args[6]
gdxfile = paste("temp_dmd/price_iter_",Args[7],".gdx",sep="")
gdxout = paste("temp_dmd/dmd_iter_", output.lvl, "_", ref.price,"_",Args[7],".gdx",sep="")

gamsdir = paste(Args[8])

print(paste("Current case and iteration:",Args[7]))
print(paste("Loading:",gdxfile))
print(paste("Creating:",gdxout))
print(paste("Using GAMS version:",gamsdir))
print(paste("Using",ncores,"cores"))
print(paste("Convergence stat =",as.character(conv.stat)))
print(paste("Output level =",output.lvl))
print(paste("Reference price =",ref.price))
# set working directory
setwd(cur.dir)

# conv.stat = 0
# ncores = 12
# setwd('D:/ReEDS_DBielen/ReEDS-2.0')
# output.lvl = "US"

#---------------------------
# Load packages

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

# reference the proper location of the gams files
igdx(gamsdir)

#---------------------------
# Parameters

alpha = 0.1

#---------------------------
# Functions

# Cartesian "join"
CJ.table <- function(X,Y)
  setkey(X[,c(k=1,.SD)],k)[Y[,c(k=1,.SD)],allow.cartesian=TRUE][,k:=NULL]

# return multiple results from parallelization
multiResultClass <- function(result1=NULL,result2=NULL)
{
  me <- list(
    result1 = result1,
    result2 = result2
  )

  ## Set the name for the class
  class(me) <- append(class(me),"multiResultClass")
  return(me)
}

#################################################
################### READ SETS ###################
#################################################

#---------------------------
# CSV

vint.vec = data.table(vint = 2010:2050)
dvc.map = fread("inputs/demand/processed data/use-dvc-opt-map.csv", header = F, col.names = c("end.use","dvc.cls","dvc.opt"))
new.dvc.vec = fread("inputs/demand/processed data/new-device-set.csv", header = F, col.names = c("dvc.opt"))[[1]]
dvc.map = dvc.map[dvc.opt %in% new.dvc.vec]

#---------------------------
# GDX
if(firstrun==1){
  rfeasgdx = "temp_dmd/dmd_preprocess.gdx"
}

if(firstrun==0){
  rfeasgdx = gdxfile
}


ba.vec = setDT(rgdx.set(rfeasgdx, "r",names=c("ba"), compress=T))

ba.vec <- ba.vec[, ba := as.integer(gsub("p","",ba))][[1]]





#################################################
################### READ DATA ###################
#################################################

#---------------------------
# Rdata

load("temp_dmd/ref_dmd_preprocess.Rdata")
load("temp_dmd/effic_preprocess.Rdata")
load("temp_dmd/surv_rate_preprocess.Rdata")
load("temp_dmd/net_dvc_req_preprocess.Rdata")

# subset based on feasible regions
ref.dmd = ref.dmd[ba %in% ba.vec]
effic = effic[ba %in% ba.vec]
surv.rates = surv.rates[ba %in% ba.vec]
net.dvc.req = net.dvc.req[ba %in% ba.vec]

#---------------------------
# GDX (prices)
# (Note: We could load and merge reference prices in the preprocessing step.
# That would decrease the number of merges in each iteration (we merge ref price
# with new price), but it would increase the number of "big" merges (e.g., anything
# merged with ref demand, which has a ton of indices). Merging the price tables is
# pretty quick, so we opt for for that approach instead.)

psupply = remove.factors(setDT(rgdx.param(gdxfile, "psupply",
                                   names=c("sector","ba","year","time.slice", "price"),
                                   compress=T, squeeze=F)))
psupply = psupply[sector == "res"][, sector := NULL]
psupply[, year := as.integer(year)]
psupply[, `:=` (ba = as.integer(str_extract(ba, "[[:digit:]]+")), 
                time.slice = as.integer(str_extract(time.slice, "[[:digit:]]+")))]

psupply0 = remove.factors(setDT(rgdx.param(gdxfile, "psupply0",
                                    names=c("sector","ba","year","time.slice", "ref.price"),
                                    compress=T, squeeze=F)))
psupply0 = psupply0[sector == "res"][, sector := NULL]
psupply0[, year := as.integer(year)]
psupply0[, `:=` (ba = as.integer(str_extract(ba, "[[:digit:]]+")), 
                time.slice = as.integer(str_extract(time.slice, "[[:digit:]]+")))]

#####################################################
################### PRICE MERGING ###################
#####################################################

#---------------------------
#

# merge reference demand with prices
ref.dmd = inner_join(ref.dmd, inner_join(psupply, psupply0))
setorderv(ref.dmd, c("ba", "inc.lvl"))

######################################################################
################### PARALLEL MERGE AND CALCULATION ###################
######################################################################

#---------------------------
#

# register workers for parallel processing
registerDoParallel(ncores)

system.time({
if (conv.stat == 0) {
  # calculate new demand quantities
  new.dmd <- foreach(dt.dmd1 = isplit(ref.dmd, ref.dmd$ba, drop = TRUE),
                     dt.eff = isplit(effic, effic$ba, drop = TRUE),
                     dt.surv = isplit(surv.rates, surv.rates$ba, drop = TRUE),
                     dt.dvc.req1 = isplit(net.dvc.req, net.dvc.req$ba, drop = TRUE),
                     .combine = list, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
                     .packages = c("dplyr", "data.table", "dtplyr", "lpSolve"))  %:%
    foreach(dt.dmd = isplit(dt.dmd1[[1]], dt.dmd1[[1]]$inc.lvl, drop = TRUE),
            dt.dvc.req = isplit(dt.dvc.req1[[1]], dt.dvc.req1[[1]]$inc.lvl, drop = TRUE),
            .combine = rbind, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
            .packages = c("dplyr", "data.table", "dtplyr", "lpSolve"))  %dopar% {

                       # assign imported data as type "data table"
                       dt.dmd = setDT(dt.dmd[[1]])
                       dt.eff = setDT(dt.eff[[1]])
                       dt.surv = setDT(dt.surv[[1]])
                       dt.dvc.req = setDT(dt.dvc.req[[1]])

                       # assign constraint RHS vector
                       setkeyv(dt.dvc.req, c("year", "end.use", "dvc.cls"))
                       const.rhs = dt.dvc.req[, .(net.dvc.req)][[1]]

                       # merge demand with efficiency
                       temp0 = inner_join(full_join(CJ.table(dt.dmd, vint.vec)[vint <= year],
                                                    dvc.map), dt.eff)

                       # calculate demand and consumer surplus
                       temp0[, dmd := ref.dmd*((price/eff)/(ref.price/ref.eff))^(-elas)
                             ][, cons.surp := (ref.price/ref.eff)*(ref.dmd^(1/elas))*(elas/(elas-1))*
                                 ((dmd^((elas-1)/elas))-((alpha*ref.dmd)^((elas-1)/elas)))
                               ][, `:=` (ref.dmd = NULL, ref.price = NULL, ref.eff = NULL, elas = NULL)]

                       # merge demand with survival rates
                       temp0 = inner_join(temp0, dt.surv)
                       setorderv(temp0, c("year", "end.use", "dvc.cls", "dvc.opt", "vint"))

                       # assign equation and variable numbers
                       temp0[, const.num := .GRP, by = .(year, end.use, dvc.cls)
                             ][, var.num := .GRP, by = .(end.use, dvc.cls, dvc.opt, vint)]

                       # sum electricity expenditures and consumer surplus across time slices
                       temp = temp0[, .(exp = sum((price/eff)*dmd), cons.surp = sum(cons.surp)),
                                    by = .(ba, inc.lvl, year, end.use, dvc.cls, dvc.opt, vint,
                                           const.num, var.num, disc.rate, cap.cost, surv.rate,
                                           exp.life)]

                       # remove extraneous columns
                       temp0[, price := NULL]

                       # set order
                       temp = temp[order(const.num, var.num)]

                       # extract dense constraint matrix
                       const.mat = as.matrix(temp[, .(const.num, var.num, surv.rate)])

                       # assign capital costs to rows where vintage = year
                       temp[, cap.cost := ifelse(vint == year, cap.cost, 0)]

                       # calculate end of horizon correction factor based on discount rate and expected device lifetime
                       # conditional on survival until 2050
                       temp[, eoh.fctr := ifelse(exp.life > 0, (1-(1/(1+disc.rate))^(exp.life-(year-vint)))/(1-(1/(1+disc.rate))), 1)]

                       # calculate total lifetime value for each device vintage
                       temp = temp[, .(value = sum((1/(1+disc.rate))^(year-2010)*(cap.cost+eoh.fctr*surv.rate*(exp-cons.surp)))),
                                   by = .(ba, inc.lvl, end.use, dvc.cls, dvc.opt, vint, var.num)]

                       # extract objective function vector
                       obj.vec = temp[, .(value)][[1]]

                       # create constraint direction vector
                       const.dir = rep("=", max(const.mat[, 1]))

                       # solve program
                       results = lp(direction = "min", objective.in = obj.vec, const.dir = const.dir,
                                    const.rhs = const.rhs, dense.const = const.mat)$solution

                       # add results to variable identifier matrix
                       temp = cbind(data.table(var.num = seq(1, max(const.mat[, 2]))), data.table(dvc.purch = results))

                       # merge into larger consumption table
                       temp = inner_join(temp0, temp)

                       # sum electricity consumption at the BA, year, and time slice (main result)
                       if (output.lvl == 'Default'){
                         
                         temp[, .(elec.cons = sum(dmd/eff*surv.rate*dvc.purch)), by = .(ba, inc.lvl, year, time.slice)]
                         
                       } else if (output.lvl == 'use'){
                         
                         temp[, .(elec.cons = sum(dmd/eff*surv.rate*dvc.purch)),
                              by = .(ba, inc.lvl, year, time.slice, end.use)]
                         
                       } else {
                         
                         stop ('Choose a valid output level parameter')
                         
                       }
                    
                       
                       
                     }
} else if (conv.stat == 1){
  # retrieve demand outputs
  outputs <- foreach(dt.dmd1 = isplit(ref.dmd, ref.dmd$ba, drop = TRUE),
                     dt.eff = isplit(effic, effic$ba, drop = TRUE),
                     dt.surv = isplit(surv.rates, surv.rates$ba, drop = TRUE),
                     dt.dvc.req1 = isplit(net.dvc.req, net.dvc.req$ba, drop = TRUE),
                     .combine = list, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
                     .packages = c("dplyr", "data.table", "dtplyr", "lpSolve"))  %:%
    foreach(dt.dmd = isplit(dt.dmd1[[1]], dt.dmd1[[1]]$inc.lvl, drop = TRUE),
            dt.dvc.req = isplit(dt.dvc.req1[[1]], dt.dvc.req1[[1]]$inc.lvl, drop = TRUE),
            .combine = rbind, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
            .packages = c("dplyr", "data.table", "dtplyr", "lpSolve"))  %dopar% {

              # assign imported data as type "data table"
              dt.dmd = setDT(dt.dmd[[1]])
              dt.eff = setDT(dt.eff[[1]])
              dt.surv = setDT(dt.surv[[1]])
              dt.dvc.req = setDT(dt.dvc.req[[1]])

              # assign constraint RHS vector
              const.rhs = dt.dvc.req[order(year, end.use, dvc.cls), .(net.dvc.req)][[1]]

              # merge demand with efficiency
              temp0 = inner_join(full_join(CJ.table(dt.dmd, vint.vec)[vint <= year],
                                           dvc.map), dt.eff)

              # calculate demand and consumer surplus
              temp0[, dmd := ref.dmd*((price/eff)/(ref.price/ref.eff))^(-elas)
                    ][, cons.surp := (ref.price/ref.eff)*(ref.dmd^(1/elas))*(elas/(elas-1))*
                        ((dmd^((elas-1)/elas))-((alpha*ref.dmd)^((elas-1)/elas)))
                      ][, `:=` (ref.dmd = NULL, ref.price = NULL, ref.eff = NULL, elas = NULL)]

              # merge demand with survival rates
              temp0 = inner_join(temp0, dt.surv)
              setorderv(temp0, c("year", "end.use", "dvc.cls", "dvc.opt", "vint"))

              # assign equation and variable numbers
              temp0[, const.num := .GRP, by = .(year, end.use, dvc.cls)
                    ][, var.num := .GRP, by = .(end.use, dvc.cls, dvc.opt, vint)]

              # sum electricity expenditures and consumer surplus across time slices
              temp = temp0[, .(exp = sum((price/eff)*dmd), cons.surp = sum(cons.surp)),
                           by = .(ba, inc.lvl, year, end.use, dvc.cls, dvc.opt, vint,
                                  const.num, var.num, disc.rate, cap.cost, surv.rate,
                                  exp.life)]

              # remove extraneous columns
              temp0[, price := NULL]

              # set order
              temp = temp[order(const.num, var.num)]

              # extract dense constraint matrix
              const.mat = as.matrix(temp[, .(const.num, var.num, surv.rate)])

              # assign capital costs to rows where vintage = year
              temp[, cap.cost := ifelse(vint == year, cap.cost, 0)]

              # calculate end of horizon correction factor based on discount rate and expected device lifetime
              # conditional on survival until 2050
              temp[, eoh.fctr := ifelse(exp.life > 0, (1-(1/(1+disc.rate))^(exp.life-(year-vint)))/(1-(1/(1+disc.rate))), 1)]

              # calculate total lifetime value for each device vintage
              temp = temp[, .(value = sum((1/(1+disc.rate))^(year-2010)*(cap.cost+eoh.fctr*surv.rate*(exp-cons.surp)))),
                          by = .(ba, inc.lvl, end.use, dvc.cls, dvc.opt, vint, var.num)]

              # extract objective function vector
              obj.vec = temp[, .(value)][[1]]

              # create constraint direction vector
              const.dir = rep("=", max(const.mat[, 1]))

              # solve program
              results = lp(direction = "min", objective.in = obj.vec, const.dir = const.dir,
                           const.rhs = const.rhs, dense.const = const.mat)$solution

              # add results to variable identifier matrix
              temp = cbind(data.table(var.num = seq(1, max(const.mat[, 2]))), data.table(dvc.purch = results))

              # merge into larger consumption table
              temp = inner_join(temp0, temp)

              # calculate number of devices purchased in every year
              result1 = temp[time.slice == "h1" & vint == year,
                             .(inc.lvl, ba, year, end.use, dvc.cls, dvc.opt, 
                               param = "dvc.purch", value = dvc.purch)]

              # calculate stock of each type of device in every year
              result2 = temp[time.slice == "h1", .(param = "dvc.stock",
                                                   value = sum(surv.rate*dvc.purch)),
                             by = .(inc.lvl, ba, year, end.use, dvc.cls, dvc.opt)]
              
              result = rbind(result1, result2)

              return(result)
              }

} else  {

  print('Invalid value for conversion status 1')
  #stop('Invalid value for conversion status 1')

}
})

# close workers to save memory
stopImplicitCluster()

####################################################################
################### EXPORT RESULTS AS A GDX FILE ###################
####################################################################

#---------------------------
#

if (conv.stat == 0) {
  
  # convert output list to data table
  new.dmd = setDT(do.call(rbind.data.frame, new.dmd))

  if (output.lvl == 'Default'){
    
    # sum over income levels
    new.dmd = new.dmd[, .(elec.cons = sum(elec.cons)), by = .(ba, year, time.slice)]
    
    # format for GDX writing
    new.dmd[, `:=` (ba = as.factor(paste("p", as.character(ba), sep = "")),
                    time.slice = as.factor(paste("h", as.character(time.slice), sep = "")),
                    year = as.factor(year))]
    
    attr(new.dmd,"symName") <- "ResDmdNew"
    
    # write new demand quantities to GDX
    print("Operations completed successfully 1")
    wgdx.lst(gdxout, new.dmd)
    
  } else if (output.lvl == 'use'){
    
    # sum over income levels
    new.dmd = new.dmd[, .(elec.cons = sum(elec.cons)), by = .(ba, year, time.slice, end.use)]
    
    # format for GDX writing
    new.dmd[, `:=` (ba = as.factor(paste("p", as.character(ba), sep = "")),
                    time.slice = as.factor(paste("h", as.character(time.slice), sep = "")),
                    year = as.factor(year),
                    end.use = as.factor(end.use))]
    
    attr(new.dmd,"symName") <- "ResDmdNew"
    
    # write new demand quantities to GDX
    print("Operations completed successfully 2")
    wgdx.lst(gdxout, new.dmd)
    
  } else {
    
    stop ('Choose a valid output level parameter')
    
  }

} else if (conv.stat == 1){

  # convert output list to data table
  outputs = setDT(do.call(rbind.data.frame, outputs))
  setorderv(outputs, c("param", "ba", "inc.lvl", "year", "end.use", "dvc.cls", "dvc.opt"))

  outputs[, `:=` (inc.lvl = as.factor(paste("i", as.character(inc.lvl),sep="")),
                 ba = as.factor(paste("p", as.character(ba), sep = "")),
                 year = as.factor(year), param = as.factor(param)
                 )]
  # write outputs to CSV
  fwrite(outputs, "outputs/data/dmd_outputs.csv")

} else  {
  print('Invalid value for conversion status 2')
  #stop('Invalid value for conversion status 2')

}
})