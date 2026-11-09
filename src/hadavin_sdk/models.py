"""Data shapes shared by every module, plus ids and canonical hashing.

Every persisted shape carries ``schema_version``. Money is ``Decimal`` (never float).
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, date, datetime
from decimal import ROUND_UP, Decimal
from enum import StrEnum
from typing import Any, ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from hadavin_sdk import defaults


def now() -> datetime:
    return datetime.now(UTC)


_COST_UNIT = Decimal("1E-8")


def round_cost_up(x: Decimal) -> Decimal:
    """A model call's cost rounded UP to 8 decimals (R214: never down). Refuses (`ValueError`) what the store would
    refuse after a paid call: a non-finite value (checked FIRST: `quantize` of a quiet NaN returns NaN without an
    error), a negative or minus-zero value, and one above `defaults.MAX_USD`. The value is not passed through the
    arithmetic context before `quantize`, so a 29-digit value keeps its last digit."""
    if type(x) is not Decimal:  # an exact Decimal, as `check_usd` requires
        raise ValueError("cost must be a Decimal")
    if not x.is_finite():
        raise ValueError("cost must be a finite number")
    if x.is_signed():
        raise ValueError("cost must not be negative")
    if x > defaults.MAX_USD:
        raise ValueError(f"cost must be at most {defaults.MAX_USD}")
    # `exponent` is an int for a finite value; at most 8 decimals already: keep the value as it is
    if cast(int, x.as_tuple().exponent) >= -8:
        return x
    return x.quantize(_COST_UNIT, rounding=ROUND_UP)


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

    @field_validator("cost_usd")
    @classmethod
    def _cost_rounded_up(cls, v: Decimal) -> Decimal:
        return round_cost_up(v)


class Verdict(Shape):
    flagged: bool
    score: float = Field(ge=0.0, le=1.0)
    backend: str
    reason_code: str | None = None
    cost_usd: Decimal = Decimal(
        0
    )  # a model-backed detector's call (llm_judge), charged by the caller

    @field_validator("cost_usd")
    @classmethod
    def _cost_rounded_up(cls, v: Decimal) -> Decimal:
        return round_cost_up(v)


class RunResult(Shape):
    outcome: Literal["succeeded", "failed", "unknown"]
    external_ref: str | None = None
    error_code: str | None = None
    retryable: bool = False


class SpendReservation(Shape):
    """One reserved amount of spend (P4d-b). `status` moves open -> settled / released / expired; an expired row
    holds the worst case (`settled_usd == reserved_usd`) until it is settled or released once. Amounts are exact
    Decimals at six decimal places."""

    reservation_id: str
    agent_id: str
    day: date
    run_id: str | None = None
    reserved_usd: Decimal
    status: Literal["open", "settled", "released", "expired"] = "open"
    settled_usd: Decimal | None = None
    created_at: datetime
    closed_at: datetime | None = None
    expired_at: datetime | None = None
    meta: dict[str, Any] | None = None
