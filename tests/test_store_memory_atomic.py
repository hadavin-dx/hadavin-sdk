"""The memory store books atomically (fix round 3 of F-store): `reserve_spend` builds the reservation row first and
only then moves the counter, `settle_spend` computes first and then mutates, so an error half way leaves the
counters, the rows and the run cost as they were.

Written by a different agent than the builder, from the claim of the fix. Memory store only, no database. The
counters and the rows are read behind the Protocol (`_spend`, `_reservations`, `_runs`) because the Protocol has no
getter for them; the public `spend_totals` is checked as well.
"""

import random
from datetime import date, datetime
from decimal import Decimal

import pytest

from hadavin_sdk.models import Run, new_id
from hadavin_sdk.store import memory as memory_mod
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import NotFound, SpendCapExceeded

D = Decimal
DAY = date(2026, 3, 14)
OTHER_DAY = date(2026, 3, 15)
AGENT = "agent-atomic"
BIG = D("1000")


def _state(store):
    """Everything a failed call must leave alone."""
    with store._lock:
        return (
            dict(store._spend),
            dict(store._reservations),
            {k: r.cost_usd for k, r in store._runs.items()},
        )


def _reserve(store, rid=None, *, day=DAY, usd="1.00", agent=AGENT, run_id=None, cap=BIG):
    rid = rid or new_id("res")
    store.reserve_spend(rid, agent, day, D(usd), day_cap=cap, month_cap=cap, run_id=run_id)
    return rid


def _run(store):
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run.run_id


class Boom(Exception):
    pass


def _raise(*_a, **_k):
    raise Boom("injected")


# --- F1: reserve builds the row first ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_day",
    [
        datetime(2026, 3, 14, 5, 30),  # noqa: DTZ001 - a time of day: the model refuses it
        datetime(2026, 3, 14, 0, 0, 1),  # noqa: DTZ001
        None,
        5,
        1.5,
        b"2026-03-14",
        object(),
    ],
    ids=["datetime_time", "datetime_second", "none", "int", "float", "bytes", "object"],
)
def test_an_invalid_day_leaves_counters_and_rows_unchanged(bad_day):
    store = MemoryStore()
    keep = _reserve(store, usd="2.00", run_id=_run(store))
    before = _state(store)
    rid = new_id("res")
    with pytest.raises(Exception) as caught:
        _reserve(store, rid, day=bad_day, usd="3.00")
    assert not isinstance(caught.value, (SpendCapExceeded, NotFound))
    assert _state(store) == before
    assert store.spend_totals(AGENT, DAY) == (D("2.00"), D("2.00"))
    assert rid not in store._reservations
    # the same id is free, and the next good booking counts once
    _reserve(store, rid, usd="3.00")
    assert store.spend_totals(AGENT, DAY) == (D("5.00"), D("5.00"))
    assert keep in store._reservations


def test_an_invalid_day_never_creates_a_counter_row_for_a_new_agent():
    store = MemoryStore()
    with pytest.raises(Exception):  # noqa: B017
        _reserve(store, day=datetime(2026, 3, 14, 1), agent="fresh-agent")  # noqa: DTZ001
    assert _state(store) == ({}, {}, {})
    assert store.spend_totals("fresh-agent", DAY) == (D(0), D(0))


def test_a_construction_failure_of_any_kind_leaves_the_counters_alone(monkeypatch):
    """Whatever makes the row fail (here the clock and the model class), the booking has not happened."""
    store = MemoryStore()
    _reserve(store, usd="1.00")
    before = _state(store)
    with monkeypatch.context() as m:
        m.setattr(memory_mod, "now", _raise)
        with pytest.raises(Boom):
            _reserve(store, usd="4.00")
    assert _state(store) == before
    with monkeypatch.context() as m:
        m.setattr(memory_mod, "SpendReservation", _raise)
        with pytest.raises(Boom):
            _reserve(store, usd="4.00")
    assert _state(store) == before
    assert store.spend_totals(AGENT, DAY) == (D("1.00"), D("1.00"))


