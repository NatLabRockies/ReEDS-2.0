# Residential demand data processing for ReEDS 2.0
# Initially written 2017-09-25
# Dave Bielen
# NREL

######################################################
#################### PRELIMINARY #####################
######################################################

#---------------------------
# Set working directory

setwd('F:/ReEDS_DBielen')
rm(list=ls())

#---------------------------
# Load packages

library(doBy)
library(ggplot2)
library(reshape2)
library(ggthemes)
library(plyr)
library(RColorBrewer)
library(scales)
library(reshape2)
library(gdata)
library(grid)
library(gdxrrw)
library(gtools)
library(dtplyr)
library(dplyr)
library(xtable)
library(data.table)
library(zoo)
library(openxlsx)
# igdx("C:/gams/win64/24.5")

#---------------------------
# Set package options

options(xtable.floating = FALSE)
options(xtable.timestamp = "")


###############################################
################### OPTIONS ###################
###############################################

#---------------------------
# Switches

#---------------------------
# Data options

#---------------------------
# Parameters and vectors

# watt-hour to btu conversion
wh2btu = 3.41214

# Baseline Weibull distribution parameters for lighting
# (note: derived using NEMS's assumed distribution across hour-of-use bins
# for GSL)

# Scale parameter for light-bulbs for a lifetime of 1 hour 
# (note: gets multiplied by hourly lifetime for technology options)
scale.lgt = 0.00277384

# shape parameter for all light-bulbs
shape.lgt = 1.74169

# Assumed lumens per hour per bulb (comes from baseline incandescent in NEMS)
lumens.base = 840

#---------------------------
# Functions

CJ.table <- function(X,Y)
  setkey(X[,c(k=1,.SD)],k)[Y[,c(k=1,.SD)],allow.cartesian=TRUE][,k:=NULL]


###########################################################
################### LOAD MAPPING TABLES ###################
###########################################################

#---------------------------
# Import set vectors and mapping tables

# map counties, BAs, counties, states, and Census divisions
geo.map = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/Mapping sets.xlsx", 
                                  "Geographic aggregation", colNames = T))

# convert FIPS codes to character format
geo.map[, cnty.fips := sprintf("%03d", cnty.fips)]
geo.map[, state.fips := sprintf("%02d", state.fips)]

# map American Community Survey income classes to ReEDS income classes
income.map = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/Mapping sets.xlsx", 
                                     "Income aggregation", colNames = T))

# map device names to device classes to end uses and fuels and efficiency units (all NEMS)
dvc.map = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/Mapping sets.xlsx", 
                                  "Residential device aggregation", colNames = T))

# map NEMS end uses to end uses for the electrification study (eventually DSGrid) and ReEDS
use.map = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/Mapping sets.xlsx", 
                                  "Residential end-use aggregation", colNames = T))

# map hours to time slices
time.map = as.data.table(read.csv("//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/time-map.csv", 
                                  header = T))

#---------------------------
# EIA mapping sets
# (note: these tables are needed to standardize across EIA and OnLocation data sources. The EIA
# data tend to use names, while the OnLocation data use codes.)

# end use mappings
eia.use.map = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/EIA mapping sets.xlsx", 
                                      "end uses", colNames = T))

# Census division mappings
eia.cens.div.map = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/EIA mapping sets.xlsx", 
                                           "Census divisions", colNames = T))

# building type mappings
eia.bldg.type.map = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/EIA mapping sets.xlsx", 
                                            "Residential building types", colNames = T))

# fuel type mappings
eia.fuel.map = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/EIA mapping sets.xlsx", 
                                       "fuels", colNames = T))

###############################################################
################### LOAD NEMS SCENARIO DATA ###################
###############################################################

#---------------------------
# Energy consumption
# (note: this data comes from EIA. The OnLocation data was flawed.)

# load data (contains energy consumption and device levels)
nems.energy.cons = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/EIA NEMS Residential.xlsx", 
                                          "Energy consumption", colNames = T, startRow = 1))

# follow naming convention
setnames(nems.energy.cons, c("ENDUSE", "CDIV", "BLDG", "FUEL",
                            "EQPCLASS", "YEAR", "Total"), 
         c("eia.use.set", "cens.div.comb", "bldg.type.name", "fuel.name", 
           "nems.dev.class", "nems.year", "energy.cons"))

# adjust furnace fan device name
nems.energy.cons[nems.dev.class == "FurnaceFans", nems.dev.class := "FF"]

# merge with EIA mappings
nems.energy.cons = join(nems.energy.cons, eia.use.map)
nems.energy.cons = join(nems.energy.cons, eia.cens.div.map)
nems.energy.cons = join(nems.energy.cons, eia.bldg.type.map)
nems.energy.cons = join(nems.energy.cons, eia.fuel.map)

# extract subset of columns
nems.energy.cons = nems.energy.cons[, .(nems.use.set, cens.div.num, bldg.type, nems.fuel.set,
                                        nems.dev.class, nems.year, energy.cons)]

# aggregate consumption for MELs, PCs, and TVs
nems.energy.cons = nems.energy.cons[, .(energy.cons = sum(energy.cons)), 
                                    by =  .(nems.use.set, cens.div.num, bldg.type, nems.fuel.set,
                                            nems.dev.class, nems.year)]

#---------------------------
# Distributed generation
# (note: this data includes DG used for own use. Sales to the grid have been netted out.)

# load data
nems.dg.cons = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/NEMS residential - v2.xlsx", "DG",
                                       colNames = T, startRow = 1))

# follow naming convention
setnames(nems.dg.cons, c("Tech", "Year", "Division", "own.use"), 
         c("nems.tech", "nems.year", "cens.div.num", "dg.cons"))

