"""The single governed write path (purpose-and-blast-radius rule (3); design reviews 6 and 7). Nothing here moves real money: `apply` writes the SQLite store, which stands in
for a processor behind the same Protocol (a client build calls the processor with the SAME business key as its idempotency key).

execute(request, approval, identity, dry_run=True) checks, in this order, and every refusal is a TYPED outcome (garbage never raises):
  1 identity     `identities.authorize` for a money action; the agent, the approver, the sweeper... are refused (IDENTITY_DENIED) before anything is parsed.
                 This is a LABEL check on a caller-asserted string, not authentication. `identity` has no default: an omitted identity is IDENTITY_DENIED.
  2 request      shapes and lengths (ids [a-z0-9-]{1,40}, <= config.MAX_LINES lines, <= 20 DISTINCT cluster ids, bounded printable text with no
                 combining mark, invisible filler or exotic space), canonical amount, supported currency, canonical non-negative basis whose `request`
                 equals the amount, a basis that is plain JSON; the business key -> KEY_INVALID / money codes. The CLUSTER is supplied by the caller
                 and is hash-bound but not re-derived here (see "signed claim" below).
  3 clock        the injected server clock: ISO with a zone, inside 2000..2100, never behind the last APPLIED reading (CLOCK_INVALID / CLOCK_BACKWARDS)
  4 replay       (tenant, key) already applied -> duplicate_ignored with THIS tenant's record; same key with other parameters -> KEY_REUSED.
                 Then a VOIDED key (WriteGate.void wrote a tombstone) -> KEY_VOIDED: a void is a withdrawal, not only a cap release.
  5 kill switch  persisted, with operator and reason -> held (never void). A replay (4) is answered even with the switch on.
  6 OVER_CAP     before any approval is looked at
  7 approval     one-use, MAC-verified. The args hash covers tenant, action, order, lines, amount, currency, key, customer, BENEFICIARY, CLUSTER, REQUESTER,
                 tier, basis and request time; the signed tier and request time must equal the request's; TTL on the server clock; the tier must be at least
                 what THIS code computes from the signed basis plus what the store applied (cumulative) and the signed risk floor; approver matrix; requester
                 != approver (approval.py). A typed code otherwise.
  8 backstop     read from the STORE plus the signed basis and tied to config.LIMITS: LINE_COMPENSATED, GOODWILL_ALREADY, OVER_REFUNDABLE, ORDER_CAP,
                 CUSTOMER_CAP, DAY_CAP (applied today + other reservations younger than the approval TTL + this). Conservative: the signed prior amounts
                 plus what this store applied since can double count, which only ever denies more.
  9 apply        applied row + consumed approval (with the requester, the ordered approvers and the executing identity) + compensation record +
                 audit rows in ONE transaction. dry_run (the default) writes no applied row, consumes no approval and does not move the clock ratchet;
                 a REFUSAL is audited in dry_run too (the audit row records the attempt, not a payment).
`APPROVAL_USED` (an approval id already consumed under another key) is defence in depth: through this API the key is inside the hash, so a different key
fails as ARGS_HASH_MISMATCH first; it can only fire on state recovered from another copy of the store.
The execution-layer outcomes IDENTITY_DENIED, NO_APPROVAL, APPROVAL_INVALID, APPROVAL_USED, CLOCK_INVALID, CLOCK_BACKWARDS, STORE_BUSY, KEY_VOIDED, KILL_SWITCH are not
pre-gate deny codes (they are not in config.DENY_RULE); every other code is.
Global state, said plainly: the kill switch, the clock ratchet, the audit chain and `sweep` are per STORE, not per tenant.

AUDIT, exactly what is and is not written. Every refusal of execute, set_kill_switch, void and sweep writes ONE `refused` row (code, key or "-", the caller's identity label, tenant or "-"; no
customer data): IDENTITY_DENIED, the request-shape codes, CLOCK_*, KEY_REUSED, KILL_SWITCH (held), the cap and approval codes. NOT written: a
`duplicate_ignored` replay (an answer, not a refusal) and STORE_BUSY (no write lock, so nothing can be written). execute, set_kill_switch,
void and sweep ALL return a typed STORE_BUSY deny when the lock is not free within config.STORE_LOCK_TIMEOUT_S; none of them raises. The Desk's
pre-gate denies (Desk.propose) and PENDING_CAP write no audit row: they are not write-path refusals. The rows are unrated: a caller can add
a row per bad call, so a client build puts RateCap (guards.py) in front. `applied` and `intent` rows carry the approval id, the requester, the ordered
approvers (normalised ids), the tier and the executing identity; `Store.who_approved` answers "who approved this?" from the approvals table.

SIGNED CLAIM, NOT RE-VERIFIED. The basis (captured, prior order/customer/refunded amounts, tier floor) and the cluster are supplied by the proposer (the
pre-gate), bound into the args hash and signed over by the approver. This path does NOT re-read the processor or the orders: a compromised proposer can
supply zeros and the approver signs a hash of them. Stage 2: the gate signs its own request, the executor re-reads the processor, and the approver UI
shows the decoded fields. Caps are PER CURRENCY (no cross-currency total exists); the sums here read this store plus the signed claim.

PROCESSOR-CALL PLACEMENT (R-REF-024; NOT built in stage 1, where the store row IS the refund). Stage 1 writes `intent` and `applied` in ONE transaction,
which is atomic but not write-ahead. A client build must NOT call the processor inside this transaction (it would hold the store-wide write lock across
a network call, and a rollback would hide an intent whose money moved). The build is: (A) one transaction: checks, `intent` row, commit; (B) the
processor call with the business key as the idempotency key, outside any transaction; (C) a second transaction: applied row, consume approval, release,
compensation record, `applied` audit row. A crash between A and C leaves an intent with no applied row, which reconciliation resolves by lookup_by_key
(R-REF-020). Two executors must not both pass A and B for one key: a real build uses core's `actions/outbox.py` (attempt rows, compare-and-set settle, IN_DOUBT; see CORE_COPIES.md) rather than hand-rolling A/B/C. There is no queue, worker or outbox here: the path is synchronous, one lock (an RLock plus SQLite BEGIN IMMEDIATE).
"""

