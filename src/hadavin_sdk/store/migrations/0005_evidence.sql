-- Hadavin core store, version 0005 (K5-core): read-tool calls and the run's redaction map.

-- One row per read-tool call of a run. Inputs and output are stored redacted (never raw); output_sha256 covers
-- the raw bytes the tool received, up to the fetch cap. duration_ms and attempt are reported at hardening.
CREATE TABLE tool_calls (
    call_id       TEXT PRIMARY KEY,
    run_id        TEXT NOT NULL,
    tool          TEXT NOT NULL,
    inputs        JSONB NOT NULL,
    output        TEXT NOT NULL,
    output_sha256 TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL,
    duration_ms   INTEGER,
    attempt       INTEGER,
    error         BOOLEAN NOT NULL DEFAULT FALSE  -- the call failed: kept for the audit, never citable
);
CREATE INDEX tool_calls_by_run ON tool_calls (run_id, created_at);

-- The run's placeholder -> original map, identifier kinds only (never a secret or regulated kind). Never
-- portal-readable; the runtime role may delete it (purge only).
CREATE TABLE redaction_maps (
    run_id     TEXT PRIMARY KEY,
    mapping    JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
