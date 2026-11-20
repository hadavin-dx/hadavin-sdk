"""Forward-only schema migrations for the Postgres store (`hadavin-sdk migrate`).

Run under a migration role, never by the runtime. Every pending `migrations/NNNN_*.sql` file is applied in one
transaction under a transaction-scoped advisory lock, so two concurrent runs apply each file once. Pattern
ported from WARDEN `audit.py:migrate` (main a1e76cbf). Rollback = restore the snapshot taken before migrating.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from psycopg import errors, sql

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.postgres import connect, names_of

_LOG = logging.getLogger("hadavin_sdk.store")

_log = logging.getLogger("hadavin_sdk.migrate")
MIGRATIONS = Path(__file__).parent / "migrations"


@dataclass(frozen=True)
class Grant:
    """What the roles get on one relation. `runtime` is the privilege list for the runtime role; `portal` says the
    read-only portal role may SELECT it. A relation not in `GRANTS` gets nothing, so `check_grants` (run by
    `migrate` and by CI) refuses a migration that creates one."""

    kind: Literal["table", "view", "sequence"]
    runtime: str
    portal: bool = False
    purge: str = (
        ""  # table-level privileges of the purge role (the evidence deleter) on this relation
    )
    # Columns the purge role may SELECT (a DELETE's WHERE needs them) and nothing else: it cannot read a stored
    # original or a tool result.
    purge_cols: tuple[str, ...] = ()
    # Table-level privileges of the reset role: the only identity that may clear a stop (`migrate --reset-role`).
    reset: str = ""
    # Table-level privileges of the release role (0008): it releases expired spend holds through ONE function and
    # appends to the audit; it holds no right on any money table.
    release: str = ""


_RW = "SELECT, INSERT, UPDATE"
_APPEND = "SELECT, INSERT"  # written once, never changed
# The one grant map. Audit rows and checkpoints are read and appended only (their triggers also refuse UPDATE,
# DELETE and TRUNCATE to any role); reconcile deletes an outbox row once it is in the chain. A later PR adds its
# relations here (K5-core `redaction_maps`, K6 labels and reports, ...); the portal list never holds
# `redaction_maps`, `events`, `tick_state.detail` or secrets.
GRANTS: dict[str, Grant] = {
    "runs": Grant("table", _RW, portal=True, purge_cols=("run_id", "state", "updated_at")),
    "plans": Grant("table", _RW, portal=True),
    "gate_decisions": Grant("table", _APPEND, portal=True),
    "approval_requests": Grant("table", _RW, portal=True),
    "approval_decisions": Grant("table", _APPEND, portal=True),
    "dead_letters": Grant("table", _APPEND),
    # Spend reservations (0007): the runtime books and closes them; only the purge role deletes closed rows.
    "spend_reservations": Grant("table", _RW, purge="DELETE", purge_cols=("status", "closed_at")),
    "spend": Grant("table", _RW),
    "spend_month": Grant("table", _RW),
    # Stop state (0006): the runtime may add a stop and read; it holds no right that turns the switch off. Only
    # the reset role clears stops (and turns the old flag off), and it writes the reset into the audit chain.
    "kill_switch": Grant("table", "SELECT", reset="SELECT, UPDATE"),
    "kill_switch_stops": Grant("table", _APPEND, reset="SELECT"),
    "kill_switch_clears": Grant("table", "SELECT", reset=_APPEND),
    "tick_state": Grant("table", _RW),
    "audit_entries": Grant("table", _APPEND, portal=True, reset=_APPEND, release=_APPEND),
    "audit_checkpoints": Grant("table", _APPEND, portal=True, reset="SELECT", release="SELECT"),
    "audit_outbox": Grant("table", "SELECT, INSERT, DELETE"),
    # K5-core: append and purge only (no UPDATE); `redaction_maps` is never portal-readable.
    # The runtime role appends and reads evidence; only the purge role (its own identity) deletes it.
    "tool_calls": Grant(
        "table", _APPEND, purge="DELETE", purge_cols=("call_id", "run_id", "created_at")
    ),
    "redaction_maps": Grant("table", _RW, purge="DELETE", purge_cols=("run_id", "updated_at")),
    "approval_decisions_seq_seq": Grant("sequence", "USAGE"),
    "dead_letters_seq_seq": Grant("sequence", "USAGE"),
}
# The function of 0008 that lowers expired holds; only the release role may run it (EXECUTE is revoked from PUBLIC
# in the migration and from every other named role here).
RELEASE_FUNCTION = "hadavin_release_expired_spend(text, date)"
_LOCK = int.from_bytes(b"hadvnmig", "big") >> 1  # one fixed key for every migrate run
_ROLE = re.compile(r"[a-z_][a-z0-9_]{0,62}")
# Names PostgreSQL reads as a keyword in a GRANT (everyone, nobody, the caller), not as one role.
_FORBIDDEN_ROLES = frozenset({"public", "none", "session_user", "current_user"})
_FILE = re.compile(r"(\d{4})_[a-z0-9_]+\.sql")
_CREATE = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:MATERIALIZED\s+)?(TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)",
    re.IGNORECASE,
)
# Possessive quantifiers (Python 3.11+) plus a leading \b: no backtracking, linear time on long identifiers.
_SERIAL = re.compile(r"\b(\w++)\s++(?:(?:BIG|SMALL)?SERIAL|SERIAL[248])\b", re.IGNORECASE)
# Statements the guard does not read. Any of these in a migration is refused ("extend the guard") rather than
# skipped, so a relation or sequence it creates cannot go ungranted.
_SAFE_CREATE = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\b|CREATE\s+OR\s+REPLACE\s+(?:FUNCTION|TRIGGER)\b"
    r"|CREATE\s+TRIGGER\b|CREATE\s+(?:TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?[a-z_]\w*\s*(?:\(|AS\b)"
    r"|CREATE\s+OR\s+REPLACE\s+VIEW\s+[a-z_]\w*\s*(?:\(|AS\b)",
    re.IGNORECASE,
)
_ANY_CREATE = re.compile(r"\bCREATE\b", re.IGNORECASE)
_UNREAD = re.compile(
    r"\bALTER\s+TABLE\b[^;]*\b(?:(?:BIG|SMALL)?SERIAL|SERIAL[248])\b|\bAS\s+IDENTITY\b|\bCREATE\s+SEQUENCE\b",
    re.IGNORECASE,
)


def _migration_files(folder: Path = MIGRATIONS) -> list[Path]:
    return sorted(folder.glob("*.sql"))


def check_ledger(paths: list[Path]) -> list[str]:
    """Problems with the file names: each is `NNNN_<name>.sql` and the numbers run 1, 2, 3 ... with no repeat or gap."""
    problems = [
        f"{p.name}: not named NNNN_<name>.sql" for p in paths if not _FILE.fullmatch(p.name)
    ]
    numbers = sorted(int(p.name[:4]) for p in paths if _FILE.fullmatch(p.name))
    for n in sorted({n for n in numbers if numbers.count(n) > 1}):
        problems.append(f"two migrations are numbered {n:04d}")
    missing = sorted(set(range(1, max(numbers, default=0) + 1)) - set(numbers))
    problems += [f"migration {n:04d} is missing" for n in missing]
    return problems


def _table_body(text: str, start: int) -> str:
    """The text of the parenthesised column list that opens at or after `start` (parentheses balanced)."""
    open_at = text.find("(", start)
    if open_at == -1:
        return ""
    depth = 0
    for i in range(open_at, len(text)):
        depth += (text[i] == "(") - (text[i] == ")")
        if depth == 0:
            return text[open_at : i + 1]
    return text[open_at:]


def _scan(paths: list[Path]) -> tuple[dict[str, str], list[str]]:
    """(relation name -> kind, unread statements). Kinds: every table, view and serial-column sequence the
    migrations create. A statement that could create a relation or sequence in a way this scan does not read
    (quoted or schema-qualified name, UNLOGGED/TEMP/FOREIGN tables, CREATE SEQUENCE, IDENTITY, ADD COLUMN ...
    SERIAL) is returned as a problem, never skipped: the guard fails closed."""
    found: dict[str, str] = {}
    unread: list[str] = []
    for path in paths:
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        text = re.sub(r"--[^\n]*", "", text)
        for m in _ANY_CREATE.finditer(text):
            if not _SAFE_CREATE.match(text, m.start()):
                snippet = " ".join(text[m.start() : m.start() + 40].split())
                unread.append(f"{path.name}: statement the guard does not read: {snippet!r}")
        unread += [
            f"{path.name}: {u.group(0)[:40]!r} is not read by the guard"
            for u in _UNREAD.finditer(text)
        ]
        for m in _CREATE.finditer(text):
            kind, name = m.group(1).lower(), m.group(2).lower()
            found[name] = kind
            if kind == "table":
                for col in _SERIAL.findall(_table_body(text, m.end())):
                    found[f"{name}_{col.lower()}_seq"] = "sequence"
    return found, unread


def check_grants(paths: list[Path]) -> list[str]:
    """Problems between the migrations and `GRANTS`: a relation they create with no entry (it would get no grant
    and fail at runtime), an entry for a relation no migration creates, or an entry of the wrong kind."""
    created, problems = _scan(paths)
    problems += [
        f"{n} ({k}) is created by a migration but is not in GRANTS"
        for n, k in sorted(created.items())
        if n not in GRANTS
    ]
    for name, grant in sorted(GRANTS.items()):
        if name not in created:
            problems.append(f"GRANTS names {name}, which no migration creates")
        elif created[name] != grant.kind:
            problems.append(
                f"GRANTS says {name} is a {grant.kind}; the migrations create a {created[name]}"
            )
    return problems


def _apply_grants(db, role_name: str, privileges, columns=None) -> None:
    """Reset the role's rights on every relation in `GRANTS`, then give back what `privileges(grant)` names."""
    role = sql.Identifier(role_name)
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    db.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(sql.Identifier(schema), role))
    for name, grant in GRANTS.items():
        what = sql.SQL(
            "SEQUENCE" if grant.kind == "sequence" else "TABLE"
        )  # a view is granted as a table
        rel = sql.Identifier(name)
        db.execute(sql.SQL("REVOKE ALL ON {} {} FROM {}").format(what, rel, role))
        if wanted := privileges(grant):
            db.execute(sql.SQL("GRANT {} ON {} {} TO {}").format(sql.SQL(wanted), what, rel, role))
        if columns is not None and (cols := columns(grant)):
            db.execute(
                sql.SQL("GRANT SELECT ({}) ON {} TO {}").format(
                    sql.SQL(", ").join(sql.Identifier(c) for c in cols), rel, role
                )
            )


