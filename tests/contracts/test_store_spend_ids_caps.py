"""Spend ids, caps, ages and the purge bound are validated by every store kind alike (fix round 3 of F-store).

Written by a different agent than the builder of the checks. Every case runs through the `store` fixture, so the
memory store and PostgreSQL must give the same outcome class for the same hostile input; the checks run before any
lock or SQL, so a refusal books nothing and leaves its reservation id free. A message names the field, never the
value.
"""

import os
from datetime import UTC, date, datetime, timedelta, tzinfo
from decimal import Decimal

import pytest

from hadavin_sdk.limits import Limits, SpendRefused
from hadavin_sdk.models import new_id
from hadavin_sdk.store.protocol import MAX_EXPIRY_AGE_S, NotFound
from tests.contracts.test_store_spend import _closed_earlier, _is_memory, _rows
from tests.test_limits_reserve import Sink, _registry

D = Decimal
DAY = date(2026, 3, 14)
AGENT = "agent-ids"
ONE = D("1.00")
CAP = D("10.00")
ZERO = (D(0), D(0))


class _NoOffset(tzinfo):
    """A tzinfo that knows no offset: the datetime is aware by `tzinfo` and naive by `utcoffset()`."""

    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

    def tzname(self, dt):
        return None


class _Text(str):
    """A str subclass: the rule is exactly a str."""


BAD_IDS = {
    "nul": "a\x00b",
    "nul_only": "\x00",
    "lone_surrogate": "ab\ud800cd",
    "low_surrogate": "\udfff",
    "too_long_201": "x" * 201,
    "too_long_multibyte": "é" * 201,
    "empty": "",
    "newline": "a\nb",
    "tab": "a\tb",
    "del": "a\x7fb",
    "c1_control": "a\x85b",
    "bool": True,
    "int": 7,
    "float": 1.5,
    "none": None,
    "bytes": b"agent",
    "list": ["agent"],
    "str_subclass": _Text("zq-value-zq"),
}
GOOD_IDS = {
    "one_char": "a",
    "exactly_200": "x" * 200,
    "multibyte_200": "é" * 200,
    "punctuation": "agent:one/two.3 four",
}


def _reserve(
    store, rid=None, *, day=DAY, agent=AGENT, usd=ONE, day_cap=CAP, month_cap=CAP, run_id=None
):
    rid = rid or new_id("res")
    store.reserve_spend(rid, agent, day, usd, day_cap=day_cap, month_cap=month_cap, run_id=run_id)
    return rid


def _assert_clean(store, rid):
    """Nothing was booked, no row exists, and the id is still free."""
    assert store.spend_totals(AGENT, DAY) == ZERO
    assert rid not in _rows(store)
    _reserve(store, rid)
    assert store.spend_totals(AGENT, DAY) == (ONE, ONE)


# --- F2: the ids ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("bad", list(BAD_IDS.values()), ids=list(BAD_IDS))
def test_a_bad_agent_id_is_a_value_error_naming_the_field_and_books_nothing(store, bad):
    rid = new_id("res")
    with pytest.raises(ValueError, match="agent_id") as caught:
        _reserve(store, rid, agent=bad)
    assert "run_id" not in str(caught.value)
    if isinstance(bad, str) and len(bad) > 3:
        assert bad not in str(caught.value)
    _assert_clean(store, rid)


@pytest.mark.parametrize("bad", list(BAD_IDS.values()), ids=list(BAD_IDS))
def test_a_bad_run_id_is_a_value_error_naming_the_field_and_books_nothing(store, bad):
    if bad is None:
        pytest.skip("None is the way to say no run")
    rid = new_id("res")
    with pytest.raises(ValueError, match="run_id") as caught:
        _reserve(store, rid, run_id=bad)
    assert "agent_id" not in str(caught.value)
    if isinstance(bad, str) and len(bad) > 3:
        assert bad not in str(caught.value)
    _assert_clean(store, rid)


