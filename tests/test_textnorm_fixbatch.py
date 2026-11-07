"""P1b fix batch: the pins added after the review of the first batch (a composed view in the redactor, the Mc and Sk scan keys, the minimums of ``scan_holds``,
the script values that are not ``EmptyView``, the cache, the one required value of ``scan_views``, the floor of the minimums, the
one-inserted-letter match and the records of the Unicode-dependent tables).

Look-alikes and scripts are built with ``chr()``. No wall-clock assertion here (the timing rows are in ``tests/test_textnorm_perf.py``);
a work bound is counted in calls. Every test names, in its docstring, the mutant of ``tests/textnorm_mutants.py`` that it is there to kill.
"""

import ast
import hashlib
import inspect
import itertools
import unicodedata
from pathlib import Path

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap, textnorm
from hadavin_sdk.guard.textnorm import (
    EmptyView,
    TextnormError,
    ViewTooShort,
    could_be_same_person,
    fold_views,
    scan_holds,
    scan_keyset,
    scan_needles,
    scan_views,
    value_scripts,
)

SRC = Path(textnorm.__file__).resolve().parents[1]


def refused(exc, message, fn, *args, **kwargs):
    """``fn`` raises ``exc``; otherwise the failure line is ``message`` (so a mutant's verdict names the guard, not a library text)."""
    try:
        fn(*args, **kwargs)
    except exc:
        return
    except Exception as other:  # noqa: BLE001 - reported with its class
        raise AssertionError(f"{message} (raised {type(other).__name__} instead)") from None
    raise AssertionError(message)


def han(n, start=0x5000):
    """``n`` distinct Han ideographs that no table reads."""
    return "".join(chr(start + 13 * i) for i in range(n))


def hangul(n):
    return "".join(chr(0xAC00 + 29 * i) for i in range(n))


def thai(n):
    return "".join(chr(0x0E01 + i) for i in range(n))


def letters(pool):
    """A maker of ``n`` distinct letters out of ``pool`` (letters no table reads as a Latin look-alike)."""
    return lambda n: pool[:n]


# ---- the redactor finds a decomposed copy of a known value --------------------------------------------------------------------
def test_redact_text_masks_a_decomposed_copy_of_a_known_name():
    """B1. Killer: ``runmap_no_composed_view``. A name stored precomposed and written with combining marks (NFD) is masked. The per-character
    ``canonical`` view composes nothing, so only the composed view finds it."""
    name = "José García"
    nfd = unicodedata.normalize("NFD", name)
    assert nfd != name
    out = runmap.redact_text("hello " + nfd + " ok", {"<NAME_1>": name})
    assert nfd not in out and "Garc" not in out, "a decomposed copy of a known name is not masked"
    assert out == "hello <NAME_1> ok"


def test_redact_text_masks_a_decomposed_secret_after_an_invisible_character():
    """B1, second row: the invisible format character between the letter and its accent must not keep them apart. Killer:
    ``runmap_composed_keeps_cf``."""
    stored = "m\u00fcller-vault"
    text = "key " + unicodedata.normalize("NFD", stored).replace("\u00fc", "u\u200b\u0308") + " end"
    out = runmap.redact_text(text, {"<NAME_1>": stored})
    assert "vault" not in out, "an invisible character keeps the letter and its accent apart"


def test_the_composed_view_is_a_view_and_canonical_stays_per_character():
    """Killers: ``runmap_no_composed_view`` and ``runmap_canonical_composes``. ``canonical`` composes nothing (positions stay exact); ``composed``
    does; ``_views`` lists the composed form."""
    nfd = "e\u0301"
    assert runmap.canonical(nfd) == nfd
    assert runmap.composed(nfd) == "\u00e9"
    assert runmap.composed("plain ascii") == "plain ascii"
    assert "x \u00e9" in runmap._views("x " + nfd)


