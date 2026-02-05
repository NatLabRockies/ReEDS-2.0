# -*- coding: utf-8 -*-
"""
@author: pbrown
@date: 20200812 11:56

Inputs
------

Outputs
-------

Notes
-----
Copied from ReEDS-1.0:
* PTS 04/25/14
    * POL37 is a warming scenario consistent with GHG stabilization at 3.7 W/m2.
    POL45 is the same but at 4.5 W/m2. Both are climate sensitivity of 3.
    * POL37 is an RCP3.7 (stabilization at 3.7W/m2 of radiative forcing by 2100) scenario
    * POL45 is an RCP4.5 (stabilization at 4.5W/m2 of radiative forcing by 2100) scenario
    * both include temperature changes and carbon caps consistent with that scenario
    (IGSM and GCAM-derived)
    * both POL scenarios override other CO2 caps (even if CO2switch is OFF).
* PTS 04/25/14
    * CS3REF and CS6REF are scenarios with no carbon signal, so lots of warming.
    The CS# is the climate sensitivity in degrees of warming per doubling of
    GHG concentration (from preindustrial levels).
    * CS3REF and CS6REF are no-policy (lots of warming) scenarios, with climate
    sensitivities of 3 and 6 degree increase for a doubling of emissions
* PTS 04/25/14
    * all inputs (temperature, carbon cap targets) are derived from IGSM-CAM and GCAM scenarios.
* SMC 08/18/14
    * New scenarios added based on CMIP5 climate data. These three scenarios include
    temperature impacts on load, generation, and transmission as well as water availability
    impacts on thermal cooling.  There are no changes to hydropower water availability.
    * MODNONE entails moderate warming and no changes to precipitation (water availability).
    * HOTWET entails significant warming and largely increased precipitation (water availability).
    * HOTDRY entails significant warming and largely decreased precipitation (water availability).
* YS 04/18/17
    * CIRA2.0 & NEWS Scenarios: Used data from CMIP5 Climate models, with a combination of
    different Representative Concentration Pathway (RCP)
    * Climate models for CIRA2.0: CanESM2, CCSM4, GISS-E2-R, HadGEM2-ES, MIROC5
    (HadGEM shows most climate impacts while GISS shows least)
    * Climate models for NEWS: HadGEM2-ES, GFDL-ESM2M, IPSL-CM5A, MIROC-ESM-CHEM,NorESM1-M
    * RCP Definition: four (2.6, 4.5, 6.0, 8.5 W/m2) greenhouse gas concentration
    (not emissions) trajectories adopted by IPCC AR5; 8.5 indicates super warm scenarios
    and 4.5 is a moderate warming scenario
    * Data includes temperature, heating/cooling degree days (HDDCDD) for calculating
    change in load, water availability & distribution adjustment factors,
    and hydro power adjustment factors
    * For CIRA2.0 work, two methods to calculate HDDCDD data:
    AT indicates using absolute temperature, and HI indicates DD data are based on heat index
    and temperature, and are adjusted for humidity. AT method was used for CIRA2.0 work

Sources
-------
Method derived from:
[1] Sullivan, P.; Colman, J.; Kalendra, E. "Predicting the response of electricity load to
climate change". Technical Report, National Renewable Energy Laboratory,
NREL/TP-6A20-64297. https://www.nrel.gov/docs/fy15osti/64297.pdf
"""

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import pandas as pd
import os
import sys
import argparse
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
# Time the operation of this script
tic = datetime.datetime.now()

#%% Parse arguments
parser = argparse.ArgumentParser(description="Format and write climate inputs")
parser.add_argument('reeds_path', help='ReEDS directory')
parser.add_argument('inputs_case', help='output directory')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing ###
# reeds_path = os.path.expanduser('~/github/ReEDS-2.0/')
# inputs_case = os.path.expanduser(
#     '~/github/ReEDS-2.0/runs/v20201208_beyond2050_Climate2100step5/inputs_case/')

#%%#################
### FIXED INPUTS ###

verbose = 2
### Set rounding precision
decimals = 5
### Link between peak-timeslices and parent-timeslices (in case we add more peak-slices)
slicetree = {'h17': 'h3'}

#%% Set up logger
log = reeds.log.makelog(
    scriptname=__file__,
    logpath=os.path.join(inputs_case,'..','gamslog.txt'),
)
print('Starting climateprep.py')

