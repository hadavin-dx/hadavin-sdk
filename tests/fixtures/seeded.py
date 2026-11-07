"""A tiny seeded generator for test data (xorshift64*): the same numbers on every machine and Python version, and no use of
the `random` module, whose generators the security scanner flags even for test data."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")
_MASK = (1 << 64) - 1


class Seeded:
    def __init__(self, seed: int) -> None:
        self._state = (seed * 0x9E3779B97F4A7C15 + 1) & _MASK or 1

    def _next(self) -> int:
        x = self._state
        x ^= x >> 12
        x ^= (x << 25) & _MASK
        x ^= x >> 27
        self._state = x
        return (x * 0x2545F4914F6CDD1D) & _MASK

    def randint(self, low: int, high: int) -> int:
        """An integer in low..high, both included."""
        return low + (self._next() >> 11) % (high - low + 1)

    def choice(self, items: Sequence[T]) -> T:
        return items[self.randint(0, len(items) - 1)]

    def sample(self, items: Sequence[T], k: int) -> list[T]:
        pool = list(items)
        return [pool.pop(self.randint(0, len(pool) - 1)) for _ in range(k)]
