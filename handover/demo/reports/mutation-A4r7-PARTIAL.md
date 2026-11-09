# MUT7 report: ORDER 225 mutation round on tree A4r7 (/tmp/dpld-s9) - PARTIAL RUN

Evidence runner output (records, does not judge). **This is a PARTIAL run**: stopped on lead order ORDER 226 after mutant 65 of 104. Mutants 66-104 were NOT run (39 mutants), including all 23 NEW mutants (N1-N23, ids 82-104) and the second phase (slow load tests for survivors).

## What was not run / what failed (first)

- NOT RUN: mutants 66-104 (39): round-2 #66-#81 (16 mutants) and all 23 new mutants for S1g/S1h/S1i code (ids 82-104). Mutant 66 was started and then killed by me mid-run on the stop order; its result is discarded and not counted; `db.py` was restored and verified (filecmp True).
- NOT RUN: phase 2 (the 3 slow load tests for survivors). Survivor status below is "survived the fast selection" only.
- The 20 new mutants required by the order are written (N1-N23 in /tmp/mut7-tools/new_mutants.py, all texts verified to occur exactly once in A4r7) but have no result.
- No hangs/timeouts, no invalid mutants in the 65 run.

## Counts (mutants 1-65 only)

- Total round-2 mutants considered so far: 65; applied (run): 62; killed: 61; survived: 1; timeout: 0; invalid: 0; not applicable: 3; not run: 39 (66-104).

## Setup

- Tree /tmp/mut7 (mutated), /tmp/mut7-pristine (pristine), both copies of /tmp/dpld-s9 (without .git and caches). Tools /tmp/mut7-tools (mut_run.py, mutants.py, extra_mutants.py, new_mutants.py, results.json, baseline.log, run.log).
- Selection: tests/test_mutation_guards.py first, then every other tests/test_*.py except test_hygiene.py (which has 2 known failures), 3 slow load tests deselected (test_f9_burst_distinct_emails, test_f13_startup_50_pending, test_f13_startup_fast_reaper_sends), `-x`, 600 s timeout per mutant. Round 2 selected 14 named files; this run adds the new files (test_loss_path_s1g/h/i, test_mutants_round2, test_stall_eviction, test_reaper_start_stop, test_server_main_reaper, test_ai_after_claim). PYTHONDONTWRITEBYTECODE=1, PYTHONPATH=src:tests:., /tmp/dpld-venv/bin/python, no cloud env vars.
- Baseline on the pristine A4r7 tree, same selection, no -x: rc 0, no failing test, 282 s (/tmp/mut7-tools/baseline.log). No known-red tests, so any failing test = kill.
- Import check per mutant imports lead_desk.desk, db, identity and server.
- Ports: round-2 #22, #23, #24, #35 had their text changed in A4r7 and were ported (new text in table). Not applicable: #20, #41, #47 (run so far); #79 (E12) is also not applicable (ids 79 not reached in the run, reason recorded in new_mutants.py).

## Not applicable (record, not judgement)

- #20 (reaper requeue age boundary <= -> <): old text `"WHERE state='sending' AND (? IS NULL OR updated_at <= ?)"` -> mutant text `"WHERE state='sending' AND (? IS NULL OR updated_at < ?)"`. Reason: Old pristine text `updated_at <= ?` is now `updated_at < ?` (S1h made the boundary strict). The old mutant's new text (`updated_at < ?`) IS the A4r7 pristine text, so applying it changes nothing. Its reverse (`<=`) is new mutant N2.
- #41 (give-back of a claim ignores send_started): old text `'WHERE state=\'sending\' AND lead_id=? AND attempts=? AND send_started=0"'` -> mutant text `'WHERE state=\'sending\' AND lead_id=? AND attempts=?"'`. Reason: Old text `... AND attempts=? AND send_started=0` (give-back guarded by send_started=0) no longer exists: `_give_back` now SETS `send_started=0` in the UPDATE and is guarded only by `state='sending' AND lead_id=? AND attempts=?`. Nearest new mutants: N10, N12.
- #47 (defer_pending cap boundary >= -> >): old text `"WHEN auto_attempts+1 >= ? THEN 'failed'"` -> mutant text `"WHEN auto_attempts+1 > ? THEN 'failed'"`. Reason: `defer_pending` (cap boundary `auto_attempts+1 >= ?`) no longer exists in A4r7; it was replaced by `_give_back` (`auto_attempts=MAX(auto_attempts-1, 0)`). Nearest new mutants: N11.
- #79 (E12 (T1 extra)): old text `'" WHERE lead_id=? AND state=\'pending\' AND auto_attempts=?"'` -> mutant text `'" WHERE lead_id=? AND state=\'pending\' AND auto_attempts>=?"'`. Reason: E12 old text `WHERE lead_id=? AND state='pending' AND auto_attempts=?` (defer_pending's guard) no longer exists; `_give_back` guards with `state='sending' AND lead_id=? AND attempts=?`. Nearest new mutant: N10.

