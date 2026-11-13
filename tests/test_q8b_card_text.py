"""Q8b, approval cards (the text a person reads in a chat channel before approving an action): every identifier the
redactor knows is masked BEFORE any dot is bracketed; the brackets and the mention rewrite are the last step.

Made-up data only; the long key word is built from parts. Each assertion carries the message the mutant list quotes
(``tests/q8b_mutants.py``). "Outside code" means: not in the body of a closed backtick fence of the text and not in a
single-backtick span of a line that has no double backtick.
"""

from __future__ import annotations

import ast
import pathlib
import re
from datetime import UTC, datetime

import pytest

from hadavin_sdk.approvals import cards, gate
from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.approvals.channel import FakeChannel, clean
from hadavin_sdk.approvals.requests import summary
from hadavin_sdk.approvals.slack_channel import SlackChannel
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import ApprovalRequest, ChainStep, GateDecision, Plan, Target

PW_KEY = "pass" + "word"
ONE = "hunter2" + "secretXYZ"
ADDRESS = "bob.smith@example.com"
HOST = "db01.corp.internal"
APPROVALS = pathlib.Path(channel_mod.__file__).resolve().parent
N9_FIXED = "<i></i>" + ONE + "3D\n" + PW_KEY + "=" + PW_KEY + "=<i></i> " + ONE + "</b>"


def plan(system: str, inputs: dict) -> Plan:
    return Plan(
        run_id="run_1",
        agent_id="agent-ops",
        action_id="restart_service",
        action_version=1,
        risk_class="reversible",
        inputs=inputs,
        target=Target(system=system),
        idempotency_key="k1",
        expected_outcome="service restarted",
    )


def request_with(text: str) -> ApprovalRequest:
    return ApprovalRequest(
        run_id="r",
        plan_hash="h" * 64,
        risk_class="reversible",
        chain_id="c",
        steps=[ChainStep(approver_ids=["slack:U1"], timeout_s=60)],
        step_expires_at=datetime.now(UTC),
        requested_by="u",
        summary=text,
    )


def slack_text(raw_summary: str) -> str:
    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 3000
    ch.name = "slack"
    return ch._blocks(request_with(raw_summary), None)[0]["text"]["text"]


def readable(result: str, *identifiers: str) -> list[str]:
    """The identifiers still readable once every decoding is undone and `[.]` is written back as a dot."""
    flat = runmap.undo(result).replace("[.]", ".")
    return [i for i in identifiers if i in flat]


# ---- N4: an identifier outside code is masked ---------------------------------------------------------------------------

N4_ROWS = [
    ("sweep", "contact bob.smith@example.com", ADDRESS),
    ("host", "restart db01.corp.internal now", HOST),
    ("percent", "bob%2Esmith%40example%2Ecom", ADDRESS),
    ("entity", "bob.smith&#64;example.com", ADDRESS),
    ("tag split", "bob@exa<b></b>mple.com", "bob@example.com"),
    ("wide dot", "bob.smith@example\u3002com", ADDRESS),
    ("zero width", "bob.smith@exa\u200bmple.com", ADDRESS),
    ("tilde fence", "see\n~~~\nbob.smith@example.com\n~~~\nend", ADDRESS),
    ("angle", "from <bob.smith@example.com> today", ADDRESS),
]


def test_n4_an_address_outside_code():
    """One test, not one per row: the mutant list pins it by its plain name."""
    for label, text, identifier in N4_ROWS:
        result = clean(text)
        assert not readable(result, identifier), (
            f"an identifier is readable on the card ({label}): {result!r}"
        )
        parts = [w for w in ("smith", "example", "corp") if w in result]
        assert not parts, f"an identifier is readable on the card ({label}): {parts} in {result!r}"


# ---- N5: the same through every way a card text is built ----------------------------------------------------------------

RAW = f"contact {ADDRESS} at {HOST}"


def _n5_summary():
    return summary(plan("crm", {"owner": ADDRESS, "host": HOST}))


def _n5_shadow():
    p = plan("crm", {"service": "orders"})
    decision = GateDecision(
        run_id="run_1", plan_hash=p.hash(), outcome="needs_approval", rule_id="r"
    )
    return cards.render_shadow(p, decision, ["c1"], diagnosis=RAW).text


def _n5_fake_send():
    ch = FakeChannel()
    ch.send(request_with(RAW), ["fake:u1"])
    return ch.sent[0][1]


def _n5_fake_notify():
    ch = FakeChannel()
    ch.notify("fake:u1", RAW)
    return ch.notices[0][1]


