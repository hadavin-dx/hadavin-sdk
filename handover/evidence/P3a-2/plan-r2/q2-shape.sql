SELECT count(*) FROM (
 SELECT a.* FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl, pg_catalog.acldefault('r', c.relowner))) a
 UNION ALL SELECT a.* FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))) a
 UNION ALL SELECT a.* FROM pg_catalog.pg_type t CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(t.typacl, pg_catalog.acldefault('T', t.typowner))) a
 UNION ALL SELECT a.* FROM pg_catalog.pg_namespace n CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(n.nspacl, pg_catalog.acldefault('n', n.nspowner))) a) x
