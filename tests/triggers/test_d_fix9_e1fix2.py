"""d-fix9 e1-fix2: no leak per failed re-check try, a ping thread that fails to start, a bounded conflict audit
write, a degraded worker that retries every error forever, and the per-sender cap. Memory store."""

from __future__ import annotations

import argparse
import io
import json
import logging
import threading
import time
from types import SimpleNamespace

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.store.protocol import StoreUnavailable
from hadavin_sdk.triggers import endpoint, worker
from hadavin_sdk.triggers.endpoint import Accepted
from hadavin_sdk.triggers.worker import Runner
from tests.triggers.test_d_fix6_e1 import (  # noqa: F401 - the autouse fixture is needed here too
    AGENT,
    DOCUMENT,
    KEY,
    NOW,
    OTHER_DOCUMENT,
    PRINCIPAL,
    SECRET,
    SENDER,
    TENANT,
    Switch,
    _conflicts,
    _free,
    _no_worker_log_handler,
    _post,
    _req,
    _settle,
    _switch_app,
    rt,
)

ARGS = argparse.Namespace(config_dir=None, host=worker.LOOPBACK, port=0, allow_non_loopback=False)


class Closing(Switch):
    """A Switch store that counts `close` calls."""

    closes = 0

    def close(self):
        self.closes += 1


# --- major 1: every failed try closes the App's store ------------------------------------------------


def test_fix2_recover_closes_the_store_on_every_failed_try(tmp_path, monkeypatch):
    app, _old = _switch_app(tmp_path)
    store = Closing()
    app.store = store
    app.runtime.store = store
    store.down = True  # the ping fails on every try
    runners: list[Runner] = []

    def build(args):
        wsgi, runner = worker.make_app(app, clock=lambda: NOW)
        runners.append(runner)
        return wsgi, runner, app

    monkeypatch.setattr(worker, "_build_app", build)
    for n in range(1, 4):
        with pytest.raises(StoreUnavailable):
            worker._recover(ARGS)
        assert store.closes == n  # one close per failed try, not a connection kept open
        assert runners[-1]._closed
    store.down = False
    _wsgi, runner = worker._recover(ARGS)  # success: the store stays open for serving
    try:
        assert store.closes == 3
    finally:
        runner.close(0)


def _patch_build(monkeypatch, app):
    import hadavin_sdk.app as app_module
    import hadavin_sdk.config as config_module
    import hadavin_sdk.registry as registry_module

    monkeypatch.setattr(app_module, "build", lambda *a, **kw: app)
    monkeypatch.setattr(config_module, "load_config", lambda d: SimpleNamespace())
    monkeypatch.setattr(
        registry_module, "load_registry", lambda c: app.registry
    )  # d-fix26: senders are checked before build
    monkeypatch.setattr(worker, "trigger_settings", lambda c: app.config.triggers)
    monkeypatch.setattr(worker, "qualified_agents", lambda r: list(app.runtime.agents))


@pytest.mark.parametrize("where", ["make_app", "check_tick"])
def test_fix2_build_app_closes_the_store_when_it_fails_after_build(tmp_path, monkeypatch, where):
    app, _old = _switch_app(tmp_path)
    store = Closing()
    app.store = store
    _patch_build(monkeypatch, app)
    real = worker.make_app

    def boom(*a, **kw):
        raise RuntimeError("bug")

    if where == "make_app":
        monkeypatch.setattr(worker, "make_app", boom)
    else:
        monkeypatch.setattr(worker, "make_app", lambda a: real(a, clock=lambda: NOW))
        monkeypatch.setattr(worker, "check_tick", boom)
    for n in (1, 2, 3):
        with pytest.raises(RuntimeError):
            worker._build_app(ARGS)
        assert store.closes == n


def test_fix2_prepare_closes_the_store_when_the_server_cannot_be_made(tmp_path, monkeypatch):
    app, _old = _switch_app(tmp_path)
    store = Closing()
    app.store = store
    wsgi, runner = worker.make_app(app)
    monkeypatch.setattr(worker, "_build_app", lambda args: (wsgi, runner, app))

    def boom(*a, **kw):
        raise OSError("bind")

    monkeypatch.setattr(worker, "make_server", boom)
    with pytest.raises(OSError):
        worker._prepare(ARGS)
    assert store.closes == 1 and runner._closed


# --- major 2: a ping thread that does not start ------------------------------------------------------


def test_fix2_a_ping_thread_that_does_not_start_is_a_counted_503_and_the_next_call_works(
    tmp_path, monkeypatch
):
    app, _store = _switch_app(tmp_path)
    real = threading.Thread.start
    raised: list[int] = []

    def start(self):
        if self.name == "trigger-ping" and not raised:
            raised.append(1)
            raise RuntimeError("can't start new thread")
        return real(self)

    monkeypatch.setattr(threading.Thread, "start", start)
    _wsgi, runner = worker.make_app(app, clock=lambda: NOW)
    with runner:
        began = time.monotonic()
        assert runner.health() == (False, 1)
        assert time.monotonic() - began < 1.0  # no 2 s wait on a ping that never ran
        began = time.monotonic()
        assert runner.health() == (True, 1)  # a fresh ping, not the dead one
        assert time.monotonic() - began < 1.0
    assert raised == [1]


