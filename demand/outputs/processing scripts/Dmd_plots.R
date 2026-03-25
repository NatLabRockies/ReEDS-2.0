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

###################################################################
################### CREATE TEMPLATE DATA TABLES ###################
###################################################################

#---------------------------
# 

########################################################
################### LOAD OUTPUT DATA ###################
########################################################

# Note: data comes in at the model's native resolution

#---------------------------
# 

data = fread("outputs/data/dmd_outputs.csv")

#---------------------------
# 

dvc.purch = data[param == "dvc.purch"]
dvc.stock = data[param == "dvc.stock"]

#########################################################
################### DATA MANIPULATION ###################
#########################################################

#---------------------------
# 

dvc.purch[, use.cls := paste(end.use, " - ", dvc.cls, sep = "")]
dvc.stock[, use.cls := paste(end.use, " - ", dvc.cls, sep = "")]

#---------------------------
# 

end.use.vec = unique(dvc.purch[, .(end.use)])[[1]]
dvc.cls.vec = unique(dvc.purch[, .(dvc.cls)])[[1]]
use.cls.vec = unique(dvc.purch[, .(use.cls)])[[1]]
inc.lvl.vec = unique(dvc.purch[, .(inc.lvl)])[[1]]

#---------------------------
#

dvc.purch[, inc.lvl := factor(inc.lvl, levels = inc.lvl.vec)]
dvc.stock[, inc.lvl := factor(inc.lvl, levels = inc.lvl.vec)]

#---------------------------
# 

# sum over BAs
dvc.purch.nat = dvc.purch[, .(dvc.purch = sum(value)), by = .(inc.lvl, year, use.cls, end.use, dvc.cls, dvc.opt)]
dvc.stock.nat = dvc.stock[, .(dvc.stock = sum(value)), by = .(inc.lvl, year, use.cls, end.use, dvc.cls, dvc.opt)]

##################################################
################### AREA PLOTS ###################
##################################################

#---------------------------
# 

for(i in use.cls.vec) {
  png(paste("outputs/graphics/dvc-purch-", i,".png", sep=""),
      width=single.w.mult*ppi, height=single.h.mult*ppi, res=ppi)

  p = ggplot(dvc.purch.nat[use.cls %in% i], 
         aes(x = year, y = dvc.purch, fill = dvc.opt)) +
    geom_area(position = 'stack') + facet_wrap(~ inc.lvl, nrow = 4) +
    theme(title = element_text(hjust=.5), 
          axis.text.x = element_text(hjust=.5, angle = 45)) +
    ggtitle(i)
  
  print(p)

  dev.off()
}

for(i in use.cls.vec) {
  png(paste("outputs/graphics/dvc-stock-", i,".png", sep=""),
      width=single.w.mult*ppi, height=single.h.mult*ppi, res=ppi)
  
  p = ggplot(dvc.stock.nat[use.cls %in% i], 
             aes(x = year, y = dvc.stock, fill = dvc.opt)) +
    geom_area(position = 'stack') + facet_wrap(~ inc.lvl, nrow = 4) +
    theme(title = element_text(hjust=.5), 
          axis.text.x = element_text(hjust=.5, angle = 45)) +
    ggtitle(i)
  
  print(p)
  
  dev.off()
}

  


