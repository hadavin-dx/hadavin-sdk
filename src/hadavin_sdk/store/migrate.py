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

from psycopg import errors as pg_errors
from psycopg import sql

from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.postgres import connect, table_privileges

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
    reset: str = ""  # privilege list of the reset group (the only role that may clear a stop)
    stop: str = ""  # privilege list of the stop login


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
    "spend_reservations": Grant("table", _RW),  # no DELETE: v1 has no pruning (P4d-b)
    # A stop is an INSERT through a function (the owner's rights); no role holds any right on these tables.
    "kill_switch": Grant("table", ""),
    "kill_switch_stop_requests": Grant("table", ""),
    "kill_switch_stop_requests_id_seq": Grant("sequence", ""),
    "kill_switch_login_labels": Grant("table", ""),
    "kill_switch_resets": Grant("table", "SELECT"),
    "kill_switch_state": Grant("view", "SELECT", reset="SELECT", stop="SELECT"),
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


# --- the three kill-switch functions, re-issued by `migrate()` on every run -----------------------------------------
# `{S}` is the schema (an identifier), `{N}` the cap on open stop requests and `{GROUP}` the reset group (literals).
# Every literal brace is doubled because the text goes through `sql.SQL(...).format`.
_RETURNS = 'RETURNS TABLE ("on" boolean, "by" text, ts timestamptz, schema_version int, version bigint, open_requests int)'
_LABEL_RE = "'^id:[A-Za-z0-9_-]{1,32}:[0-9a-f]{32}$'"  # passed as an argument, so its braces are not doubled
_STOP_FN = """CREATE OR REPLACE FUNCTION {S}.hadavin_kill_switch_stop(p_by text) {RETURNS}
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$
DECLARE n int;
BEGIN
  IF p_by IS NULL OR p_by !~ {LABEL} THEN
    RAISE EXCEPTION 'kill switch: stop label not accepted' USING ERRCODE = 'HD004'; END IF;
  PERFORM 1 FROM {S}.kill_switch k WHERE k.id = 1;
  SELECT count(*) INTO n FROM (SELECT 1 FROM {S}.kill_switch_stop_requests WHERE cleared_by IS NULL LIMIT {N}) q;
  IF n < {N} THEN
    INSERT INTO {S}.kill_switch_stop_requests ("by") VALUES (p_by);
  END IF;
  RETURN QUERY SELECT s."on", s."by", s.ts, s.schema_version, s.version, s.open_requests
               FROM {S}.kill_switch_state s;
  IF NOT FOUND THEN
    RETURN QUERY SELECT true,
                        coalesce((SELECT r."by" FROM {S}.kill_switch_stop_requests r
                                  WHERE r.cleared_by IS NULL ORDER BY r.id LIMIT 1), p_by),
                        now(), 1, 0::bigint,
                        (SELECT count(*) FROM {S}.kill_switch_stop_requests WHERE cleared_by IS NULL)::int;
  END IF;
END $f$"""
_RESET_FN = """CREATE OR REPLACE FUNCTION {S}.hadavin_kill_switch_reset(p_by text, p_expected_version bigint,
  p_expected_open int) {RETURNS}
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$
DECLARE v bigint; was_on boolean; n int;
BEGIN
  IF p_by IS NULL OR p_by !~ {LABEL} THEN
    RAISE EXCEPTION 'kill switch: name not accepted' USING ERRCODE = 'HD004'; END IF;
  SELECT k.version, k."on" INTO v, was_on FROM {S}.kill_switch k WHERE k.id = 1 FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'kill switch: row missing' USING ERRCODE = 'HD005'; END IF;
  IF p_expected_version IS NULL OR v <> p_expected_version THEN
    RAISE EXCEPTION 'kill switch: the version changed' USING ERRCODE = 'HD003'; END IF;
  UPDATE {S}.kill_switch_stop_requests r SET cleared_by = v + 1 WHERE r.cleared_by IS NULL;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF p_expected_open IS NULL OR n <> p_expected_open OR (n = 0 AND NOT was_on) THEN
    RAISE EXCEPTION 'kill switch: the open count changed' USING ERRCODE = 'HD003'; END IF;
  IF NOT was_on THEN UPDATE {S}.kill_switch SET "on" = true WHERE id = 1; END IF;
  UPDATE {S}.kill_switch SET "on" = false WHERE id = 1;
  RETURN QUERY SELECT s."on", s."by", s.ts, s.schema_version, s.version, s.open_requests
               FROM {S}.kill_switch_state s;
END $f$"""
_GUARD_FN = """CREATE OR REPLACE FUNCTION {S}.hadavin_kill_switch_guard() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$
DECLARE lbl text;
BEGIN
  IF OLD."on" AND NOT NEW."on" THEN
    IF NOT pg_has_role(session_user, {GROUP}::text, 'MEMBER') THEN
      RAISE EXCEPTION 'kill switch: only the reset role may clear it' USING ERRCODE = 'HD001'; END IF;
    SELECT l.label INTO lbl FROM {S}.kill_switch_login_labels l WHERE l.login_name = session_user::text;
    IF lbl IS NULL THEN RAISE EXCEPTION 'kill switch: login not registered' USING ERRCODE = 'HD001'; END IF;
    INSERT INTO {S}.kill_switch_resets VALUES (OLD.version, now(), lbl,
      CASE WHEN OLD."by" IS NULL OR OLD."by" = 'dba' OR OLD."by" ~ {LABEL}
           THEN OLD."by" ELSE 'unlabelled' END);
    NEW."by" := lbl; NEW.version := OLD.version + 1; NEW.ts := now();
  ELSIF NEW."on" AND NOT OLD."on" THEN
    IF NEW."by" IS NOT DISTINCT FROM OLD."by" THEN NEW."by" := NULL; END IF;
    NEW.version := OLD.version; NEW.ts := now();
  ELSE
    NEW."on" := OLD."on"; NEW."by" := OLD."by"; NEW.ts := OLD.ts; NEW.version := OLD.version;
  END IF;
  NEW.id := OLD.id; RETURN NEW;
END $f$"""
_FORBIDDEN_ROLES = frozenset({"public", "none", "session_user", "current_user"})
_GUARD_TRIGGERS = (  # (table, trigger): must stay ENABLE ALWAYS
    ("kill_switch", "kill_switch_guard"),
    ("kill_switch_stop_requests", "kill_switch_stop_requests_update"),
    ("kill_switch_stop_requests", "kill_switch_stop_requests_delete"),
    ("kill_switch_stop_requests", "kill_switch_stop_requests_no_truncate"),
    ("kill_switch_resets", "kill_switch_resets_append_only"),
    ("kill_switch_resets", "kill_switch_resets_no_truncate"),
)
_STOP_SIG = "hadavin_kill_switch_stop(text)"
_RESET_SIG = "hadavin_kill_switch_reset(text, bigint, integer)"
_GUARD_SIG = "hadavin_kill_switch_guard()"  # a trigger function: no role is meant to call it


