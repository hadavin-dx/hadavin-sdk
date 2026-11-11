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
    r = redact("first " + spelled + " end")
    assert (
        KEY in set(redact_mod._alias_keys(next(iter(r.mapping.values()))))
        or KEY in r.mapping.values()
    )
    again = redact("then " + KEY + " plain", mapping=r.mapping).text
    assert KEY not in again, again


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


def test_marks_12_the_weight_of_a_long_text_is_remembered_by_digest_and_never_wrong():
    text = "".join(chr(cp) for cp in range(0x4E00, 0x4E00 + 3000))
    textnorm._WEIGHT_MEMO.clear()
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
    the NFKD length", such as the German sharp s) does not apply to it. 87,381 syllables (262,143) pass both; 87,382 (262,146) are refused by both:
    `redact_text` with `InputTooLarge`, the bare `redact` with `TextTooLong` (nothing is shown, fail closed)."""
    syllable = chr(0xAC01)
    assert textnorm._char_weight(syllable) == len(unicodedata.normalize("NFKD", syllable)) == 3
    assert redact(syllable * 87_381).text.startswith(syllable)
    with pytest.raises(textnorm.TextTooLong):
        redact(syllable * 87_382)
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text(syllable * 87_382, {})
