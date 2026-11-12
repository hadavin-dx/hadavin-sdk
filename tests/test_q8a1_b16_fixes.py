"""Round 16 of Q8a-1: the fixes of this round, each with a test that fails on the code of round 15 (head c098aacf). Every
test is free of `conftest` fixtures so that the mutant runner can use it. A marker that must never be shown is built
from parts so that it is no secret-shaped literal."""

from __future__ import annotations

import sys

import pytest

from tests.k5_support import TOOL, k5_cfg


def _marker(tag: str) -> str:
    return "zq-b16-" + tag + "-" + "Wm4"


# ---- Issue 1: `check-config` never runs a tool module ---------------------------------------------------------------------

_SIDE_EFFECT_MODULE = """\
import os

with open(os.environ["B16_TOOL_MARKER"], "w", encoding="utf-8") as _f:
    _f.write("the tool module ran")

READ_OPERATIONS = {"bundle.read": ("GET", r"/.*")}


def read_logs(args, ctx):
    return "x"
"""


def _config_naming_a_tool_module(tmp_path, monkeypatch):
    mods = tmp_path / "mods"
    mods.mkdir()
    (mods / "zzb16_tool.py").write_text(_SIDE_EFFECT_MODULE, encoding="utf-8")
    marker = tmp_path / "ran.txt"
    monkeypatch.setenv("B16_TOOL_MARKER", str(marker))
    monkeypatch.syspath_prepend(str(mods))
    monkeypatch.delitem(sys.modules, "zzb16_tool", raising=False)
    cfg = k5_cfg(
        tmp_path / "cfg",
        tools=[{**TOOL, "function": "zzb16_tool:read_logs"}],
        config={"tool_modules": ["zzb16_tool"]},
    )
    return cfg, marker


def test_check_config_does_not_run_a_tool_module(tmp_path, monkeypatch, capsys):
    from hadavin_sdk import cli
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    cfg, marker = _config_naming_a_tool_module(tmp_path, monkeypatch)
    # control: the way `tick` loads the registry DOES run the module, so this probe can see a side effect
    load_registry(load_config(cfg))
    assert marker.exists(), "control: loading the registry must run the tool module (the probe is blind)"
    marker.unlink()
    monkeypatch.delitem(sys.modules, "zzb16_tool", raising=False)

    code = cli.main(["--config", str(cfg), "check-config"])
    seen = capsys.readouterr()
    assert code == 0, seen.err
    assert not marker.exists(), "check-config ran a tool module (client code)"
    assert "zzb16_tool" not in sys.modules, "check-config imported a tool module"


def test_check_config_says_what_it_did_not_check(tmp_path, monkeypatch, capsys):
    from hadavin_sdk import cli

    cfg, _ = _config_naming_a_tool_module(tmp_path, monkeypatch)
    assert cli.main(["--config", str(cfg), "check-config"]) == 0
    out = capsys.readouterr().out
    assert "Not checked" in out and "tool module code is not run" in out, (
        "check-config must say what it did not check"
    )


def test_check_config_still_refuses_a_tool_with_no_module_in_tool_modules(
    tmp_path, monkeypatch, capsys
):
    from hadavin_sdk import cli

    cfg, marker = _config_naming_a_tool_module(tmp_path, monkeypatch)
    cfg2 = k5_cfg(
        tmp_path / "cfg2",
        tools=[{**TOOL, "function": "zzb16_tool:read_logs"}],
        config={"tool_modules": []},
    )
    assert cli.main(["--config", str(cfg2), "check-config"]) == 2
    assert "outside tool_modules" in capsys.readouterr().err
    assert not marker.exists()


def test_check_config_exit_codes_are_those_of_main_and_tick(tmp_path, monkeypatch, capsys):
    from hadavin_sdk import cli

    def boom(*a, **k):
        raise RuntimeError(_marker("exit"))

    from tests.conftest import make_cfg

    monkeypatch.setattr(cli, "load_registry", boom)
    assert cli.main(["--config", str(make_cfg(tmp_path)), "check-config"]) == 3
    seen = capsys.readouterr()
    assert "RuntimeError" in seen.err and _marker("exit") not in seen.err + seen.out


# ---- Issue 6: ids and file names ---------------------------------------------------------------------------------------

