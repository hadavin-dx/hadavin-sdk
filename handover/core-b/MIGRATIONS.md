# Migration numbers owned by core-b (written 2026-11-20 12:20Z for the lead's integration order)

Rule: migration files are named `NNNN_name.sql` in `src/hadavin_sdk/store/migrations/`; the ledger refuses a gap or a duplicate
number; `tests/fixtures/migrations_released.json` holds a hash only for RELEASED migrations. Integrate in this order.

| number | file | step / owner | state | released (hash in migrations_released.json)? |
|---|---|---|---|---|
| 0001 | 0001_core.sql | base | on main | yes |
| 0002 | 0002_audit_chain.sql | base | on main | yes |
| 0003 | 0003_approvals_tick.sql | base | on main | yes |
| 0004 | 0004_audit_checkpoint_meta.sql | base | on main | yes |
| 0005 | 0005_evidence.sql | base | on main | yes |
| 0006 | 0006_stop_state.sql | step B (stop state) | cloud/core-b | check the manifest (lead's release decision) |
| 0007 | 0007_spend_reservations.sql | step F-store (reservations) | cloud/core-b | NOT released |
| 0008 | 0008_release_expired_spend.sql | step F-store, ORDER 020 (release command, release role) | cloud/core-b | NOT released |
| 0009 | 0009_stop_state_hardening.sql | step B, E12 (reset table, audit seq guard, watermark, ts CHECKs NOT VALID) | cloud/core-b | NOT released |
| 0010 | 0010_money_guard.sql | step F-store, E11 M4 (money guard trigger, owner-first) | cloud/core-b | NOT released |
| 0011 | 0011_money_definer.sql | ticket F-money-definer (option B, E13/E14): hadavin_limits, hadavin_caps, 7 SECURITY DEFINER functions | cloud/core-b | NOT released; step 6 (caps) is folded into it, so 0011 is still being edited (E2 = reserve reads hadavin_caps) |
| 0012 | 0012_audit_outbox_functions.sql | ticket A-audit-rights (review 1, DECISIONS 14:30Z): hadavin_audit_outbox_done, hadavin_audit_outbox_quarantine (SECURITY DEFINER; the runtime loses DELETE on audit_outbox) | cloud/core-b | NOT released |

Next free number: **0013**. No further migration is planned today.

Integration notes
- 0007-0012 are unreleased: they may still be edited in place; a hash goes into `migrations_released.json` only when the lead releases one.
- 0009 needs 0006; 0010 needs 0007 and 0008 (it names the release function owner); 0011 needs 0007-0010; 0012 needs 0002 and 0011 (the owner check of the hadavin_* functions). The ledger refuses a tree with a later file but not the earlier ones.
- Tests that read the migration list take it from the files (no hard-coded numbers), except `tests/test_k5_fixes2.py` (fake migration sets: its rename map is wrong for 0010/0011 names and passes anyway; fix when 0011 is released).
- core-a's branch must not use numbers 0006-0013.
