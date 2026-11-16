"""Round 7: one test per exit site of scripts/n8n_api.py, each with the EXACT exit code, the one fixed line, and no
traceback. The script runs as a real process against a scripted loopback n8n. Codes: 1 a check failed (n8n said
no), 2 bad usage or a name that is not exactly one workflow, 3 n8n unreachable or answered something unusable,
4 a setting or path that cannot be used."""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from support import run_python, text_file

from lead_desk import constants
from lead_desk.constants import SCRIPT_REPLY_MAX_BYTES

REPO = Path(__file__).resolve().parents[1]
CANARY = "CANARY-" + "n8n-key-7f3a"
SCRIPT = str(REPO / "scripts" / "n8n_api.py")


class Scripted(ThreadingHTTPServer):
    daemon_threads = True
    status = 200
    body = b"{}"


class H(BaseHTTPRequestHandler):
    def _go(self) -> None:
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        self.send_response(self.server.status)
        body: bytes = self.server.body
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = _go

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def n8n() -> Iterator[Scripted]:
    srv = Scripted(("127.0.0.1", 0), H)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield srv
    srv.shutdown()
    srv.server_close()
    th.join(5)


def run(
    tmp_path: Path, *args: str, url: str | None = None, key: str | None = "k-" + CANARY, **env: str
) -> tuple[int, str, str]:
    keyfile = tmp_path / "key.txt"
    environ = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(REPO / "src"),
        "LEAD_DESK_PATH_ROOTS": str(tmp_path),
    }
    if key is not None:
        keyfile.write_text(key + "\n", encoding="utf-8")
        environ["N8N_API_KEY_FILE"] = str(keyfile)
    if url is not None:
        environ["N8N_URL"] = url
    environ.update(env)
    done = run_python([SCRIPT, *args], environ, tmp_path)
    return done.returncode, done.stdout, done.stderr


def clean(rc_out_err: tuple[int, str, str]) -> None:
    _, out, err = rc_out_err
    assert "Traceback" not in out + err and CANARY not in out + err
    assert "Error" not in (out + err).replace("MaxRetryError", "")  # no Python class name reaches a person
    assert len((out + err).strip().splitlines()) <= 1


def scripted(srv: Scripted, status: int, body: bytes) -> str:
    srv.status, srv.body = status, body
    return f"http://127.0.0.1:{srv.server_address[1]}"


# -- 2: bad usage, a name that is not exactly one workflow ----------


@pytest.mark.parametrize("args", [(), ("frob",), ("import",), ("activate",), ("deactivate",)])
def test_bad_usage_is_exit_2_before_the_key_or_the_address_is_looked_at(tmp_path: Path, args: tuple[str, ...]) -> None:
    got = run(tmp_path, *args, url="http://example.test:1", key=None)  # a bad address and no key: usage still wins
    assert got[0] == constants.EXIT_REFUSED == 2 and got[2].startswith("usage:")
    clean(got)


@pytest.mark.parametrize("data", [[], [{"name": "a", "id": 1, "active": False}] * 2])
def test_a_name_that_matches_none_or_two_workflows_is_exit_2(tmp_path: Path, n8n: Scripted, data: list[object]) -> None:
    url = scripted(n8n, 200, json.dumps({"data": data}).encode())
    got = run(tmp_path, "activate", "wanted", url=url)
    assert got[0] == 2 and "exactly one is needed" in got[2]
    clean(got)


# -- 4: a setting or path that cannot be used ----------


@pytest.mark.parametrize(
    "url", ["http://example.test:9", "ftp://127.0.0.1", "http://" + "user@127.0.0.1:1", "http://127.0.0.1:99999"]
)
def test_a_bad_n8n_address_is_exit_4(tmp_path: Path, url: str) -> None:
    got = run(tmp_path, "list", url=url)
    assert got[0] == constants.EXIT_BAD_SETTING_OR_PATH == 4
    clean(got)


def test_a_missing_key_setting_is_exit_4(tmp_path: Path) -> None:
    got = run(tmp_path, "list", url="http://127.0.0.1:1", key=None)
    assert got[0] == 4 and "N8N_API_KEY_FILE" in got[2]
    clean(got)


@pytest.mark.parametrize("key", ["short", "has space in it", "kéy-with-non-ascii-1234"])
def test_a_key_file_that_is_not_one_plain_word_is_exit_4(tmp_path: Path, key: str) -> None:
    got = run(tmp_path, "list", url="http://127.0.0.1:1", key=key)
    assert got[0] == 4
    clean(got)


def test_a_workflow_file_that_is_missing_or_not_json_is_exit_4(tmp_path: Path, n8n: Scripted) -> None:
    url = scripted(n8n, 200, b"{}")
    assert run(tmp_path, "import", str(tmp_path / "nope.json"), url=url)[0] == 4
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    got = run(tmp_path, "import", str(bad), url=url)
    assert got[0] == 4 and "cannot read a workflow" in got[2]


