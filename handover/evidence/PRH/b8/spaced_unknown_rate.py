"""PR H batch 8, Issue 1(b): how many ordinary texts does the check-only reading of an UNKNOWN spaced-out secret change?

Corpus (made-up or repository text only, no client data): every line of the repository's prose and source (README, CHANGELOG, SECURITY,
docs, src, tests, tools, demos), plus the 15 texts of the clean corpus (`handover/evidence/PRH/b7/clean_corpus.py`). A text
is CHANGED when `hadavin_sdk.guard.redact.spaced_unknown` finds a run in it. Run from the repository root:
    PYTHONPATH=src python handover/evidence/PRH/b8/spaced_unknown_rate.py
"""

import sys
from pathlib import Path

import hadavin_sdk.guard  # noqa: F401  (the package re-exports `redact` as a function; the module is read from sys.modules)

R = sys.modules["hadavin_sdk.guard.redact"]
ROOT = Path(__file__).resolve().parents[4]
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
SUFFIXES = {".md", ".py", ".txt", ".json", ".toml", ".yml", ".yaml"}


def lines():
    for top in ("README.md", "CHANGELOG.md", "SECURITY.md", "docs", "src", "tests", "tools", "demos", "handover"):
        p = ROOT / top
        files = [p] if p.is_file() else sorted(p.rglob("*")) if p.exists() else []
        for f in files:
            if f.is_file() and f.suffix in SUFFIXES and ".venv" not in f.parts and "__pycache__" not in f.parts:
                try:
                    for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                        yield f"{f.relative_to(ROOT)}:{n}", line
                except (UnicodeDecodeError, OSError):
                    continue


def main() -> None:
    total = changed = runs = 0
    hits = []
    for where, line in lines():
        total += 1
        if R._SPACED_RUN.search(line):
            runs += 1
        if R.spaced_unknown(line):
            changed += 1
            hits.append(where)
    positive = len(R.spaced_unknown("log: " + " ".join(KEY) + " end"))
    ordinary = [
        "a b c d e f g h i j k l m n o p q r s t u v w x y z",
        "1 2 3 4 5 6 7 8 9 0 1 2 3",
        "H E L L O W O R L D 2 0 2 6",
        "S P E L L I N G B E E 4 2 1 7",
        "x = 1 2 3 4 5 6 7 8 9 10 11",
        "T o d a y w e s h i p r e l e a s e 4",
        "c a t d o g b i r d f i s h 1 2 3",
    ]
    ordinary_changed = sum(1 for t in ordinary if R.spaced_unknown(t))
    print(f"lines that hold a spaced-out run of {R.defaults.SPACED_RUN_MIN_TOKENS}+ single-character tokens at all: {runs}; hand-written ordinary spaced runs read as a secret: {ordinary_changed} of {len(ordinary)}")
    print(f"ordinary lines read: {total}; lines with a spaced-out run read as a secret: {changed}; positive control (the example key spaced out): {positive}")
    for h in hits[:20]:
        print("  changed:", h)


main()
