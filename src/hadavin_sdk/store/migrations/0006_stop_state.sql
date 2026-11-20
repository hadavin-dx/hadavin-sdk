-- Stop state, version 0006. The kill switch is ON when the kill_switch row is missing, or its flag is on, or a
-- row of kill_switch_stops has no row in kill_switch_clears. A stop is one INSERT into kill_switch_stops (the
-- runtime role may do that and nothing more); only the reset role may insert a clear or turn the flag off.
-- Both tables are append-only for every role (the trigger below) and by grant (`hadavin-sdk migrate`).
CREATE TABLE kill_switch_stops (
    id   BIGSERIAL PRIMARY KEY,
    "by" TEXT,
    ts   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kill_switch_clears (
    stop_id BIGINT PRIMARY KEY REFERENCES kill_switch_stops (id),
    "by"    TEXT,
    ts      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE TRIGGER kill_switch_stops_append_only BEFORE UPDATE OR DELETE ON kill_switch_stops
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_stops_no_truncate BEFORE TRUNCATE ON kill_switch_stops
    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_clears_append_only BEFORE UPDATE OR DELETE ON kill_switch_clears
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_clears_no_truncate BEFORE TRUNCATE ON kill_switch_clears
    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
