"""Fake-adapter interface (stage 1: the contract; the in-memory fakes in fakes.py implement it). Standard library only.

Each Port is the seam a real adapter (a mid-market ERP, a bank file, a phone-call task) would implement. The fakes are
FAULT-INJECTING and mimic duplicate-key semantics; real systems differ (many ERPs have no idempotency keys at all, keys
expire, and some have no unique index on the business key). The console says so on screen.

Idempotency semantics every fake implements (R-APEXC-023/024; stage-2 tests: 2x, 3x, and N threads on one instance)
  1. same idempotency key, same payload        -> original result, outcome "duplicate_ignored", nothing applied again
  2. same idempotency key, different payload   -> IdempotencyConflict, nothing applied
  3. new key, same business key (unique index) -> DuplicateBusinessKey, nothing applied. Business key of a payment entry:
     (vendor_id, norm_number, currency, total_minor). A SECOND unique index on (vendor_id, po_key, currency, total_minor,
     received day) raises DuplicateExposure. BOTH indexes are bypassed only by a `duplicate_ruling_id` that the classifier's ruling
     check accepted (an exact duplicate needs a controller's ruling): the ruling pays once more, never twice (rules.check_unique).
  4. fault "timeout_after_apply" / "error_5xx_after_apply": the effect IS applied, the caller sees AdapterTimeout /
     AdapterError with `ambiguous=True`; the caller must `lookup` before any retry (outcome "unknown" until reconciled)
  5. fault "timeout_before_apply": nothing applied; a retry is safe
  6. fault "duplicate_key_replay": the port delivers the same request twice to itself (rule 1 must absorb it)
  7. fault "partial_failure": enqueue wrote the header but not the lines; `lookup` shows status "incomplete" and only a
     human repairs it. Retries are bounded (max 2) and then the case is handed back.

Release (enqueue) key = release_key(tenant, invoice_id): one key per tenant and invoice id, no editable field in it. The generic
helper idem_key(action, vendor_id, invoice_id, norm_number, amount, reason_id) serves the other ports; `reason_id` is NEVER an approval
id. Values: hold -> the hold reason; callback -> the topic; route_for_approval -> proposal kind + ":" + sha256(sorted exception
types)[:12].

Time: every port takes a `Clock` (read-only `now()`). The advance handle exists only in the test harness class, never in this
module and never on a production port; no tool and no model reply can move the clock.
Concurrency: fault-schedule call indices are assigned under a lock, so tests with N threads assert order-independent
properties only (1 applied, the rest duplicate_ignored; counts), never which thread saw which fault.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal, Protocol

from apexc.normalise import minor as parse_minor
from apexc.normalise import norm_number
from apexc.rng import Rng, fnv1a

FaultKind = Literal["timeout_before_apply", "timeout_after_apply", "error_5xx_after_apply", "duplicate_key_replay", "partial_failure"]
FAULT_KINDS: tuple[FaultKind, ...] = (
    "timeout_before_apply",
    "timeout_after_apply",
    "error_5xx_after_apply",
    "duplicate_key_replay",
    "partial_failure",
)
CallOutcome = Literal["applied", "duplicate_ignored", "fault_injected"]


class AdapterError(Exception):
    def __init__(self, msg: str, *, ambiguous: bool) -> None:
        super().__init__(msg)
        self.ambiguous = ambiguous


class AdapterTimeout(AdapterError):
    pass


class IdempotencyConflict(Exception):
    pass


class DuplicateBusinessKey(Exception):
    pass


class DuplicateExposure(Exception):
    pass


@dataclass(frozen=True)
class Amount:
    """Money: integer string in MINOR units plus ISO-4217 currency. No floats. Arithmetic across currencies raises
    (HZ-13): there is no conversion anywhere."""

    minor: str
    currency: str

    def __post_init__(self) -> None:
        # canonical integer string only ("1_000", "+5", " 5 ", non-ASCII digits and floats are refused; "0100" becomes "100"), so
        # the business key and the duplicate checks that compare these strings cannot be dodged by spelling
        object.__setattr__(self, "minor", str(parse_minor(self.minor)))

    def _same(self, other: Amount) -> int:
        if not isinstance(other, Amount):
            raise TypeError("Amount operand required")
        if other.currency != self.currency:
            raise ValueError("cross-currency arithmetic is refused")
        return int(other.minor)

    def __add__(self, other: Amount) -> Amount:
        return Amount(str(int(self.minor) + self._same(other)), self.currency)

    def __sub__(self, other: Amount) -> Amount:
        return Amount(str(int(self.minor) - self._same(other)), self.currency)

    def __lt__(self, other: Amount) -> bool:
        return int(self.minor) < self._same(other)

    def __le__(self, other: Amount) -> bool:
        return int(self.minor) <= self._same(other)


class Clock(Protocol):
    def now(self) -> str: ...  # YYYY-MM-DDTHH:MM:SSZ


@dataclass(frozen=True)
class FaultStep:
    call_index: int  # 1-based index of the call to this port (all ops counted together)
    fault: FaultKind


@dataclass(frozen=True)
class FaultSchedule:
    """Seeded and reproducible. `from_seed`: SplitMix64 stream seeded with fnv1a("<port>:<seed>"); for each call index
    1..n_calls draw u = randint(0, 99); if u < rate_pct draw kind = kinds[randint(0, len(kinds)-1)]."""

    seed: int
    steps: tuple[FaultStep, ...] = ()

    @classmethod
    def from_seed(
        cls, seed: int, port: str, n_calls: int = 24, rate_pct: int = 25, kinds: tuple[FaultKind, ...] = FAULT_KINDS, min_faults: int = 1
    ) -> FaultSchedule:
        rng = Rng(fnv1a(f"{port}:{seed}"))
        steps = []
        for i in range(1, n_calls + 1):
            if rng.randint(0, 99) < rate_pct:
                steps.append(FaultStep(i, rng.choice(kinds)))
        while len(steps) < min_faults:  # every scenario exercises at least one fault
            i = rng.randint(1, n_calls)
            if all(s.call_index != i for s in steps):
                steps.append(FaultStep(i, rng.choice(kinds)))
        return cls(seed, tuple(sorted(steps, key=lambda s: s.call_index)))

    def fault_at(self, call_index: int) -> FaultKind | None:
        return next((s.fault for s in self.steps if s.call_index == call_index), None)


@dataclass(frozen=True)
class CallResult:
    call_id: str
    port: str
    op: str
    idempotency_key: str
    ts: str
    outcome: CallOutcome
    fault: FaultKind | None = None
    ticket_id: str | None = None  # callbacks only


PaymentEntry = (
    dict  # the payments request the executor builds: vendor_id, invoice_id, invoice_number, currency, total_minor, po_key, received_day,
)
# submitted_by, payee_binding (rules.payee_binding of the master as it is at call time), duplicate_ruling_id (only the ledgered one)


def idem_key(action: str, vendor_id: str, invoice_id: str, invoice_number: str, amount: Amount, reason_id: str) -> str:
    parts = (action, vendor_id, invoice_id, norm_number(invoice_number), amount.minor, amount.currency, reason_id)
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def release_key(tenant: str, invoice_id: str) -> str:
    """B2/M-5: ONE release key per (tenant, invoice id). It carries no editable field (no invoice number, amount or vendor), so editing
    the invoice after a release can never produce a second key and a second payment, and two tenants that reuse an invoice id on a
    shared queue never share a key."""
    return hashlib.sha256(chr(31).join(("enqueue", tenant, invoice_id, "release")).encode()).hexdigest()


class ErpPort(Protocol):
    """What the executor and the classifier context need from an ERP (FakeErp implements it). Reads are the source of truth for authority
    fields. Every WRITE takes the calling identity and is authorised (rules.authorize_op) first. Writes are limited to holds, receipt
    reservations and the decision ledgers (clears, approvals, rulings, rejections, callbacks); there is NO method that creates, edits or
    deletes a vendor, a bank account, a PO or an invoice amount."""

    def read_case(self, invoice_id: str) -> dict: ...  # a FRESH read: invoice, vendor master, history, rulings, callbacks, directory
    def all_vendors(self) -> list[dict]: ...
    def vendor_by_account(self, account_key: str) -> list[dict]: ...
    def cross_vendor_history(self, vendor_id: str) -> list[dict]: ...
    def set_hold(self, identity: str, invoice_id: str, reason: str, key: str) -> CallResult: ...  # actor is always "system"
    def lift_hold(self, identity: str, invoice_id: str, reason: str, by: str, evidence: dict | None = None) -> bool: ...
    def open_holds(self, invoice_id: str) -> list[str]: ...
    def hold_rows(self, invoice_id: str) -> dict[str, dict]: ...
    def reserve_receipt(self, identity: str, po_id: str, line: int, qty: int, invoice_id: str, available: int) -> bool: ...
    def record_clear(self, identity: str, rec: dict) -> None: ...
    def record_approval(self, identity: str, rec: dict) -> dict: ...
    def consume_approvals(self, identity: str, ids: list[str]) -> bool: ...
    def add_ruling(self, identity: str, row: dict) -> None: ...
    def record_rejection(self, identity: str, rec: dict) -> None: ...  # append-only; applied as an overlay on read
    def add_callback(self, identity: str, rec: dict) -> None: ...  # append-only: a record id is never replaced


class PaymentsPort(Protocol):
    """A payment QUEUE (what a treasury run would later pick up). It never sends money."""

    def enqueue(self, identity: str, entry: PaymentEntry, idempotency_key: str, rulings: list[dict]) -> CallResult: ...
    def dequeue(self, identity: str, idempotency_key: str) -> str: ...  # the declared undo; allowed until rules.undo_window_open is False
    def lookup(self, idempotency_key: str) -> dict | None: ...  # {"status": "queued|incomplete|dequeued", ...} or None
    def count_by_business_key(self, vendor_id: str, norm_number: str, currency: str, total_minor: str) -> int: ...


class CalloutPort(Protocol):
    """Simulated out-of-band callback. Constructed with an ERP and a Clock: it reads `contact.verified_phone` from the vendor master
    itself (the destination is NOT a parameter). The script comes from `callback_templates` (policy.json): the caller passes a template
    id and slot values; slot values are validated against each slot's regex and come only from structured fields."""

    def request_confirmation(self, identity: str, vendor_id: str, template_id: str, slots: dict[str, str], key: str) -> CallResult: ...
    def attest(self, identity: str, key: str, attested_by: str, state: str = "confirmed") -> dict: ...  # appends ONE ledger record


class DirectoryPort(Protocol):
    """Identity and roles of the people who submit, edit the master, attest, approve. One user_id is one person and one
    channel identity. Never derived from free text."""

    def user(self, user_id: str) -> dict | None: ...  # {"user_id", "name", "roles": [...]}
    def users_with_role(self, role: str) -> list[str]: ...  # snapshot taken at plan creation and stored in the plan
