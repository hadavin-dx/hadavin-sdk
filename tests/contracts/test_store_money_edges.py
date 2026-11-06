"""P4d-a2-i: the edge table of `add_spend` / `add_cost` (old rules: 8 decimals) on every store kind, the counter
ceiling one counter at a time, and the shared validators. The validators are imported inside the tests so that a
base without them fails each row on its own (an ImportError per row) and not at collection."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import Run
from tests.contracts.store_support import utc_today

D = Decimal
CEILING = 10**15
STEP = D("0.000001")


class _DecSub(Decimal):
    pass


def _run(store):
    run = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


def _scale(zeros_after_point: int, last: str) -> Decimal:
    return D("1." + "0" * zeros_after_point + last)


ACCEPT = [
    D(0),
    D("1E-6"),
    D("1.0000000"),
    D("0.00108225"),  # 8 decimals: accepted by the old methods
    D("0E-1000"),
    D("0E+5"),
    D("1E+12"),  # equal to MAX_USD
    D("1." + "0" * 27),
    D("1." + "0" * 39),
    D("1." + "0" * 999),
]
REFUSE = [
    D("-0"),
    D("-1"),
    D("NaN"),
    D("sNaN"),
    D("Infinity"),
    D("-Infinity"),
    D("1E-9"),
    D("0.123456789"),  # 9 decimals
    D("1E+13"),
    D("1E+200000"),
    _scale(27, "1"),  # 28 decimals, 29 significant digits
    _scale(39, "1"),
    _scale(999, "1"),
    True,
    1,
    0.1,
    "1",
    None,
    _DecSub("1"),
]


@pytest.mark.parametrize("usd", ACCEPT, ids=lambda v: repr(v)[:30])
def test_amounts_the_old_methods_accept(store, usd):
    agent = "edge-" + str(abs(hash(repr(usd))))
    today = utc_today(store)
    store.add_spend(agent, today, usd)
    store.add_cost(_run(store).run_id, usd)


@pytest.mark.parametrize("usd", REFUSE, ids=lambda v: repr(v)[:30])
def test_amounts_the_old_methods_refuse_and_book_nothing(store, usd):
    agent = "edge-r-" + str(abs(hash(repr(usd))))
    today = utc_today(store)
    run = _run(store)
    with pytest.raises(ValueError):
        store.add_spend(agent, today, usd)
    with pytest.raises(ValueError):
        store.add_cost(run.run_id, usd)
    assert store.spend_totals(agent, today) == (0, 0)
    assert store.get_run(run.run_id).cost_usd == 0


def test_add_spend_refuses_a_datetime_and_a_day_out_of_range(store):
    from datetime import datetime

    for bad in (
        datetime(2026, 1, 1, 0, 0),  # noqa: DTZ001 - a naive datetime is the bad value
        date(1999, 12, 31),
        date(2101, 1, 1),
        "2026-01-01",
        None,
    ):
        with pytest.raises(ValueError):
            store.add_spend("edge-day", bad, D(1))
    store.add_spend("edge-day", date(2000, 1, 1), D(1))


def test_add_cost_unknown_run_is_not_found_for_a_good_amount(store):
    from hadavin_sdk.store.protocol import NotFound

    with pytest.raises(NotFound):
        store.add_cost("run-missing", D(1))


def _plant(store, what, agent, day, run_id, value):
    """Put a counter at `value`, through the owner login on Postgres and the private dicts on memory."""
    if store.backend == "postgres":
        from tests.contracts.kinds.store_postgres import pg_driver

        drv = pg_driver()
        with drv.connect_admin(store.runtime_dsn) as conn:
            if what == "day":
                drv.execute(
                    conn,
                    "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s)",
                    (agent, day, value),
                )
            elif what == "month":
                drv.execute(
                    conn,
                    "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s)",
                    (agent, day.replace(day=1), value),
                )
            else:
                drv.execute(
                    conn, "UPDATE runs SET cost_usd = %s WHERE run_id = %s", (value, run_id)
                )
        return
    inner = store._inner
    if what == "run":
        inner._runs[run_id] = inner._runs[run_id].model_copy(update={"cost_usd": value})
    elif what == "month":
        other = day - timedelta(days=1) if day.day > 1 else day + timedelta(days=1)
        inner._spend[(agent, other)] = value
    else:  # memory: the day also plants the month ("combined day-and-month row")
        inner._spend[(agent, day)] = value


@pytest.mark.parametrize("what", ["day", "month", "run"])
def test_a_counter_lands_on_the_ceiling_and_one_more_micro_dollar_is_refused(store, what):
    agent = f"ceil-{what}"
    today = utc_today(store)
    run = _run(store)
    _plant(store, what, agent, today, run.run_id, CEILING - STEP)
    book = (
        (lambda x: store.add_cost(run.run_id, x))
        if what == "run"
        else (lambda x: store.add_spend(agent, today, x))
    )
    with pytest.raises(ValueError):
        book(2 * STEP)
    # nothing changed in ANY counter: the refused booking left the planted value
    if what == "run":
        assert store.get_run(run.run_id).cost_usd == CEILING - STEP
    else:
        day_total, month_total = store.spend_totals(agent, today)
        assert max(day_total, month_total) <= CEILING - STEP
    book(STEP)  # lands exactly on the ceiling
    if what == "run":
        assert store.get_run(run.run_id).cost_usd == CEILING
    with pytest.raises(ValueError):
        book(STEP)


def test_a_refused_ceiling_booking_does_not_move_the_other_counter(store):
    """add_spend: the month is at the ceiling (planted on another day), the day is small: refused, day stays 0."""
    if store.backend == "memory":
        today = utc_today(store)
    else:
        today = utc_today(store)
    agent = "ceil-other"
    run = _run(store)
    _plant(store, "month", agent, today, run.run_id, CEILING)
    with pytest.raises(ValueError):
        store.add_spend(agent, today, STEP)
    assert store.spend_totals(agent, today)[0] == 0


def test_validators_directly():
    from hadavin_sdk.store.protocol import check_cap, check_day, check_int, check_usd

    assert check_usd(D("0.1"), max_decimals=6) == D("0.1")
    with pytest.raises(ValueError):
        check_usd(D(0), positive=True)  # N13: positive means zero is refused
    assert check_usd(D(0)) == 0
    with pytest.raises(ValueError):
        check_usd(D("0.0000001"), max_decimals=6)
    check_usd(D("0.0000010"), max_decimals=6)  # trailing zeros are not decimals
    assert check_cap(None) is None
    assert check_cap(D(0)) == 0
    check_cap(D("0.0000001"))  # 7 decimals
    check_cap(D("0.00000001"))  # 8 decimals
    for bad in (D("NaN"), D(-1), D("0.000000001")):
        with pytest.raises(ValueError):
            check_cap(bad)
    assert check_day(date(2026, 11, 6)) == date(2026, 11, 6)
    with pytest.raises(ValueError):
        check_day(date(2101, 1, 1))
    assert check_int(5, 1, 5) == 5
    for bad in (0, 6, True, "5", 5.0):
        with pytest.raises(ValueError):
            check_int(bad, 1, 5)
