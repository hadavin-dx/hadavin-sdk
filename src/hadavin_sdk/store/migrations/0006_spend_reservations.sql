-- Hadavin core store, version 0006 (P4d-b): spend reservations. Forward-only and additive: no existing column changes.
-- Apply this migration with the kill switch on or in a quiet period: the foreign key needs a short lock on `runs`.
SET LOCAL lock_timeout = '10s';

CREATE TABLE spend_reservations (
    reservation_id TEXT PRIMARY KEY CHECK (reservation_id ~ '^[A-Za-z0-9._:-]{1,200}$'),
    schema_version INTEGER NOT NULL,
    agent_id TEXT NOT NULL CHECK (agent_id ~ '^[A-Za-z0-9._:-]{1,200}$'),
    day DATE NOT NULL CHECK (day BETWEEN DATE '2000-01-01' AND DATE '2100-12-31'),
    run_id TEXT REFERENCES runs (run_id) CHECK (run_id ~ '^[A-Za-z0-9._:-]{1,200}$'),
    reserved_usd NUMERIC NOT NULL CHECK (reserved_usd > 0 AND reserved_usd <= 1000000000000 AND reserved_usd = round(reserved_usd, 6)),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'settled', 'released', 'expired')),
    settled_usd NUMERIC CHECK (settled_usd IS NULL OR (settled_usd >= 0 AND settled_usd <= 1000000000000 AND settled_usd = round(settled_usd, 6))),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    closed_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,
    meta JSONB CHECK (meta IS NULL OR (jsonb_typeof(meta) = 'object' AND octet_length(meta::text) <= 2000)),
    CHECK ((status IN ('settled', 'expired')) = (settled_usd IS NOT NULL)),
    CHECK (status <> 'expired' OR settled_usd = reserved_usd),
    CHECK ((status = 'open') = (closed_at IS NULL)),
    CHECK (expired_at IS NULL OR status <> 'open')
);

CREATE INDEX spend_reservations_open ON spend_reservations (created_at, reservation_id) WHERE status = 'open';

-- A new row is always open, with the database clock as its time (a future created_at cannot make it immune to the sweep).
CREATE OR REPLACE FUNCTION hadavin_spend_reservations_insert() RETURNS trigger LANGUAGE plpgsql AS
$$
BEGIN
    IF NEW.status <> 'open' OR NEW.settled_usd IS NOT NULL OR NEW.closed_at IS NOT NULL OR NEW.expired_at IS NOT NULL THEN
        RAISE EXCEPTION 'spend_reservations: change refused';
    END IF;
    NEW.created_at := clock_timestamp();
    RETURN NEW;
END;
$$;
CREATE OR REPLACE TRIGGER spend_reservations_insert BEFORE INSERT ON spend_reservations
    FOR EACH ROW EXECUTE FUNCTION hadavin_spend_reservations_insert();

-- The only changes: open to expired / settled / released, and expired to settled / released. Nothing else moves.
CREATE OR REPLACE FUNCTION hadavin_spend_reservations_update() RETURNS trigger LANGUAGE plpgsql AS
$$
BEGIN
    IF NEW.reservation_id IS DISTINCT FROM OLD.reservation_id OR NEW.schema_version IS DISTINCT FROM OLD.schema_version
       OR NEW.agent_id IS DISTINCT FROM OLD.agent_id OR NEW.day IS DISTINCT FROM OLD.day
       OR NEW.run_id IS DISTINCT FROM OLD.run_id OR NEW.reserved_usd IS DISTINCT FROM OLD.reserved_usd
       OR NEW.created_at IS DISTINCT FROM OLD.created_at OR NEW.meta IS DISTINCT FROM OLD.meta THEN
        RAISE EXCEPTION 'spend_reservations: change refused';
    END IF;
    IF OLD.status = 'open' AND NEW.status = 'expired' THEN
        IF NEW.settled_usd IS DISTINCT FROM OLD.reserved_usd OR NEW.closed_at IS NULL OR NEW.expired_at IS NULL THEN
            RAISE EXCEPTION 'spend_reservations: change refused';
        END IF;
    ELSIF OLD.status = 'open' AND NEW.status IN ('settled', 'released') THEN
        NULL;
    ELSIF OLD.status = 'expired' AND NEW.status IN ('settled', 'released') THEN
        IF NEW.expired_at IS DISTINCT FROM OLD.expired_at THEN
            RAISE EXCEPTION 'spend_reservations: change refused';
        END IF;
    ELSE
        RAISE EXCEPTION 'spend_reservations: change refused';
    END IF;
    RETURN NEW;
END;
$$;
CREATE OR REPLACE TRIGGER spend_reservations_update BEFORE UPDATE ON spend_reservations
    FOR EACH ROW EXECUTE FUNCTION hadavin_spend_reservations_update();
