# cloud-fix-tests-b: failing-first tests for F3, F4, F6, F7, F10-F15 (ORDER 201)

Test file: /tmp/dpld/tests/test_hardening_cloud_b.py (23 test cases, 21 functions + 1 parametrised x2). Baseline: commit 494244e, copy /tmp/dpld-baseline. Command: `cd /tmp/dpld-baseline && PATH=/tmp/dpld-venv/bin:$PATH python -m pytest -q -rA --tb=short -p no:cacheprovider tests/test_hardening_cloud_b.py` -> **23 failed in 28.01s** (rc=1). Raw output below.

Sanity run on the implementer's work-in-progress tree (/tmp/dpld, not final): 20 passed, 3 failed (see notes). That run only checks my tests are not wrong; it is not evidence about the fix.

## Table
| test | finding | expected behaviour | failing message on old code |
|---|---|---|---|
| `test_f3_reaper_decides_stalled_open_receipt_but_not_a_fresh_one` | F3 | Reaper decides open receipts older than stall time without restart; leaves fresh ones | AttributeError: 'Desk' has no attribute 'start_background' (expected symptom) |
| `test_f3_reaper_requeues_stuck_sending_keyed` | F3 | Keyed 'sending' row older than 20 s goes pending then sent; younger left alone | AttributeError start_background (expected symptom) |
| `test_f3_reaper_makes_stuck_sending_unknown_when_blind` | F3 | Blind stuck 'sending' becomes unknown, never re-sent | AttributeError start_background (expected symptom) |
| `test_f3_transaction_1_retries_when_database_is_busy` | F3 | Receipt write retries when DB busy 7 s: 201 | expected 201 after retry, got 503 {'error': 'busy', 'receipt_id': None} |
| `test_f3_transaction_2_retries_when_database_is_busy` | F3 | Decision write retries when DB busy 7 s: 201, no open receipt | expected 201 after retry, got 503 {'error': 'busy', 'receipt_id': 1} |
| `test_f3_retry_never_answers_200_with_state_sending` | F3 | Retry never 200 with state sending | Retry answered 200 with state 'sending' |
| `test_f4_mode_mismatch_is_unknown_and_retry_is_refused` | F4 | Mode mismatch after 2xx: unknown/mode_mismatch, Retry 409, one email | got ('failed', 'mode_mismatch') |
| `test_f4_capability_is_read_again_at_startup` | F4 | Start-up re-reads capability | start-up did not re-read /fake/info ('keyed' == 'blind') |
| `test_f6_outage_is_retried_automatically[SendRefused]` | F6 | Refused sends retried automatically, ends sent | AttributeError start_background (expected symptom) |
| `test_f6_outage_is_retried_automatically[SendUnreachable]` | F6 | Unreachable sends retried automatically, ends sent | AttributeError start_background (expected symptom) |
| `test_f6_failed_only_after_the_attempt_cap` | F6 | 'failed' only after a bounded number of tries | AttributeError start_background (expected symptom) |
| `test_f6_person_retry_resets_the_count` | F6 | Person's Retry resets count: next refusal gives pending, then sent | AttributeError start_background (expected symptom) |
| `test_f7_retry_after_failed_send_adds_no_second_crm_row` | F7 | Blind CRM: Retry after failed send leaves 1 CRM row (crm_done=1) | 2 CRM rows for one lead |
| `test_f7_concurrent_drives_of_one_lead_give_one_crm_row` | F7 | Blind CRM: 6 concurrent drives give 1 CRM row, 1 email | 6 CRM rows for one lead |
| `test_f10_counts_ok_is_false_while_any_followup_is_unfinished` | F10 | /counts ok false while pending/failed/unknown/sending; keys failed, unknown, sending | ok is True while a follow-up is pending |
| `test_f11_apostrophe_email_accepted_other_characters_still_refused` | F11 | o'brien@example.test accepted; " , ; < > space still refused | got 202 verdict review, reason invalid_email |
| `test_f12_replay_with_other_payload_keeps_answer_and_makes_review_item` | F12 | Replay with other payload: original answer, payload_matches false, D<receipt> item | no D item for receipt 1; review list: [] |
| `test_f13_startup_with_50_pending_and_slow_sender_does_not_block_serving` | F13 | Start-up <2 s, /counts <2 s with 50 pending + slow sender; reaper sends all | AttributeError start_background (expected symptom) |
| `test_f14_second_desk_via_symlinked_path_is_refused` | F14 | Second desk via symlink exits 2 'another desk...' | second desk kept running (did not exit in 15 s) |
| `test_f14_lock_file_that_cannot_be_opened_gives_another_message` | F14 | Unopenable lock file: different message, non-zero exit | output was 'another desk is using this database' |
| `test_f14_lock_file_replaced_while_locking_is_detected` | F14 | Replaced lock file (new inode) detected | lock held on a file no longer at the path (inode 1139105 vs 1139121) |
| `test_f15_startup_twice_raises` | F15 | startup() twice raises | DID NOT RAISE |
| `test_f15_startup_after_serving_started_raises` | F15 | startup() after serving raises | DID NOT RAISE |

