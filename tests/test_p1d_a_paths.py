"""Ticket G, part G2 (P1d-a): every approval text path redacts first and writes `[.]` last.

One test per path that produces text for a card or a channel (G2-I1), the request stored before the change (G2-I2), and
the three SECRET pattern changes with a wall-clock bound (G2-I3). Made-up data only: addresses, hosts and secret
values are built from parts.
"""

from __future__ import annotations

import hashlib
import importlib
import time
from types import SimpleNamespace

import pytest
from markdown_it import MarkdownIt

from hadavin_sdk.approvals import cards, channel, gate, slack_channel
from hadavin_sdk.approvals.requests import summary
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import GateDecision, Plan, Target

redact = importlib.import_module("hadavin_sdk.guard.redact")

EM = "anna" + "." + "m" + "@" + "example" + "." + "org"
HOST = "db-7" + "." + "corp" + "." + "internal"
PUBLIC = "docs" + "." + "example" + "." + "com"
PUBLIC_DEFANGED = PUBLIC.replace(".", "[.]")
TEXT = f"mail {EM} about {HOST}, see {PUBLIC} first"
VALUE = "Tq7mZ" + "4xKp2" + "Vb9Lr"


@pytest.fixture
def order(monkeypatch):
    """Records each call of the redactor and of `defang_text`, in order, with the text it was given."""
    events: list[tuple[str, str]] = []
    real_redact, real_defang = runmap.redact_text, gate.defang_text

    def spy_redact(text, *args, **kwargs):
        events.append(("redact", text))
        return real_redact(text, *args, **kwargs)

    def spy_defang(text):
        events.append(("defang", text))
        return real_defang(text)

    monkeypatch.setattr(runmap, "redact_text", spy_redact)
    monkeypatch.setattr(channel, "defang_text", spy_defang)
    monkeypatch.setattr(slack_channel, "defang_text", spy_defang)
    return events


def _check(shown: str, events: list[tuple[str, str]], path: str) -> None:
    """`shown` is masked and defanged, and on the way every redactor call came before the one defang that ended it."""
    plain = shown.replace("[.]", ".")
    assert EM not in plain, f"{path}: the address is shown: {shown!r}"
    assert HOST not in plain, f"{path}: the internal host is shown: {shown!r}"
    assert "<EMAIL_1>" in shown and "<HOSTNAME_1>" in shown, f"{path}: no placeholder: {shown!r}"
    assert PUBLIC_DEFANGED in shown and PUBLIC not in shown, f"{path}: not defanged: {shown!r}"
    kinds = [k for k, _ in events]
    assert "redact" in kinds and "defang" in kinds, f"{path}: {kinds}"
    assert kinds[-1] == "defang", f"{path}: the last step is not defang: {kinds}"
    first_defang = kinds.index("defang")
    assert "redact" in kinds[:first_defang], f"{path}: defang ran before the redactor: {kinds}"
    for kind, text in events:
        if kind == "defang":
            assert EM not in text and HOST not in text, f"{path}: defang got unmasked text {text!r}"
            assert "[.]" not in text, f"{path}: `[.]` was written before the last step: {text!r}"
        else:
            assert PUBLIC_DEFANGED not in text, f"{path}: the redactor got defanged text {text!r}"


def _plan() -> Plan:
    return Plan(
        run_id="run-1",
        agent_id="test-agent",
        action_id="create_draft_record",
        action_version=1,
        risk_class="reversible",
        inputs={"contact": EM, "host": HOST},
        target=Target(system="fixture-records", ref=None),
        idempotency_key="run-1:create_draft_record",
        expected_outcome=f"a draft, see {PUBLIC} first",
    )


def _slack() -> slack_channel.SlackChannel:
    return slack_channel.SlackChannel("C1", "not-a-token", "not-a-secret")


def _request(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        summary=text, current_step=0, steps=[1], approval_id="a", plan_hash="h", status="PENDING"
    )


