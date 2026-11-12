"""Check that a builder's notes hold one line for every test that is new or changed against a base commit.

    python tools/notes_lines_check.py <base-commit> <notes.md> <test file> [<test file> ...]

A test is "new or changed" when its function is missing in the base commit's copy of the file or its syntax tree
differs from it. The notes must hold a table row (a line that starts with `|`) that names the test id in backticks
and ends in a reason cell of at least `MIN_REASON` characters (the command that shows it can fail, the killing mutant,
or the control reason). A test that existed in the base and is gone now is a problem too (a test is never deleted).
Prints one plain line per problem and exits 1; exits 0 when every test has its line. It runs `git show` only, with
a fixed argument list and no shell, and reads the files it is given; it never writes."""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_REASON = 12  # characters of the last cell: a bare "x" or "ok" is no reason


def tests_of(source: str) -> dict[str, str]:
    """name -> `ast.dump` of every top-level `test_*` function of `source`."""
    return {
        n.name: ast.dump(n)
        for n in ast.parse(source).body
        if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
    }


def changed_tests(old: str, new: str) -> tuple[list[str], list[str]]:
    """(new or changed test names, names that existed before and are gone), each sorted."""
    before, after = tests_of(old), tests_of(new)
    changed = sorted(n for n, d in after.items() if before.get(n) != d)
    gone = sorted(set(before) - set(after))
    return changed, gone


def lines_of(notes: str) -> dict[str, str]:
    """test id -> its reason cell, for every table row that names a test id in backticks."""
    out: dict[str, str] = {}
    for line in notes.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        for cell in cells:
            for name in re.findall(r"`(test_\w+)`", cell):
                out[name] = cells[-1]
    return out


def problems(changed: list[str], gone: list[str], notes: str, label: str) -> list[str]:
    rows = lines_of(notes)
    out = [
        f"{label}: the test {n} is new or changed and has no row with a reason in the notes"
        for n in changed
        if len(rows.get(n, "")) < MIN_REASON
    ]
    out += [
        f"{label}: the test {n} existed in the base commit and is gone (never delete a test)"
        for n in gone
    ]
    return out


def _base_source(base: str, rel: str) -> str:
    git = shutil.which("git")
    if git is None:
        raise SystemExit("git was not found")
    proc = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git, "show", f"{base}:{rel}"], capture_output=True, text=True, check=False
    )
    return proc.stdout if proc.returncode == 0 else ""  # a file new since the base has no old text


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(
            "usage: notes_lines_check.py <base-commit> <notes.md> <test file> [...]",
            file=sys.stderr,
        )
        return 2
    base, notes_path, files = argv[0], Path(argv[1]), argv[2:]
    notes = notes_path.read_text(encoding="utf-8")
    bad: list[str] = []
    for rel in files:
        changed, gone = changed_tests(
            _base_source(base, rel), Path(rel).read_text(encoding="utf-8")
        )
        bad += problems(changed, gone, notes, rel)
    for line in bad:
        print(line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
