"""In-memory, fault-injecting fakes for the ports in ports.py (R-APEXC-010/021/023/024/025/028/030). They mimic duplicate-key
semantics; REAL SYSTEMS DIFFER (many have no idempotency keys, keys expire, no unique business key). Every store is tenant-scoped
by construction: the tenant id is part of every key, so one tenant cannot even name another tenant's row (tenant isolation).

The Clock has NO advance method here: only the test harness subclasses it (tests/conftest.py HarnessClock)."""

from __future__ import annotations

import contextlib
import hashlib
import json
import threading

from apexc.config import ConfigHolder
from apexc.normalise import fmt_ts, norm_number, parse_ts, squeeze
from apexc.ports import (
    AdapterError,
    AdapterTimeout,
    CallResult,
    DuplicateBusinessKey,
    DuplicateExposure,
    FaultSchedule,
    IdempotencyConflict,
)
from apexc.rowstore import copy_row as copy_deep  # noqa: F401  (validated JSON copy: the core module, a temporary copy)
from apexc.rowstore import json_keys_ok  # noqa: F401
from apexc.rules import (
    authorize_op,
    callback_slots_ok,
    check_unique,
    validate_approval,
    validate_clear,
    validate_evidence,
    validate_ruling,
)
from apexc.stop_gate import EffectBlocked


class FakeClock:
    """Read-only. The advance handle exists only in the harness subclass."""

    def __init__(self, start: str) -> None:
        self._t = parse_ts(start)

    def now(self) -> str:
        return fmt_ts(self._t)


class AuditWriteError(Exception):
    pass


KIND_CEILING_FACTOR = 5  # rows per (tenant, kind, day) across all classes = 5 x the per-class cap (limits.denied_audit_per_day)


class Audit:
    """One hash chain PER TENANT (tenant isolation/segregation): a tenant's events never carry another tenant's hash, so a tenant's chain is
    byte-identical whether or not another tenant exists. Each tenant has its own list and its own lock (a flood from one tenant
    never waits on another, and an append is O(1)). Tamper-evident, not tamper-proof. A failed write raises AuditWriteError, which the
    caller must treat as a deny. The chain fields (tenant, kind, seq, prev_sha256, sha256) cannot be set by a caller. `events` is the
    flat, ordered view of every tenant's rows."""

    RESERVED = frozenset({"tenant", "kind", "seq", "prev_sha256", "sha256"})

    def __init__(self) -> None:
        self.events: list[dict] = []
        self.fail_next = False
        self.fail_kinds: set[str] = set()  # test hook: fail the write of these event kinds (an audit outage after the money moved)
        self._chains: dict[str, list[dict]] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._meta = threading.Lock()
        self._capped: dict[tuple, int] = {}
        self._kind_rows: dict[tuple, int] = {}  # review 11 N2: rows written per (tenant, kind, day), whatever the class string
        self._kind_over: dict[tuple, int] = {}
        self._cap_seen: dict[str, int] = {}  # the cap last used per kind, for suppressed_count
        self.dropped = 0  # denial rows that could not be written (an audit outage): counted, never silent

    def count_drop(self) -> None:
        with self._meta:
            self.dropped += 1

    def _tenant_lock(self, tenant: str) -> threading.Lock:
        with self._meta:
            return self._locks.setdefault(tenant, threading.Lock())

    def append(self, tenant: str, kind: str, **fields) -> dict:
        if self.RESERVED & fields.keys():
            raise ValueError("audit: a caller may not set chain fields: " + ",".join(sorted(self.RESERVED & fields.keys())))
        with self._tenant_lock(tenant):
            if self.fail_next or kind in self.fail_kinds:
                self.fail_next = False
                raise AuditWriteError("audit write failed")
            mine = self._chains.setdefault(tenant, [])
            prev = mine[-1]["sha256"] if mine else "0" * 64
            e = {"seq": len(mine) + 1, "tenant": tenant, "kind": kind, **fields, "prev_sha256": prev}
            e["sha256"] = hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest()
            mine.append(e)
            with self._meta:
                self.events.append(e)
            return e

    def append_capped(self, tenant: str, kind: str, cap: int, bucket: str, cls: str = "", **fields) -> dict | None:
        """For events an outsider can make at will (a denied attempt): at most `cap` rows per (tenant, kind, class, `bucket` = a UTC day).
        `cls` is the why-class or the actor, so one flooder uses up only its own share. Past the cap, an `audit_suppressed` row is written
        when the cap is first passed and again each time the suppressed count doubles; it carries the count so far (`suppressed`), and
        `suppressed_count` reads the rest. Events that guard an action never use this."""
        with self._meta:  # decide under the lock, write outside it (append takes the same lock)
            k = (tenant, kind, str(cls)[:40], bucket)
            kk = (tenant, kind, bucket)
            if k not in self._capped and self._kind_rows.get(kk, 0) >= KIND_CEILING_FACTOR * cap:
                # review 11 N2: a class string an outsider chooses cannot buy a new bucket once the kind has used its day: no new key is
                # stored (the dict stays bounded) and the marker says how many were turned away
                n_over = self._kind_over[kk] = self._kind_over.get(kk, 0) + 1
                mark, mark_cls, row = n_over if n_over & (n_over - 1) == 0 else 0, "*", False
            else:
                n = self._capped[k] = self._capped.get(k, 0) + 1
                n_over = n - cap
                row = n_over <= 0
                if row:
                    self._kind_rows[kk] = self._kind_rows.get(kk, 0) + 1
                mark, mark_cls = n_over if n_over > 0 and n_over & (n_over - 1) == 0 else 0, str(cls)[:40]  # 1, 2, 4, 8 ...
        if row:
            return self.append(tenant, kind, **({"cls": str(cls)[:40]} if cls else {}), **fields)
        if mark:
            self.append(tenant, "audit_suppressed", suppressed_kind=kind, bucket=bucket, cls=mark_cls, suppressed=mark)
        return None

    def suppressed_count(self, tenant: str, kind: str, bucket: str, cls: str = "") -> int:
        with self._meta:
            return max(0, self._capped.get((tenant, kind, str(cls)[:40], bucket), 0) - self._cap_seen.get(kind, 0))

    def head(self, tenant: str) -> dict:
        """The tenant's chain head (seq and hash). Tamper-evidence holds only if this value is published OUTSIDE the operator's reach
        (a witness the operator cannot rewrite): stage 2 must anchor it; in this process it proves nothing against its own operator."""
        rows = self._chains.get(tenant, [])
        return {"tenant": tenant, "seq": len(rows), "sha256": rows[-1]["sha256"] if rows else "0" * 64}

    def chain(self, tenant: str) -> list[dict]:
        return list(self._chains.get(tenant, []))

    def verify(self) -> bool:
        for rows in self._chains.values():
            prev = "0" * 64
            for e in rows:
                body = {k: v for k, v in e.items() if k != "sha256"}
                if e["prev_sha256"] != prev or hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != e["sha256"]:
                    return False
                prev = e["sha256"]
        return True


