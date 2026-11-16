-- HELD FILE 3 (v22) = PR DB-3 (NOT part of lead's answer Q34; needs the OWNER's own yes, question L22). Design of L-2: spend totals can only fall through a settle.
-- READ FIRST: who may call what is decided in ONE place, section 5.6c item 5 of CORE-PR-HANDOFF-v22.md (grant table). This file creates the functions and revokes PUBLIC;
-- it grants nothing (role names come from config; the move PR sets GRANTS). The grant table as it stands: the runtime role has SELECT on spend, spend_month and kill_switch and
-- EXECUTE on spend_reserve and spend_settle; the operator role has EXECUTE on kill_switch_engage and kill_switch_release (lead choice L22b: the runtime role may also engage);
-- PUBLIC has nothing. Older comments of this file that said otherwise were wrong and are gone.
-- Needs Postgres 14 or newer: the function bodies use BEGIN ATOMIC, which Postgres parses AND binds at creation time, so a SECURITY DEFINER body names its tables by object,
-- never by a name searched at call time. The objects are bound with the search_path of the session that creates them (the migration session); the start-up check
-- (5.6c item 4) verifies that every table a function uses is in the function's own schema.
-- What it closes: (1) a negative change to a spend total can only come from a settle and is bounded by the reservation of the same agent-day made earlier (open_usd), so
-- settled history can no longer be erased; (2) the kill switch is engaged by one function and released by another; `by` is always session_user; (3) month is DERIVED from
-- the day inside the functions; usd and open_usd are below 1e12 (US$ one trillion, my number, a sanity ceiling, owner may change it before the yes; it also refuses NaN);
-- agent ids match the ASCII allow-list `^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$` (1 to 200 characters; the lead checks it against the real agent names); a day or month must lie
-- in 2020-01-01 to 2099-12-31 (my window). The file refuses at APPLY time (23514, whole transaction rolls back) when an old row breaks a rule; pre-check before the cutover:
-- SELECT count(*) FROM spend WHERE agent_id !~ '^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$' OR day < DATE '2020-01-01' OR day >= DATE '2100-01-01' (same for spend_month); it must be 0.
-- Zero and refused amounts (v22, security minor m1): spend_reserve with p_worst NULL, 0, negative or an infinity returns NO row and writes nothing (a zero-cost call is refused: the
-- store must not call reserve for 0); spend_settle with NULL or a negative amount returns NO row and writes nothing; spend_settle(0, 0) on an existing agent-day returns the
-- unchanged row and books nothing. The store code treats an empty result as an error (test E0-F5, on an agent-day that has rows).
-- v22 (security major MJ1): the final SELECT of spend_reserve has the same guard as its two INSERTs. In v21 a reserve that the guard rejected still returned the unchanged totals when the
-- agent-day had rows, so the store read it as reserved, made the paid call, and the settle was refused: spend was never booked.
-- What it does NOT close (stated, with the control for each): (a) a hostile runtime can reserve up to the ceiling and settle it at 0, so it can under-report by any amount it reserved;
-- the control is the invoice comparison (7.3) and the call cap in our code, not this file; (b) the functions take the agent id as a plain argument, so one login that holds the
-- runtime role can settle (give back) another agent's open reservation (one runtime login for all agents; per-agent logins are L-4); (c) the owner of the functions and a superuser are
-- not stopped (the dedicated owner role is lead choice L26, 5.6c item 8); (d) a settle with actual above worst can raise a total (safe direction; it can only over-report);
-- (e) names that differ only in case or by an inner character of the allow-list are separate agent ids. PSEUDO AGENT IDS `-cli` and `-unattributed:<agent>` start with `-`, which the
-- agent-id rule refuses (23514): a store call under such an id fails closed and an existing row with such an id makes the file refuse at apply time. Lead choice L26b (5.6c item 8).
-- Cutover: existing rows get open_usd = 0 (the file cannot know what is open), so a reservation that is open at the cutover cannot be settled afterwards (23514, safe direction: the
-- total stays high). The cutover is drained: kill switch ON and no call in flight (5.6c item 9). Lock time: statement_timeout is a limit PER STATEMENT; the file has TEN ALTER TABLE lines
-- (five per table: one column, four constraints), each may hold its table lock for up to 60 seconds, so the worst case is about 10 minutes; the scans are over two small tables.
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';
ALTER TABLE spend ADD COLUMN open_usd numeric NOT NULL DEFAULT 0;
ALTER TABLE spend ADD CONSTRAINT spend_open_ok CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric);
ALTER TABLE spend ADD CONSTRAINT spend_guarded_ok CHECK (usd >= 0 AND usd < 1000000000000::numeric);
ALTER TABLE spend ADD CONSTRAINT spend_agent_len CHECK (agent_id ~ '^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$');
ALTER TABLE spend ADD CONSTRAINT spend_day_window CHECK (day >= DATE '2020-01-01' AND day < DATE '2100-01-01');
ALTER TABLE spend_month ADD COLUMN open_usd numeric NOT NULL DEFAULT 0;
ALTER TABLE spend_month ADD CONSTRAINT spend_month_open_ok CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric);
ALTER TABLE spend_month ADD CONSTRAINT spend_month_guarded_ok CHECK (usd >= 0 AND usd < 1000000000000::numeric);
ALTER TABLE spend_month ADD CONSTRAINT spend_month_agent_len CHECK (agent_id ~ '^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$');
ALTER TABLE spend_month ADD CONSTRAINT spend_month_window CHECK (month >= DATE '2020-01-01' AND month < DATE '2100-01-01');

