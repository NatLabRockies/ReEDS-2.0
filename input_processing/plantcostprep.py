#%% IMPORTS
import pandas as pd
import os
import argparse
import support_functions as sFuncs
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%% Model Inputs
parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")

parser.add_argument("reeds_path", help="ReEDS directory")
parser.add_argument("inputs_case", help="output directory")

args = parser.parse_args()

reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Testing inputs
# reeds_path = os.path.expanduser('~/github2/ReEDS-2.0/')
# inputs_case = os.path.join(reeds_path,'runs','v20220421_prmM0_ercot_seq','inputs_case')

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

convscen = sw.convscen
onswindscen = sw.onswindscen
ofswindscen = sw.ofswindscen
upvscen = sw.upvscen
cspscen = sw.cspscen
batteryscen = sw.batteryscen
drscen = sw.drscen
pvbscen = sw.pvbscen
geoscen = sw.geoscen
hydroscen = sw.hydroscen
beccsscen = sw.beccsscen
ccsflexscen = sw.ccsflexscen
h2ctscen = sw.h2ctscen
dacscen = sw.dacscen
upgradescen = sw.upgradescen
degrade_suffix = sw.degrade_suffix
caesscen = "caes_reference"
GSw_PVB_Dur = int(sw.GSw_PVB_Dur)

#%% FUNCTIONS
#function for applying dollar year deflator
def deflate_func(data,case):
    deflate = dollaryear.loc[dollaryear['Scenario'] == case,'Deflator'].values[0]
    if 'capcost' in data.columns:
        data.loc[:,'capcost'] = data['capcost'] * deflate
    if 'fom' in data.columns:
        data.loc[:,'fom'] = data['fom'] * deflate
        data.loc[:,'vom'] = data['vom'] * deflate
    return data

#%% PROCEDURE
inpath = os.path.join(reeds_path,"inputs","plant_characteristics")

dollaryear = pd.concat([pd.read_csv(os.path.join(inpath,"dollaryear.csv")),
                        pd.read_csv(
                            os.path.join(reeds_path,"inputs","consume","dollaryear.csv"))])
deflator = pd.read_csv(
    os.path.join(inpath,"../deflator.csv"),
    header=0, names=['Dollar.Year','Deflator'], index_col='Dollar.Year', squeeze=True)

dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left")

#%% Get ILR_ATB from scalars
### NOTE that as of 2021-11-15, the ILR assumed for the ATB is 1.34, but 1.3 is used in reV/ReEDS.
scalars = pd.read_csv(
    os.path.join(inputs_case,'scalars.csv'),
    header=None, names=['scalar','value','comment'], index_col='scalar')['value']

#%% PV
#Adjust cost data to 2004$
upv = pd.read_csv(os.path.join(inpath,upvscen+'.csv'))
upv = deflate_func(upv,upvscen).set_index('t')

#Prior to ATB 2020, PV costs are in $/kW_DC
#Starting with ATB 2020 cost inputs, PV costs are in $/kW_AC
#ReEDS uses DC capacity, so divide by inverter loading ratio
if not '2019' in upvscen:
    upv[['capcost','fom','vom']] = upv[['capcost','fom','vom']] / scalars['ilr_utility']

# Broadcast costs to all UPV resource classes
upv_stack = pd.concat(
    {'UPV_{}'.format(c): upv for c in range(1,11)},
    axis=0, names=['i','t']
).reset_index()

#%% Other techs
conv = pd.read_csv(os.path.join(inpath,convscen+'.csv'))
conv = deflate_func(conv,convscen)

ccsflex = pd.read_csv(os.path.join(inpath,ccsflexscen+'_cost.csv'))
ccsflex = deflate_func(ccsflex,ccsflexscen)

beccs = pd.read_csv(os.path.join(inpath,beccsscen+'.csv'))
beccs = deflate_func(beccs,beccsscen)

h2ct = pd.read_csv(os.path.join(inpath,h2ctscen+'.csv'))
h2ct = deflate_func(h2ct,h2ctscen)

if upgradescen != 'default':
    upgrade = pd.read_csv(os.path.join(inpath,upgradescen+'.csv'))
    upgrade = deflate_func(upgrade,upgradescen)
    upgrade = upgrade.rename(columns={'capcost':'upgradecost'})
    upgrade = upgrade[['i','t','upgradecost']]
    upgrade['upgradecost'] *= 1000
    upgrade['upgradecost'] = upgrade['upgradecost'].round(0).astype(int)

