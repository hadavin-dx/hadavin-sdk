"""The CPU-time budget of the fold scan and of `runmap.redact_text` (P2d-1): moved tests and new rows."""

import importlib
import time

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard.runmap import InputTooLarge, redact_text

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")
redact = redact_mod.redact
_Redactor = redact_mod._Redactor
FOLD_NOTE = getattr(redact_mod, "FOLD_NOTE", "<no FOLD_NOTE on this head>")


def test_many_short_non_ascii_lines_cost_no_per_line_pattern_runs(monkeypatch):
    assert hasattr(_Redactor, "_dry_hits"), "hook missing on this head"
    assert hasattr(_Redactor, "_folded_line"), "hook missing on this head"
    calls = []
    real_hits, real_line = _Redactor._dry_hits, _Redactor._folded_line
    monkeypatch.setattr(
        _Redactor, "_dry_hits", staticmethod(lambda t: calls.append(1) or real_hits(t))
    )
    monkeypatch.setattr(
        _Redactor,
        "_folded_line",
        lambda self, ln, *more: calls.append(1) or real_line(self, ln, *more),
    )
    out = redact("é\n" * 20_000).text
    assert out == "é\n" * 20_000
    assert calls == [], len(
        calls
    )  # FAIL-BEFORE: 2 runs of every pattern for each of the 20,000 lines


def test_the_fold_scan_stops_at_the_time_budget_with_input_too_large(monkeypatch):
    monkeypatch.setattr(defaults, "REDACT_BUDGET_S", -1.0)
    with pytest.raises(InputTooLarge):
        redact("café josé@example.com\n" * 50)  # FAIL-BEFORE: no check inside the fold pass


@pytest.mark.perf
def test_130k_short_non_ascii_lines_cost_a_small_multiple_of_ascii_lines():
    def timed(text):
        best = 1e9
        for _ in range(2):
            t0 = time.perf_counter()
            redact(text)
            best = min(best, time.perf_counter() - t0)
        return best

    ascii_s, non_s = timed("e\n" * 130_000), timed("é\n" * 130_000)
    assert non_s < 5 * ascii_s + 0.5, (ascii_s, non_s)  # the reviewed head took about 9x


def test_the_budget_is_checked_inside_the_per_line_work(monkeypatch):
    assert hasattr(_Redactor, "_over_budget"), "hook missing on this head"
    seen = []
    real = _Redactor._over_budget
    monkeypatch.setattr(
        _Redactor, "_over_budget", staticmethod(lambda d: seen.append(1) or real(d))
    )
    redact("mail josé@example.com now")
    assert (
        len(seen) >= 6
    )  # the scan, two sweeps, the suspect line, the rounds and the alignment each ask


def test_line_hits_asks_for_the_budget_once_per_pattern_and_once_after_the_last_pass(monkeypatch):
    assert hasattr(_Redactor, "_line_hits"), "hook missing on this head"
    seen = []
    real = _Redactor._over_budget
    monkeypatch.setattr(
        _Redactor, "_over_budget", staticmethod(lambda d: seen.append(1) or real(d))
    )
    _Redactor(None)._line_hits("café x", [0], 1e18)
    assert len(seen) == len(redact_mod.PATTERNS) + 1  # before each pattern, and after the last pass


def test_one_deadline_covers_the_text_and_all_its_views(monkeypatch):
    seen = []
    real = redact_mod.redact

    def spy(text, **kw):
        seen.append(kw.get("_deadline"))
        return real(text, **kw)

    monkeypatch.setattr("hadavin_sdk.guard.runmap.redact", spy)
    redact_text("mail josé@example.com %41KIA" + "IOSFODNN7EXAMPLE café", {})
    assert (
        len(seen) >= 2 and all(d is not None for d in seen) and len(set(seen)) == 1
    )  # FAIL-BEFORE: no deadline passed, 6 s per view


