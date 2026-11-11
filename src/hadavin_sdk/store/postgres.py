"""Postgres store (`pip install hadavin-sdk[pg]`). Same Protocol as `memory`; compare-and-set is in SQL, so it
holds across processes. The schema comes from `hadavin-sdk migrate` (`store/migrate.py`), never from here.

Connect pattern ported from WARDEN `audit.py:_pg_connect` (main a1e76cbf): with `iam_auth` and no password in
the DSN, the login is a 15-minute RDS IAM token and TLS is required.

Neutral protocol: the PostgreSQL wire protocol and SQL (any Postgres: RDS, Cloud SQL, Azure, self-hosted).
"""

from __future__ import annotations

import functools
import ipaddress
import logging
import os
import tempfile
import threading
import time
from collections.abc import Callable, Mapping
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from hadavin_sdk import defaults
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    OPEN_STATES,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Plan,
    Run,
    RunState,
    SpendReservation,
    TickState,
    ToolCallRecord,
    now,
)
from hadavin_sdk.store.protocol import (
    MAX_COUNTER_USD,
    MIN_SWEEP_AGE_S,
    CounterDamaged,
    KillSwitchOn,
    NotFound,
    ReservationConflict,
    SpendCapExceeded,
    SpendOutcome,
    StaleState,
    StoreBusy,
    StoreUnavailable,
    check_day,
    check_id,
    check_int,
    check_reserve,
    check_text,
    check_usd,
)

_LOG = logging.getLogger("hadavin_sdk.store")

# A purge deletes in batches so no one statement is long enough to hit the call budget's statement timeout.
PURGE_BATCH_ROWS = defaults.STORE_PURGE_BATCH_ROWS
PURGE_MIN_LEFT_MS = defaults.STORE_PURGE_MIN_LEFT_MS


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
    return conn


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
    return PostgresStore(
        conn,
        lock_timeout_ms=getattr(settings, "lock_timeout_ms", 1000),
        call_budget_ms=getattr(settings, "call_budget_ms", 5000),
    )


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


# Only these two sqlstates are retried (a deadlock and a serialization failure); never 40003 (outcome unknown).
_RETRY_SQLSTATES = frozenset({"40001", "40P01"})
_ATTEMPTS = 3


def _sqlstate(exc: BaseException) -> str | None:
    return getattr(exc, "sqlstate", None) if isinstance(exc, psycopg.Error) else None


def _map_error(exc: psycopg.Error) -> Exception | None:
    """Driver error -> Protocol error (the class only, never the driver text: it can carry values). None: let it
    through unchanged (connection, schema and privilege errors)."""
    E = psycopg.errors
    if isinstance(exc, E.UniqueViolation):
        return StaleState("conflict: the row already exists")
    if isinstance(exc, E.ForeignKeyViolation):
        return NotFound("a referenced row does not exist")
    if isinstance(
        exc, E.CheckViolation | E.NotNullViolation | E.DataError | E.ProgramLimitExceeded
    ):
        return ValueError(f"the store cannot hold this value ({type(exc).__name__})")
    if isinstance(exc, E.LockNotAvailable | E.QueryCanceled):
        return StoreBusy(f"the store was busy ({type(exc).__name__})")
    if _sqlstate(exc) in _RETRY_SQLSTATES:
        return StoreBusy(f"the store was busy ({type(exc).__name__})")
    return None


def _writes(retry: bool = True):
    """Mark a write method: one transaction per attempt whose first statement sets the timeouts, a whole-call
    budget, retries on 40001 and 40P01 only (`retry=False`: none, the call raises `StoreBusy` at once), and the
    driver errors mapped to Protocol errors. See `PostgresStore._write`."""

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            return self._write(fn, retry, args, kwargs)

        wrapper._writes = True  # the scan test reads this
        wrapper._retry = retry
        return wrapper

    return deco


def _checked_ms(name: str, value: object) -> int:
    """`value` must be a whole number of milliseconds inside the range the settings model declares for `name`
    (BN N5). A bool is refused (it is an int in Python)."""
    meta = PostgresSettings.model_fields[name].metadata
    low = next(m.ge for m in meta if hasattr(m, "ge"))
    high = next(m.le for m in meta if hasattr(m, "le"))
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be a whole number from {low} to {high}")
    return value


