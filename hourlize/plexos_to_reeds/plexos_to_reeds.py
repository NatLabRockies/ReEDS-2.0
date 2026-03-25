import pandas as pd
import numpy as np
from pdb import set_trace as pdbst
import datetime

#Enter the path to the hourly csv data by plexos region here. The first column should be 'DATETIME',
#and the following columns should be the name of each plexos region. Then run 'python plexos_to_reeds.py'
#from the command prompt, and the output file should be within outputs/
input_file = "//nrelnas01/ReEDS/Supply_Curve_Data/LOAD/2020_Update/plexos_to_reeds/h5_2007-2014_ungrown_2012_1hr_EST.csv"
output_file = 'load_hourly_ba_EST.csv'

print('Reading hourly input data: ' + input_file)
df = pd.read_csv(input_file,index_col='DATETIME', parse_dates=True)

#uppercase the columns
df.columns = [c.upper() for c in df]

#Fill missing entries with their following entries via backfill:
df = df.fillna(method='bfill')

#limit from 2007 through 2013
df = df[df.index < pd.to_datetime('2014-01-01 00:00:00')]

#Check for remaining null values
print('Checking for Errors.')
df_na = df[df.isnull().any(axis=1)]
if len(df_na) > 0:
    print('***ERROR: Not all NaNs were handled.')
    # print(df_na)
else:
    print('**PASS: no remaining NaN hourly load values.')

#find ramp rate between hours and find entries that have more than 50% change (positive or negative) from previous hour.
df_pct = df.pct_change()
df_pct_prob = df_pct[(abs(df_pct) > 0.5).any(axis=1)].copy()
#using an absoluate MW difference in addition to 50% change
#df_diff = df.diff()
#df_prob = df[((abs(df_pct) > 0.5)&(abs(df_diff) > 50)).any(axis=1)].copy()
problem_times = (abs(df_pct_prob) > 0.5).sum(axis=1).sort_values(ascending=False)
problem_regions = (abs(df_pct_prob) > 0.5).sum(axis=0)
problem_regions = problem_regions[problem_regions > 0].sort_values(ascending=False)
if len(df_pct_prob) > 0:
    print('***ERROR: We have load spikes.')
    # print('problem regions:')
    # print(problem_regions)
    # print('problem times:')
    # print(problem_times)
else:
    print('**PASS: No load spikes.')

#Find lpfs from plexos region to reeds ba and calculate hourly reeds ba load
print('Finding lpfs from plexos region to reeds ba')
df_map = pd.read_csv('inputs/plexos_node_to_reeds_ba.csv')

#Add month and season to hourly data. ERCOT uses month, and WI uses season
df_mo_to_seas = pd.read_csv('inputs/month_to_season.csv')
df['month'] = df.index.month
df = df.reset_index().merge(df_mo_to_seas, on=['month'], how='left', sort=False).set_index('DATETIME')

#ERCOT
print('Calculating ERCOT lpfs.')
#ERCOT has monthly load participation factors that are used to spread ERCOT_ERC load to nodes
df_ercot_lpf = pd.read_csv('inputs/plexos_node_monthly_lpf_ercot.csv')
df_ercot_lpf = pd.melt(df_ercot_lpf, id_vars=['node'], var_name='month', value_name= 'lpf')
df_ercot_lpf['month'] = df_ercot_lpf['month'].astype(int)

#output plexos region load that is not mapped to nodes
df_ercot_lpf_lost_node = 1 - df_ercot_lpf.groupby(['month']).sum()
df_ercot_lpf_lost_node.to_csv('outputs/lost_load_node_ercot.csv')

#map to reeds bas
df_ercot_lpf = pd.merge(left=df_ercot_lpf, right=df_map, on=['node'], how='left', sort=False)

#Track lost load fraction, plexos region load that is not mapped to reeds bas
print('Outputting lost ERCOT load.')
df_ercot_lpf.loc[pd.isna(df_ercot_lpf['reeds_ba']), 'lpf'] = 0
df_ercot_lpf_lost = 1- df_ercot_lpf.groupby(['month']).sum()
df_ercot_lpf_lost.to_csv('outputs/lost_load_ercot.csv')

#Create lpfs for each reeds ba
print('Calculating and outputting ERCOT lpf to reeds_ba')
df_ercot_lpf = df_ercot_lpf[pd.notna(df_ercot_lpf['reeds_ba'])]
df_ercot_lpf = df_ercot_lpf.groupby(['reeds_ba','month'], as_index =False).sum()
ercot_bas = df_ercot_lpf['reeds_ba'].unique().tolist()
df_ercot_lpf = df_ercot_lpf.pivot_table(index=['month'], columns='reeds_ba', values='lpf').reset_index()
df_ercot_lpf.to_csv('outputs/lpf_ercot.csv', index=False)

