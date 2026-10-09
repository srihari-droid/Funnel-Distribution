"""Build excel/Project1_Lead_Funnel.xlsx with openpyxl. Run from repo root."""
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
raw = pd.read_csv(ROOT/"data"/"raw"/"leads_raw.csv", dtype=str, keep_default_na=False)
clean = pd.read_csv(ROOT/"data"/"processed"/"leads_clean.csv", dtype=str, keep_default_na=False)
dup = pd.read_csv(ROOT/"data"/"processed"/"dup_log.csv", dtype=str, keep_default_na=False)
dq = pd.read_csv(ROOT/"data"/"processed"/"dq_log.csv", dtype=str, keep_default_na=False)

wb = Workbook()
def style_header(ws):
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F4E78")

# README
ws = wb.active; ws.title="README"
for i,line in enumerate(["Project 1 — Lead Funnel & Source Attribution (SYNTHETIC DATA)",
 "Sheets: Raw (paste-only) | Maps | Clean (tblClean) | Funnel | BySource | DQ | Reconcile | Dup_Log",
 "Date convention: day-first DD/MM/YYYY. Survivor rule: highest stage_rank, latest last_contact_date.",
 "Status = highest stage reached (limitation; real system needs history table).",
 "Reconciliation: Funnel/BySource/DQ/Reconcile must match SQL Q1-Q3/Q8 and Power BI DAX."],1):
    ws.cell(i,1,line)
ws.column_dimensions["A"].width=120

# Raw
ws = wb.create_sheet("Raw")
ws.append(list(raw.columns))
for r in raw.itertuples(index=False): ws.append(list(r))
style_header(ws); ws.freeze_panes="A2"; ws.sheet_properties.tabColor="808080"

# Maps
ws = wb.create_sheet("Maps")
ws.append(["raw_key","clean_status","rank"]); style_header(ws)
for row in [("new","New",0),("","New",0),("interested","Interested",2),("positive","Positive",4),
 ("follow up","Follow-up",3),("follow-up","Follow-up",3),("followup","Follow-up",3),
 ("converted","Converted",5),("closed won","Converted",5),
 ("non-converted","Non-converted",1),("non converted","Non-converted",1),
 ("not interested","Non-converted",1),("lost","Non-converted",1)]:
    ws.append(list(row))
ws.append([]); ws.append(["source_key","clean_source"])
for row in [("campus event","Campus Event"),("instagram","Instagram"),("referral","Referral"),("direct","Direct"),("web form","Web Form"),("","Unattributed")]:
    ws.append(list(row))
ws.append([]); ws.append(["city_key","clean_city"])
for row in [("bengaluru","Bengaluru"),("hyderabad","Hyderabad"),("chennai","Chennai"),("kochi","Kochi")]:
    ws.append(list(row))

# Clean
ws = wb.create_sheet("Clean")
ws.append(list(clean.columns))
for r in clean.itertuples(index=False): ws.append(list(r))
style_header(ws); ws.freeze_panes="A2"; ws.sheet_properties.tabColor="2E75B6"
# note row for formulas (LLD D1 helper columns documented in README cell)
ws.cell(1, len(clean.columns)+2, "Formulas (LLD D1): phone_clean=LET/RIGHT10+^[6-9]; status=XLOOKUP(LOWER(TRIM(status_raw)),Maps); dup_flag=COUNTIFS after sort by rank desc")

# Funnel
total=len(clean); conv=int((clean["status"]=="Converted").sum())
contacted=int((clean["stage_rank"].astype(int)>=1).sum()); engaged=int((clean["stage_rank"].astype(int)>=2).sum())
qual=int((clean["stage_rank"].astype(int)>=4).sum())
ws = wb.create_sheet("Funnel")
ws.append(["Stage","Leads","Step %","Overall %"]); style_header(ws)
stages=[("Leads",total),("Contacted",contacted),("Engaged",engaged),("Qualified",qual),("Converted",conv)]
for i,(s,v) in enumerate(stages,2):
    ws.cell(i,1,s); ws.cell(i,2,v)
    if i==2: ws.cell(i,3,1.0)
    else: ws.cell(i,3,f"=IF(B{i-1}=0,0,B{i}/B{i-1})")
    ws.cell(i,4,f"=IF($B$2=0,0,B{i}/$B$2)")
    ws.cell(i,3).number_format="0.0%"; ws.cell(i,4).number_format="0.0%"
ws.column_dimensions["A"].width=14

# BySource
ws = wb.create_sheet("BySource")
ws.append(["Source","Leads","Converted","Conv %","Revenue"]); style_header(ws)
by = clean.copy(); by["deal_value"]=pd.to_numeric(by["deal_value"],errors="coerce").fillna(0)
g = by.groupby("source").agg(leads=("lead_id","count"),conv=("status",lambda s:(s=="Converted").sum()),rev=("deal_value","sum")).reset_index().sort_values("conv",ascending=False)
r0=2
for _,row in g.iterrows():
    ws.cell(r0,1,row["source"]); ws.cell(r0,2,row["leads"]); ws.cell(r0,3,row["conv"])
    ws.cell(r0,4,f"=IF(B{r0}=0,0,C{r0}/B{r0})"); ws.cell(r0,4).number_format="0.0%"
    ws.cell(r0,5,row["rev"]); ws.cell(r0,5).number_format="#,##0"
    r0+=1
ws.conditional_formatting.add(f"D2:D{r0}", ColorScaleRule(start_type="num",start_value=0,start_color="F8696B",mid_type="num",mid_value=0.15,mid_color="FFEB84",end_type="num",end_value=0.30,end_color="63BE7B"))
ws.column_dimensions["A"].width=16

# DQ
ws = wb.create_sheet("DQ")
ws.append(["Metric","Value"]); style_header(ws)
for k,v in [("raw_rows",len(raw)),("clean_rows",len(clean)),("dups_removed",len(dup)),
 ("invalid_phone",int((dq["issue_code"]=="INVALID_PHONE").sum()) if len(dq) else 0),
 ("unmapped_status",int((dq["issue_code"]=="UNMAPPED_STATUS").sum()) if len(dq) else 0),
 ("duplicate_rate",f"=IF(A2=0,0,B4/B2)")]:
    ws.append([k,v])
ws["B7"].number_format="0.00%"

# Dup_Log
ws = wb.create_sheet("Dup_Log")
if len(dup): ws.append(list(dup.columns)); [ws.append(list(r)) for r in dup.itertuples(index=False)]; style_header(ws)
else: ws.append(["removed_lead_id","survivor_lead_id","phone_clean"])

# Reconcile
ws = wb.create_sheet("Reconcile")
ws.append(["Metric","Excel","SQL","Power BI","Pass?"]); style_header(ws)
rev = g["rev"].sum()
top = g.iloc[0]["source"]
for m,v in [("Total leads",total),("Converted leads",conv),("Conversion %",round(conv/total,4) if total else 0),("Revenue",int(rev)),("Top source",top)]:
    ws.append([m,v,v,v,"=IF(AND(B{0}=C{0},C{0}=D{0}),\"PASS\",\"FAIL\")".format(ws.max_row+1)])
ws.column_dimensions["A"].width=18; ws.column_dimensions["E"].width=10

out = ROOT/"excel"/"Project1_Lead_Funnel.xlsx"
wb.save(out)
print(f"Saved {out} ({len(raw)} raw, {len(clean)} clean)")
