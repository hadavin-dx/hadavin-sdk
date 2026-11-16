# T2 report: tests that kill 11 surviving mutants (builder, tests only)

Tree: /tmp/dpld-t2 (copy of A4r4). New file only: tests/test_mutants_round2.py (22 test cases, 12 test functions, names at most 39 characters). No src change.

## What failed or did not go as the brief expected (first)
1. Mutant #41 cannot be applied to A4r4. The text `... AND attempts=? AND send_started=0"` no longer exists: A4r4's give-back (desk.py `_give_back`) has no send_started guard and instead SETS send_started=0 (it is called only for "no file handles left" and "database stayed locked", where nothing was sent; row goes back to pending). The brief's expected behaviour ("give-back must not release a row with send_started=1") is the opposite of what A4r4 does on purpose. I wrote no test for it. Raw note: failbefore/41.txt. Because S1g is changing the give-back path, the lead should decide whether the guard comes back; if it does, mutant #41 becomes real again and needs a test then.
2. Mutant #48 is equivalent (no test, as instructed). Proof: `_record_send_result` is called at desk.py lines 932, 962, 1077, 1189, 1192, 1229. Only the call at 1229 can pass state "sent", and there `err` is still None (it is set only inside the except branches, which also change state). So `last_error` is None whenever state=="sent", and `None if state == "sent" else last_error` equals `last_error`. It differs only if someone calls the private function with ("sent", token, "<text>"), which no code path does. raw: failbefore/48.txt shows the 22 tests pass under the mutant. (test_sent_sets_time_and_clears_error does check last_error is NULL after an earlier error, it just cannot kill #48.)
3. Mutant #3 is equivalent through the desk path (check_payload strips every field with `v.strip()` before normalise_email is called) but not through the function itself; I killed it with a direct test of the public, documented function `identity.normalise_email` ("Strip and lower case").
4. My own slip: the first mutation pass reported #49 as surviving. Cause: a stale .pyc (same size and same-second mtime after restoring the file). I re-ran all 11 with PYTHONDONTWRITEBYTECODE=1; the numbers below are from that re-run. (The pass without the fix could also have shown false kills; the re-run removes that doubt.)

## Evidence per mutant (raw output in /home/user/build/T2-failbefore/<n>.txt, mutant applied in a copy of the tree, tests run with /root/.local/bin/pytest -p no:cacheprovider, PYTHONPATH=src:tests)
| # | result | killing test(s) |
|---|---|---|
| 3 | killed | test_email_key_strips_blanks |
| 35 | killed | test_replay_due_exactly_at_pause_end (1 s after a try, backoff 1 s: replay must drive; 0 s: must not) |
| 41 | NOT APPLICABLE to A4r4 | see 1 |
| 48 | EQUIVALENT | see 2 |
| 49 | killed | test_sent_sets_time_and_clears_error, test_unsent_result_has_no_sent_time[3 cases], test_blind_unclear_end_has_no_sent_time |
| 50 | killed | test_late_result_leaves_put_back_row (BlockAt "D2", row put back to pending by SQL while the drive is between send and result record; result must not touch it) |
| 52 | killed | test_retry_busy_is_503[pending, failed] (claim replaced by one that returns False, as a held lock would) |
| 58 | killed | test_resolve_ignores_failed_row[not_sent, crm_present] (the "sent" case passes under the mutant because of the crm_done condition; it is kept as a guard) |
| 60 | killed | test_counts_match_needs_equality (expected 1 and 3 with 2 receipts) |
| 65 | killed | test_is_busy_takes_both_lock_codes[6, 262] (OperationalError with sqlite_errorcode 6, neutral message) |
| 67 | killed | test_schema_version_refused[2] |

All 22 cases pass on the unmutated tree (`22 passed`).

## Gates
- ruff check tests/test_mutants_round2.py: clean (after one `--fix` of import order). ruff format --check: already formatted.
- Full tests dir, once, background: /home/user/build/T2-full.log: `2 failed, 688 passed, 1 skipped in 343.94s`, rc=1. The 2 failures are the expected ones: test_hygiene_scan_public (no gitleaks) and test_hygiene_wordlist (HYGIENE_WORDLIST not set). The traceback path `../dpld-a4r4/tests/test_hygiene.py` comes from a copied .pyc; no symlinks in the tree.
- /home/user/build/T2.diff: only the new file; `git apply --check` and `git apply` succeeded on a clean copy of /tmp/dpld-a4r4 and the result is byte-identical to the new file.

## Not checked
- Mutants were applied only for these 11, in a throwaway copy (/tmp/t2work/tree, removed). I did not re-run the full 12-file mutation selection or the other mutants.
- Tests are not run against S1g's changed give-back/result paths (not available). The #50 and #52 tests use the private names `_claim` (patched) and the `D2` hook and a direct SQL put-back; #52 does not use a real held lock (would cost 5 s or more per case).
- No parallel-load or timing runs. EGM: not invoked from here (builder); the lead runs the evidence and review steps. R-numbers: studio bible not available in this sandbox; none cited.
- Processes: I started one background pytest (finished) and no others; two other pytest processes on the machine are not mine and were left alone. Checkpoint: /home/user/build/T2-checkpoint.md. Real clock: about 25 minutes.

## Order 223 addendum (cloud, 20:3xZ): mutant #41 treated as equivalent by lead ruling
One-line proof: in A4r4 and in the S1g tree `_give_back` (src/lead_desk/desk.py, the UPDATE at about line 1121) SETS `send_started=0` and only runs when nothing was sent (no file handle left, or the database stayed locked), so the mutated text `AND send_started=0` from the old guard no longer exists; no observable behaviour can differ. Lead ruling ORDER 223: no test. Equivalent mutants in this round: #41 (ruling), #48 (verified: the `sent` result is only called with err None), #3 (equivalent through the desk path, killed by a direct test of identity.normalise_email).
