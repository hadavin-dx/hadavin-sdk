"""Review 5 of PR #42 (b78edeb), last batch.

(a) The scrub swaps the text for its DECODED view when another secret is whole, and that turns a half-written `&#10`
    into a newline and `%C3` into U+FFFD before the fragment strip ran. The strip now also runs on the cut text BEFORE
    the scrub.
(b) JSON writes an astral character as a surrogate pair; `_decoded` joins a valid pair, so a secret with an astral
    character written entirely as `\\uXXXX` escapes is found whole.
(d) A cut after `%C3` (an accent-first secret) or `%F0%9F` (an astral-first one) leaves no percent tail."""

from __future__ import annotations

import pytest

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod

CAP = defaults.MAX_REDACT_CHARS
RAW_CAP = 4096
CUT_AT = RAW_CAP - tools_mod.TAIL_WINDOW
BS = chr(92)
OTHER = "Hy8@" + "Rt4nWs6d"  # a fake, built from parts
ASCII = "Zk3#" + "9qWd"
ACCENT = chr(0xE9) + "Tn2Kq8x"
ASTRAL = chr(0x1F600) + "Lm4Qa7"


def _entity(s: str) -> str:
    return "".join(f"&#{ord(c)};" for c in s)


def _percent(s: str) -> str:
    return "".join(f"%{b:02X}" for b in s.encode())


def _json(s: str) -> str:
    out = []
    for c in s:
        n = ord(c)
        if n < 0x10000:
            out.append(f"{BS}u{n:04x}")
        else:
            n -= 0x10000
            out.append(f"{BS}u{0xD800 + (n >> 10):04x}{BS}u{0xDC00 + (n & 0x3FF):04x}")
    return "".join(out)


def _cut_body(spelled: str, off: int, secrets: list[str], other_spelled: str) -> str:
    head = spelled[:off]
    pad = "." * (CUT_AT - len(head) - len(other_spelled) - 10)
    raw = pad + other_spelled + "." * 10 + head + spelled[off:] + "." * 600
    out = tools_mod.prepare_output(raw, {}, CAP, secrets, raw_cap=RAW_CAP)
    assert out.endswith(tools_mod.TRUNCATED)
    return out[: -len(tools_mod.TRUNCATED)]


# (a) another secret whole earlier: the decoded view replaces the text, the cut tail must already be gone ---------------


@pytest.mark.parametrize(
    ("secret", "spell", "off", "tail_text"),
    [
        (
            ASCII,
            _entity,
            len("&#90;&#10"),
            "&#10",
        ),  # after the first entity and the start of the next
        (ASCII, _entity, len("&#90;&#10"), "\n"),  # the decoded form of that start
        (ACCENT, _percent, len("%C3"), "%C3"),
        (ACCENT, _percent, len("%C3"), chr(0xFFFD)),
        (ASTRAL, _percent, len("%F0%9F"), "%F0%9F"),
        (ASTRAL, _percent, len("%F0%9F"), chr(0xFFFD)),
        (ASTRAL, _json, len(BS + "ud83d" + BS + "ude0"), BS + "ude0"),
    ],
    ids=[
        "entity-raw",
        "entity-newline",
        "accent-raw",
        "accent-fffd",
        "astral-raw",
        "astral-fffd",
        "json-half-pair",
    ],
)
def test_a_cut_next_to_a_whole_secret_leaves_no_half_escape_or_its_decoded_form(
    secret, spell, off, tail_text
):
    body = _cut_body(spell(secret), off, [secret, OTHER], spell(OTHER))
    assert not body.endswith(tail_text), repr(body[-12:])
    assert body.endswith("." * 10), repr(body[-12:])  # everything of the cut secret is gone


@pytest.mark.parametrize(("secret", "head"), [(ACCENT, "%C3"), (ASTRAL, "%F0%9F")])
def test_a_cut_after_the_multibyte_percent_start_leaves_no_percent_tail_even_alone(secret, head):
    """Without another secret in the text (no decoded view): the tail must go too."""
    body = _cut_body(_percent(secret), len(head), [secret], "")
    assert not body.endswith(head), repr(body[-12:])
    assert "%C3" not in body[-30:] and "%F0" not in body[-30:]


# (b) an astral character written as escapes next to ASCII escapes ----------------------------------------------------------


def test_a_decoded_surrogate_pair_is_one_character():
    assert tools_mod._decoded(_json(ASTRAL)) == ASTRAL
    assert tools_mod._decoded(BS + "ud83d") == chr(0xFFFD)  # a lone half is not a character


def test_a_secret_with_an_astral_character_written_as_escapes_is_scrubbed_whole():
    out = tools_mod.prepare_output("x " + _json(ASTRAL) + " y", {}, 16_384, [ASTRAL])
    assert "<SECRET_REDACTED>" in out
    assert "Lm4" not in out and "ud83d" not in out


@pytest.mark.parametrize("off", range(1, len(_json(ASTRAL))))
def test_a_cut_at_every_offset_of_the_all_escapes_spelling_leaves_no_front(off):
    body = _cut_body(_json(ASTRAL), off, [ASTRAL, OTHER], _json(OTHER))
    assert body.endswith("." * 10), (off, repr(body[-14:]))