#%% Onshore Wind
onswinddata = pd.read_csv(os.path.join(inpath,onswindscen+'.csv'))
if 'class' in onswinddata:
    #ATB 2022 and prior style
    onswinddata.columns= ['tech','class','t','cf_mult','capcost','fom','vom']
else:
    #ATB 2023 style
    #We will have a 'turbine' column. For each turbine, we assume 10 classes
    onswinddata.columns= ['turbine','t','cf_mult','capcost','fom','vom']
    onswinddata['tech'] = 'ONSHORE'
    class_bin_num = 10
    turb_ls = []
    for turb in onswinddata['turbine'].unique():
        turb_ls += [turb]*class_bin_num
    df_class_turb = pd.DataFrame({'turbine':turb_ls, 'class':range(1, len(turb_ls) + 1)})
    onswinddata = onswinddata.merge(df_class_turb, on='turbine', how='inner')
    onswinddata = onswinddata[['tech','class','t','cf_mult','capcost','fom','vom']]
onswinddata = deflate_func(onswinddata,onswindscen)

#%% Offshore Wind
ofswinddata = pd.read_csv(os.path.join(inpath,ofswindscen+'.csv'))
if 'rsc_mult' in ofswinddata: #This is the format starting ATB 2023
    ofswind_rsc_mult = ofswinddata[['Year','Wind class','rsc_mult']].copy()
    ofswind_rsc_mult['tech'] = 'wind-ofs_' + ofswind_rsc_mult['Wind class'].astype(str)
    ofswind_rsc_mult = ofswind_rsc_mult.rename(columns={'Year':'t'})
    ofswind_rsc_mult = ofswind_rsc_mult.pivot_table(index='t',columns='tech', values='rsc_mult')
    ofswinddata = ofswinddata.drop(columns=['rsc_mult'])
else: #This is the format for ATB 2022 and before
    ofswind_rsc_mult = pd.read_csv(os.path.join(inpath,ofswindscen+'_rsc_mult.csv'),index_col=0).round(6)


ofswinddata.columns = ['tech','class','t','cf_mult','capcost','fom','vom']
ofswinddata = deflate_func(ofswinddata,ofswindscen)
winddata = pd.concat([onswinddata.copy(),ofswinddata.copy()])

winddata.loc[winddata['tech'].str.contains('ONSHORE'),'tech'] = 'wind-ons'
winddata.loc[winddata['tech'].str.contains('OFFSHORE'),'tech'] = 'wind-ofs'
winddata['i'] = winddata['tech'] + '_' + winddata['class'].astype(str)
wind_stack = winddata[['t','i','capcost','fom','vom']].copy()

#%% Geothermal
geodata = pd.read_csv(os.path.join(inpath,geoscen+'.csv'))
geodata.columns = ['tech','class','depth','t','capcost','fom','vom']
geodata['i'] = geodata['tech'] + '_' + geodata['depth'] + '_' + geodata['class'].astype(str)
geodata = deflate_func(geodata,geoscen)
geo_stack = geodata[['t','i','capcost','fom','vom']].copy()

#%% CSP
csp = pd.read_csv(os.path.join(inpath,cspscen+'.csv'))
csp = deflate_func(csp,cspscen)

csp_stack = pd.DataFrame(columns=csp.columns)

#create categories for all upv categories
for n in range(1,13):
	tcsp = csp.copy()
	tcsp['i'] = csp['type']+"_"+str(n)
	csp_stack = pd.concat([csp_stack,tcsp],sort=False)

csp_stack = csp_stack[['t','capcost','fom','vom','i']]

#%% Storage
battery = pd.read_csv(os.path.join(inpath,batteryscen+'.csv'))
battery = deflate_func(battery,batteryscen)

dr = pd.read_csv(os.path.join(inpath,'dr_'+drscen+'.csv'))
dr = deflate_func(dr,'dr_'+drscen)

caes = pd.read_csv(os.path.join(inpath,caesscen+'.csv'))
caes = deflate_func(caes,caesscen)
caes['i'] = 'caes'

