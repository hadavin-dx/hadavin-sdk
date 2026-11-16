\pset pager off
\echo == setup, as the plain migration role emig that owns schema app (no superuser anywhere below)
CREATE ROLE emig LOGIN; CREATE SCHEMA app AUTHORIZATION emig;
SET SESSION AUTHORIZATION emig;
CREATE TABLE app.audit_entries (i int);
CREATE TABLE app.q (i int);
\echo == the file: a deferred constraint trigger whose function defers again and queues a second row; the second row grants
CREATE FUNCTION app.late2() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN
  RAISE NOTICE 'LATE2 fired, i=%', NEW.i;
  IF NEW.i = 1 THEN EXECUTE 'SET CONSTRAINTS ALL DEFERRED'; INSERT INTO app.q VALUES (2);
  ELSE EXECUTE 'GR' || 'ANT SELECT ON app.audit_entries TO PUBLIC'; END IF;
  RETURN NULL; END $f$;
CREATE CONSTRAINT TRIGGER late2_t AFTER INSERT ON app.q DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app.late2();
BEGIN;
INSERT INTO app.q VALUES (1);
\echo == step 5: SET CONSTRAINTS ALL IMMEDIATE (LATE2 i=1 fires here)
SET CONSTRAINTS ALL IMMEDIATE;
\echo == step 6 stand-in: the access list just before COMMIT
SELECT relacl AS before_commit FROM pg_class WHERE oid = 'app.audit_entries'::regclass;
\echo == step 7: COMMIT (LATE2 i=2 fires here)
COMMIT;
SELECT relacl AS after_commit FROM pg_class WHERE oid = 'app.audit_entries'::regclass;
