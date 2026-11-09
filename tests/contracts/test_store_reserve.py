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
    from tests.contracts import pg_owner

    pg_owner.age(store.runtime_dsn, rid, seconds)


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


@pytest.mark.parametrize("bad", ["a\x00b", "a\ud800b"], ids=["nul", "lone_surrogate"])
def test_meta_text_is_refused_the_same_way_on_both_stores(store, bad):
    """Postgres cannot store NUL or a lone surrogate in text; memory must refuse them as well (parity), and a
    refused call books nothing."""
    agent = "rs-meta-text"
    with pytest.raises(ValueError):
        _reserve(store, agent, "1", meta={"team": bad})
    assert store.spend_totals(agent, utc_today(store)) == (0, 0)
    assert store.list_open_reservations(agent_id=agent) == []


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


MICRO = D("0.000001")


def _set_counter(store, which, agent, run, value):
    """Put one counter at `value` through the back door of each store."""
    day = utc_today(store)
    if store.backend == "postgres":
        if which == "run":
            _admin(store, "UPDATE runs SET cost_usd = %s WHERE run_id = %s", (value, run.run_id))
        elif which == "day":
            _admin(
                store,
                "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) "
                "ON CONFLICT (agent_id, day) DO UPDATE SET usd = EXCLUDED.usd",
                (agent, day, value),
            )
        else:
            _admin(
                store,
                "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) "
                "ON CONFLICT (agent_id, month) DO UPDATE SET usd = EXCLUDED.usd",
                (agent, day.replace(day=1), value),
            )
        return
    inner = store._inner
    if which == "run":
        inner._runs[run.run_id] = inner._runs[run.run_id].model_copy(update={"cost_usd": value})
    elif which == "day":
        inner._spend[(agent, day)] = value
    else:  # memory keeps days only: the month total is their sum, so use another day of the same month
        other = day.replace(day=15 if day.day != 15 else 16)
        inner._spend[(agent, other)] = value


@pytest.mark.parametrize("which", ["run", "day", "month"])
def test_the_ceiling_is_exact_for_each_counter_and_lowering_reopens_room(store, which):
    """Class: a ceiling off by one unit. A counter one micro-dollar below the ceiling accepts a reserve of one
    micro-dollar (it lands ON the ceiling), refuses the next one, and refuses a reserve of two at once; a release
    makes room again. Nothing is booked by a refused call."""
    ceiling = D(10**15)
    agent = f"rs-ceil-{which}"
    run = _run(store, agent)
    _set_counter(store, which, agent, run, ceiling - MICRO)
    day = utc_today(store)
    before_run = store.get_run(run.run_id).cost_usd

    first = _reserve(store, agent, "0.000001", run=run)
    assert first.applied is True
    with pytest.raises(ValueError):
        _reserve(store, agent, "0.000001", run=run)  # +1 micro over the ceiling
    with pytest.raises(ValueError):
        _reserve(store, agent, "0.000002", run=run)  # +2 micro over
    after = {
        "run": store.get_run(run.run_id).cost_usd,
        "day": store.spend_totals(agent, day)[0],
        "month": store.spend_totals(agent, day)[1],
    }
    assert after[which] == ceiling  # only the first reserve was booked
    assert (after["run"] - before_run) == MICRO  # the run counter moved by that one reserve only
    # the other direction: giving the first back makes room for exactly one micro-dollar again
    assert store.release_spend(first.reservation.reservation_id).applied is True
    assert _reserve(store, agent, "0.000001", run=run).applied is True
    with pytest.raises(ValueError):
        _reserve(store, agent, "0.000001", run=run)


def test_a_settle_above_the_reserved_amount_is_never_refused_by_the_ceiling(store):
    """[PL10]: settle books what was spent, even past the ceiling (the money is gone); nothing is refused."""
    agent = "rs-ceil-settle"
    ceiling = D(10**15)
    run = _run(store, agent)
    _set_counter(store, "day", agent, run, ceiling - MICRO)
    rid = _reserve(store, agent, "0.000001", run=run).reservation.reservation_id
    out = store.settle_spend(rid, D("5"))
    assert out.applied is True and out.reservation.settled_usd == D(5)
    assert store.spend_totals(agent, utc_today(store))[0] == ceiling - MICRO + D("4.999999") + MICRO


