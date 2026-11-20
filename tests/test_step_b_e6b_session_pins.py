"""E12 (Low-Medium 5): a role default `default_transaction_read_only = on` or `synchronous_commit = off` must not
weaken the store session; `connect()` pins `off` / `on` after login. Real PostgreSQL, a throwaway schema and role."""

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from hadavin_sdk.config import ConfigError
from hadavin_sdk.store import postgres as postgres_mod
from tests.contracts.kinds.store_postgres import pg_schema

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"), reason="HADAVIN_TEST_PG_DSN not set"
)


@pytest.fixture
def runtime_dsn():
    yield from pg_schema(runtime=True)


def _weaken(dsn, role):
    admin = os.environ["HADAVIN_TEST_PG_DSN"]
    with psycopg.connect(admin, autocommit=True) as db:
        for setting, value in (
            ("default_transaction_read_only", "on"),
            ("synchronous_commit", "off"),
        ):
            db.execute(
                sql.SQL("ALTER ROLE {} SET {} = {}").format(
                    sql.Identifier(role), sql.SQL(setting), sql.SQL(value)
                )
            )


def _role(dsn):
    return psycopg.conninfo.conninfo_to_dict(dsn)["user"]


def test_role_defaults_do_not_weaken_the_session(runtime_dsn):
    _weaken(runtime_dsn, _role(runtime_dsn))
    # the role default really is in force on a plain connection
    with psycopg.connect(runtime_dsn, autocommit=True) as plain:
        assert plain.execute("SHOW default_transaction_read_only").fetchone()[0] == "on"
    db = postgres_mod.connect(runtime_dsn)
    try:
        assert db.execute("SHOW default_transaction_read_only").fetchone()[0] == "off"
        assert db.execute("SHOW synchronous_commit").fetchone()[0] == "on"
        # a `limits stop` style insert succeeds
        db.execute('INSERT INTO kill_switch_stops("by") VALUES (%s)', ("e12-test",))
    finally:
        db.close()


def test_a_server_that_does_not_take_the_pin_is_refused(runtime_dsn, monkeypatch):
    real = psycopg.Connection.execute

    def fake(self, query, *a, **k):
        cur = real(self, query, *a, **k)
        if isinstance(query, str) and query.startswith("SHOW synchronous_commit"):
            return real(self, "SELECT 'off'")
        return cur

    monkeypatch.setattr(psycopg.Connection, "execute", fake)
    with pytest.raises(ConfigError, match="synchronous_commit"):
        postgres_mod.connect(runtime_dsn)
