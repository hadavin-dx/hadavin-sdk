"""Forward-only schema migrations for the Postgres store (`hadavin-sdk migrate`).

Run under a migration role, never by the runtime. Every pending `migrations/NNNN_*.sql` file is applied in one
transaction under a transaction-scoped advisory lock (a lock the database offers under a number), so two concurrent
runs apply each file once. Rollback = restore the snapshot taken before migrating.

The file-name rules, the late-file and gone-name refusals and the SQL text rules live in `migration_numbers`
(no database library there); this module only calls them. Each file is read ONCE; the text that was scanned is
the text that is executed.

What `migrate` does, in order:

1. It takes the lock (waiting at most `lock_wait_seconds`) and sets the two time limits of `RECIPE_TIMEOUTS`
   (`migration_numbers`: a lock limit and a statement limit; the hand recipe sets the same two lines).
2. It reads the flags of the migration role (the current user and the session user) and refuses a superuser or a role
   that holds `CREATEROLE`, `CREATEDB`, `BYPASSRLS` or `REPLICATION` (a role with `REPLICATION` can read every change
   made on the whole server). There is no switch to turn this check off.
3. It refuses a schema in which a table, view, sequence or function THIS PACKAGE manages (a relation in `GRANTS`,
   `schema_migrations`, or a function a migration file creates) is owned by a role the migration role cannot act as (a
   database first built with a superuser login). It names the objects and prints the `ALTER ... OWNER TO` lines that
   hand them over (runbook case (h)). Objects of another application in the same schema are never listed. Without
   that, a later `ALTER TABLE` fails with "must be owner" and the `GRANT` lines do nothing without an error.
4. After each file, in the same transaction, it reads the state back from the server (the "read-back") and refuses
   if anything is LEFT changed. It compares these values with the ones it saved before the file:
   - the database user names (the current user and the session user) and the replication-role setting;
   - the search path, three settings that change how SQL text is read, the two time limits, and the transaction
     clock and id;
   - the role memberships of the migration roles (`pg_auth_members`). A role granted to a role inside a function body
     is found here, not by the statement rule;
   - the settings saved per database or per role (`pg_db_role_setting`);
   - every trigger in the migration schema: its enabled state, its definition and the text of its function.
   It cannot see a change that a file makes and undoes before it ends. It cannot undo what a hidden `COMMIT` or a
   second connection (`dblink_exec` runs outside this transaction) already kept. The memberships and saved settings
   it compares are those of the current user, the session user, the runtime, portal and purge roles, and every role
   any of them belongs to. A change to any other role (for example by another session on the same server) is not
   compared. Then it asks the role questions again, so a file cannot leave the migration role with what the first
   check refused.
5. After the grants it reads from the server who has a right where this package lives, and refuses what this package
   does not give. It compares the database before and after the files of THIS run (what changed between two runs is
   not compared), so it finds an object that a file made or changed in any schema, by any statement, also by dynamic
   SQL, and also an object that existed before the run:
   - a relation (table, view, sequence, foreign table) whose owner or rights changed, a column right included;
   - a function whose SECURITY DEFINER flag, rights, owner, body, language or saved settings changed;
   - a schema whose owner or rights changed.
   Only what is the migration role's is compared: an object that the migration role or a role it belongs to owns or
   gave a right on. What another session commits on its own objects while the run is open does not stop the run. An
   owner change made by dynamic SQL is found for these three kinds of object only (not for a type, a domain or any
   other kind).
   It also reads the tables and functions this package names, the schema of the run, every SECURITY DEFINER function
   in that schema that the migration role (or a role it belongs to) owns, and the default rights
   (`ALTER DEFAULT PRIVILEGES`) of the migration role and of the roles it belongs to. It refuses:
   - a right for a role that is not the owner and is not named in this run (the runtime, portal and purge roles),
     and a right for PUBLIC (everyone);
   - an owner that a file handed an object to;
   - a right that may be passed on (`WITH GRANT OPTION`);
   - any right for a named role on a relation that is not in the grant map, and any right for it on a function;
   - any default right for a role other than the migration role itself (a named role included);
   - a SECURITY DEFINER function (one that runs with the rights of its owner) that is not on the reviewed list.
   A role that only has USAGE on a schema (it may look a name up) is not refused.

When `migrate` refuses, a database administrator repairs by hand (the full runbook, cases (a) to (h), is the section
"Migration repair steps" of CHANGELOG.md). Every hand step is a FILE of SQL run with `psql -X -v ON_ERROR_STOP=1 -f <file>`
and your own connection settings (never typed line by line, never a connection string in a text). The file has these
parts, in this order:

- `\\set ON_ERROR_STOP on`;
- `SET search_path TO "<the schema migrate uses>";`;
- `BEGIN;`;
- the two `SET LOCAL` lines of `RECIPE_TIMEOUTS` (`migrate` sets the same two lines itself);
- the advisory lock of `migrate` (`SELECT pg_advisory_xact_lock(<MIGRATE_LOCK>);`, only while no `migrate` runs);
- the steps, where every `UPDATE schema_migrations` is followed by a `DO` check that raises unless exactly one row with
  the new version exists and none with the old one;
- `COMMIT;`.

A late file: use the recipe in the refusal message. A renamed file or ledger row: change the row to the name of the one
folder file with the same text after the number. A database newer than the code: run the newer release; do not rename,
drop or edit the ledger.
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
    MIGRATE_LOCK_WAIT_SECONDS,
    MIGRATIONS,
    RECIPE_TIMEOUTS,
    RELEASED_MANIFEST,
    STEM,
    TRIGGER_CHANGES,
    MigrationNumberError,
    _label,
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
    more than `expected_table(grant)` (and, for columns, `expected_cols(grant)`); the relations are the tables, views,
    materialized views, sequences and foreign tables of the schema. A superuser, a role that can
    create roles or databases or bypass row security, a role that owns a relation or can CREATE in the schema is a
    problem too. The grants above are made first and this runs in the same transaction, so a problem rolls them back."""
    problems: list[str] = []
    row = db.execute(
        "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolreplication FROM pg_roles WHERE rolname = %s",
        (role,),
    ).fetchone()
    if row is None:
        return [f"{role}: the role does not exist"]
    if any(row):
        problems.append(
            f"{role}: is a superuser or can create roles or databases, bypass row security or replicate"
        )
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    table_privs = _table_privs(db)
    if db.execute("SELECT has_schema_privilege(%s, %s, 'CREATE')", (role, schema)).fetchone()[0]:
        problems.append(f"{role}: can CREATE in schema {schema}")
    rels = db.execute(
        "SELECT c.oid, c.relname, c.relkind, pg_get_userbyid(c.relowner) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relkind IN ('r','p','v','m','S','f')",
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
# The five flags that make a migration role too powerful (a superuser can change what the read-back does not read; a role
# with `REPLICATION` can read every change made on the whole server).
_ROLE_FLAGS = ("rolsuper", "rolcreaterole", "rolcreatedb", "rolbypassrls", "rolreplication")
# `session_user` too: a login that is a superuser and then runs `SET ROLE` to a plain role is still a superuser (a file can
# undo the switch inside a function body).
_ROLE_FLAGS_SQL = (
    "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolreplication FROM pg_roles "
    "WHERE rolname IN (current_user, session_user)"
)
# The roles whose memberships and saved settings the read-back compares: `own` = the current user, the session user and
# the named runtime, portal and purge roles (parameter 1: their names); `via_membership` = every role the current user,
# the session user or a named role belongs to, directly or through other roles (`pg_has_role ... 'MEMBER'`). The query list is
# server-wide (`pg_auth_members` and `pg_db_role_setting` hold every role of the server), so rows about other roles are
# left out: another session changing an unrelated role while a file runs must not stop the run.
# Settings saved per database or per role (`ALTER ROLE ... SET`, `ALTER DATABASE ... SET`): they apply to NEW sessions,
# so a file that changes them changes what the next connection runs with.
_READBACK_SETTINGS_SQL = (
    "WITH named AS (SELECT oid FROM pg_roles WHERE rolname = ANY(%s::text[]) AND NOT rolsuper), "
    "scope AS (SELECT r.oid, (r.rolname IN (current_user, session_user) OR r.oid IN (SELECT oid FROM named)) AS own, "
    "(pg_has_role(current_user, r.oid, 'MEMBER') OR pg_has_role(session_user, r.oid, 'MEMBER') "
    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, 'MEMBER'))) AS via_membership "
    "FROM pg_roles r) "
    "SELECT coalesce(d.datname, ''), coalesce(r.rolname, ''), s.setconfig::text FROM pg_db_role_setting s "
    "LEFT JOIN pg_database d ON d.oid = s.setdatabase LEFT JOIN pg_roles r ON r.oid = s.setrole "
    "WHERE s.setdatabase IN (0, (SELECT oid FROM pg_database WHERE datname = current_database())) "
    "AND (s.setrole = 0 OR s.setrole IN (SELECT oid FROM scope WHERE own OR via_membership))"
)
# Role memberships (who is a member of whom, with the grant options): the one thing a `$$` function body can change
# that no statement-start rule sees (`GRANT r TO s` inside a function, then `SELECT f();`). Names, not OIDs. Only the
# memberships of the roles in scope (what each of them is a member of) and the members of the `own` roles.
_READBACK_MEMBERS_SQL = (
    "WITH named AS (SELECT oid FROM pg_roles WHERE rolname = ANY(%s::text[]) AND NOT rolsuper), "
    "scope AS (SELECT r.oid, (r.rolname IN (current_user, session_user) OR r.oid IN (SELECT oid FROM named)) AS own, "
    "(pg_has_role(current_user, r.oid, 'MEMBER') OR pg_has_role(session_user, r.oid, 'MEMBER') "
    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, 'MEMBER'))) AS via_membership "
    "FROM pg_roles r) "
    "SELECT m.roleid::regrole::text, m.member::regrole::text, "
    "(to_jsonb(m) - 'oid' - 'roleid' - 'member')::text FROM pg_auth_members m "
    "WHERE m.member IN (SELECT oid FROM scope WHERE own OR via_membership) OR m.roleid IN (SELECT oid FROM scope WHERE own)"
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


