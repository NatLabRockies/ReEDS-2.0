# Hydropower Capacity Factor Calculations
Hydropower capacity factor data is stored in the `hydcf_{ba|county}.h5` files and is calculated by upstream input processing scripts located in a separate repository.

Each .h5 file contains annual hydropower capacity factor data for "historical" years 2010-present, as well as data for the first "future" year after the present year.
Calculation methods for the historical year capacity factors differ from that of the future year capacity factor in that historical year capacity factors are derived from actual operational data and are thus accurate to historically-observed values.
Future capacity factor data, on the other hand, are derived from averages of the same operational data over a given set of historical years. 
During runs, ReEDS will forward-fill the `hydcf_*.h5` file for all required future model years by duplicating the data of the first "future" year in the file.

Details on the historical/future year capacity factor calculations can be found in the [Historical vs Future Capacity Factor](#historical-vs-future-capacity-factor) section below.

## Procedural Details
Hydropower capacity factor is calculated using monthly net generation and capacity values from ORNL's
Existing Hydropower Assets (EHA) database by dividing the monthly net generation of all units in a region by the maximum theoretical monthly generation of said units (using monthly capacity at 100% CF).

$$ CapacityFactor_{r,m} = \sum_{u \in U_r} \sum_{h \in H_m} Gen_{u,h} / \sum_{u \in U_r}Cap_{u,h}*hrs_{m}$$

Where:
- _r_: region
- _m_: month
- _u_ ∈ _U<sub>r</sub>_: generating unit _u_ located in region _r_
- _h_ ∈ _H<sub>m</sub>_: hours _h_ in month _m_
- _Gen<sub>u,h</sub>_: generation of unit _u_ during hour _h_
- _Cap<sub>u,h</sub>_: nameplate capacity of unit _u_ during hour _h_
- _hrs<sub>m</sub>: total number of hours in month _m_

The most up-to-date ReEDS EIA-NEMS generator database is used to map plant-level ORNL capacity/generation data to ReEDS tech and region (BA/FIPS county).

### Historical vs Future Capacity Factor
The availability of historical plant-level data allows for historical capacity factors to be calculated using net and max generation values aggregated to the BA/county level.
Thus, historical capacity factor data coincides with actual energy budgets and realized generation
output.

Future capacity factor data, however, uses the average net and max generation of each plant across a given set of historical years to calculate the BA/county-level capacity factors for the future year.
For example, future capacity factor data can be calculated using the average monthly net and max generation for all hydropower units from 2010-2020 - these plant-level averages will then be aggregated to the BA/county level for capacity factor calculations.