_TABLE_PRIVS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")


def effective_problems(db, role: str, expected_table, expected_cols=None) -> list[str]:
    """What the role can REALLY do, however it got it (a direct grant, a role it is a member of, PUBLIC, a default
    privilege, ownership), against the grant map: any relation of the schema, in GRANTS or not, on which it can do
    more than `expected_table(grant)` (and, for columns, `expected_cols(grant)`). A superuser, a role that can
    create roles or databases or bypass row security, a role that owns a relation or can CREATE in the schema is a
    problem too. The grants above are made first and this runs in the same transaction, so a problem rolls them back."""
    problems: list[str] = []
    row = db.execute(
        "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles WHERE rolname = %s",
        (role,),
    ).fetchone()
    if row is None:
        return [f"{role}: the role does not exist"]
    if any(row):
        problems.append(
            f"{role}: is a superuser or can create roles or databases or bypass row security"
        )
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    if db.execute("SELECT has_schema_privilege(%s, %s, 'CREATE')", (role, schema)).fetchone()[0]:
        problems.append(f"{role}: can CREATE in schema {schema}")
    rels = db.execute(
        "SELECT c.oid, c.relname, c.relkind, pg_get_userbyid(c.relowner) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relkind IN ('r','p','v','m','S')",
        (schema,),
    ).fetchall()
    for owner in sorted({o for _, _, _, o in rels if o != role}):
        # Membership, not inherited rights: a NOINHERIT member holds no rights today and can still SET ROLE to the owner.
        if db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (role, owner)).fetchone()[0]:
            problems.append(f"{role}: is a member of {owner}, the owner of relations in {schema}")
    for oid, name, kind, owner in rels:
        if owner == role:
            problems.append(f"{role}: owns {name}")
        grant = GRANTS.get(name)
        if kind == "S":
            allowed = (
                {p.strip() for p in expected_table(grant).split(",") if p.strip()}
                if grant
                else set()
            )
            for p in ("USAGE", "SELECT", "UPDATE"):
                if (
                    p not in allowed
                    and db.execute(
                        "SELECT has_sequence_privilege(%s, %s, %s)", (role, oid, p)
                    ).fetchone()[0]
                ):
                    problems.append(f"{role}: can {p} sequence {name}")
            continue
        allowed = (
            {p.strip() for p in expected_table(grant).split(",") if p.strip()} if grant else set()
        )
        allowed_cols = set(expected_cols(grant)) if (grant and expected_cols) else set()
        for p in _TABLE_PRIVS:
            if (
                p not in allowed
                and db.execute("SELECT has_table_privilege(%s, %s, %s)", (role, oid, p)).fetchone()[
                    0
                ]
            ):
                problems.append(
                    f"{role}: can {p} {name}" + ("" if grant else " (not in the grant map)")
                )
        for (col,) in db.execute(
            "SELECT attname FROM pg_attribute WHERE attrelid = %s AND attnum > 0 AND NOT attisdropped",
            (oid,),
        ).fetchall():
            for p in ("SELECT", "INSERT", "UPDATE"):
                if p in allowed or (p == "SELECT" and col in allowed_cols):
                    continue
                if db.execute(
                    "SELECT has_column_privilege(%s, %s, %s, %s)", (role, oid, col, p)
                ).fetchone()[0]:
                    problems.append(f"{role}: can {p} {name}.{col}")
    return problems


