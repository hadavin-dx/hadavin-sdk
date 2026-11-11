\pset pager off
\echo == setup: plain role xmig with CREATE on the database (no superuser)
CREATE ROLE xmig LOGIN; GRANT CREATE ON DATABASE px TO xmig;
SELECT rolsuper FROM pg_roles WHERE rolname = 'xmig';
SET SESSION AUTHORIZATION xmig;
SELECT current_user, session_user;
CREATE EXTENSION citext;
SELECT extname, pg_catalog.pg_get_userbyid(extowner) AS extension_owner FROM pg_catalog.pg_extension WHERE extname = 'citext';
SELECT pg_catalog.pg_get_userbyid(p.proowner) AS member_function_owner, count(*) FROM pg_catalog.pg_depend d JOIN pg_catalog.pg_proc p ON p.oid = d.objid
 WHERE d.refobjid = (SELECT oid FROM pg_catalog.pg_extension WHERE extname = 'citext') AND d.deptype = 'e' AND d.classid = 'pg_catalog.pg_proc'::regclass GROUP BY 1;
