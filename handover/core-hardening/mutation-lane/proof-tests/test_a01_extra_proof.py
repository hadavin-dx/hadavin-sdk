"""PROOF-ONLY extra tests (scratch copy, not applied): kill the A-01 survivors."""

import logging
from datetime import timedelta

from hadavin_sdk.audit import chain as audit
from hadavin_sdk.audit.local_dir import LocalDirSink
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.runtime import tick
from hadavin_sdk.runtime.tick import TickStep, run_tick

# the existing `app` fixture of the tick tests, registered as a plugin: no import of the name, so no suppression
pytest_plugins = ["tests.test_p7_tick"]


def _event(i=0):
    return AuditEvent(
        run_id=f"run-{i}",
        domain="run",
        operation="state",
        principal="system:test",
        source="test",
        result="OK",
    )


def _boom(*a, **k):
    raise OSError("secret-looking detail")


def _step():
    return next(s for s in tick.STEPS if s.name == "audit_reconcile")


def test_the_list_entry_runs_audit_reconcile_every_tick():
    step = _step()
    assert step.fn is tick.audit_reconcile
    assert step.every_s == 0 and step.interval is None


def test_two_ticks_in_a_row_both_call_reconcile(app, monkeypatch):
    calls = []

    class Sink:
        def reconcile(self):
            calls.append(1)
            return 0

    monkeypatch.setattr(app, "audit", Sink())
    now = app.approvals.clock()
    assert run_tick(app, now=now, steps=[_step()]) == 0
    assert run_tick(app, now=now + timedelta(seconds=1), steps=[_step()]) == 0
    assert len(calls) == 2


def test_the_reconcile_result_is_what_gets_logged(caplog):
    class Sink:
        def reconcile(self):
            return 7

    caplog.set_level(logging.INFO, logger="hadavin_sdk.tick")
    tick.audit_reconcile(tick.TickContext(type("A", (), {"audit": Sink()})(), now=None))
    assert "audit_reconcile drained=7" in caplog.text


def test_local_dir_failed_outcome_logs_a_warning_with_type_and_id_only(tmp_path, caplog):
    sink = LocalDirSink(tmp_path)
    sink._write = _boom
    ev = _event(4)
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.audit.local_dir"):
        assert sink.write_outcome(ev) is None
    recs = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(recs) == 1
    assert "OSError" in caplog.text and ev.event_id in caplog.text
    assert "secret-looking detail" not in caplog.text and "run-4" not in caplog.text


def test_chain_duplicate_outcome_is_not_an_outage():
    log = audit.ChainAudit(audit._Db.memory())
    ev = _event(5)
    assert log.write_outcome(ev) == ev.event_id
    assert log.write_outcome(ev) == ev.event_id  # the duplicate answers with the id, never None
    assert log._db.run("SELECT event_id FROM audit_outbox") == []


def test_local_dir_duplicate_outcome_is_not_an_outage(tmp_path):
    sink = LocalDirSink(tmp_path)
    ev = _event(6)
    first = sink.write_outcome(ev)
    assert first is not None
    assert sink.write_outcome(ev) == f"{ev.event_id}.json"
    assert not list(sink.outbox.glob("*.json")) if sink.outbox.exists() else True


def test_chain_reconcile_drains_memory_only_events_once():
    log = audit.ChainAudit(audit._Db.memory())
    real_append, real_run = log._append, log._db.run
    log._append = _boom
    log._db.run = _boom
    ev = _event(7)
    assert log.write_outcome(ev) is None and len(log._pending) == 1
    log._append, log._db.run = real_append, real_run
    assert log.reconcile() == 1
    assert log._pending == []
    assert log.reconcile() == 0  # not counted again
    assert log._db.run("SELECT event_id FROM audit_entries WHERE event_id = ?", (ev.event_id,)) == [
        (ev.event_id,)
    ]


def test_chain_reconcile_keeps_an_event_whose_append_still_fails():
    log = audit.ChainAudit(audit._Db.memory())
    log._append = _boom
    ev = _event(8)
    log.write_outcome(ev)  # lands in the outbox table
    assert log.reconcile() == 0  # the append still fails: nothing counted ...
    assert len(log._db.run("SELECT event_id FROM audit_outbox")) == 1  # ... and nothing dropped


def test_local_dir_reconcile_drains_memory_only_events_once(tmp_path):
    sink = LocalDirSink(tmp_path)
    real_write = sink._write
    sink._write = _boom
    sink.outbox.write_text("a file where the folder should be")  # outbox unusable too
    ev = _event(9)
    assert sink.write_outcome(ev) is None and len(sink._pending) == 1
    sink._write = real_write
    sink.outbox.unlink()
    assert sink.reconcile() == 1
    assert sink._pending == []
    assert [e.event_id for e in sink.events()] == [ev.event_id]


def test_a_raising_step_does_not_stop_the_next_and_is_recorded(app):
    ran = []

    def boom(ctx):
        raise RuntimeError("x")

    steps = [TickStep("first", 0, boom), TickStep("second", 0, lambda ctx: ran.append(1))]
    assert run_tick(app, steps=steps) == 1
    assert ran == [1] and app.store.get_tick_state("first").last_error.startswith("RuntimeError")
