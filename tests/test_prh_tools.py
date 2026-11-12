"""PR H, WP2b: the scrub of secrets handed out to a tool, with hidden items (control characters, escape sequences).

A secret handed out to a tool is found in the JOINED reading of the result (where the hidden items that cut it are gone)
and replaced in the SPACED reading (where a space stands where a run of hidden items stood between two word characters),
so a value glued to the text before it by a hidden item stays separated. Every test whose name starts `test_mf_` must
FAIL on main (by an assertion); every other test here passes on main. Every value is made up and built from parts; every
control or invisible character is written as an escape."""

from __future__ import annotations

import hashlib
import re

import pytest

from hadavin_sdk import tools
from hadavin_sdk.guard import hidden
from tests import hidden_oracle as oracle
from tests.k5_support import TOOL

ESC, BEL, NUL = "\x1b", "\x07", "\x00"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
HAND = "Tr0ub4dor" + "-3xyzQ"
ALNUM = "Zq9" + "xw7Ty3pL4m"
SECRETS = {"HAND": HAND, "ALNUM": ALNUM}

# the items of the sweep: the 55 "removed" single characters and four sequences (CSI, OSC with each terminator, DCS)
SEQUENCES = {
    "csi": ESC + "[0m",
    "osc_bel": ESC + "]0;t" + BEL,
    "osc_st": ESC + "]0;t" + ESC + "\\",
    "dcs": ESC + "P x" + ESC + "\\",
}
ITEMS = {f"{ord(c):02x}": c for c in sorted(oracle.REMOVED)} | SEQUENCES
# ignorable characters of category Cf are already found on main; the others are new
CF_IGNORABLE = {"200b": chr(0x200B), "200d": chr(0x200D), "ad": chr(0x00AD), "e0041": chr(0xE0041)}
OTHER_IGNORABLE = {
    "fe0f": chr(0xFE0F),
    "34f": chr(0x034F),
    "115f": chr(0x115F),
    "1160": chr(0x1160),
    "3164": chr(0x3164),
    "ffa0": chr(0xFFA0),
    "e0100": chr(0xE0100),
}


def _pieces_stand(out: str, secret: str, size: int = 5) -> bool:
    return any(secret[i : i + size] in out for i in range(len(secret) - size + 1))


def _both_paths(text: str, secret: str) -> list[str]:
    return [
        tools.prepare_output(text, {}, 4000, [secret]),
        tools.error_reason(ValueError(text), [secret]),
    ]


def _cut_cases(items: dict[str, str], *, only_whole_in_joined: bool) -> list[pytest.ParameterSet]:
    cases = []
    for item_id, item in items.items():
        for name, secret in SECRETS.items():
            for off in range(1, len(secret)):
                text = "x " + secret[:off] + item + secret[off:] + " y"
                if only_whole_in_joined and secret not in oracle.readings(text)[0]:
                    continue  # the item reads as a space or swallows the rest: no secret stands in the text
                cases.append(pytest.param(text, secret, id=f"{item_id}-{name}-{off}"))
    return cases


NAMED_ROWS = [
    pytest.param("auth failed for " + HAND[:9] + ESC + "[0m" + HAND[9:], HAND, id="L6"),
    pytest.param("x " + HAND[:5] + "\x9b0m" + HAND[5:], HAND, id="L12"),
]


@pytest.mark.parametrize(
    ("text", "secret"), NAMED_ROWS + _cut_cases(ITEMS, only_whole_in_joined=True)
)
def test_mf_handed_out_cut(text, secret):
    """T2: a secret handed out to a tool, cut by one hidden item at any offset, is masked on the tool path and on the
    error path (no piece of 5 or more characters stands)."""
    for out in _both_paths(text, secret):
        assert not _pieces_stand(out, secret), out


@pytest.mark.parametrize(
    ("text", "secret"), _cut_cases(OTHER_IGNORABLE, only_whole_in_joined=False)
)
def test_mf_handed_out_cut_ignorable(text, secret):
    """The ignorable characters that are not of category Cf (variation selectors, fillers, the combining grapheme
    joiner) cut a handed-out secret the same way."""
    for out in _both_paths(text, secret):
        assert not _pieces_stand(out, secret), out


@pytest.mark.parametrize(("text", "secret"), _cut_cases(CF_IGNORABLE, only_whole_in_joined=False))
def test_handed_out_cut_cf_kept(text, secret):
    """Category Cf characters (zero-width space, joiner, soft hyphen, tag) are masked on main and stay masked."""
    for out in _both_paths(text, secret):
        assert not _pieces_stand(out, secret), out


