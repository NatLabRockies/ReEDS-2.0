import pandas as pd
import os


load_switch = 'EPMEDIUM' #A value of GSw_LoadProfiles in cases.csv.
flex_switch = 'EPMEDIUM_Enhancedflex' #A value of GSw_EFS2_FlexCase in cases.csv.
new_suffix = 'Stretch2046' #Make sure this name aligns with the groups defined below.
beg_year = 2020
end_year = 2050
inputs_dir_path = os.path.join('..', 'inputs')
df_region_map = pd.read_csv(os.path.join(inputs_dir_path, 'hierarchy.csv'))
stretch_groups = [
    {'stretch_end_year': 2046,
     'bas': df_region_map['*r'].tolist(),
    },
]

data = {
    'timeslice_load': {
        'input_file': os.path.join(inputs_dir_path, 'load', load_switch + 'load.csv'),
        'output_file': os.path.join(inputs_dir_path, 'load', load_switch + new_suffix + 'load.csv'),
        'reshape': True,
        'round': True,
        'idx_cols': ['r','timeslice'],
    },
    'timeslice_flex': {
        'input_file': os.path.join(inputs_dir_path, 'load', flex_switch + '_frac.csv'),
        'output_file': os.path.join(inputs_dir_path, 'load', flex_switch + new_suffix + '_frac.csv'),
        'reshape': True,
        'round': False,
        'idx_cols': ['flextype','r','timeslice'],
    },
    'hourly_load': {
        'input_file': os.path.join(inputs_dir_path, 'variability', 'EFS_Load', load_switch + '_load_hourly.csv.gz'),
        'output_file': os.path.join(inputs_dir_path, 'variability', 'EFS_Load', load_switch + new_suffix + '_load_hourly.csv.gz'),
        'reshape': False,
        'round': True,
        'idx_cols': ['year','hour'],
    },
}

for d in data:
    print('Stretching ' + d + '...')
    #Reading
    print('Reading into dataframe')
    data[d]['df_in'] = pd.read_csv(data[d]['input_file'])

    #set_idx_cols
    set_idx_cols = [i for i in data[d]['idx_cols'] if i not in ['year','r']]

    #Reshaping
    if data[d]['reshape']:
        print('Reshaping')
        data[d]['df_in'] = pd.melt(data[d]['df_in'], id_vars=data[d]['idx_cols'], var_name='year', value_name= 'value')
        data[d]['df_in'] = data[d]['df_in'].pivot_table(index=['year']+set_idx_cols, columns='r', values='value').reset_index()
        data[d]['df_in']['year'] = data[d]['df_in']['year'].astype(int)

    data[d]['df_out_all'] = pd.DataFrame()
    for group in stretch_groups:
        #include only bas in this group
        group_cols = [c for c in data[d]['df_in'].columns if c in data[d]['idx_cols'] + ['year'] + group['bas']]
        data[d]['df'] = data[d]['df_in'][group_cols].copy()
        #Initializing output
        data[d]['df_out'] = data[d]['df'][data[d]['df']['year'] <= beg_year].copy()
        #Mapping old years to new years.
        print('Map old years to new years')
        scalar = (end_year - beg_year) / (group['stretch_end_year'] - beg_year)
        years = [x for x in range(beg_year, end_year+1)]
        stretch_years = [beg_year + (year - beg_year) * scalar for year in years]
        year_map = dict(zip(years, stretch_years))
        data[d]['df']['stretch_year'] = data[d]['df']['year'].replace(year_map)

        years_new = years[1:] #years that we need new data for.
        for year in years_new:
            print('Calculating load for ' + str(year))
            #find stretch years that bound this year
            for i, stretch_year in enumerate(stretch_years):
                if(stretch_year > year):
                    section_end_year = stretch_year
                    section_beg_year = stretch_years[i-1]
                    break
            #grab original data from stretch_year equals section_beg_year and section_end_year
            df_load_beg = data[d]['df'][data[d]['df']['stretch_year']==section_beg_year].set_index(set_idx_cols).drop(columns=['year','stretch_year'])
            df_load_end = data[d]['df'][data[d]['df']['stretch_year']==section_end_year].set_index(set_idx_cols).drop(columns=['year','stretch_year'])
            #linear interpolation: y = y1 + (y2-y1)/(x2-x1)*(x-x1)
            df_load = df_load_beg + (df_load_end - df_load_beg)/(section_end_year - section_beg_year)*(year-section_beg_year)
            if data[d]['round']:
                #Rounding to three decimals
                df_load = df_load.round(3)
            #add columns to match df_out
            df_load = df_load.reset_index()
            df_load['year'] = year
            data[d]['df_out'] = pd.concat([data[d]['df_out'],df_load])
        #Combine into df_out_all
        group_idx = [c for c in data[d]['df_out'].columns if c in data[d]['idx_cols'] + ['year']]
        data[d]['df_out'] = data[d]['df_out'].set_index(group_idx)
        data[d]['df_out_all'] = pd.concat([data[d]['df_out_all'],data[d]['df_out']], axis='columns')

    data[d]['df_out_all'] = data[d]['df_out_all'].reset_index()
    #Reshaping if needed
    if data[d]['reshape']:
        print('Reshaping')
        data[d]['df_out_all']['year'] = data[d]['df_out_all']['year'].astype(str)
        data[d]['df_out_all'] = pd.melt(data[d]['df_out_all'], id_vars=['year']+set_idx_cols, var_name='r', value_name= 'value')
        data[d]['df_out_all'] = data[d]['df_out_all'].pivot_table(index=data[d]['idx_cols'], columns='year', values='value').reset_index()

    print('Outputting stretched load.')
    #Round to three decimals
    data[d]['df_out_all'].to_csv(data[d]['output_file'], index=False)

print('All done!')