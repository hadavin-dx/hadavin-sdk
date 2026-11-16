# Hand-off v18: what only the lead or the owner can decide (one line each)

Format: id | default if unanswered | why | who decides. Silence never counts as a yes on a money, delete or secret rule. Full text: `CORE-PR-HANDOFF-v18.md` section 10 and 0a.

**Fact first.** DB-3 (a held file, tested on 16.15 only, author-run) would stop a hostile runtime role from lowering totals or switching the kill switch off, but only together with a change of `GRANTS` and a function-grant step in `migrate()`, because `migrate()` hands the runtime role INSERT and UPDATE on those tables at every start. Nothing applies without the owner's yes.

## OWNER-OPEN
- **L22** | DB-3 `spend_guarded_writes.sql` (sha256 244d2a06...c230) is NOT built or applied | the runtime role would hold SELECT on three tables and EXECUTE on three functions (`spend_reserve`, `spend_settle`, `kill_switch_engage`); only the operator role gets `kill_switch_release`; needs PG 14+, the `GRANTS` change, the function-grant step and new store code | owner.
- **L7** | the Infinity clause is NOT applied; default file stays (5d765255...c1093); variant bd0409c9...9fe84, upgrade fafa71fa...f041f each need their own yes | owner.
- **L9** | DB-2 (changed in v18, sha256 e3111401...2ce9) is NOT applied | needs PG 14+ | owner.
- **L16** | no delete path | owner. **L17** | Q27 not assumed | owner. **D5** | not a gate | owner. **O1** as its text.

## NEEDS-LEAD
- **L23** | DB-3 not applied until you name the operator role and who holds its credential; v18 also needs your choice of how the operator reads the switch (the operator role has no table right) | lead.
- **L18** | default: PG 14+ for upgrade, DB-2, DB-3; an independent runner repeats `run_pg_v18.sh` and `run_secrets_v18.sh` on 14 and 17 | lead.
- **L20** | PR gates compare with the recorded baseline of two failing guard tests (ids and messages, v18 pass rule) | lead.
- **L13** | nobody named: operator runs `limits status --check` weekly | lead. **L19** | not done; the start-up check fails in prod and in pilot with a paid kind | lead.
- **L2, L3, L4, L5, L6, L8, L10, L11, L14, L15, L21** | defaults as in section 10 (L4 matters more now: one login per agent closes the cross-agent settle of DB-3) | lead.
- Also yours: run the EGM review of v18 (I could not); an independent evidence run of v18 (author-run only); run `gate4_v18.sh` on the current tree; save the files the reviewers write.
