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
with the fingerprint, printed by ``-rs``), and it FAILS if ``HADAVIN_REQUIRE_PINNED_UNIDATA=1`` is set. The two sections are the same
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
    return textnorm.fold_views(text, casefold=True)


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
        if os.environ.get("HADAVIN_REQUIRE_PINNED_UNIDATA") == "1":
            pytest.fail(message)
        pytest.skip(message)
    live = live_hashes()
    for name in HASHED:
        assert live[name] == section["hashes"][name], (
            f"{name}: the behaviour of the fold changed on Unicode {unicodedata.unidata_version} (bump alg and replace the entry)"
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
