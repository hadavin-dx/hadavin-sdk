"""F-money-definer step 2, builder B: what `migrate` does for the five SECURITY DEFINER money functions of 0011:
the search-path pin on every run, EXECUTE per role (and the refusal when another role can still run one), the
one-owner check (functions, then the money tables), the `hadavin_limits` rows written from the Python constants on
every run, and the grant-map completeness checks. Real PostgreSQL, a throwaway schema and real non-superuser
logins with unique names, everything dropped after. Needs HADAVIN_TEST_PG_DSN; the map tests run without it."""

from __future__ import annotations

import os
import re
from decimal import Decimal
from pathlib import Path

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql

from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    MAX_SPEND_DECIMALS,
    MAX_SPEND_EXPONENT,
    MAX_SPEND_USD,
    check_spend_amount,
)
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.protocol import (
    MAX_EXPIRY_AGE_S,
    MAX_RESERVATION_ID_CHARS,
    check_expiry_age,
    check_reservation_id,
    check_spend_cap,
)
from tests.test_stop_state_roles import World

D = Decimal
NEEDS_PG = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
MF = getattr(mig, "MONEY_FUNCTIONS", ("",) * 7)
RESERVE, SETTLE, EXPIRE, PURGE, ADD, SET_CAP, CAP_MATCHES = MF
LIMIT_NAMES = (
    "max_amount",
    "max_decimals",
    "max_id_chars",
    "max_expiry_age",
    "min_expiry_age",
    "max_day_skew",
)


# --- the maps (no database) ---------------------------------------------------------------------------------


def test_the_shared_function_list_is_exactly_the_seven_new_functions():
    assert mig.MONEY_FUNCTIONS == (
        "hadavin_reserve_spend(text, text, date, numeric, text)",
        "hadavin_settle_spend(text, numeric, text)",
        "hadavin_expire_spend_reservations(integer)",
        "hadavin_purge_spend_reservations(timestamptz)",
        "hadavin_add_spend(text, date, numeric)",
        "hadavin_set_cap(text, numeric, numeric, text)",
        "hadavin_cap_matches(text, numeric, numeric)",
    )


def test_function_grants_name_the_roles_the_ticket_names():
    who = {sig: g for sig, g in mig.FUNCTION_GRANTS.items()}
    runtime_only = (
        "hadavin_reserve_spend",
        "hadavin_settle_spend",
        "hadavin_expire_spend_reservations",
        "hadavin_add_spend",
        "hadavin_cap_matches",
        "hadavin_audit_outbox_done",  # 0012: the runtime drains its own outbox
        "hadavin_audit_outbox_quarantine",
    )
    for sig, g in who.items():
        name = sig.split("(")[0]
        assert (g.runtime, g.purge, g.release, g.reset, g.portal, g.caps) == (
            name in runtime_only,
            name == "hadavin_purge_spend_reservations",
            name == "hadavin_release_expired_spend",
            False,  # M4: the reset role runs none of the money functions
            False,
            name in ("hadavin_set_cap", "hadavin_cap_matches"),
        ), sig
    assert mig.FUNCTION_GRANTS[SET_CAP].runtime is False
    assert mig.FUNCTION_GRANTS[CAP_MATCHES].runtime is True
    assert set(who) == {*mig.MONEY_FUNCTIONS, mig.RELEASE_FUNCTION, *mig.AUDIT_FUNCTIONS}


def test_the_trigger_functions_are_the_excluded_set_and_not_in_the_map():
    assert set(mig.EXCLUDED_FUNCTIONS) >= set(mig.TRIPWIRE_FUNCTIONS)
    assert not set(mig.EXCLUDED_FUNCTIONS) & set(mig.FUNCTION_GRANTS)


def test_the_limits_relation_is_owner_only_in_the_grant_map():
    g = mig.GRANTS["hadavin_limits"]
    assert (g.kind, g.runtime, g.portal, g.purge, g.reset, g.release, g.purge_cols) == (
        "table",
        "",
        False,
        "",
        "",
        "",
        (),
    )


def test_the_caps_relation_is_owner_only_in_the_grant_map():
    g = mig.GRANTS["hadavin_caps"]
    assert (g.kind, g.runtime, g.portal, g.purge, g.reset, g.release, g.purge_cols) == (
        "table",
        "",
        False,
        "",
        "",
        "",
        (),
    )


