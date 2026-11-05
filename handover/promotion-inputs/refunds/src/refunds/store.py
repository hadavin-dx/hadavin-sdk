"""Persistent store for the governed write path (SQLite, stdlib only; a client build swaps in its own database behind the same methods).

What lives here and why (design review 6, M1/M3/B2):
  applied               one row per applied action, UNIQUE(tenant, key): the idempotency map survives a restart, a second instance and a crash.
  approvals_used        one-use approvals: UNIQUE(tenant, approval_id) so one approval can never pay under two keys. It also keeps WHO: the requester,
                        the ordered approvers (person + role), the tier and the executing identity, so "who approved this?" is answerable (`who_approved`).
  reservations          open reservations per tenant (released or converted when the action applies). `reserve` enforces the flooding caps
                        (PENDING_CAP per cluster and per sender, and the not-yet-executed share of the day cap) from THESE rows in one transaction.
  compensation_records  a record that says WHAT a human would book to compensate an applied action. It cannot be run backwards: a processor refund
                        is never taken back, only compensated by a new entry.
  audit                 hash-chained rows (prev hash + canonical body). It proves the rows were not edited in place by someone who does not rewrite the
                        whole tail; it does not prove who wrote them (no signing key here).
  meta                  kill switch (who, why, when) and the last server-clock reading (the clock may never go backwards).
Every write happens inside `transaction()` (BEGIN IMMEDIATE), so two processes on one file serialise too.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from refunds.config import APPROVAL_TTL_S, MAX_AT_SKEW_S, STORE_LOCK_TIMEOUT_S, pending_cap_decision, unapproved_share_ok
from refunds.hashing import canonical_json

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS applied(
  tenant TEXT NOT NULL, key TEXT NOT NULL, action TEXT NOT NULL, order_id TEXT NOT NULL, line_ids TEXT NOT NULL,
  amount_minor INTEGER NOT NULL CHECK (amount_minor > 0), currency TEXT NOT NULL, customer_id TEXT NOT NULL,
  approval_id TEXT NOT NULL, applied_at TEXT NOT NULL, day TEXT NOT NULL,
  PRIMARY KEY (tenant, key));
CREATE TABLE IF NOT EXISTS approvals_used(
  tenant TEXT NOT NULL, approval_id TEXT NOT NULL, key TEXT NOT NULL, requester TEXT NOT NULL, approvers TEXT NOT NULL, tier TEXT NOT NULL,
  executed_by TEXT NOT NULL, consumed_at TEXT NOT NULL, PRIMARY KEY (tenant, approval_id));
CREATE TABLE IF NOT EXISTS reservations(
  tenant TEXT NOT NULL, key TEXT NOT NULL, customer_id TEXT NOT NULL, order_id TEXT NOT NULL,
  amount_minor INTEGER NOT NULL CHECK (amount_minor > 0), currency TEXT NOT NULL, created_at TEXT NOT NULL, sender TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (tenant, key));
CREATE TABLE IF NOT EXISTS voided(
  tenant TEXT NOT NULL, key TEXT NOT NULL, reason TEXT NOT NULL, identity TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY (tenant, key));
CREATE TABLE IF NOT EXISTS compensation_records(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL, key TEXT NOT NULL, record TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, tenant TEXT NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL,
  prev TEXT NOT NULL, hash TEXT NOT NULL);
"""
GENESIS = "0" * 64


class StoreBusy(Exception):
    """The store's write lock could not be taken within the timeout (another writer holds it). A typed condition, not a raw driver error."""


