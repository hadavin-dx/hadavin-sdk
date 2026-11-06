"""The shared text fold, for any place that compares or scans text for a protected value.

A kind or demo that needs a check name or a scan imports ``identity_keys`` / ``could_be_same_person`` / ``fold_views`` / ``squeeze_views`` from
here instead of keeping its own table.
Do not use ``fold`` to display or store text: it drops the non-spacing marks (category Mn: the breve of Cyrillic short i, accents, the
Hindi and Thai vowel signs that sit above or below a letter) and so over-collides, which is the safe side for a DENY. It KEEPS the spacing
marks (Mc: the Hindi vowel signs aa and i, visarga), the modifier letters (Lm) and the modifier symbols (Sk); see "MARKS AND SCANS" below.

WORDS (one word, one meaning). A SPELLING VARIANT is one of the at most three ways one text is read (see "SPELLING VARIANTS" below). A CHECK
NAME is the comparison text made from one spelling variant; the function names say "key" (``identity_key``, ``key_tag``) and mean the
check name. A VIEW is a text returned by ``fold_views`` or ``squeeze_views`` for a scan: a spelling variant, or the same spelling variant
with the spacing marks, modifier letters and modifier symbols dropped (see "MARKS AND SCANS"). "Same person" in ``could_be_same_person`` means
the DENY test returns True: the texts may be one person or a look-alike name, which is the safe side.
Nothing in v1 stores a check name: a package that must keep a person or an id for a later
comparison stores the RAW text under its own access rules and folds it again with the current ``identity_key``.

THE RULE (read before using ``fold``): ``fold`` makes look-alike text EQUAL. That is what a DENY decision wants (separation of
duties: "alice" and the Cyrillic-a "alice" may be the same person; a blocklist; a leak scan). It is WRONG for an ALLOW decision ("this
address equals the verified address", an allowlist): folding there lets a look-alike address through.
  * ALLOW decision: ``allow_equal(a, b)`` is the WHOLE decision. EQUAL only for identical strings (``a == b``, no normalisation, so
    the text you verified is the text you use); VARIANT means a case, width, ligature or whitespace difference only (refuse); LOOKALIKE
    means the strings differ but fold to the same text through homoglyphs or invisible characters (a spoof attempt: refuse and audit it
    as such); DIFFERENT is an ordinary mismatch (refuse). The caller that wants
    case-insensitive domains lowercases the domain itself BEFORE comparing and uses the lowered text afterwards.
  * DENY decision: ``could_be_same_person(a, b)`` (built on ``identity_keys``, the SPELLING VARIANTS below). A scan for a protected value (a
    redaction, a blocklist) looks through every view of the text, BOTH ``fold_views`` AND ``squeeze_views`` (see "MARKS AND SCANS"). ``identity_key``, ``fold`` and ``squeeze`` give ONE
    spelling variant and are NOT DENY comparators or scans: one spelling variant is enough to be stable and to index, never to refuse. ``names_equal`` is
    neither: Unicode compatibility caseless equality for people's names in prose, no look-alikes.

``fold`` (stdlib only, linear):
  1. NFKD, so a base letter and its combining mark separate; 2. U+0345 becomes an iota after a Greek letter and is removed anywhere
  else (spelling variant (b) only; the other spelling variants always remove it, see SPELLING VARIANTS and U+0345 below); 3. drop control (Cc), format (Cf), non-spacing and enclosing mark (Mn, Me), private-use, surrogate and UNASSIGNED (Cn) characters and the
  invisible filler letters, EXCEPT that every whitespace character (``str.isspace``: space, tab, line feed, the line and paragraph separators
  U+2028 and U+2029, the no-break and ideographic spaces) is kept here and becomes a space in step 5; 4. NFKC; 5. every whitespace character becomes a space so words are never
  joined; 6. every Unicode decimal digit becomes an ASCII digit; 7. look-alike letters become the Latin letter or digit. Case is kept
  unless ``casefold`` is set (then ``casefold`` runs just BEFORE step 7, see below); ``collapse_ws`` squeezes runs of whitespace.

The look-alike table (step 7) is GENERATED from the Unicode UTS #39 ``confusables.txt`` MA table, version 15.1.0 (the Unicode version of the
pin; the generator refuses any other version), by ``tools/gen_confusables.py`` (pinned sha256, version and date in ``guard/_confusables.py``)
plus 16 explicit supplementary letters, one explicit override (the Cyrillic palochka U+04CF reads as ``l``, see the generator) and the
Unicode-name rules of the generator, all listed in the generator. NAME RULES COVER: small capitals, negative circled and negative squared letters, the crossed negative squared P, regional indicator letters, the squared small d, Latin letters with a stroke, hook or similar mark, and the circled, negative circled, double circled and sans-serif digits and numbers (0 to 10); the circled numbers 11 to 20 are read by NFKC, the negative circled numbers 11 to 20 are not read (a named gap). A look-alike letter that Unicode
listed only after 15.1.0 is NOT in the table. Runtime is stdlib only; the data file is not shipped. ``FOLD_VERSION`` names the fold that made
a check name. What is NOT read as an ASCII letter or digit is listed in ``tests/test_textnorm.py`` (``KNOWN_NAME_GAPS``) with the reason.

SPELLING VARIANTS. One spelling variant is not enough for a DENY: the same text can LOOK like two different words. A Greek
capital Eta looks like the Latin H, but the case-symmetric check name reads it as the small eta, which looks like n; a Greek letter followed by
U+0345 looks like the letter, but the iota rule reads it as the letter plus ``i``. So a text has a small FIXED SET of spelling variants (at most
three, never more; the number does not grow with the text), ``identity_keys(raw)``, in this order:
  (a) the lower-side spelling variant: case folded first, the look-alike table of the case-fold image, U+0345 ALWAYS dropped;
  (b) the iota spelling variant: as (a), but U+0345 becomes an iota after a Greek letter. This is ``identity_key`` and ``fold``: it is what makes the
      precomposed Greek letters with ypogegrammeni case symmetric (see U+0345);
  (c) the upper-side (table-first) spelling variant: the look-alike table runs on the letter as written (capital Eta reads H, capital Mu M, capital Nu
      N, capital Upsilon Y), then case is folded, then the table of the case-fold image; U+0345 dropped.
``could_be_same_person`` and ``allow_equal`` (LOOKALIKE) compare spelling variants: two texts match when ANY spelling variant of one equals ANY
spelling variant of the other. A scan holds a protected value when ANY view of the text (``fold_views``, ``squeeze_views``) holds ANY view of the
value. The spelling variants only add matches to (b), so the relation is never narrower than ``identity_key`` equality; it is NOT transitive (capital Eta + "oward"
matches "howard" through (c) and "noward" through (a), and those two do not match each other), so it is never a unique index, a dedupe or a
group-by: use ``identity_key`` equality there. The size cap is checked first, once, for every spelling variant and view.

IDEMPOTENT AND CASE-SYMMETRIC BY CONSTRUCTION (``identity_key``, ``could_be_same_person``, ``squeeze``; the spelling variants (a) and (b)). Running the look-alike table
first and then ``casefold`` with a table keyed by lower-case letters is neither: ``identity_key("Ø")`` would keep the capital and ``identity_key("ø")``
would give ``o``, so ``could_be_same_person("BØB", "bob")`` would be False, a DENY bypass. Now, with P = NFKC after the drops after the U+0345 step after
NFKD, D = the digit table and C = ``casefold``: ``key(x) = tag + collapse(E(C(D(P(x)))))`` where E is the look-alike table MOVED ONTO THE CASEFOLD IMAGE
(``_CF_TABLE``): for every table entry whose source ``s`` has ``casefold(s)`` a single character, ``E[casefold(s)] = value.casefold()``;
when two sources reach one casefolded letter the entry of the letter that is its own case-fold wins over the entry of its capital
(11 letters, pinned by a test: e.g. Greek eta reads n, not the capital Eta's H; the spelling variant (c) gives the capital's entry, and
``has_mixed_script`` is a second backstop). The
argument: (1) CASE SYMMETRY: C is the only case-sensitive step, it runs before E, E has casefolded table keys only, so two texts that agree
after C agree in the check name; that ``C(P(c.upper())) == C(P(c.lower()))`` for every character is a fact about the Unicode data, which
``tests/test_textnorm.py`` checks for ALL non-surrogate code points (and for pairs built from the table, and for seeded random strings)
on every supported Unicode version, with the one stated exemption of U+0345 below. (2) IDEMPOTENCE: the image of E is lower-case ASCII; every other character of the result survived C and is not a check name of E
(the table keys of E are non-ASCII and casefold-stable, asserted), so a second C changes nothing and a second E changes nothing; that the
remaining steps (P, D, the drops) leave such characters alone is again a fact about the data, checked by the same tests. The final
form is therefore a fixed point of the whole function; a test that restores the old order fails. ``fold`` WITHOUT
``casefold`` keeps case and uses the raw table (no symmetry is promised for it); ``squeeze`` casefolds first.

U+0345 (COMBINING GREEK YPOGEGRAMMENI). Every other mark is dropped, and dropping is what
makes ``identity_key(x + mark) == identity_key(x)``. U+0345 is the one mark that cannot simply be dropped: its upper case and its case fold
are the letter iota, and a Greek letter with the mark (U+1FB3, alpha with ypogegrammeni) upper-cases to two letters (alpha, iota). Two
needs conflict: case symmetry (the check name of U+1FB3 must be the check name of its upper case, alpha iota) and mark insertion (the check name of
"admin" + U+0345 must be the check name of "admin"). The rule: U+0345 is read as an iota (U+03B9, then the table: ``i``) when the last kept
character before it is a Greek letter (an alphabetic character whose Unicode name starts with GREEK; characters the fold drops, such as other
marks or a zero-width space, are skipped when looking) and is REMOVED everywhere else (after a Latin or any other letter, after a space,
at the start). It happens on the NFKD text, so the precomposed U+1FB3 and alpha + U+0345 get one check name (``ai``). Case-folding the raw text
before the drop step would turn U+0345 into an iota everywhere ("admin" + U+0345 would give ``admini``, a DENY
bypass), so there is no early case fold (it is redundant once U+0345 is handled by name: 600,000 random strings gave the same check name
with and without it). The rule was chosen for the SINGLE check name over "always drop" because always dropping breaks case symmetry for the precomposed Greek letters with
ypogegrammeni and for Greek text in capitals (U+1FB3 against alpha, iota in capitals), while this rule breaks nothing on them. But the single
check name alone is not safe: a Greek look-alike plus U+0345 ("alpha U+0345 dmin") reads as ``aidmin``, one invisible mark away from
"admin", and a run of marks gives a run of ``i``. The spelling variants fix it: (a) and (c) ALWAYS drop the mark, so for ``could_be_same_person`` and for every
scan "a Greek letter + U+0345" matches the letter, whatever follows, and the iota spelling variant (b) is kept for the case symmetry above.
What the single check name does NOT promise, both stated and tested: (1) after a Greek letter the mark is an iota, so ``identity_key(alpha + U+0345)``
is not ``identity_key(alpha)`` (the one "base + mark" pair that differs; ``could_be_same_person`` of the two is True through (a)); (2) a text that holds
a U+0345 with NO Greek letter before it (dropped characters skipped) is not case symmetric, because ``str.upper`` turns the mark into the
letter Iota while the fold removes it (``identity_key("ͅ")`` is ``""``, ``identity_key("Ι")`` is ``i``): the symmetry tests exempt
exactly that shape, nothing wider. No other code point is exempt from idempotence, case symmetry or mark insertion. ``fold`` without
``casefold`` applies the same step.

NO BOUNDED-PASS LOOP: ``fold`` is one pass per spelling variant and nothing loops to a fixed point (a later package that adds a bounded loop adds
its constant and its fail-closed error with it). The idempotence above is by construction and by test, not by iterating.

UNICODE DATA VERSION: the fold depends on the interpreter's Unicode data (which characters are unassigned, which are marks). The pinned version
is ``defaults.TEXTNORM_PINNED_UNIDATA`` (15.1.0). PRODUCTION AND PILOT MUST RUN PYTHON 3.13.x (Unicode 15.1.0); Python 3.12 (Unicode 15.0.0)
is for demos only. Moving the pin to a later Python (for example 3.14) is a DATA MIGRATION: new look-alike data, new golden hashes, a new
algorithm id. Nothing here checks the version until a caller calls ``require_pinned_unidata()``, which raises ``UnidataMismatch`` (fail closed)
when the interpreter's version is not the pin; pilot and prod code must call it before using any check name or view (the application
start-up of the package that wires this module in). A scan view (``fold_views``, ``squeeze_views``) carries NO tag: only ``identity_key`` does. On another
interpreter (a demo run, or a CI run on Python 3.12, which has Unicode 15.0.0) the functions still run, and every check name then starts with
``key_tag()``: U+E000, ``alg=<algorithm id>|ud=<this interpreter's version>``, U+E000. U+E000 is private use, which the fold
always drops, so no check name made on the pinned version can ever start with it: a check name made on another version never equals one made on the
pinned version, and two other versions never equal each other. On the pinned version the tag is empty (the bare check name IS the check name of
the current algorithm id; changing the pin changes the id). ``identity_key`` of a text that already starts with the tag of this interpreter
removes it first, so the function is idempotent there too. The cost, stated and tested: a RAW text that starts with the tag of THIS
interpreter (typed exactly, U+E000 included) has the tag stripped and so gets the same check name as the text without it (an over-collision,
the safe side of a DENY); a text that starts with the tag of ANOTHER version is not stripped (its tag text becomes part of the check name). A
caller that did not call ``require_pinned_unidata()`` (nothing in this package does) gets tagged check names on every
interpreter whose Unicode data is not the pin, for example Python 3.12; such check names compare only with check names made on the same version.
A vendored copy of the Unicode character data (instead of the interpreter's) becomes the alternative when a deployment must run a Python
whose Unicode version is not the pin and cannot be changed.

MARKS AND SCANS. Three categories are NOT dropped by the spelling variants of ``fold``, on purpose, and a caller must know it:
  * Mc (spacing combining marks, 452 code points in Unicode 15.1.0, for example the Devanagari vowel signs aa and i): a spacing vowel sign
    changes a name, so the spelling variants keep it. "ad" + U+0903 + "min" is NOT the check name of "admin", and the spelling-variant views of
    ``fold_views`` of "pass" + U+093E + "word" do NOT hold "password".
  * Lm (modifier letters): a look-alike of the letter (superscript h reads as h), kept or read as that letter.
  * Sk (modifier symbols): a compatibility Sk (NFKD gives a space plus a mark: the diaeresis U+00A8, the small tilde U+02DC) becomes a space in
    the spelling-variant views; every other Sk (the grave accent U+0060, the circumflex U+005E, the arrow head U+02C2) is kept as the symbol. ``squeeze_views`` removes both.
  So that a mark inserted into a protected value cannot hide it, ``fold_views`` and ``squeeze_views`` return, besides the spelling-variant
  views, the same views built from the text with every Mc, Lm and Sk character REMOVED BEFORE the first normalisation and before the
  look-alike table (so an Lm or Mc that the table or NFKC would read as a letter is gone too: "pass" + U+0C02 + "word" holds "PASSWORD"). Every
  other drop (Mn, Me, format, control and the rest) already applies to every view. These marks-dropped views keep every script and every letter.
  "No exemption" holds for INSERTION only: a mark ADDED to the value is found for every Mc, Lm and Sk code point, with no exemption list. It does
  NOT hold for a modifier letter that REPLACES a letter AND another one inserted in the same text ("pa" + superscript s + "s" + superscript h + "word": the
  marks-dropped views lose the letter that the first modifier stood for, the other views read the inserted one as a letter): that mixed case is
  NOT caught, it is pinned as a limit by a test, and a caller who must catch it needs its own rule.
  At most six views per call of ``squeeze_views`` (three spelling variants, each with and without the marks); ``fold_views`` adds the script views below, so
  at most nine.
  THE RULE FOR A SCAN (redaction, blocklist, has-secret): look through BOTH ``fold_views`` AND ``squeeze_views`` and take the views of the
  protected value the same way (a scan holds a value when ANY view of the text holds ANY view of the value), PASS ``casefold=True, collapse_ws=True`` to
  ``fold_views`` (its default is ``False`` for the display and comparison uses that keep case: a scan built without it misses a value that
  differs from the text by case alone, "Secret" against "SECRET"), and take the needles of the value with ``scan_needles``, which refuses a view
  shorter than ``defaults.TEXTNORM_MIN_VIEW_CHARS`` (see below). ``tests/test_textnorm.py`` pins the insertion rule for EVERY Mc, Lm and Sk code point of the interpreter.
  WHAT A SCAN RELIES ON: A value with NO ASCII letter or digit (Chinese, Arabic, Hindi, Thai) is found by the script views of ``fold_views`` (the non-ASCII letters and marks of the text, with whitespace, punctuation, symbols and ASCII characters removed), so an inserted space, hyphen, line break, ASCII letter or mark does not hide it; an inserted look-alike letter of that script, or a respelling of it, is not covered.
  SCRIPT VIEWS (``fold_views`` only). The ASCII-only ``squeeze_views`` is ``""`` for a value in a script with no ASCII letter or digit, so ``fold_views`` also returns,
  for the marks-dropped spelling variants, the SCRIPT VIEW: the view with every character removed that is not a non-ASCII letter or mark (whitespace,
  punctuation, symbols, ASCII letters and digits; the digits of other scripts were turned into ASCII digits before and go too). A view that would be empty is left out, and a script view
  equal to another view is not repeated. A scan of a value in Chinese, Hindi or Thai therefore needs the script view of the TEXT to hold the script view of the
  value. It over-matches on purpose (the safe side): a value with ASCII letters AND a script has a script view of the script part alone, which
  any text with that script part holds, and two words of a text that end and begin with the value's letters match across a separator.
  MINIMUM VIEW LENGTH: ``defaults.TEXTNORM_MIN_VIEW_CHARS`` (2), the SAME number for every view (spelling variant, marks-dropped, script and squeeze
  views). An empty needle is found in every text and a one-character needle in most, so ``scan_needles(raw)`` returns the views of a protected value
  that reach the minimum (from ``fold_views`` with ``casefold=True, collapse_ws=True`` and from ``squeeze_views``) and raises ``ViewTooShort`` when none does. A caller
  that scans must use it (P1b: the redaction package takes its needles from ``scan_needles`` and does not repeat the number). The match positions of the original text are lost by the drops: a caller that
  must cut the original text needs its own map.

INPUT RULES (every public function): the argument must be a plain ``str`` (``type(x) is str``; a ``str`` subclass or an enum member is
refused with ``NotText``), its LENGTH must be within ``defaults.TEXTNORM_MAX_CHARS`` (``TextTooLong``, checked first: every weight is at
least the length, so a longer text is refused before any per-character work), and its WEIGHT W must be within the same cap. W is the sum, over the
characters of the text, of the longest string the pipeline makes from that one character (an ASCII text has W = its length). No check name
or view of any spelling variant is longer than W of its text (plus ``len(key_tag())`` on an unpinned interpreter), because every step acts per
character or only joins or drops. Messages hold lengths and constants, never the input.
Any ``TextnormError`` on a DENY or ALLOW path means REFUSE.

Honest limits: a letter in neither the data nor the supplement nor a name rule is not folded (the known cases are listed in ``tests/test_textnorm.py``). Dropping unassigned code points (Cn) depends on the
Python build's Unicode version (``require_pinned_unidata``): a look-alike letter assigned after Unicode 15.1 is DROPPED, not folded, on the
pinned interpreter. PUNCTUATION is not folded: the Unicode hyphen (U+2010) and the other dashes, the minus sign
(U+2212), the division slash (U+2215) and the right single quotation mark (U+2019) are not read as the hyphen-minus, the slash and the
apostrophe, so "INV-2026" and "INV" + U+2212 + "2026" are different, and so are "O'Brien" and "O" + U+2019 + "Brien" in ``could_be_same_person``
(corpus rows r114 to r117, strict expected failures). ``has_mixed_script`` is the fail-closed backstop: a word that mixes Latin
with Cyrillic, Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu or another look-alike-rich script is a deny signal whatever the
table knows. Property: ``fold(x + mark) == fold(x) == fold(mark + x)`` for any non-spacing or enclosing mark (Mn, Me), format, control,
private-use, surrogate or unassigned character (the nine dropped categories), with the one exception above (U+0345 after a Greek letter, for
the single spelling variant (b) only); for the spelling variants, any such mark, U+0345 included, leaves a shared spelling variant
(``could_be_same_person(x + mark, x)``). The property does NOT hold for a spacing mark (Mc), a modifier letter (Lm) or a modifier symbol (Sk) in the
spelling variants; the marks-dropped views of ``fold_views`` and ``squeeze_views`` hold it for those.
"""