def _encoded_cuts() -> list[pytest.ParameterSet]:
    cases = []
    spellings = {
        "pct": "%1b[0m",
        "bs_x": "\\x1b[0m",
        "bs_o": "\\033[0m",
        "bs_u": "\\u001b[0m",
    }
    for sid, spelled in spellings.items():
        for name, secret in SECRETS.items():
            for off in range(1, len(secret)):
                cases.append(
                    pytest.param(
                        secret[:off] + spelled + secret[off:], secret, id=f"{sid}-{name}-{off}"
                    )
                )
    # an item cutting the percent token of one character of the secret (`%7` + item + `8` for `x`)
    for name, secret in SECRETS.items():
        for k, ch in enumerate(secret):
            h = f"{ord(ch):02x}"
            text = secret[:k] + "%" + h[0] + ESC + "[0m" + h[1] + secret[k + 1 :]
            cases.append(pytest.param(text, secret, id=f"token-{name}-{k}"))
    return cases


@pytest.mark.parametrize(
    ("text", "secret"),
    [
        pytest.param(x[:o] + "&#7;" + x[o:], x, id=f"ent-{n}-{o}")
        for n, x in SECRETS.items()
        for o in range(1, len(x))
    ],
)
def test_handed_out_entity_cut_kept(text, secret):
    """A control character spelled as an entity is dropped by the entity decoder: found on main and kept."""
    for out in _both_paths("id " + text + " end", secret):
        assert not _pieces_stand(out, secret), out


@pytest.mark.parametrize(("text", "secret"), _encoded_cuts())
def test_mf_handed_out_encoded_cut(text, secret):
    """The hidden item is spelled as an encoding (percent, backslash text, entity), or sits inside a percent token: the
    decoded reading removes it, so the secret is found and masked."""
    for out in _both_paths("id " + text + " end", secret):
        assert not _pieces_stand(out, secret), out


# ---- boundaries and the backstop of `_scrub` ----------------------------------------------------------------------


D1 = {
    "D1a": "auth failed for " + HAND + " ; INFO user" + ESC + "[0m" + KEY,
    "D1b": "auth failed for " + HAND[:9] + ESC + "[0m" + HAND[9:] + " ; user" + BEL + KEY,
}


def _d1_clean(row: str) -> None:
    for out in _both_paths(D1[row], HAND):
        assert "IOSFODNN7EXAMPLE" not in out, (row, out)
        assert not _pieces_stand(out, HAND), (row, out)


@pytest.mark.parametrize("row", ["D1a"])
def test_scrub_keeps_boundary(row):
    """A handed-out secret that stands whole, with a hidden item that makes the key a word of its own: the key is masked
    (main masks it; a scrub that returned the joined text would glue `user` to the key and leak it)."""
    _d1_clean(row)


@pytest.mark.parametrize("row", ["D1b"])
def test_mf_scrub_cut_and_boundary(row):
    """The secret is cut by a hidden item AND a hidden item makes the key a word of its own: both are masked (main
    leaks the cut secret; a scrub that returned the joined text leaks the key)."""
    _d1_clean(row)


def test_scrub_backstop_withholds(monkeypatch):
    """A scrub that cannot mask the secret in the spaced copy withholds the whole result: a stand-in for the layers
    returns, on its second call, a text that still holds the secret."""
    real = tools._scrub_layers
    calls: list[int] = []

    def later_calls_leak(raw, long_enough, scrub=tools._DEFAULT_SCRUB):
        calls.append(1)
        if (
            len(calls) >= 2
        ):  # every call after the find: the real result with the secret standing in it, as many marks as before
            return real(raw, long_enough, scrub) + " leak " + HAND
        return real(raw, long_enough, scrub)

    monkeypatch.setattr(tools, "_scrub_layers", later_calls_leak)
    text = "auth failed for " + HAND + " end" + ESC + "[0m"
    out = tools._scrub(text, [HAND])
    assert HAND not in out and not _pieces_stand(out, HAND), out
    assert tools.MARKER in out, out


def test_scrub_without_secret_returns_the_text_as_written():
    """No handed-out secret in the text: the result is the text as written, hidden items included, so the choke point
    still sees them."""
    text = "a" + BEL + "b " + ESC + "[0m" + "c"
    assert tools._scrub(text, [HAND]) == text


# ---- batch b4: the consuming reading in the scrub --------------------------------------------------------------------


def _cut_by_sgr0(secret: str, off: int = 9) -> str:
    return secret[:off] + ESC + "(B" + ESC + "[m" + secret[off:]


@pytest.mark.parametrize("tail", ["", " done", " " + "word " * 30])
def test_mf_scrub_consuming_cut(tail):
    """A handed-out secret cut by `ESC ( B` + `ESC [ m` (what `tput sgr0` writes) is masked: the conservative reading keeps
    the letter `B`, the consuming reading does not."""
    text = "result: " + _cut_by_sgr0(HAND) + tail
    for out in _both_paths(text, HAND):
        assert not _pieces_stand(out, HAND), out


