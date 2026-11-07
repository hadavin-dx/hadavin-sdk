"""The vulture whitelist may only hold names that still exist where it says they do.

Every entry of vulture_whitelist.py reads `name  # kind in path[, path]` (a leading `_.` means an attribute or method).
This check fails when an entry has no such comment, names a file that is gone, or names an identifier that the file no
longer DEFINES (parsed with `ast`: a def, a class, an assignment target, an attribute assigned, a keyword-free import
alias; a mention in a comment, a docstring or a call does not count); and when the same name is listed twice (one line
per name, all its files in the comment).

Usage: python tools/vulture_whitelist_check.py   (from the repository root)
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = re.compile(
    r"^(\S+)  # (variable|function|method|attribute|class|property) in (\S+\.py(?:, \S+\.py)*)$"
)


def defined_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add((node.asname or node.name).split(".")[0])
    return names


def main() -> int:
    problems: list[str] = []
    seen: set[str] = set()
    n = 0
    lines = (ROOT / "vulture_whitelist.py").read_text(encoding="utf-8").splitlines()
    for no, line in enumerate(lines, 1):
        if not line.strip() or line.startswith("#"):
            continue
        n += 1
        m = ENTRY.match(line)
        if not m:
            problems.append(f"line {no}: not in the form `name  # kind in path.py`")
            continue
        name, _kind, paths = m.groups()
        if name in seen:
            problems.append(f"line {no}: {name} is listed twice (merge the files into one comment)")
        seen.add(name)
        bare = name.removeprefix("_.")
        for rel in paths.split(", "):
            path = ROOT / "src" / "hadavin_sdk" / rel
            if not path.exists():
                problems.append(f"line {no}: {name}: {rel} does not exist")
            elif bare not in defined_names(ast.parse(path.read_text(encoding="utf-8"))):
                problems.append(
                    f"line {no}: {name}: {rel} no longer defines it (delete or fix the entry)"
                )
    print(f"{n} entries, {len(problems)} problems")
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
