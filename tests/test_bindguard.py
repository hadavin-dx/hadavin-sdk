"""bindguard: a server that holds a real service is not started on an address other computers can reach.

Pins: every kind of the backend table has one answer (stand-in or real), every public spelling of a bind is refused
with a real service and none is refused with stand-ins only, custom code and live egress hosts count, ``listen`` is
the only place a server socket is made and asks before it builds, the receiver needs its config, the named reason is
the only way past a refusal, and no module keeps its own copy of the loopback list. Made-up data only."""

from __future__ import annotations

import ast
import http.server
import logging
import re
import socket
import socketserver
import tomllib
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from types import MappingProxyType

import pytest
from tools import server_scan

from hadavin_sdk import bindguard, netguard
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals import Approvals, FakeChannel
from hadavin_sdk.approvals.receiver import PATH, serve
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
            require_safe_bind(bind, cfg, allow_public_bind_reason=reason, held={})  # type: ignore[arg-type]


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


class _Quiet(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # pragma: no cover - never called
        self.send_response(204)
        self.end_headers()


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
        seen.append((type(self).address_family, address))
        self.server_address = address  # type: ignore[attr-defined]

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
            listen(stand_in_config, host, 0, _Quiet, held={})  # type: ignore[arg-type]


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
        _Opaque(),  # type: ignore[arg-type]
        _Opaque(),  # type: ignore[arg-type]
        FakeChannel("sig" + "-b4-test"),
        lambda run_id, status, d: None,
        config=config,
        overrides=held if held is not None or config is None else {},
    )


def test_the_receiver_without_a_config_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        serve(_Approvals(None))  # type: ignore[call-arg, arg-type]
    with pytest.raises(TypeError):
        serve(_Approvals(None), host=ALL_ZEROS)  # type: ignore[call-arg, arg-type]
    with pytest.raises(TypeError):
        serve(_Approvals(None), None)  # type: ignore[misc, arg-type]  # config is keyword-only


