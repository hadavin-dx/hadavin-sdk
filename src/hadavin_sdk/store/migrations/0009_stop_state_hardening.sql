-- Stop state hardening (step B, E12 Medium 3, Medium 4, Low 6). The reset record is written by
-- `PostgresStore.clear_stops`. There is no watermark table: nothing ever read it (the gate read counts stops against
-- clears, see `get_kill_switch`), so it was dead schema and a second truth next to the clears (review N3).
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

-- (2) The oldest-open-stop read (`ORDER BY s.ts, s.id`) is served by an index instead of a sort.
CREATE INDEX kill_switch_stops_by_ts ON kill_switch_stops (ts);

-- (3) Planted years (0100 BC, 20000) are refused on the stop tables. isfinite() alone left them valid.
-- The constraints are NOT VALID: they are enforced for every NEW row, but the rows already there are not checked, so
-- this migration cannot fail on a database that already holds a planted ts (the stop tables are append-only: such a row
-- could not be removed below a superuser, and the upgrade would be stuck).
-- This file never validates them (`ALTER TABLE ... VALIDATE CONSTRAINT` fails the upgrade on a planted row, and a
-- conditional one needs a DO block, which the repo's statement lexer refuses). `migrate` does it right after the files
-- (`settle_stop_constraints`): every constraint whose table holds no row outside the range is validated, silently,
-- so a clean database ends validated; a database holding a planted row still upgrades and `migrate` warns, once per
-- run, until the operator has dealt with the row and runs `hadavin-sdk migrate --validate-constraints`
-- (`validate_constraints`; docs/stop-state-runbook.md, "After the upgrade").
-- ADD CONSTRAINT takes a short ACCESS EXCLUSIVE lock on the (small) stop tables, and so does the index above.
ALTER TABLE kill_switch_stops ADD CONSTRAINT kill_switch_stops_ts_range
    CHECK (ts BETWEEN '2000-01-01' AND '2100-01-01') NOT VALID;
ALTER TABLE kill_switch_clears ADD CONSTRAINT kill_switch_clears_ts_range
    CHECK (ts BETWEEN '2000-01-01' AND '2100-01-01') NOT VALID;

CREATE OR REPLACE TRIGGER kill_switch_resets_append_only BEFORE UPDATE OR DELETE ON kill_switch_resets
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_resets_no_truncate BEFORE TRUNCATE ON kill_switch_resets
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
