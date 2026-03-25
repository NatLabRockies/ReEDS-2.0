###############
#%% IMPORTS ###

import pandas as pd
import numpy as np
import os, sys, site, math
from glob import glob
from tqdm import tqdm, trange
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.optimize
from input_processing.ticker import makelog

### Shared paths
reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#######################
#%% ARGUMENT INPUTS ###

import argparse 
parser = argparse.ArgumentParser(description="Minimize LCOE for hybrid wind-PV")
parser.add_argument('case', type=str, help='completed ReEDS run to analyze')
parser.add_argument('-y', '--year', type=int, default=2040, help='cost year')
parser.add_argument('-w', '--workers', default=-1, type=int, 
    help='number of works for brut-force optimization')
parser.add_argument('-s', '--step', type=float, default=0.05, help='GIR step size')
parser.add_argument('-o', '--outpath', type=str, default='', help='output filepath')
parser.add_argument('-j', '--hpc', action='store_true', help='submit slurm job')

args = parser.parse_args()
inp = {
    'case': args.case,
    'workers': args.workers,
    'year': args.year,
    'step': args.step,
}
if args.outpath in ['','default','case']:
    inp['outpath'] = os.path.join(inp['case'],'outputs')
else:
    inp['outpath'] = args.outpath

# #%% Inputs for testing
# inp = {
#     ## ReEDS scenario
#     'case': (
#         '/Volumes/ReEDS/Users/pbrown/ReEDSruns/20211201_spurshare/20220307/'
#         'v20220307_spurH0_Z40_ISONE'),
#     ## Cost year
#     'year': 2040,
#     ## Number of parallel brute-force optimizations
#     'workers': -1,
#     'outpath': os.path.expanduser('~/Desktop'),
# }

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inp['case'],'gamslog.txt'))

#################
#%% HPC/SLURM ###
### If running on the hpc, write a slurm job submission file and submit it, then quit
if args.hpc:
    import subprocess
    ### Make the run file
    jobname = f'hybrid_minLCOE-{inp["case"].split("_")[-1]}-{inp["year"]}'
    slurm = [
        "#!/bin/bash",
        "#SBATCH --account=reedsweto",
        "#SBATCH --time=12:00:00",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks-per-node=1",
        "#SBATCH --mail-user=Patrick.Brown@nrel.gov",
        "#SBATCH --mail-type=FAIL",
        "#SBATCH --mem=64000", # RAM in MB; 90000 for normal or 184000 for big-mem
        "#SBATCH --output=/projects/reedsweto/logs/slurm-%j.out",
        ### add >>> #SBATCH --qos=high <<< above for quicker launch at double AU cost
        ### load your default settings
        ". $HOME/.bashrc",
        ### specifics for this run
        f"#SBATCH --job-name={jobname}",
        f"python hybrid_pvwind_minLCOE.py {inp['case']} -y {inp['year']} -s {inp['step']}",
    ]
    ### Write it
    callfile = os.path.join(inp['case'], 'call_hybrid.sh')
    with open(callfile, 'w+') as OPATH:
        for line in slurm:
            OPATH.writelines(line+'\n')
    ### Run it
    batchcom = f'sbatch {callfile}'
    subprocess.Popen(batchcom.split())
    quit()


#################
#%% FUNCTIONS ###

def lcoe(lifetime, discount, capex, cf, fom, itc=0, degradation=0):
    """
    Inputs
    ------
    lifetime:    economic lifetime [years]
    discount:    discount rate [fraction]
    capex:       year-0 capital expenditures [$/kWac]
    cf:          capacity factor [fraction]
    fom:         fixed O&M costs [$/kWac-yr]
    itc:         investment tax credit [fraction]
    degradation: output degradation per year [fraction]

    Outputs
    -------
    LCOE in $/kWh

    Assumptions
    -----------
    * 8760 hours per year
    """
    ### Index
    years = np.arange(0,lifetime+0.1,1)
    ### Discount rate
    discounts = np.array([1/((1+discount)**year) for year in years])
    ### Degradation
    degrades = np.array([(1-degradation)**year for year in years])
    ### FOM costs
    costs = np.ones(len(years)) * fom
    ### Add capex cost to year 0 and remove FOM
    costs[0] = capex * (1 - itc)
    ### Discount costs
    costs_discounted = costs * discounts
    ### Energy generation, discounted and degraded
    energy_discounted = cf * 8760 * discounts * degrades
    ### Set first-year generation to zero
    energy_discounted[0] = 0
    ### Sum and return
    out = costs_discounted.sum() / energy_discounted.sum()
    return out


