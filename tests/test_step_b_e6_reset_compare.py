"""E6 Major 1 (hostile review 2): a reset clears exactly the stops the operator was shown (compare-and-clear).

Before: `limits reset` cleared EVERY stop its clear statement could see, so a stop set between the audit intent and
that statement was erased, and the command printed `kill switch OFF`, exit 0. Now the reset reads the open stops
first, writes their ids into the audit intent, clears only those ids, and any other open stop keeps the switch ON
(exit 2, naming it). The memory store has the same semantics. Postgres cases need HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import hashlib
import os

import pytest

from hadavin_sdk import cli
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import AuditEvent, KillSwitch
from hadavin_sdk.store.memory import MemoryStore

needs_pg = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


class RecAudit:
    """Records the events written; an intent can be made to run a hook (a colleague stops meanwhile)."""

    def __init__(self, during_intent=None):
        self.events: list[tuple[str, AuditEvent]] = []
        self.during_intent = during_intent

    def write_intent(self, event):
        if self.during_intent:
            self.during_intent()
        self.events.append(("intent", event))

    def write_outcome(self, event):
        self.events.append(("outcome", event))


# ---- the store contract, both stores --------------------------------------------------------------------------------


def _stores(request):
    return request.param


def _memory():
    return MemoryStore(), MemoryStore


@pytest.fixture(params=["memory", pytest.param("postgres", marks=needs_pg)])
def pair(request):
    """(runtime-side store, reset-side store): the same object for memory, two logins for Postgres."""
    if request.param == "memory":
        s = MemoryStore()
        yield s, s
        return
    from tests.test_stop_state_roles import stop_world

    gen = stop_world.__wrapped__() if hasattr(stop_world, "__wrapped__") else None
    w = next(gen)
    try:
        yield w.store(w.runtime), w.store(w.reset)
    finally:
        with pytest.raises(StopIteration):
            next(gen)


def test_open_stops_lists_each_open_stop_oldest_first_with_a_unique_id(pair):
    rt, rs = pair
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    rt.set_kill_switch(KillSwitch(on=True, by="op:b"))
    stops = rs.open_stops()
    assert [s.by for s in stops] == ["op:a", "op:b"]
    assert len({s.id for s in stops}) == 2


def test_clear_stops_clears_exactly_the_given_ids_and_a_later_stop_stays_on(pair):
    rt, rs = pair
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    seen = [s.id for s in rs.open_stops()]
    rt.set_kill_switch(KillSwitch(on=True, by="op:bob"))  # set after the read
    rs.clear_stops("admin:reset", seen)
    ks = rt.get_kill_switch()
    assert (ks.on, ks.by) == (True, "op:bob")
    assert [s.by for s in rs.open_stops()] == ["op:bob"]


def test_clear_stops_with_every_open_id_reads_off_and_a_stop_after_it_reads_on(pair):
    rt, rs = pair
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    rt.set_kill_switch(KillSwitch(on=True, by="op:b"))
    rs.clear_stops("admin:reset", [s.id for s in rs.open_stops()])
    assert rt.get_kill_switch().on is False and rs.open_stops() == []
    rt.set_kill_switch(KillSwitch(on=True, by="op:later"))
    ks = rt.get_kill_switch()
    assert (ks.on, ks.by) == (True, "op:later")


def test_clear_stops_with_no_ids_changes_no_stop(pair):
    rt, rs = pair
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    rs.clear_stops("admin:reset", [])
    assert rt.get_kill_switch().on is True


def test_clear_stops_ignores_an_id_that_is_not_a_stop_or_already_cleared(pair):
    rt, rs = pair
    rt.set_kill_switch(KillSwitch(on=True, by="op:a"))
    ids = [s.id for s in rs.open_stops()]
    rs.clear_stops("admin:reset", ids)
    rs.clear_stops("admin:reset2", [*ids, "00000000-0000-4000-8000-000000000000"])
    assert rt.get_kill_switch().on is False


# ---- Limits.reset and the CLI, memory store -------------------------------------------------------------------------


def test_the_audit_intent_carries_the_ids_it_is_about_to_clear_and_a_count():
    store = MemoryStore()
    store.set_kill_switch(KillSwitch(on=True, by="op:a"))
    store.set_kill_switch(KillSwitch(on=True, by="op:b"))
    ids = [s.id for s in store.open_stops()]
    audit = RecAudit()
    Limits(store, audit, None).reset("op:carol")
    kind, event = audit.events[0]
    assert kind == "intent" and event.operation == "reset"
    assert all(i in (event.object_ref or "") for i in ids)
    assert event.inputs_hash == hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
    assert store.get_kill_switch().on is False


def test_a_stop_set_during_the_audit_intent_stays_on_and_the_cli_names_it(capsys):
    store = MemoryStore()
    store.set_kill_switch(KillSwitch(on=True, by="op:alice"))
    audit = RecAudit(
        during_intent=lambda: store.set_kill_switch(KillSwitch(on=True, by="op:bob EMERGENCY"))
    )
    code = cli.kill_switch(Limits(store, audit, None), "reset", "op:carol")
    err = capsys.readouterr().err
    assert code == 2
    assert "kill switch still ON" in err and "op:bob EMERGENCY" in err
    assert store.get_kill_switch().on is True
    assert [s.by for s in store.open_stops()] == ["op:bob EMERGENCY"]


def test_a_reset_with_nothing_set_meanwhile_prints_off_and_how_many_it_cleared(capsys):
    store = MemoryStore()
    store.set_kill_switch(KillSwitch(on=True, by="op:alice"))
    code = cli.kill_switch(Limits(store, RecAudit(), None), "reset", "op:carol")
    assert code == 0
    assert "kill switch OFF (by op:carol; cleared 1 stop(s))" in capsys.readouterr().out
    assert store.get_kill_switch().on is False


# ---- the repro of the review, real Postgres ------------------------------------------------------------------------


@needs_pg
def test_a7_a_stop_set_just_before_the_clear_statement_is_not_erased_exit_2():
    from hadavin_sdk.backends.factory import make
    from hadavin_sdk.backends.table import ChainSettings
    from tests.test_stop_state_roles import stop_world

    gen = stop_world.__wrapped__()
    w = next(gen)
    try:
        rt, rs = w.store(w.runtime), w.store(w.reset)
        audit = make("audit", ChainSettings(kind="chain"), store=rs, signer=None, anchor=None)
        rt.set_kill_switch(KillSwitch(on=True, by="op:alice"))
        alice = [r[0] for r in w.run("SELECT id::text FROM kill_switch_stops")]
        orig = rs._exec

        def hooked(q, p=()):
            if "INSERT" in q.as_string(rs._db) and "kill_switch_clears" in q.as_string(rs._db):
                rt.set_kill_switch(KillSwitch(on=True, by="op:bob EMERGENCY"))
            return orig(q, p)

        rs._exec = hooked
        code = cli.kill_switch(Limits(rs, audit, None), "reset", "op:carol")
        rs._exec = orig
        assert code == 2
        ks = rt.get_kill_switch()
        assert (ks.on, ks.by) == (True, "op:bob EMERGENCY")
        cleared = {r[0] for r in w.run("SELECT stop_id::text FROM kill_switch_clears")}
        assert cleared == set(alice)
        body = w.run("SELECT body FROM audit_entries WHERE kind = 'limits.reset'")
        assert alice[0] in body[0][0] and "bob" not in body[0][0]
    finally:
        with pytest.raises(StopIteration):
            next(gen)
