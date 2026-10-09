# Project 1 — Lead Funnel & Source Attribution (SIMULATED data)

End-to-end lead funnel on a synthetic dataset: Excel → SQL (PostgreSQL) → Power BI.

## Reproduce (< 15 min)
```bash
python scripts/00_generate_data.py --out data/raw/leads_raw.csv
python scripts/01_clean.py                 # -> data/processed/leads_clean.csv + dup/dq logs + KPI check
python scripts/02_build_excel.py           # -> excel/Project1_Lead_Funnel.xlsx
# SQL (PostgreSQL 16): psql -d leadsdb -f sql/01_schema.sql, then 02, 03, 04
#   or: \copy stg_leads_raw(...) FROM 'data/raw/leads_raw.csv' CSV HEADER;
# Power BI: follow powerbi/README_powerbi.md, paste measures.dax
```

## Results (seed 42 — your run must match exactly)
raw 4240 = clean 3928 + dups 228 + invalid 84 · total 3928 · converted 598 ·
conv 15.22% · revenue 1422900 · top source Referral 28.27%.

## Structure
```
data/raw/leads_raw.csv  data/processed/leads_clean.csv (+dup_log, dq_log)
scripts/00_generate_data.py  scripts/01_clean.py  scripts/02_build_excel.py
sql/01_schema.sql  sql/02_load_and_clean.sql  sql/03_model.sql  sql/04_analysis_queries.sql
excel/Project1_Lead_Funnel.xlsx  powerbi/measures.dax, powerquery_m.txt, README_powerbi.md
docs/metric_dictionary.md  docs/insights_summary.md
```

## Notes
- All data synthetic (phones 6–9 start, `Person N` names). Never present as client data.
- Dates day-first. Status = highest stage reached (documented limitation).
- Excel = SQL = Power BI reconciliation table in workbook `Reconcile` + `powerbi/README_powerbi.md`.
- Resume template: "Built end-to-end lead funnel on simulated [3928] leads: cleaned [312] duplicate/invalid records with Excel/SQL, defined conversion metrics, Power BI dashboard identified [Referral] as top channel at [28.27]%."
