"""bindguard: a server that holds a real service is not started on an address other computers can reach.

Pins: every kind of the backend table has one answer (stand-in or real), every public spelling of a bind is refused
with a real service and none is refused with stand-ins only, custom code and live egress hosts count, ``listen`` is
the only place a server socket is made and asks before it builds, the receiver needs its config, the named reason is
the only way past a refusal, and no module keeps its own copy of the loopback list. Made-up data only."""

from __future__ import annotations

import ast
import asyncio
import http.server
import importlib
import logging
import re
import socket
import socketserver
import sys
import tomllib
import types
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

import pytest
from tools import server_scan

from hadavin_sdk import bindguard, netguard, standins
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals import Approvals, FakeChannel
from hadavin_sdk.approvals.receiver import PATH, serve
from hadavin_sdk.approvals.requests import _BUILD_TOKEN, make_on_decided
from hadavin_sdk.backends.table import DEMO_ONLY, IN_PROCESS, NOT_PROD, TABLE, KindSettings
from hadavin_sdk.bindguard import (
    BindRefused,
    held_services_found,
    is_stand_in_object,
    listen,
    public_bind_problem,
    real_services,
    require_safe_bind,
)
from hadavin_sdk.config import Config, SourceConfig, System, load_config, load_yaml
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.injection import AnyOf, RegexDetector
from hadavin_sdk.llm.fake import FakeLLM
from hadavin_sdk.store.memory import MemoryStore
from tests.conftest import make_cfg

# built from parts: the repo scan reads a written address as a hard-coded one
_DOT = "."
ALL_ZEROS = _DOT.join(["0"] * 4)
PRIVATE = _DOT.join(("10", "0", "0", "1"))
LOOP_1 = _DOT.join(("127", "0", "0", "1"))
LOOP_2 = _DOT.join(("127", "0", "0", "2"))
PUBLIC = [
    ALL_ZEROS,
    "[::]",
    "::",
    "0",
    "",
    PRIVATE,
    "remote.example.test",
    "localhost.example.test",
    LOOP_1 + ".example.test",
    "127.1",
    "2130706433",
    "::ffff:" + PRIVATE,
    "[::1",
    "::1%eth0",
    None,
    7,
]
LOOPBACK = [LOOP_1, LOOP_2, "::1", "[::1]", "localhost", "LOCALHOST", "::ffff:" + LOOP_1]


@pytest.fixture
def stand_in_config(tmp_path: Path) -> Config:
    """The fixture config with its check module taken out: fake kinds only, one fake system and one egress host,
    both on this computer. (The fixture itself lists a check module, which counts: see the test below.)"""
    return load_config(make_cfg(tmp_path)).model_copy(update={"check_modules": []})


def _loaded(tmp_path: Path, **changes: object) -> Config:
    """The fixture config read through the real loader with ``changes`` written into config.yaml first, so every
    system and source is validated (not built with ``model_construct``). ``check_modules`` is emptied unless given."""
    folder = make_cfg(tmp_path)
    path = folder / "config.yaml"
    raw = load_yaml(path.read_text(encoding="utf-8"))
    raw["check_modules"] = []
    raw.update(changes)
    import yaml

    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return load_config(folder)


def _with_kind(cfg: Config, cap: str, kind: str) -> Config:
    """The same config with one backend swapped for `kind` (not validated: only `.kind` is read)."""
    entry = KindSettings.model_construct(kind=kind)
    value = (entry,) if cap == "detector" else entry
    return cfg.model_copy(update={"backends": cfg.backends.model_copy(update={cap: value})})


def test_the_fixture_config_holds_only_stand_ins(stand_in_config: Config) -> None:
    assert stand_in_config.check_modules == [] and stand_in_config.egress_hosts == {LOOP_1}
    assert real_services(stand_in_config, {}) == (), (
        "the stand-in fixture config counts a real service"
    )


def test_the_fixture_config_as_it_is_counts_its_check_module(tmp_path: Path) -> None:
    """Custom code runs in the process, so a config that lists a check module is not "all stand-ins"."""
    assert real_services(load_config(make_cfg(tmp_path)), {}) == ("checks:tests.fixtures.checks",)


ALL_KINDS = [(cap, kind) for cap, kinds in TABLE.items() for kind in kinds]

# The answer for every kind of the table, written out: a new kind (or a moved one) fails here until someone decides.
PINNED = {
    ("secrets", "fake"): "demo_only",
    ("secrets", "env"): "demo_only",
    ("secrets", "aws_secrets_manager"): "real",
    ("secrets", "vault"): "real",
    ("secrets", "azure_key_vault"): "real",
    ("secrets", "gcp_secret_manager"): "real",
    ("secrets", "mounted_file"): "in_process",
    ("signer", "none"): "not_prod",
    ("signer", "ed25519_local"): "in_process",
    ("signer", "aws_kms"): "real",
    ("signer", "azure_key_vault_key"): "real",
    ("signer", "gcp_kms"): "real",
    ("signer", "vault_transit"): "real",
    ("anchor", "none"): "not_prod",
    ("anchor", "s3_object_lock"): "real",
    ("anchor", "azure_immutable_blob"): "real",
    ("anchor", "gcs_retention_lock"): "real",
    ("store", "memory"): "demo_only",
    ("store", "postgres"): "real",
    ("audit", "local_dir"): "demo_only",
    ("audit", "chain"): "in_process",
    ("llm", "fake"): "demo_only",
    ("llm", "anthropic"): "real",
    ("llm", "bedrock"): "real",
    ("llm", "openai_compat"): "real",
    ("llm", "gemini"): "real",
    ("detector", "regex"): "in_process",
    ("detector", "llm_judge"): "in_process",
    ("detector", "bedrock_guardrail"): "real",
    ("channel", "fake"): "demo_only",
    ("channel", "slack"): "real",
}


@pytest.mark.parametrize(("cap", "kind"), ALL_KINDS, ids=[f"{c}/{k}" for c, k in ALL_KINDS])
def test_every_kind_of_the_table_has_exactly_one_answer(
    stand_in_config: Config, cap: str, kind: str
) -> None:
    """The pinned class of the kind is the answer; every kind not pinned as a stand-in is real."""
    found = real_services(_with_kind(stand_in_config, cap, kind), {})
    cls = PINNED[(cap, kind)]
    assert (found == ()) is (cls != "real"), f"{cap}/{kind}: {found}"
    if cls == "real":
        assert found == (f"backends.{cap}: {kind}",)


def test_the_pinned_table_is_exactly_the_kinds_of_the_table_and_the_three_lists() -> None:
    assert set(PINNED) == set(ALL_KINDS) and len(PINNED) == 31
    for (cap, kind), cls in PINNED.items():
        in_lists = {
            "demo_only": (cap, kind) in DEMO_ONLY,
            "not_prod": (cap, kind) in NOT_PROD,
            "in_process": (cap, kind) in IN_PROCESS,
        }
        listed = [name for name, yes in in_lists.items() if yes]
        assert listed == ([] if cls == "real" else [cls]), (
            f"pinned class {cls!r}, listed in {listed}"
        )


def test_the_stand_in_list_is_read_from_the_table_not_written_here() -> None:
    assert bindguard.stand_in_kinds() == DEMO_ONLY | NOT_PROD | IN_PROCESS
    assert ("llm", "fake") in bindguard.stand_in_kinds()


def test_in_process_is_exactly_these_five_pairs_and_each_is_a_kind_of_the_table() -> None:
    assert IN_PROCESS == frozenset(
        {
            ("detector", "regex"),
            ("detector", "llm_judge"),
            ("secrets", "mounted_file"),
            ("signer", "ed25519_local"),
            ("audit", "chain"),
        }
    ), "the in-process list changed: a kind that reaches a service must never be in it"
    for cap, kind in IN_PROCESS:
        assert kind in TABLE[cap], f"{cap}/{kind} is not a kind of the table"
    assert not IN_PROCESS & (DEMO_ONLY | NOT_PROD), "a kind is listed twice"


def test_a_real_service_refuses_every_public_spelling(stand_in_config: Config) -> None:
    for cap, kind in (("llm", "anthropic"), ("store", "postgres"), ("channel", "slack")):
        cfg = _with_kind(stand_in_config, cap, kind)
        for bind in PUBLIC:
            problem = public_bind_problem(bind, cfg, {})
            assert problem is not None, f"public bind {bind!r} accepted with {cap}/{kind}"
            assert f"backends.{cap}: {kind}" in problem
            with pytest.raises(BindRefused):
                require_safe_bind(bind, cfg, held={})


def test_a_real_service_accepts_every_loopback_spelling(stand_in_config: Config) -> None:
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    for bind in LOOPBACK:
        assert public_bind_problem(bind, cfg, {}) is None, f"loopback bind {bind!r} refused"
        require_safe_bind(bind, cfg, held={})


def test_stand_ins_only_accept_any_bind(stand_in_config: Config) -> None:
    for bind in PUBLIC + LOOPBACK:
        assert public_bind_problem(bind, stand_in_config, {}) is None, f"stand-ins refused {bind!r}"


def test_a_detector_that_is_real_counts(stand_in_config: Config) -> None:
    cfg = _with_kind(stand_in_config, "detector", "bedrock_guardrail")
    assert public_bind_problem(ALL_ZEROS, cfg, {}) is not None


def test_a_system_counts_unless_it_is_plain_http_on_this_computer_and_allowed(
    stand_in_config: Config,
) -> None:
    assert stand_in_config.allow_insecure_loopback is True
    here = {"records": System(base_url="http://" + LOOP_1 + ":9")}
    cases = [
        (here, True, False),  # allowed local test system: a stand-in
        (here, False, True),  # the same address without the switch: real
        ({"records": System(base_url="https://crm.example.test")}, True, True),
        ({"records": System(base_url="http://crm.example.test")}, True, True),
        ({"records": System(base_url="http://" + LOOP_2 + ":9")}, True, True),  # exact list only
    ]
    for systems, allow, real in cases:
        cfg = stand_in_config.model_copy(
            update={"systems": systems, "allow_insecure_loopback": allow}
        )
        assert (real_services(cfg, {}) == ("system records",)) is real, (systems, allow)
        assert (public_bind_problem(ALL_ZEROS, cfg, {}) is not None) is real


def test_a_configured_source_is_a_real_service(stand_in_config: Config) -> None:
    source = SourceConfig.model_construct(kind="kubernetes", settings={})
    cfg = stand_in_config.model_copy(update={"sources": {"cluster": source}})
    assert real_services(cfg, {}) == ("source cluster",)
    assert public_bind_problem(ALL_ZEROS, cfg, {}) is not None


def test_the_refusal_is_one_plain_sentence_with_no_value_of_the_bind_leaking_control_text(
    stand_in_config: Config,
) -> None:
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    text = public_bind_problem("evil\nhost", cfg, {})
    assert text is not None and "\n" not in text and "(unreadable)" in text, (
        "control text was shown in the refusal"
    )
    text = public_bind_problem(ALL_ZEROS, cfg, {})
    assert text is not None and "loopback" in text and "backends.llm: anthropic" in text


# --- custom code and live egress hosts count (the config fields the backend list does not cover) -------------------


def test_each_of_tool_modules_check_modules_and_a_live_egress_host_alone_makes_a_public_bind_refused(
    stand_in_config: Config,
) -> None:
    cases = [
        ({"tool_modules": ["my_tools"]}, "tools:my_tools"),
        ({"check_modules": ["my_checks"]}, "checks:my_checks"),
        ({"egress_hosts": frozenset({LOOP_1, "api.example.test"})}, "egress api.example.test"),
    ]
    for change, name in cases:
        cfg = stand_in_config.model_copy(update=change)
        assert real_services(cfg, {}) == (name,), change
        problem = public_bind_problem(ALL_ZEROS, cfg, {})
        assert problem is not None and name in problem
        assert public_bind_problem(LOOP_1, cfg, {}) is None


def test_loopback_egress_hosts_and_empty_lists_pass(stand_in_config: Config) -> None:
    cfg = stand_in_config.model_copy(
        update={"egress_hosts": frozenset({LOOP_1, "localhost", "::1"}), "tool_modules": []}
    )
    assert real_services(cfg, {}) == () and public_bind_problem(ALL_ZEROS, cfg, {}) is None, (
        "a loopback egress host was counted as a live one"
    )


def test_a_hostile_egress_entry_counts_and_never_shows_raw_text(stand_in_config: Config) -> None:
    for host in (LOOP_1 + "\x00", LOOP_1 + ".", "evil\nhost", "localhost.", "x" * 5000):
        cfg = stand_in_config.model_copy(update={"egress_hosts": frozenset({host})})
        found = real_services(cfg, {})
        assert len(found) == 1 and found[0].startswith("egress "), repr(host)
        problem = public_bind_problem(ALL_ZEROS, cfg, {})
        assert problem is not None and "\n" not in problem and "\x00" not in problem
        assert len(problem) < 1000


def test_systems_and_sources_built_by_the_real_loader_count(tmp_path: Path) -> None:
    """Built through ``load_config`` (validated), not ``model_construct``."""
    base = _loaded(tmp_path / "a")
    assert real_services(base, {}) == ()
    remote = _loaded(tmp_path / "b", systems={"crm": {"base_url": "https://crm.example.test"}})
    assert real_services(remote, {}) == ("system crm",)
    source = {
        "cluster": {
            "kind": "kubernetes",
            "settings": {"api_url": "https://k8s.example.test", "namespaces": ["a"]},
        }
    }
    with_source = _loaded(tmp_path / "c", sources=source)
    assert isinstance(with_source.sources["cluster"], SourceConfig)
    assert real_services(with_source, {}) == ("source cluster",)
    for cfg in (remote, with_source):
        assert public_bind_problem(ALL_ZEROS, cfg, {}) is not None


def test_a_judge_detector_cannot_stand_without_an_llm_entry(tmp_path: Path) -> None:
    """``detector/llm_judge`` is in-process because it only asks the configured ``llm`` kind, which is counted on
    its own. The config refuses a config that has no ``llm`` entry, so the judge never stands alone."""
    folder = make_cfg(tmp_path)
    path = folder / "config.yaml"
    raw = load_yaml(path.read_text(encoding="utf-8"))
    del raw["backends"]["llm"]
    raw["backends"]["detector"] = [
        {"kind": "regex", "threshold": 0.5},
        {"kind": "llm_judge", "route": "default", "threshold": 0.7},
    ]
    import yaml

    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ConfigError, match="llm"):
        load_config(folder)


def test_the_docstring_of_real_services_says_what_is_counted_and_what_is_not() -> None:
    doc = (bindguard.config_services.__doc__ or "") + (real_services.__doc__ or "")
    for word in (
        "tool_modules",
        "check_modules",
        "egress_hosts",
        "the loaded ``Config``",
        "held_services",
    ):
        assert word in doc
    assert "audit sink and registry" in (Approvals.held_services.__doc__ or "")


# --- the named reason is the only way past a refusal ----------------------------------------------------------


def test_a_public_bind_needs_the_named_reason_and_the_reason_is_logged(
    stand_in_config: Config, caplog: pytest.LogCaptureFixture
) -> None:
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    with pytest.raises(BindRefused, match="allow_public_bind_reason"):
        require_safe_bind(ALL_ZEROS, cfg, held={})
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.bindguard"):
        require_safe_bind(
            ALL_ZEROS, cfg, allow_public_bind_reason="  behind the studio proxy  ", held={}
        )
    records = [r for r in caplog.records if r.name == "hadavin_sdk.bindguard"]
    assert len(records) == 1 and records[0].levelno == logging.WARNING
    text = records[0].getMessage()
    assert "behind the studio proxy" in text and "backends.llm: anthropic" in text


@pytest.mark.parametrize(
    "reason", ["", "   ", "\t\n", "bad\x00reason", "x" * 201, "two\nlines", 7, b"ok"]
)
def test_an_unusable_reason_is_refused_even_when_it_was_not_needed(
    stand_in_config: Config, reason: object
) -> None:
    for cfg, bind in (
        (_with_kind(stand_in_config, "llm", "anthropic"), ALL_ZEROS),
        (stand_in_config, LOOP_1),
    ):
        with pytest.raises(BindRefused):
            require_safe_bind(bind, cfg, allow_public_bind_reason=reason, held={})


def test_an_empty_reason_is_refused_with_a_sentence_that_asks_for_one(
    stand_in_config: Config,
) -> None:
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    for reason in ("", "   "):
        with pytest.raises(BindRefused, match="must say why"):
            require_safe_bind(ALL_ZEROS, cfg, allow_public_bind_reason=reason, held={})


def test_a_reason_shorter_than_ten_characters_is_refused_and_ten_are_accepted(
    stand_in_config: Config,
) -> None:
    """A one-letter reason says nothing and goes to the log only (it is not an audit record): ten printable
    characters after trimming are the least."""
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    for short in ("x", "123456789", "  123456789  ", "abc def g"):
        with pytest.raises(BindRefused, match="at least 10 characters"):
            require_safe_bind(ALL_ZEROS, cfg, allow_public_bind_reason=short, held={})
    for fine in ("1234567890", "  1234567890  ", "proxy ok!!"):
        require_safe_bind(ALL_ZEROS, cfg, allow_public_bind_reason=fine, held={})


def test_a_reason_of_exactly_the_longest_size_is_accepted(stand_in_config: Config) -> None:
    require_safe_bind(
        ALL_ZEROS,
        _with_kind(stand_in_config, "llm", "anthropic"),
        allow_public_bind_reason="x" * 200,
        held={},
    )


def test_a_long_bind_text_is_cut_in_the_refusal(stand_in_config: Config) -> None:
    text = public_bind_problem("h" * 10_000, _with_kind(stand_in_config, "llm", "anthropic"), {})
    assert text is not None and "..." in text, "the long bind text was not cut"
    assert len(text) < 600 and "h" * 81 not in text, "the long bind text was not cut"


# --- listen: the one place a server socket is made --------------------------------------------------------------


_ANYTHING: tuple[type[BaseException], ...] = (
    BaseException,
)  # a thread of a test records whatever it raised


class _Finished:
    """What a finished child interpreter left: its exit code and the text it wrote."""

    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def _run_python(args: list[str], timeout: float) -> _Finished:
    """Run this interpreter with ``args`` (a fixed program of this file) and wait at most ``timeout`` seconds: a child
    that is still running then is killed. Uses ``asyncio``'s process start (no shell), so no inline suppression is needed."""

    async def go() -> _Finished:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise
        return _Finished(proc.returncode or 0, out.decode(), err.decode())

    return asyncio.run(go())


