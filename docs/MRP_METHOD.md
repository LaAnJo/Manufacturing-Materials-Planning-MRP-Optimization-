# MRP method — business logic, formulas, and limitations

## Source-derived versus scenario-generated

**Observed:** experimental concrete ingredient kg/m³, curing age in days, measured concrete compressive strength MPa.

**Synthetic:** work order count/dates/m³, safety stock, starting inventory, scheduled receipts, supplier IDs, standard lead time, minimum order quantity, rounding lots, USD/kg material prices.

Product recipes are selected from observed **28-day** sample observations, targeting nominal 25, 35, 45, and 55 MPa. These are illustrative research mix specimens, not construction-grade certified product specifications. The recipe selection is based on observed strengths and assumed ingredient unit costs and must not be used for real structural production.

## Product-level BOM explosion

For production order `o`, product `p`, raw material `m`:

`required_kg(o,m) = production_volume_m3(o) × kg_per_m3(p,m)`

`gross_requirement_kg(m,w) = SUM(required_kg(o,m))` for all work orders due in week `w`.

## Classical bucket-based projected available balance

For each material and weekly bucket:

- `pre_replenishment = opening_unconstrained_kg + scheduled_receipt_kg - gross_requirement_kg`
- `net_requirement_kg = max(0, safety_stock_kg - pre_replenishment)`
- If net requirement > 0: `planned_receipt_kg = CEILING(max(MOQ, net_requirement_kg), order_multiple_kg)`
- Otherwise: planned receipt = 0.
- `projected_end_unconstrained = pre_replenishment + planned_receipt_kg`
- The following week's `opening_unconstrained` equals previous week's `projected_end_unconstrained`.

All weights in kg; warehouse consumption assumes production takes place in the designated week, and scheduled receipts are available in that bucket.

## Lead-time feasibility / delay model

- Ideal purchase release = start of requested receipt week − primary supplier lead time in weeks.
- Scenario as-of date = 2026-10-21. Ideal releases before this are flagged (`late_release_flag=1`).
- A late order is **not** credited to the original requested week in the feasible scenario.
- Instead its simulated standard-lead-time arrival is shifted forward to the **first available weekly bucket on or after** `AS_OF + lead_time_weeks × 7 days`, but never before its requested week.
- The `delivery_delay_weeks` and `feasible_receipt_date` are included on each proposed PO; suppliers would still need to verify these dates in real practice.
- **This is NOT finite-capacity production scheduling, not actual supplier confirmation, and not an expedited-shipping simulation.**

## Two scenarios for material balance (kg)

**Baseline (no newly planned purchases):** previous projected balance + existing scheduled receipts − gross requirements. It can go negative, representing unmet quantities carried as a backlog; a negative stock is not actual physical on-hand inventory.

**Lead-time-feasible MRP:** previous feasible projected balance + scheduled receipts + purchase recommendations delivered on feasible dates − gross requirements. Negative balances are carried as cumulative modeled unfilled material demand, not as literal negative warehouse stock.

`backlog_kg = MAX(0, -projected_balance_kg)`.

`shortage_flag = 1 if projected_balance_kg < 0 else 0`.

**IMPORTANT:** You may add gross demand or purchase value over time, and count material-week shortage flags over time. You must **not add** backlog balances across weeks because the same unfilled units may persist across multiple weeks. Instead inspect backlog at a specific selected week, or the horizon's final week.

## Simplifications and boundaries

- Weekly-bucket MRP, 12 weeks, rather than daily detail.
- Seven ingredient materials, four illustrative product BOMs.
- No scrap/yield loss, QC blocking, alternative substitution, actual factory capacity, supplier calendars, batch minimums, multiple suppliers, confirmed deliveries, curing-capacity constraints, WIP, or probabilistic demand forecasting.
- Water is modeled as purchased/supplied material with zero-week lead time for instructional consistency.
- Costs are illustrative direct raw-material acquisition only; no labor, transport, taxation, spoilage, or overhead.
- Theoretical lab mix strength does not guarantee 28-day production strength or code compliance.
- Real plants should validate material specifications, supplier commitments, quality tests, site-specific processes and regulatory codes before use.
