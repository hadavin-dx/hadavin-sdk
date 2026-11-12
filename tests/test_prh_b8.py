"""PR H batch 8 (round 7): several cuts in one value, direct redact, spaced-out values, the keeping reading.

Class (Issue 4 / 3): a value cut by a mix of an escape, a string opener, a terminator and an ignorable character that no
single reading handles. Fix point: `hidden.strip_keeping` (a lone ESC eats nothing after it), the cut readings searched with
ignorable characters removed, and `compare_readings` for the direct find. Made-up values only, built from parts."""

import importlib

import pytest

from hadavin_sdk import tools
from hadavin_sdk.guard import hidden, runmap
from hadavin_sdk.guard.redact import spaced_unknown
from tests.seeded import rng

R = importlib.import_module("hadavin_sdk.guard.redact")


ESC = "\x1b"
BEL = "\x07"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
KEY2 = "AKIA" + "ZZZZODNN7EXAMPL2"
MAIL = "bob.smith" + "@" + "example.com"
PW = "hunter" + "2secretXYZ"
HAND = "Tr0ub4dor" + "-3xyzQ"
CUTS = [
    ESC + "[0m",
    ESC + "(B",
    ESC + "M",
    ESC,
    "\u200b",
    "\ufe0f",
    "\u034f",
    "\x08",
    "\x00",
    "\x9b0m",
    "%1b[0m",
]


def stands(out: str, secret: str, size: int = 8) -> bool:
    return any(secret[i : i + size] in out for i in range(len(secret) - size + 1))


def shown(text: str, path: str) -> str:
    if path == "run":
        try:
            o = runmap.redact_untrusted(text, {})
        except runmap.InputTooLarge:  # a refusal shows nothing: the safe answer
            return ""
        return str(o[0] if isinstance(o, tuple) else o)
    return tools.prepare_output(text, {}, 4000, [HAND])


ROWS = {
    "L1": "id " + KEY[:4] + ESC + "[0m" + KEY[4:],
    "L2": "id " + KEY[:4] + "\ufe0f" + KEY[4:],
    "L3": "id " + KEY[:4] + "\x08" + KEY[4:],
    "L8": "id " + KEY[:4] + "\x00" + KEY[4:],
    "L9": "id " + KEY[:4] + ESC + "(B" + ESC + "[m" + KEY[4:],
    "L10": "id " + KEY[:4] + "\u3164" + KEY[4:],
    "L11": "id " + KEY[:4] + "%1b[0m" + KEY[4:],
    "G1": "user" + BEL + KEY,
    "G2": "user" + ESC + "[0m" + KEY,
    "G3": "a " + KEY[:4] + ESC + "[0m" + KEY[4:] + " b user" + BEL + KEY2,
}


@pytest.mark.parametrize("path", ["run", "tool"])
@pytest.mark.parametrize("name", sorted(ROWS))
def test_b8_i4_runner_rows_leave_no_readable_stretch(name, path):
    """Issue 4 (mutants 102, 103): the runner's nine readable-stretch rows (several cuts in one value)."""
    assert not stands(shown(ROWS[name], path), KEY, 8), (name, path)
    assert not stands(shown(ROWS[name], path), KEY2, 8), (name, path)


@pytest.mark.parametrize("path", ["run", "tool"])
def test_b8_i4_seeded_multi_cut_property(path):
    """Issue 4 (mutants 102-104, 113): 400 seeded values, each cut at 1 to 3 places by a mix of the cut grammar; no 8-stretch stands."""
    rnd = rng(8008)
    for n in range(400):
        pos = sorted(rnd.sample(range(1, len(KEY)), rnd.randint(1, 3)))
        out, last = "", 0
        for p in pos:
            out += KEY[last:p] + rnd.choice(CUTS)
            last = p
        text = (
            rnd.choice(["id ", "key: ", "x "]) + out + KEY[last:] + rnd.choice([" end", "\n", ""])
        )
        assert not stands(shown(text, path), KEY, 8), (n, ascii(text))


DIRECT = {
    "c1": KEY + " AK" + ESC + "I" + KEY[2:],
    "c2": ESC + KEY,
    "c3": "\x9b" + KEY,
    "mail_cut": "to " + MAIL[:5] + ESC + "I" + MAIL[5:] + " x",
    "mail_esc": "mail " + ESC + MAIL,
    "ip": "from " + ESC + "10.0.0.5 and 10.0.0.5",
}


