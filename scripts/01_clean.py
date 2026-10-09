"""Mirror of sql/02_load_and_clean.sql in pandas — produces processed outputs
and verifies row accounting + headline KPIs. Run from repo root:
  python project1-lead-funnel/scripts/01_clean.py
"""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "leads_raw.csv"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

STATUS_MAP = {
 "new":"New","":"New","interested":"Interested","positive":"Positive",
 "follow up":"Follow-up","follow-up":"Follow-up","followup":"Follow-up",
 "converted":"Converted","closed won":"Converted",
 "non-converted":"Non-converted","non converted":"Non-converted",
 "not interested":"Non-converted","lost":"Non-converted",
}
RANK = {"New":0,"Non-converted":1,"Interested":2,"Follow-up":3,"Positive":4,"Converted":5}
SOURCE_MAP = {"campus event":"Campus Event","instagram":"Instagram","referral":"Referral",
 "direct":"Direct","web form":"Web Form","":"Unattributed"}
CITY_MAP = {"bengaluru":"Bengaluru","hyderabad":"Hyderabad","chennai":"Chennai","kochi":"Kochi"}

def clean_phone(p):
    d = re.sub(r"\D","",str(p or ""))
    t = d[-10:] if len(d)>=10 else ""
    if len(t)==10 and t[0] in "6789" and t.isdigit():
        return t
    return None

def parse_created(s):
    s=(s or "").strip()
    if not s: return None
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d %b %Y","%-d %b %Y"):
        try:
            # %-d unsupported on Windows; fall back
            return pd.to_datetime(s, dayfirst=True).date().isoformat()
        except Exception: pass
    try: return pd.to_datetime(s, dayfirst=True).date().isoformat()
    except Exception: return None

df = pd.read_csv(RAW, dtype=str, keep_default_na=False)
df["_row"] = range(1, len(df)+1)
stage = pd.DataFrame()
stage["source_row_number"]=df["_row"]; stage["lead_id"]=df["lead_id"]
stage["lead_name"]=df["lead_name"].str.strip().map(lambda x:"Unknown" if not x else x[:1].upper()+x[1:] if x else "Unknown")
stage["phone_clean"]=df["phone_raw"].map(clean_phone)
stage["source"]=df["source"].str.strip().str.lower().map(lambda k: SOURCE_MAP.get(k, k.title() if k else "Unattributed"))
stage["source"]=stage["source"].replace("", "Unattributed")
stage["city"]=df["city"].str.strip().str.lower().map(lambda k: CITY_MAP.get(k, k.title() if k else k))
stage["agent"]=df["agent"].str.strip()
stage["status"]=df["status_raw"].str.strip().str.lower().map(lambda k: STATUS_MAP.get(k,"Unmapped"))
stage["stage_rank"]=stage["status"].map(lambda s: RANK.get(s,0))
stage["created_date"]=df["created_date"].map(parse_created)
stage["last_contact_date"]=df["last_contact_date"].str.strip().str.slice(0,10).replace("",None)
def deal(r):
    if r["status"]!="Converted": return 0
    d=re.sub(r"[^0-9.]","",df.loc[df["lead_id"]==r["lead_id"],"deal_value_raw"].iloc[0] if (df["lead_id"]==r["lead_id"]).any() else "")
    try: return float(d) if d else 0
    except: return 0
# vectorized deal
nums = df["deal_value_raw"].str.replace("\u20b9","",regex=False).str.replace(",","",regex=False).str.strip()
nums = pd.to_numeric(nums, errors="coerce").fillna(0)
stage["deal_value"]=[float(n) if s=="Converted" else 0 for n,s in zip(nums, stage["status"])]
stage["phone_raw"]=df["phone_raw"]; stage["status_raw"]=df["status_raw"]

invalid = stage[stage["phone_clean"].isna()]
valid = stage[~stage["phone_clean"].isna()].copy()
valid = valid.sort_values(["phone_clean","stage_rank","last_contact_date","source_row_number"],
                          ascending=[True,False,False,True])
valid["rn"]=valid.groupby("phone_clean").cumcount()+1
dup = valid[valid["rn"]>1]; clean = valid[valid["rn"]==1].drop(columns=["rn"])
surv = valid[valid["rn"]==1].set_index("phone_clean")["lead_id"]
dup_log = pd.DataFrame({"removed_lead_id":dup["lead_id"].values,
 "removed_row":dup["source_row_number"].values,
 "survivor_lead_id":dup["phone_clean"].map(surv).values,
 "phone_clean":dup["phone_clean"].values})
dq = pd.DataFrame({"lead_id":invalid["lead_id"],"issue_code":"INVALID_PHONE","detail":invalid["phone_raw"]})
unmap = stage[stage["status"]=="Unmapped"][["lead_id"]]; unmap["issue_code"]="UNMAPPED_STATUS"; unmap["detail"]="status"
dq = pd.concat([dq, unmap], ignore_index=True)

clean_out = clean.drop(columns=["phone_raw","status_raw"])
clean_out.to_csv(PROC/"leads_clean.csv", index=False)
dup_log.to_csv(PROC/"dup_log.csv", index=False)
dq.to_csv(PROC/"dq_log.csv", index=False)

total=len(clean_out); conv=int((clean_out["status"]=="Converted").sum())
rev=float(clean_out["deal_value"].sum())
print(f"raw={len(df)} clean={len(clean_out)} dups={len(dup_log)} invalid={len(invalid)}")
assert len(df)==len(clean_out)+len(dup_log)+len(invalid), "row accounting failed"
assert clean_out["phone_clean"].duplicated().sum()==0, "dup phones remain"
print(f"total={total} converted={conv} conv%={round(100*conv/total,2) if total else 0} revenue={rev}")
by = clean_out.groupby("source").agg(leads=("lead_id","count"),conv=("status",lambda s:(s=="Converted").sum()),rev=("deal_value","sum"))
by["pct"]=round(100*by["conv"]/by["leads"],2)
print(by.sort_values("pct",ascending=False).to_string())
print("OK -> data/processed/leads_clean.csv")
