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
import contextlib
import os
import re
import secrets
from collections.abc import Callable

from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

_ROLE_PREFIX = "hadavin_test_migrator_"
_MARK_BASE = (
    7_302_612_000_000_000  # advisory lock keys of live test processes: this plus the role's token
)
_MARKS: dict[
    str, object
] = {}  # per database (host, port, name): the marking connection (it holds the lock); kept open until the process ends
_TOKEN = secrets.token_hex(4)
PLAIN_ROLE = _ROLE_PREFIX + _TOKEN  # one per test process: a role and its grants belong to the
# whole server, so two test processes at once on one server (two Python versions, a mutant run) must not share one
_USED_DSNS: set[str] = (
    set()
)  # one entry per connection target (the search path is left out), not per scratch schema
SCRATCH_PREFIXES = (
    "hadavin_test_",
)  # schemas made by the test fixtures; the helper works on no other
_SETUP_LOCK = 7_302_611_944  # a key of its own: not the one of `migrate()`
_PASSWORD = secrets.token_hex(
    16
)  # made new for each test run; set on the role by the helper, never stored


class NotAScratchSchema(RuntimeError):
    """The test connection would take over a schema that is not a scratch schema of a test."""


def _target_key(dsn: str) -> str:
    """The connection target of a connection string: every connection setting EXCEPT `options` (the search path), so every
    scratch schema of one database is one entry. It keeps host, port, database, user, and also `sslmode`,
    `application_name` and a password written in the string. (A *server* in this file is the whole cluster: roles
    belong to it.)"""
    parts = conninfo_to_dict(dsn)
    parts.pop("options", None)
    return make_conninfo(**parts)


def _database_of(dsn: str) -> tuple:
    """Host, port and database name of a connection string, as written. The marking connection is kept once per database
    (not once per connection target): a second one in the same process would wait for the advisory lock that the first
    holds, for ever."""
    parts = conninfo_to_dict(dsn)
    return (parts.get("host", ""), parts.get("port", ""), parts.get("dbname", ""))


def _mark_key(token: str) -> int:
    """The lock key of a token. Only exactly eight lower-case hex digits are a token this helper made (`int(x, 16)`
    alone also reads signs, spaces and underscores)."""
    if not re.fullmatch(r"[0-9a-f]{8}", token):
        raise ValueError("not a token of this helper")
    return _MARK_BASE + int(token, 16)


def _mark_the_role(db) -> None:
    """Why a test run keeps one connection open: it is the proof that this run is alive, so that another run, which
    finds the role of this run still on the server, does not drop it.

    In detail, the mark is two things on one connection. The connection is named (`application_name`) like the role,
    because a role belongs to the whole server and `pg_stat_activity` shows every connection of the server (the sweep of
    stale roles reads that, whichever database it runs in). The connection also holds an advisory lock, a second proof
    inside its own database (a lock belongs to one database). The sweep never touches a role whose mark is there. One
    marking connection per database (`_database_of`), kept open until the process ends. If the marking
    connection has died (the database was dropped with FORCE, an idle limit, a restart, `pg_terminate_backend`) it is
    opened again here, because without it a parallel sweep would drop a role that is still in use. There is a short
    window between the death of the marking connection and the next connect in which a sweep of another test run can
    still drop the role; a test that is already running on it then fails (a stated window, not closed)."""
    import psycopg

    key = _database_of(db.info.dsn)  # no password in the key
    if key in _MARKS:
        mark = _MARKS[key]
        try:
            if not mark.closed:
                mark.execute("SELECT 1")
                return
        except psycopg.Error:
            pass
        with contextlib.suppress(psycopg.Error):
            mark.close()
        del _MARKS[key]
    mark = psycopg.connect(
        make_conninfo(db.info.dsn, password=db.info.password or None, application_name=PLAIN_ROLE),
        autocommit=True,
    )
    try:
        _take_the_mark(mark)
    except BaseException:
        mark.close()
        raise
    _MARKS[key] = mark


_MARK_WAIT_SECONDS = 15


def _take_the_mark(mark) -> None:
    """Take the advisory lock of this run on the marking connection, trying again for at most `_MARK_WAIT_SECONDS`. A
    blocking wait could hang the test setup for ever: when the old marking connection died half-open (a firewall drop, a
    cut network) the server may still hold its lock until it notices. A clear error ends the wait instead."""
    import time

    deadline = time.monotonic() + _MARK_WAIT_SECONDS
    while not mark.execute("SELECT pg_try_advisory_lock(%s)", (_mark_key(_TOKEN),)).fetchone()[0]:
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"the marking connection of this test run could not take its lock in {_MARK_WAIT_SECONDS} seconds: "
                "the server still holds the lock of an earlier marking connection of this run (a half-open connection). "
                "End that session on the server (pg_terminate_backend) and run the tests again."
            )
        time.sleep(0.2)


