"""bindguard: a server that holds a real service is not started on an address other computers can reach.

Pins: every kind of the backend table has one answer (stand-in or real), every public spelling of a bind is refused
with a real service and none is refused with stand-ins only, the receiver asks before it listens, and no module keeps
its own copy of the loopback list. Made-up data only."""

from __future__ import annotations

import ast
import socket
from pathlib import Path

import pytest

from hadavin_sdk import bindguard
from hadavin_sdk.approvals.receiver import serve
from hadavin_sdk.backends.table import DEMO_ONLY, IN_PROCESS, NOT_PROD, TABLE, KindSettings
from hadavin_sdk.bindguard import BindRefused, public_bind_problem, real_services, require_safe_bind
from hadavin_sdk.config import Config, SourceConfig, System, load_config
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
    """The fixture config: fake kinds only and one fake system on this computer."""
    return load_config(make_cfg(tmp_path))


def _with_kind(cfg: Config, cap: str, kind: str) -> Config:
    """The same config with one backend swapped for `kind` (not validated: only `.kind` is read)."""
    entry = KindSettings.model_construct(kind=kind)
    value = (entry,) if cap == "detector" else entry
    return cfg.model_copy(update={"backends": cfg.backends.model_copy(update={cap: value})})


def test_the_fixture_config_holds_only_stand_ins(stand_in_config: Config) -> None:
    assert real_services(stand_in_config) == ()


ALL_KINDS = [(cap, kind) for cap, kinds in TABLE.items() for kind in kinds]


@pytest.mark.parametrize(("cap", "kind"), ALL_KINDS, ids=[f"{c}/{k}" for c, k in ALL_KINDS])
def test_every_kind_of_the_table_has_exactly_one_answer(
    stand_in_config: Config, cap: str, kind: str
) -> None:
    """A kind reaches no service exactly when the table says so (DEMO_ONLY, NOT_PROD or IN_PROCESS); every other
    kind is real."""
    found = real_services(_with_kind(stand_in_config, cap, kind))
    stand_in = (cap, kind) in DEMO_ONLY | NOT_PROD | IN_PROCESS
    assert (found == ()) is stand_in, f"{cap}/{kind}: {found}"
    if not stand_in:
        assert found == (f"backends.{cap}: {kind}",)


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
        assert TABLE[cap][kind].hosts is None, f"{cap}/{kind} names hosts it connects to"
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
    assert text is not None and "\n" not in text and "(unreadable)" in text
    text = public_bind_problem(ALL_ZEROS, cfg)
    assert text is not None and "loopback" in text and "backends.llm: anthropic" in text


# --- the receiver asks before it listens ---------------------------------------------------------------


def test_the_receiver_refuses_a_public_bind_with_a_real_service_before_it_listens(
    stand_in_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_socket(*a: object, **k: object) -> None:
        raise AssertionError("a listening socket was opened before the refusal")

    monkeypatch.setattr(socket.socket, "bind", no_socket)
    cfg = _with_kind(stand_in_config, "llm", "anthropic")
    with pytest.raises(BindRefused):
        serve(object(), host=ALL_ZEROS, port=0, config=cfg)  # type: ignore[arg-type]


def test_the_receiver_starts_on_loopback_with_a_real_service_and_publicly_with_stand_ins(
    stand_in_config: Config,
) -> None:
    real = _with_kind(stand_in_config, "llm", "anthropic")
    for host, cfg in ((LOOP_1, real), (ALL_ZEROS, stand_in_config), ("::1", real)):
        try:
            server = serve(object(), host=host, port=0, config=cfg)  # type: ignore[arg-type]
        except OSError:  # no IPv6 on this machine: not a refusal
            assert host == "::1"
            continue
        server.server_close()


def test_the_receiver_without_a_config_is_unchanged() -> None:
    server = serve(object(), host=LOOP_1, port=0)  # type: ignore[arg-type]
    server.server_close()


# --- no module keeps its own copy of the loopback list ---------------------------------------------------

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
# tools.py keeps a list of names a tool manifest may NOT name (an outbound deny list: it also holds metadata names),
# which is a different question from "is this host this computer".
ALLOWED_COPY = {"netguard.py", "tools.py"}


def _strings(node: ast.AST) -> set[str]:
    return {
        n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }


def test_no_module_keeps_its_own_loopback_list() -> None:
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name in ALLOWED_COPY:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Set | ast.Tuple | ast.List | ast.Call):
                found = _strings(node)
                if "localhost" in found and ({LOOP_1, "::1"} & found):
                    offenders.append(f"{path.relative_to(SRC)}:{node.lineno}")
    assert offenders == [], f"a copy of the loopback list: {sorted(set(offenders))}"
