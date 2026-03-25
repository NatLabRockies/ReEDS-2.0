#%%### Imports
import sys, os, site, math, time
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from glob import glob
pd.options.display.max_rows = 20
pd.options.display.max_columns = 200
import gdxpds
### Local imports
try:
    import ReEDS_Augur.functions as functions
except ModuleNotFoundError:
    import functions



#%%### Fixed inputs
dpi = None
interactive = False
savefig = True
### aggregation levels to use for dispatch plots
dispatchregions = [
    ('country','USA'),
    ('interconnect','western'),
    ('interconnect','texas'),
    ('interconnect','eastern'),
]


#%%### Functions
def group_techs(dfin, dfs, technamecol='i'):
    """
    Aggregate techs using bokehpivot tables
    """
    ## Get the colors
    tech_map = dfs['tech_map']
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    ## Aggregate by type
    dfout = dfin.copy()
    if technamecol in ['column', 'columns', 'wide', None, 0, False]:
        def renamer(x):
            out = (x if x[0].startswith('battery')
                else (x[0].strip('_01234567890*').lower(), x[1]))
            return out
        dfout.columns = dfout.columns.map(renamer)
        dfout.columns = (
            dfout.columns
            .map(lambda x: ([i for i in tech_map.index if x[0].startswith(i)][0], x[1]))
            .map(lambda x: (tech_map.get(x[0],x[0]), x[1]))
        )
    else:
        def renamer(x):
            out = x if x.startswith('battery') else x.strip('_01234567890*').lower()
            return out
        dfout[technamecol] = dfout[technamecol].map(renamer)
        dfout[technamecol] = (
            dfout[technamecol]
            .map(lambda x: ([i for i in tech_map.drop('hyd').index if x.startswith(i)]+[x])[0])
            .map(lambda x: tech_map.get(x,x))
        )
    return dfout


### Input-formatting functions
def get_gen(dfs, level='interconnect', region='texas'):
    """
    Return the sum of gen by tech for hierarchy level/region
    """
    gen_out = (
        dfs['gen']
        .assign(region=dfs['gen'].r.map(dfs['hierarchy'][level]))
        .groupby(['d','hr','i','region']).Val.sum()
        .unstack('region')[region]
        .unstack('i').fillna(0)
        # .loc[h_dt_szn.loc[h_dt_szn.year==2007,['d','hr']].values.tolist()]
        # .rename(columns=tech_map)
        .groupby(axis=1, level=0).sum()
        .reindex(dfs['h_dt_szn'][['d','hr']].values).fillna(0)
        .set_index(dfs['timeindex'])
    )
    return gen_out


def get_vre_gen(sw, dfs, level='interconnect', region='western'):
    """
    Return the sum of vre_gen by tech for hierarchy level/region
    """
    keeper = dfs['resources'].r.map(dfs['hierarchy'][level])
    vre_gen_out = dfs['vre_gen'].iloc[:,dfs['vre_gen'].columns.map(keeper)==region]
    vre_gen_out = (
        vre_gen_out
        .rename(columns=dfs['resources'].tech)
        .groupby(axis=1, level=0).sum()
        .set_index(dfs['fulltimeindex'])
    )
    if len(sw['osprey_years']) == 1:
        vre_gen_out = vre_gen_out.xs(int(sw['osprey_years'][0]), level='year', axis=0)
    return vre_gen_out


def get_load(sw, dfs, level='interconnect', region='western'):
    """
    Return the sum of load for hierarchy level/region
    """
    load_out = (
        dfs['load_r']
        .rename(columns=dfs['hierarchy'][level])
        .groupby(axis=1, level=0).sum()
        [region]
        .rename('Demand')
        .sort_index(level='hour')
        .set_axis(dfs['fulltimeindex'])
    )
    if len(sw['osprey_years']) == 1:
        load_out = load_out.xs(int(sw['osprey_years'][0]), level='year', axis=0)
    return load_out


def get_stor_charge(sw, dfs, level='interconnect', region='texas'):
    """
    Return the sum of gen by tech for hierarchy level/region
    """
    if dfs['stor_charge'].empty:
        return pd.DataFrame(index=dfs['timeindex'])
    stor_charge_out = (
        dfs['stor_charge']
        .assign(region=dfs['stor_charge'].r.map(dfs['hierarchy'][level]))
        .groupby(['d','hr','i','region']).Val.sum()
        .unstack('region')[region]
        .unstack('i')
        .reindex(dfs['h_dt_szn'].loc[dfs['h_dt_szn'].year.isin(sw['osprey_years']),['d','hr']].values, axis=0)
        .fillna(0)
        .set_index(dfs['timeindex'])
        * -1
    )
    return stor_charge_out


def get_produce(sw, dfs, level='interconnect', region='western'):
    """
    Return the sum of gen by tech for hierarchy level/region
    """
    if dfs['produce'].empty:
        return pd.Series(index=dfs['timeindex'], data=0, name=region)
    produce_out = (
        dfs['produce']
        .assign(region=dfs['produce'].r.map(dfs['hierarchy'][level]))
        .groupby(['d','hr','region']).Val.sum()
        .unstack('region').reindex(dfs['hierarchy'][level].unique(), axis=1)[region]
        .reindex(dfs['h_dt_szn'].loc[dfs['h_dt_szn'].year.isin(sw['osprey_years']),['d','hr']].values, axis=0)
        .fillna(0)
        .set_axis(dfs['timeindex'])
        * -1
    )
    return produce_out


def get_pras_system(sw, verbose=0):
    """
    Read a .pras .h5 file and return a dict of dataframes
    """
    import h5py
    ###### Read all the tables in the .pras file
    infile = os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS',
                          f"PRAS_{sw.t}i{sw.iteration}.pras")
    pras = {}
    with h5py.File(infile,'r') as f:
        keys = list(f)
        vals = {}
        for key in keys:
            vals[key] = list(f[key])
            if verbose: print('{}:\n    {}\n'.format(key,','.join(vals[key])))
            for val in vals[key]:
                pras[key,val] = pd.DataFrame(f[key][val][...])
                if verbose: print('{}/{}: {}'.format(key,val,pras[key,val].shape))
            if verbose: print('\n')

    ###### Combine into more easily-usable dataframes
    dfpras = {}
    keys = {
        ## our name: [pras key, pras capacity table name]
        'storcap': ['storages', 'dischargecapacity'],
        'gencap': ['generators', 'capacity'],
        'genstorcap': ['generatorstorages', 'gridinjectioncapacity'],
    }
    for key, val in keys.items():
        dfpras[key] = pras[val[0], val[1]]
        dfpras[key].columns = pd.MultiIndex.from_arrays(
            [pras[val[0],'_core'].category.str.decode('UTF-8'),
             pras[val[0],'_core'].region.str.decode('UTF-8')],
            names=['i','r'],
        )
        if verbose:
            print(key)
            print(dfpras[key].columns.get_level_values('i').unique())

    ### Load
    dfpras['load'] = pras['regions','load'].rename(
        columns=pras['regions','_core'].name.str.decode('UTF-8'))

    return dfpras