_CAN_SEE_SESSIONS_SQL = (
    "SELECT rolsuper OR pg_has_role(current_user, 'pg_read_all_stats', 'USAGE') FROM pg_roles "
    "WHERE rolname = current_user"
)


def _databases_that_still_hold(db, role: str) -> list[str]:
    """The databases (other than shared objects) in which `role` still owns something or holds a grant."""
    rows = db.execute(
        "SELECT DISTINCT d.datname FROM pg_shdepend s JOIN pg_database d ON d.oid = s.dbid "
        "WHERE s.refclassid = 'pg_authid'::regclass AND s.refobjid = (SELECT oid FROM pg_roles WHERE rolname = %s) "
        "ORDER BY 1",
        (role,),
    ).fetchall()
    return [r[0] for r in rows]


def sweep_stale_roles(db) -> list[str]:
    """Drop the test roles of earlier test processes that were killed before their exit hook ran: a role named
    `hadavin_test_migrator_<token>` that is not ours, has no session on the server (also none named like it: the mark of
    a live test process in any database of the server), whose live-process lock nobody holds, and that owns no schema of
    the current database except scratch schemas, nor any table, view, sequence, function or type in a schema that is not
    a scratch schema (a role of a person that happens to carry the name). What it owns in this database goes with it. Returns the names dropped.
    A role that cannot be dropped (it owns objects in another database too) is left and reported in one line that names
    those databases. A session that sets `application_name` can only keep a role, never drop one. Without the right to
    see the sessions of other users (a superuser or a member of `pg_read_all_stats`) a live role could look unused, so
    nothing is swept then."""
    import psycopg

    seen = db.execute(_CAN_SEE_SESSIONS_SQL).fetchone()
    if not seen or not seen[0]:
        print(
            "stale test roles were not looked for: this login is neither a superuser nor a member of pg_read_all_stats, "
            "so it cannot see the sessions of other test runs"
        )
        return []
    dropped = []
    rows = db.execute(
        "SELECT r.rolname FROM pg_roles r WHERE r.rolname LIKE %s AND r.rolname <> %s "
        "AND NOT EXISTS (SELECT 1 FROM pg_stat_activity a WHERE a.usename = r.rolname "
        "OR a.application_name = r.rolname) "
        "AND NOT EXISTS (SELECT 1 FROM (SELECT oid AS ns FROM pg_namespace WHERE nspowner = r.oid "
        "UNION ALL SELECT relnamespace FROM pg_class WHERE relowner = r.oid "
        "UNION ALL SELECT pronamespace FROM pg_proc WHERE proowner = r.oid "
        "UNION ALL SELECT typnamespace FROM pg_type WHERE typowner = r.oid) o JOIN pg_namespace n ON n.oid = o.ns "
        "AND NOT (n.nspname LIKE ANY(%s)))",
        (
            _ROLE_PREFIX.replace("_", "\\_") + "%",
            PLAIN_ROLE,
            [p.replace("_", "\\_") + "%" for p in SCRATCH_PREFIXES],
        ),
    ).fetchall()
    for (name,) in rows:
        token = name[len(_ROLE_PREFIX) :]
        try:
            key = _mark_key(token)
        except ValueError:
            continue  # not made by this helper
        if not db.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone()[0]:
            continue  # its process is alive
        try:
            try:
                with db.transaction():
                    db.execute(sql.SQL("DROP OWNED BY {} CASCADE").format(sql.Identifier(name)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))
                dropped.append(name)
            except psycopg.Error as e:
                try:
                    where = ", ".join(_databases_that_still_hold(db, name)) or "none found"
                # a login that may not read `pg_shdepend` must not fail the setup
                except psycopg.Error:
                    where = "not known (this login cannot read pg_shdepend)"
                print(
                    f"stale test role {name} was not dropped: {type(e).__name__}; it still holds objects in: {where}"
                )
        finally:
            try:
                db.execute("SELECT pg_advisory_unlock(%s)", (key,))
            except psycopg.Error:
                pass  # a broken connection must not fail the setup of a test
    return dropped


def _cluster_of(dsn: str) -> tuple:
    """The cluster a connection target belongs to, by host and port as written. A string with no host (the environment's
    PGHOST) and `host=localhost` count as two clusters: the effect is one more pass over the same cluster, harmless, because
    the drop of what a role owns and `DROP ROLE IF EXISTS` can be repeated."""
    parts = conninfo_to_dict(dsn)
    return (parts.get("host", ""), parts.get("port", ""))