#Calculate hourly BA load based on lpf from ERCOT
print('Calculating ERCOT contribution to hourly load by reeds_ba')
df_ercot_hourly = df[['ERCOT_ERC','month']].copy()
df_ercot_hourly = df_ercot_hourly.reset_index().merge(df_ercot_lpf, on=['month'], how='left', sort=False).set_index('DATETIME')
for ba in ercot_bas:
    df_ercot_hourly[ba] = df_ercot_hourly[ba] * df_ercot_hourly['ERCOT_ERC']
df_ercot_hourly = df_ercot_hourly[ercot_bas].round().astype(int)

#Eastern Interconnect (EI)
print('Calculating Eastern Interconnect (EI) lpfs.')
#EI assumes that load from each eastern plexos region is spread evenly among the nodes in that region
df_ei_reg_to_node = pd.read_csv('inputs/plexos_node_to_zone_ei.csv')
#uppercase the regions
df_ei_reg_to_node['region'] = df_ei_reg_to_node['region'].str.upper()
df_ei_lpf = df_ei_reg_to_node.groupby(['region'], as_index =False, sort=False).count()
df_ei_lpf['lpf'] = 1 / df_ei_lpf['node']
df_ei_lpf = df_ei_lpf[['region','lpf']]
df_ei_lpf = pd.merge(left=df_ei_reg_to_node, right=df_ei_lpf, on=['region'], how='left', sort=False)

#Check for regions in hourly data that are not in mapping file
unmapped_ei_reg = [i for i in df if i.endswith('_EI') and i not in df_ei_lpf['region'].unique()]
print('EI regions that are not mapped to nodes:')
print(unmapped_ei_reg)
#Fill in missing reg with lpf of 0
for reg in unmapped_ei_reg:
    df_ei_lpf = df_ei_lpf.append({'region':reg, 'node':'None', 'lpf':0}, ignore_index=True)

#output plexos region load that is not mapped to nodes
df_ei_lpf_lost_node = 1 - df_ei_lpf.groupby(['region']).sum()
df_ei_lpf_lost_node.to_csv('outputs/lost_load_node_ei.csv')

#map to reeds ba
df_ei_lpf = pd.merge(left=df_ei_lpf, right=df_map, on=['node'], how='left', sort=False)

#Track lost load fraction, plexos region load that is not mapped to reeds bas
print('Outputting lost EI load.')
df_ei_lpf.loc[pd.isna(df_ei_lpf['reeds_ba']), 'lpf'] = 0
df_ei_lpf_lost = 1 - df_ei_lpf.groupby(['region']).sum()
df_ei_lpf_lost.to_csv('outputs/lost_load_ei.csv')

#Create lpfs for each reeds ba
print('Calculating and outputting EI lpf to reeds_ba')
df_ei_lpf = df_ei_lpf[pd.notna(df_ei_lpf['reeds_ba'])]
df_ei_lpf = df_ei_lpf.groupby(['region','reeds_ba'], as_index=False).sum()
df_ei_lpf.to_csv('outputs/lpf_ei.csv', index=False)

#Calculate hourly BA load in each of ei_bas based on lpf from all associated plexos regions
print('Calculating EI contribution to hourly load by reeds_ba')
ei_bas = df_ei_lpf['reeds_ba'].unique().tolist()
df_ei_hourly = df[[]].copy()
for ba in ei_bas:
    df_ei_hourly[ba] = 0
    df_ba_lpf = df_ei_lpf[df_ei_lpf['reeds_ba'] == ba].copy()
    #For this ba, iterate over all plexos regions that are mapped to it, excluding plexos regions not in hourly data (df).
    ba_plexos_reg = [r for r in df_ba_lpf['region'].unique().tolist() if r in df]
    for plexos_reg in ba_plexos_reg:
        lpf = df_ba_lpf[df_ba_lpf['region'] == plexos_reg]['lpf'].sum() #this should be a single lpf, so 'sum' will just result in that one value.
        df_ei_hourly[ba] = df_ei_hourly[ba] + df[plexos_reg] * lpf
df_ei_hourly = df_ei_hourly[ei_bas].round().astype(int)

