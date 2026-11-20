"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited."""

from __future__ import annotations

import logging
import threading
from decimal import Decimal
from typing import Protocol

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.models import AuditEvent, KillSwitch, new_id, now
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import NotFound, SpendCapExceeded, Store, check_spend_amount

_LOG = logging.getLogger("hadavin_sdk.limits")


class SpendRefused(RuntimeError):
    """Do not call the model. `reason` is one of:
    kill_switch | daily_budget | monthly_budget | limits_unavailable | bad_amount | usd_cap
    (`usd_cap` comes only from the in-memory `Budget`)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class Meter(Protocol):
    """What the model gate calls around one model call. Implemented by `Limits` (store-backed) and by `Budget`
    (in memory, for the eval and replay command lines)."""

    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str:
        """Book the worst case, then return the reservation id. Any exception: no model call."""
        ...

    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal:
        """Replace the worst case with the real cost; returns the overshoot (0 when none). First call wins."""
        ...


class Budget:
    """The in-memory meter of the eval and replay command lines: ONE total USD cap for the whole invocation, kept
    in this process only (no store, no stop state, no expiry step, no run cost). Same shape as `Limits`:
    `reserve` books the worst case of one model call or refuses with SpendRefused("usd_cap"), `settle` replaces
    it with the real cost. `spent` is what is booked now: real costs of settled calls plus the worst case of
    every call that is open or was abandoned. Not the registry's `Budget` (an agent's budget numbers)."""

    def __init__(self, limit: Decimal) -> None:
        self.limit = limit
        self._lock = threading.Lock()
        # reservation id -> [reserved, booked now, state, overshoot, run_id]; state: open | forfeited | settled
        self._rows: dict[str, list] = {}
        self._closed: set[str] = set()  # run ids closed by `forfeit`

    @property
    def spent(self) -> Decimal:
        with self._lock:
            return self._spent()

    def _spent(self) -> Decimal:
        return sum((row[1] for row in self._rows.values()), Decimal(0))

    @property
    def exhausted(self) -> bool:
        return self.spent >= self.limit

    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str:
        """Book the worst case of one model call and return the reservation id. SpendRefused("bad_amount") for an
        amount the store's rule refuses; SpendRefused("usd_cap") when the booking would pass the cap, or when
        `run_id` was closed by `forfeit` (a call abandoned by its case must not start another one). A hold made
        with `run_id` None is closed only by `settle`."""
        try:
            check_spend_amount(worst_usd)
        except ValueError:
            raise SpendRefused("bad_amount") from None
        with self._lock:
            if run_id in self._closed or self._spent() + worst_usd > self.limit:
                raise SpendRefused("usd_cap")
            rid = new_id("res")
            self._rows[rid] = [worst_usd, worst_usd, "open", Decimal(0), run_id]
            return rid

    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal:
        """Replace the worst case with the real cost (it may be above it; settle never refuses) and return the
        overshoot. NotFound for an unknown id, ValueError for a bad amount. A repeat returns the first result
        and changes nothing. After `forfeit` the late settle of that call can only RAISE what is booked."""
        check_spend_amount(actual_usd)
        with self._lock:
            row = self._rows.get(reservation_id)
            if row is None:
                raise NotFound(reservation_id)
            reserved, booked, state = row[0], row[1], row[2]
            if state != "settled":
                row[1] = actual_usd if state == "open" else max(booked, actual_usd)
                row[2], row[3] = "settled", max(Decimal(0), actual_usd - reserved)
            return row[3]

    def forfeit(self, run_id: str) -> None:
        """The case `run_id` ended. Every hold made with that run id that is still open (a timeout, used-up
        retries, any provider error, a reply with no usable cost: the cost is unknown) stays booked at its worst
        case, and the run id is closed: a later reserve with it is refused, so a thread the case abandoned can
        book and call nothing more. Other run ids are not touched."""
        with self._lock:
            for row in self._rows.values():
                if row[2] == "open" and row[4] == run_id:
                    row[2] = "forfeited"
            self._closed.add(run_id)


_CAP_REASON = {"day": "daily_budget", "month": "monthly_budget"}


class Limits:
    def __init__(self, store: Store, audit: AuditSink, registry: Registry) -> None:
        self.store, self.audit, self.registry = store, audit, registry

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
        try:
            budget = self.registry.agents[agent_id].budget_usd
        except TypeError:  # an unhashable agent id
            raise KeyError(agent_id) from None
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
