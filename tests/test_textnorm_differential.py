"""The differential test and the golden test of the text fold.

DIFFERENTIAL: ``tests/fixtures/textnorm_corpus.json`` is a hostile list written from a class list. A row is
``{id, class, source, a, b, relation, status}``: ``relation`` is ``equal`` or ``different`` (``refused`` for a size row) from the stated
principle in ``source`` (the DENY views: look-alike, invisible and case variants are equal; the ALLOW view, ``allow_equal``: only identical
strings). ``status`` is ``current`` (asserted now), ``p1b`` (equal by principle but separated by the fold of this package; the
row is an expected failure, strict, and only an AssertionError counts, so an ImportError or an AttributeError is a real failure; the marker
goes when a later package makes the row pass) or ``not_taken`` (a text the Intake invoice steps read as written: asserted DIFFERENT). A value
``{"repeat": [text, n]}`` is the text repeated n times.

GOLDEN: ``tests/fixtures/textnorm_golden.json`` holds the entry of the current ``alg``: one section per Unicode data version, each with
one SHA-256 per hashed function over every non-surrogate code point and the multi-character rows of the corpus, computed WITHOUT the key
tag of an unpinned interpreter (the hashes are of the bare keys, so the 15.0.0 section is computed on Python 3.12 and the 15.1.0 section
on Python 3.13). A change of behaviour shows as a failure here; a change that makes keys different bumps ``alg`` by hand and replaces the
entry in the same pull request (no test enforces the bump; the reviewer checks it). The golden test ASSERTS on every interpreter whose
Unicode version has a section (3.12 and 3.13: no skip); on a version without one (a newer Python) it is only reported (``pytest.skip``
with the fingerprint, printed by ``-rs``), and it FAILS if ``HADAVIN_REQUIRE_PINNED_UNIDATA`` is ``1``, ``true`` or ``yes`` (any case; another value fails the run loudly). The two sections are the same
text apart from the code points assigned only in 15.1.0.
"""

import hashlib
import json
import os
import sys
import unicodedata
from pathlib import Path

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import textnorm
from hadavin_sdk.guard.textnorm import (
    FOLD_VERSION,
    AllowVerdict,
    TextTooLong,
    allow_equal,
    could_be_same_person,
    identity_key,
    squeeze,
)

FIX = Path(__file__).parent / "fixtures"
CORPUS = json.loads((FIX / "textnorm_corpus.json").read_text(encoding="utf-8"))
GOLDEN = json.loads((FIX / "textnorm_golden.json").read_text(encoding="utf-8"))


def expand(value):
    """A corpus value: a plain text, or ``{"repeat": [text, n]}``."""
    return value if isinstance(value, str) else value["repeat"][0] * value["repeat"][1]


def _param(row, *, expected_failure=False):
    marks = []
    if expected_failure and row["status"] == "p1b":
        marks.append(pytest.mark.xfail(strict=True, raises=AssertionError, reason=row["source"]))
    return pytest.param(row, id=row["id"], marks=marks)


ROWS = [_param(r, expected_failure=True) for r in CORPUS]
NOT_REFUSED = [
    _param(r) for r in CORPUS if r["relation"] != "refused"
]  # the ALLOW view holds for every status


@pytest.mark.parametrize("row", ROWS)
def test_the_identity_key_agrees_with_the_stated_principle(row):
    a, b = expand(row["a"]), expand(row["b"])
    if row["relation"] == "refused":
        with pytest.raises(TextTooLong):
            identity_key(a)
        return
    same = identity_key(a) == identity_key(b)
    if row["relation"] == "equal":
        assert same, f"{row['class']}: {row['source']}"
    else:
        assert not same, f"{row['class']}: {row['source']}"


@pytest.mark.parametrize(
    "row", [_param(r, expected_failure=True) for r in CORPUS if r["relation"] == "equal"]
)
def test_could_be_same_person_agrees_with_the_stated_principle_for_every_equal_row(row):
    """The DENY comparator, row by row. The p1b rows (r114 to r117, punctuation) are strict expected failures: they are
    the documented limit in its docstring, and if one starts to pass the row must move to ``current``."""
    a, b = expand(row["a"]), expand(row["b"])
    assert could_be_same_person(a, b), f"{row['class']}: {row['source']}"


@pytest.mark.parametrize("row", NOT_REFUSED)
def test_an_allow_decision_is_equal_only_for_identical_strings(row):
    a, b = expand(row["a"]), expand(row["b"])
    verdict = allow_equal(a, b)
    if a == b:
        assert verdict is AllowVerdict.EQUAL, row["id"]
    else:
        assert verdict is not AllowVerdict.EQUAL, f"{row['id']}: {row['source']}"


# ---- the golden file -----------------------------------------------------------------------------------------------------------------
def _fingerprint():
    return f"python {sys.version_info.major}.{sys.version_info.minor}, unicode {unicodedata.unidata_version}"


def _single_code_points():
    return (chr(cp) for cp in range(sys.maxunicode + 1) if not 0xD800 <= cp <= 0xDFFF)


