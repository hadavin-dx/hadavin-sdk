-- Stop state hardening (step B, E12 Medium 3, Medium 4, Low 6). Schema only: the code that writes the reset
-- record and reads the watermark is a follow-up (tickets/B-stop-state.md, "B7 follow-up").
--
-- (1) The reset's own audit record. `kill_switch_resets` holds one row per reset, written ONLY by the reset role
-- (INSERT; the runtime role holds nothing on it). It is the record that survives if the audit chain row of the reset
-- is lost or planted around: `audit_seq` points at the chain row when there is one. Append-only like the stop tables.
CREATE TABLE kill_switch_resets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "by"        TEXT,
    at          TIMESTAMPTZ NOT NULL DEFAULT now() CHECK (isfinite(at) AND at BETWEEN '2000-01-01' AND '2100-01-01'),
    cleared_ids UUID[] NOT NULL DEFAULT '{}',
    audit_seq   BIGINT
);

-- (2) A watermark so the gate read need not scan every stop ever made. One row (id is always true). The runtime
-- role READS it; only the reset role writes it: `through` is the newest stop time the last reset cleared. The
-- trigger below refuses a move backwards (a lower watermark would show cleared stops to the reader as open) and a
-- delete. Reader change: follow-up.
CREATE TABLE kill_switch_watermark (
    id      BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (id),
    through TIMESTAMPTZ NOT NULL CHECK (isfinite(through) AND through BETWEEN '2000-01-01' AND '2100-01-01'),
    at      TIMESTAMPTZ NOT NULL DEFAULT now() CHECK (isfinite(at) AND at BETWEEN '2000-01-01' AND '2100-01-01')
);
-- the "open stops" read: WHERE ts > watermark ORDER BY ts, served by an index instead of a scan
CREATE INDEX kill_switch_stops_by_ts ON kill_switch_stops (ts);

-- (3) Planted years (0100 BC, 20000) are refused on the stop tables. isfinite() alone left them valid.
-- The constraints are NOT VALID: they are enforced for every NEW row, but the rows already there are not checked, so
-- this migration cannot fail on a database that already holds a planted ts (the stop tables are append-only: such a row
-- could not be removed below a superuser, and the upgrade would be stuck). An operator validates later, once any such
-- row has been dealt with (docs/stop-state-runbook.md, "After the upgrade"):
--   ALTER TABLE kill_switch_stops  VALIDATE CONSTRAINT kill_switch_stops_ts_range;
--   ALTER TABLE kill_switch_clears VALIDATE CONSTRAINT kill_switch_clears_ts_range;
-- (VALIDATE fails, naming the constraint, while a bad row exists; it takes a SHARE UPDATE EXCLUSIVE lock only.)
-- ADD CONSTRAINT takes a short ACCESS EXCLUSIVE lock on the (small) stop tables, and so does the index above.
ALTER TABLE kill_switch_stops ADD CONSTRAINT kill_switch_stops_ts_range
    CHECK (ts BETWEEN '2000-01-01' AND '2100-01-01') NOT VALID;
ALTER TABLE kill_switch_clears ADD CONSTRAINT kill_switch_clears_ts_range
    CHECK (ts BETWEEN '2000-01-01' AND '2100-01-01') NOT VALID;

CREATE OR REPLACE TRIGGER kill_switch_resets_append_only BEFORE UPDATE OR DELETE ON kill_switch_resets
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_resets_no_truncate BEFORE TRUNCATE ON kill_switch_resets
    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();

CREATE OR REPLACE FUNCTION hadavin_watermark_guard() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, pg_temp
AS $fn$
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.through >= OLD.through THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'the kill switch watermark only moves forward';
END
$fn$;
CREATE OR REPLACE TRIGGER kill_switch_watermark_guard BEFORE UPDATE OR DELETE ON kill_switch_watermark
    FOR EACH ROW EXECUTE FUNCTION hadavin_watermark_guard();
CREATE OR REPLACE TRIGGER kill_switch_watermark_no_truncate BEFORE TRUNCATE ON kill_switch_watermark
    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();

-- (1b) The second guard for a planted audit seq, and the same for audit_checkpoints. The chain (audit/chain.py
-- `_append`) takes one advisory lock, reads the last row and inserts exactly last + 1 (1 for the first row), so exactly
-- last + 1 IS the rule of every legitimate writer, and a row with a huge or backward seq (which would wedge the chain:
-- every later append is last + 1 of the planted value) is refused. A CHECK range cannot say "last + 1", so this is a
-- trigger. A checkpoint (`checkpoint()`) signs the CURRENT HEAD: its seq is a row of audit_entries and its hash is that
-- row's hash, so any other checkpoint row (a planted huge seq stops all later signing, `signed_through()` is MAX(seq))
-- is refused. SECURITY INVOKER (every writer already holds SELECT on audit_entries). Search path: the table is
-- qualified from TG_TABLE_SCHEMA (not looked up through the path, so a TEMP TABLE of the caller cannot stand in), and
-- the placeholder pin below is re-pinned by `migrate` on every run to pg_catalog, <this schema>, pg_temp (temp LAST).
-- This is a tripwire for a naive plant, not a wall: a superuser or the table owner disables the trigger.
CREATE OR REPLACE FUNCTION hadavin_audit_seq_guard() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, pg_temp
AS $fn$
DECLARE
    last_seq BIGINT;
BEGIN
    EXECUTE pg_catalog.format('SELECT e.seq FROM %I.audit_entries e ORDER BY e.seq DESC LIMIT 1', TG_TABLE_SCHEMA)
        INTO last_seq;
    IF NEW.seq IS DISTINCT FROM COALESCE(last_seq, 0) + 1 THEN
        RAISE EXCEPTION 'audit seq must be the last seq + 1 (got %, last %)', NEW.seq, COALESCE(last_seq, 0)
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END
$fn$;
CREATE OR REPLACE TRIGGER audit_entries_seq_guard BEFORE INSERT ON audit_entries
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_seq_guard();

CREATE OR REPLACE FUNCTION hadavin_audit_checkpoint_guard() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, pg_temp
AS $fn$
DECLARE
    found_hash TEXT;
BEGIN
    EXECUTE pg_catalog.format('SELECT e.hash FROM %I.audit_entries e WHERE e.seq = $1', TG_TABLE_SCHEMA)
        INTO found_hash USING NEW.seq;
    IF found_hash IS DISTINCT FROM NEW.hash THEN
        RAISE EXCEPTION 'an audit checkpoint must name an existing audit row and its hash (seq %)', NEW.seq
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END
$fn$;
CREATE OR REPLACE TRIGGER audit_checkpoints_seq_guard BEFORE INSERT ON audit_checkpoints
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_checkpoint_guard();