# --- major 3: the conflict audit write is bounded ----------------------------------------------------


class BlockingAudit:
    def __init__(self):
        self.release = threading.Event()
        self.calls = 0
        self.active = 0
        self.peak = 0
        self._lock = threading.Lock()

    def write_outcome(self, event):
        with self._lock:
            self.calls += 1
            self.active += 1
            self.peak = max(self.peak, self.active)
        try:
            self.release.wait(30)
        finally:
            with self._lock:
                self.active -= 1


def test_fix2_a_blocked_audit_write_costs_the_409_at_most_2_s_and_one_write_is_pending(rt, caplog):  # noqa: F811
    audit = BlockingAudit()
    first, other = _req(DOCUMENT), _req(OTHER_DOCUMENT)
    assert worker.AUDIT_WRITE_TIMEOUT_S == 2.0
    with Runner(rt, rt.store, max_running=1, audit=audit) as runner:
        assert runner.start(first)[0] in (200, 202)
        _settle(rt.store, first.run_id)
        _free(runner)
        with caplog.at_level("WARNING", logger="hadavin_sdk.triggers"):
            began = time.monotonic()
            assert runner.start(other) == (409, {})
            took = time.monotonic() - began
            assert 1.5 < took < 4.0, took  # waited for the write, but only 2 s
            assert runner.audit_pending and audit.calls == 1
            began = time.monotonic()
            for _ in range(3):  # a conflict while one write is pending: counted, no second write
                assert runner.start(other) == (409, {})
            assert time.monotonic() - began < 1.0
            assert audit.calls == 1 and audit.peak == 1 and runner.audit_pending
            assert runner.conflict_events_dropped == 3
            assert [r for r in caplog.records if "still pending" in r.getMessage()]  # one WARNING
        audit.release.set()
        deadline = time.monotonic() + 10
        while runner.audit_pending and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not runner.audit_pending
        assert runner.start(other) == (409, {})  # the next write goes through
        assert audit.calls == 2 and audit.peak == 1


# --- major 4: every error of the re-check is retried forever; a degraded worker never exits by itself -----------------------------------


def _run_degraded(monkeypatch, outcomes):
    """main() with the store down at start; `outcomes` are the errors of the re-checks (the last is repeated)."""
    builds: list[int] = []

    def fails(args):
        raise StoreUnavailable("down")

    def build(args):
        builds.append(1)
        raise outcomes[min(len(builds), len(outcomes)) - 1]

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
    return codes, builds, made, thread


def test_fix2_every_error_is_retried_forever_and_the_worker_never_exits_by_itself(monkeypatch):
    down, bug = StoreUnavailable("down"), RuntimeError("bug")
    outcomes = (
        [bug] * 8 + [down] + [bug] * 8 + [KeyError("k")]
    )  # none of them ever stops the worker
    codes, builds, made, thread = _run_degraded(monkeypatch, outcomes)
    try:
        deadline = time.monotonic() + 15
        while len(builds) < 30 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(builds) >= 30 and thread.is_alive() and codes == []
    finally:
        made[0].shutdown()
        thread.join(30)
    assert codes == [0]


def test_fix2_the_recheck_warning_is_once_per_5_minutes_and_again_when_the_class_changes(
    monkeypatch, caplog
):
    assert worker.DEGRADED_WARN_EVERY_S == 300
    clock = [1000.0]
    monkeypatch.setattr(worker, "_monotonic", lambda: clock[0])
    outcomes: list = [RuntimeError("secret-a")] * 5
    calls: list = []

    def build(args):
        calls.append(1)
        if len(calls) > len(outcomes):
            raise outcomes[-1]
        raise outcomes[len(calls) - 1]

    monkeypatch.setattr(worker, "_build_app", build)
    monkeypatch.setattr(worker, "HEALTH_RECHECK_S", 0.01)

    def wait_calls(n):
        deadline = time.monotonic() + 15
        while len(calls) < n and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(calls) >= n

    def warns():
        return [
            r
            for r in caplog.records
            if "re-check failed" in r.getMessage() and r.levelno == logging.WARNING
        ]

    degraded = worker._Degraded(argparse.Namespace())
    with caplog.at_level("INFO", logger="hadavin_sdk.triggers"):
        degraded.start()
        try:
            wait_calls(20)
            assert [r.getMessage().count("RuntimeError") for r in warns()] == [
                1
            ]  # 20 failures, 1 line
            clock[0] += 299
            n = len(calls)
            wait_calls(n + 10)
            assert len(warns()) == 1
            clock[0] += 2  # 301 s after the first line
            n = len(calls)
            wait_calls(n + 10)
            assert len(warns()) == 2
            outcomes[:] = [
                KeyError("secret-b")
            ]  # the class changes: logged at once, inside the window
            calls.clear()
            wait_calls(10)
            assert len(warns()) == 3 and "KeyError" in warns()[-1].getMessage()
        finally:
            degraded._stopped.set()
            degraded._thread.join(10)
    assert "secret-a" not in caplog.text and "secret-b" not in caplog.text
    assert degraded.failures > 40 and degraded.health() == (False, degraded.failures)


