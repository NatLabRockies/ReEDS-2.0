# Exploding Pivot Charts

## Intro
This python bokeh app creates multiple pivot charts from data. A helpful tutorial is here: https://youtu.be/8Xi59M4bB6I. Note that some of this documentation might be outdated.

## Quickstart for using bokehpivot via command line to build comparison reports
1. See instructions at top of bokehpivot/run_report.py

## Running Bokehpivot Interface (Windows)
1. In the ReEDS repo, simply double click on bokehpivot/launch.bat to launch the tool. This will start a bokeh server in a terminal window and a browser window with an interactive interface.
1. After the tool is launched, go to the *Loading Model data* section below.
1. When done, simply close the terminal window that is running the server.
* If you're curious about the contents of the .bat files, you can open the *Launch.bat* in a text editor. The contents will look like:
  ```
  call bokeh serve . --sh --port 0
  ```
* Here is a breakdown of the contents of *Launch.bat*:
    * `bokeh serve . --sh`: Launch bokeh server and open browser window with the app. See https://docs.bokeh.org/en/latest/docs/user_guide/server.html for more info.
    * `--port 0`: This will allow bokehpivot to use an available port, and allows multiple simultaneous bokehpivot sessions (by launching multiple times).
    
## Running Bokehpivot Interface (MacOS)
In the bokehpivot directory in VSCode or terminal, launch bokehpivot by:
```
/.launch.sh
```
(if you run into an access/permission restricting issue, allow yourself access to launch.sh by running following command before ``` /.launch.sh ```:
```
chmod u+x launch.sh
```
a browser window with an interactive interface will pop up.

## Loading data
After starting up the app in a browser window, you must enter a path in the *Data Source* field, either to a CSV file or to a Model run or set of runs:
* *CSV*: Enter a path to a csv file. This file must be properly formatted, with column headers but no row headers. You can *Shift+Right Click* on a csv file, then select *Copy as Path* to get the full path to a file. After that, see the *Core Pivot Functionality* section below.
* *Model Run(s)*: Here are the options:
    * Enter a path to a Model run folder. This works using shared drives too. For example,  *\\\\nrelqnap01d\\ReEDS\\someProject\\runs\\someRun*.
    * Enter a path to a folder containing run folders. For example,  *\\\\nrelqnap01d\\ReEDS\\someProject\\runs*.
    * Enter any number of the path types above, each separated by a | (pipe) symbol
    * Enter a path to a csv file that contains a list of runs. Using this method allows scenarios to be ordered as desired and colors to be specified as well. See *bokehpivot/reeds_scenarios.csv* for an example. It's easiest to just copy *reeds_scenarios.csv* to some other location and edit/use the copy. Note that the file name must end with *reeds_scenarios.csv*.
    * After entering one of the above, see the *ReEDS Widgets* and *Core Pivot Functionality* sections below.

## Model Widgets
* **Model Variables**: Click the *Model Variables* section to expand, and update any model variables, e.g. dollar year and present value reference and end years.
* **Meta**: Click the *Meta* section to expand, and see the files used for some default *maps* (to rename and aggregate different output categories), *styles* (to reorder categories and style them), and *merges* (to join more columns, e.g. to add regional aggregations). If you'd like to update any of these files, simply edit the file (only if you're working locally), or point to a new file. When changing mappings, note that all set elements have been lowercased!
* **Filter Scenarios**: A list of scenarios will be fetched after entering a path in *Runs*. Use the *Filter Scenarios* section to reduce the scenarios from which the app will fetch output data. Note that this filter does not have an effect after the data has already been fetched. To do further filtering of scenarios when building/updating figures, use the "scenario" filter in the "Filters" dropdown (described below).
* **Build Report**: Build an HTML/Excel report based on a python file with a list of bokehpivot configurations. A select widget allows any of the reports in the *reports\\templates\\* folder to be chosen, or the path to a custom report may be entered in a text widget (for example, one that is exported using the *Export Report Config* button described below). If the report references a base case, this may be chosen with a select widget. Click the *Build Report* button to create one html file and excel file with results for that report, or click *Build Separate Reports* to split each report configuration into its own html file. In either case, a separate and independent process is initiated each time one of these buttons is clicked. Note that *Filter Scenarios* may be used to limit the scenarios included in the report.
* **Result**: Select a result from the *Result* select box. It may take a few seconds to fetch the data, depending on the number of scenarios being analyzed. After the result data is fetched, the following widgets will appear
* **Presets**: You may select a preset result from the *Preset* select box, and a set of widgets will be automatically set for you. For example, for *Generation*, *Stacked Generation* is a preset result. Note that after selecting a preset, you may make further modifications to the widgets.
* See the *Core Pivot Functionality* section below for the rest of the available widgets.