def lcoe_simple(annualized_capex, fom, cf):
    """
    """
    out = (annualized_capex + fom) / (cf * 8760)
    return out


def lcoe_single(
        gir, ds,
        costs={'dc':0,'fom_dc':0,'crf':0},
        cost_interconnection=0,
    ):
    """
    """
    gir_opt = max(gir,0)
    cf = (ds * gir_opt).clip(None,1)

    out = lcoe_simple(
        annualized_capex=(
            (gir_opt * costs['dc'] + cost_interconnection)
            * costs['crf']),
        fom=(gir_opt * costs['fom_dc']),
        cf=cf.mean(),
    ) * 1000
    return out


def lcoe_objective(
        gir_pv_wind, dspv, dswind,
        costs_pv={'dc':700,'fom_dc':10,'crf':0.07},
        costs_wind={'dc':1474,'fom_dc':39,'crf':0.07},
        cost_interconnection=0, fom_interconnection=0,
    ):
    """
    * gir = generator-to-interconnection ratio
    """
    ### Parse the inputs
    gir_pv, gir_wind = gir_pv_wind
    gir_pv = max(gir_pv,0)
    gir_wind = max(gir_wind,0)
    cf = (dswind * gir_wind + dspv * gir_pv).clip(None,1)
    ### Spur-line CRF is GIR-weighted average of PV and wind CRF
    crf_interconnection = (
        (gir_pv * costs_pv['crf'] + gir_wind * costs_wind['crf'])
        / (gir_pv + gir_wind)
    )
    ### Get the system LCOE
    out = lcoe_simple(
        annualized_capex=(
            gir_pv * costs_pv['dc'] * costs_pv['crf']
             + gir_wind * costs_wind['dc'] * costs_wind['crf']
             + cost_interconnection * crf_interconnection),
        fom=(
            gir_pv * costs_pv['fom_dc']
            + gir_wind * costs_wind['fom_dc']
            + fom_interconnection),
        cf=cf.mean(),
    ) * 1000

    return out


def cfcorr(dspv, dswind):
    """
    """
    months = list(range(1,13))
    seasons = ['winter','spring','summer','fall']
    season2months = {
        'winter': [12,1,2], 'spring': [3,4,5], 
        'summer': [6,7,8], 'fall': [9,10,11],
    }
    out = {}
    ###### Entire sample period
    ### Hourly
    out['corr_hour'] = dspv.corr(dswind)
    ### Daily
    out['corr_day'] = (
        dspv.groupby(
            [dspv.index.year,dspv.index.month,dspv.index.day]
        ).mean().corr(
            dswind.groupby(
                [dswind.index.year,dswind.index.month,dswind.index.day]
            ).mean()
    ))

    ###### Monthly assessment
    ### Hourly
    for month in months:
        out['corr{}_hour'.format(month)] = (
            dspv.loc[dspv.index.month==month]
            .corr(dswind.loc[dswind.index.month==month])
        )
    ### Daily
    for month in months:
        out['corr{}_day'.format(month)] = (
            dspv.groupby(
                [dspv.index.year,dspv.index.month,dspv.index.day]
            ).mean().loc[(slice(None),month,slice(None))]
            .corr(
                dswind.groupby(
                    [dswind.index.year,dswind.index.month,dswind.index.day]
                ).mean().loc[(slice(None),month,slice(None))]
            )
        )

    ###### Seasonal assessment
    ### Hourly
    for season in seasons:
        out['corr{}_hour'.format(season)] = (
            dspv.loc[dspv.index.month.isin(season2months[season])]
            .corr(dswind.loc[dswind.index.month.isin(season2months[season])])
        )
    ### Daily
    for season in seasons:
        out['corr{}_day'.format(season)] = (
            dspv.groupby(
                [dspv.index.year,dspv.index.month,dspv.index.day]
            ).mean().loc[(slice(None),season2months[season],slice(None))]
            .corr(
                dswind.groupby(
                    [dswind.index.year,dswind.index.month,dswind.index.day]
                ).mean().loc[(slice(None),season2months[season],slice(None))]
            )
        )

    return pd.Series(out)


