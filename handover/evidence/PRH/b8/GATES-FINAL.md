Final-head gates (head ea6dbdaf), 2026-11-12 08:08 to 08:18 UTC.
full pytest (not live, not perf): 13106 passed, 1 skipped, rc=0 (gate-final-full.txt). Run 1 on 0a789d89 had 3 failures, fixed in ea6dbdaf (gate-run1-full.txt).
stage_mutants: 37 of 37 good, rc=0.
prh_mutants as user nobody: 109 of 114 good, rc=1. SURVIVED: 54, 59 (wrong reason), 84, 93 (b7 mutants made redundant by b8) and 111 (killed in run 1, survived here: not explained).
prh_mutants as root on ea6dbdaf: NOT finished (run 1 on 0a789d89 is in gate-run1-mut-root.txt: 108 of 113, rc=1).
perf (pytest -m perf) on 0a789d89: 62 passed, rc=0 (gate-run1-perfpt.txt); not re-run on ea6dbdaf.