_STOP_TABLES = ("kill_switch", "kill_switch_stops", "kill_switch_clears")

# The right that clears or defeats a stop, per relation: flip or delete the legacy flag (UPDATE, DELETE, TRUNCATE),
# append a clear (INSERT), and TRIGGER on all three (a BEFORE INSERT trigger can swallow a stop, a trigger can
# be dropped). A column grant counts for UPDATE and INSERT (the only privileges a column can hold).
_CAN_CLEAR = """
WITH RECURSIVE want(relname, priv) AS (
    VALUES ('kill_switch', 'UPDATE'), ('kill_switch', 'DELETE'), ('kill_switch', 'TRUNCATE'),
           ('kill_switch', 'TRIGGER'), ('kill_switch_stops', 'TRIGGER'), ('kill_switch_clears', 'TRIGGER'),
           ('kill_switch_clears', 'INSERT')
), rel AS (
    SELECT c.oid, c.relacl, c.relowner, w.priv
    FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
         JOIN want w ON w.relname = c.relname
    WHERE n.nspname = pg_catalog.current_schema()
), acl AS (
    SELECT a.grantee FROM rel, pg_catalog.aclexplode(rel.relacl) a WHERE a.privilege_type = rel.priv
    UNION
    SELECT a.grantee FROM rel JOIN pg_catalog.pg_attribute att ON att.attrelid = rel.oid,
           pg_catalog.aclexplode(att.attacl) a
    WHERE att.attnum > 0 AND NOT att.attisdropped AND a.privilege_type = rel.priv
), outside AS (
    SELECT relowner AS oid FROM rel UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolsuper
), can AS (
    SELECT s.oid FROM (SELECT grantee AS oid FROM acl
                       UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = %(reset)s
                       UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE {creators}) s
    WHERE s.oid NOT IN (SELECT oid FROM outside)
    UNION
    SELECT m.member FROM pg_catalog.pg_auth_members m JOIN can ON m.roleid = can.oid
    WHERE m.member NOT IN (SELECT oid FROM outside) AND {usable}
)
SELECT name FROM (
    SELECT 'PUBLIC' AS name, 0 AS pos WHERE EXISTS (SELECT 1 FROM acl WHERE grantee = 0)
    UNION ALL
    SELECT r.rolname, 1 FROM pg_catalog.pg_roles r
    WHERE r.oid IN (SELECT oid FROM can) AND r.rolname IS DISTINCT FROM %(reset)s
) found ORDER BY pos, name
"""


