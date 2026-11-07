"""P1b order 137: the strict ``scan_views``, the registration check (``register_value``), the opt-in cache scope, the guard that no other module builds its own views,
the scan-key cap at exactly the cap and one over, the Japanese mixed minimum and the pinned outcome of the Russian word for "password".

Look-alikes and scripts are built with ``chr()``. Every test names, in its docstring, the mutant of ``tests/textnorm_mutants.py`` that it is there to kill. A test
that pins a fact and not a behaviour says so ("fact pin"). Behaviour is asserted before any private name is read.
"""

import ast
import logging
from pathlib import Path

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import textnorm
from hadavin_sdk.guard.textnorm import (
    Coverage,
    CoverageRefused,
    EmptyView,
    NotText,
    TextnormError,
    TextTooLong,
    ViewTooShort,
    fold_views,
    register_value,
    scan_cache,
    scan_holds,
    scan_keyset,
    scan_needles,
    scan_views,
    scan_views_no_value,
    squeeze_views,
    value_scripts,
)

SRC = Path(textnorm.__file__).resolve().parents[1]


def han(n, start=0x5000):
    """``n`` distinct Han ideographs that no table reads."""
    return "".join(chr(start + 13 * i) for i in range(n))


def kana(n):
    """``n`` distinct hiragana letters."""
    return "".join(chr(0x3042 + 2 * i) for i in range(n))


def hangul(n):
    return "".join(chr(0xAC00 + 29 * i) for i in range(n))


def _raises(exc, fn, *args, **kwargs):
    """The exception ``fn`` raises, which must be ``exc``. A different exception, or none, is an ``AssertionError`` whose first line says which (the
    other exception's text goes into the message; ``from None`` keeps it out of the traceback's first line)."""
    try:
        fn(*args, **kwargs)
    except exc as caught:
        return caught
    except TextnormError as other:
        raise AssertionError(
            f"{fn.__name__} raised {type(other).__name__} ({other}), not {exc.__name__}"
        ) from None
    raise AssertionError(f"{fn.__name__} raised nothing, not {exc.__name__}")


def _value(fn, *args, **kwargs):
    """What ``fn`` returns; an exception is an ``AssertionError`` that names it."""
    try:
        return fn(*args, **kwargs)
    except TextnormError as other:
        raise AssertionError(
            f"{fn.__name__} raised {type(other).__name__} ({other}) where a value was expected"
        ) from None


# ---- D1: scan_views takes a value; no value is a different function -----------------------------------------------------------------
def test_scan_views_refuses_none_as_the_value_and_the_other_function_gives_the_views_of_no_value():
    """Killer: ``scan_views: None is a value that has no scripts``. An unset configuration field must not become a scan without script views."""
    value = han(4)
    text = "x " + value + " y"
    _raises(NotText, scan_views, text, None)
    _raises(NotText, scan_views, text, value=None)
    assert value in scan_views(text, value), "scan_views gives no script view for the value"
    assert value not in scan_views_no_value(text), "the views of no value hold a script view"
    expected = {
        *fold_views(text, casefold=True, collapse_ws=True, scripts=frozenset()),
        *squeeze_views(text),
        *scan_keyset(text),
    } - {""}
    assert set(scan_views_no_value(text)) == expected, (
        "the views of no value are not fold, squeeze and keys"
    )
    _raises(NotText, scan_views_no_value, None)
    _raises(NotText, scan_views_no_value, b"x")


# ---- D2: the registration check -----------------------------------------------------------------------------------------------------
def test_a_value_in_the_insertion_band_is_registered_as_fuzzy_and_strict_accepts_it():
    """Killer: ``register: a value in the band is exact only``."""
    value = han(4)
    result = _value(register_value, value)
    assert isinstance(result, Coverage)
    assert result.coverage == "fuzzy" and result.narrowed is False, result
    assert result.needles >= 1 and result.reason
    assert scan_holds("x " + value[:2] + chr(0x6A01) + value[2:] + " y", value) is True, (
        "fuzzy but the inserted copy is not found"
    )


