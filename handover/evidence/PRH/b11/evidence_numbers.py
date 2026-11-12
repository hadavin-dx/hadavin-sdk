"""EVIDENCE for PR H batch 11: writes `numbers.txt`, every figure SECURITY.md and CHANGELOG.md may quote for the redaction work, computed
from the raw files in this folder (clean-corpus-*.txt, cells-*.jsonl, fuzz-b7-*.txt, spaced-*.txt). The docs test
`tests/test_prh_b9_docs.py::test_b11_every_figure_in_security_is_in_the_numbers_file` compares each figure of the SECURITY.md paragraph
against this file. Usage: python evidence_numbers.py (any folder)"""

import json, re
from pathlib import Path

here = Path(__file__).resolve().parent
out = []


def put(key, val):
    out.append(f"{key}={val}")


def pct(a, b):
    return f"{100 * a / b:.2f}"


for tree in ("head", "old", "main", "ea6"):
    f = here / f"clean-corpus-{tree}.txt"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"(\w) .*?: texts=(\d+) withheld_or_error=(\d+)", line)
            if m:
                put(
                    f"clean-{m.group(1)}-{tree}",
                    f"{int(m.group(3))} ({pct(int(m.group(3)), int(m.group(2)))} percent) of {int(m.group(2)):,}",
                )
for tree in ("head", "old", "main", "ea6"):
    f = here / f"cells-{tree}.jsonl"
    if f.exists():
        rows = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()]
        put(
            f"hostile-{tree}",
            f"texts {len(rows):,} readable {sum(r['readable'] for r in rows):,} withheld {sum(r['withheld'] for r in rows):,} errors {sum(1 for r in rows if r['err'])}",
        )
for tree in ("head", "old", "main"):
    f = here / f"fuzz-b7-{tree}.txt"
    if f.exists():
        put(f"fuzz-b7-{tree}", f.read_text(encoding="utf-8").strip().splitlines()[-1])
for name in ("spaced-repo-head", "spaced-stdlib-head"):
    f = here / f"{name}.txt"
    if f.exists():
        m = re.search(
            r"files=(\d+) lines=(\d+) lines_with_a_spaced_run_at_all=(\d+) lines_changed=(\d+)",
            f.read_text(encoding="utf-8"),
        )
        put(
            name,
            f"files {int(m.group(1)):,} lines {int(m.group(2)):,} runs {m.group(3)} changed {m.group(4)}",
        )
(here / "numbers.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
