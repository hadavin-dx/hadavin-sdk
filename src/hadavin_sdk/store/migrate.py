"""Forward-only schema migrations for the Postgres store (`hadavin-sdk migrate`).

Run under a migration role, never by the runtime. Every pending `migrations/NNNN_*.sql` file is applied in one
transaction under a transaction-scoped advisory lock, so two concurrent runs apply each file once. Rollback =
restore the snapshot taken before migrating.

The file-name rules, the late-file and gone-name refusals and the SQL text rules live in `migration_numbers`
(no database library there); this module only calls them. Each file is read ONCE; the text that was scanned is
the text that is executed. After each file, in the same transaction, `migrate` reads back the database user
names (the current user and the session user), the replication-role setting, the search path, three settings that
change how SQL text is read, the two time limits, the transaction clock and id, the role memberships of the migration
roles (`pg_auth_members`: a role granted to a role inside a function body is found here, not by the statement rule),
the settings saved per database or per role (`pg_db_role_setting`) and every trigger in the migration schema (its
enabled state, its definition and the text of its function), and refuses if anything is LEFT changed (it cannot see a
change that a file makes and undoes before it ends, and it cannot undo what a hidden `COMMIT` or a second connection
(`dblink_exec` runs outside this transaction) already kept). The memberships and saved settings it compares are those
of the current user, the session user, the runtime, portal and purge roles and every role any of them is a member
of; a change to any other role (for example by another session on the same server) is not compared. Then it asks the
role questions below again, so a file cannot leave the migration role holding what the first check refused.
The migration role must NOT be a superuser and must not hold `CREATEROLE`, `CREATEDB` or `BYPASSRLS`: `migrate` reads
these four flags of the current user and of the session user right after it takes its lock and refuses the run if any
is set (a superuser can change what the read-back does not read). The `REPLICATION` attribute is not checked. There is
no switch to turn this check off.
Right after that, `migrate` refuses a schema in which a table, view, sequence or function THIS PACKAGE manages (a
relation in `GRANTS`, `schema_migrations`, or a function a migration file creates) is owned by a role the migration role
cannot act as (a database first built with a superuser login): it names the objects and prints the `ALTER ... OWNER TO`
lines that hand them over (runbook case (h)). Objects of another application in the same schema are never listed. Without
that, a later `ALTER TABLE` fails with "must be owner" and the `GRANT` lines do nothing without an error.

When `migrate` refuses, a database administrator repairs by hand (the full runbook, cases (a) to (h), is the section
"Migration repair steps" of CHANGELOG.md). Every hand step is a FILE of SQL run with `psql -X -v ON_ERROR_STOP=1 -f <file>`
and your own connection settings (never typed line by line, never a connection string in a text). The file starts with
`\\set ON_ERROR_STOP on`, then `SET search_path TO "<the schema migrate uses>";`, `BEGIN;`, the two `SET LOCAL` lines of
`RECIPE_TIMEOUTS` (`migration_numbers`: a lock limit and a statement limit; `migrate` sets the same two lines itself),
the advisory lock of `migrate`
(`SELECT pg_advisory_xact_lock(<MIGRATE_LOCK>);`, only while no `migrate` runs) and ends with `COMMIT;`; after every
`UPDATE schema_migrations` it holds a `DO` check that raises unless exactly one row with the new version exists and
none with the old one. A late file: use the recipe in the refusal message. A renamed file or ledger row: change the
row to the name of the one folder file with the same text after the number. A database newer than the code: run the
newer release; do not rename, drop or edit the ledger.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from psycopg import errors as pg_errors
from psycopg import sql

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.migration_numbers import (
    MIGRATE_LOCK,
    MIGRATIONS,
    RECIPE_TIMEOUTS,
    RELEASED_MANIFEST,
    STEM,
    TRIGGER_CHANGES,
    MigrationNumberError,
    check_ledger,
    escape_name,
    gone_message,
    lex,
    list_migration_files,
    order_problems,
    read_files,
    refused_statements,
    released_problems,
)
from hadavin_sdk.store.postgres import connect

# `MIGRATIONS` and `check_ledger` are listed on purpose: they live in `migration_numbers` (no database library there)
# and are re-exported so that existing imports from this module (`cli.py`, the tests) keep working.
__all__ = ["GRANTS", "MIGRATIONS", "Grant", "check_grants", "check_ledger", "migrate"]


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


_RW = "SELECT, INSERT, UPDATE"
_APPEND = "SELECT, INSERT"  # written once, never changed
# The one grant map. Audit rows and checkpoints are read and appended only (their triggers also refuse UPDATE,
# DELETE and TRUNCATE to any role); reconcile deletes an outbox row once it is in the chain. A later PR adds its
# relations here (`redaction_maps`, labels and reports, ...); the portal list never holds
# `redaction_maps`, `events`, `tick_state.detail` or secrets.
GRANTS: dict[str, Grant] = {
    "runs": Grant("table", _RW, portal=True, purge_cols=("run_id", "state", "updated_at")),
    "plans": Grant("table", _RW, portal=True),
    "gate_decisions": Grant("table", _APPEND, portal=True),
    "approval_requests": Grant("table", _RW, portal=True),
    "approval_decisions": Grant("table", _APPEND, portal=True),
    "dead_letters": Grant("table", _APPEND),
    "spend": Grant("table", _RW),
    "spend_month": Grant("table", _RW),
    "kill_switch": Grant("table", _RW),
    "tick_state": Grant("table", _RW),
    "audit_entries": Grant("table", _APPEND, portal=True),
    "audit_checkpoints": Grant("table", _APPEND, portal=True),
    "audit_outbox": Grant("table", "SELECT, INSERT, DELETE"),
    # Append and purge only (no UPDATE); `redaction_maps` is never portal-readable.
    # The runtime role appends and reads evidence; only the purge role (its own identity) deletes it.
    "tool_calls": Grant(
        "table", _APPEND, purge="DELETE", purge_cols=("call_id", "run_id", "created_at")
    ),
    "redaction_maps": Grant("table", _RW, purge="DELETE", purge_cols=("run_id", "updated_at")),
    "approval_decisions_seq_seq": Grant("sequence", "USAGE"),
    "dead_letters_seq_seq": Grant("sequence", "USAGE"),
}
_ROLE = re.compile(r"[a-z_][a-z0-9_]{0,62}")
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
    return list_migration_files(folder)


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


def _scan(
    paths: list[Path], texts: dict[Path, str] | None = None
) -> tuple[dict[str, str], list[str]]:
    """(relation name -> kind, unread statements). Kinds: every table, view and serial-column sequence the
    migrations create. A statement that could create a relation or sequence in a way this scan does not read
    (quoted or schema-qualified name, UNLOGGED/TEMP/FOREIGN tables, CREATE SEQUENCE, IDENTITY, ADD COLUMN ...
    SERIAL) is returned as a problem, never skipped: the guard fails closed. With `texts` the scan reads that text
    (the text `migrate` will execute); without it each file is read. Comments are removed by the single-pass lexer
    and every quoted part is kept, so a statement inside a string or a `$$` body is still seen."""
    found: dict[str, str] = {}
    unread: list[str] = []
    for path in paths:
        raw = texts[path] if texts is not None else path.read_text(encoding="utf-8")
        text, lexer_problem = lex(raw, keep_quoted=True)
        if lexer_problem:
            unread.append(f"{path.name}: {lexer_problem}")
        unread += [
            f"{path.name}: {reason}"
            for reason in refused_statements(raw)
            if reason != lexer_problem
        ]
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


def check_grants(paths: list[Path], texts: dict[Path, str] | None = None) -> list[str]:
    """Problems between the migrations and `GRANTS`: a relation they create with no entry (it would get no grant
    and fail at runtime), an entry for a relation no migration creates, or an entry of the wrong kind."""
    created, problems = _scan(paths, texts)
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
        rel = sql.Identifier(
            schema, name
        )  # qualified: the search path cannot point it at another relation
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
# PostgreSQL 17 added the table privilege MAINTAIN (VACUUM, ANALYZE, REINDEX, CLUSTER, REFRESH MATERIALIZED VIEW,
# LOCK TABLE). PostgreSQL 16 refuses the name ("unrecognized privilege type"), so it is asked about only from 17.
_SERVER_VERSION_SQL = "SELECT current_setting('server_version_num')::int"
_MAINTAIN_FROM = 170000


def _table_privs(db) -> tuple[str, ...]:
    row = db.execute(_SERVER_VERSION_SQL).fetchone()
    return _TABLE_PRIVS + (("MAINTAIN",) if row and row[0] >= _MAINTAIN_FROM else ())


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
    table_privs = _table_privs(db)
    if db.execute("SELECT has_schema_privilege(%s, %s, 'CREATE')", (role, schema)).fetchone()[0]:
        problems.append(f"{role}: can CREATE in schema {schema}")
    rels = db.execute(
        "SELECT c.oid, c.relname, c.relkind, pg_get_userbyid(c.relowner) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relkind IN ('r','p','v','m','S')",
        (schema,),
    ).fetchall()
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
        for p in table_privs:
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


# SHA-256 of every released migration file (forward-only: a released file is never edited, renumbered or deleted).
# It ships with the package, so `migrate` itself can refuse a changed file; add a row when a release is cut.
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _no_duplicate_names(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """json would silently keep the LAST of two equal names: a second, edited hash would hide the first."""
    names = [k for k, _ in pairs]
    if len(set(names)) != len(names):
        raise ValueError(
            f"the name {next(n for n in names if names.count(n) > 1)!r} is written twice"
        )
    return dict(pairs)


def _released_manifest() -> dict[str, str]:
    try:
        data = json.loads(
            RELEASED_MANIFEST.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_names
        )
    except (OSError, ValueError) as e:
        raise ConfigError(f"the list of released migration files cannot be read: {e}") from e
    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data.items()
    ):
        raise ConfigError("the list of released migration files is not a name -> SHA-256 table")
    for name, value in data.items():
        if not _SHA256.fullmatch(value):
            raise ConfigError(
                f"the list of released migration files has no SHA-256 (64 hex digits) for {name!r}"
            )
    return data


# What the read-back reads after each file (module constants: the tests answer them by exact text).
# The eleven values are compared with the values saved before the first file; `transaction_timestamp()` and
# `txid_current()` DETECT a COMMIT the text rules did not see (a COMMIT starts a new transaction). They cannot undo it:
# what was committed before is kept; the run is stopped and the refusal says so.
_READBACK_VALUES = (
    "current_user",
    "session_user",
    "session_replication_role",
    "search_path",
    "standard_conforming_strings",
    "backslash_quote",
    "client_encoding",
    "lock_timeout",
    "statement_timeout",
    "transaction_timestamp",
    "txid_current",
)
_READBACK_VALUES_SQL = (
    "SELECT current_user, session_user, current_setting('session_replication_role'), "
    "current_setting('search_path'), current_setting('standard_conforming_strings'), "
    "current_setting('backslash_quote'), current_setting('client_encoding'), "
    "current_setting('lock_timeout'), current_setting('statement_timeout'), "
    "transaction_timestamp(), txid_current()"
)
# The four flags that make a migration role too powerful (a superuser can change what the read-back does not read).
_ROLE_FLAGS = ("rolsuper", "rolcreaterole", "rolcreatedb", "rolbypassrls")
# `session_user` too: a login that is a superuser and then runs `SET ROLE` to a plain role is still a superuser (a file can
# undo the switch inside a function body).
_ROLE_FLAGS_SQL = (
    "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles "
    "WHERE rolname IN (current_user, session_user)"
)
# The roles whose memberships and saved settings the read-back compares: `own` = the current user, the session user and
# the named runtime, portal and purge roles (parameter 1: their names); `closure` = every role the current user, the
# session user or a named role is a member of, directly or through other roles (`pg_has_role ... 'MEMBER'`). The query list is
# server-wide (`pg_auth_members` and `pg_db_role_setting` hold every role of the server), so rows about other roles are
# left out: another session changing an unrelated role while a file runs must not stop the run.
# Settings saved per database or per role (`ALTER ROLE ... SET`, `ALTER DATABASE ... SET`): they apply to NEW sessions,
# so a file that changes them changes what the next connection runs with.
_READBACK_SETTINGS_SQL = (
    "WITH named AS (SELECT oid FROM pg_roles WHERE rolname = ANY(%s::text[]) AND NOT rolsuper), "
    "scope AS (SELECT r.oid, (r.rolname IN (current_user, session_user) OR r.oid IN (SELECT oid FROM named)) AS own, "
    "(pg_has_role(current_user, r.oid, 'MEMBER') OR pg_has_role(session_user, r.oid, 'MEMBER') "
    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, 'MEMBER'))) AS closure "
    "FROM pg_roles r) "
    "SELECT coalesce(d.datname, ''), coalesce(r.rolname, ''), s.setconfig::text FROM pg_db_role_setting s "
    "LEFT JOIN pg_database d ON d.oid = s.setdatabase LEFT JOIN pg_roles r ON r.oid = s.setrole "
    "WHERE s.setdatabase IN (0, (SELECT oid FROM pg_database WHERE datname = current_database())) "
    "AND (s.setrole = 0 OR s.setrole IN (SELECT oid FROM scope WHERE own OR closure))"
)
# Role memberships (who is a member of whom, with the grant options): the one thing a `$$` function body can change
# that no statement-start rule sees (`GRANT r TO s` inside a function, then `SELECT f();`). Names, not OIDs. Only the
# memberships of the roles in scope (what each of them is a member of) and the members of the `own` roles.
_READBACK_MEMBERS_SQL = (
    "WITH named AS (SELECT oid FROM pg_roles WHERE rolname = ANY(%s::text[]) AND NOT rolsuper), "
    "scope AS (SELECT r.oid, (r.rolname IN (current_user, session_user) OR r.oid IN (SELECT oid FROM named)) AS own, "
    "(pg_has_role(current_user, r.oid, 'MEMBER') OR pg_has_role(session_user, r.oid, 'MEMBER') "
    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, 'MEMBER'))) AS closure "
    "FROM pg_roles r) "
    "SELECT m.roleid::regrole::text, m.member::regrole::text, "
    "(to_jsonb(m) - 'oid' - 'roleid' - 'member')::text FROM pg_auth_members m "
    "WHERE m.member IN (SELECT oid FROM scope WHERE own OR closure) OR m.roleid IN (SELECT oid FROM scope WHERE own)"
)
# Triggers of the migration schema only (the schema `current_schema()` names now); internal ones are skipped. Per
# trigger: its table's id (only to tell a renamed table from a new one), its enabled state, its full definition and
# its function's source text, the function's security mode, owner and saved settings (a function replaced
# under the same name keeps the trigger name but not what it does).
_READBACK_TRIGGERS_SQL = (
    "SELECT t.tgname, t.tgenabled, c.relname, n.nspname, t.tgrelid::bigint, pg_get_triggerdef(t.oid), "
    "p.prosrc, p.prosecdef, pg_get_userbyid(p.proowner), p.proconfig::text FROM pg_trigger t "
    "JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
    "LEFT JOIN pg_proc p ON p.oid = t.tgfoid "
    "WHERE NOT t.tgisinternal AND n.nspname = current_schema()"
)
# The parts of a saved trigger, in the order of its saved tuple (after the name, table and schema).
_TRIGGER_PARTS = (
    "enabled state",
    "definition",
    "function text",
    "function security mode",
    "function owner",
    "function settings",
)

# Trigger changes a reviewed list allows (see `_trigger_changes`). It ships next to the released-files list.

_TRIGGER_NAME = r"[A-Za-z_][A-Za-z0-9_$]*"
_TRIGGER_TABLE = re.compile(rf"(?:({_TRIGGER_NAME})\.)?({_TRIGGER_NAME})")


@dataclass(frozen=True)
class TriggerChange:
    """One reviewed entry: the migration file (name without `.sql`), the table (and the schema, when the entry names
    one; an entry with no schema means the schema `migrate` works in), the trigger, and the disabled or replica-only
    state (`D` or `R`) the entry allows (empty: none; such a state is refused)."""

    migration: str
    schema: str | None
    table: str
    trigger: str
    state: str = ""


def _trigger_changes() -> frozenset[TriggerChange]:
    """The reviewed list of triggers a migration file may change. The file is a JSON list of objects with the keys
    `migration`, `table` (`name` or `schema.name`), `trigger` and `reason` (one line of plain words), and optionally
    `enabled_state` (`D` or `R`: the one disabled or replica-only state this file may change an EXISTING trigger to; a
    trigger the file creates is never allowed to be disabled or replica-only). It is empty
    today. Anything else (a bad shape, a second entry for the same file, table and trigger, an empty or multi-line
    reason) is a `ConfigError`: a malformed list must never mean "allow"."""
    try:
        data = json.loads(TRIGGER_CHANGES.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ConfigError(f"the list of allowed trigger changes cannot be read: {e}") from e
    if not isinstance(data, list):
        raise ConfigError("the list of allowed trigger changes must be a JSON list")
    required = {"migration", "table", "trigger", "reason"}
    found: dict[tuple, TriggerChange] = {}
    for i, entry in enumerate(data):
        where = f"the list of allowed trigger changes, entry {i}"
        if (
            not isinstance(entry, dict)
            or not required <= set(entry)
            or set(entry) - required - {"enabled_state"}
        ):
            raise ConfigError(
                f"{where}, must have the keys migration, table, trigger and reason (and may have enabled_state)"
            )
        if not all(isinstance(v, str) and v.strip() for v in entry.values()):
            raise ConfigError(f"{where}, has an empty or non-text value")
        if not STEM.fullmatch(entry["migration"]):
            raise ConfigError(f"{where}, names a migration that is not a file name without .sql")
        table = _TRIGGER_TABLE.fullmatch(entry["table"])
        if table is None:
            raise ConfigError(f"{where}, has a table that is not `name` or `schema.name`")
        if escape_name(entry["trigger"]) != entry["trigger"]:
            raise ConfigError(f"{where}, has a trigger name with a control or unusual character")
        if "\n" in entry["reason"] or "\r" in entry["reason"]:
            raise ConfigError(f"{where}, has a reason of more than one line")
        state = entry.get("enabled_state", "")
        if state not in ("", "D", "R"):
            raise ConfigError(f"{where}, has an enabled_state that is not D or R")
        change = TriggerChange(
            entry["migration"], table.group(1), table.group(2), entry["trigger"], state
        )
        identity = (change.migration, change.schema, change.table, change.trigger)
        if identity in found:
            raise ConfigError(
                f"{where}, repeats {change.migration} / {entry['table']} / {change.trigger}"
            )
        found[identity] = change
    return frozenset(found.values())


def _listed(changes: frozenset[TriggerChange], key: tuple[str, str, str]) -> TriggerChange | None:
    """The reviewed entry for the trigger `key` = (schema, table, trigger name), if there is one."""
    return next(
        (
            c
            for c in changes
            if c.table == key[1] and c.trigger == key[2] and c.schema in (None, key[0])
        ),
        None,
    )


@dataclass(frozen=True)
class _Saved:
    values: tuple
    triggers: dict  # (schema, table, tgname) -> (tgenabled, definition, function text, security mode, owner, settings)
    members: frozenset = frozenset()  # (role, member, other columns as text)
    settings: frozenset = frozenset()  # (database, role, settings as text) from pg_db_role_setting
    relids: dict = field(
        default_factory=dict
    )  # the same keys -> the table's id (tells a renamed table from a new one)


def _read_back(db, named=()) -> _Saved:
    values = tuple(db.execute(_READBACK_VALUES_SQL).fetchone())
    triggers, relids = {}, {}
    for name, enabled, table, schema, relid, *detail in db.execute(
        _READBACK_TRIGGERS_SQL
    ).fetchall():
        triggers[(schema, table, name)] = (enabled, *detail)
        relids[(schema, table, name)] = relid
    scope = (list(named),)
    members = frozenset(tuple(r) for r in db.execute(_READBACK_MEMBERS_SQL, scope).fetchall())
    settings = frozenset(tuple(r) for r in db.execute(_READBACK_SETTINGS_SQL, scope).fetchall())
    return _Saved(values, triggers, members, settings, relids)


# The one example of a plain migration role (no password, no secret: the administrator adds the login method that
# fits the database). `<schema>` is the schema `migrate` works in.
PLAIN_MIGRATION_ROLE_SQL = (
    "CREATE ROLE migration_role LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS NOREPLICATION; "
    "GRANT CREATE ON SCHEMA <schema> TO migration_role; "
    "GRANT USAGE ON SCHEMA <schema> TO migration_role WITH GRANT OPTION;"
)


# A plain role can still borrow rights by being a member of a role that holds one of the four flags or is a built-in
# server role (every role whose name starts with `pg_`, for example `pg_execute_server_program`, which runs programs
# on the server, and `pg_write_server_files`; only `pg_database_owner` is allowed). The member can `SET ROLE` to it, or
# uses its rights at once when it inherits. `pg_has_role(..., 'MEMBER')` is true for either way, direct or through other
# roles. Checked for `current_user` and `session_user`.
_BORROWED_ROLES_SQL = (
    "SELECT r.rolname FROM pg_roles r WHERE (r.rolsuper OR r.rolcreaterole OR r.rolcreatedb OR r.rolbypassrls "
    "OR (left(r.rolname, 3) = 'pg_' AND r.rolname <> 'pg_database_owner')) "
    "AND r.rolname NOT IN (current_user, session_user) "
    "AND (pg_has_role(current_user, r.oid, 'MEMBER') OR pg_has_role(session_user, r.oid, 'MEMBER')) "
    "ORDER BY r.rolname"
)
# Rights to change server settings (PostgreSQL 15 and later keep them in `pg_parameter_acl`): a grant such as
# `GRANT SET ON PARAMETER session_replication_role` lets a file change what the checks rely on.
_PARAMETER_TABLE_SQL = "SELECT to_regclass('pg_parameter_acl') IS NOT NULL"
# Asked of the current user, the session user and every role either is a member of (a role that does not inherit still
# lets its member `SET ROLE` to it).
_PARAMETER_GRANTS_SQL = (
    "SELECT DISTINCT a.parname FROM pg_parameter_acl a, pg_roles r "
    "WHERE (r.rolname IN (current_user, session_user) OR pg_has_role(current_user, r.oid, 'MEMBER') "
    "OR pg_has_role(session_user, r.oid, 'MEMBER')) "
    "AND (has_parameter_privilege(r.oid, a.parname, 'SET') OR has_parameter_privilege(r.oid, a.parname, 'ALTER SYSTEM')) "
    "ORDER BY 1"
)


def _refuse_privileged_role(db) -> None:
    """The migration role must hold none of the four flags of `_ROLE_FLAGS` (checked with the live flags of the current user)."""
    rows = db.execute(_ROLE_FLAGS_SQL).fetchall()
    if not rows:
        raise ConfigError("migrate cannot read the flags of its own database role")
    held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows)]
    if held:
        raise ConfigError(
            "the migration role must not be a superuser and must not hold CREATEROLE, CREATEDB or BYPASSRLS, "
            f"but it holds: {', '.join(held)}. Run migrate with a plain role that holds none of them. A database "
            "administrator creates one once, with SQL such as: "
            f"{PLAIN_MIGRATION_ROLE_SQL}"
        )
    if borrowed := [r[0] for r in db.execute(_BORROWED_ROLES_SQL).fetchall()]:
        raise ConfigError(
            "the migration role is a member of a role that is a superuser, holds CREATEROLE, CREATEDB or BYPASSRLS, "
            f"or is a built-in server role ({', '.join(_label(b) for b in borrowed[:20])}), so it could use those rights. "
            "Remove the membership (REVOKE <that role> FROM <the migration role>) or run migrate with a plain role "
            "that is a member of none of them."
        )
    row = db.execute(_PARAMETER_TABLE_SQL).fetchone()
    if row and row[0] and (params := [r[0] for r in db.execute(_PARAMETER_GRANTS_SQL).fetchall()]):
        raise ConfigError(
            "the migration role may change server settings it must not change "
            f"({', '.join(_label(x) for x in params[:20])}): a grant on a parameter lets a file change what the checks "
            "rely on. Remove the grant (REVOKE SET, ALTER SYSTEM ON PARAMETER <name> FROM <the migration role>)."
        )


# Objects THIS PACKAGE manages in the migration schema (the relations in `GRANTS`, `schema_migrations`, and the functions
# the migration files create: `_managed_names`; parameters 1 and 2) that the migration role cannot change because another
# role owns them (it is not that role and is not a member of it that inherits its rights: `pg_has_role(..., 'USAGE')`).
# Tables and functions of another application in the same schema are not looked at. Such an object makes a later
# `ALTER TABLE` or `CREATE OR REPLACE FUNCTION` fail with "must be owner of ...", and makes the `GRANT` and `REVOKE` of
# `migrate` do nothing without an error. A database first built by a superuser login (the usual start of a demo) is in
# this state. Objects that belong to an installed extension are skipped (the owner of those is the extension's
# business). A sequence that belongs to a column or is an identity sequence goes with its table, so only the table is
# listed; a partition has an automatic dependency on its parent too, but it is a table of its own and is listed.
# Columns: what ('r' relation, 'f' function), kind (relkind or prokind), name, owner, argument list of a function.
_FOREIGN_OWNED_SQL = (
    "SELECT 'r', c.relkind::text, c.relname, pg_get_userbyid(c.relowner), '' FROM pg_class c "
    "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = current_schema() "
    "AND c.relkind IN ('r','p','v','m','S','f') AND c.relname = ANY(%s::text[]) "
    "AND NOT pg_has_role(current_user, c.relowner, 'USAGE') "
    "AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_class'::regclass AND d.objid = c.oid "
    "AND d.deptype = 'e') "
    "AND (c.relkind <> 'S' OR NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_class'::regclass "
    "AND d.objid = c.oid AND d.deptype IN ('a','i'))) "
    "UNION ALL SELECT 'f', p.prokind::text, p.proname, pg_get_userbyid(p.proowner), "
    "pg_get_function_identity_arguments(p.oid) FROM pg_proc p "
    "JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = current_schema() "
    "AND p.proname = ANY(%s::text[]) AND NOT pg_has_role(current_user, p.proowner, 'USAGE') "
    "AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_proc'::regclass AND d.objid = p.oid "
    "AND d.deptype = 'e') ORDER BY 1, 3, 5"
)
_OWNER_WORD = {
    "r": "TABLE",
    "p": "TABLE",
    "v": "VIEW",
    "m": "MATERIALIZED VIEW",
    "S": "SEQUENCE",
    "f": "FOREIGN TABLE",
}
_FUNCTION_WORD = {"f": "FUNCTION", "p": "PROCEDURE", "a": "AGGREGATE", "w": "FUNCTION"}
_SCHEMA_USAGE_SQL = "SELECT has_schema_privilege(%s, current_schema(), 'USAGE')"
_FOREIGN_OWNED_SHOWN = 20  # names in the message; every statement is printed


# The parts of a `CREATE FUNCTION` name, as PostgreSQL reads them: a quoted name (`""` inside is one quote) or a plain
# name (letters, digits, `_` and `$`; it does not start with a digit). A schema before the dot is skipped.
_QUOTED_NAME = r'"(?:[^"]|"")+"'
_QUOTED_NAME_BODY = r'"((?:[^"]|"")+)"'
_PLAIN_NAME = r"\w[\w$]*"
_SCHEMA_DOT = rf"(?:(?:{_QUOTED_NAME}|{_PLAIN_NAME})\s*\.\s*)?"
# Only at the start of a statement (the text has no comments, and a string is not a statement), so a
# `CREATE FUNCTION` that is only written inside a string is not read as a name.
_FUNCTION_CREATE = re.compile(
    rf"(?:\A|;)\s*CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+{_SCHEMA_DOT}(?:{_QUOTED_NAME_BODY}|({_PLAIN_NAME}))",
    re.IGNORECASE,
)


def _fold(name: str) -> str:
    """How PostgreSQL folds a plain name: only the letters A to Z become lower case (not the letters of other scripts
    that Python's `lower` also changes)."""
    return "".join(c.lower() if "A" <= c <= "Z" else c for c in name)


def _managed_names(texts) -> list[str]:
    """The names this package manages in its schema: every relation in `GRANTS` (`check_grants` makes these exactly the
    relations the migration files create), `schema_migrations`, and every function a migration file creates or
    replaces (a file can create no type or domain: the guard refuses `CREATE TYPE` and `CREATE DOMAIN`). `texts` are the
    file texts `migrate` executes. Sorted, lower case where the server folds the name."""
    names = set(GRANTS) | {"schema_migrations"}
    for raw in texts:
        text, _problem = lex(raw, keep_quoted=True)
        for m in _FUNCTION_CREATE.finditer(text):
            # a quoted name keeps its case and its characters (`""` is one quote); a plain one is folded to lower case
            names.add(
                m.group(1).replace('""', '"') if m.group(1) is not None else _fold(m.group(2))
            )
    return sorted(names)


def _refuse_foreign_owned(db, managed) -> None:
    """Refuse a run whose migration role cannot change what this package manages in the schema (`managed`, see
    `_managed_names`; the objects of another application in the schema are not looked at; see `_FOREIGN_OWNED_SQL`). The
    message names the objects (at most `_FOREIGN_OWNED_SHOWN`), their owners, and prints the SQL that hands every one
    of them to the migration role. A statement is printed only when every name in it is plain: another role owns the
    object and chose its name, so a name with a control or unusual character is not copied into a line that a person
    runs; for such an object the message says a person must write the statement by hand."""
    rows = db.execute(_FOREIGN_OWNED_SQL, (list(managed), list(managed))).fetchall()
    if not rows:
        return
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    me = db.execute("SELECT current_user").fetchone()[0]
    names, statements, by_hand = [], [], []
    for what, kind, name, owner, args in rows:
        if len(names) < _FOREIGN_OWNED_SHOWN:
            names.append(f"{_label(name)} (owner {_label(owner)})")
        plain = all(escape_name(x) == x for x in (name, args, schema, me))
        if not plain:
            by_hand.append(_label(name))
            continue
        ident = sql.Identifier(schema, name).as_string(db)
        to = sql.Identifier(me).as_string(db)
        if what == "f":
            signature = args if args or kind != "a" else "*"
            statements.append(
                f"ALTER {_FUNCTION_WORD.get(kind, 'FUNCTION')} {ident}({signature}) OWNER TO {to};"
            )
        else:
            statements.append(f"ALTER {_OWNER_WORD[kind]} {ident} OWNER TO {to};")
    more = len(rows) - len(names)
    hand = (
        f" A person must write the statement for {', '.join(by_hand[:20])} by hand (its name holds a character "
        "that is not copied into a printed line)."
        if by_hand
        else ""
    )
    raise ConfigError(
        f"the migration role {_label(me)} cannot change {len(rows)} object(s) of this package in schema {_label(schema)} "
        f"that another role owns: {'; '.join(names)}{f'; and {more} more' if more > 0 else ''}. A later migration "
        "that alters one of them would fail with 'must be owner', and the grants of migrate would do nothing without "
        "an error. Nothing was changed. A database administrator hands the objects to the migration role once, "
        "connected as a superuser or as a role that is a member of both the old owner and the migration role (objects of "
        "other applications in the schema are not listed and need no change; but a table of ANOTHER application that "
        "has the same name as one of this package's tables, for example spend or runs, looks the same here: do not "
        "hand that one over, point migrate at another schema instead; the same goes for a function: it is matched by "
        "name, so read the text of each listed function first and hand it over only when it is this package's own "
        "code, because the migration role would then own, and run, it), "
        "with a file of SQL run as in CHANGELOG.md, Migration repair steps, case (h): "
        + " ".join(statements)
        + hand
    )


def _refuse_unusual_strings(saved: _Saved) -> None:
    """The lexer reads strings as `standard_conforming_strings = on` does; any other start value is refused."""
    value = saved.values[_READBACK_VALUES.index("standard_conforming_strings")]
    if value != "on":
        raise ConfigError(
            f"standard_conforming_strings is {value!r} for this session; migrate needs 'on' "
            "(the file checks read strings the way 'on' does)"
        )


def _where(db_name: str) -> str:
    """The database part of a saved setting: an empty name means the setting holds in every database."""
    return f"database {_label(db_name)}" if db_name else "every database"


def _membership_words(rest: str) -> str:
    """The columns of a membership row (the JSON of `pg_auth_members` without the role and member) in words: whether the
    member may pass the role on, uses its rights at once and may `SET ROLE` to it. A column this server does not have
    (the last two are new in PostgreSQL 16) is left out; a text that is not JSON is shown as a label."""
    try:
        cols = json.loads(rest)
    except ValueError:
        return _label(rest)
    if not isinstance(cols, dict):
        return _label(rest)
    words = []
    for key, yes, no in (
        ("admin_option", "with grant option", "without grant option"),
        ("inherit_option", "uses its rights at once", "does not use its rights unless it switches"),
        ("set_option", "may switch to it", "may not switch to it"),
    ):
        if key in cols:
            words.append(yes if cols[key] else no)
    return ", ".join(words) or "no further columns"


def _label(*names: str) -> str:
    """Names of database objects for a message: control characters are written as escapes."""
    return ".".join(escape_name(n) for n in names)


def _check_read_back(
    db,
    saved: _Saved,
    file_name: str,
    allowed_triggers: frozenset[TriggerChange] = frozenset(),
    named=(),
) -> _Saved:
    """Read again after `file_name` and compare. The eleven values in `_READBACK_VALUES` (the user names and settings,
    the two time limits, then the transaction clock and id) must equal the values saved before the first file. A trigger
    that existed before the file must be unchanged in every part of `_TRIGGER_PARTS` (enabled state, definition,
    function text, security mode, owner, settings): `O` to `A` is a change too, and so is a renamed table. A trigger
    the file creates must not be disabled (`D`) or replica-only (`R`). A trigger with an entry in `allowed_triggers` (the reviewed
    list `migrations_trigger_changes.json`, an entry for this file, this table and this trigger) may change; it may still
    not disappear, and it may not be left disabled (`D`) or replica-only (`R`) unless the entry names that state. The set of
    role memberships and the saved per-database and per-role settings must equal the saved ones. Refuses with every
    difference named: a trigger change is reported as a trigger change, not as a changed session. `named` are the runtime, portal and purge roles: with the current user, the session user and
    the roles they are members of they are the only roles whose memberships and saved settings are compared (the server
    holds every role, and another session may change an unrelated one while the file runs). Returns the trigger
    state just read (the base for the next file); the saved values stay those of the start."""
    now = _read_back(db, named)
    session = [
        f"{item} was {old!a} and is now {new!a}"
        for item, old, new in zip(_READBACK_VALUES, saved.values, now.values, strict=True)
        if old != new
    ]
    triggers: list[str] = []
    for key, before in sorted(saved.triggers.items(), key=lambda kv: str(kv[0])):
        after = now.triggers.get(key)
        label = _label(key[0], key[1], key[2])
        entry = _listed(allowed_triggers, key)
        allowed = entry is not None
        if after is None:
            relid = saved.relids.get(key)
            new_home = next(  # the same trigger on the same table id under another table name: a renamed table
                (
                    k
                    for k in now.triggers
                    if relid is not None
                    and k[2] == key[2]
                    and k not in saved.triggers
                    and now.relids.get(k) == relid
                ),
                None,
            )
            if new_home is None:
                triggers.append(f"trigger {label} no longer exists")
            elif not allowed:
                triggers.append(
                    f"trigger {label}: its table was renamed from {_label(key[1])} to {_label(new_home[1])}"
                )
        elif after != before and not allowed:
            changed = [n for n, o, a in zip(_TRIGGER_PARTS, before, after, strict=True) if o != a]
            triggers.append(f"trigger {label} changed: {', '.join(changed)}")
        elif after[0] != before[0] and after[0] in ("D", "R") and after[0] != entry.state:
            triggers.append(
                f"trigger {label} is left {'disabled' if after[0] == 'D' else 'replica-only'}, "
                "which its list entry does not name (enabled_state)"
            )
    for key, (enabled, *_rest) in sorted(now.triggers.items(), key=lambda kv: str(kv[0])):
        if key not in saved.triggers and enabled in ("D", "R"):
            triggers.append(
                f"trigger {_label(key[0], key[1], key[2])} is created "
                f"{'disabled' if enabled == 'D' else 'replica-only'}"
            )
    # Only the memberships in scope (the `scope` part of the two queries) are compared. One of them changed by another session while the
    # file runs is still reported here (a false refusal; run migrate again), hence the wording.
    members = [
        f"role {_label(role)} has a new member {_label(member)} ({_membership_words(rest)})"
        for role, member, rest in sorted(now.members - saved.members)
    ]
    members += [
        f"role {_label(role)} lost the member {_label(member)} ({_membership_words(rest)})"
        for role, member, rest in sorted(saved.members - now.members)
    ]
    session += [
        f"saved setting in {_where(db_name)} for role {_label(role)} is new ({_label(conf)})"
        for db_name, role, conf in sorted(now.settings - saved.settings)
    ]
    session += [
        f"saved setting in {_where(db_name)} for role {_label(role)} is gone ({_label(conf)})"
        for db_name, role, conf in sorted(saved.settings - now.settings)
    ]
    if session or triggers or members:
        parts = []
        if session:
            parts.append("left the database session changed: " + "; ".join(session))
        if members:
            parts.append(
                "a role membership changed while the file ran (it may be another session; run migrate again): "
                + "; ".join(members)
            )
        if triggers:
            parts.append(
                "changed a trigger: "
                + "; ".join(triggers)
                + ". A trigger change is refused unless this file, this table and this trigger are named, with a reason, in "
                "migrations_trigger_changes.json next to the released-files list (a reviewed change of the package)"
            )
        raise ConfigError(f"migration {escape_name(file_name)} " + ". It also ".join(parts))
    return _Saved(saved.values, now.triggers, saved.members, saved.settings, now.relids)


def _members_of_each_other(db, named) -> bool:
    """True when two of the named roles are members of each other's rights (a member keeps the other's rights, whatever
    migrate REVOKEs)."""
    q = "SELECT pg_has_role(%s, %s, 'MEMBER')"
    return any(a != b and db.execute(q, (a, b)).fetchone()[0] for a in named for b in named)


def _recheck_roles(db, named, file_name: str) -> None:
    """After a file: ask the role questions of the start again (the flags, borrowed roles and parameter grants of the
    migration user, and the named roles' memberships of each other). The first answer was taken before the file ran, and
    a file may have changed it in a way the lists in the read-back do not show."""
    try:
        _refuse_privileged_role(db)
        if _members_of_each_other(db, named):
            raise ConfigError(
                "the runtime, portal and purge roles must not be members of each other"
            )
    except ConfigError as e:
        raise ConfigError(f"migration {escape_name(file_name)} left the roles changed: {e}") from e


def _limit_error(e: Exception, step: str) -> ConfigError | None:
    """The plain-words error for a lock wait or a statement that ran into the limits of `RECIPE_TIMEOUTS` (None for
    any other error, which is raised as it is)."""
    limits = dict(re.findall(r"SET LOCAL (\w+) = '([^']*)'", " ".join(RECIPE_TIMEOUTS)))
    if isinstance(e, pg_errors.LockNotAvailable):
        what = f"waited more than {limits.get('lock_timeout')} for a lock (lock_timeout)"
    elif (
        getattr(e, "sqlstate", None) == "57014"
    ):  # query_canceled: the code, not the words (they follow lc_messages)
        what = f"ran more than {limits.get('statement_timeout')} (statement_timeout), or was cancelled by another session"
    else:
        return None
    return ConfigError(
        f"migrate stopped and kept nothing: while {step}, a statement {what}. Another session holds a lock on a "
        "table, or the statement is too slow for a live database. Run migrate again when nothing holds the table; "
        "a migration file that really needs longer is applied by hand with a raised number (CHANGELOG.md, "
        "Migration repair steps)."
    )


def migrate(
    dsn: str,
    *,
    runtime_role: str | None = None,
    portal_role: str | None = None,
    purge_role: str | None = None,
    iam_auth: bool = False,
    region: str | None = None,
    sslmode: str | None = None,
    sslrootcert: str | None = None,
) -> list[str]:
    """Apply pending migrations; return the versions applied by this call. With `runtime_role`, give it the
    privileges `GRANTS` lists (never TRUNCATE; DELETE only on the outbox and the purged evidence tables). With `portal_role`, SELECT on the
    relations marked `portal` and nothing else. The ledger and the grant map are checked first: a bad file name,
    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database. Right after the advisory
    lock the run sets the two `SET LOCAL` limits of `RECIPE_TIMEOUTS` (a lock limit and a statement limit, the same
    lines the hand recipe sets; the numbers are in the CHANGELOG, "Migration repair steps"). They cover the rest of
    the run: reading the ledger, every file, the read-back, and the role checks and grants, so a run with no pending
    file is covered too (a `GRANT` that waits longer than the lock limit for a busy table fails the run). The lock
    limit applies to each wait for a lock and the statement limit to each statement (a file with several statements
    is not timed as a whole; seen on PostgreSQL 16.15). A limit that is reached fails the whole run, keeps nothing and
    is raised as a `ConfigError` in plain words that names the step and the setting. Order: the hand recipe sets the
    limits BEFORE the advisory lock (a person must not hang); `migrate` sets them AFTER it, on purpose: a second
    `migrate` started at the same time waits for the first (that is how two runs apply a file once) and is not
    limited while it waits. A migration file may not change either limit: the read-back after each file refuses the run
    if `lock_timeout` or `statement_timeout` differs from the value the run set.

    The migration role must not be a superuser and must not hold CREATEROLE, CREATEDB or BYPASSRLS: the run reads these
    flags of the current user and of the session user right after the limits and refuses if any is set (the
    `REPLICATION` attribute is not checked). There is no argument or setting that
    switches the check off: a database administrator who only has a superuser login creates a plain migration role
    once (the refusal message gives the SQL) and runs `migrate` as that role.

    Role membership: the refusal list of `migration_numbers` is wider than a plain list of the dangerous statements.
    `GRANT r TO s` and `REVOKE r FROM s` with no `ON` (a role-membership change) are refused in a `.sql` file, because
    the guard cannot read what they change. A role is chosen by the person running `migrate`, so it cannot be named in
    a static file: any role-membership change is made by `migrate()`'s own Python step, with the role as an argument,
    and never by a migration file. (`migrate` makes none today; privileges on tables and sequences are the
    `GRANT ... ON ...` statements it runs itself.) A `.sql` file that holds `GRANT ... ON ...` is not refused by this rule. The rule reads
    statements only at the start of a statement; a membership change made some other way (a `GRANT r TO s` inside a `$$`
    function body that the file then calls) is found by the read-back of `pg_auth_members` after the file and refuses the run."""
    for role in (runtime_role, portal_role, purge_role):
        if role is not None and not _ROLE.fullmatch(role):
            raise ConfigError(f"not a plain database role name: {role!r}")
    named = [r for r in (runtime_role, portal_role, purge_role) if r is not None]
    if len(set(named)) != len(named):
        raise ConfigError("the runtime, portal and purge roles must be different roles")
    files = _migration_files()
    if problems := check_ledger(files):
        raise MigrationNumberError(problems)
    allowed_changes = _trigger_changes()  # the reviewed list; empty today
    texts = read_files(files)  # the only read of each file: the text scanned is the text executed
    if problems := released_problems(MIGRATIONS, _released_manifest(), texts, files):
        # a released file edited, deleted, or a new file numbered below it; hashed from the text that will run
        raise MigrationNumberError(problems)
    if problems := check_grants(files, texts=texts):
        raise ConfigError("migrations are inconsistent: " + "; ".join(problems))
    applied = []
    step = ["taking the migration lock"]  # what the run is doing, for the error of a limit
    try:
        with (
            connect(
                dsn, iam_auth=iam_auth, region=region, sslmode=sslmode, sslrootcert=sslrootcert
            ) as db,
            db.transaction(),
        ):
            db.execute(
                "SELECT pg_advisory_xact_lock(%s)", (MIGRATE_LOCK,)
            )  # one key, defined in migration_numbers
            # the hand recipe's two limits (one constant); `SET LOCAL` ends with this transaction
            for limit in RECIPE_TIMEOUTS:
                db.execute(limit)
            step[0] = "checking the migration role"
            _refuse_privileged_role(db)
            _refuse_foreign_owned(db, _managed_names(texts.values()))
            db.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            step[0] = "reading the ledger"
            done = {r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()}
            if gone := gone_message(done, files):
                raise MigrationNumberError([gone])
            schema = db.execute("SELECT current_schema()").fetchone()[0] or ""
            if late := order_problems(done, files, texts, schema):
                raise MigrationNumberError(late)
            pending = [p for p in files if p.stem not in done]
            if pending:
                saved = _read_back(db, named)
                _refuse_unusual_strings(saved)
            for path in pending:
                step[0] = f"applying {path.name}"
                db.execute(texts[path])  # the text that was scanned, never a second read
                saved = _check_read_back(
                    db,
                    saved,
                    path.name,
                    frozenset(c for c in allowed_changes if c.migration == path.stem),
                    named,
                )
                _recheck_roles(db, named, path.name)
                db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
                applied.append(path.stem)
            step[0] = "checking and granting the roles"
            if _members_of_each_other(db, named):
                raise ConfigError(
                    "the runtime, portal and purge roles must not be members of each other"
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
                    db,
                    purge_role,
                    lambda g: g.purge if g else "",
                    lambda g: g.purge_cols if g else (),
                ):
                    raise ConfigError(
                        "the purge role holds more than the grant map: " + "; ".join(bad[:20])
                    )
            if portal_role:
                _apply_grants(db, portal_role, lambda g: "SELECT" if g.portal else "")
                if (
                    extra := effective_problems(
                        db, portal_role, lambda g: "SELECT" if (g and g.portal) else ""
                    )
                ):  # the same check as the runtime and purge roles (what it can really do, however it got it)
                    raise ConfigError(  # e.g. inherited from another role: REVOKE cannot take those away
                        "the portal role holds privileges outside the portal grant map: "
                        + "; ".join(extra[:20])
                    )
            for role in named:
                got = db.execute(_SCHEMA_USAGE_SQL, (role,)).fetchone()
                if not got or not got[0]:
                    raise ConfigError(
                        f"the role {_label(role)} cannot use the schema {_label(schema)} after the grants: the migration "
                        "role may not pass USAGE on the schema on. Give it the grant option "
                        f"(GRANT USAGE ON SCHEMA <schema> TO <the migration role> WITH GRANT OPTION; CREATE needs no grant option), "
                        "or make it the owner of the schema."
                    )
    except (pg_errors.LockNotAvailable, pg_errors.QueryCanceled) as e:
        if (plain := _limit_error(e, step[0])) is None:
            raise
        raise plain from e
    return applied
