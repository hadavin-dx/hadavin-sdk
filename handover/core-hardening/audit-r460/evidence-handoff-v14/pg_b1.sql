-- B1: does `CHECK (usd >= 0 AND usd < 'Infinity')` break the INSERT ... ON CONFLICT write shape of
-- store/postgres.py add_spend for a negative delta? Tables copied from 0001_core.sql:87-92 (spend) and the
-- month table of 0003 (same shape). \set VERBOSITY verbose prints SQLSTATE.
\set VERBOSITY verbose
\pset pager off
select version();
CREATE ROLE mig_v14 NOLOGIN; CREATE ROLE rt_v14 NOLOGIN;
GRANT ALL ON SCHEMA public TO mig_v14; GRANT USAGE ON SCHEMA public TO rt_v14;
SET ROLE mig_v14;
CREATE TABLE spend (agent_id text NOT NULL, day date NOT NULL, usd numeric NOT NULL, PRIMARY KEY (agent_id, day));
GRANT SELECT, INSERT, UPDATE ON spend TO rt_v14;
RESET ROLE;
\echo '--- T0 before the CHECK: old shape, reserve +5 then settle delta -3 (the shape store/postgres.py uses)'
SET ROLE rt_v14;
INSERT INTO spend (agent_id, day, usd) VALUES ('a', '2026-11-16', 5) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
INSERT INTO spend (agent_id, day, usd) VALUES ('a', '2026-11-16', -3) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
RESET ROLE;
\echo '--- apply file 1 (the Q34 CHECK plus the Infinity clause)'
SET ROLE mig_v14;
ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
RESET ROLE;
\echo '--- T1 after the CHECK: OLD SHAPE, a delta of -3 on a row that holds 2 (resulting total stays positive)'
SET ROLE rt_v14;
INSERT INTO spend (agent_id, day, usd) VALUES ('a', '2026-11-16', -3) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
\echo '--- T1b OLD SHAPE, a give-back of the exact amount (resulting total 0), the "positive control" of v12 E0-DB-1'
INSERT INTO spend (agent_id, day, usd) VALUES ('a', '2026-11-16', -2) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
\echo '--- T1c OLD SHAPE, positive delta +1 (must still work)'
INSERT INTO spend (agent_id, day, usd) VALUES ('a', '2026-11-16', 1) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
\echo '--- T2 NEW SHAPE: negative delta as UPDATE ... RETURNING (the row holds 3, +2 makes 5, -1 makes 4)'
INSERT INTO spend (agent_id, day, usd) VALUES ('a', '2026-11-16', 2) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
UPDATE spend SET usd = usd + (-1) WHERE agent_id = 'a' AND day = '2026-11-16' RETURNING usd;
\echo '--- T2b NEW SHAPE: give back to exactly 0'
UPDATE spend SET usd = usd + (-4) WHERE agent_id = 'a' AND day = '2026-11-16' RETURNING usd;
\echo '--- T2c NEW SHAPE: a delta that would leave the total below zero is refused by the CHECK (expect 23514)'
UPDATE spend SET usd = usd + (-0.01) WHERE agent_id = 'a' AND day = '2026-11-16' RETURNING usd;
\echo '--- T2d NEW SHAPE: negative delta on a row that does not exist: UPDATE touches 0 rows (the code must treat that as an error)'
UPDATE spend SET usd = usd + (-1) WHERE agent_id = 'nobody' AND day = '2026-11-16' RETURNING usd;
\echo '--- T3 hostile values as the runtime role, INSERT and UPDATE: expect 23514 each'
INSERT INTO spend (agent_id, day, usd) VALUES ('h1', '2026-11-16', -0.01);
INSERT INTO spend (agent_id, day, usd) VALUES ('h2', '2026-11-16', 'NaN');
INSERT INTO spend (agent_id, day, usd) VALUES ('h3', '2026-11-16', 'Infinity');
INSERT INTO spend (agent_id, day, usd) VALUES ('h4', '2026-11-16', '-Infinity');
UPDATE spend SET usd = 'NaN' WHERE agent_id = 'a';
UPDATE spend SET usd = 'Infinity' WHERE agent_id = 'a';
UPDATE spend SET usd = '-Infinity' WHERE agent_id = 'a';
UPDATE spend SET usd = -0.01 WHERE agent_id = 'a';
\echo '--- T3b positive delta shape on a NEW row with +0 (a zero upsert) and UPDATE to exactly 0'
INSERT INTO spend (agent_id, day, usd) VALUES ('z', '2026-11-16', 0) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
UPDATE spend SET usd = 0 WHERE agent_id = 'a' RETURNING usd;
RESET ROLE;
\echo '--- T4 ALTERNATIVE (not chosen): no CHECK, an AFTER trigger on the RESULTING value keeps the old write shape working'
SET ROLE mig_v14;
ALTER TABLE spend DROP CONSTRAINT spend_usd_ok;
CREATE OR REPLACE FUNCTION spend_result_ok() RETURNS trigger LANGUAGE plpgsql AS $f$
BEGIN
  IF NEW.usd < 0 OR NEW.usd >= 'Infinity'::numeric THEN
    RAISE EXCEPTION 'spend total out of range' USING ERRCODE = '23514';
  END IF;
  RETURN NULL;
END $f$;
CREATE TRIGGER spend_result_ok AFTER INSERT OR UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_result_ok();
RESET ROLE;
DELETE FROM spend;
SET ROLE rt_v14;
INSERT INTO spend (agent_id, day, usd) VALUES ('t', '2026-11-16', 5) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
\echo 'T4a trigger variant: old shape, delta -3 on a row of 5 (expect 2, no error)'
INSERT INTO spend (agent_id, day, usd) VALUES ('t', '2026-11-16', -3) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
\echo 'T4b trigger variant: old shape, delta -3 on a row of 2 (resulting -1: expect 23514)'
INSERT INTO spend (agent_id, day, usd) VALUES ('t', '2026-11-16', -3) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
\echo 'T4c trigger variant: negative first insert for a NEW key (no conflict): expect 23514'
INSERT INTO spend (agent_id, day, usd) VALUES ('new', '2026-11-16', -3) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd;
\echo 'T4d trigger variant: NaN and Infinity by UPDATE: expect 23514'
UPDATE spend SET usd = 'NaN' WHERE agent_id = 't';
UPDATE spend SET usd = 'Infinity' WHERE agent_id = 't';
RESET ROLE;