#%% Input-loading function
def get_inputs(sw):
    ### Make savepath
    import plots
    sw['savepath'] = os.path.join(sw['casedir'], 'outputs', 'Augur_plots')
    os.makedirs(sw['savepath'], exist_ok=True)

    ##### Load shared parameters
    fulltimeindex = np.ravel([
        pd.date_range(
            '{}-01-01'.format(y),
            '{}-01-01'.format(y+1),
            freq='H', closed='left', tz='EST',
        )[:8760]
        for y in range(2007,2014)
    ])

    if len(sw['osprey_years']) == 1:
        timeindex = pd.date_range(
            f"{sw['osprey_years'][0]}-01-01",
            f"{sw['osprey_years'][0]+1}-01-01",
            freq='H', closed='left', tz='EST',
        )[:8760]
    else:
        timeindex = np.ravel([
            pd.date_range(
                '{}-01-01'.format(y),
                '{}-01-01'.format(y+1),
                freq='H', closed='left', tz='EST',
            )[:8760]
            for y in sw['osprey_years']
        ])

    h_dt_szn = (
        pd.read_csv(os.path.join(sw['casedir'],'inputs_case','h_dt_szn.csv'))
        .assign(hr=(['hr{:>03}'.format(i+1) for i in range(sw['hoursperperiod'])]
                    * sw['periodsperyear'] * 7))
        .assign(datetime=fulltimeindex)
    )
    d_osprey = pd.read_csv(os.path.join(sw['casedir'],'inputs_case','d_osprey.csv'), header=None, squeeze=True)
    h_dt_szn['d'] = pd.concat([d_osprey]*sw['hoursperperiod']).sort_values().values

    gdxreeds = gdxpds.to_dataframes(
        os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f'reeds_data_{sw["t"]}.gdx'))
    gdxosprey = gdxpds.to_dataframes(
        os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f'osprey_inputs_{sw["t"]}.gdx'))

    techs = gdxreeds['i_subsets'].pivot(columns='i_subtech',index='i',values='Value')
    h2dac = techs['CONSUME'].dropna().index

    tech_map = pd.read_csv(
        os.path.join(sw['reeds_path'],'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).str.lower()
    tech_map = tech_map.drop_duplicates().set_index('raw').display.str.lower()

    existinghydrotechs = [
        'hyded','hydend','hydend_hyded',
    ]
    newhydrotechs = [
        'hydd','hydnd','hydnpd','hydnpnd','hydsd','hydsnd','hydud','hydund',
    ]
    tech_map = (
        tech_map
        .append(pd.Series(dict(zip(existinghydrotechs,['hydro_exist']*len(existinghydrotechs)))))
        .append(pd.Series(dict(zip(newhydrotechs,['hydro_new']*len(newhydrotechs)))))
    ).reset_index().drop_duplicates().set_index('index')[0].rename(None)

    tech_style = pd.read_csv(
        os.path.join(sw['reeds_path'],'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order', squeeze=True,
    )
    tech_style.index = tech_style.index.str.lower()
    tech_style['dropped'] = '#d62728'
    for i in ['hydro_exist', 'hydro_new']:
        tech_style[i] = tech_style['hydro']
    # ## Add some techs
    # for i in [1,2]:
    #     tech_style[f'csp{i}'] = tech_style['csp']
    # for i in [1,2,3]:
    #     tech_style[f'pvb{i}'] = tech_style['pvb']

    hierarchy = pd.read_csv(
        os.path.join(sw['casedir'],'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()

    resources = pd.read_csv(
        os.path.join(sw['casedir'],'inputs_case','resources.csv')
    ).set_index('resource')
    resources['tech'] = (
        resources.i.map(lambda x: x.split('_')[0])
        .map(lambda x: x if x.startswith('battery') else x.strip('_01234567890*')))

    resources['rb'] = resources.r

    ##### Hourly dispatch by month
    ### Load and aggregate the VRE generation profiles by tech group
    try:
        vre_gen = pd.read_hdf(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',f'pras_vre_gen_{sw.t}.h5'))
    except FileNotFoundError:
        vre_gen = None

    ### Get vre_gen by tech (only osprey_years)
    vre_gen_usa = (
        vre_gen
        .rename(columns=resources.tech)
        .groupby(axis=1, level=0).sum()
        .set_index(fulltimeindex)
    )
    if len(sw['osprey_years']) == 1:
        vre_gen_usa = vre_gen_usa.xs(int(sw['osprey_years'][0]), level='year', axis=0)

    ### Get vre_gen summed over tech by BA (full 7 years)
    vre_gen_r = (
        vre_gen
        .rename(columns=resources.rb.to_dict())
        .groupby(axis=1, level=0).sum()
    )

    ### Load Osprey load
    try:
        load_r = pd.read_hdf(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',f'load_{sw.t}.h5')
        )
    except FileNotFoundError:
        load_r = None

    ### Scale up by PRM if necessary
    if int(sw['osprey_prm']):
        prm = (
            gdxreeds['prm'].astype({'t':int})
            .pivot(index='t', columns='r', values='Value').loc[sw['t']])
        load_r *= (1 + prm)

    ### Sum over US
    load_usa = (
        load_r
        .sum(axis=1)
        .rename('Demand')
        .sort_index(level='hour')
        .set_axis(fulltimeindex)
    )
    if len(sw['osprey_years']) == 1:
        load_usa = load_usa.xs(int(sw['osprey_years'][0]), level='year', axis=0)

    ### Load PRAS load
    try:
        pras_load = pd.read_hdf(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',f'pras_load_{sw.t}.h5')
        )
    except FileNotFoundError:
        pras_load = None
    pras_load.index = fulltimeindex
    try:
        pras_h2dac_load = pd.read_hdf(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',
                f"pras_h2dac_load_{sw['t']}.h5"))
    except FileNotFoundError:
        pras_h2dac_load = pd.DataFrame(columns=pras_load.columns)
    pras_h2dac_load.index = fulltimeindex

    ### Load input capacity to PRAS
    try:
        max_cap = pd.read_csv(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',f"max_cap_{sw['t']}.csv"))
    except FileNotFoundError:
        max_cap = pd.DataFrame(columns=['i','v','r','MW'])

    ### Load and aggregate Osprey generation profiles
    try:
        gen = pd.read_csv(
            os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',
                        'gen_{}.csv'.format(sw['t'])))
        def simplify_i(x):
            _x = x if 'battery' in x else x.lower().strip('_01234567890*')
            return tech_map.get(_x,_x)
        gen.i = gen.i.map(simplify_i)
        gen_usa = get_gen(
            dfs={'gen':gen,'hierarchy':hierarchy,'timeindex':timeindex,'h_dt_szn':h_dt_szn},
            level='country', region='USA')

    except Exception as err:
        print(('gen_{}.csv'.format(sw['t']), err))
        gen = pd.DataFrame(columns=['d','hr','i','v','r','Val'])
        gen_usa = pd.DataFrame(index=timeindex)

    ### Load storage charging
    try:
        stor_charge = pd.read_csv(
            os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',
                        'storage_in_{}.csv'.format(sw['t'])))
        stor_charge_usa = get_stor_charge(
            sw,
            {'stor_charge':stor_charge,'hierarchy':hierarchy,
             'h_dt_szn':h_dt_szn,'timeindex':timeindex},
            'country','USA')

    except Exception as err:
        print(('storage_in_{}.csv'.format(sw['t']), err))
        stor_charge = pd.DataFrame(columns=['d','hr','i','v','r','Val'])
        stor_charge_usa = pd.DataFrame(index=timeindex)

    ### Load H2/CO2 production load
    try:
        produce = pd.read_csv(
            os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',
                        'produce_{}.csv'.format(sw['t'])))

        produce_usa = get_produce(
            sw,
            {'produce':produce,'hierarchy':hierarchy,
             'h_dt_szn':h_dt_szn,'timeindex':timeindex},
            'country','USA')

    except Exception as err:
        print(('produce_{}.csv'.format(sw['t']), err))
        produce = pd.DataFrame(columns=['d','hr','r','Val'])
        produce_usa = pd.Series(index=timeindex, name='produce', dtype=float)

    ### Load storage energy level
    try:
        stor_energy = (
            pd.read_csv(
                os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',
                            'storage_level_{}.csv'.format(sw['t'])))
            .groupby(['d','hr','i']).Val.sum()
            .unstack('i')
            .reindex(h_dt_szn.loc[h_dt_szn.year.isin(sw['osprey_years']),['d','hr']].values, axis=0)
            .fillna(0)
            .set_index(timeindex)
        )

    except Exception as err:
        print(('storage_level_{}.csv'.format(sw['t']), err))
        stor_energy = pd.DataFrame(index=timeindex)

    ### Load dropped load from Osprey
    try:
        dropped_load = (
            pd.read_csv(
                os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',
                            'dropped_load_{}.csv'.format(sw['t'])))
            # .groupby(['d','hr']).Val.sum()
            .pivot(index=['d','hr'], columns='r', values='Val')
            .reindex(h_dt_szn.loc[h_dt_szn.year.isin(sw['osprey_years']),['d','hr']].values, axis=0)
            .fillna(0)
        )
        dropped_load.index = timeindex

    except Exception as err:
        print(('dropped_load_{}.csv'.format(sw['t']), err))
        dropped_load = pd.DataFrame(index=timeindex)

    ### Load LOLE/EUE/NEUE from PRAS
    try:
        pras = pd.read_csv(
            os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS',
                         f"PRAS_{sw.t}i{sw.iteration}.csv"),
            index_col='h', parse_dates=True,
        )
        pras.index = fulltimeindex
    except FileNotFoundError as err:
        print(f"Failed to load PRAS outputs: {err}")
        pras = pd.DataFrame({'USA_EUE':9999}, index=fulltimeindex)

    ### Load the PRAS system
    try:
        pras_system = get_pras_system(sw)
        for key in pras_system:
            pras_system[key].index = fulltimeindex
    except FileNotFoundError as err:
        print(f"Failed to load .pras system: {err}")
        pras_system = dict()

    ###### Get net load profiles
    ### Get net load by BA
    net_load_r = load_r - vre_gen_r
    ### Get net load by ccreg
    net_load_ccreg = net_load_r.rename(columns=hierarchy.ccreg).groupby(axis=1, level=0).sum()
    ### Get net load for the USA
    net_load_usa = net_load_r.set_index(fulltimeindex).sum(axis=1)
    ### Get the net load used in Osprey
    try:
        net_load_osprey = pd.read_csv(
            os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"net_load_{sw['t']}.csv")
        ).drop(['d','hr'], axis=1, errors='ignors')
        net_load_osprey.index = load_r.index
    except FileNotFoundError as err:
        print(err)
        net_load_osprey = pd.DataFrame(index=load_r.index)

    ###### Make combined dataframes for plotting
    dfgen_all = (
        gen_usa
        .merge(vre_gen_usa, left_index=True, right_index=True)
        .merge(dropped_load.sum(axis=1).rename('dropped'), left_index=True, right_index=True)
    )

    groupcols = {
        **{c: 'coal' for c in dfgen_all if c.startswith('coal')},
        **{c: 'hydro' for c in dfgen_all if c.startswith('hyd')},
        **{c: 'h2-cc' for c in dfgen_all if c.endswith('h2-cc')},
        **{c: 'h2-ct' for c in dfgen_all if c.endswith('h2-ct')},
        # **tech_map.map(tech_style).to_dict(),
    }

    dfgen_pos = dfgen_all.rename(columns=groupcols).groupby(axis=1, level=0).sum()
    order = [c for c in tech_style.index if c in dfgen_pos]
    if not len(order) == dfgen_pos.shape[1]:
        raise Exception(
            "order and dfgen_pos don't match: {} {} {}".format(
                len(order), dfgen_pos.shape[1], ','.join([c for c in dfgen_pos if c not in order])))
    dfgen_pos = dfgen_pos[order].cumsum(axis=1)[order[::-1]]
    ### Negative components
    dfgen_neg = (
        pd.concat([stor_charge_usa, produce_usa.rename('produce')], axis=1)
        .cumsum(axis=1)
        [['produce']+stor_charge_usa.columns[::-1].tolist()]
    )

    curtailment = None

    ### Load Osprey prices by BA
    try:
        prices = (
            pd.read_csv(
                os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',
                            'prices_{}.csv'.format(sw['t'])))
            .pivot(index=['d','hr'], columns='r', values='Val')
            .fillna(0)
            .set_index(timeindex)
        )
    except FileNotFoundError as err:
        print(err)
        prices = pd.DataFrame(index=timeindex)

    ### Get top load hours by season
    hour2datetime = h_dt_szn.set_index('hour').datetime.copy()
    ### Use seasons appropriate to resolution
    seasons = net_load_ccreg.index.get_level_values('season').unique()
    if 'fall' in seasons:
        seasons = ['winter','spring','summer','fall']
    elif 'winter' in seasons:
        seasons = ['winter','spring','summer','fall']
    elif 'szn' in seasons[0]:
        seasons = [f'szn{s}' for s in sorted([int(s.strip('szn')) for s in seasons])]

    ccregs = sorted(net_load_ccreg.columns)
    peakhours = {}
    for season in seasons:
        for ccreg in ccregs:
            peakhours[season,ccreg] = (
                net_load_ccreg.loc[season][ccreg]
                .nlargest(int(sw['capcredit_szn_hours'])).index.get_level_values('hour'))

    dfpeak = (
        pd.DataFrame(peakhours)
        .stack(level=0)
        .reorder_levels([1,0], axis=0)
        .stack().map(hour2datetime).rename('datetime').to_frame()
        .assign(peak=1)
        .reset_index(level=2).rename(columns={'level_2':'ccreg'})
        .pivot(index='datetime', columns='ccreg', values='peak')
        .reindex(fulltimeindex)
        .fillna(0).astype(int)
    )

    peakcolors = plots.rainbowmapper(ccregs, plt.cm.tab20)

    ### Assign colors based on bokeh defaults
    colors = {
        'produce':tech_style['electrolyzer'],
        'dropped':'C3',
        'hydro_nd':'C9',
        # 'coal':tech_style['coal'], 'coal-new':tech_style['coal'],
        # 'coaloldscr':tech_style['coal'], 'coalolduns':tech_style['coal'],    
        # 'hydro':tech_style['hydro'],
        # 'hydro_d':tech_style['hydro'],
        # 'hydend':tech_style['hydro'], 'hyded':tech_style['hydro'],
        # 'h2-cc':tech_style['h2-cc'], 'h2-ct':tech_style['h2-ct'],
        # 'csp1':tech_style['csp'], 'csp2':tech_style['csp'],
        # 'pvb1':tech_style['pvb'], 'pvb2':tech_style['pvb'], 'pvb3':tech_style['pvb'],
    }
    try:
        for i in gen_usa.columns.tolist() + vre_gen_usa.columns.tolist():
            if i in colors:
                pass
            elif i in tech_style:
                colors[i] = tech_style[i]
            elif i in tech_map:
                colors[i] = tech_style[tech_map[i]]
            else:
                colors[i] = 'k'
                print('missing color for {}'.format(i))
    except Exception as err:
        print(err)

    ###### Store them for later
    dfs = {}
    dfs['colors'] = colors
    dfs['curtailment'] = curtailment
    dfs['dfgen_all'] = dfgen_all
    dfs['dfgen_neg'] = dfgen_neg
    dfs['dfgen_pos'] = dfgen_pos
    dfs['dfpeak'] = dfpeak
    dfs['dropped_load'] = dropped_load
    dfs['fulltimeindex'] = fulltimeindex
    dfs['gdxosprey'] = gdxosprey
    dfs['gdxreeds'] = gdxreeds
    dfs['gen'] = gen
    dfs['groupcols'] = groupcols
    dfs['h_dt_szn'] = h_dt_szn
    dfs['h2dac'] = h2dac
    dfs['hierarchy'] = hierarchy
    dfs['load_r'] = load_r
    dfs['load_usa'] = load_usa
    dfs['max_cap'] = max_cap
    dfs['net_load_r'] = net_load_r
    dfs['net_load_usa'] = net_load_usa
    dfs['order'] = order
    dfs['peakcolors'] = peakcolors
    dfs['pras_h2dac_load'] = pras_h2dac_load
    dfs['pras_load'] = pras_load
    dfs['pras_system'] = pras_system
    dfs['pras'] = pras
    dfs['prices'] = prices
    dfs['produce_usa'] = produce_usa
    dfs['produce'] = produce
    dfs['resources'] = resources
    dfs['stor_charge_usa'] = stor_charge_usa
    dfs['stor_charge'] = stor_charge
    dfs['stor_energy'] = stor_energy
    dfs['tech_map'] = tech_map
    dfs['tech_style'] = tech_style
    dfs['timeindex'] = timeindex
    dfs['vre_gen_usa'] = vre_gen_usa
    dfs['vre_gen'] = vre_gen

    return dfs


