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
    """The character reading holds the secret, and the text holds a control sequence it would show as text: that reading is
    never the result (`[0m` standing before the key). Batch 8: the KEEPING reading (an ESC that opens no sequence takes nothing
    after it, sequences removed whole) holds the secret too and shows no body, so the text is MASKED in both places instead
    of withheld; the old withheld note was the best answer only while no reading was faithful and whole."""
    text = "a " + ESC + HAND + BOUNDARIES["sgr"]
    assert hidden.leaves_text(text)
    out = tools._scrub(text, [HAND])
    assert out == "a " + tools.MARKER + " ; INFO user " + tools.MARKER, (
        f"the secret stood, or a sequence body was shown: {out!r}"
    )
    assert HAND not in out and "[0m" not in out


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
    # batch 7: the scrub masks the secret-kind values the redactor finds in the text as written too (`_found_values`), so the key
    # that follows the bell is masked here (as the marker) and still a word of its own
    assert out == "a " + tools.MARKER + " ; user " + tools.MARKER, (
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


# ---- batch b6: the readings are compared per copy, never as sets (round 5: H1, H2, H3, d3, d11) --------------------------

SGR0 = ESC + "(B" + ESC + "[m"
MARK = tools.MARKER


def _h1_rows() -> dict[str, str]:
    cut = HAND[:9] + SGR0 + HAND[9:]
    return {
        "single": "x " + HAND + " y",
        "two_plain": "x " + HAND + " y " + HAND,
        "esc_copy_after_plain": "x " + HAND + " y " + ESC + HAND,
        "esc_copy_before_plain": "x " + ESC + HAND + " y " + HAND,
        "esc_copy_around_plain": "x " + ESC + HAND + " y " + HAND + " z " + ESC + HAND,
        "cut_copy_after_plain": "x " + HAND + " y " + cut,
        "cut_copy_before_plain": "x " + cut + " y " + HAND,
        "cut_copy_two_plain": "x " + HAND + " y " + cut + " z " + HAND,
        "esc_copy_and_cut_copy": "x " + ESC + HAND + " y " + cut,
        "cut_copy_and_esc_copy": "x " + cut + " y " + ESC + HAND,
    }


@pytest.mark.parametrize("row", sorted(_h1_rows()))
def test_b6_h1_every_copy_is_masked_or_nothing_is_shown(row):
    """H1: a handed-out secret found once by one reading and twice by another is not the same find. Whatever the mix of
    plain copies, copies an ESC cut and copies `tput sgr0` cut, no stretch of 5 characters of the secret stands on either
    path (the set of secrets found was equal, so the reading that held ONE copy used to be the result)."""
    text = _h1_rows()[row]
    for out in _both_paths(text, HAND):
        assert not _pieces_stand(out, HAND), f"{row}: {out!r}"
        assert "IOSFODNN" not in out


def test_b6_h1_the_readings_that_can_hold_all_copies_still_show_the_text():
    """Availability, pinned: where one reading holds every copy the text is shown with every copy masked, not withheld."""
    assert tools._scrub(_h1_rows()["esc_copy_after_plain"], [HAND]) == "x " + MARK + " y " + MARK
    assert tools._scrub(_h1_rows()["cut_copy_after_plain"], [HAND]) == "x " + MARK + " y " + MARK
    assert tools._scrub(_h1_rows()["single"], [HAND]) == "x " + MARK + " y"


def test_b6_h1_equal_counts_that_are_different_copies_show_nothing():
    """The consuming reading holds the copy `ESC ( B` cut, the character reading the copy an ESC cut: one each, so the
    counts agree, but neither reading holds both. The result is the consuming reading's spaced copy, whose first copy has
    lost its first letter: the piece check (`piece_min`) refuses it."""
    text = "a " + ESC + HAND + " b " + HAND[:9] + SGR0 + HAND[9:]
    assert tools._scrub(text, [HAND]) == MARK + tools.TRUNCATED
    for out in _both_paths(text, HAND):
        assert not _pieces_stand(out, HAND), out


@pytest.mark.parametrize("n", [3, 6, 9, 11, 13])
def test_b6_h2_a_cut_fragment_after_an_esc_is_never_returned_as_written(n):
    """H2: `ESC` + the front of a secret + the cut marker. The grammar's reading shows the front without its first letter
    (a form's prefix test does not match it), the character reading cuts it: the text is never returned as written."""
    text = "log " + ESC + HAND[:n] + tools.TRUNCATED
    for out in _both_paths(text, HAND):
        assert not _pieces_stand(out, HAND, 4), f"{n}: {out!r}"
        assert HAND[1:5] not in out, out
    assert tools._scrub(text, [HAND]) != text


def test_b6_h2_the_fragment_row_keeps_its_text():
    assert (
        tools._scrub("log " + ESC + HAND[:11] + tools.TRUNCATED, [HAND]) == "log " + tools.TRUNCATED
    )


def test_b6_scrub_without_a_find_or_a_changed_reading_is_still_the_text_as_written():
    text = "ok " + ESC + "[0m" + "fine" + ESC + "[0m"
    assert tools._scrub(text, [HAND]) == text


def test_b6_piece_check_unit():
    forms = sorted(tools._secret_forms(HAND))
    assert tools._has_piece("x " + HAND[3:9] + " y", forms, 6)
    assert tools._has_piece("x " + HAND[3:9], forms, 6)
    assert not tools._has_piece("x " + HAND[3:8] + " y", forms, 6)
    assert not tools._has_piece("nothing here", forms, 6)
    # batch 7 (Issue 7): the check is exact, not sampled: a stretch of `piece` characters at EVERY offset of a long form is seen
    for n in (136, 300, 1000):
        # every 6-window holds a digit, so none of them is "a word of letters only" (the ordinary-word rule has its own test)
        big = "".join(chr(0x4E00 + i) if i % 4 else "7" for i in range(n))
        for start in range(n - 6 + 1):
            assert tools._has_piece(big[start : start + 6], [big], 6), (n, start)
        assert not tools._has_piece(big[0:5] + "x" + big[6:11], [big], 6)


def test_b6_h3_a_value_glued_by_a_bell_stays_a_word_of_its_own_in_the_character_reading():
    """H3: a key cut by `ESC` that takes its 4th letter (`AKI` + ESC + `AIOSF...`) is whole only in the character reading,
    which wins; its output must be the SPACED copy, so `user` + BEL + an address already in the map stays two words. The
    round-5 probe used `AKIA` + ESC + `A...` (whole in the grammar's reading), which does not reach this path. On 3db0d34d
    this input leaves the key readable (`id AKI IOSFODNN7EXAMPLE`, the address is in the map) and, with a host name
    after the bell, shows `userhost.example.org` glued."""
    from hadavin_sdk.guard import runmap

    mapping: dict[str, str] = {}
    runmap.redact_text("seen ip 10.20.30.44", mapping)
    text = "id " + KEY[:3] + ESC + KEY[3:] + " user" + BEL + "10.20.30.44"
    out = runmap.redact_untrusted(text, mapping)
    assert out == "id <APIKEY_1> user <IPV4_1>", out
    out = runmap.redact_untrusted(
        "id " + KEY[:3] + ESC + KEY[3:] + " user" + BEL + "host.example.org", {}
    )
    assert "IOSFODNN" not in out and "userhost" not in out, out


def test_b6_d3_a_key_cut_by_sgr0_is_masked_in_a_direct_redact_call():
    """d3: `redact()` read the grammar's reading only (`ESC ( B` leaves the `B`), so the key tail stood. The consuming
    reading is the second reading now; the result is the one that masks more values."""
    from hadavin_sdk.guard.redact import redact

    out = redact("id " + KEY[:4] + SGR0 + KEY[4:]).text
    assert out == "id <APIKEY_1>", out
    assert "IOSFODNN" not in out and ESC not in out


def test_b6_d3_a_plain_key_and_a_cut_key_are_both_masked():
    from hadavin_sdk.guard.redact import redact

    key2 = "AKIA" + "ZZZZODNN7EXAMPL2"
    out = redact("a " + key2 + " b " + KEY[:4] + SGR0 + KEY[4:]).text
    assert "IOSFODNN" not in out and "ZZZZODNN" not in out, out


def test_b6_d11_a_known_value_after_an_esc_is_withheld_in_a_direct_redact_call():
    """d11: a value the map already holds, directly after an ESC (the grammar's reading takes its first letter): the tail
    stood on main and on the head. Now the call returns the withheld note."""
    from hadavin_sdk.guard.redact import WITHHELD_NOTE, redact

    out = redact(ESC + HAND + " x", mapping={"<SECRET_1>": HAND}).text
    assert out == WITHHELD_NOTE, out
    out = redact("id " + HAND[:9] + ESC + "[0m" + HAND[9:], mapping={"<SECRET_1>": HAND}).text
    assert HAND[9:] not in out and out != WITHHELD_NOTE, out


def test_b6_the_readings_are_compared_per_copy_without_the_piece_check():
    """The piece check (`piece_min`) is a second guard; with it off (a piece the size of the whole form) the choice between
    the readings alone shows every copy masked: the reading that holds both copies is the result, not the first one that
    holds the same set."""
    off = tools.ScrubSettings(piece_min=32)
    rows = _h1_rows()
    for name in ("esc_copy_after_plain", "cut_copy_after_plain", "esc_copy_around_plain"):
        copies = rows[name].count(HAND) + (
            rows[name].count(ESC + HAND) if name.startswith("esc") else 0
        )
        out = tools._scrub(rows[name], [HAND], off)
        assert out.count(MARK) >= 2 and not _pieces_stand(out, HAND), f"{name}: {out!r} ({copies})"
    assert tools._scrub(rows["esc_copy_after_plain"], [HAND], off) == "x " + MARK + " y " + MARK


def test_b6_the_backstop_withholds_without_the_piece_check(monkeypatch):
    """The whole-form backstop reads a hex secret in any case; the piece check does not. A scrub that leaves the secret
    standing in capitals is refused by the backstop alone (piece check off)."""
    hexkey = "5a6b7c8d" + "9e0f1a2b" + "3c4d5e6f" + "7a8b9c0d"
    real = tools._scrub_layers
    calls: list[int] = []

    def later_calls_leak(raw, long_enough, scrub=tools._DEFAULT_SCRUB):
        calls.append(1)
        out = real(raw, long_enough, scrub)
        return out + " leak " + hexkey.upper() if len(calls) >= 2 else out

    monkeypatch.setattr(tools, "_scrub_layers", later_calls_leak)
    # the piece check is off (a 32-character secret is its own stretch at the widest setting, so it is switched off here)
    monkeypatch.setattr(tools, "_has_piece", lambda *_a, **_k: False)
    out = tools._scrub(
        "auth failed for " + hexkey + " end" + ESC + "[0m",
        [hexkey],
        tools.ScrubSettings(piece_min=32),
    )
    assert hexkey.upper() not in out and tools.MARKER in out, out


def test_b6_the_union_is_the_most_any_reading_holds_without_the_piece_check():
    """Two secrets, one whole only in the character reading and one only in the consuming reading: no reading holds both,
    so nothing is shown, with the piece check off too (the first reading with a find used to be the result)."""
    off = tools.ScrubSettings(piece_min=32)
    first, second = ALNUM, HAND
    text = "a " + ESC + first + " " + second[:9] + ESC + "(B" + second[9:]
    assert tools._scrub(text, [first, second], off) == MARK + tools.TRUNCATED


def _b6_text(g) -> str:
    """A text of 2 to 6 parts: filler, a plain copy of HAND, a copy an ESC took the first letter of, a copy `tput sgr0` cut,
    a copy a colour code cut, a bell, a cut fragment at the end (`Gen` of `test_prh_spans`: the same texts every run)."""

    def cut() -> str:
        return HAND[:9] + SGR0 + HAND[9:]

    words = ["x", "log", "id", "user", "done"]
    pieces = [
        lambda: " " + words[g.below(len(words))] + " ",
        lambda: HAND,
        lambda: ESC + HAND,
        cut,
        lambda: HAND[:5] + ESC + "[0m" + HAND[5:],
        lambda: BEL,
        lambda: ESC + "[0m",
    ]
    text = "".join(pieces[g.below(len(pieces))]() for _ in range(g.between(2, 6)))
    return text + (ESC + HAND[: g.between(2, 13)] + tools.TRUNCATED if g.below(5) == 0 else "")


def test_b6_seeded_mixes_of_copies_never_leave_a_piece_of_the_secret():
    """400 seeded texts mixing plain, ESC-cut, sgr0-cut and colour-cut copies of one handed-out secret (and a cut fragment
    at the end): on the tool and the error path no stretch of 5 characters of the secret stands in the result. On 3db0d34d
    many of them fail (the result was the reading that held the same SET of secrets, not every copy)."""
    from tests.test_prh_spans import Gen

    bad = []
    for seed in range(400):
        text = _b6_text(Gen(seed))
        for out in _both_paths(text, HAND):
            if _pieces_stand(out, HAND):
                bad.append((seed, out))
    assert not bad, f"{len(bad)} of 400 texts left a piece: {bad[:2]}"
