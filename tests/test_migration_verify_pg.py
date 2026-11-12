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
    me = env.db.execute("SELECT current_user").fetchone()[
        0
    ]  # the cluster's own superuser, whatever it is called
    assert run_verify(env, schema="public", migration_role=me) == []


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


def _recorded_grantor(db, group: str, member: str) -> str:
    """The grantor the server recorded for a membership (Issue 3 of round 3 on 3d): read from `pg_auth_members`, not
    assumed to be the login that ran the GRANT (that is the bootstrap superuser only on a cluster set up that way)."""
    row = db.execute(
        "SELECT pg_catalog.pg_get_userbyid(m.grantor) FROM pg_catalog.pg_auth_members m "
        "WHERE m.roleid = %s::pg_catalog.regrole AND m.member = %s::pg_catalog.regrole",
        (group, member),
    ).fetchone()
    assert row is not None, f"no membership of {member} in {group} is recorded"
    return row[0]


def test_a_named_role_in_pg_monitor_prints_exactly_one_statement(env):
    n = env.n
    x(env, "GRANT pg_monitor TO {}", n.rt)
    problems = run_verify(env)
    assert {p.kind for p in problems} == {"built_in_role"} and len(problems) == 4
    grantor = _recorded_grantor(env.db, "pg_monitor", n.rt)
    assert v.statements_for(problems) == [
        f'REVOKE "pg_monitor" FROM "{n.rt}" GRANTED BY "{grantor}";'
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


def test_an_object_whose_access_list_is_empty_is_still_judged_for_owner_and_definer(env):
    """Issue 11 (round 2 of 3c, N5). A hostile file revokes everything from the object's owner and from everyone: the
    access list is then EMPTY (not null), `aclexplode` gives no row, and an object read only through its access list
    would be invisible. The probe on the old code showed it WAS invisible to the unreviewed-definer and the foreign-owner
    rules; Q2 now keeps such an object as one row with no right (`privilege_type` is null)."""
    n = env.n
    x(env, "CREATE FUNCTION app.sneaky() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'")
    x(env, "ALTER FUNCTION app.sneaky() OWNER TO {}", n.mig)
    x(env, "REVOKE ALL ON FUNCTION app.sneaky() FROM PUBLIC, {}", n.mig)
    table = next(iter(GRANTS))
    x(env, "CREATE TABLE app.{} (id int)", table)
    x(env, "ALTER TABLE app.{} OWNER TO {}", table, n.other)
    x(env, "REVOKE ALL ON TABLE app.{} FROM PUBLIC, {}", table, n.other)
    acl = env.db.execute("SELECT proacl::text FROM pg_proc WHERE proname = 'sneaky'").fetchone()[0]
    assert acl == "{}", "the made-up function has an empty access list"
    got = run_verify(env)
    assert any(p.kind == "definer_unreviewed" and p.obj == "sneaky" for p in got), got
    assert any(p.kind == "foreign_owner" and p.obj == table for p in got), got
    assert not any(p.kind == "everyone" for p in got), "an empty list is not a right for everyone"


# --- `migrate()` on a real server: the check after the commit and the commit itself (ticket P3a-2, 7.6) ------------------
# Each test runs `migrate` (through `cli.main` when it checks an exit code) in a fresh scratch schema. `mrun` wraps
# `store.migrate.connect`: it counts the calls (1 = the run, 2 = the check after the commit) and lets a test act just
# before the second connection is handed over. No test returns before its first `migrate` call.

import threading
import time

from psycopg import errors as pge
from psycopg.conninfo import conninfo_to_dict

from hadavin_sdk import cli
from hadavin_sdk.store import migrate as mig
from tests.fixtures import migration_role as helper

REAL_FILES = [p.stem for p in mig._migration_files()]


@pytest.fixture
def mrun(monkeypatch, tmp_path):
    """A scratch schema (dsn scoped to it) and a recorder around `mig.connect`."""
    schema = f"hadavin_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(DSN, autocommit=True) as adm:
        adm.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    dsn = make_conninfo(DSN, options=f"-c search_path={schema}")
    state = SimpleNamespace(
        dsn=dsn, schema=schema, calls=0, before_call={}, after_call={}, tmp=tmp_path
    )
    inner = mig.connect  # the swap to a plain role (conftest) is already in place

    def wrapped(d, **kw):
        state.calls += 1
        hook = state.before_call.get(state.calls)
        if hook is not None:
            hook()
        conn = inner(d, **kw)
        after = state.after_call.get(state.calls)
        if after is not None:
            after(conn)
        return conn

    monkeypatch.setattr(mig, "connect", wrapped)
    try:
        yield state
    finally:
        with psycopg.connect(DSN, autocommit=True) as adm:
            adm.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))


def _super(text: str, *idents: str) -> None:
    with psycopg.connect(DSN, autocommit=True) as adm:
        adm.execute(sql.SQL(text).format(*[sql.Identifier(i) for i in idents]))


def _ledger_of(dsn) -> list[str]:
    with psycopg.connect(dsn, autocommit=True) as db:
        if db.execute("SELECT to_regclass('schema_migrations')").fetchone()[0] is None:
            return []
        return [r[0] for r in db.execute("SELECT version FROM schema_migrations ORDER BY 1")]


def _cli_migrate(cfg_dir, monkeypatch, dsn, *extra):
    """Config with the postgres store, the migration DSN in the environment, then `cli.main(["migrate"])`."""
    import yaml

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", dsn)
    return cli.main(["--config", str(cfg_dir), "migrate", *extra])


def _plant(monkeypatch, tmp_path, name: str, text: str) -> None:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    files = mig._migration_files() + [p]
    monkeypatch.setattr(mig, "_migration_files", lambda: files)


def _map_table() -> str:
    return next(iter(GRANTS))


def test_after_commit_a_grant_gives_exit_5_and_the_statements_repair_it(
    mrun, cfg_dir, monkeypatch, capsys
):
    table = _map_table()
    mrun.before_call[2] = lambda: _super(
        "GRANT SELECT ON TABLE {}.{} TO PUBLIC", mrun.schema, table
    )
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 5
    out, err = capsys.readouterr()
    assert err.startswith(
        "The files are applied and committed; the database is over-privileged now; run these statements; run "
        "migrate again to re-check."
    )
    assert not any(line.startswith("applied") for line in (out + err).splitlines())
    statements = [ln for ln in out.splitlines() if ln and not ln.startswith("--")]
    assert statements and all(ln.endswith(";") for ln in statements), out
    assert "over-privileged" not in out, (
        "the message goes to standard error, the statements to standard output"
    )
    assert _ledger_of(mrun.dsn) == REAL_FILES
    with psycopg.connect(DSN, autocommit=True) as adm:
        for st in statements:
            adm.execute(st)
    mrun.before_call.clear()
    assert mig.migrate(mrun.dsn) == []


@pytest.mark.parametrize("call", [1, 2], ids=["step_2", "step_6"])
def test_a_connection_lost_while_the_check_runs_before_the_commit_gives_exit_2(
    call, mrun, cfg_dir, monkeypatch, capsys
):
    """Round 2 of 3c, M4 and C1. A second session ends the run's backend (`pg_terminate_backend`: 57P01) just before the
    first (step 2) or the second (step 6) `verify` of the run reads anything: the check raises a driver error before the
    commit. That is exit 2 "kept nothing, could not run", never exit 3; the ledger is empty; the same run on a healthy
    connection then applies every file. Killed by: V67 and V68."""
    real = mig.verify
    seen = {"n": 0}

    def ends_the_session_first(db, **kw):
        seen["n"] += 1
        if seen["n"] == call:
            with psycopg.connect(DSN, autocommit=True) as adm:
                adm.execute("SELECT pg_terminate_backend(%s)", (db.info.backend_pid,))
            time.sleep(0.2)  # the backend has left when the first read goes out
        return real(db, **kw)

    monkeypatch.setattr(mig, "verify", ends_the_session_first)
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
    out, err = capsys.readouterr()
    assert err.startswith("refused: migrate stopped and kept nothing"), err
    assert "the check of the rights could not run" in err and "Run migrate again" in err
    assert "failed:" not in err and out == ""
    assert _ledger_of(mrun.dsn) == []
    monkeypatch.setattr(mig, "verify", real)
    assert mig.migrate(mrun.dsn) == REAL_FILES


# Round 3 of 3d, Issue 2. Every step before the commit, not only the two `verify` calls, ends in exit 2 when the driver fails.
_STEPS_BEFORE_THE_COMMIT = [
    "_take_the_lock",
    "_refuse_privileged_role",
    "_refuse_foreign_owned",
    "_read_back",
    "_check_read_back",
    "_recheck_roles",
    "_apply_grants",
    "_revoke_default_execute",
]


