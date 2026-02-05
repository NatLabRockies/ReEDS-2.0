# ReEDS-to-Tableau Postprocessing
#
# This script concatenates ReEDS csv outputs from a specified list of ReEDS scenarios to 
# a new directory (specified as output_dir), creates pivot tables of the specified outputs
# using custom functions that can be defined for each parameter, and creates a Tableau .hyper 
# extract file containing the pivotted tables for visualization and analysis in Tableau.
# 
# Before running this script for the first time, you'll need to install the Tableau Hyper API via pip with:
# `pip install tableauhyperapi`
#  
# Example call:
# python postprocess_for_tableau.py \
#       -d '//nrelnas01/reeds/some_dir_containing_runs' \
#       -r 'D:/mirish/projects/ReEDS-2.0' \
#       -o '//nrelnas01/reeds/some_directory_containing_runs/testbatch_suite' \
#       -s testbatch_refseq,testbatch_carbtax,testbatch,carbcap -\
#       -p standard,plexos

import pandas as pd
import geopandas as gpd
import numpy as np
import os
import sys
from pathlib import Path

# Add bokehpivot and retail_rate_module to the path so we can grab some of their objects:
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'postprocessing' / 'bokehpivot'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'postprocessing' / 'retail_rate_module'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'postprocessing' / 'tableau'))


from pivot_definitions import PIVOT_DEFS, pivots_without_csvs
import core
from reeds2 import pre_systemcost, inflate_series
import bokeh.models.widgets as bmw #for setting dollar year widget in cost reporting
import reeds_bokeh
import retail_rate_calculations

from tableauhyperapi import HyperProcess, Telemetry, \
    Connection, CreateMode, \
    NULLABLE, SqlType, TableDefinition, \
    escape_string_literal, \
    HyperException


# Define a dict of column types mapping their names to data types and 
# fancier names we'll use within Tableau for plotting.
# "val" is excluded here, which refers to the measured value column. 
# Whatever's in the "label" column of tables_to_aggregate
# will be applied as the name and the column's assigned as a double.
column_types = {
"scenario":         ["Scenario", SqlType.text()],
"i":                ["Technology or Category", SqlType.text()],
"v":                ["Class", SqlType.text()],
"h":                ["Timeslice", SqlType.text()],
"r":                ["Region", SqlType.text()],
"rf":               ["From Region", SqlType.text()],
"rt":               ["To Region", SqlType.text()],
"t":                ["Year", SqlType.int()],
"bin":              ["Bin", SqlType.text()],
"szn":              ["Season", SqlType.text()],
"capture_types":    ["Capture Type", SqlType.text()],
'cendiv':           ["Census Division", SqlType.text()],
'country':          ["Country", SqlType.text()],
'interconnect':     ["Interconnection", SqlType.text()],
'rb':               ["Balancing Area", SqlType.text()],
'st':               ["State/Province", SqlType.text()],
'transreg':         ["Transmission Region", SqlType.text()],
'usda_region':      ["USDA (Biomass Supply Curve) Region", SqlType.text()],
"ortype":           ["Reserve Type", SqlType.text()],
"trtype":           ["Transmission Type", SqlType.text()],
"type":             ["Type", SqlType.text()],
"subtype":          ["Subtype", SqlType.text()],
"cost_cat_display": ["Cost Category", SqlType.text()],
"cost_cat":         ["Cost Subcategory", SqlType.text()],
"stor_in_or_out":   ["Energy Flow", SqlType.text()],
"price_component":  ["Price Component or Credit", SqlType.text()],
"var_name":         ["Variable", SqlType.text()],
"con_name":         ["Constraint or Objective Coeffficient", SqlType.text()],
"process":          ["Process", SqlType.text()],
"subprocess":       ["Subprocess", SqlType.text()],
"starttime":        ["Start Time (UTC)", SqlType.timestamp()],
"stoptime":         ["Stop Time (UTC)", SqlType.timestamp()],
"machine":          ["Computing Resource", SqlType.text()],
"repo":             ["Repo Path", SqlType.text()],
"branch":           ["Branch", SqlType.text()],
"commit":           ["Commit Hash", SqlType.text()],
"p":                ["Product", SqlType.text()],
"e":                ["Emission Type", SqlType.text()],
"8760":             ["Time and Date", SqlType.timestamp()],
"plexos_scenario":  ["PLEXOS Scenario", SqlType.text()]
}

# Create a mapping between H5PLEXOS parameters as read in and as 
# reported to Tableau:
plexos_param_names = {
'plexos_capacity':'PLEXOS Installed Capacity (MW)',
'plexos_generation':'PLEXOS Generation (MWh)',
'plexos_emissions':'na',
'plexos_availableenergy':'PLEXOS Available Energy (GWh)',
'plexos_pumpload':'PLEXOS Pump Load (MWh)',
'plexos_load':'PLEXOS Load (MWh)',
'plexos_losses':'PLEXOS Interregional Transmission Losses (MWh)',
'plexos_lmp':'PLEXOS LMP ($/MWh)',
'plexos_use':'PLEXOS Unserved Energy (MWh)'
}


def get_region_mapping(reeds_path):
    """
    Assemble a spatial mapping file with geometry columns using various csvs
    saved in the ReEDS repo.
    """
    hier = pd.read_csv(Path(reeds_path,'inputs','hierarchy.csv'),header=0,index_col=False)
    hier = hier.rename(columns={'*r':'r'})
    hier['rb'] = hier['r']

    # Pull in geometries for BA polygons and centroids/transmission endpoints
    ba_polygons = pd.read_csv(Path(reeds_path,'inputs','shapefiles','US_CAN_MEX_PCA_polygons.csv'))
    ba_centroids = pd.read_csv(Path(reeds_path,'inputs','shapefiles','US_transmission_endpoints_and_CAN_MEX_centroids.csv'))
    hier = pd.merge(hier,ba_polygons[['WKT','rb']],on='rb',how='left')
    hier = pd.merge(hier,ba_centroids,left_on='rb',right_on='ba_str',how='left')
    hier = hier.rename(columns={i:column_types[i][0] for i in column_types})
    hier = hier.rename(columns={'WKT_x':'BA Polygon Geometry',
                                'WKT_y':'BA Centroid Geometry'})
    return hier


