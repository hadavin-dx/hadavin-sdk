"""P4d-a1: the neutral driver namespace `pg_driver()` (tests use it and never import the driver)."""

import os
from types import ModuleType

import pytest

from tests.contracts.kinds.store_postgres import pg_driver, pg_schema

NAMES = {
    "connect_admin",
    "connect_runtime",
    "connect_role",
    "execute",
    "ident",
    "sqlstate",
    "expect_sqlstate",
    "is_unique_violation",
    "make_error",
    "make_dsn",
    "dsn_parts",
}


@pytest.fixture
def drv():
    return pg_driver()


@pytest.fixture
def runtime_dsn():
    yield from pg_schema(runtime=True)


def test_the_namespace_has_exactly_the_helper_names_and_no_driver_module(drv):
    """Killer of a mutant that returns the driver module itself."""
    assert set(vars(drv)) == NAMES
    assert not isinstance(drv, ModuleType)
    assert not any(isinstance(v, ModuleType) for v in vars(drv).values())
    assert all(callable(v) for v in vars(drv).values())


def test_connect_runtime_is_the_runtime_login_and_connect_admin_the_owner(drv, runtime_dsn):
    """Killer of a mutant where `connect_runtime` returns the admin connection."""
    with drv.connect_runtime(runtime_dsn) as rt, drv.connect_admin(runtime_dsn) as admin:
        runtime_user = drv.execute(rt, "SELECT current_user")[0][0]
        owner_user = drv.execute(admin, "SELECT current_user")[0][0]
        assert runtime_user.startswith("rt_")
        assert owner_user != runtime_user
        assert not owner_user.startswith("rt_")
        # the runtime login really holds the narrower rights: it cannot create a table, the owner can
        with drv.expect_sqlstate("42501"):
            drv.execute(rt, "CREATE TABLE no_way (x int)")
        drv.execute(admin, "CREATE TABLE fine (x int)")


def test_connect_runtime_refuses_a_dsn_that_is_not_a_fixture_runtime_dsn(drv):
    with pytest.raises(ValueError, match="pg_schema"):
        drv.connect_runtime("postgresql://example.invalid/db")


def test_execute_fills_identifiers_and_parameters_and_returns_rows(drv, runtime_dsn):
    with drv.connect_admin(runtime_dsn) as admin:
        assert (
            drv.execute(admin, "CREATE TABLE {} ({} int, {} text)", idents=["t1", "a", "b"]) == []
        )
        assert drv.execute(admin, "INSERT INTO {} VALUES (%s, %s)", (7, "x"), idents=["t1"]) == []
        assert drv.execute(admin, "SELECT {}, {} FROM {}", idents=["a", "b", "t1"]) == [(7, "x")]
        # an identifier is quoted, never spliced: a hostile name stays one name
        hostile = 'a"; DROP TABLE t1; --'
        assert drv.execute(admin, "CREATE TABLE {} (x int)", idents=[hostile]) == []
        assert drv.execute(admin, "SELECT count(*) FROM {}", idents=["t1"]) == [(1,)]


def test_connect_role_has_exactly_the_listed_rights_and_is_dropped_afterwards(drv, runtime_dsn):
    with drv.connect_role(runtime_dsn, grants=[("SELECT", "spend")]) as conn:
        role = drv.execute(conn, "SELECT current_user")[0][0]
        assert drv.execute(conn, "SELECT count(*) FROM spend") == [(0,)]
        with drv.expect_sqlstate("42501"):
            drv.execute(
                conn, "INSERT INTO spend (agent_id, day, usd) VALUES ('a', current_date, 1)"
            )
        with drv.expect_sqlstate("42501"):
            drv.execute(conn, "SELECT count(*) FROM runs")
    with drv.connect_admin(runtime_dsn) as admin:
        assert drv.execute(admin, "SELECT count(*) FROM pg_roles WHERE rolname = %s", (role,)) == [
            (0,)
        ]


