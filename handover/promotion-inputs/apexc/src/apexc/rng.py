"""SplitMix64 and FNV-1a: the only randomness in the repo. No stdlib `random`, no `hash()`, no clock, so results do not
depend on PYTHONHASHSEED or the Python version. Not for security."""

from __future__ import annotations

M64 = (1 << 64) - 1


class Rng:
    def __init__(self, seed: int) -> None:
        self.s = seed & M64

    def u64(self) -> int:
        self.s = (self.s + 0x9E3779B97F4A7C15) & M64
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
        return z ^ (z >> 31)

    def randint(self, a: int, b: int) -> int:
        return a + self.u64() % (b - a + 1)

    def choice(self, seq):
        return seq[self.randint(0, len(seq) - 1)]


def fnv1a(s: str) -> int:
    h = 0xCBF29CE484222325
    for byte in s.encode():
        h = ((h ^ byte) * 0x100000001B3) & M64
    return h