# ---- the scan keys drop Mc and Sk as well ---------------------------------------------------------------------------------------
def test_every_mc_and_sk_code_point_hides_nothing_from_the_scan_keys():
    """Killer: ``keys: only the modifier letters are dropped``. ``password`` is in some scan key of ``pass`` + mark + ``word`` for EVERY Mc and Sk code point."""
    checked = 0
    for cp in range(0x110000):
        ch = chr(cp)
        if unicodedata.category(ch) not in ("Mc", "Sk"):
            continue
        keys = scan_keyset("pass" + ch + "word")
        assert any("password" in key for key in keys), (
            f"U+{cp:04X} ({unicodedata.category(ch)}) hides the word from every scan key"
        )
        checked += 1
    assert checked > 200


def test_a_spacing_mark_written_instead_of_a_letter_is_still_read_by_the_scan_keys():
    """The union of the two readings (the text as it is, and without the marks): U+0C02 reads as ``o`` and is NOT dropped from the key that reads
    it. Killer: ``keys_only_the_dropped_reading``."""
    keys = scan_keyset("passwంrd")
    assert any("password" in key for key in keys), sorted(keys)
    assert any("passwrd" in key for key in keys), sorted(keys)


# ---- the minimums of the scan's needles ---------------------------------------------------------------------------
def test_a_digit_string_needs_the_digit_minimum_and_a_letter_string_the_squeeze_minimum():
    """Killer: ``digits: a digit view needs only the squeeze minimum``. The ticket (P1) asks for 6 digits: five are refused."""
    d = defaults.TEXTNORM_MIN_DIGIT_CHARS
    assert d > defaults.TEXTNORM_MIN_SQUEEZE_CHARS, (
        "the digit minimum is not above the squeeze minimum"
    )
    short, enough = "1234567"[: d - 1], "1234567"[:d]
    refused(
        ViewTooShort,
        "a digit string under the digit minimum is scanned",
        scan_holds,
        "any " + short + " text",
        short,
    )
    refused(
        ViewTooShort,
        "scan_needles takes a digit string under the digit minimum",
        scan_needles,
        short,
    )
    assert scan_holds("any " + enough + " text", enough), (
        "a digit string at the minimum is not found"
    )
    assert scan_holds("pin 1 2 3 4 5 6", enough), "an inserted space hides the digits"
    assert scan_holds("x ab12 y", "ab12"), "a view that holds a letter keeps the squeeze minimum"


def test_a_scan_key_shorter_than_its_minimum_is_not_a_needle():
    """Killer: ``scan: a scan key needs no minimum``. The class map z to 3 turns ``zz99`` into the key ``3399``: all digits, so the digit minimum applies
    to the KEY too. Four digits would be found in almost every table of numbers."""
    needles = [needle for _kind, needle in textnorm._value_needles("zz99")]
    assert all(len(n) >= defaults.TEXTNORM_MIN_SQUEEZE_CHARS for n in needles), (
        "a needle is under the squeeze minimum"
    )
    assert not any(n.isdigit() and len(n) < defaults.TEXTNORM_MIN_DIGIT_CHARS for n in needles), (
        "a key of digits is a needle under the digit minimum"
    )
    assert scan_holds("x 3399 y", "zz99") is False, "a short digit key is found in a text"


def test_the_decisions_are_in_the_module_docstring_and_li_na_is_not_lina():
    """Items 7 and 2: the digit decision (the ticket's 6, not the earlier 4) and the 'Li Na' reading are written where a reader looks. No mutant: a
    document pin."""
    doc = textnorm.__doc__
    assert "DIGITS" in doc and "ticket (P1) asked for 6 digits" in doc
    assert "Li Na" in inspect.getdoc(could_be_same_person)
    assert could_be_same_person("Li Na", "Lina") is False, "the docstring says DIFFERENT"
    assert could_be_same_person("Li Na", "li  na") is True


# ---- a value with no ASCII letter is scanned, not EmptyView ----------------------------------------------------------------------
SCRIPT_VALUES = (
    "\u4e2d\u6587",
    "\u5bc6\u7801\u4fdd\u62a4",
    "\u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631",
    "\u0e23\u0e2b\u0e31\u0e2a\u0e1c\u0e48\u0e32\u0e19",
    "\u092a\u093e\u0938\u0935\u0930\u094d\u0921",
)


