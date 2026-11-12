"""Store Protocol: Hadavin-owned rows. ``memory`` now, ``postgres`` when Portal v0 or S11 needs it."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Protocol

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    DeadLetter,
    GateDecision,
    InboundReceipt,
    InboundRunView,
    KillSwitch,
    Plan,
    Run,
    RunState,
    TickState,
    ToolCallRecord,
)


class StaleState(RuntimeError):
    """Compare-and-set failed: the row changed since it was read."""


def is_connectivity_error(exc: BaseException) -> bool:
    """True for "the store cannot be reached" (a refused or dropped connection, a timeout), false for an error
    from a store that answered: a missing table, a missing grant. No driver import: psycopg's connection
    errors are recognised by class name along the MRO."""
    if isinstance(exc, StoreUnavailable | OSError):
        return True
    return any(
        c.__name__ in ("OperationalError", "InterfaceError") and c.__module__.startswith("psycopg")
        for c in type(exc).__mro__
    )


class StoreUnavailable(ConfigError):
    """The store cannot be reached (`tick` exits 4; nothing was changed)."""


class NotFound(KeyError):
    pass


class RerunRefused(RuntimeError):
    """The caller is not the re-run owner (a database role); a person's re-run of a message goes through that role
    only. A RuntimeError, not an OSError, so `is_connectivity_error` never reads it as an outage."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class Store(Protocol):
    def create_run(self, run: Run) -> None: ...
    def get_run(self, run_id: str) -> Run: ...
    def transition(
        self, run_id: str, expected: RunState, new: RunState, reason_code: str | None = None
    ) -> Run: ...
    def add_cost(self, run_id: str, usd: Decimal) -> None:
        """Raises NotFound for an unknown run."""
        ...

    def touch(self, run_id: str) -> None:
        """Heartbeat only: set `updated_at` to now; never checks or changes the state (tick's stuck-run
        rule). `transition` is the only compare-and-set."""
        ...

    def list_runs(self, state: RunState, updated_before: datetime, limit: int = 100) -> list[Run]:
        """Runs in `state` not updated since `updated_before`, oldest first, at most `limit`."""
        ...

    def save_plan(self, plan: Plan) -> None: ...
    def get_plan(self, run_id: str) -> Plan: ...

    def save_gate_decision(self, decision: GateDecision) -> None:
        """Once per run (append-only): a second one raises StaleState."""
        ...

    def get_gate_decision(self, run_id: str) -> GateDecision: ...

    def save_approval_request(self, req: ApprovalRequest) -> None: ...
    def get_approval_request(self, approval_id: str) -> ApprovalRequest: ...
    def update_approval_request(
        self, req: ApprovalRequest, expected_status: str, expected_step: int
    ) -> None: ...
    def record_decision(
        self,
        decision: ApprovalDecision,
        req: ApprovalRequest,
        expected_status: str,
        expected_step: int,
    ) -> None:
        """Atomically: save the decision (one per approval step) and compare-and-set the request. Either
        both happen or neither (StaleState): no decision row is ever kept for a click that lost."""
        ...

    def list_due_approvals(self, now: datetime) -> list[ApprovalRequest]: ...
    def save_approval_decision(self, decision: ApprovalDecision) -> None:
        """One per (approval_id, step): a second one raises StaleState."""
        ...

    def get_approval_decision(self, approval_id: str) -> ApprovalDecision | None:
        """The latest accepted decision for a request, or None (tick reconcile after a crash)."""
        ...

    def list_approvals(self, statuses: set[ApprovalStatus]) -> list[ApprovalRequest]: ...

    def add_dead_letter(self, dl: DeadLetter) -> None: ...
    def list_dead_letters(self, run_id: str) -> list[DeadLetter]: ...

    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]: ...
    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
        """(day, month) totals; a read with no write."""
        ...

    def get_kill_switch(self) -> KillSwitch:
        """A missing or unreadable switch row reads as ON (fail closed)."""
        ...

    def set_kill_switch(self, ks: KillSwitch) -> None: ...
    def get_tick_state(self, step: str) -> TickState | None: ...
    def save_tick_state(self, state: TickState) -> None: ...

    # --- evidence (K5): read-tool calls and the run's redaction map ---------------------------------------------
    def add_tool_call(self, call: ToolCallRecord) -> None:
        """Append-only: a second row with the same call_id raises StaleState."""
        ...

    def list_tool_calls(self, run_id: str) -> list[ToolCallRecord]:
        """Oldest first."""
        ...

    def purge_tool_calls(self, before: datetime, *, keep_run_ids: frozenset[str]) -> int:
        """Delete calls created before `before`, except those of `keep_run_ids`; returns the count."""
        ...

    def put_redaction_map(self, run_id: str, mapping: dict[str, str]) -> None:
        """Upsert the run's map (placeholder -> original, identifier kinds only; the caller filters)."""
        ...

    def get_redaction_map(self, run_id: str) -> dict[str, str] | None:
        """The saved map, or None when the run has none (a missing map is never an empty one)."""
        ...

    def purge_redaction_maps(
        self, before: datetime, *, keep_run_ids: frozenset[str], keep_open: bool = True
    ) -> int:
        """Delete maps whose run ended before `before` (the run's last state change; the map's own time when
        the run is unknown), except those of `keep_run_ids`. With `keep_open` (default) the map of a run that can
        still move (OPEN_STATES: received, working, plan ready, awaiting approval, executing, verifying) is kept,
        because restoring its inputs needs it (NEEDS_PERSON cannot move, so its map ages normally); the 400-day ceiling passes `keep_open=False`. Returns the count."""
        ...


