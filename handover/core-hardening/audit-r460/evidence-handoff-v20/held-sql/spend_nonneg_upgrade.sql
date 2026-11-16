-- HELD FILE 1c of DB-1 = THE UPGRADE from the default (spend_nonneg.sql) to the variant (spend_nonneg_finite.sql).
-- Needs its OWN owner yes (naming this file's sha256) and only makes sense when the default file is already applied
-- and the owner later says yes to L7. Both files create the constraint names spend_usd_ok and spend_month_usd_ok, so
-- this file drops and re-adds each name in ONE statement (one lock, one transaction): the table is never without a rule.
-- Needs Postgres 14 or newer ('Infinity'::numeric). Same pre-flight (CORE-PR-HANDOFF-v16.md 5.6 item 1(e)), same lock rule.
-- On a table that holds a NaN or Infinity row it fails (23514) and the migration rolls back, the old rule stays.
SET LOCAL lock_timeout = '5s';
ALTER TABLE spend DROP CONSTRAINT spend_usd_ok, ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
ALTER TABLE spend_month DROP CONSTRAINT spend_month_usd_ok, ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