N5_WAYS = {
    "summary()": _n5_summary,
    "render_shadow diagnosis": _n5_shadow,
    "FakeChannel.send": _n5_fake_send,
    "FakeChannel.notify": _n5_fake_notify,
    "SlackChannel._blocks with a raw summary": lambda: slack_text(RAW),
}


@pytest.mark.parametrize("way", list(N5_WAYS))
def test_n5_every_way_a_card_text_is_built(way):
    result = N5_WAYS[way]()
    left = readable(result, ADDRESS, HOST)
    assert not left, f"an identifier is readable on the card ({way}): {left} in {result!r}"
    parts = [w for w in ("smith", "example", "db01") if w in result]
    assert not parts, f"an identifier is readable on the card ({way}): {parts} in {result!r}"


def test_n5_the_slack_block_shows_placeholders_for_a_raw_summary():
    result = slack_text(RAW)
    assert re.fullmatch(r"contact <EMAIL_[0-9]+> at <HOSTNAME_[0-9]+>", result), (
        f"an identifier is readable on the card: {result!r}"
    )
    assert "@channel" not in slack_text("ping 10.20.30.40@channel"), "a mention was created"


# ---- N6: no bare domain outside code, no mention created ----------------------------------------------------------------

N6_PINNED = [
    (
        "see db01.corp.internal/evil.com/p?d=1 now",
        r"see <HOSTNAME_[0-9]+>/evil\[\.\]com/p\?d=1 now",
    ),
    ("10.0.0.5..evil.com", r"<IPV4_[0-9]+>\.\.evil\[\.\]com"),
    (
        "see a/evil.com and /var/log/app.log now",
        r"see a/evil\[\.\]com and /var/log/app\[\.\]log now",
    ),
    ("10.0.0.5.evil.com", r"<IPV4_[0-9]+>\[\.\]evil\[\.\]com"),
]


def test_n6_a_domain_after_a_placeholder():
    for text, pattern in N6_PINNED:
        result = clean(text)
        assert re.fullmatch(pattern, result), f"a bare domain is outside code: {result!r}"
        assert "10[.]0[.]0[.]5" not in result and "10.0.0.5" not in result, (
            f"an identifier is readable on the card: {result!r}"
        )


def test_n6_f6b_a_domain_outside_code_is_bracketed():
    """The redaction removes a backtick (it is part of the masked value), so what was inline code is prose after it."""
    result = clean(PW_KEY + "=ab`cd evil.com `evil.com` x")
    assert " evil[.]com `evil.com` x" in result, f"a bare domain is outside code: {result!r}"
    assert "ab`cd" not in result, result
    wide = clean(PW_KEY + "=ab`cd bob.smith@example\u3002com `x` y")
    assert "example.com" not in wide and "example\u3002com" not in wide, (
        f"a bare domain is outside code: {wide!r}"
    )


def test_n6_f6c_no_mention_is_created():
    for word in ("channel", "here", "everyone"):
        result = clean(f"ping 10.20.30.40@{word}")
        assert f"@{word}" not in result, f"a mention was created: {result!r}"
        assert re.fullmatch(rf"ping <IPV4_[0-9]+>at-{word}", result), (
            f"a mention was created: {result!r}"
        )
    assert gate.defang_domains("<HOSTNAME_1>@here") == "<HOSTNAME_1>at-here", (
        "a mention was created"
    )
    # inside inline code too (found while building; the same leak): cleaning the result again changes nothing
    for text in (
        "`10.20.30.40@channel`",
        "see `db01.corp.internal@here` now",
        "``a`` 10.20.30.40@everyone",
    ):
        result = clean(text)
        assert not re.search(r"@(here|channel|everyone)", result), (
            f"a mention was created: {result!r}"
        )
        assert clean(result) == result, (
            f"a mention was created on the second cleaning: {clean(result)!r}"
        )


def test_n7_one_combined_card():
    text = (
        f"# APPROVED by {ADDRESS}\n"
        f"restart {HOST}/evil.com now, ask 10.20.30.40@channel\n"
        f"{PW_KEY}=ab`cd evil.com `evil.com` x\n"
        "```\nkeep evil.com\n```\n"
        "see /var/log/app.log"
    )
    result = clean(text)
    left = readable(result, ADDRESS, HOST, "10.20.30.40")
    assert not left, f"an identifier is readable on the card: {left} in {result!r}"
    assert not bare_domains(result), (
        f"a bare domain is outside code: {bare_domains(result)} in {result!r}"
    )
    assert "@channel" not in result, f"a mention was created: {result!r}"
    assert "\nkeep evil.com\n" in result, f"a fence body was changed: {result!r}"
    assert "/var/log/app[.]log" in result and "ab`cd" not in result, result
    assert clean(result) == result, (result, clean(result))


