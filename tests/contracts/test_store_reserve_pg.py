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
REFUSED_MESSAGE = "spend_reservations: change refused"
# One whole statement per target status (no text is built from parts). `%s` is the reservation id.
TO = {
    "open": "UPDATE spend_reservations SET status = 'open', settled_usd = NULL, closed_at = NULL, "
    "expired_at = NULL WHERE reservation_id = %s",
    "settled": "UPDATE spend_reservations SET status = 'settled', settled_usd = 1, closed_at = now() "
    "WHERE reservation_id = %s",
    "released": "UPDATE spend_reservations SET status = 'released', settled_usd = NULL, closed_at = now() "
    "WHERE reservation_id = %s",
    "expired": "UPDATE spend_reservations SET status = 'expired', settled_usd = 1, closed_at = now(), "
    "expired_at = now() WHERE reservation_id = %s",
}


def _make(conn, rid, state):
    """A row in `state`, reached only by legal steps: open, then (for expired) open to expired, or (for settled
    and released) open to that status."""
    drv.execute(conn, INSERT.format(extra="", vals=""), (rid,))
    if state != "open":
        drv.execute(conn, TO[state], (rid,))


def _status(conn, rid):
    return drv.execute(
        conn, "SELECT status FROM spend_reservations WHERE reservation_id = %s", (rid,)
    )


@pytest.mark.parametrize(("old", "new"), [(a, b) for a in STATES for b in STATES])
def test_the_status_transition_matrix(rt, old, new):
    """All 16 pairs. The 5 allowed ones succeed; the other 11 fail with the trigger's own error (P0001 and the
    fixed message), never with a CHECK (a BEFORE trigger runs before the CHECKs, so a CHECK code would mean the
    trigger let the pair through)."""
    rid = f"m-{old}-{new}"
    _make(rt, rid, old)
    if (old, new) in ALLOWED:
        drv.execute(rt, TO[new], (rid,))
        assert _status(rt, rid) == [(new,)]
    else:
        assert REFUSED_MESSAGE in _refused(rt, TO[new], (rid,))
        assert _status(rt, rid) == [(old,)]


# The 5 allowed transitions, each as one whole statement with a `{}` for the frozen column that is changed too.
CARRYING = {
    ("open", "expired"): "UPDATE spend_reservations SET status = 'expired', settled_usd = 1, "
    "closed_at = now(), expired_at = now(), {} = %s WHERE reservation_id = %s",
    ("open", "settled"): "UPDATE spend_reservations SET status = 'settled', settled_usd = 1, "
    "closed_at = now(), {} = %s WHERE reservation_id = %s",
    ("open", "released"): "UPDATE spend_reservations SET status = 'released', closed_at = now(), "
    "{} = %s WHERE reservation_id = %s",
    ("expired", "settled"): "UPDATE spend_reservations SET status = 'settled', settled_usd = 1, "
    "closed_at = now(), {} = %s WHERE reservation_id = %s",
    (
        "expired",
        "released",
    ): "UPDATE spend_reservations SET status = 'released', settled_usd = NULL, "
    "closed_at = now(), {} = %s WHERE reservation_id = %s",
}
# Frozen column -> a different value as text (the server reads an untyped text value as the column's type).
FROZEN = {
    "reservation_id": "other-id",
    "schema_version": "2",
    "agent_id": "b",
    "day": "2030-01-01",
    "run_id": "run-none",
    "reserved_usd": "2",
    "created_at": "2000-01-01T00:00:00Z",
    "meta": '{"x": 1}',
}


@pytest.mark.parametrize("column", list(FROZEN))
@pytest.mark.parametrize(("old", "new"), sorted(ALLOWED))
def test_an_allowed_transition_cannot_carry_a_change_of_a_frozen_column(rt, old, new, column):
    """5 transitions x 8 frozen columns = 40 rows, each refused by the trigger (P0001, fixed message), with the
    row left as it was."""
    rid = f"f-{old}-{new}-{column}"
    _make(rt, rid, old)
    with pytest.raises(Exception) as caught:
        drv.execute(rt, CARRYING[(old, new)], (FROZEN[column], rid), idents=(column,))
    assert drv.sqlstate(caught.value) == "P0001"
    assert REFUSED_MESSAGE in str(caught.value)
    assert _status(rt, rid) == [(old,)]


def test_expired_to_settled_must_keep_expired_at(rt):
    _make(rt, "k1", "expired")
    _refused(
        rt,
        "UPDATE spend_reservations SET status = 'settled', settled_usd = 1, closed_at = now(), "
        "expired_at = now() + interval '1 hour' WHERE reservation_id = 'k1'",
    )