from __future__ import annotations

import hashlib
import re
import sys
import types
import unicodedata
from collections import Counter
from enum import Enum

from hadavin_sdk import defaults
from hadavin_sdk.guard import _confusables
from hadavin_sdk.guard._confusables import TABLE as _CONFUSABLES

__all__ = [
    "FILLERS",
    "FOLD_VERSION",
    "AllowVerdict",
    "NotText",
    "TextTooLong",
    "TextnormError",
    "UnidataMismatch",
    "ViewTooShort",
    "allow_equal",
    "could_be_same_person",
    "fold",
    "fold_views",
    "has_hidden_channel",
    "has_mixed_script",
    "identity_key",
    "identity_keys",
    "key_tag",
    "names_equal",
    "require_pinned_unidata",
    "scan_needles",
    "squeeze",
    "squeeze_views",
]


class TextnormError(Exception):
    """Base of the errors of this module. It is NOT a ``ValueError`` or a ``TypeError``: a DENY caller that does
    ``except ValueError:`` must not swallow it. On any DENY or ALLOW path any ``TextnormError`` means REFUSE."""


class TextTooLong(TextnormError):
    """The weight of a text is over ``defaults.TEXTNORM_MAX_CHARS`` (see the module docstring)."""


class NotText(TextnormError):
    """The argument is not a plain ``str`` (a ``str`` subclass and an enum member are refused too)."""


