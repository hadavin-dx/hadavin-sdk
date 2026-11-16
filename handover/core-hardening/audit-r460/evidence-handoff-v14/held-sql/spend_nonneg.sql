-- HELD FILE 1 of DB-1 (lead's answer Q34 "migration 0006"; the lead gives it the next free number at the move).
-- A spend total may not be negative, not-a-number or infinite. Applied only on the owner's yes, and only after the
-- lead's explicit yes on the second clause (question L7 of v14; silence is not a yes).
-- Needs Postgres 14 or newer ('Infinity'::numeric). On a table that already holds a bad row this statement
-- fails (and the migration rolls back): run the pre-flight query of CORE-PR-HANDOFF-v14.md 5.6 item 1(e) first.
-- Runs under the migration role, with the kill switch on and no run in flight (5.6 item 1(e)). The store code must
-- already write give-backs and settles as UPDATE (S-2a); this check refuses the INSERT ... ON CONFLICT shape for a
-- negative amount (raw-pg-b1-v13.txt T1).
-- ADD CONSTRAINT takes an ACCESS EXCLUSIVE lock on the table until the migration's transaction ends (run on 16.15:
-- raw-pg-lock-v14.txt); the runner sets no lock_timeout, so the file sets one for its own transaction: if a run
-- still holds the table, this migration fails after 5 seconds and rolls back instead of queueing every spend call.
SET LOCAL lock_timeout = '5s';
ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
