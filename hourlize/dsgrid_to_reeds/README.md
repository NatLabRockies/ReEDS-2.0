# dsgrid to ReEDS

## Overview
This script produces data ingestible into load.py from a dsgrid output parquet file.

## Steps
1. Coordinate with Ashreeta Prasanna, Elaine Hale, Dan Thom, or another member of the dsgrid team to get dsgrid load data in parquet format.
    - They will likely use a dsgrid project, e.g. https://github.com/dsgrid/dsgrid-project-loadsplice or https://github.com/dsgrid/dsgrid-project-IEF. For `dsgrid-project-loadsplice`, we may need to initially run `hourlize/dsgrid_to_reeds/eer_make_parquet.py` to create the required input for the dsgrid project.
1. Update `input_file` in `hourlize/dsgrid_to_reeds/dsgrid_to_reeds.py` and run the file to convert the dsgrid parquet file into a CSV file that is ingestible into load.py. The CSV output is saved as `load_hourly_ba_EST_...csv` in the current working directory.
1. Update `load_source` in `hourlize/inputs/configs/config_base.json` to point to the output of the prior step.
1. Change directory into `hourlize` and run `python run_hourlize.py load`.
1. Gather outputs from the new directory in `hourlize/out/`.
1. Copy new h5 load file to `inputs/load/` and name it `[somename]_load_hourly.h5`.
1. Allow new load to be used by adding `[somename]` to the `Choices` column for the `GSw_LoadProfiles` switch in `cases.csv`.
1. Use the new load trajectory in a run!