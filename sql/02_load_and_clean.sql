-- 02_load_and_clean.sql — PostgreSQL
-- Load: \copy stg_leads_raw(lead_id,lead_name,phone_raw,source,city,created_date,agent,status_raw,last_contact_date,deal_value_raw) FROM 'data/raw/leads_raw.csv' CSV HEADER;
-- Date convention: day-first (DD/MM/YYYY). Mixed formats: YYYY-MM-DD, DD/MM/YYYY, D Mon YYYY.

-- ---- 2a. Maps (idempotent) ----
INSERT INTO map_status(raw_key, clean_status, stage_rank) VALUES
 ('new','New',0),('','New',0),
 ('interested','Interested',2),
 ('positive','Positive',4),
 ('follow up','Follow-up',3),('follow-up','Follow-up',3),('followup','Follow-up',3),
 ('converted','Converted',5),('closed won','Converted',5),
 ('non-converted','Non-converted',1),('non converted','Non-converted',1),
 ('not interested','Non-converted',1),('lost','Non-converted',1)
ON CONFLICT (raw_key) DO UPDATE SET clean_status=EXCLUDED.clean_status, stage_rank=EXCLUDED.stage_rank;

INSERT INTO map_source(raw_key, clean_source) VALUES
 ('campus event','Campus Event'),('instagram','Instagram'),('referral','Referral'),
 ('direct','Direct'),('web form','Web Form'),('','Unattributed')
ON CONFLICT (raw_key) DO UPDATE SET clean_source=EXCLUDED.clean_source;

INSERT INTO map_city(raw_key, clean_city) VALUES
 ('bengaluru','Bengaluru'),('hyderabad','Hyderabad'),('chennai','Chennai'),('kochi','Kochi')
ON CONFLICT (raw_key) DO UPDATE SET clean_city=EXCLUDED.clean_city;

-- ---- 2b. Stage (normalize; read everything as text first) ----
DROP TABLE IF EXISTS leads_stage;
CREATE TABLE leads_stage AS
SELECT
  r.source_row_number,
  r.lead_id,
  COALESCE(NULLIF(INITCAP(TRIM(r.lead_name)),''),'Unknown') AS lead_name,
  CASE WHEN RIGHT(REGEXP_REPLACE(COALESCE(r.phone_raw,''),'\D','','g'),10) ~ '^[6-9][0-9]{9}$'
       THEN RIGHT(REGEXP_REPLACE(COALESCE(r.phone_raw,''),'\D','','g'),10) END AS phone_clean,
  COALESCE(msrc.clean_source,
           CASE WHEN TRIM(COALESCE(r.source,''))='' THEN 'Unattributed'
                ELSE INITCAP(TRIM(r.source)) END) AS source,
  COALESCE(mc.clean_city, INITCAP(TRIM(r.city))) AS city,
  TRIM(r.agent) AS agent,
  COALESCE(m.clean_status,'Unmapped') AS status,
  COALESCE(m.stage_rank,0) AS stage_rank,
  -- day-first date parsing: try ISO, DD/MM/YYYY, D Mon YYYY
  CASE
    WHEN TRIM(COALESCE(r.created_date,''))='' THEN NULL
    WHEN TRIM(r.created_date) ~ '^\d{4}-\d{2}-\d{2}' THEN SUBSTRING(TRIM(r.created_date),1,10)::DATE
    WHEN TRIM(r.created_date) ~ '^\d{1,2}/\d{1,2}/\d{4}' THEN TO_DATE(TRIM(r.created_date),'DD/MM/YYYY')
    ELSE TO_DATE(TRIM(r.created_date),'FMDD Mon YYYY')
  END AS created_date,
  CASE WHEN TRIM(COALESCE(r.last_contact_date,''))='' THEN NULL
       ELSE SUBSTRING(TRIM(r.last_contact_date),1,10)::DATE END AS last_contact_date,
  CASE WHEN COALESCE(m.clean_status,'Unmapped')='Converted'
       THEN COALESCE(NULLIF(REGEXP_REPLACE(COALESCE(r.deal_value_raw,''),'[^0-9.]','','g'),'')::NUMERIC,0)
       ELSE 0 END AS deal_value
FROM stg_leads_raw r
LEFT JOIN map_status m  ON LOWER(TRIM(COALESCE(r.status_raw,''))) = m.raw_key
LEFT JOIN map_source msrc ON LOWER(TRIM(COALESCE(r.source,''))) = msrc.raw_key
LEFT JOIN map_city mc ON LOWER(TRIM(COALESCE(r.city,''))) = mc.raw_key;

-- ---- 2c. DQ logs (never silently drop) ----
INSERT INTO dq_log(lead_id, source_row_number, issue_code, detail)
SELECT lead_id, source_row_number, 'INVALID_PHONE', COALESCE(phone_raw,'')
FROM leads_stage WHERE phone_clean IS NULL;
INSERT INTO dq_log(lead_id, source_row_number, issue_code, detail)
SELECT lead_id, source_row_number, 'UNMAPPED_STATUS', status FROM leads_stage WHERE status='Unmapped';
INSERT INTO dq_log(lead_id, source_row_number, issue_code, detail)
SELECT lead_id, source_row_number, 'BAD_DATE', 'created_date unparseable' FROM leads_stage WHERE created_date IS NULL;
INSERT INTO dq_log(lead_id, source_row_number, issue_code, detail)
SELECT lead_id, source_row_number, 'MISSING_SOURCE', 'blank source' FROM stg_leads_raw WHERE TRIM(COALESCE(source,''))='';

-- ---- 2d. Deduplicate on phone_clean ----
-- Survivor = highest stage_rank, then latest last_contact_date (nulls last), then lowest row number.
DROP TABLE IF EXISTS leads_ranked;
CREATE TABLE leads_ranked AS
SELECT *, ROW_NUMBER() OVER (
  PARTITION BY phone_clean
  ORDER BY stage_rank DESC, last_contact_date DESC NULLS LAST, source_row_number
) AS rn
FROM leads_stage WHERE phone_clean IS NOT NULL;

INSERT INTO dup_log(removed_lead_id, removed_row, survivor_lead_id, survivor_row, phone_clean)
SELECT d.lead_id, d.source_row_number, s.lead_id, s.source_row_number, d.phone_clean
FROM leads_ranked d JOIN leads_ranked s
  ON d.phone_clean = s.phone_clean AND s.rn = 1
WHERE d.rn > 1;

DROP TABLE IF EXISTS leads_clean;
CREATE TABLE leads_clean AS SELECT * FROM leads_ranked WHERE rn = 1;
ALTER TABLE leads_clean DROP COLUMN rn;

-- SQLite note: replace REGEXP_REPLACE with replace()/substr chains, INITCAP with
-- UPPER(SUBSTR())||LOWER(SUBSTR()), TO_DATE with date(), window functions work on 3.25+.
