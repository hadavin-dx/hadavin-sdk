"""Redaction cost (R370-style numbers, K5-core). The sweep over every pattern is marked `perf`: CI runs it in its own
blocking step, and the harness itself is tested with a deliberately quadratic pattern so a pass means something.

What is measured: wall seconds (perf_counter: process_time ticks at 15.6 ms on Windows and read 0 for the small run,
which made a linear pattern look like a jump), the median of three runs, on 64 KiB and 256 KiB of one pattern's own
keyword repeated. A linear pattern takes about 4x as long on 4x the text; a quadratic one 16x; the limit is 12x of
the small run (never less than 4 ms), with an absolute floor of 60 ms on the big run. The BANKCODE transit pattern
measured alone: 16 KiB 3 ms, 64 KiB 19 ms, 256 KiB 75 ms, 1 MiB 333 ms: linear (4x per 4x), about 0.3 us per char."""

from __future__ import annotations

import importlib
import re
import statistics
import sys
import time

import pytest

SMALL, BIG = 64 * 1024, 256 * 1024
RATIO, FLOOR_S, MIN_SMALL_S = 12.0, 0.06, 0.004


def _redact_module():
    # the package re-exports a function named `redact`, so `import ... as` would give the function, not the module
    importlib.import_module("hadavin_sdk.guard.redact")
    return sys.modules["hadavin_sdk.guard.redact"]


def _cpu(pattern: re.Pattern[str], text: str) -> float:
    runs = []
    for _ in range(3):
        t0 = time.perf_counter()
        for _match in pattern.finditer(text):
            pass
        runs.append(time.perf_counter() - t0)
    return statistics.median(runs)


def _is_superlinear(measure, unit: str, small: int, big: int) -> bool:
    texts = [(unit * (n // len(unit) + 1))[:n] for n in (small, big)]
    t_small, t_big = (measure(t) for t in texts)
    return t_big > max(FLOOR_S, RATIO * max(t_small, MIN_SMALL_S))


def is_superlinear(pattern: re.Pattern[str], unit: str, small: int = SMALL, big: int = BIG) -> bool:
    return _is_superlinear(lambda t: _cpu(pattern, t), unit, small, big)


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


# --- end to end: redact_untrusted with its views, not one pattern -------------------------------------------------------------------
# A pattern sweep cannot see the cost of the second pass (NFKC views, neutralising, unescaping): this runs the real entry
# point on text that forces a view. RE-RUN POLICY: wall clock on a shared runner is noisy; a red run is repeated once by hand
# (`pytest -m perf -k end_to_end`); two reds in a row on the same shape are a real regression, one red is noise.

BS = chr(92)
E2E_UNITS = [
    "curl -u ",
    "password= ",
    "".join(chr(ord(c) + 0xFEE0) for c in "password=") + " ",  # full-width: a view is scanned
    BS + "u0070assword= ",  # a JSON escape: the unescaped view is scanned
    "pass" + chr(0x200B) + "word= ",  # zero-width space inside the keyword
]


def _e2e(text: str) -> float:
    from hadavin_sdk.guard import runmap

    runs = []
    for _ in range(3):
        t0 = time.perf_counter()
        runmap.redact_untrusted(text, {})
        runs.append(time.perf_counter() - t0)
    return statistics.median(runs)


@pytest.mark.perf
@pytest.mark.parametrize(
    "unit", E2E_UNITS, ids=["curl-u", "password", "fullwidth", "json-escape", "zero-width"]
)
def test_redact_untrusted_end_to_end_is_not_super_linear_with_views(unit):
    assert not _is_superlinear(_e2e, unit, 16 * 1024, 64 * 1024)


@pytest.mark.perf
def test_the_slowest_measured_shape_at_the_cap_stays_under_a_ceiling():
    """Measured 7.2 s for "curl -u " at 262,144 characters on a Windows laptop (2026-11-02); the ceiling is 3x that,
    so only a real regression crosses it. Size timeouts around the measured number (see defaults.MAX_REDACT_CHARS)."""
    from hadavin_sdk import defaults
    from hadavin_sdk.guard import runmap

    text = ("curl -u " * (defaults.MAX_REDACT_CHARS // 8 + 1))[: defaults.MAX_REDACT_CHARS]
    t0 = time.perf_counter()
    runmap.redact_untrusted(text, {})
    assert time.perf_counter() - t0 < 22.0