@pytest.mark.parametrize("good", list(GOOD_IDS.values()), ids=list(GOOD_IDS))
def test_the_edges_of_a_valid_id_are_accepted(store, good):
    rid = _reserve(store, agent=good, run_id=good)
    assert _rows(store)[rid].agent_id == good
    assert store.spend_totals(good, DAY) == (ONE, ONE)


def test_run_id_none_is_accepted_and_stored_as_no_run(store):
    rid = _reserve(store, run_id=None)
    assert _rows(store)[rid].run_id is None


def test_the_agent_id_is_checked_before_the_run_id_and_both_before_everything_else(store):
    with pytest.raises(ValueError, match="agent_id"):
        _reserve(
            store, "bad id \x00", agent="a\x00", run_id="b\x00", usd=D("NaN"), day_cap=D("NaN")
        )
    with pytest.raises(ValueError, match="run_id"):
        _reserve(store, "bad id \x00", run_id="b\x00", usd=D("NaN"), day_cap=D("NaN"))
    assert store.spend_totals(AGENT, DAY) == ZERO


@pytest.mark.parametrize("which", ["agent", "run"])
def test_a_bad_id_does_not_disturb_a_stored_reservation_or_its_counters(store, which):
    kept = _reserve(store, run_id="run-keep")
    before = _rows(store)
    kw = {"agent": "a\x00"} if which == "agent" else {"run_id": "r\x00"}
    with pytest.raises(ValueError):
        _reserve(store, kept, **kw)  # even with the id of an existing row
    assert _rows(store) == before
    assert store.spend_totals(AGENT, DAY) == (ONE, ONE)


@pytest.mark.parametrize("bad", [[], {}, ["a"], {"a": 1}], ids=["list", "dict", "list1", "dict1"])
def test_limits_reserve_turns_an_unhashable_agent_id_into_a_key_error(store, bad):
    limits = Limits(store, Sink(), _registry(daily="5.00", monthly="50.00", agents=(AGENT,)))
    with pytest.raises(KeyError):
        limits.reserve(bad, ONE)
    assert store.spend_totals(AGENT, DAY) == ZERO
    assert _rows(store) == {}


@pytest.mark.parametrize("bad", [None, 1, 1.5, True, "other-agent", b"x"], ids=repr)
def test_limits_reserve_keeps_the_key_error_of_an_unknown_hashable_agent(store, bad):
    limits = Limits(store, Sink(), _registry(daily="5.00", monthly="50.00", agents=(AGENT,)))
    with pytest.raises(KeyError):
        limits.reserve(bad, ONE)
    assert _rows(store) == {}


@pytest.mark.parametrize(
    "hostile", ["a\x00b", "x" * 201, "\ud800"], ids=["nul", "201", "surrogate"]
)
def test_a_registered_agent_with_a_hostile_id_is_limits_unavailable_and_books_nothing(
    store, hostile
):
    limits = Limits(store, Sink(), _registry(daily="5.00", monthly="50.00", agents=(hostile,)))
    with pytest.raises(SpendRefused) as caught:
        limits.reserve(hostile, ONE)
    assert caught.value.reason == "limits_unavailable"
    assert _rows(store) == {}


@pytest.mark.parametrize(
    "hostile", ["r\x00", "", "r" * 201, "\ud800"], ids=["nul", "empty", "201", "sur"]
)
def test_limits_reserve_with_a_hostile_run_id_is_limits_unavailable(store, hostile):
    limits = Limits(store, Sink(), _registry(daily="5.00", monthly="50.00", agents=(AGENT,)))
    with pytest.raises(SpendRefused) as caught:
        limits.reserve(AGENT, ONE, run_id=hostile)
    assert caught.value.reason == "limits_unavailable"
    assert _rows(store) == {}


# --- F3: the caps --------------------------------------------------------------------------------------------