def _plant(tmp_path: Path, body: str) -> list[Path]:
    (tmp_path / "0001_a.sql").write_text(body, encoding="utf-8")
    return [tmp_path / "0001_a.sql"]


def test_plant_a_function_missing_from_the_maps_is_caught(tmp_path):
    files = _plant(
        tmp_path,
        "CREATE OR REPLACE FUNCTION hadavin_new_thing(p text) RETURNS void LANGUAGE sql AS $$ SELECT 1 $$;",
    )
    assert any("hadavin_new_thing" in p and "FUNCTION_GRANTS" in p for p in mig.check_grants(files))


def test_a_function_named_only_in_a_comment_is_not_created(tmp_path):
    files = _plant(tmp_path, "-- CREATE FUNCTION hadavin_ghost() ...\nSELECT 1;")
    assert not any("hadavin_ghost" in p for p in mig.check_grants(files))


def test_a_mapped_and_an_excluded_function_are_not_flagged(tmp_path):
    files = _plant(
        tmp_path,
        "CREATE OR REPLACE FUNCTION hadavin_add_spend(a text, d date, u numeric) RETURNS void "
        "LANGUAGE sql AS $$ SELECT 1 $$;\n"
        "CREATE OR REPLACE FUNCTION hadavin_money_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;",
    )
    assert not any("(function) is created" in p for p in mig.check_grants(files))


def test_a_mapped_function_that_no_migration_creates_is_caught(tmp_path):
    files = _plant(tmp_path, "SELECT 1;")
    assert any(
        "hadavin_add_spend" in p and "no migration creates" in p for p in mig.check_grants(files)
    )


def test_the_real_migrations_leave_no_function_unmapped():
    problems = mig.check_grants(mig._migration_files())
    assert not [p for p in problems if "FUNCTION" in p or "function" in p], problems


def test_the_limits_come_from_the_python_constants_and_nothing_else():
    assert mig.money_limits() == {
        "max_amount": MAX_SPEND_USD,
        "max_decimals": MAX_SPEND_DECIMALS,
        "max_id_chars": MAX_RESERVATION_ID_CHARS,
        "max_expiry_age": MAX_EXPIRY_AGE_S,
        "max_day_skew": defaults.MAX_RESERVE_DAY_SKEW_DAYS,
        "min_expiry_age": defaults.MIN_EXPIRY_AGE_S,
    }
    assert tuple(mig.money_limits()) == LIMIT_NAMES


def test_the_python_validators_agree_with_the_constants_at_the_edge():
    top = D(MAX_SPEND_USD)
    for ok in (top - D("0.000000000001"), D(0)):
        check_spend_amount(ok)
    with pytest.raises(ValueError):
        check_spend_amount(top)
    check_spend_amount(D("0." + "1" * MAX_SPEND_DECIMALS))
    with pytest.raises(ValueError):
        check_spend_amount(D("0." + "1" * (MAX_SPEND_DECIMALS + 1)))
    check_spend_cap(D(1).scaleb(MAX_SPEND_EXPONENT))
    with pytest.raises(ValueError):
        check_spend_cap(D(1).scaleb(MAX_SPEND_EXPONENT + 1))
    check_reservation_id("a" * MAX_RESERVATION_ID_CHARS)
    with pytest.raises(ValueError):
        check_reservation_id("a" * (MAX_RESERVATION_ID_CHARS + 1))
    assert check_expiry_age(MAX_EXPIRY_AGE_S) == MAX_EXPIRY_AGE_S
    with pytest.raises(ValueError):
        check_expiry_age(MAX_EXPIRY_AGE_S + 1)


# --- the database ---------------------------------------------------------------------------------------------


@pytest.fixture(name="w")
def money_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    world.release = world.new_role("rl")
    try:
        world.migrate(release_role=world.release)
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


def _can_exec(w, role, sig):
    return w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (role, sig))[0][0]


def _hadavin_functions(w):
    return w.run(
        "SELECT p.oid::regprocedure::text, pg_get_userbyid(p.proowner), p.proconfig FROM pg_proc p "
        "JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = %s AND p.proname LIKE 'hadavin\\_%%'",
        (w.schema,),
    )


@NEEDS_PG
def test_every_hadavin_function_of_the_schema_is_in_the_map_or_the_excluded_set(w):
    names = {sig.split("(")[0] for sig, _, _ in _hadavin_functions(w)}
    known = {s.split("(")[0] for s in (*mig.FUNCTION_GRANTS, *mig.EXCLUDED_FUNCTIONS)}
    assert names <= known, names - known
    assert {s.split("(")[0] for s in mig.FUNCTION_GRANTS} <= names


