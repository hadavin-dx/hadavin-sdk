"""The half-written-escape finder (`guard.runmap.partial_escape_start`) is linear in the text and finds exactly what the
regex it replaced found. The old regex is kept here, as the oracle, only for the comparison."""

from __future__ import annotations

import itertools
import random
import re

import pytest

from hadavin_sdk import tools as tools_mod
from hadavin_sdk.guard import runmap
from tests.fixtures import timing

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
        started = timing.CLOCK()
        job()
        best = min(best, timing.CLOCK() - started)
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
    # the old pattern took 1.0 s for 5000 such groups, 16 s for 20000 and 65 s for 40000 (measured once on the author's laptop, 2026-11-06); this is far less for 600000
    hostile = [
        "%C3" * 200_000 + "X",
        "%C3" * 200_000,
        "%C3" * 200_000 + "%",
        "%C3" * 200_000 + "%A",
    ]

    def run(texts):
        return lambda: [runmap.partial_escape_start(t) for t in texts]

    first = _fastest(run(hostile))
    assert first < 60.0, first  # generous: a quadratic pattern is hours


@pytest.mark.perf
@pytest.mark.parametrize("unit", ["%C3", "%C3%A", "&#", "&#x4", "\\u", "%", "&a"])
def test_the_time_of_a_long_run_grows_no_faster_than_its_length(unit):
    # the shared rule (`tests/fixtures/timing.py`) instead of "twice the input, under four times the time", which a
    # quadratic cost (exactly four times) could pass: 8x the text may take at most 24x the time. The old pattern took about
    # 0.2 s at 2000 groups and 10 s at 16000 groups here (a ratio of about 64), and only when the run is followed by a
    # character that is not part of it: a run that ends the text is found at once, so the text below has both ends.
    measured = timing.growth(
        lambda run: runmap.partial_escape_start("x" + run + "y"), unit, 6_000, 48_000
    )
    assert not measured.flagged, f"partial_escape_start on {unit!r}: {measured}"


@pytest.mark.perf
def test_the_growth_rule_flags_the_old_pattern_on_the_same_text():
    # the control for the test above: the old regex really is quadratic on a `%XX` run that is followed by a character
    # that is not part of it, and the rule flags it. Only this unit has a documented quadratic history for the old
    # pattern (the others in the test above are linear guards: they pass for a linear function and would flag a
    # quadratic one, but no quadratic pattern for them was measured here).
    measured = timing.growth(lambda run: _old("x" + run + "y", 0), "%C3", 1_500, 12_000)
    assert measured.flagged, (
        f"the old pattern was not flagged, so the rule would miss it: {measured}"
    )


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


def test_a_run_the_old_pattern_took_seconds_on_is_instant():
    # 15 000 groups: the old repeated-group pattern needed an estimated 10 s here; a function that is linear needs milliseconds.
    # This is the quick guard that fails fast if the quadratic pattern is ever put back (the larger test above would take hours).
    text = "x" + "%C3" * 15_000 + "y"
    assert _fastest(lambda: [runmap.partial_escape_start(text)]) < 2.0


# The two callers of `partial_escape_start`. The expected values below were produced by the code BEFORE this change
# (the same inputs were run on the source of origin/main b34eef8 and gave exactly these outputs), so they pin "same result".
UNDO_CLEAN = [
    ("pw=abc%C3", "pw=abc"),
    ("pw=abc%C3%A", "pw=abc"),
    ("pw=abc&#9", "pw=abc"),
    ("pw=abc&amp", "pw=abc"),
    ("ok text", "ok text"),
    ("a%C3%A9 b%C3", "a\xe9 b"),
    ("x" + chr(92) + "u00", "x"),
    ("x%C3%A9%C3%", "x"),
    ("line%C3\n", "line"),
    ("&&&&", ""),
    ("%C3%C3%C3%C3", ""),
    ("tok%C3%80%C3%81 end", "tok\xc0\xc1 end"),
    ("tail&#x4", "tail"),
]


@pytest.mark.parametrize(("text", "expected"), UNDO_CLEAN)
def test_undo_with_clean_drops_a_half_written_escape_at_the_end(text, expected):
    assert runmap.undo(text, clean=True) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("x" + "%C3" * 80, "x"), ("y" + "&" * 100, "y"), ("z" + "%C3%A9" * 30 + "%C3", "z")],
)
def test_undo_with_clean_repeats_until_a_run_longer_than_its_window_is_gone(text, expected):
    # the look-back window is a few dozen characters, so a long run needs the loop to go round many times
    assert runmap.undo(text, clean=True) == expected


def test_undo_without_clean_keeps_the_half_written_escape_as_it_always_did():
    assert runmap.undo("pw=abc%C3") == "pw=abc\ufffd"
    assert runmap.undo("&&&&") == "&&&&"


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("abc%C3", "abc"),
        ("abc%C3%A", "abc"),
        ("abc&#9", "abc"),
        ("abc", "abc"),
        ("abc%C3%A9 tail%C3", "abc%C3%A9 tail"),
    ],
)
def test_strip_fragment_removes_a_half_written_escape_before_the_marker(body, expected):
    from hadavin_sdk import tools

    out = tools._strip_fragment(body + tools.TRUNCATED, ["Zq9Lm4pTvX2"])
    assert out == expected + tools.TRUNCATED


@pytest.mark.parametrize(
    "body", ["abc" + "%C3" * 80, "abc" + "&" * 100, "abc" + "%C3%A9" * 30 + "%C3"]
)
def test_strip_fragment_repeats_over_a_run_longer_than_its_window(body):
    from hadavin_sdk import tools

    out = tools._strip_fragment(body + tools.TRUNCATED, ["Zq9Lm4pTvX2"])
    assert out == "abc" + tools.TRUNCATED


# The look-back window is part of the result, not only of the cost: an `&` followed by hundreds of letters begins a
# 'half-written entity' that reaches back past the window, and the callers have always left it alone. These outputs
# were produced by the code BEFORE this change (checked on the source of origin/main b34eef8).
@pytest.mark.parametrize("n", [500, 2000])
def test_a_half_escape_far_before_the_end_is_left_alone_by_the_windowed_callers(n):
    from hadavin_sdk import tools

    text = "x&" + "a" * n
    assert runmap.undo(text, clean=True) == text
    assert tools._strip_fragment(text + tools.TRUNCATED, ["Zq9Lm4pTvX2"]) == text + tools.TRUNCATED


def test_strip_fragment_loop_repeats_until_the_run_is_gone_even_with_a_small_scan():
    # With the smallest allowed scan (64 positions) the step after the loop cannot clean a long run; only the loop can.
    from hadavin_sdk import tools
    from hadavin_sdk.scrub_settings import ScrubSettings

    body = "x" + "%C3" * 3000
    out = tools._strip_fragment(
        body + tools.TRUNCATED, ["Zq9Lm4pTvX2"], ScrubSettings(fragment_scan=64)
    )
    assert out == "x" + tools.TRUNCATED


@pytest.mark.parametrize("pos", [-1, -3, -100])
@pytest.mark.parametrize(
    ("text", "expected"), [("%C3%C3", 0), ("%C3", 0), ("x&abc", 1), ("abc", None)]
)
def test_a_negative_start_reads_as_zero_like_the_old_pattern_did(text, expected, pos):
    # CodeRabbit found that the percent-run walk wrapped around on a negative start; the old regex search clamped it to 0.
    assert runmap.partial_escape_start(text, pos) == expected
    assert runmap.partial_escape_start(text, pos) == runmap.partial_escape_start(text, 0)
