"""Ticket G, integration of the text parts (invariant G3-I6): P1d-a (redact first, `[.]` last, glued e-mail addresses),
the fold scan of P2d-1 (look-alike spellings) and G7 (the pattern table once more after the sweep) on ONE tree.

One approval card text holds a look-alike spelling of a host the text also names in clear, two e-mail addresses glued
together with a digit or `_` behind them, and a bank code whose account stands beside a second copy of the code. One
`channel.clean()` must give a card that is fully masked, fully defanged and stable: reading it again, as `clean` or as
the Slack channel does, changes nothing. The same text for the model: one `redact_text` masks all of it and a second
call changes neither the text nor the map.

Made-up data only: every address, host, bank code and account is built from parts; the look-alike letters are escapes.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from hadavin_sdk.approvals import channel, gate, slack_channel
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import FOLD_NOTE, redact
from hadavin_sdk.guard.textnorm import fold

EM = "anna" + "." + "m" + "@" + "example" + "." + "org"
HOST = "db-7" + "." + "corp" + "." + "internal"
CYRILLIC = HOST.replace("e", "е")  # a letter of another script: the line is withheld
WIDE = HOST.replace("d", "ｄ")  # a full-width letter: runmap's NFKC view reads it, masked in place
PUBLIC = "docs" + "." + "example" + "." + "com"
PUBLIC_DEFANGED = PUBLIC.replace(".", "[.]")
BSB, ACCOUNT = "062" + "-" + "000", "1234" + "5678"
PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9]*_[0-9]+>")
# a name a renderer would turn into a link: dotted, ending in letters, not written with `[.]`
LINKABLE = re.compile(r"(?<![\w.\[/-])(?:[\w-]+\.)+[a-z]{2,24}(?![\w@-])", re.IGNORECASE)


def _text(look: str, glue: str, sep: str = "\n") -> str:
    return sep.join(
        (
            f"restart {HOST} then check {look}",
            f"mail {EM}{EM}{glue} about it, see {PUBLIC}",
            f"BSB: {BSB}",
            f"refund paid {BSB}/{ACCOUNT}",
        )
    )


def _slack(shown: str) -> str:
    ch = slack_channel.SlackChannel.__new__(slack_channel.SlackChannel)
    ch.max_card_chars = 2900
    req = SimpleNamespace(
        summary=shown, current_step=0, steps=[1], approval_id="a", status="PENDING"
    )
    return ch._blocks(req, None)[0]["text"]["text"]


def _nothing_readable(shown: str, where: str) -> None:
    plain = shown.replace("[.]", ".")
    for view in (plain, fold(plain)):
        assert HOST not in view, f"{where}: the host is readable: {shown!r}"
        assert "@" not in view and "example.org" not in view, f"{where}: an address: {shown!r}"
        assert ACCOUNT not in view, f"{where}: the account is readable: {shown!r}"
        assert BSB not in view, f"{where}: the bank code is readable: {shown!r}"
    assert CYRILLIC not in shown and WIDE not in shown, f"{where}: the look-alike is shown"
    assert "е" not in shown and "ｄ" not in shown, f"{where}: a look-alike letter"


CARDS = {
    # the look-alike is of another script: its line is withheld, with the placeholder of the host it hid
    ("cyrillic", "9"): (
        f"{FOLD_NOTE} <HOSTNAME_1>\n"
        f"mail <EMAIL_1><EMAIL_2>9 about it, see {PUBLIC_DEFANGED}\n"
        "BSB: <BANKCODE_1>\n"
        "refund paid <BANKCODE_1>/<BANKACCT_1>"
    ),
    ("cyrillic", "_x"): (
        f"{FOLD_NOTE} <HOSTNAME_1>\n"
        f"mail <EMAIL_1><EMAIL_2>_x about it, see {PUBLIC_DEFANGED}\n"
        "BSB: <BANKCODE_1>\n"
        "refund paid <BANKCODE_1>/<BANKACCT_1>"
    ),
    # a full-width letter: both spellings get the one placeholder, in the line as written
    ("wide", "9"): (
        "restart <HOSTNAME_1> then check <HOSTNAME_1>\n"
        f"mail <EMAIL_1><EMAIL_2>9 about it, see {PUBLIC_DEFANGED}\n"
        "BSB: <BANKCODE_1>\n"
        "refund paid <BANKCODE_1>/<BANKACCT_1>"
    ),
    ("wide", "_x"): (
        "restart <HOSTNAME_1> then check <HOSTNAME_1>\n"
        f"mail <EMAIL_1><EMAIL_2>_x about it, see {PUBLIC_DEFANGED}\n"
        "BSB: <BANKCODE_1>\n"
        "refund paid <BANKCODE_1>/<BANKACCT_1>"
    ),
}
LOOK = {"cyrillic": CYRILLIC, "wide": WIDE}


@pytest.mark.parametrize(("look", "glue"), sorted(CARDS))
def test_one_clean_gives_a_masked_defanged_card_and_a_second_pass_changes_nothing(look, glue):
    text = _text(LOOK[look], glue)
    assert HOST in text and LOOK[look] in text and HOST not in text.replace(HOST, "", 1)
    shown = channel.clean(text)
    assert shown == CARDS[look, glue], f"TOGETHER-CARD {look} {glue}: {shown!r}"
    _nothing_readable(shown, f"card {look} {glue}")
    # fully defanged: the public name is written with `[.]`, and nothing a renderer links is left
    assert PUBLIC not in shown and PUBLIC_DEFANGED in shown
    assert not LINKABLE.search(PLACEHOLDER.sub("", shown)), f"TOGETHER-LINK: {shown!r}"
    # stable: the three ways the stored card is read again
    assert channel.clean(shown) == shown, "TOGETHER-STABLE: clean of the card"
    assert channel.clean(gate.undefang_text(shown)) == shown, (
        "TOGETHER-STABLE: clean of the undefanged card"
    )
    assert _slack(shown) == shown, "TOGETHER-STABLE: the Slack re-render"


@pytest.mark.parametrize(("look", "glue"), sorted(CARDS))
def test_the_same_text_for_the_model_is_masked_in_one_call_and_a_second_call_changes_nothing(
    look, glue
):
    text = _text(LOOK[look], glue)
    mapping = runmap.RunMap()
    out = runmap.redact_text(text, mapping)
    # the model's text is the card before the last step: the same masks, the public name not defanged
    assert out == CARDS[look, glue].replace(PUBLIC_DEFANGED, PUBLIC), f"TOGETHER-MODEL: {out!r}"
    _nothing_readable(out, f"model {look} {glue}")
    held = dict(mapping)
    # G7: the account is found although only the sweep wrote the code's placeholder before it
    assert held["<BANKCODE_1>"] == BSB and held["<BANKACCT_1>"] == ACCOUNT
    assert (
        held["<HOSTNAME_1>"] == HOST
    )  # the look-alike got the known host's placeholder, no second entry
    assert sum(1 for p in held if p.startswith("<HOSTNAME_")) == 1
    assert runmap.redact_text(out, mapping) == out, "TOGETHER-MODEL-TWICE: the text changed"
    assert dict(mapping) == held, "TOGETHER-MODEL-TWICE: the map changed"


def test_all_of_it_on_one_line_with_a_lookalike_of_another_script_is_withheld_whole_and_stable():
    text = _text(CYRILLIC, "9", sep=", ")
    shown = channel.clean(text)
    assert shown.startswith(FOLD_NOTE + " "), shown
    rest = shown[len(FOLD_NOTE) :]
    # nothing of the line is left but the note, placeholders and the bank keyword the cleaning kept
    assert not PLACEHOLDER.sub("", rest).replace("BSB:", "").strip(), (
        f"TOGETHER-ONE-LINE: {shown!r}"
    )
    assert "<HOSTNAME_1>" in shown and "<EMAIL_1>" in shown and "<BANKCODE_1>" in shown
    _nothing_readable(shown, "one line")
    assert PUBLIC not in shown
    assert channel.clean(shown) == shown and _slack(shown) == shown


def test_the_glued_digit_does_not_unmask_the_address_on_the_card_or_for_the_model():
    """ORDER 016c item 15 on the combined tree: before the fix `anna.m@example.org9` was shown whole on both."""
    for glue in ("9", "_x", "08"):
        text = f"mail {EM}{glue} now"
        card = channel.clean(text)
        model = runmap.redact_text(text, runmap.RunMap())
        for out in (card, model):
            assert "@" not in out and "example" not in out, (glue, out)
            assert out.startswith("mail <EMAIL_1>"), (glue, out)


def test_clean_reads_its_result_again_at_most_three_times_and_then_stops(monkeypatch):
    """ORDER 016c item 14: the cap of `channel._settled`. A reader that never settles (every pass writes something
    new) is read 3 times and the last result is returned: it does not loop and does not raise (it stops, as designed)."""
    assert channel._MAX_REREADS == 3
    calls = []

    def never_settles(text, mapping, **kw):
        calls.append(text)
        return text + "x"

    monkeypatch.setattr(channel.runmap, "redact_text", never_settles)
    shown = channel._settled("start")
    # the stop is at the third re-read: three calls, and the text of the third is what comes back
    assert len(calls) == 3, calls
    assert shown == "start" + "xxx", shown


def test_clean_stops_after_the_first_reread_when_nothing_changes(monkeypatch):
    calls = []
    real = channel.runmap.redact_text

    def count(text, mapping, **kw):
        calls.append(text)
        return real(text, mapping, **kw)

    monkeypatch.setattr(channel.runmap, "redact_text", count)
    assert channel._settled("nothing to hide here") == "nothing to hide here"
    assert len(calls) == 1


@pytest.mark.parametrize("glue", ["9", "_x", "08", "_"])
def test_glued_email_regression_digit_or_underscore_behind_the_address(glue):
    """ORDER 016c item 15: `anna.m@example.org9` was shown whole to the model and on the card (the pattern ended in `\\b`)."""
    text = f"contact {EM}{glue} today"
    for out in (channel.clean(text), runmap.redact_text(text, runmap.RunMap())):
        assert "@" not in out and "example" not in out and "anna" not in out, out
        assert out.startswith("contact <EMAIL_1>"), out
        assert f"{glue} today" in out, out


GLUED = ("9", "_x", "a")
KINDS = {
    "host name": "db-7" + ".corp" + ".internal",
    "IPv4": "10.20." + "30.40",
    "phone": "+49 30 " + "1234567",
    "IBAN": "DE89" + "3704" + "0044" + "0532" + "0130" + "00",
}


@pytest.mark.parametrize("kind", ["host name", "tenant id", "account id", "secret", "bearer token"])
def test_glued_rest_other_kinds_with_no_gap(kind):
    """The value kinds probed for the glued-rest gap that have none (ORDER 016c item 15): the value is masked whatever follows."""
    text = {
        "host name": "x " + KINDS["host name"] + "{g} y",
        "tenant id": "tenant_id=acme" + "-corp-42{g} y",
        "account id": "account_id: 88123" + "456{g} y",
        "secret": "password=hunter" + "2xyz{g} y",
        "bearer token": "Bearer abcdef" + "0123456789abcd{g} y",
    }[kind]
    secret = {
        "host name": "db-7.corp",
        "tenant id": "acme-corp-42",
        "account id": "88123456",
        "secret": "hunter2xyz",
        "bearer token": "abcdef0123456789abcd",
    }[kind]
    for g in GLUED:
        out = redact(text.format(g=g)).text
        assert secret not in out, (kind, g, out)
