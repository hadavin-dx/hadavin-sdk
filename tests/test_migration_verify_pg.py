"""`verify` against a real PostgreSQL (ticket P3a-2, section 3): the version and self-check, what a clean database gives,
and that every printed statement really removes the problem it is printed for. Every test makes its own database and its
own roles (names with a random suffix, dropped at the end); nothing here touches the database of the DSN itself. A skip is
a failed evidence run: `tests/test_migration_rules.py` checks that no test skips with the DSN set."""

from __future__ import annotations

import os
import uuid
from types import SimpleNamespace

import pytest

from tests.fixtures.dsn_skip import require_module

psycopg = require_module("psycopg")  # with the DSN set a missing driver FAILS (never a skip)
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migration_verify as v
from hadavin_sdk.store.migrate import GRANTS
from hadavin_sdk.store.migration_numbers import RECIPE_TIMEOUTS

DSN = os.environ.get("HADAVIN_TEST_PG_DSN")
needs_pg = pytest.mark.skipif(
    not DSN, reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)"
)
pytestmark = needs_pg

NAMED_KINDS = {"rt": "runtime", "po": "portal", "pu": "purge"}


@pytest.fixture
def env():
    """A scratch database with the migration role `mig` owning the schema `app`, the three named roles holding USAGE on
    it, and the made-up role names. Superuser connection in `db`."""
    tag = "vp" + uuid.uuid4().hex[:10]
    names = SimpleNamespace(
        tag=tag,
        **{k: f"{tag}_{k}" for k in ("mig", "rt", "po", "pu", "grp", "boss", "boss2", "other")},
    )
    admin = psycopg.connect(DSN, autocommit=True)
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(tag)))
    roles = [
        names.mig,
        names.rt,
        names.po,
        names.pu,
        names.grp,
        names.boss,
        names.boss2,
        names.other,
    ]
    for r in roles:
        admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(r)))
    db = psycopg.connect(make_conninfo(DSN, dbname=tag), autocommit=True)
    db.execute(sql.SQL("CREATE SCHEMA app AUTHORIZATION {}").format(sql.Identifier(names.mig)))
    for r in (names.rt, names.po, names.pu):
        db.execute(sql.SQL("GRANT USAGE ON SCHEMA app TO {}").format(sql.Identifier(r)))
    try:
        yield SimpleNamespace(db=db, n=names)
    finally:
        db.close()
        admin.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(tag))
        )
        for r in roles:
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(r)))
        admin.close()


def run_verify(env, schema="app", **kw):
    n = env.n
    named = {n.rt: "runtime", n.po: "portal", n.pu: "purge"}
    args = {
        "migration_role": n.mig, "login_role": None, "named_roles": named, "grant_map": GRANTS, "schema": schema,
        "managed_relations": [*GRANTS, "schema_migrations"], "managed_functions": [], "reviewed_definers": frozenset(),
        "limits": RECIPE_TIMEOUTS,
    }  # fmt: skip
    args.update(kw)
    return v.verify(env.db, **args)


def x(env, text, *names):
    env.db.execute(sql.SQL(text).format(*[sql.Identifier(n) for n in names]))


def test_the_running_server_is_16_or_later_and_accepted(env):
    assert env.db.info.server_version >= 160000
    assert run_verify(env) == []


def test_a_server_below_16_is_refused_with_the_plain_message(env, monkeypatch):
    real = v._fetch

    def old_server(db, text, params=None, *, named=True):
        return ((150004, "x"),) if text == v.V2_SQL else real(db, text, params, named=named)

    monkeypatch.setattr(v, "_fetch", old_server)
    with pytest.raises(ConfigError, match="needs PostgreSQL 16 or later"):
        run_verify(env)


def test_the_self_check_matches_the_running_server(env):
    got = [r[0] for r in env.db.execute(v.Q0).fetchall()]
    assert sorted(got) == sorted(v.KNOWN_ACL_COLUMNS)
    v.check_acl_columns(got)


def test_the_self_check_stops_verify_when_the_server_has_a_column_the_package_does_not_know(
    env, monkeypatch
):
    real = v._fetch

    def more(db, text, params=None, *, named=True):
        got = real(db, text, params, named=named)
        return (*got, ("pg_made_up.acl",)) if text == v.Q0 else got

    monkeypatch.setattr(v, "_fetch", more)
    with pytest.raises(ConfigError, match="does not read"):
        run_verify(env)


