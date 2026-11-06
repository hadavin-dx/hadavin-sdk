"""P4d-a1: the neutral driver namespace `pg_driver()` (tests use it and never import the driver)."""

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
