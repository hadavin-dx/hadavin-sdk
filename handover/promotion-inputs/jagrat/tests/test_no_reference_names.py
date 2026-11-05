"""Guard: no reference-build name (or the "PR <number>" provenance mention) in any tracked text file.

NOT the full hygiene scan: it does not look for secrets, personal data or account numbers, and it does not read
git history. Words are built from fragments so this file carries none of them.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDS = ["hel" + "ios", "war" + "den", "bho" + "vix", "PR" + r"\W*" + "132"]
PATTERN = re.compile("|".join(w for w in WORDS), re.IGNORECASE)
SKIP = {"uv.lock"}


def hits(root: Path, files: list[str]) -> list[str]:
    out = []
    for name in files:
        p = root / name
        if name in SKIP or not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        out += [f"{name}:{i}" for i, ln in enumerate(text.splitlines(), 1) if PATTERN.search(ln)]
        if PATTERN.search(name):
            out.append(f"{name}: file name")
    return out


def tracked_files() -> list[str]:
    cmd = ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    return res.stdout.splitlines()


def test_no_reference_name_in_tracked_text():
    assert hits(ROOT, tracked_files()) == []


def test_guard_catches_a_reference_name(tmp_path):
    (tmp_path / "a.py").write_text(f"x = '{WORDS[1].upper()}'\n")
    (tmp_path / "b.py").write_text("x = 1\n")
    assert hits(tmp_path, ["a.py", "b.py"]) == ["a.py:1"]


def test_guard_catches_pr_mention_variants():
    for s in ("PR 13" + "2", "pr#13" + "2", "PR-13" + "2"):
        assert PATTERN.search(f"see {s}")
