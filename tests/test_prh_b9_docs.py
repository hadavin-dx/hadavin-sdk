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


# The batch 10 and 11 test that compared SECURITY.md with the batch 11 evidence files was replaced in batch 12 by the figure tests below,
# which read every figure of the paragraph and of the CHANGELOG item against numbers.txt, itself rebuilt from the raw files of batch 12.


# Batch 12 (round 11, issue 4): EVERY figure (one digit or more, a thousands comma, a decimal, a percent) of the SECURITY.md paragraph on
# what the redaction costs and of the CHANGELOG.md item of the batch is compared with the numbers file of the batch, and with nothing else
# (the batch 11 test searched all evidence files for any figure of three digits, so almost any figure was found).
_FIGURE = re.compile(r"(?<![\w.+\\/#:-])(\d[\d,]*(?:\.\d+)?)(?![\w])(?! ?(?:-|/)?[A-Za-z]*\d)")
# numbers that are code, not measurements: batch and round numbers, sizes of the rules in the code (8 and 12 characters, 6 on each side,
# 24 passes, ...), the 2026 date, the Python version, the file and mutant numbers the text names
_CODE_NUMBERS = {
    *map(str, range(1, 13)),
    "14", "16", "17", "24", "60", "63", "64", "4096", "2026", "3.13", "15.1",
    "186", "187", "188", "189", "190", "191", "192", "193", "194", "195", "196", "197", "198", "199", "200", "201", "202",
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
    assert not re.search(r"(?<![\d.])30 percent", SECURITY), (
        "SECURITY.md states the withdrawn 30 percent"
    )
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
    import runpy
    import shutil

    ev = ROOT / "handover/evidence/PRH/b12"
    work = tmp_path / "b12"
    shutil.copytree(ev, work, ignore=shutil.ignore_patterns("numbers.txt", "__pycache__"))
    runpy.run_path(
        str(work / "evidence_numbers.py"), run_name="__main__"
    )  # writes work / "numbers.txt"
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
