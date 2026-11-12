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


# Batch 12 (round 11, issue 4): EVERY figure (one digit or more, a thousands comma, a decimal, a percent) of the SECURITY.md paragraph on
# what the redaction costs and of the CHANGELOG.md item of the batch is compared with the numbers file of the batch, and with nothing else
# (the batch 11 test searched all evidence files for any figure of three digits, so almost any figure was found).
_FIGURE = re.compile(r"(?<![\w.+\\/#:-])(\d[\d,]*(?:\.\d+)?)(?![\w])(?! ?(?:-|/)?[A-Za-z]*\d)")
# numbers that are code, not measurements: batch and round numbers, sizes of the rules in the code (8 and 12 characters, 6 on each side,
# 24 passes, ...), the 2026 date, the Python version, the file and mutant numbers the text names
_CODE_NUMBERS = {
    *map(str, range(1, 13)),
    "14", "16", "17", "24", "60", "64", "2026", "3.13", "15.1",
    "186", "187", "188", "189", "190", "191", "192", "193", "194", "195", "196", "197", "198", "199", "200",
    "161", "162", "163", "165", "167", "168", "170", "171", "172", "173", "174", "175", "176", "178", "180", "181", "182", "183", "184",
}  # fmt: skip
_PARAGRAPH_START = "- Hidden-character and spaced-out redaction: what it costs"
_CHANGELOG_START = "- **Redaction, hidden characters, batch 12"


def _quoted_figures():
    para = next(line for line in SECURITY.splitlines() if line.startswith(_PARAGRAPH_START))
    item = next(line for line in CHANGELOG.splitlines() if line.startswith(_CHANGELOG_START))
    figures = []
    for where, text in (("SECURITY.md", para), ("CHANGELOG.md", item)):
        text = re.sub(
            r"\b(?:20\d\d-\d\d-\d\d|[0-9a-f]{8})\b", " ", text
        )  # dates and short commit ids
        text = re.sub(
            r"`[^`]*`", " ", text
        )  # code spans (the spellings and file names the text shows)
        for match in _FIGURE.finditer(text):
            figures.append((where, match.group(1).rstrip(",.")))
    return figures


def _missing_figures(figures, known):
    return sorted({f"{where}: {figure}" for where, figure in figures if figure not in known})


def _numbers_tokens():
    numbers = (ROOT / "handover/evidence/PRH/b12/numbers.txt").read_text(encoding="utf-8")
    return set(re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?![\w])", numbers))


def test_b12_every_figure_in_security_and_the_changelog_is_in_the_numbers_file():
    """Batch 12 (round 11, issue 4; class: a shipped figure that no file supports, and a docs test that cannot see it). Every figure of
    the SECURITY.md paragraph on the cost of the redaction and of the batch 12 CHANGELOG item, two digits included, is one of the
    figures of `handover/evidence/PRH/b12/numbers.txt` (written by `evidence_numbers.py` from the raw files of that folder), or is in
    the list of code numbers above, or is a live constant of `defaults.py`. The withdrawn figure 898 must not come back."""
    live = {
        f"{defaults.SPACED_READ_MAX_CHARS:,}",
        str(defaults.SPACED_READ_MAX_CHARS),
        str(defaults.MAX_REDACT_PASSES),
        str(defaults.SPACED_RUN_MAX_RUNS),
        str(defaults.SPACED_DROP_MAX),
        str(defaults.SPACED_VALUE_MIN_CHARS),
        f"{defaults.MAX_REDACT_CHARS:,}" if hasattr(defaults, "MAX_REDACT_CHARS") else "262,144",
        str(int(defaults.REDACT_BUDGET_S)),
    }
    known = _numbers_tokens() | _CODE_NUMBERS | live
    figures = _quoted_figures()
    assert len(figures) >= 20, (
        f"the figure reader found only {len(figures)} figures: it is not reading the paragraphs"
    )
    missing = _missing_figures(figures, known)
    assert missing == [], f"figures with no line in numbers.txt and no code meaning: {missing}"
    assert not re.search(r"\b898\b", SECURITY), "SECURITY.md states the withdrawn figure 898"
    assert "30 percent" not in SECURITY
    for match in re.finditer(r"\b898\b", CHANGELOG):
        near = CHANGELOG[max(0, match.start() - 250) : match.end() + 250]
        assert "withdrawn" in near, "CHANGELOG.md states 898 without saying it is withdrawn"


def test_b12_a_planted_wrong_figure_is_found_by_the_figure_test():
    """Batch 12 (issue 4; the proof asked for). A figure that is in no file (here 424,242 and 77) added to the paragraph is reported as
    missing: the test above can fail.  (Documents are not part of the mutant run, so there is no mutant for this test; the proof is this test.)"""
    real = _quoted_figures()
    planted = real + [("SECURITY.md", "424,242"), ("SECURITY.md", "77")]
    known = _numbers_tokens() | _CODE_NUMBERS
    missing = _missing_figures(planted, known)
    assert "SECURITY.md: 424,242" in missing and "SECURITY.md: 77" in missing, (
        "a planted figure was not reported"
    )
    assert (
        _missing_figures(real, known | {f for _w, f in real}) == []
    )  # and a figure that has a line is not reported


def test_b12_the_numbers_file_is_what_the_raw_files_give(tmp_path):
    """Batch 12 (issue 4; the b11 test of this name loaded a spec it never ran). `evidence_numbers.py` is RUN here on a copy of the raw files
    of the folder and its output must equal the committed `numbers.txt` line for line: a raw file changed after the numbers file was
    written, or a numbers file edited by hand, fails."""
    import shutil
    import subprocess
    import sys

    ev = ROOT / "handover/evidence/PRH/b12"
    work = tmp_path / "b12"
    shutil.copytree(ev, work, ignore=shutil.ignore_patterns("numbers.txt", "__pycache__"))
    done = subprocess.run(
        [sys.executable, "-I", str(work / "evidence_numbers.py")],
        capture_output=True, text=True, timeout=120, check=False,
    )  # fmt: skip
    assert done.returncode == 0, done.stderr[-400:]
    made = (work / "numbers.txt").read_text(encoding="utf-8")
    assert made == (ev / "numbers.txt").read_text(encoding="utf-8"), (
        "numbers.txt is not what the raw files give"
    )
    assert (
        made.count("\n") >= 20
        and "clean-A-head=" in made
        and "hostile-main=" in made
        and "fuzz-b7-head=" in made
    )


def test_b10_the_cost_bounds_in_security_are_the_live_constants():
    """Batch 10: the work budget (characters read) and the number of reads of a run are the live constants."""
    assert f"{defaults.SPACED_READ_MAX_CHARS:,} characters of reading" in SECURITY
    assert f"read at most {defaults.SPACED_DROP_MAX} times" in SECURITY
    assert f"more than {defaults.SPACED_RUN_MAX_RUNS} such stretches" in SECURITY
