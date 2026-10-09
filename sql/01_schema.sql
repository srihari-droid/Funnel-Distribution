-- 01_schema.sql — Project 1 Lead Funnel (PostgreSQL 16)
-- Run: psql -d leadsdb -f sql/01_schema.sql
DROP TABLE IF EXISTS fact_leads;
DROP TABLE IF EXISTS dim_date; DROP TABLE IF EXISTS dim_status;
DROP TABLE IF EXISTS dim_city; DROP TABLE IF EXISTS dim_agent; DROP TABLE IF EXISTS dim_source;
DROP TABLE IF EXISTS leads_clean; DROP TABLE IF EXISTS leads_ranked; DROP TABLE IF EXISTS leads_stage;
DROP TABLE IF EXISTS dup_log; DROP TABLE IF EXISTS dq_log;
DROP TABLE IF EXISTS map_city; DROP TABLE IF EXISTS map_source; DROP TABLE IF EXISTS map_status;
DROP TABLE IF EXISTS stg_leads_raw;

CREATE TABLE stg_leads_raw (
  source_row_number SERIAL PRIMARY KEY,
  lead_id TEXT, lead_name TEXT, phone_raw TEXT, source TEXT, city TEXT,
  created_date TEXT, agent TEXT, status_raw TEXT,
  last_contact_date TEXT, deal_value_raw TEXT
);

CREATE TABLE map_status (raw_key TEXT PRIMARY KEY, clean_status TEXT NOT NULL, stage_rank INT NOT NULL);
CREATE TABLE map_source (raw_key TEXT PRIMARY KEY, clean_source TEXT NOT NULL);
CREATE TABLE map_city   (raw_key TEXT PRIMARY KEY, clean_city TEXT NOT NULL);

CREATE TABLE dq_log  (id SERIAL PRIMARY KEY, lead_id TEXT, source_row_number INT, issue_code TEXT, detail TEXT);
CREATE TABLE dup_log (removed_lead_id TEXT, removed_row INT, survivor_lead_id TEXT, survivor_row INT, phone_clean TEXT);

-- Maps are populated in 02_load_and_clean.sql (idempotent inserts).
