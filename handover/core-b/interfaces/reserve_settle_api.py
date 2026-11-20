"""INTERFACE (ii), version 1: signature file, not package code. Source: origin/core/P4b1 (8cc2021)
src/hadavin_sdk/meter.py, money.py, limits.py:37-85. NEW = not on that branch, added by core-b in step F."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Protocol


@dataclass(frozen=True)
class SpendMicro:
    """Model-call spend in whole micro-dollars (exact int, 0 to MAX_USD dollars). Never a float, bool or Decimal."""

    micro: int

    @classmethod
    def from_usd(cls, x: Decimal) -> SpendMicro: ...  # exact; at most 6 decimals, else ValueError
    def to_usd(self) -> Decimal: ...  # exponent exactly -6
    @classmethod
    def ceil_cost(cls, numerator: int, denominator: int = 1_000_000) -> SpendMicro: ...  # rounded UP once


class MeterError(RuntimeError):
    """Anything a payer raises on the way to a model call: the model is NOT called."""


class OverBudget(MeterError):
    reasons: tuple[str, ...]  # "run_budget" | "daily_budget" | "monthly_budget" | "kill_switch"
    which: str | None  # "run" | "day" | "month" | None (stop state: no numbers)
    cap: Decimal | None
    current: Decimal | None
    requested: Decimal | None
    day: date


class MeterUnavailable(MeterError):
    code: str  # store_unreachable | store_busy | store_rejected | conflict | unknown_run | unknown_reservation | counter_damaged


@dataclass(frozen=True)
class Settled:
    reservation_id: str
    status: str
    charged: SpendMicro
    applied: bool
    overshoot: SpendMicro


@dataclass(frozen=True)
class SettleFailure:
    reservation_id: str
    planned: SpendMicro | None
    code: str


class Hold(Protocol):
    reservation_id: str
    agent_id: str
    run_id: str | None
    reserved: SpendMicro
    day: date
    settled: Settled | None  # set at exit
    settle_failure: SettleFailure | None  # set at exit when the settle failed (reservation kept)

    def age_s(self) -> float: ...
    def record(self, actual: SpendMicro | None, *, measured: bool = True) -> None: ...
    def release(self) -> None: ...


class Payer(Protocol):
    """What the gate wrapper is given. Implemented by `Limits` (store-backed) and, NEW, by k1b `Budget` (in memory)."""

    def hold(
        self, agent_id: str, worst: SpendMicro, *, run_id: str | None = None
    ) -> AbstractContextManager[Hold]: ...


def worst_case(  # NEW, hadavin_sdk.meter
    route: Any,  # config.Route: input_usd_per_mtok, output_usd_per_mtok, max_tokens
    system: str,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None,
    documents: list[bytes] | None,
    requests: int,  # the client's max_attempts: one hold covers its internal retries
) -> SpendMicro: ...


def actual_spend(reply: Any) -> SpendMicro: ...  # NEW: models.Reply.cost_usd rounded UP to micro-dollars