-- Reserve: adds the worst case to the total and to the open reservation of the day row and of the month row (the month is
-- the first day of the month of p_day).
CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst numeric)
RETURNS TABLE (day_usd numeric, month_usd numeric)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  INSERT INTO spend (agent_id, day, usd, open_usd) SELECT p_agent, p_day, p_worst, p_worst WHERE p_worst > 0
    ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd, open_usd = spend.open_usd + EXCLUDED.open_usd;
  INSERT INTO spend_month (agent_id, month, usd, open_usd) SELECT p_agent, date_trunc('month', p_day)::date, p_worst, p_worst WHERE p_worst > 0
    ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd, open_usd = spend_month.open_usd + EXCLUDED.open_usd;
  SELECT d.usd, m.usd FROM spend d, spend_month m
    WHERE d.agent_id = p_agent AND d.day = p_day AND m.agent_id = p_agent AND m.month = date_trunc('month', p_day)::date
      AND p_worst > 0;
END;
-- Settle: replaces one earlier reserve of p_worst by the actual cost (a give-back is p_actual = 0). It refuses
-- (23514) when p_worst is larger than what is open for that agent-day or month, so the total can fall by at most
-- the open reservation and never below the money already settled. Each row is changed only when the other row exists too, so a settle for a day that has no row changes nothing at all and
-- returns no row; the store code (L-2) must treat an empty result as an error.
CREATE OR REPLACE FUNCTION spend_settle(p_agent text, p_day date, p_worst numeric, p_actual numeric)
RETURNS TABLE (day_usd numeric, month_usd numeric)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
BEGIN ATOMIC
  UPDATE spend SET usd = usd - p_worst + p_actual, open_usd = open_usd - p_worst
    WHERE agent_id = p_agent AND day = p_day AND p_worst >= 0 AND p_actual >= 0
      AND EXISTS (SELECT 1 FROM spend_month y WHERE y.agent_id = p_agent AND y.month = date_trunc('month', p_day)::date);
  UPDATE spend_month SET usd = usd - p_worst + p_actual, open_usd = open_usd - p_worst
    WHERE agent_id = p_agent AND month = date_trunc('month', p_day)::date AND p_worst >= 0 AND p_actual >= 0
      AND EXISTS (SELECT 1 FROM spend x WHERE x.agent_id = p_agent AND x.day = p_day);
  SELECT d.usd, m.usd FROM spend d, spend_month m
    WHERE d.agent_id = p_agent AND d.day = p_day AND m.agent_id = p_agent AND m.month = date_trunc('month', p_day)::date
      AND p_worst >= 0 AND p_actual >= 0;
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
