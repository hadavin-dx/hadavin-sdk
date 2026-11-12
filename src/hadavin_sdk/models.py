"""Data shapes shared by every module, plus ids and canonical hashing.

Every persisted shape carries ``schema_version``. Money is ``Decimal`` (never float).
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


# The shape of `new_id("run")`: a caller-chosen run id must have it (checked in `Runtime.handle`).
RUN_ID_PATTERN = re.compile(r"run-[0-9a-f]{32}")


def _no_floats(obj: Any, path: str = "$") -> None:
    if isinstance(obj, float):
        raise ValueError(f"float at {path}: use a decimal string")  # noqa: TRY004 - a bad value
    if isinstance(obj, dict):
        for k, v in obj.items():
            _no_floats(v, f"{path}.{k}")
    elif isinstance(obj, list | tuple):
        for i, v in enumerate(obj):
            _no_floats(v, f"{path}[{i}]")


def canonical_json(obj: Any) -> str:
    """Key-order independent JSON; refuses floats so money cannot drift."""
    if isinstance(obj, BaseModel):
        obj = obj.model_dump(mode="json")
    _no_floats(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


class Shape(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1


class RunState(StrEnum):
    RECEIVED = "RECEIVED"
    WORKING = "WORKING"
    NO_ACTION = "NO_ACTION"
    PLAN_READY = "PLAN_READY"
    NEEDS_PERSON = "NEEDS_PERSON"
    DENIED = "DENIED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    EXECUTING = "EXECUTING"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    ROLLED_BACK = "ROLLED_BACK"
    STOPPED = "STOPPED"


# States a run can still move out of (runtime/runs.py ALLOWED has a transition from each). Only these keep
# their redaction map past the ordinary retention: NEEDS_PERSON has no outgoing transition, so a run parked
# there will never restore an input again and its map ages like any finished run's.
OPEN_STATES = frozenset(
    {
        RunState.RECEIVED,
        RunState.WORKING,
        RunState.PLAN_READY,
        RunState.WAITING_FOR_APPROVAL,
        RunState.EXECUTING,
        RunState.VERIFYING,
    }
)
RiskClass = Literal["read_only", "reversible", "sign_off"]
Outcome = Literal["allow", "needs_approval", "deny"]
ApprovalStatus = Literal["PENDING", "APPROVED", "REJECTED", "EXPIRED"]


class Run(Shape):
    run_id: str = Field(default_factory=lambda: new_id("run"))
    agent_id: str
    principal_id: str
    trigger_kind: Literal["event", "schedule", "user"]
    trigger_ref: str
    state: RunState = RunState.RECEIVED
    reason_code: str | None = None
    cost_usd: Decimal = Decimal(0)
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class Target(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: str
    ref: str | None = None


class Plan(Shape):
    plan_id: str = Field(default_factory=lambda: new_id("pln"))
    run_id: str
    agent_id: str
    action_id: str
    action_version: int
    risk_class: RiskClass
    inputs: dict[str, Any]
    target: Target
    idempotency_key: str
    expected_outcome: str
    created_at: datetime = Field(default_factory=now)

    @field_validator("created_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        """The hash covers created_at: one instant must serialise one way, whatever store returned it."""
        if value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value.astimezone(UTC)

    # A field added after v1 goes in this set: the hash leaves it out while it equals its default, so a plan stored
    # before the field existed re-hashes to the hash stored with it (tests/fixtures/plan_v1.json).
    _HASH_OMIT_IF_DEFAULT: ClassVar[frozenset[str]] = frozenset()

    def hash(self) -> str:
        # Normalised here too: model_copy(update=...) and attribute assignment skip the validator.
        plan = self.model_copy(update={"created_at": self._utc(self.created_at)})
        data = plan.model_dump(mode="json")
        for name in self._HASH_OMIT_IF_DEFAULT:
            if getattr(plan, name) == type(self).model_fields[name].get_default(
                call_default_factory=True, validated_data=dict(plan)
            ):
                data.pop(name, None)
        return sha256_hex(data)


class GateDecision(Shape):
    run_id: str
    plan_hash: str
    outcome: Outcome
    rule_id: str
    ts: datetime = Field(default_factory=now)


class ChainStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approver_ids: list[str]
    timeout_s: int


class ApprovalRequest(Shape):
    approval_id: str = Field(default_factory=lambda: new_id("apr"))
    run_id: str
    plan_hash: str
    risk_class: RiskClass
    chain_id: str
    steps: list[ChainStep]
    current_step: int = 0
    status: ApprovalStatus = "PENDING"
    step_expires_at: datetime
    requested_by: str
    summary: str
    created_at: datetime = Field(default_factory=now)
    sent_at: datetime | None = None  # None: the channel send failed; tick resends
    channel_ref: str | None = None  # the channel's message id (Slack: the message ts), for updates


class ApprovalDecision(Shape):
    approval_id: str
    plan_hash: str
    step: int
    decision: Literal["approve", "reject"]
    approver_id: str
    channel: str
    reason: str = ""
    decided_at: datetime = Field(default_factory=now)


class AuditEvent(Shape):
    """Hashes and codes only: never payload text."""

    event_id: str = Field(default_factory=lambda: new_id("evt"))
    ts: datetime = Field(default_factory=now)
    run_id: str
    domain: str
    operation: str
    principal: str
    source: str
    object_ref: str | None = None
    inputs_hash: str | None = None
    decision: str | None = None
    rule_id: str | None = None
    result: str | None = None
    error_code: str | None = None
    # Which control caught a mistake: gate, recheck, abstain, guard, verify, human_label, human_reject (K6 sets
    # the human values). Rows written before this field existed hash unchanged (the chain hashes stored text).
    caught_by: str | None = None
    # A tool call's audit event carries the SHA-256 of the output text as STORED (redacted, truncated), so a
    # later edit of the `tool_calls` row is detectable against the chain. None for every other event.
    output_hash: str | None = None
    # The gate's decide event carries the hash of the plan's inputs with their placeholders restored, so an
    # approval is bound to the real values and execution refuses a map that changed since (R6, before K8).
    restored_hash: str | None = None
    # A tool call's audit event also says how many lines it returned (who: `principal`; what: the tool and
    # `inputs_hash`; why: the run's trigger; how much: `rows`), so a client can review every read.
    rows: int | None = None


class DeadLetter(Shape):
    run_id: str
    reason: str
    errors: list[str]
    ts: datetime = Field(default_factory=now)


class TickState(BaseModel):
    """One tick step's last run (table tick_state)."""

    model_config = ConfigDict(extra="forbid")
    step: str
    last_run_at: datetime
    last_ok_at: datetime | None = None
    last_error: str | None = None


