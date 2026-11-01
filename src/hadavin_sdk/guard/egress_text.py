"""OUTPUT check for free text a person or system will read (an approver card, a summary, a reply).

``guard.redact`` is the input mask (what goes to a model); this is the output check (what comes back out). It
answers one question: may this text carry an account, an id or a protected value?

The rule is a digit budget, not a shape match. After the text is folded (``guard.textnorm``), dates, amounts and
the references the caller allows are set aside; what is left may hold fewer than ``max_digits`` digit-like
characters IN TOTAL, wherever they sit and whatever lies between them (separators, letters, look-alikes, other
scripts' digits). Digit-like LETTERS (O, l, I, S, B, Z) count when they are chained to a digit (``8 O 1 l 5 S``).
Set-aside tokens are not free: they are capped in number and two of them side by side are refused (a card
number written as ``4111111.11 1111111.11`` is two "amounts"). Protected values the caller supplies are matched as
squeezed keys; a protected value shorter than ``min_protected_len`` raises ``ValueError`` (fails loudly, never
open). The caller must supply them: the check cannot find a secret it was not given.

The text is bounded FIRST (``max_len``, typed ``TEXT_TOO_LONG`` / ``TEXT_NOT_STRING``), so the fold's cost is
bounded. Thresholds live in ``LeakPolicy`` (validated; documented defaults). The defaults are AP-flavoured
(8-digit budget, 2000-2099 dates): a support desk that legitimately prints 8-digit ids sets its own policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any

from hadavin_sdk.guard.textnorm import fold, squeeze

_MARK = ""  # private use: textnorm.fold removes it from input, so a sentinel can only be ours
_ISO = re.compile(r"(?<!\d)(\d{4})([-/.])(\d{2})\2(\d{2})(?!\d)")
_DMY = re.compile(r"(?<!\d)(\d{2})([-/.])(\d{2})\2(\d{4})(?!\d)")
_AMOUNT = r"(?:(?<![\d,.])\d{1,2}(?:,\d{3}){1,2}(?:\.\d{1,2})?(?![\d,])|(?<![\d.])\d{1,7}\.\d{1,2}(?![\d.]))"
_CURRENCY_BEFORE = "(?:(?<=[$€£¥₹])|(?<=[$€£¥₹] ))"
_AMOUNT_ANCHORED = re.compile(
    _CURRENCY_BEFORE + _AMOUNT + "|" + _AMOUNT + r"(?= ?[A-Z]{3}(?![A-Za-z]))"
)
_AMOUNT_ANY = re.compile(_AMOUNT)
_IBAN_GROUPS = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{2}\d{2}(?:[ \-]?[A-Za-z0-9]{4}){3,}")
_ACCOUNT_LIKE = re.compile(r"(?<![A-Za-z0-9])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{9,}(?![A-Za-z0-9])")
_MARK_RUN = re.compile(_MARK + r"[^A-Za-z0-9" + _MARK + r"]{0,2}" + _MARK)
_DIGITISH = frozenset("OoIlSsBZz")  # letters an attacker writes for 0 1 5 8 2
_SEPARATORS = re.compile(r"[^A-Za-z0-9]")


class Violation(StrEnum):
    TEXT_NOT_STRING = "TEXT_NOT_STRING"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    ACCOUNT_SHAPED = "ACCOUNT_SHAPED"
    DIGIT_BUDGET = "DIGIT_BUDGET"
    EXEMPT_TOKENS = "EXEMPT_TOKENS"
    PROTECTED_VALUE = "PROTECTED_VALUE"


@dataclass(frozen=True)
class LeakPolicy:
    max_digits: int = 8
    date_years: tuple[int, int] = (2000, 2099)
    max_len: int = 4096
    max_exempt_tokens: int = 6
    max_exempt_digits: int = 24
    amounts_need_currency: bool = True
    min_protected_len: int = 4
    min_protected_digits: int = 6

    def __post_init__(self) -> None:
        if not (isinstance(self.max_digits, int) and 1 <= self.max_digits <= 64):
            raise ValueError("max_digits must be an int in 1..64")
        lo, hi = self.date_years
        if not (isinstance(lo, int) and isinstance(hi, int) and 1 <= lo <= hi <= 9999):
            raise ValueError("date_years must be (low, high) with 1 <= low <= high <= 9999")
        if not (isinstance(self.max_len, int) and 1 <= self.max_len <= 1_000_000):
            raise ValueError("max_len must be an int in 1..1000000")
        if not (isinstance(self.max_exempt_tokens, int) and 0 <= self.max_exempt_tokens <= 100):
            raise ValueError("max_exempt_tokens must be an int in 0..100")
        if not (isinstance(self.max_exempt_digits, int) and 0 <= self.max_exempt_digits <= 200):
            raise ValueError("max_exempt_digits must be an int in 0..200")
        if not (
            isinstance(self.min_protected_digits, int) and 2 <= self.min_protected_digits <= 64
        ):
            raise ValueError("min_protected_digits must be an int in 2..64")
        if not isinstance(self.amounts_need_currency, bool):
            raise TypeError("amounts_need_currency must be a bool")
        if not (isinstance(self.min_protected_len, int) and 1 <= self.min_protected_len <= 64):
            raise ValueError("min_protected_len must be an int in 1..64")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any] | None) -> LeakPolicy:
        """Build from a config section; unknown keys are an error (a typo must not silently keep a default)."""
        raw = dict(raw or {})
        unknown = sorted(set(raw) - set(cls.__dataclass_fields__))
        if unknown:
            raise ValueError(f"unknown leak policy key: {unknown[0]}")
        if "date_years" in raw:
            raw["date_years"] = tuple(raw["date_years"])
        return cls(**raw)


DEFAULT_POLICY = LeakPolicy()


def _valid_date(y: str, m: str, d: str, years: tuple[int, int]) -> bool:
    try:
        if not years[0] <= int(y) <= years[1]:
            return False
        date(int(y), int(m), int(d))
        return True
    except ValueError:
        return False


def _digitish_count(t: str) -> int:
    """Digits plus digit-like letters chained to a digit (separators are skipped, any other letter ends the chain)."""
    n, chained = 0, False
    for ch in t:
        if ch.isdigit():
            n, chained = n + 1, True
        elif ch in _DIGITISH and chained:
            n += 1
        elif not _SEPARATORS.fullmatch(ch):
            chained = False
    return n


def check_text(
    text: object,
    protected: Iterable[str] = (),
    allowed: Iterable[str] = (),
    *,
    policy: LeakPolicy = DEFAULT_POLICY,
    allowed_patterns: Iterable[re.Pattern[str]] = (),
) -> Violation | None:
    """The first violation found, or None. ``allowed`` are exact references (bounded, case-insensitive);
    ``allowed_patterns`` are reference shapes. Both are set aside (and counted as exempt tokens)."""
    if not isinstance(text, str):
        return Violation.TEXT_NOT_STRING
    if len(text) > policy.max_len:
        return Violation.TEXT_TOO_LONG
    keys = []
    for p in protected:
        if not p:
            continue
        k = squeeze(p, loose=True)
        if len(k) < policy.min_protected_len:
            raise ValueError(
                "a protected value is shorter than min_protected_len: refusing to check with a value that would match anything"
            )
        keys.append(k)
    t = fold(text)
    total_digits = sum(ch.isdigit() for ch in t)
    for a in allowed:
        fa = fold(a) if a else ""
        if fa:
            t = re.sub(
                r"(?<![A-Za-z0-9])" + re.escape(fa) + r"(?![A-Za-z0-9])",
                _MARK,
                t,
                flags=re.IGNORECASE,
            )
    t = _ISO.sub(lambda m: _MARK if _valid_date(m[1], m[3], m[4], policy.date_years) else m[0], t)
    t = _DMY.sub(lambda m: _MARK if _valid_date(m[4], m[3], m[1], policy.date_years) else m[0], t)
    t = (_AMOUNT_ANCHORED if policy.amounts_need_currency else _AMOUNT_ANY).sub(_MARK, t)
    for p in allowed_patterns:
        t = p.sub(_MARK, t)
    sq = squeeze(text, loose=True)
    sq_digits = (
        "".join(ch for ch in sq if ch.isdigit()),
        "".join(ch for ch in squeeze(text) if ch.isdigit()),
    )
    for k in keys:  # the most specific finding first
        kd = "".join(ch for ch in k if ch.isdigit())
        # a protected value is found as one run of the text, or (when it holds 6+ digits) as its digits in order with anything between them
        if k in sq or (len(kd) >= policy.min_protected_digits and any(kd in s for s in sq_digits)):
            return Violation.PROTECTED_VALUE
    exempt_digits = total_digits - sum(ch.isdigit() for ch in t)
    if (
        t.count(_MARK) > policy.max_exempt_tokens
        or _MARK_RUN.search(t)
        or exempt_digits > policy.max_exempt_digits
    ):
        return Violation.EXEMPT_TOKENS
    t = t.replace(_MARK, " ")
    if _IBAN_GROUPS.search(t) or _ACCOUNT_LIKE.search(t):
        return Violation.ACCOUNT_SHAPED
    if _digitish_count(t) >= policy.max_digits:
        return Violation.DIGIT_BUDGET
    return None


def text_leaks(
    text: object, protected: Iterable[str] = (), allowed: Iterable[str] = (), **kw: Any
) -> bool:
    return check_text(text, protected, allowed, **kw) is not None
