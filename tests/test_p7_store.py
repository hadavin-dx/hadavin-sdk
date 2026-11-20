"""Slice 2 P7 store hardening: TLS rules, append-only grants, fail-closed kill switch, exact month spend.

Database tests skip without HADAVIN_TEST_PG_DSN (CI runs the postgres service)."""

import threading
from datetime import date
from decimal import Decimal

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from psycopg import errors as pg_errors
from psycopg import sql

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.config import ConfigError
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.store.migrate import migrate
from hadavin_sdk.store.postgres import tls_mode
from tests.contracts.kinds.store_postgres import pg_schema

REMOTE = "postgresql://app@db.example.internal:5432/core"
PW = "pw" + "-p7"  # built from parts


# --- TLS (no database) -------------------------------------------------------------------------------


CA = "/etc/ssl/db-ca.pem"


@pytest.mark.parametrize(
    "dsn,setting,ca,want",
    [
        (REMOTE, None, CA, "verify-full"),  # non-local host: the server is verified by default
        ("postgresql://app@localhost/core", None, None, None),  # loopback keeps the DSN's choice
        ("host=/var/run/postgresql dbname=core", None, None, None),  # unix socket
        ("postgresql://app@127.0.0.2/core", None, None, None),  # all of 127/8 is loopback
        (REMOTE + "?sslmode=verify-ca", None, CA, "verify-ca"),  # the DSN's mode is kept
        (REMOTE, "require", None, "require"),  # explicit opt-down for demo (no iam)
        (REMOTE, "disable", None, "disable"),
        ("hostaddr=10.0.0.5 dbname=core", None, CA, "verify-full"),  # hostaddr counts as the host
    ],
)
def test_tls_mode(dsn, setting, ca, want):
    assert tls_mode(dsn, sslmode=setting, sslrootcert=ca) == want


def test_a_verified_mode_needs_a_ca_bundle():
    with pytest.raises(ConfigError, match="CA bundle"):
        tls_mode(REMOTE)
    with pytest.raises(ConfigError, match="CA bundle"):
        tls_mode(REMOTE + "?sslmode=verify-full")
    assert tls_mode(REMOTE + "?sslrootcert=/x.pem") == "verify-full"


def test_pghost_counts_as_the_host(monkeypatch):
    monkeypatch.setenv("PGHOST", "db.example.internal")
    assert tls_mode("dbname=core", sslrootcert=CA) == "verify-full"


def test_ca_bundle_from_the_secrets_backend(tmp_path):
    from hadavin_sdk.store.postgres import ca_file

    pem = "-----BEGIN " + "CERTIFICATE-----\nMIIfake\n-----END " + "CERTIFICATE-----\n"
    settings = PostgresSettings(
        kind="postgres",
        dsn_secret_name="pg-dsn",  # noqa: S106 - a name
        sslrootcert_secret_name="db-ca",  # noqa: S106 - a name
    )
    path = ca_file(settings, {"db-ca": pem}.__getitem__)
    with open(path, encoding="utf-8") as f:
        assert f.read() == pem
    with_path = PostgresSettings(kind="postgres", dsn_secret_name="d", sslrootcert=CA)  # noqa: S106
    assert ca_file(with_path, None) == CA
    with pytest.raises(ValueError, match="not both"):
        PostgresSettings(
            kind="postgres",
            dsn_secret_name="d",  # noqa: S106 - a name
            sslrootcert=CA,
            sslrootcert_secret_name="db-ca",  # noqa: S106 - a name
        )


def test_iam_verifies_the_server_by_default():
    ca = CA
    assert tls_mode(REMOTE, iam_auth=True, sslrootcert=ca) == "verify-full"
    assert (
        tls_mode("postgresql://app@localhost/core", iam_auth=True, sslrootcert=ca) == "verify-full"
    )
    assert tls_mode(REMOTE, iam_auth=True, sslmode="verify-ca", sslrootcert=ca) == "verify-ca"
    with pytest.raises(ConfigError, match="sslrootcert"):
        tls_mode(REMOTE, iam_auth=True)


@pytest.mark.parametrize("weak", ["disable", "allow", "prefer", "require"])
def test_iam_refuses_an_unverified_server(weak):
    with pytest.raises(ConfigError, match="verified server"):
        tls_mode(REMOTE, iam_auth=True, sslmode=weak, sslrootcert="/ca.pem")
    with pytest.raises(ConfigError, match="verified server"):
        tls_mode(f"{REMOTE}?sslmode={weak}", iam_auth=True, sslrootcert="/ca.pem")


def test_iam_runtime_dsn_with_a_password_is_refused():
    pytest.importorskip("boto3")
    settings = PostgresSettings(
        kind="postgres",
        dsn_secret_name="pg-dsn",  # noqa: S106 - a name
        iam_auth=True,
        region="test-region-1",
    )
    dsn = f"postgresql://app:{PW}@db.example.internal/core"
    with pytest.raises(ConfigError, match="must not carry a password") as err:
        make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
    assert PW not in str(err.value)


# --- with a database ---------------------------------------------------------------------------------


@pytest.fixture
def fresh_dsn():
    yield from pg_schema(migrated=False)


@pytest.fixture
def store():
    for dsn in pg_schema():
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        s = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        yield s
        s._db.close()


