'''
This script develops BA-level building hvac load profiles for ReEDS (in GWh) based on resstock/comstock EULP outputs (MWh). The resulting files are dropped back into the directories where the raw EULP files are located.
'''
import os
import pandas as pd
import shutil
from pdb import set_trace as b

#Inputs
bldg_type = 'com' # 'com' for comstock or 'res' for resstock
bldg_path = r'/projects/geohc/jm_ReEDS-2.0/postprocessing/reValue/parallel_agg/outputs/outputs_2025-01-20-15-17-29'
bldg_tech = 'upgrade0'

shutil.copy2(os.path.realpath(__file__), bldg_path)
this_dir_path = os.path.dirname(os.path.realpath(__file__))
reeds_path = os.path.dirname(os.path.dirname(os.path.dirname(this_dir_path)))
df_county_map = pd.read_csv(f'{reeds_path}/inputs/county2zone.csv')
county_map = dict(zip(df_county_map['FIPS'], df_county_map['ba']))

eulp_files = [f'{bldg_path}/{f}' for f in os.listdir(bldg_path) if f.startswith(f'{bldg_type}_eulp_hvac_elec_MWh_{bldg_tech}')]

ls_df = []
for f in eulp_files:
    print(f)
    df = pd.read_csv(f)
    df = df.drop(columns=df.columns[0])
    counties = [c.split("', '")[2] for c in df.columns]
    cnty_fips = [int(c[1:3] + c[4:7]) for c in counties]
    bas = [county_map[c] if c in county_map else 'undefined' for c in cnty_fips]
    df.columns = bas
    df_sum = df.groupby(df.columns, axis=1).sum()
    ls_df.append(df_sum)

df_sum = pd.concat(ls_df, axis=1)
df_sum = df_sum.groupby(df_sum.columns, axis=1).sum()
df_sum = df_sum/1000 #Convert to GWh
df_sum.to_csv(f'{bldg_path}/agg_{bldg_type}_eulp_hvac_elec_GWh_{bldg_tech}.csv')
