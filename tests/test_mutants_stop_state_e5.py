"""Killers for the mutants of ``tests/stop_state_mutants.py`` that the older tests of the E5 guards let survive
(verify_schema, check_role_settings, check_maintain, collides, the still-ON message). Each test names the guard it
pins; the mutant that reverts that guard is in ``HAND`` of the mutant list. Needs HADAVIN_TEST_PG_DSN for the
database cases."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk import cli
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.secret_name import collides
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store import postgres as pg_mod
from tests.test_stop_state_roles import stop_world  # noqa: F401 - the fixture
from tests.test_stop_state_unit import Audit, StoreStub

needs_pg = pytest.mark.skipif(
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


def _role_default(w, value):
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("ALTER ROLE {} SET search_path = {}").format(
                sql.Identifier(w.runtime),
                sql.SQL(value).format(*[sql.Identifier(w.schema)])
                if "{}" in value
                else sql.SQL(value),
            )
        )


# --- verify_schema ---------------------------------------------------------------------------------------------------


@needs_pg
def test_e5e_an_extra_schema_on_the_effective_path_is_refused(w):
    """current_schema() is the configured schema, but the path also holds `public`: a second schema is on it."""
    _role_default(w, "{}, public")
    with pytest.raises(ConfigError, match="effective search_path of this login is") as err:
        _build(make_conninfo(w.dsn, user=w.runtime), db_schema=w.schema)
    assert f"{w.schema}, public" in str(err.value)


@needs_pg
def test_e5e_a_path_that_starts_with_pg_catalog_is_refused_by_current_schema(w):
    """The effective path (pg_catalog left out) equals the expected one, but current_schema() is pg_catalog."""
    _role_default(w, "pg_catalog, {}")
    with pytest.raises(ConfigError, match=r"current_schema\(\) is 'pg_catalog'"):
        _build(make_conninfo(w.dsn, user=w.runtime), db_schema=w.schema)


@needs_pg
def test_e5e_a_view_named_like_a_stop_table_is_not_the_stop_table(w):
    name = f"sb_view_{w.sfx}"
    w.schemas.append(name)
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
        for t in STOPS[1:]:
            db.execute(
                sql.SQL("CREATE TABLE {}.{} (LIKE {}.{} INCLUDING ALL)").format(
                    sql.Identifier(name),
                    sql.Identifier(t),
                    sql.Identifier(w.schema),
                    sql.Identifier(t),
                )
            )
        db.execute(
            sql.SQL("CREATE VIEW {}.kill_switch AS SELECT * FROM {}.kill_switch").format(
                sql.Identifier(name), sql.Identifier(w.schema)
            )
        )
        db.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(name), sql.Identifier(w.runtime)
            )
        )
    with pytest.raises(ConfigError, match=r"missing relations: kill_switch\)"):
        _build(make_conninfo(w.dsn, user=w.runtime, options=f"-c search_path={name}"))


@needs_pg
def test_e5e_a_refused_schema_check_closes_the_connection(w, monkeypatch):
    opened = []
    real = pg_mod.connect

    def spy(*args, **kwargs):
        conn = real(*args, **kwargs)
        opened.append(conn)
        return conn

    monkeypatch.setattr(pg_mod, "connect", spy)
    with pytest.raises(ConfigError, match="search_path"):
        _build(make_conninfo(w.dsn, user=w.runtime), db_schema=w.schema)  # unpinned: refused
    assert len(opened) == 1
    assert opened[0].closed is True


# --- check_role_settings ---------------------------------------------------------------------------------------------


@needs_pg
def test_e5e_a_role_with_a_role_wide_row_and_a_row_for_this_database_is_changed_once(w):
    """The row for this database is overwritten by the SET of the role-wide row, so it is neither reset nor reported:
    one note, and this database ends pinned to the schema whatever the order the rows are read in."""
    with psycopg.connect(w.dsn, autocommit=True) as db:
        dbname = db.info.dbname
        db.execute(
            sql.SQL("ALTER ROLE {} SET search_path = other_app").format(sql.Identifier(w.runtime))
        )
        db.execute(
            sql.SQL("ALTER ROLE {} IN DATABASE {} SET search_path = decoy_x").format(
                sql.Identifier(w.runtime), sql.Identifier(dbname)
            )
        )
    seen = []
    w.migrate(on_role_change=seen.append)
    assert len(seen) == 1 and "role-wide default" in seen[0]
    rows = dict(
        w.run(
            "SELECT d.datname, split_part(c, '=', 2) FROM pg_db_role_setting s "
            "JOIN pg_roles r ON r.oid = s.setrole LEFT JOIN pg_database d ON d.oid = s.setdatabase, "
            "unnest(s.setconfig) c WHERE r.rolname = %s AND c LIKE 'search\\_path=%%'",
            (w.runtime,),
        )
    )
    assert rows[dbname] == w.schema and rows[None] == "other_app"


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0]

    def fetchall(self):
        return self.rows


class _Db:
    """current_schema() is 'app'; an ALTER ROLE is accepted and changes nothing."""

    def __init__(self):
        self.statements = []

    def execute(self, query, params=()):
        text = query if isinstance(query, str) else query.as_string()
        if "current_schema()" in text:
            return _Result([("app", "d")])
        self.statements.append(text)
        return _Result([])


def test_e5e_a_search_path_default_that_the_repair_did_not_change_is_refused(monkeypatch):
    stuck = [(7, "r1", "d", "search_path=decoy")]
    monkeypatch.setattr(mig, "_path_rows", lambda db, named: stuck)
    db = _Db()
    with pytest.raises(ConfigError, match="could not be repaired") as err:
        mig.check_role_settings(db, ["r1"])
    assert "r1: search_path=decoy" in str(err.value)
    assert db.statements  # the repair was tried


# --- migrate calls check_maintain ------------------------------------------------------------------------------------


@needs_pg
def test_e5e_migrate_runs_check_maintain_for_the_named_roles(w, monkeypatch):
    seen = []
    monkeypatch.setattr(mig, "check_maintain", lambda db, named: seen.append(list(named)))
    w.migrate()
    assert [sorted(n) for n in seen] == [sorted(w.roles)]


# --- collides and the still-ON message -------------------------------------------------------------------------------


def test_e5e_collides_with_no_names_is_false_for_a_file_backed_provider_too():
    assert collides("a/../x", [], file_backed=True) is False
    assert collides("/lead", [], file_backed=True) is False


def test_e5e_a_reset_that_finds_the_switch_on_with_no_known_setter_says_so(capsys):
    store = StoreStub(read=KillSwitch(on=True, by=None))
    assert cli.kill_switch(Limits(store, Audit(), None), "reset", "user:op") == 2
    assert "kill switch still ON (set by someone unknown)" in capsys.readouterr().err
