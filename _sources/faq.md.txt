# FAQ

## Table of Contents

- [FAQ](#faq)
  - [Table of Contents](#table-of-contents)
    - [How much are the GAMS licensing fees?](#how-much-are-the-gams-licensing-fees)
    - [Is there a trial version of the GAMS license so that I can test ReEDS?](#is-there-a-trial-version-of-the-gams-license-so-that-i-can-test-reeds)
    - [What computer hardware is necessary to run ReEDS?](#what-computer-hardware-is-necessary-to-run-reeds)
    - [Can I configure a ReEDS case to run as an isolated interconnect?](#can-i-configure-a-reeds-case-to-run-as-an-isolated-interconnect)
    - [How do I change the spatial resolution of a ReEDS case?](#how-do-i-change-the-spatial-resolution-of-a-reeds-case)
    - [How can I reduce solve time?](#how-can-i-reduce-solve-time)
    - [How often are updates made to ReEDS?](#how-often-are-updates-made-to-reeds)
    - [What are the limitations, caveats, and known issues?](#what-are-the-limitations-caveats-and-known-issues)
      - [Capabilities that don't currently work](#capabilities-that-dont-currently-work)
      - [Assumptions](#assumptions)
      - [Input data and processing](#input-data-and-processing)
      - [Output processing](#output-processing)

<a name="gams-license"></a>
### How much are the GAMS licensing fees?

Please contact GAMS for more information.

<a name="gams-trial"></a>
### Is there a trial version of the GAMS license so that I can test ReEDS?

We have created a reduced size version of the ReEDS model that has less than 5,000 rows and columns, and therefore should be compatible with the GAMS community license ([https://www.gams.com/try_gams/](https://www.gams.com/try_gams/) -- Please contact GAMS if you need additional information regarding the community license). You can run this reduced model version by using the cases_small.csv input file. This reduced model uses a smaller technology subset, smaller geographic extent, and simplifies several model constraints.

<a name="computer-hardware"></a>
### What computer hardware is necessary to run ReEDS?

Running ReEDS using the reference case (located in cases.csv) is feasible on a laptop with 32GB of RAM. However, for running ReEDS with enhanced features such as explicit H2 modeling, C02 networks, increased temporal/spatial resolution, etc., it is recommened to utlize a higher-performance workstation or High-Performance Computing (HPC) machine.

National-scale ReEDS scenarios can be run on a laptop with 32GB of RAM. However, if you would like to run ReEDS with more detailed options (explicit H<sub>2</sub> modeling, C0<sub>2</sub> networks, higher temporal/spatial resolution, etc.), it is recommended to use a higher-performance workstation or HPC.

<a name="isolated-interconnect-reeds"></a>
### Can I configure a ReEDS case to run as an isolated interconnect?

Yes, you can configure ReEDS as a single interconnect. Limiting the spatial extent may be beneficial for modeling more difficult instances.

**WARNING!:** The default case configurations were designed for modeling the lower 48 United States. Therefore, the user should be aware of possible issues with executing an interconnect in isolation, including but not limited to the following:

- Natural gas prices are based on either national or census division supply curves. The natural gas prices are computed as a function of the quantity consumed relative to a reference quantity. Consuming less than the reference quantity drives the price downward; consuming more drives the price upward. When modeling a single interconnection, the user should either modify the reference gas quantity to account for a smaller spatial extent or use fixed gas prices in every census division (i.e., case configuration option [GSw\_GasCurve](#SwOther) = 2). For example, if we execute ERCOT in isolation using census division supply curves, we may want to reduce the reference gas quantity for the West South Central (West_South_Central) census division which includes Texas, Oklahoma, Arkansas, and Louisiana. Or we could assume the gas price in the West_South_Central region is fixed.

- Infeasibilities may arise in state-level constraints when only part of a state is represented in an interconnect. For example, the Western interconnection includes a small portion of Texas (El Paso). State-level constraints will be enforced for Texas, but El Paso may not be able to meet the requirement for all of Texas.

- Certain constraints may not apply in every interconnect. Some examples include:
  - California State RPS REC trading constraints only apply to the West
  - CAIR and CSAPR only apply to certain states, so the emission limits may need to be adjusted
  - RGGI only applies to a subset of states in the northeast
  - California policies (e.g., SB32, California Storage Mandate) only apply to California

<a name="spatial-resolution-reeds"></a>
### How do I change the spatial resolution of a ReEDS case?

The ReEDS model is capable of capturing several spatial resolutions. This aspect of the model is controlled by the `GSw_Region`, `GSw_RegionResolution`, and `GSw_HierarchyFile` switches, and sometimes by the inputs/userinput/modeled_regions.csv file.

- Balancing areas (BAs) and aggregated groups of BAs: Aggregation level is controlled by the 'aggreg' column of the inputs/hierarchy_{GSw_HierarchyFile}.csv file.
  - 134 zones: `GSw_RegionResolution = ba`
  - 132 zones (**default**): `GSw_RegionResolution = aggreg`, `GSw_HierarchyFile = default`. Merges p119 into p122 and p30 into p28.
  - 125 zones: `GSw_RegionResolution = aggreg`, `GSw_HierarchyFile = agg125`. Merges p119 into p122, p49 into p50, p124 into p99, p19 into p20, p44 into p68, p120 into p122, p29 and p30 into p28, and p71 into p72, obeying state, interconnect, NERC, and FERC region boundaries.
  - 69 zones: `GSw_RegionResolution = aggreg`, `GSw_HierarchyFile = agg69`. Obeys state, interconnect, NERC, and FERC region boundaries; most other zones below these levels are aggregated together.
  - 54 zones: `GSw_RegionResolution = aggreg`, `GSw_HierarchyFile = agg54`. Obeys state boundaries but nudges the edges of interconnect, NERC, and FERC region boundaries to align with states. Keeps CA, IL, and NY split into 2 zones and TX split into 4 zones.
- Counties: `GSw_RegionResolution = county`. Only solves in tolerable time when running a subset of the U.S. as specified by the `GSw_Region` switch.
- Mixed resolution: `GSw_RegionResolution = mixed`, `GSw_Region` set to a column in the inputs/userinput/modeled_regions.csv file. Can be used to model some regions at county resolution and others at BA or aggregated-region resolution.

<a name="reduce-solve-time"></a>
### How can I reduce solve time?

If you'd like to reduce the model solve time, consider making some of the following changes:

- `yearset_suffix = 4yr` or `yearset_suffix = 5yr`
  - Solve in 4- or 5-year steps
- `GSw_OpRes = 0`
  - Turn off operating reserves
- `GSw_MinLoading = 0`
  - Turn off the sliding-window representation of minimum-generation limits
- `GSw_HourlyNumClusters = 25` (or lower)
  - Reduce the number of representative periods
- `GSw_RegionResolution = aggreg`
  - Aggregate the native 134 zones into fewer (larger) zones, with the amount of aggregation controlled by `GSw_HierarchyFile`

<a name="reeds-updates"></a>
### How often are updates made to ReEDS?

Every year we target June 1 for the bulk of model changes to be completed, which allows us to meet the hard deadline for having a working, updated version of the model by June 30. We typically make minor updates to the model over the summer and tag a final version for that year in August or September. This version is then used to produce the Standard Scenarios and Cambium data products.

Additionally, changes are made throughout the year and a new version is created and published roughly every month. You can find current and past ReEDS versions here: {{ '[ReEDS-2.0 Releases]({}/releases)'.format(base_github_url) }}

If you would like to run ReEDS with a previous version, you can either download the source code directly or check out that version using the tag.

To check out a previous version using its tag, you can run the following command from your command line or terminal (ensure you have the main branch of the repo checked out):

```bash
git checkout tags/{version number}
```

Here is an example of what this would look like:

```bash
git checkout tags/v2024.0.0
```

<a name="known-issues"></a>
### What are the limitations, caveats, and known issues?

ReEDS is a big model with limitations and caveats. Higher-level limitations are discussed in the [model documentation](model_documentation.md); more code-facing issues are listed here.

**Note: The following limitations, caveats, and known issues are incomplete and will evolve as the model changes**

#### Capabilities that don't currently work

- Climate impacts on hydropower (`GSw_ClimateHydro`), electricity demand (`Gsw_ClimateDemand`), and water cooling (`GSw_ClimateWater`)
- `endyear` beyond 2050 (processed in forecast.py)
- Demand flexibility via the `GSw_EFS_Flex` switch
- County-level runs for regions with Canadian imports/exports and stress-period PRM formulation (`GSw_PRM_CapCredit == 0)

#### Assumptions

- Hydrogen production tax credit
  - One of the requirements of the hydrogen production tax credit is that the generation capacity must be no more than 3 years older than the electrolyzer to satisfy the "incrementality" or "additionality" condition.
  - To avoid comparing vintages of the generator and the electrolyzer and increasing computational intensity, we make a simplifying assumption that all new clean generators (2024 and onwards) satisfy the incrementality condition.

#### Input data and processing

- copy_files.py
  - copy_files.py currently copies data to a ReEDS run's inputs_case folder that might not be relevant to the run based on the run's configured switch settings (e.g. `upv_220AC-reference_ba.h5` is copied into the inputs_case folder even if PVB is turned off or GSw_PVB_ILR only contains '130' as value(s)). This leads to bloating of the inputs_case folder due to inclusion of data that is irrelevant to a given run, which could also be misleading for users. This issue can be solved by including a new column to the runfiles.csv that controls whether or not a given runfile is copied into inputs_case based on a corresponding switch setting.
- hourly_repperiods.py
  - We use available-capacity-weighted average solar and wind profiles to select representative days, so we include lots of low-resource-quality sites that realistically probably wouldn't be built. We may obtain different representative days if we were to downselect to higher-quality sites, but before running ReEDS it's hard to say where the cutoff should be. So for now we stick with the available-capacity-weighted average across all sites.
- Move distpv capacity trajectory from "exogenous capacity" into "prescribed builds"
  - Currently, distpv capacity prescriptions are captured in the the "exogenous capacity" construct which represents capacity remaining in year t for capacity that existed prior to the first solve year. The data in this construct should be monotonically decreasing over time to reflect retirements. However, the distpv capacity prescription is monotonically increasing. We should move distpv capacity prescriptions to the "prescriptive capacity" construct which represents the cumulative capacity installed in each year.

#### Output processing

- Land use
  - Land-use calculations use a static map of current land types; we do not project changes in land type (e.g. urbanization, changes to forestry and agriculture practices, etc) when assessing the land types utilized by new wind and solar.
- Retail rates
  - High-level limitations and caveats are discussed in [Brown et al 2022](https://www.nrel.gov/docs/fy22osti/78224.pdf)
  - When using a 5-year model step (for example), the value of the PTC is evenly split over all 5 years in the step. We don't try to assess in which year within the step a capacity investment is made.
