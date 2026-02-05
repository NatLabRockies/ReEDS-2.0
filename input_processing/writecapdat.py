"""
The purpose of this script is to gather individual generator data from the
NEMS generator database and organize this data into various categories, such as:
    - Non-RSC Existing Capacity
    - Non-RSC Prescribed Capacity
    - RSC Existing Capacity
    - RSC Prescribed Capacity
    - SMR Existing Capacity
    - Retirement Data
        - Generator Retirements
        - Wind Retirements
        - Non-RSC Retirements
    - Hydro Capacity Adjustment Factors - ccseasons
    - Waterconstraint Indexing
    - Canadian Imports
The categorized datasets are then written out to various csv files for use
throughout the ReEDS model.

Some notes on the NEMS database:
* Capacity is assumed to retire at the BEGINNING of 'RetireYear'. So if a row's
  'RetireYear' is 2015, that capacity is assumed to retire at 2014-12-31T23:59:59.
"""

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import argparse
import datetime
import numpy as np
import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


#%%#################
### FIXED INPUTS ###

# Generator database column selections:
Sw_onlineyearcol = 'StartYear'


#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================
def create_rsc_wsc(gendb,TECH,scalars,startyear):

    rsc_wsc = gendb.loc[(gendb['tech'].isin(TECH['rsc_wsc'])) &
                        (gendb[Sw_onlineyearcol] < startyear) &
                        (gendb['RetireYear']     > startyear)
                        ]
    
    rsc_wsc = rsc_wsc[['r','tech','summer_power_capacity_MW']].rename(columns={'tech':'i','summer_power_capacity_MW':'value'})
    # Multiply all PV capacities by ILR
    for j,row in rsc_wsc.iterrows():
        if row['i'] == 'upv':
            rsc_wsc.loc[j,'value'] *= scalars['ilr_utility']

    return rsc_wsc

#%% ===========================================================================
### --- SUPPLEMENTAL DATA ---
### ===========================================================================

#########################
### STATIC DICTIONARY ###
'''
This dictionary must be placed at the module level of this script to be used with the 
create_rsc_wsc() function in aggregate_regions
'''

TECH = {
    'capnonrsc': [
        'coaloldscr', 'coalolduns', 'biopower', 'coal-igcc',
        'coal-new', 'gas-cc', 'gas-ct', 'lfill-gas',
        'nuclear', 'o-g-s', 'battery_li', 'pumped-hydro'
    ],
    'capnonrsc_energy': [
        'battery_li'
    ],
    'prescribed_nonRSC': [
        'coal-new', 'lfill-gas', 'gas-ct', 'o-g-s', 'gas-cc', 
        'hydED', 'hydEND', 'hydND', 'hydNPND', 'hydUD', 'hydUND',
        'geothermal', 'biopower', 'coal-igcc', 'nuclear',
        'battery_li','pumped-hydro','coaloldscr',
    ],
    'prescribed_nonRSC_energy': [
        'battery_li',
    ],
    'storage'  : ['battery_li', 'pumped-hydro'
    ],
    'rsc_all': ['upv','pvb','csp-ns'],
    'rsc_csp': ['csp-ns'],
    'rsc_wsc': ['upv','pvb','csp-ns','csp-ws','wind-ons','wind-ofs',
                'geohydro_allkm','egs_allkm'],
    'prsc_all': ['upv','pvb','csp-ns','csp-ws'],
    'prsc_upv': ['upv','pvb'],
    'prsc_w': ['wind-ons','wind-ofs'],
    'prsc_csp': ['csp-ns','csp-ws'],
    'prsc_geo': ['geohydro_allkm','egs_allkm'],
    'retirements': [
        'coalolduns', 'o-g-s', 'hydED', 'hydEND', 'gas-ct', 'lfill-gas',
        'coaloldscr', 'biopower', 'gas-cc', 'coal-new',
        'battery_li','nuclear', 'pumped-hydro', 'coal-igcc',
    ],
    'retirements_energy': [
        'battery_li'
    ],
    'windret': ['wind-ons'],
    'georet': ['geohydro_allkm','egs_allkm'],
    # This is not all technologies that do not having cooling, but technologies
    # that are (or could be) in the plant database.
    'no_cooling': [
        'upv', 'pvb', 'gas-ct', 'geohydro_allkm','egs_allkm',
        'battery_li', 'pumped-hydro', 'pumped-hydro-flex', 
        'hydUD', 'hydUND', 'hydD', 'hydND', 'hydSD', 'hydSND', 'hydNPD',
        'hydNPND', 'hydED', 'hydEND', 'wind-ons', 'wind-ofs', 'caes',
    ],
}


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================