BAD_CAPS = {
    "1E+30": D("1E+30"),
    "1E+999999": D("1E+999999"),
    "1E+10": D("1E+10"),
    "5E+12": D("5E+12"),
    "13_decimals": D("0.0000000000001"),
    "1E-13": D("1E-13"),
    "1_000_000_000_000_001e-13": D("100.0000000000001"),
    "nan": D("NaN"),
    "inf": D("Infinity"),
    "minus_one": D("-1"),
    "minus_zero_exponent": D("-0E-13"),
}
GOOD_CAPS = {
    "1E+9": D("1E+9"),
    "exponent_9_wide": D("123E+9"),
    "twelve_decimals": D("1.000000000000"),
    "plain_large": D("1000000000000000000000000000000"),  # exponent 0: no other upper bound
    "ten": D("10"),
}


@pytest.mark.parametrize("which", ["day_cap", "month_cap"])
@pytest.mark.parametrize("bad", list(BAD_CAPS.values()), ids=list(BAD_CAPS))
def test_an_out_of_window_cap_is_a_value_error_and_books_nothing(store, which, bad):
    rid = new_id("res")
    with pytest.raises(ValueError, match="cap"):
        _reserve(store, rid, **{which: bad})
    _assert_clean(store, rid)


@pytest.mark.parametrize("which", ["day_cap", "month_cap"])
@pytest.mark.parametrize("good", list(GOOD_CAPS.values()), ids=list(GOOD_CAPS))
def test_a_cap_inside_the_window_books(store, which, good):
    rid = _reserve(store, **{which: good})
    assert _rows(store)[rid].status == "open"
    assert store.spend_totals(AGENT, DAY) == (ONE, ONE)


def test_a_cap_with_an_exponent_outside_the_window_is_refused_even_for_a_zero_amount(store):
    with pytest.raises(ValueError, match="cap"):
        _reserve(store, usd=D(0), day_cap=D("1E+30"))
    with pytest.raises(ValueError, match="cap"):
        _reserve(store, usd=D(0), month_cap=D("1E+999999"))
    assert store.spend_totals(AGENT, DAY) == ZERO


# --- F3: the expiry age and the purge bound ------------------------------------------------------------------

BAD_AGES = {
    "10**30": 10**30,
    "limit_plus_one": MAX_EXPIRY_AGE_S + 1,
    "true": True,
    "false": False,
    "float": 1.5,
    "float_whole": 5.0,
    "minus_one": -1,
    "none": None,
    "str": "5",
}


def test_the_age_limit_is_ten_to_the_seventh():
    assert MAX_EXPIRY_AGE_S == 10**7


@pytest.mark.parametrize("bad", list(BAD_AGES.values()), ids=list(BAD_AGES))
def test_a_bad_expiry_age_is_a_value_error_and_expires_nothing(store, bad):
    rid = _reserve(store)
    with pytest.raises(ValueError, match="older_than_s"):
        store.expire_spend_reservations(bad)
    assert _rows(store)[rid].status == "open"
    assert store.spend_totals(AGENT, DAY) == (ONE, ONE)


@pytest.mark.parametrize("edge", [0, 1, MAX_EXPIRY_AGE_S], ids=["zero", "one", "limit"])
def test_the_edges_of_the_expiry_age_are_accepted(store, edge):
    rid = _reserve(store)
    done = store.expire_spend_reservations(edge)
    assert done == (1 if edge == 0 else 0)  # a row that is not old enough stays open
    assert _rows(store)[rid].status == ("expired" if edge == 0 else "open")


def _closed_row(store):
    rid = _reserve(store)
    store.settle_spend(rid, D("0.50"), agent_id=AGENT)
    _closed_earlier(store, rid, 400)
    return rid


@pytest.mark.parametrize(
    "bad",
    [
        datetime(2030, 1, 1),  # noqa: DTZ001 - naive on purpose
        datetime(2030, 1, 1, tzinfo=_NoOffset()),
        date(2030, 1, 1),
        "2030-01-01T00:00:00+00:00",
        None,
        1.7e9,
        1_700_000_000,
    ],
    ids=["naive", "no_offset", "date", "str", "none", "float", "int"],
)
def test_a_purge_bound_that_is_not_an_aware_datetime_is_a_value_error_and_deletes_nothing(
    store, bad
):
    rid = _closed_row(store)
    with pytest.raises(ValueError, match="purge bound"):
        store.purge_spend_reservations(bad)
    assert rid in _rows(store)


