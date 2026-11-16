-- M3 and M5: held-table grants, CREATE OR REPLACE FUNCTION, no runtime grant on the log, fail-closed log, cost.
\set VERBOSITY verbose
\pset pager off
CREATE ROLE mig_v14 NOLOGIN; CREATE ROLE rt_v14 NOLOGIN;
GRANT ALL ON SCHEMA public TO mig_v14; GRANT USAGE ON SCHEMA public TO rt_v14;
SET ROLE mig_v14;
CREATE TABLE spend (agent_id text NOT NULL, day date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, day));
GRANT SELECT, INSERT, UPDATE ON spend TO rt_v14;
CREATE TABLE spend_decrease_log (id bigserial PRIMARY KEY, agent_id text, day date, scope text, old_usd numeric, new_usd numeric,
  at timestamptz DEFAULT clock_timestamp(), who text DEFAULT session_user);
CREATE INDEX spend_decrease_log_by_day ON spend_decrease_log (agent_id, day, at);
CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
  SET search_path = pg_catalog, public AS $f$
BEGIN
  INSERT INTO spend_decrease_log (agent_id, day, scope, old_usd, new_usd) VALUES (OLD.agent_id, OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd);
  RETURN NULL;
END $f$;
\echo 'CREATE OR REPLACE twice (idempotent; the migration guard accepts only OR REPLACE):'
CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
  SET search_path = pg_catalog, public AS $f$
BEGIN
  INSERT INTO spend_decrease_log (agent_id, day, scope, old_usd, new_usd) VALUES (OLD.agent_id, OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd);
  RETURN NULL;
END $f$;
CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW WHEN (NEW.usd < OLD.usd) EXECUTE FUNCTION spend_log_decrease();
REVOKE ALL ON FUNCTION spend_log_decrease() FROM PUBLIC;
RESET ROLE;
\echo '--- the runtime role has no grant on the log (REVOKE ALL, empty runtime list as the GRANTS entry would give):'
REVOKE ALL ON TABLE spend_decrease_log FROM rt_v14;
REVOKE ALL ON SEQUENCE spend_decrease_log_id_seq FROM rt_v14;
SET ROLE rt_v14;
INSERT INTO spend VALUES ('a', '2026-11-16', 5);
\echo 'a lowering UPDATE by the runtime role works and writes one row through the function:'
UPDATE spend SET usd = usd + (-2) WHERE agent_id = 'a' RETURNING usd;
\echo 'raising writes none:'
UPDATE spend SET usd = usd + 1 WHERE agent_id = 'a' RETURNING usd;
\echo 'the runtime role is denied every statement on the log (expect 42501 x5):'
SELECT * FROM spend_decrease_log;
INSERT INTO spend_decrease_log (agent_id) VALUES ('forged');
UPDATE spend_decrease_log SET new_usd = 99;
DELETE FROM spend_decrease_log;
TRUNCATE spend_decrease_log;
\echo 'and may not call the function by hand (expect 42501):'
SELECT spend_log_decrease();
RESET ROLE;
SELECT 'log rows (expect 1):', count(*) FROM spend_decrease_log;
\echo '--- fail-closed: if the log cannot be written, the settle (UPDATE) fails and the total does not change'
SET ROLE mig_v14;
ALTER TABLE spend_decrease_log ADD CONSTRAINT full_disk_stand_in CHECK (false) NOT VALID;
RESET ROLE;
SET ROLE rt_v14;
UPDATE spend SET usd = usd + (-1) WHERE agent_id = 'a' RETURNING usd;
SELECT usd FROM spend WHERE agent_id = 'a';
RESET ROLE;
SET ROLE mig_v14;
ALTER TABLE spend_decrease_log DROP CONSTRAINT full_disk_stand_in;
RESET ROLE;
\echo '--- cost of the trigger: 20000 lowering UPDATEs inside one DO block, with and without the trigger (local, indicative only)'
SET ROLE mig_v14;
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
  RAISE NOTICE 'without trigger: % ms; with trigger: % ms (20000 updates each)', round(extract(epoch from (t1-t0))*1000), round(extract(epoch from (t2-t1))*1000);
END $$;
RESET ROLE;
SELECT 'log rows now:', count(*) FROM spend_decrease_log;
SELECT 'log table + index size (bytes) for those rows:', pg_total_relation_size('spend_decrease_log');
