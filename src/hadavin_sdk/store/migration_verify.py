"""`verify`: judge the state the database is in NOW against the grant map (ticket P3a-2, plan rev 3, section 3).

`verify` replaces the question "what changed during this run?" with "what is true now?". It reads who may do what in the
database (the access lists of the 13 kinds of object that carry one, the memberships between roles, the owners and the
default rights) with eight statements, and compares that with the grant map. It only reads; it never changes anything.

Two layers, so that a test can pin each: `_read` runs the queries and returns plain rows (`Rows`); `_judge` is a pure
function that turns rows into `Problem` records. Every rule lives in `_judge`; the clause letters (S1-S8, O1-O8, D1-D4,
E1) are the clauses of section 3.3 of the ticket.

Words used here. The *named roles* are the runtime, portal and purge roles given on the command line. A *subject* is a
named role or any role it is a member of, directly or through others. *Everyone* is PostgreSQL's PUBLIC, the rights
every role has. The *family* is the migration role, the login when it differs, and every role either belongs to.

An object whose access list is EMPTY (a file revoked every right, from its owner too) has no row in `aclexplode`. Q2 keeps
such an object as one row with no right (`privilege_type` is null) so that its owner (rule O8, in the schema of the run) and
its SECURITY DEFINER flag (rule O4) are still judged; `_judge` never reads that row as a right, and never as a right for everyone. (The probe on
the code before this change showed that such an object was invisible to O4 and O8.)

What `_judge` checks for a SECURITY DEFINER function: that its schema, name and argument types are on the reviewed list
(O4), who owns it (O8: a managed object, and the schema of the run, must be owned by a role of the family; judged in the
schema of the run only), and who may EXECUTE it (a named role: always a right; everyone: refused
unless reviewed). It does not read the function's body or its `search_path` setting.

A login that differs from the migration role: `_judge` skips only a grantee that is the migration role itself. When the
login holds its own entry on an object of the package, `_judge` reports it as `other_grantee`: a refusal that a person can
recognise and resolve (a false refusal, never a missed excess right).

This module does not decide who is the migration role: the caller passes the names in. It never reads the current role
or the current schema of the session (with the search path pinned they would answer the wrong thing).
"""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import postgres as pg  # the only door to the database driver (lock-in rule)
from hadavin_sdk.store.migration_numbers import _label, escape_name

if TYPE_CHECKING:
    from hadavin_sdk.store.migrate import Grant

# --- the queries (ticket 3.2, copied without rewording; each ran on 16.15 as a plain login) ----------------------------

Q0 = """
SELECT c.relname || '.' || a.attname
  FROM pg_catalog.pg_attribute a
  JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
  JOIN pg_catalog.pg_namespace tn ON tn.oid = t.typnamespace
 WHERE n.nspname = 'pg_catalog' AND c.relkind IN ('r','v') AND tn.nspname = 'pg_catalog'
   AND t.typname = '_aclitem' AND a.attnum > 0 AND NOT a.attisdropped ORDER BY 1;
"""

V2_SQL = (
    "SELECT pg_catalog.current_setting('server_version_num')::int, pg_catalog.pg_get_userbyid(d.datdba) "
    "FROM pg_catalog.pg_database d WHERE d.datname = pg_catalog.current_database()"
)

Q1 = """
WITH RECURSIVE closure(root, role, at_once) AS (
  SELECT r.oid, r.oid, true FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(roles)s::text[])
  UNION
  SELECT c.root, m.roleid, c.at_once AND m.inherit_option
    FROM closure c JOIN pg_catalog.pg_auth_members m ON m.member = c.role)
SELECT pg_catalog.pg_get_userbyid(c.root) AS start_role, r.rolname AS member_of, bool_or(c.at_once) AS uses_rights_at_once,
       r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls, r.rolreplication
  FROM closure c JOIN pg_catalog.pg_roles r ON r.oid = c.role
 GROUP BY c.root, r.rolname, r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls, r.rolreplication
 ORDER BY 1, 2;
"""

Q1B = """
SELECT pg_catalog.pg_get_userbyid(m.member) AS member, pg_catalog.pg_get_userbyid(m.roleid) AS role_name,
       pg_catalog.pg_get_userbyid(m.grantor) AS grantor, m.admin_option, m.inherit_option, m.set_option
  FROM pg_catalog.pg_auth_members m
 WHERE m.member IN (SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(roles)s::text[]))
 ORDER BY 1, 2, 3;
"""

Q2 = """
WITH RECURSIVE subj(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])
  UNION
  SELECT m.roleid FROM subj s JOIN pg_catalog.pg_auth_members m ON m.member = s.role),
fam(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(family)s::text[])
  UNION
  SELECT m.roleid FROM fam f JOIN pg_catalog.pg_auth_members m ON m.member = f.role),
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
    FROM obj o LEFT JOIN LATERAL pg_catalog.aclexplode(o.acl) a ON true)
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
 ORDER BY 1, 3, 5, 6, 14, 18;
"""

Q3 = """
WITH RECURSIVE subj(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])
  UNION
  SELECT m.roleid FROM subj s JOIN pg_catalog.pg_auth_members m ON m.member = s.role)
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
 ORDER BY 5, 1, 2, 6;
"""

