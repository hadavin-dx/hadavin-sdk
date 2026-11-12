"""PR H batch 12: the rows of the round-11 review (issues 1 to 11 and 13). Every credential-shaped value is built from parts; the only
literal is the allowed example key. Each test names the issue it guards and the mutant (tests/prh_mutants.py, numbers 186 and up)
that reverts the guard; the failing message of a killer names the planted fault. Cost tests count WORK (characters, builds, calls),
never seconds. A test that also passes on the batch 11 head (242dfd66) says so and names the one reason it exists."""

import importlib
import json

import pytest

from hadavin_sdk import defaults, evals, tools
from hadavin_sdk.approvals import requests as approval_requests
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.injection import injection_check
from hadavin_sdk.models import RunState as S
from hadavin_sdk.registry import load_registry
from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")


# The mutant runner starts pytest with `--noconftest`, so the three fixtures this file needs are defined here (same bodies as conftest).
@pytest.fixture
def cfg_dir(tmp_path):
    from tests.conftest import make_cfg

    return make_cfg(tmp_path)


@pytest.fixture
def fake_system():
    import secrets

    from tests.fixtures.fake_system import FakeSystem

    system = FakeSystem(token=secrets.token_hex(16)).start()
    yield system
    system.stop()


@pytest.fixture
def live_cfg_dir(tmp_path, fake_system):
    from tests.conftest import make_cfg

    return make_cfg(tmp_path, port=fake_system.port)


def _crash(*a, **kw):
    raise runmap.RedactorCrash("RuntimeError")


def _refusal(*a, **kw):
    raise runmap.RedactionError("a plain refusal")


# ---- issue 1: one rule for a crash of the redactor at every catcher the b11 pass left out -------------------------------------


def _plan():
    from tests.test_s6_approvals import _plan as plan

    return plan()


def test_b12_i1_the_approval_summary_lets_a_crash_pass_and_notes_a_refusal(monkeypatch):
    """Issue 1 (class: a crash read as a limit; mutant 186). The summary of an approval card showed "(too large to show here)" for a
    crash of the redactor and the approval went on."""
    real = runmap.redact_text

    def crash_for_the_long_text(text, mapping, neutralise=None):
        if (
            "Expected:" in text
        ):  # only the full card text; the short fallback line would be accepted
            raise runmap.RedactorCrash("RuntimeError")
        return real(text, mapping, neutralise=neutralise)

    monkeypatch.setattr(runmap, "redact_text", crash_for_the_long_text)
    with pytest.raises(runmap.RedactorCrash):
        approval_requests.summary(_plan())

    def refuse_the_long_text(text, mapping, neutralise=None):
        if "Expected:" in text:  # only the full card text; the short fallback line is accepted
            raise runmap.RedactionError("a plain refusal")
        return real(text, mapping, neutralise=neutralise)

    monkeypatch.setattr(runmap, "redact_text", refuse_the_long_text)
    assert "too large to show here" in approval_requests.summary(_plan()), (
        "mutant 186: a plain refusal must still give the fixed card line"
    )


def test_b12_i1_a_crash_while_the_card_is_made_stops_the_run_with_no_card(
    live_cfg_dir, fake_system, monkeypatch
):
    """Issue 1 (mutant 187). The run waits for approval; the request hook raises `RedactorCrash`: the run goes to a person with the
    reason `redaction_error`; nothing escapes the loop and no card is sent."""
    from hadavin_sdk import app as app_mod
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.approvals import FakeChannel
    from tests.conftest import qualify
    from tests.test_cuj import _doc

    qualify(load_registry(load_config(live_cfg_dir)))
    channel = FakeChannel("sig" + "-b12")
    app = app_mod.build(
        live_cfg_dir,
        ["test-agent"],
        secrets=FakeSecretProvider({"fixture-token": fake_system.token}),
        channel=channel,
        timeout_s=0.5,
    )
    monkeypatch.setattr(app_mod, "summary", _crash)
    run = app.runtime.handle("test-agent", "svc:test-agent", _doc(app, "create.txt"))
    state = app.store.get_run(run.run_id)
    assert (state.state, state.reason_code) == (S.NEEDS_PERSON, "redaction_error"), (
        f"mutant 187: the run ended as {state.state} / {state.reason_code}"
    )
    assert channel.sent == [], (
        "mutant 187: an approval was sent although the card could not be made"
    )


