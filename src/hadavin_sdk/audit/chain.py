"""`chain` audit: an append-only hash chain in the store's database, with signed checkpoints and anchors.

Ported from WARDEN `audit.py` (main c78d7709): `_Store`, `AuditLog`, `_hash`, `_signed_message`, `verify` and its
checks, and the append-only `_PG_SCHEMA` pattern (here `store/migrations/0002_audit_chain.sql`). Edits: the
message prefix is `hadavin-audit`; rows are AuditEvents (hashes and codes only) and the AuditSink Protocol sits on
top; the signer and anchor come from the backend table; a checkpoint that cannot be signed or anchored is
logged and retried, never raised (signing is evidence, not a gate: design 4.8).

Three layers, because each one alone is beatable:
* **Append-only.** Triggers abort any UPDATE, DELETE or TRUNCATE. Anyone who can write the database can drop a
  trigger, so this is a guard rail, not proof.
* **Hash chain.** Each row's hash covers the previous row's hash and all of its own fields, so an edited,
  removed or reordered row breaks every link after it.
* **Signed checkpoints** every `checkpoint_every` rows, over `hadavin-audit:{seq}:{head}`. Someone who edits a
  row AND recomputes every later hash cannot recompute the signature; someone who also holds the key cannot
  rewrite the anchors (S3 Object Lock, written by another principal).

Honest limits: rows after the last checkpoint are chained but not yet signed (`verify` reports the tail). On
the `memory` store the chain is an in-memory SQLite database and is lost on restart, like the store.

Neutral protocol: SQL in the configured store (Postgres or the in-memory SQLite), signed with whichever signer is set.
"""

from __future__ import annotations

import contextlib
import hashlib
import inspect
import json
import logging
import re
import sqlite3
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from hadavin_sdk import defaults
from hadavin_sdk.audit import anchors
from hadavin_sdk.audit.protocol import AuditUnavailable, DuplicateEvent
from hadavin_sdk.audit.signer import Alg, Signer, verify_signature
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.store.protocol import StoreUnavailable

GENESIS = "0" * 64
_LOG = logging.getLogger("hadavin_sdk.audit.chain")
# One chain, many writers: each append holds this transaction-scoped advisory lock (a fixed key).
_PG_LOCK = int.from_bytes(b"hadvnaud", "big") >> 1

_SQLITE_SCHEMA = """
CREATE TABLE audit_entries (seq INTEGER PRIMARY KEY, at TEXT NOT NULL, run_id TEXT NOT NULL,
    kind TEXT NOT NULL, body TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL,
    event_id TEXT NOT NULL UNIQUE);
CREATE TABLE audit_checkpoints (seq INTEGER PRIMARY KEY, hash TEXT NOT NULL, signature TEXT NOT NULL,
    alg TEXT, key_label TEXT);
CREATE TABLE audit_outbox (event_id TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE INDEX audit_entries_by_run ON audit_entries (run_id, seq);
""" + "".join(
    f"CREATE TRIGGER {t}_no_{op.lower()} BEFORE {op} ON {t} "
    "BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;\n"
    for t in ("audit_entries", "audit_checkpoints")
    for op in ("UPDATE", "DELETE")
)
_TABLE_NAME = re.compile(r"\b(audit_entries|audit_checkpoints|audit_outbox)\b")
_ALL_ROWS = (
    "SELECT seq, at, run_id, kind, body, prev, hash, event_id FROM audit_entries ORDER BY seq"
)


