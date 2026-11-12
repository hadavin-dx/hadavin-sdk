"""Marks inside a protected value (P2d-1, review round w3): the redactor scans EVERY view of a line, not only ``fold``.

The class: a spacing mark (Mc), a modifier letter (Lm), a modifier symbol (Sk), a U+0345 after a Greek letter, or an invisible ASCII control
character, put INSIDE a value, hides it from ``fold`` (which keeps the first three and reads the fourth as an iota) while a reader still sees the
value. ``textnorm`` says a scan must look through the views that drop them ("MARKS AND SCANS"). Every secret here is built from parts."""

import importlib
import re
import unicodedata

import pytest

from hadavin_sdk.guard import runmap, textnorm

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")
redact = redact_mod.redact

KEY = "AKIA" + "IOSFODNN7EXAMPLE"
KEY_TAIL = "IOSFODNN7EXAMPLE"
SK_HEAD, SK_TAIL = (
    "a" * 10,
    "b" * 10,
)  # "sk-" + 20 letters is one key; the first ten alone are already a (shorter) key
MARKS = [
    chr(cp)
    for cp in range(0x110000)
    if unicodedata.category(chr(cp)) in textnorm.SPACING_CATEGORIES and cp > 0x7F
]


def _views(text: str) -> list[str]:
    return [*textnorm.fold_views(text), *textnorm.squeeze_views(text), text]


def _leaks(out: str, needle: str) -> bool:
    """True when ANY view of ``out`` still holds the needle (or its squeezed form)."""
    want = textnorm.squeeze(needle)
    return any(needle in v or want in v for v in _views(out))


def test_marks_1_the_four_review_inputs_leave_no_key():
    cases = {
        "mc": ("AKIA" + chr(0x093E) + KEY_TAIL, KEY_TAIL),
        "lm": ("AKIA" + "IOSFODNN7" + chr(0x02B0) + "EXAMPLE", "EXAMPLE"),
        "greek_iota": (chr(0x0391) + chr(0x0345) + "KIA" + KEY_TAIL, KEY_TAIL),
        "sk_secret": ("sk-" + SK_HEAD + chr(0x0903) + SK_TAIL, SK_TAIL),
    }
    for name, (spelled, needle) in cases.items():
        out = redact("the value " + spelled + " end").text
        assert not _leaks(out, needle), (name, out)
        if (
            name == "greek_iota"
        ):  # a Greek look-alike letter sits inside the value: the whole line is withheld, never emitted folded
            assert out.startswith(redact_mod.FOLD_NOTE), out
        else:  # the value is cut out in place and the words around it stay
            assert re.fullmatch(r"the value <[A-Z]+_1> end", out), (name, out)


def test_marks_2_every_spacing_mark_modifier_letter_and_modifier_symbol_inside_a_key_is_masked():
    assert len(MARKS) > 700, len(MARKS)  # 452 Mc + the Lm and Sk of this interpreter, none left out
    leaks = []
    for mark in MARKS:
        for at in (4, 9):  # inside the AKIA prefix and inside the tail
            spelled = KEY[:at] + mark + KEY[at:]
            out = redact("x " + spelled + " y").text
            if _leaks(out, KEY_TAIL) or _leaks(out, "EXAMPLE") or "AKIA" + KEY_TAIL[:3] in out:
                leaks.append((hex(ord(mark)), at))
    assert not leaks, (len(leaks), leaks[:5])


def test_marks_3_every_mark_inside_a_password_value_is_masked_in_every_copy():
    value = "hunter-secret-a1b2c3"
    leaks = []
    for mark in MARKS[
        ::7
    ]:  # a seventh of the marks: a different position than the key test, the password pattern
        spelled = value[:6] + mark + value[6:]
        out = redact("password: " + spelled + "\nagain " + spelled).text
        if _leaks(out, "secret-a1b2c3") or _leaks(out, "hunter"):
            leaks.append(hex(ord(mark)))
    assert not leaks, (len(leaks), leaks[:5])


def test_marks_4_a_greek_letter_with_the_subscript_iota_does_not_hide_a_key():
    leaks = []
    for cp in range(0x370, 0x400):
        ch = chr(cp)
        letter = textnorm.fold_view(ch, iota=False)
        if len(letter) != 1 or letter not in KEY or not ch.isalpha():
            continue
        first = KEY.index(letter)
        spelled = KEY[:first] + ch + chr(0x0345) + KEY[first + 1 :]
        out = redact("k " + spelled + " end").text
        if _leaks(out, KEY_TAIL) or _leaks(out, "EXAMPLE"):
            leaks.append((hex(cp), letter))
    assert not leaks, leaks[:5]
    assert any(textnorm.fold_view(chr(cp), iota=False) == "A" for cp in range(0x370, 0x400))