def mask_dest(x: str) -> str:
    """output masking: a destination in the audit is masked (phone: last 4 digits; email: domain only)."""
    return "***@" + x.split("@", 1)[1] if "@" in x else "***" + "".join(ch for ch in x if ch.isdigit())[-4:]


def _port_cfg(erp, pol) -> ConfigHolder:
    """A port built on an ERP that an executor already governs joins its holder at once (a forgotten `register` cannot leave a stale
    policy). Once the ERP is governed, a port on ANOTHER policy would have a private holder with no watched kill switch: that is a
    `ValueError`, never a quiet fallback. Before an executor binds the ERP it holds its own holder, replaced at `register`."""
    if erp.cfg.bound:
        if pol != erp.cfg.pol:
            raise ValueError(
                "this ERP is governed by an executor: a port cannot be built on a different policy (change it with change_config)"
            )
        return erp.cfg
    return ConfigHolder(pol)


def deny_audit(port, kind: str, **f) -> None:
    """Design M2: a refused attempt at a port leaves a masked, capped audit row BEFORE the refusal is raised. It never raises itself (a
    failed audit write must not turn a refusal into something else) and never carries a raw destination, account or free text."""
    try:
        cap = port.cfg.pol["limits"]["denied_audit_per_day"]
        port.audit._cap_seen[kind] = cap
        port.audit.append_capped(port.erp.tenant, kind, cap, port.clock.now()[:10], **f)
    except Exception:  # noqa: BLE001 - the refusal itself is what matters; the drop is COUNTED (Audit.dropped), not hidden
        with contextlib.suppress(Exception):
            port.audit.count_drop()


class _Faulty:
    """Fault schedule shared by a fake's calls; indices are assigned under a lock, so concurrent tests assert order-independent
    properties only."""

    def __init__(self, schedule: FaultSchedule | None) -> None:
        self.schedule = schedule or FaultSchedule(0)
        self._n = 0
        self._flock = threading.Lock()

    def next_fault(self) -> str | None:
        with self._flock:
            self._n += 1
            return self.schedule.fault_at(self._n)


