import numpy as np
import pandas as pd
from src.pipeline import (SOURCE, INGREDIENTS, AS_OF, WEEKS, build_material_tables,
    mrp_plan, pick_recipes, simulate_orders, validate_source)


def prepared():
    source = pd.read_csv(SOURCE)
    validate_source(source)
    prod,bom=pick_recipes(source)
    orders=simulate_orders(prod)
    gross,mats,stock,receipts,explosion=build_material_tables(bom,orders)
    weekly,planned=mrp_plan(gross,mats,stock,receipts)
    return prod,bom,orders,gross,mats,stock,receipts,explosion,weekly,planned


def test_source_and_recipe_units():
    prod,bom,*_=prepared()
    assert len(prod)==4 and len(bom)==28
    assert set(bom.material_id)==set(INGREDIENTS)
    assert (bom.kg_per_m3 >=0).all()
    assert (prod.observed_28d_strength_mpa >= prod.target_strength_mpa).all()


def test_bom_explosion_and_gross_consistency():
    prod,bom,orders,gross,mats,stock,receipts,exp,*_=prepared()
    expected=orders.merge(bom[bom.kg_per_m3.gt(0)],on='product_id')
    assert np.allclose(expected.planned_volume_m3*expected.kg_per_m3,exp.required_kg,atol=0.00051)
    assert np.isclose(gross.gross_requirement_kg.sum(),exp.required_kg.sum(),atol=0.01)
    assert len(orders)==144


def test_mrp_rolling_balance_and_lot_rules():
    *_,weekly,planned=prepared()
    for material,part in weekly.groupby('material_id'):
        part=part.sort_values('week_index')
        assert len(part)==WEEKS
        for _,row in part.iterrows():
            assert np.isclose(row.opening_unconstrained_kg+row.scheduled_receipt_kg+row.planned_receipt_kg-row.gross_requirement_kg,
                row.projected_end_unconstrained_kg,atol=0.07)
            assert row.projected_end_unconstrained_kg >= row.safety_stock_kg-0.07
        assert np.allclose(part.iloc[1:].opening_unconstrained_kg.values,part.iloc[:-1].projected_end_unconstrained_kg.values,atol=0.07)
    assert (planned.order_qty_kg>0).all()
    for _,row in planned.iterrows():
        assert row.order_qty_kg >= 0
        assert bool(row.late_release_flag) == (pd.Timestamp(row.planned_release_date)<AS_OF)


def test_scenario_fields_and_reconciliations():
    *_,weekly,planned=prepared()
    assert len(weekly)==7*WEEKS
    assert (weekly.baseline_shortage_flag==(weekly.projected_end_baseline_kg<0).astype(int)).all()
    assert (weekly.feasible_shortage_flag==(weekly.projected_end_lead_feasible_kg<0).astype(int)).all()
    assert np.isclose(planned.extended_cost_usd.sum(),weekly.planned_purchase_value_usd.sum(),atol=0.5)
    assert (planned.delivery_delay_weeks.ge(0)).all()
    assert planned.loc[planned.late_release_flag.eq(1),'delivery_delay_weeks'].ge(1).all()


def test_deterministic_rebuild():
    p,*_=prepared()
    a=simulate_orders(p);b=simulate_orders(p)
    assert a.equals(b)
