# EV7R evidence (evidence runner; I ran commands and saved raw output; I do not judge or fix)
Raw files: /home/user/build/rr6/out/EV7R/ (pytest-full.log, wrapper.log, start.txt, diff-a.txt, ruff-check.txt, ruff-format.txt, suppressions.txt, supp-tree-R7Q.txt, supp-tree-R7R.txt, strcmp.py, hostile-*.txt, run-full.sh, checkpoint.md). Times UTC (IST = +5:30). Start about 12:00, end 12:37 (about 37 of 60 min). Rules used: R-verify-tests-and-evals (gate on pytest exit code), reviewer-independence (EVIDENCE RUNNER never judges), keep-tool-output-small, agent supervision rule, long-jobs-run-detached, class-level-fixes (hostile re-run).

## What failed / not checked (first)
- Failed: nothing in the full run (0 failed). Not a failure but different from EV7P: my first QuietServer run under plain `unshare -n` had the loopback interface down ("Network is unreachable"); I re-ran under the `lo_up-q4g.py` wrapper (first attempt kept out of the result). My own `trace_lines` counter in the QuietServer table (counts lines starting `Traceback`) differs from EV7P's unknown counter in 3 rows (bug_with_pipe_context 6 vs 3, group 0 vs 3, keyboard 3 vs 0); the stderr byte counts are identical to EV7P in all 22 rows. I did not reconstruct EV7P's counter.
- Not checked: Windows/PowerShell, real IPv6, mutation runs (mutants A, B: not asked, not run by me; builder claim only), bandit, mypy, gitleaks standalone (it ran inside the tests), Python versions other than 3.12, a quiet machine (see load).
- No permission refusal happened (staged git copy was allowed). No prompt answered. No spend, no network (`unshare -n`, loopback only).

## Step 1: patches and tree
- `sha256sum -c sha256-r7r.txt`: all 3 patches OK.
- Tree: `git archive HEAD` of demo-frozen/repo2 (HEAD tree 49d3c85938fe5323a3378a49195d3b8da434b3ca) into my own dir, `git apply --binary` the CRLF patch: no error. `diff -rq` vs /home/user/build/rr6/tree-R7R (diff-a.txt): only 3 `__pycache__` folders that exist only in tree-R7R. Source identical. repo2 not edited.
- Staged git copy: `git init` + `git add -A` inside my own scratch tree (`out/EV7R/tree-a`): 318 files staged, no commit; `git status` shows only `A` entries.

## Step 2: ONE full pytest in the staged git copy
Command (run-full.sh): `env -i HOME/TMPDIR=out/EV7R/tmp-full PYTHONPATH=<tree>/src PYTHONDONTWRITEBYTECODE=1 PLAYWRIGHT_BROWSERS_PATH=rr6/pw-browsers GITLEAKS_BIN=rr6/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 timeout 3000 unshare -n python3 lo_up-q4g.py venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs tests` (default collection order puts test_load_tools before test_r7k_findings).
- Result: **6021 passed, 7 skipped, 0 failed, 60 warnings in 2050.21s (0:34:10)**, rc=0 (wrapper.log). EV7P on r7q: 2 failing tests (guard allow-list; hygiene).
- Skips (7): test_book_folder_refusals.py:237 root can read any file; test_n8n_api_url.py:524 root can read a no-permission file; test_path_confinement.py:285 needs Python 3.13; test_r7b_fake_deep_and_head.py:58 x2 only the model fake has /v1/messages; test_server_hardening.py:224 measurement run, set LEAD_DESK_LOAD_N; test_stall_eviction.py:526 Windows only. **No gitleaks skips** (gitleaks 0 skipped; DPLD_REQUIRE_SCAN=1 would have failed them).
- Load: start 0.18 0.41 0.46; end 0.67 0.44 0.59 (4 cores). Builder pytest (pid 14679, plain-copy after-grep2) was running at my start (counted in my load notes) and finished during my run; I did not touch it. Its final tail, raw: `after-grep2.log`: "SKIPPED [2] tests/test_gitleaks_semgrep_lock.py:38: no gitleaks program on PATH ...", "SKIPPED [24] tests/test_gitleaks_exceptions.py:140: no gitleaks program ...", "4610 passed, 35 skipped, 51 warnings in 1546.57s (0:25:46)", "rc=0". (104-file set, no load_tools, so not comparable to my count.)
- My tree after the run: `git status` shows no change besides staged adds; no `__pycache__` in tests.

## Step 3: ruff 0.17.1 on a copy of tree-R7R (no pycache)
- `ruff check`: "All checks passed!" rc=0. `ruff format --check`: "229 files already formatted" rc=0.

## Step 4: suppression counts (tree-R7Q vs tree-R7R, whole tree, lines)
noqa 192 / 192; `type: ignore` 126 / 126; nosemgrep 32 / 32; nosec 8 / 8; in src/: 32/32, 18/18, 0/0, 6/6. `diff` of the full line lists (with file, line number and text): empty. Unchanged (grep counts are coarser than EV7P's earlier 188->193 count, which used a different pattern; I did not reconcile the two).

## Step 5: hostile drivers (EV7P's three, on a plain copy `htree` of tree-R7R)
- String identity: `strcmp.py` parses test_r7q_findings.py of r7q and r7r, folds the new module constants (COLON_NL, TYPED_ADDRESS), `"a" + "b"` joins and f-string joins into constants, then compares: normalised AST identical = True; 242 string constants each, same multiset = True. Only the file diff is how strings are built (6 hunks). Also files differing r7q vs r7r: only tests/test_file_call_guard.py and tests/test_r7q_findings.py.
- Banner bytes: 429 lines, ends "E2E cases=6 mismatches=0"; output byte-identical to EV7P's hostile-banner.txt.
- MemoryError via secret_boundary: "CASES=24 cases_with_leak_other_than_own_args=0"; byte-identical to EV7P's hostile-mem.txt.
- QuietServer: 22 rows (11 modes x QuietServer/plain control), all rc=0; with QuietServer stderr bytes 0 for ok, write_to_gone, timeout, epipe_oserror, reset_oserror; non-zero for bug_value 2853, bug_with_pipe_context 3810, refused 2832, ssl_eof 2757, group 3498, keyboard 3066 (control: also write_to_gone 3129, epipe 2922, reset 2979). Byte counts identical to EV7P's file.

## Builder claim vs measured
| Builder claim | Measured |
|---|---|
| guard test 11 passed | Not run alone; inside the full run test_file_call_guard.py had no failure (0 failed overall) |
| hygiene sweep 193 passed 4 skipped in a git copy (gitleaks skips) | Not run alone; full staged run 6021 passed 7 skipped 0 failed; no gitleaks skips here |
| ruff clean | confirmed (check and format) |
| suppressions unchanged | confirmed (identical line lists) |
| mutants A, B kill the guard test | NOT checked (not asked) |

## Housekeeping
Started by me: run-full.sh wrapper (pid 20079, ended), foreground hostile drivers (ended), an until-loop monitor and a fallback timer (ended). `ps` at the end: no pytest process left; nothing of mine alive. Nothing committed; repo2, tree-R7B..R7R, EV7P, REV*, M8-M12* not edited.
