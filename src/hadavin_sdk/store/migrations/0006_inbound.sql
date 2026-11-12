-- Hadavin core store, version 0006 (AK-G2-a): the inbound ledger (saved message records, their texts, the key check, the re-run owner).
-- Every time column is written by the caller (no now(), no time DEFAULT). Demo stage only; see the AK-G2 pilot gate.

CREATE TABLE inbound_key_checks (
    tenant         TEXT NOT NULL,
    source         TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    readers        TEXT[] NOT NULL,
    key_check      TEXT NOT NULL CHECK (key_check ~ '^[0-9a-f]{16}$'),
    set_at         TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant, source)
);

CREATE TABLE inbound_receipts (
    tenant         TEXT NOT NULL,
    source         TEXT NOT NULL,
    delivery_key   TEXT NOT NULL CHECK (delivery_key ~ '^[0-9a-f]{64}$'),
    schema_version INTEGER NOT NULL,
    readers        TEXT[] NOT NULL,
    body_sha256    TEXT NOT NULL CHECK (body_sha256 ~ '^[0-9a-f]{64}$'),
    key_check      TEXT NOT NULL CHECK (key_check ~ '^[0-9a-f]{16}$'),
    generation     INTEGER NOT NULL CHECK (generation BETWEEN 0 AND 65535),
    run_id         TEXT CHECK (run_id IS NULL OR run_id ~ '^run-[0-9a-f]{32}$'),
    state          TEXT NOT NULL CHECK (state IN ('received', 'claimed', 'done', 'needs_person', 'refused')),
    reason         TEXT,
    last_reason    TEXT CHECK (last_reason IS NULL OR last_reason IN ('step_error', 'audit_unavailable')),
    attempts       INTEGER NOT NULL CHECK (attempts >= 0),
    lease_until    TIMESTAMPTZ,
    claim_token    TEXT CHECK (claim_token IS NULL OR claim_token ~ '^clm-[0-9a-f]{32}$'),
    reuse_of       TEXT CHECK (reuse_of IS NULL OR reuse_of ~ '^[0-9a-f]{64}$'),
    received_at    TIMESTAMPTZ NOT NULL,
    updated_at     TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant, source, delivery_key),
    CONSTRAINT inbound_receipts_reason CHECK (CASE state
        WHEN 'refused' THEN COALESCE(reason IN ('invalid_input', 'forbidden', 'duplicate', 'id_reuse'), false)
        WHEN 'needs_person' THEN COALESCE(reason IN ('low_quality', 'unreadable', 'over_budget',
            'meter_unavailable', 'masking_refused', 'outbound_refused', 'policy', 'attempts_exhausted',
            'body_missing', 'body_mismatch', 'run_interrupted', 'run_limits', 'run_mismatch',
            'run_needs_person'), false)
        ELSE reason IS NULL END),
    CONSTRAINT inbound_receipts_lease CHECK ((state = 'claimed') = (lease_until IS NOT NULL AND claim_token IS NOT NULL)),
    CONSTRAINT inbound_receipts_reuse_run CHECK ((reuse_of IS NULL) = (run_id IS NOT NULL))
);

CREATE TABLE inbound_bodies (
    tenant         TEXT NOT NULL,
    source         TEXT NOT NULL,
    delivery_key   TEXT NOT NULL CHECK (delivery_key ~ '^[0-9a-f]{64}$'),
    schema_version INTEGER NOT NULL,
    readers        TEXT[] NOT NULL,
    body           BYTEA NOT NULL,
    received_at    TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant, source, delivery_key)
);

CREATE TABLE inbound_rerun_owner (
    id        BOOLEAN PRIMARY KEY DEFAULT true CHECK (id),
    role_name NAME NOT NULL
);

CREATE INDEX inbound_receipts_waiting ON inbound_receipts (tenant, source, state, lease_until)
    WHERE state IN ('received', 'claimed', 'needs_person');
CREATE INDEX inbound_receipts_reuse ON inbound_receipts (tenant, source, reuse_of) WHERE reuse_of IS NOT NULL;

