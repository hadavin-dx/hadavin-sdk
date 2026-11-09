# Mutation run A4 (order 219), evidence runner output (records, does not judge)

Tree /tmp/ag/mut-a4 (pristine /tmp/ag/mut-a4-pristine), driver /home/user/build/mut2/mut_run.py, raw results /home/user/build/mut2/mut_results.json, logs p1.log p2.log baseline.log.

Counts: mutants 81, valid 81, killed 70, survived 11, invalid 0, timeout 0.

Test selection per mutant: tests/test_mutation_guards.py first, then test_flow, test_mutants, test_hardening, test_infra, test_http, test_server_hardening, test_hardening_cloud(+_b,_c,_d,_e), test_slow_sender, test_portal_api, with -x. Deselected (known red): test_flow::test_failed_retry, test_flow::test_retry_twice_concurrent, test_mutants::test_mutant_no_claim, test_hardening_cloud_b::test_f14_lock_file_unopenable, test_infra::test_demo_adapters; and the 3 slow load tests (run only for survivors in phase 2).

## Baseline failure set
Clean A4 tree, same selection, no -x: rc 0, 0 failures, 233 s (baseline.log). So any failing test counts as a kill.

## All mutants

| n | label | class | file:line | mutation | result | first failing test | seconds |
|---|---|---|---|---|---|---|---|
| 1 | dedupe lookup by raw email instead of email_key | dedupe-key | src/lead_desk/desk.py:583 | `"SELECT lead_id FROM leads WHERE email_key=?"` -> `"SELECT lead_id FROM leads WHERE email=?"` | KILLED | tests/test_flow.py::test_cross_source_dupe | 1.2 |
| 2 | email_key normalisation drops lower-casing | dedupe-key | src/lead_desk/identity.py:39 | `return s.strip().lower()` -> `return s.strip()` | KILLED | tests/test_flow.py::test_cross_source_dupe | 1.3 |
| 3 | email_key normalisation drops strip | dedupe-key | src/lead_desk/identity.py:39 | `return s.strip().lower()` -> `return s.lower()` | SURVIVED |  | 219.3 |
| 4 | unique index on email_key made non-unique | unique-constraint | src/lead_desk/schema.sql:41 | `CREATE UNIQUE INDEX IF NOT EXISTS leads_email_key_uq` -> `CREATE INDEX IF NOT EXISTS leads_email_key_uq` | KILLED | tests/test_mutation_guards.py::test_email_key_unique_in_sql | 0.5 |
| 5 | outcome-once trigger never fires | trigger-write-once | src/lead_desk/schema.sql:24 | `WHEN OLD.outcome IS NOT NULL   BEGIN SELECT RAISE(ABORT,'a verdict is ` -> `WHEN OLD.outcome IS NULL AND 0   BEGIN SELECT RAISE(ABORT,'a verdict i` | KILLED | tests/test_flow.py::test_write_once_triggers | 1.6 |
| 6 | receipt-immutable trigger no longer guards payload | trigger-immutable | src/lead_desk/schema.sql:20 | `received_at, payload ON receipts` -> `received_at ON receipts` | KILLED | tests/test_flow.py::test_write_once_triggers | 1.9 |
| 7 | receipts no-delete trigger disabled | trigger-immutable | src/lead_desk/schema.sql:27 | `BEFORE DELETE ON receipts   BEGIN` -> `BEFORE DELETE ON receipts WHEN 0   BEGIN` | KILLED | tests/test_flow.py::test_write_once_triggers | 1.6 |
| 8 | sent-final trigger disabled | trigger-write-once | src/lead_desk/schema.sql:62 | `WHEN OLD.state = 'sent'   BEGIN` -> `WHEN OLD.state = 'sentx'   BEGIN` | KILLED | tests/test_flow.py::test_write_once_triggers | 1.7 |
| 9 | leads no-update trigger disabled | trigger-immutable | src/lead_desk/schema.sql:43 | `BEFORE UPDATE ON leads   BEGIN` -> `BEFORE UPDATE ON leads WHEN 0   BEGIN` | KILLED | tests/test_flow.py::test_write_once_triggers | 1.7 |
| 10 | receipt uniqueness ignores source | unique-constraint | src/lead_desk/schema.sql:17 | `UNIQUE (source, source_ref)` -> `UNIQUE (source_ref)` | KILLED | tests/test_mutation_guards.py::test_email_key_race_only_index | 0.5 |
| 11 | schema source_ref length bound 128 -> 127 | boundary | src/lead_desk/schema.sql:7 | `CHECK (length(source_ref) BETWEEN 1 AND 128)` -> `CHECK (length(source_ref) BETWEEN 1 AND 127)` | KILLED | tests/test_mutation_guards.py::test_source_ref_bounds_in_sql | 0.7 |
| 12 | envelope min length boundary <= -> < | boundary | src/lead_desk/desk.py:719 | `SOURCE_REF_MIN <= len(source_ref) <= SOURCE_REF_MAX` -> `SOURCE_REF_MIN < len(source_ref) <= SOURCE_REF_MAX` | KILLED | tests/test_mutation_guards.py::test_source_ref_one_char_and_empty | 0.8 |
| 13 | automatic claim no longer clears send_started | claim-lease | src/lead_desk/desk.py:97 | `("pending",): (         "UPDATE followups SET state='sending', attempt` -> `("pending",): (         "UPDATE followups SET state='sending', attempt` | KILLED | tests/test_mutation_guards.py::test_claim_clears_send_started[states0-pending] | 0.6 |
| 14 | automatic claim has no state precondition | claim-lease | src/lead_desk/desk.py:100 | `" WHERE lead_id=? AND state = 'pending'"` -> `" WHERE lead_id=?"` | KILLED | tests/test_mutation_guards.py::test_claim_needs_the_right_state[sending-states0] | 0.7 |
| 15 | Retry claim also takes unknown rows | claim-lease | src/lead_desk/desk.py:105 | `AND state IN ('pending','failed')"` -> `AND state IN ('pending','failed','unknown')"` | KILLED | tests/test_mutation_guards.py::test_claim_needs_the_right_state[unknown-states1] | 0.7 |
| 16 | Retry of a failed row no longer restarts the auto count | retry-rule | src/lead_desk/desk.py:104 | `THEN 1 ELSE auto_attempts+1 END, updated_at=?"         " WHERE lead_id` -> `THEN auto_attempts+1 ELSE auto_attempts+1 END, updated_at=?"         "` | KILLED | tests/test_mutation_guards.py::test_claim_clears_send_started[states2-failed] | 0.7 |
| 17 | requeue cap boundary >= -> > | boundary | src/lead_desk/desk.py:377 | `(crm_done <> 1 OR send_started = 0) AND auto_attempts >= ? THEN 'faile` -> `(crm_done <> 1 OR send_started = 0) AND auto_attempts > ? THEN 'failed` | KILLED | tests/test_hardening_cloud_b.py::test_h7_requeue_at_the_cap_fails | 93.6 |
| 18 | requeue no longer sets ambiguous_prior | ambiguous-mark | src/lead_desk/desk.py:381 | `AND send_started = 1 THEN 1 ELSE ambiguous_prior END` -> `AND send_started = 1 THEN 0 ELSE ambiguous_prior END` | KILLED | tests/test_mutation_guards.py::test_requeue_marks_only_started_sends | 1.0 |
| 19 | requeue keyed/blind decision inverted | requeue-rule | src/lead_desk/desk.py:379 | `WHEN NOT ? THEN 'unknown' WHEN auto_attempts` -> `WHEN ? THEN 'unknown' WHEN auto_attempts` | KILLED | tests/test_mutation_guards.py::test_requeue_marks_only_started_sends | 0.9 |
| 20 | reaper requeue age boundary <= -> < | boundary | src/lead_desk/desk.py:383 | `WHERE state='sending' AND (? IS NULL OR updated_at <= ?)` -> `WHERE state='sending' AND (? IS NULL OR updated_at < ?)` | KILLED | tests/test_mutation_guards.py::test_requeue_age_boundary_direct | 0.8 |
| 21 | reaper stalled-receipt boundary <= -> < | boundary | src/lead_desk/desk.py:479 | `"SELECT receipt_id FROM receipts WHERE outcome IS NULL AND received_at` -> `"SELECT receipt_id FROM receipts WHERE outcome IS NULL AND received_at` | KILLED | tests/test_mutation_guards.py::test_stalled_receipt_age_boundary | 0.8 |
| 22 | reaper stuck-sending grace dropped | reaper | src/lead_desk/desk.py:489 | `stuck_before = now - int(self.config.send_timeout_seconds + SENDING_GR` -> `stuck_before = now - int(self.config.send_timeout_seconds + 0 * BUSY_W` | KILLED | tests/test_mutation_guards.py::test_requeue_age_boundary_in_reaper | 0.9 |
| 23 | reaper due-time boundary <= -> < | boundary | src/lead_desk/desk.py:511 | `if updated_at + wait <= now:` -> `if updated_at + wait < now:` | KILLED | tests/test_hardening_cloud.py::test_f6_backoff_is_waited | 53.1 |
| 24 | reaper backoff skipped after first retry | reaper | src/lead_desk/desk.py:510 | `wait = PENDING_GRACE_SECONDS if tries == 0 else backoff_after(int(trie` -> `wait = PENDING_GRACE_SECONDS if tries <= 1 else backoff_after(int(trie` | KILLED | tests/test_hardening_cloud.py::test_f6_backoff_is_waited | 51.8 |
| 25 | reaper blind/keyed check for ambiguous_prior inverted | ambiguous-mark | src/lead_desk/desk.py:517 | `if ambiguous_prior and self.outbox.capability == "blind":` -> `if ambiguous_prior and self.outbox.capability == "keyed":` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 0.9 |
| 26 | reaper ignores receipts stamped in the future | reaper | src/lead_desk/desk.py:482 | `] + self._stalled_by_own_clock(conn, now)` -> `]` | KILLED | tests/test_mutation_guards.py::test_future_receipt_by_own_clock | 0.8 |
| 27 | write transaction BEGIN IMMEDIATE -> deferred BEGIN | transaction | src/lead_desk/desk.py:262 | `conn.execute("BEGIN IMMEDIATE")` -> `conn.execute("BEGIN")` | KILLED | tests/test_hardening_cloud_b.py::test_f3_decision_write_retries_7s | 70.0 |
| 28 | write transaction never commits | transaction | src/lead_desk/desk.py:265 | `conn.execute("COMMIT")` -> `pass` | KILLED | tests/test_mutation_guards.py::test_email_key_race_only_index | 10.4 |
| 29 | duplicate diff ignores the phone field | differing-fields | src/lead_desk/desk.py:656 | `"phone": chk.phone, "company"` -> `"phone": None, "company"` | KILLED | tests/test_flow.py::test_cross_source_dupe | 0.9 |
| 30 | payload_matches inverted | idempotency | src/lead_desk/desk.py:786 | `matches = rec["payload"] == canon` -> `matches = rec["payload"] != canon` | KILLED | tests/test_flow.py::test_replay_same_source_ref | 1.0 |
| 31 | payload conflict never recorded | idempotency | src/lead_desk/desk.py:789 | `elif not matches:                 self._note_payload_conflict(rid)` -> `elif False:                 self._note_payload_conflict(rid)` | KILLED | tests/test_hardening_cloud.py::test_f12_replay_with_different_payload | 59.2 |
| 32 | created flag boundary == 1 -> <= 2 | boundary | src/lead_desk/desk.py:780 | `return int(found[0]), found[1] == 1` -> `return int(found[0]), found[1] <= 2` | KILLED | tests/test_hardening_cloud.py::test_f12_replay_with_different_payload | 58.0 |
| 33 | duplicate answered 201 instead of 200 | status-code | src/lead_desk/desk.py:698 | `status = HTTP_OK             body.update(                 verdict="dup` -> `status = HTTP_CREATED             body.update(                 verdict` | KILLED | tests/test_flow.py::test_cross_source_dupe | 1.0 |
| 34 | review verdict answered 200 instead of 202 | status-code | src/lead_desk/desk.py:705 | `status = HTTP_ACCEPTED` -> `status = HTTP_OK` | KILLED | tests/test_mutation_guards.py::test_email_key_race_only_index | 0.4 |
| 35 | replay due-time boundary <= -> < | boundary | src/lead_desk/desk.py:838 | `return bool(row[1] == 0 or row[2] + backoff_after(int(row[1])) <= self` -> `return bool(row[1] == 0 or row[2] + backoff_after(int(row[1])) < self.` | SURVIVED |  | 218.1 |
| 36 | crm leftover-intent rule inverted | crm-done | src/lead_desk/desk.py:892 | `if crm_done == CRM_STARTED and not keyed:` -> `if crm_done == CRM_STARTED and keyed:` | KILLED | tests/test_hardening_cloud_b.py::test_g2_blind_crm_not_asked_twice | 94.1 |
| 37 | crm nothing_stored handling inverted | crm-done | src/lead_desk/desk.py:915 | `if getattr(e, "nothing_stored", False):` -> `if not getattr(e, "nothing_stored", False):` | KILLED | tests/test_mutation_guards.py::test_proven_failed_put_resets_the_mark | 0.9 |
| 38 | crm mark ownership token compare = -> >= | claim-lease | src/lead_desk/desk.py:945 | `lead_id=? AND attempts=?",                     (value,` -> `lead_id=? AND attempts>=?",                     (value,` | KILLED | tests/test_hardening_cloud_e.py::test_token_stale_mark_crm_writes_nothing | 96.7 |
| 39 | touch no longer writes the send_started mark | send-started | src/lead_desk/desk.py:967 | `send_started=CASE WHEN ? THEN 1 ELSE send_started END` -> `send_started=CASE WHEN ? THEN 0 ELSE send_started END` | KILLED | tests/test_mutation_guards.py::test_touch_only_for_the_owner | 0.8 |
| 40 | send_started intent mark not requested before send | send-started | src/lead_desk/desk.py:1157 | `if not self._touch(lead_id, token, send_started=True):` -> `if not self._touch(lead_id, token, send_started=False):` | KILLED | tests/test_flow.py::test_crash_resume_each_point[D2-blind] | 2.0 |
| 41 | give-back of a claim ignores send_started | send-started | src/lead_desk/desk.py:1053 | `WHERE state='sending' AND lead_id=? AND attempts=? AND send_started=0"` -> `WHERE state='sending' AND lead_id=? AND attempts=?"` | SURVIVED |  | 217.8 |
| 42 | busy give-back no longer returns the try | retry-rule | src/lead_desk/desk.py:1052 | `auto_attempts=MAX(auto_attempts-1, 0)` -> `auto_attempts=auto_attempts` | KILLED | tests/test_hardening_cloud_d.py::test_l1n3_busy_after_the_claim_gives_th | 95.4 |
| 43 | retry cap boundary < -> <= | boundary | src/lead_desk/desk.py:1120 | `return "pending" if self._auto_attempts(lead_id) < SEND_MAX_ATTEMPTS e` -> `return "pending" if self._auto_attempts(lead_id) <= SEND_MAX_ATTEMPTS ` | KILLED | tests/test_hardening_cloud.py::test_f6_failed_only_after_cap | 52.4 |
| 44 | ambiguous send no longer retried on keyed | retry-rule | src/lead_desk/desk.py:1184 | `err in _RETRYABLE:` -> `err in ("refused", "unreachable"):` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 0.9 |
| 45 | ambiguous send keyed/blind outcome swapped | retry-rule | src/lead_desk/desk.py:1183 | `state = "failed" if self.outbox.capability == "keyed" else "unknown"` -> `state = "failed" if self.outbox.capability == "blind" else "unknown"` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 1.0 |
| 46 | ambiguous_prior send guard inverted | ambiguous-mark | src/lead_desk/desk.py:1153 | `if self.outbox.capability == "blind":                     self._record` -> `if self.outbox.capability == "keyed":                     self._record` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 1.0 |
| 47 | defer_pending cap boundary >= -> > | boundary | src/lead_desk/desk.py:1201 | `WHEN auto_attempts+1 >= ? THEN 'failed'` -> `WHEN auto_attempts+1 > ? THEN 'failed'` | KILLED | tests/test_mutation_guards.py::test_defer_pending_counts_one_try | 1.0 |
| 48 | sent result keeps the old last_error | result-record | src/lead_desk/desk.py:1231 | `None if state == "sent" else last_error,` -> `last_error,` | SURVIVED |  | 217.1 |
| 49 | sent_at set for non-sent results | result-record | src/lead_desk/desk.py:1233 | `now if state == "sent" else None,` -> `now,` | SURVIVED |  | 218.4 |
| 50 | result record ignores the sending state | claim-lease | src/lead_desk/desk.py:1228 | `WHERE lead_id=? AND attempts=? AND state='sending'"` -> `WHERE lead_id=? AND attempts=?"` | SURVIVED |  | 219.3 |
| 51 | item id with leading zero accepted | id-grammar | src/lead_desk/desk.py:1264 | `or len(ref) > MAX_DIGITS or ref[0] == "0":` -> `or len(ref) > MAX_DIGITS:` | KILLED | tests/test_hardening_cloud_d.py::test_l3n3_r1_is_found_but_r01_is_not | 97.1 |
| 52 | retry busy answered 409 instead of 503 | status-code | src/lead_desk/desk.py:1310 | `return Reply(HTTP_BUSY, {"error": "busy"})` -> `return Reply(HTTP_CONFLICT, {"error": "busy"})` | SURVIVED |  | 218.9 |
| 53 | retry of sent row reports in_progress | status-code | src/lead_desk/desk.py:1304 | `"sent": "not_retryable"` -> `"sent": "in_progress"` | KILLED | tests/test_http.py::test_review_and_envelope_errors | 22.5 |
| 54 | resolve crm_present fits crm_done 1 instead of 2 | resolve-409 | src/lead_desk/desk.py:1356 | `" AND (? = 0 OR crm_done = 2)"` -> `" AND (? = 0 OR crm_done = 1)"` | KILLED | tests/test_hardening_cloud_b.py::test_h4_crm_present_then_send | 94.9 |
| 55 | resolve sent fits crm_done 2 instead of 1 | resolve-409 | src/lead_desk/desk.py:1357 | `" AND (? = 0 OR crm_done = 1)",                         (` -> `" AND (? = 0 OR crm_done = 2)",                         (` | KILLED | tests/test_flow.py::test_unknown_blind | 1.9 |
| 56 | resolve not_sent sets pending (not failed) | resolve-409 | src/lead_desk/desk.py:1337 | `"not_sent": ("failed", "person: not sent")` -> `"not_sent": ("pending", "person: not sent")` | KILLED | tests/test_flow.py::test_unknown_blind | 2.0 |
| 57 | resolve undo marks cleared on wrong decision | resolve-409 | src/lead_desk/desk.py:1340 | `undo = int(decision == "not_sent")` -> `undo = int(decision == "sent")` | KILLED | tests/test_flow.py::test_unknown_blind | 2.0 |
| 58 | resolve idempotency: also acts on failed rows | resolve-409 | src/lead_desk/desk.py:1355 | `WHERE lead_id=? AND state='unknown'"                         " AND (? ` -> `WHERE lead_id=? AND state IN ('unknown','failed')"                    ` | SURVIVED |  | 218.5 |
| 59 | counts ok ignores unknown follow-ups | reconcile | src/lead_desk/desk.py:1438 | `and failed == 0 and unknown == 0)` -> `and failed == 0)` | KILLED | tests/test_hardening_cloud.py::test_f10_counts_ok_needs_clean | 59.1 |
| 60 | reconcile expected_match == -> >= | reconcile | src/lead_desk/desk.py:1434 | `match = None if expected is None else received == expected` -> `match = None if expected is None else received >= expected` | SURVIVED |  | 220.2 |
| 61 | decide failure limit boundary < -> <= | boundary | src/lead_desk/desk.py:602 | `if failures < DECIDE_FAIL_LIMIT:` -> `if failures <= DECIDE_FAIL_LIMIT:` | KILLED | tests/test_hardening_cloud_b.py::test_h3_poison_receipt_ends_in_review | 93.5 |
| 62 | foreign keys off | db-pragma | src/lead_desk/db.py:74 | `conn.execute("PRAGMA foreign_keys=ON")` -> `conn.execute("PRAGMA foreign_keys=OFF")` | KILLED | tests/test_infra.py::test_connection_pragmas_and_busy_503 | 10.3 |
| 63 | recursive triggers off | db-pragma | src/lead_desk/db.py:75 | `conn.execute("PRAGMA recursive_triggers=ON")` -> `conn.execute("PRAGMA recursive_triggers=OFF")` | KILLED | tests/test_infra.py::test_connection_pragmas_and_busy_503 | 10.1 |
| 64 | synchronous FULL -> OFF | db-pragma | src/lead_desk/db.py:76 | `conn.execute("PRAGMA synchronous=FULL")` -> `conn.execute("PRAGMA synchronous=OFF")` | KILLED | tests/test_infra.py::test_connection_pragmas_and_busy_503 | 9.5 |
| 65 | is_busy ignores SQLITE_LOCKED | busy-mapping | src/lead_desk/db.py:88 | `in (SQLITE_BUSY, SQLITE_LOCKED)` -> `in (SQLITE_BUSY,)` | SURVIVED |  | 218.6 |
| 66 | migration backfill sending -> crm_done 1 | migration | src/lead_desk/db.py:30 | `"UPDATE followups SET crm_done = CASE"     " WHEN state = 'sending' TH` -> `"UPDATE followups SET crm_done = CASE"     " WHEN state = 'sending' TH` | KILLED | tests/test_hardening_cloud_b.py::test_g15_old_book_is_backfilled | 94.1 |
| 67 | init_schema accepts user_version 2 | migration | src/lead_desk/db.py:145 | `if version not in (0, SCHEMA_VERSION):` -> `if version not in (0, SCHEMA_VERSION, 2):` | SURVIVED |  | 218.6 |
| 68 | E1 (T1 extra) | extra | src/lead_desk/desk.py:1234 | `int(ambiguous),` -> `0,` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 1.2 |
| 69 | E2 (T1 extra) | extra | src/lead_desk/desk.py:105 | `" WHERE lead_id=? AND state IN ('pending','failed')"` -> `" WHERE lead_id=? AND state IN ('pending','failed','sending')"` | KILLED | tests/test_mutation_guards.py::test_claim_needs_the_right_state[sending-states1] | 0.8 |
| 70 | E3 (T1 extra) | extra | src/lead_desk/desk.py:104 | `THEN 1 ELSE auto_attempts+1 END, updated_at=?"         " WHERE lead_id` -> `THEN 0 ELSE auto_attempts+1 END, updated_at=?"         " WHERE lead_id` | KILLED | tests/test_mutation_guards.py::test_claim_clears_send_started[states2-failed] | 0.8 |
| 71 | E4 (T1 extra) | extra | src/lead_desk/desk.py:887 | `if crm_done == CRM_DONE:             return True` -> `if crm_done == CRM_DONE:             return False` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 1.0 |
| 72 | E5 (T1 extra) | extra | src/lead_desk/desk.py:897 | `if not self._mark_crm(             lead_id, CRM_STARTED, token        ` -> `if not self._mark_crm(             lead_id, CRM_NOT_ASKED, token      ` | KILLED | tests/test_mutation_guards.py::test_crm_intent_mark_before_the_put | 0.9 |
| 73 | E6 (T1 extra) | extra | src/lead_desk/desk.py:926 | `return self._mark_crm(lead_id, CRM_DONE, token)  # retried` -> `return self._mark_crm(lead_id, CRM_STARTED, token)  # retried` | KILLED | tests/test_mutation_guards.py::test_ambiguous_send_marks_the_row | 0.9 |
| 74 | E7 (T1 extra) | extra | src/lead_desk/desk.py:917 | `lead_id, CRM_NOT_ASKED, token, best_effort=True` -> `lead_id, CRM_STARTED, token, best_effort=True` | KILLED | tests/test_mutation_guards.py::test_proven_failed_put_resets_the_mark | 0.9 |
| 75 | E8 (T1 extra) | extra | src/lead_desk/desk.py:381 | `WHEN crm_done = 1 AND send_started = 1 THEN 1` -> `WHEN crm_done = 1 THEN 1` | KILLED | tests/test_mutation_guards.py::test_requeue_marks_only_started_sends | 0.9 |
| 76 | E9 (T1 extra) | extra | src/lead_desk/desk.py:378 | `" WHEN crm_done <> 1 OR send_started = 0 THEN 'pending'"` -> `" WHEN crm_done <> 1 THEN 'pending'"` | KILLED | tests/test_mutation_guards.py::test_blind_requeue_unsent_goes_pending | 1.0 |
| 77 | E10 (T1 extra) | extra | src/lead_desk/desk.py:384 | `" AND (? OR crm_done <> 1 OR send_started = 0)"` -> `" AND (? OR crm_done <> 1)"` | KILLED | tests/test_mutation_guards.py::test_requeue_mode_unknown_rule | 1.0 |
| 78 | E11 (T1 extra) | extra | src/lead_desk/desk.py:968 | `" WHERE state='sending' AND lead_id=? AND attempts=?",                ` -> `" WHERE state='sending' AND lead_id=? AND attempts>=?",               ` | KILLED | tests/test_mutation_guards.py::test_touch_only_for_the_owner | 1.1 |
| 79 | E12 (T1 extra) | extra | src/lead_desk/desk.py:1202 | `" WHERE lead_id=? AND state='pending' AND auto_attempts=?"` -> `" WHERE lead_id=? AND state='pending' AND auto_attempts>=?"` | KILLED | tests/test_mutation_guards.py::test_defer_pending_counts_one_try | 1.1 |
| 80 | E13 (T1 extra) | extra | src/lead_desk/desk.py:97 | `("pending",): (         "UPDATE followups SET state='sending', attempt` -> `("pending",): (         "UPDATE followups SET state='sending', attempt` | KILLED | tests/test_mutation_guards.py::test_claim_clears_send_started[states0-pending] | 0.7 |
| 81 | E14 (T1 extra) | extra | src/lead_desk/desk.py:555 | `first <= now - self.config.stall_seconds` -> `first < now - self.config.stall_seconds` | KILLED | tests/test_mutation_guards.py::test_future_receipt_by_own_clock | 1.0 |

