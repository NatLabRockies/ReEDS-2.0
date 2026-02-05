"""
This script gathers supply curve data for on/offshore wind, upv, csp, hydro, and
psh into a single inputs_case file, rsc_combined.csv. 

This script contains additional procedures for gathering geothermal supply curve data
and EV managed charging supply curve data, and spurline supply curve data
into various separate inputs_case files.
"""

# %% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import numpy as np
import os
import sys
import h5py
import datetime
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
reeds_path = reeds.io.reeds_path

# %%#################
### FIXED INPUTS ###

### Number of bins used for everything other than wind and PV
numbins_other = 5
### Rounding precision
decimals = 7
### spur_cutoff [$/MW]: Cutoff for spur line costs; clip cost for sites with larger costs
spur_cutoff = 1e7

# %% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================
def wm(df):
    """Make a function to take the capacity-weighted average in a .groupby() call"""
    def _wm(x):
        return np.average(
            x,
            weights=(
                df.loc[x.index, 'capacity']
                if df.loc[x.index, 'capacity'].sum() > 0
                else 0
            )
        )
    return _wm


def get_exog_cap(inputs_case, tech, dfsc):
    """Get exogenous capacity by class, region, rscbin, and year"""
    dfexog = (
        pd.read_csv(os.path.join(inputs_case, f'exog_cap_{tech}.csv'))
        .merge(
            dfsc.explode('sc_point_gid').reset_index()[['sc_point_gid','bin']],
            on='sc_point_gid',
        )
        .rename(columns={'capacity':'MW'})
    )
    dfexog['rscbin'] = dfexog['bin'].map('bin{}'.format)
    dfexog = dfexog.groupby(['*tech', 'region', 'rscbin', 'year']).MW.sum()
    return dfexog


def agg_supplycurve(
    scpath,
    inputs_case,
    numbins_tech,
    agglevel,
    AggregateRegions,
    bin_method='equal_cap_cut',
    bin_col='supply_curve_cost_per_mw',
    spur_cutoff=1e7, 
    agglevel_variables=None,
    deflate=None,
    sw=None,
    write=False,
):
    """
    """
    ### Get inputs
    dfin = reeds.io.assemble_supplycurve(
        scfile=scpath,
        case=os.path.dirname(os.path.normpath(inputs_case)),
        agg=AggregateRegions,
    ).reset_index().drop(columns=['FIPS','cf'], errors='ignore')
    ## Convert dollar year and recalculate total cost
    transcost_cols = [c for c in dfin if 'cost' in c]
    dfin.loc[:, transcost_cols] *= deflate['interconnection']
    deflate_scen = os.path.splitext(os.path.basename(scpath))[0]
    dfin['capital_adder_per_mw'] *= deflate[deflate_scen]
    dfin['supply_curve_cost_per_mw'] = dfin[
        ['capital_adder_per_mw', 'cost_total_trans_usd_per_mw']
    ].sum(axis=1)
    ### Define the aggregation settings
    ## Cost and distance are weighted averages, with capacity as the weighting factor
    aggs = {'capacity': 'sum', 'sc_point_gid': list}
    index_cols = ['region', 'class', 'bin']
    aggs = {
        col: aggs.get(col, wm(dfin)) for col in dfin
        if col not in index_cols
    }

    ### Assign bins
    if dfin.empty:
        dfin['bin'] = []
    else: 
        dfin = (
            dfin
            .groupby(['region','class'], sort=False, group_keys=True)
            .apply(reeds.inputs.get_bin, numbins_tech, bin_method, bin_col)
            .reset_index(drop=True)
            .sort_values('sc_point_gid')
        )
    ### Aggregate it
    dfout = dfin.groupby(index_cols).agg(aggs)
    ### Clip negative costs and costs above cutoff
    dfout.supply_curve_cost_per_mw = dfout.supply_curve_cost_per_mw.clip(lower=0, upper=spur_cutoff)

    return dfin, dfout


# %% ============================================================================
### --- MAIN FUNCTION ---
### ============================================================================


