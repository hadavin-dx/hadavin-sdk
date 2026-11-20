"""A REAL start of the worker through `main`, as child processes, on a config that has a `triggers` block.

It needs the trigger config of core-b (`hadavin_sdk.config.TriggerSettings`, `App.trigger_secret`); on a tree without
it the whole file is skipped. The child is `python -m hadavin_sdk.triggers.worker --config-dir <dir> --port <p>`:
core-b's settings have no host or port, so the command line gives the port (a free one picked here). The sender
secrets reach the child through the `env` secrets kind (`HADAVIN_SECRET_<NAME>`, demo only). The store is the memory
store (a child's memory is not readable from here), so "a run row exists" is shown by what the worker answered:
a 2xx is sent only after the row was read, and a repeat of the same key gives the same run id from that row.

Fake secrets are built from parts; nothing here is a real secret.
"""

from __future__ import annotations

import dataclasses
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import ClassVar

import pytest

from tests.triggers.conftest import require_core_b

require_core_b(allow_module_level=True)  # with HADAVIN_REQUIRE_PG=1 a missing config is a failure, not a skip

from hadavin_sdk.config import load_config
from hadavin_sdk.registry import load_registry
from tests.conftest import make_cfg, qualify
from tests.triggers.crash_launcher import signed_post, wire_body

AGENT, PRINCIPAL = "test-agent", "svc:test-agent"
GOOD = "g" * 20 + "-" + "9" * 20  # 41 characters
OTHER = "o" * 20 + "-" + "8" * 20
SHORT = "short-" + "7" * 10  # 16 characters: below the 32 of the endpoint
DOCUMENT = "checkout 5xx from 10.0.0.5, revision 17"
FIXTURE = {"FIXTURE_TOKEN": "f" * 20 + "-" + "6" * 20}
ANY_HOST = ".".join(["0"] * 4)  # every interface: the value the worker must refuse
START_WAIT_S, EXIT_WAIT_S = 40.0, 40.0

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="SIGTERM cannot be handled on Windows"
)


def _senders_yaml(senders: dict[str, tuple[list[str], str]]) -> str:
    lines = ["triggers:", "  tenant: tenant-a", "  senders:"]
    for sender_id, (names, agent) in senders.items():
        lines += [
            f"    {sender_id}:",
            f"      secret_names: [{', '.join(names)}]",
            f"      agent_id: {agent}",
            f"      principal_id: '{PRINCIPAL}'",
        ]
    return "\n".join(lines) + "\n"


def _config(tmp_path: Path, senders=None, *, qualified: bool = True) -> Path:
    cfg = make_cfg(tmp_path)
    path = cfg / "config.yaml"
    text = path.read_text(encoding="utf-8").replace("secrets: fake", "secrets: {kind: env}")
    senders = senders or {"sender-a": (["door-a"], AGENT)}
    path.write_text(text + _senders_yaml(senders), encoding="utf-8")
    if qualified:
        qualify(load_registry(load_config(cfg)))
    return cfg


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _spawn(tmp_path: Path, cfg: Path, secrets: dict[str, str], *args: str) -> subprocess.Popen:
    env = {k: v for k, v in os.environ.items() if not k.startswith("HADAVIN_SECRET_")}
    # the fixture config's executor secret is read at start-up as well
    env.update({f"HADAVIN_SECRET_{name}": value for name, value in {**FIXTURE, **secrets}.items()})
    out, err = tmp_path / "out.txt", tmp_path / "err.txt"
    with out.open("wb") as o, err.open("wb") as e:
        return subprocess.Popen(  # noqa: S603 - this interpreter, the worker module, no shell
            [sys.executable, "-m", "hadavin_sdk.triggers.worker", "--config-dir", str(cfg), *args],
            cwd=tmp_path,
            env=env,
            stdout=o,
            stderr=e,
            stdin=subprocess.DEVNULL,
        )


def _text(tmp_path: Path, name: str) -> str:
    return (tmp_path / name).read_text(encoding="utf-8", errors="replace")


def _refused(tmp_path: Path, cfg: Path, secrets: dict[str, str], *args: str, values=()):
    """Start a child that must end with exit code 2; returns the stderr text."""
    port = _free_port()
    child = _spawn(tmp_path, cfg, secrets, "--port", str(port), *args)
    try:
        code = child.wait(timeout=EXIT_WAIT_S)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
    out, err = _text(tmp_path, "out.txt"), _text(tmp_path, "err.txt")
    assert code == 2, (code, err[-1500:])
    assert "Traceback" not in out + err
    for value in values:
        assert value not in out + err
    refusals = [
        line for line in err.splitlines() if line.startswith("trigger worker: config error")
    ]
    assert len(refusals) == 1, err
    # Every other line is a warning of the worker's own (memory store, spend), never a second refusal.
    assert [line for line in err.splitlines() if "error" in line.lower()] == refusals, err
    return refusals[0]


