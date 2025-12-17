
#Version 7/06/2022
#authors Nathan Lee and Pieter Gagnon

"""
How to use this script.

1. Copy the latest ATB csv (flattened version)- currently located here //nrelnas01/reeds/ReEDS_ATB_InputDataUpdate into your folder ~/ReEDS-2.0/input_processing/atb_updates_processing/input_files

2. Copy the latest 20YY_CSP_occ_vs_tes_duration_formatted csv (flattened version) currently located here //nrelnas01/reeds/ReEDS_ATB_InputDataUpdate into your folder ~/ReEDS-2.0/input_processing/atb_updates_processing/input_files

3. Copy the historic data csvs (previous year) from ~ReEDS-2.0/inputs/plant_characteristics into the ~/ReEDS-2.0/input_processing/atb_updates_processing/input_files
    For example if this is ATB 2022 updates to ReEDS the previous year historic data would the 2021 historic data csvs, and the necessary files would be (year will change!)
    1. battery_ATB_2021_moderate.csv
    2. conv_ATB_2021.csv
    3. csp_ATB_2021_moderate.csv
    4. geo_ATB_2021_moderate_FOM.csv
    5. ofs-wind_ATB_2021_moderate.csv
    6. ofs-wind_ATB_2021_moderate_rsc_mult.csv
    7. ons-wind_ATB_2021_moderate.csv
    8. h2-combustion_ATB_2021.csv
    9. upv_ATB_2021_moderate.csv

4. Review and update the `updates_setup()` function to ensure it points to the latest ATB csv file and that the ATB year and other assumptions are correct. This is a flat csv file from the ATB team. It is **NOT** the atb xslx file.  

5. Review and update each of the technology update functions to ensure they are correct for your application.  

6. Run the script - to run the script users can run the script and then call `run_updates()`, OR alternatively users can
   uncomment the final `#run_updates()` call in the script and then run the entire script.  
   If it is successful, you will get a successful completion message as an output. 

7. Copy the formatted ReEDS input csvs to the *~/ReEDS-2.0/inputs/plant_characteristics* folder.  

8. Add appropriate formatted ReEDS input csv file names to the *~/ReEDS-2.0/inputs/plant_characteristics/dollaryear.csv* file.  
"""

import pandas as pd
import numpy as np
import os

def updates_setup():
    """This function sets up the ReEDS ATB Input Data Update files, folders and general settings.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
         None
    
    Returns:  
            df_atb: Dataframe of atb  
            atb_year: current ATB year, such as 2022  
            atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
            atb_last_year: Last ATB year. This is set at 2050 for now.  
            dollar_yr_conv: dollar year conversion for historic data
            cpryears: Capital recovery period. This is typically 30 years for ReEDS inputs.  
            case: Core metric case. This is typically the "Market" case for ReEDS inputs.  
            atb_filters: Filters that will be used to extract data from the ATB input file.  
            atb_scenarios: ATB scenarios that will be used in ReEDS. These are typically "Moderate", "Advanced", and "Conservative"  
            input_dir: input files directory  
            output_dir: output files directory  
    """

    #Identify the current ATB csv file. This must be in a flat format
    atb_filename = 'ATB_2022_v111.csv'

    #set current ATB year
    atb_year = 2022
    
    #dollar year conversion for historic data
    #This needs to be updated annually
    #based on the ratio of the consumer price index annual average of ATB first year / previous year
    CPI_ATB_first_year = 258.811
    CPI_previous_year =  255.657
    dollar_yr_conv = CPI_ATB_first_year / CPI_previous_year
    
    #set output folder for formatted files
    output_dir = 'formatted_files_%s' % atb_year
    
    #set folder for necessary input files   
    input_dir = 'input_files'
    
    #create output_dir folder if it doesnt exist
    if os.path.isdir(output_dir) is False:
        os.mkdir(output_dir)
    
    #read in ATB csv
    df_atb = pd.read_csv(os.path.join(input_dir, atb_filename))

    #set first year for ATB - This will have to be changed if the ATB first year convention changes.
    #This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020
    atb_first_year = atb_year - 2
    
    #set atb_last_year
    atb_last_year = 2050

    #Identify the capital recovery period. This is typically 30 years for ReEDS inputs.
    crpyears = 30

    #Set the core metric case. This is typically the "Market" case for ReEDS inputs.
    case = 'Market'
    
    #create filters for ATB to pull data for reeds
    atb_filters ={'CRPYears': crpyears, 'Case': case}

    #set scenarios for atb data as array of ATB scenarios that will be used in ReEDS. These are typically "Moderate", "Advanced", and "Conservative"
    atb_scenarios = ['Moderate', 'Advanced', 'Conservative']

    return input_dir, output_dir, df_atb, atb_year, atb_first_year, atb_last_year, dollar_yr_conv, crpyears, case, atb_filters, atb_scenarios


#Technology update functions

