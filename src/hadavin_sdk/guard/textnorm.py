"""The shared text fold, for any place that compares or scans text for a protected value.

A kind or demo that needs a comparison key imports ``fold`` / ``squeeze`` / ``identity_key`` from here instead of keeping its own table.
Do not use ``fold`` to display or store text: it drops legitimate marks (Hindi and Thai vowel signs, the breve of Cyrillic short i) and so
over-collides, which is the safe side for a DENY. Nothing in v1 stores a key: a package that must keep a person or an id for a later
comparison stores the RAW text under its own access rules and folds it again with the current ``identity_key``.

THE RULE (read before using ``fold``): ``fold`` makes look-alike text EQUAL. That is what a DENY decision wants (separation of
duties: "alice" and the Cyrillic-a "alice" are the same person; a blocklist; a leak scan). It is WRONG for an ALLOW decision ("this
address equals the verified address", an allowlist): folding there lets a look-alike address through.
  * ALLOW decision: ``allow_equal(a, b)`` is the WHOLE decision. EQUAL only for identical strings (``a == b``, no normalisation, so
    the text you verified is the text you use); VARIANT means a case, width, ligature or whitespace difference only (refuse); LOOKALIKE
    means the strings differ but fold to the same text through homoglyphs or invisible characters (a spoof attempt: refuse and audit it
    as such); DIFFERENT is an ordinary mismatch (refuse). The caller that wants
    case-insensitive domains lowercases the domain itself BEFORE comparing and uses the lowered text afterwards.
  * DENY decision: ``same_person(a, b)`` (built on ``identity_key``). ``names_equal`` is neither: NFKC, case and whitespace insensitive
    equality for people's names in prose.

``fold`` (stdlib only, linear):
  1. NFKD, so a base letter and its combining mark separate; 2. drop control, format, combining-mark, private-use, surrogate and
  UNASSIGNED (Cn) characters and the invisible filler letters; 3. NFKC; 4. every Unicode whitespace character (``str.isspace``)
  becomes a space so words are never joined; 5. every Unicode decimal digit becomes an ASCII digit; 6. look-alike letters become the
  Latin letter or digit. Case is kept unless ``casefold`` is set; ``collapse_ws`` squeezes runs of whitespace.

The look-alike table (step 6) is GENERATED from the Unicode UTS #39 ``confusables.txt`` MA table by ``tools/gen_confusables.py`` (pinned
sha256, version and date in ``guard/_confusables.py``) plus 16 explicit supplementary letters and a Unicode-name rule for small capitals,
both listed in the generator. Runtime is stdlib only; the data file is not shipped. ``FOLD_VERSION`` names the fold that made a key.

INPUT RULES (every public function): the argument must be a plain ``str`` (``type(x) is str``; a ``str`` subclass or an enum member is
refused with ``NotText``), and its WEIGHT W must be within ``defaults.TEXTNORM_MAX_CHARS`` (``TextTooLong``). W is the sum, over the
characters of the text, of the longest string the pipeline makes from that one character (an ASCII text has W = its length). No key
is longer than W of its text, because every step acts per character or only joins. Messages hold lengths and constants, never the input.
Any ``TextnormError`` on a DENY or ALLOW path means REFUSE.

Honest limits: a letter in neither the data nor the supplement is not folded. Dropping unassigned code points (Cn) depends on the
Python build's Unicode version (``check_pinned_unidata``). ``has_mixed_script`` is the fail-closed backstop: a word that mixes Latin
with Cyrillic, Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu or another look-alike-rich script is a deny signal whatever the
table knows. Property: ``fold(x + mark) == fold(x)`` for any combining mark, format or unassigned character.
"""

from __future__ import annotations

import hashlib
import re
import sys
import types
import unicodedata
import warnings
from collections import Counter
from enum import Enum

from hadavin_sdk import defaults
from hadavin_sdk.guard import _confusables
from hadavin_sdk.guard._confusables import TABLE as CONFUSABLES

__all__ = [
    "FILLERS",
    "FOLD_VERSION",
    "AllowVerdict",
    "NotText",
    "TextTooLong",
    "TextnormError",
    "UnidataMismatch",
    "allow_equal",
    "check_pinned_unidata",
    "fold",
    "fold_key",
    "has_hidden_channel",
    "has_mixed_script",
    "identity_key",
    "names_equal",
    "same_person",
    "squeeze",
]


