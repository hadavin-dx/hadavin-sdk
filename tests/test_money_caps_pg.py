"""F-money-definer step 6 (first half), the caps table and its two SECURITY DEFINER functions: `hadavin_caps` (no
right for any login), `hadavin_set_cap` (caps login only, M4) and `hadavin_cap_matches` (runtime and caps, read-only,
answers same / differs / missing). Real PostgreSQL 16, a throwaway schema and real non-superuser logins with unique
names, dropped after. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
from decimal import Decimal

import psycopg
import pytest
from psycopg import errors, sql

from tests.test_stop_state_roles import World

D = Decimal
pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
SET = "hadavin_set_cap(%s, %s, %s, %s)"
MATCH = "hadavin_cap_matches(%s, %s, %s)"
TABLE_PRIVS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")


@pytest.fixture(name="w")
def caps_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        world.migrate()
        yield world
    finally:
        for s in world.stores:
            s._db.close()
        with psycopg.connect(world.dsn, autocommit=True) as db:
            for schema in world.schemas:
                db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _set(w, agent="agent-a", day=None, month=None, by="operator"):
    day = D("5") if day is None else day
    month = D("100") if month is None else month
    with w.as_(w.caps) as db:
        db.execute(f"SELECT {SET}", (agent, day, month, by))


def _match(w, role, agent, day, month):
    with w.as_(role) as db:
        return db.execute(f"SELECT {MATCH}", (agent, day, month)).fetchone()[0]


def _caps(w):
    return w.run("SELECT agent_id, day_cap, month_cap, set_by FROM hadavin_caps ORDER BY 1")


# --- the table: no login has any right ------------------------------------------------------------------------


def test_no_login_holds_any_right_on_the_caps_table(w):
    for role in (w.runtime, w.portal, w.purge, w.reset, w.caps):
        for priv in TABLE_PRIVS:
            assert w.run("SELECT has_table_privilege(%s, 'hadavin_caps', %s)", (role, priv)) == [
                (False,)
            ], (role, priv)
        assert w.run(
            "SELECT count(*) FROM pg_attribute WHERE attrelid = 'hadavin_caps'::regclass AND attnum > 0 "
            "AND has_column_privilege(%s, attrelid, attnum, 'SELECT,INSERT,UPDATE')",
            (role,),
        ) == [(0,)]
    assert w.run("SELECT has_table_privilege('public', 'hadavin_caps', 'SELECT')") == [(False,)]


@pytest.mark.parametrize("which", ["runtime", "reset", "caps"])
def test_the_runtime_the_reset_and_the_caps_login_cannot_touch_the_table_by_sql(w, which):
    _set(w)
    role = getattr(w, which)
    with w.as_(role) as db:
        for stmt in (
            "SELECT * FROM hadavin_caps",
            "INSERT INTO hadavin_caps (agent_id, day_cap, month_cap, set_by) VALUES ('x', 1, 1, 'x')",
            "UPDATE hadavin_caps SET day_cap = 1e30",
            "DELETE FROM hadavin_caps",
            "TRUNCATE hadavin_caps",
        ):
            with pytest.raises(errors.InsufficientPrivilege):
                db.execute(stmt)
    assert _caps(w) == [("agent-a", D("5"), D("100"), "operator")]


# --- who may execute ----------------------------------------------------------------------------------------------


def test_the_runtime_cannot_execute_set_cap_and_changes_nothing(w):
    with w.as_(w.runtime) as db, pytest.raises(errors.InsufficientPrivilege):
        db.execute(f"SELECT {SET}", ("agent-a", D("1"), D("1"), "evil"))
    assert _caps(w) == []


def test_the_reset_login_cannot_execute_set_cap_and_changes_nothing(w):
    """M4: one identity per function. The login that clears a stop no longer sets a cap."""
    with w.as_(w.reset) as db, pytest.raises(errors.InsufficientPrivilege):
        db.execute(f"SELECT {SET}", ("agent-a", D("1"), D("1"), "evil"))
    assert _caps(w) == []


def test_execute_rights_of_every_login_on_the_two_functions(w):
    sets = "hadavin_set_cap(text, numeric, numeric, text)"
    match = "hadavin_cap_matches(text, numeric, numeric)"
    want = {
        (w.runtime, sets): False,
        (w.runtime, match): True,
        (w.reset, sets): False,
        (w.reset, match): False,
        (w.caps, sets): True,
        (w.caps, match): True,
        (w.portal, sets): False,
        (w.portal, match): False,
        (w.purge, sets): False,
        (w.purge, match): False,
        ("public", sets): False,
        ("public", match): False,
    }
    for (role, sig), expected in want.items():
        assert w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (role, sig)) == [
            (expected,)
        ], (role, sig)


def test_the_two_functions_are_definer_pinned_volatile_and_not_strict(w):
    rows = w.run(
        "SELECT p.proname, p.prosecdef, p.provolatile, p.proisstrict, p.proconfig FROM pg_proc p "
        "JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = %s "
        "AND p.proname IN ('hadavin_set_cap', 'hadavin_cap_matches') ORDER BY 1",
        (w.schema,),
    )
    assert [r[0] for r in rows] == ["hadavin_cap_matches", "hadavin_set_cap"]
    for _, definer, volatility, strict, config in rows:
        assert (definer, volatility, strict) == (True, "v", False)
        assert config == [f"search_path=pg_catalog, {w.schema}, pg_temp"]


def test_the_caps_login_sets_a_cap_and_a_second_call_replaces_it(w):
    _set(w, day=D("5"), month=D("100"), by="first")
    _set(w, day=D("7.5"), month=D("120"), by="second")
    assert _caps(w) == [("agent-a", D("7.5"), D("120"), "second")]


# --- cap_matches ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("who", ["runtime", "caps"])
def test_cap_matches_answers_same_differs_and_missing(w, who):
    role = getattr(w, who)
    assert _match(w, role, "agent-a", D("5"), D("100")) == "missing"
    _set(w)
    assert _match(w, role, "agent-a", D("5"), D("100")) == "same"
    assert _match(w, role, "agent-a", D("5.000"), D("100.0")) == "same"
    assert _match(w, role, "agent-a", D("6"), D("100")) == "differs"
    assert _match(w, role, "agent-a", D("5"), D("101")) == "differs"
    assert (
        _match(w, role, "agent-a", D("100"), D("5")) == "differs"
    )  # day and month are not interchangeable
    assert _match(w, role, "agent-b", D("5"), D("100")) == "missing"


def test_cap_matches_changes_nothing_and_gives_the_runtime_no_table_right(w):
    _set(w)
    before = _caps(w)
    _match(w, w.runtime, "agent-a", D("1"), D("1"))
    _match(w, w.runtime, "agent-new", D("1"), D("1"))
    assert _caps(w) == before


# --- hostile arguments --------------------------------------------------------------------------------------------

BAD_CAPS = [
    None,
    D("NaN"),
    D("Infinity"),
    D("-Infinity"),
    D("-1"),
    D("-0.01"),
    D("0.0000000000001"),  # scale 13
]
BAD_IDS = [
    None,
    "",
    "a" * 201,
    "a\nb",
    "a\x01b",
    "a\x7fb",
    "a\x85b",
    "x" * 100000,
]


@pytest.mark.parametrize("bad", BAD_CAPS, ids=lambda v: repr(v)[:30])
@pytest.mark.parametrize("slot", ["day", "month"])
def test_a_bad_cap_is_refused_by_both_functions_and_nothing_is_written(w, bad, slot):
    good = D("10")
    day, month = (bad, good) if slot == "day" else (good, bad)
    with w.as_(w.caps) as db:
        with pytest.raises(errors.InvalidParameterValue, match=f"p_{slot}_cap"):
            db.execute(f"SELECT {SET}", ("agent-a", day, month, "op"))
        with pytest.raises(errors.InvalidParameterValue, match=f"p_{slot}_cap"):
            db.execute(f"SELECT {MATCH}", ("agent-a", day, month))
    assert _caps(w) == []


@pytest.mark.parametrize("bad", BAD_IDS, ids=lambda v: repr(v)[:20])
def test_a_bad_agent_id_is_refused_by_both_functions(w, bad):
    with w.as_(w.caps) as db:
        with pytest.raises(errors.InvalidParameterValue, match="p_agent"):
            db.execute(f"SELECT {SET}", (bad, D("1"), D("1"), "op"))
        with pytest.raises(errors.InvalidParameterValue, match="p_agent"):
            db.execute(f"SELECT {MATCH}", (bad, D("1"), D("1")))
    assert _caps(w) == []


@pytest.mark.parametrize("bad", [None, "", "b" * 201, "a\nb", "a\x1fb", "a\x9fb"], ids=repr)
def test_a_bad_p_by_is_refused(w, bad):
    with w.as_(w.caps) as db, pytest.raises(errors.InvalidParameterValue, match="p_by"):
        db.execute(f"SELECT {SET}", ("agent-a", D("1"), D("1"), bad))
    assert _caps(w) == []


def test_the_refusal_text_never_carries_the_value(w):
    with w.as_(w.caps) as db, pytest.raises(errors.InvalidParameterValue) as exc:
        db.execute(f"SELECT {SET}", ("secret-looking-agent\n", D("1"), D("1"), "op"))
    assert "secret-looking" not in str(exc.value)


def test_a_hostile_looking_agent_id_is_data_not_sql(w):
    agent = "x'); DROP TABLE spend; --"
    _set(w, agent=agent)
    assert _caps(w)[0][0] == agent
    assert w.exists("spend")
    assert _match(w, w.runtime, agent, D("5"), D("100")) == "same"


# --- the cap window is not the amount window --------------------------------------------------------------------


@pytest.mark.parametrize(
    "cap", [D("1E+9"), D("123E+9"), D(10**30), D("5E+12"), D("0"), D("0.000000000001")]
)
def test_the_big_and_small_caps_of_the_contract_are_accepted(w, cap):
    _set(w, day=cap, month=cap)
    assert _caps(w) == [("agent-a", cap, cap, "operator")]
    assert _match(w, w.runtime, "agent-a", cap, cap) == "same"


def test_a_scale_13_cap_is_refused_and_a_scale_12_cap_kept(w):
    _set(w, day=D("1.000000000001"), month=D("2"))
    with w.as_(w.caps) as db, pytest.raises(errors.InvalidParameterValue, match="p_day_cap"):
        db.execute(f"SELECT {SET}", ("agent-a", D("1.0000000000001"), D("2"), "op"))
    assert _caps(w) == [("agent-a", D("1.000000000001"), D("2"), "operator")]


def test_day_above_month_is_allowed(w):
    _set(w, day=D("500"), month=D("5"))
    assert _caps(w) == [("agent-a", D("500"), D("5"), "operator")]


def test_the_table_check_alone_refuses_a_nan_or_negative_cap_even_for_the_owner(w):
    with w.admin() as db:
        for bad in ("NaN", "-1", "Infinity"):
            with pytest.raises(errors.CheckViolation):
                db.execute(
                    "INSERT INTO hadavin_caps (agent_id, day_cap, month_cap, set_by) "
                    "VALUES ('z', %s::numeric, 1, 'o')",
                    (bad,),
                )