#%%### Plotting functions
def plot_b1_dispatch_usa(sw, dfs):
    """
    Osprey hourly dispatch, full year full US
    """
    if not (int(sw['osprey']) or (
        int(sw['GSw_PRM_MaxStressPeriods'])
        and (sw['GSw_PRM_StressModel'].lower() == 'osprey')
    )):
        return
    import plots
    savename = f"B1-dispatch-usa-wYEAR-{sw['t']}.png"
    for y in sw['osprey_years']:
        plt.close()
        ## Generation
        f,ax = plots.plotyearbymonth(
            dfs['dfgen_pos'].loc[str(y)], colors=[dfs['colors'][c] for c in dfs['dfgen_pos']], dpi=dpi,
        )
        ## Storage charging and H2/DAC production load
        plots.plotyearbymonth(
            dfs['dfgen_neg'].loc[str(y)], f=f, ax=ax, colors=[dfs['colors'][c] for c in dfs['dfgen_neg']],
        )
        ## Load
        plots.plotyearbymonth(
            dfs['load_usa'].loc[str(y)].to_frame(), f=f, ax=ax, colors=['k'], style='line', lwforline=0.75,
        )
        ## Legend
        leg = ax[0].legend(
            loc='upper left', bbox_to_anchor=(1,1.25),
            fontsize=11, frameon=False, ncol=2,
            columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        )
        leg.set_title('Generation', prop={'size':'large'})

        if savefig: plt.savefig(os.path.join(sw['savepath'],savename.replace('YEAR',str(y))))
        if interactive: plt.show()
        plt.close()


def plot_b1c1_profiles_usa(sw, dfs):
    """
    Table: Hourly profiles for USA
    """
    if not (int(sw['osprey']) or (
        int(sw['GSw_PRM_MaxStressPeriods'])
        and (sw['GSw_PRM_StressModel'].lower() == 'osprey')
    )):
        return
    savename = f"B1C1-profiles-usa-{sw['t']}.csv.gz"
    ### Combine results
    dfout = pd.concat({
        'gen_pos': dfs['dfgen_all'].rename(columns=dfs['groupcols']).groupby(axis=1, level=0).sum()[dfs['order']],
        'gen_neg': pd.concat([dfs['stor_charge_usa'], dfs['produce_usa'].rename('produce')], axis=1),
        'load': pd.concat([
            dfs['load_usa'].rename('total'),
            dfs['net_load_usa'].rename('net'),
            dfs['dropped_load'].sum(axis=1).rename('dropped'),
        ], axis=1),
        'curtailment': dfs['curtailment'],
        'energy': dfs['stor_energy'],
    }, axis=1).round(1)

    if savefig: dfout.to_csv(os.path.join(sw['savepath'],savename))


