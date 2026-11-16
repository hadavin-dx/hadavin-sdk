"""Inbound invoice-message intake (no message lost or double-applied no message lost or double-applied, tenant isolation tenant isolation). A fake, in-memory model of what
stage 2 must do for invoice emails and attachments:

  * WRITE-AHEAD: `receive` persists the raw message and a receipt id BEFORE anything else; a redelivery returns the same receipt.
  * AT-LEAST-ONCE processing, idempotent effects: the effect (a hold on the case) is keyed by the receipt id, so a redelivery or a
    retry after a crash mid-handler changes nothing.
  * Every message ends in a recorded TERMINAL state (processed, abstained, rejected:<reason>, dead_letter) - never "gone".
  * A poison message goes to the dead-letter list after bounded retries and never blocks the ones behind it.
  * Overload = backpressure signal + the persisted queue (the ledger itself); nothing is dropped.
  * RECONCILE compares the source's own ids with the ledger and reports every gap.
  * Every row, key and effect carries the tenant id (a tenant-scoped data layer: a key cannot be formed without a tenant)."""

from __future__ import annotations

import hashlib
import json
import threading

TERMINAL_PREFIXES = ("processed", "abstained", "rejected:", "dead_letter")
PENDING = ("received", "processing")


class _Tenant:
    """One tenant's partition: its own ledger, effects, dead letters, alerts, pending counter and lock, so a flood from one tenant never
    waits on, scans, or counts another tenant's rows (tenant isolation)."""

    def __init__(self) -> None:
        self.ledger: dict[str, dict] = {}
        self.effects: dict[str, int] = {}
        self.dead: list[str] = []
        self.alerts: list[dict] = []
        self.overflow = 0  # diagnostics (alerts, dead letters) past the cap are COUNTED here; the ledger rows stay the source of truth
        self.pending = 0
        self.lock = threading.Lock()

    def set_state(self, row: dict, state: str) -> None:
        self.pending += (state in PENDING) - (row["state"] in PENDING)
        row["state"] = state