class ViewTooShort(TextnormError):
    """No view of a protected value reaches ``defaults.TEXTNORM_MIN_VIEW_CHARS`` (``scan_needles``). Refuse to scan with the value: a needle that short is found in nearly every text."""


class UnidataMismatch(TextnormError):
    """The interpreter's Unicode data is not the version the check names were pinned to (``require_pinned_unidata()``). Fail closed: the caller must refuse to run, not fall back."""


_PINNED_PYTHON = "3.13"  # the Python minor version that carries Unicode 15.1.0 (the pin); only used in the message
_DROP_CATEGORIES = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"})
_SPACING_CATEGORIES = frozenset(
    {"Mc", "Lm", "Sk"}
)  # kept by the spelling variants, removed by the marks-dropped views of a scan
FILLERS = frozenset(
    map(chr, (0x3164, 0x115F, 0x1160, 0x2800, 0xFFA0, 0x13441, 0x13442))
)  # invisible letters/symbols used to glue or split words (the last two: Egyptian hieroglyph full blank and half blank)
_LOOKALIKES = types.MappingProxyType({chr(c): v for c, v in _CONFUSABLES.items()})
_TABLE = types.MappingProxyType(dict(_CONFUSABLES))


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


_CF_TABLE = types.MappingProxyType(_build_cf_table(_CONFUSABLES))
_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_LOOSE = types.MappingProxyType(
    str.maketrans("OILSBZGQ", "01158269")
)  # letters an attacker writes for digits


