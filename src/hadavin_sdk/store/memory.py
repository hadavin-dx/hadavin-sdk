"""In-memory store: dicts behind one lock. Rows are lost on restart (stated; Postgres comes with its trigger)."""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable, Mapping
from datetime import date, datetime
from decimal import Decimal

from hadavin_sdk.models import (
    OPEN_STATES,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Plan,
    Run,
    RunState,
    SpendReservation,
    TickState,
    ToolCallRecord,
    now,
)
from hadavin_sdk.store.protocol import (
    MAX_COUNTER_USD,
    MIN_SWEEP_AGE_S,
    CounterDamaged,
    KillSwitchOn,
    NotFound,
    ReservationConflict,
    SpendCapExceeded,
    SpendOutcome,
    StaleState,
    check_day,
    check_id,
    check_int,
    check_reserve,
    check_usd,
)

_MICRO = Decimal("1E-6")


class MemoryStore:
    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        _checkpoint: Callable[[str], None] | None = None,
    ) -> None:
        """`clock` is an aware UTC wall clock (default `models.now`); it supplies the times and the UTC date of the
        reservations. `_checkpoint` is a test-only hook called at named points inside a write."""
        self._clock = clock or now
        self._checkpoint = _checkpoint or (lambda name: None)
        self._res: dict[str, SpendReservation] = {}
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
        self._ticks: dict[str, TickState] = {}
        self._tool_calls: dict[str, ToolCallRecord] = {}
        self._maps: dict[str, tuple[dict[str, str], datetime]] = {}

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
        check_usd(usd, max_decimals=8)
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise NotFound(run_id)
            total = (
                run.cost_usd + usd
            )  # first the new total, then the ceiling, and only then the change
            if total > MAX_COUNTER_USD:
                raise ValueError("the run counter would pass its ceiling")
            self._runs[run_id] = run.model_copy(update={"cost_usd": total})

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

    def _month_total(self, agent_id: str, day: date) -> Decimal:
        return Decimal(
            sum(
                (
                    v
                    for (a, d), v in self._spend.items()
                    if a == agent_id and (d.year, d.month) == (day.year, day.month)
                ),
                Decimal(0),
            )
        )

    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
        check_usd(usd, max_decimals=8)
        check_day(day)
        with self._lock:
            new_day = self._spend.get((agent_id, day), Decimal(0)) + usd
            new_month = self._month_total(agent_id, day) + usd
            if new_day > MAX_COUNTER_USD or new_month > MAX_COUNTER_USD:
                raise ValueError("a spend counter would pass its ceiling")
            self._spend[(agent_id, day)] = new_day
            return new_day, new_month

    # --- spend reservations (P4d-b) -------------------------------------------------------------------------

    def reserve_spend(
        self,
        reservation_id: str,
        agent_id: str,
        day: date,
        amount_usd: Decimal,
        *,
        day_cap: Decimal | None,
        month_cap: Decimal | None,
        run_id: str | None = None,
        run_cap: Decimal | None,
        meta: Mapping[str, str | int | bool] | None = None,
    ) -> SpendOutcome:
        amount, meta_ok = check_reserve(
            reservation_id, agent_id, day, amount_usd, day_cap, month_cap, run_id, run_cap, meta
        )
        with self._lock:
            if self._kill.on:
                raise KillSwitchOn("the kill switch is on")
            run = None
            if run_id is not None:
                run = self._runs.get(run_id)
                if run is None:
                    raise NotFound(run_id)
                if run.agent_id != agent_id:
                    raise ValueError("the run belongs to another agent")
            stored = self._res.get(reservation_id)
            if stored is not None:
                same = (
                    stored.agent_id == agent_id
                    and stored.day == day
                    and stored.reserved_usd == amount
                    and stored.run_id == run_id
                )
                if not same:
                    raise ReservationConflict(reservation_id)
                if stored.status != "open":
                    raise StaleState(f"reservation {reservation_id} is {stored.status}")
                return SpendOutcome(stored.model_copy(deep=True), False)
            stamp = self._clock()
            if abs((day - stamp.date()).days) > 1:
                raise ValueError("day must be within one day of today (UTC)")
            new_run = None if run is None else run.cost_usd + amount
            new_day = self._spend.get((agent_id, day), Decimal(0)) + amount
            new_month = self._month_total(agent_id, day) + amount
            for which, cap, new, cur in (
                ("run", run_cap, new_run, None if run is None else run.cost_usd),
                ("day", day_cap, new_day, new_day - amount),
                ("month", month_cap, new_month, new_month - amount),
            ):
                if cap is not None and new is not None and new > cap:
                    raise SpendCapExceeded(which, cap, cur, amount)
            if any(n is not None and n > MAX_COUNTER_USD for n in (new_run, new_day, new_month)):
                raise ValueError("a spend counter would pass its ceiling")
            self._checkpoint("reserve:before_counters")
            if run is not None:
                self._runs[run_id] = run.model_copy(update={"cost_usd": new_run})
            self._spend[(agent_id, day)] = new_day
            row = SpendReservation(
                reservation_id=reservation_id,
                agent_id=agent_id,
                day=day,
                run_id=run_id,
                reserved_usd=amount,
                created_at=stamp,
                meta=dict(meta_ok) if meta_ok is not None else None,
            )
            self._res[reservation_id] = row
            return SpendOutcome(row.model_copy(deep=True), True)

    def _close(self, reservation_id: str, status: str, actual: Decimal | None) -> SpendOutcome:
        """Settle or release under the lock: every damaged-counter check BEFORE the first change."""
        row = self._res.get(reservation_id)
        if row is None:
            raise NotFound(reservation_id)
        if row.status in ("settled", "released"):
            return SpendOutcome(row.model_copy(deep=True), False)
        # positive lowers the counters, negative raises them (a settle above the reservation books the excess)
        delta = row.reserved_usd if actual is None else row.reserved_usd - actual
        run = None
        if row.run_id is not None:
            run = self._runs.get(row.run_id)
            if run is None:
                raise CounterDamaged(f"run {row.run_id} is missing")
        key = (row.agent_id, row.day)
        if key not in self._spend:
            raise CounterDamaged("the day counter is missing")
        month = self._month_total(row.agent_id, row.day)
        if delta > 0 and (
            (run is not None and run.cost_usd < delta) or self._spend[key] < delta or month < delta
        ):
            raise CounterDamaged("a counter is lower than the amount to lower")
        if run is not None:
            self._runs[row.run_id] = run.model_copy(update={"cost_usd": run.cost_usd - delta})
        self._spend[key] -= delta
        done = row.model_copy(
            update={
                "status": status,
                "settled_usd": actual if status == "settled" else None,
                "closed_at": self._clock(),
            }
        )
        self._res[reservation_id] = done
        return SpendOutcome(done.model_copy(deep=True), True)

    def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendOutcome:
        check_id(reservation_id, "reservation_id")
        check_usd(actual_usd, max_decimals=6)
        with self._lock:
            return self._close(reservation_id, "settled", actual_usd.quantize(_MICRO))

    def release_spend(self, reservation_id: str) -> SpendOutcome:
        check_id(reservation_id, "reservation_id")
        with self._lock:
            return self._close(reservation_id, "released", None)

    def get_spend_reservation(self, reservation_id: str) -> SpendReservation:
        with self._lock:
            return self._get(self._res, reservation_id)

    def list_open_reservations(
        self, agent_id: str | None = None, run_id: str | None = None, limit: int = 100
    ) -> list[SpendReservation]:
        check_int(limit, 1, 1000)
        with self._lock:
            rows = sorted(
                (
                    r
                    for r in self._res.values()
                    if r.status == "open"
                    and (agent_id is None or r.agent_id == agent_id)
                    and (run_id is None or r.run_id == run_id)
                ),
                key=lambda r: (r.created_at, r.reservation_id),
            )
            return [r.model_copy(deep=True) for r in rows[:limit]]

    def sweep_spend_reservations(
        self, older_than_s: int, *, limit: int = 100
    ) -> list[SpendReservation]:
        check_int(older_than_s, MIN_SWEEP_AGE_S, 10**7)
        check_int(limit, 1, 1000)
        with self._lock:
            stamp = self._clock()
            old = sorted(
                (
                    r
                    for r in self._res.values()
                    if r.status == "open" and (stamp - r.created_at).total_seconds() > older_than_s
                ),
                key=lambda r: (r.created_at, r.reservation_id),
            )[:limit]
            out = []
            for r in old:
                done = r.model_copy(
                    update={
                        "status": "expired",
                        "settled_usd": r.reserved_usd,
                        "closed_at": stamp,
                        "expired_at": stamp,
                    }
                )
                self._res[r.reservation_id] = done
                out.append(done.model_copy(deep=True))
            return out

    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
        with self._lock:
            month = sum(
                (
                    v
                    for (a, d), v in self._spend.items()
                    if a == agent_id and (d.year, d.month) == (day.year, day.month)
                ),
                Decimal(0),
            )
            return self._spend.get((agent_id, day), Decimal(0)), month

    def get_kill_switch(self) -> KillSwitch:
        with self._lock:
            return self._kill.model_copy(deep=True)

    def set_kill_switch(self, ks: KillSwitch) -> None:
        with self._lock:
            self._kill = ks.model_copy(deep=True)

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