## Notes (read first)
- 8 tests fail on the old code only with `AttributeError: 'Desk' object has no attribute 'start_background'` (3 x F3 reaper, 4 x F6 cases, F13). That is the expected symptom of the missing feature; they cannot show a deeper reason before the feature exists. The other 15 fail on real behaviour.
- Assumed names: Desk.start_background() (called before startup(), as the implementer documents), Desk.stop_background() (teardown), column followups.crm_done, review item id `D<receipt_id>`, /counts keys `failed`, `unknown`, `sending`. The test for F3 "Retry never 200 sending" monkeypatches the private `_record_send_result` to stand for a swallowed busy error.
- DISAGREEMENTS seen on the implementer's WIP tree (decide who is right): (1) F10: WIP names the keys `failed_followups`, `unknown_followups`, `sending_followups`; the order says `failed`, `unknown`, `sending`; my test follows the order. (2) F6 reset: after the cap, with a person's Retry and the sender refusing once more, my test expects state `pending` (count reset, automatic tries continue); WIP returns `failed`. (3) F14 unopenable lock file: the WIP server.py still prints "another desk is using this database" for any OSError (server.py not yet changed at the time of the run).
- Time: tests F3 (two busy tests) hold the database 7 s each; whole file about 28 s on the old code, about 48 s on WIP.
- Not tested by design: F1, F5, F9 (implementer), F2, F8 (lead). Nothing in src/, schema.sql or existing tests was touched; nothing committed or pushed.

