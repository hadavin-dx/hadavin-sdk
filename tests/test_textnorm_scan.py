"""P1b: the DENY keys of the text fold (``scan_keyset``, ``same_person``), the gaps it closes, and the script check.

Look-alikes are built with ``chr()``. Facts of one Unicode version are never written here: the tests state properties that hold on every
interpreter, or read the live table (the digit decisions, the modifier letters). No wall-clock assertions: the perf rows (S_call, SK-5) live
in ``tests/test_textnorm_perf.py`` (marker ``perf``), which no mutation run lists. The assertions a mutant must trip carry a message; the
mutant list (``tests/textnorm_mutants.py``) names a fragment of that message.

Where the ticket's hand trace and the run disagree the test follows the run and says so in a comment (none of the row verdicts changed; the
only differences are the table facts of Unicode 15.1.0 named next to the rows that use them).
"""

import collections
import html
import inspect
import re
import unicodedata

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import _confusables, textnorm
from hadavin_sdk.guard.textnorm import (
    FoldNotConverged,
    NotText,
    TextTooLong,
    fold,
    has_hidden_channel,
    has_mixed_script,
    identity_key,
    key_tag,
    same_person,
    scan_keyset,
)

CAP = defaults.TEXTNORM_MAX_CHARS
ZE = chr(0x437)  # Cyrillic small Ze: reads as the digit 3 in the table
VAULT = "ltq-Vault-8812"  # a made-up value
BANK = "bank12345"


def tag(text):
    """``text`` written with tag characters (U+E0000 + the ASCII code)."""
    return "".join(chr(0xE0000 + ord(c)) for c in text)


def bare(key):
    """A key without the tag of an interpreter whose Unicode version is not the pin."""
    return key.removeprefix(key_tag())