class FakePayments(_Faulty):
    """A payment QUEUE. Unique indexes via rules.check_unique; idempotency key replay returns the original; faults per the schedule."""

    def __init__(self, tenant: str, directory: dict, pol: dict, schedule: FaultSchedule | None = None) -> None:
        super().__init__(schedule)
        self.tenant, self._cfg = (
            tenant,
            ConfigHolder(pol, directory),
        )  # replaced by the executor's shared holder when it registers this port
        self.deny_sink = None  # set by Executor.register: a refused enqueue/dequeue is audited through the executor's capped path
        self.rows: dict[str, dict] = {}
        self.applies = 0
        self.replays_absorbed = 0
        self._lock = threading.Lock()

    @property
    def pol(self) -> dict:
        return self.cfg.pol

    @property
    def directory(self) -> dict:
        return self.cfg.directory

    def enqueue(self, identity: str, entry: dict, key: str, rulings: list[dict]) -> CallResult:
        self._auth(identity, "enqueue")
        fault = self.next_fault()
        if fault == "timeout_before_apply":
            raise AdapterTimeout("timeout before apply", ambiguous=False)
        with self._lock:
            row = self.rows.get(key)
            blob = json.dumps(entry, sort_keys=True)
            if row is not None:
                if row["blob"] != blob:
                    raise IdempotencyConflict(key)
                return CallResult(row["call_id"], "payments", "enqueue", key, row["ts"], "duplicate_ignored")
            probe = {**entry, "idempotency_key": key, "norm_number": norm_number(entry["invoice_number"])}
            others = [
                {**r["entry"], "idempotency_key": k, "norm_number": norm_number(r["entry"]["invoice_number"])}
                for k, r in self.rows.items()
                if r["status"] != "dequeued"
            ]
            err = check_unique(others, probe, self.pol, self.directory, rulings)
            if err in ("DuplicateBusinessKey", "RulingReused"):
                raise DuplicateBusinessKey(err)
            if err == "DuplicateExposure":
                raise DuplicateExposure(err)
            if err == "InvalidRuling":
                raise DuplicateBusinessKey(err)
            call_id = "pay-" + hashlib.sha256(key.encode()).hexdigest()[:12]
            status = "incomplete" if fault == "partial_failure" else "queued"  # partial_failure: the header was written, the lines were not
            self.rows[key] = {"blob": blob, "entry": entry, "status": status, "call_id": call_id, "ts": "", "tenant": self.tenant}
            self.applies += 1
            if fault == "duplicate_key_replay":  # the port delivers the same request to itself again: rule 1 must absorb it
                if self.rows[key]["blob"] != blob:
                    raise RuntimeError("a replayed delivery must be byte-identical")
                self.replays_absorbed += 1
        if fault in ("timeout_after_apply", "error_5xx_after_apply", "partial_failure"):
            raise (AdapterTimeout if fault == "timeout_after_apply" else AdapterError)("ambiguous", ambiguous=True)
        return CallResult(call_id, "payments", "enqueue", key, "", "applied", fault)

    def dequeue(self, identity: str, key: str) -> str:
        self._auth(identity, "dequeue")
        with self._lock:
            row = self.rows.get(key)
            if row is None:
                return "unknown"  # not a KeyError: an unknown key is a typed answer
            if row["status"] == "queued":
                row["status"] = "dequeued"
            return row["status"]

    def queued_keys(self) -> list[str]:
        with self._lock:
            return [k for k, r in self.rows.items() if r["status"] == "queued"]

    def _auth(self, identity: str, op: str) -> None:
        if op == "dequeue":
            # review 11 N1: the undo is a safety action. It does not depend on the digest: the identity is checked against the LAST policy
            # that passed it, so a tampered configuration neither blocks the undo nor widens who may do it.
            pol = self.cfg.lkg_pol
        else:
            self.cfg.check()  # a tampered configuration fails closed here too
            pol = self.pol
        try:
            authorize_op(identity, op, pol)
        except PermissionError:
            if self.deny_sink is not None:  # review 10 M2: the one attempt the demo exists to deter leaves a row
                self.deny_sink("payments_denied", cls=str(identity)[:40], identity=str(identity)[:40], op=op)
            raise

    def queued_invoice_ids(self) -> set[str]:
        with self._lock:
            return {r["entry"]["invoice_id"] for r in self.rows.values()}

    def lookup(self, key: str) -> dict | None:
        with self._lock:
            r = self.rows.get(key)
            return None if r is None else {"status": r["status"], "call_id": r["call_id"]}

    def count_by_business_key(self, vendor_id: str, number: str, currency: str, total: str) -> int:
        with self._lock:
            return sum(
                1
                for r in self.rows.values()
                if r["status"] == "queued"
                and (r["entry"]["vendor_id"], norm_number(r["entry"]["invoice_number"]), r["entry"]["currency"], r["entry"]["total_minor"])
                == (vendor_id, norm_number(number), currency, total)
            )


