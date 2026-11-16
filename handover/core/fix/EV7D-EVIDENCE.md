# EV7D evidence (evidence runner, round r7d, ORDER 268 money/mail path)

I ran and recorded; I did not judge. Raw files: /home/user/build/rr6/out/EV7D/ (logs/grp.0N.log, logs/rerun-*.log, logs/fb-*.log, logs/bounded.log, logs/mut7d.out, hd/, bc/, apply_matrix.txt, bandit-*.txt, ruff-*.txt, progress.txt). Tree: /home/user/build/rr6/tree-EV7D (frozen 49d3c859 + CRLF patch, staged, no commit). Clock 02:03-03:13 UTC (07:33-08:43 IST).

## WHAT FAILED / WAS NOT RUN (read first)
1. FAILED, real, a regression of r7d: tests/test_book_folder_refusals.py::test_the_start_scripts_say_the_same_refusal_in_both_forms. `assert ps.index("try { New-Item") < ps.index("catch {")` fails 1830 < 1695: the new try/catch in start_all.ps1 (settings call) comes before the New-Item try, so the test's order check breaks. Alone in a staged git copy: fails again. The same test PASSES on the r7c tree (copy of tree-EV7C). The builder's list of files run did not include this file.
2. Exit code of the full run is 1 although tests pass: tests/tree_guard.py prints "REPOSITORY FOLDER CHANGED BY THE TEST RUN (1 files): 'data'" at the end of group 01 (grp.01: 1779 passed, 2 skipped, rc=1). Cause: tests/test_mode_safety.py:334 does `(REPO / "data").mkdir(exist_ok=True)`; a fresh frozen checkout has no data/, so the guard sees a new empty folder. Reproduced alone: test_mode_safety.py 49 passed, rc=1 on the r7d tree AND on the r7c tree with data/ absent. (The r7c and r7d builder trees already had an empty data/, which hid it.) A clean checkout running the suite gets rc=1.
3. test_hygiene.py::test_hygiene_scan_public failed in place (gitleaks `git` finds the history of this git folder, same as r7c); PASSES alone in a staged git copy without history (1 passed).
4. NOT RUN: PowerShell (reset.ps1, start_all.ps1 text only), CodeQL, SonarCloud, CodeRabbit, GitHub CI, a full-tree mutation run (only the 12 mutants below). 5 other pytest processes (the mutant runner M7R, not mine) were running during the full run and during steps 4-5 (ps-before-full.txt: 2 at start); timings only.
5. Slip: my first lint command text had `2>/dev/null` twice; the harness refused it, nothing ran; I redid it without. Not a test of the null device. Run input was given as an empty pipe (`input=""`).
6. Test files not run: none. 138 tests/test_*.py = r7c's 137 + tests/test_r7d_findings.py, all in grp.00-03, no duplicates. Helpers not test files: conftest.py, crash_launcher.py, desk_env_probe_check.py, edge_case_helpers.py, support.py, tree_guard.py.

## 1. Patch (raw: sha.txt, apply.log, apply-stat.txt, bytecompare.txt, apply_matrix.txt)
- sha256 -c: all 3 patches OK (equal sha256-r7d.txt). git apply --check rc=0, apply rc=0. Tree id of HEAD = 49d3c859...
- Numbers: measured `git apply --stat` and `git diff --cached --stat` both "150 files changed, 14560 insertions(+), 868 deletions(-)". Builder claimed +14524/-868 (868 and 150 match; insertions differ by 36, not explained).
- Byte compare with tree-R7D (excl. .git, caches): only difference "Only in tree-R7D: data" (empty folder).
- apply_matrix.sh --check: rc=0, "APPLY MATRIX: OK"; 17 PASS, 7 FAIL cells; the table rows are identical to apply-matrix-r7d.txt (diff empty). Recommended cells a-crlf-plain, b-crlf-plain, c-lf-plain PASS. The 7 FAIL cells are the same ones as the builder's (a-lf plain/iws/pbin, b-lf pbin, c-crlf plain/iws/pbin).

## 2. Full run (recipe run_full.sh: env -i, unshare -n + lo_up-q4g.py, DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1, detached)
| group | result | time |
|---|---|---|
| grp.00 | 2 failed (book_folder start scripts; hygiene in place), 1360 passed, 1 skipped | 373.8 s |
| grp.01 | 1779 passed, 2 skipped, rc=1 (data/ guard, item 2) | 583.4 s |
| grp.02 | 834 passed, 2 skipped, rc=0 | 161.0 s |
| grp.03 | 1352 passed, 2 skipped, rc=0 | 193.9 s |
Total 5325 passed, 2 failed, 7 skipped. (r7c: 4253 passed, 8 failed, 7 skipped before reruns; the 6 r7c non-hygiene failures are gone: clock_steps, demo_folder_guard, 5 portal_demo.) Builder claimed 420 passed on its final set, no whole-tree number.
After the run: git status = only staged files, no unstaged change; ignored __pycache__ in demo_only, scripts, src/lead_desk, tools (created during the run at 02:04, in spite of PYTHONDONTWRITEBYTECODE=1; some test starts a process without it); empty folder: data/ (made by test_mode_safety); no file name with a newline.
Skips: root can read a no-permission file (x2), ntpath.isreserved needs 3.13, load-number run, Windows-only reset (+ test_book_folder root skip).