def test_a_script_value_is_scanned_and_found_with_a_separator_inserted():
    """Killer: ``scan: a value with no squeeze view is EmptyView``. Chinese, Arabic, Thai and Hindi values are scanned (the ticket asks for the script views)."""
    for value in SCRIPT_VALUES:
        assert scan_holds("x " + value + " y", value) is True, (
            f"{value!r} is not found (or is refused)"
        )
        spaced = " ".join(value.replace(" ", ""))
        assert scan_holds("x " + spaced + " y", value) is True, f"an inserted space hides {value!r}"
        assert scan_holds("an unrelated english sentence", value) is False, (
            f"{value!r} is found in english"
        )


def test_a_value_with_nothing_to_rely_on_is_still_empty_view():
    """Killer: ``scan: EmptyView is never raised``. Empty, invisible, punctuation only and marks only stay EmptyView; a lone Devanagari vowel sign is a mark."""
    for value in ("", " ", "\u200b", "!!", "***", "\u093e", "\u0301"):
        refused(
            EmptyView,
            f"scan_holds does not refuse the empty value {value!r} with EmptyView",
            scan_holds,
            "any text",
            value,
        )


def test_a_one_ideograph_value_is_too_short_not_empty():
    """One ideograph has a script view, so the refusal is ViewTooShort, not EmptyView. Killer: ``scan: EmptyView for every short value``."""
    refused(ViewTooShort, "one ideograph is not ViewTooShort", scan_holds, "any text", "\u4e2d")
    try:
        scan_holds("any text", "\u4e2d")
    except EmptyView:
        raise AssertionError("one ideograph is EmptyView") from None
    except ViewTooShort:
        pass


# ---- the views of one text are built once for any number of values ---------------------------------------------------------------
def test_scanning_one_text_for_many_values_builds_the_text_views_once(monkeypatch):
    """Killer: ``scan: the views of a text are built again for every value``. 62 values against one text read the text with ``_readings`` no more often
    than the first value did."""
    clear = getattr(textnorm._text_bundle, "cache_clear", None)
    if clear:
        clear()
    text = (
        "a long log line with several words and a pass\u200bword inside " * 3
        + "\u5bc6\u7801\u4fdd\u62a4"
    )
    real = textnorm._readings
    seen = []

    def counting(raw, *args, **kwargs):
        seen.append(raw)
        return real(raw, *args, **kwargs)

    monkeypatch.setattr(textnorm, "_readings", counting)
    values = [f"secret-value-{i:03d}" for i in range(60)] + ["password", "\u5bc6\u7801\u4fdd\u62a4"]
    hits = [scan_holds(text, values[0])]
    once = seen.count(
        text
    )  # what ONE build of the views of the text costs (the squeeze views read it again with other options)
    assert once >= 1, "the text was never read: the counter is broken"
    hits += [scan_holds(text, v) for v in values[1:]]
    assert hits[-2:] == [True, True] and not any(hits[:60]), "the scan answers are wrong"
    assert seen.count(text) == once, (
        f"the text was read {seen.count(text)} times for {len(values)} values, {once} for the first"
    )


# ---- one choke point: the value decides the scripts ---------------------------------------------------------------------
def test_scan_views_has_no_default_for_the_value():
    """Killer: ``scan_views: the value has a default``."""
    refused(TypeError, "scan_views has a default for the value", scan_views, "text")
    sig = inspect.signature(scan_views)
    assert list(sig.parameters) == ["raw", "value"], "the parameters of scan_views changed"
    assert sig.parameters["value"].default is inspect.Parameter.empty, (
        "the value of scan_views has a default"
    )


