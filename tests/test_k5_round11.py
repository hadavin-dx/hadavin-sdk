"""Round 11 (security path), red first.

B-1 (a class): any transformation AFTER the neutralising step re-opens what it closed. `redact_text` may return a DECODED
view; a card text must be sanitised and have commands withheld AFTER decoding, so the neutralising hook runs on every view.
M-2: the markup-split second view is judged by what it finds, not by kind. M-3: pass-one masks survive the swap for every
value terminator. M-4: the proposal-inputs row is driven with a secret in a declared free-text field."""

from __future__ import annotations

import ast
import pathlib
import re
import tomllib

import pytest

import hadavin_sdk
from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.guard import runmap
from tests.fixtures import k5_tools
from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg

KEY = (
    "%41KIA" + "IOSFODNN7EXAMPLE"
)  # a decode-only secret (built from parts): it makes pass two return the decoded view
ROOT = pathlib.Path(hadavin_sdk.__file__).resolve().parent
BS = chr(92)

PAYLOADS = {
    "percent command": ("%72m -rf /tmp/x", "rm -rf"),
    "percent image": ("%3Cimg src=x%3E", "<img"),
    "hex mention": (BS + "x3c!channel" + BS + "x3e", "<!channel>"),
    "entity mention": ("&lt;!channel&gt;", "<!channel>"),
    "percent link": ("%3Ca href=http://evil.example/x%3Ebad%3C/a%3E", "<a href"),
}


@pytest.mark.parametrize("name", sorted(PAYLOADS))
def test_clean_never_returns_a_decoded_view_that_was_not_sanitised(name):
    payload, bad = PAYLOADS[name]
    out = channel_mod.clean(f"note {payload} and {KEY} end")
    assert bad not in out and "IOSFODNN7EXAMPLE" not in out, (name, out)


@pytest.mark.parametrize("name", sorted(PAYLOADS))
def test_the_slack_block_never_shows_a_decoded_view_that_was_not_sanitised(name):
    from types import SimpleNamespace

    from hadavin_sdk.approvals.slack_channel import SlackChannel

    payload, bad = PAYLOADS[name]
    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 2900
    req = SimpleNamespace(
        summary=f"note {payload} and {KEY} end",
        current_step=0,
        steps=[1],
        approval_id="a",
        status="PENDING",
    )
    shown = ch._blocks(req, None)[0]["text"]["text"]
    assert bad not in shown and "IOSFODNN7EXAMPLE" not in shown, (name, shown)


def test_redact_text_applies_the_neutralise_hook_to_every_view_it_can_return():
    seen = []

    def hook(t):
        seen.append(t)
        return t.replace("DANGER", "")

    out = runmap.redact_text("x DANGER %70assword%3Dhunter2 DANGER", {}, neutralise=hook)
    assert "DANGER" not in out and "hunter2" not in out
    assert len(seen) >= 2  # the text and at least one decoded view


# ---- structural: a call of `redact_text` without the hook is only allowed where nothing sanitises its output afterwards ----------------

NO_HOOK_OK = {
    "guard/runmap.py",  # the choke point itself (safe_head, redact_bounded, redact_untrusted pass their own hooks)
    "guard/judge.py",  # the text goes to a model, not to a person's screen
    "guard/bedrock_guardrail.py",  # the text goes to a vendor screen
    "runtime/evidence.py",  # grounding compares redacted strings, nothing is shown
}  # tools.py is NOT exempt: it has no raw `redact_text` call (prepare_output uses redact_untrusted/redact_bounded)


def _callee_name(f: ast.AST) -> str:
    return f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")


def _hook_is_missing(n: ast.Call) -> bool:
    """A `redact_text` call without a real neutralising hook: no `neutralise=` keyword, `neutralise=None`, or a third
    positional argument that is `None`."""
    if _callee_name(n.func) != "redact_text":
        return False
    for k in n.keywords:
        if k.arg == "neutralise":
            return isinstance(k.value, ast.Constant) and k.value.value is None
    if len(n.args) >= 3:
        return isinstance(n.args[2], ast.Constant) and n.args[2].value is None
    return True


def _aliases_redact_text(n: ast.AST) -> bool:
    """`rt = runmap.redact_text` or passing it around: a reference that is not a call hides the call from this test."""
    return (
        isinstance(n, ast.Assign)
        and _callee_name(n.value) == "redact_text"
        and not isinstance(n.value, ast.Call)
    )


def test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook():
    bad = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if rel in NO_HOOK_OK:
                continue
            if (isinstance(n, ast.Call) and _hook_is_missing(n)) or _aliases_redact_text(n):
                bad.append(f"{rel}:{n.lineno}")
    assert not bad, f"a card text is redacted with no neutralise hook: {bad}"


