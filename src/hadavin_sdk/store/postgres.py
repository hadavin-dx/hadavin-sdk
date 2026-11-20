"""Postgres store (`pip install hadavin-sdk[pg]`). Same Protocol as `memory`; compare-and-set is in SQL, so it
holds across processes. The schema comes from `hadavin-sdk migrate` (`store/migrate.py`), never from here.

Connect pattern ported from WARDEN `audit.py:_pg_connect` (main a1e76cbf): with `iam_auth` and no password in
the DSN, the login is a 15-minute RDS IAM token and TLS is required.

Neutral protocol: the PostgreSQL wire protocol and SQL (any Postgres: RDS, Cloud SQL, Azure, self-hosted).
"""

from __future__ import annotations

import ipaddress
import logging
import os
import re
import tempfile
import threading
import uuid
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal, localcontext
from enum import Enum
from typing import Any

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    OPEN_STATES,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    AuditEvent,
    DeadLetter,
    GateDecision,
    KillSwitch,
    OpenStop,
    Plan,
    Run,
    RunState,
    SpendReservation,
    TickState,
    ToolCallRecord,
    now,
)
from hadavin_sdk.store.protocol import (
    NotFound,
    SpendCapExceeded,
    SpendRelease,
    StaleState,
    StoreUnavailable,
    check_expiry_age,
    check_purge_bound,
    check_reservation_id,
    check_spend_amount,
    check_spend_cap,
    check_spend_day,
    check_store_id,
    clean_spend_amount,
)

_LOG = logging.getLogger("hadavin_sdk.store")


_VERIFIED_TLS = frozenset({"verify-ca", "verify-full"})


def _is_local(parts: dict) -> bool:
    """Unix socket or loopback only. A host from PGHOST/hostaddr counts; anything unknown is remote."""
    hosts = str(parts.get("host") or parts.get("hostaddr") or os.environ.get("PGHOST") or "")
    if not hosts or hosts.startswith("/"):
        return True
    for h in hosts.split(","):
        if h == "localhost":
            continue
        try:
            if not ipaddress.ip_address(h).is_loopback:
                return False
        except ValueError:
            return False
    return True


def tls_mode(
    dsn: str, *, iam_auth: bool = False, sslmode: str | None = None, sslrootcert: str | None = None
) -> str | None:
    """The sslmode to connect with. Loopback and unix sockets keep the setting or the DSN's. Any other host
    defaults to `verify-full` (the server's certificate and name are checked, so credentials cannot be
    captured by an impostor); an explicit weaker `sslmode` is an opt-down for demo. With iam_auth (a bearer
    token) only `verify-full` or `verify-ca` is accepted. A verified mode needs the CA bundle."""
    parts = conninfo_to_dict(dsn)
    mode = sslmode or parts.get("sslmode")
    if not iam_auth and _is_local(parts):
        return mode
    mode = mode or "verify-full"
    if iam_auth and mode not in _VERIFIED_TLS:
        raise ConfigError(
            "store postgres: iam_auth needs a verified server "
            f"(sslmode verify-full or verify-ca), not {mode}"
        )
    if mode in _VERIFIED_TLS and not (sslrootcert or parts.get("sslrootcert")):
        raise ConfigError(
            f"store postgres: sslmode {mode} needs the server's CA bundle: set sslrootcert (a file) or "
            "sslrootcert_secret_name (a PEM in the secrets backend), or opt down with sslmode for demo"
        )
    return mode


def ca_file(settings, resolve) -> str | None:
    """The CA bundle path: the setting, or the PEM from the secrets backend written to a private temp file
    (a CA bundle is public; the file is 0600 only because mkstemp makes it so)."""
    if not settings.sslrootcert_secret_name:
        return settings.sslrootcert
    fd, path = tempfile.mkstemp(prefix="hadavin-ca-", suffix=".pem")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(resolve(settings.sslrootcert_secret_name))
    return path


PasswordSource = Callable[[str, int, str], str]  # (host, port, user) -> a short-lived password


def password_source(iam_auth: bool, region: str | None) -> PasswordSource | None:
    """The sign-in helper: None (the DSN's own password), or RDS IAM from `store/auth_aws.py`, the only
    module of the store that imports an AWS SDK (lock-in audit 2026-10-31 #5)."""
    if not iam_auth:
        return None
    try:
        from hadavin_sdk.store import auth_aws
    except ModuleNotFoundError as exc:
        if (exc.name or "").startswith("hadavin_sdk"):
            raise
        raise ConfigError(
            "store postgres with iam_auth needs: pip install hadavin-sdk[aws]"
        ) from exc
    return auth_aws.rds_iam(region)


_SESSION_PINS = (("default_transaction_read_only", "off"), ("synchronous_commit", "on"))


def connect(
    dsn: str,
    *,
    iam_auth: bool = False,
    region: str | None = None,
    sslmode: str | None = None,
    sslrootcert: str | None = None,
) -> psycopg.Connection:
    extra: dict[str, Any] = {}
    if mode := tls_mode(dsn, iam_auth=iam_auth, sslmode=sslmode, sslrootcert=sslrootcert):
        extra["sslmode"] = mode
    if sslrootcert:
        extra["sslrootcert"] = sslrootcert
    if iam_auth:
        parts = conninfo_to_dict(dsn)
        # The migration role may log in with a password; the runtime never (refused in build()).
        if not parts.get("password"):
            password = password_source(True, region)
            extra["password"] = password(
                parts["host"], int(parts.get("port") or 5432), parts["user"]
            )
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10, **extra)
    # Plan hashes include created_at: datetimes must come back in UTC whatever the server's TimeZone is.
    conn.execute("SET TIME ZONE 'UTC'")
    # Every writer relies on READ COMMITTED (a conditional UPDATE re-checks its WHERE after a row-lock wait); a
    # server or role default of REPEATABLE READ would turn that wait into an error, so the session pins it.
    conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED")
    # A role or database default must not weaken the session after login: a read-only default would make a stop fail,
    # `synchronous_commit = off` could lose an acknowledged stop on a crash. SET at session level wins over those
    # defaults; each pin is read back with SHOW and a server that did not take it refuses the connection.
    for setting, value in _SESSION_PINS:
        conn.execute(f"SET {setting} = {value}")
        got = conn.execute(f"SHOW {setting}").fetchone()[0]
        if got != value:
            conn.close()
            raise ConfigError(f"the database session did not take {setting} = {value}")
    return conn


