"""P4d-b, Postgres only: what the runtime login may do to `spend_reservations` (the triggers, the grants) and the
migration text. Not a `store` test: it needs no memory twin."""

import re
from pathlib import Path

import pytest

from tests.contracts.kinds.store_postgres import pg_driver, pg_schema

drv = pg_driver(module_level=True)
MIGRATION = next(
    (Path(__file__).parents[2] / "src/hadavin_sdk/store/migrations").glob(
        "*_spend_reservations.sql"
    )
)
INSERT = (
    "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, reserved_usd{extra}) "
    "VALUES (%s, 1, 'a', current_date, 1{vals})"
)


@pytest.fixture
def rt():
    for dsn in pg_schema(runtime=True):
        with drv.connect_runtime(dsn) as conn:
            who = drv.execute(
                conn,
                "SELECT current_user, (SELECT rolsuper FROM pg_roles WHERE rolname = current_user)",
            )[0]
            assert who[1] is False  # the checks below mean something only for a non-superuser
            yield conn


def _refused(conn, sql, params=(), code="P0001"):
    with pytest.raises(Exception) as caught:
        drv.execute(conn, sql, params)
    assert drv.sqlstate(caught.value) == code
    return str(caught.value)


def test_the_first_statement_is_the_lock_timeout():
    text = re.sub(r"--[^\n]*", "", MIGRATION.read_text(encoding="utf-8")).strip()
    assert text.startswith("SET LOCAL lock_timeout = '10s';")


def test_a_direct_update_of_a_ledger_field_is_refused_by_the_trigger_not_a_check(rt):
    drv.execute(rt, INSERT.format(extra="", vals=""), ("r1",))
    assert "spend_reservations: change refused" in _refused(
        rt, "UPDATE spend_reservations SET reserved_usd = 0.5 WHERE reservation_id = 'r1'"
    )
    drv.execute(
        rt,
        "UPDATE spend_reservations SET status = 'settled', settled_usd = 1, closed_at = now() "
        "WHERE reservation_id = 'r1'",
    )
    assert "change refused" in _refused(
        rt,
        "UPDATE spend_reservations SET status = 'open', closed_at = NULL, settled_usd = NULL "
        "WHERE reservation_id = 'r1'",
    )
    # a CHECK failure is a different code from the trigger's
    drv.execute(rt, INSERT.format(extra="", vals=""), ("r2",))
    _refused(
        rt,
        "UPDATE spend_reservations SET status = 'settled', closed_at = now() WHERE reservation_id = 'r2'",
        code="23514",
    )


def test_insert_rules_and_no_delete(rt):
    _refused(
        rt,
        INSERT.format(extra=", status, settled_usd, closed_at", vals=", 'settled', 1, now()"),
        ("r3",),
    )
    drv.execute(rt, INSERT.format(extra=", created_at", vals=", now() + interval '1 day'"), ("r4",))
    ok = drv.execute(
        rt,
        "SELECT created_at <= clock_timestamp() FROM spend_reservations WHERE reservation_id = 'r4'",
    )
    assert ok == [(True,)]  # a future created_at was replaced by the database clock
    _refused(rt, "DELETE FROM spend_reservations WHERE reservation_id = 'r4'", code="42501")
    _refused(rt, INSERT.format(extra="", vals="").replace("'a'", "'bad id'"), ("r5",), code="23514")
    _refused(rt, INSERT.format(extra=", run_id", vals=", 'run-none'"), ("r6",), code="23503")


STATES = ("open", "settled", "released", "expired")
ALLOWED = {
    ("open", "expired"),
    ("open", "settled"),
    ("open", "released"),
    ("expired", "settled"),
    ("expired", "released"),
}
SET = {
    "open": "status = 'open', settled_usd = NULL, closed_at = NULL, expired_at = NULL",
    "settled": "status = 'settled', settled_usd = 1, closed_at = now()",
    "released": "status = 'released', settled_usd = NULL, closed_at = now()",
    "expired": "status = 'expired', settled_usd = 1, closed_at = now(), expired_at = now()",
}


def _make(conn, rid, state):
    drv.execute(conn, INSERT.format(extra="", vals=""), (rid,))
    if state != "open":
        drv.execute(
            conn,
            f"UPDATE spend_reservations SET {SET['expired' if state == 'expired' else 'open']} "  # noqa: S608
            "WHERE reservation_id = %s"
            if state == "expired"
            else "SELECT 1",
            (rid,) if state == "expired" else (),
        )
    if state in ("settled", "released"):
        sql = f"UPDATE spend_reservations SET {SET[state]} WHERE reservation_id = %s"  # noqa: S608
        drv.execute(conn, sql, (rid,))


@pytest.mark.parametrize(("old", "new"), [(a, b) for a in STATES for b in STATES])
def test_the_status_transition_matrix(rt, old, new):
    rid = f"m-{old}-{new}"
    _make(rt, rid, old)
    sql = f"UPDATE spend_reservations SET {SET[new]} WHERE reservation_id = %s"  # noqa: S608
    if (old, new) in ALLOWED:
        drv.execute(rt, sql, (rid,))
        assert drv.execute(
            rt, "SELECT status FROM spend_reservations WHERE reservation_id = %s", (rid,)
        ) == [(new,)]
    else:
        # the same-status pairs and the backward ones: the trigger, or a check on the row, refuses them
        with pytest.raises(Exception) as caught:
            drv.execute(rt, sql, (rid,))
        assert drv.sqlstate(caught.value) in ("P0001", "23514")
        if drv.sqlstate(caught.value) == "P0001":
            assert "spend_reservations: change refused" in str(caught.value)


def test_expired_to_settled_must_keep_expired_at(rt):
    _make(rt, "k1", "expired")
    _refused(
        rt,
        "UPDATE spend_reservations SET status = 'settled', settled_usd = 1, closed_at = now(), "
        "expired_at = now() + interval '1 hour' WHERE reservation_id = 'k1'",
    )