class FakeErp:
    """Read side plus holds and receipt/exposure reservations; the extended accessors the classifier context needs (all vendors,
    cross-vendor history, account index, rulings, callbacks, extraction records). NO write method for vendors, POs or amounts.
    Every WRITE method takes the calling identity and calls authorize_op first (least privilege, hard rule). The ledgers the
    executor decides from live here: holds (with who lifted and on what evidence), clears, approvals, rulings, GRNs, corrections."""

    def __init__(self, tenant: str, pol: dict, clock=None) -> None:
        self.tenant, self.clock = tenant, clock
        self._cfg = ConfigHolder(pol)  # B1/M1: ONE read-only source of policy and directory; executors and ports share it
        self.vendors: dict[str, dict] = {}
        self.pos: dict[str, dict] = {}
        self.receipts: dict[str, list[dict]] = {}
        self.history: dict[str, list[dict]] = {}
        self.rulings: list[dict] = []
        self.callbacks: dict[str, dict] = {}
        self.extractions: dict[str, dict] = {}
        self.cases: dict[str, dict] = {}  # the invoice world the executor re-reads at release time
        self.holds: dict[str, list[dict]] = {}
        self.clears: list[dict] = []
        self.approvals: dict[str, dict] = {}
        self.grns: dict[str, dict] = {}
        self.corrections: dict[str, dict] = {}
        self.used_by: dict[str, str] = {}  # evidence id -> the one invoice that used it
        self.rejections: list[dict] = []  # append-only: an earlier invoice rejected by a person (never an in-place edit of history)
        self.audit = None  # optional: set by the wiring. approvals, rulings and rejections are audited strictly BEFORE they are written (a failed audit write fails the write); holds, lifts and clears are audited by the executor AFTER the write, softly (a backlog if the store is down)
        self.reserved: dict[tuple, int] = {}
        self.ports: list = []  # ports built on this ERP (callout, egress, read port): the executor pushes a config change to them too
        self._lock = threading.Lock()

    @property
    def pol(self) -> dict:
        return self.cfg.pol

    @property
    def directory(self) -> dict | None:
        return self.cfg.directory  # the ONE directory source, bound by the first Executor and moved only by change_config

    def _auth(self, identity: str, op: str) -> None:
        self.cfg.check()
        try:
            authorize_op(identity, op, self.pol)
        except PermissionError:
            if self.audit is not None:  # M6 (review 9): a denied ledger write is on the chain, capped, with a bounded identity
                try:
                    cap = self.pol["limits"]["denied_audit_per_day"]
                    self.audit._cap_seen["erp_denied"] = cap
                    self.audit.append_capped(self.tenant, "erp_denied", cap, self._now()[:10], cls=str(identity)[:40],
                                             identity=str(identity)[:40], op=str(op)[:40])  # fmt: skip
                except Exception:  # noqa: BLE001 - the refusal itself is what matters; the drop is counted, not hidden
                    with contextlib.suppress(Exception):
                        self.audit.count_drop()
            raise

    def _now(self) -> str:
        return self.clock.now() if self.clock else ""

    def read_case(self, invoice_id: str) -> dict:
        """A FRESH read of the invoice world: the stored invoice and context, with the vendor master, rulings and callback ledger
        read live from this ERP (so an edit after approval is seen)."""
        case = copy_deep(self.cases[invoice_id])
        ctx = case["context"]
        vid = ctx["vendor"]["vendor_id"] if ctx["vendor"] else None
        if vid is not None:
            ctx["vendor"] = copy_deep(self.vendors[vid])  # KeyError for a vendor no longer in the live table: never the stored snapshot
        ctx["callbacks"] = {**ctx["callbacks"], **copy_deep(self.callbacks)}
        ctx["rulings"] = copy_deep(self.rulings)
        if self.directory is not None:
            ctx["directory"] = copy_deep(self.directory)  # M2: never the stale snapshot stored with the case
        for rj in self.rejections:  # overlay: a rejection is a ledger row, applied on read
            for h in ctx["history"]:
                if h["invoice_id"] == rj["earlier_invoice_id"]:
                    h.update(status="rejected", ruling={"by": rj["by"], "role": rj["role"]})
        return case

    def _log(self, kind: str, **f) -> None:
        if self.audit is not None:
            self.audit.append(self.tenant, kind, **f)  # strict: a failed audit write fails the ledger write

    def all_vendors(self) -> list[dict]:
        with self._lock:
            return [copy_deep(v) for v in self.vendors.values()]  # copies: a reader never holds a handle on the live master

    def vendor_by_account(self, account_key: str) -> list[dict]:
        from apexc.classify import norm_acct

        with self._lock:
            return [copy_deep(v) for v in self.vendors.values() if norm_acct(v["bank"]["account"]) == account_key]

    def cross_vendor_history(self, vendor_id: str) -> list[dict]:
        with self._lock:
            return [copy_deep(h) for vid, hs in self.history.items() if vid != vendor_id for h in hs]

    def set_hold(self, identity: str, invoice_id: str, reason: str, key: str) -> CallResult:
        self._auth(identity, "hold")
        with self._lock:
            rows = self.holds.setdefault(invoice_id, [])
            if any(r["reason"] == reason for r in rows):
                return CallResult("hold", "erp", "set_hold", key, "", "duplicate_ignored")
            rows.append({"reason": reason, "open": True, "actor": "system", "placed_at": self._now(), "lifted_by": None, "evidence": None})
            return CallResult("hold", "erp", "set_hold", key, "", "applied")

    def open_holds(self, invoice_id: str) -> list[str]:
        with self._lock:
            return [r["reason"] for r in self.holds.get(invoice_id, []) if r["open"]]

    def snapshot_holds(self) -> dict[str, list[dict]]:
        """M5: a consistent deep copy of every hold row, taken under the ERP lock, so a reader never iterates a ledger a writer is growing."""
        with self._lock:
            return {i: [copy_deep(r) for r in rows] for i, rows in self.holds.items()}

    def mark_aged(self, identity: str, invoice_id: str, reason: str) -> bool:
        """Flag an open hold as escalated for age, once; True only for the call that set the flag."""
        self._auth(identity, "hold")
        with self._lock:
            for r in self.holds.get(invoice_id, []):
                if r["reason"] == reason and r["open"] and not r.get("aged"):
                    r["aged"] = True
                    return True
        return False

    def hold_rows(self, invoice_id: str) -> dict[str, dict]:
        with self._lock:
            return {r["reason"]: copy_deep(r) for r in self.holds.get(invoice_id, [])}

    def lift_hold(
        self, identity: str, invoice_id: str, reason: str, by: str, evidence: dict | None = None, clear: dict | None = None
    ) -> bool:
        """Lifts an OPEN hold once; a closed or missing hold is left exactly as it is (who lifted it and on what evidence are never overwritten).
        M4: the audit events come strictly BEFORE the writes (a failed audit write writes nothing), and an optional `clear` row is written
        together with the lift and only if the lift happens, so no clear row can exist for a lift that did nothing."""
        self._auth(identity, "lift_hold")
        if not validate_evidence(evidence):
            raise ValueError("lift evidence must be a flat dict of strings")
        if clear is not None:
            self._auth(identity, "record_clear")
            if not validate_clear(clear):
                raise ValueError("clear record has the wrong shape")
        with self._lock:
            for r in self.holds.get(invoice_id, []):
                if r["reason"] == reason and r["open"]:
                    if clear is None:
                        self._log("hold_lifted", invoice_id=invoice_id, reason=reason, by=by)
                    else:  # m4 (review 9): ONE event for the lift and its clear, so the chain can never say "lifted" for a clear that failed
                        self._log(
                            "hold_lifted", invoice_id=invoice_id, reason=reason, by=by, clear_type=clear["type"], clear_kind=clear["kind"]
                        )
                    r.update(
                        open=False, lifted_by=by, evidence=copy_deep(evidence), lifted_at=self._now()
                    )  # a copy: the caller keeps no handle
                    for v in (evidence or {}).values():
                        if isinstance(v, str):
                            self.used_by.setdefault(v, invoice_id)
                    if clear is not None:
                        self.clears.append({**clear, "ts": self._now()})
                    return True
        return False

    def record_clear(self, identity: str, rec: dict) -> None:
        self._auth(identity, "record_clear")
        if not validate_clear(rec):
            raise ValueError("clear record has the wrong shape")
        with self._lock:
            self._log(
                "clear_recorded", invoice_id=rec["invoice_id"], type=rec["type"], by=rec["by"], clear_kind=rec["kind"]
            )  # M4: audit BEFORE the write
            self.clears.append({**rec, "ts": self._now()})

    def record_approval(self, identity: str, rec: dict) -> dict:
        self._auth(identity, "record_approval")
        if not json_keys_ok(rec):  # BEFORE the JSON round trip: a tuple key raises there and an int key is silently coerced to a string
            raise ValueError("approval record may hold only string keys")
        bound = rec.get("bound")
        with self._lock:
            row = {"currency": bound.get("currency", "") if isinstance(bound, dict) else "", "single_minor": 0, **copy_deep(rec),
                   "approval_id": f"apr-{len(self.approvals) + 1}", "ts": self._now(), "consumed": False}  # fmt: skip
            if not validate_approval(row):
                raise ValueError("approval row has the wrong shape")
            self._check_bound(row)
            self._log(
                "approval_recorded", invoice_id=rec.get("invoice_id"), by=rec.get("by"), plan=rec.get("plan")
            )  # audit BEFORE the write
            self.approvals[row["approval_id"]] = row
            return copy_deep(row)

    def _check_bound(self, row: dict) -> None:
        """Design M3: the bound set is written only if it is EXACTLY what the ledgers give for this invoice now (types and cleared set
        included), so a forged superset or a stale binding is refused at the write, not only at release."""
        from apexc.rules import binding_fields, cleared_types

        inv_id = row["invoice_id"]
        if inv_id not in self.cases or self.directory is None:
            raise ValueError("approval for an invoice this ERP does not hold")
        cleared = cleared_types([c for c in self.clears if c["invoice_id"] == inv_id], self.directory, self.pol)
        if binding_fields(self.read_case(inv_id), self.pol, cleared) != row["bound"]:
            raise ValueError("the bound set is not the one the ledgers give for this invoice now")

    def consume_approvals(self, identity: str, ids: list[str]) -> bool:
        """Atomically mark approvals consumed; False if ANY is already consumed (an approval is single-use)."""
        self._auth(identity, "consume_approval")
        with self._lock:
            if any(self.approvals[i]["consumed"] for i in ids):
                return False
            for i in ids:
                self.approvals[i]["consumed"] = True
            return True

    def add_ruling(self, identity: str, row: dict) -> None:
        """A person's ruling is written to the ledger by that person's role identity (`ruling` right), stamped with the ERP clock."""
        self._auth(identity, "ruling")
        if not validate_ruling(row):
            raise ValueError("ruling has the wrong shape")
        self._log(
            "ruling_recorded", ruling_id=row.get("ruling_id"), invoice_id=row.get("invoice_id"), by=row.get("by"), ruling=row.get("ruling")
        )
        with self._lock:
            self.rulings.append({**row, "ts": row.get("ts") or self._now()})

    def add_callback(self, identity: str, rec: dict) -> None:
        """The callback ledger is APPEND-ONLY: a record id is written once and never replaced (state, attester and time stay as first written)."""
        self._auth(identity, "attest_callback")
        with self._lock:
            if rec["callback_id"] in self.callbacks:
                raise ValueError("callback ledger is append-only: " + rec["callback_id"])  # a rejected second attestation is never audited
            # design m2: the audit event comes BEFORE the record is visible, inside the lock a reader's copy would need, so no clear can ever
            # rest on an un-audited callback and there is nothing to roll back
            self._log("callback_attested", callback_id=rec["callback_id"], attested_by=rec["attested_by"], ts=rec["ts"], state=rec["state"])
            self.callbacks[rec["callback_id"]] = rec

    def record_rejection(self, identity: str, rec: dict) -> None:
        self._auth(identity, "reject")
        self._log("rejection_recorded", **{k: rec[k] for k in ("earlier_invoice_id", "by", "role")})
        with self._lock:
            self.rejections.append({**rec, "ts": self._now()})

    def reserve_receipt(self, identity: str, po_id: str, line: int, qty: int, invoice_id: str, available: int) -> bool:
        """Atomically reserve `qty` of the remaining receipt quantity for an invoice; False when it no longer fits (R-APEXC-028)."""
        self._auth(identity, "reserve_receipt")
        with self._lock:
            used = sum(v for (p, ln, _), v in self.reserved.items() if (p, ln) == (po_id, line))
            if (po_id, line, invoice_id) in self.reserved or used + qty > available:
                return (po_id, line, invoice_id) in self.reserved
            self.reserved[(po_id, line, invoice_id)] = qty
            return True