## Table (mutants 1-65)

| n | label | file:line | mutation (truncated) | result | first failing test | seconds |
|---|---|---|---|---|---|---|
| 1 | dedupe lookup by raw email instead of email_key | src/lead_desk/desk.py:662 | `"SELECT lead_id FROM leads WHERE email_key=?"` -> `"SELECT lead_id FROM leads WHERE email=?"` | KILLED | tests/test_flow.py::test_cross_source_dupe | 2.1 |
| 2 | email_key normalisation drops lower-casing | src/lead_desk/identity.py:39 | `return s.strip().lower()` -> `return s.strip()` | KILLED | tests/test_flow.py::test_cross_source_dupe | 2.6 |
| 3 | email_key normalisation drops strip | src/lead_desk/identity.py:39 | `return s.strip().lower()` -> `return s.lower()` | KILLED | tests/test_mutants_round2.py::test_email_key_strips_blanks | 99.6 |
| 4 | unique index on email_key made non-unique | src/lead_desk/schema.sql:41 | `CREATE UNIQUE INDEX IF NOT EXISTS leads_email_key_uq` -> `CREATE INDEX IF NOT EXISTS leads_email_key_uq` | KILLED | tests/test_mutation_guards.py::test_email_key_unique_in_sql | 1.4 |
| 5 | outcome-once trigger never fires | src/lead_desk/schema.sql:24 | `WHEN OLD.outcome IS NOT NULL   BEGIN SELECT RAISE(ABORT,'a verdict is ` -> `WHEN OLD.outcome IS NULL AND 0   BEGIN SELECT RAISE(ABORT,'a verdict i` | KILLED | tests/test_flow.py::test_write_once_triggers | 2.8 |
| 6 | receipt-immutable trigger no longer guards payload | src/lead_desk/schema.sql:20 | `received_at, payload ON receipts` -> `received_at ON receipts` | KILLED | tests/test_flow.py::test_write_once_triggers | 2.9 |
| 7 | receipts no-delete trigger disabled | src/lead_desk/schema.sql:27 | `BEFORE DELETE ON receipts   BEGIN` -> `BEFORE DELETE ON receipts WHEN 0   BEGIN` | KILLED | tests/test_flow.py::test_write_once_triggers | 3.1 |
| 8 | sent-final trigger disabled | src/lead_desk/schema.sql:62 | `WHEN OLD.state = 'sent'   BEGIN` -> `WHEN OLD.state = 'sentx'   BEGIN` | KILLED | tests/test_flow.py::test_write_once_triggers | 2.8 |
| 9 | leads no-update trigger disabled | src/lead_desk/schema.sql:43 | `BEFORE UPDATE ON leads   BEGIN` -> `BEFORE UPDATE ON leads WHEN 0   BEGIN` | KILLED | tests/test_flow.py::test_write_once_triggers | 3.1 |
| 10 | receipt uniqueness ignores source | src/lead_desk/schema.sql:17 | `UNIQUE (source, source_ref)` -> `UNIQUE (source_ref)` | KILLED | tests/test_mutation_guards.py::test_email_key_race_only_index | 1.4 |
| 11 | schema source_ref length bound 128 -> 127 | src/lead_desk/schema.sql:7 | `CHECK (length(source_ref) BETWEEN 1 AND 128)` -> `CHECK (length(source_ref) BETWEEN 1 AND 127)` | KILLED | tests/test_mutation_guards.py::test_source_ref_bounds_in_sql | 1.3 |
| 12 | envelope min length boundary <= -> < | src/lead_desk/desk.py:798 | `SOURCE_REF_MIN <= len(source_ref) <= SOURCE_REF_MAX` -> `SOURCE_REF_MIN < len(source_ref) <= SOURCE_REF_MAX` | KILLED | tests/test_mutation_guards.py::test_source_ref_one_char_and_empty | 1.6 |
| 13 | automatic claim no longer clears send_started | src/lead_desk/desk.py:114 | `("pending",): (         "UPDATE followups SET state='sending', attempt` -> `("pending",): (         "UPDATE followups SET state='sending', attempt` | KILLED | tests/test_mutation_guards.py::test_claim_clears_send_started[states0-pending] | 1.6 |
| 14 | automatic claim has no state precondition | src/lead_desk/desk.py:117 | `" WHERE lead_id=? AND state = 'pending'"` -> `" WHERE lead_id=?"` | KILLED | tests/test_mutation_guards.py::test_claim_needs_the_right_state[sending-states0] | 1.6 |
| 15 | Retry claim also takes unknown rows | src/lead_desk/desk.py:122 | `AND state IN ('pending','failed')"` -> `AND state IN ('pending','failed','unknown')"` | KILLED | tests/test_mutation_guards.py::test_claim_needs_the_right_state[unknown-states1] | 1.6 |
| 16 | Retry of a failed row no longer restarts the auto count | src/lead_desk/desk.py:121 | `THEN 1 ELSE auto_attempts+1 END, updated_at=?"         " WHERE lead_id` -> `THEN auto_attempts+1 ELSE auto_attempts+1 END, updated_at=?"         "` | KILLED | tests/test_mutation_guards.py::test_claim_clears_send_started[states2-failed] | 1.6 |
| 17 | requeue cap boundary >= -> > | src/lead_desk/desk.py:420 | `(crm_done <> 1 OR send_started = 0) AND auto_attempts >= ? THEN 'faile` -> `(crm_done <> 1 OR send_started = 0) AND auto_attempts > ? THEN 'failed` | KILLED | tests/test_hardening_cloud_b.py::test_h7_requeue_at_the_cap_fails | 66.5 |
| 18 | requeue no longer sets ambiguous_prior | src/lead_desk/desk.py:424 | `AND send_started = 1 THEN 1 ELSE ambiguous_prior END` -> `AND send_started = 1 THEN 0 ELSE ambiguous_prior END` | KILLED | tests/test_mutation_guards.py::test_requeue_marks_only_started_sends | 1.5 |
| 19 | requeue keyed/blind decision inverted | src/lead_desk/desk.py:422 | `WHEN NOT ? THEN 'unknown' WHEN auto_attempts` -> `WHEN ? THEN 'unknown' WHEN auto_attempts` | KILLED | tests/test_mutation_guards.py::test_requeue_marks_only_started_sends | 1.6 |
| 20 | reaper requeue age boundary <= -> < | src/lead_desk/desk.py:0 | old `WHERE state='sending' AND (? IS NULL OR updated_at <= ?)` -> `WHERE state='sending' AND (? IS NULL OR updated_at < ?)` | NOT APPLICABLE | Old pristine text `updated_at <= ?` is now `updated_at < ?` (S1h made the boundary strict). The old mutant's new text (`updated_at < ?`) IS the A4r7 pristine text, so applying it changes nothing. Its reverse (`<=`) is new mutant N | 0 |
| 21 | reaper stalled-receipt boundary <= -> < | src/lead_desk/desk.py:557 | `"SELECT receipt_id FROM receipts WHERE outcome IS NULL AND received_at` -> `"SELECT receipt_id FROM receipts WHERE outcome IS NULL AND received_at` | KILLED | tests/test_mutation_guards.py::test_stalled_receipt_age_boundary | 1.8 |
| 22 | reaper stuck-sending grace dropped (ported: now the stuck_grace_seconds property) | src/lead_desk/desk.py:273 | `return int(self.config.send_timeout_seconds + SENDING_GRACE_BUSY_WAITS` -> `return int(self.config.send_timeout_seconds + 0 * BUSY_WAIT_SECONDS)` | KILLED | tests/test_mutation_guards.py::test_requeue_age_boundary_in_reaper | 1.5 |
| 23 | reaper due-time boundary <= -> < (ported) | src/lead_desk/desk.py:590 | `if updated_at + wait_before_drive(int(tries), last_error) <= now:` -> `if updated_at + wait_before_drive(int(tries), last_error) < now:` | KILLED | tests/test_hardening_cloud.py::test_f6_backoff_is_waited | 9.3 |
| 24 | reaper backoff skipped after first retry (ported: now gate.wait_before_drive) | src/lead_desk/gate.py:58 | `return PENDING_GRACE_SECONDS if auto_attempts == 0 else backoff_after(` -> `return PENDING_GRACE_SECONDS if auto_attempts <= 1 else backoff_after(` | KILLED | tests/test_hardening_cloud.py::test_f6_backoff_is_waited | 9.4 |
| 25 | reaper blind/keyed check for ambiguous_prior inverted | src/lead_desk/desk.py:596 | `if ambiguous_prior and self.outbox.capability == "blind":` -> `if ambiguous_prior and self.outbox.capability == "keyed":` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 1.8 |
| 26 | reaper ignores receipts stamped in the future | src/lead_desk/desk.py:560 | `] + self._stalled_by_own_clock(conn, now)` -> `]` | KILLED | tests/test_mutation_guards.py::test_future_receipt_by_own_clock | 1.7 |
| 27 | write transaction BEGIN IMMEDIATE -> deferred BEGIN | src/lead_desk/desk.py:297 | `conn.execute("BEGIN IMMEDIATE")` -> `conn.execute("BEGIN")` | KILLED | tests/test_hardening_cloud_b.py::test_f3_decision_write_retries_7s | 42.9 |
| 28 | write transaction never commits | src/lead_desk/desk.py:300 | `conn.execute("COMMIT")` -> `pass` | KILLED | tests/test_mutation_guards.py::test_email_key_race_only_index | 11.4 |
| 29 | duplicate diff ignores the phone field | src/lead_desk/desk.py:735 | `"phone": chk.phone, "company"` -> `"phone": None, "company"` | KILLED | tests/test_flow.py::test_cross_source_dupe | 2.1 |
| 30 | payload_matches inverted | src/lead_desk/desk.py:865 | `matches = rec["payload"] == canon` -> `matches = rec["payload"] != canon` | KILLED | tests/test_flow.py::test_replay_same_source_ref | 2.4 |
| 31 | payload conflict never recorded | src/lead_desk/desk.py:868 | `elif not matches:                 self._note_payload_conflict(rid)` -> `elif False:                 self._note_payload_conflict(rid)` | KILLED | tests/test_hardening_cloud.py::test_f12_replay_with_different_payload | 31.2 |
| 32 | created flag boundary == 1 -> <= 2 | src/lead_desk/desk.py:859 | `return int(found[0]), found[1] == 1` -> `return int(found[0]), found[1] <= 2` | KILLED | tests/test_hardening_cloud.py::test_f12_replay_with_different_payload | 31.4 |
| 33 | duplicate answered 201 instead of 200 | src/lead_desk/desk.py:777 | `status = HTTP_OK             body.update(                 verdict="dup` -> `status = HTTP_CREATED             body.update(                 verdict` | KILLED | tests/test_flow.py::test_cross_source_dupe | 2.3 |
| 34 | review verdict answered 200 instead of 202 | src/lead_desk/desk.py:784 | `status = HTTP_ACCEPTED` -> `status = HTTP_OK` | KILLED | tests/test_mutation_guards.py::test_email_key_race_only_index | 1.4 |
| 35 | replay due-time boundary <= -> < (ported) | src/lead_desk/desk.py:919 | `return bool(row[1] == 0 or row[2] + wait_before_drive(int(row[1]), row` -> `return bool(row[1] == 0 or row[2] + wait_before_drive(int(row[1]), row` | KILLED | tests/test_mutants_round2.py::test_replay_due_exactly_at_pause_end | 99.7 |
| 36 | crm leftover-intent rule inverted | src/lead_desk/desk.py:998 | `if crm_done == CRM_STARTED and not keyed:` -> `if crm_done == CRM_STARTED and keyed:` | KILLED | tests/test_hardening_cloud_b.py::test_g2_blind_crm_not_asked_twice | 65.8 |
| 37 | crm nothing_stored handling inverted | src/lead_desk/desk.py:1024 | `if getattr(e, "nothing_stored", False):` -> `if not getattr(e, "nothing_stored", False):` | KILLED | tests/test_mutation_guards.py::test_proven_failed_put_resets_the_mark | 1.7 |
| 38 | crm mark ownership token compare = -> >= | src/lead_desk/desk.py:1054 | `lead_id=? AND attempts=?",                     (value,` -> `lead_id=? AND attempts>=?",                     (value,` | KILLED | tests/test_hardening_cloud_e.py::test_token_stale_mark_crm_writes_nothing | 70.0 |
| 39 | touch no longer writes the send_started mark | src/lead_desk/desk.py:1078 | `send_started=CASE WHEN ? THEN 1 ELSE send_started END` -> `send_started=CASE WHEN ? THEN 0 ELSE send_started END` | KILLED | tests/test_mutation_guards.py::test_touch_only_for_the_owner | 1.8 |
| 40 | send_started intent mark not requested before send | src/lead_desk/desk.py:1283 | `if not self._touch(lead_id, token, send_started=True):` -> `if not self._touch(lead_id, token, send_started=False):` | KILLED | tests/test_flow.py::test_crash_resume_each_point[D2-blind] | 3.3 |
| 41 | give-back of a claim ignores send_started | src/lead_desk/desk.py:0 | old `WHERE state='sending' AND lead_id=? AND attempts=? AND send_started=0"` -> `WHERE state='sending' AND lead_id=? AND attempts=?"` | NOT APPLICABLE | Old text `... AND attempts=? AND send_started=0` (give-back guarded by send_started=0) no longer exists: `_give_back` now SETS `send_started=0` in the UPDATE and is guarded only by `state='sending' AND lead_id=? AND attempts=?`. N | 0 |
| 42 | busy give-back no longer returns the try | src/lead_desk/desk.py:1168 | `auto_attempts=MAX(auto_attempts-1, 0)` -> `auto_attempts=auto_attempts` | KILLED | tests/test_hardening_cloud_d.py::test_l1n3_busy_after_the_claim_gives_th | 68.2 |
| 43 | retry cap boundary < -> <= | src/lead_desk/desk.py:1241 | `return "pending" if self._auto_attempts(lead_id) < SEND_MAX_ATTEMPTS e` -> `return "pending" if self._auto_attempts(lead_id) <= SEND_MAX_ATTEMPTS ` | KILLED | tests/test_mutation_guards.py::test_abort_unsent_counts_one_try | 1.7 |
| 44 | ambiguous send no longer retried on keyed | src/lead_desk/desk.py:1314 | `err in _RETRYABLE:` -> `err in ("refused", "unreachable"):` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 1.7 |
| 45 | ambiguous send keyed/blind outcome swapped | src/lead_desk/desk.py:1313 | `state = "failed" if self.outbox.capability == "keyed" else "unknown"` -> `state = "failed" if self.outbox.capability == "blind" else "unknown"` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 1.8 |
| 46 | ambiguous_prior send guard inverted | src/lead_desk/desk.py:1279 | `if self.outbox.capability == "blind":                     self._record` -> `if self.outbox.capability == "keyed":                     self._record` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 1.5 |
| 47 | defer_pending cap boundary >= -> > | src/lead_desk/desk.py:0 | old `WHEN auto_attempts+1 >= ? THEN 'failed'` -> `WHEN auto_attempts+1 > ? THEN 'failed'` | NOT APPLICABLE | `defer_pending` (cap boundary `auto_attempts+1 >= ?`) no longer exists in A4r7; it was replaced by `_give_back` (`auto_attempts=MAX(auto_attempts-1, 0)`). Nearest new mutants: N11. | 0 |
| 48 | sent result keeps the old last_error | src/lead_desk/desk.py:1342 | `None if state == "sent" else last_error,` -> `last_error,` | SURVIVED |  | 280.6 |
| 49 | sent_at set for non-sent results | src/lead_desk/desk.py:1344 | `now if state == "sent" else None,` -> `now,` | KILLED | tests/test_mutants_round2.py::test_sent_sets_time_and_clears_error | 100.1 |
| 50 | result record ignores the sending state | src/lead_desk/desk.py:1339 | `WHERE lead_id=? AND attempts=? AND state='sending'"` -> `WHERE lead_id=? AND attempts=?"` | KILLED | tests/test_mutants_round2.py::test_late_result_leaves_put_back_row | 100.0 |
| 51 | item id with leading zero accepted | src/lead_desk/desk.py:1375 | `or len(ref) > MAX_DIGITS or ref[0] == "0":` -> `or len(ref) > MAX_DIGITS:` | KILLED | tests/test_hardening_cloud_d.py::test_l3n3_r1_is_found_but_r01_is_not | 68.9 |
| 52 | retry busy answered 409 instead of 503 | src/lead_desk/desk.py:1422 | `return Reply(HTTP_BUSY, {"error": "busy"})` -> `return Reply(HTTP_CONFLICT, {"error": "busy"})` | KILLED | tests/test_mutants_round2.py::test_retry_busy_is_503[pending] | 100.5 |
| 53 | retry of sent row reports in_progress | src/lead_desk/desk.py:1416 | `"sent": "not_retryable"` -> `"sent": "in_progress"` | KILLED | tests/test_flow.py::test_failed_retry | 3.5 |
| 54 | resolve crm_present fits crm_done 1 instead of 2 | src/lead_desk/desk.py:1468 | `" AND (? = 0 OR crm_done = 2)"` -> `" AND (? = 0 OR crm_done = 1)"` | KILLED | tests/test_hardening_cloud_b.py::test_h4_crm_present_then_send | 66.4 |
| 55 | resolve sent fits crm_done 2 instead of 1 | src/lead_desk/desk.py:1469 | `" AND (? = 0 OR crm_done = 1)",                         (` -> `" AND (? = 0 OR crm_done = 2)",                         (` | KILLED | tests/test_flow.py::test_unknown_blind | 3.5 |
| 56 | resolve not_sent sets pending (not failed) | src/lead_desk/desk.py:1449 | `"not_sent": ("failed", "person: not sent")` -> `"not_sent": ("pending", "person: not sent")` | KILLED | tests/test_flow.py::test_unknown_blind | 3.2 |
| 57 | resolve undo marks cleared on wrong decision | src/lead_desk/desk.py:1452 | `undo = int(decision == "not_sent")` -> `undo = int(decision == "sent")` | KILLED | tests/test_flow.py::test_unknown_blind | 3.2 |
| 58 | resolve idempotency: also acts on failed rows | src/lead_desk/desk.py:1467 | `WHERE lead_id=? AND state='unknown'"                         " AND (? ` -> `WHERE lead_id=? AND state IN ('unknown','failed')"                    ` | KILLED | tests/test_mutants_round2.py::test_resolve_ignores_failed_row[not_sent] | 100.2 |
| 59 | counts ok ignores unknown follow-ups | src/lead_desk/desk.py:1550 | `and failed == 0 and unknown == 0)` -> `and failed == 0)` | KILLED | tests/test_hardening_cloud.py::test_f10_counts_ok_needs_clean | 31.5 |
| 60 | reconcile expected_match == -> >= | src/lead_desk/desk.py:1546 | `match = None if expected is None else received == expected` -> `match = None if expected is None else received >= expected` | KILLED | tests/test_mutants_round2.py::test_counts_match_needs_equality | 100.2 |
| 61 | decide failure limit boundary < -> <= | src/lead_desk/desk.py:681 | `if failures < DECIDE_FAIL_LIMIT:` -> `if failures <= DECIDE_FAIL_LIMIT:` | KILLED | tests/test_hardening_cloud_b.py::test_h3_poison_receipt_ends_in_review | 66.2 |
| 62 | foreign keys off | src/lead_desk/db.py:74 | `conn.execute("PRAGMA foreign_keys=ON")` -> `conn.execute("PRAGMA foreign_keys=OFF")` | KILLED | tests/test_infra.py::test_connection_pragmas_and_busy_503 | 87.3 |
| 63 | recursive triggers off | src/lead_desk/db.py:75 | `conn.execute("PRAGMA recursive_triggers=ON")` -> `conn.execute("PRAGMA recursive_triggers=OFF")` | KILLED | tests/test_infra.py::test_connection_pragmas_and_busy_503 | 86.8 |
| 64 | synchronous FULL -> OFF | src/lead_desk/db.py:76 | `conn.execute("PRAGMA synchronous=FULL")` -> `conn.execute("PRAGMA synchronous=OFF")` | KILLED | tests/test_infra.py::test_connection_pragmas_and_busy_503 | 83.7 |
| 65 | is_busy ignores SQLITE_LOCKED | src/lead_desk/db.py:88 | `in (SQLITE_BUSY, SQLITE_LOCKED)` -> `in (SQLITE_BUSY,)` | KILLED | tests/test_mutants_round2.py::test_is_busy_takes_both_lock_codes[6] | 99.8 |

