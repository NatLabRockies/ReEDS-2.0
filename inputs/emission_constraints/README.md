### CO<sub>2</sub> and CO<sub>2</sub>e Caps
CO<sub>2</sub> and CO<sub>2</sub>e emissions caps are defined in `inputs/emission_constraints/co2_cap.csv`, which includes a range of different emission cap trajectories until 2050.

### Emission Rates
Upstream and process emission rates by technology and pollutant used in ReEDS are defined in `inputs/emission_constraints/emitrate.csv`. These emission rates are taken from Table A-9 in Appendix A.5 of NLR's Standard Scenarios 2024 (https://www.nrel.gov/docs/fy25osti/92256.pdf), which details the multiple sources that these emission rates are obtained from such as U.S. Life Cycle Inventory Database, EPA's Emissions & Generation Resource Integrated Database, California Air Resources Board, etc.

Note that CH<sub>4</sub> upstream emission rate for natural gas is zero in `emitrate.csv` as we use CH<sub>4</sub> methane leakage defined using the `GSw_MethaneLeakageScen` switch to calculate it.

### Global Warming Potentials
A range of values for global warmning potentals (GWP) of CH<sub>4</sub> and N<sub>2</sub>O are taken from the most recent IPCC assessment reports (AR4 to AR6). Summary of the ranges of GWPs for these pollutants can be found in Table 7.15, page 1017 of the IPCC AR6 report (https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_FullReport.pdf).
