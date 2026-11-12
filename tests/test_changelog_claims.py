"""The CHANGELOG names tests and files in backticks; a name that no longer exists is a claim nobody can check."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_every_test_name_in_the_changelog_is_defined_in_tests():
    defined = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "tests").glob("*.py"))
    missing = sorted(
        n for n in set(re.findall(r"`(test_[A-Za-z0-9_]+)`", TEXT)) if f"def {n}" not in defined
    )
    assert missing == [], f"the CHANGELOG names tests that do not exist: {missing}"


def test_every_path_under_tests_src_or_tools_in_the_changelog_exists():
    paths = set(
        re.findall(r"`((?:tests|src|tools)/[A-Za-z0-9_./-]+\.(?:py|md|yaml|sql|toml))`", TEXT)
    )
    missing = sorted(p for p in paths if not (ROOT / p).exists())
    assert paths and missing == [], f"the CHANGELOG names files that do not exist: {missing}"