def _table_digest(table: types.MappingProxyType[int, str]) -> str:
    """SHA-256 of the table as lines ``f"{cp:06X}:{value}\\n"`` in ascending code point order, UTF-8 (as the generator writes it)."""
    lines = "".join(f"{cp:06X}:{table[cp]}\n" for cp in sorted(table))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


# Which fold made a check name: ``alg`` is bumped BY HAND in the pull request that changes what a check name can be (the golden file shows the change),
# ``tbl`` is the first 12 hex characters of the digest of the in-memory table and its entry count, ``ucd`` the UTS #39 data version,
# ``ud`` the interpreter's Unicode version. Nothing stores a check name in v1.
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


_DIGITS = types.MappingProxyType(
    _build_digit_table()
)  # built once at import: no lazy fill, so no thread can see a half-filled table


def _char_weight(c: str) -> int:
    """The weight of ``c``: the larger of the single-pass weight of ``c`` and of its case fold (the case-folding path folds case first)."""
    return max(_pass_weight(c), _pass_weight(c.casefold()))


def _pass_weight(c: str) -> int:
    """The longest string the pipeline makes from the character ``c``: after NFKD, after NFKC, after the digit and look-alike tables and after
    the case fold with the table of its image (drops only shorten, so they are left out: an upper bound). The upper-side spelling variant, which runs the
    table, then the case fold, then the table of the image, is never longer than the longest of these for any code point;
    ``test_identity_keys_and_could_be_same_person_hold_for_every_code_point_*`` checks that for all of them."""
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
    """The two input rules, in one place: every argument, left to right, is a plain ``str`` and has a weight within the cap. Every
    weight is at least the length, so a text LONGER than the cap is refused from its length alone, BEFORE any per-character work."""
    for text in texts:
        if type(text) is not str:
            raise NotText("a text must be a plain str (a subclass or an enum member is refused)")
        if len(text) > defaults.TEXTNORM_MAX_CHARS:
            raise TextTooLong(
                f"the text is too long: {len(text)} of {defaults.TEXTNORM_MAX_CHARS} allowed"
            )
        weight = _weight(text)
        if weight > defaults.TEXTNORM_MAX_CHARS:
            raise TextTooLong(
                "the text is too long once look-alike letters are expanded: "
                f"{weight} of {defaults.TEXTNORM_MAX_CHARS} allowed"
            )