## Survivors (survived the fast selection; slow load tests not run), exact mutated text

### #48 sent result keeps the old last_error (src/lead_desk/desk.py:1342)
- old text:
```
None if state == "sent" else last_error,
```
- mutated text:
```
last_error,
```

## Not run

Mutants 66-104: #66 migration backfill sending -> crm_done 1, #67 init_schema accepts user_version 2, #68 E1 (T1 extra), #69 E2 (T1 extra), #70 E3 (T1 extra), #71 E4 (T1 extra), #72 E5 (T1 extra), #73 E6 (T1 extra), #74 E7 (T1 extra), #75 E8 (T1 extra), #76 E9 (T1 extra), #77 E10 (T1 extra), #78 E11 (T1 extra), #79 E12 (T1 extra), #80 E13 (T1 extra), #81 E14 (T1 extra), #82 N1 reaper count query strict boundary < -> <=, #83 N2 _requeue_sending strict boundary < -> <=, #84 N3 validate_model_budget budget+margin >= -> >, #85 N4 validate_model_budget write_deadline+busy_wait >= -> >, #86 N5 DeskSettingRefused adapter limit >= -> >, #87 N6 label write guard drops state='sending', #88 N7 label write guard token = -> >=, #89 N8 re-read after the label write: ownership check skipped, #90 N9 re-read after the label write: stored (first-wins) label not used, #91 N10 _give_back token guard = -> >=, #92 N11 _give_back no longer returns the automatic try, #93 N12 _give_back no longer clears send_started, #94 N13 _give_back keeps a stale no_descriptors last_error, #95 N14 crm_done=2 with CRM down: gives the try back instead of using one, #96 N15 crm_done=2 with CRM down: path never taken, #97 N16 _touch swallows a busy database (returns False, not raise), #98 N17 EMFILE give-back no longer marks no_descriptors, #99 N18 EMFILE before the send is counted as a used try, not given back, #100 N19 server.main nested finally chain flattened, #101 N20 descriptor arithmetic: reserve left out of need, #102 N21 descriptor arithmetic: reserve left out of advice (fits), #103 N22 ensure_descriptor_budget soft >= need -> >, #104 N23 ensure_descriptor_budget no longer re-validates the constants

## Cleanup
- Driver and its test child stopped (the driver was killed on the order; its wrapper shell was killed first so phase 2 never started). `diff -r /tmp/mut7 /tmp/mut7-pristine -x __pycache__` is empty after restoring db.py; filecmp of db.py True. No repo edits, nothing pushed, no /tmp/dpld-*, /tmp/ag trees touched.
- One unrelated pytest process (pid 9294, /root/.local/bin/pytest) was seen running; it is not mine and was left alone.
- R-numbers: none looked up (evidence runner, no design work). EGM: this is an EVIDENCE RUNNER task; no EGM review done by me.
