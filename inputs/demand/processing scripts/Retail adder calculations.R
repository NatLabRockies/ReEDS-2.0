# Demand data processing for ReEDS 2.0
# Initially written 2017-09-25
# Dave Bielen
# NREL

######################################################
#################### PRELIMINARY #####################
######################################################

#---------------------------dsteinbe-27456s
# Set working directory

if (Sys.getenv('computername') == "DSTEINBE-27456S") {
  setwd('C:/Users/dbielen/ReEDS/ReEDS-2.0')
} else if (Sys.getenv('computername') == "1WP11RDORI01") {
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

if (Sys.getenv('computername') == "DSTEINBE-27456S")  {
  igdx("C:/gams/win64/24.8")
} else {
  igdx("C:/gams/win64/24.7")
}


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

#---------------------------
# Functions

CJ.table <- function(X,Y)
  setkey(X[,c(k=1,.SD)],k)[Y[,c(k=1,.SD)],allow.cartesian=TRUE][,k:=NULL]

#---------------------------
# Plot Options

# Plot specs
ppi = 300
single.w.mult = 10
single.h.mult = 6
textsize = 10
linesize = 1

# Plot theme
theme.main = theme(
  text                = element_text(family="Open Sans", size = textsize),
  plot.title          = element_text(hjust=.5), 
  axis.title.x        = element_text(hjust=.5),
  axis.title.y        = element_text(hjust=.5),
  axis.text.x         = element_text(hjust=.5, angle = 45),
  axis.ticks.x        = element_blank(), 
  panel.grid.major.y  = element_line(color='gray', size = .3),
  panel.grid.minor.y  = element_blank(),
  panel.grid.major.x  = element_blank(),
  panel.grid.minor.x  = element_blank(),
  panel.border        = element_blank(),
  panel.background    = element_blank(),
  legend.position     = "right",
  legend.title        = element_blank()
)

###################################################################
################### CREATE TEMPLATE DATA TABLES ###################
###################################################################

#---------------------------
# 

###########################################################
################### READ MAPPING TABLES ###################
###########################################################

#---------------------------
# 

# map counties, BAs, counties, states, and Census divisions
geo.map = setDT(read.xlsx("inputs/demand/raw data/Mapping sets.xlsx",
                          "Geographic aggregation", colNames = T))

# convert FIPS codes to character format
geo.map[, cnty.fips := sprintf("%03d", cnty.fips)]
geo.map[, state.fips := sprintf("%02d", state.fips)]

# Census division mappings
eia.cens.div.map = setDT(read.xlsx("inputs/demand/raw data/EIA mapping sets.xlsx", 
                                   "Census divisions", colNames = T))

# merge geo-map and Census division mappings
geo.map = inner_join(unique(geo.map[reeds.ba > 0, .(ba = paste("p", reeds.ba, sep = ""), 
                                                    cens.div.num, state.abb, state)]),
                     eia.cens.div.map[, .(cens.div.num, cens.div.name)])

geo.map = geo.map[state.abb != "DC"]

state.vec = unique(geo.map[, .(state)])[[1]]

# maps ReEDS BAs and market regions from the EMM
emm.map = fread("inputs/demand/raw data/NEMS-ReEDS Region Mapping.csv", header = T)[, .(ba = PCA_Code, nems.reg.abb = NEMS_Region, area = F_AREA)]

emm.map = emm.map[ba != "" & nems.reg.abb != ""][, max.area := max(area), by = .(ba)][area == max.area, .(ba, nems.reg.abb)]

#################################################
################### READ DATA ###################
#################################################

#---------------------------
# Historical data

eia.prices = setDT(read.xlsx("inputs/demand/raw data/EIA 2016 electricity prices.xlsx",
                             "Table 4", colNames = T, startRow = 3))[, .(state = State, res.price = Residential, 
                                                                         com.price = Commercial, ind.price = Industrial)]

eia.prices = eia.prices[state %in% state.vec]

eia.sales = setDT(read.xlsx("inputs/demand/raw data/EIA 2016 electricity sales.xlsx",
                             "Table 2", colNames = T, startRow = 3))[, .(state = State, res.sales = Residential, 
                                                                         com.sales = Commercial, ind.sales = Industrial)]

eia.sales = eia.sales[state %in% state.vec]

#---------------------------
# NEMS data

aeo.adders = setDT(read.xlsx("inputs/demand/raw data/NEMS price adders.xlsx",
                             "AEO2018", colNames = T, startRow = 1))

aeo.adders = melt(aeo.adders, id.vars = c("nems.reg.abb", "category"),
                  variable.name = "year", value.name = "avg.adder",
                  variable.factor = F)[, year := as.integer(year)]

aeo.adders = aeo.adders[year == 2016, .(avg.adder = sum(avg.adder)), by = .(nems.reg.abb)]

###########################################################
################### MERGE AND CALCULATE ###################
###########################################################

#---------------------------
# 

eia.data = inner_join(eia.prices, eia.sales)

eia.data = inner_join(inner_join(eia.data, geo.map[, .(ba, state)]), emm.map)

adder.data = inner_join(eia.data, aeo.adders)

adder.data = adder.data[, gen.price := (res.price*res.sales + com.price*com.sales + ind.price*ind.sales)/
                          (avg.adder*(res.sales + com.sales + ind.sales))]

price.data = adder.data[, .(ba, res = res.price, com = com.price, ind = ind.price)]

adder.data = adder.data[, .(res = res.price - gen.price, com = com.price - gen.price, 
                            ind = ind.price - gen.price), by = .(ba)]

adder.data = melt(adder.data, id.vars = c("ba"), variable.name = "sector",
                  value.name = "adder", variable.factor = F)[, .(sector, ba, adder)]

adder.data[, adder := 10*adder]

price.data = melt(price.data, id.vars = c("ba"), variable.name = "sector",
                  value.name = "price", variable.factor = F)[, .(sector, ba, price)]

price.data[, price := 10*price]

##############################################
################### EXPORT ###################
##############################################

#---------------------------
# 

fwrite(adder.data, "inputs/demand/processed data/price-adders.csv",
       sep = ",", row.names = F, col.names = F)

fwrite(price.data, "inputs/demand/processed data/retail-prices.csv",
       sep = ",", row.names = F, col.names = F)