def test_fold_views_has_no_default_for_the_scripts():
    """Killer: ``fold_views: the scripts have a default``."""
    refused(TypeError, "fold_views has a default for the scripts", fold_views, "text")
    fsig = inspect.signature(fold_views)
    assert fsig.parameters["scripts"].kind is inspect.Parameter.KEYWORD_ONLY, (
        "scripts is not keyword-only"
    )
    assert fsig.parameters["scripts"].default is inspect.Parameter.empty, (
        "the scripts of fold_views have a default"
    )


def test_no_caller_in_the_package_omits_the_value_or_the_scripts():
    """Every call of ``scan_views`` and ``fold_views`` in ``src`` passes the value / the scripts (found by reading the syntax trees). The callers
    today: ``guard/injection.py`` only (``scan_views(text, None)``: no protected value, said on purpose); ``fold_views`` is called by ``textnorm`` itself. Killer: ``injection:
    the call names no value``."""
    calls = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", getattr(node.func, "id", ""))
                if name in ("scan_views", "fold_views"):
                    calls.append((path.name, name, len(node.args), {k.arg for k in node.keywords}))
    assert calls, "no caller found: the search is broken"
    for file, name, nargs, kws in calls:
        if name == "scan_views":
            assert nargs >= 2 or "value" in kws, f"a call of scan_views in {file} names no value"
        else:
            assert "scripts" in kws, f"a call of fold_views in {file} names no scripts"
    assert {f for f, n, *_ in calls if n == "scan_views"} == {"injection.py"}, (
        "the callers of scan_views changed"
    )


def test_a_caller_that_names_only_the_value_cannot_miss_an_inserted_foreign_letter():
    """Killer: ``scan_views: the scripts of the value are not used``. The text holds a Chinese value with a Cyrillic letter inserted; the views given
    for that value hold the value, and the views given for no value do not."""
    value = "\u5bc6\u7801\u4fdd\u62a4"
    text = "\u5bc6\u7801\u0436\u4fdd\u62a4"
    assert value in scan_views(text, value), "scan_views gives no script view for the value"
    assert value not in scan_views(text, None), "scan_views gives a script view for no value"
    assert scan_holds(text, value), "scan_holds misses the inserted copy"


def test_the_injection_detector_check_method_is_called_by_injection_check_only():
    """Design review m1. ``RegexDetector.check`` called directly lets ``TextnormError`` out for a text over the cap; ``injection_check`` turns it
    into a flag (fail closed). No module of ``src`` calls ``.check(`` on a detector except ``injection.py``. No mutant: a structure pin."""
    from hadavin_sdk.guard import injection

    text = "a" * (defaults.TEXTNORM_MAX_CHARS + 1)
    detector = injection.RegexDetector(0.5)
    refused(TextnormError, "the detector accepted a text over the cap", detector.check, text, "src")
    assert injection.injection_check(detector, text, "src").flagged is True, (
        "injection_check does not flag a refused text"
    )
    callers = []
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            is_check = isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "check"
            if is_check and "detector" in ast.unparse(node.func.value).lower():
                callers.append(path.name)
    assert callers == ["injection.py"], (
        f"a detector's .check is reached outside injection_check: {callers}"
    )


# ---- the floor and the validation of the numbers --------------------------------------------------------------------------------------
def test_a_minimum_below_the_floor_or_not_a_plain_int_is_refused():
    """Killer: ``minimum: the floor is one``. A single character is found in nearly every text of its script. A bool, a float, a string and None
    are refused too (killer ``minimum: a bool is a minimum`` is in the older list)."""
    saved = {name: getattr(defaults, name) for name in textnorm._MINIMUM_NAMES}
    try:
        for name in textnorm._MINIMUM_NAMES:
            for bad in (1, 0, -3, True, 2.0, "4", None):
                setattr(defaults, name, bad)
                refused(
                    TextnormError,
                    f"{name}={bad!r} is accepted by scan_needles",
                    scan_needles,
                    "password-with-many-letters",
                )
                refused(
                    TextnormError,
                    f"{name}={bad!r} is accepted by scan_holds",
                    scan_holds,
                    "any text",
                    "password-with-many-letters",
                )
                setattr(defaults, name, saved[name])
    finally:
        for name, value in saved.items():
            setattr(defaults, name, value)