def test_marks_5_an_invisible_ascii_control_character_inside_a_value_is_masked():
    for ctl in (chr(0x7F), chr(0x01), chr(0x08), chr(0x1B) + "x"):
        for spelled, needle in (
            ("sk-" + SK_HEAD + ctl + SK_TAIL, SK_TAIL),
            ("AKIA" + ctl + KEY_TAIL, KEY_TAIL),
        ):
            out = redact("v " + spelled + " end\nsecond line").text
            assert not _leaks(out, needle), (repr(ctl), out)
            assert "second line" in out, (repr(ctl), out)


def test_marks_6_a_clear_copy_of_a_value_masked_with_a_mark_inside_is_masked_too():
    spelled = "AKIA" + chr(0x093E) + KEY_TAIL
    keys = redact_mod._alias_keys(spelled)
    assert KEY in keys and textnorm.fold(spelled) in keys, (
        keys
    )  # the alias index holds the written fold AND the marks-dropped fold
    # a password-style value: no direct pattern masks a bare copy of it, so only the alias index can
    value = "hunter" + "-secret-a1b2c3"
    spelled_pw = value[:6] + chr(0x0903) + value[6:]
    r = redact("password: " + spelled_pw + " end")
    (placeholder,) = r.mapping
    assert value[:6] not in r.text, r.text
    again = redact("then " + value + " plain", mapping=r.mapping).text
    assert value not in again and placeholder in again, again


def test_marks_7_a_second_multi_line_value_that_starts_inside_the_first_is_withheld_to_its_end():
    """Review F4: a private key block with a look-alike letter in its first line, and a `Private-Lines` block (which runs to the end of the
    text) that starts INSIDE it with a look-alike letter in its label. The second block's tail used to stay in clear."""
    e, r = chr(0x415), chr(0x420)
    tail = "SECRETTAILDATA" + "x9Q2"
    text = "\n".join(
        [
            "-----B" + e + "GIN PRIVATE KEY-----",
            "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC",
            r + "rivate-Lines: 2",
            "-----END PRIVATE KEY-----",
            tail,
            "last line",
        ]
    )
    out = redact(text).text
    assert tail not in out and "MIIEvQ" not in out, out
    assert out.startswith(redact_mod.FOLD_NOTE)
    # the withheld block lists BOTH values it holds (the key block and the one that starts inside it), not only the first
    assert len(re.findall(r"<PRIVKEY_\d+>", out)) == 2, out
    plain = redact(
        "one\n" + text.replace(e, "E").replace(r, "P")
    ).text  # the same block spelled plainly is masked by the direct pass too
    assert tail not in plain, plain


def test_marks_8_a_withheld_block_keeps_the_line_end_it_had():
    e = chr(0x415)
    block = [
        "-----B" + e + "GIN PRIVATE KEY-----",
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC",
        "-----END PRIVATE KEY-----",
    ]
    with_eol = redact("\n".join(block) + "\nnext\n").text
    assert with_eol.endswith("\nnext\n"), with_eol
    no_eol = redact("\n".join(block)).text
    assert not no_eol.endswith("\n"), repr(
        no_eol
    )  # a text that did not end in a newline does not get one


def test_marks_9_text_without_marks_or_a_secret_comes_out_unchanged():
    for text in (
        "Café résumé naïve",
        "यह एक सामान्य वाक्य है",  # Devanagari with Mc vowel signs, nothing to mask
        "これは通常の文章ーです。",  # Japanese prolonged sound mark (Lm)
        "a^b `code` é",
        "ᾳ Ἀθῆναι",
    ):
        assert redact(text).text == text, text


def test_marks_10_runmap_also_reads_the_text_without_its_marks():
    spelled = "AKIA" + chr(0x093E) + KEY_TAIL
    assert any(KEY in v for v in runmap._views("k " + spelled + " end")), runmap._views(spelled)
    out = runmap.redact_text("k " + spelled + " end", {})
    assert not _leaks(out, KEY_TAIL), out


