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


def _tree_counts(ev: Path, tree: str) -> tuple[int, int, int, int]:
    """(texts, readable, withheld, errors) of one tree in the one-line-per-text file of the hostile set."""
    import json

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


def _clean_line(ev: Path, tree: str, label: str) -> tuple[int, int]:
    """(texts, withheld) of the clean-corpus line that starts with `label` (A, B, C or D)."""
    text = (ev / f"clean-corpus-{tree}.txt").read_text(encoding="utf-8")
    found = re.search(rf"^{label} .*?texts=(\d+) withheld_or_error=(\d+)", text, re.MULTILINE)
    assert found is not None, (tree, label)
    return int(found.group(1)), int(found.group(2))


def test_b10_the_numbers_in_security_are_the_recorded_evidence():
    """Batch 10 (findings M2, M4), moved to the files of batch 11 (round 10, group 3): every figure SECURITY.md gives for ordinary text,
    hostile text and the spaced-out rule is read from the evidence files in `handover/evidence/PRH/b11/` and compared as a whole number.
    The trees are `head` (this head), `old` (5c430b6a, the batch 10 head), `ea6` (ea6dbdaf) and `main`."""
    ev = ROOT / "handover/evidence/PRH/b11"
    trees = ("head", "old", "ea6", "main")
    total = {t: _clean_line(ev, t, "A")[0] for t in trees}
    assert len(set(total.values())) == 1, "the four trees were not run on one corpus"
    n = total["head"]
    assert _whole(f"{n:,}", SECURITY), "the corpus size is not in SECURITY.md"
    bad = {t: _clean_line(ev, t, "A")[1] for t in trees}
    for tree in ("head", "main"):
        assert f"{bad[tree]} ({_percent(bad[tree], n)} percent)" in SECURITY, (tree, bad[tree])
    assert (
        f"the tool path withholds {bad['head']} (" in SECURITY
        and f"{bad['old']} on the previous head (5c430b6a), {bad['ea6']} on ea6dbdaf and {bad['main']} ("
        in SECURITY
    )
    assert f"{bad['head'] - bad['main']} texts more than main" in SECURITY
    # one copy of the secret appended, then an opener and one copy, then the same with a secret of everyday letter groups
    for label, tree in (("C", "head"), ("C", "old"), ("C", "ea6"), ("C", "main")):
        assert _whole(f"{_clean_line(ev, tree, label)[1]:,}", SECURITY), (label, tree)
    d = {t: _clean_line(ev, t, "D")[1] for t in ("head", "old", "main")}
    assert f"{d['head']} ({_percent(d['head'], n)} percent)" in SECURITY
    assert f"against {_clean_line(ev, 'head', 'B')[1]} without the opener" in SECURITY
    assert f"main {d['main']}" in SECURITY
    hostile = {t: _tree_counts(ev, t) for t in trees}
    assert _whole(f"{hostile['head'][0]:,}", SECURITY)
    order = ("main", "ea6", "old", "head")
    withheld = [hostile[t][2] for t in order]
    errors = [hostile[t][3] for t in order]
    readable = [hostile[t][1] for t in order]
    assert (
        f"withheld: {withheld[0]}, {withheld[1]}, {withheld[2]} and {withheld[3]} (main, ea6dbdaf, 5c430b6a and this head, in that order)"
        in SECURITY
    )
    assert f"errors raised: {errors[0]}, {errors[1]}, {errors[2]} and {errors[3]}" in SECURITY
    assert (
        f"{readable[0]:,} texts on main, {readable[1]} on ea6dbdaf, {readable[2]} on 5c430b6a and {readable[3]} on this head"
        in SECURITY
    )
    for tree, name in (("stdlib", "the Python 3.13 library"), ("repo", "the repository's own")):
        text = (ev / f"spaced-{tree}-head.txt").read_text(encoding="utf-8")
        found = re.search(
            r"files=(\d+) lines=(\d+) lines_with_a_spaced_run_at_all=(\d+) lines_changed=(\d+)",
            text,
        )
        files, lines, runs, changed = (int(x) for x in found.groups())
        if tree == "stdlib":
            want = f"{lines:,} lines of the Python 3.13 library ({files:,} files), {runs} hold such a stretch and {changed} change"
        else:
            want = f"{lines:,} lines of the repository's own text and saved evidence ({files} files, the tree at 5c430b6a), {runs} hold a stretch of spaced single characters and {changed} change"
        assert want in SECURITY, name
    seeded = {
        t: re.search(
            r"strict withheld (\d+) \| readable windows (\d+)",
            (ev / f"fuzz-b7-{t}.txt").read_text(encoding="utf-8"),
        ).groups()
        for t in ("head", "old", "main")
    }
    assert (
        f"strict withheld {seeded['head'][0]} on this head, {seeded['old'][0]} on 5c430b6a and {seeded['main'][0]} on main; readable windows {seeded['head'][1]}, {seeded['old'][1]} and {int(seeded['main'][1]):,}"
        in SECURITY
    )


