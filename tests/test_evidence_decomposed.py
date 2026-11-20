"""Ticket G, invariant G1-I2: ``runtime/evidence.py`` answers as main (51c9fc4) did for the composed AND the decomposed spelling of one value.

Why this file exists. On main, ``evidence.normalise``, ``evidence.contains`` and ``evidence.grounded`` read text through ``runmap.canonical``,
which on main was NFKC of the WHOLE text with the invisible format characters (category Cf) removed afterwards: a letter and its accent written as
two characters came out as the one precomposed letter. The text-folding change makes ``runmap.canonical`` work one character at a time (so match
positions stay exact), which composes nothing; ``evidence.py`` therefore reads through ``runmap.composed`` now. This file pins that the three
functions still give main's answers.

How main's behaviour is pinned: ``_main_canonical`` below is the body of ``runmap.canonical`` at main 51c9fc4, copied; ``_main_normalise`` is the
body of ``evidence.normalise`` there. The expected True and False of ``contains`` and ``grounded`` were read from main's code (both sides went
through the whole-text NFKC, so the spelling could not matter; ``grounded`` refused a value that its canonical form changes).

ONE KNOWN DIFFERENCE from main, pinned by the last test and not hidden: an invisible format character BETWEEN a letter and its accent. Main
normalised first and removed the invisible character afterwards, so the letter and the accent stayed two characters; ``runmap.composed`` removes
it first, so they join. Every word in this file is built from escapes."""

import random
import sys
import types
import unicodedata

from hadavin_sdk.guard import runmap
from hadavin_sdk.runtime import evidence


def _main_canonical(text: str) -> str:
    """``runmap.canonical`` at main 51c9fc4, word for word."""
    return "".join(
        c for c in unicodedata.normalize("NFKC", text) if unicodedata.category(c) != "Cf"
    )


def _main_normalise(text: str) -> str:
    """``evidence.normalise`` at main 51c9fc4."""
    return _main_canonical(text).casefold().strip()


def _contract(*names):
    props = {n: {"type": "string", "identifier": True} for n in names}
    return types.SimpleNamespace(input_schema={"type": "object", "properties": props})


# (label, composed spelling, decomposed spelling): the same value written two ways. NFC of the second is the first.
PAIRS = [
    ("latin e acute", "Jos\u00e9", "Jose\u0301"),
    ("latin a ring", "\u00c5sa", "A\u030asa"),
    ("latin two marks", "\u1ea1\u0308x", "a\u0323\u0308x"),
    ("german umlaut", "M\u00fcller", "Mu\u0308ller"),
    ("cyrillic short i", "\u0419\u043e\u0433", "\u0418\u0306\u043e\u0433"),
    ("greek tonos", "\u03ac\u03bb\u03c6\u03b1", "\u03b1\u0301\u03bb\u03c6\u03b1"),
    ("hangul syllable", "\ud55c\uae00", "\u1112\u1161\u11ab\u1100\u1173\u11af"),
    ("vietnamese", "Nguy\u1ec5n", "Nguye\u0302\u0303n"),
    ("turkish dotted capital", "\u0130zmir", "I\u0307zmir"),
]


def test_the_pairs_are_one_value_written_two_ways():
    for label, composed, decomposed in PAIRS:
        assert composed != decomposed, label
        assert unicodedata.normalize("NFC", decomposed) == composed, label
        assert len(decomposed) > len(composed), label


def test_normalise_gives_the_answer_of_main_for_both_spellings():
    for label, composed, decomposed in PAIRS:
        for spelling in (composed, decomposed):
            assert evidence.normalise(spelling) == _main_normalise(spelling), (
                f"G1-I2 normalise differs from main: {label} {spelling!a}"
            )
        assert evidence.normalise(composed) == evidence.normalise(decomposed), (
            f"G1-I2 normalise gives two keys for one value: {label}"
        )
    # compatibility forms and padding, as main: a full-width word with a separate accent, a ligature, spaces around
    for text in (
        "\uff2a\uff4f\uff53\uff45\u0301",
        "\ufb01le",
        "  Jose\u0301  ",
        "caf\u00e9\u200d",
        "\u2126",
    ):
        assert evidence.normalise(text) == _main_normalise(text), f"{text!a}"
    assert evidence.normalise("\uff2a\uff4f\uff53\uff45\u0301") == "jos\u00e9"


