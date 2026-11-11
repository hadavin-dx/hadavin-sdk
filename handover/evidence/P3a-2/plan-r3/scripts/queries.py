"""Final query texts of errata rev 2 (pasted verbatim into the ticket, section 3.2). Run as a plain role."""
FAMILY_CTE = """fam(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(family)s::text[])
  UNION
  SELECT m.roleid FROM fam f JOIN pg_catalog.pg_auth_members m ON m.member = f.role)"""
SUBJ_CTE = """subj(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])
  UNION
  SELECT m.roleid FROM subj s JOIN pg_catalog.pg_auth_members m ON m.member = s.role)"""

Q1 = """WITH RECURSIVE closure(root, role, at_once) AS (
  SELECT r.oid, r.oid, true FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(roles)s::text[])
  UNION
  SELECT c.root, m.roleid, c.at_once AND m.inherit_option
    FROM closure c JOIN pg_catalog.pg_auth_members m ON m.member = c.role)
SELECT pg_catalog.pg_get_userbyid(c.root) AS start_role, r.rolname AS member_of, bool_or(c.at_once) AS uses_rights_at_once,
       r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls, r.rolreplication
  FROM closure c JOIN pg_catalog.pg_roles r ON r.oid = c.role
 GROUP BY c.root, r.rolname, r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls, r.rolreplication
 ORDER BY 1, 2"""

Q1B = """SELECT pg_catalog.pg_get_userbyid(m.member) AS member, pg_catalog.pg_get_userbyid(m.roleid) AS role_name,
       pg_catalog.pg_get_userbyid(m.grantor) AS grantor, m.admin_option, m.inherit_option, m.set_option
  FROM pg_catalog.pg_auth_members m
 WHERE m.member IN (SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(roles)s::text[]))
 ORDER BY 1, 2, 3"""