def _set_lock_timeout(db, ms: int) -> None:
    """The one place the migration's own table-lock bound is set (transaction-local, milliseconds as text)."""
    db.execute("SELECT set_config('lock_timeout', %s, true)", (str(ms),))


def _install_kill_switch(db, schema: str, group: str, cap: int) -> None:
    """Re-issue the three functions (the schema, the cap and the group are written into their text), take
    EXECUTE from PUBLIC, and re-enable a guard trigger that someone disabled. `ENABLE ALWAYS` takes a table lock
    that queues a stop, so it is issued only for a trigger that is not already ALWAYS."""
    s = sql.Identifier(schema)
    for text in (_STOP_FN, _RESET_FN, _GUARD_FN):
        db.execute(
            sql.SQL(text).format(
                S=s,
                N=sql.Literal(cap),
                GROUP=sql.Literal(group),
                RETURNS=sql.SQL(_RETURNS),
                LABEL=sql.SQL(_LABEL_RE),
            )
        )
    for sig in (_STOP_SIG, _RESET_SIG, _GUARD_SIG):
        db.execute(sql.SQL("REVOKE ALL ON FUNCTION {}.{} FROM PUBLIC").format(s, sql.SQL(sig)))
    for table, trigger in _GUARD_TRIGGERS:
        state = db.execute(
            "SELECT t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = %s AND t.tgname = %s",
            (schema, table, trigger),
        ).fetchone()
        if state is None:
            raise ConfigError(f"the kill switch trigger {trigger} is missing")
        if state[0] != "A":
            db.execute(
                sql.SQL("ALTER TABLE {}.{} ENABLE ALWAYS TRIGGER {}").format(
                    s, sql.Identifier(table), sql.Identifier(trigger)
                )
            )