# --- G2-I1: one test per path ------------------------------------------------------------------------------------
def test_path_channel_clean(order):
    _check(channel.clean(TEXT), order, "channel.clean")


def test_path_neutralise_hook_does_not_defang():
    # The hook the redactor calls on the text and on every decoded view writes no `[.]`.
    assert "[.]" not in channel._neutralise(TEXT)
    assert PUBLIC in channel._neutralise(TEXT)


def test_path_requests_summary(order):
    _check(summary(_plan()), order, "requests.summary")


def test_path_cards_render_shadow(order):
    plan = _plan()
    decision = GateDecision(
        run_id=plan.run_id, plan_hash=plan.hash(), outcome="allow", rule_id="class.reversible"
    )
    card = cards.render_shadow(plan, decision, ["call-1"], diagnosis=TEXT)
    _check(card.text, order, "cards.render_shadow")
    assert card.blocks[0]["text"] == card.text


def test_path_cards_render_abstain(order):
    card = cards.render_abstain("run-1", TEXT, [f"call-1 {EM}"])
    _check(card.text, order, "cards.render_abstain")
    assert card.blocks[0]["text"] == card.text


def test_path_fake_channel_send(order):
    ch = channel.FakeChannel()
    ch.send(_request(TEXT), ["fake:a"])
    _check(ch.sent[0][1], order, "FakeChannel.send")


def test_path_fake_channel_notify(order):
    ch = channel.FakeChannel()
    ch.notify("fake:a", TEXT)
    _check(ch.notices[0][1], order, "FakeChannel.notify")


def test_path_slack_blocks(order):
    shown = _slack()._blocks(_request(TEXT), ["slack:U1"])[0]["text"]["text"]
    _check(shown, order, "SlackChannel._blocks")


def test_path_slack_blocks_of_a_summary_built_by_summary(order):
    # The real flow: `summary()` cleans once (redact, defang), `_blocks` reads that stored text and does it again.
    stored = summary(_plan())
    order.clear()
    shown = _slack()._blocks(_request(stored), None)[0]["text"]["text"]
    assert shown == stored
    kinds = [k for k, _ in order]
    assert kinds[-1] == "defang" and "redact" in kinds[: kinds.index("defang")], kinds
    assert all("[.]" not in t.replace("<HOSTNAME_1>[.]", "") for k, t in order if k == "redact")


def test_path_slack_notify(order, monkeypatch):
    ch, calls = _slack(), []
    monkeypatch.setattr(ch, "_call", lambda method, body: calls.append((method, body)) or {})
    ch.notify("slack:U1", TEXT)
    (method, body), who = calls[0], "<@U1>: "
    assert method == "chat.postMessage" and body["text"].startswith(who)
    _check(body["text"][len(who) :], order, "SlackChannel.notify")


def test_path_slack_post_card_sends_the_card_text_unchanged(order, monkeypatch):
    ch, calls = _slack(), []
    card = cards.render_abstain("run-1", TEXT, [])
    _check(card.text, order, "cards.render_abstain")
    monkeypatch.setattr(
        ch, "_call", lambda method, body: calls.append((method, body)) or {"ts": "1.2"}
    )
    assert ch.post_card(card).ok
    assert calls[0][1]["blocks"][0]["text"] == {"type": "plain_text", "text": card.text}


# --- G2-I2: a request stored before the change -------------------------------------------------------------------
def test_stored_request_from_before_the_change_is_masked_on_the_slack_card(order):
    old = gate.withhold_commands(gate.sanitise_text(TEXT))  # what the old `clean` left unmasked
    assert EM.replace("example.", "example[.]") in old and HOST.replace(".", "[.]") in old
    assert gate.undefang_text(old).count("[.]") == 0
    shown = _slack()._blocks(_request(old), None)[0]["text"]["text"]
    _check(shown, order, "SlackChannel._blocks (stored request)")
    assert shown == channel.clean(TEXT)