@pytest.mark.parametrize("target", _STEPS_BEFORE_THE_COMMIT)
def test_a_connection_lost_at_any_step_before_the_commit_gives_exit_2_and_keeps_nothing(
    target, mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 2 of round 3 on 3d. A second session ends the run's backend just before one named step of `migrate` reads or
    writes (the lock, the privileged-role check, the owner check, the read-back, the read-back after a file, the role
    re-check, the grants, the default-EXECUTE revoke). Each gives exit 2 "kept nothing", never exit 3; the ledger is
    empty; the same run on a healthy connection then applies every file. Killed by: V80 and V81."""
    real = getattr(mig, target)
    seen = {"n": 0}

    def ends_the_session_first(db, *a, **kw):
        seen["n"] += 1
        if seen["n"] == 1:
            with psycopg.connect(DSN, autocommit=True) as adm:
                adm.execute("SELECT pg_terminate_backend(%s)", (db.info.backend_pid,))
            time.sleep(0.2)
        return real(db, *a, **kw)

    runtime = "hadavin_test_rt_" + uuid.uuid4().hex[:8]
    from tests import test_migration_postgres as tp

    tp._create_roles(runtime)
    try:
        monkeypatch.setattr(mig, target, ends_the_session_first)
        assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn, "--runtime-role", runtime) == 2
        _out, err = capsys.readouterr()
        assert seen["n"] >= 1, f"{target} was never called: the cell tests nothing"
        assert err.startswith("refused: migrate stopped and kept nothing"), err
        assert "Run migrate again" in err and "failed:" not in err
        assert _ledger_of(mrun.dsn) == []
        monkeypatch.setattr(mig, target, real)
        assert mig.migrate(mrun.dsn, runtime_role=runtime) == REAL_FILES
    finally:
        tp._drop_roles(runtime)


# Issue 7 of round 14: the statements that `migrate` sends itself and that no named function wraps. Each is the first
# statement of its kind on the run's connection that holds the marker text.
_INLINE_STATEMENTS = [
    RECIPE_TIMEOUTS[0],  # the recipe limits
    "server_version_num",  # the version read
    "SELECT current_schema()",  # the identity read
    "CREATE TABLE IF NOT EXISTS schema_migrations",  # the ledger table
    "SELECT version FROM schema_migrations",  # the ledger read
    "INSERT INTO schema_migrations",  # the ledger write after a file
    "SET CONSTRAINTS ALL IMMEDIATE",  # step 5
]


@pytest.mark.parametrize("marker", _INLINE_STATEMENTS)
def test_a_connection_lost_at_a_statement_the_runner_sends_itself_gives_exit_2_and_keeps_nothing(
    marker, mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 7 of round 14. The earlier test ends the session before each named step; this one ends it just before one of
    the statements that `migrate` sends inline (the limits, the version read, the identity read, the ledger table, the
    ledger read, the ledger write, step 5). Each gives exit 2 "kept nothing", never exit 3 and never the wording of a
    failed deferred check; the ledger is empty. Together with the named steps this is the whole list that the CHANGELOG
    means by "every step before the commit". Killed by: V80 (every cell) and V90 (the step-5 wording)."""
    seen = {"conn": None, "done": False}
    mrun.after_call[1] = lambda conn: seen.update(conn=conn)
    real = psycopg.Connection.execute

    def ends_the_session_first(self, query, *a, **kw):
        if not seen["done"] and self is seen["conn"] and marker in str(query):
            seen["done"] = True
            with psycopg.connect(DSN, autocommit=True) as adm:
                adm.execute("SELECT pg_terminate_backend(%s)", (self.info.backend_pid,))
            time.sleep(0.2)
        return real(self, query, *a, **kw)

    monkeypatch.setattr(psycopg.Connection, "execute", ends_the_session_first)
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
    _out, err = capsys.readouterr()
    assert seen["done"], f"no statement with {marker!r} was sent: the cell tests nothing"
    assert err.startswith("refused: migrate stopped and kept nothing"), err
    assert "Run migrate again" in err and "failed:" not in err
    assert "a deferred check or trigger failed" not in err, err
    monkeypatch.setattr(psycopg.Connection, "execute", real)
    assert _ledger_of(mrun.dsn) == []
    assert mig.migrate(mrun.dsn) == REAL_FILES


def test_a_connection_lost_at_any_read_of_pg_roles_gives_exit_2_and_keeps_nothing(
    mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 7 of round 14, the `pg_roles` marker. The independent evidence run injected a lost connection at the second
    statement that names `pg_roles` and got a raw `OperationalError` (exit 3). Traced now: that statement is the TEST
    helper's own (`plain_role_connect` runs `ensure_plain_role` on its own connection before `migrate` has one), not a
    statement of `migrate`. Here the injection is limited to the run's own connection (the first one `migrate` opens,
    after the helper has finished), so every read of `pg_roles` that `migrate` sends on it is counted and each, one at a
    time, is made to fail: every one gives exit 2, nothing kept. There is no hole in the runner for this marker."""
    seen = {"conn": None, "count": 0, "fail_at": 0, "hit": False}
    mrun.after_call[1] = lambda conn: seen.update(conn=conn)
    real = psycopg.Connection.execute

    def counts_or_fails(self, query, *a, **kw):
        if self is seen["conn"] and "pg_roles" in str(query):
            seen["count"] += 1
            if seen["count"] == seen["fail_at"]:
                seen["hit"] = True
                raise psycopg.OperationalError("made-up: connection lost")
        return real(self, query, *a, **kw)

    monkeypatch.setattr(psycopg.Connection, "execute", counts_or_fails)
    assert mig.migrate(mrun.dsn) == REAL_FILES  # counting run
    total = seen["count"]
    assert total >= 8, f"only {total} reads of pg_roles were counted: the cell tests too little"
    with psycopg.connect(DSN, autocommit=True) as adm:
        adm.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(mrun.schema)))
        adm.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(mrun.schema)))
    for n in range(1, total + 1):
        mrun.calls = 0
        seen.update(count=0, fail_at=n, hit=False)
        assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2, f"read {n} of {total}"
        _out, err = capsys.readouterr()
        assert seen["hit"], f"read {n} was never reached"
        assert err.startswith("refused: migrate stopped and kept nothing"), (n, err)
        assert "failed:" not in err, (n, err)
        assert _ledger_of(mrun.dsn) == [], n
    seen["fail_at"] = 0
    monkeypatch.setattr(psycopg.Connection, "execute", real)
    assert mig.migrate(mrun.dsn) == REAL_FILES


def test_a_failure_to_connect_at_the_start_is_the_one_exit_3_before_any_step(
    mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 7 of round 14, `connect()` and its `SET TIME ZONE` sit outside the steps: a connection that cannot be made
    at all is exit 3 ("failed"), nothing ran and nothing was kept. This is pinned as the intended outcome (the claim
    "exit 2 at every step" starts after the connection is open). The test passes on the old code too: it pins a
    behaviour that was already right and has no branch of its own to plant a fault in."""

    def cannot_connect():
        raise psycopg.OperationalError("made-up: the server is not reachable")

    mrun.before_call[1] = cannot_connect
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 3
    _out, err = capsys.readouterr()
    assert err.startswith("failed: OperationalError"), err
    assert "made-up: the server" not in err
    assert _ledger_of(mrun.dsn) == []


def test_an_error_of_the_runner_after_the_last_file_is_never_taken_as_the_files_own(
    mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 7 of round 14. After the last file the runner's own statements run (the grants, the default-EXECUTE revoke).
    An error with a SQLSTATE that a file's text could also cause (here 42704, a missing object) must not be left raw
    because the flag "a file is running" was never cleared: it is the runner's, so exit 2, nothing kept. Killed by: V91."""

    def a_missing_object(db, *a, **kw):
        raise pge.UndefinedObject("made-up: a role that is not there")

    monkeypatch.setattr(mig, "_revoke_default_execute", a_missing_object)
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
    _out, err = capsys.readouterr()
    assert err.startswith("refused: migrate stopped and kept nothing"), err
    assert "42704" in err and "failed:" not in err, err
    assert _ledger_of(mrun.dsn) == []


def test_a_connection_lost_while_a_file_runs_is_refused_with_exit_2(
    mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 2: a connection that ends while a file runs (the file's function ends its own backend) is not the file's own
    error: it is refused with exit 2, nothing kept. Killed by: V81 (every error while a file runs is left raw)."""
    with psycopg.connect(
        DSN, autocommit=True
    ) as adm:  # the bodies hold `;`, which the text rules read as a statement end
        helper.ensure_plain_role(adm)
        for name, body in (
            (
                "hadavin_test_bye",
                "PERFORM pg_terminate_backend(pg_backend_pid()); PERFORM pg_sleep(1); RETURN 1;",
            ),
        ):
            adm.execute(
                sql.SQL("CREATE FUNCTION {}.{}() RETURNS int LANGUAGE plpgsql AS {}").format(
                    sql.Identifier(mrun.schema),
                    sql.Identifier(name),
                    sql.Literal(f"BEGIN {body} END"),
                )
            )
    _plant(monkeypatch, mrun.tmp, "0006_bye.sql", "SELECT hadavin_test_bye();\n")
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
    _out, err = capsys.readouterr()
    assert err.startswith("refused: migrate stopped and kept nothing"), err
    assert "applying 0006_bye.sql" in err and "57P01" in err, err
    assert _ledger_of(mrun.dsn) == []


def test_a_files_own_error_is_raised_as_it_is(mrun, monkeypatch):
    """The error of the text of a file keeps its own words (here a division by zero) and is not turned into the "database
    returned an error" refusal; nothing is kept. Killed by: V81 and V82."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
        adm.execute(
            sql.SQL(
                "CREATE FUNCTION {}.hadavin_test_zero() RETURNS int LANGUAGE plpgsql AS 'BEGIN RETURN 1/0; END'"
            ).format(sql.Identifier(mrun.schema))
        )
    _plant(monkeypatch, mrun.tmp, "0006_zero.sql", "SELECT hadavin_test_zero();\n")
    try:
        mig.migrate(mrun.dsn)
        raised = None
    except (ConfigError, psycopg.Error) as e:  # a wrong type is a failed assert below
        raised = e
    assert isinstance(raised, pge.DivisionByZero), (
        f"raised {type(raised).__name__}, not the file's own error"
    )
    assert _ledger_of(mrun.dsn) == []


def test_a_bug_before_the_commit_stays_loud_and_a_files_own_error_stays_its_own(mrun, monkeypatch):
    """A `RuntimeError` is not a driver error: it is raised as it is. A syntax error of a file is the file's own error and
    is not turned into the "database returned an error" refusal (its text is what the person needs). Killed by: V81."""

    def a_bug(db, *a, **kw):
        raise RuntimeError("a bug in the runner")

    monkeypatch.setattr(mig, "_refuse_foreign_owned", a_bug)
    with pytest.raises(RuntimeError, match="a bug in the runner"):
        mig.migrate(mrun.dsn)
    monkeypatch.undo()
    assert mig._is_a_files_own_error(pge.SyntaxError("x"), _UsableConnection()) is True
    assert mig._is_a_files_own_error(pge.AdminShutdown("x"), _UsableConnection()) is False
    assert mig._is_a_files_own_error(pge.QueryCanceled("x"), _UsableConnection()) is False
    assert mig._is_a_files_own_error(psycopg.OperationalError("lost"), _UsableConnection()) is False


def test_a_saved_transaction_timeout_stops_the_check_and_migrate_refuses_with_exit_2(
    mrun, cfg_dir, monkeypatch, capsys
):
    """Round 2 of 3c, M4. PostgreSQL 17 and later have `transaction_timeout`, and `verify` does not neutralise it (it
    cannot: it ends the session). On a server below 17 the setting does not exist, so below 17 this test is a VISIBLE SKIP naming "UNRUN: PostgreSQL 17 only" (three tests in this
    file need 17: this one, the next one and the one for a timeout inside a file). On 17 the setting is applied inside
    the run just before the first `verify` (a role-saved value could end the run anywhere, including inside a file,
    which is not the path under test) and a later statement runs into it. Killed by: V67."""
    if mrun_server_version() < 170000:
        pytest.skip(
            "UNRUN: PostgreSQL 17 only (`transaction_timeout` does not exist below 17); the PostgreSQL 16 fact it rests on "
            "is pinned by test_the_server_version_decides_whether_a_role_can_save_a_transaction_timeout"
        )
    real = mig.verify
    seen = {"n": 0}

    def times_out_first(db, **kw):
        seen["n"] += 1
        if seen["n"] == 1:
            db.execute("SET LOCAL transaction_timeout = '1ms'")
            time.sleep(0.05)
        return real(db, **kw)

    monkeypatch.setattr(mig, "verify", times_out_first)
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
    _out, err = capsys.readouterr()
    assert err.startswith("refused: migrate stopped and kept nothing"), err
    assert "the check of the rights could not run" in err
    assert _ledger_of(mrun.dsn) == []


def test_the_server_version_decides_whether_a_role_can_save_a_transaction_timeout(mrun):
    """The version fact the three PostgreSQL 17 tests rest on (moved here from the old PostgreSQL 16 branches of two of them,
    so that those are visible skips and the fact is a test of its own that runs on every server). Below 17,
    `transaction_timeout` does not exist: no role can save it. On 17 and later a role can save it (the value is reset
    here). On both, a clean `migrate` then runs through."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
        role = sql.Identifier(helper.PLAIN_ROLE)
        for value in ("1s", "1ms"):
            save = sql.SQL("ALTER ROLE {} SET transaction_timeout = {}").format(
                role, sql.Literal(value)
            )
            if mrun_server_version() >= 170000:
                adm.execute(save)
                adm.execute(sql.SQL("ALTER ROLE {} RESET transaction_timeout").format(role))
            else:
                with pytest.raises(pge.UndefinedObject, match="transaction_timeout"):
                    adm.execute(save)
    assert mig.migrate(mrun.dsn) == REAL_FILES


def test_a_role_saved_transaction_timeout_gives_exit_2_wherever_it_strikes(
    mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 2 of round 3 on 3d, the case that `SET LOCAL` before the first `verify` does not cover: the value is saved
    for the migration role (`ALTER ROLE ... SET transaction_timeout`), so it counts from BEGIN and can end the session at
    the lock, the version read, a refusal check, a file's read-back or the grants. On PostgreSQL 17 and later the run ends
    with exit 2 and keeps nothing, whichever step it was. THIS TEST IS UNRUN ON ANY SERVER HERE (only PostgreSQL 16 is
    installed): below 17 it is a visible skip; CI is configured to run it on 17.10 (not yet seen).
    Killed by: V80."""
    if mrun_server_version() < 170000:
        pytest.skip(
            "UNRUN: PostgreSQL 17 only (`transaction_timeout` does not exist below 17); the PostgreSQL 16 fact it rests on "
            "is pinned by test_the_server_version_decides_whether_a_role_can_save_a_transaction_timeout"
        )
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
        adm.execute(
            sql.SQL("ALTER ROLE {} SET transaction_timeout = '1ms'").format(
                sql.Identifier(helper.PLAIN_ROLE)
            )
        )
    try:
        assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
        _out, err = capsys.readouterr()
        assert err.startswith("refused: migrate stopped and kept nothing"), err
        assert "failed:" not in err
    finally:
        with psycopg.connect(DSN, autocommit=True) as adm:
            adm.execute(
                sql.SQL("ALTER ROLE {} RESET transaction_timeout").format(
                    sql.Identifier(helper.PLAIN_ROLE)
                )
            )
    assert _ledger_of(mrun.dsn) == []
    assert mig.migrate(mrun.dsn) == REAL_FILES


def test_a_session_ended_by_the_idle_in_transaction_timeout_while_a_file_runs_is_refused_with_exit_2(
    mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 1 of round 14 (batch 4), the class "the server ends the session, not the file", shown on PostgreSQL 16. The
    role saves `idle_in_transaction_session_timeout` (SQLSTATE 25P03, a FATAL error of class 25 that ends the session).
    The runner waits longer than the limit just before the first file runs, so the file's statement is the first one to
    meet the dead session. That is not the file's own error: exit 2, nothing kept, never the raw driver error (exit 3).
    The same class on PostgreSQL 17 is `transaction_timeout` (25P04), see the PG17-only test below. This real-server test
    does NOT discriminate V88 or V89 (the check that the connection is still usable also catches a dead session, so with
    the two codes taken out of the list the run still ends in exit 2); the two unit tests below kill them: V88 by
    `test_the_classifier_knows_which_sqlstates_are_not_a_files_own`, V89 by
    `test_the_classifier_never_calls_an_error_on_a_dead_connection_the_files_own`. What THIS test proves: on a real
    server the end of the session is exit 2 and the ledger stays empty."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
        adm.execute(
            sql.SQL("ALTER ROLE {} SET idle_in_transaction_session_timeout = '200ms'").format(
                sql.Identifier(helper.PLAIN_ROLE)
            )
        )
    real = mig._refuse_unusual_strings
    seen = {"n": 0}

    def waits(saved):
        seen["n"] += 1
        time.sleep(
            1.5
        )  # 7.5 times the limit (round 15: the margin was 4 times): the server ends the session while the runner thinks
        return real(saved)

    monkeypatch.setattr(mig, "_refuse_unusual_strings", waits)
    try:
        assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
        _out, err = capsys.readouterr()
        assert seen["n"] == 1, "the wait never ran: the cell tests nothing"
        assert err.startswith("refused: migrate stopped and kept nothing"), err
        assert "25P03" in err, f"the refusal must name the session-ending code 25P03: {err}"
        assert "failed:" not in err, (
            f"a lost session must not be reported as a failure of the file: {err}"
        )
        assert _ledger_of(mrun.dsn) == []
    finally:
        with psycopg.connect(DSN, autocommit=True) as adm:
            adm.execute(
                sql.SQL("ALTER ROLE {} RESET idle_in_transaction_session_timeout").format(
                    sql.Identifier(helper.PLAIN_ROLE)
                )
            )
    monkeypatch.setattr(mig, "_refuse_unusual_strings", real)
    assert mig.migrate(mrun.dsn) == REAL_FILES


@pytest.mark.parametrize(
    ("code", "own"),
    [
        ("25P03", False),  # idle-in-transaction timeout (PostgreSQL 16 errcodes.txt)
        (
            "25P04",
            False,
        ),  # transaction timeout (PostgreSQL 17; the code is psycopg's `TransactionTimeout`)
        (
            "25001",
            True,
        ),  # active_sql_transaction: a file's own error (e.g. VACUUM inside the transaction)
        ("25P02", True),  # in_failed_sql_transaction: a file's own error
        ("42601", True),
        ("22012", True),
        ("23505", True),
        ("08006", False),
        ("53300", False),
        ("57P01", False),
        ("58030", False),
        ("XX000", False),
    ],
)
def test_the_classifier_knows_which_sqlstates_are_not_a_files_own(code, own):
    """Issue 1 of round 14: the one classifier. A usable connection is checked in the next test; here the connection is
    a stand-in that is usable, so only the SQLSTATE decides. Class 25 is not excluded as a whole (25001 and 25P02 are a
    file's own errors); the two session-ending codes are named. Killed by: V88."""
    e = psycopg.errors.lookup(code)("made-up")
    got = mig._is_a_files_own_error(e, _UsableConnection())
    assert got is own, (
        f"{code} must {'be' if own else 'not be'} a file's own error on a usable connection; the classifier said {got}"
    )


class _UsableConnection:
    closed = False
    broken = False

    class info:
        transaction_status = psycopg.pq.TransactionStatus.INERROR


@pytest.mark.parametrize("state", ["closed", "broken", "unknown_status"])
def test_the_classifier_never_calls_an_error_on_a_dead_connection_the_files_own(state):
    """Issue 1 of round 14: whatever the SQLSTATE says (here a syntax error, which would be a file's own), an error that
    leaves the connection unusable is not the file's own: the session is gone. Killed by: V89."""
    conn = _UsableConnection()
    if state == "closed":
        conn.closed = True
    elif state == "broken":
        conn.broken = True
    else:

        class info:
            transaction_status = psycopg.pq.TransactionStatus.UNKNOWN

        conn.info = info
    assert mig._is_a_files_own_error(pge.SyntaxError("x"), conn) is False, (
        f"an error on a {state} connection must not be a file's own error (the session is gone)"
    )


def test_a_real_files_own_error_leaves_the_connection_usable_and_is_the_files_own(mrun):
    """Issue 1 of round 14: on a real server the connection after a file's own error (a division by zero) is usable, and
    after a session-ending termination it is not. Both measured, so the stand-ins above say what the driver says."""
    with psycopg.connect(DSN, autocommit=True) as c:
        with pytest.raises(pge.DivisionByZero) as own, c.transaction():
            c.execute("SELECT 1/0")
        assert mig._is_a_files_own_error(own.value, c) is True
    c = psycopg.connect(DSN, autocommit=True)
    with psycopg.connect(DSN, autocommit=True) as adm:
        adm.execute("SELECT pg_terminate_backend(%s)", (c.info.backend_pid,))
    time.sleep(0.2)
    with pytest.raises(psycopg.OperationalError) as lost:
        c.execute("SELECT 1")
    assert mig._is_a_files_own_error(lost.value, c) is False
    c.close()


def test_pg17_a_role_saved_transaction_timeout_that_strikes_inside_a_file_gives_exit_2(
    mrun, cfg_dir, monkeypatch, capsys
):
    """Issue 1 of round 14, the PostgreSQL 17 case (25P04). THIS TEST IS UNRUN ON ANY SERVER HERE: it is a visible skip
    below 17 (only PostgreSQL 16 is installed), and it is listed UNRUN in the CHANGELOG until the CI job on 17 runs it.
    The role saves a `transaction_timeout` that is longer than the steps before the first file and shorter than a
    `pg_sleep` inside the first file, so the timeout strikes while the file runs (the earlier test of this kind set 1 ms,
    which strikes before any file). Exit 2, nothing kept. It does not discriminate V88 or V89 (see the PostgreSQL 16 test of the same class); no mutant is tied to it."""
    if mrun_server_version() < 170000:
        pytest.skip(
            "UNRUN: PostgreSQL 17 only (`transaction_timeout` does not exist below 17); "
            "the PostgreSQL 16 form of the same class is the idle-in-transaction test above"
        )
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
        adm.execute(
            sql.SQL("ALTER ROLE {} SET transaction_timeout = '3s'").format(
                sql.Identifier(helper.PLAIN_ROLE)
            )
        )
    _plant(monkeypatch, mrun.tmp, "0006_slow.sql", "SELECT pg_sleep(8);\n")
    try:
        assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
        _out, err = capsys.readouterr()
        assert err.startswith("refused: migrate stopped and kept nothing"), err
        # What the refusal names was never observed on a server (UNRUN): the code writes the server's SQLSTATE when the driver
        # gives one (25P04), else the driver's class name for the error (psycopg's `TransactionTimeout`, or `OperationalError`
        # if the server's message arrives as a lost connection). The promise under test is exit 2, nothing kept, not a failure.
        assert any(w in err for w in ("25P04", "TransactionTimeout", "OperationalError")), (
            f"the refusal names none of the three spellings the code can write for a PostgreSQL 17 transaction timeout; the "
            f"first observation on 17 shows which one it is, then this line names it: {err}"
        )
        assert "failed:" not in err, (
            f"a lost session must not be reported as a failure of the file: {err}"
        )
        assert _ledger_of(mrun.dsn) == []
    finally:
        with psycopg.connect(DSN, autocommit=True) as adm:
            adm.execute(
                sql.SQL("ALTER ROLE {} RESET transaction_timeout").format(
                    sql.Identifier(helper.PLAIN_ROLE)
                )
            )


def mrun_server_version() -> int:
    with psycopg.connect(DSN, autocommit=True) as adm:
        return adm.info.server_version


def test_step_8_that_cannot_connect_gives_exit_5(mrun, cfg_dir, monkeypatch, capsys):
    def refuse():
        raise psycopg.OperationalError("made-up: the server is not reachable")

    mrun.before_call[2] = refuse
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 5
    out, err = capsys.readouterr()
    assert "the check after the commit could not run" in err
    assert "(OperationalError)" in err and "made-up: the server" not in err  # the class name only
    assert out == ""
    assert _ledger_of(mrun.dsn) == REAL_FILES


@pytest.mark.parametrize("how", ["third_statement_cancelled", "old_version", "plain_psycopg_error"])
def test_any_error_inside_step_8_gives_exit_5_not_exit_2(how, mrun, cfg_dir, monkeypatch, capsys):
    real_fetch = v._fetch
    seen = {"n": 0, "on": False}

    def fetch(db, text, params=None, *, named=True):
        if not seen["on"]:
            return real_fetch(db, text, params, named=named)
        seen["n"] += 1
        if how == "third_statement_cancelled" and seen["n"] == 3:
            raise pge.QueryCanceled("made-up: canceled by the statement limit")
        if how == "old_version" and seen["n"] == 1:
            return ((150000, "made-up"),)
        if how == "plain_psycopg_error" and seen["n"] == 2:
            raise psycopg.Error("made-up: a plain driver error")
        return real_fetch(db, text, params, named=named)

    monkeypatch.setattr(v, "_fetch", fetch)
    mrun.after_call[2] = lambda conn: seen.update(on=True)
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 5
    _out, err = capsys.readouterr()
    # the first sentence is the after-commit one; "Nothing was changed" may only appear inside the quoted reason
    # (the old-version message), never as the opening of a refusal
    assert err.startswith(
        "The files are applied and committed, but the check after the commit could not run"
    )
    assert not err.startswith("refused")
    assert seen["n"] >= 1, "the injected fault ran inside step 8"
    assert _ledger_of(mrun.dsn) == REAL_FILES


def test_step_8_with_a_saved_statement_timeout_still_checks(mrun):
    """D-M2. The setting is 50 ms (the ticket says 5 ms; 5 ms can also cancel the lock statement of the run itself on a
    slow machine, which would test the wrong step). Sensitivity first: the setting really cancels a long statement."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
    role = helper.PLAIN_ROLE
    _super("ALTER ROLE {} SET statement_timeout = '50ms'", role)
    try:
        with (
            psycopg.connect(helper.login_dsn(DSN, role), autocommit=True) as c,
            pytest.raises(pge.QueryCanceled),
        ):
            c.execute("SELECT pg_sleep(0.5)")
        assert mig.migrate(mrun.dsn) == REAL_FILES  # `verify` sets its own two limits first
    finally:
        _super("ALTER ROLE {} RESET statement_timeout", role)
    assert mig.migrate(mrun.dsn) == []


def test_verify_gets_through_a_one_millisecond_statement_timeout_that_cancels_its_own_query(env):
    """Round 2 of 3c, N7 (Issue 13). The 50 ms test above can pass on a fast machine because nothing is cancelled. This one
    cannot: the SESSION setting is 1 ms, the sensitivity check runs the rights query itself (the biggest query of `verify`) and must be
    cancelled, and then `verify` on the same session still returns, because it sets its own two limits first.
    Killed by: V48 (the limits are not set before the reads); the sensitivity line fails on a server where 1 ms is not
    enough to cancel that query (never silently)."""
    n = env.n
    assert env.db.autocommit, (
        "the 1 ms setting is a SESSION setting and the fixture's session must be autocommit"
    )
    env.db.execute("SET statement_timeout = '1ms'")
    try:
        params = {"named": [n.rt, n.po, n.pu], "family": [n.mig], "schema": "app"}
        with pytest.raises(pge.QueryCanceled):
            env.db.execute(v.Q2, params).fetchall()
        assert run_verify(env) == []
    finally:
        env.db.execute("RESET statement_timeout")


def test_step_8_keeps_a_role_switch_in_the_dsn(mrun):
    """D-M8: `options=-c role=<M>` in the DSN is still in force on the step-8 connection."""
    login = f"hadavin_test_l_{uuid.uuid4().hex[:8]}"
    switch = f"hadavin_test_m_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.create_login_role(adm, login)
        adm.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(switch)))
        adm.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(switch), sql.Identifier(login)))
        adm.execute(
            sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                sql.Identifier(mrun.schema), sql.Identifier(switch)
            )
        )
        adm.execute(
            sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(
                sql.Identifier(adm.execute("SELECT current_database()").fetchone()[0]),
                sql.Identifier(switch),
            )
        )
    options = conninfo_to_dict(mrun.dsn)["options"] + f" -c role={switch}"
    dsn = helper.login_dsn(mrun.dsn, login, options=options)
    seen = {}
    mrun.after_call[2] = lambda conn: seen.update(
        who=conn.execute("SELECT current_user").fetchone()[0]
    )
    try:
        assert mig.migrate(dsn) == REAL_FILES
        assert seen["who"] == switch
    finally:
        with psycopg.connect(DSN, autocommit=True) as adm:
            for r in (switch, login):
                adm.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                adm.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def test_step_8_reads_one_snapshot(mrun, monkeypatch):
    """The reads of step 8 run in one transaction with the two settings the run put on the new connection."""
    real_fetch = v._fetch
    seen = {"on": False}

    def fetch(db, text, params=None, *, named=True):
        if seen["on"] and "iso" not in seen:
            seen["iso"] = db.execute("SHOW transaction_isolation").fetchone()[0]
            seen["ro"] = db.execute("SHOW transaction_read_only").fetchone()[0]
        return real_fetch(db, text, params, named=named)

    monkeypatch.setattr(v, "_fetch", fetch)
    mrun.after_call[2] = lambda conn: seen.update(on=True)
    assert mig.migrate(mrun.dsn) == REAL_FILES
    assert (seen["iso"], seen["ro"]) == ("repeatable read", "on")


_LATE_FILE_STATEMENTS = (
    (
        "CREATE CONSTRAINT TRIGGER hadavin_test_late_t AFTER INSERT ON hadavin_test_q DEFERRABLE INITIALLY DEFERRED "
        "FOR EACH ROW EXECUTE FUNCTION hadavin_test_late()"
    ),
    "INSERT INTO hadavin_test_q VALUES (1)",
)


def _late(mrun, monkeypatch, second: str) -> None:
    """A file with a deferred constraint trigger that defers itself again: its first firing is at step 5, its second at
    COMMIT. The table and the trigger function are made beforehand (their bodies hold `;`, which the text rules read as
    the end of a statement); the file makes the trigger and the first row inside a function body, so the text rules
    see neither. `second` is what the second firing does."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
        s = sql.Identifier(mrun.schema)
        adm.execute(sql.SQL("CREATE TABLE {}.hadavin_test_q (i int)").format(s))
        adm.execute(
            sql.SQL(
                "CREATE FUNCTION {0}.hadavin_test_late() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN "
                "IF NEW.i = 1 THEN EXECUTE 'SET CONSTR' || 'AINTS ALL DEFERRED'; "
                "INSERT INTO {0}.hadavin_test_q VALUES (2); ELSE "
            ).format(s)
            + sql.SQL(second)
            + sql.SQL(" END IF; RETURN NULL; END $f$")
        )
        adm.execute(
            sql.SQL("GRANT ALL ON {}.hadavin_test_q TO {}").format(
                s, sql.Identifier(helper.PLAIN_ROLE)
            )
        )
    runs = " ".join(f"EXECUTE '{st[:3]}' || '{st[3:]}';" for st in _LATE_FILE_STATEMENTS)
    _plant(
        monkeypatch,
        mrun.tmp,
        "0006_late.sql",
        "CREATE OR REPLACE FUNCTION hadavin_test_late_runner() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"{runs} END $$;\nSELECT hadavin_test_late_runner();\n",
    )


def test_a_commit_refused_by_the_server_gives_exit_2_and_keeps_nothing(
    mrun, cfg_dir, monkeypatch, capsys
):
    """D-M3: the second firing of a deferred trigger (which deferred itself again) raises a check violation AT COMMIT."""
    second = "RAISE EXCEPTION 'made-up refusal at commit' USING ERRCODE = '23514';"
    _late(mrun, monkeypatch, second)
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 2
    _out, err = capsys.readouterr()
    assert "the database server refused the commit (23514" in err and "Nothing was kept" in err
    assert "may or may not" not in err
    assert _ledger_of(mrun.dsn) == []


def _end_the_sleeping_session(mrun, cfg_dir, monkeypatch, how: str):
    """Run `migrate` through the CLI while a second session ends the backend that sleeps at the COMMIT (`how` is the
    server function: `pg_terminate_backend` closes the connection, `pg_cancel_backend` cancels the statement). Returns
    the exit code, the pids that were ended and what `_commit_outcome` was asked and answered."""
    stop = threading.Event()
    killed, asked = [], []
    real = mig._commit_outcome
    # Issue 6 of round 3 on 3d: only the session of THIS run is ended, found by its own application name, so another
    # session that sleeps on a shared server is never touched.
    app = "hadavin_test_sleep_" + uuid.uuid4().hex[:12]
    run_dsn = make_conninfo(mrun.dsn, application_name=app)

    def recording(exc, db):
        answer = real(exc, db)
        asked.append((getattr(exc, "sqlstate", None), answer))
        return answer

    monkeypatch.setattr(mig, "_commit_outcome", recording)

    def killer():
        with psycopg.connect(DSN, autocommit=True) as adm:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not stop.is_set():
                sleeping = adm.execute(
                    "SELECT pid FROM pg_stat_activity WHERE wait_event = 'PgSleep' AND pid <> pg_backend_pid() "
                    "AND application_name = %s",
                    (app,),
                ).fetchone()
                if sleeping:
                    adm.execute(
                        sql.SQL("SELECT {}(%s)").format(sql.Identifier(how)), (sleeping[0],)
                    )
                    killed.append(sleeping[0])
                    return
                time.sleep(0.05)

    t = threading.Thread(target=killer)
    t.start()
    try:
        rc = _cli_migrate(cfg_dir, monkeypatch, run_dsn)
    finally:
        stop.set()
        t.join(15)
    return rc, killed, asked


def test_a_lost_connection_at_commit_gives_exit_5(mrun, cfg_dir, monkeypatch, capsys):
    """D-M3: the second firing sleeps; a second session ends that backend while it sleeps. The wording is asserted, not
    the outcome (here the commit did not happen; a cut after the server finished gives the same error). Round 2 of 3c
    (N8): the classifier saw exactly 57P01 and answered "unknown". Killed by: V58 and V59 (classes), and the `asked` line
    by V69 (the error is classed without asking)."""
    _late(mrun, monkeypatch, "PERFORM pg_sleep(5);")
    rc, killed, asked = _end_the_sleeping_session(
        mrun, cfg_dir, monkeypatch, "pg_terminate_backend"
    )
    _out, err = capsys.readouterr()
    assert killed, "the second session saw the sleep and ended it"
    assert rc == 5
    assert "the commit may or may not have happened" in err
    assert asked == [("57P01", "unknown")], asked


def test_a_cancel_at_commit_gives_exit_2(mrun, cfg_dir, monkeypatch, capsys):
    """Ticket 7.6 (round 2 of 3c, N8). The same sleep, ended by `pg_cancel_backend`: the server cancels the statement at
    the COMMIT (57014) and keeps the session, so the commit was refused: exit 2, nothing kept, and the classifier saw
    exactly 57014 and answered "refused"."""
    _late(mrun, monkeypatch, "PERFORM pg_sleep(5);")
    rc, killed, asked = _end_the_sleeping_session(mrun, cfg_dir, monkeypatch, "pg_cancel_backend")
    _out, err = capsys.readouterr()
    assert killed, "the second session saw the sleep and cancelled it"
    assert rc == 2, err
    assert "the database server refused the commit (57014" in err and "Nothing was kept" in err
    assert "may or may not" not in err
    assert asked == [("57014", "refused")], asked
    assert _ledger_of(mrun.dsn) == []


# --- `migrate()` on a real server: what step 2 refuses, what the run repairs, what the end of the run refuses ---------------


@pytest.fixture
def three_roles():
    """Three made-up plain roles (runtime, portal, purge); dropped afterwards."""
    tag = "hadavin_test_r" + uuid.uuid4().hex[:8]
    names = SimpleNamespace(rt=f"{tag}_rt", po=f"{tag}_po", pu=f"{tag}_pu", x=f"{tag}_x")
    with psycopg.connect(DSN, autocommit=True) as adm:
        for r in (names.rt, names.po, names.pu, names.x):
            adm.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(r)))
    try:
        yield names
    finally:
        with psycopg.connect(DSN, autocommit=True) as adm:
            for r in (names.rt, names.po, names.pu, names.x):
                adm.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                adm.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(r)))


def _public_execute_functions(db, schema: str) -> int:
    """How many functions of the schema everyone may execute (no function ACL means the default: everyone)."""
    return db.execute(
        "SELECT count(*) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = %s AND (p.proacl IS NULL OR EXISTS (SELECT 1 FROM pg_catalog.aclexplode(p.proacl) a "
        "WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE'))",
        (schema,),
    ).fetchone()[0]


def test_upgrade_from_mains_state_is_repaired(mrun, three_roles):
    """R-M9. This EMULATES the state that main's `migrate` left (main 2a8c2aa): the shipped files applied by the
    migration role in one transaction, the ledger with their versions, the three named roles granted exactly the grant
    map with the migration role as grantor, and the default EXECUTE for everyone left on the package's functions
    (main never took it off). It does not run main's code. The new `migrate` with nothing pending then returns normally
    and the default EXECUTE is gone."""
    n = three_roles
    with mig.connect(mrun.dsn) as db, db.transaction():
        db.execute(
            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        for stem in REAL_FILES:
            db.execute((mig.MIGRATIONS / f"{stem}.sql").read_text(encoding="utf-8"))
            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (stem,))
        mig._apply_grants(db, mrun.schema, n.rt, lambda g: g.runtime)
        mig._apply_grants(db, mrun.schema, n.pu, lambda g: g.purge, lambda g: g.purge_cols)
        mig._apply_grants(db, mrun.schema, n.po, lambda g: "SELECT" if g.portal else "")
    with psycopg.connect(DSN, autocommit=True) as adm:
        assert _public_execute_functions(adm, mrun.schema) > 0, (
            "the emulated state has the default EXECUTE"
        )
    assert mig.migrate(mrun.dsn, runtime_role=n.rt, portal_role=n.po, purge_role=n.pu) == []
    with psycopg.connect(DSN, autocommit=True) as adm:
        assert _public_execute_functions(adm, mrun.schema) == 0
    assert _ledger_of(mrun.dsn) == REAL_FILES


@pytest.fixture
def case_db():
    """A database of its own whose owner is a plain login role: its schema `public` is the schema of the run, with the
    server's own access list (everyone may use it; nobody but the owner may create in it)."""
    tag = "hadavin_test_pub" + uuid.uuid4().hex[:8]
    owner = tag + "_o"
    roles = [tag + "_rt", tag + "_po", tag + "_pu"]
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.create_login_role(adm, owner)
        for r in roles:
            adm.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(r)))
        adm.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(tag), sql.Identifier(owner)
            )
        )
    try:
        yield SimpleNamespace(
            tag=tag,
            dsn=helper.login_dsn(make_conninfo(DSN, dbname=tag), owner),
            admin_dsn=make_conninfo(DSN, dbname=tag),
            roles=roles,
        )
    finally:
        with psycopg.connect(DSN, autocommit=True) as adm:
            adm.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(tag))
            )
            for r in (owner, *roles):
                adm.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(r)))