def test_connect_role_with_no_grants_can_read_nothing_and_a_bad_privilege_is_refused(
    drv, runtime_dsn
):
    with drv.connect_role(runtime_dsn) as conn, drv.expect_sqlstate("42501"):
        drv.execute(conn, "SELECT count(*) FROM spend")
    bad = [("ALL", "spend")]
    with pytest.raises(ValueError, match="privilege"), drv.connect_role(runtime_dsn, grants=bad):
        pass
    with (
        pytest.raises(ValueError, match="search_path"),
        drv.connect_role("postgresql://example.invalid/db"),
    ):
        pass


def test_expect_sqlstate_passes_only_the_expected_code(drv, runtime_dsn):
    with drv.connect_admin(runtime_dsn) as admin:
        with drv.expect_sqlstate("42P01"):
            drv.execute(admin, "SELECT 1 FROM {}", idents=["no_such_table"])
        wrong = pytest.raises(AssertionError, match="expected SQLSTATE 23505, got 42P01")
        with wrong, drv.expect_sqlstate("23505"):
            drv.execute(admin, "SELECT 1 FROM {}", idents=["no_such_table"])
        nothing = pytest.raises(AssertionError, match="nothing was raised")
        with nothing, drv.expect_sqlstate("42P01"):
            drv.execute(admin, "SELECT 1")


def test_is_unique_violation_on_a_real_duplicate_and_on_made_up_errors(drv, runtime_dsn):
    with drv.connect_admin(runtime_dsn) as admin:
        drv.execute(admin, "CREATE TABLE {} (k int PRIMARY KEY)", idents=["u"])
        drv.execute(admin, "INSERT INTO {} VALUES (1)", idents=["u"])
        with pytest.raises(
            Exception
        ) as caught:  # the driver's own class is exactly what this helper hides
            drv.execute(admin, "INSERT INTO {} VALUES (1)", idents=["u"])
    assert drv.is_unique_violation(caught.value)
    assert drv.sqlstate(caught.value) == "23505"
    assert drv.is_unique_violation(drv.make_error("23505"))
    assert not drv.is_unique_violation(drv.make_error("40001"))
    assert not drv.is_unique_violation(ValueError("x"))


def test_make_error_carries_the_sqlstate_even_for_a_code_the_driver_does_not_know(drv):
    assert drv.sqlstate(drv.make_error("40001")) == "40001"
    assert drv.sqlstate(drv.make_error("40P01")) == "40P01"
    assert drv.sqlstate(drv.make_error("99999")) == "99999"
    assert drv.sqlstate(ValueError("plain")) is None
    assert isinstance(drv.make_error("40001"), Exception)


def test_make_dsn_and_dsn_parts_round_trip(drv):
    dsn = drv.make_dsn("postgresql://u@localhost:5432/db", user="v", options="-c search_path=s1")
    parts = drv.dsn_parts(dsn)
    assert (parts["user"], parts["host"], parts["port"], parts["dbname"]) == (
        "v",
        "localhost",
        "5432",
        "db",
    )
    assert parts["options"] == "-c search_path=s1"
    assert "password" not in parts


# --- order 101 item 4 -------------------------------------------------------------------------------------------
def _roles_and_schemas(drv):
    """The throw-away roles and schemas the helpers create, as the cluster lists them."""
    with drv.connect_admin(os.environ["HADAVIN_TEST_PG_DSN"]) as conn:
        roles = drv.execute(
            conn, "SELECT rolname FROM pg_roles WHERE rolname ~ '^(tr|rt|pu)_[0-9a-f]{{12}}$'"
        )
        schemas = drv.execute(
            conn, "SELECT nspname FROM pg_namespace WHERE nspname ~ '^t_[0-9a-f]{{12}}$'"
        )
    return {r[0] for r in roles}, {r[0] for r in schemas}


def test_connect_role_drops_the_role_when_a_grant_fails(drv, runtime_dsn):
    """Bug class: a half-built role left in the cluster (CREATE ROLE and the GRANT loop were outside the try).
    Killer of a mutant that moves them out of the try again."""
    before = _roles_and_schemas(drv)
    with (
        drv.expect_sqlstate("42P01"),
        drv.connect_role(runtime_dsn, grants=[("SELECT", "spend"), ("SELECT", "no_such_table")]),
    ):
        pytest.fail("the body must not be reached: the second grant fails")
    assert _roles_and_schemas(drv) == before


