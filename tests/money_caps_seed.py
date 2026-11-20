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
                seed_caps(dsn, self._schema, agent_id, *pair)
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