def batteries(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, crpyears, case):
    """This function takes in necessary updates_setup arguments to create and write the battery updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_year: atb_year
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        dollar_yr_conv: dollar year conversion for historic data
        cpryears: Capital recovery period. This is typically 30 years for ReEDS inputs.  
        case: Core metric case. This is typically the "Market" case for ReEDS inputs.            
    
    Returns:  
            None
            
    """

    #read in battery technology format types
    batt_format = pd.read_csv(os.path.join(input_dir,'batt_plant_char_format.csv'))

    #read in historic data
    atb_prev_year = atb_year-1
    hist_df = pd.read_csv(os.path.join(input_dir, 'battery_ATB_%s_moderate.csv' % atb_prev_year))
    
    #filter for data prior to atb first year for historic data
    hist_df = hist_df[hist_df['t']<atb_first_year]
    
    #update historic data dollar year
    hist_df[['capcost', 'fom', 'vom']] = hist_df[['capcost', 'fom', 'vom']] *dollar_yr_conv

    #subset the data for the appropriate filters
    atb_subset_batt = df_atb[(df_atb['Case'] == case) & (df_atb['CRPYears'] ==crpyears) & (df_atb['Technology'] == "Utility-Scale Battery Storage")]
    
    #array of column names to filter ATB data on
    filter_list = ['DisplayName', "Scenario"]
    
    #dictionary of column names to map from ATB naming convention to ReEDS input naming convention
    col_dict = {'CAPEX':'capcost', 'Fixed O&M':'fom', 'variable':'t'}
    
    #roundtrip efficiency and variable O&M are constant right now for all batt techs and years, but may need to be changed in future.
    batt_rte= 0.85
    batt_vom = 0.0

    # Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in batt_format['file'].drop_duplicates():
        format_file = batt_format[batt_format['file']==file]
        df = pd.DataFrame()

        for i, row in format_file.iterrows():

            atb_subset = atb_subset_batt.copy()
            for col in filter_list:
                atb_subset = atb_subset[atb_subset[col]==row[col]]
            
            #build dataframe for tech
            atb_subset_pivot = atb_subset.pivot(index='variable', columns='Parameter', values='value')
            atb_subset_pivot = atb_subset_pivot.reset_index()
            atb_subset_pivot = atb_subset_pivot.rename(columns=col_dict)
            atb_subset_pivot = atb_subset_pivot[col_dict.values()]
            atb_subset_pivot['i'] = row['i']
            
            atb_subset_pivot['rte'] = batt_rte
            atb_subset_pivot['vom'] = batt_vom
            
            df = pd.concat([df, atb_subset_pivot], sort=False, ignore_index=True)
        
        #clean up the dataframes to align with ReEDS input file convention and add historic data
        df = df[['i', 't', 'capcost', 'capcost_energy',
                 'fom', 'fom_energy',
                 'vom', 'rte']].copy()
        df = pd.concat([hist_df, df], sort=False, ignore_index=True)
        
        #df.sort_values(by=["i", "t"], key=natsort_keygen())
        #sorting the i and t columns while ignoring the string 'battery_' in order to avoid need for natsort package
        df['bat'] = df['i'].str.split('_').str[1].astype(int)
        df=df.sort_values(by=['bat','t'],ascending=True).drop(columns='bat')

        df['t'] = df['t'].astype('int64')
        
        #write csv to output dir
        df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)     
#end batteries


def tes(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, crpyears, case):
    """This function takes in necessary updates_setup arguments to create and write the tes updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_year: atb_year
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        dollar_yr_conv: dollar year conversion for historic data
        cpryears: Capital recovery period. This is typically 30 years for ReEDS inputs.  
        case: Core metric case. This is typically the "Market" case for ReEDS inputs.            
    
    Returns:  
            None
            
    """

    #read in tes technology format types
    tes_format = pd.read_csv(os.path.join(input_dir,'tes_plant_char_format.csv'))

    #read in historic data
    atb_prev_year = atb_year-1
    hist_df = pd.read_csv(os.path.join(input_dir, 'tes_ATB_%s_moderate.csv' % atb_prev_year))
    
    #filter for data prior to atb first year for historic data
    hist_df = hist_df[hist_df['t']<atb_first_year]
    
    #update historic data dollar year
    hist_df[['capcost', 'fom', 'vom']] = hist_df[['capcost', 'fom', 'vom']] *dollar_yr_conv

    #subset the data for the appropriate filters
    atb_subset_tes = df_atb[(df_atb['Case'] == case) & (df_atb['CRPYears'] ==crpyears) & (df_atb['Technology'] == "Utility-Scale TES Storage")]
    
    #array of column names to filter ATB data on
    filter_list = ['DisplayName', "Scenario"]
    
    #dictionary of column names to map from ATB naming convention to ReEDS input naming convention
    col_dict = {'CAPEX':'capcost', 'Fixed O&M':'fom', 'variable':'t'}

    #roundtrip efficiency and variable O&M are constant right now for all tes techs and years, but may need to be changed in future.
    tes_rte= 0.412
    tes_vom = 0.0

    # Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in tes_format['file'].drop_duplicates():
        format_file = tes_format[tes_format['file']==file]
        df = pd.DataFrame()

        for i, row in format_file.iterrows():

            atb_subset = atb_subset_tes.copy()
            for col in filter_list:
                atb_subset = atb_subset[atb_subset[col]==row[col]]
            
            #build dataframe for tech
            atb_subset_pivot = atb_subset.pivot(index='variable', columns='Parameter', values='value')
            atb_subset_pivot = atb_subset_pivot.reset_index()
            atb_subset_pivot = atb_subset_pivot.rename(columns=col_dict)
            atb_subset_pivot = atb_subset_pivot[col_dict.values()]
            atb_subset_pivot['i'] = row['i']

            atb_subset_pivot['rte'] = tes_rte
            atb_subset_pivot['vom'] = tes_vom

            df = pd.concat([df, atb_subset_pivot], sort=False, ignore_index=True)
        
        #clean up the dataframes to align with ReEDS input file convention and add historic data
        df = df[['i', 't', 'capcost', 'capcost_energy',
                 'fom', 'fom_energy',
                 'vom', 'rte']].copy()
        df = pd.concat([hist_df, df], sort=False, ignore_index=True)
        
        #df.sort_values(by=["i", "t"], key=natsort_keygen())
        #sorting the i and t columns while ignoring the string 'tes_' in order to avoid need for natsort package
        df['tes'] = df['i'].str.split('_').str[1].astype(int)
        df=df.sort_values(by=['tes','t'],ascending=True).drop(columns='tes')

        df['t'] = df['t'].astype('int64')
        
        #write csv to output dir
        df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)     
#end tes


