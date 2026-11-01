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
    Reservation,
    ReservationLimits,
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


class StoreBusy(StoreUnavailable):
    """The store's write lock was not free within the timeout (nothing was changed; retry later with the same key)."""


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

    def reserve(
        self,
        res: Reservation,
        limits: ReservationLimits,
        since: datetime,
        request: ApprovalRequest | None = None,
    ) -> str | None:
        """Hold `res` against the limits, counting THIS store's own open rows (younger than `since`) in the same
        transaction that inserts, serialised per tenant: two racing callers cannot both slip under a limit. With
        `request`, the approval request is saved in that same transaction and only if the reservation is held. Returns
        None when held (a repeat of the same key with the same content is held and unchanged), else a code:
        OPEN_LIMIT, UNIT_UNKNOWN or KEY_CONFLICT (the key is held with other content). Raises ReservationError for
        malformed input and StoreBusy when the write lock is not free in time."""
        ...

    def release_reservation(self, tenant: str, key: str) -> int:
        """Delete one reservation (it was executed, rejected or withdrawn); returns the rows removed (0 or 1)."""
        ...

    def list_reservations(self, tenant: str, since: datetime) -> list[Reservation]: ...
    def prune_reservations(self, older_than: datetime) -> int:
        """Delete reservations created before `older_than` (any tenant); returns how many."""
        ...

    def get_kill_switch(self) -> KillSwitch:
        """A missing or unreadable switch row reads as ON (fail closed)."""
        ...

    def set_kill_switch(self, ks: KillSwitch) -> None: ...
    def get_tick_state(self, step: str) -> TickState | None: ...
    def save_tick_state(self, state: TickState) -> None: ...
