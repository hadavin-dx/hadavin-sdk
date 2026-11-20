"""d-fix10 e1-fix3: a ping that fails with a refusal (not a connectivity error) counts toward the degraded
worker's fatal count; a conflict event that cannot be built leaves no stuck flag; a late close also closes the
App's store. Memory store."""

from __future__ import annotations

import argparse
import logging
import threading
import time

import pytest

from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import StoreUnavailable
from hadavin_sdk.triggers import worker
from hadavin_sdk.triggers.worker import Runner
from tests.triggers.test_d_fix6_e1 import (  # noqa: F401 - the autouse fixture is needed here too
    DOCUMENT,
    NOW,
    OTHER_DOCUMENT,
    _free,
    _get,
    _no_worker_log_handler,
    _req,
    _settle,
    _switch_app,
    rt,
)
from tests.triggers.test_d_fix8_e1fix import _http
from tests.triggers.test_d_fix9_e1fix2 import ARGS, Closing


class Refused(RuntimeError):
    """Stands for a store that answered with a refusal (a missing table, a missing grant)."""


class Failing(MemoryStore):
    """get_run of the ping id raises `exc` (a class), every time."""

    def __init__(self, exc):
        super().__init__()
        self.exc = exc
        self.closes = 0

    def get_run(self, run_id):
        if run_id == worker.PING_RUN_ID:
            raise self.exc("private text of the store failure")
        return super().get_run(run_id)

    def close(self):
        self.closes += 1


def _degraded_main(monkeypatch, tmp_path, exc):
    """main() with the store down at start; every re-check builds a real Runner whose ping raises `exc`."""
    app, _old = _switch_app(tmp_path)
    store = Failing(exc)
    app.store = store
    app.runtime.store = store
    builds: list[int] = []

    def build(args):
        builds.append(1)
        wsgi, runner = worker.make_app(app, clock=lambda: NOW)
        return wsgi, runner, app

    def fails(args):
        raise StoreUnavailable("down")

    made: list = []
    real = worker.make_server
    monkeypatch.setattr(
        worker, "make_server", lambda *a, **kw: made.append(real(*a, **kw)) or made[-1]
    )
    monkeypatch.setattr(worker, "_prepare", fails)
    monkeypatch.setattr(worker, "_build_app", build)
    monkeypatch.setattr(worker, "HEALTH_RECHECK_S", 0.01)
    codes: list = []
    thread = threading.Thread(target=lambda: codes.append(worker.main(["--port", "0"])))
    thread.start()
    return codes, builds, made, thread, store


def test_fix3_a_refusing_store_at_every_ping_stops_the_worker_with_exit_3(
    monkeypatch, tmp_path, caplog
):
    with caplog.at_level("INFO", logger="hadavin_sdk.triggers"):
        codes, builds, made, thread, store = _degraded_main(monkeypatch, tmp_path, Refused)
        thread.join(20)
        if thread.is_alive():
            made[0].shutdown()
            thread.join(20)
            pytest.fail("the worker did not stop on its own")
    assert codes == [worker.EXIT_FAILED] and len(builds) == worker.DEGRADED_FATAL_AFTER == 5
    assert store.closes == 5  # every failed try closed the connection it opened
    assert "private text" not in caplog.text
    once = [r.getMessage() for r in caplog.records if "re-check failed (Refused)" in r.getMessage()]
    assert len(once) == 1  # the class is named once per class, at WARNING
    assert [r for r in caplog.records if "re-check failed (Refused)" in r.getMessage()][0].levelno == (
        logging.WARNING
    )
    assert len([r for r in caplog.records if "not a store outage" in r.getMessage()]) == 1


def test_fix3_a_store_refusing_the_connection_never_stops_the_worker_and_health_stays_503(
    monkeypatch, tmp_path
):
    codes, builds, made, thread, _store = _degraded_main(monkeypatch, tmp_path, ConnectionRefusedError)
    try:
        deadline = time.monotonic() + 15
        while len(builds) < 20 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(builds) >= 20 > worker.DEGRADED_FATAL_AFTER and thread.is_alive() and codes == []
        status, body = _http(made[0].server_port, "GET", "/health")
        assert status == 503 and b"store_down" in body
    finally:
        made[0].shutdown()
        thread.join(30)
    assert codes == [0]


def test_fix3_health_keeps_its_shape_for_a_refusal_and_keeps_the_error_class(tmp_path):
    app, _old = _switch_app(tmp_path)
    store = Failing(Refused)
    app.store = store
    app.runtime.store = store
    wsgi, runner = worker.make_app(app, clock=lambda: NOW)
    with runner:
        status, body, _headers = _get(wsgi)
        assert status == 503 and body == b'{"status": "store_down", "store_failures": 1}'
        assert type(runner.ping_error) is Refused
        store.exc = ConnectionRefusedError
        assert runner.health() == (False, 2) and type(runner.ping_error) is ConnectionRefusedError


# --- E1b-2: an event that cannot be built leaves no stuck flag ----------------------------------------


def test_fix3_a_conflict_event_that_cannot_be_built_does_not_stick_the_flag(rt, monkeypatch, caplog):  # noqa: F811
    first, other = _req(DOCUMENT), _req(OTHER_DOCUMENT)
    real = worker._conflict_event
    calls: list[int] = []

    def flaky(found, req):
        calls.append(1)
        if len(calls) == 1:
            raise ValueError("private text of the builder")
        return real(found, req)

    monkeypatch.setattr(worker, "_conflict_event", flaky)
    with Runner(rt, rt.store, audit=rt.audit) as runner, caplog.at_level(
        "WARNING", logger="hadavin_sdk.triggers"
    ):
        assert runner.start(first)[0] in (200, 202)
        _settle(rt.store, first.run_id)
        _free(runner)
        assert runner.start(other) == (409, {})  # the 409 still goes out
        assert not runner.audit_pending
        assert "ValueError" in caplog.text and "private text" not in caplog.text
        assert [e for e in rt.audit.events() if e.domain == "trigger"] == []
        assert runner.start(other) == (409, {})  # the next conflict still writes
        assert len([e for e in rt.audit.events() if e.domain == "trigger"]) == 1
        assert not runner.audit_pending


# --- E1b-3: a late close also closes the App's store --------------------------------------------------


def test_fix3_a_recheck_that_ends_after_a_stop_closes_its_runner_and_the_apps_store(
    monkeypatch, tmp_path
):
    app, _old = _switch_app(tmp_path)
    store = Closing()
    app.store = store
    app.runtime.store = store
    entered, gate = threading.Event(), threading.Event()
    runners: list[Runner] = []

    def build(args):
        entered.set()
        gate.wait(10)
        wsgi, runner = worker.make_app(app, clock=lambda: NOW)
        runners.append(runner)
        return wsgi, runner, app

    monkeypatch.setattr(worker, "_build_app", build)
    monkeypatch.setattr(worker, "HEALTH_RECHECK_S", 0.01)
    degraded = worker._Degraded(argparse.Namespace())
    degraded.start()
    assert entered.wait(10)
    degraded._stopped.set()  # stopped while the re-check is building
    gate.set()
    degraded._thread.join(10)
    assert not degraded._thread.is_alive()
    assert len(runners) == 1 and runners[0]._closed
    assert store.closes == 1  # `_close_app` ran in the same branch
    assert degraded._runner is None
