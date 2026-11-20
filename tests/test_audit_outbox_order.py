"""N3 (xr-abc-lead-1): the outbox is read oldest instant first. The body is text, so the order must not be the text
order of `ts`: a fraction-less ts sorts after a fractional one, and a non-UTC offset sorts by its wall clock.
A row with a malformed ts or a body that is not JSON sorts last and never fails the read. SQLite always; PostgreSQL
with HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import threading

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.audit import chain as audit

# (event id, ts text): listed in the order the read must return them.
ROWS = [
    ("e1", '"2026-01-01T09:30:00+02:00"'),  # 07:30:00Z, the oldest; its text sorts last
    (
        "e2",
        '"2026-01-01T08:00:00Z"',
    ),  # 08:00:00, no fraction: its text sorts after the fractional one
    ("e3", '"2026-01-01T08:00:00.250000Z"'),  # 08:00:00.25
    ("e4", '"2026-01-01T08:00:01+00:00"'),
    ("e5", '"2026-01-01T08:00:02"'),  # no offset: UTC
    ("e6", '"not-a-date"'),  # malformed ts: last, in event id order with the others
    ("e7", None),  # not JSON
]


def _body(ts):
    return "garbage {" if ts is None else f'{{"event_id":"x","ts":{ts}}}'


def _order(db):
    for event_id, ts in reversed(ROWS):  # inserted against the expected order
        db.run("INSERT INTO audit_outbox (event_id, body) VALUES (?, ?)", (event_id, _body(ts)))
    log = audit.ChainAudit(db)
    page = db.run(log._outbox_sql(), (defaults.AUDIT_QUARANTINE_PREFIX + "%", 100, 0))
    return [r[0] for r in page]


def test_sqlite_outbox_is_read_by_instant_not_by_text():
    assert _order(audit._Db.memory()) == [r[0] for r in ROWS]


def test_the_text_order_would_be_wrong():
    """The premise: sorted as text the rows come out differently."""
    texts = sorted((ts or "~", i) for i, ts in ROWS)
    assert [i for _, i in texts] != [r[0] for r in ROWS]


def test_postgres_outbox_is_read_by_instant_not_by_text():
    pytest.importorskip("psycopg")
    import psycopg

    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema():
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute("SET TIME ZONE 'UTC'")
            assert _order(audit._Db(conn, threading.Lock(), pg=True)) == [r[0] for r in ROWS]


def test_postgres_a_wellformed_but_impossible_ts_sorts_last_and_never_fails_the_read():
    """Review M-1: 2026-02-30, hour 25 and year 0000 match a shape check but the timestamptz cast raises."""
    pytest.importorskip("psycopg")
    import psycopg

    from tests.contracts.kinds.store_postgres import pg_schema

    bad = [
        ("b1", '"2026-02-30T00:00:00Z"'),
        ("b2", '"2026-01-01T25:00:00Z"'),
        ("b3", '"0000-01-01T00:00:00Z"'),
    ]
    for dsn in pg_schema():
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute("SET TIME ZONE 'UTC'")
            db = audit._Db(conn, threading.Lock(), pg=True)
            for event_id, ts in bad + [("a1", '"2026-01-01T08:00:00Z"')]:
                db.run(
                    "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?)", (event_id, _body(ts))
                )
            log = audit.ChainAudit(db)
            page = db.run(log._outbox_sql(), (defaults.AUDIT_QUARANTINE_PREFIX + "%", 100, 0))
            assert [r[0] for r in page] == ["a1", "b1", "b2", "b3"]


# B-1 (xreview-bfix2 finding 1): out-of-range ts values planted by the runtime login must sort last and never fail
# the read; valid boundary values must still be ordered by instant.
_HOSTILE = [
    ("b1", '"2026-13-45T25:61:61Z"'),
    ("b2", '"2026-01-01T08:00:00+99:99"'),
    ("b3", '"2026-01-01T08:00:00+16:00"'),
    ("b4", '"2023-02-29T00:00:00Z"'),  # not a leap year
    ("b5", '"1900-02-29T00:00:00Z"'),  # century, not a leap year
    ("b6", '"2026-01-01T08:00:60Z"'),
]
# Valid boundaries, oldest instant first (the text order differs for the offset rows).
_VALID = [
    ("v1", '"2024-02-29T23:59:59Z"'),  # leap day
    ("v2", '"2024-03-01T05:00:00+14:00"'),  # 2024-02-29T15:00:00Z, the offset limit: older than v1
    ("v3", '"2024-03-01T00:00:00Z"'),
    ("v4", '"2000-02-29T00:00:00Z"'),  # century leap year: oldest
]


def _order_of(db, rows):
    for event_id, ts in rows:
        db.run("INSERT INTO audit_outbox (event_id, body) VALUES (?, ?)", (event_id, _body(ts)))
    log = audit.ChainAudit(db)
    page = db.run(log._outbox_sql(), (defaults.AUDIT_QUARANTINE_PREFIX + "%", 100, 0))
    return [r[0] for r in page]


_EXPECTED = ["v4", "v2", "v1", "v3", "b1", "b2", "b3", "b4", "b5", "b6"]


def test_sqlite_hostile_ts_sorts_last_and_valid_boundaries_keep_their_instant_order():
    # SQLite's julianday is lenient (it rolls 1900-02-29 over to 1 March), so only the read not failing, every
    # row returned and the valid rows keeping their instant order are pinned here; PostgreSQL pins the full order.
    order = _order_of(audit._Db.memory(), _HOSTILE + _VALID)
    assert sorted(order) == sorted(_EXPECTED)
    assert [i for i in order if i.startswith("v")] == ["v4", "v2", "v1", "v3"]


def test_postgres_hostile_ts_sorts_last_and_valid_boundaries_keep_their_instant_order():
    pytest.importorskip("psycopg")
    import psycopg

    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema():
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute("SET TIME ZONE 'UTC'")
            db = audit._Db(conn, threading.Lock(), pg=True)
            assert _order_of(db, _HOSTILE + _VALID) == _EXPECTED
