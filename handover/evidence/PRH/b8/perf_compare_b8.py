"""PR H batch 8: the perf compare the runner could not read: ALL shapes (S, H and W) at 65,536 characters, and at 262,144.
Each cell is the median CPU seconds of 3 runs in a child process of one tree. Usage (repository root, one run alone):
    python handover/evidence/PRH/b8/perf_compare_b8.py HEAD_SRC MAIN_SRC [OLD_SRC]
Prints: shape | chars | head | main | head/main | (old). `cap` = defaults.MAX_REDACT_PASSES stays 24. A cell that does not finish in
150 s prints TIMEOUT."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CODE = (
    "import json,sys;sys.path.insert(0,%r);from tests import test_prh_perf as P;"
    "print(json.dumps({k: [P.median_cpu(P.fill(v, n), 3) for n in (65536, 262144)] for k, v in P.SHAPES.items()}))" % str(ROOT)
)
def run(src):
    env = {**os.environ, "PYTHONPATH": src}
    out = {}
    for shape in json.loads(subprocess.run([sys.executable, "-c", "import sys;sys.path.insert(0,%r);from tests import test_prh_perf as P;import json;print(json.dumps(list(P.SHAPES)))" % str(ROOT)], env=env, capture_output=True, text=True).stdout.strip().splitlines()[-1]):
        code = (
            "import json,sys;sys.path.insert(0,%r);from tests import test_prh_perf as P;"
            "print(json.dumps([P.median_cpu(P.fill(P.SHAPES[%r], n), 3) for n in (65536, 262144)]))" % (str(ROOT), shape)
        )
        try:
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=150)
            out[shape] = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else ["ERR", "ERR"]
        except subprocess.TimeoutExpired:
            out[shape] = ["TIMEOUT", "TIMEOUT"]
    return out
trees = [run(p) for p in sys.argv[1:]]
print("shape | chars | head | main | head/main" + (" | old" if len(trees) > 2 else ""))
for shape in trees[0]:
    for i, n in enumerate((65536, 262144)):
        h, m = trees[0][shape][i], trees[1][shape][i]
        ratio = f"{h / m:.2f}" if isinstance(h, float) and isinstance(m, float) else "n/a"
        cell = lambda v: f"{v:.3f}" if isinstance(v, float) else str(v)
        extra = f" | {cell(trees[2][shape][i])}" if len(trees) > 2 else ""
        print(f"{shape} | {n} | {cell(h)} | {cell(m)} | {ratio}{extra}")
