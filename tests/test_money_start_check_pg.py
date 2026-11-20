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


def test_the_reset_login_mark_is_not_held_to_the_runtime_map(w):
    w.grant(f"GRANT UPDATE ON {w.schema}.hadavin_caps TO {{}}", w.reset)
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106
    settings._login_role = "reset"
    store = make("store", settings, FakeSecretProvider({"pg-dsn": w.dsn_of(w.reset)}))
    w.stores.append(store)


def test_the_purge_and_portal_logins_start_with_their_own_function_rights(w):
    # the purge login holds EXECUTE on the purge (its job) and is not the runtime: not refused
    for role in (w.portal, w.purge):
        _build(w, w.dsn_of(role))
