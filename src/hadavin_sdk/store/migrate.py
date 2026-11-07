"""Forward-only schema migrations for the Postgres store (`hadavin-sdk migrate`).

Run under a migration role, never by the runtime. Every pending `migrations/NNNN_*.sql` file is applied in one
transaction under a transaction-scoped advisory lock, so two concurrent runs apply each file once. Pattern
ported from WARDEN `audit.py:migrate` (main a1e76cbf). Rollback = restore the snapshot taken before migrating.

The file-name rules, the late-file and gone-name refusals and the SQL text rules live in `migration_numbers`
(no database library there); this module only calls them. Each file is read ONCE; the text that was scanned is
the text that is executed. After each file, in the same transaction, `migrate` reads back the database user
names (the current user and the session user), the replication-role setting, the search path, three settings that
change how SQL text is read, the transaction clock and id, the role memberships (`pg_auth_members`: a role granted to a role inside a function body is
found here, not by the statement rule) and the state of every trigger in the migration schema,
and refuses if anything is LEFT changed (it cannot see a change that a file makes and undoes before it ends). Precondition: the migration role is not a superuser (a superuser can change
what the read-back does not read).

When `migrate` refuses, a database administrator repairs by hand (the full runbook, cases (a) to (g), is the section
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
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from psycopg import sql

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.migration_numbers import (
    MIGRATE_LOCK,
    MIGRATIONS,
    RECIPE_TIMEOUTS,
    MigrationNumberError,
    check_ledger,
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
# relations here (K5-core `redaction_maps`, K6 labels and reports, ...); the portal list never holds
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
    # K5-core: append and purge only (no UPDATE); `redaction_maps` is never portal-readable.
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


# SHA-256 of every released migration file (forward-only: a released file is never edited, renumbered or deleted).
# It ships with the package, so `migrate` itself can refuse a changed file; add a row when a release is cut.
RELEASED_MANIFEST = MIGRATIONS.parent / "migrations_released.json"
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _released_manifest() -> dict[str, str]:
    try:
        data = json.loads(RELEASED_MANIFEST.read_text(encoding="utf-8"))
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
# The nine values are compared with the values saved before the first file; `transaction_timestamp()` and
# `txid_current()` are the backstop for a COMMIT the text rules did not see (a COMMIT starts a new transaction).
_READBACK_VALUES = (
    "current_user",
    "session_user",
    "session_replication_role",
    "search_path",
    "standard_conforming_strings",
    "backslash_quote",
    "client_encoding",
    "transaction_timestamp",
    "txid_current",
)
_READBACK_VALUES_SQL = (
    "SELECT current_user, session_user, current_setting('session_replication_role'), "
    "current_setting('search_path'), current_setting('standard_conforming_strings'), "
    "current_setting('backslash_quote'), current_setting('client_encoding'), "
    "transaction_timestamp(), txid_current()"
)
# Role memberships (who is a member of whom, with the grant options): the one thing a `$$` function body can change
# that no statement-start rule sees (`GRANT r TO s` inside a function, then `SELECT f();`). Names, not OIDs.
_READBACK_MEMBERS_SQL = (
    "SELECT m.roleid::regrole::text, m.member::regrole::text, "
    "(to_jsonb(m) - 'oid' - 'roleid' - 'member')::text FROM pg_auth_members m"
)
# Triggers of the migration schema only (the schema `current_schema()` names now); internal ones are skipped.
_READBACK_TRIGGERS_SQL = (
    "SELECT t.tgrelid, t.tgname, t.tgenabled, c.relname, n.nspname FROM pg_trigger t "
    "JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
    "WHERE NOT t.tgisinternal AND n.nspname = current_schema()"
)


@dataclass(frozen=True)
class _Saved:
    values: tuple
    triggers: dict  # (schema, table, tgname) -> (tgenabled, schema, table): a name, so a recreated table is the same trigger
    members: frozenset = frozenset()  # (role, member, other columns as text)


def _read_back(db) -> _Saved:
    values = tuple(db.execute(_READBACK_VALUES_SQL).fetchone())
    triggers = {
        (schema, table, name): (enabled, schema, table)
        for _relid, name, enabled, table, schema in db.execute(_READBACK_TRIGGERS_SQL).fetchall()
    }
    members = frozenset(tuple(r) for r in db.execute(_READBACK_MEMBERS_SQL).fetchall())
    return _Saved(values, triggers, members)


def _refuse_unusual_strings(saved: _Saved) -> None:
    """The lexer reads strings as `standard_conforming_strings = on` does; any other start value is refused."""
    value = saved.values[_READBACK_VALUES.index("standard_conforming_strings")]
    if value != "on":
        raise ConfigError(
            f"standard_conforming_strings is {value!r} for this session; migrate needs 'on' "
            "(the file checks read strings the way 'on' does)"
        )


def _label(*names: str) -> str:
    """Names of database objects for a message: control characters are written as escapes."""
    return ".".join(ascii(n)[1:-1] for n in names)


def _check_read_back(db, saved: _Saved, file_name: str) -> _Saved:
    """Read again after `file_name` and compare. The nine values in `_READBACK_VALUES` (seven user and setting
    values, then the transaction clock and id) must equal the values saved before the first file; a saved trigger must still exist; no trigger may be
    disabled (`D`) or replica-only (`R`) unless it already was; the set of role memberships must equal the saved set. Refuses with every difference named. Returns the
    trigger state just read (the base for the next file); the saved values stay those of the start."""
    now = _read_back(db)
    problems = [
        f"{item} was {old!a} and is now {new!a}"
        for item, old, new in zip(_READBACK_VALUES, saved.values, now.values, strict=True)
        if old != new
    ]
    for key, (_enabled, schema, table) in sorted(saved.triggers.items(), key=lambda kv: str(kv[0])):
        if key not in now.triggers:
            problems.append(f"trigger {_label(schema, table, key[2])} no longer exists")
    for key, (enabled, schema, table) in sorted(now.triggers.items(), key=lambda kv: str(kv[0])):
        before = saved.triggers.get(key)
        if enabled in ("D", "R") and (before is None or before[0] != enabled):
            problems.append(
                f"trigger {_label(schema, table, key[2])} is now "
                f"{'disabled' if enabled == 'D' else 'replica-only'}"
            )
    problems += [
        f"role {_label(role)} has a new member {_label(member)} ({_label(rest)})"
        for role, member, rest in sorted(now.members - saved.members)
    ]
    problems += [
        f"role {_label(role)} lost the member {_label(member)} ({_label(rest)})"
        for role, member, rest in sorted(saved.members - now.members)
    ]
    if problems:
        raise ConfigError(
            f"migration {ascii(file_name)[1:-1]} left the database session changed: "
            + "; ".join(problems)
        )
    return _Saved(saved.values, now.triggers, saved.members)


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
    lock (so a second run still waits for the first) the run sets the two `SET LOCAL` limits of `RECIPE_TIMEOUTS`
    (a lock limit and a statement limit, the same lines the hand recipe sets): a file that waits for a table lock or
    runs longer fails the whole run and keeps nothing; apply such a file by hand with a raised number.

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
    if problems := released_problems(MIGRATIONS, _released_manifest()):
        raise MigrationNumberError(
            problems
        )  # a released file edited, deleted, or a new file numbered below it
    texts = read_files(files)  # the only read of each file: the text scanned is the text executed
    if problems := check_grants(files, texts=texts):
        raise ConfigError("migrations are inconsistent: " + "; ".join(problems))
    applied = []
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
        db.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        done = {r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()}
        if gone := gone_message(done, files):
            raise MigrationNumberError([gone])
        schema = db.execute("SELECT current_schema()").fetchone()[0] or ""
        if late := order_problems(done, files, texts, schema):
            raise MigrationNumberError(late)
        pending = [p for p in files if p.stem not in done]
        if pending:
            saved = _read_back(db)
            _refuse_unusual_strings(saved)
        for path in pending:
            db.execute(texts[path])  # the text that was scanned, never a second read
            saved = _check_read_back(db, saved, path.name)
            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
            applied.append(path.stem)
        q = "SELECT pg_has_role(%s, %s, 'MEMBER')"  # a member keeps the other's rights, whatever we REVOKE
        for a in named:
            for b in named:
                if a != b and db.execute(q, (a, b)).fetchone()[0]:
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
                db, purge_role, lambda g: g.purge if g else "", lambda g: g.purge_cols if g else ()
            ):
                raise ConfigError(
                    "the purge role holds more than the grant map: " + "; ".join(bad[:20])
                )
        if portal_role:
            _apply_grants(db, portal_role, lambda g: "SELECT" if g.portal else "")
            if extra := _excess_privileges(db, portal_role):
                raise ConfigError(  # e.g. inherited from another role: REVOKE cannot take those away
                    f"the portal role holds privileges outside the portal grant map: {', '.join(extra)}"
                )
    return applied
