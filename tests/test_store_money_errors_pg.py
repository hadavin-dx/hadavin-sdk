"""Step 3 of F-money-definer: the store calls the money definer functions and maps what they raise. A fresh migrated
schema and the real runtime login (`World` of tests/test_stop_state_roles.py). Checks that psycopg surfaces
`exc.sqlstate` for the HD class (it has no named class), and the mapping of each code to the store's exceptions.

Needs HADAVIN_TEST_PG_DSN (skipped without it)."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg

from hadavin_sdk.config import ConfigError
from hadavin_sdk.models import new_id
from hadavin_sdk.store.protocol import NotFound, SpendCapExceeded, StaleState
from tests.money_caps_seed import seed_caps
from tests.money_days import today_utc
from tests.test_spend_reservations_pg import (  # noqa: F401  (the "w" fixture)
    AGENT,
    DAY,
    reservation_world,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

D = Decimal


def _seed(w, agent, day_cap, month_cap):
    """The function reads the caps from the table: write them as the owner (a raw call has no test hook)."""
    seed_caps(w.scoped, w.schema, agent, D(day_cap), D(month_cap))


def _reserve(store, usd="1.00", *, rid=None, day_cap="100", month_cap="100", agent=AGENT):
    rid = rid or new_id("res")
    store.reserve_spend(rid, agent, DAY, D(usd), day_cap=D(day_cap), month_cap=D(month_cap))
    return rid


def _raw(store, query, params):
    """The function call as the runtime login, without the store's mapping."""
    with store._db.transaction():
        return store._exec(query, params).fetchone()


def test_psycopg_surfaces_the_sqlstate_of_the_hd_class(w):
    rt = w.store(w.runtime)
    args = (new_id("res"), AGENT, today_utc(), D("1.00"), None)
    _seed(w, AGENT, "0", "100")
    with pytest.raises(psycopg.errors.DatabaseError) as caught:
        _raw(rt, rt._reserve_call(), args)
    assert caught.value.sqlstate == "HD001"
    assert caught.value.diag.message_primary == "day"
    _seed(w, AGENT, "100", "0")
    with pytest.raises(psycopg.errors.DatabaseError) as caught:
        _raw(rt, rt._reserve_call(), (new_id("res"), AGENT, today_utc(), D("1.00"), None))
    assert (caught.value.sqlstate, caught.value.diag.message_primary) == ("HD001", "month")
    with pytest.raises(psycopg.errors.DatabaseError) as caught:
        _raw(
            rt,
            rt._money_call("hadavin_settle_spend", "%s::text, %s::numeric, %s::text"),
            ("nope", D(1), AGENT),
        )
    assert caught.value.sqlstate == "HD002"


def test_a_cap_refusal_is_spend_cap_exceeded_with_the_counter(w):
    rt = w.store(w.runtime)
    _reserve(rt, "1.00")
    with pytest.raises(SpendCapExceeded) as day:
        _reserve(rt, "1.00", day_cap="1.50")
    assert day.value.which == "day"
    with pytest.raises(SpendCapExceeded) as month:
        _reserve(rt, "1.00", month_cap="1.50")
    assert month.value.which == "month"
    assert rt.spend_totals(AGENT, DAY) == (D("1.00"), D("1.00"))


def test_a_duplicate_id_is_stale_state_an_unknown_id_is_not_found(w):
    rt = w.store(w.runtime)
    rid = _reserve(rt)
    with pytest.raises(StaleState, match=f"spend reservation exists: {rid}"):
        _reserve(rt, "2.00", rid=rid)
    with pytest.raises(NotFound):
        rt.settle_spend("unknown-id", D("1.00"), agent_id=AGENT)
    with pytest.raises(NotFound):
        rt.settle_spend(rid, D("1.00"), agent_id="another-agent")
    row, applied = rt.settle_spend(rid, D("0.50"), agent_id=AGENT)
    assert applied and row.settled_usd == D("0.50")
    again, applied = rt.settle_spend(rid, D("0.10"), agent_id=AGENT)
    assert not applied and again == row


def test_a_missing_counter_row_is_a_runtime_error_and_the_claim_rolls_back(w):
    rt = w.store(w.runtime)
    rid = _reserve(rt)
    w.do("DELETE FROM spend")
    with pytest.raises(RuntimeError, match="spend counter row missing"):
        rt.settle_spend(rid, D("0.50"), agent_id=AGENT)
    assert w.run("SELECT status FROM spend_reservations")[0][0] == "open"


@pytest.mark.parametrize("limit", ["max_amount", "max_decimals", "max_id_chars"])
def test_a_missing_limit_row_fails_closed_for_every_call(w, limit):
    rt = w.store(w.runtime)
    rid = _reserve(rt)
    w.run("DELETE FROM hadavin_limits WHERE name = %s RETURNING 1", (limit,))
    calls = (
        lambda: _reserve(rt),
        lambda: rt.settle_spend(rid, D("0.50"), agent_id=AGENT),
        lambda: rt.add_spend(AGENT, DAY, D("1.00")),
    )
    for call in calls:
        with pytest.raises(ConfigError, match="HD004"):
            call()
    assert rt.spend_totals(AGENT, DAY) == (D("1.00"), D("1.00"))  # nothing was booked
    assert w.run("SELECT status FROM spend_reservations")[0][0] == "open"


def test_a_missing_expiry_limit_row_fails_closed_for_expire(w):
    rt = w.store(w.runtime)
    w.run("DELETE FROM hadavin_limits WHERE name = 'max_expiry_age' RETURNING 1")
    with pytest.raises(ConfigError, match="HD004"):
        rt.expire_spend_reservations(0)


def test_an_argument_the_python_check_lets_through_is_a_value_error_from_the_function(w):
    rt = w.store(w.runtime)
    with pytest.raises(ValueError, match="agent_id"):
        rt.add_spend("bad\x01agent", date(2024, 1, 31), D("1.00"))  # refused before any SQL
    assert w.count("spend") == 0


def test_an_unmapped_hd_code_is_not_mistaken_for_a_lost_connection(w):
    """psycopg raises an unknown HD code as OperationalError, the class `is_connectivity_error` reads as "store
    unreachable": the store names the whole family and fails closed with a ConfigError."""
    from types import SimpleNamespace

    from hadavin_sdk.store.postgres import _money_error
    from hadavin_sdk.store.protocol import is_connectivity_error

    mapped = _money_error(SimpleNamespace(sqlstate="HD999"))
    assert isinstance(mapped, ConfigError) and "HD999" in str(mapped)
    assert not is_connectivity_error(mapped)
    rt = w.store(w.runtime)
    _seed(w, AGENT, "0", "100")
    with pytest.raises(
        psycopg.OperationalError
    ) as caught:  # the premise: psycopg's class for the family
        _raw(rt, rt._reserve_call(), (new_id("res"), AGENT, today_utc(), D("1"), None))
    assert caught.value.sqlstate == "HD001"