def conventional_generation(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, crpyears, case):
    """This function takes in necessary updates_setup arguments to create and write the conventional generation updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_year: atb year
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        dollar_yr_conv: dollar year conversion for historic data
        cpryears: Capital recovery period. This is typically 30 years for ReEDS inputs.  
        case: Core metric case. This is typically the "Market" case for ReEDS inputs.            
    
    Returns:  
            hist_df: historic conventional generation data is returned to use with renewable fired combustion technologies.  
            df: conventional generation data is returned to use with renewable fired combustion technologies.  
    """
    
    #read in conventional generation technology format types
    conv_format = pd.read_csv(os.path.join(input_dir,'conv_plant_char_format.csv'))
    
    #read in historic data
    atb_prev_year = atb_year -1 
    hist_df_full = pd.read_csv(os.path.join(input_dir, 'conv_ATB_%s.csv' % atb_prev_year))

    #Identify the conventional technologies that are not included in the ATB, but may be required in ReEDS. This Assumes that these techs DO NOT vary by scenario"""
    non_atb_techs = hist_df_full[hist_df_full['i'].isin(['CoalOldScr', 'CoalOldUns', 'o-g-s', 'CofireOld', 'CofireNew', 'lfill-gas'])] 
    hist_df_full = hist_df_full[hist_df_full['i'].isin(['CoalOldScr', 'CoalOldUns', 'o-g-s', 'CofireOld', 'CofireNew', 'lfill-gas']) is False] 
    
    #filter for data prior to atb first year for historic data
    hist_df = hist_df_full[hist_df_full['t']<atb_first_year]

    #remove the fillowing exclusion if CCS-max technologies are included in future releases.
    #drop coal-ccs-max and gas-cc-ccs-max technologies
    hist_df = hist_df[~hist_df['i'].isin(['coal-CCS_max','Gas-CC-CCS_max' ])]

    #update historic data dollar year
    hist_df[['capcost', 'fom', 'vom']]= hist_df[['capcost', 'fom', 'vom']]*dollar_yr_conv

    #subset the data with the appropriate filters
    atb_subset_conv = df_atb[(df_atb['Case'] == case) & (df_atb['CRPYears'] ==crpyears)]

    #array of column names to filter ATB data on
    filter_list = ['DisplayName','Scenario']
    
    #dictionary of column names to map from ATB naming convention to ReEDS input naming convention
    col_dict = {'OCC':'capcost', 'Fixed O&M':'fom', 'variable':'t'}
    
    #Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in conv_format['file'].drop_duplicates():
        format_file = conv_format[conv_format['file']==file]
        df = pd.DataFrame()
        
        for i, row in format_file.iterrows():
            
            atb_subset = atb_subset_conv.copy()
            for col in filter_list:
                atb_subset = atb_subset[atb_subset[col]==row[col]]
            
            #build dataframe for tech
            atb_subset_pivot = atb_subset.pivot(index='variable', columns='Parameter', values='value')
            atb_subset_pivot = atb_subset_pivot.reset_index()
            atb_subset_pivot = atb_subset_pivot.rename(columns=col_dict)
            atb_subset_pivot = atb_subset_pivot[col_dict.values()]
            atb_subset_pivot['i'] = row['i']
            
            df = pd.concat([df, atb_subset_pivot], sort=False, ignore_index=True)
        
        #clean up the dataframes to align with ReEDS input file convention and add historic data   
        df = df[['i', 't', 'capcost', 'fom']].copy() #, 'vom'
        df = df.merge(hist_df_full[['i', 't', 'heatrate', 'vom']], on=['i', 't'], how='left')    
        df = pd.concat([hist_df, df, non_atb_techs], sort=False, ignore_index=True)
        df.sort_values(by=['i','t'], ascending=True, inplace = True)
        df.reset_index(drop=True, inplace=True)
        df['t'] = df['t'].astype('int')
        
        #write csv to output dir
        df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)

        return hist_df, df
#end conventional generation


def geothermal(output_dir, df_atb, atb_first_year, crpyears, case, atb_scenarios):
    """This function takes in necessary updates_setup arguments to create and write the geothermal OCC multipiers updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        cpryears: Capital recovery period. This is typically 30 years for ReEDS inputs.  
        case: Core metric case. This is typically the "Market" case for ReEDS inputs.            
        atb_scenarios: ATB scenarios that will be used in ReEDS. These are typically "Moderate", "Advanced", and "Conservative"

    Returns:  
            None
    """
    
    #setting historic value here as integer for use in building dataframe
    val_historic_one = 1

    #copy subset of the atb datframe for geothermal
    geo_subset = df_atb[df_atb['Technology'] == 'Geothermal'].copy()
    
    #subset the data for the appropriate filters
    geo_capcost = geo_subset[geo_subset['Parameter'] == 'OCC']
    geo_capcost = geo_capcost[(geo_capcost['CRPYears'] == crpyears) & (geo_capcost['Case'] == case)]
    
    #dictionary of technology names to map from ATB naming convention to ReEDS input naming convention
    geo_techs_dict = {'Geothermal - Deep EGS / Binary':'deep-egs_pbinary',
                    'Geothermal - Deep EGS / Flash':'deep-egs_pflash',
                    'Geothermal - Hydro / Binary':'geohydro_pbinary',
                    'Geothermal - Hydro / Flash':'geohydro_pflash',
                    'Geothermal - NF EGS / Binary':'NF-EGS_pbinary',
                    'Geothermal - NF EGS / Flash':'NF-EGS_pflash',
                    }

    #Setup the column names for the geothermal technology dataframe
    geo_techs = ['deep-egs_pbinary', 'deep-egs_pflash', 'geohydro_pbinary', 'geohydro_pflash', 'NF-EGS_pbinary', 'NF-EGS_pflash']
    
    #Loop through each of the scenarios for ReEDS to extract corresponding data from input files and add to dataframe
    for scen in atb_scenarios:
        
        #build dataframe for tech
        geo_capcost_rev = geo_capcost[geo_capcost['Scenario'] == scen]
        geo_capcost_rev = geo_capcost_rev.pivot(index='variable', columns='DisplayName', values='value')
        geo_capcost_rev = geo_capcost_rev.astype('float')
        geo_capcost_rev = geo_capcost_rev.divide(geo_capcost_rev.loc[atb_first_year,:].values)
        geo_capcost_rev.rename(columns = geo_techs_dict, inplace= True)

        geo_capex_ones = pd.DataFrame(columns= geo_techs, index=np.arange(2010, atb_first_year), data=val_historic_one)
        geo_capcost_rev =pd.concat([geo_capex_ones, geo_capcost_rev], sort = False)
    
        #undiscovered pflash and pbinary have the same cost reduction trend as geohydro pflash and pbinary, respectively.
        undisc_techs = ['undisc_pflash', 'undisc_pbinary']
        undisc_vals = [geo_capcost_rev['geohydro_pflash'],geo_capcost_rev['geohydro_pbinary']]
        undisc_val_map = dict(zip(undisc_techs, undisc_vals))
        geo_capcost_rev = geo_capcost_rev.assign(**undisc_val_map)

        #clean up the dataframes to align with ReEDS input file convention and add historic data
        geo_capcost_rev = geo_capcost_rev[['geohydro_pflash', 'geohydro_pbinary', 'undisc_pflash', 'undisc_pbinary', 'NF-EGS_pflash', 'NF-EGS_pbinary', 'deep-egs_pflash', 'deep-egs_pbinary']].copy()
        geo_capcost_rev.index = geo_capcost_rev.index.astype(int) 
        geo_capcost_rev = geo_capcost_rev.astype('object') #to allow the values of 1 to be integer and rest be decimals
        geo_capcost_rev.loc[np.arange(2010,atb_first_year+1),:] = geo_capcost_rev.loc[np.arange(2010,atb_first_year+1),:].astype(int)
        
        #write csv to output dir
        geo_capcost_rev.to_csv(os.path.join(output_dir, 'geo_ATB_2022_%s.csv' % scen.lower()), index=True) #index on for years in geothermal outputs