class TextnormError(Exception):
    """Base of the errors of this module. It is NOT a ``ValueError`` or a ``TypeError``: a DENY caller that does
    ``except ValueError:`` must not swallow it. On any DENY or ALLOW path any ``TextnormError`` means REFUSE."""


class TextTooLong(TextnormError):
    """The weight of a text is over ``defaults.TEXTNORM_MAX_CHARS`` (see the module docstring)."""


class NotText(TextnormError):
    """The argument is not a plain ``str`` (a ``str`` subclass and an enum member are refused too)."""


class UnidataMismatch(TextnormError):
    """The interpreter's Unicode data is not the version the keys were pinned to (``check_pinned_unidata(strict=True)``)."""


_DROP_CATEGORIES = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"})
FILLERS = frozenset(
    map(chr, (0x3164, 0x115F, 0x1160, 0x2800, 0xFFA0, 0x13441, 0x13442))
)  # invisible letters/symbols used to glue or split words (the last two: Egyptian hieroglyph full blank and half blank)
_LOOKALIKES = types.MappingProxyType({chr(c): v for c, v in CONFUSABLES.items()})
_TABLE = types.MappingProxyType(dict(CONFUSABLES))
_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_LOOSE = types.MappingProxyType(
    str.maketrans("OILSBZGQ", "01158269")
)  # letters an attacker writes for digits


def _table_digest(table: types.MappingProxyType[int, str]) -> str:
    """SHA-256 of the table as lines ``f"{cp:06X}:{value}\\n"`` in ascending code point order, UTF-8 (as the generator writes it)."""
    lines = "".join(f"{cp:06X}:{table[cp]}\n" for cp in sorted(table))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


# Which fold made a key: ``alg`` is bumped BY HAND in the pull request that changes what a key can be (the golden file shows the change),
# ``tbl`` is the first 12 hex characters of the digest of the in-memory table and its entry count, ``ucd`` the UTS #39 data version,
# ``ud`` the interpreter's Unicode version. Nothing stores a key in v1.
FOLD_VERSION = (
    f"alg=fold1|tbl={_table_digest(_TABLE)[:12]}:{len(_TABLE)}"
    f"|ucd={_confusables.DATA_VERSION}|ud={unicodedata.unidata_version}"
)


def _build_digit_table() -> dict[int, str]:
    return {
        cp: str(int(chr(cp)))
        for cp in range(sys.maxunicode + 1)
        if chr(cp).isdecimal() and not ("0" <= chr(cp) <= "9")
    }  # every decimal digit that is not ASCII


_DIGITS = types.MappingProxyType(
    _build_digit_table()
)  # built once at import: no lazy fill, so no thread can see a half-filled table


def _char_weight(c: str) -> int:
    """The longest string the single-pass pipeline makes from the character ``c``: after NFKD, after NFKC, after the digit and look-alike
    tables and after the case fold (drops only shorten, so they are left out: an upper bound)."""
    nfkd = unicodedata.normalize("NFKD", c)
    nfkc = unicodedata.normalize("NFKC", nfkd)
    mapped = nfkc.translate(_DIGITS).translate(_TABLE)
    return max(1, len(nfkd), len(nfkc), len(mapped), len(mapped.casefold()))


def _weight(text: str) -> int:
    """W(text): the sum of the character weights. An ASCII text has W = its length. Computed once per DISTINCT character of the text."""
    if text.isascii():
        return len(text)
    return sum(_char_weight(c) * n for c, n in Counter(text).items())


def _checked(*texts: str) -> None:
    """The two input rules, in one place: every argument, left to right, is a plain ``str`` and has a weight within the cap."""
    for text in texts:
        if type(text) is not str:
            raise NotText("a text must be a plain str (a subclass or an enum member is refused)")
        weight = _weight(text)
        if weight > defaults.TEXTNORM_MAX_CHARS:
            raise TextTooLong(
                f"text weight {weight} is over the limit {defaults.TEXTNORM_MAX_CHARS}"
            )