def _grant_execute(db, schema: str, sig: str, role: str | None) -> None:
    if role:
        db.execute(
            sql.SQL("GRANT EXECUTE ON FUNCTION {}.{} TO {}").format(
                sql.Identifier(schema), sql.SQL(sig), sql.Identifier(role)
            )
        )


def _check_kill_switch_roles(db, schema: str, named: list[str], reset_role: str) -> None:
    owners = db.execute(
        "SELECT pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND c.relname LIKE 'kill\\_switch%%' "
        "UNION SELECT pg_get_userbyid(p.proowner) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = %s AND p.proname LIKE 'hadavin\\_kill\\_switch%%'",
        (schema, schema),
    ).fetchall()
    if bad := sorted({r[0] for r in owners} & set(named)):
        raise ConfigError(
            f"a role named for migrate owns the kill switch objects: {', '.join(bad)}"
        )
    login = db.execute(
        "SELECT rolcanlogin FROM pg_roles WHERE rolname = %s", (reset_role,)
    ).fetchone()
    if login is None:
        raise ConfigError(f"the reset role {reset_role!r} does not exist; create it NOLOGIN first")
    if login[0]:
        raise ConfigError(f"the reset role {reset_role!r} must be a NOLOGIN group role")


def _role_defaults(db, runtime_role, stop_role, settings: dict[str, int]) -> None:
    """Role-level defaults for honest code (a session can undo them) and the connection limits."""
    try:
        for role, limit in (
            (runtime_role, settings["runtime_connection_limit"]),
            (stop_role, settings["stop_connection_limit"]),
        ):
            if not role:
                continue
            db.execute(
                sql.SQL("ALTER ROLE {} CONNECTION LIMIT {}").format(
                    sql.Identifier(role), sql.Literal(limit)
                )
            )
            if role == runtime_role:
                for name in (
                    "statement_timeout",
                    "lock_timeout",
                    "idle_in_transaction_session_timeout",
                ):
                    db.execute(
                        sql.SQL("ALTER ROLE {} IN DATABASE {} SET {} = {}").format(
                            sql.Identifier(role),
                            sql.Identifier(db.execute("SELECT current_database()").fetchone()[0]),
                            sql.SQL(name),
                            sql.Literal(str(settings[name])),
                        )
                    )
    except pg_errors.InsufficientPrivilege as exc:
        raise ConfigError(
            "the migration role may not run ALTER ROLE for the runtime or stop role (needs CREATEROLE with "
            "ADMIN on it, or a superuser); nothing was changed"
        ) from exc


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
    privs = table_privileges(db)
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
        for p in privs:
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


