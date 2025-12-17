#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import pandas as pd
import numpy as np
import os
import sys
import argparse
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
# Time the operation of this script
tic = datetime.datetime.now()

#%% Parse arguments
parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")
parser.add_argument("reeds_path", help="ReEDS directory")
parser.add_argument("inputs_case", help="output directory")

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing
#reeds_path = os.path.expanduser('~/github2/ReEDS-2.0/')
#inputs_case = os.path.join(reeds_path,'runs','v20220421_prmM0_ercot_seq','inputs_case')
#reeds_path = '/Users/apham/Documents/GitHub/ReEDS/ReEDS-2.0/'
#inputs_case = '/Users/apham/Documents/GitHub/ReEDS/ReEDS-2.0/runs/test_Pacific/inputs_case/'

#%% Set up logger
log = reeds.log.makelog(
    scriptname=__file__,
    logpath=os.path.join(inputs_case,'..','gamslog.txt'),
)
print('Starting plantcostprep.py')

#%% Inputs from switches
sw = reeds.io.get_switches(inputs_case)
caesscen = "caes_reference"

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def deflate_func(data,case):
    deflate = dollaryear.loc[dollaryear['Scenario'] == case,'Deflator'].values[0]
    if 'capcost' in data.columns:
        data['capcost'] *= deflate
    if 'capcost_energy' in data.columns:
        data['capcost_energy'] *= deflate
    if 'fom' in data.columns:
        data['fom'] *= deflate
        data['vom'] *= deflate
    if 'fom_energy' in data.columns:
        data['fom_energy'] *= deflate
    return data

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

dollaryear = pd.concat(
    [pd.read_csv(os.path.join(inputs_case,"dollaryear_plant.csv")),
     pd.read_csv(os.path.join(inputs_case,"dollaryear_consume.csv"))]
)
deflator = pd.read_csv(
    os.path.join(inputs_case,"deflator.csv"),
    header=0, names=['Dollar.Year','Deflator'], index_col='Dollar.Year').squeeze(1)

dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left")

#%% Get ILR_ATB from scalars
scalars = reeds.io.get_scalars(inputs_case)

#%%###############
#    -- PV --    #
##################

# Adjust cost data to 2004$
upv = pd.read_csv(os.path.join(inputs_case,'plantchar_upv.csv'))
upv = deflate_func(upv, sw.plantchar_upv).set_index('t')

# Prior to ATB 2020, PV costs are in $/kW_DC
# Starting with ATB 2020 cost inputs, PV costs are in $/kW_AC
# ReEDS uses DC capacity, so divide by inverter loading ratio
if '2019' not in sw.plantchar_upv:
    upv[['capcost','fom','vom']] = upv[['capcost','fom','vom']] / scalars['ilr_utility']

# Broadcast costs to all UPV resource classes
upv_stack = pd.concat(
    {'UPV_{}'.format(c): upv for c in range(1,11)},
    axis=0, names=['i','t']
).reset_index()

#%%########################
#    -- Other Techs --    #
###########################

conv_in = []
conv_techs = ['gas', 'gas_ccs', 'coal', 'coal_ccs', 'biopower', 'nuclear', 'nuclear_smr', 'other']
for ct in conv_techs:
    print(f"Loading plantchar_{ct}")
    df = pd.read_csv(os.path.join(inputs_case,f'plantchar_{ct}.csv'))
    df = deflate_func(df, sw[f'plantchar_{ct}'])
    conv_in.append(df)
# combine into one set of "conventional" generators
conv = pd.concat(conv_in).reset_index(drop=True)

ccsflex = pd.read_csv(os.path.join(inputs_case,'plantchar_ccsflex_cost.csv'))
ccsflex = deflate_func(ccsflex, sw.ccsflexscen)

beccs = pd.read_csv(os.path.join(inputs_case,'plantchar_beccs.csv'))
beccs = deflate_func(beccs, sw.plantchar_beccs)

h2combustion = pd.read_csv(os.path.join(inputs_case,'plantchar_h2combustion.csv'))
h2combustion = deflate_func(h2combustion, sw.plantchar_h2combustion)