# convert consumption to million btus
nems.dg.cons[, dg.cons := dg.cons*1e6]

#---------------------------
# Equipment stock
# (note: data from OnLocation.)

# load data (contains energy consumption and device levels)
nems.equip.stock = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/EIA NEMS Residential.xlsx", 
                                           "Equipment stock", colNames = T, startRow = 1))

# follow naming convention
setnames(nems.equip.stock, c("ENDUSE", "CDIV", "BLDG", "FUEL",
                             "EQPCLASS", "YEAR", "Total"), 
         c("eia.use.set", "cens.div.comb", "bldg.type.name", "fuel.name", 
           "nems.dev.class", "nems.year", "total.dev"))

# adjust furnace fan device name
nems.equip.stock[nems.dev.class == "FurnaceFans", nems.dev.class := "FF"]

# merge with EIA mappings
nems.equip.stock = join(nems.equip.stock, eia.use.map)
nems.equip.stock = join(nems.equip.stock, eia.cens.div.map)
nems.equip.stock = join(nems.equip.stock, eia.bldg.type.map)
nems.equip.stock = join(nems.equip.stock, eia.fuel.map)

# extract subset of columns
nems.equip.stock = nems.equip.stock[, .(nems.use.set, cens.div.num, bldg.type, nems.fuel.set,
                                        nems.dev.class, nems.year, total.dev)]

# aggregate consumption for MELs, PCs, and TVs
nems.equip.stock = nems.equip.stock[, .(total.dev = sum(total.dev)), 
                                    by =  .(nems.use.set, cens.div.num, bldg.type, nems.fuel.set,
                                            nems.dev.class, nems.year)]

#---------------------------
# Average efficiencies for total stock

# load data
nems.avg.eff = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/NEMS residential - v2.xlsx", 
                                       "Average Efficiencies", colNames = T, startRow = 3))

# follow naming convention
setnames(nems.avg.eff, c("END.USE", "CDIV", "BLDG", "FUEL",
                         "EQPCLASS", "YEAR", "EXEFF"), 
         c("nems.use.set.alt", "cens.div.num", "bldg.type", "nems.fuel.set", 
           "nems.dev.class", "nems.year", "avg.eff.val"))

# remove white space
nems.avg.eff[, nems.use.set.alt := trimws(nems.use.set.alt)]
nems.avg.eff[, nems.dev.class := trimws(nems.dev.class)]

#---------------------------
# Efficiency levels of remaining base-year stock
# (note: these are constant over all years)

# load data
nems.base.eff = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/NEMS residential - v2.xlsx",
                                        "Eff levels of remaining stock", colNames = F, startRow = 5))

# follow naming convention
setnames(nems.base.eff, c("X1", "X2"), c("nems.class.name", "base.eff.val"))

#---------------------------
# Retirement fractions of base-year stock
# (note: does not include lighting)

nems.rtr.frac = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/NEMS residential - v2.xlsx", 
                                        "Retirement fraction", colNames = T, startRow = 3))

# follow naming convention
setnames(nems.rtr.frac, c("Class"), c("nems.class.name"))

# add 2009 column
nems.rtr.frac[, `2009` := 0]

# add Census divisions
nems.rtr.frac = CJ.table(nems.rtr.frac, data.table(cens.div.num = 1:9))

#---------------------------
# Base-year shares and lifetimes for lighting
# (note: shares and lifetimes are from NEMS. This table is used to create annual
# retirement fractions for lighting.)

nems.base.lgt.data = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/Parameters.xlsx",
                                             "Initial lighting shares", colNames = T, startRow = 1))

#---------------------------
# Survival rate parameters
# (note: )

nems.weibull = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/NEMS residential - v2.xlsx", 
                                       "Survival Rate", colNames = T, startRow = 7))

# follow naming convention
setnames(nems.weibull, c("RTCLNAME", "RTK(I)", "RTLAMBDA(I)"), c("nems.dev.class", "shape", "scale"))

# remove unwanted quotes
nems.weibull[, nems.dev.class := gsub("'", "", nems.dev.class)]

#---------------------------
# Technology options
# (notes: (1) there are issues with the native NEMS technology options sheet.
#         (2) lighting needs to be loaded separately.)

# load main data
nems.tech.opt = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/NEMS residential - v2.xlsx", 
                                        "Technology Options", colNames = T, startRow = 6))

# follow naming convention
setnames(nems.tech.opt, c("X1", "RTTYEQCL", "RTINITYR", "RTLASTYR", "RTCENDIV", 
                          "RTEQEFF", "RTEQCOST", "RTTYNAME"), 
         c("nems.use.num", "nems.class.num", "nems.first.yr", "nems.last.yr", 
           "cens.div.num", "eff.val", "cap.cost", "nems.type.name"))

# remove unwanted quotes
nems.tech.opt[, nems.type.name := gsub("'", "", nems.type.name)]

# remove unwanted columns
# (note: can add back in as needed --- e.g., subsidies, pointers, etc.)
nems.tech.opt = nems.tech.opt[, .(nems.use.num, nems.class.num, nems.first.yr, nems.last.yr,
                                  cens.div.num, eff.val, cap.cost, nems.type.name)]

# remove double-counted devices
# (note: WTF, NEMS?)
nems.tech.opt = nems.tech.opt[!(nems.type.name == "CT_AIR#2" & nems.last.yr == 2013 & 
                                eff.val == 3.96)]

# load lighting data
nems.lgt.opt = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/Other technology options.xlsx", 
                                       "Lighting - options only", colNames = T))

