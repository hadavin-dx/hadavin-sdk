"""d-fix6 E1: the audit event of a signed 409, its per-sender rate cap, and ``GET /health`` in place of exit 4.

Memory store and the scripted model double of the other worker tests. Fake secrets only.
"""

from __future__ import annotations

import hashlib
import http.client
import io
import json
import threading
import time
from types import SimpleNamespace

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import StoreUnavailable
from hadavin_sdk.triggers import endpoint, worker
from hadavin_sdk.triggers.endpoint import Accepted
from hadavin_sdk.triggers.worker import Runner
from tests.k5_support import build_runtime, k5_cfg
from tests.triggers.test_worker import (
    AGENT,
    DOCUMENT,
    OTHER_DOCUMENT,
    PRINCIPAL,
    SECRET,
    SENDER,
    TENANT,
    GateLLM,
    _app,
    _free,
    _no_worker_log_handler,  # noqa: F401 - autouse fixture of test_worker, needed here too
    _settings,
    _settle,
)

NOW = 1_800_000_000
KEY = "key-1"


@pytest.fixture
def rt(tmp_path):
    runtime, _cards = build_runtime(k5_cfg(tmp_path), GateLLM())
    return runtime


def _sha(document: bytes) -> str:
    return hashlib.sha256(document).hexdigest()


def _post(wsgi, document: bytes, *, key: str = KEY, sign: bool = True):
    """One signed POST straight into the WSGI callable: (status, body, the signature header that was sent)."""
    body = json.dumps({"key": key, "document": document.decode()}).encode()
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": endpoint.PATH,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    sig = ""
    if sign:
        headers = {
            k.lower(): v for k, v in hmac_v0.sign(body, NOW, SECRET, endpoint.PREFIX).items()
        }
        sig = headers[endpoint.SIGNATURE_HEADER.lower()]
        environ["HTTP_" + endpoint.TIMESTAMP_HEADER.upper().replace("-", "_")] = headers[
            endpoint.TIMESTAMP_HEADER.lower()
        ]
        environ["HTTP_" + endpoint.SIGNATURE_HEADER.upper().replace("-", "_")] = sig
    seen: list = []
    out = wsgi(environ, lambda status, headers: seen.append((status, dict(headers))))
    return int(seen[0][0][:3]), b"".join(out), sig


def _get(wsgi, path: str = "/health", method: str = "GET"):
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "wsgi.input": io.BytesIO(b"")}
    seen: list = []
    out = wsgi(environ, lambda status, headers: seen.append((status, dict(headers))))
    return int(seen[0][0][:3]), b"".join(out), seen[0][1]


def _conflicts(rt):
    return [e for e in rt.audit.events() if e.domain == "trigger"]


def _req(document: bytes) -> Accepted:
    return Accepted(
        sender=SENDER,
        agent_id=AGENT,
        principal_id=PRINCIPAL,
        run_id=endpoint.derive_run_id(TENANT, SENDER, KEY),
        trigger_ref=endpoint.trigger_ref(SENDER, KEY, document),
        document=document,
    )


# --- (a) the audit event of a 409 --------------------------------------------------------------------


def test_e1_a_409_writes_one_audit_event_with_exactly_ids_and_both_hashes(rt):
    app = _app(rt, _settings(max_running=1))
    app.audit = rt.audit
    wsgi, runner = worker.make_app(app, clock=lambda: NOW)
    with runner:
        status, _body, first_sig = _post(wsgi, DOCUMENT)
        assert status in (200, 202)
        _settle(rt.store, _req(DOCUMENT).run_id)
        _free(runner)
        assert _conflicts(rt) == []  # a repeat of the same document is no conflict
        assert _post(wsgi, DOCUMENT)[0] == 200 and _conflicts(rt) == []
        status, body, second_sig = _post(wsgi, OTHER_DOCUMENT)
        assert (status, body) == (409, b"")
    (event,) = _conflicts(rt)  # exactly one event for the one 409
    wanted = {
        "run_id": _req(DOCUMENT).run_id,
        "domain": "trigger",
        "operation": "conflict",
        "principal": PRINCIPAL,
        "source": f"trigger:{SENDER}",
        "object_ref": KEY,
        "inputs_hash": _sha(OTHER_DOCUMENT),  # the new request
        "output_hash": _sha(DOCUMENT),  # the stored one
        "result": "conflict",
    }
    dumped = event.model_dump(mode="json")
    given = {k: v for k, v in dumped.items() if v is not None}
    for volatile in ("event_id", "ts", "schema_version"):
        given.pop(volatile)
    assert given == wanted
    text = repr(event) + event.model_dump_json() + repr(dumped)
    for private in (
        DOCUMENT.decode(),
        OTHER_DOCUMENT.decode(),
        first_sig,
        second_sig,
        SECRET,
        endpoint.trigger_ref(SENDER, KEY, OTHER_DOCUMENT),
    ):
        assert private not in text, private