Q2 = """WITH RECURSIVE """ + SUBJ_CTE + """,
""" + FAMILY_CTE + """,
named(role) AS (SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])),
obj(kind, relkind, cls, oid, schema, name, sub, owner, definer, row_type, acl) AS (
  SELECT CASE c.relkind WHEN 'S' THEN 'sequence' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized view'
                        WHEN 'f' THEN 'foreign table' WHEN 'r' THEN 'table' WHEN 'p' THEN 'table'
                        ELSE 'relation of an unread kind' END,
         c.relkind::text, 'pg_catalog.pg_class'::pg_catalog.regclass, c.oid, n.nspname, c.relname, '', c.relowner, false, false,
         coalesce(c.relacl, pg_catalog.acldefault(CASE c.relkind WHEN 'S' THEN 's' ELSE 'r' END::"char", c.relowner))
    FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname !~ '^pg_(toast|temp_)' AND (c.relkind IN ('r','p','v','m','S','f') OR c.relacl IS NOT NULL)
  UNION ALL
  SELECT 'column', c.relkind::text, 'pg_catalog.pg_class'::pg_catalog.regclass, c.oid, n.nspname, c.relname, a.attname, c.relowner, false, false, a.attacl
    FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid = a.attrelid JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
   WHERE a.attacl IS NOT NULL AND NOT a.attisdropped AND n.nspname !~ '^pg_(toast|temp_)'
  UNION ALL
  SELECT CASE p.prokind WHEN 'p' THEN 'procedure' WHEN 'a' THEN 'aggregate' ELSE 'function' END, '',
         'pg_catalog.pg_proc'::pg_catalog.regclass, p.oid, n.nspname, p.proname,
         pg_catalog.pg_get_function_identity_arguments(p.oid), p.proowner, p.prosecdef, false,
         coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))
    FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname !~ '^pg_(toast|temp_)'
  UNION ALL
  SELECT 'schema', '', 'pg_catalog.pg_namespace'::pg_catalog.regclass, n.oid, n.nspname, '', '', n.nspowner, false, false,
         coalesce(n.nspacl, pg_catalog.acldefault('n', n.nspowner))
    FROM pg_catalog.pg_namespace n WHERE n.nspname !~ '^pg_(toast|temp_)'
  UNION ALL
  SELECT CASE t.typtype WHEN 'd' THEN 'domain' ELSE 'type' END, coalesce(rc.relkind::text, ''),
         'pg_catalog.pg_type'::pg_catalog.regclass, t.oid, n.nspname, t.typname, '', t.typowner, false,
         (t.typtype = 'c' AND t.typrelid <> 0 AND rc.relkind <> 'c'),
         coalesce(t.typacl, pg_catalog.acldefault('T', t.typowner))
    FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    LEFT JOIN pg_catalog.pg_class rc ON rc.oid = t.typrelid
   WHERE n.nspname !~ '^pg_(toast|temp_)' AND NOT (t.typelem <> 0 AND t.typcategory = 'A')
  UNION ALL
  SELECT 'database', '', 'pg_catalog.pg_database'::pg_catalog.regclass, d.oid, '', d.datname, '', d.datdba, false, false,
         coalesce(d.datacl, pg_catalog.acldefault('d', d.datdba))
    FROM pg_catalog.pg_database d WHERE d.datname = pg_catalog.current_database()
  UNION ALL
  SELECT 'foreign-data wrapper', '', 'pg_catalog.pg_foreign_data_wrapper'::pg_catalog.regclass, w.oid, '', w.fdwname, '', w.fdwowner, false, false,
         coalesce(w.fdwacl, pg_catalog.acldefault('F', w.fdwowner)) FROM pg_catalog.pg_foreign_data_wrapper w
  UNION ALL
  SELECT 'foreign server', '', 'pg_catalog.pg_foreign_server'::pg_catalog.regclass, s.oid, '', s.srvname, '', s.srvowner, false, false,
         coalesce(s.srvacl, pg_catalog.acldefault('S', s.srvowner)) FROM pg_catalog.pg_foreign_server s
  UNION ALL
  SELECT 'language', '', 'pg_catalog.pg_language'::pg_catalog.regclass, l.oid, '', l.lanname, '', l.lanowner, false, false,
         coalesce(l.lanacl, pg_catalog.acldefault('l', l.lanowner)) FROM pg_catalog.pg_language l
  UNION ALL
  SELECT 'large object', '', 'pg_catalog.pg_largeobject'::pg_catalog.regclass, m.oid, '', m.oid::text, '', m.lomowner, false, false,
         coalesce(m.lomacl, pg_catalog.acldefault('L', m.lomowner)) FROM pg_catalog.pg_largeobject_metadata m
  UNION ALL
  SELECT 'parameter', '', 'pg_catalog.pg_parameter_acl'::pg_catalog.regclass, a.oid, '', a.parname, '', 0::pg_catalog.oid, false, false, a.paracl
    FROM pg_catalog.pg_parameter_acl a WHERE a.paracl IS NOT NULL
  UNION ALL
  SELECT 'tablespace', '', 'pg_catalog.pg_tablespace'::pg_catalog.regclass, s.oid, '', s.spcname, '', s.spcowner, false, false,
         coalesce(s.spcacl, pg_catalog.acldefault('t', s.spcowner)) FROM pg_catalog.pg_tablespace s),
items AS (
  SELECT o.*, (o.schema IN ('pg_catalog', 'information_schema')) AS system, a.grantee, a.grantor, a.privilege_type, a.is_grantable
    FROM obj o CROSS JOIN LATERAL pg_catalog.aclexplode(o.acl) a)
SELECT i.kind, i.relkind, i.schema, i.system, i.name, i.sub, pg_catalog.pg_get_userbyid(i.owner) AS owner,
       (i.owner IN (SELECT role FROM fam)) AS family_owned, i.definer, i.row_type,
       xe.extname AS extension, pg_catalog.pg_get_userbyid(xe.extowner) AS extension_owner,
       (xe.extowner IN (SELECT role FROM fam)) AS extension_family_owned,
       CASE i.grantee WHEN 0 THEN NULL ELSE pg_catalog.pg_get_userbyid(i.grantee) END AS grantee,
       (i.grantee IN (SELECT role FROM subj)) AS grantee_is_subject, (i.grantee IN (SELECT role FROM named)) AS grantee_is_named,
       (i.grantee = i.owner) AS owner_item, i.privilege_type, i.is_grantable,
       pg_catalog.pg_get_userbyid(i.grantor) AS grantor, (i.grantor = i.owner) AS grantor_is_owner
  FROM items i
  LEFT JOIN pg_catalog.pg_depend xd ON xd.classid = i.cls AND xd.objid = i.oid AND xd.objsubid = 0 AND xd.deptype = 'e'
       AND i.kind <> 'column'
  LEFT JOIN pg_catalog.pg_extension xe ON xe.oid = xd.refobjid
 WHERE (i.grantee IN (SELECT role FROM subj)
        AND (NOT i.system OR (i.grantee IN (SELECT role FROM named)
                               OR pg_catalog.pg_get_userbyid(i.grantee) !~ '^pg_')))
    OR (NOT i.system AND i.grantee = 0
        AND (i.kind NOT IN ('function', 'procedure', 'aggregate', 'type', 'domain', 'language')
             OR i.owner IN (SELECT role FROM fam) OR i.definer))
    OR (NOT i.system AND i.schema = %(schema)s)
 ORDER BY 1, 3, 5, 6, 14, 18"""

