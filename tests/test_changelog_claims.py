"""The CHANGELOG names tests, files and numbers; a name that no longer exists or a number that is no longer true is a claim
nobody can check. Round 16: names are found with `ast` (an exact `def name(`, not a text search), tests are searched in every
folder under `tests/`, any repository path may be named, and the counts of the batch 16 entry are computed here."""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "tests"))


def _defined_test_names() -> set[str]:
    names: set[str] = set()
    for path in (ROOT / "tests").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                names.add(node.name)
    return names


def test_every_test_name_in_the_changelog_is_defined_in_tests():
    defined = _defined_test_names()
    named = set(re.findall(r"`(test_[A-Za-z0-9_]+)`", TEXT))
    assert named, "the CHANGELOG names no test: the scan is empty"
    missing = sorted(n for n in named if n not in defined)
    assert missing == [], f"the CHANGELOG names tests that do not exist: {missing}"


def test_every_repository_path_in_the_changelog_exists():
    paths = set(
        re.findall(
            r"`((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:py|md|yaml|yml|sql|toml|txt|json|sh))`",
            TEXT,
        )
    )
    # a path under the package is written without the `src/hadavin_sdk/` prefix in prose, and a few are examples
    # (a file the reader makes); only paths that start at a folder of this repository are checked
    # `handover/` is the studio's notes folder: it is on its own branch, not in the code branches, so its paths are not checked here
    roots = {p.name for p in ROOT.iterdir() if p.is_dir()} - {"handover"}
    own = sorted(p for p in paths if p.split("/")[0] in roots)
    assert own, "the CHANGELOG names no repository path: the scan is empty"
    missing = [p for p in own if not (ROOT / p).exists()]
    assert missing == [], f"the CHANGELOG names files that do not exist: {missing}"


def _computed_counts() -> dict[str, int]:
    import _guard_allowances as allowances
    import stage_mutants
    import test_guard_reasons as reasons
    import test_stage_names as names

    handlers = 0
    for path in (ROOT / "src").rglob("*.py"):
        handlers += sum(
            1 for line in path.read_text(encoding="utf-8").splitlines() if "noqa: BLE001" in line
        )
    own = len(allowances.NEW_ALLOWED)
    return {
        "REASONS": len(allowances.REASONS),
        "CHECKED": len(allowances.REASONS) - len(reasons.UNCHECKED),
        "OWN": own,
        "ALL": own + len(names.GUARD_ALLOWED),
        "MUTANTS": len(stage_mutants.M),
        "HANDLERS": handlers,
    }


def test_the_counts_of_the_batch_16_entry_are_the_counts_of_this_head():
    got = _computed_counts()
    claim = re.search(
        r"\*\*Counts at this head[^*]*\*\*\s*(\d+) reasons, (\d+) of them checked by code; the allowance table has (\d+) rows of "
        r"its own plus the older ones \((\d+) rows in all\); (\d+) mutants in `tests/stage_mutants.py`; (\d+) handlers marked",
        TEXT,
    )
    assert claim, "the batch 16 entry has no sentence of counts in the written form"
    said = dict(
        zip(
            ("REASONS", "CHECKED", "OWN", "ALL", "MUTANTS", "HANDLERS"),
            map(int, claim.groups()),
            strict=True,
        )
    )
    assert said == got, f"the CHANGELOG counts {said} are not the counts of this head {got}"
