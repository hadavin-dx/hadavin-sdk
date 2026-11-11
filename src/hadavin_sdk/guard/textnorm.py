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
  1. NFKD, so a base letter and its combining mark separate; 2. U+0345 becomes an iota after a Greek letter and is removed anywhere
  else (see U+0345 below); 3. drop control, format, combining-mark, private-use, surrogate and UNASSIGNED (Cn) characters, the
  invisible filler letters and U+FFFD (an unassigned code point that is a SOURCE of the look-alike table is kept for step 7 instead:
  gap 2, only a table of a newer Unicode version has one); 4. NFKC; 5. every Unicode whitespace character (``str.isspace``) becomes a
  space so words are never joined; 6. every Unicode decimal digit becomes an ASCII digit, every Unicode dash (category Pd) and the
  minus sign U+2212 becomes ``-``, the fraction and division slashes U+2044, U+2215, U+29F8, U+FF0F and U+2571 become ``/``, the
  typographic single quotes become ``'`` and the double quotes ``"`` (gap 4); 7. look-alike letters become the Latin letter or digit.
  Case is kept unless ``casefold`` is set (then ``casefold`` runs just BEFORE step 7, see below); ``collapse_ws`` squeezes runs of
  whitespace.

The look-alike table (step 6) is GENERATED from the Unicode UTS #39 ``confusables.txt`` MA table by ``tools/gen_confusables.py`` (pinned
sha256, version and date in the generator and in ``guard/_confusables.py``; Unicode 15.1.0, the version of the interpreter pin) plus
explicit overrides, supplementary letters and a Unicode-name rule for small capitals,
both listed in the generator. Runtime is stdlib only; the data file is not shipped. ``FOLD_VERSION`` names the fold that made a key.

