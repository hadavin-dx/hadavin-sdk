-- NOTE (v3 table, four alert columns at the end): matches the flows in n8n-flows-v3, n8n-flows-film-v3, n8n-flows-real-v3. The flows in this folder (v2) ignore the extra columns, so this table also runs them.
-- OLDER NOTE: this table matches the flows in this folder (mf-*.json, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
-- Design A lead table (Postgres). The insert is the claim. Created before the flows run.
CREATE TABLE mf_leads(
  lead_key      text PRIMARY KEY,
  email         text,
  name          text,
  state         text NOT NULL DEFAULT 'new' CHECK (state IN ('new','processing','done','review','unknown','failed')),
  claimed_until timestamptz,
  claim_token   text,
  attempts      int  NOT NULL DEFAULT 0,
  crm_id        text,
  mail_sent     boolean NOT NULL DEFAULT false,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
  alert_sent    boolean NOT NULL DEFAULT false,
  alert_token   text,
  alert_until   timestamptz,
  alert_attempts int NOT NULL DEFAULT 0);
