-- HELD FILE 3 (v17) = PR DB-3 (NOT part of lead's answer Q34; needs the OWNER's own yes, question L22). Design of L-2
-- (security major M1 of the v16 review). Needs Postgres 14 or newer: the function bodies use BEGIN ATOMIC, which Postgres
-- parses AND binds at creation time, so a SECURITY DEFINER body names its tables by object, never by a name searched at
-- call time (no search_path or temporary-table lookup is possible, and no schema name is written into this file).
-- What it closes: (1) a negative change to a spend total can only come from a settle and is bounded by the reservation
-- the same agent-day made earlier (`open_usd`), so settled history can no longer be erased; (2) the kill switch is
-- engaged by one function and released by another that only the operator role may run; `by` is always session_user.
-- What it does NOT close: a runtime that lies about the actual cost of a call can still under-report by at most the
-- amount it reserved for that call (the reserve itself is bounded by the call cap in our code); that is the invoice
-- comparison's job (7.3). The role grants are NOT in this file (role names come from config): the move PR changes
-- GRANTS so the runtime role has SELECT only on spend, spend_month and kill_switch, EXECUTE on the three functions
-- spend_reserve, spend_settle and kill_switch_engage, and the operator role has EXECUTE on kill_switch_release.
SET LOCAL lock_timeout = '5s';
ALTER TABLE spend ADD COLUMN open_usd numeric NOT NULL DEFAULT 0;
ALTER TABLE spend ADD CONSTRAINT spend_open_ok CHECK (open_usd >= 0 AND open_usd < 'Infinity'::numeric);
ALTER TABLE spend ADD CONSTRAINT spend_guarded_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);
ALTER TABLE spend_month ADD COLUMN open_usd numeric NOT NULL DEFAULT 0;
ALTER TABLE spend_month ADD CONSTRAINT spend_month_open_ok CHECK (open_usd >= 0 AND open_usd < 'Infinity'::numeric);
ALTER TABLE spend_month ADD CONSTRAINT spend_month_guarded_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);

-- Reserve: adds the worst case to the total and to the open reservation of the day and of the month (both rows).
CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_month date, p_worst numeric)
RETURNS TABLE (day_usd numeric, month_usd numeric)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  INSERT INTO spend (agent_id, day, usd, open_usd) VALUES (p_agent, p_day, p_worst, p_worst)
    ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd, open_usd = spend.open_usd + EXCLUDED.open_usd;
  INSERT INTO spend_month (agent_id, month, usd, open_usd) VALUES (p_agent, p_month, p_worst, p_worst)
    ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd, open_usd = spend_month.open_usd + EXCLUDED.open_usd;
  SELECT d.usd, m.usd FROM spend d, spend_month m
    WHERE d.agent_id = p_agent AND d.day = p_day AND m.agent_id = p_agent AND m.month = p_month;
END;
-- Settle: replaces one earlier reserve of p_worst by the actual cost (a give-back is p_actual = 0). It refuses
-- (23514) when p_worst is larger than what is open for that agent-day or month, so the total can fall by at most
-- the open reservation and never below the money already settled.
CREATE OR REPLACE FUNCTION spend_settle(p_agent text, p_day date, p_month date, p_worst numeric, p_actual numeric)
RETURNS TABLE (day_usd numeric, month_usd numeric)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  UPDATE spend SET usd = usd - p_worst + p_actual, open_usd = open_usd - p_worst
    WHERE agent_id = p_agent AND day = p_day AND p_worst >= 0 AND p_actual >= 0;
  UPDATE spend_month SET usd = usd - p_worst + p_actual, open_usd = open_usd - p_worst
    WHERE agent_id = p_agent AND month = p_month AND p_worst >= 0 AND p_actual >= 0;
  SELECT d.usd, m.usd FROM spend d, spend_month m
    WHERE d.agent_id = p_agent AND d.day = p_day AND m.agent_id = p_agent AND m.month = p_month;
END;
-- Kill switch: engage (any caller that may run it: stopping is the safe direction) and release (operator only).
-- `by` is session_user, never a caller-supplied value; the row exists from migration 0003 (an UPDATE only).
CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS void
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  UPDATE kill_switch SET "on" = true, "by" = session_user, ts = clock_timestamp() WHERE id = 1;
END;
CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  UPDATE kill_switch SET "on" = false, "by" = session_user, ts = clock_timestamp() WHERE id = 1;
END;
REVOKE ALL ON FUNCTION spend_reserve(text, date, date, numeric) FROM PUBLIC;
REVOKE ALL ON FUNCTION spend_settle(text, date, date, numeric, numeric) FROM PUBLIC;
REVOKE ALL ON FUNCTION kill_switch_engage() FROM PUBLIC;
REVOKE ALL ON FUNCTION kill_switch_release() FROM PUBLIC;
