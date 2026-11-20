"""B1 of F-store review 3: the SECURITY DEFINER release function must not be hijackable through the temp schema
(pg_temp is searched first for relations unless the path says otherwise). Real PostgreSQL, real release login."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")


from tests.test_release_expired_spend_pg import (
    AGENT,
    DAY,
    _world_with_holds,
    release_world,  # noqa: F401 - the fixture
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


def test_proconfig_has_catalog_first_and_pg_temp_last(w):
    cfg = w.run(
        "SELECT proconfig FROM pg_proc WHERE oid = to_regprocedure('hadavin_release_expired_spend(text, date)')"
    )[0][0]
    (entry,) = [c for c in cfg if c.startswith("search_path=")]
    parts = [p.strip().strip('"') for p in entry.split("=", 1)[1].split(",")]
    assert parts[0] == "pg_catalog" and parts[-1] == "pg_temp"
    assert w.schema in parts


def test_a_temp_table_trigger_of_the_release_login_does_not_fire(w):
    _world_with_holds(w)
    rl = w.as_(w.release)
    try:
        rl.execute(
            "CREATE TEMP TABLE spend_reservations (agent_id text, day date, status text, "
            "settled_usd numeric, reserved_usd numeric)"
        )
        rl.execute("CREATE TEMP TABLE spend (agent_id text, day date, usd numeric)")
        rl.execute("CREATE TEMP TABLE spend_month (agent_id text, month date, usd numeric)")
        rl.execute("CREATE TEMP TABLE fired (who text, su boolean)")
        rl.execute(
            "INSERT INTO pg_temp.spend_reservations VALUES (%s, %s, 'expired', 0, 1)", (AGENT, DAY)
        )
        # counter rows too, so the OLD (hijackable) function runs to the end and the `fired` count is what fails
        rl.execute("INSERT INTO pg_temp.spend VALUES (%s, %s, 5)", (AGENT, DAY))
        rl.execute(
            "INSERT INTO pg_temp.spend_month VALUES (%s, %s, 5)", (AGENT, DAY.replace(day=1))
        )
        rl.execute(
            "CREATE FUNCTION pg_temp.evil() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
            "INSERT INTO pg_temp.fired SELECT current_user, "
            "(SELECT rolsuper FROM pg_roles WHERE rolname = current_user); RETURN NEW; END $$"
        )
        rl.execute(
            "CREATE TRIGGER t BEFORE UPDATE ON pg_temp.spend_reservations "
            "FOR EACH ROW EXECUTE FUNCTION pg_temp.evil()"
        )
        row = rl.execute(
            "SELECT reservations, released_usd FROM hadavin_release_expired_spend(%s, %s)",
            (AGENT, DAY),
        ).fetchone()
        assert rl.execute("SELECT count(*) FROM pg_temp.fired").fetchone()[0] == 0
        # the real rows were released, not the planted one
        assert (row[0], str(row[1])) == (2, "3.00")
        assert rl.execute("SELECT status FROM pg_temp.spend_reservations").fetchone() == (
            "expired",
        )
    finally:
        rl.close()


def _pin(w):
    cfg = w.run(
        "SELECT proconfig FROM pg_proc WHERE oid = to_regprocedure('hadavin_release_expired_spend(text, date)')"
    )[0][0]
    (entry,) = [c for c in cfg if c.startswith("search_path=")]
    return [p.strip().strip('"') for p in entry.split("=", 1)[1].split(",")]


def test_the_pin_survives_a_second_migrate(w):
    w.migrate(release_role=w.release)
    assert _pin(w) == ["pg_catalog", w.schema, "pg_temp"]  # not the 0008 placeholder


def test_a_hand_run_create_or_replace_drops_the_pin_and_migrate_puts_it_back(w):
    from hadavin_sdk.store.migrate import MIGRATIONS

    text = (MIGRATIONS / "0008_release_expired_spend.sql").read_text()
    start = text.index("CREATE OR REPLACE FUNCTION")
    w.do(text[start : text.index("$fn$;", text.index("AS $fn$") + 7) + len("$fn$;")])
    assert _pin(w) == [
        "pg_catalog",
        "pg_temp",
    ]  # the reset: fails closed, the money tables are not found
    w.migrate(release_role=w.release)
    assert _pin(w) == ["pg_catalog", w.schema, "pg_temp"]
