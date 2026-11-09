"""P4d-b, B8 (a), (b): new code against a database that is behind. The "behind" schema is built from an explicit list
of SQL files by executing them directly. The ticket names P3a's `tests/migration_schemas.py` for this; P3a has not
merged (the file is on no branch of this repository), so the same few lines are written here and move to that helper
when it lands (ticket P4d, N1)."""

from decimal import Decimal
from pathlib import Path

import pytest

from hadavin_sdk.store.postgres import PostgresStore
from hadavin_sdk.store.protocol import is_connectivity_error
from tests.contracts.kinds.store_postgres import pg_driver, pg_schema
from tests.contracts.store_support import utc_today

drv = pg_driver(module_level=True)
D = Decimal
MIGRATIONS = Path(__file__).parents[2] / "src" / "hadavin_sdk" / "store" / "migrations"
AGENT = "ag-behind"
RUNTIME_RIGHTS = [
    ("SELECT", "kill_switch"),
    ("SELECT", "runs"),
    ("UPDATE", "runs"),
    ("SELECT", "spend"),
    ("INSERT", "spend"),
    ("UPDATE", "spend"),
    ("SELECT", "spend_month"),
    ("INSERT", "spend_month"),
    ("UPDATE", "spend_month"),
]


@pytest.fixture
def behind_dsn():
    yield from pg_schema(migrated=False)


def _apply(dsn, stems):
    """Run the named migration files, in order, as the owner (an explicit list, never the folder's content)."""
    with drv.connect_admin(dsn, autocommit=False) as conn:
        for stem in stems:
            text = (MIGRATIONS / f"{stem}.sql").read_text(encoding="utf-8")
            drv.execute(conn, text.replace("{", "{{").replace("}", "}}"))
        conn.commit()


def _reserve(store):
    return store.reserve_spend(
        "behind-1",
        AGENT,
        utc_today(store),
        D(1),
        day_cap=None,
        month_cap=None,
        run_id=None,
        run_cap=None,
    )


def _counters(dsn):
    with drv.connect_admin(dsn) as conn:
        return drv.execute(conn, "SELECT count(*) FROM spend")[0][0]


MATCH_A = 'relation "spend_reservations" does not exist'
MATCH_B = "permission denied"


def test_b8a_a_database_without_the_reservation_table_fails_loudly_and_books_nothing(behind_dsn):
    _apply(
        behind_dsn,
        [
            "0001_core",
            "0002_audit_chain",
            "0003_approvals_tick",
            "0004_audit_checkpoint_meta",
            "0005_evidence",
        ],
    )
    grants = [*RUNTIME_RIGHTS]
    with drv.connect_role(behind_dsn, grants=grants) as conn:
        store = PostgresStore(conn)
        with pytest.raises(Exception, match=MATCH_A) as info:
            _reserve(store)
        caught = info.value
        assert drv.sqlstate(caught) == "42P01"  # undefined_table
        assert is_connectivity_error(caught) is False  # a missing table is not a network problem
    assert _counters(behind_dsn) == 0


def test_b8b_a_table_without_the_runtime_grant_fails_loudly_and_books_nothing(behind_dsn):
    _apply(
        behind_dsn,
        [
            "0001_core",
            "0002_audit_chain",
            "0003_approvals_tick",
            "0004_audit_checkpoint_meta",
            "0005_evidence",
            "0006_spend_reservations",
        ],
    )
    with drv.connect_role(
        behind_dsn, grants=RUNTIME_RIGHTS
    ) as conn:  # no right on spend_reservations
        store = PostgresStore(conn)
        with pytest.raises(Exception, match=MATCH_B) as info:
            _reserve(store)
        caught = info.value
        assert drv.sqlstate(caught) == "42501"  # insufficient_privilege
        assert is_connectivity_error(caught) is False
    assert _counters(behind_dsn) == 0