def test_contains_gives_the_answer_of_main_whatever_the_spelling_of_the_text_or_the_value():
    """On main both the text and the value went through whole-text NFKC, so all four combinations were True, and a different value was False."""
    for label, composed, decomposed in PAIRS:
        for text_spelling in (composed, decomposed):
            for value_spelling in (composed, decomposed):
                text = "pod " + text_spelling + " is up"
                assert evidence.contains(text, value_spelling) is True, (
                    f"G1-I2 contains: {label} text {text_spelling!a} value {value_spelling!a}"
                )
                assert evidence.contains(text.upper(), value_spelling, casefold=True) is True, (
                    f"G1-I2 contains casefold: {label} text {text_spelling!a} value {value_spelling!a}"
                )
    for text_spelling in ("Jos\u00e9", "Jose\u0301"):
        text = "pod " + text_spelling + " is up"
        assert evidence.contains(text, "Jose") is False, "the accent is part of the value"
        assert evidence.contains(text, "Jos\u00e8") is False, "another accent is another value"
        assert evidence.contains(text, "Jos") is False, "the front of a longer name is not the name"
        assert evidence.contains(text, "jos\u00e9") is False, "exact unless casefold"
    assert evidence.contains("pod Jose is up", "Jos\u00e9") is False
    assert evidence.contains("pod Jose is up", "Jose\u0301") is False


def test_grounded_gives_the_answer_of_main_for_both_spellings():
    """Main: a value that its canonical form changes is refused (the value the executor gets is the one that is compared), so a DECOMPOSED identifier
    was refused whatever the text held; a precomposed identifier was found in a text of either spelling."""
    contract = _contract("name")
    for label, composed, decomposed in PAIRS:
        for text_spelling in (composed, decomposed):
            texts = ["pod " + text_spelling + " is up"]
            assert evidence.grounded(contract, {"name": composed}, texts, {}) is True, (
                f"G1-I2 grounded: precomposed {label} not found in {text_spelling!a}"
            )
            assert evidence.grounded(contract, {"name": decomposed}, texts, {}) is False, (
                f"G1-I2 grounded: decomposed {label} accepted with {text_spelling!a} (main refused it)"
            )
    for text_spelling in ("Jos\u00e9", "Jose\u0301"):
        texts = ["pod " + text_spelling + " is up"]
        assert evidence.grounded(contract, {"name": "Jose"}, texts, {}) is False
    assert evidence.grounded(contract, {"name": "Jos\u00e9"}, ["pod Jose is up"], {}) is False


def test_the_composed_form_equals_the_canonical_form_of_main_for_every_single_code_point():
    """Every code point alone (surrogates left out: they are not text): what evidence.py reads now equals what it read on main."""
    for cp in range(sys.maxunicode + 1):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        if runmap.composed(ch) != _main_canonical(ch):
            raise AssertionError(f"G1-I2 code point U+{cp:04X} reads differently from main")


def test_normalise_equals_main_on_seeded_mixtures_without_invisible_characters():
    """Seeded mixtures of letters, combining marks, conjoining jamo, ligatures and full-width forms; no invisible format character (see the last
    test for that one difference)."""
    alphabet = (
        [chr(c) for c in range(0x61, 0x7B)]
        + [chr(c) for c in range(0x300, 0x330)]  # combining marks
        + [chr(c) for c in (0x1100, 0x1112, 0x1161, 0x1173, 0x11AB, 0x11AF)]  # jamo
        + [chr(c) for c in (0xFB01, 0xFF21, 0xFF4A, 0x2126, 0x212B, 0x130, 0x131, 0xDF)]
        + [chr(c) for c in (0x410, 0x418, 0x435, 0x3B1, 0x3C9, 0xE9, 0xC5, 0x20)]
    )
    assert all(unicodedata.category(c) != "Cf" for c in alphabet)
    rng = random.Random(20261120)  # noqa: S311 - test data only
    for _ in range(5000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 16)))
        assert evidence.normalise(text) == _main_normalise(text), f"{text!a}"
        nfd = unicodedata.normalize("NFD", text)
        assert evidence.normalise(nfd) == evidence.normalise(text), (
            f"the decomposed form has another key: {text!a}"
        )


def test_known_difference_from_main_an_invisible_character_between_a_letter_and_its_accent_now_joins_them():
    """NOT main's answer, on purpose of ``runmap.composed`` and reported in the G1 evidence: main read e + U+200B + U+0301 as the letter and a
    separate accent (it normalised first and removed the invisible character afterwards), so the precomposed value was NOT found in such a text.
    The fold removes the invisible character first, so it is found. As an identifier VALUE such a spelling is refused, as on main."""
    for hidden in ("\u200b", "\u00ad", "\u2060"):
        spelled = "Jose" + hidden + "\u0301"
        assert _main_normalise(spelled) == "jose\u0301", "what main gave"
        assert evidence.normalise(spelled) == "jos\u00e9", "what the fold gives"
        assert evidence.contains("pod " + spelled + " is up", "Jos\u00e9") is True
        assert (
            evidence.grounded(_contract("name"), {"name": spelled}, ["pod Jos\u00e9 is up"], {})
            is False
        ), "a value with an invisible character is refused, as on main"
