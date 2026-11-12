"""Redaction cost (R370-style numbers, K5-core). The sweep over every pattern is marked `perf`: CI runs it in its own
blocking step, and the harness itself is tested with a deliberately quadratic pattern so a pass means something.

What is measured: CPU seconds of one call, timed in blocks of at least 10 ms (50 ms on a coarse clock), the fastest of
two runs per size (three for the end-to-end cases), on 64 KiB and 256 KiB of one pattern's own keyword repeated (`tests/fixtures/timing.py` says why a block and why the fastest). A
linear pattern takes about 4x as long on 4x the text; a quadratic one 16x; the limit is 3x per size ratio (12x for 4x the
text) of the small run (never less than 1 ms), with no fixed seconds floor on the big run. The BANKCODE transit pattern
measured alone: 16 KiB 3 ms, 64 KiB 19 ms, 256 KiB 75 ms, 1 MiB 333 ms: linear (4x per 4x), about 0.3 us per char."""

from __future__ import annotations

import importlib
import re
import sys
import time

import pytest

from tests.fixtures import timing

SMALL, BIG = 64 * 1024, 256 * 1024


def _redact_module():
    # the package re-exports a function named `redact`, so `import ... as` would give the function, not the module
    importlib.import_module("hadavin_sdk.guard.redact")
    return sys.modules["hadavin_sdk.guard.redact"]


def _count_matches(pattern: re.Pattern[str], text: str) -> int:
    n = 0
    for _match in pattern.finditer(text):
        n += 1
    return n


def _cpu(pattern: re.Pattern[str], text: str) -> float:
    return timing.block_seconds(lambda t: _count_matches(pattern, t), text)


def is_superlinear(pattern: re.Pattern[str], unit: str, small: int = SMALL, big: int = BIG) -> bool:
    return timing.is_superlinear(lambda t: _cpu(pattern, t), unit, small, big, repeats=2)


def _keywords(source: str) -> list[str]:
    """The literal lower-case words a pattern is written around (`curl`, `mysql`, `password`), longest first."""
    words = re.findall(r"(?<![\\\[\w\-])[a-z][a-z]{2,}(?:-[a-z]+)?(?![\w\]\[])", source)
    return sorted(set(words), key=len, reverse=True)[:2]


def _units(pattern: re.Pattern[str]) -> list[str]:
    return ["a.", "a=", *[word + " " for word in _keywords(pattern.pattern)]]


@pytest.mark.perf  # timing-based (8x vs a 24x limit): it belongs with the other timing tests, not in the unit suite
def test_the_harness_flags_a_quadratic_pattern_and_passes_a_linear_one():
    quadratic = re.compile(r"\bcurl\b[^\r\n]*?[ \t]-u")  # the shape the command patterns had
    bounded = re.compile(r"\bcurl\b[^\r\n]{0,1024}?[ \t]-u")
    # 8x the text: a linear cost grows about 8x (limit 24x), a quadratic one about 64x
    assert is_superlinear(quadratic, "curl ", small=4 * 1024, big=32 * 1024)
    assert not is_superlinear(bounded, "curl ", small=4 * 1024, big=32 * 1024)


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
# point on text that forces a view. The time is CPU time in blocks, the fastest of three runs per size, so a busy runner
# does not move it much; a red run is a real regression until shown otherwise.

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

    return timing.block_seconds(lambda t: runmap.redact_untrusted(t, {}), text)


@pytest.mark.perf
@pytest.mark.parametrize(
    "unit", E2E_UNITS, ids=["curl-u", "password", "fullwidth", "json-escape", "zero-width"]
)
def test_redact_untrusted_end_to_end_is_not_super_linear_with_views(unit):
    assert not timing.is_superlinear(_e2e, unit, 16 * 1024, 64 * 1024, repeats=3)


@pytest.mark.perf
def test_the_slowest_measured_shape_at_the_cap_stays_under_a_ceiling():
    """Measured 7.2 s for "curl -u " at 262,144 characters on a Windows laptop and 7.7 s in a container (2026-11-02).
    The ceiling is 30 s (about 4x) and the best of two runs counts, so a loaded runner has to be slow twice in a
    row to cross it. Size timeouts around the measured number (see defaults.MAX_REDACT_CHARS)."""
    from hadavin_sdk import defaults
    from hadavin_sdk.guard import runmap

    text = ("curl -u " * (defaults.MAX_REDACT_CHARS // 8 + 1))[: defaults.MAX_REDACT_CHARS]
    best = float("inf")
    for _ in range(2):
        t0 = time.perf_counter()
        runmap.redact_untrusted(text, {})
        best = min(best, time.perf_counter() - t0)
        if best < 30.0:
            break
    assert best < 30.0