def test_the_band_edges_of_a_script_value():
    """Killers: ``register: the band minimum is one too high`` and ``register: the band maximum is one too low``. Four Han letters are fuzzy, three are
    exact only; the longest needle (the maximum) is fuzzy, one more is exact only."""
    top = defaults.TEXTNORM_INSERTION_MAX_CHARS
    for count, want in ((3, "exact_only"), (4, "fuzzy"), (top, "fuzzy"), (top + 1, "exact_only")):
        got = _value(register_value, han(count), strict=False)
        assert got.coverage == want, f"{count} Han letters: {got.coverage}, not {want}"


def test_a_latin_value_is_exact_only_and_strict_refuses_it_by_default():
    """Killer: ``register: strict is not the default``. A value we cannot cover loudly is acceptable, one we cannot cover silently is not. The message
    says what to do and never holds the value."""
    value = "Pass" + "word" + "17"
    assert defaults.TEXTNORM_STRICT_COVERAGE is True
    caught = _raises(CoverageRefused, register_value, value)
    message = str(caught)
    assert value not in message and value.lower() not in message.lower(), (
        "the message holds the value"
    )
    for part in ("REFUSED", "longer form", "strict=False", f"{len(value)} characters"):
        assert part in message, f"{part!r} is not in the refusal: {message}"
    loose = _value(register_value, value, strict=False)
    assert loose.coverage == "exact_only" and "Latin" in loose.reason, loose


def test_the_default_of_strict_is_the_constant_in_defaults(monkeypatch):
    """Killer: ``register: strict is not the default``. The constant is read when the function runs."""
    value = "Pass" + "word" + "17"
    _raises(CoverageRefused, register_value, value)
    monkeypatch.setattr(defaults, "TEXTNORM_STRICT_COVERAGE", False)
    assert _value(register_value, value).coverage == "exact_only", (
        "a False constant did not make the default loose"
    )
    _raises(NotText, register_value, value, strict="yes")


def test_a_value_with_a_script_part_and_an_ascii_part_that_has_no_needle_is_narrowed():
    """Killer: ``register: a narrowed value is accepted in strict mode``. The script part is a needle; the number next to it (four digits, under the digit
    minimum) is not, so a text with only the number is not found: said in the result, refused in strict mode. With six digits the number is a needle."""
    script = han(4)
    short = _value(register_value, script + "1234", strict=False)
    assert short.coverage == "fuzzy" and short.narrowed is True, short
    caught = _raises(CoverageRefused, register_value, script + "1234")
    assert "only in part" in str(caught), str(caught)
    full = _value(register_value, script + "123456")
    assert full.narrowed is False and full.coverage == "fuzzy", full
    assert _value(register_value, script, strict=False).narrowed is False


def test_a_value_that_cannot_be_scanned_is_refused_in_both_modes():
    """Killer: ``register: a refused value is registered``. ``register_value`` raises what ``scan_holds`` raises."""
    for strict in (True, False):
        _raises(EmptyView, register_value, "", strict=strict)
        _raises(ViewTooShort, register_value, "ab", strict=strict)
        _raises(
            ViewTooShort,
            register_value,
            "9" * (defaults.TEXTNORM_MIN_DIGIT_CHARS - 1),
            strict=strict,
        )
    _raises(NotText, register_value, b"abc")


def test_registration_is_logged_with_the_coverage_and_never_the_value(caplog):
    """Killer: ``register: the coverage is not logged at its level``. INFO for a fuzzy value, WARNING for an exact-only one."""
    fuzzy_value = han(5)
    plain = "Pass" + "word" + "17"
    with caplog.at_level(logging.INFO, logger="hadavin_sdk.guard"):
        _value(register_value, fuzzy_value)
        _value(register_value, plain, strict=False)
    records = [
        r for r in caplog.records if r.name == "hadavin_sdk.guard" and "coverage=" in r.getMessage()
    ]
    levels = [r.levelno for r in records]
    assert levels == [logging.INFO, logging.WARNING], (
        f"levels {levels} instead of INFO then WARNING"
    )
    assert (
        "coverage=fuzzy" in records[0].getMessage()
        and "coverage=exact_only" in records[1].getMessage()
    )
    assert fuzzy_value not in caplog.text and plain not in caplog.text, "the log holds a value"


