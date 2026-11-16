\pset pager off
\set ON_ERROR_STOP 0
\echo == setup: database owned by postgres; migration role mig owns schema app and table app.t; boss holds SELECT WITH GRANT OPTION
CREATE ROLE mig LOGIN; CREATE ROLE boss; CREATE ROLE rt; CREATE ROLE cr CREATEROLE;
CREATE SCHEMA app AUTHORIZATION mig;
SET ROLE mig;
CREATE TABLE app.t (i int, secret text);
GRANT USAGE ON SCHEMA app TO boss, rt;
GRANT SELECT ON app.t TO boss WITH GRANT OPTION;
GRANT SELECT, INSERT ON app.t TO rt;          -- grantor mig (the owner)
RESET ROLE;
SET ROLE boss;
GRANT SELECT ON app.t TO rt;                  -- grantor boss
GRANT SELECT (secret) ON app.t TO rt;         -- column right, grantor boss
RESET ROLE;
\echo == (a1) access list before
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
SELECT attname, attacl FROM pg_attribute WHERE attrelid = 'app.t'::regclass AND attacl IS NOT NULL;
\echo == (a2) step 4 as the owner mig: REVOKE ALL ON TABLE app.t FROM rt
SET ROLE mig; REVOKE ALL ON TABLE app.t FROM rt; RESET ROLE;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
SELECT attname, attacl FROM pg_attribute WHERE attrelid = 'app.t'::regclass AND attacl IS NOT NULL;
SET SESSION AUTHORIZATION rt; SELECT count(*) AS rt_can_still_read FROM app.t; RESET SESSION AUTHORIZATION;
\echo == (a3) as superuser: REVOKE SELECT ON TABLE app.t FROM rt (superuser acts as the owner)
REVOKE SELECT ON TABLE app.t FROM rt;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
\echo == (a4) as superuser: REVOKE SELECT ON TABLE app.t FROM rt GRANTED BY boss
REVOKE SELECT ON TABLE app.t FROM rt GRANTED BY boss;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
\echo == (a5) as superuser: REVOKE GRANT OPTION FOR SELECT ON app.t FROM boss CASCADE (the dependent entries go)
REVOKE GRANT OPTION FOR SELECT ON TABLE app.t FROM boss CASCADE;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
SELECT attname, attacl FROM pg_attribute WHERE attrelid = 'app.t'::regclass AND attacl IS NOT NULL;
\echo == (a6) as boss itself: SET ROLE boss; REVOKE ... FROM rt (works where boss still holds the option)
SET ROLE mig; GRANT SELECT ON app.t TO boss WITH GRANT OPTION; RESET ROLE;
SET ROLE boss; GRANT SELECT ON app.t TO rt; RESET ROLE;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
SET ROLE boss; REVOKE SELECT ON app.t FROM rt; RESET ROLE;
SELECT relacl AS after_revoke_as_boss FROM pg_class WHERE oid = 'app.t'::regclass;
\echo == (a7) plain REVOKE SELECT ... FROM boss without CASCADE when a dependent entry exists
SET ROLE boss; GRANT SELECT ON app.t TO rt; RESET ROLE;
REVOKE SELECT ON app.t FROM boss;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
REVOKE SELECT ON app.t FROM boss CASCADE;
SELECT relacl AS after_cascade FROM pg_class WHERE oid = 'app.t'::regclass;
\echo == (a8) memberships: cr (CREATEROLE) creates grp and grants it to rt; superuser revokes
SET ROLE cr; CREATE ROLE grp; GRANT grp TO rt; RESET ROLE;
SELECT pg_get_userbyid(roleid) AS role, pg_get_userbyid(member) AS member, pg_get_userbyid(grantor) AS grantor, admin_option, inherit_option, set_option FROM pg_auth_members WHERE roleid IN ('grp'::regrole) ORDER BY 2;
REVOKE grp FROM rt;
SELECT count(*) AS rt_still_member FROM pg_auth_members WHERE roleid = 'grp'::regrole AND member = 'rt'::regrole;
REVOKE grp FROM rt GRANTED BY cr;
SELECT count(*) AS after_granted_by_cr FROM pg_auth_members WHERE roleid = 'grp'::regrole AND member = 'rt'::regrole;
\echo == (a9) membership granted by the bootstrap superuser: plain REVOKE works
GRANT grp TO rt;
SELECT pg_get_userbyid(grantor) AS grantor FROM pg_auth_members WHERE roleid = 'grp'::regrole AND member = 'rt'::regrole;
REVOKE grp FROM rt;
SELECT count(*) AS after_plain_revoke FROM pg_auth_members WHERE roleid = 'grp'::regrole AND member = 'rt'::regrole;
\echo == (a10) two grants of the same membership by two grantors: one REVOKE leaves the other
GRANT grp TO rt; SET ROLE cr; GRANT grp TO rt; RESET ROLE;
SELECT pg_get_userbyid(grantor) AS grantor FROM pg_auth_members WHERE roleid = 'grp'::regrole AND member = 'rt'::regrole ORDER BY 1;
REVOKE grp FROM rt;
SELECT pg_get_userbyid(grantor) AS left_grantor FROM pg_auth_members WHERE roleid = 'grp'::regrole AND member = 'rt'::regrole;
\echo == (a11) object right granted by a superuser that is not the owner: grantor recorded as the owner
GRANT UPDATE ON app.t TO rt;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
\echo == (a12) GRANTED BY for an object right naming a role that is not the current user
REVOKE UPDATE ON app.t FROM rt GRANTED BY mig;
SELECT relacl FROM pg_class WHERE oid = 'app.t'::regclass;
