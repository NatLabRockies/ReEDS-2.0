## Hourlize
This code processes hourly resource and load data into ReEDS inputs. The vision is for this script to allow maximum flexibility
temporally and spatially.

There are two main files, *resource.py* and *load.py*, which share a common configuration file, *config.py*,
with separate sections for resource, load, and shared configuration.

To run, simply run `python resource.py` or `python load.py` from within the root folder, after making sure that
the paths in *config.py* are correct.

### Resource Logic (resource.py)
* The main inputs are reV outputs for a given reV scenario:
   * a supply curve file for a given technology, with rows for each resource, characterized by a given capacity and transmission cost (*sc_path* in *config.py*).
   * A set of hourly generation profiles, one for each row of the supply curve file (*profile_path*). Note that PV has mulitple generation profiles per row.
1. The supply curve is filtered if necessary, based on *filter_cols*.
1. A 'region' column is added to the supply curve and filled with the selected regionality (*reg_out_col* in *config.py*).
1. If we have minimum capacity thresholds for the supply curve points, these are applied to further filter the supply curve.
1. A 'class' column is added and filled with the associated class of each row (*class_path* in *config.py*).
1. A 'bin' column is added and filled with the associated bin of each row (*bin_...* in *config.py*).
1. An aggregated supply curve outputs is created with capacity, cost, and distance columns for each region+class+bin.
1. The hourly generation profiles are gathered, and averages and representative profiles are selected for each region+class.
1. Based on the selected representative profiles, we calculate capacity factor means and standard deviations for each region+class.
1. The supply curve, profiles, and performance characteristics are sent to a new folder in *out/*.
* Current inputs and outputs are stored here: `\\nrelnas01\ReEDS\Supply_Curve_Data\`


### Load Logic (load.py)
* Hourly PLEXOS region load data is first converted into ReEDS BA-level data by *plexos_to_reeds/plexos_to_reeds.py*
   * See *plexos_to_reeds/README.md* for more details
1. If specified, we reduce the hourly data to one year.
1. If specified, we remove the final day from leap years.
1. If specified, we shift the data into local time of each BA.
1. If specified, we calibrate each year of hourly data to EIA 2010 load data by state combined with load participation factors by BA. These load participation factors are from heritage ReEDS load inputs, which I believe were derived from Ventyx 2006 county-level load data.
1. For each BA we calculate average load by timeslice and peak load by season.
1. The load profiles, means by timeslice, and peaks by season are sent to a new folder in *out/*
* Current inputs and outputs are stored here: `\\nrelnas01\ReEDS\Supply_Curve_Data\LOAD\`


See comments in those files for more information.
