"""Fixes for the code review of PR #42 (egm/bhovix-core/pr42/review-code-1.md): M2 input cap on redaction, M3 grounding
cannot be left off, m1 the request carries the checked host, m2 more refused ranges, m3 lookups cannot pile up threads,
m5 what the redactor does not claim, and the ledger refusing two migrations with one number (B2)."""

from __future__ import annotations

import ipaddress
import threading
import time

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.config import load_config
from hadavin_sdk.guard import http as http_guard
from hadavin_sdk.guard import runmap
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store import migrate as mig
from tests.conftest import qualify
from tests.k5_support import SECRETS, ScriptLLM, build_runtime, k5_cfg
from tests.test_k5_review import _ctx

# --- M2: redact_text is the one choke point for input size ------------------------------------------------------------

TOO_BIG = "x" * (defaults.MAX_REDACT_CHARS + 1)


def test_redact_text_refuses_more_than_the_cap_without_redacting():
    with pytest.raises(runmap.RedactionError):
        runmap.redact_text(TOO_BIG, {})
    assert runmap.redact_text("x" * defaults.MAX_REDACT_CHARS, {}) != ""  # the cap itself is fine


def test_every_entry_point_inherits_the_cap():
    with pytest.raises(runmap.RedactionError):
        runmap.redact_untrusted(TOO_BIG, {})
    with pytest.raises(runmap.RedactionError):
        runmap.redact_value({"a": TOO_BIG}, {})
    # many small strings are as costly as one big one
    half = "y" * (defaults.MAX_REDACT_CHARS // 2 + 1)
    with pytest.raises(runmap.RedactionError):
        runmap.redact_value([half, half], {})
    with pytest.raises(runmap.RedactionError):
        runmap.redact_value({half: half}, {})


def test_a_tool_result_is_cut_before_redaction_whatever_the_manifest_cap():
    huge = "a" * (3 * defaults.MAX_REDACT_CHARS)
    out = tools_mod.prepare_output(
        huge, {}, 10 * defaults.MAX_REDACT_CHARS, None, 4 * defaults.MAX_REDACT_CHARS
    )
    assert len(out) <= defaults.MAX_REDACT_CHARS + 100  # cut, redacted, no RedactionError


# --- M3: a bare Hooks() cannot drop grounding ------------------------------------------------------------------------------


def test_a_runtime_without_a_validator_refuses_an_agent_with_identifier_inputs(tmp_path):
    with pytest.raises(ValueError, match="hooks.validate_proposal"):
        build_runtime(k5_cfg(tmp_path), ScriptLLM([]), validate=False)


def test_a_runtime_without_a_validator_refuses_an_untooled_agent_too(tmp_path):
    cfg = k5_cfg(tmp_path, tools=[], tools_allowed=[])
    cfg_obj = load_config(cfg)
    reg = load_registry(cfg_obj)
    qualify(reg)
    with pytest.raises(ValueError, match="identifier inputs"):
        Runtime(reg, MemoryStore(), None, None, None, None, ["test-agent"], Hooks())


def test_the_app_factory_always_supplies_the_validator(tmp_path):
    for sub, kw in (("tooled", {}), ("plain", {"tools": [], "tools_allowed": []})):
        cfg = k5_cfg(tmp_path / sub, **kw)
        qualify(load_registry(load_config(cfg)))
        app = app_mod.build(cfg, ["test-agent"], secrets=SECRETS, llm=ScriptLLM([]))
        assert app.runtime.hooks.validate_proposal is not None, sub


# --- m1: the request carries the host the checks read ------------------------------------------------------------------------


class _Resp:
    def read(self, n=-1):
        return b""

    def __enter__(self):
        return self

    def __exit__(self, *e):
        return False


@pytest.mark.parametrize(
    ("sent", "expected"),
    [
        ("https://API.EXAMPLE.COM./x", "https://api.example.com/x"),
        ("https://api.example.com./x?q=1", "https://api.example.com/x?q=1"),
        ("https://Api.Example.Com:443/x", "https://api.example.com:443/x"),
    ],
)
def test_the_opener_receives_the_normalised_host(monkeypatch, sent, expected):
    seen = []

    class Opener:
        def open(self, req, timeout=None):
            seen.append(req.full_url)
            return _Resp()

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", Opener())
    _ctx(ports=[443]).fetch("GET", sent, operation="bundle.read")
    assert seen == [expected]


# --- m2: ranges the address check refuses ----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ip",
    [
        "0.0.0.1",  # 0.0.0.0/8: "this network", Linux connects it to the local host
        "0.255.255.255",
        "64:ff9b:1::7f00:1",  # the local-use NAT64 prefix (RFC 8215), whole
        "64:ff9b::7f00:1",  # NAT64 of loopback
        "::ffff:169.254.169.254",  # IPv4-mapped metadata
        "::ffff:100.100.100.200",  # IPv4-mapped metadata that no stdlib flag knows (only the embedded check sees it)
        "::ffff:198.18.0.7",  # IPv4-mapped benchmark range
        "2002:7f00:1::1",  # 6to4 of loopback
        "fd00:ec2::254",  # the AWS metadata service over IPv6
    ],
)
def test_more_refused_forms(ip):
    assert http_guard._refused(ipaddress.ip_address(ip))


def test_the_carrier_grade_nat_range_stays_allowed_on_purpose():
    assert not http_guard._refused(ipaddress.ip_address("100.64.0.9"))


# --- m3: name lookups that never answer cannot pile up threads -------------------------------------------------------------------


def test_stuck_lookups_are_capped(monkeypatch):
    release = threading.Event()
    monkeypatch.setattr(http_guard, "RESOLVE_TIMEOUT_S", 0.01)
    monkeypatch.setattr(http_guard.socket, "getaddrinfo", lambda *a, **k: release.wait(5))
    before = threading.active_count()
    try:
        for _ in range(http_guard.MAX_STUCK_LOOKUPS):
            with pytest.raises(OSError, match="took more than"):
                http_guard._resolve("slow.example.test", 443)
        with pytest.raises(OSError, match="too many name lookups"):
            http_guard._resolve("slow.example.test", 443)
        assert threading.active_count() - before <= http_guard.MAX_STUCK_LOOKUPS
    finally:
        release.set()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and threading.active_count() > before:
            time.sleep(0.01)
    http_guard._STUCK.acquire()  # all permits are back: one can be taken again...
    http_guard._STUCK.release()  # ...and is returned


# --- m5: what the redactor claims (bare tokens) ---------------------------------------------------------------------------------


def test_a_labelled_secret_is_masked_but_a_bare_unlabelled_hex_token_in_prose_is_out_of_scope():
    """The scope is written in guard/redact.py: a secret is found by its label or its known prefix. A bare 40-hex
    string in prose has no label, so it is NOT claimed (it looks like a git SHA or a build id, which the model
    needs). This pins that scope, so widening or narrowing it is a decision, not an accident."""
    bare = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b"
    assert bare not in runmap.redact_text(f"api_key={bare}", {})
    assert bare in runmap.redact_text(f"the build {bare} failed", {})


# --- B2: two migrations with one number are refused -------------------------------------------------------------------------------


def test_the_real_migrations_never_share_a_number():
    numbers = [p.name[:4] for p in mig._migration_files()]
    assert len(numbers) == len(set(numbers)), numbers
    assert mig.check_ledger(mig._migration_files()) == []
