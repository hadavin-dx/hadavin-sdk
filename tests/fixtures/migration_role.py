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
import re
import secrets
from collections.abc import Callable

from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

_ROLE_PREFIX = "hadavin_test_migrator_"
_HOLD_BASE = (
    7_302_612_000_000_000  # advisory lock keys of live test processes: this plus the role's token
)
_HOLDS: dict[
    str, object
] = {}  # per connection target: the connection that holds that lock; kept open until the process ends
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
    """The connection target of a connection string: host, port, database and user, without its search path, so every
    scratch schema of one database is one entry. (A *server* in this file is the whole cluster: roles belong to it.)"""
    parts = conninfo_to_dict(dsn)
    parts.pop("options", None)
    return make_conninfo(**parts)


def _hold_key(token: str) -> int:
    """The lock key of a token. Only exactly eight lower-case hex digits are a token this helper made (`int(x, 16)`
    alone also reads signs, spaces and underscores)."""
    if not re.fullmatch(r"[0-9a-f]{8}", token):
        raise ValueError("not a token of this helper")
    return _HOLD_BASE + int(token, 16)


def _hold_the_role(db) -> None:
    """A test run keeps one connection open, named after its role, so other runs can tell the role is still in use.

    In detail: a role belongs to the whole server, but an advisory lock belongs to one database, so the mark is two
    things: the connection is named (`application_name`) like the role, and `pg_stat_activity` shows every connection
    of the server (the sweep of stale roles reads that, whichever database it runs in); an advisory lock is held on top
    (a second proof inside this database). The sweep never touches a role whose mark is there. One connection per
    connection target (host, port, database and user), kept open until the process ends."""
    import psycopg

    key = _target_key(db.info.dsn)  # no password in the key
    if key in _HOLDS:
        return
    hold = psycopg.connect(
        make_conninfo(db.info.dsn, password=db.info.password or None, application_name=PLAIN_ROLE),
        autocommit=True,
    )
    try:
        hold.execute("SELECT pg_advisory_lock(%s)", (_hold_key(_TOKEN),))
    except BaseException:
        hold.close()
        raise
    _HOLDS[key] = hold


_CAN_SEE_SESSIONS_SQL = (
    "SELECT rolsuper OR pg_has_role(current_user, 'pg_read_all_stats', 'MEMBER') FROM pg_roles "
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
    the current database except scratch schemas. What it owns in this database goes with it. Returns the names dropped.
    A role that cannot be dropped (it owns objects in another database too) is left and reported in one line that names
    those databases. A session that sets `application_name` can only keep a role, never drop one. Without the right to
    see the sessions of other users (a superuser or a member of `pg_read_all_stats`) a live role could look unused, so
    nothing is swept then."""
    import psycopg

    seen = db.execute(_CAN_SEE_SESSIONS_SQL).fetchone()
    if not seen or not seen[0]:
        return []
    dropped = []
    rows = db.execute(
        "SELECT r.rolname FROM pg_roles r WHERE r.rolname LIKE %s AND r.rolname <> %s "
        "AND NOT EXISTS (SELECT 1 FROM pg_stat_activity a WHERE a.usename = r.rolname "
        "OR a.application_name = r.rolname) "
        "AND NOT EXISTS (SELECT 1 FROM pg_namespace n WHERE n.nspowner = r.oid AND NOT (n.nspname LIKE ANY(%s)))",
        (
            _ROLE_PREFIX.replace("_", "\\_") + "%",
            PLAIN_ROLE,
            [p.replace("_", "\\_") + "%" for p in SCRATCH_PREFIXES],
        ),
    ).fetchall()
    for (name,) in rows:
        token = name[len(_ROLE_PREFIX) :]
        try:
            key = _hold_key(token)
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
                where = ", ".join(_databases_that_still_hold(db, name)) or "none found"
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
    """The server (cluster) a connection target belongs to: host and port."""
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


def _close_the_hold() -> None:
    for hold in _HOLDS.values():
        hold.close()
    _HOLDS.clear()


atexit.register(
    _close_the_hold
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
    _hold_the_role(db)
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