def _fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    s = unicodedata.normalize("NFKD", raw)
    s = "".join(
        " " if ch.isspace() else ch
        for ch in s
        if ch.isspace() or (unicodedata.category(ch) not in _DROP_CATEGORIES and ch not in FILLERS)
    )
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_DIGITS).translate(_TABLE)
    if collapse_ws:
        s = " ".join(s.split())
    return s.casefold() if casefold else s


def fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    """The comparison form of ``raw`` (see the module docstring). Linear in the weight of ``raw``, which is bounded first."""
    _checked(raw)
    return _fold(raw, casefold=casefold, collapse_ws=collapse_ws)


def squeeze(raw: str, *, loose: bool = False) -> str:
    """Comparison key: folded, upper-case letters and digits only; ``loose`` also treats the digit-like letters O I L S B Z G Q as the
    digits 0 1 1 5 8 2 6 9."""
    _checked(raw)
    s = _fold(raw).upper()
    if loose:
        s = s.translate(_LOOSE)
    return _NON_ALNUM.sub("", s)


def _canon(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", s).casefold().split())


def identity_key(raw: str) -> str:
    """The comparison key of a DENY decision: ``fold`` with case folded and whitespace collapsed. One definition for every caller.
    The empty string and invisible-only text give ``""``, which is never a value to store or index. ``fold_key`` is this function."""
    _checked(raw)
    return _fold(raw, casefold=True, collapse_ws=True)


fold_key = identity_key


def same_person(a: str, b: str) -> bool:
    """DENY comparator (separation of duties, a blocklist): True when ``a`` and ``b`` have the same ``identity_key``. Look-alike letters,
    case, width, ligatures, invisible characters and marks all compare equal, which is the safe side for a DENY. NEVER an ALLOW."""
    _checked(a, b)
    return fold_key(a) == fold_key(b)


class AllowVerdict(Enum):
    """Result of ``allow_equal``. A plain ``Enum`` on purpose: ``if allow_equal(a, b):`` raises ``TypeError`` instead of being always
    true. Compare with ``is AllowVerdict.EQUAL``."""

    EQUAL = "EQUAL"  # identical strings: the only verdict that allows
    DIFFERENT = "DIFFERENT"  # an ordinary mismatch: refuse
    VARIANT = "VARIANT"  # differs only in case, width, ligature or whitespace (NFKC + casefold equal): refuse, a plain mistake or a variant
    LOOKALIKE = "LOOKALIKE"  # differs but folds equal through homoglyphs, invisible characters or marks: refuse and audit as a spoof

    def __bool__(self) -> bool:
        raise TypeError("an AllowVerdict has no truth value: compare with 'is AllowVerdict.EQUAL'")


def allow_equal(a: str, b: str) -> AllowVerdict:
    """The whole ALLOW decision for "is this the verified value?": only ``EQUAL`` allows. No normalisation: the comparison is ``a == b``
    so the value that was verified is the value that is used. Both arguments are checked (type, then size) before any work."""
    _checked(a, b)
    if a == b:
        return AllowVerdict.EQUAL
    if _canon(a) == _canon(b):
        return AllowVerdict.VARIANT
    if same_person(a, b):
        return AllowVerdict.LOOKALIKE
    return AllowVerdict.DIFFERENT


def names_equal(a: str, b: str) -> bool:
    """People's names in prose: NFKC, case and whitespace insensitive. NOT an ALLOW decision (``allow_equal``) and NOT a DENY decision
    either (``same_person``: this one does not fold look-alikes, so a Cyrillic-a name is a different name here). Never stored, never a key."""
    _checked(a, b)
    return _canon(a) == _canon(b)


# The hidden channel: characters that show nothing and can carry text or bits. Exactly two rules: (1) the tag block U+E0000 to U+E007F;
# (2) every Variation_Selector other than the two emoji selectors U+FE0E and U+FE0F (Mongolian free selectors U+180B-180D and U+180F,
# U+FE00-FE0D, U+E0100-E01EF). Other invisible characters, combining marks, whitespace, U+FE0E, U+FE0F and characters written as HTML
# entities are NOT counted and are unbounded: ``fold`` drops them, and the look-alike check (not this signal) catches a known value
# hidden with them. The text is read RAW: no escape decoder runs, so a caller that checks decoded views calls this on each view.
_HIDDEN_CHANNEL = re.compile(
    r"[\U000e0000-\U000e007f\u180b-\u180d\u180f\ufe00-\ufe0d\U000e0100-\U000e01ef]"
)


def has_hidden_channel(text: str) -> bool:
    """True when the RAW ``text`` holds a tag character or a free variation selector (the two rules above). A caller decides what to do;
    England, Scotland and Wales flag emoji (tag letters) and an ideographic variation selector after a Japanese name are reported (the safe
    side)."""
    _checked(text)
    return _HIDDEN_CHANNEL.search(text) is not None


def check_pinned_unidata(expected: str | None = None, *, strict: bool = False) -> None:
    """Compare the interpreter's Unicode data version with ``expected`` (default: ``defaults.TEXTNORM_PINNED_UNIDATA``, read when the
    function runs, so a patched constant is seen). A difference raises ``UnidataMismatch`` when ``strict`` and warns otherwise. Pilot and prod
    call it with ``strict=True``."""
    if expected is None:
        expected = defaults.TEXTNORM_PINNED_UNIDATA
    if unicodedata.unidata_version != expected:
        message = (
            f"Unicode data {unicodedata.unidata_version} is not the pinned {expected}: "
            "keys made here may differ from keys made elsewhere"
        )
        if strict:
            raise UnidataMismatch(message)
        warnings.warn(message, stacklevel=2)


_NON_LATIN_SCRIPTS = (
    "CYRILLIC", "GREEK", "ARMENIAN", "CHEROKEE", "COPTIC", "GEORGIAN", "HEBREW", "LISU", "CANADIAN", "OSAGE", "VAI", "NKO",
    "TIFINAGH", "BAMUM", "WARANG", "DESERET", "MIAO", "ELBASAN", "CARIAN", "LYCIAN", "LYDIAN", "OLD ",
)  # fmt: skip
_WORD = re.compile(r"\w+", re.UNICODE)
_UNIT_SYMBOLS = frozenset(
    map(chr, (0xB5, 0x2126))
)  # micro sign, ohm sign: unit symbols (5 us, 50 kOhm) that NFKC turns into Greek letters


def has_mixed_script(text: str) -> bool:
    """True if any word mixes Latin letters with Cyrillic, Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu or another
    look-alike-rich script (UTS #39 style). Invisible and combining characters are removed first (a zero-width space inside a word does
    not split it). The micro sign and the ohm sign are exempt (unit symbols); a Greek mu or omega typed as a Greek letter next to Latin
    letters is flagged. The micro and ohm signs are removed BEFORE the analysis, so a word that holds only such a sign plus a
    look-alike letter (micro sign + Cyrillic a) is not flagged by this function; the fold and the table still see the Cyrillic letter. A
    fail-closed deny signal that does not depend on the look-alike table. Digits and punctuation are script-neutral.

    Honest limits: the script list is a curated prefix list of Unicode character names, NOT the UTS #39 script-extension data (Runic, Tamil,
    Bopomofo and others are not on it and are neither folded nor flagged; each added script is a new false-positive source, and the fold
    table is the first line for those). Greek letters next to Latin ones are flagged, so a technical word with a Greek delta or theta glued
    to Latin letters is a false positive; only the micro and ohm signs are exempt. The deny is fail-closed by design."""
    _checked(text)
    kept = "".join(
        " " if ch.isspace() else ch  # a newline or tab separates words, as in fold
        for ch in text
        if ch.isspace()
        or (
            ch not in _UNIT_SYMBOLS
            and ch not in FILLERS
            and unicodedata.category(ch) not in _DROP_CATEGORIES
        )
    )
    for word in _WORD.findall(unicodedata.normalize("NFKC", kept)):
        latin = other = False
        for ch in word:
            if not ch.isalpha():
                continue
            name = unicodedata.name(ch, "")
            if name.startswith("LATIN"):
                latin = True
            elif name.startswith(_NON_LATIN_SCRIPTS):
                other = True
            if latin and other:
                return True
    return False
