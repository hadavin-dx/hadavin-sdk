# RESULTS-B (builder B, order C-R7U): m7 mail counter, m8 loopback table, m5 weak test

Start 2026-11-14 16:06 UTC (21:36 IST). Tree: /home/user/build/rr6/tree-R7U-B (byte copy of tree-R7T + this delta).

## FAILED / NOT RUN / NOT CHECKED (first)
- NOT RUN: the full suite and the guard run (the lead runs ONE guard run after the merge). Run here: my file, tests/test_r7t_findings.py, tests/test_real_check_dry.py (231 passed, after1.log) and a final-bytes re-run of my file plus the r7t subset (after2.log, see the end of this file).
- after1.log ended with "REPOSITORY FOLDER CHANGED BY THE TEST RUN (2 files)": I edited the docstrings of the two test files while that run was going (my own edit, not a test writing into the tree). after2.log is the run on the final bytes.
- NOT DONE (honest): the smtp `attempts` counter is NOT turned into a failing check (reason below). Residual of m7 that stays: a mail in delivery lag after a hard kill is invisible to both counters.
- Mutants ran on a copy (out/R7U-B/mutX, 5 MB), not in place; its test file has the docstring text from before my last docstring edit (code and test bodies identical).
- ruff I001 on scripts/run_real_check.py:64 appears on the plain r7t file too (checked: same single I001 on a copy of r7t); it comes from checking a copy outside the package, not from my change. Ruff check/format on the three changed files with src, tools, demo_only linked: only that I001.
- Interaction with builder A: A owns counter value checks inside `read_counter_files_checked` (m2). My smtp read goes through that reader, so A's value check protects the mail counter too. I did NOT test hostile values (1e999, -1, true) for the smtp counter because that is A's code; the lead's merge should add the smtp suffix to A's value-check test. My hunk in run_real_check.py is at the line that read the smtp counter plus one new function; no other region touched.

## Findings and test ids (file tests/test_r7u_b_findings.py unless named)

### m7 the smtp `sent` counter
Code (scripts/run_real_check.py): new `smtp_counter_is_known(read)` (file found, no unreadable file, `sent` present), placed just before `drain`; at the old line 1308 the counter is read with `read_counter_files_checked`; when not known the run prints "the desk's mail counter cannot be trusted ..." and hands floor F4 an empty dict, so F4 fails (result `checks.ok` false, exit EXIT_FAILED). Before: `read_counter_files` summed whatever files could be read, so ONE unreadable file of two gave a smaller number and F4 could hold.
Note: a missing file / a file without `sent` already failed on r7t (F4 reads `sent` as None); those cases are PINS.

| test | on r7t | on r7u-B |
|---|---|---|
| test_b7_one_unreadable_mail_counter_file_is_not_a_smaller_number_it_fails_closed | FAILS | passes |
| test_b7_a_real_mail_counter_file_cut_in_half_fails_closed (real desk processes, real file cut, real reader) | FAILS | passes |
| test_b7_the_mail_counter_rule_needs_a_file_no_unreadable_file_and_the_sent_number | FAILS (no function) | passes |
| test_b7_the_run_says_in_words_that_the_mail_count_is_not_known | FAILS | passes |
| test_b7_a_missing_or_incomplete_mail_counter_fails_closed[no-file / no-sent-number / only-unreadable] | PIN | passes |
| test_b7_a_run_with_a_readable_mail_counter_ends_with_zero (control) | PIN | passes |

Pins named: the three parametrised cases and the control kill a change that makes a missing counter read as 0 or a known counter always unknown (mutants B09, B10, B12).

Honest answer to "is a mail in delivery lag after a hard kill invisible to both counters, can `attempts` bound it?" (read from src/lead_desk/smtp_provider.py `send`): `attempts` is written before the connection; `sent` is written only after the server's final reply and the close of the socket. A desk stopped hard after the server accepted the mail and before the `sent` write leaves a delivered mail the desk's `sent` does not count. The mailbox reader counts it only once the mailbox shows it (delivery lag), so for that time BOTH sources miss it: YES, invisible. `attempts` (written first) does count that send, so `attempts` is a CEILING: real mails <= attempts. It cannot be a failing check for F4's rule "mails <= leads + unknown", because an attempt that failed before the network step (connection refused, retried) is also counted, so `attempts > leads + unknown` can happen with no excess mail, and a check on it would raise false failures. What bounds the invisible mails today: only sends in flight at the kill can be in that state, the floor `window` already uses min(SEND_WORKERS_MAX, sending_at_kill), those leads end `unknown`, and F4 allows `leads + unknown`, so one invisible mail per in-flight send is inside the allowance. Next step if a stricter bound is wanted (needs the owner's decision, it changes what the run may call ok): write a `failed_before_network` counter in smtp_provider.send, then check `mails <= leads + unknown` against `attempts - failed_before_network`; not built because it changes the provider's counter file contract that builder A/C do not expect. t16 (tests/test_r7t_findings.py): it feeds made-up numbers to the floor function and passes on r7s and r7t: kept (no deleted tests), comment edited to say it is a unit pin of F4 arithmetic only and vacuous for the reading of the counter; the non-vacuous tests are the four FAILS above.