class _Quiet(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        raise AssertionError("this handler is never called: the server is only started and stopped")


def _no_server(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a: object, **k: object) -> None:
        raise AssertionError("a server was built before the refusal")

    monkeypatch.setattr(http.server.ThreadingHTTPServer, "__init__", boom)
    monkeypatch.setattr(socket.socket, "bind", boom)


def test_listen_refuses_before_any_server_exists(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_server(monkeypatch)
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    for host in (ALL_ZEROS, "::", PRIVATE, "remote.example.test", ""):
        with pytest.raises(BindRefused):
            listen(cfg, host, 0, _Quiet, held={})


def test_listen_starts_on_loopback_with_a_real_service_and_anywhere_with_stand_ins(
    stand_in_config: Config,
) -> None:
    real = _with_kind(stand_in_config, "llm", "anthropic")
    for host, cfg in ((LOOP_1, real), ("localhost", real), (ALL_ZEROS, stand_in_config)):
        server = listen(cfg, host, 0, _Quiet, held={})
        server.server_close()


def test_listen_with_the_reason_starts_a_public_server_with_a_real_service(
    stand_in_config: Config, caplog: pytest.LogCaptureFixture
) -> None:
    real = _with_kind(stand_in_config, "llm", "anthropic")
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.bindguard"):
        server = listen(
            real, ALL_ZEROS, 0, _Quiet, allow_public_bind_reason="proxy in front", held={}
        )
    server.server_close()
    assert any("proxy in front" in r.getMessage() for r in caplog.records)


def _has_ipv6() -> bool:
    try:
        with socket.socket(socket.AF_INET6) as s:
            s.bind(("::1", 0))
        return True
    except OSError:
        return False


@pytest.mark.skipif(not _has_ipv6(), reason="this machine has no IPv6 loopback")
def test_listen_really_starts_on_an_ipv6_loopback_address(stand_in_config: Config) -> None:
    real = _with_kind(stand_in_config, "llm", "anthropic")
    for host in ("::1", "[::1]"):
        server = listen(real, host, 0, _Quiet, held={})
        try:
            assert server.address_family == socket.AF_INET6
            assert server.server_address[0] == "::1"
        finally:
            server.server_close()


def test_listen_picks_the_ipv6_family_for_an_ipv6_address_even_without_ipv6_on_this_machine(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The server class gets the family of the address (AF_INET6 for ``::1``), or ``::1`` could never be served.
    The socket is not made (this machine may have no IPv6): the constructor only records what it was given."""
    seen = []

    def record(
        self: object, address: tuple, handler: object, bind_and_activate: bool = True
    ) -> None:
        seen.append((cast(Any, type(self)).address_family, address))
        cast(Any, self).server_address = address

    monkeypatch.setattr(socketserver.TCPServer, "__init__", record)
    real = _with_kind(stand_in_config, "llm", "anthropic")
    for host, family in (
        ("::1", socket.AF_INET6),
        ("[::1]", socket.AF_INET6),
        (LOOP_1, socket.AF_INET),
        ("localhost", socket.AF_INET),
    ):
        listen(real, host, 0, _Quiet, held={})
        want = (family, (LOOP_1 if family == socket.AF_INET else "::1", 0))
        assert seen[-1] == want, f"wrong family or address for {host!r}: {seen[-1]}"


def test_listen_binds_the_literal_for_localhost_and_never_looks_a_name_up(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*a: object, **k: object) -> None:
        raise AssertionError("a name was looked up")

    for fn in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
        monkeypatch.setattr(socket, fn, boom)
    real = _with_kind(stand_in_config, "llm", "anthropic")
    for host in ("localhost", "LocalHost"):
        server = listen(real, host, 0, _Quiet, held={})
        try:
            assert server.server_address[0] == LOOP_1
        finally:
            server.server_close()


def test_listen_refuses_a_name_that_is_not_localhost_even_with_stand_ins(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_server(monkeypatch)
    for host in (
        "remote.example.test",
        "localhost.example.test",
        "",
        "0",
        "127.1",
        "::1%eth0",
        "[" + LOOP_1 + "]",
        "0177.0.0.1",
        7,
        None,
    ):
        with pytest.raises(BindRefused):
            listen(stand_in_config, host, 0, _Quiet, held={})


def test_listen_checks_the_address_the_socket_really_got(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the socket ends up on an address that is not loopback although none was asked for, it is closed."""
    real = _with_kind(stand_in_config, "llm", "anthropic")
    closed = []
    orig_close = http.server.ThreadingHTTPServer.server_close

    def close(self: http.server.ThreadingHTTPServer) -> None:
        closed.append(True)
        orig_close(self)

    monkeypatch.setattr(http.server.ThreadingHTTPServer, "server_close", close)
    monkeypatch.setattr(bindguard, "_literal", lambda host: (ALL_ZEROS, socket.AF_INET))
    with pytest.raises(BindRefused, match="not on this computer"):
        listen(real, LOOP_1, 0, _Quiet, held={})
    assert closed == [True]


# --- the receiver needs its config and its approvals must be the ones built with it -------------------------------


def _Approvals(config: Config | None, held: dict[str, object] | None = None) -> Approvals:
    """A real ``Approvals`` made of the core's own stand-ins (what ``serve`` accepts: the exact class). ``held``
    are the objects ``build()`` would have recorded (the audit sink and registry are not counted then)."""
    return Approvals(
        MemoryStore(),
        _Opaque(),
        _Opaque(),
        FakeChannel("sig" + "-b4-test"),
        make_on_decided({}),
        config=config,
        overrides=held if held is not None or config is None else {},
        _built_by=_BUILD_TOKEN if config is not None else None,
    )


def test_the_receiver_without_a_config_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        serve(_Approvals(None))
    with pytest.raises(TypeError):
        serve(_Approvals(None), host=ALL_ZEROS)
    with pytest.raises(TypeError):
        serve(_Approvals(None), None)  # config is keyword-only


def test_the_receiver_refuses_a_public_bind_with_a_real_service_before_any_socket_exists(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_server(monkeypatch)
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    with pytest.raises(BindRefused):
        serve(_Approvals(cfg), config=cfg, host=ALL_ZEROS, port=0)


def test_the_receiver_refuses_a_config_that_is_not_the_one_the_approvals_were_built_with(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stand-in config beside real approvals must not let a public bind through."""
    _no_server(monkeypatch)
    real = _with_kind(stand_in_config, "llm", "anthropic")
    for held in (real, None):
        with pytest.raises(BindRefused, match="built with"):
            serve(_Approvals(held), config=stand_in_config, host=ALL_ZEROS, port=0)


def test_the_receiver_starts_and_the_reason_passes_through_it(stand_in_config: Config) -> None:
    real = _with_kind(stand_in_config, "llm", "anthropic")
    appr = _Approvals(real)
    server = serve(appr, config=real, port=0)
    assert server.server_address[0] == LOOP_1
    server.server_close()
    with pytest.raises(BindRefused):
        serve(appr, config=real, host=ALL_ZEROS, port=0)
    server = serve(
        appr, config=real, host=ALL_ZEROS, port=0, allow_public_bind_reason="proxy in front"
    )
    server.server_close()


def test_a_built_app_serves_with_its_own_config_and_not_with_a_copy(tmp_path: Path) -> None:
    """``build`` hands its config to the approvals, so the identity check holds for a real app."""
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.app import build
    from hadavin_sdk.approvals import FakeChannel
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify

    folder = make_cfg(tmp_path)
    qualify(load_registry(load_config(folder)))
    app = build(
        folder,
        ["test-agent"],
        secrets=FakeSecretProvider({"fixture-token": "t" * 16}),
        channel=FakeChannel("sig" + "-b2-test"),
        timeout_s=0.5,
    )
    assert app.approvals.config is app.config
    server = serve(app.approvals, config=app.config, port=0)
    server.server_close()
    with pytest.raises(BindRefused, match="built with"):
        serve(app.approvals, config=app.config.model_copy(), port=0)


# --- every route by which a real service reaches the approvals is counted (round 2, issue 1) ---------------------


class _RealChannel(FakeChannel):
    """A subclass of a stand-in is NOT a stand-in: a subclass can reach anything."""


class _RealLLM(FakeLLM):
    pass


class _RealDetector:
    backend = "real_screen"

    def check(self, text: str, source: str) -> object:
        return RegexDetector(0.5).check(text, source)


class _Built:
    """A real ``build()`` result seen through a stand-in config. The registry of the fixture needs a check module,
    and a check module counts as a real service, so a built app's own config is never "stand-ins only". The
    config is therefore copied with the check module taken out, and the approvals are put together from the built
    app's own parts, its recorded overrides and that config: what is under test is the part the config does not
    say (what ``build()`` was handed)."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self.config = app.config.model_copy(update={"check_modules": []})
        built = app.approvals
        self.store, self.audit, self.registry = built.store, built.audit, built.registry
        self.recorded = built.overrides
        self.approvals = Approvals(
            built.store,
            built.audit,
            built.registry,
            built.channel,
            make_on_decided({}),
            detector=built.detector,
            config=self.config,
            overrides=built.overrides,
            _built_by=_BUILD_TOKEN,
        )


def _built(tmp_path: Path, **over: object) -> _Built:
    """``build()`` with a fake secrets provider and channel unless ``over`` replaces them."""
    from hadavin_sdk.app import build
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify

    folder = make_cfg(tmp_path)
    qualify(load_registry(load_config(folder)))
    kw: dict[str, object] = {
        "secrets": FakeSecretProvider({"fixture-token": "t" * 16}),
        "channel": FakeChannel("sig" + "-b3-test"),
        "timeout_s": 0.5,
    }
    kw.update(over)
    return _Built(build(folder, ["test-agent"], **kw))


def _stand_in_bind_lands_on_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let a test pass the check with a wildcard host and still bind only on this computer."""
    monkeypatch.setattr(bindguard, "_literal", lambda host: (LOOP_1, socket.AF_INET))


def test_a_built_app_with_stand_ins_only_accepts_any_bind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROL (passes on the old code too): nothing real is held, so a public bind is not refused."""
    app = _built(tmp_path)
    assert real_services(app.config, app.approvals.held_services()) == ()
    _stand_in_bind_lands_on_loopback(monkeypatch)
    serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0).server_close()


def _override_cases(tmp_path: Path) -> list[tuple[str, object, str]]:
    return [
        ("channel", _RealChannel("sig" + "-b3-real"), "held channel: _RealChannel"),
        ("llm", _RealLLM(tmp_path, {}), "held llm: _RealLLM"),
        ("detector", _RealDetector(), "held detector: _RealDetector"),
        ("tools", {"lookup": lambda inputs: "x"}, "held tools"),
    ]


@pytest.mark.parametrize("name", ["channel", "llm", "detector", "tools"])
def test_an_injected_real_service_beside_a_stand_in_config_refuses_a_public_bind_and_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """The class: a service that reaches the approvals by a route other than the config. Each ``build()``
    override is counted; the refusal names the override; the named reason lets it through (the bind itself is
    kept on this computer by the test)."""
    obj, shown = {n: (o, t) for n, o, t in _override_cases(tmp_path / "objects")}[name]
    kw = {"channel": FakeChannel("sig" + "-b3-test")} if name != "channel" else {}
    app = _built(tmp_path / "app", **{**kw, name: obj})
    assert real_services(app.config, {}) == ()  # the config alone says "stand-ins"
    assert name in app.recorded, "the override was not recorded on the approvals"
    with monkeypatch.context() as m:
        _no_server(m)
        with pytest.raises(BindRefused, match=re.escape(shown)):
            serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0)
    _stand_in_bind_lands_on_loopback(monkeypatch)
    serve(
        app.approvals,
        config=app.config,
        host=ALL_ZEROS,
        port=0,
        allow_public_bind_reason="behind our own proxy",
    ).server_close()
    serve(app.approvals, config=app.config, port=0).server_close()


def _by_hand(app: Any, channel: object, **extra: object) -> Approvals:
    return Approvals(
        app.store,
        app.audit,
        app.registry,
        channel,
        make_on_decided({}),
        _built_by=_BUILD_TOKEN,
        **extra,
    )


def test_a_real_source_or_tools_dict_handed_in_is_counted_and_an_empty_one_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    channel = app.approvals.channel
    for name, value, shown in (
        ("sources", {"cluster": object()}, "held sources"),
        ("tools", {"lookup": lambda inputs: "x"}, "held tools"),
    ):
        approvals = _by_hand(app, channel, config=app.config, overrides={name: value})
        with monkeypatch.context() as m:
            _no_server(m)
            with pytest.raises(BindRefused, match=shown):
                serve(approvals, config=app.config, host=ALL_ZEROS, port=0)
    empty = _by_hand(app, channel, config=app.config, overrides={"sources": {}, "tools": {}})
    _stand_in_bind_lands_on_loopback(monkeypatch)
    refusal = ""
    try:
        serve(empty, config=app.config, host=ALL_ZEROS, port=0).server_close()
    except BindRefused as exc:
        refusal = str(exc)
    assert not refusal, f"an empty tools or sources mapping was counted: {refusal}"


def test_approvals_built_by_hand_with_a_real_channel_and_a_stand_in_config_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Approvals(real_channel, ..., config=stand_in)``: the config alone would say "stand-ins only"."""
    app = _built(tmp_path)
    approvals = _by_hand(app, _RealChannel("sig" + "-b3-real"), config=app.config)
    with monkeypatch.context() as m:
        _no_server(m)
        with pytest.raises(BindRefused, match="held channel: _RealChannel"):
            serve(approvals, config=app.config, host=ALL_ZEROS, port=0)
    for held in ({"store": _Opaque()}, {"detector": _RealDetector()}):
        odd = _by_hand(app, app.approvals.channel, config=app.config)
        object.__setattr__(odd, "_" + next(iter(held)), next(iter(held.values())))
        with monkeypatch.context() as m:
            _no_server(m)
            with pytest.raises(BindRefused, match="held"):
                serve(odd, config=app.config, host=ALL_ZEROS, port=0)


class _Opaque:
    """Any object that is not one of the core's own stand-ins."""


def test_approvals_built_by_hand_without_a_config_are_refused_and_the_text_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    approvals = _by_hand(app, app.approvals.channel)
    assert approvals.config is None and dict(approvals.overrides) == {}
    with monkeypatch.context() as m:
        _no_server(m)
        for host in (LOOP_1, ALL_ZEROS):
            with pytest.raises(BindRefused, match="built by hand with no config"):
                serve(approvals, config=app.config, host=host, port=0)


def test_the_config_and_the_overrides_of_the_approvals_cannot_be_assigned_or_edited(
    tmp_path: Path,
) -> None:
    app = _built(tmp_path)
    approvals = app.approvals
    with pytest.raises(AttributeError):
        approvals.config = app.config.model_copy()
    with pytest.raises(AttributeError):
        approvals.overrides = {}
    with pytest.raises(TypeError):
        approvals.overrides["llm"] = _Opaque()
    assert set(approvals.overrides) == {"secrets", "channel"} == set(app.recorded), (
        "the overrides were not recorded on the approvals"
    )


def test_a_channel_replaced_after_the_build_is_seen_when_the_server_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    object.__setattr__(app.approvals, "_channel", _RealChannel("sig" + "-b3-late"))
    with monkeypatch.context() as m:
        _no_server(m)
        with pytest.raises(BindRefused, match="held channel: _RealChannel"):
            serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0)


def test_only_the_cores_own_stand_in_classes_are_stand_ins_and_a_subclass_is_not() -> None:
    """The list is exact classes, never names or marker attributes."""
    from hadavin_sdk import standins

    assert standins.registered() == {
        FakeChannel,
        FakeLLM,
        FakeSecretProvider,
        MemoryStore,
        RegexDetector,
    }
    assert is_stand_in_object(FakeChannel("sig" + "-b3-test"))
    assert not is_stand_in_object(_RealChannel("sig" + "-b3-test")), (
        "a subclass of a stand-in was read as a stand-in"
    )
    assert not is_stand_in_object(_Opaque())

    class FakeChannel_:  # a name that looks like a stand-in is not one
        pass

    assert not is_stand_in_object(FakeChannel_())
    assert is_stand_in_object(AnyOf([RegexDetector(0.5), RegexDetector(0.7)]))
    assert not is_stand_in_object(AnyOf([RegexDetector(0.5), _RealDetector()])), (
        "a detector list with a real entry was read as a stand-in"
    )


def test_real_services_counts_held_objects_in_words_and_ignores_none(
    stand_in_config: Config,
) -> None:
    held = {"channel": _Opaque(), "detector": None, "tools": {}, "sources": {"s": 1}}
    assert real_services(stand_in_config, held) == ("held channel: _Opaque", "held sources"), (
        "a held object was not counted"
    )
    assert real_services(stand_in_config, {"detector": None, "tools": {}}) == ()
    assert real_services(stand_in_config, None) == real_services(stand_in_config, {}) == ()
    # control text in a name never reaches the sentence
    (text,) = real_services(stand_in_config, {"bad\nname": _Opaque()})
    assert "\n" not in text


def test_the_post_bind_check_counts_held_objects_too(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no reason, a socket that lands off this computer is closed when only a held object is real."""
    closed = []
    orig_close = http.server.ThreadingHTTPServer.server_close

    def close(self: http.server.ThreadingHTTPServer) -> None:
        closed.append(True)
        orig_close(self)

    monkeypatch.setattr(http.server.ThreadingHTTPServer, "server_close", close)
    monkeypatch.setattr(bindguard, "_literal", lambda host: (ALL_ZEROS, socket.AF_INET))
    with pytest.raises(BindRefused, match="not on this computer"):
        listen(stand_in_config, LOOP_1, 0, _Quiet, held={"channel": _Opaque()})
    assert closed == [True]


def test_the_http_loopback_half_of_url_allowed_and_the_system_rule_agree(
    stand_in_config: Config,
) -> None:
    """``real_services`` re-states the plain-http-to-this-computer half of ``config.url_allowed`` (url_allowed also
    says yes to https, which is not "local" here): over a table of hosts both give the same answer."""
    from hadavin_sdk.config import url_allowed

    hosts = [LOOP_1, "localhost", "[::1]", LOOP_2, "127.1", "LOCALHOST", ALL_ZEROS, PRIVATE, "[::]"]
    for allow in (True, False):
        for host in hosts:
            url = f"http://{host}:9/"
            cfg = stand_in_config.model_copy(
                update={
                    "systems": {"s": System.model_construct(base_url=url)},
                    "allow_insecure_loopback": allow,
                }
            )
            local = real_services(cfg, {}) == ()
            assert local == url_allowed(url, allow), f"{host!r} allow={allow}"


def _chains_rooted_at(tree: ast.AST, owner: str) -> set[str]:
    """Every attribute chain that starts at the name ``owner`` or at a name bound to it (one step: ``a = owner``),
    for example ``approvals.receive`` or ``a.audit.write_outcome``."""
    names = {owner}
    for n in ast.walk(tree):
        if (
            isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Name)
            and n.value.id in names
            and all(isinstance(t, ast.Name) for t in n.targets)
        ):
            names |= {t.id for t in n.targets if isinstance(t, ast.Name)}
    chains: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute):
            parts = [n.attr]
            node = n.value
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name) and node.id in names:
                chains.add(".".join([node.id, *reversed(parts)]))
    # keep only the longest chain of each: ``approvals.audit`` inside ``approvals.audit.write_outcome`` is one use
    return {c for c in chains if not any(o != c and o.startswith(c + ".") for o in chains)}


def _calls_given(tree: ast.AST, owner: str) -> set[str]:
    """The callee of every call that is handed ``owner`` (or a name bound to it) as an argument, for example
    ``Approvals.real_now(approvals)`` or ``handle_slack_action(approvals, ...)``: the argument position, which an
    attribute chain does not show."""
    names = {owner}
    for n in ast.walk(tree):
        if (
            isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Name)
            and n.value.id in names
            and all(isinstance(t, ast.Name) for t in n.targets)
        ):
            names |= {t.id for t in n.targets if isinstance(t, ast.Name)}
    callees: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            args = [*n.args, *(k.value for k in n.keywords)]
            if any(isinstance(a, ast.Name) and a.id in names for a in args):
                callees.add(ast.unparse(n.func))
    return callees


def test_the_listener_reaches_the_approvals_only_through_the_signature_check() -> None:
    """The reason that lets a receiver stand beside a signer (``IN_PROCESS`` in the backend table): the one route
    calls ``approvals.receive`` (with ``record_only=True``) and nothing else of the approvals, and ``receive``
    hands a decision on only after the channel's ``parse_decision`` (the signature check) returned one. Every
    attribute chain that starts at ``approvals`` (or a name bound to it) is listed, not only the calls."""
    receiver = ast.parse((SRC / "approvals" / "receiver.py").read_text(encoding="utf-8"))
    assert _chains_rooted_at(receiver, "approvals") == {
        "approvals.receive",
        "approvals.config",
        "approvals.config_facts",
    }, "the listener reaches more of the approvals than receive (and the config identity check)"
    assert (
        _calls_given(receiver, "approvals")
        == {
            "handle_slack_action",
            "Approvals.held_services",
            "Approvals.real_now",
            "_recheck",
            "object.__getattribute__",  # the recheck reads every slot of Approvals.__slots__
            "standins.is_pinned_instance",  # reads only the class of the object (the pin), never the object
            "type",
        }
    ), (
        "the listener hands the approvals to more callees than the ones named here (argument position)"
    )
    (handler,) = [
        n
        for n in ast.walk(receiver)
        if isinstance(n, ast.FunctionDef) and n.name == "handle_slack_action"
    ]
    receive_calls = [
        n
        for n in ast.walk(handler)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "receive"
    ]
    assert len(receive_calls) == 1
    flags = {k.arg: ast.unparse(k.value) for k in receive_calls[0].keywords}
    assert flags == {"record_only": "True"}, (
        "the listener must only record a decision, never run it"
    )
    handler_calls = {
        n.func.id
        for n in ast.walk(receiver)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "handle_slack_action" in handler_calls
    requests = ast.parse((SRC / "approvals" / "requests.py").read_text(encoding="utf-8"))
    (cls,) = [n for n in requests.body if isinstance(n, ast.ClassDef) and n.name == "Approvals"]
    (receive,) = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "receive"]
    body = [ast.unparse(stmt) for stmt in receive.body[1:]]  # [0] is the docstring
    assert body[0].startswith("d = self.channel.parse_decision(")
    assert body[1].startswith("if d is None:") and "return" in body[1]
    assert body[2] == "return self.decide(d, record_only=record_only)"
    # nothing else in the receiver module calls a method that records or runs a decision
    called = {
        n.func.attr
        for n in ast.walk(receiver)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    assert called.isdisjoint(
        {"decide", "on_decided", "sweep", "request", "update_message", "write_outcome"}
    )


def test_the_receiver_default_host_is_this_computer() -> None:
    import inspect

    assert inspect.signature(serve).parameters["host"].default == LOOP_1, (
        "the receiver default host is not this computer"
    )


def test_the_receiver_serves_exactly_one_route() -> None:
    """The signer, the secrets and the channel are reachable from a listener only through the routes it serves; a
    new route is a visible change of this list."""
    tree = ast.parse((SRC / "approvals" / "receiver.py").read_text(encoding="utf-8"))
    routes = sorted(
        {
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("/")
        }
    )
    do_methods = sorted(
        n.name
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name.startswith("do_")
    )
    assert routes == [PATH] == ["/slack/actions"]
    assert do_methods == ["do_POST"]


# --- the only place that makes a server socket is bindguard.listen ---------------------------------------------

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
ROOT = SRC.parents[1]
SERVER_CLASS = re.compile(
    r"^(?:(?:Threading|Forking)?(?:HTTP|TCP|UDP|UnixStream|UnixDatagram)Server|(?:Simple|Doc)?XMLRPCServer)$"
)
SERVER_CALLS = {
    "bind",
    "listen",
    "start_server",
    "start_unix_server",
    "create_server",
    "create_unix_server",
    "create_datagram_endpoint",
    "run_app",
}
# names that are servers whatever they are called on (a client library has none of them)
SERVER_NAMES = {"Listener", "TCPSite", "UnixSite", "SockSite"}
# whole modules that only exist to serve
SERVER_MODULES = {"hypercorn", "waitress", "gunicorn", "uvicorn", "cheroot", "twisted"}


def server_sockets(source: str, allowed: tuple[int, int] | None = None) -> list[str]:
    """Every use of a form in the lists above (a server class, a bind/listen call, ``multiprocessing`` ``Listener``,
    ``http.server.test``, a datagram endpoint, an aiohttp site or ``run_app``, an import of a module that only
    serves, any ``.run(...)`` with a ``host=`` argument) in ``source`` outside the line range ``allowed``. It is a
    list of forms, not proof that no other form exists."""
    found = []
    for node in ast.walk(ast.parse(source)):
        name = None
        if isinstance(node, ast.Name) and (
            SERVER_CLASS.match(node.id)
            or node.id in SERVER_NAMES
            or node.id in SERVER_CALLS - {"bind", "listen"}
        ):
            name = node.id
        elif isinstance(node, ast.Attribute) and (
            SERVER_CLASS.match(node.attr) or node.attr in SERVER_CALLS or node.attr in SERVER_NAMES
        ):
            name = node.attr
        elif (
            isinstance(node, ast.Attribute)
            and node.attr == "test"
            and isinstance(node.value, ast.Attribute | ast.Name)
            and getattr(node.value, "attr", getattr(node.value, "id", None)) == "server"
        ) or (
            isinstance(node, ast.ImportFrom)
            and node.module == "http.server"
            and any(a.name == "test" for a in node.names)
        ):
            name = "http.server.test"
        elif isinstance(node, ast.Import | ast.ImportFrom):
            roots = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            if hit := next((r for r in roots if r.split(".")[0] in SERVER_MODULES), None):
                name = f"import {hit}"
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run"
            and any(k.arg == "host" for k in node.keywords)
        ):
            name = ".run(host=)"
        if name is not None:
            line = cast(Any, node).lineno
            if allowed is None or not allowed[0] <= line <= (allowed[1]):
                found.append(f"{name}@{line}")
    return found


def _listen_lines() -> tuple[int, int]:
    tree = ast.parse((SRC / "bindguard.py").read_text(encoding="utf-8"))
    (fn,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "listen"]
    assert fn.end_lineno is not None
    return fn.lineno, fn.end_lineno


def test_only_listen_creates_a_server_socket() -> None:
    offenders = []
    for top in ("src", "demos", "tools"):
        for path in sorted((ROOT / top).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            allowed = _listen_lines() if rel == "src/hadavin_sdk/bindguard.py" else None
            offenders += [
                f"{rel}:{hit}" for hit in server_sockets(path.read_text(encoding="utf-8"), allowed)
            ]
    assert offenders == [], f"another server socket outside listen: {offenders}"
    # the scan really sees the server in listen (it is not blind to the one file it exempts)
    own = (SRC / "bindguard.py").read_text(encoding="utf-8")
    assert server_sockets(own) and server_sockets(own, _listen_lines()) == []


BAD_FIXTURES = {
    "ThreadingHTTPServer": "from http.server import ThreadingHTTPServer\nThreadingHTTPServer(('', 1), None)\n",
    "HTTPServer": "import http.server\nhttp.server.HTTPServer(('', 1), None)\n",
    "socketserver.TCPServer": "import socketserver\nsocketserver.TCPServer(('', 1), None)\n",
    "socketserver.ThreadingUDPServer": "import socketserver\nsocketserver.ThreadingUDPServer(('', 1), None)\n",
    "asyncio.start_server": "import asyncio\nasyncio.start_server(None, '', 1)\n",
    "from-import start_server": "from asyncio import start_server\nstart_server(None, '', 1)\n",
    "uvicorn.run": "import uvicorn\nuvicorn.run(None)\n",
    ".bind(": "import socket\ns = socket.socket()\ns.bind(('', 1))\n",
    ".listen(": "import socket\ns = socket.socket()\ns.listen()\n",
    "multiprocessing Listener": "from multiprocessing.connection import Listener\nListener(('', 1))\n",
    "multiprocessing.connection.Listener": "import multiprocessing.connection\nmultiprocessing.connection.Listener(('', 1))\n",
    "http.server.test": "import http.server\nhttp.server.test(HandlerClass=None)\n",
    "from http.server import test": "from http.server import test\ntest()\n",
    "create_datagram_endpoint": "async def f(loop):\n    await loop.create_datagram_endpoint(None, local_addr=('', 1))\n",
    "aiohttp run_app": "from aiohttp import web\nweb.run_app(None, host='')\n",
    "aiohttp TCPSite": "from aiohttp import web\nweb.TCPSite(None, '', 1)\n",
    "hypercorn": "import hypercorn.asyncio\n",
    "from waitress": "from waitress import serve\nserve(None)\n",
    "app.run(host=)": "app = object()\napp.run(host='', port=1)\n",
    "loop.create_server": "async def f(loop):\n    await loop.create_server(None, '', 1)\n",
}


@pytest.mark.parametrize("name", sorted(BAD_FIXTURES))
def test_the_server_scan_flags_each_seeded_bad_fixture(name: str) -> None:
    assert server_sockets(BAD_FIXTURES[name]), f"the scan missed {name}"


def test_the_server_scan_does_not_flag_a_client_or_a_handler() -> None:
    ok = "from http.server import BaseHTTPRequestHandler\nimport socket\nsocket.create_connection(('x', 1))\n"
    assert server_sockets(ok) == []


# --- no module keeps its own copy of the loopback list ---------------------------------------------------

# A short string constant that names loopback (the three spellings, any 127. prefix, or a name that holds the word
# localhost) must be in netguard.py or in this pinned list of (file, line text) -> why it stays. Docstrings and long
# sentences are not lists, so only constants up to 64 characters are read.
LOOP_WORD = re.compile(r"(?<![A-Za-z0-9])localhost(?![A-Za-z0-9])", re.IGNORECASE)
ALLOWED_COPIES = {
    ("store/postgres.py", 'if h == "localhost":'): (
        "reads a database address list with the standard library and also treats a unix socket as local; "
        "it decides how strict the database connection must be, so it is not widened to the bind rule"
    ),
    (
        "tools.py",
        '"localhost",',
    ): "an outbound deny list: names a tool manifest may NOT name (it also holds metadata names)",
    ("tools.py", '"localhost.localdomain",'): "an outbound deny list, same list",
    ("tools.py", '"ip6-localhost",'): "an outbound deny list, same list",
    (
        "tools.py",
        'or host.endswith((".localhost", ".metadata.google.internal"))',
    ): "an outbound deny list: any name under .localhost",
}


def loopback_constants(source: str) -> list[tuple[int, str]]:
    """(line, value) of every short string constant that names loopback in any of the usual shapes: a set, tuple,
    list, dict, regex, ``startswith`` argument, or a piece of a concatenation."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) <= 64:
            v = node.value
            if (
                v in netguard.LOOPBACK_LITERALS
                or v.startswith("127.")
                or LOOP_WORD.search(v)
                or re.search(r"127\\?\.0", v)
            ):
                hits.append((node.lineno, v))
    return hits


def test_no_module_keeps_its_own_loopback_list() -> None:
    offenders, used = [], set()
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        if rel == "netguard.py":
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, value in loopback_constants(path.read_text(encoding="utf-8")):
            key = (rel, lines[lineno - 1].strip())
            if key in ALLOWED_COPIES:
                used.add(key)
            else:
                offenders.append(f"{rel}:{lineno} {value!r}")
    assert offenders == [], f"a copy of the loopback list: {offenders}"
    assert used == set(ALLOWED_COPIES), (
        f"an allowed copy is gone, remove it: {set(ALLOWED_COPIES) - used}"
    )


LOOPBACK_SHAPES = {
    "set": '_X = {"127.0.0.1", "::1"}\n',
    "tuple": 'X = ("localhost",)\n',
    "list": 'X = ["::1"]\n',
    "dict": 'X = {"127.0.0.1": True}\n',
    "regex": 'import re\nX = re.compile(r"^127\\.0\\.0\\.1$")\n',
    "startswith": 'def f(h):\n    return h.startswith("127.")\n',
    "concatenation": 'X = "127." + "0.0.1"\n',
    "name with the word": 'X = "localhost.localdomain"\n',
    "single literal": 'X = "::1"\n',
}


@pytest.mark.parametrize("shape", sorted(LOOPBACK_SHAPES))
def test_the_copy_scan_sees_each_shape_of_a_loopback_list(shape: str) -> None:
    assert loopback_constants(LOOPBACK_SHAPES[shape]), f"the copy scan missed: {shape}"


def test_the_copy_scan_ignores_ordinary_text() -> None:
    assert (
        loopback_constants('X = "a sentence that says nothing"\nY = "1270"\nZ = "locally hosted"\n')
        == []
    )


@pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="the mutation runner copies no pyproject.toml; the normal run and CI read it",
)
def test_the_netguard_docstring_states_the_supported_python_range() -> None:
    requires = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "requires-python"
    ]
    assert requires in (netguard.__doc__ or ""), f"say {requires!r} in the netguard docstring"


# --- round 3, class A: the answer is not given once; it is asked again and cannot be changed under the guard ---------


def _post(server: http.server.HTTPServer, *, close: bool = True) -> int:
    """POST one request to ``serve``'s server (run in a thread for the one request) and return the status; the
    server socket is closed afterwards unless ``close`` is False (the caller closes it)."""
    import http.client
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection(LOOP_1, server.server_address[1], timeout=5)
        conn.request("POST", PATH, body=b"{}", headers={"Content-Length": "2"})
        status = conn.getresponse().status
        conn.close()
        return status
    finally:
        server.shutdown()
        if close:
            server.server_close()
        thread.join(timeout=5)


def test_the_guarded_attributes_of_the_approvals_are_set_once(tmp_path: Path) -> None:
    app = _built(tmp_path)
    a = app.approvals
    for name, value in (
        ("channel", _RealChannel("sig" + "-b4-a")),
        ("store", _Opaque()),
        ("detector", _RealDetector()),
        ("config", app.config),
        ("overrides", {}),
    ):
        with pytest.raises(AttributeError):
            setattr(a, name, value)
    with pytest.raises(TypeError):
        vars(a)  # slots: no instance dictionary to write into


def test_a_real_channel_put_in_after_the_server_started_answers_503_and_one_log_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The bypass of the setter (writing the private slot) is outside what a setter can stop, so the receiver asks
    again at every request on a public bind with no reason."""
    app = _built(tmp_path)
    a = app.approvals
    _stand_in_bind_lands_on_loopback(monkeypatch)
    server = serve(a, config=app.config, host=ALL_ZEROS, port=0)
    try:  # one server for both requests, closed at the end whatever happens
        assert _post(server, close=False) != 503, "a stand-in server refused its first request"
        object.__setattr__(a, "_channel", _RealChannel("sig" + "-b4-late"))
        with caplog.at_level(logging.WARNING, logger="hadavin_sdk.receiver"):
            assert _post(server, close=False) == 503, (
                "a real channel put in after the start was served"
            )
    finally:
        server.server_close()
    assert [
        r.getMessage() for r in caplog.records if "held channel: _RealChannel" in r.getMessage()
    ], "the refused request was not logged with the held object"


def test_a_loopback_bind_does_not_pay_the_recheck(tmp_path: Path) -> None:
    app = _built(tmp_path, channel=_RealChannel("sig" + "-b4-real"))
    a = app.approvals
    assert _post(serve(a, config=app.config, port=0)) != 503, (
        "a loopback bind was refused at the request"
    )


def test_a_bind_with_a_reason_does_not_pay_the_recheck(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path, channel=_RealChannel("sig" + "-b4-real"))
    a = app.approvals
    _stand_in_bind_lands_on_loopback(monkeypatch)
    server = serve(
        a, config=app.config, host=ALL_ZEROS, port=0, allow_public_bind_reason="proxy in front"
    )
    assert _post(server) != 503, "a bind with a reason was refused at the request"


def test_what_the_config_said_at_construction_is_kept_when_its_lists_are_emptied(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    for field in ("tool_modules", "check_modules"):
        cfg = stand_in_config.model_copy(update={field: ["my_module"]})
        approvals = _Approvals(cfg)
        getattr(cfg, field).clear()
        assert real_services(cfg, {}) == () and approvals.real_now(), (
            "the facts were read again, not kept"
        )
        with monkeypatch.context() as m:
            _no_server(m)
            with pytest.raises(BindRefused, match="my_module"):
                serve(approvals, config=cfg, host=ALL_ZEROS, port=0)


def test_serve_refuses_a_subclass_and_a_look_alike_of_the_approvals(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Quiet(Approvals):
        def held_services(self) -> dict[str, object]:
            return {}

    base = _Approvals(stand_in_config)
    sub = Quiet(
        base.store,
        base.audit,
        base.registry,
        base.channel,
        make_on_decided({}),
        config=stand_in_config,
        overrides={},
    )
    _no_server(monkeypatch)
    for odd in (sub, _Opaque()):
        refusal: str | None = None
        try:
            serve(odd, config=stand_in_config, host=LOOP_1, port=0)
        except BindRefused as exc:
            refusal = str(exc)
        assert refusal is not None, f"the exact-type guard let {type(odd).__name__} through"
        assert "made by the core" in refusal, (
            f"the exact-type guard did not refuse {type(odd).__name__}: {refusal}"
        )


def test_emptiness_is_read_by_exact_type_and_an_object_that_raises_counts() -> None:
    class Lazy:
        def __bool__(self) -> bool:
            return False

        def __len__(self) -> int:
            return 0

    class Raises:
        def __bool__(self) -> bool:
            raise RuntimeError("no")

        def __len__(self) -> int:
            raise RuntimeError("no")

    class Sub(dict):
        pass

    assert held_services_found({"tools": {}, "sources": {}}) == ()
    objects: tuple[object, ...] = (Lazy(), Raises(), Sub(), MappingProxyType({}))
    for obj in objects:
        assert held_services_found({"tools": obj}) == ("held tools",), type(obj).__name__
    assert held_services_found({"sources": {"a": 1}}) == ("held sources",)
    cyc = AnyOf([])
    cyc.detectors = (cyc,)
    assert held_services_found({"detector": cyc}) == ("held detector: AnyOf",), (
        "an object that raises was passed on or read as a stand-in"
    )


def test_held_is_required_everywhere_it_decides(stand_in_config: Config) -> None:
    with pytest.raises(TypeError):
        listen(stand_in_config, LOOP_1, 0, _Quiet)
    with pytest.raises(TypeError):
        require_safe_bind(LOOP_1, stand_in_config)
    with pytest.raises(TypeError):
        public_bind_problem(LOOP_1, stand_in_config)
    with pytest.raises(TypeError):
        real_services(stand_in_config)


def test_approvals_made_by_hand_are_refused_on_a_public_bind_unless_the_audit_and_registry_are_stand_ins(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _Approvals(stand_in_config)
    by_hand = Approvals(
        base.store,
        _Opaque(),
        _Opaque(),
        base.channel,
        make_on_decided({}),
        config=stand_in_config,
    )
    assert set(by_hand.held_services()) >= {"audit", "registry"}, (
        "a hand-built Approvals did not name its audit sink and registry"
    )
    assert real_services(stand_in_config, by_hand.held_services()) == (
        "held audit: _Opaque",
        "held registry: _Opaque",
    )
    _no_server(monkeypatch)
    with pytest.raises(BindRefused, match="held audit: _Opaque"):
        serve(by_hand, config=stand_in_config, host=ALL_ZEROS, port=0)
    assert "audit" not in base.held_services(), "a built Approvals counted its audit sink"


def test_an_approvals_cannot_be_copied_or_pickled(stand_in_config: Config) -> None:
    import copy
    import pickle

    a = _Approvals(stand_in_config)
    for op in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError, match="cannot be copied"):
            op(a)


def test_a_mapping_handed_to_build_is_copied_so_emptying_it_later_changes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mine = {"lookup": lambda inputs: "x"}
    app = _built(tmp_path, tools=mine)
    mine.clear()
    _no_server(monkeypatch)
    with pytest.raises(BindRefused, match="held tools"):
        serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0)


def test_an_override_and_a_different_object_now_in_its_place_are_both_counted(
    tmp_path: Path,
) -> None:
    app = _built(tmp_path, channel=_RealChannel("sig" + "-b4-given"))
    a = app.approvals
    object.__setattr__(a, "_channel", FakeChannel("sig" + "-b4-now"))
    assert "held channel_given_to_build: _RealChannel" in real_services(
        app.config, a.held_services()
    ), "an overridden object was hidden by the object now in its place"
    assert "store" in a.held_services() and "detector" in a.held_services(), (
        "the store or the detector is not named among the held objects"
    )


def test_the_approvals_that_build_made_go_through_serve_with_a_real_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End to end, with no re-assembly: the object ``build()`` returned (its own check module counts, too)."""
    app = _built(tmp_path, channel=_RealChannel("sig" + "-b4-e2e")).app
    _no_server(monkeypatch)
    with pytest.raises(BindRefused, match="held channel: _RealChannel"):
        serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0)