# --- B3 (e1, e2, e3): a settle never refuses an excess ------------------------------------------------------------

EXCESS_VALUES = [
    ("0.5", "5.0"),
    ("10", "20"),
    ("10", "20.000001"),
    ("0.5", "1.5"),
    ("0.5", "1.500001"),
]


def _counters(store, agent, run):
    day = utc_today(store)
    d, m = store.spend_totals(agent, day)
    return {"run": store.get_run(run.run_id).cost_usd, "day": d, "month": m}


def _nothing_below_zero(store, agent, run):
    assert all(v >= 0 for v in _counters(store, agent, run).values())


@pytest.mark.parametrize("closed_by", ["open", "expired"])
@pytest.mark.parametrize(("reserved", "actual"), EXCESS_VALUES)
def test_e1_e2_a_settle_above_the_reserved_amount_books_the_full_excess_on_all_three_counters(
    store, reserved, actual, closed_by
):
    agent = f"rs-e12-{closed_by}-{reserved}-{actual}"
    run = _run(store, agent)
    rid = _reserve(store, agent, reserved, run=run).reservation.reservation_id
    if closed_by == "expired":
        _age(store, rid, 120)
        assert [
            r.reservation_id
            for r in store.sweep_spend_reservations(60, limit=1000)
            if r.agent_id == agent
        ] == [rid]
    out = store.settle_spend(rid, D(actual))
    assert out.applied is True and out.reservation.status == "settled"
    assert out.reservation.settled_usd == D(actual)
    assert _counters(store, agent, run) == {"run": D(actual), "day": D(actual), "month": D(actual)}
    _nothing_below_zero(store, agent, run)


@pytest.mark.parametrize("which", ["run", "day", "month"])
def test_e3_after_a_settle_past_the_ceiling_only_lowering_writes_still_work(store, which):
    ceiling = D(10**15)
    agent = f"rs-e3-{which}"
    run = _run(store, agent)
    day = utc_today(store)
    _set_counter(store, which, agent, run, ceiling - 1)
    first = _reserve(store, agent, "0.5", run=run).reservation.reservation_id
    out = store.settle_spend(
        first, D("1.000001")
    )  # excess 0.500001: the counter ends above the ceiling
    assert out.applied is True
    before = _counters(store, agent, run)
    assert before[which] == ceiling + MICRO
    with pytest.raises(ValueError):
        _reserve(store, agent, "0.000001", run=run)
    if which == "run":
        with pytest.raises(ValueError):
            store.add_cost(run.run_id, MICRO)
    else:
        with pytest.raises(ValueError):
            store.add_spend(agent, day, MICRO)
    assert _counters(store, agent, run) == before  # nothing moved in any counter
    # a second setup: a lowering write still works at that level
    agent2 = f"rs-e3b-{which}"
    run2 = _run(store, agent2)
    _set_counter(store, which, agent2, run2, ceiling - 1)
    a = _reserve(store, agent2, "0.5", run=run2).reservation.reservation_id
    b = _reserve(store, agent2, "0.25", run=run2).reservation.reservation_id
    store.settle_spend(a, D("1.000001"))
    assert _counters(store, agent2, run2)[which] == ceiling + D("0.250001")
    released = store.release_spend(b)
    assert released.applied is True and released.reservation.status == "released"
    assert _counters(store, agent2, run2)[which] == ceiling + MICRO


# --- B3 release guard (r1 to r4) ----------------------------------------------------------------------------------