### m8 LOCALHOST accepted as design, names, table
Statement of design: in the docstring of tests/test_r7u_b_findings.py (I do not own the loopback module or fakes docstrings; C does).
Renamed (tests/test_r7t_findings.py):
- OLD test_t12_a_loopback_spelling_is_accepted_by_the_shared_rule -> NEW test_t12_the_shared_rule_answers_yes_to_a_loopback_spelling_and_promises_no_listener (docstring added; body unchanged).
- test_t6_the_mail_fakes_still_listen_on_this_computer kept: it really binds three hosts (HOST, localhost, 127.0.0.1) and asserts a port, so its name is true.
New table tests (PINS, they pass on r7t; there is no code change for m8, the behaviour was right and only the claims were loose):
- test_b8_the_rule_accepts_these_spellings_by_design_and_a_bind_is_a_separate_fact: truthful result measured here (Linux, under `unshare -n`, probe in out/R7U-B/probe.py): "LOCALHOST": rule yes, bind works, address 127.0.0.1. "[::1]": rule yes, bind FAILS (socket.gaierror: the stand-in server is an IPv4 socket). "::ffff:127.0.0.1": rule yes, bind works, address 127.0.0.1 (the system reads the mapped literal as the IPv4 address on this platform).
- test_b8_whatever_the_bind_does_it_never_listens_beyond_this_computer[LOCALHOST / [::1] / ::ffff:127.0.0.1]: a working bind is on 127.x, a failing one raises.
The `::ffff:` row is platform dependent (a different OS resolver may refuse it); the test asserts the Linux result and says so.
Non-vacuity: mutants B13 (LOCALHOST refused), B14 (host argument ignored), B15 (mapped address no longer read as IPv4) are killed by b8.

### m5 t9 test 2
OLD test_t9_a_counter_the_desk_could_not_write_ends_the_real_run_as_failed (tests/test_r7t_findings.py): its body makes the counter path a folder BEFORE start, so the strict write fails before the create is sent: no contact exists and `_hiding_crm(1)` hides nothing. It still tests "a counter the desk could not write ends the run as failed". Body unchanged (a weaker/other body would lose that case); docstring rewritten to say exactly this and to point to the new test.
NEW test_b5_a_hidden_contact_and_a_counter_file_that_cannot_be_read_ends_as_failed: real desks create real contacts and write the real counter; the list hides 1 contact (`_hiding_crm(1)`), then the first HubSpot counter file is cut in half at read time; asserts `created` read before the cut is >= 1 (contacts exist), "counter cannot be trusted" printed, EXIT_FAILED. Companion test_b5_control_a_hidden_contact_with_a_readable_counter_is_reported shows the hidden contact is real ("may be left in HubSpot"). Both are PINS: they pass on r7t (the r7t code was already right; the order asked for a test that fails on r7t but there is no failing behaviour to catch; non-vacuity: mutants B16 and B17, see below).
Non-vacuity: mutant B16 (counter_is_known without the unreadable clause) and B17 (counter_known = True) are both KILLED by test_b5_a_hidden_contact_and_a_counter_file_that_cannot_be_read_ends_as_failed.

## Before/after on the r7t sources (pins named)
before.log (my file on the unchanged r7t sources, run 5 min 23 s): 4 failed, 10 passed. Failing ids: the four FAILS rows of the m7 table. Passing (PINS): b7 control, b7 three parametrised missing/incomplete cases, b8 table, b8 never-beyond x3 is 3 ids, b5 control, b5 main (10 ids in all: 1 + 3 + 1 + 3 + 1 + 1).
after1.log (my file + tests/test_r7t_findings.py + tests/test_real_check_dry.py on r7u-B): 231 passed in 906 s.

## Mutants (out/R7U-B/mut_b.py, results mut-results.tsv, raw mutraw-B*.txt; one runner, one mutant at a time on copy mutX, restored from tree-R7U-B and compared byte for byte after each: 17 of 17 restored-byte-equal=True)
B01 files > 0 -> >= 0 KILLED; B02 drop unreadable == 0 KILLED; B03 drop "sent" in totals KILLED; B04 first `and` -> `or` KILLED; B05 unreadable == 0 -> < 2 KILLED; B06 "sent" -> "attempts" KILLED; B07 ignore the known flag at the hand-over to F4 KILLED; B08 known = True KILLED; B09 read the hubspot suffix KILLED; B10 wrong suffix (no file) KILLED; B11 message printing removed KILLED; B12 unknown gives {'sent': 0} instead of {} KILLED; B13 `name.lower()` dropped in is_loopback_host KILLED; B14 make_fakes_server ignores the host argument KILLED; B15 mapped-IPv4 branch removed KILLED; B16 counter_is_known without the unreadable clause KILLED (by b5); B17 counter_known = True KILLED (by b5). 17 killed, 0 survived.

## Ruff, suppressions
ruff 0.17.1 (/.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/...) on a COPY of the three changed files (out/R7U-B/ruffcopy, src/tools/demo_only linked): `ruff check`: only the I001 that r7t's own copy also shows; `ruff format --check`: 3 files already formatted. Suppressions (one method, the grep from the order): 367 on tree-R7U-B, delta 0.

## Delta
out/R7U-B/r7u-B.diff (diff -ruN a/ b/ from tree-R7T; 3 files: scripts/run_real_check.py, tests/test_r7t_findings.py, tests/test_r7u_b_findings.py new) and r7u-B.diff.sha256. No pycache of mine (the six __pycache__ folders exist in tree-R7T too).

## Ask-back answered
The take-side banner test q1: tests/test_r7q_findings.py::test_q1_the_banner_cost_counts_the_longest_request_the_run_can_send (line 110; the other q1 tests in that file are the longest-request and email-key ones).

## Final-bytes run
after2.log (my file + tests/test_r7t_findings.py subset -k "b7 or b8 or b5 or t12 or t9 or t16 or t2 or t1", final bytes, no edits during the run): 79 passed, 73 deselected in 841 s, no "REPOSITORY FOLDER CHANGED" line. Diff sha256 in r7u-B.diff.sha256 (mutX and the ruff copy were deleted after use to save disk; df shows the disk still ~2.7 GB free).