# ---- D5: no other module builds its own views ---------------------------------------------------------------------------------------
BUILDERS = frozenset(
    {
        "scan_needles",
        "fold_views",
        "squeeze_views",
        "scan_keyset",
        "squeeze",
        "fold",
        "identity_keys",
    }
)


def _textnorm_builder_calls():
    """(file, name) for every call, in a module of ``src`` other than ``textnorm.py``, of a view builder of ``textnorm`` (``textnorm.name(...)`` or a
    name imported from it)."""
    found = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name in ("textnorm.py", "_confusables.py", "_scripts.py"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("textnorm")
            for alias in node.names
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "textnorm"
            ):
                name = func.attr
            elif isinstance(func, ast.Name) and func.id in imported:
                name = func.id
            else:
                continue
            if name in BUILDERS:
                found.append((path.name, name))
    return found


def test_no_module_outside_textnorm_builds_its_own_views():
    """Killer: ``injection: a module builds its own views``. Outside ``textnorm.py`` only the choke points may be called: ``scan_holds``, ``scan_views``,
    ``scan_views_no_value``, ``register_value``, ``scan_cache``. (``runmap.redact_text`` keeps its own position-exact views and does not call
    ``textnorm`` at all; the CHANGELOG states that as a limit.)"""
    assert _textnorm_builder_calls() == [], (
        f"a module builds its own views: {_textnorm_builder_calls()}"
    )
    seen = set()
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "textnorm.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "textnorm"
            ):
                seen.add(node.attr)
    assert seen, "no module of src uses textnorm: the search is broken"
    allowed = {
        "scan_holds",
        "scan_views",
        "scan_views_no_value",
        "register_value",
        "scan_cache",
        "require_pinned_unidata",
    }
    assert seen <= allowed, f"a module of src uses {sorted(seen - allowed)} of textnorm"


# ---- D7: the views of a text are kept only inside a scope --------------------------------------------------------------------------
def _counting_readings(monkeypatch):
    seen = []
    real = textnorm._readings

    def counting(raw, *args, **kwargs):
        seen.append(raw)
        return real(raw, *args, **kwargs)

    monkeypatch.setattr(textnorm, "_readings", counting)
    return seen


def test_nothing_of_a_text_is_kept_between_calls_outside_a_scope(monkeypatch):
    """Killer: ``cache: the views are kept outside a scope``. Two scans of one text outside ``scan_cache`` read it twice as often as one."""
    text = "a log line that may hold a secret pass\u200bword inside it " * 2
    seen = _counting_readings(monkeypatch)
    assert scan_holds(text, "password") is True
    once = seen.count(text)
    assert once >= 1
    assert scan_holds(text, "password") is True
    assert seen.count(text) == 2 * once, "the views of the text were kept between two calls"
    assert textnorm._SCAN_CACHE.get() is None, "a cache exists outside a scope"


