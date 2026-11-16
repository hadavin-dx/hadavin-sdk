-- HELD FILE 3 (v18) = PR DB-3 (NOT part of lead's answer Q34; needs the OWNER's own yes, question L22). Design of L-2
-- (security major M1 of the v16 review). Needs Postgres 14 or newer: the function bodies use BEGIN ATOMIC, which Postgres
-- parses AND binds at creation time, so a SECURITY DEFINER body names its tables by object, never by a name searched at
-- call time (no search_path or temporary-table lookup is possible, and no schema name is written into this file). The
-- objects are bound with the search_path of the session that creates them (the migration session): the start-up check
-- of 5.6 item 1(o2) verifies that every table a function uses is in the function's own schema (v18, minor m7).
-- What it closes: (1) a negative change to a spend total can only come from a settle and is bounded by the reservation
-- of the same agent-day made earlier (`open_usd`), so settled history can no longer be erased; (2) the kill switch is
-- engaged by one function and released by another that only the operator role may run; `by` is always session_user.
-- v18: the month is DERIVED from the day inside the functions (v17 took it as a second input, so a caller could pick any
-- month); `usd` and `open_usd` are below 1e12 (US$ one trillion, my number, a sanity ceiling, owner may change it before
-- the yes: it replaces the v17 'Infinity' check and also refuses NaN); agent ids are 1 to 200 characters (NOT VALID: it
-- checks new rows only, so an old row never blocks the file); engage no longer rewrites `by` and `ts` when the switch is
-- already ON and creates the row when it is missing (v17 did nothing silently); release changes a row only if it is ON.
-- What it does NOT close (stated, with the control for each): (a) a hostile runtime can reserve up to the ceiling and settle
-- it at 0, so it can under-report by any amount it reserved; the control is the invoice comparison (7.3) and the call cap in our
-- code, not this file; (b) the functions take the agent id as a plain argument, so one login that holds the runtime role can
-- settle (give back) another agent's open reservation: the database has one runtime login for all agents (5.6 item 5), the settled
-- money stays safe, the control is the invoice comparison; per-agent logins are L-4; (c) the owner and a superuser are not stopped.
-- The role grants are NOT in this file (role names come from config): the move PR sets GRANTS so that the runtime role has SELECT
-- only on spend, spend_month and kill_switch and EXECUTE on spend_reserve, spend_settle and kill_switch_engage; the operator
-- role has EXECUTE on kill_switch_release and nothing else; PUBLIC has none (5.6 item 1(o2) says how migrate() re-applies them).
SET LOCAL lock_timeout = '5s';
ALTER TABLE spend ADD COLUMN open_usd numeric NOT NULL DEFAULT 0;
ALTER TABLE spend ADD CONSTRAINT spend_open_ok CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric);
ALTER TABLE spend ADD CONSTRAINT spend_guarded_ok CHECK (usd >= 0 AND usd < 1000000000000::numeric);
ALTER TABLE spend ADD CONSTRAINT spend_agent_len CHECK (length(agent_id) BETWEEN 1 AND 200) NOT VALID;
ALTER TABLE spend_month ADD COLUMN open_usd numeric NOT NULL DEFAULT 0;
ALTER TABLE spend_month ADD CONSTRAINT spend_month_open_ok CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric);
ALTER TABLE spend_month ADD CONSTRAINT spend_month_guarded_ok CHECK (usd >= 0 AND usd < 1000000000000::numeric);
ALTER TABLE spend_month ADD CONSTRAINT spend_month_agent_len CHECK (length(agent_id) BETWEEN 1 AND 200) NOT VALID;

-- Reserve: adds the worst case to the total and to the open reservation of the day row and of the month row (the month is
-- the first day of the month of p_day).
CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst numeric)
RETURNS TABLE (day_usd numeric, month_usd numeric)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  INSERT INTO spend (agent_id, day, usd, open_usd) VALUES (p_agent, p_day, p_worst, p_worst)
    ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd, open_usd = spend.open_usd + EXCLUDED.open_usd;
  INSERT INTO spend_month (agent_id, month, usd, open_usd) VALUES (p_agent, date_trunc('month', p_day)::date, p_worst, p_worst)
    ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd, open_usd = spend_month.open_usd + EXCLUDED.open_usd;
  SELECT d.usd, m.usd FROM spend d, spend_month m
    WHERE d.agent_id = p_agent AND d.day = p_day AND m.agent_id = p_agent AND m.month = date_trunc('month', p_day)::date;
END;
-- Settle: replaces one earlier reserve of p_worst by the actual cost (a give-back is p_actual = 0). It refuses
-- (23514) when p_worst is larger than what is open for that agent-day or month, so the total can fall by at most
-- the open reservation and never below the money already settled.
CREATE OR REPLACE FUNCTION spend_settle(p_agent text, p_day date, p_worst numeric, p_actual numeric)
RETURNS TABLE (day_usd numeric, month_usd numeric)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  UPDATE spend SET usd = usd - p_worst + p_actual, open_usd = open_usd - p_worst
    WHERE agent_id = p_agent AND day = p_day AND p_worst >= 0 AND p_actual >= 0;
  UPDATE spend_month SET usd = usd - p_worst + p_actual, open_usd = open_usd - p_worst
    WHERE agent_id = p_agent AND month = date_trunc('month', p_day)::date AND p_worst >= 0 AND p_actual >= 0;
  SELECT d.usd, m.usd FROM spend d, spend_month m
    WHERE d.agent_id = p_agent AND d.day = p_day AND m.agent_id = p_agent AND m.month = date_trunc('month', p_day)::date;
END;
-- Kill switch: engage (any caller that may run it: stopping is the safe direction) and release (operator only).
-- `by` is session_user, never a caller-supplied value. Engage creates the row when it is missing (a missing row is read
-- as "stopped" by the store, so this only makes it visible) and does not touch `by` and `ts` of a switch that is already ON.
CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS void
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  INSERT INTO kill_switch (id, schema_version, "on", "by", ts) VALUES (1, 1, true, session_user, clock_timestamp())
    ON CONFLICT (id) DO UPDATE SET "on" = true, "by" = session_user, ts = clock_timestamp() WHERE kill_switch."on" = false;
END;
CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  UPDATE kill_switch SET "on" = false, "by" = session_user, ts = clock_timestamp() WHERE id = 1 AND "on" = true;
END;
REVOKE ALL ON FUNCTION spend_reserve(text, date, numeric) FROM PUBLIC;
REVOKE ALL ON FUNCTION spend_settle(text, date, numeric, numeric) FROM PUBLIC;
REVOKE ALL ON FUNCTION kill_switch_engage() FROM PUBLIC;
REVOKE ALL ON FUNCTION kill_switch_release() FROM PUBLIC;
