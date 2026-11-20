"""Ticket G, part G2 (P1d-a): every approval text path redacts first and writes `[.]` last.

One test per path that produces text for a card or a channel (G2-I1), the request stored before the change (G2-I2), and
the three SECRET pattern changes with a wall-clock bound (G2-I3). Made-up data only: addresses, hosts and secret
values are built from parts.
"""

from __future__ import annotations

import importlib
import time
from types import SimpleNamespace

import pytest

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


def test_undefang_text_leaves_code_and_placeholder_dots():
    assert gate.undefang_text("a[.]b `c[.]d` <HOSTNAME_1>[.]e") == "a.b `c[.]d` <HOSTNAME_1>[.]e"
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
