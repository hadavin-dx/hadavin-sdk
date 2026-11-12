"""Forward-only schema migrations for the Postgres store (`hadavin-sdk migrate`).

Run under a migration role, never by the runtime. Every pending `migrations/NNNN_*.sql` file is applied in one
transaction under a transaction-scoped advisory lock (a lock the database offers under a number), so two concurrent
runs apply each file once. Rollback = restore the snapshot taken before migrating.

The file-name rules, the late-file and gone-name refusals and the SQL text rules live in `migration_numbers`
(no database library there); this module only calls them. Each file is read ONCE; the text that was scanned is
the text that is executed.

What `migrate` promises. "Stopped" means: the run is refused and everything it did is undone, unless a file ended the
transaction itself (a hidden COMMIT); that case is reported separately with its own message. "Detected" means: the run
reports it loudly, but the change is already in the database and a person must act. "Lasting right" means a right that
is still there when the check looks. The same table is in CHANGELOG.md (a test compares the two texts).

[promise table]
| Who wrote the file | What `migrate` does | Word |
|---|---|---|
| 1. We did, and made an honest mistake | When the file leaves a named role, or everyone, with a right outside the grant map, the run is refused and undone. The same mistake is caught before release, because the build server runs the shipped files on an empty database and tests what each role can really do. | STOPPED |
| 2. Someone careless, or a file copied from elsewhere | The same, for lasting rights only. Nothing is promised about lost data, and nothing about code the file leaves behind to run later. | STOPPED, for lasting rights only |
| 3. Someone who wants to do harm | NOT stopped. Lasting excess rights that exist when the check after the commit runs are reported, with the statements that remove them. Such a file can also cheat the check after the commit, or make it fail to run; a check that cannot run ends in the same loud "applied, not verified" result, never in "applied". | DETECTED, not stopped |
[end of promise table]

Why row 3 cannot be better: the file runs as the owner of every table. The real protections against a harmful file are
elsewhere: a person reviews every file, each released file's fingerprint is recorded and checked, and a separate
read-only login that only checks is a later ticket.

What `migrate` does, in order (eight steps; each refusal before the commit keeps nothing):

1. Before it connects: the file names, the ledger order, the fingerprints of released files, `check_grants`.
2. It connects, takes the lock (waiting at most `lock_wait_seconds`) and sets the two time limits of `RECIPE_TIMEOUTS`
   (`migration_numbers`: a lock limit and a statement limit; the hand recipe sets the same two lines). It refuses a
   server below PostgreSQL 16, a migration role that is a superuser or holds `CREATEROLE`, `CREATEDB`, `BYPASSRLS` or
   `REPLICATION` (a role with `REPLICATION` can read every change made on the whole server), and a schema in which a
   table, view, sequence or function THIS PACKAGE manages is owned by a role the migration role cannot act as (it
   prints the `ALTER ... OWNER TO` lines, runbook case (h)). It reads the schema of the run once.
3. `verify`, before the first file: the state of the database is judged against the rules below. A right that the run
   itself repairs at step 4 is not refused here. Anything else stops the run with "No file ran".
4. Each pending file, then the read-back after it (the values, memberships, saved settings and triggers it saved before
   the file; the memberships are read from `pg_auth_members`), then the role questions again, so a mistake in a file
   that changes the migration role's own rights is refused, then the ledger row. The read-back names the file; it cannot see a change
   that a file makes and undoes before it ends, and cannot undo what a hidden `COMMIT` or a second connection
   (`dblink_exec` runs outside this transaction) already kept.
5. The runner's own writes: the grants of the grant map for each named role, and the removal of everyone's `EXECUTE` on
   the functions the files name.
6. The deferred checks and triggers run early (`SET CONSTRAINTS ALL IMMEDIATE`), the read-back once more, then `verify`
   in full. A problem here refuses the whole run (rows 1 and 2 of the table).
7. The COMMIT. A commit the server refused keeps nothing (exit 2). A commit whose outcome is unknown (lost connection)
   is reported as "may or may not have happened" (exit 5).
8. After the commit, on a new connection, as the migration role, in one read-only snapshot: `verify` again. Excess
   rights found here are reported with the statements that remove them, and `migrate` exits with 5 ("applied, not
   verified"); a check that cannot run says so in the same way. `migrate` never says "applied" unless this check ran to
   the end and found nothing. Running `migrate` again is the way to re-check.

What `verify` judges (the rules are in `migration_verify._judge`). For each of the three named roles, and every role it
belongs to: no flag of the five above, no built-in `pg_*` role, no role of the migration role family, no owned object,
no right that the grant map does not give (columns included), no grant option, no SECURITY DEFINER function that
everyone or the role may call. For the objects of the migration role family in the schema of the run, and for the
schema itself: rights only for the owner, the migration role and the named roles as far as the grant map gives them;
nothing for everyone except USAGE on the schema and on a row type; no SECURITY DEFINER function that is not on
`REVIEWED_DEFINER_FUNCTIONS`; an owner that is a role of the family. Default rights (`ALTER DEFAULT PRIVILEGES`): none
for a named role, none for everyone beyond the server's own entry, none for another role on what the family makes.
What everyone holds on the system schemas is the server as shipped and is not judged. A clean run means "no excess right
was there when we looked", not "the database is safe from now on".

These text rules (`GRANT` or `REVOKE` of a right on anything but a table, view, sequence, column or function,
`ALTER DEFAULT PRIVILEGES`, a change of owner, `CREATE TYPE`, a role-membership statement without `ON`) refuse common
accidents early with a plain message. They are not the guard: dynamic SQL passes them, and `verify` judges what is in
the database afterwards.

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

import psycopg
from psycopg import errors as pg_errors
from psycopg import sql
from psycopg.pq import TransactionStatus

from hadavin_sdk.errors import AppliedNotVerifiedError, ConfigError
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
from hadavin_sdk.store.migration_verify import (
    STEP4_SQL,
    V2_SQL,
    Problem,
    check_version,
    pinned_read,
    statement_blocks,
    verify,
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


def _apply_grants(db, schema: str, role_name: str, privileges, columns=None) -> None:
    """Reset the role's rights on every relation in `GRANTS` in `schema` (the schema of the run, read once at step 1),
    then give back what `privileges(grant)` names."""
    role = sql.Identifier(role_name)
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


# The COMMIT of a run (ticket P3a-2, 4.1 step 7). A commit that the server refuses (a deferred check or trigger that
# raises at commit time while the session stays usable) means nothing was kept. Anything else (a lost connection, no
# SQLSTATE at all, a shutdown, a code outside this list) means the commit may or may not have happened. The list errs
# towards "unknown": a refused commit outside it is reported as "may or may not have happened", which costs one more
# run of `migrate`, never a false "nothing was kept". Probed on PostgreSQL 16.15: 23503 (a deferred foreign key), 57014
# (a cancel), 57P01 (`pg_terminate_backend`: closed connection, so "unknown").
_COMMIT_REFUSED_CLASSES = ("22", "23", "40", "42", "44", "P0")
_COMMIT_REFUSED_STATES = frozenset({"55P03", "55000", "55006", "57014"})


def _commit_outcome(exc: BaseException, db) -> Literal["refused", "unknown"]:
    """Decide what an error at the COMMIT means. "refused" only when all four hold: the error carries an SQLSTATE; the
    connection is not closed; the connection's transaction state is IDLE (the server rolled back and the session lives);
    and the SQLSTATE is of a class in `_COMMIT_REFUSED_CLASSES` or one of `_COMMIT_REFUSED_STATES`. Everything else is
    "unknown"."""
    state = getattr(exc, "sqlstate", None)
    if not state or getattr(db, "closed", True):
        return "unknown"
    if db.info.transaction_status != TransactionStatus.IDLE:
        return "unknown"
    if state in _COMMIT_REFUSED_STATES or state.startswith(_COMMIT_REFUSED_CLASSES):
        return "refused"
    return "unknown"


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
    "SELECT current_user, session_user, pg_catalog.current_setting('session_replication_role'), "
    "pg_catalog.current_setting('search_path'), pg_catalog.current_setting('standard_conforming_strings'), "
    "pg_catalog.current_setting('backslash_quote'), pg_catalog.current_setting('client_encoding'), "
    "pg_catalog.current_setting('lock_timeout'), pg_catalog.current_setting('statement_timeout'), "
    "pg_catalog.transaction_timestamp(), pg_catalog.txid_current()"
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
# Triggers of the migration schema only (the schema of the run, read once at step 1 and passed as the parameter); internal ones are skipped. Per
# trigger: its table's id (only to tell a renamed table from a new one), its enabled state, its full definition and
# its function's source text, the function's security mode, owner and saved settings (a function replaced
# under the same name keeps the trigger name but not what it does).
_READBACK_TRIGGERS_SQL = (
    "SELECT t.tgname, t.tgenabled, c.relname, n.nspname, t.tgrelid::bigint, pg_get_triggerdef(t.oid), "
    "p.prosrc, p.prosecdef, pg_get_userbyid(p.proowner), p.proconfig::text FROM pg_trigger t "
    "JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
    "LEFT JOIN pg_proc p ON p.oid = t.tgfoid "
    "WHERE NOT t.tgisinternal AND n.nspname = %s"
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


def _read_back(db, schema: str, named=(), *, if_ended: _Saved | None = None) -> _Saved:
    """The eleven session values are read as the session has them now (a file may have changed the search path or a
    limit, and the read must see that, so they are read OUTSIDE `pinned_read`; every name in that statement is a
    keyword or written `pg_catalog.`, so a function a file made cannot answer in its place). The three reads of the
    catalog run inside `pinned_read`, so an unqualified catalog name cannot be captured by a temporary table."""
    values = tuple(db.execute(_READBACK_VALUES_SQL).fetchone())
    if if_ended is not None and db.info.transaction_status == TransactionStatus.IDLE:
        # a file ended the transaction (COMMIT): a statement now runs on its own and nothing can be pinned. The clock and
        # id just read already differ from the saved ones, so the caller refuses on them; the catalog parts stay as saved
        # (they are not read, and must not be reported as changed).
        return _Saved(
            values, if_ended.triggers, if_ended.members, if_ended.settings, if_ended.relids
        )
    triggers, relids = {}, {}
    with pinned_read(db, RECIPE_TIMEOUTS):
        trigger_rows = db.execute(_READBACK_TRIGGERS_SQL, (schema,)).fetchall()
        scope = (list(named),)
        member_rows = db.execute(_READBACK_MEMBERS_SQL, scope).fetchall()
        setting_rows = db.execute(_READBACK_SETTINGS_SQL, scope).fetchall()
    for name, enabled, table, trigger_schema, relid, *detail in trigger_rows:
        triggers[(trigger_schema, table, name)] = (enabled, *detail)
        relids[(trigger_schema, table, name)] = relid
    members = frozenset(tuple(r) for r in member_rows)
    settings = frozenset(tuple(r) for r in setting_rows)
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
    "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s "
    "AND c.relkind IN ('r','p','v','m','S','f') AND c.relname = ANY(%s::text[]) "
    "AND NOT pg_has_role(current_user, c.relowner, 'USAGE') "
    "AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_class'::regclass AND d.objid = c.oid "
    "AND d.deptype = 'e') "
    "AND (c.relkind <> 'S' OR NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_class'::regclass "
    "AND d.objid = c.oid AND d.deptype IN ('a','i'))) "
    "UNION ALL SELECT 'f', p.prokind::text, p.proname, pg_get_userbyid(p.proowner), "
    "pg_get_function_identity_arguments(p.oid) FROM pg_proc p "
    "JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = %s "
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
# function can be missed by the owner check. The check of the final state (`verify`) also
# finds it, by the rights and the owner the function has when the files have run. (The plain form `CREATE FUNCTION` with no
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


def _name_of(quoted: str | None, plain: str | None) -> str | None:
    """A name as the server stores it: a quoted one keeps its case (`""` is one quote), a plain one is folded."""
    if quoted is not None:
        return quoted.replace('""', '"')
    return _fold(plain) if plain is not None else None


def _managed_names(texts, schema: str) -> tuple[list[str], list[str]]:
    """The names this package manages in its schema, as two lists, one per catalog (a relation and a function may
    share a name, and a name of one list says nothing about the other catalog): (1) the relations: every relation in
    `GRANTS` (`check_grants` makes these exactly the relations the migration files create) and `schema_migrations`;
    (2) the functions: every function a migration file creates or replaces (a statement the scan can read cannot create a
    type or a domain; dynamic SQL can, and `verify` judges the result). `texts` are the file texts `migrate` executes; `schema` is the
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


