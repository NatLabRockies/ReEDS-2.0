# Clean Air Act, Section 111

## The regulation itself

The Clean Air Act, Section 111 is a federal regulation from the Environmental Protection Agency (EPA), which features carbon pollution standards to reduce greenhouse gas emissions from power plants.
These regulations are called Section 111 for the section of the tax code which it is implemented in.
The regulations stipulate a couple of compliance mechanisms for plants to comply with these regulations.

The first compliance mechanism, and the strictest, is a best system of emissions reduction (BSER) for every technology and vintage (existing vs new plants).
This is enforced at the plant level i.e. each plant must meet its BSER.
The BSERs are listed below:

- Existing coal plants:
  - If the plant will permanently cease operations before Jan. 1, 2032: they are not subject to these standards
  - If the plant is operating on or after Jan. 1, 2032, and demonstrate that they plan to permanently cease operation before Jan. 1, 2039: they must cofire with 40% natural gas from 2030 through 2039
  - If the plant plant to operate on or after Jan. 1, 2039: they must upgrade with CCS with 90% capture by Jan. 1, 2032
- New coal plants:
  - No regulations since no new coal plants are being built these days
- Existing gas-CCs and gas-CTs:
  - No regulations
- New gas-CCs and gas-CTs:
  - If the plant is operating at <= 40% capacity factor: they are unregulated
  - If a plant is operating above 40% CF: they must upgrade with CCS by 2032.

The second compliance mechanism, which is slightly more lenient, is a emissions rate-based mechanism.
This is enforced at the state level.
If a state opts into this compliance mechanism, the emisisons rate (tons CO<sub>2</sub>/MWh) of their coal fleet must be less than or equal to the emissions rate of a 90% coal-CCS plant.
This in theory enables some unabated coal plants to remain online after 2032, even though they won't be able to generate much.
This is only possible if that state also has coal-CCS plants with high capture rates that stay online and generate, to average out the emissions rate to below the threshold.

### Other resources

- [Simplified presentation on the final regulations](https://www.epa.gov/system/files/documents/2024-04/cps-presentation-final-rule-4-24-2024.pdf)
- [Final regulations](https://www.federalregister.gov/documents/2024/05/09/2024-09233/new-source-performance-standards-for-greenhouse-gas-emissions-from-new-modified-and-reconstructed)
- [History of the Clean Air Act](https://www.epa.gov/clean-air-act-overview/evolution-clean-air-act)

## Implementation in ReEDS

In ReEDS, new gas plants must adhere to their BSER and existing coal plants adhere to an emissions rate-based standard.

For new gas plants, this is the code implementation:

1. `inputs/scalars.csv`
    - `caa_gas_max_cf` = 0.40.
    This is the maximum capacity factor that new gas plants (CCs or CTs) can operate at without being regulated under Clean Air Act, Section 111, expressed as a fraction.
2. `c_supplymodel.gms` - `eq_caa_max_cf` enforces the maximum capacity factor for new gas plants.


For existing coal plants, this is the code implementation:

1. `inputs/scalars.csv`
    - `caa_coal_retire_year` = 2032.
    This is the year in which coal capacity is forced to either retire or upgrade with CCS to meet the emissions requirements under Clean Air Act, Section 111.
    - `caa_first_year` = 2024.
    This is the year in which the emissions requirements under Clean Air Act, Section 111 are first active.
    - `caa_rate_emis_standard` = 0.1039.
    This is the emissions rate (metric tons CO<sub>2</sub> per MWh) equivalent to average emissions from a new coal-CCS plant, assuming 90% capture rate.
    The emissions rate from a new coal-CCS plant in ReEDS is 0.051956 metric tons CO<sub>2</sub> per MWh (see `emit_rate` parameter) which assumes 95% capture.
    For 90% capture, the emissions rate is double that or 0.1039 metric tons CO<sub>2</sub> per MWh, which we use as the standard.
2. `input_processing/WriteHintage.py`
    - Coal plants are binned at the unit level if `GSw_Clean_Air_Act=1` so that each coal unit can independently choose to retire or upgrade.
    - Coal plants maintain their exogenous retirement assumption, except after 2032, when the Clean Air Act regulations begin and coal can retire endogenously.
    For example, if the NEMS data states that a plant will retire in 2029, we maintain that assumption and that plant will retire in 2029.
    However, if the NEMS data previously stated that a plant will retire in 2040, they are now subject to the Clean Air Act regulations and may retire sooner than their previously stated retirement date.
3. `b_inputs.gms`
    - `numhintage` is set to 300, so that we can accomodate a large number of coal bins since they are binned at the unit level.
    - Revise `m_capacity_exog` so that it matches with which coal capacity is allowed.
    - if `caa_coal_retire_year` is not in the set of years being modeled for this run, then set it to the first year that is modeled after `caa_coal_retire_year`.
    For example, if running 5 year solves, then instead of enforcing coal retirement in 2032, it will be enforced in 2035.

4. `c_supplymodel.gms`
    - `eq_caa_rate_standard(st,t)` - this constraint enforces the rate-based emissions standard by setting the maximum coal emissions rate per state under Clean Air Act Section 111.

## Assumptions

- We do not include the compliance mechanism for coal plants to cofire with natural gas in the model.
We have modeled this in ReEDS previously in our analysis of these regulations and found that coal plants almost never choose this compliance mechanism.
They would prefer to upgrade with CCS or retire.
