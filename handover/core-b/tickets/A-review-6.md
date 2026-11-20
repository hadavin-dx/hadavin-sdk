# A-review-6: `_drain_older_first` on the write path (branch cloud/core-b)

Reviewer: fresh, read-only on source. Test run (one, no workers):
`pytest tests/warden_port tests/test_audit_drain.py tests/test_audit_drain_transient.py tests/test_audit_drain_transient_2.py` against the PG DSN: **571 passed in 28.01s**.

Verdict: **CLEAN** (nothing above Minor). Three Minor and two Notes below.

## Answers

1. **Test rewrite did not weaken the protected property.** `test_an_outcome_that_cannot_be_appended_waits_in_the_outbox`
   (tests/warden_port/test_audit_chain.py:504) still asserts: the failed outcome returns None (never raises, never blocks),
   exactly one outbox row holds it (not lost), the tick writes it (reconcile == 1), nothing remains afterwards. It now runs
   reconcile BEFORE the next write_intent, because with the pre-drain the intent itself would drain the row; the "intent
   first, tick later" order it used to pin is the overtaking that was fixed on purpose. That path is now pinned by
   `test_a_new_event_does_not_overtake_a_parked_outcome` (:520) and, for PG-style transient errors,
   `test_a_newer_inline_event_does_not_overtake...` (tests/test_audit_drain_transient.py:156). The "sick outbox must not block
   an intent" half is covered by `test_an_inline_intent_is_written_even_when_the_older_row_is_still_refused` (:166).
   Gap (Minor-1): no test makes the drain RAISE or stall (only refuse), see below.

2. **Latency/failure on the write path.** No exception can leak: `_drain_older_first` (chain.py:320) wraps `_drain_pass` in
   `except Exception`, and `_drain_pass` already folds select/append errors into `_Pass`. No recursion: `_drain_pass` holds the
   non-reentrant `_flush_lock` (:443) but `_drain_item`/`_drain`/`_append` never take it and `checkpoint()` does not call
   write_*; `_flush_pending` (takes the same lock) is called only after the drain returned. Added cost exists only while
   `_outbox_dirty` is True. Costs:
   - Minor-2 (chain.py:443-476): the drain holds `_flush_lock` for the whole pass (up to AUDIT_DRAIN_BATCH=500 appends plus
     the paging select) and other writer threads block on it in their own `_drain_older_first`. A pass stops at the first
     transient refusal, so the worst case on a sick PG is about one `lock_timeout` (10 s, store/postgres.py:197) in the drain
     plus one more in the new append, i.e. up to ~2x previous caller latency, and concurrent writers queue behind it. Before
     this change the write path took `_flush_lock` only when `_pending` was non-empty. No hard cap on a healthy but huge backlog
     (500 appends under the lock, each with the advisory lock) either; tick has the same cost, but a caller thread now pays it.
     Suggest a cheaper bound for the write path (e.g. limit the pre-drain to a small batch, or `acquire(blocking=False)` /
     skip when another thread is draining).
   - Minor-3 (chain.py:476-480, 453): `_outbox_dirty` clears only when the select finds NO rows. Unreadable rows (counted
     `unreadable`, kept) or permanently-refused rows with sqlstate 42501 (not quarantined) keep `seen > 0` forever, so every
     write_intent/write_outcome of the process then runs a full select + retry pass until an operator fixes them. Correct but a
     permanent per-write tax. Quarantined rows are excluded by the NOT LIKE, so they do not cause it.

3. **Audit-before-action holds.** A drain that raises is swallowed and logged (:326-331); the intent is then appended, or
   `AuditUnavailable` is raised from write_intent (:290-292), never silently skipped. A drain that stalls blocks the caller
   (bounded by lock_timeout on PG), it does not drop the intent; there is no statement_timeout, so a hung (not locked)
   connection could stall both, as before. DuplicateEvent still propagates from write_intent unchanged. A drained older row
   whose delete fails is deduped on the next pass (`not_deleted`), no loss.

4. **Chain kinds and release CLI.**
   - `local_dir` (audit/local_dir.py) is a separate class with its own outbox folder; `_drain_older_first` does not exist
     there, so behaviour is unchanged (it still has no older-first guarantee: Note-1).
   - `chain` on memory (SQLite) and postgres: both covered by the 571 passing tests (PG schema from migrate).
   - Release CLI (cli.py:481, store/postgres.py:765-817): the release role has NO grant on audit_outbox at all
     (migrate.py:68-70: only audit_entries APPEND and audit_checkpoints SELECT). `_outbox_dirty` is set only after a
     successful outbox INSERT (chain.py:304), which that role can never do, so the flag stays False and the pre-drain never
     runs, never issuing a SELECT/DELETE on audit_outbox with the wrong role. A failed outcome falls to `_pending` as before.
     No behaviour change. (Not covered by a test: Minor-1.)

## Findings

- Minor-1: no test for a drain that raises or stalls on the write path, nor for the release-role case staying inert
  (dirty never set). The "never raises" guard at chain.py:326 is untested; a monkeypatched `_drain_pass` raising, asserting
  write_intent still returns and write_outcome still returns, would pin it. Also none for concurrent writers during a drain.
- Minor-2: lock-held drain latency on the write path, see 2.
- Minor-3: permanent dirty flag with unreadable / 42501 rows, see 2.
- Note-1: ordering protection covers only the outbox table, not `_pending` (memory) events and not rows parked by an earlier
  process or another process (`_outbox_dirty` starts False, chain.py:~251); the docstring says "this process", which is
  honest. Those rows still reconcile by ts on the tick.
- Note-2 (race, benign): a write_outcome inserting an outbox row sets `_outbox_dirty = True` without the flush lock; a drain
  that read an empty table just before can then set it False (:480), losing the flag for that row until the next tick. The row
  is not lost; only the older-first guard is skipped for it.
