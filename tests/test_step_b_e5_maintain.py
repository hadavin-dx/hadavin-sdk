"""E5 Major 6 (hostile review 1): on PostgreSQL 17 the MAINTAIN right lets a role LOCK a table in any mode, so a
runtime role holding it (directly, through PUBLIC or through pg_maintain) could take ACCESS EXCLUSIVE on the stop
tables and block every read of the stop. `migrate` revokes MAINTAIN from everyone but the owner on the three stop
tables and refuses when a named role still holds it; the store connection that reads the stop sets lock_timeout.

The check is gated on server_version_num >= 170000 (below it the privilege does not exist and naming it is an
error). The test server of the lane is PostgreSQL 16, so the logic is run against a scripted connection here, and
a real-server case runs where the server is 17 or newer. Needs HADAVIN_TEST_PG_DSN for the real cases."""

from __future__ import annotations

import os
import time

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql

from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig

needs_pg = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeDb:
    """A scripted connection: `acl` is the (table, grantee) MAINTAIN grants other than the owner's; a REVOKE removes
    them unless `sticky`; `holds` are the named roles for which has_table_privilege(..., 'MAINTAIN') stays true."""

    def __init__(self, version=170000, acl=(), holds=(), sticky=False):
        self.version, self.acl, self.holds, self.sticky = version, list(acl), set(holds), sticky
        self.revokes = []

    def execute(self, query, params=()):
        text = query if isinstance(query, str) else query.as_string()
        if "server_version_num" in text:
            return _Result([(self.version,)])
        if "current_schema()" in text and "aclexplode" not in text:
            return _Result([("app",)])
        if "aclexplode" in text:
            return _Result(list(self.acl))
        if text.startswith("REVOKE") or "REVOKE" in text.split("ON")[0]:
            self.revokes.append(text)
            if not self.sticky:
                self.acl = []
            return _Result([])
        if "has_table_privilege" in text:
            if self.version < 170000:
                raise AssertionError("MAINTAIN named on a server that does not have it")
            return _Result([(params[0] in self.holds,)])
        raise AssertionError(text)


def test_below_postgresql_17_nothing_is_checked_or_named():
    db = FakeDb(version=160000, acl=[("kill_switch", "PUBLIC")])
    mig.check_maintain(db, ["rt"])
    assert db.revokes == []


def test_a_maintain_grant_on_a_stop_table_is_revoked():
    db = FakeDb(acl=[("kill_switch", "PUBLIC"), ("kill_switch_stops", "rt")])
    mig.check_maintain(db, ["rt"])
    assert len(db.revokes) == 2 and any("PUBLIC" in r for r in db.revokes)
    assert all("MAINTAIN" in r for r in db.revokes)


def test_a_maintain_grant_that_stays_after_the_revoke_is_refused():
    db = FakeDb(acl=[("kill_switch", "other")], sticky=True)
    with pytest.raises(ConfigError, match="MAINTAIN.*other"):
        mig.check_maintain(db, ["rt"])


def test_a_named_role_that_can_maintain_through_pg_maintain_is_refused():
    db = FakeDb(holds={"rt"})
    with pytest.raises(ConfigError, match="rt holds MAINTAIN"):
        mig.check_maintain(db, ["rt", "po"])


def test_a_clean_server_passes():
    mig.check_maintain(FakeDb(), ["rt", "po"])


@needs_pg
def test_the_store_connection_that_reads_the_stop_waits_at_most_lock_timeout(monkeypatch):
    """A holder of ACCESS EXCLUSIVE on the stop table makes the read fail inside the timeout, not hang."""
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends.factory import make
    from hadavin_sdk.backends.table import PostgresSettings
    from tests.contracts.kinds.store_postgres import pg_schema

    monkeypatch.setattr(defaults, "STORE_LOCK_TIMEOUT_MS", 500)
    gen = pg_schema()
    dsn = next(gen)
    store = make(
        "store",
        PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn"),  # noqa: S106
        FakeSecretProvider({"pg-dsn": dsn}),
    )
    holder = psycopg.connect(dsn)
    try:
        assert store._db.execute("SHOW lock_timeout").fetchone()[0] == "500ms"
        holder.execute("LOCK TABLE kill_switch IN ACCESS EXCLUSIVE MODE")
        started = time.monotonic()
        with pytest.raises(errors.LockNotAvailable):
            store.get_kill_switch()
        assert time.monotonic() - started < 10
    finally:
        holder.rollback()
        holder.close()
        store._db.close()
        gen.close()


@needs_pg
def test_on_a_real_postgresql_17_a_runtime_role_cannot_lock_a_stop_table():
    from tests.test_stop_state_roles import World

    dsn = os.environ["HADAVIN_TEST_PG_DSN"]
    with psycopg.connect(dsn) as db:
        if db.execute("SELECT current_setting('server_version_num')::int").fetchone()[0] < 170000:
            pytest.skip("MAINTAIN exists from PostgreSQL 17; this server is older")
    w = World()
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(w.schema)))
        for r in w.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        w.migrate()
        tables = ("kill_switch", "kill_switch_stops", "kill_switch_clears")
        for t in tables:
            w.grant("GRANT MAINTAIN ON {} TO PUBLIC", t)
            w.grant("GRANT MAINTAIN ON {} TO {}", t, w.runtime)
        w.migrate()
        # no MAINTAIN grant is left on any stop table, for PUBLIC or any role (the owner's own is not listed)
        left = w.run(
            "SELECT c.relname, a.grantee FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace, "
            "aclexplode(c.relacl) a WHERE n.nspname = %s AND c.relname = ANY(%s) "
            "AND a.privilege_type = 'MAINTAIN' AND a.grantee <> c.relowner",
            (w.schema, list(tables)),
        )
        assert left == []
        for t in tables:  # the runtime login cannot LOCK any of the three, in the strongest mode
            with (
                w.as_(w.runtime, autocommit=False) as db,
                pytest.raises(errors.InsufficientPrivilege),
            ):
                db.execute(
                    sql.SQL("LOCK TABLE {}.{} IN ACCESS EXCLUSIVE MODE").format(
                        sql.Identifier(w.schema), sql.Identifier(t)
                    )
                )
        # membership in pg_maintain cannot be revoked per table: migrate refuses and names the cause
        with psycopg.connect(w.dsn, autocommit=True) as db:
            db.execute(sql.SQL("GRANT pg_maintain TO {}").format(sql.Identifier(w.runtime)))
        with pytest.raises(ConfigError, match="MAINTAIN|pg_maintain"):
            w.migrate()
    finally:
        with psycopg.connect(w.dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(w.schema)))
            for r in w.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))