def test_marks_11_the_views_by_name_are_exactly_the_views_of_fold_views():
    samples = [
        "plain",
        "AKIA" + chr(0x093E) + KEY_TAIL,
        chr(0x0391) + chr(0x0345) + "KIA",
        chr(0x0391) + chr(0x0345) + "K" + chr(0x02B0) + "IA" + chr(0x0903),
        "ͺ" + "x" + chr(0x0345),
    ]
    for s in samples:
        named = []
        for marks in (False, True):
            for iota in (True, False):
                v = textnorm.fold_view(s, marks_dropped=marks, iota=iota)
                if v not in named:
                    named.append(v)
        assert sorted(named) == sorted(textnorm.fold_views(s)), s
        assert textnorm.fold_view(s) == textnorm.fold(s)
        assert textnorm.without_spacing_marks(s) == "".join(
            c for c in s if unicodedata.category(c) not in textnorm.SPACING_CATEGORIES
        )


def test_marks_12_the_weight_of_a_long_text_is_remembered_by_digest_and_never_wrong(monkeypatch):
    text = "".join(chr(cp) for cp in range(0x4E00, 0x4E00 + 3000))
    monkeypatch.setattr(textnorm, "_WEIGHT_MEMO", {})  # restored after the test
    first = textnorm._weight(text)
    assert len(textnorm._WEIGHT_MEMO) == 1
    (key,) = textnorm._WEIGHT_MEMO
    assert isinstance(key, bytes) and len(key) == 32  # a digest: no text is kept
    assert textnorm._weight(text) == first == sum(textnorm._char_weight(c) for c in text)
    other = text + chr(
        0x5000
    )  # another text is never answered with the remembered weight of this one
    assert textnorm._weight(other) == sum(textnorm._char_weight(c) for c in other) == first + 1
    for i in range(textnorm._WEIGHT_MEMO_MAX + 5):
        textnorm._weight(text + chr(0x5000 + i))
    assert len(textnorm._WEIGHT_MEMO) <= textnorm._WEIGHT_MEMO_MAX


@pytest.mark.parametrize("kind", ["mc", "lm", "sk"])
def test_marks_13_the_three_categories_are_all_covered_by_the_mark_list(kind):
    wanted = {"mc": "Mc", "lm": "Lm", "sk": "Sk"}[kind]
    assert sum(unicodedata.category(m) == wanted for m in MARKS) > 50


def test_marks_14_the_alignment_of_every_view_agrees_with_that_view_of_the_fold_or_steps_aside():
    views = [(False, True), (False, False), (True, True), (True, False)]
    for mark in MARKS + [chr(0x0345), "^", "`"]:
        for s in ("e" + mark + "x", chr(0x0391) + mark + "k", "A" + mark + chr(0x0345) + "B"):
            for marks, iota in views:
                got = redact_mod._Redactor._aligned_fold(s, float("inf"), (marks, iota, 0))
                want = textnorm.fold_view(s, marks_dropped=marks, iota=iota).replace("\u2044", "/")
                assert got is None or got[0] == want, (hex(ord(mark)), marks, iota)
                if (
                    marks and s == "e" + mark + "x"
                ):  # a marks-dropped view of a plain letter pair with a mark: aligned, never stepped aside
                    assert got is not None and got[0] == "ex", (hex(ord(mark)), got)


def test_marks_15_a_hangul_line_is_refused_at_the_same_size_by_the_redactor_and_the_fold():
    """Review F3. A Hangul syllable is 3 characters after NFKD and its fold weight is 3, so the two size rules agree: ticket V23 (the class "weight above
    the NFKD length", such as the German sharp s) does not apply to it. 87,381 syllables (262,143) pass both; 87,382 (262,146) are refused by both (the test takes 0.5 s CPU, measured 2026-11-11):
    `redact_text` with `InputTooLarge`, the bare `redact` with `TextTooLong` (nothing is shown, fail closed)."""
    syllable = chr(0xAC01)
    assert textnorm._char_weight(syllable) == len(unicodedata.normalize("NFKD", syllable)) == 3
    assert redact(syllable * 87_381).text.startswith(syllable)
    with pytest.raises(textnorm.TextTooLong):
        redact(syllable * 87_382)
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text(syllable * 87_382, {})


EDGE_SAMPLES = [  # (text before the value, the value, text after it); every line also holds a non-ASCII letter, so the fold scan runs
    ("password=", "Hunter2" + "abc", " end"),
    ("secret: ", "Hunter2" + "abc", " end"),
    ("api_key=", "Hunter2" + "abc", " end"),
    ("Authorization: Bearer ", "Hunter2" + "abc", " end"),
    ("", "sk-" + SK_HEAD + SK_TAIL, " end"),
    ("", KEY, " end"),
    ("email ", "jo" + "@example.com", " end"),
]


