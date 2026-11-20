-- Spend reservations (step F). A reservation is money set aside for one model call before the call: the worst
-- case is booked on the day and month counters (spend, spend_month) in the same transaction that adds the row
-- here. Settling replaces it with the real cost. A reservation nobody closed is marked expired by the tick
-- and stays booked at the full amount. The upper bound of the two amount checks also refuses NaN and Infinity.
CREATE TABLE spend_reservations (
    reservation_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    day DATE NOT NULL,
    run_id TEXT,
    reserved_usd NUMERIC NOT NULL CHECK (reserved_usd >= 0 AND reserved_usd < 1000000000),
    settled_usd NUMERIC CHECK (settled_usd >= 0 AND settled_usd < 1000000000),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'settled', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    closed_at TIMESTAMPTZ,
    CHECK ((status = 'open') = (settled_usd IS NULL)),
    CHECK ((status = 'open') = (closed_at IS NULL)),
    CHECK (status <> 'expired' OR settled_usd = reserved_usd)
);
CREATE INDEX spend_reservations_open ON spend_reservations (created_at) WHERE status = 'open';
