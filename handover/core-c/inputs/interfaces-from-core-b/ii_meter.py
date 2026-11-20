"""INTERFACE (ii), version 2: signature file, not package code. Lands in src/hadavin_sdk/limits.py in step F.
Source: handover/core-b/inputs/draft-ticket-F-store-with-INTERFACE-ii.md, block "INTERFACE (ii)"."""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol


class SpendRefused(RuntimeError):
    """Do not call the model. `reason` is one of:
    kill_switch | daily_budget | monthly_budget | limits_unavailable | bad_amount"""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class Meter(Protocol):
    """Implemented by `Limits` (store-backed) and by k1b `Budget` (in memory, with a lock)."""

    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str:
        """Book the worst case, then return the reservation id. Any exception: no model call."""
        ...

    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal:
        """Replace the worst case with the real cost; returns the overshoot (0 when none). First call wins."""
        ...
