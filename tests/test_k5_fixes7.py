"""Review 5 of PR #42 (independent evidence on c210edd): a cut INSIDE an escape (`\\u005`, `&#9`, `%C3`, half of a
surrogate pair) left the front of a character next to `[truncated]`: no form matched a half-written escape. Every cut
offset inside the spelling is tested, for four shapes and two secrets (one with an astral character).

The first cut is the `raw_cap` one (4096 bytes) so the cases are cheap; it is the same `_cut` and the same boundary rule
as the window cut, and `max_bytes` equals the redactor cap so nothing else shortens the output.

Also pinned here: the layers the scrub does NOT undo. Those tests state what happens today (the text stays), they are
not a claim of protection; the CHANGELOG lists them."""

from __future__ import annotations

import codecs
from urllib.parse import quote

import pytest

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod

CAP = defaults.MAX_REDACT_CHARS
RAW_CAP = 4096
CUT_AT = (
    RAW_CAP - tools_mod.TAIL_WINDOW
)  # `_cut` falls back 256 bytes when the last 256 hold no whitespace
BS = chr(92)
S_ASCII = "Zk3#" + "9qWd"  # fakes, built from parts
S_ASTRAL = (
    chr(0x1F600) + "Vh5" + chr(0xE9) + "Tn2"
)  # starts with an astral character (a surrogate pair)
S_ACCENT = chr(0xE9) + "Tn2Kq8x"  # starts with a two-byte UTF-8 character (%C3%A9)


def _plain(s: str) -> str:
    return s


def _entity(s: str) -> str:
    return "".join(f"&#{ord(c)};" for c in s)


def _entity_hex(s: str) -> str:
    return "".join(f"&#x{ord(c):X};" for c in s)


def _json(s: str) -> str:
    """What `json.dumps` writes for non-ASCII text: a backslash-u escape per UTF-16 unit (a pair for an astral one)."""
    out = []
    for c in s:
        n = ord(c)
        if n < 0x10000:
            out.append(f"{BS}u{n:04x}")
        else:
            n -= 0x10000
            out.append(f"{BS}u{0xD800 + (n >> 10):04x}{BS}u{0xDC00 + (n & 0x3FF):04x}")
    return "".join(out)


def _percent(s: str) -> str:
    return "".join(f"%{b:02X}" for b in s.encode())


SHAPES = {
    "plain": _plain,
    "entity": _entity,
    "entity_hex": _entity_hex,
    "json": _json,
    "percent": _percent,
}


def _out(spelled: str, off: int, secrets: list[str], other_spelled: str = "") -> str:
    """A text cut after `off` characters of `spelled`; `other_spelled` (another handed-out secret) stands whole earlier."""
    head = spelled[:off]
    pad = "." * (CUT_AT - len(head) - len(other_spelled) - 10)
    raw = pad + other_spelled + "." * 10 + head + spelled[off:] + "." * 600
    assert len(raw.encode()) > RAW_CAP
    out = tools_mod.prepare_output(raw, {}, CAP, secrets, raw_cap=RAW_CAP)
    assert out.endswith(tools_mod.TRUNCATED), "the text was not cut: the test does not test the cut"
    return out[: -len(tools_mod.TRUNCATED)]


def _longest_prefix_in(tail: str, spelled: str) -> int:
    return max((n for n in range(3, len(spelled) + 1) if spelled[:n] in tail), default=0)


def _cases():
    for secret_name, secret in (("ascii", S_ASCII), ("astral", S_ASTRAL), ("accent", S_ACCENT)):
        for shape, spell in SHAPES.items():
            n = len(spell(secret))
            for off in range(1, n):
                yield pytest.param(secret, shape, off, id=f"{secret_name}-{shape}-{off}")


@pytest.mark.parametrize(("secret", "shape", "off"), list(_cases()))
def test_a_cut_at_every_offset_inside_the_spelling_leaves_no_prefix_of_it(secret, shape, off):
    other = "Hy8@" + "Rt4nWs6d"
    spell = SHAPES[shape]
    body = _out(spell(secret), off, [secret, other], spell(other))
    tail = body[-64:]
    for s in (secret, other):
        assert _longest_prefix_in(tail, spell(s)) == 0, (shape, off, tail[-30:])
    for form in tools_mod._secret_forms(secret):
        for n in range(3, len(form)):
            assert not tail.endswith(form[:n]), (form, n)


def test_a_cut_inside_a_surrogate_pair_does_not_leave_the_first_half():
    secret = chr(0x1F600) + "Lm4Qa7"
    spelled = _json(secret)
    pair_at = spelled.index(BS + "ud83d")
    for off in range(pair_at, pair_at + 12):  # through both halves
        body = _out(spelled, off, [secret])
        assert BS + "ud83d" not in body[-64:], off
        assert BS + "ud83" not in body[-64:], off


def test_a_cut_inside_a_json_quote_escape_does_not_leave_the_backslash():
    secret = 'Pw9"' + "Ke2" + BS + "Nb"  # a quote and a backslash: json.dumps spells them \" and \\
    spelled = "".join(f"{BS}u{ord(c):04x}" for c in secret)
    for off in range(1, len(spelled)):
        body = _out(spelled, off, [secret])
        assert _longest_prefix_in(body[-64:], spelled) == 0, off
    quoted = tools_mod._secret_forms(secret)
    assert any(BS + '"' in f for f in quoted)  # the form with the quote escape exists


# --- what the scrub does NOT undo: pinned as behaviour, not as protection ------------------------------------------------

HIDDEN = "Vh5$" + "Tn2@Wd8%Re1&Yb4^"  # a fake, built from parts


@pytest.mark.parametrize(
    "name",
    ["hex_of_percent", "rot13", "reversed", "dash_split"],
)
def test_layers_the_scrub_does_not_undo_stay_in_the_output(name):
    spelled = {
        "hex_of_percent": quote(HIDDEN, safe="").encode().hex(),
        "rot13": codecs.encode(HIDDEN, "rot13"),
        "reversed": HIDDEN[::-1],
        "dash_split": "-".join(HIDDEN),
    }[name]
    out = tools_mod.prepare_output("x " + spelled + " y", {}, 16_384, [HIDDEN])
    # Documented in the CHANGELOG: the scrub undoes JSON u-escapes, percent-encoding (twice), HTML entities, NFKC,
    # base64/base32 and hex of the secret itself. It does not undo these; the text is returned as it came.
    assert spelled in out