def test_the_row_is_built_before_the_counter_moves(monkeypatch):
    """The order itself: at the moment the model is called the counter still shows the old amount."""
    store = MemoryStore()
    _reserve(store, usd="1.00")
    seen = []
    real = memory_mod.SpendReservation

    def spy(**kw):
        seen.append(dict(store._spend))
        return real(**kw)

    monkeypatch.setattr(memory_mod, "SpendReservation", spy)
    _reserve(store, usd="2.00")
    assert seen == [{(AGENT, DAY): D("1.00")}]
    assert store._spend[(AGENT, DAY)] == D("3.00")


def test_a_refused_cap_still_builds_no_row_and_books_nothing():
    store = MemoryStore()
    _reserve(store, usd="9.00", cap=D("10"))
    before = _state(store)
    with pytest.raises(SpendCapExceeded):
        _reserve(store, usd="2.00", cap=D("10"))
    assert _state(store) == before


# --- F1: settle computes first ---------------------------------------------------------------------------------


def test_a_settle_that_fails_before_the_row_is_closed_changes_nothing(monkeypatch):
    store = MemoryStore()
    run_id = _run(store)
    rid = _reserve(store, usd="1.00", run_id=run_id)
    before = _state(store)
    with monkeypatch.context() as m:
        m.setattr(memory_mod, "now", _raise)  # read when the closed row is built
        with pytest.raises(Boom):
            store.settle_spend(rid, D("0.40"), agent_id=AGENT)
    assert _state(store) == before
    assert store.get_run(run_id).cost_usd == 0
    assert store.spend_totals(AGENT, DAY) == (D("1.00"), D("1.00"))
    row, applied = store.settle_spend(
        rid, D("0.40"), agent_id=AGENT
    )  # the first settle is still the first
    assert applied and row.settled_usd == D("0.40")
    assert store.get_run(run_id).cost_usd == D("0.40")
    assert store.spend_totals(AGENT, DAY) == (D("0.40"), D("0.40"))


def test_a_settle_that_fails_on_the_run_copy_changes_nothing(monkeypatch):
    store = MemoryStore()
    run_id = _run(store)
    rid = _reserve(store, usd="1.00", run_id=run_id)
    before = _state(store)
    with monkeypatch.context() as m:
        m.setattr(type(store._runs[run_id]), "model_copy", _raise)
        with pytest.raises(Boom):
            store.settle_spend(rid, D("0.40"), agent_id=AGENT)
    assert _state(store) == before


@pytest.mark.parametrize("with_run", [False, True])
@pytest.mark.parametrize("expired", [False, True])
def test_a_settle_with_the_counter_row_missing_raises_and_changes_nothing(with_run, expired):
    store = MemoryStore()
    run_id = _run(store) if with_run else None
    rid = _reserve(store, usd="1.00", run_id=run_id)
    if expired:
        assert store.expire_spend_reservations(0) == 1
    with store._lock:
        store._spend.clear()
    before = _state(store)
    with pytest.raises(RuntimeError, match="spend counter row missing"):
        store.settle_spend(rid, D("2.00"), agent_id=AGENT)
    assert _state(store) == before
    assert before[1][rid].status == ("expired" if expired else "open")
    if with_run:
        assert store.get_run(run_id).cost_usd == 0
    assert (AGENT, DAY) not in store._spend  # no counter row was invented


def test_a_missing_counter_row_of_another_day_does_not_block_a_settle():
    store = MemoryStore()
    rid = _reserve(store, usd="1.00")
    other = _reserve(store, day=OTHER_DAY, usd="1.00")
    with store._lock:
        del store._spend[(AGENT, OTHER_DAY)]
    row, applied = store.settle_spend(rid, D("0.50"), agent_id=AGENT)
    assert applied and row.settled_usd == D("0.50")
    with pytest.raises(RuntimeError, match="spend counter row missing"):
        store.settle_spend(other, D("0.50"), agent_id=AGENT)


