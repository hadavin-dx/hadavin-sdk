"""What the runtime login may do to the audit tables, through `migrate --runtime-role` (xreview bfix2 finding 2).

The tamper-evidence sentence of README.md and SECURITY.md holds only while the runtime login (1) does not own the
audit tables and (2) has no UPDATE, DELETE or TRUNCATE on audit_entries. Both the privilege (has_table_privilege)
and a real attempt are checked, because the append-only triggers refuse the same statements to any role: a real
attempt must fail with InsufficientPrivilege (SQLSTATE 42501, the grant), not with the trigger's text.

Two more rights are broader than they need to be today (migrate.py GRANTS: DELETE on audit_outbox, INSERT on
audit_checkpoints). Those are recorded as xfail, to pass once the migrate change of
handover/core-b/tickets/A-audit-rights.md lands. Needs HADAVIN_TEST_PG_DSN; skipped without it."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql

from hadavin_sdk.errors import ConfigError
from tests.test_stop_state_roles import World

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

LATER = "finding 2: enforced in a later migrate change"
HEAD_HASH = "h" * 64


def _teardown(w: World) -> None:
    with psycopg.connect(w.dsn, autocommit=True) as db:
        for schema in w.schemas:
            db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
        for r in w.roles:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


@pytest.fixture(scope="module", name="w")
def world():
    w = World()
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(w.schema)))
        for r in w.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        w.migrate()
        with w.admin() as db:
            db.execute(
                "INSERT INTO audit_entries (seq, at, run_id, kind, body, prev, hash, event_id) "
                "VALUES (1, 't', 'r', 'k', '{}', %s, %s, 'seed-e1') ON CONFLICT DO NOTHING",
                ("0" * 64, HEAD_HASH),
            )
            db.execute(
                "INSERT INTO audit_outbox (event_id, body) VALUES ('seed-o1', '{}') ON CONFLICT DO NOTHING"
            )
        yield w
    finally:
        _teardown(w)


def _has(w: World, table: str, priv: str) -> bool:
    with w.admin() as db:
        return db.execute(
            "SELECT has_table_privilege(%s, %s, %s)", (w.runtime, f"{w.schema}.{table}", priv)
        ).fetchone()[0]


def _attempt(w: World, statement: str, params=()):
    """Run one statement as the runtime login in a transaction that is always rolled back."""
    with w.as_(w.runtime, autocommit=False) as db:
        try:
            db.execute(statement, params)
        finally:
            db.rollback()


def test_runtime_does_not_own_the_audit_tables(w):
    owners = w.run(
        "SELECT tablename, tableowner FROM pg_tables WHERE schemaname = %s "
        "AND tablename IN ('audit_entries', 'audit_checkpoints', 'audit_outbox')",
        (w.schema,),
    )
    assert len(owners) == 3
    assert all(owner != w.runtime for _, owner in owners)


def test_runtime_privileges_on_audit_entries(w):
    assert _has(w, "audit_entries", "SELECT")
    assert _has(w, "audit_entries", "INSERT")
    for priv in ("UPDATE", "DELETE", "TRUNCATE"):
        assert not _has(w, "audit_entries", priv), priv


def test_runtime_can_append_to_audit_entries(w):
    _attempt(
        w,
        "INSERT INTO audit_entries (seq, at, run_id, kind, body, prev, hash, event_id) "
        "VALUES ((SELECT MAX(seq) + 1 FROM audit_entries), 't', 'r', 'k', '{}', %s, %s, 'rt-e2')",
        (HEAD_HASH, "g" * 64),
    )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_entries SET body = 'x' WHERE seq = 1",
        "DELETE FROM audit_entries WHERE seq = 1",
        "TRUNCATE audit_entries",
    ],
)
def test_runtime_cannot_change_audit_entries(w, statement):
    with pytest.raises(errors.InsufficientPrivilege):
        _attempt(w, statement)
    assert w.run("SELECT COUNT(*) FROM audit_entries WHERE event_id = 'seed-e1'")[0][0] == 1


@pytest.mark.xfail(reason=LATER, strict=False)
def test_runtime_has_no_delete_on_audit_outbox(w):
    assert not _has(w, "audit_outbox", "DELETE")
    with pytest.raises(errors.InsufficientPrivilege):
        _attempt(w, "DELETE FROM audit_outbox WHERE event_id = 'seed-o1'")


@pytest.mark.xfail(reason=LATER, strict=False)
def test_runtime_has_no_insert_on_audit_checkpoints(w):
    assert not _has(w, "audit_checkpoints", "INSERT")
    with pytest.raises(errors.InsufficientPrivilege):
        _attempt(
            w,
            "INSERT INTO audit_checkpoints (seq, hash, signature) VALUES (1, %s, 'planted')",
            (HEAD_HASH,),
        )


# --- migrate refuses a runtime or caps role that owns the audit tables (finding 2, third part) --------------------------

AUDIT_TABLES = ("audit_entries", "audit_checkpoints", "audit_outbox")


def _owner_of(w: World, table: str) -> str:
    return w.run(
        "SELECT tableowner FROM pg_tables WHERE schemaname = %s AND tablename = %s",
        (w.schema, table),
    )[0][0]


@pytest.mark.parametrize("who", ["runtime", "caps"])
@pytest.mark.parametrize("table", AUDIT_TABLES)
def test_migrate_refuses_a_login_that_owns_an_audit_table(w, who, table):
    """An owner can DISABLE the append-only triggers: the refusal names the role and the table."""
    role, owner = getattr(w, who), _owner_of(w, table)
    w.grant(f"ALTER TABLE {table} OWNER TO {{}}", role)
    try:
        with pytest.raises(ConfigError, match=rf"{role}: owns {table}"):
            w.migrate()
    finally:
        w.grant(f"ALTER TABLE {table} OWNER TO {{}}", owner)
    assert w.migrate() == []  # the refusal rolled back, and the restored owner passes again


@pytest.mark.parametrize("who", ["runtime", "caps"])
def test_migrate_refuses_a_login_that_is_a_member_of_the_owner_role(w, who):
    role, owner = getattr(w, who), _owner_of(w, "audit_entries")
    with w.hazard():  # a login that inherits the owner is visible to every other worker's migrate
        w.grant("GRANT {} TO {}", owner, role)
        try:
            with pytest.raises(ConfigError, match=rf"{role} is a member of {owner}"):
                w.migrate()
        finally:
            w.grant("REVOKE {} FROM {}", owner, role)
    assert w.migrate() == []


@pytest.mark.parametrize("who", ["runtime", "caps"])
def test_migrate_refuses_a_login_that_is_a_member_of_the_role_that_owns_an_audit_table(w, who):
    """Not the function owner: only the relation check of `effective_problems` can catch this one."""
    role, owner = getattr(w, who), _owner_of(w, "audit_entries")
    helper = w.new_role(f"ao_{who}", "NOLOGIN")
    w.grant("ALTER TABLE audit_entries OWNER TO {}", helper)
    w.grant("GRANT {} TO {}", helper, role)
    try:
        with pytest.raises(
            ConfigError, match=rf"{role}: is a member of {helper}, the owner of relations"
        ):
            w.migrate()
    finally:
        w.grant("REVOKE {} FROM {}", helper, role)
        w.grant("ALTER TABLE audit_entries OWNER TO {}", owner)
    assert w.migrate() == []


def test_migrate_takes_back_a_hand_grant_on_the_audit_tables(w):
    """TRIGGER and TRUNCATE can defeat the tripwires: a hand grant goes at the next run."""
    for priv in ("TRUNCATE", "TRIGGER", "DELETE", "UPDATE"):
        w.grant(f"GRANT {priv} ON TABLE audit_entries TO {{}}", w.runtime)
        # migrate re-applies the grant map first (REVOKE ALL, then the map), so the extra grant is taken back
        assert w.migrate() == []
        assert not _has(w, "audit_entries", priv)


def test_the_caps_login_holds_only_the_audit_append_and_the_cap_functions(w):
    for table, privs in (
        ("audit_entries", {"SELECT", "INSERT"}),
        ("audit_checkpoints", {"SELECT"}),
        ("audit_outbox", set()),
    ):
        for priv in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            got = w.run(
                "SELECT has_table_privilege(%s, %s, %s)", (w.caps, f"{w.schema}.{table}", priv)
            )[0][0]
            assert got is (priv in privs), (table, priv)
