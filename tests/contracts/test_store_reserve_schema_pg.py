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
    ("SELECT", "kill_switch_state"),
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
            "0007_kill_switch_guard",  # the runtime reads the switch first: its state view must exist
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
            "0007_kill_switch_guard",
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


# --- the local builder cannot drift from the real migration (lead order 182) ------------------------------------
# REMOVAL NOTE: when P3a merges, `_apply` and this block are replaced by `tests/migration_schemas.py` in the same
# rebase of this PR; the equality test is then replaced by the one P3a ships for its own helper.

ALL_STEMS = sorted(p.stem for p in MIGRATIONS.glob("*.sql"))
BOOKKEEPING = {"schema_migrations"}  # written by `migrate()` itself, not by any migration file
# The kill switch functions are installed by `migrate()` in code (their text names the reset group role), so no
# migration file holds them; the file 0007 holds only a placeholder guard. They are left out of the file-by-file
# comparison and checked to exist in the real schema.
INSTALLED_BY_MIGRATE = (
    "hadavin_kill_switch_stop",
    "hadavin_kill_switch_reset",
    "hadavin_kill_switch_guard",
)


@pytest.fixture
def real_dsn():
    yield from pg_schema(migrated=True)


def _catalog(dsn):
    """Everything a migration creates in the schema of `dsn`: columns, constraints, indexes, triggers and function
    bodies, as text, with the schema name replaced so two schemas compare equal."""
    with drv.connect_admin(dsn) as conn:
        (schema,) = drv.execute(conn, "SELECT current_schema()")[0]
        queries = {
            "columns": "SELECT table_name, column_name, ordinal_position, data_type, is_nullable, column_default "
            "FROM information_schema.columns WHERE table_schema = current_schema() ORDER BY 1, 3",
            "constraints": "SELECT c.conrelid::regclass::text, c.conname, c.contype, pg_get_constraintdef(c.oid) "
            "FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace "
            "WHERE n.nspname = current_schema() ORDER BY 1, 2",
            "indexes": "SELECT tablename, indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = current_schema() ORDER BY 1, 2",
            "triggers": "SELECT tgrelid::regclass::text, tgname, tgenabled, pg_get_triggerdef(oid) FROM pg_trigger "
            "WHERE NOT tgisinternal AND tgrelid IN "
            "(SELECT oid FROM pg_class WHERE relnamespace = current_schema()::regnamespace) ORDER BY 1, 2",
            "functions": "SELECT p.proname, pg_get_functiondef(p.oid) FROM pg_proc p "
            "WHERE p.pronamespace = current_schema()::regnamespace ORDER BY 1",
        }
        out = {}
        for name, query in queries.items():
            rows = drv.execute(conn, query)
            out[name] = sorted(
                {
                    tuple(str(v).replace(schema, "<schema>") for v in row)
                    for row in rows
                    if not any(b in str(row) for b in BOOKKEEPING)
                    and not (name == "functions" and row[0] in INSTALLED_BY_MIGRATE)
                }
            )
        return out


def test_the_local_schema_builder_gives_the_same_catalog_as_the_real_migration(
    behind_dsn, real_dsn
):
    _apply(behind_dsn, ALL_STEMS)
    built, real = _catalog(behind_dsn), _catalog(real_dsn)
    assert any(
        "spend_reservations" in str(row) for row in real["columns"]
    )  # the snapshot is not empty
    assert len(real["constraints"]) > 20 and len(real["triggers"]) >= 2 and real["functions"]
    assert built == real
    with drv.connect_admin(real_dsn) as conn:
        found = {
            r[0]
            for r in drv.execute(
                conn,
                "SELECT proname FROM pg_proc WHERE pronamespace = current_schema()::regnamespace",
            )
        }
    assert set(INSTALLED_BY_MIGRATE) <= found  # migrate() really installed them


def test_the_catalog_comparison_notices_a_missing_migration_file(behind_dsn, real_dsn):
    _apply(behind_dsn, ALL_STEMS[:-1])  # the newest file left out: the comparison must differ
    assert _catalog(behind_dsn) != _catalog(real_dsn)
