# Lane 3 fix 2, round 6 (B15b, resumed after B15), 2026-11-14
Base f3c39cf8 + fix-1 r6 + fix-2 r6. No commit, no push. Real clock (date -u): start 05:01Z.
Final head tree 3633781d719a6ebf05b248851e0855a9ef102037 (git write-tree; the recut patch on base, and the on-fix-1-r6 patch on base+fix-1-r6, both give this tree; `git apply --check` rc 0 on a fresh fix-1-r6 tree).

## Where B15 stood
0 of 15 items were done when I started (checked by reading and grepping the files, not by tree-hash diff against the r5 patch).

## The 15 items (all done; tests in tests/test_one_key_file_rule_r6.py and edits to older tests)
1 one line-end rule at all positions + docs; 2 n8n_api uses envnum.read_secret_file; 3 fake model server same, exit 2 kept; 4 AST guard over src/scripts/demo_only/load_tools/tools + sh/ps1 scan + one definition; 5 smtp wrapper = read_smtp_password; 6 mailbox sentence in contract/limits/settings; 7 lock wording "(6) to (12)", step 12 exit 4; 8 one envnum.retry_after_seconds at crm_hubspot, live_claude, burst; load_driver uses it when lead_desk imports, else a stand-alone copy pinned to it by a test (load_driver must run without src); 9 _usd_arg refuses non-finite or <= 0; 10 "lead-book" everywhere (40 lines), "another desk is using this lead-book", run_real_check wording, DESK_OUTBOX values named in docs; 11 AST path-probe guard with a reasoned allow-list (stale allowance fails); 12 O_NOCTTY; 13 fake server cap test (exit 2, 4096 ok, 4097 refused); 14 one path_kind(db); 15 docstring words.

## Extra fix not in the list: lockfile.lock_path
On Python 3.13.18 Path.resolve() does not raise on a loop of links, so two existing tests (a looped lock name, a looped DB path) failed on this interpreter (desk went on to the demo-server step, exit 1). lock_path now stats the resolved path and refuses on ELOOP with LockUnavailableError (RuntimeError still caught for older Pythons).

## Evidence
- Fails before: raw/b15b-fails-before.log = 58 failed, 27 passed on the r5 code (27 are regression pins). My first copy raw/b16-fails-before.log was overwritten by builder B16 (name clash, my slip).
- Hand mutants: raw/b15b-mutation.log: 7 planted, 7 killed, none survived.
- First full run: raw/b15-full-final.log: 2 failed, 4011 passed, 170 skipped in 889s. Both failures were in my new test file. Class: a test text must not hold a pattern a repo guard reads as code. (1) my allow-list string held `st_mtime <` and test_clock_steps wants a `# wall-clock:` mark; (2) a made-up HTTP date held a time of day (`07:28:00`), which test_hygiene_scan_public flags. Fixes: the date is now built with email.utils.formatdate (marked wall-clock), the allow-list line carries the mark. Sweep of the file for time.time(, st_mtime, time-of-day and 32+ hex patterns: only the marked line remains. tests/test_hygiene.py, test_clock_steps.py, test_codeant_hygiene.py pass on the fixed file.
- Second full run: raw/b15-full-final2.log (see the report for its tail).

## Not checked
ruff, mypy, bandit, CodeQL (CI only, by order). Windows. run_live_check handling of SettingRefused beyond the cap tests. No independent EGM review of the r6 result yet.

## Full runs on the final head (tree 3633781d719a6ebf05b248851e0855a9ef102037, clone without the n8n ref and without data/)
- Run 1 (raw/b15-full-final.log, earlier head): 2 failed, 4011 passed, 170 skipped. Both failures were in my new test file (guard patterns in test text); fixed.
- Run 2 (raw/b15-full-final2-hung-at-18pct.log): hung at about 18% in tests/test_fakes_body_before_answer.py; I killed it. The file passes alone (17 passed, 22.6 s). Cause not established (guess: clash with other builders' runs on the same machine).
- Run 3 (raw/b15-full-final3.log), final head: `4013 passed, 170 skipped in 896.78s (0:14:56)`, 0 failed, started 05:57Z.
