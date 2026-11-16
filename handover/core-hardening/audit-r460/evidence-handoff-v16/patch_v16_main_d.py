import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "CORE-PR-HANDOFF-v16.md"
s = p.read_text(encoding="utf-8")
L = s.split("\n")
def idx(prefix):
    h = [i for i, l in enumerate(L) if l.startswith(prefix)]
    if len(h) != 1: print("LINE MISMATCH", prefix[:50], len(h)); sys.exit(1)
    return h[0]
def sub(i, old, new, n=1):
    c = L[i].count(old)
    if c != n: print(f"MISMATCH {c}!={n}: {old[:70]!r}"); sys.exit(1)
    L[i] = L[i].replace(old, new)
i = idx("Every file named in this section exists")
a = L[i].index("**New in v15 (folder `evidence-handoff-v15/`):**"); b = L[i].index("**Carried from v14 and NOT re-run")
seg = L[i][a:b]
seg = seg.replace("**New in v15 (folder `evidence-handoff-v15/`):**", "**Carried from v15, NOT re-run in v16 (folder `evidence-handoff-v15/`; this is v15's run with v15's file names; v16's run is in the paragraph above):**")
for x, y in (("pg_v16.py", "pg_v15.py"), ("pg_run_v16.sh", "pg_run_v15.sh"), ("raw-pg-v16-run1.txt", "raw-pg-v15-run1.txt"), ("raw-pg-v16-run2.txt", "raw-pg-v15-run2.txt"), ("raw-pg-version-v16.txt", "raw-pg-version-v15.txt"), ("174 of 174", "93 of 93"), ("evidence-handoff-v16/", "evidence-handoff-v15/")):
    seg = seg.replace(x, y)
L[i] = L[i][:a] + seg + L[i][b:]
sub(i, "`gate4.sh` (**never run**: syntax-checked with `bash -n`, `raw-gate4-syntax.txt`, and compared with `ci.yml` by `check_gate4_vs_ci.py`, `raw-gate4-vs-ci.txt`;", "`gate4.sh` (**ran once in v16 as `gate4_v16.sh` on the unchanged tree, see 7.2 E0-S1-1**; v14 syntax-checked it with `bash -n`, `raw-gate4-syntax.txt`, and compared it with `ci.yml` by `check_gate4_vs_ci.py`, `raw-gate4-vs-ci.txt`;")
j = idx("**Not checked (nothing here is")
sub(j, "**`gate4.sh` has never run** (syntax-checked and compared with `ci.yml` only).", "**`gate4.sh` ran once in v16 on the unchanged tree: four steps `rc=0`, `pytest` `rc=1` (2 failed, 9364 passed; L20); it has not run on a changed tree.**")
sub(j, "**What was run in v15 is only: the Postgres program of 8, the independent citation checker, the planned-name listing and the banned-string count; the import-graph, cycle, snippet and fence programs of v14 were not re-run.** **No unit test, `ruff`, `bandit` or CodeQL was run;", "**What was run in v16 is only: the Postgres program of 8 (twice), the baseline gate script on the unchanged tree and the banned-string count; the citation, planned-name, import-graph, cycle, snippet and fence programs were not re-run (8).** **No unit test, `ruff`, `bandit` or CodeQL was run on a changed tree (none exists);")
p.write_text("\n".join(L), encoding="utf-8"); print("part D ok")
