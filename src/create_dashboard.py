"""Create portable offline interactive HTML + illustrative BI-style preview PNG."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'charts'
OUT.mkdir(exist_ok=True)
w=pd.read_csv(ROOT/'outputs/weekly_mrp.csv')
po=pd.read_csv(ROOT/'outputs/purchase_recommendations.csv')
wo=pd.read_csv(ROOT/'data/processed/production_orders.csv')
materials=pd.read_csv(ROOT/'data/processed/materials.csv')
weeks=sorted(w.week_start.unique())
demand=w.groupby('week_start').gross_requirement_kg.sum().reindex(weeks)/1000
receipts=w.groupby('material_name').planned_receipt_kg.sum().sort_values()/1000
baseline=w.groupby('week_start').baseline_backlog_kg.sum().reindex(weeks)/1000
feasible=w.groupby('week_start').feasible_backlog_kg.sum().reindex(weeks)/1000
heat=w.pivot(index='material_name',columns='week_start',values='feasible_shortage_flag')

# PNG: a visual target the user can recreate using standard Power BI visuals.
BG='#0b1526'; CARD='#14243a'; LIGHT='#eaf2fb'; MUTED='#91a7bf'; TEAL='#41d2ce'; AMBER='#ffc56b'; PINK='#fb7f93'; GRID='#334761'
fig=plt.figure(figsize=(16,9),facecolor=BG)
canvas=fig.add_axes([0,0,1,1]);canvas.axis('off')
canvas.text(.055,.956,'MATERIALS PLANNING  /  MRP CONTROL TOWER',color=LIGHT,fontsize=23,weight='bold',va='top')
canvas.text(.055,.912,'Concrete production simulation  •  12-week horizon starting Nov 2, 2026  •  USD & kg',color=MUTED,fontsize=11)
canvas.text(.945,.932,'SCENARIO • NOT ACTUAL ERP',ha='right',color=AMBER,fontsize=10,weight='bold')

def card(x,y,width,height):
    canvas.add_patch(FancyBboxPatch((x,y),width,height,boxstyle='round,pad=0.007,rounding_size=0.013',
                                   linewidth=0,facecolor=CARD,transform=canvas.transAxes))
    return x+0.017,y+height-0.035
kpis=[('WORK ORDERS',f'{len(wo):,}',TEAL),('PRODUCTION VOLUME',f'{wo.planned_volume_m3.sum():,.1f} m³',LIGHT),
      ('MATERIAL DEMAND',f'{w.gross_requirement_kg.sum()/1000:,.0f} t',LIGHT),
      ('PROPOSED PURCHASES',f'${po.extended_cost_usd.sum()/1000:,.1f}K',LIGHT),
      ('LATE-RELEASE ALERTS',str(int(po.late_release_flag.sum())),PINK)]
for i,(label,value,col) in enumerate(kpis):
    x=.052+i*.1818; tx,ty=card(x,.745,.169,.127)
    canvas.text(tx,ty,label,color=MUTED,fontsize=9,weight='medium',va='top')
    canvas.text(tx,ty-.057,value,color=col,fontsize=22,weight='bold',va='top')

def ax_card(rect,title):
    x,y,width,height=rect
    card(x,y,width,height)
    a=fig.add_axes([x+.026,y+.042,width-.049,height-.104],facecolor=CARD)
    a.set_title(title,loc='left',color=LIGHT,pad=18,fontsize=13,weight='bold')
    for spine in a.spines.values():spine.set_visible(False)
    a.tick_params(colors=MUTED,labelsize=8,length=0)
    a.grid(axis='y',color=GRID,alpha=.55,zorder=0)
    return a
ax1=ax_card((.052,.405,.43,.307),'Weekly material demand   /   tonnes')
xx=np.arange(len(demand));ax1.bar(xx,demand.values,color=TEAL,width=.63,zorder=3)
ax1.set_xticks(xx[::2],[pd.Timestamp(d).strftime('%b %d') for d in demand.index[::2]])
ax1.set_ylim(0,max(demand)*1.24)
ax2=ax_card((.50,.405,.445,.307),'Proposed receipts   /   tonnes by material')
ax2.grid(axis='x',color=GRID,alpha=.55);ax2.grid(axis='y',visible=False)
ax2.barh(np.arange(len(receipts)),receipts.values,color=AMBER,height=.58,zorder=4)
ax2.set_yticks(np.arange(len(receipts)),[x.replace('Ground blast furnace','G.B.F.') for x in receipts.index]);ax2.tick_params(axis='y',labelsize=8)
ax2.set_xlim(0,max(receipts)*1.25)
ax3=ax_card((.052,.077,.43,.294),'Cumulative unfilled material demand   /   tonnes')
ax3.plot(xx,baseline.values,color=PINK,lw=2.5,label='No new purchase orders')
ax3.plot(xx,feasible.values,color=TEAL,lw=2.5,label='Lead-time feasible MRP')
ax3.set_xticks(xx[::2],[pd.Timestamp(d).strftime('%b %d') for d in weeks[::2]])
ax3.legend(loc='upper left',frameon=False,labelcolor=LIGHT,fontsize=8)
ax4=ax_card((.50,.077,.445,.294),'Shortage risk matrix   /   red = backlog remains')
idx=heat.index.tolist();mat=heat.loc[idx,weeks].fillna(0).values
from matplotlib.colors import ListedColormap
ax4.imshow(mat,aspect='auto',cmap=ListedColormap(['#1a6f65','#ee758a']),vmin=0,vmax=1)
ax4.set_yticks(np.arange(len(idx)),[x.replace('Ground blast furnace','G.B.F.') for x in idx]);ax4.tick_params(axis='y',labelsize=8)
ax4.set_xticks(np.arange(0,12,2),[pd.Timestamp(weeks[i]).strftime('%b %d') for i in range(0,12,2)])
ax4.grid(visible=False)
canvas.text(.052,.037,'Observed: source mix quantities & strength  |  Simulated: work orders, stock, suppliers, prices & all procurement outcomes',color=MUTED,fontsize=10)
fig.savefig(OUT/'powerbi_dashboard_preview.png',dpi=145,facecolor=BG,bbox_inches='tight',pad_inches=.10)
plt.close(fig)

# Fully offline, hoverable and zoomable HTML dashboard. Plotly.js bundled inside.
config=dict(displayModeBar=True,responsive=True)
def polish(f):
    f.update_layout(template='plotly_white',height=350,margin=dict(t=60,l=25,r=25,b=30),
      font=dict(family='Arial',size=12),paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',
      title_font=dict(size=17,color='#19314a'), xaxis=dict(gridcolor='#e8edf2'),yaxis=dict(gridcolor='#e8edf2'))
    return f
f1=polish(px.bar(x=demand.index,y=demand.values,labels={'x':'Week','y':'Tonnes'},title='Weekly ingredient demand',color_discrete_sequence=['#168a92']))
f2=polish(px.bar(x=receipts.values,y=receipts.index,orientation='h',labels={'x':'Tonnes','y':'Material'},
                    title='Recommended material purchasing',color_discrete_sequence=['#f4aa44']))
f3=go.Figure();f3.add_scatter(x=weeks,y=baseline.values,mode='lines+markers',name='No new POs',line_color='#eb7486');f3.add_scatter(x=weeks,y=feasible.values,mode='lines+markers',name='Feasible MRP',line_color='#168a92')
f3.update_layout(title='Unfilled demand over time (tonnes)',xaxis_title='Week',yaxis_title='Tonnes');polish(f3)
f4=polish(px.imshow(heat,color_continuous_scale=['#cbf2dc','#ec7789'],zmin=0,zmax=1,aspect='auto',title='Material-week shortage alerts'))
import plotly.io as pio
blocks=[]
for n,f in enumerate((f1,f2,f3,f4)):
    blocks.append(pio.to_html(f,full_html=False,include_plotlyjs='inline' if n==0 else False,config=config))
metrics=[('Planned work orders',f'{len(wo):,}'),('Planned concrete',f'{wo.planned_volume_m3.sum():,.1f} m³'),('Material demand',f'{w.gross_requirement_kg.sum()/1000:,.1f} t'),
         ('Proposed purchases',f'${po.extended_cost_usd.sum():,.0f}'),('Late release lines',f'{po.late_release_flag.sum():,}')]
cards=''.join(f'<div class="kpi"><small>{lab}</small><b>{val}</b></div>' for lab,val in metrics)
pt=po[['material_name','primary_supplier','planned_release_date','requested_receipt_date','order_qty_kg','extended_cost_usd','release_status']].copy()
pt['order_qty_kg']=pt.order_qty_kg.map(lambda n:f'{n:,.0f}')
pt['extended_cost_usd']=pt.extended_cost_usd.map(lambda n:f'${n:,.0f}')
pt=pt.sort_values('requested_receipt_date')
rows=''.join('<tr>'+''.join(f'<td>{s}</td>' for s in t)+'</tr>' for t in pt.head(35).itertuples(index=False,name=None))
header=''.join(f'<th>{x.replace("_"," ").title()}</th>' for x in pt.columns)
html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MRP Control Tower • Interactive dashboard</title><style>
body{{margin:0;background:#f3f6fb;font:14px system-ui,Segoe UI,Arial;color:#16344b}} header{{background:#11253b;color:white;padding:33px 5.5%}}
h1{{margin:0;font-size:30px;letter-spacing:.015em}}header p{{color:#adbed1;margin:10px 0 0}}
main{{max-width:1380px;margin:20px auto;padding:0 24px}}.bar{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:17px}}.kpi{{flex:1;min-width:175px;background:white;padding:22px 17px;border-radius:12px;box-shadow:0 5px 17px #213d5a12;display:grid;gap:9px}}
.kpi small{{text-transform:uppercase;color:#607b92;font-weight:700;letter-spacing:.08em}}.kpi b{{font-size:27px;color:#133f59}}
.charts{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:17px}}.plot{{background:white;border-radius:12px;overflow:hidden;box-shadow:0 5px 17px #213d5a12}}
section{{background:white;margin-top:18px;padding:22px;border-radius:12px;box-shadow:0 5px 17px #213d5a12}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:11px 8px;border-bottom:1px solid #edf1f5;text-align:left}}th{{color:#4a6d85;text-transform:uppercase;font-size:10px}}.scroll{{overflow:auto}}.note{{color:#647b90;font-size:12px;line-height:1.6}}@media(max-width:850px){{.charts{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>MANUFACTURING / MATERIALS CONTROL TOWER</h1><p>12-week simulated concrete MRP · data date 21 Oct 2026 · Hover, zoom, and export the charts</p></header>
<main><div class="bar">{cards}</div><div class="charts">{''.join('<div class="plot">'+x+'</div>' for x in blocks)}</div>
<section><h2>Purchase recommendation queue</h2><div class="scroll"><table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></div></section>
<p class="note">Source observations: concrete ingredients and 28-day compressive strength. All production orders, beginning stocks, purchases, lead times and costs are simulated. Backlog is a point-in-time stock balance, not additive across time. This HTML report is a functional browser-based analogue; it is not a native Power BI PBIX file.</p></main></body></html>'''
(OUT/'interactive_mrp_dashboard.html').write_text(html,encoding='utf-8')
print('dashboard HTML',len(html),'bytes; preview', (OUT/'powerbi_dashboard_preview.png').stat().st_size)
