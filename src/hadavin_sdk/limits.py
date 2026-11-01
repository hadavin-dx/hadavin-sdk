"""Limits: spend meter, daily, monthly and per-run budgets, kill switch. Every stop and reset is audited.

Two ways to spend, both kept:

* ``reserve`` -> call -> ``settle`` (R214, the one to use): the worst case of the call is booked atomically
  BEFORE it starts, in the store, so N concurrent callers can never book more than the cap (the lifted
  reserve-then-reconcile pattern of the ask-your-data meter); ``settle`` swaps the reservation for the real cost.
  A crash between the two leaves the worst case booked, which fails safe.
* ``blocked`` + ``charge`` (the original check-then-charge): kept so existing callers do not break, but a check
  and a later charge are two steps, so parallel calls can each pass the check and overshoot the cap. Migrate:
  replace ``blocked`` + ``charge`` around a model call with ``reserve`` + ``settle`` (see CHANGELOG).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.config import Route
from hadavin_sdk.llm.common import estimate_tokens
from hadavin_sdk.models import AuditEvent, KillSwitch, now
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import Store

# A run's total lives under a pseudo agent id at one fixed day, so a run that crosses midnight or a month end
# keeps one counter. ponytail: one small row pair per run; prune old `run:` rows if the table ever matters.
_RUN_DAY = date(1970, 1, 1)
_RUN_PREFIX = "run:"
_M = Decimal(1_000_000)


def worst_case_usd(route: Route, prompt_chars: int) -> Decimal:
    """What one call can cost at most: the input estimate (pessimistic 3 characters a token) at the input rate
    plus ``max_tokens`` at the output rate."""
    return (
        Decimal(estimate_tokens("x" * prompt_chars)) * route.input_usd_per_mtok
        + Decimal(route.max_tokens) * route.output_usd_per_mtok
    ) / _M


class OverBudget(RuntimeError):
    """No room for the call. ``reasons`` use the names ``blocked`` returns, plus ``run_budget``."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


@dataclass
class Reservation:
    agent_id: str
    run_id: str | None
    day: date
    usd: Decimal
    settled: bool = False


class Limits:
    def __init__(self, store: Store, audit: AuditSink, registry: Registry) -> None:
        self.store, self.audit, self.registry = store, audit, registry
        self._settle_lock = threading.Lock()

    def reserve(self, agent_id: str, usd: Decimal, run_id: str | None = None) -> Reservation:
        """Book ``usd`` (the call's worst case) against the run, daily and monthly caps in one atomic step each
        and return the reservation, or raise ``OverBudget`` having booked nothing. Needs the kill switch off."""
        if usd < 0:
            raise ValueError("negative reservation")
        if self.store.get_kill_switch().on:
            raise OverBudget(["kill_switch"])
        agent = self.registry.agents[agent_id]
        day = now().date()
        run_key = _RUN_PREFIX + run_id if run_id and agent.max_run_usd is not None else None
        if run_key and not self.store.reserve_spend(
            run_key, _RUN_DAY, usd, agent.max_run_usd, agent.max_run_usd
        ):
            raise OverBudget(["run_budget"])
        budget = agent.budget_usd
        if not self.store.reserve_spend(agent_id, day, usd, budget.daily, budget.monthly):
            if run_key:  # give the run's share back
                self.store.add_spend(run_key, _RUN_DAY, -usd)
            d, m = self.store.spend_totals(agent_id, day)
            reasons = [
                r
                for r, over in (
                    ("daily_budget", d + usd > budget.daily),
                    ("monthly_budget", m + usd > budget.monthly),
                )
                if over
            ]
            raise OverBudget(reasons or ["daily_budget"])
        return Reservation(agent_id, run_id if run_key else None, day, usd)

    def settle(self, res: Reservation, actual: Decimal) -> None:
        """Replace the reservation with what the call really cost (a cost above the reservation is recorded, not
        refused; ``actual=0`` releases it after a call that was never billed). Once per reservation."""
        if actual < 0:
            raise ValueError("negative cost")
        with self._settle_lock:
            if res.settled:
                raise ValueError("reservation already settled")
            res.settled = True
        delta = actual - res.usd
        if delta == 0:
            return
        self.store.add_spend(res.agent_id, res.day, delta)
        if res.run_id:
            self.store.add_spend(_RUN_PREFIX + res.run_id, _RUN_DAY, delta)

    def release(self, res: Reservation) -> None:
        self.settle(res, Decimal(0))

    def charge(self, agent_id: str, usd: Decimal) -> tuple[Decimal, Decimal]:
        return self.store.add_spend(agent_id, now().date(), usd)

    def blocked(self, agent_id: str) -> list[str]:
        reasons = []
        if self.store.get_kill_switch().on:
            reasons.append("kill_switch")
        day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write
        budget = self.registry.agents[agent_id].budget_usd
        if day >= budget.daily:
            reasons.append("daily_budget")
        if month >= budget.monthly:
            reasons.append("monthly_budget")
        return reasons

    @staticmethod
    def _event(on: bool, by: str, operation: str) -> AuditEvent:
        return AuditEvent(
            run_id="-",
            domain="limits",
            operation=operation,
            principal=by,
            source="cli",
            result="on" if on else "off",
        )

    def stop(self, by: str) -> None:
        """An emergency stop must work when the audit store is down: switch first, then audit (outbox)."""
        self.store.set_kill_switch(KillSwitch(on=True, by=by))
        self.audit.write_outcome(self._event(True, by, "stop"))

    def reset(self, by: str) -> None:
        """Removing a safety control is audited first; if that fails, the switch stays on."""
        self.audit.write_intent(self._event(False, by, "reset"))
        self.store.set_kill_switch(KillSwitch(on=False, by=by))