def test_the_hook_check_itself_catches_a_missing_none_and_an_alias():
    def parse(src):
        return ast.parse(src).body[0]

    assert _hook_is_missing(parse("redact_text(t, m)").value), (
        "the hook check does not see a call with no hook"
    )
    assert _hook_is_missing(parse("runmap.redact_text(t, m, None)").value), (
        "the hook check does not see a hook that is None (positional)"
    )
    assert _hook_is_missing(parse("runmap.redact_text(t, m, neutralise=None)").value), (
        "the hook check does not see a hook that is None (keyword)"
    )
    assert not _hook_is_missing(parse("runmap.redact_text(t, m, neutralise=_neutralise)").value), (
        "the hook check flags a call that has its hook"
    )
    assert _aliases_redact_text(parse("rt = runmap.redact_text")), (
        "the hook check does not see an alias of redact_text"
    )


def test_only_clean_and_the_slack_block_call_the_card_sanitisers():
    allowed = {"approvals/gate.py", "approvals/channel.py", "approvals/slack_channel.py"}
    bad = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel in allowed:
            continue
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and _callee_name(n.func) in {
                "sanitise_text",
                "withhold_commands",
            }:
                bad.append(f"{rel}:{n.lineno}")
    assert not bad, bad
    # Q8b: the last step of a card text and the one function that feeds a card, each name with its own allowed files
    allowed_by_name = {
        "defang_domains": {"approvals/gate.py", "approvals/channel.py"},
        "redact_for_people": {"approvals/channel.py", "approvals/slack_channel.py"},
    }
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and rel not in allowed_by_name.get(
                _callee_name(n.func), {rel}
            ):
                bad.append(f"{rel}:{n.lineno} {_callee_name(n.func)}")
    assert not bad, bad


# ---- M-2 ---------------------------------------------------------------------------------------------------------------------------------


def test_a_second_markup_split_secret_of_the_same_kind_is_masked():
    out = channel_mod.clean("api_key=AAAAAAAA1234 and password%<i> </i>3Dhunter2 end")
    assert "hunter2" not in out and "AAAAAAAA1234" not in out, out


def test_an_ordinary_card_keeps_its_spaces_even_when_it_looks_like_a_header():
    text = "authorization: failed for user x and more words"
    assert channel_mod.clean(text) == text
    marked = "<b>authorization: failed for user x</b> and more words"
    assert " for user x and more" in channel_mod.clean(marked)


# ---- M-3 ---------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("enc", ["%3B", "%26", "%22", "%27", "%2C", "%20"])
def test_pass_one_masks_survive_the_swap_for_every_value_terminator(enc):
    text = f"password=ab{enc}zq9tail and {KEY}"
    out = runmap.redact_text(text, {})
    assert "zq9" not in out and "IOSFODNN7EXAMPLE" not in out, (enc, out)


# ---- M-4 ---------------------------------------------------------------------------------------------------------------------------------

SPELLINGS = {
    "percent": "%41KIA" + "IOSFODNN7EXAMPLE",
    "entity": "&#65;KIA" + "IOSFODNN7EXAMPLE",
    "assignment": "password%3Dhunter2",
}


@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
def test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card(
    spelling, tmp_path
):
    from hadavin_sdk.store import MemoryStore

    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5 refused; rollout revision 17 failed"
    llm = ScriptLLM(
        [
            {"tool": "app"},
            {
                "propose": {"host": "<IPV4_1>", "revision": "17"},
                "reason": f"a {SPELLINGS[spelling]} b",
            },
        ]
    )
    store = MemoryStore()
    rt, cards = build_runtime(k5_cfg(tmp_path), llm, store=store)
    run = handle(rt)
    plan = store.get_plan(run.run_id)
    assert plan is not None, "the proposal did not reach a stored plan"
    stored = repr(plan.inputs)
    shown = " ".join(c.text for c in cards)
    for needle in ("IOSFODNN7EXAMPLE", "hunter2"):
        assert needle not in stored and needle not in shown, (spelling, stored, shown[:200])
    assert re.search(r"<(?!IPV4_)[A-Z]+_\d+>", stored), stored


# ---- minors ------------------------------------------------------------------------------------------------------------------------------


def test_percent_u_and_brace_unicode_escapes_are_decoded():
    assert runmap.undo("%u0041") == "A"
    assert runmap.undo(BS + "u{41}") == "A"
    assert runmap.undo(BS + "u{1F600}") == "\U0001f600"
    out = runmap.redact_text("k %u0041KIA" + "IOSFODNN7EXAMPLE z", {})
    assert "IOSFODNN7EXAMPLE" not in out