#Western Interconnect (WI)
print('Calculating Western Interconnect (WI) lpfs.')
#WI has seasonal load participation factors that are used to spread load from WI plexos regions to nodes
seasons = ['Spring','Summer','Autumn','Winter']
df_wi_lpf = pd.read_csv('inputs/plexos_node_seasonal_lpf_wi.csv')
#uppercase the regions
df_wi_lpf['region'] = df_wi_lpf['region'].str.upper()

#Check for regions in hourly data that are not in mapping file
unmapped_wi_reg = [i for i in df if i.endswith('_WI') and i not in df_wi_lpf['region'].unique()]
print('WI regions that are not mapped to nodes:')
print(unmapped_wi_reg)
#Fill in missing reg with lpf of 0
for reg in unmapped_wi_reg:
    df_wi_lpf = df_wi_lpf.append({'region':reg, 'node':'None','Spring':0,'Summer':0,'Autumn':0,'Winter':0}, ignore_index=True)

df_wi_lpf = pd.melt(df_wi_lpf, id_vars=['region','node'], var_name='season', value_name= 'lpf')

#output plexos region load that is not mapped to nodes
df_wi_lpf_lost_node = 1 - df_wi_lpf.groupby(['region','season']).sum()
df_wi_lpf_lost_node.to_csv('outputs/lost_load_node_wi.csv')

#map to reeds ba
df_wi_lpf = pd.merge(left=df_wi_lpf, right=df_map, on=['node'], how='left', sort=False)

#Track lost load fraction, plexos region load that is not mapped to reeds bas
print('Outputting lost EI load.')
df_wi_lpf.loc[pd.isna(df_wi_lpf['reeds_ba']), 'lpf'] = 0
df_wi_lpf_lost = 1 - df_wi_lpf.groupby(['region','season']).sum()
df_wi_lpf_lost.to_csv('outputs/lost_load_wi.csv')

#Create lpfs for each reeds ba
print('Calculating and outputting WI lpf to reeds_ba')
df_wi_lpf = df_wi_lpf[pd.notna(df_wi_lpf['reeds_ba'])]
df_wi_lpf = df_wi_lpf.groupby(['region','season','reeds_ba'], as_index =False).sum()
df_wi_lpf.to_csv('outputs/lpf_wi.csv', index=False)

#Calculate hourly BA load in each of wi_bas based on lpf from all associated plexos regions
print('Calculating WI contribution to hourly load by reeds_ba')
wi_bas = df_wi_lpf['reeds_ba'].unique().tolist()
df_wi_hourly = df[[]].copy()
for ba in wi_bas:
    df_wi_hourly[ba] = 0
    df_ba_lpf = df_wi_lpf[df_wi_lpf['reeds_ba'] == ba].copy()
    #For this ba, iterate over all plexos regions that are mapped to it, excluding plexos regions not in hourly data (df).
    ba_plexos_reg = [r for r in df_ba_lpf['region'].unique().tolist() if r in df]
    for plexos_reg in ba_plexos_reg:
        for season in seasons:
            lpf = df_ba_lpf[(df_ba_lpf['region'] == plexos_reg)&(df_ba_lpf['season'] == season)]['lpf'].sum() #this should be a single lpf, so 'sum' will just result in that one value.
            seas_cond = df['season'] == season
            df_wi_hourly.loc[seas_cond, ba] = df_wi_hourly.loc[seas_cond, ba] + df.loc[seas_cond, plexos_reg] * lpf
df_wi_hourly = df_wi_hourly[wi_bas].round().astype(int)

#combine interconnect loads and output hourly load by reeds ba
all_bas = list(set(ercot_bas + ei_bas + wi_bas))
df_ba_hourly = df[[]].copy()
for ba in all_bas:
    df_ba_hourly[ba] = 0
    if ba in df_ercot_hourly:
        df_ba_hourly[ba] = df_ba_hourly[ba] + df_ercot_hourly[ba]
    if ba in df_ei_hourly:
        df_ba_hourly[ba] = df_ba_hourly[ba] + df_ei_hourly[ba]
    if ba in df_wi_hourly:
        df_ba_hourly[ba] = df_ba_hourly[ba] + df_wi_hourly[ba]
df_ba_hourly.sort_index(axis=1, inplace=True)
df_ba_hourly.to_csv('outputs/'+output_file)
print('Done! Output file is at outputs/'+output_file)

#Check to make sure that total load is the same between ReEDS BAs and PLEXOS regions minus losses (excluding plexos regions that are not mapped to reeds bas)
print('Validating outputs.')

