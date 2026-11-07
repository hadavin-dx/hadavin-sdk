"""The `postgres` store kind. Needs HADAVIN_TEST_PG_DSN (CI: the postgres service). Without it the kind skips on a
laptop (no Docker needed) and fails under the fail rule (`HADAVIN_REQUIRE_PG` or `CI`, see `require_backend`).
Each test gets its own schema, migrated fresh and dropped afterwards, also when the set-up fails half way."""

import contextlib
import re
import string
import uuid
from collections.abc import Sequence
from types import SimpleNamespace

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from tests.contracts.kinds import kind, pg_test_dsn, require_backend

# runtime DSN -> the DSN of the purge role of the same schema (only for `pg_schema(runtime=True)`)
PURGE_DSN: dict[str, str] = {}
# runtime DSN -> the DSN of the owner login of the same schema (what `connect_admin` uses for a runtime DSN)
OWNER_DSN: dict[str, str] = {}


def pg_schema(migrated=True, runtime=False):
    """Yield a DSN whose search_path is a fresh (migrated) schema; drop the schema afterwards. With `runtime`,
    yield instead the DSN of a new non-owner login role that `migrate` granted its runtime rights (K2: the store
    suite must pass with only those rights); the role is dropped afterwards. Everything created is dropped in the
    `finally`, also when `migrate` or a role creation fails (a failed set-up must not leave a schema or a role
    behind), and the DSN entries of `OWNER_DSN` and `PURGE_DSN` go with it. Each clean-up statement is tried even
    when an earlier one failed; the first failure is raised after all were tried."""
    dsn = pg_test_dsn()  # fails under HADAVIN_REQUIRE_PG or CI, else skips
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.migrate import migrate

    schema = f"t_{uuid.uuid4().hex[:12]}"
    scoped = make_conninfo(dsn, options=f"-c search_path={schema}")
    created_roles: list[str] = []
    runtime_dsn = None
    try:
        with psycopg.connect(dsn, autocommit=True) as db:
            db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        if migrated:
            migrate(scoped)
        if runtime:
            role, purge = "rt_" + uuid.uuid4().hex[:12], "pu_" + uuid.uuid4().hex[:12]
            with psycopg.connect(dsn, autocommit=True) as db:
                for r in (role, purge):
                    db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
                    created_roles.append(r)
            migrate(scoped, runtime_role=role, purge_role=purge)
            runtime_dsn = make_conninfo(scoped, user=role)
            PURGE_DSN[runtime_dsn] = make_conninfo(scoped, user=purge)
            OWNER_DSN[runtime_dsn] = scoped
            yield runtime_dsn
        else:
            yield scoped
    finally:
        if runtime_dsn is not None:
            PURGE_DSN.pop(runtime_dsn, None)
            OWNER_DSN.pop(runtime_dsn, None)
        failures: list[psycopg.Error] = []

        def drop(db, template, name):
            """One clean-up statement; a failure is kept and the next statement still runs."""
            try:
                db.execute(sql.SQL(template).format(sql.Identifier(name)))
            except psycopg.Error as exc:
                failures.append(exc)

        try:
            with psycopg.connect(dsn, autocommit=True) as db:
                for r in created_roles:
                    drop(db, "DROP OWNED BY {}", r)
                    drop(db, "DROP ROLE {}", r)
                drop(db, "DROP SCHEMA IF EXISTS {} CASCADE", schema)
        except psycopg.Error as exc:  # the connection itself failed or would not close
            failures.append(exc)
        if failures:
            raise failures[0]


class _SplitStore:
    """The runtime role for everything, the purge role for the two purges: as `app.build` wires them
    (`purge_dsn_secret_name`), so the suite runs with each identity holding only its own rights."""

    def __init__(self, main, purge, runtime_dsn):
        self._main, self._purge, self.runtime_dsn = main, purge, runtime_dsn

    def __getattr__(self, name):
        return getattr(self._main, name)

    def purge_tool_calls(self, *a, **k):
        return self._purge.purge_tool_calls(*a, **k)

    def purge_redaction_maps(self, *a, **k):
        return self._purge.purge_redaction_maps(*a, **k)

    @property
    def connection_id(self):
        """The server process ids of the two connections: what a test compares to see that two handles do not
        share a connection, without naming the driver or reaching into a store's private field."""
        return (self._main._db.info.backend_pid, self._purge._db.info.backend_pid)

    def close(self):
        self._main._db.close()
        self._purge._db.close()


def _open_split(dsn):
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
    store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
    purge_store = make("store", settings, FakeSecretProvider({"pg-dsn": PURGE_DSN[dsn]}))
    return _SplitStore(store, purge_store, dsn)


@kind("store", "postgres")
def postgres(tmp_path):
    for dsn in pg_schema(runtime=True):
        store = _open_split(dsn)
        yield store
        store.close()


@kind("store_pair", "postgres")
def postgres_pair(tmp_path):
    """Two independent handles (two connections each) on one schema: a race test then tests the SQL, not the
    in-process lock of one handle."""
    for dsn in pg_schema(runtime=True):
        a, b = _open_split(dsn), _open_split(dsn)
        yield a, b
        a.close()
        b.close()


# --- the neutral driver namespace (P4d-a1). The tests of the contract suite use this and never import the driver.
# The driver is named in this module and, as the constant `PG_DRIVER_MODULE`, in `kinds/__init__.py`; older test
# files outside `tests/contracts` still import it themselves, and P4d-c moves them here and then makes a guard
# test enforce the two-name allow-list. -----------------------------------------------------------------------

_PRIVILEGES = frozenset({"SELECT", "INSERT", "UPDATE", "DELETE"})