alldata = pd.concat([conv,upv_stack,wind_stack,geo_stack,csp_stack,battery,dr,caes,beccs,ccsflex,h2ct],sort=False)

if upgradescen != 'default':
    alldata = pd.concat([alldata,upgrade])

alldata['t'] = alldata['t'].astype(int)

#Convert from $/kw to $/MW
alldata['capcost'] = alldata['capcost']*1000
alldata['fom'] = alldata['fom']*1000

alldata['capcost'] = alldata['capcost'].round(0).astype(int)
alldata['fom'] = alldata['fom'].round(0).astype(int)
alldata['vom'] = alldata['vom'].round(4)
alldata['heatrate'] = alldata['heatrate'].round(4)

# Fill empty values with 0, melt to long format
outdata = (
	alldata.fillna(0)
	.melt(id_vars=['i','t'])
	### Rename the columns so GAMS reads them as a comment
	.rename(columns={'i':'*i'})
)

outdata = outdata.loc[outdata.variable.isin(['capcost','fom','vom','heatrate','upgradecost','rte'])]

#%% wind capacity factors
windcfmult = winddata[['t','i','cf_mult']].set_index(['i','t'])['cf_mult']
windcfmult = windcfmult.round(6)
outwindcfmult = windcfmult.reset_index().pivot_table(index='t',columns='i', values='cf_mult')

#%% Other technologies
ccsflex_perf = pd.read_csv(os.path.join(inpath,ccsflexscen+'_perf.csv'),index_col=0).round(6)
hydro = pd.read_csv(os.path.join(inpath,hydroscen+'.csv'), index_col=0).round(6)
degrade = pd.read_csv(
	os.path.join(reeds_path,"inputs","degradation",'degradation_annual_' + degrade_suffix + '.csv'),
	header=None)
degrade.columns = ['i','rate']
degrade = sFuncs.expand_GAMS_tech_groups(degrade)
degrade = degrade.set_index('i').round(6)

#%%### PV+battery cost model
### Get PVB designs
pvb_ilr = pd.read_csv(
    os.path.join(inputs_case, 'pvb_ilr.csv'),
    header=0, names=['pvb_type','ilr'], index_col='pvb_type', squeeze=True)
pvb_bir = pd.read_csv(
    os.path.join(inputs_case, 'pvb_bir.csv'),
    header=0, names=['pvb_type','bir'], index_col='pvb_type', squeeze=True)
### Get PV and battery $/Wac costs for PVB
battery_USDperWac = battery.loc[battery.i=='battery_{}'.format(GSw_PVB_Dur)].set_index('t').capcost
UPV_defaultILR_USDperWac = upv.capcost * scalars['ilr_utility']
### Get cost-sharing assumptions
pvbvalues = pd.read_csv(os.path.join(inpath,'pvb_'+pvbscen+'.csv'), index_col='parameter')
fixed_ac_noninverter_cost_USDperWac = (
    pvbvalues.loc['fixed','value']
    * deflator[pvbvalues.loc['fixed','dollaryear']]
    ### Input units are in $/Wac, so convert to $/MWac to match units used in ReEDS
    * 1000
)

