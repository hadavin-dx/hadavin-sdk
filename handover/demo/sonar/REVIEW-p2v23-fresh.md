# rv35: independent review of sonar-p2-regex-http-bug-v2.3-delta.patch (test-only, tests/test_sonar_p2_gaps.py, 12 -> 18 tests)
Fresh clone of the public repo at 26ca762 + v2.2 delta + v2.3 delta, scratch /tmp/work/rv35-1 (base/, mutdir/, mx/). No pushes, no network writes, made-up data. Preamble rules used: 5, 6, 7, 8, 12, 19, 20. Not run: full suite, Sonar, Windows, Python 3.12 (3.13 venv /tmp/work/civenv), EGM skills.

## Verdict: P2 v2.3 CLEAN (no Blocker, no Major; 3 Nits)

## Failures first
- None in the delta.
- Found while mutating (NOT the delta, pre-existing): tests/test_later_approval.py::test_resolve_413_drains_the_unread_body_like_post_leads fails 3 of 15 runs on an idle machine on the clean tree (`assert [] == [70000]`, a real-socket race). It also made my first wide runs report two false "kills" (P03, P07); I re-ran with the test deselected and corrected the table below. The repo already has sonar/flaky413-fix.patch for it (not evaluated here).
- Own slip: my first wide-mutant run ran while other pytest jobs of mine were running; the false kills above came from that. Re-run done alone.

## Claims about desk.py (read at 26ca762, src/lead_desk/desk.py, db.py): all TRUE
- desk.py:163 `class _GateBusy(sqlite3.OperationalError)`; raised at :430 with text "database is locked (write gate wait ran out)"; db.is_busy (db.py:107) is True for it (message contains "database is locked").
- `_locked_retry` (:443-460): deadline = monotonic()+WRITE_DEADLINE_SECONDS set once per call; loop `range(LOCK_RETRIES)` (constants.py:47, = 3); re-raises at once if not busy, or `_GateBusy`, or last attempt; also raises when monotonic() >= call_deadline. So 1 try for _GateBusy, 3 for a plain busy error, 1 try when the clock passes the deadline inside the first try.
- `_finish_with` (:2154): catches OperationalError, if is_busy logs exactly `"%s: database stayed locked; the row stays as it was and shows as stalled"` and returns None; `_finish_update_moved` returns False for None. Warning "expected one row, changed %d" only after a result.
- `_mark_contacted` (:2090) uses `step_rank < ?` (so same rank is not moved); `_record_send_result` writes `None if state == "sent" else last_error` (a sent result clears last_error).

## Determinism
- 18 passed on the real code.
- 30 runs idle: 0 failures. 30 runs with 6 busy loops (bash `while :`, killed by PID) on 4 cores: 0 failures. DESK_BIND=127.0.0.2 and DESK_BIND=::1: 18 passed each.
- No sleep, thread or socket in the file (grep: no matches for sleep/thread/socket/time.). Clock is FakeClock (time.monotonic and time.sleep patched); the deadline test jumps `clock.now`.
- No-socket proof: autouse fixture raising on socket.socket.__init__, create_connection, getaddrinfo (plugin /tmp/work/rv30-main/m/nosock.py, copy /tmp/work/rv35-1/nosock.py) loaded with `-p nosock`: 18 passed.

## Mutants (runner /tmp/work/rv35-1/mut35.py = rv30's mut30.py pointed at my clone; kill set = only the new file; raw: /tmp/work/rv35-1/mutres.txt)
The five asked: O21 KILLED (test_e, 1 failing case), O03 KILLED (test_e, 2 cases), O06 KILLED (test_f_no_new_try_after_the_call_deadline), O12 KILLED (test_g_a_stage_at_the_same_rank_does_not_move), O14 KILLED (test_g_a_sent_result_clears_the_last_error).
The seven v2.2 mutants: M01 (8 failing), M04 (3), M06 (2), M08 (2), M09 (1), M10 (1), M26 (1) all still KILLED.
Rest of O01..O26: killed except O13, O15, O17, O24, O25 (survive this file; the notes say the existing repo tests kill them; I did not re-verify these five).