_EVENT = {"run_id": "r", "domain": "d", "operation": "o", "principal": "p", "source": "s"}
# the six inputs of the independent evidence (probe 5) and the siblings found in this round
_HOSTILE_EVENT_IDS = ("../x", "..\\x", "/etc/x", "a/b", ".hidden", "a b", "a:b", "ABC", "nul", "com1", "abc\n")


@pytest.mark.parametrize("hostile", _HOSTILE_EVENT_IDS)
def test_the_refusal_of_a_bad_event_id_does_not_quote_the_id(hostile):
    from pydantic import ValidationError

    from hadavin_sdk.models import AuditEvent

    with pytest.raises(ValidationError) as raised:
        AuditEvent(event_id=hostile, **_EVENT)
    text = str(raised.value) + repr(raised.value)
    assert "input_value" not in text, "the refusal of a bad event id quotes the id: input_value is printed"
    assert hostile.strip() not in text or len(hostile.strip()) < 3, "the refusal of a bad event id quotes the id"
    assert "plain file name" in text


def test_an_event_id_with_a_colon_a_capital_or_a_device_name_is_refused_and_a_generated_id_is_not():
    from hadavin_sdk.models import AuditEvent, new_id

    for ok in (new_id("evt"), "evt-ok_1", "con-x", "a"):
        AuditEvent(event_id=ok, **_EVENT)
    for bad in ("a:b", "Abc", "NUL", "nul", "com9", "lpt1", "aux", "prn", "con"):
        try:
            AuditEvent(event_id=bad, **_EVENT)
        except ValueError as refused:
            assert "plain file name" in str(refused), f"the refusal of the event id {bad!r} has another sentence"
        else:
            raise AssertionError(f"an event id that is not a plain file name was accepted: {bad!r}")


def test_the_local_audit_folder_never_makes_a_file_from_an_event_that_skipped_the_model_check(tmp_path):
    """`model_construct` skips validation: the folder's own test refuses the name before any path is made."""
    from hadavin_sdk.audit.local_dir import LocalDirSink
    from hadavin_sdk.models import AuditEvent

    audit = LocalDirSink(tmp_path / "audit")
    evil = AuditEvent.model_construct(event_id="../../escaped", ts=None, **_EVENT)
    try:
        audit.write_intent(evil)
    except ValueError as refused:
        assert "plain file name" in str(refused), "the folder refused the hostile event id with another sentence"
    else:
        raise AssertionError("the local audit folder wrote an event whose id is not a plain file name")
    assert audit.write_outcome(evil) is None  # kept in memory, no file
    assert not (tmp_path / "escaped.json").exists() and not (tmp_path.parent / "escaped.json").exists()
    assert not list((tmp_path / "audit").rglob("*escaped*")), "a file was made from the hostile id"


def test_shown_id_shows_only_ids_of_the_prefixes_the_code_makes():
    from hadavin_sdk.errors import ID_PREFIXES, shown_id

    tail = "a1" * 16
    for prefix in ID_PREFIXES:
        assert shown_id(f"{prefix}-{tail}") == f"{prefix}-{tail}"
    assert shown_id(f"run-{tail}:12") == f"run-{tail}:12"
    for refused in (f"key-{tail}", f"cfg-{tail}", f"abc-{tail}", f"run-{tail}x", f"RUN-{tail}", f"x-{tail}"):
        assert shown_id(refused) == "?", f"an id with a prefix the code does not make is shown: {refused[:8]}"


def test_every_prefix_given_to_new_id_in_the_package_is_in_the_shown_list():
    import ast
    from pathlib import Path

    from hadavin_sdk.errors import ID_PREFIXES

    src = Path(__file__).resolve().parent.parent / "src" / "hadavin_sdk"
    seen = set()
    for path in src.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "new_id":
                arg = node.args[0] if node.args else None
                assert isinstance(arg, ast.Constant) and isinstance(arg.value, str), (
                    f"{path.name}:{node.lineno}: new_id is called with a prefix that is not a written word"
                )
                seen.add(arg.value)
    assert seen, "no new_id call was found: the scan is empty"
    assert seen <= set(ID_PREFIXES), f"new_id prefixes missing from ID_PREFIXES: {sorted(seen - set(ID_PREFIXES))}"


# ---- Issue 5: the executor call sites are tested through `execute`, not through the helper -------------------------------


