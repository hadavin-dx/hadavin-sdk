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
import tempfile
import threading
import time
from collections.abc import Callable
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
    ApprovalWeek,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Label,
    LevelEvent,
    PilotWeek,
    Plan,
    Run,
    RunState,
    TickState,
    now,
)
from hadavin_sdk.store.protocol import HarmfulSticky, NotFound, StaleState, StoreUnavailable

_LOG = logging.getLogger("hadavin_sdk.store")
_DEADLOCK_RETRIES = 3


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


class PostgresStore:
    # ponytail: one connection behind one lock per process; a pool (psycopg_pool) when throughput matters.
    # A dropped connection fails the call (the run ends safely); reconnect-on-error arrives with S11 hosting.
    def __init__(self, conn: psycopg.Connection) -> None:
        self._db = conn
        self._lock = threading.Lock()

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

    # --- K6 measurement ------------------------------------------------------------------------------------

    _LABEL_COLS = "l.seq, l.label_id, l.run_id, l.label, l.principal_id, l.channel, l.approved_by, l.created_at"

    def _retrying(self, fn):
        """Run a transactional `fn`; a deadlock the database breaks is retried (bounded), then raised. The advisory
        locks below are taken in one sorted order, so this is a belt on top of the braces."""
        for attempt in range(_DEADLOCK_RETRIES + 1):
            try:
                return fn()
            except psycopg.errors.DeadlockDetected:
                if attempt == _DEADLOCK_RETRIES:
                    raise
                time.sleep(0.01 * (attempt + 1))
        raise AssertionError("unreachable")  # pragma: no cover

    def _lock_keys(self, keys) -> None:
        # Caller holds self._lock and is inside a transaction. Sorted: every caller takes locks in the same order.
        for key in sorted(set(keys)):
            self._exec("SELECT pg_advisory_xact_lock(hashtext(%s))", (key,))

    def add_labels(
        self, items: list[tuple[Label, LevelEvent | None]], *, may_lower_harmful: bool
    ) -> list[LevelEvent]:
        """All labels (each with its demotion) in ONE transaction. The sticky-harmful check and the insert happen
        under advisory locks for every run and every (agent, action) in the batch, all taken first in one sorted
        order (two batches cannot deadlock; a deadlock the database still breaks is retried). Returns the demotions
        that were really inserted (one that already existed is not). Any failure stores nothing."""
        keys = [f"run/{label.run_id}" for label, _ in items] + [
            f"level/{d.agent_id}/{d.action_id}" for _, d in items if d is not None
        ]

        def attempt() -> list[LevelEvent]:
            inserted: list[LevelEvent] = []
            with self._lock, self._db.transaction():
                self._lock_keys(keys)
                for label, demote in items:
                    if label.label != "harmful" and not may_lower_harmful:
                        cur = self._exec(
                            "SELECT label FROM labels WHERE run_id = %s "
                            "AND (channel = 'chat' OR approved_by IS NOT NULL) "
                            "ORDER BY seq DESC LIMIT 1",
                            (label.run_id,),
                        ).fetchone()
                        if cur is not None and cur["label"] == "harmful":
                            raise HarmfulSticky(label.run_id)
                    lrow = {
                        k: v for k, v in _row(label).items() if k != "seq"
                    }  # seq is the database's
                    self._exec(
                        sql.SQL("INSERT INTO labels ({}) VALUES ({})").format(
                            sql.SQL(", ").join(sql.Identifier(c) for c in lrow),
                            sql.SQL(", ").join(sql.Placeholder() * len(lrow)),
                        ),
                        list(lrow.values()),
                    )
                    if demote is not None and self._insert_level(demote):
                        inserted.append(demote)
            return inserted

        try:
            return self._retrying(attempt)
        except psycopg.errors.UniqueViolation:
            raise StaleState("label exists") from None

    def claim_action(self, nonce: str, at: datetime) -> bool:
        with self._lock:
            row = self._exec(
                "INSERT INTO seen_actions (nonce, seen_at) VALUES (%s, %s) "
                "ON CONFLICT (nonce) DO NOTHING RETURNING nonce",
                (nonce, at),
            ).fetchone()
        return row is not None

    def release_action(self, nonce: str) -> None:
        with self._lock:
            self._exec("DELETE FROM seen_actions WHERE nonce = %s", (nonce,))

    def purge_actions(self, before: datetime) -> int:
        with self._lock:
            return self._exec("DELETE FROM seen_actions WHERE seen_at < %s", (before,)).rowcount

    def _insert_level(self, ev: LevelEvent) -> bool:
        """Caller holds the lock and is inside a transaction that already holds the (agent, action) advisory lock
        (which orders this against a `clear_demotion` compare-and-set). A demotion that already exists is not
        inserted twice (unique index). True when a row was inserted."""
        row = self._exec(
            'INSERT INTO level_events (agent_id, action_id, kind, reason, "by", at) '
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (agent_id, action_id, reason) WHERE kind = 'demote' DO NOTHING RETURNING seq",
            (ev.agent_id, ev.action_id, ev.kind, ev.reason, ev.by, ev.at),
        ).fetchone()
        return row is not None

    def list_labels_between(self, start: datetime, end: datetime) -> list[Label]:
        return self._labels_where("WHERE l.created_at >= %s AND l.created_at < %s", (start, end))

    def list_csv_import(self, import_id: str) -> list[Label]:
        # import_id is hex from the parser; escape LIKE wildcards anyway
        safe = import_id.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return self._labels_where("WHERE l.label_id LIKE %s", (f"csv-{safe}-%",))

    def list_level_events(self) -> list[LevelEvent]:
        with self._lock:
            rows = self._exec(
                'SELECT seq, agent_id, action_id, kind, reason, "by", at FROM level_events ORDER BY seq'
            ).fetchall()
        return [LevelEvent.model_validate(r) for r in rows]

    def add_level_event(self, event: LevelEvent) -> bool:
        def attempt() -> bool:
            with self._lock, self._db.transaction():
                self._lock_keys([f"level/{event.agent_id}/{event.action_id}"])
                return self._insert_level(event)

        return self._retrying(attempt)

    def clear_demotion(self, event: LevelEvent, expected_seq: int) -> bool:
        def attempt() -> bool:
            with self._lock, self._db.transaction():
                self._lock_keys([f"level/{event.agent_id}/{event.action_id}"])
                newest = self._exec(
                    "SELECT max(seq) AS s FROM level_events WHERE agent_id = %s AND action_id = %s",
                    (event.agent_id, event.action_id),
                ).fetchone()["s"]
                if (newest or 0) != expected_seq:
                    return False
                self._insert_level(event)
            return True

        return self._retrying(attempt)

    def _labels_where(self, where: str, params: tuple) -> list[Label]:
        """`where` is fixed SQL text from this module; values always go through `params`."""
        query = sql.SQL("SELECT {} FROM labels l {} ORDER BY l.seq").format(
            sql.SQL(self._LABEL_COLS), sql.SQL(where)
        )
        with self._lock:
            rows = self._exec(query, params).fetchall()
        return [Label.model_validate(r) for r in rows]

    def list_labels(self, run_id: str) -> list[Label]:
        return self._labels_where("WHERE l.run_id = %s", (run_id,))

    def list_labels_for(self, agent_id: str, action_id: str, since: datetime | None) -> list[Label]:
        join = "JOIN plans p ON p.run_id = l.run_id WHERE p.agent_id = %s AND p.action_id = %s"
        if since is None:
            return self._labels_where(join, (agent_id, action_id))
        return self._labels_where(join + " AND l.created_at >= %s", (agent_id, action_id, since))

    def count_proposals(self, agent_id: str, action_id: str, since: datetime | None) -> int:
        query = "SELECT count(*) AS n FROM plans WHERE agent_id = %s AND action_id = %s"
        params: tuple = (agent_id, action_id)
        if since is not None:
            query, params = query + " AND created_at >= %s", (*params, since)
        with self._lock:
            return int(self._exec(query, params).fetchone()["n"])

    def current_overrides(self) -> dict[tuple[str, str], str]:
        with self._lock:
            rows = self._exec(
                "SELECT DISTINCT ON (agent_id, action_id) agent_id, action_id, kind "
                "FROM level_events ORDER BY agent_id, action_id, seq DESC"
            ).fetchall()
        return {(r["agent_id"], r["action_id"]): "shadow" for r in rows if r["kind"] == "demote"}

    def held_run_ids(self) -> set[str]:
        with self._lock:
            rows = self._exec(
                "SELECT DISTINCT run_id FROM labels WHERE label IN ('wrong', 'harmful', 'missed')"
            ).fetchall()
        return {r["run_id"] for r in rows}

    def put_report(self, week: date, body: str) -> bool:
        with self._lock:
            row = self._exec(
                "INSERT INTO reports (week_start, body_md, created_at) VALUES (%s, %s, %s) "
                "ON CONFLICT (week_start) DO NOTHING RETURNING week_start",
                (week, body, now()),
            ).fetchone()
        return row is not None

    def get_report(self, week: date) -> str | None:
        with self._lock:
            row = self._exec(
                "SELECT body_md FROM reports WHERE week_start = %s", (week,)
            ).fetchone()
        return row["body_md"] if row else None

    def pilot_week(self, week: date) -> PilotWeek:
        with self._lock:
            row = self._exec("SELECT * FROM v_pilot_week WHERE week = %s", (week,)).fetchone()
        return PilotWeek.model_validate(row) if row else PilotWeek(week=week)

    def approval_week(self, week: date) -> ApprovalWeek:
        with self._lock:
            row = self._exec("SELECT * FROM v_approval_week WHERE week = %s", (week,)).fetchone()
        return ApprovalWeek.model_validate(row) if row else ApprovalWeek(week=week)