if sw.upgradescen != 'default':
    upgrade = pd.read_csv(os.path.join(inputs_case,'plantchar_upgrades.csv'))
    upgrade = deflate_func(upgrade, sw.upgradescen)
    upgrade = upgrade.rename(columns={'capcost':'upgradecost'})
    upgrade = upgrade[['i','t','upgradecost']]
    upgrade['upgradecost'] *= 1000
    upgrade['upgradecost'] = upgrade['upgradecost'].round(0).astype(int)

#%%#########################
#    -- Onshore Wind --    #
############################

onswinddata = pd.read_csv(os.path.join(inputs_case,'plantchar_onswind.csv'))
#We will have a 'Turbine' column. For each turbine, we assume 10 classes
onswinddata.columns= ['turbine','t','cf_mult','capcost','fom','vom']
onswinddata['tech'] = 'ONSHORE'
class_bin_num = 10
turb_ls = []
for turb in onswinddata['turbine'].unique():
    turb_ls += [turb]*class_bin_num
df_class_turb = pd.DataFrame({'turbine':turb_ls, 'class':range(1, len(turb_ls) + 1)})
onswinddata = onswinddata.merge(df_class_turb, on='turbine', how='inner')
onswinddata = onswinddata[['tech','class','t','cf_mult','capcost','fom','vom']]
onswinddata = deflate_func(onswinddata, sw.plantchar_onswind)

#%%##########################
#    -- Offshore Wind --    #
#############################

ofswinddata = pd.read_csv(os.path.join(inputs_case,'plantchar_ofswind.csv'))
if 'Turbine' in ofswinddata:
    #ATB 2024 style
    #We will have a 'Turbine' column (fixed vs floating). For each turbine, we assume 5 classes
    #(fixed = 1-5 and floating = 6-10)
    ofswinddata.columns= ['turbine','t','cf_mult','capcost','fom','vom','rsc_mult']
    ofswinddata['tech'] = 'OFFSHORE'
    class_bin_num = 5
    turb_ls = []
    for turb in ofswinddata['turbine'].unique():
        turb_ls += [turb]*class_bin_num
    df_class_turb = pd.DataFrame({'turbine':turb_ls, 'class':range(1, len(turb_ls) + 1)})
    ofswinddata = ofswinddata.merge(df_class_turb, on='turbine', how='inner')
    ofswind_rsc_mult = ofswinddata[['t','class','rsc_mult']].copy()
    ofswind_rsc_mult['tech'] = 'wind-ofs_' + ofswind_rsc_mult['class'].astype(str)
    ofswind_rsc_mult = ofswind_rsc_mult.pivot_table(index='t',columns='tech', values='rsc_mult')
    ofswinddata = ofswinddata[['tech','class','t','cf_mult','capcost','fom','vom']]
else:
    #ATB 2023 style
    #We need to reduce to 5 classes for fixed and 5 for floating. We'll leave classes 1-5 alone (for fixed), remove classes 6,7,13, and 14, and then rename classes 8-12 to 6-10 (for floating)
    ofswinddata = ofswinddata[~ofswinddata['Wind class'].isin([6,7,13,14])]
    float_cond = ofswinddata['Wind class'] > 7
    ofswinddata.loc[float_cond, 'Wind class'] = ofswinddata.loc[float_cond, 'Wind class'] - 2
    ofswind_rsc_mult = ofswinddata[['Year','Wind class','rsc_mult']].copy()
    ofswind_rsc_mult['tech'] = 'wind-ofs_' + ofswind_rsc_mult['Wind class'].astype(str)
    ofswind_rsc_mult = ofswind_rsc_mult.rename(columns={'Year':'t'})
    ofswind_rsc_mult = ofswind_rsc_mult.pivot_table(index='t',columns='tech', values='rsc_mult')
    ofswinddata = ofswinddata.drop(columns=['rsc_mult'])
    ofswinddata.columns = ['tech','class','t','cf_mult','capcost','fom','vom']
ofswinddata = deflate_func(ofswinddata, sw.plantchar_ofswind)
winddata = pd.concat([onswinddata.copy(),ofswinddata.copy()])