def test_marks_16_a_mark_beside_a_value_is_masked_with_it():
    """Review w4 M1. The marks-dropped views cut a value short at the mark beside it and left the mark in clear. The class: ADDING a spacing
    mark, modifier letter or modifier symbol before or after a value must not change what is masked. Checked for every open-ended pattern
    and for fixed-length ones, with a mark before, after, and on both sides, and with the same value twice in a line."""
    leaks = []
    marks = [*MARKS[::9], "^", "`", chr(0xB4), chr(0x2B0), chr(0x93E)]
    for pre, value, post in EDGE_SAMPLES:
        base = redact("caf\u00e9 " + pre + value + post).text
        assert value not in base and "<" in base, (pre, base)
        for mark in marks:
            for before, after in ((mark, ""), ("", mark), (mark, mark * 2)):
                text = "caf\u00e9 " + pre + before + value + after + post
                out = redact(text).text
                # an open-ended value (a password, a secret, a token) takes the mark beside it with it; a fixed-shape key or address ends where
                # its shape ends, so only its own characters must be gone
                open_ended = pre.endswith(("=", ": ", "Bearer "))
                if (
                    (open_ended and mark in out)
                    or value in out
                    or textnorm.fold(value) in textnorm.fold(out)
                ):
                    leaks.append((pre, hex(ord(mark)), bool(before), bool(after)))
                twice = redact(text + " " + pre + before + value + after + post).text
                if (open_ended and mark in twice) or value in twice:
                    leaks.append(("twice", pre, hex(ord(mark))))
    assert not leaks, (len(leaks), leaks[:5])


def test_marks_17_an_ascii_circumflex_or_backtick_is_a_mark_only_on_a_line_with_other_non_ascii_text():
    """Review w4 m1, decided on the evidence: the fold scan (and so the marks-dropped views) runs only for a line with a non-ASCII character
    (``_plain``). On an all-ASCII line ``^`` and the backtick are the visible characters they look like, so ``AKIA^...`` is a different
    string that no pattern claims; the same on 8b2b716. With one non-ASCII letter on the line they are read as marks and the key is masked.
    This pins that boundary (CHANGELOG, P2d-1: "What this does NOT promise")."""
    spelled = KEY[:4] + "^" + KEY[4:]
    assert redact("k " + spelled + " e").text == "k " + spelled + " e"
    out = redact("k caf\u00e9 " + spelled + " e").text
    assert KEY_TAIL not in out and "<" in out, out


CONTROLS = [chr(cp) for cp in (*range(0x20), 0x7F, *range(0x80, 0xA0)) if cp not in (0x0A, 0x0D)]
PW = "Hunter2" + "abcdef"
PREFIXES = ["k ", "user\t", "id: ", "", "k\t"]  # a space, a word and a tab, a label, nothing, a tab
SUFFIXES = [" e", "", "\tok", "\t"]


def _windows(value: str, size: int = 4) -> list[str]:
    return [value[i : i + size] for i in range(len(value) - size + 1)]


def _leaks_of(secret: str, text: str) -> bool:
    out = redact(text).text
    return any(w in out for w in _windows(secret))


def test_marks_18_a_control_character_inside_a_key_or_a_value_leaves_no_piece_in_clear():
    """Round w5. The class "a control character inside a secret splits it so a piece stays visible", over EVERY position of the key and of the
    password value, every C0 and C1 control character except the two line ends, five prefixes and four suffixes. Escape and U+009B are
    alone here (a whole sequence is test 20)."""
    leaks = []
    for ctl in CONTROLS:
        for at in range(1, len(KEY)):
            for pre, suf in zip(PREFIXES, SUFFIXES * 2, strict=False):
                if _leaks_of(KEY, pre + KEY[:at] + ctl + KEY[at:] + suf):
                    leaks.append(("key", hex(ord(ctl)), at, pre, suf))
        for at in range(1, len(PW)):
            if _leaks_of(PW, "password=" + PW[:at] + ctl + PW[at:] + " e"):
                leaks.append(("pw", hex(ord(ctl)), at))
    assert not leaks, (len(leaks), leaks[:4])