# --- (a) the per-sender rate cap ----------------------------------------------------------------------


def test_e1_the_11th_conflict_in_a_minute_writes_no_event_but_is_still_409_and_counted(rt, caplog):
    clock = [1000.0]
    first, other = _req(DOCUMENT), _req(OTHER_DOCUMENT)
    with Runner(rt, rt.store, audit=rt.audit, rate_clock=lambda: clock[0]) as runner:
        assert runner.start(first)[0] in (200, 202)
        _settle(rt.store, first.run_id)
        _free(runner)
        with caplog.at_level("DEBUG", logger="hadavin_sdk.triggers"):
            for n in range(10):
                clock[0] += 1.0
                assert runner.start(other) == (409, {}), n
            assert len(_conflicts(rt)) == 10 and runner.conflict_events_dropped == 0
            warnings = [r for r in caplog.records if "over the cap" in r.getMessage()]
            assert warnings == []
            clock[0] += 1.0
            assert runner.start(other) == (409, {})  # the 11th: still answered
            assert len(_conflicts(rt)) == 10 and runner.conflict_events_dropped == 1
            for _ in range(3):
                clock[0] += 1.0
                assert runner.start(other) == (409, {})
            assert len(_conflicts(rt)) == 10 and runner.conflict_events_dropped == 4
            warnings = [r for r in caplog.records if "over the cap" in r.getMessage()]
            assert len(warnings) == 1  # one WARNING per minute, not one per refused event
            assert warnings[0].levelname == "WARNING"
            for private in (_req(OTHER_DOCUMENT).trigger_ref, _sha(OTHER_DOCUMENT), _sha(DOCUMENT)):
                assert private not in caplog.text
            clock[0] += 61.0  # the window is over: events again, and the next drop warns again
            assert runner.start(other) == (409, {})
            assert len(_conflicts(rt)) == 11


def test_e1_the_cap_is_per_sender_and_a_constructor_parameter(rt):
    assert worker.CONFLICT_EVENTS_PER_MINUTE == 10
    with Runner(rt, rt.store, audit=rt.audit, conflict_events_per_minute=2) as runner:
        first, other = _req(DOCUMENT), _req(OTHER_DOCUMENT)
        assert runner.start(first)[0] in (200, 202)
        _settle(rt.store, first.run_id)
        _free(runner)
        for _ in range(5):
            assert runner.start(other) == (409, {})
        assert len(_conflicts(rt)) == 2 and runner.conflict_events_dropped == 3
    for bad in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="conflict_events_per_minute"):
            Runner(rt, rt.store, conflict_events_per_minute=bad)


def test_e1_a_failing_audit_never_changes_the_409(rt):
    class Broken:
        def write_outcome(self, event):
            raise RuntimeError("audit down")

    with Runner(rt, rt.store, audit=Broken()) as runner:
        first = _req(DOCUMENT)
        assert runner.start(first)[0] in (200, 202)
        _settle(rt.store, first.run_id)
        _free(runner)
        assert runner.start(_req(OTHER_DOCUMENT)) == (409, {})


# --- (b) /health ----------------------------------------------------------------------------------------


class Switch(MemoryStore):
    """A memory store that is down while `down` is set."""

    down = False

    def get_run(self, run_id):
        if self.down:
            raise OSError("private text of the store failure")
        return super().get_run(run_id)


def _switch_app(tmp_path):
    runtime, _cards = build_runtime(k5_cfg(tmp_path), GateLLM())
    store = Switch()
    runtime.store = store
    app = SimpleNamespace(
        config=SimpleNamespace(triggers=_settings(max_running=1), environment="demo"),
        registry=runtime.registry,
        runtime=runtime,
        store=store,
        audit=runtime.audit,
        trigger_secret={"door-a": SECRET}.__getitem__,
    )
    return app, store