class ToolCallRecord(BaseModel):
    """One read-tool call of a run (table tool_calls). Inputs and output are stored redacted (design 6.3)."""

    model_config = ConfigDict(extra="forbid")
    call_id: str  # "<run_id>:<n>"
    run_id: str
    tool: str
    inputs: dict[str, Any]
    output: str  # redacted, then truncated
    output_sha256: str  # of the raw bytes the tool received, up to the fetch cap
    created_at: datetime = Field(default_factory=now)
    duration_ms: int | None = None
    attempt: int | None = None
    error: bool = False  # the tool failed: the row is kept but is never evidence


class KillSwitch(Shape):
    on: bool = False
    by: str | None = None
    ts: datetime = Field(default_factory=now)


class GateRun(Shape):
    agent_id: str
    model_id: str
    prompt_sha256: str
    config_hash: str
    golden_sha256: str
    n: int
    passed: int  # items that passed (k == 1) or passed all k runs (k > 1)
    pass_rate: float  # pass@1: passing (item, run) pairs / (n * k)
    threshold: float
    green: bool
    ts: datetime = Field(default_factory=now)
    # K1a: defaults keep lines written before pass^k parseable.
    k: int = 1
    # Share of items passing all k runs; None when k == 1.
    pass_k: float | None = None
    # (item, run) pairs with no proposal / (n * k), traps included.
    abstain_rate: float | None = None
    # Decimal, not Money: models.py must not import config.py.
    cost_per_task_usd: Decimal | None = None
    # Set by the replay check (K1b).
    baseline_pass_rate: float | None = None
    # One-sided 95 % Clopper-Pearson upper bound on the failure rate.
    upper_error_bound: float | None = None


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    input: dict[str, Any]


class Reply(Shape):
    text: str = ""
    tool_calls: list[ToolCall] = []
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal(0)
    model_id: str
    stop_reason: str = "end_turn"
    latency_ms: int = 0


class Verdict(Shape):
    flagged: bool
    score: float = Field(ge=0.0, le=1.0)
    backend: str
    reason_code: str | None = None
    cost_usd: Decimal = Decimal(
        0
    )  # a model-backed detector's call (llm_judge), charged by the caller


class RunResult(Shape):
    outcome: Literal["succeeded", "failed", "unknown"]
    external_ref: str | None = None
    error_code: str | None = None
    retryable: bool = False