@pytest.mark.parametrize(
    "spelling", ["%1B%28B%1B%5Bm", "\\u001b(B\\u001b[m", "&#27;(B&#27;[m", "&#x1b;(B&#x1b;[m"]
)
def test_mf_scrub_consuming_cut_encoded(spelling):
    text = "result: " + HAND[:9] + spelling + HAND[9:] + " done"
    for out in _both_paths(text, HAND):
        assert not _pieces_stand(out, HAND), out


def test_scrub_lost_letter_withholds_the_result():
    """`ESC e` + the rest of a handed-out secret that starts with `e` next to a secret cut by `ESC ( B`: the grammar's reading
    holds the first, the consuming reading the second, and they cannot be merged: nothing is shown, never one of them."""
    first, second = "e" + "Yk3pQ9wRtZ", HAND
    text = "a " + ESC + first + " b " + _cut_by_sgr0(second)
    out = tools._scrub(text, [first, second])
    assert out == tools.MARKER + tools.TRUNCATED, out


def test_scrub_two_secrets_found_by_different_readings():
    """One secret whole for the grammar's reading, another only for the consuming one: neither is shown."""
    other = ALNUM
    text = "k " + other + " m " + _cut_by_sgr0(HAND)
    for out in _both_paths(text, HAND):
        assert not _pieces_stand(out, HAND), out
    out = tools.prepare_output(text, {}, 4000, [HAND, other])
    assert not _pieces_stand(out, HAND) and not _pieces_stand(out, other), out


# ---- batch b5: a joined reading is never handed on (Issues 1 and 2 of round 4) -------------------------------------------


BOUNDARIES = {
    "bel": " ; user" + BEL + KEY,
    "sgr": " ; INFO user" + ESC + "[0m" + KEY,
}


def _clean_of(out: str, *secrets: str) -> None:
    assert "IOSFODNN7EXAMPLE" not in out, out
    for secret in secrets:
        assert not _pieces_stand(out, secret), out


@pytest.mark.parametrize("boundary", sorted(BOUNDARIES))
def test_scrub_character_reading_keeps_boundary(boundary):
    """A handed-out secret that only the CHARACTER reading holds whole (`ESC` + `T` + ...: the grammar's reading reads
    `ESC T` as one escape and eats the `T`), and a hidden item that makes a key a word of its own elsewhere: the secret is
    masked AND the key is masked. A scrub that returned the character reading with no gap glued `user` to the key, which the
    redactor does not mask (main masks it: the bell separates them). With a control sequence as the boundary (`ESC [ 0 m`)
    the character reading would show its body (`[0m`) as text and glue the key to it, so the text is withheld."""
    text = "a " + ESC + HAND + BOUNDARIES[boundary]
    rd = hidden.readings(text)
    assert HAND in rd.characters and HAND not in rd.joined and HAND not in rd.consuming_joined
    for out in _both_paths(text, HAND):
        _clean_of(out, HAND)


@pytest.mark.parametrize("boundary", sorted(BOUNDARIES))
def test_mf_scrub_consuming_reading_keeps_boundary(boundary):
    """The same for a secret that only the CONSUMING reading holds whole (`ESC ( B` + `ESC [ m` cut it: `tput sgr0`)."""
    text = "a " + _cut_by_sgr0(HAND) + BOUNDARIES[boundary]
    rd = hidden.readings(text)
    assert HAND in rd.consuming_joined and HAND not in rd.joined and HAND not in rd.characters
    for out in _both_paths(text, HAND):
        _clean_of(out, HAND)


def test_scrub_character_reading_with_a_sequence_is_withheld():
    """The character reading holds the secret, and the text holds a control sequence it would show as text: nothing is
    shown (never the character reading with `[0m` standing before the key)."""
    text = "a " + ESC + HAND + BOUNDARIES["sgr"]
    assert hidden.leaves_text(text)
    out = tools._scrub(text, [HAND])
    assert out == tools.MARKER + tools.TRUNCATED, (
        f"a character reading with a sequence body was shown: {out!r}"
    )


def test_leaves_text():
    """Only the letter after an ESC is the difference between the character reading and the grammar's reading when no
    sequence has a body: a lone ESC, ESC and a letter or digit. Every longer item leaves text."""
    assert not hidden.leaves_text("plain")
    assert not hidden.leaves_text("a" + ESC + "T" + "b" + BEL + "c" + ESC + "9" + ESC)
    for item in ("[0m", "(~", "]0;t" + BEL, "P x" + ESC + "\\", " " + "@"):
        assert hidden.leaves_text("a" + ESC + item + "b"), repr(item)
    assert hidden.leaves_text("a\x9b31mb")


