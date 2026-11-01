-- Each checkpoint now records how it was signed (`alg`) and by which key (`key_label`, non-secret: never a key
-- ARN or URL). Old rows load unchanged through the defaults (`ed25519`, empty label). ADD COLUMN with a constant
-- default rewrites no row, so the append-only triggers do not fire. An old runtime that still inserts three
-- columns keeps working against the new table.
ALTER TABLE audit_checkpoints ADD COLUMN IF NOT EXISTS alg TEXT NOT NULL DEFAULT 'ed25519';
ALTER TABLE audit_checkpoints ADD COLUMN IF NOT EXISTS key_label TEXT NOT NULL DEFAULT '';
