"""Store suite: the public Store Protocol only, over every registered store kind (P2 adds postgres)."""

import random
import threading
import time
from datetime import date, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    ChainStep,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Plan,
    Run,
    RunState,
    Target,
    TickState,
    ToolCallRecord,
    now,
)
from hadavin_sdk.store.protocol import NotFound, StaleState
from tests.contracts.store_support import utc_today

S = RunState


def _run(store, state=S.RECEIVED):
    run = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    if state is not S.RECEIVED:
        store.transition(run.run_id, S.RECEIVED, state)
    return store.get_run(run.run_id)


def _request(store, status="PENDING", expires_in=timedelta(minutes=1)):
    req = ApprovalRequest(
        run_id="run-x",
        plan_hash="h",
        risk_class="reversible",
        chain_id="c",
        steps=[ChainStep(approver_ids=["user:a"], timeout_s=60)],
        status=status,
        step_expires_at=now() + expires_in,
        requested_by="svc:a",
        summary="s",
    )
    store.save_approval_request(req)
    return req


def test_runs_are_copies_and_unknown_is_not_found(store):
    run = _run(store)
    got = store.get_run(run.run_id)
    got.state = S.SUCCEEDED
    assert store.get_run(run.run_id).state == S.RECEIVED
    with pytest.raises(NotFound):
        store.get_run("run-missing")


def test_transition_is_compare_and_set(store):
    run = _run(store)
    moved = store.transition(run.run_id, S.RECEIVED, S.WORKING, "why")
    assert (moved.state, moved.reason_code) == (S.WORKING, "why")
    with pytest.raises(StaleState):
        store.transition(run.run_id, S.RECEIVED, S.WORKING)


def test_add_cost_accumulates_and_unknown_run_is_not_found(store):
    run = _run(store)
    store.add_cost(run.run_id, Decimal("0.25"))
    store.add_cost(run.run_id, Decimal("0.50"))
    assert store.get_run(run.run_id).cost_usd == Decimal("0.75")
    with pytest.raises(NotFound):
        store.add_cost("run-missing", Decimal(1))


def test_touch_moves_updated_at_and_keeps_state(store):
    run = _run(store, S.WORKING)
    time.sleep(0.01)
    store.touch(run.run_id)
    got = store.get_run(run.run_id)
    assert got.updated_at > run.updated_at and got.state == S.WORKING
    with pytest.raises(NotFound):
        store.touch("run-missing")


def test_list_runs_by_state_age_and_limit(store):
    a, b = _run(store, S.WORKING), _run(store, S.WORKING)
    _run(store, S.RECEIVED)
    cutoff = now() + timedelta(seconds=1)
    found = store.list_runs(S.WORKING, cutoff)
    assert {r.run_id for r in found} == {a.run_id, b.run_id}
    assert [r.run_id for r in found] == sorted(
        [a.run_id, b.run_id], key=lambda i: store.get_run(i).updated_at
    )  # oldest first
    assert len(store.list_runs(S.WORKING, cutoff, limit=1)) == 1
    assert store.list_runs(S.WORKING, a.updated_at - timedelta(seconds=1)) == []


def test_approval_request_update_is_compare_and_set(store):
    req = _request(store)
    store.update_approval_request(req.model_copy(update={"status": "APPROVED"}), "PENDING", 0)
    assert store.get_approval_request(req.approval_id).status == "APPROVED"
    with pytest.raises(StaleState):
        store.update_approval_request(req.model_copy(update={"status": "REJECTED"}), "PENDING", 0)
    with pytest.raises(NotFound):
        store.get_approval_request("apr-missing")


def test_due_approvals_are_pending_and_expired(store):
    due = _request(store, expires_in=timedelta(seconds=-1))
    _request(store)
    _request(store, status="APPROVED", expires_in=timedelta(seconds=-1))
    assert [r.approval_id for r in store.list_due_approvals(now())] == [due.approval_id]


