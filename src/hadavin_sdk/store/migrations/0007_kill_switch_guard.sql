-- P2a-1: a stop is an INSERT of a new request row; a reset is a function that only a registered login in the
-- reset group can complete. The three real functions and the group name are written by `migrate()` on every run
-- (they name the schema and the group); this file creates what does not depend on either.
-- Lock order everywhere: kill_switch, then kill_switch_stop_requests, then kill_switch_resets.

ALTER TABLE kill_switch ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;

-- Core stored whatever name the caller typed. A name that is not a keyed label becomes 'unlabelled', so the
-- guard never copies typed text (an e-mail address, for example) into the reset record.
UPDATE kill_switch SET "by" = 'unlabelled'
WHERE "by" IS NOT NULL AND "by" <> 'dba' AND "by" !~ '^id:[A-Za-z0-9_-]{1,32}:[0-9a-f]{32}$';

CREATE TABLE kill_switch_stop_requests (
    id         BIGSERIAL PRIMARY KEY,
    "by"       TEXT NOT NULL,
    ts         TIMESTAMPTZ NOT NULL DEFAULT now(),
    cleared_by BIGINT
);
CREATE INDEX kill_switch_stop_requests_open ON kill_switch_stop_requests (id) WHERE cleared_by IS NULL;

CREATE TABLE kill_switch_resets (
    old_version BIGINT PRIMARY KEY,
    reset_at    TIMESTAMPTZ NOT NULL,
    login_label TEXT NOT NULL,
    old_by      TEXT
);

CREATE TABLE kill_switch_login_labels (
    login_name TEXT PRIMARY KEY,
    label      TEXT NOT NULL UNIQUE
);

-- ONE source for "is the switch on": the flag, or at least one open request.
CREATE VIEW kill_switch_state AS
SELECT (k."on" OR r.id IS NOT NULL) AS "on",
       CASE WHEN k."on" THEN k."by" WHEN r.id IS NOT NULL THEN r."by" ELSE k."by" END AS "by",
       CASE WHEN k."on" THEN k.ts   WHEN r.id IS NOT NULL THEN r.ts   ELSE k.ts   END AS ts,
       k.schema_version, k.version,
       (SELECT count(*) FROM kill_switch_stop_requests WHERE cleared_by IS NULL)::int AS open_requests
FROM kill_switch k
LEFT JOIN LATERAL (SELECT id, "by", ts FROM kill_switch_stop_requests
                   WHERE cleared_by IS NULL ORDER BY id LIMIT 1) r ON true
WHERE k.id = 1;

-- Placeholder guard: refuses every reset until `migrate()` installs the real text (so a hand-applied file locks
-- resets out instead of leaving them open).
CREATE OR REPLACE FUNCTION hadavin_kill_switch_guard() RETURNS trigger LANGUAGE plpgsql AS
$f$ BEGIN
  IF OLD."on" AND NOT NEW."on" THEN
    RAISE EXCEPTION 'kill switch: the guard is not installed; run hadavin-sdk migrate' USING ERRCODE = 'HD001';
  END IF;
  RETURN NEW;
END $f$;
CREATE OR REPLACE TRIGGER kill_switch_guard BEFORE UPDATE ON kill_switch
    FOR EACH ROW EXECUTE FUNCTION hadavin_kill_switch_guard();
ALTER TABLE kill_switch ENABLE ALWAYS TRIGGER kill_switch_guard;

-- Friction for the owner too: the request table accepts only `cleared_by` going from NULL to a value.
CREATE OR REPLACE FUNCTION hadavin_kill_switch_requests_guard() RETURNS trigger LANGUAGE plpgsql AS
$f$ BEGIN
  IF TG_OP = 'UPDATE' AND OLD.cleared_by IS NULL AND NEW.cleared_by IS NOT NULL
     AND NEW.id = OLD.id AND NEW."by" = OLD."by" AND NEW.ts = OLD.ts THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'the stop request table is append-only';
END $f$;
CREATE OR REPLACE TRIGGER kill_switch_stop_requests_update BEFORE UPDATE ON kill_switch_stop_requests
    FOR EACH ROW EXECUTE FUNCTION hadavin_kill_switch_requests_guard();
CREATE OR REPLACE TRIGGER kill_switch_stop_requests_delete BEFORE DELETE ON kill_switch_stop_requests
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_stop_requests_no_truncate BEFORE TRUNCATE ON kill_switch_stop_requests
    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
ALTER TABLE kill_switch_stop_requests ENABLE ALWAYS TRIGGER kill_switch_stop_requests_update;
ALTER TABLE kill_switch_stop_requests ENABLE ALWAYS TRIGGER kill_switch_stop_requests_delete;
ALTER TABLE kill_switch_stop_requests ENABLE ALWAYS TRIGGER kill_switch_stop_requests_no_truncate;

CREATE OR REPLACE TRIGGER kill_switch_resets_append_only BEFORE UPDATE OR DELETE ON kill_switch_resets
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_resets_no_truncate BEFORE TRUNCATE ON kill_switch_resets
    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
ALTER TABLE kill_switch_resets ENABLE ALWAYS TRIGGER kill_switch_resets_append_only;
ALTER TABLE kill_switch_resets ENABLE ALWAYS TRIGGER kill_switch_resets_no_truncate;