from __future__ import annotations

import functools
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from refunds import identities, textnorm
from refunds.adapters.ports import KeyInvalid, business_key, valid_id
from refunds.approval import ApprovalVerifier, norm
from refunds.config import (
    APPROVAL_TTL_S,
    CLOCK_MAX,
    CLOCK_MIN,
    EXPOSURE_WINDOW_S,
    LIMITS,
    MAX_LINES,
    REASON_MIN,
    REQUESTED_AT_MAX,
    TEXT_MAX,
    tier_for,
)
from refunds.hashing import args_hash
from refunds.identity import MAX_CLUSTER_SIZE
from refunds.money import MoneyError, parse_minor, parse_nonneg
from refunds.store import StoreBusy
from refunds.storeport import StorePort

ACTION_TO_IDENTITY_ACTION = {
    "refund": "payments.refund",
    "goodwill": "payments.credit",
    "cancel": "orders.cancel",
    "reship": "orders.reship",
}
FMT = "%Y-%m-%dT%H:%M:%SZ"
REQUEST_FIELDS = (
    "tenant_id", "action", "order_id", "line_ids", "amount_minor", "currency", "customer_id", "cluster", "requested_at", "tier", "basis",
    "beneficiary", "requester",
)  # fmt: skip
BASIS_NUMBERS = ("captured_minor", "prior_order_minor", "prior_customer_30d_minor", "prior_refunded_minor")
_LABEL = re.compile(r"[a-z0-9_.-]{1,40}")  # an identity label as it may appear in an audit row; anything else is logged as "?"


def _deny(code: str) -> dict:
    return {"outcome": "denied", "code": code}


_KEY64 = re.compile(r"[0-9a-f]{64}")  # a business key is a SHA-256 hex digest


def _typed_busy(fn):
    """A writer that cannot get the store's write lock in time gets a typed STORE_BUSY deny, never an exception (an operator's emergency stop included)."""

    @functools.wraps(fn)
    def wrapper(self, *a, **kw):
        try:
            return fn(self, *a, **kw)
        except StoreBusy:
            return _deny("STORE_BUSY")

    return wrapper


def _text_ok(s: object) -> bool:
    """`textnorm.text_ok` at the config length: what the beneficiary (a customer's address, which may hold accented letters) must satisfy."""
    return textnorm.text_ok(s, TEXT_MAX)


def _ascii_text_ok(s: object) -> bool:
    """Requester, approver-side labels and operator reasons are staff or system ids: ASCII only, so a look-alike letter from another script cannot
    make a requester read as someone else (the confusables table cannot be complete; a safe charset can)."""
    return _text_ok(s) and isinstance(s, str) and s.isascii()