Q3 = """WITH RECURSIVE """ + SUBJ_CTE + """
SELECT d.deptype::text, d.classid::pg_catalog.regclass::text AS catalog, d.objid, d.objsubid,
       pg_catalog.pg_get_userbyid(d.refobjid) AS role,
       pg_catalog.pg_describe_object(d.classid, d.objid, d.objsubid) AS described,
       (d.classid = 'pg_catalog.pg_class'::pg_catalog.regclass AND EXISTS (
          SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
           WHERE c.oid = d.objid AND n.nspname ~ '^pg_(toast_)?temp_')) AS temporary
  FROM pg_catalog.pg_shdepend d
 WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass AND d.refobjid IN (SELECT role FROM subj)
   AND (d.dbid = (SELECT oid FROM pg_catalog.pg_database WHERE datname = pg_catalog.current_database())
        OR (d.dbid = 0 AND (d.classid <> 'pg_catalog.pg_database'::pg_catalog.regclass
                             OR d.objid = (SELECT oid FROM pg_catalog.pg_database WHERE datname = pg_catalog.current_database()))))
 ORDER BY 5, 1, 2, 6"""

Q4 = """WITH RECURSIVE """ + SUBJ_CTE + """,
""" + FAMILY_CTE + """
SELECT d.defaclobjtype::text AS kind, n.nspname AS schema, pg_catalog.pg_get_userbyid(d.defaclrole) AS set_for,
       (d.defaclrole IN (SELECT role FROM fam)) AS set_for_family,
       CASE a.grantee WHEN 0 THEN NULL ELSE pg_catalog.pg_get_userbyid(a.grantee) END AS grantee,
       (a.grantee IN (SELECT role FROM subj)) AS grantee_is_subject, a.privilege_type, a.is_grantable
  FROM pg_catalog.pg_default_acl d LEFT JOIN pg_catalog.pg_namespace n ON n.oid = d.defaclnamespace
 CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a
 WHERE a.grantee IN (SELECT role FROM subj) OR a.grantee = 0 OR d.defaclrole IN (SELECT role FROM fam)
 ORDER BY 1, 2, 3, 5, 7"""

STEP4 = """WITH RECURSIVE """ + FAMILY_CTE + """
SELECT p.oid::pg_catalog.regprocedure::text AS shown, n.nspname, p.proname,
       pg_catalog.pg_get_function_identity_arguments(p.oid) AS args, p.prokind::text
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
 WHERE n.nspname = %(schema)s AND p.proowner IN (SELECT role FROM fam) AND p.proname = ANY(%(managed)s::text[])
   AND EXISTS (SELECT 1 FROM pg_catalog.aclexplode(coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))) a
                WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE')
 ORDER BY 2, 3, 4"""

# rev 3: Q0 and the version read, exactly as ticket rev 2 section 3.2 and 3.5 print them
Q0 = """SELECT c.relname || '.' || a.attname
  FROM pg_catalog.pg_attribute a
  JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
  JOIN pg_catalog.pg_namespace tn ON tn.oid = t.typnamespace
 WHERE n.nspname = 'pg_catalog' AND c.relkind IN ('r','v') AND tn.nspname = 'pg_catalog'
   AND t.typname = '_aclitem' AND a.attnum > 0 AND NOT a.attisdropped ORDER BY 1"""
VERSION = "SELECT pg_catalog.current_setting('server_version_num')::int"