# follow naming convention
setnames(nems.lgt.opt, c("FirstYear", "LastYear", "Cost", "Lumens/Watt", "Life(hrs)", 
                          "Application", "BulbType"), 
         c("nems.first.yr", "nems.last.yr", "cap.cost", "eff.val", "lifetime", 
           "nems.dev.class", "nems.type.name"))

# remove unwanted columns
# (note: can add back in as needed --- e.g., subsidies, pointers, etc.)
nems.lgt.opt = nems.lgt.opt[, .(nems.first.yr, nems.last.yr, cap.cost, eff.val,
                                lifetime, nems.dev.class, nems.type.name)]

# load minor end-use data
nems.minor.opt = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/Other technology options.xlsx", 
                                         "Minor end-uses", colNames = T))

# add Census divisions
nems.minor.opt = CJ.table(nems.minor.opt, data.table(cens.div.num = 1:9))

# load base year device info
# (note: this is artificial, but helps unify the parameters for GAMS)
nems.base.opt = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/Other technology options.xlsx", 
                                        "Base-year devices", colNames = T))

# add Census divisions
nems.base.opt = CJ.table(nems.base.opt, data.table(cens.div.num = 1:9))

############################################################################
################### LOAD DEMOGRAPHIC AND LOAD SHAPE DATA ###################
############################################################################

# This data allows us to disaggregate the coarse data from NEMS along spatial and
# and temporal dimensions. It also allows us to disaggregate the data across
# income classes.

#---------------------------
# Demographic data

# households per county
hshld = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/County demographics.xlsx", 
                                "Households", colNames = F, startRow = 6))

# adjust names
setnames(hshld, c("X1", "X2", "X3"), c("cnty.st", "mkt.key", "hshld.cnty"))

# remove "CNTY" prefix
hshld[, mkt.key := gsub("CNTY", "", mkt.key)]

# income distributions
inc.dist = as.data.table(read.xlsx("ReEDS-2.0/inputs/demand/raw data/County demographics.xlsx", 
                                   "Income distribution", colNames = F, startRow = 6))

# adjust names
setnames(inc.dist, sprintf("X%s", seq(1,14)), c(c("cnty.st", "mkt.key"), 
                                                sprintf("i%s", seq(1,12))))

# convert to long format
inc.dist = melt(inc.dist, id.vars = c("cnty.st", "mkt.key"),
                variable.name = "inc.lvl", value.name = "hshld.inc.cnty",
                variable.factor = F)

# remove income level prefix, split fips code into state and county components
inc.dist = inc.dist[, .(state.fips = substr(mkt.key, 5, 6), cnty.fips = substr(mkt.key, 7, 9),
                        inc.lvl, hshld.inc.cnty)]

# remove counties without data (just Oglala Lakota, SD)
inc.dist = inc.dist[!(state.fips == "46" & cnty.fips == "102")]

#---------------------------
# Load shape data
# (note: this data comes from the EPSA electrification study.)

# hourly residential load shapes by end-use
load.shapes = as.data.table(read.csv("ReEDS-2.0/inputs/demand/raw data/Residential load shapes.csv", 
                                     header = T))

################################################################
################### ADJUSTMENTS FOR LIGHTING ###################
################################################################

#---------------------------
# Calculate base stock retirement fractions

# calculate Weibull parameters
nems.base.lgt.data[, scale := scale.lgt*lifetime][, shape := shape.lgt]

# expand by number of years
nems.base.lgt.surv = CJ.table(nems.base.lgt.data, 
                              data.table(nems.year = 2010:2050))

# calculate retirement fractions for each technology
nems.base.lgt.surv[, rtr.frac := pweibull(nems.year - 2009,
                                          shape = shape, scale = scale)]

# convert to wide format
nems.lgt.rtr.frac = dcast(nems.base.lgt.surv[, .(nems.class.name, nems.type.name, nems.use.num, 
                                                 nems.class.num, nems.year, rtr.frac)], 
                          nems.class.name + nems.type.name + nems.use.num + nems.class.num ~ nems.year, 
                          value.var = c("rtr.frac"))

# add 2009 column
nems.lgt.rtr.frac[, `2009` := 0]

# add Census divisions
nems.lgt.rtr.frac = CJ.table(nems.lgt.rtr.frac, data.table(cens.div.num = 1:9))

#---------------------------
# Adjust average and base efficiencies (watts to lumens per watt)
# (note: we might be able to do better than this with the EIA data)

# calculate base wattage level
nems.base.lgt.eff = nems.base.lgt.data[, .(base.eff.val = sum(share*base.eff.val)),
                                       by = nems.class.name]

# merge base lighting efficiency with main base efficiency table
nems.base.eff = full_join(nems.base.eff, nems.base.lgt.eff)

# calculate lumens per watt assuming the lumen level of the baseline incandescent bulb
nems.avg.eff[nems.use.set.alt == "LIGHTING" & nems.dev.class == "GSL", 
             avg.eff.val := 840/avg.eff.val
             ][nems.use.set.alt == "LIGHTING" & nems.dev.class == "REF", 
               avg.eff.val := 650/avg.eff.val
               ][nems.use.set.alt == "LIGHTING" & nems.dev.class == "LFL", 
                 avg.eff.val := 2880/avg.eff.val
                 ][nems.use.set.alt == "LIGHTING" & nems.dev.class == "EXT", 
                   avg.eff.val := 1040/avg.eff.val]

#---------------------------
# Fill in data for lighting options to match main technology options table

# assign use number (note: this doesn't exist in NEMS)
nems.lgt.opt[, nems.use.num := 10]

# assign class numbers (note: this doesn't exist in NEMS)
nems.lgt.opt[nems.dev.class == "GSL", nems.class.num := 1]
nems.lgt.opt[nems.dev.class == "REF", nems.class.num := 2]
nems.lgt.opt[nems.dev.class == "EXT", nems.class.num := 3]
nems.lgt.opt[nems.dev.class == "LFL", nems.class.num := 4]

