-- HELD FILE 1b of DB-1 = THE VARIANT (needs the OWNER's own yes, question L7; without it this file is never moved).
-- CHECK (usd >= 0 AND usd < 'Infinity'::numeric): also refuses a not-a-number and an infinite total.
-- It is pinned separately from spend_nonneg.sql (its own sha256 in HELD); an owner yes covers exactly the sha256 it
-- names and nothing else. Apply ONE of the two held files, never both (same constraint names).
-- Needs Postgres 14 or newer ('Infinity'::numeric does not parse before 14). Same pre-flight, lock and timing rules as
-- spend_nonneg.sql.
SET LOCAL lock_timeout = '5s';
ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
