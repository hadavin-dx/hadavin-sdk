"""Postgres only: a busy per-tenant reservation lock is the typed StoreBusy (a StoreUnavailable), not a raw driver error."""

import pytest

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.models import Reservation, ReservationLimits
from hadavin_sdk.store.protocol import StoreBusy, StoreUnavailable, is_connectivity_error
from tests.contracts.kinds.store_postgres import pg_schema


def test_a_busy_reservation_lock_is_a_typed_store_busy():
    psycopg = pytest.importorskip("psycopg")
    for dsn in pg_schema():
        store = make(
            "store",
            PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn"),  # noqa: S106 - a name
            FakeSecretProvider({"pg-dsn": dsn}),
        )
        res = Reservation(tenant="t", key="k", scopes=["c"], actor="a", unit="USD", amount=1)
        lim = ReservationLimits(
            max_per_scope=3, max_per_actor=3, unit_caps={"USD": 10}, lock_timeout_s=1
        )
        with psycopg.connect(dsn, autocommit=True) as other:
            other.execute("BEGIN")
            other.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", ("t",))
            try:
                store.reserve(res, lim, res.created_at)
            except StoreBusy as e:
                assert isinstance(e, StoreUnavailable) and is_connectivity_error(e)
            except Exception as e:  # noqa: BLE001
                pytest.fail(f"expected StoreBusy, got {type(e).__name__}")
            else:
                pytest.fail("reserved while another transaction held the tenant lock")
            other.execute("ROLLBACK")
        assert store.reserve(res, lim, res.created_at) is None
        store._db.close()
