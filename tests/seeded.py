"""A small seeded generator for the property tests. The same seed gives the same cases on every run and on every Python
version (the standard `random` module is not used: the project's lint rule refuses it, as it is not for secrets, and a
test needs repeatable cases, not unpredictable ones). SplitMix64 (Steele, Lea and Flood, 2014): a 64-bit counter run
through a fixed mixing step."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")
_MASK = (1 << 64) - 1


class Seeded:
    def __init__(self, seed: int) -> None:
        self._state = seed & _MASK

    def _next(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & _MASK
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def random(self) -> float:
        """A float in [0, 1)."""
        return (self._next() >> 11) / float(1 << 53)

    def randrange(self, stop: int) -> int:
        """An int in [0, stop)."""
        if stop <= 0:
            raise ValueError("randrange needs a positive stop")
        return self._next() % stop

    def randint(self, low: int, high: int) -> int:
        """An int in [low, high], both ends included."""
        return low + self.randrange(high - low + 1)

    def choice(self, items: Sequence[T]) -> T:
        return items[self.randrange(len(items))]

    def sample(self, items: Sequence[T], k: int) -> list[T]:
        """`k` different items, in a random order."""
        pool = list(items)
        if not 0 <= k <= len(pool):
            raise ValueError("sample: k is larger than the population")
        out = []
        for _ in range(k):
            out.append(pool.pop(self.randrange(len(pool))))
        return out