_PIN = re.compile(r"search_path\s*=\s*(.*?)(?=\s+-c\s|\s+--|$)")
_STOP_TABLES = ("kill_switch", "kill_switch_stops", "kill_switch_clears")


def names_of(text: str) -> list[str]:
    """The schema names of a search_path value as the server reads them: a quoted name keeps its case and `""` is one
    quote, an unquoted name is folded to lower case; without the implicit pg_catalog and pg_temp."""
    out: list[str] = []
    for m in re.finditer(r'\s*(?:"((?:[^"]|"")*)"|([^,"]*?))\s*(?:,|$)', text):
        quoted, bare = m.group(1), m.group(2)
        name = quoted.replace('""', '"') if quoted is not None else (bare or "").strip().lower()
        if name and name != "pg_catalog" and not name.startswith("pg_temp"):
            out.append(name)
    return out


def _names(text: str) -> list[str]:
    return names_of(text)


def expected_schemas(dsn: str, schema: str | None) -> list[str]:
    """The schemas this store is configured for: `settings.db_schema`, else what the DSN pins, else `public`. A
    setting that disagrees with the DSN's pin is a configuration error."""
    pinned: list[str] = []
    options = re.sub(
        r"\\(.)", r"\1", conninfo_to_dict(dsn).get("options") or ""
    )  # libpq: \\<char> is <char>
    if m := _PIN.search(options):
        pinned = _names(m.group(1))
    if schema and pinned and pinned != [schema]:
        raise ConfigError(
            f"store postgres: backends.store.db_schema is {schema!r} but the DSN pins search_path to "
            f"{', '.join(pinned)}; make them the same"
        )
    return [schema] if schema else pinned or ["public"]


def verify_schema(conn: psycopg.Connection, expected: list[str]) -> str:
    """Refuse to start unless the connection's effective search_path is exactly `expected` and the stop tables are
    in `current_schema()`. A role may change its OWN default path (`ALTER ROLE r SET search_path`); without this
    a changed default would make the process read a decoy stop table. Returns current_schema()."""
    schema, effective = conn.execute(
        "SELECT pg_catalog.current_schema(), pg_catalog.current_schemas(false)"
    ).fetchone()
    if not schema:
        raise ConfigError(
            "store postgres: the search_path names no schema that exists (effective search_path of this login: "
            f"empty; the store is configured for {', '.join(expected)})"
        )
    effective = [n for n in effective if n != "pg_catalog" and not n.startswith("pg_temp")]
    if effective != expected or schema != expected[0]:
        raise ConfigError(
            f"store postgres: the effective search_path of this login is {', '.join(effective) or 'empty'} "
            f"(current_schema() is {schema!r}) but the store is configured for {', '.join(expected)}. "
            "backends.store.db_schema is the EXPECTED schema (the check), it does not choose the schema of the "
            "login. Make the login really use it: pin it in the DSN (options=-c search_path=<schema>), or make "
            "the role default equal to it (ALTER ROLE <login> SET search_path = <schema>; "
            "hadavin-sdk migrate does this for this database when it names the role), then set db_schema to "
            "the same schema"
        )
    found = {
        r[0]
        for r in conn.execute(
            "SELECT c.relname FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relkind IN ('r','p') AND c.relname = ANY(%s)",
            (schema, list(_STOP_TABLES)),
        ).fetchall()
    }
    if missing := [t for t in _STOP_TABLES if t not in found]:
        raise ConfigError(
            f"store postgres: kill_switch not found in current_schema() = {schema!r} (missing relations: "
            f"{', '.join(missing)}): the stop state is not in the schema this store reads. Run hadavin-sdk migrate for that schema, or fix the "
            "search_path of the login"
        )
    return schema


_ALL_TABLE_RIGHTS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
_COLUMN_RIGHTS = ("SELECT", "INSERT", "UPDATE", "REFERENCES")  # what a column grant can give


def own_stop_rights_problems(conn: psycopg.Connection, schema: str) -> list[str]:
    """What the CURRENT login can do on the three stop tables beyond what `GRANTS` gives the runtime role, however
    it got it (a direct grant, a column grant, a role it is a member of, PUBLIC). Strings like `UPDATE on
    kill_switch`: the right and the table, never a value. [] for a superuser or a member of the tables' owner:
    that login owns the tables and is outside the guarantee (migrate warns when no roles are named)."""
    from hadavin_sdk.store.migrate import GRANTS  # late: migrate imports this module

    me = conn.execute(
        "SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname = current_user"
    ).fetchone()
    if me is None or me[0]:
        return []
    rows = conn.execute(
        "SELECT c.oid, c.relname, pg_catalog.pg_has_role(current_user, c.relowner, 'MEMBER') "
        "FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND c.relkind IN ('r','p') AND c.relname = ANY(%s)",
        (schema, list(_STOP_TABLES)),
    ).fetchall()
    if any(owns for _, _, owns in rows):
        return []
    rights = list(_ALL_TABLE_RIGHTS)
    if conn.info.server_version >= 170000:
        rights.append("MAINTAIN")
    problems = []
    for oid, name, _ in sorted(rows, key=lambda r: r[1]):
        allowed = {x.strip() for x in GRANTS[name].runtime.split(",") if x.strip()}
        for right in rights:
            if right in allowed:
                continue
            held = conn.execute(
                "SELECT pg_catalog.has_table_privilege(%s, %s)", (oid, right)
            ).fetchone()[0]
            if not held and right in _COLUMN_RIGHTS:
                held = conn.execute(
                    "SELECT pg_catalog.has_any_column_privilege(%s, %s)", (oid, right)
                ).fetchone()[0]
            if held:
                problems.append(f"{right} on {name}")
    return problems


