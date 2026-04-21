# Nuclear-Stor: Technical Documentation

> Comprehensive documentation of the nuclear-stor hybrid technology implementation in ReEDS-2.0.
> Target audience: New ReEDS developers who need to understand, use, modify, or extend nuclear-stor.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Technology Architecture](#2-technology-architecture)
3. [Configuration & Switches](#3-configuration--switches)
4. [Input Data Pipeline](#4-input-data-pipeline)
5. [GAMS Set Definitions](#5-gams-set-definitions)
6. [Cost Formulation](#6-cost-formulation)
7. [Financial Treatment](#7-financial-treatment)
8. [Model Variables](#8-model-variables)
9. [Constraint Equations](#9-constraint-equations)
10. [Storage Dynamics](#10-storage-dynamics)
11. [Objective Function](#11-objective-function)
12. [Reporting](#12-reporting)
13. [Solve-Time Processing](#13-solve-time-processing)
14. [Comparison with Other Hybrid Technologies](#14-comparison-with-other-hybrid-technologies)
15. [How to Modify or Extend](#15-how-to-modify-or-extend)
16. [File Reference](#16-file-reference)

---

## 1. Overview

Nuclear-stor is a **hybrid technology** in ReEDS that couples a nuclear generator (conventional large reactor or SMR) with onsite thermal energy storage (TES), typically using molten salt. The nuclear reactor charges the TES during periods of low electricity demand or low prices, and the TES discharges through an energy island (turbine-generator + electrical equipment) during high-demand periods.

This design allows otherwise baseload nuclear plants to provide **flexible, dispatchable output** — shifting energy across hours within a day — making nuclear more competitive in grids with high renewable penetration. The implementation follows the same hybrid-plant framework used by PV+battery (PVB) technologies but with nuclear-specific adaptations.

### Key Design Principles

- **Configurable**: Up to 8 distinct nuclear-stor types can be defined, each with its own boiler coupling ratio (BCR), storage technology, generator technology, and grid charging capability.
- **Parameter-driven**: Each type is parameterized by BCR and grid charging ratio rather than encoding configuration into technology names.
- **Component-based costs**: Capital, FOM, and VOM costs are built from the constituent nuclear and storage technology costs, with adjustments for the shared energy island.
- **Auto-propagated inputs**: Most input CSV files are automatically populated with nuclear-stor rows by cloning the paired generator tech's rows during preprocessing — developers rarely need to add nuclear-stor rows manually.

---

## 2. Technology Architecture

### Technology Types

Nuclear-stor supports up to 8 configurable types, named `Nuclear-Stor1` through `Nuclear-Stor8` in the model technology set. Each type is independently configured with:

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| **Generator tech** | Which nuclear reactor to pair | `nuclear` (large), `nuclear-smr` |
| **Storage tech** | Which storage technology to pair | `tes-ms` (molten-salt TES) |
| **BCR** | Boiler coupling ratio — ratio of storage power capacity to nuclear power capacity | 0.45, 0.5, 0.65 |
| **Grid charging ratio** | Fraction of nuclear capacity available for charging storage from the grid | 0.0, 0.5, 1.0 |

### Default 6-Type Configuration

The standard case configuration (`cases_nuclearstor_main.csv`) defines 6 types:

| Type | Generator | Storage | BCR | Grid Charging |
|------|-----------|---------|-----|---------------|
| Nuclear-Stor1 | Nuclear-SMR | tes-ms | 0.45 | 0.0 |
| Nuclear-Stor2 | Nuclear-SMR | tes-ms | 0.50 | 0.0 |
| Nuclear-Stor3 | Nuclear-SMR | tes-ms | 0.65 | 0.0 |
| Nuclear-Stor4 | Nuclear | tes-ms | 0.45 | 0.0 |
| Nuclear-Stor5 | Nuclear | tes-ms | 0.50 | 0.0 |
| Nuclear-Stor6 | Nuclear | tes-ms | 0.65 | 0.0 |

### Physical Interpretation

The BCR defines the ratio of the storage system's power capacity to the nuclear generator's capacity. For example, with BCR = 0.45 and a 300 MW nuclear plant:
- **Storage power capacity**: 0.45 × 300 = 135 MW
- **Total power block output**: (1 + 0.45) × 300 = 435 MW (the energy island handles both nuclear output and storage discharge)
- **Storage energy capacity**: Determined endogenously by the model via the `CAP_ENERGY` variable, subject to minimum duration constraints

The grid charging ratio, when nonzero, adds a heater that allows the TES to be charged from grid electricity (in addition to charging from the nuclear plant's thermal output).

---

## 3. Configuration & Switches

All nuclear-stor behavior is controlled through case file switches. These are set in the `cases_nuclearstor_*.csv` files and read during preprocessing.

### Master Switch

| Switch | Values | Description |
|--------|--------|-------------|
| `GSw_NuclearStor` | `0` / `1` | Master on/off. When `0`, all Nuclear-Stor types are banned (added to `ban(i)` and `bannew(i)` sets). Default: `0`. |

### Type Configuration Switches

| Switch | Format | Description |
|--------|--------|-------------|
| `GSw_NuclearStor_Types` | `1_2_3_4_5_6` | Underscore-delimited list of which types (1–8) to activate. Unused types are banned. |
| `GSw_NuclearStor_BCR` | `0.45_0.5_0.65_0.45_0.5_0.65` | BCR for each type. Must have 1 value (broadcast to all types) or the same number of values as types. |
| `GSw_NuclearStor_StorageTechs` | `tes-ms_tes-ms_...` | Storage technology for each type. Currently only `tes-ms` is tested. |
| `GSw_NuclearStor_GenTechs` | `nuclear-smr_nuclear-smr_..._nuclear_nuclear_nuclear` | Generator technology for each type. Must be `nuclear` or `nuclear-smr`. |
| `GSw_NuclearStor_GridCharging` | `0.0_0.0_...` | Grid charging ratio for each type. `0.0` = no grid charging. |

### Related Switches

| Switch | Description |
|--------|-------------|
| `Sw_HybridPlant` | Must be ≥ 2 for nuclear-stor dispatch equations to be active (enables non-CSP hybrid plants). Default: `3` (all hybrids). |
| `Sw_NukeStateBan` | `0` = remove state nuclear bans, `1` = enforce bans, `2` = model bans as cost penalty. Nuclear-stor inherits these regional bans. |
| `GSw_NuclearDemo` | `1` = include nuclear demonstration plants (relevant for Nuclear-SMR paired types). |
| `Sw_TES` | Must be `1` for TES to be available (otherwise all TES-based nuclear-stor types are banned). |

### Type Banning Logic

Types are selectively banned in `b_inputs.gms` (lines 857–898) using compile-time `$ifthen` blocks. The logic bans all types NOT listed in `GSw_NuclearStor_Types`. For example, if `GSw_NuclearStor_Types = 1_2_3`, then types 4–8 are added to the `ban(i)` set.

---

## 4. Input Data Pipeline

The input processing pipeline transforms case-file switches and raw technology data into model-ready CSV files. This is the most important section for developers adding or modifying nuclear-stor behavior.

### Step 1: Configuration CSV Generation (`copy_files.py`, lines 1640–1690)

The function `handle_misc_files()` in `input_processing/copy_files.py` reads the `GSw_NuclearStor_*` switches and generates four CSV files in `inputs_case/`:

| Generated File | Contents | GAMS Consumer |
|----------------|----------|---------------|
| `nuclear_stor_bcr.csv` | BCR values indexed by `Nuclear-Stor{N}` | `bcr(i)` parameter |
| `nuclear_stor_gridcharging.csv` | Grid charging ratios indexed by `Nuclear-Stor{N}` | `gridcharge_ratio(i)` parameter |
| `nuclear_stor_storagetechs.csv` | Storage tech mapping (e.g., `Nuclear-Stor1 → tes_ms`) | `nuclear_stor_stortech(i,ii)` set |
| `nuclear_stor_gentechs.csv` | Generator tech mapping (e.g., `Nuclear-Stor1 → nuclear-smr`) | `nuclear_stor_gentech(i,ii)` set |

The `_expand_to_len()` helper broadcasts a single value to all types if only one value is provided (e.g., `GSw_NuclearStor_BCR = 0.5` → all types get BCR 0.5).

### Step 2: Technology Row Propagation (`copy_files.py`, lines 1943–2200+)

The `propagate_nuclearstor_tech_rows()` function is the **linchpin** of the nuclear-stor data pipeline. It automatically clones input CSV rows from the paired generator tech (Nuclear or Nuclear-SMR) to each Nuclear-Stor type.

**How it works:**

1. For each `(generator_tech → Nuclear-Stor{N})` pair from the configuration:
2. Scan all CSV files in `inputs_case/`
3. For each file, identify columns that contain technology identifiers (using the `_looks_like_tech_column()` heuristic: ≥60% of non-empty values match entries in `inputs/sets/i.csv`)
4. Clone rows where the tech-id column contains the generator tech name, replacing it with the Nuclear-Stor type name
5. For wide-format files (tech names as column headers), copy the generator tech's column to a new Nuclear-Stor column

**Skip lists** — These files/directories are NOT propagated (lines 1988–2008):

| Skip Target | Reason |
|-------------|--------|
| `capacity_exogenous/` | Exogenous capacity handled separately |
| `demonstration_files/` | Demo plants handled separately |
| `plantchar_*.csv` | Handled by `plantcostprep.py` separately |
| `plantcharout.csv` | Generated later in the pipeline |
| `emission_constraints/emitrate.csv` | Nuclear-stor doesn't have different emission rates |
| `financials/cap_penalty.csv` | Not applicable |
| `national_generation/gbin_min.csv` | Not applicable |
| `unitdata.csv` | Existing plant data — no existing nuclear-stor plants |
| `sets/tg.csv` | Tech group mapping handled in GAMS |
| `tech-subset-table.csv` | Already has explicit nuclear-stor rows |
| `financials/incentives_*.csv` | Incentive eligibility handled separately |
| `financials/ref_cap_cost_diff_*.csv` | Regional cost differences handled separately |
| Any file already containing `nuclear-stor` or `nuclear_stor` | Already has explicit rows |

**This is a common source of confusion**: If a new input file is created that contains technology-specific rows, it will automatically receive nuclear-stor rows via propagation UNLESS it matches one of the skip conditions above. If nuclear-stor rows should NOT be auto-generated for a new file, add it to the skip list.

### Step 3: Financial Parameter Propagation (`calc_financial_inputs.py`, lines 85–102)

The `append_nuclear_stor_parameters()` function (from `reeds.financials`) copies degradation and other financial parameters from the storage technology (e.g., `tes_ms`) to each Nuclear-Stor type. This runs after `propagate_nuclearstor_tech_rows()` and handles parameters that the row propagation cannot (because they come from the storage tech, not the generator tech).

### Step 4: Plant Cost Processing (`plantcostprep.py`)

- Processes heater costs for TES variants (converting $/kW to $/MW)
- Handles `plantchar_*.csv` files that were skipped by the propagation step
- Generates `plantcharout.csv` with nuclear-stor-specific cost entries

---

## 5. GAMS Set Definitions

### Technology Sets (`b_inputs.gms`, lines 472–480)

```
nuclear_stor(i)      — All nuclear+storage technologies (union of types 1–8)
nuclear_stor1(i)     — Nuclear+storage type 1
nuclear_stor2(i)     — Nuclear+storage type 2
  ...
nuclear_stor8(i)     — Nuclear+storage type 8
```

These sets are populated from the `tech-subset-table.csv` at `b_inputs.gms` line 1071:

```gams
nuclear_stor(i)$(not ban(i))  = yes$i_subsets(i,'Nuclear-Stor') ;
nuclear_stor1(i)$(not ban(i)) = yes$i_subsets(i,'Nuclear-Stor1') ;
...
```

### Technology Subset Memberships (`tech-subset-table.csv`)

All Nuclear-Stor types are marked `YES` for the following subsets:

| Subset | Meaning |
|--------|---------|
| `CONV` | Conventional (dispatchable) technology |
| `STORAGE` | Storage technology |
| `STORAGE_HYBRID` | Hybrid VRE-storage technology |
| `THERMAL_STORAGE` | Thermal storage technology |
| `NUCLEAR-STOR` | Parent nuclear-stor category |
| `NUCLEAR-STOR{N}` | Specific type self-reference |

### Linking Sets (`b_inputs.gms`, lines 1135–1165)

Two linking sets connect each hybrid type to its component technologies:

```gams
nuclear_stor_stortech(i,ii)  — Maps Nuclear-Stor{N} to its storage tech (e.g., tes-ms)
nuclear_stor_gentech(i,ii)   — Maps Nuclear-Stor{N} to its generator tech (e.g., nuclear-smr)
```

These are loaded from the CSV files generated in Step 1 above.

### Derived Set: TES Detection (`b_inputs.gms`, lines 1168–1172)

```gams
nuclear_stor_with_tes(i) = yes  if the storage tech is in i_subsets(ii,'tes')
```

If a Nuclear-Stor type's storage tech is TES, it is automatically added to the `tes(i)` and `thermal_storage(i)` sets. This triggers TES-specific cost formulations and efficiency handling.

### Technology Group Membership (`b_inputs.gms`, line 1112)

Nuclear-stor technologies are grouped under the `'nuclear'` technology group:

```gams
tg_i('nuclear',i)$[(nuclear(i) or nuclear_stor(i))] = yes ;
```

This means nuclear-stor capacity counts toward nuclear-related policy constraints (e.g., nuclear generation mandates).

---

## 6. Cost Formulation

### Capital Cost (`b_inputs.gms`, lines 6060–6091)

The capital cost formula differs based on whether the storage technology is thermal (TES) or non-thermal (e.g., battery):

**For TES-based nuclear-stor** (the standard configuration):

```
cost_cap(i,t) = cost_cap_nuclear_stor_p(i,t)           [nuclear plant cost]
              - turbine_generator_cost_nuc_stor(i,t)    [remove turbine-generator]
              - electrical_cost_nuc_stor(i,t)            [remove electrical equipment]
              + (1 + bcr(i)) × cost_cap_nuclear_stor_s(i,t)  [TES energy island, scaled]
              + gridcharge_ratio(i) × heater_capcost     [grid charging heater]
```

**Why remove and re-add turbine/electrical costs?** In a nuclear-stor plant, the TES replaces the conventional turbine-generator and electrical equipment with an *energy island* (power block) that must handle both the nuclear plant's output AND the storage discharge. The energy island (storage plant capex) is therefore sized at (1 + BCR) × nuclear capacity. The original turbine-generator (GN-COA Code 23) and electrical equipment (GN-COA Code 24) costs are subtracted once from the nuclear cost and implicitly included in the storage plant's capital cost at the larger (1+BCR) scale.

The cost fractions removed are from ATB 2024 Table 6, GN-COA breakdown (Abou-Jaoude et al. 2024, INL/RPT-24-77048):
- Code 23 (Energy Conversion System): Large = 3.92%, SMR = 3.86%
- Code 24 (Electrical Equipment): Large = 6.32%, SMR = 9.46%

**For non-TES nuclear-stor** (e.g., paired with battery):

```
cost_cap(i,t) = cost_cap_nuclear_stor_p(i,t) + bcr(i) × cost_cap_nuclear_stor_s(i,t)
```

### Component Cost Parameters (`b_inputs.gms`, lines 4510–4524)

```gams
cost_cap_nuclear_stor_p(i,t) = plant_char0(gentech, t, 'capcost')   [nuclear portion]
cost_cap_nuclear_stor_s(i,t) = plant_char0(stortech, t, 'capcost')  [storage portion]
cost_cap_energy(i,t)         = plant_char0(stortech, t, 'capcost_energy')  [energy capacity cost]
```

### Fixed O&M Cost (`b_inputs.gms`, lines 4718–4730)

```
cost_fom(i,v,r,t) = cost_fom_nuclear_stor_p(i,v,r,t)       [nuclear FOM]
                   + bcr(i) × cost_fom_nuclear_stor_s(i,v,r,t)  [storage FOM, scaled by BCR]

cost_fom_energy(i,v,r,t) = plant_char(stortech, v, t, 'fom_energy')  [energy capacity FOM]
```

FOM is charged on `CAP(i,v,r,t)` (nuclear power capacity) and `CAP_ENERGY(i,v,r,t)` (storage energy capacity) separately.

### Variable O&M Cost (`b_inputs.gms`, lines 4641–4647)

Two separate VOM parameters:

```gams
cost_vom(i,v,r,t)                  — Nuclear plant VOM (from gentech); applied to GEN_PLANT
cost_vom_nuclear_stor_s(i,v,r,t)   — Storage VOM (from stortech); applied to GEN_STORAGE
```

If the storage tech has no VOM data, a minimum floor (`storage_vom_min`) is applied to prevent solver degeneracy.

---

## 7. Financial Treatment

Nuclear-stor receives a **cost-weighted average** financial multiplier that blends the nuclear and storage portions' distinct ITC, depreciation, and financing risk characteristics.

### Financial Multiplier Splitting (`d1_financials.gms`, lines 158–260)

The model computes separate financial multipliers for each component:

```gams
cost_cap_fin_mult_nuclear_stor_p(i,r,t)  — Nuclear portion multiplier (nuclear ITC, 15-yr MACRS)
cost_cap_fin_mult_nuclear_stor_s(i,r,t)  — Storage portion multiplier (storage ITC, 5-yr MACRS)
```

These are loaded from the component technologies' standalone multipliers:

```gams
cost_cap_fin_mult_nuclear_stor_p(i,r,t) = cost_cap_fin_mult(gentech, r, t)
cost_cap_fin_mult_nuclear_stor_s(i,r,t) = cost_cap_fin_mult(stortech, r, t)
```

**Important**: The assignment of component multipliers must happen BEFORE the global trim step that zeros out `cost_cap_fin_mult` for technologies not in `valinv_irt` for a given region. Component techs (e.g., `Nuclear-SMR`, `tes-ms`) may not independently appear in every region.

### Financing Risk Adjustment (`d1_financials.gms`, lines 168–178)

For a hybrid plant, the entire project carries nuclear-level financing risk. The storage portion's `financing_risk_mult` is replaced with the nuclear tech's:

```
adjusted_storage_mult = storage_mult × (nuclear_risk / storage_risk)
```

### Cost-Weighted Average (`d1_financials.gms`, lines 220–250)

The final multiplier blends both portions weighted by their capital cost shares:

```
cost_cap_fin_mult(i,r,t) = 
    (nuc_cost × nuc_mult + stor_cost × stor_mult)
    / (nuc_cost + stor_cost)
```

Where:
- For TES types: `nuc_cost` = nuclear capex minus turbine-generator and electrical; `stor_cost` = (1+BCR) × storage capex + heater cost
- For non-TES types: `nuc_cost` = nuclear capex; `stor_cost` = BCR × storage capex

Three variants exist: `cost_cap_fin_mult` (with ITC), `_noITC`, and `_no_credits`.

### Energy Upsizing (`c_supplyobjective.gms`, lines 155–160)

When nuclear-stor energy capacity is upsized (via `INV_ENER_UP`), the **storage-side** financial multiplier is used (not the blended multiplier), since energy upsizing is purely a storage investment:

```gams
cost_cap_fin_mult_nuclear_stor_s(i,r,t) × INV_ENER_UP(i,v,r,rscbin,t) × cost_ener_up(...)
```

---

## 8. Model Variables

Nuclear-stor uses the **hybrid plant variable framework** shared with PVB. All variables are defined in `c_supplymodel.gms` (lines 47–57).

### Power Variables (all in MW, average over timeslice)

| Variable | Description |
|----------|-------------|
| `GEN(i,v,r,h,t)` | **Net output to grid**. For nuclear-stor: GEN = GEN_PLANT + GEN_STORAGE − STORAGE_IN_PLANT |
| `GEN_PLANT(i,v,r,h,t)` | Thermal output from the nuclear reactor |
| `GEN_STORAGE(i,v,r,h,t)` | Discharge from the storage system |
| `STORAGE_IN_PLANT(i,v,r,h,t)` | Storage charging from the coupled nuclear plant (thermal charging) |
| `STORAGE_IN_GRID(i,v,r,h,t)` | Storage charging from the grid (via heater, if enabled) |

### Capacity Variables

| Variable | Description |
|----------|-------------|
| `CAP(i,v,r,t)` | Nuclear power capacity in MW (the reactor's nameplate) |
| `CAP_ENERGY(i,v,r,t)` | Storage energy capacity in MWh (endogenous, not fixed duration) |
| `INV(i,v,r,t)` | Investment in new nuclear-stor capacity (MW) |
| `INV_ENERGY(i,v,r,t)` | Investment in new storage energy capacity (MWh) |

### Storage State Variables

| Variable | Description |
|----------|-------------|
| `STORAGE_LEVEL(i,v,r,h,t)` | Energy stored in the TES at each timeslice (MWh) |
| `STORAGE_INTERDAY_LEVEL(i,v,r,allszn,t)` | Interday storage level (if `Sw_InterDayLinkage = 1`) |

---

## 9. Constraint Equations

All constraint equations are in `c_supplymodel.gms`. They are active when `Sw_HybridPlant ≥ 2` (which enables the `$Sw_HybridPlant` conditional). All equations below apply to `storage_hybrid(i)$(not csp(i))`, which includes nuclear-stor.

### Total Generation Accounting (`eq_plant_total_gen`, line 3402)

**Net grid output = plant output + storage discharge − plant charging**

```
GEN(i,v,r,h,t) = GEN_PLANT + GEN_STORAGE − STORAGE_IN_PLANT
```

Nuclear-stor's `GEN` represents the net power delivered to the transmission system, which can be less than the nuclear plant's output (when storing) or more (when discharging from storage).

### Plant Energy Limit (`eq_hybrid_plant_energy_limit`, line 3418)

**Nuclear output cannot exceed reactor capacity**

```
CAP(i,v,r,t) ≥ GEN_PLANT(i,v,r,h,t)     [for nuclear-stor]
m_cf(i,v,r,h,t) × CAP(i,v,r,t) ≥ GEN_PLANT(...)  [for PVB — CF-derated]
```

Key difference from PVB: Nuclear-stor uses 100% of capacity (no capacity factor derating), reflecting that nuclear plants can operate at full thermal output in any hour.

### Storage Charging from Plant (`eq_hybrid_plant_storage_limit`, line 3440)

**Storage charging cannot exceed nuclear output**

```
GEN_PLANT(i,v,r,h,t) ≥ STORAGE_IN_PLANT(i,v,r,h,t)
```

You can only store as much thermal energy as the reactor is producing in that hour.

### Power Block Capacity Limit (`eq_plant_capacity_limit`, line 3445)

**Total power through the energy island cannot exceed (1 + BCR) × nuclear capacity**

```
CAP(i,v,r,t) × (1 + bcr(i)) ≥ GEN_PLANT + STORAGE_IN_PLANT + GEN_STORAGE + STORAGE_IN_GRID + OPRES
```

The energy island (turbine-generator + electrical equipment) must handle all simultaneous power flows: nuclear output, storage charging/discharging, grid charging, and operating reserves.

### Grid Charging Limit (`eq_cap_storage_in_grid`, line 3467)

**Grid charging power is limited by the grid charging ratio**

```
CAP(i,v,r,t) × gridcharge_ratio(i) ≥ STORAGE_IN_GRID(i,v,r,h,t)
```

When `gridcharge_ratio = 0`, this effectively disables grid charging. This constraint only applies to nuclear-stor (not PVB).

### Storage Power Capacity Limit (`eq_hybrid_storage_capacity_limit`, line 3475)

**Storage power flows cannot exceed storage power capacity (BCR × CAP)**

```
CAP(i,v,r,t) × bcr(i) ≥ GEN_STORAGE + STORAGE_IN_PLANT + STORAGE_IN_GRID
```

### Storage Energy Duration (`eq_storage_duration`, line 3198)

**Storage level cannot exceed energy capacity**

```
CAP_ENERGY(i,v,r,t) ≥ STORAGE_LEVEL(i,v,r,h,t)     [for nuclear-stor, battery, tes]
```

Unlike CSP-TES or PSH (which use a fixed `storage_duration × CAP`), nuclear-stor uses the endogenous `CAP_ENERGY` variable.

### Minimum Duration (`eq_battery_minduration`, line 3265)

**Energy capacity must be at least BCR × minnuclear_storduration × nuclear capacity**

```
CAP_ENERGY(i,v,r,t) ≥ CAP(i,v,r,t) × bcr(i) × minnuclear_storduration
```

Where `minnuclear_storduration = 1.5` hours (from `inputs/scalars.csv`). This prevents the model from building nuclear-stor with trivially small storage.

### Minimum Generation (`eq_mingen_fixed`, line 1321)

**Nuclear-stor uses GEN_PLANT (not GEN) for minimum generation tracking**

```
GEN_PLANT(i,v,r,h,t) ≥ mingen_fixed(i) × avail(i,r,h) × CAP(i,v,r,t)     [nuclear-stor]
GEN(i,v,r,h,t) ≥ ...                                                         [all others]
```

This ensures the minimum generation constraint applies to the nuclear reactor's thermal output, not the net grid output.

### Capacity Credit / PRM (lines 1686–1790)

Nuclear-stor participates in the planning reserve margin (PRM) capacity credit system:

- **`eq_cap_sdbin_energy_balance` (line 1688)**: Uses `CAP_ENERGY` for storage duration bin energy balance:
  ```
  CAP_ENERGY(i,v,r,t) ≥ Σ CAP_SDBIN_ENERGY(i,v,r,ccseason,sdbin,t)
  ```

- **`eq_sdbin_power_limit` (line 1730)**: Nuclear-stor does NOT receive the `hybrid_cc_derate` factor that PVB gets — nuclear-stor's capacity credit is applied directly without a hybrid derate, reflecting that the nuclear plant can dispatch independently of weather conditions.

- **PRM supply (line 1783)**: Nuclear-stor capacity credit appears as: `cc_storage(i,sdbin) × CAP_SDBIN(...)` (no hybrid derate multiplier, unlike PVB).

### Prescribed Energy Capacity (`eq_prescribed_nonRSC`, line 960)

For prescribed capacity builds, energy capacity investment is tracked separately:
```
Σ INV_ENERGY(i,newv,r,tt) ≥ prescribed energy amount    [for battery, tes, nuclear_stor]
```

### RPS / REC Accounting (lines 2664, 2739)

Grid-charged energy is excluded from REC generation (same as PVB):
```
RECs = GEN(i,v,r,h,t) − STORAGE_IN_GRID(i,v,r,h,t)$nuclear_stor(i)
```

This prevents double-counting of grid electricity that was already credited to the original generator.

---

## 10. Storage Dynamics

### Two Charging Paths

Nuclear-stor has two distinct charging paths with different efficiencies:

| Path | Variable | Efficiency Parameter | Typical Value |
|------|----------|---------------------|---------------|
| **Plant charging** (nuclear → TES) | `STORAGE_IN_PLANT` | `storage_eff_nuclear_stor_p(i,t)` | 0.99 for TES; standalone RTE for battery |
| **Grid charging** (grid → heater → TES) | `STORAGE_IN_GRID` | `storage_eff_nuclear_stor_g(i,t)` | Standalone storage RTE (from `plant_char0`) |

**Why is TES plant-charging efficiency 0.99 instead of 1.0?** A small loss (1%) is applied to prevent solver degeneracy — without it, the solver would be indifferent between storing and immediately dispatching, leading to cycling behavior in the solution.

For non-TES storage (e.g., battery), the plant-charging efficiency equals the standalone storage round-trip efficiency (RTE).

Grid charging always uses the standalone storage RTE regardless of storage type.

### Storage Level Tracking (`eq_storage_level`, line 3120)

The storage level equation tracks energy inventory across timeslices:

```
STORAGE_LEVEL(next_h) = STORAGE_LEVEL(h)
    + storage_eff_nuclear_stor_p × hours × STORAGE_IN_PLANT    [plant charging inflow]
    + storage_eff_nuclear_stor_g × hours × STORAGE_IN_GRID     [grid charging inflow]
    − hours × GEN_STORAGE                                       [discharge outflow]
    − reg_reserve_losses                                        [operating reserve losses]
```

### Interday Storage

If `Sw_InterDayLinkage = 1`, nuclear-stor can participate in interday storage arbitrage (shifting energy between representative days). The interday storage level is bounded by `CAP_ENERGY`:

```
CAP_ENERGY(i,v,r,t) ≥ STORAGE_INTERDAY_LEVEL(i,v,r,allszn,t)
```

---

## 11. Objective Function

The objective function in `c_supplyobjective.gms` includes nuclear-stor cost terms across both the capital and operational components.

### Capital Component (`eq_Objfn_inv`)

- **Power capacity investment**: `cost_cap(i,t) × cost_cap_fin_mult(i,r,t) × INV(i,v,r,t)` — uses the blended financial multiplier
- **Energy capacity investment**: `cost_cap_energy(i,t) × cost_cap_fin_mult_nuclear_stor_s(i,r,t) × INV_ENERGY(i,v,r,t)` — uses the storage-side financial multiplier
- **Energy upsizing**: Uses storage-side multiplier (line 157)

### Operational Component (`eq_Objfn_op`)

- **Plant-side VOM**: `cost_vom(i,v,r,t) × GEN_PLANT(i,v,r,h,t)` — VOM is on the nuclear reactor's thermal output
- **Storage-side VOM**: `cost_vom_nuclear_stor_s(i,v,r,t) × GEN_STORAGE(i,v,r,h,t)` — VOM on storage discharge
- **FOM (power)**: `cost_fom(i,v,r,t) × CAP(i,v,r,t)`
- **FOM (energy)**: `cost_fom_energy(i,v,r,t) × CAP_ENERGY(i,v,r,t)`
- **Fuel cost**: Applied to `GEN_PLANT` (not `GEN`) — only the nuclear reactor burns fuel. `GEN_STORAGE` has no fuel cost.

  ```gams
  heat_rate(i,v,r,t) × fuel_price(i,r,t) × GEN_PLANT(i,v,r,h,t)$nuclear_stor(i)
  ```

### PTC Treatment (line 381)

Production tax credits exclude grid-charged energy:

```gams
ptc_value × (GEN(i,v,r,h,t) − STORAGE_IN_GRID(i,v,r,h,t)$nuclear_stor(i))
```

Grid-charged electricity is purchased, not generated, so it should not receive production tax credits.

---

## 12. Reporting

Results reporting in `e_report.gms` handles nuclear-stor by splitting costs and generation into plant-side and storage-side components.

### VOM Cost Reporting (lines 1169–1180, 1425–1435)

- **Plant-side VOM**: `cost_vom × GEN_PLANT.l` (not `GEN.l`)
- **Storage-side VOM**: `cost_vom_nuclear_stor_s × GEN_STORAGE.l`
- **Reported separately as** `cost_vom` and `cost_vom_stor` in the `costnew` output

### Fuel Cost Reporting (lines 1183–1188, 1468–1474)

```gams
heat_rate × fuel_price × GEN_PLANT.l(i,v,r,h,t)$nuclear_stor(i)
```

Only the plant side burns fuel.

### Investment Cost Reporting (line 1323)

Energy capacity investment is reported alongside batteries and standalone TES:

```gams
sum{v$[valinv(i,v,r,t)$(battery(i) or tes(i) or nuclear_stor(i))],
    cost_cap_fin_mult_out(i,r,t) × cost_cap_energy(i,t) × INV_ENERGY.l(i,v,r,t) }
```

### Grid Charging in Load Balance (line 394)

Grid charging from nuclear-stor is subtracted from generation in the storage intake reporting:

```gams
- STORAGE_IN_GRID.l(i,v,r,h,t)$[nuclear_stor(i)$Sw_HybridPlant]
```

---

## 13. Solve-Time Processing

### Parameter Rounding (`d_solveprep.gms`, lines 78–102)

Before each solve, storage-related parameters are rounded to 2 decimal places for numerical stability:

```gams
cost_vom_nuclear_stor_s(i,v,r,t) = round(..., 2)
storage_eff_nuclear_stor_g(i,t)  = round(..., 2)
storage_eff_nuclear_stor_p(i,t)  = round(..., 2)
```

### Variable Fixing (`d2_varfix.gms`, lines 28–36)

In iterative solve windows, energy-related variables for nuclear-stor are fixed for past years:

```gams
CAP_ENERGY.fx(i,v,r,tfix)$(battery(i) or tes(i) or nuclear_stor(i))     = CAP_ENERGY.l(...)
INV_ENERGY.fx(i,v,r,tfix)$(battery(i) or tes(i) or nuclear_stor(i))     = INV_ENERGY.l(...)
CAP_SDBIN_ENERGY.fx(i,v,r,ccseason,sdbin,tfix)$(...nuclear_stor(i)...)  = CAP_SDBIN_ENERGY.l(...)
```

---

## 14. Comparison with Other Hybrid Technologies

| Aspect | Nuclear-Stor | PV+Battery (PVB) | CSP-TES |
|--------|--------------|-------------------|---------|
| **Energy source** | Nuclear (dispatchable) | Solar PV (variable) | Solar CSP (variable) |
| **Storage tech** | TES (molten salt) or battery | Battery (Li-ion) | TES (built-in) |
| **Capacity ratio** | `bcr(i)` (configurable, e.g., 0.45–0.65) | `bcr(i)` (from ILR/BIR config) | Fixed (solar multiple) |
| **Plant CF** | 100% — no hourly derating | `m_cf(i,v,r,h,t)` — solar variability | CSP solar resource |
| **Energy capacity** | Endogenous via `CAP_ENERGY` | Fixed via `GSw_PVB_Dur` | Fixed via `storage_duration(i)` |
| **Power block** | (1 + BCR) × CAP | CAP / ILR | CAP |
| **Grid charging** | Yes, via `gridcharge_ratio` | Yes, via `STORAGE_IN_GRID` | No |
| **Plant charging efficiency** | 0.99 (TES) / RTE (battery) | RTE / inverter_eff | Inherent in CSP model |
| **Grid charging efficiency** | Standalone storage RTE | Standalone battery RTE | N/A |
| **Min duration constraint** | `bcr × minnuclear_storduration` | None (fixed duration) | Inherent |
| **Fuel cost** | Applied to `GEN_PLANT` only | None (solar is free) | None |
| **PTC exclusion** | Grid-charged energy excluded | Grid-charged energy excluded | N/A |

---

## 15. How to Modify or Extend

### Adding a New Nuclear-Stor Type (e.g., Type 9)

1. **Add to technology set**: Add `Nuclear-Stor9` to `inputs/sets/i.csv`
2. **Add subtech**: Add `NUCLEAR-STOR9` to `inputs/sets/i_subtech.csv`
3. **Add to tech-subset-table**: Add a `Nuclear-Stor9` row to `inputs/tech-subset-table.csv` with the same column values as existing nuclear-stor types (STORAGE=YES, STORAGE_HYBRID=YES, THERMAL_STORAGE=YES, CONV=YES, NUCLEAR-STOR=YES, NUCLEAR-STOR9=YES)
4. **Add column header**: Add `NUCLEAR-STOR9` as a column in `tech-subset-table.csv`
5. **Add set declaration in GAMS**: Add `nuclear_stor9(i)` to `b_inputs.gms` set declarations (~line 480) and the assignment block (~line 1078)
6. **Add banning logic**: Extend the `$ifthen` blocks in `b_inputs.gms` (lines 857–898) to handle the new type count
7. **Add to config set**: Add `Nuclear-Stor9` to `inputs/sets/nuclear_stor_config.csv`
8. **Update case files**: Set `GSw_NuclearStor_Types` to include `9` and provide values for BCR, storage tech, gen tech, and grid charging

All other input files will be automatically populated by `propagate_nuclearstor_tech_rows()`.

### Changing the Storage Technology

To pair nuclear with a different storage technology (e.g., a next-generation TES):

1. Ensure the new storage tech exists in `inputs/sets/i.csv` and has cost data in `plantchar_*.csv`
2. Set `GSw_NuclearStor_StorageTechs` to the new tech name (e.g., `tes-nextgen_tes-nextgen_...`)
3. The tech should have rows in the TES subset of `tech-subset-table.csv` for automatic `tes(i)` / `thermal_storage(i)` membership
4. If the new tech is NOT a TES type, the non-thermal cost formula applies (no turbine-generator/electrical cost adjustment)

### Changing the Generation Technology

To pair storage with a different generation technology (e.g., a future advanced reactor):

1. Ensure the new generator tech exists in `inputs/sets/i.csv` and has cost data in `plantchar_*.csv`
2. Set `GSw_NuclearStor_GenTechs` to the new tech name (e.g., `nuclear-advreactor_nuclear-advreactor_...`)
3. The tech should have rows in `tech-subset-table.csv`
4. The new generator tech's cost and performance parameters will automatically propagate to the nuclear-stor variants via `propagate_nuclearstor_tech_rows()`

### Adding New Parameters

If you need a new nuclear-stor-specific parameter:

1. **Option A (from generator tech)**: No action needed — `propagate_nuclearstor_tech_rows()` will automatically clone the generator tech's rows for any new parameter CSV
2. **Option B (from storage tech)**: Add handling in `calc_financial_inputs.py` via `append_nuclear_stor_parameters()`, or manually populate the CSV
3. **Option C (nuclear-stor-specific)**: Create a new CSV with explicit nuclear-stor entries. If the CSV already contains "nuclear-stor" text, the propagation function will skip it (which is correct for bespoke parameters)
4. **In GAMS**: Load the parameter in `b_inputs.gms` with a `$nuclear_stor(i)` conditional

### Common Pitfalls

1. **Duplicate rows from propagation**: If `plantchar_*.csv` is NOT in the skip list AND `plantcostprep.py` also creates nuclear-stor rows, you'll get duplicates. The skip list prevents this — do NOT remove `plantchar_*` from it.
2. **Missing rows from propagation**: If a new file contains nuclear-relevant rows but uses a non-standard column name for the technology identifier, the heuristic (`_looks_like_tech_column()`, requiring ≥60% match against `i.csv`) may fail to detect it. Solution: rename the column to `i` or `*i`.
3. **Financial multiplier ordering**: The nuclear-stor financial multiplier assignment in `d1_financials.gms` MUST happen before the global trim step. If you add new financial calculations, be mindful of ordering.
4. **Set membership**: Nuclear-stor must be in `storage_hybrid(i)` for hybrid plant constraints to apply. If creating a new variant, ensure `tech-subset-table.csv` has `STORAGE_HYBRID=YES`.
5. **Grid charging without heater cost**: If grid charging is enabled but the storage tech has no `heater_char` data, the heater cost term in the capital cost formula will be zero, which may be unintended.

---

## 16. File Reference

### GAMS Model Files

| File | Nuclear-Stor Content |
|------|---------------------|
| `b_inputs.gms` | Technology set declarations (L472–480), switch/ban logic (L783–898), set assignment from tech-subset-table (L1066–1078), linking set loading (L1135–1172), BCR & grid charging parameters (L4456–4485), capital cost parameters (L4510–4524), VOM parameters (L4641–4647), FOM parameters (L4718–4730), storage efficiency (L5965–5977), capital cost composition (L6060–6091), storage duration (L6105–6120) |
| `c_supplymodel.gms` | Variable declarations (L47–57), min generation (L1321), PRM/capacity credit (L1688–1710), storage level tracking (L3120–3156), storage duration (L3198–3211), min duration (L3265–3275), interday bounds (L3359–3379), hybrid plant equations (L3402–3495) |
| `c_supplyobjective.gms` | VOM costs (L200–215), FOM costs (L220–230), fuel costs (L255–260), energy upsizing (L155–160), PTC exclusion (L381) |
| `d1_financials.gms` | Financial multiplier splitting (L75–95), financing risk adjustment (L168–178), cost-weighted average (L220–260) |
| `d_solveprep.gms` | Parameter rounding (L78, L101–102) |
| `d2_varfix.gms` | Variable fixing for iterative solves (L28, L33, L36) |
| `e_report.gms` | VOM splits (L1169–1180, L1425–1435), fuel cost (L1468–1474), investment cost (L1323), grid charging (L394) |

### Python Input Processing

| File | Nuclear-Stor Content |
|------|---------------------|
| `input_processing/copy_files.py` | Configuration CSV generation (L1640–1690), `propagate_nuclearstor_tech_rows()` function (L1943–2200+) |
| `input_processing/calc_financial_inputs.py` | `append_nuclear_stor_parameters()` for degradation/financial params (L85–102) |
| `input_processing/plantcostprep.py` | Heater cost processing for TES (L412–450) |

### Input Data Files

| File | Content |
|------|---------|
| `inputs/sets/i.csv` (L44–53) | Technology set entries: Nuclear-Stor1 through Nuclear-Stor8 |
| `inputs/sets/i_subtech.csv` (L69–77) | Subtech entries: NUCLEAR-STOR parent + NUCLEAR-STOR1–8 |
| `inputs/sets/nuclear_stor_config.csv` | Configuration set listing Nuclear-Stor1–8 |
| `inputs/tech-subset-table.csv` | Subset memberships (STORAGE, STORAGE_HYBRID, THERMAL_STORAGE, CONV) |
| `inputs/scalars.csv` (L28, L63, L80) | `electrical_cost=53.6`, `minnuclear_storduration=1.5`, `startcost_plant_nuc_stor=70` |

### Generated at Runtime (in `inputs_case/`)

| File | Content |
|------|---------|
| `nuclear_stor_bcr.csv` | BCR values indexed by type |
| `nuclear_stor_gridcharging.csv` | Grid charging ratios indexed by type |
| `nuclear_stor_storagetechs.csv` | Storage tech mapping per type |
| `nuclear_stor_gentechs.csv` | Generator tech mapping per type |

### Case Configuration Files

| File | Content |
|------|---------|
| `cases_nuclearstor_main.csv` | Standard 6-type test/control cases with nuclear mandate variants |
| `cases_nuclearstor_gridcharging.csv` | Grid charging sensitivity cases (50%, 100%) |
| `cases_nuclearstor_marketsensitivity.csv` | Market sensitivity cases (gas price, demand, transmission, IRA) |
| `cases_nuclearstor_test.csv` | Testing configuration |
| `cases_nuclearstor_master.csv` | Master case list |
| `cases_nuclearstor_combined.csv` | Combined case list |
