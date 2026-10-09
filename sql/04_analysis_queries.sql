-- 04_analysis_queries.sql — ≥8 analytical queries (PostgreSQL)
-- Q1 Headline KPIs
SELECT COUNT(*) AS total_leads,
       SUM(CASE WHEN status_name='Converted' THEN 1 ELSE 0 END) AS converted,
       ROUND(100.0*SUM(CASE WHEN status_name='Converted' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS conv_pct,
       COALESCE(SUM(deal_value),0) AS revenue,
       CASE WHEN SUM(CASE WHEN status_name='Converted' THEN 1 ELSE 0 END)>0
            THEN ROUND(SUM(deal_value)*1.0/SUM(CASE WHEN status_name='Converted' THEN 1 ELSE 0 END),2) END AS avg_deal
FROM fact_leads;

-- Q2 Conversion by source
SELECT s.source_name, COUNT(*) AS leads,
       SUM(CASE WHEN f.status_name='Converted' THEN 1 ELSE 0 END) AS converted,
       ROUND(100.0*SUM(CASE WHEN f.status_name='Converted' THEN 1 ELSE 0 END)/COUNT(*),2) AS conv_pct,
       COALESCE(SUM(f.deal_value),0) AS revenue
FROM fact_leads f JOIN dim_source s USING (source_key)
GROUP BY s.source_name ORDER BY conv_pct DESC;

-- Q3 Funnel (status = highest stage reached; rank: New 0, Non-converted 1, Interested 2, Follow-up 3, Positive 4, Converted 5)
SELECT stage, leads, ROUND(100.0*leads/NULLIF(LAG(leads) OVER (ORDER BY ord),0),1) AS step_pct
FROM (
  SELECT 1 ord,'Leads' stage, COUNT(*) leads FROM fact_leads
  UNION ALL SELECT 2,'Contacted', COUNT(*) FROM fact_leads WHERE stage_rank>=1
  UNION ALL SELECT 3,'Engaged',   COUNT(*) FROM fact_leads WHERE stage_rank>=2
  UNION ALL SELECT 4,'Qualified', COUNT(*) FROM fact_leads WHERE stage_rank>=4
  UNION ALL SELECT 5,'Converted', COUNT(*) FROM fact_leads WHERE stage_rank=5
) t ORDER BY ord;

-- Q4 High-volume, low-conversion sources (>=100 leads, <5%)
SELECT s.source_name, COUNT(*) leads,
       ROUND(100.0*SUM(CASE WHEN f.status_name='Converted' THEN 1 ELSE 0 END)/COUNT(*),2) conv_pct
FROM fact_leads f JOIN dim_source s USING (source_key)
GROUP BY s.source_name
HAVING COUNT(*)>=100 AND 100.0*SUM(CASE WHEN f.status_name='Converted' THEN 1 ELSE 0 END)/COUNT(*) < 5;

-- Q5 Monthly trend
SELECT DATE_TRUNC('month',created_date) AS month, COUNT(*) leads,
       ROUND(100.0*SUM(CASE WHEN status_name='Converted' THEN 1 ELSE 0 END)/COUNT(*),2) conv_pct,
       COALESCE(SUM(deal_value),0) revenue
FROM fact_leads GROUP BY 1 ORDER BY 1;

-- Q6 Agent leaderboard
SELECT a.agent_name, COUNT(*) leads,
       SUM(CASE WHEN f.status_name='Converted' THEN 1 ELSE 0 END) converted,
       ROUND(100.0*SUM(CASE WHEN f.status_name='Converted' THEN 1 ELSE 0 END)/COUNT(*),2) conv_pct,
       COALESCE(SUM(f.deal_value),0) revenue
FROM fact_leads f JOIN dim_agent a USING (agent_key) GROUP BY a.agent_name ORDER BY revenue DESC;

-- Q7 Duplicate audit (must return zero rows on clean table)
SELECT phone_clean, COUNT(*) FROM leads_clean GROUP BY phone_clean HAVING COUNT(*)>1;

-- Q8 Row accounting (raw = clean + dups + rejected/invalid; invalids excluded before ranking so no overlap)
SELECT (SELECT COUNT(*) FROM stg_leads_raw) AS raw_rows,
       (SELECT COUNT(*) FROM leads_clean)   AS clean_rows,
       (SELECT COUNT(*) FROM dup_log)       AS dups_removed,
       (SELECT COUNT(*) FROM dq_log WHERE issue_code='INVALID_PHONE') AS invalid_phone;

-- Q9 Conversion by city
SELECT c.city_name, COUNT(*) leads,
       ROUND(100.0*SUM(CASE WHEN f.status_name='Converted' THEN 1 ELSE 0 END)/COUNT(*),2) conv_pct
FROM fact_leads f JOIN dim_city c USING (city_key) GROUP BY c.city_name ORDER BY conv_pct DESC;

-- Q10 Status distribution
SELECT status_name, COUNT(*) leads,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),2) AS share_pct
FROM fact_leads GROUP BY status_name ORDER BY leads DESC;