## Survivors (fast selection), exact line changed

### #3 email_key normalisation drops strip (src/lead_desk/identity.py:39)
- old: `'return s.strip().lower()'`
- new: `'return s.lower()'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 58 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #35 replay due-time boundary <= -> < (src/lead_desk/desk.py:838)
- old: `'return bool(row[1] == 0 or row[2] + backoff_after(int(row[1])) <= self._now())'`
- new: `'return bool(row[1] == 0 or row[2] + backoff_after(int(row[1])) < self._now())'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #41 give-back of a claim ignores send_started (src/lead_desk/desk.py:1053)
- old: `'WHERE state=\'sending\' AND lead_id=? AND attempts=? AND send_started=0"'`
- new: `'WHERE state=\'sending\' AND lead_id=? AND attempts=?"'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #48 sent result keeps the old last_error (src/lead_desk/desk.py:1231)
- old: `'None if state == "sent" else last_error,'`
- new: `'last_error,'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #49 sent_at set for non-sent results (src/lead_desk/desk.py:1233)
- old: `'now if state == "sent" else None,'`
- new: `'now,'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #50 result record ignores the sending state (src/lead_desk/desk.py:1228)
- old: `'WHERE lead_id=? AND attempts=? AND state=\'sending\'"'`
- new: `'WHERE lead_id=? AND attempts=?"'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #52 retry busy answered 409 instead of 503 (src/lead_desk/desk.py:1310)
- old: `'return Reply(HTTP_BUSY, {"error": "busy"})'`
- new: `'return Reply(HTTP_CONFLICT, {"error": "busy"})'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #58 resolve idempotency: also acts on failed rows (src/lead_desk/desk.py:1355)
- old: `'WHERE lead_id=? AND state=\'unknown\'"\n                        " AND (? = 0'`
- new: `'WHERE lead_id=? AND state IN (\'unknown\',\'failed\')"\n                        " AND (? = 0'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #60 reconcile expected_match == -> >= (src/lead_desk/desk.py:1434)
- old: `'match = None if expected is None else received == expected'`
- new: `'match = None if expected is None else received >= expected'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #65 is_busy ignores SQLITE_LOCKED (src/lead_desk/db.py:88)
- old: `'in (SQLITE_BUSY, SQLITE_LOCKED)'`
- new: `'in (SQLITE_BUSY,)'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