def _wait_ready(child: subprocess.Popen, tmp_path: Path, port: int) -> None:
    deadline = time.monotonic() + START_WAIT_S
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise AssertionError(
                f"the worker ended (exit {child.returncode}): {_text(tmp_path, 'err.txt')[-2000:]}"
            )
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.1)
    raise AssertionError("the worker did not listen in time")


def test_1_starts_answers_a_signed_request_and_stops_on_sigterm_with_exit_0(tmp_path):
    cfg = _config(tmp_path)
    port = _free_port()
    child = _spawn(tmp_path, cfg, {"DOOR_A": GOOD}, "--port", str(port))
    try:
        _wait_ready(child, tmp_path, port)
        body = wire_body("key-1", DOCUMENT)
        status, answer = signed_post(port, body, GOOD)
        assert status in (200, 202), (status, answer, _text(tmp_path, "err.txt")[-1500:])
        first = json.loads(answer)
        assert first["run_id"] and first["state"]
        # The same key again: the answer is built from the stored row, so the run id is the same one.
        status2, answer2 = signed_post(port, body, GOOD)
        assert status2 in (200, 202) and json.loads(answer2)["run_id"] == first["run_id"]
        # A wrong secret is refused and starts nothing.
        assert signed_post(port, wire_body("key-2", DOCUMENT), OTHER)[0] in (401, 403)
        child.send_signal(signal.SIGTERM)
        code = child.wait(timeout=EXIT_WAIT_S)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
    out, err = _text(tmp_path, "out.txt"), _text(tmp_path, "err.txt")
    assert code == 0, (code, err[-1500:])
    assert "Traceback" not in out + err and GOOD not in out + err and OTHER not in out + err


def test_2a_a_secret_shorter_than_32_characters_is_refused(tmp_path):
    line = _refused(tmp_path, _config(tmp_path), {"DOOR_A": SHORT}, values=(SHORT,))
    assert "sender-a" in line or "secret" in line


def test_2b_two_senders_with_one_secret_value_are_refused(tmp_path):
    cfg = _config(tmp_path, {"sender-a": (["door-a"], AGENT), "sender-b": (["door-b"], AGENT)})
    _refused(tmp_path, cfg, {"DOOR_A": GOOD, "DOOR_B": GOOD}, values=(GOOD,))


def test_2c_a_sender_whose_agent_is_not_qualified_is_refused(tmp_path):
    cfg = _config(tmp_path, qualified=False)  # the gate record is missing: no agent is qualified
    line = _refused(tmp_path, cfg, {"DOOR_A": GOOD}, values=(GOOD,))
    assert "not qualified" in line and "sender-a" in line


def test_2d_a_host_that_is_not_loopback_needs_the_command_line_switch(tmp_path):
    # core-b's settings have no `allow_non_loopback`: the switch is `--allow-non-loopback`.
    line = _refused(
        tmp_path, _config(tmp_path), {"DOOR_A": GOOD}, "--host", ANY_HOST, values=(GOOD,)
    )
    assert "not loopback" in line and "--allow-non-loopback" in line


def test_2e_a_port_already_in_use_is_a_config_error(tmp_path):
    cfg = _config(tmp_path)
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen(1)
        port = taken.getsockname()[1]
        child = _spawn(tmp_path, cfg, {"DOOR_A": GOOD}, "--port", str(port))
        try:
            code = child.wait(timeout=EXIT_WAIT_S)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=10)
    out, err = _text(tmp_path, "out.txt"), _text(tmp_path, "err.txt")
    assert code == 2, (code, err[-1500:])
    assert "Traceback" not in out + err and GOOD not in out + err
    assert [line for line in err.splitlines() if "cannot listen" in line] != []
    assert len([line for line in err.splitlines() if "config error" in line]) == 1


def test_3_the_worker_asks_only_for_the_names_the_senders_list(tmp_path):
    """In this process, with the real `App`: a recording provider; `App.trigger_secret` refuses any other name."""
    from hadavin_sdk.app import build
    from hadavin_sdk.triggers import worker

    asked: list[str] = []

    class Recording:
        values: ClassVar[dict[str, str]] = {
            "door-a": GOOD,
            "door-b": OTHER,
            "never-listed": "n" * 40,
            "fixture-token": "f" * 40,
        }

        def get(self, name: str) -> str:
            asked.append(name)
            return self.values[name]

    cfg = _config(tmp_path, {"sender-a": (["door-a"], AGENT), "sender-b": (["door-b"], AGENT)})
    app = build(cfg, [AGENT], secrets=Recording())
    with pytest.raises(PermissionError) as refusal:
        app.trigger_secret("never-listed")
    assert "never-listed" not in str(refusal.value)
    assert "never-listed" not in asked
    calls: list[str] = []
    real = app.trigger_secret

    def spy(name: str) -> str:
        calls.append(name)
        return real(name)

    app = dataclasses.replace(app, trigger_secret=spy)
    _wsgi, runner = worker.make_app(app)
    runner.close(0)
    assert sorted(calls) == ["door-a", "door-b"]
    assert "never-listed" not in asked