def test_scrub_result_is_the_spaced_copy_of_the_reading_that_holds_the_secret():
    """The result of a find in the character reading keeps the space the bell made, so the key is a word of its own."""
    text = "a " + ESC + HAND + " ; user" + BEL + KEY
    out = tools._scrub(text, [HAND])
    assert out == "a " + tools.MARKER + " ; user " + KEY, (
        f"result with no gap before the key: {out!r}"
    )


def test_scrub_two_secrets_that_only_the_character_reading_holds():
    """Two handed-out secrets, both whole only in the character reading: the union is in ONE reading, so both are masked
    in its spaced copy and the boundary key stays masked."""
    first, second = ALNUM, HAND
    text = "a " + ESC + first + " ; " + ESC + second + BOUNDARIES["bel"]
    rd = hidden.readings(text)
    assert first in rd.characters and second in rd.characters
    assert first not in rd.joined and second not in rd.joined
    out = tools.prepare_output(text, {}, 4000, [first, second])
    _clean_of(out, first, second)
    out = tools.error_reason(ValueError(text), [first, second])
    _clean_of(out, first, second)


@pytest.mark.parametrize("cut", ["(B", "(B" + ESC + "[m"], ids=["nF-only", "sgr0"])
def test_scrub_two_secrets_one_in_the_character_and_one_in_the_consuming_reading(cut):
    """HAND1 only whole in the character reading (`ESC` + `Z`...), HAND2 only whole in the consuming reading (`ESC ( B`, with
    or without `ESC [ m`, cuts it): no reading holds both and the readings cannot be merged, so nothing is shown (the first
    reading with a find used to be the result and showed the half of HAND2 that its `(B` cut). With `ESC [ m` the character
    reading would also show the body of a sequence; with `ESC ( B` alone it is the union that is not in one reading."""
    first, second = ALNUM, HAND
    text = "a " + ESC + first + " " + second[:9] + ESC + cut + second[9:]
    rd = hidden.readings(text)
    assert first in rd.characters and first not in rd.joined and first not in rd.consuming_joined
    assert second in rd.consuming_joined and second not in rd.characters and second not in rd.joined
    out = tools._scrub(text, [first, second])
    assert out == tools.MARKER + tools.TRUNCATED, (
        f"one reading was shown with a half secret: {out!r}"
    )
    for out in (
        tools.prepare_output(text, {}, 4000, [first, second]),
        tools.error_reason(ValueError(text), [first, second]),
    ):
        _clean_of(out, first, second)


# ---- T12 ----------------------------------------------------------------------------------------------------------


def test_first_decoded_plain():
    """A control character reads as itself, so the scan of a cut tail skips it."""
    for c in sorted(oracle.REMOVED):
        assert tools._first_decoded(c) == c, hex(ord(c))


def test_bells_tail_cost(monkeypatch):
    """A cut tail of 4,000 bells makes no `_decoded_clean` call per bell."""
    calls: list[int] = []
    real = tools._decoded_clean

    def counting(text, window=0):
        calls.append(1)
        return real(text) if not window else real(text, window)

    monkeypatch.setattr(tools, "_decoded_clean", counting)
    forms = sorted({f for f in tools._secret_forms(HAND)})
    text = "x" + BEL * 4000 + tools.TRUNCATED
    tools._strip_fragment(text, forms)
    assert len(calls) <= MAIN_DECODED_CLEAN_CALLS_FOR_BELLS, len(calls)


MAIN_DECODED_CLEAN_CALLS_FOR_BELLS = (
    0  # measured on main (see the fail-before file); a bell is not the start of a form
)


class _NoDigest:
    """A stand-in for the run's context of a tool that fetched nothing: `digest()` is None, so the box hashes the value
    the tool returned."""


def _box(fn):
    spec = tools.ToolSpec(**TOOL)
    return tools.ToolBox({"read_logs": spec}, {"read_logs": fn}, timeout_s=5)


def test_mf_digest_keeps_nul():
    """The recorded digest of a tool result that holds NUL is the hash of what the tool returned (main hashed a text with
    NUL turned into U+FFFD)."""
    value = "a" + NUL + "b"
    out = _box(lambda args, ctx: value).invoke("read_logs", {"name": "x"}, {})
    assert out.sha256 == hashlib.sha256(value.encode()).hexdigest()


def test_mf_l8_through_runner():
    """A key cut by NUL in a tool's return value is masked on the result the box hands to the model (not only through
    `prepare_output`)."""
    value = "id " + KEY[:4] + NUL + KEY[4:]
    out = _box(lambda args, ctx: value).invoke("read_logs", {"name": "x"}, {})
    assert "IOSFODNN7EXAMPLE" not in out.text, out.text
    assert not re.search(r"[\x00]", out.text)
