"""Inbound message ledger (inbound ledger; R-DEALDESK-093): no message is silently lost or double-applied.
Write-ahead: the raw message and a receipt id are committed BEFORE the source is acked or anything is processed. At-least-once processing with an
idempotency key (tenant, msg_id) so a redelivery changes nothing; the same id with a DIFFERENT body is never dropped: it is recorded as its own rejected
row (`id_reuse`). Every message ends in a recorded terminal state: processed, abstained, dead_lettered or rejected (with a reason). `reconcile` compares
the source's own ids with the ledger and lists the ids still open; `recover` re-offers them. Overload is a rate cap (refused BEFORE the ack, the sender
retries) and a bounded queue with backpressure (`offer` returns False), never a drop.

KNOWN LIMIT: the deadline abandons a worker thread, it cannot release a lock that thread holds. A handler hung INSIDE `TenantStore.lock` therefore blocks every
later handler of that tenant (each is dead-lettered with reason `deadline`, recoverable by `recover`), and the abandoned thread may still finish its effect later.

Bounds (limits.py): a message above the size limit is refused before the ack; the handler has a per-message deadline (a stalled dependency is dead-lettered
with reason `deadline`; the stuck thread is abandoned, not killed: Python cannot kill a thread, so CPU-bound work is bounded by the size limit and linear
scanners instead). The authenticated identity of the sender (channel) is set by `receive(auth=...)` and cannot be supplied in the body.

LedgerStore is a kind: MemoryLedger (neutral default, tests) and SqliteLedger (stdlib sqlite3, WAL, synchronous=FULL; a client build swaps in PostgreSQL
behind the same methods when it needs multi-writer or more than a few hundred durable commits per second)."""

from __future__ import annotations

import hashlib
import json
import queue
import sqlite3
import threading
import time
from collections import Counter
from collections.abc import Callable
from typing import Protocol

from dealdesk.errors import Malformed
from dealdesk.guards import RateCap
from dealdesk.limits import DEFAULT_LIMITS, Limits
from dealdesk.store import check_tenant

TERMINAL = ("processed", "abstained", "dead_lettered", "rejected")
HANDLER_STATES = ("processed", "abstained")  # what a handler may return; the other two are the inbox's own verdicts
MAX_ATTEMPTS = 3
ID_REUSE_MARK = "#idreuse-"  # reserved: a sender id may not contain it


class LedgerStore(Protocol):
    def receive(
        self, tenant: str, msg_id: str, raw: str, state: str = "received", reason: str | None = None
    ) -> str: ...  # "new" | "duplicate" | "conflict" (same id, different body)
    def set_state(self, tenant: str, msg_id: str, state: str, reason: str | None) -> None: ...
    def get(self, tenant: str, msg_id: str) -> dict | None: ...
    def ids(self, tenant: str) -> dict[str, str]: ...  # msg_id -> state
    def open_ids(self, tenant: str) -> list[str]: ...  # received or processing


