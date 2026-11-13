# P2 v2.3 delta (test-only)
Patch: sonar/sonar-p2-regex-http-bug-v2.3-delta.patch. EDITS tests/test_sonar_p2_gaps.py (the file v2.2 adds): +87 -3 lines, 12 -> 18 tests. No src change. Applies on 26ca762 (which already contains P2 v2.1 and P1 v3.2) AFTER v2.2-delta (it edits that file; it cannot go before it). Also applies on db54e13 + P2 v2.1. Order matrix with P3 v3 (and P1 v3.2 on db54e13): evidence-p2v23-5.

## Failures / not done first
- Not run: full suite (lead's), Sonar, Windows, Python 3.12 (3.13 used). 5 of the 31 reviewer mutants still survive THIS file (O13, O15, O17, O24, O25); the reviewer measured them as killed by existing repo tests, I did not re-run those repo files.
- The 30-run files were run on a shared 4-core machine with other sessions loading it; 0 failures.
- New tests pin what the base does; they do not prove that behaviour is right.

## What was found in desk.py (read, not guessed)
`_GateBusy` subclasses sqlite3.OperationalError with the text "database is locked...", so `db.is_busy` is True for it: `_finish_with` SWALLOWS it (log "<what>: database stayed locked; ...", returns None), `_locked_retry` does not retry it (one try), other busy errors are tried LOCK_RETRIES (3) times.

## Tests added
(e) test_e_a_locked_database_is_swallowed_and_logged [_GateBusy, plain "database is locked"]: `_record_send_result` returns without raising; exactly one log line "record_send_result: database stayed locked; the row stays as it was and shows as stalled"; no "expected one row" warning; tries 1 for _GateBusy and 3 for plain busy; row still 'sending', stage 'new', copy wait kept. Kills O21 (the asked mutant), O03 (log line removed), also O02, O04, O05, O19, O11, O26.
(f) test_f_no_new_try_after_the_call_deadline (fake clock jumps past WRITE_DEADLINE_SECONDS inside the try: exactly 1 try) + test_f_busy_tries_within_the_deadline_are_all_used (3 tries). Kills O06. No sleeps; time.monotonic is the FakeClock.
(g) test_g_a_stage_at_the_same_rank_does_not_move (lead already at after_followup's rank, changed_at=5 stays, wait kept): kills O12 (`<` -> `<=`). test_g_a_sent_result_clears_the_last_error (old 'old' + passed 'ignored' -> NULL): kills O14.
(d fixed) nits 2/3: expected line is f"desk listening on http://{HOST}:4321" (HOST from tests/support.py); the dead DESK_PORT env var is gone.
All four were small and deterministic, so none is listed as "not pinned".

## Mutants (evidence-p2v23-1; runner evidence-p2v23-mutant-runner.py: reviewer's M01..M26 + O01..O26 list, only the new file is run, on a COPY of the tree, source restored after each)
Reviewer's 5 survivors now: O03 KILLED (test_e), O06 KILLED (test_f), O12 KILLED (test_g), O14 KILLED (test_g), O21 KILLED (test_e). The 7 M mutants still all KILLED; O01..O26 only O13, O15, O17, O24, O25 survive this file (see above). New tests on the real code: 18 passed.

## Gates (fresh clone at 26ca762 + v2.2 + v2.3)
- Stability (evidence-p2v23-2): 30 runs idle 0 failures; 30 runs with 6 busy loops on 4 cores 0 failures (loops killed by PID); DESK_BIND=127.0.0.2: 18 passed.
- evidence-p2v23-3: after `git add -A`, DPLD_REQUIRE_SCAN=1 + gitleaks 8.30.1: test_hygiene, test_codeant_hygiene, test_sonar_p2_choke_points, test_sonar_p2_gaps = 58 passed, 0 skipped; `gitleaks git --staged`: no leaks; plus test_mirror_gate 29 passed with the gaps file; mypy linux and win32 clean (27 files).
- evidence-p2v23-4: ruff check and ruff format --check (152 files) clean.
- Literals: the only http text is f"desk listening on http://{HOST}:4321": starts with "desk" and sits in a test file (same three S5332 reasons as rv30); the repo's literal scan (in test_hygiene) passed. No suppression comments added.

## Rung table (R448)
| component | need | rung tried | verdict |
| 6 tests + 1 line edit | kill the 5 reader survivors, close nits 2/3 | existing helpers (_mid_send, FakeClock, caplog, monkeypatch of Desk._write / _locked_retry) | KEEP-CODE (tests only, no new helper) |
Sonar: tests only, no issue expected to change.
