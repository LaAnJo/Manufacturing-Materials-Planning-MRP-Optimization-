# Power BI Dashboard — Manufacturing Materials Planning & MRP Optimization

**The project contains POWER BI-READY DATA + DAX + a full visual design, not a native `.pbix` report.** A native PBIX file must be created and saved in Power BI Desktop on Windows. `charts/powerbi_dashboard_preview.png` shows the intended layout, not a Power BI screenshot.

## 1. Start

Run `python -m src.pipeline` in the project root if you want to regenerate all CSV files.
Open **Power BI Desktop → Blank report → Home → Get data → Text/CSV**. Import each CSV below; select Load. Rename query tables exactly:

| Path | Model table | Role |
|---|---|---|
| `data/processed/weeks.csv` | weeks | DimWeek (12 buckets) |
| `data/processed/materials.csv` | materials | DimMaterial |
| `data/processed/products.csv` | products | DimProduct |
| `data/processed/bom.csv` | bom | FactBOM |
| `data/processed/production_orders.csv` | production_orders | FactWorkOrders |
| `outputs/weekly_mrp.csv` | weekly_mrp | FactWeeklyMRP |
| `outputs/purchase_recommendations.csv` | purchase_recommendations | FactPurchasePlan |
| `data/processed/inventory_initial.csv` | inventory_initial | Inventory snapshot (optional) |
| `data/processed/scheduled_receipts.csv` | scheduled_receipts | Scheduled PO receipts (optional) |

For date text, set `week_start`, `production_date`, `planned_release_date`, `requested_receipt_date` to **Date** in Power Query/Model view. Note that `weekly_mrp.planned_release_date` has empty strings for rows with no recommended order; Power Query can convert blank values to null before changing the data type.
Set kg and monetary figures to Decimal Number; counts and week index to Whole Number. Turn OFF automatic aggregation on IDs.

## 2. Model relationships (single-direction from dimensions to facts)

- `weeks[week_index]` (1) → `weekly_mrp[week_index]` (*)
- `weeks[week_index]` (1) → `purchase_recommendations[week_index]` (*)
- `weeks[week_index]` (1) → `production_orders[week_index]` (*)
- `materials[material_id]` (1) → `weekly_mrp[material_id]` (*)
- `materials[material_id]` (1) → `purchase_recommendations[material_id]` (*)
- `materials[material_id]` (1) → `bom[material_id]` (*)
- `products[product_id]` (1) → `production_orders[product_id]` (*)
- `products[product_id]` (1) → `bom[product_id]` (*)

Avoid joining `weekly_mrp` and `purchase_recommendations` directly (both are facts); avoid bidirectional loops. Use `weeks[week_start]` to filter all three time-based facts; avoid cross-filtering fact tables directly.

## 3. Add DAX measures

Choose Modeling → New measure and paste **one** measure at a time from `DAX_MEASURES.dax` (omit comments and separating lines). Use currency formatting for purchase value and % formatting for feasible order rate.

## 4. Report page 1: Planning overview (16:9 canvas)

Page title: **MATERIALS PLANNING | CONTROL TOWER**; subtitle **12-week simulated concrete MRP · as-of 21 Oct 2026**.

Top slicers: `materials[material_name]` on the left, `weeks[week_start]` on the right. The Week slicer filters production orders, MRP and purchasing. The Material slicer does not filter production orders because the work-order fact has no direct Material relationship (this is correct).

Top cards:
1. `[Planned Volume m3]` — 2,977.3 m³ (all weeks, not filtered by material)
2. `[Material Demand Tonnes]` — 6,723.8 t (material filter applies)
3. `[Proposed Purchase Value USD]` — $275,391 (material filter applies)
4. `[Late Release Lines]` — 5 (material filter applies)

Visual A: **Clustered column**: Axis `weeks[week_start]`; Values `Material Demand Tonnes` (demand trend).

Visual B: **Stacked/clustered bar**: Axis `materials[material_name]`; Values `Planned Receipts Tonnes` (purchasing plan by material).

Visual C: **Line chart**: Axis `weeks[week_start]`; Values `Feasible Backlog At Latest Week Tonnes` and `Baseline Backlog At Latest Week Tonnes` (point-in-time backlog trend). Keep weeks sorted ascending.

Visual D: **Table**: `purchase_recommendations[material_name]`, `[primary_supplier]`, `[planned_release_date]`, `[requested_receipt_date]`, `[order_qty_kg]`, `[extended_cost_usd]`, `[release_status]`. Use conditional formatting for `late_release_flag=1`.

## 5. Report page 2: Shortage & lead time risk

Four cards: `[Baseline Shortage Material Weeks]`, `[Lead Feasible Shortage Material Weeks]`, `[Feasible Order Rate]`, `[Feasible Backlog At Latest Week Tonnes]`.

- **Matrix heatmap:** rows `weekly_mrp[material_name]`; columns `weeks[week_start]`; values `MAX(weekly_mrp[feasible_shortage_flag])`; background color = red for 1, green for 0.
- **Line chart:** weeks on X; `Feasible Backlog At Latest Week Tonnes` on Y.
- **Supplier lead-time bar:** category `materials[material_name]`; value `materials[lead_time_weeks]`, summarize by MAX rather than SUM.
- **Detail table:** material, week, net requirement, planned receipt, planned release date, baseline backlog, feasible backlog.

## 6. Report page 3: BOM and production plan

- **Column chart:** `production_orders[product_id]` vs `Planned Volume m3`.
- **Matrix:** `bom[product_id]` rows; `bom[material_id]` columns; value `MAX(bom[kg_per_m3])` (kg per m³, not a total gross material demand).
- **Table:** product ID, nominal target strength, observed 28d lab strength, number of source rows, cost per m³ from `products`.

## 7. Definitions / quality checks

- `gross_requirement_kg`: BOM quantity (kg/m³) × planned production volume (m³), summed to material/week.
- `planned_receipt_kg`: ordered using safety stock, MOQ, and order multiples in idealized MRP.
- `late_release_flag`: the release needed for the ideal receipt is before the as-of date. The proposed PO is **not** credited to its requested week; instead its supply is deferred to the first feasible standard-lead-time delivery week. No expedited arrival is automatically assumed.
- `baseline_backlog_kg`: cumulative shortfall with **only** beginning stock and already-scheduled receipts, ignoring new MRP suggestions.
- `feasible_backlog_kg`: cumulative shortfall with beginning stock, scheduled receipts, and new MRP receipts shifted forward when the original release was late.
- `baseline_shortage_flag`, `feasible_shortage_flag`: count *material-weeks* with negative projected stocks, NOT missed production orders or realized stockouts.
- Backlog fields are **stock balances** as of one week; do not SUM over weeks in a headline KPI. Use the `... At Latest Week ...` measures above.
- Reconcile totals against `outputs/kpi_summary.csv`. Slicers change context, so compare unfiltered pages only.
- Illustrative prices and suppliers do NOT reflect real purchase contracts. The recipes are observed experimental mixture examples, NOT structural concrete specifications.

## 8. Finish

Save as `reports/Manufacturing_Materials_MRP_Optimization.pbix` via **File → Save as** in Power BI Desktop. Export screenshots into `charts/` and upload this folder to your GitHub repository.

Official Microsoft documentation: https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tutorial-create-measures
