-- Pre-flight for roles.sql. Run as an admin. READ-ONLY: it changes nothing.
-- roles.sql REVOKEs privileges from PUBLIC, which changes access for EVERY login in this database. This script lists
-- every other non-superuser LOGIN role that holds CONNECT/TEMP on the database or USAGE/CREATE on the schemas public,
-- shop, analytics ONLY through PUBLIC (no grant of its own, not the owner), i.e. exactly the logins that would lose
-- access. Lines are "role | object | privilege | via". It then lists, for information only (they never block):
-- functions in those schemas that PUBLIC can EXECUTE (the read-only login could call them; roles.sql does not
-- revoke them) and every pg_default_acl entry (privileges that future objects get, which may re-open access).
-- Usage: psql -d <db> -v ON_ERROR_STOP=1 -f preflight_roles.sql
\if :{?ro_role}
\else
  \set ro_role askdata_ro
\endif
WITH me AS (
    SELECT r.oid, r.rolname FROM pg_roles r
    WHERE r.rolcanlogin AND NOT r.rolsuper AND r.rolname <> :'ro_role' AND left(r.rolname, 3) <> 'pg_'
), objs AS (
    SELECT 'database ' || d.datname AS object, d.datdba AS owner, p.priv,
           COALESCE(d.datacl, acldefault('d', d.datdba)) AS acl
    FROM pg_database d, (VALUES ('CONNECT'), ('TEMPORARY')) p(priv)
    WHERE d.datname = current_database()
    UNION ALL
    SELECT 'schema ' || n.nspname, n.nspowner, p.priv, COALESCE(n.nspacl, acldefault('n', n.nspowner))
    FROM pg_namespace n, (VALUES ('USAGE'), ('CREATE')) p(priv)
    WHERE n.nspname IN ('public', 'shop', 'analytics')
), loss AS (
    SELECT me.rolname AS role, o.object, o.priv AS privilege, 'PUBLIC' AS via
    FROM me JOIN objs o ON o.owner <> me.oid
    WHERE EXISTS (SELECT 1 FROM aclexplode(o.acl) a WHERE a.grantee = 0 AND a.privilege_type = o.priv)
      AND NOT EXISTS (SELECT 1 FROM aclexplode(o.acl) a WHERE a.grantee = me.oid AND a.privilege_type = o.priv)
)
SELECT count(*) > 0 AS has_loss, count(*) AS loss_count,
       COALESCE(string_agg(role || ' | ' || object || ' | ' || privilege || ' | ' || via, E'\n'
                           ORDER BY role, object, privilege), '(none)') AS loss_list
FROM loss \gset
\echo preflight: :loss_count privilege(s) would be lost through PUBLIC (role | object | privilege | via):
\echo :loss_list
SELECT count(*) AS fn_count,
       COALESCE(string_agg(n.nspname || '.' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')',
                           E'\n' ORDER BY n.nspname, p.proname, p.oid), '(none)') AS fn_list
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname IN ('public', 'shop', 'analytics')
  AND EXISTS (SELECT 1 FROM aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a
              WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE') \gset
\echo preflight: :fn_count function(s) in public/shop/analytics are executable by PUBLIC (info, not a block):
\echo :fn_list
SELECT count(*) AS dacl_count,
       COALESCE(string_agg(pg_get_userbyid(d.defaclrole) || ' | ' || COALESCE(n.nspname, '(all schemas)') || ' | '
                           || d.defaclobjtype::text || ' | ' || d.defaclacl::text, E'\n'
                           ORDER BY pg_get_userbyid(d.defaclrole), n.nspname, d.defaclobjtype), '(none)') AS dacl_list
FROM pg_default_acl d LEFT JOIN pg_namespace n ON n.oid = d.defaclnamespace \gset
\echo preflight: :dacl_count default-privilege entr(y/ies) in pg_default_acl (role | schema | object type | acl; info):
\echo :dacl_list