class Intake:
    def __init__(
        self, backpressure_at: int = 500, max_attempts: int = 3, max_raw_bytes: int = 5_000_000, max_diagnostics: int = 1000
    ) -> None:
        self._t: dict[str, _Tenant] = {}
        self._meta = threading.Lock()
        self.applies = 0
        self.backpressure_at, self.max_attempts = backpressure_at, max_attempts
        self.max_raw_bytes, self.max_diagnostics = max_raw_bytes, max_diagnostics

    def _note(self, t: _Tenant, bucket: list, item) -> None:
        """Bounded diagnostics (call under the tenant lock): a flood of mismatching redeliveries cannot grow memory without limit."""
        if len(bucket) < self.max_diagnostics:
            bucket.append(item)
        else:
            t.overflow += 1

    def _tenant(self, tenant: str) -> _Tenant:
        with self._meta:
            return self._t.setdefault(tenant, _Tenant())

    # flat read-only views for tests and the reconciler (O(total); the hot paths below never use them)
    @property
    def ledger(self) -> dict[tuple[str, str], dict]:
        return {(t, m): r for t, x in list(self._t.items()) for m, r in list(x.ledger.items())}

    @property
    def effects(self) -> dict[tuple[str, str], int]:
        return {(t, m): n for t, x in list(self._t.items()) for m, n in list(x.effects.items())}

    @property
    def dead(self) -> list[tuple[str, str]]:
        return [(t, m) for t, x in list(self._t.items()) for m in x.dead]

    def alerts(self, tenant: str) -> list[dict]:
        return list(self._tenant(tenant).alerts)

    def receive(self, tenant: str, msg_id: str, raw: bytes) -> dict:
        """Write-ahead. Returns the receipt (same one for a redelivery) and whether the caller should slow down. A redelivery whose bytes
        DIFFER from the stored ones is a tamper or a source bug: the original stays, the new bytes go to the dead-letter list and an
        alert is recorded."""
        t = self._tenant(tenant)
        digest = hashlib.sha256(raw).hexdigest()
        with t.lock:
            row = t.ledger.get(msg_id)
            if row is None:
                too_big = len(raw) > self.max_raw_bytes  # an oversized body is not stored: its hash and a terminal state are
                row = {
                    "receipt": hashlib.sha256(json.dumps([tenant, msg_id]).encode()).hexdigest()[
                        :16
                    ],  # unambiguous: ("t1","m1") != ("t","1m1")
                    "raw": b"" if too_big else raw,
                    "sha256": digest,
                    "state": "rejected:too_large" if too_big else "received",
                    "attempts": 0,
                    "tenant": tenant,
                }
                t.ledger[msg_id] = row
                t.pending += not too_big
            elif row["sha256"] != digest:
                self._note(t, t.alerts, {"kind": "redelivery_mismatch", "msg_id": msg_id, "new_sha256": digest})
                self._note(t, t.dead, f"{msg_id}#mismatch-{digest[:8]}")
            return {"receipt": row["receipt"], "backpressure": t.pending >= self.backpressure_at}

    def _apply_effect(self, tenant: str, receipt: str) -> None:
        """Idempotent by (tenant, receipt): the second application is a no-op."""
        t = self._tenant(tenant)
        with t.lock:
            if receipt not in t.effects:
                t.effects[receipt] = 1
                with self._meta:
                    self.applies += 1

    def process(self, tenant: str, msg_id: str, handler, crash_after_effect: bool = False) -> str:
        """One processing attempt. `handler(raw)` returns 'processed' | 'abstained' | 'rejected:<why>' or raises (poison/crash)."""
        t = self._tenant(tenant)
        with t.lock:
            row = t.ledger[msg_id]
            if row["state"].startswith(TERMINAL_PREFIXES):
                return row["state"]  # redelivery after a terminal state changes nothing
            if row["state"] == "processing":
                return "processing"  # minor 6: another worker holds this message; running the handler twice is wasted work
            t.set_state(row, "processing")
            row["attempts"] += 1
            attempts = row["attempts"]
        try:
            out = handler(row["raw"])
            if not isinstance(out, str) or not (out in ("processed", "abstained") or out.startswith("rejected:")):
                raise ValueError("handler returned a non-terminal answer")  # bounded retries, then the dead letter: never a loop
            if out == "processed":
                self._apply_effect(tenant, row["receipt"])
            if crash_after_effect and attempts == 1:
                raise RuntimeError("crash after effect, before the terminal state was written")
        except Exception:  # noqa: BLE001 - poison or crash: bounded retries then dead letter
            with t.lock:
                if row["attempts"] >= self.max_attempts:
                    t.set_state(row, "dead_letter")
                    self._note(t, t.dead, msg_id)
                else:
                    t.set_state(row, "received")
            return row["state"]
        with t.lock:
            t.set_state(row, out)
        return out

    def drain(self, handler, crash_after_effect_for=frozenset()) -> None:
        """Process every non-terminal row until each is terminal (retries are bounded, so this ends)."""
        while True:
            todo = [
                (tn, m)
                for tn, x in list(self._t.items())
                for m, r in list(x.ledger.items())
                if not r["state"].startswith(TERMINAL_PREFIXES)
            ]
            if not todo:
                return
            for tenant, msg_id in todo:
                self.process(tenant, msg_id, handler, crash_after_effect=(tenant, msg_id) in crash_after_effect_for)

    def reconcile(self, tenant: str, source_ids: set[str]) -> dict:
        """Compare the SOURCE's own ids (mailbox UIDs, provider event ids) with the ledger: missing = in the source, not in the ledger;
        unterminal = in the ledger without a terminal state; extra = in the ledger, not in the source."""
        t = self._tenant(tenant)
        with t.lock:
            mine = set(t.ledger)
            unterminal = sorted(m for m, r in t.ledger.items() if not r["state"].startswith(TERMINAL_PREFIXES))
        return {"missing": sorted(source_ids - mine), "unterminal": unterminal, "extra": sorted(mine - source_ids)}

    def export(self, tenant: str) -> list[dict]:
        """What a tenant may see: only its own rows (the data layer filters by tenant; there is no unscoped read)."""
        t = self._tenant(tenant)
        with t.lock:
            return [{"msg_id": m, "receipt": r["receipt"], "state": r["state"], "raw": r["raw"]} for m, r in t.ledger.items()]