@pytest.mark.real_connect
def test_the_public_schema_with_the_server_default_passes(case_db):
    """R-B2: everyone holds USAGE on `public` (the server's own default); `migrate` with the three roles returns."""
    rt, po, pu = case_db.roles
    assert mig.migrate(case_db.dsn, runtime_role=rt, portal_role=po, purge_role=pu) == REAL_FILES
    assert mig.migrate(case_db.dsn, runtime_role=rt, portal_role=po, purge_role=pu) == []


@pytest.mark.real_connect
def test_create_for_everyone_on_public_is_refused(case_db):
    """The sensitivity control of the test above: with CREATE on `public` for everyone, step 2 refuses and no file ran."""
    rt, po, pu = case_db.roles
    with psycopg.connect(case_db.admin_dsn, autocommit=True) as adm:
        adm.execute("GRANT CREATE ON SCHEMA public TO PUBLIC")
    with pytest.raises(ConfigError) as e:
        mig.migrate(case_db.dsn, runtime_role=rt, portal_role=po, purge_role=pu)
    text = str(e.value)
    assert (
        "Nothing was changed. No file ran." in text and "CREATE" in text and "everyone" in text
    ), text
    assert _ledger_of(case_db.dsn) == []


def test_a_named_role_in_pg_monitor_is_refused_at_step_2_with_one_statement(mrun, three_roles):
    """D-M4: one membership line and one statement, `REVOKE "pg_monitor" FROM "<role>" GRANTED BY "<grantor>";`; no file ran."""
    n = three_roles
    with psycopg.connect(DSN, autocommit=True) as adm:
        adm.execute(sql.SQL("GRANT pg_monitor TO {}").format(sql.Identifier(n.rt)))
        grantor = _recorded_grantor(adm, "pg_monitor", n.rt)
    with pytest.raises(ConfigError) as e:
        mig.migrate(mrun.dsn, runtime_role=n.rt)
    text = str(e.value)
    assert "Nothing was changed. No file ran." in text, text
    statement = f'REVOKE "pg_monitor" FROM "{n.rt}" GRANTED BY "{grantor}";'
    # the membership line and the three roles it brings in (pg_read_all_settings, pg_read_all_stats, pg_stat_scan_tables)
    # are four lines; they print the SAME statement, and no other statement is printed
    assert (
        text.count(statement) == text.count("REVOKE ") == text.count("built-in server role") == 4
    ), text
    assert _ledger_of(mrun.dsn) == []