def _lower(store, which, agent, run, value):
    day = utc_today(store)
    if store.backend == "postgres":
        sql = {
            "run": ("UPDATE runs SET cost_usd = %s WHERE run_id = %s", (value, run.run_id)),
            "day": ("UPDATE spend SET usd = %s WHERE agent_id = %s", (value, agent)),
            "month": ("UPDATE spend_month SET usd = %s WHERE agent_id = %s", (value, agent)),
        }[which]
        _admin(store, *sql)
    elif which == "run":
        inner = store._inner
        inner._runs[run.run_id] = inner._runs[run.run_id].model_copy(update={"cost_usd": value})
    else:  # memory's month is the sum of its days, so lowering the day lowers both
        store._inner._spend[(agent, day)] = value


def _remove_month_counter(store, agent):
    if store.backend == "postgres":
        _admin(store, "DELETE FROM spend_month WHERE agent_id = %s", (agent,))
    else:
        del store._inner._spend[(agent, utc_today(store))]


def _snapshot(store, rid, agent, run):
    row = store.get_spend_reservation(rid)
    return (row.status, row.settled_usd, row.closed_at), _counters(store, agent, run)


@pytest.mark.parametrize("closed_by", ["open", "expired"])
@pytest.mark.parametrize("which", ["run", "day", "month", "missing-month-row"])
def test_r1_to_r4_a_release_with_a_damaged_counter_changes_nothing_and_works_after_repair(
    store, which, closed_by
):
    agent = f"rs-r-{which}-{closed_by}"
    run = _run(store, agent)
    rid = _reserve(store, agent, "2", run=run).reservation.reservation_id
    if closed_by == "expired":
        _age(store, rid, 120)
        store.sweep_spend_reservations(60, limit=1000)
    if which == "missing-month-row":
        _remove_month_counter(store, agent)
    else:
        _lower(store, which, agent, run, D("0.5"))
    before = _snapshot(store, rid, agent, run)
    with pytest.raises(CounterDamaged):
        store.release_spend(rid)
    assert _snapshot(store, rid, agent, run) == before  # the row was not left half-closed
    # repair by hand: every counter back to the reserved amount, then the release succeeds (r4)
    day = utc_today(store)
    for w in ("run", "day", "month"):
        if which == "missing-month-row" and w in ("day", "month"):
            if store.backend == "postgres":
                _admin(
                    store,
                    "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, 2) "
                    "ON CONFLICT (agent_id, month) DO UPDATE SET usd = 2",
                    (agent, day.replace(day=1)),
                )
            else:
                store._inner._spend[(agent, day)] = D(2)
            break
        _lower(store, w, agent, run, D(2))
        if store.backend == "memory" and w == "day":
            break
    out = store.release_spend(rid)
    assert out.applied is True and out.reservation.status == "released"
    _nothing_below_zero(store, agent, run)


# --- B5: 10,000 tiny pairs equal the exact sum --------------------------------------------------------------------


