# -*- coding: utf-8 -*-
"""
The purpose of this script is to group existing generating 
units into historical, binned vintages (hintages) 

The primary arguments are the plant data file to use, the number of bins, 
and the minimum deviation across bins. There are also operations specific
to proessing data for whether or not GSw_WaterMain are enabled. 

Kmeans clustering is the default option and the general sequence, by tech and 
BA combinations, is as follows:
    
    1. Check to see if the number of unique units is less than the number of bins
       - if true, check to see if the deviation across all those different units exceeds the minimum deviation
         - if true, use the raw data and assign bins to each individual units
         - if false, proceed with binning 
       - if false, proceed with binning
    2. Perform capacity-weighted kmeans clustering with the maximum number of bins
       - Maximum number of bins first defined as the minimum of..
         - number of bins assigned by user
         - number of unique heat rates
         - number of units in the tech/BA combination
    3. Check to see if the deviation across all heat rate centroids exceed the minimum deviation 
       - if so, proceed to '4'
       - if not, return to '2' but reduce the number of bins by 1
    4. Assign units to their nearest heat rate bin
       - if only one unique unit in a bin, assign its original heat rate
       - if more than one unit in a bin, assign the capacity-weighted average
    5. For all years from 2010-2100, compute the remaining amount of capacity
       based on the units specified retirement date and compute the remaining
       units' capacity-weighted-average characteristics (FOM/VOM/HR/...)

---

For testing - the default arguments are passed in to the main(...) function

"""
#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import math
import numpy as np
import os
import sys
import pandas as pd
import warnings
import datetime
from sklearn.cluster import KMeans
from sklearn.exceptions import ConvergenceWarning
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
# Time the operation of this script
tic = datetime.datetime.now()

# ignore ConvergenceWarnings that occur in this file from the kmeans function 
warnings.filterwarnings("ignore", category=ConvergenceWarning)


