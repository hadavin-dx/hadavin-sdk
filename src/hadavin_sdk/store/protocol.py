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
    DeadLetter,
    GateDecision,
    KillSwitch,
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

    def reserve_spend(
        self,
        agent_id: str,
        day: date,
        usd: Decimal,
        daily_cap: Decimal,
        monthly_cap: Decimal,
        *,
        run_key: str | None = None,
        run_day: date | None = None,
        run_cap: Decimal | None = None,
    ) -> list[str]:
        """ONE atomic step (any number of threads or processes): if the kill switch is off (a missing row counts
        as on), the day total plus ``usd`` stays within ``daily_cap``, the month total within ``monthly_cap`` and,
        when ``run_key`` is given, the run's total (kept under ``run_key`` on ``run_day``) within ``run_cap``, add
        ``usd`` to all of them and return ``[]``. Otherwise add nothing and return the reasons
        (``kill_switch``, ``run_budget``, ``daily_budget``, ``monthly_budget``). The check and the booking
        share one lock or transaction, so a switch flipped before the step always wins."""
        ...

    def settle_spend(self, deltas: list[tuple[str, date, Decimal]]) -> None:
        """Apply every ``(agent_id, day, delta)`` (delta may be negative) in ONE atomic step: all or none."""
        ...

    def prune_spend(self, before: date) -> int:
        """Delete the per-run counters (agent ids ``run:...`` or ``<n>:<tenant>/run:...``) whose day is before
        ``before``; returns the number of day rows removed. Needs DELETE: not the runtime role's."""
        ...

    def get_kill_switch(self) -> KillSwitch:
        """A missing or unreadable switch row reads as ON (fail closed)."""
        ...

    def set_kill_switch(self, ks: KillSwitch) -> None: ...
    def get_tick_state(self, step: str) -> TickState | None: ...
    def save_tick_state(self, state: TickState) -> None: ...
