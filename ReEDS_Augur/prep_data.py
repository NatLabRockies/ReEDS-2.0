#%% Notes
"""
This script writes inputs for resource adequacy calculations:
* capacity_credit.py (existing and marginal capacity credit)
* run_pras.jl -> ReEDS2PRAS.jl -> PRAS.jl (probabilistic resource adequacy)

The files used by PRAS are:
* In {case}/ReEDS_Augur/augur_data:
    * cap_converter_{year}.csv
    * energy_cap_{year}.csv
    * max_cap_{year}.csv
    * pras_load_{year}.h5
    * pras_vre_gen_{year}.h5
    * tran_cap_{year}.csv
* In {case}/inputs_case:
    * hydcf.csv
    * outage_forced_hourly.h5
    * outage_forced_static.csv
    * resources.csv
    * tech-subset-table.csv
    * unitdata.csv
    * unitsize.csv
"""

#%% General imports
import os
import re
import pandas as pd
import numpy as np
import gdxpds
### Local imports
import reeds


### Functions
def errorcheck_reeds2pras(casedir, csvout, h5out):
    ### In ReEDS2PRAS, two classes of technologies are handled separately:
    ### - Technologies in pras_vre_gen:
    ###   - Capacity is defined as the maximum of the hourly generation profile
    ###   - Capacity is not disaggregated into units and no outages are applied
    ### - Technologies in max_cap:
    ###   - Capacity is taken from max_cap and disaggregated into units
    ###   - Unit outages are applied
    ###   - (except for batteries and dispatchable hydro, which are not disaggregated and
    ###     for which outages are not applied)
    ### So here, to avoid double-counting, make sure the techs in pras_vre_gen and max_cap
    ### do not overlap
    profile_techs = h5out['pras_vre_gen'].columns.map(lambda x: x.split('|')[0]).unique()
    max_cap_techs = csvout['max_cap'].index.get_level_values('i').unique()
    for check in [
        [i for i in profile_techs if i in max_cap_techs],
        [i for i in max_cap_techs if i in profile_techs],
    ]:
        if len(check):
            raise ValueError(f'{check} overlap between pras_vre_gen and max_cap')

    ### ReEDS2PRAS takes the region list from the load data, so make sure all regions
    ### with generation/transmission capacity show up in the load data
    load_regions = h5out['pras_load'].columns
    profile_regions = h5out['pras_vre_gen'].columns.map(lambda x: x.split('|')[1]).unique()
    max_cap_regions = csvout['max_cap'].index.get_level_values('r').unique()
    tran_regions = (
        list(csvout['tran_cap'].index.get_level_values('r').unique())
        + list(csvout['tran_cap'].index.get_level_values('rr').unique())
    )
    energy_regions = csvout['energy_cap'].index.get_level_values('r').unique()
    converter_regions = csvout['cap_converter'].index
    for check in [
        [r for r in profile_regions if r not in load_regions],
        [r for r in max_cap_regions if r not in load_regions],
        [r for r in tran_regions if r not in load_regions],
        [r for r in energy_regions if r not in load_regions],
        [r for r in converter_regions if r not in load_regions],
    ]:
        if len(check):
            raise ValueError(f'{check} are not in pras_load')

    ### Make sure disaggregated techs have unit sizes, forced outage rates, and MTTRs
    unitsize = pd.read_csv(
        os.path.join(casedir, 'inputs_case', 'unitsize.csv'),
        index_col='tech',
    )['MW']
    mttr = pd.read_csv(os.path.join(casedir, 'inputs_case', 'mttr.csv'), index_col='tech')
    outage_forced = reeds.io.get_outage_hourly(casedir, 'forced')
    outage_techs = outage_forced.columns.get_level_values('i').unique()
    ## ReEDS2PRAS does not disaggregate batteries
    battery_techs = reeds.techs.get_tech_subset_table(casedir).loc[['BATTERY']].tolist()
    for check, infile in [
        ([i for i in max_cap_techs if i not in unitsize.index.tolist() + battery_techs], 'unitsize.csv'),
        ([i for i in max_cap_techs if i not in mttr.index], 'mttr.csv'),
        ([i for i in max_cap_techs if i not in outage_techs], 'outage_forced_hourly.h5'),
    ]:
        if len(check):
            raise ValueError(f'{check} are missing from {infile}')


