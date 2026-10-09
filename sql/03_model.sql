-- 03_model.sql — star schema, grain: one row per unique lead
DROP TABLE IF EXISTS fact_leads;
DROP TABLE IF EXISTS dim_date; DROP TABLE IF EXISTS dim_status;
DROP TABLE IF EXISTS dim_city; DROP TABLE IF EXISTS dim_agent; DROP TABLE IF EXISTS dim_source;

CREATE TABLE dim_status AS
SELECT DISTINCT clean_status AS status_name, stage_rank,
       (clean_status='Converted') AS is_converted FROM map_status;

CREATE TABLE dim_source AS
SELECT ROW_NUMBER() OVER (ORDER BY source) AS source_key, source AS source_name,
       CASE WHEN source IN ('Campus Event','Direct') THEN 'Offline'
            WHEN source IN ('Instagram','Web Form') THEN 'Online'
            WHEN source='Referral' THEN 'Word of mouth' ELSE 'Other' END AS channel_type
FROM (SELECT DISTINCT source FROM leads_clean) s;

CREATE TABLE dim_agent AS
SELECT ROW_NUMBER() OVER (ORDER BY agent) AS agent_key, agent AS agent_name
FROM (SELECT DISTINCT agent FROM leads_clean) a;

CREATE TABLE dim_city AS
SELECT ROW_NUMBER() OVER (ORDER BY city) AS city_key, city AS city_name
FROM (SELECT DISTINCT city FROM leads_clean) c;

CREATE TABLE dim_date AS
SELECT d::DATE AS date_key, d::DATE AS date,
       DATE_TRUNC('month', d::DATE)::DATE AS month,
       TO_CHAR(d::DATE,'Mon YYYY') AS month_name,
       EXTRACT(YEAR FROM d::DATE)::INT AS year,
       EXTRACT(WEEK FROM d::DATE)::INT AS week
FROM GENERATE_SERIES((SELECT MIN(created_date) FROM leads_clean),
                     (SELECT MAX(created_date) FROM leads_clean), '1 day') d;

CREATE TABLE fact_leads AS
SELECT c.lead_id, ds.source_key, da.agent_key, dc.city_key,
       st.status_name, c.stage_rank, c.deal_value,
       c.created_date, c.last_contact_date, c.phone_clean,
       c.lead_name, c.agent, c.source, c.city
FROM leads_clean c
JOIN dim_source ds ON ds.source_name = c.source
JOIN dim_agent  da ON da.agent_name  = c.agent
JOIN dim_city   dc ON dc.city_name   = c.city
JOIN dim_status st ON st.status_name = c.status;
