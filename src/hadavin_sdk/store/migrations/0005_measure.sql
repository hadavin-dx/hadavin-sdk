-- Hadavin core store, version 0005 (K6 measurement): labels, level events, weekly reports, the tick detail column
-- and the three views the weekly report and the portal read. Labels, level events and reports are append-only for the
-- runtime role (SELECT, INSERT); a demotion is cleared by a later `clear` row, never by a DELETE.

CREATE TABLE labels (
    seq          BIGSERIAL UNIQUE,   -- insertion order: "latest" means the highest seq, never created_at
    label_id     TEXT PRIMARY KEY,
    run_id       TEXT NOT NULL,
    label        TEXT NOT NULL CHECK (label IN ('agree', 'partial', 'wrong', 'harmful', 'abstain_ok', 'missed')),
    principal_id TEXT NOT NULL,
    channel      TEXT NOT NULL CHECK (channel IN ('chat', 'csv')),
    approved_by  TEXT,
    created_at   TIMESTAMPTZ NOT NULL
);
CREATE INDEX labels_by_run ON labels (run_id, created_at);

CREATE TABLE level_events (
    seq       BIGSERIAL PRIMARY KEY,
    agent_id  TEXT NOT NULL,
    action_id TEXT NOT NULL,
    kind      TEXT NOT NULL CHECK (kind IN ('demote', 'clear')),
    reason    TEXT NOT NULL,
    "by"      TEXT NOT NULL,
    at        TIMESTAMPTZ NOT NULL
);
CREATE INDEX level_events_by_action ON level_events (agent_id, action_id, seq);
-- A demotion is recorded once per reason: two ticks (or a tick and a click) that both decide to demote insert one row.
CREATE UNIQUE INDEX level_events_one_demote_per_reason ON level_events (agent_id, action_id, reason)
    WHERE kind = 'demote';

-- Promotion evidence is per config: a proposal records the config hash, model and prompt that made it.
ALTER TABLE plans ADD COLUMN config_hash TEXT;
ALTER TABLE plans ADD COLUMN model_id TEXT;
ALTER TABLE plans ADD COLUMN prompt_sha256 TEXT;
CREATE INDEX plans_by_action_hash ON plans (agent_id, action_id, config_hash);

-- A demotion card or a breach notice is recorded here once it was really delivered (a permanent record, unlike
-- the expiring click nonces): until it is, every tick tries again.
CREATE TABLE announcements (
    key TEXT PRIMARY KEY,
    at  TIMESTAMPTZ NOT NULL
);

-- One row per signed channel click the measurement acted on (the request's timestamp and signature): a captured
-- request replayed inside the signature window finds its row and is refused. A row older than twice the signature
-- window can never be replayed, so a tick step deletes it (the only DELETE the runtime role has on these tables);
-- the same table holds the short claim that stops two ticks announcing one weekly report.
CREATE TABLE seen_actions (
    nonce     TEXT PRIMARY KEY,
    seen_at   TIMESTAMPTZ NOT NULL,
    team_id   TEXT NOT NULL DEFAULT '',   -- the workspace the signed request came from
    action_ts TEXT NOT NULL DEFAULT ''    -- the click's own timestamp inside the signed payload
);

CREATE TABLE reports (
    week_start DATE PRIMARY KEY,     -- ISO week (Monday)
    body_md    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

-- K4's backlog step writes it (oldest_received_age_s, events started late); the weekly report reads it.
ALTER TABLE tick_state ADD COLUMN detail JSONB;

-- A chat label, or a csv label the line owner approved, counts. The latest such label of a run is its label.
CREATE VIEW v_pilot_week AS
WITH r AS (
    SELECT run_id, state, reason_code, cost_usd, created_at,
           date_trunc('week', created_at AT TIME ZONE 'UTC')::date AS week
    FROM runs),
p AS (SELECT run_id, created_at AS planned_at FROM plans),
l AS (SELECT DISTINCT ON (run_id) run_id, label FROM labels
      WHERE channel = 'chat' OR approved_by IS NOT NULL
      ORDER BY run_id, seq DESC)
SELECT r.week,
       count(*)                                                          AS runs,
       count(p.run_id)                                                   AS proposals,
       count(*) FILTER (WHERE r.reason_code = 'shadow')                  AS shadow_cards,
       count(*) FILTER (WHERE r.reason_code = 'shadow_undelivered')      AS cards_not_delivered,
       count(l.run_id)                                                   AS labelled,
       count(*) FILTER (WHERE l.label = 'agree')                         AS agree,
       count(*) FILTER (WHERE l.label = 'partial')                       AS partial,
       count(*) FILTER (WHERE l.label = 'wrong')                         AS wrong,
       count(*) FILTER (WHERE l.label = 'harmful')                       AS harmful,
       count(*) FILTER (WHERE l.label = 'abstain_ok')                    AS abstain_ok,
       count(*) FILTER (WHERE l.label = 'missed')                        AS missed,
       count(*) FILTER (WHERE r.reason_code IN ('uncited', 'ungrounded', 'run_budget', 'tool_error',
                                                'redaction_error')
                        OR (r.state = 'NO_ACTION' AND p.run_id IS NULL)) AS abstained,
       count(*) FILTER (WHERE r.state = 'SUCCEEDED')                     AS fixes_verified,
       percentile_cont(0.5) WITHIN GROUP
           (ORDER BY extract(epoch FROM p.planned_at - r.created_at))    AS median_s_to_proposal,
       avg(r.cost_usd)                                                   AS avg_cost_usd
FROM r LEFT JOIN p USING (run_id) LEFT JOIN l USING (run_id)
GROUP BY r.week;

CREATE VIEW v_caught_week AS
SELECT date_trunc('week', at::timestamptz AT TIME ZONE 'UTC')::date AS week,
       body::jsonb ->> 'caught_by'               AS caught_by,
       count(DISTINCT run_id)                     AS n
FROM audit_entries
WHERE body::jsonb ->> 'caught_by' IS NOT NULL
GROUP BY 1, 2;

CREATE VIEW v_approval_week AS
SELECT date_trunc('week', d.decided_at AT TIME ZONE 'UTC')::date AS week,
       count(*)                                           AS decisions,
       count(*) FILTER (WHERE d.decision = 'reject')      AS wont_run,
       percentile_cont(0.5) WITHIN GROUP
           (ORDER BY extract(epoch FROM d.decided_at - r.created_at)) AS median_s
FROM approval_decisions d JOIN approval_requests r USING (approval_id)
GROUP BY 1;
