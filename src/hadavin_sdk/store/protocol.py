"""Store Protocol: Hadavin-owned rows. ``memory`` now, ``postgres`` when Portal v0 or S11 needs it."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol, cast

from hadavin_sdk.defaults import MAX_USD
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
    SpendReservation,
    TickState,
    ToolCallRecord,
)


class StaleState(RuntimeError):
    """Compare-and-set failed: the row changed since it was read."""


# The most any one spend counter (the day, the month, a run's cost) may hold. A booking that would pass it is a
# ValueError and books nothing. The excess of a settle above its reservation is NOT held under it (the money is spent).
MAX_COUNTER_USD = 10**15
# The youngest age (seconds) of an open reservation that the sweep may expire; the meter picks the real value.
MIN_SWEEP_AGE_S = 30
_MIN_DAY, _MAX_DAY = date(2000, 1, 1), date(2100, 12, 31)
_ID_RE = re.compile(r"[A-Za-z0-9._:-]{1,200}\Z")


class SpendCapExceeded(RuntimeError):
    """A booking would pass a cap. `which` is "run", "day" or "month" (the first failing one in that order)."""

    def __init__(self, which: str, cap: Decimal, current: Decimal, requested: Decimal) -> None:
        super().__init__(f"{which} cap {cap} exceeded: current {current}, requested {requested}")
        self.which, self.cap, self.current, self.requested = which, cap, current, requested


class KillSwitchOn(RuntimeError):
    """The kill switch is on (or unreadable): no new reservation."""


class CounterDamaged(RuntimeError):
    """A counter is lower than the amount to lower, or its row is missing: damaged data; nothing was changed."""


class ReservationConflict(StaleState):
    """The reservation id exists with different content."""


@dataclass(frozen=True)
class SpendOutcome:
    """`applied` is true only when THIS call changed the row; a replay or a lost race gives false."""

    reservation: SpendReservation
    applied: bool


def check_usd(x: object, *, positive: bool = False, max_decimals: int | None = None) -> Decimal:
    """An amount of money: exactly `Decimal` (not bool, int, float, str or a subclass), finite, not negative and not
    minus zero, at most `MAX_USD`; `positive` also refuses zero; `max_decimals` limits the decimal places (read from
    the digit tuple, never through the arithmetic context; trailing zeros do not count). `ValueError` otherwise."""
    if type(x) is not Decimal:
        raise ValueError("an amount must be a Decimal")
    if not x.is_finite():
        raise ValueError("an amount must be a finite number")
    if x.is_signed():
        raise ValueError("an amount must not be negative")
    if x > MAX_USD:
        raise ValueError(f"an amount may be at most {MAX_USD}")
    if positive and x == 0:
        raise ValueError("an amount must be greater than zero")
    if max_decimals is not None and x != 0:
        _sign, digits, exponent = x.as_tuple()
        exponent = cast(int, exponent)  # an int for a finite value (checked above)
        trailing = len(digits) - len("".join(map(str, digits)).rstrip("0"))
        if exponent + trailing < -max_decimals:
            raise ValueError(f"an amount may have at most {max_decimals} decimal places")
    return x


def check_cap(x: object) -> Decimal | None:
    """A cap: None (no cap) or an amount with at most 8 decimals (zero is allowed). The store never rounds a cap."""
    return None if x is None else check_usd(x, max_decimals=8)


def check_day(d: object) -> date:
    """A calendar date (not a datetime) from 2000-01-01 to 2100-12-31."""
    if type(d) is not date or not _MIN_DAY <= d <= _MAX_DAY:
        raise ValueError("day must be a date from 2000-01-01 to 2100-12-31")
    return d


def check_int(x: object, lo: int, hi: int) -> int:
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError(f"must be an integer from {lo} to {hi}")
    return x


def check_id(x: object, what: str = "id") -> str:
    """A reservation or agent id: 1 to 200 characters of letters, digits and `. _ : -`."""
    if type(x) is not str or _ID_RE.match(x) is None:
        raise ValueError(f"{what} must be 1 to 200 characters of letters, digits and . _ : -")
    return x


_META_KEY = re.compile(r"[a-z_]{1,40}\Z")


_MICRO = Decimal("1E-6")


def check_reserve(
    reservation_id, agent_id, day, amount_usd, day_cap, month_cap, run_id, run_cap, meta
) -> tuple[Decimal, dict[str, str | int | bool] | None]:
    """Precedence step 1 of `reserve_spend`, shared by both stores: every argument is validated before anything is
    read or written. Returns the amount quantized to six decimals and the checked meta."""
    check_id(reservation_id, "reservation_id")
    check_id(agent_id, "agent_id")
    check_day(day)
    check_usd(amount_usd, positive=True, max_decimals=6)
    for cap in (day_cap, month_cap, run_cap):
        check_cap(cap)
    if run_id is None:
        if run_cap is not None:
            raise ValueError("run_cap needs a run_id")
    else:
        check_id(run_id, "run_id")
    return amount_usd.quantize(_MICRO), check_meta(meta)


def check_meta(meta: object) -> dict[str, str | int | bool] | None:
    """Billing tags: None or at most 20 keys `[a-z_]{1,40}`, values str (up to 200 characters), int or bool, and
    at most 2000 bytes of `json.dumps(meta, ensure_ascii=False, separators=(", ", ": "))` in UTF-8."""
    import json

    if meta is None:
        return None
    if not isinstance(meta, Mapping) or len(meta) > 20:
        raise ValueError("meta must be a mapping of at most 20 keys")
    # NUL and a lone surrogate: the same refusal as the Postgres write wrapper, on both stores
    check_text(meta)
    for k, v in meta.items():
        if type(k) is not str or _META_KEY.match(k) is None:
            raise ValueError("meta keys must match [a-z_]{1,40}")
        if type(v) not in (str, int, bool) or (type(v) is str and len(v) > 200):
            raise ValueError("meta values must be str (up to 200 characters), int or bool")
        if type(v) is int and abs(v) > 2**53:
            raise ValueError("meta integers must be within 2**53")
    out = dict(meta)
    if len(json.dumps(out, ensure_ascii=False, separators=(", ", ": ")).encode("utf-8")) > 2000:
        raise ValueError("meta may be at most 2000 bytes")
    return out


def is_connectivity_error(exc: BaseException) -> bool:
    """True for "the store cannot be reached" (a refused or dropped connection, a timeout), false for an error
    from a store that answered: a missing table, a missing grant. No driver import: psycopg's connection
    errors are recognised by class name along the MRO."""
    if getattr(exc, "sqlstate", None) in ("40001", "40P01", "55P03", "57014"):
        return False
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


class StoreBusy(RuntimeError):
    """A write could not finish in time: a lock wait, the call budget, or retries on a deadlock or a serialization
    failure ran out. The call changed nothing; a caller may send the same call again. Not a connectivity error."""


_STEP_RE = re.compile(r"[a-z_]+")


def check_step_name(s: object) -> str:
    """A tick step name: one or more of `a-z` and `_`, the whole string (a trailing newline does not pass)."""
    if type(s) is not str or _STEP_RE.fullmatch(s) is None:
        raise ValueError("a tick step name must match [a-z_]+")
    return s


def _scan_text(x: object, depth: int = 0) -> None:
    if depth > 64:
        raise ValueError("a value is nested too deeply")
    if isinstance(x, str):
        if "\x00" in x:
            raise ValueError("text must not hold a NUL character")
        try:
            x.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("text must not hold a lone surrogate") from None
    elif isinstance(x, float):
        if not math.isfinite(x):
            raise ValueError("a number must be finite")
    elif isinstance(x, Mapping):
        for k, v in x.items():
            _scan_text(k, depth + 1)
            _scan_text(v, depth + 1)
    elif isinstance(x, list | tuple | set | frozenset):
        for v in x:
            _scan_text(v, depth + 1)


def check_text(model: object) -> None:
    """Deep scan of every string field and dict key of `model.model_dump()` for NUL and lone surrogates, and of
    nested data for NaN and infinite floats. `ValueError` on the first hit; the message never echoes the value."""
    _scan_text(model.model_dump() if hasattr(model, "model_dump") else model)


class Store(Protocol):
    def create_run(self, run: Run) -> None: ...
    def get_run(self, run_id: str) -> Run: ...
    def transition(
        self, run_id: str, expected: RunState, new: RunState, reason_code: str | None = None
    ) -> Run: ...
    def add_cost(self, run_id: str, usd: Decimal) -> None:
        """Raises NotFound for an unknown run, `ValueError` for a bad amount or a total past `MAX_COUNTER_USD`."""
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

    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
        """`ValueError` for a bad amount or day (`check_usd` with 8 decimals, `check_day`) or when a counter would
        pass `MAX_COUNTER_USD`; nothing is booked then."""
        ...

    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
        """(day, month) totals; a read with no write."""
        ...

    def reserve_spend(
        self,
        reservation_id: str,
        agent_id: str,
        day: date,
        amount_usd: Decimal,
        *,
        day_cap: Decimal | None,
        month_cap: Decimal | None,
        run_id: str | None = None,
        run_cap: Decimal | None,
        meta: Mapping[str, str | int | bool] | None = None,
    ) -> SpendOutcome:
        """Book `amount_usd` on the day and month counters (and the run's, with `run_id`) in one step, refusing at
        the caps (`SpendCapExceeded`, first failing of run, day, month), at the kill switch (`KillSwitchOn`) and at
        `MAX_COUNTER_USD` (`ValueError`). Same id and content again returns the open row with `applied=False`;
        same id with other content is `ReservationConflict`; a closed one is `StaleState`."""
        ...

    def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendOutcome:
        """Close an open (or expired) reservation at the real cost (at most 6 decimals; may exceed the reserved
        amount, which is booked in full). A closed one returns its first result with `applied=False`."""
        ...

    def release_spend(self, reservation_id: str) -> SpendOutcome:
        """Close an open (or expired) reservation and give back the reserved amount; `CounterDamaged` (nothing
        changed) if a counter is lower than that amount or missing."""
        ...

    def get_spend_reservation(self, reservation_id: str) -> SpendReservation: ...
    def list_open_reservations(
        self, agent_id: str | None = None, run_id: str | None = None, limit: int = 100
    ) -> list[SpendReservation]: ...
    def sweep_spend_reservations(
        self, older_than_s: int, *, limit: int = 100
    ) -> list[SpendReservation]:
        """Open rows older than `older_than_s` (30 to 10**7) become `expired` (no counter moves)."""
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
        """Delete calls created before `before`, except those of `keep_run_ids`; returns the count.
        The Postgres store deletes in batches (`defaults.STORE_PURGE_BATCH_ROWS`) and stops early when the call
        budget is nearly spent, keeping what it deleted: call again until the count is below the batch size."""
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
        because restoring its inputs needs it (NEEDS_PERSON cannot move, so its map ages normally); the 400-day ceiling passes `keep_open=False`. Returns the count. Batching as for `purge_tool_calls`."""
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