# Below PostgreSQL 16: every non-superuser CREATEROLE login of the server, except the roles the operator vouches for.
_CREATORS = "(r.rolcreaterole AND r.rolname::text <> ALL(%(accepted)s::text[]))"


def _check_stop_relations(db) -> None:
    """The check below reads the grants of the three stop relations in `current_schema()`. It must find all three
    there, and their bare names must resolve to them: a search_path that names no schema, a schema without the
    tables, a missing table or a temporary table of the same name would leave the check reading nothing (or the
    wrong thing) and passing."""
    schema, path = db.execute(
        "SELECT pg_catalog.current_schema(), pg_catalog.current_setting('search_path')"
    ).fetchone()
    found = {}
    if schema:
        found = dict(
            db.execute(
                "SELECT c.relname, c.oid::int8 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n "
                "ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relkind IN ('r','p') "
                "AND c.relname = ANY(%s)",
                (schema, list(_STOP_TABLES)),
            ).fetchall()
        )
    missing = [t for t in _STOP_TABLES if t not in found]
    shadowed = [
        t
        for t in found
        if db.execute("SELECT pg_catalog.to_regclass(%s)::oid::int8", (t,)).fetchone()[0]
        != found[t]
    ]
    if not schema or missing or shadowed:
        raise ConfigError(
            f"cannot check who could clear a stop: the tables {', '.join(_STOP_TABLES)} must all be in the "
            f"schema the store uses, and they are not (schema {schema!r}, search_path {path!r}, missing "
            f"{missing or 'none'}, names that resolve to another relation {shadowed or 'none'}). Run migrate "
            "with a search_path whose first existing schema holds the stop tables"
        )