def plot_b1_load_duration(sw, dfs):
    """
    Load & generation duration curve
    """
    if not (int(sw['osprey']) or (
        int(sw['GSw_PRM_MaxStressPeriods'])
        and (sw['GSw_PRM_StressModel'].lower() == 'osprey')
    )):
        return
    import plots
    top = 100
    savename = f"B1-load-duration-top{top}-{sw['t']}.png"

    sorted_index = dfs['load_usa'].sort_values(ascending=False).index
    dfplot = dfs['dfgen_pos'].loc[sorted_index].set_index(np.linspace(0,100,len(dfs['dfgen_pos']))) / 1000
    plt.close()
    f,ax = plt.subplots(figsize=(7,3.75), dpi=dpi)
    ## Generation
    dfplot.plot.area(ax=ax, color=dfs['colors'], lw=0, stacked=False, alpha=1)
    ## Wash it out
    # dfplot.max(axis=1).plot.area(ax=ax, color='w', lw=0, alpha=0.3)
    ## Load
    ax.plot(
        np.linspace(0,100,len(dfs['load_usa'])),
        dfs['load_usa'].loc[sorted_index].values / 1000,
        c='k', ls='-', lw=2, solid_capstyle='butt')
    ## Mark the extrema
    ax.plot(
        [0], [dfs['load_usa'].max()/1000],
        lw=0, marker=1, ms=5, c='k',)
    ax.plot(
        [100], [dfs['load_usa'].min()/1000],
        lw=0, marker=0, ms=5, c='k',)
    ## Formatting
    ax.set_ylabel('Load [GW]')
    ax.set_xlabel(
        f"Percent of dispatch period ({min(sw['osprey_years'])}–{max(sw['osprey_years'])}) [%]")
    ax.set_xlim(0,top)
    ax.legend(
        loc='center left', bbox_to_anchor=(1,0.5),
        fontsize=11, frameon=False, ncol=2,
        columnspacing=0.5, handletextpad=0.5, handlelength=0.75,
    )
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_b1_netload_duration(sw, dfs):
    """
    Net load duration curve
    """
    if not (int(sw['osprey']) or (
        int(sw['GSw_PRM_MaxStressPeriods'])
        and (sw['GSw_PRM_StressModel'].lower() == 'osprey')
    )):
        return
    import plots
    for top in [100,10,1]:
        savename = f"B1-netload-duration-top{top}-{sw['t']}.png"

        sorted_index = dfs['net_load_usa'].sort_values(ascending=False).index
        dfplot = dfs['dfgen_pos'].loc[sorted_index].set_index(np.linspace(0,100,len(dfs['dfgen_pos']))) / 1000
        plt.close()
        f,ax = plt.subplots(figsize=(7,3.75), dpi=dpi)
        ## Generation
        dfplot.plot.area(ax=ax, color=dfs['colors'], lw=0, stacked=False, alpha=1)
        ## Wash it out
        # dfplot.max(axis=1).plot.area(ax=ax, color='w', lw=0, alpha=0.3)
        ## Net load
        ax.plot(
            np.linspace(0,100,len(dfs['net_load_usa'])),
            dfs['net_load_usa'].loc[sorted_index].values / 1000,
            c='k', ls='-', lw=2, solid_capstyle='butt')
        ## Mark the extrema
        ax.plot(
            [0], [dfs['net_load_usa'].max()/1000],
            lw=0, marker=1, ms=5, c='k',)
        ax.plot(
            [dfs['net_load_usa'].sort_values(ascending=False).abs().argmin() / len(dfs['net_load_usa']) * 100],
            [0],
            lw=0, marker=2, ms=5, c='k',)
        ## Formatting
        ax.set_ylabel('Net load [GW]')
        ax.set_xlabel(
            f"Percent of dispatch period ({min(sw['osprey_years'])}–{max(sw['osprey_years'])}) [%]")
        ax.set_xlim(0,top)
        # ax.set_ylim(net_load_usa.min()/1000)
        ax.legend(
            loc='center left', bbox_to_anchor=(1,0.5),
            fontsize=11, frameon=False, ncol=2,
            columnspacing=0.5, handletextpad=0.5, handlelength=0.75,
        )
        plots.despine(ax)
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_netload_profile(sw, dfs):
    """
    Net load profile
    """
    import plots
    for y in sw['osprey_years']:
        savename = f"A-netload-profile-w{y}-{sw['t']}.png"

        dfpos = dfs['net_load_usa'].loc[str(y)].clip(lower=0)
        dfneg = dfs['net_load_usa'].loc[str(y)].clip(upper=0)
        plt.close()
        f,ax = plots.plotyearbymonth(
            dfpos, colors=['C3'], dpi=dpi,
        )
        plots.plotyearbymonth(
            dfneg, colors=['C0'],
            f=f, ax=ax,
        )
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_dispatch_maxmin_netload_weeks(sw, dfs):
    """
    Osprey hourly dispatch for max/min net load days ±3 days
    """
    if not (int(sw['osprey']) or (
        int(sw['GSw_PRM_MaxStressPeriods'])
        and (sw['GSw_PRM_StressModel'].lower() == 'osprey')
    )):
        return
    import plots
    savename = f"B1-dispatch-maxmin_netload_weeks-{sw['t']}.png"

    plottimes = {}
    for level, region in dispatchregions:
        try:
            net_load_region = (
                dfs['net_load_r'].rename(columns=dfs['hierarchy'][level])
                .groupby(axis=1, level=0).sum()
                .set_index(dfs['fulltimeindex'])
                # .loc[str(sw['reeds_data_year'])]
                [region]
            )
        except KeyError as err:
            print(err)
            continue
        net_load_region_day = net_load_region.groupby([
            net_load_region.index.year, net_load_region.index.month, net_load_region.index.day
        ]).sum()
        peakdays = {
            'min': net_load_region_day.nsmallest(1).index.values[0],
            'max': net_load_region_day.nlargest(1).index.values[0],
        }
        ### Add 3 days on either side
        for i in peakdays:
            peakdaystart = pd.Timestamp(
                '{}-{}-{} 00:00'.format(*peakdays[i]), tz='EST')
            ### Loop back to beginning of year (messes up datetime x axis on plots)
            # peakrange = range(
            #     (list(timeindex).index(peakdaystart) - 72),
            #     (list(timeindex).index(peakdaystart) + 96))
            # plottimes[level,region,i] = timeindex[[h % 8760 for h in peakrange]]
            ### Just keep the timestamps that are in the next year, then drop from plot
            plottimes[level,region,i] = pd.date_range(
                peakdaystart - pd.Timedelta('72H'),
                peakdaystart + pd.Timedelta('95H'),
                freq='H',
            )

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        len(dispatchregions)*2, 1, figsize=(10,len(dispatchregions)*3.0),
        gridspec_kw={'hspace':0.75},
    )
    # row, level, region = 0, 'country', 'USA'
    for row, (level,region) in enumerate(dispatchregions):
        try:
            dfall = (
                get_gen(dfs,level,region)
                .merge(
                    get_vre_gen(sw,dfs,level,region),
                    left_index=True, right_index=True)
            ) / 1000
        except KeyError:
            continue
        ### Aggregate some columns
        dfpos = dfall.rename(columns=dfs['groupcols']).groupby(axis=1, level=0).sum()
        order = [c for c in dfs['tech_style'].index if c in dfpos]
        if not len(order) == dfpos.shape[1]:
            raise Exception(
                "order and dfpos don't match: {} {} {}".format(
                    len(order), dfpos.shape[1], ','.join([c for c in dfpos if c not in order])))
        dfpos = dfpos[order].cumsum(axis=1)[order[::-1]]
        ### Negative components
        dfneg = (
            pd.concat(
                [get_stor_charge(sw,dfs,level,region),
                get_produce(sw,dfs,level,region).rename('produce')],
                axis=1)
            .cumsum(axis=1)
            [['produce']+get_stor_charge(sw,dfs,level,region).columns[::-1].tolist()]
        ) / 1000

        ### Plot the max net load week
        for plotcol in dfpos:
            ax[row*2].fill_between(
                plottimes[level,region,'max'],
                dfpos.reindex(plottimes[level,region,'max'])[plotcol].fillna(0).values,
                lw=0, color=dfs['colors'][plotcol], label=plotcol,
            )
        for plotcol in dfneg:
            ax[row*2].fill_between(
                plottimes[level,region,'max'],
                dfneg.reindex(plottimes[level,region,'max'])[plotcol].fillna(0).values,
                lw=0, color=dfs['colors'][plotcol], label=plotcol,
            )
        ax[row*2].plot(
            plottimes[level,region,'max'],
            get_load(sw,dfs,level,region).reindex(plottimes[level,region,'max']).fillna(0).values / 1000,
            color='k', lw=1.5,
        )
        ax[row*2].set_title(
            '{} max'.format(region), x=0.01, ha='left', va='top', y=1.0, weight='bold')
        ### Plot the min net load week
        for plotcol in dfpos:
            ax[row*2+1].fill_between(
                plottimes[level,region,'min'],
                dfpos.reindex(plottimes[level,region,'min'])[plotcol].fillna(0).values,
                lw=0, color=dfs['colors'][plotcol], label=plotcol,
            )
        for plotcol in dfneg:
            ax[row*2+1].fill_between(
                plottimes[level,region,'min'],
                dfneg.reindex(plottimes[level,region,'min'])[plotcol].fillna(0).values,
                lw=0, color=dfs['colors'][plotcol], label=plotcol,
            )
        ax[row*2+1].plot(
            plottimes[level,region,'min'],
            get_load(sw,dfs,level,region).reindex(plottimes[level,region,'min']).fillna(0).values / 1000,
            color='k', lw=1.5,
        )
        ax[row*2+1].set_title(
            '{} min'.format(region), x=0.01, ha='left', va='top', y=1.0, weight='bold')
    ## Legend
    leg = ax[0].legend(
        loc='upper left', bbox_to_anchor=(1.02,1),
        fontsize=11, frameon=False, ncol=1,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    ax[0].set_ylabel('Generation [GW]', ha='right', y=1)

    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_b1_storage_energy(sw, dfs):
    """
    Osprey storage energy level
    """
    import plots
    for y in sw['osprey_years']:
        savename = f"B1-storage_energy-w{y}-{sw['t']}.png"

        dfplot = dfs['stor_energy'].loc[str(y)].cumsum(axis=1)[dfs['stor_charge_usa'].columns[::-1]]
        plt.close()
        f,ax = plots.plotyearbymonth(
            dfplot, colors=[dfs['colors'][c] for c in dfplot], dpi=dpi,
        )
        ## Legend
        ax[0].legend(
            loc='upper left', bbox_to_anchor=(1,1.25),
            fontsize=11, frameon=False, ncol=1,
            title='Energy level',
            columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        )
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_c1_curtailment_timeseries(sw, dfs):
    """
    Augur C1 curtailment timeseries
    """
    import plots
    for y in sw['osprey_years']:
        savename = f"C1-curtailment-timeseries-w{y}-{sw['t']}.png"

        plt.close()
        ## VRE gen
        f,ax = plots.plotyearbymonth(
            dfs['vre_gen_usa'].loc[str(y)].cumsum(axis=1)[dfs['vre_gen_usa'].columns[::-1]],
            colors=[dfs['colors'][c] for c in dfs['vre_gen_usa'].columns[::-1]],
            dpi=dpi, alpha=1,
        )
        ## Wash it out
        # plots.plotyearbymonth(
        #     dfs['vre_gen_usa'].loc[str(y)].sum(axis=1).rename('_nolabel_').to_frame(),
        #     f=f, ax=ax, colors=['w'], alpha=0.4,
        # )
        ## Curtailment
        if dfs['curtailment'] is not None:
            plots.plotyearbymonth(
                dfs['curtailment'].loc[str(y)].sum(axis=1).rename('curtailment').to_frame(),
                f=f, ax=ax, colors=['k'],
            )
        ## Legend
        ax[0].legend(
            loc='upper left', bbox_to_anchor=(1,1.25),
            fontsize=11, frameon=False, ncol=1,
            columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        )
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_c1_load_netload_curtailment_profile(sw, dfs):
    """
    Load, net load, curtailment
    """
    import plots
    for y in sw['osprey_years']:
        savename = f"C1-load_netload_curtailment-profile-w{y}-{sw['t']}.png"
        MWperTW = 1e6

        plt.close()
        f,ax = plt.subplots(figsize=(10,3.75))
        ### Load
        (dfs['load_usa']/MWperTW).loc[str(y)].plot(
            ax=ax, color='k', lw=0.25, label='End-use electricity demand')
        ### Net load including storage dispatch
        (((dfs['net_load_usa'] - dfs['gen_usa'][dfs['stor_charge_usa'].columns.values].sum(axis=1)
          ).clip(lower=0)/MWperTW
         ).loc[str(y)]
        ).plot.area(
            ax=ax, color='C3', lw=0, label='Demand – (VRE + storage)')
        ### Curtailment
        if dfs['curtailment'] is not None:
            (-dfs['curtailment'].sum(axis=1)/MWperTW).loc[str(y)].plot.area(
                ax=ax, color='C0', lw=0, label='Curtailment')
        ax.axhline(0,c='k',ls=':',lw=0.5)
        # ax.set_ylim(-curtailment.sum(axis=1).max()/MWperTW, load_usa.max()/MWperTW)
        ax.legend(
            frameon=False,
            columnspacing=0.5, handletextpad=0.3, handlelength=0.75,
        )
        ax.set_ylabel('TW (national total)')
        plots.despine(ax)
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_c1_curtailment_duration(sw, dfs):
    """
    Augur C1 curtailment duration curve
    """
    import plots
    savename = f"C1-curtailment-duration-{sw['t']}.png"

    sorted_index = dfs['curtailment'].sum(axis=1).sort_values(ascending=False).index
    dfplot = (
        dfs['vre_gen_usa'].cumsum(axis=1)[dfs['vre_gen_usa'].columns[::-1]]
        .loc[sorted_index]
        .set_index(np.linspace(0,100,len(dfs['vre_gen_usa'])))
        / 1000
    )
    curtailment_plot = dfs['curtailment'].sum(axis=1).loc[sorted_index].copy()
    curtailment_plot.loc[curtailment_plot==0] = np.nan
    plt.close()
    f,ax = plt.subplots(figsize=(7,3.75), dpi=dpi)
    ## Generation
    dfplot.plot.area(ax=ax, color=dfs['colors'], lw=0, stacked=False, alpha=1)
    ## Wash it out
    # dfplot.sum(axis=1).plot.area(ax=ax, color='w', lw=0, alpha=0.3)
    ## Curtailment
    ax.plot(
        np.linspace(0,100,len(dfs['load_usa'])),
        curtailment_plot.values / 1000,
        c='k', ls='-', lw=2, label='curtailment', solid_capstyle='butt')
    ## Mark the extrema
    ax.plot(
        [0], [curtailment_plot.max()/1000],
        lw=0, marker=1, ms=5, c='k',)
    ax.plot(
        [(curtailment_plot.fillna(0)>0).sum()/len(dfs['load_usa'])*100], [0],
        lw=0, marker=2, ms=5, c='k',)
    ## Formatting
    ax.set_ylabel('Generation [GW]')
    ax.set_xlabel('Percent of year [%]')
    ax.set_xlim(0,100)
    # ax.set_xlim(0,(curtailment_plot>0).sum()/len(curtailment)*100)
    ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(4))
    ax.legend(
        loc='center left', bbox_to_anchor=(1,0.5),
        fontsize=11, frameon=False, ncol=1,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.75,
    )
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_b1_dropped_load_timeseries(sw, dfs):
    """
    Osprey dropped load timeseries
    """
    if not dfs['dropped_load'].sum(axis=1).sum():
        return
    import plots
    for y in sw['osprey_years']:
        savename = f"B1-dropped_load-timeseries-w{y}-{sw['t']}.png"

        plt.close()
        ## Load
        f,ax = plots.plotyearbymonth(
            dfs['load_usa'].loc[str(y)].to_frame(), colors=['0.8'], dpi=dpi
        )
        ## Dropped load
        plots.plotyearbymonth(
            dfs['dropped_load'].sum(axis=1).loc[str(y)].rename('Dropped').to_frame(),
            f=f, ax=ax, colors=['C3'], dpi=dpi,
        )
        ## Legend
        ax[0].legend(
            loc='upper left', bbox_to_anchor=(1,1.25),
            fontsize=11, frameon=False, ncol=1,
            columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        )
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_b1_dropped_load_timeseries_full(sw, dfs):
    """
    Dropped load timeseries
    """
    import plots
    dropped = {
        'osprey':dfs['dropped_load'].sum(axis=1),
        'pras':dfs['pras']['USA_EUE']
    }
    timeindex_y = pd.date_range(
        f"{sw['t']}-01-01", f"{sw['t']+1}-01-01", closed='left', freq='H',
        tz='EST')[:8760]
    for model in ['osprey','pras']:
        if ((not dropped[model].sum()) or (dropped[model] == 9999).all()):
            continue
        savename = f"B1-dropped_load-timeseries-wfull-{model}-{sw['t']}.png"
        wys = sw['osprey_years'] if model == 'osprey' else range(2007,2014)
        plt.close()
        f,ax = plt.subplots(len(wys), 1, sharex=True, sharey=True, figsize=(13.33,5))
        for row, y in enumerate(wys):
            # ax[row].fill_between(
            #     timeindex_y, dfs['load_usa'].loc[str(y)].values/1e3,
            #     lw=0, color='0.8')
            ax[row].fill_between(
                timeindex_y, dropped[model].loc[str(y)].values/1e3,
                lw=0.2, color='C3')
            ### Formatting
            ax[row].annotate(
                y, (0.01,1), xycoords='axes fraction',
                fontsize=14, weight='bold', va='top')
        ### Formatting
        ax[0].set_xlim(
            pd.Timestamp(f"{sw['t']}-01-01 00:00-05:00"),
            pd.Timestamp(f"{sw['t']}-12-31 23:59-05:00"))
        ax[0].set_ylim(0)
        ax[len(wys)-1].set_ylabel('Dropped load [GW]', y=0, ha='left')
        plots.despine(ax)
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_b1_h2dac_load_timeseries(sw, dfs):
    """
    Osprey dropped load timeseries
    """
    import plots

    if dfs['produce_usa'].sum():
        dfplot = dfs['produce_usa']
    else:
        dfplot = dfs['pras_h2dac_load'].sum(axis=1)

    for y in sw['osprey_years']:
        savename = f"B1-h2dac_load-timeseries-w{y}-{sw['t']}.png"

        plt.close()
        ## DAC and H2 demand
        f,ax = plots.plotyearbymonth(
            dfplot.loc[str(y)].rename('H2/DAC\ndemand').abs().to_frame(),
            colors=['C9'], dpi=dpi,
        )
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_b1_dropped_load_duration(sw, dfs):
    """
    Dropped load duration
    """
    import plots
    dropped = {
        'osprey':dfs['dropped_load'].sum(axis=1),
        'pras':dfs['pras']['USA_EUE']
    }

    for model in ['osprey','pras']:
        if ((not dropped[model].sum()) or (dropped[model] == 9999).all()):
            continue
        savename = f"B1-dropped_load-duration-{model}-{sw['t']}.png"
        plt.close()
        f,ax = plt.subplots(dpi=dpi)
        # ## Load
        # ax.fill_between(
        #     range(len(dfs['load_usa'])),
        #     dfs['load_usa'].sort_values(ascending=False).values/1e3,
        #     color='0.8', lw=0, label='Demand',
        # )
        ## Dropped load
        ax.fill_between(
            range(len(dfs['load_usa'])),
            dropped[model].rename('Dropped').sort_values(ascending=False).values/1e3,
            color='C3', lw=0, label='Dropped',
        )
        ## Mark the extrema
        ax.plot(
            [0], [dropped[model].max()/1000],
            lw=0, marker=1, ms=5, c='C3',)
        ax.plot(
            [(dropped[model]>0).sum()], [0],
            lw=0, marker=2, ms=5, c='C3',)
        ## Formatting
        ax.set_ylabel('Demand [GW]')
        ax.set_xlabel(
            f"Hours of dispatch period ({min(sw['osprey_years'])}–"
            f"{max(sw['osprey_years'])}) [h]")
        ax.set_xlim(0,(dropped[model]>0).sum())
        ax.set_ylim(0)
        ax.legend(
            # loc='upper left', bbox_to_anchor=(1,1.25),
            fontsize=11, frameon=True, ncol=1,
            columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        )
        plots.despine(ax)
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def map_dropped_load(sw, dfs):
    """
    Annual EUE and NEUE by ReEDS zone
    """
    import reedsplots

    ### Get the inputs
    dfba = reedsplots.get_zonemap(sw['casedir'])
    dfba['labelx'] = dfba.geometry.centroid.x
    dfba['labely'] = dfba.geometry.centroid.y
    dropped = {
        'osprey': dfs['dropped_load'],
        'pras': dfs['pras'][
            [c for c in dfs['pras'] if c.endswith('_EUE') and (not c.startswith('USA'))]
        ]
    }
    dropped['pras'].columns = dropped['pras'].columns.map(lambda x: x.split('_')[0])
    units = {
        ('EUE','max'): ('MW',1), ('EUE','mean'): ('MW',1), ('EUE','sum'): ('GWh',1e-3),
        ('NEUE','max'): ('%',1e2), ('NEUE','sum'): ('ppm',1e6),
    }

    ### Plot it
    for metric in ['EUE','NEUE']:
        for model in ['osprey','pras']:
            if model == 'osprey':
                load = dfs['load_r'].set_index(dropped['pras'].index)
            else:
                load = dfs['pras_load']
            if not dropped[model].sum().sum():
                continue
            for agg in ['max','sum','mean']:
                if (metric,agg) not in units:
                    continue
                savename = f"B1-dropped_load-map-{metric}_{agg}-{model}-{sw['t']}.png"

                dfplot = dfba.copy()
                if metric == 'EUE':
                    dfplot['val'] = dropped[model].agg(agg)
                elif (metric == 'NEUE') and (agg == 'max'):
                    dfplot['val'] = (dropped[model] / load).agg(agg)
                elif (metric == 'NEUE'):
                    dfplot['val'] = dropped[model].agg(agg) / load.agg(agg)
                dfplot.val = (dfplot.val * units[metric,agg][1]).replace(0, np.nan)

                plt.close()
                f,ax = plt.subplots(figsize=(8,8/1.45), dpi=150)
                ### Background
                dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.2)
                ### Data
                dfplot.plot(ax=ax, column='val', cmap=plt.cm.gist_earth_r)
                for r, row in dfplot.iterrows():
                    if row.val > 0:
                        ax.annotate(
                            f'{row.val:,.0f} {units[metric,agg][0]}',
                            (row.labelx, row.labely),
                            color='r', ha='center', va='top', fontsize=6, weight='bold')
                ### Formatting
                for r, row in dfba.iterrows():
                    ax.annotate(r, (row.labelx, row.labely),
                                ha='center', va='bottom', fontsize=6, color='C7')
                ax.axis('off')
                if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
                if interactive: plt.show()
                plt.close()


