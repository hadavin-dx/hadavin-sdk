# AK-G2 rev 6 plan review, round 6, egm-design (agent a69dd4c7)
Verdict: 0 Blockers, 1 Major, 9 Nits. Rev 5 Majors M1 (key_check) and M2 (3 roles, probe) closed in design; M3 (mutation runner command) closed as text only: needs run_mutants keywords conftest/pass_env/forbid_skips = lead decision R1.
Counts re-derived and hold: 79 rows, 143 mutants, 4 fail-before.

## Major 1
BN-59/BN-50/BN-33 say each role passes `effective_problems`, but migrate.py:255-261 flags any column-level UPDATE not in the table-level list (only SELECT on expected_cols is allowed). Dispatch (state, attempts, lease_until...) and re-run owner (generation, run_id) UPDATE grants would fail migrate with ConfigError. `_apply_grants` (:182-187) can grant column SELECT only. Fix: Grant update-column fields, _apply_grants grants UPDATE(cols), effective_problems gets expected_update_cols; row for existing runtime/purge behaviour unchanged; negative test (column UPDATE outside list reported); mutant removing that check.

## Nits
1. l.9 says 57 build notes, BN-30 says 67.
2. Race: key change committed between receive_inbound re-read and INSERT -> trigger 23514 -> 500. Map to key_changed (503), add row. Door cannot lock row (FOR SHARE needs UPDATE).
3. inbound_key_checks.key_check has no hex CHECK; stolen dispatch credential can write non-hex (DoS) or another valid value (silently disables body re-check). Add CHECK, L24 case, state limit.
4. Probe "exactly one non-owner role holds UPDATE(generation)" under-specified (superusers, PUBLIC, inherited members); cannot see rerun-owner row (only owner reads it). Specify query or state fail-closed not fail-loud.
5. migrate with renamed re-run owner role leaves old UPDATE(generation): run same query inside migrate. Tell lead "0 roles allowed at migrate" differs from ORDER 178 (6) plain reading.
6. Missing mutants/cases: CHECKs on body_sha256, reuse_of, key_check; key_check equality for the reuse-row INSERT shape alone.
7. Door role table-level SELECT on inbound_receipts: column-limit it, add L24 negative.
8. Single dependency: BN-63 Postgres-only; name a trigger ("client whose store is not Postgres"); state hmac_v0 and forwarder self-hostable.
9. Wording: "ledger name" vs key_name; "receipt" -> "saved message record" in owner-facing PL4; explain body_check_old_key/key check; state fixtures build fresh schema per session so migration mutants die.

Not checked by reviewer: ticket l.143-385 and 494-730 line by line; all PostgreSQL behaviour; mutation_runner/heavy_slot/RUN_ID_PATTERN (not on this branch).