# COMBINING GREEK YPOGEGRAMMENI: the only mark whose case fold is a letter (iota); see "U+0345" in the module docstring
_YPOGEGRAMMENI = "\u0345"
_IOTA = "\u03b9"


def _is_greek_letter(ch: str) -> bool:
    """A letter whose Unicode name starts with GREEK: the Greek and Coptic block, Greek Extended and the few Greek letters elsewhere
    (U+1D26 to U+1D2A, U+AB65). Coptic letters are not Greek here."""
    return ch.isalpha() and unicodedata.name(ch, "").startswith("GREEK ")


def _kept(ch: str) -> bool:
    """True for a character the drop step keeps (whitespace is kept and later becomes a space)."""
    return ch.isspace() or (unicodedata.category(ch) not in _DROP_CATEGORIES and ch not in FILLERS)


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


# The SPELLING VARIANTS (module docstring): a text is read at most three ways, a fixed set. Each is (iota rule, table first):
# (a) lower side, U+0345 always dropped; (b) lower side, U+0345 an iota after a Greek letter (this is ``identity_key``);
# (c) upper side: the look-alike table runs on the letter as written, then case is folded, then the table of the case-fold image;
# U+0345 dropped. A fourth spelling variant is a change of the algorithm id and of the tests that pin three.
_READINGS = (
    (False, False),
    (True, False),
    (False, True),
)


