'''This script ingests eer data, reshapes the data & outputs the data to the 
same folder as csvs in the terminal's current directory.  The resulting csv can 
be used in load.py.'''

import pandas as pd
import os
from datetime import datetime
from pandas.tseries.offsets import DateOffset
from pdb import set_trace as bp
import numpy as np
import shutil

startTime = datetime.now()
this_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'

beg_year = 2021
end_year = 2050
weather_years = list(range(2007,2014))
known_years = [2021] + [x for x in range(2025, 2051, 5)]
years = [x for x in range(beg_year, end_year+1)]
eer_scenario = '20230604_reeds_load_baseline'
input_file_dir = r'//nrelnas01/ReEDS/Users/ahamilto/NTPS/Demand_Analysis/6.4.23/6.4.23_load_files'
input_file_list = os.listdir(input_file_dir)
output_dir = this_dir_path + 'outputs/load_hourly_ba_EST_EER_' + eer_scenario + '_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
os.mkdir(output_dir)
shutil.copy2(os.path.realpath(__file__), output_dir)

for weather_year in weather_years:
    print('Processing weather year ' + str(weather_year) + ': ' + str(datetime.now() - startTime))
    eer_files = [x for x in input_file_list
                 if eer_scenario in x and
                 'w' + str(weather_year) in x
                 ]

    data = {}
    print('Reading input files: '+ str(datetime.now() - startTime))
    for f in eer_files:
        f_years = f.replace(eer_scenario + '_','').replace('.csv','')
        data[f_years] = pd.read_csv(input_file_dir + '/' + f)
        #Remove final day of weather leap years (by selecting first 8760 hours of each year)
        data[f_years] = data[f_years].head(8760).copy()

    for known_year in known_years:
        data['e{}_w{}'.format(known_year, weather_year)]['year'] = known_year

    print('Interpolating load: '+ str(datetime.now() - startTime))
    df = pd.DataFrame()
    for year in years:
        #find known years that bound this year
        for i, known_year in enumerate(known_years):
            if(known_year > year):
                section_end_year = known_year
                section_beg_year = known_years[i-1]
                break
        #grab dataframes for linear interpolation
        beg_key = 'e{}_w{}'.format(section_beg_year, weather_year)
        end_key = 'e{}_w{}'.format(section_end_year, weather_year)
        df_load_beg = data[beg_key].set_index('timestamp').drop(columns='year')
        df_load_end = data[end_key].set_index('timestamp').drop(columns='year')
        #linear interpolation: y = y1 + (y2-y1)/(x2-x1)*(x-x1). x is year; y is value
        df_load = df_load_beg + (df_load_end - df_load_beg)/(section_end_year - section_beg_year)*(year-section_beg_year)
        #change from GW to MW
        df_load = df_load * 1000
        df_load = df_load.round(0)
        df_load = df_load.astype(int)
        df_load = df_load.reset_index()
        df_load['year'] = year
        #Create new timestamps
        df_load['DATETIME'] = pd.date_range('1/1/' + str(year) + ' 00:00', periods=8760, freq='1H')
        df = pd.concat([df, df_load])

    #Drop unnecessary datetime columns and set index
    df = df.drop(columns=['year','timestamp'])
    df = df.set_index('DATETIME')

    #Output
    print('Outputting load: '+ str(datetime.now() - startTime))
    df.to_csv(output_dir + '/w' + str(weather_year) + '.csv')
print('All done!: '+ str(datetime.now() - startTime))