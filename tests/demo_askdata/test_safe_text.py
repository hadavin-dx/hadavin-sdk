"""A-11: nothing forbidden survives `clean`; attacks stay visible."""

import random

from askdata.safe_text import clean, is_forbidden

ESC = chr(27)
BEL = chr(7)
BS = chr(92)


def test_complete_ansi_and_osc_sequences_are_removed_whole():
    assert clean(f"a{ESC}[2K{ESC}[1Ab") == "ab"
    assert clean(f"x{ESC}]8;;http://evil.example{BEL}link{ESC}]8;;{BEL}y") == "xlinky"
    assert clean(f"x{ESC}]0;title{ESC}{BS}y") == "xy"


def test_lone_escape_c1_and_bidi_become_visible_text():
    assert clean(ESC + "x") == BS + "x1bx"
    assert clean(chr(0x9B) + "x") == BS + "x9bx"
    assert clean("a" + chr(0x202E) + "b") == "a" + BS + "u202eb"
    assert clean(chr(0) + chr(127)) == BS + "x00" + BS + "x7f"


def test_newline_and_tab_are_kept_except_in_cells():
    assert clean("a\nb\tc") == "a\nb\tc"
    assert clean("a\nb\tc", cell=True) == "a b c"


def test_500_random_strings_contain_no_forbidden_character_after_clean():
    rng = random.Random(7)  # noqa: S311  # test data, not a security use
    pool = [chr(i) for i in range(0x30)] + [chr(i) for i in range(0x7F, 0xA0)]
    pool += list("[];ab Z") + [BS] + [chr(c) for c in (0x200B, 0x202E, 0x2066, 0xFEFF)]
    pool += [ESC + "[31m", ESC + "]8;;x" + BEL]
    for _ in range(500):
        text = "".join(rng.choice(pool) for _ in range(rng.randint(0, 40)))
        assert not any(is_forbidden(ch, keep_whitespace=False) for ch in clean(text, cell=True)), (
            repr(text)
        )
        assert not any(is_forbidden(ch) for ch in clean(text)), repr(text)
