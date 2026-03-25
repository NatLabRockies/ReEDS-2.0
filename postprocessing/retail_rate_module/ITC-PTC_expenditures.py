"""
Author: pbrown 20201230
* Purpose: Calculate yearly PTC and ITC expenditures
* Usage notes
    * To use this script, direct `reeds_path` and `runpath` under "USER INPUTS" to the
    desired ReEDS-2.0 and {batch}_{case} run directories
    * Outputs are saved to ReEDS-2.0/runs/{batch}_{case}/outputs/
    * To use for outputs generated before PR #527 (2cec69214baddf817b276a89e3f4072ab76cf2c9),
    add the following lines to the start of e_report.gms and re-run (otherwise geothermal
    won't be included)
    e_report.gms and e_report_dump.py:
    cost_cap_fin_mult_noITC(i,r,t)$geo(i) = cost_cap_fin_mult_noITC("geothermal",r,t)
    cost_cap_fin_mult_no_credits(i,r,t)$geo(i) = cost_cap_fin_mult_no_credits("geothermal",r,t)
* Caveats
    * We don't include PTC expenditures for plants built before 2010, 
    so PTC expenditures for 2010–2019 will be too low
"""

###############
#%% IMPORTS ###
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import os, sys, math
pd.options.display.max_columns = 20
pd.options.display.max_rows = 10

###################
#%% USER INPUTS ###

### Direct these paths to the desired ReEDS-2.0 and {batch}_{case} run directories
reeds_path = os.path.expanduser(os.path.join('~','Projects','Retail','ReEDS-2.0',''))
runpath = os.path.join(reeds_path,'runs','v20201203_retail_Mid_ITCPTC','')
### Inflation adjustments
input_dollar_year = 2004
output_dollar_year = 2019
### Indicate whether to show and save output plots
show_plots = True
save_plots = True
### Indicate whether to print some samples of dataframes to the terminal
verbose = True


#################
#%% FUNCTIONS ###

###### Inflation
def get_inflatable(inflationpath=None):
    """
    Get an [inyear,outyear] lookup table for inflation
    """
    inflation = pd.read_csv(inflationpath, index_col='t')
    ### Make the single-pair function
    def inflatifier(inyear, outyear=2019, inflation=inflation):
        if inyear < outyear:
            return inflation.loc[inyear+1:outyear,'inflation_rate'].cumprod()[outyear]
        elif inyear > outyear:
            return 1 / inflation.loc[outyear+1:inyear,'inflation_rate'].cumprod()[inyear]
        else:
            return 1
    ### Make the output table
    inflatable = {}
    for inyear in range(1960,2051):
        for outyear in range(1960,2051):
            inflatable[inyear,outyear] = inflatifier(inyear,outyear)
    inflatable = pd.Series(inflatable)
    return inflatable

inflatable = get_inflatable(os.path.join(runpath,'inputs_case','inflation.csv'))

#################
#%% PROCEDURE ###

#%%### PTC ######

#%% Get the yearly PTC values (not NPV)
ptc_values = pd.read_csv(
    os.path.join(runpath,'inputs_case','ptc_values.csv'),
    dtype={'ptc_dur':'int'}
)
### Get the techs for which the PTC applies
i_ptc = sorted(ptc_values.i.unique())
### Take a look
if verbose:
    print('\nptc_values')
    print(ptc_values.sample(5))
    print(ptc_values.sort_values('t'))

#%%### Get the PTC-eligible capcity by year
### Get capacity additions of PTC-qualified techs
cap_new = (
    pd.read_csv(os.path.join(runpath,'outputs','cap_new_icrt.csv'))
    .rename(columns={'Dim1':'i','Dim2':'v','Dim3':'r','Dim4':'t','Val':'cap'})
)
cap_add = cap_new.loc[cap_new.i.isin(i_ptc)]

### Get total capacity of PTC-qualified techs
cap_in = (
    pd.read_csv(os.path.join(runpath,'outputs','cap_icrt.csv'))
    .rename(columns={'Dim1':'i','Dim2':'v','Dim3':'r','Dim4':'t','Val':'cap'})
)
cap = cap_in.loc[cap_in.i.isin(i_ptc)]

### Get the capacity that qualifies for the PTC
cap_new_ptc_eligible = (
    cap_new.merge(ptc_values, on=['i','v','r','t']).rename(columns={'t':'t_online'}))

### Get the PTC-eligible capacity in each year
### Assume no retirements
cap_ptc_eligible = []
for i in cap_new_ptc_eligible.index:
    ### Make the dataframe of PTC-eligible years, add it to the list
    df = pd.DataFrame(
        ### Duplicate the (i,v,r,t) entry for each year it's eligible
        {y: cap_new_ptc_eligible.loc[i] 
         for y in range(
             cap_new_ptc_eligible.loc[i,'t_online'],
             cap_new_ptc_eligible.loc[i,'t_online']+cap_new_ptc_eligible.loc[i,'ptc_dur']
          )
         }
    ).T.reset_index().rename(columns={'index':'t'})
    cap_ptc_eligible.append(df)
