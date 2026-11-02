"""Store suite: the public Store Protocol only, over every registered store kind (P2 adds postgres)."""

import threading
import time
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    ChainStep,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Reservation,
    ReservationLimits,
    Run,
    RunState,
    TickState,
    now,
)
from hadavin_sdk.store.protocol import NotFound, StaleState
from hadavin_sdk.store.reservations import ReservationError

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


# ---------------------------------------------------------------- reservations (store-enforced limits)
def _res(key, *, tenant="t", scopes=None, actor="a", unit="USD", amount=100, at=None):
    return Reservation(
        tenant=tenant, key=key, scopes=scopes if scopes is not None else [f"s-{key}"], actor=actor, unit=unit, amount=amount,
        created_at=at or now(),
    )  # fmt: skip


LIM = ReservationLimits(max_per_scope=3, max_per_actor=3, unit_caps={"USD": 2500})
WAY_BACK = datetime(2000, 1, 1, tzinfo=UTC)


def test_reserve_caps_scope_actor_and_unit_total_from_the_stores_own_rows(store):
    for i in range(3):  # one subject, three actors: the scope limit bites
        assert store.reserve(_res(f"a{i}", scopes=["c1"], actor=f"x{i}"), LIM, WAY_BACK) is None
    assert store.reserve(_res("a9", scopes=["c1"], actor="x9"), LIM, WAY_BACK) == "OPEN_LIMIT"
    for i in range(3):  # one actor, three subjects: the actor limit bites
        assert store.reserve(_res(f"d{i}", actor="same"), LIM, WAY_BACK) is None
    assert store.reserve(_res("d9", actor="same"), LIM, WAY_BACK) == "OPEN_LIMIT"
    flood = [
        store.reserve(_res(f"f{i}", actor=f"f{i}", amount=100), LIM, WAY_BACK) for i in range(100)
    ]
    held = sum(r.amount for r in store.list_reservations("t", WAY_BACK))
    assert held <= 2500 and flood.count(None) > 0 and "OPEN_LIMIT" in flood


def test_reserve_is_idempotent_conflicting_and_typed(store):
    assert store.reserve(_res("k"), LIM, WAY_BACK) is None
    assert store.reserve(_res("k"), LIM, WAY_BACK) is None
    assert store.reserve(_res("k", amount=999), LIM, WAY_BACK) == "KEY_CONFLICT"
    assert [r.amount for r in store.list_reservations("t", WAY_BACK)] == [100]
    assert store.reserve(_res("u", unit="EUR"), LIM, WAY_BACK) == "UNIT_UNKNOWN", (
        "an unconfigured unit is not an OPEN_LIMIT"
    )


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda: _res("k", amount=0), "BAD_AMOUNT"),
        (lambda: _res("k", amount=-5), "BAD_AMOUNT"),
        (lambda: _res("k", scopes=[]), "BAD_SCOPES"),
        (lambda: _res("k", scopes=["a", "a"]), "BAD_SCOPES"),
        (lambda: _res("k", actor=""), "BAD_ACTOR"),
        (lambda: _res("\x00k"), "BAD_KEY"),
        (lambda: _res("k", tenant="t" * 300), "BAD_TENANT"),
        (lambda: _res("k", at=datetime(2026, 1, 1)), "NAIVE_TIME"),  # noqa: DTZ001 - the point
    ],
)
def test_reserve_refuses_malformed_input_with_a_typed_error(store, mutate, code):
    with pytest.raises(ReservationError) as e:
        store.reserve(mutate(), LIM, WAY_BACK)
    assert e.value.code == code and store.list_reservations("t", WAY_BACK) == []


def test_reserve_since_after_created_is_refused(store):
    with pytest.raises(ReservationError):
        store.reserve(_res("k", at=WAY_BACK), LIM, now())


def test_reserve_window_scoping_release_and_prune(store):
    old = now() - timedelta(days=2)
    assert store.reserve(_res("old", scopes=["c1"], actor="x", at=old), LIM, WAY_BACK) is None
    cut = now() - timedelta(days=1)
    for i in range(3):
        assert store.reserve(_res(f"n{i}", scopes=["c1"], actor=f"y{i}"), LIM, cut) is None, (
            "the 2-day-old hold does not count"
        )
    assert store.reserve(_res("n9", scopes=["c1"], actor="y9"), LIM, cut) == "OPEN_LIMIT"
    assert store.reserve(_res("n9", scopes=["c1"], actor="y9", tenant="other"), LIM, cut) is None, (
        "another tenant, same key"
    )
    assert store.reserve(_res("n0", scopes=["c1"], actor="y0", tenant="other"), LIM, cut) is None, (
        "and same content, still its own row"
    )
    assert {r.key for r in store.list_reservations("other", WAY_BACK)} == {"n9", "n0"}
    assert store.release_reservation("t", "n0") == 1 and store.release_reservation("t", "n0") == 0
    assert store.release_reservation("zzz", "n1") == 0, "release is tenant scoped"
    assert store.prune_reservations(cut) == 1, "only the 2-day-old row"
    assert "old" not in {r.key for r in store.list_reservations("t", WAY_BACK)}


def test_reserve_saves_the_approval_request_in_the_same_transaction_only_when_held(store):
    req = _request(store)  # saved once by itself
    other = req.model_copy(update={"approval_id": "apr-new"})
    full = ReservationLimits(max_per_scope=1, max_per_actor=9, unit_caps={"USD": 99999})
    assert store.reserve(_res("k1", scopes=["c1"]), full, WAY_BACK, request=other) is None
    assert store.get_approval_request("apr-new").approval_id == "apr-new"
    refused = req.model_copy(update={"approval_id": "apr-refused"})
    assert store.reserve(_res("k2", scopes=["c1"]), full, WAY_BACK, request=refused) == "OPEN_LIMIT"
    with pytest.raises(NotFound):
        store.get_approval_request("apr-refused")


def test_concurrent_reservations_cannot_both_slip_under_a_limit(store):
    out, lim = [], ReservationLimits(max_per_scope=3, max_per_actor=99, unit_caps={"USD": 10**9})
    ts = [
        threading.Thread(
            target=lambda i=i: out.append(
                store.reserve(_res(f"c{i}", scopes=["one"], actor=f"z{i}"), lim, WAY_BACK)
            )
        )
        for i in range(12)
    ]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert out.count(None) == 3 and out.count("OPEN_LIMIT") == 9