def test_marks_20_an_escape_sequence_inside_a_key_or_a_value_leaves_no_piece_in_clear_and_loses_no_real_character():
    """Round w5, majors 1 and 2: a sequence (ESC [ parameters final, ESC and a letter, U+009B parameters final) at ANY position, and in front of
    a key at the start of a line or after a label. Which characters of a sequence are the key's own cannot be known, so every reading is
    scanned: the whole sequence dropped, all but its last character dropped, the sequence read as a space, only the ESC dropped."""
    shapes = [
        "\x1b[0m",
        "\x1b[1;31m",
        "\x1b[F",
        "\x1b[",
        "\x1bA",
        "\x9b1I",
        "\x9b2a",
        "\x9b7E",
        "\x9bp",
        "\x9b",
    ]
    leaks = []
    for seq in shapes:
        for at in range(len(KEY) + 1):
            for pre in PREFIXES:
                if _leaks_of(KEY, pre + KEY[:at] + seq + KEY[at:] + " e"):
                    leaks.append(("key", seq, at, pre))
        for at in range(len(PW) + 1):
            if _leaks_of(PW, "password=" + PW[:at] + seq + PW[at:] + " e"):
                leaks.append(("pw", seq, at))
    assert not leaks, (len(leaks), leaks[:6])
    for text in ("k AKIA\x1b[0m" + KEY[4:] + " e", "AKIAIOS\x1b[F" + KEY[7:], "AKIA\x9b1" + KEY[4:], "id: \x9b" + "password=" + PW,
                 "id: \x1b" + KEY, "k " + KEY[:14] + "\x9b" + KEY[14:] + " e"):  # fmt: skip
        out = redact(text).text
        assert "<APIKEY_1>" in out or "<SECRET_1>" in out, (text, out)
    assert (
        redact("foo\x1b[1mbar").text == "foo bar"
    )  # a sequence that hides nothing is still removed, with a boundary


def test_marks_21_a_white_space_control_beside_a_non_letter_character_of_a_secret_is_read_like_any_other():
    """Round w5, major 3: the all-ASCII line must not behave differently from the line with one non-ASCII letter on it, whatever stands beside
    the tab (a letter, a digit or one of ``_ - . + / =``)."""
    for ctl in "\t\x0b\x0c\x1c":
        for left, right in (("ghp_", "IOSFODNN7EXAMPLE" * 2), ("sk-", "abcdefghijklmnopqrstuvwxyz"), ("sk_live_", "abcdefghij" * 2),
                            ("password=", "Hunter2abc-" + "def"), ("password=", "Hunter2abc_def"), ("password=", "Hunter2abc.def"),
                            ("password=", "Hunter2abc+def"), ("password=", "Hunter2abc/def"), ("password=", "Hunter2abc=def")):  # fmt: skip
            secret = right
            for at in range(len(right)):
                plain = "x " + left + right[:at] + ctl + right[at:] + " e"
                assert not _leaks_of(secret, plain), repr(plain)
                assert not _leaks_of(secret, plain + "\u00e9"), repr(
                    plain
                )  # the same line with one non-ASCII letter


def test_marks_18b_a_new_line_or_carriage_return_is_a_line_end_and_cuts_a_key_in_two():
    """The boundary that stays: a line end is not read as a separator inside a value (CHANGELOG, P2d-1). A key cut by one is two lines. Also with
    a non-ASCII word on the line and with a spacing mark in the key (the fold scan runs there, the line ends must hold there too)."""
    for end in ("\n", "\r", "\r\n"):
        for pre, mid in (("k ", ""), ("caf\u00e9 ", ""), ("k ", "\u093e")):
            text = pre + KEY[:4] + mid + end + KEY[4:] + " e"
            assert redact(text).text == text, (pre, mid, end)


def test_marks_18c_a_tab_between_fields_is_kept_and_only_a_secret_and_the_field_joined_to_it_are_masked():
    assert redact("a\tb\tc\n1\t2\t3").text == "a\tb\tc\n1\t2\t3"
    out = redact("user\t" + KEY + "\tok").text
    assert out.startswith("user\t<APIKEY_1>") and KEY not in out, (
        out
    )  # stated: the field after a masked key may go with it
    out = redact("id\tpassword=abc\tstatus=ok").text
    assert out == "id\tpassword=<SECRET_1>", (
        out
    )  # stated over-masking: the field after a secret is masked with it


def test_marks_18d_an_escape_character_keeps_the_letter_after_it_between_two_word_characters():
    out = redact("k " + KEY[:1] + "\x1b" + KEY[1:] + " e").text
    assert KEY_TAIL not in out and "<APIKEY_1>" in out, out
    seq = redact(
        "foo\x1b[1mbar"
    ).text  # a real sequence is still removed, and a boundary stays where it stood
    assert seq == "foo bar", seq
    assert "\x1b" not in seq and "[1m" not in seq


