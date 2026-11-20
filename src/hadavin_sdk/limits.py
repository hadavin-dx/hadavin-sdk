"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Protocol

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.models import AuditEvent, KillSwitch, new_id, now
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import SpendCapExceeded, Store, check_spend_amount

_LOG = logging.getLogger("hadavin_sdk.limits")


class SpendRefused(RuntimeError):
    """Do not call the model. `reason` is one of:
    kill_switch | daily_budget | monthly_budget | limits_unavailable | bad_amount"""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class Meter(Protocol):
    """What the model gate calls around one model call. Implemented by `Limits` (store-backed)."""

    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str:
        """Book the worst case, then return the reservation id. Any exception: no model call."""
        ...

    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal:
        """Replace the worst case with the real cost; returns the overshoot (0 when none). First call wins."""
        ...


_CAP_REASON = {"day": "daily_budget", "month": "monthly_budget"}


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

    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str:
        """Book the worst case of one model call on the agent's day and month counters and return the
        reservation id. Any exception means no model call: SpendRefused carries the audit error code; an unknown
        agent is a KeyError, also while the stop state is on. Every store or stop-state failure is
        SpendRefused("limits_unavailable"): no path returns an id without a booking."""
        try:
            check_spend_amount(worst_usd)
        except ValueError:
            raise SpendRefused("bad_amount") from None
        budget = self.registry.agents[agent_id].budget_usd
        try:
            if self.store.get_kill_switch().on:
                raise SpendRefused("kill_switch")
            rid = new_id("res")
            self.store.reserve_spend(
                rid,
                agent_id,
                now().date(),
                worst_usd,
                day_cap=budget.daily,
                month_cap=budget.monthly,
                run_id=run_id,
            )
            return rid
        except SpendRefused:
            raise
        except SpendCapExceeded as exc:
            raise SpendRefused(_CAP_REASON.get(exc.which, "limits_unavailable")) from None
        except Exception as exc:  # noqa: BLE001 - fail closed: whatever the store raised, no model call
            _LOG.warning("reserve refused: limits_unavailable error_kind=%s", type(exc).__name__)
            raise SpendRefused("limits_unavailable") from None

    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal:
        """Replace the worst case with the real cost and return the overshoot (0 when none), always from the
        stored row: a repeated call returns the first result. NotFound for an unknown id, ValueError for a bad
        amount. An overshoot is booked in full and audited once; the audit never makes this raise."""
        row, applied = self.store.settle_spend(reservation_id, actual_usd)
        over = max(Decimal(0), (row.settled_usd or Decimal(0)) - row.reserved_usd)
        if applied and over > 0:
            try:
                self.audit.write_outcome(
                    AuditEvent(
                        run_id=row.run_id or "-",
                        domain="limits",
                        operation="overshoot",
                        principal=row.agent_id,
                        source="meter",
                        result="booked",
                    )
                )
            except Exception as exc:  # noqa: BLE001 - the booking is done; an audit failure must not undo the reply
                _LOG.warning("overshoot audit not written error_kind=%s", type(exc).__name__)
        return over

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
        """Removing a safety control is audited first; if that fails, the switch stays on. A clear the store
        refuses (the runtime role may not reset) leaves a `reset_failed` outcome, and the error is raised again."""
        self.audit.write_intent(self._event(False, by, "reset"))
        try:
            self.store.set_kill_switch(KillSwitch(on=False, by=by))
        except Exception:
            self.audit.write_outcome(self._event(True, by, "reset_failed"))
            raise
