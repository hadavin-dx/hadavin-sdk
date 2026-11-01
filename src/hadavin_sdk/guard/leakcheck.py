"""Output leak check for free text a person or system will read (an approver card, a summary).

The rule is a digit budget, not a shape match: after dates (calendar-valid, plausible years), amounts, reference
ids the caller allows and a grouped IBAN are set aside, the text may hold fewer than ``max_digits`` digits IN
TOTAL, whatever lies between them (separators, letters, look-alike letters, other scripts' digits). Protected
values the caller supplies are matched as squeezed keys. Matching shapes alone loses to ``1234 ab 5678 ab 9012``.

Text is NFKC-normalised, zero-width / format / combining characters dropped, every Unicode decimal digit
folded to ASCII, and Cyrillic / Greek look-alike letters folded to Latin (a table, not every Unicode
confusable). Stdlib only."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from datetime import date

_BREAKS = chr(10) + chr(13) + chr(9) + chr(11) + chr(12)
_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_PAIRS = (  # code points, so this file stays ASCII
    ((0x430, 0x435, 0x43E, 0x440, 0x441, 0x445, 0x443, 0x456, 0x455, 0x458, 0x43A, 0x43C, 0x442, 0x43D, 0x432), "aeopcxyisjkmthb"),
    ((0x410, 0x412, 0x415, 0x41A, 0x41C, 0x41D, 0x41E, 0x420, 0x421, 0x422, 0x425), "ABEKMHOPCTX"),
    ((0x405, 0x406, 0x408, 0x423, 0x4AE, 0x4C0), "SIJYYI"),
    ((0x4BB, 0x4CF, 0x51B, 0x51D, 0x4AF), "hlqwy"),
    ((0x3BF, 0x3B1, 0x3BD, 0x39F, 0x391, 0x392, 0x395, 0x399, 0x39A, 0x39C, 0x39D, 0x3A1, 0x3A4, 0x3A7, 0x3A5, 0x396, 0x397), "oavOABEIKMNPTXYZH"),
)  # fmt: skip
LOOKALIKES = {chr(c): a for cps, letters in _PAIRS for c, a in zip(cps, letters, strict=True)}

_ISO = re.compile(r"(?<!\d)(\d{4})([-/.])(\d{2})\2(\d{2})(?!\d)")
_DMY = re.compile(r"(?<!\d)(\d{2})([-/.])(\d{2})\2(\d{4})(?!\d)")
_AMOUNT_GROUPED = re.compile(r"(?<![\d,.])\d{1,2}(?:,\d{3}){1,2}(?:\.\d{1,2})?(?![\d,])")
_AMOUNT_DECIMAL = re.compile(r"(?<![\d.])\d{1,7}\.\d{1,2}(?![\d.])")
_IBAN_GROUPS = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{2}\d{2}(?:[ \-]?[A-Za-z0-9]{4}){3,}")
_ACCOUNT_LIKE = re.compile(r"(?<![A-Za-z0-9])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{9,}(?![A-Za-z0-9])")


def fold(raw: str) -> str:
    s = "".join(" " if ch in _BREAKS else ch for ch in unicodedata.normalize("NFKC", raw))
    s = "".join(ch for ch in s if unicodedata.category(ch) not in ("Cc", "Cf", "Mn"))
    return "".join(str(int(ch)) if ch.isdecimal() else LOOKALIKES.get(ch, ch) for ch in s)


def squeeze(raw: str, loose: bool = False) -> str:
    """Comparison key: folded, upper-case letters and digits only; ``loose`` also folds O/0 and I/L/1."""
    s = fold(raw).upper()
    if loose:
        s = s.translate(str.maketrans("OIL", "011"))
    return _NON_ALNUM.sub("", s)


def _valid_date(y: str, m: str, d: str, years: tuple[int, int]) -> bool:
    try:
        if not years[0] <= int(y) <= years[1]:
            return False
        date(int(y), int(m), int(d))
        return True
    except ValueError:
        return False


def text_leaks(
    text: str,
    protected: Iterable[str] = (),
    allowed: Iterable[str] = (),
    *,
    max_digits: int = 8,
    date_years: tuple[int, int] = (2000, 2099),
    allowed_patterns: Iterable[re.Pattern[str]] = (),
) -> bool:
    """True if ``text`` may carry an account, id or protected value. ``allowed`` are exact strings (the
    case's own reference); ``allowed_patterns`` are reference shapes set aside before counting."""
    t = fold(text)
    for a in allowed:
        if a:
            t = t.replace(fold(a), " REF ")
    t = _ISO.sub(lambda m: " DATE " if _valid_date(m[1], m[3], m[4], date_years) else m[0], t)
    t = _DMY.sub(lambda m: " DATE " if _valid_date(m[4], m[3], m[1], date_years) else m[0], t)
    t = _AMOUNT_DECIMAL.sub(" AMT ", _AMOUNT_GROUPED.sub(" AMT ", t))
    for p in allowed_patterns:
        t = p.sub(" REF ", t)
    if _IBAN_GROUPS.search(t) or _ACCOUNT_LIKE.search(t):
        return True
    if sum(ch.isdigit() for ch in t) >= max_digits:
        return True
    sq = squeeze(text, loose=True)
    return any(len(k := squeeze(p, loose=True)) >= 4 and k in sq for p in protected if p)
