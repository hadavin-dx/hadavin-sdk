"""Two money types that never mix: `SpendMicro` (what model calls cost, in whole micro-dollars) and `BusinessMoney`
(an amount of a client's own business, such as a refund, in minor units). A refund can never be added to a spend
counter because the two types share no conversion (bible R171). Inside the meter every spend amount is a
`SpendMicro`; at the store boundary it becomes a `Decimal` with exactly six decimals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Context, Decimal
from typing import Any

from hadavin_sdk.defaults import MAX_USD, MICRO_DECIMALS, MICRO_PER_USD
from hadavin_sdk.store.protocol import check_usd

_CURRENCY = re.compile(r"[A-Z]{3}")
_MAX_MICRO = MAX_USD * MICRO_PER_USD


@dataclass(frozen=True)
class SpendMicro:
    """Model-call spend in whole micro-dollars: an exact `int` from 0 to `MAX_USD` dollars. Never a float, a bool
    or a Decimal. It has no `__int__`, `__float__` or `__index__`, so it cannot slip into plain arithmetic."""

    micro: int

    def __post_init__(self) -> None:
        if type(self.micro) is not int:
            raise ValueError("micro must be an exact int")
        if not 0 <= self.micro <= _MAX_MICRO:
            raise ValueError("micro is out of range")

    @classmethod
    def from_usd(cls, x: Decimal) -> SpendMicro:
        """Exact conversion of a US-dollar Decimal with at most six decimals (`check_usd`, the one validator)."""
        check_usd(x, max_decimals=MICRO_DECIMALS)
        _sign, digits, exponent = x.as_tuple()
        if not any(digits):
            return cls(0)
        # exact scaling with a context wide enough for every digit (never the thread's default precision)
        wide = Context(prec=len(digits) + abs(exponent) + MICRO_DECIMALS + 1)  # type: ignore[arg-type]
        return cls(
            int(x.scaleb(MICRO_DECIMALS, context=wide))
        )  # exact: check_usd allowed only trailing zeros

    def to_usd(self) -> Decimal:
        """The amount as a Decimal with exponent exactly -6."""
        return Decimal((0, tuple(int(d) for d in str(self.micro)), -MICRO_DECIMALS))

    @classmethod
    def ceil_cost(cls, numerator: int, denominator: int = MICRO_PER_USD) -> SpendMicro:
        """`numerator / denominator` rounded UP, once (bible R214: never down, never to nearest)."""
        if type(numerator) is not int or type(denominator) is not int:
            raise ValueError("numerator and denominator must be exact ints")
        if denominator <= 0:
            raise ValueError("denominator must be above zero")
        if numerator < 0:
            raise ValueError("numerator must not be negative")
        return cls(-(-numerator // denominator))

    def __add__(self, other: Any) -> SpendMicro:
        if type(other) is not SpendMicro:
            return NotImplemented
        return SpendMicro(self.micro + other.micro)

    def __sub__(self, other: Any) -> SpendMicro:
        if type(other) is not SpendMicro:
            return NotImplemented
        if other.micro > self.micro:
            raise ValueError("spend cannot go below zero")
        return SpendMicro(self.micro - other.micro)

    def __lt__(self, other: Any) -> bool:
        return self.micro < other.micro if type(other) is SpendMicro else NotImplemented

    def __le__(self, other: Any) -> bool:
        return self.micro <= other.micro if type(other) is SpendMicro else NotImplemented

    def __gt__(self, other: Any) -> bool:
        return self.micro > other.micro if type(other) is SpendMicro else NotImplemented

    def __ge__(self, other: Any) -> bool:
        return self.micro >= other.micro if type(other) is SpendMicro else NotImplemented


@dataclass(frozen=True)
class BusinessMoney:
    """An amount of the client's own business in minor units (for example cents) and a 3-letter currency. It adds
    and subtracts only with the same currency and has NO conversion to or from `SpendMicro`."""

    minor: int
    currency: str

    def __post_init__(self) -> None:
        if type(self.minor) is not int:
            raise ValueError("minor must be an exact int")
        if type(self.currency) is not str or _CURRENCY.fullmatch(self.currency) is None:
            raise ValueError("currency must be 3 capital letters")

    def __add__(self, other: Any) -> BusinessMoney:
        if type(other) is not BusinessMoney:
            return NotImplemented
        if other.currency != self.currency:
            raise ValueError("currencies differ")
        return BusinessMoney(self.minor + other.minor, self.currency)

    def __sub__(self, other: Any) -> BusinessMoney:
        if type(other) is not BusinessMoney:
            return NotImplemented
        if other.currency != self.currency:
            raise ValueError("currencies differ")
        return BusinessMoney(self.minor - other.minor, self.currency)
