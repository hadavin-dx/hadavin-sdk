\pset pager off
\echo == (a13) the column entry rt=r/boss left after (a5); boss holds no grant option now
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
SELECT attname, attacl FROM pg_attribute WHERE attrelid = 'app.t'::regclass AND attacl IS NOT NULL;
SET SESSION AUTHORIZATION rt; SELECT secret FROM app.t; RESET SESSION AUTHORIZATION;
\echo == (a14) superuser: REVOKE SELECT (secret) ON app.t FROM rt  (acts as the owner)
REVOKE SELECT (secret) ON app.t FROM rt;
SELECT attname, attacl FROM pg_attribute WHERE attrelid = 'app.t'::regclass AND attacl IS NOT NULL;
\echo == (a15) SET ROLE boss; REVOKE SELECT (secret) ON app.t FROM rt; RESET ROLE
SET ROLE boss; REVOKE SELECT (secret) ON app.t FROM rt; RESET ROLE;
SELECT attname, attacl FROM pg_attribute WHERE attrelid = 'app.t'::regclass AND attacl IS NOT NULL;
\echo == (a16) table-level entry granted by boss: SET ROLE boss form removes it (grantor-first order)
SET ROLE mig; GRANT SELECT ON app.t TO boss WITH GRANT OPTION; RESET ROLE;
SET ROLE boss; GRANT SELECT ON app.t TO rt; RESET ROLE;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
SET ROLE boss; REVOKE SELECT ON TABLE app.t FROM rt; RESET ROLE;
SELECT relacl AS after FROM pg_class WHERE oid = 'app.t'::regclass;
