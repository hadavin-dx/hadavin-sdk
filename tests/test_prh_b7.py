"""PR H batch 7: the rows and properties of the round-6 review (Issues 1 to 9, 12). Every credential-shaped value is built from
parts; the only literal is the allowed example key. Each test names the issue it guards and the mutant (tests/prh_mutants.py)
that reverts the guard."""

import importlib
import random

import pytest

from hadavin_sdk import tools
from hadavin_sdk.guard import hidden, runmap
from hadavin_sdk.guard.redact import WITHHELD_NOTE, redact

# looked up by name so that the file can be run on the tree before batch 7 (the new names are missing there: those tests fail)
compare_readings = getattr(
    importlib.import_module("hadavin_sdk.guard.redact"), "compare_readings", None
)

ESC = "\x1b"
HAND = "Qx7mLp" + "-9vRtzKw2"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
TRUNCATED = tools.TRUNCATED
MARKER = tools.MARKER


def stands(out: str, secret: str, size: int = 8) -> bool:
    return any(secret[i : i + size] in out for i in range(len(secret) - size + 1))


def both(text: str, secret: str) -> list[str]:
    return [
        tools.prepare_output(text, {}, 4000, [secret]),
        tools.error_reason(ValueError(text), [secret]),
    ]


# ---- Issue 2: the limit of the redactor is a limit, not an error on a short text --------------------------------------
SEVEN = [
    "Qx7m\x1bLp-9vRtzKw2 AKIAIOSFODNN%1b7EXAMPLE {H} {K} AK\\u001bIAIOSFODNN7EXAMPLE {K} {H} \x07",
    "log line AKIAIOSFODNN\x1b7EXAMPLE AKIAI\\u001bOSFODNN7EXAMPLE",
    "{K} AKIAIOSFO\x1b[31mDNN7EXAMPLE AKIAIOSFODNN%1b7EXAMPLE AKIAIOSFODNN\x077EXAMPLE \x1b[0m {H} done",
    "done {H} AKIAI\x1b[31mOSFODNN7EXAMPLE \u200b AKIAIOSFODNN\\u001b7EXAMPLE {H}",
    "\x1b AKIA&#27;IOSFODNN7EXAMPLE user &#27; Company AKIAIOSFODNN\\u001b7EXAMPLE",
    "AKIAI\x1bOSFODNN7EXAMPLE {K} Company \x07 log line error AKIAIOSFODN\x1b(BN7EXAMPLE AKIAIOSFODNN%1b7EXAMPLE",
    "AKIAIOSFODNN7\x1b[0mEXAMPLE AKIAIOSFODNN%1b7EXAMPLE %1b Qx7\x07mLp-9vRtzKw2",
]


@pytest.mark.parametrize("raw", SEVEN, ids=[f"seven_{i}" for i in range(len(SEVEN))])
def test_b7_i2_small_texts_that_raised_input_too_large_give_a_result(raw):
    """Issue 2 (mutants 82, 83): the 7 fuzz inputs that raised `InputTooLarge` on c802cc0f. A text under the size cap never
    raises; no 8-character stretch of the handed-out value or of the key stands in the result."""
    text = raw.replace("{H}", HAND).replace("{K}", KEY)
    for out in both(text, HAND):
        assert isinstance(out, str)
        assert not stands(out, HAND) and not stands(out, KEY), repr(out)


def test_b7_i2_a_limit_is_its_own_class_and_is_still_an_input_too_large():
    """Issue 2 (mutant 83): the five limit sites raise `RedactionLimit`, a subclass, so the callers that refuse an
    oversized text still catch it, and the scrub can tell a limit from a size."""
    assert issubclass(getattr(runmap, "RedactionLimit", object), runmap.InputTooLarge)
    assert getattr(runmap, "RedactionLimit", runmap.InputTooLarge) is not runmap.InputTooLarge


def test_b7_i2_tools_catch_a_limit_and_withhold():
    text = SEVEN[0].replace("{H}", HAND).replace("{K}", KEY)
    out = tools.prepare_output(text, {}, 4000, [HAND])
    assert out  # not an exception; whatever is shown holds no readable window (checked above)


# ---- Issue 1: an encoded escape followed by an encoded first letter ---------------------------------------------------
def _spell(c: str, how: str) -> str:
    return {
        "percent": "%" + format(ord(c), "02x"),
        "percent_up": "%" + format(ord(c), "02X"),
        "entity": f"&#{ord(c)};",
        "entity_hex": f"&#x{ord(c):x};",
        "json": f"\\u{ord(c):04x}",
    }[how]


