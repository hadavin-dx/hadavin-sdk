"""Regenerate tools/out from handover/demo. Run from the repo root:
  python3 handover/flows-audit/tools/make_out.py
Names: path relative to handover/demo, '/' -> '__', '.json' stripped. Diff: diff__<a>__TO__<b>.txt.
Writes ONLY under handover/flows-audit/tools/out."""

import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(HERE, "dump_nodes.py")
DEMO = os.path.join(HERE, "..", "..", "demo")
OUT = os.path.join(HERE, "out")
SUCC = {
    "n8n-flows": "n8n-flows-v3",
    "n8n-flows/v1-superseded": "n8n-flows",
    "n8n-flows-v3": "n8n-flows-v4",
    "n8n-flows-v4": "n8n-flows-real-v5",
    "n8n-flows-real": "n8n-flows-real-v3",
    "n8n-flows-real-v3": "n8n-flows-real-v4",
    "n8n-flows-real-v4": "n8n-flows-real-v5",
    "n8n-flows-film": "n8n-flows-film-v3",
    "n8n-flows-film-v3": "n8n-flows-film-v4",
    "n8n-flows-film-v4": "n8n-flows-film-v5",
    "n8n-flows-real-v5": "n8n-flows-film-v5",
}


def run(*a):
    return subprocess.run([sys.executable, T, *a], capture_output=True, text=True, cwd=DEMO)


def nm(p):
    return p.replace("/", "__")[:-5]


os.makedirs(OUT, exist_ok=True)
c = run("counts", ".")
open(os.path.join(OUT, "counts.txt"), "w").write(c.stdout)
files = [l.split(" ", 1)[1] for l in c.stdout.splitlines() if l[:1].isdigit()]
for f in files:
    r = run("table", f)
    assert r.returncode == 0, f
    open(os.path.join(OUT, nm(f) + ".md"), "w").write(r.stdout)
n = 0
for f in files:
    d, b = os.path.split(f)
    pairs = []
    if (
        d in SUCC
        and b.startswith("mf-")
        and "mf-table" not in b
        and os.path.exists(os.path.join(DEMO, SUCC[d], b))
    ):
        pairs.append(os.path.join(SUCC[d], b))
    if f == "n8n-table-screen/mf-table-screen.json":
        pairs.append("n8n-table-screen-v2/mf-table-screen-v2.json")
    for g in pairs:
        open(os.path.join(OUT, f"diff__{nm(f)}__TO__{nm(g)}.txt"), "w").write(
            run("diff", f, g).stdout
        )
        n += 1
print(len(files), "tables;", n, "diffs")