def pg_driver(*, module_level=False):
    """A small namespace of neutral operations (never the driver module itself). It skips, or fails under the fail
    rule, when the driver is not installed; it does NOT need a database (`dsn=False`), so the functions that
    connect are the ones that need `HADAVIN_TEST_PG_DSN`, through the DSN a fixture hands them.
    `module_level=True` is for a call at the top of a test module."""
    require_backend("postgres", dsn=False, module_level=module_level)
    import psycopg
    from psycopg import errors, sql
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    def ident(name):
        return sql.Identifier(name)

    def connect_admin(dsn, *, autocommit=True):
        """The owner login. Given the DSN of a runtime login made by `pg_schema(runtime=True)`, the owner login
        of the same schema; any other DSN is used as it is."""
        return psycopg.connect(OWNER_DSN.get(dsn, dsn), autocommit=autocommit)

    def connect_runtime(dsn, *, autocommit=True):
        """The runtime login of a fixture schema. `dsn` must be the one `pg_schema(runtime=True)` yielded."""
        if dsn not in OWNER_DSN:
            raise ValueError("connect_runtime needs the DSN that pg_schema(runtime=True) yielded")
        return psycopg.connect(dsn, autocommit=autocommit)

    @contextlib.contextmanager
    def connect_role(dsn, *, grants: Sequence[tuple[str, str]] = ()):
        """A throw-away login role with EXACTLY `grants` (pairs of privilege and table, in the schema of `dsn`)
        and usage on that schema; yields its connection; drops the role afterwards. The role is dropped also
        when one of the grants fails (bug class: a half-built role left in the cluster)."""
        owner = OWNER_DSN.get(dsn, dsn)
        found = re.search(r"search_path=(\w+)", conninfo_to_dict(owner).get("options", ""))
        if not found:
            raise ValueError("connect_role needs a DSN whose options set a search_path")
        schema, role = found.group(1), "tr_" + uuid.uuid4().hex[:12]
        for privilege, _ in grants:
            if privilege not in _PRIVILEGES:
                raise ValueError(f"privilege {privilege!r} is not one of {sorted(_PRIVILEGES)}")
        conn = None
        created = False
        try:
            with psycopg.connect(owner, autocommit=True) as admin:
                admin.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(role)))
                created = True
                admin.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                        sql.Identifier(schema), sql.Identifier(role)
                    )
                )
                for privilege, table in grants:
                    admin.execute(
                        sql.SQL("GRANT {} ON TABLE {}.{} TO {}").format(
                            sql.SQL(privilege),
                            sql.Identifier(schema),
                            sql.Identifier(table),
                            sql.Identifier(role),
                        )
                    )
            conn = psycopg.connect(make_conninfo(owner, user=role), autocommit=True)
            yield conn
        finally:
            if conn is not None:
                conn.close()
            if created:
                with psycopg.connect(owner, autocommit=True) as admin:
                    admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def execute(conn, template, params=None, idents=()):
        """Run `template` (each `{}` is filled with the next quoted identifier of `idents`; write `{{` and `}}`
        for a literal brace); the rows as a list of tuples, or an empty list for a statement that returns none.
        The number of `{}` must equal the number of `idents` and a `{}` may not be named or numbered: anything
        else is a `ValueError` that says so (the driver's own message for a mismatch is an IndexError that
        names neither). With no `params` (None or empty) the statement goes to the server as written, so a literal
        `%` (a LIKE pattern) needs no doubling; with `params` the driver reads `%` as a placeholder start and a
        literal one is written `%%`. The cursor is closed before the call returns."""
        parsed = [p for p in string.Formatter().parse(template) if p[1] is not None]
        fields = [name for _, name, _, _ in parsed]
        if any(name or spec or conv for _, name, spec, conv in parsed):
            raise ValueError(
                "execute: only plain {} placeholders (no name, number, format or !conversion)"
            )
        if len(fields) != len(idents):
            raise ValueError(
                f"execute: the template has {len(fields)} {{}} placeholders but {len(idents)} "
                f"identifiers were given"
            )
        query = sql.SQL(template).format(*[sql.Identifier(i) for i in idents])
        with conn.cursor() as cur:
            cur.execute(query, params or None)
            return cur.fetchall() if cur.description else []

    def sqlstate(exc):
        return getattr(exc, "sqlstate", None)

    @contextlib.contextmanager
    def expect_sqlstate(code):
        """Use instead of `pytest.raises(<driver class>)`: the block must raise a database error with `code`."""
        try:
            yield
        except psycopg.Error as exc:
            if exc.sqlstate != code:
                raise AssertionError(
                    f"expected SQLSTATE {code}, got {exc.sqlstate}: {exc}"
                ) from exc
        else:
            raise AssertionError(f"expected SQLSTATE {code}, but nothing was raised")

    def is_unique_violation(exc):
        return isinstance(exc, errors.UniqueViolation) or sqlstate(exc) == "23505"

    def make_error(code):
        """A driver error object that carries SQLSTATE `code`, for wrapper unit tests."""
        try:
            return errors.lookup(code)(f"made-up error {code}")
        except KeyError:
            return type("MadeUpError", (psycopg.DatabaseError,), {"sqlstate": code})(
                f"made-up error {code}"
            )

    def make_dsn(base, **parts):
        return make_conninfo(base, **parts)

    def dsn_parts(dsn):
        return conninfo_to_dict(dsn)

    return SimpleNamespace(
        connect_admin=connect_admin,
        connect_runtime=connect_runtime,
        connect_role=connect_role,
        execute=execute,
        ident=ident,
        sqlstate=sqlstate,
        expect_sqlstate=expect_sqlstate,
        is_unique_violation=is_unique_violation,
        make_error=make_error,
        make_dsn=make_dsn,
        dsn_parts=dsn_parts,
    )
