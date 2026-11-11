\pset pager off
\echo == setup: runtime role hrt is a member of pg_monitor (granted by an administrator)
CREATE ROLE hrt; GRANT pg_monitor TO hrt;
\echo == (h1) the closure of hrt (Q1 shape)
WITH RECURSIVE s(role) AS (SELECT 'hrt'::regrole::oid UNION SELECT m.roleid FROM s JOIN pg_catalog.pg_auth_members m ON m.member = s.role)
SELECT pg_catalog.pg_get_userbyid(role) AS subject FROM s ORDER BY 1;
\echo == (h2) what ticket rev 1 (3.1 change (a) + S5) would read in the two system schemas: items whose grantee is a subject
WITH RECURSIVE s(role) AS (SELECT 'hrt'::regrole::oid UNION SELECT m.roleid FROM s JOIN pg_catalog.pg_auth_members m ON m.member = s.role),
items AS (
  SELECT 'relation' AS kind, n.nspname, c.relname AS name, a.grantee, a.privilege_type FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
    CROSS JOIN LATERAL pg_catalog.aclexplode(c.relacl) a WHERE n.nspname IN ('pg_catalog','information_schema')
  UNION ALL
  SELECT 'function', n.nspname, p.proname, a.grantee, a.privilege_type FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) a WHERE n.nspname IN ('pg_catalog','information_schema')
  UNION ALL
  SELECT 'column', n.nspname, c.relname || '.' || t.attname, a.grantee, a.privilege_type FROM pg_catalog.pg_attribute t JOIN pg_catalog.pg_class c ON c.oid = t.attrelid
    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace CROSS JOIN LATERAL pg_catalog.aclexplode(t.attacl) a WHERE n.nspname IN ('pg_catalog','information_schema') AND t.attacl IS NOT NULL)
SELECT pg_catalog.pg_get_userbyid(i.grantee) AS grantee, i.kind, count(*) AS problem_lines_rev1_would_print
  FROM items i WHERE i.grantee IN (SELECT role FROM s) GROUP BY 1, 2 ORDER BY 1, 2;
\echo == (h3) three examples of the REVOKE that rev 1 would print and its 4.2 test would run as a superuser
WITH RECURSIVE s(role) AS (SELECT 'hrt'::regrole::oid UNION SELECT m.roleid FROM s JOIN pg_catalog.pg_auth_members m ON m.member = s.role)
SELECT format('REVOKE %s ON FUNCTION %I.%I(%s) FROM %I;', a.privilege_type, n.nspname, p.proname, pg_catalog.pg_get_function_identity_arguments(p.oid), pg_catalog.pg_get_userbyid(a.grantee))
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) a
 WHERE n.nspname = 'pg_catalog' AND a.grantee IN (SELECT role FROM s) ORDER BY 1 LIMIT 3;
\echo == (h4) the single fix the errata prints: the membership line only
SELECT format('REVOKE %I FROM %I GRANTED BY %I;', pg_catalog.pg_get_userbyid(m.roleid), pg_catalog.pg_get_userbyid(m.member), pg_catalog.pg_get_userbyid(m.grantor))
  FROM pg_catalog.pg_auth_members m WHERE m.member = 'hrt'::regrole;
