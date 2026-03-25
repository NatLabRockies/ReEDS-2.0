# Demand data processing for ReEDS 2.0
# Initially written 2017-09-25
# Dave Bielen
# NREL

######################################################
#################### PRELIMINARY #####################
######################################################

#---------------------------
# Set working directory

setwd('C:/Users/dbielen/Desktop/ReEDS-LDRD-FY17/Demand data/')
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
library(table1xls)
igdx("C:/gams/win64/24.5")

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

wh2btu = 3.41214

#---------------------------
# Functions

CJ.table <- function(X,Y)
  setkey(X[,c(k=1,.SD)],k)[Y[,c(k=1,.SD)],allow.cartesian=TRUE][,k:=NULL]


###################################################################
################### CREATE TEMPLATE DATA TABLES ###################
###################################################################

#---------------------------
# Import set vectors and mapping tables

# map counties, BAs, counties, states, and Census divisions
geo.map = as.data.table(read.xlsx("Mapping sets.xlsx", "Geographic aggregation", colNames = T))

# map American Community Survey income classes to ReEDS income classes
income.map = as.data.table(read.xlsx("Mapping sets.xlsx", "Income aggregation", colNames = T))

# map device names to device classes to end uses and fuels and efficiency units (all NEMS)
dvc.map = as.data.table(read.xlsx("Mapping sets.xlsx", "Device aggregation", colNames = T))

# map NEMS end uses to end uses for the electrification study (eventually DSGrid) and ReEDS
use.map = as.data.table(read.xlsx("Mapping sets.xlsx", "End-use aggregation", colNames = T))

#---------------------------
# EIA mapping sets

eia.use.map = as.data.table(read.xlsx("EIA mapping sets.xlsx", "end uses", colNames = T))

eia.cens.div.map = as.data.table(read.xlsx("EIA mapping sets.xlsx", "Census divisions", colNames = T))

eia.bldg.type.map = as.data.table(read.xlsx("EIA mapping sets.xlsx", "building types", colNames = T))

eia.fuel.map = as.data.table(read.xlsx("EIA mapping sets.xlsx", "fuels", colNames = T))


###############################################################
################### LOAD NEMS SCENARIO DATA ###################
###############################################################

#---------------------------
# Energy consumption (EIA)

# load data (contains energy consumption and device levels)
eia.energy.cons = as.data.table(read.xlsx("EIA NEMS Residential.xlsx", 
                                          "Energy consumption", 
                                          colNames = T, startRow = 1))

# follow naming convention
setnames(eia.energy.cons, c("ENDUSE", "CDIV", "BLDG", "FUEL",
                            "EQPCLASS", "YEAR", "Total"), 
         c("eia.use.set", "cens.div.name", "bldg.type.name", "fuel.name", 
           "nems.dev.class", "nems.year", "energy.cons"))

# convert consumption to quads
eia.energy.cons[, energy.cons := energy.cons/1e9]

# subset electricity
eia.energy.cons = eia.energy.cons[fuel.name == "Electricity"]

#---------------------------
# Energy consumption from AEO data browser (Census division - aggregate)

# load data
div.aeo = as.data.table(read.xlsx("AEO2017 browser data.xlsx",
                                          "res-cons-by-cens-div", colNames = T, startRow = 1))

# reshape to long
div.aeo = melt(div.aeo, id.vars = c("nems.year"), variable.name = "cens.div", 
               value.name = "browser", variable.factor = F)

# convert data storage type
div.aeo[, cens.div := as.numeric(cens.div)]

#---------------------------
# Energy consumption from AEO data browser (National - end use)

# load data
use.aeo = as.data.table(read.xlsx("AEO2017 browser data.xlsx",
                                  "res-cons-by-end-use", colNames = T, startRow = 1))

# reshape to long
use.aeo = melt(use.aeo, id.vars = c("nems.year"), variable.name = "nems.use.set", 
               value.name = "browser", variable.factor = F)

#---------------------------
# Distributed generation totals

