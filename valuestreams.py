import sys
import os
import gdxpds
import pandas as pd
import raw_value_streams as rvs
from datetime import datetime
import logging

sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')

this_dir_path = os.path.dirname(os.path.realpath(__file__))
vs_path = this_dir_path + '/inputs_case'
output_dir = this_dir_path + '/outputs'
solution_file = this_dir_path + '/ReEDSmodel_p.gdx'
mps_file = this_dir_path + '/ReEDSmodel.mps'

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)

df_var_map = pd.read_csv(vs_path+'/var_map.csv', dtype=object)
var_list = df_var_map['var_name'].values.tolist()

#common function for outputting to csv
def add_concat_csv(df_in, csv_file):
    df_in['t'] = pd.to_numeric(df_in['t'])
    if not os.path.exists(csv_file):
        df_in.to_csv(csv_file,index=False)
    else:
        df_csv = pd.read_csv(csv_file)
        df_out = pd.concat([df_csv, df_in], ignore_index=True, sort=False)
        df_out.to_csv(csv_file,index=False)

def createValueStreams():
    very_start = datetime.now()
    logger.info('Starting valuestreams.py')
    df = rvs.get_value_streams(solution_file, mps_file, var_list)
    logger.info('Raw value streams completed: ' + str(datetime.now() - very_start))

    df = pd.merge(left=df, right=df_var_map, on='var_name', how='inner')

    #Chosen plants (with nonzero levels in solution)
    start = datetime.now()
    df_lev = df[df['var_level'] != 0].copy()
    #convert to list of lists for speed
    df_lev_ls = df_lev.values.tolist()
    cols = df_lev.columns.values.tolist()
    ci = {c:i for i,c in enumerate(cols)}
    #Use iterrows or itertuples or somthing faster? iterrows is most convenient so if this isn't a bottleneck, use it.
    replace_cols = ['i','v','r','t']
    for i, r in enumerate(df_lev_ls):
        var_set_ls = r[ci['var_set']].split('.')
        for c in replace_cols:
            if str(r[ci[c]]).isdigit():
                df_lev_ls[i][ci[c]] = var_set_ls[int(r[ci[c]])]
    #convert back to pandas dataframe
    df_lev = pd.DataFrame(df_lev_ls)
    df_lev.columns = cols

    #Fill missing values with 'none'
    out_sets = ['i','v','r','t','var_name','con_name']
    df_lev[out_sets] = df_lev[out_sets].fillna(value='none')

    #Reduce df_lev to columns of interest and groupby sum
    out_cols = out_sets + ['value']
    df_lev = df_lev[out_cols]
    df_lev = df_lev.groupby(out_sets, sort=False, as_index =False).sum()

    add_concat_csv(df_lev.copy(), output_dir + '/valuestreams_chosen.csv')
    logger.info('Levels output: ' + str(datetime.now() - start))
    logger.info('Done with years: ' + str(df_lev['t'].unique().tolist()))
    logger.info('Finished valuestreams.py. Total time: ' + str(datetime.now() - very_start))

if __name__ == '__main__':
    createValueStreams()
    os.remove(solution_file)
    os.remove(mps_file)