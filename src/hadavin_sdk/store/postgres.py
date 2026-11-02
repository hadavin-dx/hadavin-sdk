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
import queue
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
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

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Plan,
    Run,
    RunState,
    TickState,
    now,
)
from hadavin_sdk.store.protocol import NotFound, StaleState, StoreUnavailable

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
    captured by an impostor); an explicit weaker `sslmode` is an opt-down for dev. With iam_auth (a bearer
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
            "sslrootcert_secret_name (a PEM in the secrets backend), or opt down with sslmode for dev"
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
    root_cert = ca_file(settings, deps.resolve)

    def connector() -> psycopg.Connection:
        return connect(
            dsn,
            iam_auth=settings.iam_auth,
            region=settings.region,
            sslmode=settings.sslmode,
            sslrootcert=root_cert,
        )

    try:
        conn = connector()
    except psycopg.OperationalError as exc:
        # The class only: driver messages can carry the host and user.
        raise StoreUnavailable(
            f"store postgres: cannot connect ({exc.__class__.__name__})"
        ) from None
    return PostgresStore(conn, connector)


RUN_KEY_SQL = r"^([0-9]+:[^/]*/)?run:"  # a per-run counter key (see Limits._key)


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


class _RolledBack(Exception):
    """Raised inside a spend transaction to undo it and hand ``result`` back to the caller."""

    def __init__(self, result: Any) -> None:
        super().__init__("rolled back")
        self.result = result


class PostgresStore:
    # ponytail: one connection behind one lock per process; a pool (psycopg_pool) when throughput matters.
    # A dropped connection fails the call (the run ends safely); reconnect-on-error arrives with S11 hosting.
    # Spend reservations wait on row locks, so they use a connection of their own (``connector``) and never hold
    # the process lock while waiting; without a connector (a test wrapping one connection) they share ``conn``.
    LOCK_TIMEOUT_MS = 5000
    RESERVE_ATTEMPTS = 3
    POOL_SIZE = (
        8  # connections for spend work, per process: bounded, well below a server's max_connections
    )
    POOL_WAIT_S = 10.0

    def __init__(
        self, conn: psycopg.Connection, connector: Callable[[], psycopg.Connection] | None = None
    ) -> None:
        self._db = conn
        self._connector = connector
        self._lock = threading.Lock()
        self._idle: queue.LifoQueue[psycopg.Connection] = queue.LifoQueue()
        self._slots = threading.BoundedSemaphore(self.POOL_SIZE)

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
        return Decimal(d), Decimal(m)

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

    def close(self) -> None:
        """Close the spend pool and the main connection."""
        while True:
            try:
                self._idle.get_nowait().close()
            except queue.Empty:
                break
        self._db.close()

    @contextmanager
    def _borrow(self) -> Iterator[psycopg.Connection]:
        """A pooled connection for spend work (at most POOL_SIZE at once; callers wait, then fail closed).
        A connection that raised is closed, never reused. Connect errors become StoreUnavailable carrying the
        class name only (driver text can hold the host and user)."""
        if not self._slots.acquire(timeout=self.POOL_WAIT_S):
            raise StoreUnavailable("store postgres: no spend connection free (pool exhausted)")
        conn = None
        try:
            try:
                conn = self._idle.get_nowait()
                if conn.closed or conn.broken:
                    conn = None
            except queue.Empty:
                pass
            if conn is None:
                if self._connector is None:
                    raise StoreUnavailable("store postgres: no connector for pooled spend work")
                for attempt in (1, 2):  # one retry of a connect failure
                    try:
                        conn = self._connector()
                        break
                    except psycopg.Error as exc:
                        if attempt == 2:
                            raise StoreUnavailable(
                                f"store postgres: cannot connect ({type(exc).__name__})"
                            ) from None
                        time.sleep(0.05)
            yield conn
        except BaseException:
            if conn is not None:
                conn.close()
            conn = None
            raise
        finally:
            if conn is not None:
                self._idle.put(conn)
            self._slots.release()

    def _spend_tx(self, work: Callable[[psycopg.Connection], Any]) -> Any:
        """Run ``work`` in one transaction with a bounded lock wait, retrying a serialization failure, a deadlock
        or a lock timeout a few times; then fail closed with StoreUnavailable (the caller does not proceed).
        Any other database error is StoreUnavailable too, by class name only."""
        last: Exception | None = None
        for attempt in range(self.RESERVE_ATTEMPTS):
            try:
                if (
                    self._connector is None
                ):  # a test wrapping one connection: share it under the lock
                    with self._lock:
                        return self._run_tx(self._db, work)
                with self._borrow() as conn:
                    return self._run_tx(conn, work)
            except (
                psycopg.errors.SerializationFailure,
                psycopg.errors.DeadlockDetected,
                psycopg.errors.LockNotAvailable,
            ) as exc:
                last = exc
                if attempt + 1 < self.RESERVE_ATTEMPTS:
                    time.sleep(0.02 * (attempt + 1))
            except psycopg.Error as exc:  # every driver error: its text can quote a parameter value
                raise StoreUnavailable(
                    f"store postgres: spend operation failed ({type(exc).__name__})"
                ) from None
        raise StoreUnavailable(
            f"store postgres: spend counters busy ({type(last).__name__}) after "
            f"{self.RESERVE_ATTEMPTS} attempts"
        ) from None

    def _run_tx(self, conn: psycopg.Connection, work: Callable[[psycopg.Connection], Any]) -> Any:
        try:
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('lock_timeout', %s, true)",
                    (f"{int(self.LOCK_TIMEOUT_MS)}ms",),
                )
                return work(conn)
        except (
            _RolledBack
        ) as done:  # the work decided nothing is to be written: the rollback is the answer
            return done.result

    @staticmethod
    def _locked_total(
        conn: psycopg.Connection, table: str, col: str, agent_id: str, key
    ) -> Decimal:
        """Create the counter row at zero if absent, lock it (FOR UPDATE) and return its total. ``table`` and
        ``col`` are fixed names from this module."""
        conn.execute(
            sql.SQL(
                "INSERT INTO {t} (agent_id, {c}, usd) VALUES (%s, %s, 0) ON CONFLICT DO NOTHING"
            ).format(t=sql.Identifier(table), c=sql.Identifier(col)),
            (agent_id, key),
        )
        row = (
            conn.cursor(row_factory=dict_row)
            .execute(
                sql.SQL("SELECT usd FROM {t} WHERE agent_id = %s AND {c} = %s FOR UPDATE").format(
                    t=sql.Identifier(table), c=sql.Identifier(col)
                ),
                (agent_id, key),
            )
            .fetchone()
        )
        return Decimal(row["usd"])

    def reserve_spend(
        self,
        agent_id: str,
        day: date,
        usd: Decimal,
        daily_cap: Decimal,
        monthly_cap: Decimal,
        *,
        run_key: str | None = None,
        run_day: date | None = None,
        run_cap: Decimal | None = None,
    ) -> list[str]:
        """One transaction: lock the run, day and month counters (run first, then day before month, the order
        every writer takes them), then read the kill switch, decide, and book all or nothing. A concurrent
        reserver waits on the row lock and then sees this total, so the caps hold across processes."""
        month = day.replace(day=1)
        use_run = run_key is not None and run_cap is not None
        rday = run_day or day

        def work(conn: psycopg.Connection) -> list[str]:
            r = Decimal(0)
            if use_run:
                r = self._locked_total(conn, "spend", "day", run_key, rday)
                self._locked_total(conn, "spend_month", "month", run_key, rday.replace(day=1))
            d = self._locked_total(conn, "spend", "day", agent_id, day)
            m = self._locked_total(conn, "spend_month", "month", agent_id, month)
            ks = (
                conn.cursor(row_factory=dict_row)
                .execute('SELECT "on" FROM kill_switch WHERE id = 1')
                .fetchone()
            )
            if (
                ks is None or ks["on"]
            ):  # a missing row is ON (fail closed), as get_kill_switch reads it
                raise _RolledBack(["kill_switch"])
            reasons = []
            if use_run and r + usd > run_cap:
                reasons.append("run_budget")
            if d + usd > daily_cap:
                reasons.append("daily_budget")
            if m + usd > monthly_cap:
                reasons.append("monthly_budget")
            if reasons:
                # Roll back: the zero rows inserted above only to lock the counters must not stay (agent rows are
                # never pruned, so a refused day would leave one forever).
                raise _RolledBack(reasons)
            self._add(conn, agent_id, day, usd)
            if use_run:
                self._add(conn, run_key, rday, usd)
            return []

        return self._spend_tx(work)

    @staticmethod
    def _add(conn: psycopg.Connection, agent_id: str, day: date, usd: Decimal) -> None:
        if (
            usd < 0
        ):  # taking back: only from a counter that exists (a pruned one is not recreated negative)
            conn.execute(
                "UPDATE spend SET usd = usd + %s WHERE agent_id = %s AND day = %s",
                (usd, agent_id, day),
            )
            conn.execute(
                "UPDATE spend_month SET usd = usd + %s WHERE agent_id = %s AND month = %s",
                (usd, agent_id, day.replace(day=1)),
            )
            return
        conn.execute(
            "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) "
            "ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd",
            (agent_id, day, usd),
        )
        conn.execute(
            "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) "
            "ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd",
            (agent_id, day.replace(day=1), usd),
        )

    def settle_spend(self, deltas: list[tuple[str, date, Decimal]]) -> None:
        def work(conn: psycopg.Connection) -> None:
            for (
                agent_id,
                day,
                delta,
            ) in deltas:  # in the caller's order: run counter first (as reserve)
                self._add(conn, agent_id, day, delta)

        self._spend_tx(work)

    def prune_spend(self, before: date) -> int:
        def work(conn: psycopg.Connection) -> int:
            n = conn.execute(
                "DELETE FROM spend WHERE agent_id ~ %s AND day < %s", (RUN_KEY_SQL, before)
            ).rowcount
            conn.execute(
                "DELETE FROM spend_month WHERE agent_id ~ %s AND month < %s",
                (RUN_KEY_SQL, before.replace(day=1)),
            )
            return n

        return self._spend_tx(work)

    def get_kill_switch(self) -> KillSwitch:
        found = self._select(KillSwitch, "kill_switch", "id = 1", ())
        if not found:  # migrate seeds the row: its absence means a broken schema, so fail closed
            _LOG.error(
                "kill_switch row missing: treating the kill switch as ON; run hadavin-sdk migrate"
            )
            return KillSwitch(on=True, by="system:kill_switch_row_missing")
        return found[0]

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

    def save_tick_state(self, state: TickState) -> None:
        self._insert("tick_state", state, upsert_on="step")
