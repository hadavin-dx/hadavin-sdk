-- Money definer functions (ticket F-money-definer, option B of E13). This file adds the SECURITY DEFINER functions below
-- that are the only writers of the three money tables (spend, spend_month, spend_reservations), plus the release
-- function of 0008 (replaced below). THE WALL IS BUILT BY `migrate`, NOT BY THIS FILE ALONE: when roles are named,
-- `migrate` takes every write right on those tables from the runtime login (it keeps SELECT on spend and spend_month)
-- and grants it EXECUTE on reserve, settle, expire and add_spend; the purge role gets EXECUTE on the purge only. A
-- deployment migrated without naming roles has no wall (the stop-state check refuses it). The store (Python) calls
-- these functions by their schema-qualified name; the SQL of the bookings exists in this file only.
--
-- THE PROMISE (with the roles named): a runtime login cannot lower a booked amount, except by settling an open hold it can
-- name, once, by at most that hold's reserved amount. It cannot lower a plain charge, a settled or expired amount, forge
-- a settled row, edit usd, or touch a row by SQL (it has no right on the tables).
-- HONEST RESIDUAL (do not over-claim): the runtime still chooses the other arguments. (1) The caps are NOT arguments:
-- hadavin_reserve_spend takes 5 arguments (p_id, p_agent, p_day, p_usd, p_run_id) and reads day_cap and month_cap from the
-- table hadavin_caps, which the runtime login cannot write (HD005 when the agent has no row). So the runtime can neither
-- lower a booked amount nor choose or raise a cap. (2) It can settle any open hold whose id it knows to 0: the counter
-- falls by at most that hold's reserved amount, once. (3) It can expire any open hold older than
-- the limit min_expiry_age (default 3600 s; a younger age is refused, review M1), and the release function only lowers a
-- hold that was expired for longer than that: a self-inflicted outage, safe (holds stay booked at the reserved amount,
-- and a real late settle still finds its hold). (3b) It can name any booking day within max_day_skew days (default 1)
-- of the database's UTC date, never a far day that would start a fresh counter (review B3). (4) It can raise any counter by
-- add_spend.
--
-- Rules every function body follows:
--   * SECURITY DEFINER, VOLATILE (stated), NOT STRICT (a STRICT function returns NULL silently for a NULL argument, which
--     would look like success; every NULL is an explicit error instead), no EXCEPTION block (it would open a
--     subtransaction), no dynamic SQL (no EXECUTE, no format()): every table name is static and resolves through the pinned
--     search path. `#variable_conflict use_column` and a table alias on every table reference: a column named like an OUT
--     variable is never ambiguous.
--   * Placeholder pin `SET search_path = pg_catalog, pg_temp`: `migrate` re-pins every function to
--     pg_catalog, <this schema>, pg_temp on every run (this file cannot know the schema). pg_temp must stay LAST or a temp
--     table of the caller shadows the money tables; pg_catalog first means no user operator or function shadows
--     +, <=, greatest, clock_timestamp. A function body calls only pg_catalog built-ins.
--   * Every argument is validated INSIDE (the function is the trust boundary; the Python checks are an early, friendly
--     refusal that prove nothing): NULL, ids, NaN and infinity, scale, caps (no upper bound of the amount window: a cap
--     of 10 to the 12th must keep working), days, ages, bounds. A bad argument is ERRCODE 22023 and the text names the
--     parameter, never the value. The limits are read from the table hadavin_limits (written by `migrate` on every run
--     from the constants of the package; owner only), never written as a literal here. A missing limit row is HD004: fail
--     closed.
--   * Error codes: HD001 cap reached (message 'day' or 'month'), HD002 reservation not found (unknown or another
--     agent's id, the same error for both), HD003 counter row missing (the whole transaction rolls back), HD004 limit row
--     missing, HD005 no cap row for the agent (reserve only; fail closed), 22023 invalid argument, 23505 duplicate
--     reservation id (native).
--   * Lock order: the reservation row, the day counter, the month counter (the order of 0008 and of the store), so there is
--     no lock cycle.
-- Owner: whoever runs `migrate` (one owner for all hadavin_* functions and the money tables, checked by `migrate`). A
-- bug in a function runs with the owner's rights, and the 0010 triggers pass the owner by design: there is no second line.
-- Break-glass: the owner (never the runtime) repairs with direct SQL or ships a migration with CREATE OR REPLACE for the
-- function (the pin is re-applied by the next migrate run).

-- The limits the functions read. Rows (names are the interface): max_amount (exclusive upper bound of one amount),
-- max_decimals (scale), max_id_chars, max_expiry_age, min_expiry_age (youngest age a hold may be expired at, and how long
-- an expired hold is kept before the release function may lower it), max_day_skew (days a booking day may be from the
-- database's UTC date). Written by `migrate` as the owner; no other role has any right.
CREATE TABLE hadavin_limits (
    name TEXT PRIMARY KEY,
    value NUMERIC NOT NULL
);
REVOKE ALL ON hadavin_limits FROM PUBLIC;

-- The counters refuse a negative or infinite amount by themselves (review N1), whoever writes them: NaN sorts above every
-- number, so it fails the second test. Added NOT VALID (no long lock on a big table) and validated at once (this file is
-- unreleased: a database that already holds a bad row stops here, which is the point). The reservation amounts have
-- the same bounds since 0007.
ALTER TABLE spend ADD CONSTRAINT spend_usd_range CHECK (usd >= 0 AND usd < 'Infinity'::numeric) NOT VALID;
ALTER TABLE spend VALIDATE CONSTRAINT spend_usd_range;
ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_range CHECK (usd >= 0 AND usd < 'Infinity'::numeric) NOT VALID;
ALTER TABLE spend_month VALIDATE CONSTRAINT spend_month_usd_range;

-- hadavin_reserve_spend: book the worst case of one model call on the day and month counters, in the transaction that
-- adds the reservation row, refusing it when it would pass a cap (HD001 day first, then month; the whole function rolls
-- back with the caller's transaction). A duplicate id is the native unique_violation (23505).
CREATE OR REPLACE FUNCTION hadavin_reserve_spend(
    p_id TEXT, p_agent TEXT, p_day DATE, p_usd NUMERIC, p_run_id TEXT
)
RETURNS void
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
#variable_conflict use_column
DECLARE
    v_max_amount NUMERIC;
    v_max_decimals NUMERIC;
    v_max_id NUMERIC;
    v_skew NUMERIC;
    v_today DATE;
    v_month DATE;
    v_day_cap NUMERIC;
    v_month_cap NUMERIC;
BEGIN
    SELECT l.value INTO v_max_amount FROM hadavin_limits l WHERE l.name = 'max_amount';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_amount missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_max_decimals FROM hadavin_limits l WHERE l.name = 'max_decimals';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_decimals missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_max_id FROM hadavin_limits l WHERE l.name = 'max_id_chars';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_id_chars missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_skew FROM hadavin_limits l WHERE l.name = 'max_day_skew';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_day_skew missing' USING ERRCODE = 'HD004'; END IF;

    IF p_id IS NULL OR pg_catalog.char_length(p_id) NOT BETWEEN 1 AND v_max_id OR p_id !~ '^[A-Za-z0-9._:-]+$' THEN
        RAISE EXCEPTION 'invalid argument: p_id' USING ERRCODE = '22023';
    END IF;
    IF p_agent IS NULL OR pg_catalog.char_length(p_agent) NOT BETWEEN 1 AND v_max_id
       OR p_agent ~ E'[\\x01-\\x1f\\x7f-\\x9f]' THEN
        RAISE EXCEPTION 'invalid argument: p_agent' USING ERRCODE = '22023';
    END IF;
    IF p_run_id IS NOT NULL AND (pg_catalog.char_length(p_run_id) NOT BETWEEN 1 AND v_max_id
                                 OR p_run_id ~ E'[\\x01-\\x1f\\x7f-\\x9f]') THEN
        RAISE EXCEPTION 'invalid argument: p_run_id' USING ERRCODE = '22023';
    END IF;
    IF p_day IS NULL OR NOT pg_catalog.isfinite(p_day) OR p_day < DATE '1970-01-01' OR p_day > DATE '9999-12-31' THEN
        RAISE EXCEPTION 'invalid argument: p_day' USING ERRCODE = '22023';
    END IF;
    -- the booking day is the database's UTC date, give or take max_day_skew days (a clock a little off, a call across
    -- midnight). Any other day would start a fresh day and month counter, so a runtime that names 2099-01-01, then
    -- 2099-02-01 and so on would never meet a cap (review B3). The same 22023 as any other refused argument.
    v_today := (pg_catalog.clock_timestamp() AT TIME ZONE 'UTC')::date;
    IF p_day < v_today - v_skew::integer OR p_day > v_today + v_skew::integer THEN
        RAISE EXCEPTION 'invalid argument: p_day' USING ERRCODE = '22023';
    END IF;
    -- written positively: NaN sorts above every number and Infinity is above the window, both fail this test
    IF p_usd IS NULL OR NOT (p_usd >= 0 AND p_usd < v_max_amount) OR pg_catalog.scale(p_usd) > v_max_decimals THEN
        RAISE EXCEPTION 'invalid argument: p_usd' USING ERRCODE = '22023';
    END IF;
    -- the caps come from hadavin_caps (owner-written; the runtime cannot choose or change them), read without a lock: a
    -- concurrent hadavin_set_cap is seen either before or after, both are fine. No row: refuse, fail closed (HD005).
    SELECT c.day_cap, c.month_cap INTO v_day_cap, v_month_cap FROM hadavin_caps c WHERE c.agent_id = p_agent;
    IF NOT FOUND THEN RAISE EXCEPTION 'caps' USING ERRCODE = 'HD005'; END IF;
    v_month := pg_catalog.date_trunc('month', p_day)::date;

    INSERT INTO spend_reservations (reservation_id, agent_id, day, run_id, reserved_usd)
    VALUES (p_id, p_agent, p_day, p_run_id, p_usd);
    INSERT INTO spend (agent_id, day, usd) VALUES (p_agent, p_day, 0) ON CONFLICT DO NOTHING;
    -- strictly day before month: seed and book the day, then the month; a refusal raises and everything rolls back
    UPDATE spend s SET usd = s.usd + p_usd
     WHERE s.agent_id = p_agent AND s.day = p_day AND s.usd < v_day_cap AND s.usd + p_usd <= v_day_cap;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'day' USING ERRCODE = 'HD001';
    END IF;
    INSERT INTO spend_month (agent_id, month, usd) VALUES (p_agent, v_month, 0) ON CONFLICT DO NOTHING;
    UPDATE spend_month m SET usd = m.usd + p_usd
     WHERE m.agent_id = p_agent AND m.month = v_month AND m.usd < v_month_cap AND m.usd + p_usd <= v_month_cap;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'month' USING ERRCODE = 'HD001';
    END IF;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_reserve_spend(TEXT, TEXT, DATE, NUMERIC, TEXT) FROM PUBLIC;

-- hadavin_settle_spend: replace a hold by the real cost. The claim comes first (the row lock; a second caller waits,
-- finds the row settled, claims nothing and gets the stored row back with claimed = false). settled_usd is what stays
-- booked on the counters: the actual amount, or for a row that was expired the larger of the actual and the reserved amount
-- (after expiry the booking never goes down). The counters move by settled - reserved on the row's own day and month,
-- day first. The run cost is added as the actual amount (a missing run row is ignored). An unknown id or another agent's id
-- (when p_agent is given) is HD002, the same error for both; a missing counter row is HD003. p_agent NULL means "any
-- agent" (the documented residual).
CREATE OR REPLACE FUNCTION hadavin_settle_spend(p_id TEXT, p_actual NUMERIC, p_agent TEXT)
RETURNS TABLE (
    reservation_id TEXT, agent_id TEXT, day DATE, run_id TEXT, reserved_usd NUMERIC, settled_usd NUMERIC,
    status TEXT, created_at TIMESTAMPTZ, closed_at TIMESTAMPTZ, claimed BOOLEAN
)
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
#variable_conflict use_column
DECLARE
    v_max_amount NUMERIC;
    v_max_decimals NUMERIC;
    v_max_id NUMERIC;
    v_was TEXT;
    v_delta NUMERIC;
    rec RECORD;
BEGIN
    SELECT l.value INTO v_max_amount FROM hadavin_limits l WHERE l.name = 'max_amount';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_amount missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_max_decimals FROM hadavin_limits l WHERE l.name = 'max_decimals';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_decimals missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_max_id FROM hadavin_limits l WHERE l.name = 'max_id_chars';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_id_chars missing' USING ERRCODE = 'HD004'; END IF;

    IF p_id IS NULL OR pg_catalog.char_length(p_id) NOT BETWEEN 1 AND v_max_id OR p_id !~ '^[A-Za-z0-9._:-]+$' THEN
        RAISE EXCEPTION 'invalid argument: p_id' USING ERRCODE = '22023';
    END IF;
    IF p_actual IS NULL OR NOT (p_actual >= 0 AND p_actual < v_max_amount) OR pg_catalog.scale(p_actual) > v_max_decimals THEN
        RAISE EXCEPTION 'invalid argument: p_actual' USING ERRCODE = '22023';
    END IF;
    IF p_agent IS NOT NULL AND (pg_catalog.char_length(p_agent) NOT BETWEEN 1 AND v_max_id
                                OR p_agent ~ E'[\\x01-\\x1f\\x7f-\\x9f]') THEN
        RAISE EXCEPTION 'invalid argument: p_agent' USING ERRCODE = '22023';
    END IF;

    -- the claim: the lock reads the status BEFORE the change (after a lock wait READ COMMITTED re-checks the row, so a
    -- concurrent settle or expire cannot be misread)
    SELECT r.status INTO v_was FROM spend_reservations r
     WHERE r.reservation_id = p_id AND (p_agent IS NULL OR r.agent_id = p_agent) AND r.status IN ('open', 'expired')
       FOR UPDATE;
    IF NOT FOUND THEN
        SELECT * INTO rec FROM spend_reservations r WHERE r.reservation_id = p_id;
        IF NOT FOUND OR (p_agent IS NOT NULL AND rec.agent_id <> p_agent) THEN
            RAISE EXCEPTION 'reservation not found' USING ERRCODE = 'HD002';
        END IF;
        reservation_id := rec.reservation_id; agent_id := rec.agent_id; day := rec.day; run_id := rec.run_id;
        reserved_usd := rec.reserved_usd; settled_usd := rec.settled_usd; status := rec.status;
        created_at := rec.created_at; closed_at := rec.closed_at; claimed := false;
        RETURN NEXT;
        RETURN;
    END IF;
    UPDATE spend_reservations r
       SET status = 'settled',
           settled_usd = CASE WHEN v_was = 'expired' THEN GREATEST(p_actual, r.reserved_usd) ELSE p_actual END,
           closed_at = pg_catalog.clock_timestamp()
     WHERE r.reservation_id = p_id
    RETURNING r.* INTO rec;
    v_delta := rec.settled_usd - rec.reserved_usd;
    IF v_was = 'open' OR v_delta <> 0 THEN  -- an expired row that does not rise leaves the counters alone
        -- a counter never goes below zero: a counter that drifted under its open holds (an operator repair) is refused
        UPDATE spend s SET usd = s.usd + v_delta
         WHERE s.agent_id = rec.agent_id AND s.day = rec.day AND s.usd + v_delta >= 0;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'spend counter row missing or below its holds' USING ERRCODE = 'HD003';
        END IF;
        UPDATE spend_month m SET usd = m.usd + v_delta
         WHERE m.agent_id = rec.agent_id AND m.month = pg_catalog.date_trunc('month', rec.day)::date
           AND m.usd + v_delta >= 0;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'spend counter row missing or below its holds' USING ERRCODE = 'HD003';
        END IF;
    END IF;
    IF rec.run_id IS NOT NULL THEN  -- the real actual amount; a missing run row is ignored (parity with the memory store and the old Postgres store; review m9: a run of ANOTHER agent is not excluded: residual)
        UPDATE runs u SET cost_usd = u.cost_usd + p_actual WHERE u.run_id = rec.run_id;
    END IF;
    reservation_id := rec.reservation_id; agent_id := rec.agent_id; day := rec.day; run_id := rec.run_id;
    reserved_usd := rec.reserved_usd; settled_usd := rec.settled_usd; status := rec.status;
    created_at := rec.created_at; closed_at := rec.closed_at; claimed := true;
    RETURN NEXT;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_settle_spend(TEXT, NUMERIC, TEXT) FROM PUBLIC;

-- hadavin_expire_spend_reservations: mark the open holds older than p_age_s seconds (database clock) expired. They stay
-- booked at the full reserved amount: the counters do not move. Returns the number of rows.
CREATE OR REPLACE FUNCTION hadavin_expire_spend_reservations(p_age_s INTEGER)
RETURNS BIGINT
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
#variable_conflict use_column
DECLARE
    v_max_age NUMERIC;
    v_min_age NUMERIC;
    n BIGINT;
BEGIN
    SELECT l.value INTO v_max_age FROM hadavin_limits l WHERE l.name = 'max_expiry_age';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_expiry_age missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_min_age FROM hadavin_limits l WHERE l.name = 'min_expiry_age';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit min_expiry_age missing' USING ERRCODE = 'HD004'; END IF;
    -- a hold younger than min_expiry_age cannot be expired (review M1): the runtime login runs this function, and a
    -- live hold expired at age 0 can be released by the operator, after which the real cost of its late settle is lost
    IF p_age_s IS NULL OR p_age_s < v_min_age OR p_age_s > v_max_age THEN
        RAISE EXCEPTION 'invalid argument: p_age_s' USING ERRCODE = '22023';
    END IF;
    UPDATE spend_reservations r
       SET status = 'expired', settled_usd = r.reserved_usd, closed_at = pg_catalog.clock_timestamp()
     WHERE r.status = 'open'
       AND r.created_at <= pg_catalog.clock_timestamp() - pg_catalog.make_interval(secs => p_age_s::double precision);
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_expire_spend_reservations(INTEGER) FROM PUBLIC;

-- hadavin_release_expired_spend (replaces the 0008 body, same signature, owner and pin; `migrate` re-pins it): the one
-- supported way the booked amount of an expired hold goes down. Review M1: only holds that were expired more than
-- min_expiry_age seconds ago (closed_at is the moment of the expiry) are released, so a late settle of a hold that was
-- just expired still finds it and books the real cost. Everything else is as in 0008.
CREATE OR REPLACE FUNCTION hadavin_release_expired_spend(p_agent TEXT, p_day DATE)
RETURNS TABLE (
    reservations BIGINT, released_usd NUMERIC, day_usd NUMERIC, month_usd NUMERIC, applied_usd NUMERIC
)
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
#variable_conflict use_column
DECLARE
    n BIGINT;
    total NUMERIC;
    old_day NUMERIC;
    v_min_age NUMERIC;
BEGIN
    SELECT l.value INTO v_min_age FROM hadavin_limits l WHERE l.name = 'min_expiry_age';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit min_expiry_age missing' USING ERRCODE = 'HD004'; END IF;
    WITH claimed AS (
        UPDATE spend_reservations
           SET status = 'settled', settled_usd = 0
         WHERE agent_id = p_agent AND day = p_day AND status = 'expired'
           AND closed_at <= pg_catalog.clock_timestamp()
                            - pg_catalog.make_interval(secs => v_min_age::double precision)
        RETURNING reserved_usd
    )
    SELECT count(*), COALESCE(sum(reserved_usd), 0) INTO n, total FROM claimed;
    reservations := n;
    released_usd := total;
    IF n = 0 THEN
        SELECT s.usd INTO day_usd FROM spend s WHERE s.agent_id = p_agent AND s.day = p_day;
        SELECT m.usd INTO month_usd FROM spend_month m
         WHERE m.agent_id = p_agent AND m.month = pg_catalog.date_trunc('month', p_day)::date;
        applied_usd := 0;
        RETURN NEXT;
        RETURN;
    END IF;
    SELECT s.usd INTO old_day FROM spend s WHERE s.agent_id = p_agent AND s.day = p_day FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'spend counter row missing';
    END IF;
    UPDATE spend s SET usd = GREATEST(s.usd - total, 0)
     WHERE s.agent_id = p_agent AND s.day = p_day RETURNING s.usd INTO day_usd;
    applied_usd := old_day - day_usd;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'spend counter row missing';
    END IF;
    UPDATE spend_month m SET usd = GREATEST(m.usd - total, 0)
     WHERE m.agent_id = p_agent AND m.month = pg_catalog.date_trunc('month', p_day)::date RETURNING m.usd INTO month_usd;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'spend month counter row missing';
    END IF;
    RETURN NEXT;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_release_expired_spend(TEXT, DATE) FROM PUBLIC;

-- hadavin_purge_spend_reservations: delete the SETTLED rows closed before p_before (a settled row, or one released by
-- 0008: settled at 0). An expired hold nobody settled is KEPT: it is still booked and a late settle must find it.
CREATE OR REPLACE FUNCTION hadavin_purge_spend_reservations(p_before TIMESTAMPTZ)
RETURNS BIGINT
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
#variable_conflict use_column
DECLARE
    n BIGINT;
BEGIN
    IF p_before IS NULL OR NOT pg_catalog.isfinite(p_before) THEN
        RAISE EXCEPTION 'invalid argument: p_before' USING ERRCODE = '22023';
    END IF;
    DELETE FROM spend_reservations r WHERE r.status = 'settled' AND r.closed_at < p_before;
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_purge_spend_reservations(TIMESTAMPTZ) FROM PUBLIC;

-- hadavin_add_spend: a plain charge on the day and the month counter (two upserts, day then month); returns both totals.
CREATE OR REPLACE FUNCTION hadavin_add_spend(p_agent TEXT, p_day DATE, p_usd NUMERIC)
RETURNS TABLE (day_usd NUMERIC, month_usd NUMERIC)
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
#variable_conflict use_column
DECLARE
    v_max_amount NUMERIC;
    v_max_decimals NUMERIC;
    v_max_id NUMERIC;
    v_month DATE;
BEGIN
    SELECT l.value INTO v_max_amount FROM hadavin_limits l WHERE l.name = 'max_amount';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_amount missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_max_decimals FROM hadavin_limits l WHERE l.name = 'max_decimals';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_decimals missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_max_id FROM hadavin_limits l WHERE l.name = 'max_id_chars';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_id_chars missing' USING ERRCODE = 'HD004'; END IF;

    IF p_agent IS NULL OR pg_catalog.char_length(p_agent) NOT BETWEEN 1 AND v_max_id
       OR p_agent ~ E'[\\x01-\\x1f\\x7f-\\x9f]' THEN
        RAISE EXCEPTION 'invalid argument: p_agent' USING ERRCODE = '22023';
    END IF;
    IF p_day IS NULL OR NOT pg_catalog.isfinite(p_day) OR p_day < DATE '1970-01-01' OR p_day > DATE '9999-12-31' THEN
        RAISE EXCEPTION 'invalid argument: p_day' USING ERRCODE = '22023';
    END IF;
    IF p_usd IS NULL OR NOT (p_usd >= 0 AND p_usd < v_max_amount) OR pg_catalog.scale(p_usd) > v_max_decimals THEN
        RAISE EXCEPTION 'invalid argument: p_usd' USING ERRCODE = '22023';
    END IF;
    v_month := pg_catalog.date_trunc('month', p_day)::date;

    INSERT INTO spend AS s (agent_id, day, usd) VALUES (p_agent, p_day, p_usd)
    ON CONFLICT (agent_id, day) DO UPDATE SET usd = s.usd + EXCLUDED.usd
    RETURNING s.usd INTO day_usd;
    INSERT INTO spend_month AS m (agent_id, month, usd) VALUES (p_agent, v_month, p_usd)
    ON CONFLICT (agent_id, month) DO UPDATE SET usd = m.usd + EXCLUDED.usd
    RETURNING m.usd INTO month_usd;
    RETURN NEXT;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_add_spend(TEXT, DATE, NUMERIC) FROM PUBLIC;

-- Step 6 (caps out of the runtime's hands), ADDITIONS ONLY: the table of caps and the two functions around it. The
-- reserve function above takes 5 arguments (p_id, p_agent, p_day, p_usd, p_run_id) and reads its caps from this table.
-- hadavin_caps: one row per agent. Owner only: no role holds any right on it (`migrate` GRANTS row is all ""); the
-- definer functions below touch it as owner. The CHECKs are the part of the cap rule that is a property of the value
-- (>= 0 and finite; NaN sorts above every number, so it fails the second test); the scale limit comes from
-- hadavin_limits and is enforced inside hadavin_set_cap. NOT the amount window: a cap of 10 to the 30th is valid.
CREATE TABLE hadavin_caps (
    agent_id TEXT PRIMARY KEY,
    day_cap NUMERIC NOT NULL CHECK (day_cap >= 0 AND day_cap < 'Infinity'::numeric),
    month_cap NUMERIC NOT NULL CHECK (month_cap >= 0 AND month_cap < 'Infinity'::numeric),
    set_by TEXT NOT NULL,
    set_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
REVOKE ALL ON hadavin_caps FROM PUBLIC;

-- hadavin_set_cap: upsert the caps of one agent (the reset login runs it; the runtime cannot). Arguments are validated
-- inside: the agent id as in the other functions, both caps by the cap rule, p_by non-empty without control characters.
CREATE OR REPLACE FUNCTION hadavin_set_cap(p_agent TEXT, p_day_cap NUMERIC, p_month_cap NUMERIC, p_by TEXT)
RETURNS void
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
#variable_conflict use_column
DECLARE
    v_max_decimals NUMERIC;
    v_max_id NUMERIC;
BEGIN
    SELECT l.value INTO v_max_decimals FROM hadavin_limits l WHERE l.name = 'max_decimals';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_decimals missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_max_id FROM hadavin_limits l WHERE l.name = 'max_id_chars';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_id_chars missing' USING ERRCODE = 'HD004'; END IF;

    IF p_agent IS NULL OR pg_catalog.char_length(p_agent) NOT BETWEEN 1 AND v_max_id
       OR p_agent ~ E'[\\x01-\\x1f\\x7f-\\x9f]' THEN
        RAISE EXCEPTION 'invalid argument: p_agent' USING ERRCODE = '22023';
    END IF;
    IF p_by IS NULL OR pg_catalog.char_length(p_by) NOT BETWEEN 1 AND v_max_id
       OR p_by ~ E'[\\x01-\\x1f\\x7f-\\x9f]' THEN
        RAISE EXCEPTION 'invalid argument: p_by' USING ERRCODE = '22023';
    END IF;
    IF p_day_cap IS NULL OR NOT (p_day_cap >= 0 AND p_day_cap < 'Infinity'::numeric)
       OR pg_catalog.scale(p_day_cap) > v_max_decimals THEN
        RAISE EXCEPTION 'invalid argument: p_day_cap' USING ERRCODE = '22023';
    END IF;
    IF p_month_cap IS NULL OR NOT (p_month_cap >= 0 AND p_month_cap < 'Infinity'::numeric)
       OR pg_catalog.scale(p_month_cap) > v_max_decimals THEN
        RAISE EXCEPTION 'invalid argument: p_month_cap' USING ERRCODE = '22023';
    END IF;

    INSERT INTO hadavin_caps AS c (agent_id, day_cap, month_cap, set_by, set_at)
    VALUES (p_agent, p_day_cap, p_month_cap, p_by, pg_catalog.clock_timestamp())
    ON CONFLICT (agent_id) DO UPDATE
       SET day_cap = EXCLUDED.day_cap, month_cap = EXCLUDED.month_cap, set_by = EXCLUDED.set_by,
           set_at = EXCLUDED.set_at;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_set_cap(TEXT, NUMERIC, NUMERIC, TEXT) FROM PUBLIC;

-- hadavin_cap_matches: read-only comparison. Says whether the supplied pair equals the stored one: 'same', 'differs',
-- or 'missing' (no row). It reveals nothing but that, gives no table right and changes nothing. VOLATILE like the others.
CREATE OR REPLACE FUNCTION hadavin_cap_matches(p_agent TEXT, p_day_cap NUMERIC, p_month_cap NUMERIC)
RETURNS TEXT
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
#variable_conflict use_column
DECLARE
    v_max_decimals NUMERIC;
    v_max_id NUMERIC;
    rec RECORD;
BEGIN
    SELECT l.value INTO v_max_decimals FROM hadavin_limits l WHERE l.name = 'max_decimals';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_decimals missing' USING ERRCODE = 'HD004'; END IF;
    SELECT l.value INTO v_max_id FROM hadavin_limits l WHERE l.name = 'max_id_chars';
    IF NOT FOUND THEN RAISE EXCEPTION 'limit max_id_chars missing' USING ERRCODE = 'HD004'; END IF;

    IF p_agent IS NULL OR pg_catalog.char_length(p_agent) NOT BETWEEN 1 AND v_max_id
       OR p_agent ~ E'[\\x01-\\x1f\\x7f-\\x9f]' THEN
        RAISE EXCEPTION 'invalid argument: p_agent' USING ERRCODE = '22023';
    END IF;
    IF p_day_cap IS NULL OR NOT (p_day_cap >= 0 AND p_day_cap < 'Infinity'::numeric)
       OR pg_catalog.scale(p_day_cap) > v_max_decimals THEN
        RAISE EXCEPTION 'invalid argument: p_day_cap' USING ERRCODE = '22023';
    END IF;
    IF p_month_cap IS NULL OR NOT (p_month_cap >= 0 AND p_month_cap < 'Infinity'::numeric)
       OR pg_catalog.scale(p_month_cap) > v_max_decimals THEN
        RAISE EXCEPTION 'invalid argument: p_month_cap' USING ERRCODE = '22023';
    END IF;

    SELECT c.day_cap, c.month_cap INTO rec FROM hadavin_caps c WHERE c.agent_id = p_agent;
    IF NOT FOUND THEN RETURN 'missing'; END IF;
    IF rec.day_cap = p_day_cap AND rec.month_cap = p_month_cap THEN RETURN 'same'; END IF;
    RETURN 'differs';
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_cap_matches(TEXT, NUMERIC, NUMERIC) FROM PUBLIC;