def plot_pras_ICAP(sw, dfs):
    """
    Plot the available capacity used in PRAS without any outages
    """
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    ### Collect the PRAS system capacities
    gencap = dfs['pras_system']['gencap'].groupby(axis=1, level=0).sum()
    storcap = dfs['pras_system']['storcap'].groupby(axis=1, level=0).sum()
    genstorcap = dfs['pras_system']['genstorcap'].groupby(axis=1, level=0).sum()
    cap = pd.concat([gencap, storcap, genstorcap], axis=1)
    ## Drop any empties
    cap = cap.replace(0,np.nan).dropna(axis=1, how='all').fillna(0).astype(int)
    ## Get the colors
    tech_map = dfs['tech_map']
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    tech_style = dfs['tech_style']
    ## Aggregate by type
    cap.columns = cap.columns.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).str.lower()
    cap.columns = (
        cap.columns
        .map(lambda x: [i for i in tech_map.index if x.startswith(i)][0])
        .map(lambda x: tech_map.get(x,x))
    )
    cap.columns
    cap = cap.groupby(axis=1, level=0).sum()
    order = [c for c in tech_style.index if c in cap]
    cap = cap[order]
    if cap.shape[1] != len(order):
        raise Exception(f"missing colors: {cap.columns}, {tech_style}")
    ## Cumulate for plot
    cumcap = cap.cumsum(axis=1)[order[::-1]]
    load = dfs['pras_system']['load'].sum(axis=1)

    ### Plot it
    years = list(range(2007,2014))
    for y in years:
        savename = f"B1-PRAS-ICAP-w{y}-{sw['t']}.png"
        plt.close()
        f,ax = plots.plotyearbymonth(
            load.loc[str(y)],
            colors=['k'], style='line', lwforline=1,
        )
        plots.plotyearbymonth(
            cumcap.loc[str(y)], colors=[tech_style[c] for c in cumcap],
            f=f, ax=ax,
        )
        ## Legend
        leg = ax[0].legend(
            loc='upper left', bbox_to_anchor=(1,1.25),
            fontsize=11, frameon=False, ncol=1,
            columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        )
        leg.set_title(f'ICAP {y}', prop={'size':'large'})
        ## Save it
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_augur_pras_capacity(sw, dfs):
    """
    Plot the nameplate capacity from Augur and PRAS to check consistency
    """
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    savename = f"B1-PRAS-Augur-capacity-{sw['t']}.png"
    ### Get the colors
    tech_style = dfs['tech_style']
    ### Collect the PRAS system capacities
    gencap = dfs['pras_system']['gencap']
    storcap = dfs['pras_system']['storcap']
    genstorcap = dfs['pras_system']['genstorcap']
    load = dfs['pras_system']['load'] / 1e3
    cap = {}
    cap['pras'] = pd.concat([gencap, storcap, genstorcap], axis=1) / 1e3
    ## Drop any empties
    cap['pras'] = cap['pras'].replace(0,np.nan).dropna(axis=1, how='all').fillna(0)
    ## Aggregate by type
    cap['pras'] = (
        group_techs(cap['pras'], dfs, technamecol='wide')
        .groupby(axis=1, level=[1,0]).sum().max().rename('MW')
    )

    ### Collect the Augur capacities
    cap['augur'] = dfs['max_cap'].groupby(['i','r'], as_index=False).MW.sum()
    ## Convert from s to p regions
    cap['augur'].r = cap['augur'].r
    ## Aggregate by type
    cap['augur'] = (
        group_techs(cap['augur'], dfs, technamecol='i')
        .replace({'i':{'hydro_new':'hydro', 'hydro_exist':'hydro'}})
        .groupby(['r','i']).MW.sum() / 1e3
    )

    ### Drop VRE since its capacity is handled differently
    for datum in cap:
        cap[datum] = (
            cap[datum].loc[
                ~cap[datum].index.get_level_values('i').isin(
                    dfs['vre_gen_usa'].columns.tolist())
            ]
        )

    ### Get coordinates
    zones = dfs['hierarchy'].index
    ncols = int(np.around(np.sqrt(len(zones)) * 1.618, 0))
    nrows = len(zones) // ncols + int(bool(len(zones) % ncols))
    coords = dict(zip(zones, [(row,col) for row in range(nrows) for col in range(ncols)]))

    ### Plot the capacities
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(1.2*ncols, 1.2*nrows), sharex=True,
        gridspec_kw={'wspace':0.6, 'hspace':0.5}
    )
    alltechs = set()
    for r in zones:
        df = pd.concat({'A':cap['augur'].loc[r], 'P':cap['pras'].loc[r]}, axis=1).T
        order = [c for c in tech_style.index if c in df]
        missing = [c for c in df if c not in order]
        if len(missing):
            print(f'WARNING: Missing colors for these techs: {missing}')
        df = df[order].copy()
        alltechs.update(df.columns.tolist())
        plots.stackbar(df=df, ax=ax[coords[r]], colors=tech_style, net=False, width=0.8)
        ### Formatting
        ax[coords[r]].set_title(r)
        ax[coords[r]].set_xticks([0,1])
        ax[coords[r]].set_xticklabels(['A','P'])
        ### Legend
        if r == zones[-1]:
            handles = [
                mpl.patches.Patch(facecolor=tech_style[i], edgecolor='none', label=i)
                for i in [j for j in tech_style.index if j in alltechs]
            ][::-1]
            ax[coords[r]].legend(
                handles=handles, loc='center left', bbox_to_anchor=(1,0.5),
                frameon=False, columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
                ncol=len(alltechs)//3,
            )
    ### Formatting
    plots.trim_subplots(ax=ax, nrows=nrows, ncols=ncols, nsubplots=len(zones))
    ax[-1, 0].set_ylabel('Nameplate capacity [GW]', y=0, ha='left')
    plots.despine(ax)
    ## Save it
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_pras_ICAP_regional(sw, dfs, numdays=5):
    """
    Plot the available capacity used in PRAS without any outages
    """
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    ### Get the peak dropped-load periods
    import plots
    dropped = dfs['pras']['USA_EUE'].copy()
    dropped = dropped.groupby(
        [dropped.index.year, dropped.index.month, dropped.index.day]
    ).sum().nlargest(numdays).replace(0,np.nan).dropna()

    ### Collect the PRAS system capacities
    gencap = dfs['pras_system']['gencap']
    storcap = dfs['pras_system']['storcap']
    genstorcap = dfs['pras_system']['genstorcap']
    load = dfs['pras_system']['load'] / 1e3
    cap = pd.concat([gencap, storcap, genstorcap], axis=1) / 1e3
    ## Drop any empties
    cap = cap.replace(0,np.nan).dropna(axis=1, how='all').fillna(0)
    ## Get the colors
    tech_map = dfs['tech_map']
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    tech_style = dfs['tech_style']
    ## Aggregate by type
    def renamer(x):
        out = (x if x[0].startswith('battery')
               else (x[0].strip('_01234567890*').lower(), x[1]))
        return out
    cap.columns = cap.columns.map(renamer)
    cap.columns = (
        cap.columns
        .map(lambda x: ([i for i in tech_map.index if x[0].startswith(i)][0], x[1]))
        .map(lambda x: (tech_map.get(x[0],x[0]), x[1]))
    )
    cap = cap.groupby(axis=1, level=[1,0]).sum()

    ### Get coordinates
    zones = dfs['hierarchy'].index
    ncols = int(np.around(np.sqrt(len(zones)) * 1.618, 0))
    nrows = len(zones) // ncols + int(bool(len(zones) % ncols))
    coords = dict(zip(zones, [(row,col) for row in range(nrows) for col in range(ncols)]))

    ### Plot the highest-EUE days
    for day in range(len(dropped)):
        date = '{}-{:>02}-{:>02}'.format(*dropped.index[day])
        savename = f"B1-PRAS-ICAP-{sw['t']}-{date.replace('-','')}.png"
        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(1.2*ncols, 1.2*nrows), sharex=True,
            gridspec_kw={'wspace':0.6, 'hspace':0.5}
        )
        for r in zones:
            df = cap.loc[date][r].copy()
            ### Cumulate for plot
            order = [c for c in tech_style.index if c in df]
            df = df[order]
            ### Plot it
            plots.stackbar(
                df=df, ax=ax[coords[r]], colors=tech_style, net=False, align='edge')
            ax[coords[r]].plot(range(len(df)), load.loc[date][r].values, c='k', lw=1)
            ### Formatting
            ax[coords[r]].set_title(r)
        ### Formatting
        plots.trim_subplots(ax=ax, nrows=nrows, ncols=ncols, nsubplots=len(zones))
        ax[coords[zones[0]]].set_xlim(0,24)
        ax[coords[zones[0]]].set_xticks([])
        ax[-1, 0].set_xlabel(date, x=0, ha='left', labelpad=10)
        ax[-1, 0].set_ylabel('ICAP [GW]', y=0, ha='left')
        plots.despine(ax)
        ## Save it
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_pras_unitsize_distribution(sw, dfs):
    """
    Distribution of PRAS unit sizes by tech
    """
    if not len(dfs['pras_system']):
        print('PRAS system was not loaded')
        return
    savename = f"B1-PRAS-unitcap-{sw['t']}.png"
    import plots
    gencap = dfs['pras_system']['gencap']
    storcap = dfs['pras_system']['storcap']
    genstorcap = dfs['pras_system']['genstorcap']
    cap = (
        pd.concat([gencap, storcap, genstorcap], axis=1)
        .max().rename('MW').reset_index()
    )
    ## Get the colors
    tech_map = dfs['tech_map'].copy()
    tech_map.index = tech_map.index.str.lower()
    tech_map = tech_map.str.lower()
    tech_style = dfs['tech_style'].copy()
    ## Aggregate by type
    cap.i = cap.i.map(
        lambda x: x if x.startswith('battery') else (x.strip('_01234567890*').lower()))
    cap.i = (
        cap.i
        .map(lambda x: tech_map.get(x,x))
        .map(lambda x: ([i for i in tech_map.drop('hyd').index if x.startswith(i)]+[x])[0])
    )
    if 'new_blank_genstor' in cap.i.values:
        if (cap.loc[cap.i=='new_blank_genstor','MW'] == 0).all():
            cap = cap.loc[cap.i != 'new_blank_genstor'].copy()

    techs = cap.i.unique()
    nondisaggtechs = (
        dfs['vre_gen_usa'].columns.tolist()
        + ['hydro_exist']
        + [i for i in techs if i.startswith('battery')]
        + [i for i in techs if (('canada' in i.lower()) or ('can-imports' in i.lower()))]
    )
    order = [i for i in tech_style.index if i in techs]
    others = [i for i in techs if ((i not in order) and (i not in nondisaggtechs))]
    for i in others:
        tech_style[i] = 'k'

    plt.close()
    f,ax = plt.subplots(1,2,figsize=(7,3.75))
    for i in (order+others)[::-1]:
        df = cap.loc[cap.i==i]
        col = 1 if i in nondisaggtechs else 0
        ax[col].plot(
            range(len(df)), df.MW.sort_values().values, c=tech_style[i], label=i)
        ax[col].annotate(
            f' {i}', (len(df), df.MW.max()), fontsize=10,
        )
    for col in range(2):
        ax[col].set_ylabel('Unit size [MW]')
        ax[col].set_xlabel('Number of units')
        ax[col].set_xlim(0)
        ax[col].set_ylim(0)
        ax[col].legend(
            ncol=1, columnspacing=0.5, frameon=False,
            handletextpad=0.3, handlelength=0.7,
            loc='upper center', bbox_to_anchor=(0.5,-0.2))
    ax[0].set_title('Disaggregated techs')
    ax[1].set_title('Aggregated techs (PRAS FOR=0)')
    plots.despine(ax)
    ## Save it
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_b1_prices(sw, dfs):
    """
    Osprey energy prices, pre-startup-cost adder
    """
    if dfs['prices'].empty:
        return
    import plots
    savename = f"B1-prices-MAXmax-wYEAR-{sw['t']}.png"
    ### Plot it
    for y in sw['osprey_years']:
        for ymax in [100, int(dfs['prices'].max().max())]:
            plt.close()
            f,ax = plots.plotyearbymonth(
                dfs['prices'].loc[str(y)], style='line', lwforline='0.25', dpi=dpi,
            )
            # for row in range(12):
            #     ax[row].axhline(0,c='k',ls=':',lw=0.5)
            ax[0].set_ylim(0,ymax)
            ax[0].set_title(
                '({}) (y = {:.0f}–{:.0f} $/MWh)'.format(
                    sw['t'],
                    dfs['prices'].min().min(), ymax))
            if savefig: plt.savefig(os.path.join(
                sw['savepath'],savename.replace('MAX',str(ymax)).replace('YEAR',str(y))
            ))
            if interactive: plt.show()
            plt.close()