class FakeCallout:
    """Simulated out-of-band callback: the destination is READ from the vendor master here (never a parameter), the template
    slots must fullmatch their patterns, a request is idempotent by key, and an attestation writes the callback LEDGER record."""

    def __init__(self, erp: FakeErp, clock: FakeClock, pol: dict, audit: Audit) -> None:
        self.erp, self.clock, self.audit, self._cfg = erp, clock, audit, _port_cfg(erp, pol)
        self.dials: list[dict] = []
        self.tickets: dict[str, dict] = {}
        self._lock = threading.Lock()
        erp.ports.append(self)

    @property
    def pol(self) -> dict:
        return self.cfg.pol

    def _deny(self, why: str, exc: Exception, identity, **f) -> None:
        deny_audit(
            self, "callback_denied", identity=str(identity)[:40], why=why, **f
        )  # design M2: a refused request is on the chain, masked
        raise exc

    def request_confirmation(self, identity: str, vendor_id: str, template_id: str, slots: dict[str, str], key: str) -> CallResult:
        try:
            with self.cfg.effect():  # M5 (review 9): in flight until the call is placed and audited; the kill switch waits for it
                return self._request_confirmation(identity, vendor_id, template_id, slots, key)
        except EffectBlocked:
            self._deny("kill_switch", EgressDenied("kill_switch"), identity)

    def _request_confirmation(self, identity: str, vendor_id: str, template_id: str, slots: dict[str, str], key: str) -> CallResult:
        try:
            authorize_op(identity, "request_vendor_confirmation", self.pol)
        except PermissionError as e:
            self._deny("identity", e, identity)
        if not callback_slots_ok(template_id, slots, self.pol):
            self._deny("slots_rejected", ValueError("slots rejected"), identity, template=str(template_id)[:40])
        with self._lock:
            phone = self.erp.vendors[vendor_id]["contact"]["verified_phone"]
            topic = self.pol["callback_templates"][template_id]["topic"]
            if key in self.tickets:
                t = self.tickets[key]
                if (t["vendor_id"], t["topic"]) != (vendor_id, topic):  # minor 5: a key replays only the SAME request
                    self._deny("key_reused", ValueError("idempotency key reused for a different request"), identity, template=template_id)
                return CallResult(t["ticket"], "callout", "request", key, self.clock.now(), "duplicate_ignored", ticket_id=t["ticket"])
            # B1 (v7): audit BEFORE the call is placed; a failed audit write places no call and a retry with the same key starts clean
            self.audit.append(self.erp.tenant, "callback_requested", vendor_id=vendor_id, topic=topic)
            ticket = f"tk-{len(self.tickets) + 1}"
            self.tickets[key] = {"ticket": ticket, "vendor_id": vendor_id, "topic": topic, "dialed": phone, "state": "pending"}
            self.dials.append({"vendor_id": vendor_id, "dialed": phone, "topic": topic})
            return CallResult(ticket, "callout", "request", key, self.clock.now(), "applied", ticket_id=ticket)

    def attest(self, identity: str, key: str, attested_by: str, state: str = "confirmed") -> dict:
        try:
            authorize_op(identity, "attest_callback", self.pol)
        except PermissionError as e:
            self._deny("attest_identity", e, identity)
        with self._lock:
            t = self.tickets.get(key)  # the ticket is read-only from here on
        if t is None:
            raise ValueError("unknown callback ticket")
        if state not in ("confirmed", "denied"):
            raise ValueError("unknown callback state")
        if self.erp.directory is not None and attested_by not in self.erp.directory:
            raise ValueError("unknown attester")  # the attester is a named person of the directory, not a free string
        rec = {"callback_id": f"cb-{t['ticket']}", "vendor_id": t["vendor_id"], "topic": t["topic"], "state": state, "dialed": t["dialed"],
               "attested_by": attested_by, "ts": self.clock.now()}  # fmt: skip
        self.erp.add_callback(
            identity, rec
        )  # audits (callback_attested) strictly BEFORE the record exists; a second attestation is rejected unaudited
        return rec