def who_else_can_clear(
    db, reset_role: str | None, accepted_admin_roles: tuple[str, ...] = ()
) -> list[str]:
    """Who, besides the reset role, could clear or defeat a stop IN THIS SCHEMA, read from the grants on this
    schema's `kill_switch` (UPDATE, DELETE, TRUNCATE), `kill_switch_clears` (INSERT) and the three stop tables
    (TRIGGER) only, so roles of other schemas or applications on the same server never change the answer. It
    raises ConfigError when the three tables are not all in `current_schema()` or a bare name resolves to
    something else: nothing to read is never a pass. Listed: every role those relations grant such a right to
    (table or column grant; `PUBLIC` is listed as PUBLIC), every role that is a member, directly or through other
    roles, with or without inheritance (a NOINHERIT member can SET ROLE), of such a role or of the reset role, and
    the roles that can hand themselves the reset role: below PostgreSQL 16 every non-superuser with CREATEROLE
    (except the roles the operator vouches for in `accepted_admin_roles`: they are left out of THIS listing only,
    never from a grant on the stop tables, never from a membership, never the reset role); from 16 a membership
    counts when its SET, INHERIT or ADMIN option is true, so the holder of the ADMIN option on the reset role (the
    login that created it has it) is listed. The listing is conservative: `usable` is judged per membership, not
    along the whole path, so a role whose chain mixes INHERIT-only and SET-only links is listed although it
    cannot reach the right (a rare, harmless false refusal).

    Outside the guarantee, never listed and never followed: the reset role itself, the owner of the relations
    (it can DROP and recreate them), superusers, managed-database admin roles that are not superusers
    (rds_superuser, azure_pg_admin, cloudsqlsuperuser; below PostgreSQL 16 listed only if they hold CREATEROLE),
    SECURITY DEFINER functions of another privileged role, and a role whose only path is membership in the owner,
    in a superuser, or in a PostgreSQL predefined role that holds no grant here (`pg_write_all_data` and the like
    can write every table of the server). Whoever hands out those memberships owns that risk;
    `effective_problems` still refuses the NAMED roles for them."""
    _check_stop_relations(db)
    # pg_auth_members has the option columns from PostgreSQL 16; before that every membership can SET ROLE and a
    # CREATEROLE login can grant any role to itself.
    new = db.execute(
        "SELECT pg_catalog.current_setting('server_version_num')::int >= 160000"
    ).fetchone()[0]
    usable = "(m.inherit_option OR m.set_option OR m.admin_option)" if new else "TRUE"
    creators = "FALSE" if new else _CREATORS
    query = _CAN_CLEAR.format(usable=usable, creators=creators)
    params = {"reset": reset_role, "accepted": list(accepted_admin_roles)}
    return [r[0] for r in db.execute(query, params).fetchall()]


def _paths(config_value: str) -> list[str]:
    return names_of(config_value)


def _path_rows(db, named: list[str]):
    """(role oid, role name, database name or None, setting) of every search_path default that reaches the named
    roles: the role-wide row, the row for this database, and the database-wide and server-wide rows."""
    return db.execute(
        "SELECT s.setrole, pg_catalog.pg_get_userbyid(s.setrole), d.datname, c "
        "FROM pg_catalog.pg_db_role_setting s CROSS JOIN LATERAL unnest(s.setconfig) c "
        "LEFT JOIN pg_catalog.pg_database d ON d.oid = s.setdatabase "
        "WHERE c LIKE 'search\\_path=%%' AND (s.setdatabase = 0 OR d.datname = current_database()) "
        "AND (s.setrole = 0 OR s.setrole IN (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = ANY(%s)))",
        (named,),
    ).fetchall()


def _effective_rows(rows, schema: str):
    """The rows that decide a named role's path in this database, and are not the schema. The row for this
    database overrides the role-wide row (PostgreSQL applies role-in-database, then role, then database, then
    server), so a role-wide row under a pinned row is shadowed and does not count."""
    pinned = {r[1] for r in rows if r[0] and r[2] and _paths(r[3].split("=", 1)[1]) == [schema]}
    return [
        r
        for r in rows
        if _paths(r[3].split("=", 1)[1]) != [schema] and not (r[0] and not r[2] and r[1] in pinned)
    ]