# --- nit: the degraded socket timeout ----------------------------------------------------------------


@pytest.mark.parametrize(("configured", "wanted"), [(7, 17.0), (None, worker.ACK_WAIT_S + 10.0)])
def test_fix2_the_degraded_socket_timeout_is_the_configured_ack_wait_plus_slack(
    monkeypatch, configured, wanted
):
    import hadavin_sdk.config as config_module

    seen: list = []

    def fails(args):
        raise StoreUnavailable("down")

    def spy(host, port, app, timeout):
        seen.append(timeout)
        raise worker.ConfigError(
            "stop here"
        )  # ends `_serve_degraded` right after the timeout is chosen

    monkeypatch.setattr(worker, "_prepare", fails)
    monkeypatch.setattr(worker, "make_server", spy)
    if configured is None:
        monkeypatch.setattr(config_module, "load_config", lambda d: 1 / 0)
    else:
        monkeypatch.setattr(config_module, "load_config", lambda d: SimpleNamespace())
        monkeypatch.setattr(
            worker, "trigger_settings", lambda c: SimpleNamespace(ack_wait_s=configured)
        )
    assert worker.main(["--port", "0"]) == worker.EXIT_CONFIG
    assert seen == [wanted]


# --- test gaps: no conflict event for an unauthenticated request; the cap is per sender --------------


def _post_signed_with(wsgi, document: bytes, secret: str):
    body = json.dumps({"key": KEY, "document": document.decode()}).encode()
    headers = {k.lower(): v for k, v in hmac_v0.sign(body, NOW, secret, endpoint.PREFIX).items()}
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": endpoint.PATH,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "HTTP_" + endpoint.TIMESTAMP_HEADER.upper().replace("-", "_"): headers[
            endpoint.TIMESTAMP_HEADER.lower()
        ],
        "HTTP_" + endpoint.SIGNATURE_HEADER.upper().replace("-", "_"): headers[
            endpoint.SIGNATURE_HEADER.lower()
        ],
    }
    seen: list = []
    out = wsgi(environ, lambda status, hdrs: seen.append(status))
    return int(seen[0][:3]), b"".join(out)


def test_fix2_an_unsigned_or_wrongly_signed_conflicting_document_writes_no_event(tmp_path):
    app, _store = _switch_app(tmp_path)
    wsgi, runner = worker.make_app(app, clock=lambda: NOW)
    audit = app.audit
    with runner:
        assert _post(wsgi, DOCUMENT)[0] in (200, 202)
        _settle(app.store, endpoint.derive_run_id(TENANT, SENDER, KEY))
        _free(runner)

        def trigger_events():
            return [e for e in audit.events() if e.domain == "trigger"]

        assert trigger_events() == []
        for _ in range(3):
            assert _post(wsgi, OTHER_DOCUMENT, sign=False)[0] == 401
            assert _post_signed_with(wsgi, OTHER_DOCUMENT, "not" + SECRET)[0] == 401
        assert trigger_events() == [] and runner.conflict_events_dropped == 0
        assert not runner.audit_pending and runner._conflict_windows == {}
        assert _post(wsgi, OTHER_DOCUMENT)[0] == 409  # the control: a signed one is written
        assert len(trigger_events()) == 1


def _req_of(sender: str, document: bytes) -> Accepted:
    return Accepted(
        sender=sender,
        agent_id=AGENT,
        principal_id=PRINCIPAL,
        run_id=endpoint.derive_run_id(TENANT, sender, KEY),
        trigger_ref=endpoint.trigger_ref(sender, KEY, document),
        document=document,
    )


def test_fix2_the_cap_is_per_sender_and_the_window_dict_is_bounded_by_the_senders(rt):  # noqa: F811
    with Runner(
        rt, rt.store, max_running=1, audit=rt.audit, conflict_events_per_minute=2
    ) as runner:
        for sender in ("door-a", "door-b"):
            first = _req_of(sender, DOCUMENT)
            assert runner.start(first)[0] in (200, 202)
            _settle(rt.store, first.run_id)
            _free(runner)

        def by_source():
            return [e.source for e in _conflicts(rt)]

        for _ in range(6):  # sender A is far over its cap
            assert runner.start(_req_of("door-a", OTHER_DOCUMENT)) == (409, {})
        assert by_source() == ["trigger:door-a"] * 2 and runner.conflict_events_dropped == 4
        assert runner.start(_req_of("door-b", OTHER_DOCUMENT)) == (409, {})  # B is not stopped by A
        assert by_source().count("trigger:door-b") == 1 and runner.conflict_events_dropped == 4
        for _ in range(50):
            runner.start(_req_of("door-a", OTHER_DOCUMENT))
            runner.start(_req_of("door-b", OTHER_DOCUMENT))
        assert set(runner._conflict_windows) == {"door-a", "door-b"}
        assert by_source().count("trigger:door-b") == 2
