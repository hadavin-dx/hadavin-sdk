"""K5-core round 10, M2 (least privilege of the runtime and purge roles), on a real Postgres. Needs
HADAVIN_TEST_PG_DSN (CI: the postgres service); skipped without it."""

from __future__ import annotations

import os
import uuid

import pytest

from hadavin_sdk.config import ConfigError
from tests.contracts.kinds.store_postgres import PURGE_DSN, pg_schema

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


def _connect(dsn):
    import psycopg

    return psycopg.connect(dsn, autocommit=True)


def _denied(dsn, statement):
    import psycopg

    with _connect(dsn) as db, pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(statement)


def test_the_purge_role_can_read_only_the_columns_its_delete_needs():
    for runtime in pg_schema(runtime=True):
        purge = PURGE_DSN[runtime]
        with _connect(purge) as db:
            db.execute("SELECT run_id, updated_at FROM redaction_maps")
            db.execute("SELECT call_id, run_id, created_at FROM tool_calls")
            db.execute("SELECT run_id, state, updated_at FROM runs")
        for statement in (
            "SELECT mapping FROM redaction_maps",  # the stored originals
            "SELECT output FROM tool_calls",  # a stored tool result
            "SELECT * FROM runs",
            "SELECT * FROM plans",
            "SELECT * FROM audit_entries",
            "SELECT * FROM approval_decisions",
            "SELECT * FROM gate_decisions",
        ):
            _denied(purge, statement)


def test_the_purge_role_cannot_write_or_truncate_anything_but_delete_two_tables():
    for runtime in pg_schema(runtime=True):
        purge = PURGE_DSN[runtime]
        for statement in (
            "UPDATE runs SET state = 'x'",
            "DELETE FROM runs",
            "DELETE FROM plans",
            "DELETE FROM approval_requests",
            "DELETE FROM kill_switch",
            "INSERT INTO tool_calls (call_id) VALUES ('x')",
            "UPDATE redaction_maps SET updated_at = now()",
            "TRUNCATE tool_calls",
            "TRUNCATE redaction_maps",
        ):
            _denied(purge, statement)
        with _connect(purge) as db:
            db.execute("DELETE FROM tool_calls")  # the one thing it exists to do
            db.execute("DELETE FROM redaction_maps")


def test_the_runtime_role_cannot_delete_or_truncate_evidence():
    for runtime in pg_schema(runtime=True):
        for statement in (
            "DELETE FROM redaction_maps",
            "DELETE FROM tool_calls",
            "TRUNCATE redaction_maps",
            "TRUNCATE tool_calls",
        ):
            _denied(runtime, statement)


# --- the effective-privilege assertion: whatever the route, more than the map is refused -------------------------------------------------


def _prepared():
    """A migrated schema with a runtime and a purge role that have NOT been granted yet. Yields (admin DSN,
    scoped DSN, runtime role, purge role, run-migrate callable)."""
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.migrate import migrate

    dsn = os.environ["HADAVIN_TEST_PG_DSN"]
    schema, rt, pu = (f"{p}_{uuid.uuid4().hex[:10]}" for p in ("t", "rt", "pu"))
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        for role in (rt, pu):
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(role)))
    scoped = make_conninfo(dsn, options=f"-c search_path={schema}")
    migrate(scoped)
    try:
        yield dsn, schema, rt, pu, lambda: migrate(scoped, runtime_role=rt, purge_role=pu)
    finally:
        with psycopg.connect(dsn, autocommit=True) as db:
            for role in (rt, pu):
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_the_grant_map_alone_passes_the_assertion():
    for _dsn, _schema, _rt, _pu, run in _prepared():
        assert run() == []  # already migrated: only the grants and the assertion run


def test_a_privilege_inherited_from_another_role_is_refused():
    for dsn, schema, rt, _pu, run in _prepared():
        extra = f"extra_{uuid.uuid4().hex[:8]}"
        with _connect(dsn) as db:
            db.execute(f'CREATE ROLE "{extra}"')
            db.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO "{extra}"')
            db.execute(f'GRANT DELETE ON "{schema}".tool_calls TO "{extra}"')
            db.execute(f'GRANT "{extra}" TO "{rt}"')
        try:
            with pytest.raises(
                ConfigError, match=r"runtime role holds more than the grant map.*DELETE tool_calls"
            ):
                run()
        finally:
            with _connect(dsn) as db:
                db.execute(f'DROP OWNED BY "{extra}"')
                db.execute(f'DROP ROLE "{extra}"')


def test_a_public_grant_on_a_relation_outside_the_map_is_refused():
    for dsn, schema, _rt, _pu, run in _prepared():
        with _connect(dsn) as db:
            db.execute(f'GRANT SELECT ON "{schema}".schema_migrations TO PUBLIC')
        with pytest.raises(ConfigError, match="schema_migrations"):
            run()


def test_create_on_the_schema_is_refused_for_the_purge_role():
    for dsn, schema, _rt, pu, run in _prepared():
        with _connect(dsn) as db:
            db.execute(f'GRANT CREATE ON SCHEMA "{schema}" TO "{pu}"')
        with pytest.raises(ConfigError, match="can CREATE in schema"):
            run()


def test_a_superuser_as_the_purge_role_is_refused():
    for dsn, _schema, _rt, pu, run in _prepared():
        with _connect(dsn) as db:
            db.execute(f'ALTER ROLE "{pu}" SUPERUSER')
        with pytest.raises(ConfigError, match="superuser|members of each other"):
            run()
