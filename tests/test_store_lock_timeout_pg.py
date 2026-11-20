"""The PostgreSQL store sets `lock_timeout` from `defaults.STORE_LOCK_TIMEOUT_MS` right after it connects (fix round
3 of F-store): a call that waits on a row lock fails after that time instead of holding the process-wide store lock
for ever, and `Limits.reserve` maps the failure to SpendRefused("limits_unavailable"). The migrate connection sets
no lock timeout.

Written by a different agent than the builder. Needs HADAVIN_TEST_PG_DSN (skipped without it). The store is built
the way the contract suite builds it (`make("store", ...)` on a fresh migrated schema); a second connection holds
the row lock of the day counter and is rolled back in a `finally`.
"""

import os
import time
from datetime import date
from decimal import Decimal

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg

from hadavin_sdk import defaults
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.limits import Limits, SpendRefused
from hadavin_sdk.models import new_id, now
from hadavin_sdk.store import migrate as migrate_mod
from hadavin_sdk.store import postgres as postgres_mod
from tests.contracts.kinds.store_postgres import pg_schema
from tests.test_limits_reserve import Sink, _registry

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

D = Decimal
AGENT = "agent-a"
WITHIN_S = 15  # "an error, not a hang"


def _build(dsn):
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
    return make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))


@pytest.fixture
def scoped():
    yield from pg_schema()


@pytest.fixture
def store(scoped):
    built = _build(scoped)
    yield built
    built._db.close()


def _today():
    return now().date()


def _seed(store):
    """One booking, so the day counter row of (AGENT, today) exists and can be locked."""
    store.reserve_spend(
        new_id("res"), AGENT, _today(), D("0.10"), day_cap=D("100"), month_cap=D("100")
    )


def _holder(scoped):
    """A second connection that updates the counter row and does not commit."""
    db = psycopg.connect(scoped)
    db.execute("UPDATE spend SET usd = usd WHERE agent_id = %s AND day = %s", (AGENT, _today()))
    return db


def _row_count(store):
    return store._db.execute("SELECT count(*) FROM spend_reservations").fetchone()[0]


def test_the_default_is_ten_seconds_and_the_runtime_connection_carries_it(store):
    assert defaults.STORE_LOCK_TIMEOUT_MS == 10000
    assert store._db.execute("SHOW lock_timeout").fetchone()[0] == "10s"


def test_the_value_comes_from_the_default_at_build_time(scoped, monkeypatch):
    monkeypatch.setattr(defaults, "STORE_LOCK_TIMEOUT_MS", 2500)
    built = _build(scoped)
    try:
        assert built._db.execute("SHOW lock_timeout").fetchone()[0] == "2500ms"
    finally:
        built._db.close()


def test_the_migrate_connection_sets_no_lock_timeout(scoped, monkeypatch):
    seen = []
    real = migrate_mod.connect

    def spy(*args, **kwargs):
        db = real(*args, **kwargs)
        seen.append(db.execute("SHOW lock_timeout").fetchone()[0])
        return db

    monkeypatch.setattr(migrate_mod, "connect", spy)
    migrate_mod.migrate(scoped, no_roles=True)  # idempotent on a migrated schema
    assert seen == ["0"]
    # and the shared `connect()` itself sets none: the store sets it in `build()` only
    with postgres_mod.connect(scoped) as db:
        assert db.execute("SHOW lock_timeout").fetchone()[0] == "0"


def test_a_call_that_waits_on_a_row_lock_fails_instead_of_hanging(scoped, store, monkeypatch):
    """The real default: the wait ends in an error inside WITHIN_S seconds, through `Limits.reserve`."""
    limits = Limits(store, Sink(), _registry(daily="100", monthly="1000", agents=(AGENT,)))
    limits.reserve(AGENT, D("0.10"))  # seeds the counter row
    before = _row_count(store)
    holder = _holder(scoped)
    try:
        started = time.monotonic()
        with pytest.raises(SpendRefused) as caught:
            limits.reserve(AGENT, D("0.10"))
        waited = time.monotonic() - started
    finally:
        holder.rollback()
        holder.close()
    assert caught.value.reason == "limits_unavailable"
    assert waited < WITHIN_S
    assert (
        waited >= defaults.STORE_LOCK_TIMEOUT_MS / 1000 * 0.8
    )  # it did wait for the lock, then gave up
    # the failed call left nothing behind, and the store works again once the lock is gone
    assert _row_count(store) == before
    rid = limits.reserve(AGENT, D("0.10"))
    assert rid and _row_count(store) == before + 1


def test_the_store_call_itself_raises_a_lock_error_and_books_nothing(scoped, monkeypatch):
    monkeypatch.setattr(defaults, "STORE_LOCK_TIMEOUT_MS", 1000)
    built = _build(scoped)
    try:
        _seed(built)
        holder = _holder(scoped)
        try:
            started = time.monotonic()
            with pytest.raises(psycopg.errors.LockNotAvailable):
                built.reserve_spend(
                    new_id("res"), AGENT, _today(), D("1"), day_cap=D("100"), month_cap=D("100")
                )
            assert 0.8 <= time.monotonic() - started < WITHIN_S
        finally:
            holder.rollback()
            holder.close()
        assert built.spend_totals(AGENT, _today()) == (D("0.10"), D("0.10"))
        assert _row_count(built) == 1
        # a counter of another day is not locked: the wait is per row
        built.reserve_spend(
            new_id("res"), AGENT, date(2026, 1, 5), D("1"), day_cap=D("100"), month_cap=D("100")
        )
    finally:
        built._db.close()
