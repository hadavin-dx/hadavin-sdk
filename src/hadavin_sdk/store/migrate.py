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
    purge: str = (
        ""  # table-level privileges of the purge role (the evidence deleter) on this relation
    )
    # Columns the purge role may SELECT (a DELETE's WHERE needs them) and nothing else: it cannot read a stored
    # original or a tool result.
    purge_cols: tuple[str, ...] = ()
    # AK-G2-a: the three inbound logins (door, dispatch, re-run owner). Each field is a privilege list for the whole
    # relation, plus the columns that role may SELECT or UPDATE alone. All empty = the role gets nothing here.
    door: str = ""
    door_select_cols: tuple[str, ...] = ()
    dispatch: str = ""
    dispatch_select_cols: tuple[str, ...] = ()
    dispatch_update_cols: tuple[str, ...] = ()
    rerun: str = ""
    rerun_select_cols: tuple[str, ...] = ()
    rerun_update_cols: tuple[str, ...] = ()


_RUN_VIEW_COLS = (
    "run_id",
    "agent_id",
    "principal_id",
    "trigger_ref",
    "state",
    "reason_code",
    "updated_at",
)
_RW = "SELECT, INSERT, UPDATE"
_APPEND = "SELECT, INSERT"  # written once, never changed
# The one grant map. Audit rows and checkpoints are read and appended only (their triggers also refuse UPDATE,
# DELETE and TRUNCATE to any role); reconcile deletes an outbox row once it is in the chain. A later PR adds its
# relations here (K5-core `redaction_maps`, K6 labels and reports, ...); the portal list never holds
# `redaction_maps`, `events`, `tick_state.detail` or secrets.
GRANTS: dict[str, Grant] = {
    "runs": Grant(
        "table",
        _RW,
        portal=True,
        purge_cols=("run_id", "state", "updated_at"),
        dispatch_select_cols=_RUN_VIEW_COLS,
        rerun_select_cols=("run_id", "state"),
    ),
    "plans": Grant("table", _RW, portal=True),
    "gate_decisions": Grant("table", _APPEND, portal=True),
    "approval_requests": Grant("table", _RW, portal=True),
    "approval_decisions": Grant("table", _APPEND, portal=True),
    "dead_letters": Grant("table", _APPEND, dispatch=_APPEND),
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
    "dead_letters_seq_seq": Grant("sequence", "USAGE", dispatch="USAGE"),
    # AK-G2-a: the inbound ledger. The runtime and portal roles get nothing. Door = append a receipt, its text and
    # the first key check; dispatch = claim, release, finish, read the text, the key check; re-run owner = reopen;
    # purge = delete final texts (it never reads one). Nobody gets DELETE on receipts or TRUNCATE on anything.
    "inbound_receipts": Grant(
        "table",
        "",
        purge_cols=("tenant", "source", "delivery_key", "state", "run_id", "updated_at"),
        door="INSERT",
        door_select_cols=(
            "tenant",
            "source",
            "delivery_key",
            "body_sha256",
            "reuse_of",
            "state",
            "readers",
        ),
        dispatch="SELECT",
        dispatch_update_cols=(
            "state",
            "attempts",
            "lease_until",
            "claim_token",
            "reason",
            "last_reason",
            "updated_at",
        ),
        rerun="SELECT",
        rerun_update_cols=(
            "state",
            "generation",
            "run_id",
            "attempts",
            "reason",
            "last_reason",
            "lease_until",
            "claim_token",
            "updated_at",
        ),
    ),
    "inbound_bodies": Grant(
        "table",
        "",
        purge="DELETE",
        purge_cols=("tenant", "source", "delivery_key"),
        door="INSERT",
        dispatch="SELECT",
    ),
    "inbound_key_checks": Grant(
        "table",
        "",
        door="INSERT",
        door_select_cols=("tenant", "source", "key_check"),
        dispatch="SELECT",
        dispatch_update_cols=("key_check", "set_at"),
    ),
    "inbound_rerun_owner": Grant("table", "", rerun="SELECT"),
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


def _apply_grants(db, role_name: str, privileges, columns=None, update_columns=None) -> None:
    """Reset the role's rights on every relation in `GRANTS`, then give back what `privileges(grant)` names; with
    `columns` / `update_columns`, also the single columns it may SELECT / UPDATE (a column-only UPDATE grant is
    `GRANT UPDATE (cols)`, never a table-level one). Both default to None: today's calls issue the same statements."""
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
        if update_columns is not None and (cols := update_columns(grant)):
            db.execute(
                sql.SQL("GRANT UPDATE ({}) ON {} TO {}").format(
                    sql.SQL(", ").join(sql.Identifier(c) for c in cols), rel, role
                )
            )


_TABLE_PRIVS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")


def effective_problems(
    db, role: str, expected_table, expected_cols=None, expected_update_cols=None
) -> list[str]:
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
        allowed_update_cols = (
            set(expected_update_cols(grant)) if (grant and expected_update_cols) else set()
        )
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
                if (
                    p in allowed
                    or (p == "SELECT" and col in allowed_cols)
                    or (p == "UPDATE" and col in allowed_update_cols)
                ):
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


INBOUND_FUNCTIONS = (
    "hadavin_inbound_receipt_update",
    "hadavin_inbound_receipt_insert",
    "hadavin_inbound_body_insert",
)


def _pin_inbound_functions(db) -> None:
    """On every run: pin each inbound trigger function to `<current schema>, pg_temp`, so a caller's temporary
    table can never shadow `inbound_rerun_owner` or `runs`."""
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    for fn in INBOUND_FUNCTIONS:
        db.execute(
            sql.SQL("ALTER FUNCTION {}() SET search_path = {}, pg_temp").format(
                sql.Identifier(fn), sql.Identifier(schema)
            )
        )


def _bind_rerun_owner(db, role_name: str) -> None:
    """Record the one re-run owner. An earlier owner of another name loses every right on every `GRANTS` relation."""
    old = db.execute("SELECT role_name FROM inbound_rerun_owner WHERE id").fetchone()
    if old is not None and old[0] != role_name:
        _apply_grants(db, old[0], lambda g: "")
    db.execute(
        "INSERT INTO inbound_rerun_owner (id, role_name) VALUES (true, %s) "
        "ON CONFLICT (id) DO UPDATE SET role_name = EXCLUDED.role_name",
        (role_name,),
    )


def _check_rerun_holders(db, role_name: str) -> None:
    """Exactly one role other than the table owner and superusers may UPDATE `generation`, and it is the re-run
    owner (a role that cannot log in). A stray holder is refused; the transaction rolls back."""
    rows = db.execute(
        "SELECT r.rolname FROM pg_roles r WHERE NOT r.rolsuper AND r.rolname NOT LIKE 'pg\\_%' "
        "AND r.oid <> (SELECT relowner FROM pg_class WHERE oid = to_regclass('inbound_receipts')) "
        "AND has_column_privilege(r.oid, to_regclass('inbound_receipts'), 'generation', 'UPDATE')"
    ).fetchall()
    others = sorted(r[0] for r in rows if r[0] != role_name)
    if others or [r[0] for r in rows] != [role_name]:
        raise ConfigError(
            "another role can re-run an inbound message (UPDATE on inbound_receipts.generation): "
            + ", ".join(others or ["(the re-run owner has lost it)"])
            + "; revoke it by hand"
        )


def migrate(
    dsn: str,
    *,
    runtime_role: str | None = None,
    portal_role: str | None = None,
    purge_role: str | None = None,
    inbound_door_role: str | None = None,
    inbound_dispatch_role: str | None = None,
    rerun_owner_role: str | None = None,
    iam_auth: bool = False,
    region: str | None = None,
    sslmode: str | None = None,
    sslrootcert: str | None = None,
) -> list[str]:
    """Apply pending migrations; return the versions applied by this call. With `runtime_role`, give it the
    privileges `GRANTS` lists (never TRUNCATE; DELETE only on the outbox and the purged evidence tables). With `portal_role`, SELECT on the
    relations marked `portal` and nothing else. The ledger and the grant map are checked first: a bad file name,
    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database."""
    inbound = {
        "--inbound-door-role": inbound_door_role,
        "--inbound-dispatch-role": inbound_dispatch_role,
        "--rerun-owner-role": rerun_owner_role,
    }
    if 0 < sum(v is not None for v in inbound.values()) < len(inbound):  # before any connection
        raise ConfigError(
            "the three inbound roles are given together or not at all; missing: "
            + ", ".join(k for k, v in inbound.items() if v is None)
        )
    all_roles = (runtime_role, portal_role, purge_role, *inbound.values())
    for role in all_roles:
        if role is not None and not _ROLE.fullmatch(role):
            raise ConfigError(f"not a plain database role name: {role!r}")
    named = [r for r in all_roles if r is not None]
    if len(set(named)) != len(named):
        raise ConfigError(
            "the runtime, portal, purge, inbound door, inbound dispatch and re-run owner roles must be different roles"
        )
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
        if rerun_owner_role:
            can_login = db.execute(
                "SELECT rolcanlogin FROM pg_roles WHERE rolname = %s", (rerun_owner_role,)
            ).fetchone()
            if can_login is None or can_login[0]:
                raise ConfigError("the re-run owner role must exist and must not be able to log in")
        known = {
            r[0]
            for r in db.execute(
                "SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)", (named,)
            ).fetchall()
        }
        if missing := sorted(set(named) - known):
            raise ConfigError(  # before pg_has_role, which raises a raw database error for a name that does not exist
                "these database roles do not exist: " + ", ".join(missing) + "; create them first"
            )
        q = "SELECT pg_has_role(%s, %s, 'MEMBER')"  # a member keeps the other's rights, whatever we REVOKE
        for a in named:
            for b in named:
                if a != b and db.execute(q, (a, b)).fetchone()[0]:
                    raise ConfigError(
                        "the runtime, portal, purge and inbound roles must not be members of each other"
                    )
        if rerun_owner_role:
            _bind_rerun_owner(db, rerun_owner_role)
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
        for role_name, priv, sel, upd in (
            (
                inbound_door_role,
                lambda g: g.door,
                lambda g: g.door_select_cols,
                lambda g: (),
            ),
            (
                inbound_dispatch_role,
                lambda g: g.dispatch,
                lambda g: g.dispatch_select_cols,
                lambda g: g.dispatch_update_cols,
            ),
            (
                rerun_owner_role,
                lambda g: g.rerun,
                lambda g: g.rerun_select_cols,
                lambda g: g.rerun_update_cols,
            ),
        ):
            if not role_name:
                continue
            _apply_grants(db, role_name, priv, sel, upd)
            if bad := effective_problems(
                db,
                role_name,
                lambda g, f=priv: f(g) if g else "",
                lambda g, f=sel: f(g) if g else (),
                lambda g, f=upd: f(g) if g else (),
            ):
                raise ConfigError(
                    f"the inbound role {role_name} holds more than the grant map: "
                    + "; ".join(bad[:20])
                )
        if rerun_owner_role:
            _check_rerun_holders(db, rerun_owner_role)
        if portal_role:
            _apply_grants(db, portal_role, lambda g: "SELECT" if g.portal else "")
            if extra := _excess_privileges(db, portal_role):
                raise ConfigError(  # e.g. inherited from another role: REVOKE cannot take those away
                    f"the portal role holds privileges outside the portal grant map: {', '.join(extra)}"
                )
        _pin_inbound_functions(db)
    return applied
