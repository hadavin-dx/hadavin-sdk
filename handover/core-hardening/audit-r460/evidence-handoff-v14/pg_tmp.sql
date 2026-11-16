-- v14 B1 (security) experiments: the temporary-table bypass of the decrease record, the fix, REVOKE TEMP, a schema
-- other than public, the not-a-number trigger condition, and what ADD CONSTRAINT locks. Private cluster, made-up data.
-- Run as the postgres user by pg_experiment_v14.sh, which copies the two held files next to this script.
\set VERBOSITY verbose
\pset pager off
\set ON_ERROR_STOP 0
CREATE ROLE mig14 NOLOGIN; CREATE ROLE rt14 NOLOGIN;
GRANT ALL ON SCHEMA public TO mig14; GRANT USAGE ON SCHEMA public TO rt14;
SET ROLE mig14;
CREATE TABLE spend (agent_id text NOT NULL, day date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, day));
CREATE TABLE spend_month (agent_id text NOT NULL, month date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, month));
GRANT SELECT, INSERT, UPDATE ON spend, spend_month TO rt14;
RESET ROLE;
\echo '=== T0 the v13 function (unqualified name, search_path pg_catalog, public) is bypassed by a temporary table'
SET ROLE mig14;
CREATE TABLE spend_decrease_log (agent_id text NOT NULL, period date NOT NULL, scope text NOT NULL, old_usd numeric NOT NULL, new_usd numeric NOT NULL, at timestamptz NOT NULL DEFAULT clock_timestamp(), who text NOT NULL DEFAULT session_user);
CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $f$
BEGIN INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES (OLD.agent_id, OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd); RETURN NULL; END $f$;
CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW WHEN (NEW.usd < OLD.usd) EXECUTE FUNCTION spend_log_decrease();
RESET ROLE;
SET ROLE rt14;
INSERT INTO spend VALUES ('a', '2026-11-16', 5);
\echo 'runtime role creates a temporary table of the same name as the log (PUBLIC may create temporary tables by default):'
CREATE TEMP TABLE spend_decrease_log (agent_id text, period date, scope text, old_usd numeric, new_usd numeric, at timestamptz DEFAULT clock_timestamp(), who text DEFAULT session_user);
UPDATE spend SET usd = usd - 3 WHERE agent_id = 'a' RETURNING usd;
SELECT 'temp table rows (the attacker sees the row here):', count(*) FROM pg_temp.spend_decrease_log;
DROP TABLE pg_temp.spend_decrease_log;
RESET ROLE;
SELECT 'REAL log rows after the lowering (v13 function; expect 0 = the bypass works):', count(*) FROM public.spend_decrease_log;
DROP TABLE public.spend_decrease_log CASCADE;
\echo '=== T1 the v14 held file 2 (schema-qualified through TG_TABLE_SCHEMA, search_path pg_catalog, pg_temp) with the same attack'
SET ROLE mig14;
\i spend_decrease_log.sql
RESET ROLE;
REVOKE ALL ON TABLE spend_decrease_log FROM rt14;
SET ROLE rt14;
CREATE TEMP TABLE spend_decrease_log (agent_id text, period date, scope text, old_usd numeric, new_usd numeric, at timestamptz DEFAULT clock_timestamp(), who text DEFAULT session_user);
UPDATE spend SET usd = usd - 1 WHERE agent_id = 'a' RETURNING usd;
SELECT 'temp table rows (expect 0):', count(*) FROM pg_temp.spend_decrease_log;
DROP TABLE pg_temp.spend_decrease_log;
RESET ROLE;
SELECT 'REAL log rows (v14 function; expect 1 = the real log got the row):', count(*) FROM public.spend_decrease_log;
\echo '=== T2 REVOKE TEMPORARY ON DATABASE ... FROM PUBLIC: the runtime role can no longer create the temporary table (expect 42501)'
SELECT has_database_privilege('rt14', current_database(), 'TEMP') AS rt14_can_temp_before;
REVOKE TEMPORARY ON DATABASE exp FROM PUBLIC;
SELECT has_database_privilege('rt14', current_database(), 'TEMP') AS rt14_can_temp_after;
SET ROLE rt14;
CREATE TEMP TABLE spend_decrease_log (agent_id text);
RESET ROLE;
\echo 'the migration role (database owner is postgres here; the check uses the role name) is unaffected only if it holds TEMP itself:'
GRANT TEMPORARY ON DATABASE exp TO mig14;
SELECT has_database_privilege('mig14', current_database(), 'TEMP') AS mig14_can_temp;
\echo '=== T3 a schema other than public: the function writes the log of the schema of the table that fired it'
CREATE SCHEMA s14 AUTHORIZATION mig14;
GRANT USAGE ON SCHEMA s14 TO rt14;
SET ROLE mig14;
SET search_path = s14;
CREATE TABLE spend (agent_id text NOT NULL, day date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, day));
CREATE TABLE spend_month (agent_id text NOT NULL, month date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, month));
GRANT SELECT, INSERT, UPDATE ON s14.spend, s14.spend_month TO rt14;
\i spend_decrease_log.sql
RESET ROLE;
REVOKE ALL ON TABLE s14.spend_decrease_log FROM rt14;
SET ROLE rt14;
INSERT INTO s14.spend VALUES ('b', '2026-11-16', 4);
UPDATE s14.spend SET usd = usd - 1 WHERE agent_id = 'b' RETURNING usd;
RESET ROLE;
SELECT 's14 log rows (expect 1):', count(*) FROM s14.spend_decrease_log;
SELECT 'public log rows still (expect 1, unchanged):', count(*) FROM public.spend_decrease_log;
RESET search_path;
\echo '=== T6 trigger condition: lowering, raising, NaN, Infinity, no change (DB-2 applied alone, no CHECK; expect 4 rows: 5->4, 6->NaN, NaN->5, 5->Infinity; the raise 4->6 and NaN->NaN write none)'
TRUNCATE public.spend_decrease_log;
SET ROLE rt14;
INSERT INTO spend VALUES ('c', '2026-11-16', 5);
UPDATE spend SET usd = usd - 1 WHERE agent_id = 'c';
UPDATE spend SET usd = usd + 2 WHERE agent_id = 'c';
UPDATE spend SET usd = 'NaN' WHERE agent_id = 'c';
UPDATE spend SET usd = 'NaN' WHERE agent_id = 'c';
UPDATE spend SET usd = 5 WHERE agent_id = 'c';
UPDATE spend SET usd = 'Infinity' WHERE agent_id = 'c';
RESET ROLE;
SELECT old_usd, new_usd FROM public.spend_decrease_log ORDER BY at;
\echo 'the formula suggested by the review, NOT (NEW > OLD), is false for a NaN new value because NaN sorts above every number:'
SELECT 'NaN' ::numeric > 5 AS nan_gt_5, NOT ('NaN'::numeric > 5) AS review_formula_for_nan_new, 'NaN'::numeric >= 'Infinity'::numeric AS nan_ge_inf;
\echo '=== T7 what ADD CONSTRAINT holds: ACCESS EXCLUSIVE until the transaction ends, also with NOT VALID then VALIDATE in the same transaction'
BEGIN;
SET LOCAL lock_timeout = '5s';
ALTER TABLE public.spend ADD CONSTRAINT t7_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric) NOT VALID;
SELECT 'after NOT VALID, lock mode:', mode FROM pg_locks WHERE relation = 'public.spend'::regclass AND pid = pg_backend_pid() AND mode LIKE 'AccessExclusive%';
ALTER TABLE public.spend VALIDATE CONSTRAINT t7_ok;
SELECT 'after VALIDATE, lock mode still:', mode FROM pg_locks WHERE relation = 'public.spend'::regclass AND pid = pg_backend_pid() AND mode LIKE 'AccessExclusive%';
ROLLBACK;