# expand by Census divisions
nems.lgt.opt = CJ.table(nems.lgt.opt, data.table(cens.div.num = 1:9))

# remove columns that would complicate merge with main tech options table
# (note: the only column retained here that is not in the main file is lifetime)
nems.lgt.opt = nems.lgt.opt[, .(nems.use.num, nems.class.num, nems.first.yr, nems.last.yr,
                                cens.div.num, eff.val, cap.cost, lifetime, nems.type.name)]

##########################################################
################### MERGE MAPPING SETS ###################
##########################################################

#---------------------------
# Device aggregation (NEMS) and end-use aggregation (NEMS and ReEDS)

dvc.use.map = join(use.map, dvc.map)

###########################################################
################### MERGE RAW NEMS DATA ###################
###########################################################

#---------------------------
# Average efficiencies and device map (both NEMS)

nems.avg.eff = join(nems.avg.eff, 
                    dvc.use.map[, .(nems.use.set.alt, nems.use.num, nems.dev.class, 
                                    nems.class.num, eff.units, serv.units)])

#---------------------------
# Base efficiencies and device map (both NEMS)

nems.base.eff = full_join(nems.base.eff, 
                          dvc.use.map[, .(nems.use.num, nems.class.name, nems.class.num, reeds.dev.class, 
                                          nems.fuel.set, serv.units, model.ind)])

# assign base efficiencies for minor end-use devices
nems.base.eff[model.ind == 0, base.eff.val := 1]

# remove non-modeled electric equipment classes
nems.base.eff = nems.base.eff[!(nems.fuel.set == "EL" & is.na(reeds.dev.class))]

#---------------------------
# Energy consumption and device map (both NEMS)

nems.energy.cons = join(nems.energy.cons, dvc.use.map[, .(nems.use.set, nems.use.num, reeds.use.set, nems.dev.class, nems.class.num, reeds.dev.class, nems.fuel.set, serv.units)])

#---------------------------
# Equipment stock and device map (both NEMS)

nems.equip.stock = join(nems.equip.stock, 
                        dvc.use.map[, .(nems.use.set, nems.use.num, reeds.use.set, 
                                        nems.dev.class, nems.class.num, reeds.dev.class)])

#---------------------------
# Retirement fractions and device map

# merge with device map
nems.rtr.frac = join(nems.rtr.frac, dvc.use.map[, .(nems.class.name, nems.use.num, nems.class.num)])

# merge with base options
# (note: this deletes non-electric device classes)
nems.rtr.frac = inner_join(nems.rtr.frac[, nems.class.name := NULL], 
                           nems.base.opt[, .(nems.use.num, nems.class.num, nems.type.name, cens.div.num)])

# merge with main retirement fraction table with lighting table
nems.rtr.frac = merge(nems.rtr.frac, nems.lgt.rtr.frac[, nems.class.name := NULL],
                      by = intersect(names(nems.rtr.frac), names(nems.lgt.rtr.frac)),
                      all = T)

#---------------------------
# Technology options

# merge lighting with main options table
nems.tech.opt = full_join(nems.tech.opt, nems.lgt.opt)

# merge minor end-uses with main options table
nems.tech.opt = full_join(nems.tech.opt, nems.minor.opt)

# define device type vintage (new or base)
nems.tech.opt[, dvc.type.vint := "new"]
# new.dvc.vec = unique(nems.tech.opt[, .(nems.type.name)])

# merge with base device table, assign vintage
nems.tech.opt = full_join(nems.tech.opt, nems.base.opt)
nems.tech.opt[is.na(dvc.type.vint), dvc.type.vint := "base"]

# merge with device map
nems.tech.opt = join(nems.tech.opt, 
                     dvc.use.map[, .(nems.use.set, reeds.use.set, nems.use.num, nems.dev.class, 
                                     nems.class.num, reeds.dev.class, nems.fuel.set, serv.units, 
                                     model.ind)])

# base efficiencies
nems.tech.opt = left_join(nems.tech.opt, nems.base.eff[, .(nems.use.num, nems.class.num, base.eff.val)])

# assign base-year device with base efficiency
nems.tech.opt[eff.val == -1, eff.val := base.eff.val]

# Weibull parameters
nems.tech.opt = left_join(nems.tech.opt, nems.weibull)

# Merge in lifetimes and efficiencies for base lighting devices
nems.tech.opt = left_join(nems.tech.opt, nems.base.lgt.data[, .(nems.class.num, nems.type.name, temp1 = lifetime, temp2 = base.eff.val)])

# assign lifetimes for base lighting, remove temporary column
nems.tech.opt[nems.use.set == "LT" & dvc.type.vint == "base", lifetime := temp1
              ][nems.use.set == "LT" & dvc.type.vint == "base", eff.val := temp2
                ][, c("temp1", "temp2") := NULL]

# calculate Weibull parameters for lighting
nems.tech.opt[nems.use.set == "LT", scale := scale.lgt*lifetime
              ][nems.use.set == "LT", shape := shape.lgt]

# assign arbitrary Weibull parameters for minor end-uses
# (note: the current values will phase out the entire stock each year)
nems.tech.opt[model.ind == 0, scale := .9
              ][model.ind == 0, shape := 100]

########################################################################################
################### MERGE AND ADJUST DEMOGRAPHIC AND LOAD SHAPE DATA ###################
########################################################################################

#---------------------------
# Income distributions over BAs and income classes

# merge with geographic data
inc.dist = join(inc.dist, geo.map[, .(state.fips, cnty.fips, reeds.ba, cens.div.num)])