@NEEDS_PG
def test_migrate_refuses_a_hadavin_function_nobody_mapped(w):
    w.do("CREATE FUNCTION hadavin_rogue() RETURNS int LANGUAGE sql AS 'SELECT 1'")
    with pytest.raises(ConfigError, match=r"FUNCTION_GRANTS.*hadavin_rogue"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_the_search_path_of_each_money_function_is_pinned_with_the_temp_schema_last(w):
    pinned = {s: c for s, _, c in _hadavin_functions(w)}
    for sig in mig.MONEY_FUNCTIONS:
        (key,) = [k for k in pinned if k.split("(")[0] == sig.split("(")[0]]
        assert pinned[key] == [f"search_path=pg_catalog, {w.schema}, pg_temp"], key


@NEEDS_PG
@pytest.mark.parametrize("index", range(7))
def test_migrate_again_re_pins_a_function_whose_pin_was_lost(w, index):
    sig = mig.MONEY_FUNCTIONS[index]
    w.do(f"ALTER FUNCTION {sig} SET search_path = pg_catalog, pg_temp")
    assert w.migrate(release_role=w.release) == []
    got = w.run("SELECT proconfig FROM pg_proc WHERE oid = to_regprocedure(%s)", (sig,))
    assert got == [([f"search_path=pg_catalog, {w.schema}, pg_temp"],)]
    w.do(f"ALTER FUNCTION {sig} RESET search_path")
    w.migrate(release_role=w.release)
    got = w.run("SELECT proconfig FROM pg_proc WHERE oid = to_regprocedure(%s)", (sig,))
    assert got == [([f"search_path=pg_catalog, {w.schema}, pg_temp"],)]


@NEEDS_PG
def test_the_pin_does_nothing_for_a_schema_that_has_no_money_functions(w):
    scoped = w.new_schema("empty")
    with psycopg.connect(scoped, autocommit=True) as db:
        mig._pin_money_functions(db)  # no function, no error


@NEEDS_PG
def test_execute_goes_to_exactly_the_roles_of_the_map(w):
    holders = {
        w.runtime: lambda g: g.runtime,
        w.purge: lambda g: g.purge,
        w.release: lambda g: g.release,
        w.reset: lambda g: g.reset,
        w.portal: lambda g: g.portal,
        w.caps: lambda g: g.caps,
    }
    for sig, grant in mig.FUNCTION_GRANTS.items():
        for role, wants in holders.items():
            assert _can_exec(w, role, sig) is wants(grant), (role, sig)
        assert w.run("SELECT has_function_privilege('public', %s, 'EXECUTE')", (sig,)) == [(False,)]


@NEEDS_PG
@pytest.mark.parametrize("index", range(5))
def test_migrate_takes_a_hand_grant_of_execute_back_from_the_wrong_role(w, index):
    sig = mig.MONEY_FUNCTIONS[index]
    for role in (w.portal, w.reset, w.release, w.runtime, w.purge, w.caps):
        w.grant(f"GRANT EXECUTE ON FUNCTION {sig} TO {{}}", role)
    w.migrate(release_role=w.release)
    grant = mig.FUNCTION_GRANTS[sig]
    assert _can_exec(w, w.runtime, sig) is grant.runtime
    assert _can_exec(w, w.purge, sig) is grant.purge
    assert _can_exec(w, w.caps, sig) is grant.caps
    for role in (w.portal, w.reset, w.release):
        assert _can_exec(w, role, sig) is False


@NEEDS_PG
@pytest.mark.parametrize("index", range(7))
def test_migrate_refuses_when_public_can_run_a_money_function(w, index):
    sig = mig.MONEY_FUNCTIONS[index]
    w.do(f"GRANT EXECUTE ON FUNCTION {sig} TO PUBLIC")
    with pytest.raises(ConfigError, match=r"can run .*hadavin_"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_migrate_refuses_when_a_role_reaches_execute_through_a_membership(w):
    helper = w.new_role("helper", "NOLOGIN")
    w.grant(f"GRANT EXECUTE ON FUNCTION {PURGE} TO {{}}", helper)
    w.grant("GRANT {} TO {}", helper, w.portal)
    with pytest.raises(ConfigError):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_the_reset_role_slot_gives_execute_to_exactly_the_mapped_function(w, monkeypatch):
    """The reset slot works for a mapped function (add_spend stands in beside the two cap functions)."""
    monkeypatch.setitem(mig.FUNCTION_GRANTS, ADD, mig.FunctionGrant(runtime=True, reset=True))
    w.migrate(release_role=w.release)
    assert _can_exec(w, w.reset, ADD) is True
    for sig in mig.FUNCTION_GRANTS:
        if sig != ADD:
            assert _can_exec(w, w.reset, sig) is False, sig


@NEEDS_PG
@pytest.mark.parametrize("index", range(5))
def test_migrate_refuses_execute_for_the_reset_role_on_any_other_function(w, index):
    sig = mig.MONEY_FUNCTIONS[index]
    helper = w.new_role("rh", "NOLOGIN")
    w.grant(f"GRANT EXECUTE ON FUNCTION {sig} TO {{}}", helper)
    w.grant("GRANT {} TO {}", helper, w.reset)
    with pytest.raises(ConfigError, match=rf"{w.reset} can run"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_the_caps_role_holds_execute_on_exactly_the_two_cap_functions_and_passes_migrate(w):
    ran = {sig for sig in mig.FUNCTION_GRANTS if _can_exec(w, w.caps, sig)}
    assert ran == {SET_CAP, CAP_MATCHES}
    assert w.migrate(release_role=w.release) == []


@NEEDS_PG
def test_the_reset_role_holds_execute_on_no_money_function(w):
    """M4 (review-money-1): one identity per function. The login that clears a stop sets no cap."""
    assert {sig for sig in mig.FUNCTION_GRANTS if _can_exec(w, w.reset, sig)} == set()


@NEEDS_PG
@pytest.mark.parametrize("sig_name", ["SET_CAP", "CAP_MATCHES"])
def test_migrate_takes_the_cap_functions_back_from_the_reset_role(w, sig_name):
    sig = {"SET_CAP": SET_CAP, "CAP_MATCHES": CAP_MATCHES}[sig_name]
    w.grant(f"GRANT EXECUTE ON FUNCTION {sig} TO {{}}", w.reset)
    w.migrate(release_role=w.release)
    assert _can_exec(w, w.reset, sig) is False
    helper = w.new_role("ch", "NOLOGIN")
    w.grant(f"GRANT EXECUTE ON FUNCTION {sig} TO {{}}", helper)
    w.grant("GRANT {} TO {}", helper, w.reset)
    with pytest.raises(ConfigError, match=rf"{w.reset} can run"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_the_caps_role_may_not_be_the_reset_role_or_a_member_of_one(w):
    with pytest.raises(ConfigError, match="must be different roles"):
        w.migrate(release_role=w.release, caps_role=w.reset)
    w.grant("GRANT {} TO {}", w.reset, w.caps)
    with pytest.raises(ConfigError, match="must not be members of each other"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_a_caps_role_that_holds_more_than_the_map_is_refused(w):
    """Rights that come through a role it is a member of cannot be revoked from the caps role itself: refused."""
    for stmt in (
        "GRANT UPDATE ON TABLE spend TO {}",
        "GRANT DELETE ON TABLE audit_entries TO {}",
        "GRANT INSERT ON TABLE kill_switch_clears TO {}",
    ):
        helper = w.new_role("ch2", "NOLOGIN")
        w.grant(stmt, helper)
        w.grant("GRANT {} TO {}", helper, w.caps)
        with pytest.raises(ConfigError, match="the caps role holds more than the grant map"):
            w.migrate(release_role=w.release)
        w.grant("REVOKE {} FROM {}", helper, w.caps)
        w.roles.remove(helper)
        w.grant("DROP OWNED BY {}", helper)
        w.grant("DROP ROLE {}", helper)
        assert w.migrate(release_role=w.release) == []


@NEEDS_PG
@pytest.mark.parametrize("sig_name", ["SET_CAP", "CAP_MATCHES"])
def test_migrate_refuses_the_cap_functions_for_roles_that_may_not_run_them(w, sig_name):
    sig = {"SET_CAP": SET_CAP, "CAP_MATCHES": CAP_MATCHES}[sig_name]
    wants = mig.FUNCTION_GRANTS[sig]
    for role in (w.portal, w.purge, w.release):
        w.grant(f"GRANT EXECUTE ON FUNCTION {sig} TO {{}}", role)
    w.grant(f"GRANT EXECUTE ON FUNCTION {sig} TO {{}}", w.runtime)
    w.migrate(release_role=w.release)
    assert _can_exec(w, w.runtime, sig) is wants.runtime
    for role in (w.portal, w.purge, w.release):
        assert _can_exec(w, role, sig) is False
    w.do(f"GRANT EXECUTE ON FUNCTION {sig} TO PUBLIC")
    with pytest.raises(ConfigError, match=r"can run .*hadavin_"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_the_purge_role_with_only_execute_on_the_purge_function_passes_migrate(w):
    assert _can_exec(w, w.purge, PURGE) is True
    assert _can_exec(w, w.purge, RESERVE) is False
    assert w.migrate(release_role=w.release) == []


@NEEDS_PG
def test_the_execute_grants_are_applied_in_the_run_that_applies_0011():
    """A fresh schema: one migrate run applies every file AND gives the roles their EXECUTE."""
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        applied = world.migrate()
        assert any(a.startswith("0011") for a in applied)
        assert _can_exec(world, world.runtime, RESERVE) is True
        assert _can_exec(world, world.purge, PURGE) is True
    finally:
        with psycopg.connect(world.dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(world.schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


# --- one owner --------------------------------------------------------------------------------------------------


@NEEDS_PG
def test_the_default_owner_is_one_role_and_migrate_passes(w):
    owners = {o for _, o, _ in _hadavin_functions(w)}
    assert len(owners) == 1
    assert w.migrate(release_role=w.release) == []


@NEEDS_PG
def test_a_function_with_another_owner_is_refused_and_named(w):
    other = w.new_role("fo", "NOLOGIN")
    w.do(f"ALTER FUNCTION {ADD} OWNER TO {other}")
    with pytest.raises(ConfigError) as err:
        w.migrate(release_role=w.release)
    text = str(err.value)
    assert "hadavin_add_spend" in text and other in text and "ALTER FUNCTION" in text
    assert "OWNER TO" in text


@NEEDS_PG
def test_a_trigger_function_with_another_owner_is_refused_too(w):
    other = w.new_role("fo", "NOLOGIN")
    w.do(f"ALTER FUNCTION hadavin_money_guard() OWNER TO {other}")
    with pytest.raises(ConfigError, match="hadavin_money_guard"):
        w.migrate(release_role=w.release)


@NEEDS_PG
@pytest.mark.parametrize("which", ["runtime", "portal", "purge", "reset", "release"])
def test_a_named_role_that_owns_the_functions_is_refused(w, which):
    role = getattr(w, which)
    for sig, _, _ in _hadavin_functions(w):
        w.do(f"ALTER FUNCTION {sig} OWNER TO {role}")
    with pytest.raises(ConfigError) as err:
        w.migrate(release_role=w.release)
    assert role in str(err.value) and "owner" in str(err.value)


@NEEDS_PG
def test_a_named_role_that_is_a_member_of_the_function_owner_is_refused(w):
    owner = w.new_role("fo", "NOLOGIN")
    for sig, _, _ in _hadavin_functions(w):
        w.do(f"ALTER FUNCTION {sig} OWNER TO {owner}")
    w.grant("GRANT {} TO {}", owner, w.runtime)
    with pytest.raises(ConfigError, match="member"):
        w.migrate(release_role=w.release)


@NEEDS_PG
@pytest.mark.parametrize(
    "table",
    ["spend", "spend_month", "spend_reservations", "runs", "hadavin_limits", "hadavin_caps"],
)
def test_a_money_table_with_another_owner_than_the_functions_is_refused(w, table):
    fo = w.new_role("fo", "NOLOGIN")
    for sig, _, _ in _hadavin_functions(w):
        w.do(f"ALTER FUNCTION {sig} OWNER TO {fo}")
    with pytest.raises(ConfigError) as err:
        w.migrate(release_role=w.release)
    text = str(err.value)
    assert "ALTER" in text and "OWNER TO" in text and fo in text
    assert table in text or "spend" in text


@NEEDS_PG
def test_the_owner_texts_name_roles_and_objects_never_values(w):
    other = w.new_role("fo", "NOLOGIN")
    w.do(f"ALTER FUNCTION {ADD} OWNER TO {other}")
    with pytest.raises(ConfigError) as err:
        w.migrate(release_role=w.release)
    assert not re.search(r"postgresql://|password", str(err.value), re.IGNORECASE)


@NEEDS_PG
def test_the_runtime_that_owns_a_table_still_gets_the_existing_refusal(w):
    w.do(f"ALTER TABLE spend OWNER TO {w.runtime}")
    with pytest.raises(ConfigError, match=rf"{w.runtime}: owns spend"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_a_superuser_function_owner_is_allowed_with_a_note():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
        is_super = db.execute(
            "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"
        ).fetchone()[0]
    try:
        if not is_super:
            pytest.skip("the test login is not a superuser")
        notes: list[str] = []
        world.migrate(notes=notes)
        assert any("superuser" in n for n in notes), notes
    finally:
        with psycopg.connect(world.dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(world.schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


# --- hadavin_limits -----------------------------------------------------------------------------------------------


def _limits(w):
    return {k: v for k, v in w.run("SELECT name, value FROM hadavin_limits")}


@NEEDS_PG
def test_migrate_writes_the_limit_rows_from_the_python_constants(w):
    assert _limits(w) == {k: D(v) for k, v in mig.money_limits().items()}


@NEEDS_PG
def test_the_sql_limits_equal_the_python_constants_the_validators_use(w):
    got = _limits(w)
    assert got["max_amount"] == D(MAX_SPEND_USD)
    assert got["max_decimals"] == MAX_SPEND_DECIMALS
    assert "max_exponent" not in got
    assert got["max_id_chars"] == MAX_RESERVATION_ID_CHARS
    assert got["max_expiry_age"] == MAX_EXPIRY_AGE_S


@NEEDS_PG
def test_migrate_again_puts_back_a_changed_and_a_deleted_limit_row(w):
    w.do("UPDATE hadavin_limits SET value = 1 WHERE name = 'max_amount'")
    w.do("DELETE FROM hadavin_limits WHERE name = 'max_id_chars'")
    w.migrate(release_role=w.release)
    assert _limits(w) == {k: D(v) for k, v in mig.money_limits().items()}


@NEEDS_PG
def test_a_changed_default_reaches_the_rows_at_the_next_migrate(w, monkeypatch):
    monkeypatch.setattr(mig, "MAX_EXPIRY_AGE_S", 12345)
    monkeypatch.setattr(mig, "MAX_RESERVATION_ID_CHARS", 77)
    w.migrate(release_role=w.release)
    got = _limits(w)
    assert got["max_expiry_age"] == 12345 and got["max_id_chars"] == 77


@NEEDS_PG
def test_the_limit_rows_are_owned_by_the_function_owner(w):
    (owner,) = {o for _, o, _ in _hadavin_functions(w)}
    assert w.run(
        "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = 'hadavin_limits'::regclass"
    ) == [(owner,)]


@NEEDS_PG
def test_no_role_but_the_owner_can_read_or_write_the_limits(w):
    for role in (w.runtime, w.portal, w.purge, w.reset, w.release):
        for priv in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"):
            assert w.run("SELECT has_table_privilege(%s, 'hadavin_limits', %s)", (role, priv)) == [
                (False,)
            ], (role, priv)
        assert w.run(
            "SELECT count(*) FROM pg_attribute WHERE attrelid = 'hadavin_limits'::regclass AND attnum > 0 "
            "AND has_column_privilege(%s, attrelid, attnum, 'SELECT,INSERT,UPDATE')",
            (role,),
        ) == [(0,)]
    with w.as_(w.runtime) as db:
        for stmt in (
            "SELECT * FROM hadavin_limits",
            "UPDATE hadavin_limits SET value = 0",
            "DELETE FROM hadavin_limits",
            "INSERT INTO hadavin_limits VALUES ('x', 1)",
        ):
            with pytest.raises(errors.InsufficientPrivilege):
                db.execute(stmt)


@NEEDS_PG
def test_a_hand_grant_on_the_limits_is_taken_back_and_one_through_public_is_refused(w):
    w.grant("GRANT SELECT, UPDATE ON hadavin_limits TO {}", w.runtime)
    w.grant("GRANT SELECT ON hadavin_limits TO {}", w.portal)
    w.migrate(release_role=w.release)
    for role in (w.runtime, w.portal):
        assert w.run("SELECT has_table_privilege(%s, 'hadavin_limits', 'SELECT')", (role,)) == [
            (False,)
        ]
    w.do("GRANT SELECT ON hadavin_limits TO PUBLIC")
    with pytest.raises(ConfigError, match="hadavin_limits"):
        w.migrate(release_role=w.release)