def test_the_number_of_passes_must_be_a_plain_int_of_at_least_one():
    """Killers: ``passes: the number of passes is not checked`` and ``passes: a bool is a number of passes``."""
    saved = defaults.TEXTNORM_MAX_PASSES
    try:
        for bad in (0, -1, True, 2.0, "3", None):
            defaults.TEXTNORM_MAX_PASSES = bad
            refused(
                TextnormError, f"TEXTNORM_MAX_PASSES={bad!r} is accepted", scan_keyset, "some text"
            )
    finally:
        defaults.TEXTNORM_MAX_PASSES = saved


# ---- one inserted letter of the value's own script ---------------------------------------------------------------------------
def _insertions(needle, ch):
    return [needle[:i] + ch + needle[i:] for i in range(1, len(needle))]


def test_one_inserted_letter_of_the_same_script_is_found_at_every_inner_position():
    """Killers: ``insertion: the match is never made``, ``insertion: the first half is not searched``, ``insertion: the second half is not searched``
    and ``insertion: the minimum is one too high``. Every inner position, and a foreign-script insertion, are found."""
    m = textnorm._insertion_minimum(han(4))
    needle = han(m)
    extra = chr(0x6A01)
    assert value_scripts(needle) == {"HAN"}
    for i, text in enumerate(_insertions(needle, extra), 1):
        assert scan_holds("x" + text + "y", needle), (
            f"an inserted letter after character {i} of {m} is not found"
        )
    assert scan_holds(needle, needle), "the exact needle is not found"
    assert scan_holds(needle[:2] + chr(0x0436) + needle[2:], needle), (
        "a foreign-script letter is not dropped by the script view"
    )


def test_two_inserted_letters_a_missing_letter_and_a_changed_letter_are_not_found():
    """Killer: ``insertion: a changed letter is a match``. The matcher is ONE inserted letter, no more."""
    m = textnorm._insertion_minimum(han(4))
    needle = han(m)
    a, b = chr(0x6A01), chr(0x6A02)
    assert scan_holds(needle[:1] + a + needle[1:2] + b + needle[2:], needle) is False, (
        "two inserted letters are found"
    )
    assert scan_holds(needle[:1] + a + a + needle[1:], needle) is False, (
        "two inserted letters in a row are found"
    )
    assert scan_holds(needle[:-1], needle) is False, "a missing letter is found"
    assert scan_holds(needle[:1] + a + needle[2:], needle) is False, "a changed letter is found"


def test_a_needle_below_the_minimum_of_its_script_is_matched_exactly_only():
    """Killer: ``insertion: the minimum is one too low``. One letter fewer than the minimum: the inserted copy is NOT found; the exact one is."""
    m = textnorm._insertion_minimum(han(4))
    needle = han(m - 1)
    assert len(needle) >= defaults.TEXTNORM_MIN_IDEOGRAPH_CHARS, (
        "the minimum leaves no room under it"
    )
    assert scan_holds("x" + needle + "y", needle) is True, "the exact short needle is not found"
    assert scan_holds("x" + needle[:1] + chr(0x6A01) + needle[1:] + "y", needle) is False, (
        "a needle under the minimum is matched with an insertion"
    )


