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
# runtime DSN -> the logins of an `inbound=True` schema: door, dispatch (DSNs), migrator (the scoped admin DSN), rerun (role name)
INBOUND: dict[str, dict[str, str]] = {}


def pg_schema(migrated=True, runtime=False, inbound=False):
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
    role = purge = door = dispatch = owner = None
    try:
        if runtime:
            role, purge = "rt_" + uuid.uuid4().hex[:12], "pu_" + uuid.uuid4().hex[:12]
            with psycopg.connect(dsn, autocommit=True) as db:
                for r in (role, purge):
                    db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
                if inbound:  # AK-G2-a: door and dispatch log in; the re-run owner cannot
                    door, dispatch, owner = (
                        "dr_" + uuid.uuid4().hex[:12],
                        "dp_" + uuid.uuid4().hex[:12],
                        "ro_" + uuid.uuid4().hex[:12],
                    )
                    for r in (door, dispatch):
                        db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
                    db.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(owner)))
            if inbound:
                migrate(
                    scoped,
                    runtime_role=role,
                    purge_role=purge,
                    inbound_door_role=door,
                    inbound_dispatch_role=dispatch,
                    rerun_owner_role=owner,
                )
            else:
                migrate(scoped, runtime_role=role, purge_role=purge)
            runtime_dsn = make_conninfo(scoped, user=role)
            PURGE_DSN[runtime_dsn] = make_conninfo(scoped, user=purge)
            if inbound:
                INBOUND[runtime_dsn] = {
                    "door": make_conninfo(scoped, user=door),
                    "dispatch": make_conninfo(scoped, user=dispatch),
                    "migrator": scoped,
                    "rerun": owner,
                    "schema": schema,
                }
            yield runtime_dsn
        else:
            yield scoped
    finally:
        with psycopg.connect(dsn, autocommit=True) as db:
            for r in (role, purge, door, dispatch, owner):
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


class InboundSplitStore:
    """Each inbound call goes to the login that owns it: `receive_inbound` to the door, the purge to the purge login,
    every other inbound call (and the Store calls tests need to set up runs) to dispatch or runtime, as the app
    wires them. `reopen_inbound` goes through the door login on purpose: it must always be `RerunRefused`."""

    def __init__(self, runtime, door, dispatch, purge, migrator_dsn, rerun_role):
        self.runtime, self.door, self.dispatch, self.purge = runtime, door, dispatch, purge
        self._migrator_dsn, self._rerun_role = migrator_dsn, rerun_role

    def __getattr__(self, name):
        if name in ("receive_inbound", "reopen_inbound"):
            return getattr(self.door, name)
        if name == "purge_inbound_bodies":
            return getattr(self.purge, name)
        if name.endswith("_inbound") or "inbound" in name:
            return getattr(self.dispatch, name)
        return getattr(self.runtime, name)

    def rerun_owner_reopen(self, tenant, source, delivery_key, now):
        """The re-run owner's reopen (a setup step, not a negative test): the migrator connection acts as that role."""
        from hadavin_sdk.store.postgres import connect, PostgresStore

        db = connect(self._migrator_dsn)
        try:
            db.execute(f'SET ROLE "{self._rerun_role}"')
            return PostgresStore(db).reopen_inbound(tenant, source, delivery_key, now)
        finally:
            db.execute("RESET ROLE")
            db.close()

    def close(self):
        for st in (self.runtime, self.door, self.dispatch, self.purge):
            st._db.close()


def inbound_postgres_store(tmp_path=None):
    """Yield an `InboundSplitStore` over a fresh migrated schema (six roles)."""
    for dsn in pg_schema(runtime=True, inbound=True):
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        info = INBOUND[dsn]

        def build(d):
            return make("store", settings, FakeSecretProvider({"pg-dsn": d}))

        split = InboundSplitStore(
            build(dsn),
            build(info["door"]),
            build(info["dispatch"]),
            build(PURGE_DSN[dsn]),
            info["migrator"],
            info["rerun"],
        )
        yield split
        split.close()