class RateLimited(Exception):
    pass


class ConnectionRefused(Exception):
    pass


class EgressDenied(Exception):
    pass


class ReadOnlyErp:
    """The AP/ERP READ port (purpose limitation): read-only, one identity per caller, a purpose recorded for every read in the tenant's audit chain,
    a request-rate cap and a connection cap. It exposes NO write method (the test introspects). `get_vendor` returns the full record
    only to an identity that holds the `vendor` read right; an identity with `vendor_masked` gets name, status and currency."""

    def __init__(self, erp: FakeErp, audit: Audit, clock, pol: dict) -> None:
        self.erp, self.audit, self.clock, self._cfg = erp, audit, clock, _port_cfg(erp, pol)
        erp.ports.append(self)
        self._stamps: list = []
        self._open = 0
        self._lock = threading.Lock()

    @property
    def pol(self) -> dict:
        return self.cfg.pol

    def _gate(self, identity: str, obj: str, purpose: str) -> None:
        try:
            authorize_op(identity, obj, self.pol, "read")
        except PermissionError:
            deny_audit(self, "read_denied", identity=str(identity)[:40], object=obj, purpose=str(purpose)[:80], why="identity")  # design M2
            raise
        with self._lock:
            now = parse_ts(self.clock.now())
            self._stamps = [t for t in self._stamps if (now - t).total_seconds() < 60]
            limited = len(self._stamps) >= self.pol["limits"]["erp_reads_per_minute"]
            if not limited:
                self._stamps.append(now)
        if limited:
            deny_audit(self, "read_denied", identity=str(identity)[:40], object=obj, purpose=str(purpose)[:80], why="rate_limited")
            raise RateLimited(identity)
        self.audit.append(self.erp.tenant, "read", identity=identity, object=obj, purpose=purpose)  # one log row per access

    def connection(self):
        outer = self

        class _Conn:
            def __enter__(self):
                with outer._lock:
                    if outer._open >= outer.pol["limits"]["erp_connections"]:
                        raise ConnectionRefused("too many connections")
                    outer._open += 1

            def __exit__(self, *a):
                with outer._lock:
                    outer._open -= 1

        return _Conn()

    def get_vendor(self, identity: str, vendor_id: str, purpose: str) -> dict:
        full = "vendor" in self.pol["identities"].get(identity, {}).get("read", [])
        self._gate(identity, "vendor" if full else "vendor_masked", purpose)
        v = copy_deep(self.erp.vendors[vendor_id])
        return v if full else {"vendor_id": v["vendor_id"], "name": v["name"], "status": v["status"], "currency": v["currency"]}

    def get_po(self, identity: str, po_id: str, purpose: str) -> dict | None:
        self._gate(identity, "po", purpose)
        return copy_deep(self.erp.pos.get(po_id))  # design M1: a copy, never the live ERP object