Q4 = """
WITH RECURSIVE subj(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])
  UNION
  SELECT m.roleid FROM subj s JOIN pg_catalog.pg_auth_members m ON m.member = s.role),
fam(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(family)s::text[])
  UNION
  SELECT m.roleid FROM fam f JOIN pg_catalog.pg_auth_members m ON m.member = f.role)
SELECT d.defaclobjtype::text AS kind, n.nspname AS schema, pg_catalog.pg_get_userbyid(d.defaclrole) AS set_for,
       (d.defaclrole IN (SELECT role FROM fam)) AS set_for_family,
       CASE a.grantee WHEN 0 THEN NULL ELSE pg_catalog.pg_get_userbyid(a.grantee) END AS grantee,
       (a.grantee IN (SELECT role FROM subj)) AS grantee_is_subject, a.privilege_type, a.is_grantable
  FROM pg_catalog.pg_default_acl d LEFT JOIN pg_catalog.pg_namespace n ON n.oid = d.defaclnamespace
 CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a
 WHERE a.grantee IN (SELECT role FROM subj) OR a.grantee = 0 OR d.defaclrole IN (SELECT role FROM fam)
 ORDER BY 1, 2, 3, 5, 7;
"""

# The functions whose default EXECUTE for everyone the run removes (step 4 of `migrate`): the functions the files name
# in the schema of the run, and the ones a file wrote with another schema before the dot (`other_schemas`, `other_names`
# are two lists of the same length).
STEP4_SQL = """
WITH RECURSIVE fam(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(family)s::text[])
  UNION
  SELECT m.roleid FROM fam f JOIN pg_catalog.pg_auth_members m ON m.member = f.role)
SELECT p.oid::pg_catalog.regprocedure::text AS shown, n.nspname, p.proname,
       pg_catalog.pg_get_function_identity_arguments(p.oid) AS args, p.prokind::text
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
 WHERE p.proowner IN (SELECT role FROM fam)
   AND ((n.nspname = %(schema)s AND p.proname = ANY(%(managed)s::text[]))
        OR (n.nspname, p.proname) IN (SELECT * FROM ROWS FROM (pg_catalog.unnest(%(other_schemas)s::text[]), pg_catalog.unnest(%(other_names)s::text[]))))
   AND EXISTS (SELECT 1 FROM pg_catalog.aclexplode(coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))) a
                WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE')
 ORDER BY 2, 3, 4;
"""

# --- the closed lists -------------------------------------------------------------------------------------------------

# One kind of problem per lettered clause of section 3.3 (the closed tuple; a repository test pins it).
PROBLEM_KINDS = (
    "flag",
    "built_in_role",
    "can_act_as_family",
    "named_roles_overlap",
    "owns",
    "right",
    "grant_option",
    "definer_callable",
    "unread_catalog",
    "unread_relation_kind",
    "foreign_owner",
    "other_grantee",
    "everyone",
    "object_grant_option",
    "definer_unreviewed",
    "schema_right",
    "default_for_named",
    "default_for_everyone",
    "default_for_other",
    "default_unknown_kind",
    "missing_schema_usage",
)

# The 14 columns of type `aclitem[]` on PostgreSQL 16.15 (fact 9) and where each is read: (query, a text that must occur
# in that query's constant). `pg_init_privs.initprivs` is known and not judged.
KNOWN_ACL_COLUMNS: Mapping[str, tuple[str, str]] = {
    "pg_attribute.attacl": ("Q2", "a.attacl"),
    "pg_class.relacl": ("Q2", "c.relacl"),
    "pg_database.datacl": ("Q2", "d.datacl"),
    "pg_default_acl.defaclacl": ("Q4", "d.defaclacl"),
    "pg_foreign_data_wrapper.fdwacl": ("Q2", "w.fdwacl"),
    "pg_foreign_server.srvacl": ("Q2", "s.srvacl"),
    "pg_init_privs.initprivs": (
        "none",
        "a record of the rights at install time; gives nobody a right",
    ),
    "pg_language.lanacl": ("Q2", "l.lanacl"),
    "pg_largeobject_metadata.lomacl": ("Q2", "m.lomacl"),
    "pg_namespace.nspacl": ("Q2", "n.nspacl"),
    "pg_parameter_acl.paracl": ("Q2", "a.paracl"),
    "pg_proc.proacl": ("Q2", "p.proacl"),
    "pg_tablespace.spcacl": ("Q2", "s.spcacl"),
    "pg_type.typacl": ("Q2", "t.typacl"),
}

QUERY_TEXTS = {
    "Q0": Q0,
    "Q1": Q1,
    "Q1B": Q1B,
    "Q2": Q2,
    "Q3": Q3,
    "Q4": Q4,
    "STEP4": STEP4_SQL,
    "V2": V2_SQL,
}

_FLAGS = (
    ("rolsuper", "SUPERUSER"),
    ("rolcreaterole", "CREATEROLE"),
    ("rolcreatedb", "CREATEDB"),
    ("rolbypassrls", "BYPASSRLS"),
    ("rolreplication", "REPLICATION"),
)
# Catalogs whose access lists Q2 or Q4 read (rule S8): a row of `pg_shdepend` of type `a` in any other catalog is a place
# this version does not read.
_READ_CATALOGS = frozenset(
    {
        "pg_class",
        "pg_proc",
        "pg_namespace",
        "pg_type",
        "pg_database",
        "pg_foreign_data_wrapper",
        "pg_foreign_server",
        "pg_language",
        "pg_largeobject",
        "pg_parameter_acl",
        "pg_tablespace",
        "pg_default_acl",
    }
)
# The server's own default for everyone, written into a default-rights entry for all schemas (fact 23): kept from the
# runner so that this module does not import it.
_BUILT_IN_DEFAULT = frozenset({("f", "EXECUTE"), ("T", "USAGE")})
_DEFAULT_KINDS = {"r": "table", "S": "sequence", "f": "function", "T": "type", "n": "schema"}
_DEFAULT_WORDS = {"r": "TABLES", "S": "SEQUENCES", "f": "FUNCTIONS", "T": "TYPES", "n": "SCHEMAS"}
_FUNCTION_KINDS = ("function", "procedure", "aggregate")
_NOTHING_BY_DEFAULT = (
    "table",
    "view",
    "materialized view",
    "foreign table",
    "sequence",
    "column",
    "large object",
    "foreign-data wrapper",
    "foreign server",
    "tablespace",
    "parameter",
)
_SQL_KIND = {
    "table": "TABLE",
    "view": "TABLE",
    "materialized view": "TABLE",
    "foreign table": "TABLE",
    "column": "TABLE",
    "sequence": "SEQUENCE",
    "function": "ROUTINE",
    "procedure": "ROUTINE",
    "aggregate": "ROUTINE",
    "schema": "SCHEMA",
    "type": "TYPE",
    "domain": "DOMAIN",
    "database": "DATABASE",
    "language": "LANGUAGE",
    "foreign-data wrapper": "FOREIGN DATA WRAPPER",
    "foreign server": "FOREIGN SERVER",
    "tablespace": "TABLESPACE",
    "large object": "LARGE OBJECT",
    "parameter": "PARAMETER",
}
_RIGHT_WORDS = re.compile(r"[A-Z][A-Z ]{1,20}")
_MEMBERSHIP_KINDS = ("built_in_role", "can_act_as_family", "named_roles_overlap")
EVERYONE = "everyone (PUBLIC)"

