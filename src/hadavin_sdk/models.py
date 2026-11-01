"""Data shapes shared by every module, plus ids and canonical hashing.

Every persisted shape carries ``schema_version``. Money is ``Decimal`` (never float).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


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
    # What produced this proposal (K6): the agent's config hash (levels excluded), the model and the prompt.
    # Promotion evidence counts only proposals made under the CURRENT config hash: labels on an older prompt
    # say nothing about the new one. None on plans stored before this field existed (they never count).
    config_hash: str | None = None
    model_id: str | None = None
    prompt_sha256: str | None = None

    @field_validator("created_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        """The hash covers created_at: one instant must serialise one way, whatever store returned it."""
        if value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value.astimezone(UTC)

    # A field added after v1 goes in this set: the hash leaves it out while it equals its default, so a plan stored
    # before the field existed re-hashes to the hash stored with it (tests/fixtures/plan_v1.json).
    _HASH_OMIT_IF_DEFAULT: ClassVar[frozenset[str]] = frozenset(
        {"config_hash", "model_id", "prompt_sha256"}
    )

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
    # A signed channel click (K6): the workspace it came from and its own timestamp, so a refused or accepted
    # click can be traced to both. Rows written before these fields existed hash unchanged.
    team_id: str | None = None
    action_ts: str | None = None


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
    # A step's own numbers (K6; K4's backlog step writes `oldest_received_age_s` and `late_starts`). Codes and
    # counts only, never run content. Round-trips through the store as JSONB.
    detail: dict[str, Any] | None = None


LabelName = Literal["agree", "partial", "wrong", "harmful", "abstain_ok", "missed"]


class Label(BaseModel):
    """A person's verdict on one run (table labels). Append-only: the latest eligible label of a run is its label."""

    model_config = ConfigDict(extra="forbid")
    label_id: str = Field(default_factory=lambda: new_id("lbl"))
    run_id: str
    label: LabelName
    principal_id: str
    channel: Literal["chat", "csv"]
    approved_by: str | None = None  # csv only: the line owner who approved the import
    created_at: datetime = Field(default_factory=now)
    # Insertion order, assigned by the store (None until stored). "Latest" always means the highest seq: two
    # labels can share a created_at, and a clock read before a lock can lag the commit; the order of insertion
    # cannot tie and cannot lag.
    seq: int | None = None

    @property
    def counts(self) -> bool:
        """Evidence: a chat label, or a csv label the line owner approved."""
        return self.channel == "chat" or self.approved_by is not None


class LevelEvent(BaseModel):
    """A demotion or the line owner's clear (table level_events). The latest event per (agent, action) wins."""

    model_config = ConfigDict(extra="forbid")
    seq: int | None = None  # assigned by the store
    agent_id: str
    action_id: str
    kind: Literal["demote", "clear"]
    reason: str
    by: str
    at: datetime = Field(default_factory=now)


_LABEL_COLUMNS = ("agree", "partial", "wrong", "harmful", "abstain_ok", "missed")


def iso_week(moment: datetime) -> date:
    """The Monday (UTC) of the ISO week the instant falls in: what `date_trunc('week', ... AT TIME ZONE 'UTC')` gives."""
    day = moment.astimezone(UTC).date()
    return day - timedelta(days=day.weekday())


def latest_labels(labels: list[Label]) -> dict[str, Label]:
    """run_id -> its label: the latest eligible one (a chat label, or an approved csv label), latest by insertion
    order (`seq`). A label not stored yet (no seq) is newer than any stored one."""
    out: dict[str, Label] = {}
    for lab in sorted((x for x in labels if x.counts), key=label_order):
        out[lab.run_id] = lab
    return out


def label_order(x: Label) -> tuple[float, datetime, str]:
    """Sort key for "oldest first": insertion order; a label without a seq (not stored yet) sorts last."""
    return (float("inf") if x.seq is None else x.seq, x.created_at, x.label_id)


class PilotWeek(BaseModel):
    """One ISO week of the pilot (view v_pilot_week; the memory store computes the same numbers in Python)."""

    model_config = ConfigDict(extra="forbid")
    week: date
    runs: int = 0
    proposals: int = 0
    shadow_cards: int = 0
    cards_not_delivered: int = 0
    labelled: int = 0
    agree: int = 0
    partial: int = 0
    wrong: int = 0
    harmful: int = 0
    abstain_ok: int = 0
    missed: int = 0
    abstained: int = 0
    fixes_verified: int = 0
    median_s_to_proposal: float | None = None
    avg_cost_usd: Decimal | None = None

    def count_of(self, classes: tuple[str, ...] | list[str]) -> int:
        """Runs of the week whose label is one of `classes` (the view has one column per label class)."""
        return sum(getattr(self, c) for c in classes if c in _LABEL_COLUMNS)


class ApprovalWeek(BaseModel):
    """One ISO week of approval decisions (view v_approval_week)."""

    model_config = ConfigDict(extra="forbid")
    week: date
    decisions: int = 0
    wont_run: int = 0
    median_s: float | None = None


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