winddata.loc[winddata['tech'].str.contains('ONSHORE'),'tech'] = 'wind-ons'
winddata.loc[winddata['tech'].str.contains('OFFSHORE'),'tech'] = 'wind-ofs'
winddata['i'] = winddata['tech'] + '_' + winddata['class'].astype(str)
wind_stack = winddata[['t','i','capcost','fom','vom']].copy()

#%%#######################
#    -- Geothermal --    #
##########################

geodata = pd.read_csv(os.path.join(inputs_case,'plantchar_geo.csv'))
geodata.columns = ['tech','class','depth','t','capcost','fom','vom']
geodata['i'] = geodata['tech'] + '_' + geodata['depth'] + '_' + geodata['class'].astype(str)
geodata = deflate_func(geodata, sw.plantchar_geo)
geo_stack = geodata[['t','i','capcost','fom','vom']].copy()


#%%################
#    -- CSP --    #
###################


csp = pd.read_csv(os.path.join(inputs_case,'plantchar_csp.csv'))
csp = deflate_func(csp, sw.plantchar_csp)

csp_stack = pd.DataFrame(columns=csp.columns)

#create categories for all upv categories
for n in range(1,13):
	tcsp = csp.copy()
	tcsp['i'] = csp['type']+"_"+str(n)
	csp_stack = pd.concat([csp_stack,tcsp],sort=False)

csp_stack = csp_stack[['t','capcost','fom','vom','i']]

#%%####################
#    -- Storage --    #
#######################

battery = pd.read_csv(os.path.join(inputs_case,'plantchar_battery.csv'))
battery = deflate_func(battery, sw.plantchar_battery)

tes = pd.read_csv(os.path.join(inputs_case,'plantchar_tes.csv'))
tes = deflate_func(tes, sw.plantchar_tes)

evmc_storage = pd.read_csv(os.path.join(inputs_case,'plantchar_evmc_storage.csv'))
evmc_storage = deflate_func(evmc_storage, 'evmc_storage_' + sw.evmcscen)
evmc_shape = pd.read_csv(os.path.join(inputs_case,'plantchar_evmc_shape.csv'), dtype = {'fom':float,'vom':float,'rte':float})
evmc_shape = deflate_func(evmc_shape, 'evmc_shape_' + sw.evmcscen)

caes = pd.read_csv(os.path.join(inputs_case,'plantchar_caes.csv'))
caes = deflate_func(caes,caesscen)
caes['i'] = 'caes'

#%%############################
#    -- Nuclear Storage --    #
###############################

nuclear_stor = pd.read_csv(os.path.join(inputs_case,'plantchar_nuclear_stor.csv'))
nuclear_stor = deflate_func(nuclear_stor, sw.plantchar_nuclear_stor)
# temporary until nuclear-stor is modified to be hybrid-storage where any generation tech can pair with storage
# and this will be replaced with a loop iterating through all hybrid-storage types.
nuclear_stor['i'] = 'Nuclear-Stor1'

#%%############################
#    -- Concat all data --    #
###############################

alldata = pd.concat([conv,upv_stack,wind_stack,geo_stack,csp_stack,battery,tes,
                     evmc_storage,evmc_shape,caes,nuclear_stor,beccs,ccsflex,h2combustion],sort=False)

if sw.upgradescen != 'default':
    alldata = pd.concat([alldata,upgrade])

alldata['t'] = alldata['t'].astype(int)

#Convert from $/kw to $/MW
alldata['capcost'] = alldata['capcost']*1000
alldata['capcost_energy'] = alldata.get('capcost_energy', 0) * 1000
alldata['fom'] = alldata['fom']*1000
alldata['fom_energy'] = alldata.get('fom_energy', 0) * 1000

alldata['capcost'] = alldata['capcost'].round(0).astype(int)
alldata['capcost_energy'] = (alldata['capcost_energy'].fillna(0)).round(0).astype(int)
alldata['fom'] = alldata['fom'].round(0).astype(int)
alldata['fom_energy'] = (alldata['fom_energy'].fillna(0)).round(0).astype(int)
alldata['vom'] = alldata['vom'].round(4)
alldata['heatrate'] = alldata['heatrate'].round(4)