@pytest.mark.parametrize("how", ["percent", "percent_up", "entity", "entity_hex", "json"])
@pytest.mark.parametrize("first", ["T", "Z", "a", "q", "7", "A"])
def test_b7_i1_encoded_escape_and_encoded_first_letter(how, first):
    """Issue 1 (mutant 84): class = a decoded reading in which an escape takes the letter after it (the grammar's Fe rule
    reads `ESC` + capital as one short sequence). The scrub of handed-out values also reads the character reading of the
    decoded text. Property: over every spelling and every class of first letter, no 6-character stretch stands."""
    secret = first + "r0ub4dor-3xyzQ"
    text = "x " + _spell(ESC, how) + _spell(first, how) + "r0ub4dor" + _spell("-", how) + "3xyzQ y"
    for out in both(text, secret):
        assert not stands(out, secret, 6), (how, first, repr(out))


# ---- Issue 3: a word-like secret in coloured text is masked, not the whole result withheld ------------------------------
@pytest.mark.parametrize("secret", ["ProdCompany" + "2024!", "my" + "SECRET" + "phrase9"])
def test_b7_i3_word_like_secret_in_a_coloured_log_is_masked_not_withheld(secret):
    """Issue 3 (mutant 85): the piece check looks only at what the scrub itself did not mask, and the scrub's marker is cut
    out first, so a secret that holds `SECRET` or a word of the log does not withhold the log."""
    text = ESC + "[32m" + "Company deploy ok " + secret + " done" + ESC + "[0m"
    for out in both(text, secret):
        assert out != MARKER + TRUNCATED, repr(out)
        assert secret not in out and "deploy ok" in out, repr(out)


# ---- Issue 4: the seeded fuzz of the independent evidence (seed 20261112) ---------------------------------------------
_HID = [
    ESC + "[0m",
    ESC + "[31m",
    ESC + "(B",
    "\u200b",
    "\u202e",
    "\u2066",
    "\x07",
    "%1b",
    "&#27;",
    "\\u001b",
    ESC,
]
_WORDS = ["ok", "error", "Company", "user", "log line", "10.0.0.1", "done"]


def _piece(r: random.Random) -> str:
    k = r.random()
    if k < 0.25:
        return r.choice(_WORDS)
    if k < 0.45:
        return HAND
    if k < 0.55:
        return KEY
    if k < 0.75:
        s = r.choice([HAND, KEY])
        i = r.randrange(1, len(s))
        return s[:i] + r.choice(_HID) + s[i:]
    return r.choice(_HID)


def _fuzz_texts(n: int):
    r = random.Random(20261112)  # noqa: S311 - the seeded generator of the independent evidence, not a secret
    for _ in range(n):
        yield " ".join(_piece(r) for _ in range(r.randrange(2, 9)))


def test_b7_i4_seeded_fuzz_no_exception_and_no_readable_window():
    """Issue 4 (mutants 86 to 90): 1500 texts of the independent evidence's generator (the first 1500 of its 3000). Property:
    `prepare_output` and `error_reason` raise nothing, and no 8-character window of the handed-out value or of the key
    stands in the result (c802cc0f: 7 exceptions and 548 readable windows in 3000 texts)."""
    for t in _fuzz_texts(1500):
        for out in both(t, HAND):
            assert not stands(out, HAND) and not stands(out, KEY), (t, out)


def test_b7_i4_a_cut_copy_beside_a_masked_copy_is_not_left():
    """Issue 4 (mutants 86, 87): a form found as written no longer skips the decoded views; a value whole in one place and
    cut in another is masked in both (counted per copy)."""
    text = "a " + KEY + " b AKIAIOSF" + ESC + "I" + "ODNN7EXAMPLE c " + KEY[:6] + "%1b[0m" + KEY[6:]
    for out in both(text, KEY):
        assert not stands(out, KEY, 6), repr(out)


# ---- Issues 5, 6, 8: the direct redact() ------------------------------------------------------------------------------
@pytest.mark.parametrize("opener", ["\x9b", "\x90", "\x9d", "\x9e", "\x9f"])
def test_b7_i5_a_known_value_cut_by_any_opener_is_withheld(opener):
    """Issue 5 (mutant 91): the guard is any sequence opener, not only ESC (ECMA-48 8-bit C1 controls, from memory)."""
    out = redact(opener + HAND + " x", mapping={"<SECRET_1>": HAND}).text
    assert out == WITHHELD_NOTE or not stands(out, HAND, 6), repr(out)


