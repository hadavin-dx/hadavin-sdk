"""Counts, for every mutant of the five mutant files whose file is guard/runmap.py or guard/redact.py, how often its `old` text
occurs in a tree (ticket G4, 13.3). Usage: python handover/core-c/evidence/g4_snippets.py <repo-root> [<tree-root>]
`repo-root` supplies the mutant lists, `tree-root` (default: repo-root) the source whose files are counted. Read-only.
Prints `module, name, file, count` per entry, a SUMMARY line and the entries not found exactly once."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
tree = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else repo
sys.path.insert(0, str(repo))
sys.path.insert(0, str(repo / "tests"))
MODULES = ["redact_mutants", "p1d_a_mutants", "gate_mutants", "stage_mutants", "textnorm_mutants"]
TARGETS = ("guard/runmap.py", "guard/redact.py")
rows, odd = [], []
for mod in MODULES:
    m = importlib.import_module(mod)
    for mut in m.M:
        if not mut.file.endswith(TARGETS):
            continue
        count = (tree / mut.file).read_text().count(mut.old)
        rows.append((mod, mut.name, mut.file, count))
        print(mod, "|", mut.name, "|", mut.file, "|", count)
        if count != 1:
            odd.append((mod, mut.name, count))
print(f"SUMMARY: {len(rows)} mutants on runmap.py/redact.py; not exactly once: {len(odd)}")
for mod, name, count in odd:
    print("NOT ONCE:", mod, name, count)
