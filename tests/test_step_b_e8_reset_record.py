"""E12 Medium 3 and 4, code side (B8): the reset writes its own record (there is no watermark table, review N3), and the gate read
stays correct and fast with very many cleared stops. Real PostgreSQL, throwaway schema and roles (the stop-state
world of tests/test_stop_state_roles.py), dropped after. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
import time

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")


from hadavin_sdk.models import KillSwitch
from tests.test_stop_state_roles import DENIED, stop_world  # noqa: F401  (fixture `w`)

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


def _reset(w, by="admin:reset"):
    rs = w.store(w.reset)
    ids = [s.id for s in rs.open_stops()]
    rs.clear_stops(by, ids)
    return ids


def test_reset_writes_one_record_with_the_cleared_ids(w):
    rt = w.store(w.runtime)
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    rt.set_kill_switch(KillSwitch(on=True, by="op:b"))
    ids = _reset(w)
    rows = w.run('SELECT "by", cleared_ids::text[], audit_seq FROM kill_switch_resets')
    assert len(rows) == 1
    assert rows[0][0] == "admin:reset" and sorted(rows[0][1]) == sorted(ids) and rows[0][2] is None
    # a second reset with nothing open: one more record with no cleared id
    _reset(w, "admin:again")
    assert w.run("SELECT count(*) FROM kill_switch_resets")[0][0] == 2
    last = w.run('SELECT cleared_ids FROM kill_switch_resets WHERE "by" = %s', ("admin:again",))
    assert last[0][0] == []


def test_audit_seq_is_stored_when_the_caller_knows_it(w):
    w.store(w.runtime).set_kill_switch(KillSwitch(on=True, by="op:a"))
    rs = w.store(w.reset)
    rs.clear_stops("admin:reset", [s.id for s in rs.open_stops()], audit_seq=7)
    assert w.run("SELECT audit_seq FROM kill_switch_resets")[0][0] == 7


def test_a_stop_set_during_the_reset_stays_on_and_is_not_hidden(w):
    rt = w.store(w.runtime)
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    rs = w.store(w.reset)
    seen = [s.id for s in rs.open_stops()]
    rt.set_kill_switch(KillSwitch(on=True, by="op:late"))  # after the read, before the clear
    rs.clear_stops("admin:reset", seen)
    got = w.read()
    assert got.on and got.by == "op:late"
    assert [s.by for s in rs.open_stops()] == ["op:late"]
    ids = w.run("SELECT cleared_ids::text[] FROM kill_switch_resets")[0][0]
    assert ids == seen


def test_a_hand_inserted_older_stop_after_the_reset_still_counts_as_open(w):
    rt = w.store(w.runtime)
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    _reset(w)
    assert not w.read().on
    through = w.run("SELECT max(ts) FROM kill_switch_stops")[0][0]  # the cleared stop's time
    # a stop with a time well below it, inserted by the runtime login itself (it may INSERT stops)
    with w.as_(w.runtime) as db:
        db.execute(
            "INSERT INTO kill_switch_stops (\"by\", ts) VALUES ('planted:old', %s - interval '30 days')",
            (through,),
        )
    got = w.read()
    assert got.on and got.by == "planted:old"
    assert [s.by for s in w.store(w.reset).open_stops()] == ["planted:old"]


def test_the_runtime_cannot_touch_the_resets_table(w):
    _stop = w.store(w.runtime)
    _stop.set_kill_switch(KillSwitch(on=True, by="op:a"))
    _reset(w)
    with w.as_(w.runtime) as db:
        for stmt in (
            "SELECT * FROM kill_switch_resets",
            "INSERT INTO kill_switch_resets (\"by\") VALUES ('x')",
        ):
            with pytest.raises(DENIED):
                db.execute(stmt)
    with w.as_(w.reset) as db, pytest.raises(DENIED):  # the reset login cannot edit its record
        db.execute("UPDATE kill_switch_resets SET \"by\" = 'x'")


def test_the_gate_read_is_fast_with_many_cleared_stops_and_still_sees_a_new_one(w):
    n = 200_000
    w.do(
        "INSERT INTO kill_switch_stops (id, \"by\", ts) SELECT gen_random_uuid(), 'bulk', "  # noqa: S608
        f"'2020-01-01'::timestamptz + (g || ' seconds')::interval FROM generate_series(1, {n}) g"
    )
    w.do(
        "INSERT INTO kill_switch_clears (stop_id, \"by\", ts) SELECT id, 'bulk', ts FROM kill_switch_stops"
    )
    w.do("ANALYZE kill_switch_stops")
    w.do("ANALYZE kill_switch_clears")
    rs = w.store(w.reset)
    rs.clear_stops("admin:reset", [])  # flag off
    rt = w.store(w.runtime)
    t0 = time.monotonic()
    got = rt.get_kill_switch()
    took = time.monotonic() - t0
    assert not got.on
    assert took < 1.0, f"gate read took {took:.2f}s with {n} cleared stops"
    rt.set_kill_switch(KillSwitch(on=True, by="op:new"))
    got = rt.get_kill_switch()
    assert got.on and got.by == "op:new"