## 3. Lint (copy of the staged tree, `--no-cache`)
- ruff 0.17.1 check: "All checks passed!" rc=0. format --check: "215 files already formatted" rc=0.
- bandit -ll CI set (src tools scripts -c pyproject.toml): rc=0, Medium 0, High 0.
- bandit -ll whole tree incl. tests (no -c; pyproject excludes tests): rc=1, Medium 22, High 0, all in 14 test files (claim_checks_and_crm_mode, followup_edge_cases, hung_adapter_calls, hung_model_call, later_approval, load_tools, model_stamp_and_reaper, mutants, mutation_guards, portal_lead_pages, reset_scripts, review_item_edge_cases, slow_sender, stamp_locks_and_budget). Builder: 22 Medium, none in support.py: same. r7c had 23 (support.py:451 gone).
- Suppressions (line counts, grep -rIE): frozen noqa 250, type-ignore 121, nosec 12, nosemgrep 32, S603 52. r7c 174/127/8/32/7. r7d 175/126/8/32/7. Sum noqa+type+nosec+nosemgrep r7c 341, r7d 341 (builder says 335=335 with another grep). One noqa more, one type-ignore less than r7c.

## 4. Hostile (hd/hostile-table.md, copied to EV7D-hostile-table.md; HD7 rc=0; 278 rows, 139 per tree)
| | old | new (EV7D) | (r7c new) |
|---|---|---|---|
| traceback in output | 22 | 0 | 0 |
| hang | 11 | 0 | 0 |
| escape char | 1 | 0 | 0 |
| typed text echoed | 0 | 0 | 0 |
| longest wall | 30.02 s | 5.91 s | 5.79 s |
Bounded checks (bc/bc7d.py, unshare -n, r7c tree vs EV7D; logs/bounded.log):
- load_driver closed port: r7c burst:100000, burst:1000, rate:50:3 all hit my 25 s hard stop (no output). EV7D: rc=3, one line "ERROR: the desk cannot be reached: nothing answers at that address (is it running?); no request was sent": burst:1000 3.2 s, rate:50:3 4.2 s, burst:100000 19.5 s in that run (other pytest running, many processes). Run alone twice: 0.7 s and 0.5 s (burst:10000 0.1 s). Builder claim "well under 5 s": holds alone, not in the loaded run.
- fake_model_server --port=0: listens on a random port, still running at 10 s, ended by the check (both trees).
- FIFO as SMTP CA file: both `CaFileRefused DESK_SMTPP_CA_FILE cannot be read as a file of trusted certificates` (3.1 s new).
- empty --key-file (run_live_check): rc=2 "the key file holds no key" (both), 0.3 s.
- IMAP silent server (step 10.0, total 2.0): r7c returned after 15.3 s; EV7D 3.8 s; rc 0, 1 connection, no traceback.
- run_real_check --live-model, key file ends with NBSP, no input: r7c printed the cost lines and reached "Start?" (MAIN-RC 6 at EOF, prompt=True); EV7D no prompt, MAIN-RC 2, 3 lines, 9.3 s.
- SMTP reply: cap bytes accepted in both; cap+1: r7c `code 250`, EV7D `_Closed: reply too long`.

## 5. Fail-before (r7d tests + changed helpers support.py, tree_guard.py copied into a git copy of tree-EV7C; one file per run; logs/fb-*.log; fa = as is, fb = plus constant IMAP_SECONDS_MAX like the builder)
| file | fa (as is) | fb (+constant) |
|---|---|---|
| test_r7d_findings | collection ImportError IMAP_SECONDS_MAX | 58 failed, 8 passed (601.9 s); builder claim 58/8 = same |
| test_hubspot_probe | 1 failed, 41 passed | 1 failed, 41 passed |
| test_r7c_start_all_parity | 1 failed, 4 passed | 1 failed, 4 passed |
| test_r5_refusals | 1 failed, 212 passed | 1 failed, 212 passed |
| test_script_number_limits | 1 failed, 114 passed | 1 failed, 114 passed |
| test_real_check_dry | 79 passed | 79 passed |
| test_r7c_burst_probe_and_names | 8 passed | 8 passed |
| test_r7c_smtp_reply_total_cap | 2 passed | 2 passed |
| test_special_output_files | 47 passed | 47 passed |
The last 4 pass on the r7c code (not fail-before; real_check_dry test change is the builder's stated "same assertions").

## 6. Mutants (mut7d.py, copy of tree-EV7D per mutant, unshare -n; logs/mut7d.out)
| mutant | tests | result |
|---|---|---|
| CLEAN | 5 r7c files | rc 0, 36 passed |
| M3 jsonread RecursionError->KeyError | same | KILLED, 12 failed |
| M8 bad_request RecursionError removed | same | KILLED, 2 failed |
| D05 imap deadline line removed | same | KILLED, 2 failed |
| D11 smtp_provider conn.close() removed | same | KILLED, 2 failed |
| D20 run_real_check strip(" \t")->strip() (fullmatch) | same | KILLED, 2 failed |
| D21 same on out[name...] | same | SURVIVED, 36 passed (same as r7c) |
| N1 live key check removed (run_real_check) | test_r7d_findings | KILLED, 5 failed (411 s) |
| N2 IMAP upper cap removed | test_r7d_findings | KILLED, 4 failed |
| N3 reply cap +2 -> +1 | r7d + smtp_reply_total_cap | KILLED, 9 failed |
| N4 hubspot _why prints any category | r7d + hubspot_probe | KILLED, 1 failed |
| M1 load_driver listen probe disabled | test_r7d_findings | KILLED, 1 failed |
N1-N4, M1 are my own picks (R7D-RESULTS names no mutant list; its "CONTROL" labels name none executed). Mutant folders removed; tree-EV7D unchanged after all runs (git status clean apart from index).
Processes: none of mine left running. Working copies removed except tree-EV7D and out/EV7D logs.