# sum to BA level
inc.dist = inc.dist[, .(hshld.inc.ba = sum(hshld.inc.cnty)), 
                    by = .(reeds.ba, cens.div.num, inc.lvl)]

# create column with Census division sums
inc.dist[, hshld.div := sum(hshld.inc.ba), by = .(cens.div.num)]

# calculate proportions of each BA/income bin within each Census division
# (note: this can be used directly to disaggregate device numbers from Census divisions
# to BAs/income classes)
inc.dist = inc.dist[, .(reeds.ba, cens.div.num, inc.lvl,
                        hshld.prop.inc.ba = hshld.inc.ba/hshld.div)]

#---------------------------
# Load shapes by end-use

# merge with geographic mapping table
# (note: need to use unique function to map states to BAs many-to-one. Otherwise, counties are included
# and merge is many-to-many.)
load.shapes = left_join(load.shapes, unique(geo.map[, .(state.abb, reeds.ba, cens.div.num)]))

# merge with time slice mapping table
load.shapes = left_join(load.shapes[, state.abb := NULL], time.map)

# convert to long format over end-use shapes
load.shapes = melt(load.shapes, 
                   id.vars = c("reeds.ba", "cens.div.num", "nems.year", "HourID", "time.slice"),
                   variable.name = "elec.use.set", value.name = "load.prop.hr.use",
                   variable.factor = F)

# sum hourly proportions up to time slice proportions
load.shapes = load.shapes[, .(load.prop.ts.use = sum(load.prop.hr.use)), 
                          by = .(reeds.ba, cens.div.num, nems.year, time.slice, elec.use.set)]

#---------------------------
# Load shapes by ReEDS end-use

# map load shapes from electrification end-uses into ReEDS end-uses
load.shapes = left_join(load.shapes, use.map[, .(elec.use.set, reeds.use.set)])

# merge load shape and income distribution tables
load.shapes = left_join(load.shapes, inc.dist)

# calculate load proportions over income classes, BAs, and time slices
load.shapes = load.shapes[, .(reeds.ba, cens.div.num, inc.lvl, nems.year, time.slice, 
                              reeds.use.set, load.prop = load.prop.ts.use*hshld.prop.inc.ba)]

##########################################################################################
################### ADJUST/DECOMPOSE ENERGY CONSUMPTION AND STOCK DATA ###################
##########################################################################################

#---------------------------
# Format and apply distribution generation consumption totals

# shift DG data from long to wide format (solar versus other)
nems.dg.cons = dcast(nems.dg.cons, nems.year + cens.div.num ~ nems.tech,
                     value.var = c("dg.cons"))

# rename columns
setnames(nems.dg.cons, c("Other", "Solar_PV"), c("other.dg.cons", "solar.dg.cons"))

# merge data
nems.energy.cons = join(nems.energy.cons, nems.dg.cons)

# apply DG consumption values for single family homes (central AC and MELs)
nems.energy.cons[bldg.type == "1" & nems.dev.class == "CENT_AIR", 
                 energy.cons := energy.cons + 0.35*solar.dg.cons
                 ][bldg.type == "1" & nems.dev.class == "MEL", 
                   energy.cons := energy.cons + other.dg.cons + 0.65*solar.dg.cons]

nems.energy.cons[, c("other.dg.cons", "solar.dg.cons") := NULL]

#---------------------------
# Subset energy consumption and stock data

# subset out non-electric equipment classes
nems.energy.cons = nems.energy.cons[nems.fuel.set == "EL"]
nems.equip.stock = nems.equip.stock[nems.fuel.set == "EL"]

#---------------------------
# Aggregate miscellaneous electric loads

# calculate an aggregate end-use consumption level
nems.energy.cons[, energy.cons.use := sum(energy.cons), 
                 by = .(cens.div.num, bldg.type, nems.year, nems.use.set)]

# remove TVs and PCs
nems.equip.stock = nems.equip.stock[!(nems.dev.class %in% c("TV&R", "PC&R"))]
nems.energy.cons = nems.energy.cons[!(nems.dev.class %in% c("TV&R", "PC&R"))]

# apply total end-use consumption levels for MELs
nems.energy.cons[nems.dev.class == "MEL", energy.cons := energy.cons.use]

################################################################
################### PERFORM UNIT CONVERSIONS ###################
################################################################

#---------------------------
# Energy consumption

# MMbtu to btu
# nems.energy.cons[, energy.cons := 1e6*energy.cons]

#---------------------------
# Efficiency levels

# full stock
# btu out/wh in to btu out/btu in
nems.avg.eff[eff.units %in% c("HSPF", "SEER", "EER"), 
             avg.eff.val := avg.eff.val/wh2btu]
# lumens/w to lumens/btu
nems.avg.eff[eff.units %in% c("watts"), 
             avg.eff.val := avg.eff.val/(wh2btu*8760)]
# kwh/yr or kwh/cycle to btu/yr or btu/cycle
nems.avg.eff[serv.units %in% c("cycles", "generic"),
             avg.eff.val := 1e3*avg.eff.val*wh2btu]

# base stock
# kwh/yr or kwh/cycle to btu
nems.base.eff[serv.units %in% c("lumens"), 
              base.eff.val := base.eff.val/(wh2btu*8760)]
nems.base.eff[serv.units %in% c("cycles", "generic"),
              base.eff.val := 1e3*base.eff.val*wh2btu]

# technology options
# (lumens per watt to lumens per btu)
nems.tech.opt[serv.units %in% c("lumens"), 
              eff.val := eff.val/(wh2btu*8760)]

