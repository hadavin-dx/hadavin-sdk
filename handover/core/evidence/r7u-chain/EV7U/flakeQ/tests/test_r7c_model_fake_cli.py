"""Round 7C: command line of the model fake (nits and open items O-2, O-5, E).

O-2 (decided): `--port 0` stays allowed because the server prints the port it really got on its first line (and the
option help says "0 = a free port"); the test pins that line and that the port answers.
Nit: an empty `--key-file` used to start the fake with the key "" (sign-in check off): now one refusal line, exit 2/4.
O-5 (decided): a `/v1/messages` body that is not a JSON object (also one nested 100,000 deep) is read as an EMPTY
request (demo_only/fake_model_server.py: `except ValueError: request = {}`), so the fake answers by its mode: 200 in
mode ok, and counts one call. 400 is only for `/control`, whose body must be an object."""

from __future__ import annotations

import http.client
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from support import REPO, popen_program, run_program, start_serving, stop_serving

from demo_only.fake_model_server import make_model_server

KEY = "made-up-key-for-test-only"


def _run_fake(args: list[str], cwd: Path, **kw: Any) -> Any:
    env = {
        "PYTHONPATH": f"{REPO / 'src'}:{REPO}",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PATH": ":".join(("/usr" + "/bin", "/bin")),
    }
    return popen_program(
        [sys.executable, "-m", "demo_only.fake_model_server", *args],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kw,
    )


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the stand-in crashes on a non-object body or ignores port 0.
def test_port_zero_prints_the_real_port_and_answers(tmp_path: Path) -> None:
    proc = _run_fake(["--port", "0", "--mode", "ok"], REPO)
    try:
        assert proc.stdout is not None
        first = proc.stdout.readline().decode()
        port = int(first.rsplit(" ", 1)[1])
        assert first.startswith("fake model listening on port ") and port > 0
        deadline = time.monotonic() + 10
        while True:
            try:
                c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                c.request("GET", "/stats")
                assert c.getresponse().status == 200
                break
            except OSError:
                assert time.monotonic() < deadline
                time.sleep(0.1)
    finally:
        proc.terminate()
        proc.wait(10)
        if proc.stdout is not None:
            proc.stdout.close()


@pytest.mark.parametrize("content", ["", "\n", "   \n"])
def test_an_empty_key_file_is_refused_with_one_line(tmp_path: Path, content: str) -> None:
    key = tmp_path / "key.txt"
    key.write_text(content, encoding="utf-8")
    done = run_program(
        [sys.executable, "-m", "demo_only.fake_model_server", "--port", "0", "--key-file", str(key)],
        cwd=REPO,
        env={
            "PYTHONPATH": f"{REPO / 'src'}:{REPO}",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LEAD_DESK_PATH_ROOTS": str(tmp_path),
        },
        capture_output=True,
        timeout=30,
    )
    text = done.stdout.decode() + done.stderr.decode()
    assert done.returncode != 0 and "no key" in text and "Traceback" not in text, text


@pytest.fixture
def model() -> Any:
    srv, state = make_model_server(port=0, mode="ok", key=KEY)
    thread = start_serving(srv)
    yield srv.server_port, state
    stop_serving(srv, thread)


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the stand-in crashes on a non-object body or ignores port 0.
@pytest.mark.parametrize("body", [b"[" * 100_000, b"[]", b"{not json", b"\xff\xfe", b"null"])
def test_a_message_body_that_is_not_an_object_is_an_empty_request_and_answers_200(model: Any, body: bytes) -> None:
    port, state = model
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    c.request("POST", "/v1/messages", body, {"x-api-key": KEY, "Content-Type": "application/json"})
    r = c.getresponse()
    r.read()
    assert r.status == 200 and state.calls == 1 and state.last_request == {}


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the stand-in crashes on a non-object body or ignores port 0.
def test_a_control_body_that_is_not_an_object_is_a_400(model: Any) -> None:
    port, _state = model
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    c.request("POST", "/control", b"[" * 100_000, {"Content-Type": "application/json"})
    r = c.getresponse()
    r.read()
    assert r.status == 400