def test_marks_19_a_look_alike_letter_with_a_subscript_iota_does_not_withhold_the_line_beside_an_address():
    for text in ("\u1fb3 jos\u00e9@example.com", "jos\u00e9@example.com \u1fb3"):
        out = redact(text).text
        assert redact_mod.FOLD_NOTE not in out and "<EMAIL_" in out and "\u1fb3" in out, out


def test_marks_22_a_stored_value_with_a_tab_beside_a_non_letter_gets_its_alias_so_a_clear_copy_is_masked():
    """Round w5, minor 6: the alias index learns the spellings of a masked value; a tab beside ``-`` made the value look plain and it got none."""
    out = redact("password=Hunter2abc-\tdef and later Hunter2abc-def").text
    assert "Hunter2abc" not in out and "def" not in out.replace("<", ""), out


def test_marks_23_a_masked_value_keeps_the_white_space_control_beside_it_and_a_sequence_in_front_is_read_as_a_space():
    """Round w5, minor 3 and mutants: the run of marks a masked value takes with it is spacing marks, modifier letters and modifier symbols
    (``_is_edge_mark``), not the white-space-like controls (``_is_spacing`` counts those, to join across them)."""
    mc = (
        KEY[:4] + "\u093e" + KEY[4:]
    )  # a spacing mark inside: only the views that drop it read the key, and the line is treated per view
    assert redact("a\t" + mc + " b c").text == "a\t<APIKEY_1> b c"
    assert redact("a " + mc + "\t b c").text == "a <APIKEY_1>\t b c"
    assert (
        redact("ok " + KEY + "\u02b0 e").text == "ok <APIKEY_1> e"
    )  # a modifier letter beside the value goes with it
    assert (
        redact("foo\x1b[1m" + KEY).text == "foo<APIKEY_1>"
    )  # glued in front: the sequence is read as a space, found, and removed
    assert (
        redact("k " + KEY[:14] + "\x9b" + KEY[14:] + " e").text == "k <APIKEY_1> e"
    )  # a piece found in one view and the whole in another: ONE value
    m: dict[str, str] = {}
    assert (
        runmap.redact_text("k A\x85" + KEY[1:] + " e", m) == "k <APIKEY_2> e"
    )  # runmap's second pass reads it without the NEL (the number shows it)


def test_marks_24_a_mark_inside_a_key_and_a_tab_glued_to_a_word_beside_it_leave_no_piece_in_clear():
    """Found while fixing round w5: the views that drop the marks also dropped the tab that stood between the key and the word before it."""
    leaks = []
    for mark in ("\u093e", "\u02b0", "\u0903", "\u02c6"):
        for at in range(1, len(KEY)):
            for pre, suf in (("a\t", " b c"), ("a\t", "\tb c"), ("a ", "\tb"), ("user\t", "\tok")):
                if _leaks_of(KEY, pre + KEY[:at] + mark + KEY[at:] + suf):
                    leaks.append((hex(ord(mark)), at, pre, suf))
    assert not leaks, (len(leaks), leaks[:4])


def test_marks_25_strip_ansi_keeps_one_letter_after_an_escape_between_word_characters_and_removes_a_sequence():
    assert redact_mod.strip_ansi("a\x1bXb") == "a\x1bXb"  # the letter may be a key's own
    assert redact_mod.strip_ansi("a\x1b[0mb") == "a b"
    assert redact_mod.strip_ansi("a\x9b1Ib") == "a b"


def test_marks_26_a_key_glued_to_a_word_by_one_tab_and_cut_by_another_leaves_no_piece_in_clear():
    """Found in round 5: ``user<TAB>AKIAIOSF<TAB>ODNN7EXAMPLE`` read with all tabs dropped glues the word to the key; with all tabs kept
    the key is cut. Only the view that keeps the tab in front and drops the one inside finds it."""
    leaks = []
    for ctl in ("\t", "\x0b", "\x0c", "\x1f"):
        for at in range(1, len(KEY)):
            for pre, suf in (("user" + ctl, ""), ("user" + ctl, ctl + "ok"), ("", ctl + "ok")):
                if _leaks_of(KEY, pre + KEY[:at] + ctl + KEY[at:] + suf):
                    leaks.append((hex(ord(ctl)), at, pre, suf))
    assert not leaks, (len(leaks), leaks[:4])
    assert "<APIKEY_1>" in runmap.redact_text("user\t" + KEY[:8] + "\t" + KEY[8:], {})