#%%### Procedure
def main(t, casedir, iteration=0):
    #%%### DEBUGGING: Inputs
    # t = 2020
    # reeds_path = os.path.expanduser('~/github2/ReEDS-2.0')
    # casedir = os.path.join(reeds_path,'runs','v20230214_PRMaugurM0_Pacific_d7fIrh4_CC_y2012')

    #%%### Get inputs from ReEDS
    gdx_file = os.path.join(casedir,'ReEDS_Augur','augur_data',f'reeds_data_{t}.gdx')
    gdxreeds = gdxpds.to_dataframes(gdx_file)
    ### Use indices as multiindex
    for key in gdxreeds:
        # try:
        if 'i' in gdxreeds[key]:
            gdxreeds[key].i = gdxreeds[key].i.str.lower()
        if 'ii' in gdxreeds[key]:
            gdxreeds[key].ii = gdxreeds[key].ii.str.lower()
        if 't' in gdxreeds[key]:
            gdxreeds[key].t = gdxreeds[key].t.astype(int)

    #%% Load other inputs from ReEDS
    inputs_case = os.path.join(casedir, 'inputs_case')

    sw = reeds.io.get_switches(casedir)
    sw['t'] = t

    h_dt_szn = pd.read_csv(os.path.join(inputs_case, 'rep', 'h_dt_szn.csv'))
    hmap_allyrs = pd.read_csv(
        os.path.join(inputs_case, 'rep', 'hmap_allyrs.csv'),
        low_memory=False,
    )
    hmap_allyrs['szn'] = h_dt_szn['season'].copy()

    hmap_myr_stress = pd.read_csv(
        os.path.join(inputs_case, f'stress{t}i{iteration}', 'hmap_myr.csv'),
        low_memory=False,
        index_col='*timestamp',
        parse_dates=True,
    ).rename_axis('timestamp')

    h_dt_szn = h_dt_szn.set_index(['year', 'hour'])
    # Add explicit timestamp index
    h_dt_szn['timestamp'] = pd.to_datetime(
        h_dt_szn.index.map(hmap_allyrs.set_index(['year', 'hour'])['*timestamp']))
    h_dt_szn = h_dt_szn.reset_index().set_index('timestamp')

    load = reeds.io.read_file(os.path.join(inputs_case, 'load.h5'), parse_timestamps=True)

    resources = pd.read_csv(os.path.join(inputs_case, 'resources.csv'))
    recf = reeds.io.read_file(os.path.join(inputs_case, 'recf.h5'), parse_timestamps=True)
    recf.columns = pd.MultiIndex.from_tuples([tuple(x.split('|')) for x in recf.columns],
                                             names=('i','r'))

    tech_subset_table = reeds.techs.expand_GAMS_tech_groups(
        reeds.techs.get_tech_subset_table(casedir).reset_index()
    ).set_index('tech_group').i

    techs_vre = tech_subset_table.loc[['VRE', 'CSP', 'PVB']].unique()
    if int(sw.pras_vre_combine):
        ## Group all into a single "vre" tech
        techs_vre_simplify = dict(zip(
            techs_vre,
            ['vre']*len(techs_vre)
        ))
    else:
        ## Strip the resource class but keep resource type;
        ## e.g. "upv_5" -> "upv", "csp2_3" -> "csp"
        techs_vre_simplify = dict(zip(
            techs_vre,
            [re.sub('\d?_\d+$', '', i) for i in techs_vre]
        ))

    try:
        offshore = pd.read_csv(
            os.path.join(casedir, 'inputs_case', 'offshore.csv'),
            header=None,
        ).squeeze(1).tolist()
    except pd.errors.EmptyDataError:
        offshore = []

    #%%### Set up the output containers and a few other inputs
    csvout, h5out = {}, {}

    #%%### Transmission routes, capacity, and losses
    if int(sw.pras_trans_contingency):
        trancap_reeds = gdxreeds['cap_trans_prm']
    else:
        trancap_reeds = gdxreeds['cap_trans_energy']

    #%%### Efficiencies and storage parameters
    duration = gdxreeds['storage_duration'].loc[
        gdxreeds['storage_duration'].i.isin(gdxreeds['storage_standalone'].i)
    ].set_index('i').Value


    #%%### Nameplate capacity
    cap_ivr_realvint = (
        gdxreeds['cap_ivrt'].loc[gdxreeds['cap_ivrt'].t==t].drop('t', axis=1)
        .groupby(['i','v','r'], as_index=False).Value.sum()
    )
    ### Reset the vintages of all storage units to 'new1' to reduce model size
    cap_storage_devint = cap_ivr_realvint.loc[
        cap_ivr_realvint.i.isin(gdxreeds['storage_standalone'].i)].copy()
    cap_storage_devint['v'] = 'new1'
    cap_storage_devint = (
        cap_storage_devint.groupby(['i','v','r'], as_index=False).Value.sum())

    def _devint_storage(dfin):
        dfout = pd.concat([
            dfin.loc[~dfin.i.isin(gdxreeds['storage_standalone'].i)],
            cap_storage_devint
        ], axis=0)
        return dfout

    cap_ivr = _devint_storage(cap_ivr_realvint)

    #%%### Nameplate energy capacity
    cap_energy_ivr = (
        gdxreeds['cap_energy_ivrt'].loc[gdxreeds['cap_energy_ivrt'].t==t].drop('t', axis=1)
        .groupby(['i','v','r'], as_index=False).Value.sum()
    )
    ### Reset the vintages of all storage energy capacity units to 'new1' as well
    cap_energy_ivr_devint = cap_energy_ivr.loc[
        cap_energy_ivr.i.isin(gdxreeds['storage_standalone'].i)].copy()
    cap_energy_ivr_devint['v'] = 'new1'
    cap_energy_ivr_devint = (
        cap_energy_ivr_devint.groupby(['i','v','r'], as_index=False).Value.sum())
    cap_energy_ivr = pd.concat([
        cap_energy_ivr.loc[~cap_energy_ivr.i.isin(gdxreeds['storage_standalone'].i)],
        cap_energy_ivr_devint
    ], axis=0)

    #%% Remove VRE and demand-modifying techs (H2 production, DAC, DR)
    demand_techs = tech_subset_table[['CONSUME', 'DR_SHED']].values
    cap_nonloadtechs = cap_ivr.loc[~cap_ivr.i.isin(demand_techs)].copy()

    vretechs_i = resources.i.str.lower().unique()
    cap_vre = (
        cap_ivr.loc[cap_ivr.i.str.lower().isin(vretechs_i)]
        .set_index(['i','v','r']).Value.copy()
    )

    #%%### VRE generation, accounting for generation
    ### Apply CF adjustment to capacity (the resulting df is not meaningful but it's only a step
    ### toward the generation df).
    ### Some RE techs, like CSP, don't have cf_adj_t defined in all years,
    ### so fill missing values with 1, then drop rows with missing region (indicating no capacity)
    cf_adj_iv = (
        gdxreeds['cf_adj_t_filt'].loc[gdxreeds['cf_adj_t_filt'].t==t].drop('t', axis=1)
        .set_index(['i','v']).Value
    )
    cap_vre_derated = cap_vre.multiply(cf_adj_iv, fill_value=1).reset_index().dropna()
    if len(cap_vre) != len(cap_vre_derated):
        raise Exception(
            "CF adjustment didn't work; probably missing values in cf_adj_t_filt. "
            f"len(cap_vre) = {len(cap_vre)}; len(cap_vre_derated) = {(len(cap_vre_derated))}."
        )
    cap_vre_derated = cap_vre_derated.groupby(['i','r']).Value.sum()

    ### Multiply derated capacity by CF to get generation
    gen_vre_ir = recf.multiply(cap_vre_derated, axis=1).dropna(axis=1)
    ### Check for missing data
    if gen_vre_ir.shape[1] != cap_vre_derated.shape[0]:
        missing_in_gen_vre_ir = set(cap_vre_derated.index) - set(gen_vre_ir.columns)
        missing_in_cap_vre_derated = set(gen_vre_ir.columns) - set(cap_vre_derated.index)
        raise Exception(
            f"Mismatch between VRE capacity and available CF data. "
            f"Missing in gen_vre_ir: {missing_in_gen_vre_ir or 'None'}, "
            f"Missing in cap_vre_derated: {missing_in_cap_vre_derated or 'None'}"
        )
    ### Aggregate by model zone
    gen_vre_r = gen_vre_ir.copy()
    gen_vre_r = gen_vre_r.groupby(axis=1, level='r').sum()

    ### Store generation by (i,r) for capacity_credit.py
    gen_vre_resources = gen_vre_ir.reindex(resources[['i','r']], axis=1).fillna(0).clip(lower=0)

    vre_gen_exist = gen_vre_resources.copy()
    vre_gen_exist.columns = ['|'.join(c) for c in vre_gen_exist.columns]
    vre_gen_exist.index = h_dt_szn.set_index(['ccseason','year','h','hour']).index
    h5out['vre_gen_exist'] = vre_gen_exist

    ### Store generation by (i,r) for PRAS, after aggregating i if necessary
    pras_vre_gen = gen_vre_resources.copy()
    pras_vre_gen.columns = pd.MultiIndex.from_arrays([
        pras_vre_gen.columns.get_level_values('i').map(lambda x: techs_vre_simplify.get(x,x)),
        pras_vre_gen.columns.get_level_values('r')
    ])
    pras_vre_gen = pras_vre_gen.groupby(['i','r'], axis=1).sum()

    pras_vre_gen.columns = ['|'.join(c) for c in pras_vre_gen.columns]
    h5out['pras_vre_gen'] = pras_vre_gen


    ###### Store marginal CF by (i,r) for capacity_credit.py
    ## Use the cf_adj_iv for the latest available vintage
    cf_adj_i = cf_adj_iv.reset_index()
    ## Temporarily reformat the vintage so we can select the last one
    def intify(v):
        try:
            return int(v)
        except ValueError:
            return v
    cf_adj_i.v = (
        cf_adj_i.v.str.replace('new','')
        .map(intify)
        .map(lambda x: x if str(x).startswith('init') else f'new{x:>03}')
    )
    cf_adj_i = (
        cf_adj_i.sort_values(['i','v']).drop_duplicates('i', keep='last')
        .set_index('i').Value
        .reindex(recf.columns.get_level_values('i').unique()).fillna(1)
    )

    ### Multiply [CF] * [CF adjustment] to get marginal CF
    vre_cf_marg = (
        recf.multiply(cf_adj_i, level='i', axis=1)
        .reindex(resources[['i','r']], axis=1)
    )
    vre_cf_marg.columns = ['|'.join(c) for c in vre_cf_marg.columns]
    vre_cf_marg.index = h_dt_szn.set_index(['ccseason','year','h','hour']).index
    h5out['vre_cf_marg'] = vre_cf_marg

    h_dt_szn_load_years = h_dt_szn.loc[h_dt_szn.index.isin(load.index.get_level_values('datetime'))]

    #%%### Flexible load
    ### H2 and DAC: Make it all inflexible (necessary for PRAS)
    load_h2dac_all_hourly = (
        gdxreeds['prod_filt']
        .groupby(['r', 'allh']).Value.sum().reset_index()
        .merge(h_dt_szn_load_years[['h']].reset_index(), left_on='allh', right_on='h')
        .pivot(index='timestamp', columns='r', values='Value')
        .fillna(0)
        .reindex(h_dt_szn_load_years.index)
    )

    #%% Load shedding
    ## Get the DR shed load for all weather years
    gen_h_stress = gdxreeds['gen_h_stress_filt']
    gen_shed = gen_h_stress.loc[
        (gen_h_stress['t'] == t)
        & gen_h_stress['i'].isin(tech_subset_table['DR_SHED'].values)
    ].groupby(['r','allh']).Value.sum().unstack('r')
    ## First assign values to all timestamps in GSw_HourlyChunkLengthStress
    gen_shed_combined = gen_shed.reindex(hmap_myr_stress.h.values)
    gen_shed_combined.index = hmap_myr_stress.index
    ## Now fill other hours with zero
    gen_shed_combined = gen_shed_combined.reindex(h_dt_szn.index).fillna(0)

    #%% Flexibly sited load -> pd.Series with index = regions and missing values 0-filled
    ra_cap_loadsite = (
        gdxreeds['ra_cap_loadsite']
        .loc[gdxreeds['ra_cap_loadsite']['t'] == t]
        .drop(columns='t')
        .set_index('r')
        .squeeze(1)
        .reindex(load.columns).fillna(0)
    )

    ra_cap_flatload = (
        gdxreeds['ra_cap_flatload']
        .loc[gdxreeds['ra_cap_flatload']['t'] == t]
        .drop(columns='t')
        .set_index('r')
        .squeeze(1)
        .reindex(load.columns).fillna(0)
    )
    #%%### Total load and net load
    ### Get Candian exports and add to this solve year's load
    can_exports = (
        gdxreeds['can_exports_h_filt']
        .merge(h_dt_szn_load_years[['h']].reset_index(), left_on='allh', right_on='h')
        .pivot(index='timestamp', columns='r', values='Value')
    )
    load_year = load.loc[t].add(can_exports, fill_value=0)

    ### PRAS doesn't yet handle flexible load, so include all H2/DAC load in the
    ### version we write for PRAS
    if int(sw['pras_include_h2dac']):
        print(f'Added H2/DAC to PRAS load since pras_include_h2dac = {sw.pras_include_h2dac}')
        pras_load = load_year.add(load_h2dac_all_hourly, fill_value=0)
    else:
        pras_load = load_year.copy()

    ### Add zeros for offshore zones
    for r in offshore:
        pras_load[r] = 0

    ### Subtract dr-shed load
    if int(sw.GSw_DRShed) and not gen_shed_combined.empty:
        print(f'Subtracted shed load from PRAS load since GSw_DRShed = {sw.GSw_DRShed}')
        pras_load = pras_load.subtract(gen_shed_combined, fill_value=0).clip(lower=0)

    ### Add flexibly sited load if its profile is inflexible (GSw_LoadSiteCF = 1)
    if (
        np.isclose(float(sw.GSw_LoadSiteCF), 1)
        and len(ra_cap_loadsite)
        and int(sw.GSw_LoadSiteRA)
    ):
        print(
            f'Added CAP_LOADSITE to PRAS load since GSw_LoadSiteCF = {sw.GSw_LoadSiteCF} '
            f'and GSw_LoadSiteRA = {sw.GSw_LoadSiteRA}'
        )
        pras_load += ra_cap_loadsite

    # Add flat load cap (old approach for Utah)
    if sw.GSw_FlatLoadAdd and len(ra_cap_flatload):
        print(
            f'Added CAP_FLAT_LOAD to PRAS load since Sw_FlatLoadAdd = {sw.GSw_FlatLoadAdd}'
        )
        pras_load += ra_cap_flatload    
        
    h5out['pras_load'] = pras_load
    ## Include the hourly H2/DAC load for debugging
    h5out['pras_h2dac_load'] = load_h2dac_all_hourly

    ### Store load with the appropriate index for capacity_credit.py
    h5out['load'] = (
        load_year.merge(
            h_dt_szn[['ccseason', 'year', 'h', 'hour']], left_index=True, right_index=True
        )
        .set_index(['ccseason', 'year', 'h', 'hour'])
    )

    #%%### Collect some csv's for ReEDS2PRAS
    ### Transmission capacity: Subset for RA according to GSw_PRMTRADE_level switch
    tran_cap = (
        trancap_reeds.set_index(['r','rr','trtype']).rename(columns={'Value':'MW'}))
    if sw.GSw_PRMTRADE_level != 'country':
        hierarchy = reeds.io.get_hierarchy(casedir)
        if sw.GSw_PRMTRADE_level == 'r':
            rmap = dict(zip(hierarchy.index, hierarchy.index))
        else:
            rmap = hierarchy[sw.GSw_PRMTRADE_level]
        tran_cap['level'] = tran_cap.index.get_level_values('r').map(rmap)
        tran_cap['levell'] = tran_cap.index.get_level_values('rr').map(rmap)
        tran_cap = (
            tran_cap.loc[tran_cap.level==tran_cap.levell]
            .drop(['level','levell'], axis=1)
        )
    csvout['tran_cap'] = tran_cap

    ### Converter capacity: Offshore zones don't need converters since offshore generation
    ## exports are assumed to be in DC, so add converter capacity to each offshore zone
    ## equal to the VSC transmission capacity into / out of the zone.
    ## Transmission capacity is defined in both directions and VSC is the same in both,
    ## so we can just keep offshore transmission in one direction.
    offshore_with_transmission = [
        r for r in offshore if r in tran_cap.index.get_level_values('r').unique()
    ]
    csvout['cap_converter'] = pd.concat([
        gdxreeds['cap_converter_filt'].set_index('r').rename(columns={'Value':'MW'}),
        tran_cap.loc[offshore_with_transmission].groupby('r').sum(),
    ])

    ### Nameplate capacity
    max_cap = cap_nonloadtechs.set_index(['i','v','r']).Value.rename('MW')
    ## Drop VRE since it is handled through pras_vre_gen
    max_cap = max_cap.loc[
        ~max_cap.index.get_level_values('i').str.startswith(
            tuple(
                list(techs_vre_simplify.keys()) + list(techs_vre_simplify.values())
            )
        )
    ].copy()
    ## Aggregate geothermal
    simplify_geo = dict(zip(
        tech_subset_table['GEO'].values,
        ['geothermal']*len(tech_subset_table['GEO'])
    ))
    max_cap = max_cap.rename(index=simplify_geo, level='i').groupby(['i','v','r']).sum()

    ## Storage energy capacity [MWh] = power capacity [MW] * duration [h]
    energy_cap = (
        cap_storage_devint
        .set_index(['i','v','r']).Value
        .multiply(duration)
        .rename('MWh')
    )
    ## Append batteries energy capacity
    energy_cap = pd.concat([
        energy_cap,
        cap_energy_ivr.set_index(['i','v','r'])['Value'].rename('MWh')
    ])
    energy_cap = energy_cap.round(2)
    energy_cap = energy_cap[energy_cap > 0]

    # Add to max_cap any index in energy_cap that's missing, setting them to 0
    missing_index = energy_cap.index.difference(max_cap.index)
    max_cap = pd.concat([max_cap, pd.Series(0, index=missing_index, name=max_cap.name)])

    ## Drop storage with energy or power capacity below the PRAS cutoff
    too_small_storage = list(set(
        energy_cap.loc[energy_cap < sw['storcap_cutoff']].index.tolist()
        + max_cap.loc[energy_cap.index].loc[
            max_cap.loc[energy_cap.index] < sw['storcap_cutoff']].index.tolist()
        + max_cap.loc[max_cap < sw['storcap_cutoff']/2].index.tolist()
    ))

    csvout['energy_cap'] = energy_cap.drop(too_small_storage, errors='ignore')
    csvout['max_cap'] = max_cap.drop(too_small_storage, errors='ignore')

    ### Storage efficiency
    storage_hybrid = reeds.techs.expand_GAMS_tech_groups(
        reeds.techs.get_tech_subset_table(casedir).loc[['STORAGE_HYBRID']].reset_index()
    ).i
    storage_eff = (
        gdxreeds['storage_eff']
        .loc[gdxreeds['storage_eff'].t==t]
        .set_index('i')
        .Value
        .rename('fraction')
        ## Only keep standalone storage
        .drop(storage_hybrid, errors='ignore')
    )
    ## As in ReEDS LP, storage losses are applied to charging side (none for discharging)
    csvout['charge_eff'] = storage_eff
    csvout['discharge_eff'] = pd.Series(index=storage_eff.index, data=1., name='fraction')

    #%% Planning reserve margin in MW (sometimes used during unit disaggregation)
    csvout['max_unitsize'] = (
        gdxreeds['prm'].loc[gdxreeds['prm'].t == t].set_index('r').Value
        * h5out['pras_load'].max()
    ).round().astype(int).rename_axis('r').rename('mw')
    ## Turn off for counties by setting to zero (zeros in this file mean the max unit
    ## size is not enforced for that region in ReEDS2PRAS)
    agglevel_variables = reeds.spatial.get_agglevel_variables(
        reeds.io.reeds_path, os.path.join(casedir, 'inputs_case')
    )
    counties = agglevel_variables['county_regions']
    if len(counties):
        csvout['max_unitsize'].loc[counties] = 0

    #%% Strip water tech suffixes from water-dependent technologies
    ### and change upgrade techs to the tech they are upgraded FROM.
    ### It would be more natural to use the tech they are upgraded TO but in most cases
    ### (e.g. for CCS and H2) we don't have empirical outage rates for the upgraded-TO tech.
    watertech2tech = pd.concat([
        pd.read_csv(
            os.path.join(casedir,'inputs_case','i_coolingtech_watersource_link.csv'),
            usecols=['*i','ii'],
        ),
        pd.read_csv(
            os.path.join(casedir,'inputs_case','i_coolingtech_watersource_upgrades_link.csv'),
            usecols=['*i','ii'],
        ),
    ]).apply(lambda x: x.str.lower()).set_index('*i').squeeze(1)

    upgrade2from = (
        pd.concat([
            pd.read_csv(
                os.path.join(casedir, 'inputs_case', 'upgrade_link.csv')
            ).rename(columns={'*TO':'TO'}),
            pd.read_csv(
                os.path.join(casedir, 'inputs_case', 'upgradelink_water.csv')
            ).rename(columns={'*TO-WATER':'TO', 'FROM-WATER':'FROM', 'DELTA-WATER':'DELTA'}),
        ])
        .apply(lambda x: x.str.lower())
        .set_index('TO').FROM
        .map(lambda x: watertech2tech.get(x,x))
    )
    watertech2tech = watertech2tech.map(lambda x: upgrade2from.get(x,x))

    techmap = pd.concat([upgrade2from, watertech2tech]).to_dict()

    ### Simplify all the techs in output csv files and sum the capacities
    for key in csvout:
        indices = csvout[key].index.names
        if ('i' in indices) and ('cap' in key):
            csvout[key] = csvout[key].rename(index=techmap, level='i').groupby(indices).sum()


    #%% Check for errors before sending to ReEDS2PRAS
    errorcheck_reeds2pras(casedir, csvout, h5out)


    #%%### Write it
    #%% .csv files
    for key in csvout:
        csvout[key].round(int(sw['decimals'])).to_csv(
            os.path.join(casedir,'ReEDS_Augur','augur_data',f'{key}_{t}.csv'),
        )

    #%% .h5 files
    for key in h5out:
        if key.startswith('pras'):
            reeds.io.write_profile_to_h5(
                df=h5out[key].astype(np.float32),
                filename=f'{key}_{t}.h5',
                outfolder=os.path.join(casedir,'ReEDS_Augur','augur_data'),
            )
        else:
            h5out[key].astype(np.float32).to_hdf(
                os.path.join(casedir,'ReEDS_Augur','augur_data',f'{key}_{t}.h5'),
                key='data', complevel=4, mode='w',
            )

    #%%### Return outputs for debugging
    return csvout, h5out