def refused(exc, message, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc:
        return
    except Exception as other:  # noqa: BLE001 - reported with its class
        raise AssertionError(f"{message} (raised {type(other).__name__} instead)") from None
    raise AssertionError(message)


def shares(a, b):
    """``scan_keyset`` of the two texts share a key."""
    return bool(scan_keyset(a) & scan_keyset(b))


def high_bits(seed):
    """Integer arithmetic only; the generator takes the HIGH bits (``x >> 33``), never ``x % n`` of the raw state (ADV-R5-15)."""
    state = seed
    while True:
        state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        yield state >> 33


def draw(gen, n):
    return next(gen) % n


# ---- SK-1 to SK-6: the contract of scan_keyset ---------------------------------------------------------------------------------------------
def test_sk1_scan_keyset_has_exactly_one_parameter_named_raw():
    params = list(inspect.signature(scan_keyset).parameters)
    assert params == ["raw"], (
        f"scan_keyset has parameters {params}: a clock or a deadline was added"
    )


def test_sk2_at_most_eight_keys_none_longer_than_the_weight_and_the_input_rules_hold():
    hostile = [
        "\u0397" * 40,
        ZE * 40,
        "al" + tag("x") + "ice",
        "hello" + tag("bank 12345") + "\u0397\u03b7\u0397\u03b7",
        "\u03a3" * 20 + tag("sigma"),
        "\u0130\u03f4\ufdfa\u1e9e",
        "",
        "!!",
    ]
    gen = high_bits(7)
    for _ in range(600):
        hostile.append("".join(chr(draw(gen, 0x2FFF) + 0x20) for _ in range(draw(gen, 12))))
    assert len(hostile) >= 500
    for text in hostile:
        keys = scan_keyset(text)
        assert len(keys) <= 8, f"scan_keyset made {len(keys)} keys for {text!r}"
        weight = textnorm._weight(text)
        assert all(len(k) <= weight for k in keys), f"a key is longer than the weight of {text!r}"
    over = "a" * (CAP + 1)
    refused(TextTooLong, "scan_keyset accepted a text over the size rule", scan_keyset, over)
    assert scan_keyset("a" * CAP) == {"a" * CAP}, "the text at the size rule is refused"
    refused(NotText, "scan_keyset accepted bytes", scan_keyset, b"x")
    refused(NotText, "scan_keyset accepted an int", scan_keyset, 1)

    class Member(str):
        pass

    refused(NotText, "scan_keyset accepted a str subclass", scan_keyset, Member("x"))


def test_sk2_the_key_count_over_every_code_point_is_at_most_eight():
    worst = 0
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        n = len(scan_keyset(chr(cp)))
        worst = max(worst, n)
        assert n <= 8, f"U+{cp:04X} made {n} keys"
    print(f"most keys of one code point: {worst}")


def test_sk3_the_az3x9_rows_ze_reads_as_three_and_z():
    texts = ["az3x9", "a" + ZE + ZE + "x9", "azzx9", "a33x9", "a3zx9", "a" + ZE + "zx9"]
    for t in texts:
        assert "a33x9" in scan_keyset(t), f"{t!r}: no key a33x9 (the class map z to 3 is missing)"
    for a, b in ((ZE, "3"), (ZE, "z"), ("3", "z")):
        assert same_person(a, b), f"same_person({a!r}, {b!r}) is False"


def test_sk6_hash_tilde_at_pipe_and_the_replacement_character_are_dropped():
    assert scan_keyset("a" + chr(0xFFFD) + "b") == {"ab"}
    assert scan_keyset("a#b") == {"ab"}
    assert scan_keyset("a~b@c|d") == {"abcd"}
    assert bare(identity_key("a" + chr(0xFFFD) + "b")) == "ab", "U+FFFD is kept by the fold"


def test_invisible_only_text_has_an_empty_key_set_and_the_bits_pin():
    assert scan_keyset("") == frozenset()
    assert scan_keyset("\u200b\u200c\u2060\ufeff") == frozenset()
    bits = "".join(
        "\u200c" if b == "1" else "\u200b"
        for b in format(int.from_bytes(VAULT.encode(), "big"), "b")
    )
    assert scan_keyset(bits) == frozenset(), (
        "a value written as bits in two zero-width characters has a key"
    )


def test_the_scan_keys_hold_letters_and_digits_only():
    for text in (
        "a b-c_d.e",
        "ba" + "\u200b" + "nk",
        "x" + tag("y z"),
        "\u03a9\u2248\u00e7\u221a\u222b",
        "a\tb\nc",
    ):
        for key in scan_keyset(text):
            assert all(c.isalnum() and unicodedata.category(c) != "Lm" for c in key), (text, key)


# ---- the tag texts T0 to T3 ----------------------------------------------------------------------------------------------------------
def test_tag_t0_the_text_without_its_tag_characters():
    assert "aiice" in scan_keyset("al" + tag("x") + "ice"), (
        "T0 (the text without its tag characters) is not a key"
    )
    assert {"aiicex", "aixice", "x"} <= scan_keyset("al" + tag("x") + "ice")


def test_tag_t1_the_tag_characters_decoded_in_place():
    keys = scan_keyset("ba" + tag("n") + "k12345")
    assert BANK in keys, "T1 (the tag characters decoded in place) is not a key"
    assert {"bak12345", "bak12345n", "n"} <= keys


def test_tag_t2_the_text_followed_by_the_decoded_tag_characters():
    keys = scan_keyset(tag("12345") + "bank")
    assert BANK in keys, "T2 (the text followed by the decoded tag characters) is not a key"
    assert {"bank", "12345bank", "12345"} <= keys


def test_tag_t3_the_decoded_tag_characters_alone():
    keys = scan_keyset("hello" + tag("bank 12345"))
    assert BANK in keys, "T3 (the decoded tag characters alone) is not a key"


def test_a_tag_text_still_returns_its_keys_and_the_signal_is_a_separate_function():
    text = "alice" + tag("x")
    assert scan_keyset(text), "a text with a tag character has no keys"
    assert has_hidden_channel(text) is True
    assert has_hidden_channel(tag("approved")) is True
    assert same_person("alice" + tag("x"), "alice")
    assert bare(identity_key(tag("approved"))) == "", "identity_key reads the tag letters"


# ---- the readings: Eta, Nu, Upsilon, palochka, Sigma ---------------------------------------------------------------------------------------
def test_capital_and_small_eta_read_h_and_n_in_both_directions_and_both_readings():
    assert scan_keyset("\u0397\u03b7\u0397\u03b7") == {"hnhn", "nnnn"}, (
        "reading B is missing: capital Eta pair has not both keys"
    )
    assert same_person("\u0397\u03b7\u0397\u03b7", "hnhn")
    assert same_person("\u0397\u03b7\u0397\u03b7", "nnnn"), (
        "reading B is missing: no match with nnnn"
    )
    assert same_person("hnhn", "\u0397\u03b7\u0397\u03b7") and same_person(
        "nnnn", "\u0397\u03b7\u0397\u03b7"
    )
    assert scan_keyset("\u0397") == {"h", "n"}, (
        "capital Eta must read H (reading A) and n (reading B)"
    )
    assert scan_keyset("\u03b7") == {"n"}


def test_capital_eta_pair_does_not_match_hn_the_pinned_limit():
    assert not same_person("\u0397\u0397", "hn"), (
        "the pinned limit (each reading is one letter) changed"
    )
    assert same_person("\u0397\u0397", "hh") and same_person("\u0397\u0397", "nn")


def test_nu_upsilon_palochka_and_sigma_read_by_both_readings():
    assert scan_keyset("\u039d") == {"n", "v"} and scan_keyset("\u03bd") == {"v"}, (
        "capital and small Nu"
    )
    assert scan_keyset("\u03a5") == {"u", "y"} and scan_keyset("\u03c5") == {"u"}, (
        "capital and small Upsilon"
    )
    assert (
        same_person("\u039d\u03bd", "nv")
        and same_person("\u039d\u039d", "nn")
        and not same_person("\u039d\u039d", "nv")
    )
    assert scan_keyset("\u04c0") == {"i"} and scan_keyset("\u04cf") == {"i"}, (
        "capital and small palochka read i (l to i)"
    )
    assert (
        shares("a\u04c0\u04c0ow", "allow")
        and shares("pay\u04cf", "payl")
        and shares("pay\u04cf", "payi")
    )
    for ch in ("\u03a3", "\u03c3", "\u03c2"):
        assert scan_keyset(ch) == {"o"}, f"Sigma form U+{ord(ch):04X}"


def test_identity_key_of_each_row_equals_the_case_fold_first_reading():
    """The ticket says reading A; the built identity path is the casefold-first order (fold4 keeps the P1a idempotent order), which the
    scan keys call reading B. Eta, Nu, Upsilon, palochka and Sigma all agree with it."""
    for ch in (
        "\u0397",
        "\u03b7",
        "\u039d",
        "\u03bd",
        "\u03a5",
        "\u03c5",
        "\u03a3",
        "\u03c3",
        "\u04c0",
        "\u04cf",
    ):
        assert bare(identity_key(ch)) == textnorm._converge(ch, textnorm._pass_b), (
            f"U+{ord(ch):04X}"
        )
    assert bare(identity_key("\u0397")) == "n" and bare(identity_key("\u03b7")) == "n"


def test_sigma_needs_two_changing_passes_and_the_bound_is_exact():
    sigma = "\u03a3"
    assert scan_keyset(sigma), "capital Sigma has no key at the default bound"
    original = defaults.TEXTNORM_MAX_PASSES
    try:
        defaults.TEXTNORM_MAX_PASSES = 3
        assert scan_keyset(sigma)
        defaults.TEXTNORM_MAX_PASSES = 2
        refused(
            FoldNotConverged,
            "capital Sigma at 2 passes did not raise FoldNotConverged",
            scan_keyset,
            sigma,
        )
    finally:
        defaults.TEXTNORM_MAX_PASSES = original
    assert issubclass(FoldNotConverged, textnorm.TextnormError)


def test_fuzz_the_readings_converge_and_the_maximum_of_changing_passes_is_recorded():
    """BN-10: record the maximum number of changing passes over every code point and a seeded fuzz; FoldNotConverged is never expected."""
    most = {"A": 0, "B": 0}
    steps = {"A": textnorm._pass_a, "B": textnorm._pass_b}

    def changing(text, step):
        n = 0
        while True:
            out = step(text)
            if out == text:
                return n
            text = out
            n += 1
            assert n <= 2, f"{text!r} needs a third changing pass"

    samples = [chr(cp) for cp in range(0x110000) if not 0xD800 <= cp <= 0xDFFF]
    gen = high_bits(11)
    alphabet = [c for c in samples if ord(c) < 0x3000 or ord(c) >= 0x1D400]
    for _ in range(20000):
        samples.append("".join(alphabet[draw(gen, len(alphabet))] for _ in range(1 + draw(gen, 6))))
    for text in samples:
        for name, step in steps.items():
            most[name] = max(most[name], changing(text, step))
        scan_keyset(text)  # FoldNotConverged would raise here
    print(
        f"maximum changing passes: reading A {most['A']}, reading B {most['B']} (bound {defaults.TEXTNORM_MAX_PASSES})"
    )
    assert most["A"] <= 2 and most["B"] <= 2
    assert max(most.values()) + 1 <= defaults.TEXTNORM_MAX_PASSES, "no room for the confirming pass"


# ---- gap 2, gap 4, U+FFFD -----------------------------------------------------------------------------------------------------------------
def test_gap2_an_unassigned_table_source_is_read_before_the_drop(monkeypatch):
    cn = 0x113D4  # unassigned at Unicode 15.1.0 (assigned in a later version)
    if unicodedata.category(chr(cn)) != "Cn":
        pytest.skip("U+113D4 is assigned on this interpreter")
    assert fold("p" + chr(cn) + "yp") == "pyp", "an unassigned code point is not dropped"
    table = dict(textnorm._TABLE)
    table[cn] = "l"
    cf = dict(textnorm._CF_TABLE)
    cf[cn] = "l"
    monkeypatch.setattr(textnorm, "_TABLE", str.maketrans(table))
    monkeypatch.setattr(textnorm, "_CF_TABLE", str.maketrans(cf))
    monkeypatch.setattr(textnorm, "_TABLE_SOURCES", frozenset(textnorm._TABLE_SOURCES | {cn}))
    assert fold("p" + chr(cn) + "yp") == "plyp", (
        "a Cn table source is dropped before the table is read (gap 2)"
    )
    # only Cn: every other dropped category is dropped first, so a mark never changes the key
    assert fold("p" + chr(0x301) + "yp") == "pyp"
    assert fold("p" + chr(0xE000) + "yp") == "pyp"


def test_gap2_no_table_source_of_the_live_table_is_in_a_dropped_category_but_cn():
    dropped = textnorm._DROP_CATEGORIES - {"Cn"}
    bad = [hex(cp) for cp in _confusables.TABLE if unicodedata.category(chr(cp)) in dropped]
    assert not bad, f"table sources in a dropped category: {bad}"


GAP4 = [
    ("a\u2010b", "a-b"),
    ("a\u2013b", "a-b"),
    ("a\u2014b", "a-b"),
    ("a\u2212b", "a-b"),
    ("a\u2044b", "a/b"),
    ("a\u2215b", "a/b"),
    ("a\u29f8b", "a/b"),
    ("a\uff0fb", "a/b"),
    ("a\u2571b", "a/b"),
    ("a\u2018b", "a'b"),
    ("a\u2019b", "a'b"),
    ("a\u201bb", "a'b"),
    ("a\u201cb", 'a"b'),
    ("a\u201db", 'a"b'),
    ("a\u201fb", 'a"b'),
]


def test_gap4_dashes_slashes_and_quotes_read_as_ascii_in_identity_key():
    for raw, want in GAP4:
        assert bare(identity_key(raw)) == want, (
            f"gap 4 map: U+{ord(raw[1]):04X} does not read as {want!r}"
        )


def test_gap4_every_pd_dash_reads_as_the_hyphen_minus():
    dashes = [
        chr(cp)
        for cp in range(0x110000)
        if not 0xD800 <= cp <= 0xDFFF and unicodedata.category(chr(cp)) == "Pd"
    ]
    assert dashes, "the interpreter lists no Pd dash"
    for d in dashes:
        # NFKC may turn a dash into another character first; the key must equal the hyphen-minus key of the same text
        assert bare(identity_key("a" + d + "b")) == "a-b" or identity_key(
            "a" + d + "b"
        ) == identity_key("a" + unicodedata.normalize("NFKC", d) + "b"), hex(ord(d))


def test_gap5_hidden_separators_are_dropped_and_the_scan_key_has_no_spaces():
    assert shares("bank 12345", "ba\u200bnk\u200b12345"), "a hidden separator splits the value"
    for t in ("ba nk12345", "b a n k 1 2 3 4 5", "bank12345"):
        assert shares("bank 12345", t), f"the scan key keeps whitespace: {t!r}"
    assert scan_keyset("\u200b\u200b") == frozenset()
    assert scan_keyset("a\x00b") == {"ab"}
    assert scan_keyset("ja\u200bvascript") == {"javascript"}


# ---- Ze, l to i, punctuation ---------------------------------------------------------------------------------------------------------------
def test_l_to_i_rows():
    assert shares("a" + chr(0x406) * 2 + "ow-this-value", "allow-this-value"), (
        "row 1: the class map l to i is missing"
    )
    assert scan_keyset("a" + chr(0x406) * 2 + "ow-this-value") == {"aiiowthisvaiue"}, (
        "row 1: the key holds a character that is not a letter or a digit"
    )
    assert shares(chr(0x399) + "l", "il"), "row 2"
    assert shares("aIIow", "allow"), "row 3"
    assert scan_keyset("ops" + chr(0x701) + "manager@example.test") == scan_keyset(
        "ops.manager@example.test"
    ), "row 4: U+0701 is kept in the key (punctuation is not dropped)"
    assert scan_keyset("Anna_Schmidt") == scan_keyset("Anna Schmidt"), (
        "row 5: an underscore is kept in the key"
    )
    assert shares("ref" + chr(0xA789) + "2026", "ref:2026"), "row 6"


def test_the_over_match_rows_and_the_pinned_non_matches():
    assert identity_key("\u304b") == identity_key("\u304c"), "ka and ga differ under identity_key"
    assert shares("Anna Maria", "Ann Amaria")
    assert shares("Li Na", "Lina")
    for text in (
        "tomark us",
        "market",
    ):  # substring use: the key of the needle is inside a key of the text
        assert any("mark" in k for k in scan_keyset(text)), text
    # the pinned limit: U+0138 has no table entry, so it is not folded
    assert not shares("kra" + chr(0x138) + "key", "krakkey"), (
        "U+0138 is folded now: update the limit"
    )
    assert not shares("&#65;BC", "ABC") and not shares("&#49;2345", "12345")
    assert scan_keyset("&#65;BC") == {"65bc"} and scan_keyset("&#49;2345") == {"492345"}


@pytest.mark.parametrize(
    "escaped",
    ["&#97;bcdef12", "\\u0061bcdef12", "%61bcdef12", "\\x61bcdef12"],
    ids=["html", "json", "percent", "backslash-x"],
)
def test_an_escaped_letter_is_not_decoded_by_any_key(escaped):
    assert not shares(escaped, "abcdef12"), "an escape was decoded"
    assert not any("abcdef12" in k for k in scan_keyset(escaped)), "a key holds the decoded value"


def test_nb_entity_rows_the_text_reads_as_written():
    assert shares("&LTQ-VAULT-8812", "ltq-Vault-8812"), "NB-1"
    assert any(
        k2 in k1
        for k1 in scan_keyset("R&ltq-vault-8812 ok")
        for k2 in scan_keyset("ltq-Vault-8812")
    ), "NB-2"
    assert (
        html.unescape("&LTQ-VAULT-8812") == "<Q-VAULT-8812"
    )  # why the entity step would have lost it


# ---- the digit-valued look-alikes ----------------------------------------------------------------------------------------------------------
DIGIT_CLASS_DECISIONS = {
    "2": "kept: the source imitates the digit; leetspeak is not a look-alike class",
    "3": "class-mapped: z to 3 in scan_keyset (Cyrillic Ze reads as both)",
    "4": "kept: the source imitates the digit; leetspeak is not a look-alike class",
    "5": "kept: the source imitates the digit; leetspeak is not a look-alike class",
    "6": "kept: the source imitates the digit; leetspeak is not a look-alike class",
    "7": "kept: the source imitates the digit; leetspeak is not a look-alike class",
    "8": "kept: the source imitates the digit; leetspeak is not a look-alike class",
    "9": "kept: the source imitates the digit; leetspeak is not a look-alike class",
}
# one source per digit value (read from the Unicode 15.1.0 table; the ticket's U+1C84 for 7 has no entry there, U+104D2 Osage ZA has)
DIGIT_SOURCES = {2: 0x1A7, 3: 0x1B7, 4: 0x13CE, 5: 0x1BC, 6: 0x431, 7: 0x104D2, 8: 0x222, 9: 0x2CCA}
DIGIT_LETTER = {
    2: "s",
    4: "y",
    5: "s",
    6: "b",
    7: "z",
    8: "o",
    9: "g",
}  # an ASCII letter the source resembles


def test_digit_valued_look_alikes_have_one_decision_per_value_and_no_source_is_a_modifier_letter():
    values = {
        v
        for cp, v in _confusables.TABLE.items()
        if v.isascii() and v.isdigit() and unicodedata.category(chr(cp)) != "Nd"
    }
    assert values == set(DIGIT_CLASS_DECISIONS), (
        f"the table has digit values without a decision or a decision without a value: {sorted(values ^ set(DIGIT_CLASS_DECISIONS))}"
    )
    lm = [hex(cp) for cp in _confusables.TABLE if unicodedata.category(chr(cp)) == "Lm"]
    assert not lm, f"table sources of category Lm (dead under the Lm removal): {lm}"
    assert textnorm._CLASS_MAP[ord("z")] == ord("3"), "value 3 is class-mapped (z to 3)"


@pytest.mark.parametrize("digit", sorted(DIGIT_SOURCES))
def test_pin_found_a_digit_written_by_one_look_alike_is_the_digit(digit):
    src = chr(DIGIT_SOURCES[digit])
    assert _confusables.TABLE[DIGIT_SOURCES[digit]] == str(digit), (
        f"U+{DIGIT_SOURCES[digit]:04X} is not a source of {digit}"
    )
    assert same_person("ab" + src + "cd", "ab" + str(digit) + "cd"), (
        f"digit {digit} is not found through U+{DIGIT_SOURCES[digit]:04X}"
    )


# U+01BC (capital tone five) also reads s through reading B: its case-fold partner U+01BD is a table source for s (a known case-fold conflict).
# So the not-matched row for value 5 uses the Warang Citi capital Horr, which has no such partner.
NOT_MATCHED_SOURCES = {**DIGIT_SOURCES, 5: 0x118BB}


def test_a_case_fold_partner_can_read_a_letter_the_capital_does_not():
    assert shares(chr(0x1BC), "s") and shares(chr(0x1BC), "5"), (
        "U+01BC reads s and 5 (the pinned conflict)"
    )


@pytest.mark.parametrize("digit", sorted(DIGIT_LETTER))
def test_pin_not_matched_the_letter_a_digit_look_alike_resembles_is_not_the_source(digit):
    src = chr(NOT_MATCHED_SOURCES[digit])
    letter = DIGIT_LETTER[digit]
    assert not shares("qq" + src + "qq", "qq" + letter + "qq"), (
        f"leetspeak class: U+{NOT_MATCHED_SOURCES[digit]:04X} matches the letter {letter!r}"
    )


# ---- the order 11 table: V and its disguises -----------------------------------------------------------------------------------------------
def _lookalike(script, ch, lower_only=True):
    """The table source of the live table that reads ``ch`` and whose name starts with ``script`` (smallest code point; lower case first)."""
    best = None
    for cp, v in _confusables.TABLE.items():
        if (
            v == ch
            and unicodedata.name(chr(cp), "").startswith(script)
            and (best is None or (chr(cp).islower(), -cp) > (chr(best).islower(), -best))
        ):
            best = cp
    return None if best is None else chr(best)


def _disguise(value, script):
    out = []
    for c in value:
        sub = _lookalike(script, c) if c.isalpha() else None
        out.append(sub or c)
    return "".join(out)


def test_r11_cyr_greek_fw_zw_mark_split_up_low_the_value_shares_a_key_with_its_disguises():
    cyr = (
        chr(0x4CF) + chr(0x442) + chr(0x51B) + "-V" + chr(0x430) + "u" + "l" + chr(0x442) + "-8812"
    )
    assert shares(cyr, VAULT), "R11-CYR"
    grk = VAULT.replace("a", chr(0x3B1)).replace("u", chr(0x3C5)).replace("t", chr(0x3C4))
    assert shares(grk, VAULT), "R11-GRK"
    fw = "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in VAULT)
    assert shares(fw, VAULT), "R11-FW"
    assert shares("ba\u200bnk\u200b12345", BANK), "R11-ZW"
    assert shares(VAULT[:3] + "\u0301" + VAULT[3:], VAULT), "R11-MARK"
    assert shares(VAULT[:7] + "\n" + VAULT[7:], VAULT), "R11-SPLIT"
    assert shares(VAULT.upper(), VAULT), "R11-UP"
    assert shares(VAULT.lower(), VAULT), "R11-LOW"
    assert _disguise(VAULT, "CYRILLIC") != VAULT and shares(_disguise(VAULT, "CYRILLIC"), VAULT)
    assert _disguise(VAULT, "GREEK") != VAULT and shares(_disguise(VAULT, "GREEK"), VAULT)


def test_no_value_of_the_table_is_zero_or_one():
    assert not [v for v in _confusables.TABLE.values() if v in ("0", "1")], (
        "the table maps a letter to 0 or 1"
    )


# ---- modifier letters (Lm) -----------------------------------------------------------------------------------------------------------------
def test_r12_lm_inserting_any_modifier_letter_still_finds_the_value():
    value = "bank12345-vault"
    lms = [
        chr(cp)
        for cp in range(0x110000)
        if not 0xD800 <= cp <= 0xDFFF and unicodedata.category(chr(cp)) == "Lm"
    ]
    print(f"modifier letters (Lm): {len(lms)}")
    assert lms, "the interpreter lists no Lm"
    for c in lms:
        assert shares(value[:2] + c + value[2:], value), f"U+{ord(c):04X} hides the value"
    assert bare(identity_key("ba" + chr(0x640) + "nk")) == "ba" + chr(0x640) + "nk", (
        "identity_key dropped U+0640"
    )
    assert identity_key("ba" + chr(0x640) + "nk") != identity_key("bank")


def test_r12_lm_fold_a_modifier_letter_that_nfkd_turns_into_a_letter_still_matches():
    w = "ab" + chr(0x2BC) + "ncd-12345-xyz"
    assert shares("ab" + chr(0x149) + "cd-12345-xyz", w), (
        "a modifier letter made by NFKD survives in the key"
    )


def test_r13_lm_mix_the_substitution_and_the_stated_limit():
    undo = lambda t: unicodedata.normalize("NFKC", t)
    one = "ba" + chr(0x2B0) + "nk12345"
    assert BANK in scan_keyset(one), "(1) an inserted modifier letter hides the value"
    two = "b" + chr(0x1D43) + "nk12345"
    assert BANK not in scan_keyset(two), (
        "(2) the t view alone must not find a substituted modifier letter"
    )
    assert BANK in scan_keyset(undo(two)), (
        "(2) the undo view finds it (NFKC reads the modifier letter as a)"
    )
    three = "b" + chr(0x1D43) + "n" + chr(0x2B0) + "k12345"
    assert BANK not in scan_keyset(three) and BANK not in scan_keyset(undo(three)), (
        "(3) a pinned limit changed"
    )
    assert scan_keyset(three) == {"bnk12345"} and scan_keyset(undo(three)) == {"banhk12345"}


def test_pin_encl_enclosed_forms_without_a_decomposition_or_table_entry_give_no_ascii_key():
    names = re.compile(
        r"CIRCLED|SQUARED|PARENTHESIZED|REGIONAL INDICATOR|DINGBAT|NEGATIVE|FULL STOP|COMMA|ENCLOSED"
    )
    one = re.compile(
        r"LETTER [A-Z]\b|DIGIT|NUMBER|\b(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|"
        r"FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN|NINETEEN|TWENTY)\b|\b[0-9]{1,2}\b"
    )
    selected = []
    for cp in range(0x80, 0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        name = unicodedata.name(ch, "")
        if (
            not name
            or unicodedata.category(ch)[0] not in "SNL"
            or not names.search(name)
            or not one.search(name)
        ):
            continue
        if (
            unicodedata.decomposition(ch)
            and "<" in unicodedata.decomposition(ch)
            or unicodedata.normalize("NFKD", ch) != ch
        ):
            continue
        if cp in _confusables.TABLE:
            continue
        selected.append(ch)
        for key in scan_keyset(ch):
            assert not any(c.isascii() and c.isalnum() for c in key), (
                f"U+{cp:04X} gives the ASCII key {key!r}"
            )
    print(f"enclosed forms selected: {len(selected)}; runs: 8 (2 readings x 4 tag texts)")
    if unicodedata.unidata_version == defaults.TEXTNORM_PINNED_UNIDATA:
        assert len(selected) >= 100, (
            f"the name selection chose {len(selected)} code points (the ticket's count is 135)"
        )
    assert selected, "the selection is empty: a regex that matches nothing passes"


# ---- the properties -----------------------------------------------------------------------------------------------------------------------
LEGACY_ENTITIES = sorted(k for k in html.entities.html5 if not k.endswith(";"))
CONTEXT = (
    list("abcxyz019 &#;%-_\n")
    + ["&" + n for n in LEGACY_ENTITIES[:40]]
    + ["&#", "&#x", ZE, "\u200b", "\u0301", "\u00ad", "\u2060", "\ufe0f"]
)


def _variant(value, kind, gen):
    if kind == 0:
        return _disguise(value, "CYRILLIC")
    if kind == 1:
        return _disguise(value, "GREEK")
    if kind == 2:
        return "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in value)
    if kind == 3:
        out = []
        for c in value:
            out.append(c)
            if draw(gen, 4) == 0:
                out.append("\u200b\u200c\u200d\u2060\u00ad"[draw(gen, 5)])
        return "".join(out)
    if kind == 4:
        i = draw(gen, len(value))
        while not value[i].isalpha():
            i = (i + 1) % len(value)
        return value[: i + 1] + "\u0301" + value[i + 1 :]
    if kind == 5:
        i = 1 + draw(gen, len(value) - 1)
        return value[:i] + "\n" + value[i:]
    if kind == 6:
        return value.upper()
    return value.lower()


def test_every_disguise_of_a_value_found_inside_any_context_property():
    gen = high_bits(2026)
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789-"
    per_kind = collections.Counter()
    cases = 0
    for n in range(2400):
        kind = n % 8
        value = "a" + "".join(alphabet[draw(gen, len(alphabet))] for _ in range(11 + draw(gen, 29)))
        c1 = "".join(CONTEXT[draw(gen, len(CONTEXT))] for _ in range(draw(gen, 5)))
        c2 = "".join(CONTEXT[draw(gen, len(CONTEXT))] for _ in range(draw(gen, 5)))
        variant = _variant(value, kind, gen)
        text = c1 + variant + c2
        keys = scan_keyset(value)
        assert any(k in t for k in keys for t in scan_keyset(text)), (
            f"class {kind}: {value!r} lost in {text!r}"
        )
        per_kind[kind] += 1
        cases += 1
    assert cases >= 2000 and all(v >= 200 for v in per_kind.values()), per_kind


def test_mixed_reading_texts_match_the_needle():
    gen = high_bits(99)
    chars = "abcdefghijklmnopqrstuvwxyz0123456789zl3i -_"
    cases = 0
    for _ in range(2200):
        needle = "q" + "".join(chars[draw(gen, len(chars))] for _ in range(3 + draw(gen, 12)))
        parts = []
        for c in needle:
            pick = draw(gen, 5)
            if pick == 1 and c in "z3":
                parts.append(ZE)
            elif pick == 2:
                parts.append(c + "\u200b")
            elif pick == 3:
                parts.append(" " + c)
            elif pick == 4 and c.isascii() and c not in " ":
                parts.append(tag(c))
            else:
                parts.append(c)
        text = "".join(parts)
        if not any(c.isalnum() for c in needle):
            continue
        assert shares(needle, text), f"{needle!r} not found in {text!r}"
        cases += 1
    assert cases >= 2000


def test_same_person_the_identity_half_and_the_empty_key_sets():
    assert same_person("!!", "!!"), "the identity half of same_person is missing"
    assert not same_person("!!", "??"), "both empty key-sets count as a match"


def test_same_person_properties():
    assert same_person("alice", "alice") and same_person("", "") and same_person("\u200b", "\u200b")
    assert same_person("alice", "al\u200bice") and same_person("Alice", "\u0410lice")
    assert not same_person("\u0397\u0397", "hn")
    assert (
        same_person("\u0397", "h") and same_person("\u0397", "n") and not same_person("h", "n")
    ), "not transitive"
    gen = high_bits(5)
    texts = ["".join(chr(draw(gen, 0x2000)) for _ in range(draw(gen, 6))) for _ in range(800)]
    for t in texts:
        assert same_person(t, t), repr(t)
    for a, b in zip(texts[::2], texts[1::2], strict=False):
        if identity_key(a) == identity_key(b):
            assert same_person(a, b), (a, b)
        assert same_person(a, b) == same_person(b, a)


def test_the_scan_match_of_two_empty_key_sets_is_false_and_x_x_is_true_when_x_has_keys():
    assert textnorm._scan_match("!!", "??") is False, "two empty key-sets match"
    assert textnorm._scan_match("", "") is False, "two empty key-sets match"
    for x in ("alice", "\u0397", "z", ZE + "x", tag("abc")):
        assert textnorm._scan_match(x, x), repr(x)


def test_the_old_identity_groups_stay_together_for_the_deny_comparison():
    """Every code point that shares an ``identity_key`` with another is ``same_person`` with it (never narrower than the key)."""
    groups = collections.defaultdict(list)
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        groups[identity_key(chr(cp))].append(chr(cp))
    checked = 0
    for members in groups.values():
        for other in members[1:]:
            assert same_person(members[0], other), f"U+{ord(members[0]):04X} and U+{ord(other):04X}"
            checked += 1
    assert checked > 1000


# ---- has_mixed_script: every script of the data, except Common, Inherited and the East Asian ones ------------------------------------------
def test_runic_and_tamil_next_to_latin_are_flagged_and_single_script_text_is_not():
    runic, tamil = chr(0x16A0), chr(0x0B85)
    assert has_mixed_script("pay" + runic + "pal"), "Runic next to Latin is not flagged"
    assert has_mixed_script("pay" + tamil + "pal"), "Tamil next to Latin is not flagged"
    assert not has_mixed_script(runic * 4) and not has_mixed_script(tamil * 4 + " " + tamil)
    assert not has_mixed_script("ABC" + chr(0x4E2D) + chr(0x6587)), "Han next to Latin is flagged"
    assert not has_mixed_script("abc" + chr(0x3042) + chr(0x30A2) + chr(0xAC00)), (
        "Kana or Hangul next to Latin is flagged"
    )
    assert not has_mixed_script("version 2.1 \u2013 final"), "common characters are flagged"


def test_every_script_of_the_data_next_to_latin_is_flagged_except_the_east_asian_ones():
    from hadavin_sdk.guard import _scripts

    exempt = textnorm._EXEMPT_WITH_LATIN
    per_script = {}
    for lo, hi, index in _scripts.RANGES:
        per_script.setdefault(_scripts.SCRIPT_NAMES[index], []).append((lo, hi))
    flagged, skipped = 0, []
    for name, spans in per_script.items():
        if name in ("Latin", "Common", "Inherited"):
            continue
        letter = next(
            (chr(c) for lo, hi in spans for c in range(lo, hi + 1) if chr(c).isalpha()), None
        )
        if letter is None:
            skipped.append(name)
            continue
        got = has_mixed_script("pay" + letter + "pal")
        assert got is (name not in exempt), f"{name}: flagged={got}"
        flagged += name not in exempt
    print(f"scripts flagged: {flagged}; scripts without a letter: {len(skipped)}")
    assert flagged > 100


# ---- BN-17: a caller that never called require_pinned_unidata() on another Unicode version -----------------------------------------------
def test_on_another_unicode_version_identity_keys_are_tagged_and_scan_keys_are_not(monkeypatch):
    pinned_key = identity_key("bob")
    pinned_scan = scan_keyset("bob" + ZE)
    monkeypatch.setattr(unicodedata, "unidata_version", "9.9.9")
    tagged = identity_key("bob")
    assert (
        tagged != pinned_key
        and tagged.startswith("alg=")
        and "ud=9.9.9" in tagged
        and tagged.endswith("bob")
    ), "a key made on another Unicode version carries no tag"
    assert identity_key(tagged) == tagged, "the own tag is not stripped: the key is not idempotent"
    assert identity_key(key_tag() + "bob") == tagged, (
        "a raw text that starts with the own tag keeps it in the key"
    )
    assert scan_keyset("bob" + ZE) == pinned_scan, (
        "a scan key carries a tag (they are compared at once, never stored)"
    )
    assert same_person("bob", "b" + chr(0x43E) + "b"), (
        "same_person is unusable on another Unicode version"
    )
    assert not same_person("bob", "bobby")