def test_each_script_has_its_own_minimum():
    """Killer: ``insertion: the minimum ignores the script``. Every entry of ``TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT`` is used for its script;
    the others take the default."""
    makers = {
        "HAN": han,
        "HANGUL": hangul,
        "THAI": thai,
        "KANA": letters(
            "\u3042\u3044\u3046\u3048\u304a\u304b\u304d\u304f\u3051\u3053\u3055\u3057\u3059\u305b\u305d\u305f"
        ),
        "ARABIC": letters(
            "\u0628\u062a\u062c\u062d\u062f\u0631\u0632\u0633\u0634\u0635\u0636\u0637\u0639\u063a\u0641\u0642"
        ),
        "HEBREW": letters(
            "\u05d0\u05d1\u05d2\u05d3\u05d4\u05d6\u05d7\u05d8\u05db\u05dc\u05de\u05e0\u05e1\u05e2\u05e4\u05e6"
        ),
        "DEVANAGARI": letters(
            "\u0915\u0916\u0917\u0918\u091a\u091b\u091c\u091d\u091f\u0920\u0921\u0922\u0923\u0924\u0925\u0926"
        ),
        "CYRILLIC": letters(
            "\u0431\u0433\u0434\u0436\u0437\u0438\u0439\u043b\u043f\u0444\u0446\u0447\u0448\u0449\u044d\u044e"
        ),
        "GREEK": letters(
            "\u03b3\u03b4\u03b6\u03b8\u03bb\u03be\u03c0\u03c3\u03c6\u03c8\u03c9\u03b2\u03b7\u03bc\u03b5\u03b9"
        ),
    }
    table = dict(defaults.TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT)
    assert table, "no script has a minimum of its own: the table is dead"
    for group, make in makers.items():
        want = table.get(group, defaults.TEXTNORM_INSERTION_MIN_CHARS)
        assert value_scripts(make(8)) == {group}, f"{group}: the sample is not of that script"
        assert textnorm._insertion_minimum(make(8)) == want, (
            f"{group}: the insertion minimum is not the one of the table"
        )
    for group in table:
        assert group in makers, f"{group} has a minimum but this test has no sample for it"
    extra = {
        "HAN": chr(0x6A01),
        "HANGUL": chr(0xB000),
        "THAI": chr(0x0E2F),
        "KANA": "\u3092",
        "ARABIC": "\u0648",
        "HEBREW": "\u05ea",
        "DEVANAGARI": "\u0939",
        "CYRILLIC": "\u044b",
        "GREEK": "\u03c4",
    }
    for group, make in makers.items():
        m = textnorm._insertion_minimum(make(8))
        needle = make(m)
        ins = extra[group]
        assert ins not in needle
        assert scan_holds(needle[:2] + ins + needle[2:], needle) is True, (
            f"{group}: an insertion into a needle at its minimum is not found"
        )
        short = make(m - 1)
        whole = short in textnorm.fold_views(short, scripts=value_scripts(short))
        # Cyrillic and Greek: the table reads some of their letters as Latin look-alikes, so the script view holds only FRAGMENTS of the needle
        # (CHANGELOG, fragmentation); a fragment of the needle is found exactly, so the negative check below is made only where the view is whole.
        if len(short) >= defaults.TEXTNORM_MIN_SCRIPT_CHARS and whole:
            assert scan_holds(short[:2] + ins + short[2:], short) is False, (
                f"{group}: an insertion into a needle under its minimum is found"
            )


def test_a_script_that_was_not_measured_takes_the_cautious_default():
    """Killer: ``insertion: the minimum ignores the script``. Armenian is not in the table: its minimum is the default, 8: the largest minimum of the
    measured scripts that have no Latin look-alike letters (Thai)."""
    armenian = "".join(chr(0x0531 + i) for i in range(10))
    assert value_scripts(armenian) == {"ARMENIAN"}
    assert "ARMENIAN" not in dict(defaults.TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT)
    assert textnorm._insertion_minimum(armenian) == defaults.TEXTNORM_INSERTION_MIN_CHARS == 8
    mixed = han(4) + hangul(1)
    assert textnorm._insertion_minimum(mixed) == 5, (
        "a needle with two scripts takes the larger minimum"
    )


def test_a_needle_longer_than_the_maximum_is_matched_exactly_only():
    """Killer: ``insertion: the maximum is one too high``. The longest needle is matched; one more character is exact only."""
    top = defaults.TEXTNORM_INSERTION_MAX_CHARS
    extra = chr(0x6A01)
    at = han(top)
    over = han(top + 1)
    assert scan_holds(at[:5] + extra + at[5:], at) is True, (
        "a needle at the maximum is not matched with an insertion"
    )
    assert scan_holds(over, over) is True, "the exact long needle is not found"
    assert scan_holds(over[:5] + extra + over[5:], over) is False, (
        "a needle over the maximum is matched with an insertion"
    )


