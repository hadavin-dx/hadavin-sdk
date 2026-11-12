"""EVIDENCE RUNNER own listing: controls of tests/test_q8b_batch8_lines.py (the LINES text) with no mutant naming their test as killer.
Reads the two files by text; does not import the builder's helpers. Run in the worktree root."""
import re, ast
lines_src = open("tests/test_q8b_batch8_lines.py", encoding="utf-8").read()
ids = re.findall(r"^(tests/[\w./]+\.py::[^\s|]+) \| control \|", lines_src, re.M)
mut = open("tests/q8b_mutants.py", encoding="utf-8").read()
# own reading: every mutant( ... ) call; the killer is the last quoted-string pair before the closing; collect all test names after a test file arg
killers = set(re.findall(r"test_[a-z0-9_]+", mut))
rows = []
for i in ids:
    name = i.split("::")[1].split("[")[0]
    rows.append((i, name in killers))
print("controls", len(ids), "distinct ids", len(set(ids)))
print("named anywhere in q8b_mutants.py:", sum(r[1] for r in rows), "not named:", sum(not r[1] for r in rows))
for i, ok in rows:
    if not ok: print("UNPLANTED", i)