def test_connect_role_drops_the_role_when_the_body_raises(drv, runtime_dsn):
    before = _roles_and_schemas(drv)
    with pytest.raises(KeyError, match="boom"), drv.connect_role(runtime_dsn):
        raise KeyError("boom")
    assert _roles_and_schemas(drv) == before


@pytest.mark.parametrize(
    ("template", "idents", "needle"),
    [
        ("SELECT 1 FROM {}", (), "1 {} placeholders but 0 identifiers"),
        ("SELECT 1", ("spend",), "0 {} placeholders but 1 identifiers"),
        ("SELECT 1 FROM {} JOIN {}", ("spend",), "2 {} placeholders but 1 identifiers"),
        ("SELECT 1 FROM {name}", ("spend",), "only plain {} placeholders"),
        ("SELECT 1 FROM {0}", ("spend",), "only plain {} placeholders"),
        ("SELECT 1 FROM {:x}", ("spend",), "only plain {} placeholders"),
        ("SELECT 1 FROM {!r}", ("spend",), "only plain {} placeholders"),
    ],
)
def test_execute_refuses_a_placeholder_and_identifier_mismatch_with_a_clear_error(
    drv, runtime_dsn, template, idents, needle
):
    """Bug class: a silent mismatch (an extra identifier was ignored) or an opaque IndexError."""
    with (
        drv.connect_admin(runtime_dsn) as admin,
        pytest.raises(ValueError, match="execute:") as caught,
    ):
        drv.execute(admin, template, idents=idents)
    assert needle in str(caught.value)


def test_execute_takes_a_doubled_brace_as_a_literal_brace(drv, runtime_dsn):
    with drv.connect_admin(runtime_dsn) as admin:
        assert drv.execute(admin, "SELECT '{{\"a\": 1}}'::jsonb ->> 'a'") == [("1",)]


class _CursorSpy:
    """A connection that hands out cursors and keeps them, and has no `execute` (the old path)."""

    def __init__(self, conn):
        self.conn, self.cursors = conn, []

    def cursor(self):
        cur = self.conn.cursor()
        self.cursors.append(cur)
        return cur


def test_execute_closes_its_cursor_also_when_the_statement_fails(drv, runtime_dsn):
    """Bug class: a cursor left open until garbage collection. Killer of a mutant that does not close it."""
    with drv.connect_admin(runtime_dsn) as admin:
        spy = _CursorSpy(admin)
        assert drv.execute(spy, "SELECT 1") == [(1,)]
        assert drv.execute(spy, "CREATE TABLE {} (x int)", idents=["c1"]) == []
        with drv.expect_sqlstate("42P01"):
            drv.execute(spy, "SELECT 1 FROM {}", idents=["no_such_table"])
        assert len(spy.cursors) == 3
        assert all(cur.closed for cur in spy.cursors)


def test_pg_schema_removes_its_dsn_entries_and_schema_when_closed_and_when_thrown_into(drv):
    from tests.contracts.kinds.store_postgres import OWNER_DSN, PURGE_DSN

    for end in ("close", "throw"):
        before = _roles_and_schemas(drv)
        gen = pg_schema(runtime=True)
        dsn = next(gen)
        assert dsn in OWNER_DSN
        assert dsn in PURGE_DSN
        assert _roles_and_schemas(drv) != before
        if end == "close":
            gen.close()
        else:
            with pytest.raises(RuntimeError, match="planted"):
                gen.throw(RuntimeError("planted"))
        assert dsn not in OWNER_DSN
        assert dsn not in PURGE_DSN
        assert _roles_and_schemas(drv) == before


@pytest.mark.parametrize("runtime", [False, True])
def test_pg_schema_drops_what_it_made_when_migrate_fails(drv, monkeypatch, runtime):
    """Bug class: a failed set-up leaks the schema and the roles. `migrated=False` with `runtime` makes the
    roles first and fails in the second migrate call."""
    before = _roles_and_schemas(drv)

    def boom(*args, **kwargs):
        raise RuntimeError("planted migrate failure")

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", boom)
    with pytest.raises(RuntimeError, match="planted migrate failure"):
        next(pg_schema(migrated=not runtime, runtime=runtime))
    assert _roles_and_schemas(drv) == before