# Fill empty values with 0, melt to long format
outdata = (
	alldata.fillna(0)
	.melt(id_vars=['i','t'])
	### Rename the columns so GAMS reads them as a comment
	.rename(columns={'i':'*i'})
)

outdata = outdata.loc[outdata.variable.isin(['capcost', 'capcost_energy',
                                             'fom', 'fom_energy',
                                             'vom','heatrate','upgradecost','rte'])]

#%%##################################
#    -- Wind Capacity Factors --    #
#####################################

windcfmult = winddata[['t','i','cf_mult']].set_index(['i','t'])['cf_mult']
windcfmult = windcfmult.round(6)
outwindcfmult = windcfmult.reset_index().pivot_table(index='t',columns='i', values='cf_mult')

#%%###########################################################
#    -- Electrolyzer Stack Replacement Cost Adjustment --    #
##############################################################

consume_char = pd.read_csv(os.path.join(inputs_case,'consume_char.csv'))

# grab the electrolyzer cost 'h2_elec_stack_replace_year' years into the future
current_year = datetime.date.today().year
mask = (consume_char['*i'].isin(['electrolyzer'])) & (consume_char['parameter'].isin(['cost_cap']) & (consume_char['t'].isin([current_year+scalars['h2_elec_stack_replace_year']]))) 
elec_cost_future = consume_char[mask]['value'].values[0]

# read in financials_sys from inputs_case and take the average of all past years to get an average discount rate
financials_sys = pd.read_csv(os.path.join(inputs_case,'financials_sys.csv')) 
discount_rate = np.average(financials_sys[(financials_sys['t'] <= current_year)]['d_real'].values)

# the capital cost of electrolyzers needs to be increased by the cost to replace the stack ('h2_elec_stack_replace_perc')
# this replacement cost is represented as a percent of the capital cost of a new electrolyzer in that year. This cost occurs 'h2_elec_stack_replace_year' years in the future so we discount it.
mask = (consume_char['*i'].isin(['electrolyzer'])) & (consume_char['parameter'].isin(['cost_cap'])) 
consume_char.loc[mask, 'value'] = consume_char[mask]['value'] + round( (elec_cost_future * scalars['h2_elec_stack_replace_perc'])/(discount_rate**scalars['h2_elec_stack_replace_year']) ,3)

#%%###############################
#    -- Other Technologies --    #
##################################

ccsflex_perf = pd.read_csv(os.path.join(inputs_case,'plantchar_ccsflex_perf.csv'),index_col=0).round(6)
hydro = pd.read_csv(os.path.join(inputs_case,'plantchar_hydro.csv'), index_col=0).round(6)
dr_shed = pd.read_csv(os.path.join(inputs_case,'plantchar_dr_shed.csv'), index_col=0).round(6)
degrade = pd.read_csv(
	os.path.join(inputs_case,'degradation_annual.csv'),
	header=None)
degrade.columns = ['i','rate']
degrade = reeds.techs.expand_GAMS_tech_groups(degrade)
degrade = degrade.set_index('i').round(6)

#%%##################################
#    -- PV+Battery Cost Model --    #
#####################################

# Get PVB designs
pvb_ilr = pd.read_csv(
    os.path.join(inputs_case, 'pvb_ilr.csv'),
    header=0, names=['pvb_type','ilr'], index_col='pvb_type').squeeze(1)
pvb_bir = pd.read_csv(
    os.path.join(inputs_case, 'pvb_bir.csv'),
    header=0, names=['pvb_type','bir'], index_col='pvb_type').squeeze(1)
# Get PV and battery $/Wac costs for PVB
battery_USDperWac = (
    battery.loc[battery.i==f'battery_li'].set_index('t').capcost
    + float(sw.GSw_PVB_Dur)
      * battery.loc[battery.i==f'battery_li'].set_index('t').capcost_energy
)
UPV_defaultILR_USDperWac = upv.capcost * scalars['ilr_utility']
# Get cost-sharing assumptions
pvbvalues = pd.read_csv(os.path.join(inputs_case,'plantchar_pvb.csv'), index_col='parameter')
fixed_ac_noninverter_cost_USDperWac = (
    pvbvalues.loc['fixed','value']
    * deflator[pvbvalues.loc['fixed','dollaryear']]
    # Input units are in $/Wac, so convert to $/MWac to match units used in ReEDS
    * 1000
)

