"""Deterministic concrete production materials planning simulation.

Source: UCI Concrete Compressive Strength (Yeh, 1998): uploaded concrete.csv.
Only BOM recipe observations are source-derived; production orders, stock,
suppliers, unit costs, and receipts are scenario assumptions, not observations.
"""
from __future__ import annotations
import math
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data' / 'raw' / 'concrete.csv'
PROCESSED = ROOT / 'data' / 'processed'
OUTPUTS = ROOT / 'outputs'
START = pd.Timestamp('2026-11-02')
AS_OF = pd.Timestamp('2026-10-21')
WEEKS = 12
SEED = 426
INGREDIENTS = ['cement', 'slag', 'ash', 'water', 'superplastic', 'coarseagg', 'fineagg']
MATERIALS = [
    ('cement', 'Portland cement', 'KilnWorks Materials', 2, 12000, 4000, 0.160, 1.15),
    ('slag', 'Ground blast furnace slag', 'GreenBind Minerals', 3, 8000, 2000, 0.092, 0.72),
    ('ash', 'Fly ash', 'EcoAsh Supply', 2, 5000, 1000, 0.083, 0.94),
    ('water', 'Mixing water', 'Plant Utility', 0, 5000, 1000, 0.004, 1.35),
    ('superplastic', 'Superplasticizer', 'PolyMix Chemicals', 3, 500, 100, 2.350, 0.63),
    ('coarseagg', 'Coarse aggregate', 'Rockline Aggregates', 1, 30000, 10000, 0.027, 0.90),
    ('fineagg', 'Fine aggregate', 'Sandway Supply', 1, 30000, 10000, 0.029, 0.78),
]
TARGETS = [("MX25", 25), ("MX35", 35), ("MX45", 45), ("MX55", 55)]


def validate_source(df: pd.DataFrame) -> None:
    needed = set(INGREDIENTS + ['age', 'strength'])
    if set(df.columns) != needed:
        raise ValueError(f'Expected {needed}; got {set(df.columns)}')
    if df.empty or df.isna().any().any():
        raise ValueError('Source is empty or contains nulls')
    if (df[INGREDIENTS] < 0).any().any() or (df[['age', 'strength']] <= 0).any().any():
        raise ValueError('Physical values outside expected range')
    if len(df.loc[df.age == 28]) < 4:
        raise ValueError('Insufficient 28-day mix observations')