def _drop_the_role_at_exit() -> None:
    """On a normal exit (also an exception or a `sys.exit`, not a kill: no hook runs then, and `sweep_stale_roles` of a
    later run takes care of it), take the role of this process off every server it was made on. A role belongs to the
    whole server but what it owns belongs to one database, so first what it owns is dropped in every database used
    (its grants go with it), and then the role is dropped once. A server that is gone or a role in use is reported in
    one line and does not fail the test run."""
    import psycopg

    env_dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
    by_server: dict[tuple, list[str]] = {}
    for dsn in sorted(_USED_DSNS | ({_target_key(env_dsn)} if env_dsn else set())):
        by_server.setdefault(_cluster_of(dsn), []).append(dsn)
    for dsns in by_server.values():
        try:
            for dsn in dsns:
                with psycopg.connect(dsn, autocommit=True) as db:
                    if not db.execute(
                        "SELECT 1 FROM pg_roles WHERE rolname = %s", (PLAIN_ROLE,)
                    ).fetchone():
                        break  # this server never saw the role
                    # CASCADE: a table another login (the test superuser) made inside a schema this role owns depends
                    # on that schema, and a plain DROP OWNED BY refuses to drop the schema then
                    db.execute(
                        sql.SQL("DROP OWNED BY {} CASCADE").format(sql.Identifier(PLAIN_ROLE))
                    )
            else:
                with psycopg.connect(dsns[0], autocommit=True) as db:
                    db.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(PLAIN_ROLE)))
        except (
            psycopg.Error
        ) as e:  # a server that is gone or a role in use must not fail the test run
            print(f"test role {PLAIN_ROLE} was not dropped: {type(e).__name__}")


def _close_the_marks() -> None:
    for mark in _MARKS.values():
        with contextlib.suppress(Exception):
            mark.close()
    _MARKS.clear()


atexit.register(
    _close_the_marks
)  # runs after the drop below (atexit runs the last registered first)
atexit.register(_drop_the_role_at_exit)


def _is_scratch(schema) -> bool:
    return bool(schema) and schema.startswith(SCRATCH_PREFIXES)


def scram_hash(db, role: str, password: str) -> str:
    """The SCRAM-SHA-256 verifier of `password` for `role`, made on this side, so a statement carries the hash and never
    the password (and the server log never holds it)."""
    return db.pgconn.encrypt_password(password.encode(), role.encode(), b"scram-sha-256").decode()


_PASSWORDS: dict[
    str, str
] = {}  # login role -> its password, for the roles this helper made or gave a hash


def set_login_password(db, role: str, password: str | None = None) -> str:
    """Give an existing login role a password (stored as a SCRAM hash made on this side) and remember it for
    `login_dsn`. For a role made by other SQL, for example the SQL the refusal message prints."""
    password = password or secrets.token_hex(16)
    hashed = scram_hash(db, role, password)
    db.execute(
        sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(role), sql.Literal(hashed))
    )
    _PASSWORDS[role] = password
    return password


def login_dsn(dsn: str, role: str, **parts) -> str:
    """The connection string that logs in as `role` (made by `create_login_role` or `set_login_password`), with its
    password, so the login also works on a server that asks for one. Every test login goes through this."""
    return make_conninfo(dsn, user=role, password=_PASSWORDS[role], **parts)


def create_login_role(db, role: str, password: str | None = None) -> str:
    """Make a plain login role (none of the five flags) whose password is a SCRAM hash, so it also logs in on a server
    that asks for a password; on a server that trusts the connection (the CI service) the password is not asked. Returns
    the password (new for each call unless one is given)."""
    password = password or secrets.token_hex(16)
    db.execute(
        sql.SQL(
            "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS NOREPLICATION PASSWORD {}"
        ).format(sql.Identifier(role), sql.Literal(scram_hash(db, role, password)))
    )
    _PASSWORDS[role] = password
    return password


def ensure_plain_role(db) -> None:
    """Make the login role once: look in `pg_roles` first, and only create it when it is missing (a role belongs to the
    whole server, so an earlier test of this process may have made it). The password is sent as a SCRAM hash made on
    this side, so the password itself is in no statement and never reaches the server log, and the role is never
    created or changed a second time (a repeated `CREATE ROLE` fails on the server, and the server logs the failed
    statement). Before the first creation, the roles that killed test processes left are swept."""
    if db.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (PLAIN_ROLE,)).fetchone():
        return
    _mark_the_role(db)
    sweep_stale_roles(db)
    create_login_role(db, PLAIN_ROLE, _PASSWORD)


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
                _mark_the_role(
                    db
                )  # also when the role exists: a marking connection that died is opened again
                ensure_plain_role(db)
                _USED_DSNS.add(_target_key(dsn))
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
