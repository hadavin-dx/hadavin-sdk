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


def _cli_migrate(cfg_dir, monkeypatch, dsn):
    """Config with the postgres store, the migration DSN in the environment, then `cli.main(["migrate"])`."""
    import yaml

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", dsn)
    return cli.main(["--config", str(cfg_dir), "migrate"])


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


def test_step_8_that_cannot_connect_gives_exit_5(mrun, cfg_dir, monkeypatch, capsys):
    def refuse():
        raise psycopg.OperationalError("made-up: the server is not reachable")

    mrun.before_call[2] = refuse
    assert _cli_migrate(cfg_dir, monkeypatch, mrun.dsn) == 5
    out, err = capsys.readouterr()
    assert "the check after the commit could not run" in err and "made-up: the server" in err
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


def test_a_lost_connection_at_commit_gives_exit_5(mrun, cfg_dir, monkeypatch, capsys):
    """D-M3: the second firing sleeps; a second session ends that backend while it sleeps. The wording is asserted, not
    the outcome (here the commit did not happen; a cut after the server finished gives the same error)."""
    _late(mrun, monkeypatch, "PERFORM pg_sleep(5);")
    stop = threading.Event()
    killed = []

    def killer():
        with psycopg.connect(DSN, autocommit=True) as adm:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not stop.is_set():
                sleeping = adm.execute(
                    "SELECT pid FROM pg_stat_activity WHERE wait_event = 'PgSleep' AND pid <> pg_backend_pid()"
                ).fetchone()
                if sleeping:
                    adm.execute("SELECT pg_terminate_backend(%s)", (sleeping[0],))
                    killed.append(sleeping[0])
                    return
                time.sleep(0.05)

    t = threading.Thread(target=killer)
    t.start()
    try:
        rc = _cli_migrate(cfg_dir, monkeypatch, mrun.dsn)
    finally:
        stop.set()
        t.join(15)
    _out, err = capsys.readouterr()
    assert killed, "the second session saw the sleep and ended it"
    assert rc == 5
    assert "the commit may or may not have happened" in err


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
        grantor = adm.execute("SELECT current_user").fetchone()[0]
        adm.execute(sql.SQL("GRANT pg_monitor TO {}").format(sql.Identifier(n.rt)))
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
    assert _ledger_of(mrun.dsn) == []


def test_step_4_revokes_an_aggregate_with_no_arguments_that_has_the_name_of_a_files_function(
    mrun, monkeypatch
):
    """REVOKE writes `()` for an aggregate with no arguments (`(*)` is a syntax error there). A file function and an
    aggregate share a name; the migration role owns the aggregate; step 4 takes EXECUTE for everyone off both.
    Old mutant E5 (a `*` branch) is retired: the server writes no `*` for the identity arguments on 16.15, so that
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