def plot_b1_price_duration(sw, dfs):
    """
    Osprey energy price duration, pre-startup-cost adder
    """
    if dfs['prices'].empty:
        return
    import plots
    for yscale in ['linear','log']:
        savename = f"B1-price_duration-{yscale}-{sw['t']}.png"

        plt.close()
        f,ax = plt.subplots(dpi=dpi)
        for r in dfs['prices']:
            ax.plot(
                np.linspace(0,100,len(dfs['prices'])),
                dfs['prices'][r].sort_values(ascending=False).values,
                label=r, lw=0.5,
            )
        ax.set_ylabel('Osprey price [2004$/MWh]')
        ax.set_xlabel(
            f"Percent of dispatch period ({min(sw['osprey_years'])}–{max(sw['osprey_years'])}) [%]")
        ax.set_title(sw['t'])
        ax.set_xlim(0,100)
        ax.set_yscale(yscale)
        ax.set_ylim((None if yscale == 'linear' else 0.1), None)
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5))
        ax.axhline(0,c='0.5',lw=0.5,ls='--')
        plots.despine(ax)
        if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
        if interactive: plt.show()
        plt.close()


def plot_b1_co2emissions(sw, dfs):
    """
    CO2 emissions
    """
    import plots
    savename = f"B1-CO2emissions-{sw['t']}.png"

    ###### Load the data
    emit_rate = pd.read_csv(
        os.path.join(sw['casedir'],'ReEDS_Augur','augur_data','emit_rate_{}.csv'.format(sw['t']))
    ) ### ton/MWh
    emit_rate = (
        emit_rate
        .loc[emit_rate.e=='CO2'].drop(['e'],axis=1)
        .set_index(['i','v','r'])
        .emit_rate
    )

    co2_emissions = (
        dfs['gen']
        .set_index(['d','hr','i','v','r'])
        .unstack(['i','v','r']).fillna(0)
        .loc[dfs['h_dt_szn'].loc[dfs['h_dt_szn'].year==2007,['d','hr']].values.tolist()]
        .set_index(dfs['timeindex'])['Val']
        # .T
        * emit_rate
    ).dropna(axis=1, how='all').sum(axis=1,level='i')

    negcols = co2_emissions.sum().loc[co2_emissions.sum() < 0].index.values
    poscols = [c for c in co2_emissions if c not in negcols]
    df = co2_emissions.sum(axis=1).cumsum()/1E6

    ###### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(12,3.75))
    # ax.fill_between(df.index, df.values)
    df.plot(ax=ax, color='C5', zorder=6, label='Cumulative [MT]')
    ax.fill_between(
        df.index, (co2_emissions[poscols].sum(axis=1).values/1E3),
        color='C1', lw=0, label='Hourly, positive [kT]',
    )
    ax.fill_between(
        df.index, (co2_emissions[negcols].sum(axis=1).values/1E3),
        color='C0', lw=0, label='Hourly, negative [kT]',
    )
    # (co2_emissions[poscols].sum(axis=1)/1E3).plot(
    #     ax=ax, color='C3', lw=0.5, zorder=4, label='Hourly, positive [kT]')
    # (co2_emissions[negcols].sum(axis=1)/1E3).plot(
    #     ax=ax, color='C0', lw=0.5, zorder=3, label='Hourly, negative [kT]')
    ax.legend(frameon=False, handletextpad=0.5, handlelength=0.7, fontsize='large')
    ax.axhline(0,c='k',lw=0.75,ls='-',zorder=5)
    ax.set_ylabel('CO2 emissions')
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_a_meritorder(sw, dfs):
    """
    Osprey merit order curve
    """
    import plots
    savename = f"A-meritorder-{sw['t']}.png"

    ### Load capacity and gen cost
    gen_cap = (
        dfs['gdxreeds']['cap_ivrt'].loc[dfs['gdxreeds']['cap_ivrt'].t.astype(int)==sw['t']]
        .drop('t', axis=1).rename(columns={'Value':'MW'})
    )
    # gen_cap = gdxosprey['cap'].rename(columns={'Value':'MW'})
    gen_cap.i = gen_cap.i.map(
        lambda x: x if x.startswith('battery') else x.strip('_0123456789')).str.lower()
    gen_cap = gen_cap.loc[~gen_cap.i.isin(dfs['h2dac'].str.lower())]
    gen_cap = gen_cap.groupby(['i','v','r'], as_index=False).MW.sum()
    gen_cost = dfs['gdxosprey']['gen_cost'].rename(columns={'Value':'USDperMWh'})
    gen_cost.i = gen_cost.i.map(lambda x: x if x.startswith('battery') else x.strip('_0123456789'))
    gen_cost = gen_cost.groupby(['i','v','r'], as_index=False).USDperMWh.mean()
    ### The only missing costs are for pumped hydro
    ### But actually we probably shouldn't do any value-filling, since
    ### Osprey uses these (i,v,r) directly
    gen_cost_cap = gen_cap.merge(gen_cost, on=['i','v','r'], how='left').fillna(0)

    costcolors = {
        **dfs['tech_map'].map(dfs['tech_style']).to_dict(),
        **dfs['colors'],
    }
    gen_cost_cap['color'] = gen_cost_cap.i.map(costcolors)
    gen_cost_cap = gen_cost_cap.sort_values('USDperMWh')

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(7,3.75), dpi=dpi)
    ax.scatter(
        gen_cost_cap.MW.cumsum().values / 1000,
        gen_cost_cap.USDperMWh.values,
        c=gen_cost_cap.color.values,
        s=5,
    )
    # ax.bar(
    #     x=gen_cost_cap.MW.cumsum().values / 1000,
    #     height=gen_cost_cap.USDperMWh.values,
    #     width=gen_cost_cap.MW.values / 1000 + 1,
    #     color=gen_cost_cap.color.values,
    # )
    ax.set_ylabel('Cost [2004$/MWh]')
    ax.set_xlabel('Cumulative capacity [GW')
    ax.set_xlim(0)
    ax.set_ylim(0)
    ax.set_title(sw['t'])
    ## Legend
    handles = [
        mpl.patches.Patch(facecolor=costcolors[i], edgecolor='none', label=i)
        for i in gen_cost_cap.i.unique()
    ][::-1]
    ax.legend(
        handles=handles, loc='upper left', frameon=False,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        ncol=3,
    )
    plots.despine(ax, right=True)

    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_e_cc_mar(sw, dfs):
    """
    Marginal capacity credit
    """
    import plots
    param = 'cc_mar'
    savename = f"E-{param}-{sw['t']}.png"

    if not int(sw['GSw_PRM_CapCredit']):
        raise KeyError('No capacity credit values to plot')
    cc_results = gdxpds.to_dataframes(os.path.join(
        sw['casedir'],'ReEDS_Augur','augur_data',
        'ReEDS_Augur_{}.gdx'.format(sw['t'])
    ))

    dfplot = cc_results[param].drop('t',axis=1).copy()
    dfplot['tech'] = dfplot.i.map(lambda x: x.split('_')[0])
    techs = sorted(dfplot.tech.unique())
    numrows = len(techs)
    bootstrap = 5
    squeeze = 0.7
    ### Use seasons appropriate to resolution
    if 'wint' in dfplot.szn.values:
        seasons = ['wint','spri','summ','fall']
        histcolor = ['C0','C2','C1','C3']
        xticklabels = seasons
    elif 'szn' in dfplot.szn.values[0]:
        seasons = [f'szn{s}' for s in sorted(dfplot.szn.str.strip('szn').astype(int).unique())]
        histcolor = plots.rainbowmapper(seasons)
        xticklabels = [s.strip('szn') for s in seasons]
    else:
        seasons = dfplot.szn.unique()
        histcolor = plots.rainbowmapper(seasons)
        xticklabels = seasons

    plt.close()
    f,ax = plt.subplots(numrows, figsize=(6,8), sharex=True, sharey=True)
    for row, tech in enumerate(techs):
        df = dfplot.loc[(dfplot.tech==tech)].copy()
        ### Each observation in the histogram is a (i,r) pair
        df['i_r'] = df.i + '_' + df.r
        df = df.pivot(columns='szn',values='Value',index='i_r')[seasons]

        plots.plotquarthist(
            ax[row], df, histcolor=histcolor,
            bootstrap=bootstrap, density=True, squeeze=squeeze,
            pad=0.03,
        )

        ### Formatting
        ax[row].set_ylabel(tech)
        ax[row].yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1))
        ax[row].yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5))
        ax[row].set_ylim(0,1)

    ax[0].set_title('{} {}'.format(sw['t'], param),
                    weight='bold', fontsize='x-large')
    ax[-1].set_xticklabels(xticklabels, rotation=90)

    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_e_netloadhours_timeseries(sw, dfs):
    """
    Peak net load hours by ccreg
    """
    import plots
    savename = f"E-netloadhours-timeseries-{sw['t']}.png"

    ### Plot it
    years = range(2007,2014)
    ccregs = sorted(dfs['dfpeak'].columns)
    plt.close()
    f,ax = plt.subplots(len(years),1,sharex=False,sharey=True,figsize=(12,6))
    for row, year in enumerate(years):
        df = dfs['dfpeak'].loc[str(year)].cumsum(axis=1)[ccregs[::-1]]
        df.plot.area(
            ax=ax[row], color=dfs['peakcolors'], stacked=False, alpha=1,
            legend=False,
        )
        ax[row].annotate(
            year,(0.005,0.95),xycoords='axes fraction',ha='left',va='top',
            weight='bold',fontsize='large')
        if row < (len(years) - 1):
            ax[row].set_xticklabels([])
    h,l = ax[0].get_legend_handles_labels()
    ax[0].legend(
        h[::-1], l[::-1],
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        loc='upper left', bbox_to_anchor=(1,1), frameon=False, title='ccreg',
    )
    ax[3].set_ylabel('Net load peak instances [#]')
    # ax[-1].xaxis.set_major_locator(mpl.dates.MonthLocator())
    # ax[-1].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