# A plain role can still borrow rights by being a member of a role that holds one of the five flags or is a built-in
# server role (every role whose name starts with `pg_`, for example `pg_execute_server_program`, which runs programs
# on the server, and `pg_write_server_files`; only `pg_database_owner` is allowed). The member can `SET ROLE` to it, or
# uses its rights at once when it inherits. `pg_has_role(..., 'MEMBER')` is true for either way, direct or through other
# roles. Checked for `current_user` and `session_user`.
_BORROWED_ROLES_SQL = (
    "SELECT r.rolname FROM pg_roles r WHERE (r.rolsuper OR r.rolcreaterole OR r.rolcreatedb OR r.rolbypassrls OR r.rolreplication "
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
    """The migration role must hold none of the five flags of `_ROLE_FLAGS` (checked with the live flags of the current user)."""
    rows = db.execute(_ROLE_FLAGS_SQL).fetchall()
    if not rows:
        raise ConfigError("migrate cannot read the flags of its own database role")
    held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows)]
    if held:
        raise ConfigError(
            "the migration role must not be a superuser and must not hold CREATEROLE, CREATEDB, BYPASSRLS or REPLICATION, "
            f"but it holds: {', '.join(held)}. Run migrate with a plain role that holds none of them. A database "
            "administrator creates one once, with SQL such as: "
            f"{PLAIN_MIGRATION_ROLE_SQL}"
        )
    if borrowed := [r[0] for r in db.execute(_BORROWED_ROLES_SQL).fetchall()]:
        raise ConfigError(
            "the migration role is a member of a role that is a superuser, holds CREATEROLE, CREATEDB, BYPASSRLS or REPLICATION, "
            f"or is a built-in server role ({_shown((_label(b) for b in borrowed), ', ')}), so it could use those rights. "
            "Remove the membership (REVOKE <that role> FROM <the migration role>) or run migrate with a plain role "
            "that is a member of none of them."
        )
    row = db.execute(_PARAMETER_TABLE_SQL).fetchone()
    if row and row[0] and (params := [r[0] for r in db.execute(_PARAMETER_GRANTS_SQL).fetchall()]):
        raise ConfigError(
            "the migration role may change server settings it must not change "
            f"({_shown((_label(x) for x in params), ', ')}): a grant on a parameter lets a file change what the checks "
            "rely on. Remove the grant (REVOKE SET, ALTER SYSTEM ON PARAMETER <name> FROM <the migration role>)."
        )


