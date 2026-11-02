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

import json
import re
import threading
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_CEILING, Decimal
from typing import Any

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.config import Route
from hadavin_sdk.models import AuditEvent, KillSwitch, now
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import Store

# A run's total lives under a pseudo agent id, on the day the run started, so a run that crosses midnight or a
# month end keeps one counter and an expired one can be pruned by age (``Limits.prune_runs``).
_RUN_PREFIX = "run:"
_M = Decimal(1_000_000)
_RUN_RETENTION_DAYS = 7
_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")  # agent ids and tenants: no '/' or ':' in a counter key


def _money(usd: object, what: str) -> Decimal:
    """A finite, non-negative Decimal, or ValueError (NaN, Infinity and negatives would corrupt a counter)."""
    if not isinstance(usd, Decimal) or not usd.is_finite() or usd < 0:
        raise ValueError(f"{what} must be a finite, non-negative Decimal")
    return usd


def prompt_bytes(
    messages: list[dict[str, Any]],
    system: str = "",
    documents: list[bytes] | None = None,
    tools: list[dict[str, Any]] | None = None,
    output_schema: dict[str, Any] | None = None,
) -> int:
    """UTF-8 bytes of everything a call sends: messages, system text, tool schemas, the output schema and the
    documents. A document counts 3 bytes per byte, because the kinds decode it with replacement and each bad byte
    becomes U+FFFD (3 bytes). Sizes are summed part by part: no giant joined string is built."""
    size = len(system.encode("utf-8"))
    size += sum(len(str(m.get("content", "")).encode("utf-8")) + 16 for m in messages)
    size += sum(3 * len(d) for d in documents or [])
    for extra in (tools, output_schema):
        if extra:
            size += len(json.dumps(extra, default=str).encode("utf-8"))
    return size


def worst_case_usd(route: Route, prompt_size_bytes: int) -> Decimal:
    """An upper bound of what one call costs: ``max_tokens`` at the output rate, plus the prompt at the input rate
    assuming at most ``route.prompt_bytes_per_token`` bytes per token. The default of 1 is a true bound for
    byte-level tokenizers (a token is at least one byte); raise it per route only after measuring that model's
    tokenizer, as a looser bound lets concurrent calls overshoot. Size the prompt with ``prompt_bytes``."""
    if prompt_size_bytes < 0:
        raise ValueError("prompt size must not be negative")
    tokens = (Decimal(prompt_size_bytes) / route.prompt_bytes_per_token).to_integral_value(
        ROUND_CEILING
    )
    return (
        tokens * route.input_usd_per_mtok + Decimal(route.max_tokens) * route.output_usd_per_mtok
    ) / _M


class OverBudget(RuntimeError):
    """No room for the call. ``reasons`` use the names ``blocked`` returns, plus ``run_budget``."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


class StoreLacksReserve(TypeError):
    """The store has no ``reserve_spend``/``settle_spend``/``prune_spend`` (a custom store written before R214)."""


@dataclass
class Reservation:
    agent_id: str
    run_id: str | None
    day: date
    usd: Decimal
    run_day: date | None = None
    settled: bool = False
    settling: bool = False


class Limits:
    def __init__(
        self, store: Store, audit: AuditSink, registry: Registry, tenant: str = ""
    ) -> None:
        missing = [
            m for m in ("reserve_spend", "settle_spend", "prune_spend") if not hasattr(store, m)
        ]
        if missing:
            raise StoreLacksReserve(
                f"store {type(store).__name__} lacks {', '.join(missing)}: add them (store/protocol.py) "
                "to use Limits; blocked()+charge() alone cannot hold a cap under concurrency"
            )
        self.store, self.audit, self.registry = store, audit, registry
        self._settle_lock = threading.Lock()
        # R371: every counter key carries the tenant, so two clients on one store never share a budget or a run share.
        if tenant and not _ID.fullmatch(tenant):
            raise ValueError("tenant must match [A-Za-z0-9._-]{1,64}")
        self.tenant = tenant

    def _key(self, name: str) -> str:
        """Injective: a tenant is length-prefixed (``3:abc/name``) and a bare key never starts with digits and a
        colon (agent ids may not hold ':' or '/'), so no two (tenant, name) pairs share a counter."""
        return f"{len(self.tenant)}:{self.tenant}/{name}" if self.tenant else name

    def reserve(
        self, agent_id: str, usd: Decimal, run_id: str | None = None, run_day: date | None = None
    ) -> Reservation:
        """Book ``usd`` (the call's worst case) against the kill switch, run, daily and monthly caps in ONE atomic
        store step and return the reservation, or raise ``OverBudget`` having booked nothing. ``run_day`` is the
        day the run started (default today)."""
        _money(usd, "reservation")
        agent = self.registry.agents[agent_id]
        day = now().date()
        run_key = (
            self._key(_RUN_PREFIX + run_id) if run_id and agent.max_run_usd is not None else None
        )
        run_day = (run_day or day) if run_key else None
        budget = agent.budget_usd
        reasons = self.store.reserve_spend(
            self._key(agent_id),
            day,
            usd,
            budget.daily,
            budget.monthly,
            run_key=run_key,
            run_day=run_day,
            run_cap=agent.max_run_usd,
        )
        if reasons:
            raise OverBudget(reasons)
        return Reservation(agent_id, run_id if run_key else None, day, usd, run_day)

    def settle(self, res: Reservation, actual: Decimal) -> None:
        """Replace the reservation with what the call really cost, in one atomic store step (a cost above the
        reservation is recorded, not refused; ``actual=0`` releases it after a call that was never billed). Once
        per reservation: it counts as settled only after the store accepted it, so a failed settle can be retried
        and the real cost is never lost."""
        _money(actual, "cost")
        with self._settle_lock:
            if res.settled or res.settling:
                raise ValueError("reservation already settled")
            res.settling = True
        delta = actual - res.usd
        try:
            if delta != 0:
                # One global lock order, the order reserve takes: the run counter first, then the agent.
                items = []
                if res.run_id:
                    items.append(
                        (self._key(_RUN_PREFIX + res.run_id), res.run_day or res.day, delta)
                    )
                items.append((self._key(res.agent_id), res.day, delta))
                self.store.settle_spend(items)
        except BaseException:
            with self._settle_lock:
                res.settling = False
            raise
        with self._settle_lock:
            res.settled, res.settling = True, False

    def release(self, res: Reservation) -> None:
        self.settle(res, Decimal(0))

    def prune_runs(self, keep_days: int = _RUN_RETENTION_DAYS) -> int:
        """Delete the per-run counters (every tenant) of runs that started more than ``keep_days`` ago (a crashed
        run leaves its row). It needs DELETE on the spend tables, which the runtime database role does NOT have
        (least privilege): run it from the maintenance job (``hadavin-sdk prune-runs``, its own database identity
        from ``migrate --maintenance-role``), never from the runtime. A reservation stranded by a crash on an AGENT
        counter ages out with its day and month; to release it sooner use ``store.settle_spend([(key, day, -usd)])``."""
        return self.store.prune_spend(now().date() - timedelta(days=keep_days))

    def charge(self, agent_id: str, usd: Decimal) -> tuple[Decimal, Decimal]:
        _money(usd, "charge")
        return self.store.add_spend(self._key(agent_id), now().date(), usd)

    def blocked(self, agent_id: str) -> list[str]:
        reasons = []
        if self.store.get_kill_switch().on:
            reasons.append("kill_switch")
        day, month = self.store.spend_totals(self._key(agent_id), now().date())  # a read, no write
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