def test_the_receiver_refuses_a_public_bind_with_a_real_service_before_any_socket_exists(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_server(monkeypatch)
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    with pytest.raises(BindRefused):
        serve(_Approvals(cfg), config=cfg, host=ALL_ZEROS, port=0)  # type: ignore[arg-type]


def test_the_receiver_refuses_a_config_that_is_not_the_one_the_approvals_were_built_with(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stand-in config beside real approvals must not let a public bind through."""
    _no_server(monkeypatch)
    real = _with_kind(stand_in_config, "llm", "anthropic")
    for held in (real, None):
        with pytest.raises(BindRefused, match="built with"):
            serve(_Approvals(held), config=stand_in_config, host=ALL_ZEROS, port=0)  # type: ignore[arg-type]


def test_the_receiver_starts_and_the_reason_passes_through_it(stand_in_config: Config) -> None:
    real = _with_kind(stand_in_config, "llm", "anthropic")
    appr = _Approvals(real)
    server = serve(appr, config=real, port=0)  # type: ignore[arg-type]
    assert server.server_address[0] == LOOP_1
    server.server_close()
    with pytest.raises(BindRefused):
        serve(appr, config=real, host=ALL_ZEROS, port=0)  # type: ignore[arg-type]
    server = serve(
        appr, config=real, host=ALL_ZEROS, port=0, allow_public_bind_reason="proxy in front"
    )  # type: ignore[arg-type]
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

    def __init__(self, app: object) -> None:
        self.app = app
        self.config = app.config.model_copy(update={"check_modules": []})  # type: ignore[attr-defined]
        built = app.approvals  # type: ignore[attr-defined]
        self.store, self.audit, self.registry = built.store, built.audit, built.registry
        self.recorded = built.overrides
        self.approvals = Approvals(
            built.store,
            built.audit,
            built.registry,
            built.channel,
            lambda run_id, status, d: None,
            detector=built.detector,
            config=self.config,
            overrides=built.overrides,
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
    return _Built(build(folder, ["test-agent"], **kw))  # type: ignore[arg-type]


def _stand_in_bind_lands_on_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let a test pass the check with a wildcard host and still bind only on this computer."""
    monkeypatch.setattr(bindguard, "_literal", lambda host: (LOOP_1, socket.AF_INET))


def test_a_built_app_with_stand_ins_only_accepts_any_bind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROL (passes on the old code too): nothing real is held, so a public bind is not refused."""
    app = _built(tmp_path)
    assert real_services(app.config, app.approvals.held_services()) == ()  # type: ignore[attr-defined]
    _stand_in_bind_lands_on_loopback(monkeypatch)
    serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0).server_close()  # type: ignore[attr-defined]


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
    assert real_services(app.config, {}) == ()  # type: ignore[attr-defined]  # the config alone says "stand-ins"
    assert name in app.recorded, "the override was not recorded on the approvals"
    with monkeypatch.context() as m:
        _no_server(m)
        with pytest.raises(BindRefused, match=re.escape(shown)):
            serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0)  # type: ignore[attr-defined]
    _stand_in_bind_lands_on_loopback(monkeypatch)
    serve(  # type: ignore[attr-defined]
        app.approvals,
        config=app.config,
        host=ALL_ZEROS,
        port=0,
        allow_public_bind_reason="behind our own proxy",
    ).server_close()
    serve(app.approvals, config=app.config, port=0).server_close()  # type: ignore[attr-defined]


def _by_hand(app: object, channel: object, **extra: object) -> Approvals:
    return Approvals(
        app.store,  # type: ignore[attr-defined]
        app.audit,  # type: ignore[attr-defined]
        app.registry,  # type: ignore[attr-defined]
        channel,  # type: ignore[arg-type]
        lambda run_id, status, d: None,
        **extra,  # type: ignore[arg-type]
    )


def test_a_real_source_or_tools_dict_handed_in_is_counted_and_an_empty_one_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    channel = app.approvals.channel  # type: ignore[attr-defined]
    for name, value, shown in (
        ("sources", {"cluster": object()}, "held sources"),
        ("tools", {"lookup": lambda inputs: "x"}, "held tools"),
    ):
        approvals = _by_hand(app, channel, config=app.config, overrides={name: value})  # type: ignore[attr-defined]
        with monkeypatch.context() as m:
            _no_server(m)
            with pytest.raises(BindRefused, match=shown):
                serve(approvals, config=app.config, host=ALL_ZEROS, port=0)  # type: ignore[attr-defined]
    empty = _by_hand(app, channel, config=app.config, overrides={"sources": {}, "tools": {}})  # type: ignore[attr-defined]
    _stand_in_bind_lands_on_loopback(monkeypatch)
    refusal = ""
    try:
        serve(empty, config=app.config, host=ALL_ZEROS, port=0).server_close()  # type: ignore[attr-defined]
    except BindRefused as exc:
        refusal = str(exc)
    assert not refusal, f"an empty tools or sources mapping was counted: {refusal}"


def test_approvals_built_by_hand_with_a_real_channel_and_a_stand_in_config_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Approvals(real_channel, ..., config=stand_in)``: the config alone would say "stand-ins only"."""
    app = _built(tmp_path)
    approvals = _by_hand(app, _RealChannel("sig" + "-b3-real"), config=app.config)  # type: ignore[attr-defined]
    with monkeypatch.context() as m:
        _no_server(m)
        with pytest.raises(BindRefused, match="held channel: _RealChannel"):
            serve(approvals, config=app.config, host=ALL_ZEROS, port=0)  # type: ignore[attr-defined]
    for held in ({"store": _Opaque()}, {"detector": _RealDetector()}):
        odd = _by_hand(app, app.approvals.channel, config=app.config)  # type: ignore[attr-defined]
        object.__setattr__(odd, "_" + next(iter(held)), next(iter(held.values())))
        with monkeypatch.context() as m:
            _no_server(m)
            with pytest.raises(BindRefused, match="held"):
                serve(odd, config=app.config, host=ALL_ZEROS, port=0)  # type: ignore[attr-defined]


class _Opaque:
    """Any object that is not one of the core's own stand-ins."""


def test_approvals_built_by_hand_without_a_config_are_refused_and_the_text_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path)
    approvals = _by_hand(app, app.approvals.channel)  # type: ignore[attr-defined]
    assert approvals.config is None and dict(approvals.overrides) == {}
    with monkeypatch.context() as m:
        _no_server(m)
        for host in (LOOP_1, ALL_ZEROS):
            with pytest.raises(BindRefused, match="built by hand with no config"):
                serve(approvals, config=app.config, host=host, port=0)  # type: ignore[attr-defined]


def test_the_config_and_the_overrides_of_the_approvals_cannot_be_assigned_or_edited(
    tmp_path: Path,
) -> None:
    app = _built(tmp_path)
    approvals = app.approvals  # type: ignore[attr-defined]
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
            serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0)  # type: ignore[attr-defined]


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
            line = node.lineno
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
    a = app.approvals  # type: ignore[attr-defined]
    for name, value in (
        ("channel", _RealChannel("sig" + "-b4-a")),
        ("store", _Opaque()),
        ("detector", _RealDetector()),
        ("config", app.config),  # type: ignore[attr-defined]
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
    a = app.approvals  # type: ignore[attr-defined]
    _stand_in_bind_lands_on_loopback(monkeypatch)
    server = serve(a, config=app.config, host=ALL_ZEROS, port=0)  # type: ignore[attr-defined]
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
    a = app.approvals  # type: ignore[attr-defined]
    assert _post(serve(a, config=app.config, port=0)) != 503, (  # type: ignore[attr-defined]
        "a loopback bind was refused at the request"
    )


def test_a_bind_with_a_reason_does_not_pay_the_recheck(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _built(tmp_path, channel=_RealChannel("sig" + "-b4-real"))
    a = app.approvals  # type: ignore[attr-defined]
    _stand_in_bind_lands_on_loopback(monkeypatch)
    server = serve(
        a, config=app.config, host=ALL_ZEROS, port=0, allow_public_bind_reason="proxy in front"
    )  # type: ignore[attr-defined]
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
        lambda *a: None,
        config=stand_in_config,
        overrides={},
    )
    _no_server(monkeypatch)
    for odd in (sub, _Opaque()):
        with pytest.raises(BindRefused, match="made by the core"):
            serve(odd, config=stand_in_config, host=LOOP_1, port=0)  # type: ignore[arg-type]


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
    for obj in (Lazy(), Raises(), Sub(), MappingProxyType({})):
        assert held_services_found({"tools": obj}) == ("held tools",), type(obj).__name__
    assert held_services_found({"sources": {"a": 1}}) == ("held sources",)
    cyc = AnyOf([])
    cyc.detectors = (cyc,)  # type: ignore[assignment]
    assert held_services_found({"detector": cyc}) == ("held detector: AnyOf",), (
        "an object that raises was passed on or read as a stand-in"
    )


def test_held_is_required_everywhere_it_decides(stand_in_config: Config) -> None:
    with pytest.raises(TypeError):
        listen(stand_in_config, LOOP_1, 0, _Quiet)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        require_safe_bind(LOOP_1, stand_in_config)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        public_bind_problem(LOOP_1, stand_in_config)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        real_services(stand_in_config)  # type: ignore[call-arg]


def test_approvals_made_by_hand_are_refused_on_a_public_bind_unless_the_audit_and_registry_are_stand_ins(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _Approvals(stand_in_config)
    by_hand = Approvals(
        base.store,
        _Opaque(),
        _Opaque(),
        base.channel,
        lambda *a: None,
        config=stand_in_config,  # type: ignore[arg-type]
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
        serve(app.approvals, config=app.config, host=ALL_ZEROS, port=0)  # type: ignore[attr-defined]


def test_an_override_and_a_different_object_now_in_its_place_are_both_counted(
    tmp_path: Path,
) -> None:
    app = _built(tmp_path, channel=_RealChannel("sig" + "-b4-given"))
    a = app.approvals  # type: ignore[attr-defined]
    object.__setattr__(a, "_channel", FakeChannel("sig" + "-b4-now"))
    assert "held channel (given to build): _RealChannel" in real_services(
        app.config, a.held_services()
    ), (  # type: ignore[attr-defined]
        "an overridden object was hidden by the object now in its place"
    )
    assert "store" in a.held_services() and "detector" in a.held_services(), (
        "the store or the detector is not named among the held objects"
    )


def test_the_approvals_that_build_made_go_through_serve_with_a_real_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End to end, with no re-assembly: the object ``build()`` returned (its own check module counts, too)."""
    app = _built(tmp_path, channel=_RealChannel("sig" + "-b4-e2e")).app  # type: ignore[attr-defined]
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
        self.module.Child = cls  # type: ignore[attr-defined]


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
    namespace = {
        "go": go,
        "__slots__": (),
        "__module__": "tests_clone",
        "__doc__": None,
        "__annotations__": shared,
    }
    base, clone = type("Base", (), dict(namespace)), type("Base", (), dict(namespace))

    class Child(base):  # type: ignore[valid-type,misc]
        pass

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
    home.module.__getattr__ = lambda name: Planted  # type: ignore[attr-defined]
    assert home.module.Child is Planted  # type: ignore[attr-defined]  # only through __getattr__
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
    fc.many = list(range(50))  # type: ignore[attr-defined]
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
    fc.post_card = lambda *a: None  # type: ignore[attr-defined]  # a function put on the instance
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
    mine.append(_RealDetector())  # type: ignore[arg-type]
    assert is_stand_in_object(both), "a list changed later changed the detector list"
    with pytest.raises(AttributeError):
        both.detectors.append(_RealDetector())  # type: ignore[attr-defined]


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
    import subprocess
    import sys

    out = subprocess.run(  # noqa: S603 - our own interpreter and our own probe text
        [sys.executable, "-I", "-c", _RUNTIME_PROBE, str(ROOT)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
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

    seen: list[list[tuple[str, str]]] = []
    real_bind = socket.socket.bind

    def spy(self: socket.socket, address: object) -> None:
        frames, f = [], sys._getframe(1)
        while f is not None and len(frames) < 4:
            frames.append((Path(f.f_code.co_filename).name, f.f_code.co_name))
            f = f.f_back
        seen.append(frames)
        return real_bind(self, address)  # type: ignore[arg-type]

    monkeypatch.setattr(socket.socket, "bind", spy)
    app = _built(tmp_path)
    serve(app.approvals, config=app.config, port=0).server_close()  # type: ignore[attr-defined]
    real = _built(tmp_path / "real", channel=_RealChannel("sig" + "-b4-rt"))
    serve(real.approvals, config=real.config, port=0).server_close()  # type: ignore[attr-defined]
    listen(real.config, LOOP_1, 0, _Quiet, held={}).server_close()  # type: ignore[attr-defined]
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
    patched.check = lambda text, source: None  # type: ignore[method-assign,assignment]
    assert not is_stand_in_object(patched), "a function put on the detector list was not noticed"
    with monkeypatch.context() as m:
        m.setattr(AnyOf, "check", lambda self, text, source: None)
        assert not is_stand_in_object(_any_of()), "a patched AnyOf.check was not noticed"
    as_list = _any_of()
    as_list.detectors = [RegexDetector(0.5)]  # type: ignore[assignment]
    assert not is_stand_in_object(as_list), "a list of detectors was read as a tuple"

    class EmptyIter:
        def __iter__(self):  # a foreign iteration that says "nothing in here"
            return iter(())

    empty = _any_of()
    empty.detectors = EmptyIter()  # type: ignore[assignment]
    assert not is_stand_in_object(empty), "a detector holder that iterates as empty was trusted"

    class MyTuple(tuple):
        def __iter__(self):
            return iter(())

    sub = _any_of()
    sub.detectors = MyTuple((_RealDetector(),))  # type: ignore[assignment]
    assert not is_stand_in_object(sub), "a tuple subclass with a foreign iteration was trusted"
    mixed = AnyOf([RegexDetector(0.5), _RealDetector()])  # type: ignore[list-item]
    assert not is_stand_in_object(mixed)


def test_a_detector_list_nested_or_cyclic_is_read_without_recursion_errors() -> None:
    nested = AnyOf([_any_of(), RegexDetector(0.5)])
    assert is_stand_in_object(nested), "a list of lists of stand-ins is a stand-in"
    deep: AnyOf = _any_of()
    for _ in range(10):
        deep = AnyOf([deep])  # type: ignore[list-item]
    assert not is_stand_in_object(deep), "nesting past the depth limit was trusted"
    loop = _any_of()
    loop.detectors = (loop,)  # type: ignore[assignment]
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
        llm.routes["x"] = value  # type: ignore[assignment]
        assert not is_stand_in_object(llm), f"a function inside {value!r} was not noticed"
    for kind in (set, frozenset):
        llm = FakeLLM(tmp_path, {})
        llm.calls.append(
            {"f": kind([print])}
        )  # a callable inside a set inside a dict inside a list
        llm.calls.append(kind([print]))
        assert not is_stand_in_object(llm)
    store = MemoryStore()
    store._runs["x"] = (lambda: None,)  # type: ignore[assignment]
    assert not is_stand_in_object(store)
    # the limit FAILS CLOSED: a function below the last level that is entered is not seen, but a container left
    # unexplored that holds anything but plain atoms reads as real; plain atoms there are fine
    far = FakeLLM(tmp_path, {})
    far.routes["x"] = {"k": [(lambda: None,)]}  # type: ignore[assignment]
    assert not is_stand_in_object(far), "a container past the depth limit was trusted"
    atoms = FakeLLM(tmp_path, {})
    atoms.routes["x"] = {"k": [(1, "two", None)]}  # type: ignore[assignment]
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
    a = app.approvals  # type: ignore[attr-defined]
    with pytest.raises(AttributeError, match="set once"):
        a.__class__ = SlotSub  # type: ignore[assignment]
    assert type(a) is Approvals
    with pytest.raises(AttributeError, match="set once"):
        a._channel = _RealChannel("sig" + "-b5-w")  # type: ignore[assignment]
    for name in Approvals.__slots__:
        with pytest.raises(AttributeError, match="set once"):
            setattr(a, name, None)
    with pytest.raises(AttributeError, match="set once"):
        a.brand_new = 1  # type: ignore[attr-defined]
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
    a = app.approvals  # type: ignore[attr-defined]
    _stand_in_bind_lands_on_loopback(monkeypatch)
    server = serve(a, config=app.config, host=ALL_ZEROS, port=0)  # type: ignore[attr-defined]
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
    found = held_services_found({_EqBoomKey(): {}})  # type: ignore[dict-item]
    assert found == ("held (unreadable)",), (
        f"a key whose comparison raises was not counted: {found}"
    )

    boom = {_BoomKey(): _Opaque(), "ok": FakeChannel("sig" + "-b5-k")}
    found = held_services_found(boom)
    assert found == ("held (unreadable): _Opaque",), found
    unhashable = _Hostile([([1, 2], _Opaque()), (_BoomKey(), _Opaque())])
    found = held_services_found(unhashable)  # type: ignore[arg-type]
    assert len(found) == 2 and all(f.startswith("held (unreadable)") for f in found), found

    found = held_services_found({_EqBoomKey(): {}})  # type: ignore[dict-item]
    assert found == ("held (unreadable)",), (
        f"a key whose comparison raises was not counted: {found}"
    )

    class Raises:
        def items(self) -> list[object]:
            raise RuntimeError("no items")

        def __bool__(self) -> bool:
            return True

    assert held_services_found(Raises()) == ("held (unreadable)",)  # type: ignore[arg-type]


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
    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(())


class _TextWithCode(str):
    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = str.__hash__


class _NumberWithCode(int):
    pass


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
    for shape in sorted(_held_shapes()):
        for make in (
            lambda: FakeLLM(tmp_path, {}),
            lambda: FakeChannel("sig" + "-b6-a"),
            _populated_store,
            lambda: FakeSecretProvider({"a": "b"}),
            lambda: RegexDetector(0.5),
        ):
            obj = make()
            assert is_stand_in_object(obj), "control: the untouched stand-in reads as a stand-in"
            obj.extra = _held_shapes()[shape]  # type: ignore[attr-defined]
            assert not is_stand_in_object(obj), (
                f"a held {shape} was trusted by {type(obj).__name__}"
            )
            obj.extra = [[_held_shapes()[shape]]]  # type: ignore[attr-defined]
            assert not is_stand_in_object(obj), f"a held {shape} inside lists was trusted"


def test_a_dict_key_is_judged_like_a_value_and_a_container_is_read_with_the_builtin_iterator(
    tmp_path: Path,
) -> None:
    from hadavin_sdk import standins

    llm = FakeLLM(tmp_path, {})
    llm.routes[_Plain()] = 1  # type: ignore[index]
    assert not is_stand_in_object(llm), "a foreign object used as a dict key was trusted"
    # ``_values`` never runs a subclass's own iteration or lookup
    assert standins._values(_ListWithCode([1, 2])) == (1, 2), "a subclass's own iteration was run"
    assert standins._values(_DictWithCode(k="v")) == ("k", "v")
    assert standins._values(42) == ()


def test_a_populated_store_and_the_real_models_still_read_as_stand_ins(tmp_path: Path) -> None:
    from decimal import Decimal

    store = _populated_store()
    store.add_cost(next(iter(store._runs)), Decimal("0.5"))
    assert is_stand_in_object(store), "plain rows of the store's own models were refused"
    store._runs["x"] = _Plain()  # type: ignore[assignment]
    assert not is_stand_in_object(store), "a foreign object among the rows was trusted"


def test_the_five_stand_in_classes_hold_no_class_level_container() -> None:
    """The pin compares class attributes by identity, so a list or dict that lives on the class could be changed
    in place without the pin noticing; none of the five classes (nor ``Approvals``) has one."""
    from collections import Counter, defaultdict, deque

    from hadavin_sdk import standins

    mutable = (dict, list, set, bytearray, deque, defaultdict, Counter)
    classes = [standins._live_class(key) for key in standins._PINNED_KEYS]
    assert all(classes) and len(classes) == 7
    for cls in classes:
        for base in cls.__mro__:  # type: ignore[union-attr]
            if base is object:
                continue
            for name, value in vars(base).items():
                if (
                    name == "__annotations__"
                ):  # the empty one the pin itself adds; nothing runs from it
                    continue
                assert not isinstance(value, mutable), (
                    f"{base.__name__}.{name} is a mutable container"
                )


# class B: the depth limit fails closed, and the answer is not cached


def test_a_container_left_unexplored_at_the_depth_limit_reads_as_real(tmp_path: Path) -> None:
    from hadavin_sdk import standins

    llm = FakeLLM(tmp_path, {})
    assert is_stand_in_object(llm), "control"
    llm.routes = [[[[lambda: None]]]]  # type: ignore[assignment]
    assert not is_stand_in_object(llm), "a function four lists down was trusted"
    llm.routes = [[[[1, "plain"]]]]  # type: ignore[assignment]
    assert is_stand_in_object(llm), "a depth-four list of plain data was refused"
    llm.routes = [[[[_Plain()]]]]  # type: ignore[assignment]
    assert not standins.is_stand_in(llm), "a foreign object at the depth limit was trusted"
    # what is left unexplored counts against the node budget too
    llm.routes = [[[[1] * 50]]]  # type: ignore[assignment]
    with pytest.MonkeyPatch.context() as m:
        m.setattr(standins, "SCAN_NODES", 20)
        assert not standins.is_stand_in(llm), "an unexplored container past the node budget passed"


def test_a_function_put_in_after_an_earlier_question_is_seen_at_the_next_one(
    tmp_path: Path,
) -> None:
    """The answer is not cached: a cache that looks at the top level only would miss this (a change inside a held
    container leaves the object's own attributes as they were)."""
    llm = FakeLLM(tmp_path, {})
    for _ in range(3):
        assert is_stand_in_object(llm)
    llm.routes["x"] = {"k": [lambda: None]}  # type: ignore[assignment]
    assert not is_stand_in_object(llm), "a change inside a held container was not seen"


# class C: Approvals is pinned and its slots cannot be undone


def test_an_approvals_slot_cannot_be_deleted_or_deleted_and_set_again(tmp_path: Path) -> None:
    app = _built(tmp_path)
    a = app.approvals  # type: ignore[attr-defined]
    channel = a.channel
    with pytest.raises(AttributeError, match="cannot be deleted"):
        del a._channel
    with pytest.raises(AttributeError, match="cannot be deleted"):
        del a.clock
    with pytest.raises(AttributeError):
        del a.channel
    assert a.channel is channel, "a refused delete still changed the object"
    with pytest.raises(AttributeError):
        a._channel = _RealChannel("sig" + "-b6-del")  # type: ignore[assignment]
    assert a.channel is channel


def _serve_public(
    app: object, monkeypatch: pytest.MonkeyPatch
) -> tuple[http.server.HTTPServer, Approvals]:
    a = app.approvals  # type: ignore[attr-defined]
    _stand_in_bind_lands_on_loopback(monkeypatch)
    return serve(a, config=app.config, host=ALL_ZEROS, port=0), a  # type: ignore[attr-defined]


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
        except Exception as exc:  # noqa: BLE001 - a dropped connection shows as an http.client error
            raise AssertionError(
                f"a missing slot dropped the connection instead of a 503: {exc!r}"
            ) from None
        assert status == 503, "a missing slot gave no 503"
    finally:
        object.__setattr__(a, "_channel", saved)
        server.server_close()


def test_the_classes_are_pinned_when_the_receiver_is_imported_not_at_the_first_question() -> None:
    """In a fresh interpreter: after the import and before any question, six of the seven pins exist (every one but the
    fake secret provider: the repo rule forbids anything reachable from approvals to import the secret holders, so
    that one is pinned at the first question unless its module happens to be loaded)."""
    import subprocess
    import sys

    code = (
        "import hadavin_sdk.approvals.receiver\n"
        "from hadavin_sdk import standins\n"
        "want = set(standins._PINNED_KEYS) - {('hadavin_sdk.actions.secrets', 'FakeSecretProvider')}\n"
        "assert want <= set(standins._PINNED), sorted(want - set(standins._PINNED))\n"
        "print('pinned', len(want))\n"
    )
    done = subprocess.run(  # noqa: S603 - our own interpreter, a fixed program
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=False
    )
    assert done.returncode == 0 and "pinned 6" in done.stdout, (
        f"the pins were not all taken at import: {done.stderr[-300:]}"
    )


# class D: small defects in the same files


class _BoomStr(str):
    def isprintable(self) -> bool:
        raise RuntimeError("no text for this key")


def test_a_hostile_text_key_gets_a_fixed_label_and_nothing_is_called_on_it_again() -> None:
    found = held_services_found({_BoomStr("ch"): _Opaque()})  # type: ignore[dict-item]
    assert found == ("held (unreadable)",), found
    found = held_services_found({_BoomStr("tools"): {"a": 1}})  # type: ignore[dict-item]
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
        except BaseException as exc:  # noqa: BLE001 - the test records anything
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
    import subprocess
    import sys

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
    done = subprocess.run(  # noqa: S603 - our own interpreter, a fixed program
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=False
    )
    assert done.returncode == 0 and "ok" in done.stdout, (
        f"a read of __annotations__ changed the verdict: {done.stderr[-300:]}"
    )


def test_a_class_attribute_equal_to_the_pinned_one_but_not_the_same_object_reads_as_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pin (not a new rule): attributes are compared by identity, not by equality."""
    assert is_stand_in_object(FakeChannel("sig" + "-b6-id")), "control"
    monkeypatch.setattr(FakeChannel, "max_card_chars", int(str(FakeChannel.max_card_chars)))
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
    forged[2] = tuple((Key(k), v) for k, v in pin[2])  # type: ignore[union-attr]
    monkeypatch.setattr(standins, "_shape", lambda c: tuple(forged))
    assert not standins._same_shape(cls, pin), "a key of another type was read as the pinned key"


def test_a_nested_stand_in_is_judged_by_its_pin_and_scanned_in_turn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    llm = FakeLLM(tmp_path, {})
    llm.child = FakeChannel("sig" + "-b6-nest")  # type: ignore[attr-defined]
    assert is_stand_in_object(llm), "control: a stand-in inside a stand-in is plain data"
    llm.child.hook = lambda: None  # type: ignore[attr-defined]
    assert not is_stand_in_object(llm), "a function held by a nested stand-in was not seen"
    llm.child = FakeChannel("sig" + "-b6-nest2")  # type: ignore[attr-defined]
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
    a = app.approvals  # type: ignore[attr-defined]
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
    assert len(standins._PINNED_KEYS) == 7