# Objects THIS PACKAGE manages in the migration schema (`_managed_names`: parameter 1 = the relations in `GRANTS` and
# `schema_migrations`, parameter 2 = the functions the migration files create) that the migration role cannot change because another
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
# name (letters, digits, `_` and `$`; the pattern also lets a digit start it, which only adds a name no object has: a
# false refusal at most). The schema before the dot is captured (groups 1 and 2); a database part
# before the schema (`db.schema.name`) is read and left out (PostgreSQL accepts it only for the current database).
_QUOTED_NAME = r'"(?:[^"]|"")+"'
_QUOTED_NAME_BODY = r'"((?:[^"]|"")+)"'
_PLAIN_NAME = r"\w[\w$]*"
_ANY_PART = rf"(?:{_QUOTED_NAME}|{_PLAIN_NAME})"
_DATABASE_DOT = rf"(?:{_ANY_PART}\s*\.\s*(?={_ANY_PART}\s*\.\s*{_ANY_PART}))?"
_SCHEMA_DOT = rf"{_DATABASE_DOT}(?:(?:{_QUOTED_NAME_BODY}|({_PLAIN_NAME}))\s*\.\s*)?"
# Only a `CREATE FUNCTION` at the start of a statement is read (the text has no comments), so one in the middle of a
# statement is not read as a name. Two things follow, one in each direction. (1) A `;` inside a string literal or a
# `$$` body is not told from a statement end, so a `CREATE FUNCTION` written after it IS read as a name: that adds a name
# (a false refusal). (2) A function made some other way, for example `EXECUTE format('CREATE OR REPLACE FUNCTION ...')`
# inside a `$$` body, is NOT read, and the guard refuses `EXECUTE` and `DO` only at the start of a statement, so such a
# function can be missed by the owner check. The check of rights and SECURITY DEFINER (`_refuse_unlisted_grantees`)
# also finds it, by what is new in the schema after the files (`_function_ids`). (The plain form `CREATE FUNCTION` with no
# `OR REPLACE` is read here but is refused earlier by `_SAFE_CREATE`, so it never reaches a run.)
_FUNCTION_CREATE = re.compile(
    rf"(?:\A|;)\s*CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+{_SCHEMA_DOT}(?:{_QUOTED_NAME_BODY}|({_PLAIN_NAME}))",
    re.IGNORECASE,
)


def _fold(name: str) -> str:
    """How PostgreSQL folds a plain name in a UTF-8 database: only the letters A to Z become lower case (not the letters
    of other scripts that Python's `lower` also changes). A database in a single-byte encoding (not UTF-8) also folds
    some capital letters above ASCII; that case was not run (the test servers are UTF-8), so a name with such a letter
    could be matched wrongly there: the result is a false refusal or a name not looked at by the owner check."""
    return "".join(c.lower() if "A" <= c <= "Z" else c for c in name)


_GRANT_MAP_WORDS = (
    " (the grant map is the list in the code of the tables each role of this package may use, and the rights each "
    "may have on each: for the portal role SELECT only)"
)


def _name_of(quoted: str | None, plain: str | None) -> str | None:
    """A name as the server stores it: a quoted one keeps its case (`""` is one quote), a plain one is folded."""
    if quoted is not None:
        return quoted.replace('""', '"')
    return _fold(plain) if plain is not None else None


def _managed_names(texts, schema: str) -> tuple[list[str], list[str]]:
    """The names this package manages in its schema, as two lists, one per catalog (a relation and a function may
    share a name, and a name of one list says nothing about the other catalog): (1) the relations: every relation in
    `GRANTS` (`check_grants` makes these exactly the relations the migration files create) and `schema_migrations`;
    (2) the functions: every function a migration file creates or replaces (a file can create no type or domain: the
    guard refuses `CREATE TYPE` and `CREATE DOMAIN`). `texts` are the file texts `migrate` executes; `schema` is the
    schema of the run (a function written with another schema before the dot is not in this schema, so it is not
    listed). Each list is sorted, lower case where the server folds the name."""
    relations = set(GRANTS) | {"schema_migrations"}
    names: set[str] = set()
    for raw in texts:
        text, _problem = lex(raw, keep_quoted=True)
        for m in _FUNCTION_CREATE.finditer(text):
            where = _name_of(m.group(1), m.group(2))
            # no schema written (the search path decides) or the schema of the run
            if where is None or where == schema:
                names.add(_name_of(m.group(3), m.group(4)))
    return sorted(relations), sorted(names)


def _refuse_foreign_owned(db, texts) -> None:
    """Refuse a run whose migration role cannot change what this package manages in the schema (the names, see
    `_managed_names`; the objects of another application in the schema are not looked at; see `_FOREIGN_OWNED_SQL`). The
    message names the objects (at most `_FOREIGN_OWNED_SHOWN`), their owners, and prints the SQL that hands every one
    of them to the migration role. A statement is printed only when every name in it is plain: another role owns the
    object and chose its name, so a name with a control or unusual character is not copied into a line that a person
    runs; for such an object the message says a person must write the statement by hand."""
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    managed_rel, managed_fn = _managed_names(texts, schema)
    rows = db.execute(_FOREIGN_OWNED_SQL, (managed_rel, managed_fn)).fetchall()
    if not rows:
        return
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
        f" A person must write the statement for {_shown(by_hand, ', ')} by hand (its name holds a character "
        "that is not copied into a printed line)."
        if by_hand
        else ""
    )
    wrong = (
        f"the migration role {_label(me)} cannot change {len(rows)} object(s) of this package in schema "
        f"{_label(schema)} that another role owns: {'; '.join(names)}{f'; and {more} more' if more > 0 else ''}. "
        "A later migration that alters one of them would fail with 'must be owner', and the grants of migrate would "
        "do nothing without an error."
    )
    unchanged = "Nothing was changed."
    to_do = (
        "What to do, in three steps. (1) Check the tables. Objects of other applications in the schema are not listed "
        "and need no change, but a table of ANOTHER application with the same name as one of this package's tables "
        "(for example spend or runs) looks the same here: do not hand that one over, point migrate at another schema "
        "instead. (2) Check the functions. A function is matched by name only, so read the text of each listed "
        "function and hand it over only when it is this package's own code: the migration role would then own it and "
        "run it, and a function made SECURITY DEFINER runs with its owner's rights, so handing it over also hands "
        "over what it can do. (3) Hand the objects over. A database administrator, connected as a superuser or as a "
        "role that is a member of both the old owner and the migration role, runs a file of SQL as described in "
        "CHANGELOG.md, Migration repair steps, case (h): " + " ".join(statements) + hand
    )
    raise ConfigError(f"{wrong} {unchanged} {to_do}")


# SECURITY DEFINER functions a migration file may create: the reviewed list, like `TRIGGER_CHANGES`. Empty today: such a
# function runs with the rights of its owner (the migration role), so a role that may call it gets everything the
# migration role can do. Adding a name here is a code change that a reviewer reads.
REVIEWED_DEFINER_FUNCTIONS: frozenset[str] = frozenset()

