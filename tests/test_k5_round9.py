"""K5-core review round 9 (fresh review of head bdb1f6f). Every test names the finding it closes and fails on
that head."""

from __future__ import annotations

import re
import sys
import time

import pytest

from hadavin_sdk.guard import runmap


def _redact_module():
    return sys.modules["hadavin_sdk.guard.redact"]


# --- B1: no redaction pattern is super-linear on its own keywords repeated ----------------------------------------------------


def _keywords(source: str) -> list[str]:
    """The literal lower-case words a pattern is written around (`curl`, `mysql`, `password`), longest first."""
    words = re.findall(r"(?<![\\\[\w\-])[a-z][a-z]{2,}(?:-[a-z]+)?(?![\w\]\[])", source)
    return sorted(set(words), key=len, reverse=True)[:8]


def _units(pattern: re.Pattern[str]) -> list[str]:
    out = ["a.", "a-", "a.a.", "eyJa.", "a=", "http://a:"]
    for word in _keywords(pattern.pattern):
        out += [word + " ", word + " -", word + "="]
    return out


def test_every_redaction_pattern_is_linear_on_its_own_keywords_repeated():
    slow = []
    for name, pat in _redact_module().PATTERNS:
        for unit in _units(pat):
            times = []
            for n in (8_000, 32_000):
                text = (unit * (n // len(unit) + 1))[:n]
                best = 1e9
                for _ in range(
                    2
                ):  # the best of two: a busy machine must not look like a slow pattern
                    t0 = time.perf_counter()
                    list(pat.finditer(text))
                    best = min(best, time.perf_counter() - t0)
                times.append(best)
            if times[1] > 0.12 and times[1] > 8 * max(times[0], 0.003):  # 4x the text, 16x the time
                slow.append((name, unit, [round(t, 3) for t in times]))
    assert not slow, slow


@pytest.mark.parametrize(
    "word", ["curl", "mysql", "redis-cli", "sqlcmd", "ldapsearch", "htpasswd", "mongo"]
)
def test_a_document_of_repeated_command_words_is_redacted_in_bounded_time(word):
    from hadavin_sdk import defaults

    doc = (word + " ") * (defaults.MAX_DOCUMENT_BYTES // (len(word) + 1))
    t0 = time.perf_counter()
    runmap.redact_untrusted(doc, {})
    assert time.perf_counter() - t0 < 15  # the old command patterns took minutes here


# --- M1: a long local part is still masked ------------------------------------------------------------------------------------


@pytest.mark.parametrize("length", [65, 100, 254])
@pytest.mark.parametrize("at", ["@", "%40"])
def test_a_long_email_local_part_is_masked(length, at):
    local = "a1B2c3D4" * 40
    text = f"bounce to {local[:length]}{at}example.com now"
    out = runmap.redact_untrusted(text, {})
    assert local[:length] not in out and "example.com" not in out
