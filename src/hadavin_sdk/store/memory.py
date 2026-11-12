"""In-memory store: dicts behind one lock. Rows are lost on restart (stated; Postgres comes with its trigger)."""

from __future__ import annotations

import threading
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

from hadavin_sdk.models import (
    INBOUND_FINAL_STATES,
    INBOUND_OPEN_STATES,
    INBOUND_RETRY_REASONS,
    OPEN_STATES,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    DeadLetter,
    GateDecision,
    InboundReceipt,
    InboundRunView,
    KillSwitch,
    Plan,
    Run,
    RunState,
    TickState,
    ToolCallRecord,
    check_inbound_move,
    inbound_reason_allowed,
    new_id,
    now,
)
from hadavin_sdk.store.protocol import NotFound, ReceiveResult, RerunRefused, StaleState


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
        self._ticks: dict[str, TickState] = {}
        self._tool_calls: dict[str, ToolCallRecord] = {}
        self._maps: dict[str, tuple[dict[str, str], datetime]] = {}
        # inbound ledger (AK-G2-a), keyed (tenant, source, delivery_key); one lock, like every other table here
        self._inbound: dict[tuple[str, str, str], InboundReceipt] = {}
        self._inbound_bodies: dict[tuple[str, str, str], bytes] = {}
        self._inbound_checks: dict[tuple[str, str], str] = {}

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
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise NotFound(run_id)
            self._runs[run_id] = run.model_copy(update={"cost_usd": run.cost_usd + usd})

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
        with self._lock:
            self._spend[(agent_id, day)] += usd
            month = sum(
                v
                for (a, d), v in self._spend.items()
                if a == agent_id and (d.year, d.month) == (day.year, day.month)
            )
            return self._spend[(agent_id, day)], Decimal(month)

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

    # --- inbound ledger (AK-G2-a) -----------------------------------------------------------------------------

    @staticmethod
    def _check_inbound_insert(rec: InboundReceipt) -> None:
        """The two legal shapes of a new receipt (the Postgres INSERT trigger's rule): a fresh `received` row with
        the run id of generation 0, or a `refused id_reuse` row with no run id."""
        if (
            rec.generation != 0
            or rec.attempts != 0
            or rec.last_reason is not None
            or rec.lease_until is not None
            or rec.claim_token is not None
            or rec.updated_at != rec.received_at
        ):
            raise ValueError("inbound receipt: not a legal new receipt")
        fresh = (
            rec.state == "received"
            and rec.reason is None
            and rec.reuse_of is None
            and rec.run_id == "run-" + rec.delivery_key[:28] + "0000"
        )
        reuse = (
            rec.state == "refused"
            and rec.reason == "id_reuse"
            and rec.reuse_of is not None
            and rec.run_id is None
        )
        if not (fresh or reuse):
            raise ValueError("inbound receipt: not a legal new receipt")

    def receive_inbound(
        self, rec: InboundReceipt, body: bytes | None, *, max_reuse: int, max_open: int
    ) -> ReceiveResult:
        self._check_inbound_insert(rec)
        key = (rec.tenant, rec.source, rec.delivery_key)
        with self._lock:
            stored = self._inbound_checks.setdefault((rec.tenant, rec.source), rec.key_check)
            if stored != rec.key_check:
                return "key_changed"
            if (found := self._inbound.get(key)) is not None:
                return "duplicate" if found.body_sha256 == rec.body_sha256 else "conflict"
            if rec.reuse_of is not None:
                reuse_rows = sum(
                    1
                    for r in self._inbound.values()
                    if r.tenant == rec.tenant
                    and r.source == rec.source
                    and r.reuse_of == rec.reuse_of
                )
                if reuse_rows >= max_reuse:
                    return "conflict_capped"
            if rec.state == "received":
                open_rows = sum(
                    1
                    for r in self._inbound.values()
                    if r.tenant == rec.tenant
                    and r.source == rec.source
                    and r.state in INBOUND_OPEN_STATES
                )
                if open_rows >= max_open:
                    return "busy"
            self._inbound[key] = rec.model_copy(deep=True)
            if body is not None:
                self._inbound_bodies[key] = bytes(body)
            return "new"

    def claim_inbound(
        self, tenant: str, source: str, now: datetime, lease_s: int
    ) -> InboundReceipt | None:
        with self._lock:
            ready = sorted(
                (
                    r
                    for r in self._inbound.values()
                    if r.tenant == tenant
                    and r.source == source
                    and (
                        r.state == "received"
                        or (
                            r.state == "claimed"
                            and r.lease_until is not None
                            and r.lease_until < now
                        )
                    )
                ),
                key=lambda r: (r.received_at, r.delivery_key),
            )
            if not ready:
                return None
            r = ready[0]
            taken = r.model_copy(
                update={
                    "attempts": r.attempts + (1 if r.state == "claimed" else 0),
                    "state": "claimed",
                    "claim_token": new_id("clm"),
                    "lease_until": now + timedelta(seconds=lease_s),
                    "updated_at": now,
                }
            )
            self._inbound[(tenant, source, r.delivery_key)] = taken
            return taken.model_copy(deep=True)

    def get_inbound_body(self, tenant: str, source: str, delivery_key: str) -> bytes | None:
        with self._lock:
            return self._inbound_bodies.get((tenant, source, delivery_key))

    def _claimed(self, tenant: str, source: str, delivery_key: str, token: str) -> InboundReceipt:
        r = self._inbound.get((tenant, source, delivery_key))
        if r is None:
            raise NotFound(delivery_key)
        if r.state != "claimed" or r.claim_token != token:
            raise StaleState("inbound receipt is not claimed with this token")
        return r

    def finish_inbound(
        self,
        tenant: str,
        source: str,
        delivery_key: str,
        claim_token: str,
        state: str,
        reason: str | None,
        now: datetime,
    ) -> None:
        if state not in INBOUND_FINAL_STATES or not inbound_reason_allowed(state, reason):
            raise ValueError("inbound finish: not a final state with an allowed reason")
        with self._lock:
            r = self._claimed(tenant, source, delivery_key, claim_token)
            check_inbound_move(r.state, state)
            self._inbound[(tenant, source, delivery_key)] = r.model_copy(
                update={
                    "state": state,
                    "reason": reason,
                    "lease_until": None,
                    "claim_token": None,
                    "updated_at": now,
                }
            )

    def release_inbound(
        self,
        tenant: str,
        source: str,
        delivery_key: str,
        claim_token: str,
        reason: str,
        now: datetime,
    ) -> None:
        if reason not in INBOUND_RETRY_REASONS:
            raise ValueError("inbound release: not a retry reason")
        with self._lock:
            r = self._claimed(tenant, source, delivery_key, claim_token)
            self._inbound[(tenant, source, delivery_key)] = r.model_copy(
                update={
                    "state": "received",
                    "last_reason": reason,
                    "lease_until": None,
                    "claim_token": None,
                    "attempts": r.attempts + (1 if reason == "step_error" else 0),
                    "updated_at": now,
                }
            )

    def reopen_inbound(
        self, tenant: str, source: str, delivery_key: str, now: datetime
    ) -> InboundReceipt:
        raise RerunRefused(
            "rerun_owner_only"
        )  # only the Postgres re-run owner role may; memory has no such role

    def _rerun_owner_reopen(
        self, tenant: str, source: str, delivery_key: str, now: datetime
    ) -> InboundReceipt:
        """Test seam (not in any protocol): the re-run owner's reopen, with the database rule's checks."""
        with self._lock:
            r = self._inbound.get((tenant, source, delivery_key))
            if r is None or r.state != "needs_person":
                raise NotFound(delivery_key) if r is None else StaleState("rerun_shape")
            run = self._runs.get(r.run_id) if r.run_id else None
            if run is not None and run.state in OPEN_STATES:
                raise StaleState("rerun_run_open")
            if r.generation + 1 > 65535:
                raise StaleState("rerun_shape")
            gen = r.generation + 1
            reopened = r.model_copy(
                update={
                    "state": "received",
                    "generation": gen,
                    "run_id": "run-" + r.delivery_key[:28] + format(gen, "04x"),
                    "attempts": 0,
                    "reason": None,
                    "last_reason": None,
                    "lease_until": None,
                    "claim_token": None,
                    "updated_at": now,
                }
            )
            self._inbound[(tenant, source, delivery_key)] = reopened
            return reopened.model_copy(deep=True)

    def list_inbound_sources(self) -> list[tuple[str, str, int]]:
        with self._lock:
            counts: dict[tuple[str, str], int] = defaultdict(int)
            for r in self._inbound.values():
                if r.state in ("received", "claimed", "needs_person"):
                    counts[(r.tenant, r.source)] += 1
            return [(t, s, n) for (t, s), n in sorted(counts.items())]

    def purge_inbound_bodies(self, before: datetime, ceiling: datetime) -> int:
        """Never an open receipt's text. Past `ceiling`: any final receipt's. Past `before`: a refused receipt's, or a
        done receipt whose run is missing or ended (not open, not waiting for a person, not stopped)."""
        held = OPEN_STATES | {RunState.NEEDS_PERSON, RunState.STOPPED}
        with self._lock:
            gone = []
            for key in self._inbound_bodies:
                r = self._inbound.get(key)
                if r is None or r.state not in INBOUND_FINAL_STATES:
                    continue
                run = self._runs.get(r.run_id) if r.run_id else None
                aged = r.updated_at < before and (
                    r.state == "refused"
                    or (r.state == "done" and (run is None or run.state not in held))
                )
                if r.updated_at < ceiling or aged:
                    gone.append(key)
            for key in gone:
                del self._inbound_bodies[key]
            return len(gone)

    def get_inbound_key_check(self, tenant: str, source: str) -> str | None:
        with self._lock:
            return self._inbound_checks.get((tenant, source))

    def set_inbound_key_check(
        self, tenant: str, source: str, old: str, new: str, now: datetime
    ) -> None:
        with self._lock:
            stored = self._inbound_checks.get((tenant, source))
            if stored is None:
                raise NotFound(f"{tenant}/{source}")
            if stored != old:
                raise StaleState("inbound key check changed")
            self._inbound_checks[(tenant, source)] = new

    def get_inbound_run(self, run_id: str) -> InboundRunView:
        with self._lock:
            run = self._get(self._runs, run_id)
        return InboundRunView(
            run_id=run.run_id,
            agent_id=run.agent_id,
            principal_id=run.principal_id,
            trigger_ref=run.trigger_ref,
            state=run.state,
            reason_code=run.reason_code,
            updated_at=run.updated_at,
        )