# The objects of the whole database that a run is compared on: not the system schemas, not what an installed extension
# owns (`pg_depend`, type `e`: the extension's, not this package's).
# Parts of the queries below, put in by `_sql` (a plain text replacement of a marker, so that no query is built by a
# format string). `@MINE@` = the migration role and every role it belongs to, directly or through other roles
# (`pg_has_role ... 'MEMBER'` is true for the role itself). `@ITEM@` = one right as text: who gave it, who has it, the
# right, and whether it may be passed on (ids and fixed words, joined by one space, so two different rights never make
# the same text).
_NOT_SYSTEM_PARTS = {
    "@NOT_SYSTEM_C@": "n.nspname <> 'information_schema' AND n.nspname !~ '^pg_' "
    "AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_class'::regclass AND d.objid = c.oid AND d.deptype = 'e')",
    "@NOT_SYSTEM_P@": "n.nspname <> 'information_schema' AND n.nspname !~ '^pg_' "
    "AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_proc'::regclass AND d.objid = p.oid AND d.deptype = 'e')",
    "@ME@": "(SELECT oid FROM pg_roles WHERE rolname = current_user)",
    "@MINE@": "(SELECT r.oid FROM pg_roles r WHERE pg_has_role(current_user, r.oid, 'MEMBER'))",
    "@ITEM@": "a.grantor::text || ' ' || a.grantee::text || ' ' || a.privilege_type || ' ' || a.is_grantable::text",
    "@RELKINDS@": "('r','p','v','m','S','f')",
}


def _sql(text: str) -> str:
    for marker, part in _NOT_SYSTEM_PARTS.items():
        text = text.replace(marker, part)
    return text