def main(
    reeds_path, inputs_case, AggregateRegions=1, rsc_wsc_dat=None, write=True, **kwargs
):
    # #%% Settings for testing
    # reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # inputs_case = os.path.join(reeds_path,'runs','v20251209_scM0_Pacific','inputs_case')
    # AggregateRegions = 1
    # rsc_wsc_dat = None
    # write = True
    # kwargs = {}

    #%% Inputs from switches
    sw = reeds.io.get_switches(inputs_case)
    ### Overwrite switches with keyword arguments
    for kw, arg in kwargs.items():
        sw[kw] = arg
    endyear = int(sw.endyear)
    startyear = int(sw.startyear)
    geohydrosupplycurve = sw.geohydrosupplycurve
    egssupplycurve = sw.egssupplycurve
    egsnearfieldsupplycurve = sw.egsnearfieldsupplycurve
    pshsupplycurve = sw.pshsupplycurve
    numbins = {
        "upv": int(sw.numbins_upv),
        "wind-ons": int(sw.numbins_windons),
        "wind-ofs": int(sw.numbins_windofs),
        "csp": int(sw.numbins_csp),
        "geohydro": int(sw.numbins_geohydro_allkm),
        "egs": int(sw.numbins_egs_allkm),
    }

    # Use agglevel_variables function to obtain spatial resolution variables 
    agglevel_variables  = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)
    agglevel = agglevel_variables['agglevel']

    val_r_all = pd.read_csv(
        os.path.join(inputs_case,'val_r_all.csv'), header=None).squeeze(1).tolist()
    # Read in tech-subset-table.csv to determine number of csp configurations
    tech_subset_table = pd.read_csv(os.path.join(inputs_case, "tech-subset-table.csv"))
    csp_configs = tech_subset_table.loc[
        (tech_subset_table.CSP == "YES") & (tech_subset_table.STORAGE == "YES")
    ].shape[0]

    # Read in dollar year conversions for RSC data
    dollaryear = pd.read_csv(
        os.path.join(inputs_case, 'dollaryear_sc.csv'), index_col='Scenario',
    ).squeeze(1)
    ## Interconnection cost dollar year is stored as metadata
    fpath_interconnection = os.path.join(
        reeds_path, 'inputs', 'supply_curve', 'interconnection_land.h5'
    )
    with h5py.File(fpath_interconnection, 'r') as f:
        dollaryear['interconnection'] = f['data'].attrs['dollaryear']
    deflator = pd.read_csv(
        os.path.join(inputs_case, 'deflator.csv'), index_col='*Dollar.Year',
    ).squeeze(1)
    deflate = dollaryear.map(deflator).rename('Deflator')

    #%% Load the existing RSC capacity (PV plants, wind, and CSP) if not provided in main function call
    if rsc_wsc_dat is None:
        # writesupplycurves.py is being run as a main input processing script
        rsc_wsc = pd.read_csv(os.path.join(inputs_case, "rsc_wsc.csv"))
    else:
        # writesupplycurves.py is being passed rsc_wsc data from an aggregate_regions.py call
        rsc_wsc = rsc_wsc_dat.copy()

    for j, row in rsc_wsc.iterrows():
        # Group CSP tech
        if row["i"] in ["csp-ws"]:
            rsc_wsc.loc[j, "i"] = "csp"
    rsc_wsc = rsc_wsc.groupby(["r", "i"]).sum().reset_index()
    rsc_wsc.i = rsc_wsc.i.str.lower()

    if len(rsc_wsc.columns) < 3:
        rsc_wsc["value"] = ""
        rsc_wsc.columns = ["r", "tech", "exist"]

    else:
        rsc_wsc.columns = ["r", "tech", "exist"]

    ### Change the units
    rsc_wsc.exist /= 1000
    tout = rsc_wsc.copy()

    # %% Load supply curve files ---------------------------------------------------------

    alloutcap_list = []
    alloutcost_list = []
    spurout_list = []

    # %%#################
    #    -- Wind --    #
    ####################

    windin, wind = {}, {}
    cost_components_wind_list = []
    wind_types = ["ons"]
    if int(sw["GSw_OfsWind"]):
        wind_types.append("ofs")

    for s in wind_types:
        windin[s], wind[s] = agg_supplycurve(
            scpath=os.path.join(inputs_case,f'supplycurve_wind-{s}.csv'),
            inputs_case=inputs_case, 
            agglevel=agglevel, AggregateRegions=AggregateRegions, 
            numbins_tech=numbins[f'wind-{s}'], spur_cutoff=spur_cutoff,
            agglevel_variables=agglevel_variables, deflate=deflate,
            sw=sw, write=write
            )
        
        cost_components = (
            wind[s][["cost_total_trans_usd_per_mw", "capital_adder_per_mw"]]
            .round(2)
            .reset_index()
            .rename(
                columns={
                    "region": "r",
                    "class": "*i",
                    "bin": "rscbin",
                    "cost_total_trans_usd_per_mw": "cost_trans",
                    "capital_adder_per_mw": "cost_cap",
                }
            )
        )

        cost_components["*i"] = f"wind-{s}_" + cost_components[
            "*i"
        ].astype(str)
        cost_components["rscbin"] = "bin" + cost_components[
            "rscbin"
        ].astype(str)
        cost_components = pd.melt(
            cost_components,
            id_vars=["*i", "r", "rscbin"],
            var_name="sc_cat",
            value_name="value",
        )
        cost_components_wind_list.append(cost_components)

        spurout_list.append(
            wind[s]
            .reset_index()
            .assign(i=f"wind-{s}_" + wind[s].reset_index()["class"].astype(str))
            .assign(rscbin="bin" + wind[s].reset_index()["bin"].astype(str))
            .rename(columns={"region": "r"})
        )

    cost_components_wind = pd.concat(cost_components_wind_list)
    windall = (
        pd.concat(wind, axis=0)
        .reset_index(level=0)
        .rename(columns={"level_0": "tech"})
        .reset_index()
    )
    ### Normalize formatting
    windall["tech"] = "wind-" + windall["tech"]
    windall.supply_curve_cost_per_mw = windall.supply_curve_cost_per_mw.round(2)
    windall["class"] = "class" + windall["class"].astype(str)
    windall["bin"] = "wsc" + windall["bin"].astype(str)
    ### Pivot, with bins in long format
    bins_wind = list(range(1, max(numbins["wind-ons"], numbins["wind-ofs"]) + 1))
    windcost = (
        windall.pivot(
            index=["region", "class", "tech"],
            columns="bin",
            values="supply_curve_cost_per_mw",
        )
        .fillna(0)
        .reset_index()
    )
    windcost.rename(
        columns={"wsc{}".format(i): "bin{}".format(i) for i in bins_wind},
        inplace=True,
    )
    alloutcost_list.append(windcost)

    windcap = (
        windall.pivot(
            index=["region", "class", "tech"], columns="bin", values="capacity"
        )
        .fillna(0)
        .reset_index()
    )
    windcap.rename(
        columns={"wsc{}".format(i): "bin{}".format(i) for i in bins_wind},
        inplace=True,
    )
    alloutcap_list.append(windcap)

    if write:
        ## Exogenous wind capacity
        dfwindexog = get_exog_cap(inputs_case, tech='wind-ons', dfsc=wind['ons'])
        dfwindexog.round(3).to_csv(os.path.join(inputs_case, "exog_wind_ons_rsc.csv"))

    # %%###############
    #    -- PV --    #
    ##################

    upvin, upv = agg_supplycurve(
        scpath=os.path.join(inputs_case, 'supplycurve_upv.csv'),
        inputs_case=inputs_case,
        agglevel=agglevel, AggregateRegions=AggregateRegions,
        numbins_tech=numbins['upv'], spur_cutoff=spur_cutoff,
        agglevel_variables=agglevel_variables, deflate=deflate,
        sw=sw, write=write
        )

    # Similar to wind, save the trans vs cap components and then concatenate them below just
    # before outputting rsc_combined.csv
    cost_components_upv = (
        upv[["cost_total_trans_usd_per_mw", "capital_adder_per_mw"]].round(2).reset_index()
    )
    cost_components_upv = cost_components_upv.rename(
        columns={
            "region": "r",
            "class": "*i",
            "bin": "rscbin",
            "cost_total_trans_usd_per_mw": "cost_trans",
            "capital_adder_per_mw": "cost_cap",
        }
    )
    cost_components_upv["*i"] = "upv_" + cost_components_upv["*i"].astype(str)
    cost_components_upv["rscbin"] = "bin" + cost_components_upv["rscbin"].astype(str)
    cost_components_upv = pd.melt(
        cost_components_upv,
        id_vars=["*i", "r", "rscbin"],
        var_name="sc_cat",
        value_name="value",
    )

    if write:    
        ## Exogenous UPV capacity
        dfupvexog = get_exog_cap(inputs_case, tech='upv', dfsc=upv)
        dfupvexog.round(3).to_csv(os.path.join(inputs_case, "exog_upv_rsc.csv"))

    ### Normalize formatting
    upv = upv.reset_index()
    upv["class"] = "class" + upv["class"].astype(str)
    upv["bin"] = "upvsc" + upv["bin"].astype(str)

    spurout_list.append(
        upv.assign(i="upv_" + upv["class"].astype(str).str.strip("class"))
        .assign(rscbin="bin" + upv["bin"].str.strip("upvsc"))
        .rename(columns={"region": "r"})
    )

    ### Pivot, with bins in long format
    bins_upv = list(range(1, numbins["upv"] + 1))
    upvcost = (
        upv.pivot(
            columns="bin", values="supply_curve_cost_per_mw", index=["region", "class"]
        ).fillna(0)
        ### reV spur line and reinforcement costs are now in per MW-AC terms, so removing the
        ### correction term that was applied.
        .assign(tech="upv")
    ).reset_index()
    upvcost.rename(
        columns={"upvsc{}".format(i): "bin{}".format(i) for i in bins_upv},
        inplace=True,
    )
    alloutcost_list.append(upvcost)

    upvcap = (
        upv.pivot(columns="bin", values="capacity", index=["region", "class"])
        .fillna(0)
        .reset_index()
        .assign(tech="upv")
    )
    upvcap.rename(
        columns={"upvsc{}".format(i): "bin{}".format(i) for i in bins_upv},
        inplace=True,
    )
    alloutcap_list.append(upvcap)

    # %%################
    #    -- CSP --    #
    ###################

    if int(sw["GSw_CSP"]):
        cspin, csp = agg_supplycurve(
            scpath=os.path.join(inputs_case, 'supplycurve_csp.csv'),
            inputs_case=inputs_case,
            agglevel=agglevel, AggregateRegions=AggregateRegions, 
            numbins_tech=numbins['csp'], spur_cutoff=spur_cutoff,
            agglevel_variables=agglevel_variables, deflate=deflate,
            sw=sw, write=False
        )

        ### Normalize formatting
        csp = csp.reset_index()
        csp["class"] = "class" + csp["class"].astype(str)
        csp["bin"] = "cspsc" + csp["bin"].astype(str)

        spurout_list.append(
            csp.assign(i="csp_" + csp["class"].astype(str).str.strip("class"))
            .assign(rscbin="bin" + csp["bin"].str.strip("cspsc"))
            .rename(columns={"region": "r"})
        )

        ### Pivot, with bins in long format
        cspcost = (
            csp.pivot(
                columns="bin", values="supply_curve_cost_per_mw", index=["region", "class"]
            ).fillna(0)
        ).reset_index()
        cspcap = (
            csp.pivot(columns="bin", values="capacity", index=["region", "class"])
            .fillna(0)
            .reset_index()
        )

        ## Duplicate the CSP supply curve for each CSP configuration
        bins_csp = list(range(1, numbins["csp"] + 1))
        cspcap = (
            pd.concat(
                {"csp{}".format(i): cspcap for i in range(1, csp_configs + 1)}, axis=0
            )
            .reset_index(level=0)
            .rename(columns={"level_0": "tech"})
            .reset_index(drop=True)
        )
        cspcap.rename(
            columns={"cspsc{}".format(i): "bin{}".format(i) for i in bins_csp},
            inplace=True,
        )
        alloutcap_list.append(cspcap)
        
        cspcost = (
            pd.concat(
                {"csp{}".format(i): cspcost for i in range(1, csp_configs + 1)}, axis=0
            )
            .reset_index(level=0)
            .rename(columns={"level_0": "tech"})
            .reset_index(drop=True)
        )
        cspcost.rename(
            columns={"cspsc{}".format(i): "bin{}".format(i) for i in bins_csp},
            inplace=True,
        )
        alloutcost_list.append(cspcost)

    # %% Geothermal
    if int(sw["GSw_Geothermal"]):
        use_geohydro_rev_sc = (geohydrosupplycurve == "reV")
        use_egs_rev_sc = (egssupplycurve == "reV")
    else:
        use_geohydro_rev_sc = False
        use_egs_rev_sc = False

    ## reV supply curves
    if use_geohydro_rev_sc or use_egs_rev_sc:
        geoin, geo = {}, {}
        rev_geo_types = []
        if use_geohydro_rev_sc:
            rev_geo_types.append("geohydro")
        if use_egs_rev_sc:
            rev_geo_types.append("egs")
        for s in rev_geo_types:
            geoin[s], geo[s] = agg_supplycurve(
                scpath=os.path.join(
                    inputs_case,
                    f'supplycurve_{s}.csv'),
                numbins_tech=numbins[s], inputs_case=inputs_case,
                agglevel=agglevel, AggregateRegions=AggregateRegions,
                spur_cutoff=spur_cutoff,agglevel_variables=agglevel_variables, deflate=deflate,
                sw=sw, write=False
            )
            spurout_list.append(
                geo[s]
                .reset_index()
                .assign(i=f"{s}_allkm_" + geo[s].reset_index()["class"].astype(str))
                .assign(rscbin="bin" + geo[s].reset_index()["bin"].astype(str))
                .rename(columns={"region": "r"})
            )

        geoall = (
            pd.concat(geo, axis=0)
            .reset_index(level=0)
            .rename(columns={"level_0": "type"})
            .reset_index()
        )
        geoall["type"] = geoall["type"] + "_allkm"
        geoall.supply_curve_cost_per_mw = geoall.supply_curve_cost_per_mw.round(2)
        geoall["class"] = "class" + geoall["class"].astype(str)
        geoall["bin"] = "geosc" + geoall["bin"].astype(str)
        ### Pivot, with bins in long format
        geocost = (
            geoall.pivot(
                index=["region", "class", "type"],
                columns="bin",
                values="supply_curve_cost_per_mw",
            )
            .fillna(0)
            .reset_index()
        )
        geocap = (
            geoall.pivot(
                index=["region", "class", "type"], columns="bin", values="capacity"
            )
            .fillna(0)
            .reset_index()
        )

        ### Geothermal bins (flexible)
        bins_geo = (range(1, max(numbins['geohydro']*use_geohydro_rev_sc, numbins['egs']*use_egs_rev_sc) + 1))
        geocap.rename(
            columns={
                **{
                    "type": "tech",
                    "Unnamed: 0": "region",
                    "Unnamed: 1": "class",
                    "Unnamed 2": "tech",
                },
                **{"geosc{}".format(i): "bin{}".format(i) for i in bins_geo},
            },
            inplace=True,
        )
        alloutcap_list.append(geocap)

        geocost.rename(
            columns={
                **{
                    "type": "tech",
                    "Unnamed: 0": "region",
                    "Unnamed: 1": "class",
                    "Unnamed 2": "tech",
                },
                **{"geosc{}".format(i): "bin{}".format(i) for i in bins_geo},
            },
            inplace=True,
        )
        alloutcost_list.append(geocost)

        if write:
            ## Geothermal discovery rates
            geo_disc_rate = pd.read_csv(os.path.join(inputs_case, "geo_discovery_rate.csv"))
            geo_disc_rate.round(decimals).to_csv(
                os.path.join(inputs_case, "geo_discovery_rate.csv"), index=False
            )
            geo_discovery_factor = pd.read_csv(
                os.path.join(inputs_case, "geo_discovery_factor.csv")
            )
            geo_discovery_factor = geo_discovery_factor.loc[
                geo_discovery_factor.r.isin(val_r_all)].copy()
            geo_discovery_factor.round(decimals).to_csv(
                os.path.join(inputs_case, "geo_discovery_factor.csv"), index=False
            )

            if use_geohydro_rev_sc:
                ## Exogenous geohydro capacity
                dfgeohydroexog = get_exog_cap(inputs_case, tech='geohydro', dfsc=geo['geohydro'])
                dfgeohydroexog.round(3).to_csv(
                    os.path.join(inputs_case, "exog_geohydro_allkm_rsc.csv")
                )

    # %% Get supply-curve data for postprocessing
    spurcols = [
        'i',
        'r',
        'rscbin',
        'capacity',
        'dist_spur_km',
        'dist_reinforcement_km',
        'supply_curve_cost_per_mw',
    ]
    spurout = pd.concat(spurout_list)[spurcols].round(2)
    if write:
        ## Spurline and reinforcement distances and costs
        spurout.to_csv(os.path.join(inputs_case, "spur_parameters.csv"), index=False)

    ### Get spur-line and reinforcement distances if using in annual trans investment limit
    poi_distance = spurout.copy()
    ## Duplicate CSP entries for each CSP system design
    poi_distance_csp = poi_distance.loc[poi_distance.i.str.startswith("csp")].copy()
    poi_distance_csp_broadcasted = pd.concat(
        [
            poi_distance_csp.assign(
                i=poi_distance_csp.i.str.replace("csp_", f"csp{i}_")
            )
            for i in range(1, csp_configs + 1)
        ],
        axis=0,
    )
    poi_distance_out = (
        pd.concat(
            [
                poi_distance.loc[~poi_distance.i.str.startswith("csp")],
                poi_distance_csp_broadcasted,
            ],
            axis=0,
        )
        ## Reformat to save for GAMS
        .rename(columns={"i": "*i"})
        .set_index(["*i", "r", "rscbin"])
    )
    ## Convert to miles
    distance_spur = (poi_distance_out.dist_spur_km.rename("miles") / 1.609).round(3)
    if write:
        distance_spur.to_csv(os.path.join(inputs_case, "distance_spur.csv"))

    distance_reinforcement = (
        poi_distance_out.dist_reinforcement_km.rename("miles") / 1.609
    ).round(3)
    if write:
        distance_reinforcement.to_csv(
            os.path.join(inputs_case, "distance_reinforcement.csv")
        )

    # %%###################################
    #    -- Supply Curve Data --    #
    ######################################
    # %% Combine the supply curves
    alloutcap = (
        pd.concat(alloutcap_list)
        .rename(columns={"region": "r"})
        .assign(var="cap")
    )
    alloutcap["class"] = alloutcap["class"].map(lambda x: x.lstrip("cspclass"))
    alloutcap["class"] = (
        "class" + alloutcap["class"].map(lambda x: x.lstrip("class")).astype(str)
    )

    t1 = alloutcap.pivot(
        index=["r", "tech", "var"],
        columns="class",
        values=[c for c in alloutcap.columns if c.startswith("bin")],
    ).reset_index()
    ### Concat the multi-level column names to a single level
    t1.columns = ["_".join(i).strip("_") for i in t1.columns.tolist()]

    t2 = t1.merge(tout, on=["r", "tech"], how="outer").fillna(0)

    ### Subset to single-tech curves
    wndonst2 = t2.loc[t2.tech == "wind-ons"].copy()
    wndofst2 = t2.loc[t2.tech == "wind-ofs"].copy()
    cspt2 = t2.loc[t2.tech.isin(["csp{}".format(i) for i in range(1, csp_configs + 1)])]
    upvt2 = t2.loc[t2.tech == "upv"].copy()
    geohydrot2 = t2.loc[t2.tech == "geohydro_allkm"].copy()
    egst2 = t2.loc[t2.tech == "egs_allkm"].copy()

    ### Get the combined outputs
    outcap = pd.concat([wndonst2, wndofst2, upvt2, cspt2, geohydrot2, egst2])

    moutcap = pd.melt(outcap, id_vars=["r", "tech", "var"])
    moutcap = moutcap.loc[~moutcap.variable.isin(["exist", "temp"])].copy()

    moutcap["bin"] = moutcap.variable.map(lambda x: x.split("_")[0])
    moutcap["class"] = moutcap.variable.map(lambda x: x.split("_")[1].lstrip("class"))
    outcols = ["r", "tech", "var", "bin", "class", "value"]
    moutcap = moutcap.loc[moutcap.value != 0, outcols].copy()

    outcapfin = (
        moutcap.pivot(
            index=["r", "tech", "var", "class"], columns="bin", values="value"
        )
        .fillna(0)
        .reset_index()
    )

    alloutcost = (
        pd.concat(alloutcost_list)
        .rename(columns={"region": "r"})
        .set_index(["r", "class", "tech"])
        .reset_index()
        .assign(var="cost")
    )
    alloutcost["class"] = alloutcost["class"].map(lambda x: x.lstrip("cspclass"))
    alloutcost["class"] = alloutcost["class"].map(lambda x: x.lstrip("class"))

    allout = pd.concat([outcapfin, alloutcost])
    allout["tech"] = allout["tech"] + "_" + allout["class"].astype(str)
    alloutm = pd.melt(allout, id_vars=["r", "tech", "var"])
    alloutm.rename(columns={"bin":"variable"}, inplace=True)
    alloutm = alloutm.loc[alloutm.variable != "class"].copy()
    allout_list = [alloutm]

    # %%----------------------------------------------------------------------------------
    ##########################
    #    -- Hydropower --    #
    ##########################
    """
    Adding hydro costs and capacity separate as it does not
    require the calculations to reduce capacity by existing amounts.
    
    Goal here is to acquire a data frame that matches the format
    of alloutm so that we can simply stack the two.
    """
    hydcap = pd.read_csv(os.path.join(inputs_case, "hydcap.csv"))
    hydcost = pd.read_csv(os.path.join(inputs_case, "hydcost.csv"))

    hydcap = (
        pd.melt(hydcap, id_vars=["tech", "class"])
        .set_index(["tech", "class", "variable"])
        .sort_index()
    )
    hydcap = hydcap.reset_index()
    hydcost = pd.melt(hydcost, id_vars=["tech", "class"])

    # Convert dollar year
    hydcost[hydcost.select_dtypes(include=["number"]).columns] *= deflate["hydcost"]

    hydcap["var"] = "cap"
    hydcost["var"] = "cost"

    hyddat = pd.concat([hydcap, hydcost])
    hyddat["bin"] = hyddat["class"].map(lambda x: x.replace("hydclass", "bin"))
    hyddat["class"] = hyddat["class"].map(lambda x: x.replace("hydclass", ""))

    hyddat.rename(columns={"variable": "r", "bin": "variable"}, inplace=True)
    hyddat = hyddat[["tech", "r", "value", "var", "variable"]].fillna(0)
    allout_list.append(hyddat)

    #########################################
    #    -- Pumped Storage Hydropower --    #
    #########################################

    if int(sw["GSw_Storage"]):
        # Input processing currently assumes that cost data in CSV file is in 2004$
        psh_cap = pd.read_csv(os.path.join(inputs_case, "psh_supply_curves_capacity.csv"))
        psh_cost = pd.read_csv(os.path.join(inputs_case, "psh_supply_curves_cost.csv"))
        psh_durs = pd.read_csv(
            os.path.join(inputs_case, "psh_supply_curves_duration.csv"), header=0
        )

        psh_cap = pd.melt(psh_cap, id_vars=["r"])
        psh_cost = pd.melt(psh_cost, id_vars=["r"])

        # Convert dollar year
        psh_cost[psh_cost.select_dtypes(include=["number"]).columns] *= deflate["PHScostn"]

        psh_cap["var"] = "cap"
        psh_cost["var"] = "cost"

        psh_out = pd.concat([psh_cap, psh_cost]).fillna(0)
        psh_out["tech"] = "pumped-hydro"
        psh_out["variable"] = psh_out.variable.map(lambda x: x.replace("pshclass", "bin"))
        psh_out = psh_out[hyddat.columns].copy()
        allout_list.append(psh_out)

        if write:
            # Select storage duration correponding to the supply curve
            psh_dur_out = psh_durs[psh_durs["pshsupplycurve"] == pshsupplycurve]["duration"]
            psh_dur_out.to_csv(
                os.path.join(inputs_case, "psh_sc_duration.csv"), index=False, header=False
            )

    #######################################################
    #    -- Demand Response  --    #
    #######################################################

    if int(sw["GSw_DRShed"]):
        # Use capacity and cost to add DR Shed to rsc_combined
        # Define rsc class using tech
        dr_shed_cap = pd.read_csv(os.path.join(inputs_case,'dr_shed_cap.csv'))
        dr_shed_cap['class'] = dr_shed_cap['tech']
        dr_shed_cost = pd.read_csv(os.path.join(inputs_case,'dr_shed_cost.csv'))
        dr_shed_cost['class'] = dr_shed_cost['tech']

        dr_shed_cap = (pd.melt(dr_shed_cap, id_vars=['tech','class'])
                    .set_index(['tech','class','variable'])
                    .sort_index())
        dr_shed_cap = dr_shed_cap.reset_index()
        dr_shed_cost = pd.melt(dr_shed_cost, id_vars=['tech','class'])

        # Convert dollar year
        dr_shed_cost[dr_shed_cost.select_dtypes(include=['number']).columns] *= deflate['dr_shed']

        # Assign rsc cat
        dr_shed_cap['var'] = 'cap'
        dr_shed_cost['var'] = 'cost'

        # Combined cost and capacity
        dr_shed_dat = pd.concat([dr_shed_cap, dr_shed_cost])
        dr_shed_dat['bin'] = dr_shed_dat['class'].map(lambda x: x.replace('dr_shed_','bin'))
        dr_shed_dat['class'] = dr_shed_dat['class'].map(lambda x: x.replace('dr_shed_',''))

        dr_shed_dat.rename(columns={'variable':'r','bin':'variable'}, inplace=True)
        dr_shed_dat = dr_shed_dat[['tech','r','value','var','variable']].fillna(0)
        allout_list.append(dr_shed_dat)

    #######################################################
    #    -- EV Managed Charging --    #
    #######################################################
    rsc_dr = {}
    for drcat in ["evmc"]:
        scen = {"evmc": sw.evmcscen}[drcat]
        active = {"evmc": int(sw.GSw_EVMC)}[drcat]
        if (scen.lower() != "none") and active:
            rsc = pd.read_csv(os.path.join(inputs_case, f"{drcat}_rsc.csv"))
            rsc["var"] = rsc["var"].str.lower()

            # Convert dollar year
            rsc.loc[rsc['var']=='Cost','value'] *= deflate[f'{drcat}_rsc_{scen}']
        
            # Duplicate or interpolate data for all years between start and
            # end year. Only DR has yearly supply curve data.
            yrs = pd.DataFrame(list(range(startyear, endyear+1)), columns=['year'])
            yrs['tmp'] = 1

            # Get all years for all parts of data
            tmp = rsc[
                [c for c in rsc.columns if c not in ["year", "value"]]
            ].drop_duplicates()
            tmp["tmp"] = 1
            tmp = pd.merge(tmp, yrs, on="tmp").drop("tmp", axis=1)
            tmp = pd.merge(tmp, rsc, how="outer", on=list(tmp.columns))

            # Interpolate between years that exist using a linear spline interpolation
            # extrapolating any values at the beginning or end as required
            # Include all years here then filter later to get spline correct if data
            # covers more than the years modeled
            def grouper(group):
                return group.interpolate(
                    limit_direction="both", method="slinear", fill_value="extrapolate"
                )

            rsc = tmp.groupby(
                [c for c in tmp.columns if c not in ["value", "year"]], group_keys=True
            ).apply(grouper)
            rsc = (
                rsc[rsc.year.isin(yrs.year)][
                    ### Reorder to match other supply curves
                    ["tech", "r", "var", "bin", "year", "value"]
                ]
                ### Rename the first column so GAMS reads the header as a comment
                .rename(
                    columns={
                        "tech": "*tech",
                        "var": "sc_cat",
                        "bin": "rscbin",
                        "year": "t",
                    }
                )
            )
            # Ensure no values are < 0
            rsc["value"].clip(lower=0, inplace=True)
        else:
            rsc = pd.DataFrame(columns=["*tech", "r", "sc_cat", "rscbin", "t", "value"])

        if write:
            rsc.to_csv(
                os.path.join(inputs_case, f"rsc_{drcat}.csv"), index=False, header=True
            )

        rsc_dr[drcat] = rsc.copy()

    # %%----------------------------------------------------------------------------------
    ##################################
    #    -- Combine everything --    #
    ##################################

    ### Combine, then drop the (cap,cost) entries with nan cost
    alloutm = (
        pd.concat(allout_list)
        .pivot(
            index=["r", "tech", "variable"], columns=["var"], values=["value"]
        )
        .dropna()["value"]
        .reset_index()
        .melt(id_vars=["r", "tech", "variable"])[
            ["tech", "r", "var", "variable", "value"]
        ]
        ### Rename the first column so GAMS reads the header as a comment
        .rename(columns={"tech": "*i", "var": "sc_cat", "variable": "rscbin"})
        .astype({"value": float})
        ### Drop 0 values
        .replace({"value": {0.0: np.nan}})
        .dropna()
        .round(5)
    )

    ## Merge geothermal non-reV supply curves if applicable
    if int(sw["GSw_Geothermal"]):
        if not use_geohydro_rev_sc:
            geohydro_rsc = pd.read_csv(os.path.join(inputs_case, "geo_rsc.csv"), header=0)
            geohydro_rsc = geohydro_rsc.loc[
                geohydro_rsc["*i"].str.startswith("geohydro_allkm")
            ]
            # Filter by valid regions
            geohydro_rsc = geohydro_rsc.loc[geohydro_rsc["r"].isin(val_r_all)]
            # Convert dollar year
            geohydro_rsc.sc_cat = geohydro_rsc.sc_cat.str.lower()
            geohydro_rsc.loc[geohydro_rsc.sc_cat == "cost", "value"] *= deflate[
                "geo_rsc_{}".format(geohydrosupplycurve)
            ]
            geohydro_rsc["rscbin"] = "bin1"
            alloutm = pd.concat([alloutm, geohydro_rsc])

        if not use_egs_rev_sc:
            egs_rsc = pd.read_csv(os.path.join(inputs_case, "geo_rsc.csv"), header=0)
            egs_rsc = egs_rsc.loc[egs_rsc["*i"].str.startswith("egs_allkm")]
            # Filter by valid regions
            egs_rsc = egs_rsc.loc[egs_rsc["r"].isin(val_r_all)]
            # Convert dollar year
            egs_rsc.sc_cat = egs_rsc.sc_cat.str.lower()
            egs_rsc.loc[egs_rsc.sc_cat == "cost", "value"] *= deflate[
                "geo_rsc_{}".format(egssupplycurve)
            ]
            egs_rsc["rscbin"] = "bin1"
            alloutm = pd.concat([alloutm, egs_rsc])

        egsnearfield_rsc = pd.read_csv(os.path.join(inputs_case, "geo_rsc.csv"), header=0)
        egsnearfield_rsc = egsnearfield_rsc.loc[
            egsnearfield_rsc["*i"].str.startswith("egs_nearfield")
        ]
        # Filter by valid regions
        egsnearfield_rsc = egsnearfield_rsc.loc[egsnearfield_rsc["r"].isin(val_r_all)]
        # Convert dollar year
        egsnearfield_rsc.sc_cat = egsnearfield_rsc.sc_cat.str.lower()
        egsnearfield_rsc.loc[egsnearfield_rsc.sc_cat == "cost", "value"] *= deflate[
            "geo_rsc_{}".format(egsnearfieldsupplycurve)
        ]
        egsnearfield_rsc["rscbin"] = "bin1"
        alloutm = pd.concat([alloutm, egsnearfield_rsc])

    ### Combine with cost components
    alloutm = pd.concat([alloutm, cost_components_upv, cost_components_wind])
    if write:
        alloutm.to_csv(
            os.path.join(inputs_case, "rsc_combined.csv"), index=False, header=True
        )
    
    #%%----------------------------------------------------------------------------------
    #######################
    #    -- Biomass --    #
    #######################
    """
    Biomass is currently being handled directly in b_inputs.gms
    """

    # %%----------------------------------------------------------------------------------
    ##########################################
    #    -- Spur lines (disaggregated) --    #
    ##########################################
    ### Get interconnection cost for reV sites within modeled area
    interconnection_cost = reeds.io.assemble_supplycurve()
    sitemap = reeds.io.get_sitemap()
    county2zone = reeds.io.get_county2zone(os.path.dirname(os.path.normpath(inputs_case)))
    interconnection_cost['r'] = interconnection_cost.index.map(sitemap.FIPS).map(county2zone)
    val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'),
        header=None,
    ).squeeze(1).values
    spursites = interconnection_cost.loc[interconnection_cost.r.isin(val_r)].copy()
    spursites['x'] = 'i' + spursites.index.astype(str)
    if write:
        spursites[["x", "cost_total_trans_usd_per_mw"]].rename(columns={"x": "*x"}).to_csv(
            os.path.join(inputs_case, "spurline_cost.csv"), index=False
        )
        spursites["x"].to_csv(
            os.path.join(inputs_case, "x.csv"), index=False, header=False
        )
        spursites[["x", "r"]].rename(
            columns={"x": "*x"}
        ).drop_duplicates().to_csv(os.path.join(inputs_case, "x_r.csv"), index=False)

    ###### Site maps
    ### UPV
    sitemap_upv = (
        upvin.assign(i="upv_" + upvin["class"].astype(str))
        .assign(rscbin="bin" + upvin["bin"].astype(str))
        .assign(x="i" + upvin["sc_point_gid"].astype(str))
    )
    sitemap_upv = (
        sitemap_upv
        ### Assign rb's based on the no-exclusions transmission table
        .assign(r=sitemap_upv.x.map(spursites.set_index("x").r))[
            ["i", "r", "rscbin", "x"]
        ].rename(columns={"i": "*i"})
    )
    ### wind-ons
    sitemap_windons = (
        windin["ons"]
        .assign(i="wind-ons_" + windin["ons"]["class"].astype(str))
        .assign(rscbin="bin" + windin["ons"]["bin"].astype(str))
        .assign(x="i" + windin["ons"]["sc_point_gid"].astype(str))
    )
    sitemap_windons = (
        sitemap_windons
        ### Assign r's based on the no-exclusions transmission table
        .assign(r=sitemap_windons.x.map(spursites.set_index("x").r))[
            ["i", "r", "rscbin", "x"]
        ].rename(columns={"i": "*i"})
    )

    ### Combine, then only keep sites that show up in both supply curve and spur-line cost tables
    spurline_sitemap_list = [sitemap_upv, sitemap_windons]
    ### geohydro_allkm
    if use_geohydro_rev_sc:
        sitemap_geohydro = (
            geoin["geohydro"]
            .assign(i="geohydro_allkm_" + geoin["geohydro"]["class"].astype(str))
            .assign(rscbin="bin" + geoin["geohydro"]["bin"].astype(str))
            .assign(x="i" + geoin["geohydro"]["sc_point_gid"].astype(str))
        )
        sitemap_geohydro = (
            sitemap_geohydro
            ### Assign rb's based on the no-exclusions transmission table
            .assign(r=sitemap_geohydro.x.map(spursites.set_index("x").r))[
                ["i", "r", "rscbin", "x"]
            ].rename(columns={"i": "*i"})
        )
        spurline_sitemap_list.append(sitemap_geohydro)
    ### egs_allkm
    if use_egs_rev_sc:
        sitemap_egs = (
            geoin["egs"]
            .assign(i="egs_allkm_" + geoin["egs"]["class"].astype(str))
            .assign(rscbin="bin" + geoin["egs"]["bin"].astype(str))
            .assign(x="i" + geoin["egs"]["sc_point_gid"].astype(str))
        )
        sitemap_egs = (
            sitemap_egs
            ### Assign rb's based on the no-exclusions transmission table
            .assign(r=sitemap_egs.x.map(spursites.set_index("x").r))[
                ["i", "r", "rscbin", "x"]
            ].rename(columns={"i": "*i"})
        )
        spurline_sitemap_list.append(sitemap_egs)

    spurline_sitemap = pd.concat(spurline_sitemap_list, ignore_index=True)
    spurline_sitemap = spurline_sitemap.loc[
        spurline_sitemap.x.isin(spursites.x.values)
    ].copy()
    if write:
        spurline_sitemap.to_csv(
            os.path.join(inputs_case, "spurline_sitemap.csv"), index=False
        )

    ### Add mapping from sc_point_gid to bin for reeds_to_rev.py
    site_bin_map_list = [
        upvin.assign(tech="upv")[["tech", "sc_point_gid", "bin"]]
    ]
    for wind_type, dfin in windin.items():
        site_bin_map_list.append(
            dfin.assign(tech=f"wind-{wind_type}")[
                ["tech", "sc_point_gid", "bin"]
            ]
        )
    if use_geohydro_rev_sc:
        site_bin_map_list.append(
            geoin["geohydro"].assign(tech="geohydro_allkm")[
                ["tech", "sc_point_gid", "bin"]
            ]
        )
    if use_egs_rev_sc:
        site_bin_map_list.append(
            geoin["egs"].assign(tech="egs_allkm")[["tech", "sc_point_gid", "bin"]]
        )
    site_bin_map = pd.concat(site_bin_map_list, ignore_index=True)
    if write:
        site_bin_map.to_csv(os.path.join(inputs_case, "site_bin_map.csv"), index=False)

    return alloutm


# %% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == "__main__":
    ### Time the operation of this script
    tic = datetime.datetime.now()

    ### Parse arguments
    parser = argparse.ArgumentParser(description="Format and supply curves")
    parser.add_argument("reeds_path", help="path to ReEDS directory")
    parser.add_argument("inputs_case", help="path to inputs_case directory")

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    # %% Run it
    print("Starting writesupplycurves.py")

    main(reeds_path=reeds_path, inputs_case=inputs_case)

    reeds.log.toc(
        tic=tic, year=0, process='input_processing/writesupplycurves.py',
        path=os.path.join(inputs_case,'..'))
    
    print('Finished writesupplycurves.py')