def test_a_right_granted_by_a_grant_option_holder_is_not_dropped_at_step_2(
    mrun, three_roles, monkeypatch
):
    """D-m5 / effect E38. A right on a table of the map that the runtime role holds from a role other than the migration
    role cannot be taken away by the run (its REVOKE removes only the rights it granted itself), so the run refuses at step
    2: no pending file ran. The control: the same right granted by the owner is repaired by step 4 and the file runs."""
    n = three_roles
    assert mig.migrate(mrun.dsn, runtime_role=n.rt) == REAL_FILES
    table = "audit_entries"
    assert "DELETE" not in GRANTS[table].runtime
    _plant(monkeypatch, mrun.tmp, "0006_one.sql", "SELECT 1;\n")
    s = sql.Identifier(mrun.schema)
    t = sql.Identifier(table)
    with psycopg.connect(DSN, autocommit=True) as adm:
        adm.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(s, sql.Identifier(n.x)))
        adm.execute(
            sql.SQL("GRANT DELETE ON TABLE {}.{} TO {} WITH GRANT OPTION").format(
                s, t, sql.Identifier(n.x)
            )
        )
        adm.execute(
            sql.SQL("SET ROLE {}").format(sql.Identifier(n.x))
        )  # the grantor of the next line is `x`
        adm.execute(sql.SQL("GRANT DELETE ON TABLE {}.{} TO {}").format(s, t, sql.Identifier(n.rt)))
        adm.execute("RESET ROLE")
    with pytest.raises(ConfigError) as e:
        mig.migrate(mrun.dsn, runtime_role=n.rt)
    assert "Nothing was changed. No file ran." in str(e.value), str(e.value)
    assert "0006_one" not in _ledger_of(mrun.dsn)
    with psycopg.connect(DSN, autocommit=True) as adm:  # the control: the owner is the grantor
        adm.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(n.x)))
        adm.execute(
            sql.SQL("REVOKE DELETE ON TABLE {}.{} FROM {}").format(s, t, sql.Identifier(n.rt))
        )
        adm.execute("RESET ROLE")
        adm.execute(sql.SQL("REVOKE ALL ON TABLE {}.{} FROM {}").format(s, t, sql.Identifier(n.x)))
        adm.execute(sql.SQL("REVOKE USAGE ON SCHEMA {} FROM {}").format(s, sql.Identifier(n.x)))
        adm.execute(sql.SQL("GRANT DELETE ON TABLE {}.{} TO {}").format(s, t, sql.Identifier(n.rt)))
    assert mig.migrate(mrun.dsn, runtime_role=n.rt) == ["0006_one"]