#%% Inputs from switches
sw = reeds.io.get_switches(inputs_case)
climatescen = sw.climatescen
climateloc = sw.climateloc
GSw_ClimateWater = int(sw.GSw_ClimateWater)
GSw_ClimateHydro = int(sw.GSw_ClimateHydro)
GSw_ClimateDemand = int(sw.GSw_ClimateDemand)
GSw_LoadProfiles = sw.GSw_LoadProfiles
startyear = int(sw.startyear)
endyear = int(sw.endyear)
GSw_ClimateStartYear = int(sw.GSw_ClimateStartYear)

if climateloc.startswith('inputs'):
    climateloc = os.path.join(reeds_path, *(os.path.split(climateloc)))
else:
    pass

### Get the directory for climate inputs
climatedir = os.path.join(climateloc, climatescen)

### Get modeled years
modelyears = pd.read_csv(os.path.join(inputs_case,'modeledyears.csv')).columns.astype(int).tolist()
allyears = list(range(startyear, endyear+1))
### Get reeds_data_year
reeds_data_year = 2012

### Get valid regions
val_r_all = pd.read_csv(
    os.path.join(inputs_case, 'val_r_all.csv'), header=None).squeeze(1).tolist()

### Get some other fixed inputs
scalars = reeds.io.get_scalars(inputs_case)
distloss = scalars.distloss

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

#########################################
#    -- Cooling water, Hydropower --    #
#########################################

def readwrite(
    infile, inputs_case=inputs_case, decimals=decimals, endyear=endyear):
    """
    Load modifiers, interpolate to all years, write GAMS-readable csv.
    """
    ### Indicate which indices to use
    index = {
        'UnappWaterMult': ['wst','r','szn'],
        'UnappWaterSeaAnnDistr': ['wst','r','szn'],
        'UnappWaterMultAnn': ['wst','r'],
        'hydadjann': ['r'],
        'hydadjsea': ['r','szn'],
    }
    ### Load the climate scenario data
    dfin = pd.read_csv(os.path.join(inputs_case, infile+'.csv'))
    
    ### Put in GAMS-readable format
    dfout = pd.pivot_table(dfin, values='Value', index=index[infile], columns=['t'])
    ### If data end before endyear, create a column for endyear so we can forward-fill to it
    lastdatayear = max([int(y) for y in dfout.columns])
    if endyear > lastdatayear:
        dfout[endyear] = dfout.loc[:,lastdatayear]
    ### If data start after 2010, add a column for 2010
    if (2010 not in dfout.columns) and all(dfout.columns.values > 2010):
        ### For UnappWaterSeaAnnDistr we give the new values directly rather than as a ratio,
        ### so we backfill with the earliest available data
        if infile == 'UnappWaterSeaAnnDistr':
            dfout[2010] = dfout.iloc[:,0]
        ### Otherwise we fill with 1 (i.e. no change). Note that since we interpolate to the
        ### next value, the years between 2010 and the first year with data will not be 1.
        else:
            dfout[2010] = 1.
        ### Move 2010 column to the front of the dataframe
        dfout.sort_index(axis=1, inplace=True)
    ### Interpolate to missing years
    dfinterp = (
        dfout
        ### Switch column names from integer years to timestamps
        .rename(columns={c: pd.Timestamp(str(c)) for c in dfout.columns})
        ### Add empty columns at year-starts between existing data (mean doesn't do anything)
        .resample('YS', axis=1).mean()
        ### Interpolate linearly to fill the new columns
        .T.interpolate('linear').T
    )
    dfout = (
        ### Switch back to integer year column names
        dfinterp.rename(columns={c: c.year for c in dfinterp.columns})
        ### Drop extra data after the model end year
        .loc[:,:endyear]
    )
    ### Write it to output folder
    dfout.round(decimals).to_csv(os.path.join(inputs_case, 'climate_'+infile+'.csv'))
    return dfout


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if GSw_ClimateWater:
    print('Writing annual and seasonal water climate multipliers')
    for infile in ['UnappWaterMult','UnappWaterMultAnn','UnappWaterSeaAnnDistr']:
        readwrite(infile=infile)

if GSw_ClimateHydro:
    print('Writing annual and seasonal hydro climate multipliers')
    for infile in ['hydadjann','hydadjsea']:
        readwrite(infile=infile)

if not any([GSw_ClimateWater,GSw_ClimateHydro,GSw_ClimateDemand]):
    print("All climate switches are off.")

reeds.log.toc(tic=tic, year=0, process='input_processing/climateprep.py',
    path=os.path.join(inputs_case,'..'))

print('Finished climateprep.py')
