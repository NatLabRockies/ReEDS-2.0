# Input files

- `ccseason_dates.csv`: Defines the time resolution (`ccseason`) on which the capacity market is cleared when using the capacity credit resource adequacy method.
New `ccseason` definitions may be added as new columns
(and added to the choices for the `GSw_PRM_CapCreditSeasons` switch in `cases.csv`),
but each column should include a `hot` and `cold` season, since the nameplate capacity is adjusted in those seasons based on summer/winter capacities from EIA and projected climate impacts (if activated via the `GSw_ClimateHeuristics` switch).
- `peak_net_imports.csv`: 99.9th percentile coincident transfers (BA-level, aggregated to NERC region-level) between 2019-2023 from EIA Hourly Grid Monitor used as an estimate of current interregional transfer capabilities, as tabulated in [ESIG 2024](https://www.esig.energy/wp-content/uploads/2024/06/ESIG-Interregional-Transmission-Resilience-methodology-report-2024.pdf).
Values for SERC-E/SE/C calculated using ESIG 2024 methodology.
The same 0.1% definition has been used elsewhere, e.g. <https://www.congress.gov/bill/118th-congress/senate-bill/2827/text#id6543a3657b784ecbb9362b629a5290ea>.
Values for MW_TotalDemand are for 2024 from [LTRA 2023](https://www.nerc.com/pa/RAPA/ra/Reliability%20Assessments%20DL/NERC_LTRA_2023.pdf) and represent on-peak projections (same as used in  NERC planning reserve margin calculations).
- `prm_annual.csv`: Taken from the 2023 NERC LTRA (specifically the "Reference Margin Level (%)" reported for each reliability region)