def test_the_scope_keeps_digests_not_texts_at_most_two_and_empties_itself(monkeypatch):
    """Killers: ``cache: the key is the text``, ``cache: the scope is not emptied``, ``cache: more than two texts are kept``. The cache holds no text,
    not even as a key; it is empty when the scope ends, also after an exception."""
    texts = [f"text number {i} with a pass\u200bword in it" for i in range(3)]
    holder = {}
    with scan_cache():
        for t in texts:
            assert scan_holds(t, "password") is True
        cache = textnorm._SCAN_CACHE.get()
        holder["cache"] = cache
        assert cache is not None and len(cache) == 2, f"{len(cache)} texts kept, two allowed"
        assert all(len(k) == 64 and set(k) <= set("0123456789abcdef") for k in cache), (
            "a key is not a digest"
        )
        assert not any(t in cache for t in texts), "a text is a key"
        with scan_cache():
            assert textnorm._SCAN_CACHE.get() is cache, (
                "an inner scope does not share the outer cache"
            )
        assert textnorm._SCAN_CACHE.get() is cache
    assert holder["cache"] == {} and textnorm._SCAN_CACHE.get() is None, (
        "the scope did not empty the cache"
    )
    with pytest.raises(RuntimeError), scan_cache():
        scan_holds(texts[0], "password")
        holder["again"] = textnorm._SCAN_CACHE.get()
        raise RuntimeError("stop")
    assert holder["again"] == {} and textnorm._SCAN_CACHE.get() is None, (
        "an exception left the cache full"
    )


# ---- F1: the Russian word for "password" ---------------------------------------------------------------------------------------------
def test_the_russian_word_for_password_is_accepted_at_the_pinned_outcome():
    """Fact pin (the CHANGELOG says the word is accepted; a table reading said it is refused; this is what the code does). Killer: ``squeeze: the minimum is five``, which drops the four-letter squeeze needle. The word is built from code points: pe, a, er, o, el, soft sign. The two needles are
    the script view (Cyrillic pe and el with the Latin look-alikes a, p, o, b) and the squeeze view APOB."""
    word = "".join(chr(c) for c in (0x43F, 0x430, 0x440, 0x43E, 0x43B, 0x44C))
    script_needle = chr(0x43F) + "apo" + chr(0x43B) + "b"
    needles = _value(scan_needles, word)
    assert set(needles) == {script_needle, "APOB"}, f"the needles of the word are {sorted(needles)}"
    assert scan_holds("x " + word + " y", word) is True
    assert scan_holds("x " + " ".join(word) + " y", word) is True, (
        "a space between the letters hides the word"
    )
    assert scan_holds("an unrelated english sentence", word) is False
    assert _value(register_value, word, strict=False).coverage == "exact_only"


def test_the_strict_refusal_names_the_setting_that_makes_it_strict():
    """Order 140 (1). The message of ``CoverageRefused`` names ``TEXTNORM_STRICT_COVERAGE`` and ``strict=False``, for a Latin value and for a narrowed one.
    Killer: ``register: the refusal does not name the setting``."""
    for value in ("Pass" + "word" + "17", han(4) + "1234"):
        message = str(_raises(CoverageRefused, register_value, value))
        assert "TEXTNORM_STRICT_COVERAGE" in message, (
            f"the refusal does not name the setting: {message}"
        )
        assert "strict=False" in message, f"the refusal does not name the way out: {message}"


def test_the_matcher_takes_a_window_that_agrees_with_the_needle_to_the_end():
    """Killer: ``insertion: a window that agrees to the end is not a match``. ``scan_holds`` finds an exact copy before the matcher runs, so the case where
    the window equals the second half (plus nothing, or plus one letter after it) is only reached by the matcher itself; it must say True for an exact
    copy inside a longer view, with the half found first or second, and False when the copy is broken twice."""
    needle = han(6)
    other = chr(0x6A01)
    assert textnorm._holds_with_one_insertion("ab" + needle + "cd", needle) is True, (
        "an exact copy inside a view is not matched"
    )
    assert textnorm._holds_with_one_insertion(needle, needle) is True, (
        "an exact copy that is the whole view is not matched"
    )
    assert textnorm._holds_with_one_insertion(needle + other, needle) is True, (
        "an exact copy followed by one letter is not matched"
    )
    assert textnorm._holds_with_one_insertion(other + needle, needle) is True, (
        "an exact copy preceded by one letter is not matched"
    )
    twice = needle[:2] + other + needle[2:4] + other + needle[4:]
    assert textnorm._holds_with_one_insertion(twice, needle) is False, (
        "two inserted letters are matched"
    )


