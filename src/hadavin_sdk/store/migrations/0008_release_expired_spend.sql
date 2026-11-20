-- Release of expired spend holds (step F-store, ORDER 020 M1) and the closed_at index of the purge.
-- hadavin_release_expired_spend(agent, day) is the ONLY way the booked amount of an expired hold goes down (a runtime
-- login cannot lower it with its own UPDATE: the guard trigger of 0010 refuses it, proven by tests/test_money_guard_pg.py). It is
-- owned by the migration owner (SECURITY DEFINER), so the release login needs no right on the money tables
-- at all: `migrate --release-role` grants it EXECUTE on this one function and the audit append path, and nothing
-- else. Nobody else may run it: EXECUTE is taken from PUBLIC here, and `migrate` refuses a run where the
-- runtime, portal, purge or reset role can run it.
-- One statement sequence in one transaction (a function body is one): lock the EXPIRED rows of the named agent
-- and day and mark them settled at 0 (the claim: a late settle now returns the stored row and changes nothing),
-- then lower the day counter and the month counter by the same sum, never below zero (applied_usd is what the day
-- counter really fell by, so a drift shows). Open rows (live holds),
-- settled rows and the rows of any other day or agent are not touched. The order is row, day, month, the order of
-- settle and reserve, so there is no lock cycle. A missing counter row aborts the whole release.
CREATE OR REPLACE FUNCTION hadavin_release_expired_spend(p_agent TEXT, p_day DATE)
RETURNS TABLE (
    reservations BIGINT, released_usd NUMERIC, day_usd NUMERIC, month_usd NUMERIC, applied_usd NUMERIC
)
LANGUAGE plpgsql
SECURITY DEFINER
-- Placeholder pin: `migrate` re-pins it to pg_catalog, <this schema>, pg_temp (ALTER FUNCTION), because this file
-- cannot know the schema. pg_temp must stay LAST or a temp table of the caller shadows the money tables.
SET search_path = pg_catalog, pg_temp
AS $fn$
DECLARE
    n BIGINT;
    total NUMERIC;
    old_day NUMERIC;
BEGIN
    WITH claimed AS (
        UPDATE spend_reservations
           SET status = 'settled', settled_usd = 0
         WHERE agent_id = p_agent AND day = p_day AND status = 'expired'
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
    -- the amount the day counter really fell by; below `released_usd` when the counter was already lower (drift)
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

-- The purge deletes closed rows by closed_at; without an index it reads the whole table.
CREATE INDEX spend_reservations_closed ON spend_reservations (closed_at) WHERE status <> 'open';