### Make the big dataframe with PTC-eligible capacity by year
cap_ptc_eligible = pd.concat(cap_ptc_eligible, axis=0)


#%% Aggregate the eligible capacity over construction years
cap_ptc_eligible_agg = (
    cap_ptc_eligible
    .groupby(['i','v','r','t','ptc_value'])['cap']
    .sum().reset_index())

#%% Take a look
if verbose:
    print('\ncap_ptc_eligible example')
    print(cap_ptc_eligible.loc[
        (cap_ptc_eligible.i=='biopower') & (cap_ptc_eligible.r=='p10')
    ])
    print(cap_ptc_eligible_agg.loc[
        (cap_ptc_eligible_agg.i=='biopower') & (cap_ptc_eligible_agg.r=='p10')
    ])

#%%### Get the fraction of (i,v,r,t) capacity that is PTC-eligible in each year
cap = (
    ### Only keep PTC-qualified techs
    cap_in.loc[cap_in.i.isin(i_ptc)]
    ### Aggregate over regions
    .groupby(['i','v','t'], as_index=False)['cap'].sum()
)
### Merge it with PTC-eligible capacity
cap = cap.merge(
    ### Aggregate over regions
    cap_ptc_eligible_agg.groupby(['i','v','t','ptc_value'],as_index=False)['cap'].sum(),
    on=['i','v','t'], suffixes=('_total','_eligible'),
    how='left'
).fillna(0)
### Get the fraction of eligible capacity
cap['frac_eligible'] = cap['cap_eligible'] / cap['cap_total']


#%%### Get the generation that is PTC-eligible
gen_in = (
    pd.read_csv(os.path.join(runpath,'outputs','gen_icrt.csv'))
    .rename(columns={'Dim1':'i','Dim2':'v','Dim3':'r','Dim4':'t','Val':'gen'})
)
### Aggregate over regions
gen = gen_in.groupby(['i','v','t'],as_index=False)['gen'].sum().merge(
    cap[['i','v','t','frac_eligible','ptc_value']],
    how='inner'
)
gen['ptc_expenditure'] = gen.gen * gen.frac_eligible * gen.ptc_value


#%% Downselect to entries with nonzero PTC expenditures and convert to output dollar year
ptc_out = gen.loc[gen.ptc_expenditure > 0].reset_index(drop=True).copy()
ptc_out['ptc_value'] = ptc_out.ptc_value * inflatable[input_dollar_year,output_dollar_year]
ptc_out['ptc_expenditure'] = (
    ptc_out.ptc_expenditure * inflatable[input_dollar_year,output_dollar_year])


#%%### ITC ######

#%% Get the ITC fractions (already corrected for construction time)
itc_fractions = pd.read_csv(
    os.path.join(runpath,'inputs_case','itc_fractions.csv'),
    dtype={'t':'int'}
).drop('country',axis=1)
### Take a look
if verbose:
    print('\nitc_fractions example before backfill')
    print(itc_fractions.loc[itc_fractions.i=='upv_1'].head())

### Extend backwards to 2010
### (calc_financial_inputs.py only includes entries that begin construction in 2010,
### so it doesn't have entries for techs that come online in 2010 and began construction
### before 2010)
### According to https://www.seia.org/initiatives/solar-investment-tax-credit-itc,
### the ITC was constant between 2008–2014.
itc_extend = itc_fractions.set_index(['i','t']).unstack('t').copy()['itc_frac']
earliest_year = min(list(itc_extend.columns))
for year in range(2010,earliest_year):
    itc_extend[year] = itc_extend[earliest_year]
### Overwrite with extended version
itc_fractions = itc_extend.sort_index(axis=1).stack().rename('itc_frac').dropna().reset_index()
### Take another look
if verbose:
    print('\nitc_fractions example after backfill')
    print(itc_fractions.loc[itc_fractions.i=='upv_1'].head())


#%% Get ITC-eligible capex spending
capex_in = (
    pd.read_csv(os.path.join(runpath,'outputs','capex_ivrt.csv'))
    .rename(columns={'Dim1':'i','Dim2':'v','Dim3':'r','Dim4':'t','Val':'capex'})
)
capex_itc = (
    ### Only keep ITC-qualified techs
    capex_in.loc[capex_in.i.isin(itc_fractions.i.unique())]
    ### Aggregate over regions and vintages
    .groupby(['i','t'], as_index=False)['capex'].sum()
)


#%% Merge on (i,t) and get the fraction of capex for which ITC applies
itc_cost = capex_itc.merge(
    itc_fractions, on=['i','t'], how='inner')
