# `valnew.csv` (Value of New Investments)

This note documents the components (first column) in `outputs/valnew.csv`, what they mean, and how ReEDS calculates them.

**Source of truth**: the `valnew(...)` calculations are defined in the “Value (Revenue) of new builds” block in [e_report.gms](../e_report.gms#L1018-L1115).

## File layout

`valnew.csv` is written as a long table:

- `component`: the value stream or helper quantity (e.g., `MW`, `val_load`, `val_resmarg`)
- `i`: technology
- `r`: region (BA)
- `t`: model year
- `Value`: numeric value (units depend on `component`)

The `component` index is overloaded: it includes both helper quantities (like `MW` and `MWh`) and monetized value streams (like `val_load`).

## Important conventions used in the formulas

The formulas below reference the same objects used in GAMS:

- `INV.l(i,v,r,t)`, `INV_REFURB.l(i,v,r,t)`: solution levels for new-build and refurbishment investment decisions
- `CAP.l(i,v,r,t)`: solution level for capacity
- `GEN.l(i,v,r,h,t)`: solution level for generation in timeslice `h`
- `STORAGE_IN.l(i,v,r,h,t)`: charging / pumping (subtracted to get **net injections** for energy/capacity value)
- `hours(h)`: number of real-world hours represented by timeslice `h`
- `reqt_price(type, subtype, r, h, t)`: shadow price (dual) of requirement `type` at that index
- `reqt_price_sys(...)`: system-average (aggregate) price profile for the same requirement
- `reqt_quant(type, subtype, r, h, t)`: requirement quantity

Also:

- `valinv(i,v,r,t)` is used as a filter for “new investment vintages” that are relevant for this report.
- `tfirst(t)` is true in the first solve year; most `valnew` entries are not defined there.
- `ilr(i)` is the inverter-loading ratio adjustment used for PV-style technologies.
- `h_stress_t(allh,t)` selects “stress hours” used for PRM valuation when `Sw_PRM_CapCredit=0`.

### Net injections used in several value terms

Many value streams use **net injections** rather than gross generation:

- `net_inj(i,v,r,h,t) = GEN.l(i,v,r,h,t) - STORAGE_IN.l(i,v,r,h,t)`

…but the subtraction is only applied when the tech is a standalone storage technology or added pumped hydro:

- subtract charging if `[storage_standalone(i) or hyd_add_pump(i)]`

This makes `val_load`/`val_resmarg` behave like market revenue from net energy supplied.

## Components (helper quantities)

### `MW` (new-build capacity proxy)

**Units**: MW

**Meaning**: the amount of “new investment” capacity attributed to year `t` for tech `i` in region `r`.

**Calculation** (conceptual):

- Sum new-build plus refurbishment investments over investment vintages `v`, then adjust by `ilr(i)`:

$$
\text{MW}_{i,r,t} = \frac{\sum_{v \in \text{valinv}}\left( INV_{i,v,r,t} + INV\_REFURB_{i,v,r,t} \right)}{ilr(i)}
$$

**Notes**:

- Not reported in the first model year: gated by `not tfirst(t)`.
- For PV-like technologies, dividing by `ilr(i)` converts inverter-side investment to a consistent MW basis.

### `inv_cap_ratio` (investment-to-capacity ratio)

**Units**: dimensionless

**Meaning**: a weighting factor used to scale generation/value so it reflects the “new” portion of a tech in a region-year when capacity exists from multiple vintages.

**Calculation** (as implemented):

- For each relevant vintage, compute `investment / capacity` and sum:

$$
\text{inv\_cap\_ratio}_{i,r,t} = \sum_{v: CAP_{i,v,r,t} > 0}\frac{INV_{i,v,r,t} + INV\_REFURB_{i,v,r,t}}{CAP_{i,v,r,t}}
$$

**Why it exists**: `valnew` is “value of new investments”, but most operational quantities (`GEN`, `OPRES`) are reported for the whole tech-vintage. This ratio is used to allocate a share of operational value to the marginal/new investment.

### `MWh` (new-build energy proxy)

**Units**: MWh (annual, timeslice-weighted)

**Meaning**: an energy quantity associated with the new investments.

**Calculation**:

- Default: sum annual generation for new-investment vintages and scale by `inv_cap_ratio`.
- For VRE, use **uncurtailed** generation so the “available energy” of new VRE isn’t suppressed by system-level curtailment.

Conceptually:

$$
\text{MWh}_{i,r,t} = \left(\sum_{v \in \text{valinv}} \text{gen\_ivrt}(i,v,r,t)\right)\cdot \text{inv\_cap\_ratio}_{i,r,t}
$$

For VRE, `gen_ivrt_uncurt` replaces `gen_ivrt`.

### `MW` / `MWh` benchmarks

These are not tied to a specific technology; they represent the size of the “market” being valued.

- `valnew('MWh','benchmark',r,t)`: total load requirement energy in region `r`.
- `valnew('MWh','benchmark','sys',t)`: total load requirement energy systemwide.
- `valnew('MW','benchmark',r,t)`: annual PRM requirement in region `r`.
- `valnew('MW','benchmark','sys',t)`: annual PRM requirement systemwide.

## Components (value streams)

All value components below are in currency units (model dollars), with the same scaling conventions as the rest of the report (notably `cost_scale` is already accounted for in the relevant prices).

### `val_load` (energy value at regional load prices)

**Units**: 2004$ / year (annual value in model year `t`, not discounted)

**Meaning**: energy-market value of the new investment, valued at the regional hourly (timeslice) load price.

**Calculation**:

$$
\text{val\_load}_{i,r,t} = \left(\sum_{v,h \in \text{valinv}} \text{net\_inj}_{i,v,r,h,t} \cdot hours(h) \cdot price^{load}_{r,h,t}\right)\cdot \text{inv\_cap\_ratio}_{i,r,t}
$$

where `price^load` is `reqt_price('load','na',r,h,t)`.

Because `reqt_price('load',...)` is explicitly converted to **$/MWh** in the reporting step (it divides the load-balance marginal by `hours(h)` and removes `pvf_onm(t)`), multiplying by `net_inj` (MW) and `hours(h)` yields dollars for that model year.

**Interpretation**:

- If a tech tends to inject more during high-price slices, `val_load` is higher.
- For storage, charging reduces net injections and therefore reduces `val_load` in those charging slices.

### `val_load_sys` (energy value at system-average load prices)

**Units**: 2004$ / year (annual value in model year `t`, not discounted)

**Meaning**: counterfactual energy value if the same injection profile were valued at the *system average* load price profile.

Same as `val_load` but uses `reqt_price_sys('load','na',h,t)`.

**Use case**: comparing `val_load` vs `val_load_sys` isolates whether the tech benefits from being located in a high-price region versus just the overall system value.

### `val_resmarg` (PRM / stress-hour capacity value)

**Meaning**: value of the new investment in meeting the planning reserve margin (PRM) requirement.

There are two model formulations; which one is used depends on `Sw_PRM_CapCredit`.

#### Case A: `Sw_PRM_CapCredit = 0` (stress-hour energy proxy)

- Value is computed using net injections during stress hours multiplied by the stress-hour PRM price:

$$
\text{val\_resmarg}_{i,r,t} = \left(\sum_{v,allh \in \text{stress}} \text{net\_inj}_{i,v,r,allh,t} \cdot price^{PRM}_{r,allh,t}\right)\cdot \text{inv\_cap\_ratio}_{i,r,t}
$$

where stress is `h_stress_t(allh,t)` and price is `reqt_price('res_marg','na',r,allh,t)`.

#### Case B: `Sw_PRM_CapCredit = 1` (capacity credit for VRE)

- For VRE, ReEDS uses capacity credit `m_cc_mar(i,r,ccseason,t)` and seasonal PRM prices.

Conceptually:

$$
\text{val\_resmarg}_{i,r,t} = \sum_{ccseason} m\_cc\_mar(i,r,ccseason,t) \cdot \text{MW}_{i,r,t} \cdot price^{PRM}_{r,ccseason,t}
$$

**Note in code**: non‑VRE under the CapCredit formulation is not fully covered in this report block (there’s a comment about needing `cap_firm()` with vintage).

### `val_resmarg_sys` (system-average PRM value)

Same as `val_resmarg`, but with `reqt_price_sys('res_marg',...)` instead of regional prices.

### `val_opres` (operating reserve value)

**Meaning**: value (or cost impact) of the new investment with respect to operating reserve requirements.

There are three tech cases in the code:

1) **Non-wind / non-PV / non-PVB**: direct reserve provision valued at operating reserve prices.

