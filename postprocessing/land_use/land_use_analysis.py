
'''
This script takes uses the outputs from reeds_to_rev.py to evaluate
land-use impacts for a ReEDS scenario. It is run automatically during a ReEDS
run when the `reeds_to_rev` switch is enabled. 

The processing is currently only configured to work for UPV, but will
hopefully be expanded to work for other technologies in the future. 

Note that land-use fields must be processed as part of the rev run to be analyzed here.

Passed arguments: 
    - path to ReEDS scenario 

Other input data:
    - rev supply curve aggreation file that contains land-use charactistics
    - mapping files for relevant land use categories (see /postprocessing/land_use/inputs)

Outputs:
    - land_use_[category].csv: saved to the output folder of the ReEDS runs.
'''

import os
import sys
import pandas as pd
import argparse
import time
from input_processing.ticker import makelog

#######################
# Helper functions 
#######################

# calculates total land area required
def totalLand(scen_path, upv_land_use, total_area):

    print("...processing total land use.")

    # check whether each supply curve point is full (within tolerance of 0.1 MW)
    upv_land_use['sc_full_bool'] = (abs(upv_land_use['capacity'] - upv_land_use['built_capacity']) < 0.1)
    upv_land_use['fraction_built'] =  upv_land_use['built_capacity'] / upv_land_use['capacity']
    upv_land_use['built_area_sq_km'] = upv_land_use['area_sq_km'] * upv_land_use['fraction_built']

    # calculate total area
    upv_land_use['built_capacity_MW'] = upv_land_use['built_capacity']
    upv_area = upv_land_use.groupby(['year'])[["built_capacity_MW", "built_area_sq_km"]].sum()

    # TO DO: add in total non-excluded area (current total is only available for development)
    # TO DO: modify to use multiple years of land-use data
    upv_area['avail_area_sq_km'] = total_area

    # save output
    upv_area.to_csv(os.path.join(scen_path, "outputs", "land_use_upv.csv"), float_format='%.2f')

# calculates capacity deployed by land use category
# assumes for now that capacity is evenly distributed by land-use type,
# but in the future we will want to revisit this assumption.
def calculateCapacityByUse(df, tag):

    # NAs indicate no cells or builds in that supply curve point
    # df = df.fillna(0)
    df['built_capacity'] = df['built_capacity'].fillna(0)
    df['fraction_built'] = df['fraction_built'].fillna(0)

    frac_column = "fraction_" + tag
    # get total area by class
    df[frac_column] =  df['cells'] / df['n_gids'] 
    df[tag + '_area_sq_km'] = df[frac_column] *  df['area_sq_km']
    
    # amount of capacity built in each land class is (total capacity built in sc_point) x (share of land use / total sc point)
    df[tag + '_built_capacity'] = df[frac_column] *  df['built_capacity']

    # area use is a function of the fraction of total sc curve area used
    df[tag + '_area_sq_km_built'] = df[tag + '_area_sq_km'] * df['fraction_built']
    return df


# helper function to parse any columns with JSON data
def parseJSON(df, col, var, mapping=None):
    out = df[col].apply(pd.read_json, typ="series")

    # NAs are zeros
    out.fillna(0, inplace=True)
    # get sum of cells classified by land-use
    out['n_gids_land_use'] = out.sum(axis=1)

    # line up sc_point_gid, year, and other info from original mapping data
    out['sc_point_gid'] = df['sc_point_gid']
    out['state'] = df['state']
    out['area_sq_km'] = df['area_sq_km']
    out['n_gids'] = df['n_gids']
    
    # land-use mapping files do not vary by year, but this capability may be added eventually
    # out['year'] = df['year']  
    
    # compare total cells in sc point to those mapped by the category
    # use '9999' to indicate capacity built on cells that aren't classified
    out[9999] = out['n_gids'] - out['n_gids_land_use']
    
    # melt mapping data to long format
    out = out.melt(id_vars=["sc_point_gid", "state", "area_sq_km", "n_gids", "n_gids_land_use"], var_name=var, value_name="cells")

    # add mapping details (files found in ReEDS postprocessing module)
    if mapping is not None:
        try:
            df_map = pd.read_csv(os.path.join("postprocessing", "land_use", "inputs", mapping + ".csv"))
            out = out.merge(df_map.drop("color", axis=1, errors="ignore"), how="left", on=var)
            out.drop([var,'n_gids_land_use'], axis=1, inplace=True)
        except:
            print("Error reading specified mapping file.")
    return out

# this function processes land-use categories defined by JSONs
def processLandUseJSON(df_name, df_vals, scen_path, land_use_map, upv_land_use):

    print("...processing %s classification." % df_name, end=" ")

    # get nlcd land classifications
    land_class = parseJSON(land_use_map, df_vals[0], df_vals[1], mapping=df_vals[2])
        
    # expand land-use classification to match years of builds
    land_class_merge = expandYears(land_class, upv_land_use)
    land_use = land_class_merge.merge(upv_land_use[['year', 'sc_point_gid', 'built_capacity', 'fraction_built']], on=["sc_point_gid", "year"], how="outer")    

    # allocate capacity to each land use category    
    land_use = calculateCapacityByUse(land_use, df_name)

    # rename cells column
    var_name = df_name + "_n_gids"
    land_use.rename(columns={"cells": var_name}, inplace=True)

    # drop rows where there the sc doesn't have that classification to reduce file size
    # keep rows with no built capacity as this helps with calculating total use later
    land_use = land_use[land_use[var_name] > 0]

    # save outputs
    land_use.to_csv(os.path.join(scen_path, "outputs", "land_use_%s.csv.gz" % df_name), float_format='%.2f', index=False)

