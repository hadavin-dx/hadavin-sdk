"""ONE text fold for every place that compares or scans text for a protected value.

Used by ``guard.egress_text`` (output check) and ``approvals.gate`` (secret views); a demo or kind that needs a
comparison key imports ``fold`` / ``squeeze`` from here instead of keeping its own table.

``fold`` (all stdlib, one pass per step, O(n)):
  1. NFKD, so a base letter and its combining mark separate; 2. drop control, format, combining-mark,
  line/paragraph-separator, private-use and surrogate characters and the invisible filler letters; 3. NFKC; 4. every Unicode whitespace character
  (``str.isspace``: NEL, U+001C..U+001F, U+2028, no-break space and the rest) becomes a space (words are never joined); 5. every Unicode decimal digit becomes an ASCII digit;
  6. look-alike letters (a table of Cyrillic, Greek, Armenian and Latin-extended letters that read as Latin ones)
  become the Latin letter. Case is kept unless ``casefold`` is set; ``collapse_ws`` squeezes runs of whitespace to one space and strips the ends.
``identity_fold.fold`` is ``fold(text, casefold=True, collapse_ws=True)``.

Honest limits: the look-alike table is a curated list, not the full Unicode confusables set (that data is not in
the standard library). A letter not in the table is not folded. ``test_textnorm`` pins what the table covers.
Property: ``fold(x + mark) == fold(x)`` for any combining mark or format character.
"""

from __future__ import annotations

import re
import unicodedata

_DROP_CATEGORIES = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs"})
FILLERS = frozenset("ㅤᅟᅠ⠀ﾠ")  # invisible letters/symbols used to glue or split words
_PAIRS = (  # (code points, Latin letters); code points so this file stays ASCII
    ((0x430, 0x435, 0x43E, 0x440, 0x441, 0x445, 0x443, 0x456, 0x455, 0x458, 0x43A, 0x43C, 0x442, 0x43D, 0x432), "aeopcxyisjkmthb"),
    ((0x410, 0x412, 0x415, 0x41A, 0x41C, 0x41D, 0x41E, 0x420, 0x421, 0x422, 0x425), "ABEKMHOPCTX"),
    ((0x405, 0x406, 0x408, 0x423, 0x4AE, 0x4C0, 0x51A, 0x51C), "SIJYYIQW"),
    ((0x4BB, 0x4CF, 0x51B, 0x51D, 0x4AF, 0x501), "hlqwyd"),  # shha, palochka, qa, we, straight u, komi de
    ((0x3BF, 0x3B1, 0x3BD, 0x39F, 0x391, 0x392, 0x395, 0x399, 0x39A, 0x39C, 0x39D, 0x3A1, 0x3A4, 0x3A7, 0x3A5, 0x396, 0x397),
     "oavOABEIKMNPTXYZH"),
    ((0x3B9, 0x3BA, 0x3C1, 0x3C4, 0x3C5, 0x3C7, 0x3F2, 0x3F3, 0x3F9, 0x37F), "ikptuxcjCJ"),  # Greek iota kappa rho tau upsilon chi, lunate sigma, yot
    ((0x3B5, 0x261), "eg"),  # Greek epsilon, Latin script g
    ((0x131, 0x130), "iI"),  # dotless i, dotted capital I
    ((0x585, 0x57D, 0x578, 0x570, 0x555, 0x54D), "ounhOU"),  # Armenian oh, seh, vo, ho
)  # fmt: skip
LOOKALIKES: dict[str, str] = {
    chr(c): a for cps, letters in _PAIRS for c, a in zip(cps, letters, strict=True)
}
_TABLE = {ord(k): v for k, v in LOOKALIKES.items()}
_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_DIGITS = {}  # filled lazily: decimal digit -> ASCII (str.translate speeds the common case)


def _digit_table() -> dict[int, str]:
    if not _DIGITS:
        for cp in range(0x20000):  # every Nd character is below U+20000
            ch = chr(cp)
            if ch.isdecimal() and not ("0" <= ch <= "9"):
                _DIGITS[cp] = str(int(ch))
    return _DIGITS


def fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    """The comparison form of ``raw`` (see the module docstring). Linear in ``len(raw)``; callers bound the length first."""
    s = unicodedata.normalize("NFKD", raw)
    s = "".join(
        " " if ch.isspace() else ch
        for ch in s
        if ch.isspace() or (unicodedata.category(ch) not in _DROP_CATEGORIES and ch not in FILLERS)
    )
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_digit_table()).translate(_TABLE)
    if collapse_ws:
        s = " ".join(s.split())
    return s.casefold() if casefold else s


def squeeze(raw: str, *, loose: bool = False) -> str:
    """Comparison key: folded, upper-case letters and digits only; ``loose`` also treats O/0 and I/L/1 as one character."""
    s = fold(raw).upper()
    if loose:
        s = s.translate(str.maketrans("OIL", "011"))
    return _NON_ALNUM.sub("", s)
