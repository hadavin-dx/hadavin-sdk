"""E6 Major 2 (hostile review 2): the runtime login's own rights on the stop tables are checked when the store is
built. A `GRANT ALL ON ALL TABLES` after migrate (a provisioning step, a restored snapshot) lets the runtime clear a
stop with one INSERT into kill_switch_clears; now the store refuses to start, naming the table and the right (never
a value). The reset login (marked by the CLI) is not held to the runtime's map. Real PostgreSQL, throwaway schema
and roles with unique names (the `w` fixture), dropped afterwards. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import KillSwitch
from tests.test_stop_state_roles import stop_world  # noqa: F401 - the fixture

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


def _build(w, role, *, mark=None):
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106
    if mark:
        settings._login_role = mark
    store = make("store", settings, FakeSecretProvider({"pg-dsn": w.dsn_of(role)}))
    w.stores.append(store)
    return store


def test_a_clean_migrate_starts_for_the_runtime_login(w):
    assert _build(w, w.runtime).get_kill_switch().on is False


def test_a8_grant_all_after_migrate_is_refused_at_start_naming_table_and_right(w):
    w.grant("GRANT ALL ON ALL TABLES IN SCHEMA " + w.schema + " TO {}", w.runtime)
    with pytest.raises(ConfigError) as caught:
        _build(w, w.runtime)
    msg = str(caught.value)
    assert "kill_switch_clears" in msg and "INSERT" in msg
    assert w.dsn not in msg and "password" not in msg.lower()


@pytest.mark.parametrize(
    ("table", "right"),
    [
        ("kill_switch", "UPDATE"),
        ("kill_switch", "INSERT"),
        ("kill_switch", "DELETE"),
        ("kill_switch", "TRUNCATE"),
        ("kill_switch_stops", "UPDATE"),
        ("kill_switch_stops", "DELETE"),
        ("kill_switch_stops", "TRUNCATE"),
        ("kill_switch_clears", "INSERT"),
        ("kill_switch_clears", "UPDATE"),
        ("kill_switch_clears", "DELETE"),
        ("kill_switch_clears", "TRUNCATE"),
        ("kill_switch_stops", "TRIGGER"),
    ],
)
def test_one_extra_right_on_a_stop_table_is_refused_and_named(w, table, right):
    w.grant(f"GRANT {right} ON {w.schema}.{table} TO {{}}", w.runtime)
    with pytest.raises(ConfigError) as caught:
        _build(w, w.runtime)
    assert table in str(caught.value) and right in str(caught.value)


def test_the_extra_right_through_a_role_the_runtime_is_a_member_of_is_refused_too(w):
    group = w.new_role("grp", "NOLOGIN")
    w.grant(f"GRANT INSERT ON {w.schema}.kill_switch_clears TO {{}}", group)
    w.grant("GRANT {} TO {}", group, w.runtime)
    with pytest.raises(ConfigError, match="kill_switch_clears"):
        _build(w, w.runtime)


def test_the_stop_command_path_builds_through_the_same_factory_and_writes_nothing_when_refused(w):
    """`limits stop` builds its store with make("store", ...) (cli.py), the factory checked above, so a refused
    build means no stop is written and the CLI's ConfigError handling shows the message."""
    w.grant("GRANT ALL ON ALL TABLES IN SCHEMA " + w.schema + " TO {}", w.runtime)
    with pytest.raises(ConfigError, match="kill_switch_clears"):
        _build(w, w.runtime)
    assert w.count("kill_switch_stops") == 0


def test_the_reset_login_marked_by_the_cli_starts_and_clears(w):
    rt = _build(w, w.runtime)
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    rs = _build(w, w.reset, mark="reset")
    rs.clear_stops("admin:reset", [s.id for s in rs.open_stops()])
    assert rt.get_kill_switch().on is False


def test_a_login_with_reset_rights_that_is_not_marked_is_refused_so_the_runtime_cannot_pass_as_reset(
    w,
):
    with pytest.raises(ConfigError, match="kill_switch"):
        _build(w, w.reset)


def test_a_marker_cannot_come_from_the_config_file():
    with pytest.raises(ValueError):
        PostgresSettings(kind="postgres", dsn_secret_name="x", _login_role="reset")  # noqa: S106


def test_the_other_logins_start(w):
    for role in (w.portal, w.purge):
        _build(w, role)