def migrate(
    dsn: str,
    *,
    runtime_role: str | None = None,
    portal_role: str | None = None,
    purge_role: str | None = None,
    reset_role: str | None = None,
    stop_role: str | None = None,
    max_open_stop_requests: int = defaults.KILL_SWITCH_MAX_OPEN_STOP_REQUESTS,
    lock_timeout_ms: int = defaults.KILL_SWITCH_MIGRATE_LOCK_TIMEOUT_MS,
    advisory_wait_ms: int = defaults.KILL_SWITCH_MIGRATE_ADVISORY_WAIT_MS,
    role_statement_timeout_ms: int = defaults.KILL_SWITCH_ROLE_STATEMENT_TIMEOUT_MS,
    role_lock_timeout_ms: int = defaults.KILL_SWITCH_ROLE_LOCK_TIMEOUT_MS,
    role_idle_in_transaction_timeout_ms: int = defaults.KILL_SWITCH_ROLE_IDLE_IN_TRANSACTION_TIMEOUT_MS,
    runtime_connection_limit: int = defaults.KILL_SWITCH_RUNTIME_CONNECTION_LIMIT,
    stop_connection_limit: int = defaults.KILL_SWITCH_STOP_CONNECTION_LIMIT,
    iam_auth: bool = False,
    region: str | None = None,
    sslmode: str | None = None,
    sslrootcert: str | None = None,
) -> list[str]:
    """Apply pending migrations; return the versions applied by this call. With `runtime_role`, give it the
    privileges `GRANTS` lists (never TRUNCATE; DELETE only on the outbox and the purged evidence tables). With `portal_role`, SELECT on the
    relations marked `portal` and nothing else. The ledger and the grant map are checked first: a bad file name,
    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database.

    `reset_role` (REQUIRED: the guard function text names it) is the NOLOGIN group whose members may clear a stop;
    `stop_role` is the optional login of the operator's stop. Both get EXECUTE on one function and SELECT on the
    state view, nothing else. The stop and reset functions and the guard are re-issued on every run."""
    for role in (runtime_role, portal_role, purge_role, reset_role, stop_role):
        if role is not None and (not _ROLE.fullmatch(role) or role in _FORBIDDEN_ROLES):
            raise ConfigError(f"not a plain database role name: {role!r}")
    named = [
        r for r in (runtime_role, portal_role, purge_role, reset_role, stop_role) if r is not None
    ]
    if len(set(named)) != len(named):
        raise ConfigError(
            "the runtime, portal, purge, reset and stop roles must be different roles"
        )
    for name, value in (
        ("max_open_stop_requests", max_open_stop_requests),
        ("lock_timeout_ms", lock_timeout_ms),
        ("advisory_wait_ms", advisory_wait_ms),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ConfigError(f"{name} must be an integer of at least 1 (0 means no timeout)")
    files = _migration_files()
    if problems := check_ledger(files) + check_grants(files):
        raise ConfigError("migrations are inconsistent: " + "; ".join(problems))
    if reset_role is None:
        raise ConfigError(
            "migrate needs reset_role: the NOLOGIN group whose members may reset the kill switch"
        )
    applied = []
    with (
        connect(
            dsn, iam_auth=iam_auth, region=region, sslmode=sslmode, sslrootcert=sslrootcert
        ) as db,
        db.transaction(),
    ):
        # Any login can take an advisory lock, so the wait for ours is bounded; then the (shorter) table-lock
        # bound, set AFTER the advisory lock so a second honest `migrate` that waits for this one still goes through.
        db.execute("SELECT set_config('lock_timeout', %s, true)", (str(advisory_wait_ms),))
        try:
            db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK,))
        except pg_errors.LockNotAvailable as exc:
            raise ConfigError(
                "another session holds the migration lock; see the runbook (pg_locks, locktype advisory)"
            ) from exc
        _set_lock_timeout(db, lock_timeout_ms)
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
            # A file may SET LOCAL its own (longer) lock_timeout, and that would stay for every later file and for
            # the role and function steps. The configured bound is put back after every file.
            _set_lock_timeout(db, lock_timeout_ms)
            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
            applied.append(path.stem)
        q = "SELECT pg_has_role(%s, %s, 'MEMBER')"  # a member keeps the other's rights, whatever we REVOKE
        for a in named:
            for b in named:
                if a != b and db.execute(q, (a, b)).fetchone()[0]:
                    raise ConfigError(
                        "the runtime, portal, purge, reset and stop roles must not be members of each other"
                    )
        schema = db.execute("SELECT current_schema()").fetchone()[0]
        _check_kill_switch_roles(db, schema, named, reset_role)
        _install_kill_switch(db, schema, reset_role, max_open_stop_requests)
        _grant_execute(db, schema, _STOP_SIG, runtime_role)
        _grant_execute(db, schema, _STOP_SIG, stop_role)
        _grant_execute(db, schema, _RESET_SIG, reset_role)
        _role_defaults(
            db,
            runtime_role,
            stop_role,
            {
                "statement_timeout": role_statement_timeout_ms,
                "lock_timeout": role_lock_timeout_ms,
                "idle_in_transaction_session_timeout": role_idle_in_transaction_timeout_ms,
                "runtime_connection_limit": runtime_connection_limit,
                "stop_connection_limit": stop_connection_limit,
            },
        )
        for role, pick in ((reset_role, lambda g: g.reset), (stop_role, lambda g: g.stop)):
            if role is None:
                continue
            _apply_grants(db, role, pick)
            if bad := effective_problems(db, role, lambda g, pick=pick: pick(g) if g else ""):
                raise ConfigError(
                    f"the {role} role holds more than the grant map: " + "; ".join(bad[:20])
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