def test_b5_ten_thousand_reserve_settle_pairs_equal_the_exact_decimal_sum(store):
    agent = "rs-b5"
    run = _run(store, agent)
    expected = D(0)
    for i in range(10_000):
        micro = (i * 7919) % 999_983 + 1  # six decimals, never zero
        reserved = D(micro) / D(10**6)
        settled = D(micro * 3 // 4) / D(10**6)
        rid = f"b5-{i}-{store.backend}"
        store.reserve_spend(
            rid,
            agent,
            utc_today(store),
            reserved,
            day_cap=None,
            month_cap=None,
            run_id=run.run_id,
            run_cap=None,
        )
        store.settle_spend(rid, settled)
        expected += settled
    assert _counters(store, agent, run) == {"run": expected, "day": expected, "month": expected}


# --- B5: the model-based property test (200 fixed seeds x 30 steps, both stores) -----------------------------------

MODEL_SEEDS = range(200)
MODEL_STEPS = 30


def _month_key(day):
    """Integer months, independent of the code's `day.replace(day=1)`."""
    return day.year * 12 + day.month


class _Ledger:
    """The model's three counters: run cost, per day, per month."""

    def __init__(self):
        self.run, self.day, self.month = D(0), {}, {}

    def move(self, row, delta):
        self.run += delta if row["run"] else 0
        self.day[row["day"]] = self.day.get(row["day"], D(0)) + delta
        key = _month_key(row["day"])
        self.month[key] = self.month.get(key, D(0)) + delta


def _micro(rng, high):
    return D(rng.randrange(1, high)) / D(10**6)


def test_b5_model_reserve_settle_release_and_sweep_match_a_plain_python_ledger(store):
    """Each seed has its own agent and run, so one store serves all seeds (the runtime role cannot truncate).
    The model is a dict of reservations and three counters. Memory also runs `sweep_spend_reservations`, aging
    the chosen open rows first; Postgres runs the same sequences without sweeps (its sweep is proved in B7 with
    the owner fixture, because the database clock and the insert trigger make aging impossible here)."""
    from tests.contracts.test_store import _SeededChoices

    today = utc_today(store)
    days = [today + timedelta(days=k) for k in (-1, 0, 1)]
    counts = {
        "granted": 0,
        "refused": 0,
        "settled": 0,
        "released": 0,
        "expired": 0,
        "closed_replay": 0,
    }
    ops = ["reserve", "reserve", "reserve", "settle", "settle", "release", "replay", "check"]
    if store.backend == "memory":
        ops.append("sweep")
    for seed in MODEL_SEEDS:
        rng = _SeededChoices(seed)
        agent = f"pm-{seed}-{store.backend}"
        run = _run(store, agent)
        res: dict[str, dict] = {}
        ledger = _Ledger()
        day_tot, month_tot = ledger.day, ledger.month
        for step in range(MODEL_STEPS):
            where = (seed, step)
            op = rng.choice(ops)
            open_ids = [r for r, v in sorted(res.items()) if v["status"] in ("open", "expired")]
            if op == "reserve":
                rid = f"pm-{seed}-{step}-{store.backend}"
                row = {
                    "amount": _micro(rng, 2_000_000),
                    "day": rng.choice(days),
                    "run": rng.choice([True, False]),
                    "status": "open",
                    "settled": None,
                }
                caps = [
                    rng.choice([None, _micro(rng, 8_000_000)]) for _ in range(3)
                ]  # day, month, run
                if not row["run"]:
                    caps[2] = None  # a run cap needs a run
                refused = None
                for which, total, cap in (
                    ("run", ledger.run if row["run"] else None, caps[2]),
                    ("day", day_tot.get(row["day"], D(0)), caps[0]),
                    ("month", month_tot.get(_month_key(row["day"]), D(0)), caps[1]),
                ):
                    if cap is not None and total is not None and total + row["amount"] > cap:
                        refused = which
                        break
                try:
                    out = _reserve(
                        store,
                        agent,
                        row["amount"],
                        rid=rid,
                        day=row["day"],
                        run=run if row["run"] else None,
                        caps=tuple(caps),
                    )
                except SpendCapExceeded as exc:
                    assert refused == exc.which, where
                    with pytest.raises(NotFound):
                        store.get_spend_reservation(rid)
                    counts["refused"] += 1
                else:
                    assert refused is None and out.applied is True, where
                    res[rid] = row
                    ledger.move(row, row["amount"])
                    counts["granted"] += 1
            elif op == "replay" and res:
                rid = rng.choice(sorted(res))
                row = res[rid]
                same = {
                    "day": row["day"],
                    "run": run if row["run"] else None,
                    "rid": rid,
                    "caps": (None, None, None),
                }
                if rng.choice([True, False]):  # the same content
                    if row["status"] == "open":
                        out = _reserve(store, agent, row["amount"], **same)
                        assert out.applied is False and out.reservation.status == "open", where
                    else:
                        with pytest.raises(StaleState):
                            _reserve(store, agent, row["amount"], **same)
                        counts["closed_replay"] += 1
                else:  # other content: conflict whatever the status
                    with pytest.raises(ReservationConflict):
                        _reserve(store, agent, row["amount"] + D("0.000001"), **same)
            elif op in ("settle", "release") and res:
                rid = rng.choice(sorted(res))
                row = res[rid]
                actual = _micro(rng, 3_000_000) if op == "settle" else None
                out = (
                    store.settle_spend(rid, actual) if op == "settle" else store.release_spend(rid)
                )
                if row["status"] in ("open", "expired"):
                    assert out.applied is True, where
                    ledger.move(row, (actual if actual is not None else D(0)) - row["amount"])
                    row["status"] = "settled" if op == "settle" else "released"
                    row["settled"] = actual
                    counts["settled" if op == "settle" else "released"] += 1
                else:
                    assert out.applied is False, where
                assert out.reservation.status == row["status"], where
                assert out.reservation.settled_usd == row["settled"], where
            elif op == "sweep":
                aged = [
                    r for r in open_ids if res[r]["status"] == "open" and rng.choice([True, False])
                ]
                for rid in aged:
                    _age(store, rid, 600)
                swept = [
                    r.reservation_id
                    for r in store.sweep_spend_reservations(60, limit=1000)
                    if r.agent_id == agent
                ]
                assert swept == sorted(
                    swept, key=lambda r: (store.get_spend_reservation(r).created_at, r)
                )
                assert sorted(swept) == sorted(aged), where
                for rid in aged:
                    res[rid]["status"], res[rid]["settled"] = "expired", res[rid]["amount"]
                    counts["expired"] += 1
            # after every step: counters, run cost, each row and the open list equal the model
            for d in days:
                assert store.spend_totals(agent, d) == (
                    day_tot.get(d, D(0)),
                    month_tot.get(_month_key(d), D(0)),
                ), where
            assert store.get_run(run.run_id).cost_usd == ledger.run, where
            for rid, row in res.items():
                got = store.get_spend_reservation(rid)
                assert (got.status, got.settled_usd, got.reserved_usd) == (
                    row["status"],
                    row["settled"],
                    row["amount"],
                ), (where, rid)
            assert {
                r.reservation_id for r in store.list_open_reservations(agent_id=agent, limit=1000)
            } == {r for r, v in res.items() if v["status"] == "open"}, where
    # the sequences really reached every branch (a model that never refuses or settles proves nothing)
    assert counts["granted"] > 800 and counts["refused"] > 300, counts
    assert counts["settled"] > 300 and counts["released"] > 100 and counts["closed_replay"] > 50, (
        counts
    )
    if store.backend == "memory":
        assert counts["expired"] > 100, counts


def test_b12_memory_the_lock_covers_the_cap_check_and_the_write():
    """Memory store only (the hook exists there only). The first thread is held between its cap check and its write
    while a second thread reserves; with the lock the second waits and is refused, so exactly one is granted. Without
    the lock both pass the cap check, every time (no luck of the interpreter lock)."""
    import threading

    from hadavin_sdk.store.memory import MemoryStore

    entered, release = threading.Event(), threading.Event()
    calls = []

    def hook(name):
        calls.append(name)
        if len(calls) == 1:
            entered.set()
            release.wait(5)

    store = MemoryStore(_checkpoint=hook)
    day = utc_today(store)
    results = []

    def go(rid):
        try:
            store.reserve_spend(
                rid,
                "rs-b12",
                day,
                D(1),
                day_cap=D("1.5"),
                month_cap=None,
                run_id=None,
                run_cap=None,
            )
            results.append("ok")
        except SpendCapExceeded:
            results.append("cap")

    first = threading.Thread(target=go, args=("b12-1",), daemon=True)
    first.start()
    assert entered.wait(5)
    second = threading.Thread(target=go, args=("b12-2",), daemon=True)
    second.start()
    second.join(0.3)  # with the lock the second thread is still waiting for it here
    release.set()
    first.join(10)
    second.join(10)
    assert sorted(results) == ["cap", "ok"]
    assert store.spend_totals("rs-b12", day) == (D(1), D(1))