@pytest.mark.parametrize("opener", ["\x9b", "\x90", "\x9d", "\x9e", "\x9f"])
def test_b7_i5_a_key_cut_by_an_opener_never_shows_its_tail(opener):
    out = redact("x " + KEY[:8] + opener + "[0m" + KEY[8:] + " y").text
    assert KEY[9:] not in out, repr(out)


def test_b7_i5_a_key_cut_by_tput_sgr0_is_masked_whole_in_the_direct_redact():
    """Mutant 90: `ESC ( B ESC [ m` (what `tput sgr0` writes) cuts a key; the consuming reading takes the letter `B` as part of
    the sequence, so the key is whole there. Without that reading the key shows as written."""
    text = "x " + KEY[:6] + ESC + "(B" + ESC + "[m" + KEY[6:] + " y"
    out = redact(text).text
    assert out == WITHHELD_NOTE or not stands(out, KEY, 6), repr(out)
    assert "<APIKEY_" in out, repr(out)


def test_b7_i6_two_readings_that_mask_different_values_are_withheld():
    """Issue 6 (mutant 92): the grammar's reading masks the token, the consuming reading the two keys; neither output may be
    shown because each leaves the other's value readable. (C2 of the codebase review was not reproduced as a readable
    token by the reviewer; the guard row is pinned.)"""
    jwt = "eyJhbGciOiJIUzI1NiJ9." + "eyJzdWIiOiIxMjM0NTY3ODkwIn0." + "abcdefghijk"
    text = (
        ESC
        + jwt
        + " "
        + KEY[:6]
        + ESC
        + "(B"
        + ESC
        + "[m"
        + KEY[6:]
        + " and "
        + KEY[:7]
        + ESC
        + "(B"
        + ESC
        + "[m"
        + KEY[7:]
    )
    out = redact(text).text
    assert out == WITHHELD_NOTE or ("yJhbGci" not in out and not stands(out, KEY, 6)), repr(out)


def test_b7_i6_compare_readings_is_the_one_rule():
    """Issue 6 (mutant 93): the rule shared by `redact()` and `runmap._consuming_wins`."""
    assert compare_readings({"a"}, {"a", "b"}) == "second"
    assert compare_readings({"a", "b"}, {"a"}) == "first"
    assert compare_readings({"a"}, {"a"}) == "same"
    assert compare_readings({"a"}, {"b"}) == "conflict"
    assert compare_readings(set(), set()) == "same"
    assert compare_readings({"a", "c"}, {"a", "b"}) == "conflict"


def test_b7_i6_a_reading_that_holds_only_pieces_is_covered():
    """Issue 6 (mutant 97): a reading that glued a word to a key finds a few digits of it as a phone number; the reading that
    found the whole key covers it, so the two do not conflict (the 257-keys control of `test_prh_steps` needs this)."""
    assert compare_readings({KEY}, {KEY[8:]}) == "first"
    assert compare_readings({KEY[8:]}, {KEY}) == "second"
    assert compare_readings({KEY, "x" * 9}, {KEY[8:], "y" * 9}) == "conflict"
    assert compare_readings({KEY}, {KEY[4:], KEY[:10]}) == "first"


@pytest.mark.parametrize(
    "cut",
    ["\u200b", "\u202e", "\ufeff", "\u2066", "\u200d", "\u2060", "\u00ad", "\x07"],
    ids=lambda c: f"u{ord(c):04x}",
)
def test_b7_i8_direct_redact_masks_a_key_cut_by_a_hidden_or_ignorable_character(cut):
    """Issue 8 (mutant 94): class = a hidden item the sequence reader leaves in the text (zero width, bidirectional, BOM,
    soft hyphen, bell): direct `redact()` reads the text as `runmap.canonical` does and masks the key or withholds."""
    for i in (3, 8, 12):
        out = redact("k " + KEY[:i] + cut + KEY[i:] + " y").text
        assert out == WITHHELD_NOTE or not stands(out, KEY, 6), (i, repr(out))


def test_b7_i8_hex_value_cut_by_a_bidirectional_character():
    value = "9F3AC7B2E1D04" + "A6B55C8F0123456789A"
    out = redact("ENCRYPTION_KEY=" + value[:13] + "\u202e" + value[13:] + " z").text
    assert out == WITHHELD_NOTE or value[:10] not in out, repr(out)


