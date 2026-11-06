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
  Latin letter or digit. Case is kept unless ``casefold`` is set (then ``casefold`` runs BEFORE step 6, see below); ``collapse_ws``
  squeezes runs of whitespace.

The look-alike table (step 6) is GENERATED from the Unicode UTS #39 ``confusables.txt`` MA table by ``tools/gen_confusables.py`` (pinned
sha256, version and date in ``guard/_confusables.py``) plus 16 explicit supplementary letters and a Unicode-name rule for small capitals,
both listed in the generator. Runtime is stdlib only; the data file is not shipped. ``FOLD_VERSION`` names the fold that made a key.

IDEMPOTENT AND CASE-SYMMETRIC BY CONSTRUCTION (``identity_key``, ``same_person``, ``squeeze``; alg ``fold2``). The old order (table, then
casefold, with a table keyed by lower-case letters) was neither: ``identity_key("\u00d8")`` kept the capital and ``identity_key("\u00f8")``
gave ``o``, so ``same_person("B\u00d8B", "bob")`` was False, a DENY bypass. Now, with P = NFKC after the drops after NFKD, D = the digit
table and C = ``casefold``: ``key(x) = tag + collapse(E(C(D(P(C(x))))))`` (C runs twice: first on the raw text, because the upper-case
of a Greek letter with a trailing iota mark is a real letter that P would drop as a mark if C had not turned it into one first; again
after P, because NFKC makes capitals) where E is the look-alike table MOVED ONTO THE CASEFOLD IMAGE
(``_CF_TABLE``): for every table entry whose source ``s`` has ``casefold(s)`` a single character, ``E[casefold(s)] = value.casefold()``;
when two sources reach one casefolded letter the entry of the letter that is its own case-fold wins over the entry of its capital
(13 letters, pinned by a test: e.g. Greek eta reads n, not the capital Eta's H; ``has_mixed_script`` is the backstop for those). The
argument: (1) CASE SYMMETRY: C is the only case-sensitive step, it runs before P and before E, E has casefolded keys only, so two texts that agree
after C agree in the key; that ``C(P(c.upper())) == C(P(c.lower()))`` for every character is a fact about the Unicode data, which
``tests/test_textnorm.py`` checks for ALL non-surrogate code points (and for pairs built from the table) on every supported Unicode
version. (2) IDEMPOTENCE: the image of E is lower-case ASCII; every other character of the result survived C and is not a key of E
(keys of E are non-ASCII and casefold-stable, asserted), so a second C changes nothing and a second E changes nothing; that the
remaining steps (P, D, the drops) leave such characters alone is again a fact about the data, checked by the same tests. The final
form is therefore a fixed point of the whole function; a mutant that restores the old order is killed by those tests. ``fold`` WITHOUT
``casefold`` keeps case and uses the raw table (no symmetry is promised for it); ``squeeze`` casefolds first.

NO BOUNDED-PASS LOOP IN P1a: ``fold`` is one pass and nothing loops to a fixed point; the constant ``defaults.TEXTNORM_MAX_PASSES`` is
read by NOTHING in this package (it is first read by P1b, which may add a bounded loop with a fail-closed error). The idempotence above is
by construction and by test, not by iterating.

UNICODE DATA VERSION: the fold depends on the interpreter's Unicode data (which characters are unassigned). The pinned version is
``defaults.TEXTNORM_PINNED_UNIDATA``. ``require_pinned_unidata()`` is the guard entry point: it raises ``UnidataMismatch`` (fail closed)
when the interpreter's version is not the pin; pilot and prod code calls it before using any key (``app.build`` of P1b). On another
interpreter (development, tests; Python 3.12 has Unicode 15.0.0) the functions still run, and ``identity_key`` then returns a key that
starts with ``key_tag()``: U+E000, ``alg=fold2|ud=<this interpreter's version>``, U+E000. U+E000 is private use, which the fold
always drops, so no key made on the pinned version can ever start with it: a key made on another version never equals one made on the
pinned version, and two other versions never equal each other. On the pinned version the tag is empty (the bare key IS the key of
``alg`` ``fold2``; changing the pin bumps ``alg``). ``identity_key`` of a text that already starts with the tag of this interpreter
removes it first, so the function is idempotent there too.

INPUT RULES (every public function): the argument must be a plain ``str`` (``type(x) is str``; a ``str`` subclass or an enum member is
refused with ``NotText``), and its WEIGHT W must be within ``defaults.TEXTNORM_MAX_CHARS`` (``TextTooLong``). W is the sum, over the
characters of the text, of the longest string the pipeline makes from that one character (an ASCII text has W = its length). No key
is longer than W of its text (plus ``len(key_tag())`` on an unpinned interpreter), because every step acts per character or only joins. Messages hold lengths and constants, never the input.
Any ``TextnormError`` on a DENY or ALLOW path means REFUSE.

Honest limits: a letter in neither the data nor the supplement is not folded. Dropping unassigned code points (Cn) depends on the
Python build's Unicode version (``require_pinned_unidata``). ``has_mixed_script`` is the fail-closed backstop: a word that mixes Latin
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
    "key_tag",
    "names_equal",
    "require_pinned_unidata",
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
    """The interpreter's Unicode data is not the version the keys were pinned to (``require_pinned_unidata()``, or
    ``check_pinned_unidata(strict=True)``). Fail closed: the caller must refuse to run, not fall back."""


_DROP_CATEGORIES = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"})
FILLERS = frozenset(
    map(chr, (0x3164, 0x115F, 0x1160, 0x2800, 0xFFA0, 0x13441, 0x13442))
)  # invisible letters/symbols used to glue or split words (the last two: Egyptian hieroglyph full blank and half blank)
_LOOKALIKES = types.MappingProxyType({chr(c): v for c, v in CONFUSABLES.items()})
_TABLE = types.MappingProxyType(dict(CONFUSABLES))


def _build_cf_table(table: dict[int, str]) -> dict[int, str]:
    """The look-alike table moved onto the case-fold image (see the module docstring): keyed by ``casefold(source)`` (single characters
    only; a source whose case fold is longer is looked up through its parts), valued by the lower-cased value. A letter that is its own
    case fold wins over its capital; otherwise the lowest code point wins (deterministic)."""
    own: dict[int, str] = {}
    derived: dict[int, str] = {}
    for cp in sorted(table):
        folded = chr(cp).casefold()
        if len(folded) != 1:
            continue
        (own if folded == chr(cp) else derived).setdefault(ord(folded), table[cp].casefold())
    return {**derived, **own}


_CF_TABLE = types.MappingProxyType(_build_cf_table(CONFUSABLES))
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
_ALG = "fold2"
FOLD_VERSION = (
    f"alg={_ALG}|tbl={_table_digest(_TABLE)[:12]}:{len(_TABLE)}"
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
    """The weight of ``c``: the larger of the single-pass weight of ``c`` and of its case fold (the case-folding path folds case first)."""
    return max(_pass_weight(c), _pass_weight(c.casefold()))


def _pass_weight(c: str) -> int:
    """The longest string the single-pass pipeline makes from the character ``c``: after NFKD, after NFKC, after the digit and look-alike
    tables and after the case fold (drops only shorten, so they are left out: an upper bound)."""
    nfkd = unicodedata.normalize("NFKD", c)
    nfkc = unicodedata.normalize("NFKC", nfkd)
    digits = nfkc.translate(_DIGITS)
    mapped = digits.translate(_TABLE)
    cased = digits.casefold()
    return max(
        1,
        len(nfkd),
        len(nfkc),
        len(mapped),
        len(mapped.casefold()),
        len(cased),
        len(cased.translate(_CF_TABLE)),
    )


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
    s = unicodedata.normalize("NFKD", raw.casefold() if casefold else raw)
    s = "".join(
        " " if ch.isspace() else ch
        for ch in s
        if ch.isspace() or (unicodedata.category(ch) not in _DROP_CATEGORIES and ch not in FILLERS)
    )
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_DIGITS)
    # casefold BEFORE the table and use the table moved onto the casefold image: idempotent and case-symmetric (module docstring)
    s = s.casefold().translate(_CF_TABLE) if casefold else s.translate(_TABLE)
    return " ".join(s.split()) if collapse_ws else s


def fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    """The comparison form of ``raw`` (see the module docstring). Linear in the weight of ``raw``, which is bounded first."""
    _checked(raw)
    return _fold(raw, casefold=casefold, collapse_ws=collapse_ws)


def squeeze(raw: str, *, loose: bool = False) -> str:
    """Comparison key: folded, upper-case letters and digits only; ``loose`` also treats the digit-like letters O I L S B Z G Q as the
    digits 0 1 1 5 8 2 6 9."""
    _checked(raw)
    s = _fold(raw, casefold=True).upper()
    if loose:
        s = s.translate(_LOOSE)
    return _NON_ALNUM.sub("", s)


def key_tag() -> str:
    """``""`` on the pinned Unicode version; otherwise U+E000 + ``alg=<alg>|ud=<this interpreter's Unicode version>`` + U+E000, which
    ``identity_key`` puts in front of its key so a key made on another version never equals a key made on the pinned one. Read at call
    time. U+E000 is private use: the fold drops it, so no untagged key can start with the tag."""
    version = unicodedata.unidata_version
    if version == defaults.TEXTNORM_PINNED_UNIDATA:
        return ""
    return f"\ue000alg={_ALG}|ud={version}\ue000"


def _canon(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", s).casefold().split())


def identity_key(raw: str) -> str:
    """The comparison key of a DENY decision: ``fold`` with case folded and whitespace collapsed. One definition for every caller.
    The empty string and invisible-only text give ``""`` on the pinned Unicode version (never a value to store or index). On another version
    the key starts with ``key_tag()``. ``fold_key`` is this function."""
    _checked(raw)
    tag = key_tag()
    if tag and raw.startswith(tag):
        raw = raw[len(tag) :]  # already a key of this interpreter: the function stays idempotent
    return tag + _fold(raw, casefold=True, collapse_ws=True)


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


def require_pinned_unidata(expected: str | None = None) -> None:
    """GUARD ENTRY POINT for pilot and prod (P1b: ``app.build`` calls it): raise ``UnidataMismatch`` unless the interpreter's Unicode data
    version is ``expected`` (default ``defaults.TEXTNORM_PINNED_UNIDATA``, read when the function runs). Fail closed: it never warns and
    never returns on a mismatch. Development and tests may run on another version; their keys carry ``key_tag()``."""
    check_pinned_unidata(expected, strict=True)


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