IDEMPOTENT AND CASE-SYMMETRIC BY CONSTRUCTION (``identity_key``, ``same_person``, ``squeeze``; alg ``fold4``). The first order (table, then
casefold, with a table keyed by lower-case letters; alg ``fold1``) was neither: ``identity_key("\u00d8")`` kept the capital and ``identity_key("\u00f8")``
gave ``o``, so ``same_person("B\u00d8B", "bob")`` was False, a DENY bypass. Now, with P = NFKC after the drops after the U+0345 step after
NFKD, D = the digit table and C = ``casefold``: ``key(x) = tag + collapse(E(C(D(P(x)))))`` where E is the look-alike table MOVED ONTO THE CASEFOLD IMAGE
(``_CF_TABLE``): for every table entry whose source ``s`` has ``casefold(s)`` a single character, ``E[casefold(s)] = value.casefold()``;
when two sources reach one casefolded letter the entry of the letter that is its own case-fold wins over the entry of its capital
(13 letters, pinned by a test: e.g. Greek eta reads n, not the capital Eta's H; ``has_mixed_script`` is the backstop for those). The
argument: (1) CASE SYMMETRY: C is the only case-sensitive step, it runs before E, E has casefolded keys only, so two texts that agree
after C agree in the key; that ``C(P(c.upper())) == C(P(c.lower()))`` for every character is a fact about the Unicode data, which
``tests/test_textnorm.py`` checks for ALL non-surrogate code points (and for pairs built from the table, and for seeded random strings)
on every supported Unicode version, with the one stated exemption of U+0345 below. (2) IDEMPOTENCE: the image of E is lower-case ASCII; every other character of the result survived C and is not a key of E
(keys of E are non-ASCII and casefold-stable, asserted), so a second C changes nothing and a second E changes nothing; that the
remaining steps (P, D, the drops) leave such characters alone is again a fact about the data, checked by the same tests. The final
form is therefore a fixed point of the whole function; a mutant that restores the old order is killed by those tests. ``fold`` WITHOUT
``casefold`` keeps case and uses the raw table (no symmetry is promised for it); ``squeeze`` casefolds first.

U+0345 (COMBINING GREEK YPOGEGRAMMENI; decision of P1a fix2, review 2 of this package). Every other mark is dropped, and dropping is what
makes ``identity_key(x + mark) == identity_key(x)``. U+0345 is the one mark that cannot simply be dropped: its upper case and its case fold
are the letter iota, and a Greek letter with the mark (U+1FB3, alpha with ypogegrammeni) upper-cases to two letters (alpha, iota). Two
needs conflict: case symmetry (the key of U+1FB3 must be the key of its upper case, alpha iota) and mark insertion (the key of
"admin" + U+0345 must be the key of "admin"). The rule: U+0345 is read as an iota (U+03B9, then the table: ``i``) when the last kept
character before it is a Greek letter (an alphabetic character whose Unicode name starts with GREEK; characters the fold drops, such as other
marks or a zero-width space, are skipped when looking) and is REMOVED everywhere else (after a Latin or any other letter, after a space,
at the start). It happens on the NFKD text, so the precomposed U+1FB3 and alpha + U+0345 get one key (``ai``). ``fold2`` (the first
order-fixed fold) case-folded the raw text before the drop step, which turned U+0345 into an iota everywhere ("admin" + U+0345 gave ``admini``, a DENY
bypass); ``fold3`` has no early case fold (it is redundant once U+0345 is handled by name: 600,000 random strings gave the same key with and
without it). Chosen over "always drop" because always dropping breaks case symmetry for the precomposed Greek letters with
ypogegrammeni and for Greek text in capitals (U+1FB3 against alpha, iota in capitals), while this rule breaks nothing on them. What the
rule does NOT promise, both stated and tested: (1) after a Greek letter the mark is an iota, so ``identity_key(alpha + U+0345)`` is
not ``identity_key(alpha)`` (the one "base + mark" pair that differs; the mark is a visible subscript there); (2) a text that holds U+0345
NOT after a Greek letter is not case symmetric, because ``str.upper`` turns the mark into the letter Iota while the fold removes it
(``identity_key("\u0345")`` is ``""``, ``identity_key("\u0399")`` is ``i``); the symmetry tests exempt every text that holds U+0345 and pin the Greek-letter case apart. No other code
point is exempt from idempotence, case symmetry or mark insertion. ``fold`` without ``casefold`` applies the same step.

ONE PASS FOR THE IDENTITY KEY, A BOUNDED LOOP FOR THE SCAN KEYS: ``fold`` and ``identity_key`` are one pass; the idempotence above is by
construction and by test, not by iterating. ``scan_keyset`` runs each of its two readings (A: table first, B: case fold first) to a fixed
point in at most ``defaults.TEXTNORM_MAX_PASSES`` passes (the confirming pass included) and raises ``FoldNotConverged`` otherwise; no
code point needs more than 2 changing passes plus the confirming one (capital Sigma on reading A; a test records the maximum).

``scan_keyset`` (DENY scans): at most 8 keys (2 readings x the tag texts T0 to T3) made of letters and digits only, with the class
maps ``z`` to ``3`` (Cyrillic Ze) and ``l`` to ``i``, modifier letters (Lm) removed, no escape decoder. ``same_person`` is
``identity_key`` equality OR a shared scan key; it is not transitive (capital Eta matches ``h`` and ``n``); never use it for an index.

UNICODE DATA VERSION: the fold depends on the interpreter's Unicode data (which characters are unassigned). The pinned version is
``defaults.TEXTNORM_PINNED_UNIDATA``. ``require_pinned_unidata()`` is the guard entry point: it raises ``UnidataMismatch`` (fail closed)
when the interpreter's version is not the pin; ``app.build`` calls it in pilot and prod before anything else. On another
interpreter (development, tests; Python 3.12 has Unicode 15.0.0) the functions still run, and ``identity_key`` then returns a key that
starts with ``key_tag()``: U+E000, ``alg=fold4|ud=<this interpreter's version>``, U+E000. U+E000 is private use, which the fold
always drops, so no key made on the pinned version can ever start with it: a key made on another version never equals one made on the
pinned version, and two other versions never equal each other. On the pinned version the tag is empty (the bare key IS the key of
``alg`` ``fold4``; changing the pin bumps ``alg``). ``identity_key`` of a text that already starts with the tag of this interpreter
removes it first, so the function is idempotent there too. The cost, stated and tested: a RAW text that starts with the tag of THIS
interpreter (typed exactly, U+E000 included) has the tag stripped and so gets the same key as the text without it (an over-collision,
the safe side of a DENY); a text that starts with the tag of ANOTHER version is not stripped (its tag text becomes part of the key). A
caller that did not call ``require_pinned_unidata()`` (``app.build`` does in pilot and prod; a dev or test caller may not) gets tagged keys on every
interpreter whose Unicode data is not the pin, for example Python 3.12; such keys compare only with keys made on the same version.

INPUT RULES (every public function): the argument must be a plain ``str`` (``type(x) is str``; a ``str`` subclass or an enum member is
refused with ``NotText``), and its WEIGHT W must be within ``defaults.TEXTNORM_MAX_CHARS`` (``TextTooLong``). W is the sum, over the
characters of the text, of the longest string the pipeline makes from that one character (an ASCII text has W = its length). No key
is longer than W of its text (plus ``len(key_tag())`` on an unpinned interpreter), because every step acts per character or only joins. Messages hold lengths and constants, never the input.
Any ``TextnormError`` on a DENY or ALLOW path means REFUSE.

Honest limits: a letter in neither the data nor the supplement is not folded. Dropping unassigned code points (Cn) depends on the
Python build's Unicode version (``require_pinned_unidata``). ``has_mixed_script`` is the fail-closed backstop: a word that mixes Latin
with Cyrillic, Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu, Runic, Tamil or any other non-East-Asian script is a deny signal whatever the
table knows (every script in the Unicode data except Common, Inherited and the East Asian scripts counts). Property: ``fold(x + mark) == fold(x) == fold(mark + x)`` for any combining mark, format, control, private-use or unassigned character,
with the one exception above (U+0345 after a Greek letter).
"""

from __future__ import annotations

import bisect
import hashlib
import re
import sys
import time
import types
import unicodedata
import warnings
from collections import Counter
from enum import Enum

from hadavin_sdk import defaults
from hadavin_sdk.guard import _confusables, _scripts
from hadavin_sdk.guard._confusables import TABLE as CONFUSABLES

__all__ = [
    "FILLERS",
    "FOLD_VERSION",
    "AllowVerdict",
    "FoldNotConverged",
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
    "scan_keyset",
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


class FoldNotConverged(TextnormError):
    """A DENY reading of ``scan_keyset`` was still changing after ``defaults.TEXTNORM_MAX_PASSES`` passes (the last one is the confirming
    pass). Fail closed: any ``TextnormError`` on a DENY path means REFUSE. Not seen on any code point or in the fuzz tests; it is the
    bound, not an expected answer."""


_DROP_CATEGORIES = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"})
FILLERS = frozenset(
    map(chr, (0x3164, 0x115F, 0x1160, 0x2800, 0xFFA0, 0x13441, 0x13442))
)  # invisible letters/symbols used to glue or split words (the last two: Egyptian hieroglyph full blank and half blank)
_REPLACEMENT = "\ufffd"  # U+FFFD: a way to hide a character between two letters; dropped from every key whatever its source
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
_TABLE_SOURCES = frozenset(CONFUSABLES)
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
_ALG = "fold4"
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


def _build_punct_table() -> dict[int, str]:
    """Gap 4: every dash (category Pd) and the minus sign read as ``-``; the fraction, division and big solidus forms as ``/``; the
    typographic single and double quotes as ``'`` and ``"``. Applied after NFKC, so compatibility forms (U+2011, U+FE63) are already
    their base."""
    table = {
        cp: "-"
        for cp in range(sys.maxunicode + 1)
        if unicodedata.category(chr(cp)) == "Pd" and cp != 0x2D
    }
    table[0x2212] = "-"
    table.update({cp: "/" for cp in (0x2044, 0x2215, 0x29F8, 0xFF0F, 0x2571)})
    table.update({cp: "'" for cp in (0x2018, 0x2019, 0x201B)})
    table.update({cp: '"' for cp in (0x201C, 0x201D, 0x201F)})
    return table


_PUNCT = types.MappingProxyType(_build_punct_table())
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


# COMBINING GREEK YPOGEGRAMMENI: the only mark whose case fold is a letter (iota); see "U+0345" in the module docstring
_YPOGEGRAMMENI = "\u0345"
_IOTA = "\u03b9"


def _is_greek_letter(ch: str) -> bool:
    """A letter whose Unicode name starts with GREEK: the Greek and Coptic block, Greek Extended and the few Greek letters elsewhere
    (U+1D26 to U+1D2A, U+AB65). Coptic letters are not Greek here."""
    return ch.isalpha() and unicodedata.name(ch, "").startswith("GREEK ")


def _kept(ch: str) -> bool:
    """True for a character the drop step keeps (whitespace is kept and later becomes a space). An unassigned (Cn) code point that is a source
    of the look-alike table is kept too, so the table can read it (gap 2); every other dropped category is dropped before the table. U+FFFD
    is dropped whatever its source."""
    if ch.isspace():
        return True
    if ch in FILLERS or ch == _REPLACEMENT:
        return False
    category = unicodedata.category(ch)
    return category not in _DROP_CATEGORIES or (category == "Cn" and ord(ch) in _TABLE_SOURCES)


def _subscript_iota(s: str) -> str:
    """U+0345 on an NFKD text: an iota (U+03B9) when the last kept character before it is a Greek letter, otherwise removed. Characters the
    fold drops anyway (other marks, format characters, fillers) are skipped when looking for that letter, so inserting one never changes the
    result. A run of U+0345 after a Greek letter gives a run of iotas. This is the one place where a mark is kept (module docstring)."""
    if _YPOGEGRAMMENI not in s:
        return s
    out: list[str] = []
    last = ""  # the last character kept by the drop step
    for ch in s:
        if ch == _YPOGEGRAMMENI:
            if last and _is_greek_letter(last):
                out.append(_IOTA)
                last = _IOTA
            continue
        out.append(ch)
        if _kept(ch):
            last = ch
    return "".join(out)


def _prepare(raw: str) -> str:
    """Steps S1 to S5: NFKD, the U+0345 rule, the drops (whitespace becomes a space), NFKC, the digit table, the dash/slash/quote map."""
    s = _subscript_iota(unicodedata.normalize("NFKD", raw))
    s = "".join(" " if ch.isspace() else ch for ch in s if _kept(ch))
    s = unicodedata.normalize("NFKC", s)
    return s.translate(_DIGITS).translate(_PUNCT)


def _fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    s = _prepare(raw)
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
    """DENY comparator (separation of duties, a blocklist): True when ``a`` and ``b`` have the same ``identity_key`` OR their ``scan_keyset``
    key-sets share a key. Look-alike letters, case, width, ligatures, invisible characters, marks, spaces and punctuation all compare
    equal, which is the safe side for a DENY. It is never narrower than ``identity_key`` equality and ``same_person(x, x)`` is True for
    every text that does not raise. It is NOT transitive (capital Eta matches ``h`` and ``n``, which do not match each other): never use it
    for a unique index, a dedupe or a group-by; use ``identity_key`` equality there. NEVER an ALLOW."""
    _checked(a, b)
    return identity_key(a) == identity_key(b) or _scan_match(a, b)


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


# ---- the DENY keys ------------------------------------------------------------------------------------------------------------------
_TAG_FIRST, _TAG_LAST = 0xE0000, 0xE007F
_TAG_PRINTABLE_FIRST, _TAG_PRINTABLE_LAST = 0xE0020, 0xE007E


def _tag_texts(raw: str) -> list[str]:
    """T0 to T3 (hidden channel in tag form): T0 = the text without any tag character; T1 = tag characters U+E0020 to U+E007E decoded in
    place to their ASCII letters (the other tag characters removed); T2 = T0 followed by the decoded tag characters in order; T3 = the
    decoded tag characters alone. A text with no tag character has only T0."""
    if not any(_TAG_FIRST <= ord(ch) <= _TAG_LAST for ch in raw):
        return [raw]
    t0: list[str] = []
    t1: list[str] = []
    decoded: list[str] = []
    for ch in raw:
        cp = ord(ch)
        if _TAG_FIRST <= cp <= _TAG_LAST:
            if _TAG_PRINTABLE_FIRST <= cp <= _TAG_PRINTABLE_LAST:
                letter = chr(cp - _TAG_FIRST)
                t1.append(letter)
                decoded.append(letter)
        else:
            t0.append(ch)
            t1.append(ch)
    text0 = "".join(t0)
    return [text0, "".join(t1), text0 + "".join(decoded), "".join(decoded)]


def _clock() -> float:
    """The clock of the scan time budget: ``time.monotonic()`` read at each call (a test replaces ``time.monotonic`` with a fake that jumps
    forward and needs no sleep). A module function and not a parameter: ``scan_keyset`` keeps its one parameter (SK-1)."""
    return time.monotonic()


def _converge(text: str, step, deadline: float | None = None) -> str:
    """Repeat ``step`` until its output equals its input, for at most ``defaults.TEXTNORM_MAX_PASSES`` passes (the confirming pass
    included); a text still changing after that raises ``FoldNotConverged``. With a ``deadline`` (a value of ``_clock()``), a pass that
    would start after it raises ``TextTooLong`` (the scan time budget, checked between passes, never inside one)."""
    for _ in range(defaults.TEXTNORM_MAX_PASSES):
        if deadline is not None and _clock() > deadline:
            raise TextTooLong("the scan time budget ran out")
        out = step(text)
        if out == text:
            return out
        text = out
    raise FoldNotConverged(
        f"a reading was still changing after {defaults.TEXTNORM_MAX_PASSES} passes"
    )


def _pass_a(text: str) -> str:
    """Reading A, one pass: the look-alike table first (each letter by its own case: capital Eta reads ``H``), then the case fold."""
    return _prepare(text).translate(_TABLE).casefold()


def _pass_b(text: str) -> str:
    """Reading B, one pass: the case fold first, then the table on the case-fold image (capital Eta becomes eta and reads ``n``)."""
    return _prepare(text).casefold().translate(_CF_TABLE)


# Cyrillic Ze reads 3 and the table sends stroke look-alikes to l or I: join the classes.
_CLASS_MAP = str.maketrans("zl", "3i")


def _scan_key(text: str, step, deadline: float | None = None) -> str:
    """One key of one reading of one tag text: the reading to its fixed point, the class maps ``z`` to ``3`` and ``l`` to ``i``, then only
    letters and digits (every character for which ``str.isalnum()`` is False, and every modifier letter (category Lm), is removed)."""
    s = _converge(text, step, deadline).translate(_CLASS_MAP)
    return "".join(ch for ch in s if ch.isalnum() and unicodedata.category(ch) != "Lm")


def scan_keyset(raw: str) -> frozenset[str]:
    """The DENY keys of a text: a small set of strings, two texts match when their key-sets share a key (or, for a scan, when a key of
    the needle is inside a key of the text). Contract SK-1 to SK-6: the one parameter is ``raw``; at most 2 readings x 4 tag texts = 8
    keys, by construction, each at most as long as the weight of ``raw``; a text over the size rule raises ``TextTooLong``, a non-``str``
    ``NotText``; over-matching is the safe side; a call that has run longer than ``defaults.REDACT_BUDGET_S`` seconds (wall clock, checked before each pass of each reading, never inside a pass) raises ``TextTooLong`` and returns no keys, so a hostile text cannot hold the caller for long (the budget is a parameter of the module, not of the call: SK-1); the keys hold letters and digits only (spaces, punctuation,
    ``#``, ``~``, ``@``, ``|`` and U+FFFD are dropped). Invisible-only text gives ``frozenset()``.

    Order: the size rule on the raw text; every modifier letter (Lm) is removed from the raw text; the tag texts T0 to T3 (a text with no tag
    character has only T0); for each text two readings, A (table first, each letter by its own case) and B (case fold first), each repeated
    to its fixed point; the class maps; the drop. Every step acts on one character at a time except NFKC, which only joins, so a copy's key
    does not depend on its neighbours. No escape decoder runs (HTML entities, percent and backslash escapes come from the caller's own
    decoded view). Scan keys carry no ``key_tag()``: they are compared at once, never stored."""
    _checked(raw)
    deadline = _clock() + defaults.REDACT_BUDGET_S
    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Lm")
    keys = {
        _scan_key(text, step, deadline)
        for text in dict.fromkeys(_tag_texts(raw))
        for step in (_pass_a, _pass_b)
    }
    keys.discard("")
    return frozenset(keys)


def _scan_match(a: str, b: str) -> bool:
    """True if the key-sets of ``a`` and ``b`` share a key. Two empty key-sets share none."""
    return bool(scan_keyset(a) & scan_keyset(b))


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


_SCRIPT_STARTS = tuple(first for first, _, _ in _scripts.RANGES)  # sorted: the lookup is a bisect
_SCRIPT_NAMES = _scripts.SCRIPT_NAMES
# Scripts that may share a word with Latin letters (UTS #39 allows Latin with these in one identifier: Chinese, Japanese, Korean). Every
# other script in the Unicode data (Common and Inherited are neutral) next to Latin is a deny signal.
_EXEMPT_WITH_LATIN = frozenset({"Han", "Hiragana", "Katakana", "Hangul", "Bopomofo"})
_WORD = re.compile(r"\w+", re.UNICODE)
_UNIT_SYMBOLS = frozenset(
    map(chr, (0xB5, 0x2126))
)  # micro sign, ohm sign: unit symbols (5 us, 50 kOhm) that NFKC turns into Greek letters


def _script(ch: str) -> str | None:
    """The Unicode script of ``ch`` from the generated data (``_scripts``, Scripts.txt of the pinned version), or None for Common, Inherited
    and a code point the data does not list."""
    cp = ord(ch)
    i = bisect.bisect_right(_SCRIPT_STARTS, cp) - 1
    if i >= 0:
        first, last, index = _scripts.RANGES[i]
        if first <= cp <= last:
            return _SCRIPT_NAMES[index]
    return None


def has_mixed_script(text: str) -> bool:
    """True if any word mixes Latin letters with letters of another script, except Han, Hiragana, Katakana, Hangul and Bopomofo (UTS #39
    allows those with Latin). The script of a letter comes from the generated data of the pinned Unicode version
    (``guard/_scripts.py``, made by ``tools/gen_confusables.py`` from ``Scripts.txt``), so every script the data names is covered: Cyrillic,
    Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu, Runic, Tamil and the rest. Invisible and combining characters are removed
    first (a zero-width space inside a word does not split it). The micro sign and the ohm sign are exempt (unit symbols); a Greek mu or omega
    typed as a Greek letter next to Latin letters is flagged. The micro and ohm signs are removed BEFORE the analysis, so a word that holds
    only such a sign plus a look-alike letter (micro sign + Cyrillic a) is not flagged by this function; the fold and the table still see the
    Cyrillic letter. A fail-closed deny signal that does not depend on the look-alike table. Digits and punctuation are script-neutral.

    Honest limits: the script is the Script property, not Script_Extensions, so a letter shared by several scripts counts as the one script
    the data gives it. Greek letters next to Latin ones are flagged, so a technical word with a Greek delta or theta glued to Latin letters
    is a false positive; only the micro and ohm signs are exempt. A word of Latin and Arabic, Devanagari, Thai and so on is flagged too. The
    deny is fail-closed by design. A code point added to Unicode after the pinned version is not in the data and counts as neutral."""
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
            script = _script(ch)
            if script == "Latin":
                latin = True
            elif script is not None and script not in _EXEMPT_WITH_LATIN:
                other = True
            if latin and other:
                return True
    return False