class Store:
    def __init__(self, path: str = ":memory:", timeout_s: float = STORE_LOCK_TIMEOUT_S) -> None:
        self.path = path
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=timeout_s)
        self._db.row_factory = sqlite3.Row
        if path != ":memory:":
            self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)
        self._mutex = threading.RLock()
        self._depth = 0

    def close(self) -> None:
        self._db.close()

    @contextlib.contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """All-or-nothing. Re-entrant inside one thread (an inner call joins the outer transaction)."""
        with self._mutex:
            if self._depth:
                self._depth += 1
                try:
                    yield self._db
                finally:
                    self._depth -= 1
                return
            try:
                self._db.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as e:  # the lock timeout (or a busy database): typed, never a raw driver error
                raise StoreBusy(str(e)) from e
            self._depth = 1
            try:
                yield self._db
            except BaseException:
                self._rollback()
                raise
            else:
                try:
                    self._db.execute("COMMIT")
                except BaseException:
                    self._rollback()  # a failed COMMIT must not leave the connection inside a transaction
                    raise
            finally:
                self._depth = 0

    def _rollback(self) -> None:
        """Roll back without letting a failing ROLLBACK replace the error that caused it."""
        with contextlib.suppress(sqlite3.Error):
            self._db.execute("ROLLBACK")

    # ---------------------------------------------------------------- meta: clock and kill switch
    def meta(self, k: str) -> str | None:
        with self._mutex:
            row = self._db.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
        return row["v"] if row else None

    def set_meta(self, k: str, v: str) -> None:
        with self.transaction() as db:
            db.execute("INSERT INTO meta(k, v) VALUES(?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v))

    def kill_switch(self) -> dict:
        raw = self.meta("kill_switch")
        return json.loads(raw) if raw else {"on": False, "operator": None, "reason": None, "at": None}

    def set_kill_switch(self, on: bool, operator: str, reason: str, at: str) -> None:
        with self.transaction():
            self.set_meta("kill_switch", canonical_json({"on": bool(on), "operator": operator, "reason": reason, "at": at}))
            self.audit("-", "kill_switch_on" if on else "kill_switch_off", {"operator": operator, "reason": reason}, at)

    # ---------------------------------------------------------------- audit chain
    def audit(self, tenant: str, event: str, detail: dict, ts: str) -> None:
        with self.transaction() as db:
            row = db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            prev = row["hash"] if row else GENESIS
            body = canonical_json({"ts": ts, "tenant": tenant, "event": event, "detail": detail})
            digest = hashlib.sha256((prev + body).encode("ascii")).hexdigest()
            db.execute(
                "INSERT INTO audit(ts, tenant, event, detail, prev, hash) VALUES(?,?,?,?,?,?)",
                (ts, tenant, event, canonical_json(detail), prev, digest),
            )

    def audit_rows(self) -> list[dict]:
        with self._mutex:
            return [dict(r) for r in self._db.execute("SELECT * FROM audit ORDER BY seq")]

    def audit_chain_ok(self) -> bool:
        prev = GENESIS
        for r in self.audit_rows():
            body = canonical_json({"ts": r["ts"], "tenant": r["tenant"], "event": r["event"], "detail": json.loads(r["detail"])})
            if r["prev"] != prev or hashlib.sha256((prev + body).encode("ascii")).hexdigest() != r["hash"]:
                return False
            prev = r["hash"]
        return True

    # ---------------------------------------------------------------- applied actions (every read is tenant-scoped)
    def get_applied(self, tenant: str, key: str) -> dict | None:
        with self._mutex:
            row = self._db.execute("SELECT * FROM applied WHERE tenant=? AND key=?", (tenant, key)).fetchone()
        return dict(row) if row else None

    def order_rows(self, tenant: str, order_id: str) -> list[dict]:
        with self._mutex:
            return [dict(r) for r in self._db.execute("SELECT * FROM applied WHERE tenant=? AND order_id=?", (tenant, order_id))]

    def sum_order(
        self, tenant: str, order_id: str, currency: str, actions: tuple[str, ...] = ("refund", "cancel", "reship", "goodwill")
    ) -> int:
        total = 0
        with self._mutex:
            for action in actions:  # one fixed query per action: no string-built SQL
                row = self._db.execute(
                    "SELECT COALESCE(SUM(amount_minor),0) AS s FROM applied WHERE tenant=? AND order_id=? AND currency=? AND action=?",
                    (tenant, order_id, currency, action),
                ).fetchone()
                total += int(row["s"])
        return total

    def sum_customers_since(self, tenant: str, customer_ids: list[str], currency: str, since: str) -> int:
        total = 0
        with self._mutex:
            for cid in sorted(set(customer_ids)):
                row = self._db.execute(
                    "SELECT COALESCE(SUM(amount_minor),0) AS s FROM applied WHERE tenant=? AND currency=? AND applied_at>=? AND customer_id=?",
                    (tenant, currency, since, cid),
                ).fetchone()
                total += int(row["s"])
        return total

    def sum_day(self, tenant: str, currency: str, day: str) -> int:
        with self._mutex:
            row = self._db.execute(
                "SELECT COALESCE(SUM(amount_minor),0) AS s FROM applied WHERE tenant=? AND currency=? AND day=?",
                (tenant, currency, day),
            ).fetchone()
        return int(row["s"])

    def count_applied(self, tenant: str | None = None) -> int:
        with self._mutex:
            if tenant is None:
                return int(self._db.execute("SELECT COUNT(*) AS n FROM applied").fetchone()["n"])
            return int(self._db.execute("SELECT COUNT(*) AS n FROM applied WHERE tenant=?", (tenant,)).fetchone()["n"])

    def insert_applied(self, rec: dict) -> None:
        with self.transaction() as db:
            db.execute(
                "INSERT INTO applied(tenant,key,action,order_id,line_ids,amount_minor,currency,customer_id,approval_id,applied_at,day) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    rec["tenant"], rec["key"], rec["action"], rec["order_id"], json.dumps(rec["line_ids"]), rec["amount_minor"],
                    rec["currency"], rec["customer_id"], rec["approval_id"], rec["applied_at"], rec["day"],
                ),
            )  # fmt: skip

    # ---------------------------------------------------------------- one-use approvals
    def approval_key(self, tenant: str, approval_id: str) -> str | None:
        with self._mutex:
            row = self._db.execute(
                "SELECT key FROM approvals_used WHERE tenant=? AND approval_id=?", (tenant, approval_id)
            ).fetchone()
        return row["key"] if row else None

    def consume_approval(
        self, tenant: str, approval_id: str, key: str, requester: str, approvers: list[dict], tier: str, executed_by: str, at: str
    ) -> None:
        with self.transaction() as db:
            db.execute(
                "INSERT INTO approvals_used(tenant, approval_id, key, requester, approvers, tier, executed_by, consumed_at) VALUES(?,?,?,?,?,?,?,?)",
                (tenant, approval_id, key, requester, canonical_json(approvers), tier, executed_by, at),
            )

    def who_approved(self, tenant: str, key: str) -> dict | None:
        """Who raised, approved and executed the applied action `key` (tenant-scoped); None if it was never applied."""
        with self._mutex:
            row = self._db.execute(
                "SELECT a.approval_id, u.requester, u.approvers, u.tier, u.executed_by, a.applied_at FROM applied a "
                "JOIN approvals_used u ON u.tenant=a.tenant AND u.approval_id=a.approval_id WHERE a.tenant=? AND a.key=?",
                (tenant, key),
            ).fetchone()
        if row is None:
            return None
        r = dict(row)
        r["approvers"] = json.loads(r["approvers"])
        return r

    # ---------------------------------------------------------------- reservations
    def _window(self, at: str) -> str:
        """The start of the open-reservation window for the time `at`: `at` minus the approval TTL. The window is never taken from a caller, and `at`
        itself may not run ahead of the newest time this store has already seen by more than MAX_AT_SKEW_S (a far-future `at` would otherwise sit
        in the table for ever, or push the window past every real row)."""
        try:
            at_dt = datetime.strptime(at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        except (TypeError, ValueError):
            raise ValueError("AT_NOT_A_TIME") from None
        seen = [
            x
            for x in (self.meta("last_clock"), self._newest("reservations", "created_at"), self._newest("applied", "applied_at"))
            if x
        ]
        if seen and at_dt > datetime.strptime(max(seen), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC) + timedelta(
            seconds=MAX_AT_SKEW_S
        ):
            raise ValueError("AT_AHEAD_OF_THE_STORE_CLOCK")
        return (at_dt - timedelta(seconds=APPROVAL_TTL_S)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _newest(self, table: str, column: str) -> str | None:
        queries = {
            ("reservations", "created_at"): "SELECT MAX(created_at) AS m FROM reservations",
            ("applied", "applied_at"): "SELECT MAX(applied_at) AS m FROM applied",
        }
        with self._mutex:
            return self._db.execute(queries[(table, column)]).fetchone()["m"]

    def reserve(
        self, tenant: str, key: str, customer_id: str, order_id: str, amount_minor: int, currency: str, at: str, *,
        cluster: list[str], sender: str,
    ) -> str | None:  # fmt: skip
        """Idempotent (the same key reserves once) and BOUNDED: in ONE transaction it counts the tenant's open reservations younger than `since` and
        returns "PENDING_CAP" (R-REF-025) when the cluster or the sender already holds the maximum open proposals, or when the open not-yet-executed
        total plus this one would exceed the unapproved share of the day cap. The caps read THIS table, not a caller-supplied port state, so a looping
        agent cannot fill the day cap with reservations. Returns None when the reservation is held. `at` is the desk's SERVER clock (never a request
        field); the window start is derived from it here, not passed in. A bad or runaway `at` raises ValueError (a caller bug, not a deny)."""
        since = self._window(at)
        with self.transaction() as db:
            if db.execute("SELECT 1 FROM reservations WHERE tenant=? AND key=?", (tenant, key)).fetchone():
                return None
            open_cluster, open_sender = self._open_counts(tenant, cluster, sender, since)
            held = int(
                db.execute(
                    "SELECT COALESCE(SUM(amount_minor),0) AS s FROM reservations WHERE tenant=? AND currency=? AND created_at>=?",
                    (tenant, currency, since),
                ).fetchone()["s"]
            )
            if pending_cap_decision(open_cluster, open_sender) or not unapproved_share_ok(held, amount_minor, currency):
                return "PENDING_CAP"
            db.execute(
                "INSERT INTO reservations(tenant,key,customer_id,order_id,amount_minor,currency,created_at,sender) VALUES(?,?,?,?,?,?,?,?)",
                (tenant, key, customer_id, order_id, amount_minor, currency, at, sender),
            )
        return None

    def _open_counts(self, tenant: str, cluster: list[str], sender: str, since: str, exclude_key: str = "") -> tuple[int, int]:
        """(open reservations of the cluster, open reservations of the sender), younger than `since`, not counting `exclude_key` (a key's own entry)."""
        with self._mutex:
            n_cluster = sum(
                int(self._db.execute(
                    "SELECT COUNT(*) AS n FROM reservations WHERE tenant=? AND created_at>=? AND customer_id=? AND key<>?",
                    (tenant, since, cid, exclude_key),
                ).fetchone()["n"])
                for cid in sorted(set(cluster))
            )  # fmt: skip
            n_sender = int(
                self._db.execute(
                    "SELECT COUNT(*) AS n FROM reservations WHERE tenant=? AND created_at>=? AND sender=? AND key<>?",
                    (tenant, since, sender, exclude_key),
                ).fetchone()["n"]
            )
        return n_cluster, n_sender

    def open_state(
        self, tenant: str, cluster: list[str], sender: str, currency: str, at: str, day: str, exclude_key: str = ""
    ) -> dict:
        """The pre-gate's port state, read from the store: open reservations younger than the window that ends at `at`, the day's applied total and
        the open-proposal counts."""
        since = self._window(at)
        with self._mutex:
            rows = [
                dict(r)
                for r in self._db.execute(
                    "SELECT key AS request_ref, customer_id, order_id, amount_minor FROM reservations WHERE tenant=? AND currency=? AND created_at>=? ORDER BY key",
                    (tenant, currency, since),
                )
            ]
        n_cluster, n_sender = self._open_counts(tenant, cluster, sender, since, exclude_key)
        return {
            "open_reservations": [{**r, "amount_minor": str(r["amount_minor"])} for r in rows],
            "store_day_refunded_minor": {currency: str(self.sum_day(tenant, currency, day))},
            "open_proposals": {"cluster": n_cluster, "sender": n_sender},
        }

    def void_key(self, tenant: str, key: str, reason: str, identity: str, at: str) -> None:
        """Write the tombstone: this key can never be executed again (WriteGate refuses it as KEY_VOIDED). A void is a WITHDRAWAL, not only a cap release;
        a new proposal that should go ahead needs a new key (other lines, amount or order)."""
        with self.transaction() as db:
            db.execute(
                "INSERT OR IGNORE INTO voided(tenant,key,reason,identity,at) VALUES(?,?,?,?,?)",
                (tenant, key, reason, identity, at),
            )

    def is_voided(self, tenant: str, key: str) -> bool:
        with self._mutex:
            return self._db.execute("SELECT 1 FROM voided WHERE tenant=? AND key=?", (tenant, key)).fetchone() is not None

    def release(self, tenant: str, key: str) -> int:
        with self.transaction() as db:
            return db.execute("DELETE FROM reservations WHERE tenant=? AND key=?", (tenant, key)).rowcount

    def other_reserved(self, tenant: str, currency: str, own_key: str, since: str) -> int:
        """Open reservations of OTHER keys that are not older than `since` (an expired reservation no longer holds a cap)."""
        with self._mutex:
            row = self._db.execute(
                "SELECT COALESCE(SUM(amount_minor),0) AS s FROM reservations WHERE tenant=? AND currency=? AND key<>? AND created_at>=?",
                (tenant, currency, own_key, since),
            ).fetchone()
        return int(row["s"])

    def sweep_reservations(self, older_than: str, at: str) -> int:
        """Delete reservations created before `older_than` (any tenant). One audit row per sweep that removed something."""
        with self.transaction() as db:
            n = db.execute("DELETE FROM reservations WHERE created_at<?", (older_than,)).rowcount
            if n:
                self.audit("-", "reservations_swept", {"count": n, "older_than": older_than}, at)
        return n

    def reservations(self, tenant: str) -> list[dict]:
        with self._mutex:
            return [dict(r) for r in self._db.execute("SELECT * FROM reservations WHERE tenant=? ORDER BY key", (tenant,))]

    # ---------------------------------------------------------------- compensation records
    def add_compensation_record(self, tenant: str, key: str, record: dict) -> None:
        with self.transaction() as db:
            db.execute("INSERT INTO compensation_records(tenant,key,record) VALUES(?,?,?)", (tenant, key, canonical_json(record)))

    def compensation_records(self, tenant: str) -> list[dict]:
        with self._mutex:
            return [
                json.loads(r["record"])
                for r in self._db.execute("SELECT record FROM compensation_records WHERE tenant=? ORDER BY seq", (tenant,))
            ]
