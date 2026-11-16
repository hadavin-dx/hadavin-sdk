"""The `postgres` store kind. Needs HADAVIN_TEST_PG_DSN (CI: the postgres service); skipped without it, so the
laptop needs no Docker. Each test gets its own schema, migrated fresh and dropped afterwards."""

import os
import uuid

import pytest

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from tests.contracts.kinds import kind

# runtime DSN -> the DSN of the purge role of the same schema (only for `pg_schema(runtime=True)`)
PURGE_DSN: dict[str, str] = {}


def pg_schema(migrated=True, runtime=False):
    """Yield a DSN whose search_path is a fresh (migrated) schema; drop the schema afterwards. With `runtime`,
    yield instead the DSN of a new non-owner login role that `migrate` granted its runtime rights (K2: the store
    suite must pass with only those rights); the role is dropped afterwards."""
    dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
    if not dsn:
        pytest.skip("HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)")
    psycopg = pytest.importorskip("psycopg")
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.migrate import migrate

    schema = f"t_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    scoped = make_conninfo(dsn, options=f"-c search_path={schema}")
    if migrated:
        migrate(scoped)
    role = purge = None
    try:
        if runtime:
            role, purge = "rt_" + uuid.uuid4().hex[:12], "pu_" + uuid.uuid4().hex[:12]
            with psycopg.connect(dsn, autocommit=True) as db:
                for r in (role, purge):
                    db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
            migrate(scoped, runtime_role=role, purge_role=purge)
            runtime_dsn = make_conninfo(scoped, user=role)
            PURGE_DSN[runtime_dsn] = make_conninfo(scoped, user=purge)
            yield runtime_dsn
        else:
            yield scoped
    finally:
        with psycopg.connect(dsn, autocommit=True) as db:
            for r in (role, purge):
                if r:
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


class _SplitStore:
    """The runtime role for everything, the purge role for the two purges: as `app.build` wires them
    (`purge_dsn_secret_name`), so the suite runs with each identity holding only its own rights."""

    def __init__(self, main, purge):
        self._main, self._purge = main, purge

    def __getattr__(self, name):
        return getattr(self._main, name)

    def purge_tool_calls(self, *a, **k):
        return self._purge.purge_tool_calls(*a, **k)

    def purge_redaction_maps(self, *a, **k):
        return self._purge.purge_redaction_maps(*a, **k)


@kind("store", "postgres")
def postgres(tmp_path):
    for dsn in pg_schema(runtime=True):
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        purge_store = make("store", settings, FakeSecretProvider({"pg-dsn": PURGE_DSN[dsn]}))
        yield _SplitStore(store, purge_store)
        store._db.close()
        purge_store._db.close()
