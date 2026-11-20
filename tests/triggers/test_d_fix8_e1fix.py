"""d-fix8 e1-fix: a degraded worker recovers in the same process, the /health ping is bounded, and a missing
`audit` on the App is warned about once at start. Memory store and the scripted model of the worker tests."""

from __future__ import annotations

import argparse
import http.client
import json
import threading
import time

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import StoreUnavailable
from hadavin_sdk.triggers import endpoint, worker
from tests.triggers.test_d_fix6_e1 import (  # noqa: F401 - the autouse fixture is needed here too
    DOCUMENT,
    KEY,
    SECRET,
    _get,
    _no_worker_log_handler,
    _switch_app,
)


class Flaky(MemoryStore):
    """A memory store whose ping (get_run of the never-stored id) fails `fail_pings` times, then works."""

    fail_pings = 0
    pings = 0

    def get_run(self, run_id):
        if run_id == worker.PING_RUN_ID:
            self.pings += 1
            if self.pings <= self.fail_pings:
                raise OSError("private text of the store failure")
        return super().get_run(run_id)


class Hung(MemoryStore):
    """get_run of the ping id blocks until `release` is set."""

    def __init__(self):
        super().__init__()
        self.release = threading.Event()

    def get_run(self, run_id):
        if run_id == worker.PING_RUN_ID:
            self.release.wait(30)
        return super().get_run(run_id)


def _http(port: int, method: str, path: str, body: bytes | None = None, headers=None):
    conn = http.client.HTTPConnection(worker.LOOPBACK, port, timeout=15)
    try:
        conn.request(method, path, body=body, headers=headers or {})
        reply = conn.getresponse()
        return reply.status, reply.read()
    finally:
        conn.close()


def _signed_post(port: int):
    body = json.dumps({"key": KEY, "document": DOCUMENT.decode()}).encode()
    headers = hmac_v0.sign(body, int(time.time()), SECRET, endpoint.PREFIX)
    return _http(port, "POST", endpoint.PATH, body, headers)


def test_e1fix_a_worker_started_with_the_store_down_recovers_in_the_same_process(
    tmp_path, monkeypatch, caplog
):
    app, _store = _switch_app(tmp_path)
    store = Flaky()
    app.store = store
    app.runtime.store = store
    builds: list[int] = []

    def build(args):
        builds.append(1)
        if len(builds) <= 2:  # the first two re-checks cannot even build (store down)
            raise OSError("cannot connect to private-host")
        wsgi, runner = worker.make_app(app)
        return wsgi, runner, app

    def fails(args):
        raise StoreUnavailable("cannot connect to private-host")

    store.fail_pings = 2  # then two builds that answer but whose ping fails, then the store is back
    made: list = []
    real = worker.make_server
    monkeypatch.setattr(
        worker, "make_server", lambda *a, **kw: made.append(real(*a, **kw)) or made[-1]
    )
    monkeypatch.setattr(worker, "_prepare", fails)
    monkeypatch.setattr(worker, "_build_app", build)
    monkeypatch.setattr(worker, "HEALTH_RECHECK_S", 0.05)
    codes: list = []
    with caplog.at_level("INFO", logger="hadavin_sdk.triggers"):
        thread = threading.Thread(target=lambda: codes.append(worker.main(["--port", "0"])))
        thread.start()
        try:
            deadline = time.monotonic() + 15
            while not made and time.monotonic() < deadline:
                time.sleep(0.01)
            assert made, "the worker did not start"
            port = made[0].server_port
            seen_503 = 0
            first_ok = None
            while time.monotonic() < deadline:
                health = _http(port, "GET", "/health")
                post = _signed_post(port)
                if health[0] == 503:
                    seen_503 += 1
                if post[0] in (200, 202):
                    first_ok = (post, store.pings, health[0])
                    break
                assert post == (503, b"")  # never a 2xx before the real Runner exists
                time.sleep(0.01)
            assert seen_503 >= 1 and first_ok, "no 503 then 202 in one process"
            assert first_ok[1] > 2  # the failing pings were all seen first
            ok = _http(port, "GET", "/health")
            assert ok[0] == 200 and json.loads(ok[1])["status"] == "ok"
        finally:
            if made:
                made[0].shutdown()
            thread.join(30)
    assert not thread.is_alive() and codes == [0]
    assert sum("store is back" in r.getMessage() for r in caplog.records) == 1
    assert "private-host" not in caplog.text and "private text" not in caplog.text