def test_get_approval_decision_returns_latest_or_none(store):
    assert store.get_approval_decision("apr-x") is None

    def decision(step, verdict):
        return ApprovalDecision(
            approval_id="apr-x",
            plan_hash="h",
            step=step,
            decision=verdict,
            approver_id="user:a",
            channel="fake",
        )

    store.save_approval_decision(decision(0, "reject"))
    store.save_approval_decision(decision(1, "approve"))
    assert store.get_approval_decision("apr-x").decision == "approve"
    with pytest.raises(StaleState):  # one decision per step: a racing or replayed one is refused
        store.save_approval_decision(decision(1, "reject"))
    assert store.get_approval_decision("apr-x").decision == "approve"


def test_gate_decision_is_written_once(store):
    d = GateDecision(run_id="run-g", plan_hash="h", outcome="allow", rule_id="r")
    store.save_gate_decision(d)
    with pytest.raises(StaleState):
        store.save_gate_decision(d.model_copy(update={"outcome": "deny"}))
    assert store.get_gate_decision("run-g").outcome == "allow"


def test_tick_state_round_trip(store):
    assert store.get_tick_state("sweep") is None
    at = now()
    store.save_tick_state(TickState(step="sweep", last_run_at=at, last_error="X: y"))
    store.save_tick_state(TickState(step="sweep", last_run_at=at, last_ok_at=at))
    got = store.get_tick_state("sweep")
    assert (got.last_run_at, got.last_ok_at, got.last_error) == (at, at, None)


def test_sent_at_and_channel_ref_round_trip(store):
    req = _request(store)
    assert (req.sent_at, req.channel_ref) == (None, None)
    sent = req.model_copy(update={"sent_at": now(), "channel_ref": "ts-1"})
    store.update_approval_request(sent, "PENDING", 0)
    assert store.get_approval_request(req.approval_id).channel_ref == "ts-1"


def test_list_approvals_by_status(store):
    pending, done = _request(store), _request(store)
    store.update_approval_request(done.model_copy(update={"status": "APPROVED"}), "PENDING", 0)
    assert [r.approval_id for r in store.list_approvals({"PENDING"})] == [pending.approval_id]
    assert {r.approval_id for r in store.list_approvals({"PENDING", "APPROVED"})} == {
        pending.approval_id,
        done.approval_id,
    }
    assert store.list_approvals({"EXPIRED"}) == []


def test_spend_day_and_month_totals(store):
    today = now().date()
    assert store.spend_totals("a", today) == (Decimal(0), Decimal(0))
    assert store.spend_totals("a", today) == (Decimal(0), Decimal(0))  # a read writes nothing
    store.add_spend("a", today, Decimal("0.40"))
    assert store.add_spend("a", today, Decimal("0.10")) == (Decimal("0.50"), Decimal("0.50"))
    _, month = store.add_spend("a", today - timedelta(days=40), Decimal(5))
    assert month == Decimal(5)
    assert store.spend_totals("a", today) == (Decimal("0.50"), Decimal("0.50"))


def test_month_total_spans_days_and_money_is_exact(store):
    d1, d2 = date(2026, 3, 10), date(2026, 3, 11)
    store.add_spend("m", d1, Decimal("0.00108225"))
    day, month = store.add_spend("m", d2, Decimal("0.5"))
    assert (day, month) == (Decimal("0.5"), Decimal("0.50108225"))
    assert store.spend_totals("m", d1) == (Decimal("0.00108225"), Decimal("0.50108225"))
    run = _run(store)
    store.add_cost(run.run_id, Decimal("0.00108225"))
    assert store.get_run(run.run_id).cost_usd == Decimal("0.00108225")


def test_dead_letters_and_kill_switch(store):
    store.add_dead_letter(DeadLetter(run_id="run-x", reason="r", errors=["e"]))
    assert [d.reason for d in store.list_dead_letters("run-x")] == ["r"]
    assert store.list_dead_letters("run-y") == []
    assert store.get_kill_switch().on is False
    store.set_kill_switch(KillSwitch(on=True, by="user:a"))
    assert (store.get_kill_switch().on, store.get_kill_switch().by) == (True, "user:a")


