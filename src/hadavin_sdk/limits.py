"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable
from decimal import ROUND_DOWN, Decimal, InvalidOperation

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.meter import Caps, Hold, Meter, MeterError, Settled, SettleFailure
from hadavin_sdk.models import AuditEvent, KillSwitch, now
from hadavin_sdk.money import BusinessMoney, SpendMicro
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import Store

CAP_DECIMALS = 8  # a cap has at most this many decimals (`store.protocol.check_cap`); budgets are rounded DOWN to it


class Limits:
    def __init__(self, store: Store, audit: AuditSink, registry: Registry) -> None:
        self.store, self.audit, self.registry = store, audit, registry
        # The meter's two reactions. Plain attributes, read when the meter signals (not when it is built), so a
        # caller may set them at any time. Both run in the calling thread, inside the exit of the hold.
        self.on_overshoot: Callable[[Settled], None] | None = None
        self.on_settle_failed: Callable[[SettleFailure], None] | None = None
        self._meter: Meter | None = None
        self._meter_lock = threading.Lock()

    def charge(self, agent_id: str, usd: Decimal | SpendMicro) -> tuple[Decimal, Decimal]:
        if isinstance(usd, BusinessMoney):
            raise TypeError("business money is not spend")
        if isinstance(usd, SpendMicro):
            usd = usd.to_usd()
        return self.store.add_spend(agent_id, now().date(), usd)

    def caps(self, agent_id: str) -> Caps:
        """The caps of one agent from the registry: day and month from its budget, run from `max_run_usd`.
        A budget is rounded DOWN to `CAP_DECIMALS` decimals (the store refuses more); an unknown agent is a
        `MeterError`."""
        agent = self.registry.agents.get(agent_id)
        if agent is None:
            raise MeterError("unknown agent")

        def down(x: Decimal | None) -> Decimal | None:
            if x is None:
                return None
            try:
                return x.quantize(Decimal(1).scaleb(-CAP_DECIMALS), rounding=ROUND_DOWN)
            except InvalidOperation:
                raise MeterError("a budget is not usable") from None

        return Caps(
            day=down(agent.budget_usd.daily),
            month=down(agent.budget_usd.monthly),
            run=down(agent.max_run_usd),
        )

    def _the_meter(self) -> Meter:
        if self._meter is None:
            with self._meter_lock:
                if self._meter is None:  # double-checked: 8 threads on first use make one Meter
                    self._meter = Meter(
                        self.store,
                        clock=lambda: now(),
                        on_overshoot=self._signal_overshoot,
                        on_settle_failed=self._signal_settle_failed,
                    )
        return self._meter

    def _signal_overshoot(self, settled: Settled) -> None:
        callback = self.on_overshoot  # read now, not at build
        if callback is not None:
            callback(settled)

    def _signal_settle_failed(self, failure: SettleFailure) -> None:
        callback = self.on_settle_failed
        if callback is not None:
            callback(failure)

    def hold(
        self, agent_id: str, worst: SpendMicro, *, run_id: str | None = None
    ) -> contextlib.AbstractContextManager[Hold]:
        """Reserve `worst` against this agent's caps before a model call; settles on every exit (see `Meter.hold`)."""
        return self._the_meter().hold(agent_id, worst, self.caps(agent_id), run_id=run_id)

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
