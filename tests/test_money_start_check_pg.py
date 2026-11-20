"""Review M3 (hostile re-read 2): the store refuses to start for a runtime login that holds a write right on a money
table (table or column level, directly or through a role) or may EXECUTE set_cap, release or purge. The owner or a
superuser (the dev setup) is outside the check. Real PostgreSQL, throwaway schema and roles. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.errors import ConfigError
from tests.test_stop_state_roles import stop_world  # noqa: F401 - the fixture

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
TABLES = ("spend", "spend_month", "spend_reservations", "hadavin_caps", "hadavin_limits")
FUNCTIONS = {
    "hadavin_set_cap": "(text, numeric, numeric, text)",
    "hadavin_release_expired_spend": "(text, date)",
    "hadavin_purge_spend_reservations": "(timestamptz)",
}


def _build(w, dsn):
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106
    store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
    w.stores.append(store)
    return store


def test_a_restricted_runtime_login_starts(w):
    assert _build(w, w.dsn_of(w.runtime)).get_kill_switch().on is False


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.parametrize("right", ["INSERT", "UPDATE", "DELETE", "TRUNCATE"])
def test_a_table_write_right_is_refused_and_named(w, table, right):
    w.grant(f"GRANT {right} ON {w.schema}.{table} TO {{}}", w.runtime)
    with pytest.raises(ConfigError) as caught:
        _build(w, w.dsn_of(w.runtime))
    msg = str(caught.value)
    assert f"{right} on {table}" in msg and "--runtime-role" in msg
    assert w.dsn not in msg


@pytest.mark.parametrize(
    ("table", "column", "right"),
    [
        ("spend", "usd", "UPDATE"),
        ("spend_reservations", "reserved_usd", "UPDATE"),
        ("hadavin_caps", "day_cap", "UPDATE"),
        ("spend", "usd", "INSERT"),
    ],
)
def test_a_column_grant_is_refused_too(w, table, column, right):
    w.grant(f"GRANT {right} ({column}) ON {w.schema}.{table} TO {{}}", w.runtime)
    with pytest.raises(ConfigError, match=f"{right} on {table}"):
        _build(w, w.dsn_of(w.runtime))


def test_a_right_through_a_role_the_login_is_a_member_of_is_refused(w):
    group = w.new_role("mgrp", "NOLOGIN")
    w.grant(f"GRANT UPDATE ON {w.schema}.hadavin_caps TO {{}}", group)
    w.grant("GRANT {} TO {}", group, w.runtime)
    with pytest.raises(ConfigError, match="UPDATE on hadavin_caps"):
        _build(w, w.dsn_of(w.runtime))


@pytest.mark.parametrize("function", list(FUNCTIONS))
def test_execute_on_a_function_of_another_role_is_refused(w, function):
    w.grant(
        f"GRANT EXECUTE ON FUNCTION {w.schema}.{function}{FUNCTIONS[function]} TO {{}}", w.runtime
    )
    with pytest.raises(ConfigError, match=f"EXECUTE on {function}"):
        _build(w, w.dsn_of(w.runtime))


def test_select_on_spend_and_the_runtime_functions_are_not_a_problem(w):
    # GRANTS gives the runtime SELECT on spend and spend_month and EXECUTE on the bookings: that is the clean state
    assert w.run("SELECT has_table_privilege(%s, %s, 'SELECT')", (w.runtime, f"{w.schema}.spend"))[
        0
    ][0]
    _build(w, w.dsn_of(w.runtime))


def test_the_owner_login_is_outside_the_check(w):
    # the dev setup: the superuser/owner connection starts even though it holds every right
    assert _build(w, w.scoped).get_kill_switch().on is False


def _build_marked(w, role, mark):
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106
    if mark:
        settings._login_role = mark
    store = make("store", settings, FakeSecretProvider({"pg-dsn": w.dsn_of(role)}))
    w.stores.append(store)
    return store


def test_the_reset_mark_exempts_exactly_the_check(w):
    # an over-granted reset-marked login builds; the same over-grant on an unmarked login is refused
    other = w.new_role("ovg")
    w.grant(f"GRANT USAGE ON SCHEMA {w.schema} TO {{}}", other)
    w.grant(f"GRANT UPDATE ON {w.schema}.spend TO {{}}", other)
    _build_marked(w, other, "reset")
    with pytest.raises(ConfigError, match="UPDATE on spend"):
        _build_marked(w, other, None)


def test_the_purge_and_portal_logins_start_with_their_own_function_rights(w):
    # the purge login holds EXECUTE on the purge (its job) and is not the runtime: not refused
    for role in (w.portal, w.purge):
        _build(w, w.dsn_of(role))


def test_the_caps_login_mark_is_exempt_like_the_reset_login(w):
    w.grant(f"GRANT UPDATE ON {w.schema}.hadavin_caps TO {{}}", w.caps)
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106
    settings._login_role = "reset"  # what the CLI sets for the caps login (cli._caps_login)
    store = make("store", settings, FakeSecretProvider({"pg-dsn": w.dsn_of(w.caps)}))
    w.stores.append(store)


@pytest.mark.parametrize("table", ["spend", "hadavin_caps"])
def test_the_caps_login_cannot_start_the_runtime_store_with_a_money_table_write(w, table):
    # an unmarked caps login (the runtime path) is held to the runtime's rights: a money-table write refuses it
    w.grant(f"GRANT UPDATE ON {w.schema}.{table} TO {{}}", w.caps)
    with pytest.raises(ConfigError, match=f"UPDATE on {table}"):
        _build(w, w.dsn_of(w.caps))


def _server_version(w):
    return int(w.run("SHOW server_version_num")[0][0])


@pytest.mark.parametrize(
    "target", ["spend.UPDATE", "hadavin_caps.UPDATE", "kill_switch_clears.INSERT"]
)
def test_a_noinherit_login_in_a_group_with_write_rights_is_refused(w, target):
    # has_table_privilege is false for a NOINHERIT login, but it can SET ROLE to the group and write
    table, right = target.split(".")
    group = w.new_role("ngrp", "NOLOGIN")
    w.grant(f"GRANT {right} ON {w.schema}.{table} TO {{}}", group)
    w.grant("ALTER ROLE {} NOINHERIT", w.runtime)
    w.grant("GRANT {} TO {}", group, w.runtime)
    with pytest.raises(ConfigError, match=f"{right} on {table}"):
        _build(w, w.dsn_of(w.runtime))


def test_a_nested_group_chain_is_walked(w):
    outer = w.new_role("outer", "NOLOGIN")
    inner = w.new_role("inner", "NOLOGIN")
    w.grant(f"GRANT UPDATE ON {w.schema}.spend TO {{}}", inner)
    w.grant("GRANT {} TO {}", inner, outer)
    w.grant("ALTER ROLE {} NOINHERIT", w.runtime)
    w.grant("GRANT {} TO {}", outer, w.runtime)
    with pytest.raises(ConfigError, match="UPDATE on spend"):
        _build(w, w.dsn_of(w.runtime))


def test_inherit_false_set_true_membership_is_refused(w):
    if _server_version(w) < 160000:
        pytest.skip("GRANT ... WITH INHERIT FALSE, SET TRUE needs PostgreSQL 16 or later")
    group = w.new_role("fgrp", "NOLOGIN")
    w.grant(f"GRANT UPDATE ON {w.schema}.spend TO {{}}", group)
    w.grant("GRANT {} TO {} WITH INHERIT FALSE, SET TRUE", group, w.runtime)
    with pytest.raises(ConfigError, match="UPDATE on spend"):
        _build(w, w.dsn_of(w.runtime))


def test_the_owner_exemption_logs_a_warning(w, caplog):
    import hadavin_sdk.store.postgres as pgmod

    pgmod._WARNED_OWNER.discard(w.schema)
    with caplog.at_level("WARNING", logger="hadavin_sdk.store"):
        _build(w, w.scoped)
    assert "start checks" in caplog.text and "skipped" in caplog.text


def test_owning_one_money_table_exempts_only_that_table(w):
    # the login owns hadavin_limits (so it holds every right there) but also UPDATE on spend: spend is still judged
    w.grant(f"ALTER TABLE {w.schema}.hadavin_limits OWNER TO {{}}", w.runtime)
    w.grant(f"GRANT UPDATE ON {w.schema}.spend TO {{}}", w.runtime)
    with pytest.raises(ConfigError) as caught:
        _build(w, w.dsn_of(w.runtime))
    assert "UPDATE on spend" in str(caught.value) and "hadavin_limits" not in str(caught.value)


def test_the_trigger_right_on_a_money_table_is_refused(w):
    w.grant(f"GRANT TRIGGER ON {w.schema}.spend_month TO {{}}", w.runtime)
    with pytest.raises(ConfigError, match="TRIGGER on spend_month"):
        _build(w, w.dsn_of(w.runtime))


def test_missing_money_tables_are_said_not_passed_silently(w, caplog):
    import psycopg

    import hadavin_sdk.store.postgres as pgmod

    empty = w.new_schema("empty")
    with psycopg.connect(empty) as db, caplog.at_level("WARNING", logger="hadavin_sdk.store"):
        assert pgmod.own_money_rights_problems(db, f"sb_empty_{w.sfx}") == []
    assert "not found" in caplog.text and "spend" in caplog.text


def test_only_the_window_refusal_is_the_booking_day_refusal(w):
    import psycopg

    import hadavin_sdk.store.postgres as pgmod
    from hadavin_sdk.store.protocol import BookingDayRefused

    def refusal(day_sql):
        with w.as_(w.runtime) as db, pytest.raises(psycopg.errors.DataError) as err:
            db.execute(f"SELECT * FROM hadavin_add_spend('x', {day_sql}, 1)")  # noqa: S608
        return pgmod._money_error(err.value)

    assert isinstance(refusal("current_date + 5"), BookingDayRefused)
    for other in ("DATE 'infinity'", "DATE '1960-01-01'"):
        got = refusal(other)
        assert isinstance(got, ValueError) and not isinstance(got, BookingDayRefused)