def test_verify_restores_the_search_path_and_leaves_nothing_behind(env):
    before = env.db.execute("SHOW search_path").fetchone()
    with env.db.transaction():
        run_verify(env)
        assert env.db.execute("SHOW search_path").fetchone() == before
        assert env.db.execute("SHOW statement_timeout").fetchone()[0] == "0"


def test_the_public_schema_with_the_server_default_passes_verify(env):
    assert run_verify(env, schema="public", migration_role="postgres") == []


def test_a_temporary_table_that_shadows_a_catalog_table_changes_nothing(env):
    with env.db.transaction():
        env.db.execute("CREATE TEMP TABLE pg_class (relname text)")
        env.db.execute("CREATE TEMP TABLE pg_auth_members (member oid)")
        assert run_verify(env) == []


def test_message_safety_names_with_newline_and_escape(env):
    n = env.n
    x(env, 'CREATE TABLE app."we\nird\x1b[2J" (id int)')
    x(env, 'ALTER TABLE app."we\nird\x1b[2J" OWNER TO {}', n.mig)
    x(env, 'GRANT SELECT ON app."we\nird\x1b[2J" TO PUBLIC')
    got = run_verify(env)
    assert [p.kind for p in got] == ["everyone"] and got[0].fix == "" and got[0].by_hand == "name"
    assert "\n" not in got[0].line() and "\x1b" not in got[0].line()
    assert v.statements_for(got) == []


def test_row_types_of_six_relation_kinds_pass_and_a_standalone_composite_type_does_not(env):
    n = env.n
    for stmt in (
        "CREATE TABLE app.t1 (id int)",
        "CREATE TABLE app.t2 (id int) PARTITION BY RANGE (id)",
        "CREATE TABLE app.t2a PARTITION OF app.t2 FOR VALUES FROM (0) TO (10)",
        "CREATE VIEW app.v1 AS SELECT 1 AS a",
        "CREATE MATERIALIZED VIEW app.m1 AS SELECT 1 AS a",
    ):
        env.db.execute(stmt)
    for rel in ("t1", "t2", "t2a", "v1", "m1"):
        kind = "MATERIALIZED VIEW" if rel == "m1" else "VIEW" if rel == "v1" else "TABLE"
        env.db.execute(
            sql.SQL(f"ALTER {kind} app.{rel} OWNER TO {{}}").format(sql.Identifier(n.mig))
        )
    assert run_verify(env) == []
    env.db.execute("CREATE TYPE app.pair AS (a int, b int)")
    x(env, "ALTER TYPE app.pair OWNER TO {}", n.mig)
    got = run_verify(env)
    assert [(p.kind, p.obj) for p in got] == [("everyone", "pair")]


def _statements_clean(env, expect_kinds_by_hand=()):
    problems = run_verify(env)
    assert problems, "the case must start with a problem"
    for stmt in v.statements_for(problems):
        env.db.execute(stmt)
    left = run_verify(env)
    assert [p for p in left if p.fix] == [], [p.line() for p in left]
    assert sorted({p.by_hand for p in left}) == sorted(set(expect_kinds_by_hand)), [
        p.line() for p in left
    ]
    return problems