def get_pvb_cost(
        UPV_defaultILR_USDperWac, battery_USDperWac,
        ILR_user=1.8, BIR_user=0.5,
        inverter_cost_ac_fraction=0.05,
        fixed_ac_noninverter_cost_USDperWac=0.0455,
        ILR_ATB=1.3,
):
    # Inverter cost is taken as a fixed fraction of UPV AC cost
    inverter_USDperWac = UPV_defaultILR_USDperWac * inverter_cost_ac_fraction
    # Standalone PV $/Wdc is [$/Wac] * [Wac/Wdc], where [$/Wac] is the full
    # $/Wac minus the inverter cost and AC fixed costs
    UPV_USDperWdc = (
        UPV_defaultILR_USDperWac
        - inverter_USDperWac
        - fixed_ac_noninverter_cost_USDperWac
    ) / ILR_ATB
    # Standalone PV $/Wac for the user-defined ILR: [$/Wac] + [$/Wdc] * ILR
    UPV_USDperWac = (
        inverter_USDperWac
        + fixed_ac_noninverter_cost_USDperWac
        + UPV_USDperWdc * ILR_user
    )
    # PVB system cost
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
    # Standalone system cost for two systems with same DC capacity;
    # here the battery needs its own inverter and AC fixed costs,
    # so we don't subtract them out as we did above for PVB
    standalone_USDperWac = (
        # PV
        UPV_USDperWac
        # Battery sized relative to PV
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
for i in sw['GSw_PVB_Types'].split('_'):
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

#%%##################################
#    -- Nuclear+Storage Cost Model --    #
#####################################
# Get nuclear+storage designs
nuclear_bcrs = pd.read_csv(
    os.path.join(inputs_case, 'nuclear_stor_bcr.csv'),
    header=0, names=['nuclear_type','bcr'], index_col='nuclear_type').squeeze(1)
nuclear_storagetech = pd.read_csv(
    os.path.join(inputs_case, 'nuclear_stor_storagetechs.csv'),
    header=0, names=['nuclear_type','storage_type'], index_col='nuclear_type').squeeze(1)
# Get cost-sharing assumptions
mstesvalues = pd.read_csv(os.path.join(inputs_case,'mstes_values.csv'), index_col='parameter')
heatpump_cost_USDperWac = (
    mstesvalues.loc['heatpump','value']
    * mstesvalues.loc['heatrate','value']
    * deflator[mstesvalues.loc['heatpump','dollaryear']]
    # Input units are in $/Wac, so convert to $/MWac to match units used in ReEDS
    * 1000
)

nuclear_default = nuclear_stor.set_index('t').capcost

# Calculate nuclear storage cost fraction for each design
nuclearstorage = {}
for i in sw['GSw_NuclearStor_Types'].split('_'):
    stor_tech = nuclear_storagetech.loc['nuclear-stor{}'.format(i)]
    nuclear_bcr = nuclear_bcrs.loc['nuclear-stor{}'.format(i)]
    print(f"Calculating nuclear-stor{i} with storage tech {stor_tech} and BCR {nuclear_bcr}")
    if stor_tech.startswith('battery'):
        storage_USDperWac = battery.loc[battery.i==stor_tech].set_index('t').capcost
        energyconversion_cost_USDperWac = 0  # battery is DC-coupled
    elif stor_tech.startswith('tes'):
        storage_USDperWac = tes.loc[tes.i==stor_tech].set_index('t').capcost
        energyconversion_cost_USDperWac = heatpump_cost_USDperWac
    elif stor_tech.startswith('caes'):
        storage_USDperWac = caes.loc[caes.i==stor_tech].set_index('t').capcost
        energyconversion_cost_USDperWac = 0  # CAES is coupled using the same equipment as it is to the grid
    print('storage_USDperWac', storage_USDperWac)
    print('energyconversion_cost_USDperWac', energyconversion_cost_USDperWac)
    print('nuclear_default', nuclear_default)
    nuclear_storage_cost = nuclear_default + nuclear_bcr * (storage_USDperWac - energyconversion_cost_USDperWac)
    print('nuclear_storage_cost', nuclear_storage_cost)
    nuclearstorage['nuclear-stor{}'.format(i)] = nuclear_storage_cost / nuclear_default
nuclearstorage = pd.concat(nuclearstorage, axis=1)


## Create Electric DAC scenario output
# For electric DAC, we assume a sorbent system: https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a
# FYI, for DAC-gas we assume a solvent system: https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987
dac_elec = pd.read_csv(os.path.join(inputs_case,'dac_elec.csv'))
dac_elec = deflate_func(dac_elec, f'dac_elec_{sw.dacscen}').round(4)
# Fill empty values with 0, melt to long format
outdac_elec = (
    dac_elec.fillna(0)
    .melt(id_vars=['i','t'],value_vars=['capcost','fom','vom','conversionrate'])
    ### Rename the columns so GAMS reads them as a comment
    .rename(columns={'i':'*i'})
)


## Create Gas DAC scenario output
# For DAC-gas we assume a solvent system: https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987
dac_gas = pd.read_csv(os.path.join(inputs_case,'dac_gas.csv'))
dac_gas = deflate_func(dac_gas, f'dac_gas_{sw.GSw_DAC_Gas_Case}').round(4)


#%%###################################################
#    -- Cost Adjustment for cost_upgrade Techs --    #
######################################################
upgrade_mult_mid = pd.read_csv(os.path.join(inputs_case,"upgrade_mult_mid.csv"))
upgrade_mult_advanced = pd.read_csv(os.path.join(inputs_case,"upgrade_mult_advanced.csv"))
upgrade_mult_conservative = pd.read_csv(os.path.join(inputs_case,"upgrade_mult_conservative.csv"))

if int(sw.GSw_UpgradeCost_Mult) == 0:
    upgrade_mult = upgrade_mult_mid
elif int(sw.GSw_UpgradeCost_Mult) == 1:
    upgrade_mult = upgrade_mult_advanced
elif int(sw.GSw_UpgradeCost_Mult) == 2:
    upgrade_mult = upgrade_mult_conservative
elif int(sw.GSw_UpgradeCost_Mult) == 3:
    upgrade_mult = 1
elif int(sw.GSw_UpgradeCost_Mult) == 4:
    upgrade_mult = 1 + (1-upgrade_mult_mid)
elif int(sw.GSw_UpgradeCost_Mult) == 5:
    upgrade_mult = 1.2

#%%###########################
#    -- Data Write-Out --    #
##############################

print('writing plant data to:', os.getcwd())
outdata.to_csv(os.path.join(inputs_case,'plantcharout.csv'), index=False)
upv.cf_improvement.round(3).to_csv(os.path.join(inputs_case,'pv_cf_improve.csv'), header=False)
outwindcfmult.to_csv(os.path.join(inputs_case,'windcfmult.csv'))
ccsflex_perf.to_csv(os.path.join(inputs_case,'ccsflex_perf.csv'))
consume_char.to_csv(os.path.join(inputs_case,'consume_char.csv'),index=False)
hydro.to_csv(os.path.join(inputs_case,'hydrocapcostmult.csv'))
dr_shed.to_csv(os.path.join(inputs_case,'dr_shed_capcostmult.csv'))
ofswind_rsc_mult.to_csv(os.path.join(inputs_case,'ofswind_rsc_mult.csv'))
degrade.to_csv(os.path.join(inputs_case,'degradation_annual.csv'),header=False)
pvb.to_csv(os.path.join(inputs_case,'pvbcapcostmult.csv'))
nuclearstorage.to_csv(os.path.join(inputs_case,'nuclearstorcapcostmult.csv'))
upgrade_mult.round(4).to_csv(os.path.join(inputs_case,'upgrade_mult_final.csv'), index=False)
outdac_elec.to_csv(os.path.join(inputs_case,'consumechardac.csv'), index=False)
dac_gas.to_csv(os.path.join(inputs_case,'dac_gas.csv'), index=False)

reeds.log.toc(tic=tic, year=0, process='input_processing/plantcostprep.py', 
    path=os.path.join(inputs_case,'..'))

print('Finished plantcostprep.py')