def get_pvb_cost(
        UPV_defaultILR_USDperWac, battery_USDperWac,
        ILR_user=1.8, BIR_user=0.5,
        inverter_cost_ac_fraction=0.05,
        fixed_ac_noninverter_cost_USDperWac=0.0455,
        ILR_ATB=1.3,
):
    ### Inverter cost is taken as a fixed fraction of UPV AC cost
    inverter_USDperWac = UPV_defaultILR_USDperWac * inverter_cost_ac_fraction
    ### Standalone PV $/Wdc is [$/Wac] * [Wac/Wdc], where [$/Wac] is the full
    ### $/Wac minus the inverter cost and AC fixed costs
    UPV_USDperWdc = (
        UPV_defaultILR_USDperWac
        - inverter_USDperWac
        - fixed_ac_noninverter_cost_USDperWac
    ) / ILR_ATB
    ### Standalone PV $/Wac for the user-defined ILR: [$/Wac] + [$/Wdc] * ILR
    UPV_USDperWac = (
        inverter_USDperWac
        + fixed_ac_noninverter_cost_USDperWac
        + UPV_USDperWdc * ILR_user
    )
    ### PVB system cost
    PVB_USDperWac = (
        ## PV
        UPV_USDperWac
        ## Battery sized relative to PV
        + BIR_user * (
            battery_USDperWac
            ## Minus fixed AC costs
            - fixed_ac_noninverter_cost_USDperWac
            - inverter_USDperWac
        )
    )
    ### Standalone system cost for two systems with same DC capacity;
    ### here the battery needs its own inverter and AC fixed costs,
    ### so we don't subtract them out as we did above for PVB
    standalone_USDperWac = (
        ## PV
        UPV_USDperWac
        ## Battery sized relative to PV
        + BIR_user * battery_USDperWac
    )
    ### Savings vs standalone
    # savings_fraction = 1 - PVB_USDperWac / standalone_USDperWac
    # savings_USDperWac = standalone_USDperWac - PVB_USDperWac
    pvb_cost_fraction = PVB_USDperWac / standalone_USDperWac
    ### Outputs
    out = {
        'pvb': PVB_USDperWac,
        'standalone_pv_dc': UPV_USDperWdc,
        'standalone_pv_ac': UPV_USDperWac,
        'standalone_both': standalone_USDperWac,
        'inverter': inverter_USDperWac,
        'pvb_cost_fraction': pvb_cost_fraction,
    }
    return out

#%% Calculate PVB cost fraction for each PVB design
pvb = {}
for i in range(1,4):
    pvb['pvb{}'.format(i)] = get_pvb_cost(
        UPV_defaultILR_USDperWac=UPV_defaultILR_USDperWac,
        battery_USDperWac=battery_USDperWac,
        ILR_user=pvb_ilr['pvb{}'.format(i)],
        BIR_user=pvb_bir['pvb{}'.format(i)],
        inverter_cost_ac_fraction=pvbvalues.loc['inverter_fraction','value'],
        fixed_ac_noninverter_cost_USDperWac=fixed_ac_noninverter_cost_USDperWac,
        ILR_ATB=scalars['ilr_utility'],
    )['pvb_cost_fraction']
pvb = pd.concat(pvb, axis=1)


## Create Electric DAC scenario output
# For electric DAC, we assume a sorbent system: https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a
# FYI, for DAC-gas we assume a solvent system: https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987
if dacscen:
    dac = pd.read_csv(os.path.join(reeds_path,"inputs","consume",f'dac_elec_{dacscen}.csv'))
    dac = deflate_func(dac, f'dac_elec_{dacscen}')

    dac['capcost'] = dac['capcost'].round(0).astype(int)
    dac['fom'] = dac['fom'].round(0).astype(int)
    dac['vom'] = dac['vom'].round(8)
    dac['conversionrate'] = dac['conversionrate'].round(8)


    # Fill empty values with 0, melt to long format
    outdac = (
        dac.fillna(0)
        .melt(id_vars=['i','t'],value_vars=['capcost','fom','vom','conversionrate'])
        ### Rename the columns so GAMS reads them as a comment
        .rename(columns={'i':'*i'})
    )

    outdac.to_csv(os.path.join(inputs_case,'consumechardac.csv'), index=False)


#%% Write the outputs
print('writing plant data to:', os.getcwd())
pvb.to_csv(os.path.join(inputs_case,'pvbcapcostmult.csv'))
geodata.to_csv(os.path.join(inputs_case,'geodataout.csv'))

ccsflex_perf.to_csv(os.path.join(inputs_case,'ccsflex_perf.csv'))
hydro.to_csv(os.path.join(inputs_case,'hydrocapcostmult.csv'))
ofswind_rsc_mult.to_csv(os.path.join(inputs_case,'ofswind_rsc_mult.csv'))
degrade.to_csv(os.path.join(inputs_case,'degradation_annual.csv'),header=False)
outwindcfmult.to_csv(os.path.join(inputs_case,'windcfmult.csv'))
upv.cf_improvement.round(3).to_csv(os.path.join(inputs_case,'pv_cf_improve.csv'), header=False)
outdata.to_csv(os.path.join(inputs_case,'plantcharout.csv'), index=False)

toc(tic=tic, year=0, process='input_processing/plantcostprep.py', 
    path=os.path.join(inputs_case,'..'))
print('plantcostprep.py completed successfully')
