"""Parallel test workers share one PostgreSQL cluster and roles are server-wide: a login that inherits the owner is
seen by every other worker's `migrate`. `World.hazard()` holds the exclusive server gate while such a grant exists.
Real PostgreSQL, throwaway schemas and logins. Needs HADAVIN_TEST_PG_DSN."""

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