def _hash(prev: str, seq: int, at: str, run_id: str, kind: str, body: str) -> str:
    material = json.dumps(
        [prev, seq, at, run_id, kind, body], ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _driver_names(exc: BaseException) -> set[str]:
    return {c.__name__ for c in type(exc).__mro__ if c.__module__.startswith("psycopg")}


def _is_outage(exc: BaseException) -> bool:
    """True only for "the database cannot be reached right now": OSError, StoreUnavailable, a psycopg
    InterfaceError, or a psycopg OperationalError with no SQLSTATE or one of class 08 (connection) or 57P
    (operator shutdown). Used where an outage stays quiet (reading the outbox). No driver import: psycopg errors
    are recognised by class name along the MRO."""
    if isinstance(exc, StoreUnavailable | OSError):
        return True
    names = _driver_names(exc)
    if "InterfaceError" in names:
        return True
    if "OperationalError" in names:
        state = getattr(exc, "sqlstate", None)
        return state is None or state.startswith(("08", "57P"))
    return False


def _is_permanent(exc: BaseException) -> bool:
    """True only for the KNOWN permanent refusals: SQLSTATE class 22 (data) or 23 (integrity), 42501 (missing
    grant), 54000 (limit exceeded), a psycopg DataError or IntegrityError without a SQLSTATE, and local data
    errors (ValueError, TypeError, sqlite3 data, integrity and programming errors). EVERY other psycopg or OS
    error is transient (timeouts 57014 and 55P03, 40001, 40P01, 53300, 25006, class 08, 57P): the event stays in
    the retry set. An error of NO known kind (not a database, OS or local data error) is NOT permanent: it is
    treated as transient and reported by name (`_is_unclassified`), so a bug in a wrapped connection never
    quarantines a row that could be written."""
    if isinstance(exc, StoreUnavailable | OSError):
        return False
    names = _driver_names(exc)
    if names:
        state = getattr(exc, "sqlstate", None)
        if isinstance(state, str):
            return state.startswith(defaults.AUDIT_PERMANENT_SQLSTATES)
        return bool(names & {"DataError", "IntegrityError"})
    return isinstance(exc, ValueError | TypeError | sqlite3.Error) and not isinstance(
        exc, sqlite3.OperationalError
    )


def _is_unclassified(exc: BaseException) -> bool:
    """True for an exception that is neither a known permanent refusal nor a known transient database or OS error
    (an AttributeError or RuntimeError from a wrapped connection, say). It is retried like a transient error and
    fails the reconcile step with its own text."""
    if _is_permanent(exc) or _is_outage(exc) or _driver_names(exc):
        return False
    return not isinstance(exc, sqlite3.OperationalError)


def _sort_ts(event: AuditEvent) -> datetime:
    """The ordering instant of an event: a naive `ts` is read as UTC (it would otherwise raise in the comparison
    with an aware one); only the order uses this, the event keeps its own `ts`."""
    return event.ts if event.ts.tzinfo is not None else event.ts.replace(tzinfo=UTC)


def _takes_meta(put: Callable) -> bool:
    params = inspect.signature(put).parameters.values()
    names = {p.name for p in params}
    return any(p.kind is p.VAR_KEYWORD for p in params) or {"alg", "key_label"} <= names


def signer_label(signer: Signer) -> str:
    """The non-secret name written beside each checkpoint and anchor. The operator's `key_label` setting when
    set, else a fingerprint of the PUBLIC key: the same key gets the same label whether it was configured by
    alias, ARN or URL, and the label never holds an account id."""
    label = getattr(signer, "key_label", None)
    return label or "pk:" + hashlib.sha256(signer.public_key()).hexdigest()[:16]


def _signed_message(seq: int, head: str) -> bytes:
    return f"hadavin-audit:{seq}:{head}".encode()


class _Db:
    """The few statements the chain runs, on SQLite (the `memory` store) or the `postgres` store's connection.
    One lock per connection: on postgres it is the store's own, so no store statement lands inside an audit
    transaction (WARDEN 2026-10-15: a read inside another thread's BEGIN ... COMMIT failed CI twice)."""

    def __init__(self, conn: Any, lock: Any, pg: bool, schema: str | None = None) -> None:
        self.conn, self.lock, self.pg = conn, lock, pg
        # Postgres only: every statement names this schema (an unqualified name is looked up in the session's
        # temporary schema first, so a temporary table of that name would shadow the real one).
        self.schema = schema

    @classmethod
    def memory(cls) -> _Db:
        conn = sqlite3.connect(":memory:", isolation_level=None, check_same_thread=False)
        conn.executescript(_SQLITE_SCHEMA)
        return cls(conn, threading.Lock(), pg=False)

    def _t(self, sql: str) -> str:
        """The statement with the three audit table names qualified by the schema (postgres kind only)."""
        if not self.pg:
            return sql
        if (
            not self.schema
        ):  # a caller that gave none: resolved once (current_schema() never answers pg_temp)
            self.schema = self.conn.execute("SELECT current_schema()").fetchone()[0]
            if not self.schema:
                raise ConfigError("audit chain: the search_path names no schema that exists")
        quoted = '"' + self.schema.replace('"', '""') + '"'
        return _TABLE_NAME.sub(lambda m: f"{quoted}.{m.group(1)}", sql.replace("?", "%s"))

    def _q(self, sql: str, params: tuple = ()) -> list[tuple]:
        cur = self.conn.execute(self._t(sql), params)
        return cur.fetchall() if cur.description else []

    def run(self, sql: str, params: tuple = ()) -> list[tuple]:
        with self.lock:
            return self._q(sql, params)

    @contextlib.contextmanager
    def transaction(self) -> Iterator[Callable[..., list[tuple]]]:
        with self.lock:
            if self.pg:
                with self.conn.transaction():
                    self.conn.execute("SELECT pg_advisory_xact_lock(%s)", (_PG_LOCK,))
                    yield self._q
                return
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._q
                self.conn.execute("COMMIT")
            finally:
                # Only a transaction still open is rolled back: a ROLLBACK with none raised "no transaction is
                # active" over the error that ended it (WARDEN, Sonar python:S9152).
                if self.conn.in_transaction:
                    self.conn.execute("ROLLBACK")


@dataclass
class _Pass:
    done: int = 0
    unreadable: int = 0
    not_writable: int = 0
    deferred: int = 0
    unclassified: int = 0
    not_deleted: int = 0
    marked: int = 0
    select_error: Exception | None = None


@dataclass
class Verification:
    rows: int = 0
    signed_through: int = 0
    problems: list[str] = field(default_factory=list)
    unreadable: bool = (
        False  # the audit or its anchors could not be read: not checked, not "tampered"
    )

    @property
    def ok(self) -> bool:
        return not self.problems

    @property
    def unsigned_tail(self) -> int:
        return self.rows - self.signed_through


# A ts is cast to timestamptz only when it is a real calendar value (a shape check alone lets 2026-02-30 through; no `?` here: the placeholder translation would rewrite it and
# the cast then raises, which would block every batch read). Month-specific day ranges; 29 February only in a
# leap year (divisible by 4, a century only when divisible by 400; any other such row sorts last, never an error). Hours 00-23, minutes and seconds 00-59, offset hours 00-15.
_LEAP2 = "(0[48]|[2468][048]|[13579][26])"
_TS_SHAPE = (
    "^((000[1-9]|00[1-9][0-9]|0[1-9][0-9]{2}|[1-9][0-9]{3})-("
    "(0[13578]|1[02])-(0[1-9]|[12][0-9]|3[01])|"
    "(0[469]|11)-(0[1-9]|[12][0-9]|30)|"
    "02-(0[1-9]|1[0-9]|2[0-8]))|"
    f"([0-9]{{2}}{_LEAP2}|{_LEAP2}00)-02-29)"
    "[T ]([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    "(\\.[0-9]{1,9}){0,1}"
    "(Z|[+-](0[0-9]|1[0-5])(:{0,1}[0-5][0-9]){0,1}){0,1}$"
)


class ChainAudit:
    """The AuditSink Protocol over the chain, plus `checkpoint()` (inline every N rows, and from `tick`) and
    `verify()`. Keys returned by the writes are event ids."""

    def __init__(
        self,
        db: _Db,
        signer: Signer | None = None,
        anchor: Any = None,
        checkpoint_every: int = 100,
        drain_batch: int | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._db, self.signer, self.anchor = db, signer, anchor
        # A custom anchor kind written before alg and key_label existed takes three arguments: it still works (its
        # objects just lack the two fields) and is logged once, instead of failing every put with a TypeError.
        self._anchor_takes_meta = not hasattr(anchor, "put") or _takes_meta(anchor.put)
        if not self._anchor_takes_meta:
            _LOG.warning(
                "audit anchor put() takes no alg/key_label: its objects will not verify offline"
            )
        self.checkpoint_every = checkpoint_every
        self.drain_batch = drain_batch if drain_batch is not None else defaults.AUDIT_DRAIN_BATCH
        self._sleep = sleep
        self._clock = clock
        # Last resort when even the outbox table cannot be written (the database is down): drained by the next
        # successful write of this process and by reconcile. In-process only: lost if the process exits first.
        self._pending: list[AuditEvent] = []
        self._flush_lock = threading.Lock()  # one drainer of _pending at a time
        # Parked events the database refused for a reason other than an outage: moved here by the flush so
        # they do not block the ones after them. In-process only, retried once per reconcile: lost when the process exits.
        self._unwritable: list[AuditEvent] = []
        # True after this process wrote an outbox row: the next write drains the outbox first (ordering).
        self._outbox_dirty = False
        # The last flush stopped at a transient error that is not an outage (timeout, lock wait): reconcile says so.
        self._transient_stuck = False
        # Checkpoints whose anchor put failed: retried by the next checkpoint() (ponytail: in-process only; a
        # restart drops the list and `verify` then reports "never anchored", which is the truth).
        self._unanchored: dict[int, tuple[str, str]] = {}

    # --- AuditSink ----------------------------------------------------------------------------------

    def _append(self, event: AuditEvent) -> str:
        body = event.model_dump_json()
        at = event.ts.astimezone(UTC).isoformat(timespec="microseconds")
        kind = f"{event.domain}.{event.operation}"
        with self._db.transaction() as q:
            if q("SELECT 1 FROM audit_entries WHERE event_id = ?", (event.event_id,)):
                raise DuplicateEvent(event.event_id)
            last = q("SELECT seq, hash FROM audit_entries ORDER BY seq DESC LIMIT 1")
            seq, prev = (last[0][0] + 1, last[0][1]) if last else (1, GENESIS)
            q(
                "INSERT INTO audit_entries (seq, at, run_id, kind, body, prev, hash, event_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    seq,
                    at,
                    event.run_id,
                    kind,
                    body,
                    prev,
                    _hash(prev, seq, at, event.run_id, kind, body),
                    event.event_id,
                ),
            )
        if self.signer is not None and seq % self.checkpoint_every == 0:
            self.checkpoint()
        return event.event_id

    def write_intent(self, event: AuditEvent) -> str:
        self._drain_older_first()
        try:
            key = self._append(event)
        except DuplicateEvent:
            raise
        except Exception as exc:
            raise AuditUnavailable(f"intent {event.event_id}: {exc.__class__.__name__}") from exc
        if self._pending:  # the chain just answered: write what this process parked in memory
            self._flush_pending()
        return key

    def write_outcome(self, event: AuditEvent) -> str | None:
        """Never raises: the chain, then the outbox table, then memory (all drained by reconcile)."""
        self._drain_older_first()
        try:
            key = self._append(event)
        except DuplicateEvent:
            return event.event_id
        except Exception:  # noqa: BLE001 - the contract is "never raises"
            try:
                self._db.run(
                    "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?) "
                    "ON CONFLICT (event_id) DO NOTHING",
                    (event.event_id, event.model_dump_json()),
                )
                self._outbox_dirty = True
            except Exception:  # noqa: BLE001
                self._pending.append(event)
            return None
        if self._pending:  # only after a successful append, never after a failed one
            self._flush_pending()
        return key

    def _drain_older_first(self) -> None:
        """A newer event must not overtake an older one this process parked in the outbox table: before the append,
        one bounded drain pass puts the parked rows in the chain first. Best effort, never raises: if the older
        rows are still refused for a transient reason the new event is written anyway (an intent must not wait on a
        sick outbox); their own `ts` still shows the order, and the next tick reconciles by ts."""
        if not self._outbox_dirty:
            return
        try:
            self._drain_pass(retry_refused=False)
        except Exception as exc:  # noqa: BLE001
            _LOG.warning(
                "audit outbox pre-drain failed (%s); retried next time", type(exc).__name__
            )

    def _flush_pending(self) -> int:
        """Write the events parked in memory, oldest first. A TRANSIENT failure (an outage, a timeout, a lock wait,
        a deadlock: anything not known to be permanent) stops the flush at that event: it and the ones after it
        stay in `_pending`, in order, and the next append or reconcile retries them. An event the database
        refuses for a PERMANENT reason (`_is_permanent`) is moved to `_unwritable` (kept in memory, counted in one
        warning) so it cannot block the events after it. Returns how many were written. Never raises."""
        done = aside = 0
        try:
            with self._flush_lock:
                while self._pending:
                    failed = self._drain_with_backoff(self._pending[0])
                    if failed is not None and not _is_permanent(failed):
                        _LOG.warning(
                            "audit pending flush: event stays parked after %d attempts (%s), total=%d",
                            defaults.AUDIT_FLUSH_ATTEMPTS,
                            type(failed).__name__,
                            len(self._pending),
                        )
                        self._transient_stuck = not _is_outage(failed)
                        break
                    event = self._pending.pop(
                        0
                    )  # only the lock holder removes; other threads only append
                    if failed is None:
                        done += 1
                    else:
                        self._unwritable.append(event)
                        aside += 1
                else:
                    self._transient_stuck = False
        except Exception as exc:  # noqa: BLE001 - a flush failure is never the caller's error
            _LOG.warning("audit pending flush stopped (%s); retried next time", type(exc).__name__)
        if aside:
            _LOG.warning(
                "audit pending flush: written=%d not_writable=%d (kept in memory, total=%d)",
                done,
                aside,
                len(self._unwritable),
            )
        return done

    def _drain_with_backoff(self, event: AuditEvent) -> Exception | None:
        """`_drain` with up to AUDIT_FLUSH_ATTEMPTS tries on a TRANSIENT failure, sleeping AUDIT_FLUSH_BACKOFF_S
        doubling, capped at AUDIT_FLUSH_BACKOFF_MAX_S. A permanent failure is returned at once. Returns the last
        failure; the caller keeps the event parked."""
        delay = defaults.AUDIT_FLUSH_BACKOFF_S
        failed = None
        for attempt in range(defaults.AUDIT_FLUSH_ATTEMPTS):
            failed = self._drain(event)
            if failed is None or _is_permanent(failed):
                return failed
            if attempt + 1 < defaults.AUDIT_FLUSH_ATTEMPTS:
                self._sleep(min(delay, defaults.AUDIT_FLUSH_BACKOFF_MAX_S))
                delay *= 2
        return failed

    def reconcile(self) -> int:
        """Write parked events to the chain; returns how many. Memory events and the outbox rows of this tick
        (at most `defaults.AUDIT_DRAIN_BATCH`, oldest first) are merged into ONE order: `event.ts`, then
        `event_id`. An outbox row is deleted only after its event is in the chain. The call raises with counts only
        when something needs the operator: an unreadable row; a poison row (a PERMANENT refusal, see
        `_is_permanent`), which is moved to the quarantine id prefix and counted every tick until an operator
        removes it (handover tickets/A-audit-drain.md); a row or memory event still refused for a transient
        reason that is not an outage (timeout, lock wait); a failed delete. A plain outage (database unreachable)
        is quiet: retried next time. Reading the outbox fails the step for every error except an outage."""
        r = self._drain_pass(tick=True)
        if r.select_error is not None:
            if _is_outage(r.select_error):
                return r.done  # the database is still down: retried next time
            raise RuntimeError(f"audit outbox: read failed ({type(r.select_error).__name__})")
        earlier = 0
        with contextlib.suppress(Exception):  # the count is a report, not a gate
            total = self._db.run(
                "SELECT COUNT(*) FROM audit_outbox WHERE event_id LIKE ?",
                (defaults.AUDIT_QUARANTINE_PREFIX + "%",),
            )
            earlier = max(0, int(total[0][0]) - r.marked)
        in_memory = len(self._unwritable) + (len(self._pending) if self._transient_stuck else 0)
        quarantine_text = (
            f"{earlier} poison rows quarantined earlier (event_id prefix "
            f"{defaults.AUDIT_QUARANTINE_PREFIX!r}; operator removal: tickets/A-audit-drain.md)"
        )
        deferred_text = f"{r.deferred} rows refused for a transient error, retried next tick"
        problems = [
            text
            for count, text in (
                (r.unreadable, f"{r.unreadable} unreadable rows kept"),
                (r.not_writable, f"{r.not_writable} rows not writable"),
                (earlier, quarantine_text),
                (r.deferred, deferred_text),
                (
                    r.unclassified,
                    f"{r.unclassified} items refused for an unclassified error (retried, not quarantined)",
                ),
                (r.not_deleted, f"{r.not_deleted} rows not deleted"),
                (in_memory, f"{in_memory} events not writable in memory"),
            )
            if count
        ]
        if problems:
            _LOG.warning(
                "audit outbox: drained=%d unreadable=%d not_writable=%d not_deleted=%d (kept) "
                "quarantined_now=%d quarantined_earlier=%d deferred=%d",
                r.done,
                r.unreadable,
                r.not_writable,
                r.not_deleted,
                r.marked,
                earlier,
                r.deferred,
            )
            raise RuntimeError("audit outbox: " + ", ".join(problems))
        return r.done

    def _outbox_sql(self) -> str:
        """The read of one batch, oldest `ts` first (the body is text and `ts` is its ISO timestamp: a row whose body
        is not JSON has no `ts` and sorts last, it is never a reason for the read to fail)."""
        # The text ts is normalised before it sorts: a fraction-less ts sorts after a fractional one as text, and
        # an offset other than Z sorts by its wall clock. PostgreSQL casts to timestamptz (only a well-formed ISO
        # value is cast: a malformed one is NULL, never an error; a ts without an offset is read as UTC, the session
        # time zone is pinned); SQLite uses julianday, which reads offsets and fractions and returns NULL otherwise.
        ts = (
            'CASE WHEN substring(body from \'"ts":"([^"]*)"\') ~ '
            f"'{_TS_SHAPE}' "
            'THEN (substring(body from \'"ts":"([^"]*)"\'))::timestamptz END'
            if self._db.pg
            else "CASE WHEN json_valid(body) THEN julianday(json_extract(body, '$.ts')) END"
        )
        return (
            "SELECT event_id, body FROM audit_outbox WHERE event_id NOT LIKE ? "  # noqa: S608 - ts is a constant
            f"ORDER BY ({ts} IS NULL), {ts}, event_id LIMIT ? OFFSET ?"
        )

    def _drain_pass(self, retry_refused: bool = True, tick: bool = False) -> _Pass:
        """One bounded drain pass: parked memory events and one batch of outbox rows, merged and sorted by
        (ts, event_id). Holds the flush lock. Never raises: a failed read is returned in `select_error`."""
        r = _Pass()
        with self._flush_lock:
            # Events refused earlier go back in front of the queue: one retry per pass.
            if retry_refused:
                self._pending[:0], self._unwritable = self._unwritable, []
            items: list[tuple[AuditEvent, str | None]] = [(e, None) for e in self._pending]
            # Rows that are not readable never use a slot of the batch: the read pages on until it holds
            # `AUDIT_DRAIN_BATCH` readable rows or the table is exhausted.
            seen = good = 0
            while good < self.drain_batch:
                want = self.drain_batch - good
                try:
                    page = self._db.run(
                        self._outbox_sql(), (defaults.AUDIT_QUARANTINE_PREFIX + "%", want, seen)
                    )
                except Exception as exc:  # noqa: BLE001
                    r.select_error = exc
                    break
                seen += len(page)
                for event_id, body in page:
                    try:
                        event = AuditEvent.model_validate_json(body)
                    except ValueError:
                        r.unreadable += 1
                        continue
                    if event.event_id != event_id:
                        r.unreadable += 1
                        continue
                    items.append((event, event_id))
                    good += 1
                if len(page) < want:
                    break
            items.sort(key=lambda it: (_sort_ts(it[0]), it[0].event_id))
            for event, row_id in items:
                if self._drain_item(event, row_id, r, tick):
                    break  # a transient refusal stops the pass: nothing newer is written past it
            if r.select_error is None and not seen:
                self._outbox_dirty = False
        return r

    def _drain_item(
        self, event: AuditEvent, row_id: str | None, r: _Pass, tick: bool = False
    ) -> bool:
        """Drain one item. True when the pass must stop here (a transient refusal)."""
        failed = self._drain(event)
        if failed is None:
            if row_id is None:
                self._pending.remove(event)
            else:
                try:
                    self._db.run("DELETE FROM audit_outbox WHERE event_id = ?", (row_id,))
                except Exception:  # noqa: BLE001 - in the chain; the next drain dedupes and deletes
                    r.not_deleted += 1
                    return False
            r.done += 1
            return False
        if _is_permanent(failed):
            if row_id is None:
                self._pending.remove(event)
                self._unwritable.append(event)
            else:
                r.not_writable += 1
                # A missing grant (42501) is mended by the operator and then every row drains: no quarantine.
                if getattr(failed, "sqlstate", None) != "42501" and tick:
                    # Age from the row's own ts (stable across processes: a tick is one process); naive = UTC.
                    age = (self._clock() - _sort_ts(event)).total_seconds()
                    if age >= defaults.AUDIT_QUARANTINE_AFTER_S:
                        r.marked += self._quarantine(event, row_id)
            return False
        if row_id is None:
            self._transient_stuck = not _is_outage(failed)
        elif not _is_outage(failed):
            r.deferred += 1
        if _is_unclassified(failed):
            r.unclassified += 1
        return True

    def _quarantine(self, event: AuditEvent, row_id: str) -> int:
        """Mark a poison row: kept in the outbox under the quarantine prefix, skipped by every later read."""
        try:
            self._db.run(
                "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?) ON CONFLICT (event_id) DO NOTHING",
                (defaults.AUDIT_QUARANTINE_PREFIX + row_id, event.model_dump_json()),
            )
            self._db.run("DELETE FROM audit_outbox WHERE event_id = ?", (row_id,))
        except Exception:  # noqa: BLE001
            return 0
        return 1

    def _drain(self, event: AuditEvent) -> Exception | None:
        """Append one parked event. None when it is in the chain (now or already); else the exception, for the
        caller to tell an outage from a refusal."""
        try:
            self._append(event)
        except DuplicateEvent:
            return None
        except Exception as exc:  # noqa: BLE001 - stays parked; the caller decides what the reason means
            return exc
        return None

    def verify_object(self, key: str) -> bool:
        """The event's row holds its own content's hash and links to the row before it, which holds its own."""
        found = self._db.run("SELECT seq FROM audit_entries WHERE event_id = ?", (key,))
        if not found:
            return False
        s = found[0][0]
        rows = self._db.run(
            "SELECT seq, at, run_id, kind, body, prev, hash FROM audit_entries "
            "WHERE seq IN (?, ?) ORDER BY seq",
            (s - 1, s),
        )
        by = {r[0]: r for r in rows}
        row, before = by.get(s), by.get(s - 1)
        if row is None or (s > 1 and before is None):
            return False
        prev = before[6] if before else GENESIS
        return (
            row[5] == prev
            and _hash(row[5], *row[:5]) == row[6]
            and (before is None or _hash(before[5], *before[:5]) == before[6])
        )

    def events(self, run_id: str | None = None) -> list[AuditEvent]:
        if run_id is None:
            rows = self._db.run("SELECT body FROM audit_entries ORDER BY seq")
        else:
            rows = self._db.run(
                "SELECT body FROM audit_entries WHERE run_id = ? ORDER BY seq", (run_id,)
            )
        return [AuditEvent.model_validate_json(body) for (body,) in rows]

    # --- checkpoints and verification ---------------------------------------------------------------

    def signed_through(self) -> int:
        """The last row a checkpoint covers (0 when none does)."""
        top = self._db.run("SELECT MAX(seq) FROM audit_checkpoints")
        return int(top[0][0]) if top and top[0][0] is not None else 0

    def checkpoint(self) -> int | None:
        """Sign the current head (once) and anchor it. Returns the head's seq, or None when there is nothing to
        sign, no signer, or the signing failed. Never raises: a failure is logged by its kind only and the next
        call retries; the chain itself is untouched."""
        if self.signer is None:
            return None
        try:
            self._retry_anchors()
            last = self._db.run("SELECT seq, hash FROM audit_entries ORDER BY seq DESC LIMIT 1")
            if not last:
                return None
            seq, head = last[0]
            if self.signed_through() >= seq:
                return seq
            signature = self.signer.sign(_signed_message(seq, head)).hex()
            new = self._db.run(
                "INSERT INTO audit_checkpoints (seq, hash, signature, alg, key_label) "
                "VALUES (?, ?, ?, ?, ?) ON CONFLICT (seq) DO NOTHING RETURNING seq",
                (seq, head, signature, self.signer.alg, signer_label(self.signer)),
            )
        except Exception as exc:  # noqa: BLE001 - evidence, not a gate (design 4.8)
            _LOG.error("audit checkpoint not signed (%s); retried next time", type(exc).__name__)
            return None
        if new and self.anchor is not None:
            self._anchor(seq, head, signature)
        return seq

    def _anchor(self, seq: int, head: str, signature: str) -> None:
        try:
            if self._anchor_takes_meta:
                self.anchor.put(
                    seq, head, signature, alg=self.signer.alg, key_label=signer_label(self.signer)
                )
            else:
                self.anchor.put(seq, head, signature)
        except Exception as exc:  # noqa: BLE001 - an anchor outage must not stop the recording
            _LOG.error(
                "audit checkpoint %s not anchored (%s); retried next time", seq, type(exc).__name__
            )
            self._unanchored[seq] = (head, signature)
        else:
            self._unanchored.pop(seq, None)

    def _retry_anchors(self) -> None:
        for seq, (head, signature) in sorted(self._unanchored.items()):
            self._anchor(seq, head, signature)

    def verify(self) -> Verification:
        """Recompute the whole chain, check every checkpoint signature and, with an anchor, every anchor. Never
        raises: damage or an unreachable store is a finding."""
        try:
            rows = self._db.run(_ALL_ROWS)
            stored = self._db.run(
                "SELECT seq, hash, signature, alg FROM audit_checkpoints ORDER BY seq"
            )
            checkpoints = [row[:3] for row in stored]
            row_algs = {row[0]: row[3] for row in stored if row[3]}
            public = self.signer.public_key() if self.signer is not None else None
            anchors = self.anchor.all() if self.anchor is not None else None
        except Exception as exc:  # noqa: BLE001
            # The class only: driver messages can carry the host and user.
            return Verification(
                problems=[f"the audit cannot be read ({type(exc).__name__})"], unreadable=True
            )
        alg = self.signer.alg if self.signer is not None else "ed25519"
        return verify_rows(rows, checkpoints, public, anchors, alg, row_algs)


def verify_rows(
    rows: list,
    checkpoints: list,
    public_key: bytes | None,
    anchors: dict[int, tuple[str, str]] | None = None,
    alg: Alg = "ed25519",
    row_algs: dict[int, str] | None = None,
) -> Verification:
    """Rows and checkpoints as read from the tables, in seq order. With `anchors`, every checkpoint must also
    match the copy written out of reach when it was made. `row_algs` is the scheme each checkpoint row recorded
    (seq -> alg); a row without one (written before 0004, or by an older runtime) is checked with `alg`."""
    result = Verification(rows=len(rows))
    hashes = _check_chain(rows, result.problems)
    if public_key is None:
        if checkpoints:
            result.problems.append("checkpoints exist but no signer is configured to check them")
    else:
        _check_checkpoints(checkpoints, hashes, public_key, result, alg, row_algs or {})
    if anchors is not None:
        _check_anchors(checkpoints, anchors, result.problems)
    return result


def _check_chain(rows: list, problems: list[str]) -> dict[int, str]:
    hashes: dict[int, str] = {}
    prev = GENESIS
    for expected, row in enumerate(rows, 1):
        seq, at, run_id, kind, body, stored_prev, stored_hash, event_id = row
        if seq != expected:
            problems.append(f"row {expected} is missing (next row is {seq})")
        if stored_prev != prev:
            problems.append(f"row {seq} does not link to the row before it")
        if _hash(stored_prev, seq, at, run_id, kind, body) != stored_hash:
            problems.append(f"row {seq} was changed after it was written")
        elif _body_event_id(body) != event_id:
            # The event_id column is outside the hash (it is the dedupe index); the body inside it names
            # the event, so a changed column (pointing verify_object or a dedupe elsewhere) is caught here.
            problems.append(f"row {seq} event id column does not match its body")
        hashes[seq] = stored_hash
        prev = stored_hash
    return hashes


def _body_event_id(body: str) -> str | None:
    try:
        return json.loads(body).get("event_id")
    except (ValueError, AttributeError):
        return None


def _check_checkpoints(
    checkpoints: list,
    hashes: dict[int, str],
    public_key: bytes,
    result: Verification,
    alg: Alg = "ed25519",
    row_algs: dict[int, str] | None = None,
) -> None:
    for seq, head, signature in checkpoints:
        try:
            raw = bytes.fromhex(signature)
        except ValueError:
            raw = b""
        if not verify_signature(
            public_key,
            raw,
            _signed_message(seq, head),
            (row_algs or {}).get(seq, alg),  # type: ignore[arg-type]
        ):
            result.problems.append(f"checkpoint {seq} has an invalid signature")
            continue
        if hashes.get(seq) != head:
            result.problems.append(f"checkpoint {seq} was signed over a different history")
            continue
        result.signed_through = max(result.signed_through, seq)


def _check_anchors(
    checkpoints: list, anchors: dict[int, tuple[str, str]], problems: list[str]
) -> None:
    stored = {seq: (head, signature) for seq, head, signature in checkpoints}
    for seq, pair in sorted(stored.items()):
        if seq not in anchors:
            problems.append(f"checkpoint {seq} was never anchored")
        elif anchors[seq] != pair:
            problems.append(f"checkpoint {seq} differs from its anchor: the history was rewritten")
    for seq in sorted(set(anchors) - set(stored)):
        problems.append(f"anchor {seq} has no checkpoint here: the database lost history")


def verify_anchor_bodies(
    bodies: list[bytes],
    public_key: bytes,
    names: list[str] | None = None,
    assume_alg: Alg | None = None,
) -> list[str]:
    """Offline: check the anchor objects alone against a public key. The scheme and key label come from each
    body (`alg`, `key_label`), so nothing else has to be known. A body from the previous build holds `key_id`
    (possibly an ARN): it is accepted but never compared or printed, so an upgraded chain with old and new
    anchors is not a finding and no account id reaches the report.

    `names` (the object names exactly as listed, e.g. `anchors/000000000002.json`, same order as `bodies`): each
    must be `anchors.key(seq)` for the body's own seq, so an object copied under another name is a finding.

    Legacy anchors (written before `alg` existed) cannot say how they were signed. Upgrade path, no rewrite of
    the immutable objects: pass `assume_alg` (the scheme of the key that was configured then). The signature
    check against the public key is then the proof: a wrong guess fails every signature, never passes. Such a
    body has no label, so the different-keys check skips it."""
    if not bodies:
        return ["no anchor objects given: nothing was verified"]
    if names is not None and len(names) != len(bodies):
        return ["names and bodies differ in length: nothing was verified"]
    problems = []
    labels = set()
    seqs: set[int] = set()
    for i, raw in enumerate(bodies):
        try:
            a = json.loads(raw)
            seq, head = a["seq"], a["hash"]
            alg = a.get("alg") or assume_alg
            label = a.get("key_label")
            if type(seq) is not int or seq < 1 or alg is None:
                raise TypeError("seq or alg")
            if label is not None:
                if not isinstance(label, str) or not label:
                    raise TypeError("label")
                labels.add(label)
            elif (
                "alg" in a and "key_id" not in a
            ):  # a current body names its key; a legacy one has `key_id`
                raise TypeError("label")
            signature = bytes.fromhex(a["signature"])
        except (ValueError, KeyError, TypeError, AttributeError):
            problems.append(
                "an anchor body is unreadable or has no alg and key label "
                "(a pre-alg anchor: pass assume_alg)"
            )
            continue
        if names is not None and names[i] != anchors.key(seq):
            problems.append(f"anchor object {names[i]!r} holds seq {seq}: the name does not match")
        if seq in seqs:
            problems.append(f"anchor {seq} appears twice")
        seqs.add(seq)
        if not verify_signature(public_key, signature, _signed_message(seq, head), alg):
            problems.append(f"anchor {seq} has an invalid signature")
    if len(labels) > 1:
        problems.append(
            f"anchors report {len(labels)} different key labels: {sorted(labels)} (a relabelled or rotated key)"
        )
    return problems


# --------------------------------------------------------------------------- table factory


def build(settings, deps) -> ChainAudit:
    """`backends.audit: {kind: chain, checkpoint_every, anchor}`, in the store's database."""
    from hadavin_sdk.store.memory import MemoryStore

    store = deps.store
    if isinstance(store, MemoryStore):
        db = _Db.memory()
    elif hasattr(store, "_db") and hasattr(store, "_lock"):
        # The postgres store's connection and lock (one connection per process; schema from `migrate`).
        db = _Db(store._db, store._lock, pg=True, schema=getattr(store, "_schema", None))
        try:
            db.run("SELECT alg, key_label FROM audit_checkpoints LIMIT 1")
        except Exception as exc:  # noqa: BLE001 - any driver error here means "not migrated or unreachable"
            from hadavin_sdk.store.protocol import StoreUnavailable, is_connectivity_error

            if is_connectivity_error(exc):
                # A connection-level failure is an outage, not a missing migration: `tick` exits 4, not 2.
                raise StoreUnavailable(
                    f"audit chain: the store is unreachable ({type(exc).__name__})"
                ) from None
            raise ConfigError(
                f"audit chain: the audit tables are missing; run hadavin-sdk migrate "
                f"({type(exc).__name__})"
            ) from None
    else:
        raise ConfigError("audit chain: needs store memory or postgres")
    if deps.anchor is not None and deps.signer is None:
        raise ConfigError("audit chain: an anchor needs a signer (backends.signer)")
    # The anchor is its own capability (backends.anchor), built before the audit and handed in through Deps.
    return ChainAudit(
        db,
        deps.signer,
        deps.anchor,
        settings.checkpoint_every,
        getattr(settings, "drain_batch", None),
    )
