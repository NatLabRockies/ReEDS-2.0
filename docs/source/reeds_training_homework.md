---
orphan: true
---
### Task 1: Perform a ReEDS run with the default settings in ERCOT at the BA and county resolutions
#### Run the model
1. Create your own branch off main and name it XX_homework where XX are your initials

2. Navigate to the folder where the repo has been cloned on your local machine

3. Open the cases_spatialflex.csv file

4. Change the 'ignore' row value to be 1 for all columns except ERCOT_county which you can either set to 0 or leave blank

5. Add a new column with 'ERCOT_BA' in row 1. 
   - Copy the contents of rows 2-6 from the ERCOT_county column
   - Replace 'county' with 'ba' in row 5 (GWs_RegionResolution)
   - Save cases_spatialflex.csv in the ReEDS-2.0 folder (you can overwrite the existing file)

6. Open VS Code
   - Open the folder where your repo is located (File -> Open Folder -> navigate to ReEDS-2.0 folder)
   - Open a new terminal and activate the reeds2 environment

7. Start a new run
   - `python runbatch.py`
   - when prompted for case file name, enter 'spatialflex'
   - when prompted for how many simultaneous runs you would like to execute, enter 2
   - The 'ERCOT_county' and 'ERCOT_BA' runs should start   


#### Review the results
1. Navigate to 'ReEDS-2.0/runs/{your run name}/outputs/reeds-report' and open 'report.html'
2. Learn to create your own plots of the results using bokehpivot
   - See [Bokeh Pivot](../postprocessing_tools.md#bokehpivot)

#### Create an informal slide deck
Create an informal slide deck with the following results: 
   - Stacked bar chart of total installed capacity in 2030 
      - Include a stacked bar chart of the differences
   - Stacked bar chart of total installed firm capacity in 2030
   - Stacked bar chat of generation in all modeled years
   - Stacked bar chart of total system costs discounted 
   - Plots of the locational capacity build out by technology (maps of where capacity is located) 
   - Plots of the curtailment rates 


### Task 2: Perform a ReEDS run with enforced decarbonization at the BA resolution in the Western Interconnection.
#### Run the model
1. Ensure you are on your XX_homework branch, then navigate to the folder where the repo has been cloned on your local machine

2. Open the cases_spatialflex.csv file

3. Add a new column with 'Western_BA_Decarb' in row 1
   - Copy the contents of rows 2-6 from the ERCOT_county column
   - Replace 'county' with 'ba' in row 5 (GSw_RegionResolution)
   - Replace 'ercot' with 'western' in row 4 (GSw_Region)
   - Add 2 additional rows, populating column A with 'GSw_AnnualCapScen' and 'GSw_AnnualCap' in rows 7 and 8 respectively
   - Under the 'Western_BA_Decarb' column, populate these rows with 'start2023_100pct2035' and '1' respectively (leave these rows blank in all other columns)

4. Change the ‘ignore’ row value to be 1 for all columns except ‘Western_BA_Decarb’ which you can either set to 0 or leave blank

5. Save cases_spatialflex.csv in ReEDS-2.0 folder

6. Open VS Code
   - Open the folder where your repo is located (File -> Open Folder -> navigate to ReEDS-2.0 folder)
   - Open a new terminal and activate the reeds2 environment

7. Start a new run
   - `python runbatch.py`
   - when prompted for case file name, enter 'spatialflex'
   - The 'Western_BA_Decarb' run should start

#### Create an informal slide deck
Create an informal slide deck with the following results: 
   - Stacked bar chart of total installed capacity in 2030 
      - Include a stacked bar chart of the differences
   - Stacked bar chart of total installed firm capacity in 2030
   - Stacked bar chat of generation in all modeled years
   - Stacked bar chart of total system costs discounted 
   - Plots of the locational capacity build out by technology (maps of where capacity is located) 
   - Plots of the curtailment rates 