###############
#%% IMPORTS ###
import pandas as pd
import numpy as np

#################
#%% PROCEDURE ###

#%% Get historical emissions from EIA
### Parent site: https://www.eia.gov/totalenergy/data/monthly/#environment
dfin = pd.read_csv('https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T11.06')
description = 'Total Energy Electric Power Sector CO2 Emissions'
df = dfin.loc[dfin.Description==description].copy()
nummonths_2022 = df.YYYYMM.astype(str).str.startswith('2022').sum()
### Annual emissions are labeled as YYYY13,
### so complete years of monthly data will have 13 entries
if nummonths_2022 == 13:
    ## Keep the summed value
    dfout = df.loc[df.YYYYMM == 202213].copy()
    print('Reported value for 2022:')
else:
    ## Drop any summed values and keep the 12 most recent monthly values
    dfout = df.loc[
        ~df.YYYYMM.astype(str).str.endswith('13')
    ].sort_values('YYYYMM').tail(12)
    print('Sum of reported values for {}-{}:'.format(dfout.YYYYMM.min(), dfout.YYYYMM.max()))

#%% Final value - copy to inputs/scalars.csv
val = np.around(dfout.Value.astype(float).sum(), 3)
print(f'{val:.3f} {dfout.Unit.unique()[0]}')

# #%% Write it automatically
# import os
# dfwrite = pd.read_csv(
#     os.path.join('..','..','inputs','scalars.csv'),
#     header=None, names=['parameter','value','comment'], index_col='parameter'
# )
# dfwrite.loc['co2_emissions_2022','value'] = val
# dfwrite.to_csv(os.path.join('..','..','inputs','scalars.csv'), header=False)
