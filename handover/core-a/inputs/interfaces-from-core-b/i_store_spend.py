"""INTERFACE (i), version 2.1: signature file, not package code. Added to `Store` in src/hadavin_sdk/store/protocol.py
and to models.py in step F. Source: inputs/draft-ticket-F-store-with-INTERFACE-ii.md, "Store Protocol additions"."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Protocol


class SpendCapExceeded(RuntimeError):
    def __init__(self, which: str) -> None:  # "day" or "month"; day is checked first
        super().__init__(f"{which} cap reached")
        self.which = which


class SpendReservation(
    Protocol
):  # a frozen pydantic BaseModel (not a Shape): the nine table columns
    reservation_id: str  # "res-" + uuid4 hex, always fresh
    agent_id: str
    day: date  # UTC date at reserve time
    run_id: str | None
    reserved_usd: Decimal
    settled_usd: Decimal | None
    status: Literal["open", "settled", "expired"]
    created_at: datetime  # database clock
    closed_at: datetime | None


class StoreSpend(Protocol):
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
        """Book usd on day and month or book nothing: SpendCapExceeded, StaleState (id exists), ValueError."""
        ...

    def settle_spend(
        self, reservation_id: str, actual_usd: Decimal
    ) -> tuple[SpendReservation, bool]:
        """The stored row and `applied` (true only for the call that changed it). NotFound for an unknown id;
        ValueError for a bad amount. Also adds the actual amount to the run's cost when the row has a run."""
        ...

    def expire_spend_reservations(self, older_than_s: int) -> int: ...

    def purge_spend_reservations(self, before: datetime) -> int: ...
