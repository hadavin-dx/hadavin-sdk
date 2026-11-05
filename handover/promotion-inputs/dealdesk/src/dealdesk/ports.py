"""Ports the demo talks to. Spec only: protocols; the fault-injecting fakes (`adapters/fake_*.py`) come in stage 2.

CRM, billing and identity are READ-ONLY by construction: no write method exists, and a test asserts it (HZ-10).
Fakes mimic common duplicate-key semantics and are not a model of any real system; real systems differ (retry windows, key scoping,
eventual consistency). The console says so.

Idempotency: every effect carries a business-scoped key from `canon.idem_key` (canonical-JSON array of action, deal_id, terms_hash, then
lane+epoch or epoch). A unique index on the key (channel, draft sink, store) makes a replay return the first record with `duplicate_ignored`.
The key's epoch moves when an earlier approval for the same (deal, terms, lane) EXPIRED or was VOIDED, so a re-request is possible and
exactly one approval per epoch is live. Timeout after apply: the caller gets no answer although the effect HAS happened; the tool records
outcome `unknown`, looks the key up (`get_by_key`) and reports the single record. It never retries blind. The key shape differs from the
frozen contract's `hash(action, business id, amount, currency, reason id)`: our terms_hash already covers amount and currency.

Seeded fault schedule (per case, `faults`): [{"port", "op", "on_call", "fault"}], fault in
  timeout_after_apply | server_error_after_apply | duplicate_key_replay | partial_failure (record stored, notification not sent: resend, one record) |
  read_timeout (reads: at most 2 retries, i.e. 3 attempts, then hand back with reason source_unavailable).
Ports: crm, billing, identity, approval_channel, draft_sink. Same seed gives the same faults.

Time: nothing reads the wall clock. `Clock.now()` returns a UTC timestamp; scripted runs advance it. Origin: a case starts at `requested_at`;
step k+1 is requested at the accepted decision time of step k; a decision's `after_h` counts from THAT step's request time.
"""

from __future__ import annotations

from typing import Literal, Protocol


class Clock(Protocol):
    def now(self) -> str: ...  # YYYY-MM-DDTHH:MM:SSZ


class CRMPort(Protocol):
    """Authority for deal owner, account name, currency, customer tier, request type, ARR, seats, plan. Notes and thread are UNTRUSTED text."""

    def get_deal(self, deal_id: str) -> dict: ...
    def find_by_account_name(
        self, name: str, owner_id: str
    ) -> list[str]: ...  # deal ids; more than one = name alone is ambiguous (R-006)
    def get_notes(self, deal_id: str) -> str: ...  # attacker-controlled
    def get_thread(self, deal_id: str) -> list[dict]: ...  # attacker-controlled


class BillingPort(Protocol):
    """Authority for list price and cost per seat, margin floor per plan (minor units, per currency), standard terms, price book version."""

    def get_pricebook(self) -> dict: ...


class IdentityPort(Protocol):
    """Authority for who is who: person to role. A role named in a message is never used. Re-read at draft time (leaver or demotion voids)."""

    def get_person(self, person_id: str) -> dict | None: ...
    def people_with_role(self, role: str) -> list[str]: ...


class ApprovalChannel(Protocol):
    """The approval transport (core `Channel` kind in stage 2). request() is idempotent by key."""

    def request(self, idempotency_key: str, request: dict) -> dict: ...  # {"approval_id", "outcome": applied|duplicate_ignored}
    def get_by_key(self, idempotency_key: str) -> dict | None: ...
    def deliver_decision(
        self, raw: dict
    ) -> dict | None: ...  # a SignedDecision as a dict, or None if the transport itself rejects it


class ProposalStore(Protocol):
    """Holds proposals (by proposal_id), approval requests and decision records. Unique index on idempotency_key."""

    def put_proposal(self, proposal: dict) -> None: ...
    def get_proposal(self, proposal_id: str) -> dict | None: ...
    def current_epoch(
        self, deal_id: str, terms_hash: str, lane: str
    ) -> int: ...  # lane is commercial|legal|finance or the literal 'draft' for quote drafts
    def last_rejection(
        self, account_id: str, lane: str
    ) -> str | None: ...  # receipt ts of the latest eligible rejection (cooldown is per account and lane)
    def mark_expired_or_void(self, approval_id: str, reason: str) -> None: ...


class Ledger(Protocol):
    """Append-only run record: audit events (hash chain), adapter calls, decision records. One chain per RUN; per-case chains concatenate
    in case_id order with prev_sha256 carried across; ids and timestamps are deterministic from (seed, case_id, kind, n)."""

    def append(self, event: dict) -> dict: ...  # returns the event with seq, prev_sha256, sha256


class PutResult(dict):
    """{"draft_id": str, "outcome": "applied" | "duplicate_ignored"}"""


class DraftSink(Protocol):
    """Where quote drafts go (a local store, not the CRM). Unique index on `idempotency_key`."""

    def put_draft(self, idempotency_key: str, draft: dict) -> PutResult: ...
    def get_by_key(self, idempotency_key: str) -> dict | None: ...


Port = CRMPort | BillingPort | IdentityPort | ApprovalChannel | DraftSink
PortOutcome = Literal["applied", "duplicate_ignored", "fault_injected"]
