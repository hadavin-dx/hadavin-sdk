"""E5 Major 2 (hostile review 1): the runtime login must not be able to make a process read a decoy stop table by
changing its OWN default search path (`ALTER ROLE <runtime> SET search_path = decoy`). Tests elsewhere pin the path
in the connection string, which hides it. Here the connection string is NOT pinned.

The store verifies at start-up that the effective search path of its connection is exactly the schema it is
configured for (the DSN's search_path option, else `backends.store.schema`, else `public`) and that the three stop
tables are in `current_schema()`; `migrate` finds and repairs per-role and per-database search_path settings of the
roles it is given. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
import uuid

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.store.migrate import migrate
from tests.test_stop_state_roles import stop_world  # noqa: F401 - the fixture

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

STOPS = ("kill_switch", "kill_switch_stops", "kill_switch_clears")


def _build(dsn, **settings):
    return make(
        "store",
        PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn", **settings),  # noqa: S106
        FakeSecretProvider({"pg-dsn": dsn}),
    )


def _decoy(w):
    """A schema the runtime login OWNS with an empty (OFF) copy of the stop tables."""
    name = f"sb_decoy_{w.sfx}"
    w.schemas.append(name)
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("CREATE SCHEMA {} AUTHORIZATION {}").format(
                sql.Identifier(name), sql.Identifier(w.runtime)
            )
        )
        for t in STOPS:
            db.execute(
                sql.SQL("CREATE TABLE {}.{} (LIKE {}.{} INCLUDING ALL)").format(
                    sql.Identifier(name),
                    sql.Identifier(t),
                    sql.Identifier(w.schema),
                    sql.Identifier(t),
                )
            )
        db.execute(
            sql.SQL("INSERT INTO {}.kill_switch SELECT * FROM {}.kill_switch").format(
                sql.Identifier(name), sql.Identifier(w.schema)
            )
        )
        db.execute(sql.SQL('UPDATE {}.kill_switch SET "on" = FALSE').format(sql.Identifier(name)))
    return name


def _attack(w, decoy):
    """The runtime login changes ITS OWN default search path."""
    with w.as_(w.runtime) as db:
        db.execute(
            sql.SQL("ALTER ROLE {} SET search_path = {}").format(
                sql.Identifier(w.runtime), sql.Identifier(decoy)
            )
        )


def _unpinned(w, role):
    return make_conninfo(w.dsn, user=role)


def _setting_rows(w, role):
    return w.run(
        "SELECT s.setdatabase, s.setconfig FROM pg_db_role_setting s JOIN pg_roles r ON r.oid = s.setrole "
        "WHERE r.rolname = %s AND EXISTS (SELECT 1 FROM unnest(s.setconfig) c WHERE c LIKE 'search_path=%%')",
        (role,),
    )


def test_a_runtime_login_that_changed_its_own_search_path_is_refused_at_start(w):
    decoy = _decoy(w)
    _attack(w, decoy)
    # a stop is in the real schema; the decoy says OFF
    w.store(w.runtime).set_kill_switch(KillSwitch(on=True, by="ops:stop"))
    with pytest.raises(ConfigError, match="search_path") as err:
        _build(_unpinned(w, w.runtime), db_schema=w.schema)
    assert decoy in str(err.value) and w.schema in str(err.value)


def test_the_default_expectation_is_public_and_a_decoy_path_is_refused_too(w):
    decoy = _decoy(w)
    _attack(w, decoy)
    with pytest.raises(ConfigError, match="search_path"):
        _build(_unpinned(w, w.runtime))


def test_an_unpinned_login_whose_path_is_not_the_configured_schema_is_refused(w):
    with pytest.raises(ConfigError, match="search_path") as err:
        _build(_unpinned(w, w.runtime), db_schema=w.schema)  # the role default is "$user", public
    assert w.schema in str(err.value)


def test_a_role_default_path_equal_to_the_configured_schema_starts(w):
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("ALTER ROLE {} SET search_path = {}").format(
                sql.Identifier(w.runtime), sql.Identifier(w.schema)
            )
        )
    s = _build(_unpinned(w, w.runtime), db_schema=w.schema)
    try:
        assert s.get_kill_switch().on is False
    finally:
        s._db.close()


def test_a_pinned_connection_string_overrides_a_role_default_and_the_real_tables_are_read(w):
    decoy = _decoy(w)
    _attack(w, decoy)
    w.store(w.runtime).set_kill_switch(KillSwitch(on=True, by="ops:stop"))
    assert w.read().on is True  # the pinned DSN of the world wins over the role default


def test_a_schema_setting_that_differs_from_the_pinned_dsn_is_refused(w):
    other = w.new_schema("other")
    assert other
    with pytest.raises(ConfigError, match="search_path"):
        _build(w.dsn_of(w.runtime), db_schema=f"sb_other_{w.sfx}")


def test_missing_stop_tables_say_kill_switch_not_found_in_current_schema_and_name_it(w):
    empty = w.new_schema("empty")
    name = f"sb_empty_{w.sfx}"
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(name), sql.Identifier(w.runtime)
            )
        )
    with pytest.raises(ConfigError, match=r"kill_switch not found in current_schema\(\)") as err:
        _build(make_conninfo(empty, user=w.runtime))
    assert name in str(err.value)


def test_migrate_repairs_a_search_path_default_the_runtime_set_on_itself(w):
    decoy = _decoy(w)
    _attack(w, decoy)
    assert _setting_rows(w, w.runtime)
    w.migrate()
    assert _setting_rows(w, w.runtime)  # role-wide row kept (E5c); this database is pinned instead


def test_migrate_repairs_a_role_in_database_search_path_default(w):
    decoy = _decoy(w)
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("ALTER ROLE {} IN DATABASE {} SET search_path = {}").format(
                sql.Identifier(w.reset),
                sql.Identifier(db.info.dbname),
                sql.Identifier(decoy),
            )
        )
    assert _setting_rows(w, w.reset)
    w.migrate()
    assert _setting_rows(w, w.reset) == []


def test_migrate_refuses_a_database_wide_search_path_that_is_not_the_schema(w):
    decoy = _decoy(w)
    name = f"sb_db_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    try:
        dsn = make_conninfo(w.dsn, dbname=name)
        with psycopg.connect(dsn, autocommit=True) as db:
            db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(w.schema)))
        with psycopg.connect(w.dsn, autocommit=True) as db:
            db.execute(
                sql.SQL("ALTER DATABASE {} SET search_path = {}").format(
                    sql.Identifier(name), sql.Identifier(decoy)
                )
            )
        scoped = make_conninfo(dsn, options=f"-c search_path={w.schema}")
        with pytest.raises(ConfigError, match="database"):
            migrate(
                scoped,
                runtime_role=w.runtime,
                portal_role=w.portal,
                purge_role=w.purge,
                reset_role=w.reset,
            )
    finally:
        with psycopg.connect(w.dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