CREATE OR REPLACE FUNCTION hadavin_inbound_receipt_update() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER AS
$f$
DECLARE owner_name name;
BEGIN
    IF NEW.tenant IS DISTINCT FROM OLD.tenant OR NEW.source IS DISTINCT FROM OLD.source
       OR NEW.delivery_key IS DISTINCT FROM OLD.delivery_key OR NEW.body_sha256 IS DISTINCT FROM OLD.body_sha256
       OR NEW.key_check IS DISTINCT FROM OLD.key_check OR NEW.readers IS DISTINCT FROM OLD.readers
       OR NEW.reuse_of IS DISTINCT FROM OLD.reuse_of OR NEW.received_at IS DISTINCT FROM OLD.received_at
       OR NEW.schema_version IS DISTINCT FROM OLD.schema_version THEN
        RAISE EXCEPTION 'inbound_immutable' USING ERRCODE = '23514';
    END IF;
    IF OLD.state = 'needs_person' AND NEW.state = 'received' THEN
        SELECT role_name INTO owner_name FROM inbound_rerun_owner WHERE id;
        IF owner_name IS NULL OR current_user <> owner_name THEN
            RAISE EXCEPTION 'rerun_owner_only' USING ERRCODE = '42501';
        END IF;
        IF EXISTS (SELECT 1 FROM runs WHERE run_id = OLD.run_id AND state IN
                   ('RECEIVED', 'WORKING', 'PLAN_READY', 'WAITING_FOR_APPROVAL', 'EXECUTING', 'VERIFYING')) THEN
            RAISE EXCEPTION 'rerun_run_open' USING ERRCODE = '55000';
        END IF;
        IF NEW.generation <> OLD.generation + 1
           OR NEW.run_id IS DISTINCT FROM 'run-' || substr(OLD.delivery_key, 1, 28) || lpad(to_hex(NEW.generation), 4, '0')
           OR NEW.attempts <> 0 OR NEW.reason IS NOT NULL OR NEW.last_reason IS NOT NULL
           OR NEW.lease_until IS NOT NULL OR NEW.claim_token IS NOT NULL THEN
            RAISE EXCEPTION 'inbound_reopen_shape' USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END IF;
    IF NEW.generation <> OLD.generation OR NEW.run_id IS DISTINCT FROM OLD.run_id THEN
        RAISE EXCEPTION 'inbound_immutable' USING ERRCODE = '23514';
    END IF;
    IF NEW.attempts < OLD.attempts THEN
        RAISE EXCEPTION 'inbound_attempts_down' USING ERRCODE = '23514';
    END IF;
    IF NOT ((OLD.state = 'received' AND NEW.state = 'claimed')
            OR (OLD.state = 'claimed' AND NEW.state IN ('claimed', 'received', 'done', 'needs_person', 'refused'))) THEN
        RAISE EXCEPTION 'inbound_state_move' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END
$f$;

CREATE OR REPLACE FUNCTION hadavin_inbound_receipt_insert() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER AS
$f$
DECLARE stored text;
BEGIN
    SELECT key_check INTO stored FROM inbound_key_checks WHERE tenant = NEW.tenant AND source = NEW.source;
    IF stored IS NULL OR NEW.key_check <> stored THEN
        RAISE EXCEPTION 'inbound_key_changed' USING ERRCODE = '23514';
    END IF;
    IF NEW.generation <> 0 OR NEW.attempts <> 0 OR NEW.last_reason IS NOT NULL OR NEW.lease_until IS NOT NULL
       OR NEW.claim_token IS NOT NULL OR NEW.updated_at <> NEW.received_at THEN
        RAISE EXCEPTION 'inbound_insert_refused' USING ERRCODE = '23514';
    END IF;
    IF NEW.state = 'received' AND NEW.reason IS NULL AND NEW.reuse_of IS NULL
       AND NEW.run_id = 'run-' || substr(NEW.delivery_key, 1, 28) || '0000' THEN
        RETURN NEW;
    END IF;
    IF NEW.state = 'refused' AND NEW.reason = 'id_reuse' AND NEW.reuse_of IS NOT NULL AND NEW.run_id IS NULL THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'inbound_insert_refused' USING ERRCODE = '23514';
END
$f$;

CREATE OR REPLACE FUNCTION hadavin_inbound_body_insert() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER AS
$f$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM inbound_receipts r
                   WHERE r.tenant = NEW.tenant AND r.source = NEW.source AND r.delivery_key = NEW.delivery_key
                     AND r.state = 'received' AND r.reuse_of IS NULL AND r.readers = NEW.readers) THEN
        RAISE EXCEPTION 'inbound_insert_refused' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END
$f$;

CREATE OR REPLACE TRIGGER inbound_receipts_update BEFORE UPDATE ON inbound_receipts
    FOR EACH ROW EXECUTE FUNCTION hadavin_inbound_receipt_update();
CREATE OR REPLACE TRIGGER inbound_receipts_insert BEFORE INSERT ON inbound_receipts
    FOR EACH ROW EXECUTE FUNCTION hadavin_inbound_receipt_insert();
CREATE OR REPLACE TRIGGER inbound_bodies_insert BEFORE INSERT ON inbound_bodies
    FOR EACH ROW EXECUTE FUNCTION hadavin_inbound_body_insert();
ALTER TABLE inbound_receipts ENABLE ALWAYS TRIGGER inbound_receipts_update;
ALTER TABLE inbound_receipts ENABLE ALWAYS TRIGGER inbound_receipts_insert;
ALTER TABLE inbound_bodies ENABLE ALWAYS TRIGGER inbound_bodies_insert;
