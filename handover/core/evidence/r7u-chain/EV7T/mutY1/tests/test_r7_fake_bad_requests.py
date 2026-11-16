"""Round 7 (F2): a request with a bad body or query shape gets ONE fixed 400 answer from every fake server, never a
traceback and never silence. Fixed at the one place all handler methods pass through (demo_only/bad_request.py).
Every case here is a real request over a loopback socket to the real handler class; nothing is faked in between."""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator
from http.server import HTTPServer
from typing import Any

import pytest

from demo_only import fake_hubspot as fh
from demo_only.bad_request import BAD_REQUEST_ERRORS, BAD_REQUEST_TEXT, AnswersBadRequests
from demo_only.fake_model_server import make_model_server
from demo_only.fakes_server import make_fakes_server

KEY = "made-up-" + "hubspot-key"
TIMEOUT = 5.0


def ask(port: int, method: str, path: str, body: bytes | None = None, headers: dict[str, str] | None = None) -> Any:
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=TIMEOUT)
    try:
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        return r.status, r.read()
    finally:
        c.close()


def serve(srv: Any) -> Iterator[int]:
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield int(srv.server_address[1])
    srv.shutdown()
    srv.server_close()
    th.join(5)


@pytest.fixture
def hubspot() -> Iterator[int]:
    state = fh.HubspotState(KEY, "ok")
    handler = type("H", (fh._Handler,), {"state": state})
    yield from serve(fh.FakeHubspot(("127.0.0.1", 0), handler))


@pytest.fixture
def fakes() -> Iterator[int]:
    yield from serve(make_fakes_server("keyed", 0, "keyed", "127.0.0.1"))


@pytest.fixture
def model() -> Iterator[int]:
    srv, _state = make_model_server("127.0.0.1", 0, "ok")
    yield from serve(srv)


AUTH = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
HUBSPOT_BAD = [
    ("POST", "/crm/v3/objects/contacts", b"{}"),
    ("POST", "/crm/v3/objects/contacts", b"[]"),
    ("POST", "/crm/v3/objects/contacts", b"zzz"),
    ("POST", "/crm/v3/objects/contacts", b'{"properties":[]}'),
    ("POST", "/crm/v3/objects/contacts", None),
    ("POST", "/crm/v3/objects/contacts/search", b"[]"),
    ("POST", "/crm/v3/objects/contacts/search", b"{}"),
    ("GET", "/crm/v3/objects/contacts?limit=abc", None),
    ("GET", "/crm/v3/objects/contacts?after=abc", None),
]


@pytest.mark.parametrize(("method", "path", "body"), HUBSPOT_BAD)
def test_hubspot_fake_answers_a_bad_shape_with_one_fixed_400(
    hubspot: int, capfd: pytest.CaptureFixture[str], method: str, path: str, body: bytes | None
) -> None:
    status, text = ask(hubspot, method, path, body, AUTH)
    assert status == 400 and json.loads(text)["message"] == BAD_REQUEST_TEXT
    assert "Traceback" not in capfd.readouterr().err


FAKES_BAD = [
    ("POST", "/fake/outbox", b"[]"),
    ("POST", "/fake/outbox", b'"x"'),
    ("POST", "/fake/outbox", b'{"key":1,"to":[],"subject":{}}'),
    ("POST", "/fake/crm", b"[]"),
    ("POST", "/fake/crm", b'{"lead_id":[],"record":3}'),
    ("POST", "/fake/crm/fields", b"[]"),
    ("POST", "/fake/control", b"[]"),
    ("POST", "/fake/control", b'{"delay_ms":"x","target":[]}'),
    ("POST", "/fake/outbox", b"\xff\xfe"),
]


@pytest.mark.parametrize(("method", "path", "body"), FAKES_BAD)
def test_fakes_server_answers_a_bad_shape_at_once_without_a_traceback(
    fakes: int, capfd: pytest.CaptureFixture[str], method: str, path: str, body: bytes
) -> None:
    status, _text = ask(fakes, method, path, body, {"Content-Type": "application/json"})
    assert 400 <= status < 500  # an answer came inside the time limit, and it is a client-error answer
    assert "Traceback" not in capfd.readouterr().err


MODEL_BAD = [
    ("POST", "/control", b"[]"),
    ("POST", "/control", b'{"mode":[]}'),
    ("POST", "/control", b'{"slow_seconds":"x"}'),
    ("POST", "/v1/messages", b"[]"),
    ("POST", "/v1/messages", b'{"messages":"x"}'),
    ("POST", "/v1/messages", b'{"messages":[1]}'),
    ("POST", "/v1/messages", b'{"messages":[{"content":[1]}]}'),
    ("POST", "/v1/messages", b"\xff\xfe"),
]


@pytest.mark.parametrize(("method", "path", "body"), MODEL_BAD)
def test_model_fake_answers_a_bad_shape_at_once_without_a_traceback(
    model: int, capfd: pytest.CaptureFixture[str], method: str, path: str, body: bytes
) -> None:
    status, _text = ask(
        model, method, path, body, {"x-api-key": "made-up-key-for-test", "Content-Type": "application/json"}
    )
    assert status < 500  # an answer came inside the time limit (a handled bad shape is a 4xx, a tolerated one a 200)
    assert "Traceback" not in capfd.readouterr().err


# -- the one choke point itself: each of the five error classes, from each method -----------------------------------


@pytest.mark.parametrize("error", BAD_REQUEST_ERRORS)
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_the_mix_in_turns_each_error_class_from_each_method_into_one_400(
    error: type[Exception], method: str, capfd: pytest.CaptureFixture[str]
) -> None:
    def boom(self: Any) -> None:
        raise error("secret-looking text that must never be echoed")

    class H(AnswersBadRequests):
        def _send_bad_request(self) -> None:
            body = BAD_REQUEST_TEXT.encode()
            self.send_response(400)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: Any) -> None:
            pass

    setattr(H, f"do_{method}", boom)
    # the wrapping happens when a method is defined in the class body: build the class the same way
    H = type("H2", (H,), {f"do_{method}": boom})
    srv = HTTPServer(("127.0.0.1", 0), H)
    port = int(srv.server_address[1])
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        status, text = ask(port, method, "/x", b"{}" if method != "GET" else None)
    finally:
        srv.shutdown()
        srv.server_close()
        th.join(5)
    assert status == 400 and text == BAD_REQUEST_TEXT.encode()
    assert "secret-looking" not in text.decode() and "Traceback" not in capfd.readouterr().err


def test_a_handler_error_after_the_answer_started_does_not_send_a_second_answer() -> None:
    class H(AnswersBadRequests):
        def _send_bad_request(self) -> None:  # pragma: no cover - must not be called
            raise AssertionError("a second answer was started")

        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")
            raise KeyError("after the answer")

        def log_message(self, *args: Any) -> None:
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        status, text = ask(int(srv.server_address[1]), "GET", "/x")
    finally:
        srv.shutdown()
        srv.server_close()
        th.join(5)
    assert (status, text) == (200, b"ok")
