# hourly_process.py

## Switches
* `GSw_HourlyNumClusters` specifies the maximum number of representative periods.
* Two other switches, `GSw_HourlyPeakLevel` and `GSw_HourlyMinRElevel`, indicate additional "stress periods" that can be added. They're both set to "interconnect" by default, so for the US they add the 3 peak-load days, 3 minimum-wind days, and 3 minimum-PV days by interconnect, resulting in 33+9=42 by default if `GSw_HourlyNumClusters`=33.
* When using `GSw_HourlyClusterAlgorithm=optimized` (the default), then depending on the setting of `GSw_HourlyClusterRegionLevel` there will be a maximum number of days it needs to reproduce the distribution of load/pv/wind. When `GSw_HourlyClusterRegionLevel=transreg` (the default), there are 11 regions and 3 features, so it needs ~33 days to reproduce the distribution (like an eigenvalue problem).
    * So turning up `GSw_HourlyNumClusters` on its own won't increase the temporal coverage. If you want more temporal coverage, the options are:
        * Switch to `GSw_HourlyType=wek`, which increases the length of the periods from 1 day to 5 days. If all the other switches are left at their defaults, switching to `wek` would increase the coverage from 42 days to 5*42=210 days.
        * Reduce `GSw_HourlyClusterRegionLevel` to something smaller than transreg (like `st`), and then increase `GSw_HourlyNumClusters`
        * Switch to `GSw_HourlyClusteAlgorithm=hierarchical` and then increase `GSw_HourlyNumClusters` (although that's less desirable, because hierarchical clustering doesn't do as good of a job of reproducing the actual spatial distribution of CF and load)
        * Switch to `Gsw_HourlyType=year`. Although if you're running for the whole US you'll need to turn on region aggregation (`GSw_AggregateRegions=1` and `GSw_HierarchyFile` in [`agg0`, `agg1`, or `agg2`]) for it to solve.
* `GSw_HourlyClusterAlgorithm`
    * If set to 'hierarchical', then hierarchical clustering is used via
        ```python
        sklearn.cluster.AgglomerativeClustering(
            n_clusters=int(sw['GSw_HourlyNumClusters']),
            affinity='euclidean', linkage='ward')
        ```
    * If set to 'optimized', then a two-step custom optimization is performed using the `hourly_repperiods.optimize_period_weights()` and `hourly_repperiods.assign_representative_days()` functions to minimize the deviation in regional load and PV/wind CF between the weighted representative periods and the full year.
    * If set to a string containing the substring 'user', then instead of optimizing the choice of representative periods for this run, we read them from the inputs/variability/period_szn_user.csv file.
        * The scenario name is in the first column, labeled 'scenario'. ReEDS will use rows with the same label as `GSw_HourlyClusterAlgorithm`.
            * So if you want to use the example period:szn map, just set `GSw_HourlyClusterAlgorithm=user`.
            * If you want to specify a different period:szn map, then add your mapping at the bottom of inputs/variability/period_szn_user.csv with a unique scenario name in the 'scenario' column, and set `GSw_HourlyClusterAlgorithm` to your unique scenario name, *which must contain the substring 'user'*. (For example, I could use a mapping called 'user_myname_20230130' by adding my period:szn map to inputs/variability/period_szn_user.csv with 'user_myname_20230130' in the 'scenario' column and setting `GSw_HourlyClusterAlgorithm=user_myname_20230130`.)
            * Make sure the settings for `GSw_HourlyType` and `GSw_HourlyWeatherYears` match your user-defined map. For example, if your 'user_myname_20230130' map includes 365 representative days for weather year 2012, then set `GSw_HourlyType=day` and `GSw_HourlyWeatherYears=2012`.


## Conventions
* Timestamps are formatted as `y{year}d{day of year}h{hour of day}` in hour-ending format in Eastern Standard Time. The numbering of days begins at 1. For example, the hour from 3am-4am on January 3, 2012 would be indicated as `y2012d003h004`.
    * When using representative weks (5-day periods), timestamps are instead formatted as `y{year}w{wek of year}h{hour of wek}`. The numbering of weks begins at 1. In this format, the hour from 3am-4am on January 3, 2012 would be indicated as `y2012w001h052`.
* Representative and stress **periods** (indexed as `szn` within ReEDS) are labeled similarly to timestamps but without the `h{hour of day}` component...
    * *Except stress periods and stress timeslices have an 's' prefix.* So if the time period above showed up as a stress period, it would be labeled as `h=sy2012d003h004` and `szn=sy2012d003` for represntative days (or `h=sy2012w001h052` and `szn=sy2012w001` for representative weks). Stress periods are modeled using different loads and transmission capacities than representative periods, so they need to be indexed separately.


# hourly_writetimeseries.py

## Conventions

## Switches