def test_b12_i1_a_golden_input_with_a_crashed_redactor_is_not_a_config_error(
    live_cfg_dir, monkeypatch
):
    """Issue 1 (mutant 188): `evals.gate` told the operator the input "cannot be redacted" for a crash of the redactor."""
    cfg = load_config(live_cfg_dir)
    reg = load_registry(cfg)

    class Never:
        def chat(self, *a, **k):
            raise AssertionError("the model must not be reached")

    monkeypatch.setattr(runmap, "redact_untrusted", _crash)
    with pytest.raises(runmap.RedactorCrash):
        evals.gate(reg, Never(), "test-agent")
    monkeypatch.setattr(runmap, "redact_untrusted", _refusal)
    with pytest.raises(ConfigError, match="cannot be redacted"):
        evals.gate(reg, Never(), "test-agent")


def test_b12_i1_the_injection_check_stops_the_run_when_the_log_line_crashes_the_redactor(
    monkeypatch,
):
    """Issue 1 (no mutant of its own: the rule lives in `safe_head`, mutant 163). A detector that fails is a flag; if the redactor
    crashes while the cause is written to the log, `RedactorCrash` leaves the check (nothing passes)."""

    class Broken:
        def check(self, text, source):
            raise ValueError("a broken detector")

    assert injection_check(Broken(), "x", "t").flagged is True  # a plain failure stays a flag
    monkeypatch.setattr(runmap, "redact_bounded", _crash)
    with pytest.raises(runmap.RedactorCrash):
        injection_check(Broken(), "x", "t")


class _BrokenDetector:
    backend = "broken"

    def check(self, text, source):
        raise ValueError("a broken detector")


def test_b12_i1_a_crash_in_the_injection_screen_stops_the_run_as_redaction_error(
    tmp_path, monkeypatch
):
    """Issue 1 (mutant 189). The check of the document (a detector that fails, a redactor that crashes while writing the log line)
    escaped `Runtime.handle` with no handler. It is now the stop `redaction_error`."""
    rt, _cards = build_runtime(k5_cfg(tmp_path), ScriptLLM([{"noaction": True}]))
    rt.detector = _BrokenDetector()
    real = runmap.redact_bounded

    def crash_for_the_log_line(text, mapping, neutralise=None):
        if text == "a broken detector":
            raise runmap.RedactorCrash("RuntimeError")
        return real(text, mapping, neutralise)

    monkeypatch.setattr(runmap, "redact_bounded", crash_for_the_log_line)
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "redaction_error"), (
        f"mutant 189: the document screen ended as {run.state} / {run.reason_code}"
    )


def test_b12_i1_a_crash_in_the_tool_result_screen_stops_the_run_as_redaction_error(
    tmp_path, monkeypatch
):
    """Issue 1 (mutant 190): the same rule for the screen of a tool result."""
    from tests.fixtures import k5_tools

    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5 refused; rollout revision 17 failed"
    rt, _cards = build_runtime(k5_cfg(tmp_path), ScriptLLM([{"tool": "app"}, {"noaction": True}]))
    real_screen = rt._screen
    seen = []

    def screen(run, text, source):
        seen.append(source)
        if source.startswith("tool:"):
            rt.detector = _BrokenDetector()
            real = runmap.redact_bounded

            def crash(text2, mapping, neutralise=None):
                if text2 == "a broken detector":
                    raise runmap.RedactorCrash("RuntimeError")
                return real(text2, mapping, neutralise)

            monkeypatch.setattr(runmap, "redact_bounded", crash)
        return real_screen(run, text, source)

    monkeypatch.setattr(rt, "_screen", screen)
    run = handle(rt)
    assert any(s.startswith("tool:") for s in seen)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "redaction_error"), (
        f"mutant 190: the tool result screen ended as {run.state} / {run.reason_code}"
    )


def test_b12_i1_a_crash_of_the_redactor_does_not_stop_the_other_steps_of_the_tick(monkeypatch):
    """Issue 1 (mutant 191). `_message` was called inside `except Exception` of `_run_step`: a crash escaped before the state of the
    step was saved and stopped the rest of the tick. Now the message is a fixed note, the step is recorded as failed."""
    from hadavin_sdk.runtime import tick

    saved = []

    class Store:
        def get_tick_state(self, name):
            return None

        def save_tick_state(self, state):
            saved.append(state)

    class Ctx:
        app = type("A", (), {"store": Store()})()
        now = __import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").UTC)

    def boom(ctx):
        raise ValueError("a step failed")

    monkeypatch.setattr(runmap, "redact_bounded", _crash)
    result = tick._run_step(Ctx(), tick.TickStep("probe", 0, boom))
    assert result == tick.FAILED
    assert saved and saved[0].last_error == "ValueError: " + tick.CRASH_NOTE, (
        f"mutant 191: the step was recorded as {saved[0].last_error if saved else None!r}"
    )
    monkeypatch.setattr(runmap, "redact_bounded", _refusal)
    assert tick._message(ValueError("x")) == runmap.SAFE_HEAD_NOTE


