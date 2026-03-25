# Retail rate module

This module can be used after finishing a ReEDS run to calculate retail electricity rates by state and year,
where each state is served by its own investor-owned utility (IOU).
(This section will be expanded once the documentation is written.)

## Usage

* `cd` to the REEDS-2.0/postprocessing/retail_rate_module directory
* Run the retail_rate_calculations.py script, with the name of a run folder as a required argument input. For example:
    * `D:\username\ReEDS-2.0\postprocessing\retail_rate_module> python retail_rate_calculations.py v20200806_retailtest_MidCase`

## Outputs

All outputs are written to the `outputs/retail/` folder within the provided run folder. Outputs include:
* `retail_rate_components.csv`: All monetary values are in 2004 dollars. To obtain the retail rate, divide the sum of the cost columns by the 'retail_load' column.
* `costs_over_time.html`: Summary plots for national rates.

## Caveats
* The plotting portion of the script will currently fail if technologies are built that are not in the `map_i_to_tech.csv` file. The main `retail_rate_components.csv` file will still be produced as usual; this error only affects the production of the `costs_over_time.html` summary plots.
