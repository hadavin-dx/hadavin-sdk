"""Regenerate tools/out from handover/demo. Run from the repo root:
  python3 handover/flows-audit/tools/make_out.py
Names: path relative to handover/demo, '/' -> '__', '.json' stripped. Diff: diff__<a>__TO__<b>.txt.
Writes ONLY under handover/flows-audit/tools/out."""

import contextlib
import io
import os

import dump_nodes

HERE = os.path.dirname(os.path.abspath(__file__))
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


class Result:
    def __init__(self, returncode, stdout):
        self.returncode = returncode
        self.stdout = stdout


def run(*a):
    """Run dump_nodes.py in this process (same code, same output) from the demo folder."""
    buf = io.StringIO()
    with contextlib.chdir(DEMO), contextlib.redirect_stdout(buf):
        rc = dump_nodes.main(list(a))
    return Result(rc, buf.getvalue())


def nm(p):
    return p.replace("/", "__")[:-5]


os.makedirs(OUT, exist_ok=True)
c = run("counts", ".")
with open(os.path.join(OUT, "counts.txt"), "w") as fh:
    fh.write(c.stdout)
files = [l.split(" ", 1)[1] for l in c.stdout.splitlines() if l[:1].isdigit()]
for f in files:
    r = run("table", f)
    if r.returncode != 0:
        raise RuntimeError(f"dump_nodes table {f} failed with exit code {r.returncode}")
    with open(os.path.join(OUT, nm(f) + ".md"), "w") as fh:
        fh.write(r.stdout)
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
        with open(os.path.join(OUT, f"diff__{nm(f)}__TO__{nm(g)}.txt"), "w") as fh:
            fh.write(run("diff", f, g).stdout)
        n += 1
print(len(files), "tables;", n, "diffs")