def _functions_in_other_schemas(texts, schema: str) -> tuple[list[str], list[str]]:
    """The functions a file creates or replaces with another schema written before the dot, as two lists of the same
    length (the schemas, the names): `_managed_names` lists only the schema of the run."""
    homes: set[tuple[str, str]] = set()
    for raw in texts:
        text, _problem = lex(raw, keep_quoted=True)
        for m in _FUNCTION_CREATE.finditer(text):
            where = _name_of(m.group(1), m.group(2))
            if where is not None and where != schema:
                homes.add((where, _name_of(m.group(3), m.group(4))))
    ordered = sorted(homes)
    return [w for w, _n in ordered], [n for _w, n in ordered]


def _refuse_foreign_owned(db, schema: str, texts) -> None:
    """Refuse a run whose migration role cannot change what this package manages in the schema (the names, see
    `_managed_names`; the objects of another application in the schema are not looked at; see `_FOREIGN_OWNED_SQL`). The
    message names the objects (at most `_FOREIGN_OWNED_SHOWN`), their owners, and prints the SQL that hands every one
    of them to the migration role. A statement is printed only when every name in it is plain: another role owns the
    object and chose its name, so a name with a control or unusual character is not copied into a line that a person
    runs; for such an object the message says a person must write the statement by hand."""
    managed_rel, managed_fn = _managed_names(texts, schema)
    rows = db.execute(_FOREIGN_OWNED_SQL, (schema, managed_rel, schema, managed_fn)).fetchall()
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
REVIEWED_DEFINER_FUNCTIONS: frozenset[tuple[str, str, str]] = frozenset()
# The key of an entry is (schema, name, identity arguments as the server prints them). `RUN_SCHEMA` in the first place
# stands for "the schema of the run", which only the run knows; `migrate` turns it into the real name before `verify` is
# called, so `verify` never sees this word.
RUN_SCHEMA = "(the schema of the run)"