def test_a_latin_value_is_not_covered_by_the_one_inserted_letter_match():
    """A stated LIMIT (CHANGELOG): the squeeze view of an ASCII value is exact, so a letter inserted into it ("pasxsword") is a different word. No
    mutant: a limit pin."""
    assert scan_holds("pasxsword", "password") is False, "the limit moved: update the CHANGELOG"


def _brute(view, needle, alphabet):
    if needle in view:
        return True
    return any(needle[:i] + c + needle[i:] in view for i in range(1, len(needle)) for c in alphabet)


def test_the_matcher_agrees_with_the_brute_force_definition_on_every_small_string():
    """Killers: the three ``insertion:`` mutants of the matcher itself. EVERY needle of 2 to 6 letters and EVERY view of up to 9 letters over a
    two-letter alphabet (every case of an overlapping half occurs) against the definition 'the needle with one letter inserted between two of its
    letters is a substring of the view'."""
    alphabet = "ab"
    true_cases = false_cases = 0
    for m in range(2, 7):
        for needle in map("".join, itertools.product(alphabet, repeat=m)):
            for n in range(10):
                for base in map("".join, itertools.product(alphabet, repeat=n)):
                    want = _brute(base, needle, alphabet)
                    assert textnorm._holds_with_one_insertion(base, needle) is want, (
                        f"the matcher and the definition differ on {base!r} / {needle!r}"
                    )
                    true_cases += want
                    false_cases += not want
    assert true_cases > 5000 and false_cases > 5000, "the sample is lopsided"