def test_b12_i1_extract_and_the_k1b_loop_let_a_crash_of_the_redactor_stop_the_run(
    monkeypatch, tmp_path, cfg_dir
):
    """Issue 1 (no mutant of its own: both call `safe_head`, mutant 163; passes on 242dfd66, the one reason it exists is that the two
    sibling callers named by the review were never run with a crashing redactor). `extract` and the replay loop raise
    `RedactorCrash`; the replay writes FAILED.txt."""
    from pydantic import BaseModel

    from hadavin_sdk.extract import extract
    from tests.k1b_support import ScriptedLLM, text_reply
    from tests.test_k1b_replay import Env

    class Out(BaseModel):
        need: int

    class LLM:
        def chat(self, messages, **kw):
            from hadavin_sdk.models import Reply

            return Reply(text=json.dumps({"other": "x"}), model_id="fake")

    monkeypatch.setattr(runmap, "redact_bounded", _crash)
    with pytest.raises(runmap.RedactorCrash):
        extract(LLM(), b"doc", Out, run_id="r", route="x")
    env = Env(tmp_path, cfg_dir)
    with pytest.raises(runmap.RedactorCrash):
        env.run(ScriptedLLM([text_reply("this is not a diagnosis")]))
    assert "RedactorCrash" in (env.out / "FAILED.txt").read_text(encoding="utf-8")


# ---- issue 2: a backslash-e inside a value, decided by the shape of the word (a Windows path is the control) -----------------

from tests.test_prh_b10 import BSL, stands  # noqa: E402


def _glue(*parts):
    return "".join(parts)


V28 = _glue("qZ7k", "M3vR", "t9Lx", "P2wB", "n5Hc", "D8fJ", "s4Yg")  # made-up, 28 characters
V9 = _glue("qZ7k", "M3vR", "t")  # a handed-out value of 9 characters
V6 = _glue("qZ7k", "M3")  # 6 characters
B64 = _glue(
    "Ab3+", "dE6/", "gH9&", "jK2m"
)  # made-up, symbols of the base64 and form alphabets inside the window

ESC_CELLS = {}
for _name, _value in (("v28", V28), ("v9", V9), ("v6", V6), ("b64", B64)):
    for _at in range(1, len(_value)):
        ESC_CELLS[f"{_name}@{_at}"] = (_value, _value[:_at] + BSL + "e" + _value[_at:])
for _name, _value in (("v28", V28), ("b64", B64)):  # every 2, 3, 4 and 5 characters
    for _gap in (2, 3, 4, 5):
        ESC_CELLS[f"{_name}/every{_gap}"] = (
            _value,
            (BSL + "e").join(_value[i : i + _gap] for i in range(0, len(_value), _gap)),
        )


@pytest.mark.parametrize("cell", sorted(ESC_CELLS))
def test_b12_i2_a_value_with_a_backslash_e_at_any_place_is_not_shown(cell):
    """Issue 2 (mutants 192 and 193; the grid of the review: every offset of a 28-, a 9- and a 6-character handed-out value and of a
    value with base64 symbols, and a spelling every 2 to 5 characters). Whatever the redactor does with the text (mask it or withhold
    it), no stretch of 8 characters of the value (the whole value if it has fewer) stands in the result, with or without the
    backslash-e spellings in it. The value is also handed to the tool."""
    value, text = ESC_CELLS[cell]
    size = min(8, len(value))
    out = tools.prepare_output(text, {}, 4000, [value])
    for shown in (out, out.replace(BSL + "e", "")):
        assert not stands(shown, value, size), (
            f"mutants 192/193: the value of cell {cell} is readable"
        )


@pytest.mark.parametrize(
    "path",
    [
        "C:" + BSL + "env",
        "C:" + BSL + "Users" + BSL + "err" + BSL + "x",
        "D:" + BSL + "tmp" + BSL + "ex" + BSL + "data",
        "src" + BSL + "err" + BSL + "x",
        "z:" + BSL + "env" + BSL + "a",
    ],
)
def test_b12_i2_a_path_name_after_a_backslash_is_left_as_written(path):
    """Issue 2, the controls (mutants 193 and 194). Passes on 242dfd66; the one reason it exists: it pins that the glued rule does not read the
    spelling of a path name (a drive letter and a colon in front, or a backslash within 12 characters after) and that the path takes no
    heavier path."""
    assert runmap.hex_unescape(path) == path, f"mutants 193/194: {path!r} was read as ESC"
    assert tools._HIDDENISH.search(path) is None
    assert tools.prepare_output(path, {}, 4000, [V28]) == path