_PROBLEMS_SHOWN = 20  # how many items a refusal message lists; the rest is counted ("and N more")


def _shown(items, joiner: str = "; ", limit: int = _PROBLEMS_SHOWN) -> str:
    """The first `limit` items joined, and how many were left out (never a silent cut)."""
    items = list(items)
    more = len(items) - limit
    return joiner.join(items[:limit]) + (f"{joiner}and {more} more" if more > 0 else "")


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
    *,
    schema: str,
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
    now = _read_back(db, schema, named, if_ended=saved)
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


def _fetch_version(db) -> int:
    """The server version number (`V2_SQL`, every name qualified), read before the first query that needs PostgreSQL 16."""
    return db.execute(V2_SQL).fetchone()[0]


def _revoke_default_execute(db, schema: str, me: str, login: str, texts) -> None:
    """Step 4, second part: everyone may call a new function by default; remove that for the functions this package's
    files name (in the schema of the run, or written with another schema before the dot), when the migration role (or a
    role it belongs to) owns them. The read runs in
    `pinned_read`; the writes are outside it, with the schema read at step 1."""
    _relations, functions = _managed_names(texts, schema)
    other_schemas, other_names = _functions_in_other_schemas(texts, schema)
    family = [me] + ([login] if login != me else [])
    with pinned_read(db, RECIPE_TIMEOUTS):
        rows = db.execute(
            STEP4_SQL,
            {
                "family": family,
                "schema": schema,
                "managed": functions,
                "other_schemas": other_schemas,
                "other_names": other_names,
            },
        ).fetchall()
    for _shown_name, where, name, args, _kind in rows:
        signature = args  # an aggregate with no arguments has `` here (checked on 16.15), so the text is `()`
        if any(escape_name(part) != part for part in (where, name, signature)):
            # a name with a control character is never written into a statement (the same rule as the printed
            # statements of `verify`); the check at step 6 judges the function and refuses it with a line to act on
            continue
        db.execute(
            sql.SQL("REVOKE ALL ON ROUTINE {}({}) FROM PUBLIC").format(
                sql.Identifier(where, name), sql.SQL(signature)
            )
        )