def main(reeds_path, inputs_case, agglevel, regions):
    
    # #%% Settings for testing
    #reeds_path = "/Users/apham/Documents/GitHub/ReEDS/ReEDS-2.0/"
    #inputs_case = os.path.join(reeds_path,'runs','test_newNEMS_OR_water','inputs_case')


    #########################
    ### SUPPLEMENTAL DATA ###
    
    quartershorten = {'spring':'spri','summer':'summ','fall':'fall','winter':'wint'}

    hotcold_months = {'NOV':'cold', 'DEC':'cold', 'JAN':'cold', 'FEB':'cold', 
                    'JUN':'hot',  'JUL':'hot',  'AUG':'hot'
                    }
    
    #%% Inputs from switches
    sw = reeds.io.get_switches(inputs_case)
    retscen = sw.retscen
    GSw_WaterMain = int(sw.GSw_WaterMain)
    GSw_PVB = int(sw.GSw_PVB)
    startyear = int(sw.startyear)
    endyear = int(sw.endyear)

    scalars = reeds.io.get_scalars(inputs_case)

    years = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv')
    ).columns.astype(int).values.tolist()

    ####################
    ### DICTIONARIES ###

    COLNAMES = {
        'capnonrsc': (
            ['tech','coolingwatertech','r','ctt','wst','summer_power_capacity_MW'],
            ['i','coolingwatertech','r','ctt','wst','value']
        ),
        'capnonrsc_energy': (
            ['tech','r','energy_capacity_MWh'],
            ['i','r','value']
        ),
        'prescribed_nonRSC': (
            [Sw_onlineyearcol,'r','tech','coolingwatertech','ctt','wst','summer_power_capacity_MW'],
            ['t','r','i','coolingwatertech','ctt','wst','value']
        ),
        'prescribed_nonRSC_energy': (
            [Sw_onlineyearcol,'r','tech','coolingwatertech','ctt','wst','energy_capacity_MWh'],
            ['t','r','i','coolingwatertech','ctt','wst','value']
        ),
        'rsc': (
            ['tech','r','ctt','wst','summer_power_capacity_MW'],
            ['i','r','ctt','wst','value']
        ),
        'rsc_wsc': (
            ['r','tech','summer_power_capacity_MW'],
            ['r','i','value']
        ),
        'prsc_upv': (
            [Sw_onlineyearcol,'r','tech','summer_power_capacity_MW'],
            ['t','r','i','value']
        ),
        'prsc_w': (
            [Sw_onlineyearcol,'r','tech','summer_power_capacity_MW'],
            ['t','r','i','value']
        ),
        'prsc_csp': (
            [Sw_onlineyearcol,'r','tech','ctt','wst','summer_power_capacity_MW'],
            ['t','r','i','ctt','wst','value']
        ),
        'prsc_geo': (
            [Sw_onlineyearcol,'r','tech','summer_power_capacity_MW'],
            ['t','r','i','value']
        ),        
        'retirements': (
            [retscen,'r','tech','coolingwatertech','ctt','wst','summer_power_capacity_MW'],
            ['t','r','i','coolingwatertech','ctt','wst','value']
        ),
        'retirements_energy': (
            [retscen,'r','tech','energy_capacity_MWh'],
            ['t','r','i','value']
        ),        
        'windret': (
            ['r','tech','RetireYear','summer_power_capacity_MW'],
            ['r','i','t','value']
        ),
        'georet': (
            ['r','tech','RetireYear','summer_power_capacity_MW'],
            ['r','i','t','value']
        ),
    }


    #%%
    print('Importing generator database:')
    gdb_use = pd.read_csv(os.path.join(inputs_case,'unitdata.csv'),
                        low_memory=False)

    
    rcol_dict = {'county':'FIPS', 'ba':'reeds_ba'}
    # Create the 'r_col' column
    if agglevel in ['county','ba']:
        r_col = rcol_dict[agglevel]        
        gdb_use['r'] = gdb_use[r_col].copy()
        # Filter generator database to regions that match the spatial resolution of the run
        gdb_use = gdb_use[gdb_use['r'].isin(regions)]
    elif agglevel == 'aggreg':
        rb_aggreg = pd.read_csv(os.path.join(inputs_case,'rb_aggreg.csv'), index_col='ba').squeeze(1)
        gdb_use = gdb_use.assign(r=gdb_use.reeds_ba.map(rb_aggreg))
        # Filter generator database to regions that match the spatial resolution of the run
        gdb_use = gdb_use[gdb_use['r'].isin(regions)]

    # If PVB is turned off, consider all PVB as UPV and battery_li for existing and prescribed builds 
    # If PVB is turned on, consider all PVB as 'pvb'
    if GSw_PVB == 0:
        gdb_use['tech'] = gdb_use['tech'].replace('pvb_battery','battery_li')
        gdb_use['tech'] = gdb_use['tech'].replace('pvb_pv','upv')
    else:
        gdb_use['tech'] = gdb_use['tech'].replace('pvb_battery','pvb')
        gdb_use['tech'] = gdb_use['tech'].replace('pvb_pv','pvb')


    # Consider all DUPV as UPV for existing and prescribed builds.
    gdb_use['tech'] = gdb_use['tech'].replace('dupv','upv')  

    # Change tech category of hydro that will be prescribed to use upgrade tech
    # This is a coarse assumption that all recent new hydro is upgrades
    # Existing hydro techs (hydED/hydEND) specifically refer to hydro that exists in startyear
    # Future work could incorporate this change into unit database creation and possibly
    #    use data from ORNL HydroSource to assign a more accurate hydro category.
    gdb_use.loc[
        (gdb_use['tech']=='hydEND') & (gdb_use[Sw_onlineyearcol] >= startyear), 'tech'
    ] = 'hydUND'
    gdb_use.loc[
        (gdb_use['tech']=='hydED') & (gdb_use[Sw_onlineyearcol] >= startyear), 'tech'
    ] = 'hydUD'

    # We model csp-ns (CSP No Storage) as upv throughout ReEDS, but switch it back for reporting.
    # So save the csp-ns capacity separately, then rename it.
    csp_units = (
        gdb_use.loc[(gdb_use['tech']=='csp-ns') & (gdb_use['RetireYear'] > startyear)]
        .groupby(['r','StartYear','RetireYear']).summer_power_capacity_MW.sum()
        .reset_index()
    )
    if len(csp_units):
        cap_cspns = (
            pd.concat(
                {i: pd.Series(
                    [row.summer_power_capacity_MW]*(row.RetireYear - row.StartYear + 2),
                    index=range(row.StartYear, row.RetireYear + 2)
                ) for (i,row) in csp_units.iterrows()},
                axis=1)
            .rename(columns=csp_units['r']).fillna(0)
            .groupby(axis=1, level=0).sum()
            .stack().replace(0,np.nan).dropna()
            .rename_axis(['t','*r']).reorder_levels(['*r','t']).rename('MWac')
        )
        cap_cspns = (
            cap_cspns.loc[cap_cspns.index.get_level_values('t') >= startyear].copy())
    else:
        cap_cspns = pd.DataFrame(columns=['*r','t','MWac']).set_index(['*r','t'])
    # csp-ns capacity is MWac measured at the power block, while PV capacity is MWdc,
    # so multiply csp-ns capacity by the ILR [MWdc/MWac] of PV
    gdb_use.loc[gdb_use['tech']=='csp-ns','summer_power_capacity_MW'] *= scalars['ilr_utility']
    # Rename csp-ns to upv
    gdb_use.loc[gdb_use['tech']=='csp-ns','coolingwatertech'] = (
        gdb_use.loc[gdb_use['tech']=='csp-ns','coolingwatertech']
        .map(lambda x: x.replace('csp-ns','upv'))
    )
    gdb_use.loc[gdb_use['tech']=='csp-ns','tech'] = 'upv'

    # If using cooling water, set the coolingwatertech of technologies with no
    # cooling to be the same as the tech
    if GSw_WaterMain == 1:
        gdb_use.loc[gdb_use['tech'].isin(TECH['no_cooling']),
                    'coolingwatertech'] = gdb_use.loc[gdb_use['tech'].isin(TECH['no_cooling']),
                                                    'tech']

    #%%##################################
    #    -- All Existing Capacity --    #
    #####################################

    ### Used as the starting point for intra-zone network reinforcement costs
    #   Power capacity in MW
    poi_cap_init = gdb_use.loc[(gdb_use[Sw_onlineyearcol] < startyear) &
                            (gdb_use['RetireYear'] > startyear) 
    ].groupby('r').summer_power_capacity_MW.sum().rename('MW').round(3)
    poi_cap_init.index = poi_cap_init.index.rename('*r')

    #%%######################################
    #    -- non-RSC Existing Capacity --    #
    #########################################

    print('Gathering non-RSC Existing Capacity...')
    capnonrsc = gdb_use.loc[(gdb_use['tech'].isin(TECH['capnonrsc'])) &
                            (gdb_use[Sw_onlineyearcol] < startyear) &
                            (gdb_use['RetireYear']     > startyear)
                            ]
    capnonrsc = capnonrsc[COLNAMES['capnonrsc'][0]]
    capnonrsc.columns = COLNAMES['capnonrsc'][1]
    capnonrsc = capnonrsc.groupby(COLNAMES['capnonrsc'][1][:-1]).sum().reset_index()

    capnonrsc_energy = gdb_use.loc[(gdb_use['tech'].isin(TECH['capnonrsc_energy'])) &
                                    (gdb_use[Sw_onlineyearcol] < startyear) &
                                    (gdb_use['RetireYear']     > startyear)
                                    ]
    capnonrsc_energy = capnonrsc_energy[COLNAMES['capnonrsc_energy'][0]]
    capnonrsc_energy.columns = COLNAMES['capnonrsc_energy'][1]
    capnonrsc_energy = capnonrsc_energy.groupby(COLNAMES['capnonrsc_energy'][1][:-1]).sum().reset_index()


    #%%########################################
    #    -- non-RSC Prescribed Capacity --    #
    ###########################################

    print('Gathering non-RSC Prescribed Capacity...')
    ### prescribed power capacity
    prescribed_nonRSC = gdb_use.loc[(gdb_use['tech'].isin(TECH['prescribed_nonRSC'])) &
                                    (gdb_use[Sw_onlineyearcol] >= startyear)
                                    ]
    prescribed_nonRSC = prescribed_nonRSC[COLNAMES['prescribed_nonRSC'][0]]
    prescribed_nonRSC.columns = COLNAMES['prescribed_nonRSC'][1]
    # Remove ctt and wst data from storage, set coolingwatertech to tech type ('i')
    for j, row in prescribed_nonRSC.iterrows():
        if row['i'] in TECH['storage']:
            prescribed_nonRSC.loc[j,['ctt','wst','coolingwatertech']] = ['n','n',row['i']]


    if int(sw.GSw_NuclearDemo)==1:
        # Load in demo data and stack it on prescribed non-RSC 
        demo = pd.read_csv(
            os.path.join(inputs_case,'demonstration_plants.csv')).drop("notes", axis=1)
        # Filter demonstration plants to regions in function call
        demo = demo[demo['r'].isin(regions)]
        prescribed_nonRSC = pd.concat([prescribed_nonRSC,demo],sort=False)

    prescribed_nonRSC = (
        prescribed_nonRSC.groupby(COLNAMES['prescribed_nonRSC'][1][:-1]).sum().reset_index())
    
    ### prescribed energy capacity
    prescribed_nonRSC_energy = gdb_use.loc[(gdb_use['tech'].isin(TECH['prescribed_nonRSC_energy'])) &
                                    (gdb_use[Sw_onlineyearcol] >= startyear)
                                    ]
    prescribed_nonRSC_energy = prescribed_nonRSC_energy[COLNAMES['prescribed_nonRSC_energy'][0]]
    prescribed_nonRSC_energy.columns = COLNAMES['prescribed_nonRSC_energy'][1]
    # Remove ctt and wst data from storage, set coolingwatertech to tech type ('i')
    for j, row in prescribed_nonRSC_energy.iterrows():
        if row['i'] in TECH['storage']:
            prescribed_nonRSC_energy.loc[j,['ctt','wst','coolingwatertech']] = ['n','n',row['i']]

    prescribed_nonRSC_energy = (
        prescribed_nonRSC_energy.groupby(COLNAMES['prescribed_nonRSC_energy'][1][:-1]).sum().reset_index())

    #%%##################################
    #    -- RSC Existing Capacity --    #
    #####################################
    '''
    The following are RSC tech that are treated differently in the model
    '''
    print('Gathering RSC Existing Capacity...')
    # DUPV and UPV values are collected at the same time here:
    caprsc = gdb_use.loc[(gdb_use['tech'].isin(TECH['rsc_all'][:2])) &
                        (gdb_use[Sw_onlineyearcol] < startyear)  &
                        (gdb_use['RetireYear']     > startyear)
                        ]
    caprsc = caprsc[COLNAMES['rsc'][0]]
    caprsc.columns = COLNAMES['rsc'][1]
    caprsc = caprsc.groupby(COLNAMES['rsc'][1][:-2]).value.sum().reset_index()
    # Multiply all PV capacities by ILR
    caprsc['value'] = caprsc['value'] * scalars['ilr_utility']

    # Add existing CSP builds:
    #   Note: Since CSP data is affected by GSw_WaterMain, it must be dealt with
    #       separate from the other RSC tech (UPV, DUPV, wind, etc)
    csp = gdb_use.loc[(gdb_use['tech'].isin(TECH['rsc_csp']))    &
                    (gdb_use[Sw_onlineyearcol] < startyear) &
                    (gdb_use['RetireYear']     > startyear)
                    ]
    csp = csp[COLNAMES['rsc'][0]]
    csp.columns = COLNAMES['rsc'][1]
    csp = csp.groupby(COLNAMES['rsc'][1][:-1]).sum().reset_index()
    if GSw_WaterMain == 1:
        csp['i'] = csp['i'] + '_' + csp['ctt'] + '_' + csp['wst']
    csp.drop('wst', axis=1, inplace=True)

    # Add existing hydro builds:
    gendb = gdb_use[["tech", 'r', "summer_power_capacity_MW"]]
    gendb = gendb[(gendb.tech == 'hydED') | (gendb.tech == 'hydEND')]

    hyd = gendb.groupby(['tech', 'r']).sum() \
            .reset_index() \
            .rename({"tech":"i","summer_power_capacity_MW":"value"}, axis=1)

    hyd['ctt'] = 'n'

    # Concat all RSC Existing Data to one dataframe:
    caprsc = pd.concat([caprsc, csp, hyd])

    # Export Existing RSC data specifically used in writesupplycurves.py
    rsc_wsc = create_rsc_wsc(gdb_use, TECH=TECH, scalars=scalars,startyear=startyear)

    # Create geoexist.csv and copy to inputs_case
    geoexist = gdb_use.loc[(gdb_use['tech'].isin(['geohydro_allkm','egs_allkm'])) &
                       (gdb_use[Sw_onlineyearcol] < startyear) &
                       (gdb_use['RetireYear']     > startyear)
                       ]
    geoexist = (geoexist[['tech','r','summer_power_capacity_MW']]
                .rename(columns={'tech':'*i','summer_power_capacity_MW':'MW'})
                )
    geoexist = geoexist.groupby(['*i','r']).sum().reset_index()
    # Rename generic geothermal tech category to geohydro_allkm_1
    geoexist['*i'] = 'geohydro_allkm_1'


    #%%####################################
    #    -- RSC Prescribed Capacity --    #
    #######################################

    print('Gathering RSC Prescribed Capacity...')
    # DUPV and UPV values are collected at the same time here:
    pupv = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_upv'])) &
                    (gdb_use[Sw_onlineyearcol] >= startyear)
                    ]
    pupv = pupv[COLNAMES['prsc_upv'][0]]
    pupv.columns = COLNAMES['prsc_upv'][1]
    pupv = pupv.groupby(['t','r','i']).sum().reset_index()
    # Multiply all PV capacities by ILR
    pupv['value'] = pupv['value'] * scalars['ilr_utility']

    # Load in wind builds:
    pwind = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_w'])) &
                        (gdb_use[Sw_onlineyearcol] >= startyear)
                        ]
    pwind = pwind[COLNAMES['prsc_w'][0]]
    pwind.columns = COLNAMES['prsc_w'][1]

    pwind = pwind.groupby(['t','r','i']).sum().reset_index()
    pwind.sort_values(['t','r'], inplace=True)

    # Add prescribed csp builds:
    #   Note: Since csp is affected by GSw_WaterMain, it must be dealt with separate
    #         from the other RSC tech (dupv, upv, wind, etc)
    pcsp = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_csp'])) &
                    (gdb_use[Sw_onlineyearcol] >= startyear)
                    ]
    pcsp = pcsp[COLNAMES['prsc_csp'][0]]
    pcsp.columns = COLNAMES['prsc_csp'][1]
    if GSw_WaterMain == 1:
        pcsp['i'] = np.where(pcsp['i']=='csp-ws',pcsp['i']+'_'+pcsp['ctt']+'_'+pcsp['wst'],'csp-ws')

    # Load in geo builds:
    pgeo = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_geo'])) &
                        (gdb_use[Sw_onlineyearcol] >= startyear)
                        ]
    pgeo = pgeo[COLNAMES['prsc_geo'][0]]
    pgeo.columns = COLNAMES['prsc_geo'][1]

    pgeo = pgeo.groupby(['t','r','i']).sum().reset_index()
    pgeo.sort_values(['t','r'], inplace=True)

    # Concat all RSC Existing Data to one dataframe:
    prescribed_rsc = pd.concat([pupv,pwind,pcsp,pgeo],sort=False)

    #%%----------------------------------------------------------------------------
    ################################
    # -- SMR Existing Capacity --  #
    ################################
    print('Gathering SMR Existing Capacity...')
    # Grab the first year for smr because that is when new capacity can begin to be built (for 
    # smr, smr_ccs and electrolyzers)
    firstyear = pd.read_csv(
        os.path.join(inputs_case,'firstyear.csv'),
    ).rename(columns={'*i':'i'}).set_index('i').squeeze(1)
    h2_prod_first_year = firstyear['smr']
    # Get exogenous H2 demand
    h2_exogenous_demand = (
        pd.read_csv(os.path.join(inputs_case,'h2_exogenous_demand.csv'))
        .rename(columns={f'{sw.GSw_H2_Demand_Case}':'million_tons'},)
        .drop(['*p'], axis=1).set_index('t').squeeze(1)
    )
    ### Get BA share of national H2 demand
    h2_ba_share = pd.read_csv(
        os.path.join(inputs_case,'h2_ba_share.csv'))
    # Filter to regions in function call
    h2_ba_share = h2_ba_share[h2_ba_share['*r'].isin(regions)]
    h2_ba_share = h2_ba_share.rename(columns={'*r':'r'}).pivot(index='t', columns='r', values='fraction')
    ## h2_ba_share is only populated for 2021 and 2050, so need to fill the empty data
    h2_ba_share = h2_ba_share.reindex(sorted(set(years+[2021,2050])))
    ## If a region has no data for 2021, it's zero (GAMS convention)
    h2_ba_share.loc[2021] = h2_ba_share.loc[2021].fillna(0)
    ## Backfill before 2021
    h2_ba_share.loc[:2021] = h2_ba_share.loc[:2021].fillna(method='bfill')
    ## Interpolate between 2021-2050
    h2_ba_share.loc[2021:] = h2_ba_share.loc[2021:].interpolate('index')
    ## Only keep the modeled years
    h2_ba_share = h2_ba_share.loc[years].copy()
    ## Reshape from wide to long format
    h2_ba_share_out = h2_ba_share.reset_index().melt(id_vars='t', var_name='*r', value_name='fraction')[['*r','t','fraction']]

    # Calculating the consumption characteristics (has columns i, t, parameter, value)
    consume_char0 = pd.read_csv(
        os.path.join(inputs_case,'consume_char.csv')).rename(columns={'*i':'i'})
    consume_char0['i'] = consume_char0['i'].str.lower()
    consume_char0 = consume_char0.set_index(['i','t','parameter']).value

    outage_forced_static = pd.read_csv(os.path.join(inputs_case,'outage_forced_static.csv'),
                                header=None, index_col=0,
    ).squeeze(1)

    smr_init_ele_efficiency = consume_char0['smr',startyear,'ele_efficiency']
    smr_outage_forced = outage_forced_static['smr']
    h2_demand_initial = h2_exogenous_demand[h2_prod_first_year]

    # Now make some calculations to get the existing SMR capacity
    # Hydrogen demand per r,t (million metric tons) * (10^9 kg/million metric ton) * (kWh/kg)
    # / 8760 to convert kWh --> kW  / (10^3 kW/MW) / outage rate
    # * to make a tiny adjustment upwards to avoid infeasibilities
    h2_existing_smr_cap = (
        h2_ba_share.stack('r').reorder_levels(['r','t']).rename('fraction').reset_index())
    # If this was multiplied by the H2 demand per year, then we would be forcing
    # existing SMR to meet exogenous H2 demand forever and we don't want that.
    # Only for it to meet 2023 demand
    h2_existing_smr_cap['million_tons'] = h2_existing_smr_cap['fraction'] * h2_demand_initial
    h2_existing_smr_cap['value'] =  (
        h2_existing_smr_cap['million_tons'] * 1e9 * smr_init_ele_efficiency
        / 8760 / 1000 / (1 - smr_outage_forced) * 1.0001)
    # Make any value after h2_prod_first_year to be the same MW value as h2_prod_first_year
    # (aka we will not force model to build more SMR capacity in 2030 once it has already
    # met h2 demand in 2024). aka if model year is 2024, then from 2024-2050, the data
    # will be the same df with columns t, r, fraction, million metric tons,
    # value for 134 different BAs in h2_prod_first_year
    # (but only do this if endyear > h2_prod_first_year, otherwise it will introduce NaNs)
    if endyear > h2_prod_first_year:
        h2_prod_first_year_df = h2_existing_smr_cap[
            h2_existing_smr_cap['t']==h2_prod_first_year
        ].drop(['t'], axis=1)
        # For any years after h2_prod_first_year
        after_h2_prod_first_year_df = h2_existing_smr_cap[
            h2_existing_smr_cap['t'] > h2_prod_first_year
        ].drop(['fraction','million_tons','value'], axis=1)
        # New df from 2025 --> 2050 
        after_h2_prod_first_year_df = pd.merge(
            h2_prod_first_year_df,
            after_h2_prod_first_year_df,
            how='left', on=['r'],
        )
        # Concat 2010-2024 df and 2025-->end of model
        h2_existing_smr_cap = pd.concat([
            h2_existing_smr_cap[h2_existing_smr_cap['t']<=h2_prod_first_year],
            after_h2_prod_first_year_df
        ])
    # Filter down to modeled regions and years (otherwise b_inputs will throw an error)
    h2_existing_smr_cap = (h2_existing_smr_cap
        .rename(columns={'r':'*r'})
        .sort_values(by=['t','*r'])
    )


    #%%----------------------------------------------------------------------------
    ################################
    #    -- Retirements Data --    #
    ################################
    print('Gathering Retirement Data...')
    rets = gdb_use.loc[(gdb_use['tech'].isin(TECH['retirements'])) &
                    (gdb_use[retscen]>startyear)
                    ]
    rets = rets[COLNAMES['retirements'][0]]
    rets.columns = COLNAMES['retirements'][1]
    rets.sort_values(by=COLNAMES['retirements'][1],inplace=True)
    rets = rets.groupby(COLNAMES['retirements'][1][:-1]).sum().reset_index()

    rets_energy = gdb_use.loc[(gdb_use['tech'].isin(TECH['retirements_energy'])) &
                    (gdb_use[retscen]>startyear)
                    ]
    rets_energy = rets_energy[COLNAMES['retirements_energy'][0]]
    rets_energy.columns = COLNAMES['retirements_energy'][1]
    rets_energy.sort_values(by=COLNAMES['retirements_energy'][1],inplace=True)
    rets_energy = rets_energy.groupby(COLNAMES['retirements_energy'][1][:-1]).sum().reset_index()

    ################################
    #    -- Wind Retirements --    #
    ################################
    print('Gathering Wind Retirement Data...')
    wind_rets = gdb_use.loc[(gdb_use['tech'].isin(TECH['windret'])) &
                            (gdb_use[Sw_onlineyearcol] <= startyear) &
                            (gdb_use['RetireYear']     >  startyear) &
                            (gdb_use['RetireYear']     <  startyear + 30)
                            ]
    wind_rets = wind_rets[COLNAMES['windret'][0]]
    wind_rets.columns = COLNAMES['windret'][1]
    wind_rets['v'] = 'init-1'
    wind_rets = wind_rets.groupby(['i','v','r','t']).sum().reset_index()

    wind_rets = (wind_rets.pivot_table(index = ['i','v','r'], columns = 't', values='value')
                        .reset_index()
                        .fillna(0)
                )
    #================================
    #   --- Geothermal Retirements ---
    #================================
    print('Gathering Geothermal Retirement Data...')
    geo_retirements = gdb_use.loc[(gdb_use['tech'].isin(TECH['georet'])) &
                    (gdb_use[Sw_onlineyearcol] <= startyear) &
                    (gdb_use['RetireYear']     >  startyear) &
                    (gdb_use['RetireYear']     <  startyear + 30)
                    ]
    geo_retirements = geo_retirements[COLNAMES['georet'][0]]
    geo_retirements.columns = COLNAMES['georet'][1]
    geo_retirements['v'] = 'init-1'
    geo_retirements = geo_retirements.groupby(['i','v','r','t']).sum().reset_index()

    geo_retirements = (geo_retirements
            .pivot_table(index = ['i','v','r'], columns = 't', values='value')
            .reset_index()
            .fillna(0)
            )


    #%%----------------------------------------------------------------------------
    #############################################################
    #    -- Hydro Capacity Adjustment Factors: CC-Seasaon --    #
    #############################################################

    # Initialize with monthly hydropower capacity adjustment factor values
    hydcapadj_ccszn = pd.read_csv(os.path.join(inputs_case,'hydcapadj.csv'))
    #Filter to regions in function call
    hydcapadj_ccszn = hydcapadj_ccszn[hydcapadj_ccszn['r'].isin(regions)]
    # Map hot/cold values to ccseason months and filter for ccseason data
    hydcapadj_ccszn['ccseason'] = hydcapadj_ccszn['month'].map(hotcold_months)
    hydcapadj_ccszn = (hydcapadj_ccszn[hydcapadj_ccszn['ccseason'].isin(['cold','hot'])]
                    .drop(columns='month'))
    # Average monthly data to get factor values by ccseason
    hydcapadj_ccszn = hydcapadj_ccszn.groupby(['*i','r','ccseason']).mean().reset_index()
    hydcapadj_ccszn['value'] = hydcapadj_ccszn['value'].round(5)


    #%%----------------------------------------------------------------------------
    ########################################
    #    -- Waterconstraint Indexing --    #
    ########################################

    rets['i'] = rets['i'].str.lower()
    rets_energy['i'] = rets_energy['i'].str.lower()
    prescribed_nonRSC['i'] = prescribed_nonRSC['i'].str.lower()
    prescribed_nonRSC_energy['i'] = prescribed_nonRSC_energy['i'].str.lower()

    # When water constraints are enabled, retirements are also indexed by cooling technology
    # and cooling water source. otherwise, they only have the indices of year, region, and tech
    if GSw_WaterMain == 1:
        ### Group by all cols except 'value'
        rets = rets.groupby(COLNAMES['retirements'][1][:-1]).sum().reset_index()
        rets.columns = COLNAMES['retirements'][1]

        capnonrsc = capnonrsc.groupby(COLNAMES['capnonrsc'][1][:-1]).sum().reset_index()
        capnonrsc.columns = COLNAMES['capnonrsc'][1]

        prescribed_nonRSC = (
            prescribed_nonRSC
            .groupby(COLNAMES['prescribed_nonRSC'][1][:-1]).sum().reset_index())
        prescribed_nonRSC.columns = COLNAMES['prescribed_nonRSC'][1]

        prescribed_nonRSC_energy = (
            prescribed_nonRSC_energy
            .groupby(COLNAMES['prescribed_nonRSC_energy'][1][:-1]).sum().reset_index())

        rets['i'] = rets['coolingwatertech']
        rets = rets.groupby(['t','r','i']).value.sum().reset_index()
        rets.columns = ['t','r','i','value']

        capnonrsc['i'] = capnonrsc['coolingwatertech']
        capnonrsc = capnonrsc.groupby(['i','r']).value.sum().reset_index()
        capnonrsc.columns = ['i','r','value']

        prescribed_nonRSC['i'] = prescribed_nonRSC['coolingwatertech']
        prescribed_nonRSC = prescribed_nonRSC.groupby(['t','r','i']).value.sum().reset_index()
        prescribed_nonRSC.columns = ['t','r','i','value']

        prescribed_nonRSC_energy['i'] = prescribed_nonRSC_energy['coolingwatertech']
        prescribed_nonRSC_energy = prescribed_nonRSC_energy.groupby(['t','r','i']).value.sum().reset_index()
        prescribed_nonRSC_energy.columns = ['t','r','i','value']
    else:
    # Group by [year, region, tech]
        rets = rets.groupby(['t','r','i']).value.sum().reset_index()
        rets.columns = ['t','r','i','value']

        capnonrsc = capnonrsc.groupby(['i','r']).value.sum().reset_index()
        capnonrsc.columns = ['i','r','value']

        prescribed_nonRSC = prescribed_nonRSC.groupby(['t','r','i']).value.sum().reset_index()
        prescribed_nonRSC.columns = ['t','r','i','value']

        prescribed_nonRSC_energy = prescribed_nonRSC_energy.groupby(['t','r','i']).value.sum().reset_index()
        prescribed_nonRSC_energy.columns = ['t','r','i','value']

    # Final Groupby step for capacity groupings not affected by GSw_WaterMain:
    caprsc = caprsc.groupby(['i','r']).value.sum().reset_index()
    prescribed_rsc = prescribed_rsc.groupby(['t','i','r']).value.sum().reset_index()


    #%%----------------------------------------------------------------------------
    ################################
    #    -- Canadian Imports --    #
    ################################

    can_imports_year_mwh = pd.read_csv(os.path.join(inputs_case,'can_imports.csv'),
                                    index_col='r').dropna()
    # Filter to regions in function call
    can_imports_year_mwh = can_imports_year_mwh[can_imports_year_mwh.index.isin(regions)]
    can_imports_year_mwh.columns = can_imports_year_mwh.columns.astype(int)
    can_imports_year_mwh = can_imports_year_mwh.reindex(years, axis=1).dropna(axis=1)

    ## Get hours per quarter
    year = sw['GSw_HourlyWeatherYears'].split('_')[0]
    timestamps = pd.Series(index=pd.date_range(f'{year}-01-01', periods=8760, freq='H'))

    month2quarter = pd.read_csv(
        os.path.join(inputs_case, 'month2quarter.csv'),
        index_col='month',
    ).squeeze(1)

    quarterhours = timestamps.index.month.map(month2quarter).value_counts()
    quarterhours.index = quarterhours.index.map(lambda x: quartershorten.get(x,x)).rename('szn')

    can_imports_quarter_frac = pd.read_csv(os.path.join(inputs_case,'can_imports_quarter_frac.csv'),
                                    header=0, names=['szn','frac'], index_col='szn'
                                    ).squeeze(1)
    can_imports_capacity = (
        ## Start with annual imports in MWh
        pd.concat({szn: can_imports_year_mwh for szn in quartershorten.values()}, axis=0, names=['szn','r'])
        ## Multiply by season frac to get MWh per season
        .multiply(can_imports_quarter_frac, axis=0, level='szn')
        ## Divide by hours per season to get average MW by season
        .divide(quarterhours, axis=0, level='szn')
        ## Keep the max value across seasons
        .groupby('r', axis=0).max()
        ## Reshape for GAMS
        .stack().rename_axis(['*r','t']).rename('MW').round(3)
    )


    #%%----------------------------------------------------------------------------
    ##############################
    #    -- Data Write-Out --    #
    ##############################

    #Round outputs before writing out
    for df in [rets, rets_energy, capnonrsc, capnonrsc_energy, prescribed_nonRSC, prescribed_nonRSC_energy,
               caprsc, prescribed_rsc, h2_existing_smr_cap]:
        df['value'] = df['value'].round(6)
        # Set all years to integer datatype
        if 't' in df.columns:
            df['t'] = df.t.astype(float).round().astype(int)

    #%% 
    # Return 
    files_out = {'capnonrsc' :  capnonrsc[['i','r','value']],
                'capnonrsc_energy' : capnonrsc_energy[['i','r','value']],
                'rets' :  rets[['t','r','i','value']],
                'rets_energy' : rets_energy[['t','r','i','value']],
                'prescribed_nonRSC' : prescribed_nonRSC[['t','i','r','value']],
                'prescribed_nonRSC_energy' : prescribed_nonRSC_energy[['t','i','r','value']],
                'caprsc' :caprsc[['i','r','value']],
                'prescribed_rsc' : prescribed_rsc[['t','i','r','value']],
                'wind_rets' : wind_rets,
                'h2_existing_smr_cap' : h2_existing_smr_cap[['*r','t','value']],
                'geo_retirements' : geo_retirements,
                'poi_cap_init' : poi_cap_init, 
                'cap_cspns': cap_cspns,
                'rsc_wsc':rsc_wsc,
                'hydcapadj_ccszn' : hydcapadj_ccszn[['*i','ccseason','r','value']],
                'can_imports_capacity' : can_imports_capacity,
                'geoexist' : geoexist,
                'h2_ba_share': h2_ba_share_out
                }

    return files_out 

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == '__main__':
    ### Time the operation of this script
    tic = datetime.datetime.now()
    
    ### Parse arguments
    parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")
    parser.add_argument("reeds_path", help="ReEDS directory")
    parser.add_argument("inputs_case", help="path to runs/{case}/inputs_case")

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )
    print('Starting writecapdat.py')


    # Use agglevel_variables function to obtain spatial resolution variables 
    agglevel_variables  = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)

    # For mixed resolution runs the main function of writecapdat needs to be executed separately for each desired resolution 
    # Then the data from each resolution are combined and written to the inputs_case folder 
    if agglevel_variables['lvl'] == 'mult':
        for resolution in agglevel_variables['agglevel']:
            if resolution == 'aggreg':
                aggreg_data  = main(reeds_path, inputs_case, agglevel=resolution, 
                                     regions=agglevel_variables['ba_regions'] )
            if resolution == 'ba':
                ba_data = main(reeds_path, inputs_case, agglevel=resolution, 
                                regions=agglevel_variables['ba_regions'])
            if resolution == 'county':
                county_data = main(reeds_path, inputs_case, agglevel=resolution,
                                     regions=agglevel_variables['county_regions'],)
        
        # Combine and write mixed resolution data
        # ReEDS only supports county-BA, county-aggreg combinations 
        combined_data = {}
        if 'ba' in agglevel_variables['agglevel']:
            for key in ba_data.keys() :
                if county_data[key].empty:
                    combined_data[key] = ba_data[key]
                elif ba_data[key].empty:
                    combined_data[key] = county_data[key]
                else:
                    combined_data[key] = pd.concat([ba_data[key], county_data[key]])

        if 'aggreg' in agglevel_variables['agglevel']:
            for key in aggreg_data.keys() :
                if county_data[key].empty:
                    combined_data[key] = aggreg_data[key]
                elif aggreg_data[key].empty:
                    combined_data[key] = county_data[key]
                else:
                    combined_data[key] = pd.concat([aggreg_data[key], county_data[key]])
        
        data = combined_data

    # Single Resolution Procedure
    else: 
        agglevel = agglevel_variables['agglevel']
        regions = pd.read_csv(os.path.join(inputs_case,f'val_{agglevel}.csv'),header=None).squeeze(1).values
        data = main(reeds_path, inputs_case,agglevel, regions)

    # Write it
    print('Writing out capacity data')
    outname = {
        'rets': 'retirements',
        'rets_energy': 'retirements_energy',
        'wind_rets': 'wind_retirements',
        'hydcapadj_ccszn': 'cap_hyd_ccseason_adj',
    }
    keep_index = {
        'poi_cap_init': True,
        'cap_cspns': True,
        'can_imports_capacity': True,
    }
    for key, df in data.items():
        df.to_csv(
            os.path.join(inputs_case, f'{outname.get(key, key)}.csv'),
            index=keep_index.get(key, False),
        )

    reeds.log.toc(tic=tic, year=0, process='input_processing/writecapdat.py',
        path=os.path.join(inputs_case,'..'))

    print('Finished writecapdat.py')
