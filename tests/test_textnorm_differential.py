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
    scan_keyset,
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


# Rows the identity key keeps apart but the DENY scan joins, by design: the scan key drops spaces, punctuation, controls and tag characters,
# so these pairs are the same person for the DENY comparison (the safe side of a DENY). Named, so a new over-match shows as a failure.
OVER_MATCH = {
    "r020": "a tag letter is decoded in the scan key (tag text T1/T2)",
    "r060": "a visible space is dropped by the scan key",
    "r078": "a Unicode space is dropped by the scan key",
    "r094": "a control is dropped by the scan key",
    "r140": "a trailing dot is dropped by the scan key",
    "r174": "a spacing mark (Mc) is not a letter or digit, so the scan key drops it (the safe side of a DENY)",
    "r175": "a spacing mark (Mc) is not a letter or digit, so the scan key drops it (the safe side of a DENY)",
    "r176": "a spacing mark (Mc) is not a letter or digit, so the scan key drops it (the safe side of a DENY)",
}


@pytest.mark.parametrize("row", NOT_REFUSED)
def test_the_deny_comparison_agrees_with_the_stated_principle_and_is_never_narrower_than_the_identity_key(
    row,
):
    a, b = expand(row["a"]), expand(row["b"])
    got = could_be_same_person(a, b) or bool(scan_keyset(a) & scan_keyset(b))
    if identity_key(a) == identity_key(b):
        assert got, f"{row['id']}: the deny comparison is narrower than identity_key equality"
    if row["relation"] == "equal":
        assert got, f"{row['class']}: {row['source']}"
    elif row["id"] in OVER_MATCH:
        assert got, f"{row['id']}: the named over-match is gone ({OVER_MATCH[row['id']]})"
    else:
        assert not got, f"{row['id']}: a new over-match: {row['source']}"


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


def _keyset_hash(texts):
    """SHA-256 over the key-set of every text: one line per text, the helper digest of its sorted unique keys."""
    h = hashlib.sha256()
    for text in texts:
        h.update((_keyset_digest(textnorm.scan_keyset(text)) + "\n").encode("ascii"))
    return h.hexdigest()


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
KEYSET_HASHED = ("scan_keyset",)


def live_hashes():
    """What the golden file holds, computed now. ``python -c 'from tests.test_textnorm_differential import live_hashes'`` rewrites the entry."""
    texts = [*_single_code_points(), *_corpus_rows()]
    return {
        **{name: _digest(fn, texts) for name, fn in HASHED.items()},
        "scan_keyset": _keyset_hash(texts),
    }


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
        assert set(section["hashes"]) == {*HASHED, *KEYSET_HASHED}
        assert all(len(h) == 64 for h in section["hashes"].values())


def test_the_golden_hashes_equal_the_live_ones():
    section = GOLDEN["sections"].get(unicodedata.unidata_version)
    if section is None:
        message = f"no golden section for {_fingerprint()} (sections: {sorted(GOLDEN['sections'])}): reported, not asserted"
        if pin_required(os.environ):
            pytest.fail(message)
        pytest.skip(message)
    live = live_hashes()
    for name in (*HASHED, *KEYSET_HASHED):
        # The alg id changes when identity_key, fold, squeeze, fold_views or squeeze_views change; a change of identity_keys ALONE keeps it,
        # because nothing may store or index an identity_keys result (rule D4 of the ticket; tests/test_textnorm_meta.py enforces the "nothing").
        action = (
            "replace the entry; the alg id stays (rule D4: identity_keys is never stored)"
            if name == "identity_keys"
            else "bump alg and replace the entry"
        )
        assert live[name] == section["hashes"][name], (
            f"{name}: the behaviour of the fold changed on Unicode {unicodedata.unidata_version} ({action})"
        )


# The five hashes that did NOT move when the DENY check began to read the marks-dropped text (F6-1, ORDER 177): copied from the golden file
# of the head before that change. A change of the alg id is for these; identity_keys alone may change without one (rule D4).
UNMOVED_BY_F6_1 = {
    "15.0.0": {
        "identity_key": "a701e40f85a2d37b5da895001e934cbede2d3098fe11a287c5aac1294d97bc4f",
        "squeeze": "7368c4692417bc861672268b6392667d340b1a556863c3058822e1478aa861d9",
        "squeeze_loose": "03c32c9f58eb4defcf78629ef559c20c1677a0ca20183610ae8c53bce3d2462d",
        "fold_views": "2ce9debaabc84b8763cbfca937e13419cba535bf0245edbc13aa0ec1659a3bb1",
        "squeeze_views": "c4a2f83f2dca99c40dae2f7f5b2a34c99baff4d4bbfe08e8a439bc42a11eb511",
    },
    "15.1.0": {
        "identity_key": "e1e91426b47dee0ed37059a650fd691a5a87fea5bac9cf5ec3ca3625bdfeb6b2",
        "squeeze": "7368c4692417bc861672268b6392667d340b1a556863c3058822e1478aa861d9",
        "squeeze_loose": "03c32c9f58eb4defcf78629ef559c20c1677a0ca20183610ae8c53bce3d2462d",
        "fold_views": "58382278973c699354830fb37c7cd83e9b8b9f48a07c0708c01c61a42176fd41",
        "squeeze_views": "c4a2f83f2dca99c40dae2f7f5b2a34c99baff4d4bbfe08e8a439bc42a11eb511",
    },
}


def test_only_the_identity_keys_hash_moved_when_the_deny_check_began_to_drop_the_spacing_marks():
    """F6-1 changes ``identity_keys`` and nothing else: the other five golden hashes of both sections are the ones of the head before the
    change, so the alg id stays ``fold4`` (rule D4), and ``identity_keys`` is the one entry that is NOT among them."""
    assert set(GOLDEN["sections"]) == set(UNMOVED_BY_F6_1)
    for version, section in GOLDEN["sections"].items():
        for name, digest in UNMOVED_BY_F6_1[version].items():
            assert section["hashes"][name] == digest, f"{version} {name}: this hash moved, bump alg"
        assert set(section["hashes"]) - set(UNMOVED_BY_F6_1[version]) == {"identity_keys"}
    assert FOLD_VERSION.startswith("alg=fold4|"), (
        "the alg id changed: that is for the five hashes above, not for identity_keys alone"
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
    """The message printed ``HADAVIN_REQUIRE_PINNED_UNIDATA=1`` although ``true`` and ``yes`` are accepted too."""
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


# Rows the single check name (``identity_key``) still separates but the DENY check passes ALONE, because it fails closed on a character this
# Python cannot name (F6-5, P1a fix8): r085 is a code point unassigned in Unicode 15.1 that a newer table maps to a letter. The DENY comparison
# above also accepts the scan keys, so this row is asserted for ``could_be_same_person`` alone.
DENY_FAILS_CLOSED = frozenset({"r085"})


@pytest.mark.parametrize("row", [_param(r) for r in CORPUS if r["id"] in DENY_FAILS_CLOSED])
def test_could_be_same_person_alone_fails_closed_on_a_character_this_python_cannot_name(row):
    a, b = expand(row["a"]), expand(row["b"])
    assert could_be_same_person(a, b), f"{row['id']}: the DENY check did not fail closed"