def test_a_ledger_trigger_that_disables_the_audit_triggers_is_refused_at_the_end_of_the_run(
    mrun, monkeypatch
):
    """D-m11 (round-12 F2 variant): a file makes a trigger on the ledger whose function switches the audit triggers off.
    It fires at the migration's own ledger insert, so only the check at the end of the run (step 6) can see the result:
    the run is refused as a mistake and keeps nothing."""
    assert mig.migrate(mrun.dsn) == REAL_FILES
    body = (
        "CREATE OR REPLACE FUNCTION hadavin_test_off() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
        "EXECUTE 'ALTER TABLE audit_entries DISABLE TRIGGER USER'; RETURN NULL; END $$;\n"
        "CREATE TRIGGER hadavin_test_off_t AFTER INSERT ON schema_migrations FOR EACH ROW "
        "EXECUTE FUNCTION hadavin_test_off();\n"
    )
    _plant(monkeypatch, mrun.tmp, "0006_off.sql", body)
    with pytest.raises(ConfigError) as e:
        mig.migrate(mrun.dsn)
    text = str(e.value)
    assert "changed a trigger" in text and "audit_entries" in text and "enabled state" in text, text
    assert "0006_off" not in _ledger_of(mrun.dsn), "the run kept nothing"
    with psycopg.connect(DSN, autocommit=True) as adm:
        states = adm.execute(
            "SELECT t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = 'audit_entries' "
            "AND NOT t.tgisinternal",
            (mrun.schema,),
        ).fetchall()
    assert states and all(s[0] == "O" for s in states), "every audit trigger is still enabled"