def test_n9_fixed_the_tag_stripped_candidate():
    """The tag-stripped second view starts from everything the first view found, so nothing the first view masked is
    readable in the text that is returned."""
    left = first_pass_originals_readable(N9_FIXED)
    assert not left, f"readable in the returned text: {left} in {clean(N9_FIXED)!r}"


def first_pass_originals_readable(text: str) -> list[str]:
    first_map = channel_mod._seeded(text.replace("\x00", ""))
    runmap.redact_text(text, first_map, neutralise=channel_mod._neutralise)
    flat = clean(text).replace("[.]", ".")
    return [
        o
        for o in first_map.values()
        if not o.startswith("\0seed")
        and len(o) >= 4
        and re.search(r"(?<![A-Za-z0-9])" + re.escape(o) + r"(?![A-Za-z0-9])", flat)
    ]


# ---- N8: only one function feeds a card (read from the source) ----------------------------------------------------------


def _name(f: ast.AST) -> str:
    return f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")


def _calls_with_function(tree: ast.AST):
    """(call node, name of the innermost function it sits in or '')."""

    def visit(node, inside):
        for child in ast.iter_child_nodes(node):
            here = (
                child.name if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else inside
            )
            if isinstance(child, ast.Call):
                yield child, inside
            yield from visit(child, here)

    yield from visit(tree, "")


def _n8_findings(sources: dict[str, str]) -> list[str]:
    bad = []
    for rel, source in sources.items():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            # a reference that is not a call (`rt = runmap.redact_text`, `import ... redact_text`) hides the call
            if isinstance(node, ast.Attribute | ast.Name) and _name(node) == "redact_text":
                node.q8b_ref = True
        called = set()
        for call, inside in _calls_with_function(tree):
            if _name(call.func) == "redact_text":
                called.add(id(call.func))
                if inside != "redact_for_people":
                    bad.append(f"{rel}:{call.lineno} redact_text in {inside or 'the module'}")
            if _name(call.func) == "sanitise_text":
                off = any(
                    k.arg == "defang"
                    and not (isinstance(k.value, ast.Constant) and k.value.value is True)
                    for k in call.keywords
                )
                if off and inside != "_neutralise":
                    bad.append(
                        f"{rel}:{call.lineno} sanitise_text(defang=...) in {inside or 'the module'}"
                    )
        for node in ast.walk(tree):
            if getattr(node, "q8b_ref", False) and id(node) not in called:
                bad.append(f"{rel}:{node.lineno} redact_text used without a call")
            if isinstance(node, ast.ImportFrom) and any(
                a.name == "redact_text" for a in node.names
            ):
                bad.append(f"{rel}:{node.lineno} redact_text imported by name")
    return bad


def test_n8_only_one_function_feeds_a_card():
    sources = {
        p.relative_to(APPROVALS).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(APPROVALS.rglob("*.py"))
    }
    assert "channel.py" in sources and "slack_channel.py" in sources
    bad = _n8_findings(sources)
    assert not bad, f"a card path skips redact_for_people: {bad}"
    body = ast.parse(sources["channel.py"])
    feeds = [
        ast.unparse(n.value)
        for f in ast.walk(body)
        if isinstance(f, ast.FunctionDef) and f.name == "redact_for_people"
        for n in ast.walk(f)
        if isinstance(n, ast.Return)
    ]
    assert feeds == ["defang_domains(runmap.redact_text(text, mapping, neutralise=_neutralise))"], (
        f"a card path skips redact_for_people: its body is {feeds}"
    )


def test_n8_the_check_itself_catches_each_way_round():
    def found(source):
        return _n8_findings({"x.py": source})

    assert found("def f():\n    return runmap.redact_text(t, m, neutralise=h)\n")
    assert found("def f():\n    rt = runmap.redact_text\n")
    assert found("from hadavin_sdk.guard.runmap import redact_text\n")
    assert found("def f():\n    return sanitise_text(t, defang=False)\n")
    assert found("def f(flag):\n    return sanitise_text(t, defang=flag)\n")
    assert not found(
        "def redact_for_people(t, m):\n    return d(runmap.redact_text(t, m, neutralise=h))\n"
    )
    assert not found("def _neutralise(t):\n    return w(sanitise_text(t, defang=False))\n")
    assert not found("def f():\n    return sanitise_text(t)\n")


