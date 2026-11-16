-- HELD FILE 2 = PR DB-2 (NOT part of lead's answer Q34; needs the OWNER's own yes, question L9). The lead gives it
-- the next free number at the move and adds the GRANTS entry for spend_decrease_log in the same move PR: an EMPTY
-- runtime list and the new audit-reader flag, Grant("table", "", audit_read=True) (question L12; NOT portal=True).
-- Needs Postgres 14 or newer: the trigger condition below reads 'Infinity'::numeric (independent of L7).
-- (a) The key columns of both spend tables never change (a rewritten key hides a total from the decrease record
--     and from the readers). (b) every lowering of a total writes one row to a table the runtime role cannot write;
--     the trigger function is SECURITY DEFINER and is owned by the migration role (a plain non-superuser role).
-- Security blocker B1 (v13): the function names its log table with the schema of the table that fired it
-- (TG_TABLE_SCHEMA, quoted with %I) and its search_path is pg_catalog then pg_temp LAST. Postgres searches the
-- session's temporary schema FIRST for a relation name unless pg_temp is named in the path, and PUBLIC may create
-- temporary tables, so a runtime role could create a temporary table of the same name and every lowering wrote its
-- row there (evidence-handoff-v14/raw-pg-tmp-v14.txt, test T0).
-- WARNING for editors: spend_keep_keys() reads NEW.day for the table `spend` and NEW.month for every OTHER table.
-- Attaching it to a third table breaks every UPDATE of that table (no such column). Give a third table its own function.
CREATE OR REPLACE FUNCTION spend_keep_keys() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, pg_temp AS $f$
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
SET search_path = pg_catalog, pg_temp AS $f$
BEGIN
  IF TG_TABLE_NAME = 'spend' THEN
    EXECUTE format('INSERT INTO %I.spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES ($1, $2, $3, $4, $5)', TG_TABLE_SCHEMA)
      USING OLD.agent_id, OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd;
  ELSE
    EXECUTE format('INSERT INTO %I.spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES ($1, $2, $3, $4, $5)', TG_TABLE_SCHEMA)
      USING OLD.agent_id, OLD.month, TG_TABLE_NAME, OLD.usd, NEW.usd;
  END IF;
  RETURN NULL;
END $f$;
REVOKE ALL ON FUNCTION spend_log_decrease() FROM PUBLIC;
-- Security minor 3 (v13): log a lowering, and also a total that becomes not-a-number or infinite (a bad value that
-- DB-1 would refuse; DB-2 may be applied alone). In Postgres a not-a-number value sorts ABOVE every number, so
-- NEW.usd >= 'Infinity' is true for both; the formula NOT (NEW.usd > OLD.usd) suggested by the review would miss
-- not-a-number for the same reason (evidence-handoff-v14/raw-pg-tmp-v14.txt, test T6; v15: raw-pg-v15.txt).
CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW
  WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd < OLD.usd OR NEW.usd >= 'Infinity'::numeric))
  EXECUTE FUNCTION spend_log_decrease();
CREATE TRIGGER spend_month_log_decrease AFTER UPDATE ON spend_month FOR EACH ROW
  WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd < OLD.usd OR NEW.usd >= 'Infinity'::numeric))
  EXECUTE FUNCTION spend_log_decrease();