def hash_request(req: dict, key: str) -> str:
    """The hash an approval must carry for exactly this request. Beneficiary, cluster and requester are inside it: they feed the cluster cap and the
    approver checks, so changing them after signing must void the approval."""
    args = {
        "order_id": req["order_id"],
        "line_ids": sorted(req["line_ids"]),
        "amount_minor": req["amount_minor"],
        "currency": req["currency"],
        "beneficiary": req["beneficiary"],
        "cluster": sorted(req["cluster"]),
        "requester": req["requester"],
    }
    return args_hash(
        req["tenant_id"], req["action"], args, req["tier"], req["basis"], key, req["customer_id"], req["requested_at"]
    )


class WriteGate:
    """Holds a VERIFIER only: this object has no way to issue an approval (see approval.py for what that does and does not prove)."""

    def __init__(self, store: StorePort, verifier: ApprovalVerifier, clock: Callable[[], str]) -> None:
        self.store, self.approvals, self.clock = store, verifier, clock

    # ---------------------------------------------------------------- helpers
    def _now(self) -> datetime | str:
        try:
            dt = datetime.fromisoformat(self.clock())
            if dt.tzinfo is None:
                return "CLOCK_INVALID"
            now = dt.astimezone(UTC).replace(microsecond=0)
        except Exception:  # noqa: BLE001 - an injected clock may raise anything; it is a typed deny, never a crash
            return "CLOCK_INVALID"
        stamp = now.strftime(FMT)
        if not CLOCK_MIN <= stamp < CLOCK_MAX:
            return "CLOCK_INVALID"
        last = self.store.meta("last_clock")
        if last is not None and stamp < last:
            return "CLOCK_BACKWARDS"
        return now

    @staticmethod
    def _parse(req: object) -> tuple[dict, str] | str:
        """(clean request, business key) or a typed code. Never raises."""
        if not isinstance(req, dict) or not all(f in req for f in REQUEST_FIELDS):
            return "KEY_INVALID"
        if not isinstance(req["action"], str) or req["action"] not in ACTION_TO_IDENTITY_ACTION:
            return "KEY_INVALID"
        cluster = req["cluster"]
        if not (
            valid_id(req["customer_id"])
            and isinstance(cluster, list)
            and 0 < len(cluster) <= MAX_CLUSTER_SIZE
            and all(valid_id(c) for c in cluster)
            and len(set(cluster)) == len(cluster)
            and req["customer_id"] in cluster
        ):
            return "KEY_INVALID"
        if not (isinstance(req["line_ids"], list) and len(req["line_ids"]) <= MAX_LINES):
            return "KEY_INVALID"
        if not (
            isinstance(req["requested_at"], str)
            and len(req["requested_at"]) <= REQUESTED_AT_MAX
            and isinstance(req["tier"], str)
            and req["tier"] in ("human", "four_eyes")
        ):
            return "KEY_INVALID"
        if not (_ascii_text_ok(req["requester"]) and _text_ok(req["beneficiary"])):
            return "KEY_INVALID"
        # one word mixing Latin with Cyrillic/Greek/Armenian letters is a look-alike: refused outright
        if textnorm.mixed_script(req["beneficiary"]):
            return "KEY_INVALID"
        basis = req["basis"]
        if not (  # EXACTLY these keys, all text: nothing nested, nothing extra can ride along into the hash (or past it)
            isinstance(basis, dict)
            and set(basis) == {*BASIS_NUMBERS, "tier_floor", "request"}
            and all(isinstance(v, str) for v in basis.values())
            and basis["tier_floor"] in ("", "human", "four_eyes")
        ):
            return "KEY_INVALID"
        try:
            for k in BASIS_NUMBERS:
                parse_nonneg(basis[k])
            parse_minor(req["amount_minor"], req["currency"])
        except MoneyError as e:
            return e.code
        if (
            basis["request"] != req["amount_minor"]
        ):  # the signed `request` is the amount the approver saw: it cannot be another number or free text
            return "KEY_INVALID"
        try:
            key = business_key(
                req["tenant_id"], req["action"], req["order_id"], req["line_ids"], req["amount_minor"], req["currency"]
            )
        except KeyInvalid:
            return "KEY_INVALID"
        return req, key

    @staticmethod
    def _single_cap(req: dict, amount: int) -> str | None:
        lim = LIMITS[req["currency"]]
        return "OVER_CAP" if amount > lim.hard_cap or (req["action"] == "goodwill" and amount > lim.goodwill_cap) else None

    def _cumulatives(self, req: dict, amount: int, now: datetime) -> tuple[int, int]:
        """(order cumulative, cluster 30-day cumulative): the signed prior amounts + what this store applied since + this request."""
        b, t = req["basis"], req["tenant_id"]
        since = (now - timedelta(seconds=EXPOSURE_WINDOW_S)).strftime(FMT)
        order_cum = int(b["prior_order_minor"]) + self.store.sum_order(t, req["order_id"], req["currency"]) + amount
        cust_cum = (
            int(b["prior_customer_30d_minor"])
            + self.store.sum_customers_since(t, req["cluster"], req["currency"], since)
            + amount
        )
        return order_cum, cust_cum

    def _min_tier(self, req: dict, amount: int, now: datetime) -> str:
        """The lowest tier this code accepts: tier of the largest cumulative, raised by the signed risk floor. 'above' is left to the cap checks."""
        order_cum, cust_cum = self._cumulatives(req, amount, now)
        base = tier_for(req["currency"], max(amount, order_cum, cust_cum))
        return base if base == "above" or req["basis"]["tier_floor"] != "four_eyes" else "four_eyes"

    def _backstop(self, req: dict, key: str, amount: int, now: datetime) -> str | None:
        """Ledger first, then the money caps (the order of gate_rules.md section 1). Reads the STORE and the signed basis; conservative on purpose."""
        lim, t, oid = LIMITS[req["currency"]], req["tenant_id"], req["order_id"]
        basis = req["basis"]
        # "shipping" is NOT excluded: a second refund of the shipping charge is a line overlap like any other
        lines = set(req["line_ids"])
        for r in self.store.order_rows(t, oid):
            if r["action"] == "cancel" and req["action"] in ("refund", "reship", "cancel"):
                return "LINE_COMPENSATED"
            if (
                req["action"] in ("refund", "reship")
                and r["action"] in ("refund", "reship")
                and lines & set(_loads(r["line_ids"]))
            ):
                return "LINE_COMPENSATED"
            if req["action"] == "cancel" and r["action"] in ("refund", "reship"):
                return "LINE_COMPENSATED"
            if req["action"] == "goodwill" and r["action"] == "goodwill":
                return "GOODWILL_ALREADY"
        if req["action"] in ("refund", "cancel"):
            refunded = int(basis["prior_refunded_minor"]) + self.store.sum_order(t, oid, req["currency"], ("refund", "cancel"))
            if refunded + amount > int(basis["captured_minor"]):
                return "OVER_REFUNDABLE"
        order_cum, cust_cum = self._cumulatives(req, amount, now)
        if order_cum > lim.hard_cap:
            return "ORDER_CAP"
        if cust_cum > lim.customer_30d_cap:
            return "CUSTOMER_CAP"
        day = now.strftime("%Y-%m-%d")
        since = (now - timedelta(seconds=APPROVAL_TTL_S)).strftime(FMT)
        if (
            self.store.sum_day(t, req["currency"], day) + self.store.other_reserved(t, req["currency"], key, since) + amount
            > lim.store_day_cap
        ):
            return "DAY_CAP"
        return None

    # ---------------------------------------------------------------- the one entry point
    def execute(self, request: object, approval: object, identity: object = None, dry_run: bool = True) -> dict:
        """`identity` has no usable default: omitted (or not a string) it is IDENTITY_DENIED, so leaving it out never grants the executor's authority."""
        try:
            return self._execute(request, approval, identity, dry_run)
        except StoreBusy:
            # the write lock was not free within the timeout: a typed deny; retry later with the same key
            return _deny("STORE_BUSY")

    def _early(self, code: str, identity: object, request: object) -> dict:
        """Refuse BEFORE a key exists (identity, shape, clock): one audit row with the code and the caller's label, no request content."""
        tenant = request.get("tenant_id") if isinstance(request, dict) else None
        with self.store.transaction():
            now = self._now()
            self.store.audit(
                tenant if isinstance(tenant, str) and valid_id(tenant) else "-",
                "refused",
                {"key": "-", "code": code, "identity": _label(identity)},
                now.strftime(FMT) if isinstance(now, datetime) else "-",
            )
        return _deny(code)

    def _execute(self, request: object, approval: object, identity: object, dry_run: bool) -> dict:
        if not isinstance(identity, str) or not any(
            identities.authorize(identity, a) for a in ACTION_TO_IDENTITY_ACTION.values()
        ):
            # first: a caller that may not write learns nothing about the request
            return self._early("IDENTITY_DENIED", identity, request)
        parsed = self._parse(request)
        if isinstance(parsed, str):
            return self._early(parsed, identity, request)
        req, key = parsed
        if not identities.authorize(identity, ACTION_TO_IDENTITY_ACTION[req["action"]]):
            return self._early("IDENTITY_DENIED", identity, request)
        amount, tenant = int(req["amount_minor"]), req["tenant_id"]
        # ONE critical section: clock, replay, kill switch, approval, caps and the write (SQLite BEGIN IMMEDIATE)
        with self.store.transaction():
            now = self._now()
            if isinstance(now, str):
                return self._refuse(tenant, key, now, "-", identity)
            return self._decide(req, key, amount, tenant, now.strftime(FMT), now, approval, dry_run is not False, identity)

    def _decide(
        self,
        req: dict,
        key: str,
        amount: int,
        tenant: str,
        stamp: str,
        now: datetime,
        approval: object,
        dry_run: bool,
        identity: str,
    ) -> dict:
        row = self.store.get_applied(tenant, key)
        if row is not None:
            same = (row["action"], row["order_id"], _loads(row["line_ids"]), row["amount_minor"], row["currency"]) == (
                req["action"], req["order_id"], sorted(req["line_ids"]), amount, req["currency"],
            )  # fmt: skip
            if same:
                return {"outcome": "duplicate_ignored", "code": None, "record": _rec(row)}
            return self._refuse(tenant, key, "KEY_REUSED", stamp, identity)
        if self.store.is_voided(tenant, key):
            return self._refuse(tenant, key, "KEY_VOIDED", stamp, identity)
        if self.store.kill_switch()["on"]:
            self.store.audit(tenant, "refused", {"key": key, "code": "KILL_SWITCH", "identity": identity}, stamp)
            return {"outcome": "held", "code": "KILL_SWITCH"}
        code = self._single_cap(req, amount)
        if code is not None:
            return self._refuse(tenant, key, code, stamp, identity)
        code = self.approvals.verify(
            approval, args_hash=hash_request(req, key), tenant_id=tenant, tier=req["tier"], requested_at=req["requested_at"],
            min_tier=self._min_tier(req, amount, now), requester=req["requester"], beneficiary=req["beneficiary"], now=now,
        )  # fmt: skip
        if code is not None:
            return self._refuse(tenant, key, code, stamp, identity)
        used = self.store.approval_key(tenant, approval["approval_id"])  # type: ignore[index]
        if used is not None and used != key:
            return self._refuse(tenant, key, "APPROVAL_USED", stamp, identity)
        code = self._backstop(req, key, amount, now)
        if code is not None:
            return self._refuse(tenant, key, code, stamp, identity)
        if dry_run:  # the default: nothing is written, nothing is consumed, the clock ratchet does not move
            return {
                "outcome": "dry_run",
                "code": None,
                "would_apply": {"action": req["action"], "amount_minor": amount, "currency": req["currency"]},
            }
        rec = {
            "tenant": tenant, "key": key, "action": req["action"], "order_id": req["order_id"], "line_ids": sorted(req["line_ids"]),
            "amount_minor": amount, "currency": req["currency"], "customer_id": req["customer_id"],
            "approval_id": approval["approval_id"], "applied_at": stamp, "day": stamp[:10],
        }  # type: ignore[index]  # fmt: skip
        approvers = [{"person": norm(s["person"]), "role": s["role"]} for s in approval["steps"]]  # type: ignore[index]  # verified above
        who = {
            "approval_id": rec["approval_id"],
            "requester": norm(req["requester"]),
            "approvers": approvers,
            "tier": req["tier"],
            "executed_by": identity,
            "signer": self.approvals.signer_kind,
        }
        self.store.set_meta("last_clock", stamp)
        self.store.audit(tenant, "intent", {"key": key, **who}, stamp)
        self.store.insert_applied(rec)
        self.store.consume_approval(tenant, rec["approval_id"], key, who["requester"], approvers, req["tier"], identity, stamp)
        self.store.release(tenant, key)  # the reservation became an executed amount
        self.store.add_compensation_record(
            tenant, key,
            {"kind": "compensation_record", "for": key, "action": req["action"], "amount_minor": amount, "currency": req["currency"],
             "note": "a processor action is never taken back; a human books a compensating entry against this one"},
        )  # fmt: skip
        self.store.audit(tenant, "applied", {"key": key, "amount_minor": amount, "currency": req["currency"], **who}, stamp)
        return {"outcome": "applied", "code": None, "record": _rec(rec)}

    def _refuse(self, tenant: str, key: str, code: str, stamp: str, identity: str) -> dict:
        self.store.audit(tenant, "refused", {"key": key, "code": code, "identity": _label(identity)}, stamp)
        return _deny(code)

    # ---------------------------------------------------------------- kill switch (who, why, audited) and the reservation sweeper
    @_typed_busy
    def set_kill_switch(self, identity: str, on: bool, reason: str) -> dict:
        if not isinstance(identity, str) or not identities.authorize(identity, "killswitch.operate"):
            return self._early("IDENTITY_DENIED", identity, {})
        reason = reason.strip() if isinstance(reason, str) else reason
        # the reason goes into the audit chain: no newline, bidi or look-alike characters
        if not _reason_ok(reason) or not isinstance(on, bool):
            return self._early("KEY_INVALID", identity, {})
        # the same clock rule as a payment: valid, in the window, never behind the last applied/flipped reading
        with self.store.transaction():
            now = self._now()
            if isinstance(now, str):
                return self._refuse("-", "-", now, "-", _label(identity))
            stamp = now.strftime(FMT)
            self.store.set_kill_switch(on, identity, reason, stamp)
            self.store.set_meta("last_clock", stamp)
        return {"outcome": "ok", "code": None, "kill_switch": self.store.kill_switch()}

    @_typed_busy
    def void(self, identity: str, tenant_id: str, key: str, reason: str) -> dict:
        """Withdraw a proposal for good (rejected, withdrawn, superseded). Two effects in ONE transaction: its reservation stops holding cap now instead of
        at the TTL, and a TOMBSTONE is written, so execute refuses this key as KEY_VOIDED even if a still-valid signed approval exists. A new proposal that
        should go ahead needs a new key (other lines, amount or order). Only an identity holding `approvals.void` (the executor class) may; it audits who
        voided what and why. `key` is a 64-hex business key; `reason` is ASCII text of at least REASON_MIN characters (no names or ticket text: the chain is immutable)."""
        if not isinstance(identity, str) or not identities.authorize(identity, "approvals.void"):
            return self._early("IDENTITY_DENIED", identity, {"tenant_id": tenant_id})
        reason = reason.strip() if isinstance(reason, str) else reason
        if not (valid_id(tenant_id) and isinstance(key, str) and _KEY64.fullmatch(key) and _reason_ok(reason)):
            return self._early("KEY_INVALID", identity, {"tenant_id": tenant_id})
        with self.store.transaction():
            now = self._now()
            if isinstance(now, str):
                return self._refuse("-", "-", now, "-", _label(identity))
            n = self.store.release(tenant_id, key)
            self.store.void_key(tenant_id, key, reason, identity, now.strftime(FMT))
            self.store.audit(
                tenant_id, "voided", {"key": key, "reason": reason, "identity": identity, "released": n}, now.strftime(FMT)
            )
        return {"outcome": "ok", "code": None, "released": n}

    @_typed_busy
    def sweep(self, identity: str) -> dict:
        """Release reservations older than the approval TTL (their proposals can no longer be approved). Only the sweeper-class identities may."""
        if not isinstance(identity, str) or not identities.authorize(identity, "release"):
            return self._early("IDENTITY_DENIED", identity, {})
        with self.store.transaction():
            now = self._now()
            if isinstance(now, str):
                return self._refuse("-", "-", now, "-", _label(identity))
            older = (now - timedelta(seconds=APPROVAL_TTL_S)).strftime(FMT)
            n = self.store.sweep_reservations(older, now.strftime(FMT))
        return {"outcome": "ok", "code": None, "released": n}


def _reason_ok(reason: object) -> bool:
    """An operator reason: ASCII, printable, REASON_MIN..TEXT_MAX characters. It is written into an immutable chain, so no names, emails or ticket text."""
    return _ascii_text_ok(reason) and len(str(reason)) >= REASON_MIN


def _label(identity: object) -> str:
    return identity if isinstance(identity, str) and _LABEL.fullmatch(identity) else "?"


def _loads(raw: str) -> list:
    return json.loads(raw)


def _rec(row: dict) -> dict:
    """What a caller may see: the record of ITS tenant's action. (The store never returns another tenant's row: every read is tenant-scoped.)"""
    r = dict(row)
    r["line_ids"] = _loads(r["line_ids"]) if isinstance(r["line_ids"], str) else r["line_ids"]
    return r