def after_all(env, reviewed):
    return [
        p for p in run_verify(env, reviewed_definers=reviewed) if p.kind == "definer_unreviewed"
    ]


def test_a_reviewed_definer_is_excused_only_in_its_schema_with_its_arguments(env):
    """C-F9 on a real server: a SECURITY DEFINER function owned by the migration role is excused by the reviewed key
    (schema, name, argument list) and by nothing broader: the same name in another schema and an overload are not."""
    n = env.n
    for text in (
        "CREATE SCHEMA other AUTHORIZATION {}",
        "CREATE FUNCTION app.door(q text) RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'",
        "CREATE FUNCTION app.door(q text, r int) RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 2'",
        "CREATE FUNCTION other.door(q text) RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 3'",
        "ALTER FUNCTION app.door(text) OWNER TO {}",
        "ALTER FUNCTION app.door(text, int) OWNER TO {}",
        "ALTER FUNCTION other.door(text) OWNER TO {}",
        "CREATE FUNCTION app.third(q text) RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 4'",
    ):
        x(env, text, *([n.mig] if "{}" in text else []))
    before = [p for p in run_verify(env) if p.kind == "definer_unreviewed"]
    assert any(p.obj == "door" and p.schema == "app" for p in before), [p.line() for p in before]
    reviewed = frozenset({("app", "door", "q text")})
    after = [
        p for p in run_verify(env, reviewed_definers=reviewed) if p.kind == "definer_unreviewed"
    ]
    spots = {(p.schema, p.detail) for p in after}
    assert ("app", "q text") not in spots, "the reviewed function is excused"
    assert any(p.schema == "app" and p.detail != "q text" for p in after), (
        "the overload is not excused"
    )
    assert not any(p.schema == "app" and p.detail == "q text" for p in after)
    # a function that a role outside the migration role's family owns (here the made-up role `other`) is not judged by S7
    x(env, "ALTER FUNCTION app.third(text) OWNER TO {}", n.other)
    assert not any(p.obj == "third" for p in after_all(env, reviewed))
    # and one of the family is judged, in the schema of the run only: `other.door` is never named
    assert not any(p.schema == "other" for p in after_all(env, reviewed))


