"""`migrate` reports a `default_transaction_isolation` default that reaches a named login and is not `read committed`
(lead-build-4 item 2). The store's connection pins READ COMMITTED itself (`postgres.py` `_SESSION_PINS`), so the
default changes nothing for the store; it is reported (log line and the `notes` of the CLI), never silently accepted
and never changed. Real PostgreSQL, a throwaway schema and throwaway logins. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from tests.test_stop_state_roles import World

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


@pytest.fixture(name="w")
def world():
    w = World()
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(w.schema)))
        for r in w.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        w.migrate()
        yield w
    finally:
        with psycopg.connect(w.dsn, autocommit=True) as db:
            for schema in w.schemas:
                db.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema))
                )
            for r in w.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _database(w) -> str:
    return w.run("SELECT current_database()")[0][0]


def _notes(w) -> list[str]:
    notes: list[str] = []
    w.migrate(notes=notes)
    return [n for n in notes if "default_transaction_isolation" in n]


def _setting(w, role: str) -> list[str]:
    rows = w.run(
        "SELECT c FROM pg_db_role_setting s CROSS JOIN LATERAL unnest(s.setconfig) c "
        "WHERE s.setrole = %s::regrole::oid AND c LIKE 'default\\_transaction\\_isolation=%%'",
        (role,),
    )
    return [r[0] for r in rows]


def test_no_default_no_note(w):
    assert _notes(w) == []


@pytest.mark.parametrize("level", ["repeatable read", "serializable"])
@pytest.mark.parametrize("scope", ["role in database", "role"])
def test_a_weaker_default_of_a_named_login_is_reported_not_changed(w, level, scope):
    where = f"IN DATABASE {_database(w)} " if scope == "role in database" else ""
    w.do(f"ALTER ROLE {w.runtime} {where}SET default_transaction_isolation = '{level}'")
    (note,) = _notes(w)
    assert w.runtime in note and level in note and "Not changed" in note
    assert _setting(w, w.runtime) == [f"default_transaction_isolation={level}"]  # never erased


def test_read_committed_is_not_reported(w):
    w.do(f"ALTER ROLE {w.portal} SET default_transaction_isolation = 'read committed'")
    assert _notes(w) == []


def test_a_database_wide_row_is_reported_as_every_role():
    """The catalog row of ALTER DATABASE ... SET (no role) is shared by parallel tests, so it is read from a double here;
    the query that finds it is the same one the role rows above go through."""
    from hadavin_sdk.store import migrate as mig

    class Db:
        def execute(self, query, params=()):
            return self

        def fetchall(self):
            return [
                ("-", 0, "appdb", "default_transaction_isolation=serializable"),
                ("-", 0, None, "default_transaction_isolation=read committed"),
            ]

    (note,) = mig.check_isolation_settings(Db(), ["rt"])
    assert "every role in database appdb" in note and "serializable" in note


def test_a_login_that_is_not_named_is_not_reported(w):
    other = w.new_role("other")
    w.do(f"ALTER ROLE {other} SET default_transaction_isolation = 'serializable'")
    assert _notes(w) == []


def test_the_notes_are_logged_at_warning_level(w, caplog):
    w.do(f"ALTER ROLE {w.purge} SET default_transaction_isolation = 'repeatable read'")
    with caplog.at_level("WARNING", logger="hadavin_sdk.migrate"):
        w.migrate()
    assert any(
        w.purge in r.getMessage() and "repeatable read" in r.getMessage() for r in caplog.records
    )