@pytest.mark.parametrize("name", sorted(DIRECT))
def test_b8_i3_direct_redact_masks_or_withholds_every_copy(name):
    """Issue 3 (mutants 105, 106): `redact()` itself (not only the run path) leaves no readable piece of the value."""
    out = R.redact(DIRECT[name]).text
    for secret in (KEY, MAIL, "10.0.0.5"):
        assert not stands(out, secret, min(len(secret), 8)) or secret not in DIRECT[name].replace(
            ESC, ""
        ), (
            name,
            out,
        )


def test_b8_i4_a_lone_escape_eats_nothing_after_it():
    """The keeping reading (mutant 102): a lone ESC removes only itself, so the capital letter after it stays (`strip`
    eats it as a one-letter function); a full sequence with a body is removed whole."""
    assert hidden.strip_keeping("a" + ESC + "Kb")[0] == "aKb"
    assert hidden.strip("a" + ESC + "Kb")[0] == "ab"
    assert hidden.strip_keeping("a" + ESC + "[0mb")[0] == "ab"


# ---- Issue 1: spaced-out values -------------------------------------------------------------------------------------
def test_b8_i1_known_value_written_with_spaces_is_masked():
    """Issue 1 (mutants 107, 108): a known handed-out value of 12 or more characters typed with spaces is masked on the tool path."""
    spaced = " ".join(HAND + "abc")
    out = tools.prepare_output("note: " + spaced + " end", {}, 4000, [HAND + "abc"])
    assert not stands(out.replace(" ", ""), HAND + "abc", 8), out


def test_b8_i1_short_known_value_with_spaces_is_not_touched():
    """Control: below the 12-character floor the spaced-out rule does not fire (no over-masking of ordinary words)."""
    text = "a b c d e f g h"
    assert tools.prepare_output(text, {}, 4000, ["abcdefgh"]) == text


def test_b8_i1_ordinary_spaced_text_is_unchanged():
    """Control (the floor, mutant 109): a long ordinary sentence of single-letter tokens, no secret shape, is returned as written."""
    text = (
        "note: "
        + "hello world this is plain text again and again please and then some more words"
        + " end"
        + " a b c d e f g h i j k l m n o p q"  # single-character words: the spaced-run reader is reached
    )
    assert R.redact(text).text == text
    assert tools.prepare_output(text, {}, 4000, []) == text


def test_b8_i1_unknown_secret_shape_typed_with_spaces_is_masked_on_the_run_path():
    """Issue 1 (mutants 110, 111): a key-shaped value of 20 characters typed with a space between each, with no known value
    behind it, is masked (a run of 10 or more spaced tokens is read as one word for the check only)."""
    out = shown("key: " + " ".join(KEY) + " end", "run")
    assert not stands(out.replace(" ", ""), KEY, 8), out


def test_b8_i1_the_switch_is_a_named_constant():
    from hadavin_sdk import defaults

    assert defaults.SPACED_VALUE_MIN_CHARS == 12 and defaults.SPACED_RUN_MIN_TOKENS == 10
    assert defaults.READ_SPACED_OUT_UNKNOWN is True


def test_b8_i4_the_mixed_reading_keeps_a_lone_escape_byte_and_drops_a_charset_sequence():
    """Issue 4 (mutant 112): `AK ESC I AIOSF ESC ( B ODNN7EXAMPLE`: only this reading gives the key back."""
    t = "AK" + ESC + "IAIOSF" + ESC + "(B" + "ODNN7EXAMPLE"
    assert hidden.strip_mixed(t)[0] == KEY
    assert KEY not in (hidden.strip(t)[0], hidden.strip_keeping(t)[0], hidden.strip_consuming(t)[0])


def test_b8_i4_the_run_path_reads_the_mixed_cut_of_a_key():
    """Issue 4 (mutant 113): a key cut by a lone escape plus its byte AND a charset sequence is masked on the run path."""
    t = "log: AK" + ESC + "IAIOSF" + ESC + "(B" + "ODNN7EXAMPLE end"
    out = runmap.redact_untrusted(t, {})
    assert out == "log: <APIKEY_1> end", (
        "the mixed reading was not read on the run path (mutant 113): " + repr(out)
    )


def test_b8_i1_a_repeated_letter_run_is_not_read_as_a_spaced_out_secret():
    """Issue 1 (mutant 115): `x x x x ...` collapses to one letter repeated, which the patterns call high entropy by length;
    full-suite tests `test_k5_truncation_follows_redaction` and `test_m3_bytes_sent...` caught it after the first gate run."""
    assert spaced_unknown("x " * 5000) == []
    assert tools.prepare_output("x " * 400, {}, 10000) == "x " * 400


