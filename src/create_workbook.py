"""Build the Excel planning workbook with artifact_tool (not openpyxl)."""
from pathlib import Path
import csv
from artifact_tool import Workbook,SpreadsheetFile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'/'MRP_Planning_Workbook.xlsx'
WB=Workbook.create()
NAVY='#10253B'; TEAL='#096B72'; BLUE='#DDECF2'; WHITE='#FFFFFF'; MUTED='#5B7284'; GOLD='#FFEDCB'; LRED='#FDE1E6'; GREEN='#DCF3E9'

def letters(n):
    s=''
    while n:
        n,r=divmod(n-1,26);s=chr(65+r)+s
    return s

def load(file):
    with open(ROOT/file,newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        rows=list(reader)
        hdr=list(reader.fieldnames)
    clean=[]
    for row in rows:
        values=[]
        for h in hdr:
            v=row[h]
            if v=='':values.append(None)
            else:
                if h in ['week_index','lead_time_weeks','late_release_flag','baseline_shortage_flag','feasible_shortage_flag','delivery_delay_weeks','target_strength_mpa','source_test_rows','moq_kg','order_multiple_kg']:
                    values.append(int(float(v)))
                elif h.endswith(('_kg','_m3','_mpa','_usd','_tonnes','_per_kg')) or h in ('kg_per_m3','planned_volume_m3','strength','age','material_cost_usd_m3','unit_cost_usd_per_kg','order_qty_kg'):
                    try:values.append(float(v))
                    except ValueError:values.append(v)
                else:values.append(v)
        clean.append(values)
    return hdr,clean

def data_sheet(title,file,tablename,formats=None):
    hdr,rows=load(file)
    sheet=WB.worksheets.add(title)
    end_col=letters(len(hdr))
    sheet.merge_cells(f'A1:{end_col}2')
    sheet.get_range('A1').values=[[title.replace('_',' ').upper()+'  |  SCENARIO DATA']]
    sheet.get_range(f'A1:{end_col}2').format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':16},'row_height':22}
    sheet.merge_cells(f'A3:{end_col}3')
    sheet.get_range('A3').values=[['Original concrete dataset supplies mixture ingredients; inventory, lead times, order quantities and prices are simulated.']]
    sheet.get_range(f'A3:{end_col}3').format={'font':{'color':MUTED,'size':10},'row_height':25}
    header_row=5; start=6; end=start+len(rows)-1
    sheet.get_range(f'A5:{end_col}5').values=[hdr]
    sheet.get_range(f'A5:{end_col}5').format={'fill':TEAL,'font':{'bold':True,'color':WHITE,'size':10},'row_height':31,'wrap_text':True}
    if rows:
        sheet.get_range(f'A{start}:{end_col}{end}').values=rows
        sheet.get_range(f'A{start}:{end_col}{end}').format={'row_height':19,'font':{'size':10}}
    sheet.freeze_panes.freeze_rows(5)
    for idx,h in enumerate(hdr,1):
        col=letters(idx)
        if any(s in h for s in ('material_name','product_name','supplier','release_status','scenario','recipe_status')):
            width=31
        elif h in ('source','order_status','inventory_source'):
            width=37
        elif h in ('planned_release_date','requested_receipt_date','feasible_receipt_date'):
            width=22
        elif h in ('material_id','product_id','order_id','po_recommendation_id','week_start','production_date'):
            width=19
        else:width=18
        sheet.get_range(f'{col}:{col}').format.column_width=width
        if h.endswith(('_usd','_usd_per_kg')) or h in ('material_cost_usd_m3','unit_cost_usd_per_kg'):
            sheet.get_range(f'{col}{start}:{col}{end}').set_number_format('$#,##0.00')
        elif h.endswith(('_kg','_m3','_mpa')) or h in ('kg_per_m3','planned_volume_m3'):
            sheet.get_range(f'{col}{start}:{col}{end}').set_number_format('#,##0.00')
    if rows:
        try:sheet.tables.add(f'A5:{end_col}{end}',True,tablename)
        except Exception as e:print('Table style skipped',title,str(e)[:120])
    return sheet,hdr,len(rows)

m,hm,nm=data_sheet('MRP_Weekly','outputs/weekly_mrp.csv','MRPWeeklyTable')
p,hp,np=data_sheet('Purchase_Plan','outputs/purchase_recommendations.csv','PurchasePlanTable')
w,hw,nw=data_sheet('Production_Orders','data/processed/production_orders.csv','ProductionOrdersTable')
ma,hma,nma=data_sheet('Materials','data/processed/materials.csv','MaterialMasterTable')
b,hb,nb=data_sheet('BOM','data/processed/bom.csv','BOMTable')
pr,hpr,npr=data_sheet('Products','data/processed/products.csv','ProductTable')

# Validation computations are actual Excel formulas, not stored Python values.
mcheck=letters(len(hm)+1)
m.get_range(f'{mcheck}5').values=[['MRP_BALANCE_CHECK_KG']]
m.get_range(f'{mcheck}5').format={'fill':TEAL,'font':{'bold':True,'color':WHITE},'wrap_text':True}
m.get_range(f'{mcheck}6:{mcheck}{nm+5}').formulas=[[f'=ROUND(E{r}+G{r}+J{r}-F{r}-O{r},2)'] for r in range(6,nm+6)]
m.get_range(f'{mcheck}:{mcheck}').format.column_width=24
pcheck=letters(len(hp)+1)
p.get_range(f'{pcheck}5').values=[['COST_CHECK_USD']]
p.get_range(f'{pcheck}5').format={'fill':TEAL,'font':{'bold':True,'color':WHITE}}
p.get_range(f'{pcheck}6:{pcheck}{np+5}').formulas=[[f'=ROUND(I{r}*J{r}-K{r},2)'] for r in range(6,np+6)]
p.get_range(f'{pcheck}:{pcheck}').format.column_width=23

sd=WB.worksheets.add('Dashboard')
sd.merge_cells('A1:M2');sd.get_range('A1').values=[['MANUFACTURING MATERIALS  |  MRP EXECUTIVE DASHBOARD']]
sd.get_range('A1:M2').format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':17},'row_height':24}
sd.merge_cells('A3:M3');sd.get_range('A3').values=[['12-week simulated concrete MRP • Data planning date: Oct 21, 2026 • Source BOM from concrete.csv']]
sd.get_range('A3:M3').format={'font':{'color':MUTED,'size':11},'row_height':29}
for cc in 'ABCDEFGHIJKLM':sd.get_range(f'{cc}:{cc}').format.column_width=15
cards=[('A','WORK ORDERS',f'=COUNTA(Production_Orders!A6:A{nw+5})','0'),
       ('D','PRODUCTION m³',f'=SUM(Production_Orders!F6:F{nw+5})','#,##0.0'),
       ('G','GROSS DEMAND t',f'=SUM(MRP_Weekly!F6:F{nm+5})/1000','#,##0.0'),
       ('J','PURCHASE VALUE $',f'=SUM(Purchase_Plan!K6:K{np+5})','$#,##0')]
for anchor,label,formula,fmt in cards:
    col='ABCDEFGHIJKLM'.index(anchor)
    start=col+1;end=min(start+2,13)
    a=letters(start);z=letters(end)
    sd.merge_cells(f'{a}5:{z}5');sd.merge_cells(f'{a}6:{z}8')
    sd.get_range(f'{a}5').values=[[label]]
    sd.get_range(f'{a}6').formulas=[[formula]]
    sd.get_range(f'{a}5:{z}5').format={'fill':TEAL,'font':{'color':WHITE,'bold':True,'size':10},'row_height':24}
    sd.get_range(f'{a}6:{z}8').format={'fill':BLUE,'font':{'color':NAVY,'bold':True,'size':22},'row_height':25}
    sd.get_range(f'{a}6').set_number_format(fmt)
sd.get_range('A10:C10').merge_cells('A10:C10') if False else None
sd.get_range('A11:D11').values=[['WEEK START','DEMAND (t)','SHORTAGE FLAGS','LATE RELEASES']]
sd.get_range('A11:D11').format={'fill':TEAL,'font':{'color':WHITE,'bold':True},'row_height':28}
import datetime
for i in range(12):
    row=12+i
    from datetime import timedelta,date
    week=(date(2026,11,2)+timedelta(weeks=i)).isoformat()
    sd.get_range(f'A{row}').values=[[week]]
    sd.get_range(f'B{row}').formulas=[[f'=SUMIF(MRP_Weekly!$D$6:$D${nm+5},A{row},MRP_Weekly!$F$6:$F${nm+5})/1000']]
    sd.get_range(f'C{row}').formulas=[[f'=SUMIF(MRP_Weekly!$D$6:$D${nm+5},A{row},MRP_Weekly!$U$6:$U${nm+5})']]
    sd.get_range(f'D{row}').formulas=[[f'=SUMIF(MRP_Weekly!$D$6:$D${nm+5},A{row},MRP_Weekly!$M$6:$M${nm+5})']]
sd.get_range('B12:B23').set_number_format('#,##0.0')
sd.get_range('C12:D23').set_number_format('0')
try:
    chart=sd.charts.add('ColumnClustered',sd.get_range('A11:B23'))
    chart.title_text='Weekly gross ingredient demand (tonnes)'
    chart.set_position('F11','M25')
except Exception as e:print('dashboard chart issue',str(e)[:300])
sd.merge_cells('A27:M28');sd.get_range('A27').values=[['METHOD NOTE  •  MRP suggested receipts cover safety stock subject to MOQ / lot multiple. Late-release POs are shifted to earliest standard-lead-time delivery.']]
sd.get_range('A27:M28').format={'fill':GOLD,'font':{'color':NAVY,'size':11},'wrap_text':True,'row_height':26}
sd.merge_cells('A30:M31');sd.get_range('A30').values=[['DATA NOTE  •  Original mix quantities and compressive strength are experimental observations. Production demand, stock, suppliers, lead times and costs are all synthetic.']]
sd.get_range('A30:M31').format={'fill':BLUE,'font':{'color':NAVY,'size':11},'wrap_text':True,'row_height':26}
sd.freeze_panes.freeze_rows(3)

ass=WB.worksheets.add('Assumptions')
ass.get_range('A1:E2').merge_cells('A1:E2') if False else None
ass.merge_cells('A1:E2');ass.get_range('A1').values=[['MODEL ASSUMPTIONS & DATA LINEAGE']]
ass.get_range('A1:E2').format={'fill':NAVY,'font':{'color':WHITE,'bold':True,'size':16},'row_height':23}
info=[['Setting','Value','Type','Detail','Source'],
 ['Original observations',1030,'Observed','Concrete mixture ingredients, curing days, strength','UCI / uploaded concrete.csv'],
 ['28-day observations',425,'Observed','Used for demonstration mix recipes','UCI / uploaded concrete.csv'],
 ['Planning as-of','2026-10-21','Scenario','Late release comparison cutoff','Scenario'],
 ['Production start','2026-11-02','Scenario','First weekly bucket','Scenario'],
 ['Planning horizon weeks',12,'Scenario','Week starts on Monday','Scenario'],
 ['Products',4,'Derived','Illustrative 25/35/45/55 MPa targets','Observed 28-day rows'],
 ['Work orders',144,'Simulated','3 orders per product/week','NumPy seeded'],
 ['Material pricing','USD/kg','Simulated','Illustrative only; no supplier quotes','Material master'],
 ['Lead time','0–3 weeks','Simulated','Primary suppliers','Material master'],
 ['Safety stock','0.35× average weekly demand','Scenario','Deterministic planning policy','Pipeline'],
 ['MOQ & order lot','By material','Simulated','Round receipts up to lot multiple','Material master'],
 ['Late releases','Release before as-of','Derived','Delay to earliest feasible weekly bucket','Pipeline'],
 ['Baseline projected inventory','Opening + existing receipts – gross','Derived','No newly recommended purchases','Pipeline'],
 ['Feasible projected inventory','Opening + scheduled + lead-feasible purchases – gross','Derived','Late receipts rescheduled, not treated as on-time','Pipeline'],
 ['Backlog','Max(0, –projected stock)','Derived','Snapshot by week, NOT summed across weeks','Pipeline'],
 ['Research/design caveat','Not certified','Warning','Measured lab strengths do not certify production-grade concrete','README']]
ass.get_range('A4:E20').values=info
ass.get_range('A4:E4').format={'fill':TEAL,'font':{'bold':True,'color':WHITE},'row_height':28}
for c,width in [('A',28),('B',25),('C',19),('D',61),('E',32)]:ass.get_range(f'{c}:{c}').format.column_width=width
ass.get_range('D5:D20').format.wrap_text=True
ass.get_range('A5:E20').format.row_height=29
ass.freeze_panes.freeze_rows(4)

print('Inspect summary',WB.inspect({'kind':'table','range':'Dashboard!A5:D13','include':'values,formulas','table_max_rows':10,'table_max_cols':4}).ndjson[:1800])
errs=WB.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A','options':{'use_regex':True,'max_results':20},'summary':'formula error validation'})
print('Formula errors',errs.ndjson[:1300])
SpreadsheetFile.export_xlsx(WB).save(str(OUT))
print('EXPORTED',OUT,OUT.stat().st_size)
