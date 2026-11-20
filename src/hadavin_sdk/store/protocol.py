"""Store Protocol: Hadavin-owned rows. ``memory`` now, ``postgres`` when Portal v0 or S11 needs it."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    MAX_SPEND_DECIMALS,
    MAX_SPEND_EXPONENT,
    MAX_SPEND_USD,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Plan,
    Run,
    RunState,
    SpendReservation,
    TickState,
    ToolCallRecord,
    check_spend_amount,
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


class SpendCapExceeded(RuntimeError):
    """A reserve would pass a cap; nothing was booked. `which` is "day" or "month" (the day is checked first)."""

    def __init__(self, which: str) -> None:
        super().__init__(f"{which} cap reached")
        self.which = which


MAX_RESERVATION_ID_CHARS = 200
_RESERVATION_ID = re.compile(r"[A-Za-z0-9._:-]+")


def check_reservation_id(reservation_id: object) -> str:
    """The one id rule of the spend reservations, used by both stores before any lock or SQL: exactly a str of
    1 to 200 characters, only A-Z a-z 0-9 . _ : - (a NUL, for one, would reach PostgreSQL as a DataError).
    Anything else is a ValueError that names the rule, never the value."""
    if (
        type(reservation_id) is not str
        or not 1 <= len(reservation_id) <= MAX_RESERVATION_ID_CHARS
        or _RESERVATION_ID.fullmatch(reservation_id) is None
    ):
        raise ValueError(
            "reservation id must be a str of 1 to 200 characters from A-Z a-z 0-9 . _ : -"
        )
    return reservation_id


def check_store_id(value: object, what: str) -> str:
    """The id rule of `agent_id` and `run_id` in the spend methods, used by both stores before any lock or SQL:
    exactly a str of 1 to 200 characters, no NUL or other control character, encodable as UTF-8 (a lone surrogate
    is not). A ValueError names `what`, never the value."""
    if (
        type(value) is not str
        or not 1 <= len(value) <= MAX_RESERVATION_ID_CHARS
        or any(ord(c) < 32 or 127 <= ord(c) < 160 for c in value)
    ):
        raise ValueError(f"{what} must be a str of 1 to 200 characters with no control characters")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError(f"{what} must be encodable as UTF-8") from None
    return value


def check_spend_day(day: object) -> date:
    """A booking day is a plain date: a datetime or a string would be kept under another key than the row."""
    if type(day) is not date:
        raise ValueError("a spend day must be a date")
    return day


def clean_spend_amount(usd: object) -> Decimal:
    """`check_spend_amount`, then `-0` becomes `0` (no arithmetic: the caller's Decimal context never touches
    the amount). What a store writes into a counter or a reservation row."""
    usd = check_spend_amount(usd)
    return usd.copy_abs() if usd.is_zero() else usd


def check_spend_cap(cap: object) -> Decimal:
    """The cap rule of `reserve_spend`, used by both stores before any lock or SQL: a Decimal (not a float, an
    int, a bool, a str or None), finite, 0 <= cap, with the exponent window of an amount (-12 to 9); no other
    upper bound. Anything else is a ValueError and nothing is booked. A NaN cap must never reach the comparison:
    PostgreSQL sorts NaN above every number, so it would be no cap at all."""
    if (
        type(cap) is not Decimal
        or not cap.is_finite()
        or cap < 0
        or not -MAX_SPEND_DECIMALS <= cap.as_tuple().exponent <= MAX_SPEND_EXPONENT
    ):
        raise ValueError(
            "spend cap must be a finite Decimal with 0 <= cap, at most 12 decimal places and an exponent of at most 9"
        )
    return cap


MAX_EXPIRY_AGE_S = 10**7  # a larger age overflows a timestamp (memory) or a PostgreSQL interval


def check_purge_bound(before: object) -> datetime:
    """The bound of `purge_spend_reservations`, used by both stores: a timezone-aware datetime. Anything else
    (a naive datetime, a date, a str) is a ValueError and nothing is deleted."""
    if not isinstance(before, datetime) or before.tzinfo is None or before.utcoffset() is None:
        raise ValueError("purge bound must be a timezone-aware datetime")
    return before


def check_expiry_age(older_than_s: object) -> int:
    """The age rule of `expire_spend_reservations`, used by both stores: an int (not a bool) that is not
    negative. Anything else is a ValueError and nothing expires."""
    if type(older_than_s) is not int or not 0 <= older_than_s <= MAX_EXPIRY_AGE_S:
        raise ValueError("older_than_s must be an int with 0 <= older_than_s <= 10**7")
    return older_than_s


@dataclass(frozen=True)
class SpendRelease:
    """What `release_expired_spend` changed: the expired holds it lowered to 0, their summed reserved amount, and
    the day and month counter after the release (None when the agent has no counter row for that day)."""

    agent_id: str
    day: date
    reservations: int
    released_usd: Decimal
    day_usd: Decimal | None
    month_usd: Decimal | None
    applied_usd: Decimal = Decimal(
        0
    )  # what the day counter really fell by; below released_usd means drift
    intent_id: str = ""  # the audit intent row written before the release
    outcome_audited: bool = True  # False: committed, but the outcome row could not be written


class SpendReleaser(Protocol):
    """Optional, separate from `Store` so a custom store without it still starts. Only the Postgres store has it,
    and only the release login may run it (migration 0008)."""

    def release_expired_spend(
        self, agent_id: str, day: date, actor: str, audit: Any
    ) -> SpendRelease: ...


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
        """A missing or unreadable switch row reads as ON (fail closed). On Postgres the switch is also ON while
        any stop has no clear; the memory store keeps one flag and guarantees nothing."""
        ...

    def set_kill_switch(self, ks: KillSwitch) -> None:
        """`on=True` adds a stop. `on=False` clears the stops visible to its clear statement; on Postgres only the
        reset role may (the runtime role is refused by the database). A stop committed after that statement began
        stays ON; one committed between the audit intent and that statement is cleared. A reset that finds no
        switch row raises (the state stays ON)."""
        ...

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

    # --- spend reservations (0007): book the worst case before a model call, the real cost after it ---------------
    def reserve_spend(
        self,
        reservation_id: str,
        agent_id: str,
        day: date,
        usd: Decimal,
        *,
        day_cap: Decimal,
        month_cap: Decimal,
        run_id: str | None = None,
    ) -> None:
        """Book `usd` on the day and the month counter, or book nothing. A counter that is already at its cap,
        or that would pass it, refuses: SpendCapExceeded (`which` "day" or "month", the day is checked first).
        StaleState when the id exists; ValueError for an amount that is not a finite Decimal in [0, 10**9) or
        a cap that is not a finite Decimal >= 0 (`check_spend_cap`). Checked in this order: the amount, the caps
        (ValueError), the id (StaleState), the caps comparison (SpendCapExceeded)."""
        ...

    def settle_spend(
        self, reservation_id: str, actual_usd: Decimal, *, agent_id: str | None = None
    ) -> tuple[SpendReservation, bool]:
        """With `agent_id`, a reservation of another agent is NotFound (the same as an unknown id). The stored row and `applied` (true only for the call that changed it). The first call closes an open
        or an expired row: the counters of the row's own day and month move by actual minus reserved (after
        expiry only upward), `settled_usd` becomes what stays booked (the actual amount; for a row that was
        expired the larger of actual and reserved) and the real actual amount is added to the run's cost when
        the row has a run that exists.
        A later call changes nothing. NotFound for an unknown id; ValueError for a bad amount."""
        ...

    def expire_spend_reservations(self, older_than_s: int) -> int:
        """Open rows older than `older_than_s` seconds become expired; the counters do not move, so the worst
        case stays booked. Returns the count. ValueError when `older_than_s` is not an int (a bool is not one)
        or is negative."""
        ...

    def purge_spend_reservations(self, before: datetime) -> int:
        """Delete closed rows (settled or expired) closed before `before`; never an open row. Returns the count."""
        ...


def missing_methods(store: object) -> list[str]:
    """The methods of `Store` that `store` does not have. A custom store written for an earlier version lacks the
    evidence methods (`add_tool_call`, `list_tool_calls`, `purge_tool_calls`, `put_redaction_map`,
    `get_redaction_map`, `purge_redaction_maps`) or the spend reservation methods (`reserve_spend`, `settle_spend`,
    `expire_spend_reservations`, `purge_spend_reservations`); the app refuses it at start with these names rather
    than failing on the first tool call or model call."""
    return sorted(
        n
        for n, v in vars(Store).items()
        if callable(v) and not n.startswith("_") and not callable(getattr(store, n, None))
    )