# The state of one object is what a file can change on it. Every row starts with the id, then `_IN_SCOPE` and `_OWNER`
# (the same two places for a function, a relation and a schema), then the fields named below, each a column of its own
# (no hash and no joined text: two different states can never look the same, and no md5, which a server in FIPS mode
# refuses).
#
# In scope: the object is owned by the migration role or a role it belongs to (`@MINE@`), or one of those roles gave a
# right on it. Only an object in scope before or after the files is compared, and of an object that another role owns
# only the rights that a role of `@MINE@` gave are part of the state. So what ANOTHER session commits while the run is
# open (the run reads committed data: a new table of another application, a GRANT by its owner) is not taken for a
# change made by a file. What is still taken for one: a change by another session to an object in scope (for example
# an administrator who grants a right on a table of the migration role during the run); the refusal says so.
_IN_SCOPE, _OWNER = 0, 1
# A function: its SECURITY DEFINER flag, its rights, and what it runs: the body as text (`prosrc`), the body of a
# function written in the SQL-standard form (`RETURN ...` or `BEGIN ATOMIC`: the server keeps it parsed in `prosqlbody`
# and leaves `prosrc` empty, so it is read with `pg_get_function_sqlbody`), the library file of a C function
# (`probin`), the language and the saved settings.
_FUNCTION_FIELDS = (
    "in scope",
    "owner",
    "SECURITY DEFINER flag",
    "rights",
    "body",
    "SQL-standard body",
    "library file",
    "language",
    "saved settings",
)
_FUNCTION_STATE_SQL = _sql(
    "SELECT p.oid, (p.proowner IN @MINE@ OR EXISTS (SELECT 1 FROM aclexplode(p.proacl) a WHERE a.grantor IN @MINE@)), "
    "pg_get_userbyid(p.proowner), p.prosecdef, "
    "coalesce((SELECT array_agg(q.x ORDER BY q.x) FROM (SELECT @ITEM@ AS x FROM aclexplode(p.proacl) a "
    "WHERE p.proowner IN @MINE@ OR a.grantor IN @MINE@) q)::text, ''), "
    "p.prosrc, pg_get_function_sqlbody(p.oid), p.probin, p.prolang::bigint, p.proconfig::text "
    "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE "
    "@NOT_SYSTEM_P@"
)
# A relation: its rights and the rights on its columns (the column number first).
_RELATION_FIELDS = ("in scope", "owner", "rights", "column rights")
_RELATION_STATE_SQL = _sql(
    "SELECT c.oid, (c.relowner IN @MINE@ OR EXISTS (SELECT 1 FROM aclexplode(c.relacl) a WHERE a.grantor IN @MINE@) "
    "OR EXISTS (SELECT 1 FROM pg_attribute t, aclexplode(t.attacl) a WHERE t.attrelid = c.oid AND a.grantor IN @MINE@)), "
    "pg_get_userbyid(c.relowner), "
    "coalesce((SELECT array_agg(q.x ORDER BY q.x) FROM (SELECT @ITEM@ AS x FROM aclexplode(c.relacl) a "
    "WHERE c.relowner IN @MINE@ OR a.grantor IN @MINE@) q)::text, ''), "
    "coalesce((SELECT array_agg(q.x ORDER BY q.x) FROM (SELECT t.attnum::text || ' ' || @ITEM@ AS x "
    "FROM pg_attribute t, aclexplode(t.attacl) a WHERE t.attrelid = c.oid "
    "AND (c.relowner IN @MINE@ OR a.grantor IN @MINE@)) q)::text, '') "
    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
    "WHERE c.relkind IN @RELKINDS@ AND @NOT_SYSTEM_C@"
)
_SCHEMA_FIELDS = ("in scope", "owner", "rights")
_SCHEMA_STATE_SQL = _sql(
    "SELECT n.oid, (n.nspowner IN @MINE@ OR EXISTS (SELECT 1 FROM aclexplode(n.nspacl) a WHERE a.grantor IN @MINE@)), "
    "pg_get_userbyid(n.nspowner), "
    "coalesce((SELECT array_agg(q.x ORDER BY q.x) FROM (SELECT @ITEM@ AS x FROM aclexplode(n.nspacl) a "
    "WHERE n.nspowner IN @MINE@ OR a.grantor IN @MINE@) q)::text, '') "
    "FROM pg_namespace n WHERE n.nspname <> 'information_schema' AND n.nspname !~ '^pg_'"
)
# What is looked at after the files: (1) the relations and functions this package names in its schema, with every right
# on them, (2) every relation, function and schema in scope that is new or whose state differs from before the files,
# ANYWHERE in the database, whatever schema the file wrote and however the statement was made; of a changed object that
# another role owns only the rights that the migration role or a role it belongs to gave, (3) every SECURITY DEFINER
# function in the schema of the run that the migration role or a role it belongs to owns, also one that no file of this
# run made or touched (it runs with the rights of its owner, so it stays a way to use the migration role's rights for
# as long as it exists). The rights of a plain function that no file touched are not looked at, also when the migration
# role owns it.
# `%(managed_rel)s` are names of `pg_class` (the grant map and the ledger), `%(managed_fn)s` names of `pg_proc` (the
# functions the files create): a function called like a table of the grant map is not a managed function.
# Columns: relation, role, right, is the owner's own right, column, schema, may be passed on, is in the grant map or
# the ledger, kind.
_ACL_RELATION_SQL = _sql(
    "SELECT c.relname, CASE a.grantee WHEN 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END, a.privilege_type, "
    "a.grantee = c.relowner AND (c.relowner = @ME@ OR c.oid = ANY(%(kept_rel)s::oid[])), NULL::text, n.nspname, "
    "a.is_grantable, (n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)), c.relkind::text "
    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
    "CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE ((n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)) "
    "OR (c.oid = ANY(%(changed_rel)s::oid[]) AND (c.relowner IN @MINE@ OR a.grantor IN @MINE@))) "
    "AND c.relkind IN @RELKINDS@ AND "
    "@NOT_SYSTEM_C@"
    " UNION ALL "
    "SELECT c.relname, CASE a.grantee WHEN 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END, a.privilege_type, "
    "a.grantee = c.relowner AND (c.relowner = @ME@ OR c.oid = ANY(%(kept_rel)s::oid[])), t.attname, n.nspname, "
    "a.is_grantable, (n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)), c.relkind::text "
    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
    "JOIN pg_attribute t ON t.attrelid = c.oid AND t.attnum > 0 AND NOT t.attisdropped "
    "CROSS JOIN LATERAL aclexplode(t.attacl) a WHERE ((n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)) "
    "OR (c.oid = ANY(%(changed_rel)s::oid[]) AND (c.relowner IN @MINE@ OR a.grantor IN @MINE@))) "
    "AND c.relkind IN @RELKINDS@ AND "
    "@NOT_SYSTEM_C@"
    " ORDER BY 6, 1, 5, 2, 3"
)
# Columns: name, schema, argument list, SECURITY DEFINER, has no rights list (the default), role, right, is the owner's
# own right, may be passed on, `judged`. `judged` is true for a function this package names or a file changed: its
# rights are read (of a changed function that another role owns: only the rights a role of `@MINE@` gave). It is false
# for a row that is listed only because of (3) above: only the SECURITY DEFINER flag of that function is refused.
_ACL_FUNCTION_SQL = _sql(
    "SELECT p.proname, n.nspname, pg_get_function_identity_arguments(p.oid), p.prosecdef AS definer, p.proacl IS NULL, "
    "CASE a.grantee WHEN 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END, a.privilege_type, "
    "a.grantee = p.proowner AND (p.proowner = @ME@ OR p.oid = ANY(%(kept_fn)s::oid[])), coalesce(a.is_grantable, false), "
    "((n.nspname = %(schema)s AND p.proname = ANY(%(managed_fn)s)) OR (p.oid = ANY(%(changed_fn)s::oid[]) "
    "AND (p.proacl IS NULL OR p.proowner IN @MINE@ OR a.grantor IN @MINE@))) AS judged "
    "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
    "LEFT JOIN LATERAL aclexplode(p.proacl) a ON true "
    "WHERE ((n.nspname = %(schema)s AND p.proname = ANY(%(managed_fn)s)) OR p.oid = ANY(%(changed_fn)s::oid[]) "
    "OR (n.nspname = %(schema)s AND p.prosecdef AND p.proowner IN @MINE@)) AND "
    "@NOT_SYSTEM_P@"
    " ORDER BY 2, 1, 3, 6, 7"
)
# An object whose owner is not the migration role (the owner row of an ACL is hidden while the ACL is NULL).
# Columns: what ('r' relation, 'f' function, 'n' schema), kind (relkind or prokind), schema, name, argument list, owner.
_ACL_OWNER_SQL = _sql(
    "SELECT 'r', c.relkind::text, n.nspname, c.relname, '', pg_get_userbyid(c.relowner) "
    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
    "WHERE ((n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)) OR c.oid = ANY(%(changed_rel)s::oid[])) AND c.relkind IN @RELKINDS@ "
    "AND c.relowner <> @ME@ AND c.oid <> ALL(%(kept_rel)s::oid[]) AND "
    "@NOT_SYSTEM_C@"
    " UNION ALL "
    "SELECT 'f', p.prokind::text, n.nspname, p.proname, pg_get_function_identity_arguments(p.oid), pg_get_userbyid(p.proowner) "
    "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
    "WHERE ((n.nspname = %(schema)s AND p.proname = ANY(%(managed_fn)s)) OR p.oid = ANY(%(changed_fn)s::oid[])) "
    "AND p.proowner <> @ME@ AND p.oid <> ALL(%(kept_fn)s::oid[]) AND "
    "@NOT_SYSTEM_P@"
    " UNION ALL "
    "SELECT 'n', '', n.nspname, '', '', pg_get_userbyid(n.nspowner) FROM pg_namespace n "
    "WHERE n.oid = ANY(%(changed_schema)s::oid[]) AND n.nspowner <> @ME@ AND n.oid <> ALL(%(kept_schema)s::oid[]) "
    "AND n.nspname <> 'information_schema' AND n.nspname !~ '^pg_'"
    " ORDER BY 1, 3, 4, 5"
)
# The schema of the run (every right on it) and every schema that a file changed (its owner or its rights; of a changed
# schema that another role owns only the rights a role of `@MINE@` gave): who may use it and who may create in it (a
# role that may create in a schema can plant a function that a role of this package then calls, so a CREATE right is
# the one that matters most). The owner's own rights and the rights of the migration role itself are not a stranger's
# (the last column). The built-in `pg_database_owner` (whoever owns the database) gets no exception of its own: where
# it owns the schema (the `public` schema of PostgreSQL 15 and later) its rights are the owner's; anywhere else a right
# for it is a right for another role and is refused like one.
_ACL_SCHEMA_SQL = _sql(
    "SELECT n.nspname, CASE a.grantee WHEN 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END, a.privilege_type, "
    "a.is_grantable, a.grantee = n.nspowner OR a.grantee = @ME@ FROM pg_namespace n "
    "CROSS JOIN LATERAL aclexplode(n.nspacl) a "
    "WHERE n.nspname = %(schema)s OR (n.oid = ANY(%(changed_schema)s::oid[]) "
    "AND (n.nspowner IN @MINE@ OR a.grantor IN @MINE@)) ORDER BY 1, 2, 3"
)
# Default rights (`ALTER DEFAULT PRIVILEGES`) of the migration role and of every role it belongs to, for every schema
# and for all schemas at once: they decide the rights of every object such a role makes LATER, also outside `migrate`. An
# administrator may have set them. Not a stranger's right, so not listed: the right of the role the defaults are for
# (`d.defaclrole`), and a right that a role the migration role belongs to gives TO the migration role itself.
# Columns: kind, schema (NULL: every schema), role, right, the role whose new objects get it.
_ACL_DEFAULT_SQL = _sql(
    "SELECT d.defaclobjtype::text, n.nspname, "
    "CASE a.grantee WHEN 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END, a.privilege_type, "
    "pg_get_userbyid(d.defaclrole) "
    "FROM pg_default_acl d LEFT JOIN pg_namespace n ON n.oid = d.defaclnamespace "
    "CROSS JOIN LATERAL aclexplode(d.defaclacl) a "
    "WHERE (d.defaclrole = @ME@ OR pg_has_role(current_user, d.defaclrole, 'MEMBER')) "
    "AND a.grantee <> d.defaclrole AND a.grantee <> @ME@ ORDER BY 1, 2, 3, 4, 5"
)
_DEFAULT_KINDS = {"r": "table", "S": "sequence", "f": "function", "T": "type", "n": "schema"}
_DEFAULT_WORDS = {"r": "TABLES", "S": "SEQUENCES", "f": "FUNCTIONS", "T": "TYPES", "n": "SCHEMAS"}
# The server's own default, which it writes into the list as soon as ANY default right for all schemas is set for a
# role (seen on PostgreSQL 16.15: after `ALTER DEFAULT PRIVILEGES FOR ROLE r GRANT EXECUTE ON FUNCTIONS TO x` the list
# is `{=X/r,r=X/r,x=X/r}`): everyone may call a new function and use a new type. With no list at all the same holds, so
# this entry says nothing new and nobody set it; it is not refused (a function this package makes loses that right
# anyway, see `_refuse_unlisted_grantees`). The same right for everyone set for ONE schema is never the server's own
# (a list for one schema starts empty) and is refused.
_BUILT_IN_DEFAULT = frozenset({("f", "EXECUTE"), ("T", "USAGE")})
_PROBLEMS_SHOWN = 20  # how many items a refusal message lists; the rest is counted ("and N more")