def check_role_settings(db, named: list[str]) -> list[str]:
    """Per-role and per-database `search_path` defaults that reach the named logins (`pg_db_role_setting`). A role
    may change its OWN default (`ALTER ROLE r SET search_path`), so a login could be sent to a decoy schema it owns
    and read a decoy stop table. A role row is a role's setting for EVERY database of the cluster, so it is never
    erased: for a role-wide row that is not the migrated schema this database gets
    `ALTER ROLE r IN DATABASE <this database> SET search_path = <schema>` (it takes precedence here, other databases
    keep their setting). A row for this database only is reset. Roles that are not named are never touched. A
    database-wide or server-wide row cannot be repaired for one role and is refused. The result is read back.
    Returns one line per change (role, database scope, old value, new value)."""
    schema, dbname_now = db.execute(
        "SELECT pg_catalog.current_schema(), pg_catalog.current_database()"
    ).fetchone()
    rows = _path_rows(db, named)
    changes = []
    wide = {r[1] for r in _effective_rows(rows, schema) if r[0] and not r[2]}
    for setrole, role, dbname, config in _effective_rows(rows, schema):
        if setrole == 0:
            raise ConfigError(
                f"a {'database-wide' if dbname else 'server-wide'} search_path default ({config}) reaches the "
                f"named roles and is not the schema {schema!r}: a login would read the stop state of another "
                "schema. Run ALTER DATABASE ... RESET search_path (or ALTER ROLE ALL ... RESET search_path) as a "
                "role that may"
            )
        old = config.split("=", 1)[1]
        if dbname:
            if role in wide:
                continue  # overwritten by the SET below
            stmt = sql.SQL("ALTER ROLE {} IN DATABASE {} RESET search_path").format(
                sql.Identifier(role), sql.Identifier(dbname)
            )
            note = f"role {role} in database {dbname}: search_path {old} reset (was the decoy of this database)"
        else:
            stmt = sql.SQL("ALTER ROLE {} IN DATABASE {} SET search_path = {}").format(
                sql.Identifier(role), sql.Identifier(dbname_now), sql.Identifier(schema)
            )
            note = (
                f"role {role} (role-wide default, kept for other databases) in database {dbname_now}: "
                f"search_path {old} -> {schema}"
            )
        try:
            db.execute(stmt)
        except errors.InsufficientPrivilege as exc:
            raise ConfigError(
                f"cannot change the search_path default of role {role} (it is {old}, not the schema {schema!r}): "
                "ALTER ROLE needs a migrate login with CREATEROLE and the ADMIN OPTION on that role "
                "(PostgreSQL 16 and later; before 16 CREATEROLE or superuser). Run migrate with such a login, or "
                f"run ALTER ROLE {role} IN DATABASE {dbname_now} SET search_path = {schema} as a role that may"
            ) from exc
        changes.append(note)
    if left := _effective_rows(_path_rows(db, named), schema):
        raise ConfigError(
            "a search_path default of a named role could not be repaired: "
            + ", ".join(f"{r[1]}: {r[3]}" for r in left)
        )
    return changes


def _maintainers(db, schema: str):
    """(stop table, grantee) for every MAINTAIN grant on a stop table other than the owner's own (PUBLIC as 'PUBLIC')."""
    return db.execute(
        "SELECT c.relname, CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_catalog.pg_get_userbyid(a.grantee) END "
        "FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace, "
        "pg_catalog.aclexplode(c.relacl) a WHERE n.nspname = %s AND c.relname = ANY(%s) "
        "AND a.privilege_type = 'MAINTAIN' AND a.grantee <> c.relowner ORDER BY 1, 2",
        (schema, list(_STOP_TABLES)),
    ).fetchall()


def _holds(db, role: str, schema: str, table: str, privilege: str) -> bool:
    """Whether the role holds the privilege on schema.table; the relation name is built with quote_ident, so a
    schema with capitals or special characters resolves to itself."""
    return db.execute(
        "SELECT pg_catalog.has_table_privilege(%s, "
        "(pg_catalog.quote_ident(%s) || '.' || pg_catalog.quote_ident(%s))::regclass, %s)",
        (role, schema, table, privilege),
    ).fetchone()[0]


def check_maintain(db, named: list[str]) -> None:
    """PostgreSQL 17 added MAINTAIN, which also lets its holder LOCK a table in any mode: a runtime role that held it
    (a grant, PUBLIC, or membership in pg_maintain) could take ACCESS EXCLUSIVE on a stop table and block every read
    of the stop. Every MAINTAIN grant on the three stop tables other than the owner's is revoked, and a named role
    that can still maintain them (PUBLIC cannot be revoked per role; pg_maintain is a membership) is refused. Before
    17 the privilege does not exist and is not named."""
    if (
        db.execute("SELECT pg_catalog.current_setting('server_version_num')::int").fetchone()[0]
        < 170000
    ):
        return
    schema = db.execute("SELECT pg_catalog.current_schema()").fetchone()[0]
    for table, grantee in _maintainers(db, schema):
        who = sql.SQL("PUBLIC") if grantee == "PUBLIC" else sql.Identifier(grantee)
        db.execute(
            sql.SQL("REVOKE MAINTAIN ON TABLE {}.{} FROM {}").format(
                sql.Identifier(schema), sql.Identifier(table), who
            )
        )
    if left := _maintainers(db, schema):
        raise ConfigError(
            "MAINTAIN (which can LOCK a table) is still held on the stop tables by "
            + ", ".join(f"{g} on {t}" for t, g in left)
            + ": REVOKE it as the owner of the tables"
        )
    for role in named:
        for table in _STOP_TABLES:
            if _holds(db, role, schema, table, "MAINTAIN"):
                raise ConfigError(
                    f"{role} holds MAINTAIN on {table} (through pg_maintain or a role it is a member of), so it "
                    "could LOCK the stop tables and block every read of the stop: remove that membership"
                )