class EgressGate:
    """Outbound vendor messages (purpose limitation): the destination must be the master-verified contact of THAT vendor (callback: the verified
    number, which must be on `trusted_phones`; email: `email_on_file` with no contact edit); the body is rendered from a fixed template
    with validated slots (there is no free-text send); an OUTPUT CHECK rejects any body containing a protected value (bank account,
    routing, tax id, phone, another vendor's tax id); a per-day cap; every send is audited."""

    BODIES = {
        "confirm_price": "Please confirm the price on invoice {invoice_number} ({currency} {amount_minor}).",
        "confirm_quantity": "Please confirm the quantity on invoice {invoice_number} for {po_id}.",
        "confirm_tax": "Please confirm the tax on invoice {invoice_number} ({currency} {amount_minor}).",
        "confirm_bank_details": "Please confirm the bank details on invoice {invoice_number} ending {account_last4}.",
        "confirm_new_vendor": "Please confirm your company details for invoice {invoice_number}.",
        "confirm_contact": "Please confirm your contact details for invoice {invoice_number}.",
        "confirm_master_edit": "Please confirm the recent change to your account for invoice {invoice_number}.",
        "notify_hold": "Invoice {invoice_number} is on hold for review.",
        "request_credit_note": "Please send a credit note for invoice {invoice_number}.",
    }

    def __init__(self, erp: FakeErp, clock, audit: Audit, pol: dict) -> None:
        self.erp, self.clock, self.audit, self._cfg = erp, clock, audit, _port_cfg(erp, pol)
        self.outbox: list[dict] = []
        self._lock = threading.Lock()
        erp.ports.append(self)

    @property
    def pol(self) -> dict:
        return self.cfg.pol

    def _deny(self, why: str, identity, channel, template_id, to) -> None:
        """Design M2: the refused attempt is on the chain (destination masked, capped per day) BEFORE the refusal is raised."""
        deny_audit(self, "egress_denied", identity=str(identity)[:40], channel=str(channel)[:20], template=str(template_id)[:40],
                   to=mask_dest(str(to)), why=why)  # fmt: skip
        raise EgressDenied(why)

    def send(self, identity: str, channel: str, vendor_id: str, to: str, template_id: str, slots: dict[str, str]) -> dict:
        try:
            with self.cfg.effect():  # M5 (review 9): in flight until the message is audited and in the outbox
                return self._send(identity, channel, vendor_id, to, template_id, slots)
        except EffectBlocked:
            self._deny("kill_switch", identity, channel, template_id, to)

    def _send(self, identity: str, channel: str, vendor_id: str, to: str, template_id: str, slots: dict[str, str]) -> dict:
        try:
            authorize_op(identity, "request_vendor_confirmation", self.pol)
        except PermissionError:
            deny_audit(self, "egress_denied", identity=str(identity)[:40], channel=str(channel)[:20], template=str(template_id)[:40],
                       to=mask_dest(str(to)), why="identity")  # fmt: skip
            raise
        v = self.erp.vendors.get(vendor_id)
        if v is None:
            self._deny("unknown vendor", identity, channel, template_id, to)
        c = v["contact"]
        if template_id not in self.pol["egress_templates"].get(channel, ()):
            self._deny("template not allowed on this channel", identity, channel, template_id, to)
        if channel == "callback":
            if to not in c["trusted_phones"] or to != c["verified_phone"]:
                self._deny("destination is not the master-verified number", identity, channel, template_id, to)
        elif to != c["email_on_file"] or c.get("email_changed_at"):
            self._deny("destination is not the master-verified address", identity, channel, template_id, to)
        day = self.clock.now()[:10]
        if not callback_slots_ok(template_id, slots, self.pol):  # M5: every template, email included, takes exactly its validated slots
            self._deny("slots rejected", identity, channel, template_id, to)
        body = self.BODIES[template_id].format(
            **{k: slots.get(k, "") for k in ("invoice_number", "currency", "amount_minor", "po_id", "account_last4")}
        )
        secret = {  # M5: squeezed keys (NFKC, no separators, no zero-width) of every vendor's account, routing, tax id and phones
            squeeze(x)
            for o in self.erp.all_vendors()
            for x in (
                o["bank"]["account"],
                o["bank"]["routing"],
                o["tax_id"],
                o["contact"]["verified_phone"],
                *o["contact"]["trusted_phones"],
            )
        }
        body_key = squeeze(body)
        if any(len(s) >= 6 and s in body_key for s in secret):  # 6+: the last 4 an invoice may legitimately show are never a full value
            self._deny("output check: body contains a protected value", identity, channel, template_id, to)
        msg = {"channel": channel, "to": to, "template": template_id, "body": body, "day": day, "vendor_id": vendor_id}
        with self._lock:
            sent_today = sum(1 for m in self.outbox if m["day"] == day)  # M7: a cap PER UTC DAY (resets at midnight)
            if sent_today >= self.pol["limits"]["egress_per_day"]:
                self._deny("daily egress cap", identity, channel, template_id, to)
            if (
                sum(1 for m in self.outbox if m["day"] == day and m["vendor_id"] == vendor_id)
                >= self.pol["limits"]["egress_per_vendor_per_day"]
            ):
                self._deny(
                    "daily egress cap for this vendor", identity, channel, template_id, to
                )  # one vendor's flood cannot use up the others' share
            # B1 (v7): audit BEFORE the message leaves; a failed audit write sends nothing and counts against no cap
            self.audit.append(self.erp.tenant, "egress", channel=channel, to=mask_dest(to), template=template_id)
            self.outbox.append(msg)
        return msg


for _c in (
    FakePayments,
    FakeErp,
    FakeCallout,
    ReadOnlyErp,
    EgressGate,
):  # `cfg` is read-only: only bind_cfg (the executor's _push) changes it
    _c.cfg = property(lambda self: self._cfg)