_BY_HAND = {
    "name": "a person must write the statement by hand (a name holds a character that is not copied into a printed line)",
    "system": "this is an object of the server itself; a database administrator decides; no statement is printed",
    "database_owner": "this role owns the database; hand the database to another role (ALTER DATABASE ... OWNER TO ...)",
    "owner": "hand it to the migration role or drop it",
    "hand": "a person decides this by hand; no statement is printed",
}


# --- the result type --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Problem:
    """One thing that is wrong. Field order is the one of ticket 3.1a; `via` and `word` are two fields added because the
    line needs the role a right reaches the named role through and the word for the kind of object (3.1a has no place for
    either)."""

    kind: str  # one of PROBLEM_KINDS
    schema: str  # "" for an object that lives in no schema (database, large object, parameter, a role ...)
    obj: str  # the object's name; "" when the problem is about a role alone
    detail: str  # the column, the argument list, or the membership path; "" otherwise
    role: str  # the named role (or everyone) the problem is about; everyone is written EVERYONE
    right: str  # the right, the flag, "OWNER" or "MEMBER"
    grantor: str  # the role recorded as grantor of the item ("" for flags and ownership)
    owner: str = ""  # the object's owner ("" for role-only problems); for a default right: the role it is set for
    grantor_is_owner: bool = False
    outside_package: bool = (
        False  # the object is outside the schema of the run, or its owner is not in the family
    )
    extension: str = ""  # the extension the object is a member of ("" if none)
    fix: str = ""  # the statement(s) that remove it, or "" (a person writes it by hand)
    by_hand: str = ""  # "" / "name" / "system" / "database_owner" / "extension" / "owner" / "hand"
    repaired_by_run: bool = False  # true only for the two cases of section 4.1 step 2
    via: str = ""  # the role the right reaches the named role through (a group, a built-in role)
    word: str = ""  # the kind of object in words ("table", "function", "role" ...)

    @property
    def order(self) -> int:
        """Index of the statement group of section 4.2: 0 memberships, 1 default rights, 2 object rights granted by
        another role, 3 grant options granted by another role, 4 object rights granted by the owner, 5 grant options
        granted by the owner, 6 flags, 7 SECURITY DEFINER, 8 by hand.

        Deviation from the plan (rev 3 had 8 groups, with every grant option after every owner right): a statement that
        acts as another grantor (`SET ROLE <g>; ...`) needs that grantor's own right to look the schema up, and the
        owner's statement that takes the grantor's USAGE away must therefore come AFTER it. The real-server test
        `test_a_grant_option_from_two_grantors_is_removed_by_the_printed_statements` fails with the plan's order."""
        if not self.fix:
            return 8
        if self.kind in _MEMBERSHIP_KINDS or (self.kind == "right" and self.via):
            return 0
        if self.kind.startswith("default_"):
            return 1
        if self.kind in ("grant_option", "object_grant_option"):
            return 5 if self.grantor_is_owner else 3
        if self.kind == "flag":
            return 6
        if self.kind in ("definer_callable", "definer_unreviewed"):
            return 7
        return 4 if self.grantor_is_owner else 2

    def sort_key(self) -> tuple:
        return (
            self.order,
            self.kind,
            self.schema,
            self.obj,
            self.detail,
            self.role,
            self.right,
            self.grantor,
        )

    def _target(self) -> str:
        name = (
            _label(self.schema, self.obj)
            if self.schema and self.obj
            else _label(self.schema or self.obj)
        )
        if self.word in _FUNCTION_KINDS:
            return f"{name}({_label(self.detail)})"
        if self.word == "column" and self.detail:
            return f"{name}, column {_label(self.detail)}"
        return name

    def _who(self) -> str:
        return self.role if self.role == EVERYONE else _label(self.role)

    def _what(self) -> str:
        k = self.kind
        who = self._who()
        via = _label(self.via) if self.via else ""
        if k == "flag":
            return f"has the flag {self.right}" + (f" (through {via})" if via else " (directly)")
        if k == "built_in_role":
            return f"is a member of the built-in server role {via}" + (
                f" (through {self.detail})" if self.detail else ""
            )
        if k == "can_act_as_family":
            return f"can act as the migration role {via} (member of it through {self.detail})"
        if k == "named_roles_overlap":
            return f"the runtime, portal and purge roles must not be members of each other ({who} is a member of {via})"
        if k == "owns":
            return "owns this object"
        if k in ("right", "other_grantee", "everyone", "schema_right", "unread_relation_kind"):
            if k == "right":
                return (
                    f"can use it through the role {via}, {self.right}"
                    if via
                    else f"has {self.right}"
                )
            if k == "other_grantee":
                return f"has {self.right}; only the owner, the migration role and the grant map's roles may hold rights here"
            if k == "schema_right":
                return f"has {self.right} on the schema of the run; only USAGE is allowed"
            if k == "unread_relation_kind":
                return f"has {self.right} on a relation of a kind this version does not read (relkind {self.detail})"
            return f"has {self.right}"
        if k in ("grant_option", "object_grant_option"):
            return f"may pass {self.right} on to others"
        if k == "definer_callable":
            return f"may call it, and it runs with the rights of its owner {_label(self.owner)} (SECURITY DEFINER)"
        if k == "definer_unreviewed":
            return "runs with the rights of its owner (SECURITY DEFINER) and is not on the reviewed list"
        if k == "unread_catalog":
            return f"is named in the access list of a kind of object this version does not read ({_label(self.detail)})"
        if k == "foreign_owner":
            return f"is owned by {_label(self.owner)}, which is not the migration role or a role it belongs to"
        if k.startswith("default_"):
            if k == "default_unknown_kind":
                return (
                    f"a default right of a kind this version does not know ({_label(self.detail)})"
                )
            where = f" in the schema {_label(self.schema)}" if self.schema else " in every schema"
            return (
                f"gets {self.right} on every new {_DEFAULT_KINDS.get(self.detail, self.detail)} "
                f"that {_label(self.owner)} makes{where}"
            )
        return "has a problem"

    def line(self) -> str:
        """`<object words> <name><detail>: <role words> <what>. <ending>` (ticket 3.1a)."""
        if self.kind == "missing_schema_usage":
            return (
                f"the role {_label(self.role)} cannot use the schema {_label(self.schema)} after the grants: the migration "
                "role may not pass USAGE on the schema on. Give it the grant option "
                "(GRANT USAGE ON SCHEMA <schema> TO <the migration role> WITH GRANT OPTION; CREATE needs no grant option), "
                "or make it the owner of the schema."
            )
        if self.kind in ("flag", "built_in_role", "can_act_as_family", "named_roles_overlap"):
            head = f"role {self._who()}: "
            what = self._what()
        elif self.kind.startswith("default_"):
            head = f"{self.word or 'default right'}: {self._who()} "
            what = self._what()
        else:
            head = (
                f"{self.word} {self._target()}: {self._who()} "
                if self.word
                else f"{self._target()}: {self._who()} "
            )
            what = self._what()
        body = what
        if self.fix:
            ending = f"To remove: {self.fix}"
        elif self.by_hand == "extension":
            ending = (
                f"belongs to the extension {_label(self.extension)} (owner {_label(self.owner)}), not to this package; "
                "a REVOKE is undone by the next ALTER EXTENSION ... UPDATE; a database administrator decides "
                "(for example a database of its own for this package, or the extension installed in another schema); no "
                "statement is printed"
            )
        else:
            ending = _BY_HAND.get(self.by_hand, "")
        prefix = "NOT THIS PACKAGE'S OBJECT: " if self.outside_package else ""
        text = f"{prefix}{head}{body}."
        if ending:
            text += f" {ending}"
        if self.outside_package and self.fix:
            text += (
                f" Confirm with the owner of {self._target()} ({_label(self.owner)}) before running the statement; "
                "another application may need this right."
            )
        return text