END_OF_RUN = "(after the last file and the grants)"  # in the place of a file name at the last read-back (step 6)

_RUN_IDENTITY_SQL = "SELECT current_schema(), current_user, session_user"
# Who owns the schema of the run when the run starts. A schema that a database administrator owns and in which the
# migration role may create (the setup `PLAIN_MIGRATION_ROLE_SQL` prints) is a normal setup, so `verify`'s refusal of a
# schema that the migration role family does not own is applied only to a schema whose owner CHANGED during the run
# (a file or another session handed it to someone else).
_SCHEMA_OWNER_SQL = "SELECT pg_catalog.pg_get_userbyid(n.nspowner) FROM pg_catalog.pg_namespace n WHERE n.nspname = %s"


def _reviewed_definers(schema: str) -> frozenset[tuple[str, str, str]]:
    """`REVIEWED_DEFINER_FUNCTIONS` (read now, so a test can replace it) with the schema of the run filled in."""
    return frozenset(
        (schema if where == RUN_SCHEMA else where, name, args)
        for where, name, args in REVIEWED_DEFINER_FUNCTIONS
    )


def _state_problems(
    db,
    *,
    me: str,
    login: str,
    named_roles: dict[str, str],
    schema: str,
    texts,
    schema_owner: str,
) -> list[Problem]:
    """Every right in the database that the grant map does not give, read from the state of the database now (`verify`).
    `schema_owner` is who owned the schema of the run when the run started (see `_SCHEMA_OWNER_SQL`)."""
    managed_relations, managed_functions = _managed_names(texts, schema)
    found = verify(
        db,
        migration_role=me,
        login_role=login,
        named_roles=named_roles,
        grant_map=GRANTS,
        schema=schema,
        managed_relations=managed_relations,
        managed_functions=managed_functions,
        reviewed_definers=_reviewed_definers(schema),
        limits=RECIPE_TIMEOUTS,
    )
    return [
        p
        for p in found
        if not (
            p.kind == "foreign_owner"
            and p.word == "schema"
            and p.schema == schema
            and not p.obj
            and p.owner == schema_owner
        )
    ]


