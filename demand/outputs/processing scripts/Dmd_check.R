# Demand data processing for ReEDS 2.0
# Initially written 2017-09-25
# Dave Bielen
# NREL

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
igdx("C:/gams/win64/24.7")

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
# Tables that apply to all sectors

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
geo.map = inner_join(unique(geo.map[reeds.ba > 0, .(ba = paste("p", reeds.ba, sep = ""), cens.div.num, state.abb)]),
                     eia.cens.div.map[, .(cens.div.num, cens.div.name)])

geo.map = geo.map[state.abb != "DC"]

########################################################
################### LOAD OUTPUT DATA ###################
########################################################


#---------------------------
# ReEDS 2.0 w/ ReEDS 2.0 supply side prices

res.dmd.use1 = remove.factors(setDT(rgdx.param("temp_dmd/dmd_use_chk_reeds.gdx", "ResDmdUse",
                                               names=c("ba", "year", "end.use", "ReEDS2.0"),
                                               compress=T, squeeze=F)))[, year := as.integer(year)]

dmd.sec1 = remove.factors(setDT(rgdx.param("temp_dmd/dmd_use_chk_reeds.gdx", "DmdSec",
                            names=c("sector", "ba", "year", "time.slice", "ReEDS2.0"),
                            compress=T, squeeze=F)))[, year := as.integer(year)]

#---------------------------
# ReEDS 2.0 w/ NEMS supply side prices

res.dmd.use2 = remove.factors(setDT(rgdx.param("temp_dmd/dmd_use_chk_nems.gdx", "ResDmdUse",
                                names=c("ba", "year", "end.use", "NEMS"),
                                compress=T, squeeze=F)))[, year := as.integer(year)]

dmd.sec2 = remove.factors(setDT(rgdx.param("temp_dmd/dmd_use_chk_nems.gdx", "DmdSec",
                            names=c("sector", "ba", "year", "time.slice", "NEMS"),
                            compress=T, squeeze=F)))[, year := as.integer(year)]

#---------------------------
# AEO2017 

dmd.sec.aeo = remove.factors(setDT(rgdx.param("temp_dmd/dmd_chk_aeo.gdx", "DmdSecAEO",
                               names=c("sector", "ba", "year", "AEO2017"),
                               compress=T, squeeze=F)))[, year := as.integer(year)]

#---------------------------
# Heritage ReEDS

dmd.hreeds = remove.factors(setDT(rgdx.param("//nrelqnap01d/ReEDS/FY17-Standard Scenarios-WJC-90699d9/StandardScenarios2017/Mid_Case/gdxfiles/CONVqn.gdx", 
                              "CONVqmnallyears",
                               names=c("tech", "ba", "temp.year", "temp.value"),
                               compress=T, squeeze=F)))[tech == "reqt"]

dmd.hreeds[, temp.year := as.integer(temp.year)]

dmd.hreeds = CJ.table(dmd.hreeds, data.table(year = 2010:2050))[year - temp.year > -1 & year - temp.year <= 1]

dmd.hreeds[, temp.value2 := shift(temp.value), by = .(ba)]

dmd.hreeds = dmd.hreeds[, .(ba, year, ReEDS1.0 = (temp.value + temp.value2)/2)]

#########################################################
################### DATA MANIPULATION ###################
#########################################################

#---------------------------
# 

res.dmd.use1.div = inner_join(res.dmd.use1, geo.map)
res.dmd.use1.div = res.dmd.use1.div[, .(ReEDS2.0 = sum(ReEDS2.0)/1e6), 
                                    by = .(cens.div.name, year, end.use)]

res.dmd.use1.nat = res.dmd.use1.div[, .(ReEDS2.0 = sum(ReEDS2.0)), 
                                    by = .(year, end.use)]

#---------------------------
# 

dmd.sec1.nat = dmd.sec1[, .(ReEDS2.0 = sum(ReEDS2.0)/1e6), by = .(sector, year)]

dmd.sec2.nat = dmd.sec2[, .(NEMS = sum(NEMS)/1e6), by = .(sector, year)]

dmd.sec.aeo.nat = dmd.sec.aeo[, .(AEO2017 = sum(AEO2017)/1e6), by = .(sector, year)]

dmd.sec.nat = inner_join(inner_join(dmd.sec1.nat, dmd.sec2.nat), dmd.sec.aeo.nat)

dmd.sec.nat = melt(dmd.sec.nat, id.vars = c("sector", "year"),
                       variable.name = "scenario", value.name = "dmd",
                       variable.factor = F)

dmd.sec.nat[scenario == "ReEDS2.0", scenario := "ReEDS2.0 w/ own ref prices"]
dmd.sec.nat[scenario == "NEMS", scenario := "ReEDS2.0 w/ AEO ref prices"]
dmd.sec.nat[scenario == "AEO2017", scenario := "AEO2017 levels"]

#---------------------------
# 

dmd.st1 = inner_join(dmd.sec1, geo.map)
dmd.st2 = inner_join(dmd.sec2, geo.map)
dmd.hreeds.st = inner_join(dmd.hreeds, geo.map)

