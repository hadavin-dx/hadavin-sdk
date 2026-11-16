"""Mutation checks for tools/scan_repo.py: each test plants ONE weakening in a temporary copy of the script and asserts that
tests/test_scan_repo.py then FAILS (so the tests really pin that check). A control run on the unchanged copy must pass, otherwise a
"failure" could be an unrelated breakage. The real script and the real list are never modified (the copy lives in tmp_path)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "tools" / "scan_repo.py"
# the three tests that read the real repo and its real list are left out: only the planted-input tests judge the copy
DESELECT = "not real_list_says and not weakened and not the_real_repo_passes and not real_repo_has"

MUTATIONS = {
    "NUL skip moved before the checks": (
        "        hits += _check_suppressions(rel, text, data, listed, seen)\n",
        '        if b"\\0" in data:\n            continue\n        hits += _check_suppressions(rel, text, data, listed, seen)\n',
    ),
    "hash check dropped": ("elif listed[key] != hashlib.sha256(data).hexdigest():", "elif False:"),
    "glob check dropped": ('if any(ch in parts[0] for ch in "*?["):', "if False:"),
    "re.IGNORECASE removed": ("_I = re.IGNORECASE", "_I = 0"),
    "placeholder and short reason accepted": (
        "if len(parts) == 4 and all(parts) and reason_problem(parts[3]):",
        "if False:",
    ),
    "nested pyproject table check dropped": (
        'if low == "pyproject.toml" and "/" in rel and NESTED_PYPROJECT_TABLE.search(text):',
        "if False:",
    ),
    "file-level noqa without codes accepted": ("if BLANKET_FILE_NOQA.search(line)", "if False"),
    "NUL allowed for any extension": (
        "if Path(rel).suffix.lower() in BINARY_EXTENSIONS:",
        "if True:",
    ),
}


def _place(tmp_path: Path, source: str) -> Path:
    """tools/scan_repo.py reads ../tests/test_no_reference_material.py by default, so the copy gets the same neighbour."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tests").mkdir()
    banned = (ROOT / "tests" / "test_no_reference_material.py").read_text(encoding="utf-8")
    (tmp_path / "tests" / "test_no_reference_material.py").write_text(banned, encoding="utf-8")
    script = tmp_path / "tools" / "scan_repo.py"
    script.write_text(source, encoding="utf-8")
    return script


def _run(script: Path):
    env = {**os.environ, "SCAN_REPO_SCRIPT": str(script)}
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(ROOT / "tests" / "test_scan_repo.py"),
        "-q",
        "-x",
        "-p",
        "no:cacheprovider",
        "-k",
        DESELECT,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, env=env, cwd=ROOT)  # noqa: S603


def test_control_the_unchanged_copy_passes(tmp_path):
    r = _run(_place(tmp_path, REAL.read_text(encoding="utf-8")))
    assert r.returncode == 0, r.stdout[-1500:]


@pytest.mark.parametrize("name", list(MUTATIONS))
def test_each_planted_weakening_makes_the_scan_tests_fail(tmp_path, name):
    old, new = MUTATIONS[name]
    src = REAL.read_text(encoding="utf-8")
    assert src.count(old) == 1, (
        f"mutation anchor for {name!r} no longer matches the script exactly once"
    )
    r = _run(_place(tmp_path, src.replace(old, new)))
    assert r.returncode == 1, (
        f"{name}: the scan tests still passed on the weakened script\n{r.stdout[-1500:]}"
    )