def merge_spatial_data(pivot,pivot_info,col_defs,region_mapping):
    """
    Merge region_mapping into a pivot table natively. 
    This drastically increases the size of a table, so it's intended 
    for use only when an output csv is going to be used directly
    instead of analyzed in Tableau, which can do merges on the fly.
    """
    # Merge regional metadata columns where appropriate:	
    if 'r' in pivot_info['id_columns'] and pivot_name != 'region_mapping':	
        # Exclude i**** individual site supply regions from mapping table if none are present in the pivot table to speed up merges:	
        if pivot[pivot['r'].str.startswith('i')].empty:	
            this_region_mapping = region_mapping.loc[~region_mapping['r'].str.startswith('i'),:]	
        pivot = pivot.merge(this_region_mapping,how='left')	
        # Rearrange columns:	
        new_region_cols = this_region_mapping.drop('r',axis=1).columns.tolist()	
        pivot = pivot[pivot_info['id_columns'] + \
                        new_region_cols + \
                        pivot.drop(set(pivot_info['id_columns'] + new_region_cols),axis=1).columns.tolist()]	
        # Insert region mapping columns into column definitions:	
        col_defs = col_defs[0:len(pivot_info['id_columns'])] + \
                    [ TableDefinition.Column(col, SqlType.text(), NULLABLE) for col in new_region_cols if col not in ['BA Polygon Geometry','BA Centroid Geometry'] ] + \
                    [ TableDefinition.Column(col, SqlType.geography(), NULLABLE) for col in new_region_cols if col in ['BA Polygon Geometry','BA Centroid Geometry'] ] + \
                    col_defs[len(pivot_info['id_columns']):]	
    elif 'st' in pivot_info['id_columns']:	
        this_region_mapping = region_mapping.drop(['r','Balancing Area'],axis=1).drop_duplicates()	
        pivot = pivot.merge(this_region_mapping,left_on='st',right_on='State/Province' ,how='left')	
        # Rearrange columns:	
        new_region_cols = this_region_mapping.drop('State/Province',axis=1).columns.tolist()	
        pivot = pivot[pivot_info['id_columns'] + \
                        new_region_cols + \
                        pivot.drop(set(pivot_info['id_columns'] + new_region_cols),axis=1).columns.tolist()]	
        # Insert region mapping columns into column definitions:	
        col_defs = col_defs[0:len(pivot_info['id_columns'])] + \
                    col_defs[len(pivot_info['id_columns']):]	
    elif 'rf' in pivot_info['id_columns']: #for transmission table	
        this_region_mapping = region_mapping.loc[~region_mapping['r'].str.get(0).isin(['s','i']),:] #exclude non-BA regions from merge	
        pivot = pivot.merge(region_mapping.add_prefix('From '),how='left',left_on='rf',right_on='From r')	
        pivot = pivot.merge(region_mapping.add_prefix('To '),how='left',left_on='rt',right_on='To r')	
        pivot = pivot.drop(['From r','To r'],axis=1)
        # Join on line geometries:
        pivot = pivot.merge(line_geometries,how='left',left_on=['From Balancing Area','To Balancing Area'],right_on=['from_ba','to_ba'])
        pivot = pivot.drop(['from_ba','to_ba'],axis=1)	
        pivot = pivot.rename(columns={'WKT':'Line Geometry'})

        # Rearrange columns:	
        geometry_cols = ['From BA Polygon Geometry','From BA Centroid Geometry',
                            'To BA Polygon Geometry','To BA Centroid Geometry',
                            'Line Geometry']
        new_region_cols = [ col for col in region_mapping.add_prefix('From ').drop('From r',axis=1).columns.tolist() if col not in geometry_cols ] + \
                            [ col for col in region_mapping.add_prefix('To ').drop('To r',axis=1).columns.tolist() if col not in geometry_cols ] + \
                            geometry_cols
        pivot = pivot[pivot_info['id_columns'] + \
                        new_region_cols + \
                        pivot.drop(set(pivot_info['id_columns'] + new_region_cols),axis=1).columns.tolist()]	
        # Insert region mapping columns into column definitions:	
        col_defs = col_defs[0:len(pivot_info['id_columns'])] + \
                    [ TableDefinition.Column(col, SqlType.text(), NULLABLE) for col in new_region_cols if col not in geometry_cols ] + \
                    [ TableDefinition.Column(col, SqlType.geography(), NULLABLE) for col in new_region_cols if col in geometry_cols ] + \
                    col_defs[len(pivot_info['id_columns']):]	
    return pivot, col_defs


def concatenate_csvs(this_csv,rel_path,col_name,scenarios,runs_dir):
    """
    For the csv name input as a string, this_csv, grab the csv
    from each ReEDS scenario in the list scenarios and concatenate 
    into a single table with a scenario column name and headers
    specified in columname_defs.
    """
    df_list = []
    for this_scenario in scenarios:
        # -- Add a scenario name and append this csv to the list --
        try:
            df = pd.read_csv(Path(runs_dir) / this_scenario / rel_path / ( this_csv + '.csv'))
        except FileNotFoundError:
            print(f'Scenario {this_scenario} did not create a csv for {this_csv}. Skipping the scenario.')
            continue
        if any(['Symbol not found:' in x for x in df.columns]):
            print(f'Scenario {this_scenario} created a csv for {this_csv} but the variable did not exist in GAMS. Skipping the scenario.')
            continue
        df.insert(0,'Scenario',this_scenario)
        # Reset set columns to account for different GAMS versions' naming conventions:
        df.columns = ['Scenario'] + ['Dim' + str(c+1) for c in range(len(df.columns) - 2) ] + ['Val']
        df_list.append(df)
    # Concatenate all the dfs:
    try:
        full_df = pd.concat(df_list,axis=0)
    except ValueError:
        print(f'No scenarios have data for {this_csv}. Not adding it to the hyper file.')
        raise ValueError
    # Remove any "Undf" values representing years that didn't solve, and set any "Eps" instances to their intended value of zero:
    full_df = full_df.rename(columns={'value':'Val'}) #rename valuestreams "value" to "val" if present--make more elegant later
    full_df = full_df.loc[full_df['Val'] != 'Undf']
    full_df.loc[full_df['Val'] == 'Eps'] = 0
    #Rename the columns to their set names so they're not just "Dim1", "Dim2", etc.
    full_df.columns = ['scenario'] + col_name

    return full_df


def create_table_definitions(table_aggregation_csv_path):
    """
    Create a dict of Tableau Hyper API objects which define all the tables to be created in the .hyper file.
    
    returns: 
        path_dict, a dict of path strings whose keys are each csv to be aggregated
        table_dict, a dict of Hyper API table def objects whose keys are each csv to be aggregated
        columnnames_dict, a dict of column names for each concatenated csv
    """
    csv_list = pd.read_csv(table_aggregation_csv_path)
    csv_list = csv_list[csv_list.ignore!=1].reset_index() #ignore any csvs flagged as such

    path_dict = {}
    table_dict = {}
    columnnames_dict = {}
    for this_csv_idx in range(0,len(csv_list)):
        csv_parameters = csv_list.loc[this_csv_idx]
        path_dict[csv_parameters['csv']] = csv_parameters['path']

        # Assemble the columns from those listed in the table aggregation csv
        column_objects = []
        column_objects.append(TableDefinition.Column('Scenario', SqlType.text(), NULLABLE)) #first column is always ReEDS scenario
        for col in csv_parameters[6:]:
            if not isinstance(col,str): #have run out of columns to add
                break
            elif col == 'val': #label the measure column according to what's specified in the table aggregation csv
                column_objects.append(TableDefinition.Column(csv_parameters['label'], SqlType.double(), NULLABLE))
            else: #regular column listed in column_types
                try:
                    column_objects.append(TableDefinition.Column(column_types[col][0], column_types[col][1], NULLABLE))
                except KeyError:
                    print('{} contains a column name whose type has not been defined in column_types.'.format(csv_parameters['csv']))

        this_table = TableDefinition(
            table_name=csv_parameters['csv'],
            columns = column_objects
        )
        
        table_dict[csv_parameters['csv']] = this_table

        these_columnnames = csv_parameters[6:]
        these_columnnames[these_columnnames=='val'] = csv_parameters['label']
        columnnames_dict[csv_parameters['csv']] = [ x for x in these_columnnames if str(x) != 'nan' ]

    return path_dict, table_dict, columnnames_dict