# adjust solar water heating
# (note: this is based on the NEMS assumption that half of solar water heater 
# consumption is provided by backup electricity)
nems.avg.eff[nems.dev.class == "SOLAR_WH", avg.eff.val := 2*avg.eff.val]
nems.base.eff[nems.class.name == "Solar Water Heaters", base.eff.val := 2*base.eff.val]
nems.tech.opt[nems.dev.class == "SOLAR_WH", eff.val := 2*eff.val
              ][nems.dev.class == "SOLAR_WH", base.eff.val := 2*base.eff.val]

##################################################################
################### CONSTRUCT BASE STOCK TABLE ###################
##################################################################

# This will create a data table to track device the evolution of the base device
# stock over time. The indices for this table are income class, BA, year, end-use,
# device class, and efficiency. The device class and efficiency indices are one-to-one,
# except for lighting. This could change in the future with more resolved data.

#---------------------------
# Extract and prepare base stock data

# extract NEMS base stock from total device stock table
nems.base.stock = nems.equip.stock[nems.year == 2009, 
                                   .(cens.div.num, bldg.type, nems.use.num, reeds.use.set, nems.dev.class, 
                                     nems.class.num, reeds.dev.class, total.dev)]

# merge in base efficiency device name
# (note: this expands the lighting categories into different base efficiencies)
nems.base.stock = left_join(nems.base.stock, 
                            nems.base.opt[, .(cens.div.num, nems.use.num, nems.class.num, nems.type.name)])

# merge in shares for lighting
nems.base.stock = join(nems.base.stock, 
                       nems.base.lgt.data[, .(nems.use.num, nems.class.num, nems.type.name, share)])

# recalculate number of lighting devices to account for shares
nems.base.stock[nems.use.num == 10, total.dev := total.dev*share]

#---------------------------
# Calculate evolution of base stock

# merge stock data with retirement fractions
nems.base.stock = join(nems.base.stock, nems.rtr.frac)

# convert to long format
nems.base.stock = melt(nems.base.stock[, share := NULL], 
                       id.vars = c("cens.div.num", "bldg.type", "nems.use.num", "reeds.use.set", "nems.dev.class", 
                                   "nems.class.num", "reeds.dev.class", "nems.type.name", "total.dev"), 
                       variable.name = "nems.year", value.name = "rtr.frac",
                       variable.factor = F)

# convert data storage type
nems.base.stock[, nems.year := as.numeric(nems.year)]

# apply full first-year phaseout for non-modeled end-uses
nems.base.stock[nems.use.num > 10 & nems.year == 2009, rtr.frac := 0]
nems.base.stock[nems.use.num > 10 & nems.year > 2009, rtr.frac := 1]

# apply retirement fractions to determine number of remaining base stock devices
nems.base.stock[, rem.stock := total.dev*(1-rtr.frac)]

#---------------------------
# Disaggregate base stock into income classes and BAs

# aggregate over building types
nems.base.stock = nems.base.stock[, .(rem.stock = sum(rem.stock)),
                                  by = .(cens.div.num, nems.year, reeds.use.set, 
                                         reeds.dev.class, nems.type.name)]

# merge in income distribution data table
nems.base.stock = full_join(nems.base.stock, inc.dist)

# apply income/BA proportions to remaining stock
nems.base.stock[, rem.stock := rem.stock*hshld.prop.inc.ba]

#---------------------------
# Make final preparations for GAMS formatting

# 
nems.base.stock = nems.base.stock[nems.year > 2009, .(inc.lvl, reeds.ba = paste("p", reeds.ba, sep = ""), 
                                                      nems.year, reeds.use.set, reeds.dev.class, 
                                                      nems.type.name, rem.stock)]

#---------------------------
# Export final data
# (note: this should be commented out if it's not being used as it takes a long time)

write.table(nems.base.stock,
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/base-stock-counts.csv",
            sep = ",", row.names = F, col.names = F)

####################################################################
################### CONSTRUCT TOTAL DEVICE TABLE ###################
####################################################################

# This will create a data table to track the evolution of the total number of devices 
# over time. The indices for this table are income class, BA, year, end-use, and
# device class. For some end-uses (e.g., space heating/cooling and water heating),
# GAMS will aggregate over device classes to allow for substitution in the model.

#---------------------------
# Clean and aggregate device table

# aggregate over building types
nems.equip.stock = nems.equip.stock[, .(total.dev = sum(total.dev)),
                                    by = .(cens.div.num, nems.year, reeds.use.set, reeds.dev.class)]

#---------------------------
# Disaggregate base stock into income classes and BAs

# merge in income distribution data table
nems.equip.stock = full_join(nems.equip.stock, inc.dist)

# apply income/BA proportions to remaining stock
nems.equip.stock[, total.dev := total.dev*hshld.prop.inc.ba]

# set total device number to unity for MELs, furnace fans, and secondary heat
nems.equip.stock = nems.equip.stock[reeds.use.set %in% c("MSC", "FUF", "SCH"), total.dev := 1]

#---------------------------
# Remove extraneous columns 

nems.equip.stock = nems.equip.stock[nems.year > 2009, .(inc.lvl, reeds.ba = paste("p", reeds.ba, sep = ""), 
                                                        nems.year, reeds.use.set, reeds.dev.class, total.dev)]

#---------------------------
# Export final data
# (note: this should be commented out if it's not being used as it takes a long time)

write.table(nems.equip.stock,
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/total-device-counts.csv",
            sep = ",", row.names = F, col.names = F)

#################################################################################################
################### CALCULATE AVERAGE EFFICIENCIES AND END-USE SERVICE DEMAND ###################
#################################################################################################

#---------------------------
# Translate energy consumption into service consumption

# Merge energy consumption data with efficiency data
# model year efficiencies (2010-2050)
nems.serv.cons = join(nems.energy.cons, nems.avg.eff[, .(cens.div.num, bldg.type, nems.year, 
                                                         nems.use.num, nems.class.num, avg.eff.val)])

