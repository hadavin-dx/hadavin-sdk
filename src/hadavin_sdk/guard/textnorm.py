"""ONE text fold for every place that compares or scans text for a protected value.

Used by ``guard.egress_text`` (output check) and ``approvals.gate`` (secret views); a kind or demo that needs a comparison key
imports ``fold`` / ``squeeze`` from here instead of keeping its own table. Do not use ``fold`` to display or store text: it drops
legitimate marks (Hindi and Thai vowel signs, the breve of Cyrillic short i) and so over-collides, which is the safe side for a DENY.

THE RULE (read before using ``fold``): ``fold`` makes look-alike text EQUAL. That is what a DENY decision wants (separation of
duties: "alice" and the Cyrillic-a "alice" are the same person; a blocklist; a leak scan). It is WRONG for an ALLOW decision ("this
address equals the verified address", an allowlist): folding there lets a look-alike address through.
  * ALLOW decision: ``allow_equal(a, b)`` is the WHOLE decision. EQUAL only for identical strings (``a == b``, no normalisation, so
    the text you verified is the text you use); LOOKALIKE means the strings differ but fold to the same text (a spoof attempt or a
    case/width/ligature variant: refuse, and audit it as such); DIFFERENT is an ordinary mismatch (refuse). The caller that wants
    case-insensitive domains lowercases the domain itself BEFORE comparing and uses the lowered text afterwards.
  * ``names_equal`` is NOT an ALLOW comparison: NFKC, case and whitespace insensitive equality for people's names in prose.

``fold`` (stdlib only, linear):
  1. NFKD, so a base letter and its combining mark separate; 2. drop control, format, combining-mark, private-use, surrogate and
  UNASSIGNED (Cn) characters and the invisible filler letters; 3. NFKC; 4. every Unicode whitespace character (``str.isspace``)
  becomes a space so words are never joined; 5. every Unicode decimal digit becomes an ASCII digit; 6. look-alike letters become the
  Latin letter or digit. Case is kept unless ``casefold`` is set; ``collapse_ws`` squeezes runs of whitespace.

The look-alike table (step 6) is GENERATED from the Unicode UTS #39 ``confusables.txt`` MA table by ``tools/gen_confusables.py`` (pinned
sha256, version and date in ``guard/_confusables.py``) plus 16 explicit supplementary letters and a Unicode-name rule for small capitals, both listed in the generator. Runtime is
stdlib only; the data file is not shipped.

Honest limits: a letter in neither the data nor the supplement is not folded. Dropping unassigned code points (Cn) depends on the
Python build's Unicode version. ``has_mixed_script`` is the fail-closed backstop: a word that mixes Latin with Cyrillic, Greek,
Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu or another look-alike-rich script is a deny signal whatever the table knows. Property:
``fold(x + mark) == fold(x)`` for any combining mark, format or unassigned character.
"""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum

from hadavin_sdk.guard._confusables import TABLE as CONFUSABLES

_DROP_CATEGORIES = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"})
FILLERS = frozenset(
    map(chr, (0x3164, 0x115F, 0x1160, 0x2800, 0xFFA0))
)  # invisible letters/symbols used to glue or split words
LOOKALIKES: dict[str, str] = {chr(c): v for c, v in CONFUSABLES.items()}
_TABLE = dict(CONFUSABLES)
_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_LOOSE = str.maketrans("OILSBZGQ", "01158269")  # letters an attacker writes for digits


def _build_digit_table() -> dict[int, str]:
    return {
        cp: str(int(chr(cp)))
        for cp in range(0x20000)
        if chr(cp).isdecimal() and not ("0" <= chr(cp) <= "9")
    }  # every Nd < U+20000


_DIGITS = (
    _build_digit_table()
)  # built once at import: no lazy fill, so no thread can see a half-filled table


def fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    """The comparison form of ``raw`` (see the module docstring). Linear in ``len(raw)``; callers bound the length first."""
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


def squeeze(raw: str, *, loose: bool = False) -> str:
    """Comparison key: folded, upper-case letters and digits only; ``loose`` also treats the digit-like letters O I L S B Z G Q as the
    digits 0 1 1 5 8 2 6 9."""
    s = fold(raw).upper()
    if loose:
        s = s.translate(_LOOSE)
    return _NON_ALNUM.sub("", s)


def _canon(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", s).casefold().split())


class AllowVerdict(StrEnum):
    EQUAL = "EQUAL"  # identical strings: the only verdict that allows
    DIFFERENT = "DIFFERENT"  # an ordinary mismatch: refuse
    LOOKALIKE = "LOOKALIKE"  # differs but folds equal (homoglyph, case, width, ligature, invisible character): refuse and audit as a spoof


def allow_equal(a: str, b: str) -> AllowVerdict:
    """The whole ALLOW decision for "is this the verified value?": only ``EQUAL`` allows. No normalisation: the comparison is ``a == b``
    so the value that was verified is the value that is used."""
    if a == b:
        return AllowVerdict.EQUAL
    if fold(a, casefold=True, collapse_ws=True) == fold(b, casefold=True, collapse_ws=True):
        return AllowVerdict.LOOKALIKE
    return AllowVerdict.DIFFERENT


def names_equal(a: str, b: str) -> bool:
    """People's names in prose: NFKC, case and whitespace insensitive. NEVER for an ALLOW decision (``allow_equal``): a German sharp-s word equals its "ss" spelling
    here and a fullwidth at-sign equals the ASCII one."""
    return _canon(a) == _canon(b)


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
    letters is flagged. A fail-closed deny signal that does not depend on the look-alike table. Digits and punctuation are script-neutral."""
    kept = "".join(
        ch
        for ch in text
        if ch not in _UNIT_SYMBOLS
        and ch not in FILLERS
        and unicodedata.category(ch) not in _DROP_CATEGORIES
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