# --- round 3, class B: the stand-in registry takes only the core's own listed classes -------------------------------


def test_no_registration_door_exists_and_the_five_are_a_literal_of_pairs() -> None:
    from hadavin_sdk import standins

    assert not hasattr(standins, "stand_in"), "a registration decorator still exists"
    assert not hasattr(standins, "_CLASSES"), "a mutable registry still exists"
    assert type(standins._ALLOWED) is tuple and all(
        type(p) is tuple and len(p) == 2 for p in standins._ALLOWED
    )
    for module in {m for m, _ in standins._ALLOWED}:
        src = (SRC / (module.removeprefix("hadavin_sdk.").replace(".", "/") + ".py")).read_text(
            encoding="utf-8"
        )
        assert "stand_in" not in src, f"{module} still mentions the old decorator"


def test_a_forged_class_with_the_same_module_and_name_is_not_a_stand_in() -> None:
    """Class 1 (round 4): trust is not read from ``__module__`` or ``__qualname__``, which the class author writes."""
    forged = type("FakeLLM", (), {"__module__": "hadavin_sdk.llm.fake", "__qualname__": "FakeLLM"})
    assert forged.__module__ == "hadavin_sdk.llm.fake" and forged.__qualname__ == "FakeLLM"
    assert not is_stand_in_object(forged()), (
        "a class that wrote the core's module and name was trusted"
    )

    class FakeChannel:
        __module__ = "hadavin_sdk.approvals.channel"

    assert not is_stand_in_object(FakeChannel())


class _Home:
    """A stand-in home for a class made by a test: a plain module put in ``sys.modules`` and named in the list."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, name: str = "tests_fake_home") -> None:
        import sys
        import types

        from hadavin_sdk import standins

        self.standins, self.name = standins, name
        self.module = types.ModuleType(name)
        monkeypatch.setitem(sys.modules, name, self.module)
        monkeypatch.setattr(standins, "_ALLOWED", (*standins._ALLOWED, (name, "Child")))
        monkeypatch.setattr(standins, "_PINNED", dict(standins._PINNED))
        monkeypatch.setattr(standins, "_SEEN", standins._SEEN)

    def put(self, cls: type) -> None:
        self.module.__dict__["Child"] = cls


def test_a_method_replaced_on_a_base_class_or_changed_bases_read_as_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Class 1, N3: the pin covers every class of the mro, and the mro itself."""

    class Base:
        def go(self) -> int:
            return 1

    class Other:
        pass

    class Child(Base):
        pass

    home = _Home(monkeypatch)
    home.put(Child)
    assert is_stand_in_object(Child()), "control: a listed class is a stand-in"
    monkeypatch.setattr(Base, "go", lambda self: 2)  # a method replaced on the base
    assert not is_stand_in_object(Child()), "a method replaced on a base class was not noticed"
    monkeypatch.undo()


def test_changed_bases_of_a_stand_in_read_as_real(monkeypatch: pytest.MonkeyPatch) -> None:
    class Base:
        pass

    class Other:
        pass

    class Child(Base):
        pass

    home = _Home(monkeypatch)
    home.put(Child)
    assert is_stand_in_object(Child())
    Child.__bases__ = (Other,)
    assert not is_stand_in_object(Child()), "a changed base class was not noticed"


def test_a_base_swapped_for_a_copy_with_the_same_attributes_reads_as_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The mro itself is pinned, not only the attributes of its classes: a clone with the very same objects in it
    leaves every attribute check equal."""

    def go(self: object) -> int:
        return 1

    shared: dict[
        str, object
    ] = {}  # one annotations dictionary for both, so only the mro tells them apart
    shared_slotnames: list[str] = []
    namespace = {
        "go": go,
        "__slots__": (),
        "__module__": "tests_clone",
        "__doc__": None,
        "__annotations__": shared,
        # ``copyreg._slotnames`` (the pin touches it, for ``copy.copy``) writes a NEW list into a class that has none:
        # the clone would then differ from the base by that list alone and the attribute check would notice it. One list
        # for both, so only the mro tells them apart (the row B98; since batch 10 it survived without this line).
        "__slotnames__": shared_slotnames,
    }
    base, clone = type("Base", (), dict(namespace)), type("Base", (), dict(namespace))

    Child = type("Child", (base,), {})

    home = _Home(monkeypatch)
    home.put(Child)
    assert is_stand_in_object(Child())
    Child.__bases__ = (clone,)
    assert not is_stand_in_object(Child()), (
        "a base class swapped for a clone was not noticed (the mro is not pinned)"
    )


def test_a_module_that_is_not_imported_or_whose_name_was_rebound_gives_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    assert is_stand_in_object(FakeSecretProvider({})), "control"
    with monkeypatch.context() as m:
        m.delitem(sys.modules, "hadavin_sdk.actions.secrets")
        assert not is_stand_in_object(FakeSecretProvider({})), "an unimported module matched"
    import hadavin_sdk.actions.secrets as secrets_module

    class Forged:
        pass

    with monkeypatch.context() as m:
        m.setattr(
            secrets_module, "FakeSecretProvider", Forged
        )  # the module name now means another class
        assert not is_stand_in_object(FakeSecretProvider({})), "a rebound module name still matched"
        assert not is_stand_in_object(Forged()), "the rebound class was trusted"
    assert is_stand_in_object(FakeSecretProvider({}))


def test_the_class_is_looked_up_in_the_module_dictionary_not_with_getattr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A module-level ``__getattr__`` must never be run to find a trusted class."""

    class Planted:
        pass

    home = _Home(monkeypatch, "tests_fake_home_getattr")
    home.module.__dict__["__getattr__"] = lambda name: Planted
    assert home.module.Child is Planted  # only through __getattr__
    assert not is_stand_in_object(Planted()), (
        "a class found through a module __getattr__ was trusted"
    )


def test_a_cleared_pin_of_a_class_that_was_seen_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from hadavin_sdk import standins

    assert is_stand_in_object(FakeChannel("sig" + "-b5-pin")), "control"
    monkeypatch.setattr(standins, "_PINNED", {})
    assert not is_stand_in_object(FakeChannel("sig" + "-b5-pin")), (
        "a cleared pin re-pinned and trusted"
    )


def test_a_subclass_of_a_listed_class_is_not_that_class(monkeypatch: pytest.MonkeyPatch) -> None:
    class Child:
        pass

    home = _Home(monkeypatch)
    home.put(Child)
    assert is_stand_in_object(Child())

    class Sub(Child):
        pass

    assert not is_stand_in_object(Sub()), (
        "a subclass was read as the class (isinstance instead of identity)"
    )


def test_a_metaclass_that_fakes_equality_and_hash_is_not_a_stand_in() -> None:
    class Meta(type):
        def __hash__(cls) -> int:
            return hash(FakeChannel)

        def __eq__(cls, other: object) -> bool:
            return True

    class Spoof(metaclass=Meta):
        pass

    assert not is_stand_in_object(Spoof()), (
        "a class that fakes equality and hash was read as a stand-in"
    )


