"""EVIDENCE (batch 11 copy; adds changed_outside_handover): how many ordinary lines does the spaced-out-secret rule (`redact.spaced_unknown`, after the 6-distinct-character
rule) change? Usage: python spaced_rate.py <tree-root> <corpus-root> [more corpus roots]. A line is CHANGED when spaced_unknown finds a run.
Corpus roots are read recursively (.md .py .txt .rst .json .toml .yml .yaml). Also prints a positive control and ordinary spaced-out text."""

import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1] + "/src")
import hadavin_sdk.guard  # noqa

R = sys.modules["hadavin_sdk.guard.redact"]
SUF = {".md", ".py", ".txt", ".rst", ".json", ".toml", ".yml", ".yaml"}
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
tot = chg = runs = files = outside = 0
hits = []
for root in sys.argv[2:]:
    for f in sorted(Path(root).rglob("*")):
        if (
            f.is_file()
            and f.suffix in SUF
            and ".git" not in f.parts
            and "__pycache__" not in f.parts
            and ".venv" not in f.parts
            and "venv" not in f.parts
        ):
            try:
                lines = f.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            files += 1
            for n, line in enumerate(lines, 1):
                tot += 1
                if R._SPACED_RUN.search(line):
                    runs += 1
                if R.spaced_unknown(line):
                    chg += 1
                    outside += "handover" not in f.parts
                    if len(hits) < 15:
                        hits.append(f"{f}:{n}: {line[:100]!r}")
print("tree", R.__file__)
print(
    f"files={files} lines={tot} lines_with_a_spaced_run_at_all={runs} lines_changed={chg} changed_outside_handover={outside}"
)
print(
    "positive control (example key spaced out) runs found:",
    len(R.spaced_unknown("log: " + " ".join(KEY) + " end")),
)
ord_ = [
    "a b c d e f g h i j k l m n o p q r s t u v w x y z",
    "1 2 3 4 5 6 7 8 9 0 1 2 3",
    "H E L L O W O R L D 2 0 2 6",
    "x = 1 2 3 4 5 6 7 8 9 10 11",
    "a a a a a a a a a a a a",
    "t h i s i s a t e s t o f s p a c i n g",
    "A B C D E F G H I J K L M N O",
]
print("ordinary spaced texts changed:", [bool(R.spaced_unknown(t)) for t in ord_])
for h in hits:
    print("  changed:", h)