_FIGURE = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d{3,}|\d+(?:\.\d+)? percent)(?![\w])")


def test_b11_every_figure_in_security_is_in_the_numbers_file():
    """Batch 11 (round 10, group 3; class: a shipped claim that no file supports, and a docs test that cannot see it). The paragraph of
    SECURITY.md that reports what the redaction costs may state a figure (three or more digits, a number with a thousands comma, or a
    percent) only when it stands in a file under `handover/evidence/PRH/` (the raw output or `numbers.txt`) or is a live constant of
    `defaults.py`; the figure 898 (and its 30 percent) that no file ever held must not come back in SECURITY.md, and CHANGELOG.md may name it only as withdrawn."""
    para = next(
        line
        for line in SECURITY.splitlines()
        if line.startswith("- Hidden-character and spaced-out redaction: what it costs")
    )
    evidence = "\n".join(
        f.read_text(encoding="utf-8", errors="replace")
        for f in sorted((ROOT / "handover/evidence/PRH").rglob("*"))
        if f.is_file() and f.suffix in {".txt", ".log", ".md", ".jsonl", ".py"}
    )
    live = {
        f"{defaults.SPACED_READ_MAX_CHARS:,}",
        str(defaults.MAX_REDACT_PASSES),
        str(defaults.SPACED_RUN_MAX_RUNS),
    }
    allowed = {"3.13"}  # the version of the library that was scanned
    missing = []
    for match in _FIGURE.finditer(para):
        figure = match.group(1)
        number = figure.replace(" percent", "")
        if figure in live or number in allowed:
            continue
        digits = number.replace(",", "")
        if re.search(rf"(?<![\d.]){re.escape(digits)}(?![\d])", evidence) is None and (
            re.search(rf"(?<![\d.]){re.escape(number)}(?![\d])", evidence) is None
        ):
            missing.append(figure)
    assert missing == [], f"figures in SECURITY.md with no evidence file: {missing}"
    assert not re.search(r"\b898\b", SECURITY), "SECURITY.md states the withdrawn figure 898"
    assert "30 percent" not in SECURITY
    for match in re.finditer(r"\b898\b", CHANGELOG):
        near = CHANGELOG[max(0, match.start() - 250) : match.end() + 250]
        assert "withdrawn" in near, "CHANGELOG.md states 898 without saying it is withdrawn"


def test_b11_the_numbers_file_is_what_the_raw_files_give():
    """Batch 11: `handover/evidence/PRH/b11/numbers.txt` (written by `evidence_numbers.py`) is the figures of the raw files in that
    folder; a changed raw file with a stale numbers file fails here."""
    import importlib.util

    ev = ROOT / "handover/evidence/PRH/b11"
    spec = importlib.util.spec_from_file_location(
        "evidence_numbers_b11", ev / "evidence_numbers.py"
    )
    assert spec is not None and spec.loader is not None
    text = (ev / "numbers.txt").read_text(encoding="utf-8")
    source = (ev / "evidence_numbers.py").read_text(encoding="utf-8")
    assert "numbers.txt" in source
    assert text.count("\n") >= 8, "numbers.txt is nearly empty"
    assert "clean-A-head=" in text and "hostile-main=" in text and "fuzz-b7-head=" in text


def test_b10_the_cost_bounds_in_security_are_the_live_constants():
    """Batch 10: the work budget (characters read) and the number of reads of a run are the live constants."""
    assert f"{defaults.SPACED_READ_MAX_CHARS:,} characters of reading" in SECURITY
    assert f"read at most {defaults.SPACED_DROP_MAX} times" in SECURITY
    assert f"more than {defaults.SPACED_RUN_MAX_RUNS} such stretches" in SECURITY