# ---- Issue 4: the evidence runner's own generator (seed 777), all 3096 texts -------------------------------------------
_RUNNER_HAND = "Zq4nWs" + "-8kLpv3Hd"
_RUNNER_PW = "password=" + "hunter" + "2secretXYZ"
_RUNNER_HIDDEN = {
    "esc_csi": ESC + "[0m", "esc_csi2": ESC + "[1;31m", "esc_nF": ESC + "(B", "esc_osc": ESC + "]0;t\x07",
    "esc_osc_st": ESC + "]0;t" + ESC + "\\", "esc_alone": ESC, "bel": "\x07", "bs": "\x08", "del": "\x7f", "nul": "\x00",
    "c1_csi": "\x9b0m", "c1_st": "\x9c", "zwsp": "\u200b", "zwj": "\u200d", "bidi_rlo": "\u202e", "bidi_lri": "\u2066",
    "wj": "\u2060", "bom": "\ufeff", "shy": "\xad", "vs16": "\ufe0f", "tag": "\U000e0041", "enc_pct": "%1b[0m",
    "enc_pct2": "%1B[31m", "enc_html": "&#27;[0m", "enc_hex": "&#x1b;[0m", "enc_u": "\\u001b[0m", "enc_x": "\\x1b[0m",
    "enc_json": "\\u001b[0m",
}  # fmt: skip


def _runner_cases(rnd=None):
    for s in (_RUNNER_HAND, KEY, _RUNNER_PW):
        for h in _RUNNER_HIDDEN.values():
            for i in range(1, len(s)):
                yield s, "log: " + s[:i] + h + s[i:] + " end"
    r = rnd or rng(777)
    names = list(_RUNNER_HIDDEN)
    for _ in range(1500):
        s = r.choice([_RUNNER_HAND, KEY, _RUNNER_PW])
        cuts = sorted(r.sample(range(1, len(s)), r.randrange(1, 4)))
        out, p = "", 0
        for c in cuts:
            out += s[p:c] + _RUNNER_HIDDEN[r.choice(names)]
            p = c
        yield s, "x " + out + s[p:] + " y"


def test_b8_i3_direct_redact_keeping_row():
    """Issue 3 (mutant 105): `AK` + ESC `I` + `AIOSF` + a colour code + the tail: only the keeping reading gives the key
    back (the character reading would show `[0m` inside it), so direct `redact()` needs it."""
    out = R.redact("x AK" + ESC + "IAIOSF" + ESC + "[0m" + "ODNN7EXAMPLE y").text
    assert out == "x <APIKEY_1> y", out


def test_b8_i3_a_soft_conflict_is_not_a_refusal():
    """Issue 3 (mutant 106): ordinary text with a cursor-up sequence (ESC `M`) beside a plain key: the key is masked and the
    text is not withheld for the letter the keeping reading kept."""
    out = R.redact("line one" + ESC + "Mline two " + KEY).text
    assert out == "line one line two <APIKEY_1>", out
    out = R.redact("x" + ESC + "M" + KEY + " y" + ESC + "M" + MAIL).text
    assert out == "x <APIKEY_1> <EMAIL_1>", out


def test_b8_i1_known_value_with_spaces_is_masked_on_the_direct_call():
    """Issue 1 (mutant 107): `redact(text, mapping)` with the value known: a spaced-out copy is masked."""
    out = R.redact("key: " + " ".join(KEY) + " end", mapping={"<APIKEY_1>": KEY}).text
    assert out == "key: <APIKEY_1> end", out


@pytest.mark.parametrize("path", ["run", "tool"])
def test_b8_i4_a_key_cut_by_a_kept_letter_and_a_joiner(path):
    """Issue 4 (mutant 104): `AK` + ESC `I` (the letter stays) + `AIOSF` + a zero-width joiner + the tail: the cut reading is
    only the key once its ignorable character is out."""
    text = "id AK" + ESC + "IAIOSF" + "\u200d" + "ODNN7EXAMPLE end"
    assert not stands(shown(text, path), KEY, 8), (path, shown(text, path))


