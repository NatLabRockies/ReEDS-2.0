# Input files
1. *cost_hurdle_country.csv*: Indicates the hurdle rate for transmission flows between USA/Canada and USA/Mexico. **Unknown source.**
1. *r_rr_adj.csv*: Set of zones that are adjacent to each other, including Canada/Mexico zones.
1. *rev_transmission_basecost.csv*: Base transmission costs (before terrain mlutipliers) used in reV. Sources for numeric values are:
    1. TEPPC: https://www.wecc.org/Administrative/TEPPC_TransCapCostCalculator_E3_2019_Update.xlsx
    1. SCE: http://www.caiso.com/Documents/SCE2019DraftPerUnitCostGuide.xlsx
    1. MISO: https://cdn.misoenergy.org/20190212%20PSC%20Item%2005a%20Transmission%20Cost%20Estimation%20Guide%20for%20MTEP%202019_for%20review317692.pdf
        1. A more recent guide with a working link (as of 20230227) is available at https://cdn.misoenergy.org/Transmission%20Cost%20Estimation%20Guide%20for%20MTEP22337433.pdf.
    1. Southeast: **Unknown source**
1. *routes_adjacent.csv*: Set of US zones that are adjacent to each other.
1. *transmission_capacity_future_baseline.csv*: Historically installed (since 2010) and currently planned transmission capacity additions. **Many unknown sources.**
1. *transmission_capacity_future_{`GSw_TransScen`}.csv*: Available future routes for transmission capacity as specified by `GSw_TransScen`.
1. *transmission_capacity_init_AC_NARIS2024.csv*: Initial AC transmission capacities between 134 US ReEDS zones. Calculated using the code available at https://github.nrel.gov/pbrown/TSC and nodal network data from https://www.nrel.gov/docs/fy21osti/79224.pdf. The method is described by Brown, P.R. et al 2023, "A general method for estimating zonal transmission interface limits from nodal network data", in prep.
1. *transmission_capacity_init_AC_REFS2009.csv*: Initial AC transmission capacities between 134 US ReEDS zones. Calculated for https://www.nrel.gov/analysis/re-futures.html.
1. *transmission_capacity_init_nonAC.csv*: Initial DC transmission capacities between 134 US ReEDS zones. **Many unknown sources.**
1. *transmission_distance_cost_500kVac.csv*: Distance and cost for a representative transmission route between each pair of 134 US ReEDS zones, assuming a 500 kV single-circuit line. Routes are determined by the reV model using a least-cost-path algorithm accounting for terrain and land type multipliers. Costs represent the appropriate base cost from rev_transmission_basecost.csv multiplied by the appropriate terrain and land type multipliers for each 90m pixel crossed by the path. Endpoints are in inputs/shapefiles/transmission_endpoints and represent a point within the largest urban area in each of the 134 ReEDS zones.
1. *transmission_distance_cost_500kVdc.csv*: Same as transmission_distance_cost_500kVdc.csv except assuming a 500 kV bipole DC line.


# Relevant switches
1. `GSw_HierarchyFile`: Indicate the suffix of the inputs/hierarchy.csv file you wish to use.
    1. By default the transreg boundaries are used for operating reserve sharing, capacity credit calculations, and the boundaries for limited-transmission cases.
1. `GSw_TransInvMaxLongTerm`: Limit on annual transmission deployment nationwide **IN/AFTER** `firstyear_trans_longterm`, measured in TW-miles
1. `GSw_TransInvMaxNearTerm`: Limit on annual transmission deployment nationwide **BEFORE** `firstyear_trans_longterm`, measured in TW-miles
1. `GSw_TransInvPRMderate`: By default, adding 1 MW of transmission capacity between two zones increases the energy transfer capability by 1 MW but the PRM trading capability by only 0.85 MW; here you can adjust that derate
1. `GSw_TransCostMult`: Applies to interzonal transmission capacity (including AC/DC converters) but not FOM costs
1. `GSw_TransSquiggliness`: Somewhat similar to `GSw_TransCostMult`, but scales the distance for each inter-zone interface. So turning it up to 1.3 will increase costs and losses by 1.3, and for the same amount of GW it will increase TWmiles by 1.3.
1. `GSw_TransHurdle`: Intra-US hurdle rate for interzonal flows, measured in $2004/MWh
1. `GSw_TransHurdleLevel`: Indicate the level of hierarchy.csv between which to apply the hurdle rate specified by `GSw_TransHurdle`. i.e. if set to ‘st’, intra-state flows will have no hurdle rates but inter-state flows will have hurdle rates specified by `GSw_TransHurdle`.
1. `GSw_TransRestrict`: Indicate the level of hierarchy.csv within which to allow transmission expansion. i.e. if set to ‘st’, no inter-state expansion is allowed.
1. `GSw_TransScen`: Indicate the inputs/transmission/transmission_capacity_future_{`GSw_TransScen`}.csv file to use, which includes the list of interfaces that can be expanded. Note that the full list of expandable interfaces is indicated by this file plus transmission_capacity_future_default.csv (currently planned additions) plus transmission_capacity_init_AC_NARIS2024.csv (existing AC interfaces, which can be expanded by default) plus transmission_capacity_init_nonAC.csv (existing DC connections, which can be expanded by default). Applies to AC, LCC, and VSC.
1. `GSw_VSC`: Indicate whether to allow VSC expansion. Will only have an effect if paired with a `GSw_TransScen` that includes VSC interfaces.
1. `GSw_PRM_hierarchy_level`: Level of hierarchy.csv within which to calculate net load, used for capacity credit. Larger levels indicate more planning coordination between regions.
1. `GSw_PRMTRADE_level`: Level of hierarchy.csv within which to allow PRM trading. By default it’s set to ‘country’, indicating no limits. If set to ‘r’, no PRM trading is allowed.
