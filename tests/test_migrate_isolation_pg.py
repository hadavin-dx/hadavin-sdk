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


def _made_world():
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


@pytest.fixture(name="w")
def world():
    yield from _made_world()


@pytest.fixture(name="w2")
def second_world():
    """Another test's world on the same server (a parallel worker's, in a real run)."""
    yield from _made_world()


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


@pytest.mark.parametrize("level", ["read committed", "read uncommitted"])
def test_read_committed_and_its_alias_are_not_reported(w, level):
    """PostgreSQL runs `read uncommitted` as `read committed`: no note for either."""
    w.do(f"ALTER ROLE {w.portal} SET default_transaction_isolation = '{level}'")
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


# --- parallel workers share one cluster: a role that inherits the owner is visible to every migrate -----------------------


def test_a_role_that_inherits_the_owner_is_seen_by_another_worlds_migrate(w, w2):
    """Why `World.hazard()` exists: roles are server-wide, and a login that inherits the (superuser) owner can write
    every money table of every schema, so ANOTHER world's migrate refuses while the grant exists."""
    from hadavin_sdk.errors import ConfigError

    owner = w.run("SELECT current_user")[0][0]
    with w.hazard():
        w.grant("GRANT {} TO {}", owner, w.runtime)
        try:
            with pytest.raises(ConfigError, match="can write a money table"):
                w2.migrate()
        finally:
            w.grant("REVOKE {} FROM {}", owner, w.runtime)
    assert w2.migrate() == []


def _gate_free_for_shared() -> bool:
    """True when a second connection can take the shared gate (what every other worker's migrate needs)."""
    from tests import pg_gate

    with psycopg.connect(w_dsn(), autocommit=True) as db:
        got = db.execute("SELECT pg_try_advisory_lock_shared(%s)", (pg_gate.GATE,)).fetchone()[0]
        if got:
            db.execute("SELECT pg_advisory_unlock_shared(%s)", (pg_gate.GATE,))
        return got


def w_dsn() -> str:
    return os.environ["HADAVIN_TEST_PG_DSN"]


def test_hazard_holds_the_exclusive_server_gate(w):
    """Another worker's migrate takes the gate SHARED; while a hazard role may exist it must be unable to. (Not
    asserted outside the block: another worker may hold either lock at that moment.)"""
    with w.hazard():
        assert _gate_free_for_shared() is False