def _corpus_rows():
    for row in CORPUS:
        if row["relation"] == "refused":
            continue
        for value in (row["a"], row["b"]):
            text = expand(value)
            if len(text) > 1:
                yield text


def _bare(fn):
    """``fn`` with the tag of an unpinned interpreter taken off the key: the golden hashes are of the bare keys."""

    def wrapped(text):
        return fn(text).removeprefix(textnorm.key_tag())

    return wrapped


def _digest(fn, texts):
    """SHA-256 of ``len:key`` lines of ``fn`` over ``texts`` (a key never holds a lone surrogate, but the encoding says so anyway)."""
    h = hashlib.sha256()
    for text in texts:
        key = fn(text)
        h.update(f"{len(key)}:{key}\n".encode("utf-8", "surrogatepass"))
    return h.hexdigest()


def _loose(text):
    return squeeze(text, loose=True)


def _joined(fn):
    """A function that returns the readings of a text (a tuple), as one string: the readings in their fixed order, without the tag of an
    unpinned interpreter, joined by U+001F (a control character, which no key or view holds)."""

    def wrapped(text):
        return "\x1f".join(view.removeprefix(textnorm.key_tag()) for view in fn(text))

    return wrapped


def _fold_views(text):
    """``fold_views`` with the scripts of the text itself: the script views of the old (fix6) algorithm, so the golden hash does not move."""
    return textnorm.fold_views(text, casefold=True, scripts=textnorm.value_scripts(text))


HASHED = {
    "identity_key": _bare(identity_key),
    "squeeze": squeeze,
    "squeeze_loose": _loose,
    "identity_keys": _joined(textnorm.identity_keys),
    "fold_views": _joined(_fold_views),
    "squeeze_views": _joined(textnorm.squeeze_views),
}


def live_hashes():
    """What the golden file holds, computed now. ``python -c 'from tests.test_textnorm_differential import live_hashes'`` rewrites the entry."""
    texts = [*_single_code_points(), *_corpus_rows()]
    return {name: _digest(fn, texts) for name, fn in HASHED.items()}


def _keyset_digest(keys):
    """The helper a key-set function is hashed with: sorted unique keys, each ``len:key``, concatenated, then hashed."""
    joined = "".join(f"{len(k)}:{k}" for k in sorted(set(keys)))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def test_the_golden_file_has_one_entry_for_the_current_algorithm():
    assert set(GOLDEN) == {"note", "alg", "unidata", "sections"}
    assert FOLD_VERSION.startswith(f"alg={GOLDEN['alg']}|"), (
        "the golden entry is for another alg: replace it with the bump"
    )
    assert GOLDEN["unidata"] == defaults.TEXTNORM_PINNED_UNIDATA
    assert GOLDEN["unidata"] in GOLDEN["sections"], (
        "the pinned Unicode version has no golden section"
    )
    assert {"15.0.0", "15.1.0"} <= set(GOLDEN["sections"]), (
        "Python 3.12 and 3.13 must each have a section"
    )
    for section in GOLDEN["sections"].values():
        assert set(section) == {"hashes"}
        assert set(section["hashes"]) == set(HASHED)
        assert all(len(h) == 64 for h in section["hashes"].values())


def test_the_golden_hashes_equal_the_live_ones():
    section = GOLDEN["sections"].get(unicodedata.unidata_version)
    if section is None:
        message = f"no golden section for {_fingerprint()} (sections: {sorted(GOLDEN['sections'])}): reported, not asserted"
        if pin_required(os.environ):
            pytest.fail(message)
        pytest.skip(message)
    live = live_hashes()
    for name in HASHED:
        assert live[name] == section["hashes"][name], (
            f"{name}: the behaviour of the fold changed on Unicode {unicodedata.unidata_version} (bump alg and replace the entry)"
        )


_TRUE = frozenset({"1", "true", "yes"})
_FALSE = frozenset({"", "0", "false", "no"})


def pin_required(env):
    """Whether the run is required to be on the pinned Unicode version: ``HADAVIN_REQUIRE_PINNED_UNIDATA`` is ``1``, ``true`` or ``yes`` in any
    letter case (spaces around it are ignored). Unset, empty, ``0``, ``false`` and ``no`` mean it is not required. ANY OTHER value (``on``,
    ``2``, ``enable``) is refused loudly (``pytest.UsageError``): a CI variable with a typo must not turn the pin off in silence."""
    raw = env.get("HADAVIN_REQUIRE_PINNED_UNIDATA", "")
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise pytest.UsageError(
        f"HADAVIN_REQUIRE_PINNED_UNIDATA={raw!r} is not understood: use 1, true or yes (required) or 0, false, no or nothing (not required)"
    )


def _pin_violation(env, version, pinned):
    """The message of a run that is required to be on the pinned Unicode version and is not, else ``None``."""
    if pin_required(env) and version != pinned:
        return (
            f"HADAVIN_REQUIRE_PINNED_UNIDATA is set (1, true or yes) but this Python carries Unicode {version}, "
            f"not the pinned {pinned}: run the suite on the interpreter of the pin"
        )
    return None