@pytest.mark.perf  # a wall-clock bound: CI runs it in its perf step (it needs the postgres service)
def test_verify_cost_on_a_large_catalog(env, monkeypatch):
    """D-m10: one `verify` call on a database with 5,000 tables of another application (each with a column grant to a third
    role), 20,000 functions, 2,000 large objects, 500 roles with memberships and a 25-level diamond of memberships under
    the runtime role. Under 30 s for the whole call (each of its 8 statements has a 60 s limit); the time of each
    statement is printed."""
    n = env.n
    db = env.db
    pre = f"{n.tag}_big"
    extra_roles = [f"{pre}_{i}" for i in range(500)]
    diamond = [f"{pre}_d{i}_{side}" for i in range(25) for side in "ab"]
    try:
        db.execute("CREATE SCHEMA other_app")
        db.execute(
            sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(f"{pre}_third")),
        )
        db.execute(
            sql.SQL(
                "DO $$ BEGIN FOR i IN 1..5000 LOOP EXECUTE format('CREATE TABLE other_app.t%s (a int, b int)', i); "
                "EXECUTE format('GRANT SELECT (a) ON other_app.t%s TO {}', i); END LOOP; END $$"
            ).format(sql.Identifier(f"{pre}_third")),
        )
        db.execute(
            "DO $$ BEGIN FOR i IN 1..20000 LOOP EXECUTE format('CREATE FUNCTION other_app.f%s() RETURNS int "
            "LANGUAGE sql AS ''SELECT %s''', i, i); END LOOP; END $$"
        )
        db.execute("SELECT lo_create(0) FROM generate_series(1, 2000)")
        for r in extra_roles + diamond:
            db.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(r)))
        for i, r in enumerate(extra_roles[:-1]):  # a chain of 500 memberships (no cycle)
            db.execute(
                sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(extra_roles[i + 1]), sql.Identifier(r)
                )
            )
        # the diamond: level i has two roles, each a member of both roles of level i+1
        for i in range(24):
            for up in "ab":
                for low in "ab":
                    db.execute(
                        sql.SQL("GRANT {} TO {}").format(
                            sql.Identifier(f"{pre}_d{i + 1}_{up}"),
                            sql.Identifier(f"{pre}_d{i}_{low}"),
                        )
                    )
        for low in "ab":
            db.execute(
                sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(f"{pre}_d0_{low}"), sql.Identifier(n.rt)
                )
            )
        db.execute("ANALYZE")
        real_fetch, each = v._fetch, []

        def timed(db_, text, params=None, *, named=True):
            t0 = time.perf_counter()
            try:
                return real_fetch(db_, text, params, named=named)
            finally:
                each.append(time.perf_counter() - t0)

        monkeypatch.setattr(v, "_fetch", timed)
        start = time.perf_counter()
        problems = run_verify(env)
        took = time.perf_counter() - start
        print(f"verify on the large catalog: {took:.2f} s, {len(problems)} problems")
        print("seconds per statement: " + ", ".join(f"{t:.3f}" for t in each))
        assert len(each) == 8, each
        assert took < 30, f"one verify call took {took:.1f} s"
    finally:
        db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(f"{pre}_third")))
        with psycopg.connect(DSN, autocommit=True) as adm:
            for r in [f"{pre}_third", *extra_roles, *diamond]:
                adm.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(r)))


@pytest.mark.parametrize(
    ("kind", "create", "name"),
    [
        ("table", "CREATE TABLE {s}.runs (i int)", "runs"),
        ("sequence", "CREATE SEQUENCE {s}.dead_letters_seq_seq", "dead_letters_seq_seq"),
        (
            "function",
            "CREATE FUNCTION {s}.hadavin_audit_append_only() RETURNS int LANGUAGE sql AS $q$ SELECT 1 $q$",
            "hadavin_audit_append_only",
        ),
    ],
    ids=["table", "sequence", "function"],
)
def test_a_name_the_package_manages_that_a_third_role_owns_is_refused_at_step_2(
    mrun, three_roles, kind, create, name
):
    """O8 on a real server, for each kind: an object with a name of the grant map (or a function the files create) that a
    role outside the migration role's family owns is refused before any file runs: the migration role could not change it
    later. The statements printed hand it to the migration role."""
    n = three_roles
    s = sql.Identifier(mrun.schema).as_string(None)
    word = "FUNCTION" if kind == "function" else kind.upper()
    target = f"{s}.{name}" + ("()" if kind == "function" else "")
    with psycopg.connect(DSN, autocommit=True) as adm:
        adm.execute(create.format(s=s))
        adm.execute(sql.SQL(f"ALTER {word} {target} OWNER TO {{}}").format(sql.Identifier(n.x)))
    with pytest.raises(ConfigError) as e:
        mig.migrate(mrun.dsn)
    text = str(e.value)
    assert "Nothing was changed" in text and name in text and n.x in text, text
    # the words of the step-1 read (`_refuse_foreign_owned`); the step-2 check of `verify` finds the same object and
    # would refuse with its own words, so this line is what shows that the step-1 read saw the owner. Mutants OW5, OW6.
    assert "cannot change 1 object(s) of this package" in text, text
    assert _ledger_of(mrun.dsn) == []