class Rows(NamedTuple):
    """What `_read` returns. Each tuple field holds psycopg rows made with `namedtuple_row`, so fields are read by the
    column names of the queries."""

    version: int
    database_owner: str
    acl_columns: tuple[str, ...]
    subjects: tuple
    family: tuple
    memberships: tuple
    items: tuple
    owned_or_named: tuple
    defaults: tuple


# --- pinned reads and the two checks that need no judging ----------------------------------------------------------------


@contextmanager
def pinned_read(db, limits: Sequence[str]) -> Iterator[None]:
    """A savepoint (a transaction on a fresh connection) in which the two time limits and the search path are set before
    any read, and which always ends by rolling back, so the limits and the path are restored and nothing is kept. With
    the path pinned to `pg_catalog, pg_temp` an unqualified catalog name cannot be captured by a temporary table
    (fact 1), and the saved settings of the role cannot stop the check (fact 36). `transaction_timeout` of PostgreSQL 17
    and later is NOT neutralised: a saved value can stop the check, which then ends as "could not run"."""
    with db.transaction():
        for line in limits:
            db.execute(line)
        db.execute("SET LOCAL search_path = pg_catalog, pg_temp")
        yield
        raise pg.Rollback


def check_version(version: int, shown: str | None = None) -> None:
    """Refuse a server below PostgreSQL 16 (ticket 3.5), before the first query that needs 16."""
    if version < 160000:
        text = shown or (
            f"{version // 10000}.{version % 10000}" if version >= 100000 else str(version)
        )
        raise ConfigError(
            f"this database server is PostgreSQL {_label(str(text))}; migrate needs PostgreSQL 16 or later (it reads who is a "
            "member of which role in the form that version 16 introduced). Nothing was changed. Run migrate against a "
            "server of version 16 or later."
        )


def check_acl_columns(columns: Sequence[str]) -> None:
    """The self-check of ticket 3.6: the access-list columns this server has must be exactly the ones this module knows."""
    have = set(columns)
    unknown = sorted(have - set(KNOWN_ACL_COLUMNS))
    if unknown:
        raise ConfigError(
            "this PostgreSQL version keeps access rights in a place this version of the package does not read "
            f"({', '.join(_label(c) for c in unknown)}). migrate cannot say that the roles hold only what the grant map "
            "gives. Nothing was changed. Use a PostgreSQL version this release names as supported, or a newer release "
            "of the package."
        )
    missing = sorted(set(KNOWN_ACL_COLUMNS) - have)
    if missing:
        raise ConfigError(
            "this PostgreSQL version does not have "
            f"({', '.join(_label(c) for c in missing)}), a place this version of the package reads. migrate cannot say "
            "that the roles hold only what the grant map gives. Nothing was changed. Use a PostgreSQL version this "
            "release names as supported, or a newer release of the package."
        )