def _without_spacing_marks(text: str) -> str:
    """``text`` without any Mc, Lm or Sk character. It runs on the RAW text, before the first normalisation: NFKD and NFKC read a modifier
    letter such as U+02B0 as the letter h, so a mark must be gone before they run."""
    return "".join(ch for ch in text if unicodedata.category(ch) not in _SPACING_CATEGORIES)


def _script_view(view: str) -> str:
    """The SCRIPT VIEW of a view: only the non-ASCII letters and marks stay. Whitespace, punctuation, symbols, ASCII letters and digits (and the
    digits of other scripts, which are ASCII by now) are removed, so a separator or an ASCII letter inserted into a value in a script with no
    ASCII letter or digit cannot hide it."""
    return "".join(
        ch
        for ch in view
        if not ch.isascii() and (ch.isalpha() or unicodedata.category(ch)[0] == "M")
    )


def _prefix(nfkd: str, *, iota: bool, marks: bool = False) -> str:
    """The spelling variant-independent steps on an NFKD text: U+0345 (an iota after a Greek letter when ``iota``, otherwise it is dropped like any
    mark), the drops (with ``marks``, also every Mc, Lm and Sk character), whitespace, NFKC and the digits."""
    s = _subscript_iota(nfkd) if iota else nfkd
    s = "".join(
        " " if ch.isspace() else ch
        for ch in s
        if _kept(ch) and not (marks and unicodedata.category(ch) in _SPACING_CATEGORIES)
    )
    s = unicodedata.normalize("NFKC", s)
    return s.translate(_DIGITS)


def _finish(s: str, *, casefold: bool, table_first: bool, collapse_ws: bool) -> str:
    # casefold BEFORE the table and use the table moved onto the casefold image: idempotent and case-symmetric (module docstring);
    # table first is the spelling variant by the letter's own case (capital Eta reads h)
    if not casefold:
        s = s.translate(_TABLE)
    elif table_first:
        s = s.translate(_TABLE).casefold().translate(_CF_TABLE)
    else:
        s = s.casefold().translate(_CF_TABLE)
    return " ".join(s.split()) if collapse_ws else s


def _fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    """ONE spelling variant, the iota spelling variant (b): what ``fold`` and ``identity_key`` return."""
    prefix = _prefix(unicodedata.normalize("NFKD", raw), iota=True)
    return _finish(prefix, casefold=casefold, table_first=False, collapse_ws=collapse_ws)


def _views(
    raw: str,
    *,
    casefold: bool,
    collapse_ws: bool,
    marks_dropped: bool = False,
    script: bool = False,
) -> tuple[str, ...]:
    """Every spelling variant of ``raw`` as a string, without repeats, in the order of ``_READINGS``. Without ``casefold`` there is no upper side
    (the table already runs on the letter as written), so only (a) and (b) remain. With ``marks_dropped`` the same spelling variants of the
    text WITHOUT its Mc, Lm and Sk characters follow (a scan wants them; the DENY check names do not use them): at most twice as many views.
    With ``script`` the SCRIPT VIEW of each of those follows it (``_script_view``; left out when empty or already there): at most three times as many."""
    texts = [raw]
    if marks_dropped:
        texts.append(_without_spacing_marks(raw))
    views: list[str] = []
    for marks, text in enumerate(texts):
        nfkd = unicodedata.normalize("NFKD", text)
        with_iota = _prefix(nfkd, iota=True, marks=bool(marks))
        prefixes = {
            True: with_iota,
            False: _prefix(nfkd, iota=False, marks=bool(marks))
            if _YPOGEGRAMMENI in nfkd
            else with_iota,
        }
        for iota, table_first in _READINGS:
            if table_first and not casefold:
                continue
            view = _finish(
                prefixes[iota], casefold=casefold, table_first=table_first, collapse_ws=collapse_ws
            )
            if view not in views:
                views.append(view)
            if script and marks:
                only = _script_view(view)
                if only and only not in views:
                    views.append(only)
    return tuple(views)


def fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    """ONE spelling variant of ``raw`` (the iota spelling variant, see the module docstring), NOT a scan or a DENY comparator: a scan uses ``fold_views``. Linear in
    the weight of ``raw``, which is bounded first."""
    _checked(raw)
    return _fold(raw, casefold=casefold, collapse_ws=collapse_ws)


def fold_views(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> tuple[str, ...]:
    """Every view of ``raw`` for a SCAN: a redaction or a blocklist looks for the secret in EVERY view of the text (module docstring, "MARKS AND SCANS").
    The views are the spelling variants of ``raw`` (at most three: two without ``casefold``; ``fold(raw, ...)`` is one of them), then the same
    spelling variants of ``raw`` with every spacing mark (Mc), modifier letter (Lm) and modifier symbol (Sk) removed before the first
    normalisation (all scripts are kept), then the SCRIPT VIEW of each of those (non-ASCII letters and marks only; left out when empty or repeated).
    At most nine views (six without ``casefold``), none repeated. A secret hidden by inserting such a mark is found in the
    marks-dropped views.

    THE RULE FOR A SCAN: pass ``casefold=True`` (and ``collapse_ws=True``). The default ``False`` keeps the case of the text (the display and comparison callers want that), so a scan
    built without it misses "SECRET" when the protected value is "secret". A redaction MUST ALSO scan ``squeeze_views`` (the ASCII letters and digits with
    every separator removed) and take its needles with ``scan_needles``.

    A value with NO ASCII letter or digit (Chinese, Arabic, Hindi, Thai) is found by the script views of ``fold_views`` (the non-ASCII letters and marks of the text, with whitespace, punctuation, symbols and ASCII characters removed), so an inserted space, hyphen, line break, ASCII letter or mark does not hide it; an inserted look-alike letter of that script, or a respelling of it, is not covered."""
    _checked(raw)
    return _views(raw, casefold=casefold, collapse_ws=collapse_ws, marks_dropped=True, script=True)


def scan_needles(raw: str, *, loose: bool = False) -> tuple[str, ...]:
    """The needles of a PROTECTED VALUE ``raw`` for a scan: every view of ``fold_views(raw, casefold=True)`` and of ``squeeze_views(raw, loose=loose)``
    that has at least ``defaults.TEXTNORM_MIN_VIEW_CHARS`` characters (the same number for every view), without repeats. A view shorter than
    that, an empty one above all, is not a needle: it is found in every text. Raises ``ViewTooShort`` when no view reaches the minimum (the
    value is empty, invisible, one character or a script with no letters): the caller must REFUSE to scan with that value. The text to scan
    is read with ``fold_views(text, casefold=True, collapse_ws=True)`` and ``squeeze_views(text, loose=loose)``; it holds the value when any of those views
    contains any needle."""
    _checked(raw)
    minimum = defaults.TEXTNORM_MIN_VIEW_CHARS
    needles: list[str] = []
    for view in (
        *fold_views(raw, casefold=True, collapse_ws=True),
        *squeeze_views(raw, loose=loose),
    ):
        if len(view) >= minimum and view not in needles:
            needles.append(view)
    if not needles:
        raise ViewTooShort(
            f"no view of the value has {minimum} characters or more: refuse to scan with it"
        )
    return tuple(needles)


def squeeze(raw: str, *, loose: bool = False) -> str:
    """Check name for a scan on letters and digits: folded, upper-case letters and digits only; ``loose`` also treats the digit-like letters O I L S B Z G Q as the
    digits 0 1 1 5 8 2 6 9. The result is ``""`` for a text without an ASCII letter or digit after the fold (a name in Chinese or Hindi, for
    example): an empty needle matches every text, so a caller must REFUSE an empty result, never scan with it."""
    _checked(raw)
    s = _fold(raw, casefold=True).upper()
    if loose:
        s = s.translate(_LOOSE)
    return _NON_ALNUM.sub("", s)


def squeeze_views(raw: str, *, loose: bool = False) -> tuple[str, ...]:
    """Every view of ``raw`` squeezed as ``squeeze`` does (at most six, none repeated): the views a scan on letters and digits looks through.
    They are the spelling variants (at most three; ``squeeze(raw, loose=loose)`` is one of them) and the same spelling variants of ``raw`` with
    every spacing mark (Mc), modifier letter (Lm) and modifier symbol (Sk) removed BEFORE the first normalisation and before the look-alike table,
    so "pass" + U+0C02 + "word" holds ``PASSWORD`` (the table would read U+0C02 as the letter o). A view is ``""`` for a text without an ASCII letter or
    digit after the fold: an empty needle matches every text, so a caller must REFUSE an empty view of a protected value, never scan with it. A
    scan reads these views AND ``fold_views`` (module docstring, "MARKS AND SCANS")."""
    _checked(raw)
    out: list[str] = []
    for view in _views(raw, casefold=True, collapse_ws=False, marks_dropped=True):
        s = view.upper()
        if loose:
            s = s.translate(_LOOSE)
        s = _NON_ALNUM.sub("", s)
        if s not in out:
            out.append(s)
    return tuple(out)


def key_tag() -> str:
    """``""`` on the pinned Unicode version; otherwise U+E000 + ``alg=<alg>|ud=<this interpreter's Unicode version>`` + U+E000, which
    ``identity_key`` puts in front of its check name so a check name made on another version never equals a check name made on the pinned one. Read at call
    time. U+E000 is private use: the fold drops it, so no untagged key can start with the tag."""
    version = unicodedata.unidata_version
    if version == defaults.TEXTNORM_PINNED_UNIDATA:
        return ""
    return f"\ue000alg={_ALG}|ud={version}\ue000"


def _canon(s: str) -> str:
    """Unicode compatibility caseless matching: NFKD, case fold, NFKD, case fold; a case fold of a composed letter can leave a
    sequence that normalises again, which is why Unicode writes it with two folds. The second fold is kept because the standard has it; on
    Unicode 15.0 and 15.1 it changes no result for any single code point (checked), so no test can tell it from a single fold. What the
    tests do pin is the NFKD step against the old NFKC (nine code points were not case symmetric). Whitespace is collapsed."""
    folded = unicodedata.normalize("NFKD", unicodedata.normalize("NFKD", s).casefold()).casefold()
    return " ".join(unicodedata.normalize("NFKD", folded).split())


def identity_key(raw: str) -> str:
    """ONE spelling variant of ``raw``, NOT a DENY comparator: ``fold`` with case folded and whitespace collapsed (the iota spelling variant, see the module
    docstring). Stable and idempotent, so it stays the check name to keep and to index; but a DENY decision compares ``identity_keys`` (``could_be_same_person``).
    The empty string and invisible-only text give ``""`` on the pinned Unicode version (never a value to store or index). On another version
    the check name starts with ``key_tag()``."""
    _checked(raw)
    tag = key_tag()
    if tag and raw.startswith(tag):
        # already a check name of this interpreter: the function stays idempotent
        raw = raw[len(tag) :]
    return tag + _fold(raw, casefold=True, collapse_ws=True)


def _keys(raw: str) -> tuple[str, ...]:
    tag = key_tag()
    if tag and raw.startswith(tag):
        raw = raw[len(tag) :]
    return tuple(tag + view for view in _views(raw, casefold=True, collapse_ws=True))


def identity_keys(raw: str) -> tuple[str, ...]:
    """The check names of ``raw`` for a DENY decision: one per spelling variant (at most three, no repeats, a fixed order: (a), (b), (c) of the module
    docstring). ``identity_key(raw)`` is one of them. Two texts match when ANY key of one equals ANY key of the other
    (``could_be_same_person``). Not transitive, so never a unique index or a group-by: use ``identity_key`` for those."""
    _checked(raw)
    return _keys(raw)


def could_be_same_person(a: str, b: str) -> bool:
    """DENY comparator (separation of duties, a blocklist): True when ANY spelling variant of ``a`` equals ANY spelling variant of ``b`` (``identity_keys``).
    Look-alike letters, case, width, ligatures, non-spacing and enclosing marks (Mn, Me) and invisible characters compare equal, which is the safe side
    for a DENY. NOT equal: a spacing mark (Mc), modifier letter (Lm) or modifier symbol (Sk) inserted into a name makes it "different" (a scan
    uses ``fold_views`` and ``squeeze_views``, which do remove them), and PUNCTUATION is not folded: "O'Brien" against "O" + U+2019 + "Brien", and a
    Unicode hyphen (U+2010) against "-", compare as different (strict expected failures, corpus rows r114 to r117). Not transitive. NEVER an ALLOW."""
    _checked(a, b)
    return not set(_keys(a)).isdisjoint(_keys(b))


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
    # any spelling variant of one equals any spelling variant of the other
    if could_be_same_person(a, b):
        return AllowVerdict.LOOKALIKE
    return AllowVerdict.DIFFERENT


def names_equal(a: str, b: str) -> bool:
    """People's names in prose: NFKC, case and whitespace insensitive. NOT an ALLOW decision (``allow_equal``) and NOT a DENY decision
    either (``could_be_same_person``: this one does not fold look-alikes, so a Cyrillic-a name is a different name here). Never stored, never a check name."""
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
    """GUARD ENTRY POINT for pilot and prod (the application start-up of the package that wires this module in calls it): raise ``UnidataMismatch`` unless the interpreter's Unicode data
    version is ``expected`` (default ``defaults.TEXTNORM_PINNED_UNIDATA``, read when the function runs, so a patched constant is seen).
    Fail closed: it never warns and never returns on a mismatch. A demo run or a CI run may use another version; their keys carry
    ``key_tag()``. The message says what to do: for the pin it names Python 3.13."""
    if expected is None:
        expected = defaults.TEXTNORM_PINNED_UNIDATA
    if unicodedata.unidata_version != expected:
        fix = (
            f"run Python {_PINNED_PYTHON} (Unicode {expected})"
            if expected == "15.1.0"
            else f"run a Python with Unicode {expected}"
        )
        raise UnidataMismatch(
            f"this Python uses Unicode {unicodedata.unidata_version}; {fix} for pilot or prod"
        )


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