# --- inbound ledger (AK-G2-a): the saved record of every message that should start work -----------------------------
INBOUND_STATES = ("received", "claimed", "done", "needs_person", "refused")
INBOUND_OPEN_STATES = frozenset({"received", "claimed"})
INBOUND_FINAL_STATES = frozenset({"done", "needs_person", "refused"})
# Reasons added by the ledger itself (a message the ledger refused or handed to a person).
INBOUND_REASONS = frozenset(
    {
        "id_reuse",
        "attempts_exhausted",
        "body_missing",
        "body_mismatch",
        "run_interrupted",
        "run_limits",
        "run_mismatch",
        "run_needs_person",
    }
)
# A failed try that goes back to the queue (never a final state).
INBOUND_RETRY_REASONS = frozenset({"step_error", "audit_unavailable"})
INBOUND_REFUSED_REASONS = frozenset({"invalid_input", "forbidden", "duplicate", "id_reuse"})
INBOUND_NEEDS_PERSON_REASONS = frozenset(
    {
        "low_quality",
        "unreadable",
        "over_budget",
        "meter_unavailable",
        "masking_refused",
        "outbound_refused",
        "policy",
        "attempts_exhausted",
        "body_missing",
        "body_mismatch",
        "run_interrupted",
        "run_limits",
        "run_mismatch",
        "run_needs_person",
    }
)
# The state moves the ledger allows. `needs_person -> received` is the re-run owner's alone (a database rule).
INBOUND_ALLOWED: dict[str, frozenset[str]] = {
    "received": frozenset({"claimed"}),
    "claimed": frozenset({"claimed", "received", "done", "needs_person", "refused"}),
    "needs_person": frozenset({"received"}),
}
INBOUND_NAME = re.compile(r"[a-z][a-z0-9_-]{0,39}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX16 = re.compile(r"[0-9a-f]{16}")
_CLAIM_TOKEN = re.compile(r"clm-[0-9a-f]{32}")


def inbound_reason_allowed(state: str, reason: str | None) -> bool:
    """The `reason` a receipt in `state` may carry (one list, mirrored by the migration's CHECK)."""
    if state == "refused":
        return reason in INBOUND_REFUSED_REASONS
    if state == "needs_person":
        return reason in INBOUND_NEEDS_PERSON_REASONS
    return reason is None


def check_inbound_move(frm: str, to: str) -> None:
    """Like `runtime/runs.py:check`, without its "STOPPED is always allowed" exception: `done` and `refused` are final."""
    if to not in INBOUND_ALLOWED.get(frm, frozenset()):
        raise ValueError(f"inbound receipt: {frm} -> {to} is not allowed")


class InboundReceipt(Shape):
    """One saved message record (table inbound_receipts). Only keyed hashes of the sender's id and text; the text
    itself lives in its own table and is deleted on a schedule."""

    tenant: str
    source: str  # the ledger name of the inbound address
    readers: frozenset[str]
    delivery_key: str
    body_sha256: str
    key_check: str
    generation: int = Field(default=0, ge=0, le=65535)
    run_id: str | None
    state: Literal["received", "claimed", "done", "needs_person", "refused"] = "received"
    reason: str | None = None
    last_reason: str | None = None
    attempts: int = Field(default=0, ge=0)
    lease_until: datetime | None = None
    claim_token: str | None = None
    reuse_of: str | None = None
    received_at: datetime
    updated_at: datetime

    @property
    def item_id(self) -> str:
        return "inb-" + self.delivery_key[:32]

    @model_validator(mode="after")
    def _legal(self) -> InboundReceipt:
        if not INBOUND_NAME.fullmatch(self.tenant) or not INBOUND_NAME.fullmatch(self.source):
            raise ValueError("inbound receipt: bad tenant or source name")
        if not self.readers or not all(isinstance(r, str) and r for r in self.readers):
            raise ValueError("inbound receipt: readers must be a non-empty set of names")
        for value, pattern, what in (
            (self.delivery_key, _HEX64, "delivery_key"),
            (self.body_sha256, _HEX64, "body_sha256"),
            (self.key_check, _HEX16, "key_check"),
        ):
            if not pattern.fullmatch(value):
                raise ValueError(
                    f"inbound receipt: {what} is not lower-case hex of the right length"
                )
        if self.reuse_of is not None and not _HEX64.fullmatch(self.reuse_of):
            raise ValueError("inbound receipt: reuse_of is not lower-case hex")
        if self.run_id is not None and not RUN_ID_PATTERN.fullmatch(self.run_id):
            raise ValueError("inbound receipt: run_id has the wrong shape")
        if (self.reuse_of is None) != (self.run_id is not None):
            raise ValueError("inbound receipt: only an id-reuse row has no run id")
        if not inbound_reason_allowed(self.state, self.reason):
            raise ValueError(
                f"inbound receipt: reason {self.reason!r} is not allowed in state {self.state}"
            )
        if self.last_reason is not None and self.last_reason not in INBOUND_RETRY_REASONS:
            raise ValueError("inbound receipt: last_reason must be a retry reason")
        if (self.state == "claimed") != (
            self.lease_until is not None and self.claim_token is not None
        ):
            raise ValueError(
                "inbound receipt: a lease and a claim token exist exactly when claimed"
            )
        if self.claim_token is not None and not _CLAIM_TOKEN.fullmatch(self.claim_token):
            raise ValueError("inbound receipt: claim_token has the wrong shape")
        return self


class InboundRunView(BaseModel):
    """The seven run columns dispatch may read (the narrow read: the dispatch login has no right on the rest)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str
    agent_id: str
    principal_id: str
    trigger_ref: str
    state: RunState
    reason_code: str | None
    updated_at: datetime