#%% ===========================================================================
### --- FUNCTIONS AND CLASSES ---
### ===========================================================================
class grouping:
    def __init__(self, nbins, *args, **kwargs):
        #df = tdat
        #nbins=6
        if nbins == 'unit':
            self.df = self.unit(*args)
        elif nbins == 'group':
            self.df = self.group(*args)
        else:
            nbins = int(nbins)
            self.df = self.kmeans(nbins, *args, **kwargs)
                  
        
    def unit(self, input_df, *args, **kwargs):
        '''
        This method creates a unique hintage bin for every generator
        
        input_df: pandas DataFrame object containing ReEDS generators
        *args: collects unused positional arguments to simplify code
        **kwargs: collects unused keyword arguments to simplify code
        '''
        output_df = pd.DataFrame()
        # NOTE: The calculations here and below in group() can probably be done 
        # faster by group (without a loop).
        for ba in input_df.r.unique():
            ba_df = input_df[input_df.r == ba].copy()
            for tech in ba_df.TECH.unique():
                df = ba_df[ba_df.TECH == tech].copy()
                df['bin'] = df.reset_index(drop=True).index + 1
                output_df = pd.concat([output_df, df])

        return output_df
    

    def group(self, input_df, col, *args, **kwargs):
        '''
        This method creates hintage bins for unique region, tech, and specified
        column combinations.
        
        input_df: (pandas.DataFrame object) containing ReEDS generators
        col: (str) The name of the column used in binning
        *args: collects unused positional arguments to simplify code
        **kwargs: collects unused keyword arguments to simplify code
        '''
        grouping_df = (input_df[['r', 'TECH', col]]
                       .drop_duplicates()
                       .reset_index(drop=True)
                       )
        output_df = pd.DataFrame()        
        for ba in grouping_df.r.unique():
            ba_df = grouping_df[grouping_df.r == ba].copy()
            for tech in ba_df.TECH.unique():
                tech_df = ba_df[ba_df.TECH == tech].copy()
                tech_df['bin'] = tech_df.reset_index().index + 1
                
                output_df = pd.concat([output_df, tech_df.reset_index(drop=True)])
        

        output_df = input_df.merge(output_df,
                                   on=['r','TECH', col],
                                   how='left'
                                   )
        return output_df
    

    class _kmeans:
        def __init__(self, input_df, col, bins, minSpread=2000, n_init=10):
            '''
            bin and return the centroids or breakpoints of each bin
    
            df (DataFrame object): Pandas Dataframe containing data for binning
            col (str): the column name that is to be binned
            bins (int): the number of desired bins
            '''
            self.bins = bins
            df = input_df.copy()
            
            #if the number of unique heat rates is already less than the number of bins
            if len(df[col].unique()) <= bins:
                #no matter what, set the bins to the number of unique heat rates
                self.bins = len(df[col].unique())

                # in order for us to skip binning, we'll need to check
                # if the minimum difference across all unique heat rates
                # exceeds the minSpread - if so, we can justify
                # avoiding the binning algorithm
                if len(df[col].unique()) > 1:
                    mindiff_unique = min([abs(j-i) for i, j in zip(df[col].unique()[:-1], 
                                                                   df[col].unique()[1:])])
                    
                #note that if we only have one unique value for this tech/BA combo 
                #heat rate, then we can skip binning altogether
                if len(df[col].unique()) == 1:
                    mindiff_unique = minSpread + 1
                
            # if the number of unique elements is greater than the number of bins
            # make sure we skip the following condition and perform binning
            else:
                mindiff_unique = minSpread + 1
            
            # if you can use the raw data as is - ie if the observed heat rates
            # are disparate enough such that they exceed minspread and the 
            # the number of units is not greater than the number of bins -
            # then just use the raw data
            if len(df[col].unique()) <= bins and mindiff_unique > minSpread:
                bins = len(df[col].unique())
                # if the maximum deviation across all heat rates 
                # is less than the minimum deviation
                if (df[col].max() - df[col].min()) < minSpread:
                    # put all units into one bin
                    df['centroid'] = df[col].mean()
                    df['bin'] = 1
                else:
                    df['centroid'] = df[col]
                    temp = pd.DataFrame(data=dict(centroid=df[col].unique(), bin=None))
                    temp.bin = temp.index + 1
                    df = df.merge(temp, on='centroid', how='left')
                self.centers = df
            
            # if you can't just use the raw data
            else:
                # if the number of bins exceeds the number of observations
                # reset the number of bins to the length of the data
                # note if the heat rates were not disparate enough
                # we would've caught that in the previous condition block
                if bins > len(df.index):
                    self.bins = max(len(df)-1, 1)
    
                # make a temporary binning DF
                bin_df = pd.concat([df[col],
                                   pd.DataFrame(columns=['centroid', 'upper',
                                                         'lower', 'bin'])])
                bin_df.rename(columns={0: col}, inplace=True)
    
                # establish parameters necessary for the while loop
                spread = minSpread - 1
                nbins = self.bins
                
                # while the minimum spread hasn't been exceeded
                # and the number of bins haven't been exhausted
                # keep attempting to cluster - if these conditions
                # haven't been met, try again with one fewer bin                
                while spread < minSpread or nbins == 1:  
                    df = input_df.copy()
                    
                    # initialize the centroids - note that the
                    # random_state argument implies a static seed
                    # for the random processes/distribution-draws 
                    # used in the kmeans function           
                    centroids_obj = KMeans(
                        n_clusters=nbins, random_state=0, max_iter=1000, n_init=n_init,
                    ).fit(df[[col]].to_numpy(), sample_weight = df['Summer.capacity'].to_numpy())
                    
                    #need to convert array of length-one arrays to one long array
                    centroids = [ i[0] for i in centroids_obj.cluster_centers_]

                    # create a list of unique centroids
                    centroids = list(set(centroids))
                                        
                    # make the binning matrix
                    k = pd.DataFrame(index=df[col], columns=centroids).reset_index()
                    k = k.set_index('HR')

                    # compute the difference between the observed heat rate and the centroid                                        
                    for c in centroids:
                        k[c] = abs(k.index - c)
                        
                    # select the closest centroid
                    k['centroid'] = k.columns[k[centroids].values.argmin(1)]
        
                    # Merge centroids onto original DF
                    k_bins = k.centroid.drop_duplicates().reset_index().copy()
                    k_bins['bin'] = k_bins.index + 1
                    k_map = k.reset_index().merge(k_bins[['centroid', 'bin']],
                                                  on='centroid',
                                                  how='left').set_index('HR')
                    
                    # find the minimum deviation across all heat rate combinations
                    if len(centroids)>1:
                        spread = min([abs(j-i) for i, j in zip(k['centroid'].unique()[:-1], 
                                                               k['centroid'].unique()[1:])])
                    # if there is only one centroid, 
                    # set the conditional to exit the while loop
                    else:
                        spread = minSpread + 1 
                    
                    #reset the index for formatting
                    k_map.reset_index(inplace=True)                    
                                   
                    nbins -= 1
                    #end of while loop for nbins and spread < minspread check
                
                # merge the binned heat rates with the original plant data
                # this will be the output to the kmeans function
                self.centers = df.merge(k_map.drop_duplicates()[[col, 'centroid', 'bin']],
                                        how='left', on=col)
    

    def kmeans(self, nbins, input_df, *args, **kwargs):
        '''
        bin and return the centroids or breakpoints of each bin

        df (DataFrame object): Pandas Dataframe containing data for binning
        col (str): the column name that is to be binned
        bins (int): the number of desired bins
        *args: collects unused positional arguments to simplify code
        **kwargs: collects unused keyword arguments to simplify code
        '''
        print("Starting kmeans clustering of existing generators")
        print("using {} bins and a minimum deviation of {} mmBTU/MWh \n".format(
            nbins, kwargs['minSpread']))
        print("Note that the clustering can result in warnings if the heat rates")
        print("or number of unique plants exceeds the bins specified in the loop")
        tdat=pd.DataFrame()
        
        # for all unique BA/technology combinations...
        for i in input_df.id.unique():
            tdat = pd.concat([tdat,
                              self._kmeans(input_df[input_df.id == i],
                                     'HR',
                                     nbins,
                                     minSpread=int(kwargs['minSpread'])
                                     ).centers])
        return tdat


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================
def main(reeds_path, inputs_case):
    print('Starting WriteHintage.py')

    # #%% Settings for testing
    # reeds_path = os.path.expanduser('~/github/ReEDS-2.0')
    # inputs_case = os.path.join(
    #     reeds_path,'runs','v20231027_yamM0_Z45_h_d_365_transreg_z69_core','inputs_case')

    #%% Inputs from switches
    sw = reeds.io.get_switches(inputs_case)

    nBin = int(sw.numhintage)
    retscen = sw.retscen
    mindev = int(sw.mindev)
    GSw_WaterMain = sw.GSw_WaterMain    
    GSw_RetireYears_Coal = int(sw.GSw_RetireYears_Coal)
    GSw_RetireYears_Thermal = int(sw.GSw_RetireYears_Thermal)
    GSw_Clean_Air_Act = int(sw.GSw_Clean_Air_Act)

    #%%
    # Inflation factor 1987$ to 2004$
    inflator = 1.69
    
    # Dictionary of relevant technology groups
    TECH = {
    # This is not all technologies that do not having cooling, but technologies
    # that are (or could be) in the plant database.
    'no_cooling':['upv', 'pvb', 'gas-ct', 'geohydro_allkm',
                    'battery_li', 'pumped-hydro', 'pumped-hydro-flex', 
                    'hydUD', 'hydUND', 'hydD', 'hydND', 'hydSD', 'hydSND', 'hydNPD',
                    'hydNPND', 'hydED', 'hydEND', 'wind-ons', 'wind-ofs', 'caes'
                    ]
    }

    # Import mapping files
    r_county = pd.read_csv(
        os.path.join(inputs_case,'r_county.csv'), index_col='county').squeeze(1)

    # Import generator database
    indat = pd.read_csv(os.path.join(inputs_case,'unitdata.csv'),
                        low_memory=False
    )

    # Map counties to modeled regions
    indat['r'] = indat.FIPS.map(r_county)

    # Apply inflation to VOM costs
    indat['T_VOM'] *= inflator
    indat['T_CCSV'] = indat.T_VOM + inflator * indat.T_CCSV

    # Apply inflation and add capital expenditures to FOM costs
    indat['T_FOM'] = inflator * (indat.T_FOM + indat.T_CAPAD)
    indat['T_CCSF'] = indat.T_FOM + inflator * indat.T_CCSF

    # Concatenate tech names based on whether water analysis is on -or- leave them alone
    if GSw_WaterMain == '1':
        # If techs do not have a cooling technology, then replace coolingwatertech with the tech name
        indat.loc[indat['tech'].isin(TECH['no_cooling']),
                  'coolingwatertech'] = indat.loc[indat['tech'].isin(TECH['no_cooling']),'tech']
        indat['tech'] = indat.coolingwatertech

    ### NOTE: New addition for columns AO:AR, AW:AX in the plant file
    ad = indat[["tech", "r", "ctt", "summer_power_capacity_MW", "TC_WIN", retscen,
                "StartYear", "IsExistUnit", "HeatRate", "T_VOM", "T_FOM",
                "T_CCSROV", "T_CCSF", "T_CCSV", "T_CCSHR", "T_CCSCAPA", "T_CCSLOC"]].copy() 

    # Rename columns in ad
    rename = {
        'tech'   : 'TECH',
        'r'      : 'r',
        'ctt'    : 'ctt',
        'summer_power_capacity_MW'    : 'Summer.capacity',
        'TC_WIN' : 'Winter.capacity',
        retscen  : 'RetireYear',
        'StartYear' : 'onlineyear',
        'IsExistUnit' : 'EXIST',
        'HeatRate' : 'HR',
        'T_VOM'  : 'VOM',
        'T_FOM'  : 'FOM',
        'T_CCSROV' : 'CCS_Retro_OvernightCost',
        'T_CCSF' : 'CCS_Retro_FOM',
        'T_CCSV' : 'CCS_Retro_VOM',
        'T_CCSHR': 'CCS_Retro_HR',
        'T_CCSCAPA': 'CCS_Retro_CapAdjust',
        'T_CCSLOC': 'CCS_Retro_LocFactor'
    }
    ad.rename(columns=rename, inplace=True)

    # Subset only generators that exist
    ad = ad[ad.EXIST]

    # Only want those with a heat rate - all other binning is arbitrary
    # because the only data we get from generator database is the capacity and heat
    # rate but O&M costs are assumed
    df = ad[(~ad.HR.isna()) & (~ad.TECH.isin(['geohydro_allkm', 'CofireNew']))]

    # Adjust retirement dates of coal specifically or thermal techs generally based on switch

    tech_table = pd.read_csv(
        os.path.join(inputs_case, 'tech-subset-table.csv')).set_index('Unnamed: 0')
    coal_techs = [x.lower() for x in tech_table[tech_table['COAL'] == 'YES'].index.values.tolist()]
    thermal_techs = [x.lower() for x in tech_table[(tech_table['COAL'] == 'YES') | 
                                                   (tech_table['GAS'] == 'YES') | 
                                                   (tech_table['NUCLEAR'] == 'YES') |
                                                   (tech_table['OGS'] == 'YES')].index.values.tolist()]

    current_yr = datetime.date.today().year
    
    if GSw_RetireYears_Thermal == 0:
        # Thermal retirements are not adjusted, data is straight from EIA unit database
        # Coal retirement can be adjusted separately when GSw_RetireYears_Thermal = 0
        # if GSw_RetireYears_Coal = 0, coal retirements are not adjusted, data is straight from EIA unit database
        if GSw_RetireYears_Coal < 0:
            # For coal units with retire year before current_yr - GSw_RetireYears_Coal, they are forced to retire in current_yr.
            # For coal units with retire year after or equal to current_yr - GSw_RetireYears_Coal, their lifetime is shorted by |GSw_RetireYears_Coal|.
            df.loc[(df['RetireYear'] < current_yr - GSw_RetireYears_Coal) & (df['RetireYear'] > current_yr)
                & (df['TECH'].isin(coal_techs)), 'RetireYear'] = current_yr
            df.loc[(df['RetireYear'] >= current_yr - GSw_RetireYears_Coal) & (df['TECH'].isin(coal_techs)),
                'RetireYear'] += GSw_RetireYears_Coal

        elif GSw_RetireYears_Coal > 0:
            # Lifetime of all currently operating coal units is extended by GSw_RetireYears_Coal
            df.loc[(df['RetireYear'] > current_yr) & (df['TECH'].isin(coal_techs)),
                'RetireYear'] += GSw_RetireYears_Coal

    # Adjust thermal techs' retirement dates when GSw_RetireYears_Thermal != 0
    elif GSw_RetireYears_Thermal < 0:
        # For thermal units with retire year before current_yr - GSw_RetireYears_Thermal, they are forced to retire in current_yr.
        # For thermal units with retire year after or equal to current_yr - GSw_RetireYears_Thermal, their lifetime is shorted by |GSw_RetireYears_Thermal|.
        df.loc[(df['RetireYear'] < current_yr - GSw_RetireYears_Thermal) & (df['RetireYear'] > current_yr)
               & (df['TECH'].isin(thermal_techs)), 'RetireYear'] = current_yr
        df.loc[(df['RetireYear'] >= current_yr - GSw_RetireYears_Thermal) & (df['TECH'].isin(thermal_techs)),
               'RetireYear'] += GSw_RetireYears_Thermal

    elif GSw_RetireYears_Thermal > 0:
        # Lifetime of all currently operating thermal units is extended by GSw_RetireYears_Thermal
        df.loc[(df['RetireYear'] > current_yr) & (df['TECH'].isin(thermal_techs)),
               'RetireYear'] += GSw_RetireYears_Thermal
        
    # Group up similar generators
    dat = df.groupby([
        'TECH', 'r', 'HR', 'onlineyear', 
        'RetireYear', 'VOM', 'FOM',"CCS_Retro_OvernightCost", "CCS_Retro_FOM", 
        "CCS_Retro_VOM", "CCS_Retro_HR", "CCS_Retro_CapAdjust", "CCS_Retro_LocFactor",
    ])[['Summer.capacity','Winter.capacity']].sum().reset_index()

    # Remove 'others' category
    dat = dat[dat.TECH != 'others'].copy()

    # Remove some generators based on retire year and online year
    dat = dat[(dat.RetireYear >= 2010) & (dat['onlineyear'] < 2010)].copy()

    # Make unique ID column for generators
    id_delimiter = '<dontputthisinaname>'
    dat['id'] = dat.TECH + id_delimiter + dat.r
    
    # Bin hintage data - this leverages the kmeans function in
    # the grouping class to perform the operations in the _kmeans sub-class
    # and returns the 'dat' dataframe with the additional 'bin' column
    # this needs to be done separately since coal techs are regulated at the unit level
    dat_non_coal = dat[~dat.TECH.isin(coal_techs)] # all non-coal plants
    dat_coal = dat[dat.TECH.isin(coal_techs)] # coal plants

    # treat the non-coal options regularly
    tdat_non_coal = grouping(nBin, dat_non_coal, 'HR', minSpread=mindev).df

    # coal plants are grouped at the unit level if GSw_Clean_Air_Act is enabled
    if GSw_Clean_Air_Act == 1:
        tdat_coal = grouping('unit', dat_coal, 'HR', minSpread=mindev).df
    else:
        tdat_coal = grouping(nBin, dat_coal, 'HR', minSpread=mindev).df

    tdat = pd.concat([tdat_non_coal, tdat_coal], ignore_index=True, axis=0)
    
    # calculate the maximum hintage number, to be used in b_inputs.gms, and export it
    max_hintage_number = tdat['bin'].max()
    max_hintage_number_text = f'scalar max_hintage_number "--number-- the maximum number of bins used in this ReEDS run" /{max_hintage_number}/ ;'
    with open(os.path.join(inputs_case,'max_hintage_number.txt'), 'w') as file:
        file.write(f'{max_hintage_number_text}')

   # calculate the capacity-weighted average heat rate for each bin 
    # by taking the product of the sum of the capacity and the centroid of the bin
    tdat['wHR'] = tdat.HR * tdat['Summer.capacity']
    tdat['wVOM'] = tdat.VOM * tdat['Summer.capacity']
    tdat['wFOM'] = tdat.FOM * tdat['Summer.capacity']
    tdat['solveYearOnline'] = tdat.onlineyear * tdat['Summer.capacity']
    tdat['wCCS_Retro_OvernightCost'] = tdat.CCS_Retro_OvernightCost * tdat['Summer.capacity']
    tdat['wCCS_Retro_FOM'] = tdat.CCS_Retro_FOM * tdat['Summer.capacity']
    tdat['wCCS_Retro_VOM'] = tdat.CCS_Retro_VOM * tdat['Summer.capacity']
    tdat['wCCS_Retro_HR'] = tdat.CCS_Retro_HR * tdat['Summer.capacity']
    tdat['wCCS_Retro_CapAdjust'] = tdat.CCS_Retro_CapAdjust * tdat['Summer.capacity']
    tdat['wCCS_Retro_LocFactor'] = tdat.CCS_Retro_LocFactor * tdat['Summer.capacity']

    zout = pd.DataFrame()
    level_cols = ['wHR', 'wVOM', 'wFOM', 'solveYearOnline','wCCS_Retro_OvernightCost',
                  'wCCS_Retro_FOM','wCCS_Retro_VOM','wCCS_Retro_HR',
                  'wCCS_Retro_CapAdjust','wCCS_Retro_LocFactor']

    combine_cols = level_cols + ['Winter.capacity']

