-- v14 M1 of the security review: cost, size and fail-closed behaviour of the decrease record on the FINAL schema
-- of held file 2 (column "period"; v13 measured an older schema with a column "day"). Local, indicative only.
\set VERBOSITY verbose
\pset pager off
\set ON_ERROR_STOP 0
CREATE ROLE mig14c NOLOGIN; CREATE ROLE rt14c NOLOGIN;
GRANT ALL ON SCHEMA public TO mig14c; GRANT USAGE ON SCHEMA public TO rt14c;
SET ROLE mig14c;
CREATE TABLE spend (agent_id text NOT NULL, day date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, day));
CREATE TABLE spend_month (agent_id text NOT NULL, month date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, month));
GRANT SELECT, INSERT, UPDATE ON spend, spend_month TO rt14c;
\i spend_decrease_log.sql
RESET ROLE;
REVOKE ALL ON TABLE spend_decrease_log FROM rt14c;
SET ROLE rt14c;
INSERT INTO spend VALUES ('a', '2026-11-16', 5);
UPDATE spend SET usd = usd - 2 WHERE agent_id = 'a' RETURNING usd;
RESET ROLE;
SELECT 'log rows (expect 1):', count(*) FROM spend_decrease_log;
\echo '--- fail-closed: if the log cannot be written, the lowering fails and the total does not change'
SET ROLE mig14c;
ALTER TABLE spend_decrease_log ADD CONSTRAINT full_disk_stand_in CHECK (false) NOT VALID;
RESET ROLE;
SET ROLE rt14c;
UPDATE spend SET usd = usd - 1 WHERE agent_id = 'a' RETURNING usd;
SELECT usd AS total_after_refused_lowering FROM spend WHERE agent_id = 'a';
RESET ROLE;
SET ROLE mig14c;
ALTER TABLE spend_decrease_log DROP CONSTRAINT full_disk_stand_in;
\echo '--- the size figures a status line could read (the portal role has no table privilege needed for these functions? checked in the Python run)'
RESET ROLE;
\echo '--- cost of the trigger: 20000 lowering UPDATEs inside one DO block, with and without the trigger (local, indicative only)'
SET ROLE mig14c;
DO $$ DECLARE t0 timestamptz; t1 timestamptz; t2 timestamptz; i int;
BEGIN
  INSERT INTO spend VALUES ('perf', '2026-11-16', 1000000);
  ALTER TABLE spend DISABLE TRIGGER spend_log_decrease;
  t0 := clock_timestamp();
  FOR i IN 1..20000 LOOP UPDATE spend SET usd = usd + (-0.01) WHERE agent_id = 'perf'; END LOOP;
  t1 := clock_timestamp();
  ALTER TABLE spend ENABLE TRIGGER spend_log_decrease;
  FOR i IN 1..20000 LOOP UPDATE spend SET usd = usd + (-0.01) WHERE agent_id = 'perf'; END LOOP;
  t2 := clock_timestamp();
  RAISE NOTICE 'without the logging trigger: % ms; with it: % ms (20000 updates each)', round(extract(epoch from (t1-t0))*1000), round(extract(epoch from (t2-t1))*1000);
END $$;
RESET ROLE;
SELECT 'log rows now:', count(*) FROM spend_decrease_log;
SELECT 'log table + index size (bytes) for those rows:', pg_total_relation_size('spend_decrease_log');
SELECT 'bytes per row:', round(pg_total_relation_size('spend_decrease_log')::numeric / count(*), 1) FROM spend_decrease_log;