## Raw output (old code)
```

FFFFFFFFFFFFFFFFFFFFFFF                                                  [100%]
=================================== FAILURES ===================================
_______ test_f3_reaper_decides_stalled_open_receipt_but_not_a_fresh_one ________
tests/test_hardening_cloud_b.py:119: in test_f3_reaper_decides_stalled_open_receipt_but_not_a_fresh_one
    rig = reaper_rig(env, bg)
          ^^^^^^^^^^^^^^^^^^^
tests/test_hardening_cloud_b.py:87: in reaper_rig
    bg(rig.desk)
tests/test_hardening_cloud_b.py:53: in start
    desk.start_background()
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'Desk' object has no attribute 'start_background'
_________________ test_f3_reaper_requeues_stuck_sending_keyed __________________
tests/test_hardening_cloud_b.py:142: in test_f3_reaper_requeues_stuck_sending_keyed
    rig = reaper_rig(env, bg)
          ^^^^^^^^^^^^^^^^^^^
tests/test_hardening_cloud_b.py:87: in reaper_rig
    bg(rig.desk)
tests/test_hardening_cloud_b.py:53: in start
    desk.start_background()
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'Desk' object has no attribute 'start_background'
____________ test_f3_reaper_makes_stuck_sending_unknown_when_blind _____________
tests/test_hardening_cloud_b.py:160: in test_f3_reaper_makes_stuck_sending_unknown_when_blind
    rig = reaper_rig(env, bg, outbox="blind")
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_hardening_cloud_b.py:87: in reaper_rig
    bg(rig.desk)
tests/test_hardening_cloud_b.py:53: in start
    desk.start_background()
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'Desk' object has no attribute 'start_background'
_____________ test_f3_transaction_1_retries_when_database_is_busy ______________
tests/test_hardening_cloud_b.py:180: in test_f3_transaction_1_retries_when_database_is_busy
    assert reply.status == 201, f"expected 201 after retry, got {reply.status} {reply.body}"
E   AssertionError: expected 201 after retry, got 503 {'error': 'busy', 'receipt_id': None}
E   assert 503 == 201
E    +  where 503 = Reply(status=503, body={'error': 'busy', 'receipt_id': None}, drive_lead_id=None).status
------------------------------ Captured log call -------------------------------
WARNING  lead_desk:desk.py:159 request failed: OperationalError
_____________ test_f3_transaction_2_retries_when_database_is_busy ______________
tests/test_hardening_cloud_b.py:201: in test_f3_transaction_2_retries_when_database_is_busy
    assert reply.status == 201, f"expected 201 after retry, got {reply.status} {reply.body}"
E   AssertionError: expected 201 after retry, got 503 {'error': 'busy', 'receipt_id': 1}
E   assert 503 == 201
E    +  where 503 = Reply(status=503, body={'error': 'busy', 'receipt_id': 1}, drive_lead_id=None).status
------------------------------ Captured log call -------------------------------
WARNING  lead_desk:desk.py:159 request failed: OperationalError
______________ test_f3_retry_never_answers_200_with_state_sending ______________
tests/test_hardening_cloud_b.py:215: in test_f3_retry_never_answers_200_with_state_sending
    assert not (reply.status == 200 and state == "sending"), f"Retry answered 200 with state 'sending': {reply.body}"
E   AssertionError: Retry answered 200 with state 'sending': {'item_id': 'FL18fd07396efd', 'state': 'sending'}
E   assert not (200 == 200 and 'sending' == 'sending'
E    +  where 200 = Reply(status=200, body={'item_id': 'FL18fd07396efd', 'state': 'sending'}, drive_lead_id=None).status
E     
E       sending)
____________ test_f4_mode_mismatch_is_unknown_and_retry_is_refused _____________
tests/test_hardening_cloud_b.py:231: in test_f4_mode_mismatch_is_unknown_and_retry_is_refused
    assert rig.state(lid) == ("unknown", "mode_mismatch"), f"got {rig.state(lid)}"
E   AssertionError: got ('failed', 'mode_mismatch')
E   assert ('failed', 'mode_mismatch') == ('unknown', 'mode_mismatch')
E     
E     At index 0 diff: 'failed' != 'unknown'
E     Use -v to get more diff
_________________ test_f4_capability_is_read_again_at_startup __________________
tests/test_hardening_cloud_b.py:245: in test_f4_capability_is_read_again_at_startup
    assert rig.outbox.capability == "blind", "start-up did not re-read /fake/info"
E   AssertionError: start-up did not re-read /fake/info
E   assert 'keyed' == 'blind'
E     
E     - blind
E     + keyed
_____________ test_f6_outage_is_retried_automatically[SendRefused] _____________
tests/test_hardening_cloud_b.py:270: in test_f6_outage_is_retried_automatically
    rig = reaper_rig(env, bg, outbox=FlakyOutbox(2, exc))
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_hardening_cloud_b.py:87: in reaper_rig
    bg(rig.desk)
tests/test_hardening_cloud_b.py:53: in start
    desk.start_background()
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'Desk' object has no attribute 'start_background'
___________ test_f6_outage_is_retried_automatically[SendUnreachable] ___________
tests/test_hardening_cloud_b.py:270: in test_f6_outage_is_retried_automatically
    rig = reaper_rig(env, bg, outbox=FlakyOutbox(2, exc))
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_hardening_cloud_b.py:87: in reaper_rig
    bg(rig.desk)
tests/test_hardening_cloud_b.py:53: in start
    desk.start_background()
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'Desk' object has no attribute 'start_background'
__________________ test_f6_failed_only_after_the_attempt_cap ___________________
tests/test_hardening_cloud_b.py:280: in test_f6_failed_only_after_the_attempt_cap
    rig = reaper_rig(env, bg, outbox=FlakyOutbox(10**6))
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_hardening_cloud_b.py:87: in reaper_rig
    bg(rig.desk)
tests/test_hardening_cloud_b.py:53: in start
    desk.start_background()
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'Desk' object has no attribute 'start_background'
____________________ test_f6_person_retry_resets_the_count _____________________
tests/test_hardening_cloud_b.py:294: in test_f6_person_retry_resets_the_count
    rig = reaper_rig(env, bg, outbox=FlakyOutbox(10**6))
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_hardening_cloud_b.py:87: in reaper_rig
    bg(rig.desk)
tests/test_hardening_cloud_b.py:53: in start
    desk.start_background()
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'Desk' object has no attribute 'start_background'
____________ test_f7_retry_after_failed_send_adds_no_second_crm_row ____________
tests/test_hardening_cloud_b.py:339: in test_f7_retry_after_failed_send_adds_no_second_crm_row
    assert rig.crm.count == 1, f"{rig.crm.count} CRM rows for one lead"
E   AssertionError: 2 CRM rows for one lead
E   assert 2 == 1
E    +  where 2 = <test_hardening_cloud_b.BlindCrm object at 0x7f6a81cf1220>.count
E    +    where <test_hardening_cloud_b.BlindCrm object at 0x7f6a81cf1220> = Rig(desk=<lead_desk.desk.Desk object at 0x7f6a81cf1310>, config=Config(db_path=PosixPath('/tmp/pytest-of-root/pytest-1...ytest-1322/test_f7_retry_after_failed_sen0/rig1/replies.json'), desks=[<lead_desk.desk.Desk object at 0x7f6a81cf1310>]).crm
____________ test_f7_concurrent_drives_of_one_lead_give_one_crm_row ____________
tests/test_hardening_cloud_b.py:350: in test_f7_concurrent_drives_of_one_lead_give_one_crm_row
    assert rig.crm.count == 1, f"{rig.crm.count} CRM rows for one lead"
E   AssertionError: 6 CRM rows for one lead
E   assert 6 == 1
E    +  where 6 = <test_hardening_cloud_b.BlindCrm object at 0x7f6a81b49190>.count
E    +    where <test_hardening_cloud_b.BlindCrm object at 0x7f6a81b49190> = Rig(desk=<lead_desk.desk.Desk object at 0x7f6a81b4b710>, config=Config(db_path=PosixPath('/tmp/pytest-of-root/pytest-1...ytest-1322/test_f7_concurrent_drives_of_o0/rig1/replies.json'), desks=[<lead_desk.desk.Desk object at 0x7f6a81b4b710>]).crm
_________ test_f10_counts_ok_is_false_while_any_followup_is_unfinished _________
tests/test_hardening_cloud_b.py:372: in test_f10_counts_ok_is_false_while_any_followup_is_unfinished
    assert c["ok"] is False, f"ok is {c['ok']} while a follow-up is pending"
E   AssertionError: ok is True while a follow-up is pending
E   assert True is False
______ test_f11_apostrophe_email_accepted_other_characters_still_refused _______
tests/test_hardening_cloud_b.py:392: in test_f11_apostrophe_email_accepted_other_characters_still_refused
    assert (ok.status, ok.body.get("verdict")) == (201, "new"), f"got {ok.status} {ok.body}"
E   AssertionError: got 202 {'receipt_id': 1, 'verdict': 'review', 'reason': 'invalid_email', 'replayed': False}
E   assert (202, 'review') == (201, 'new')
E     
E     At index 0 diff: 202 != 201
E     Use -v to get more diff
____ test_f12_replay_with_other_payload_keeps_answer_and_makes_review_item _____
tests/test_hardening_cloud_b.py:419: in test_f12_replay_with_other_payload_keeps_answer_and_makes_review_item
    assert f"D{rid}" in items, f"no D item for receipt {rid}; review list: {list(items)}"
E   AssertionError: no D item for receipt 1; review list: []
E   assert 'D1' in {}
___ test_f13_startup_with_50_pending_and_slow_sender_does_not_block_serving ____
tests/test_hardening_cloud_b.py:438: in test_f13_startup_with_50_pending_and_slow_sender_does_not_block_serving
    bg(desk2)
tests/test_hardening_cloud_b.py:53: in start
    desk.start_background()
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'Desk' object has no attribute 'start_background'
______________ test_f14_second_desk_via_symlinked_path_is_refused ______________
tests/test_hardening_cloud_b.py:487: in test_f14_second_desk_via_symlinked_path_is_refused
    second.wait(timeout=15)
/usr/lib/python3.12/subprocess.py:1264: in wait
    return self._wait(timeout=timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/lib/python3.12/subprocess.py:2045: in _wait
    raise TimeoutExpired(self.args, timeout)
E   subprocess.TimeoutExpired: Command '['/tmp/dpld-venv/bin/python', '-m', 'lead_desk.server']' timed out after 15 seconds

During handling of the above exception, another exception occurred:
tests/test_hardening_cloud_b.py:489: in test_f14_second_desk_via_symlinked_path_is_refused
    pytest.fail("a second desk is serving the same lead book through a symlink (it did not exit)")
E   Failed: a second desk is serving the same lead book through a symlink (it did not exit)
________ test_f14_lock_file_that_cannot_be_opened_gives_another_message ________
tests/test_hardening_cloud_b.py:516: in test_f14_lock_file_that_cannot_be_opened_gives_another_message
    assert b"another desk is using this database" not in out, out.decode(errors="replace")[-300:]
E   AssertionError: another desk is using this database
E     
E   assert b'another desk is using this database' not in b'another desk is using this database\n'
____________ test_f14_lock_file_replaced_while_locking_is_detected _____________
tests/test_hardening_cloud_b.py:538: in test_f14_lock_file_replaced_while_locking_is_detected
    assert os.fstat(f.fileno()).st_ino == os.stat(path).st_ino, "the lock is held on a file no longer at the path"
E   AssertionError: the lock is held on a file no longer at the path
E   assert 1139105 == 1139121
E    +  where 1139105 = os.stat_result(st_mode=33188, st_ino=1139105, st_dev=65024, st_nlink=0, st_uid=0, st_gid=0, st_size=0, st_atime=1794219579, st_mtime=1794219579, st_ctime=1794219579).st_ino
E    +    where os.stat_result(st_mode=33188, st_ino=1139105, st_dev=65024, st_nlink=0, st_uid=0, st_gid=0, st_size=0, st_atime=1794219579, st_mtime=1794219579, st_ctime=1794219579) = <built-in function fstat>(11)
E    +      where <built-in function fstat> = os.fstat
E    +      and   11 = <built-in method fileno of _io.BufferedRandom object at 0x7f6a81aaeb90>()
E    +        where <built-in method fileno of _io.BufferedRandom object at 0x7f6a81aaeb90> = <_io.BufferedRandom name='/tmp/pytest-of-root/pytest-1322/test_f14_lock_file_replaced_wh0/desk.sqlite3.lock'>.fileno
E    +  and   1139121 = os.stat_result(st_mode=33188, st_ino=1139121, st_dev=65024, st_nlink=1, st_uid=0, st_gid=0, st_size=0, st_atime=1794219579, st_mtime=1794219579, st_ctime=1794219579).st_ino
E    +    where os.stat_result(st_mode=33188, st_ino=1139121, st_dev=65024, st_nlink=1, st_uid=0, st_gid=0, st_size=0, st_atime=1794219579, st_mtime=1794219579, st_ctime=1794219579) = <built-in function stat>(PosixPath('/tmp/pytest-of-root/pytest-1322/test_f14_lock_file_replaced_wh0/desk.sqlite3.lock'))
E    +      where <built-in function stat> = os.stat
________________________ test_f15_startup_twice_raises _________________________
tests/test_hardening_cloud_b.py:549: in test_f15_startup_twice_raises
    with pytest.raises(Exception):  # noqa: B017, PT011 (the type is the implementer's choice; any raise counts)
E   Failed: DID NOT RAISE Exception
________________ test_f15_startup_after_serving_started_raises _________________
tests/test_hardening_cloud_b.py:559: in test_f15_startup_after_serving_started_raises
    with pytest.raises(Exception):  # noqa: B017, PT011
E   Failed: DID NOT RAISE Exception
=========================== short test summary info ============================
FAILED tests/test_hardening_cloud_b.py::test_f3_reaper_decides_stalled_open_receipt_but_not_a_fresh_one
FAILED tests/test_hardening_cloud_b.py::test_f3_reaper_requeues_stuck_sending_keyed
FAILED tests/test_hardening_cloud_b.py::test_f3_reaper_makes_stuck_sending_unknown_when_blind
FAILED tests/test_hardening_cloud_b.py::test_f3_transaction_1_retries_when_database_is_busy
FAILED tests/test_hardening_cloud_b.py::test_f3_transaction_2_retries_when_database_is_busy
FAILED tests/test_hardening_cloud_b.py::test_f3_retry_never_answers_200_with_state_sending
FAILED tests/test_hardening_cloud_b.py::test_f4_mode_mismatch_is_unknown_and_retry_is_refused
FAILED tests/test_hardening_cloud_b.py::test_f4_capability_is_read_again_at_startup
FAILED tests/test_hardening_cloud_b.py::test_f6_outage_is_retried_automatically[SendRefused]
FAILED tests/test_hardening_cloud_b.py::test_f6_outage_is_retried_automatically[SendUnreachable]
FAILED tests/test_hardening_cloud_b.py::test_f6_failed_only_after_the_attempt_cap
FAILED tests/test_hardening_cloud_b.py::test_f6_person_retry_resets_the_count
FAILED tests/test_hardening_cloud_b.py::test_f7_retry_after_failed_send_adds_no_second_crm_row
FAILED tests/test_hardening_cloud_b.py::test_f7_concurrent_drives_of_one_lead_give_one_crm_row
FAILED tests/test_hardening_cloud_b.py::test_f10_counts_ok_is_false_while_any_followup_is_unfinished
FAILED tests/test_hardening_cloud_b.py::test_f11_apostrophe_email_accepted_other_characters_still_refused
FAILED tests/test_hardening_cloud_b.py::test_f12_replay_with_other_payload_keeps_answer_and_makes_review_item
FAILED tests/test_hardening_cloud_b.py::test_f13_startup_with_50_pending_and_slow_sender_does_not_block_serving
FAILED tests/test_hardening_cloud_b.py::test_f14_second_desk_via_symlinked_path_is_refused
FAILED tests/test_hardening_cloud_b.py::test_f14_lock_file_that_cannot_be_opened_gives_another_message
FAILED tests/test_hardening_cloud_b.py::test_f14_lock_file_replaced_while_locking_is_detected
FAILED tests/test_hardening_cloud_b.py::test_f15_startup_twice_raises - Faile...
FAILED tests/test_hardening_cloud_b.py::test_f15_startup_after_serving_started_raises
23 failed in 28.01s
rc=1

```