def _shown(items, joiner: str = "; ", limit: int = _PROBLEMS_SHOWN) -> str:
    """The first `limit` items joined, and how many were left out (never a silent cut)."""
    items = list(items)
    more = len(items) - limit
    return joiner.join(items[:limit]) + (f"{joiner}and {more} more" if more > 0 else "")


class _Objects:
    """What exists in the whole database (not the system schemas): every function, relation and schema with the state a
    file can change (`_FUNCTION_STATE_SQL`, `_RELATION_STATE_SQL`, `_SCHEMA_STATE_SQL`), by id; one table of ids per
    catalog, because an id is only unique inside its catalog. Read before the files run and after them. (Two reads of
    every function and relation of the database per run: the cost of a check that does not depend on how a file made
    the change.)"""

    def __init__(
        self, functions: dict[int, tuple], relations: dict[int, tuple], schemas: dict[int, tuple]
    ) -> None:
        self.functions = functions
        self.relations = relations
        self.schemas = schemas


def _objects(db) -> _Objects:
    return _Objects(
        {row[0]: tuple(row[1:]) for row in db.execute(_FUNCTION_STATE_SQL).fetchall()},
        {row[0]: tuple(row[1:]) for row in db.execute(_RELATION_STATE_SQL).fetchall()},
        {row[0]: tuple(row[1:]) for row in db.execute(_SCHEMA_STATE_SQL).fetchall()},
    )


@dataclass(frozen=True)
class _Changed:
    """What `_changed_since` found, one set of ids per catalog (`pg_proc`, `pg_class`, `pg_namespace`): the ids that
    are new or changed, and the ids that kept the owner they had before the files."""

    functions: frozenset[int] = frozenset()
    relations: frozenset[int] = frozenset()
    schemas: frozenset[int] = frozenset()
    kept_functions: frozenset[int] = frozenset()
    kept_relations: frozenset[int] = frozenset()
    kept_schemas: frozenset[int] = frozenset()


def _changed_ids(before: dict[int, tuple], after: dict[int, tuple]) -> frozenset[int]:
    """The ids of one catalog that are in scope (before or after) and are new or differ in any field."""
    return frozenset(
        i
        for i, st in after.items()
        if (st[_IN_SCOPE] or (i in before and before[i][_IN_SCOPE])) and before.get(i) != st
    )


def _kept_owner_ids(before: dict[int, tuple], after: dict[int, tuple]) -> frozenset[int]:
    """The ids of one catalog whose owner is the one the object had before the files."""
    return frozenset(
        i for i, st in after.items() if i in before and before[i][_OWNER] == st[_OWNER]
    )


def _changed_since(before: _Objects, after: _Objects) -> _Changed:
    """What is new or changed after the files, and what kept its owner; per catalog. Changed means: the object is in
    scope before or after (see `_IN_SCOPE`) and any field of its state differs (`_FUNCTION_FIELDS`, `_RELATION_FIELDS`,
    `_SCHEMA_FIELDS`). Found by what the files left behind, so an object made or changed by dynamic SQL, written with
    another schema, or replaced under the same id is found, also when it existed before the run. An object that is out
    of scope before and after (another role owns it and the migration role gave no right on it) is never listed,
    whatever another session did to it meanwhile. An owner other than the migration role is accepted only for an object
    that already had it before the files (a database first built under a role the migration role belongs to:
    `_refuse_foreign_owned` looked at that before); an owner that a file handed over is refused. The comparison covers
    ONE run: what a hand step or another program changed between two runs is not compared."""
    return _Changed(
        _changed_ids(before.functions, after.functions),
        _changed_ids(before.relations, after.relations),
        _changed_ids(before.schemas, after.schemas),
        _kept_owner_ids(before.functions, after.functions),
        _kept_owner_ids(before.relations, after.relations),
        _kept_owner_ids(before.schemas, after.schemas),
    )


_NO_RIGHT_OUTSIDE = "a role named in this run gets no right outside the grant map, which holds tables, views and sequences only"


def _routine_name(schema: str, name: str, args: str) -> str:
    """A function as SQL text for `REVOKE ... ON ROUTINE`: the schema and the name as quoted names (a `"` inside is
    doubled, which is all a quoted name needs), then the argument list as the server prints it
    (`pg_get_function_identity_arguments`: two functions may share a name)."""
    quoted = ".".join('"' + part.replace('"', '""') + '"' for part in (schema, name))
    return f"{quoted}({args})"