#flatten hourly plexos data and re-add month and season columns for lost load adjustment
df_flat = df.drop(columns=['month', 'season'])
df_flat = pd.melt(df_flat.reset_index(), id_vars=['DATETIME'], var_name='region', value_name= 'load')
df_flat['month'] = df_flat['DATETIME'].dt.month
df_flat = df_flat.merge(df_mo_to_seas, on=['month'], how='left', sort=False)

#get total TWh from plexos input data:
plexos_twh_total = df_flat['load'].sum()/1e6
print('total PLEXOS TWh:')
print(plexos_twh_total)

#Calculate reduced plexos data and compare to output ba-level data
df_flat = df_flat.merge(df_ei_lpf_lost.reset_index(), on=['region'], how='left', sort=False)
df_flat['lpf'].fillna(0, inplace=True)
df_flat.rename(columns={'lpf':'lpf_ei'}, inplace=True)
df_flat = df_flat.merge(df_wi_lpf_lost.reset_index(), on=['region','season'], how='left', sort=False)
df_flat['lpf'].fillna(0, inplace=True)
df_flat.rename(columns={'lpf':'lpf_wi'}, inplace=True)
df_erc_lost = df_ercot_lpf_lost.reset_index()
df_erc_lost['region'] = 'ERCOT_ERC'
df_erc_lost.rename(columns={'lpf':'lpf_erc'}, inplace=True)
df_flat = df_flat.merge(df_erc_lost, on=['region','month'], how='left', sort=False)
df_flat['lpf_erc'].fillna(0, inplace=True)
df_flat['lpf'] = df_flat['lpf_ei'] + df_flat['lpf_wi'] + df_flat['lpf_erc']
df_flat['load_reduced'] = df_flat['load'] * (1 - df_flat['lpf'])

plexos_twh_reduced = df_flat['load_reduced'].sum()/1e6
print('total PLEXOS TWh reduced (should be same as next):')
print(plexos_twh_reduced)

#get total TWh from df_ba_hourly:
ba_twh_total = df_ba_hourly.to_numpy().sum()/1e6
print('total BA TWh:')
print(ba_twh_total)

#get US total MWh from df_ba_hourly
us_bas = ['p'+str(i+1) for i in range(134)]
ba_us_twh_total = df_ba_hourly[us_bas].to_numpy().sum()/1e6
print('total US BA TWh:')
print(ba_us_twh_total)

#Check for negatives
df_ba_flat = pd.melt(df_ba_hourly.reset_index(), id_vars=['DATETIME'], var_name='reeds_ba', value_name= 'load')
df_ba_negative = df_ba_flat[df_ba_flat['load'] < 0].copy()
df_ba_negative = df_ba_negative.sort_values(by=['load'], ascending=True)
if len(df_ba_negative) > 0:
    print('***ERROR: We have negative load in certain bas')
    df_ba_negative.to_csv('outputs/negative_ba_loads.csv', index=False)
else:
    print('***PASS: No negative loads by BA')

#check for spikes
print('Checking for spikes in load')
df_diff_ba = df_ba_hourly.diff().fillna(0)
df_pct_ba = df_ba_hourly.pct_change().fillna(0)
df_diff_ba_flat = pd.melt(df_diff_ba.reset_index(), id_vars=['DATETIME'], var_name='reeds_ba', value_name= 'diff')
df_pct_ba_flat = pd.melt(df_pct_ba.reset_index(), id_vars=['DATETIME'], var_name='reeds_ba', value_name= 'pct_change')
df_chng_ba = pd.merge(left=df_ba_flat, right=df_diff_ba_flat, how='outer', on=['DATETIME','reeds_ba'], sort=False)
df_chng_ba = pd.merge(left=df_chng_ba, right=df_pct_ba_flat, how='outer', on=['DATETIME','reeds_ba'], sort=False)
df_chng_ba['abs_diff'] = abs(df_chng_ba['diff'])
df_chng_ba['abs_pct_change'] = abs(df_chng_ba['pct_change'])
df_chng_ba = df_chng_ba.sort_values(by=['abs_pct_change'], ascending=False)
df_chng_ba_20 = df_chng_ba[df_chng_ba['abs_pct_change']>.2]
df_chng_us_ba_20 = df_chng_ba_20[df_chng_ba_20['reeds_ba'].isin(us_bas)]
df_chng_us_ba_20.to_csv('outputs/us_ba_load_hourly_diff_check.csv', index=False)

pdbst()