# ---- D3: the Japanese mixed minimum -----------------------------------------------------------------------------------------------------
def test_a_japanese_needle_of_han_and_kana_takes_the_han_minimum_and_other_mixtures_the_largest():
    """Killers: ``insertion: Han and kana take the larger minimum`` and ``insertion: any mixture that holds Han and kana takes the smaller minimum``.
    Measured: a mixed Han and kana needle of four letters has an extra false-hit rate of 0.3 percent at 10,000 characters (CHANGELOG, D3), within the
    bound of the other scripts. A pure kana needle keeps its own minimum; Han, kana and Hangul together take the largest."""
    han_min = dict(defaults.TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT)["HAN"]
    kana_min = dict(defaults.TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT)["KANA"]
    hangul_min = dict(defaults.TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT)["HANGUL"]
    assert han_min < kana_min and han_min < hangul_min
    mixed = han(han_min - 1) + kana(1)
    assert value_scripts(mixed) == {"HAN", "KANA"}
    extra = chr(0x6A01)
    assert _value(scan_holds, "x" + mixed[:2] + extra + mixed[2:] + "y", mixed) is True, (
        "a mixed needle at the Han minimum is not matched with an insertion"
    )
    assert _value(register_value, mixed).coverage == "fuzzy", (
        "a mixed Han and kana needle at the Han minimum is not fuzzy"
    )
    pure = kana(han_min)
    assert scan_holds("x" + pure[:2] + chr(0x3092) + pure[2:] + "y", pure) is False, (
        "a pure kana needle took the Han minimum"
    )
    three = han(han_min - 1) + kana(1) + hangul(1)
    assert value_scripts(three) == {"HAN", "KANA", "HANGUL"}
    assert textnorm._insertion_minimum(three) == max(han_min, kana_min, hangul_min), (
        "three groups do not take the largest minimum"
    )


# ---- R2-03: the scan-key cap at exactly the cap and one over -----------------------------------------------------------------------------
def _stub_keys(monkeypatch, counts, drop_last=False):
    """Make ``scan_keyset`` produce a chosen number of distinct keys. ``counts`` is the number of tag texts of the text as it is and of the text without
    its spacing mark (the text holds one, so both readings exist); each tag text gives two keys (the two passes). With ``drop_last`` the last key of
    the first reading is empty, and so dropped, which makes an odd count. A stub of ``_tag_texts`` and ``_scan_key``: the real tables never reach
    these counts (thirteen at most, see the other cap test)."""
    text = "a\u0c02"

    def tags(variant):
        n = counts[0] if variant == text else counts[1]
        return [f"{'A' if variant == text else 'B'}{i}" for i in range(n)]

    def key(tag_text, step):
        if drop_last and tag_text == f"A{counts[0] - 1}" and step is textnorm._pass_b:
            return ""
        return f"k{tag_text}{step.__name__}"

    monkeypatch.setattr(textnorm, "_tag_texts", tags)
    monkeypatch.setattr(textnorm, "_scan_key", key)
    return text


def test_exactly_the_cap_in_scan_keys_is_allowed_and_one_over_is_refused(monkeypatch):
    """Killers: ``keys: the cap guard refuses the cap itself`` and ``keys: the cap guard is gone``. Sixteen keys (2 readings x 4 tag texts x 2 passes) are
    allowed; seventeen raise ``TextTooLong`` (and so does eighteen). Behaviour first; the constant is read last (fact pin: it is 16)."""
    text = _stub_keys(monkeypatch, (4, 4))
    assert len(_value(scan_keyset, text)) == 16, "the cap itself was refused or the stub is wrong"
    text = _stub_keys(monkeypatch, (5, 4), drop_last=True)
    _raises(TextTooLong, scan_keyset, text)
    text = _stub_keys(monkeypatch, (5, 4))
    _raises(TextTooLong, scan_keyset, text)
    assert textnorm._SCAN_KEY_CAP == 16