# end geothermal 


def geothermal_fom(input_dir, output_dir, df_atb, atb_year, atb_first_year, crpyears, case):
    """This function takes in necessary updates_setup arguments to create and write the geothermal fixed operation and maintenance (FOM) cost multipiers updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_year: atb year
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        cpryears: Capital recovery period. This is typically 30 years for ReEDS inputs.  
        case: Core metric case. This is typically the "Market" case for ReEDS inputs.            
       
    Returns:  
            None
    """

    #read in geothermal technology format types
    geo_conv_format = pd.read_csv(os.path.join(input_dir,'geo_fom_plant_char_format.csv'))
    
    #read in historic data
    atb_prev_year = atb_year - 1
    geo_fom_hist = pd.read_csv(os.path.join(input_dir, 'geo_ATB_%s_moderate_FOM.csv' % atb_prev_year), header=None)

    #rename historic geothermal data columns for ease of use
    geo_fom_hist.rename(columns={0:"tech", 1:"t", 2:"value" }, inplace=True)

    #create array of undiscovered geothermal resource types
    undisc_geo_tech = ['undisc_pflash_1','undisc_pflash_2','undisc_pflash_3','undisc_pflash_4','undisc_pflash_5','undisc_pflash_6','undisc_pflash_7','undisc_pflash_8', 'undisc_pbinary_1', 'undisc_pbinary_2', 'undisc_pbinary_3', 'undisc_pbinary_4', 'undisc_pbinary_5', 'undisc_pbinary_6', 'undisc_pbinary_7', 'undisc_pbinary_8']

    #filter for data prior to atb first year for historic data and remove undisc_geo_tech    
    geo_fom_hist = geo_fom_hist[(geo_fom_hist["t"]< atb_first_year) & (~geo_fom_hist["tech"].isin(undisc_geo_tech))]
    
    #set historic fom cost data to 1
    geo_fom_hist['value'] = 1.0
    
    #subset the data for with appropriate filters and ensure the values are the correct type
    geo_subset = df_atb[(df_atb['Case'] == case) & (df_atb['CRPYears'] ==crpyears)].copy()
    geo_subset = geo_subset[(geo_subset['Technology'] == 'Geothermal') & (geo_subset['Parameter'] == 'Fixed O&M') ]
    geo_subset['value'] = geo_subset['value'].astype('float64')
    
    #array of column names to filter ATB data on
    filter_list = ['DisplayName', 'Scenario']
    
    #Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in geo_conv_format['file'].drop_duplicates():
        format_file = geo_conv_format[geo_conv_format['file']==file]
        df = pd.DataFrame()
        for j, row in format_file.iterrows():
                geo_subset2 = geo_subset.copy()
                
                for col in filter_list:
                    geo_subset2 = geo_subset2[geo_subset2[col]==row[col]]
                
                #build dataframe for tech
                geo_subset2 = geo_subset2[["variable", "DisplayName", "value"]]
                geo_subset2["tech"] = row["i"]
                geo_subset2['value'] = geo_subset2['value'] / geo_subset2['value'].max()
                df = pd.concat([df, geo_subset2], sort=False, ignore_index=True)
        
        df.rename(columns={"variable":"t"}, inplace=True)
        df.drop(columns=["DisplayName"], inplace=True)
        df = pd.concat([df, geo_fom_hist], sort=False, ignore_index=True)
        df.sort_values(by=['tech','t'], ascending=True, inplace = True)
        
        #undiscovered pflash and pbinary have the same cost reduction trend as geohydro pflash and pbinary, respectively.
        equivalent_undisc_dict = {'geohydro_pflash_1':'undisc_pflash_1', 'geohydro_pflash_2':'undisc_pflash_2','geohydro_pflash_3':'undisc_pflash_3','geohydro_pflash_4':'undisc_pflash_4','geohydro_pflash_5':'undisc_pflash_5','geohydro_pflash_6':'undisc_pflash_6','geohydro_pflash_7':'undisc_pflash_7','geohydro_pflash_8':'undisc_pflash_8', \
                                'geohydro_pbinary_1':'undisc_pbinary_1', 'geohydro_pbinary_2':'undisc_pbinary_2', 'geohydro_pbinary_3':'undisc_pbinary_3', 'geohydro_pbinary_4':'undisc_pbinary_4', 'geohydro_pbinary_5':'undisc_pbinary_5', 'geohydro_pbinary_6':'undisc_pbinary_6', 'geohydro_pbinary_7':'undisc_pbinary_7', 'geohydro_pbinary_8':'undisc_pbinary_8'}
        df_geohydro = df[df["tech"].str.contains('geohydro_')]
        df_geohydro = df_geohydro.replace({'tech':equivalent_undisc_dict})
        df = pd.concat([df, df_geohydro], sort=False, ignore_index=True)
        
        #clean up the dataframes to align with ReEDS input file convention and add historic data
        df = df[['tech', 't', 'value']].copy()
        df['t'] = df['t'].astype('int')
        df.sort_values(by=['tech','t'], ascending=True, inplace = True)
        
        #write csv to output dir
        df.to_csv(os.path.join(output_dir, '%s.csv' % file ), index=False, header=False)
# end geothermal fom


