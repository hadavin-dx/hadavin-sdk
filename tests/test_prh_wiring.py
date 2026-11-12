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

    def spy_find(self, text, readings=True, **kw):
        # `find` has a keyword of its own now (`swept`, the final guard); the spy passes every keyword on unchanged
        seen_find.append(text)
        return real_find(self, text, readings, **kw)

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


# a string sequence ends with ESC and a backslash; the backslash must not be read as the start of an escape of its own
# (`\n`, `\t`, `\r` or three octal digits) by the decoded readings, which would cut the value that follows
_ST = ESC + chr(92)
_STRING_OPENERS = {
    "osc": ESC + "]0;t",
    "dcs": ESC + "Pq",
    "sos": ESC + "Xq",
    "pm": ESC + "^q",
    "apc": ESC + "_q",
}
_CUT_VALUES = {
    "password": "pass" + "word=" + "hunter" + "2secretXYZ",
    "mail": "to " + "bob.smith" + "@" + "example.com",
    "uuid": "request_id " + "123e4567-e89b-12d3" + "-a456-426614174000",
}


@pytest.mark.parametrize("opener", sorted(_STRING_OPENERS))
@pytest.mark.parametrize("kind", sorted(_CUT_VALUES))
@pytest.mark.parametrize("path", ["untrusted", "tool", "error", "head"])
def test_mf_string_terminator_backslash_does_not_cut_the_value(path, kind, opener):
    plain = _CUT_VALUES[kind]
    value = plain.split("=")[-1] if kind == "password" else plain.split(" ", 1)[1]
    for cut in (3, 5, 7):
        text = (
            plain[: len(plain) - len(value) + cut]
            + _STRING_OPENERS[opener]
            + _ST
            + plain[len(plain) - len(value) + cut :]
        )
        out = _paths()[path](text)
        assert not any(value[i : i + 5] in out for i in range(len(value) - 4)), (
            path,
            kind,
            opener,
            cut,
            out,
        )


@pytest.mark.parametrize("cut", [chr(0x0B), chr(0x0C), chr(0x85)])
def test_card_masks_a_value_cut_by_a_character_the_card_deletes(cut):
    """The card's own cleaning deletes control characters before any value is looked for, so main masked a password
    cut by one (main passes this test; it is a step-back guard for the card)."""
    value = "hunter" + "2secretXYZ"
    for at in (1, 3, 5):
        text = "password=" + value[:at] + cut + value[at:] + " end"
        out = channel_mod.clean(text)
        assert not any(value[i : i + 5] in out for i in range(len(value) - 4)), (at, out)
