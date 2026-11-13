# B2 results (mutation sets on tree-M, main 61ded9e + patch1 + patch2). Raw: res-*.tsv (tab: name, verdict, first FAILED id, last pytest line, seconds), raw-res-<set>-<id>.log, log-*.txt, baseline-*.log
Run: 2026-11-13 10:15Z-11:25Z. Per mutant: `unshare -n` + lo_up.py, TMPDIR=/home/user/build/rr6/tmp-B2 (outside every tree), PYTHONPATH=tree-M/src, `pytest -q -x -p no:cacheprovider -rf <killing tests>`, 240 s limit, file restored after each mutant (verified: tree-M git diff and status equal tree-M-start.diff / -status at the end).
Killing tests (the JSON holds no test per mutant; chosen from evidence-q4h-mutants.txt headers): M: tests/test_start_prompt_hardening.py; R: tests/test_take_script_refusals.py; S, K: same file with -k "scan or keep or sample"; C, N: tests/test_real_run_v6.py + tests/test_core_key_readers.py; P: tests/test_desk_address_required.py.
Baselines (unmutated tree-M, same wrapper): M 129 passed; C+N 86 passed; P 16 passed; S/K selection 73 passed 70 deselected; R full file 143 passed.
Adapted: paths only (tree, venv312, lo_up copy, TMPDIR), `unshare -n` instead of `unshare -rn` (brief), no connect-blocker sitecustomize, runner = own copy runmut.py of mut_portable.py (+ first FAILED id, timeout, resume). Combo mutants P2b/P4b via runcombo.py (paths adapted from mut2b-b12.py).
Interruption: container restart ~10:22Z killed the chain during M23; M1-M22 kept, M23 re-run. Everything else ran once.

| set | mutants | KILLED | SURVIVED | NOT PLANTED | CRASHED |
|---|---|---|---|---|---|
| M (muts-sp.json) | 23 | 23 (M2 flagged by my regex, see below, real assertion failure) | 0 | 0 | 0 |
| R | 20 | 19 | 1 (R20) | 0 | 0 |
| S | 12 | 12 | 0 | 0 | 0 |
| K | 15 | 13 | 2 (K6, K10) | 0 | 0 |
| C | 9 | 8 | 1 (C9) | 0 | 0 |
| N | 20 | 19 | 1 (N20) | 0 | 0 |
| P (muts2.json, P1-P10) | 10 | 7 | 3 (P2, P4, P10) | 0 | 0 |
| P2b, P4b (combined) | 2 | 2 | 0 | 0 | 0 |
| muts1.json M12 (v. muts-sp M12) | 1 | - | - | 1 | 0 |
