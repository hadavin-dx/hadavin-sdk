# Hand-off v21: what only the lead or the owner can decide (one line each)

Format: id | default if unanswered | why | who decides. Silence never counts as a yes on a money, delete or secret rule. Full text: `CORE-PR-HANDOFF-v21.md` section 10 (the one list of defaults) and section 0. This file repeats that list and adds nothing to it.

## Do first (lead)
1. **Relay the findings of the independent evidence runner of v20** if anything is still missing: `review-handoff-v20-evidence.md` was relayed late and is handled (B1, G1 to G8: `v21-CHANGES.md`). No independent runner has re-run v21.
2. **Run the EGM review of v21** (a builder cannot call the skills).
3. **Postgres 14 and 17.10** are not run (L18): an independent runner repeats the two commands of section 10 L18.

## OWNER-OPEN
- **L22** | DB-3 `spend_guarded_writes.sql` (sha256 `e2f8017c1975f88c251e6ec2426e3c54f89cf6a3dc61c7f0417d2e8473a075fb`, changed in v21: a settle that its checks reject returns no row) is NOT built or applied | the runtime role would hold SELECT on three tables and EXECUTE on `spend_reserve` and `spend_settle`; the operator role EXECUTE on `kill_switch_engage` and `kill_switch_release`; it needs the `GRANTS` change and the function-grant step in the same PR | owner.
- **L7** | Infinity clause not applied; default file stays | owner. **L9** | DB-2 not applied | owner. **L16, L17, D5, O1** | as in section 10 | owner.

## Lead's choices (not decided by me; each default is stated and built as the default)
- **L22b** | who may call `kill_switch_engage`. Default (least privilege): the operator role only. Other option: the runtime role as well. | lead.
- **L26** | a dedicated no-login owner role for the four DB-3 functions. Default: not built (the owner stays the migration role; the start-up check reports it). | lead.
- **L26b** | the pseudo agent ids `-cli` and `-unattributed:<agent>`. **Your default (the store skips the DB-3 functions for them and keeps the old path) cannot work as written:** after DB-3 the runtime role has SELECT only and the CHECK refuses those names. Options: (A) widen the agent-id rule to those two shapes; (B) a second table with its own functions. Until you choose, DB-3 stays unapplied. | lead.
- **L23** | the operator role for `kill_switch_engage` and `kill_switch_release`: who holds it. DB-3 is not applied until named. | lead.

## NEEDS-LEAD (defaults in section 10)
- **L18** floor 14 for the upgrade file, DB-2 and DB-3. **L20** gates compare with the baseline of two failing guard tests; `gate4_v21.sh` ran once on the unchanged tree (rc 0 on the comparator). **L21** S-1 is not split; **S-2b is split in two sessions** (S-2b-1, S-2b-2; say if you want two PRs). **L13** nobody named for `limits status --check`; the 60-minute alert needs a 5 to 15 minute schedule, otherwise the worst-case detection is about a week. **L19**, **L24** (two rows per ordinary settle), **L25** (agent-id characters `A-Z a-z 0-9 . _ : @ / + -`, 1 to 200). **L2 to L6, L8, L10, L11, L14, L15** as in section 10.
- My own numbers, yours to change: `spend.kill_switch_alert_minutes` 60, the day window 2020-01-01 to 2099-12-31, the 60 s `statement_timeout` of DB-3 (per statement, not per file), the 1,000,000,000,000 ceiling.