@pytest.mark.parametrize(
    "text",
    [
        "ab" + BSL + "eb",
        "q" + BSL + "eZ",
        "abc+" + BSL + "e/def",
        "key:" + BSL + "e" + "abcdef",  # a colon that is no drive letter
        "x" + BSL + "e" + "y" * 13 + BSL,  # 12 or more token characters after, then a backslash
    ],
)
def test_b12_i2_a_backslash_e_glued_between_two_characters_of_a_word_is_read_as_esc(text):
    """Issue 2 (mutant 192; fails on 242dfd66 for the first three rows; the last two pass there and are kept as the 12-after rule and the
    colon rule, one reason each)."""
    assert runmap.hex_unescape(text) == text.replace(BSL + "e", "\x1b"), (
        f"mutant 192: {text!r} was not read"
    )


@pytest.mark.parametrize(
    "text", ["q" + BSL + "eZ" + BSL + "e7", "a" + BSL + "eb" + BSL + "ec" + BSL + "ed"]
)
def test_b12_i2_the_chain_rule_reads_a_backslash_e_one_character_from_the_next_one(text):
    """Issue 2 (mutant 182). A spelling with another one a single token character away is read, also the first of the pair (the glued
    rule leaves it out because a backslash follows within 12 characters). Passes on 242dfd66; the one reason it exists: it is the
    only direct test of the chain rule after batch 12 moved the glued rule next to it."""
    assert runmap.hex_unescape(text) == text.replace(BSL + "e", "\x1b"), (
        f"mutant 182: {text!r} was not read"
    )


# ---- issue 3: "is this value new" asks the SECRET holders only, at both sites that ask it --------------------------------------

KEY12 = "AKIA" + "IOSFODNN7EXAMPLE"


def test_b12_i3_a_key_that_is_only_a_piece_of_a_held_identifier_is_new_to_the_consuming_reading():
    """Issue 3, site `_consuming_wins` (mutant 195; fails on 242dfd66). The held value is an ARN (not a secret kind) that holds the key; the
    reading finds the key under a new placeholder: it is new, so the reading wins and the cut copy is judged."""
    arn = "arn:aws:iam::123456789012:user/" + KEY12
    known = {"<ARN_1>": arn}
    new_map = {"<ARN_1>": arn, "<APIKEY_2>": KEY12}
    assert runmap._consuming_wins("nothing of it left", new_map, known) is True, (
        "mutant 195: a key that is a piece of a held identifier was called already found (consuming reading)"
    )


def test_b12_i3_a_key_that_is_only_a_piece_of_a_held_identifier_is_new_to_the_character_reading():
    """Issue 3, site `_char_reading_wins` (mutant 196; fails on 242dfd66)."""
    arn = "arn:aws:iam::123456789012:user/" + KEY12
    known = {"<ARN_1>": arn}
    new_map = {"<ARN_1>": arn, "<APIKEY_2>": KEY12}
    assert runmap._char_reading_wins("nothing of it left", new_map, known, {}, set(), "") is True, (
        "mutant 196: a key that is a piece of a held identifier was called already found (character reading)"
    )


def test_b12_i3_a_key_that_is_a_piece_of_a_held_secret_is_still_not_new():
    """Issue 3 control (mutants 195 and 196). Passes on 242dfd66; the one reason it exists: a piece of a held SECRET is still "already
    found" at both sites, so the fix did not make every reading win."""
    held = {"<APIKEY_1>": KEY12}
    new_map = {"<APIKEY_1>": KEY12, "<APIKEY_2>": KEY12[:12]}
    assert runmap._consuming_wins("nothing of it left", new_map, held) is False
    assert runmap._char_reading_wins("nothing of it left", new_map, held, {}, set(), "") is False


# ---- issue 6: a gap character glued in front of a spaced run does not start the run late ---------------------------------------

from tests.test_prh_b10 import on_the_run_path, spaced  # noqa: E402

GAPS = ["️", "ㅤ", "ᅟ", "ᅠ", "ﾠ", "͏"]  # variation selector, fillers, combining grapheme joiner