## Core Pivot Functionality
* **Chart Type**: *Dot*, *Line*, Bar, Area, or Map. Note that Map requires that a mapped region (i, n, r, rnew, rto, st) is chosen as x-axis
* **X-axis (required)**: Select a column to use as x-axis
* **Group X By**: Select a column to group the x-axis (if both x-axis and grouping columns are discrete).
* **Y-axis (required)**: Select a column to use as y-axis
* **Y-Axis Aggregation**: Select *Sum*, *Average*, or *Weighted Ave*, or *Weighted Ave Ratio*. *Weighted Ave* requires another field, the *Weighting Factor*, and *Weighted Ave Ratio*, a ratio of weighted averages, requires both *Weighting Factor* (for the numerator of the ratio) and *Denominator Weighting Factor*. For electricity price, for example, select *load* as the *Weighting Factor*.
* **Series**: Pick a column to split the data into separate, color-coded series. If Chart Type (see Plot Adjustments
below) is Area or Bar, series will automatically be stacked. If Chart Type is Line or Dot, the series will not be stacked.
* **Series Legend**: Click on this to see the color and name of each series
* **Explode By**: Select a discrete column to split into multiple charts. The charts' titles will correspond to the
exploded column values.
* **Group Exploded Charts By**: Select a discrete column to group exploded charts. Play around with plot sizes (see below)
and/or resize your browser screen to make a nice 2d array of charts.
* **Comparisons**: This section allows comparisons across any dimension. You first select the *Operation*, then the column you'd like to *Operate Across*, then the *Base* that you'd like to compare to. Here are a couple examples for results:
    * Generation differences: Select *Generation* as *Result*, and select *Stacked Gen* under *Presets*. Then, under *Comparisons*, select *Operation*=*Difference*, *Operate Across*=*scenario*, and *Base*=your-base-case.
    * Generation Fraction: Select *Generation* as *Result*, and select *Stacked Gen* under *Presets*. Then, under *Comparisons*, select *Operation*=*Ratio*, *Operate Across*=*tech*, and *Base*=*Total*.
    * Capacity Differences, solve-year-to-solve-year: Select *Capacity* as *Result*, and select *Stacked Capacity* under *Presets*. Then, under *Comparisons*, select *Operation*=*Difference*, *Operate Across*=*year*, and *Base*=*Consecutive*.
* **Filters**: Each column can be used to filter data with checkboxes. After selecting Filters, you must press the Update Filters button to apply the filters
* **Update Filters**: This is used for updating the charts once filters have been changed
* **Plot Adjustments**: Make additional figure modifications: Size, x-axis/y-axis limits and scale, etc.
* **Map Adjustments**: By default, data is binned using the *Auto Equal Num* method, which tries to split the data evenly between bins. But bins can also be specified as having equal width, or they can be set fully manually, using comma separated breakpoints. The two auto binning methods can also accept a number of bins and min/max values. Finally, stylistic adjustments to the maps may be made. Different coloring palettes may be used from https://bokeh.pydata.org/en/latest/docs/reference/palettes.html as long as the number of bins is allowed in that palette.
* **Auto/Manual Update**: Setting *Auto Update* to *Disable* will disallow plots and data to be updated automatically while widgets are altered. The *Manual Update* button can be used to manually update plots and data. Setting *Render plots* to *No* will disallow rendering of figures. This is useful if, for instance, rendering plots is taking a very long time, and you simply want to download the data for a given widget config.
* **Download/Export**: Download any data you're viewing with the *Download csv of View* and *Download html of View* buttons, or download all data for a given source/result with the *Download csv of Source* button. It will be downloaded into a timestamped file in the *bokehpivot\\out\\* folder, under your username. *Export URL* will save any non-default widget configuration as a URL query string (starting with "?") and create a text file. At a later time, you will be able to load the same view by simply appending the URL query string to your bokehpivot URL (with your bokeh server running). If the URL is from Scorpio/Orion, you may access the URL from any computer connected to the NLR network (while the bokeh server on Scorpio/Orion is still running). *Export Report Config* will save config as a report section configuration dict in a python file, which can then be loaded as a custom file in the *Build Report* section above.

## Creating report templates:
Report templates are in the *reports\\templates\\* folder. Each of these files consists of a list of configurations. Every configuration has these keys:
* *name*: The title of this section of the report, shown in both the HTML and Excel sheets
* *result* (optional): The result name (required if using the *preset* key).
* *preset* (optional): The preset name.
* *config* (optional): Full configuration if not using *result* or *preset* keys, or additional configuration to add. See *reports\\templates\\jobs_report.py* for examples of the *config* key used in addition to presets.
* *modify* (optional): This allows comparison charts to be built when a base case has been specified. *'modify': 'diff'* indicates that difference charts should be shown with the base case, while *'modify': 'base_only'* indicates that the result should only be shown for the base case.

## Tips
1. Pressing *Alt* will collapse all expandable sections.
1. Shift+Right Click on a file or folder in Windows Explorer will show the "Copy as Path" option, which may be pasted directly in the data source field.
1. Shift+Right Click on a folder or in a folder in Windows Explorer will show the "Open Command Window Here" option, which is helpful when running the static report .py files.
1. To suppress the automatic update of the plot while configuring the widgets, simply set *Auto-Update* to *Disable* to stop rendering of plots, then make your widget changes, then finally click the *Manual Update* button.
1. You may interact with the bokeh server with multiple browser windows/tabs, and these interactions will be independent, so you can leave one result open in one tab while you load another in a separate tab, for example.
1. The charts themselves have some useful features shown on the right-hand-side of each chart. For example, hovering over data on a chart will show you the series, x-value, and y-value of the data (not currently working for Area charts). You may also box-zoom or pan (and reset to go back to the initial view). Finally, the charts can be saved as pngs.

## Troubleshooting
1. If the window becomes unresponsive, simply refresh the page (you may want to export config first).
1. If a page refresh doesn't work, then restart the bokeh server. If you have time, you can send Matt a screenshot of the error in the terminal window, if there is one.

## Additional Resources
This tool uses bokeh, built on python:
https://docs.bokeh.org/en/latest/.
The site has good documentation in the User Guide and Reference.

There is also an active google group for issues:
https://discourse.bokeh.org

And of course, python has good documentation too:
https://docs.python.org/2.7/tutorial/