def test_the_interpreter_is_on_the_pinned_unicode_version_when_the_run_requires_it():
    """Fails when ``HADAVIN_REQUIRE_PINNED_UNIDATA`` is ``1``, ``true`` or ``yes`` (any case) and ``unicodedata.unidata_version`` is not
    ``defaults.TEXTNORM_PINNED_UNIDATA``; passes without the variable (a developer on another Python still runs the suite). A value
    that is none of the accepted spellings fails the run loudly. When the run requires the pin, the PRODUCT guard ``require_pinned_unidata()``
    is called too, the one entry point that pilot and prod call at start-up."""
    message = _pin_violation(
        os.environ, unicodedata.unidata_version, defaults.TEXTNORM_PINNED_UNIDATA
    )
    assert message is None, message
    if pin_required(os.environ):
        textnorm.require_pinned_unidata()  # raises UnidataMismatch off the pin


def test_the_product_guard_agrees_with_the_interpreter_and_with_the_pin_constant():
    """``require_pinned_unidata`` from product code, with no environment variable: it returns on the pinned Unicode version and raises
    ``UnidataMismatch`` on any other, whichever interpreter runs the suite; and it reads ``defaults.TEXTNORM_PINNED_UNIDATA``."""
    if unicodedata.unidata_version == defaults.TEXTNORM_PINNED_UNIDATA:
        assert textnorm.require_pinned_unidata() is None
    else:
        with pytest.raises(textnorm.UnidataMismatch):
            textnorm.require_pinned_unidata()
    with pytest.raises(textnorm.UnidataMismatch):
        textnorm.require_pinned_unidata("0.0.0")
    assert textnorm.require_pinned_unidata(unicodedata.unidata_version) is None


def test_the_pin_variable_accepts_one_true_and_yes_in_any_case_and_refuses_other_values_loudly():
    var = "HADAVIN_REQUIRE_PINNED_UNIDATA"
    for yes in ("1", "true", "TRUE", "True", "yes", "YES", "Yes", " 1 ", "tRuE"):
        assert pin_required({var: yes}) is True, yes
    for no in ("", "0", "false", "False", "NO", "no", " "):
        assert pin_required({var: no}) is False, no
    assert pin_required({}) is False
    for odd in ("on", "2", "enable", "y", "t", "required", "1 1", "truee"):
        with pytest.raises(pytest.UsageError):
            pin_required({var: odd})
    pinned = defaults.TEXTNORM_PINNED_UNIDATA
    other = "16.0.0" if pinned != "16.0.0" else "15.1.0"
    for yes in ("true", "YES"):
        assert _pin_violation({var: yes}, other, pinned) is not None, yes
        assert _pin_violation({var: yes}, pinned, pinned) is None, yes


def test_the_pin_message_names_every_accepted_spelling_of_the_variable():
    """fix7 (NIT): the message printed ``HADAVIN_REQUIRE_PINNED_UNIDATA=1`` although ``true`` and ``yes`` are accepted too."""
    message = _pin_violation({"HADAVIN_REQUIRE_PINNED_UNIDATA": "yes"}, "15.0.0", "15.1.0")
    assert message and "=1" not in message and "1, true or yes" in message


def test_the_pin_check_fails_only_when_required_and_off_the_pin():
    pinned = defaults.TEXTNORM_PINNED_UNIDATA
    other = "16.0.0" if pinned != "16.0.0" else "15.1.0"
    required = {"HADAVIN_REQUIRE_PINNED_UNIDATA": "1"}
    assert _pin_violation({}, other, pinned) is None
    assert _pin_violation({"HADAVIN_REQUIRE_PINNED_UNIDATA": "0"}, other, pinned) is None
    assert _pin_violation(required, pinned, pinned) is None
    assert _pin_violation(required, other, pinned) is not None


def test_the_pin_constant_is_the_version_of_the_vendored_table_and_of_the_golden_file():
    """One value in three places: a change of ``defaults.TEXTNORM_PINNED_UNIDATA`` alone must fail here."""
    from hadavin_sdk.guard import _confusables

    assert (
        defaults.TEXTNORM_PINNED_UNIDATA
        == _confusables.DATA_VERSION
        == GOLDEN["unidata"]
        == "15.1.0"
    )


def test_the_key_set_helper_ignores_order_and_repeats_and_keeps_the_length_prefix():
    assert _keyset_digest(["b", "a", "a"]) == _keyset_digest(["a", "b"])
    assert _keyset_digest(["ab", "c"]) != _keyset_digest(["a", "bc"]), (
        "the length prefix is what separates the keys"
    )
    assert _keyset_digest([]) == hashlib.sha256(b"").hexdigest()


def test_the_digest_helper_changes_when_one_key_changes():
    assert _digest(str.upper, ["a", "b"]) != _digest(str.lower, ["a", "b"])
    assert _digest(str, ["ab", "c"]) != _digest(str, ["a", "bc"])


def test_a_corpus_value_may_be_a_repeat():
    assert expand("ab") == "ab" and expand({"repeat": ["ab", 3]}) == "ababab"
    assert textnorm.FOLD_VERSION == FOLD_VERSION
