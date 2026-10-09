# Metric dictionary (single source of truth — PRD A10)

| Metric | Definition | Formula |
|---|---|---|
| Total Leads | Unique leads after de-duplication | `COUNTROWS(fact_leads)` |
| Converted Leads | Unique leads with status = Converted | `CALCULATE([Total Leads], status="Converted")` |
| Conversion Rate | Converted ÷ Total (0 if no leads) | `DIVIDE([Converted],[Total],0)` — stored 2 decimals, displayed 1 |
| Stage reached | Status as highest stage reached. Ranks: New 0, Non-converted 1, Interested 2, Follow-up 3, Positive 4, Converted 5. Limitation: real system needs status-history table. | `stage_rank` |
| Contacted / Engaged / Qualified | rank ≥1 / ≥2 / ≥4 | DAX `Contacted/Engaged/Qualified` |
| Stage-to-stage conversion | Stage n+1 ÷ stage n | Funnel `step %` |
| Revenue | Sum deal_value for Converted only (others forced 0) | `SUM(deal_value)` |
| Avg Deal Value | Revenue ÷ Converted | `DIVIDE([Revenue],[Converted],0)` |
| Duplicate Rate | Dups removed ÷ raw rows | `228/4240 = 5.38%` (this run) |
| Invalid-phone Rate | Rejected invalid ÷ raw | `84/4240 = 1.98%` |

Day-first date convention (DD/MM/YYYY). Survivor rule: highest stage_rank, latest last_contact_date (nulls last), lowest row number. Row accounting: raw (4240) = clean (3928) + dups (228) + invalid (84).