def offshore_wind(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, atb_filters):
    """This function takes in necessary updates_setup arguments to create and write the offshore wind updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        dollar_yr_conv: dollar year conversion for historic data
        atb_filters: Filters that will be used to extract data from the ATB input file.
        
    Returns:  
            None
    """    

    #read in offshore technology format types
    windoffs_char_format = pd.read_csv(os.path.join(input_dir,'ofs-wind_plant_char_format.csv'))
    
    #read in historic data
    atb_prev_year = atb_year-1
    hist_df = pd.read_csv(os.path.join(input_dir, 'ofs-wind_ATB_%s_moderate.csv' % atb_prev_year))

    #filter for data prior to atb first year for historic data
    hist_df = hist_df[hist_df['Year']<atb_first_year]
    
    #update historic data dollar year
    hist_df[['Cap cost 1000$/MW', 'Fixed O&M 1000$/MW-yr', 'Var O&M $/MWh']] =hist_df[['Cap cost 1000$/MW', 'Fixed O&M 1000$/MW-yr', 'Var O&M $/MWh']] *dollar_yr_conv

    #array of column names to filter ATB data on
    filter_list = ['DisplayName', 'Scenario']
    
    #dictionary of column names to map from ATB naming convention to ReEDS input naming convention
    col_dict = {'OCC':'Cap cost 1000$/MW', 'Fixed O&M':'Fixed O&M 1000$/MW-yr', 'CF':'CFc', 'variable':'Year'}
    
    #set variable O&M equal to zero
    vom = 0.0

    # Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in windoffs_char_format['file'].drop_duplicates():
        format_file = windoffs_char_format[windoffs_char_format['file'] == file]
        df = pd.DataFrame()

        for i, row in format_file.iterrows():

            atb_subset = df_atb.copy()

            for col in filter_list:
                atb_subset = atb_subset[atb_subset[col]==row[col]]
            
            #fitering for applicable atb_filters
            for k, v in atb_filters.items():
                atb_subset = atb_subset[atb_subset[k]==v]

            #build dataframe for tech    
            atb_subset_pivot = atb_subset.pivot(index='variable', columns='Parameter', values='value')
            atb_subset_pivot = atb_subset_pivot.reset_index()
            atb_subset_pivot = atb_subset_pivot.rename(columns=col_dict)
            atb_subset_pivot = atb_subset_pivot[col_dict.values()]
            atb_subset_pivot['Tech'] = row['i']
            atb_subset_pivot['Wind class'] = row['Wind class']
            
            #set vom
            atb_subset_pivot['Var O&M $/MWh'] = vom

            df = pd.concat([df, atb_subset_pivot], sort=False, ignore_index=True)

        #clean up the dataframes to align with ReEDS input file convention and add historic data   
        df = df[['Tech', 'Wind class', 'Year', 'Cap cost 1000$/MW', 'Fixed O&M 1000$/MW-yr', 'CFc', 'Var O&M $/MWh']].copy()
        df = pd.concat([hist_df, df], sort=False, ignore_index=True)
        df.sort_values(by=['Wind class','Year'], ascending=True, inplace = True)
        df['Year'] = df['Year'].astype('int')
        
        #write csv to output dir
        df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)
#end offshore wind


def onshore_wind(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, atb_filters):
    """This function takes in necessary updates_setup arguments to create and write the onshore wind updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_year: atb year
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        dollar_yr_conv: dollar year conversion for historic data
        atb_filters: Filters that will be used to extract data from the ATB input file.

    Returns:  
            None
    """  
    #read in onshore technology format types
    windons_char_format = pd.read_csv(os.path.join(input_dir,'ons-wind_plant_char_format.csv'))
    
    #read in historic data
    atb_prev_year = atb_year -1
    hist_df = pd.read_csv(os.path.join(input_dir, 'ons-wind_ATB_%s_moderate.csv' % atb_prev_year))
    
    #filter for data prior to atb first year for historic data
    hist_df = hist_df[hist_df['Year']<atb_first_year]

    #update historic data dollar year
    hist_df[['Cap cost 1000$/MW', 'Fixed O&M 1000$/MW-yr', 'Var O&M $/MWh']] = hist_df[['Cap cost 1000$/MW', 'Fixed O&M 1000$/MW-yr', 'Var O&M $/MWh']] *dollar_yr_conv
    
    #array of column names to filter ATB data on
    filter_list = ['DisplayName', 'Scenario']

    #dictionary of column names to map from ATB naming convention to ReEDS input naming convention
    col_dict = {'OCC':'Cap cost 1000$/MW', 'Fixed O&M':'Fixed O&M 1000$/MW-yr', 'CF':'CFc', 'variable':'Year'}

    #set variable O&M equal to zero
    vom = 0.0 

    # Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in windons_char_format['file'].drop_duplicates():
        format_file = windons_char_format[windons_char_format['file'] == file]
        df = pd.DataFrame()

        for i, row in format_file.iterrows():

            atb_subset = df_atb.copy()

            for col in filter_list:
                atb_subset = atb_subset[atb_subset[col]==row[col]]
            
            #fitering for applicable atb_filters 
            for k, v in atb_filters.items():
                atb_subset = atb_subset[atb_subset[k]==v]
            
            #build dataframe for tech    
            atb_subset_pivot = atb_subset.pivot(index='variable', columns='Parameter', values='value')
            atb_subset_pivot = atb_subset_pivot.reset_index()
            atb_subset_pivot = atb_subset_pivot.rename(columns=col_dict)
            atb_subset_pivot = atb_subset_pivot[col_dict.values()]
            
            #clean up the dataframes to align with ReEDS input file convention and add historic data
            atb_subset_pivot['Tech'] = row['i']
            atb_subset_pivot['Wind class'] = row['Wind class']
            
            #set vom
            atb_subset_pivot['Var O&M $/MWh'] = vom        
            
            df = pd.concat([df, atb_subset_pivot], sort=False, ignore_index=True)
        
        #clean up the dataframes to align with ReEDS input file convention and add historic data     
        df = df[['Tech', 'Wind class', 'Year', 'Cap cost 1000$/MW', 'Fixed O&M 1000$/MW-yr', 'CFc', 'Var O&M $/MWh']].copy()
        df = pd.concat([hist_df, df], sort=False, ignore_index=True)
        df.sort_values(by=['Wind class','Year'], ascending=True, inplace = True)
        df['Year'] = df['Year'].astype('int')
        
        #write csv to output dir
        df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)
# end onshore wind    


