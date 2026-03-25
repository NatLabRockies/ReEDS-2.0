# Load shape data processing for ReEDS 2.0
# Initially written 2017-11-31
# Dave Bielen
# NREL

###################################################
#################### OVERVIEW #####################
###################################################

# The purpose of this script is to determine the hours that comprise time slice H17, i.e., 
# the top 40 load hours for the year. Currently, ReEDS assumes that these hours occur during
# summer afternoons (H3). The script reads in energy consumption and load shape data for all
# sectors and exports a mapping of hours to time slices for all BAs and model years.

# As of now, this script also creates the commercial and industrial consumption data to be
# imported into ReEDS. This will likely change in the future.

system.time({

######################################################
#################### PRELIMINARY #####################
######################################################

#---------------------------
# Set working directory

if (Sys.getenv('computername') == "1WP11RDORI01") {
  setwd('F:/ReEDS_DBielen/ReEDS-2.0')
} else if (Sys.getenv('computername') == "1WP11RDORI02")  {
  setwd('D:/ReEDS_DBielen/ReEDS-2.0')
} else {
  stop("What is this strange machine you're using?")
}
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
library(grid)
library(gdxrrw)
library(gtools)
library(dtplyr)
library(dplyr)
library(xtable)
library(data.table)
library(zoo)
library(openxlsx)
library(doParallel)
library(iterators)
library(lpSolve)
# igdx("C:/gams/win64/24.5")

#---------------------------
# Set package options

options(xtable.floating = FALSE)
options(xtable.timestamp = "")

#---------------------------
# Register workers

registerDoParallel(10)

###############################################
################### OPTIONS ###################
###############################################

#---------------------------
# Switches

# Does commercial buildings data need to be merged? Yes or no.
com.data.join = "No"

#---------------------------
# Data options

#---------------------------
# Parameters and vectors

mmbtu2mwh = 0.29329722222222

#---------------------------
# Functions

CJ.table <- function(X,Y)
  setkey(X[,c(k=1,.SD)],k)[Y[,c(k=1,.SD)],allow.cartesian=TRUE][,k:=NULL]

###########################################################
################### READ MAPPING TABLES ###################
###########################################################

#---------------------------
# Tables that apply to all sectors

# map counties, BAs, counties, states, and Census divisions
geo.map = setDT(read.xlsx("inputs/demand/raw data/Mapping sets.xlsx", 
                                  "Geographic aggregation", colNames = T))

# convert FIPS codes to character format
geo.map[, cnty.fips := sprintf("%03d", cnty.fips)]
geo.map[, state.fips := sprintf("%02d", state.fips)]

# map hours to time slices
time.map = setDT(read.xlsx("inputs/demand/raw data/Mapping sets.xlsx", 
                                   "Timeslice aggregation", colNames = T))

#---------------------------
# Tables that apply to the residential buildings sector

# map NEMS end uses to end uses for the electrification study (eventually DSGrid) and ReEDS
res.use.map = setDT(read.xlsx("inputs/demand/raw data/Mapping sets.xlsx", 
                                      "Residential end-use aggregation", colNames = T))

#---------------------------
# Tables that apply to the commercial buildings sector

# map NEMS end uses to end uses for the electrification study (eventually DSGrid) and ReEDS
com.use.map = setDT(read.xlsx("inputs/demand/raw data/Mapping sets.xlsx", 
                                      "Commercial end-use aggregation", colNames = T))

#---------------------------
# Tables that apply to the industrial sector

#---------------------------
# EIA mapping sets
# (note: these tables are needed to standardize across EIA and OnLocation data sources. The EIA
# data tend to use names, while the OnLocation data use codes.)

# end use mappings
eia.use.map = setDT(read.xlsx("inputs/demand/raw data/EIA mapping sets.xlsx", 
                                      "end uses", colNames = T))

# Census division mappings
eia.cens.div.map = setDT(read.xlsx("inputs/demand/raw data/EIA mapping sets.xlsx", 
                                           "Census divisions", colNames = T))

# residential building type mappings
eia.res.bldg.type.map = setDT(read.xlsx("inputs/demand/raw data/EIA mapping sets.xlsx", 
                                                "Residential building types", colNames = T))

# commercial building type mappings
eia.com.bldg.type.map = setDT(read.xlsx("inputs/demand/raw data/EIA mapping sets.xlsx", 
                                                "Commercial building types", colNames = T))

# fuel type mappings
eia.fuel.map = setDT(read.xlsx("inputs/demand/raw data/EIA mapping sets.xlsx", 
                                       "fuels", colNames = T))

############################################################
################### READ LOAD SHAPE DATA ###################
############################################################

# This section reads load shape data for each sector. For commercial buildings, it contains an algorithm 
# for reading and merging raw state-by-state .csv files into one main file. A switch is instituted to 
# allow the user to bypass the merge step and directly load the combined data if the merge has already 
# been performed.

#---------------------------
# Residential buildings load shapes

# hourly residential load shapes by end-use
res.load.shapes = setDT(fread("inputs/demand/raw data/Residential load shapes.csv",
                                      header = T))

#---------------------------
# Commercial buildings load shapes

if(com.data.join == "Yes"){
  
  # construct vector of state abbreviations
  state.vec = unique(geo.map[!(state.abb %in% c("AK", "DC", "HI")), .(state.abb)])[[1]]
  
  com.load.shapes <- foreach(i=state.vec, .combine = rbind, .packages = c("data.table")) %do%  {
    # read raw data
    temp = setDT(fread(paste("inputs/demand/raw data/Commercial load shapes/2016-08-08 - Comm Load by End Use - ", i,".csv", 
                                        sep = ""), header = T))
    
    # format table
    temp = temp[, .(state.abb = i, HourID = .I, SPH = heat.ind, SPC = cool.ind, LGT = lght.ind,
                    APP = appl.ind, MSC = misc.ind, WTH = watr.ind)]
  }
  
  # write data to CSV so it can be loaded directly in future runs
  fwrite(com.load.shapes, "inputs/demand/raw data/Commercial load shapes.csv", 
         row.names = F, col.names = T)
  
} else if(com.data.join == "No"){
  
  com.load.shapes = setDT(fread("inputs/demand/raw data/Commercial load shapes.csv", header = T))
  
} else {
  
  stop("Choose a valid value for the commercial buildings data join switch.")
  
}


#---------------------------
# Industrial facilities load shapes

# hourly residential load shapes
ind.load.shapes = setDT(fread("inputs/demand/raw data/Industrial load shapes.csv",
                                      header = T))

###############################################################################
################### READ HISTORICAL ENERGY CONSUMPTION DATA ###################
###############################################################################

#---------------------------
# Commercial buildings

# load energy consumption data
com.energy.cons.hist = setDT(fread("inputs/demand/raw data/Commercial sales.csv",
                                           header = T, skip = 4))

# adjust names
setnames(com.energy.cons.hist, c("Year"), c("nems.year"))

# convert data to long format
com.energy.cons.hist = melt(com.energy.cons.hist, id.vars = c("nems.year"),
                            variable.name = "cens.div.name", value.name = "com.energy.cons",
                            variable.factor = F)

# adjust Census division column, merge with division numbers
com.energy.cons.hist[, cens.div.name := gsub("Commercial...", "", cens.div.name)]
com.energy.cons.hist[, cens.div.name := gsub(".million.kilowatthours", "", cens.div.name)]
com.energy.cons.hist[, cens.div.name := gsub(".", " ", cens.div.name, fixed = T)]
com.energy.cons.hist[, cens.div.name := gsub(" Contiguous", "", cens.div.name, fixed = T)]
com.energy.cons.hist = join(com.energy.cons.hist, eia.cens.div.map[, .(cens.div.name, cens.div.num)])

# convert to million btus
com.energy.cons.hist = com.energy.cons.hist[, .(com.energy.cons = sum(com.energy.cons)*3412.1416416), by = .(cens.div.num, nems.year)]

#---------------------------
# Industrial load data

# this table can be used to apportion consumption from the Census division level to the state level
ind.energy.cons.hist = setDT(read.xlsx("inputs/demand/raw data/Industrial load disaggregation.xlsx", 
                                               "Industrial sales", colNames = T, startRow = 5))

# adjust names
setnames(ind.energy.cons.hist, c("Year"), c("nems.year"))

# convert data to long format
ind.energy.cons.hist = melt(ind.energy.cons.hist, id.vars = c("nems.year"),
                            variable.name = "state", value.name = "ind.energy.cons",
                            variable.factor = F)

# adjust state column
ind.energy.cons.hist[, state := gsub("Industrial.:.", "", state)]
ind.energy.cons.hist[, state := gsub(".million.kilowatthours", "", state)]
ind.energy.cons.hist[, state := gsub(".", " ", state, fixed = T)]
ind.energy.cons.hist[state == "District Of Columbia", state := "Maryland"]

# convert to million btus
ind.energy.cons.hist = ind.energy.cons.hist[, .(ind.energy.cons = sum(ind.energy.cons)*3412.1416416), by = .(state, nems.year)]

############################################################################
################### READ MODELED ENERGY CONSUMPTION DATA ###################
############################################################################

#---------------------------
# Residential buildings
# (note: this data comes from EIA.)

# load data (contains energy consumption and device levels)
res.energy.cons = setDT(read.xlsx("inputs/demand/raw data/EIA NEMS Residential.xlsx",
                                          "Energy consumption",
                                          colNames = T, startRow = 1))

# follow naming convention
setnames(res.energy.cons, c("ENDUSE", "CDIV", "BLDG", "FUEL",
                             "EQPCLASS", "YEAR", "Total"), 
         c("eia.use.set", "cens.div.comb", "bldg.type.name", "fuel.name", 
           "nems.dev.class", "nems.year", "res.energy.cons"))

# adjust furnace fan device name
res.energy.cons[nems.dev.class == "FurnaceFans", nems.dev.class := "FF"]

# merge with EIA mappings
res.energy.cons = join(res.energy.cons, eia.use.map)
res.energy.cons = join(res.energy.cons, eia.cens.div.map)
res.energy.cons = join(res.energy.cons, eia.res.bldg.type.map)
res.energy.cons = join(res.energy.cons, eia.fuel.map)

# extract subset of columns
res.energy.cons = res.energy.cons[, .(cens.div.num, bldg.type, nems.year, 
                                      nems.use.set, nems.fuel.set,
                                      nems.dev.class, res.energy.cons)]

# extract electric device consumption
res.energy.cons = res.energy.cons[nems.fuel.set == "EL"]

#---------------------------
# Commercial buildings
# (note: this data comes from EIA.)

# load energy consumption data
com.energy.cons = setDT(read.xlsx("inputs/demand/raw data/EIA NEMS commercial.xlsx", 
                                          "Energy consumption", 
                                          colNames = T, startRow = 1))

# follow naming convention
setnames(com.energy.cons, c("Division", "Year", "EndUse", "BldgType", "EndUseConsump"), 
         c("cens.div.comb", "nems.year", "nems.use.comb", "bldg.type.comb", "com.energy.cons"))

# convert years to numerical
com.energy.cons[, nems.year := as.numeric(nems.year)]

# merge with EIA mappings
com.energy.cons = join(com.energy.cons, eia.cens.div.map)
com.energy.cons = join(com.energy.cons, eia.com.bldg.type.map)

# extract subset of columns
com.energy.cons = com.energy.cons[, .(cens.div.num, nems.year, nems.use.comb, bldg.type.name, com.energy.cons)]

# convert to million btu
com.energy.cons[, com.energy.cons := 1e6*com.energy.cons]

#---------------------------
# Industrial facilities
# (note: this data comes from the AEO data browser.)

# load energy consumption data
ind.energy.cons = setDT(read.xlsx("inputs/demand/raw data/NEMS industrial.xlsx", 
                                          "Energy consumption", 
                                          colNames = T, startRow = 1))

# convert to long format
ind.energy.cons = melt(ind.energy.cons, id.vars = c("nems.year"),
                       variable.name = "cens.div.num", value.name = "ind.energy.cons",
                       variable.factor = F)

# convert data storage type
ind.energy.cons[, cens.div.num := as.numeric(cens.div.num)]

# convert to million btu
ind.energy.cons[, ind.energy.cons := 1e9*ind.energy.cons]

########################################################################
################### READ DISTRIBUTED GENERATION DATA ###################
########################################################################

#---------------------------
# Residential buildings
# (note: this data includes DG used for own use. Sales to the grid have been netted out.)

# load data
res.dg.cons = setDT(read.xlsx("inputs/demand/raw data/NEMS residential - v2.xlsx", 
                                      "DG", colNames = T, startRow = 1))

# follow naming convention
setnames(res.dg.cons, c("Tech", "Year", "Division", "own.use"), 
         c("nems.tech", "nems.year", "cens.div.num", "dg.cons"))

# convert consumption to million btus
res.dg.cons[, dg.cons := dg.cons*1e6]

#---------------------------
# Commercial buildings
# (note: need to calculate amount for own use using total generation and sales to grid.)

# load data
com.dg.gen = setDT(read.xlsx("inputs/demand/raw data/EIA NEMS commercial.xlsx", 
                                     "Distributed generation", colNames = T, startRow = 1))
com.dg.sales = setDT(read.xlsx("inputs/demand/raw data/EIA NEMS commercial.xlsx", 
                                       "DG sales to grid", colNames = T, startRow = 1))

# merge data
com.dg.cons = inner_join(com.dg.gen[, .(Division, Year, BldgType, Tech, dg.gen = Total)],
                         com.dg.sales[, .(Division, Year, BldgType, Tech, dg.sales = Total)])

# follow naming convention
setnames(com.dg.cons, c("Division", "Year", "BldgType", "Tech"), 
         c("cens.div.num", "nems.year", "bldg.type.name", "dg.tech"))

# calculate consumption, convert to million btus
com.dg.cons[, dg.cons := (dg.gen - dg.sales)*1e6]

########################################################################
################### READ SPATIAL DISAGGREGATION DATA ###################
########################################################################

#---------------------------
# Households
# (note: used to disaggregate residential buildings data.)

# households per county
hshld.dist = setDT(read.xlsx("inputs/demand/raw data/County demographics.xlsx", 
                                     "Households", colNames = F, startRow = 6))

# adjust names
setnames(hshld.dist, c("X1", "X2", "X3"), c("cnty.st", "mkt.key", "hshld.cnty"))

# remove income level prefix, split fips code into state and county components
hshld.dist = hshld.dist[, .(state.fips = substr(mkt.key, 5, 6), cnty.fips = substr(mkt.key, 7, 9),
                        hshld.cnty)]

# remove counties without data (just Oglala Lakota, SD)
hshld.dist = hshld.dist[!(state.fips == "46" & cnty.fips == "102")]

#---------------------------
# Population
# (note: used to disaggregate commercial buildings data.)

# people per county
pop.dist = setDT(read.xlsx("inputs/demand/raw data/County demographics.xlsx", 
                                   "Population", colNames = F, startRow = 6))

# adjust names
setnames(pop.dist, c("X1", "X2", "X3"), c("cnty.st", "mkt.key", "pop.cnty"))

# remove income level prefix, split fips code into state and county components
pop.dist = pop.dist[, .(state.fips = substr(mkt.key, 5, 6), cnty.fips = substr(mkt.key, 7, 9),
                            pop.cnty)]

# remove counties without data (just Oglala Lakota, SD)
pop.dist = pop.dist[!(state.fips == "46" & cnty.fips == "102")]

#---------------------------
# Industrial load data

# this table can be used to apportion consumption from the state level to the BA level; it also maps
# BAs into NERC regions for the purposes of specifying load shapes
ind.ba.frac = setDT(read.xlsx("inputs/demand/raw data/Industrial load disaggregation.xlsx", 
                                      "BA fractions", colNames = T))

# adjust BA column
ind.ba.frac[, reeds.ba := as.numeric(gsub("p", "", reeds.ba))]

##########################################################################
################### ADJUST SPATIAL DISAGGREGATION DATA ###################
##########################################################################

#---------------------------
# Household distributions over BAs

# merge with geographic data
hshld.dist = inner_join(hshld.dist, geo.map[, .(state.fips, cnty.fips, reeds.ba, state.abb, cens.div.num)])

# assign DC to Maryland
hshld.dist[state.abb == "DC", state.abb := "MD"]

# sum to BA level
hshld.dist = hshld.dist[, .(hshld.ba = sum(hshld.cnty)), by = .(reeds.ba, state.abb, cens.div.num)]

# create column with Census division sums
hshld.dist[, hshld.div := sum(hshld.ba), by = .(cens.div.num)]

# calculate proportions of each BA/income bin within each Census division
# (note: this can be used directly to disaggregate device numbers from Census divisions
# to BAs classes)
hshld.dist = hshld.dist[, .(reeds.ba, state.abb, cens.div.num, hshld.prop.ba = hshld.ba/hshld.div)]

#---------------------------
# Population distributions over BAs

# merge with geographic data
pop.dist = inner_join(pop.dist, geo.map[, .(state.fips, cnty.fips, reeds.ba, state.abb, cens.div.num)])

# assign DC to Maryland
pop.dist[state.abb == "DC", state.abb := "MD"]

# sum to BA level
pop.dist = pop.dist[, .(pop.ba = sum(pop.cnty)), by = .(reeds.ba, state.abb, cens.div.num)]

# create column with Census division sums
pop.dist[, pop.div := sum(pop.ba), by = .(cens.div.num)]

# calculate proportions of each BA within each Census division
pop.dist = pop.dist[, .(reeds.ba, state.abb, cens.div.num, pop.prop.ba = pop.ba/pop.div)]

#---------------------------
# Industrial consumption distributions over BAs

# merge state consumption data to geographic mapping
ind.energy.cons.hist = inner_join(ind.energy.cons.hist, 
                                  unique(geo.map[, .(state, state.abb, cens.div.num)]))

# sum consumption over Census divisions
ind.energy.cons.hist[, ind.energy.cons.div := sum(ind.energy.cons), by = .(cens.div.num, nems.year)]

# calculate load proportions for each state within Census divisions
ind.state.dist = ind.energy.cons.hist[, .(state.abb, cens.div.num, nems.year,
                                          ind.load.dist = ind.energy.cons/ind.energy.cons.div)]

# merge BA distributions within states with state distributions within Census divisions
ind.load.dist = inner_join(ind.state.dist, ind.ba.frac[, .(reeds.ba, state.abb, frac.ba.state)])

# calculate proportions of each BA within each Census division
ind.load.dist = ind.load.dist[, .(reeds.ba, state.abb, cens.div.num, nems.year, 
                                  ind.load.prop.ba = ind.load.dist*frac.ba.state)]

# create temporary table to cover all model years
ind.load.dist.temp = CJ.table(unique(geo.map[, .(reeds.ba, state.abb, cens.div.num)]), 
                              data.table(nems.year = 2017:2050))

# apply 2016 distribution to all future years
ind.load.dist.temp = inner_join(ind.load.dist.temp, 
                                ind.load.dist[nems.year == 2016, 
                                              .(reeds.ba, state.abb, cens.div.num, ind.load.prop.ba)])

# merge both load distribution tables
ind.load.dist = rbind(ind.load.dist[nems.year %in% seq(2010, 2016)], ind.load.dist.temp)

##########################################################################
################### PREPARE RESIDENTIAL BUILDINGS DATA ###################
##########################################################################

#---------------------------
# Disaggregate load shape data

# merge with household distribution data
res.load.shapes = inner_join(res.load.shapes, hshld.dist)

# convert to long format over end-use shapes
res.load.shapes = melt(res.load.shapes[, state.abb := NULL],
                       id.vars = c("reeds.ba", "cens.div.num","HourID", "hshld.prop.ba"),
                       variable.name = "elec.use.set", value.name = "load.prop.hr.use",
                       variable.factor = F)

# calculate fractions for each hour and BA by end use
res.load.shapes = res.load.shapes[, .(reeds.ba, cens.div.num, HourID, elec.use.set, 
                                      load.prop.hr.ba.use = load.prop.hr.use*hshld.prop.ba)]

#---------------------------
# Apply distribution generation consumption totals, aggregate consumption

# shift DG data from long to wide format (solar versus other)
res.dg.cons = dcast(res.dg.cons, nems.year + cens.div.num ~ nems.tech,
                     value.var = c("dg.cons"))

# rename columns
setnames(res.dg.cons, c("Other", "Solar_PV"), c("other.dg.cons", "solar.dg.cons"))

# merge data
res.energy.cons = join(res.energy.cons, res.dg.cons)

# apply DG consumption values for single family homes (central AC and MELs)
res.energy.cons[bldg.type == "1" & nems.dev.class == "CENT_AIR", 
                 res.energy.cons := res.energy.cons + 0.35*solar.dg.cons
                 ][bldg.type == "1" & nems.dev.class == "MEL", 
                   res.energy.cons := res.energy.cons + other.dg.cons + 0.65*solar.dg.cons]

# remove unneeded columns
res.energy.cons[, c("other.dg.cons", "solar.dg.cons") := NULL]

# aggregate consumption to years, end-uses, and Census divisions
res.energy.cons = res.energy.cons[, .(res.energy.cons = sum(res.energy.cons)), 
                                  by =  .(cens.div.num, nems.year, nems.use.set)]

#---------------------------
# Construct 8760 profiles of total consumption by BA

# merge electrification end uses into energy consumption table
res.energy.cons = inner_join(res.energy.cons, res.use.map[, .(elec.use.set, nems.use.set)])

setorderv(res.load.shapes, c("cens.div.num"))

system.time({
  res.energy.cons <- foreach(dt.shapes = isplit(res.load.shapes, res.load.shapes$cens.div.num, drop = TRUE),
                             dt.cons = isplit(res.energy.cons, res.energy.cons$cens.div.num, drop = TRUE),
                             .combine = rbind, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
                             .packages = c("dplyr", "data.table", "dtplyr")) %dopar% {

                               # assign imported data as type "data table"
                               dt.shapes = setDT(dt.shapes[[1]])
                               dt.cons = setDT(dt.cons[[1]])

                               # merge load shape and energy consumption data
                               dt.cons = inner_join(dt.cons[, .(res.energy.cons = sum(res.energy.cons)),
                                                            by = .(cens.div.num, nems.year, elec.use.set)],
                                                    dt.shapes)

                               # apply load shape proportions and sum over end uses
                               dt.cons = dt.cons[, .(res.energy.cons = sum(res.energy.cons*load.prop.hr.ba.use)),
                                                 by = .(reeds.ba, nems.year, HourID)]

                  }
})

#########################################################################
################### PREPARE COMMERCIAL BUILDINGS DATA ###################
#########################################################################

#---------------------------
# Disaggregate load shape data

# merge with population distribution data
com.load.shapes = inner_join(com.load.shapes, pop.dist)

# convert to long format over end-use shapes
com.load.shapes = melt(com.load.shapes[, state.abb := NULL],
                       id.vars = c("reeds.ba", "cens.div.num","HourID", "pop.prop.ba"),
                       variable.name = "elec.use.set", value.name = "load.prop.hr.use",
                       variable.factor = F)

# calculate fractions for each hour and BA by end use
com.load.shapes = com.load.shapes[, .(reeds.ba, cens.div.num, HourID, elec.use.set, 
                                      load.prop.hr.ba.use = load.prop.hr.use*pop.prop.ba)]

#---------------------------
# Apply distribution generation consumption totals, aggregate consumption

# shift DG data from long to wide format (solar versus other)
com.dg.cons = dcast(com.dg.cons, cens.div.num + nems.year + bldg.type.name ~ dg.tech,
                    value.var = c("dg.cons"))

# rename columns
setnames(com.dg.cons, c("Solar_PV"), c("solar.dg.cons"))

# merge data
com.energy.cons = join(com.energy.cons, com.dg.cons[, .(cens.div.num, nems.year, bldg.type.name, solar.dg.cons)])

# apply DG consumption values
com.energy.cons[nems.use.comb == "2 Cooling", com.energy.cons := com.energy.cons + 0.12*solar.dg.cons
                ][nems.use.comb == "4 Ventilation", com.energy.cons := com.energy.cons + 0.13*solar.dg.cons
                  ][nems.use.comb == "6 Lighting", com.energy.cons := com.energy.cons + 0.16*solar.dg.cons
                    ][nems.use.comb == "10 Other", com.energy.cons := com.energy.cons + 0.59*solar.dg.cons]

# aggregate consumption to years, end-uses, and Census divisions
com.energy.cons = com.energy.cons[, .(com.energy.cons = sum(com.energy.cons)), 
                                  by =  .(cens.div.num, nems.year, nems.use.comb)]

#---------------------------
# Merge modeled consumption data with historical consumption data

# create end use proportions for 2013 (first year of modeled data)
com.energy.cons.temp = com.energy.cons[nems.year == 2013, 
                                       .(nems.use.comb, end.use.prop = com.energy.cons/sum(com.energy.cons)), 
                                       by = .(cens.div.num)]

# merge with historical data
com.energy.cons.temp = inner_join(com.energy.cons.hist[nems.year %in% seq(2010, 2012)], com.energy.cons.temp)

# apply end use proportions
com.energy.cons.temp[, com.energy.cons := com.energy.cons*end.use.prop]

# merge with modeled consumption table
com.energy.cons = rbind(com.energy.cons, com.energy.cons.temp[, .(cens.div.num, nems.year, nems.use.comb, com.energy.cons)])

#---------------------------
# Construct 8760 profiles of total consumption by BA

# merge electrification end uses into energy consumption table
com.energy.cons = inner_join(com.energy.cons, com.use.map[, .(elec.use.set, nems.use.comb)])

setorderv(com.load.shapes, c("cens.div.num"))

system.time({
  com.energy.cons <- foreach(dt.shapes = isplit(com.load.shapes, com.load.shapes$cens.div.num, drop = TRUE),
                             dt.cons = isplit(com.energy.cons, com.energy.cons$cens.div.num, drop = TRUE),
                             .combine = rbind, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
                             .packages = c("dplyr", "data.table", "dtplyr")) %dopar% {

                               # assign imported data as type "data table"
                               dt.shapes = setDT(dt.shapes[[1]])
                               dt.cons = setDT(dt.cons[[1]])

                               # merge load shape and energy consumption data
                               dt.cons = inner_join(dt.cons[, .(com.energy.cons = sum(com.energy.cons)),
                                                            by = .(cens.div.num, nems.year, elec.use.set)],
                                                    dt.shapes)

                               # apply load shape proportions and sum over end uses
                               dt.cons = dt.cons[, .(com.energy.cons = sum(com.energy.cons*load.prop.hr.ba.use)),
                                                 by = .(reeds.ba, nems.year, HourID)]

                             }
})

##########################################################################
################### PREPARE INDUSTRIAL FACILITIES DATA ###################
##########################################################################

#---------------------------
# Disaggregate load shape data

# convert load shape data into long format
ind.load.shapes = melt(ind.load.shapes, id.vars = c("HourID"), variable.name = "nerc.region",
                       value.name = "load.prop.hr", variable.factor = F)

ind.load.shapes[, nerc.region := gsub("/", ".", nerc.region, fixed = T)]


# merge load shape data with BA/NERC region mapping
ind.load.shapes = inner_join(ind.ba.frac[, .(reeds.ba, nerc.region)], ind.load.shapes)

# merge with geographic industrial load distribution data
# (note: assume 2016 distributions apply to all NEMS modeled years)
ind.load.shapes = inner_join(ind.load.shapes[, .(reeds.ba, HourID, load.prop.hr)],
                             ind.load.dist[, .(reeds.ba, cens.div.num, nems.year, ind.load.prop.ba)])

# calculate fractions for each hour and BA by end use
ind.load.shapes = ind.load.shapes[, .(reeds.ba, cens.div.num, nems.year, HourID,  
                                      load.prop.hr.ba = load.prop.hr*ind.load.prop.ba)]

#---------------------------
# Merge modeled consumption data with historical consumption data

# aggregate historical state level consumption data to the Census division level
ind.energy.cons.temp = ind.energy.cons.hist[nems.year %in% seq(2010, 2014),
                                            .(ind.energy.cons = sum(ind.energy.cons)),
                                            by = .(cens.div.num, nems.year)]

# merge with modeled consumption table
ind.energy.cons = rbind(ind.energy.cons.temp, ind.energy.cons)

#---------------------------
# Construct 8760 profiles of total consumption by BA

setorderv(ind.load.shapes, c("cens.div.num"))

system.time({
  ind.energy.cons <- foreach(dt.shapes = isplit(ind.load.shapes, ind.load.shapes$cens.div.num, drop = TRUE),
                             dt.cons = isplit(ind.energy.cons, ind.energy.cons$cens.div.num, drop = TRUE),
                             .combine = rbind, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
                             .packages = c("dplyr", "data.table", "dtplyr")) %dopar% {

                               # assign imported data as type "data table"
                               dt.shapes = setDT(dt.shapes[[1]])
                               dt.cons = setDT(dt.cons[[1]])

                               # merge load shape and energy consumption data
                               dt.cons = inner_join(dt.cons, dt.shapes)
                               
                               # apply load shape proportions
                               dt.cons = dt.cons[, .(ind.energy.cons = ind.energy.cons*load.prop.hr.ba),
                                                         by = .(reeds.ba, nems.year, HourID)]

                             }
})

##############################################################
################### DETERMINE TOP 40 HOURS ###################
##############################################################

#---------------------------
# Merge disaggregated sectoral load data

res.energy.cons = res.energy.cons[nems.year > 2009]

setorderv(res.energy.cons, c("reeds.ba", "nems.year", "HourID"))
setorderv(com.energy.cons, c("reeds.ba", "nems.year", "HourID"))
setorderv(ind.energy.cons, c("reeds.ba", "nems.year", "HourID"))
energy.cons = cbind(res.energy.cons, com.energy.cons[, .(com.energy.cons)], ind.energy.cons[, .(ind.energy.cons)])
  
# sum across sectors
energy.cons = energy.cons[, .(reeds.ba, nems.year, HourID, 
                              energy.cons = res.energy.cons + com.energy.cons + ind.energy.cons)]

#---------------------------
# Determine H17 hours

# merge with time slice mapping table
energy.cons = inner_join(energy.cons, time.map[, .(HourID, time.slice)])

# extract summer afternoon load data (H3)
energy.cons.H3 = energy.cons[time.slice == "H3"]

# extract top 40 hours of H3 for each BA
energy.cons.H17 = energy.cons.H3[order(-energy.cons), .SD[1:40], by = .(reeds.ba, nems.year)
                                 ][, H17.ind := 1]

#---------------------------
# Construct and export updated time mapping table

# create new time mapping tables
time.map.new = CJ.table(CJ.table(data.table(reeds.ba = 1:134), data.table(nems.year = 2015:2050)),
                        time.map[, .(HourID, time.slice)])
time.map.temp = CJ.table(CJ.table(data.table(reeds.ba = 1:134), data.table(nems.year = 2010:2014)),
                         time.map[, .(HourID)])

# merge H17 hours indicator into time mapping table
time.map.new = left_join(time.map.new, energy.cons.H17[, .(reeds.ba, nems.year, HourID, H17.ind)])

# assign H17 hours
time.map.new[H17.ind == 1, time.slice := "H17"]

# remove H17 indicator column
time.map.new[, H17.ind := NULL]

# merge 2015 assignments into pre-2015 table
time.map.temp = inner_join(time.map.temp, time.map.new[nems.year == 2015, .(reeds.ba, HourID, time.slice)])

# merge pre-2015 table
time.map.new = rbind(time.map.new, time.map.temp)

# export new time map
fwrite(time.map.new, "//nrelqnap01d/ReEDS/FY18-ReEDS-2.0/DemandData/time-map.csv", row.names = F)

#########################################################################
################### CONSTRUCT TOTAL CONSUMPTION TABLE ###################
#########################################################################

#---------------------------
#

# merge H17 hours indicator into time mapping table
energy.cons = left_join(energy.cons, energy.cons.H17[, .(reeds.ba, nems.year, HourID, H17.ind)])

# assign H17 hours
energy.cons[H17.ind == 1, time.slice := "H17"]


# system.time({
#   temp1 <- foreach(dt.cons = isplit(energy.cons, energy.cons$reeds.ba, drop = TRUE),
#                    .combine = rbind, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
#                    .packages = c("dplyr", "data.table", "dtplyr")) %dopar% {
#                      
#                      # assign imported data as type "data table"
#                                  dt.cons = setDT(dt.cons[[1]])
#                                  
#                      # merge load shape and energy consumption data
#                                  dt.cons[, .(energy.cons = mmbtu2mwh*sum(energy.cons)),
#                                  by = .(reeds.ba, nems.year, time.slice)]
#                                  
#                                }
#   })


# sum to time slice level and convert from mmBtu to MWh
energy.cons = energy.cons[, .(energy.cons = mmbtu2mwh*sum(energy.cons)),
                          by = .(reeds.ba = paste("p", reeds.ba, sep = ""), nems.year, time.slice)]

# export consumption
fwrite(energy.cons, "inputs/demand/processed data/ref-consumption.csv",
       sep = ",", row.names = F, col.names = F)

####################################################################################################
################### CONSTRUCT FINAL COMMERCIAL AND INDUSTRIAL CONSUMPTION TABLES ###################
####################################################################################################

#---------------------------
# Commercial buildings

# merge commercial consumption data with new time slice map
com.energy.cons = inner_join(com.energy.cons, time.map.new)

# sum to time slice level and convert from mmBtu to MWh
com.energy.cons = com.energy.cons[, .(com.energy.cons = mmbtu2mwh*sum(com.energy.cons)), 
                                  by = .(reeds.ba = paste("p", reeds.ba, sep = ""), nems.year, time.slice)]

# export consumption
fwrite(com.energy.cons, "inputs/demand/processed data/commercial-load.csv",
       sep = ",", row.names = F, col.names = F)

#---------------------------
# Industrial facilities

# merge consumption data with new time slice map
ind.energy.cons = inner_join(ind.energy.cons, time.map.new)

# sum to time slice level and convert from mmBtu to MWh
ind.energy.cons = ind.energy.cons[, .(ind.energy.cons = mmbtu2mwh*sum(ind.energy.cons)), 
                                  by = .(reeds.ba = paste("p", reeds.ba, sep = ""), nems.year, time.slice)]

# export consumption
fwrite(ind.energy.cons, "inputs/demand/processed data/industrial-load.csv",
       sep = ",", row.names = F, col.names = F)

##########################################################
################### ALTERNATIVE METHOD ###################
##########################################################

#---------------------------
# Construct 8760 profiles of total consumption by BA

# setorderv(res.load.shapes, c("cens.div.num"))
# setorderv(com.load.shapes, c("cens.div.num"))
# setorderv(ind.load.shapes, c("cens.div.num"))
# 
# system.time({
#   result <- foreach(dt.res.shapes = isplit(res.load.shapes, res.load.shapes$cens.div.num, drop = TRUE),
#                     dt.res.cons = isplit(res.energy.cons, res.energy.cons$cens.div.num, drop = TRUE),
#                     dt.com.shapes = isplit(com.load.shapes, com.load.shapes$cens.div.num, drop = TRUE),
#                     dt.com.cons = isplit(com.energy.cons, com.energy.cons$cens.div.num, drop = TRUE),
#                     dt.ind.shapes = isplit(ind.load.shapes, ind.load.shapes$cens.div.num, drop = TRUE),
#                     dt.ind.cons = isplit(ind.energy.cons, ind.energy.cons$cens.div.num, drop = TRUE),
#                     .combine = rbind, .multicombine = TRUE, .maxcombine = 200, .inorder = FALSE,
#                     .packages = c("dplyr", "data.table", "dtplyr")) %dopar% {
# 
#                       # assign imported data as type "data table"
#                       dt.res.shapes = setDT(dt.res.shapes[[1]])
#                       dt.res.cons = setDT(dt.res.cons[[1]])
#                       dt.com.shapes = setDT(dt.com.shapes[[1]])
#                       dt.com.cons = setDT(dt.com.cons[[1]])
#                       dt.ind.shapes = setDT(dt.ind.shapes[[1]])
#                       dt.ind.cons = setDT(dt.ind.cons[[1]])
# 
#                       # merge load shape and energy consumption data
#                       dt.res.cons = inner_join(dt.res.cons[, .(res.energy.cons = sum(res.energy.cons)),
#                                                            by = .(cens.div.num, nems.year, elec.use.set)],
#                                                dt.res.shapes)
# 
#                       # apply load shape proportions and sum over end uses
#                       dt.res.cons = dt.res.cons[, .(res.energy.cons = sum(res.energy.cons*load.prop.hr.ba.use)),
#                                                 by = .(reeds.ba, nems.year, HourID)]
# 
#                       # merge load shape and energy consumption data
#                       dt.com.cons = inner_join(dt.com.cons[, .(com.energy.cons = sum(com.energy.cons)),
#                                                            by = .(cens.div.num, nems.year, elec.use.set)],
#                                                dt.com.shapes)
# 
#                       # apply load shape proportions and sum over end uses
#                       dt.com.cons = dt.com.cons[, .(com.energy.cons = sum(com.energy.cons*load.prop.hr.ba.use)),
#                                                 by = .(reeds.ba, nems.year, HourID)]
# 
#                       # merge load shape and energy consumption data
#                       dt.ind.cons = inner_join(dt.ind.cons, dt.ind.shapes)
# 
#                       # apply load shape proportions
#                       dt.ind.cons = dt.ind.cons[, .(ind.energy.cons = ind.energy.cons*load.prop.hr.ba),
#                                                 by = .(reeds.ba, nems.year, HourID)]
#                       
#                       # merge sectoral data
#                       setorderv(dt.res.cons, c("reeds.ba", "nems.year", "HourID"))
#                       setorderv(dt.com.cons, c("reeds.ba", "nems.year", "HourID"))
#                       setorderv(dt.ind.cons, c("reeds.ba", "nems.year", "HourID"))
#                       dt.energy.cons = cbind(dt.res.cons, dt.com.cons[, .(com.energy.cons)], dt.ind.cons[, .(ind.energy.cons)])
#                       
#                       rm(dt.res.cons, dt.com.cons, dt.ind.cons)
#                       
#                       # sum across sectors
#                       dt.energy.cons = dt.energy.cons[, .(reeds.ba, nems.year, HourID,
#                                                           energy.cons = res.energy.cons + com.energy.cons + ind.energy.cons)]
# 
#                     }
# })

})

stopImplicitCluster()