def test_an_aware_purge_bound_deletes_the_closed_rows_before_it(store):
    closed = _closed_row(store)
    open_row = _reserve(store)
    bound = datetime.now(UTC) - timedelta(days=1)
    assert store.purge_spend_reservations(bound) == 1
    assert set(_rows(store)) == {open_row}
    assert closed not in _rows(store)


def test_an_aware_purge_bound_in_another_zone_is_accepted(store):
    from datetime import timezone

    _closed_row(store)
    zone = timezone(timedelta(hours=-11))
    assert store.purge_spend_reservations(datetime.now(zone) - timedelta(days=1)) == 1


# --- F4: a missing counter row -------------------------------------------------------------------------------


def _drop_day_counters(store):
    """Delete the day counter rows behind the Protocol, as a crash or an operator could."""
    if _is_memory(store):
        with store._lock:
            store._spend.clear()
        return
    import psycopg
    from psycopg.conninfo import make_conninfo

    schema = store._main._db.execute("SHOW search_path").fetchone()[0].strip('"')
    dsn = make_conninfo(os.environ["HADAVIN_TEST_PG_DSN"], options=f"-c search_path={schema}")
    with psycopg.connect(dsn, autocommit=True) as admin:
        admin.execute("DELETE FROM spend")


@pytest.mark.parametrize("with_run", [False, True])
def test_settle_with_the_counter_row_missing_is_a_runtime_error_and_changes_nothing(
    store, with_run
):
    run_id = (
        "run-without-a-row" if with_run else None
    )  # a run id with no run row moves only the counters
    rid = _reserve(store, run_id=run_id)
    before = _rows(store)[rid]
    _drop_day_counters(store)
    with pytest.raises(RuntimeError, match="spend counter row missing"):
        store.settle_spend(rid, D("0.40"), agent_id=AGENT)
    assert _rows(store)[rid] == before
    assert before.status == "open"
    # and again: the refusal is repeatable, the row never became settled
    with pytest.raises(RuntimeError, match="spend counter row missing"):
        store.settle_spend(rid, D("0.40"), agent_id=AGENT)
    assert _rows(store)[rid] == before


def test_settle_of_an_expired_row_with_the_counter_row_missing_is_also_refused(store):
    rid = _reserve(store)
    assert store.expire_spend_reservations(0) == 1
    before = _rows(store)[rid]
    _drop_day_counters(store)
    with pytest.raises(RuntimeError, match="spend counter row missing"):
        store.settle_spend(
            rid, D("5.00"), agent_id=AGENT
        )  # a rise, so the counter would have to move
    assert _rows(store)[rid] == before


def test_settle_of_an_unknown_id_is_still_not_found(store):
    with pytest.raises(NotFound):
        store.settle_spend(new_id("res"), D("1"), agent_id=AGENT)


# --- the day: a value the row model coerces must not be booked under another key -----------------------------


@pytest.mark.parametrize(
    "coerced",
    [datetime(2026, 3, 14), "2026-03-14"],  # noqa: DTZ001 - a midnight datetime and an ISO string
    ids=["midnight", "iso"],
)
def test_a_day_that_is_not_a_date_is_refused_or_booked_on_the_counter_of_its_date(store, coerced):
    """Refusing it is fine; accepting it is fine only if the counter, the row and the settle agree on the day."""
    rid = new_id("res")
    try:
        _reserve(store, rid, day=coerced)
    except Exception:  # noqa: BLE001 - any refusal class, as long as nothing was left behind
        assert rid not in _rows(store)
        assert store.spend_totals(AGENT, DAY) == ZERO
        return
    assert _rows(store)[rid].day == DAY
    assert store.spend_totals(AGENT, DAY) == (ONE, ONE), "booked under another key"
    row, applied = store.settle_spend(rid, D("0.25"), agent_id=AGENT)
    assert applied and row.settled_usd == D("0.25")
    assert store.spend_totals(AGENT, DAY) == (D("0.25"), D("0.25"))
