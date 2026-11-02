"""OUTPUT check for free text a person or system will read (an approver card, a summary, a reply).

``guard.redact`` is the input mask (what goes to a model); this is the output check (what comes back out). It answers one
question: may this text carry an account, an id or a protected value?

The rule is a digit budget, not a shape match. After the text is folded (``guard.textnorm``), dates, amounts and the references the
caller allows are set aside; what is left may hold fewer than ``max_digits`` digit-like characters IN TOTAL, wherever they sit and
whatever lies between them (separators, letters, look-alikes, other scripts' digits). Digit-like LETTERS (O o I l L S s B Z z, capital
G and Q) count when they sit in a run with a real digit (``8 O 1 l 5 S``) or form a letter-only run of ``letter_run_min`` or more
(``OlISBZGQ``). The lowercase i, b, g, q ("big issue", "is") are WEAK letters: they never start a run and never qualify one, but once a letters-only
run has ``letter_run_min`` strong letters they count too, so ``OlISBZGq`` is
counted as 8. Residual: weak letters beside real digits (``1b5i7g3q``) and runs with fewer strong letters are not counted; they ARE folded in the protected-value key.

Set-aside tokens are not free, and the budgets ADD UP: a card number split into a plain part and an "amount" must not slip through.
The set-aside amounts and references have their own budget (``max_exempt_tokens``, ``max_exempt_digits``, always below
``max_digits``), two of them side by side are refused, an amount counts only with a currency from ``LeakPolicy.currencies`` next to
it, and ``max_total_digits`` (below ``2 * max_digits - 1``) caps the SUM of the plain digit-like characters, the digits of the
set-aside amounts and references, and ``DATE_DIGITS`` (5) per date. A date is not free either: a valid date from the allowed years
carries about 15 bits (4.6 decimal digits), so ``max_dates`` dates can still carry a few digits of an id; ``max_total_digits`` counts
them. Residual: digits spelled as words, or written as numerals of a script the fold does not map (Chinese numerals, for example),
are not counted.

Protected values: the caller supplies them (the check cannot find a secret it was not given). A value with at least
``min_protected_len`` Latin letters or digits is matched as a squeezed key (and, with 6+ digits, as its digits in order with anything
between them). A short or non-Latin value (a name in Japanese, Cyrillic or Arabic script, a 2-3 letter name) is matched in the folded,
case-folded text: a Latin value as a word (not glued to other LETTERS, so ``Bob123`` hits ``Bob``), a value in any other script as a
plain substring, because Chinese, Japanese, Thai, Lao and Khmer write no spaces (``contact Zhang Wei`` in unspaced CJK text still
hits); the price is that a short Cyrillic or Greek name also hits inside a longer word (fail closed). ``on_short="raise"`` makes such
a value a ``ValueError`` instead (strict mode). A value that folds to nothing is always a ``ValueError``.

A word that mixes Latin with Cyrillic, Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu or another look-alike-rich script is
refused (``MIXED_SCRIPT``, UTS #39 style) whatever the look-alike table knows; the micro sign and the ohm sign are exempt (unit
symbols); turn it off with ``deny_mixed_script=False`` only where such words are legitimate.

The text is bounded FIRST (``max_len``, typed ``TEXT_TOO_LONG`` / ``TEXT_NOT_STRING``), so the fold's cost is bounded. Every threshold is
a ``LeakPolicy`` field (validated; ``LeakPolicy.from_mapping`` rejects unknown keys).

There is NO default policy: ``check_text`` needs ``policy=``. ``LeakPolicy.payments()`` is the strict profile (8-digit budget, 14 in
total, 2000-2099 dates; it refuses an order id or a phone number of 8 digits or more); ``LeakPolicy.general()`` is for replies that
legitimately carry ids and phone numbers (12-digit budget, 22 in total), at the price of letting a card number out when it is sent in pieces: pair it with a protected-value list. Defaults table: ``docs/promoted-controls.md``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from functools import lru_cache
from typing import Any

from hadavin_sdk.guard.textnorm import fold, has_mixed_script, squeeze

DATE_DIGITS = (
    5  # digits one date counts in the combined budget: log10(100 years x 12 months x 31 days) = 4.6
)
_MARK = chr(
    0xE000
)  # private use: textnorm.fold removes it from input, so a sentinel can only be ours
_ISO = re.compile(r"(?<!\d)(\d{4})([-/.])(\d{2})\2(\d{2})(?!\d)")
_DAY_FIRST_OR_MONTH_FIRST = re.compile(r"(?<!\d)(\d{2})([-/.])(\d{2})\2(\d{4})(?!\d)")
_AMOUNT = r"(?:(?<![\d,.])\d{1,2}(?:,\d{3}){1,2}(?:\.\d{1,2})?(?![\d,])|(?<![\d.])\d{1,7}\.\d{1,2}(?![\d.]))"
_CUR_SYMBOLS = "$" + "".join(
    map(chr, (0x20AC, 0xA3, 0xA5, 0x20B9))
)  # dollar, euro, pound, yen, rupee
_CURRENCY_BEFORE = "(?:(?<=[" + _CUR_SYMBOLS + "])|(?<=[" + _CUR_SYMBOLS + "] ))"
_IBAN_GROUPS = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{2}\d{2}(?:[ \-]?[A-Za-z0-9]{4}){3,}")
_MARK_RUN = re.compile(_MARK + r"[^A-Za-z0-9" + _MARK + r"]{0,2}" + _MARK)
_DIGITISH = frozenset("OoIlLSsBZzGQ")  # letters an attacker writes for 0 1 1 5 8 2 6 9
_WEAK_DIGITISH = frozenset(
    "ibgq"
)  # also written for digits, but ordinary prose ("big issue"): counted only inside a qualified run
_SEPARATORS = re.compile(r"[^A-Za-z0-9]")
DEFAULT_CURRENCIES = frozenset(
    [
        "USD",
        "EUR",
        "GBP",
        "CAD",
        "AUD",
        "NZD",
        "CHF",
        "JPY",
        "CNY",
        "INR",
        "SEK",
        "NOK",
        "DKK",
        "PLN",
        "CZK",
        "HUF",
        "BRL",
        "MXN",
        "ZAR",
        "SGD",
        "HKD",
        "KRW",
        "AED",
        "SAR",
        "TRY",
        "ILS",
        "THB",
        "IDR",
        "MYR",
        "PHP",
    ]
)


class Violation(StrEnum):
    TEXT_NOT_STRING = "TEXT_NOT_STRING"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    ACCOUNT_SHAPED = "ACCOUNT_SHAPED"
    DIGIT_BUDGET = "DIGIT_BUDGET"
    EXEMPT_TOKENS = "EXEMPT_TOKENS"
    PROTECTED_VALUE = "PROTECTED_VALUE"
    MIXED_SCRIPT = "MIXED_SCRIPT"


@dataclass(frozen=True)
class LeakPolicy:
    max_digits: int = 8
    max_total_digits: int = 14
    date_years: tuple[int, int] = (2000, 2099)
    max_len: int = 4096
    max_exempt_tokens: int = 6
    max_exempt_digits: int = 7
    max_dates: int = 2
    amounts_need_currency: bool = True
    currencies: frozenset[str] = field(default=DEFAULT_CURRENCIES)
    min_protected_len: int = 4
    min_protected_digits: int = 4
    letter_run_min: int = 6
    on_short: str = "token"
    account_min_len: int = 9
    deny_mixed_script: bool = True

    def __post_init__(self) -> None:
        def need(ok: bool, msg: str) -> None:
            if not ok:
                raise ValueError(msg)

        def is_int(v: object, lo: int, hi: int) -> bool:
            return type(v) is int and lo <= v <= hi

        need(is_int(self.max_digits, 1, 64), "max_digits must be an int in 1..64")
        lo, hi = self.date_years
        need(
            is_int(lo, 1, 9999) and is_int(hi, 1, 9999) and lo <= hi,
            "date_years must be (low, high) with 1 <= low <= high <= 9999",
        )
        need(is_int(self.max_len, 1, 100_000), "max_len must be an int in 1..100000")
        need(is_int(self.max_exempt_tokens, 0, 100), "max_exempt_tokens must be an int in 0..100")
        need(is_int(self.max_exempt_digits, 0, 200), "max_exempt_digits must be an int in 0..200")
        need(is_int(self.max_dates, 0, 20), "max_dates must be an int in 0..20")
        need(
            self.max_exempt_digits < self.max_digits,
            "max_exempt_digits must be below max_digits",
        )
        need(
            is_int(self.max_total_digits, 1, 128)
            and self.max_total_digits <= 2 * self.max_digits - 2,
            "max_total_digits must be an int in 1..(2 x max_digits - 2): the plain and the set-aside digits add up",
        )
        need(type(self.amounts_need_currency) is bool, "amounts_need_currency must be a bool")
        need(
            isinstance(self.currencies, frozenset)
            and all(isinstance(c, str) and re.fullmatch(r"[A-Z]{3}", c) for c in self.currencies),
            "currencies must be a frozenset of 3-letter upper-case codes",
        )
        need(is_int(self.min_protected_len, 1, 64), "min_protected_len must be an int in 1..64")
        need(
            is_int(self.min_protected_digits, 2, 64), "min_protected_digits must be an int in 2..64"
        )
        need(self.on_short in ("token", "raise"), 'on_short must be "token" or "raise"')
        need(is_int(self.account_min_len, 4, 64), "account_min_len must be an int in 4..64")
        need(type(self.deny_mixed_script) is bool, "deny_mixed_script must be a bool")

    @classmethod
    def payments(cls) -> LeakPolicy:
        """Strict: for approver cards and replies near money. Refuses 8 or more plain digit-like characters, or 14 or more in total."""
        return cls()

    @classmethod
    def general(cls) -> LeakPolicy:
        """For replies that carry order ids and phone numbers (up to 11 plain digits, 21 in total). Weaker against a card number
        split into pieces: use a protected-value list with it."""
        return cls(
            max_digits=12, max_total_digits=22, max_exempt_digits=9, max_dates=3, account_min_len=14
        )

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any] | None) -> LeakPolicy:
        """Build from a config section; unknown keys are an error (a typo must not silently keep a default)."""
        raw = dict(raw or {})
        unknown = sorted(set(raw) - set(cls.__dataclass_fields__))
        if unknown:
            raise ValueError(f"unknown leak policy key: {unknown[0]}")
        if "date_years" in raw:
            raw["date_years"] = tuple(raw["date_years"])
        if "currencies" in raw:
            raw["currencies"] = frozenset(raw["currencies"])
        return cls(**raw)


@lru_cache(maxsize=64)
def _rx(policy: LeakPolicy) -> tuple[re.Pattern[str], re.Pattern[str], re.Pattern[str]]:
    codes = "|".join(sorted(policy.currencies)) or "(?!)"
    anchored = re.compile(
        _CURRENCY_BEFORE + _AMOUNT + "|" + _AMOUNT + r"(?= ?(?:" + codes + r")(?![A-Za-z]))"
    )
    account = re.compile(
        r"(?<![A-Za-z0-9])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{"
        + str(policy.account_min_len)
        + r",}(?![A-Za-z0-9])"
    )
    return anchored, re.compile(_AMOUNT), account


def _valid_date(y: int, m: int, d: int, years: tuple[int, int]) -> bool:
    try:
        if not years[0] <= y <= years[1]:
            return False
        date(y, m, d)
        return True
    except ValueError:
        return False


def _digitish_count(t: str, letter_run_min: int) -> int:
    """Digits plus digit-like letters. Characters are grouped into runs of digits and digit-like letters (separators are skipped, any
    other letter ends the run). In a run that holds a real digit every strong letter counts; a run of letters only counts once it holds at
    least ``letter_run_min`` strong letters (a fully letter-encoded account), so ordinary words made of such letters stay free. Weak
    letters (lowercase i b g q) extend a run and count only in a letters-only run that has ``letter_run_min`` strong letters; beside a
    real digit they do not count ("this is big 12345" would otherwise count 11)."""
    total, digits, strong, weak = 0, 0, 0, 0

    def close() -> None:
        nonlocal total, digits, strong, weak
        if digits:
            total += digits + strong
        elif strong >= letter_run_min:
            total += strong + weak
        digits = strong = weak = 0

    for ch in t:
        if ch.isdigit():
            digits += 1
        elif ch in _DIGITISH:
            strong += 1
        elif ch in _WEAK_DIGITISH:
            weak += 1
        elif not _SEPARATORS.fullmatch(ch):
            close()
    close()
    return total


def _word_hit(w: str, tf: str) -> bool:
    """A short or non-Latin protected value ``w`` (folded, case-folded) in the folded text ``tf``. A Latin value must not sit inside a
    longer word; a value in a script without spaces is a plain substring."""
    if not w.isascii():
        return w in tf
    lead = "A-Za-z" if w[0].isalpha() else "A-Za-z0-9"
    trail = "A-Za-z" if w[-1].isalpha() else "A-Za-z0-9"
    return re.search(f"(?<![{lead}]){re.escape(w)}(?![{trail}])", tf, re.IGNORECASE) is not None


def check_text(
    text: object,
    protected: Iterable[str] = (),
    allowed: Iterable[str] = (),
    *,
    policy: LeakPolicy,
    allowed_patterns: Iterable[re.Pattern[str]] = (),
) -> Violation | None:
    """The first violation found, or None. ``allowed`` are exact references (bounded, case-insensitive); ``allowed_patterns`` are
    reference shapes. Both are set aside (and counted as exempt tokens)."""
    if not isinstance(text, str):
        return Violation.TEXT_NOT_STRING
    if len(text) > policy.max_len:
        return Violation.TEXT_TOO_LONG
    keys: list[tuple[str, str]] = []  # (squeezed key, digits of the key)
    words: list[str] = []
    for p in protected:
        if not isinstance(p, str) or not p:
            raise ValueError(
                "a protected value is empty or not text: refusing to check with a value that would match everything or nothing"
            )
        fv = fold(p, casefold=True, collapse_ws=True)
        if not fv:
            raise ValueError(
                "a protected value folds to nothing: refusing to check with a value that would match everything or nothing"
            )
        k = squeeze(p, loose=True)
        if len(k) >= policy.min_protected_len:
            keys.append((k, "".join(ch for ch in k if ch.isdigit())))
        elif policy.on_short == "raise":
            raise ValueError(
                "a protected value is shorter than min_protected_len (or has too few Latin letters or digits)"
            )
        else:
            words.append(fv)
    t = fold(text)
    anchored, any_amount, account_like = _rx(policy)

    def digits_in(s: str) -> int:
        return sum(ch.isdigit() for ch in s)

    d0 = digits_in(t)
    for a in allowed:
        fa = fold(a) if a else ""
        if fa:
            t = re.sub(
                r"(?<![A-Za-z0-9])" + re.escape(fa) + r"(?![A-Za-z0-9])",
                _MARK,
                t,
                flags=re.IGNORECASE,
            )
    marks_allowed, d1 = t.count(_MARK), digits_in(t)
    t = _ISO.sub(
        lambda m: (
            _MARK if _valid_date(int(m[1]), int(m[3]), int(m[4]), policy.date_years) else m[0]
        ),
        t,
    )

    def day_month_year(m: re.Match[str]) -> str:  # 25/03/2026 and 03/25/2026 are both dates
        a, b, y = int(m[1]), int(m[3]), int(m[4])
        return (
            _MARK
            if _valid_date(y, b, a, policy.date_years) or _valid_date(y, a, b, policy.date_years)
            else m[0]
        )

    t = _DAY_FIRST_OR_MONTH_FIRST.sub(day_month_year, t)
    n_dates, d2 = t.count(_MARK) - marks_allowed, digits_in(t)
    t = (anchored if policy.amounts_need_currency else any_amount).sub(_MARK, t)
    for p in allowed_patterns:
        t = p.sub(_MARK, t)
    sq = squeeze(text, loose=True)
    sq_digits = (
        "".join(ch for ch in sq if ch.isdigit()),
        "".join(ch for ch in squeeze(text) if ch.isdigit()),
    )
    for k, kd in keys:  # the most specific finding first
        if k in sq or (len(kd) >= policy.min_protected_digits and any(kd in s for s in sq_digits)):
            return Violation.PROTECTED_VALUE
    if words:
        tf = fold(text, casefold=True, collapse_ws=True)
        for w in words:
            if _word_hit(w, tf):
                return Violation.PROTECTED_VALUE
    exempt_digits = (d0 - d1) + (
        d2 - digits_in(t)
    )  # amounts, allowed references and patterns (dates are counted by number)
    if (
        t.count(_MARK) > policy.max_exempt_tokens
        or n_dates > policy.max_dates
        or _MARK_RUN.search(t)
        or exempt_digits > policy.max_exempt_digits
    ):
        return Violation.EXEMPT_TOKENS
    if policy.deny_mixed_script and has_mixed_script(text):
        return Violation.MIXED_SCRIPT
    t = t.replace(_MARK, " ")
    if _IBAN_GROUPS.search(t) or account_like.search(t):
        return Violation.ACCOUNT_SHAPED
    plain = _digitish_count(t, policy.letter_run_min)
    if (
        plain >= policy.max_digits
        or plain + exempt_digits + DATE_DIGITS * n_dates >= policy.max_total_digits
    ):
        return Violation.DIGIT_BUDGET
    return None


def text_leaks(
    text: object,
    protected: Iterable[str] = (),
    allowed: Iterable[str] = (),
    *,
    policy: LeakPolicy,
    **kw: Any,
) -> bool:
    return check_text(text, protected, allowed, policy=policy, **kw) is not None