# --- layer 1: read -----------------------------------------------------------------------------------------------------


def _fetch(db, text: str, params: Mapping | None = None, *, named: bool = True) -> tuple:
    cur = db.cursor(row_factory=pg.named_rows if named else pg.tuple_rows)
    cur.execute(text, params or {})
    return tuple(cur.fetchall())


def _read(
    db,
    *,
    named: Sequence[str],
    family: Sequence[str],
    schema: str,
    managed_functions: Sequence[str],
) -> Rows:
    """Run the queries of ticket 3.2: V2, Q0, Q1 twice (named roles, family), Q1b, Q2, Q3, Q4 (eight statements, whatever
    the size of the database). The version and the access-list columns are checked as soon as they are read, before the
    queries that need version 16. `managed_functions` is used by the step-4 query only, not here."""
    del managed_functions
    named_list, family_list = list(named), list(family)
    version, owner = _fetch(db, V2_SQL, named=False)[0]
    check_version(version)
    acl_columns = tuple(r[0] for r in _fetch(db, Q0, named=False))
    check_acl_columns(acl_columns)
    subjects = _fetch(db, Q1, {"roles": named_list})
    fam = _fetch(db, Q1, {"roles": family_list})
    # Q1b gets every role of the closure of the named roles, so that a path of memberships can be followed.
    closure = sorted({r.member_of for r in subjects} | set(named_list))
    memberships = _fetch(db, Q1B, {"roles": closure})
    params = {"named": named_list, "family": family_list, "schema": schema}
    items = _fetch(db, Q2, params)
    owned = _fetch(db, Q3, {"named": named_list})
    defaults = _fetch(db, Q4, {"named": named_list, "family": family_list})
    return Rows(version, owner, acl_columns, subjects, fam, memberships, items, owned, defaults)


# --- layer 2: judge ----------------------------------------------------------------------------------------------------


def _plain(*texts: str) -> bool:
    return all(isinstance(t, str) and escape_name(t) == t for t in texts)


def _ident(*parts: str) -> pg.SqlPart:
    return pg.quote_identifier(*parts)


def _s(text: pg.SqlPart) -> str:
    return pg.sql_string(text)


def _object_sql(kind: str, schema: str, name: str, sub: str) -> pg.SqlPart | None:
    """The object as it is written after ON, or None when the texts are not plain."""
    if kind in (
        "table",
        "view",
        "materialized view",
        "foreign table",
        "column",
        "sequence",
        "type",
        "domain",
    ):
        return _ident(schema, name) if _plain(schema, name) else None
    if kind in _FUNCTION_KINDS:
        # the identity arguments of an aggregate with none are empty on 16.15 (checked), so `()` is what is printed
        # (`(*)` is a syntax error in GRANT, REVOKE and ALTER ROUTINE)
        args = sub
        return (
            pg.sql_template("{}({})", _ident(schema, name), pg.sql_words(args))
            if _plain(schema, name, sub)
            else None
        )
    if kind == "schema":
        return _ident(schema) if _plain(schema) else None
    if kind in (
        "database",
        "language",
        "foreign-data wrapper",
        "foreign server",
        "tablespace",
        "parameter",
    ):
        return _ident(name) if _plain(name) else None
    if kind == "large object":
        return pg.sql_words(name) if name.isdigit() else None
    return None


def _revoke(
    item_kind: str,
    schema: str,
    name: str,
    sub: str,
    right: str,
    grantee: str | None,
    grantor: str,
    grantor_is_owner: bool,
    *,
    option: bool = False,
) -> str:
    """The REVOKE statement of ticket 4.2 for one access-list item, or "" when a text in it is not plain."""
    target = _object_sql(item_kind, schema, name, sub)
    word = _SQL_KIND.get(item_kind)
    if target is None or word is None or not _RIGHT_WORDS.fullmatch(right):
        return ""
    if grantee is not None and not _plain(grantee):
        return ""
    if not grantor_is_owner and not _plain(grantor):
        return ""
    who = pg.sql_words("PUBLIC") if grantee is None else _ident(grantee)
    right_sql = pg.sql_words(right)
    if item_kind == "column":
        right_sql = (
            pg.sql_template("{} ({})", pg.sql_words(right), _ident(sub)) if _plain(sub) else None
        )
        if right_sql is None:
            return ""
    head = "REVOKE GRANT OPTION FOR {} ON {} {} FROM {}" if option else "REVOKE {} ON {} {} FROM {}"
    stmt = pg.sql_template(head, right_sql, pg.sql_words(word), target, who)
    text = _s(stmt) + (" CASCADE;" if option else ";")
    if not grantor_is_owner:
        text = f"SET ROLE {_s(_ident(grantor))}; {text} RESET ROLE;"
    return text


def _membership_fix(member: str, group: str, grantor: str) -> str:
    if not _plain(member, group, grantor):
        return ""
    return f"REVOKE {_s(_ident(group))} FROM {_s(_ident(member))} GRANTED BY {_s(_ident(grantor))};"


class _Hop(NamedTuple):
    member: str
    group: str
    grantor: str


def _paths(memberships: Sequence) -> dict[str, list[tuple[str, str]]]:
    edges: dict[str, list[tuple[str, str]]] = {}
    for m in memberships:
        edges.setdefault(m.member, []).append((m.role_name, m.grantor))
    return edges


def _path(edges: Mapping[str, Sequence[tuple[str, str]]], start: str, target: str) -> list[_Hop]:
    """The shortest chain of memberships from `start` to `target` (a list of hops), or [] if there is none."""
    if start == target:
        return []
    seen = {start}
    queue: deque[tuple[str, list[_Hop]]] = deque([(start, [])])
    while queue:
        node, hops = queue.popleft()
        for role, grantor in sorted(edges.get(node, ())):
            if role in seen:
                continue
            nxt = [*hops, _Hop(node, role, grantor)]
            if role == target:
                return nxt
            seen.add(role)
            queue.append((role, nxt))
    return []


