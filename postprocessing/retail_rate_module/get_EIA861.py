"""
pbrown 20210129 09:55
Usage notes
* EIA periodically updates past data. To make sure you're using the most recent data,
delete the EIA861 folder and run the whole script below.
* To add additional data years, add entries to the `urls`, `salesfiles`, and `flags`
dictionaries (the entries will hopefully be similar to the entries for 2019).
"""

###############
#%% IMPORTS ###

import numpy as np
import pandas as pd
import sys, os, math
import requests, zipfile, urllib.request

from tqdm import tqdm, trange

##############
#%% INPUTS ###

datadir = os.path.join('inputs','EIA861','')
write_outputs = True

#################
#%% PROCEDURE ###

###########
#%% Download EIA Form 861 data from https://www.eia.gov/electricity/data/eia861/

###### Set the urls (current as of 20210129)
### Original
# urls = {
#     2019: 'https://www.eia.gov/electricity/data/eia861/zip/f8612019.zip',
#     2018: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612018.zip',
#     2017: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612017.zip',
#     2016: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612016.zip',
#     2015: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612015.zip',
#     2014: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612014.zip',
#     2013: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612013.zip',
#     2012: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612012.zip',
#     2011: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86111.zip',
#     2010: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86110.zip',
#     2009: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86109.zip',
#     2008: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86108.zip',
#     2007: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86107.zip',
#     2006: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86106.zip',
#     2005: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86105.zip',
#     2004: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86104.zip',
#     2003: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86103.zip',
#     2002: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86102.zip',
#     2001: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86101.zip',
#     2000: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f86100.zip',
# }
### Reformatted
urls = {
    2020: 'https://www.eia.gov/electricity/data/eia861/zip/f8612020er.zip', ### Early-release
    2019: 'https://www.eia.gov/electricity/data/eia861/zip/f8612019.zip',
    2018: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612018.zip',
    2017: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612017.zip',
    2016: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612016.zip',
    2015: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612015.zip',
    2014: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612014.zip',
    2013: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612013.zip',
    2012: 'https://www.eia.gov/electricity/data/eia861/archive/zip/f8612012.zip',
    2011: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2011.zip',
    2010: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2010.zip',
    2009: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2009.zip',
    2008: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2008.zip',
    2007: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2007.zip',
    2006: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2006.zip',
    2005: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2005.zip',
    2004: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2004.zip',
    2003: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2003.zip',
    2002: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2002.zip',
    2001: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2001.zip',
    2000: 'https://www.eia.gov/electricity/data/eia861/archive/zip/861_2000.zip',
}

### Create the output folder and download the zips
os.makedirs(os.path.join(datadir,'zips'), exist_ok=True)

for year in tqdm(urls):
    ### Download it
    url = urls[year]
    filename = os.path.basename(url)
    if not os.path.exists(os.path.join(datadir, 'zips', filename)):
        urllib.request.urlretrieve(url, os.path.join(datadir, 'zips', filename))
    ### Unzip it
    if not os.path.isdir(os.path.join(datadir, str(year))):
        zip_ref = zipfile.ZipFile(os.path.join(datadir, 'zips', filename), 'r')
        # zip_ref.extractall(os.path.join(datadir, os.path.splitext(filename)[0]))
        zip_ref.extractall(os.path.join(datadir, str(year)))
        zip_ref.close()