def _problem_lines(problems: list[Problem]) -> str:
    """The first `_PROBLEMS_SHOWN` problem lines, one per line, and a count of the rest (never a silent cut)."""
    lines = [f"  - {p.line()}" for p in problems]
    text = "\n".join(lines[:_PROBLEMS_SHOWN])
    more = len(lines) - _PROBLEMS_SHOWN
    if more > 0:
        text += f"\n  - and {more} more lines; run the statements above, then run migrate again to see the rest"
    return text


def _after_commit(
    applied: list[str],
    problems: list[Problem],
    *,
    could_not_run: str = "",
    commit_unknown: bool = False,
) -> AppliedNotVerifiedError:
    """The error of ticket P3a-2, 4.2: the files are committed (or may be) and nobody has confirmed the rights. The first
    sentence of each form is fixed; `cli` prints this text to standard error and the statements to standard output."""
    own, outside = statement_blocks(problems)
    versions = ", ".join(applied) if applied else "no file (nothing was pending)"
    if commit_unknown:
        head = (
            "The connection was lost while the files were being committed, so the commit may or may not have "
            "happened, and nothing was checked afterwards; run migrate again: it applies the files that are not in "
            "the ledger and checks the database either way."
        )
        body = f"Tried to commit: {versions}."
    elif could_not_run:
        head = (
            "The files are applied and committed, but the check after the commit could not run "
            f"({_label(could_not_run)}), so nobody has confirmed that the roles hold only what the grant map gives; "
            "run migrate again to check."
        )
        body = f"Applied in this run: {versions}."
    else:
        head = (
            "The files are applied and committed; the database is over-privileged now; run these statements; run "
            "migrate again to re-check."
        )
        body = f"Applied in this run: {versions}.\nWhat is wrong ({len(problems)} things):\n{_problem_lines(problems)}"
        total = len(own) + len(outside)
        body += (
            f"\nThe {total} statements that remove them are printed on standard output, in the order to run them "
            f"(all of them, not only the first {_PROBLEMS_SHOWN}): {len(own)} on this package's objects and "
            f"{len(outside)} in a second block marked NOT THIS PACKAGE'S OBJECTS."
        )
        by_name = sum(1 for p in problems if not p.fix and p.by_hand == "name")
        by_system = sum(1 for p in problems if not p.fix and p.by_hand == "system")
        other = sum(1 for p in problems if not p.fix) - by_name - by_system
        if by_name or by_system or other:
            parts = []
            if by_name:
                parts.append(
                    f"{by_name} because a name holds a character that is not copied into a printed line"
                )
            if by_system:
                parts.append(f"{by_system} because the object belongs to the server itself")
            if other:
                parts.append(f"{other} for the reason its line gives")
            body += (
                f"\nFor {by_name + by_system + other} of them no statement is printed: {', '.join(parts)}; "
                "a person decides those by hand."
            )
        body += (
            "\nmigrate did not remove anything itself. Until a person has run the statements, the roles named above "
            "can do more than the grant map allows."
            "\nThis check ran after the commit, on a new connection, as the migration role; what it found was made by "
            "this run or by another session since the commit. A file written to do harm can also cheat this check; "
            'see "What migrate promises" in CHANGELOG.md.'
        )
    return AppliedNotVerifiedError(
        f"{head}\n{body}",
        applied=applied,
        problems=problems,
        statements=[*own, *outside],
        could_not_run=could_not_run,
        commit_unknown=commit_unknown,
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
    applied: list[str] = []
    step = ["taking the migration lock"]  # what the run is doing, for the error of a limit
    named_roles = {
        role: kind
        for role, kind in (
            (runtime_role, "runtime"),
            (portal_role, "portal"),
            (purge_role, "purge"),
        )
        if role is not None
    }
    try:
        with connect(
            dsn, iam_auth=iam_auth, region=region, sslmode=sslmode, sslrootcert=sslrootcert
        ) as db:
            reached_commit = False
            try:
                with db.transaction():
                    _take_the_lock(db, lock_wait_seconds)
                    # the hand recipe's two limits (one constant); `SET LOCAL` ends with this transaction
                    for limit in RECIPE_TIMEOUTS:
                        db.execute(limit)
                    step[0] = "checking the migration role"
                    check_version(_fetch_version(db))
                    schema, me, login = db.execute(_RUN_IDENTITY_SQL).fetchone()
                    schema = schema or ""  # read once; passed on
                    with pinned_read(db, RECIPE_TIMEOUTS):
                        _refuse_privileged_role(db)
                        owner_row = db.execute(_SCHEMA_OWNER_SQL, (schema,)).fetchone()
                    schema_owner = owner_row[0] if owner_row else ""
                    with pinned_read(db, RECIPE_TIMEOUTS):
                        _refuse_foreign_owned(db, schema, texts.values())
                    db.execute(
                        "CREATE TABLE IF NOT EXISTS schema_migrations "
                        "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
                    )
                    step[0] = "reading the ledger"
                    done = {
                        r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()
                    }
                    if gone := gone_message(done, files):
                        raise MigrationNumberError([gone])
                    if late := order_problems(done, files, texts, schema):
                        raise MigrationNumberError(late)
                    pending = [p for p in files if p.stem not in done]
                    # step 2: what the database already holds, before any file runs. Two kinds are repaired by step 4
                    # and so are not refused here; the named roles' USAGE on the schema is given by step 4 too, so a
                    # missing USAGE is judged at step 6 only.
                    step[0] = "checking the rights the database already holds"
                    before = [
                        p
                        for p in _state_problems(
                            db,
                            me=me,
                            login=login,
                            named_roles=named_roles,
                            schema=schema,
                            texts=texts.values(),
                            schema_owner=schema_owner,
                        )
                        if not p.repaired_by_run and p.kind != "missing_schema_usage"
                    ]
                    if before:
                        raise ConfigError(
                            "before any migration file ran, this database already holds rights that the grant map "
                            f"does not give:\n{_problem_lines(before)}\nNothing was changed. No file ran. What to "
                            "do: a database administrator runs the statements printed with each line (or removes "
                            "the cause named there), then run migrate again."
                        )
                    if pending:
                        saved = _read_back(db, schema, named)
                        _refuse_unusual_strings(saved)
                    for path in pending:  # step 3
                        step[0] = f"applying {path.name}"
                        db.execute(texts[path])  # the text that was scanned, never a second read
                        saved = _check_read_back(
                            db,
                            saved,
                            path.name,
                            frozenset(c for c in allowed_changes if c.migration == path.stem),
                            named,
                            schema=schema,
                        )
                        with pinned_read(db, RECIPE_TIMEOUTS):
                            _recheck_roles(db, named, path.name)
                        db.execute(
                            "INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,)
                        )
                        applied.append(path.stem)
                    step[0] = "granting the roles"  # step 4: every write of the runner itself
                    if runtime_role:
                        _apply_grants(db, schema, runtime_role, lambda g: g.runtime)
                    if purge_role:
                        _apply_grants(
                            db, schema, purge_role, lambda g: g.purge, lambda g: g.purge_cols
                        )
                    if portal_role:
                        _apply_grants(
                            db, schema, portal_role, lambda g: "SELECT" if g.portal else ""
                        )
                    _revoke_default_execute(db, schema, me, login, texts.values())
                    step[0] = "running the deferred checks and triggers early"  # step 5
                    try:
                        db.execute("SET CONSTRAINTS ALL IMMEDIATE")
                    except psycopg.Error as e:
                        if (plain := _limit_error(e, step[0])) is not None:
                            raise plain from e
                        raise ConfigError(
                            "a deferred check or trigger failed when migrate ran it before the commit: "
                            f"{_label(str(e.diag.message_primary or e))}. Nothing was kept."
                        ) from e
                    step[0] = "checking the database once more before the commit"  # step 6
                    if pending:
                        _check_read_back(db, saved, END_OF_RUN, frozenset(), named, schema=schema)
                        with pinned_read(db, RECIPE_TIMEOUTS):
                            _recheck_roles(db, named, END_OF_RUN)
                    if problems := _state_problems(
                        db,
                        me=me,
                        login=login,
                        named_roles=named_roles,
                        schema=schema,
                        texts=texts.values(),
                        schema_owner=schema_owner,
                    ):
                        raise ConfigError(
                            "after the migration files and the grants, rights that the grant map does not give are "
                            f"in place:\n{_problem_lines(problems)}\nThe whole run is rolled back; the database is as "
                            "it was before this run, unless a file ended the transaction itself (that is reported "
                            "separately above). What to do: (1) if a migration file made it, remove that statement "
                            "from the file; (2) if no file did, a database administrator runs the statement printed "
                            "with the line; (3) run migrate again."
                        )
                    reached_commit = True
                # leaving `db.transaction()` is the COMMIT (step 7)
            except psycopg.Error as e:
                if not reached_commit:
                    raise
                if _commit_outcome(e, db) == "refused":
                    raise ConfigError(
                        f"the database server refused the commit ({getattr(e, 'sqlstate', None)}: "
                        f"{_label(str(e.diag.message_primary or e))}). Nothing was kept; run migrate again."
                    ) from e
                raise _after_commit(applied, [], commit_unknown=True) from e
    except (pg_errors.LockNotAvailable, pg_errors.QueryCanceled) as e:
        if (plain := _limit_error(e, step[0])) is None:
            raise
        raise plain from e
    # step 8: a new connection, one snapshot, no lock. Any failure here is "applied but not verified", never "refused".
    try:
        with connect(
            dsn, iam_auth=iam_auth, region=region, sslmode=sslmode, sslrootcert=sslrootcert
        ) as after:
            after.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            after.read_only = True
            problems = _state_problems(
                after,
                me=me,
                login=login,
                named_roles=named_roles,
                schema=schema,
                texts=texts.values(),
                schema_owner=schema_owner,
            )
    except Exception as e:  # any error at all: the commit happened and the check did not finish
        raise _after_commit(applied, [], could_not_run=type(e).__name__) from e
    if problems:
        raise _after_commit(applied, problems)
    return applied
