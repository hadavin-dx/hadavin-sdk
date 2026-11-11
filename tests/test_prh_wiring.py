"""PR H, WP2a: what the producers hand to the redactor, and the approval card.

T7: no removed or space-like item reaches `runmap.redact` or the redactor's `find` from any producer path (a stand-in
records every call). T8 card: the payload of a string sequence is deleted and a placeholder forged by a hidden item is
written in the escaped look-alike form. Every test whose name starts `test_mf_` must FAIL on main."""

from __future__ import annotations

import importlib

import pytest

from hadavin_sdk import tools
from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.guard import runmap
from tests import hidden_oracle as oracle

redact_mod = importlib.import_module(
    "hadavin_sdk.guard.redact"
)  # the package also exports a function `redact`

ESC, BEL = "\x1b", "\x07"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
HIDDEN = oracle.REMOVED | oracle.SPACE_LIKE
ITEMS = sorted(HIDDEN) + [
    ESC + "[0m",
    ESC + "]0;t" + BEL,
    ESC + "Pq" + ESC + "\\",
    ESC + "(B",
    "\x9b0m",
    "\x90q\x9c",
]


def _paths():
    return {
        "untrusted": lambda t: runmap.redact_untrusted(t, {}),
        "tool": lambda t: tools.prepare_output(t, {}, 4000, []),
        "error": lambda t: tools.error_reason(ValueError(t), []),
        "head": lambda t: runmap.safe_head(t, 4000),
        "card": channel_mod.clean,
        "value": lambda t: runmap.redact_value({"k": t}, {}),
        "plain": lambda t: runmap.redact_text(t, {}),
    }


def _record(monkeypatch):
    seen_redact: list[str] = []
    seen_find: list[str] = []
    real_redact = runmap.redact
    real_find = redact_mod._Redactor.find

    def spy_redact(text, **kw):
        seen_redact.append(text)
        return real_redact(text, **kw)

    def spy_find(self, text):
        seen_find.append(text)
        return real_find(self, text)

    monkeypatch.setattr(runmap, "redact", spy_redact)
    monkeypatch.setattr(redact_mod._Redactor, "find", spy_find)
    return seen_redact, seen_find


def _bad(texts: list[str]) -> list[str]:
    return [t for t in texts if any(c in HIDDEN for c in t)]


@pytest.mark.parametrize("path", list(_paths()))
def test_mf_no_hidden_item_reaches_redact(path, monkeypatch):
    seen_redact, _ = _record(monkeypatch)
    run = _paths()[path]
    for item in ITEMS:
        run("id " + KEY[:4] + item + KEY[4:] + " and a" + item + "b end")
    assert seen_redact
    assert _bad(seen_redact) == []


@pytest.mark.parametrize("path", list(_paths()))
def test_mf_no_hidden_item_reaches_find(path, monkeypatch):
    _, seen_find = _record(monkeypatch)
    run = _paths()[path]
    for item in ITEMS:
        run("id " + KEY[:4] + item + KEY[4:] + " and a" + item + "b end")
    assert seen_find
    assert _bad(seen_find) == []


def test_mf_card_dcs_payload_deleted():
    """The payload of a device control string is not shown to the approver (a terminal hides it too)."""
    out = channel_mod.clean("a " + ESC + "Pq payload" + ESC + "\\" + " b")
    assert "payload" not in out, out


def test_mf_card_m5a():
    """A placeholder forged by a hidden item on the card is written escaped: one real `<IPV4_1>`, one look-alike."""
    out = channel_mod.clean("<" + ESC + "[0mIPV4_1> and 10.0.0.5")
    assert out.count("<IPV4_1>") == 1, out
    assert out.count("‹IPV4_1›") == 1, out