def build(settings, deps) -> PostgresStore:
    """Table factory: the DSN is a platform secret named in the settings (never the executor's)."""
    password_source(
        settings.iam_auth, settings.region
    )  # a missing `aws` extra fails here, with the hint
    dsn = deps.resolve(settings.dsn_secret_name)
    if settings.iam_auth and conninfo_to_dict(dsn).get("password"):
        raise ConfigError(
            "store postgres: with iam_auth the DSN must not carry a password (the login is an IAM token)"
        )
    try:
        conn = connect(
            dsn,
            iam_auth=settings.iam_auth,
            region=settings.region,
            sslmode=settings.sslmode,
            sslrootcert=ca_file(settings, deps.resolve),
        )
    except psycopg.OperationalError as exc:
        # The class only: driver messages can carry the host and user.
        raise StoreUnavailable(
            f"store postgres: cannot connect ({exc.__class__.__name__})"
        ) from None
    try:
        schema = verify_schema(conn, expected_schemas(dsn, settings.db_schema))
        if getattr(settings, "_login_role", "runtime") == "runtime" and (
            problems := own_stop_rights_problems(conn, schema)
        ):
            raise ConfigError(
                "store postgres: this login holds rights on the stop tables that only the reset role may hold ("
                + "; ".join(problems)
                + "). A login that can write there can clear a stop. Revoke them from the login and from the "
                "roles it is a member of, or run hadavin-sdk migrate with --runtime-role naming this login "
                "(it resets the grants and refuses what stays)"
            )
    except BaseException:
        conn.close()
        raise
    # A store call that waits on a row lock for longer than this fails loudly instead of holding the process-wide
    # store lock. Set here, not in `connect()`: the migrate path shares `connect()` and its statements may run long.
    conn.execute(
        sql.SQL("SET lock_timeout = {}").format(sql.Literal(defaults.STORE_LOCK_TIMEOUT_MS))
    )
    return PostgresStore(conn)


def _row(model: BaseModel) -> dict[str, Any]:
    """Model -> column values: dicts/lists as JSONB, enums as their text, everything else as is."""
    py, js = model.model_dump(), model.model_dump(mode="json")
    out = {}
    for k, v in py.items():
        if isinstance(v, dict | list):
            out[k] = Jsonb(js[k])
        elif isinstance(v, Enum):
            out[k] = js[k]
        else:
            out[k] = v
    return out


_SCHEMA_TABLES = ("spend", "spend_month", "spend_reservations")


