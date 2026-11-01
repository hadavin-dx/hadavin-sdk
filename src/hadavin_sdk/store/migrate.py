"""Forward-only schema migrations for the Postgres store (`hadavin-sdk migrate`).

Run under a migration role, never by the runtime. Every pending `migrations/NNNN_*.sql` file is applied in one
transaction under a transaction-scoped advisory lock, so two concurrent runs apply each file once. Pattern
ported from WARDEN `audit.py:migrate` (main a1e76cbf). Rollback = restore the snapshot taken before migrating.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from psycopg import sql

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.postgres import connect

MIGRATIONS = Path(__file__).parent / "migrations"


@dataclass(frozen=True)
class Grant:
    """What the roles get on one relation. `runtime` is the privilege list for the runtime role; `portal` says the
    read-only portal role may SELECT it. A relation not in `GRANTS` gets nothing, so `check_grants` (run by
    `migrate` and by CI) refuses a migration that creates one."""

    kind: Literal["table", "view", "sequence"]
    runtime: str
    portal: bool = False


_RW = "SELECT, INSERT, UPDATE"
_APPEND = "SELECT, INSERT"  # written once, never changed
# The one grant map. Audit rows and checkpoints are read and appended only (their triggers also refuse UPDATE,
# DELETE and TRUNCATE to any role); reconcile deletes an outbox row once it is in the chain. A later PR adds its
# relations here (K5-core `redaction_maps`, K6 labels and reports, ...); the portal list never holds
# `redaction_maps`, `events`, `tick_state.detail` or secrets.
GRANTS: dict[str, Grant] = {
    "runs": Grant("table", _RW, portal=True),
    "plans": Grant("table", _RW, portal=True),
    "gate_decisions": Grant("table", _APPEND, portal=True),
    "approval_requests": Grant("table", _RW, portal=True),
    "approval_decisions": Grant("table", _APPEND, portal=True),
    "dead_letters": Grant("table", _APPEND),
    "spend": Grant("table", _RW),
    "spend_month": Grant("table", _RW),
    "kill_switch": Grant("table", _RW),
    "tick_state": Grant("table", _RW),
    "reservations": Grant("table", "SELECT, INSERT, DELETE"),
    "audit_entries": Grant("table", _APPEND, portal=True),
    "audit_checkpoints": Grant("table", _APPEND, portal=True),
    "audit_outbox": Grant("table", "SELECT, INSERT, DELETE"),
    "approval_decisions_seq_seq": Grant("sequence", "USAGE"),
    "dead_letters_seq_seq": Grant("sequence", "USAGE"),
}
_LOCK = int.from_bytes(b"hadvnmig", "big") >> 1  # one fixed key for every migrate run
_ROLE = re.compile(r"[a-z_][a-z0-9_]{0,62}")
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


def _apply_grants(db, role_name: str, privileges) -> None:
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


def migrate(
    dsn: str,
    *,
    runtime_role: str | None = None,
    portal_role: str | None = None,
    iam_auth: bool = False,
    region: str | None = None,
    sslmode: str | None = None,
    sslrootcert: str | None = None,
) -> list[str]:
    """Apply pending migrations; return the versions applied by this call. With `runtime_role`, give it the
    privileges `GRANTS` lists (never TRUNCATE; DELETE only on the outbox). With `portal_role`, SELECT on the
    relations marked `portal` and nothing else. The ledger and the grant map are checked first: a bad file name,
    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database."""
    for role in (runtime_role, portal_role):
        if role is not None and not _ROLE.fullmatch(role):
            raise ConfigError(f"not a plain database role name: {role!r}")
    if runtime_role is not None and runtime_role == portal_role:
        raise ConfigError("the runtime role and the portal role must be different roles")
    files = _migration_files()
    if problems := check_ledger(files) + check_grants(files):
        raise ConfigError("migrations are inconsistent: " + "; ".join(problems))
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
            raise ConfigError(f"applied migrations have no file in this release: {', '.join(gone)}")
        for path in files:
            if path.stem in done:
                continue
            db.execute(path.read_text(encoding="utf-8"))  # a file shipped in this package
            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
            applied.append(path.stem)
        if runtime_role and portal_role:
            q = "SELECT pg_has_role(%s, %s, 'MEMBER')"  # a member keeps the other's rights, whatever we REVOKE
            if (
                db.execute(q, (runtime_role, portal_role)).fetchone()[0]
                or db.execute(q, (portal_role, runtime_role)).fetchone()[0]
            ):
                raise ConfigError(
                    "the runtime role and the portal role must not be members of each other"
                )
        if runtime_role:
            _apply_grants(db, runtime_role, lambda g: g.runtime)
        if portal_role:
            _apply_grants(db, portal_role, lambda g: "SELECT" if g.portal else "")
            if extra := _excess_privileges(db, portal_role):
                raise ConfigError(  # e.g. inherited from another role: REVOKE cannot take those away
                    f"the portal role holds privileges outside the portal grant map: {', '.join(extra)}"
                )
    return applied
