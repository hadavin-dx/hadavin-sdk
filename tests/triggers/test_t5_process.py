"""Ticket D cases that need a process but no database: start refusal through `main`, the pure start
checks, and the stop signal.

D1 starts `python -m hadavin_sdk.triggers.worker` as a child. D3 starts
`tests/triggers/crash_launcher.py` on the memory store (the launcher builds the worker from its
pieces and serves through `worker.serve`; it does not call `main`, which needs the config block
`triggers` that does not exist yet). Ticket case ids (tickets/D-signed-endpoint.md, section 10) are
named in each docstring.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.triggers import endpoint, worker
from tests.conftest import make_cfg
from tests.k5_support import k5_cfg
from tests.triggers.conftest import require_core_b
from tests.triggers.crash_launcher import ROOT, TENANT, Child, signed_post, wire_body

SENDER, AGENT, PRINCIPAL = "sender-a", "test-agent", "svc:test-agent"
# Fake secrets, built from parts at run time.
SECRET = "t5" * 4 + "c" * 32
OTHER_SECRET = "t5" * 4 + "d" * 32
SHORT_SECRET = "t5" + "e" * 29  # 31 characters: one under the floor
CANARY = "canary-" + "f" * 33  # in the child's environment; must never be printed
CHILD_TIMEOUT_S = 60
STOP_WAIT_S = 15.0
DOCUMENT = "checkout 5xx from 10.0.0.5, revision 17"


# --- D1: start refusal through main ---------------------------------------------------------------


def _run_main(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603 - this interpreter, the module under test, no shell
        [sys.executable, "-m", "hadavin_sdk.triggers.worker", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        check=False,
        env={**os.environ, "TRIGGER_TEST_CANARY": CANARY},
    )


def test_d1_main_refuses_to_start_without_a_triggers_block(tmp_path):
    """D1 (ticket H8 through `main`). Start: the worker module as a child process on a copy of the
    fixture config, which has no `triggers` block. Expected: exit code 2, one clear line on stderr,
    nothing on stdout, no traceback, nothing from the environment. Store: none is opened."""
    require_core_b()  # the real Config must have the `triggers` field
    cfg = make_cfg(tmp_path)
    done = _run_main("--config-dir", str(cfg), "--port", "0")
    assert done.returncode == 2, done.stderr
    assert "triggers block not configured" in done.stderr
    assert done.stderr.startswith("trigger worker: config error:")
    assert len(done.stderr.strip().splitlines()) == 1
    assert done.stdout == ""
    assert "Traceback" not in done.stderr and CANARY not in done.stderr + done.stdout


def test_d1_main_refuses_an_unreadable_config_without_a_traceback(tmp_path):
    """D1 (ticket H8 through `main`). Start: the worker module as a child process on a folder that
    does not exist. Expected: exit code 2, a config error line, no traceback, no serving line."""
    done = _run_main("--config-dir", str(tmp_path / "missing"), "--port", "0")
    assert done.returncode == 2, done.stderr
    assert "config error" in done.stderr and "Traceback" not in done.stderr
    assert "serving" not in done.stderr and done.stdout == ""
    assert CANARY not in done.stderr


# --- D2: the pure start checks --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("secrets", "words"),
    [
        ({SENDER: (SHORT_SECRET,)}, "a secret under 32 characters"),
        ({SENDER: (SECRET,), "sender-b": (SECRET,)}, "share a secret"),
        ({SENDER: (SECRET, OTHER_SECRET), "sender-b": (OTHER_SECRET,)}, "share a secret"),
        ({SENDER: ()}, "no secret"),
        ({SENDER: ("",)}, "an empty secret"),
        ({}, "no trigger sender has a secret"),
    ],
    ids=["short", "shared", "shared-second-value", "none", "empty", "no-sender"],
)
def test_d2_check_secrets_refuses_and_never_prints_a_value(secrets, words):
    """D2 (ticket H8). Start check `check_secrets`: a secret one character under the floor, one
    value shared by two senders, no value, an empty value. Expected: ValueError that names the
    sender and the rule, never a value. Store: not touched."""
    with pytest.raises(ValueError, match=words) as refused:
        endpoint.check_secrets(secrets)
    text = str(refused.value)
    assert not any(value and value in text for values in secrets.values() for value in values)


def test_d2_check_secrets_accepts_the_floor_and_two_values():
    """D2 control: 32 characters, and two different values for one sender, are accepted."""
    endpoint.check_secrets({SENDER: (SHORT_SECRET + "e",), "sender-b": (SECRET, OTHER_SECRET)})


def _sender(**over):
    base = {"id": SENDER, "secret_names": ["door-a"], "agent_id": AGENT, "principal_id": PRINCIPAL}
    return SimpleNamespace(**{**base, **over})


PRINCIPALS = {PRINCIPAL: SimpleNamespace(kind="service"), "ada": SimpleNamespace(kind="human")}


@pytest.mark.parametrize(
    ("over", "words"),
    [
        ({"agent_id": "no-such-agent"}, "agent no-such-agent is not qualified"),
        ({"principal_id": "svc:nobody"}, "principal svc:nobody is not in principals.yaml"),
        ({"principal_id": "ada"}, "principal ada is not of kind service"),
    ],
    ids=["unknown-agent", "unknown-principal", "principal-not-service"],
)
def test_d2_check_senders_refuses_a_bad_agent_or_principal(over, words):
    """D2 (ticket H8). Start check `check_senders`: a sender whose agent is not qualified, whose
    principal is unknown, whose principal is not of kind service. Expected: ConfigError naming the
    sender and the reason. Store: not touched."""
    with pytest.raises(ConfigError, match=words) as refused:
        worker.check_senders([(SENDER, _sender(**over))], [AGENT], PRINCIPALS)
    assert f"trigger sender {SENDER}" in str(refused.value)


def test_d2_check_senders_accepts_a_qualified_agent_and_a_service_principal():
    """D2 control: the good sender passes."""
    worker.check_senders([(SENDER, _sender())], [AGENT], PRINCIPALS)


@pytest.mark.parametrize(
    ("host", "words"),
    [
        ("0.0.0.0", "is not loopback"),  # noqa: S104 - the refused value, nothing binds to it
        ("192.0.2.7", "is not loopback"),
        ("", "must be an IP address or localhost"),
        ("example.invalid", "must be an IP address or localhost"),
    ],
    ids=["every-interface", "other-address", "empty", "host-name"],
)
def test_d2_check_bind_refuses_a_host_that_is_not_loopback(host, words):
    """D2 (ticket H8). Start check `check_bind` without the switch: every interface, a public
    address, an empty host, a host name. Expected: ConfigError. Store: not touched."""
    with pytest.raises(ConfigError, match=words):
        worker.check_bind(host, False)


def test_d2_check_bind_needs_the_switch_to_be_exactly_true():
    """D2: loopback and localhost pass; a non-loopback address passes only with the switch set to
    the boolean True (a truthy text does not count); a host name is refused even with it."""
    worker.check_bind("127.0.0.1", False)
    worker.check_bind("localhost", False)
    worker.check_bind("192.0.2.7", True)
    with pytest.raises(ConfigError, match="is not loopback"):
        worker.check_bind("192.0.2.7", "true")  # type: ignore[arg-type]
    with pytest.raises(ConfigError, match="must be an IP address or localhost"):
        worker.check_bind("example.invalid", True)


# --- D3: the stop signal --------------------------------------------------------------------------


@pytest.mark.skipif(sys.platform == "win32", reason="SIGTERM cannot be handled on Windows")
def test_d3_sigterm_stops_a_serving_worker_cleanly(tmp_path):
    """D3 (review finding Major 2). A serving child (memory store, a model double that takes 1.5 s).
    Request: one signed key, answered 202 while its loop is still running; SIGTERM right after.
    Expected: the child exits 0 within a few seconds, with no traceback, and the port is closed.
    Store (printed by the child after `serve` returned): the run row exists and has left RECEIVED
    and WORKING, so the running loop was allowed to end; it was not left for the tick."""
    cfg = k5_cfg(tmp_path)
    run_id = "run-" + hashlib.sha256(f"{TENANT}\0{SENDER}\0key-1".encode()).hexdigest()[:32]
    with Child(tmp_path / "child", cfg, {SENDER: SECRET}, "--llm-delay-s", "1.5") as child:
        status, data = signed_post(child.port, wire_body("key-1", DOCUMENT), SECRET)
        assert status == 202, (status, data)
        assert json.loads(data)["run_id"] == run_id
        sent = time.monotonic()
        child.proc.send_signal(signal.SIGTERM)
        assert child.wait(STOP_WAIT_S) == 0, child.stderr()[-2000:]
        took = time.monotonic() - sent
        out, err = child.stdout(), child.stderr()
        after = signed_post(child.port, wire_body("key-2", DOCUMENT), SECRET)
    assert took < STOP_WAIT_S
    assert out.strip().splitlines()[-1] == "stopped"
    assert "Traceback" not in err and SECRET not in err + out
    states = [line.split()[2] for line in out.splitlines() if line.startswith(f"run {run_id} ")]
    assert len(states) == 1, out
    assert states[0] not in ("RECEIVED", "WORKING"), out
    assert after[0] is None  # nothing listens any more