$$
\text{val\_opres}_{i,r,t} = \left(\sum_{ortype,v,h} OPRES_{ortype,i,v,r,h,t} \cdot hours(h) \cdot price^{OR}_{ortype,r,h,t}\right)\cdot \text{inv\_cap\_ratio}_{i,r,t}
$$

2) **Wind**: treated as an *increase in reserve requirements* proportional to wind generation (`orperc(ortype,'or_wind')`), so it enters with a negative sign.

3) **PV / PVB**: similar negative treatment based on PV capacity in daylight hours (`dayhours(h)`), scaled by `CAP/ilr`.

System version `val_opres_sys` uses `reqt_price_sys('oper_res',...)`.

**Practical note**: it’s common for `val_opres` to be absent from `valnew.csv` if `OPRES.l(...)` is zero or if opres is disabled/has no modeled hours.

### `val_rps` (state RPS REC value)

**Meaning**: value of state renewable portfolio standard (RPS) credits associated with the tech’s generation.

**Calculation**:

- For each RPS category `RPSCat`, multiply generation by a state mapping and multipliers, then value at the state RPS price.

Conceptually:

$$
\text{val\_rps}_{i,r,t} = \left(\sum_{v,h,RPSCat} GEN_{i,v,r,h,t} \cdot REC\_mult(i,RPSCat,r,...) \cdot hours(h) \cdot price^{RPS}_{RPSCat,r,t}\right)\cdot \text{inv\_cap\_ratio}_{i,r,t}
$$

System version `val_rps_sys` uses `reqt_price_sys('state_rps',...)`.

### Benchmarks for value streams (`'benchmark'` / `'sys'`)

For `val_load`, `val_resmarg`, `val_opres`, and `val_rps`, there are also benchmark rows that compute the “total market value” of that requirement:

- Regional benchmark typically looks like: `sum price * quantity`.
- System benchmark sums across all regions.

These are useful for answering questions like “how big is the PRM value pool in WI in 2050?” independent of any one technology.

## Why you may see “more components” in some runs

Different ReEDS configurations can change which `valnew` rows are nonzero and therefore written:

- If operating reserves aren’t modeled for any hours (or `OPRES.l` is zero), `val_opres` won’t appear.
- If state RPS isn’t active (no binding RPS constraints), `val_rps` may be zero.
- If the run’s output pipeline changes (custom branches), additional `valnew('val_*',...)` terms could be added in `e_report.gms`.

If you ever see a `component` in a run that is not listed above, the quickest way to resolve it is to search for `valnew('that_component'` in the run’s `e_report.gms`.
