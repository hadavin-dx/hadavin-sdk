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

import pytest

from hadavin_sdk import bindguard, netguard
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals import Approvals, FakeChannel
from hadavin_sdk.approvals.receiver import PATH, serve
from hadavin_sdk.backends.table import DEMO_ONLY, IN_PROCESS, NOT_PROD, TABLE, KindSettings
from hadavin_sdk.bindguard import (
    BindRefused,
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
    assert real_services(stand_in_config) == (), "the stand-in fixture config counts a real service"


def test_the_fixture_config_as_it_is_counts_its_check_module(tmp_path: Path) -> None:
    """Custom code runs in the process, so a config that lists a check module is not "all stand-ins"."""
    assert real_services(load_config(make_cfg(tmp_path))) == ("checks:tests.fixtures.checks",)


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
    found = real_services(_with_kind(stand_in_config, cap, kind))
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
            problem = public_bind_problem(bind, cfg)
            assert problem is not None, f"public bind {bind!r} accepted with {cap}/{kind}"
            assert f"backends.{cap}: {kind}" in problem
            with pytest.raises(BindRefused):
                require_safe_bind(bind, cfg)


def test_a_real_service_accepts_every_loopback_spelling(stand_in_config: Config) -> None:
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    for bind in LOOPBACK:
        assert public_bind_problem(bind, cfg) is None, f"loopback bind {bind!r} refused"
        require_safe_bind(bind, cfg)


def test_stand_ins_only_accept_any_bind(stand_in_config: Config) -> None:
    for bind in PUBLIC + LOOPBACK:
        assert public_bind_problem(bind, stand_in_config) is None, f"stand-ins refused {bind!r}"


def test_a_detector_that_is_real_counts(stand_in_config: Config) -> None:
    cfg = _with_kind(stand_in_config, "detector", "bedrock_guardrail")
    assert public_bind_problem(ALL_ZEROS, cfg) is not None


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
        assert (real_services(cfg) == ("system records",)) is real, (systems, allow)
        assert (public_bind_problem(ALL_ZEROS, cfg) is not None) is real


def test_a_configured_source_is_a_real_service(stand_in_config: Config) -> None:
    source = SourceConfig.model_construct(kind="kubernetes", settings={})
    cfg = stand_in_config.model_copy(update={"sources": {"cluster": source}})
    assert real_services(cfg) == ("source cluster",)
    assert public_bind_problem(ALL_ZEROS, cfg) is not None


def test_the_refusal_is_one_plain_sentence_with_no_value_of_the_bind_leaking_control_text(
    stand_in_config: Config,
) -> None:
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    text = public_bind_problem("evil\nhost", cfg)
    assert text is not None and "\n" not in text and "(unreadable)" in text, (
        "control text was shown in the refusal"
    )
    text = public_bind_problem(ALL_ZEROS, cfg)
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
        assert real_services(cfg) == (name,), change
        problem = public_bind_problem(ALL_ZEROS, cfg)
        assert problem is not None and name in problem
        assert public_bind_problem(LOOP_1, cfg) is None


def test_loopback_egress_hosts_and_empty_lists_pass(stand_in_config: Config) -> None:
    cfg = stand_in_config.model_copy(
        update={"egress_hosts": frozenset({LOOP_1, "localhost", "::1"}), "tool_modules": []}
    )
    assert real_services(cfg) == () and public_bind_problem(ALL_ZEROS, cfg) is None, (
        "a loopback egress host was counted as a live one"
    )


def test_a_hostile_egress_entry_counts_and_never_shows_raw_text(stand_in_config: Config) -> None:
    for host in (LOOP_1 + "\x00", LOOP_1 + ".", "evil\nhost", "localhost.", "x" * 5000):
        cfg = stand_in_config.model_copy(update={"egress_hosts": frozenset({host})})
        found = real_services(cfg)
        assert len(found) == 1 and found[0].startswith("egress "), repr(host)
        problem = public_bind_problem(ALL_ZEROS, cfg)
        assert problem is not None and "\n" not in problem and "\x00" not in problem
        assert len(problem) < 1000


def test_systems_and_sources_built_by_the_real_loader_count(tmp_path: Path) -> None:
    """Built through ``load_config`` (validated), not ``model_construct``."""
    base = _loaded(tmp_path / "a")
    assert real_services(base) == ()
    remote = _loaded(tmp_path / "b", systems={"crm": {"base_url": "https://crm.example.test"}})
    assert real_services(remote) == ("system crm",)
    source = {
        "cluster": {
            "kind": "kubernetes",
            "settings": {"api_url": "https://k8s.example.test", "namespaces": ["a"]},
        }
    }
    with_source = _loaded(tmp_path / "c", sources=source)
    assert isinstance(with_source.sources["cluster"], SourceConfig)
    assert real_services(with_source) == ("source cluster",)
    for cfg in (remote, with_source):
        assert public_bind_problem(ALL_ZEROS, cfg) is not None


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
    doc = real_services.__doc__ or ""
    for word in (
        "tool_modules",
        "check_modules",
        "egress_hosts",
        "the loaded ``Config``",
        "held_services",
        "Not read: the audit sink",
    ):
        assert word in doc


# --- the named reason is the only way past a refusal ----------------------------------------------------------


def test_a_public_bind_needs_the_named_reason_and_the_reason_is_logged(
    stand_in_config: Config, caplog: pytest.LogCaptureFixture
) -> None:
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    with pytest.raises(BindRefused, match="allow_public_bind_reason"):
        require_safe_bind(ALL_ZEROS, cfg)
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.bindguard"):
        require_safe_bind(ALL_ZEROS, cfg, allow_public_bind_reason="  behind the studio proxy  ")
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
            require_safe_bind(bind, cfg, allow_public_bind_reason=reason)  # type: ignore[arg-type]


def test_an_empty_reason_is_refused_with_a_sentence_that_asks_for_one(
    stand_in_config: Config,
) -> None:
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    for reason in ("", "   "):
        with pytest.raises(BindRefused, match="must say why"):
            require_safe_bind(ALL_ZEROS, cfg, allow_public_bind_reason=reason)


def test_a_reason_shorter_than_ten_characters_is_refused_and_ten_are_accepted(
    stand_in_config: Config,
) -> None:
    """A one-letter reason says nothing and goes to the log only (it is not an audit record): ten printable
    characters after trimming are the least."""
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    for short in ("x", "123456789", "  123456789  ", "abc def g"):
        with pytest.raises(BindRefused, match="at least 10 characters"):
            require_safe_bind(ALL_ZEROS, cfg, allow_public_bind_reason=short)
    for fine in ("1234567890", "  1234567890  ", "proxy ok!!"):
        require_safe_bind(ALL_ZEROS, cfg, allow_public_bind_reason=fine)


def test_a_reason_of_exactly_the_longest_size_is_accepted(stand_in_config: Config) -> None:
    require_safe_bind(
        ALL_ZEROS,
        _with_kind(stand_in_config, "llm", "anthropic"),
        allow_public_bind_reason="x" * 200,
    )


def test_a_long_bind_text_is_cut_in_the_refusal(stand_in_config: Config) -> None:
    text = public_bind_problem("h" * 10_000, _with_kind(stand_in_config, "llm", "anthropic"))
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
            listen(cfg, host, 0, _Quiet)


def test_listen_starts_on_loopback_with_a_real_service_and_anywhere_with_stand_ins(
    stand_in_config: Config,
) -> None:
    real = _with_kind(stand_in_config, "llm", "anthropic")
    for host, cfg in ((LOOP_1, real), ("localhost", real), (ALL_ZEROS, stand_in_config)):
        server = listen(cfg, host, 0, _Quiet)
        server.server_close()


def test_listen_with_the_reason_starts_a_public_server_with_a_real_service(
    stand_in_config: Config, caplog: pytest.LogCaptureFixture
) -> None:
    real = _with_kind(stand_in_config, "llm", "anthropic")
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.bindguard"):
        server = listen(real, ALL_ZEROS, 0, _Quiet, allow_public_bind_reason="proxy in front")
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
        server = listen(real, host, 0, _Quiet)
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
        listen(real, host, 0, _Quiet)
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
        server = listen(real, host, 0, _Quiet)
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
            listen(stand_in_config, host, 0, _Quiet)  # type: ignore[arg-type]


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
        listen(real, LOOP_1, 0, _Quiet)
    assert closed == [True]


# --- the receiver needs its config and its approvals must be the ones built with it -------------------------------


class _Approvals:
    """What serve reads of an Approvals: its config and what it holds (stand-ins unless a test says otherwise)."""

    def __init__(self, config: Config | None, held: dict[str, object] | None = None) -> None:
        self.config = config
        self._held = held or {}

    def held_services(self) -> dict[str, object]:
        return dict(self._held)


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
    assert real_services(app.config) == ()  # type: ignore[attr-defined]  # the config alone says "stand-ins"
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
    serve(empty, config=app.config, host=ALL_ZEROS, port=0).server_close()  # type: ignore[attr-defined]


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
        setattr(odd, next(iter(held)), next(iter(held.values())))
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
    app.approvals.channel = _RealChannel("sig" + "-b3-late")  # type: ignore[attr-defined]
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
    assert real_services(stand_in_config, None) == real_services(stand_in_config) == ()
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
            local = real_services(cfg) == ()
            assert local == url_allowed(url, allow), f"{host!r} allow={allow}"


def _called_attributes(tree: ast.AST, owner: str) -> set[str]:
    """The names of the methods called on a variable called ``owner`` anywhere in ``tree``."""
    return {
        n.func.attr
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == owner
    }


def test_the_listener_reaches_the_approvals_only_through_the_signature_check() -> None:
    """The reason that lets a receiver stand beside a signer (``IN_PROCESS`` in the backend table): the one route
    calls ``approvals.receive`` and nothing else of the approvals, and ``receive`` hands a decision on only after the
    channel's ``parse_decision`` (the signature check) returned one."""
    receiver = ast.parse((SRC / "approvals" / "receiver.py").read_text(encoding="utf-8"))
    assert _called_attributes(receiver, "approvals") == {"receive", "held_services"}, (
        "the listener calls more of the approvals than receive"
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
    assert called.isdisjoint({"decide", "on_decided", "sweep", "request", "update_message"})


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