def test_printed_statements_remove_every_problem_for_every_grantor_form(env):
    n = env.n
    x(env, "CREATE TABLE app.secret (id int, hidden int)")
    x(env, "ALTER TABLE app.secret OWNER TO {}", n.mig)
    # grantor = owner: a table right for everyone and for a named role; a column right
    x(env, "GRANT SELECT ON app.secret TO PUBLIC")
    x(env, "GRANT DELETE ON app.secret TO {}", n.rt)
    x(env, "GRANT SELECT (hidden) ON app.secret TO {}", n.po)
    # grantor = a grant option holder (table and column)
    x(env, "GRANT USAGE ON SCHEMA app TO {}", n.boss)
    x(env, "GRANT USAGE ON SCHEMA app TO {}", n.boss2)
    x(env, "GRANT SELECT ON app.secret TO {} WITH GRANT OPTION", n.boss)
    x(env, "GRANT SELECT (id) ON app.secret TO {} WITH GRANT OPTION", n.boss2)
    x(env, "SET ROLE {}", n.boss)
    x(env, "GRANT SELECT ON app.secret TO {}", n.pu)
    x(env, "RESET ROLE")
    x(env, "SET ROLE {}", n.boss2)
    x(env, "GRANT SELECT (id) ON app.secret TO {}", n.pu)
    x(env, "RESET ROLE")
    # a membership granted by a CREATEROLE role, a built-in role, a flag through a group, a default right
    x(env, "ALTER ROLE {} CREATEROLE", n.boss)
    x(env, "GRANT pg_monitor TO {}", n.po)
    x(env, "ALTER ROLE {} CREATEDB", n.grp)
    x(env, "GRANT {} TO {}", n.grp, n.pu)
    x(env, "ALTER DEFAULT PRIVILEGES FOR ROLE {} GRANT SELECT ON TABLES TO {}", n.mig, n.other)
    problems = _statements_clean(env)
    kinds = {p.kind for p in problems}
    assert {
        "everyone",
        "right",
        "object_grant_option",
        "built_in_role",
        "flag",
        "default_for_other",
    } <= kinds


def test_a_grant_option_from_two_grantors_is_removed_by_the_printed_statements(env):
    n = env.n
    x(env, "CREATE TABLE app.g (id int)")
    x(env, "ALTER TABLE app.g OWNER TO {}", n.mig)
    x(env, "GRANT USAGE ON SCHEMA app TO {}", n.boss)
    x(env, "GRANT USAGE ON SCHEMA app TO {}", n.boss2)
    x(env, "GRANT SELECT ON app.g TO {} WITH GRANT OPTION", n.boss)
    x(env, "GRANT SELECT ON app.g TO {} WITH GRANT OPTION", n.boss2)
    x(env, "SET ROLE {}", n.boss2)
    x(env, "GRANT SELECT ON app.g TO {} WITH GRANT OPTION", n.boss)
    x(env, "RESET ROLE")
    x(env, "SET ROLE {}", n.boss)
    x(env, "GRANT SELECT ON app.g TO {}", n.other)
    x(env, "RESET ROLE")
    problems = _statements_clean(env)
    assert len([p for p in problems if p.kind == "other_grantee" and p.role == n.boss]) >= 1


def test_a_named_role_in_pg_monitor_prints_exactly_one_statement_verify(env):
    n = env.n
    x(env, "GRANT pg_monitor TO {}", n.rt)
    problems = run_verify(env)
    assert {p.kind for p in problems} == {"built_in_role"} and len(problems) == 4
    assert v.statements_for(problems) == [
        f'REVOKE "pg_monitor" FROM "{n.rt}" GRANTED BY "postgres";'
    ]
    _statements_clean(env)


def test_a_membership_granted_by_a_createrole_role_is_removed_by_the_printed_statement(env):
    n = env.n
    x(env, "ALTER ROLE {} CREATEROLE", n.boss)
    x(env, "GRANT {} TO {} WITH ADMIN OPTION", n.grp, n.boss)
    env.db.execute(
        sql.SQL("GRANT {} TO {} GRANTED BY {}").format(
            sql.Identifier(n.grp), sql.Identifier(n.rt), sql.Identifier(n.boss)
        )
    )
    x(env, "ALTER ROLE {} CREATEDB", n.grp)
    problems = _statements_clean(env)
    assert any(p.kind == "flag" for p in problems)


def test_the_database_owner_membership_is_a_by_hand_line(env):
    n = env.n
    x(env, "ALTER DATABASE {} OWNER TO {}", n.tag, n.rt)
    problems = run_verify(env)
    hand = [p for p in problems if p.by_hand == "database_owner"]
    assert hand and all(p.fix == "" for p in hand)
    assert "ALTER DATABASE" in hand[0].line()


def test_a_left_over_object_owned_by_a_named_role_is_found(env):
    n = env.n
    x(env, "CREATE TABLE app.mine (id int)")
    x(env, "ALTER TABLE app.mine OWNER TO {}", n.pu)
    got = run_verify(env)
    assert any(p.kind == "owns" and p.role == n.pu for p in got)
    assert (
        any(p.kind == "foreign_owner" for p in got) is False
    )  # `mine` is not a name of the grant map
