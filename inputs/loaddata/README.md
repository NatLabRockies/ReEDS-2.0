# Load Profile options

### Describing the switch options for GSw_EFS1_AllYearLoad 
These files are stored in `inputs/loaddata/{switch_name}_load_hourly.h5`.

| Switch Name    | Description of Profile | Origin |
| ------------- | ------------- | ------------- |
| Baseline | NEED INFO HERE | NEED INFO HERE  |
| Clean2035_LTS | Net-zero emissions, economy wide, by 2050 based on the White House's Long Term Strategy as shown here: https://www.whitehouse.gov/wp-content/uploads/2021/10/US-Long-Term-Strategy.pdf | Developed for the 100% Clean Electricity by 2035 study: https://www.nrel.gov/docs/fy22osti/81644.pdf |
| Clean2035    | Accelerated Demand Electrification (ADE) profile. This profile was custom made for the 100% Clean Electricity by 2035 study. More information about how it was formed can be found in https://www.nrel.gov/docs/fy22osti/81644.pdf Appendix C. | Developed for the 100% Clean Electricity by 2035 study: https://www.nrel.gov/docs/fy22osti/81644.pdf |
| Clean2035clip1pct | Same as Clean2035 but clips off the top 1% of load hours. | Developed for the 100% Clean Electricity by 2035 study: https://www.nrel.gov/docs/fy22osti/81644.pdf |
| EPHIGH | Features a combination of technology advancements, policy support and consumer enthusiasm that enables transformational change in electrification.   | Developed for the Electrification Futures Study https://www.nrel.gov/docs/fy18osti/71500.pdf. |
| EPMEDIUMStretch2046 | An average of the EPMEDIUM profile and the AEO reference trajectory. This was created to very roughly simulate the EV and broader electrification incentives in IRA, before we had better estimates of the actual effects of IRA. | NREL researchers combined the EPMEDIUM profile and the AEO reference trajectory.
| EPMEDIUM | Features a future with widespread electrification among the “low-hanging fruit” opportunities in electric vehicles, heat pumps and select industrial applications, but one that does not result in transformational change. | Developed for the Electrification Futures Study https://www.nrel.gov/docs/fy18osti/71500.pdf. |
| EPREFERENCE | Features the least incremental change in electrification through 2050, which serves as a baseline of comparison to the other scenarios.| Developed for the Electrification Futures Study https://www.nrel.gov/docs/fy18osti/71500.pdf. |
| EER_100by2050  | 100% decarbonization by 2050 scenario. This does not explicitly include the impacts of the Inflation Reduction Act. However, due to its decarbonization, it is a more aggressive electrification profile than EER_IRA.  | Purchased from Evolved Energy Research in June 2023 for the National Transmission Planning Study and to update our load profiles in general. More information can be found in EER's Annual Decarbonization Report https://www.evolved.energy/post/adp2022. |
| EER_IRAmoderate  | Modeling load change under moderate assumptions about the Inflation Reduction Act | Purchased from Evolved Energy Research in June 2023 for the National Transmission Planning Study and to update our load profiles in general. More information can be found in EER's Annual Decarbonization Report https://www.evolved.energy/post/adp2022. |
| EER_IRAlow  | Modeling load change under conservative assumptions about the Inflation Reduction Act   | Purchased from Evolved Energy Research in June 2023 for the National Transmission Planning Study and to update our load profiles in general. More information can be found in EER's Annual Decarbonization Report https://www.evolved.energy/post/adp2022. |
| EER_Baseline_AEO2022  | Business as usual load growth. Based on the service demand projections from AEO 2022. This does not include the impacts of the Inflation Reduction Act.   | Purchased from Evolved Energy Research in June 2023 for the National Transmission Planning Study and to update our load profiles in general. More information can be found in EER's Annual Decarbonization Report https://www.evolved.energy/post/adp2022. |
| historic | Historic demand from 2007-2013. This is multiplied by annual growth factors from AEO to forecast load growth. | NEED INFO HERE |

The h5 files stored here have one of two formats:
1. EER style format: 7 weather years (2007-2013), these data are produced by the script `ReEDS-2.0/hourize/eer_to_reeds/eer_to_reeds.py`
2. Other: 1 weather year (2012)