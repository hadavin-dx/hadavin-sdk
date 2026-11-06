"""P4d-b: spend reservations on every store kind (the public Store protocol; Postgres-only rows use the owner login
through `pg_driver`). Each test uses its own agent id, so one store serves all of them."""

import itertools
from datetime import timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import KillSwitch, Run
from hadavin_sdk.store.protocol import (
    CounterDamaged,
    KillSwitchOn,
    NotFound,
    ReservationConflict,
    SpendCapExceeded,
    StaleState,
)
from tests.contracts.store_support import utc_today

D = Decimal
_ids = itertools.count()


def _rid(store, tag="r"):
    return f"{tag}-{next(_ids)}-{store.backend}"


def _run(store, agent="ag"):
    run = Run(agent_id=agent, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


def _reserve(store, agent, amount, *, rid=None, day=None, run=None, caps=(None, None, None), **kw):
    return store.reserve_spend(
        rid or _rid(store),
        agent,
        day or utc_today(store),
        D(amount),
        day_cap=caps[0],
        month_cap=caps[1],
        run_id=run.run_id if run else None,
        run_cap=caps[2],
        **kw,
    )


def _admin(store, sql, params=()):
    from tests.contracts.kinds.store_postgres import pg_driver

    drv = pg_driver()
    with drv.connect_admin(store.runtime_dsn) as conn:
        return drv.execute(conn, sql, params)


def _age(store, rid, seconds):
    """Make an open reservation `seconds` older: memory moves its clock; Postgres rewrites created_at as the owner
    with triggers off (the update trigger refuses the change otherwise)."""
    if store.backend == "memory":
        inner = store._inner
        row = inner._res[rid]
        inner._res[rid] = row.model_copy(
            update={"created_at": row.created_at - timedelta(seconds=seconds)}
        )
        return
    from tests.contracts.kinds.store_postgres import pg_driver

    drv = pg_driver()
    with drv.connect_admin(store.runtime_dsn) as conn:
        drv.execute(conn, "SET session_replication_role = replica")
        drv.execute(
            conn,
            "UPDATE spend_reservations SET created_at = created_at - make_interval(secs => %s) "
            "WHERE reservation_id = %s",
            (seconds, rid),
        )


def test_reserve_books_the_three_counters_and_returns_the_row(store):
    agent = "rs-book"
    run = _run(store, agent)
    out = _reserve(store, agent, "1.5", run=run, caps=(D(5), D(10), D(5)))
    assert out.applied is True
    r = out.reservation
    assert (r.status, r.reserved_usd, r.settled_usd, r.run_id) == (
        "open",
        D("1.5"),
        None,
        run.run_id,
    )
    assert r.reserved_usd.as_tuple().exponent == -6
    assert store.spend_totals(agent, utc_today(store)) == (D("1.5"), D("1.5"))
    assert store.get_run(run.run_id).cost_usd == D("1.5")
    assert store.get_spend_reservation(r.reservation_id).status == "open"
    assert [x.reservation_id for x in store.list_open_reservations(agent_id=agent)] == [
        r.reservation_id
    ]


def test_the_caps_are_keyword_only_with_no_default(store):
    with pytest.raises(TypeError):
        store.reserve_spend("x", "a", utc_today(store), D(1))


def test_a_cap_is_exact_at_the_boundary_and_one_micro_dollar_over_is_refused(store):
    agent = "rs-cap"
    _reserve(store, agent, "1", caps=(D(2), None, None))
    _reserve(store, agent, "1", caps=(D(2), None, None))  # lands exactly on the cap
    with pytest.raises(SpendCapExceeded) as e:
        _reserve(store, agent, "0.000001", caps=(D(2), None, None))
    assert (e.value.which, e.value.cap, e.value.requested) == ("day", D(2), D("0.000001"))
    assert store.spend_totals(agent, utc_today(store)) == (D(2), D(2))


def test_run_and_month_caps_are_exact_at_the_boundary_too(store):
    agent = "rs-cap2"
    run = _run(store, agent)
    for caps, which in (((None, None, D(2)), "run"), ((None, D(4), None), "month")):
        _reserve(store, agent, "1", run=run, caps=caps)
        _reserve(store, agent, "1", run=run, caps=caps)  # lands exactly on the cap
        with pytest.raises(SpendCapExceeded) as e:
            _reserve(store, agent, "0.000001", run=run, caps=caps)
        assert e.value.which == which


def test_the_first_failing_cap_is_named_in_the_order_run_day_month(store):
    agent = "rs-order"
    run = _run(store, agent)
    for caps, which in [
        ((D(0), D(0), D(0)), "run"),
        ((D(0), D(0), D(9)), "day"),
        ((D(9), D(0), D(9)), "month"),
    ]:
        with pytest.raises(SpendCapExceeded) as e:
            _reserve(store, agent, "1", run=run, caps=caps)
        assert e.value.which == which
    # nothing stayed booked and no reservation row was kept by the refused calls
    assert store.spend_totals(agent, utc_today(store)) == (0, 0)
    assert store.get_run(run.run_id).cost_usd == 0
    assert store.list_open_reservations(agent_id=agent) == []


def test_validation_comes_first_and_changes_nothing(store):
    agent = "rs-val"
    for kw in (
        {"amount": "0"},
        {"amount": "0.0000001"},
        {"caps": (D("0.000000001"), None, None)},
        {"caps": (D(-1), None, None)},
        {"meta": {"Bad": 1}},
        {"meta": {"k": 1.5}},
        {"meta": {f"k{'a' * 0}_{i}".replace("0", "z"): 1 for i in range(21)}},
        {"rid": "bad id"},
        {"day": utc_today(store) + timedelta(days=2)},
    ):
        amount = kw.pop("amount", "1")
        with pytest.raises(ValueError):
            _reserve(store, agent, amount, **kw)
    with pytest.raises(ValueError):  # run_cap without a run
        _reserve(store, agent, "1", caps=(None, None, D(1)))
    assert store.spend_totals(agent, utc_today(store)) == (0, 0)


def _meta_of_size(target, *, wide=False):
    """A valid meta whose json.dumps (the ticket's separators) is exactly `target` UTF-8 bytes; with `wide` one
    character is a two-byte `e` with an accent."""
    import json

    def size(m):
        return len(json.dumps(m, ensure_ascii=False, separators=(", ", ": ")).encode("utf-8"))

    for full in range(19):
        meta = {f"k_{chr(97 + i)}": "x" * 200 for i in range(full)}
        meta["pad"] = ""
        n = target - size(meta) - (2 if wide else 0)
        if 0 <= n <= 200:
            meta["pad"] = "x" * n + ("\u00e9" if wide else "")
            assert size(meta) == target
            return meta
    raise AssertionError("no layout")


def test_meta_is_stored_and_its_size_rule_is_the_same_on_both_stores(store):
    agent = "rs-meta"
    out = _reserve(store, agent, "1", meta={"team": "x", "n": 3, "ok": True})
    assert store.get_spend_reservation(out.reservation.reservation_id).meta == {
        "team": "x",
        "n": 3,
        "ok": True,
    }
    for wide in (False, True):
        _reserve(store, agent, "0.000001", meta=_meta_of_size(2000, wide=wide))
        with pytest.raises(ValueError):
            _reserve(store, agent, "0.000001", meta=_meta_of_size(2001, wide=wide))


def test_the_kill_switch_refuses_a_new_reserve_and_a_replay_but_not_settle_or_release(store):
    agent = "rs-kill"
    a = _reserve(store, agent, "1")
    b = _reserve(store, agent, "1")
    try:
        store.set_kill_switch(KillSwitch(on=True, by="user:t"))
        with pytest.raises(KillSwitchOn):
            _reserve(store, agent, "1")
        with pytest.raises(KillSwitchOn):
            _reserve(store, agent, "1", rid=a.reservation.reservation_id)
        assert store.settle_spend(a.reservation.reservation_id, D("0.5")).applied is True
        assert store.release_spend(b.reservation.reservation_id).applied is True
    finally:
        store.set_kill_switch(KillSwitch(on=False, by="user:t"))


def test_the_run_must_exist_and_belong_to_the_agent(store):
    agent = "rs-run"
    with pytest.raises(NotFound):
        store.reserve_spend(
            _rid(store),
            agent,
            utc_today(store),
            D(1),
            day_cap=None,
            month_cap=None,
            run_id="run-nope",
            run_cap=None,
        )
    other = _run(store, "someone-else")
    with pytest.raises(ValueError):
        _reserve(store, agent, "1", run=other)
    assert store.get_run(other.run_id).cost_usd == 0
    assert store.spend_totals(agent, utc_today(store)) == (0, 0)


def test_replay_conflict_and_closed_replay(store):
    agent = "rs-replay"
    rid = _rid(store)
    first = _reserve(store, agent, "1", rid=rid)
    again = _reserve(store, agent, "1.000000", rid=rid)
    assert (first.applied, again.applied) == (True, False)
    assert store.spend_totals(agent, utc_today(store)) == (D(1), D(1))
    for kw in ({"amount": "2"}, {}):
        with pytest.raises(ReservationConflict):
            _reserve(store, "other-agent" if not kw else agent, kw.get("amount", "1"), rid=rid)
    store.settle_spend(rid, D("0.4"))
    with pytest.raises(StaleState):
        _reserve(store, agent, "1", rid=rid)
    with pytest.raises(ReservationConflict):  # content check first, whatever the status
        _reserve(store, agent, "3", rid=rid)
    assert issubclass(ReservationConflict, StaleState)


def test_settle_below_equal_above_and_the_replays(store):
    agent = "rs-settle"
    run = _run(store, agent)
    day = utc_today(store)
    out = _reserve(store, agent, "1", run=run)
    rid = out.reservation.reservation_id
    s = store.settle_spend(rid, D("0.5"))
    assert (s.applied, s.reservation.status, s.reservation.settled_usd) == (
        True,
        "settled",
        D("0.5"),
    )
    assert s.reservation.closed_at is not None
    assert store.spend_totals(agent, day) == (D("0.5"), D("0.5"))
    assert store.get_run(run.run_id).cost_usd == D("0.5")
    r1 = store.settle_spend(rid, D(5))  # N10 r1: the FIRST result comes back, counters unchanged
    assert (r1.applied, r1.reservation.settled_usd) == (False, D("0.5"))
    assert store.spend_totals(agent, day) == (D("0.5"), D("0.5"))
    assert (
        store.release_spend(rid).applied is False
        and store.get_spend_reservation(rid).status == "settled"
    )
    # above the reservation: the full excess is booked, no cap, no ceiling
    up = _reserve(store, agent, "1", run=run)
    s2 = store.settle_spend(up.reservation.reservation_id, D("5"))
    assert s2.applied is True and s2.reservation.settled_usd == D(5)
    assert store.spend_totals(agent, day) == (D("5.5"), D("5.5"))
    assert store.get_run(run.run_id).cost_usd == D("5.5")
    # equal and zero
    eq = _reserve(store, agent, "1")
    store.settle_spend(eq.reservation.reservation_id, D(1))
    z = _reserve(store, agent, "1")
    assert store.settle_spend(z.reservation.reservation_id, D(0)).reservation.settled_usd == 0
    assert store.spend_totals(agent, day)[0] == D("6.5")


def test_settle_validates_first_and_refuses_more_than_six_decimals(store):
    agent = "rs-settle-val"
    rid = _reserve(store, agent, "1").reservation.reservation_id
    for bad in (D("0.0000013"), D("0.00000124"), D(-1), D("NaN"), D("1E+13"), 1):
        with pytest.raises(ValueError):
            store.settle_spend(rid, bad)
    assert store.get_spend_reservation(rid).status == "open"
    store.settle_spend(rid, D(1))
    with pytest.raises(ValueError):  # a malformed amount is refused even for a closed reservation
        store.settle_spend(rid, D("0.0000013"))
    with pytest.raises(NotFound):
        store.settle_spend("nope", D(1))


def test_release_gives_back_the_full_amount_and_replays(store):
    agent = "rs-release"
    run = _run(store, agent)
    rid = _reserve(store, agent, "2", run=run).reservation.reservation_id
    out = store.release_spend(rid)
    assert (out.applied, out.reservation.status, out.reservation.settled_usd) == (
        True,
        "released",
        None,
    )
    assert store.spend_totals(agent, utc_today(store)) == (0, 0)
    assert store.get_run(run.run_id).cost_usd == 0
    again = store.release_spend(rid)
    assert again.applied is False
    assert store.settle_spend(rid, D(1)).applied is False
    assert store.spend_totals(agent, utc_today(store)) == (0, 0)
    with pytest.raises(NotFound):
        store.release_spend("nope")
    with pytest.raises(StaleState):
        _reserve(store, agent, "2", rid=rid)


def test_sweep_expires_old_open_rows_without_moving_counters_and_an_expired_row_settles_once(store):
    agent = "rs-sweep"
    day = utc_today(store)
    old = _reserve(store, agent, "1").reservation.reservation_id
    _age(store, old, 120)
    for bad in (29, 10**7 + 1, True):
        with pytest.raises(ValueError):
            store.sweep_spend_reservations(bad)
    with pytest.raises(ValueError):
        store.sweep_spend_reservations(60, limit=0)
    swept = [r for r in store.sweep_spend_reservations(60, limit=1000) if r.agent_id == agent]
    assert [(r.reservation_id, r.status, r.settled_usd) for r in swept] == [(old, "expired", D(1))]
    assert swept[0].expired_at is not None and swept[0].closed_at is not None
    assert store.spend_totals(agent, day) == (D(1), D(1))  # no counter moved
    assert store.list_open_reservations(agent_id=agent) == []
    late = store.settle_spend(old, D("0.25"))  # an expired row may be corrected once
    assert (late.applied, late.reservation.status, late.reservation.settled_usd) == (
        True,
        "settled",
        D("0.25"),
    )
    assert late.reservation.expired_at == swept[0].expired_at
    assert store.spend_totals(agent, day) == (D("0.25"), D("0.25"))
    assert store.settle_spend(old, D(9)).applied is False


def test_an_expired_row_can_be_released_and_a_young_row_is_not_swept(store):
    agent = "rs-sweep2"
    day = utc_today(store)
    young = _reserve(store, agent, "1").reservation.reservation_id
    old = _reserve(store, agent, "2").reservation.reservation_id
    _age(store, old, 400)
    store.sweep_spend_reservations(300, limit=1000)
    assert store.get_spend_reservation(young).status == "open"
    assert store.get_spend_reservation(old).status == "expired"
    out = store.release_spend(old)
    assert (out.applied, out.reservation.status) == (
        True,
        "released",
    )  # N10 r2: full reserved amount drops
    assert store.spend_totals(agent, day) == (D(1), D(1))


def test_list_open_orders_by_creation_and_filters(store):
    agent = "rs-list"
    run = _run(store, agent)
    ids = [
        _reserve(store, agent, "1", run=run if i % 2 else None).reservation.reservation_id
        for i in range(4)
    ]
    got = store.list_open_reservations(agent_id=agent)
    assert [r.reservation_id for r in got] == ids
    assert [r.reservation_id for r in store.list_open_reservations(run_id=run.run_id)] == ids[1::2]
    assert len(store.list_open_reservations(agent_id=agent, limit=2)) == 2
    for bad in (0, 1001, True):
        with pytest.raises(ValueError):
            store.list_open_reservations(limit=bad)
    with pytest.raises(NotFound):
        store.get_spend_reservation("nope")


def test_a_damaged_counter_refuses_a_lowering_and_leaves_the_row_as_it_was(store):
    agent = "rs-damage"
    day = utc_today(store)
    rid = _reserve(store, agent, "1").reservation.reservation_id
    if store.backend == "postgres":
        _admin(store, "UPDATE spend SET usd = 0.5 WHERE agent_id = %s", (agent,))
    else:
        store._inner._spend[(agent, day)] = D("0.5")
    with pytest.raises(CounterDamaged):
        store.release_spend(rid)
    with pytest.raises(CounterDamaged):
        store.settle_spend(rid, D("0.2"))  # lowers by 0.8
    assert store.get_spend_reservation(rid).status == "open"
    assert store.spend_totals(agent, day)[0] == D("0.5")
    # the sweep still closes it without raising, and no counter moves
    _age(store, rid, 100)
    assert [
        r.reservation_id
        for r in store.sweep_spend_reservations(60, limit=1000)
        if r.agent_id == agent
    ] == [rid]


def test_a_missing_counter_row_is_damage_for_a_raise_too(store):
    agent = "rs-missing"
    day = utc_today(store)
    rid = _reserve(store, agent, "1").reservation.reservation_id
    if store.backend == "postgres":
        _admin(store, "DELETE FROM spend_month WHERE agent_id = %s", (agent,))
    else:
        del store._inner._spend[(agent, day)]
    with pytest.raises(CounterDamaged):
        store.settle_spend(rid, D(3))  # a raise: the missing row matches nothing
    assert store.get_spend_reservation(rid).status == "open"


def test_the_ceiling_refuses_a_reserve_after_every_cap_and_books_nothing(store):
    agent = "rs-ceiling"
    day = utc_today(store)
    run = _run(store, agent)
    ceiling = 10**15
    if store.backend == "postgres":
        _admin(store, "UPDATE runs SET cost_usd = %s WHERE run_id = %s", (ceiling, run.run_id))
    else:
        store._inner._runs[run.run_id] = store._inner._runs[run.run_id].model_copy(
            update={"cost_usd": D(ceiling)}
        )
    with pytest.raises(ValueError):
        _reserve(store, agent, "0.000001", run=run)
    assert store.spend_totals(agent, day) == (0, 0)
    assert store.get_run(run.run_id).cost_usd == ceiling
    # every cap is evaluated BEFORE the ceiling: the day cap of 0 wins over the run counter at the ceiling
    with pytest.raises(SpendCapExceeded) as e:
        _reserve(store, agent, "0.000001", run=run, caps=(D(0), None, None))
    assert e.value.which == "day"


def test_a_concurrent_pair_cannot_pass_the_cap(store_pair):
    import threading

    a, b = store_pair
    agent = "rs-race"
    day = utc_today(a)
    results = []

    def go(s, i):
        try:
            s.reserve_spend(
                f"race-{i}-{a.backend}",
                agent,
                day,
                D(1),
                day_cap=D(3),
                month_cap=None,
                run_cap=None,
            )
            results.append("ok")
        except SpendCapExceeded:
            results.append("cap")

    threads = [threading.Thread(target=go, args=(a if i % 2 else b, i)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["cap"] * 5 + ["ok"] * 3
    assert a.spend_totals(agent, day) == (D(3), D(3))


def test_the_day_must_be_within_one_day_of_the_store_date(store):
    agent = "rs-day"
    today = utc_today(store)
    _reserve(store, agent, "1", day=today - timedelta(days=1))
    _reserve(store, agent, "1", day=today + timedelta(days=1))
    for d in (today - timedelta(days=2), today + timedelta(days=2)):
        with pytest.raises(ValueError):
            _reserve(store, agent, "1", day=d)