def utility_PV(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, atb_filters):
    """This function takes in necessary updates_setup arguments to create and write the utility PV updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Args:  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_year: atb year
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        dollar_yr_conv: dollar year conversion for historic data
        atb_filters: Filters that will be used to extract data from the ATB input file.

    Returns:  
            None
    """

    #read in utility PV technology format types
    upv_char_format = pd.read_csv(os.path.join(input_dir,'upv_plant_char_format.csv'))

    #read in historic data
    atb_prev_year = atb_year - 1
    upv_hist = pd.read_csv(os.path.join(input_dir, 'upv_ATB_%s_moderate.csv' % atb_prev_year))
    
    #filter for data prior to atb first year for historic data
    upv_hist = upv_hist[upv_hist['t']<atb_first_year]

    #update historic data dollar year
    upv_hist[['capcost', 'fom', 'vom']] =upv_hist[['capcost', 'fom', 'vom']] * dollar_yr_conv
    
    #array of column names to filter ATB data on
    filter_list = ["DisplayName", "Scenario"]
    
    #dictionary of column names to map from ATB naming convention to ReEDS input naming convention
    col_dict = {'OCC':'capcost', 'Fixed O&M':'fom', 'CF': 'cf_improvement','variable':'t'}
    
    #set variable O&M equal to zero
    vom = 0.0
    
    # Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in upv_char_format['file'].drop_duplicates():
        format_file = upv_char_format[upv_char_format['file']==file]
        df = pd.DataFrame()

        for i, row in format_file.iterrows():
        
            atb_subset = df_atb.copy()

            for col in filter_list:
                atb_subset = atb_subset[atb_subset[col]==row[col]]

            #fitering for applicable atb_filters
            for k, v in atb_filters.items():
                atb_subset = atb_subset[atb_subset[k]==v]
            
            #build dataframe for tech   
            atb_subset_pivot = atb_subset.pivot(index= 'variable', columns='Parameter', values='value')
            atb_subset_pivot = atb_subset_pivot.reset_index()
            atb_subset_pivot = atb_subset_pivot.rename(columns=col_dict)
            atb_subset_pivot = atb_subset_pivot[col_dict.values()]

            #set vom
            atb_subset_pivot['vom'] = vom

            df = pd.concat([df, atb_subset_pivot], sort=False, ignore_index=True)

        df = df[['t', 'capcost', 'fom', 'vom', 'cf_improvement']].copy()

        df = pd.concat([upv_hist, df], sort=False, ignore_index=True)
        
        #clean up the dataframes to align with ReEDS input file convention and add historic data  
        df['cf_improvement'] = df['cf_improvement'].astype('float')
        df['t'] = df['t'].astype('int64')
        df['cf_improvement'] = df['cf_improvement'] /df['cf_improvement'].min()
        df.loc[df['t']<atb_first_year,'cf_improvement'] = 1
        df['t'] = df['t'].astype('int')
        
        #write csv to output dir        
        df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)

    # end utility PV (UPV)


def csp(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, atb_filters):
    """This function takes in necessary updates_setup arguments to create and write the concentrated solar power (csp) updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    Concentrating solar power (csp) technology options in ReEDS encompass a subset of possible thermal system configurations, with and without thermal storage
        csp1 corresponds to a 6 hour storage duration and solar multiple of 1.0
        csp2 corresponds to an 8 hour storage duration and solar multiple of 1.3
        csp3 corresponds to a 10 hour storage duration and solar multiple of 2.4 
        csp4 corresponds to a 14 hour storage duration and solar multiple of 2.7

    Args:  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        update historic data dollar year
        atb_filters: Filters that will be used to extract data from the ATB input file.

    Returns:  
            None
    """  

    #read in annual update to csp technology options occ
    csp_techoptions_occ = pd.read_csv(os.path.join(input_dir,'%s_CSP_occ_vs_tes_duration_formatted.csv' % atb_year))    

    #read in csp technology format types
    csp_char_format = pd.read_csv(os.path.join(input_dir,'csp_plant_char_format.csv'))

    #read in historic data
    atb_prev_year = atb_year -1
    csp_hist = pd.read_csv(os.path.join(input_dir, 'csp_ATB_%s_moderate.csv' % atb_prev_year))

    #filter for data prior to atb first year for historic data
    csp_hist = csp_hist[csp_hist['t']<atb_first_year]  #kept for future use, but could revise years if the values never change.

    #update historic data dollar year
    csp_hist[['capcost', 'fom', 'vom']] = csp_hist[['capcost', 'fom', 'vom']] * dollar_yr_conv
    
    #array of column names to filter ATB data on
    filter_list = ["DisplayName", "Scenario"]
    
    #dictionary of technololgy in column names to map from ATB naming convention to ReEDS input naming convention
    tech_type_cols = {'Technology':'type', 'Year':'t', 'OCC':'capcost' } #this could be removed if we revise how csp team formats the file they give us
    
    #dictionary of tech names to map from ATB naming convention to ReEDS input naming convention
    tech_type_dict = {'14-HOUR TES':'csp1','10-HOUR TES':'csp2', '8-HOUR TES':'csp3', '6-HOUR TES':'csp4'}
    
    #dictionary of column names to map from ATB naming convention to ReEDS input naming convention
    col_dict = {'variable':'t', 'Fixed O&M':'fom', 'Variable O&M':'vom'}
    
    atb_subset = df_atb.copy()

    #Rename columns and technology types of CSP_technology options data
    csp_techoptions_occ.rename(columns=tech_type_cols,inplace=True)
    csp_techoptions_occ.replace({"type": tech_type_dict},inplace=True)

    #fitering for applicable atb_filters
    for k, v in atb_filters.items():
        atb_subset = atb_subset[atb_subset[k]==v]
    
    #fitering for applicable technology filters
    atb_subset =atb_subset[atb_subset['Technology']=='CSP']
    atb_subset = atb_subset[atb_subset["Parameter"].isin(['Fixed O&M', 'Variable O&M'])]
    atb_subset['value'] = atb_subset['value'].astype('float64')

    # Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in csp_char_format['file'].drop_duplicates():
        format_file = csp_char_format[csp_char_format['file']==file]
        df = pd.DataFrame()

        for i, row in format_file.iterrows():
            atb_subset2 = atb_subset
        
            for col in filter_list:     #these steps could be cleaned up in the future to make this smoother.
                csp_hist2 = csp_hist
                atb_subset2 = atb_subset2[atb_subset2[col]==row[col]]
            
            csp_techoptions_occ2 = csp_techoptions_occ   
                
            atb_subset_pivot = atb_subset2.pivot(index='variable', columns='Parameter', values='value')
            atb_subset_pivot = atb_subset_pivot.reset_index()
            atb_subset_pivot.rename(columns=col_dict, inplace=True)
            atb_subset_pivot['type'] = row['ReedsTech']
            
            csp_hist2 = csp_hist2[csp_hist2['type']==row['ReedsTech']]
            
            csp_techoptions_occ2 = csp_techoptions_occ2[csp_techoptions_occ['Scenario']==row['Scenario']]
            csp_techoptions_occ2 = csp_techoptions_occ2[csp_techoptions_occ2['type']==row['ReedsTech']]
            csp_techoptions_occ2.drop(columns='Scenario',inplace=True)
            csp_costs = pd.merge(csp_techoptions_occ2,atb_subset_pivot, on=["type", 't'])
            df = pd.concat([df, csp_costs,csp_hist2], sort=False, ignore_index=True)

        #clean up the dataframes to align with ReEDS input file convention 
        df = df[['type', 't', 'capcost', 'fom', 'vom']].copy()
        df['t'] = df['t'].astype('int')
        df.sort_values(by = ['type', 't'], ascending = [True, True], inplace=True)

        #write csv to output dir  
        df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)