@pytest.mark.parametrize("gap", GAPS, ids=[f"{ord(g):04x}" for g in GAPS])
def test_b12_i6_a_gap_character_glued_in_front_of_a_spaced_run_does_not_start_the_run_late(gap):
    """Issue 6 (mutant 197; fails on 242dfd66: the run started at the third character, two tokens late). The word class that stops a run
    from starting in the middle of a longer word held the gap characters, although the run rule itself treats them as gaps."""
    runs = redact_mod._runs_of(gap + spaced(KEY12))
    assert runs and runs[0][0] == 1, (
        f"mutant 197: the run started at {runs[0][0] if runs else None}, not at the first token"
    )


@pytest.mark.parametrize("gap", GAPS, ids=[f"{ord(g):04x}" for g in GAPS])
@pytest.mark.parametrize("where", ["head", "tail"])
def test_b12_i6_a_spaced_key_with_a_gap_character_glued_at_the_head_or_the_tail_is_masked(
    gap, where
):
    """Issue 6 (mutant 197). Passes on 242dfd66 end to end (the hidden-character strip runs first there, measured); the one reason it exists is
    that it pins the result for the rows the review named, beside the run-level test above that fails there."""
    text = "key: " + (gap + spaced(KEY12) if where == "head" else spaced(KEY12) + gap) + " end"
    out = on_the_run_path(text)
    assert not stands(out.replace(" ", "").replace(gap, ""), KEY12, 6), (
        f"mutant 197: the key stands in {out!r}"
    )
    assert not stands(
        tools.prepare_output(text, {}, 4000, []).replace(" ", "").replace(gap, ""), KEY12, 6
    )


# ---- issue 11: the word-class scan reaches the end of CJK Extension J ----------------------------------------------------------


def test_b12_i11_the_word_class_scan_reaches_the_end_of_cjk_extension_j():
    """Issue 11 (mutant 198). Unicode 17 added CJK Extension J (U+323B0 to U+3347F); the scan used to stop at U+323FF. The data of this
    Python may not know the block yet (so the test derivation over all code points cannot see it): the scan bound is checked directly.
    Fails on 242dfd66 (the bound was 0x32400)."""
    assert redact_mod._WORD_PLANES[0].stop > 0x3347F, (
        "mutant 198: the scan stops before the end of CJK Extension J"
    )


# ---- issue 7: `_only_inside_held` is inside the work budget ------------------------------------------------------------------


class _CountingWork:
    def __init__(self):
        self.checks = 0

    def check(self):
        self.checks += 1


def _held_pem_and_text():
    pem = "k" + "Q7z" * 600  # a held value of 1,801 characters (PEM size)
    current = {"<SECRET_1>": pem}
    text = (
        pem * 140
    )  # about 252,000 characters: many overlapping copies of the small value, all inside the held value
    return pem, current, text


def test_b12_i7_the_search_for_copies_of_a_value_inside_a_big_held_value_looks_at_the_clock():
    """Issue 7 (mutant 199; fails on 242dfd66: the function took no `work` and never looked at the clock). A 252,000-character text and a
    held 1,801-character value that holds the small value 63,000 times: the clock is looked at every 4,096 hits, and the answer is
    still True (every copy lies inside a held value)."""
    pem, current, text = _held_pem_and_text()
    work = _CountingWork()
    assert runmap._only_inside_held("Q7zQ7zQ7zQ7zQ7zQ7z", current, (text, text), work) is True
    assert work.checks >= 20, f"mutant 199: the clock was looked at {work.checks} times"


def test_b12_i7_a_held_value_shorter_than_the_spaced_minimum_does_not_cover_a_copy():
    """Issue 7 (mutant 200; fails on 242dfd66). The spaced sweep masks no spaced copy of a held value under
    `defaults.SPACED_VALUE_MIN_CHARS`, so a match of it with the gaps taken out proves nothing."""
    short = "abcdefghijk"  # 11 characters
    assert len(short) < defaults.SPACED_VALUE_MIN_CHARS
    current = {"<SECRET_1>": short}
    assert runmap._only_inside_held("abcdefgh", current, ("a b c d e f g h i j k",)) is False, (
        "mutant 200: a spaced copy inside a short held value was called covered"
    )


def test_b12_i7_a_long_held_value_still_covers_a_spaced_copy_inside_it():
    """Issue 7 control (mutant 200). Passes on 242dfd66; the one reason it exists: the 12-character limit does not break the case
    batch 11 built (a spaced copy of a value inside a long held value is covered)."""
    long_ = "abcdefghijklmnop"
    current = {"<SECRET_1>": long_}
    assert (
        runmap._only_inside_held("abcdefgh", current, ("a b c d e f g h i j k l m n o p",)) is True
    )