itc_cost['itc_expenditure'] = itc_cost.capex * itc_cost.itc_frac
### Treasury pays the cost in the next year
itc_cost['t_treasury'] = itc_cost.t + 1


#%% Convert to output dollar year
itc_out = itc_cost.copy()
itc_out['capex'] = itc_cost.capex * inflatable[input_dollar_year,output_dollar_year]
itc_out['itc_expenditure'] = (
    itc_cost.itc_expenditure * inflatable[input_dollar_year,output_dollar_year])


#%%### Determine whether to take ITC or PTC for overlapping techs

### LBNL 2009 says the PTC is better than the ITC for geothermal 
### (https://www.osti.gov/servlets/purl/950222)
### (or at least it was given the cost and policy specifics in 2009).
### So just apply the PTC for geothermal plants that are eligible for it,
### and ITC after the PTC has expired.
def geo(x):
    """True if tech in geotech else False"""
    return (('pflash' in x) or ('geo' in x) or ('pbinary' in x))

### Get the last year for which geothermal is eligible for the PTC
geo_ptc_cutoff = ptc_values.loc[ptc_values.i.map(geo),'t'].max()

###### Drop ITC for t <= geo_ptc_cutoff
### Get the list of (i,t) to drop
drop_itc = [
    tuple(y) for y in 
    itc_out.loc[
        itc_out.i.map(geo) & (itc_out.t <= geo_ptc_cutoff)
    ][['i','t']].values.tolist()
]
### Drop it
itc_out_deduplicated = itc_out.drop(
    itc_out.loc[
        itc_out.apply(lambda row: tuple(row[['i','t']].to_list()) in drop_itc, axis=1)
    ].index)
if verbose:
    print('Apply PTC for geothermal built <= {} and ITC thereafter'.format(geo_ptc_cutoff))
    print('{} entries keep PTC instead of ITC:\n    {}'.format(
        itc_out.shape[0] - itc_out_deduplicated.shape[0], 
        '\n    '.join(['{} {}'.format(*i) for i in drop_itc])))


#%% Save it

if verbose:
    print('\nptc_out')
    print(ptc_out)
ptc_out.to_csv(
    os.path.join(runpath,'outputs','ptc_expenditures_{}USD.csv'.format(output_dollar_year)),
    index=False
)
if verbose:
    print('\nitc_out_deduplicated')
    print(itc_out_deduplicated)
itc_out_deduplicated.to_csv(
    os.path.join(runpath,'outputs','itc_expenditures_{}USD.csv'.format(output_dollar_year)),
    index=False
)


#############
#%% PLOTS ###

### Stop here if plots are turned off
if not (show_plots or save_plots):
    quit()

###########################################
### PLOTTING FUNCTIONS (just for looks) ###

def plotparams():
    """
    Format plots
    """
    plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['mathtext.rm'] = 'Arial'
    plt.rcParams['mathtext.it'] = 'Arial:italic'
    plt.rcParams['mathtext.bf'] = 'Arial:bold'
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['axes.labelsize'] = 'x-large'
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    plt.rcParams['xtick.labelsize'] = 'large'
    plt.rcParams['ytick.labelsize'] = 'large'
    plt.rcParams['xtick.top'] = True
    plt.rcParams['ytick.right'] = True
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['savefig.bbox'] = 'tight'
    # plt.rcParams['figure.figsize'] = 6.4, 4.8 # 1.33, matplotlib default
    # plt.rcParams['figure.figsize'] = 5.0, 4.0 # 1.25
    plt.rcParams['figure.figsize'] = 5.0, 3.75 # 1.33, fits 4x in ppt slide
    plt.rcParams['xtick.major.size'] = 4 # default 3.5
    plt.rcParams['ytick.major.size'] = 4 # default 3.5
    plt.rcParams['xtick.minor.size'] = 2.5 # default 2
    plt.rcParams['ytick.minor.size'] = 2.5 # default 2

plotparams()

def _despine_sub(ax, 
    top=False, right=False, left=True, bottom=True,
    direction='out'):
    """
    """
    if not top: ax.spines['top'].set_visible(False)
    if not right: ax.spines['right'].set_visible(False)
    if not left: ax.spines['left'].set_visible(False)
    if not bottom: ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='both', which='both',
                   direction=direction, 
                   top=top, right=right, 
                   left=left, bottom=bottom)

def despine(ax=None, 
    top=False, right=False, left=True, bottom=True,
    direction='out'):
    """
    """
    if ax is None:
        ax = plt.gca()
    if type(ax) is np.ndarray:
        for sub in ax:
            if type(sub) is np.ndarray:
                for subsub in sub:
                    _despine_sub(subsub, top, right, left, bottom, direction)
            else:
                _despine_sub(sub, top, right, left, bottom, direction)
    else:
        _despine_sub(ax, top, right, left, bottom, direction)

