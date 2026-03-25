###########
#%% IMPORTS
import os
import pandas as pd

reeds_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pd.options.display.max_rows = 45
pd.options.display.max_columns = 200


#############
#%% PROCEDURE

#%% Define switch collections for scenarios
sw = {
    ### Transmission
    'transmission': {
        'No': {'GSw_TransRestrict':'r','GSw_TransMultiLink':0},
        'Xlim': {'GSw_TransInvMax':1.36, 'GSw_TransRestrict':'transreg'},
        'Lim': {'GSw_TransInvMax':3.64, 'GSw_TransRestrict':'transreg'},
        'AC': {},
        'LCC': {'GSw_TransInterconnect':1, 'GSw_TransScen':'LCC_20220808'},
        'VSC': {'GSw_TransInterconnect':1, 'GSw_TransScen':'VSC_all', 'GSw_VSC':1},
    },
    ### Demand
    'demand': {
        'DemHi': {},
        'DemLo': {'GSw_EFS1_AllYearLoad':'EERbaseClip40'},
    },
    ### Policy
    'policy': {
        ### Actual phaseout
        '100by2035': {},
        '90by2035': {
            'GSw_AnnualCapScen':'start2024_90pct2035_100pct2045',
            'GSw_NG_CRF_penalty':'ramp_2045'},
        'CurrentPol': {'GSw_AnnualCap':0, 'GSw_NG_CRF_penalty':'none'},
        ### 2032 phaseout
        '100by2035EarlyPhaseout': {'GSw_TCPhaseout_forceyear':2032},
        '90by2035EarlyPhaseout': {
            'GSw_AnnualCapScen':'start2024_90pct2035_100pct2045',
            'GSw_NG_CRF_penalty':'ramp_2045', 'GSw_TCPhaseout_forceyear':2032},
        'CurrentPolEarlyPhaseout': {
            'GSw_AnnualCap':0, 'GSw_NG_CRF_penalty':'none', 'GSw_TCPhaseout_forceyear':2032},
        ### No phaseout
        # '100by2035NoPhaseout': {'GSw_TCPhaseout':0, 'incentives_suffix':'ira_extend'},
        # '90by2035NoPhaseout': {
        #     'GSw_AnnualCapScen':'start2024_90pct2035_100pct2045',
        #     'GSw_NG_CRF_penalty':'ramp_2045', 'GSw_TCPhaseout':0,
        #     'incentives_suffix':'ira_extend'},
        'CurrentPolNoPhaseout': {
            'GSw_AnnualCap':0, 'GSw_NG_CRF_penalty':'none', 'GSw_TCPhaseout':0,
            'incentives_suffix':'ira_extend'},
        ### No IRA
        '100by2035NoIRA': { # secondary
            'incentives_suffix':'biennial', 'distpvscen':'StScen2022_Mid_Case_noIRA',
            'GSw_NukeNoRetire':0, 'GSw_TCPhaseout':0,
        },
        '90by2035NoIRA': { # secondary
            'GSw_AnnualCapScen':'start2024_90pct2035_100pct2045', 'GSw_NG_CRF_penalty':'ramp_2045',
            'incentives_suffix':'biennial', 'distpvscen':'StScen2022_Mid_Case_noIRA',
            'GSw_NukeNoRetire':0, 'GSw_TCPhaseout':0,
        },
        'CurrentPolNoIRA': {
            'GSw_AnnualCap':0, 'GSw_NG_CRF_penalty':'none',
            'incentives_suffix':'biennial', 'distpvscen':'StScen2022_Mid_Case_noIRA',
            'GSw_NukeNoRetire':0, 'GSw_TCPhaseout':0,
        },
    },
    ### Sensitivity
    'sensitivity': {
        'core': {},
        'TransCost5x': {'GSw_TransCostMult':5},
        'DERhi': {'distpvscen':'Decarb_2021'}, # secondary
        'SitingLim': { # high priority
            'GSw_SitingUPV':'limited', 'GSw_SitingWindOns':'limited'},
        'PVbattCostLo': {
            'upvscen':'upv_ATB_2022_advanced', 'batteryscen':'battery_ATB_2022_advanced'},
        'WindCostLo': {
            'onswindscen':'ons-wind_ATB_2022_advanced',
            'ofswindscen':'ofs-wind_ATB_2022_advanced'},
        'CCS0Nuc0': {'GSw_CCS':0, 'GSw_Nuclear':0},
        # 'NucCCScostHi': { # secondary
        #     'ccs_upgrade_cost_coal':'petra_atb_declines_frac',
        #     'ccs_upgrade_cost_gas':'petra_atb_declines_frac',
        #     'convscen':'conv_ATB_2022_vogtle'},
        'NSMR1DAC1': {'GSw_NuclearSMR':1, 'GSw_DAC':2},
        'GasPriceHi': {'ngscen':'AEO_2023_LOG'},
        'GasPriceLo': {'ngscen':'AEO_2023_HOG'},
        'H2priceHi': {'rectfuelscen':40},
        'H2priceLo': {'rectfuelscen':10},
        'DemandClip80': {'GSw_EFS1_AllYearLoad':'EERhighClip80'},
        'PRMtradeFERC': {'GSw_PRMTRADE_level':'transreg'}, # secondary
        'NetLoadInt': {'capcredit_hierarchy_level':'interconnect'}, # secondary
        'Climate': {
            'GSw_ClimateHeuristics':'2025_2050_linear', 'GSw_ClimateHydro':1,
            ## 'GSw_WaterMain':1, 'GSw_WaterCapacity':1, 'GSw_WaterUse':1, 'GSw_ClimateWater':1,
        },
        'AllWrong': { # high priority
            'rectfuelscen':40, 'GSw_CCS':0, 'GSw_Nuclear':0,
            'GSw_SitingUPV':'limited', 'GSw_SitingWindOns':'limited',
            'GSw_ClimateHeuristics':'2025_2050_linear', 'GSw_ClimateHydro':1,
        },
    }
}