@pytest.mark.parametrize(
    "statement",
    [
        (
            "UPDATE spend_reservations SET status = 'expired', settled_usd = 2, closed_at = now(), "
            "expired_at = now() WHERE reservation_id = %s"
        ),  # settled_usd differs from reserved_usd
        (
            "UPDATE spend_reservations SET status = 'expired', settled_usd = 1, closed_at = NULL, "
            "expired_at = now() WHERE reservation_id = %s"
        ),  # closed_at missing
        (
            "UPDATE spend_reservations SET status = 'expired', settled_usd = 1, closed_at = now(), "
            "expired_at = NULL WHERE reservation_id = %s"
        ),  # expired_at missing
    ],
    ids=["settled_usd-differs", "closed_at-null", "expired_at-null"],
)
def test_open_to_expired_needs_its_three_fields(rt, statement):
    _make(rt, "e1", "open")
    assert REFUSED_MESSAGE in _refused(rt, statement, ("e1",))


@pytest.mark.parametrize("target", ["settled", "released"])
def test_expired_to_settled_or_released_cannot_change_expired_at(rt, target):
    _make(rt, f"x-{target}", "expired")
    statement = (
        "UPDATE spend_reservations SET status = 'settled', settled_usd = 1, closed_at = now(), "
        "expired_at = now() + interval '1 hour' WHERE reservation_id = %s"
        if target == "settled"
        else "UPDATE spend_reservations SET status = 'released', settled_usd = NULL, closed_at = now(), "
        "expired_at = now() + interval '1 hour' WHERE reservation_id = %s"
    )
    assert REFUSED_MESSAGE in _refused(rt, statement, (f"x-{target}",))


@pytest.mark.parametrize(
    ("statement", "params", "code"),
    [
        (
            (
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, reserved_usd) "
                "VALUES ('i1', 1, 'a', current_date, 'NaN')"
            ),
            (),
            "23514",
        ),
        (
            (
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, reserved_usd) "
                "VALUES ('i2', 1, 'a', current_date, -1)"
            ),
            (),
            "23514",
        ),
        (
            (
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, reserved_usd) "
                "VALUES ('i3', 1, 'a', current_date, 0.0000001)"
            ),
            (),
            "23514",
        ),
        (
            (
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, reserved_usd) "
                "VALUES ('bad id', 1, 'a', current_date, 1)"
            ),
            (),
            "23514",
        ),
        (
            (
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, reserved_usd) "
                "VALUES ('i5', 1, 'bad agent', current_date, 1)"
            ),
            (),
            "23514",
        ),
        (
            (
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, reserved_usd) "
                "VALUES ('i6', 1, 'a', DATE '0001-01-01', 1)"
            ),
            (),
            "23514",
        ),
        (
            (
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, run_id, reserved_usd) "
                "VALUES ('i7', 1, 'a', current_date, 'run-none', 1)"
            ),
            (),
            "23503",
        ),
    ],
    ids=["nan", "negative", "seven-decimals", "bad-id", "bad-agent", "day-0001", "unknown-run"],
)
def test_the_insert_rules_refuse_what_the_grammar_forbids(rt, statement, params, code):
    _refused(rt, statement, params, code=code)


@pytest.mark.parametrize(
    "statement",
    [
        (
            "UPDATE spend_reservations SET status = 'released', closed_at = now(), reserved_usd = 2 "
            "WHERE reservation_id = 'c1'"
        ),
        (
            "UPDATE spend_reservations SET status = 'released', closed_at = now(), agent_id = 'b' "
            "WHERE reservation_id = 'c1'"
        ),
        (
            "UPDATE spend_reservations SET status = 'released', closed_at = now(), day = day + 1 "
            "WHERE reservation_id = 'c1'"
        ),
        (
            "UPDATE spend_reservations SET status = 'released', closed_at = now(), meta = jsonb_build_object() "
            "WHERE reservation_id = 'c1'"
        ),
        (
            "UPDATE spend_reservations SET status = 'released', closed_at = now(), schema_version = 2 "
            "WHERE reservation_id = 'c1'"
        ),
    ],
    ids=["reserved_usd", "agent_id", "day", "meta", "schema_version"],
)
def test_a_legal_transition_cannot_carry_a_change_of_an_identity_field(rt, statement):
    drv.execute(rt, INSERT.format(extra="", vals=""), ("c1",))
    assert "change refused" in _refused(rt, statement)
