"""PR H batch 9, group 5 and group 6: what SECURITY.md and CHANGELOG.md say is pinned to the code. Not part of the mutant run (the
mutant run copies only the test files and the source, not the documents)."""

import re
from pathlib import Path

from hadavin_sdk import defaults

ROOT = Path(__file__).resolve().parents[1]
SECURITY = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_b9_g5_security_says_a_value_of_no_pattern_shape_is_not_read():
    """Group 5: the statement `tests/test_prh_b9.py::test_b9_g5_a_value_of_no_pattern_shape_is_not_read...` proves, in the text."""
    assert "of no pattern's shape" in SECURITY, (
        "SECURITY.md must say that a value of no pattern's shape is not read"
    )
    assert "NOT covered, by design" in SECURITY


def test_b9_g6_the_spaced_out_numbers_in_security_are_the_live_constants():
    """Group 6: every number SECURITY.md gives for the spaced-out rule is read from the live constant."""
    bullet = next(line for line in SECURITY.splitlines() if "spaces between its characters" in line)
    want = {
        "12 or more characters": defaults.SPACED_VALUE_MIN_CHARS,
        "10 or more single-character words": defaults.SPACED_RUN_MIN_TOKENS,
        "at least 6 different characters": defaults.SPACED_RUN_MIN_DISTINCT,
        "more than 32 such stretches": defaults.SPACED_RUN_MAX_RUNS,
    }
    for phrase, live in want.items():
        assert phrase in bullet, phrase
        assert str(live) in phrase, f"{phrase!r} is not the live value {live}"


def _whole(number: int | str, text: str) -> bool:
    """Is `number` in `text` as a whole number (not a part of a longer one)?"""
    return re.search(rf"(?<![\d,.]){re.escape(str(number))}(?![\d,])", text) is not None


def _evidence_number(path: Path, key: str) -> int:
    """The whole number after `key=` in an evidence file (`texts=7950 withheld_or_error=126 ...`)."""
    found = re.search(rf"\b{re.escape(key)}=(\d+)\b", path.read_text(encoding="utf-8"))
    assert found is not None, f"{key} is not in {path}"
    return int(found.group(1))


def _percent(part: int, whole: int) -> str:
    return f"{100 * part / whole:.2f}"


def test_b10_the_pass_counts_in_the_documents_are_the_ones_the_tests_pin():
    """Batch 10 (finding M2): the seeded worst (`16`) and the most any recorded row needs (`8`) are read from the tests that assert them;
    CHANGELOG.md and defaults.py state those numbers, and the old ones (14 and 7) are not stated as current."""
    steps = (ROOT / "tests/test_prh_steps.py").read_text(encoding="utf-8")
    worst = int(re.search(r'state\["peak"\] == (\d+)', steps).group(1))
    rows = int(re.search(r"assert worst == (\d+), worst", steps).group(1))
    defaults_text = (ROOT / "src/hadavin_sdk/defaults.py").read_text(encoding="utf-8")
    assert re.search(rf"their worst is {worst}\)", defaults_text), (
        "defaults.py names another seeded worst"
    )
    assert f"MAX_REDACT_PASSES = {defaults.MAX_REDACT_PASSES}" in defaults_text
    assert defaults.MAX_REDACT_PASSES > worst
    assert f"(their worst is {worst}) and that no recorded row needs more than {rows}" in CHANGELOG
    assert "their worst is 14" not in CHANGELOG and "needs more than 7;" not in CHANGELOG


def test_b10_the_numbers_in_security_are_the_recorded_evidence():
    """Batch 10 (findings M2, M4): every figure SECURITY.md gives for ordinary text, hostile text and the spaced-out rule is read from
    the evidence files in `handover/evidence/PRH/b10/` and compared as a whole number."""
    ev = ROOT / "handover/evidence/PRH/b10"
    texts = {
        t: _evidence_number(ev / f"clean-corpus-{t}.txt", "texts")
        for t in ("head", "base", "old", "main")
    }
    assert len(set(texts.values())) == 1, "the four trees were not run on one corpus"
    total = texts["head"]
    bad = {t: _evidence_number(ev / f"clean-corpus-{t}.txt", "withheld_or_error") for t in texts}
    assert _whole(f"{total:,}", SECURITY), "the corpus size is not in SECURITY.md"
    for tree in ("head", "old", "base", "main"):
        assert _whole(bad[tree], SECURITY), (tree, bad[tree])
    for tree in ("head", "old", "main"):
        assert f"{bad[tree]} ({_percent(bad[tree], total)} percent)" in SECURITY, (tree, bad[tree])
    assert f"{bad['head'] - bad['main']} texts more than main" in SECURITY
    # the hostile set: counts per tree from the one-line-per-text files
    import json

    def counts(tree: str) -> tuple[int, int, int, int]:
        rows = [
            json.loads(line)
            for line in (ev / f"cells-{tree}.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        return (
            len(rows),
            sum(1 for r in rows if r["readable"]),
            sum(1 for r in rows if r["withheld"]),
            sum(1 for r in rows if r["err"]),
        )

    n, *_ = counts("head")
    assert _whole(f"{n:,}", SECURITY)
    withheld = [counts(t)[2] for t in ("main", "old", "base", "head")]
    errors = [counts(t)[3] for t in ("main", "old", "base", "head")]
    # the order in the text is main, ea6dbdaf, the batch 9 head, this head
    assert f"withheld: {withheld[0]}, {withheld[1]}, {withheld[2]} and {withheld[3]}" in SECURITY
    assert f"errors raised: {errors[0]}, {errors[1]}, {errors[2]} and {errors[3]}" in SECURITY
    readable = [counts(t)[1] for t in ("main", "old", "base", "head")]
    assert (
        f"{readable[0]:,} texts on main, {readable[1]} on ea6dbdaf, {readable[2]} on the batch 9 head and {readable[3]} on this head"
        in SECURITY
    )
    spaced = (ev / "spaced-stdlib-head.txt").read_text(encoding="utf-8")
    found = re.search(
        r"files=(\d+) lines=(\d+) lines_with_a_spaced_run_at_all=(\d+) lines_changed=(\d+)", spaced
    )
    files, lines, runs, changed = (int(x) for x in found.groups())
    assert (
        f"{lines:,} lines of the Python 3.13 library ({files:,} files), {runs} hold such a stretch and {changed} change"
        in SECURITY
    )
    repo = (ev / "spaced-repo-head.txt").read_text(encoding="utf-8")
    found = re.search(
        r"files=(\d+) lines=(\d+) lines_with_a_spaced_run_at_all=(\d+) lines_changed=(\d+)", repo
    )
    files, lines, runs, changed = (int(x) for x in found.groups())
    assert (
        f"{lines:,} lines of the repository's own text and saved evidence ({files} files), {runs} hold a stretch of spaced single characters and {changed} change"
        in SECURITY
    )


def test_b10_the_cost_bounds_in_security_are_the_live_constants():
    """Batch 10: the work budget (characters read) and the number of reads of a run are the live constants."""
    assert f"{defaults.SPACED_READ_MAX_CHARS:,} characters of reading" in SECURITY
    assert f"read at most {defaults.SPACED_DROP_MAX} times" in SECURITY
    assert f"more than {defaults.SPACED_RUN_MAX_RUNS} such stretches" in SECURITY
