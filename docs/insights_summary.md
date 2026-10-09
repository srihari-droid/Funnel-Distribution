# Insights summary (1 page — SIMULATED data, seed 42, N=4000+240 dups)

Headline (verified Excel = Python/SQL-logic = DAX definitions): **3,928** unique leads,
**598** converted, **15.22%** conversion, **₹14,22,900** revenue, avg deal **₹2,379**.

- **Referral converts best at 28.27%** (573 leads, 162 converted), followed by Direct 21.16% and Campus Event 17.64%. Instagram (6.62%, 951 leads) and Web Form (6.78%, 590 leads) are high-volume, low-yield — Instagram meets the ≥100-leads & <5%? No: 6.6%, but still ~4× worse than Referral.
- **Funnel:** Leads 3928 → Contacted 3600 → Engaged 2472 → Qualified 998 → Converted 598. Biggest drop is Engaged→Qualified (Follow-up/Interested stall): follow-up process is the bottleneck, not closing.
- **Data quality:** 5.38% duplicates removed (logged), 1.98% invalid phones rejected, 84 blank sources → "Unattributed" (8.86% conv — worth tracking separately).

Recommendations:
1. Shift follow-up capacity toward Referral/Direct; protect response-time SLA there.
2. Fix Instagram/Web Form: audit message-to-lead match and first-contact speed before spending more; pilot revised script on 200 leads.
3. Add status-history table + enforce phone validation at entry (10-digit, 6–9 start, uniqueness check) to kill the 7% duplicate/invalid inflow.

Limitations: status = highest stage reached (no true step conversion); synthetic names/phones; day-first dates.