# Adjust the HR, VOM, FOM, solveYearOnline, and winter capacity
    for i in list(range(2010, tdat.RetireYear.max() + 1)):
        # Subset on years earlier than i
        ydat = tdat.loc[tdat.RetireYear > i, ['id','bin','Summer.capacity'] + combine_cols]

        # Sum up the parameters by id and bin
        ydat = ydat.groupby(['id','bin']).sum()

        # Levelize parameters
        for j in level_cols:
            ydat[j] /= ydat['Summer.capacity']

        ydat['year'] = i
        # Paste dataframes together
        zout = pd.concat([zout, ydat])

    # Parse id
    zout.reset_index(inplace=True)
    if GSw_WaterMain == '1':
        zout['tech'] = zout.id.str.rsplit(id_delimiter, n=1, expand=True)[0]
        zout['r'] = zout.id.str.rsplit(id_delimiter, n=1, expand=True)[1]
    else:
        zout['tech'] = zout.id.str.split(id_delimiter, n=1, expand=True)[0]
        zout['r'] = zout.id.str.split(id_delimiter, n=1, expand=True)[1]
    zout.drop(columns='id', inplace=True)

    #%%###############################
    #    -- Get DPV Generators --    #
    ##################################

    dpv = pd.read_csv(os.path.join(inputs_case,'distpvcap.csv')).set_index('r')
           
    # Fill in odd years' values for dpv (only add odd year data if that
    # data does not already exist)
    firstyr = int(dpv.columns.min())
    lastyr = int(dpv.columns.max())
    oddyrs = [str(x) for x in np.arange(firstyr,lastyr+1) if x % 2 != 0]
    for yr in oddyrs:
        if yr not in dpv.columns:
            dpv[yr] = (dpv[str(int(yr)-1)] + dpv[str(int(yr)+1)]) / 2
    dpv = pd.melt(dpv.reset_index(),id_vars=['r'])
    dpv.rename(columns=dict(zip(dpv.columns,['r','year','Summer.capacity'])),
               inplace=True)

    # Initialize columns for dpv dataframe
    dpv['tech'] = 'distpv'
    dpv['wHR'] = 0
    dpv['wVOM'] = 0
    dpv['wFOM'] = 0
    dpv['Winter.capacity'] = dpv['Summer.capacity']
    dpv['bin'] = 1
    dpv['solveYearOnline'] = 2010
    dpv['year'] = dpv['year'].astype(int)

    # Concat dpv and the output dataframes
    zout = pd.concat([zout, dpv])

    #%%############################################################################
    #    -- Get forced retirement dataframe and merge onto output dataframe --    #
    ###############################################################################
    forced_retire = pd.read_csv(
        os.path.join(inputs_case, 'forced_retirements.csv'),
        header=0, names=['tech','st','retire_year'])
    
    # Forced retirements are at the state level, so use hierarchy to get the regions
    state2r = (
        pd.read_csv(
            os.path.join(inputs_case, 'hierarchy.csv'),
            usecols=['*r', 'st']
        )
        .rename(columns={'*r': 'r'})
    )
    forced_retire = (
        pd.merge(forced_retire, state2r, on='st')
        .drop(columns='st')
        .drop_duplicates()
    )

    zout = zout.merge(forced_retire, how='left', on=['tech', 'r']).fillna(9000)
    
    # Zero out retired generators' capacity
    zout.loc[zout.solveYearOnline >= zout.retire_year, 'Summer.capacity'] = 0
    zout.loc[zout.solveYearOnline >= zout.retire_year, 'Winter.capacity'] = 0
    
    # Clean up output dataframe
    zout['bin_int'] = zout['bin'] # keep integer bins in dataframe for ease of plotting
    zout['bin'] = 'init-' + zout['bin'].astype(str)
    zout['solveYearOnline'] = zout['solveYearOnline'].round()
    zout['wFOM'] *= 1e3
    zout.rename(columns={'Summer.capacity': 'cap',
                         'Winter.capacity': 'wintercap',
                         'solveYearOnline': 'wOnlineYear',
                         'year': 'yr',
                         'tech': 'TECH'},
                inplace=True)

    zout.cap = zout.cap.round(decimals=1)
    zout.wintercap = zout.wintercap.round(decimals=1)
    zout.wHR = zout.wHR.round(decimals=1)
    zout.wFOM = zout.wFOM.round(decimals=3)
    zout.wVOM = zout.wVOM.round(decimals=3)
    zout.wCCS_Retro_OvernightCost = zout.wCCS_Retro_OvernightCost.round(decimals=3)
    zout.wCCS_Retro_FOM = zout.wCCS_Retro_FOM.round(decimals=3)
    zout.wCCS_Retro_VOM = zout.wCCS_Retro_VOM.round(decimals=3)
    zout.wCCS_Retro_HR = zout.wCCS_Retro_HR.round(decimals=1)
    zout.wCCS_Retro_CapAdjust = zout.wCCS_Retro_CapAdjust.round(decimals=3)
    zout.wCCS_Retro_LocFactor = zout.wCCS_Retro_LocFactor.round(decimals=3)
    
    #%% Save output dataframe in inputs_case folder
    cols = ['TECH', 'bin', 'r', 'yr', 'cap', 'wintercap', 'wHR',
            'wFOM', 'wVOM', 'wOnlineYear',
            'wCCS_Retro_OvernightCost','wCCS_Retro_FOM','wCCS_Retro_VOM', # new addition: revised to include CCS retrofits
            'wCCS_Retro_HR','wCCS_Retro_CapAdjust','wCCS_Retro_LocFactor']

    zout[cols].dropna().to_csv(os.path.join(inputs_case,'hintage_data.csv'), index=False)

    #%%####################################################################################
    #    -- Make plots comparing actual unit heatrates with binned ones, if desired --    #
    #######################################################################################

    make_plots = 0 
    
    # Make plots comparing actual unit heatrates with binned ones, if desired
    if make_plots:
        import matplotlib.pyplot as plt
        # Create facet plots for heatrate, FO&M, VO&M, and online year
        allgens = pd.merge(
            tdat.loc[
                (tdat.RetireYear > 2020) & (tdat['onlineyear'] < 2020),
                ['TECH','r','bin','HR','FOM','VOM','onlineyear','Summer.capacity']],
            zout.loc[zout.yr==2020],
            left_on=['r','TECH','bin'],
            right_on=['r','TECH','bin_int'],
            how='left')
        
        ## Summary scatter plot for all techs
        plt.close()
        plt.scatter(allgens['HR'],allgens['wHR'],c=allgens['Summer.capacity'],alpha=0.15)
        plt.rcParams["figure.figsize"] = (7,10)
        color_bar = plt.colorbar()
        color_bar.set_label('Summer Capacity (MW)')
        #Plot an abline of slope 1 for reference
        x_vals = np.array((0,45000))
        y_vals = 1 * x_vals
        plt.plot(x_vals, y_vals)
        plt.title('Hintage Binning Results for All BAs and All Techs')
        plt.xlabel("Actual Heat Rate (MMBtu / MWh)")
        plt.ylabel("Binned Heat Rate (MMBtu / MWh)")
        plt.savefig(os.path.join(inputs_case, 'hintage_data_2020_heatrate_binning_summary.png'))


        ## Faceted scatter plot showing a fairly random selection of nine BAs for all techs
        # Get color axes range to set static across subplots:
        color_col = 'onlineyear'
        bas_to_plot = ['p1','p2','p3','p50','p51','p52','p110','p120','p130']
        vmin_global = min([ allgens.loc[allgens['r']==ba,color_col].min() for ba in bas_to_plot])
        vgmax_global = max([ allgens.loc[allgens['r']==ba,color_col].max() for ba in bas_to_plot])

        plt.close()
        f = plt.figure()    
        f, axes = plt.subplots(nrows = 3, ncols = 3, figsize=(12,12), sharex=True, sharey = True)

        axes = axes.ravel()
        for i,ba in zip(range(9),bas_to_plot):
            im = axes[i].scatter(allgens.loc[allgens['r']==ba,'HR'],
                                 allgens.loc[allgens['r']==ba,'wHR'],
                                 c=allgens.loc[allgens['r']==ba,color_col],
                                 vmin=vmin_global,
                                 vmax=vgmax_global)
            
            #Plot an abline of slope 1 for reference
            x_vals = np.array((5000,25000))
            y_vals = 1 * x_vals
            axes[i].plot(x_vals, y_vals)
            axes[i].set_title(ba)
        
        # Add common axis labels:
        f.add_subplot(111, frame_on=False)
        plt.tick_params(labelcolor="none", bottom=False, left=False)
        plt.xlabel("Actual Heat Rate (MMBtu / MWh)")
        plt.ylabel("Binned Heat Rate (MMBtu / MWh)",labelpad=20)

        f.subplots_adjust(right=0.8)
        cbar_ax = f.add_axes([0.85,0.1,0.03,0.8]) 
        color_bar = f.colorbar(im, cax=cbar_ax)
        color_bar.set_label(color_col)

        plt.savefig(os.path.join(inputs_case, 'hintage_data_2020_BA_binning_examples_all_techs.png'))


        ## Faceted scatter plot showing the BA with the highest number of units for each tech 
        # (i.e. where our binning assumptions have the most impact)
        color_col = 'onlineyear'
        allgens.groupby(["r", "TECH"]).count().groupby('TECH').max()
        bas_with_max_num_units_by_tech = (
            allgens.groupby(["r", "TECH"]).count()
            .groupby('TECH').idxmax()['bin_x'].tolist()
        )

        # Get color axes range to set static across subplots:
        vmin_global = min(
            [allgens.loc[(allgens['r']==ba) & (allgens['TECH']==tech), color_col].min()
             for ba,tech in bas_with_max_num_units_by_tech])
        vgmax_global = max(
            [allgens.loc[(allgens['r']==ba) & (allgens['TECH']==tech), color_col].max()
             for ba,tech in bas_with_max_num_units_by_tech])

        # Create plot:
        plt.close()
        f = plt.figure()    
        num_cols = math.floor(math.sqrt(len(bas_with_max_num_units_by_tech)))
        add_row = math.ceil(math.sqrt(len(bas_with_max_num_units_by_tech)) % num_cols)

        f, axes = plt.subplots(
            nrows=(num_cols + add_row), ncols=num_cols, figsize=(14,12), sharex=True, sharey=True)

        axes = axes.ravel()
        i=0
        for ba,tech in bas_with_max_num_units_by_tech:
            im = axes[i].scatter(
                allgens.loc[(allgens['r']==ba) & (allgens['TECH']==tech),'HR'],
                allgens.loc[(allgens['r']==ba) & (allgens['TECH']==tech),'wHR'],
                c=allgens.loc[(allgens['r']==ba) & (allgens['TECH']==tech),color_col],
                vmin=vmin_global,
                vmax=vgmax_global)
            
            #Plot an abline of slope 1 for reference
            x_vals = np.array((5000,25000))
            y_vals = 1 * x_vals
            axes[i].plot(x_vals, y_vals)

            num_units = len(allgens.loc[(allgens['r']==ba) & (allgens['TECH']==tech),'HR'])
            axes[i].set_title(f'{tech} in {ba}: {num_units} units')

            i += 1
        
        # Add common axis labels:
        f.add_subplot(111, frame_on=False)
        plt.tick_params(labelcolor="none", bottom=False, left=False)
        plt.xlabel("Actual Heat Rate (MMBtu / MWh)")
        plt.ylabel("Binned Heat Rate (MMBtu / MWh)",labelpad=20)

        f.subplots_adjust(right=0.8)
        cbar_ax = f.add_axes([0.85,0.1,0.03,0.8]) 
        color_bar = f.colorbar(im, cax=cbar_ax)
        color_bar.set_label(color_col)

        plt.savefig(
            os.path.join(
                inputs_case, 'hintage_data_2020_BAs_with_max_num_units_of_each_tech.png'))


        corrcoef = allgens['HR'].corr(allgens['wHR'])
        print(f'Pearson correlation coefficient between actual and binned heat rates is {corrcoef}')


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================
if __name__ == '__main__':

    ### Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('reeds_path', type=str, help='Path to local ReEDS repo')
    parser.add_argument('inputs_case', type=str)

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    #%% Run it
    main(reeds_path=reeds_path, inputs_case=inputs_case)

    reeds.log.toc(tic=tic, year=0, process='input_processing/WriteHintage.py', 
        path=os.path.join(inputs_case,'..'))

    print('Finished WriteHintage.py')
  