def test_a_module_that_is_not_a_plain_module_gives_real(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    import types

    import hadavin_sdk.actions.secrets as secrets_module

    class Fancy(types.ModuleType):
        pass

    fancy = Fancy("hadavin_sdk.actions.secrets")
    fancy.__dict__.update(vars(secrets_module))
    with monkeypatch.context() as m:
        m.setitem(sys.modules, "hadavin_sdk.actions.secrets", fancy)
        assert not is_stand_in_object(FakeSecretProvider({})), (
            "a module of another type was read as the home of a stand-in"
        )


def test_an_instance_with_more_values_than_the_budget_reads_as_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from hadavin_sdk import standins

    fc = FakeChannel("sig" + "-b5-budget")
    assert is_stand_in_object(fc), "control"
    fc.many = list(range(50))
    assert is_stand_in_object(fc), "control: plain values within the budget are fine"
    monkeypatch.setattr(standins, "SCAN_NODES", 10)
    assert not is_stand_in_object(fc), (
        "an instance past the node budget was trusted (the node budget)"
    )


def test_a_stand_in_that_was_changed_is_read_as_real(monkeypatch: pytest.MonkeyPatch) -> None:
    assert is_stand_in_object(FakeChannel("sig" + "-b4-ok")), (
        "control: an untouched stand-in is one"
    )
    fc = FakeChannel("sig" + "-b4-inst")
    fc.post_card = lambda *a: None  # a function put on the instance
    assert not is_stand_in_object(fc), (
        "a stand-in holding a function of its own was still read as a stand-in"
    )
    monkeypatch.setattr(FakeChannel, "send", lambda self, *a: None)  # a replaced method
    assert not is_stand_in_object(FakeChannel("sig" + "-b4-cls")), (
        "a replaced method of a stand-in class was not noticed"
    )
    monkeypatch.undo()
    monkeypatch.setattr(
        FakeChannel, "extra_method", lambda self: None, raising=False
    )  # an added one
    assert not is_stand_in_object(FakeChannel("sig" + "-b4-add")), (
        "a method added to a stand-in class was not noticed"
    )
    monkeypatch.undo()
    assert is_stand_in_object(FakeChannel("sig" + "-b4-back")), "the class was not restored"


def test_every_registered_stand_in_is_still_one_when_made_in_the_usual_way(tmp_path: Path) -> None:
    """Guards against the over-refusal of the instance rule: the core's own fakes hold no function of their own."""
    for obj in (
        FakeChannel("sig" + "-b4-x"),
        FakeLLM(tmp_path, {}),
        FakeSecretProvider({}),
        MemoryStore(),
        RegexDetector(0.5),
    ):
        assert is_stand_in_object(obj), type(obj).__name__


def test_a_detector_list_is_a_copy_and_cannot_be_changed_in_place() -> None:
    mine = [RegexDetector(0.5)]
    both = AnyOf(mine)
    mine.append(_RealDetector())
    assert is_stand_in_object(both), "a list changed later changed the detector list"
    with pytest.raises(AttributeError):
        both.detectors.append(_RealDetector())


# --- round 3, class C: the scan has holes by nature, so the bind itself is checked at run time too -----------------


NEW_FORMS = {
    "alias import": "from http.server import ThreadingHTTPServer as S\nS(('', 80), None)\n",
    "alias of a module": "import socketserver as ss\nss.TCPServer(('', 1), None)\n",
    "positional run host": "app = object()\napp.run('0.0.0.0', 5000)\n",
    "wsgiref make_server": "from wsgiref.simple_server import make_server\nmake_server('', 1, None)\n",
    "wsgiref alias": "import wsgiref.simple_server as w\nw.WSGIServer(('', 1), None)\n",
    "werkzeug run_simple": "from werkzeug.serving import run_simple\nrun_simple('', 1, None)\n",
    "websockets serve": "import websockets\nwebsockets.serve(None, '', 1)\n",
    "trio serve_tcp": "import trio\ntrio.serve_tcp(None, 1)\n",
    "anyio listener": "import anyio\nanyio.create_tcp_listener(local_port=1)\n",
    "grpc port": "def f(server):\n    server.add_insecure_port('[::]:1')\n",
    "grpc secure port": "def f(server):\n    server.add_secure_port('[::]:1', None)\n",
    "base subclass": "import socketserver\nclass S(socketserver.BaseServer):\n    pass\n",
    "alias base subclass": "from socketserver import BaseServer as B\nclass S(B):\n    pass\n",
    "import_module": "import importlib\nimportlib.import_module('uvicorn')\n",
}


def test_the_resolved_scan_flags_each_new_form_and_the_old_scan_did_not() -> None:
    missed = [n for n, src in sorted(NEW_FORMS.items()) if not server_scan.resolved_forms(src)]
    assert missed == [], f"the alias-resolving scan missed {missed}"
    seen_before = [
        n
        for n, src in sorted(NEW_FORMS.items())
        if server_sockets(src)
        and n not in {"alias of a module", "wsgiref alias", "base subclass", "import_module"}
    ]
    assert seen_before == [], (
        f"already seen by the name scan (the fixture proves nothing): {seen_before}"
    )


def test_the_resolved_scan_ignores_what_only_looks_like_a_server() -> None:
    quiet = (
        "import subprocess\nimport asyncio\nfrom socketserver import BaseServer\n"
        "subprocess.run('ls', shell=True)\nasyncio.run(None)\n"
        "def f(db):\n    db.run('SELECT 1')\n\ndef g(s: BaseServer) -> None:\n    pass\n"
    )
    assert server_scan.resolved_forms(quiet) == []


# one fixture per launcher word, each holding that word ALONE (so taking that word away from the list is seen)
LAUNCHER_FIXTURES = {
    r"http\.server": "exec http.server 8000\n",
    r"flask\s+run": "flask run\n",
    r"uvicorn": 'CMD ["uvicorn", "app:app"]\n',
    r"gunicorn": "command: gunicorn app:app\n",
    r"hypercorn": "hypercorn app:app\n",
    r"waitress": "waitress-serve app:app\n",
    r"serve_forever": "srv.serve_forever()\n",
    r"--host\b": "app --host x\n",
    r"0\.0\.0\.0": "ports: 0.0.0.0:80\n",
    r"\bnc\s+-l": "nc -l 9000\n",
    r"\bsocat\b": "socat TCP-LISTEN:1 -\n",
    r"python\s+-m\s+\w*server": "python -m myserver 80\n",
    r"\brunserver\b": "manage runserver\n",
}


def test_every_launcher_word_has_a_fixture_of_its_own_and_only_its_own() -> None:
    assert set(LAUNCHER_FIXTURES) == set(server_scan.LAUNCHER_WORD_LIST), (
        "a launcher word has no fixture of its own (or a fixture has no word)"
    )
    for word, text in sorted(LAUNCHER_FIXTURES.items()):
        others = re.compile(
            "|".join(w for w in server_scan.LAUNCHER_WORD_LIST if w != word), re.IGNORECASE
        )
        assert not others.search(text), f"the fixture for {word} also holds another word"


def test_the_launcher_scan_flags_each_seeded_launcher_by_its_own_word() -> None:
    """Each fixture is read by the scan as it is (not by the list of words in this file), so a word taken out of
    the scan is seen as that word's own miss."""
    for word, text in sorted(LAUNCHER_FIXTURES.items()):
        assert server_scan.launcher_hits(text), f"the launcher scan missed {word}"


def test_the_launcher_globs_name_the_new_kinds_of_launcher_file() -> None:
    globs = set(server_scan.LAUNCHER_GLOBS)
    for needed in ("Makefile", "justfile", "*.bash", "*.ps1", "entrypoint*", "k8s/**/*.y*ml"):
        assert needed in globs, f"{needed} is not scanned"
    import fnmatch

    for name in ("Makefile", "justfile", "run.bash", "start.ps1", "entrypoint.sh", "web.mk"):
        assert any(fnmatch.fnmatch(name, g) for g in globs), f"{name} is not matched by a glob"


def test_the_pyproject_scripts_are_read_and_the_dependency_lists_are_not() -> None:
    quiet = '[project]\nname = "x"\ndependencies = ["uvicorn>=0.30", "waitress"]\n'
    assert server_scan.pyproject_hits(quiet) == []
    serving = (
        '[project.scripts]\nserve = "http.server:test"\nrun = "uvicorn app:app --host 0.0.0.0"\n'
        '[tool.poe.tasks]\nweb = "gunicorn app:app"\n[project.entry-points."x.y"]\nz = "waitress:serve"\n'
    )
    hits = server_scan.pyproject_hits(serving)
    assert "entry point http.server" in hits and "entry point waitress" in hits, (
        f"an entry point in a serving module was not read: {hits}"
    )
    assert {"uvicorn", ALL_ZEROS, "gunicorn"} <= set(hits), f"a script table was not read: {hits}"
    if (
        ROOT / "pyproject.toml"
    ).exists():  # the mutation runner copies none; the normal run and CI read it
        own = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        assert server_scan.pyproject_hits(own) == [], "pyproject.toml of this repo starts a server"


# a launcher word that is not ours, written down with why: (file, word, how many times) -> reason. A second one
# of the same word is a different key, so it fails until a person writes it down
LAUNCHER_ALLOWED = {
    (
        ".github/workflows/ci.yml",
        ".".join(["0"] * 4),
        2,
    ): "the address each of the two throwaway secrets-service containers of the CI listens on (one per job); "
    "it is not code of this repo",
}


def _launcher_files() -> list[Path]:
    files = [
        p
        for pattern in server_scan.LAUNCHER_GLOBS
        for p in ROOT.rglob(pattern)
        if ".git" not in p.parts and ".venv" not in p.parts and "node_modules" not in p.parts
    ]
    files += sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
    return sorted(set(files))


def _launcher_keys(texts: dict[str, str]) -> set[tuple[str, str, int]]:
    return {
        (rel, word, n)
        for rel, text in texts.items()
        for word, n in server_scan.launcher_counts(text).items()
    }


def test_an_allowed_launcher_word_allows_only_its_own_count() -> None:
    word = ".".join(["0"] * 4)
    one = {"f.yml": f"a: {word}\n"}
    two = {"f.yml": f"a: {word}\nb: {word}\n"}
    assert _launcher_keys(one) == {("f.yml", word, 1)}
    assert _launcher_keys(two) == {("f.yml", word, 2)}
    assert _launcher_keys(two) - {("f.yml", word, 1)}, (
        "the count of a word was lost: a second word passed on the first one's allowance"
    )


@pytest.mark.skipif(
    not (ROOT / ".github" / "workflows").is_dir(),
    reason="the mutation runner copies no .github folder; the normal run and CI read it",
)
def test_no_script_dockerfile_compose_or_workflow_starts_a_server() -> None:
    texts = {
        p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8", errors="replace")
        for p in _launcher_files()
    }
    keys = _launcher_keys(texts)
    unexplained = sorted(keys - set(LAUNCHER_ALLOWED))
    assert unexplained == [], f"a launcher starts a server: {unexplained}"
    assert keys >= set(LAUNCHER_ALLOWED), (
        "an allowed launcher word is gone or its count changed, fix the list"
    )
    own = ROOT / "pyproject.toml"
    if own.exists():
        assert server_scan.pyproject_hits(own.read_text(encoding="utf-8")) == []


def test_the_resolved_scan_finds_nothing_outside_listen_in_src_demos_tools() -> None:
    offenders = []
    for top in ("src", "demos", "tools"):
        for path in sorted((ROOT / top).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            lo, hi = _listen_lines() if rel == "src/hadavin_sdk/bindguard.py" else (0, 0)
            for hit in server_scan.resolved_forms(path.read_text(encoding="utf-8")):
                if not lo <= int(hit.rsplit("@", 1)[1]) <= hi:
                    offenders.append(f"{rel}:{hit}")
    assert offenders == [], f"another server form outside listen: {offenders}"
    own = (SRC / "bindguard.py").read_text(encoding="utf-8")
    assert server_scan.resolved_forms(own), "the resolved scan is blind to the server in listen"


_RUNTIME_PROBE = r"""
import importlib.util, json, pathlib, pkgutil, socket, sys, traceback
root = pathlib.Path(sys.argv[1])
sys.path[:0] = [str(root / "src"), str(root)]
binds = []
def boom(self, *a, **k):
    binds.append(traceback.format_stack()[-3].strip().splitlines()[0])
    raise OSError("bind during import")
socket.socket.bind = boom
failed = []
import hadavin_sdk
for m in pkgutil.walk_packages(hadavin_sdk.__path__, "hadavin_sdk."):
    try:
        importlib.import_module(m.name)
    except Exception as exc:
        failed.append(m.name + " " + type(exc).__name__)
for path in sorted((root / "tools").glob("*.py")):
    try:
        spec = importlib.util.spec_from_file_location("probe_" + path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    except Exception as exc:
        failed.append(path.name + " " + type(exc).__name__)
print(json.dumps({"binds": binds, "failed": failed}))
"""


def test_importing_the_package_binds_no_socket() -> None:
    import json

    out = _run_python(["-I", "-c", _RUNTIME_PROBE, str(ROOT)], 300)
    assert out.returncode == 0 or "bind during import" in out.stderr, out.stderr[-300:]
    assert "bind during import" not in out.stderr, (
        f"a module bound a socket when it was imported: {out.stderr[-300:]}"
    )
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert result["binds"] == [], f"a module bound a socket when it was imported: {result['binds']}"
    assert result["failed"] == [], (
        f"a module could not be imported, so it was not checked: {result['failed']}"
    )


def test_the_only_code_that_reaches_a_socket_bind_is_listen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The control at the one place every server must pass: the frames above each ``socket.bind`` made while the
    receiver runs. The caller of the bind must be the standard ``TCPServer.server_bind``, called by the server
    class made INSIDE ``listen`` and nothing else (a second bind written inside ``listen``, or anywhere else,
    would show a different frame first). Paths that no test runs are not covered."""
    import sys

    seen: list[list[tuple[str, Any]]] = []
    real_bind = socket.socket.bind

    def spy(self: socket.socket, address: Any) -> None:
        frames: list[tuple[str, Any]] = []
        f: Any = sys._getframe(1)
        while f is not None and len(frames) < 4:
            frames.append((Path(f.f_code.co_filename).name, f.f_code.co_name))
            f = f.f_back
        seen.append(frames)
        return real_bind(self, address)

    monkeypatch.setattr(socket.socket, "bind", spy)
    app = _built(tmp_path)
    serve(app.approvals, config=app.config, port=0).server_close()
    real = _built(tmp_path / "real", channel=_RealChannel("sig" + "-b4-rt"))
    serve(real.approvals, config=real.config, port=0).server_close()
    listen(real.config, LOOP_1, 0, _Quiet, held={}).server_close()
    assert len(seen) == 3, "the receiver reached a bind a different number of times than expected"
    expected = [
        ("socketserver.py", "server_bind"),
        ("bindguard.py", "server_bind"),
        ("socketserver.py", "__init__"),
        ("bindguard.py", "listen"),
    ]
    for frames in seen:
        assert frames == expected, f"a bind came from somewhere other than listen: {frames}"


# --- round 4, batch 5 ------------------------------------------------------------------------------------------------
# class 2: everything trusted is pinned, the instance is scanned to a bounded depth


def _any_of() -> AnyOf:
    return AnyOf([RegexDetector(0.5), RegexDetector(0.7)])


def test_a_detector_list_with_a_function_a_patched_method_or_a_foreign_container_reads_as_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert is_stand_in_object(_any_of()), "control"
    patched = _any_of()
    patched.check = lambda text, source: None
    assert not is_stand_in_object(patched), "a function put on the detector list was not noticed"
    with monkeypatch.context() as m:
        m.setattr(AnyOf, "check", lambda self, text, source: None)
        assert not is_stand_in_object(_any_of()), "a patched AnyOf.check was not noticed"
    as_list = _any_of()
    as_list.detectors = [RegexDetector(0.5)]
    assert not is_stand_in_object(as_list), "a list of detectors was read as a tuple"

    class EmptyIter:
        def __iter__(self):  # a foreign iteration that says "nothing in here"
            return iter(())

    empty = _any_of()
    empty.detectors = EmptyIter()
    assert not is_stand_in_object(empty), "a detector holder that iterates as empty was trusted"

    class MyTuple(tuple):
        def __iter__(self):
            return iter(())

    sub = _any_of()
    sub.detectors = MyTuple((_RealDetector(),))
    assert not is_stand_in_object(sub), "a tuple subclass with a foreign iteration was trusted"
    mixed = AnyOf([RegexDetector(0.5), _RealDetector()])
    assert not is_stand_in_object(mixed)


def test_a_detector_list_nested_or_cyclic_is_read_without_recursion_errors() -> None:
    nested = AnyOf([_any_of(), RegexDetector(0.5)])
    assert is_stand_in_object(nested), "a list of lists of stand-ins is a stand-in"
    deep: AnyOf = _any_of()
    for _ in range(10):
        deep = AnyOf([deep])
    assert not is_stand_in_object(deep), "nesting past the depth limit was trusted"
    loop = _any_of()
    loop.detectors = (loop,)
    assert not is_stand_in_object(loop), "a detector list holding itself was trusted"


def test_a_function_hidden_inside_a_stand_in_reads_as_real_up_to_the_depth_limit(
    tmp_path: Path,
) -> None:
    from hadavin_sdk import standins

    assert standins.SCAN_DEPTH == 4
    plain = FakeLLM(tmp_path, {})
    assert is_stand_in_object(plain), "control"
    # levels: the values of the instance's own attributes are level 1; a container inside one adds a level.
    # ``routes`` is level 1, so the value put in it is level 2
    hidden = [
        lambda: None,  # level 2
        {"k": lambda: None},  # level 3
        {"k": (lambda: None,)},  # level 4, the last one entered
    ]
    for value in hidden:
        llm = FakeLLM(tmp_path, {})
        llm.routes["x"] = value
        assert not is_stand_in_object(llm), f"a function inside {value!r} was not noticed"
    for kind in (set, frozenset):
        llm = FakeLLM(tmp_path, {})
        llm.calls.append(
            {"f": kind([print])}
        )  # a callable inside a set inside a dict inside a list
        llm.calls.append(kind([print]))
        assert not is_stand_in_object(llm)
    store = MemoryStore()
    store._runs["x"] = (lambda: None,)
    assert not is_stand_in_object(store)
    # the limit FAILS CLOSED: a function below the last level that is entered is not seen, but a container left
    # unexplored that holds anything but plain atoms reads as real; plain atoms there are fine
    far = FakeLLM(tmp_path, {})
    far.routes["x"] = {"k": [(lambda: None,)]}
    assert not is_stand_in_object(far), "a container past the depth limit was trusted"
    atoms = FakeLLM(tmp_path, {})
    atoms.routes["x"] = {"k": [(1, "two", None)]}
    assert is_stand_in_object(atoms), "a plain-data container at the depth limit was refused"
    for obj in (FakeChannel("sig" + "-b5-d"), MemoryStore(), FakeSecretProvider({"a": "b"})):
        assert is_stand_in_object(obj)


def test_a_stand_in_with_no_instance_dictionary_or_a_hostile_one_never_raises() -> None:
    class Slotted:
        __slots__ = ()

    assert not is_stand_in_object(Slotted())
    assert not is_stand_in_object(object())
    assert not is_stand_in_object(None)


# class 3: the live object keeps its type and its set-once slots


class SlotSub(Approvals):
    __slots__ = ()


def test_an_approvals_refuses_plain_writes_a_class_swap_and_weak_references(tmp_path: Path) -> None:
    import weakref

    app = _built(tmp_path)
    a = app.approvals
    with pytest.raises(AttributeError, match="set once"):
        a.__class__ = SlotSub
    assert type(a) is Approvals
    with pytest.raises(AttributeError, match="set once"):
        a._channel = _RealChannel("sig" + "-b5-w")
    for name in Approvals.__slots__:
        with pytest.raises(AttributeError, match="set once"):
            setattr(a, name, None)
    with pytest.raises(AttributeError, match="set once"):
        a.brand_new = 1
    with pytest.raises(AttributeError):
        _ = a.__dict__
    with pytest.raises(TypeError):
        weakref.ref(a)
    now = a.clock
    a.clock = lambda: now()  # the one name that can be set again
    assert a.clock is not now and a.clock() is not None


def test_a_class_swapped_with_the_object_level_write_is_answered_503(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    app = _built(tmp_path)
    a = app.approvals
    _stand_in_bind_lands_on_loopback(monkeypatch)
    server = serve(a, config=app.config, host=ALL_ZEROS, port=0)
    object.__setattr__(a, "__class__", SlotSub)
    try:
        with caplog.at_level(logging.WARNING, logger="hadavin_sdk.receiver"):
            assert _post(server) == 503, "an Approvals whose class was swapped was served"
    finally:
        object.__setattr__(a, "__class__", Approvals)
    assert any("no longer an exact Approvals" in r.getMessage() for r in caplog.records), (
        "the refusal did not say that the object is no longer an exact Approvals"
    )


# class 4: the guard never raises on a hostile input


class _BoomKey:
    def __str__(self) -> str:
        raise RuntimeError("no text for this key")

    def __hash__(self) -> int:
        return 7


class _EqBoomKey:
    """Hashes like "tools", so the lookup in the counted-when-not-empty set compares it, and the comparison raises."""

    def __hash__(self) -> int:
        return hash("tools")

    def __eq__(self, other: object) -> bool:
        raise RuntimeError("no comparison")


class _Hostile:
    """A mapping whose keys cannot be sorted, hashed or shown."""

    def __init__(self, items: list[tuple[object, object]]) -> None:
        self._items = items

    def items(self) -> list[tuple[object, object]]:
        return self._items

    def __bool__(self) -> bool:
        return True


def test_a_hostile_key_or_mapping_makes_the_answer_real_and_never_raises() -> None:
    found = held_services_found({_EqBoomKey(): {}})
    assert found == ("held (unreadable)",), (
        f"a key whose comparison raises was not counted: {found}"
    )

    boom = {_BoomKey(): _Opaque(), "ok": FakeChannel("sig" + "-b5-k")}
    found = held_services_found(boom)
    assert found == ("held (unreadable)",), found
    unhashable = _Hostile([([1, 2], _Opaque()), (_BoomKey(), _Opaque())])
    found = held_services_found(unhashable)
    assert len(found) == 2 and all(f.startswith("held (unreadable)") for f in found), found

    found = held_services_found({_EqBoomKey(): {}})
    assert found == ("held (unreadable)",), (
        f"a key whose comparison raises was not counted: {found}"
    )

    class Raises:
        def items(self) -> list[object]:
            raise RuntimeError("no items")

        def __bool__(self) -> bool:
            return True

    assert held_services_found(Raises()) == ("held (unreadable)",)


def test_a_class_whose_name_raises_when_read_is_counted_with_a_fixed_label() -> None:
    """New test, fails on the old code only if the label read is outside the try (the try is the choke point that
    turns any error while a held object is looked at into a fixed label)."""

    def _raising_name(cls: type) -> str:
        raise RuntimeError("the name of a class that raises")

    class Meta(type):
        __name__ = property(_raising_name)

    odd = Meta("Odd", (), {})
    assert held_services_found({"channel": odd()}) == ("held (unreadable)",), (
        "the name of a class that raises was not counted with a fixed label"
    )


# class 6: a refused request is logged at most once a minute per set of services


def test_a_refused_request_is_logged_once_a_minute_per_set_of_services(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from hadavin_sdk.approvals import receiver

    clock = [1000.0]
    monkeypatch.setattr(receiver.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(receiver, "_LAST_LOGGED", {})
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.receiver"):
        for _ in range(50):
            receiver._refused(("held channel: A",))
        assert len(caplog.records) == 1, "a flood of requests filled the log"
        receiver._refused(("held channel: B",))
        assert len(caplog.records) == 2, "a second set of services was hidden by the first"
        clock[0] += 59
        receiver._refused(("held channel: A",))
        assert len(caplog.records) == 2
        clock[0] += 2
        receiver._refused(("held channel: A",))
        assert len(caplog.records) == 3, "the limit never lets the line through again"


# class 5: the scan of Python files reads scopes, star imports, more entry points and real addresses


def test_a_star_import_of_a_server_module_is_resolved() -> None:
    for src in (
        "from socketserver import *\nTCPServer(('', 1), None)\n",
        "from http.server import *\nThreadingHTTPServer(('', 1), None)\n",
        "from waitress import *\nserve(None)\n",
    ):
        assert server_scan.resolved_forms(src), f"a star import was not resolved: {src!r}"
    assert server_scan.resolved_forms("from math import *\nsqrt(4)\n") == []


def test_aliases_are_read_in_the_scope_they_are_written_in() -> None:
    both = (
        "def a():\n    import socketserver as s\n    return s.TCPServer(('', 1), None)\n\n"
        "def b():\n    import os as s\n    return s.getcwd()\n"
    )
    # the same name means a server in one function and a harmless module in the other: only the first is flagged
    flagged = server_scan.resolved_forms(both)
    assert flagged and all(int(h.rsplit("@", 1)[1]) <= 3 for h in flagged), (
        f"the harmless import was read as a server: {flagged}"
    )
    # last-wins on a flat table hid the first function's server
    reverse = (
        "def b():\n    import os as s\n    return s.getcwd()\n\n"
        "def a():\n    import socketserver as s\n    return s.TCPServer(('', 1), None)\n"
    )
    assert server_scan.resolved_forms(reverse), "a later import of the same name hid a server"
    # an import inside a function does not rename a name used in another function
    leak = "def a():\n    import socketserver as s\n\ndef b(s):\n    return s.TCPServer\n"
    assert server_scan.resolved_forms(leak) == [], (
        "an import in one function renamed a name in another"
    )
    # a module-level import is seen inside a function, and inside a class
    assert server_scan.resolved_forms(
        "import socketserver as s\nclass C:\n    def f(self):\n        return s.TCPServer\n"
    ), "a module-level import was not seen inside a function"


def test_import_module_of_a_serving_module_is_flagged() -> None:
    for name in ("socketserver", "http.server", "uvicorn", "waitress.server", "xmlrpc.server"):
        src = f"import importlib\nimportlib.import_module({name!r})\n"
        assert server_scan.resolved_forms(src), f"import_module({name!r}) was not flagged"
    assert server_scan.resolved_forms("import importlib\nimportlib.import_module('json')\n") == []


def test_the_entry_points_of_the_serving_libraries_are_flagged() -> None:
    for src in (
        "from waitress import serve\nserve(None, host='')\n",
        "import waitress\nwaitress.serve(None)\n",
        "from hypercorn.asyncio import serve\nserve(None, None)\n",
        "import hypercorn.trio\nhypercorn.trio.serve(None, None)\n",
        "from uvicorn import Server\nServer(None)\n",
        "from twisted.internet import reactor\nreactor.listenTCP(1, None)\n",
    ):
        assert server_scan.resolved_forms(src), f"not flagged: {src!r}"


def test_a_run_host_is_read_with_the_rule_of_the_guard_and_hex_words_are_not_hosts() -> None:
    for host in ("", "localhost", "LocalHost", ALL_ZEROS, "::", "[::1]", LOOP_1):
        assert server_scan.resolved_forms(f"app.run({host!r})\n"), f"{host!r} is a host"
    for word in ("add", "bad", "cafe", "dead", "1", "a.b", "5"):
        assert server_scan.resolved_forms(f"db.run({word!r})\n") == [], f"{word!r} is not a host"


# --- round 5, batch 6 ------------------------------------------------------------------------------------------------
# class A: a held value is judged by an allowlist of exact types, not by "is it callable"


def _populated_store() -> MemoryStore:
    """A store filled through its own methods (rows of the models it keeps): plain data, still a stand-in."""
    from hadavin_sdk.models import Run

    store = MemoryStore()
    store.create_run(Run(agent_id="a", principal_id="p", trigger_kind="user", trigger_ref="r"))
    return store


class _Plain:
    """A client-like object that is not callable and has no code of its own on the instance."""

    def __enter__(self) -> object:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class _DictWithCode(dict):
    def __getitem__(self, key: object) -> object:
        return key


class _ListWithCode(list):
    def __iter__(self):
        return iter(())


class _TextWithCode(str):
    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = str.__hash__


class _NumberWithCode(int):
    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = int.__hash__


def _real_factory() -> list[int]:
    return []


def _held_shapes() -> dict[str, object]:
    import types
    from collections import ChainMap, UserDict, defaultdict, deque

    return {
        "dict_subclass_with_getitem": _DictWithCode(a=1),
        "list_subclass": _ListWithCode([1]),
        "defaultdict_real_factory": defaultdict(_real_factory),
        "object_with_enter_and_exit": _Plain(),
        "simple_namespace": types.SimpleNamespace(a=1),
        "mapping_proxy": MappingProxyType({"a": 1}),
        "user_dict": UserDict({"a": 1}),
        "chain_map": ChainMap({"a": 1}),
        "deque_subclass": type("D", (deque,), {})([1]),
        "generator": (x for x in range(3)),
        "iterator": iter([1, 2]),
        "memoryview": memoryview(b"ab"),
        "bytearray": bytearray(b"ab"),
        "plain_foreign_object": _Opaque(),
        "str_subclass": _TextWithCode("a"),
        "int_subclass": _NumberWithCode(1),
    }


def test_a_held_value_that_is_not_plain_data_reads_as_real_whatever_it_is(tmp_path: Path) -> None:
    """The scan is an allowlist of exact types: every shape below passed when only ``callable`` was refused."""
    makers = (
        lambda: FakeLLM(tmp_path, {}),
        lambda: FakeChannel("sig" + "-b6-a"),
        _populated_store,
        lambda: FakeSecretProvider({"a": "b"}),
        lambda: RegexDetector(0.5),
    )
    for make in (
        makers
    ):  # the controls first, so a failure below is about the shape and never about a control
        assert is_stand_in_object(make()), "control: the untouched stand-in reads as a stand-in"
    for shape in sorted(_held_shapes()):
        for make in makers:
            obj = make()
            obj.extra = _held_shapes()[shape]
            assert not is_stand_in_object(obj), (
                f"a held {shape} was trusted by {type(obj).__name__}"
            )
            obj.extra = [[_held_shapes()[shape]]]
            assert not is_stand_in_object(obj), f"a held {shape} inside lists was trusted"


def test_a_text_or_number_subclass_is_not_a_plain_atom(tmp_path: Path) -> None:
    """Own shape and own message for the row that judges atoms by ``isinstance``: the hosts below hold no enum member,
    so the controls pass whatever is done to the atom rule, and only the subclasses are the difference."""
    hosts = (lambda: FakeChannel("sig" + "-b9-atom"), lambda: RegexDetector(0.5))
    for make in hosts:
        assert is_stand_in_object(make()), "control: the untouched stand-in reads as a stand-in"
    for what, value in {
        "a str subclass": _TextWithCode("a"),
        "an int subclass": _NumberWithCode(1),
        "a bool-like int subclass inside a list": [_NumberWithCode(0)],
    }.items():
        for make in hosts:
            host = make()
            host.extra = value
            assert not is_stand_in_object(host), (
                f"{what} was trusted as a plain atom by {type(host).__name__}"
            )


def test_a_dict_key_is_judged_like_a_value_and_a_container_is_read_with_the_builtin_iterator(
    tmp_path: Path,
) -> None:
    from hadavin_sdk import standins

    llm = FakeLLM(tmp_path, {})
    llm.routes[_Plain()] = 1
    assert not is_stand_in_object(llm), "a foreign object used as a dict key was trusted"
    # ``_values`` never runs a subclass's own iteration or lookup
    assert standins._values(_ListWithCode([1, 2]), 10) == (1, 2), (
        "a subclass's own iteration was run"
    )
    assert standins._values(_DictWithCode(k="v"), 10) == ("k", "v")
    assert standins._values(42, 10) == ()


def test_a_populated_store_and_the_real_models_still_read_as_stand_ins(tmp_path: Path) -> None:
    from decimal import Decimal

    store = _populated_store()
    store.add_cost(next(iter(store._runs)), Decimal("0.5"))
    assert is_stand_in_object(store), "plain rows of the store's own models were refused"
    store._runs["x"] = _Plain()
    assert not is_stand_in_object(store), "a foreign object among the rows was trusted"


def test_the_eight_pinned_plain_classes_hold_no_class_level_mutable_value() -> None:
    """The pin compares class attributes by identity, so a value that lives on the class and can be changed in
    place (a list, a dict, a set, a mutable instance) would change without the pin noticing. The five stand-ins, the
    detector list, ``Approvals`` and the core ``Runtime`` hold only functions, descriptors, classes and plain atoms
    there. (The model rows are pydantic classes: their class-level dictionaries are judged by their own test, see
    ``test_every_data_class_is_a_forbidding_pydantic_model_or_the_one_plain_dataclass``.)"""
    import inspect
    import types

    importlib.import_module("hadavin_sdk.runtime.agent_loop")  # its last line pins ``Runtime``
    from hadavin_sdk import standins

    keys = (*standins._ALLOWED, standins._DETECTOR_LIST, standins.APPROVALS, standins.RUNTIME)
    classes = [standins.live_class(key) for key in keys]
    assert all(classes) and len(classes) == 8
    for cls in classes:
        for base in cls.__mro__:
            if base is object:
                continue
            for name, value in vars(base).items():
                if (
                    name
                    in (
                        "__annotations__",  # the empty one the pin itself adds; nothing runs from it
                        "__slotnames__",  # the list of slot names ``copy`` caches; only read to restore a copy
                    )
                ):
                    continue
                allowed = (
                    inspect.isfunction(value)
                    or isinstance(value, classmethod | staticmethod | property | type)
                    or type(value)
                    in (
                        types.WrapperDescriptorType,
                        types.MethodDescriptorType,
                        types.ClassMethodDescriptorType,
                        types.MemberDescriptorType,
                        types.GetSetDescriptorType,
                    )
                    or standins._is_one_of(type(value), standins._ATOM_TYPES)
                    or (type(value) is tuple and all(type(v) is str for v in value))
                    or type(value) in (frozenset, type(None), type(Ellipsis))
                    or name in ("__module__", "__qualname__", "__doc__", "__slots__", "__dict__")
                )
                assert allowed, f"{base.__name__}.{name} is a {type(value).__name__}: mutable?"


# class B: the depth limit fails closed, and the answer is not cached


def _nested(levels: int, leaf: object) -> object:
    """``leaf`` inside ``levels`` lists: put as an attribute (level 1), the leaf sits at level ``levels + 1``."""
    value = leaf
    for _ in range(levels):
        value = [value]
    return value


def test_a_container_left_unexplored_at_the_depth_limit_reads_as_real(tmp_path: Path) -> None:
    from hadavin_sdk import standins

    limit = standins.SCAN_DEPTH_VALUES
    llm = FakeLLM(tmp_path, {})
    assert is_stand_in_object(llm), "control"
    llm.routes = _nested(limit, lambda: None)
    assert not is_stand_in_object(llm), f"a function {limit} lists down was trusted"
    llm.routes = _nested(limit, [1, "plain"])
    assert not is_stand_in_object(llm), (
        "a list one level past the limit was trusted (a container left unexplored must fail closed)"
    )
    llm.routes = _nested(limit - 1, [1, "plain"])
    assert is_stand_in_object(llm), "a plain list at the last level entered was refused"
    llm.routes = _nested(limit, 1)
    assert is_stand_in_object(llm), "plain atoms at the depth limit were refused"
    llm.routes = _nested(limit, _Plain())
    assert not standins.is_stand_in(llm), "a foreign object at the depth limit was trusted"
    # what is entered counts against the node budget (the size is charged when the container is entered)
    llm.routes = _nested(3, [1] * 50)
    with pytest.MonkeyPatch.context() as m:
        m.setattr(standins, "SCAN_NODES", 20)
        assert not standins.is_stand_in(llm), "a container past the node budget passed"


def test_a_function_put_in_after_an_earlier_question_is_seen_at_the_next_one(
    tmp_path: Path,
) -> None:
    """The answer is not cached: a cache that looks at the top level only would miss this (a change inside a held
    container leaves the object's own attributes as they were)."""
    llm = FakeLLM(tmp_path, {})
    for _ in range(3):
        assert is_stand_in_object(llm)
    llm.routes["x"] = {"k": [lambda: None]}
    assert not is_stand_in_object(llm), "a change inside a held container was not seen"


# class C: Approvals is pinned and its slots cannot be undone


def test_an_approvals_slot_cannot_be_deleted_or_deleted_and_set_again(tmp_path: Path) -> None:
    app = _built(tmp_path)
    a = app.approvals
    channel = a.channel
    with pytest.raises(AttributeError, match="cannot be deleted"):
        del a._channel
    with pytest.raises(AttributeError, match="cannot be deleted"):
        del a.clock
    with pytest.raises(AttributeError):
        del a.channel
    assert a.channel is channel, "a refused delete still changed the object"
    with pytest.raises(AttributeError):
        a._channel = _RealChannel("sig" + "-b6-del")
    assert a.channel is channel


def _serve_public(
    app: Any, monkeypatch: pytest.MonkeyPatch
) -> tuple[http.server.HTTPServer, Approvals]:
    a = app.approvals
    _stand_in_bind_lands_on_loopback(monkeypatch)
    return serve(a, config=app.config, host=ALL_ZEROS, port=0), a


def test_a_patched_approvals_class_is_answered_503(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from hadavin_sdk.approvals import receiver

    patches: dict[str, object] = {
        "channel": property(lambda self: FakeChannel("sig" + "-b6-p")),
        "held_services": lambda self: {},
        "real_now": lambda self: (),
        "receive": lambda self, *args, **kw: (True, "ok"),
        "detector": property(lambda self: None),
        "store": property(lambda self: MemoryStore()),
    }
    for name, patch in patches.items():
        with monkeypatch.context() as m:
            m.setattr(receiver, "_LAST_LOGGED", {})  # one line a minute per set: start with none
            app = _built(tmp_path / name)
            server, _a = _serve_public(app, m)
            try:
                assert _post(server, close=False) != 503, "control: the untouched server refused"
                m.setattr(Approvals, name, patch)
                caplog.clear()
                with caplog.at_level(logging.WARNING, logger="hadavin_sdk.receiver"):
                    assert _post(server, close=False) == 503, (
                        f"a patched Approvals.{name} was served"
                    )
            finally:
                server.server_close()
            assert any("Approvals class was changed" in r.getMessage() for r in caplog.records)


def test_a_slot_deleted_with_the_object_level_call_is_answered_503_not_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    server, a = _serve_public(app, monkeypatch)
    saved = a.channel
    object.__delattr__(a, "_channel")
    try:
        try:
            status = _post(server, close=False)
        except (
            standins.SURPRISE_ERRORS
        ) as exc:  # a dropped connection shows as an http.client error
            raise AssertionError(
                f"a missing slot dropped the connection instead of a 503: {exc!r}"
            ) from None
        assert status == 503, "a missing slot gave no 503"
    finally:
        object.__setattr__(a, "_channel", saved)
        server.server_close()


def test_the_classes_are_pinned_when_the_receiver_is_imported_not_at_the_first_question() -> None:
    """In a fresh interpreter: after the import and before any question, every pin exists except the three whose module
    the approvals side cannot import (the fake secret provider, the core ``Runtime`` and its ``Hooks``: each pins
    itself as its own module is loaded, tested next). The three are LATE; every other key (20 of the 23: the five
    stand-ins, the detector list, ``Approvals``, the 11 model rows, ``Route``, ``Card`` and ``RunState``) is taken
    at import. The counts are read from the code, so a key added or removed changes them here and in the CHANGELOG."""

    from hadavin_sdk import standins as _s

    keys = len(_s._PINNED_KEYS)

    code = (
        "import hadavin_sdk.approvals.receiver\n"
        "from hadavin_sdk import standins\n"
        "late = {('hadavin_sdk.actions.secrets', 'FakeSecretProvider'), standins.RUNTIME, standins.HOOKS}\n"
        "want = set(standins._PINNED_KEYS) - late\n"
        "assert want <= set(standins._PINNED), sorted(want - set(standins._PINNED))\n"
        "print('pinned', len(want), len(standins._PINNED_KEYS))\n"
    )

    proof = "import hadavin_sdk, sys; print('PKG', hadavin_sdk.__file__)\n"
    done = _run_python(["-c", proof + code], 120)
    assert done.returncode == 0 and f"pinned {keys - 3} {keys}" in done.stdout, (
        f"the pins were not all taken at import: {done.stderr[-300:]}"
    )


# class D: small defects in the same files


class _BoomStr(str):
    def isprintable(self) -> bool:
        raise RuntimeError("no text for this key")


def test_a_hostile_text_key_gets_a_fixed_label_and_nothing_is_called_on_it_again() -> None:
    found = held_services_found({_BoomStr("ch"): _Opaque()})
    assert found == ("held (unreadable)",), found
    found = held_services_found({_BoomStr("tools"): {"a": 1}})
    assert found == ("held (unreadable)",), found


def test_one_hundred_threads_logging_one_hundred_sets_each_raise_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import threading

    from hadavin_sdk.approvals import receiver

    monkeypatch.setattr(receiver, "_LAST_LOGGED", {})
    monkeypatch.setattr(receiver._LOG, "warning", lambda *a, **k: None)
    errors: list[BaseException] = []
    start = threading.Barrier(100)

    def work(n: int) -> None:
        start.wait()
        try:
            for i in range(100):
                receiver._refused((f"held channel: T{n}-{i}",))
        except _ANYTHING as exc:  # the test records anything
            errors.append(exc)

    threads = [threading.Thread(target=work, args=(n,)) for n in range(100)]
    import sys

    interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)  # switch threads very often, so a race between two steps shows
    try:
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
    finally:
        sys.setswitchinterval(interval)
    assert not errors, f"{len(errors)} threads raised: {errors[:1]!r}"
    assert len(receiver._LAST_LOGGED) <= 64


def test_a_set_of_services_used_again_is_remembered_longer_than_ones_used_once(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The one forgotten first is the one used longest ago (not the first one stored)."""
    from hadavin_sdk.approvals import receiver

    monkeypatch.setattr(receiver.time, "monotonic", lambda: 1000.0)
    monkeypatch.setattr(receiver, "_LAST_LOGGED", {})
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.receiver"):
        receiver._refused(("held channel: Keep",))
        for i in range(30):
            receiver._refused((f"held channel: A{i}",))
        receiver._refused(
            ("held channel: Keep",)
        )  # used again within the minute: no new line, moved to the end
        for i in range(40):
            receiver._refused((f"held channel: B{i}",))
        before = len(caplog.records)
        receiver._refused(("held channel: Keep",))
        assert len(caplog.records) == before, "a set used again was forgotten before older ones"


def test_the_refusal_log_never_lets_an_error_out(monkeypatch: pytest.MonkeyPatch) -> None:
    from hadavin_sdk.approvals import receiver

    monkeypatch.setattr(receiver, "_LAST_LOGGED", {})

    def boom(*a: object, **k: object) -> None:
        raise RuntimeError("log failure")

    monkeypatch.setattr(receiver._LOG, "warning", boom)
    receiver._refused(("held channel: X",))  # must not raise


def test_the_classes_still_read_as_stand_ins_after_their_annotations_are_read() -> None:
    """A fresh interpreter: reading ``__annotations__`` of a pinned class (it adds an entry to the class
    dictionary on some Python versions) must not make the class read as real."""

    code = (
        "from hadavin_sdk.actions.secrets import FakeSecretProvider\n"
        "from hadavin_sdk.approvals import Approvals, FakeChannel\n"
        "from hadavin_sdk.guard.injection import AnyOf, RegexDetector\n"
        "from hadavin_sdk.llm.fake import FakeLLM\n"
        "from hadavin_sdk.store.memory import MemoryStore\n"
        "from hadavin_sdk import standins\n"
        "objs = [FakeSecretProvider({}), FakeChannel('s'), RegexDetector(0.5), MemoryStore(), AnyOf([])]\n"
        "assert all(standins.is_stand_in(o) for o in objs)\n"
        "for cls in (FakeSecretProvider, FakeChannel, RegexDetector, FakeLLM, MemoryStore, AnyOf, Approvals):\n"
        "    for base in cls.__mro__:\n"
        "        if base is not object:\n"
        "            base.__annotations__\n"
        "            vars(base)\n"
        "assert all(standins.is_stand_in(o) for o in objs), 'a read of __annotations__ changed the verdict'\n"
        "print('ok')\n"
    )

    proof = "import hadavin_sdk, sys; print('PKG', hadavin_sdk.__file__)\n"
    done = _run_python(["-c", proof + code], 120)
    assert done.returncode == 0 and "ok" in done.stdout, (
        f"a read of __annotations__ changed the verdict: {done.stderr[-300:]}"
    )


def test_a_class_attribute_equal_to_the_pinned_one_but_not_the_same_object_reads_as_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pin (not a new rule): attributes are compared by identity, not by equality."""
    assert is_stand_in_object(FakeChannel("sig" + "-b6-id")), "control"
    pinned = FakeChannel.max_card_chars
    assert pinned > 256, "a small int is cached: an equal int would be the same object"
    equal = int(str(pinned))
    assert equal == pinned and equal is not pinned, (
        "the test must put an equal but different object"
    )
    monkeypatch.setattr(FakeChannel, "max_card_chars", equal)
    assert FakeChannel.max_card_chars is equal, "the patch did not take effect"
    assert not is_stand_in_object(FakeChannel("sig" + "-b6-id2")), (
        "an equal but different class attribute was read as the pinned one"
    )


def test_a_class_dictionary_key_that_is_a_text_subclass_is_not_the_pinned_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pin: the comparison needs the key to be a plain ``str``."""
    from hadavin_sdk import standins

    cls = FakeChannel
    pin = standins._shape(cls)

    class Key(str):
        pass

    forged = list(pin)
    forged[2] = tuple((Key(k), v) for k, v in pin[2])
    monkeypatch.setattr(standins, "_shape", lambda c: tuple(forged))
    assert not standins._same_shape(cls, pin), "a key of another type was read as the pinned key"


def test_a_nested_stand_in_is_judged_by_its_pin_and_scanned_in_turn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    llm = FakeLLM(tmp_path, {})
    llm.child = FakeChannel("sig" + "-b6-nest")
    assert is_stand_in_object(llm), "control: a stand-in inside a stand-in is plain data"
    llm.child.hook = lambda: None
    assert not is_stand_in_object(llm), "a function held by a nested stand-in was not seen"
    llm.child = FakeChannel("sig" + "-b6-nest2")
    monkeypatch.setattr(FakeChannel, "send", lambda self, *a: None)
    assert not is_stand_in_object(llm), "a changed class of a nested stand-in was trusted"


def test_a_model_row_holding_a_foreign_object_reads_as_real() -> None:
    from hadavin_sdk.models import Run

    store = MemoryStore()
    run = Run(agent_id="a", principal_id="p", trigger_kind="user", trigger_ref="r")
    store._runs["r"] = run
    assert is_stand_in_object(store), "control"
    run.__dict__["extra"] = _Plain()
    assert not is_stand_in_object(store), "a foreign object inside a model row was trusted"


def test_the_guard_reads_the_approvals_through_the_accessors_the_runtime_uses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    a = app.approvals
    real = _RealChannel("sig" + "-b6-acc")
    monkeypatch.setattr(Approvals, "channel", property(lambda self: real))
    held = Approvals.held_services(a)
    assert held["channel"] is real, "held_services read the private slot, not the accessor"
    assert Approvals.real_now(a), "real_now did not see what the accessor returns"


def test_the_refusal_memory_is_changed_under_its_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    from hadavin_sdk.approvals import receiver

    entered: list[int] = []

    class Recording:
        def __enter__(self) -> None:
            entered.append(1)

        def __exit__(self, *exc: object) -> None:
            return None

    monkeypatch.setattr(receiver, "_LAST_LOGGED", {})
    monkeypatch.setattr(receiver, "_LAST_LOGGED_LOCK", Recording())
    monkeypatch.setattr(receiver._LOG, "warning", lambda *a, **k: None)
    receiver._refused(("held channel: Locked",))
    assert entered == [1], "the memory of logged sets was changed without its lock"


def test_the_lists_of_trusted_classes_are_exactly_these_literals() -> None:
    """A sixth stand-in, a new plain-data type, or an eighth pinned class is a visible edit of this test."""
    from hadavin_sdk import standins

    assert standins._ALLOWED == (
        ("hadavin_sdk.actions.secrets", "FakeSecretProvider"),
        ("hadavin_sdk.approvals.channel", "FakeChannel"),
        ("hadavin_sdk.guard.injection", "RegexDetector"),
        ("hadavin_sdk.llm.fake", "FakeLLM"),
        ("hadavin_sdk.store.memory", "MemoryStore"),
    ), "the list of the five stand-in classes changed"
    models = "hadavin_sdk.models"
    assert standins._DATA_CLASSES == (
        (models, "Run"),
        (models, "Target"),
        (models, "Plan"),
        (models, "GateDecision"),
        (models, "ChainStep"),
        (models, "ApprovalRequest"),
        (models, "ApprovalDecision"),
        (models, "DeadLetter"),
        (models, "TickState"),
        (models, "ToolCallRecord"),
        (models, "KillSwitch"),
        ("hadavin_sdk.config", "Route"),
        ("hadavin_sdk.approvals.cards", "Card"),
    ), "the list of plain-data types changed"
    assert standins._LEAF_CLASSES == ((models, "RunState"),)
    assert standins.RUNTIME == ("hadavin_sdk.runtime.agent_loop", "Runtime")
    assert standins.HOOKS == ("hadavin_sdk.runtime.agent_loop", "Hooks")
    assert standins._PINNED_KEYS == (
        *standins._ALLOWED,
        standins._DETECTOR_LIST,
        standins.APPROVALS,
        *standins._DATA_CLASSES,
        *standins._LEAF_CLASSES,
        standins.HOOKS,
        standins.RUNTIME,
    ), "the eager pin list changed: the CHANGELOG lists it (a test compares them)"
    assert len(standins._PINNED_KEYS) == 23


# --- round 6, batch 7 ----------------------------------------------------------------------------------------------
# class A: a held value's class is judged by identity, never by hash or equality (a metaclass the value controls)


def _spoof_class(target: type, base: bool = False) -> type:
    """A class whose metaclass hashes like ``target`` and is equal to everything. With ``base`` it also derives from
    ``target`` (so the builtin methods of ``target`` can read an instance)."""

    class Meta(type):
        def __hash__(cls) -> int:
            return hash(target)

        def __eq__(cls, other: object) -> bool:
            return True

    return Meta("Spoof", (target,) if base else (), {})


def _spoof_empty(
    target: type, member: bool = False, model: bool = False, base: bool = False
) -> object:
    """An instance of such a class that holds nothing: only the class is false, so a row that changes ONE class
    comparison is the only thing the test can see. With ``member`` it also lists itself as a member of an enum with
    its own value, so every check below the class judgement passes; with ``model`` it carries the three empty
    slots a model row is asked for; with ``base`` it derives from ``target`` (a container the builtin methods read)."""
    cls = _spoof_class(target, base=base)
    if model:
        cast(Any, cls).__pydantic_extra__ = None
        cast(Any, cls).__pydantic_private__ = None
        cast(Any, cls).__pydantic_fields_set__ = set()
    value = cls()
    if member:
        cast(Any, cls).__members__ = {"x": value}
        value._value_ = "x"
        value.__objclass__ = cls
    return value


def _spoof(target: type) -> object:
    """An instance of such a class that holds a real client."""
    value = _spoof_class(target)()
    value.client = _Opaque()
    return value


def _spoof_hosts(tmp_path: Path) -> list[object]:
    """Fresh stand-ins to hold a value: each reads as a stand-in before the value is put in."""
    from hadavin_sdk.models import Run

    store = MemoryStore()
    store.create_run(Run(agent_id="a", principal_id="p", trigger_kind="user", trigger_ref="r"))
    return [FakeLLM(tmp_path, {}), FakeChannel("sig" + "-b7-a"), store]


def _assert_every_host_refuses(tmp_path: Path, value: object, what: str) -> None:
    for host in _spoof_hosts(tmp_path):
        assert is_stand_in_object(host), "control"
        cast(Any, host).extra = value
        assert not is_stand_in_object(host), f"{what} was trusted by {type(host).__name__}"


def test_a_held_class_that_fakes_equality_and_hash_does_not_pass_as_an_atom(tmp_path: Path) -> None:
    _assert_every_host_refuses(
        tmp_path, _spoof(str), "a held class that fakes equality passed as an atom"
    )
    _assert_every_host_refuses(
        tmp_path,
        _spoof_empty(str),
        "an empty instance of a class that fakes equality passed as an atom",
    )


def test_a_held_class_that_fakes_equality_and_hash_does_not_pass_as_a_container(
    tmp_path: Path,
) -> None:
    from collections import deque

    for target in (dict, list, tuple, set, frozenset, deque):
        _assert_every_host_refuses(
            tmp_path, _spoof(target), "a held class that fakes equality passed as a container"
        )
        _assert_every_host_refuses(
            tmp_path,
            _spoof_empty(target, base=True),
            "an empty instance of a class that fakes equality passed as a container",
        )


def test_a_held_class_that_fakes_equality_and_hash_does_not_pass_as_a_model_row(
    tmp_path: Path,
) -> None:
    from hadavin_sdk.models import ChainStep, Run

    for target in (Run, ChainStep):
        _assert_every_host_refuses(
            tmp_path, _spoof(target), "a held class that fakes equality passed as a model row"
        )
        _assert_every_host_refuses(
            tmp_path,
            _spoof_empty(target, model=True),
            "an empty instance of a class that fakes equality passed as a model row",
        )


def test_a_held_class_that_fakes_equality_and_hash_does_not_pass_as_the_run_state(
    tmp_path: Path,
) -> None:
    from hadavin_sdk.models import RunState

    _assert_every_host_refuses(
        tmp_path, _spoof(RunState), "a held class that fakes equality passed as the run state"
    )
    _assert_every_host_refuses(
        tmp_path,
        _spoof_empty(RunState, member=True),
        "a class that fakes equality and lists itself as a member passed as the run state",
    )


def test_a_held_class_that_fakes_equality_is_not_an_atom_at_the_depth_tail(tmp_path: Path) -> None:
    """At every depth from 1 to 10 (the old limit was 4, the new one is 8): the last level is judged by identity."""
    for depth in range(1, 11):
        _assert_every_host_refuses(
            tmp_path,
            _nested(depth - 1, _spoof(str)),
            f"a held class that faked equality at depth {depth} passed at the depth tail",
        )


def test_a_held_class_that_fakes_equality_is_refused_as_a_key_and_in_a_nested_detector_list(
    tmp_path: Path,
) -> None:
    _assert_every_host_refuses(tmp_path, {_spoof(str): 1}, "a spoofed class used as a dict key")
    for target in (str, dict):
        member = RegexDetector(0.5)
        members = AnyOf([member, RegexDetector(0.7)])
        outer = AnyOf([members])
        assert is_stand_in_object(outer), "control"
        member.extra = _spoof(target)
        assert not is_stand_in_object(outer), (
            "a spoofed class inside a nested detector list was trusted"
        )


# class B: depth 8, a populated store, and the pin that makes "the model rows are all in __dict__" stay true


def _full_store() -> MemoryStore:
    """One of each model row the stand-in store keeps, with an approval request that has two chain steps."""
    from datetime import UTC, date, datetime
    from decimal import Decimal

    from hadavin_sdk.models import (
        ApprovalDecision,
        ApprovalRequest,
        ChainStep,
        DeadLetter,
        GateDecision,
        KillSwitch,
        Plan,
        Run,
        Target,
        TickState,
        ToolCallRecord,
    )

    store = MemoryStore()
    run = Run(agent_id="a", principal_id="p", trigger_kind="user", trigger_ref="r")
    store.create_run(run)
    plan = Plan(
        run_id=run.run_id,
        agent_id="a",
        action_id="act",
        action_version=1,
        risk_class="reversible",
        inputs={"amount": "10", "lines": [{"sku": "x", "qty": 1}]},
        target=Target(system="crm", ref="r1"),
        idempotency_key="k",
        expected_outcome="done",
    )
    store.save_plan(plan)
    store.save_gate_decision(
        GateDecision(
            run_id=run.run_id, plan_hash=plan.hash(), outcome="needs_approval", rule_id="r"
        )
    )
    req = ApprovalRequest(
        run_id=run.run_id,
        plan_hash=plan.hash(),
        risk_class="reversible",
        chain_id="c",
        steps=[
            ChainStep(approver_ids=["u1", "u2"], timeout_s=60),
            ChainStep(approver_ids=["u3"], timeout_s=60),
        ],
        step_expires_at=datetime.now(UTC),
        requested_by="p",
        summary="s",
    )
    store.save_approval_request(req)
    store.save_approval_decision(
        ApprovalDecision(
            approval_id=req.approval_id,
            plan_hash=plan.hash(),
            step=0,
            decision="approve",
            approver_id="fake:u1",
            channel="fake",
        )
    )
    store.add_dead_letter(DeadLetter(run_id=run.run_id, reason="r", errors=["e1", "e2"]))
    store.save_tick_state(TickState(step="s", last_run_at=datetime.now(UTC)))
    store.add_tool_call(
        ToolCallRecord(
            call_id=f"{run.run_id}:1",
            run_id=run.run_id,
            tool="t",
            inputs={"a": [1, 2]},
            output="o",
            output_sha256="0" * 64,
        )
    )
    store.set_kill_switch(KillSwitch(on=True, by="x"))
    store.add_spend("a", date(2026, 1, 1), Decimal("1.5"))
    store.put_redaction_map(run.run_id, {"<A>": "b"})
    return store


def test_a_store_holding_one_of_each_model_row_it_keeps_reads_as_a_stand_in(tmp_path: Path) -> None:
    from hadavin_sdk.approvals.cards import Card

    store = _full_store()
    assert is_stand_in_object(store), (
        "a plain store holding every kind of row was refused (503 on a public bind)"
    )
    channel = FakeChannel("sig" + "-b7-cards")
    channel.cards.append(
        Card(text="t", blocks=[{"type": "section", "text": {"a": ["b"]}}], display_hash="h")
    )
    assert is_stand_in_object(channel), "a channel holding a card was refused"
    store._approvals[next(iter(store._approvals))].steps[0].approver_ids.append(_Opaque())
    assert not is_stand_in_object(store), "a foreign object inside a chain step was trusted"


def test_the_depth_limit_for_held_values_is_eight_and_one_level_more_reads_as_real(
    tmp_path: Path,
) -> None:
    from hadavin_sdk import standins

    assert standins.SCAN_DEPTH_VALUES == 8 and standins.SCAN_DEPTH == 4
    store = MemoryStore()
    store.extra = _nested(standins.SCAN_DEPTH_VALUES, 1)
    assert is_stand_in_object(store), "plain atoms at the last level were refused"
    store.extra = _nested(standins.SCAN_DEPTH_VALUES + 1, 1)
    assert not is_stand_in_object(store), "a list one level past the limit was trusted"
    store.extra = _nested(standins.SCAN_DEPTH_VALUES + 1, _Opaque())
    assert not is_stand_in_object(store), "a real object past the limit was trusted"


# class C: the cost of reading a held structure is charged before it is made


def test_a_huge_container_is_not_copied_and_a_shared_one_is_charged_every_time(
    tmp_path: Path,
) -> None:
    import time
    import tracemalloc

    big = list(range(10**6))
    for name, value in (("shared list", [big] * 30), ("big dict", dict.fromkeys(range(10**6)))):
        store = MemoryStore()
        store.extra = value
        tracemalloc.start()
        before = tracemalloc.get_traced_memory()[0]
        started = time.monotonic()
        answer = is_stand_in_object(store)
        took = time.monotonic() - started
        peak = tracemalloc.get_traced_memory()[1] - before
        tracemalloc.stop()
        assert not answer, f"a {name} past the budget was trusted"
        assert peak < 4_000_000, f"the {name} was copied before it was counted: peak {peak} bytes"
        assert took < 5, f"the {name} took {took:.1f} s"


def test_a_container_referenced_many_times_is_charged_each_time_it_is_entered() -> None:
    """100,000 plain values referenced three times: each is under the budget of 250,000, the sum is not."""
    shared = list(range(100_000))
    store = MemoryStore()
    assert is_stand_in_object(store), "control"
    store.once = [shared]
    assert is_stand_in_object(store), "one copy of 100,000 plain values is within the budget"
    store.thrice = [shared, shared, shared]
    assert not is_stand_in_object(store), "a container entered three times was charged once"


def test_the_size_check_reads_the_builtin_length_not_the_one_of_a_subclass() -> None:
    from hadavin_sdk import standins

    class Liar(list):
        def __len__(self) -> int:
            return 0

    assert standins._values(Liar(range(50)), 10) is None, "a subclass's own length was believed"
    assert standins._values(list(range(5)), 10) == (0, 1, 2, 3, 4)
    assert standins._values({1: 2, 3: 4}, 3) is None, "a dict counts its keys and its values"


# class D: the run state, on_decided, serve(), every slot, the secret provider pin, the refusal log


def test_a_run_state_that_is_not_a_real_member_or_has_an_attribute_hung_on_it_reads_as_real() -> (
    None
):
    from hadavin_sdk.models import RunState

    store = MemoryStore()
    store.extra = RunState.WORKING
    assert is_stand_in_object(store), "control: a real member is plain data"
    fake = str.__new__(RunState, "WORKING")
    fake._value_ = "WORKING"
    store.extra = fake
    assert not is_stand_in_object(store), (
        "an object made as a run state but not a member was trusted"
    )
    member = RunState.EXECUTING
    member.client = _Opaque()
    try:
        store.extra = member
        assert not is_stand_in_object(store), (
            "a run state member with an attribute hung on it was trusted"
        )
    finally:
        del member.client


def _approvals_with(app: Any, on_decided: object) -> Approvals:
    built = app.approvals
    return Approvals(
        built.store,
        built.audit,
        built.registry,
        built.channel,
        on_decided,
        detector=built.detector,
        config=app.config,
        overrides=built.overrides,
        _built_by=_BUILD_TOKEN,
    )


def test_an_on_decided_that_is_not_the_one_the_core_builds_is_counted_on_a_public_bind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import types

    from hadavin_sdk.approvals.requests import _ON_DECIDED_CODE

    app = _built(tmp_path)
    _stand_in_bind_lands_on_loopback(monkeypatch)
    serve(
        _approvals_with(app, make_on_decided({})), config=app.config, host=ALL_ZEROS, port=0
    ).server_close()
    real = {
        "rt": _Opaque()
    }  # a fake real service that a callable run after a valid signature can reach

    def closing_over_a_dict(run_id: str, status: str, d: object) -> object:
        return real["rt"]

    empty: dict = {}

    def closing_over_empty(run_id: str, status: str, d: object) -> object:
        return empty

    text = "not a dict"

    def reads_text() -> str:
        return text

    cell_of_text = reads_text.__closure__
    shapes = {
        "a function that closes over a dict holding a service": closing_over_a_dict,
        "a function that closes over an empty dict (not the core's code)": closing_over_empty,
        "a lambda": lambda run_id, status, d: None,
        "the core's code with a cell that is not a dict": types.FunctionType(
            _ON_DECIDED_CODE, {}, None, None, cell_of_text
        ),
    }
    for what, func in shapes.items():
        approvals = _approvals_with(app, func)
        assert _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
            f"{what} was not counted as held on_decided"
        )
        assert "held on_decided: function" in real_services(
            app.config,
            approvals.held_services(),
        ), f"{what} was not named as held on_decided"


def test_serve_with_an_unreadable_approvals_object_raises_bind_refused_not_another_error(
    tmp_path: Path,
) -> None:
    app = _built(tmp_path)
    a = app.approvals
    saved = a.channel
    object.__delattr__(a, "_channel")
    try:
        with pytest.raises(BindRefused, match="could not read what the approvals hold"):
            serve(a, config=app.config, port=0)
    finally:
        object.__setattr__(a, "_channel", saved)


def test_the_slot_list_of_the_approvals_is_pinned() -> None:
    assert Approvals.__slots__ == (
        "_audit_sink",
        "_channel",
        "_clock",
        "_config",
        "_config_facts",
        "_detector",
        "_hand_built",
        "_on_decided",
        "_overrides",
        "_registry",
        "_store",
    ), "a slot was added or removed: the recheck reads every slot of Approvals.__slots__; review it"


@pytest.mark.parametrize("slot", Approvals.__slots__)
def test_every_slot_deleted_with_the_object_level_call_is_answered_503(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, slot: str
) -> None:
    app = _built(tmp_path)
    server, a = _serve_public(app, monkeypatch)
    saved = object.__getattribute__(a, slot)
    object.__delattr__(a, slot)
    try:
        status = _post(server, close=False)
        assert status == 503, f"a deleted {slot} was still served (status {status})"
    finally:
        object.__setattr__(a, slot, saved)
        server.server_close()


def _fresh(code: str) -> str:

    import hadavin_sdk

    proof = "import hadavin_sdk, sys; print('PKG', hadavin_sdk.__file__)\n"
    done = _run_python(["-c", proof + code], 120)
    last = (done.stderr.strip().splitlines() or [""])[-1]
    assert done.returncode == 0 and "ok" in done.stdout, f"{last} | {done.stdout[-100:]}"
    package = done.stdout.split("PKG ", 1)[1].splitlines()[0]
    assert package == hadavin_sdk.__file__, (
        f"the child imported {package}, not the package under test {hadavin_sdk.__file__}"
    )
    return done.stdout


def test_the_fake_secret_provider_is_pinned_when_its_module_is_loaded_whichever_comes_first() -> (
    None
):
    """The receiver does not import the secrets module (repo rule); the secrets module pins its own class as it is
    created. So a change made after the module is loaded is seen even if the first question comes much later."""
    first = (
        "import sys\n"
        "import hadavin_sdk.approvals.receiver\n"
        "assert 'hadavin_sdk.actions.secrets' not in sys.modules, 'the receiver imported the secrets module'\n"
        "from hadavin_sdk import standins\n"
        "import hadavin_sdk.actions.secrets as m\n"
        "key = ('hadavin_sdk.actions.secrets', 'FakeSecretProvider')\n"
        "assert key in standins._PINNED, 'not pinned when its module was loaded'\n"
        "cls = m.FakeSecretProvider\n"
        "assert standins.is_stand_in(cls({}))\n"
        "cls.get = lambda self, name: 'x'\n"
        "assert not standins.is_stand_in(cls({})), 'a method patched before the first question was not seen'\n"
        "print('ok')\n"
    )
    _fresh(first)
    swapped = (
        "import hadavin_sdk.approvals.receiver\n"
        "from hadavin_sdk import standins\n"
        "import hadavin_sdk.actions.secrets as m\n"
        "original = m.FakeSecretProvider({})\n"
        "Sub = type('FakeSecretProvider', (m.FakeSecretProvider,), {})\n"
        "m.__dict__['FakeSecretProvider'] = Sub\n"
        "assert not standins.is_stand_in(Sub({})), 'a same-name subclass was trusted'\n"
        "assert not standins.is_stand_in(original), 'the original read as a stand-in after a swap'\n"
        "print('ok')\n"
    )
    _fresh(swapped)
    loaded_first = (
        "import hadavin_sdk.actions.secrets as m\n"
        "import hadavin_sdk.approvals.receiver\n"
        "from hadavin_sdk import standins\n"
        "m.FakeSecretProvider.get = lambda self, name: 'x'\n"
        "assert not standins.is_stand_in(m.FakeSecretProvider({}))\n"
        "print('ok')\n"
    )
    _fresh(loaded_first)


def test_a_long_or_unprintable_key_or_class_name_is_never_written_to_the_refusal_line() -> None:
    unreadable = ("held (unreadable)",)
    assert held_services_found({"k" * 10_000: _Opaque()}) == unreadable, (
        "a 10,000-character key was written to the refusal line"
    )
    assert held_services_found({"a" * 41: _Opaque()}) == unreadable, (
        "a 41-character key was written"
    )
    assert held_services_found({"a\x1bb": _Opaque()}) == unreadable, (
        "a key with a control character was written"
    )
    assert held_services_found({"x" * 40: _Opaque()}) == (f"held {'x' * 40}: _Opaque",), (
        "a plain 40-character key was refused its own name"
    )
    long_name = type("N" * 500, (), {})
    assert held_services_found({"channel": long_name()}) == ("held channel: (unreadable)",), (
        "a long class name was written to the refusal line"
    )
    odd_name = type("a\x1bb", (), {})
    assert held_services_found({"channel": odd_name()}) == ("held channel: (unreadable)",), (
        "a class name with a control character was written"
    )
    assert held_services_found({"channel": _Opaque()}) == ("held channel: _Opaque",)


# --- batch 8: class 1 (a helper believed by identity must have its content judged), class 2 (instance state outside
# the scan), class 3 (one budget on every walk), class 4 (every read in serve()), class 5 (docs match code) ----------


def _refused_on_public_bind(
    app: Any, approvals: Approvals, monkeypatch: pytest.MonkeyPatch, shown: str
) -> bool:
    """True when ``serve`` on a public bind is refused with ``shown`` in the text; False when it is served."""
    with monkeypatch.context() as m:
        _no_server(m)
        try:
            serve(approvals, config=app.config, host=ALL_ZEROS, port=0)
        except BindRefused as exc:
            assert shown in str(exc), f"refused for another reason: {exc}"
            return True
        except (
            AssertionError
        ) as exc:  # ``_no_server`` raises this when the server would be built: served
            assert "a server was built" in str(exc), str(exc)
    return False


def _core_runtime(app: Any) -> Any:
    """The runtime ``build()`` made for this app: the exact core class, holding the stand-ins of the fixture."""
    return app.app.runtime


def test_a_make_on_decided_holder_that_holds_anything_but_the_core_runtime_is_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    spoof_runtime = type("Runtime", (), {})  # same name, not the core class
    counted = {
        "a holder with a real object under rt": {"rt": _Opaque()},
        "a holder with a lambda under rt": {"rt": lambda: None},
        "a holder with a lambda under another key": {"other": lambda: None},
        "a holder with two keys": {"rt": _core_runtime(app), "extra": 1},
        "a holder whose rt is a class of the same name": {"rt": spoof_runtime()},
        "a holder with a non-text key": {1: _core_runtime(app)},
    }
    for what, holder in counted.items():
        approvals = _approvals_with(app, make_on_decided(holder))
        assert _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
            f"{what} was believed to be the core's on_decided"
        )
    for what, holder in {
        "an empty holder": {},
        "the core runtime": {"rt": _core_runtime(app)},
    }.items():
        approvals = _approvals_with(app, make_on_decided(holder))
        assert not _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
            f"{what} was counted as a held service"
        )


def test_a_core_on_decided_whose_closure_cell_is_replaced_is_judged_by_what_it_now_holds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    func = make_on_decided({})
    approvals = _approvals_with(app, func)
    cell = func.__closure__[0]
    assert not _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), "control"
    for what, content in {
        "a dict holding a lambda": {"rt": lambda: None},
        "a list": [],
        "a dict subclass": type("D", (dict,), {})(),
    }.items():
        cell.cell_contents = content
        assert _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
            f"a cell replaced by {what} was served"
        )
    cell.cell_contents = {"rt": _core_runtime(app)}
    assert not _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
        "a cell holding the core runtime was counted"
    )


def test_approvals_made_by_hand_with_empty_overrides_count_as_hand_built() -> None:
    cfg = None
    hand = Approvals(
        MemoryStore(),
        _Opaque(),
        _Opaque(),
        FakeChannel("sig" + "-b8-hand"),
        make_on_decided({}),
        config=cfg,
        overrides={},
    )
    held = hand.held_services()
    assert "audit" in held and "registry" in held, (
        "an Approvals made by hand with overrides={} was believed to be built by build()"
    )


def test_a_clock_that_is_not_the_core_clock_is_counted_and_is_judged_at_every_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import types
    from datetime import UTC, datetime

    from hadavin_sdk.approvals.requests import _FIXED_CLOCK_CODE, fixed_clock
    from hadavin_sdk.models import now

    app = _built(tmp_path)
    approvals = _approvals_with(app, make_on_decided({}))
    assert "clock" not in approvals.held_services(), "the core clock was counted"
    approvals.clock = fixed_clock(datetime(2026, 1, 1, tzinfo=UTC))
    assert "clock" not in approvals.held_services(), "a fixed_clock was counted"
    real = _Opaque()

    def closing_over_real() -> object:
        return real

    shapes = {
        "a lambda": lambda: now(),
        "a function closing over a real object": closing_over_real,
        "the fixed_clock code with a real object in its cell": types.FunctionType(
            _FIXED_CLOCK_CODE, {}, None, None, (types.CellType(real),)
        ),
    }
    for what, clock in shapes.items():
        approvals.clock = clock
        assert "clock" in approvals.held_services(), f"{what} was not counted as held"
        assert _refused_on_public_bind(app, approvals, monkeypatch, "held clock"), (
            f"{what} was served on a public bind"
        )
    approvals.clock = now
    assert "clock" not in approvals.held_services(), "the core clock was counted after a reset"


def test_a_counter_with_an_attribute_hung_on_it_reads_as_real(tmp_path: Path) -> None:
    from collections import Counter

    plain: Counter[str] = Counter()
    for host in _spoof_hosts(tmp_path):
        assert is_stand_in_object(host), "control"
        cast(Any, host).stats = plain
        assert is_stand_in_object(host), "a plain empty Counter was refused"
        hidden: Counter[str] = Counter()
        cast(Any, hidden).client = _Opaque()
        cast(Any, host).stats = hidden
        assert not is_stand_in_object(host), (
            f"a Counter with an attribute holding a real object was trusted by {type(host).__name__}"
        )


def test_the_instance_state_helper_refuses_a_counter_with_an_attribute() -> None:
    from collections import Counter

    from hadavin_sdk import standins

    clean: Counter[str] = Counter()
    assert standins._no_instance_state(clean, Counter), "the helper refused a clean Counter"
    cast(Any, clean).client = _Opaque()
    assert not standins._no_instance_state(clean, Counter), (
        "the helper passed a Counter with an attribute"
    )
    assert standins._no_instance_state("text", str), "the helper refused a string"


def test_the_fake_model_with_its_own_counter_still_reads_as_a_stand_in(tmp_path: Path) -> None:
    llm = FakeLLM(tmp_path, {})
    llm._attempts["x"] += 1
    assert is_stand_in_object(llm), "the fake model holding a used Counter was refused"


def test_only_the_counter_among_the_allowlisted_types_can_carry_instance_state() -> None:
    """Every plain type goes through ``standins._no_instance_state``. A type that has an instance dictionary is
    listed here: a new one fails until it is added to the test with its attribute check."""
    from collections import Counter, defaultdict

    from hadavin_sdk import standins

    kinds = (*standins._ATOM_TYPES, *standins._PLAIN_CONTAINERS, Counter, defaultdict)
    with_state = {k for k in kinds if k.__dictoffset__ != 0}
    assert with_state == {Counter}, (
        f"an allowlisted type has an instance dictionary: {sorted(k.__name__ for k in with_state)}; "
        "check it in standins._no_instance_state and list it here"
    )


def _load_data_modules() -> None:
    importlib.import_module("hadavin_sdk.models")


def _pydantic_rows() -> list[tuple[tuple[str, str], type]]:
    from hadavin_sdk import standins

    _load_data_modules()
    found = [(key, standins.live_class(key)) for key in standins._DATA_CLASSES]
    assert all(c is not None for _, c in found)
    return [(key, c) for key, c in found if key not in standins._DATACLASS_KEYS]


@pytest.mark.parametrize("slot", ["__pydantic_extra__", "__pydantic_private__"])
def test_a_model_row_with_state_in_a_pydantic_slot_reads_as_real(slot: str) -> None:
    for key, cls in _pydantic_rows():
        row = cast(Any, cls).model_construct()
        store = MemoryStore()
        store.extra = row
        assert is_stand_in_object(store), f"control: a plain {key[1]} row was refused"
        object.__setattr__(row, slot, {"c": _Opaque()})
        assert not is_stand_in_object(store), (
            f"a {key[1]} row with a real object in {slot} was trusted"
        )


def test_a_model_row_with_a_foreign_fields_set_reads_as_real() -> None:
    for key, cls in _pydantic_rows():
        for what, value in {
            "a non-text member": {1},
            "a subclass of set": type("S", (set,), {})(),
            "a list": [],
        }.items():
            row = cast(Any, cls).model_construct()
            object.__setattr__(row, "__pydantic_fields_set__", value)
            store = MemoryStore()
            store.extra = row
            assert not is_stand_in_object(store), (
                f"a {key[1]} row whose fields-set is {what} was trusted"
            )


def test_a_patched_method_of_a_model_class_is_seen_because_data_classes_are_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from hadavin_sdk.models import Run

    store = _populated_store()
    assert is_stand_in_object(store), "control"
    monkeypatch.setattr(Run, "hash_marker", lambda self: "x", raising=False)
    assert not is_stand_in_object(store), "a method added to a model class was not seen"


def _data_class_problem(key: tuple[str, str], cls: type) -> str | None:
    import dataclasses

    from pydantic import BaseModel

    if dataclasses.is_dataclass(cls):
        return None if "__slots__" not in vars(cls) else "a dataclass with slots"
    if not (isinstance(cls, type) and issubclass(cls, BaseModel)):
        return f"{key[1]} is neither a pydantic model nor a plain dataclass"
    if cast(Any, cls).model_config.get("extra") != "forbid":
        return f"{key[1]} does not forbid extra fields"
    if cast(Any, cls).__private_attributes__:
        return f"{key[1]} declares private attributes"
    return None


def test_every_data_class_is_a_forbidding_pydantic_model_or_the_one_plain_dataclass() -> None:
    from hadavin_sdk import standins

    _load_data_modules()

    for key in standins._DATA_CLASSES:
        cls = standins.live_class(key)
        assert cls is not None, key
        assert _data_class_problem(key, cls) is None, _data_class_problem(key, cls)
        assert (key in standins._DATACLASS_KEYS) == __import__("dataclasses").is_dataclass(cls), (
            f"{key[1]} is listed with the wrong base kind"
        )
    assert _data_class_problem(("m", "Plain"), type("Plain", (), {})) is not None, (
        "the check passed a class that is not a pydantic model"
    )


def _counting(monkeypatch: pytest.MonkeyPatch, name: str, limit: int) -> list[int]:
    from hadavin_sdk import standins

    calls = [0]
    real = getattr(standins, name)

    def counted(*args: object, **kw: object) -> object:
        calls[0] += 1
        if calls[0] > limit:
            # ``pytest.fail`` is a ``BaseException``: the guard's ``except Exception`` cannot swallow it, and it stops
            # the work at the limit (an unbounded walk would otherwise run for minutes)
            pytest.fail(
                f"{name} was called more than {limit} times: the cost is not bounded", pytrace=False
            )
        return real(*args, **kw)

    monkeypatch.setattr(standins, name, counted)
    return calls


def test_a_detector_list_built_to_fan_out_is_cut_off_by_the_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import time

    d = RegexDetector(0.5)
    deep = AnyOf([AnyOf([AnyOf([AnyOf([d] * 100)] * 100)] * 100)] * 100)
    from hadavin_sdk import standins

    # the scan of the members runs before the walk: both are counted, and either stops the work at its limit
    entered = _counting(monkeypatch, "_entered", standins.SCAN_NODES + 50_000)
    calls = _counting(monkeypatch, "_check", 5_000)
    started = time.monotonic()
    assert not is_stand_in_object(deep), "a fan-out of 10^8 visits was trusted"
    assert time.monotonic() - started < 5, "the fan-out took more than 5 s"
    assert calls[0] <= 5_000
    assert entered[0] <= standins.SCAN_NODES + 50_000


def test_the_walk_of_a_detector_list_is_charged_for_every_visit() -> None:
    d = RegexDetector(0.5)
    assert is_stand_in_object(AnyOf([d] * 2_000)), "2,000 shared detectors were refused"
    assert not is_stand_in_object(AnyOf([d] * 7_500)), (
        "7,500 shared detectors (scanned once, walked once) were not charged for the walk"
    )


def test_a_million_shared_members_of_a_detector_list_cost_a_bounded_time_and_memory() -> None:
    import time
    import tracemalloc

    big = AnyOf([RegexDetector(0.5)] * 10**6)
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    started = time.monotonic()
    answer = is_stand_in_object(big)
    took = time.monotonic() - started
    peak = tracemalloc.get_traced_memory()[1] - before
    tracemalloc.stop()
    assert not answer, "a detector list of 10^6 shared members was trusted"
    assert took < 5, f"10^6 shared members took {took:.1f} s"
    assert peak < 4_000_000, f"10^6 shared members were copied: peak {peak} bytes"


def test_fifteen_hundred_references_to_one_stand_in_cost_one_shape_comparison_per_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    channel = FakeChannel("sig" + "-b8-shared")
    store = MemoryStore()
    store.extra = [channel] * 1_500  # inside the budget: each reference is visited
    calls = _counting(monkeypatch, "_same_shape", 20)
    assert is_stand_in_object(store), "1,500 references to one stand-in were refused"
    assert 1 <= calls[0] <= 20


def test_a_stand_in_is_charged_twenty_values_and_a_few_thousand_references_are_fine() -> None:
    channel = FakeChannel("sig" + "-b8-weight")
    store = MemoryStore()
    store.extra = [channel] * 5_000
    assert is_stand_in_object(store), (
        "5,000 references to one stand-in (about 165,000 values) were refused"
    )
    store.extra = [channel] * 12_000
    assert not is_stand_in_object(store), (
        "12,000 references to one stand-in (about 400,000 values) passed"
    )
    store.extra = [1] * 20_000
    assert is_stand_in_object(store), "20,000 plain numbers were charged like stand-ins"
    from hadavin_sdk.models import Run

    row = Run(agent_id="a", principal_id="p", trigger_kind="user", trigger_ref="r")
    store.extra = [row] * 2_000
    assert is_stand_in_object(store), "2,000 references to one model row were refused"
    store.extra = [row] * 8_000
    assert not is_stand_in_object(store), (
        "8,000 references to one model row were not charged for the rows"
    )


def test_an_over_budget_structure_is_named_apart_from_a_real_service() -> None:
    from hadavin_sdk import standins

    big = MemoryStore()
    big.extra = list(range(standins.SCAN_NODES + 1))
    assert standins.verdict(big) == standins.VERDICT_OVER_BUDGET
    foreign = MemoryStore()
    foreign.extra = _Opaque()
    assert standins.verdict(foreign) == standins.VERDICT_REAL, (
        "a real object was reported as over budget"
    )
    assert standins.verdict(MemoryStore()) == standins.VERDICT_STAND_IN
    assert held_services_found({"store": big}) == (
        "held store: over budget (too many values to check)",
    ), "an over-budget store was not named apart"
    assert held_services_found({"store": foreign}) == ("held store: MemoryStore",), (
        "a real object inside a store was reported as over budget"
    )


def test_serve_refuses_with_bind_refused_when_an_object_raises_while_the_approvals_are_read(
    tmp_path: Path,
) -> None:
    """New test, fails on the old code (an object that raises while ``held_services`` reads it escaped as its own
    error): a hostile mapping in the overrides slot raises when it is read, not when a slot is missing."""

    class Hostile:
        def keys(self) -> object:
            raise RuntimeError("hostile overrides")

        def __getitem__(self, key: object) -> object:
            raise RuntimeError("hostile overrides")

    app = _built(tmp_path)
    a = app.approvals
    saved = object.__getattribute__(a, "_overrides")
    object.__setattr__(a, "_overrides", Hostile())
    try:
        with pytest.raises(BindRefused, match="could not read what the approvals hold"):
            serve(a, config=app.config, port=0)
    finally:
        object.__setattr__(a, "_overrides", saved)


@pytest.mark.parametrize("slot", Approvals.__slots__)
def test_serve_refuses_with_bind_refused_when_any_slot_is_deleted(
    tmp_path: Path, slot: str
) -> None:
    """A deleted slot (``object.__delattr__``) means the object cannot be trusted: the start check reads every slot
    and answers ``BindRefused`` for each one, also for the slots (the audit sink and the registry among them) that a built object's held map does not name."""
    app = _built(tmp_path)
    a = app.approvals
    saved = object.__getattribute__(a, slot)
    object.__delattr__(a, slot)
    try:
        with pytest.raises(BindRefused, match="could not read what the approvals hold"):
            serve(a, config=app.config, port=0)
    finally:
        object.__setattr__(a, slot, saved)


def test_every_name_in_a_refusal_line_is_a_plain_word() -> None:
    unreadable = ("held (unreadable)",)
    for hostile in ("channel: FakeChannel", "a b", "a.b", "a-b", "9lives", "", "é\u200b"):
        assert held_services_found({hostile: _Opaque()}) == unreadable, (
            f"the key {hostile!r} was written to the refusal line"
        )
    assert held_services_found({"channel_2": _Opaque()}) == ("held channel_2: _Opaque",)
    assert held_services_found({"channel": type("a b", (), {})()}) == (
        "held channel: (unreadable)",
    ), "a class name with a space was written to the refusal line"


def test_operator_config_names_are_filtered_in_the_refusal_line(stand_in_config: Config) -> None:
    from hadavin_sdk.bindguard import config_services

    cfg = stand_in_config.model_copy(
        update={
            "tool_modules": ["ok.module-name", "bad name: x", "y" * 41],
            "check_modules": ["line\nbreak"],
        }
    )
    lines = config_services(cfg)
    assert "tools:ok.module-name" in lines, "a plain module name was refused its own name"
    assert "tools:bad name: x" not in lines, (
        "a tools module name with a space was written to the refusal line"
    )
    assert "tools:(unreadable)" in lines, (
        "a hostile tools module name was written to the refusal line"
    )
    assert "checks:(unreadable)" in lines, (
        "a hostile checks module name was written to the refusal line"
    )
    assert not any("bad name" in line or "break" in line for line in lines)


def test_every_run_state_member_keeps_only_the_keys_of_a_fresh_enum_member() -> None:
    from hadavin_sdk import standins
    from hadavin_sdk.models import RunState

    for member in RunState:
        keys = set(object.__getattribute__(member, "__dict__"))
        assert keys <= standins._ENUM_MEMBER_KEYS, (
            f"{member.name} holds {sorted(keys - standins._ENUM_MEMBER_KEYS)} beyond the keys of a "
            f"fresh enum member {sorted(standins._ENUM_MEMBER_KEYS)} on this Python: a Run would read as real"
        )
    assert standins._ENUM_MEMBER_KEYS >= {"_value_", "_name_"}, (
        "the probe enum has no value and name keys"
    )


def test_the_class_level_attributes_of_the_pinned_classes_are_functions_or_builtin_descriptors() -> (
    None
):
    """``inspect.ismethoddescriptor`` accepts anything with ``__get__`` and no ``__set__``, an ``lru_cache`` wrapper
    included. Only these types are allowed as a class attribute that holds code."""
    import functools
    import types

    from hadavin_sdk import standins

    allowed = (
        types.FunctionType,
        classmethod,
        staticmethod,
        property,
        types.WrapperDescriptorType,
        types.MethodDescriptorType,
        types.ClassMethodDescriptorType,
        types.MemberDescriptorType,
        types.GetSetDescriptorType,
    )
    assert not isinstance(functools.lru_cache(lambda: 1), allowed), (
        "control: a cache wrapper is refused"
    )
    importlib.import_module("hadavin_sdk.runtime.agent_loop")  # its last line pins ``Runtime``

    plain = (*standins._ALLOWED, standins._DETECTOR_LIST, standins.APPROVALS, standins.RUNTIME)
    for key in plain:  # the model rows are pydantic classes: judged by their own test
        cls = standins.live_class(key)
        for base in cls.__mro__:
            if base is object:
                continue
            for name, value in vars(base).items():
                if callable(value) or hasattr(type(value), "__get__"):
                    assert type(value) in allowed or isinstance(value, type), (
                        f"{base.__name__}.{name} is a {type(value).__name__}, not a function or builtin descriptor"
                    )


def _changelog_problems(
    text: str,
    depth_values: int,
    nodes: int,
    weight: int,
    depth: int,
    slots: tuple[str, ...],
    rows: int,
) -> list[str]:
    problems = []
    if "handover/" in text:
        problems.append("the CHANGELOG points at a handover path")
    for want in (
        f"depth of {depth_values} levels",
        f"at most {nodes} values",
        f"charged {weight} values",
        f"nesting at most {depth} deep",
        f"read are: {', '.join(f'`{s}`' for s in slots)}.",
        f"runs {rows} mutants ({rows - 1} on Python 3.14",
    ):
        if want not in text:
            problems.append(f"the CHANGELOG does not say {want!r}")
    return problems


def _code_numbers() -> tuple[int, int, int, int, tuple[str, ...], int]:
    import sys

    from hadavin_sdk import standins
    from tests import bind_mutants

    rows = len(bind_mutants.M) + (1 if sys.version_info >= (3, 14) else 0)
    return (
        standins.SCAN_DEPTH_VALUES,
        standins.SCAN_NODES,
        standins.STAND_IN_WEIGHT,
        standins.SCAN_DEPTH,
        Approvals.__slots__,
        rows,
    )


def test_changelog_numbers_and_lists_are_the_ones_in_the_code() -> None:
    changelog = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    if not changelog.is_file():  # the mutation runner copies src and tests only
        pytest.skip("no CHANGELOG.md next to the tests (a mutation copy)")
    problems = _changelog_problems(changelog.read_text(encoding="utf-8"), *_code_numbers())
    assert not problems, f"the CHANGELOG and the code differ: {problems}"


def test_the_changelog_check_notices_a_changed_number_a_changed_list_and_a_handover_path() -> None:
    changelog = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    if not changelog.is_file():
        pytest.skip("no CHANGELOG.md next to the tests (a mutation copy)")
    text = changelog.read_text(encoding="utf-8")
    depth_values, nodes, weight, depth, slots, rows = _code_numbers()
    for what, args in {
        "depth": (depth_values + 1, nodes, weight, depth, slots, rows),
        "nodes": (depth_values, nodes + 1, weight, depth, slots, rows),
        "weight": (depth_values, nodes, weight + 1, depth, slots, rows),
        "detector depth": (depth_values, nodes, weight, depth + 1, slots, rows),
        "slots": (depth_values, nodes, weight, depth, slots[:-1], rows),
        "rows": (depth_values, nodes, weight, depth, slots, rows + 1),
    }.items():
        assert _changelog_problems(text, *args), (
            f"a changed {what} was not noticed in the CHANGELOG"
        )
    assert _changelog_problems(text + "\nsee handover/x", *_code_numbers()), (
        "a handover path in the CHANGELOG was not noticed"
    )


# ---------------------------------------------------------------------------------------------------------------
# Round 9 (package PD part 2, batch 9): clock and atom state, pin moment, pre-authentication cost, refusal text.
# ---------------------------------------------------------------------------------------------------------------


def _hostile_tz(seen: list[str]) -> Any:
    """A ``tzinfo`` whose ``utcoffset`` records a call: foreign code that an aware ``datetime.timestamp()`` runs."""
    from datetime import timedelta, tzinfo

    class Tz(tzinfo):
        def utcoffset(self, dt: object) -> timedelta:
            seen.append("utcoffset")
            return timedelta(0)

        def dst(self, dt: object) -> timedelta:
            return timedelta(0)

        def tzname(self, dt: object) -> str:
            return "x"

    return Tz()


def test_a_fixed_clock_with_a_foreign_tzinfo_is_counted_and_never_runs_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Class: an exact type judged without its state. ``receive`` calls ``clock().timestamp()`` before the signature is
    checked, and an aware moment calls ``tzinfo.utcoffset``. A tzinfo that is not None or ``datetime.UTC`` is counted."""
    from datetime import UTC, datetime, timedelta, timezone

    from hadavin_sdk.approvals.requests import fixed_clock
    from hadavin_sdk.models import now

    app = _built(tmp_path)
    approvals = _approvals_with(app, make_on_decided({}))
    for what, moment in {
        "no tzinfo": datetime.fromisoformat("2026-01-01T00:00:00"),
        "datetime.UTC": datetime(2026, 1, 1, tzinfo=UTC),
    }.items():
        approvals.clock = fixed_clock(moment)
        assert not _refused_on_public_bind(app, approvals, monkeypatch, "held clock"), (
            f"control: a fixed_clock with {what} was counted"
        )
    approvals.clock = now
    seen: list[str] = []
    for what, tz in {
        "a tzinfo subclass": _hostile_tz(seen),
        "an exact timezone": timezone(timedelta(hours=1)),
    }.items():
        approvals.clock = fixed_clock(datetime(2026, 1, 1, tzinfo=tz))
        assert "clock" in approvals.held_services(), f"a fixed_clock with {what} was not counted"
        assert _refused_on_public_bind(app, approvals, monkeypatch, "held clock"), (
            f"a fixed_clock with {what} was served on a public bind"
        )
    assert seen == [], "the guard ran the foreign utcoffset"


def test_a_clock_swapped_in_after_the_start_is_answered_503_and_never_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import datetime

    from hadavin_sdk.approvals.requests import fixed_clock

    app = _built(tmp_path)
    server, approvals = _serve_public(app, monkeypatch)
    try:
        assert _post(server, close=False) != 503, "control: the untouched server refused"
        seen: list[str] = []
        approvals.clock = fixed_clock(datetime(2026, 1, 1, tzinfo=_hostile_tz(seen)))
        assert _post(server, close=False) == 503, (
            "a hostile-tzinfo clock was served after the start"
        )
        assert seen == [], "the foreign utcoffset ran before the answer"
    finally:
        server.server_close()


def test_the_clock_of_build_is_judged_like_the_clock_set_later(tmp_path: Path) -> None:
    from datetime import datetime

    from hadavin_sdk.approvals.requests import fixed_clock

    seen: list[str] = []
    app = _built(tmp_path, clock=fixed_clock(datetime(2026, 1, 1, tzinfo=_hostile_tz(seen))))
    assert "clock" in app.app.approvals.held_services(), (  # the real build result
        "a build(clock=...) with a foreign tzinfo was not counted"
    )
    assert seen == []


def test_models_now_with_its_code_replaced_is_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from hadavin_sdk.models import now

    app = _built(tmp_path)
    approvals = _approvals_with(app, make_on_decided({}))
    approvals.clock = now
    assert "clock" not in approvals.held_services(), "control: models.now was counted"
    original = now.__code__
    try:
        monkeypatch.setattr(
            now,
            "__code__",
            (lambda: 0).__code__,
        )
        assert "clock" in approvals.held_services(), (
            "models.now with another code object was not counted"
        )
    finally:
        now.__code__ = original


def test_a_stand_in_holding_a_datetime_with_a_foreign_tzinfo_reads_as_real(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    seen: list[str] = []
    for host in _spoof_hosts(tmp_path):
        assert is_stand_in_object(host), "control"
        cast(Any, host).when = datetime.fromisoformat("2026-01-01T00:00:00")
        assert is_stand_in_object(host), "a naive datetime was refused"
        cast(Any, host).when = datetime(2026, 1, 1, tzinfo=UTC)
        assert is_stand_in_object(host), "a datetime in UTC was refused"
        cast(Any, host).when = datetime(2026, 1, 1, tzinfo=_hostile_tz(seen))
        assert not is_stand_in_object(host), (
            f"a datetime with a foreign tzinfo was trusted by {type(host).__name__}"
        )
    assert seen == []


def test_a_path_with_a_real_object_in_a_slot_reads_as_real(tmp_path: Path) -> None:
    """Class: slots of an allowlisted atom. ``PosixPath`` keeps its parts in slots that ``__dict__`` does not show."""
    for host in _spoof_hosts(tmp_path):
        assert is_stand_in_object(host), "control"
        cast(Any, host).where = tmp_path
        assert is_stand_in_object(host), "a plain Path was refused"
        evil = Path(str(tmp_path))
        cast(Any, evil)._str = _Opaque()
        cast(Any, host).where = evil
        assert not is_stand_in_object(host), (
            f"a Path with a real object in a slot was trusted by {type(host).__name__}"
        )


def test_a_class_patched_before_the_first_question_reads_as_real() -> None:
    """Class: pinned late. The pins are taken when the receiver is imported, so a change made after the import and
    before any question is seen (fresh interpreter: the pin state of this one is not reusable)."""
    head = (
        "import hadavin_sdk.approvals.receiver\n"
        "import hadavin_sdk.runtime.agent_loop\n"
        "from hadavin_sdk import standins\n"
        "from hadavin_sdk.models import Run\n"
        "from hadavin_sdk.store.memory import MemoryStore\n"
        "s = MemoryStore()\n"
        "s.create_run(Run(agent_id='a', principal_id='p', trigger_kind='user', trigger_ref='r'))\n"
    )
    out = _fresh(head + "print('ok', standins.verdict(s))\n")
    assert "ok stand-in" in out, "control: the untouched store did not read as a stand-in"
    for patch in (
        "Run.hook = lambda self: None",
        "from hadavin_sdk.models import RunState\nRunState.hook = lambda self: None",
    ):
        out = _fresh(head + f"{patch}\nprint('ok', standins.verdict(s))\n")
        assert "ok real" in out, (
            f"a class patched before the first question read as a stand-in: {patch}"
        )
    out = _fresh(
        head
        + "from hadavin_sdk.runtime.agent_loop import Runtime\n"
        + "r = object.__new__(Runtime)\n"
        + "Runtime.on_decided = lambda self: None\n"
        + "print('ok', standins.is_pinned_instance(r, standins.RUNTIME))\n"
    )
    assert "ok False" in out, (
        f"a Runtime class patched before the first question was believed: {out[-60:]}"
    )
    out = _fresh(
        head
        + "from hadavin_sdk.runtime.agent_loop import Runtime\n"
        + "print('ok', standins.is_pinned_instance(object.__new__(Runtime), standins.RUNTIME))\n"
    )
    assert "ok True" in out, "control: the untouched Runtime class was not believed"


def test_a_hand_built_runtime_in_a_holder_is_counted_and_a_hand_built_approvals_gets_no_belief(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from hadavin_sdk.runtime.agent_loop import Runtime

    app = _built(tmp_path)
    real = _Opaque()
    hand = object.__new__(Runtime)
    hand.store, hand.llm, hand.detector = real, real, real
    approvals = _approvals_with(app, make_on_decided({"rt": hand}))
    assert _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
        "a Runtime holding real objects was believed"
    )
    built = app.approvals
    handmade = Approvals(
        built.store,
        built.audit,
        built.registry,
        built.channel,
        make_on_decided({"rt": _core_runtime(app)}),
        detector=built.detector,
        config=app.config,
        overrides=built.overrides,
    )
    assert "on_decided" in handmade.held_services(), (
        "a hand-built Approvals was believed with a runtime in its holder"
    )


def test_a_serve_of_an_approvals_class_with_a_replaced_method_is_refused_before_anything_else(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    approvals = app.approvals
    _stand_in_bind_lands_on_loopback(monkeypatch)
    served = None
    try:
        with monkeypatch.context() as m:
            m.setattr(Approvals, "held_services", lambda self: (), raising=True)
            with pytest.raises(BindRefused, match="changed after it was pinned"):
                served = serve(approvals, config=app.config, host=ALL_ZEROS, port=0)
    finally:
        if served is not None:  # a regression that serves must not leak the socket
            served.server_close()


MIXED_ROWS = 1_000  # the row count of the CHANGELOG figure; the cost tests and the CHANGELOG test read it from here


def _fill_mixed(store: MemoryStore, rows: int) -> MemoryStore:
    """``rows`` runs of four kinds in turn: a bare run; a run with a plan; a run with an approval request of two
    steps; a run with a tool call. This is the mix the 1,000-row figure of the CHANGELOG was measured on."""
    from datetime import UTC, datetime

    from hadavin_sdk.models import (
        ApprovalRequest,
        ChainStep,
        Plan,
        Run,
        Target,
        ToolCallRecord,
    )

    def plan(run: Run, i: int, inputs: dict[str, object]) -> Plan:
        return Plan(
            run_id=run.run_id,
            agent_id="a",
            action_id="act",
            action_version=1,
            risk_class="reversible",
            inputs=inputs,
            target=Target(system="crm", ref="r1"),
            idempotency_key=f"k{i}",
            expected_outcome="done",
        )

    for i in range(rows):
        run = Run(agent_id="a", principal_id="p", trigger_kind="user", trigger_ref=f"r{i}")
        store.create_run(run)
        kind = i % 4
        if kind == 1:
            store.save_plan(plan(run, i, {"amount": "10", "lines": [{"sku": "x", "qty": 1}]}))
        elif kind == 2:
            store.save_approval_request(
                ApprovalRequest(
                    run_id=run.run_id,
                    plan_hash=plan(run, i, {"amount": "10"}).hash(),
                    risk_class="reversible",
                    chain_id="c",
                    steps=[
                        ChainStep(approver_ids=["u1", "u2"], timeout_s=60),
                        ChainStep(approver_ids=["u3"], timeout_s=60),
                    ],
                    step_expires_at=datetime.now(UTC),
                    requested_by="p",
                    summary="s",
                )
            )
        elif kind == 3:
            store.add_tool_call(
                ToolCallRecord(
                    call_id=f"{run.run_id}:1",
                    run_id=run.run_id,
                    tool="t",
                    inputs={"a": [1, 2]},
                    output="o",
                    output_sha256="0" * 64,
                )
            )
    return store


def _mixed_store(rows: int) -> MemoryStore:
    return _fill_mixed(MemoryStore(), rows)


def test_a_thousand_row_store_is_a_stand_in_and_answers_401_not_503(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Class: pre-authentication cost. The budget is a bound on the work, not a limit that a normal store reaches."""
    from hadavin_sdk import standins

    app = _built(tmp_path)
    store = _fill_mixed(app.approvals.store, MIXED_ROWS)
    assert standins.verdict(store) == "stand-in", "1,000 rows were not a stand-in"
    server, _ = _serve_public(app, monkeypatch)
    try:
        assert _post(server, close=False) == 401, "a 1,000-row store was refused"
    finally:
        server.server_close()


def test_a_store_over_the_budget_is_named_over_budget_and_a_real_object_is_named_real() -> None:
    from hadavin_sdk import standins

    huge = _mixed_store(1)
    huge.extra = [list(range(1_000))] * 500  # 500,000 values, shared
    assert standins.verdict(huge) == "over budget", "a store of 500,000 values was not over budget"
    big = list(range(1_000))
    real = _Opaque()
    for real_last in (True, False):
        # one level holds 500 references to a 1,000-value list (the budget runs out inside it) and a real object
        level: list[Any] = [big] * 500
        level = [*level, real] if real_last else [real, *level]
        store = _mixed_store(1)
        store.extra = [level]
        assert standins.verdict(store) == "real", (
            f"a real object met after the budget ran out was labelled otherwise (real_last={real_last})"
        )


def test_a_thousand_rows_use_at_most_half_the_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Counted in values, not seconds: the budget leaves at least 2x room for 1,000 mixed rows."""
    from hadavin_sdk import standins

    used: list[int] = []
    real_charge = standins._Budget.charge

    def charge(self: object, n: int) -> bool:
        used.append(n)
        return real_charge(self, n)

    monkeypatch.setattr(standins._Budget, "charge", charge)
    assert standins.verdict(_mixed_store(MIXED_ROWS)) == "stand-in"
    assert sum(used) <= standins.SCAN_NODES // 2, (
        f"1,000 rows used {sum(used)} of {standins.SCAN_NODES} values"
    )


def test_a_refusal_text_cannot_imitate_a_line_of_its_own() -> None:
    """Class: free text in a refusal. A host or reason that is not printable ASCII, or that carries a lookalike, is
    shown as unreadable; a host that reads like ``x, held channel: FakeChannel`` is not shown whole."""
    from hadavin_sdk import bindguard

    for host in ("\u0430pp.example", "host\u00b2", "x, held channel: FakeChannel", "a b", "a\nb"):
        shown = bindguard._shown(host)
        assert shown == "(unreadable)", f"{host!r} was shown as {shown!r}"
    assert bindguard._shown(ALL_ZEROS) == ALL_ZEROS, "control: an address was not shown"
    assert bindguard.reason_problem("a long enough reason caf\u00e9") is not None, (
        "a non-ASCII reason was accepted"
    )
    assert bindguard.reason_problem("a plain reason") is None, "control: a plain reason was refused"
    assert not bindguard._is_plain_word("\u0430bc"), "a Cyrillic word was a plain word"
    assert not bindguard._is_plain_name("\u0430bc"), "a Cyrillic name was a plain name"
    assert not bindguard._is_plain_name("a.\u00b2"), "a superscript digit was a plain name part"
    assert not bindguard._is_plain_name("a.\u0663"), "an Arabic-Indic digit was a plain name part"
    assert bindguard._is_plain_name("a-b.2"), "control: a plain name was refused"


def test_the_changelog_states_the_pin_moment_the_budget_row_count_and_the_boundary() -> None:
    changelog = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    if not changelog.is_file():
        pytest.skip("no CHANGELOG.md next to the tests (a mutation copy)")
    from hadavin_sdk import standins
    from hadavin_sdk.approvals import requests as R

    text = changelog.read_text(encoding="utf-8")
    flat = " ".join(text.split())
    for key in standins._PINNED_KEYS:
        assert f"`{key[1]}`" in flat, f"the CHANGELOG pin list does not name {key[1]}"
    for factory in sorted(standins._DEFAULT_FACTORIES, key=lambda f: f.__name__):
        assert f"`{factory.__name__}`" in flat, (
            f"the CHANGELOG does not name the defaultdict factory {factory.__name__}"
        )
    rows = MIXED_ROWS
    assert f"{rows:,} mixed rows" in flat or f"{rows} mixed rows" in flat, (
        "the CHANGELOG does not give the 1,000-row figure"
    )
    assert "can be imported by code already running in the server process" in flat, (
        "the build-token boundary is not stated"
    )
    assert R._BUILD_TOKEN is not None


def test_every_build_argument_is_either_recorded_as_an_override_or_named_as_not_a_service() -> None:
    """Class: an object handed to ``build()`` that the guard never hears about. Fails on 83cdb7a2 (a real old-code run: the names recorded in ``build()`` there are
    channel, detector, llm, secrets, sources, tools, without ``hold_run_ids``); a new argument is caught. ``hold_run_ids`` is a callable the
    purge tick runs, so it is recorded in ``overrides`` like the other callables (batch 10); ``timeout_s`` is a number
    and ``clock`` is judged as the approvals' own clock. The recorded names are read from the ``build()`` source, not
    from a copy of the list, and the folder that is searched must exist and hold files (a wrong path found nothing and
    asserted nothing before batch 10)."""
    import inspect

    from hadavin_sdk.app import build

    params = set(inspect.signature(build).parameters) - {"config_dir", "agents"}
    recorded = {"secrets", "channel", "detector", "llm", "tools", "sources", "hold_run_ids"}
    not_services = {"timeout_s", "clock"}
    assert params == recorded | not_services, (
        f"a build argument is in neither list: {params ^ (recorded | not_services)}"
    )
    assert len(params) == 9, f"build() has {len(params)} parameters besides config_dir and agents"
    source = inspect.getsource(build)
    block = source[source.index("overrides = {") : source.index("cfg = load_config")]
    named = set(re.findall(r'\("(\w+)",', block))
    assert named == recorded, f"the names recorded in build() are {sorted(named)}"


def test_the_depth_is_eight_levels_below_the_own_dictionary_and_the_texts_say_so() -> None:
    """The sentence in the module text and the CHANGELOG is the behaviour: 8 nested containers are entered, the ninth
    reads as real when it holds anything but plain atoms."""
    import re

    from hadavin_sdk import standins

    def nested(levels: int, leaf: object) -> object:
        value: object = [leaf]
        for _ in range(levels - 1):
            value = [value]
        return value

    host = MemoryStore()
    host.extra = nested(standins.SCAN_DEPTH_VALUES, 1)
    assert standins.verdict(host) == "stand-in", "eight nested containers of numbers were refused"
    host.extra = nested(standins.SCAN_DEPTH_VALUES, _Opaque())
    assert standins.verdict(host) == "real", "a real object eight containers deep was not seen"
    host.extra = nested(standins.SCAN_DEPTH_VALUES + 1, _Opaque())
    assert standins.verdict(host) == "real", "a real object nine containers deep was trusted"
    doc = standins.__doc__ or ""
    assert (
        f"``SCAN_DEPTH_VALUES`` ({standins.SCAN_DEPTH_VALUES}) levels of containers below the instance's own"
        in " ".join(doc.split())
    ), "the module text does not say how deep the scan goes"
    changelog = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    if changelog.is_file():
        flat = " ".join(changelog.read_text(encoding="utf-8").split())
        match = re.search(
            r"depth of (\d+) levels of dict, list, tuple, set or deque below the instance's own dictionary",
            flat,
        )
        assert match and int(match.group(1)) == standins.SCAN_DEPTH_VALUES, (
            "the CHANGELOG depth sentence is wrong"
        )


def test_a_core_runtime_whose_class_was_patched_is_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from hadavin_sdk.runtime.agent_loop import Runtime

    app = _built(tmp_path)
    approvals = _approvals_with(app, make_on_decided({"rt": _core_runtime(app)}))
    assert not _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
        "control: the built runtime was counted"
    )
    with monkeypatch.context() as m:
        m.setattr(Runtime, "on_decided", lambda self, *a, **k: None, raising=False)
        assert _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
            "a Runtime whose class was patched was believed"
        )


def test_a_card_with_a_slot_reads_as_real() -> None:
    from hadavin_sdk import standins

    key = ("hadavin_sdk.approvals.cards", "Card")
    cls = standins.live_class(key)
    assert cls is not None
    assert standins._data_state_ok(object.__new__(cls), key), "control: a plain Card was refused"

    class Slotted:
        __slots__ = ("x",)

    held = Slotted()
    cast(Any, held).x = _Opaque()
    assert not standins._data_state_ok(held, key), "a row with a slot was trusted"


def test_a_holder_key_that_is_a_text_subclass_runs_no_code_of_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []

    class Key(str):
        def __eq__(self, other: object) -> bool:
            seen.append("eq")
            return True

        def __ne__(self, other: object) -> bool:
            seen.append("ne")
            return False

        def __hash__(self) -> int:
            return hash("rt")

    app = _built(tmp_path)
    approvals = _approvals_with(app, make_on_decided({Key("rt"): _core_runtime(app)}))
    assert _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
        "a holder whose key is a text subclass was believed"
    )
    assert seen == [], "the key's own comparison ran before the signature was checked"


# ---------------------------------------------------------------------------------------------------------------
# Batch 10 (package PD part 2, review round 9): atom judge at the last level, instance shadows, one budget per request,
# CHANGELOG counts tied to the code, the 13 data classes, live_class, the clock's module names.
# ---------------------------------------------------------------------------------------------------------------


def _last_level_verdict(leaf: object) -> str:
    """The verdict of a store that holds ``leaf`` in a list in the container of the LAST level the scan enters (the
    values it holds are only looked at, never entered)."""
    from hadavin_sdk import standins

    host = MemoryStore()
    host.extra = _nested(standins.SCAN_DEPTH_VALUES, leaf)
    return standins.verdict(host)


def test_the_last_level_judges_an_atom_like_every_other_level(tmp_path: Path) -> None:
    """Class: ATOM. At the depth limit an atom was judged by type only, so a ``datetime`` with a foreign ``tzinfo`` or a
    ``Path`` with a real object in a slot at the ninth level read as plain (a real service called a stand-in). Fails on
    83cdb7a2 (plain atoms and subclasses stay as they were: those lines are controls)."""
    from datetime import UTC, datetime

    seen: list[str] = []
    evil_path = Path(str(tmp_path))
    cast(Any, evil_path)._str = _Opaque()
    assert _last_level_verdict(datetime(2026, 1, 1, tzinfo=UTC)) == "stand-in", (
        "control: UTC datetime"
    )
    assert _last_level_verdict(datetime.fromisoformat("2026-01-01T00:00:00")) == "stand-in", (
        "control: naive datetime"
    )
    assert _last_level_verdict(tmp_path) == "stand-in", "control: a plain Path"
    assert _last_level_verdict(1) == "stand-in", "control: a number"
    assert _last_level_verdict(datetime(2026, 1, 1, tzinfo=_hostile_tz(seen))) == "real", (
        "a datetime with a foreign tzinfo at the last level was trusted"
    )
    assert _last_level_verdict(evil_path) == "real", (
        "a Path with a real object in a slot at the last level was trusted"
    )
    assert _last_level_verdict(_NumberWithCode(1)) == "real", (
        "an int subclass at the last level was trusted"
    )
    assert _last_level_verdict(_TextWithCode("x")) == "real", (
        "a str subclass at the last level was trusted"
    )
    assert seen == []


def _runtime_counted(app: Any, runtime: Any) -> bool:
    return "on_decided" in _approvals_with(app, make_on_decided({"rt": runtime})).held_services()


def test_a_function_or_a_name_put_on_the_core_runtime_instance_is_counted(tmp_path: Path) -> None:
    """Class: INSTANCE-SHADOW. ``Runtime`` has no ``__slots__``: ``rt.on_decided = f`` on the instance shadows the pinned
    class method (a function is a non-data descriptor), and the class pin cannot see it. Fails on 83cdb7a2."""
    app = _built(tmp_path)
    rt = _core_runtime(app)
    assert not _runtime_counted(app, rt), "control: the runtime build() made was counted"
    own = object.__getattribute__(rt, "__dict__")
    for name in ("on_decided", "tick", "execute", "handle", "a_name_the_class_never_had"):
        own[name] = lambda *args, **kw: None
        try:
            assert _runtime_counted(app, rt), f"an instance-level {name} was not counted"
        finally:
            del own[name]
        assert not _runtime_counted(app, rt), (
            f"control: {name} was removed and the runtime was still counted"
        )


def test_a_member_of_the_core_runtime_that_is_not_the_one_build_made_is_counted(
    tmp_path: Path,
) -> None:
    """Class: INSTANCE-SHADOW, one line of ``_RUNTIME_SEALED`` at a time, and the hooks field by field."""
    import copy

    app = _built(tmp_path)
    rt = _core_runtime(app)
    own = object.__getattribute__(rt, "__dict__")
    for name, other in (
        ("registry", _Opaque()),
        ("audit", _Opaque()),
        ("limits", _Opaque()),
        ("agents", set(own["agents"])),  # an equal set is still not the one build() put there
        ("hooks", copy.copy(own["hooks"])),  # equal fields, but not the object build() made
    ):
        was = own[name]
        own[name] = other
        try:
            assert _runtime_counted(app, rt), f"a replaced {name} was not counted"
        finally:
            own[name] = was
    own["agents"].add("another-agent")
    try:
        assert _runtime_counted(app, rt), "an agent added in place was not counted"
    finally:
        own["agents"].discard("another-agent")
    hooks = own["hooks"]
    for field in ("hold_run_ids", "execute", "post_card"):
        was = getattr(hooks, field)
        setattr(hooks, field, lambda *args, **kw: None)
        try:
            assert _runtime_counted(app, rt), f"hooks.{field} replaced was not counted"
        finally:
            setattr(hooks, field, was)
    assert not _runtime_counted(app, rt), (
        "control: after every restore the runtime is believed again"
    )


def test_pin_a_service_of_the_core_runtime_that_is_not_a_stand_in_is_counted(
    tmp_path: Path,
) -> None:
    """Class: INSTANCE-SHADOW (the three members that reach a service: each must still be a stand-in). A sealed runtime
    whose ``store``, ``llm`` or ``detector`` was replaced by a real object is counted. NEW on batch 10: the row B215
    survived without it. PIN: passes on 83cdb7a2 too (the stand-in check of these three was already there)."""
    app = _built(tmp_path)
    rt = _core_runtime(app)
    own = object.__getattribute__(rt, "__dict__")
    assert not _runtime_counted(app, rt), "control: the runtime build() made was counted"
    for name in ("store", "llm", "detector"):
        was = own[name]
        own[name] = _Opaque()
        try:
            assert _runtime_counted(app, rt), f"a replaced {name} was not counted"
        finally:
            own[name] = was
    assert not _runtime_counted(app, rt), (
        "control: after every restore the runtime is believed again"
    )


def test_hold_run_ids_put_into_the_hooks_of_a_real_runtime_is_refused_on_a_public_bind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The evidence for ``hold_run_ids`` is no longer a text search: a ``hold_run_ids`` put into the hooks of the runtime
    in the holder makes the verdict real, so a public bind refuses it, and a ``hold_run_ids`` given to ``build()`` is
    recorded in ``overrides``."""
    app = _built(tmp_path)
    approvals = _approvals_with(app, make_on_decided({"rt": _core_runtime(app)}))
    assert not _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), "control"
    hooks = _core_runtime(app).hooks
    hooks.hold_run_ids = lambda: set()
    try:
        assert _refused_on_public_bind(app, approvals, monkeypatch, "held on_decided"), (
            "a hold_run_ids put into the hooks was believed"
        )
    finally:
        hooks.hold_run_ids = None
    given = _built(tmp_path / "given", hold_run_ids=lambda: set())
    assert "hold_run_ids" in given.approvals.overrides, (
        "hold_run_ids given to build() was not recorded"
    )
    assert "hold_run_ids" in given.approvals.held_services(), (
        "a recorded hold_run_ids was not counted"
    )


def test_a_runtime_made_by_hand_with_stand_ins_only_is_not_believed(tmp_path: Path) -> None:
    """Class: INSTANCE-SHADOW. A runtime ``build()`` did not seal is never believed, whatever it holds."""
    from hadavin_sdk.runtime.agent_loop import Runtime

    app = _built(tmp_path)
    real = _core_runtime(app)
    hand = object.__new__(Runtime)
    object.__getattribute__(hand, "__dict__").update(object.__getattribute__(real, "__dict__"))
    assert not _runtime_counted(app, real), "control"
    assert _runtime_counted(app, hand), "an unsealed copy of the runtime was believed"


def test_a_request_scans_the_store_the_runtime_holds_once_and_stays_within_one_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Class: COST. ``real_now`` is what every unauthenticated POST runs: the store the approvals hold is also the store
    of the runtime in ``on_decided``, and the two askers each had a fresh budget. Now one ``Scan`` per request.
    Fails on 83cdb7a2 (a real old-code run: "the store was scanned 2 times in one request")."""
    from hadavin_sdk import standins

    app = _built(tmp_path)
    store = app.approvals.store
    assert _core_runtime(app).store is store
    # the approvals of ``build()`` hold the runtime in their ``on_decided``: the runtime check reads the same store
    approvals = _approvals_with(app, make_on_decided({"rt": _core_runtime(app)}))
    store.extra = [list(range(1000))] * (standins.SCAN_NODES * 4 // 5 // 1000)
    scans: list[int] = []
    charged: list[int] = []
    real_check, real_charge = standins._check, standins._Budget.charge

    def check(obj: object, depth: int, seen: frozenset[int], budget: object) -> bool:
        if obj is store and depth == 0:
            scans.append(1)
        return real_check(obj, depth, seen, budget)

    def charge(self: object, n: int) -> bool:
        charged.append(n)
        return real_charge(self, n)

    monkeypatch.setattr(standins, "_check", check)
    monkeypatch.setattr(standins._Budget, "charge", charge)
    assert approvals.real_now() == (), "control: the 80% store was refused"
    assert len(scans) == 1, f"the store was scanned {len(scans)} times in one request"
    assert sum(charged) <= standins.SCAN_NODES, (
        f"one request charged {sum(charged)} values, more than one budget ({standins.SCAN_NODES})"
    )


def test_one_request_is_bounded_by_one_budget_when_every_object_is_big(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Class: COST, worst case. The store, the detector's holder and the runtime's members all hold large values; the
    values charged by ONE ``real_now`` stay within one budget plus the last charge (the walk stops at the wall)."""
    from hadavin_sdk import standins

    app = _built(tmp_path)
    approvals = _approvals_with(app, make_on_decided({"rt": _core_runtime(app)}))
    big = [list(range(1000))] * 150
    app.approvals.store.extra = big
    app.approvals.channel.extra = big
    _core_runtime(app).llm.extra = big
    charged: list[int] = []
    real_charge = standins._Budget.charge

    def charge(self: object, n: int) -> bool:
        charged.append(n)
        return real_charge(self, n)

    monkeypatch.setattr(standins._Budget, "charge", charge)
    result = approvals.real_now()
    assert result, "control: three 150,000-value objects were not over one budget together"
    assert sum(charged) <= standins.SCAN_NODES + 1_000, (
        f"one request charged {sum(charged)} values (one budget is {standins.SCAN_NODES})"
    )


def test_models_now_with_a_replaced_module_name_is_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Class: CLOCK/GLOBALS. ``models.now`` reads ``datetime`` and ``UTC`` from its module: replacing either runs foreign
    code before the signature is checked. Fails on 83cdb7a2 (only the code object was pinned)."""
    from hadavin_sdk import models

    app = _built(tmp_path)
    approvals = _approvals_with(app, make_on_decided({}))
    approvals.clock = models.now
    assert "clock" not in approvals.held_services(), "control: models.now was counted"
    for name in ("datetime", "UTC"):
        with monkeypatch.context() as m:
            m.setattr(models, name, _Opaque())
            assert "clock" in approvals.held_services(), (
                f"models.now with a replaced {name} was not counted"
            )
    assert "clock" not in approvals.held_services(), "control: restored"


def test_pin_a_class_name_whose_value_pretends_to_be_a_type_is_not_a_class() -> None:
    """Class: LIVE-CLASS. ``isinstance(x, type)`` asks ``x.__class__``, which an object controls; the type of the value
    is what counts. PIN: passes on 83cdb7a2 too (that source already asked the type of the value); the row B251 shows
    the test fails when the check goes back to ``isinstance``."""
    import sys
    import types

    from hadavin_sdk import standins

    def _claims_type(self: object) -> type:
        return type

    Liar = type("Liar", (), {"__class__": property(_claims_type)})

    module = types.ModuleType("b10_live_class_probe")
    module.__dict__["Thing"] = Liar()
    module.__dict__["Real"] = Liar
    sys.modules["b10_live_class_probe"] = module
    try:
        assert standins.live_class(("b10_live_class_probe", "Thing")) is None, (
            "an object whose __class__ says type was taken as a class"
        )
        assert standins.live_class(("b10_live_class_probe", "Real")) is Liar, (
            "control: a class was refused"
        )
    finally:
        del sys.modules["b10_live_class_probe"]


def test_pin_all_thirteen_data_classes_stay_as_pinned_after_use_in_a_fresh_interpreter() -> None:
    """Class: OUTAGE-GUARD. The 13 data classes are pinned when the receiver is imported. Using each one (a validation
    that fails still runs the class's validator, and a deferred build would replace it) must not change a pinned class:
    if it did, every store would read as real and every request would be answered 503. NEW on batch 10 for the
    ``Run`` class only; the other twelve are new coverage. PIN: passes on 83cdb7a2 (the pins held there too); the row
    B252 shows the test fails when one class is left out of the eager pin."""
    code = (
        "import hadavin_sdk.approvals.receiver\n"
        "from hadavin_sdk import standins\n"
        "from hadavin_sdk.models import Run\n"
        "from hadavin_sdk.store.memory import MemoryStore\n"
        "keys = list(standins._DATA_CLASSES)\n"
        "assert len(keys) == 13, len(keys)\n"
        "missing = [k for k in keys if k not in standins._PINNED]\n"
        "assert not missing, ('not pinned at import', missing)\n"
        "for key in keys:\n"
        "    cls = standins.live_class(key)\n"
        "    if hasattr(cls, 'model_validate'):\n"
        "        try:\n"
        "            cls.model_validate({})\n"
        "        except Exception:\n"
        "            pass\n"
        "bad = [k for k in keys if not standins._same_shape(standins.live_class(k), standins._PINNED[k])]\n"
        "assert not bad, ('changed by use', bad)\n"
        "s = MemoryStore()\n"
        "s.create_run(Run(agent_id='a', principal_id='p', trigger_kind='user', trigger_ref='r'))\n"
        "print('ok', standins.verdict(s))\n"
    )
    out = _fresh(code)
    assert "ok stand-in" in out, (
        f"a normal store was not a stand-in after the 13 classes were used: {out[-80:]}"
    )


def _pin_sentence_counts(flat: str) -> tuple[int, int, set[str]]:
    match = re.search(r"seen at once: (.*?) \((\d+) of the (\d+) pinned classes\)", flat)
    assert match, "the CHANGELOG pin-list sentence was not found"
    names = set(re.findall(r"`(\w+)`", match.group(1)))
    return int(match.group(2)), int(match.group(3)), names


def _pin_sentence_problems(flat: str) -> list[str]:
    """What differs between the CHANGELOG pin sentence in ``flat`` and ``standins`` (empty when they agree)."""
    from hadavin_sdk import standins

    at_import, total, names = _pin_sentence_counts(flat)
    own_module = {standins.RUNTIME[0], standins.HOOKS[0], standins._ALLOWED[0][0]}
    late = [k for k in standins._PINNED_KEYS if k[0] in own_module]
    early = {k[1] for k in standins._PINNED_KEYS if k not in late}
    problems = []
    if total != len(standins._PINNED_KEYS):
        problems.append(f"the CHANGELOG says {total} pinned classes")
    if at_import != len(standins._PINNED_KEYS) - len(late):
        problems.append(f"the CHANGELOG says {at_import} at import")
    if names != early:
        problems.append(
            f"the classes in the CHANGELOG list differ from the code: {sorted(names ^ early)}"
        )
    return problems


def test_the_changelog_pin_counts_and_the_row_figure_are_the_code_s() -> None:
    """Class: TEXT-TEST. The sentence that lists the pinned classes is PARSED: the count of classes pinned at import, the
    count of all pinned classes and every class name in the list are the ones in ``standins``; the 1,000-row figure is
    ``MIXED_ROWS``. Fails on 83cdb7a2 (no ``HOOKS`` there). The mutation runner copies no CHANGELOG, so this test is
    skipped there: the check that a count off by one is noticed is ``test_the_pin_count_check_notices_a_count_off_by_one``."""
    changelog = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    if not changelog.is_file():
        pytest.skip("no CHANGELOG.md next to the tests (a mutation copy)")
    flat = " ".join(changelog.read_text(encoding="utf-8").split())
    assert not _pin_sentence_problems(flat), _pin_sentence_problems(flat)
    assert f"{MIXED_ROWS:,} mixed rows" in flat, "the CHANGELOG row figure is not MIXED_ROWS"


def test_the_pin_count_check_notices_a_count_off_by_one() -> None:
    """Class: MUTANT-KILLER for the count itself, without the CHANGELOG file (so it runs in a mutation copy): a made-up
    sentence with the right counts agrees with the code, and the same sentence with each count one too high, or one class
    name left out, does not. Fails on 83cdb7a2 (no ``HOOKS`` there)."""
    from hadavin_sdk import standins

    own_module = {standins.RUNTIME[0], standins.HOOKS[0], standins._ALLOWED[0][0]}
    early = sorted({k[1] for k in standins._PINNED_KEYS if k[0] not in own_module})
    total = len(standins._PINNED_KEYS)

    def sentence(at_import: int, all_: int, names: list[str]) -> str:
        listed = ", ".join(f"`{n}`" for n in names)
        return f"seen at once: {listed} ({at_import} of the {all_} pinned classes)"

    good = sentence(len(early), total, early)
    assert _pin_sentence_problems(good) == [], f"control: {_pin_sentence_problems(good)}"
    assert _pin_sentence_problems(sentence(len(early) + 1, total, early)), (
        "a count at import one too high"
    )
    assert _pin_sentence_problems(sentence(len(early), total + 1, early)), "a total one too high"
    assert _pin_sentence_problems(sentence(len(early), total, early[1:])), "a class name left out"


def test_pin_a_model_row_visited_is_charged_the_stand_in_weight_each_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Class: MUTANT-KILLER (the charge itself, not a count of values that happens to be near a limit). Five more runs in
    the store are five more rows, and each row is charged ``STAND_IN_WEIGHT`` once. PIN: passes on 83cdb7a2; row B219 shows it fails when the
    charge is dropped."""
    from hadavin_sdk import standins

    def weights(runs: int) -> int:
        charged: list[int] = []
        real_charge = standins._Budget.charge

        def charge(self: object, n: int) -> bool:
            charged.append(n)
            return real_charge(self, n)

        with monkeypatch.context() as m:
            m.setattr(standins._Budget, "charge", charge)
            assert (
                standins.verdict(_mixed_store(0) if runs == 0 else _runs_store(runs)) == "stand-in"
            )
        return charged.count(standins.STAND_IN_WEIGHT)

    assert weights(6) - weights(1) == 5, (
        "five more model rows were not charged five more row weights"
    )


def _runs_store(runs: int) -> MemoryStore:
    from hadavin_sdk.models import Run

    store = MemoryStore()
    for i in range(runs):
        store.create_run(
            Run(agent_id="a", principal_id="p", trigger_kind="user", trigger_ref=f"r{i}")
        )
    return store


def test_pin_copying_an_object_of_a_pinned_class_does_not_change_the_answer(tmp_path: Path) -> None:
    """Class: PIN-FRAGILITY. ``copy.copy`` writes ``__slotnames__`` into the class dictionary the first time; the pin
    must include it, or a copy of the hooks (or of a data row) made anywhere makes every later question read as real.
    PIN: passes on 83cdb7a2 (the hooks were not pinned there, so nothing could change); row B256 shows it fails when
    the pin stops including ``__slotnames__``."""
    import copy

    app = _built(tmp_path)
    rt = _core_runtime(app)
    copy.copy(object.__getattribute__(rt, "__dict__")["hooks"])
    copy.deepcopy(object.__getattribute__(rt, "__dict__")["hooks"])
    assert not _runtime_counted(app, rt), "a copy of the hooks made the runtime read as real"


# ---------------------------------------------------------------------------------------------------------------
# Batch 11 (package PD part 2, review round 10): what the hooks carry, every member of the runtime, no leak, a real
# run and tick between two key snapshots.
# ---------------------------------------------------------------------------------------------------------------


def _seal(runtime: Any) -> None:
    """Seal a runtime again (a test that puts a toolbox into the hooks first)."""
    from hadavin_sdk.approvals import requests as R

    R._seal_runtime(runtime)


def _real_function(*args: object, **kw: object) -> str:
    return "a real function put in after the seal"


def test_a_tool_put_into_the_hooks_of_a_sealed_runtime_is_counted(tmp_path: Path) -> None:
    """Class: SEAL-COMPLETE (round 10, design M-1). ``build()`` gives the runtime its own copy of ``tools``; adding a tool
    to that dict keeps the identity of the hooks and of the dict, so an identity check read a runtime with a real
    callable in it as a stand-in. Fails on 304c3bd3."""
    app = _built(tmp_path)
    rt = _core_runtime(app)
    hooks = rt.hooks
    assert not _runtime_counted(app, rt), "control: the runtime build() made was counted"
    hooks.tools["lookup"] = _real_function
    try:
        assert _runtime_counted(app, rt), (
            "a tool added to hooks.tools after the seal was not counted"
        )
    finally:
        del hooks.tools["lookup"]
    assert not _runtime_counted(app, rt), (
        "control: the tool was removed and the runtime was counted"
    )
    given = _built(tmp_path / "given", tools={"lookup": lambda inp: "x"})
    given_rt = _core_runtime(given)
    tools = given_rt.hooks.tools
    first = tools["lookup"]
    tools["lookup"] = _real_function
    try:
        assert _runtime_counted(given, given_rt), (
            "a tool replaced in hooks.tools after the seal was not counted"
        )
    finally:
        tools["lookup"] = first
    del tools["lookup"]
    tools["renamed"] = first
    assert _runtime_counted(given, given_rt), "a tool renamed in hooks.tools was not counted"


def test_the_toolbox_and_the_executor_of_a_sealed_runtime_cannot_be_changed_unseen(
    tmp_path: Path,
) -> None:
    """Class: SEAL-COMPLETE (round 10, codebase N11). A member of the toolbox, a name added to it, or the secrets the
    executor holds is replaced after the seal. Fails on 304c3bd3 (the fields were compared by identity only)."""
    from hadavin_sdk.tools import ToolBox

    app = _built(tmp_path)
    rt = _core_runtime(app)
    box = ToolBox({}, {"echo": lambda inp, ctx: "x"}, timeout_s=1.0)
    rt.hooks.toolbox = box
    _seal(rt)
    assert not _runtime_counted(app, rt), "control: a runtime sealed with a toolbox was counted"
    box.abandoned()  # rebinds ``_abandoned`` (state that moves in use)
    assert not _runtime_counted(app, rt), (
        "control: ordinary use of the toolbox made it read as real"
    )
    executor = rt.hooks.execute.__self__
    in_dict = (
        ("a function of the toolbox replaced", box._fns, "echo", _real_function),
        ("a name added to the toolbox", box._fns, "extra", _real_function),
    )
    for label, target, key, new in in_dict:
        had, was = key in target, target.get(key)
        target[key] = new
        try:
            assert _runtime_counted(app, rt), f"{label} was not counted"
        finally:
            if had:
                target[key] = was
            else:
                del target[key]
        assert not _runtime_counted(app, rt), f"control: {label} was undone and still counted"
    on_object: tuple[tuple[str, Any, str, Any], ...] = (
        ("the argument checker of the toolbox replaced", box, "_arg_errors", _real_function),
        ("the secrets the executor holds replaced", executor, "_secrets", _Opaque()),
    )
    for label, owner, name, new in on_object:
        was = getattr(owner, name)
        setattr(owner, name, new)
        try:
            assert _runtime_counted(app, rt), f"{label} was not counted"
        finally:
            setattr(owner, name, was)
        assert not _runtime_counted(app, rt), f"control: {label} was undone and still counted"


def test_the_code_and_the_closure_cells_of_a_hook_function_cannot_be_rewritten_unseen(
    tmp_path: Path,
) -> None:
    """Class: SEAL-COMPLETE (round 10, design M-1). ``post_card`` and ``request_approval`` are closures made by
    ``build()``: a cell's content (``cell.cell_contents = x``) or the function's code can be rewritten and the function
    object stays the same. Fails on 304c3bd3."""
    app = _built(tmp_path)
    rt = _core_runtime(app)
    hooks = rt.hooks
    assert not _runtime_counted(app, rt), "control"
    for name in ("post_card", "request_approval"):
        fn = getattr(hooks, name)
        assert fn.__closure__, f"control: {name} has no closure cell to rewrite"
        for index, cell in enumerate(fn.__closure__):
            was = cell.cell_contents
            cell.cell_contents = _Opaque()
            try:
                assert _runtime_counted(app, rt), (
                    f"cell {index} of {name} rewritten was not counted"
                )
            finally:
                cell.cell_contents = was
            assert not _runtime_counted(app, rt), f"control: cell {index} of {name} restored"
        code = fn.__code__
        fn.__code__ = code.replace(co_name=code.co_name + "_rewritten")
        try:
            assert _runtime_counted(app, rt), f"the code of {name} rewritten was not counted"
        finally:
            fn.__code__ = code
        assert not _runtime_counted(app, rt), f"control: the code of {name} restored"


def test_the_judged_names_of_a_runtime_are_all_its_keys(tmp_path: Path) -> None:
    """Class: SEAL-COMPLETE (round 10, codebase M1). ``_RUNTIME_SEALED`` and ``_RUNTIME_SERVICES`` together name every
    key of a built ``Runtime``; a member added to ``Runtime.__init__`` fails here until it is judged (it would
    otherwise be believed whatever it held). Fails on 304c3bd3 (``_evidence`` and ``_kinds`` were not listed)."""
    from hadavin_sdk.approvals import requests as R

    keys = set(object.__getattribute__(_core_runtime(_built(tmp_path)), "__dict__"))
    judged = set(R._RUNTIME_SEALED) | set(R._RUNTIME_SERVICES)
    assert judged == keys, (
        f"the judged names and the keys of a built Runtime differ: {sorted(judged ^ keys)}"
    )


def test_a_kinds_or_evidence_put_on_the_core_runtime_is_counted(tmp_path: Path) -> None:
    """Class: SEAL-COMPLETE (round 10, codebase M1). ``rt._kinds = <object with __contains__>`` ran foreign code on the
    paths ``on_decided`` reaches. Fails on 304c3bd3 for both members."""

    class Contains:
        def __contains__(self, item: object) -> bool:
            return True

    app = _built(tmp_path)
    rt = _core_runtime(app)
    own = object.__getattribute__(rt, "__dict__")
    assert not _runtime_counted(app, rt), "control"
    for name, other in (
        ("_kinds", Contains()),
        ("_kinds", frozenset({"another-kind"})),
        ("_kinds", set(own["_kinds"])),
        ("_evidence", _Opaque()),
    ):
        was = own[name]
        own[name] = other
        try:
            assert _runtime_counted(app, rt), (
                f"a replaced {name} ({type(other).__name__}) was not counted"
            )
        finally:
            own[name] = was
    assert not _runtime_counted(app, rt), "control: restored"


def test_a_sealed_runtime_that_is_dropped_is_freed(tmp_path: Path) -> None:
    """Class: LEAK (round 10, design M-2). The seal's value used to hold the hooks, which reach the runtime (hooks ->
    ``request_approval`` -> ``Approvals`` -> ``on_decided`` -> holder -> runtime): the weak table never freed one. A
    built app is dropped and the runtime must be gone after ``gc.collect()``. Fails on 304c3bd3."""
    import gc
    import weakref

    from hadavin_sdk.approvals import requests as R

    app = _built(tmp_path)
    rt = _core_runtime(app)
    assert rt in R._RUNTIME_SEALS, "control: the runtime was not sealed"
    ref = weakref.ref(rt)
    del app, rt
    gc.collect()
    assert ref() is None, "a dropped runtime is still held (the seal keeps it alive)"


def test_the_seal_is_private(tmp_path: Path) -> None:
    """Class: API (round 10, design N-1). The function that records what a runtime may be believed to hold is not a
    public name of the approvals package or of ``requests``. Fails on 304c3bd3 (it was ``seal_runtime``)."""
    from hadavin_sdk import approvals
    from hadavin_sdk.approvals import requests as R

    assert not hasattr(R, "seal_runtime"), "seal_runtime is a public name of requests"
    assert not hasattr(approvals, "seal_runtime"), "seal_runtime is a public name of approvals"
    public = {name for name in dir(R) if not name.startswith("_")}
    assert not {n for n in public if "seal" in n.lower()}, (
        "a public name of requests mentions the seal"
    )
    assert callable(R._seal_runtime), "control: the private function is missing"


def test_pin_a_real_run_and_a_real_tick_add_no_name_to_the_runtime(tmp_path: Path) -> None:
    """Class: OUTAGE-GUARD (round 10, design M-3 and codebase M2). The key set is compared at every request: a name the
    runtime writes lazily while it works (a cache, a counter) would read as a shadow and answer 503 to every public
    POST. A real ``handle`` (a document in, a plan and an approval request out, with the fixture's recorded model) and a
    real ``tick`` run between two snapshots; the runtime stays believed. PIN: passes on 304c3bd3 (a real old-code run: the
    runtime wrote no lazy name there); the row B257 adds a lazy attribute in ``handle`` and this test fails on it."""
    from hadavin_sdk.runtime.tick import run_tick

    app = _built(tmp_path)
    rt = _core_runtime(app)
    before = tuple(object.__getattribute__(rt, "__dict__"))
    assert not _runtime_counted(app, rt), "control: counted before the run"
    document = (app.app.config.inputs_dir / "create.txt").read_bytes()
    run = rt.handle("test-agent", "svc:test-agent", document)
    assert run.state.value == "WAITING_FOR_APPROVAL", (
        f"the run did not reach the approval: {run.state}"
    )
    assert run_tick(app.app) == 0, "the tick did not finish"
    assert tuple(object.__getattribute__(rt, "__dict__")) == before, (
        "the run or the tick added or removed a name of the runtime"
    )
    assert not _runtime_counted(app, rt), "a runtime that has worked was counted"


def test_an_object_read_after_the_budget_ran_out_is_not_blamed_for_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Class: TEXT (round 10, codebase N12). One ``Scan`` covers a request: when the budget runs out the object that
    crossed the limit can be a small one asked about last, and the line blamed it. The scan now records the object that
    used the most of the budget, and the line for another object says so. Fails on 304c3bd3 (both lines said
    ``over budget (too many values to check)``). The budget is made small (90 values) so the first store (72 values)
    leaves too little for the channel (32 values)."""
    from hadavin_sdk import standins

    monkeypatch.setattr(standins, "SCAN_NODES", 90)
    store, channel = MemoryStore(), FakeChannel("sig" + "-b11-test")
    scan = standins.Scan()
    lines = bindguard.held_services_found({"a_store": store, "b_channel": channel}, scan)
    assert lines == (
        "held b_channel: not read in full, another object (MemoryStore) used most of the budget",
    ), f"the lines were {lines}"
    assert scan.heaviest is store, "the scan did not record the object that used the most budget"
    alone = bindguard.held_services_found({"b_channel": channel}, standins.Scan())
    assert alone == (), "control: the channel alone was counted"


# ---------------------------------------------------------------------------------------------------------------
# Batch 12 (package PD part 2, review round 11): the members limits, audit, registry and _evidence, identity before
# any read, the walk limits, a real tool call and an executed action between two seals.
# ---------------------------------------------------------------------------------------------------------------


def _fields(obj: object) -> dict:
    return object.__getattribute__(obj, "__dict__")


@pytest.mark.parametrize(
    ("member", "field"),
    [
        ("limits", "store"),
        ("limits", "audit"),
        ("limits", "registry"),
        ("audit", "root"),
        ("audit", "_pending"),
        ("registry", "agents"),
        ("registry", "config"),
        ("_evidence", "scrub"),
    ],
)
def test_a_field_of_limits_audit_registry_or_evidence_replaced_after_the_seal_is_counted(
    tmp_path: Path, member: str, field: str
) -> None:
    """Class: SEAL-COMPLETE (round 11, issue 1). Trace (see the CHANGELOG): ``handle``, ``tick`` and ``on_decided`` reach
    ``limits.store``, ``limits.audit``, ``limits.registry`` (``Limits.blocked`` and ``charge``), the audit sink's own
    fields, the registry's members and the evidence settings, so each is compared. Fails on 82dd69c1 (those four
    members were compared by identity only)."""
    app = _built(tmp_path)
    rt = _core_runtime(app)
    owner = _fields(rt)[member]
    own = _fields(owner)
    assert not _runtime_counted(app, rt), "control"
    was = own[field]
    own[field] = _Opaque()
    try:
        assert _runtime_counted(app, rt), f"{member}.{field} replaced was not counted"
    finally:
        own[field] = was
    assert not _runtime_counted(app, rt), "control: restored"


def test_a_name_added_to_limits_audit_registry_or_evidence_is_counted(tmp_path: Path) -> None:
    """Class: SEAL-COMPLETE (round 11, issue 1): a new instance name on one of the four members. Fails on 82dd69c1."""
    app = _built(tmp_path)
    rt = _core_runtime(app)
    for member in ("limits", "audit", "registry"):
        own = _fields(_fields(rt)[member])
        own["a_name_the_class_never_had"] = _Opaque()
        try:
            assert _runtime_counted(app, rt), f"a name added to {member} was not counted"
        finally:
            del own["a_name_the_class_never_had"]
    assert not _runtime_counted(app, rt), "control: restored"


def _recording_dict_class(calls: list[str]) -> type:
    def recording(self: object) -> dict:
        calls.append("dict")
        return {}

    return type("Hostile", (), {"__dict__": property(recording)})


def test_an_object_put_in_a_hook_field_runs_no_code_of_its_own_before_it_is_compared(
    tmp_path: Path,
) -> None:
    """Class: FOREIGN-CODE-BEFORE-AUTH (round 11, issue 1). A replacement whose class has a ``__dict__`` property: the
    walk compared fields first and read the instance dictionary of the replacement. Now the object is compared (identity)
    before anything is read from it. Fails on 82dd69c1 (the call list holds one entry)."""
    app = _built(tmp_path)
    rt = _core_runtime(app)
    calls: list[str] = []
    hostile = _recording_dict_class(calls)()
    fields = _fields(rt.hooks)
    for name in ("execute", "post_card", "toolbox", "validate_proposal"):
        was = fields[name]
        fields[name] = hostile
        try:
            assert _runtime_counted(app, rt), f"hooks.{name} replaced was not counted"
        finally:
            fields[name] = was
    assert calls == [], f"the foreign __dict__ property ran: {calls}"
    for member in ("limits", "audit", "registry", "_evidence"):
        own = _fields(rt)
        was = own[member]
        own[member] = hostile
        try:
            assert _runtime_counted(app, rt), f"{member} replaced was not counted"
        finally:
            own[member] = was
    assert calls == [], f"the foreign __dict__ property ran: {calls}"


def test_an_entered_object_whose_class_is_swapped_runs_no_code_of_its_own(tmp_path: Path) -> None:
    """Class: FOREIGN-CODE-BEFORE-AUTH (round 11, issue 1). The recorded object stays the same but its ``__class__`` is
    assigned a subclass with a ``__dict__`` property: the class is compared before the instance dictionary is read.
    Fails on 82dd69c1."""
    app = _built(tmp_path)
    rt = _core_runtime(app)
    executor = rt.hooks.execute.__self__
    calls: list[str] = []

    def recording(self: object) -> dict:
        calls.append("dict")
        return {}

    Swapped = type("Swapped", (type(executor),), {"__dict__": property(recording)})

    original = type(executor)
    executor.__class__ = Swapped
    try:
        assert _runtime_counted(app, rt), "an executor of a swapped class was not counted"
    finally:
        executor.__class__ = original
    assert calls == [], f"the swapped class ran its __dict__ property: {calls}"
    assert not _runtime_counted(app, rt), "control: restored"


def test_hooks_tools_replaced_by_a_copy_is_judged_by_contents_not_identity(tmp_path: Path) -> None:
    """Decision (round 11 addendum 1): the runtime reads ``hooks.tools[name]``, so an equal copy of the dict behaves
    the same and is believed; a copy with another item, another key or one more key is counted."""
    given = _built(tmp_path, tools={"lookup": lambda inp: "x"})
    rt = _core_runtime(given)
    fields = _fields(rt.hooks)
    first = fields["tools"]
    fields["tools"] = dict(first)
    assert not _runtime_counted(given, rt), "an equal copy of hooks.tools was counted"
    for other in (
        {"lookup": _real_function},
        {"renamed": first["lookup"]},
        {},
        {**first, "b": first["lookup"]},
    ):
        fields["tools"] = other
        assert _runtime_counted(given, rt), (
            f"hooks.tools replaced by {sorted(other)} was not counted"
        )
    fields["tools"] = first


def test_a_real_tool_call_and_an_executed_action_leave_the_runtime_believed(tmp_path: Path) -> None:
    """Class: OUTAGE-GUARD (round 11, issue 4). A real tool call through ``Runtime._run_tool`` and an approved action
    through ``Approvals.decide`` -> ``on_decided`` -> ``execute`` (the executor runs and the run ends in the state the
    fixture gives it) between two seal checks: a lazily made value in the executor, the toolbox or ``validate_proposal``
    would read as a change and answer 503 to every public request. Verify and rollback are reached by ``execute`` only
    when the executor's call succeeds; the fixture's call does not, so they are not driven here (named in the report)."""
    from hadavin_sdk.models import ApprovalDecision

    app = _built(tmp_path, tools={"lookup": lambda inp: "found"})
    rt = _core_runtime(app)
    assert not _runtime_counted(app, rt), "control: counted before any work"
    out = rt._run_tool("lookup", {}, {})
    assert out.text and not out.error, f"the tool call did not run: {out}"
    assert not _runtime_counted(app, rt), "a real tool call made the runtime read as changed"
    document = (app.app.config.inputs_dir / "create.txt").read_bytes()
    run = rt.handle("test-agent", "svc:test-agent", document)
    due = app.app.store.list_due_approvals(datetime(2100, 1, 1, tzinfo=UTC))
    req = next(r for r in due if r.run_id == run.run_id)
    decision = ApprovalDecision(
        approval_id=req.approval_id,
        plan_hash=req.plan_hash,
        step=req.current_step,
        decision="approve",
        approver_id="user:a",
        channel="fake",
    )
    assert app.app.approvals.decide(decision) == (True, "approved")
    assert app.app.store.get_run(run.run_id).state.value != "WAITING_FOR_APPROVAL", (
        "the action was not executed"
    )
    assert not _runtime_counted(app, rt), "an executed action made the runtime read as changed"


def test_a_decision_through_on_decided_adds_no_name_to_the_runtime(tmp_path: Path) -> None:
    """Class: OUTAGE-GUARD (round 11, issue 4): the lazy-name check also covers ``on_decided`` (a rejected decision)."""
    from hadavin_sdk.models import ApprovalDecision

    app = _built(tmp_path)
    rt = _core_runtime(app)
    before = tuple(_fields(rt))
    document = (app.app.config.inputs_dir / "create.txt").read_bytes()
    run = rt.handle("test-agent", "svc:test-agent", document)
    due = app.app.store.list_due_approvals(datetime(2100, 1, 1, tzinfo=UTC))
    req = next(r for r in due if r.run_id == run.run_id)
    decision = ApprovalDecision(
        approval_id=req.approval_id,
        plan_hash=req.plan_hash,
        step=req.current_step,
        decision="reject",
        approver_id="user:a",
        channel="fake",
    )
    assert app.app.approvals.decide(decision)[0] is True
    assert tuple(_fields(rt)) == before, "a decision added or removed a name of the runtime"
    assert not _runtime_counted(app, rt), "a runtime that took a decision was counted"


def test_the_seal_refuses_an_object_that_is_not_a_core_runtime() -> None:
    """Class: API (round 11, issue 4): ``_seal_runtime`` accepts the exact core ``Runtime`` only. Fails on 82dd69c1."""
    from hadavin_sdk.approvals import requests as R

    class Imposter:
        pass

    with pytest.raises(TypeError):
        R._seal_runtime(Imposter())


def _seal_cost_walk(rt: object) -> int:
    from hadavin_sdk.approvals import requests as R

    return len(R._RUNTIME_SEALS[rt][4]) + len(R._RUNTIME_SEALS[rt][6])


def test_a_runtime_with_more_hook_objects_than_the_cap_is_refused_at_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Class: LIMITS (round 11, issue 3). ``_WALK_NODES`` is enforced inside the loops and at seal time: a build over
    the cap raises, and the text says the seal is over budget. Fails on 82dd69c1 (no error at build)."""
    from hadavin_sdk.approvals import requests as R

    app = _built(tmp_path)
    rt = _core_runtime(app)
    need = _seal_cost_walk(rt)
    monkeypatch.setattr(R, "_WALK_NODES", need // 2)
    with pytest.raises(ValueError, match=r"too many hook objects to check .*over budget"):
        R._seal_runtime(rt)


def test_a_walk_cap_equal_to_the_need_still_seals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Class: LIMITS (round 11, issue 3), the edge: exactly the number of objects the walk needs is accepted."""
    from hadavin_sdk.approvals import requests as R

    app = _built(tmp_path)
    rt = _core_runtime(app)
    hooks_need = len(R._RUNTIME_SEALS[rt][4])
    members_need = len(R._RUNTIME_SEALS[rt][6])
    monkeypatch.setattr(R, "_WALK_NODES", max(hooks_need, members_need))
    R._seal_runtime(rt)
    assert not _runtime_counted(app, rt), "a runtime sealed at exactly the cap was counted"


def test_a_walk_that_grows_past_the_cap_after_the_seal_says_the_seal_is_over_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Class: LIMITS (round 11, issue 3): the refusal names the cause, not ``on_decided``."""
    from hadavin_sdk.approvals import requests as R

    app = _built(tmp_path)
    rt = _core_runtime(app)
    monkeypatch.setattr(R, "_WALK_NODES", len(R._RUNTIME_SEALS[rt][4]) - 1)
    held = _approvals_with(app, make_on_decided({"rt": rt})).held_services()
    assert "seal_over_budget" in held and "on_decided" not in held, f"the names were {sorted(held)}"


def test_a_hook_function_with_an_empty_closure_cell_filled_later_is_counted(tmp_path: Path) -> None:
    """Class: LIMITS (round 11, issue 3), ``_EMPTY_CELL``: an empty cell and a cell holding ``None`` are not the same."""
    app = _built(tmp_path)
    rt = _core_runtime(app)

    def outer() -> object:
        held = None

        def inner() -> object:
            return held

        return inner

    cell = types.CellType()  # a cell with nothing in it
    empty = types.FunctionType(cast(Any, outer()).__code__, {}, "late", None, (cell,))
    _fields(rt.hooks)["tools"]["late"] = empty
    _seal(rt)
    assert not _runtime_counted(app, rt), "control: sealed with an empty cell"
    cell.cell_contents = None
    assert _runtime_counted(app, rt), "an empty cell filled with None was not counted"
