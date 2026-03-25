###########
#%% IMPORTS
import os, subprocess
from glob import glob

#############
#%% PROCEDURE
### Change to the directory of this file
os.chdir(os.path.dirname(os.path.abspath(__file__)))

### Get model execution file
files = glob('*')
callfile = [c for c in files if os.path.basename(c).startswith('call')][0]

#%% Get the lines to run
runlines = []
with open(callfile, 'r') as f:
    for l in f:
        if (
            l.startswith('gams e_report.gms')
            or l.startswith('python e_report_dump.py')
            or 'bokehpivot' in l
        ):
            runlines.append(l.strip())

#%% Change the .g00 file from the final year to the most recently finished year
### Get the call to e_report, separate arguments into a list
old_e_report = runlines[0].split()
### Get the year from the most recent .g00 file
g00files = glob(os.path.join('g00files','*'))
years = []
for f in g00files:
    try:
        ### Keep it if it ends with _{year}
        years.append(int(os.path.splitext(f)[0].split('_')[-1]))
    except ValueError:
        ### If we can't turn the piece after the '_' into an int, it's not a year
        pass
### Keep the largest year
year = max(years)

### Overwrite the year from g00file in the call to e_report with the most recent year
new_e_report = []
for l in old_e_report:
    if not l.startswith('r=g00files'):
        ### Keep as is
        new_e_report.append(l)
    else:
        ### Overwite the old year (the last 4 characters) with the new year
        new_e_report.append(l[:-4]+str(year))
        
### Replace the old e_report call with the new e_report call
runlines[0] = ' '.join(new_e_report)

#%% Run it
for l in runlines:
    print(l,'\n')
    ### subprocess.call() takes a list of arguments rather than a space-delimited
    ### string, but don't split the "ReEDS 2.0" argument for bokeh
    subprocess.call(
        [c.replace('"ReEDS_2.0"','ReEDS 2.0')
         for c in l.replace('ReEDS 2.0','ReEDS_2.0').split()]
    )
