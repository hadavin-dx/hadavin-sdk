-- HELD FILE 1a of DB-1 = THE DEFAULT (lead's answer Q34, "migration 0006": CHECK (usd >= 0), exactly that).
-- A spend total may not be negative. It does NOT refuse a not-a-number total (NaN >= 0 is true in Postgres) and
-- does NOT refuse +Infinity; the code-level finite-number refusal of our store (S-2a, 5.4) does, whether or not this
-- file is applied. The stricter variant is the OTHER file spend_nonneg_finite.sql (owner yes L7); apply ONE of the two,
-- never both (both add the same constraint names). Applied only on the owner's yes that names THIS file's sha256.
-- Works on every Postgres version the studio could run (no 'Infinity' literal).
-- On a table that already holds a bad row this statement fails and the migration rolls back: run the pre-flight query
-- of CORE-PR-HANDOFF-v15.md 5.6 item 1(e) first. Runs under the migration role (a plain non-superuser role that owns
-- the tables), with the kill switch on and no run in flight. The store code must already write give-backs and settles
-- as UPDATE (S-2a); this check refuses the INSERT ... ON CONFLICT shape for a negative amount.
-- ADD CONSTRAINT takes an ACCESS EXCLUSIVE lock until the migration's transaction ends; the runner sets no
-- lock_timeout, so the file sets one for its own transaction: if a run still holds the table, this migration fails
-- after 5 seconds and rolls back instead of queueing every spend call.
SET LOCAL lock_timeout = '5s';
ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0);
ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0);