def test_b8_i4_one_key_cut_twice_is_one_placeholder():
    """Issue 4 (mutant 104): a cut reading is searched with its ignorable characters out, so ONE key cut by a combining
    grapheme joiner and a lone ESC `M` is ONE placeholder; read with the joiner in, it was masked as a second value."""
    text = "x AK\u034fIAI" + ESC + "MOSFODNN7EXAMPLE y"
    assert tools.prepare_output(text, {}, 4000, []) == "x <APIKEY_1> y"


def test_b8_i4_the_runner_exact_generator_leaves_no_readable_stretch():
    """Issue 4 (mutants 102, 103, 114): the evidence runner's OWN 3096 texts (`random.Random(777)`, as in its script; the one
    corpus of this file, batch 9 group 10): 9 left an 8-character stretch on the old code. None may now (withheld is allowed)."""
    leaks = []
    n = 0
    for s, t in _runner_cases(rng(777)):
        n += 1
        if stands(tools.prepare_output(t, {}, 4000, [_RUNNER_HAND]), s.replace("password=", ""), 8):
            leaks.append(ascii(t))
    assert n == 3096
    assert not leaks, leaks[:3]


def test_b8_i4_a_handed_out_value_cut_by_a_charset_sequence_and_a_kept_letter():
    """Issue 4 (mutant 114): `Zq4nWs-8` + ESC `(B` + `kLpv3` + ESC `H` + `d`: only the mixed reading holds the whole value;
    the tool scrub withholds the text (nothing of the value stands)."""
    t = (
        "x "
        + _RUNNER_HAND[:8]
        + ESC
        + "(B"
        + _RUNNER_HAND[8:13]
        + ESC
        + "H"
        + _RUNNER_HAND[13:]
        + " y"
    )
    out = tools.prepare_output(t, {}, 4000, [_RUNNER_HAND])
    assert not stands(out, _RUNNER_HAND, 6), out


# ---- Issue 5: no decoded reading holds an ignorable character (the argument behind the old "equivalent" mutant) ----------
def _spell_hidden(c: str, how: int) -> str:
    b = c.encode("utf-8")
    return [
        "".join("%" + format(x, "02x") for x in b),
        "".join("%" + format(x, "02X") for x in b),
        f"&#x{ord(c):x};",
        f"&#{ord(c)};",
        f"\\u{ord(c):04x}",
    ][how % 5]


def test_b8_i5_no_decoded_reading_holds_an_ignorable_character():
    """Issue 5: `runmap.decodes(t, characters=True, keeping=True)` and `tools._decoded_readings(t)` never return a view that
    holds an ignorable character (every one is non-ASCII and `nfkc` removes it each round). 3000 seeded texts that spell an
    ignorable character as a percent token, an entity or a JSON escape, beside the key (the committed script for the old
    mutant 90 claim)."""
    rnd = rng(5005)
    hid = [
        c
        for c in "\u200b\u200c\u200d\u2060\ufeff\u034f\ufe0f\u180e\u00ad"
        if hidden.IGNORABLE_RE.search(c)
    ]
    assert len(hid) >= 6
    for n in range(3000):
        parts = []
        for ch in KEY[: rnd.randrange(2, len(KEY))]:
            parts.append(ch)
            if rnd.randrange(3) == 0:
                parts.append(_spell_hidden(rnd.choice(hid), rnd.randrange(5)))
        text = "x " + "".join(parts) + " y"
        for view in (
            *runmap.decodes(text, characters=True, keeping=True),
            *tools._decoded_readings(text),
        ):
            assert not hidden.IGNORABLE_RE.search(view), (n, ascii(text), ascii(view))


def test_b8_i6_the_withheld_share_is_bounded():
    """Issue 6: over-withholding is measured on both paths (the 3000 seeded texts of `tests/test_prh_b7.py`): the tool path
    withholds 155 (5.2 percent) and direct `redact()` 14 (0.5 percent), measured at the head of batch 9 (155 and 22 at batch 8;
    on the same seeded texts the old bound of 200 passed with 143 too). The bounds ARE the measured values: one more withheld
    text fails them, so a change that withholds more must say so here."""
    from tests import test_prh_b7 as b7

    tool = direct = n = 0
    for t in b7._fuzz_texts(3000):
        n += 1
        o = tools.prepare_output(t, {}, 4000, [b7.HAND])
        tool += "withheld" in o or o.startswith(tools.MARKER + tools.TRUNCATED)
        direct += R.redact(t).text == R.WITHHELD_NOTE
    assert n == 3000
    assert tool <= 155, tool
    assert direct <= 14, direct
