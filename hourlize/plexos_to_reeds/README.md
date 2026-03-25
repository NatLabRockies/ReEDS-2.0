## PLEXOS region to ReEDS BA hourly load data
*plexos_to_reeds.py* is a script for converting hourly PLEXOS region load data to hourly ReEDS BA load data. The current inputs and outputs are here: `\\nrelnas01\ReEDS\Supply_Curve_Data\LOAD\2020_Update\plexos_to_reeds`

### The full data pipeline that produces the input file to *plexos_to_reeds.py*:
1. The ultimate source is a plexos zonal 5 min load, 2002-2017, UTC, grown to 2050.
   * This data was apparently derived from a combination of FERC form 714 and ISO-specific hourly (or mostly hourly) data. 5 min data is simulated. Finally, this data was "grown" to 2050 based on region-specific growth factors.
   * All plexos regions have complete set of data 2007-2013 EST (except first couple hours in 2017 in a few regions)
   * There are indications that the load data in certain regions of this file might have shifted because of daylight savings.
1. Some regions are added/altered/removed:
   * ACDC regions are filled with 0 load
   * For NewFoundland the data is copied from QUEBEC and multiplied by 0.0502. This was before before the ungrowing because it used a different set of growth factors.
   * The NOVA_SCOTIA data was ungrown with the rest and then added to NEW_BRUNSWICK before output.
1. The data is ungrown 2012 using the region-dependent growth factors.
   * We apparently can’t ungrow to the native, pre-grown loads.
1. A script is used to “clean” the 5 min data by looking at hour-to-hour differences, and when there are 4 consecutive hour-to-hour changes of greater than 50%, interpolating between two hours before and 1 hour after.
   * This could be simplified by just using hourly data, since that is the resolution of the source data (FERC and ISO) anyway.
1. The data is reduced to hourly data.
1. The result is hourly PLEXOS region load data in EST.
   * This file is here: https://github.nrel.gov/PCM/griddb/blob/master/data/NARIS/h5_2007-2014_ungrown_2012_1hr_EST.csv
   * See the README for more info here: https://github.nrel.gov/PCM/griddb/blob/master/data/NARIS/readme.md

### Basic logic in *plexos_to_reeds.py*
1. The output of the above process, *h5_2007-2014_ungrown_2012_1hr_EST.csv* is read in as an input
1. Data is reduced to 2007-2013 only.
1. Load participation factors (I believe from Energy Visuals) are used to map the data to PLEXOS nodes. WECC uses seasonal factors, ERCOT uses monthly factors, and EI simply
assumes that PLEXOS region data is split evenly between the associated nodes.
1. The PLEXOS nodes are mapped directly to ReEDS BAs based strictly on location of the nodes and BA boundaries.
1. This results in load participation factors between PLEXOS regions and ReEDS BAs. Hourly ReEDS BA-level data is then produced using the load participation factors
1. The resulting file is *outputs/load_hourly_ba_EST.csv*
