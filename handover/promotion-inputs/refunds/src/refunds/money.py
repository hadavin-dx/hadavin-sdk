"""Money parsing (R-REF-010). A pure function; the only place an amount string becomes an integer."""

from __future__ import annotations

import re

from refunds.config import LIMITS

# canonical positive integer minor-unit string: ASCII digits, no sign, no leading zero, no exponent, <= 12 digits
_CANON = re.compile(r"[1-9][0-9]{0,11}")
_CANON0 = re.compile(r"0|[1-9][0-9]{0,11}")


class MoneyError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def parse_minor(amount: object, currency: object) -> int:
    """Return the integer or raise MoneyError(code). Never raises anything else, whatever the input types are.
    Codes: CURRENCY_UNSUPPORTED, AMOUNT_NOT_CANONICAL."""
    if not isinstance(currency, str) or currency not in LIMITS:
        raise MoneyError("CURRENCY_UNSUPPORTED")
    if not isinstance(amount, str) or _CANON.fullmatch(amount) is None:
        raise MoneyError("AMOUNT_NOT_CANONICAL")
    return int(amount)


def parse_nonneg(amount: object) -> int:
    """Canonical NON-NEGATIVE minor-unit string (for the signed basis: prior amounts may be 0, never negative, padded or non-ASCII). Raises MoneyError only."""
    if not isinstance(amount, str) or _CANON0.fullmatch(amount) is None:
        raise MoneyError("AMOUNT_NOT_CANONICAL")
    return int(amount)