def test_b7_i8_d6_a_combining_mark_is_not_a_hidden_item():
    """Decision d6: U+0301 changes the character it follows (the string is a different string, NFKC keeps it), so it is not
    removed and a key with one inside is left as written. Pinned as documented behaviour, not a promise to mask it."""
    text = "k " + KEY[:8] + "́" + KEY[8:] + " y"
    assert redact(text).text == text


def test_b7_i8_plain_text_with_a_zero_width_joiner_is_unchanged():
    """Control: text with a hidden item and no value is returned as written (no over-withholding)."""
    text = "family \U0001f468\u200d\U0001f469 ok"
    assert redact(text).text == text


# ---- Issue 9: spaced-out secrets are documented behaviour, not a promise ---------------------------------------------
def test_b7_i9_spaced_out_secret_is_documented_behaviour():
    """Issue 9: a value written with a visible space between its characters is not masked (a product decision for the
    owner: `q-prh-spaced-secrets`). Pinned so a change is a decision, not an accident."""
    spaced = " ".join(KEY)
    assert redact("k " + spaced + " y").text == "k " + spaced + " y"


# ---- Issue 7: the piece check is exact -------------------------------------------------------------------------------
@pytest.mark.parametrize("n", [136, 300])
def test_b7_i7_a_long_handed_out_secret_cut_at_any_offset(n):
    """Issue 7 (mutant 95): the check is exact: a 6-character stretch of a long secret, at an odd offset, in coloured text."""
    secret = "".join(
        str(i % 10) if i % 4 == 3 else chr(0x61 + (i * 7 + i // 5) % 26) for i in range(n)
    )
    for start in (0, 1, 7, 33, 67, 101, n - 6):
        # one whole copy is found and masked, so the check runs; the 6-character stretch beside it must not stand
        text = ESC + "[0m" + "ok " + secret + " " + secret[start : start + 6] + " done"
        for out in both(text, secret):
            assert secret[start : start + 6] not in out, (n, start, out)


# ---- Issue 12 --------------------------------------------------------------------------------------------------------
def test_b7_i12_h2_fixed_row_a_whole_copy_and_a_cut_copy_with_a_short_tail():
    """Issue 12 (C5, mutant 79): `x HAND y ESC HAND[:6]` + the truncation tail."""
    text = "x " + HAND + " y " + ESC + HAND[:6] + TRUNCATED
    for out in both(text, HAND):
        assert not stands(out, HAND, 6), repr(out)


@pytest.mark.parametrize("n", [5, 6])
def test_b7_i12_mutant_95_the_front_an_esc_ate_the_first_letter_of_is_cut_too(n):
    """Mutant 95: `ESC` takes the first letter of the secret's front (`ESC Q` reads as one sequence), so what is left (`x7mLp`)
    is no form's start; the cut end must lose it too (the 6-window check of the older row did not see 5 characters)."""
    text = "x " + HAND + " y " + ESC + HAND[:n] + TRUNCATED
    for out in both(text, HAND):
        assert HAND[1:n] not in out, repr(out)


def test_b7_i2_a_work_limit_on_a_small_text_gives_the_withheld_note_not_an_error(monkeypatch):
    """Mutant 83: the redactor's work limit (`RedactionLimit`, an `InputTooLarge`) is caught where all tool results pass; it is
    forced here, because the fuzz rows that raised it are fixed."""

    def refuse(*_a, **_k):
        raise runmap.RedactionLimit("forced")

    monkeypatch.setattr(runmap, "redact_untrusted", refuse)
    assert tools.redact_layered("a small text", {}) == MARKER + TRUNCATED
    assert isinstance(tools.prepare_output("a small text", {}, 4000, [HAND]), str)
    assert isinstance(tools.error_reason(ValueError("a small text"), [HAND]), str)


@pytest.mark.parametrize(
    "text",
    [
        KEY + " " + KEY[:3] + "\x07" + KEY[3:],
        KEY + " " + KEY[:10] + ESC + "[0m" + KEY[10:],
        KEY[:16] + ESC + "[31m" + KEY[16:] + " " + KEY,
    ],
)
def test_b7_i4_mutant_86_a_whole_and_a_cut_copy_are_both_masked_with_no_error(text):
    """Mutant 86: needed values counted per value, not per copy: the cut copy raised a limit or left its tail (`LE`)."""
    out = runmap.redact_untrusted(text, {})
    assert out.count("<APIKEY_") == 2 and "LE" not in out.replace("<APIKEY_", ""), repr(out)


def test_b7_i4_mutant_87_a_remnant_of_a_masked_value_is_refused_not_shown():
    """Mutant 87: `AKIAIO(BSFODNN7EXAMPLE` (the charset sequence ate nothing the key needs, a letter is left) beside a whole
    key: the consuming reading masks one copy and leaves a remnant of the other; the text is refused (`RedactionLimit`)."""
    text = "AKIAIO" + ESC + "(BSFODNN7EXAMPLE " + KEY
    with pytest.raises(runmap.RedactionLimit):
        runmap.redact_untrusted(text, {})
    for out in both(text, HAND):
        assert not stands(out, KEY, 8), repr(out)


@pytest.mark.parametrize("text", [KEY + " \x07", "\x07 " + KEY[:13] + "\u202e" + KEY[13:]])
def test_b7_i4_mutant_88_a_value_found_as_written_is_scrubbed_by_the_tool_paths(text):
    """Mutant 88: values the redactor finds as written are scrubbed in the tool output: the marker, not a placeholder."""
    for out in both(text, HAND):
        assert "<APIKEY_" not in out and "<SECRET_REDACTED>" in out, repr(out)


def test_b7_hidden_exports_the_sequence_opener_set():
    seq = hidden.SEQ_ANY
    assert seq.search("\x9b") and seq.search(ESC) and not seq.search("\x07")


@pytest.mark.parametrize("opener", ["\x90", "\x98", "\x9d", "\x9e", "\x9f"])
@pytest.mark.parametrize("end", ["\x07", "\n"])
def test_b7_i5_a_string_opener_ended_by_a_bell_does_not_hide_the_key_in_the_direct_redact(
    opener, end
):
    """Resume brief, case U+0090 and its kin (mutant 98): a string sequence that a bell does not close swallows the rest of the
    line in the grammar's reading, so `redact()` showed `AKIAIOSF` and nothing after it. The character reading finds the whole
    key; a line end really breaks the key (the text shows it broken), so only the bell rows must not show a window."""
    out = redact("key " + KEY[:8] + opener + "x" + end + KEY[8:] + " end").text
    if end == "\x07":
        assert out == WITHHELD_NOTE or not stands(out, KEY, 8), repr(out)
    else:
        assert KEY not in out


# ---- Issue 10: the withheld share, by cause; the clean corpus ----------------------------------------------------------
def test_b7_i10_a_key_cut_by_an_ignorable_character_is_masked_whole_not_withheld():
    """Issue 10 (mutant 99; the extra view of mutant 100 was shown redundant): a key a bidirectional isolate cuts (an ignorable character, not a removed one) was masked
    in its front only, its tail stood, and the piece check withheld the whole result (c802cc0f: withheld)."""
    text = ESC + "[31m " + KEY[:12] + "\u2066" + KEY[12:]
    for out in both(text, HAND):
        assert out != MARKER + TRUNCATED and "withheld" not in out, repr(out)
        assert not stands(out, KEY, 6), repr(out)


def test_b7_i10_a_short_value_that_fronts_a_longer_one_is_masked_after_the_longer():
    """Issue 10 (mutant 101): two values, one the front of the other (`AKIAIOSFODNN` inside the key): masked shortest first the
    tail of the longer one stands and the result is withheld."""
    text = "A\\u001bKIAIOSFODNN7EXAMPLE ok ok AKIAIOS\\u001bFODNN7EXAMPLE Company \x1b[0m"
    for out in both(text, HAND):
        assert out != MARKER + TRUNCATED and "withheld" not in out, repr(out)
        assert not stands(out, KEY, 6), repr(out)


def test_b7_i10_the_clean_corpus_is_never_withheld():
    """Issue 10: ordinary text with ordinary hidden items (colour codes, tabs, joiners, overstrike; the corpus of
    `tests/record_prh_main.py`) is never withheld on the tool and error paths, with a handed-out secret that is not in it, and
    with one masked copy of the secret added (60 runs)."""
    from tests import record_prh_main as rec

    runs = 0
    for name, text in sorted(rec.CORPUS.items()):
        for t, with_copy in ((text, False), (text + "\n" + HAND, True)):
            for out in both(t, HAND):
                runs += 1
                assert HAND not in out, (name, out)
                assert (MARKER in out) is with_copy or with_copy is False, (name, out)
                assert out.replace(MARKER, "").replace(TRUNCATED, "").strip() != "" or with_copy, (
                    name,
                    out,
                )
                assert "withheld" not in out and not out.startswith(MARKER + TRUNCATED), (name, out)
    assert runs == 4 * len(rec.CORPUS)
