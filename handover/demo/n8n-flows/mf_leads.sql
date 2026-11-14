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