#%% Get the files we need
### Original
# salesfiles = {
#     2019: os.path.join(datadir, '2019', 'Sales_Ult_Cust_2019.xlsx'),
#     2018: os.path.join(datadir, '2018', 'Sales_Ult_Cust_2018.xlsx'),
#     2017: os.path.join(datadir, '2017', 'Sales_Ult_Cust_2017.xlsx'),
#     2016: os.path.join(datadir, '2016', 'Sales_Ult_Cust_2016.xlsx'),
#     2015: os.path.join(datadir, '2015', 'Sales_Ult_Cust_2015.xlsx'),
#     2014: os.path.join(datadir, '2014', 'Sales_Ult_Cust_2014.xls'),
#     2013: os.path.join(datadir, '2013', 'Sales_Ult_Cust_2013.xls'),
#     2012: os.path.join(datadir, '2012', 'retail_sales_2012.xls'),
#     2011: os.path.join(datadir, '2011', 'file2_2011.xls'),
#     2010: os.path.join(datadir, '2010', 'file2_2010.xls'),
#     2009: os.path.join(datadir, '2009', '2009', 'file2_2009.xls'),
#     2008: os.path.join(datadir, '2008', '2008', 'file2_2008.xls'),
#     2007: os.path.join(datadir, '2007', '2007', 'file2_2007.xls'),
#     2006: os.path.join(datadir, '2006', 'file2.xls'),
#     2005: os.path.join(datadir, '2005', '2005', 'file2.xls'),
#     2004: os.path.join(datadir, '2004', '2004', 'file2.xls'),
#     2003: os.path.join(datadir, '2003', '2003', 'file2.xls'),
#     2002: os.path.join(datadir, '2002', '2002', 'file2.xls'),
#     2001: os.path.join(datadir, '2001', '2001', 'file2.xls'),
#     2000: os.path.join(datadir, '2000', 'FILE2.xls'),
# }
### Reformatted
salesfiles = {
    2020: os.path.join(datadir, '2020', 'Sales_Ult_Cust_2020_Data_Early_Release.xlsx'), ### ER
    2019: os.path.join(datadir, '2019', 'Sales_Ult_Cust_2019.xlsx'),
    2018: os.path.join(datadir, '2018', 'Sales_Ult_Cust_2018.xlsx'),
    2017: os.path.join(datadir, '2017', 'Sales_Ult_Cust_2017.xlsx'),
    2016: os.path.join(datadir, '2016', 'Sales_Ult_Cust_2016.xlsx'),
    2015: os.path.join(datadir, '2015', 'Sales_Ult_Cust_2015.xlsx'),
    2014: os.path.join(datadir, '2014', 'Sales_Ult_Cust_2014.xls'),
    2013: os.path.join(datadir, '2013', 'Sales_Ult_Cust_2013.xls'),
    2012: os.path.join(datadir, '2012', 'Sales_Ult_Cust_2012.xlsx'),
    2011: os.path.join(datadir, '2011', '2011', 'Sales_Ult_Cust_2011.xlsx'),
    2010: os.path.join(datadir, '2010', '2010', 'Sales_Ult_Cust_2010.xlsx'),
    2009: os.path.join(datadir, '2009', '2009', 'Sales_Ult_Cust_2009.xlsx'),
    2008: os.path.join(datadir, '2008', '2008', 'Sales_Ult_Cust_2008.xlsx'),
    2007: os.path.join(datadir, '2007', '2007', 'Sales_Ult_Cust_2007.xlsx'),
    2006: os.path.join(datadir, '2006', '2006', 'Sales_Ult_Cust_2006.xlsx'),
    2005: os.path.join(datadir, '2005', '2005', 'Sales_Ult_Cust_2005.xlsx'),
    2004: os.path.join(datadir, '2004', '2004', 'Sales_Ult_Cust_2004.xlsx'),
    2003: os.path.join(datadir, '2003', '2003', 'Sales_Ult_Cust_2003.xlsx'),
    2002: os.path.join(datadir, '2002', '2002', 'Sales_Ult_Cust_2002.xlsx'),
    2001: os.path.join(datadir, '2001', '2001', 'Sales_Ult_Cust_2001.xlsx'),
    2000: os.path.join(datadir, '2000', '2000', 'Sales_Ult_Cust_2000.xlsx'),
}

datacols = [
    'rev_res','sales_res','cust_res',
    'rev_com','sales_com','cust_com',
    'rev_ind','sales_ind','cust_ind',
    'rev_tran','sales_tran','cust_tran',
    'rev','sales','cust',
]
prefixcols_2000 = ['year','utility_id','utility_name',
                   'state','part',]

prefixcols_2001 = ['year','utility_id','utility_name',
                   'part','service_type','data_type','state','ownership']

prefixcols_2013 = ['year','utility_id','utility_name',
                   'part','service_type','data_type','state','ownership','ba_code',]

prefixcols_2019 = ['year','utility_id','utility_name',
                   'part','service_type','data_type','state','ownership','ba_code','shortform']

