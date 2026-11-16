-- HELD FILE 2 = PR DB-2 (NOT part of lead's answer Q34; needs its own lead yes, question L9). The lead gives it
-- the next free number at the move and adds the GRANTS entry for spend_decrease_log in the same move PR
-- (empty runtime list: Grant("table", "")).
-- (a) The key columns of both spend tables never change (a rewritten key hides a total from the decrease record
--     and from the readers, raw-pg-m1-v13.txt M1a). (b) every lowering of a total writes one row to a table the
--     runtime role cannot read or write; the trigger function is SECURITY DEFINER with a fixed search_path.
CREATE OR REPLACE FUNCTION spend_keep_keys() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public AS $f$
BEGIN
  IF TG_TABLE_NAME = 'spend' THEN
    IF NEW.agent_id IS DISTINCT FROM OLD.agent_id OR NEW.day IS DISTINCT FROM OLD.day THEN
      RAISE EXCEPTION 'spend key columns may not change' USING ERRCODE = '42501';
    END IF;
  ELSE
    IF NEW.agent_id IS DISTINCT FROM OLD.agent_id OR NEW.month IS DISTINCT FROM OLD.month THEN
      RAISE EXCEPTION 'spend key columns may not change' USING ERRCODE = '42501';
    END IF;
  END IF;
  RETURN NEW;
END $f$;
CREATE TRIGGER spend_keep_keys BEFORE UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();
CREATE TRIGGER spend_month_keep_keys BEFORE UPDATE ON spend_month FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();

CREATE TABLE spend_decrease_log (
  agent_id text NOT NULL,
  period   date NOT NULL,        -- the day (table spend) or the first of the month (table spend_month)
  scope    text NOT NULL,        -- 'spend' or 'spend_month'
  old_usd  numeric NOT NULL,
  new_usd  numeric NOT NULL,
  at       timestamptz NOT NULL DEFAULT clock_timestamp(),
  who      text NOT NULL DEFAULT session_user
);
CREATE INDEX spend_decrease_log_by_agent ON spend_decrease_log (agent_id, period, at);
CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public AS $f$
BEGIN
  IF TG_TABLE_NAME = 'spend' THEN
    INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES (OLD.agent_id, OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd);
  ELSE
    INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES (OLD.agent_id, OLD.month, TG_TABLE_NAME, OLD.usd, NEW.usd);
  END IF;
  RETURN NULL;
END $f$;
REVOKE ALL ON FUNCTION spend_log_decrease() FROM PUBLIC;
CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW WHEN (NEW.usd < OLD.usd) EXECUTE FUNCTION spend_log_decrease();
CREATE TRIGGER spend_month_log_decrease AFTER UPDATE ON spend_month FOR EACH ROW WHEN (NEW.usd < OLD.usd) EXECUTE FUNCTION spend_log_decrease();
