-- NOTE: this table matches the CURRENT flows (mf-*.json in this folder, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
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
  updated_at    timestamptz NOT NULL DEFAULT now());