# print([len(v) for k,v in sw.items()])
# print(np.cumprod(np.array([len(v) for k,v in sw.items()])))

#%% Define the case name format
def make_case(label, defaults, sw):
    ### Get collections of settings
    sensitivity = label.split('__')[-1]
    transmission, demand, policy = label.split('__')[0].split('_')
    ### Build the new case settings
    settings = {
        **sw['transmission'][transmission],
        **sw['demand'][demand],
        **sw['policy'][policy],
        **sw['sensitivity'][sensitivity],
    }
    for key in settings:
        if key not in defaults.index:
            raise Exception(f'{key} not in defaults')
    case = pd.Series(settings, dtype='object').reindex(defaults.index).fillna('')
    return case

#%% Load defaults
defaults = pd.read_csv(
    os.path.join(reeds_path,'cases_NTPS_defaults.csv'),
    index_col=0, squeeze=True,
)

#%% Create the case names
cases = (
    ### Tier 1
    [
        f'{t}_{d}_{p}__core'
        for p in sw['policy']
        for d in sw['demand']
        for t in sw['transmission']
    ]
    # ### Tier 2
    + [
        f'{t}_DemLo_CurrentPol__{s}'
        for s in ['SitingLim','AllWrong']
        for t in sw['transmission']
    ]
    + [
        f'{t}_DemHi_CurrentPol__{s}'
        for s in ['SitingLim','AllWrong']
        for t in sw['transmission']
    ]
    # + [
    #     f'{t}_DemHi_100by2035NoPhaseout__{s}'
    #     for s in sw['sensitivity']
    #     for t in sw['transmission']
    # ]
    # ### Tier 3
    # + [
    #     f'{t}_DemHi_90by2035NoPhaseout__{s}'
    #     for s in sw['sensitivity']
    #     for t in sw['transmission']
    # ]
    + [
        f'{t}_DemLo_CurrentPolNoPhaseout__{s}'
        for s in sw['sensitivity']
        for t in sw['transmission']
    ]
    # ### Tier 4
    + [
        f'{t}_DemHi_100by2035EarlyPhaseout__{s}'
        for s in sw['sensitivity']
        for t in sw['transmission']
    ]
    ### Tier 5
    + [
        f'{t}_DemLo_CurrentPol__{s}'
        for s in sw['sensitivity']
        for t in sw['transmission']
    ]
    + [
        f'{t}_DemHi_90by2035EarlyPhaseout__{s}'
        for s in sw['sensitivity']
        for t in sw['transmission']
    ]
    + [
        f'{t}_DemLo_CurrentPolEarlyPhaseout__{s}'
        for s in sw['sensitivity']
        for t in sw['transmission']
    ]
)

#%% Create the cases dataframe
dfcases = pd.concat({
    **{'Default Value':defaults},
    **{case: make_case(case, defaults, sw) for case in cases},
}, axis=1)

#%% Any special-case adjustments
dfcases.loc[
    'GSw_EFS1_AllYearLoad',
    [c for c in dfcases if (('DemandClip80' in c) and ('Current' in c))]
] = 'EERbaseClip80'

#%% Drop duplicates and take a look
dfcases = dfcases.T.drop_duplicates().T
print(dfcases.shape[1]-1,'cases')
# display(dfcases)

#%% Write it
dfcases.to_csv(os.path.join(reeds_path,'cases_NTPS_all.csv'))
