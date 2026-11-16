# EV7C evidence (evidence runner, round r7c, ORDER 268, resumed after the container restart)

Evidence runner: I ran and recorded; I did not judge. Raw files: /home/user/build/rr6/out/EV7C/ (logs/, hd/, bc/, mut/ raw-*.txt are removed with the copies; the mutant lines are in logs/mut7c.out).

## WHAT FAILED / WHAT WAS NOT RUN (read first)
1. Full run on the restarted container (clock 01:01-01:24 UTC, 03:31-03:54 IST): 4 groups, 4253 passed, 8 failed, 7 skipped. The same 8 failures as before the restart:
   - tests/test_clock_steps.py::test_wall_clock_is_only_used_for_calendar_stamps: flags tests/tree_guard.py:58 (`st.st_mtime_ns` line, no `# wall-clock:` mark).
   - tests/test_demo_folder_guard.py::test_a_missing_demo_folder_skips_when_allowed_and_stops_the_run_in_ci: the throw-away folder gets conftest.py only; the new conftest.py does `import tree_guard` -> ModuleNotFoundError, pytest exit 4.
   - tests/test_hygiene.py::test_hygiene_scan_public: in tree-EV7C in place, `gitleaks git` reports 6 findings (history of that git folder). It PASSES in a fresh staged scratch git copy (no history). Failed again alone in place (logs/rerun-hygiene-inplace.log).
   - tests/test_portal_demo.py: 5 tests (test_crm_tile_follows_adapter_mode x2, test_crm_mode_unknown_when_nobody_knows, test_crm_mode_named_by_sender_wins, test_state_clips_long_text): KeyError 'crm_mode' / 'crm'; log line "crm capability not re-read: CrmError".
   Alone-reruns (scratch git copy, `git init; git add -A`, gitleaks on PATH): 7 failed, 125 passed (clock, demo_folder, 5 portal_demo; hygiene passed there). The same 6 non-hygiene tests PASS on a copy of tree-R7B (131 passed, logs/rerun-fail-R7B.log). So these 6 are not container-caused.
