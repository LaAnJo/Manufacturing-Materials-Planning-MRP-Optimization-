-- SQLite queries for the generated mrp_analytics.sqlite database.
-- NOTE: Backlog at different weeks is a stock/point-in-time measure: NEVER SUM backlog over time.

-- 1. Production plan volume by illustrative recipe.
SELECT o.product_id, p.product_name, COUNT(*) AS work_orders,
       ROUND(SUM(o.planned_volume_m3),1) AS planned_m3
FROM production_orders o
JOIN products p ON p.product_id=o.product_id
GROUP BY o.product_id,p.product_name ORDER BY o.product_id;

-- 2. Total material requirements and modeled purchasing cost.
SELECT m.material_name,
       ROUND(SUM(w.gross_requirement_kg)/1000,1) AS gross_demand_tonnes,
       ROUND(SUM(w.planned_receipt_kg)/1000,1) AS planned_purchase_tonnes,
       ROUND(SUM(w.planned_purchase_value_usd),2) AS modeled_purchase_usd
FROM weekly_mrp w JOIN materials m ON m.material_id=w.material_id
GROUP BY m.material_name ORDER BY modeled_purchase_usd DESC;

-- 3. Material-week shortage flags (not a count of failed production orders).
SELECT week_start, SUM(baseline_shortage_flag) AS baseline_material_shortage_count,
       SUM(feasible_shortage_flag) AS feasible_material_shortage_count,
       SUM(late_release_flag) AS late_release_recommendations
FROM weekly_mrp
GROUP BY week_start ORDER BY week_start;

-- 4. Items to expedite or validate because intended releases are before as-of date.
SELECT material_name, primary_supplier, planned_release_date,
       requested_receipt_date, order_qty_kg, extended_cost_usd
FROM purchase_recommendations
WHERE late_release_flag=1 ORDER BY requested_receipt_date,material_name;

-- 5. Rolling inventory coverage and net requirements.
SELECT material_name, week_start, gross_requirement_kg,
       scheduled_receipt_kg, net_requirement_kg, planned_receipt_kg,
       projected_end_unconstrained_kg, projected_end_lead_feasible_kg,
       feasible_backlog_kg
FROM weekly_mrp WHERE material_id='cement' ORDER BY week_index;

-- 6. BOM explosion for one production order.
SELECT order_id, product_id, material_id, planned_volume_m3,
       kg_per_m3, required_kg
FROM bom_explosion WHERE order_id='WO-0001' ORDER BY material_id;

-- 7. End-of-horizon comparison (no cross-week sum of backlogs).
SELECT material_name, ROUND(projected_end_baseline_kg,1) AS baseline_stock_kg,
       ROUND(projected_end_lead_feasible_kg,1) AS lead_feasible_stock_kg,
       ROUND(feasible_backlog_kg,1) AS feasibility_backlog_kg
FROM weekly_mrp WHERE week_index=11 ORDER BY feasibility_backlog_kg DESC;

-- 8. Simulated purchase orders by supplier.
SELECT primary_supplier, COUNT(*) AS po_lines,
       ROUND(SUM(extended_cost_usd),2) AS planned_value_usd,
       SUM(late_release_flag) AS expedited_lines
FROM purchase_recommendations GROUP BY primary_supplier
ORDER BY planned_value_usd DESC;
