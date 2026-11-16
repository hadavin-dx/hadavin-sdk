-- M1: key-column rewrite evades a decrease trigger; a BEFORE UPDATE key guard closes it.
\set VERBOSITY verbose
\pset pager off
CREATE ROLE mig_v13 NOLOGIN; CREATE ROLE rt_v13 NOLOGIN;
GRANT ALL ON SCHEMA public TO mig_v13; GRANT USAGE ON SCHEMA public TO rt_v13;
SET ROLE mig_v13;
CREATE TABLE spend (agent_id text NOT NULL, day date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, day));
CREATE TABLE spend_month (agent_id text NOT NULL, month date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, month));
GRANT SELECT, INSERT, UPDATE ON spend, spend_month TO rt_v13;
ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
CREATE TABLE spend_decrease_log (agent_id text, day date, scope text, old_usd numeric, new_usd numeric,
  at timestamptz DEFAULT clock_timestamp(), who text DEFAULT session_user);
CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
  SET search_path = pg_catalog, public AS $f$
BEGIN
  INSERT INTO spend_decrease_log (agent_id, day, scope, old_usd, new_usd) VALUES (OLD.agent_id, OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd);
  RETURN NULL;
END $f$;
CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW WHEN (NEW.usd < OLD.usd) EXECUTE FUNCTION spend_log_decrease();
RESET ROLE;
SET ROLE rt_v13;
INSERT INTO spend VALUES ('x', '2026-11-16', 5);
\echo '--- M1a v12 design only (usd-decrease trigger): the key rewrite keeps usd equal, so nothing is logged'
UPDATE spend SET day = day - 3650 WHERE agent_id = 'x';
INSERT INTO spend (agent_id, day, usd) VALUES ('x', '2026-11-16', 0.5) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
\echo 'rows of spend for x (the old total now sits on a day nobody reads; today holds 0.5):'
SELECT agent_id, day, usd FROM spend ORDER BY day;
RESET ROLE;
SELECT 'log rows (expect 0):', count(*) FROM spend_decrease_log;
\echo '--- M1b the fix: a BEFORE UPDATE key guard on both tables'
SET ROLE mig_v13;
CREATE OR REPLACE FUNCTION spend_keep_keys() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $f$
BEGIN
  IF TG_TABLE_NAME = 'spend' THEN
    IF NEW.agent_id IS DISTINCT FROM OLD.agent_id OR NEW.day IS DISTINCT FROM OLD.day THEN
      RAISE EXCEPTION 'spend key columns may not change' USING ERRCODE = '42501'; END IF;
  ELSE
    IF NEW.agent_id IS DISTINCT FROM OLD.agent_id OR NEW.month IS DISTINCT FROM OLD.month THEN
      RAISE EXCEPTION 'spend key columns may not change' USING ERRCODE = '42501'; END IF;
  END IF;
  RETURN NEW;
END $f$;
CREATE TRIGGER spend_keep_keys BEFORE UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();
CREATE TRIGGER spend_keep_keys BEFORE UPDATE ON spend_month FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();
RESET ROLE;
SET ROLE rt_v13;
INSERT INTO spend VALUES ('y', '2026-11-16', 5);
INSERT INTO spend_month VALUES ('y', '2026-11-01', 5);
\echo 'expect 42501 for each key rewrite:'
UPDATE spend SET day = day - 3650 WHERE agent_id = 'y';
UPDATE spend SET agent_id = 'renamed' WHERE agent_id = 'y';
UPDATE spend_month SET month = month - 3650 WHERE agent_id = 'y';
UPDATE spend_month SET agent_id = 'renamed' WHERE agent_id = 'y';
\echo 'the legitimate writes still work (upsert +1, update -1):'
INSERT INTO spend (agent_id, day, usd) VALUES ('y', '2026-11-16', 1) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
UPDATE spend SET usd = usd + (-1) WHERE agent_id = 'y' AND day = '2026-11-16' RETURNING usd;
INSERT INTO spend_month (agent_id, month, usd) VALUES ('y', '2026-11-01', 1) ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd RETURNING usd;
UPDATE spend_month SET usd = usd + (-1) WHERE agent_id = 'y' AND month = '2026-11-01' RETURNING usd;
\echo 'ON CONFLICT DO UPDATE that also sets the key (must be refused too):'
INSERT INTO spend (agent_id, day, usd) VALUES ('y', '2026-11-16', 1) ON CONFLICT (agent_id, day) DO UPDATE SET day = EXCLUDED.day - 1;
\echo 'many small decrements are NOT stopped (each is a legal lowering); each is logged:'
UPDATE spend SET usd = usd + 1 WHERE agent_id = 'y' AND day = '2026-11-16';
UPDATE spend SET usd = usd - 0.1 WHERE agent_id = 'y' AND day = '2026-11-16';
UPDATE spend SET usd = usd - 0.1 WHERE agent_id = 'y' AND day = '2026-11-16';
UPDATE spend SET usd = 0 WHERE agent_id = 'y' AND day = '2026-11-16';
RESET ROLE;
SELECT agent_id, scope, old_usd, new_usd FROM spend_decrease_log ORDER BY at;
\echo '--- M1c can the runtime role switch the guard off? (expect 42501 must be owner)'
SET ROLE rt_v13;
ALTER TABLE spend DISABLE TRIGGER spend_keep_keys;
DROP TRIGGER spend_keep_keys ON spend;
RESET ROLE;