def pick_recipes(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pick one observed 28-day recipe per illustrative target, not certified mix design."""
    subset = raw.loc[raw.age.eq(28)].copy()
    subset = subset.groupby(INGREDIENTS, as_index=False).agg(
        tested_strength_mpa=('strength', 'mean'), test_rows=('strength', 'size')
    )
    prices = {item[0]: item[6] for item in MATERIALS}
    subset['indicative_material_cost_usd_m3'] = sum(subset[m] * prices[m] for m in INGREDIENTS)
    used = set()
    products = []
    bom = []
    for product_id, target in TARGETS:
        candidates = subset.loc[
            subset.tested_strength_mpa.between(target + 1.0, target + 7.0)
        ].copy()
        if candidates.empty:
            candidates = subset.loc[subset.tested_strength_mpa.ge(target + 1.0)].copy()
        # Prioritize reasonable cost, then margin near the target; deterministic tie-breaker.
        candidates['rank_score'] = candidates['indicative_material_cost_usd_m3'] + 2 * abs(candidates.tested_strength_mpa - (target+3))
        candidates = candidates.sort_values(['rank_score','tested_strength_mpa'], kind='stable')
        row = next((r for _, r in candidates.iterrows() if tuple(round(float(r[c]), 4) for c in INGREDIENTS) not in used), None)
        if row is None:
            raise ValueError(f'Could not find recipe for {product_id}')
        used.add(tuple(round(float(row[c]), 4) for c in INGREDIENTS))
        products.append(dict(product_id=product_id,product_name=f'Illustrative {target} MPa mix',target_strength_mpa=target,
            observed_28d_strength_mpa=round(float(row.tested_strength_mpa),2),source_test_rows=int(row.test_rows),
            material_cost_usd_m3=round(float(row.indicative_material_cost_usd_m3),2),
            recipe_status='Research example; not certified for structural use'))
        for m in INGREDIENTS:
            bom.append(dict(product_id=product_id,material_id=m,kg_per_m3=float(row[m]),bom_uom='kg per m3',
                source='Observed concrete.csv 28-day recipe'))
    return pd.DataFrame(products),pd.DataFrame(bom)


def simulate_orders(products: pd.DataFrame) -> pd.DataFrame:
    rng=np.random.default_rng(SEED)
    orders=[]
    k=0
    for w in range(WEEKS):
        week_date = START + pd.Timedelta(days=7*w)
        factor=1.0+0.12*math.sin(w*math.pi/6)
        for _, prod in products.iterrows():
            for nth in range(3):
                k+=1
                qty=round(float(rng.uniform(13,29) * factor),1)
                orders.append(dict(order_id=f'WO-{k:04d}', product_id=prod.product_id,
                    week_index=w, week_start=week_date.strftime('%Y-%m-%d'),
                    production_date=(week_date+pd.Timedelta(days=int(rng.integers(0,5)))).strftime('%Y-%m-%d'),
                    planned_volume_m3=qty, order_status='Simulated / planned'))
    return pd.DataFrame(orders)


def build_material_tables(bom:pd.DataFrame,orders:pd.DataFrame):
    explosion=orders.merge(bom[bom.kg_per_m3.gt(0)],on='product_id',validate='many_to_many')
    explosion['required_kg']=(explosion.planned_volume_m3*explosion.kg_per_m3).round(3)
    gross=explosion.groupby(['material_id','week_index','week_start'],as_index=False)['required_kg'].sum().rename(columns={'required_kg':'gross_requirement_kg'})
    avg=gross.groupby('material_id')['gross_requirement_kg'].sum()/WEEKS
    mats=[]
    stock=[]
    receipts=[]
    receipt_pattern={'cement':[(1,0.62)],'slag':[(2,0.54)],'ash':[(1,0.60)],
      'water':[(1,0.20)],'superplastic':[(2,0.62)],'coarseagg':[(1,0.58)],'fineagg':[(2,0.65)]}
    for m,name,supplier,lead,moq,multiple,price,opening_weeks in MATERIALS:
        demand=float(avg.get(m,0))
        # Zero-consumption BOM components are retained, not incorrectly treated as purchasing requirements.
        safety=round(demand*0.35,2)
        opening=round(demand*opening_weeks,2)
        mats.append(dict(material_id=m,material_name=name,primary_supplier=supplier,lead_time_weeks=lead,
            moq_kg=moq,order_multiple_kg=multiple,unit_cost_usd_per_kg=price,
            safety_stock_kg=safety, lead_time_source='Simulated',price_source='Simulated'))
        stock.append(dict(material_id=m,as_of_date=str(AS_OF.date()),opening_on_hand_kg=opening,
            inventory_source='Simulated'))
        for w,ratio in receipt_pattern[m]:
            qty=round(demand*ratio,2)
            receipts.append(dict(receipt_id=f'SR-{m.upper()}-{w}',material_id=m,
                week_index=w,week_start=(START+pd.Timedelta(days=7*w)).strftime('%Y-%m-%d'),
                scheduled_receipt_kg=qty,receipt_source='Simulated existing open PO'))
    return gross, pd.DataFrame(mats),pd.DataFrame(stock),pd.DataFrame(receipts),explosion


def mrp_plan(gross: pd.DataFrame,mats:pd.DataFrame,stock:pd.DataFrame,receipts:pd.DataFrame):
    weekly=[]
    proposed=[]
    start=str(START.date())
    for _,material in mats.iterrows():
        m=material.material_id
        demand_map={int(x.week_index):float(x.gross_requirement_kg) for x in gross.itertuples() if x.material_id==m}
        receipt_map={int(x.week_index):float(x.scheduled_receipt_kg) for x in receipts.itertuples() if x.material_id==m}
        initial=float(stock.loc[stock.material_id.eq(m),'opening_on_hand_kg'].iloc[0])
        safety=float(material.safety_stock_kg)
        lead=int(material.lead_time_weeks)
        moq=float(material.moq_kg)
        multiple=float(material.order_multiple_kg)
        projected=baseline=initial
        material_week_offset=len(weekly)
        material_order_offset=len(proposed)
        for w in range(WEEKS):
            date=START+pd.Timedelta(weeks=w)
            gross_kg=demand_map.get(w,0.0)
            scheduled=receipt_map.get(w,0.0)
            pre_replenishment=projected+scheduled-gross_kg
            deficiency=max(0.0,safety-pre_replenishment)
            planned=0.0
            if deficiency>0.005:
                planned=math.ceil(max(moq,deficiency)/multiple-1e-10)*multiple
            release_date=date-pd.Timedelta(weeks=lead)
            late=int(planned>0 and release_date<AS_OF)
            feasible_receipt=0.0  # populated after delayed deliveries are assigned
            closing=pre_replenishment+planned
            baseline=baseline+scheduled-gross_kg
            def r(x): return round(float(x),2)
            item=dict(material_id=m,material_name=material.material_name,week_index=w,
               week_start=date.strftime('%Y-%m-%d'),opening_unconstrained_kg=r(projected),
               gross_requirement_kg=r(gross_kg),scheduled_receipt_kg=r(scheduled),
               safety_stock_kg=r(safety),net_requirement_kg=r(deficiency),
               planned_receipt_kg=r(planned),planned_release_date=release_date.strftime('%Y-%m-%d') if planned else '',
               lead_time_weeks=lead,late_release_flag=late,
               planned_receipt_feasible_kg=r(feasible_receipt),
               projected_end_unconstrained_kg=r(closing),
               projected_end_baseline_kg=r(baseline),baseline_backlog_kg=r(max(0,-baseline)),
               baseline_shortage_flag=int(baseline<0),
               projected_end_lead_feasible_kg=0.0,
               feasible_backlog_kg=0.0,
               feasible_shortage_flag=0,
               unit_cost_usd_per_kg=float(material.unit_cost_usd_per_kg),
               planned_purchase_value_usd=r(planned*material.unit_cost_usd_per_kg),
               scenario='Simulated / illustrative')
            weekly.append(item)
            if planned>0:
                proposed.append(dict(po_recommendation_id=f'MRP-{m.upper()}-{w:02d}',material_id=m,
                    material_name=material.material_name,primary_supplier=material.primary_supplier,
                    planned_release_date=release_date.strftime('%Y-%m-%d'),requested_receipt_date=date.strftime('%Y-%m-%d'),
                    week_index=w,lead_time_weeks=lead,order_qty_kg=r(planned),
                    unit_cost_usd_per_kg=float(material.unit_cost_usd_per_kg),
                    extended_cost_usd=r(planned*material.unit_cost_usd_per_kg),
                    late_release_flag=late,
                    release_status='Expedite requested date / negotiate' if late else 'Release on schedule',
                    source='MRP recommendation on simulated plan'))
            projected=closing
        # A past-due ideal release does not magically arrive on its requested date.
        # Instead move that proposed order to the first weekly receipt bucket compatible
        # with the supplier's STANDARD lead time counted from the scenario as-of date.
        # This prevents persistent 'phantom' backlogs from simply dropping the order.
        deliveries={}
        earliest_day=AS_OF+pd.Timedelta(weeks=lead)
        earliest_bucket=max(0,math.ceil((earliest_day-START).days/7))
        for item in proposed[material_order_offset:]:
            feasible_week=max(int(item['week_index']),earliest_bucket)
            item['delivery_delay_weeks']=feasible_week-int(item['week_index'])
            item['feasible_receipt_date']=(START+pd.Timedelta(weeks=feasible_week)).strftime('%Y-%m-%d')
            deliveries[feasible_week]=deliveries.get(feasible_week,0)+item['order_qty_kg']
        feasible=initial
        for item in weekly[material_week_offset:]:
            week_idx=int(item['week_index'])
            delivered=deliveries.get(week_idx,0.0)
            feasible=feasible+item['scheduled_receipt_kg']+delivered-item['gross_requirement_kg']
            item['planned_receipt_feasible_kg']=round(delivered,2)
            item['projected_end_lead_feasible_kg']=round(feasible,2)
            item['feasible_backlog_kg']=round(max(0,-feasible),2)
            item['feasible_shortage_flag']=int(feasible<-0.005)
    return pd.DataFrame(weekly),pd.DataFrame(proposed)


def save_csv(df:pd.DataFrame, folder:Path, name:str)->None:
    df.to_csv(folder / name,index=False,float_format='%.4f')


def run():
    PROCESSED.mkdir(parents=True,exist_ok=True)
    OUTPUTS.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(SOURCE)
    validate_source(raw)
    products,bom=pick_recipes(raw)
    orders=simulate_orders(products)
    gross,mats,stock,receipts,explosion=build_material_tables(bom,orders)
    weekly,recommendations=mrp_plan(gross,mats,stock,receipts)
    weeks_df=pd.DataFrame([dict(week_index=w,week_start=(START+pd.Timedelta(weeks=w)).strftime('%Y-%m-%d'),
                week_label=(START+pd.Timedelta(weeks=w)).strftime('%b %d'),
                year=int((START+pd.Timedelta(weeks=w)).year)) for w in range(WEEKS)])
    save_tables={
      'weeks.csv':weeks_df, 'materials.csv':mats,'products.csv':products,'bom.csv':bom,'production_orders.csv':orders,
      'inventory_initial.csv':stock,'scheduled_receipts.csv':receipts,
    }
    for n,df in save_tables.items(): save_csv(df,PROCESSED,n)
    generated={
      'weekly_mrp.csv':weekly, 'purchase_recommendations.csv':recommendations,
      'material_demand_weekly.csv':gross, 'bom_explosion.csv':explosion,
    }
    for n,df in generated.items():save_csv(df,OUTPUTS,n)
    # One material-week row = a UNIQUE KPI opportunity. Backlog columns are stock states,
    # not independently additive material demand. Do not sum backlogs across time.
    kpi={
      'source_rows':len(raw),'source_28_day_rows':int(raw.age.eq(28).sum()),
      'product_recipes':len(products),'production_orders':len(orders),
      'planning_weeks':WEEKS,'planned_concrete_volume_m3':round(float(orders.planned_volume_m3.sum()),1),
      'material_requirement_tonnes':round(float(gross.gross_requirement_kg.sum()/1000),1),
      'planned_purchase_orders':len(recommendations),
      'planned_purchase_value_usd':round(float(recommendations.extended_cost_usd.sum()),2),
      'late_release_recommendations':int(recommendations.late_release_flag.sum()),
      'baseline_shortage_material_weeks':int(weekly.baseline_shortage_flag.sum()),
      'lead_feasible_shortage_material_weeks':int(weekly.feasible_shortage_flag.sum()),
      'final_baseline_backlog_tonnes':round(float(weekly.loc[weekly.week_index.eq(WEEKS-1),'baseline_backlog_kg'].sum()/1000),1),
      'final_feasible_backlog_tonnes':round(float(weekly.loc[weekly.week_index.eq(WEEKS-1),'feasible_backlog_kg'].sum()/1000),1),
      'as_of':AS_OF.strftime('%Y-%m-%d'),'planning_start':START.strftime('%Y-%m-%d'),
    }
    save_csv(pd.DataFrame([kpi]),OUTPUTS,'kpi_summary.csv')
    dbpath=ROOT/'mrp_analytics.sqlite'
    with sqlite3.connect(dbpath) as con:
        for tab,frame in {**{n[:-4]:f for n,f in save_tables.items()},**{n[:-4]:f for n,f in generated.items()},'kpi_summary':pd.DataFrame([kpi])}.items():
            frame.to_sql(tab,con,if_exists='replace',index=False)
        for q in ['CREATE INDEX IF NOT EXISTS idx_mrp_material_week ON weekly_mrp(material_id,week_index)',
                  'CREATE INDEX IF NOT EXISTS idx_po_material_week ON purchase_recommendations(material_id,week_index)']:
            con.execute(q)
    print('MRP DEMONSTRATION — only BOM ingredient profiles from observed input; other fields simulated')
    for k,v in kpi.items(): print(f'  {k}: {v}')
    return dict(kpi=kpi,products=products,bom=bom,orders=orders,mats=mats,stock=stock,receipts=receipts,gross=gross,weekly=weekly,recommendations=recommendations)

if __name__=='__main__':
    run()