Own 24 new mutants P01-P24 of the send/result path (runner /tmp/work/rv35-1/mutP.py, raw mutPres.txt; survivors re-run against 17 repo test files, runner mutW.py, raw mutWres.txt):
| mutant | file alone | wider repo tests |
| P04 _mark_contacted rowcount >= 0 | KILLED (test_g same rank) | |
| P05 step_rank +1 | KILLED | |
| P13 call deadline = now | KILLED (test_e, test_f within) | |
| P15 stayed-locked log at info | KILLED | |
| P16 swallow every OperationalError | KILLED (test b) | |
| P21 sent always frees wait | KILLED | |
| P22 GateBusy retried | KILLED | |
| P24 log text changed | KILLED | |
| P02 crm_tries kept | survived | KILLED (test_a_new_stage_after_the_follow_up_is_copied_at_once...) |
| P06 changed_at not set | survived | KILLED (test_contacted_and_sent_same_transaction) |
| P07 WHERE allows pending | survived | KILLED (test_late_result_leaves_put_back_row) |
| P08 sent_at never set | survived | KILLED (test_sent_sets_time_and_clears_error) |
| P09 ambiguous always 1 | survived | KILLED (test_retry_twice_concurrent) |
| P10 updated_at 0 | survived | KILLED (test_backoff_is_waited) |
| P11 last_error dropped on failure | survived | KILLED (test_model_error_is_one_try_each) |
| P17 gate wait max not min | survived | KILLED (test_a_gate_wait_that_ran_out_is_not_queued_again) |
| P18 pending_or_failed <= | survived | KILLED (test_model_error_is_one_try_each) |
| P19 send: ambiguous flag dropped | survived | KILLED (test_blind_send_timeout_is_unknown) |
| P01 _mark_contacted: flow None -> True | survived | survived (needs a desk without leadflow; that is outside this file; Nit) |
| P03 crm_error kept on stage move | survived | survived (Nit) |
| P20 retry not limited to auto | survived | survived (Nit; send path, not this file) |
| P12 deadline `>` instead of `>=` | survived | not run (edge of equality with a float clock; practically equivalent) |
| P14 call_deadline not cleared in finally | survived | not run (every call resets it; equivalent for this path) |
| P23 range(LOCK_RETRIES+1) | survived | EQUIVALENT (the `attempt == LOCK_RETRIES - 1` guard still raises at try 3) |
Result: of 24, 8 die in the new file, 10 more die in existing repo tests, P01/P03/P20 survive everything I ran (the file's job is the result record, not those lines), P12/P14 not pursued, P23 equivalent. The 17 repo files run (about 170 s, 503 passed clean) are a subset (list in /tmp/work/rv35-1/wide.txt), not the full suite.

## Apply
- 26ca762 + v2.2 + v2.3: both `git apply --check` and apply OK. v2.3 cannot go before v2.2 (it edits the v2.2 file; alone on 26ca762 it fails).
- db54e13 + P1 v3.2 + P2 v2.1 + P3 v3 + v2.2 + v2.3: all apply, 18 passed.
- Whole handover/demo tree: `grep -l test_sonar_p2_gaps` over all 150+ .patch files: ONLY the v2.2 and v2.3 deltas touch the file. For each other patch P (every .patch under /tmp/demo-lead/handover/demo, matrix /tmp/work/rv35-1/matrix26.txt): on 26ca762, "D22 D23 then P" and "P then D22 D23" agree for every patch that applies alone; no patch that applies alone fails because of the deltas. 60 random orders (seeded) of 6 series patches (P3 v3, flaky413, P1 v3.2.2 delta, nodemo-ci-job v3, nodemo-optional-hygiene v4, p2-feed-optional) with D22 and D23 inserted at random positions (D22 before D23): 0 delta-caused failures, 0 series-only failures. The evidence-p2v23-5 matrix "fail at P1" lines are P1 v3.2 already inside 26ca762 (not the delta), as the notes say.

## Literals / hygiene
- The only http text added: `f"desk listening on http://{HOST}:4321"` (line 227); HOST = Config().bind (tests/support.py:35), the f-string element begins with "desk listening on", so a starts-with S5332 check cannot match; also a test file (tests/ and test_ prefix; sonar.test.inclusions). rv30's three reasons stand; I did not re-fetch the Sonar source this time. No other URL or secret-like literal.
- After `git add -A`: DPLD_REQUIRE_SCAN=1 with gitleaks 8.30.1 on PATH: test_hygiene + test_codeant_hygiene + test_sonar_p2_choke_points + test_sonar_p2_gaps: 58 passed, 0 skipped (-rs). `gitleaks git --staged`: no leaks; `gitleaks dir` on the file: no leaks. No git stash used in that clone.
- ruff check: clean; ruff format --check: 152 files already formatted; mypy --platform linux and win32: no issues in 27 source files. No suppression comments added (grep the patch: none).

## Nits
1. The new file cannot detect P01 (a desk with no leadflow), P03 (crm_error kept) or P20 (send path retry flag); optional, outside the file's stated scope.
2. test_e relies on FakeClock (from _mid_send) for "3 tries"; correct, but the 3-try assertion would depend on real time if someone moved the test off _mid_send. Fine as written.
3. The new docstring header says "behaviours ... that no test pinned down" while the module docstring still lists "four behaviours" in the text after it; wording only (the first line was changed, the rest still names four). Cosmetic.

## Housekeeping
All processes I started (busy loops, runners) are stopped; the mutation runs restored source after each mutant (git diff in base/ and mutdir/ is empty). Tokens: not measured.

P2 v2.3 CLEAN