#%%### PTC
### Aggregate over i's
icat = {}
for i in ptc_out.i.unique():
    if 'bio' in i:
        icat[i] = 'Biopower'
    elif 'wind' in i:
        icat[i] = 'Land-based Wind'
    elif ('geo' in i) or ('pflash' in i):
        icat[i] = 'Geothermal'
    elif 'hyd' in i:
        icat[i] = 'Hydro'
    else:
        raise Exception('i not included: {}'.format(i))

colors = {
    'Biopower':'C2', 
    'Land-based Wind':plt.cm.tab20(1), 
    'Geothermal': 'C5',
    'Hydro':plt.cm.tab20(0),
}

dfplot = ptc_out.copy()
dfplot['icat'] = dfplot.i.map(icat)
dfplot = dfplot.groupby(['t','icat'])['ptc_expenditure'].sum().unstack(level=1) / 1E9

### Plot it
plt.close()
f,ax = plt.subplots()
dfplot.plot.bar(
    ax=ax, stacked=True,
    color=colors, alpha=1, width=0.8
)
### Legend
h,l = ax.get_legend_handles_labels()
ax.legend(
    handles=h[::-1], labels=l[::-1],
#     loc='center left', bbox_to_anchor=(1,0.5), 
    loc='upper left', bbox_to_anchor=(-0.02,1.03), 
    ncol=1, fontsize=13,
    handletextpad=0.3, handlelength=0.7, frameon=False,
)
### Formatting
ax.set_ylabel('Annual PTC Payments [Billion $]')
ax.set_xlabel('')
ax.set_ylim(0)
xlabels = ax.get_xticklabels()
for x in xlabels:
    x._text = '{}–{}'.format(x._text, int(x._text)+1)
ax.set_xticklabels(xlabels, rotation=45, ha='right', rotation_mode='anchor')
despine(ax)

### Save it
if save_plots:
    plt.savefig(
        os.path.join(runpath,'outputs','ptc_expenditures_{}USD.png'.format(output_dollar_year))
    )
if show_plots:
    plt.show()
else:
    plt.close()


#%%### ITC
icat = {}
for i in itc_out_deduplicated.i.unique():
    if 'csp' in i:
        icat[i] = 'CSP'
    elif 'distpv' in i.lower():
        icat[i] = 'Distributed PV'
#     elif 'dupv' in i.lower():
#         icat[i] = 'Distributed Utility PV'
    elif 'upv' in i.lower():
        icat[i] = 'Utility PV'
    elif ('pflash' in i) or ('geo' in i.lower()):
        icat[i] = 'Geothermal'
    elif 'wind-ofs' in i:
        icat[i] = 'Offshore Wind'
    else:
        raise Exception('i not included: {}'.format(i))

colors = {
    'CSP':'C3', 
    'Distributed PV': plt.cm.Dark2(5), # or plt.cm.tab20(3)
    'Utility PV': plt.cm.Dark2(5), # or plt.cm.tab20(2)
    'Geothermal': 'C5',
    'Offshore Wind':plt.cm.tab20(1), 
}

dfplot = itc_out_deduplicated.copy()
dfplot['icat'] = dfplot.i.map(icat)
### Note that we plot against ReEDS year (t) instead of treasury year (t_treasury);
### to change, switch 't' for 't_treasury' in the next line
dfplot = dfplot.groupby(['t','icat'])['itc_expenditure'].sum().unstack(level=1) / 1E9 / 2


plt.close()
f,ax = plt.subplots(figsize=(6.0, 3.75))
dfplot.plot.bar(
    ax=ax, stacked=True,
    color=colors, alpha=1, width=0.8
)
### Legend
h,l = ax.get_legend_handles_labels()
ax.legend(
    handles=h[::-1], labels=l[::-1],
#     loc='center left', bbox_to_anchor=(1,0.5), 
    loc='upper right', #bbox_to_anchor=(-0.02,1.03), 
    ncol=1, fontsize=13,
    handletextpad=0.3, handlelength=0.7, frameon=False,
)
### Formatting
ax.set_xlabel('')
ax.set_ylabel('Annual ITC Payments [Billion $]'.format(output_dollar_year))
ax.set_ylim(0)
xlabels = ax.get_xticklabels()
for x in xlabels:
    x._text = '{}–{}'.format(x._text, int(x._text)+1)
ax.set_xticklabels(xlabels, rotation=60, ha='right', va='center', rotation_mode='anchor')
despine(ax)

### Save it
if save_plots:
    plt.savefig(
        os.path.join(runpath,'outputs','itc_expenditures_{}USD.png'.format(output_dollar_year))
    )
if show_plots:
    plt.show()
else:
    plt.close()
