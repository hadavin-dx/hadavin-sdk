"""Inbound-message ledger (no-lost-messages), SQLite behind the `InboundLedgerPort` interface. One implementation, two modes:
  * `InboundLedger(":memory:")` (alias `FakeInboundLedger`): the test fake. NOT durable: say so wherever it is used.
  * `InboundLedger("path/to/ledger.db")`: the neutral default durable backend, WAL journal with `synchronous=FULL`, so a receipt is on disk before `record_receipt` returns
    (write-ahead). A restart test proves it. Postgres is the alternative for a client that has one, behind the same interface.
Rules: a receipt is keyed by (tenant, message id, CONTENT HASH). The same triple again is a redelivery: same receipt, deliveries + 1, nothing else changes. The same message id with DIFFERENT
content (a forged or colliding Message-ID, or a re-sent edited mail) is a NEW receipt that is dead-lettered at once with an alert, linked to the first via `conflict_of`; the first receipt and its
state are never touched, so an attacker copying a Message-ID cannot get a legitimate mail rejected. Every receipt ends in exactly one terminal state. Over capacity raises OverloadedError
(backpressure; the message stays at the source). Tenants are separate namespaces (tenant-isolation)."""

from __future__ import annotations

import sqlite3
import threading

from .port import TERMINAL_STATES, OverloadedError, Receipt

_SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, receipt_id TEXT UNIQUE NOT NULL, tenant TEXT NOT NULL, message_id TEXT NOT NULL, raw_sha TEXT NOT NULL,
  verified_sender TEXT, state TEXT, reason TEXT NOT NULL DEFAULT '', deliveries INTEGER NOT NULL DEFAULT 1, conflict_of TEXT,
  UNIQUE (tenant, message_id, raw_sha));
CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL, receipt_id TEXT NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL);
"""


def _locked(fn):
    def wrapper(self, *a, **kw):
        with self._lock:
            return fn(self, *a, **kw)

    wrapper.__name__, wrapper.__doc__ = fn.__name__, fn.__doc__
    return wrapper


class InboundLedger:
    def __init__(self, path: str = ":memory:", capacity: int | None = None) -> None:
        self.path, self._capacity = path, capacity
        self._lock = threading.RLock()  # ONE connection is shared by all threads: every method, reads included, runs under this lock
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        if path != ":memory:":
            self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.executescript(_SCHEMA)

    @property
    def durable(self) -> bool:
        return self.path != ":memory:"

    def close(self) -> None:
        self._db.close()

    def _receipt(self, row) -> Receipt:
        return Receipt(row[0], row[1], row[2], row[3], row[4])

    def record_receipt(self, tenant_id: str, message_id: str, raw_sha256: str, verified_sender: str | None = None) -> tuple[Receipt, bool]:
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                row = self._db.execute(
                    "SELECT receipt_id,tenant,message_id,raw_sha,verified_sender FROM receipts WHERE tenant=? AND message_id=? AND raw_sha=?",
                    (tenant_id, message_id, raw_sha256),
                ).fetchone()
                if row:
                    self._db.execute("UPDATE receipts SET deliveries=deliveries+1 WHERE receipt_id=?", (row[0],))
                    self._db.execute("COMMIT")
                    return self._receipt(row), False
                if (
                    self._capacity is not None
                    and self._db.execute("SELECT COUNT(*) FROM receipts WHERE state IS NULL").fetchone()[0] >= self._capacity
                ):
                    self._db.execute("ROLLBACK")
                    raise OverloadedError("ledger at capacity: retry later")
                n = self._db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0] + 1
                rid = f"r-{n:07d}"
                first = self._db.execute(
                    "SELECT receipt_id FROM receipts WHERE tenant=? AND message_id=? ORDER BY seq LIMIT 1", (tenant_id, message_id)
                ).fetchone()
                self._db.execute(
                    "INSERT INTO receipts (receipt_id,tenant,message_id,raw_sha,verified_sender,conflict_of) VALUES (?,?,?,?,?,?)",
                    (rid, tenant_id, message_id, raw_sha256, verified_sender, first[0] if first else None),
                )
                if first:
                    self._db.execute(
                        "UPDATE receipts SET state='dead_lettered', reason='message id reused with different content' WHERE receipt_id=?",
                        (rid,),
                    )
                    self._db.execute(
                        "INSERT INTO alerts (tenant,receipt_id,kind,detail) VALUES (?,?,?,?)",
                        (tenant_id, rid, "message_id_conflict", f"same Message-ID as {first[0]}, different content"),
                    )
                self._db.execute("COMMIT")
                return Receipt(rid, tenant_id, message_id, raw_sha256, verified_sender), True
            except OverloadedError:
                raise
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    @_locked
    def get(self, receipt_id: str) -> Receipt | None:
        row = self._db.execute(
            "SELECT receipt_id,tenant,message_id,raw_sha,verified_sender FROM receipts WHERE receipt_id=?", (receipt_id,)
        ).fetchone()
        return self._receipt(row) if row else None

    def set_terminal(self, receipt_id: str, state: str, reason: str = "") -> None:
        if state not in TERMINAL_STATES:
            raise ValueError(f"not a terminal state: {state!r}")
        with self._lock:
            row = self._db.execute("SELECT state FROM receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
            if row is None:
                raise KeyError(receipt_id)
            if row[0] not in (None, state):
                raise ValueError(f"receipt already ended as {row[0]!r}")
            self._db.execute("UPDATE receipts SET state=?, reason=? WHERE receipt_id=?", (state, reason, receipt_id))

    @_locked
    def unresolved(self, tenant_id: str) -> list[Receipt]:
        rows = self._db.execute(
            "SELECT receipt_id,tenant,message_id,raw_sha,verified_sender FROM receipts WHERE tenant=? AND state IS NULL ORDER BY seq",
            (tenant_id,),
        ).fetchall()
        return [self._receipt(r) for r in rows]

    @_locked
    def state_of(self, tenant_id: str, message_id: str, raw_sha256: str | None = None) -> str | None:
        q, args = "SELECT state FROM receipts WHERE tenant=? AND message_id=?", [tenant_id, message_id]
        if raw_sha256 is not None:
            q, args = q + " AND raw_sha=?", [*args, raw_sha256]
        row = self._db.execute(q + " ORDER BY seq LIMIT 1", args).fetchone()
        return row[0] if row else None

    @_locked
    def deliveries(self, tenant_id: str, message_id: str) -> int:
        row = self._db.execute(
            "SELECT deliveries FROM receipts WHERE tenant=? AND message_id=? ORDER BY seq LIMIT 1", (tenant_id, message_id)
        ).fetchone()
        return row[0] if row else 0

    @_locked
    def alerts(self, tenant_id: str) -> list[tuple[str, str]]:
        return self._db.execute("SELECT kind, detail FROM alerts WHERE tenant=? ORDER BY id", (tenant_id,)).fetchall()

    @_locked
    def reconcile(self, tenant_id: str, source_ids: set[str]) -> dict:
        have = {r[0] for r in self._db.execute("SELECT DISTINCT message_id FROM receipts WHERE tenant=?", (tenant_id,))}
        conflicts = sorted(
            r[0]
            for r in self._db.execute("SELECT message_id FROM receipts WHERE tenant=? GROUP BY message_id HAVING COUNT(*)>1", (tenant_id,))
        )
        return {"missing": sorted(source_ids - have), "unknown": sorted(have - source_ids), "conflicts": conflicts}

    @_locked
    def counts(self, tenant_id: str) -> dict:
        rows = self._db.execute("SELECT state, COUNT(*) FROM receipts WHERE tenant=? GROUP BY state", (tenant_id,)).fetchall()
        by = {s: n for s, n in rows}
        c = {"received": sum(by.values()), "unresolved": by.get(None, 0)}
        for s in TERMINAL_STATES:
            c[s] = by.get(s, 0)
        return c


FakeInboundLedger = InboundLedger  # the in-memory mode is the test fake