def test_append_only_tables_get_no_update(fresh_dsn):
    import psycopg

    role = "rt_" + fresh_dsn.rsplit("search_path=t_", 1)[1][:8]
    with psycopg.connect(fresh_dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))
    try:
        migrate(fresh_dsn, runtime_role=role)
        with psycopg.connect(fresh_dsn, autocommit=True) as db:

            def can(table, priv):
                q = "SELECT has_table_privilege(%s, %s, %s)"
                return db.execute(q, (role, table, priv)).fetchone()[0]

            for table in ("approval_decisions", "dead_letters", "gate_decisions"):
                assert can(table, "INSERT") and can(table, "SELECT")
                assert not can(table, "UPDATE") and not can(table, "DELETE"), table
            for table in ("runs", "approval_requests", "spend_month", "tick_state"):
                assert can(table, "UPDATE") and not can(table, "DELETE"), table
            # Stop state (0006): the runtime may add a stop and read; nothing it holds turns the switch off.
            assert can("kill_switch_stops", "INSERT") and can("kill_switch_stops", "SELECT")
            for table, privs in (
                ("kill_switch", ("INSERT", "UPDATE", "DELETE", "TRUNCATE")),
                ("kill_switch_stops", ("UPDATE", "DELETE", "TRUNCATE")),
                ("kill_switch_clears", ("INSERT", "UPDATE", "DELETE", "TRUNCATE")),
            ):
                assert can(table, "SELECT"), table
                assert not any(can(table, p) for p in privs), table
    finally:
        with psycopg.connect(fresh_dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def test_migrate_seeds_the_kill_switch_off(store):
    ks = store.get_kill_switch()
    assert ks.on is False


def test_missing_kill_switch_row_fails_closed(store, caplog):
    with store._lock:
        store._exec("DELETE FROM kill_switch")
    ks = store.get_kill_switch()
    assert ks.on is True and ks.by == "system:kill_switch_row_missing"
    assert "kill_switch row missing" in caplog.text


def test_an_open_stop_reads_on_while_the_flag_is_off(store):
    store.set_kill_switch(KillSwitch(on=True, by="ops"))
    with store._lock:
        flag = store._exec('SELECT "on" FROM kill_switch').fetchone()["on"]
        stops = store._exec("SELECT count(*) AS n FROM kill_switch_stops").fetchone()["n"]
    assert flag is False and stops == 1  # a stop is one appended row; the old flag is not touched
    ks = store.get_kill_switch()
    assert ks.on is True and ks.by == "ops"


def test_a_reset_clears_the_stops_it_can_see_and_a_later_stop_reads_on_again(store):
    store.set_kill_switch(KillSwitch(on=True, by="first"))
    store.set_kill_switch(KillSwitch(on=True, by="second"))
    assert store.get_kill_switch().by == "first"  # the oldest open stop is the one reported
    store.set_kill_switch(KillSwitch(on=False, by="admin"))
    assert store.get_kill_switch().on is False
    with store._lock:
        clears = store._exec('SELECT "by" FROM kill_switch_clears ORDER BY stop_id').fetchall()
    assert [c["by"] for c in clears] == ["admin", "admin"]
    store.set_kill_switch(KillSwitch(on=False, by="admin"))  # nothing open: a reset is still fine
    store.set_kill_switch(KillSwitch(on=True, by="third"))
    ks = store.get_kill_switch()
    assert ks.on is True and ks.by == "third"


def test_the_old_flag_still_reads_on_and_a_reset_turns_it_off(store):
    with store._lock:
        store._exec('UPDATE kill_switch SET "on" = TRUE, "by" = %s', ("before-0006",))
    ks = store.get_kill_switch()
    assert ks.on is True and ks.by == "before-0006"
    store.set_kill_switch(KillSwitch(on=False, by="admin"))
    ks = store.get_kill_switch()
    assert ks.on is False and ks.by == "admin"


def test_a_missing_flag_row_stays_on_after_a_reset(store):
    with store._lock:
        store._exec("DELETE FROM kill_switch")
    store.set_kill_switch(KillSwitch(on=False, by="admin"))
    assert store.get_kill_switch().by == "system:kill_switch_row_missing"


def test_the_stop_tables_are_append_only_for_the_owner_too(store):
    store.set_kill_switch(KillSwitch(on=True, by="ops"))
    store.set_kill_switch(KillSwitch(on=False, by="admin"))
    for table in ("kill_switch_stops", "kill_switch_clears"):
        for statement in ('UPDATE {} SET "by" = NULL', "DELETE FROM {}", "TRUNCATE {} CASCADE"):
            with pytest.raises(pg_errors.RaiseException, match="append-only"), store._lock:
                store._exec(sql.SQL(statement).format(sql.Identifier(table)))


def test_month_spend_is_exact_under_concurrent_writers(fresh_dsn):
    migrate(fresh_dsn)
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
    stores = [make("store", settings, FakeSecretProvider({"pg-dsn": fresh_dsn})) for _ in range(4)]
    days = [date(2026, 3, d) for d in (1, 2, 3, 4)]
    gate = threading.Barrier(len(stores))

    def charge(s, day):
        gate.wait()
        for _ in range(25):
            s.add_spend("a", day, Decimal("0.01"))

    threads = [threading.Thread(target=charge, args=a) for a in zip(stores, days, strict=True)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert stores[0].spend_totals("a", days[0]) == (Decimal("0.25"), Decimal("1.00"))
    for s in stores:
        s._db.close()
