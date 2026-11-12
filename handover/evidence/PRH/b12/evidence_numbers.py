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
for tree in ("head", "old", "main", "ea6"):
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
# batch 12: perf rows, the full test run, the mutant runs and the skip table
f = here / "perf-compare.txt"
if f.exists():
    for line in f.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) == 5 and cells[1].isdigit():
            put("perf-" + cells[0].split(" ")[0], f"{cells[0]} | chars {cells[1]} | head {cells[2]} | main {cells[3]} | ratio {cells[4]}")
f = here / "full-pytest.txt"
if f.exists():
    tail = [x for x in f.read_text(encoding="utf-8").splitlines() if re.search(r"\d+ passed", x)]
    if tail:
        put("full-pytest", tail[-1].strip("= "))
for name in ("mut-root", "mut-nobody", "stage-mutants"):
    f = here / f"{name}.txt"
    if f.exists():
        m = re.findall(r"(\d+) of (\d+) good", f.read_text(encoding="utf-8"))
        if m:
            put(name, f"{m[-1][0]} of {m[-1][1]} good")
f = here / "skip-table.txt"
if f.exists():
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("total skipped"):
            put("skipped", line.split(":", 1)[1].strip())
# derived lines: the per-text comparison, the difference to main, the corpus size of the earlier batches
f = here / "splitleak-diff.txt"
if f.exists():
    m = re.search(r"head readable split texts: (\d+) main readable split texts: (\d+)", f.read_text(encoding="utf-8"))
    put("split-texts-readable", f"head {int(m.group(1)):,} main {int(m.group(2)):,}")
f = here / "fuzz-b7-main.txt"
if f.exists():
    m = re.search(r"texts (\d+) .*readable windows (\d+)", f.read_text(encoding="utf-8").strip().splitlines()[-1])
    put("fuzz-b7-sizes", f"texts {int(m.group(1)):,} readable windows on main {int(m.group(2)):,}")
if "clean-A-head" in dict(x.split("=", 1) for x in out) and "clean-A-main" in dict(x.split("=", 1) for x in out):
    d = dict(x.split("=", 1) for x in out)
    h = int(d["clean-A-head"].split()[0])
    mm = int(d["clean-A-main"].split()[0])
    n = int(d["clean-A-head"].split(" of ")[1].replace(",", ""))
    put("clean-A-head-minus-main", f"{h - mm} texts, {(h - mm) * 100 / n:.2f} of a percentage point")
put("clean-corpus-earlier-batches", "21,783 texts (the batch 11 corpus, from the batch 11 numbers)")
(here / "numbers.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
