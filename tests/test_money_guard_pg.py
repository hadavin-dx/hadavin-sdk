"""E11 M4 (migration 0010_money_guard): a runtime login can raise a booked spend amount but can never LOWER one;
only the body of the SECURITY DEFINER release function can. Real PostgreSQL, a throwaway schema and real
non-superuser logins (the `w` fixture of the release tests), unique names, everything dropped after.

`lowering_attacks(w)` runs every way the runtime login can think of to lower a booked amount and returns the
statements that WENT THROUGH (it must be empty); the mutant tests reuse it."""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors

from tests.test_release_expired_spend_pg import (
    AGENT,
    DAY,
    _counters,
    _expire,
    _release,
    _reserve,
    _status,
    release_world,  # noqa: F401 - the fixture
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

D = Decimal
MONTH = DAY.replace(day=1)


def seed(w):
    """An open 2.00 hold and a settled 1.00 hold (settled at 0.40): returns (open_id, settled_id)."""
    rt = w.store(w.runtime)
    opened = _reserve(rt, "2.00")
    settled = _reserve(rt, "1.00")
    rt.settle_spend(settled, D("0.40"))
    return opened, settled


def trigger_role(w):
    """A login made for the trigger tests: not the owner, not a definer, and holding the table rights the runtime held
    before F-money-definer step 4 (SELECT, INSERT, UPDATE). The missing GRANT no longer decides for it, so the
    trigger of 0010 does (and a trigger mutant is killed through it). Dropped with the world's roles."""
    role = w.new_role("tg")
    w.grant("GRANT USAGE ON SCHEMA {} TO {}", w.schema, role)
    for table in ("spend", "spend_month", "spend_reservations"):
        w.grant(f"GRANT SELECT, INSERT, UPDATE ON {table} TO {{}}", role)
    return role


def lowering_attacks(w, opened, settled, role=None):
    """Statements of `role` (default: the runtime login) that lower a booked amount; returns those that did NOT
    raise. Run as the runtime login, the missing GRANT refuses every one before any trigger runs; run as the
    trigger role, the trigger refuses them."""
    role = role or w.runtime
    by = (AGENT, DAY)
    attacks = {
        "spend": ("UPDATE spend SET usd = usd - 0.5 WHERE agent_id = %s AND day = %s", by),
        "spend_zero": ("UPDATE spend SET usd = 0 WHERE agent_id = %s AND day = %s", by),
        "month": (
            "UPDATE spend_month SET usd = usd - 0.5 WHERE agent_id = %s AND month = %s",
            (AGENT, MONTH),
        ),
        "reserved": (
            "UPDATE spend_reservations SET reserved_usd = 1 WHERE reservation_id = %s",
            (opened,),
        ),
        "settled": (
            "UPDATE spend_reservations SET settled_usd = 0.1 WHERE reservation_id = %s",
            (settled,),
        ),
        "upsert": (
            (
                "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, 0) "
                "ON CONFLICT (agent_id, day) DO UPDATE SET usd = EXCLUDED.usd"
            ),
            by,
        ),
    }
    went_through = []
    with w.as_(role) as db:
        for guc in (
            False,
            True,
        ):  # the second round sets the plain switch first: it must change nothing
            if guc:
                db.execute("SET hadavin.release = on")
            for name, (stmt, params) in attacks.items():
                try:
                    db.execute(stmt, params)
                    went_through.append(f"{name}{'+guc' if guc else ''}")
                except errors.InsufficientPrivilege:
                    pass
        try:
            db.execute("SET ROLE " + w.release)
            went_through.append("set_role")
        except psycopg.Error:
            pass
    return went_through


def test_n1_the_runtime_login_cannot_lower_any_booked_amount(w):
    """Step 4: every attack as the runtime login is refused by the missing GRANT (before any trigger runs)."""
    opened, settled = seed(w)
    before = (_counters(w), _status(w, opened), _status(w, settled))
    assert before[0] == (D("2.40"), D("2.40"))
    assert lowering_attacks(w, opened, settled) == []
    assert (_counters(w), _status(w, opened), _status(w, settled)) == before


def test_n2_the_runtime_login_cannot_raise_a_booked_amount_either(w):
    seed(w)
    with w.as_(w.runtime) as db:
        for stmt in (
            "UPDATE spend SET usd = usd + 1",
            "UPDATE spend_month SET usd = usd + 1",
            "INSERT INTO spend (agent_id, day, usd) VALUES ('other', '2026-01-01', 1)",
        ):
            with pytest.raises(errors.InsufficientPrivilege):
                db.execute(stmt)
    assert _counters(w) == (D("2.40"), D("2.40"))


def test_n3_the_trigger_still_stops_a_login_that_holds_the_table_right(w):
    """The trigger of 0010 is the second wall: a login that did get UPDATE (a hand grant, a later bug) still cannot
    lower a booked amount."""
    opened, settled = seed(w)
    before = (_counters(w), _status(w, opened), _status(w, settled))
    assert lowering_attacks(w, opened, settled, role=trigger_role(w)) == []
    assert (_counters(w), _status(w, opened), _status(w, settled)) == before


def test_n4_the_refusal_is_insufficient_privilege_and_names_the_table(w):
    seed(w)
    with w.as_(w.runtime) as db, pytest.raises(errors.InsufficientPrivilege, match="spend_month"):
        db.execute("UPDATE spend_month SET usd = 0 WHERE agent_id = %s", (AGENT,))
    with (
        w.as_(trigger_role(w)) as db,
        pytest.raises(errors.InsufficientPrivilege, match="spend_month"),
    ):
        db.execute("UPDATE spend_month SET usd = 0 WHERE agent_id = %s", (AGENT,))


def test_the_runtime_login_can_still_raise_and_book_and_settle(w):
    opened, _settled = seed(w)
    rt = w.store(w.runtime)
    with w.as_(trigger_role(w)) as db:
        db.execute("UPDATE spend SET usd = usd + 1 WHERE agent_id = %s", (AGENT,))
        db.execute("UPDATE spend SET usd = usd WHERE agent_id = %s", (AGENT,))  # equal is not lower
    assert _counters(w)[0] == D("3.40")
    row, first = rt.settle_spend(opened, D("5.00"))  # NULL -> amount, and above the reserved amount
    assert first is True and row.settled_usd == D("5.00")
    _expire(w, _reserve(rt, "1.00"))  # open -> expired: settled_usd NULL -> reserved


def test_a_late_settle_of_an_expired_hold_still_works_through_the_guard(w):
    rt = w.store(w.runtime)
    rid = _reserve(rt, "1.00")
    _expire(w, rid)
    row, first = rt.settle_spend(
        rid, D("0.10")
    )  # delta 0: the booking stays at the reserved amount
    assert first is True and row.settled_usd == D("1.00")
    assert _counters(w) == (D("1.00"), D("1.00"))


def test_the_release_function_still_lowers_through_the_guard(w):
    rt = w.store(w.runtime)
    a = _reserve(rt, "1.00")
    _expire(w, a)
    done = _release(w)
    assert (done.reservations, done.released_usd) == (1, D("1.00"))
    assert _counters(w) == (D("0.00"), D("0.00")) and _status(w, a) == ("settled", 0)


def test_the_guard_is_on_all_three_tables_and_its_search_path_is_pinned(w):
    rows = w.run(
        "SELECT c.relname, t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
        "WHERE t.tgfoid = to_regprocedure('hadavin_money_guard()') AND NOT t.tgisinternal"
    )
    assert sorted(rows) == [("spend", "O"), ("spend_month", "O"), ("spend_reservations", "O")]
    cfg = w.run(
        "SELECT proconfig, prosecdef FROM pg_proc WHERE oid = to_regprocedure('hadavin_money_guard()')"
    )[0]
    assert cfg[1] is False  # SECURITY INVOKER
    (entry,) = [c for c in cfg[0] if c.startswith("search_path=")]
    parts = [p.strip().strip('"') for p in entry.split("=", 1)[1].split(",")]
    assert parts[0] == "pg_catalog" and parts[-1] == "pg_temp" and w.schema in parts


def test_the_runtime_login_cannot_switch_the_guard_off(w):
    seed(w)
    with w.as_(w.runtime) as db:
        for stmt in (
            "ALTER TABLE spend DISABLE TRIGGER spend_money_guard",
            "DROP TRIGGER spend_money_guard ON spend",
            (
                "CREATE OR REPLACE FUNCTION hadavin_money_guard() RETURNS trigger LANGUAGE plpgsql "
                "AS $$ BEGIN RETURN NEW; END $$"
            ),
            "SET session_replication_role = replica",
        ):
            with pytest.raises((errors.InsufficientPrivilege, errors.InvalidSchemaName)):
                db.execute(stmt)


def test_a_settle_in_the_same_transaction_does_not_open_the_counter_further(w):
    """Settling an open 2.00 hold at 0.50 lowers the counters by 1.50, and by nothing more, however the runtime
    login words its own UPDATE after it."""
    rt = w.store(w.runtime)
    rid = _reserve(rt, "2.00")
    with w.as_(trigger_role(w), autocommit=False) as db:
        db.execute(
            "UPDATE spend_reservations SET status = 'settled', settled_usd = 0.50, closed_at = clock_timestamp() "
            "WHERE reservation_id = %s",
            (rid,),
        )
        db.execute(
            "UPDATE spend SET usd = usd - 1.50 WHERE agent_id = %s", (AGENT,)
        )  # exactly the fall
        with pytest.raises(errors.InsufficientPrivilege):
            db.execute("UPDATE spend SET usd = usd - 0.10 WHERE agent_id = %s", (AGENT,))
        db.rollback()
    assert _counters(w) == (D("2.00"), D("2.00"))