dmd.st1 = dmd.st1[year %in% c(2030,2050), .(ReEDS2.0 = sum(ReEDS2.0)/1e6), by = .(state.abb, year)]
dmd.st2 = dmd.st2[year %in% c(2030,2050), .(NEMS = sum(NEMS)/1e6), by = .(state.abb, year)]
dmd.hreeds.st = dmd.hreeds.st[year %in% c(2030,2050), .(ReEDS1.0 = sum(ReEDS1.0)/1e6), by = .(state.abb, year)]

dmd.st = inner_join(inner_join(dmd.st1, dmd.st2), dmd.hreeds.st)

dmd.st = melt(dmd.st, id.vars = c("state.abb", "year"),
              variable.name = "scenario", value.name = "dmd",
              variable.factor = F)

dmd.st[scenario == "ReEDS2.0", scenario := "ReEDS2.0 w/ \n HReEDS ref prices"]
dmd.st[scenario == "NEMS", scenario := "ReEDS2.0 w/ \n AEO ref prices"]
dmd.st[scenario == "ReEDS1.0", scenario := "Heritage ReEDS"]

#########################################################################
################### END-USE AND CENSUS DIVISION PLOTS ###################
#########################################################################


#---------------------------
# 

png(paste("outputs/graphics/dmd-use-div.png", sep=""),
    width=single.w.mult*ppi, height=single.h.mult*ppi, res=ppi)

ggplot(res.dmd.use1.div,
       aes(x = year, y = ReEDS2.0, fill = end.use)) +
  geom_area(position = 'stack') + facet_wrap(~ cens.div.name, nrow = 3) +
  theme.main +
  scale_x_continuous("Year") + scale_y_continuous("Consumption [TWh]", limits = c(0, NA)) +
  ggtitle("Residential consumption by end-use and Census division")

dev.off()

png(paste("outputs/graphics/dmd-use-nat.png", sep=""),
    width=single.w.mult*ppi, height=single.h.mult*ppi, res=ppi)

ggplot(res.dmd.use1.nat,
       aes(x = year, y = ReEDS2.0, fill = end.use)) +
  geom_area(position = 'stack') +
  theme.main +
  scale_x_continuous("Year") + scale_y_continuous("Consumption [TWh]", limits = c(0, NA)) +
  ggtitle("National residential consumption by end-use")

dev.off()

########################################################################
################### REFERENCE PRICE COMPARISON PLOTS ###################
########################################################################


#---------------------------
# 

png("outputs/graphics/ref-price-comp.png",
    width=single.w.mult*ppi, height=single.h.mult*ppi, res=ppi)

ggplot(dmd.sec.nat, aes(x = year, y = dmd, color = scenario)) +
  geom_line(size=linesize) + facet_wrap(~ sector, nrow = 1)  + 
  theme.main +
  scale_x_continuous("Year") + scale_y_continuous("Consumption [TWh]", limits = c(0, NA)) +
  ggtitle("National electricity consumption by sector")

dev.off()

######################################################################
################### REEDS VERSION COMPARISON PLOTS ###################
######################################################################

#---------------------------
# 

png(paste("outputs/graphics/reeds-comp.png", sep=""),
    width=single.w.mult*ppi, height=single.h.mult*ppi, res=ppi)

ggplot(dmd.st,
       aes(x = year, y = dmd, fill = scenario)) +
  geom_bar(stat = 'identity', position=position_dodge()) + 
  facet_wrap(~ state.abb, nrow = 8, scales = "free_y") +
  theme.main +
  scale_x_continuous("Year", breaks = c(2030, 2050)) + scale_y_continuous("Consumption [TWh]", limits = c(0, NA), 
                                                                          breaks = pretty_breaks(n=3)) +
  ggtitle("Electricity consumption by state")

dev.off()

########################################################
################### LOAD OUTPUT DATA ###################
########################################################


#---------------------------
# 

res.dvc.cons = inner_join(res.dvc.cons.mdl, res.dvc.cons.ref)[, pct.dev := 100*(res.dvc.cons.mdl-res.dvc.cons.ref)/res.dvc.cons.ref]
res.cons = inner_join(sec.cons.mdl[sector == "res"], res.cons.ref)[, pct.dev := 100*(ReEDS-AEO2017)/AEO2017]

res.cons.plot = melt(res.cons[, sector := NULL], id.vars = c("year"), variable.name = "source")
res.cons.plot[, year := as.numeric(levels(year))[year]]

# chk = res.dvc.cons.ref[, .(res.cons.ref = sum(res.dvc.cons.ref)), by = .(year)]
# chk = res.dvc.cons.mdl[, .(res.cons.mdl = sum(res.dvc.cons.mdl)), by = .(year)]

png("outputs/graphics/ref-vs-mdl-dmd.png",
    width=single.w.mult*ppi, height=single.h.mult*ppi, res=ppi)

ggplot(res.cons.plot, aes(x = year, y = value, color = source)) +
  geom_line(size=linesize) + 
  theme.main +
  scale_x_continuous("Year") + scale_y_continuous("Consumption [TWh]", limits = c(0, NA)) +
  ggtitle("National residential electricity consumption")

dev.off()