# EVIDENCE RUNNER V1 (for builder F1). Raw logs in this folder. No judgement.
Trees: RR/tree-V1old and RR/tree-V1 both `git HEAD 61ded9e` (patches applied as working-tree changes, not committed; the brief's "ee3d6ce" is not a git sha in either tree). `diff -rq` old vs V1 = exactly the 7 files of fix.patch (out/F1/fix.patch sha256 31b5be92d983cdc3...); `git apply -R --check` on V1 OK, `git apply --check` on V1old OK. lead_desk.__file__: tree-V1old/src/lead_desk/__init__.py, tree-V1/src/..., tmp-V1/mut/src/... (each under its own tree).
All runs: `unshare -n` + drivers/lo_up-q4g.py, TMPDIR private, PYTHONPATH=T/src, pytest -q -p no:cacheprovider.

| run | tree | what | passed | failed | skipped | errors | wall | hang |
|---|---|---|---|---|---|---|---|---|
| 1 | V1old 61ded9e | new test file, NO refusals.py | 0 | 0 | 0 | 1 (collection) | 1s | no |
| 2 | V1old 61ded9e | new test file + stub refusals.py (EXIT_REFUSED=2, EXIT_UNREACHABLE=3) | 0 | 32 | 0 | 0 | 11s | no |
| 3 | V1old | same, --tb=line | 0 | 32 | 0 | 0 | 10s | no |
| 4-6 (V1-...-run1..3-newtests) | V1 61ded9e+F1 | new test file | 32 | 0 | 0 | 0 | 9s each | no |
| 4 neighbours | V1 | 28 neighbour files + new file (29) | 2245 | 0 | 109 | 0 | 721s | no |
| 4 neighbours | V1old | same 28 files (new file absent) | 2213 | 0 | 109 | 0 | 715s | no |
Neighbour delta: +32 passed (= the 32 new tests), skipped 109 = 109, failed 0 = 0. Skips: playwright missing (5), no gitleaks (4), ntpath.isreserved needs Python 3.13 (1), others same in both trees.

## (1) Fails-before
No stub: `ModuleNotFoundError: No module named 'refusals'` at tests/test_script_refusals_feed.py:24 (collection error, 1 error). Note: brief said constants EXIT_USAGE/EXIT_UNREACHABLE; the real file has EXIT_REFUSED/EXIT_UNREACHABLE, I used those.
With stub: ALL 32 FAIL on old code (ids: V1old-61ded9e-run2-stub.log). First error lines I read per test (19 of the 32 have a readable detail block in run 2; run 3 --tb=line shows the same first line per test): 17 x `AssertionError: Traceback (most recent call last):` (index out of range x5, bad DESK_PORT x3, desk not running, canned file x6, scrub unwritable text, SMTP CA folder), 2 x `AssertionError: usage: feed.py ...` (--index/--all). The other 13 (hang/hangup/rubbish, scrub non-workflow x6, reset_check/crash_desk, SMTP CA not-a-certificate/missing) fail on the same assertions family (Traceback in output, or wrong exit code); I did not read each one's first line separately.

## (3) Ruff
Project config (line-length 120, pyproject): `ruff check` -> All checks passed; `ruff format --check` -> 7 files already formatted.
With --line-length 100 as the brief asked: check = 153 errors (152 E501, 1 I001), format --check = 6 of 7 files would be reformatted. The project line length is 120, so the 100 result is outside the repo config. Logs: ruff-*.log.

## (4) Mutation (tests/test_script_refusals_feed.py only, in tmp-V1/mut; every file restored and cmp'd identical)
| mutant | killed? | first failing test |
|---|---|---|
| 1 feed.main try/except removed | yes (18 failed) | feed_index_out_of_range[0] |
| 2 unreachable line prints DESK_BIND:DESK_PORT | yes (1) | feed_desk_not_running_says_so... |
| 3a --index upper bound +1 | yes (1) | index_out_of_range[7] |
| 3b --index accepts 0 | yes (1) | index_out_of_range[0] |
| 3c --index last valid index refused (`< len`) | NO SURVIVED, 32 passed | none |
| 4 scrub writes file before encoding | yes (1) | scrub_refuses_text_it_cannot_write... |
| 5 smtp_provider raw SSLError (try/except removed) | yes (3) | smtp_ca_file[not-a-certificate] |
| 6 refusals.EXIT_UNREACHABLE 3->1 | NO SURVIVED, 32 passed (the test imports the same constant, so it moves with it; nothing pins the literal 3) | none |
| 6b feed.py `return 1` instead of EXIT_UNREACHABLE | yes (4) | feed_desk_not_running... |
| 7 scrub: non-UTF-8 no longer refused | yes (1) | scrub_refuses...[\xff\xfe\x00] |
| 8a reset_check bad setting returns 0 (reset.sh would go on to delete; reset_check itself deletes nothing, reset.sh line 52 gates on it) | yes (1) | ...bad_setting...[reset_check.py] |
| 8b reset_check no handler for bad setting | yes (1) | same |
Survivors to fix: 3c (no test of the last valid index) and 6 (literal exit code 3 never asserted independent of the constant).

## (5) Hostile inputs: out/V1/hostile-table.tsv (38 rows; unshare -n, timeout 20s, no desk running)
Traceback: only #17 -> `feed.py` with demo_only/canned_leads.json = 100000-deep nested `[`: exit 1, 23-line traceback ending `RecursionError` (load_leads catches OSError/ValueError, not RecursionError; scrub_n8n_export does catch it: #27 refused, exit 2).
Hang (20s timeout, rc TIMEOUT): #14 feed canned file = FIFO with no writer; #28 scrub in.json = FIFO. No refusal line either way.
Typed text echoed (no traceback, exit 2): #1 `--index 1e999`, #3 5000-digit --index, #6 unicode --index: argparse's own `feed.py: error: argument --index: invalid int value: '<typed>'` plus usage line (not the "refused:" form; F1's test comment says the shared parser is builder F2's job). #7 ESC text not echoed (argparse accepted/escaped differently, see table).
Others OK (one refusal line, exit 2 or 3, no echo): --index -0, fullwidth, arabic digit (treated as 1 -> exit 3), spaces; DESK_PORT ESC/1e999; DESK_BIND 100k chars; canned dir/5000-digit int/symlink/10 MB (exit 3); reset_check bad ports (2), lock path dir (3), 100k-char db path (3), ENOTDIR path (rc 0, nothing printed); scrub 10 MB ok (rc 0, 9s), deep nest/non-UTF-8/5000-digit/odd types(rc 0, 204 bytes)/dir/symlink/out-dir/lone surrogate/0 args/ESC path (rc 2, one line). NUL in argv (#2, #36) cannot be passed by the OS (ValueError in my harness), not run. DESK_PORT with NUL not possible in env either.

## Not run / uncertain
Not run: 68 of 97 test files (all not matching the grep), full suite, Windows, ruff/mypy/bandit/gitleaks beyond item (3). Neighbour runs of V1 and V1old ran in parallel with each other and with other runners on the same 4-core machine; a first V1old attempt was killed (my own 460s wrapper limit, at 58%, no failures seen) and relaunched with a 1500s limit; an orphan of that first run was killed ~1 minute after the relaunch, so the V1old run may have overlapped with it briefly (it passed anyway). Mutation harness: tmp-V1/mutate.py, hostile harness: tmp-V1/hostile.py (my files only).
Commands: tmp-V1/run.sh (wrapper), tmp-V1/mutate.py, tmp-V1/hostile.py, `git apply [-R] --check`, `diff -rq`, ruff check/format (+ --line-length 100).
Cleanup: stub refusals.py and the copied test removed from tree-V1old; no scratch worktrees; no processes of mine left (pgrep checked).