def test_step_4_revokes_an_aggregate_with_no_arguments_that_has_the_name_of_a_files_function(
    mrun, monkeypatch
):
    """REVOKE writes `()` for an aggregate with no arguments (`(*)` is a syntax error there). A file function and an
    aggregate share a name; the migration role owns the aggregate; step 4 takes EXECUTE for everyone off both.
    Old the old `*` branch is retired: the server writes no `*` for the identity arguments on 16.15, so that
    branch could never run and was removed."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
        s = sql.Identifier(mrun.schema)
        adm.execute(
            sql.SQL(
                "CREATE AGGREGATE {}.hadavin_test_dual(*) (sfunc = int8inc, stype = int8, initcond = '0')"
            ).format(s)
        )
        adm.execute(
            sql.SQL("ALTER AGGREGATE {}.hadavin_test_dual(*) OWNER TO {}").format(
                s, sql.Identifier(helper.PLAIN_ROLE)
            )
        )
    _plant(
        monkeypatch,
        mrun.tmp,
        "0006_dual.sql",
        "CREATE OR REPLACE FUNCTION hadavin_test_dual(x int) RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;\n",
    )
    assert mig.migrate(mrun.dsn) == REAL_FILES + ["0006_dual"]
    with psycopg.connect(DSN, autocommit=True) as adm:
        rows = adm.execute(
            "SELECT pg_get_function_identity_arguments(p.oid), p.prokind::text, "
            "(SELECT count(*) FROM aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
            " WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE') "
            "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
            "WHERE n.nspname = %s AND p.proname = 'hadavin_test_dual' ORDER BY 2",
            (mrun.schema,),
        ).fetchall()
    assert [(r[0], r[1]) for r in rows] == [("", "a"), ("x integer", "f")], rows
    assert [r[2] for r in rows] == [0, 0], rows


_AWKWARD = ["MixedCase", "na\u00efve_\u0192", "back\\slash", "line\nbreak", 'quo""te']


def test_step_4_takes_everyones_execute_off_functions_with_awkward_names(mrun, monkeypatch):
    """Round 2 of 3c, C2 (Issue 6). The REVOKE of step 4 is built with the driver's identifier quoting, so a function
    whose name has a capital letter, a non-ASCII letter, a backslash, a line break or a double quote is revoked like any
    other. On the code before this change the names that `ascii()` would escape (all but the first) were skipped, EVERYONE
    kept EXECUTE, and step 6 refused the whole run for a file that did nothing wrong; this test fails there (run
    against the old code, see the PR notes). Killed by: V66 (the skip is put back)."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
    body = " ".join(
        f'CREATE OR REPLACE FUNCTION "{name}"(x int) RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;'
        for name in _AWKWARD
    )
    _plant(monkeypatch, mrun.tmp, "0006_awkward.sql", body + "\n")
    assert mig.migrate(mrun.dsn) == REAL_FILES + ["0006_awkward"]
    with psycopg.connect(DSN, autocommit=True) as adm:
        rows = adm.execute(
            "SELECT p.proname, (SELECT count(*) FROM aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
            " WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE') "
            "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = %s AND p.proname = ANY(%s) ORDER BY 1",
            (mrun.schema, [n.replace('""', '"') for n in _AWKWARD]),
        ).fetchall()
    names = [r[0] for r in rows]
    assert sorted(names) == sorted(n.replace('""', '"') for n in _AWKWARD), names
    assert [r[1] for r in rows] == [0] * len(_AWKWARD), rows
    assert mig.migrate(mrun.dsn) == []


def test_step_4_takes_everyones_execute_off_a_function_whose_argument_has_an_odd_name_and_type(
    mrun, monkeypatch
):
    """Issue 5 of round 3 on 3d: the identity-argument text that step 4 passes on is the server's own, quoted by the
    server, and is not checked by `_plain`; a function `"f"("Odd Arg" "char")` (an argument name with a capital and a
    space, and a type whose name the server writes in double quotes: `"char"`) is revoked like any other. Killed by: V83 (the arguments are left out of the statement,
    so the REVOKE names no function and the run fails)."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
    body = 'CREATE OR REPLACE FUNCTION "f"("Odd Arg" "char") RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;\n'
    _plant(monkeypatch, mrun.tmp, "0006_odd_argument.sql", body)
    try:
        applied = mig.migrate(mrun.dsn)
    except (ConfigError, psycopg.Error) as e:  # a wrong type is a failed assert below
        applied = f"{type(e).__name__}: {e}"
    assert applied == REAL_FILES + ["0006_odd_argument"]
    with psycopg.connect(DSN, autocommit=True) as adm:
        everyone = adm.execute(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace, "
            "aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
            "WHERE n.nspname = %s AND p.proname = 'f' AND a.grantee = 0 AND a.privilege_type = 'EXECUTE'",
            (mrun.schema,),
        ).fetchone()[0]
    assert everyone == 0
    assert mig.migrate(mrun.dsn) == []


def test_an_unreadable_lock_view_is_a_plain_config_error(env):
    """Ticket 6.2, real server: the lock is held by another session, the login that waits may not read
    `pg_stat_activity` (a catalog view this database's administrator closed), and `migrate`'s wait ends. The answer is
    a ConfigError that says the holder could not be read and that nothing was changed (exit 2), never a raw driver error.
    Killed by: mutant V73 (the handler does not catch the driver error)."""
    from hadavin_sdk.store import migrate as mig

    n = env.n
    login = f"{n.tag}_login"
    helper.create_login_role(env.db, login)
    try:
        env.db.execute("REVOKE SELECT ON pg_catalog.pg_stat_activity FROM PUBLIC")
        dsn = helper.login_dsn(make_conninfo(DSN, dbname=n.tag), login)
        with psycopg.connect(make_conninfo(DSN, dbname=n.tag), autocommit=True) as holder:
            holder.execute("BEGIN")
            holder.execute("SELECT pg_advisory_xact_lock(%s)", (mig.MIGRATE_LOCK,))
            with psycopg.connect(dsn, autocommit=True) as waiter:
                waiter.execute("BEGIN")
                outcome = None
                try:
                    mig._take_the_lock(waiter, 1)
                except (ConfigError, psycopg.Error) as exc:  # judged below, outside the handler
                    outcome = exc
                waiter.execute("ROLLBACK")
            holder.execute("ROLLBACK")
        assert isinstance(outcome, ConfigError), f"expected the refusal, got {outcome!r}"
        text = str(outcome)
        assert "could not read who holds it" in text
        assert "Nothing was changed." in text and "permission denied" in text
        assert "migrate waited 1 seconds for the migration lock and gave up" in text
    finally:
        env.db.execute("GRANT SELECT ON pg_catalog.pg_stat_activity TO PUBLIC")
        env.db.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(login)))


def test_the_lock_queries_tell_a_live_session_from_a_prepared_transaction(env):
    """Real server, the two queries of ticket 6.1 on their own. A live session that holds the migration lock is NOT a
    prepared transaction: the count of lock rows without a session is 0 and no prepared transaction is named. After the
    lock is held by a prepared transaction, the count is 1 and exactly that transaction is named, not a bystander that
    holds another lock. Killed by: mutant V72 (`l.pid IS NULL` is left out of the count) and V71 (the old listing)."""
    from hadavin_sdk.store import migrate as mig

    n = env.n
    gid, by = f"{n.tag}_holder", f"{n.tag}_bystander"
    dsn = make_conninfo(DSN, dbname=n.tag)

    def look():
        count = env.db.execute(mig._LOCK_PREPARED_SQL, (mig.MIGRATE_LOCK,)).fetchone()[0]
        names = [r[0] for r in env.db.execute(mig._PREPARED_SQL, (mig.MIGRATE_LOCK,)).fetchall()]
        return count, names

    with psycopg.connect(dsn, autocommit=True) as live:
        live.execute("BEGIN")
        live.execute("SELECT pg_advisory_xact_lock(%s)", (mig.MIGRATE_LOCK,))
        assert look() == (0, [])
        live.execute("ROLLBACK")
    assert look() == (0, [])
    try:
        with psycopg.connect(dsn, autocommit=True) as a:
            a.execute("BEGIN")
            a.execute("SELECT pg_advisory_xact_lock(%s)", (mig.MIGRATE_LOCK + 1,))
            a.execute(sql.SQL("PREPARE TRANSACTION {}").format(sql.Literal(by)))
            a.execute("BEGIN")
            a.execute("SELECT pg_advisory_xact_lock(%s)", (mig.MIGRATE_LOCK,))
            a.execute(sql.SQL("PREPARE TRANSACTION {}").format(sql.Literal(gid)))
        assert look() == (1, [gid])
    finally:
        for g in (gid, by):
            env.db.execute(sql.SQL("ROLLBACK PREPARED {}").format(sql.Literal(g)))
