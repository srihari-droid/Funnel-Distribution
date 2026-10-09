# Power BI report — build steps (LeadFunnel.pbix cannot be generated headless; build in Desktop in ~30 min)

Import: `data/processed/leads_clean.csv` via `powerbi/powerquery_m.txt`, or Postgres tables
`fact_leads + dim_*` (DirectQuery/Import). Apply `powerbi/measures.dax`.

## Page 1 — Funnel & Attribution (slicers on top: Month | Source | City | Agent)
| KPI cards (4) | Funnel bar (FunnelStages + [Funnel Value]) | Bar: [Conversion %] by source + [Overall Conv Benchmark] constant line |
| Combo: monthly leads (columns) + [Conversion %] (line) |
Rules: max 6 visuals; same colour = same meaning; % with 1 decimal display; every visual titled as a question.

## Page 2 — Data Quality
Cards: raw rows, clean rows, dups removed, invalid phones, duplicate rate. Table: `dq_log` by issue_code.

## Reconciliation (must PASS, tolerance 0 on stored 2-decimal values)
| Metric | Value (this run, seed 42) |
|---|---|
| Total leads | 3928 |
| Converted leads | 598 |
| Conversion % | 15.22% |
| Revenue | 1422900 |
| Top source | Referral 28.27% |
Copy these into `excel/...xlsx > Reconcile` columns C (SQL) and D (Power BI) after running
`sql/04_analysis_queries.sql` Q1/Q2 and reading the DAX cards.