def _path_text(start: str, hops: Sequence[_Hop]) -> str:
    return " -> ".join([_label(start), *(_label(h.group) for h in hops)]) if hops else ""


def _rights_for(role_kind: str, g: Grant) -> frozenset[str]:
    """The table-level rights a named role of this kind may hold on one relation of the grant map (ticket 3.2)."""
    if role_kind == "runtime":
        words = g.runtime
    elif role_kind == "portal":
        words = "SELECT" if g.portal else ""
    else:
        words = g.purge
    return frozenset(w.strip() for w in words.split(",") if w.strip())


_RELKIND_OF_MAP = {"table": ("r", "p"), "view": ("v",), "sequence": ("S",)}


def _allowed_for(role_kind: str, it, schema: str, grant_map: Mapping[str, Grant]) -> bool:
    """Does the grant map (or the baseline) give a named role of this kind this one item?"""
    if it.kind == "schema":
        return it.privilege_type == "USAGE"
    if it.kind == "database":
        return it.privilege_type == "CONNECT"
    if it.schema != schema or it.name not in grant_map:
        return False
    g = grant_map[it.name]
    if it.kind == "column":
        return (
            role_kind == "purge"
            and g.kind == "table"
            and it.relkind in _RELKIND_OF_MAP["table"]
            and it.sub in g.purge_cols
            and it.privilege_type == "SELECT"
            and not it.is_grantable
        )
    wanted = {"table": "table", "view": "view", "sequence": "sequence"}.get(it.kind)
    if wanted != g.kind:
        return False
    return it.privilege_type in _rights_for(role_kind, g) and not it.is_grantable