def update_hyper_file_from_csv(table_def,csv_path,hyper_path,create_new=False):
    """
    Load data from a csv into a Hyper file, creating a new Hyper file if directed to do so
    """
    print(f"Loading data from {csv_path} into table in Tableau Hyper file at {hyper_path}")
    create_mode_to_use = CreateMode.CREATE_AND_REPLACE if create_new else CreateMode.NONE

    # Optional process parameters.
    # They are documented in the Tableau Hyper documentation, chapter "Process Settings"
    # (https://help.tableau.com/current/api/hyper_api/en-us/reference/sql/processsettings.html).
    process_parameters = {
        # Limits the number of Hyper event log files to two.
        "log_file_max_count": "2",
        # Limits the size of Hyper event log files to 100 megabytes.
        "log_file_size_limit": "100M"
    }

    # Starts the Hyper Process with telemetry enabled to send data to Tableau.
    # To opt out, simply set telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU.
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters=process_parameters) as hyper:

        # Optional connection parameters.
        # They are documented in the Tableau Hyper documentation, chapter "Connection Settings"
        # (https://help.tableau.com/current/api/hyper_api/en-us/reference/sql/connectionsettings.html).
        connection_parameters = {"lc_time": "en_US"}

        # Creates new Hyper file if directed to.
        with Connection(endpoint=hyper.endpoint,
                        database=hyper_path,
                        create_mode=create_mode_to_use,
                        parameters=connection_parameters) as connection:

            connection.catalog.create_table_if_not_exists(table_definition=table_def)

            # Using path to current file, create a path that locates CSV file packaged with these examples.
            # path_to_csv = str(Path(__file__).parent / "data" / "customers.csv")

            # Load all rows into the table from the CSV file.
            # `execute_command` executes a SQL statement and returns the impacted row count.
            #
            # Note:
            # You might have to adjust the COPY parameters to the format of your specific csv file.
            # The example assumes that your columns are separated with the ',' character
            # and that NULL values are encoded via the string 'NULL'.
            # Also be aware that the `header` option is used in this example:
            # It treats the first line of the csv file as a header and does not import it.
            #
            # The parameters of the COPY command are documented in the Tableau Hyper SQL documentation
            # (https:#help.tableau.com/current/api/hyper_api/en-us/reference/sql/sql-copy.html).
            count_in_table = connection.execute_command(
                command=f"COPY {table_def.table_name} from {escape_string_literal(str(csv_path))} with "
                f"(format csv, NULL 'NULL', delimiter ',', header)") #include ", header" in string if header is present to skip it

            # print(f"The number of rows in table {table_def.table_name} is {count_in_table}.")

        # print("The connection to the Hyper file has been closed.")
    # print("The Hyper process has been shut down.")


