# Real-run v6 patch chain: Linux evidence summary (CORE cloud session, 2026-11-13)

Repo under test: public demo repo, main 61ded9e, made-up data. Patches: (1) real-run-fixes-v6-after-sonar-p3-final.patch (9fc11e9a), (2) desk-address-required-v6.patch (66679357), applied in that order; core-touches-3.patch (c61791a6) alone. Python 3.12.3, one venv, serial runs, `unshare -n` with loopback up (no network). Only product tests were run: no ruff, mypy, bandit, gitleaks or hygiene scans.

All numbers are RUNNER OUTPUT (evidence runners record, they do not judge). I did not re-run them; I only read them. I wrote no fix and changed no code.

## What failed or is uncertain (first)
1. 9 mutants survived in runner B2's run (R20, K6, K10, C9, N20, P2, P4, P10, and see table). None was investigated; nothing was fixed (LEAD order).
2. R20 survived here but the demo's first-pass evidence says it was KILLED. Cause unknown.
3. P2, P4, P10 survive singly; the demo evidence has no results for muts2.json, so there is no first pass to compare with. Their two combined mutants P2b and P4b were killed.
4. K6 and K10: the demo says only the pair together is killed. The pair was NOT run, so that claim is not re-verified.
5. My brief put TMPDIR inside the tree: it caused 2 failures in runner A run 1 and runner C. Runs marked "TMPDIR outside" are clean.
6. Not run: ruff/mypy/bandit/gitleaks/hygiene; the K6+K10 pair; mutants outside the JSON files; Windows; Playwright tests (166) and gitleaks tests (28) skip because the tools are missing.
7. Runner B2: its first baseline script was not fully stopped and ran in parallel with the second for a while; one first-baseline SK line shows rc=1 (54 s), unexplained (probably shared TMPDIR). The final baseline (rc=0, 73 passed) and all mutant runs ran alone.

## Test runs
| run | tree / head | passed | failed | skipped | wall | hang | note |
|---|---|---|---|---|---|---|---|
| A run 1 (TMPDIR inside tree, my brief) | 61ded9e + 2 patches | 3779 | 2 | 198 | 1303 s | no | the 2 failures are folder-caused (see A3) |
| A run 2 (TMPDIR outside tree) | 61ded9e + 2 patches | 3781 | 0 | 198 | 1293 s | no | clean number |
| A rerun of the 2 failing files (TMPDIR outside) | 61ded9e + 2 patches | 3 | 0 | 0 | 2 s | no | |
| A attempt 1 of run 1 / of run 2 | | n/a | n/a | n/a | 238 s / n/a | SIGTERM exit 143 / container restart | do not count |
| A3 full suite, clean unpatched main (TMPDIR inside tree) | 61ded9e | 3405 | 2 | 198 | 1165 s | no | the same 2 tests fail: cause is the folder, not the patches |
| C full suite, core-touches-3 alone (TMPDIR inside tree), 5 file groups | 61ded9e + c61791a6 | 3417 | 2 | 198 | about 1212 s | no | same 2 tests; rerun with TMPDIR outside: 3 passed |
| B patched, 12 touched test files | 61ded9e + 2 patches | 1263 | 0 | 1 | see B/RESULTS.md | no | |

The 2 folder-caused tests: tests/test_demo_folder_guard.py::test_a_missing_demo_folder_skips_when_allowed_and_stops_the_run_in_ci and tests/test_no_placeholders.py::test_no_placeholder_text_ships.
Passed difference 3781 vs 3405 = 376: the patches add tests (not counted per file by me). The 198 skips are the same in all runs: Playwright missing 166, gitleaks missing 28, 4 others.