def test_e1fix_a_degraded_worker_stops_cleanly_while_still_down(monkeypatch):
    def fails(args):
        raise StoreUnavailable("down")

    made: list = []
    real = worker.make_server
    monkeypatch.setattr(
        worker, "make_server", lambda *a, **kw: made.append(real(*a, **kw)) or made[-1]
    )
    monkeypatch.setattr(worker, "_prepare", fails)
    monkeypatch.setattr(worker, "_build_app", fails)
    monkeypatch.setattr(worker, "HEALTH_RECHECK_S", 0.02)
    codes: list = []
    thread = threading.Thread(target=lambda: codes.append(worker.main(["--port", "0"])))
    thread.start()
    deadline = time.monotonic() + 15
    while not made and time.monotonic() < deadline:
        time.sleep(0.01)
    assert made
    time.sleep(0.2)  # several failed re-checks
    status, body = _http(made[0].server_port, "GET", "/health")
    assert status == 503 and json.loads(body)["store_failures"] > 1
    made[0].shutdown()
    thread.join(30)
    assert not thread.is_alive() and codes == [0]
    assert not [t for t in threading.enumerate() if t.name == "trigger-recover" and t.is_alive()]


def test_e1fix_the_health_ping_is_bounded_and_never_leaks_more_than_one_thread(
    tmp_path, monkeypatch
):
    app, _store = _switch_app(tmp_path)
    hung = Hung()
    app.store = hung
    monkeypatch.setattr(worker, "HEALTH_PING_TIMEOUT_S", 0.2)
    wsgi, runner = worker.make_app(app, clock=lambda: 1_800_000_000)

    def pings():
        return [t for t in threading.enumerate() if t.name == "trigger-ping" and t.is_alive()]

    with runner:
        for n in (1, 2, 3):
            started = time.monotonic()
            status, body, _ = _get(wsgi)
            assert time.monotonic() - started < 5
            assert status == 503 and json.loads(body) == {
                "status": "store_down",
                "store_failures": n,
            }
            assert len(pings()) == 1  # the same pending ping, never a second one
        hung.release.set()
        deadline = time.monotonic() + 10
        while pings() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not pings()
        status, body, _ = _get(wsgi)
        assert status == 200 and json.loads(body)["status"] == "ok"
        assert json.loads(body)["store_failures"] == 3


def test_e1fix_main_warns_once_when_the_app_has_no_audit_and_make_app_does_not(
    tmp_path, monkeypatch, caplog
):
    app, _store = _switch_app(tmp_path)
    del app.audit
    with caplog.at_level("WARNING", logger="hadavin_sdk.triggers"):
        wsgi, runner = worker.make_app(app)  # tests build stand-ins this way: no warning here
        assert [r for r in caplog.records if "audit" in r.getMessage()] == []
        monkeypatch.setattr(worker, "_build_app", lambda args: (wsgi, runner, app))
        args = argparse.Namespace(
            config_dir=None, host=worker.LOOPBACK, port=0, allow_non_loopback=False
        )
        server, got = worker._prepare(args)
        server.server_close()
        got.close(0)
    warns = [r.getMessage() for r in caplog.records if "audit" in r.getMessage()]
    assert len(warns) == 1 and "'audit'" in warns[0] and "SimpleNamespace" in warns[0]
    assert SECRET not in warns[0]


def test_e1fix_no_warning_when_the_app_has_an_audit(tmp_path, monkeypatch, caplog):
    app, _store = _switch_app(tmp_path)
    wsgi, runner = worker.make_app(app)
    monkeypatch.setattr(worker, "_build_app", lambda args: (wsgi, runner, app))
    args = argparse.Namespace(
        config_dir=None, host=worker.LOOPBACK, port=0, allow_non_loopback=False
    )
    with caplog.at_level("WARNING", logger="hadavin_sdk.triggers"):
        server, got = worker._prepare(args)
        server.server_close()
        got.close(0)
    assert [r for r in caplog.records if "audit" in r.getMessage()] == []


@pytest.mark.parametrize("name", ["HEALTH_RECHECK_S", "HEALTH_PING_TIMEOUT_S"])
def test_e1fix_the_constants(name):
    assert getattr(worker, name) == {"HEALTH_RECHECK_S": 5.0, "HEALTH_PING_TIMEOUT_S": 2.0}[name]
