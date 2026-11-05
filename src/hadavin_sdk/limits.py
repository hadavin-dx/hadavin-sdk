"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited."""

from __future__ import annotations

from decimal import Decimal

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.errors import SwitchChanged
from hadavin_sdk.models import AuditEvent, KillSwitch, now
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import Store


class Limits:
    def __init__(self, store: Store, audit: AuditSink, registry: Registry) -> None:
        self.store, self.audit, self.registry = store, audit, registry

    def charge(self, agent_id: str, usd: Decimal) -> tuple[Decimal, Decimal]:
        return self.store.add_spend(agent_id, now().date(), usd)

    def is_stopped(self) -> bool:
        """The kill switch alone (``blocked`` also reads budgets). An unreadable store raises."""
        return bool(self.store.get_kill_switch().on)

    def blocked(self, agent_id: str) -> list[str]:
        reasons = []
        if self.is_stopped():
            reasons.append("kill_switch")
        day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write
        budget = self.registry.agents[agent_id].budget_usd
        if day >= budget.daily:
            reasons.append("daily_budget")
        if month >= budget.monthly:
            reasons.append("monthly_budget")
        return reasons

    @staticmethod
    def _event(on: bool, by: str, operation: str, source: str) -> AuditEvent:
        return AuditEvent(
            run_id="-",
            domain="limits",
            operation=operation,
            principal=by,
            source=source,
            result="on" if on else "off",
        )

    def stop(self, by: str, source: str = "cli") -> None:
        """An emergency stop must work when the audit store is down: switch first, then audit (outbox)."""
        self.store.set_kill_switch(KillSwitch(on=True, by=by))
        self.audit.write_outcome(self._event(True, by, "stop", source))

    def switch(self) -> KillSwitch:
        """The stored kill-switch record (``on``, ``by``, ``ts``)."""
        return self.store.get_kill_switch()

    def reset(
        self, by: str, source: str = "cli", expect: tuple[str | None, object] | None = None
    ) -> None:
        """Removing a safety control is audited first; if that fails, the switch stays on. With ``expect=(by, ts)`` (what the caller's own stop
        wrote) the switch is cleared ONLY if it is still that record: read again after the audit intent and just before the write, so a
        stop by an operator or by another gate in between is kept (``SwitchChanged``, an outcome row ``reset_refused``). The store has no
        atomic compare-and-set, so a stop landing between that read and the write is not seen: that window is the store kind's to close."""
        self.audit.write_intent(self._event(False, by, "reset", source))
        if expect is not None:
            now_ks = self.store.get_kill_switch()
            if now_ks.on and (now_ks.by, now_ks.ts) != tuple(expect):
                self.audit.write_outcome(self._event(True, by, "reset_refused", source))
                raise SwitchChanged("the durable stop is not the one this caller wrote")
        self.store.set_kill_switch(KillSwitch(on=False, by=by))
