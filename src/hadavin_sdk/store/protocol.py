"""Store Protocol: Hadavin-owned rows. ``memory`` now, ``postgres`` when Portal v0 or S11 needs it."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalWeek,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Label,
    LevelEvent,
    PilotWeek,
    Plan,
    Run,
    RunState,
    TickState,
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


class HarmfulSticky(RuntimeError):
    """A non-harmful label on a run whose latest eligible label is harmful, from someone who may not lower it."""


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

    # --- K6 measurement: labels, demotions, reports ---------------------------------------------------------
    def add_labels(
        self, items: list[tuple[Label, LevelEvent | None]], *, may_lower_harmful: bool
    ) -> None:
        """Every (label, demotion) in ONE transaction, with the sticky-harmful rule checked inside it and serialised
        per run: unless `may_lower_harmful`, a non-harmful label on a run whose latest eligible label is harmful
        raises HarmfulSticky. A duplicate `label_id` raises StaleState. Either way nothing is stored. This is the
        ONLY way a label enters the store. A label's `created_at` is moved to just after the run's newest existing
        label when it is not later than it, so commit order and time order agree (a clock read before the lock
        cannot put a later commit earlier). A demotion that already exists (same agent, action and reason) is
        not inserted twice."""
        ...

    def claim_action(self, nonce: str, at: datetime) -> bool:
        """Record a signed channel click's nonce; False when it was already seen (a replay)."""
        ...

    def list_labels(self, run_id: str) -> list[Label]:
        """Every label of the run, oldest first."""
        ...

    def list_labels_for(self, agent_id: str, action_id: str, since: datetime | None) -> list[Label]:
        """Labels of runs whose plan is for (agent, action), created at or after `since` (None: all), oldest first."""
        ...

    def count_proposals(self, agent_id: str, action_id: str, since: datetime | None) -> int:
        """Plans for (agent, action) created at or after `since` (None: all)."""
        ...

    def list_labels_between(self, start: datetime, end: datetime) -> list[Label]:
        """Every label created in [start, end), runs with or without a plan, oldest first."""
        ...

    def list_csv_import(self, import_id: str) -> list[Label]:
        """Every label stored by one csv import (ids `csv-<import_id>-<row>-p|a`), oldest first."""
        ...

    def add_level_event(self, event: LevelEvent) -> None:
        """Append a demotion (idempotent per agent, action and reason). A `clear` goes through `clear_demotion`."""
        ...

    def clear_demotion(self, event: LevelEvent, expected_seq: int) -> bool:
        """Append a `clear` only if the newest level event of that (agent, action) still has seq `expected_seq`:
        a compare-and-set. False when something (a new demotion) landed since the caller looked, and nothing is
        written; the caller must look again."""
        ...

    def list_level_events(self) -> list[LevelEvent]:
        """Every demotion and clear, in seq order."""
        ...

    def current_overrides(self) -> dict[tuple[str, str], str]:
        """(agent, action) -> "shadow" for every pair whose latest level event is a `demote`."""
        ...

    def held_run_ids(self) -> set[str]:
        """Runs ever labelled wrong, harmful or missed (their evidence is held, K5)."""
        ...

    def put_report(self, week: date, body: str) -> bool:
        """Store the week's report once; False when that week already has one (the first stays)."""
        ...

    def get_report(self, week: date) -> str | None: ...

    def pilot_week(self, week: date) -> PilotWeek:
        """`week` is the Monday of an ISO week (UTC). A week with no runs is all zeros."""
        ...

    def approval_week(self, week: date) -> ApprovalWeek: ...