def _sha(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class MemoryLedger:
    def __init__(self) -> None:
        self._d: dict[tuple[str, str], dict] = {}
        self._l = threading.Lock()

    def receive(self, tenant, msg_id, raw, state="received", reason=None):
        with self._l:
            cur = self._d.get((tenant, msg_id))
            if cur is not None:
                return "duplicate" if cur["raw_sha256"] == _sha(raw) else "conflict"
            self._d[(tenant, msg_id)] = {"raw_sha256": _sha(raw), "raw": raw, "state": state, "reason": reason, "attempts": 0}
            return "new"

    def set_state(self, tenant, msg_id, state, reason):
        with self._l:
            r = self._d[(tenant, msg_id)]
            if r["state"] in TERMINAL:
                return  # a terminal state is final
            r["state"], r["reason"] = state, reason
            r["attempts"] += state == "processing"

    def get(self, tenant, msg_id):
        with self._l:
            r = self._d.get((tenant, msg_id))
            return dict(r) if r else None

    def ids(self, tenant):
        with self._l:
            return {m: r["state"] for (t, m), r in self._d.items() if t == tenant}

    def open_ids(self, tenant):
        with self._l:
            return sorted(m for (t, m), r in self._d.items() if t == tenant and r["state"] in ("received", "processing"))


class SqliteLedger:
    """sqlite3 (stdlib). One connection guarded by a lock; WAL + synchronous=FULL so a committed receipt survives a crash."""

    def __init__(self, path: str) -> None:
        self._c = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._c.execute("PRAGMA journal_mode=WAL")
        self._c.execute("PRAGMA synchronous=FULL")
        self._c.execute(
            "CREATE TABLE IF NOT EXISTS msgs (tenant TEXT NOT NULL, msg_id TEXT NOT NULL, raw TEXT NOT NULL, raw_sha256 TEXT NOT NULL, state TEXT NOT NULL, "
            "reason TEXT, attempts INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (tenant, msg_id))"
        )
        self._l = threading.Lock()

    def receive(self, tenant, msg_id, raw, state="received", reason=None):
        with self._l:
            h = _sha(raw)
            cur = self._c.execute(
                "INSERT OR IGNORE INTO msgs (tenant, msg_id, raw, raw_sha256, state, reason) VALUES (?,?,?,?,?,?)",
                (tenant, msg_id, raw, h, state, reason),
            )
            if cur.rowcount == 1:
                return "new"
            old = self._c.execute("SELECT raw_sha256 FROM msgs WHERE tenant=? AND msg_id=?", (tenant, msg_id)).fetchone()
            return "duplicate" if old and old[0] == h else "conflict"

    def set_state(self, tenant, msg_id, state, reason):
        with self._l:
            self._c.execute(
                "UPDATE msgs SET state=?, reason=?, attempts=attempts+? WHERE tenant=? AND msg_id=? AND state NOT IN "
                "('processed','abstained','dead_lettered','rejected')",
                (state, reason, int(state == "processing"), tenant, msg_id),
            )

    def get(self, tenant, msg_id):
        with self._l:
            r = self._c.execute(
                "SELECT raw, state, reason, attempts FROM msgs WHERE tenant=? AND msg_id=?", (tenant, msg_id)
            ).fetchone()
            return {"raw": r[0], "state": r[1], "reason": r[2], "attempts": r[3]} if r else None

    def ids(self, tenant):
        with self._l:
            return dict(self._c.execute("SELECT msg_id, state FROM msgs WHERE tenant=?", (tenant,)).fetchall())

    def open_ids(self, tenant):
        with self._l:
            rows = self._c.execute(
                "SELECT msg_id FROM msgs WHERE tenant=? AND state IN ('received','processing') ORDER BY msg_id", (tenant,)
            ).fetchall()
            return [r[0] for r in rows]

    def close(self) -> None:
        self._c.close()


class _Deadline(Exception):
    """The handler did not return within the per-message deadline."""


class Inbox:
    """`handler(message_dict) -> ("processed"|"abstained", reason)`; it may raise Malformed (rejected) or anything else (retried, then dead-lettered).
    The handler's effects MUST be idempotent by message content/business key; the inbox adds the (tenant, msg_id) key on top."""

    def __init__(
        self,
        ledger: LedgerStore,
        handler: Callable[[dict], tuple[str, str | None]],
        queue_bound: int = 64,
        limits: Limits = DEFAULT_LIMITS,
        rate_cap: RateCap | None = None,
        now_s: Callable[[], float] = time.monotonic,
    ) -> None:
        self.ledger, self.handler, self.limits, self.rate_cap, self.now_s = ledger, handler, limits, rate_cap, now_s
        self.q: queue.Queue = queue.Queue(maxsize=queue_bound)
        self.refusals: Counter = Counter()  # reason -> count, for messages refused BEFORE any ack

    def _refuse(self, reason: str) -> None:
        self.refusals[reason] += 1

    def receive(self, tenant: str, msg: dict, auth: dict | None = None) -> str | None:
        """Persist first, then return the receipt id (the 'ack'). A message that cannot be keyed, is too large, carries a reserved key, or arrives above
        the rate cap is refused BEFORE any ack (the sender still holds it and may retry): `None`, with the reason counted in `refusals`."""
        try:
            check_tenant(tenant)
            if not isinstance(msg, dict) or "_auth" in msg:
                return self._refuse("malformed")
            mid = msg["msg_id"]
            if not isinstance(mid, str) or not mid or len(mid) > self.limits.max_id_chars or ID_REUSE_MARK in mid:
                return self._refuse("malformed")  # the marker is reserved for the inbox's own id_reuse rows
            if auth is not None and (not isinstance(auth, dict) or set(auth) - {"person_id", "identity"}):
                return self._refuse("malformed")
            body = {**msg, "_auth": auth}
            raw = json.dumps(body, sort_keys=True, ensure_ascii=True)
        except (Malformed, KeyError, TypeError, ValueError):
            return self._refuse("malformed")
        if len(raw.encode("ascii")) > self.limits.max_message_bytes:
            return self._refuse("oversize")
        if self.rate_cap is not None and not self.rate_cap.allow(self.now_s()):
            return self._refuse("rate_limited")
        status = self.ledger.receive(tenant, mid, raw)
        if status == "conflict":  # same id, different body: never dropped, never merged; recorded as its own rejected row
            cid = f"{mid}{ID_REUSE_MARK}{_sha(raw)[:16]}"  # mid is at most max_id_chars: the 16 hex digits are never cut
            self.ledger.receive(
                tenant, cid, raw, "rejected", "id_reuse"
            )  # ONE write: there is no moment where the conflicting body is `received`
            return "rcpt-" + _sha(f"{tenant}/{cid}")[:20]
        return "rcpt-" + _sha(f"{tenant}/{mid}")[:20]

    def offer(self, tenant: str, mid: str, block: bool = False) -> bool:
        try:
            self.q.put((tenant, mid), block=block, timeout=None if block else 0)
            return True
        except queue.Full:
            return False  # backpressure: the caller waits or drains; nothing is dropped

    def _run_handler(self, msg: dict) -> tuple[str, str | None]:
        """Run the handler under the per-message deadline. On expiry the worker thread is abandoned (it cannot be killed) and `_Deadline` is raised."""
        box: dict = {}

        def work() -> None:
            try:
                box["out"] = self.handler(msg)
            except BaseException as e:  # noqa: BLE001  re-raised in the caller's thread
                box["err"] = e

        th = threading.Thread(target=work, daemon=True)
        th.start()
        th.join(self.limits.handler_deadline_s)
        if th.is_alive():
            raise _Deadline("deadline")
        if "err" in box:
            raise box["err"]
        return box["out"]

    def process(self, tenant: str, mid: str) -> str:
        row = self.ledger.get(tenant, mid)
        if row is None:
            raise KeyError("not received")
        if row["state"] in TERMINAL:
            return row["state"]  # redelivery of a finished message changes nothing
        msg = json.loads(row["raw"])
        for _ in range(MAX_ATTEMPTS):
            self.ledger.set_state(tenant, mid, "processing", None)
            try:
                state, reason = self._run_handler({**msg, "tenant_id": tenant})
                if state not in HANDLER_STATES:
                    raise RuntimeError("handler returned a non-terminal or unknown state")
            except Malformed as e:
                self.ledger.set_state(tenant, mid, "rejected", str(e)[:120])
                return "rejected"
            except _Deadline:
                self.ledger.set_state(tenant, mid, "dead_lettered", "deadline")
                return "dead_lettered"
            except Exception:  # noqa: BLE001, S112  poison or transient: retry, then dead-letter
                continue
            self.ledger.set_state(tenant, mid, state, reason)
            return state
        self.ledger.set_state(tenant, mid, "dead_lettered", "attempts exhausted")
        return "dead_lettered"

    def recover(self, tenant: str) -> int:
        """After a crash: re-offer every row still `received` or `processing` (a handler is idempotent, so a repeat changes nothing). Returns how many were
        offered; those that do not fit the bounded queue are processed in place (backpressure, never dropped)."""
        n = 0
        for mid in self.ledger.open_ids(tenant):
            if not self.offer(tenant, mid):
                self.drain()
                self.offer(tenant, mid)
            n += 1
        self.drain()
        return n

    def drain(self) -> None:
        while True:
            try:
                tenant, mid = self.q.get_nowait()
            except queue.Empty:
                return
            self.process(tenant, mid)


def reconcile(ledger: LedgerStore, tenant: str, source_ids: set[str]) -> dict:
    """Compare the source's own ids (mailbox UIDs, provider event ids) with the ledger, both directions; the state counts; and the IDS still open."""
    led = ledger.ids(tenant)
    reused = sorted(i for i in led if ID_REUSE_MARK in i)
    own = {i for i in led if ID_REUSE_MARK not in i}
    counts = {
        s: sum(1 for i in own if led[i] == s) for s in (*TERMINAL, "received", "processing")
    }  # the source's own messages; id_reuse rows are listed apart
    return {
        "missing_in_ledger": sorted(source_ids - set(led)),
        "unknown_in_ledger": sorted(own - source_ids),
        "non_terminal": counts["received"] + counts["processing"],
        "open_ids": ledger.open_ids(tenant),
        "id_reuse_rows": reused,
        "counts": counts,
        "received": len(source_ids),
    }
