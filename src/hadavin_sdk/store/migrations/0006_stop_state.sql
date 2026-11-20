-- Stop state (step B). A stop is one new row in kill_switch_stops. A reset adds one row per open stop to
-- kill_switch_clears. The switch reads ON while the kill_switch row is missing, or its flag is on, or a stop
-- has no clear. Both tables are append-only for every role: the trigger function of 0002 refuses UPDATE,
-- DELETE and TRUNCATE. The id is a random UUID, not a serial number, so a role that may insert cannot guess
-- the next id and block a later stop.
CREATE TABLE kill_switch_stops (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "by" TEXT,
    ts   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kill_switch_clears (
    stop_id UUID PRIMARY KEY REFERENCES kill_switch_stops (id),
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
