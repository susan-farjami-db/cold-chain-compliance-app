-- Creates the schema + tables used by the Cold Chain app and seeds sample data.
-- Parameters: :catalog, :schema. Safe to re-run: seed rows are only inserted into empty tables.

CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema);

-- Master list of trailers feeding the Unit # dropdown.
CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.trailers') (
  trailer_id STRING COMMENT 'Trailer / unit number',
  body_type STRING,
  fleet_code STRING,
  active BOOLEAN
)
COMMENT 'Sample trailer master for the Cold Chain app';

-- Compliance records maintained through the app.
CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.cold_chain_compliance') (
  unit_number STRING COMMENT 'Unit Number',
  trailer_type STRING COMMENT 'Trailer',
  owner_name STRING COMMENT 'Contractor vs. Trailer Owner Name',
  last_update_date DATE COMMENT 'Last Update Date made via Application (auto-stamped)',
  last_change_description STRING COMMENT 'Detailed description of last change',
  updated_by STRING COMMENT 'User that made the update (auto-captured)',
  pending_action_items STRING COMMENT 'Pending Action Items',
  tval_status STRING COMMENT 'Compliant for T-Val (filter field)',
  recert_appt_date STRING COMMENT 'Re-Certification or Install Appointment Date'
)
COMMENT 'Cold Chain T-Val compliance records, maintained via the app';

-- Seed 30 synthetic reefer trailers.
INSERT INTO IDENTIFIER(:catalog || '.' || :schema || '.trailers')
SELECT
  CONCAT('R', LPAD(CAST(10000 + id AS STRING), 5, '0')) AS trailer_id,
  CASE WHEN id % 3 = 0 THEN 'Reefer 48ft' ELSE 'Reefer 53ft' END AS body_type,
  CASE WHEN id % 2 = 0 THEN 'CONTRACTOR' ELSE 'OWNED' END AS fleet_code,
  id % 10 <> 9 AS active
FROM RANGE(1, 31) AS t(id)
WHERE NOT EXISTS (SELECT 1 FROM IDENTIFIER(:catalog || '.' || :schema || '.trailers'));

-- Seed a handful of synthetic compliance records.
INSERT INTO IDENTIFIER(:catalog || '.' || :schema || '.cold_chain_compliance')
SELECT * FROM VALUES
  ('R10001', 'Reefer 53ft', 'Sample Carrier A', DATE'2026-09-02', 'Initial T-Val certification recorded', 'sample.user@example.com', NULL, 'Compliant for T-Val', NULL),
  ('R10002', 'Reefer 53ft', 'Sample Carrier B', DATE'2026-09-10', 'Temperature probe failed calibration', 'sample.user@example.com', 'Replace probe and re-test', 'NOT ABLE TO HAUL TVAL UNTIL HQ APPROVES', '2026-11-15'),
  ('R10003', 'Reefer 48ft', 'Sample Owner C', DATE'2026-09-18', 'Annual re-certification completed', 'sample.user@example.com', NULL, 'Compliant for T-Val', '2027-09-18'),
  ('R10004', 'Reefer 53ft', 'Sample Carrier A', DATE'2026-10-01', 'Data logger install scheduled', 'sample.user@example.com', 'Confirm install appointment', 'NOT ABLE TO HAUL TVAL UNTIL HQ APPROVES', '2026-11-04'),
  ('R10005', 'Reefer 53ft', 'Sample Owner D', DATE'2026-10-12', 'Door seal replaced, re-validated', 'sample.user@example.com', NULL, 'Compliant for T-Val', NULL)
  AS v(unit_number, trailer_type, owner_name, last_update_date, last_change_description, updated_by, pending_action_items, tval_status, recert_appt_date)
WHERE NOT EXISTS (SELECT 1 FROM IDENTIFIER(:catalog || '.' || :schema || '.cold_chain_compliance'));