def test_undefang_text_leaves_code_and_reads_a_placeholder_dot_as_a_dot():
    # Fix round: the `[.]` behind a placeholder is undone too, so the redactor reads a stored card as it read the
    # text before the defang (first written here as "stays `[.]`", which made `<EMAIL_1>[.]08::` read differently).
    assert gate.undefang_text("a[.]b `c[.]d` <HOSTNAME_1>[.]e") == "a.b `c[.]d` <HOSTNAME_1>.e"
    assert gate.defang_text(gate.undefang_text("<HOSTNAME_1>[.]e.com")) == "<HOSTNAME_1>[.]e[.]com"
    assert gate.undefang_text("x\n```\nc[.]d\n```\ny[.]z") == "x\n```\nc[.]d\n```\ny.z"


# --- G2-I3: the three SECRET pattern changes ---------------------------------------------------------------------
def _secret_patterns():
    plain = [p for k, p in redact.PATTERNS if k == "SECRET" and "(?<!&amp;)[\\w.\\-]*" in p.pattern]
    query = [
        p for k, p in redact.PATTERNS if k == "SECRET" and "(?<=&amp;))[\\w.\\-]*" in p.pattern
    ]
    assert len(plain) == 1 and len(query) == 1
    return plain[0], query[0]


def _masked(text: str) -> str:
    return runmap.redact_text(text, runmap.RunMap())


def test_secret_key_behind_a_long_prefix_is_masked():
    for n in (39, 40, 41, 60, 400):
        out = _masked("x" * n + "_pass" + "word=" + VALUE + " end")
        assert VALUE not in out and out.endswith(" end"), (n, out)


def test_secret_value_keeps_an_ampersand_in_the_plain_form():
    left, right = VALUE[:7], VALUE[7:]
    for amp in ("&", "&amp;"):
        out = _masked("pass" + "word=" + left + amp + right + " end")
        assert left not in out and right not in out and out.endswith(" end"), out


def test_secret_value_in_the_query_form_ends_at_the_next_parameter():
    left, right = VALUE[:7], VALUE[7:]
    for amp in ("&", "&amp;"):
        url = "https://" + PUBLIC + "/cb?to" + "ken=" + left + amp + "page=2"
        out = _masked(url)
        assert left not in out and out.endswith("page=2"), out
        out = _masked("https://" + PUBLIC + "/cb?to" + "ken=" + left + amp + right + " end")
        assert left not in out and right not in out and out.endswith(" end"), out