@pytest.mark.parametrize("bad", [D("NaN"), D(-1), 1, 1.0, None, D("1E+10")], ids=repr)
def test_a_bad_settle_amount_changes_nothing(bad):
    store = MemoryStore()
    rid = _reserve(store, usd="1.00", run_id=_run(store))
    before = _state(store)
    with pytest.raises(ValueError, match="amount"):
        store.settle_spend(rid, bad, agent_id=AGENT)
    assert _state(store) == before


# --- the stress ------------------------------------------------------------------------------------------------


def _booked(row):
    return row.reserved_usd if row.status == "open" else row.settled_usd


def _assert_counters_are_the_rows(store):
    with store._lock:
        rows, spend = list(store._reservations.values()), dict(store._spend)
    want: dict = {}
    for row in rows:
        want[(row.agent_id, row.day)] = want.get((row.agent_id, row.day), D(0)) + _booked(row)
    assert spend == want


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_200_random_failing_and_succeeding_operations_keep_the_counters_equal_to_the_rows(
    seed, monkeypatch
):
    rnd = random.Random(seed)  # noqa: S311 - a seeded test shuffle
    store = MemoryStore()
    runs = [_run(store) for _ in range(3)]
    agents = ["a-1", "a-2"]
    days = [DAY, OTHER_DAY, date(2026, 4, 2)]
    bad_days = [datetime(2026, 3, 14, 9), None, 3]  # noqa: DTZ001
    outcomes = {"ok": 0, "fail": 0}
    for _ in range(200):
        op = rnd.choice(["reserve", "reserve", "reserve", "settle", "settle", "expire"])
        before = _state(store)
        try:
            if op == "reserve":
                kw = {
                    "day": rnd.choice(days),
                    "usd": f"{rnd.randint(0, 300)}.{rnd.randint(0, 99):02d}",
                    "agent": rnd.choice(agents),
                    "run_id": rnd.choice([None, *runs, "no-such-run"]),
                    "cap": D(rnd.choice(["50", "200", "400"])),
                }
                fault = rnd.choice(["none", "none", "day", "agent", "run", "cap", "clock", "id"])
                if fault == "day":
                    kw["day"] = rnd.choice(bad_days)
                elif fault == "agent":
                    kw["agent"] = rnd.choice(["", "a\x00", 7, "x" * 201])
                elif fault == "run":
                    kw["run_id"] = rnd.choice(["", "r\x00", 7, "\ud800"])
                elif fault == "cap":
                    kw["cap"] = rnd.choice([D("NaN"), D(-1), D("1E+30")])
                elif fault == "id":
                    kw["rid"] = rnd.choice(["bad\x00", 5])
                with monkeypatch.context() as m:
                    if fault == "clock":
                        m.setattr(memory_mod, "now", _raise)
                    _reserve(store, **kw)
            elif op == "settle":
                ids = sorted(store._reservations) or ["res-none"]
                amount = rnd.choice(
                    [D(f"{rnd.randint(0, 400)}.{rnd.randint(0, 99):02d}"), D("NaN"), D(-1)]
                )
                with monkeypatch.context() as m:
                    if rnd.random() < 0.15:
                        m.setattr(memory_mod, "now", _raise)
                    store.settle_spend(rnd.choice(ids), amount, agent_id=AGENT)
            else:
                store.expire_spend_reservations(rnd.choice([0, 0, 10**9 // 100]))
            outcomes["ok"] += 1
        except Exception as exc:  # noqa: BLE001 - any refusal, whatever its class, must leave no trace
            outcomes["fail"] += 1
            if op != "expire":  # a refused reserve or settle changes nothing at all
                assert _state(store) == before, exc
        _assert_counters_are_the_rows(store)
    assert outcomes["ok"] > 20 and outcomes["fail"] > 20
    # the public view agrees with the rows too
    for agent in agents:
        for day in days:
            day_total, month_total = store.spend_totals(agent, day)
            assert day_total == store._spend.get((agent, day), D(0))
            assert month_total == sum(
                (
                    v
                    for (a, d), v in store._spend.items()
                    if a == agent and (d.year, d.month) == (day.year, day.month)
                ),
                D(0),
            )