def test_a_spent_budget_refuses_before_any_line_is_treated(monkeypatch):
    assert hasattr(_Redactor, "_folded_line"), "hook missing on this head"
    calls = []
    real = _Redactor._folded_line
    monkeypatch.setattr(
        _Redactor, "_folded_line", lambda self, *a: calls.append(1) or real(self, *a)
    )
    monkeypatch.setattr(defaults, "REDACT_BUDGET_S", -1.0)
    text = "".join(f"user{i} café: josé{i}@exemple.fr" + chr(10) for i in range(3_000))
    with pytest.raises(InputTooLarge):
        redact(text)
    assert calls == []  # a work count, not a clock: nothing was treated once the budget was spent


def test_a_suspect_line_loops_only_the_patterns_that_matched_it(monkeypatch):
    assert hasattr(_Redactor, "_mask_in_place"), "hook missing on this head"
    seen = []
    real = _Redactor._mask_in_place

    def spy(self, body, folded, where, alike, only=None, marks=False):
        seen.append(only)
        return real(self, body, folded, where, alike, only=only, marks=marks)

    monkeypatch.setattr(_Redactor, "_mask_in_place", spy)
    assert redact("mail josé@example.com now").text == "mail <EMAIL_1> now"
    assert seen and all(o is not None and 0 < len(o) < 10 for o in seen), (
        seen
    )  # FAIL-BEFORE: every pattern (about 95) took a round


def test_the_budget_is_cpu_time_of_the_thread_not_the_wall_clock(monkeypatch):
    def forbidden():
        raise AssertionError("the wall clock was read")

    monkeypatch.setattr(time, "monotonic", forbidden)
    assert (
        redact("café josé@example.com").text == "café <EMAIL_1>"
    )  # FAIL-BEFORE: read time.monotonic
    redact_text("mail josé@example.com café", {})


def test_the_cookie_line_really_takes_three_rounds(monkeypatch):
    assert hasattr(_Redactor, "_aligned_fold"), "hook missing on this head"
    calls = []
    real = _Redactor._aligned_fold
    monkeypatch.setattr(
        _Redactor,
        "_aligned_fold",
        staticmethod(lambda b, d, *view: calls.append(b) or real(b, d, *view)),
    )
    assert redact("Cookie: sid=josé@example.com; a=bé").text == "Cookie: <SECRET_1>"
    assert len(calls) >= 3, calls  # two rounds that change the text and one that finds nothing


def test_aligned_fold_checks_the_budget_every_4096_characters():
    assert hasattr(_Redactor, "_aligned_fold"), "hook missing on this head"
    with pytest.raises(InputTooLarge):
        _Redactor._aligned_fold("é" * 5000, 0.0)  # a deadline in the past


def test_a_pattern_that_matched_nowhere_in_a_line_is_not_run_on_it(monkeypatch):
    assert hasattr(_Redactor, "_fold_scan"), "hook missing on this head"
    runs = []

    class Counting:
        def finditer(self, text):
            runs.append(text)
            return iter(())

        def sub(self, repl, text):
            return text

    monkeypatch.setattr(redact_mod, "PATTERNS", [*redact_mod.PATTERNS, ("TENANT", Counting())])
    out = redact("plain line" + chr(10) + "café josé@example.com ok").text
    assert "<EMAIL_1>" in out
    assert (
        "cafe jose@example.com ok" not in runs
    )  # the line's own round skipped it (only the whole-text scans ran it)
    assert len(runs) >= 2  # ... and the two whole-text scans did


# ===================================================== new rows (P2d-1) =====================================================
import unicodedata

from hadavin_sdk.guard import runmap, textnorm

BS = chr(92)
KEY_ = "AKIA" + "IOSFODNN7EXAMPLE"


class CountedClock:
    """A clock that returns `first` for the first `n` reads and `later` afterwards."""

    def __init__(self, first: float, n: int, later: float) -> None:
        self.first, self.n, self.later, self.reads = first, n, later, 0

    def __call__(self) -> float:
        self.reads += 1
        return self.first if self.reads <= self.n else self.later


