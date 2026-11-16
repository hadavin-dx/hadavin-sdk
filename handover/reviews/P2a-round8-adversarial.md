# P2a round 8, adversarial review (ticket revision 9, 459 lines)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-design`, read-only, nothing run, did not open `reviews/`. Round 1 of at most 3 under order 16. Cites checked against core ce70eb5 on disk (not the PR #50 snapshot). All SQL and trace reasoning UNVERIFIED.

Verdict: NOT CLEAN. 0 Blocker, 1 Major, 6 Nit.

## MAJOR

**M1. The reset records the wrong person as "who stopped"; the ticket says the opposite (lines 70, 186-209, 211-230, DBA recipe line 235).** Line 70 says `kill_switch_resets.old_by` is NULL for a stop that was only a request. The guard trigger (lines 221-222) writes `NEW."by" := lbl` on every ON to OFF, so after the first reset `kill_switch."by"` holds the resetter's label permanently. The reset function's pre-step (line 203, `UPDATE ... SET "on" = true`) is an OFF to ON update, and the trigger's OFF to ON branch (line 224) leaves `by` untouched. On the normal path (a request-only stop, every reset after the first) the pre-step flips the flag ON with `by` = the previous resetter, then ON to OFF inserts `OLD."by"` into `old_by`: `old_by` names the PREVIOUS RESETTER as the one who stopped, never NULL. The same stale `by` appears in the view (lines 59-61, `k."by"` when `k."on"`) after the DBA recipe `UPDATE kill_switch SET "on" = true` (line 235). This is an audit-attribution defect on a security path; the runbook sends an investigator to `old_by` first. S31 case g asserts only "`old_by` = what was on the flag", so planned evidence would not catch it; no mutant covers it (mut-G9, mut-G11 test other columns). Fix, either shape: the pre-step sets `"by"` from the earliest open stop request, or the trigger's OFF to ON branch sets `NEW."by" := NULL` unless explicitly set; change the DBA recipe to set `"by"` explicitly; add a test (reset twice with request-only stops; second `old_by` is not the first resetter's label), a mutant (pre-step leaves `by` unchanged), and correct line 70.

## NIT

- N1: stale round policy (lines 3, 18, 385, 389) against order 16: say "orders through 16 applied; ticket review rounds limited per order 16"; "two rounds in a row" stays only for RESULT review.
- N2: line 353 test says the raw login name appears nowhere in audit or tables, but `kill_switch_login_labels.login_name` (line 71) stores it by design; say "nowhere except `kill_switch_login_labels`".
- N3: mut-F15 (cap `<=` instead of `<`) names a killer that passes on the mutant (`LIMIT N` bounds the count); re-point to `test_stop_at_cap_adds_no_row` or drop F15 as a duplicate of F13 and recount (174 and 171 change).
- N4: mut-K3 names an existing file with the test name marked UNVERIFIED; mut-ST20 is "killed only if psycopg sends an int8" but its killer is a text assertion; state the text assertion as the killer.
- N5: the missing-row stop returns hard-coded `open_requests` 1 and `by` = `p_by`, not the earliest open request; the planned "view row equals the stop function's return" test fails there. Exempt the case or compute from the table.
- N6: (a) `Limits.reset` step 1 writes the `reset_denied` audit row; the audit-down test at `tests/test_review_pr3_round2.py:278-290` expects exit 5, so say it uses the never-raising `write_outcome` path (else `AuditUnavailable`, exit 3); (b) the livelock runbook revokes EXECUTE on the stop function from the runtime, which also disables automatic meter stops (P4b1) while the operator resets: state the trade-off; (c) reset audit says `reset` even when the view still reads ON (in-flight stop stays open, S31 case i); fails safe; have the CLI print the returned `on`.

## Counts recounted (match the ticket)

Mutants: G 44, F 16, R 19, ST 22, P 21, L 45, K 7, total 174; [catalog] rows 4 (G12, G39, F9, R8), so 170 have a behaviour killer; revision-8 count 159 with 8 removals and 23 additions reconciles. `migrate(` call sites 26; `Limits(` sites 9 (7 test + 2 src); S29-S42 = 14 steps; equivalent rows 6.

## Held

Core cites (`migrate.py` Grant 24, GRANTS 55, `_LOCK` 69, `_ROLE` 70, `_SAFE_CREATE` 80, `_UNREAD` 87, `_scan` 123, `check_grants` 150, `_apply_grants` 169, `effective_problems` 193, `migrate` 283, lock 308-314, `gone` check 320-326; `limits.py` stop 43-46, reset 48; `protocol.py:116`; `0003_approvals_tick.sql` 25-27, 30-35; `tick.py:295-332`). BIGSERIAL sequence registration; empty rights; `test_k2_migrations.py:226-227` `{''}` problem is real; probes P1-P3; S1-S28 cites; the (version, count) race argument; no real-looking secret, `.test` e-mail domain; superuser-in-group trace.

## Not checked

No SQL run; plpgsql compilation, `HD00x` SQLSTATE acceptance, `RETURN QUERY`/`FOUND`, `$` handling, PostgreSQL 17 behaviour; tickets P4d, P3a, P1m, P4b1/2, P4c and cross-ticket cites; `app.py`/`cli.py`/`agent_loop.py` cites and most test-file cites; PR #50 snapshot facts; bible rule numbers; killability of each of the 174 mutants beyond those named.
