"""ONE text fold for every place that compares or scans text for a protected value.

Used by ``guard.egress_text`` (output check) and ``approvals.gate`` (secret views); a kind or demo that needs a comparison key
imports ``fold`` / ``squeeze`` from here instead of keeping its own table.

THE RULE (read before using ``fold``): ``fold`` makes look-alike text EQUAL. That is what a DENY decision wants (separation of
duties: "alice" and the Cyrillic-a "alice" are the same person; a blocklist; a leak scan). It is WRONG for an ALLOW decision
("this address equals the verified address", an allowlist): folding there lets a look-alike address through. For ALLOW use
``safe_equal`` (exact after NFKC, case and whitespace) and refuse when ``confusable_not_equal`` is True.

``fold`` (stdlib only, linear):
  1. NFKD, so a base letter and its combining mark separate; 2. drop control, format, combining-mark, private-use, surrogate and
  UNASSIGNED (Cn) characters and the invisible filler letters; 3. NFKC; 4. every Unicode whitespace character (``str.isspace``,
  which includes line and paragraph separators, NEL, no-break space) becomes a space so words are never joined; 5. every Unicode
  decimal digit becomes an ASCII digit; 6. look-alike letters (a curated table of Cyrillic, Greek, Armenian and Latin-extended
  letters) become the Latin letter. Case is kept unless ``casefold`` is set; ``collapse_ws`` squeezes runs of whitespace.

Honest limits: the table is curated, NOT the full Unicode confusables set (that data is not in the standard library); a letter not
in it is not folded. Dropping unassigned code points (Cn) depends on the Python build's Unicode version: a newly assigned
character stops being dropped on an older interpreter and starts on a newer one. ``mixed_script`` is the fail-closed backstop: a
word that mixes Latin with Cyrillic, Greek, Armenian, Cherokee or Coptic letters is a deny signal (UTS #39 style) whatever the table
knows. Property: ``fold(x + mark) == fold(x)`` for any combining mark, format or unassigned character.
"""

from __future__ import annotations

import re
import unicodedata

_DROP_CATEGORIES = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"})
FILLERS = frozenset(
    map(chr, (0x3164, 0x115F, 0x1160, 0x2800, 0xFFA0))
)  # invisible letters/symbols used to glue or split words
_PAIRS = (  # (code points, Latin letters); code points so this file stays ASCII
    ((0x430, 0x435, 0x43E, 0x440, 0x441, 0x445, 0x443, 0x456, 0x455, 0x458, 0x43A, 0x43C, 0x442, 0x43D, 0x432), "aeopcxyisjkmthb"),
    ((0x410, 0x412, 0x415, 0x41A, 0x41C, 0x41D, 0x41E, 0x420, 0x421, 0x422, 0x425), "ABEKMHOPCTX"),
    ((0x405, 0x406, 0x408, 0x423, 0x4AE, 0x4C0, 0x51A, 0x51C), "SIJYYIQW"),
    ((0x4BB, 0x4CF, 0x51B, 0x51D, 0x4AF, 0x501), "hlqwyd"),  # shha, palochka, qa, we, straight u, komi de
    ((0x433,), "r"),  # Cyrillic ghe (the r in a spoofed "drill")
    ((0x417, 0x437), "33"),  # Cyrillic Ze reads as the digit 3
    ((0x461,), "w"),  # Cyrillic omega
    ((0x3BF, 0x3B1, 0x3BD, 0x39F, 0x391, 0x392, 0x395, 0x399, 0x39A, 0x39C, 0x39D, 0x3A1, 0x3A4, 0x3A7, 0x3A5, 0x396, 0x397),
     "oavOABEIKMNPTXYZH"),
    ((0x3B9, 0x3BA, 0x3C1, 0x3C4, 0x3C5, 0x3C7, 0x3F2, 0x3F3, 0x3F9, 0x37F), "ikptuxcjCJ"),  # Greek iota kappa rho tau upsilon chi, lunate sigma, yot
    ((0x3B7, 0x3B3, 0x3BC, 0x3C9), "nyuw"),  # Greek eta, gamma, mu, omega
    ((0x3B5, 0x261, 0x251, 0xF8, 0x142, 0x111, 0x1D0F, 0x1D21), "egaoldow"),  # epsilon, script g, alpha, o-slash, l-stroke, d-stroke, small caps O, W
    ((0x131, 0x130), "iI"),  # dotless i, dotted capital I
    ((0x585, 0x57D, 0x578, 0x570, 0x555, 0x54D, 0x581), "ounhOUg"),  # Armenian oh, seh, vo, ho, Oh, Seh, co
)  # fmt: skip
LOOKALIKES: dict[str, str] = {
    chr(c): a for cps, letters in _PAIRS for c, a in zip(cps, letters, strict=True)
}
_TABLE = {ord(k): v for k, v in LOOKALIKES.items()}
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


def safe_equal(a: str, b: str) -> bool:
    """Equality for ALLOW decisions: NFKC, case and whitespace only. No look-alike is equal."""
    return _canon(a) == _canon(b)


def confusable_not_equal(a: str, b: str) -> bool:
    """True when ``a`` and ``b`` fold to the same text but are NOT ``safe_equal``: a look-alike pair. An ALLOW check
    (recipient equals the verified address) must refuse on True; a DENY check treats the pair as the same."""
    return fold(a, casefold=True, collapse_ws=True) == fold(
        b, casefold=True, collapse_ws=True
    ) and not safe_equal(a, b)


_NON_LATIN_SCRIPTS = ("CYRILLIC", "GREEK", "ARMENIAN", "CHEROKEE", "COPTIC")
_WORD = re.compile(r"\w+", re.UNICODE)


def mixed_script(text: str) -> bool:
    """True if any word mixes Latin letters with Cyrillic, Greek, Armenian, Cherokee or Coptic letters (UTS #39 style). A fail-closed
    deny signal that does not depend on the look-alike table. Digits and punctuation are script-neutral."""
    for word in _WORD.findall(unicodedata.normalize("NFKC", text)):
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
