"""Interactive simulated MRP control-tower dashboard. Launch: streamlit run app.py."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='MRP | Materials Control Tower',page_icon='🏭',layout='wide')

@st.cache_data
def load():
    csv=lambda file:pd.read_csv(ROOT/file)
    return (csv('outputs/weekly_mrp.csv'),csv('outputs/purchase_recommendations.csv'),
            csv('data/processed/production_orders.csv'),csv('data/processed/materials.csv'),
            csv('data/processed/products.csv'),csv('data/processed/bom.csv'))

w,po,wo,materials,products,bom=load()
st.title('🏭 Materials Planning & MRP Control Tower')
st.caption('ILLUSTRATIVE SCENARIO · Source-observed concrete mix proportions · Simulated production, inventory, supplier lead times and costs')
allm=materials.material_name.tolist()
select=st.sidebar.multiselect('Filter raw materials', allm,default=allm)
st.sidebar.caption('Work-order volume is a global metric, independent of the raw-material filter.')
st.sidebar.warning('Experimental recipes, not certified structural concrete designs. Costs, stock and purchasing are simulation assumptions.')
filtered=w[w.material_name.isin(select)].copy()
pof=po[po.material_name.isin(select)].copy()
first,last=st.columns(2)
with first:
    st.write('**Planning date:** 2026-10-21')
with last:
    st.write('**Planning horizon:** 2026-11-02 → 2027-01-18 (12 weeks)')
metrics=[('Planned volume',f'{wo.planned_volume_m3.sum():,.1f} m³'),('Materials demand',f'{filtered.gross_requirement_kg.sum()/1000:,.1f} t'),
         ('Proposed purchasing',f'${pof.extended_cost_usd.sum():,.0f}'),('Late releases',f'{pof.late_release_flag.sum():,.0f}')]
for col,(label,value) in zip(st.columns(4),metrics):col.metric(label,value)

def format_fig(fig,height=320):
    fig.update_layout(template='plotly_white',height=height,margin=dict(t=45,b=25,l=15,r=20),
        font=dict(family='Arial',size=12),legend=dict(orientation='h',y=1.15))
    return fig

c1,c2=st.columns([1.2,1])
with c1:
    byweek=filtered.groupby('week_start',as_index=False)['gross_requirement_kg'].sum()
    byweek['tonnes']=byweek.gross_requirement_kg/1000
    fig=px.bar(byweek,x='week_start',y='tonnes',title='Weekly material demand (tonnes)',
        labels={'week_start':'Week starting','tonnes':'Tonnes'},color_discrete_sequence=['#127f91'])
    st.plotly_chart(format_fig(fig),use_container_width=True)
with c2:
    summary=filtered.groupby('material_name',as_index=False).agg(planned_receipt_kg=('planned_receipt_kg','sum'))
    summary['tonnes']=summary.planned_receipt_kg/1000
    fig=px.bar(summary.sort_values('tonnes'),y='material_name',x='tonnes',orientation='h',
        title='Proposed purchases by material (tonnes)',labels={'material_name':'','tonnes':'Tonnes'},
        color_discrete_sequence=['#ed9a30'])
    st.plotly_chart(format_fig(fig),use_container_width=True)

c3,c4=st.columns([1.2,1])
with c3:
    trend=filtered.groupby('week_start',as_index=False).agg(baseline=('baseline_backlog_kg','sum'),feasible=('feasible_backlog_kg','sum'))
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=trend.week_start,y=trend.baseline/1000,name='No new POs',line=dict(color='#e35b68',width=3)))
    fig.add_trace(go.Scatter(x=trend.week_start,y=trend.feasible/1000,name='Lead-time feasible',line=dict(color='#127f91',width=3)))
    fig.update_layout(title='Outstanding material backlog at each week (tonnes)',xaxis_title='Week starting',yaxis_title='Tonnes')
    st.plotly_chart(format_fig(fig),use_container_width=True)
with c4:
    pivot=filtered.pivot(index='material_name',columns='week_start',values='feasible_shortage_flag').fillna(0)
    fig=px.imshow(pivot.astype(int),color_continuous_scale=['#d9f1e9','#e66d76'],
        zmin=0,zmax=1,title='Lead-feasible shortage alerts · material × week',labels={'color':'Shortage'})
    st.plotly_chart(format_fig(fig),use_container_width=True)

st.subheader('Purchase recommendations')
st.caption('Orders flagged “Expedite / validate” require supplier confirmation; the model does not assume expedited deliveries.')
cols=['material_name','primary_supplier','planned_release_date','requested_receipt_date','order_qty_kg','extended_cost_usd','release_status']
st.dataframe(pof[cols].sort_values(['requested_receipt_date','material_name']),use_container_width=True,hide_index=True)
with st.expander('Recipe BOM (kg per cubic meter), derived from observed 28-day concrete data'):
    st.dataframe(bom.pivot(index='product_id',columns='material_id',values='kg_per_m3'),use_container_width=True)
    st.dataframe(products,use_container_width=True,hide_index=True)
st.caption('Backlog figures are point-in-time material balances. Do not add backlog across weeks or interpret shortage material-weeks as missed work orders.')
