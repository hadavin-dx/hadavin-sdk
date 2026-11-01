"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited."""

from __future__ import annotations

import hashlib
from decimal import Decimal

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.guard.identity_text import identity_key
from hadavin_sdk.models import AuditEvent, KillSwitch, now
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import Store


class Limits:
    def __init__(self, store: Store, audit: AuditSink, registry: Registry) -> None:
        self.store, self.audit, self.registry = store, audit, registry

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

    @staticmethod
    def _by(by: str) -> str:
        """`by` goes into the hash-chained log. An emergency stop must never be refused, so text that is not bounded printable
        text (a newline, bidi or look-alike character, 10 KB) is not rejected: it is replaced by a short hash of itself."""
        return (
            by
            if identity_key(by, max_len=128, ascii_only=True) is not None
            else "h:" + hashlib.sha256(str(by).encode("utf-8", "replace")).hexdigest()[:16]
        )

    def stop(self, by: str) -> None:
        """An emergency stop must work when the audit store is down: switch first, then audit (outbox)."""
        by = self._by(by)
        self.store.set_kill_switch(KillSwitch(on=True, by=by))
        self.audit.write_outcome(self._event(True, by, "stop"))

    def reset(self, by: str) -> None:
        """Removing a safety control is audited first; if that fails, the switch stays on."""
        by = self._by(by)
        self.audit.write_intent(self._event(False, by, "reset"))
        self.store.set_kill_switch(KillSwitch(on=False, by=by))