# load data
nems.dg.cons = as.data.table(read.xlsx("NEMS residential - v2.xlsx", "DG",
                                       colNames = T, startRow = 1))

# follow naming convention
setnames(nems.dg.cons, c("Tech", "Year", "Division", "own.use"), 
         c("nems.tech", "nems.year", "cens.div", "energy.cons"))

# convert consumption to quads
nems.dg.cons[, energy.cons := energy.cons/1e3]

##########################################################
################### ADJUST ENERGY DATA ###################
##########################################################

#---------------------------
# Implement EIA data mappings

eia.energy.cons = join(eia.energy.cons, eia.use.map)
eia.energy.cons = join(eia.energy.cons, eia.cens.div.map)
eia.energy.cons = join(eia.energy.cons, eia.bldg.type.map)
eia.energy.cons = join(eia.energy.cons, eia.fuel.map)

######################################################
################### AGGREGATE DATA ###################
######################################################

#---------------------------
# Move secondary heating into the space heating end use

eia.energy.cons[nems.use.set == "SH", nems.dev.class := "SH"]
eia.energy.cons[nems.use.set == "SH", nems.use.set := "HT"]

#---------------------------
# Give TVs and computers their own end uses

eia.energy.cons[nems.dev.class == "TV&R", nems.use.set := "TV&R"]
eia.energy.cons[nems.dev.class == "PC&R", nems.use.set := "PC&R"]

#---------------------------
# Sum over building types and end uses

div.data = eia.energy.cons[, .(energy.cons = sum(energy.cons), 
                               energy.cons.noac = sum(.SD[!(bldg.type == 1 &
                                                              nems.dev.class == "CENT_AIR"), energy.cons])),
                           by = .(cens.div, nems.year)]

#---------------------------
# Sum over Census divisions, building types and device classes

use.data = eia.energy.cons[, .(energy.cons = sum(energy.cons), 
                              energy.cons.noac = sum(.SD[!(bldg.type == 1 &
                                                             nems.dev.class == "CENT_AIR"), energy.cons])),
                            by = .(nems.use.set, nems.year)]

##################################################
################### MERGE DATA ###################
##################################################

#---------------------------
# Census division electricity consumption

div.data = inner_join(div.data, div.aeo)

div.data = melt(div.data, id.vars = c("nems.year", "cens.div"), 
                variable.name = "source", 
                value.name = "value", variable.factor = F)

div.data[source == "energy.cons", source := "EIA (CAC)"]
div.data[source == "energy.cons.noac", source := "EIA (no CAC)"]
div.data[source == "browser", source := "AEO browser"]

#---------------------------
# End use electricity consumption

use.data = inner_join(use.data, use.aeo)

use.data = melt(use.data, id.vars = c("nems.year", "nems.use.set"), 
                variable.name = "source", 
                value.name = "value", variable.factor = F)

use.data[source == "energy.cons", source := "EIA (CAC)"]
use.data[source == "energy.cons.noac", source := "EIA (no CAC)"]
use.data[source == "browser", source := "AEO browser"]

#########################################################
################### CREATE TEST PLOTS ###################
#########################################################

#---------------------------
# Electricity consumption by Census division

png("Figures/EIA Census division comparison.png", width=3000, height=3600, res=300)

ggplot(data = div.data, aes(x = nems.year, y = value, color = source)) +
  geom_line(size = 1) +
  facet_wrap(~ cens.div, nrow = 3, scales = "free_y") +
  labs(title = "Residential electricity consumption by Census division", 
       x = "Year", y = "Electricity consumption (quads)") +
  theme_classic()

dev.off()

#---------------------------
# Electricity consumption by end use

png("Figures/EIA end use comparison.png", width=3000, height=3600, res=300)

ggplot(data = use.data, aes(x = nems.year, y = value, color = source)) +
  geom_line(size = 1) +
  facet_wrap(~ nems.use.set, nrow = 4, scales = "free_y") +
  labs(title = "Residential electricity consumption by end use", 
       x = "Year", y = "Electricity consumption (quads)") +
  theme_classic() + theme(axis.text.x = element_text(angle = 45))

dev.off()
