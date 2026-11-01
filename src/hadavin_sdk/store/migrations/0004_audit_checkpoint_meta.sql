-- Each checkpoint now records how it was signed (`alg`) and by which key (`key_label`, non-secret: never a key
-- ARN or URL). Columns are NULL for rows written before this migration or by an older runtime: NULL means "not
-- recorded", and verify then uses the configured signer's scheme. No guessed default: a constant would label
-- an Azure (ECDSA P-256) deployment's old rows as ed25519. ADD COLUMN with no default rewrites no row, so the
-- append-only triggers do not fire, and an old runtime that inserts three columns keeps working.
ALTER TABLE audit_checkpoints ADD COLUMN IF NOT EXISTS alg TEXT;
ALTER TABLE audit_checkpoints ADD COLUMN IF NOT EXISTS key_label TEXT;