GAP_ITEMS = [
    "\t",
    "\x1d",
    "\x1b[0m",
    "\x9b1m",
    "\u093e",
]  # a tab, a group separator, two escape sequences, a mark
GAP_MORE = [
    "\x1b[?25h",
    "\x1b[2 q",
    "\x1b]0;t\x07",
    "\u200b",
    "\x85",
    "\x1f",
]  # a private parameter, an intermediate byte, a title string, a zero-width space, NEL, U+001F
PRE = ("k ", "user\t", "id: ", "a\x1b[0m")
SUF = (" e", "", "\tok")


def _pieces_left(secret: str, text: str, size: int = 3) -> list[str]:
    out = redact(text).text
    return [w for w in _windows(secret, size) if w in out]


def _pair_leaks(firsts: list[str], seconds: list[str]) -> list[tuple]:
    leaks = []
    for a in firsts:
        for b in seconds:
            for p in range(len(KEY) + 1):
                for q in range(p, len(KEY) + 1):
                    if p == 0 and q == 0:
                        continue
                    spelled = KEY[:p] + a + KEY[p:q] + b + KEY[q:]
                    for pre in PRE:
                        for suf in SUF:
                            if _pieces_left(KEY, pre + spelled + suf):
                                leaks.append((a, b, p, q, pre, suf))
    return leaks


def test_marks_27_two_hiding_techniques_at_any_two_positions_leave_no_three_character_piece():
    """Round 6. The class: techniques that each work alone are not combined. Every ordered pair of five items (a tab, a group separator, two
    escape sequences, a mark) at every pair of positions of the key (the two may stand at the same place), against the FULL product of four
    prefixes and three suffixes; no window of THREE characters of the key may stay in the text."""
    leaks = _pair_leaks(GAP_ITEMS, GAP_ITEMS)
    assert not leaks, (len(leaks), leaks[:3])


def test_marks_27b_the_other_shapes_beside_a_tab_at_any_two_positions_leave_no_three_character_piece():
    leaks = _pair_leaks(GAP_MORE, ["\t"]) + _pair_leaks(["\t"], GAP_MORE)
    assert not leaks, (len(leaks), leaks[:3])


def test_marks_27c_three_techniques_at_any_three_positions_leave_no_three_character_piece():
    leaks = []
    order = [("\t", "\x1b[0m", "\u093e"), ("\x1b[1m", "\x1e", "\t"), ("\t", "\t", "\x9b2K")]
    for items in order:
        for p in range(len(KEY) + 1):
            for q in range(p, len(KEY) + 1):
                for r in range(q, len(KEY) + 1):
                    if p == q == r == 0:
                        continue
                    a, b, c = items
                    spelled = KEY[:p] + a + KEY[p:q] + b + KEY[q:r] + c + KEY[r:]
                    for pre, suf in (("user\t", "\tok"), ("k ", " e")):
                        if _pieces_left(KEY, pre + spelled + suf):
                            leaks.append((items, p, q, r, pre, suf))
    assert not leaks, (len(leaks), leaks[:3])


def test_marks_28_a_key_after_any_number_of_tab_separated_columns_with_hidden_items_inside_is_masked():
    """Runs of white-space-like controls numbered 0 to 6 in front of the key, with a tab and an escape sequence inside it (the old views tried
    only the first three runs)."""
    leaks = []
    for runs in range(7):
        for sep in ("\t", "\x1f"):
            for at in range(1, len(KEY) - 1):
                spelled = KEY[:at] + sep + KEY[at : at + 2] + "\x1b[0m" + KEY[at + 2 :]
                for tail in (" e", "\tok", ""):
                    text = ("w" + sep) * runs + "user" + sep + spelled + tail
                    if _pieces_left(KEY, text):
                        leaks.append((runs, sep, at, tail))
    assert not leaks, (len(leaks), leaks[:3])


def test_marks_29_the_reproduced_inputs_of_round_6_are_masked():
    k = "AKIA" + "IOSFODNN7" + "EXAMPLE"
    g = "ghp_" + "A" * 18 + "\t" + "B" * 18
    for text in (
        "a\tb\tc\td\t" + k[:12] + "\t" + k[12:] + " e",
        "a\tb\tc\tuser\t" + k[:8] + "\t" + k[8:] + " e",
        "user\t" + k[:4] + "\x1b[0m" + k[4:8] + "\t" + k[8:] + " e",
        "user\t" + k[:7] + "\t\x1b[0m" + k[7:] + " e",
        "user\t" + k[:8] + "\t" + k[8:13] + "\x1b[1m" + k[13:] + " e",
        "user\x1b[0m" + k[:7] + "\x1b[0m" + k[7:] + " e",
        "a\tb\tc\td\t" + g,
    ):
        out = redact(text).text
        assert "<APIKEY_1>" in out and not _pieces_left(k, text) and "BBB" not in out, (text, out)
    assert (
        redact("id: \x9b" + k).text == "id: \x9b<APIKEY_1>"
    )  # the placeholder is not eaten by the sequence remover


