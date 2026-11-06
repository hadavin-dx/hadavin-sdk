"""The agent gate must refuse general-purpose briefs with no explicit model, and never choose a weaker model itself."""
import importlib.util
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "hooks" / "agent_preamble_gate.py"
spec = importlib.util.spec_from_file_location("agent_preamble_gate", SRC)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

BRIEF = g.MARKER + " " + g.EGM_MARKER + " " + g.CODE_MARKER + " build the thing. " + "x" * 300
BRIEF_NO_CODE_LAST = g.MARKER + " " + g.EGM_MARKER + " build the thing. " + "x" * 300


def test_brief_without_code_last_marker_is_denied_even_with_a_model():
    reason = g.decide({"tool_input": {"subagent_type": "general-purpose", "prompt": BRIEF_NO_CODE_LAST, "model": "opus"}})
    assert reason and "CODE-LAST v1" in reason and "R448" in reason


def call(**inp):
    inp.setdefault("subagent_type", "general-purpose")
    inp.setdefault("prompt", BRIEF)
    return g.decide({"tool_input": inp})


def test_missing_or_bad_model_denied():
    assert "model" in call()
    assert "model" in call(model="")
    assert "model" in call(model="inherit")


def test_any_explicit_model_allowed_including_opus():
    for m in ("opus", "sonnet", "haiku", "Opus"):
        assert call(model=m) is None


def test_other_rules_unchanged():
    assert "STUDIO-PREAMBLE" in call(model="sonnet", prompt="y" * 400)
    assert call(subagent_type="egm:egm-design", prompt="short") is None
    assert call(subagent_type="Explore", prompt=BRIEF) is None
    assert call(prompt="short brief") is None


def test_claude_and_empty_type_are_gated_for_model():
    assert "model" in call(subagent_type="claude")
    assert "model" in call(subagent_type="")


def test_ungated_types_need_no_model():
    for t in ("egm:egm-design", "caveman:cavecrew-builder", "Explore", "Plan", "fork"):
        assert call(subagent_type=t) is None


def test_non_string_model_denied_not_crash():
    assert "model" in call(model=["opus"])
    assert "model" in call(model=None)


def test_main_fails_open_on_garbage_stdin(monkeypatch, capsys):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert g.main() == 0
    assert capsys.readouterr().out == ""
