"""INTERFACE (i), version 1: signature file, not package code. Source: origin/core/P4d-a2 (a8abba0)
src/hadavin_sdk/store/protocol.py:35-69, 301-338 and models.py:351-366. These names are ADDED to the existing
`Store` Protocol and to `hadavin_sdk.store.protocol` / `hadavin_sdk.models` in step F."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Protocol

MAX_COUNTER_USD = 10**15  # the most one counter (day, month, run) may hold
MIN_SWEEP_AGE_S = 30  # the youngest open reservation the sweep may expire


class StaleState(RuntimeError):  # exists on main: store/protocol.py:25
    """Compare-and-set failed: the row changed since it was read."""


class SpendCapExceeded(RuntimeError):
    """A booking would pass a cap. `which` is "run", "day" or "month" (the first failing one in that order)."""

    which: str
    cap: Decimal
    current: Decimal
    requested: Decimal


class KillSwitchOn(RuntimeError):
    """The stop state is on (or unreadable): no new reservation."""


class CounterDamaged(RuntimeError):
    """A counter is lower than the amount to lower, or its row is missing; nothing was changed."""


class ReservationConflict(StaleState):
    """The reservation id exists with different content."""


class SpendReservation(Protocol):  # a frozen pydantic model (`Shape`) in models.py
    reservation_id: str  # [A-Za-z0-9._:-]{1,200}, chosen by the caller: the idempotence key
    agent_id: str
    day: date  # UTC budget day, 2000-01-01 to 2100-12-31
    run_id: str | None
    reserved_usd: Decimal  # > 0, at most 6 decimals
    status: Literal["open", "settled", "released", "expired"]
    settled_usd: Decimal | None  # expired rows hold reserved_usd here until settled or released
    created_at: datetime  # database clock
    closed_at: datetime | None
    expired_at: datetime | None
    meta: dict[str, Any] | None  # at most 2000 bytes; never client text


@dataclass(frozen=True)
class SpendOutcome:
    """`applied` is true only when THIS call changed the row; a replay or a lost race gives false."""

    reservation: SpendReservation
    applied: bool


class StoreSpend(Protocol):
    """The six methods added to `Store`. `add_spend` and `spend_totals` (main, store/protocol.py:107-110) stay."""

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
    ) -> SpendOutcome: ...

    def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendOutcome: ...

    def release_spend(self, reservation_id: str) -> SpendOutcome: ...

    def get_spend_reservation(self, reservation_id: str) -> SpendReservation: ...

    def list_open_reservations(
        self, agent_id: str | None = None, run_id: str | None = None, limit: int = 100
    ) -> list[SpendReservation]: ...

    def sweep_spend_reservations(
        self, older_than_s: int, *, limit: int = 100
    ) -> list[SpendReservation]: ...
