import os
import shutil
import sys
import pandas as pd
import requests

vizit_commit = 'af6571408f0ce30e1e46082f4abd65ffb3dda2e9'
thisDir = os.path.dirname(os.path.realpath(__file__))
outputDir = sys.argv[1]
bpStyleDir = (os.path.join(thisDir,os.pardir,'bokehpivot','in','reeds2'))

ls_df = []
#Read in styles from bokehpivot
for f in os.listdir(bpStyleDir):
    if f.endswith('_style.csv'):
        df = pd.read_csv(os.path.join(bpStyleDir,f))
        df['column_name'] = f.replace('_style.csv','')
        df = df.rename(columns={'order':'column_value'})
        ls_df.append(df)

df_style = pd.concat(ls_df, ignore_index=True)
df_style = df_style[['column_name','column_value','color']].copy()

#Get specified version of vizit based on commit hash
vizit_filename = 'vizit.html'
vizit_url = f'https://raw.githubusercontent.com/mmowers/vizit/{vizit_commit}/index.html'
vizit_html = requests.get(vizit_url).text
if vizit_html == '404: Not Found':
    vizit_html = (f'<!DOCTYPE html>\nCould not retrieve <a href="{vizit_url}">{vizit_url}</a>.<br><br>'
                  'Save that link as an html file, or go to latest vizit at '
                  '<a href="https://mmowers.github.io/vizit/">https://mmowers.github.io/vizit/</a>')

#Create new vizit folder and move csvs folders from bokehpivot reports into vizit folder, along
#with vizit config and styling files.
if os.path.exists(os.path.join(outputDir, 'vizit')):
    shutil.rmtree(os.path.join(outputDir, 'vizit'))
os.mkdir(os.path.join(outputDir, 'vizit'))
with open(os.path.join(outputDir, 'vizit', vizit_filename), 'w') as f:
    f.write(vizit_html)
shutil.copy2(os.path.join(thisDir, 'vizit-config-reduced-report.json'),
             os.path.join(outputDir,'reeds-report-reduced','csvs'))
df_style.to_csv(os.path.join(outputDir,'reeds-report-reduced','csvs','style.csv'), index=False)
shutil.move(os.path.join(outputDir,'reeds-report-reduced','csvs'), os.path.join(outputDir,'vizit','reduced-report'))
shutil.copy2(os.path.join(thisDir, 'vizit-config-state-report.json'),
             os.path.join(outputDir,'reeds-report-state','csvs'))
df_style.to_csv(os.path.join(outputDir,'reeds-report-state','csvs','style.csv'), index=False)
shutil.move(os.path.join(outputDir,'reeds-report-state','csvs'), os.path.join(outputDir,'vizit','state-report'))
shutil.rmtree(os.path.join(outputDir,'reeds-report-state'))

#If we have ReEDS to reV outputs, produce vizit report of capacity by site
techs = ['wind-ons', 'wind-ofs', 'upv', 'dupv']
df_ls = []
for tech in techs:
    rev_file = os.path.join(outputDir, f'df_sc_out_{tech}_reduced.csv')
    if os.path.isfile(rev_file):
        df = pd.read_csv(rev_file)
        df['tech'] = tech
        df_ls.append(df)
df_rev = pd.concat(df_ls, ignore_index=True)
if not df_rev.empty:
    os.mkdir(os.path.join(outputDir, 'vizit', 'reeds-to-rev'))
    df_rev.to_csv(os.path.join(outputDir,'vizit','reeds-to-rev','df_sc_out.csv'), index=False)
    df_style.to_csv(os.path.join(outputDir,'vizit','reeds-to-rev','style.csv'), index=False)
    shutil.copy2(os.path.join(thisDir, 'vizit-config-reeds-to-rev.json'),
                 os.path.join(outputDir,'vizit','reeds-to-rev'))