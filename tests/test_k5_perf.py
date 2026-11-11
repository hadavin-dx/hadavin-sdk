"""Redaction cost (R370-style numbers, K5-core). The sweep over every pattern is marked `perf`: CI runs it in its own
blocking step, and the harness itself is tested with a deliberately quadratic pattern so a pass means something.

What is measured: the processor time of this process (on Windows the wall clock: process_time ticks at 15.6 ms there
and read 0 for the small run, which made a linear pattern look like a jump) of one scan, on 16 KiB and 256 KiB of one pattern's own keyword repeated
(256 KiB is the redaction input cap). The shared rule (`tests/fixtures/timing.py`) does the timing: it repeats the scan
until a batch is long enough to time, lets the two sizes take turns and takes each size's fastest of five batches, so a
fast small run is timed properly and never rounded up. The limit is 3x the size ratio, with no fixed seconds figure on
either run. What each test can flag (a cost growing as size ** e is flagged when e is above 1 + log 3 / log gap):
  * the pattern sweep, 16 KiB to 256 KiB, gap 16: linear grows 16x, the limit is 48x, quadratic 256x; e above 1.40;
  * the end-to-end tests, 4 KiB to 64 KiB, gap 16: the same; e above 1.40;
  * the harness check with a real quadratic pattern, 4 KiB to 32 KiB, gap 8: limit 24x, quadratic 64x; e above 1.53
    (256 KiB of that pattern would take minutes). A quadratic stand-in at exactly the sweep's two sizes is flagged, and
    a linear and an "n log n" one pass, in `tests/test_migration_numbers.py` (`test_the_timing_harness_*`).
Until 2026-11-11 the sweep ran 64 KiB to 256 KiB (gap 4: only e above 1.79, a quadratic cost 1.33x over the limit) and
the end-to-end tests 16 KiB to 64 KiB. The BANKCODE transit pattern
measured alone: 16 KiB 3 ms, 64 KiB 19 ms, 256 KiB 75 ms, 1 MiB 333 ms: linear (4x per 4x), about 0.3 us per char."""

from __future__ import annotations

import importlib
import re
import sys
import time

import pytest

from tests.fixtures import timing

SMALL, BIG = 16 * 1024, 256 * 1024


def _redact_module():
    # the package re-exports a function named `redact`, so `import ... as` would give the function, not the module
    importlib.import_module("hadavin_sdk.guard.redact")
    return sys.modules["hadavin_sdk.guard.redact"]


def _scan(pattern: re.Pattern[str], text: str) -> None:
    for _match in pattern.finditer(text):
        pass


def is_superlinear(pattern: re.Pattern[str], unit: str, small: int = SMALL, big: int = BIG) -> bool:
    return timing.is_superlinear(lambda t: _scan(pattern, t), unit, small, big)


def _keywords(source: str) -> list[str]:
    """The literal lower-case words a pattern is written around (`curl`, `mysql`, `password`), longest first."""
    words = re.findall(r"(?<![\\\[\w\-])[a-z][a-z]{2,}(?:-[a-z]+)?(?![\w\]\[])", source)
    return sorted(set(words), key=len, reverse=True)[:2]


def _units(pattern: re.Pattern[str]) -> list[str]:
    return ["a.", "a=", *[word + " " for word in _keywords(pattern.pattern)]]


@pytest.mark.perf  # timing-based (16x vs a 12x limit): it belongs with the other timing tests, not in the unit suite
def test_the_harness_flags_a_quadratic_pattern_and_passes_a_linear_one():
    quadratic = re.compile(r"\bcurl\b[^\r\n]*?[ \t]-u")  # the shape the command patterns had
    bounded = re.compile(r"\bcurl\b[^\r\n]{0,1024}?[ \t]-u")
    # 8x the text: a linear cost grows about 8x (limit 24x), a quadratic one about 64x
    assert is_superlinear(quadratic, "curl ", small=4 * 1024, big=32 * 1024)
    assert not is_superlinear(bounded, "curl ", small=4 * 1024, big=32 * 1024)


@pytest.mark.perf
def test_no_redaction_pattern_is_super_linear_on_its_own_keywords_repeated():
    cases = [
        (name, lambda t, p=pat: _scan(p, t), unit)
        for name, pat in _redact_module().PATTERNS
        for unit in _units(pat)
    ]
    assert len(cases) >= 150, "the sweep would look at too little"
    # every slow pattern AND every pattern that could not be timed, each by name (a refusal does not stop the sweep)
    assert timing.problems(cases, SMALL, BIG) == []


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


def _e2e(text: str) -> None:
    from hadavin_sdk.guard import runmap

    runmap.redact_untrusted(text, {})


@pytest.mark.perf
@pytest.mark.parametrize(
    "unit", E2E_UNITS, ids=["curl-u", "password", "fullwidth", "json-escape", "zero-width"]
)
def test_redact_untrusted_end_to_end_is_not_super_linear_with_views(unit):
    assert not timing.is_superlinear(_e2e, unit, 4 * 1024, 64 * 1024)


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
