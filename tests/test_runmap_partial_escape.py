"""The half-written-escape finder (`guard.runmap.partial_escape_start`) is linear in the text and finds exactly what the
regex it replaced found. The old regex is kept here, as the oracle, only for the comparison."""

from __future__ import annotations

import itertools
import random
import re
import time

from hadavin_sdk import tools as tools_mod
from hadavin_sdk.guard import runmap

# The pattern as it was before (a repeated group before an end anchor: time grows with the square of a `%XX` run).
_OLD = re.compile(
    r"(?:&#(?:[xX][0-9a-fA-F]*|[0-9]*)|&[A-Za-z]*|\\u[dD][89abAB][0-9a-fA-F]{2}(?:\\u?[0-9a-fA-F]{0,3}|\\)?|\\u[0-9a-fA-F]{0,3}|\\|(?:%[89a-fA-F][0-9a-fA-F])+%?[0-9a-fA-F]?|%[0-9a-fA-F]?)$"
)

PIECES = [
    "%", "&", "#", "\\", "u", "x", "X", "C", "3", "a", "9", "d", "D", "8", "B", "f", "z", "\n", "\r", " ", "é",
    "%C3", "%a9", "%E2%82", "&#x", "&#9", "&amp", "\\ud8", "\\ud83d\\", "\\u00", "%9", "A", "\r\n", "日",
]  # fmt: skip
ALPHABET = ["%", "8", "A", "3", "x", "\n", "é"]


def _old(text: str, pos: int) -> int | None:
    m = _OLD.search(text, pos)
    return None if m is None else m.start()


def _fastest(job, repeats: int = 3) -> float:
    """The fastest of a few runs: one slow run on a busy machine does not decide the result."""
    best = float("inf")
    for _ in range(repeats):
        started = time.perf_counter()
        job()
        best = min(best, time.perf_counter() - started)
    return best


def test_it_finds_exactly_what_the_old_pattern_found_on_a_fuzz_corpus():
    rng = random.Random(20261104)  # noqa: S311 - a seeded test generator
    checked = hits = 0
    for i in range(60000):
        many = 60 if i % 20 == 0 else 14  # some texts hold runs of more than 14 groups
        text = "".join(rng.choice(PIECES) for _ in range(rng.randint(0, many)))
        pos = rng.choice([0, 0, rng.randint(0, len(text) + 1)])
        want = _old(text, pos)
        assert runmap.partial_escape_start(text, pos) == want, (text, pos)
        checked += 1
        hits += want is not None
    assert (
        hits > 5000 and checked == 60000
    )  # the corpus has both finds and misses (a sensitivity control)


def test_it_finds_exactly_what_the_old_pattern_found_on_every_short_text_over_a_small_alphabet():
    # exhaustive: every text of up to 6 characters over seven characters (one of them non-ASCII, one a line break), at
    # every start position from 0 to one past the end (about 1.1 million comparisons, a few seconds)
    checked = hits = 0
    for n in range(7):
        for letters in itertools.product(ALPHABET, repeat=n):
            text = "".join(letters)
            for pos in range(n + 2):
                want = _old(text, pos)
                assert runmap.partial_escape_start(text, pos) == want, (text, pos)
                checked += 1
                hits += want is not None
    assert checked == sum(len(ALPHABET) ** n * (n + 2) for n in range(7))  # every case was visited
    assert 0 < hits < checked  # the corpus holds both finds and misses (a sensitivity control)


def test_runs_longer_than_the_fuzz_texts_and_other_line_endings_agree_too():
    for groups in (1, 2, 14, 15, 16, 40, 100):
        for tail in ("", "%", "A", "%A", "%A9", "x", "\n", "%\n", "\r", "é", "%é"):
            for head in ("", "ab", "é", "\r"):
                text = head + "%C3" * groups + tail
                for pos in (0, 1, len(text) // 2, len(text) - 1, len(text), len(text) + 1):
                    assert runmap.partial_escape_start(text, pos) == _old(text, pos), (
                        groups,
                        tail,
                        head,
                        pos,
                    )


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
    # the old pattern took 1.3 s for 5000 such groups, 23 s for 20000 and 79 s for 40000 (measured); this is far less for 600000
    hostile = [
        "%C3" * 200_000 + "X",
        "%C3" * 200_000,
        "%C3" * 200_000 + "%",
        "%C3" * 200_000 + "%A",
    ]

    def run(texts):
        return lambda: [runmap.partial_escape_start(t) for t in texts]

    first = _fastest(run(hostile))
    assert first < 60.0, (
        first
    )  # generous: a busy runner or a coverage run is slower, a quadratic pattern is hours
    second = _fastest(
        run([t * 2 for t in hostile])
    )  # twice the input: about twice the time, never four times
    assert second < max(4 * first, 1.0), (first, second)


def test_other_long_runs_are_linear_too():
    texts = (
        "&" * 300_000,
        "&#" * 150_000,
        "&" + "a" * 300_000 + "&",
        "\\u" * 150_000,
        "%" * 300_000,
    )
    assert _fastest(lambda: [runmap.partial_escape_start(t) for t in texts]) < 60.0


def test_the_fragment_cut_in_tools_removes_a_half_written_escape_and_keeps_the_rest():
    forms = ["zzzzzzzz"]
    for tail in ("%E2%82", "%C3%A", "&#x4", "\\u00", "%"):
        assert tools_mod._strip_fragment("keep this text " + tail + tools_mod.TRUNCATED, forms) == (
            "keep this text " + tools_mod.TRUNCATED
        )
    whole = "keep %41 and &amp; and \\u0041 text"
    assert (
        tools_mod._strip_fragment(whole + tools_mod.TRUNCATED, forms) == whole + tools_mod.TRUNCATED
    )
    # a run of half escapes longer than the look-back is taken off in steps, until none is left at the end
    out = tools_mod._strip_fragment("x" + "%C3" * 80 + tools_mod.TRUNCATED, forms)
    assert "%C3" not in out and out.endswith(tools_mod.TRUNCATED)
    # a text without the marker is returned as it is
    assert tools_mod._strip_fragment("abc%C3", forms) == "abc%C3"
