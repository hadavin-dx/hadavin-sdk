"""T-E1: the read-only login (control C2). Each REVOKE is exercised as the login itself.

The connection overrides default_transaction_read_only to off, so the READ ONLY default cannot be what stops a
write: only the revoked privileges can.
"""

import psycopg
import pytest

# A class-42 error (42501 insufficient_privilege is the expected one) means the database refused the statement.
DENIED = [
    "INSERT INTO shop.orders VALUES (9999, 1, DATE '2026-01-01', 'paid', 1)",
    "UPDATE shop.orders SET status = 'x'",
    "DELETE FROM shop.orders",
    "TRUNCATE shop.orders",
    "DROP TABLE shop.orders",
    "CREATE TABLE analytics.t (x integer)",
    "CREATE TABLE public.t (x integer)",
    "CREATE TEMP TABLE t (x integer)",
    "SELECT * FROM shop.customers",
    "SELECT email FROM shop.customers",
    "SELECT * FROM pg_shadow",
    "SELECT pg_read_file('postgresql.conf')",
    "COPY (SELECT 1) TO PROGRAM 'echo x'",
    "INSERT INTO analytics.orders_v VALUES (9999, 1, DATE '2026-01-01', 'paid', 1)",
    "UPDATE analytics.orders_v SET status = 'x'",
    "DROP VIEW analytics.orders_v",
]
VIEWS = ["customers_v", "products_v", "orders_v", "order_items_v"]


def _ro(db):
    return psycopg.connect(
        db.ro_dsn, autocommit=True, options="-c default_transaction_read_only=off"
    )


@pytest.mark.parametrize("sql", DENIED)
def test_denied_for_the_login(db, sql):
    with _ro(db) as conn, pytest.raises(psycopg.Error) as caught:
        conn.execute(sql)
    assert caught.value.sqlstate == "42501", caught.value.sqlstate


@pytest.mark.parametrize("view", VIEWS)
def test_each_view_can_be_selected(db, view):
    with _ro(db) as conn:
        assert conn.execute(f"SELECT count(*) FROM analytics.{view}").fetchone()[0] > 0  # noqa: S608


def test_role_defaults_are_set_but_are_only_defaults(db):
    with psycopg.connect(db.ro_dsn, autocommit=True) as conn:
        assert conn.execute("SHOW default_transaction_read_only").fetchone()[0] == "on"
        assert conn.execute("SHOW transaction_read_only").fetchone()[0] == "on"
    with _ro(db) as conn:  # a session can override a default; that is why privileges are what holds
        assert conn.execute("SHOW transaction_read_only").fetchone()[0] == "off"


def test_roles_script_refuses_without_confirm(make_db):
    env = make_db(apply_roles=False)
    done = env.roles_sql()
    assert done.returncode == 3, done.stderr
    assert "refusing" in done.stderr


def test_preflight_stops_when_another_login_would_lose_access(make_db):
    env = make_db(apply_roles=False)
    other = env.name + "_other"
    with env.admin() as conn:
        conn.execute(f'CREATE ROLE "{other}" LOGIN')  # holds CONNECT/TEMP only through PUBLIC
        conn.execute(
            "CREATE FUNCTION public.askdata_fn_probe() RETURNS int LANGUAGE sql AS 'SELECT 1'"
        )
        conn.execute(
            f'ALTER DEFAULT PRIVILEGES FOR ROLE "{other}" IN SCHEMA public GRANT SELECT ON TABLES TO "{other}"'
        )
    try:
        refused = env.roles_sql("-v", "confirm_dedicated=yes")
        assert refused.returncode == 3, refused.stderr
        assert (
            other in refused.stdout and "PUBLIC" in refused.stdout
        )  # the listing names the login and the path
        assert "accept_loss" in refused.stderr
        assert "askdata_fn_probe" in refused.stdout  # the PUBLIC-executable function listing
        assert f"{other} | public | r |" in refused.stdout  # the pg_default_acl listing
        accepted = env.roles_sql("-v", "confirm_dedicated=yes", "-v", "accept_loss=yes")
        assert accepted.returncode == 0, accepted.stderr
    finally:
        with env.admin() as conn:
            conn.execute("DROP FUNCTION IF EXISTS public.askdata_fn_probe()")
            conn.execute(f'DROP OWNED BY "{other}"')
            conn.execute(f'DROP ROLE "{other}"')
