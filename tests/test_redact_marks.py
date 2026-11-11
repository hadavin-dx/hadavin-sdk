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
                got = redact_mod._Redactor._aligned_fold(s, float("inf"), (marks, iota))
                want = textnorm.fold_view(s, marks_dropped=marks, iota=iota).replace("\u2044", "/")
                assert got is None or got[0] == want, (hex(ord(mark)), marks, iota)


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


@pytest.mark.parametrize("cp", [0x09, 0x0B, 0x0C, 0x1C, 0x85])
def test_marks_18_white_space_inside_a_key_is_not_undone_but_an_invisible_control_character_is(cp):
    """The hidden-control-character class: NUL, 0x01-0x08, 0x0E-0x1A and DEL are dropped by the fold and the key is masked. Tab, VT, FF,
    FS and NEL are read as a SPACE by the fold, as a reader sees them: a key cut by one is two words, which no pattern claims; the same on
    8b2b716 (evidence: handover note, ctl-compare.txt). ESC is cut away together with the next character by an earlier stage."""
    for at in (4, 10):
        text = "k " + KEY[:at] + chr(cp) + KEY[at:] + " e"
        assert redact(text).text == text, (hex(cp), at)
    for hidden in (0x00, 0x01, 0x08, 0x0E, 0x1A, 0x7F):
        out = redact("k " + KEY[:4] + chr(hidden) + KEY[4:] + " e").text
        assert KEY_TAIL not in out and "<" in out, (hex(hidden), out)


def test_marks_19_a_look_alike_letter_with_a_subscript_iota_does_not_withhold_the_line_beside_an_address():
    for text in ("\u1fb3 jos\u00e9@example.com", "jos\u00e9@example.com \u1fb3"):
        out = redact(text).text
        assert redact_mod.FOLD_NOTE not in out and "<EMAIL_" in out and "\u1fb3" in out, out
