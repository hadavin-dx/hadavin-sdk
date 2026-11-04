"""The half-written-escape finder (`guard.runmap.partial_escape_start`) is linear in the text and finds exactly what the
regex it replaced found. The old regex is kept here, as the oracle, only for the comparison."""

from __future__ import annotations

import random
import re
import time

from hadavin_sdk.guard import runmap

# The pattern as it was before (a repeated group before an end anchor: time grows with the square of a `%XX` run).
_OLD = re.compile(
    r"(?:&#(?:[xX][0-9a-fA-F]*|[0-9]*)|&[A-Za-z]*|\\u[dD][89abAB][0-9a-fA-F]{2}(?:\\u?[0-9a-fA-F]{0,3}|\\)?|\\u[0-9a-fA-F]{0,3}|\\|(?:%[89a-fA-F][0-9a-fA-F])+%?[0-9a-fA-F]?|%[0-9a-fA-F]?)$"
)

PIECES = [
    "%", "&", "#", "\\", "u", "x", "X", "C", "3", "a", "9", "d", "D", "8", "B", "f", "z", "\n", " ",
    "%C3", "%a9", "%E2%82", "&#x", "&#9", "&amp", "\\ud8", "\\ud83d\\", "\\u00", "%9", "A",
]  # fmt: skip


def _old(text: str, pos: int) -> int | None:
    m = _OLD.search(text, pos)
    return None if m is None else m.start()


def test_it_finds_exactly_what_the_old_pattern_found_on_a_fuzz_corpus():
    rng = random.Random(20261104)  # noqa: S311 - a seeded test generator
    checked = hits = 0
    for _ in range(60000):
        text = "".join(rng.choice(PIECES) for _ in range(rng.randint(0, 14)))
        pos = rng.choice([0, 0, rng.randint(0, len(text) + 1)])
        want = _old(text, pos)
        assert runmap.partial_escape_start(text, pos) == want, (text, pos)
        checked += 1
        hits += want is not None
    assert (
        hits > 5000 and checked == 60000
    )  # the corpus has both finds and misses (a sensitivity control)


def test_the_listed_endings_are_found_and_whole_escapes_are_not():
    f = runmap.partial_escape_start
    assert f("abc%C3") == 3 and f("abc%C3%A") == 3 and f("abc%C3%") == 3 and f("abc%C3A") == 3
    assert (
        f("x&#9") == 1 and f("x&#x4") == 1 and f("x&am") == 1 and f("x\\u00") == 1 and f("x\\") == 1
    )
    assert f("x\\ud83d\\u") == 1 and f("x%") == 1 and f("x%4") == 1
    assert (
        f("x%41") is None and f("x&amp;") is None and f("x\\u0041") is None and f("hello") is None
    )
    assert f("%C3%A9\n") == 0  # `$` also matches before a final line break, as before
    assert f("ab%C3%A9", 4) == 5 and f("ab%C3%A9", 6) is None  # nothing starts before `pos`


def test_a_very_long_run_of_percent_bytes_takes_linear_time():
    # the old pattern took 1.3 s for 5000 such groups, 23 s for 20000 and 79 s for 40000 (measured); this is under a second for 600000
    hostile = [
        "%C3" * 200_000 + "X",
        "%C3" * 200_000,
        "%C3" * 200_000 + "%",
        "%C3" * 200_000 + "%A",
    ]
    started = time.perf_counter()
    for text in hostile:
        runmap.partial_escape_start(text)
    first = time.perf_counter() - started
    assert first < 2.0, first
    doubled = [t * 2 for t in hostile]  # twice the input: about twice the time, never four times
    started = time.perf_counter()
    for text in doubled:
        runmap.partial_escape_start(text)
    second = time.perf_counter() - started
    assert second < max(4 * first, 1.0), (first, second)


def test_other_long_runs_are_linear_too():
    started = time.perf_counter()
    for text in (
        "&" * 300_000,
        "&#" * 150_000,
        "&" + "a" * 300_000 + "&",
        "\\u" * 150_000,
        "%" * 300_000,
    ):
        runmap.partial_escape_start(text)
    assert time.perf_counter() - started < 3.0
