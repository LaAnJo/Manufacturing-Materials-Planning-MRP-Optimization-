# Data dictionary

| File | Grain | Primary fields |
|---|---|---|
| `data/raw/concrete.csv` | One original experimental sample / age | `cement`, `slag`, `ash`, `water`, `superplastic`, `coarseagg`, `fineagg` kg/m³; `age` days; `strength` MPa |
| `data/processed/weeks.csv` | One planning week (12 rows) | `week_index`, `week_start`, `week_label` |
| `data/processed/products.csv` | One nominal product recipe | `product_id`, `target_strength_mpa`, `observed_28d_strength_mpa`, `material_cost_usd_m3` |
| `data/processed/bom.csv` | Product × material | `product_id`, `material_id`, `kg_per_m3` |
| `data/processed/materials.csv` | Material | `lead_time_weeks`, `moq_kg`, `order_multiple_kg`, `unit_cost_usd_per_kg`, `safety_stock_kg` |
| `data/processed/inventory_initial.csv` | Material snapshot | `opening_on_hand_kg` |
| `data/processed/scheduled_receipts.csv` | Simulated existing open receipt | `material_id`, `week_start`, `scheduled_receipt_kg` |
| `data/processed/production_orders.csv` | Production work order | `order_id`, `product_id`, `week_start`, `planned_volume_m3` |
| `outputs/bom_explosion.csv` | Production order × consumed material | `required_kg`, `kg_per_m3`, `planned_volume_m3` |
| `outputs/material_demand_weekly.csv` | Material × week | `gross_requirement_kg` |
| `outputs/weekly_mrp.csv` | Material × week (84 rows) | gross, scheduled receipts, safety stock, net requirement, proposed receipt, feasibility and backlog |
| `outputs/purchase_recommendations.csv` | Planned MRP purchasing line (67 rows) | receipt dates, release date, `delivery_delay_weeks`, `extended_cost_usd`, `late_release_flag` |
| `outputs/kpi_summary.csv` | Whole simulation | Fixed aggregate outcomes, global (not cross-filtered) |

## KPI pitfalls

- `production_orders` contains 144 orders, **not** 144 real factory orders.
- `material_demand_weekly` uses kg; divide by 1000 for metric tonnes.
- `feasible_backlog_kg` is a cumulative negative inventory balance by material at the END of the listed week; it is NOT a fresh weekly shortage quantity. Do not SUM these across weeks.
- `late_release_flag` is based on comparing ideal PO release with 2026-10-21.
- `planned_receipt_feasible_kg` may appear in a different week from `planned_receipt_kg` because some deliveries are delayed.
- `extended_cost_usd` uses hypothetical prices and is not actual procurement spend.
- A count of shortage *material-weeks* is not a count of missed production orders.