def main(raw_args=None):
    # -- Argument Block --
    # parser = argparse.ArgumentParser(description="""This script concatenates csv outputs from specified ReEDS runs and outputs them as csvs and a Tableau Hyper extract file.""")
    # parser.add_argument("-d","--runs_dir", help="full path to directory containing ReEDS runs")
    # parser.add_argument("-r","--reeds_path", default=str(Path(__file__).resolve().parents[1]), help="full path to ReEDS repo")
    # parser.add_argument("-o","--output_dir", help="name of new directory to create to house outputs within ReEDS-2.0/runs")
    # parser.add_argument("-p","--pivot_dicts", type=lambda s: [x for x in s.split(',')], help="python list of keys to PIVOT_DEFS (in pivot_definitions.py) specifying which set of pivot tables to create")
    # parser.add_argument("-s","--scenarios", type=lambda s: [x for x in s.split(',')], help="Python list of scenario names to include")
    # parser.add_argument("-a","--all_scenarios", action='store_true', help="Flag to include all scenarios in runs_dir ")
    # parser.add_argument("-dy","--dollar_year", type=str, default=str(reeds_bokeh.DEFAULT_DOLLAR_YEAR), help="desired dollar year for outputs (!!!!note: only works for bokehpivot system cost outputs currently. All else still in 2004$")

    # args = parser.parse_args(raw_args)
    # runs_dir = args.runs_dir
    # reeds_path = args.reeds_path
    # output_dir = args.output_dir
    # pivot_dict = args.pivot_dicts
    # scenarios = args.scenarios
    # include_all_scenarios = args.all_scenarios
    # DOLLAR_YEAR = args.dollar_year

    # if include_all_scenarios and scenarios is not None:
    #     raise argparse.ArgumentTypeError("""
    #         Either -a can be specified to include all ReEDS scenarios 
    #         containing outputs within runs_dir, or -s can be specified 
    #         with a list of scenarios to include, but not both.
    #         """)
    # elif include_all_scenarios:
    #     scenarios = os.listdir(runs_dir)
    
    # if  include_all_scenarios is None and any([ f for f in scenarios if not (Path(runs_dir) / f).is_dir() ]):
    #     print(f'Scenarios {[ f for f in scenarios if not (Path(runs_dir) / f).is_dir() ]} are not directories. Skipping them.')
    # scenarios = [ f for f in scenarios if (Path(runs_dir) / f).is_dir() ]

    # incomplete_scenarios = [ f for f in scenarios if 'outputs' not in os.listdir(Path(runs_dir) / f) ] #grab only directories that contain "outputs"
    # incomplete_scenarios = [ f for f in scenarios if 'cap.csv' not in os.listdir(Path(runs_dir) / f / 'outputs') ] #check that outputs contains results
    # if incomplete_scenarios:
    #     print(f'Scenarios {incomplete_scenarios} are incomplete. Skipping them.')
    # scenarios = [ f for f in scenarios if f not in incomplete_scenarios ]


    # # Test arguments:
    # runs_dir = '//nrelnas01/reeds/FY21-EMRE-BeyondVRE/runs/v20210825'	    runs_dir = '//nrelnas01/reeds/FY21-EMRE-BeyondVRE/runs/v20220514'
    # reeds_path = str(Path(__file__).resolve().parents[2])	    runs_dir = r'D:\mirish\ReEDS-2.0\runs'
    # output_dir = "v20210825_results"	    reeds_path = str(Path(__file__).resolve().parents[2])
    # pivot_dicts = ['standard']	    output_dir = "v20220514_tableaupr_results"
    # scenarios = [ f for f in os.listdir(runs_dir) if 'x2' in f and 'outputs' in os.listdir(Path(runs_dir) / f) ] #grab this suite and only scens that contain "outputs"	    pivot_dicts = ['standard']
    # scenarios = [ f for f in scenarios if 'cap.csv' in os.listdir(Path(runs_dir) / f / 'outputs') ] #check that outputs contains results	    scenarios = [ f for f in os.listdir(runs_dir) if 'outputs' in os.listdir(Path(runs_dir) / f) ] #grab this suite and only scens that contain "outputs"
    # DOLLAR_YEAR = '2020'

        # Test arguments:	    # Test arguments:
    runs_dir = r'\\nrelnas01\ReEDS\Some Project\runs\Some Runs Folder' # file path to the folder that contains your runs
    reeds_path = r'\\nrelnas01\ReEDS\Some Location\ReEDS-2.0' # file path to where your ReEDS repo is located
    output_dir = r'\\nrelnas01\ReEDS\Some Location\tableau_report' # where you want the tableau results to output to
    pivot_dicts = ['standard']	   
    scenarios = [ f for f in os.listdir(runs_dir) ]
    scenarios = [ f for f in scenarios if 'cap.csv' in os.listdir(Path(runs_dir) / f / 'outputs') ] #check that outputs contains results	    
    # scenarios.remove('name of folder') quick way to remove a run if say, it failed
    # scenarios = ['PTCFIX_v4_Mid_Case'] # quick test of only one scenario
    DOLLAR_YEAR = '2020'

    # Create results directory in runs_dir/runs if it doesn't exist:
    output_path = (Path(runs_dir) / output_dir)
    output_path.mkdir(parents=False,exist_ok=True)

    # Redirect output to a log file within the output directory:
    sys.stdout = open(output_path / 'tableau_postprocessing_log.txt', 'a')
    sys.stderr = open(output_path /'tableau_postprocessing_log.txt', 'a')

    # Internal defaults (only used for bokehpivot currently):
    PV_YEAR = reeds_bokeh.DEFAULT_PV_YEAR
    DISCOUNT_RATE = reeds_bokeh.DEFAULT_DISCOUNT_RATE
    END_YEAR = reeds_bokeh.DEFAULT_END_YEAR 

    # -- Concatenate scenarios --
    
    # Load in Tableau table definitions for all specified csvs:
    csv_paths, table_defs, columnname_defs = create_table_definitions(Path(reeds_path,'postprocessing','tableau','tables_to_aggregate.csv'))

    # -- Create pivot tables from concatenated csvs --
    # Set bokehpivot internals needed for cost calculations:
    core.GL['widgets'] = {'var_dollar_year': bmw.TextInput(title='Dollar Year', value=str(DOLLAR_YEAR), css_classes=['wdgkey-dollar_year', 'reeds-vars-drop'], visible=False),
                            'var_discount_rate': bmw.TextInput(title='Discount Rate', value=str(DISCOUNT_RATE), css_classes=['wdgkey-discount_rate', 'reeds-vars-drop'], visible=False),
                            'var_pv_year': bmw.TextInput(title='Present Value Reference Year', value=str(PV_YEAR), css_classes=['wdgkey-pv_year', 'reeds-vars-drop'], visible=False),
                            'var_end_year': bmw.TextInput(title='Present Value End Year', value=str(END_YEAR), css_classes=['wdgkey-end_year', 'reeds-vars-drop'], visible=False)}

    # Read in regional mapping table as well as WKT line geometries:	
    region_mapping = get_region_mapping(reeds_path)	
    line_geometries = pd.read_csv(Path(reeds_path,'inputs','shapefiles','r_rr_lines_to_25_nearest_neighbors.csv')) #includes lines for 25 nearest neighbors--could include all but tabke would be 40k rows
    cs_geometries = gpd.read_file(Path(reeds_path,'inputs','shapefiles','ctus_cs_polygons_BVRE.gpkg')) #storage formation polygons
    cs_geometries['Formation Polygon Geometry'] = cs_geometries['geometry'].to_crs('EPSG:4326')
    cs_geometries = cs_geometries[['cs','Formation Deposition','Formation Depth (ft)','Formation Thickness (ft)','Formation Basin','Formation Lithology','Formation CO2 Storage Capacity (MMT CO2)','Formation Centroid State','Formation Polygon Geometry']]

    # Read in table containing list of included csvs to get label values for each csv:
    csv_list = pd.read_csv(Path(reeds_path,'postprocessing','tableau','tables_to_aggregate.csv'))

    create_new = True #create a new .hyper file on the first iteration
    for pivot_dict in pivot_dicts:
        for pivot_name in PIVOT_DEFS[pivot_dict]:
            pivot_info = PIVOT_DEFS[pivot_dict][pivot_name]
            # Initialize the Tableau column definitions for the pivot table's ID columns:
            col_defs = [ TableDefinition.Column(column_types[col][0], column_types[col][1], NULLABLE) for col in pivot_info['id_columns'] ] #probably need to manually change some of these names

            pivot = pd.DataFrame(columns = pivot_info['id_columns'])
            for this_csv, this_operation in zip(pivot_info['csvs'],pivot_info['operation']):
                print(f'Processing {this_csv}')
                if pivot_name not in pivots_without_csvs: #tables that aren't in tables_to_aggregate are created in the switches below
                    try:
                        this_df = concatenate_csvs(this_csv,csv_paths[this_csv],columnname_defs[this_csv],scenarios,runs_dir)
                    except ValueError:
                        continue
                    if this_df.empty:
                        print(f'The concatenated csv for {this_csv} is empty. Skipping that csv for {pivot_name}.')
                        continue
                else:
                    this_df = pd.DataFrame()

                # Custom table manipulations below: 
                this_col_list = []
                if this_df.empty and pivot_name not in pivots_without_csvs:
                    print(f'Warning: {this_csv} is empty. Still adding a column of NULL values to the pivot table.')
                elif this_csv == 'prod_load':
                    this_df['i'] = 'Production Load'
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv in ['prod_h2_price','prod_h2comb_cost']:
                    this_df = this_df.pivot_table(index=pivot_info['id_columns'], columns='p', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                    if this_csv == 'prod_h2_price':
                        this_col_list = {'DAC':'Direct Air CO2 Capture Price (2004 $/metric ton)',
                                        'H2_blue':'Blue Hydrogen Price (2004 $/metric ton)',
                                        'H2_green':'Green Hydrogen Price (2004 $/metric ton)'}
                    elif this_csv == 'prod_h2comb_cost':
                        this_col_list = {'H2_blue':'Blue Hydrogen Fuel Price (2004 $/MMBtu)',
                                        'H2_green':'Green Hydrogen Fuel Price (2004 $/MMBtu)'}
                    this_df = this_df.rename(columns=this_col_list)                
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv == 'stor_inout':
                    this_df = this_df.loc[this_df['stor_in_or_out']=='IN'].drop(['stor_in_or_out'],axis=1)
                    this_df = this_df.groupby(pivot_info['id_columns'],as_index=False).sum()
                    this_df = this_df.rename(columns={'Storage Operation (MWh)':'Storage Charging and Pumping (MWh)'})
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv in ['opRes_supply_h','opRes_supply']:
                    this_df = this_df.pivot_table(index=pivot_info['id_columns'], columns='ortype', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                    this_col_list = {'reg':'Reserve Supply - Reg (MWh-h)',
                                    'spin':'Reserve Supply - Spin (MW-h)',
                                    'flex':'Reserve Supply - Flex (MW-h)'}
                    this_df = this_df.rename(columns=this_col_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv == 'opres_trade':
                    this_df['trtype'] = np.nan
                    this_df['trtype'] = this_df['trtype'].astype(str)
                    this_df = this_df.pivot_table(index=pivot_info['id_columns'], columns='ortype', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                    this_col_list = {'reg':'Reserve Trade - Reg (MW-h)',
                                    'spin':'Reserve Trade - Spin (MW-h)',
                                    'flex':'Reserve Trade - Flex (MW-h)'}
                    this_df = this_df.rename(columns=this_col_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv in ['emit_irt','emit_r']:
                    this_df = this_df.pivot_table(index=pivot_info['id_columns'], columns='e', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                    this_col_list = {'CO2':'CO2 Emissions from Generation (MMT)',
                                    'SO2':'SO2 Emissions from Generation (MMT)',
                                    'NOX':'NOX Emissions from Generation (MMT)',
                                    'CH4':'CH4 Emissions from Generation (MMT)',
                                    'CO2e':'CO2e Emissions from Generation (MMT)'}
                    this_df = this_df.rename(columns=this_col_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv == 'reqt_price':
                    this_df['type_subtype'] = this_df['type'] + '_' + this_df['subtype']
                    this_df = this_df.pivot_table(index=pivot_info['id_columns'], columns='type_subtype', aggfunc=np.mean).droplevel(0,axis=1).reset_index()
                    this_col_list = {'annual_cap_CO2':'CO2 Cap Compliance Price (2004 $)',
                                    'load_na':'Energy Price (2004 $/MWh)',
                                    'oper_res_flex':'Reserve Price - Flex (2004 $/MW-h)',
                                    'oper_res_reg':'Reserve Price - Reg (2004 $/MW-h)',
                                    'oper_res_spin':'Reserve Price - Spin (2004 $/MW-h)',
                                    'res_marg_ann_na':'Planning Reserve Compliance Price (2004 $)',
                                    'res_marg_na':'duplicate',
                                    'state_rps_CES':'State CES Compliance Price (2004 $)',
                                    'state_rps_RPS_All':'State All-RPS Price (2004 $)',
                                    'state_rps_RPS_Solar':'State Solar RPS Price (2004 $)'}
                    this_df = this_df.rename(columns=this_col_list)
                    this_df = this_df.drop(['duplicate'],axis=1)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv == 'reqt_quant' and this_operation == 'custom':
                    this_df['type_subtype'] = this_df['type'] + '_' + this_df['subtype']
                    this_df = this_df.pivot_table(index=pivot_info['id_columns'], columns='type_subtype', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                    this_col_list = {'annual_cap_CO2':'CO2 Emissions Cap (Mt CO2)',
                                    'load_na':'Hourly Load (MWh)',
                                    'nat_gen_na':'CES Generation Requirement (MWh)',
                                    'oper_res_flex':'Reserve Provision - Flex (MW-h)',
                                    'oper_res_reg':'Reserve Provision - Reg (MW-h)',
                                    'oper_res_spin':'Reserve Provision - Spin (MW-h)',
                                    'res_marg_ann_na':'Planning Reserve Margin (%))',
                                    'res_marg_na':'duplicate',
                                    'state_rps_CES':'State CES Generation (MWh)',
                                    'state_rps_RPS_All':'State All-RPS Generation (MWh))',
                                    'state_rps_RPS_Solar':'State Solar RPS Generation (MWh)',
                                    'state_rps_RPS_Wind':'State Wind RPS Generation (MWh)'}
                    this_df = this_df.rename(columns=this_col_list)
                    this_df = this_df.drop(['duplicate'],axis=1)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv == 'emit_captured_r':
                    this_df = this_df.pivot_table(index=pivot_info['id_columns'], columns='capture_types', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                    this_col_list = {'co2_ccs':'CO2 Captured via CCS Generation (metric tons)',
                                    'co2_smr-ccs':'CO2 Captured via SMR H2 Production (metric tons)',
                                    'co2_dac':'CO2 Captured via DAC (metric tons)'}
                    this_df = this_df.rename(columns=this_col_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv == 'reqt_quant' and this_operation == 'load_only': #grab only timeslice load from reqt_quant
                    this_df = this_df.loc[this_df['type']=='load']
                    this_df['type_subtype'] = this_df['type'] + '_' + this_df['subtype']
                    this_df['i'] = 'Load'
                    this_df = this_df.pivot_table(index=pivot_info['id_columns'], columns='type_subtype', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                    this_col_list = {'load_na':'Load (MWh)'}
                    this_df = this_df.rename(columns=this_col_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]            
                elif this_csv == 'systemcost_ba': #Special: we use bokehpivot preprocessing functions here for discounting, annualizing, and inflating 
                    this_df_list = []
                    
                    #Read in cost category mapping:
                    cost_cat_map = pd.read_csv(Path(reeds_path) / 'postprocessing' / 'bokehpivot' / 'in' / 'reeds2' / 'cost_cat_map.csv', header=0, names=['cost_cat','cost_cat_display'])
                    
                    for this_scenario in scenarios:
                        # Keeping the table calculations below separate for each cost output (despite the code being a bit inefficient) to facilitate understanding of each cost calc.
                        # First, retrieve discounted and undiscounted annualized costs:
                        # (This is equivalent to bokehpivot's ReEDS preset for 'Sys Cost Annualized (Bil $)': presets 'Discounted by Year' and 'Undiscounted by Year')
                        this_sc = reeds_bokeh.df_to_lowercase(pd.read_csv(Path(runs_dir) / this_scenario / 'outputs' / 'systemcost_ba.csv', header=0, names=['cost_cat', 'r', 'year', 'Cost (Bil $)']))
                        this_sc = this_sc.loc[this_sc['Cost (Bil $)'] != 'Undf']
                        this_sc.loc[this_sc['Cost (Bil $)'] == 'Eps'] = 0
                        dfs = {'sc': this_sc,
                            'sw': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'switches.csv', header=None, names=['switch','value']),
                            'val_r': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'val_r.csv',header=None),
                            'df_capex_init': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'df_capex_init.csv'),
                            'crf': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'crf.csv', header=0, names=['year', 'crf']),
                            'scalars': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'scalars.csv', header=None, usecols=[0,1], names=['scalar', 'value'])}
                        this_ann_df = pre_systemcost(dfs,annualize=True,shift_capital=True,maintain_ba_index=True) #this func is from reeds2.py, altered to keep BA
                        this_ann_df = this_ann_df.merge(cost_cat_map,on='cost_cat',how='left')
                        this_ann_df = this_ann_df.rename(columns={'Cost (Bil $)':f'Sys Cost Annualized - Undiscounted (Bil {DOLLAR_YEAR}$)',
                                                                        'Discounted Cost (Bil $)':f'Sys Cost Annualized - Discounted to {PV_YEAR} (Bil {DOLLAR_YEAR}$)'}) #these have already been inflated in pre_systemcost

                        # Second, retrieve discounted and undiscounted annual system costs with O&M costs truncated to just 2050 (not to 2070):
                        # (This is equivalent to bokehpivot's ReEDS preset for 'Sys Cost truncated at final year (Bil $)': presets 'Discounted by Year' and 'Undiscounted by Year')
                        this_sc = reeds_bokeh.df_to_lowercase(pd.read_csv(Path(runs_dir) / this_scenario / 'outputs' / 'systemcost_ba_bulk_ew.csv', header=0, names=['cost_cat', 'r', 'year', 'Cost (Bil $)']))
                        this_sc = this_sc.loc[this_sc['Cost (Bil $)'] != 'Undf']
                        this_sc.loc[this_sc['Cost (Bil $)'] == 'Eps'] = 0
                        dfs = {'sc': this_sc,
                            'sw': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'switches.csv', header=None, names=['switch','value']),
                            'scalars': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'scalars.csv', header=None, usecols=[0,1], names=['scalar', 'value'])}
                        this_trunc_df = pre_systemcost(dfs,shift_capital=True,maintain_ba_index=True)
                        this_trunc_df = this_trunc_df.merge(cost_cat_map,on='cost_cat',how='left')
                        this_trunc_df = this_trunc_df.rename(columns={'Cost (Bil $)':f'Sys Cost Truncated at Final Year - Undiscounted (Bil {DOLLAR_YEAR}$)',
                                                                    'Discounted Cost (Bil $)':f'Sys Cost Truncated at Final Year - Discounted to {PV_YEAR} (Bil {DOLLAR_YEAR}$)'}) #these have already been inflated in pre_systemcost

                        # Third, retrieve discounted and undiscounted annual system costs WITHOUT truncating O&M costs to 2050 (allowing them to continue to 2070):
                        # (This is equivalent to bokehpivot's ReEDS preset for 'Sys Cost beyond final year (Bil $)': presets 'Discounted by Year' and 'Undiscounted by Year')
                        this_sc = reeds_bokeh.df_to_lowercase(pd.read_csv(Path(runs_dir) / this_scenario / 'outputs' / 'systemcost_ba_bulk.csv', header=0, names=['cost_cat', 'r', 'year', 'Cost (Bil $)']))
                        this_sc = this_sc.loc[this_sc['Cost (Bil $)'] != 'Undf']
                        this_sc.loc[this_sc['Cost (Bil $)'] == 'Eps'] = 0
                        dfs = {'sc': this_sc,
                            'sw': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'switches.csv', header=None, names=['switch','value']),
                            'scalars': pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'scalars.csv', header=None, usecols=[0,1], names=['scalar', 'value'])}
                        this_untrunc_df = pre_systemcost(dfs,shift_capital=True,maintain_ba_index=True)
                        this_untrunc_df = this_untrunc_df.merge(cost_cat_map,on='cost_cat',how='left')
                        this_untrunc_df = this_untrunc_df.rename(columns={'Cost (Bil $)':f'Sys Cost Beyond Final Year - Undiscounted (Bil {DOLLAR_YEAR}$)',
                                                                        'Discounted Cost (Bil $)':f'Sys Cost Beyond Final Year - Discounted to {PV_YEAR} (Bil {DOLLAR_YEAR}$)'}) #these have already been inflated in pre_systemcost

                        this_scen_df = pd.merge(this_ann_df,this_trunc_df,on=['r','year','cost_cat_display','cost_cat'],how='outer')
                        this_scen_df = this_scen_df.merge(this_untrunc_df,on=['r','year','cost_cat_display','cost_cat'],how='outer')
                        this_scen_df.insert(0,'scenario',this_scenario)
                        this_scen_df = this_scen_df.rename(columns={'year':'t'})
                        this_scen_df = this_scen_df[ pivot_info['id_columns'] + [ col for col in this_scen_df.columns if col not in pivot_info['id_columns'] ]]
                        this_df_list.append(this_scen_df)
                    this_df = pd.concat(this_df_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv == 'retail':
                    this_df_list = []
                    for this_scenario in scenarios:
                        if not (Path(runs_dir) / this_scenario / 'outputs' / 'retail' / 'retail_rate_components.csv').is_file():
                            print(f'Scenario {this_scenario} did not report retail rate module outputs.')
                        else:
                            this_scen_df = retail_rate_calculations.get_dfplot(run_dir=str(Path(runs_dir) / this_scenario), inputpath=str(Path(reeds_path) / 'postprocessing' / 'retail_rate_module' / 'inputs.csv'), plot_dollar_year=int(DOLLAR_YEAR),tableau_export=True)
                            
                            this_scen_df = this_scen_df.rename(columns=retail_rate_calculations.tracelabels) #rename cost categories using the plotting dict in the retail rate module
                            this_scen_df = this_scen_df.rename(columns={'busbar_load':'Busbar Load (MWh)',
                                                            'end_use_load':'End-Use Load (MWh)',
                                                            'distPV_gen':'Distributed PV Generation (MWh)',
                                                            'retail_load':'Retail Load (MWh)',
                                                            'ptc_grossup':f'PTC Grossup ({DOLLAR_YEAR}¢/kWh)',
                                                            'itc_normalized_value':f'ITC Normalized Value ({DOLLAR_YEAR}¢/kWh)'})
                            this_scen_df_mwh = this_scen_df[['Busbar Load (MWh)','End-Use Load (MWh)','Distributed PV Generation (MWh)','Retail Load (MWh)']]
                            this_scen_df_mwh['price_component'] = "" #create a column of type object

                            this_scen_df_prices = this_scen_df.drop(['Busbar Load (MWh)','End-Use Load (MWh)','Distributed PV Generation (MWh)','Retail Load (MWh)'],axis=1)
                            this_scen_df_prices = this_scen_df_prices.melt(ignore_index=False, var_name = 'price_component', value_name=f'Retail Rate by Component ({DOLLAR_YEAR}¢/kWh)')
                            
                            this_scen_df_incentives = this_scen_df[[f'PTC Grossup ({DOLLAR_YEAR}¢/kWh)',f'ITC Normalized Value ({DOLLAR_YEAR}¢/kWh)']]
                            this_scen_df_incentives = this_scen_df_incentives.melt(ignore_index=False, var_name = 'price_component', value_name=f'Tax Credit ({DOLLAR_YEAR}¢/kWh)')
                            
                            this_scen_df = pd.merge(this_scen_df_prices,this_scen_df_incentives,on=['state','t','price_component'],how='outer')
                            this_scen_df = pd.merge(this_scen_df,this_scen_df_mwh,on=['state','t','price_component'],how='outer')
                            this_scen_df['price_component'] = this_scen_df['price_component'].replace("",np.nan)
                            this_scen_df = this_scen_df.reset_index()
                            this_scen_df = this_scen_df.rename(columns={'state':'st'})
                            this_scen_df.insert(0,'scenario',this_scenario)
                            this_df_list.append(this_scen_df)
                    if not this_df_list:
                        print('No scenarios reported retail rate module outputs. Skipping the retail_rates pivot table.')
                        continue
                    this_df = pd.concat(this_df_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif this_csv == 'region_mapping':
                    # Read in regional mapping table:
                    this_df = region_mapping.copy()
                    # # Exclude i**** individual site supply regions from mapping table if none are present in the scenarios being processed in order to speed up merges:
                    # if pivot[pivot['r'].str.startswith('i')].empty:
                    #     this_region_mapping = region_mapping.loc[~region_mapping['r'].str.startswith('i'),:]
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                    # Set the column definitions here rather than below, where all columns are assumed to be of type double.
                    this_col_def = [ TableDefinition.Column(col, SqlType.text(), NULLABLE) for col in this_col_list if col not in ['r','BA Polygon Geometry','BA Centroid Geometry']]
                    this_col_def = this_col_def + [ TableDefinition.Column(col, SqlType.geography(), NULLABLE) for col in this_col_list if col in ['BA Polygon Geometry','BA Centroid Geometry']]
                elif this_csv == 'line_mapping':
                    # Read in line geometries table:
                    this_df = line_geometries
                    this_df = this_df.rename(columns={'from_ba':'rf',
                                                    'to_ba':'rt',
                                                    'WKT':'Line Geometry'})
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                    # Set the column definitions here rather than below, where all columns are assumed to be of type double.
                    this_col_def = [ TableDefinition.Column(col, SqlType.text(), NULLABLE) for col in this_col_list if col not in ['Line Geometry']]
                    this_col_def = this_col_def + [ TableDefinition.Column(col, SqlType.geography(), NULLABLE) for col in this_col_list if col in ['Line Geometry']]
                elif this_csv in region_mapping.columns:
                    this_df = pd.read_csv(Path(reeds_path,'inputs','shapefiles','WKT_csvs',(this_csv + '_WKT.csv')))
                    this_df = this_df.rename(columns={'WKT':column_types[this_csv][0] + " Geometry"})
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                    this_df = this_df[[this_csv,column_types[this_csv][0] + " Geometry"]] #reorder to keep ID col first
                    # Set the column definitions here rather than below, where all columns are assumed to be of type double.
                    this_col_def = [TableDefinition.Column(column_types[this_csv][0] + " Geometry", SqlType.geography(), NULLABLE)]
                elif this_csv == 'ctus_r_cs_mapping':
                    this_df_list = []
                    for this_scenario in scenarios:
                        # Read in CO2 spur line geometry table:
                        r_cs_spurline_geometries = pd.read_csv(Path(runs_dir) / this_scenario / 'inputs_case' / 'ctus_r_cs_spurlines_200mi.csv') #includes lines for 25 nearest neighbors--could include all but tabke would be 40k rows
                        r_cs_spurline_geometries['distance_m'] = r_cs_spurline_geometries['distance_m'] * 0.000621371 #m to mi
                        r_cs_spurline_geometries = r_cs_spurline_geometries.rename(columns={'WKT':'Spur Line Geometry',
                                                                                            'ba_str':'r',
                                                                                            'FmnID':'cs',
                                                                                            'distance_m':'Spur Line Length (mi)'})
                        this_scen_df = r_cs_spurline_geometries
                        this_scen_df.insert(0, 'scenario', this_scenario)
                        this_df_list.append(this_scen_df)
                    this_df = pd.concat(this_df_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                    # Set the column definitions here rather than below, where all columns are assumed to be of type double.
                    this_col_def = [ TableDefinition.Column(col, SqlType.text(), NULLABLE) for col in this_col_list if col not in ['Spur Line Geometry']]
                    this_col_def = this_col_def + [ TableDefinition.Column(col, SqlType.geography(), NULLABLE) for col in this_col_list if col in ['Spur Line Geometry']]            
                elif this_csv == 'ctus_cs_mapping':
                    # Read in CO2 storage formation geometry table:
                    this_df = cs_geometries
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                    # Set the column definitions here rather than below, where all columns are assumed to be of type double.
                    this_col_def = [ TableDefinition.Column(col, SqlType.text(), NULLABLE) for col in this_col_list if col not in ['Formation Polygon Geometry']]
                    this_col_def = this_col_def + [ TableDefinition.Column(col, SqlType.geography(), NULLABLE) for col in this_col_list if col in ['Formation Polygon Geometry']]
                elif this_csv == 'meta':
                    this_df_list = []
                    for this_scenario in scenarios:
                        if not (Path(runs_dir) / this_scenario / 'meta.csv').is_file():
                            print(f'Scenario {this_scenario} did not report scenario metadata and solve times in metadata.csv.')
                        else:
                            if pivot_name == 'runtimes':
                                this_scen_df = pd.read_csv(Path(runs_dir) / this_scenario / 'meta.csv', header=3, names=['t','subprocess','starttime','stoptime','Processing Time (min)'])
                                
                                this_scen_df['Processing Time (min)'] /= 60 #sec to min
                                this_scen_df.loc[this_scen_df['t']==0] = np.nan
                                this_scen_df.insert(1,'process',"")
                                this_scen_df = this_scen_df.loc[~this_scen_df['Processing Time (min)'].isnull()] #eliminate erroneous "end" subprocess in inputs processing
                                this_scen_df['process'] = this_scen_df['subprocess'].map({'createmodel.gms':'Input Processing',
                                                                                    'pickle_jar':'Augur',
                                                                                    'd_solveoneyear.gms':'ReEDS Solve',
                                                                                    'd_solveallyears.gms':'ReEDS Solve'})
                                this_scen_df.loc[this_scen_df['subprocess'].str.contains('ReEDS_Augur',case=False,na=False),'process'] = 'Augur'                                            
                                this_scen_df.loc[this_scen_df['subprocess'].str.contains('input_processing',case=False,na=False),'process'] = 'Input Processing'                                            
                                this_scen_df.loc[this_scen_df['subprocess'].str.contains('report',case=False,na=False),'process'] = 'Reporting (Postprocessing)'                                            
                                
                                this_scen_df.insert(0,'scenario',this_scenario)
                                this_df_list.append(this_scen_df)
                            elif pivot_name == 'metadata':
                                this_scen_df = pd.read_csv(Path(runs_dir) / this_scenario / 'meta.csv', header=0)
                                this_scen_df = this_scen_df.iloc[[0],:] #keep only the first row
                                this_scen_df.insert(0,'scenario',this_scenario)
                                this_df_list.append(this_scen_df)
                    if not this_df_list:
                        print(f'No scenarios reported metadata and runtime info in metadata.csv. Skipping the {pivot_name} pivot table.')
                        continue
                    this_df = pd.concat(this_df_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]
                elif 'plexos' in pivot_name:
                    from pivot.query import PLEXOSSolution
                    
                    this_df_list = []
                    for this_scenario in scenarios:
                        this_plexos_dir = Path(runs_dir) / this_scenario / 'plexos_export' / 'solutions' 
                        if not (this_plexos_dir).is_dir():
                            print(f'Scenario {this_scenario} did not report PLEXOS solutions.')
                            continue
                        else:
                            plexos_solution_parent_dirs = os.listdir(this_plexos_dir)
                            all_plexos_solution_paths = [  os.listdir(this_plexos_dir / x ) for x in plexos_solution_parent_dirs  ]
                            plexos_solution_paths = []
                            for i,p in zip(range(len(all_plexos_solution_paths)),all_plexos_solution_paths):
                                plexos_solution_paths = plexos_solution_paths + [ (plexos_solution_parent_dirs[i],x) for x in p if '.h5' in x ]

                                ## If the solutions are in a subfolder, use the following: 
                                # # plexos_solution_paths = plexos_solution_paths + [ (plexos_solution_parent_dirs[i],x) for x in p if '.h5' in x ]

                                # for intermediary in os.listdir(this_plexos_dir / plexos_solution_parent_dirs[i]):
                                #     if os.path.isdir(this_plexos_dir / plexos_solution_parent_dirs[i] / intermediary):
                                #         all_soln = os.listdir(this_plexos_dir / plexos_solution_parent_dirs[i] / intermediary)
                                #         plexos_solution_paths = plexos_solution_paths + [ (plexos_solution_parent_dirs[i],str( Path(intermediary) / x)) for x in all_soln if '.h5' in x ]

                            # First, get the generator--region mapping:
                            try:
                                with PLEXOSSolution( str(this_plexos_dir / plexos_solution_parent_dirs[0] / plexos_solution_paths[0][1]) ) as db:
                                    gen_to_ba = db.relations["regions_generators"].to_frame().reset_index()
                                    gen_to_ba.index = gen_to_ba['child']
                                    gen_to_ba = gen_to_ba['parent'] 
                                    # If we're querying emissions, we also need the generator-to-category (i) mapping:
                                    if this_csv == 'plexos_emissions':
                                        gen_to_i = db.objects["generators"].to_frame().reset_index()
                                        gen_to_i.index = gen_to_i['name']
                                        gen_to_i = gen_to_i['category'] 
                            except Exception: #try the next one if it exists
                                with PLEXOSSolution( str(this_plexos_dir / plexos_solution_parent_dirs[0] / plexos_solution_paths[1][1]) ) as db:
                                    print(f'Querying first h5 from {plexos_solution_paths[1]} for BA mapping did not work. Trying the next one.')
                                    gen_to_ba = db.relations["regions_generators"].to_frame().reset_index()
                                    gen_to_ba.index = gen_to_ba['child']
                                    gen_to_ba = gen_to_ba['parent'] 
                                    # If we're querying emissions, we also need the generator-to-category (i) mapping:
                                    if this_csv == 'plexos_emissions':
                                        gen_to_i = db.objects["generators"].to_frame().reset_index()
                                        gen_to_i.index = gen_to_i['name']
                                        gen_to_i = gen_to_i['category'] 

                            # Only perform interval queries if we want interval data:
                            if '8760' in pivot_info['id_columns']:
                                timescale_required = 'interval'
                            else:
                                timescale_required = 'day' #otherwise need day, not year, so that we can still eliminate warm-start days
                            
                            # Now, loop through solutions and grow a df:
                            this_scen_df_list = []
                            for this_soln in plexos_solution_paths:
                                try:
                                    with PLEXOSSolution( str(this_plexos_dir / this_soln[0] / this_soln[1]) ) as db:
                                        if this_csv == 'plexos_capacity':
                                            df = db.generator("Installed Capacity", timescale=timescale_required)
                                        elif this_csv == 'plexos_availableenergy':
                                            df = db.generator("Available Energy", timescale=timescale_required)
                                        elif this_csv == 'plexos_generation':
                                            df = db.generator("Generation", timescale=timescale_required)
                                        elif this_csv == 'plexos_load':
                                            df = db.region("Load", timescale=timescale_required)
                                        elif this_csv == 'plexos_losses':
                                            df = db.region("Interregional Transmission Losses", timescale=timescale_required)
                                        elif this_csv == 'plexos_pumpload':
                                            df = db.generator("Pump Load", timescale=timescale_required)
                                        elif this_csv == 'plexos_use':
                                                df = db.region("Unserved Energy", timescale=timescale_required)
                                        elif this_csv == 'plexos_lmp':
                                            df = db.region("Price", timescale=timescale_required)
                                        elif this_csv == 'plexos_emissions':
                                            df = db.emissions_generators("Production", timescale=timescale_required)
                                except Exception:
                                    print(f'HDF5 query hit an error for {this_soln[0]}/{this_soln[1]}')
                                    pass
                                        
                                    df = df.to_frame()
                                    df.insert(0,'plexos_scenario',this_soln[0])
                                    this_scen_df_list.append(df)
                                except Exception:
                                    print(f'HDF5 query hit an error for {this_soln[0]}/{this_soln[1]}')
                                    pass
                                    
                            this_scen_df = pd.concat(this_scen_df_list)
                            this_scen_df = this_scen_df.reset_index()

                            # Eliminate overlapping warm-start days at the beginning of each month:
                            this_scen_df = this_scen_df.groupby(list(this_scen_df.columns[:-1])).head(1)
                            
                            if this_csv == 'plexos_capacity':
                                this_scen_df = this_scen_df.drop_duplicates() #for getting rid of repeated capacity values

                            this_scen_df['t'] = this_scen_df['timestamp'].dt.year
                            this_scen_df = this_scen_df.rename(columns={'category':'i',
                                                                        'timestamp':'8760'})

                            # Map to BA and aggregate to state level if desired:
                            if this_csv in ['plexos_load','plexos_use','plexos_lmp']:
                                this_scen_df = this_scen_df.rename(columns={'name':'r',
                                                                            'category':'st'})
                            elif 'r' in pivot_info['id_columns'] or 'st' in pivot_info['id_columns']:
                                if 'child' in this_scen_df.columns:
                                    this_scen_df['r'] = this_scen_df['child'].map(gen_to_ba)
                                else:
                                    this_scen_df['r'] = this_scen_df['name'].map(gen_to_ba)
                                if 'st' in pivot_info['id_columns']:
                                    this_scen_df = this_scen_df.merge(region_mapping[['Balancing Area','State/Province']].drop_duplicates(),left_on='r',right_on='Balancing Area',how='left').drop(['r','Balancing Area'],axis=1)                    
                                    this_scen_df = this_scen_df.rename(columns={'State/Province':'st'})

                            if this_csv == 'plexos_emissions':
                                this_scen_df['i'] = this_scen_df['child'].map(gen_to_i)
                                this_scen_df = this_scen_df[['plexos_scenario','parent','i','r','t',0]]
                                this_scen_df = this_scen_df.pivot_table(index=['plexos_scenario','i','r','t'], columns='parent', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                                this_col_list = {'CO2':'CO2 Emissions (metric tons)',
                                                'SO2':'SO2 Emissions (metric tons)',
                                                'NOX':'NOx Emissions (metric tons)'}
                                this_scen_df = this_scen_df.rename(columns=this_col_list) 
                            else:
                                this_scen_df = this_scen_df[[c for c in pivot_info['id_columns'] if c != 'scenario'] + [0]]
                                if this_operation == 'sum':
                                    this_scen_df = this_scen_df.groupby([c for c in pivot_info['id_columns'] if c != 'scenario']).sum().reset_index()
                                elif this_operation == 'mean':
                                    this_scen_df = this_scen_df.groupby([c for c in pivot_info['id_columns'] if c != 'scenario']).mean().reset_index()
                                this_scen_df.columns = [c for c in pivot_info['id_columns'] if c != 'scenario'] + [plexos_param_names[this_csv]]


                            this_scen_df.insert(0,'scenario',this_scenario)
                            this_df_list.append(this_scen_df)

                    if not this_df_list:
                        print(f'No scenarios reported PLEXOS results for {this_csv}. Skipping that csv.')
                        continue
                    this_df = pd.concat(this_df_list)
                    this_col_list = [ x for x in this_df.columns if x not in pivot_info['id_columns'] ]   
                # For the rest of the csvs, just sum or take an average:
                elif pivot_info['operation'][pivot_info['csvs'] == this_csv] == 'sum':
                    id_cols_in_df = [ col for col in pivot_info['id_columns'] if col in this_df.columns ]
                    this_df = this_df.groupby(id_cols_in_df,as_index=False).sum()
                elif pivot_info['operation'][pivot_info['csvs'] == this_csv] == 'mean':
                    id_cols_in_df = [ col for col in pivot_info['id_columns'] if col in this_df.columns ]
                    this_df = this_df.groupby(id_cols_in_df,as_index=False).mean()
                elif this_operation not in ['sum','mean']: 
                    raise ValueError(f"""Operation "{this_operation}" is not implemented.""")

                # Allow for csvs that don't contain all the pivot table's ID columns by creating those columns and filling them with NaNs:
                id_cols_not_in_df = [ col for col in pivot_info['id_columns'] if col not in this_df.columns ]
                if any(id_cols_not_in_df):
                    for this_col in id_cols_not_in_df:
                        this_df[this_col] = np.nan  #need pandas Series of type object with np.nan values
                        this_df[this_col] = this_df[this_col].astype(object)

                # Assign the pre-defined column to this_col_list if it hasn't been custom-made above:
                if not this_col_list and pivot_name != 'metadata':
                    this_col_list = [ csv_list.loc[(csv_list['ignore']!=1) & (csv_list['csv']==this_csv),'label'].to_list()[0] ]

                # Up until now, any outputs in units of $ should be in 2004$.
                # Unforgivably hacky--Anywhere there's a "2004" in a column name, convert the dollar year to the one desired:
                if any('2004' in s for s in this_col_list):
                    for s in [x for x in this_col_list if '2004' in x]:
                        this_df[s] = inflate_series(this_df[s]) #this bokehpivot function uses the dollar year DOLLAR_YEAR, via core.GL (set above)
                        this_col_list = [ {s:s.replace('2004',DOLLAR_YEAR)}.get(x, x) for x in this_col_list ]
                        this_df = this_df.rename(columns={s:s.replace('2004',DOLLAR_YEAR)})

                # Exclude any extra columns and record the Tableau column definition(s) for this csv:
                this_df = this_df[pivot_info['id_columns'] + this_col_list] #sort to expected order and exclude any extraneous columns
                # The columns of region_mapping, line_mapping, and the geometry tables include geometry types are are set above:
                if pivot_name not in ['region_mapping','line_mapping','ctus_r_cs_mapping','ctus_cs_mapping'] and this_csv not in region_mapping.columns:
                    this_col_def = [ TableDefinition.Column(col, SqlType.double(), NULLABLE) for col in this_col_list ]
                col_defs = col_defs + this_col_def

                pivot = pd.merge(pivot,this_df,how='outer',on=pivot_info['id_columns'])

            # Optionally merge spatial data into the pivot.
            # Only do this if the pivot csv exported is to be used independently
            # and it needs regional data natively merged in
            if False:
                pivot, col_defs = merge_spatial_data(pivot,pivot_info,col_defs,region_mapping)

            # Write to csv:
            pivot.fillna('NULL').to_csv(output_path / (pivot_name + '.csv'),index=False) #have to fill NAs to NULL for direct writing to .hyper
            
            # Write to .hyper file:
            this_table_def = TableDefinition(
                table_name=pivot_name,
                columns = col_defs
            )
            try:
                update_hyper_file_from_csv(this_table_def,output_path / (pivot_name + '.csv'),output_path / (output_dir + '_pivot.hyper'),create_new)
                create_new = False
                print(f'''Added {pivot_name} to {(output_dir + '_pivot.hyper')}.''')
            except HyperException as ex:
                print(ex)
            
    print('Done.')


if __name__ == '__main__':
    main()
