# Hand-off v17: what only the lead or the owner can decide (one line each)

Format: id | default if unanswered | why | who decides. Silence never counts as a yes on a money, delete or secret rule. Full text: `CORE-PR-HANDOFF-v17.md` section 10 and 0a.

**Fact first.** DB-3 (a held file, tested on 16.15 only) would stop a hostile runtime role from lowering totals or switching the kill switch off. Nothing applies without the owner's yes.

## OWNER-OPEN
- **L22** (new) | DB-3 `spend_guarded_writes.sql` (sha256 03380075...ed6e) is NOT built or applied | changes the runtime role to select-only plus execute on four functions; needs PG 14+ and new store code | owner.
- **L7** | the Infinity clause is NOT applied; default file stays (5d765255...c1093); variant bd0409c9...9fe84, upgrade fafa71fa...f041f each need their own yes | owner.
- **L9** | DB-2 (changed in v17, sha256 b4dfdf3a...1ec9) is NOT applied | needs PG 14+ | owner.
- **L16** | no delete path | owner. **L17** | Q27 not assumed | owner. **D5** | not a gate | owner. **O1** as its text.

## NEEDS-LEAD
- **L23** (new) | DB-3 not applied until you name the operator role and who holds its credential | lead.
- **L18** | default: PG 14+ for upgrade, DB-2, DB-3; an independent runner repeats `run_pg_v17.sh` and `run_secrets_v17.sh` on 14 and 17 | lead.
- **L20** | PR gates compare with the recorded baseline of two failing guard tests | lead.
- **L13** | nobody named: operator runs `limits status --check` weekly | lead. **L19** | not done; the start-up check fails in prod and in pilot with a paid kind | lead.
- **L2, L3, L4, L5, L6, L8, L10, L11, L14, L15, L21** | defaults as in section 10 | lead.
- Also yours: run the EGM review of v17 (I could not), run `gate4_v17.sh` on the current tree, and save the files the reviewers write.