class PostgresStore:
    # ponytail: one connection behind one lock per process; a pool (psycopg_pool) when throughput matters.
    # A dropped connection fails the call (the run ends safely); reconnect-on-error arrives with S11 hosting.
    def __init__(
        self,
        conn: psycopg.Connection,
        *,
        on_retry: Callable[[str, int], None] | None = None,
        lock_timeout_ms: int = 1000,
        call_budget_ms: int = 5000,
    ) -> None:
        # Settings ranges are the PostgresSettings ranges (one place): a value outside them is refused, so a
        # budget of 0 can never build a store that refuses every write.
        self._lock_timeout_ms = _checked_ms("lock_timeout_ms", lock_timeout_ms)
        self._call_budget_ms = _checked_ms("call_budget_ms", call_budget_ms)
        self._db = conn
        # Re-entrant: the write wrapper holds it for a whole transaction and the helpers take it again inside.
        self._lock = threading.RLock()
        self._on_retry = on_retry
        self._deadline: float | None = None  # monotonic; set only by the thread that holds the lock

    def _write(self, fn, retry: bool, args: tuple, kwargs: dict):
        for a in (*args, *kwargs.values()):
            if isinstance(a, BaseModel | dict | str):
                check_text(a)
        deadline = time.monotonic() + self._call_budget_ms / 1000

        def attempt():
            with self._lock:
                if self._deadline is not None:  # called from inside another wrapped write
                    return fn(self, *args, **kwargs)
                left = int((deadline - time.monotonic()) * 1000)
                if left < 1:
                    raise StoreBusy("the call budget was spent")
                self._deadline = deadline
                try:
                    with self._db.transaction():
                        self._db.execute(
                            "SELECT set_config('lock_timeout', %s, true), "
                            "set_config('statement_timeout', %s, true)",
                            (str(min(self._lock_timeout_ms, left)), str(left)),
                        )
                        return fn(self, *args, **kwargs)
                finally:
                    self._deadline = None

        def before_sleep(state: RetryCallState) -> None:
            if self._on_retry is not None:
                exc = state.outcome.exception()
                self._on_retry(_sqlstate(exc) or "", state.attempt_number)

        # The sleep happens between attempts, outside the lock and outside any transaction.
        retrying = Retrying(
            stop=stop_after_attempt(_ATTEMPTS if retry else 1),
            wait=wait_exponential_jitter(multiplier=0.02, max=1, exp_base=2, jitter=0.02),
            retry=retry_if_exception(lambda e: _sqlstate(e) in _RETRY_SQLSTATES),
            before_sleep=before_sleep,
            reraise=True,
        )
        try:
            return retrying(attempt)
        except psycopg.Error as exc:
            mapped = _map_error(exc)
            if mapped is None:
                raise
            raise mapped from None

    # --- generic helpers ---------------------------------------------------------------------------------

    def _exec(self, query, params=()) -> psycopg.Cursor:
        """The one way a method sends SQL. Inside a wrapped write it first compares the monotonic clock with the
        call's deadline: a spent budget rolls the transaction back (the raise) and the statement is NOT sent."""
        deadline = self._deadline
        if deadline is not None and time.monotonic() >= deadline:
            raise StoreBusy("the call budget was spent")
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

    @_writes()
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

    @_writes()
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

    @_writes(retry=False)
    def add_cost(self, run_id: str, usd: Decimal) -> None:
        check_usd(usd, max_decimals=8)
        with self._lock, self._db.transaction():
            row = self._exec(
                "UPDATE runs SET cost_usd = cost_usd + %s WHERE run_id = %s RETURNING cost_usd",
                (usd, run_id),
            ).fetchone()
            if row is None:
                raise NotFound(run_id)
            if row["cost_usd"] > MAX_COUNTER_USD:  # the ValueError rolls the transaction back
                raise ValueError("the run counter would pass its ceiling")

    @_writes(retry=False)
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

    @_writes()
    def save_plan(self, plan: Plan) -> None:
        self._insert("plans", plan, upsert_on="run_id")

    def get_plan(self, run_id: str) -> Plan:
        return self._one(Plan, "plans", "run_id", run_id)

    @_writes()
    def save_gate_decision(self, decision: GateDecision) -> None:
        try:
            self._insert("gate_decisions", decision)  # append-only: the runtime role has no UPDATE
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"gate decision exists: {decision.run_id}") from None

    def get_gate_decision(self, run_id: str) -> GateDecision:
        return self._one(GateDecision, "gate_decisions", "run_id", run_id)

    # --- approvals -----------------------------------------------------------------------------------------

    @_writes()
    def save_approval_request(self, req: ApprovalRequest) -> None:
        self._insert("approval_requests", req, upsert_on="approval_id")

    def get_approval_request(self, approval_id: str) -> ApprovalRequest:
        return self._one(ApprovalRequest, "approval_requests", "approval_id", approval_id)

    @_writes()
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

    @_writes()
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

    @_writes()
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
            " ORDER BY created_at, approval_id",
        )

    # --- dead letters, spend, kill switch ------------------------------------------------------------------

    @_writes(retry=False)
    def add_dead_letter(self, dl: DeadLetter) -> None:
        self._insert("dead_letters", dl)

    def list_dead_letters(self, run_id: str) -> list[DeadLetter]:
        return self._select(DeadLetter, "dead_letters", "run_id = %s", (run_id,), " ORDER BY seq")

    @_writes(retry=False)
    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
        """Day and month counters, each one atomic upsert, in one transaction: exact under concurrency."""
        check_usd(usd, max_decimals=8)
        check_day(day)
        month = day.replace(day=1)
        with self._lock, self._db.transaction():
            d = self._exec(
                "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) "
                "ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd",
                (agent_id, day, usd),
            ).fetchone()["usd"]
            m = self._exec(
                "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) "
                "ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd "
                "RETURNING usd",
                (agent_id, month, usd),
            ).fetchone()["usd"]
            if (
                d > MAX_COUNTER_USD or m > MAX_COUNTER_USD
            ):  # the ValueError rolls both counters back
                raise ValueError("a spend counter would pass its ceiling")
        return Decimal(d), Decimal(m)

    # --- spend reservations (P4d-b) -------------------------------------------------------------------------

    @staticmethod
    def _reservation(row: dict) -> SpendReservation:
        micro = Decimal("1E-6")
        for k in ("reserved_usd", "settled_usd"):
            if row.get(k) is not None:
                row[k] = Decimal(row[k]).quantize(micro)
        return SpendReservation.model_validate(row)

    def _stored_reservation(self, reservation_id: str) -> SpendReservation | None:
        row = self._exec(
            "SELECT * FROM spend_reservations WHERE reservation_id = %s", (reservation_id,)
        ).fetchone()
        return None if row is None else self._reservation(row)

    def _cap_failure(self, which: str, table: str, key: dict, cap: Decimal, amount: Decimal):
        cols = {"runs": "cost_usd", "spend": "usd", "spend_month": "usd"}
        where = sql.SQL(" AND ").join(
            sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder(k)) for k in key
        )
        query = sql.SQL("SELECT {} AS v FROM {} WHERE {}").format(
            sql.Identifier(cols[table]), sql.Identifier(table), where
        )
        cur = self._exec(query, key).fetchone()
        return SpendCapExceeded(which, cap, cur["v"] if cur else Decimal(0), amount)

    @_writes()
    def reserve_spend(
        self,
        reservation_id: str,
        agent_id: str,
        day: date,
        amount_usd: Decimal,
        *,
        day_cap: Decimal | None,
        month_cap: Decimal | None,
        run_id: str | None = None,
        run_cap: Decimal | None,
        meta: Mapping[str, str | int | bool] | None = None,
    ) -> SpendOutcome:
        amount, meta_ok = check_reserve(
            reservation_id, agent_id, day, amount_usd, day_cap, month_cap, run_id, run_cap, meta
        )
        month = day.replace(day=1)
        with self._lock, self._db.transaction():
            if self.get_kill_switch().on:  # the one kill switch read (fails closed)
                raise KillSwitchOn("the kill switch is on")
            if run_id is not None:
                run = self._exec(
                    "SELECT agent_id FROM runs WHERE run_id = %s", (run_id,)
                ).fetchone()
                if run is None:
                    raise NotFound(run_id)
                if run["agent_id"] != agent_id:
                    raise ValueError("the run belongs to another agent")
            inserted = self._exec(
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, run_id, "
                "reserved_usd, meta) VALUES (%s, 1, %s, %s, %s, %s, %s) "
                "ON CONFLICT (reservation_id) DO NOTHING RETURNING *",
                (
                    reservation_id,
                    agent_id,
                    day,
                    run_id,
                    amount,
                    None if meta_ok is None else Jsonb(meta_ok),
                ),
            ).fetchone()
            if inserted is None:
                stored = self._stored_reservation(reservation_id)
                if stored is None:  # the winner rolled back between our insert and our read
                    raise StaleState(f"reservation {reservation_id} changed, retry")
                same = (
                    stored.agent_id == agent_id
                    and stored.day == day
                    and stored.reserved_usd == amount
                    and stored.run_id == run_id
                )
                if not same:
                    raise ReservationConflict(reservation_id)
                if stored.status != "open":
                    raise StaleState(f"reservation {reservation_id} is {stored.status}")
                return SpendOutcome(stored, False)
            today = self._exec("SELECT (now() AT TIME ZONE 'UTC')::date AS d").fetchone()["d"]
            if abs((day - today).days) > 1:
                raise ValueError("day must be within one day of today (UTC)")
            self._exec(
                "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, 0) ON CONFLICT DO NOTHING",
                (agent_id, day),
            )
            self._exec(
                "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, 0) "
                "ON CONFLICT DO NOTHING",
                (agent_id, month),
            )
            totals = []
            steps = []
            if run_id is not None:
                steps.append(
                    (
                        "run",
                        "runs",
                        (
                            "UPDATE runs SET cost_usd = cost_usd + %(amt)s WHERE run_id = %(run_id)s "
                            "AND (%(cap)s::numeric IS NULL OR cost_usd + %(amt)s <= %(cap)s) "
                            "RETURNING cost_usd AS v"
                        ),
                        {"run_id": run_id},
                        run_cap,
                    )
                )
            steps.append(
                (
                    "day",
                    "spend",
                    (
                        "UPDATE spend SET usd = usd + %(amt)s WHERE agent_id = %(agent_id)s AND day = %(day)s "
                        "AND (%(cap)s::numeric IS NULL OR usd + %(amt)s <= %(cap)s) RETURNING usd AS v"
                    ),
                    {"agent_id": agent_id, "day": day},
                    day_cap,
                )
            )
            steps.append(
                (
                    "month",
                    "spend_month",
                    (
                        "UPDATE spend_month SET usd = usd + %(amt)s WHERE agent_id = %(agent_id)s "
                        "AND month = %(month)s AND (%(cap)s::numeric IS NULL OR usd + %(amt)s <= %(cap)s) "
                        "RETURNING usd AS v"
                    ),
                    {"agent_id": agent_id, "month": month},
                    month_cap,
                )
            )
            for which, table, query, key, cap in steps:
                got = self._exec(query, {**key, "amt": amount, "cap": cap}).fetchone()
                if got is None:  # that counter's cap failed: the whole transaction rolls back
                    raise self._cap_failure(which, table, key, cap, amount)
                totals.append(got["v"])
            if any(t > MAX_COUNTER_USD for t in totals):
                raise ValueError("a spend counter would pass its ceiling")
            return SpendOutcome(self._reservation(inserted), True)

    def _close(self, reservation_id: str, status: str, actual: Decimal | None) -> SpendOutcome:
        """Settle or release: the claim is the first write; the counters move in lock order (run, day, month) by
        `delta` (positive lowers through a guard in the WHERE clause, negative raises). Zero rows from a counter
        means damaged data: everything rolls back, the claim included."""
        with self._lock, self._db.transaction():
            claim = self._exec(
                "UPDATE spend_reservations SET status = %s, settled_usd = %s, closed_at = clock_timestamp() "
                "WHERE reservation_id = %s AND status IN ('open', 'expired') RETURNING *",
                (status, actual, reservation_id),
            ).fetchone()
            if claim is None:
                stored = self._stored_reservation(reservation_id)
                if stored is None:
                    raise NotFound(reservation_id)
                return SpendOutcome(stored, False)
            delta = claim["reserved_usd"] - (0 if actual is None else actual)
            targets = []
            if claim["run_id"] is not None:
                targets.append(
                    ("runs", "cost_usd", "run_id = %(run_id)s", {"run_id": claim["run_id"]})
                )
            targets.append(
                (
                    "spend",
                    "usd",
                    "agent_id = %(agent_id)s AND day = %(day)s",
                    {"agent_id": claim["agent_id"], "day": claim["day"]},
                )
            )
            targets.append(
                (
                    "spend_month",
                    "usd",
                    "agent_id = %(agent_id)s AND month = %(month)s",
                    {"agent_id": claim["agent_id"], "month": claim["day"].replace(day=1)},
                )
            )
            for table, col, where, key in targets:
                query = sql.SQL(
                    "UPDATE {t} SET {c} = {c} - %(delta)s WHERE {w} AND {c} >= %(delta)s RETURNING {c}"
                ).format(t=sql.Identifier(table), c=sql.Identifier(col), w=sql.SQL(where))
                got = self._exec(query, {**key, "delta": delta}).fetchone()
                if got is None:
                    _LOG.error(
                        "spend counter damaged: %s for reservation %s", table, reservation_id
                    )
                    raise CounterDamaged(
                        f"{table}: a counter is lower than the amount to lower or missing"
                    )
            return SpendOutcome(self._reservation(claim), True)

    @_writes()
    def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendOutcome:
        check_id(reservation_id, "reservation_id")
        check_usd(actual_usd, max_decimals=6)
        return self._close(reservation_id, "settled", actual_usd.quantize(Decimal("1E-6")))

    @_writes()
    def release_spend(self, reservation_id: str) -> SpendOutcome:
        check_id(reservation_id, "reservation_id")
        return self._close(reservation_id, "released", None)

    def get_spend_reservation(self, reservation_id: str) -> SpendReservation:
        with self._lock:
            found = self._stored_reservation(reservation_id)
        if found is None:
            raise NotFound(reservation_id)
        return found

    def list_open_reservations(
        self, agent_id: str | None = None, run_id: str | None = None, limit: int = 100
    ) -> list[SpendReservation]:
        check_int(limit, 1, 1000)
        with self._lock:
            rows = self._exec(
                "SELECT * FROM spend_reservations WHERE status = 'open' "
                "AND (%(a)s::text IS NULL OR agent_id = %(a)s) AND (%(r)s::text IS NULL OR run_id = %(r)s) "
                "ORDER BY created_at, reservation_id LIMIT %(n)s",
                {"a": agent_id, "r": run_id, "n": limit},
            ).fetchall()
        return [self._reservation(r) for r in rows]

    @_writes()
    def sweep_spend_reservations(
        self, older_than_s: int, *, limit: int = 100
    ) -> list[SpendReservation]:
        check_int(older_than_s, MIN_SWEEP_AGE_S, 10**7)
        check_int(limit, 1, 1000)
        with self._lock, self._db.transaction():
            ids = self._exec(
                "SELECT reservation_id FROM spend_reservations WHERE status = 'open' "
                "AND clock_timestamp() - created_at > make_interval(secs => %s) "
                "ORDER BY created_at, reservation_id LIMIT %s FOR UPDATE SKIP LOCKED",
                (older_than_s, limit),
            ).fetchall()
            out = []
            for r in ids:
                row = self._exec(
                    "UPDATE spend_reservations SET status = 'expired', settled_usd = reserved_usd, "
                    "closed_at = clock_timestamp(), expired_at = clock_timestamp() "
                    "WHERE reservation_id = %s AND status = 'open' RETURNING *",
                    (r["reservation_id"],),
                ).fetchone()
                if row is not None:
                    out.append(self._reservation(row))
            return out

    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
        with self._lock:
            d = self._exec(
                "SELECT usd FROM spend WHERE agent_id = %s AND day = %s", (agent_id, day)
            ).fetchone()
            m = self._exec(
                "SELECT usd FROM spend_month WHERE agent_id = %s AND month = %s",
                (agent_id, day.replace(day=1)),
            ).fetchone()
        return (Decimal(d["usd"]) if d else Decimal(0)), (Decimal(m["usd"]) if m else Decimal(0))

    def get_kill_switch(self) -> KillSwitch:
        found = self._select(KillSwitch, "kill_switch", "id = 1", ())
        if not found:  # migrate seeds the row: its absence means a broken schema, so fail closed
            _LOG.error(
                "kill_switch row missing: treating the kill switch as ON; run hadavin-sdk migrate"
            )
            return KillSwitch(on=True, by="system:kill_switch_row_missing")
        return found[0]

    @_writes()
    def set_kill_switch(self, ks: KillSwitch) -> None:
        row = {"id": 1, **_row(ks)}
        cols = [sql.Identifier(c) for c in row]
        query = sql.SQL(
            "INSERT INTO kill_switch ({}) VALUES ({}) ON CONFLICT (id) DO UPDATE SET {}"
        ).format(
            sql.SQL(", ").join(cols),
            sql.SQL(", ").join(sql.Placeholder() * len(row)),
            sql.SQL(", ").join(sql.SQL("{0} = EXCLUDED.{0}").format(c) for c in cols[1:]),
        )
        with self._lock:
            self._exec(query, list(row.values()))

    def get_tick_state(self, step: str) -> TickState | None:
        found = self._select(TickState, "tick_state", "step = %s", (step,))
        return found[0] if found else None

    @_writes()
    def save_tick_state(self, state: TickState) -> None:
        self._insert("tick_state", state, upsert_on="step")

    # --- evidence (K5) ------------------------------------------------------------------------------------------

    @_writes()
    def add_tool_call(self, call: ToolCallRecord) -> None:
        try:
            self._insert("tool_calls", call)
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"tool call exists: {call.call_id}") from None

    def list_tool_calls(self, run_id: str) -> list[ToolCallRecord]:
        return self._select(
            ToolCallRecord, "tool_calls", "run_id = %s", (run_id,), " ORDER BY created_at, call_id"
        )

    def _purge_in_batches(self, query: str, params: tuple) -> int:
        """Delete in batches of `PURGE_BATCH_ROWS` rows (class: one unbounded statement under a call budget). `query`
        is a DELETE whose last `%s` is the batch size. Stops when a batch is short or the call budget is nearly spent;
        what the finished batches deleted stays deleted and is returned (a purge is safe to run again, so a caller
        that needs every row gone calls until the answer is smaller than the batch size)."""
        total = 0
        while True:
            deadline = self._deadline
            if (
                total
                and deadline is not None
                and (deadline - time.monotonic()) * 1000 < PURGE_MIN_LEFT_MS
            ):  # a first batch always goes to `_exec`, which raises StoreBusy when the budget is spent
                return total
            deleted = self._exec(query, (*params, PURGE_BATCH_ROWS)).rowcount
            total += deleted
            if deleted < PURGE_BATCH_ROWS:
                return total

    @_writes()
    def purge_tool_calls(self, before: datetime, *, keep_run_ids: frozenset[str]) -> int:
        with self._lock:
            return self._purge_in_batches(
                "DELETE FROM tool_calls WHERE call_id IN (SELECT call_id FROM tool_calls "
                "WHERE created_at < %s AND NOT (run_id = ANY(%s)) ORDER BY call_id LIMIT %s)",
                (before, sorted(keep_run_ids)),
            )

    @_writes()
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

    @_writes()
    def purge_redaction_maps(
        self, before: datetime, *, keep_run_ids: frozenset[str], keep_open: bool = True
    ) -> int:
        """Aged from the run's last state change (the map's own time when the run is unknown); the maps of runs
        that can still move (OPEN_STATES) are kept unless `keep_open` is false. A run parked in NEEDS_PERSON cannot
        move, so its map ages like a finished run's."""
        with self._lock:
            if keep_open:
                open_states = sorted(s.value for s in OPEN_STATES)
                return self._purge_in_batches(
                    "DELETE FROM redaction_maps WHERE run_id IN (SELECT m.run_id FROM redaction_maps m "
                    "WHERE NOT (m.run_id = ANY(%s)) AND "
                    "COALESCE((SELECT r.updated_at FROM runs r WHERE r.run_id = m.run_id), m.updated_at) < %s "
                    "AND NOT EXISTS (SELECT 1 FROM runs r WHERE r.run_id = m.run_id AND r.state = ANY(%s)) "
                    "ORDER BY m.run_id LIMIT %s)",
                    (sorted(keep_run_ids), before, open_states),
                )
            return self._purge_in_batches(
                "DELETE FROM redaction_maps WHERE run_id IN (SELECT m.run_id FROM redaction_maps m "
                "WHERE NOT (m.run_id = ANY(%s)) AND "
                "COALESCE((SELECT r.updated_at FROM runs r WHERE r.run_id = m.run_id), m.updated_at) < %s "
                "ORDER BY m.run_id LIMIT %s)",
                (sorted(keep_run_ids), before),
            )