def plot_e_netloadhours_histogram(sw, dfs):
    """
    histograms of peak net load occurrence
    """
    import plots
    savename = f"E-netloadhours-histogram-{sw['t']}.png"

    ### Plot it
    years = range(2007,2014)
    ccregs = sorted(dfs['dfpeak'].columns)
    plt.close()
    f,ax = plt.subplots(1,3,figsize=(12,3.75))
    ### hour
    dfs['dfpeak'].groupby(dfs['dfpeak'].index.hour).sum()[ccregs[::-1]].plot.bar(
        ax=ax[0], color=dfs['peakcolors'], stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[0].set_xlabel('Hour [EST]')
    ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(4))
    ax[0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))
    ax[0].tick_params(labelrotation=0)
    ### Month
    dfs['dfpeak'].groupby(dfs['dfpeak'].index.month).sum()[ccregs[::-1]].plot.bar(
        ax=ax[1], color=dfs['peakcolors'], stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[1].set_xlabel('Month')
    ax[1].tick_params(labelrotation=0)
    ### Year
    dfs['dfpeak'].groupby(dfs['dfpeak'].index.year).sum()[ccregs[::-1]].plot.bar(
        ax=ax[2], color=dfs['peakcolors'], stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[2].set_xlabel('Year')
    ax[2].set_xticks(range(len(years)))
    ax[2].set_xticklabels(
        years,
        rotation=35, ha='right', rotation_mode='anchor')
    # ax[2].tick_params(labelrotation=45)
    ### Formatting
    h,l = ax[2].get_legend_handles_labels()
    ax[2].legend(
        h[::-1], l[::-1],
        loc='center left', bbox_to_anchor=(1,0.5), frameon=False,
        title=sw['capcredit_hierarchy_level'],
        ncol=1, columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    ax[0].set_ylabel('Net peak load instances [#]')
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(sw['savepath'],savename))
    if interactive: plt.show()
    plt.close()


#%%### Main function
def main(sw, augur_plots=1):
    """
    augur_plots [0-3]: Indicate how many plots to make (higher number = more plots)
    """
    ### Local imports
    site.addsitedir(os.path.join(sw['reeds_path'],'postprocessing'))
    import plots
    plots.plotparams()

    #%% Get the inputs
    dfs = get_inputs(sw)

    #%% Make the plots
    try:
        plot_b1_dispatch_usa(sw, dfs)
    except Exception as err:
        print('plot_b1_dispatch_usa() failed:', err)

    try:
        plot_b1c1_profiles_usa(sw, dfs)
    except Exception as err:
        print('plot_b1c1_profiles_usa() failed:', err)

    try:
        plot_b1_load_duration(sw, dfs)
    except Exception as err:
        print('plot_b1_load_duration() failed:', err)

    try:
        plot_b1_netload_duration(sw, dfs)
    except Exception as err:
        print('plot_b1_netload_duration() failed:', err)

    try:
        plot_dispatch_maxmin_netload_weeks(sw, dfs)
    except Exception as err:
        print('plot_dispatch_maxmin_netload_weeks() failed:', err)

    try:
        plot_c1_curtailment_duration(sw, dfs)
    except Exception as err:
        print('plot_c1_curtailment_duration() failed:', err)

    try:
        plot_b1_dropped_load_timeseries(sw, dfs)
    except Exception as err:
        print('plot_b1_dropped_load_timeseries() failed:', err)

    try:
        plot_b1_dropped_load_timeseries_full(sw, dfs)
    except Exception as err:
        print('plot_b1_dropped_load_timeseries_full() failed:', err)

    try:
        plot_b1_dropped_load_duration(sw, dfs)
    except Exception as err:
        print('plot_b1_dropped_load_duration() failed:', err)

    try:
        map_dropped_load(sw, dfs)
    except Exception as err:
        print('map_dropped_load() failed:', err)

    try:
        plot_pras_ICAP_regional(sw, dfs)
    except Exception as err:
        print('plot_pras_ICAP_regional() failed:', err)

    try:
        plot_pras_unitsize_distribution(sw, dfs)
    except Exception as err:
        print('plot_pras_unitsize_distribution() failed:', err)

    try:
        plot_b1_price_duration(sw, dfs)
    except Exception as err:
        print('plot_b1_price_duration() failed:', err)

    try:
        plot_b1_co2emissions(sw, dfs)
    except Exception as err:
        print('plot_b1_co2emissions() failed:', err)

    try:
        plot_e_cc_mar(sw, dfs)
    except Exception as err:
        print('plot_e_cc_mar() failed:', err)

    try:
        plot_e_netloadhours_timeseries(sw, dfs)
    except Exception as err:
        print('plot_e_netloadhours_timeseries() failed:', err)

    try:
        plot_e_netloadhours_histogram(sw, dfs)
    except Exception as err:
        print('plot_e_netloadhours_histogram() failed:', err)

    if int(sw['GSw_H2']) or int(sw['GSw_DAC']):
        try:
            plot_b1_h2dac_load_timeseries(sw, dfs)
        except Exception as err:
            print('plot_b1_h2dac_load_timeseries() failed:', err)

    if augur_plots >= 2:
        try:
            plot_augur_pras_capacity(sw, dfs)
        except Exception as err:
            print('plot_augur_pras_capacity() failed:', err)

        try:
            plot_pras_ICAP(sw, dfs)
        except Exception as err:
            print('plot_pras_ICAP() failed:', err)

        try:
            plot_netload_profile(sw, dfs)
        except Exception as err:
            print('plot_netload_profile() failed:', err)

        try:
            plot_a_meritorder(sw, dfs)
        except Exception as err:
            print('plot_a_meritorder() failed:', err)

        try:
            plot_b1_storage_energy(sw, dfs)
        except Exception as err:
            print('plot_b1_storage_energy() failed:', err)

        try:
            plot_c1_load_netload_curtailment_profile(sw, dfs)
        except Exception as err:
            print('plot_c1_load_netload_curtailment_profile() failed:', err)

        try:
            plot_b1_prices(sw, dfs)
        except Exception as err:
            print('plot_b1_prices() failed:', err)

    if augur_plots >= 3:
        try:
            plot_c1_curtailment_timeseries(sw, dfs)
        except Exception as err:
            print('plot_c1_curtailment_timeseries() failed:', err)


#%%### PROCEDURE
if __name__ == '__main__':
    #%%### ARGUMENT INPUTS
    import argparse
    parser = argparse.ArgumentParser(
        description='Create the necessary 8760 and capacity factor data for hourly resolution')
    parser.add_argument('--reeds_path', help='ReEDS-2.0 directory')
    parser.add_argument('--casedir', help='ReEDS-2.0/runs/{case} directory')
    parser.add_argument('--t', type=int, default=2050, help='solve year to plot')
    parser.add_argument('--iteration', '-i', type=int, default=-1,
                        help='iteration to plot (default of -1 means latest iteration)')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    casedir = args.casedir
    t = args.t
    iteration = args.iteration

    # #%%### Inputs for debugging
    # reeds_path = os.path.expanduser('~/github2/ReEDS-2.0/')
    # casedir = os.path.join(reeds_path,'runs','v20230414_prasM1_WECCh2_SP_sh4msp30_so1slaMspy2')
    # casedir = (
    #     '/Volumes/ReEDS/FY22-NTP/Candidates/Archive/ReEDSruns/20230512/'
    #     'v20230512_ntpH0_AC_DemMd_90by2035EP__core')
    # t = 2035
    # interactive = True
    # iteration = -1
    # sw['reeds_path'] = reeds_path
    # sw['casedir'] = casedir

    #%%### INPUTS
    ### Switches
    sw = functions.get_switches(casedir)
    sw['t'] = t

    ### Run for the latest iteration
    if iteration < 0:
        sw['iteration'] = int(
            os.path.splitext(
                sorted(glob(os.path.join(sw.casedir,'lstfiles',f'*{sw.t}i*.lst')))[-1]
            )[0]
            .split(f'{sw.t}i')[-1]
        )
    else:
        sw['iteration'] = iteration

    ### Make the plots if it's a plot year
    if t in sw['plot_years']:
        print('plotting intermediate Augur results...')
        ## Local imports
        site.addsitedir(os.path.join(sw['reeds_path'],'postprocessing'))
        import plots
        plots.plotparams()
        # tic = datetime.datetime.now()
        try:
            main(sw)
        except Exception as err:
            print('G_plots.py failed with the following exception:')
            print(err)
        # functions.toc(tic=tic, year=t, process='ReEDS_Augur/G_plots.py')

    ### Remove intermediate csv files to save drive space
    if not int(sw['keep_augur_files']):
        functions.delete_csvs(sw)
