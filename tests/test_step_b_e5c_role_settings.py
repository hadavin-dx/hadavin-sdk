"""E5c (review 6, R6-2): `migrate` must not erase a named role's cluster-wide search_path default (it reaches every
database of the server). For a role-wide row that is not the migrated schema it writes
`ALTER ROLE r IN DATABASE <this database> SET search_path = <schema>` (higher precedence, this database only), never
touches a role that is not named, and reports what it changed. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from hadavin_sdk.store.migrate import migrate
from tests.test_stop_state_roles import stop_world  # noqa: F401 - the fixture

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


def _rows(w, role):
    """{database name or None: search_path value} of the role's search_path defaults."""
    with psycopg.connect(w.dsn, autocommit=True) as db:
        return {
            r[0]: r[1].split("=", 1)[1]
            for r in db.execute(
                "SELECT d.datname, c FROM pg_db_role_setting s JOIN pg_roles r ON r.oid = s.setrole "
                "LEFT JOIN pg_database d ON d.oid = s.setdatabase, unnest(s.setconfig) c "
                "WHERE r.rolname = %s AND c LIKE 'search\\_path=%%'",
                (role,),
            ).fetchall()
        }


def _set_wide(w, role, value):
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("ALTER ROLE {} SET search_path = {}").format(
                sql.Identifier(role), sql.Identifier(value)
            )
        )


def _dbname(w):
    with psycopg.connect(w.dsn) as db:
        return db.info.dbname


def test_a_role_wide_default_survives_and_this_database_is_pinned_to_the_schema(w):
    _set_wide(w, w.runtime, "other_app")
    seen = []
    w.migrate(on_role_change=seen.append)
    rows = _rows(w, w.runtime)
    assert rows[None] == "other_app"  # other databases keep their setting
    assert rows[_dbname(w)] == w.schema  # this database is pinned
    assert len(seen) == 1
    for part in (w.runtime, _dbname(w), "other_app", w.schema):
        assert part in seen[0]


def test_a_second_migrate_changes_nothing_more(w):
    _set_wide(w, w.runtime, "other_app")
    w.migrate()
    seen = []
    w.migrate(on_role_change=seen.append)
    assert seen == []
    assert _rows(w, w.runtime)[None] == "other_app"


def test_a_role_that_is_not_named_is_never_touched(w):
    other = w.new_role("other")
    _set_wide(w, other, "other_app")
    _set_wide(w, w.runtime, "other_app")
    w.migrate()
    assert _rows(w, other) == {None: "other_app"}


def test_the_migrate_return_is_still_the_applied_list(w):
    _set_wide(w, w.runtime, "other_app")
    assert w.migrate() == []  # already migrated by the fixture: nothing applied
    assert migrate is not None