### #67 init_schema accepts user_version 2 (src/lead_desk/db.py:145)
- old: `'if version not in (0, SCHEMA_VERSION):'`
- new: `'if version not in (0, SCHEMA_VERSION, 2):'`
- fast selection: no test failed (guards plus 13 files).  Slow load tests: SURVIVED the 3 slow load tests too (rc=0) in 59 s
- why no test caught it: no test in the selection asserts the changed behaviour (nothing failed; no further analysis done by the runner).

## Earlier 7 survivors (#4, #11, #12, #13, #20, #21, #26)

- #4 unique index on email_key made non-unique: KILLED, by tests/test_mutation_guards.py::test_email_key_unique_in_sql
- #11 schema source_ref length bound 128 -> 127: KILLED, by tests/test_mutation_guards.py::test_source_ref_bounds_in_sql
- #12 envelope min length boundary <= -> <: KILLED, by tests/test_mutation_guards.py::test_source_ref_one_char_and_empty
- #13 automatic claim no longer clears send_started: KILLED, by tests/test_mutation_guards.py::test_claim_clears_send_started[states0-pending]
- #20 reaper requeue age boundary <= -> <: KILLED, by tests/test_mutation_guards.py::test_requeue_age_boundary_direct
- #21 reaper stalled-receipt boundary <= -> <: KILLED, by tests/test_mutation_guards.py::test_stalled_receipt_age_boundary
- #26 reaper ignores receipts stamped in the future: KILLED, by tests/test_mutation_guards.py::test_future_receipt_by_own_clock

## Not run

- Phase 2 (3 slow load tests on survivors): see per-survivor line above; any marked NOT RUN did not fit the 75 minute box.
- Nothing else skipped; no mutant INVALID; all 81 old texts occur exactly once in the A4 pristine files, including T1 extras E1-E14 as #68-#81 (mutate.py EXTRA used unchanged).