def test_two_threads_racing_one_cas_exactly_one_wins(store):
    run = _run(store)
    results = []
    gate = threading.Barrier(2)

    def race():
        gate.wait()
        try:
            store.transition(run.run_id, S.RECEIVED, S.WORKING)
            results.append("won")
        except StaleState:
            results.append("stale")

    threads = [threading.Thread(target=race) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["stale", "won"]


def test_record_decision_is_atomic(store):
    req = _request(store)
    d = ApprovalDecision(
        approval_id=req.approval_id,
        plan_hash="h",
        step=0,
        decision="reject",
        approver_id="user:a",
        channel="fake",
    )
    approved = req.model_copy(update={"status": "APPROVED"})
    with pytest.raises(StaleState):  # the request is not at step 1: nothing is written
        store.record_decision(d, approved, "PENDING", 1)
    assert store.get_approval_decision(req.approval_id) is None
    assert store.get_approval_request(req.approval_id).status == "PENDING"
    store.record_decision(d, approved, "PENDING", 0)
    assert store.get_approval_decision(req.approval_id).decision == "reject"
    with pytest.raises(StaleState):  # a second click on the same step
        store.record_decision(d, approved, "PENDING", 0)


# --- evidence (K5): tool calls and redaction maps --------------------------------------------------------------------


def _call(run_id, n, age=timedelta(0), **kw):
    return ToolCallRecord(
        call_id=f"{run_id}:{n}",
        run_id=run_id,
        tool="read_logs",
        inputs=kw.pop("inputs", {"name": "app", "n": n}),
        output=kw.pop("output", f"line {n}"),
        output_sha256="a" * 64,
        created_at=now() - age,
        **kw,
    )


def test_tool_calls_round_trip_in_order_and_refuse_a_duplicate(store):
    first, second = (
        _call("run-a", 1, timedelta(seconds=5), duration_ms=7, attempt=1),
        _call("run-a", 2),
    )
    store.add_tool_call(second)
    store.add_tool_call(first)
    got = store.list_tool_calls("run-a")
    assert [c.call_id for c in got] == ["run-a:1", "run-a:2"]
    assert (
        got[0].inputs == {"name": "app", "n": 1} and got[0].duration_ms == 7 and got[0].attempt == 1
    )
    assert got[1].duration_ms is None
    assert store.list_tool_calls("run-none") == []
    with pytest.raises(StaleState):
        store.add_tool_call(first)


def test_purge_tool_calls_keeps_held_runs_and_recent_rows(store):
    old_held, old_free, fresh = (
        _call("run-h", 1, timedelta(days=40)),
        _call("run-f", 1, timedelta(days=40)),
        _call("run-n", 1),
    )
    for c in (old_held, old_free, fresh):
        store.add_tool_call(c)
    cutoff = now() - timedelta(days=30)
    assert store.purge_tool_calls(cutoff, keep_run_ids=frozenset({"run-h"})) == 1
    assert [c.run_id for r in ("run-h", "run-f", "run-n") for c in store.list_tool_calls(r)] == [
        "run-h",
        "run-n",
    ]
    assert store.purge_tool_calls(cutoff, keep_run_ids=frozenset()) == 1
    assert store.list_tool_calls("run-h") == []


def test_redaction_map_upserts_and_a_missing_map_is_none(store):
    assert store.get_redaction_map("run-a") is None
    store.put_redaction_map("run-a", {"<IPV4_1>": "10.0.0.5"})
    store.put_redaction_map("run-a", {"<IPV4_1>": "10.0.0.5", "<EMAIL_1>": "a@example.test"})
    assert store.get_redaction_map("run-a") == {
        "<IPV4_1>": "10.0.0.5",
        "<EMAIL_1>": "a@example.test",
    }
    store.put_redaction_map("run-b", {})
    assert store.get_redaction_map("run-b") == {}  # an empty map is not a missing one
    got = store.get_redaction_map("run-a")
    got["<X_1>"] = "changed"
    assert "<X_1>" not in store.get_redaction_map("run-a")  # a copy


def test_purge_redaction_maps_keeps_held_runs(store):
    for run_id in ("run-h", "run-f"):
        store.put_redaction_map(run_id, {"<IPV4_1>": "10.0.0.5"})
    future = now() + timedelta(days=1)  # every row is older than this
    assert store.purge_redaction_maps(future, keep_run_ids=frozenset({"run-h"})) == 1
    assert store.get_redaction_map("run-f") is None and store.get_redaction_map("run-h")
    assert store.purge_redaction_maps(now() - timedelta(days=1), keep_run_ids=frozenset()) == 0
    assert store.purge_redaction_maps(future, keep_run_ids=frozenset()) == 1


def test_tool_calls_with_the_same_time_list_in_a_fixed_order(store):
    stamp = now()
    for n in (3, 1, 2):
        store.add_tool_call(_call("run-t", n).model_copy(update={"created_at": stamp}))
    ids = [c.call_id for c in store.list_tool_calls("run-t")]
    assert ids == ["run-t:1", "run-t:2", "run-t:3"]


def test_tool_call_error_flag_round_trips(store):
    store.add_tool_call(_call("run-e", 1, error=True, output="ERROR: boom"))
    store.add_tool_call(_call("run-e", 2))
    assert [c.error for c in store.list_tool_calls("run-e")] == [True, False]


def test_purge_redaction_maps_keeps_the_map_of_an_open_run_until_the_ceiling(store):
    awaiting = _run(store, S.WAITING_FOR_APPROVAL)
    done = _run(store, S.NO_ACTION)
    for run in (awaiting, done):
        store.put_redaction_map(run.run_id, {"<IPV4_1>": "10.0.0.5"})
    future = now() + timedelta(days=1)  # both runs last changed before this
    assert store.purge_redaction_maps(future, keep_run_ids=frozenset()) == 1
    assert store.get_redaction_map(done.run_id) is None
    assert store.get_redaction_map(awaiting.run_id) is not None
    assert store.purge_redaction_maps(future, keep_run_ids=frozenset(), keep_open=False) == 1
    assert store.get_redaction_map(awaiting.run_id) is None


def test_purge_redaction_maps_ages_a_run_parked_in_needs_person_like_a_finished_one(store):
    """Round 6: NEEDS_PERSON has no outgoing transition, so its map can never be restored again."""
    parked = _run(store, S.NEEDS_PERSON)
    store.put_redaction_map(parked.run_id, {"<IPV4_1>": "10.0.0.5"})
    assert store.purge_redaction_maps(now() + timedelta(days=1), keep_run_ids=frozenset()) == 1
    assert store.get_redaction_map(parked.run_id) is None


def test_purge_redaction_maps_ages_a_finished_run_from_when_it_finished(store):
    done = _run(store, S.NO_ACTION)
    store.put_redaction_map(done.run_id, {"<IPV4_1>": "10.0.0.5"})  # written after the run ended
    before_run_ended = done.updated_at - timedelta(seconds=1)
    assert store.purge_redaction_maps(before_run_ended, keep_run_ids=frozenset()) == 0
    assert store.purge_redaction_maps(now() + timedelta(days=1), keep_run_ids=frozenset()) == 1


def test_duplicate_run_id_is_stale_and_changes_nothing(store):
    """A second `create_run` with an id already stored raises `StaleState` and leaves the first run as it was
    (`Runtime.handle(run_id=...)` relies on this to tell "already started" from "new")."""
    first = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t-1")
    store.create_run(first)
    other = Run(
        run_id=first.run_id, agent_id="b", principal_id="q", trigger_kind="user", trigger_ref="t-2"
    )
    with pytest.raises(StaleState):
        store.create_run(other)
    with pytest.raises(StaleState):
        store.create_run(first)  # the very same run, again
    got = store.get_run(first.run_id)
    assert (got.agent_id, got.principal_id, got.trigger_kind, got.trigger_ref) == (
        "a",
        "p",
        "event",
        "t-1",
    )


_RUN_KW = {"agent_id": "a", "principal_id": "p", "trigger_kind": "event"}


def test_concurrent_create_run_with_one_id_has_one_winner(store):
    """Eight threads create a run with the same id at the same moment: one succeeds, seven get `StaleState`."""
    shared_id = Run(**_RUN_KW, trigger_ref="-").run_id
    gate = threading.Barrier(8)
    won, stale, other = [], [], []

    def go(i):
        run = Run(run_id=shared_id, **{**_RUN_KW, "trigger_ref": f"t-{i}"})
        gate.wait()
        try:
            store.create_run(run)
            won.append(i)
        except StaleState:
            stale.append(i)
        except Exception as exc:  # noqa: BLE001 - anything else is a failure, reported below
            other.append(exc)

    threads = [threading.Thread(target=go, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not other
    assert len(won) == 1 and len(stale) == 7
    assert store.get_run(shared_id).trigger_ref == f"t-{won[0]}"


def _plan(run_id, outcome="done"):
    return Plan(
        run_id=run_id,
        agent_id="a",
        action_id="act",
        action_version=1,
        risk_class="reversible",
        inputs={"k": 1},
        target=Target(system="crm", ref="r-1"),
        idempotency_key="idem-1",
        expected_outcome=outcome,
    )


def test_plan_round_trip_replace_and_unknown_is_not_found(store):
    """P4d-a1: `save_plan` and `get_plan` were called by no contract test before (the session-end check
    found them)."""
    run = _run(store)
    first = _plan(run.run_id, "first")
    store.save_plan(first)
    assert store.get_plan(run.run_id) == first
    second = _plan(run.run_id, "second")  # a new plan for the same run replaces the old one
    store.save_plan(second)
    got = store.get_plan(run.run_id)
    assert got == second
    assert got.plan_id != first.plan_id
    with pytest.raises(NotFound):
        store.get_plan("run-missing")


# --- model-based property test (P4d-a1 skeleton over the existing methods; P4d-b adds the reservation ones) --
SEEDS = range(200)
STEPS = 30


def _month_key(day):
    """The reference model keys months by integer arithmetic, independent of the code's `day.replace(day=1)`."""
    return day.year * 12 + day.month


def test_spend_and_cost_counters_match_a_plain_python_ledger(store):
    """200 fixed seeds x 30 steps of add_spend / add_cost / spend_totals against a reference ledger. Each seed has
    its own agent id, so one store serves all seeds with no reset (the runtime role cannot truncate)."""
    today = utc_today(store)
    days = [today + timedelta(days=k) for k in range(-45, 3)]  # spans two or three calendar months
    for seed in SEEDS:
        rng = random.Random(seed)  # noqa: S311 - a seeded test generator, not a secret
        agent = f"agent-{seed}"
        runs = [_run(store) for _ in range(2)]
        day_total: dict = {}
        month_total: dict = {}
        run_total = {r.run_id: Decimal(0) for r in runs}
        for _ in range(STEPS):
            kind = rng.choice(["spend", "spend", "cost", "totals"])
            day = rng.choice(days)
            usd = Decimal(rng.randrange(0, 5_000_000)) / Decimal(1_000_000)
            if kind == "spend":
                day_total[day] = day_total.get(day, Decimal(0)) + usd
                month_total[_month_key(day)] = month_total.get(_month_key(day), Decimal(0)) + usd
                got = store.add_spend(agent, day, usd)
                assert got == (day_total[day], month_total[_month_key(day)]), (seed, day)
            elif kind == "cost":
                run = rng.choice(runs)
                run_total[run.run_id] += usd
                store.add_cost(run.run_id, usd)
            else:
                want = (
                    day_total.get(day, Decimal(0)),
                    month_total.get(_month_key(day), Decimal(0)),
                )
                assert store.spend_totals(agent, day) == want, (seed, day)
            for run in runs:
                assert store.get_run(run.run_id).cost_usd == run_total[run.run_id], (
                    seed,
                    run.run_id,
                )


def test_store_pair_gives_two_handles_on_the_same_data(store_pair):
    """`a` writes, `b` reads it. Memory: one object twice (its contract). Postgres: two connections, so a race
    test over the pair tests the SQL and not the in-process lock of one handle."""
    a, b = store_pair
    run = _run(a)
    assert b.get_run(run.run_id).run_id == run.run_id
    b.add_cost(run.run_id, Decimal("0.5"))
    assert a.get_run(run.run_id).cost_usd == Decimal("0.5")
    if a.backend == "memory":
        assert a._inner is b._inner
    else:
        # Postgres only (memory has no connection): the four server processes are four different ones
        assert all(x != y for x, y in zip(a.connection_id, b.connection_id, strict=True))