def _executor_answering(status, *, lookup=None):
    from types import SimpleNamespace

    from hadavin_sdk.actions.contract import HttpExecutor
    from hadavin_sdk.actions.executor import Executor

    contract = SimpleNamespace(
        executor=HttpExecutor(kind="http", operation="POST /records", lookup_operation=lookup, secret_name="tok"),
        idempotency_header="Idempotency-Key",
    )
    ex = Executor.__new__(Executor)
    ex.registry = SimpleNamespace(contracts={"act": contract})
    ex._caller = lambda contract, heartbeat: (lambda method, path, body, headers: (status, None))
    return ex


def _approved_plan():
    from hadavin_sdk.models import ApprovalDecision, GateDecision, Plan, Target

    plan = Plan(
        run_id="run-1", agent_id="a", action_id="act", action_version=1, risk_class="reversible", inputs={"x": 1},
        target=Target(system="s"), idempotency_key="run-1:act", expected_outcome="x",
    )  # fmt: skip
    gd = GateDecision(run_id="run-1", plan_hash=plan.hash(), outcome="needs_approval", rule_id="r")
    ad = ApprovalDecision(
        approval_id="apr-1", plan_hash=plan.hash(), step=0, decision="approve", approver_id="user:a", channel="fake"
    )
    return plan, gd, ad


@pytest.mark.parametrize(("code", "outcome"), [(404, "failed"), (503, "unknown"), (408, "unknown")])
def test_execute_reports_an_error_status_as_its_digits_and_never_through_the_text_of_the_status(code, outcome):
    text = _marker("status")

    class Odd(int):
        def __str__(self) -> str:
            return text

        __repr__ = __str__

    plan, gd, ad = _approved_plan()
    result = _executor_answering(Odd(code)).execute(plan, gd, ad)
    assert text not in str(result.error_code), "execute built its error code from the text of the status"
    assert result.outcome == outcome, f"execute gave outcome {result.outcome!r} for status {code}"
    assert result.error_code == f"http_{code}", "execute gave an error code that is not the digits of the status"


# ---- Issue 5: `_port` of a tool names the port by digits only ----------------------------------------------------------------


def test_a_refused_port_is_shown_by_its_digits_never_by_the_text_of_the_value():
    from types import SimpleNamespace

    from hadavin_sdk.tools import ToolRefused

    from hadavin_sdk import tools as tools_mod

    text = _marker("port")

    class Odd(int):
        def __str__(self) -> str:
            return text

        __repr__ = __str__

    tool = tools_mod.ToolContext.__new__(tools_mod.ToolContext)
    tool.spec = SimpleNamespace(ports=[443])
    tool._cluster_ports, tool._https_ports = set(), {443}
    parts = SimpleNamespace(port=Odd(8081))
    with pytest.raises(ToolRefused) as raised:
        tool._port(parts, "https")
    assert text not in str(raised.value), "the refusal shows the port by the text of the value"
    assert "8081" in str(raised.value), "the refusal does not show the digits of the port"


# ---- Issue 3: ledger names read from the database are shown only in the shape of a migration file name ------------------------


def test_the_refusal_of_a_ledger_row_without_a_file_shows_only_names_shaped_like_ours():
    from hadavin_sdk.store.migrate import _shown_ledger_names

    text = _marker("ledger")
    got = _shown_ledger_names(["0006_evidence", text, "0009_z", "../etc/passwd", "payments-prod"])
    assert got == ["0006_evidence", "0009_z", "3 other(s)"], "a ledger name of another shape is shown"
    assert _shown_ledger_names(["0006_evidence"]) == ["0006_evidence"]
    assert _shown_ledger_names(["a" * 90, "0001_x\nsecret"]) == ["2 other(s)"]


def test_the_outbox_never_makes_a_file_from_an_event_id_that_is_not_a_plain_name(tmp_path):
    from hadavin_sdk.audit.local_dir import LocalDirSink
    from hadavin_sdk.models import AuditEvent

    audit = LocalDirSink(tmp_path / "audit")
    odd = AuditEvent.model_construct(event_id="Upper-Case", ts=None, **_EVENT)  # a valid file name on most systems
    assert audit.write_outcome(odd) is None
    made = [p.name for p in (tmp_path / "audit").rglob("*") if p.is_file()]
    assert not made, f"the outbox made a file from an event id that is not a plain name: {made}"