def test_e1_health_is_200_when_the_store_is_up_and_503_with_a_counter_when_it_is_down(
    tmp_path, caplog
):
    app, store = _switch_app(tmp_path)
    wsgi, runner = worker.make_app(app, clock=lambda: NOW)
    with runner, caplog.at_level("DEBUG", logger="hadavin_sdk.triggers"):
        status, body, headers = _get(wsgi)
        assert status == 200 and json.loads(body) == {"status": "ok", "store_failures": 0}
        assert headers["Content-Type"] == "application/json"
        store.down = True
        status, body, headers = _get(wsgi)
        assert status == 503 and headers["Retry-After"] == "1"
        assert json.loads(body) == {"status": "store_down", "store_failures": 1}
        assert set(json.loads(body)) == {"status", "store_failures"}
        # a request path that saw the store down counts too
        assert _post(wsgi, DOCUMENT)[0] == 503
        assert json.loads(_get(wsgi)[1]) == {"status": "store_down", "store_failures": 3}
        store.down = False
        status, body, _ = _get(wsgi)
        assert status == 200 and json.loads(body) == {"status": "ok", "store_failures": 3}
        assert (
            _get(wsgi, method="POST")[0] == 405 and _get(wsgi, method="POST")[2]["Allow"] == "GET"
        )
        assert _get(wsgi, path="/health/x")[0] == 404
    assert "private text" not in caplog.text


def test_e1_health_needs_no_signature_and_leaks_nothing(tmp_path, caplog):
    app, store = _switch_app(tmp_path)
    wsgi, runner = worker.make_app(app, clock=lambda: NOW)
    with runner, caplog.at_level("DEBUG", logger="hadavin_sdk.triggers"):
        first = _post(wsgi, DOCUMENT)
        assert first[0] in (200, 202)
        _settle(app.store, endpoint.derive_run_id(TENANT, SENDER, KEY))
        _free(runner)
        assert _post(wsgi, OTHER_DOCUMENT)[0] == 409
        assert (
            _post(wsgi, DOCUMENT, sign=False)[0] == 401
        )  # the trigger path still needs the signature
        assert _post(wsgi, OTHER_DOCUMENT, sign=False)[0] == 401  # unsigned and conflicting:
        assert len([e for e in app.audit.events() if e.domain == "trigger"]) == 1  # no new event
        for down in (False, True):
            store.down = down
            status, body, headers = _get(wsgi)  # no header at all
            assert status == (503 if down else 200)
            text = body.decode() + repr(headers)
            for private in (
                SENDER,
                TENANT,
                KEY,
                SECRET,
                _sha(DOCUMENT),
                _sha(OTHER_DOCUMENT),
                DOCUMENT.decode(),
                AGENT,
                PRINCIPAL,
            ):
                assert private not in text, private
    health_lines = [r.getMessage() for r in caplog.records if "health" in r.getMessage()]
    assert health_lines and all(
        "{" not in line and "private text" not in line for line in health_lines
    )
    assert "store_failures" not in caplog.text  # the body is never logged


def test_e1_without_a_health_callable_the_path_is_an_ordinary_404(rt):
    wsgi = endpoint.make_wsgi(
        _settings(), {SENDER: (SECRET,)}, lambda req: (503, None), lambda: float(NOW)
    )
    assert _get(wsgi)[0] == 404


# --- (b) start with the store down ----------------------------------------------------------------------


@pytest.mark.parametrize("error", [StoreUnavailable, ConnectionRefusedError])
def test_e1_start_with_the_store_down_starts_and_health_is_503(monkeypatch, caplog, error):
    fake_secret = "pg" + "-pass-" + "Zq7" * 6

    def fails(args):
        raise error(f"cannot connect to postgresql://app:{fake_secret}@db-host/hadavin")

    made: list = []
    real = worker.make_server

    def spy(*a, **kw):
        made.append(real(*a, **kw))
        return made[-1]

    monkeypatch.setattr(worker, "_prepare", fails)
    monkeypatch.setattr(worker, "make_server", spy)
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
            answers = []
            for method, path in (("GET", "/health"), ("POST", endpoint.PATH)):
                conn = http.client.HTTPConnection(worker.LOOPBACK, port, timeout=15)
                try:
                    conn.request(method, path, body=b"{}" if method == "POST" else None)
                    reply = conn.getresponse()
                    answers.append((reply.status, reply.read()))
                finally:
                    conn.close()
        finally:
            if made:
                made[0].shutdown()
            thread.join(30)
    assert not thread.is_alive() and codes == [0]  # started and stopped cleanly: no exit 4
    assert answers[0][0] == 503 and json.loads(answers[0][1]) == {
        "status": "store_down",
        "store_failures": 1,
    }
    assert answers[1] == (503, b"")
    warns = [
        r.getMessage()
        for r in caplog.records
        if r.levelname == "WARNING" and "SIGTERM" not in r.getMessage()
    ]
    assert len(warns) == 1 and error.__name__ in warns[0] and "store unreachable" in warns[0]
    for private in (fake_secret, "postgresql", "db-host"):
        assert private not in caplog.text


def test_e1_there_is_no_exit_code_4_any_more():
    assert not hasattr(worker, "EXIT_STORE")
