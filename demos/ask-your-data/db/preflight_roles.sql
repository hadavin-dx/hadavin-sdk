-- Pre-flight for roles.sql. Run as an admin. READ-ONLY: it changes nothing.
-- roles.sql REVOKEs privileges from PUBLIC, which changes access for EVERY login in this database. This script lists
-- every other non-superuser LOGIN role that holds CONNECT/TEMP on the database or USAGE/CREATE on the schemas public,
-- shop, analytics ONLY through PUBLIC (no grant of its own, not the owner), i.e. exactly the logins that would lose
-- access. Lines are "role | object | privilege | via". (Function EXECUTE listing: phase P1.)
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
