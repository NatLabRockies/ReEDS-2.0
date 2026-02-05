# ReEDS-to-Tableau Postprocessing

This directory contains files that facilitate the postprocessing and analysis of ReEDS and ReEDS-to-PLEXOS results in [Tableau](https://www.tableau.com/). Tableau is a commercial software that requires purchase of a license.

You can run `postprocess_for_tableau.py` from the command line to assemble results, metadata, and supporting spatial files from multiple ReEDS (and optionally, ReEDS-to-PLEXOS) scenarios into a single Tableau extract (Tableau's proprietary .hyper format, which is basically a self-contained SQL database), which is optimized for use within Tableau. 

`postprocess_for_tableau.py` creates pivot tables of ReEDS outputs specified in the `PIVOT_DEFS` dictionary within `pivot_definitions.py`. You can specify which collections of pivot tables you want to include in your .hyper output file with the `-p` flag. Most of the outputs in each pivot table are simply the names of csvs created by `e_report_dump.py`, for which the column formats and the intended names of each as they'll appear in Tableau are defined in `tables_to_aggregate.csv`. (If running `postprocess_for_tableau.py` throws an error The script assembles the pivot tables and combines them into a single Tableau .hyper extract file containing the pivotted tables for visualization and analysis in Tableau. It also creates a csv version of each pivot table.

Before running this script for the first time, you'll need to install the Tableau Hyper API via pip with:

`pip install tableauhyperapi`


Note that if you're pulling ReEDS-to-PLEXOS results into Tableau, you'll also need to have the [h5plexos](https://github.com/NatLabRockies/h5plexos) package installed.

### Example call:

```bash
python postprocess_for_tableau.py \
    -d '//nrelnas01/reeds/some_dir_containing_runs' \
    -o '//nrelnas01/reeds/some_directory_containing_runs/testbatch_suite' \    
    -s testbatch_refseq,testbatch_carbtax,testbatch,carbcap \
    -p standard,plexos
```
Run python postprocess_for_tableau.py --help for descriptions of the flags above and their expected arguments or simply look at the calls to argparse within in the script.

Alternatively to explicitly specifying the names of scenarios directly with the `-s` flag as in the example above, you can automatically include all completed ReEDS scenarios by including the `-a` flag instead.

### Troubleshooting

`postprocess_for_tableau.py` creates a log file in the output directory called `tableau.txt` and redirects stdout and stderr there. Some error handling is present in the script, but if you encounter an error, the culprit is often an incorrect set of column definitions in `tables_to_aggregate.csv`. Sometimes the names of outputs and the order of sets they're based on differ across branches of ReEDS. If columns you've defined in a pivot table within `pivot_definitions.py` aren't appearing in the .hyper output, check that they're correctly specified (including the correct path) in `tables_to_aggregate.csv` and `pivot_definitions.py`. 

Often, it's best to run the script line-by-line in an IDE to diagnose and fix problems. One place to look is the long series of `elif` statements that define custom operations for any csvs defined in `pivot_definitions.py` that don't follow the simple pattern of joining one new column to a pivot table per csv.

You'll notice a bunch of assignments to `col_defs` in `postprocess_for_tableau.py`. All dimensions and attributes (i.e. columns of tables) in Tableau must have data types defined, and we specify those to in a list with `col_defs`. These column types are passed to the `tableauhyperapi` function along with the location of the pivot table csv that we've just created in order for the pivot csv to be written into the Tableau .hyper file (which is really a SQL database under the hood). Those types are defined for all index sets in `column_types`, and the value column of csvs are by default assumed to be of type `SqlType.double()`. Where we need a different type, like a date or a geography for mapping, we define the `SqlType` explicitly in the logic within `main()`.

### Adding new outputs to the Tableau postprocessing

Say you've got a new output csv that's created in `e_report.gms` and `e_report_dump.py`, and you want to export it into Tableau, and it's indexed on `(i,r,t)`. First, add it as a row in `tables_to_aggregate.csv`, along with its relative location within a ReEDS scenario directory, the name of the column as you'd like it to appear in Tableau, and the sets it's indexed on, in the correct order. These index names tell the script the header names of each column in the csv, and they appear in Tableau as defined in `column_types` within `postprocess_for_tableau.py`. If you're adding a new set name, add the set name and the name you'd like to appear in Tableau to that `column_types` dictionary.

Next, you'd add the csv name as defined `tables_to_aggregate.csv` to the `csvs` list for whichever pivot tables you'd like it to appear in within `pivot_definitions.py`. You must also add a corresponding entry to `operation` to tell the script how to aggregate any index columns that appear in your csv beyond the index columns defined for that pivot table in `id_columns`. Entries of `sum` or `mean` will aggregate across any extra columns accordingly. For example, we could export our `(i,r,t)`-indexed csv to the `scen_r_t` pivot table with the `operation` set to `sum`, which would tell the script to eliminate the `i` column by summing across all `i`. You could also include any string in `operation` and then use that to explicitly define a custom operation within the series of `elif`s in the `main()` block of `postprocess_for_tableau.py`.


## Tableau Analysis Templates

There's also a Tableau template in this directory: `standard_reeds_analysis.twb`. A `.twb` file includes the structure of a Tableau notebook (i.e. the structure worksheets and dashboards), but not the data it refers to. The template is set up to connect to a `.hyper` extract created using this workflow. This way, you can open up `standard_reeds_analysis.twb` in Tableau, connect to the `.hyper` data extract you've created using the workflow above, and it will populate the sheets with your results. Note that once you've done that, you can always save your Tableau notebook as a `.twbx`, which packages both the `twb` and the `.hyper` into one file, making sharing your results easier.

## ReEDS-to-PLEXOS

You can pull PLEXOS results into their own pivot tables and add them to the Tableau extract simply by including the "plexos" pivot table collection in your call to `postprocess_for_tableau.py`. The script is currently set up to identify each different directory within `<scenario directory>/plexos_export/solutions` as its own PLEXOS scenario, which will be differentiated by its name in a "PLEXOS Scenario" column in the Tableau pivot tables that are created.

## Geospatial Mapping in Tableau

Several pivot tables containing geometry/geography columns are created in the `standard` pivot table collection. These can be used to create choropleth maps, etc. within Tableau. `region_mapping` contains the mapping heirarchy of ReEDS regions and BAs, and `line_mapping` contains straight-line paths between each BA and the 25 BAs closest to it. The pivot tables pull from csvs in `inputs/shapefiles` that each contain a WKT-formatted geometry column in the EPSG:4326 format.

## Dollar-year Adjustments

Just as a note, `postprocess_for_tableau.py` converts any cost to the dollar year specified with the input argument `-dy <year>`, wherever a column is titled with the string "2004$".