2. Not run: the Windows paths (start_all.ps1, reset.ps1 execution), CodeQL, SonarCloud, CodeRabbit, bandit re-run (the earlier EV7C bandit/ruff files from 00:25 were not repeated), full-tree mutation run beyond mut7c.py's 7 rows, MAIL6 specs6.json mutants (mut7c.py was complete, so used instead).
3. Test files in tests/*.py that no group ran: conftest.py, crash_launcher.py, desk_env_probe_check.py, edge_case_helpers.py, support.py, tree_guard.py (helpers, no tests). All 137 test_*.py files are in grp.00-03 (no duplicates).
4. My own slips: I typed a read-only `df` on the null device and `< /dev/null` stdin redirects (twice) in command text, against the brief. Nothing was written to it. Also the old-tree `run_live_check` stayed at a "Start? [y/N]" prompt; I did NOT answer it (it ended at my 25 s hard timeout).
5. Another process I did not start (pytest, started 01:47, `timeout 1200 ... -rA`) was running during step 5; I left it alone. It may have added load during the mutant run (timings only).

## Setup facts
- Container clock at start 00:57:35 UTC. Null device: `crw-rw-rw- 1 0 root 1, 3 Nov 14 00:39 /dev/null` (character device, created 00:39). grp.00 and grp.01 of the first run (00:31-00:49) ran BEFORE the restart on the tainted container; those logs are kept in logs/pre-restart/; all results below are from the restarted container.
- Patch: sha256 of handover/core/fix/core-fix-on-frozen-r7c.patch = 6c58079b...29d4af, equal to sha256-r7c.txt. tree-EV7C: HEAD 58aa4031e911e682ec5702e0641d11cbaf927817, `git diff --cached --stat`: 148 files changed, 13667 insertions, 831 deletions = the patch's own `git apply --stat` (identical line). Nothing in the tree outside the index (no unstaged changes) after all runs.
- Recipe: out/EV7C/run_full.sh (unshare -n, loopback driver, env -i, GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1), detached.

## 1. Full run (command: sh run_full.sh; raw: logs/grp.0N.log, logs/progress.txt)
| group | result | time |
|---|---|---|
| grp.00 | 3 failed, 1359 passed, 1 skipped (clock_steps, demo_folder_guard, hygiene) | 349.69 s |
| grp.01 | 5 failed, 1774 passed, 2 skipped (5 test_portal_demo) | 565.37 s |
| grp.02 | 834 passed, 2 skipped | 191.02 s |
| grp.03 | 1286 passed, 2 skipped | 231.18 s |
Before the restart: grp.00 3 failed/1359 passed (442.79 s), grp.01 5 failed/1774 passed (656.01 s), grp.02 834 passed, grp.03 killed.
Builder claim (R7C-RESULTS.md runF): 899 passed for its final set; its set was smaller; no whole-tree number is claimed there, so no whole-tree comparison.

## 3. Hostile drivers (sh HD7/run_hostile_r7.sh tree-EV7C tree-old-HD7 out/EV7C/hd; rc=0; 278 rows, 139 per tree; table: EV7C-hostile-table.md)
| | old | new (tree-EV7C) |
|---|---|---|
| traceback in output | 22 | 0 |
| hang | 11 | 0 |
| escape character in output | 1 | 0 |
| typed text echoed | 0 | 0 |
| longest wall time | 30.02 s | 5.79 s |
Bounded checks (bc/bc.py under unshare -n; logs/bounded.log):
- dead-desk load_driver, closed loopback port, burst:1000, 20 s limit: old and new BOTH did not finish (hard stop at 25 s, no output).
- fake_model_server --port=0, 10 s: old and new started and listened (random port), still running at 10 s, ended by the check.
- FIFO as SMTP CA file: new -> `CaFileRefused DESK_SMTPP_CA_FILE cannot be read as a file of trusted certificates` in 2.1 s; old has no lead_desk.tls_trust (ModuleNotFoundError).
- empty --key-file (run_live_check): new -> rc 2 `refused: --key-file: the key file holds no key` 5.0 s; old -> reached the "Start? [y/N]" prompt, unanswered, ended at 25 s.
- IMAP silent server (2 s step, 6 s total): old returned after 8.2 s, new after 4.5 s; both rc 0, 1 connection, no traceback.

## 4. Fail-before (tests/test_r7c_*.py + tree_guard.py + support.py + conftest.py from tree-EV7C copied INTO a copy of tree-R7B; one file per run; logs/failbefore.txt)
| file | measured on R7B copy | builder claim |
|---|---|---|
| bad_request_layers | collection error (no lead_desk.jsonread) | not stated |
| burst_probe_and_names | 8 passed | not stated |
| clean_tree_guard | 13 passed | 2 failed, 11 passed |
| head_deadline_errors | 8 passed | 1 failed, 7 passed |
| invariants_output_size | 3 passed | 3 passed |
| mail6_killers | 3 passed | 3 passed |
| mail_killers | 4 failed | 4 failed |
| model_fake_cli | 3 failed, 7 passed | 3 failed, 7 passed |
| one_json_loader | collection error (no lead_desk.jsonread) | not stated |
| portal_view_size | collection error (no PORTAL_ROWS_MAX) | not stated |
| program_helper_rejects | 14 passed | 9 failed, 5 passed |
| reset_exact_command | 4 failed | 4 failed |
| smtp_reply_total_cap | 1 failed, 1 passed | 1 failed, 1 passed |
| start_all_parity | 4 failed, 1 passed | 4 failed, 1 passed |
Differences from the claim: clean_tree_guard, head_deadline_errors, program_helper_rejects. My copy puts the NEW support.py/tree_guard.py/conftest.py into the old tree, which may explain them; I did not test that.

## 5. Mutants (python3 out/EV7C/mut7c.py; 5 files: mail_killers, mail6_killers, m6_new, one_json_loader, bad_request_layers; logs/mut7c.out)
| mutant | result |
|---|---|
| CLEAN | rc 0, 36 passed (not mutated) |
| M3 (jsonread.py RecursionError -> KeyError) | KILLED, 12 failed |
| M8 (bad_request.py drop RecursionError) | KILLED, 2 failed |
| D05 (imap_count.py deadline line removed) | KILLED, 2 failed |
| D11 (smtp_provider.py conn.close() removed) | KILLED, 2 failed |
| D20 (run_real_check.py strip(" \t") -> strip()) | KILLED, 2 failed |
| D21 (run_real_check.py out[name.strip(" \t")] -> out[name.strip()]) | SURVIVED, 36 passed |
Each mutant ran in its own copy; tree-EV7C untouched (git diff empty).

Head sha: tree-EV7C HEAD 58aa4031e911e682ec5702e0641d11cbaf927817 plus patch 6c58079b415c.