## Fails-before (new or changed test functions against unpatched main)
Full per-function table: B/per-test.txt. Four variants: patched, before (strict unpatched source), precheck (the demo's own set-up, labelled extra), oldconftest.
- Strict "before": test_real_run_v6 and test_start_prompt_hardening do not collect, and test_take_script_refusals, test_path_confinement, test_real_check_dry error at setup. These count as failing for a MISSING MODULE reason (the patch's new scripts), not behaviour.
- "precheck" variant, per file: clock_steps 2 failed; core_key_readers 7 failed, 5 passed; desk_address_required 13 failed, 3 passed; ledger_amounts 2 failed; live_claude 3 failed; path_confinement 1 failed; real_check_dry 5 failed; real_run_v6 70 failed, 4 passed; start_prompt_hardening 52 failed; take_script_refusals 69 failed.
- 45 new or changed test functions PASS on old code (B/passes-on-old.txt): fails-before = NO for those. Named pins: the two 1512-key-file equality tests (expected, equality with the old rule).
- core-touches-3 alone (C): 7 failed, 5 passed on unpatched main; fails-before NO for the two "identical to the old rule on 1512 key files" tests (hubspot, smtp), YES for live-equal, and YES for the three "reason text" cases.
- Doc difference: src-v6/README.md says desk-address 12 failed / 4 passed; the demo's own evidence file and my run say 13 / 3.

## Mutation sets (runner B2, driver mut_portable.py copy `runmut.py`, tree-M, -x, one at a time, 240 s limit, no crash or timeout)
Killing test files were chosen by the runner from the headers of the demo evidence file; the JSON files hold no killing test per mutant. Baselines on unmutated tree-M all passed.
| set | killed | survived | not planted |
|---|---|---|---|
| M (M1-M23) | 23 | 0 | 0 |
| R (R1-R20) | 19 | 1 (R20) | 0 |
| S (S1-S12) | 12 | 0 | 0 |
| K (K1-K15) | 13 | 2 (K6, K10) | 0 |
| C (C1-C9) | 8 | 1 (C9) | 0 |
| N (N1-N20) | 19 | 1 (N20) | 0 |
| P (P1-P10, muts2.json) | 7 | 3 (P2, P4, P10) | 0 |
| P2b, P4b (combined) | 2 | 0 | 0 |
M12 of muts1.json is NOT PLANTED (its old text no longer matches the merged code); muts-sp.json's adapted M12 was planted and killed.

## Interim vs final survivors (each named, with the test file that should have killed it)
| id | interim (my 10:44Z block, raw counts) | final (B2 report) | demo first pass | test file chosen to kill it | note |
|---|---|---|---|---|---|
| C9 | survived (CN set) | SURVIVED | survivor, "equivalent" | test_real_run_v6.py + test_core_key_readers.py | demo says equivalent: not judged by me |
| N20 | survived (CN set) | SURVIVED in this test selection | survivor | same two files | demo says killed by R2 in the other file; in B2's run R2 was KILLED, so that claim holds |
| K6 | survived | SURVIVED | survivor | test_take_script_refusals.py -k "scan or keep or sample" | demo says only the pair K6+K10 is killed; pair NOT run |
| K10 | survived | SURVIVED | survivor | same | same |
| R20 "config unreadable old" | not yet in the interim count | SURVIVED (143 passed in 128.84 s) | KILLED | test_take_script_refusals.py | DIFFERS from demo evidence; cause not investigated (would need the R20 text in scripts/run_real_check.py) |
| P2 hubspot absent falls back to the vendor | P survivors 3 | SURVIVED (16 passed) | no first pass | test_desk_address_required.py | killed only together with the check it guards (P2b) |
| P4 live absent falls back to the provider | | SURVIVED (16 passed) | no first pass | same | killed only in P4b |
| P10 hubspot required check disabled, exit 0 path | | SURVIVED (16 passed) | no first pass | same | |
| M2 "wrong reason suspected" | flagged | KILLED, real first failure is an AssertionError in test_a_failing_console_probe_is_not_a_terminal | killed | test_start_prompt_hardening.py | the flag came from the word "error" in log text (runner regex), a false flag |
| S2, N12, N14 | | KILLED now | survivors in the first pass | | consistent with tests added after the first pass (demo notes) |

Interim count differences: the 10:44Z block showed CN 2 survived, M 1 "wrong-reason suspected", P 3 survived, K 1 survived (K was still running). Final: C9 + N20, M 0 survived, P2 + P4 + P10, K6 + K10, plus R20.

## Files
A/ (RESULTS.md, raw/ logs incl. unpatched-main full run), B/ (RESULTS.md, per-test.txt, passes-on-old.txt, raw/), B2/ (RESULTS.md, res-*.tsv, res-combo.txt, muts-*.json, raw/), C/ (RESULTS.md, raw/). No xml, no secrets (cpush.sh gitleaks gate).
