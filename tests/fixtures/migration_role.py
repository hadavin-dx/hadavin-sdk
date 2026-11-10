"""A test-only way to run `migrate()` as a plain migration role.

`migrate()` always refuses a migration role that is a superuser or holds CREATEROLE, CREATEDB or BYPASSRLS, and has no
switch to turn that off. The test databases are reached with a superuser login (the CI service and a laptop cluster), so
the tests swap `store.migrate.connect` for `plain_role_connect(...)`: it connects as given, and when the login is a
superuser it makes sure the plain role `PLAIN_ROLE` exists, makes it the owner of the schema in use (so that the rights it grants are its own) and runs
`SET ROLE` to it. `migrate()` is called exactly as in production and its signature is untouched. A test that proves the
refusal carries the marker `real_connect` and sees the unchanged `connect`.

WARNING: for a throwaway test server only. When the login is a superuser, `plain_role_connect` CHANGES THE OWNER of the
schema in use and creates a role on the server. It therefore refuses (raises `NotAScratchSchema`) when the schema in use
is `public`, a system schema, or not set, because that is not a scratch schema of a test. Never point
`HADAVIN_TEST_PG_DSN` at a database that holds real data."""

from __future__ import annotations

from collections.abc import Callable

from psycopg import errors as pg_errors
from psycopg import sql

PLAIN_ROLE = "hadavin_test_migrator"
_SETUP_LOCK = 7_302_611_944  # a key of its own: not the one of `migrate()`


class NotAScratchSchema(RuntimeError):
    """The test connection would take over a schema that is not a scratch schema of a test."""


def _is_scratch(schema) -> bool:
    return (
        bool(schema)
        and schema != "public"
        and not schema.startswith("pg_")
        and schema != "information_schema"
    )


def ensure_plain_role(db) -> None:
    """Make the role if it is not there (a role belongs to the whole server, so an earlier test may have made it)."""
    try:
        with db.transaction():  # a savepoint when the caller is already in a transaction
            db.execute(
                sql.SQL(
                    "CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS"
                ).format(sql.Identifier(PLAIN_ROLE))
            )
    except (pg_errors.DuplicateObject, pg_errors.UniqueViolation):
        pass


def plain_role_connect(real_connect: Callable) -> Callable:
    def connect(dsn, **kwargs):
        db = real_connect(dsn, **kwargs)
        try:
            row = db.execute(
                "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"
            ).fetchone()
            if row is not None and row[0]:
                role = sql.Identifier(PLAIN_ROLE)
                with (
                    db.transaction()
                ):  # one at a time: two threads of a test make the role and the owner together
                    db.execute("SELECT pg_advisory_xact_lock(%s)", (_SETUP_LOCK,))
                    schema = db.execute("SELECT current_schema()").fetchone()[0]
                    if not _is_scratch(schema):
                        raise NotAScratchSchema(
                            f"the schema in use is {schema!r}: the test helper changes the owner of the schema in use, "
                            "so it only runs on a scratch schema of a test (set search_path to one first)"
                        )
                    ensure_plain_role(db)
                    db.execute(
                        sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(schema), role)
                    )
                db.execute(sql.SQL("SET ROLE {}").format(role))
        except BaseException:
            db.close()
            raise
        return db

    return connect