def test_marks_30_the_marks_dropped_view_as_written_drops_the_white_space_controls_and_flags_them_like_marks():
    """The view with no gap (``read`` 0) is what ``fold_views`` calls a marks-dropped view: it drops the spacing marks AND the white-space-like
    controls; ``_mark_flags`` flags a tab-like control as a mark, ``_is_edge_mark`` does not (a control is not a mark beside a value)."""
    assert redact_mod._view("a\tb\u093ec\x1fd", True, True) == "abcd"
    assert redact_mod._view("a\tb", False, True) == "a b"
    assert redact_mod._mark_flags("\t")[0] and redact_mod._mark_flags("\u093e")[0]
    assert not redact_mod._mark_flags("a")[0]
    assert not redact_mod._is_edge_mark("\t") and redact_mod._is_edge_mark("\u093e")


def test_marks_31_a_line_ends_at_new_line_or_carriage_return_only_so_a_withheld_line_takes_the_rest_of_its_text():
    """A vertical tab, form feed, U+001C, NEL or U+2028 is not a line end for the redactor: the line stays whole, so the note replaces all of it."""
    for sep in ("\x0b", "\x0c", "\x1c", "\x85", " "):
        out = redact("АKIA" + KEY_TAIL + sep + "tail words").text
        assert "tail" not in out and out.startswith("[line withheld"), (hex(ord(sep)), out)


def test_marks_32_a_hidden_item_beside_a_value_stays_in_the_text_and_counts_as_the_space_it_may_stand_for():
    """Exact outputs, one per way the gap view can go wrong: a hidden item at the END of a match is not part of the value (the item stays);
    a character the fold drops, a spacing mark, an escape sequence or a tab in front of a key is the space before it (the key is masked
    although a word is glued to it); a key cut by a tab on a line with no other hidden item is found."""
    assert redact("ok " + KEY + "\u200b e").text == "ok <APIKEY_1>\u200b e"
    assert redact("user\u200b" + KEY + " e").text == "user\u200b<APIKEY_1> e"
    assert (
        redact("user\u200b" + KEY[:6] + "\u200b" + KEY[6:] + " e").text == "user\u200b<APIKEY_1> e"
    )
    assert redact("user\u093e" + KEY + " e").text == "user<APIKEY_1> e"
    assert redact("user\x1b[0m" + KEY + " e").text == "user<APIKEY_1> e"
    assert redact("user\t" + KEY[:8] + "\t" + KEY[8:] + " e").text == "user\t<APIKEY_1> e"
    assert redact("a\u200b" + KEY + "\x1b[1m e").text == "a\u200b<APIKEY_1> e"
    assert (
        redact("caf\u00e9 password=\ufe0fHunter2abc\u0301 \u093e").text
        == "caf\u00e9 password=\ufe0f<SECRET_1>\u0301 \u093e"
    )  # a hidden item and a mark beside a value stay


def test_marks_33_a_gap_is_skipped_after_every_item_a_pattern_reads_and_is_never_read_as_an_item():
    """``_tolerant``: ``a[^z]b`` must not take the gap for its middle character (the guard), ``ab+c`` takes a gap after each item, and a gap
    stands for nothing at the front of a match."""
    gap = redact_mod.GAP
    p = redact_mod._tolerant(re.compile("a[^z]b"))
    assert (
        p.fullmatch("a" + gap + "b") is None
        and p.fullmatch("axb")
        and p.fullmatch("ax" + gap + "b")
    )
    q = redact_mod._tolerant(re.compile("ab+c"))
    assert (
        q.fullmatch("a" + gap + "b" + gap + "b" + gap + "c")
        and q.fullmatch("a" + gap + "c") is None
    )
    assert q.search(gap + "abc").start() == 1
    assert redact_mod._reads_gap(*_parse_one("[^z]")) and not redact_mod._reads_gap(
        *_parse_one("a")
    )
    assert not redact_mod._reads_gap(*_parse_one("[a-z]")) and redact_mod._reads_gap(
        *_parse_one(r"\W")
    )


def _parse_one(src: str):
    from re import _parser

    parsed = _parser.parse(src)
    op, av = parsed.data[0]
    return op, av, parsed.state