# base year efficiencies (2009)
nems.serv.cons = left_join(nems.serv.cons, nems.base.eff[, .(nems.use.num, nems.class.num, base.eff.val)])

# assign average efficiencies to new efficiency variable
nems.serv.cons[nems.year > 2009, avg.eff.val.new := avg.eff.val]

# assign base year efficiencies to new efficiency variable for 2009
nems.serv.cons[nems.year == 2009, avg.eff.val.new := base.eff.val]

# double solar water heater consumption of electricity
# nems.serv.cons[nems.dev.class == "SOLAR_WH", energy.cons := 2*energy.cons]

# apply relative efficiencies where NEMS does not specify service units but allows
# endogenous choices
# (note: this includes electric cooking, refrigeration, and freezing. We also include
# clothes washing, which technically has service units --- cycles --- but what the hell)
nems.serv.cons[serv.units %in% c("cycles", "generic") & nems.year == 2009, 
               avg.eff.val.new := 1]
nems.serv.cons[serv.units %in% c("cycles", "generic") & nems.year > 2009, 
               avg.eff.val.new := base.eff.val/avg.eff.val]

#### !!!! DELETE WHEN NEW CODE IS VALIDATED !!!! ####
# nems.serv.cons[nems.use.set %in% c("RF", "FZ") & nems.year == 2009, 
#                avg.eff.val.new := 1]
# nems.serv.cons[nems.use.set %in% c("RF", "FZ") & nems.year > 2009, 
#                avg.eff.val.new := avg.eff.val/base.eff.val]
# nems.serv.cons[nems.use.set == "CK" & nems.fuel.set == "EL" & nems.year == 2009, 
#                avg.eff.val.new := 1]
# nems.serv.cons[nems.use.set == "CK" & nems.fuel.set == "EL" & nems.year > 2009, 
#                avg.eff.val.new := avg.eff.val/base.eff.val]
# nems.serv.cons[nems.use.set %in% c("CW") & nems.year == 2009, 
#                avg.eff.val.new := 1]
# nems.serv.cons[nems.use.set %in% c("CW") & nems.year > 2009, 
#                avg.eff.val.new := base.eff.val/avg.eff.val]

# apply baseline NEMS efficiency where NEMS specifies exogenous improvement
# (note: this includes furnace fans, miscellaneous loads, and secondary heating.
# In this category, any changes to efficiency in ReEDS will be relative to the 
# NEMS exogenous trajectory.)
nems.serv.cons[nems.use.set %in% c("Other", "FF", "SH"), avg.eff.val.new := 1]

# calculate service consumption
nems.serv.cons[, serv.cons := energy.cons*avg.eff.val.new]

#### !!!! DELETE WHEN NEW CODE IS VALIDATED !!!! ####
# nems.serv.cons[serv.units %in% c("btu", "lumens"), 
#                serv.cons := energy.cons*avg.eff.val.new]
# nems.serv.cons[serv.units %in% c("cycles", "generic"), 
#                serv.cons := energy.cons/avg.eff.val.new]

#---------------------------
# Disaggregate spatially and temporally

# sum service demand and energy consumption over appropriate categories
# (note: this includes building type (single family, multi-family, manufactured), 
# which we do not model separately. We continue to disaggregate by
# year, census division, and equipment class.)
nems.serv.cons = nems.serv.cons[nems.year > 2009, .(energy.cons = sum(energy.cons), serv.cons = sum(serv.cons)), 
                                by = .(cens.div.num, nems.year, reeds.use.set, reeds.dev.class)]

# calculate reference efficiency levels, adjust for zero consumption
nems.ref.eff = nems.serv.cons[, .(cens.div.num, nems.year, reeds.use.set, reeds.dev.class, 
                                  ref.eff.val = serv.cons/energy.cons)
                              ][is.na(ref.eff.val), ref.eff.val := 1]

# merge service consumption with load shape table
nems.serv.cons = left_join(nems.serv.cons, 
                           load.shapes[, .(inc.lvl, reeds.ba, cens.div.num, nems.year, 
                                           time.slice, reeds.use.set, load.prop)])

# expand efficiencies to all income levels and BAs
nems.ref.eff = left_join(nems.ref.eff, 
                         CJ.table(unique(geo.map[reeds.ba > 0, .(cens.div.num, reeds.ba)]), 
                                  unique(income.map[, .(inc.lvl = reeds.inc.set)])))

# apply load proportions
nems.serv.cons = nems.serv.cons[, .(inc.lvl, reeds.ba = paste("p", reeds.ba, sep = ""), 
                                    nems.year, time.slice, reeds.use.set, 
                                    reeds.dev.class, serv.cons = serv.cons*load.prop)]

# arrange efficiency table
nems.ref.eff = nems.ref.eff[, .(inc.lvl, reeds.ba = paste("p", reeds.ba, sep = ""), 
                                nems.year, reeds.use.set, 
                                reeds.dev.class, ref.eff.val)]

#---------------------------
# Export final data

write.table(nems.serv.cons, 
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/service-cons.csv",
            sep = ",", row.names = F, col.names = F)

write.table(nems.ref.eff, 
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/ref-eff.csv",
            sep = ",", row.names = F, col.names = F)

#################################################################################
################### PREPARE TECHNOLOGY OPTIONS TABLE FOR GAMS ###################
#################################################################################

#---------------------------
# Subset out modeled electric devices
nems.tech.opt = nems.tech.opt[nems.fuel.set == "EL" & !(is.na(reeds.dev.class))]

