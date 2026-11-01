"""Fixtures for the Ask-your-data demo tests. No live API call is made anywhere: the model is the scripted fake.

The database fixture creates a uniquely named database and roles (`askdata_t_` + 8 hex) with random passwords on
the Postgres named by HADAVIN_TEST_PG_DSN (the CI service, or a local container), applies the demo scripts, and
drops everything in a finalizer. Without the variable the DB tests skip on a laptop and FAIL when CI=true.
"""

from __future__ import annotations

import importlib.util
import os
import secrets
import shutil
import subprocess  # runs psql with a fixed argument list, never a shell
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

DEMO = Path(__file__).resolve().parents[2] / "demos" / "ask-your-data"
sys.path.insert(0, str(DEMO))


def load_script(name: str):
    """Import db/<name>.py by path (db/ is a folder of scripts, not a package)."""
    spec = importlib.util.spec_from_file_location(f"askdata_db_{name}", DEMO / "db" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _need(reason: str) -> None:
    if os.environ.get("CI") == "true":
        pytest.fail(reason, pytrace=False)
    pytest.skip(reason)


@pytest.fixture(scope="session")
def admin_dsn() -> str:
    dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
    if not dsn:
        _need("HADAVIN_TEST_PG_DSN is not set (the CI postgres service, or a local container)")
    return dsn


@pytest.fixture(scope="session")
def psql() -> str:
    found = os.environ.get("PSQL") or shutil.which("psql")
    if not found:
        _need("psql not found: install the PostgreSQL client or set PSQL to its path")
    return found


def _split(dsn: str) -> tuple[str, str, str | None]:
    """(connection string without user and password, admin user, admin password)."""
    parts = conninfo_to_dict(dsn)
    user, pw = parts.pop("user", "postgres"), parts.pop("password", None)
    return make_conninfo(**parts), user, pw or None


@dataclass
class Db:
    name: str
    base: str  # host, port and sslmode only
    admin_user: str
    admin_pw: str | None
    ro_role: str
    ro_password: str
    psql: str

    def dsn(self, user: str, password: str | None) -> str:
        return make_conninfo(
            self.base, dbname=self.name, user=user, **({"password": password} if password else {})
        )

    @property
    def admin_dsn(self) -> str:
        return self.dsn(self.admin_user, self.admin_pw)

    @property
    def ro_dsn(self) -> str:
        return self.dsn(self.ro_role, self.ro_password)

    def run_psql(self, user: str, password: str | None, *args: str, stdin: str | None = None):
        """Run psql as `user`; the password travels in PGPASSWORD, never in the arguments."""
        conninfo = make_conninfo(self.base, dbname=self.name, user=user)
        env = {**os.environ, "PGPASSWORD": password or ""}
        return subprocess.run(  # noqa: S603  # fixed argument list, no shell
            [self.psql, "-w", "-X", "-q", *args, conninfo], input=stdin, text=True, capture_output=True,
            **({} if stdin is not None else {"stdin": subprocess.DEVNULL}), env=env, check=False, timeout=120,
        )  # fmt: skip

    def create_login(self, role: str, password: str, *grants: str) -> str:
        """A LOGIN role with CONNECT on this database plus the given GRANT bodies; returns its DSN."""
        with self.admin() as conn:
            conn.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
            conn.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(self.name), sql.Identifier(role)
                )
            )
            for grant in grants:  # trusted literals from the tests, e.g. "USAGE ON SCHEMA scratch"
                conn.execute(sql.SQL("GRANT {} TO {}").format(sql.SQL(grant), sql.Identifier(role)))
        return self.dsn(role, password)

    def admin(self) -> psycopg.Connection:
        return psycopg.connect(self.admin_dsn, autocommit=True)

    def roles_sql(self, *extra: str):
        """Run db/roles.sql as the admin with the given -v options; returns the CompletedProcess."""
        return self.run_psql(
            self.admin_user, self.admin_pw, "-v", f"ro_role={self.ro_role}", "-v", f"ro_password={self.ro_password}",
            *extra, "-f", str(DEMO / "db" / "roles.sql"),
        )  # fmt: skip


@pytest.fixture(scope="session")
def make_db(admin_dsn: str, psql: str) -> Iterator[Callable[..., Db]]:
    """Factory: a fresh database with schema, seed and views (roles optional). Cleans up at session end."""
    made: list[tuple[str, str]] = []
    seed = load_script("seed")
    base, admin_user, admin_pw = _split(admin_dsn)
    maint = make_conninfo(
        base, dbname="postgres", user=admin_user, **({"password": admin_pw} if admin_pw else {})
    )

    def factory(*, apply_roles: bool = True) -> Db:
        tag = "askdata_t_" + secrets.token_hex(4)
        ro_role, ro_pw = tag + "_ro", secrets.token_urlsafe(18)
        with psycopg.connect(maint, autocommit=True) as c:
            c.execute(f'CREATE DATABASE "{tag}"')  # tag is generated here, not input
        made.append((tag, ro_role))
        env = Db(tag, base, admin_user, admin_pw, ro_role, ro_pw, psql_path)
        with env.admin() as c:
            c.execute((DEMO / "db" / "schema.sql").read_text(encoding="utf-8"))
            for stmt in seed.sql_statements():
                c.execute(stmt)
            c.execute((DEMO / "db" / "views.sql").read_text(encoding="utf-8"))
            c.execute("CREATE SCHEMA scratch; CREATE TABLE scratch.marker (v integer)")
        if apply_roles:
            done = env.roles_sql("-v", "confirm_dedicated=yes", "-v", "accept_loss=yes")
            assert done.returncode == 0, done.stderr[-800:]
        return env

    psql_path = psql
    yield factory
    with psycopg.connect(maint, autocommit=True) as c:
        for tag, ro_role in made:
            c.execute(f'DROP DATABASE IF EXISTS "{tag}" WITH (FORCE)')
            for role in (ro_role, tag + "_rw", tag + "_scratch"):
                c.execute(f'DROP ROLE IF EXISTS "{role}"')


@pytest.fixture(scope="session")
def db(make_db: Callable[..., Db]) -> Db:
    return make_db()


@pytest.fixture(scope="session")
def rw_login(db: Db) -> tuple[str, str]:
    """A login that HAS write privilege on scratch.marker: only the layers below the validator stop it."""
    role, pw = db.name + "_rw", secrets.token_urlsafe(18)
    dsn = db.create_login(role, pw, "USAGE ON SCHEMA scratch", "INSERT, SELECT ON scratch.marker")
    return dsn, role