#end csp

def h2_combustion(hist_df_conv, df_conv, input_dir, output_dir, atb_year, atb_first_year  ):
    """This function takes in necessary updates_setup arguments to create and write the renwable fired combutions (or reect) updates to csv.
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.
    
    H2-CT and H2-CC capital costs do not come directly from the ATB:
        Capital costs are calculated from natural gas AVG CF CT and AVG CF CC technologies, respectively, using a constant multiplier.
        Here the constant multiplier is calculated from historic year data and used through the projection.
        fom and vom are identifical to the natural gas AVG CF CT and AVG CF CC technologies.

    Args:  
        hist_df_conv: historic conventional generation data is returned to use with renewable fired combustion technologies.  
        df_conv: conventional generation data is returned to use with renewable fired combustion technologies.  
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb 
        atb_year: year of ATB release 
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  

    Returns:  
            None
    """    
   
    #read in h2fuel PV technology format types
    h2combustion_char_format = pd.read_csv(os.path.join(input_dir,'h2-combustion_plant_char_format.csv'))

    #dictionary of technololgy in column names to map from conventional generation technologies to H2-CT technologies
    tech_dict = {'Gas-CT': 'H2-CT', 'Gas-CC': 'H2-CC'}
    
    #copy the conventional generation technologies and fiter
    df_h2combustion = df_conv.copy(deep=True)
    df_h2combustion = df_h2combustion[df_h2combustion['i'].isin(['Gas-CT', 'Gas-CC'])]
    
    """
    This commented out code is pulling historic h2-ct reeds input data; however, this causes a disconnect as previously historic data was pulled from gas and then converted. to maintain consistency this approach is used here instead, below.
    h2combustion_hist = pd.read_csv(os.path.join(input_dir, 'h2-combustion_ATB_2021.csv'))
    hist_df = h2combustion_hist[h2combustion_hist['t']<atb_first_year]
    hist_df = hist_df[hist_df['i'].isin(['H2-CT', 'H2-CC'])]
    hist_df.loc[hist_df['i']=='H2-CC','fom'] = df_h2combustion.loc[(df_h2combustion['t'] < atb_first_year) & (df_h2combustion['i'] =='Gas-CC'),'fom'].values
    """
    
    #read in historic data
    atb_prev_year = atb_year -1
    h2combustion_hist = pd.read_csv(os.path.join(input_dir, 'h2-combustion_ATB_%s.csv' %atb_prev_year))

    #fiter historic data for data prior to the first year of ATB
    hist_df = h2combustion_hist[h2combustion_hist['t']<atb_first_year]
    
    #dollar year conversion is not needed as we swap it out later for conventional generation historic data.

    #copy the conventional generation technologies and fiter
    hist_df = hist_df[hist_df['i'].isin(['H2-CT', 'H2-CC'])]
    hist_df.loc[hist_df['i']=='H2-CC','fom'] = df_h2combustion.loc[(df_h2combustion['t'] < atb_first_year) & (df_h2combustion['i'] =='Gas-CC'),'fom'].values

    #determine historic multipliers for H2-CT And H2-CC from natural gas AVG CF CT and AVG CF CC technologies.
    df_h2combustion = df_h2combustion[df_h2combustion['t']>=atb_first_year]
    df_h2combustion['capcost'] = df_h2combustion['capcost'].astype('float64')

    #determine the multipliers to convert from conventional generation costs to h2fuel generation costs
    h2combustion_mult = hist_df[(hist_df['t'] == 2019) & (hist_df['i'] =='H2-CT')]['capcost'].iloc[0] / hist_df_conv[(hist_df_conv['t'] == 2019) & (hist_df_conv['i'] =='Gas-CT')]['capcost'].iloc[0]
    h2cc_mult = hist_df[(hist_df['t'] == 2019) & (hist_df['i'] =='H2-CC')]['capcost'].iloc[0] / hist_df_conv[(hist_df_conv['t'] == 2019) & (hist_df_conv['i'] =='Gas-CC')]['capcost'].iloc[0]
    
    #swap historic h2fuel for historic conventional (already in updated dollar year from conventional technologies)
    hist_df2 = hist_df_conv[hist_df_conv['t']<atb_first_year]
    hist_df2 = hist_df_conv[hist_df_conv['i'].isin(['Gas-CT', 'Gas-CC'])]

    df = pd.concat([hist_df2, df_h2combustion], sort=False, ignore_index=True)
    df['capcost'] = df['capcost'].astype('float64')

    df.loc[df['i']=='Gas-CT','capcost'] *= h2combustion_mult
    df.loc[df['i']=='Gas-CC','capcost'] *= h2cc_mult

    #clean up the dataframes to align with ReEDS input file convention 
    df.replace({"i": tech_dict},inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.sort_values(by = ['i', 't'], ascending = [False, True], inplace=True)
    df['t'] = df['t'].astype('int')
    file = h2combustion_char_format['file'].drop_duplicates()[0]
    
    #write csv to output dir  
    df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)
