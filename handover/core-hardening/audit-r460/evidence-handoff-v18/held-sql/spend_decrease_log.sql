-- HELD FILE 2 (v17) = PR DB-2 (NOT part of lead's answer Q34; needs the OWNER's own yes, question L9). The lead gives it
-- the next free number at the move and adds the GRANTS entries for spend_decrease_log AND kill_switch_log in the same
-- move PR: an EMPTY runtime list and the audit-reader flag, Grant("table", "", audit_read=True) (question L12; NOT
-- portal=True). v16 adds to v15: (c) a record of every kill-switch change, (d) append-only triggers on both records.
-- v17 adds to v16: the lock_timeout line below (v16 had none although the text said it did), and the kill-switch log
-- trigger never blocks a switch ON (security minor m5). v18: the handler also catches a cancelled statement (57014), which
-- `WHEN OTHERS` alone does not, so a statement_timeout cannot block a switch ON either (minor m4).
-- Needs Postgres 14 or newer: the trigger condition below reads 'Infinity'::numeric (independent of L7).
-- (a) The key columns of both spend tables never change (a rewritten key hides a total from the decrease record
--     and from the readers). (b) every lowering of a total writes one row to a table the runtime role cannot write;
--     the trigger function is SECURITY DEFINER and is owned by the migration role (a plain non-superuser role).
-- Security blocker B1 (v13): the function names its log table with the schema of the table that fired it
-- (TG_TABLE_SCHEMA, quoted with %I) and its search_path is pg_catalog then pg_temp LAST. Postgres searches the
-- session's temporary schema FIRST for a relation name unless pg_temp is named in the path, and PUBLIC may create
-- temporary tables, so a runtime role could create a temporary table of the same name and every lowering wrote its
-- row there (evidence-handoff-v14/raw-pg-tmp-v14.txt, test T0; v16: raw-pg-v16-run1.txt F1 and F2).
-- ADD CONSTRAINT-style locks: CREATE TRIGGER takes SHARE ROW EXCLUSIVE on the table, which conflicts with a writer; the
-- runner sets no lock_timeout, so this file sets one for its own transaction: it fails after 5 seconds and rolls back
-- instead of queueing every spend call.
SET LOCAL lock_timeout = '5s';
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
-- not-a-number for the same reason (evidence-handoff-v14/raw-pg-tmp-v14.txt, test T6; v16: raw-pg-v16-run1.txt E12).
CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW
  WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd < OLD.usd OR NEW.usd >= 'Infinity'::numeric))
  EXECUTE FUNCTION spend_log_decrease();
CREATE TRIGGER spend_month_log_decrease AFTER UPDATE ON spend_month FOR EACH ROW
  WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd < OLD.usd OR NEW.usd >= 'Infinity'::numeric))
  EXECUTE FUNCTION spend_log_decrease();

-- (c) v16, security major 5: every change of the kill switch ("on" turning on or off) writes one row to a table the
-- runtime role cannot write or read. Same hardening as spend_log_decrease(): SECURITY DEFINER, search_path with pg_temp
-- last, the schema taken from TG_TABLE_SCHEMA with %I, EXECUTE revoked from PUBLIC. `who` is the login role that did it.
CREATE TABLE kill_switch_log (
  at     timestamptz NOT NULL DEFAULT clock_timestamp(),
  old_on boolean NOT NULL,
  new_on boolean NOT NULL,
  old_by text,
  new_by text,
  who    text NOT NULL DEFAULT session_user
);
CREATE INDEX kill_switch_log_by_time ON kill_switch_log (at);
-- v17, security minor m5 (decided): a failing record must never stop a switch ON (stopping is the safe direction and
-- must always work). A switch OFF still fails when the record cannot be written (fail closed: no unrecorded release).
CREATE OR REPLACE FUNCTION kill_switch_log_change() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp AS $f$
BEGIN
  BEGIN
    EXECUTE format('INSERT INTO %I.kill_switch_log (old_on, new_on, old_by, new_by) VALUES ($1, $2, $3, $4)', TG_TABLE_SCHEMA)
      USING OLD."on", NEW."on", OLD."by", NEW."by";
  EXCEPTION WHEN OTHERS OR QUERY_CANCELED THEN
    IF NEW."on" THEN
      RAISE WARNING 'kill_switch_log not written (%): the switch ON is kept', SQLSTATE;
    ELSE
      RAISE;
    END IF;
  END;
  RETURN NULL;
END $f$;
REVOKE ALL ON FUNCTION kill_switch_log_change() FROM PUBLIC;
CREATE TRIGGER kill_switch_log_change AFTER UPDATE ON kill_switch FOR EACH ROW
  WHEN (NEW."on" IS DISTINCT FROM OLD."on")
  EXECUTE FUNCTION kill_switch_log_change();

-- (d) v16, security minor 4: both records are append-only for EVERY role, the owner included: UPDATE, DELETE and
-- TRUNCATE are refused with 42501. The owner can still DROP the trigger or DISABLE it and a superuser can bypass
-- triggers: this makes edits visible to a reviewer and impossible by accident, it is not protection against the owner
-- of the database. No retention delete exists (L16, owner): if the owner ever says yes, a reviewed file replaces
-- these triggers for that one purpose.
CREATE OR REPLACE FUNCTION audit_log_append_only() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, pg_temp AS $f$
BEGIN
  RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = '42501';
END $f$;
CREATE TRIGGER spend_decrease_log_append_only BEFORE UPDATE OR DELETE ON spend_decrease_log FOR EACH ROW
  EXECUTE FUNCTION audit_log_append_only();
CREATE TRIGGER spend_decrease_log_no_truncate BEFORE TRUNCATE ON spend_decrease_log FOR EACH STATEMENT
  EXECUTE FUNCTION audit_log_append_only();
CREATE TRIGGER kill_switch_log_append_only BEFORE UPDATE OR DELETE ON kill_switch_log FOR EACH ROW
  EXECUTE FUNCTION audit_log_append_only();
CREATE TRIGGER kill_switch_log_no_truncate BEFORE TRUNCATE ON kill_switch_log FOR EACH STATEMENT
  EXECUTE FUNCTION audit_log_append_only();
