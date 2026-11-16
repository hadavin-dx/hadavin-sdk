\pset pager off
\echo == (c1) a fresh database: the public schema owner and access list
SELECT nspname, pg_get_userbyid(nspowner) AS owner, nspacl FROM pg_namespace WHERE nspname = 'public';
SELECT a.grantee, CASE a.grantee WHEN 0 THEN '(everyone)' ELSE pg_get_userbyid(a.grantee) END AS grantee_name, a.privilege_type, pg_get_userbyid(a.grantor) AS grantor
  FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a WHERE n.nspname = 'public';
\echo == (c2) acldefault for a schema (what a NULL nspacl means): nothing for everyone
SELECT acldefault('n', 'pg_database_owner'::regrole);
\echo == (c3) a database owned by a plain role pc_mig: is pc_mig a member of pg_database_owner and of the public owner
CREATE ROLE pc_mig LOGIN;