def _excess_privileges(db, role: str) -> list[str]:
    """Effective privileges (inherited ones too) the role holds beyond SELECT on the `portal` relations."""
    extra = []
    for name, grant in GRANTS.items():
        if grant.kind == "sequence":
            privs, q = ("USAGE", "SELECT", "UPDATE"), "SELECT has_sequence_privilege(%s, %s, %s)"
        else:
            privs = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
            q = "SELECT has_table_privilege(%s, %s, %s)"
        allowed = {"SELECT"} if grant.portal else set()
        extra += [
            f"{name}:{p}"
            for p in privs
            if p not in allowed and db.execute(q, (role, name, p)).fetchone()[0]
        ]
    return extra


def _apply_release_function(db, release_role: str | None, others: list[str]) -> None:
    """EXECUTE on the release function: the release role gets it, every other named role loses it, and a named
    role that can still run it (through PUBLIC or a role it is a member of) is refused."""
    if db.execute("SELECT to_regprocedure(%s)", (RELEASE_FUNCTION,)).fetchone()[0] is None:
        return
    fn = sql.SQL(RELEASE_FUNCTION)
    # SECURITY DEFINER: the search path is pinned with the catalog first and the temp schema last, so neither a
    # temp table of the caller nor a writable schema can stand in for a money table or a catalog function.
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    try:
        db.execute(
            sql.SQL("ALTER FUNCTION {} SET search_path = pg_catalog, {}, pg_temp").format(
                fn, sql.Identifier(schema)
            )
        )
    except errors.InsufficientPrivilege as exc:
        owner = db.execute(
            "SELECT pg_get_userbyid(proowner) FROM pg_proc WHERE oid = to_regprocedure(%s)",
            (RELEASE_FUNCTION,),
        ).fetchone()[0]
        raise ConfigError(
            f"cannot pin the search path of {RELEASE_FUNCTION}: it is owned by {owner}, and only its owner (or a "
            f"member of that role) may alter it. Run migrate as {owner}."
        ) from exc
    for role in others:
        db.execute(sql.SQL("REVOKE ALL ON FUNCTION {} FROM {}").format(fn, sql.Identifier(role)))
    if release_role:
        db.execute(
            sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(fn, sql.Identifier(release_role))
        )
    for role in others:
        if db.execute(
            "SELECT has_function_privilege(%s, to_regprocedure(%s), 'EXECUTE')",
            (role, RELEASE_FUNCTION),
        ).fetchone()[0]:
            raise ConfigError(f"{role} can run {RELEASE_FUNCTION}: only the release role may")


