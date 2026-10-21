# Manufacturing Materials Planning & MRP Optimization

**Python · SQL · Excel · Power BI · Materials Requirements Planning (MRP)**

> **Portfolio simulation — not a production ERP system.** The uploaded `concrete.csv` supplies real experimental concrete mix ingredient quantities and strength measurements. **ALL** production work orders, supplier identities, stock levels, incoming receipts, lead times, purchase quantities, prices and procurement results are synthetic and reproducible. Mixes are demonstrations, not certified structural concrete recipes.

![Power BI-inspired MRP control tower preview](charts/powerbi_dashboard_preview.png)

## Business problem

Given upcoming concrete manufacturing orders and a bill of materials (BOM), what raw materials will be needed each week? How can purchasing recommend appropriately sized material receipts while protecting safety stock and identifying orders that cannot meet the required dates under standard supplier lead times?

This project addresses **time-phased gross requirements**, BOM explosion, opening inventory, scheduled receipts, safety stock, minimum order quantities (MOQ), lot multiples, planned order releases and projected material shortages.

## Key scenario results

| Metric | Result | Description |
|---|---:|---|
| Observed concrete dataset rows | 1,030 | Original mix/strength observations |
| 28-day measurements screened | 425 | Ingredient recipe selection |
| Illustrative concrete recipes | 4 | Nominal strength targets 25 / 35 / 45 / 55 MPa |
| Simulated production orders | **144** | 3 × 4 recipes × 12 weeks |
| Planned concrete production | **2,977.3 m³** | Simulated scheduled volume |
| Exploded ingredient demand | **6,723.8 tonnes** | BOM × planned m³ |
| Recommended purchase lines | **67** | MRP net requirements after rounding |
| Proposed purchase value | **$275,391** | Hypothetical prices in USD/kg |
| Purchase lines requiring lead-time review | **5** | Requested release before as-of date |
| Baseline shortage material-weeks | **70** | Without new purchase recommendations |
| Lead-feasible shortage material-weeks | **4** | After shifting delayed deliveries to first feasible week |

**Caution:** Material-week alerts are not proven factory stoppages or missed work orders. Baseline/feasible backlogs are **stock balances at a point in time**, and must not be summed over weeks. A decrease in simulated shortage alerts is not an independently validated production improvement.

## How the input dataset is used

The source has nine columns: `cement`, `slag`, `ash`, `water`, `superplastic`, `coarseagg`, `fineagg`, `age`, `strength`.

The seven ingredient columns represent **kg required per m³ of concrete**; `age` means curing age in days and `strength` is measured compressive strength in MPa. Source documentation and license: [UCI Concrete Compressive Strength (Yeh, 1998)](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength), DOI: [10.24432/C5PK67](https://doi.org/10.24432/C5PK67), **CC BY 4.0**.

We select four illustrative observed 28-day recipes matching nominal strength bands; these are experimental mix rows and are **not certified, engineered or qualified for field use**. The per-m³ ingredient requirements serve as demonstration BOMs. We generate synthetic future production orders from a fixed random seed to create a realistic MRP classroom scenario.

## What is implemented

1. **BOM explosion:** `planned_volume_m3 × kg_per_m3` → material requirements in kg.
2. **Weekly net requirements:** compare gross demand with projected on-hand and scheduled receipts, target safety stock.
3. **Lot sizing:** round proposed receipts to MOQ and order multiples.
4. **Planned releases:** subtract each material's modeled supplier lead time from the ideal receipt date.
5. **Lead-time constraints:** if the release date is before the scenario as-of date, flag the PO and reschedule its feasible receipt to the first compatible weekly bucket. Do **not** credit phantom on-time supply.
6. **Inventory scenarios:** compare no-new-PO baseline with feasible proposed deliveries and show week-end backlog exposure.
7. **Supplier purchasing:** quantify proposed lines, dated release queue, and illustrative spend.
8. **Validation:** formula-driven Excel checks, reproducible Python pipeline and tests, SQL queries, BI-ready CSVs.

For exact assumptions and definitions, see [MRP Methodology](docs/MRP_METHOD.md) and [Data Dictionary](docs/DATA_DICTIONARY.md).

## Project files

```text
Manufacturing_Materials_MRP_Optimization/
├── README.md
├── LICENSE_NOTE.md
├── requirements.txt
├── app.py                              # Interactive Streamlit control tower
├── charts/
│   ├── interactive_mrp_dashboard.html  # Fully offline interactive dashboard
│   └── powerbi_dashboard_preview.png   # Power BI report layout reference
├── data/
│   ├── raw/concrete.csv                # Original user-uploaded dataset
│   └── processed/                     # Recipes, BOM, 12-week dimension, inventory, suppliers, orders
├── outputs/                            # Weekly MRP, purchase plan, KPIs, explosion
├── reports/MRP_Planning_Workbook.xlsx  # 8-sheet Excel planning workbook
├── mrp_analytics.sqlite               # Reproducible SQLite database
├── sql/01_analytics.sql                # 8 practical SQL analyses
├── powerbi/
│   ├── POWER_BI_BUILD_GUIDE.md         # Exact model, measures and page-by-page visuals
│   ├── DAX_MEASURES.dax
│   └── MRP_Dashboard_Theme.json
├── src/pipeline.py
├── src/create_dashboard.py
├── src/create_workbook.py
└── tests/test_pipeline.py
```

## Quick start (Windows VS Code terminal)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.pipeline
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.create_dashboard
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The Streamlit command runs a full interactive materials control tower in your browser. For **zero-install viewing**, double-click `charts/interactive_mrp_dashboard.html` — charts contain bundled JS, so the file works offline. To explore SQL, open `mrp_analytics.sqlite` in your favorite SQLite browser and run `sql/01_analytics.sql` queries.

The Excel workbook is included and ready to open. Regenerating it via `src/create_workbook.py` requires the specialized `artifact_tool` Python environment and is optional; the core pipeline, HTML dashboard, SQLite results, and tests use the installable packages above.

## Power BI report

**Power BI assets are included, but not a native PBIX file.** A genuine `.pbix` must be assembled in Power BI Desktop on Windows. The folder `powerbi/` includes the prepared import data, star-schema relationships, DAX formulas, page-by-page layout, and color theme. The dashboard preview in `charts/` is a rendered design reference, not a screenshot of a native PBIX report.

Follow [POWER_BI_BUILD_GUIDE.md](powerbi/POWER_BI_BUILD_GUIDE.md), then save the result as `reports/Manufacturing_Materials_MRP_Optimization.pbix` locally in Power BI Desktop.

## What the project demonstrates on a resume

> Built a reproducible materials requirements planning (MRP) simulation using observed concrete mix ingredient profiles and synthetic production orders, inventory and supplier lead times; implemented time-phased BOM explosion, lot-sized purchasing, lead-time feasibility checks and material-shortage dashboards with Python, SQL, Excel and Power BI-ready datasets.

Do not represent hypothetical savings or synthetic improvements as actual operations outcomes.

## Attribution

Yeh, I. (1998). *Concrete Compressive Strength* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5PK67 . Dataset licensed CC BY 4.0; `concrete.csv` preserves the ingredient data under the user's supplied column labels. See `LICENSE_NOTE.md` for license information. The synthetic scenario and original project code are separate from the source measurements.
