"""Redaction cost (R370-style numbers, K5-core). The sweep over every pattern is marked `perf`: CI runs it in its own
step that never blocks a merge (a shared runner is noisy), and the harness itself is tested with a deliberately
quadratic pattern so a pass means something.

What is measured: CPU seconds (process time), the median of three runs, on 64 KiB and 256 KiB of one pattern's own
keyword repeated. A linear pattern takes about 4x as long on 4x the text; a quadratic one 16x; the limit is 12x, with
a floor that keeps the 15.6 ms Windows clock tick from deciding anything."""

from __future__ import annotations

import re
import statistics
import sys
import time

import pytest

SMALL, BIG = 64 * 1024, 256 * 1024
RATIO, FLOOR_S = 12.0, 0.06


def _redact_module():
    return sys.modules["hadavin_sdk.guard.redact"]


def _cpu(pattern: re.Pattern[str], text: str) -> float:
    runs = []
    for _ in range(3):
        t0 = time.process_time()
        for _match in pattern.finditer(text):
            pass
        runs.append(time.process_time() - t0)
    return statistics.median(runs)


def is_superlinear(pattern: re.Pattern[str], unit: str, small: int = SMALL, big: int = BIG) -> bool:
    texts = [(unit * (n // len(unit) + 1))[:n] for n in (small, big)]
    t_small, t_big = (_cpu(pattern, t) for t in texts)
    return t_big > max(FLOOR_S, RATIO * t_small)


def _keywords(source: str) -> list[str]:
    """The literal lower-case words a pattern is written around (`curl`, `mysql`, `password`), longest first."""
    words = re.findall(r"(?<![\\\[\w\-])[a-z][a-z]{2,}(?:-[a-z]+)?(?![\w\]\[])", source)
    return sorted(set(words), key=len, reverse=True)[:2]


def _units(pattern: re.Pattern[str]) -> list[str]:
    return ["a.", "a=", *[word + " " for word in _keywords(pattern.pattern)]]


def test_the_harness_flags_a_quadratic_pattern_and_passes_a_linear_one():
    quadratic = re.compile(r"\bcurl\b[^\r\n]*?[ \t]-u")  # the shape the command patterns had
    bounded = re.compile(r"\bcurl\b[^\r\n]{0,1024}?[ \t]-u")
    assert is_superlinear(quadratic, "curl ", small=8 * 1024, big=32 * 1024)
    assert not is_superlinear(bounded, "curl ", small=8 * 1024, big=32 * 1024)


@pytest.mark.perf
def test_no_redaction_pattern_is_super_linear_on_its_own_keywords_repeated():
    slow = [
        (name, unit)
        for name, pat in _redact_module().PATTERNS
        for unit in _units(pat)
        if is_superlinear(pat, unit)
    ]
    assert not slow, slow
