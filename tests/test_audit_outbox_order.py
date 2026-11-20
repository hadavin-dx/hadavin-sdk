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