def _refuse_unlisted_grantees(
    db,
    texts,
    named,
    changed: _Changed | None = None,
) -> None:
    """After every file and every grant of this run, read from the server who has a right where this package lives, and
    refuse what this package does not give. Looked at: the relations (tables, views, sequences, foreign tables) in `GRANTS`
    and `schema_migrations`; the functions this package names; every relation, function and schema that is new or
    changed after the files, in any schema (also one that existed before the run; see `_changed_since` for what
    "changed" covers); every SECURITY DEFINER function in the schema of the run that the migration role or a role it
    belongs to owns; the schema of the run; and the default rights of the migration role and of the roles it belongs
    to. Refused:
    - a right for a role that is not the owner and is not named in this run (the runtime, portal and purge roles), and a
      right for PUBLIC (everyone);
    - an owner other than the migration role that a file handed an object to;
    - a right that may be passed on (`WITH GRANT OPTION`);
    - ANY right for a named role on a relation that is not in the grant map, and any right for it on a function (a
      named role gets what the grant map gives and USAGE on a schema, nothing else; USAGE on a sequence lets a role take
      the next number, which changes the sequence, so it is not "only reading");
    - CREATE (any right but USAGE) on a schema for any role but the owner and the migration role;
    - any default right for any role but the role it is set for and the migration role (a named role gets none either);
    - a SECURITY DEFINER function that is not on `REVIEWED_DEFINER_FUNCTIONS`.
    The same holds when `migrate` runs with no role arguments. How much each named role may do on the relations of the
    schema of the run is checked by `effective_problems`. A function nobody granted anything to has the default right
    "everyone may call it": that default is removed here (`REVOKE ... FROM PUBLIC`), only for the functions this package
    names or a file changed, so only the owner may call them. Any role may have USAGE on a schema (looking a name up;
    PUBLIC has it by default on `public`). The run is in one transaction, so a refusal keeps nothing."""
    changed = changed or _Changed()
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    managed_rel, managed_fn = _managed_names(texts, schema)
    allowed = set(named)
    keys = {
        "schema": schema,
        "managed_rel": managed_rel,
        "managed_fn": managed_fn,
        "changed_fn": sorted(changed.functions),
        "changed_rel": sorted(changed.relations),
        "changed_schema": sorted(changed.schemas),
        "kept_fn": sorted(changed.kept_functions),
        "kept_rel": sorted(changed.kept_relations),
        "kept_schema": sorted(changed.kept_schemas),
    }
    problems: list[str] = []
    for rel, who, priv, is_owner, col, rel_schema, grantable, is_managed, relkind in db.execute(
        _ACL_RELATION_SQL, keys
    ).fetchall():
        if is_owner:
            continue
        word = _OWNER_WORD.get(relkind, "relation").lower()
        where = f"the {word} {_label(rel_schema, rel)}" + (f", column {_label(col)}" if col else "")
        if who not in allowed:
            problems.append(f"{_label(who)} has {priv} on {where}")
        elif not is_managed:
            problems.append(
                f"{_label(who)} has {priv} on {where}, which is not in the grant map ({_NO_RIGHT_OUTSIDE})"
            )
        elif grantable:
            problems.append(
                f"{_label(who)} may pass {priv} on {where} on to others (WITH GRANT OPTION)"
            )
    for what, kind, obj_schema, name, args, owner in db.execute(_ACL_OWNER_SQL, keys).fetchall():
        if what == "n":
            thing = f"the schema {_label(obj_schema)}"
        elif what == "f":
            thing = f"the {_FUNCTION_WORD.get(kind, 'FUNCTION').lower()} {_label(obj_schema, name)}({_label(args)})"
        else:
            thing = f"the {_OWNER_WORD.get(kind, 'relation').lower()} {_label(obj_schema, name)}"
        problems.append(
            f"{thing} was handed to {_label(owner)} (it is not owned by the migration role)"
        )
    revoke: dict[str, None] = {}  # in the order read, each function once
    for (
        name,
        fn_schema,
        args,
        definer,
        default_acl,
        who,
        priv,
        is_owner,
        grantable,
        judged,
    ) in db.execute(_ACL_FUNCTION_SQL, keys).fetchall():
        shown = f"the function {_label(fn_schema, name)}({_label(args)})"
        if definer and name not in REVIEWED_DEFINER_FUNCTIONS:
            problems.append(
                f"{shown} is SECURITY DEFINER (it runs with the rights of its owner)"
                + (
                    ""
                    if judged
                    else ", and no file of this run made or changed it: the migration role or a role it belongs to "
                    "owns it"
                )
            )
        if not judged:
            continue
        if default_acl:
            revoke[_routine_name(fn_schema, name, args)] = None
        elif who is not None and not is_owner:
            if who not in allowed:
                problems.append(f"{_label(who)} has {priv} on {shown}")
            else:
                problems.append(f"{_label(who)} has {priv} on {shown} ({_NO_RIGHT_OUTSIDE})")
            if grantable:
                problems.append(
                    f"{_label(who)} may pass {priv} on {shown} on to others (WITH GRANT OPTION)"
                )
    for sname, who, priv, grantable, is_owner in db.execute(_ACL_SCHEMA_SQL, keys).fetchall():
        if is_owner:
            continue
        if grantable:
            problems.append(
                f"{_label(who)} may pass {priv} on the schema {_label(sname)} on to others (WITH GRANT OPTION)"
            )
        elif priv != "USAGE":  # USAGE only lets a role look a name up
            problems.append(f"{_label(who)} has {priv} on the schema {_label(sname)} itself")
    for kind, where, who, priv, for_role in db.execute(_ACL_DEFAULT_SQL).fetchall():
        if where is None and who == "PUBLIC" and (kind, priv) in _BUILT_IN_DEFAULT:
            continue  # the server's own default, see `_BUILT_IN_DEFAULT`
        place = "every schema" if where is None else f"the schema {_label(where)}"
        problems.append(
            f"{_label(who)} gets {priv} on every new {_DEFAULT_KINDS.get(kind, kind)} that {_label(for_role)} makes "
            f"in {place} (a default right, `ALTER DEFAULT PRIVILEGES`, which this statement undoes: ALTER DEFAULT PRIVILEGES FOR ROLE "
            f"<that role>{'' if where is None else ' IN SCHEMA <that schema>'} REVOKE {priv} ON "
            f"{_DEFAULT_WORDS.get(kind, 'TABLES')} FROM <the role or PUBLIC>)"
        )
    if problems:
        raise ConfigError(
            f"after the migration files ran, rights that this package does not give are in place, in schema "
            f"{_label(schema)} or elsewhere in this database: {_shown(sorted(set(problems)))}. "
            "Nothing was changed. The whole run is undone. "
            "Only the migration role itself and the runtime, portal and purge roles named in this run may have rights "
            "on this package's tables, views, sequences, functions and schema; a named role gets the rights of the "
            "grant map and nothing on any other table, view, sequence or function; and a function that runs with the "
            "rights of its owner (SECURITY DEFINER) is not allowed unless a reviewer put it on the list in the code. "
            "What to do, in three steps. (1) If a migration file made it (a GRANT to another role or to PUBLIC, "
            "ALTER DEFAULT PRIVILEGES, a SECURITY DEFINER function, an owner change), remove that statement from the file. "
            "(2) If no file did, an earlier run or a database administrator did (also a default right set for the "
            "database), or another session changed an object of the migration role while this run was open (the run "
            "compares the database before and after its files and reads what other sessions commit meanwhile): when "
            "the role is the runtime, portal or purge role of this package and the object is in the grant map, name it "
            "in this run; otherwise a database administrator revokes the right. (3) Run migrate again."
        )
    for ident in revoke:
        db.execute(sql.SQL("REVOKE ALL ON ROUTINE {} FROM PUBLIC").format(sql.SQL(ident)))