class PostgresStore:
    # ponytail: one connection behind one lock per process; a pool (psycopg_pool) when throughput matters.
    # A dropped connection fails the call (the run ends safely); reconnect-on-error arrives with S11 hosting.
    def __init__(self, conn: psycopg.Connection) -> None:
        self._db = conn
        self._lock = threading.Lock()
        # Resolved once: the stop-state statements name this schema (`current_schema()` never answers pg_temp).
        self._schema = conn.execute("SELECT current_schema()").fetchone()[0]
        if not self._schema:
            raise ConfigError("store postgres: the search_path names no schema that exists")

    # --- generic helpers ---------------------------------------------------------------------------------

    def _exec(self, query, params=()) -> psycopg.Cursor:
        return self._db.cursor(row_factory=dict_row).execute(query, params)

    def _insert(self, table: str, model: BaseModel, upsert_on: str | None = None) -> None:
        row = _row(model)
        cols = [sql.Identifier(c) for c in row]
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(cols),
            sql.SQL(", ").join(sql.Placeholder() * len(row)),
        )
        if upsert_on:
            query += sql.SQL(" ON CONFLICT ({}) DO UPDATE SET {}").format(
                sql.Identifier(upsert_on),
                sql.SQL(", ").join(sql.SQL("{0} = EXCLUDED.{0}").format(c) for c in cols),
            )
        with self._lock:
            self._exec(query, list(row.values()))

    def _select(self, model: type[BaseModel], table: str, where: str, params, tail: str = ""):
        """`where` and `tail` are fixed SQL text from this module; values always go through `params`."""
        cols = sql.SQL(", ").join(sql.Identifier(c) for c in model.model_fields)
        query = sql.SQL("SELECT {} FROM {} WHERE {}{}").format(
            cols, sql.Identifier(table), sql.SQL(where), sql.SQL(tail)
        )
        with self._lock:
            rows = self._exec(query, params).fetchall()
        return [model.model_validate(r) for r in rows]

    def _one(self, model: type[BaseModel], table: str, key: str, value: str):
        found = self._select(model, table, f"{key} = %s", (value,))
        if not found:
            raise NotFound(value)
        return found[0]

    # --- runs --------------------------------------------------------------------------------------------

    def create_run(self, run: Run) -> None:
        try:
            self._insert("runs", run)
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"run exists: {run.run_id}") from None

    def get_run(self, run_id: str) -> Run:
        return self._one(Run, "runs", "run_id", run_id)

    def _missing_or_stale(self, table: str, key: str, value: str, stale: str) -> Exception:
        with self._lock:
            exists = self._exec(
                sql.SQL("SELECT 1 FROM {} WHERE {} = %s").format(
                    sql.Identifier(table), sql.Identifier(key)
                ),
                (value,),
            ).fetchone()
        return StaleState(stale) if exists else NotFound(value)

    def transition(
        self, run_id: str, expected: RunState, new: RunState, reason_code: str | None = None
    ) -> Run:
        with self._lock:
            row = self._exec(
                "UPDATE runs SET state = %s, reason_code = %s, updated_at = %s "
                "WHERE run_id = %s AND state = %s RETURNING run_id",
                (new.value, reason_code, now(), run_id, expected.value),
            ).fetchone()
        if row is None:
            raise self._missing_or_stale("runs", "run_id", run_id, f"{run_id}: expected {expected}")
        return self.get_run(run_id)

    def _update_run(self, query: str, value: Any, run_id: str) -> None:
        with self._lock:
            cur = self._exec(query, (value, run_id))
        if cur.rowcount == 0:
            raise NotFound(run_id)

    def add_cost(self, run_id: str, usd: Decimal) -> None:
        usd = clean_spend_amount(usd)
        self._update_run("UPDATE runs SET cost_usd = cost_usd + %s WHERE run_id = %s", usd, run_id)

    def touch(self, run_id: str) -> None:
        self._update_run("UPDATE runs SET updated_at = %s WHERE run_id = %s", now(), run_id)

    def list_runs(self, state: RunState, updated_before: datetime, limit: int = 100) -> list[Run]:
        return self._select(
            Run,
            "runs",
            "state = %s AND updated_at < %s",
            (state.value, updated_before, limit),
            " ORDER BY updated_at LIMIT %s",
        )

    # --- plans and gate decisions --------------------------------------------------------------------------

    def save_plan(self, plan: Plan) -> None:
        self._insert("plans", plan, upsert_on="run_id")

    def get_plan(self, run_id: str) -> Plan:
        return self._one(Plan, "plans", "run_id", run_id)

    def save_gate_decision(self, decision: GateDecision) -> None:
        try:
            self._insert("gate_decisions", decision)  # append-only: the runtime role has no UPDATE
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"gate decision exists: {decision.run_id}") from None

    def get_gate_decision(self, run_id: str) -> GateDecision:
        return self._one(GateDecision, "gate_decisions", "run_id", run_id)

    # --- approvals -----------------------------------------------------------------------------------------

    def save_approval_request(self, req: ApprovalRequest) -> None:
        self._insert("approval_requests", req, upsert_on="approval_id")

    def get_approval_request(self, approval_id: str) -> ApprovalRequest:
        return self._one(ApprovalRequest, "approval_requests", "approval_id", approval_id)

    def update_approval_request(
        self, req: ApprovalRequest, expected_status: str, expected_step: int
    ) -> None:
        row = _row(req)
        sets = sql.SQL(", ").join(
            sql.SQL("{} = %s").format(sql.Identifier(c)) for c in row if c != "approval_id"
        )
        query = sql.SQL(
            "UPDATE approval_requests SET {} WHERE approval_id = %s AND status = %s AND current_step = %s"
        ).format(sets)
        values = [v for c, v in row.items() if c != "approval_id"]
        with self._lock:
            cur = self._exec(query, [*values, req.approval_id, expected_status, expected_step])
        if cur.rowcount == 0:
            raise self._missing_or_stale(
                "approval_requests",
                "approval_id",
                req.approval_id,
                f"{req.approval_id}: not {expected_status}/{expected_step}",
            )

    def record_decision(
        self,
        decision: ApprovalDecision,
        req: ApprovalRequest,
        expected_status: str,
        expected_step: int,
    ) -> None:
        drow, rrow = _row(decision), _row(req)
        insert = sql.SQL("INSERT INTO approval_decisions ({}) VALUES ({})").format(
            sql.SQL(", ").join(sql.Identifier(c) for c in drow),
            sql.SQL(", ").join(sql.Placeholder() * len(drow)),
        )
        update = sql.SQL(
            "UPDATE approval_requests SET {} WHERE approval_id = %s AND status = %s AND current_step = %s"
        ).format(
            sql.SQL(", ").join(
                sql.SQL("{} = %s").format(sql.Identifier(c)) for c in rrow if c != "approval_id"
            )
        )
        values = [v for c, v in rrow.items() if c != "approval_id"]
        lost = False
        try:
            with self._lock, self._db.transaction():
                self._exec(insert, list(drow.values()))
                cur = self._exec(update, [*values, req.approval_id, expected_status, expected_step])
                if cur.rowcount == 0:
                    lost = True
                    raise psycopg.Rollback()  # the insert above is undone with it
        except psycopg.errors.UniqueViolation:
            lost = True
        if lost:
            raise self._missing_or_stale(
                "approval_requests",
                "approval_id",
                req.approval_id,
                f"{req.approval_id}: not {expected_status}/{expected_step}",
            )

    def list_due_approvals(self, now: datetime) -> list[ApprovalRequest]:
        return self._select(
            ApprovalRequest,
            "approval_requests",
            "status = 'PENDING' AND step_expires_at <= %s",
            (now,),
        )

    def save_approval_decision(self, decision: ApprovalDecision) -> None:
        try:
            self._insert("approval_decisions", decision)
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"decision exists: {decision.approval_id}/{decision.step}") from None

    def get_approval_decision(self, approval_id: str) -> ApprovalDecision | None:
        found = self._select(
            ApprovalDecision,
            "approval_decisions",
            "approval_id = %s",
            (approval_id,),
            " ORDER BY seq DESC LIMIT 1",
        )
        return found[0] if found else None

    def list_approvals(self, statuses: set[ApprovalStatus]) -> list[ApprovalRequest]:
        return self._select(
            ApprovalRequest,
            "approval_requests",
            "status = ANY(%s)",
            (sorted(statuses),),
            " ORDER BY created_at",
        )

    # --- dead letters, spend, kill switch ------------------------------------------------------------------

    def add_dead_letter(self, dl: DeadLetter) -> None:
        self._insert("dead_letters", dl)

    def list_dead_letters(self, run_id: str) -> list[DeadLetter]:
        return self._select(DeadLetter, "dead_letters", "run_id = %s", (run_id,), " ORDER BY seq")

    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
        """Day and month counters, each one atomic upsert, in one transaction: exact under concurrency."""
        usd = clean_spend_amount(usd)  # a bad amount is a ValueError before any SQL; -0 becomes 0
        month = day.replace(day=1)
        with self._lock, self._db.transaction():
            d = self._exec(
                self._t(
                    "INSERT INTO {spend} (agent_id, day, usd) VALUES (%s, %s, %s) "
                    "ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd"
                ),
                (agent_id, day, usd),
            ).fetchone()["usd"]
            m = self._exec(
                self._t(
                    "INSERT INTO {spend_month} (agent_id, month, usd) VALUES (%s, %s, %s) "
                    "ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd "
                    "RETURNING usd"
                ),
                (agent_id, month, usd),
            ).fetchone()["usd"]
        return Decimal(d), Decimal(m)

    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
        with self._lock:
            d = self._exec(
                self._t("SELECT usd FROM {spend} WHERE agent_id = %s AND day = %s"), (agent_id, day)
            ).fetchone()
            m = self._exec(
                self._t("SELECT usd FROM {spend_month} WHERE agent_id = %s AND month = %s"),
                (agent_id, day.replace(day=1)),
            ).fetchone()
        return (Decimal(d["usd"]) if d else Decimal(0)), (Decimal(m["usd"]) if m else Decimal(0))

    def _t(self, text: str) -> sql.Composed:
        """A statement whose spend, spend_month and spend_reservations names carry the schema. An unqualified name
        is looked up in the session's temporary schema first, so a temporary table of that name would shadow it."""
        s = sql.Identifier(self._schema)
        return sql.SQL(text).format(
            **{t: sql.SQL("{}.{}").format(s, sql.Identifier(t)) for t in _SCHEMA_TABLES}
        )

    def _stop_tables(self) -> dict[str, sql.Composed]:
        """The three stop-state relations with the schema named. An unqualified name is looked up in the session's
        temporary schema first, so a temporary table called `kill_switch` would shadow the real one."""
        s = sql.Identifier(self._schema)
        return {
            "flag": sql.SQL("{}.kill_switch").format(s),
            "stops": sql.SQL("{}.kill_switch_stops").format(s),
            "clears": sql.SQL("{}.kill_switch_clears").format(s),
            "resets": sql.SQL("{}.kill_switch_resets").format(s),
            "mark": sql.SQL("{}.kill_switch_watermark").format(s),
        }

    def get_kill_switch(self) -> KillSwitch:
        t = self._stop_tables()
        cols = sql.SQL(", ").join(sql.Identifier(c) for c in KillSwitch.model_fields)
        with self._lock:
            rows = self._exec(
                sql.SQL("SELECT {} FROM {flag} WHERE id = 1").format(cols, **t)
            ).fetchall()
        found = [KillSwitch.model_validate(r) for r in rows]
        if not found:  # migrate seeds the row: its absence means a broken schema, so fail closed
            _LOG.error(
                "kill_switch row missing: treating the kill switch as ON; run hadavin-sdk migrate"
            )
            return KillSwitch(on=True, by="system:kill_switch_row_missing")
        if found[0].on:
            return found[0]
        with (
            self._lock
        ):  # the flag is off: any stop with no clear still means ON (the oldest one is reported)
            # Every clear names one distinct stop (primary key plus foreign key), so "some stop has no clear" is
            # exactly count(stops) > count(clears): two index-only counts, however many cleared stops there are.
            # A time watermark cannot make this cheaper without risk: a stop hidden because its ts is at or below
            # the watermark (a planted old ts, a hand-inserted stop after a reset) must still count as open. The
            # slow oldest-first anti-join runs only when a stop really is open (the switch is ON anyway).
            row = self._exec(
                sql.SQL(
                    "SELECT (SELECT count(*) FROM {stops}) > (SELECT count(*) FROM {clears}) AS any_open"
                ).format(**t)
            ).fetchone()
            stop = None
            if row["any_open"]:
                stop = self._exec(
                    sql.SQL(
                        'SELECT s."by", s.ts FROM {stops} s WHERE NOT EXISTS '
                        "(SELECT 1 FROM {clears} c WHERE c.stop_id = s.id) ORDER BY s.ts, s.id LIMIT 1"
                    ).format(**t)
                ).fetchone()
        if stop is not None:
            return KillSwitch(on=True, by=stop["by"], ts=stop["ts"])
        return found[0]

    def set_kill_switch(self, ks: KillSwitch) -> None:
        t = self._stop_tables()
        if ks.on:  # a stop is one INSERT: all the runtime role may do to the stop state
            with self._lock:  # no ts: the database clock sets it (the column default)
                self._exec(sql.SQL('INSERT INTO {stops} ("by") VALUES (%s)').format(**t), (ks.by,))
            return
        # A reset (the reset role only): the old flag off and one clear per stop the clear statement can see, in
        # one transaction. A stop committed after that statement began has no clear, so the switch stays ON; a
        # stop committed before it began (also one committed after the caller's audit intent) is cleared.
        with self._lock, self._db.transaction():
            flag = self._exec(
                sql.SQL('UPDATE {flag} SET "on" = FALSE, "by" = %s, ts = %s WHERE id = 1').format(
                    **t
                ),
                (ks.by, ks.ts),
            )
            if (
                flag.rowcount != 1
            ):  # a broken schema reads ON whatever is cleared: say so, clear nothing
                raise ConfigError(
                    "kill_switch row missing: the kill switch stays ON and nothing was cleared; "
                    "run hadavin-sdk migrate"
                )
            self._exec(
                sql.SQL(
                    'INSERT INTO {clears} (stop_id, "by", ts) SELECT s.id, %s, %s '
                    "FROM {stops} s WHERE NOT EXISTS "
                    "(SELECT 1 FROM {clears} c WHERE c.stop_id = s.id) "
                    "ON CONFLICT (stop_id) DO NOTHING"
                ).format(**t),
                (ks.by, ks.ts),
            )

    def open_stops(self) -> list[OpenStop]:
        t = self._stop_tables()
        with self._lock:
            rows = self._exec(
                sql.SQL(
                    'SELECT s.id::text AS id, s."by", s.ts FROM {stops} s WHERE NOT EXISTS '
                    "(SELECT 1 FROM {clears} c WHERE c.stop_id = s.id) ORDER BY s.ts, s.id"
                ).format(**t)
            ).fetchall()
        return [OpenStop.model_validate(r) for r in rows]

    def clear_stops(self, by: str, stop_ids: Sequence[str], audit_seq: int | None = None) -> None:
        """Compare-and-clear (the reset role only): the old flag off and one clear row for each of exactly these
        stop ids, one `kill_switch_resets` row (who, the ids it really cleared, the audit chain seq when the caller
        knows it) and the watermark moved to the newest cleared stop time, all in one transaction. A stop that is not in `stop_ids` (set after the caller read the open stops)
        gets no clear and keeps the switch ON."""
        t = self._stop_tables()
        ids = [
            str(uuid.UUID(str(i))) for i in stop_ids
        ]  # a malformed id is an error here, not in the database
        stamp = now()
        with self._lock, self._db.transaction():
            flag = self._exec(
                sql.SQL('UPDATE {flag} SET "on" = FALSE, "by" = %s, ts = %s WHERE id = 1').format(
                    **t
                ),
                (by, stamp),
            )
            if (
                flag.rowcount != 1
            ):  # a broken schema reads ON whatever is cleared: say so, clear nothing
                raise ConfigError(
                    "kill_switch row missing: the kill switch stays ON and nothing was cleared; "
                    "run hadavin-sdk migrate"
                )
            cleared: list[str] = []
            newest = None
            if ids:
                done = self._exec(
                    sql.SQL(
                        'WITH c AS (INSERT INTO {clears} (stop_id, "by", ts) SELECT s.id, %s, %s '
                        "FROM {stops} s WHERE s.id = ANY(%s::uuid[]) AND NOT EXISTS "
                        "(SELECT 1 FROM {clears} x WHERE x.stop_id = s.id) "
                        "ON CONFLICT (stop_id) DO NOTHING RETURNING stop_id) "
                        "SELECT array_agg(c.stop_id::text) AS ids, max(s.ts) AS newest "
                        "FROM c JOIN {stops} s ON s.id = c.stop_id"
                    ).format(**t),
                    (by, stamp, ids),
                ).fetchone()
                cleared = list(done["ids"] or [])
                newest = done["newest"]
            # The reset's own record (the reset role holds INSERT only, so no RETURNING) and the watermark.
            self._exec(
                sql.SQL(
                    'INSERT INTO {resets} ("by", at, cleared_ids, audit_seq) VALUES (%s, %s, %s::uuid[], %s)'
                ).format(**t),
                (by, stamp, cleared, audit_seq),
            )
            if newest is not None:  # never lowers: the trigger refuses it, GREATEST keeps it quiet
                self._exec(
                    sql.SQL(
                        "INSERT INTO {mark} AS w (id, through, at) VALUES (TRUE, %s, %s) "
                        "ON CONFLICT (id) DO UPDATE SET through = GREATEST(w.through, EXCLUDED.through), "
                        "at = EXCLUDED.at"
                    ).format(**t),
                    (newest, stamp),
                )

    def get_tick_state(self, step: str) -> TickState | None:
        found = self._select(TickState, "tick_state", "step = %s", (step,))
        return found[0] if found else None

    def save_tick_state(self, state: TickState) -> None:
        self._insert("tick_state", state, upsert_on="step")

    # --- evidence (K5) ------------------------------------------------------------------------------------------

    def add_tool_call(self, call: ToolCallRecord) -> None:
        try:
            self._insert("tool_calls", call)
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"tool call exists: {call.call_id}") from None

    def list_tool_calls(self, run_id: str) -> list[ToolCallRecord]:
        return self._select(
            ToolCallRecord, "tool_calls", "run_id = %s", (run_id,), " ORDER BY created_at, call_id"
        )

    def _purge(self, table: str, column: str, before: datetime, keep: frozenset[str]) -> int:
        query = sql.SQL("DELETE FROM {} WHERE {} < %s AND NOT (run_id = ANY(%s))").format(
            sql.Identifier(table), sql.Identifier(column)
        )
        with self._lock:
            return self._exec(query, (before, sorted(keep))).rowcount

    def purge_tool_calls(self, before: datetime, *, keep_run_ids: frozenset[str]) -> int:
        return self._purge("tool_calls", "created_at", before, keep_run_ids)

    def put_redaction_map(self, run_id: str, mapping: dict[str, str]) -> None:
        with self._lock:
            self._exec(
                "INSERT INTO redaction_maps (run_id, mapping, updated_at) VALUES (%s, %s, %s) "
                "ON CONFLICT (run_id) DO UPDATE SET mapping = EXCLUDED.mapping, "
                "updated_at = EXCLUDED.updated_at",
                (run_id, Jsonb(mapping), now()),
            )

    def get_redaction_map(self, run_id: str) -> dict[str, str] | None:
        with self._lock:
            row = self._exec(
                "SELECT mapping FROM redaction_maps WHERE run_id = %s", (run_id,)
            ).fetchone()
        return dict(row["mapping"]) if row else None

    def purge_redaction_maps(
        self, before: datetime, *, keep_run_ids: frozenset[str], keep_open: bool = True
    ) -> int:
        """Aged from the run's last state change (the map's own time when the run is unknown); the maps of runs
        that can still move (OPEN_STATES) are kept unless `keep_open` is false. A run parked in NEEDS_PERSON cannot
        move, so its map ages like a finished run's."""
        with self._lock:
            if keep_open:
                open_states = sorted(s.value for s in OPEN_STATES)
                return self._exec(
                    "DELETE FROM redaction_maps m WHERE NOT (m.run_id = ANY(%s)) AND "
                    "COALESCE((SELECT r.updated_at FROM runs r WHERE r.run_id = m.run_id), "
                    "m.updated_at) < %s AND NOT EXISTS (SELECT 1 FROM runs r "
                    "WHERE r.run_id = m.run_id AND r.state = ANY(%s))",
                    (sorted(keep_run_ids), before, open_states),
                ).rowcount
            return self._exec(
                "DELETE FROM redaction_maps m WHERE NOT (m.run_id = ANY(%s)) AND "
                "COALESCE((SELECT r.updated_at FROM runs r WHERE r.run_id = m.run_id), "
                "m.updated_at) < %s",
                (sorted(keep_run_ids), before),
            ).rowcount

    # --- spend reservations (0007) --------------------------------------------------------------------------
    # The cap check and the booking are one conditional UPDATE per counter, in the transaction that adds the
    # reservation row. The UPDATE relies on READ COMMITTED (its re-check after a row-lock wait), which
    # `connect()` sets for the whole session.

    def reserve_spend(
        self,
        reservation_id: str,
        agent_id: str,
        day: date,
        usd: Decimal,
        *,
        day_cap: Decimal,
        month_cap: Decimal,
        run_id: str | None = None,
    ) -> None:
        check_store_id(agent_id, "agent_id")
        if run_id is not None:
            check_store_id(run_id, "run_id")
        check_spend_day(day)
        check_reservation_id(reservation_id)
        check_spend_amount(usd)
        check_spend_cap(day_cap)  # before any SQL: a NaN cap would compare as no cap
        check_spend_cap(month_cap)
        month = day.replace(day=1)
        try:
            with self._lock, self._db.transaction():
                self._exec(
                    self._t(
                        "INSERT INTO {spend_reservations} "
                        "(reservation_id, agent_id, day, run_id, reserved_usd) VALUES (%s, %s, %s, %s, %s)"
                    ),
                    (reservation_id, agent_id, day, run_id, usd),
                )
                self._exec(
                    self._t(
                        "INSERT INTO {spend} (agent_id, day, usd) VALUES (%s, %s, 0) ON CONFLICT DO NOTHING"
                    ),
                    (agent_id, day),
                )
                # strictly day before month (the order of add_spend): seed and book the day, then the month;
                # zero rows = refused, everything rolls back
                booked = self._exec(
                    self._t(
                        "UPDATE {spend} SET usd = usd + %(amt)s WHERE agent_id = %(agent)s "
                        "AND day = %(day)s AND usd < %(cap)s AND usd + %(amt)s <= %(cap)s RETURNING usd"
                    ),
                    {"amt": usd, "agent": agent_id, "day": day, "cap": day_cap},
                ).fetchone()
                if booked is None:
                    raise SpendCapExceeded("day")
                self._exec(
                    self._t(
                        "INSERT INTO {spend_month} (agent_id, month, usd) VALUES (%s, %s, 0) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    (agent_id, month),
                )
                booked = self._exec(
                    self._t(
                        "UPDATE {spend_month} SET usd = usd + %(amt)s WHERE agent_id = %(agent)s "
                        "AND month = %(month)s AND usd < %(cap)s AND usd + %(amt)s <= %(cap)s RETURNING usd"
                    ),
                    {"amt": usd, "agent": agent_id, "month": month, "cap": month_cap},
                ).fetchone()
                if booked is None:
                    raise SpendCapExceeded("month")
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"spend reservation exists: {reservation_id}") from None

    # One statement: the inner SELECT locks the row and reads its status BEFORE the change (after a row-lock
    # wait it reads the committed status, so a concurrent expire or settle cannot be misread). settled_usd is
    # what stays booked on the counters: the actual amount, or for a row that was expired the larger of the
    # actual and the reserved amount (after expiry the booking never goes down).
    _CLAIM = (
        "WITH old AS (SELECT status FROM {spend_reservations} WHERE reservation_id = %(id)s "
        "AND (%(agent)s::text IS NULL OR agent_id = %(agent)s) AND status IN ('open', 'expired') FOR UPDATE) "
        "UPDATE {spend_reservations} r SET status = 'settled', settled_usd = CASE WHEN old.status = 'expired' "
        "THEN GREATEST(%(a)s::numeric, r.reserved_usd) ELSE %(a)s::numeric END, "
        "closed_at = clock_timestamp() FROM old WHERE r.reservation_id = %(id)s "
        "RETURNING r.*, old.status AS was"
    )

    def settle_spend(
        self, reservation_id: str, actual_usd: Decimal, *, agent_id: str | None = None
    ) -> tuple[SpendReservation, bool]:
        check_reservation_id(reservation_id)
        check_spend_amount(actual_usd)
        if agent_id is not None:
            check_store_id(agent_id, "agent_id")
        with self._lock, self._db.transaction():
            # The claim comes first. A second caller waits on the row lock, finds the row settled, claims
            # nothing and gets the stored row back unchanged.
            row = self._exec(
                self._t(self._CLAIM), {"id": reservation_id, "a": actual_usd, "agent": agent_id}
            ).fetchone()
            if row is None:
                row = self._exec(
                    self._t("SELECT * FROM {spend_reservations} WHERE reservation_id = %s"),
                    (reservation_id,),
                ).fetchone()
                if row is None or (agent_id is not None and row["agent_id"] != agent_id):
                    raise NotFound(reservation_id)  # also another agent's id: nothing is revealed
                return SpendReservation.model_validate(row), False
            was = row.pop("was")
            # what the counters must move by: the booked amount changes from reserved to settled_usd
            with localcontext(defaults.money_context()):  # not the caller's precision
                delta = row["settled_usd"] - row["reserved_usd"]
            if (
                was == "open" or delta
            ):  # a row that was expired and does not rise leaves the counters alone
                # the row's own day and its month, never today's; day first, then month
                for query, key in (
                    (
                        "UPDATE {spend} SET usd = usd + %s WHERE agent_id = %s AND day = %s",
                        row["day"],
                    ),
                    (
                        "UPDATE {spend_month} SET usd = usd + %s WHERE agent_id = %s AND month = %s",
                        row["day"].replace(day=1),
                    ),
                ):
                    if self._exec(self._t(query), (delta, row["agent_id"], key)).rowcount == 0:
                        raise RuntimeError("spend counter row missing")  # rolls the claim back
            if row["run_id"] is not None:  # the real actual amount; a missing run row is ignored
                self._exec(
                    "UPDATE runs SET cost_usd = cost_usd + %s WHERE run_id = %s",
                    (actual_usd, row["run_id"]),
                )
        return SpendReservation.model_validate(row), True

    def expire_spend_reservations(self, older_than_s: int) -> int:
        """The age is measured on the database clock; the counters do not move."""
        check_expiry_age(older_than_s)
        with self._lock:
            return self._exec(
                self._t(
                    "UPDATE {spend_reservations} SET status = 'expired', settled_usd = reserved_usd, "
                    "closed_at = clock_timestamp() WHERE status = 'open' "
                    "AND created_at <= clock_timestamp() - make_interval(secs => %s::double precision)"
                ),
                (older_than_s,),
            ).rowcount

    def purge_spend_reservations(self, before: datetime) -> int:
        """SETTLED rows only (a settled row, or one released by 0008: settled at 0). An expired hold nobody
        settled is KEPT: it is still booked, and a late settle must find it (E11 M3). Run by the purge role,
        which reads `status` and `closed_at` and nothing else."""
        check_purge_bound(before)
        with self._lock:
            return self._exec(
                self._t(
                    "DELETE FROM {spend_reservations} WHERE status = 'settled' AND closed_at < %s"
                ),
                (before,),
            ).rowcount

    def release_expired_spend(
        self, agent_id: str, day: date, actor: str, audit: Any
    ) -> SpendRelease:
        """Release the EXPIRED holds of one agent and one day (migration 0008). Order: the audit intent row is
        written first (if that fails, nothing changed and the error is raised); then ONE transaction lowers the
        expired rows to settled at 0 and moves the day and the month counter by the same sum, never below zero;
        then the outcome row (its failure is logged, never raised: the release is committed). Live (open) holds,
        settled rows and other days are not touched. Runs only under the release login: any other login gets
        InsufficientPrivilege and a `release_failed` outcome. `audit` is the chain audit of the same login."""
        check_store_id(agent_id, "agent_id")
        check_store_id(actor, "actor")
        check_spend_day(day)
        ref = f"{agent_id}:{day.isoformat()}"
        intent_id = audit.write_intent(_release_event(actor, ref, "intent"))
        try:
            with self._lock, self._db.transaction():
                row = self._exec(
                    "SELECT * FROM hadavin_release_expired_spend(%s, %s)", (agent_id, day)
                ).fetchone()
        except Exception as exc:
            _write_outcome(audit, _release_event(actor, ref, "release_failed", type(exc).__name__))
            raise
        done = SpendRelease(
            agent_id=agent_id,
            day=day,
            reservations=int(row["reservations"]),
            released_usd=row["released_usd"],
            day_usd=row["day_usd"],
            month_usd=row["month_usd"],
            applied_usd=row["applied_usd"] if row["applied_usd"] is not None else Decimal(0),
            intent_id=str(intent_id),
        )
        # requested = the sum of the expired holds; applied = what the day counter really fell by (a lower
        # applied than requested is drift that the counter clamp at zero would otherwise hide)
        audited = _write_outcome(
            audit,
            _release_event(
                actor,
                ref,
                f"released rows={done.reservations} requested_usd={done.released_usd} "
                f"applied_usd={done.applied_usd}",
            ),
        )
        return replace(done, outcome_audited=audited)


def _release_event(actor: str, ref: str, result: str, error: str | None = None) -> AuditEvent:
    return AuditEvent(
        run_id="-",
        domain="limits",
        operation="release_expired",
        principal=actor,
        source="cli",
        object_ref=ref,
        result=result,
        error_code=error,
    )


def _write_outcome(audit: Any, event: AuditEvent) -> bool:
    """True only when the outcome row reached the chain. The audit contract is "never raises": a failed append is
    parked (outbox table, which the release login cannot write, or memory of this process) and `write_outcome`
    returns None, so a None key means the row is NOT in the chain and the process may end before it is drained.
    An exception is the same answer (the release is already committed or already failed: logged, not raised)."""
    try:
        key = audit.write_outcome(event)
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("release outcome not audited error_kind=%s", type(exc).__name__)
        return False
    if key is None:
        _LOG.warning("release outcome parked, not in the chain event_id=%s", event.event_id)
        return False
    return True