def _judge(
    rows: Rows,
    *,
    named_roles: Mapping[str, str],
    family: Sequence[str],
    grant_map: Mapping[str, Grant],
    schema: str,
    managed_relations: Sequence[str],
    managed_functions: Sequence[str],
    reviewed_definers: frozenset[tuple[str, str, str]],
) -> list[Problem]:
    """Turn rows into problems (every rule of ticket 3.3). Pure: no database, no clock."""
    migration_role = family[0] if family else ""
    managed_rel, managed_fn = set(managed_relations), set(managed_functions)
    out: list[Problem] = []
    named = sorted(named_roles)

    # closures: named role -> {role: reached at once}; the database owner also reaches `pg_database_owner` (fact 8)
    closure: dict[str, dict[str, bool]] = {n: {n: True} for n in named}
    flags: dict[str, tuple[str, ...]] = {}
    for r in rows.subjects:
        closure.setdefault(r.start_role, {})[r.member_of] = bool(r.uses_rights_at_once)
        flags[r.member_of] = tuple(word for col, word in _FLAGS if getattr(r, col))
    for n in named:
        if rows.database_owner in closure[n] and "pg_database_owner" not in closure[n]:
            closure[n]["pg_database_owner"] = closure[n][rows.database_owner]
    fam_roles = {r.member_of for r in rows.family} | set(family)
    fam_has_db_owner = rows.database_owner in fam_roles
    named_of: dict[str, list[str]] = {}
    for n in named:
        for role in closure[n]:
            named_of.setdefault(role, []).append(n)
    edges = _paths(rows.memberships)

    def membership_problem(kind: str, n: str, target: str, **kw) -> Problem:
        hops = _path(edges, n, target)
        first = hops[0] if hops else None
        fix = _membership_fix(first.member, first.group, first.grantor) if first else ""
        by_hand = "" if fix else ("name" if first else "hand")
        return Problem(
            kind,
            "",
            "",
            _path_text(n, hops),
            n,
            kw.pop("right", "MEMBER"),
            first.grantor if first else "",
            fix=fix,
            by_hand=by_hand,
            via=target,
            word="role",
            **kw,
        )

    # S1 flags, S2 built-in roles, S3 family and overlap
    for n in named:
        for role in sorted(closure[n]):
            for word in flags.get(role, ()):
                fix = f"ALTER ROLE {_s(_ident(role))} NO{word};" if _plain(role) else ""
                out.append(
                    Problem(
                        "flag",
                        "",
                        "",
                        "",
                        n,
                        word,
                        "",
                        fix=fix,
                        by_hand="" if fix else "name",
                        via=role if role != n else "",
                        word="role",
                    )
                )
            if role.startswith("pg_"):
                p = membership_problem("built_in_role", n, role)
                if role == "pg_database_owner":
                    p = Problem(**{**p.__dict__, "fix": "", "by_hand": "database_owner"})
                out.append(p)
            elif role in fam_roles:
                out.append(membership_problem("can_act_as_family", n, role))
            elif role != n and role in named_roles:
                out.append(membership_problem("named_roles_overlap", n, role))

    # S4 owns nothing, S8 named where nothing is read
    for r in rows.owned_or_named:
        if r.deptype == "o" and not r.temporary:
            out.append(
                Problem(
                    "owns", "", r.described, "", r.role, "OWNER", "", by_hand="owner", word="object"
                )
            )
        elif r.deptype == "a" and not r.role.startswith("pg_") and r.catalog not in _READ_CATALOGS:
            out.append(
                Problem(
                    "unread_catalog",
                    "",
                    r.described,
                    r.catalog,
                    r.role,
                    "ACL",
                    "",
                    by_hand="hand",
                    word="object",
                )
            )

    seen_objects: set[tuple] = set()
    for it in rows.items:
        fam_owned = bool(it.family_owned) or (it.owner == "pg_database_owner" and fam_has_db_owner)
        in_run = (not it.system) and it.schema == schema
        ext = it.extension if (it.extension and not it.extension_family_owned) else ""
        outside = (not in_run) or not fam_owned

        def make(
            kind,
            role,
            right,
            *,
            fix=None,
            option=False,
            via="",
            detail=None,
            rep=False,
            it=it,
            ext=ext,
            outside=outside,
            in_run=in_run,
        ) -> Problem:
            sub = it.sub if detail is None else detail
            by_hand = ""
            if fix is None:
                fix = _revoke(
                    it.kind,
                    it.schema,
                    it.name,
                    it.sub,
                    right,
                    None if role == EVERYONE else it.grantee,
                    it.grantor,
                    bool(it.grantor_is_owner),
                    option=option,
                )
            if it.system:
                fix, by_hand = "", "system"
            elif ext:
                fix, by_hand = "", "extension"
            elif not fix:
                by_hand = "name"
            return Problem(
                kind,
                it.schema,
                it.name,
                sub,
                role,
                right,
                it.grantor or "",
                it.owner or "",
                bool(it.grantor_is_owner),
                outside,
                ext,
                fix,
                by_hand,
                rep,
                via,
                it.kind,
            )

        # an object whose access list is empty (a file revoked everything, from the owner too) comes as one row with no
        # right (`privilege_type` is null, from the LEFT JOIN of Q2): it has no right to judge and must never be read as
        # "for everyone"; its owner and its SECURITY DEFINER flag are judged below, once per object
        if it.privilege_type is None:
            continue

        # --- items that name a subject role (S5, S6) -----------------------------------------------------------
        if it.grantee is not None and it.grantee_is_subject:
            if it.grantee.startswith("pg_") or it.owner_item:
                continue
            reaching = sorted(set(named_of.get(it.grantee, [])))
            if it.is_grantable:
                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))
            for n in reaching:
                if _allowed_for(named_roles[n], it, schema, grant_map):
                    continue
                if it.grantee == n:
                    rep = (
                        in_run
                        and it.name in grant_map
                        and bool(it.grantee_is_named)
                        and it.grantor == migration_role
                        and it.kind in ("table", "view", "sequence", "column")
                    )
                    out.append(make("right", n, it.privilege_type, rep=rep))
                else:
                    hops = _path(edges, n, it.grantee)
                    mfix = (
                        _membership_fix(hops[0].member, hops[0].group, hops[0].grantor)
                        if hops
                        else ""
                    )
                    p = make("right", n, it.privilege_type, fix=mfix or None, via=it.grantee)
                    out.append(p)
            continue

        # --- items for everyone ---------------------------------------------------------------------------------
        if it.grantee is None:
            kind, right = it.kind, it.privilege_type
            in_fn = kind in _FUNCTION_KINDS
            managed_here = (
                in_run and fam_owned and in_fn and it.name in managed_fn and right == "EXECUTE"
            )
            if in_fn and it.definer and right == "EXECUTE" and not ext:
                key = (it.schema, it.name, it.sub)
                if key not in reviewed_definers:
                    out.append(
                        make(
                            "definer_callable",
                            EVERYONE,
                            right,
                            fix=_definer_fix(it),
                            rep=managed_here,
                        )
                    )
            if in_fn and right == "EXECUTE":
                if in_run and fam_owned:
                    out.append(make("everyone", EVERYONE, right, rep=managed_here))
                continue
            if kind in ("type", "domain"):
                if in_run and fam_owned and not it.row_type:
                    out.append(make("everyone", EVERYONE, right))
                continue
            if kind == "language":
                if in_run and fam_owned:
                    out.append(make("everyone", EVERYONE, right))
                continue
            if kind == "schema":
                if right != "USAGE":
                    out.append(make("schema_right" if in_run else "everyone", EVERYONE, right))
                continue
            if kind == "database":
                if right not in ("CONNECT", "TEMPORARY"):
                    out.append(make("everyone", EVERYONE, right))
                continue
            if kind == "relation of an unread kind":
                out.append(make("unread_relation_kind", EVERYONE, right, detail=it.relkind, fix=""))
                continue
            if kind in _NOTHING_BY_DEFAULT:
                out.append(make("everyone", EVERYONE, right))
            continue

        # --- items for a role that is neither a subject nor everyone (third role): the schema of the run only ---
        if not in_run or it.owner_item or it.grantee == migration_role:
            continue
        if it.kind == "relation of an unread kind":
            out.append(
                make(
                    "unread_relation_kind", it.grantee, it.privilege_type, detail=it.relkind, fix=""
                )
            )
        elif it.kind == "schema":
            out.append(
                make(
                    "schema_right" if it.privilege_type != "USAGE" else "other_grantee",
                    it.grantee,
                    it.privilege_type,
                )
            )
            if it.is_grantable:
                out.append(make("object_grant_option", it.grantee, it.privilege_type, option=True))
        elif fam_owned:
            out.append(make("other_grantee", it.grantee, it.privilege_type))
            if it.is_grantable:
                out.append(make("object_grant_option", it.grantee, it.privilege_type, option=True))

    # O4 reviewed definers and O8 owner of the package's own objects: once per object, from the rows of the schema of the run
    for it in rows.items:
        if it.system or it.schema != schema:
            continue
        fam_owned = bool(it.family_owned) or (it.owner == "pg_database_owner" and fam_has_db_owner)
        key = (it.kind, it.schema, it.name, it.sub)
        if key in seen_objects:
            continue
        seen_objects.add(key)
        ext = it.extension if (it.extension and not it.extension_family_owned) else ""
        if (
            it.kind in _FUNCTION_KINDS
            and fam_owned
            and it.definer
            and (it.schema, it.name, it.sub) not in reviewed_definers
        ):
            out.append(
                Problem(
                    "definer_unreviewed",
                    it.schema,
                    it.name,
                    it.sub,
                    it.owner,
                    "SECURITY DEFINER",
                    "",
                    it.owner,
                    False,
                    False,
                    ext,
                    _definer_fix(it) if not ext else "",
                    "extension" if ext else "",
                    False,
                    "",
                    it.kind,
                )
            )
        managed = (
            (it.kind in ("table", "view", "sequence") and it.name in managed_rel)
            or (it.kind in _FUNCTION_KINDS and it.name in managed_fn)
            or it.kind == "schema"
        )
        if managed and not fam_owned:
            out.append(
                Problem(
                    "foreign_owner",
                    it.schema,
                    it.name,
                    it.sub,
                    it.owner,
                    "OWNER",
                    "",
                    it.owner,
                    False,
                    False,
                    "",
                    "",
                    "owner",
                    False,
                    "",
                    it.kind,
                )
            )

    # D1-D4 default rights
    for d in rows.defaults:
        right = d.privilege_type
        if d.kind not in _DEFAULT_WORDS:
            out.append(_default("default_unknown_kind", d, "", ""))
            continue
        if d.grantee is not None and d.grantee_is_subject:
            if d.grantee == d.set_for:
                continue
            out.append(_default("default_for_named", d, right, d.grantee))
        elif d.grantee is None:
            built_in = d.kind in "fT" and not d.schema and (d.kind, right) in _BUILT_IN_DEFAULT
            if not built_in:
                out.append(_default("default_for_everyone", d, right, EVERYONE))
        elif d.set_for_family and d.grantee != d.set_for and d.grantee != migration_role:
            out.append(_default("default_for_other", d, right, d.grantee))

    # a named role must be able to use the schema of the run (the only "too little" this module reports)
    schema_items = [
        i for i in rows.items if i.kind == "schema" and i.schema == schema and not i.system
    ]
    for n in named:
        can = any(
            i.privilege_type == "USAGE"
            and (
                i.grantee is None
                or i.grantee == n
                or (i.grantee_is_subject and closure[n].get(i.grantee, False))
            )
            for i in schema_items
        )
        if not can:
            out.append(
                Problem("missing_schema_usage", schema, "", "", n, "USAGE", "", word="schema")
            )
    return sorted(set(out), key=lambda p: p.sort_key())