@pytest.mark.perf
def test_align_1_the_per_character_class_agrees_with_the_fold_for_every_code_point():
    assert hasattr(redact_mod, "_char_class"), "hook missing on this head"
    redact_mod._char_class.cache_clear()
    try:
        for cp in range(0x110000):
            if 0xD800 <= cp <= 0xDFFF or 0x20 <= cp <= 0x7E:
                continue
            ch = chr(cp)
            cls = redact_mod._char_class(ch)
            assert cls is None or cls[0] == textnorm.fold(ch).replace("⁄", "/"), hex(cp)
    finally:
        redact_mod._char_class.cache_clear()


def test_mid_1_the_budget_is_checked_in_the_middle_of_a_line(monkeypatch):
    assert hasattr(_Redactor, "_aligned_fold"), "hook missing on this head"

    def run(n):
        monkeypatch.setattr(redact_mod.time, "thread_time", CountedClock(0.0, 1, 2.0))
        return _Redactor._aligned_fold("é" * n, 1.0)

    with pytest.raises(InputTooLarge):
        run(5000)
    assert run(4096) is not None
    with pytest.raises(InputTooLarge):
        run(4097)


def _percent_text() -> str:
    return "pw=ab%41 here"


def test_budget_1_a_spent_budget_after_stage_one_refuses(monkeypatch):
    monkeypatch.setattr(defaults, "REDACT_BUDGET_S", -1.0)
    with pytest.raises(InputTooLarge):
        redact_text(_percent_text(), {})


def test_budget_1b_the_check_after_stage_one_runs_before_any_decoded_mask(monkeypatch):
    calls = []
    real = runmap._decoded_masks
    monkeypatch.setattr(runmap, "_decoded_masks", lambda *a, **k: calls.append(1) or real(*a, **k))
    monkeypatch.setattr(runmap.time, "thread_time", CountedClock(0.0, 1, 100.0))
    with pytest.raises(InputTooLarge):
        redact_text(_percent_text(), {})
    assert calls == []  # with the check after stage 1 removed (mutant R2) this is [1]


def test_budget_2_the_deadline_is_shared_by_every_view(monkeypatch):
    text = "pw=ab%41 x " + BS + "u0041"
    assert len(runmap._views(text)) == 2
    assert redact(text).mapping == {}
    seen = []
    real = runmap.redact
    monkeypatch.setattr(runmap, "redact", lambda *a, **k: seen.append(1) or real(*a, **k))
    monkeypatch.setattr(runmap.time, "thread_time", CountedClock(0.0, 3, 100.0))
    with pytest.raises(InputTooLarge):
        redact_text(text, {})
    assert len(seen) == 2  # stage 1 and view one; the check before view two raised


def test_budget_3_the_alias_build_is_budgeted(monkeypatch):
    assert hasattr(_Redactor, "_over_budget"), "hook missing on this head"
    folded = []
    real = redact_mod.fold
    monkeypatch.setattr(redact_mod, "fold", lambda t, **k: folded.append(t) or real(t, **k))
    mapping = {f"<NAME_{i}>": f"Josée Martín{i} Zürich" for i in range(1, 301)}
    monkeypatch.setattr(redact_mod.time, "thread_time", CountedClock(0.0, 1, 100.0))
    with pytest.raises(InputTooLarge):
        redact("plain ascii text", mapping=mapping, _deadline=6.0)
    assert len(folded) <= 1, len(folded)  # with the check removed (mutant N15) all 300 are folded


def test_hostile_2_many_stored_originals_with_an_encoding_mark_stop_at_the_first_check(
    monkeypatch,
):
    originals = [f"ab{i:04d}%3Bzq9x" for i in range(300)]
    mapping = runmap.RunMap({f"<NAME_{i + 1}>": o for i, o in enumerate(originals)})
    undone = []
    real_undo = runmap.undo

    def spy(t, *a, **k):
        if t in originals:  # `_views` calls `undo` once on the whole text: not counted
            undone.append(t)
        return real_undo(t, *a, **k)

    monkeypatch.setattr(runmap, "undo", spy)
    monkeypatch.setattr(runmap.time, "thread_time", CountedClock(0.0, 2, 100.0))
    with pytest.raises(InputTooLarge):
        redact_text(" ".join(originals), mapping)
    assert len(undone) <= 1, len(undone)  # without the per-original check (mutant DM-1): 256