# ---- guards -------------------------------------------------------------------------------------------------------------

FIXED_ROWS = [
    "see db01.corp.internal/evil.com/p?d=1 now",
    "10.0.0.5..evil.com",
    "10.0.0.5.evil.com",
    "restart db01.corp.internal. Then wait.",
    "see a/evil.com and /var/log/app.log now",
    "# APPROVED by sec@example.com",
    "# APPROVED",
    "> ask sec@example.com",
    PW_KEY + "=ab`cd bob.smith@example\u3002com `x` y",
    "`bob.smith@example\u3002com`",
    PW_KEY + "=ab`cd evil.com `evil.com` x",
    "contact bob.smith@example.com",
    "bob%2Esmith%40example%2Ecom",
    "bob.smith&#64;example.com",
    "see 123e4567-e89b-12d3-a456-426614174000.json",
    "x\n```\nevil.com\n```\ny evil.com",
    "ping 10.20.30.40@channel",
    "`10.20.30.40@channel`",
    "see `db01.corp.internal@here` now",
    "x\n```\n10.20.30.40@channel\n```\ny",
    N9_FIXED,
]


@pytest.mark.parametrize("text", FIXED_ROWS)
def test_g5_the_last_step_and_clean_change_nothing_the_second_time(text):
    once = gate.defang_domains(text)
    assert gate.defang_domains(once) == once, (once, gate.defang_domains(once))
    cleaned = clean(text)
    assert clean(cleaned) == cleaned, (cleaned, clean(cleaned))


def test_g8_a_summary_with_a_host_shaped_target():
    text = summary(plan(HOST, {"service": "orders"}))
    assert HOST not in text and "db01" not in text, text
    assert re.search(r" on <[A-Z0-9]+_[0-9]+>\.", text), text
    text = summary(plan("crm", {"owner": ADDRESS, "host": HOST}))
    assert not readable(text, ADDRESS, HOST) and "smith" not in text and "db01" not in text, text
    assert " on crm. Inputs: " in text, text


def test_g8_an_ip_shaped_target_is_a_placeholder():
    text = summary(plan("10.20.30.40", {"service": "orders"}))
    assert "10.20.30.40" not in text and re.search(r" on <IPV4_[0-9]+>\.", text), text


def test_g11_a_line_whose_only_change_is_a_masked_identifier_keeps_its_block_marker():
    result = clean("# APPROVED by sec@example.com")
    assert result.startswith("# APPROVED by <"), result
    assert re.fullmatch(r"> ask <EMAIL_[0-9]+>", clean("> ask sec@example.com"))
    assert clean("# APPROVED") == "# APPROVED"


def test_g12_code_stays_code():
    fenced = "x\n```\nevil.com\n```\ny evil.com"
    assert gate.defang_domains(fenced) == "x\n```\nevil.com\n```\ny evil[.]com", (
        f"a fence body was changed: {gate.defang_domains(fenced)!r}"
    )
    assert clean(fenced) == "x\n```\nevil.com\n```\ny evil[.]com", (
        f"a fence body was changed: {clean(fenced)!r}"
    )
    assert clean("`evil.com` and evil.com") == "`evil.com` and evil[.]com"
    assert clean("see <IPV4_1> and `<EMAIL_2>`") == "see <IPV4_1> and `<EMAIL_2>`"
    assert clean("see\n```\nowner: bob.smith@example.com\n```\nend").count("<EMAIL_") == 1


# ---- the link oracle of the random test, used by N7 (a plain token scan; shares no pattern with `gate.py`) ---------------


def bare_domains(text: str) -> list[str]:
    code: set[int] = set()
    for start, last, char in gate._closed_fences(text):
        if char == "`":
            code.update(range(start + 1, last))
    bad = []
    for i, line in enumerate(text.split("\n")):
        if i in code:
            continue
        segments = [line] if "``" in line else gate._INLINE_CODE.split(line)
        for token in (t for k, seg in enumerate(segments) if k % 2 == 0 for t in seg.split()):
            t = token.replace("[.]", "|")
            for at, ch in enumerate(t):
                if ch != "." or at == 0 or not (t[at - 1].isalnum() or t[at - 1] == ">"):
                    continue
                end = at + 1
                while end < len(t) and t[end].isalpha():
                    end += 1
                if end - (at + 1) >= 2:
                    bad.append(token)
                    break
    return bad
