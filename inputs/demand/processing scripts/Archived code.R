# Plot energy consumption by end-use

data.plot = nems.serv.cons[, .(energy.cons = sum(energy.cons)),
                           by = .(nems.dev.class, nems.fuel.set, nems.use.set, 
                                  cens.div, nems.year)]

png(paste("Figures/Energy consumption by device.png", sep=""),
    width=3000, height=3600, res=300)

ggplot(data = data.plot[nems.fuel.set == "EL"],
       aes(x = nems.year, y = energy.cons, fill = nems.dev.class)) +
  geom_area(position='stack') + facet_grid(~ cens.div)

dev.off()


######################################################################
################### CALCULATE NEW DEVICE PURCHASES ###################
######################################################################



#---------------------------
# Remove base stock from device tabulations in each year

# extract full NEMS stock
nems.stock = nems.energy.cons[, .(nems.dev.class, nems.class.name,
                                  cens.div, bldg.type, nems.year, total.dev)]

# merge in remaining base stock quantities
nems.stock = merge(nems.stock, 
                   nems.base.stock[, .(nems.dev.class, nems.class.name,
                                       cens.div, bldg.type, nems.year, rem.stock)])

# !!!!!!!! remove double-counted devices (should be corrected with new NEMS data)
nems.stock = unique(nems.stock)

# calculate number of non-base stock devices
nems.stock[, non.base.dev := total.dev - rem.stock]

#---------------------------
# Calculate new purchases in each model year

# cross-join to get to get all combinations of years and vintages
nems.vint = CJ.table(nems.stock[, .(nems.dev.class, nems.class.name,
                                    cens.div, bldg.type, nems.year, non.base.dev)], 
                     data.table(nems.year.vint = 2010:2050))

# calculate age for each year/vintage pair, remove negative entries
nems.vint[, age := nems.year - nems.year.vint]
nems.vint = nems.vint[age >= 0]

# merge in survival rates
nems.vint = join(nems.vint, nems.surv.rate[, .(nems.dev.class, age, surv.rate)])

# initialize new purchase and stock variables
nems.vint[, c("new.purch", "stock") := list(numeric(), numeric())]
nems.vint[nems.year == 2010, new.purch := non.base.dev]

# loop over years to calculate new purchases
for(i in 2011:2050){
  
  # assign previous year's purchases to temporary stock column, then apply survival rate
  # to get number of previous year vintage remaining in each model year
  nems.vint = nems.vint[, .(nems.year, non.base.dev, nems.year.vint, age, surv.rate, 
                            new.purch, stock, stock.temp = .SD[nems.year == i-1, new.purch]),
                        by = .(nems.dev.class, nems.class.name, cens.div, bldg.type)
                        ][nems.year.vint == i-1, stock := stock.temp*surv.rate]
  
  # add up stock from all previous vintages to create a temporary cumulative stock variable, then
  # subtract that stock from non-base stock to get current year's purchases
  nems.vint = nems.vint[, .(nems.year, non.base.dev, nems.year.vint, age, surv.rate, new.purch,
                            stock, cum.stock.temp = sum(.SD[nems.year == i & nems.year.vint < i, stock])),
                        by = .(nems.dev.class, nems.class.name, cens.div, bldg.type)
                        ][nems.year == i, new.purch := non.base.dev - cum.stock.temp
                          ][, cum.stock.temp := NULL]
  
}

# remove extraneous rows to get purchase table
nems.purch = nems.vint[nems.year.vint == 2010, 
                       .(nems.dev.class, nems.class.name, cens.div, bldg.type, nems.year, new.purch)]




write.csv(nems.purch, "NEMS_purchases.csv")

nems.stock[nems.year > 2010, new.purch := 0]


nems.stock[nems.year.vint == 2010, dev.vint := max(new.purch), by = .(nems.dev.class, nems.class.name, cens.div, bldg.type)]
nems.stock

nems.stock[nems.year == 2011, new.purch := non.base.dev]

nems.vint = nems.stock[nems.year == 2010, .(nems.dev.class, nems.class.name, cens.div, bldg.type, temp = new.purch)]

nems.stock[nems.year.vint == 2010, dev.vint := nems.stock[nems.year == 2010, .(nems.class.name, cens.div, bldg.type, new.purch)], 
           by = .(nems.class.name, cens.div, bldg.type)]
nems.stock[, dev.vint := new.purch, by = .(nems.class.name, cens.div, bldg.type, nems.year.vint)]

write.csv(nems.stock, "NEMS_stock_evolution.csv")