def _definer_fix(it) -> str:
    if it.system or not _plain(it.schema, it.name, it.sub):
        return ""
    word = "PROCEDURE" if it.kind == "procedure" else "FUNCTION"
    return f"ALTER {word} {_s(_ident(it.schema, it.name))}({it.sub}) SECURITY INVOKER;"


def _default(kind: str, d, right: str, who: str) -> Problem:
    where = f" IN SCHEMA {_s(_ident(d.schema))}" if d.schema else ""
    fix = ""
    by_hand = "hand" if kind == "default_unknown_kind" else "name"
    if (
        kind != "default_unknown_kind"
        and _plain(d.set_for, d.schema or "", who)
        and _RIGHT_WORDS.fullmatch(right)
    ):
        grantee = "PUBLIC" if who == EVERYONE else _s(_ident(who))
        fix = (
            f"ALTER DEFAULT PRIVILEGES FOR ROLE {_s(_ident(d.set_for))}{where} "
            f"REVOKE {right} ON {_DEFAULT_WORDS[d.kind]} FROM {grantee};"
        )
        by_hand = ""
    return Problem(
        kind,
        d.schema or "",
        "",
        d.kind,
        who or EVERYONE,
        right,
        "",
        d.set_for,
        False,
        False,
        "",
        fix,
        by_hand,
        False,
        "",
        _DEFAULT_KINDS.get(d.kind, ""),
    )


def statements_for(problems: Sequence[Problem]) -> list[str]:
    """The statements of ticket 4.2: de-duplicated, in the order of `Problem.order` (memberships first, then default
    rights, object rights granted by another role, rights granted by the owner, grant options, flags, SECURITY DEFINER)."""
    seen: set[str] = set()
    out: list[str] = []
    for p in sorted((p for p in problems if p.fix), key=lambda p: p.sort_key()):
        if p.fix not in seen:
            seen.add(p.fix)
            out.append(p.fix)
    return out


def statement_blocks(problems: Sequence[Problem]) -> tuple[list[str], list[str]]:
    """The statements in two blocks (ticket 4.2, F11): the first holds the package's own objects and the named roles'
    memberships and flags; the second holds statements for objects that are not this package's, which a person confirms
    with the object's owner before running."""
    own = [p for p in problems if not p.outside_package]
    outside = [p for p in problems if p.outside_package]
    first = statements_for(own)
    return first, [s for s in statements_for(outside) if s not in first]


def verify(
    db,
    *,
    migration_role: str,
    login_role: str | None,
    named_roles: Mapping[str, str],
    grant_map: Mapping[str, Grant],
    schema: str,
    managed_relations: Sequence[str],
    managed_functions: Sequence[str],
    reviewed_definers: frozenset[tuple[str, str, str]],
    limits: Sequence[str],
) -> list[Problem]:
    """Every problem in the state the database is in now (the caller cuts the printed list; the decision is taken on
    the full list). Reads only. Raises `ConfigError` for a server below PostgreSQL 16 and for an access-list column this
    version does not know."""
    family = [migration_role] + (
        [login_role] if login_role and login_role != migration_role else []
    )
    with pinned_read(db, limits):
        rows = _read(
            db,
            named=sorted(named_roles),
            family=family,
            schema=schema,
            managed_functions=managed_functions,
        )
    check_version(rows.version)
    check_acl_columns(rows.acl_columns)
    return _judge(
        rows,
        named_roles=named_roles,
        family=family,
        grant_map=grant_map,
        schema=schema,
        managed_relations=managed_relations,
        managed_functions=managed_functions,
        reviewed_definers=reviewed_definers,
    )