#################
#%% PROCEDURE ###

#%% Get run settings
switches = pd.read_csv(
    os.path.join(inp['case'],'inputs_case','switches.csv'),
    header=None, index_col=0, squeeze=True,
)
scalars = pd.read_csv(
    os.path.join(inp['case'],'inputs_case','scalars.csv'),
    header=None, index_col=0
)[1]

#%% Load CF profiles from ReEDS/reV
cfpv = pd.read_csv(
    os.path.join(
        reeds_path,'inputs','variability','multi_year',
        f'upv-{switches["GSw_SitingUPV"]}.csv.gz'
    ),
    index_col=0,
)
cfwind = pd.read_csv(
    os.path.join(
        reeds_path,'inputs','variability','multi_year',
        f'wind-ons-{switches["GSw_SitingWindOns"]}.csv.gz'
    ),
    index_col=0,
)
### Make tz-naive time index
timeindex = pd.concat([
    pd.Series(
        index=pd.date_range(
            f'{y}-01-01 00:00', f'{y+1}-01-01 00:00', freq='H', closed='left')[:8760],
        dtype=float)
    for y in range(2007,2014)
]).index
cfpv.index = timeindex
cfwind.index = timeindex

#%% Get site-to-profile lookup
sitemap = pd.read_csv(
    os.path.join(inp['case'],'inputs_case','spurline_sitemap.csv')
).rename(columns={'*i':'i'})
### Get profile names
sitemap['profile'] = sitemap.i.map(lambda x: x.split('_')[1]) + '_' + sitemap.r
sitemap['tech'] = sitemap.i.map(lambda x: x.split('_')[0])
### Get list of valid regions and subset to those regions
val_r = pd.read_csv(
    os.path.join(inp['case'],'inputs_case','val_r.csv')
).columns.values
sitemap = sitemap.loc[sitemap.r.isin(val_r)].copy()
### Make lookup and a single-level column version to write out
profilemap = sitemap.pivot(columns='tech',index='x',values=['profile','i','r']).dropna()
profilemap_out = profilemap.copy()
profilemap_out.columns = ['_'.join(x) for x in profilemap_out.columns]

#%% Get site-specific spur-line costs
spurline_cost = pd.read_csv(
    os.path.join(inp['case'],'inputs_case','spurline_cost.csv'),
    names=['x','trans_cap_cost_per_kw'], header=0, index_col='x', squeeze=True,
## Convert to $/kW
) / 1000

#%% Get costs
## Current format
plantcharout = pd.read_csv(
    os.path.join(inp['case'],'inputs_case','plantcharout.txt'),
    sep=' ', names=['indices','val'],
)
plantcharout.val = plantcharout.val.str.strip(',').astype(float)
plantcharout['i'] = plantcharout.indices.map(lambda x: x.strip('()').split('.')[0].lower())
plantcharout['t'] = plantcharout.indices.map(lambda x: x.strip('()').split('.')[1]).astype(int)
plantcharout['plantcat'] = plantcharout.indices.map(lambda x: x.strip('()').split('.')[2].lower())
## Make lookups
pvcapex = plantcharout.loc[
    plantcharout.i.str.startswith('upv') & (plantcharout.plantcat=='capcost')
].set_index(['i','t']).val / 1000
pvfom = plantcharout.loc[
    plantcharout.i.str.startswith('upv') & (plantcharout.plantcat=='fom')
].set_index(['i','t']).val / 1000
windcapex = plantcharout.loc[
    plantcharout.i.str.startswith('wind-ons') & (plantcharout.plantcat=='capcost')
].set_index(['i','t']).val / 1000
windfom = plantcharout.loc[
    plantcharout.i.str.startswith('wind-ons') & (plantcharout.plantcat=='fom')
].set_index(['i','t']).val / 1000

#%% Get financial assumptions
crf = pd.read_csv(
    os.path.join(inp['case'],'inputs_case','crf.csv'),
    header=None, names=['t','crf'], index_col='t', squeeze=True,
)
cap_cost_mult = pd.read_csv(
    os.path.join(inp['case'],'inputs_case','cap_cost_mult.csv'),
    header=None, names=['i','r','t','ccmult'],
)
ccmult = {
    tech: (
        cap_cost_mult
        .loc[cap_cost_mult.i.str.startswith(tech),['r','t','ccmult']]
        .drop_duplicates()
        .pivot(index='t',columns='r',values='ccmult')
    )
    for tech in ['upv','wind-ons']
}