def migrate(
    dsn: str,
    *,
    runtime_role: str | None = None,
    portal_role: str | None = None,
    purge_role: str | None = None,
    reset_role: str | None = None,
    release_role: str | None = None,
    no_roles: bool = False,
    iam_auth: bool = False,
    region: str | None = None,
    sslmode: str | None = None,
    sslrootcert: str | None = None,
    accepted_admin_roles: tuple[str, ...] = (),
    on_role_change: Callable[[str], None] | None = None,
) -> list[str]:
    """Apply pending migrations; return the versions applied by this call. With `runtime_role`, give it the
    privileges `GRANTS` lists (never TRUNCATE; DELETE only on the outbox and the purged evidence tables). With `portal_role`, SELECT on the
    relations marked `portal` and nothing else. With `release_role`, EXECUTE on the release function of 0008 and the audit append (nothing on the money tables). With `reset_role`, what `Grant.reset` lists: clear stops, turn the
    old flag off, append the reset to the audit chain, and nothing else. The ledger and the grant map are checked first: a bad file name,
    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database. A run that names no
    role is refused unless `no_roles=True` (CLI `--no-roles`): it would apply the schema and never look at who can
    clear a stop, and exit 0. Every search_path default of a named role that migrate changed is passed to
    `on_role_change` (role, database scope, old and new value) and logged (`hadavin_sdk.migrate`, warning).
    `accepted_admin_roles`: plain role names the operator vouches for (cannot grant the reset role to itself; for
    example a managed service's administrator). Below PostgreSQL 16 they are left out of the CREATEROLE listing and
    nowhere else; each one is logged at warning level (logger `hadavin_sdk.store`) and the command line prints
    them. It needs named roles, and a name that is also a named role is refused."""
    roles = (runtime_role, portal_role, purge_role, reset_role, release_role)
    for role in roles:
        if role is not None and (not _ROLE.fullmatch(role) or role in _FORBIDDEN_ROLES):
            raise ConfigError(f"not a plain database role name: {role!r}")
    named = [r for r in roles if r is not None]
    if len(set(named)) != len(named):
        raise ConfigError(
            "the runtime, portal, purge, reset and release roles must be different roles"
        )
    if no_roles and named:
        raise ConfigError("no_roles (--no-roles) says no role is named, and a role is named")
    accepted = tuple(accepted_admin_roles)
    if isinstance(accepted_admin_roles, str) or any(
        not _ROLE.fullmatch(a) or a in _FORBIDDEN_ROLES for a in accepted
    ):
        raise ConfigError(
            f"accepted_admin_roles must be plain database role names: {accepted_admin_roles!r}"
        )
    if accepted and not named:
        raise ConfigError(
            "accepted_admin_roles is only read when roles are named: it changes the who-else check"
        )
    if overlap := sorted(set(accepted) & set(named)):
        raise ConfigError(
            f"accepted_admin_roles must not name a role this command grants: {', '.join(overlap)}"
        )
    files = _migration_files()
    if problems := check_ledger(files) + check_grants(files):
        raise ConfigError("migrations are inconsistent: " + "; ".join(problems))
    if not named and not no_roles:
        raise ConfigError(
            "no role is named, so the stop-state check (who could clear a stop) would be skipped. Name the "
            "runtime, portal, purge and reset roles in ONE migrate command, or pass --no-roles to apply the "
            "schema without checking any role (the first install, before the roles exist)"
        )
    applied = []
    with (
        connect(
            dsn, iam_auth=iam_auth, region=region, sslmode=sslmode, sslrootcert=sslrootcert
        ) as db,
        db.transaction(),
    ):
        db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK,))
        db.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        done = {r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()}
        if gone := sorted(done - {p.stem for p in files}):
            raise ConfigError(
                f"applied migrations have no file in this release: {', '.join(gone)}. If a migration file was renamed "
                "and its tables already exist, rename the ledger row by hand (change the version of that row in the "
                "schema_migrations table to the new file name); if its content changed too, drop what it made and "
                "run migrate again"
            )
        for path in files:
            if path.stem in done:
                continue
            db.execute(path.read_text(encoding="utf-8"))  # a file shipped in this package
            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
            applied.append(path.stem)
        q = "SELECT pg_has_role(%s, %s, 'MEMBER')"  # a member keeps the other's rights, whatever we REVOKE
        for a in named:
            for b in named:
                if a != b and db.execute(q, (a, b)).fetchone()[0]:
                    raise ConfigError(
                        "the runtime, portal, purge, reset and release roles must not be members of each other"
                    )
        if runtime_role:
            _apply_grants(db, runtime_role, lambda g: g.runtime)
            if bad := effective_problems(db, runtime_role, lambda g: g.runtime if g else ""):
                raise ConfigError(
                    "the runtime role holds more than the grant map: " + "; ".join(bad[:20])
                )
        if purge_role:
            _apply_grants(db, purge_role, lambda g: g.purge, lambda g: g.purge_cols)
            if bad := effective_problems(
                db, purge_role, lambda g: g.purge if g else "", lambda g: g.purge_cols if g else ()
            ):
                raise ConfigError(
                    "the purge role holds more than the grant map: " + "; ".join(bad[:20])
                )
        if reset_role:
            _apply_grants(db, reset_role, lambda g: g.reset)
            if bad := effective_problems(db, reset_role, lambda g: g.reset if g else ""):
                raise ConfigError(
                    "the reset role holds more than the grant map: " + "; ".join(bad[:20])
                )
        if release_role:
            _apply_grants(db, release_role, lambda g: g.release)
            if bad := effective_problems(db, release_role, lambda g: g.release if g else ""):
                raise ConfigError(
                    "the release role holds more than the grant map: " + "; ".join(bad[:20])
                )
        _apply_release_function(db, release_role, [r for r in named if r != release_role])
        if portal_role:
            _apply_grants(db, portal_role, lambda g: "SELECT" if g.portal else "")
            if extra := _excess_privileges(db, portal_role):
                raise ConfigError(  # e.g. inherited from another role: REVOKE cannot take those away
                    f"the portal role holds privileges outside the portal grant map: {', '.join(extra)}"
                )
        if named:
            for note in check_role_settings(db, named):
                _log.warning("migrate changed a role setting: %s", note)
                if on_role_change:
                    on_role_change(note)
            check_maintain(db, named)
        if accepted:
            _LOG.warning(
                "migrate: administrator roles accepted by the operator, NOT checked as able to clear a stop "
                "(below PostgreSQL 16 only; a grant on the stop tables still lists them): %s",
                ", ".join(accepted),
            )
        if named and (others := who_else_can_clear(db, reset_role, accepted)):
            raise ConfigError(
                "roles other than the reset role could clear a stop (a right on kill_switch or "
                "kill_switch_clears, or membership in a role that holds one): "
                + ", ".join(others[:20])
                + ". Name the runtime, portal, purge and reset roles in ONE migrate command, and revoke the "
                "right or the membership of any other role. Below PostgreSQL 16 a role listed only because it holds "
                "CREATEROLE can be named with accepted_admin_roles (command line: --accept-admin-role) when you "
                "vouch that it cannot grant the reset role to itself (see docs/stop-state-runbook.md)"
            )
    return applied