#---------------------------
# Assign relative efficiencies for devices with generic efficiency units
nems.tech.opt[serv.units  %in% c("cycles", "generic"), eff.val := base.eff.val/eff.val]

#---------------------------
# Expand options table to include all model years

# create a vintage column
nems.tech.opt = CJ.table(nems.tech.opt, data.table(nems.year = 2010:2050))

# remove rows with year outside bounds created by "first year" and "last year" columns
nems.tech.opt = nems.tech.opt[nems.year >= nems.first.yr & nems.year <= nems.last.yr]

#---------------------------
# Fill to all BAs

nems.tech.opt = full_join(nems.tech.opt, unique(geo.map[reeds.ba > 0, .(cens.div.num, reeds.ba)]))

#---------------------------
# Create mapping and subsets

tech.map = unique(nems.tech.opt[, .(reeds.use.set, reeds.dev.class, nems.type.name)])
new.dvc.set = unique(nems.tech.opt[dvc.type.vint == "new", .(nems.type.name)])
base.dvc.set = unique(nems.tech.opt[dvc.type.vint == "base", .(nems.type.name)])

#---------------------------
# Calculate survival rates (new devices only)

# cross-join tech options table with vintage table to create survival rate table
nems.surv.rate = CJ.table(nems.tech.opt[dvc.type.vint == "new", .(reeds.ba = paste("p", reeds.ba, sep = ""), 
                                                                  nems.year, reeds.use.set, reeds.dev.class, 
                                                                  nems.type.name, shape, scale)],
                          data.table(nems.vint = 2010:2050))

# calculate age for each year/vintage pair, remove negative entries
nems.surv.rate = nems.surv.rate[nems.year >= nems.vint]

# apply Weibull parameters to generate survival rate table
nems.surv.rate = nems.surv.rate[, .(reeds.ba, nems.vint, nems.year, reeds.use.set, reeds.dev.class, nems.type.name,
                                    surv.rate = 1-pweibull(nems.year - nems.vint, shape = shape, scale = scale))]

# cut off at less than 0.1%
nems.surv.rate[surv.rate < 0.001, surv.rate := 0]

#---------------------------
# Remove extraneous columns 

nems.tech.opt = nems.tech.opt[, .(reeds.ba = paste("p", reeds.ba, sep = ""), nems.year, reeds.use.set, 
                                  reeds.dev.class, nems.type.name, eff.val, cap.cost, shape, scale)]

#---------------------------
# Export CSVs

# efficiency
write.table(nems.tech.opt[, .(reeds.ba, nems.year, reeds.use.set, reeds.dev.class, nems.type.name, eff.val)],
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/device-efficiency.csv",
            sep = ",", row.names = F, col.names = F)

# cost
write.table(nems.tech.opt[, .(reeds.ba, nems.year, reeds.use.set, reeds.dev.class, nems.type.name, cap.cost)],
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/device-capital-cost.csv",
            sep = ",", row.names = F, col.names = F)

# survival rates
write.table(nems.surv.rate,
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/surv-rates.csv",
            sep = ",", row.names = F, col.names = F)


# Weibull shape
write.table(nems.tech.opt[, .(reeds.ba, nems.year, reeds.use.set, reeds.dev.class, nems.type.name, shape)],
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/weibull-shape.csv",
            sep = ",", row.names = F, col.names = F)

# Weibull scale
write.table(nems.tech.opt[, .(reeds.ba, nems.year, reeds.use.set, reeds.dev.class, nems.type.name, scale)],
            "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/weibull-scale.csv",
            sep = ",", row.names = F, col.names = F)

############################################################
################### EXPORT SETS FOR GAMS ###################
############################################################

#---------------------------
# Native sets

# income set
write.table(income.map[, .(reeds.inc.set)], 
            "ReEDS-2.0/inputs/demand/processed data/income-class-set.csv",
            sep = ",", row.names = F, col.names = F)

# end uses
write.table(unique(tech.map[, .(reeds.use.set)]),
            "ReEDS-2.0/inputs/demand/processed data/end-use-set.csv",
            sep = ",", row.names = F, col.names = F)

# device classes
write.table(unique(tech.map[, .(reeds.dev.class)]),
            "ReEDS-2.0/inputs/demand/processed data/device-class-set.csv",
            sep = ",", row.names = F, col.names = F)

# device options
write.table(unique(tech.map[, .(nems.type.name)]),
            "ReEDS-2.0/inputs/demand/processed data/device-option-set.csv",
            sep = ",", row.names = F, col.names = F)

#---------------------------
# Subsets

write.table(new.dvc.set,
            file = "ReEDS-2.0/inputs/demand/processed data/new-device-set.csv", 
            sep = ",", row.names = F, col.names = F)

write.table(base.dvc.set,
            file = "ReEDS-2.0/inputs/demand/processed data/base-device-set.csv", 
            sep = ",", row.names = F, col.names = F)

#---------------------------
# Mapping sets

# uses -> device classes
write.table(dvc.use.map[!is.na(reeds.dev.class), .(reeds.use.set, reeds.dev.class)], 
            "ReEDS-2.0/inputs/demand/processed data/use-dvc-map.csv", 
            sep = ",", row.names = F, col.names = F)

# uses -> device classes -> efficiencies
write.table(tech.map, 
            "ReEDS-2.0/inputs/demand/processed data/use-dvc-opt-map.csv", 
            sep = ",", row.names = F, col.names = F)

##################################################################
################### EXPORT PARAMETERS FOR GAMS ###################
##################################################################

#---------------------------
# 

# discount rates
write.table(income.map[, .(reeds.inc.set, disc.rate)], 
            "ReEDS-2.0/inputs/demand/processed data/discount-rates.csv",
            sep = ",", row.names = F, col.names = F)