# end h2fuel tech


def offshore_wind_rsc_mult(input_dir, output_dir, df_atb, atb_year, atb_first_year, atb_filters):
    """This function takes in necessary updates_setup arguments to create and write the offshore wind rsc mutlipliers (or grid connection costs) updates to csv.  
    Offshore wind technologies also include the grid connection costs in ReEDS as this is a signficant share of total costs.   
    
    Users should review all of the values set in this function to ensure the updates are completed as desired.

    Args:   
        input_dir: input files directory  
        output_dir: output files directory  
        df_atb: Dataframe of atb  
        atb_year: year of ATB release 
        atb_first_year: First ATB year. This is 2 years prior to ATB year, for example, for the 2022 ATB the first year is 2020  
        atb_filters: Filters that will be used to extract data from the ATB input file.

    Returns:  
            None
    """  
    
    #read in reect PV technology format types
    ofswind_rsc_mlt_char_format = pd.read_csv(os.path.join(input_dir,'ofs-wind_rsc_mult_plant_char_format.csv'))  
    
    #read in historic data
    atb_prev_year = atb_year - 1
    ofswind_rsc_mut_hist = pd.read_csv(os.path.join(input_dir, 'ofs-wind_ATB_%s_moderate_rsc_mult.csv' %atb_prev_year))
    
    #filter historic data prior to ATB first year
    ofswind_rsc_mut_hist = ofswind_rsc_mut_hist[ofswind_rsc_mut_hist.iloc[:,0]<atb_first_year]
    ofswind_rsc_mut_hist.rename(columns={'Unnamed: 0':'t'}, inplace=True )

    #array of column names to filter ATB data on
    filter_list = ['DisplayName', 'Scenario']
    
    #fitering for applicable technology filters
    atb_subset = df_atb.copy()
    atb_subset = atb_subset.loc[(atb_subset['variable'] >= atb_first_year) & (atb_subset['Parameter'] == "GCC")]
    atb_subset = atb_subset.loc[(atb_subset['DisplayName'] == "Offshore Wind - Class 1") | (atb_subset['DisplayName'] == "Offshore Wind - Class 8") ]
   
    for k, v in atb_filters.items():
        atb_subset = atb_subset[atb_subset[k]==v]
    
    atb_subset['value'] = atb_subset['value'].astype('float64')

    # Loop through each of the necessary input files for ReEDS to extract corresponding data from input files and add to dataframe
    for file in ofswind_rsc_mlt_char_format["file"].drop_duplicates():
        format_file = ofswind_rsc_mlt_char_format[ofswind_rsc_mlt_char_format['file'] == file]
        scen = format_file["Scenario"].iloc[0]

        atb_subset2 = atb_subset[atb_subset["Scenario"]==scen]
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()
            
        df1["wind-ofs_1*wind-ofs_7"]  = atb_subset2[atb_subset2['DisplayName'] =="Offshore Wind - Class 1"]["value"] / atb_subset2[atb_subset2['DisplayName'] =="Offshore Wind - Class 1"]["value"].max()
        df1["t"] = atb_subset[atb_subset['DisplayName'] =="Offshore Wind - Class 1"]["variable"]
        df2["wind-ofs_8*wind-ofs_14"] = atb_subset2[atb_subset2['DisplayName'] =="Offshore Wind - Class 8"]["value"] / atb_subset2[atb_subset2['DisplayName'] =="Offshore Wind - Class 8"]["value"].max()
        df1.reset_index(drop=True, inplace=True)
        df2.reset_index(drop=True, inplace=True)
        df1["wind-ofs_8*wind-ofs_14"] = df2["wind-ofs_8*wind-ofs_14"]
        df1= df1[["t", "wind-ofs_1*wind-ofs_7", "wind-ofs_8*wind-ofs_14"]].copy()
        
        df = pd.concat([ofswind_rsc_mut_hist, df1], sort=False, ignore_index=True)
        
        #clean up the dataframes to align with ReEDS input file convention 
        df.rename(columns={"t":"t"}, inplace=True)
        df['t'] = df['t'].astype('int')
        
        #write csv to output dir  
        df.to_csv(os.path.join(output_dir, '%s.csv' % file), index=False)
# end offshore wind rsc_mult


def run_updates():

    """This function runs the ReEDS ATB Input Data Updates

    Args:  
        None          
    
    Returns:  
        None
    """

    successful_completion_message = "ReEDS ATB Input Updates complete! \n Be sure to 1) copy the formatted csvs to the ~/ReEDS-2.0/inputs/plant_characteristics folder, \n and 2) Add appropriate formatted ReEDS input csv file names to the ~/ReEDS-2.0/inputs/plant_characteristics/dollaryear.csv file."

    #run necessary setup and retrieve variables needed for for updates
    input_dir, output_dir, df_atb, atb_year, atb_first_year, atb_last_year, dollar_yr_conv, crpyears, case, atb_filters, atb_scenarios = updates_setup()

    #start technology updates
    
    #run battery updates
    batteries(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, crpyears, case)

    #run thermal energy storage updates
    tes(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, crpyears, case)

    #run conventional generation updates 
    #retrieve historic and updated conventional generation dataframes for use with renewable fired combustion technologies
    hist_df_conv, df_conv = conventional_generation(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, crpyears, case)

    #run geothermal occ and fom updates
    geothermal(output_dir, df_atb, atb_first_year, crpyears, case, atb_scenarios)
    geothermal_fom(input_dir, output_dir, df_atb, atb_year, atb_first_year, crpyears, case)

    #run offshore wind updates
    offshore_wind(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, atb_filters)

    #run onshore wind updates
    onshore_wind(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, atb_filters)
    
    #run onshore wind updates
    utility_PV(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, atb_filters)

    #run csp updates
    csp(input_dir, output_dir, df_atb, atb_year, atb_first_year, dollar_yr_conv, atb_filters)

    #run h2-ct and h2-cc technologies
    h2_combustion(hist_df_conv, df_conv, input_dir, output_dir, atb_year, atb_first_year)

    #run offshore wind rsc multipliers (grid connection costs)
    offshore_wind_rsc_mult(input_dir, output_dir, df_atb, atb_year, atb_first_year, atb_filters)

    print(successful_completion_message)


#Run updates
run_updates()


#end updates