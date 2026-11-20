"""The ONE place that writes `hadavin_caps` for tests (step 6). After step 6 the Postgres reserve function reads the
caps of the agent from the table and takes none as an argument, while the Python interface (and every contract test)
still passes `day_cap` and `month_cap`. A test-only wrapper (`tests/conftest.py`, fixture `_seed_caps_before_reserve`)
therefore writes the pair the caller passes into the table, as the OWNER, before the store's `reserve_spend` runs. It is
never in `src`. A test that must prove the table wins, or that no row refuses, carries the marker `no_cap_seed`."""

from __future__ import annotations

import os
from decimal import Decimal

from hadavin_sdk.store.protocol import check_store_id

_UPSERT = (
    "INSERT INTO {t} (agent_id, day_cap, month_cap, set_by) VALUES (%s, %s, %s, 'test-seed') "
    "ON CONFLICT (agent_id) DO UPDATE SET day_cap = EXCLUDED.day_cap, month_cap = EXCLUDED.month_cap "
    "WHERE {t}.set_by = 'test-seed'"
)


def seed_caps(dsn_or_conn, schema: str | None, agent: str, day_cap, month_cap) -> None:
    """Upsert (agent, day_cap, month_cap) into `hadavin_caps` as the owner. `dsn_or_conn` is an owner DSN (a new
    autocommit connection) or an open owner connection; `schema` qualifies the table (None: the search path)."""
    import psycopg
    from psycopg import sql

    name = sql.Identifier("hadavin_caps")
    table = sql.SQL("{}.{}").format(sql.Identifier(schema), name) if schema else name
    query = sql.SQL(_UPSERT).format(t=table)
    args = (agent, Decimal(day_cap), Decimal(month_cap))
    if isinstance(dsn_or_conn, str):
        with psycopg.connect(dsn_or_conn, autocommit=True) as db:
            db.execute(query, args)
    else:
        dsn_or_conn.execute(query, args)


_WIDENED: set[tuple[str, str]] = set()
WIDE_SKEW_DAYS = 100_000


def widen_day_window(dsn: str, schema: str | None) -> None:
    """Raise `max_day_skew` of `hadavin_limits` as the OWNER, once per schema. `hadavin_reserve_spend` refuses a day more
    than `max_day_skew` days from the database's UTC date (review B3), and `hadavin_expire_spend_reservations` refuses an
    age below `min_expiry_age` (review M1: also set to 0 here); the contract and money tests reserve on fixed past
    days (month rollovers, a settle on another day) that the store contracts need, so the test-only wrapper below widens
    the window. Never in `src`. The tests of the window itself carry `no_cap_seed` and keep the real value."""
    import psycopg
    from psycopg import sql

    key = (dsn, str(schema))
    if key in _WIDENED:
        return
    name = sql.Identifier("hadavin_limits")
    table = sql.SQL("{}.{}").format(sql.Identifier(schema), name) if schema else name
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("UPDATE {} SET value = %s WHERE name = 'max_day_skew'").format(table),
            (WIDE_SKEW_DAYS,),
        )
        # the tests expire a hold at age 0 and release it at once (review M1: the real minimum is 3600 s)
        db.execute(sql.SQL("UPDATE {} SET value = 0 WHERE name = 'min_expiry_age'").format(table))
    _WIDENED.add(key)


def seeding_reserve(original):
    """Wrap `PostgresStore.reserve_spend`: seed the caps the caller passes, then delegate. The owner DSN is the test
    DSN (`HADAVIN_TEST_PG_DSN`) scoped to the schema of the store; the pair is written once per (schema, agent)
    unless it changes. A row written by anything else (`set_cap`, set_by <> 'test-seed') is never overwritten: the table
    wins, as in production. A seed failure is not swallowed."""

    def reserve_spend(self, reservation_id, agent_id, day, usd, *, day_cap, month_cap, run_id=None):
        dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
        try:
            pair = (Decimal(day_cap), Decimal(month_cap))
            ok = pair[0].is_finite() and pair[1].is_finite() and pair[0] >= 0 and pair[1] >= 0
        except Exception:  # noqa: BLE001 - a bad argument: the store refuses it itself, seed nothing
            ok = False
        if dsn and ok:
            try:
                check_store_id(agent_id, "agent_id")
            except ValueError:  # an id the store refuses itself below: nothing to seed
                pass
            else:
                import psycopg

                try:
                    seed_caps(dsn, self._schema, agent_id, *pair)
                except psycopg.errors.DataError:
                    pass  # a cap the numeric type cannot hold (1E+999999): the store refuses it itself below
        if dsn:
            try:
                widen_day_window(dsn, self._schema)
            except Exception:  # noqa: BLE001, S110 - no limits table yet: the store refuses below
                pass
        return original(
            self,
            reservation_id,
            agent_id,
            day,
            usd,
            day_cap=day_cap,
            month_cap=month_cap,
            run_id=run_id,
        )

    return reserve_spend


def widening_expire(original):
    """Wrap `PostgresStore.expire_spend_reservations`: widen the window first, as `seeding_reserve` does. A sequence
    may call expire BEFORE any reserve (the model test of seed 23 does), and the real `min_expiry_age` (3600 s) would
    then refuse the age 0 the contract tests use."""

    def expire_spend_reservations(self, older_than_s):
        dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
        if dsn:
            try:
                widen_day_window(dsn, self._schema)
            except Exception:  # noqa: BLE001, S110 - no limits table yet: the store refuses below
                pass
        return original(self, older_than_s)

    return expire_spend_reservations


def widening_add_spend(original):
    """Wrap `PostgresStore.add_spend`: widen the window first (`hadavin_add_spend` has the day window of reserve, review
    m1), as `seeding_reserve` does. Tests that carry `no_cap_seed` keep the real value."""

    def add_spend(self, agent_id, day, usd):
        dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
        if dsn:
            try:
                widen_day_window(dsn, self._schema)
            except Exception:  # noqa: BLE001, S110 - no limits table yet: the store refuses below
                pass
        return original(self, agent_id, day, usd)

    return add_spend


def seed_registry_caps(dsn_or_conn, schema: str | None, registry) -> None:
    """Seed the caps of every non-retired agent of `registry` with the registry's own budget, as the owner: the
    state `limits sync-caps` leaves, so a FULL tick (step `check_caps`) finds no drift."""
    for agent in registry.agents.values():
        if agent.status != "retired":
            seed_caps(
                dsn_or_conn, schema, agent.id, agent.budget_usd.daily, agent.budget_usd.monthly
            )