def missing_methods(store: object) -> list[str]:
    """The methods of `Store` that `store` does not have. A custom store written for an earlier version lacks the
    evidence methods (`add_tool_call`, `list_tool_calls`, `purge_tool_calls`, `put_redaction_map`,
    `get_redaction_map`, `purge_redaction_maps`); the app refuses it at start with these names rather than failing
    on the first tool call."""
    return sorted(
        n
        for n, v in vars(Store).items()
        if callable(v) and not n.startswith("_") and not callable(getattr(store, n, None))
    )


ReceiveResult = Literal["new", "duplicate", "conflict", "conflict_capped", "busy", "key_changed"]


class InboundStore(Protocol):
    """The inbound ledger (AK-G2-a). A NEW protocol next to `Store`: a custom store written before it has no
    inbound methods and still works until a webhook is configured. Every time is an argument or a record field
    (no store clock). A missing receipt is `NotFound`; another state or claim token is `StaleState`."""

    def receive_inbound(
        self, rec: InboundReceipt, body: bytes | None, *, max_reuse: int, max_open: int
    ) -> ReceiveResult:
        """One transaction: first key check, key comparison, dedupe by delivery key (same text: `duplicate`,
        other text: `conflict`), the reuse-row cap (`conflict_capped`), the open-message cap (`busy`, only for a
        new message), then the receipt and its text. `key_changed` writes nothing."""
        ...

    def claim_inbound(
        self, tenant: str, source: str, now: datetime, lease_s: int
    ) -> InboundReceipt | None:
        """Take the oldest `received` receipt, or a `claimed` one whose lease ran out (that counts one try)."""
        ...

    def get_inbound_body(self, tenant: str, source: str, delivery_key: str) -> bytes | None: ...
    def finish_inbound(
        self,
        tenant: str,
        source: str,
        delivery_key: str,
        claim_token: str,
        state: str,
        reason: str | None,
        now: datetime,
    ) -> None: ...
    def release_inbound(
        self,
        tenant: str,
        source: str,
        delivery_key: str,
        claim_token: str,
        reason: str,
        now: datetime,
    ) -> None: ...
    def reopen_inbound(
        self, tenant: str, source: str, delivery_key: str, now: datetime
    ) -> InboundReceipt:
        """A person's re-run: only the re-run owner role may; every other caller gets `RerunRefused`."""
        ...

    def list_inbound_sources(self) -> list[tuple[str, str, int]]: ...
    def purge_inbound_bodies(self, before: datetime, ceiling: datetime) -> int: ...
    def get_inbound_key_check(self, tenant: str, source: str) -> str | None: ...
    def set_inbound_key_check(
        self, tenant: str, source: str, old: str, new: str, now: datetime
    ) -> None: ...
    def get_inbound_run(self, run_id: str) -> InboundRunView: ...


def missing_inbound_methods(store: object) -> list[str]:
    """The methods of `InboundStore` that `store` does not have (the app refuses such a store when a webhook is set)."""
    return sorted(
        n
        for n, v in vars(InboundStore).items()
        if callable(v) and not n.startswith("_") and not callable(getattr(store, n, None))
    )