### Reformatted
years = sorted(salesfiles.keys())
sheet_name = 'States'
skiprows = {year:[0,1,2] for year in years}
skiprows[2020] = [0,1,2,3] ### ER
flags = {
    ### year: (skipfooter, names, engine)
    2020: (1, prefixcols_2013+datacols, 'openpyxl'), ### ER
    2019: (1, prefixcols_2019+datacols, 'openpyxl'),
    2018: (1, prefixcols_2013+datacols, 'openpyxl'),
    2017: (1, prefixcols_2013+datacols, 'openpyxl'),
    2016: (1, prefixcols_2013+datacols, 'openpyxl'),
    2015: (1, prefixcols_2013+datacols, 'openpyxl'),
    2014: (1, prefixcols_2013+datacols, 'xlrd'),
    2013: (1, prefixcols_2013+datacols, 'xlrd'),
    2012: (0, prefixcols_2001+datacols, 'openpyxl'),
    2011: (1, prefixcols_2001+datacols, 'openpyxl'),
    2010: (1, prefixcols_2001+datacols, 'openpyxl'),
    2009: (1, prefixcols_2001+datacols, 'openpyxl'),
    2008: (1, prefixcols_2001+datacols, 'openpyxl'),
    2007: (1, prefixcols_2001+datacols, 'openpyxl'),
    2006: (1, prefixcols_2001+datacols, 'openpyxl'),
    2005: (1, prefixcols_2001+datacols, 'openpyxl'),
    2004: (1, prefixcols_2001+datacols, 'openpyxl'),
    2003: (1, prefixcols_2001+datacols, 'openpyxl'),
    2002: (0, prefixcols_2001+datacols, 'openpyxl'),
    2001: (0, prefixcols_2001+datacols, 'openpyxl'),
    2000: (0, prefixcols_2000+datacols, 'openpyxl'),
}

#%%### Load the downloaded and unzipped data
dictin = {}
for year in tqdm(years):
    dictin[year] = pd.read_excel(
        salesfiles[year], 
        sheet_name=sheet_name, skiprows=skiprows[year], skipfooter=flags[year][0],
        na_values='.', header=None, names=flags[year][1], engine=flags[year][2], 
    ).fillna(0.)
dfin = pd.concat(dictin, axis=0, ignore_index=True, sort=False)

## #%%### Save the full form data
## if write_outputs:
##     dfin.to_csv('eia_861.csv', index=False)

#%%### Create and save the nationally-aggregated data
'''
From Sales_Ult_Cust data file:
To calculate a state or the US total, sum Parts (A,B,C & D) for Revenue, but 
only Parts (A,B & D) for Sales and Customers. To avoid double counting of 
customers, the aggregated customer counts for the states and US do not include
the customer count for respondents with ownership code 'Behind the Meter'.
This group consists of Third Party Owners of rooftop solar systems.
'''
#%% Drop Alaska and Hawaii, aggregate by year
df_nat = (
    dfin.loc[(~dfin.state.isin(['AK','HI'])) & dfin.part.isin(['A','B','D'])]
    .drop(['utility_id', 'rev_res', 'rev_com', 'rev_ind', 'rev_tran', 'rev'], axis=1)
).groupby('year', as_index=False).sum()
### Calculate fractional change in customers from start year
df_nat['cust_norm'] = df_nat['cust'] / df_nat.loc[0,'cust']

### Aggregate revenue by year
df_nat_rev = (
    dfin.loc[
        (~dfin.state.isin(['AK','HI'])) & dfin.part.isin(['A','B','C','D']),
        ['year', 'rev_res', 'rev_com', 'rev_ind', 'rev_tran', 'rev']
    ]
).groupby('year', as_index=False).sum()

### Merge together, drop all the transportation data
df_nat = df_nat.merge(df_nat_rev, on='year').drop(['sales_tran','cust_tran','rev_tran'], axis=1)
df_nat['avg_retail_rate'] = df_nat['rev'] / df_nat['sales']

#%% Save it
if write_outputs:
    df_nat.to_csv('df_f861_contiguous.csv', index=False)


#%%### Create and save the state-aggregated data
#%% Repeat the above procedure but differentiate by state
df_state = (
    dfin.loc[(~dfin.state.isin(['AK','HI'])) & dfin.part.isin(['A','B','D'])]
    .drop(['utility_id', 'rev_res', 'rev_com', 'rev_ind', 'rev_tran', 'rev'], axis=1)
).groupby(['year','state'], as_index=False).sum()
### Calculate fractional change in customers from start year
df_state['cust_norm'] = df_state['cust'] / df_state.loc[0,'cust']

### Aggregate revenue by year
df_state_rev = (
    dfin.loc[
        (~dfin.state.isin(['AK','HI'])) & dfin.part.isin(['A','B','C','D']),
        ['year', 'state', 'rev_res', 'rev_com', 'rev_ind', 'rev_tran', 'rev']
    ]
).groupby(['year','state'], as_index=False).sum()

### Merge together, drop all the transportation data
df_state = (
    df_state.merge(df_state_rev, on=['year','state'])
    .drop(['sales_tran','cust_tran','rev_tran'], axis=1))
df_state['avg_retail_rate'] = df_state['rev'] / df_state['sales']

#%% Save it
if write_outputs:
    df_state.to_csv('df_f861_state.csv', index=False)
