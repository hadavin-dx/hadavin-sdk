"""In-memory store: dicts behind one lock. Rows are lost on restart (stated; Postgres comes with its trigger)."""

from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal, localcontext

from hadavin_sdk import defaults
from hadavin_sdk.models import (
    OPEN_STATES,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    DeadLetter,
    GateDecision,
    KillSwitch,
    OpenStop,
    Plan,
    Run,
    RunState,
    SpendReservation,
    TickState,
    ToolCallRecord,
    now,
)
from hadavin_sdk.store.protocol import (
    NotFound,
    SpendCapExceeded,
    StaleState,
    check_expiry_age,
    check_purge_bound,
    check_reservation_id,
    check_spend_cap,
    check_spend_day,
    check_store_id,
    clean_spend_amount,
)


class MemoryStore:
    def __init__(self) -> None:
        # ponytail: one global lock; per-row locks only if a real backend ever needs throughput here.
        self._lock = threading.Lock()
        self._runs: dict[str, Run] = {}
        self._plans: dict[str, Plan] = {}
        self._gates: dict[str, GateDecision] = {}
        self._approvals: dict[str, ApprovalRequest] = {}
        self._decisions: list[ApprovalDecision] = []
        self._dead: dict[str, list[DeadLetter]] = defaultdict(list)
        self._spend: dict[tuple[str, date], Decimal] = defaultdict(Decimal)
        self._kill = KillSwitch()
        self._stops: list[
            OpenStop
        ] = []  # the open ones; a clear removes them (the history is not kept)
        self._ticks: dict[str, TickState] = {}
        self._tool_calls: dict[str, ToolCallRecord] = {}
        self._maps: dict[str, tuple[dict[str, str], datetime]] = {}
        self._reservations: dict[str, SpendReservation] = {}

    @staticmethod
    def _get(table: dict, key: str):
        try:
            return table[key].model_copy(deep=True)
        except KeyError:
            raise NotFound(key) from None

    def create_run(self, run: Run) -> None:
        with self._lock:
            if run.run_id in self._runs:
                raise StaleState(f"run exists: {run.run_id}")
            self._runs[run.run_id] = run.model_copy(deep=True)

    def get_run(self, run_id: str) -> Run:
        with self._lock:
            return self._get(self._runs, run_id)

    def transition(
        self, run_id: str, expected: RunState, new: RunState, reason_code: str | None = None
    ) -> Run:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise NotFound(run_id)
            if run.state != expected:
                raise StaleState(f"{run_id}: state is {run.state}, expected {expected}")
            run = run.model_copy(
                update={"state": new, "reason_code": reason_code, "updated_at": now()}
            )
            self._runs[run_id] = run
            return run.model_copy(deep=True)

    def add_cost(self, run_id: str, usd: Decimal) -> None:
        usd = clean_spend_amount(usd)
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise NotFound(run_id)
            with localcontext(defaults.money_context()):
                cost = run.cost_usd + usd
            self._runs[run_id] = run.model_copy(update={"cost_usd": cost})

    def touch(self, run_id: str) -> None:
        """Heartbeat only: moves `updated_at`, never checks or changes the state (`transition` is the only
        compare-and-set)."""
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise NotFound(run_id)
            self._runs[run_id] = run.model_copy(update={"updated_at": now()})

    def list_runs(self, state: RunState, updated_before: datetime, limit: int = 100) -> list[Run]:
        """Oldest first, at most `limit`."""
        with self._lock:
            found = sorted(
                (
                    r
                    for r in self._runs.values()
                    if r.state == state and r.updated_at < updated_before
                ),
                key=lambda r: r.updated_at,
            )
            return [r.model_copy(deep=True) for r in found[:limit]]

    def save_plan(self, plan: Plan) -> None:
        with self._lock:
            self._plans[plan.run_id] = plan.model_copy(deep=True)

    def get_plan(self, run_id: str) -> Plan:
        with self._lock:
            return self._get(self._plans, run_id)

    def save_gate_decision(self, decision: GateDecision) -> None:
        with self._lock:
            if decision.run_id in self._gates:
                raise StaleState(f"gate decision exists: {decision.run_id}")
            self._gates[decision.run_id] = decision.model_copy(deep=True)

    def get_gate_decision(self, run_id: str) -> GateDecision:
        with self._lock:
            return self._get(self._gates, run_id)

    def save_approval_request(self, req: ApprovalRequest) -> None:
        with self._lock:
            self._approvals[req.approval_id] = req.model_copy(deep=True)

    def get_approval_request(self, approval_id: str) -> ApprovalRequest:
        with self._lock:
            return self._get(self._approvals, approval_id)

    def update_approval_request(
        self, req: ApprovalRequest, expected_status: str, expected_step: int
    ) -> None:
        with self._lock:
            cur = self._approvals.get(req.approval_id)
            if cur is None:
                raise NotFound(req.approval_id)
            if cur.status != expected_status or cur.current_step != expected_step:
                raise StaleState(f"{req.approval_id}: {cur.status}/{cur.current_step}")
            self._approvals[req.approval_id] = req.model_copy(deep=True)

    def record_decision(
        self,
        decision: ApprovalDecision,
        req: ApprovalRequest,
        expected_status: str,
        expected_step: int,
    ) -> None:
        with self._lock:
            cur = self._approvals.get(req.approval_id)
            if cur is None:
                raise NotFound(req.approval_id)
            key = (decision.approval_id, decision.step)
            stale = cur.status != expected_status or cur.current_step != expected_step
            if stale or any((d.approval_id, d.step) == key for d in self._decisions):
                raise StaleState(f"{req.approval_id}: {cur.status}/{cur.current_step}")
            self._decisions.append(decision.model_copy(deep=True))
            self._approvals[req.approval_id] = req.model_copy(deep=True)

    def list_due_approvals(self, now: datetime) -> list[ApprovalRequest]:
        with self._lock:
            return [
                r.model_copy(deep=True)
                for r in self._approvals.values()
                if r.status == "PENDING" and r.step_expires_at <= now
            ]

    def save_approval_decision(self, decision: ApprovalDecision) -> None:
        with self._lock:
            key = (decision.approval_id, decision.step)
            if any((d.approval_id, d.step) == key for d in self._decisions):
                raise StaleState(f"decision exists: {key}")
            self._decisions.append(decision.model_copy(deep=True))

    def get_approval_decision(self, approval_id: str) -> ApprovalDecision | None:
        with self._lock:
            for d in reversed(self._decisions):
                if d.approval_id == approval_id:
                    return d.model_copy(deep=True)
            return None

    def list_approvals(self, statuses: set[ApprovalStatus]) -> list[ApprovalRequest]:
        with self._lock:
            return [
                r.model_copy(deep=True) for r in self._approvals.values() if r.status in statuses
            ]

    def add_dead_letter(self, dl: DeadLetter) -> None:
        with self._lock:
            self._dead[dl.run_id].append(dl.model_copy(deep=True))

    def list_dead_letters(self, run_id: str) -> list[DeadLetter]:
        with self._lock:
            return [d.model_copy(deep=True) for d in self._dead.get(run_id, [])]

    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
        check_store_id(agent_id, "agent_id")  # the same refusals as the definer function
        check_spend_day(day)
        usd = clean_spend_amount(usd)  # a bad amount is a ValueError; -0 becomes 0
        with self._lock:
            with localcontext(defaults.money_context()):
                self._spend[(agent_id, day)] += usd
                month = self._month_total(agent_id, day)
            return self._spend[(agent_id, day)], month

    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
        with self._lock:
            month = self._month_total(agent_id, day)
            return self._spend.get((agent_id, day), Decimal(0)), month

    def get_kill_switch(self) -> KillSwitch:
        """ON while any stop is open (the oldest is reported), else the flag. Same reading as Postgres; the memory
        store still guarantees nothing about who may clear (any caller can)."""
        with self._lock:
            if self._stops:
                first = self._stops[0]
                return KillSwitch(on=True, by=first.by, ts=first.ts)
            return self._kill.model_copy(deep=True)

    def set_kill_switch(self, ks: KillSwitch) -> None:
        with self._lock:
            if ks.on:
                self._stops.append(OpenStop(id=str(uuid.uuid4()), by=ks.by, ts=ks.ts))
                return
            self._stops.clear()
            self._kill = ks.model_copy(deep=True)

    def open_stops(self) -> list[OpenStop]:
        with self._lock:
            return [s.model_copy() for s in sorted(self._stops, key=lambda s: s.ts)]

    def clear_stops(self, by: str, stop_ids: Sequence[str], audit_seq: int | None = None) -> None:
        with self._lock:
            wanted = set(stop_ids)
            self._stops = [s for s in self._stops if s.id not in wanted]
            self._kill = KillSwitch(on=False, by=by)

    def get_tick_state(self, step: str) -> TickState | None:
        with self._lock:
            state = self._ticks.get(step)
            return state.model_copy() if state else None

    def save_tick_state(self, state: TickState) -> None:
        with self._lock:
            self._ticks[state.step] = state.model_copy()

    def add_tool_call(self, call: ToolCallRecord) -> None:
        with self._lock:
            if call.call_id in self._tool_calls:
                raise StaleState(f"tool call exists: {call.call_id}")
            self._tool_calls[call.call_id] = call.model_copy(deep=True)

    def list_tool_calls(self, run_id: str) -> list[ToolCallRecord]:
        with self._lock:
            rows = [c for c in self._tool_calls.values() if c.run_id == run_id]
            return [
                c.model_copy(deep=True)
                for c in sorted(rows, key=lambda c: (c.created_at, c.call_id))
            ]

    def purge_tool_calls(self, before: datetime, *, keep_run_ids: frozenset[str]) -> int:
        with self._lock:
            gone = [
                k
                for k, c in self._tool_calls.items()
                if c.created_at < before and c.run_id not in keep_run_ids
            ]
            for k in gone:
                del self._tool_calls[k]
            return len(gone)

    def put_redaction_map(self, run_id: str, mapping: dict[str, str]) -> None:
        with self._lock:
            self._maps[run_id] = (dict(mapping), now())

    def get_redaction_map(self, run_id: str) -> dict[str, str] | None:
        with self._lock:
            found = self._maps.get(run_id)
            return dict(found[0]) if found else None

    def purge_redaction_maps(
        self, before: datetime, *, keep_run_ids: frozenset[str], keep_open: bool = True
    ) -> int:
        with self._lock:
            gone = []
            for k, (_, at) in self._maps.items():
                run = self._runs.get(k)
                if keep_open and run is not None and run.state in OPEN_STATES:
                    continue
                if (run.updated_at if run is not None else at) < before and k not in keep_run_ids:
                    gone.append(k)
            for k in gone:
                del self._maps[k]
            return len(gone)

    # --- spend reservations: the same rules as the Postgres store, under the one lock (one process only) ------

    def _month_total(self, agent_id: str, day: date) -> Decimal:
        with localcontext(defaults.money_context()):
            return sum(
                (
                    v
                    for (a, d), v in self._spend.items()
                    if a == agent_id and (d.year, d.month) == (day.year, day.month)
                ),
                Decimal(0),
            )

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
        check_store_id(agent_id, "agent_id")
        if run_id is not None:
            check_store_id(run_id, "run_id")
        check_spend_day(day)
        check_reservation_id(reservation_id)
        usd = clean_spend_amount(usd)
        check_spend_cap(day_cap)
        check_spend_cap(month_cap)
        with self._lock:
            prior = self._reservations.get(reservation_id)
            if prior is not None:
                if (prior.agent_id, prior.day, prior.reserved_usd, prior.run_id) == (
                    agent_id,
                    day,
                    usd,
                    run_id,
                ):
                    return  # a retry of a committed reserve: the same row, nothing booked again
                raise StaleState(f"spend reservation exists: {reservation_id}")
            booked = self._spend.get((agent_id, day), Decimal(0))
            with localcontext(defaults.money_context()):
                day_ok = booked < day_cap and booked + usd <= day_cap
            if not day_ok:
                raise SpendCapExceeded("day")
            month = self._month_total(agent_id, day)
            with localcontext(defaults.money_context()):
                month_ok = month < month_cap and month + usd <= month_cap
            if not month_ok:
                raise SpendCapExceeded("month")
            # the row is built first: a model that refuses its input must leave the counter alone
            row = SpendReservation(
                reservation_id=reservation_id,
                agent_id=agent_id,
                day=day,
                run_id=run_id,
                reserved_usd=usd,
                created_at=now(),
            )
            with localcontext(defaults.money_context()):
                self._spend[(agent_id, day)] = booked + usd  # the month is the sum over its days
            self._reservations[reservation_id] = row

    def settle_spend(
        self, reservation_id: str, actual_usd: Decimal, *, agent_id: str
    ) -> tuple[SpendReservation, bool]:
        check_reservation_id(reservation_id)
        actual_usd = clean_spend_amount(actual_usd)
        check_store_id(agent_id, "agent_id")
        with self._lock:
            row = self._reservations.get(reservation_id)
            if row is None or row.agent_id != agent_id:
                raise NotFound(reservation_id)
            if row.status == "settled":
                return row, False
            # settled_usd is what stays booked: after expiry the booked amount never goes down
            booked = max(actual_usd, row.reserved_usd) if row.status == "expired" else actual_usd
            if (row.agent_id, row.day) not in self._spend:
                raise RuntimeError("spend counter row missing")
            run = self._runs.get(row.run_id) if row.run_id is not None else None
            with localcontext(defaults.money_context()):
                new_run = (  # a missing run row moves only the counters
                    run.model_copy(update={"cost_usd": run.cost_usd + actual_usd})
                    if run is not None
                    else None
                )
            row = row.model_copy(
                update={"status": "settled", "settled_usd": booked, "closed_at": now()}
            )
            with localcontext(defaults.money_context()):
                self._spend[(row.agent_id, row.day)] += booked - row.reserved_usd
            if new_run is not None:
                self._runs[new_run.run_id] = new_run
            self._reservations[reservation_id] = row
            return row, True

    def expire_spend_reservations(self, older_than_s: int) -> int:
        check_expiry_age(older_than_s)
        with self._lock:
            at = now()
            cutoff = at - timedelta(seconds=older_than_s)
            old = [
                r
                for r in self._reservations.values()
                if r.status == "open" and r.created_at <= cutoff
            ]
            for r in old:  # a status change only: the counters keep the worst case
                self._reservations[r.reservation_id] = r.model_copy(
                    update={"status": "expired", "settled_usd": r.reserved_usd, "closed_at": at}
                )
            return len(old)

    def purge_spend_reservations(self, before: datetime) -> int:
        check_purge_bound(before)
        with self._lock:
            gone = [
                k
                for k, r in self._reservations.items()
                if r.status == "settled" and r.closed_at is not None and r.closed_at < before
            ]
            for k in gone:
                del self._reservations[k]
            return len(gone)