def test_the_work_of_the_matcher_is_linear_in_the_view_for_a_text_built_to_defeat_it(monkeypatch):
    """The worst case: a view that is copies of the first half of the needle. The work is counted (``_one_off`` calls), not timed: one call per hit
    of an intact half, at most two per position of the view, and each call looks at a window of the needle's length. No mutant: a bound pin."""
    top = defaults.TEXTNORM_INSERTION_MAX_CHARS
    needle = "a" * (top // 2) + "b" * (top - top // 2)
    view = "a" * 5000
    calls = []
    real = textnorm._one_off
    monkeypatch.setattr(textnorm, "_one_off", lambda w, t: calls.append(len(w)) or real(w, t))
    assert textnorm._holds_with_one_insertion(view, needle) is False
    assert len(calls) <= 2 * len(view), "more than two comparisons per position of the view"
    assert max(calls) <= len(needle) + 1, "a comparison looks at more than the needle's length"


# ---- the records and the documents ----------------------------------------------------------------------------------------------------
# The digest of the two interpreter-built tables (``_PUNCT``: the dash, quote and slash readings; ``_DIGITS``: every decimal digit of the
# interpreter read as an ASCII digit) for each Unicode version the suite runs on. 15.0.0 and 15.1.0 give one table: the 15.1 additions are
# ideographs only. Recorded on both interpreters (CHANGELOG, "Pins").
PINNED_TABLE_DIGESTS = {
    "15.0.0": "8896f9860278877c9e5f5ab6728c8f63fdb8458ac238add6262929fec42aa8f1",
    "15.1.0": "8896f9860278877c9e5f5ab6728c8f63fdb8458ac238add6262929fec42aa8f1",
}


def test_the_unicode_dependent_tables_have_a_pinned_digest_for_each_version_we_run():
    """Code review m3. ``_PUNCT`` and ``_DIGITS`` are built from the interpreter's ``unicodedata`` at import. Their digest is pinned for each
    Unicode version the suite runs on, so a change in what the interpreter says about a dash or a digit is caught here and not in a redaction.
    A version with no pinned digest skips, and the skip names it. Killers: ``punct_table_drops_a_dash``, ``digit_table_drops_a_script``."""
    version = unicodedata.unidata_version
    if version not in PINNED_TABLE_DIGESTS:
        pytest.skip(f"no table digest is pinned for Unicode {version}")
    digest = hashlib.sha256(
        repr((sorted(textnorm._PUNCT.items()), sorted(textnorm._DIGITS.items()))).encode()
    ).hexdigest()
    assert digest == PINNED_TABLE_DIGESTS[version], (
        f"the tables for Unicode {version} changed: {digest}"
    )


def test_script_of_has_a_two_word_group_for_every_named_letter_family():
    """Review nit 7. ``_script_of`` has no dead branch: for every letter, the group is the first word of its name, or two words when the first
    word is shared (OLD, ...), or HAN, KANA or UNNAMED."""
    seen = set()
    for cp in range(0x80, 0x110000):
        ch = chr(cp)
        if not unicodedata.category(ch).startswith("L"):
            continue
        group = textnorm._script_of(ch)
        assert group and group == group.upper(), (cp, group)
        assert len(group.split()) <= 2, (cp, group)
        seen.add(group)
    assert {"HAN", "KANA", "UNNAMED", "CYRILLIC", "GREEK", "THAI"} <= seen


def test_the_hebrew_word_for_password_is_refused_as_too_short():
    """Review nit 10: the table reads samekh as a letter, so the Hebrew 'password' (samekh yod samekh mem he) has too few letters of its own
    script. A stated cost, pinned."""
    word = "סיסמה"
    with pytest.raises(ViewTooShort):
        scan_holds("any text", word)


def test_the_module_docstring_lists_every_public_name():
    """Item 8. The 28 names are documented once, in the module docstring; the list in ``tests/test_textnorm.py`` pins the names."""
    doc = textnorm.__doc__
    assert len(textnorm.__all__) == 28
    for name in textnorm.__all__:
        assert f"``{name}``" in doc, f"{name} is not documented in the module docstring"


def test_the_mixed_value_claim_of_the_changelog_holds():
    """The CHANGELOG says a value with ASCII letters and a script part ("pw" plus four ideographs) has the script part as a needle of its own, so a
    text with the script part and without the ASCII part is flagged; with a script part of three ideographs it is refused. No mutant: the
    claim has its own pin since the review found none."""
    assert scan_holds("x \u4e2d\u6587\u6d4b\u8bd5 y", "pw\u4e2d\u6587\u6d4b\u8bd5") is True, (
        "the script part alone is not found"
    )
    assert scan_holds("x pw y", "pw\u4e2d\u6587\u6d4b\u8bd5") is False, (
        "the ASCII part alone is found"
    )
    refused(
        ViewTooShort,
        "a script part of three ideographs next to ASCII is scanned",
        scan_holds,
        "x",
        "pw\u4e2d\u6587\u6d4b",
    )


def test_a_short_cyrillic_or_greek_word_is_refused_at_a_measured_cost():
    """The cost of the minimums for Cyrillic and Greek (CHANGELOG, "Cost of the refusal"): letters the table reads as Latin look-alikes make a
    squeeze view of the same length, the others stay in the script view, and a word is refused when neither view reaches four. Measured on Bible
    translations: Russian words of 5 letters are refused in about a third of the forms, of 6 in about one in seven, of 7 or more never; Greek
    words of 4, 5 and 6 letters in 46, 13 and 2 percent, of 7 or more never. Three examples of each side are pinned. No mutant: a cost pin."""
    for word in (
        "\u0417\u0435\u043c\u043b\u044f",
        "\u0443\u0432\u0438\u0434\u0435\u043b",
        "\u0398\u03b5\u03bf\u03c2",
        "\u03be\u03c5\u03bb\u03bf\u03bd",
    ):
        refused(ViewTooShort, f"{word!r} is scanned: the measured cost changed", scan_needles, word)
    for word in (
        "\u043a\u0440\u0430\u0441\u043d\u044b\u0439",
        "\u041c\u043e\u0441\u043a\u0432\u0430",
        "\u0391\u03b4\u03b5\u03bb\u03c6\u03bf\u03c2",
    ):
        assert scan_needles(word), f"{word!r} is refused: the measured cost changed"