#%% Turn off divide-by-zero warnings
np.seterr(divide='ignore')

### Make the savename
savename = f'hybrid_minLCOE-{inp["year"]}'
print(os.path.join(inp['outpath'], savename))

### Create the inputs dataframe
dfin = pd.Series(inp).T

#%% Loop over shared sites
dictout = {}
for x in tqdm(profilemap.index):
    # x = profilemap.index[0]
    ### Get PV and wind costs
    inp['costs_pv'] = {
        'dc': pvcapex.loc[profilemap.loc[x,('i','upv')], inp['year']],
        'fom_dc': pvfom.loc[profilemap.loc[x,('i','upv')], inp['year']],
        'crf': crf[inp['year']] * ccmult['upv'].loc[inp['year'],profilemap.loc[x,('r','upv')]]
    }
    inp['costs_wind'] = {
        'dc': windcapex.loc[profilemap.loc[x,('i','wind-ons')], inp['year']],
        'fom_dc': windfom.loc[profilemap.loc[x,('i','wind-ons')], inp['year']],
        'crf': crf[inp['year']] * ccmult['wind-ons'].loc[inp['year'],profilemap.loc[x,('r','wind-ons')]]
    }

    ### Set up additional function params
    dswind = cfwind[profilemap.loc[x,('profile','wind-ons')]]
    dspv = cfpv[profilemap.loc[x,('profile','upv')]]

    params = (
        dspv, dswind,
        inp['costs_pv'],
        inp['costs_wind'],
        spurline_cost[x],
        spurline_cost[x] * scalars['trans_fom_frac'],
    )

    ### Do the optimization
    results = scipy.optimize.brute(
        lcoe_objective,
        ranges=(slice(0,2.001,inp['step']), slice(0,2.001,inp['step'])),
        args=params,
        full_output=True,
        disp=False,
        workers=inp['workers'],
    )

    ### Save it
    dictout[x] = {
        'gir_pv': max(results[0][0],0),
        'gir_wind': max(results[0][1],0),
        'lcoe_opt': results[1],
    }
    corrout = cfcorr(dspv, dswind)
    for k,v in corrout.iteritems():
        dictout[x][k] = v
    dictout[x]['cfopt'] = (
        dswind * dictout[x]['gir_wind'] + dspv * dictout[x]['gir_pv']
    ).clip(None,1).mean()

    ###### Individual optimizations
    ### PV
    pvparams = (
        dspv, 
        inp['costs_pv'],
        spurline_cost[x],
    )
    pvresults = scipy.optimize.brute(
        lcoe_single,
        ranges=(slice(0,2.001,inp['step']),),
        args=pvparams,
        full_output=True,
        disp=False,
        workers=inp['workers'],
    )

    ### Wind
    windparams = (
        dswind, 
        inp['costs_wind'],
        spurline_cost[x],
    )
    windresults = scipy.optimize.brute(
        lcoe_single,
        ranges=(slice(0,2.001,inp['step']),),
        args=windparams,
        full_output=True,
        disp=False,
        workers=inp['workers'],
    )
    ### Save it
    dictout[x]['gir_pvonly'] = pvresults[0][0]
    dictout[x]['lcoe_pvonly'] = pvresults[1]
    dictout[x]['gir_windonly'] = windresults[0][0]
    dictout[x]['lcoe_windonly'] = windresults[1]
    dictout[x]['cf_pvonly'] = (dspv * dictout[x]['gir_pvonly']).clip(None,1).mean()
    dictout[x]['cf_windonly'] = (dswind * dictout[x]['gir_windonly']).clip(None,1).mean()

#%% Create the output dataframe
dfout = (
    pd.DataFrame(dictout).T
    .merge(profilemap_out, left_index=True, right_index=True)
    .merge(spurline_cost, left_index=True, right_index=True)
) 
dfout.index.name = 'x'

### Save it
dfout.round(4).to_csv(os.path.join(inp['outpath'],savename+'.csv'), index=True)
dfin.to_csv(os.path.join(inp['outpath'],'INPUTS-'+savename+'.csv'), header=False)
