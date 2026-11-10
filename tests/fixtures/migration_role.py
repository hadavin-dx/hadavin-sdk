"""A test-only way to run `migrate()` as a plain migration role.

`migrate()` always refuses a migration role that is a superuser or holds CREATEROLE, CREATEDB or BYPASSRLS, and has no
switch to turn that off. The test databases are reached with a superuser login (the CI service and a laptop cluster), so
the tests swap `store.migrate.connect` for `plain_role_connect(...)`: it connects as given, and when the login is a
superuser it makes sure the plain role `PLAIN_ROLE` exists, makes it the owner of the schema in use (so that the rights it grants are its own) and connects again AS that
role (a login, so the session user is the plain role). `migrate()` is called exactly as in production and its signature is untouched. A test that proves the
refusal carries the marker `real_connect` and sees the unchanged `connect`.

WARNING: for a throwaway test server only. When the login is a superuser, `plain_role_connect` CHANGES THE OWNER of the
schema in use and creates a role on the server. It therefore refuses (raises `NotAScratchSchema`) when the schema in use
does not start with the scratch prefix (`SCRATCH_PREFIXES`), because that is not a scratch schema of a test. Never point
`HADAVIN_TEST_PG_DSN` at a database that holds real data."""

from __future__ import annotations

import atexit
import os
import secrets
from collections.abc import Callable

from psycopg import sql
from psycopg.conninfo import make_conninfo

PLAIN_ROLE = "hadavin_test_migrator_" + secrets.token_hex(
    4
)  # one per test process: a role and its grants belong to the
# whole server, so two test processes at once on one server (two Python versions, a mutant run) must not share one
_USED_DSNS: set[str] = set()
SCRATCH_PREFIXES = (
    "hadavin_test_",
)  # schemas made by the test fixtures; the helper works on no other
_SETUP_LOCK = 7_302_611_944  # a key of its own: not the one of `migrate()`
_PASSWORD = secrets.token_hex(
    16
)  # made new for each test run; set on the role by the helper, never stored


class NotAScratchSchema(RuntimeError):
    """The test connection would take over a schema that is not a scratch schema of a test."""


def _drop_the_role_at_exit() -> None:
    """Take the role of this process off every server it was made on (what it owns and its grants go with it). A server
    that is gone or a role in use is reported in one line and does not fail the test run."""
    import psycopg

    env_dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
    for dsn in _USED_DSNS | ({env_dsn} if env_dsn else set()):
        try:
            with psycopg.connect(dsn, autocommit=True) as db:
                if not db.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s", (PLAIN_ROLE,)
                ).fetchone():
                    continue  # this server never saw the role
                # CASCADE: a table another login (the test superuser) made inside a schema this role owns depends on
                # that schema, and a plain DROP OWNED BY refuses to drop the schema then
                db.execute(sql.SQL("DROP OWNED BY {} CASCADE").format(sql.Identifier(PLAIN_ROLE)))
                db.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(PLAIN_ROLE)))
        except (
            psycopg.Error
        ) as e:  # a server that is gone or a role in use must not fail the test run
            print(f"test role {PLAIN_ROLE} was not dropped: {type(e).__name__}")


atexit.register(_drop_the_role_at_exit)


def _is_scratch(schema) -> bool:
    return bool(schema) and schema.startswith(SCRATCH_PREFIXES)


def ensure_plain_role(db) -> None:
    """Make the login role once: look in `pg_roles` first, and only create it when it is missing (a role belongs to the
    whole server, so an earlier test of this process may have made it). The password is sent as a SCRAM hash made on
    this side, so the password itself is in no statement and never reaches the server log, and the role is never
    created or changed a second time (a repeated `CREATE ROLE` fails on the server, and the server logs the failed
    statement)."""
    if db.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (PLAIN_ROLE,)).fetchone():
        return
    hashed = db.pgconn.encrypt_password(
        _PASSWORD.encode(), PLAIN_ROLE.encode(), b"scram-sha-256"
    ).decode()
    db.execute(
        sql.SQL(
            "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS PASSWORD {}"
        ).format(sql.Identifier(PLAIN_ROLE), sql.Literal(hashed))
    )


def plain_role_connect(real_connect: Callable) -> Callable:
    """When the login is a superuser: make the plain LOGIN role and its schema ownership, then connect AS that role (the
    session user is the plain role, as in production). Any other login is used as given."""

    def connect(dsn, **kwargs):
        db = real_connect(dsn, **kwargs)
        try:
            row = db.execute(
                "SELECT rolsuper FROM pg_roles WHERE rolname = session_user"
            ).fetchone()
            if row is None or not row[0]:
                return db
            with (
                db.transaction()
            ):  # one at a time: two threads of a test make the role and the owner together
                db.execute("SELECT pg_advisory_xact_lock(%s)", (_SETUP_LOCK,))
                schema = db.execute("SELECT current_schema()").fetchone()[0]
                if not _is_scratch(schema):
                    raise NotAScratchSchema(
                        f"the schema in use is {schema!r}: the test helper changes the owner of the schema in use, "
                        f"so it only runs on a scratch schema of a test (its name starts with one of {SCRATCH_PREFIXES!r})"
                    )
                ensure_plain_role(db)
                _USED_DSNS.add(dsn)
                db.execute(
                    sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                        sql.Identifier(schema), sql.Identifier(PLAIN_ROLE)
                    )
                )
        except BaseException:
            db.close()
            raise
        db.close()
        return real_connect(make_conninfo(dsn, user=PLAIN_ROLE, password=_PASSWORD), **kwargs)

    return connect