# expand land-use mapping for all ReEDS years
def expandYears(land_mapping, reeds_results):
    df_out = pd.DataFrame()
    years = reeds_results['year'].unique().tolist()
    for y in years:
        df = land_mapping.copy()
        df['year'] = y
        df_out = pd.concat([df_out, df])
    return df_out

# process use of land identified as species range/habitat
def getSpeciesImpact(scen_path, upv_land_use):
    
    print("...processing species habitat and range information.")
    
    species_cols = [col for col in upv_land_use.columns if 'range' in col or 'habitat' in col]
    id_cols = ['year', 'region', 'sc_point_gid', 'sc_full_bool', 'n_gids', 'fraction_built', 'area_sq_km', 'built_area_sq_km']
    species_land_use = upv_land_use[id_cols+ species_cols]
    
    # melt to long
    species_land_use = pd.melt(species_land_use, id_vars=id_cols, value_vars=species_cols, var_name="species", value_name="species_n_gids")

    # categorize by species and impact type
    species_land_use['species_extent'] = species_land_use['species'].str.replace(".*_", "", regex=True)
    species_land_use['species'] = species_land_use['species'].str.replace("_.*", "", regex=True)

    # calculate density
    species_land_use['species_density'] = species_land_use['species_n_gids'] / species_land_use['n_gids']

    # save outputs
    species_land_use.to_csv(os.path.join(scen_path, "outputs", "land_use_species.csv.gz"), float_format='%.2f', index=False)

# primary process function called by main loop for each tech
def getLandUse(scenario, scen_path, rev_paths, tech):

    print("Getting %s land-use data for %s" % (tech, scenario))

    # select rev case for tech being processed
    rev = rev_paths.loc[rev_paths.tech == tech].squeeze()

    # for older UPV rev runs land-use data had to be added in a separate file. 
    # newer runs using the 2022 UPV sc will now have this directly in the "aggregation" sc file
    if "2021_Update" in rev.rev_path:
        map_file = "%s_agg_land_use.csv.gz" % rev.rev_case
    else:
        map_file = "%s_supply-curve-aggregation.csv" % rev.rev_case

    try:
        land_use_map = pd.read_csv(os.path.join(rev.rev_path, map_file))
    except:
        sys.exit("Error reading rev mapping file. Check that appropriate file is in the rev folder.")

    # load ouputs from reeds_to_rev.py script
    builds_upv = pd.read_csv(os.path.join(scen_path, "outputs", "df_sc_out_upv_reduced.csv"))

    # if using land-use features that change over time then merge on year, otherwise ignore year
    upv_land_use = builds_upv.merge(land_use_map, on=['sc_point_gid'])
    total_area = land_use_map['area_sq_km'].sum()

    ## Total land area estimates ####
    totalLand(scen_path, upv_land_use, total_area)

    ## Land classifications defined by JSON mappings ####

    # dictionary defines land use categories specified with JSON files
    # format is short name: (name of column in rev mapping, new column name, mapping file for renaming values if any)
    json_data = {"fed_land": ("fed_land_owner", "fed_land_owner", "federal_land_lookup"), # federal land ownership
                 "nlcd": ("usa_mrlc_nlcd2011", "nlcd_value", "nlcd_classifications")}     # national land cover database

    for df_name in json_data:
        
        st = time.time()
        processLandUseJSON(df_name, json_data[df_name], scen_path, land_use_map, upv_land_use)
        et = time.time()
        print("(elapsed time: %0.2f seconds)" % (et - st))

    ## Species habitat and range ####
    getSpeciesImpact(scen_path, upv_land_use)


#######################
# Main 
#######################

if __name__ == '__main__':

    # Argument inputs
    parser = argparse.ArgumentParser(description="""This script calculates evaluates land-use implications for 
                                                    solar buildouts from one or more ReEDS runs. 
                                                    Requires the 'reeds_to_rev.py' to have been run.""")
    parser.add_argument("scenario", help="Folder of ReEDS run")
    args = parser.parse_args()

    scen = os.path.basename(args.scenario)
    scen_path = args.scenario

    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(args.scenario,'gamslog.txt'))

    print("\nRunning 'land_use_analysis.py' script.\n")
    
    try:
        # get path to relevant rev files and switch settings 
        rev_paths = pd.read_csv(
            os.path.join(scen_path, "inputs_case", "supplycurve_metadata", "rev_supply_curves.csv"))

        # eventual plan is to add function calls for other techs (namely wind-ons)
        getLandUse(scen, scen_path, rev_paths, tech="upv")
    except Exception as err:
        print(err)
    print("")
    
    print("Completed 'land_use_analysis.py' script.")

    # debugging 
    # python postprocessing/land_use/land_use_analysis.py /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/runs/2022_03_26_AllOptions_sites
    # python /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/postprocessing/bokehpivot/reports/interface_report_model.py "ReEDS 2.0" /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/runs/2022_03_26_AllOptions_sites all No none /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/postprocessing/bokehpivot/reports/templates/reeds2/land_use.py one /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/runs/2022_03_26_AllOptions_sites/outputs/reeds-report-land no