def test_a_body_that_cannot_be_encoded_is_exit_4(tmp_path: Path) -> None:
    """A file cannot reach this refusal (json.dumps escapes a lone surrogate), so call() is driven directly with a
    body that json.dumps cannot encode (a list that contains itself)."""
    keyfile = tmp_path / "key.txt"
    keyfile.write_text("k-" + CANARY + "\n", encoding="utf-8")
    code = (
        "import sys; sys.path.insert(0, %r); import n8n_api; b = []; b.append(b); n8n_api.call('POST', '/workflows', b)"
        % str(REPO / "scripts")
    )
    environ = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(REPO / "src") + os.pathsep + str(REPO),
        "N8N_API_KEY_FILE": str(keyfile),
        "LEAD_DESK_PATH_ROOTS": str(tmp_path),
        "N8N_URL": "http://127.0.0.1:1",
    }
    done = run_python([text_file(code)], environ, tmp_path)
    assert done.returncode == 4 and "cannot encode the workflow as JSON" in done.stderr
    assert "Traceback" not in done.stderr and CANARY not in done.stderr


# -- 3: n8n cannot be reached, or answered something unusable ----------


def test_nothing_listening_is_exit_3(tmp_path: Path) -> None:
    got = run(tmp_path, "list", url="http://127.0.0.1:1")
    assert got[0] == constants.EXIT_UNREACHABLE == 3
    clean(got)


@pytest.mark.parametrize(
    ("status", "body", "words"),
    [
        (200, b"<html>not json</html>", "not JSON"),
        (200, b"[" * 100_000, "nested too deeply"),
        (200, b" " * (SCRIPT_REPLY_MAX_BYTES + 2), "too big"),
        (500, b"{}", "answered 500 to the workflow list"),
        (401, b'{"message":"x"}', "answered 401 to the workflow list"),
        (200, b'{"nodata": []}', "unexpected body"),
        (200, b'{"data": [3]}', "an entry without name"),
        (200, b'{"data": [{"name": 5, "id": 1, "active": true}]}', "an entry without name"),
    ],
    ids=["not-json", "too-deep", "too-big", "http-500", "http-401", "no-data", "odd-entry", "name-not-text"],
)
def test_an_unusable_answer_from_n8n_is_exit_3(
    tmp_path: Path, n8n: Scripted, status: int, body: bytes, words: str
) -> None:
    got = run(tmp_path, "list", url=scripted(n8n, status, body))
    assert got[0] == 3 and words in got[2]
    clean(got)


# -- 1: n8n answered, and said no ----------


def test_n8n_refusing_an_import_is_exit_1(tmp_path: Path, n8n: Scripted) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text(json.dumps({"name": "made-up", "nodes": [], "connections": {}}), encoding="utf-8")
    got = run(tmp_path, "import", str(wf), url=scripted(n8n, 400, b"{}"))
    assert got[0] == constants.EXIT_CHECK_FAILED == 1 and "import: n8n answered 400" in got[1]


def test_n8n_refusing_an_activation_is_exit_1(tmp_path: Path, n8n: Scripted) -> None:
    n8n.status, n8n.body = 200, json.dumps({"data": [{"name": "wanted", "id": 7, "active": False}]}).encode()
    url = f"http://127.0.0.1:{n8n.server_address[1]}"

    class Flip(BaseHTTPRequestHandler):
        pass

    # the list answers 200; the POST that follows is answered with the same scripted 200 by H, so script a switch:
    orig = H._go

    def go(self: H) -> None:
        if self.command == "POST":
            self.server.status, self.server.body = 409, b"{}"
        orig(self)

    H.do_GET = H.do_POST = go
    try:
        got = run(tmp_path, "activate", "wanted", url=url)
    finally:
        H.do_GET = H.do_POST = orig
    assert got[0] == 1 and "activate: n8n answered 409" in got[1]


# -- burst --url: a far address is refused before ANY name lookup or connect (EV6) ----------


@pytest.mark.parametrize(
    "far",
    [
        "http://" + "evil.example:9/leads",
        "http://" + "192.0.2.1:9/leads",
        "https://127.0.0.1:9/x",
        "http://[2001:db8::1]:9/x",
    ],
)
def test_burst_refuses_a_far_address_before_any_lookup_or_connect(
    far: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import socket

    from demo_only import burst

    calls: list[str] = []
    for name in ("connect", "connect_ex"):
        monkeypatch.setattr(socket.socket, name, lambda *a, _n=name, **k: calls.append(_n) or 1)
    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "create_connection"):
        monkeypatch.setattr(socket, name, lambda *a, _n=name, **k: calls.append(_n) or 1)
    args = ["--url", far, "--n", "3", "--email", "a@example.test", "--ref-prefix", "r", "--source", "form"]
    with pytest.raises(SystemExit) as stop:
        burst.main(args)
    assert stop.value.code == 2 and calls == []
    assert len(capsys.readouterr().err.strip().splitlines()) <= 1