_N = 50_000
_HOSTILE = {
    "name run": "a" * _N,
    "name run with dots": "a.-_" * (_N // 4),
    "key word run": "to" + "ken" * (_N // 3),
    "key word run, then no value": "pass" * (_N // 4) + " ",
    "name run, then a value": "a" * _N + "pass" + "word=x",
    "query key word run": "?" + "to" + "ken" * (_N // 3),
    "ampersand value": "to" + "ken=" + "&a" * (_N // 2),
    "query ampersand value": "?to" + "ken=" + "&a" * (_N // 2),
    "query entity value": "?to" + "ken=" + "&amp;a" * (_N // 6),
    "query pairs": "?" + ("to" + "ken=a&") * (_N // 8),
    "comma value": "to" + "ken=" + ",a" * (_N // 2),
}


@pytest.mark.perf  # a wall-clock bound: measured under 0.05 s per pattern and 0.3 s per redact_text call
@pytest.mark.parametrize("name", sorted(_HOSTILE))
def test_secret_patterns_are_linear_on_a_50000_character_run(name):
    text = _HOSTILE[name]
    for pattern in _secret_patterns():
        t0 = time.perf_counter()
        pattern.findall(text)
        took = time.perf_counter() - t0
        assert took < 2.0, f"{name}: {took:.2f} s for {pattern.pattern[:40]!r}"
    t0 = time.perf_counter()
    try:
        runmap.redact_text(text, runmap.RunMap())
    except runmap.RedactionError:
        pass  # refusing (fail closed) is allowed; taking long is not
    took = time.perf_counter() - t0
    assert took < 10.0, f"{name}: redact_text took {took:.2f} s"


# --- fix round: defang over the whole token, glued addresses, a card that reads the same twice --------------------
EVIL = "evil" + "." + "com"
_PIECES = [
    EM, HOST, PUBLIC, EVIL, "www" + "." + "evil" + "." + "digital", "<HOSTNAME_1>", "<EMAIL_1>",
    "_", "*", "[", "]", "(", ")", "-", "@", ".", ",", ":", "/", "~", "0", "9", "x", "q", "é", "例",
    "。", " ", " ", "\n", "08::", "pass" + "word=", "&", "?",
]  # fmt: skip
_PIECES_CODE = [*_PIECES, "`", "`", "```"]
_LINKABLE = (
    gate._DOMAIN,
    gate._DOMAIN_LAST,
    gate._NON_ASCII_HOST,
    gate._PLACEHOLDER_DOT,
    gate._WIDE_DOTS,
)
_HALF = gate._NAME_DOT  # a plain dot between two name characters


def _glue(stream: str, pieces: list[str], count: int = 400) -> list[str]:
    """Seeded texts (no `random`): 3 to 14 pieces each, picked by sha256 of the stream name and a counter."""
    out, k = [], 0
    for _ in range(count):
        parts = []
        n = 3 + int(hashlib.sha256(f"{stream}:n:{k}".encode()).hexdigest(), 16) % 12
        for _ in range(n):
            k += 1
            parts.append(
                pieces[int(hashlib.sha256(f"{stream}:{k}".encode()).hexdigest(), 16) % len(pieces)]
            )
        out.append("".join(parts))
    return out


def _text_tokens(text: str):
    for tok in MarkdownIt("commonmark").parse(text):
        for child in tok.children or []:
            if child.type == "text":
                yield child.content


def _assert_not_linkable(shown: str, source: str) -> None:
    for piece in (shown, *_text_tokens(shown)):
        for rx in _LINKABLE:
            assert not rx.search(piece), (
                f"LINK: {source!r} -> {shown!r}: {piece!r} matches {rx.pattern}"
            )
        for token in gate._DOTTED_TOKEN.finditer(piece):
            if "[.]" in token.group(0):
                assert not _HALF.search(token.group(0)), (
                    f"HALF: {source!r} -> {shown!r}: {token.group(0)!r}"
                )


def test_defang_takes_every_dot_of_a_host_with_text_glued_on():
    done = PUBLIC_DEFANGED
    for tail in ("_x", "_", "0x", "9", "_x.y", "例"):
        assert gate.defang_text("see " + PUBLIC + tail).startswith("see " + done), tail
    assert gate.defang_text("see " + EVIL + "_x") == "see " + EVIL.replace(".", "[.]") + "_x"
    assert gate.defang_text("_a" + PUBLIC + "_") == "_a" + done + "_"
    assert gate.defang_text("<HOSTNAME_1>." + PUBLIC + "0x") == "<HOSTNAME_1>[.]" + done + "0x"
    assert gate.defang_text("v1.2 and 3.14") == "v1.2 and 3.14"  # no host: nothing written


def test_defang_reads_inline_code_as_a_renderer_does():
    # Unambiguous inline code stays; a backtick left over on another line shifts the pairs, so nothing is code.
    assert gate.defang_text("run `" + PUBLIC + "` now") == "run `" + PUBLIC + "` now"
    shifted = "a ` b\n`" + PUBLIC + "` c"
    assert gate.defang_text(shifted) == "a ` b\n`" + PUBLIC_DEFANGED + "` c"
    fenced = "x\n```\n" + PUBLIC + "\n```\n`" + PUBLIC + "` " + PUBLIC
    assert (
        gate.defang_text(fenced)
        == "x\n```\n" + PUBLIC + "\n```\n`" + PUBLIC + "` " + PUBLIC_DEFANGED
    )


def test_property_no_linkable_host_after_defang_text():
    for x in [*_glue("G2-defang", _PIECES), *_glue("G2-defang-code", _PIECES_CODE)]:
        once = gate.defang_text(x)
        if "`" not in x:
            _assert_not_linkable(once, x)
        assert gate.defang_text(once) == once, f"NOT IDEMPOTENT: {x!r} -> {once!r}"
        if "`" not in x:  # inside inline code a wide dot stays as written
            assert once.replace("[.]", ".") == gate._WIDE_DOTS.sub(".", x).replace("[.]", "."), (
                f"DOTS ONLY: {x!r}"
            )


def test_property_no_linkable_host_on_the_card_and_the_card_reads_the_same_twice():
    slack = _slack()
    for x in [*_glue("G2-card", _PIECES), *_glue("G2-card-code", _PIECES_CODE)]:
        shown = channel.clean(x)
        for text in _text_tokens(shown):
            for rx in _LINKABLE:
                assert not rx.search(text), (
                    f"LINK: {x!r} -> {shown!r}: {text!r} matches {rx.pattern}"
                )
        if "`" not in shown:
            _assert_not_linkable(shown, x)
        plain = shown.replace("[.]", ".")
        # The card shows no address or host the model's view masks. (An address with a digit or `_` glued behind
        # it is masked in neither: the EMAIL pattern ends at a word boundary. Not part of this fix.)
        model = runmap.redact_text(x, runmap.RunMap())
        for value in (EM, HOST):
            assert plain.count(value) <= model.count(value), f"SHOWN: {value!r}: {x!r} -> {shown!r}"
        again = slack._blocks(_request(shown), None)[0]["text"]["text"]
        assert again == shown, f"ROUND TRIP: {x!r}: {shown!r} / {again!r}"
        # a stored card is read again through `undefang_text` (SlackChannel._blocks, FakeChannel.send)
        assert channel.clean(gate.undefang_text(shown)) == shown, f"CLEAN TWICE: {x!r}: {shown!r}"


def test_glued_addresses_are_masked_whole_in_one_pass():
    for n in (2, 3, 5):
        for tail in ("", "sq", " end"):
            mapping = runmap.RunMap()
            out = runmap.redact_text("to " + EM * n + tail, mapping)
            assert "@" not in out and "example" not in out, (n, tail, out)
            seeded = runmap.RunMap({p: "\0seed" + p for p in mapping})
            assert runmap.redact_text(out, seeded) == out, (n, tail, out)
    assert _masked(EM + " " + EM) == "<EMAIL_1> <EMAIL_1>"  # separate addresses: as before


def test_card_of_a_text_whose_placeholder_starts_another_match_is_stable():
    for x in (
        "/08::" + "duglq" + HOST + " end",
        "pass" + "word=" + EM + "=&" + EM + "=g#c " + HOST,
    ):
        shown = channel.clean(x)
        assert _slack()._blocks(_request(shown), None)[0]["text"]["text"] == shown, (x, shown)


def test_stored_request_from_before_the_change_is_masked_by_the_fake_channel():
    old = gate.withhold_commands(gate.sanitise_text(TEXT))
    ch = channel.FakeChannel()
    ch.send(_request(old), ["fake:a"])
    assert ch.sent[0][1] == channel.clean(TEXT)
    assert EM not in ch.sent[0][1].replace("[.]", ".")


@pytest.mark.perf  # a wall-clock bound: measured well under 1 s each
@pytest.mark.parametrize("unit", [EM, "a@b.cc", "a@b.cc.", EM + "."])
def test_glued_addresses_are_linear(unit):
    text = unit * (40_000 // len(unit))
    t0 = time.perf_counter()
    try:
        runmap.redact_text(text, runmap.RunMap())
    except runmap.RedactionError:
        pass
    took = time.perf_counter() - t0
    assert took < 10.0, f"{unit!r}: {took:.2f} s"
    t0 = time.perf_counter()
    gate.defang_text((PUBLIC + "_") * 5_000 + ("a." * 20_000))
    assert time.perf_counter() - t0 < 5.0