_LOCK_HOLDER_SQL = (
    "SELECT a.pid, a.usename, a.application_name, a.state, a.backend_start FROM pg_locks l "
    "JOIN pg_stat_activity a ON a.pid = l.pid WHERE l.locktype = 'advisory' AND l.granted AND l.objsubid = 1 "
    "AND l.database = (SELECT oid FROM pg_database WHERE datname = current_database()) "
    "AND ((l.classid::bigint << 32) | l.objid::bigint) = %s ORDER BY a.backend_start LIMIT 1"
)
# A prepared transaction (`PREPARE TRANSACTION`: a transaction a session set aside to commit later) keeps its locks
# and has no session: its row in `pg_locks` has no process number.
_LOCK_PREPARED_SQL = (
    "SELECT count(*) FROM pg_locks l WHERE l.locktype = 'advisory' AND l.granted AND l.objsubid = 1 AND l.pid IS NULL "
    "AND l.database = (SELECT oid FROM pg_database WHERE datname = current_database()) "
    "AND ((l.classid::bigint << 32) | l.objid::bigint) = %s"
)
# The prepared transactions of this database (the view shows them to every login), oldest first.
_PREPARED_SQL = "SELECT gid, owner, prepared FROM pg_prepared_xacts WHERE database = current_database() ORDER BY prepared LIMIT 5"
# `lock_timeout` is a whole number of milliseconds that PostgreSQL holds in 32 bits.
MAX_LOCK_WAIT_SECONDS = 2_147_483


def _seen(value) -> str:
    """A column of `pg_stat_activity` as words: the server shows NULL for the session of another user to a login that may
    not look."""
    return "not visible to this login" if value is None else str(value)


def _take_the_lock(db, wait_seconds: int) -> None:
    """Take the one migration lock (the same key a hand recipe takes), waiting at most `wait_seconds`. The wait is
    bounded by `lock_timeout` (a number of milliseconds made from an integer); the next statements of the run set the
    two limits of `RECIPE_TIMEOUTS`. A run that gives up names the session that holds the lock and changes nothing."""
    # `statement_timeout` is also a limit on the wait for a lock: a value saved for the migration role would end the
    # wait early and the message would blame the wrong limit. The wait has the one limit `lock_timeout`.
    db.execute(
        f"SET LOCAL lock_timeout = '{int(wait_seconds) * 1000}ms'; SET LOCAL statement_timeout = 0;"
    )
    try:
        with (
            db.transaction()
        ):  # a savepoint: the refusal below can still ask the server who holds the lock
            db.execute(
                "SELECT pg_advisory_xact_lock(%s)", (MIGRATE_LOCK,)
            )  # one key, in migration_numbers
    except pg_errors.LockNotAvailable:
        row = db.execute(_LOCK_HOLDER_SQL, (MIGRATE_LOCK,)).fetchone()
        gave_up = f"migrate waited {wait_seconds} seconds for the migration lock and gave up"
        if row is None and (db.execute(_LOCK_PREPARED_SQL, (MIGRATE_LOCK,)).fetchone() or (0,))[0]:
            listed = [
                f"'{_label(str(gid))}' (owner {_label(str(owner))}, prepared {since})"
                for gid, owner, since in db.execute(_PREPARED_SQL).fetchall()
            ]
            raise ConfigError(
                f"{gave_up}: a prepared transaction holds it (a transaction that a session set aside with PREPARE "
                "TRANSACTION; it keeps its locks until it is finished and has no session that could be ended). "
                f"The oldest prepared transactions of this database: {_shown(listed) or 'none visible'}. "
                "Nothing was changed. A database administrator finishes the one that holds the lock (ROLLBACK "
                "PREPARED '<its name>' or COMMIT PREPARED '<its name>'); then run migrate again."
            ) from None
        who = (
            f"the session of {_seen(row[1])} (process {row[0]}, application {_seen(row[2])}, "
            f"state {_seen(row[3])}, connected since {_seen(row[4])})"
            if row
            else "a session this login cannot see"
        )
        raise ConfigError(
            f"{gave_up}: {who} holds it. "
            "Nothing was changed. Wait until that run ends and run migrate again; if it is stuck, a database "
            "administrator ends that session (pg_terminate_backend with the process number), or you run migrate "
            "again with a larger lock_wait_seconds (the command line option --lock-wait-seconds) when the other run "
            "is a long migration."
        ) from None


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
    lock_wait_seconds: int = MIGRATE_LOCK_WAIT_SECONDS,
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
    `migrate` started at the same time waits for the first (that is how two runs apply a file once), but only for
    `lock_wait_seconds` (command line option `--lock-wait-seconds`; from 1 to `MAX_LOCK_WAIT_SECONDS`, the most that
    the server accepts); then it gives up, changes nothing and names the session that holds the lock. A migration file may not change either limit: the read-back after each file refuses the run
    if `lock_timeout` or `statement_timeout` differs from the value the run set.

    The migration role must not be a superuser and must not hold CREATEROLE, CREATEDB, BYPASSRLS or REPLICATION: the run reads these
    flags of the current user and of the session user right after the limits and refuses if any is set (a role with
    `REPLICATION` can read every change made on the whole server). There is no argument or setting that
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
    if (
        isinstance(lock_wait_seconds, bool)
        or not isinstance(lock_wait_seconds, int)
        or not 1 <= lock_wait_seconds <= MAX_LOCK_WAIT_SECONDS
    ):
        raise ConfigError(
            f"lock_wait_seconds must be a whole number of seconds, from 1 to {MAX_LOCK_WAIT_SECONDS}"
        )
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
            _take_the_lock(db, lock_wait_seconds)
            # the hand recipe's two limits (one constant); `SET LOCAL` ends with this transaction
            for limit in RECIPE_TIMEOUTS:
                db.execute(limit)
            step[0] = "checking the migration role"
            _refuse_privileged_role(db)
            _refuse_foreign_owned(db, texts.values())
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
            objects_before = _objects(db)
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
                        f"the runtime role has more than the grant map, in schema {_label(schema)}: "
                        + _shown(bad)
                        + _GRANT_MAP_WORDS
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
                        f"the purge role has more than the grant map, in schema {_label(schema)}: "
                        + _shown(bad)
                        + _GRANT_MAP_WORDS
                    )
            if portal_role:
                _apply_grants(db, portal_role, lambda g: "SELECT" if g.portal else "")
                if (
                    extra := effective_problems(
                        db, portal_role, lambda g: "SELECT" if (g and g.portal) else ""
                    )
                ):  # the same check as the runtime and purge roles (what it can really do, however it got it)
                    raise ConfigError(  # e.g. inherited from another role: REVOKE cannot take those away
                        f"the portal role has privileges outside the portal grant map, in schema {_label(schema)}: "
                        + _shown(extra)
                        + _GRANT_MAP_WORDS
                    )
            changed = _changed_since(objects_before, _objects(db))
            _refuse_unlisted_grantees(db, texts.values(), named, changed)
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
