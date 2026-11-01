-- Hadavin core store, version 0005: reservations, the rows that hold a cap while a proposal waits for a person.
-- Written and released by `Store.reserve` / `release_reservation` (one transaction per call, serialised per tenant);
-- `created_at` is TIMESTAMPTZ (no string comparison of times); the index serves the per-tenant age window.
CREATE TABLE reservations (
    tenant         TEXT NOT NULL,
    key            TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    subject        TEXT NOT NULL,
    scopes         JSONB NOT NULL,
    actor          TEXT NOT NULL,
    unit           TEXT NOT NULL,
    amount         BIGINT NOT NULL CHECK (amount > 0),
    created_at     TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant, key)
);
CREATE INDEX reservations_by_tenant_age ON reservations (tenant, created_at);
CREATE INDEX reservations_by_subject ON reservations (tenant, subject);