def test_hostile_2b_the_check_sits_at_the_top_of_the_loop_before_any_skip(monkeypatch):
    class CountingMap(dict):
        yielded = 0

        def items(self):
            for kv in list(super().items()):
                CountingMap.yielded += 1
                yield kv

    current = CountingMap({f"<NAME_{i}>": f"plain{i}" for i in range(300)})
    current["<NAME_999>"] = "ab%3Bzq9x"
    monkeypatch.setattr(runmap.time, "thread_time", lambda: 100.0)
    with pytest.raises(InputTooLarge):
        runmap._decoded_masks(current, "ab%3Bzq9x", 0.0)
    assert CountingMap.yielded == 1, CountingMap.yielded  # moved after the skips (DM-1b): 301


def test_dm_2_257_decomposed_names_refuse_the_text_and_256_do_not():
    def names(n):
        return [
            unicodedata.normalize("NFD", f"Zoé{chr(0x41 + i % 26)}{i:04d} Müller") for i in range(n)
        ]

    def run(n):
        ns = names(n)
        mapping = {f"<NAME_{i + 1}>": v for i, v in enumerate(ns)}
        return redact_text(" ; ".join(ns), mapping)

    with pytest.raises(InputTooLarge):
        run(257)
    run(256)


@pytest.mark.perf
def test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse():
    zw = chr(0x200B)
    cyr_a = chr(0x430)
    attack_key = KEY_.replace("A", chr(0x410), 1)
    cap = 262_144
    shapes = {
        "e-acute lines": "é\n" * 130_000,
        "fdfa": chr(0xFDFA) * 14_563,
        "cyrillic a": cyr_a * cap,
        "zwsp password": ("pass" + zw + "word=") * 16_000,
        "full-width password": "".join(chr(ord(c) + 0xFEE0) for c in "password=") * 20_000,
        "lookalike key lines": ("the key " + attack_key + "\n") * 4_000,
        "accented address lines": "mail josé@exemple.fr\n" * 7_000,
        "at-cap attack line": ("the key " + attack_key + " ") + cyr_a * (cap - 100),
        "4000 attack lines": ("k " + attack_key + "\n") * 4_000,
        "nested escapes": "%26amp%3B" * (cap // 9),
    }
    mc = chr(0x93E)
    shapes["devanagari lines"] = ("यह एक वाक्य है\n" * 18_000)[
        :cap
    ]  # every line holds spacing marks: a second view of each
    shapes["mark-split key lines"] = (("the key " + KEY_[:4] + mc + KEY_[4:] + "\n") * 7_000)[:cap]
    shapes["mc at cap"] = mc * cap
    # a refusal is the fail-closed answer to a text that spends the budget; only these two shapes may be refused (on a machine slower than the
    # test machine), every other shape must come back as a text, so that the assertions below really run for it
    may_refuse = {"e-acute lines", "devanagari lines"}
    for name, text in shapes.items():
        assert len(text) <= cap, name
        try:
            out = redact_text(text, runmap.RunMap())
        except (InputTooLarge, runmap.TooDeep):
            assert name in may_refuse, name
            continue
        assert KEY_[:12] not in out and attack_key not in out and KEY_[4:] not in out, name
        assert "exemple.fr" not in out.replace("<", ""), name
        if name in {"lookalike key lines", "at-cap attack line", "4000 attack lines"}:
            # a result that is not a refusal says what happened: the key is masked in place (a placeholder) or the line is withheld (the note)
            assert "<APIKEY_" in out or redact_mod.FOLD_NOTE in out, name
        if name == "mark-split key lines":
            assert out.count("<APIKEY_") >= 1 and mc not in out.replace("\n", ""), name


def test_view_1_the_clock_is_read_before_each_view_of_a_line(monkeypatch):
    """Review w4 m3: a round runs up to four views of a line and one view of a long line can take a large share of the budget, so the clock is
    read before EACH view, not once per round."""
    events: list[str] = []
    real_budget, real_fold = _Redactor._over_budget, _Redactor._aligned_fold

    def budget(deadline):
        events.append("clock")
        real_budget(deadline)

    def fold(body, deadline, *view):
        events.append("view")
        return real_fold(body, deadline, *view)

    real_mask = _Redactor._mask_in_place

    def mask(self, *a, **k):
        out = real_mask(self, *a, **k)
        events.append("mask")  # logged when the masking of one view is over
        return out

    monkeypatch.setattr(_Redactor, "_mask_in_place", mask)
    monkeypatch.setattr(_Redactor, "_over_budget", staticmethod(budget))
    monkeypatch.setattr(_Redactor, "_aligned_fold", staticmethod(fold))
    out = redact_text("caf\u00e9 password=Hunter2abc^ end", runmap.RunMap())
    assert "Hunter2" not in out
    assert events.count("view") >= 2
    assert all(events[i - 1] == "clock" for i, e in enumerate(events) if e == "view"), events


def _count_checks(monkeypatch):
    seen = []
    real = _Redactor._over_budget
    monkeypatch.setattr(
        _Redactor, "_over_budget", staticmethod(lambda d: seen.append(1) or real(d))
    )
    return seen


def test_clock_1_mask_in_place_looks_at_the_clock_once_per_pattern(monkeypatch):
    seen = _count_checks(monkeypatch)
    _Redactor(None)._mask_in_place("ab", "ab", [0, 1], bytearray(2))
    assert len(seen) == len(redact_mod.PATTERNS)


def test_clock_2_withhold_looks_at_the_clock_once_per_pattern_and_view(monkeypatch):
    seen = _count_checks(monkeypatch)
    _Redactor(None)._withhold(["x", "y"], "x")
    assert len(seen) == 2 * len(redact_mod.PATTERNS)


def test_clock_3_registering_a_written_value_looks_at_the_clock_once_per_alias_key(monkeypatch):
    seen = _count_checks(monkeypatch)
    written = "Hunter2\u093eabc\tdef"
    r = _Redactor(None)
    r._register_written("SECRET", written)
    assert len(seen) == len(redact_mod._alias_keys(written)) > 1


def test_clock_4_a_line_that_is_withheld_looks_at_the_clock_before_each_view(monkeypatch):
    seen = _count_checks(monkeypatch)
    line = (
        "АKIA" + "IOSFODNN7" + "EXAMPLE"
    )  # a Cyrillic capital A for the first letter of an access key id: withheld whole
    out = _Redactor(None)._folded_line(line)
    assert out.startswith(redact_mod.FOLD_NOTE), out
    views = 1 + len(redact_mod._view_specs(line))  # the fold and every other view of the line
    assert len(seen) >= 2 * len(redact_mod.PATTERNS) + 3 + views, (
        len(seen)
    )  # the withhold pass, one look before each view of the check that a view finds something new, and one before each round


def test_clock_5_a_tab_table_near_the_limit_is_refused_never_finished_late(monkeypatch):
    """Whatever read of the clock first sees the deadline passed, the call raises; it never goes on to finish. ``total`` is the number of reads
    a call makes when the clock never moves: it is above the number of pattern passes of two views, so the loops do look at the clock."""
    text = "id\tname\tvalue\tstatus\n" * 60
    clean = CountedClock(0.0, 10**9, 100.0)
    monkeypatch.setattr(runmap.time, "thread_time", clean)
    redact_text(text, {})
    total = clean.reads
    assert total > 2 * len(redact_mod.PATTERNS), total
    for k in (1, total // 4, total // 2, total - 2):
        clock = CountedClock(0.0, k, 100.0)
        monkeypatch.setattr(runmap.time, "thread_time", clock)
        with pytest.raises(InputTooLarge):
            redact_text(text, {})
        assert clock.reads <= total, (k, clock.reads, total)
