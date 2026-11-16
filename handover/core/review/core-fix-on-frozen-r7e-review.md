# Review of r7e (core-fix-on-frozen-r7e.patch, delta r7d to r7e), fallback goldfish reviewer

Money and mail path, no round cap. Date 2026-11-14. Made-up data, loopback only (every run inside `unshare -n`), no spend. I worked only in copies under /home/user/build/rr6/tmp-REV7E (tree = copy of tree-R7E without .git; froz = frozen files plus the r7e tests). No tree was edited (one temporary mutant in my copy of load_driver.py, restored and diffed).

## NOT RUN / NOT CHECKED (first)
- No full suite. I ran: tests/test_r7e_findings.py, test_r7c_clean_tree_guard.py, test_book_folder_refusals.py, test_portal_demo.py together (158 passed, 1 skipped "root can read any file", 112 s), and test_r7d_findings.py -k "handshake or n2 or imap" (36 passed, 4.5 s). ruff check "All checks passed", ruff format --check "216 files already formatted" (venv-br ruff).
- Not run: PowerShell (reset.ps1, start_all.ps1: no .ps1 changed in r7e), the hygiene/git tests (need a staged git copy), Python 3.13/3.14, any mutant of the guard (I read the builder's mutg logs and checked the labels against them; I did not re-run those mutants), EV7E evidence (not read), the builder's item 7 (the two mail-path files it could not find: still not read by me).
- The test_hygiene and test_vendor_hosts "CONTROL ... passes on the frozen tree" labels: not checked (need git).

## Verdict
NOT CLEAN. 0 Blocker, 1 Major, 3 Minor, 2 Nit. M1-new itself is closed; the Major is a sibling in the same class (the stop state and the answered state disagree).

## Major

### M1. A run the driver stopped early can still end rc 0 with no refusal line, while most requests were never sent
File: load_tools/load_driver.py:403-412 (_note_attempt) and :598 (run, `unreachable`).
`_STOP` is set when the error counter reaches 2 x threads before any answer. If an answer arrives later (a slow first reply, a desk that is slow to start), `_ANSWERED` is set, so `unreachable` is false, but `_STOP` stays set: every remaining request is logged `driver:stopped` and never sent, and the run ends rc 0 with the normal JSON summary and no warning.
Measured (made-up stdlib server on loopback; first request answered 202 after 3 s, requests that arrive in the first 3 s are dropped; burst:8, 1 worker, 2 threads): rc 0, final_status `{'error': 1, '202': 1, 'driver:stopped': 6}`, stderr empty. Six of eight requests the desk could have taken were silently not sent and the exit code says success.
The false "cannot be reached" line itself cannot appear after an answer (see "M1-new closure"); this is the opposite failure: a partial run reported as success. Same class as M1-new: two flags that can disagree (stop set, answered set later).
Fix at the choke point: in `run`, if `stop.is_set()` (any `driver:stopped` line exists) end with a non-zero code and one true line ("the run was stopped early: N of M requests were not sent; the desk answered only after the stop"), or do not stop on errors seen before the first answer has had a chance to arrive (stop only after the first full try-deadline without any answer). Test: the server above; assert rc is not 0 and the line names the count.

## Minor

### m1. CONTROL labels still false: "passes on the frozen tree" is untrue for 11 test cases (r7d m2 not fully closed)
I ran the labelled tests against frozen source (frozen files plus the r7e tests/ folder, froz):
- 10 of the 23 tests labelled "CONTROL (r7e, new since frozen): passes on the frozen tree..." FAIL on frozen: `tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once` for lock-pipe, lock-link-to-pipe, lock-folder, model-log-pipe, model-log-link-to-pipe, model-log-folder, stats-pipe, stats-link-to-pipe, trace-pipe, trace-link-to-pipe. Frozen says "cannot open the lock file: UnsupportedOperation", the test wants "... not a regular file". These are real fix tests (good), but the label says the opposite.
- `tests/test_portal_demo.py::test_burst_keeps_every_answer[hang_up-error]` is labelled "CONTROL (r7e, old, body unchanged): passes on the frozen tree". Both parts false: the decorator changed ("RemoteDisconnected" in frozen, "error" now) and it fails on frozen.
- The other 19 "old, body changed" and 13 "new since frozen" cases I ran passed on frozen, so those labels hold. The label kind (new / old changed / old unchanged) matched a body diff against frozen for every labelled test except the portal one (checked with ast, all test files).
Fix: for these, replace "passes on the frozen tree" with "FAILS on the frozen tree (fix test)"; make the kind a computed fact. The sentence "passes on the frozen tree" is one generic line on 51 tests; prefer a per-test fact only where it was run.

### m2. docs/real-services.md overclaims about a changed key file
New line: "a file that you change, replace or damage between the check and that later read is refused by the program that reads it". A file replaced by another valid key is simply read and used; only a damaged one is refused. Fix the sentence: "a file that you damage (empty, too big, not a plain file) between the check and the later read is refused...; a file you replace with another valid key is used as it then is." (This is the N6 statement; it exists, but is wrong in one word.)

### m3. tests/support.py::book_folder_in_repo follows a pre-existing `data` link
`data.exists()` and `mkdir(exist_ok=True)` and `mkdtemp(dir=data)` follow a symlink: if `data` is a link to a folder, the test creates (and removes) its folder inside the link target. It never deletes a pre-existing non-empty data/ (rmtree only the fresh folder, rmdir only when this call made it; fine) and never follows a link for deletion. The rule given for this review says "must not follow a link". Fix: `if data.is_symlink(): pytest.fail(...)`/refuse, and make `made` from `os.path.lexists`.

## Nit

### n1. A desk that dies after answering keeps the driver busy for request-count x 30 s
Measured: server answers 5 requests then drops everything; burst:8, 2 threads: rc 0 after 62.7 s, 3 `error` lines (each request retries for the 30 s deadline). With burst:100000 and 64 threads the run would last hours. By design (patient sender, BURST_RETRY_DEADLINE_SECONDS) and the same in r7d, so not a r7e regression, but nothing bounds the total. Suggest: stop when every try of the last N requests ended in an error after the answered state (or a total run deadline from the schedule length). Owner decision if kept as is: state it in docs/limits.md.
### n2. A stray empty `data/` folder sits in tree-R7E
/home/user/build/rr6/tree-R7E/data (empty, dated 01:36) is not in frozen and not in a patch (an empty folder cannot be). A leftover of an earlier run; harmless to the patch, but the evidence tree is not "as the patch makes it". Remove it before EV7E counts the guard.

## Closure of r7d findings (my checks)
- M1-new (answered flag): CLOSED. `_note_attempt(code)` is now called first for every code (load_driver.py:208). Fail-before by me: I reverted those lines in my copy; test_m1_new_... FAILED with "ERROR: the desk cannot be reached: every request ended in a connection error"; restored (diff clean); with the fix it passes. Server patterns on loopback (burst:8, 2 threads unless noted): answers-then-drops rc 0 (5 x 202, 3 error, 62.7 s; see n1); drops-then-answers rc 3, 2 s, "cannot be reached" (true: no answer was ever received, 2 error + 6 stopped); only 202 rc 0 8 x 202; only 429 rc 0 8 x 429; alternating drop/202 rc 0 8 x 202; only 503: still retrying after 100 s (killed by my harness; 30 s deadline per request x 4 requests per thread, by design). Closed port 127.0.0.1:1 with burst:100000: one line "nothing answers at that address ... no request was sent", rc 3, 0.49 s, no log file made. The false line cannot appear after any answer: not seen in any pattern. The new problem is M1 above.
- m1 (exit code 2): CLOSED by decision (kept 2); constants.py, docs/limits.md and docs/settings.md name run_real_check as the one exception; test_m1_the_exit_code_2... passes; I did not run it on r7d (by construction it fails: the strings are new).
- m2 (CONTROL labels): PARTLY. The 13 clean_tree_guard labels are TRUE: I compared each "killed by mutants X" with the builder's raw/mutg-A..J logs: all 13 match exactly (e.g. D kills 9 incl. the unchanged-tree test; H and H2 survive, as the file says). Re-running those mutants: not done by me. The rest: see m1 above.
- m3 (portal query): CLOSED. test_state_reads_ask_the_sender_for_at_most_200_rows asserts at least 2 queries and all equal `limit=200`; passed in my run. Mutant claim (LIMIT_QUERY emptied) not re-run.
- Nits: N6 stated (but see m2). `_token` removed from hubspot_probe._why (no caller passes it; test passes). imap_count handshake: see next.

## imap_count (point 2): the total deadline is still real
Handshake timer removed. CPython's `do_handshake` bounds the whole handshake by the socket time-out (it does not restart per byte), and `_create_socket` sets that time-out to min(step, time left) just before wrap_socket. Evidence: test_n2_the_total_time_limit_covers_the_tls_handshake [silent] and [handshake-drip] (drip = TLS record header then one byte every 0.2 s) pass in about 1.5 s against a 1.5 s total and a 30 s step; the builder's mutant without the timer passed all 36 before the change and they pass now (my run: 36 passed). Connect: bounded by min(step, left) per address; silent and reads: `_DeadlineReader` unchanged. Classification: `handshake_limited_by_total = left_now <= step` is computed at handshake start, correct. Dropped imports (socket, threading) are unused now: ruff clean. Not tested by me: a host with several addresses, all silent (each gets min(step, left), so the total still holds by the same bound).

## Changed existing tests (point 3)
- test_book_folder_refusals ordering: old `ps.index("try { New-Item") < ps.index("catch {")`; new: New-Item before the refusal line, exactly one `catch {` between them. Not weaker than the old assertion (the old one did not tie the catch to the line either); the regex on the line and exit 4 is unchanged. Passed in my run.
- test_mode_safety reset_sh and test_reset_scripts (3 uses): assertions identical, only the setup/cleanup moved into the helper (read the delta line by line: no assertion removed). Helper: removes only its own fresh folder, rmdir of data/ only when this call made it and it is empty, never a non-empty one. Link: see m3.
- test_portal_demo: one new test; the rest label-only except the label problem above.
- No test deleted; no assertion text removed in the delta apart from the two above (checked by listing every non-comment changed line of tests/ in the delta).

## Suppressions (point 5)
Delta r7d to r7e: 0 added and 0 removed lines containing noqa, type: ignore, nosec, nosemgrep, S603, pragma (grep of the delta). ruff and format clean.

## Not done by me (fix-dont-defer)
The guard mutants (read, not re-run); PowerShell; the two mail-path files the builder could not find (item 7 of R7E-RESULTS: owner of that item is the lead; they must be sent to the next round); full suite and EV7E evidence. Builder open item 3 (one flake of test_start_all_sh... under load): I did not run test_reset_scripts, so not seen by me.