def test_clean_and_the_fake_channel_do_not_reuse_a_placeholder_number():
    out = channel_mod.clean("host <IPV4_1> and 10.0.0.9")
    assert out.count("<IPV4_1>") == 1 and "<IPV4_2>" in out and "10.0.0.9" not in out


def _imports_the_bare_redactor(n: ast.AST) -> bool:
    return (
        isinstance(n, ast.ImportFrom)
        and ((n.module or "").endswith(("guard.redact", "guard")) or n.level > 0)
        and any(a.name in {"redact", "redact_many"} for a in n.names)
    )


def test_the_bare_redactor_ban_also_catches_an_aliased_import():
    bad = []
    for base in (ROOT, ROOT.parents[1] / "demos"):
        for path in base.rglob("*.py"):
            rel = path.relative_to(base).as_posix()
            if base == ROOT and rel in {"guard/runmap.py", "guard/redact.py", "guard/__init__.py"}:
                continue
            bad += [
                f"{rel}:{n.lineno}"
                for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
                if _imports_the_bare_redactor(n)
            ]
    assert not bad, bad


def test_the_gitleaks_header_chain_regex_matches_the_three_planted_headers_and_nothing_longer():
    cfg = tomllib.loads((ROOT.parents[1] / ".gitleaks.toml").read_text(encoding="utf-8"))
    chain = re.compile(cfg["allowlists"][0]["regexes"][0])
    h = "-----BEGIN " + "PRIVATE KEY-----"
    three = f'{h}",\n        "{h}",\n        "{h}'
    four = f'{h}",\n        "{h}",\n        "{h}",\n        "{h}'
    assert chain.fullmatch(three) and chain.fullmatch(h)
    assert not chain.fullmatch(four)
    assert not chain.fullmatch(
        h + "\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n-----END " + "PRIVATE KEY-----"
    )


@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
def test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record(spelling, tmp_path):
    from hadavin_sdk.store import MemoryStore

    k5_tools.RESULTS["app"] = "ok 10.0.0.5"
    llm = ScriptLLM([{"tool": f"app {SPELLINGS[spelling]}"}, {"noaction": True}])
    store = MemoryStore()
    rt, _ = build_runtime(k5_cfg(tmp_path), llm, store=store)
    run = handle(rt)
    stored = repr([c.inputs for c in store.list_tool_calls(run.run_id)])
    assert "IOSFODNN7EXAMPLE" not in stored and "hunter2" not in stored, stored


# ---- round 12: the reviewer's concrete inputs (the class is covered by tests/test_k5_round12_fuzz.py) ---------------------------------------


@pytest.mark.parametrize("enc", ["%0D", "%0B", "%0C", "%E2%80%A8", "%1C", "%C2%85"])
def test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked(enc):
    out = runmap.redact_text(f"password=ab{enc}zq9tail and {KEY}", {})
    assert "zq9" not in out, (enc, out)


def test_a_value_with_a_plain_comma_and_an_encoded_one_is_masked_whole():
    assert "x=1" not in runmap.redact_text(f"password=a,b%2Cx=1 and {KEY}", {})


def test_junk_ahead_cannot_use_up_the_pairing_slots_and_a_long_value_is_masked_or_refused():
    junk = " ".join(f"<IPV4_{i}>" for i in range(400))
    assert "zq9" not in runmap.redact_text(f"{junk} password=ab%3Bzq9 and {KEY}", {})
    long = "q" * 4200
    try:
        out = runmap.redact_text(f"password={long}%3Bzq9tail and {KEY}", {})
    except runmap.InputTooLarge:
        return
    assert "zq9" not in out


def test_the_tag_deleted_view_keeps_real_placeholders_and_line_breaks():
    out = channel_mod.clean(
        "<b>head</b>\nhost <IPV4_1> line\nnext <SECRET_2> password%<i> </i>3Dxyz9abc end"
    )
    assert "xyz9abc" not in out and "<IPV4_1>" in out and "<SECRET_2>" in out, out
    assert "head\nhost" in out and "line\nnext" in out, (
        out
    )  # a line break after a tag survives the view


def test_more_pairable_values_than_the_bound_are_refused_not_skipped():
    text = " ".join(f"password=ab%3Bzz{i}" for i in range(300)) + " and " + KEY
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text(text, {})


def test_a_plain_secret_and_a_markup_split_one_are_both_masked():
    out = channel_mod.clean("api_key=AAAA7777 and password%<i> </i>3Dhunter2 end")
    assert "AAAA7777" not in out and "hunter2" not in out, out


def test_markdown_cannot_be_formed_around_a_placeholder():
    out = channel_mod.clean("see [a](<IPV4_1>) and 10.0.0.9 and [b](10.0.0.9)")
    assert "](" not in out and "10.0.0.9" not in out, out
