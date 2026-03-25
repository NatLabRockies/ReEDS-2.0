# H2 inputs 

## consume_char_[GSw_H2_Inputs].csv

Contains cost and performance assumption for electrolyzers and steam-methane reformer.

Electrolyzer capital cost assumptions are based on the Pathways to Commercial Liftoff: Clean Hydrogen Report (https://liftoff.energy.gov/wp-content/uploads/2023/05/20230320-Liftoff-Clean-H2-vPUB-0329-update.pdf) [see values in the footnotes of Figure 3 on page 14]. The reference scenario assumes linearly decline from 1750 $/kW in 2022 to 550 $/kW in 2030, and then remain constant after. The low cost scenario assumes further declines from 2030 to 2050. 

Fixed O&M values are assumed to be 5% of CAPEX (source: https://iopscience.iop.org/article/10.1088/1748-9326/acacb5)

Electrolyzer performance (efficiency) as well as SMR cost and performance assumptions are derived from assumptions H2A: Hydrogen Analysis Production Models (https://www.nrel.gov/hydrogen/h2a-production-models.html), with guidance from Paige Jadun. See original input assumptions in the ReEDS-2.0_Input_Processing repo: https://github.nrel.gov/ReEDS/ReEDS-2.0_Input_Processing/blob/main/H2/costs/H2ProductionCosts-20210414.xlsx.

Note that SMR costs are currently in 2018$ and electrolyzer costs are in 2022$.

## h2_transport_and_storage_costs.csv

| Investment    | Cost type | Units |
| ------------- | ------------- | ------------- |
| Pipelines  | Overnight Capital Cost  | $/[(tonne/hour)*mile] |
| Pipelines  | FOM  | $/[(tonne/hour)*mile*year] |
| Pipelines  | Electric load | MWh/tonne |
| Compressors  | Overnight Capital Cost  | $/(tonne-hour) |
| Compressors  | FOM  | $/[(tonne/hour)*year) |
| Compressors  | Electric load  | MWh/tonne |
| Storage  | Overnight Capital Cost  | $/tonne |
| Storage  | FOM  | $/(tonne*year) |
| Storage  | Electric load  | MWh/tonne |

The values in `H2_transport_and_storage_costs.csv` are based on raw data provided from the SERA model by Paige Jadun. The raw data are formated by the `process-h2-inputs.py` script in the input processing repository (https://github.nrel.gov/ReEDS/ReEDS-2.0_Input_Processing/blob/main/H2/process-h2-inputs.py).

## h2_storage_rb.csv

Mapping of ReEDS balancing are to available H2 storage type. Since costs are always ordered (saltcavern < hardrock < above ground), BAs with access to saltcaverns or hardrock storage are only assigned to the cheapest option to reduce the model size.
