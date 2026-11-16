# Hand-off v20: what only the lead or the owner can decide (one line each)

Format: id | default if unanswered | why | who decides. Silence never counts as a yes on a money, delete or secret rule. Full text: `CORE-PR-HANDOFF-v20.md` section 10 (the one list of defaults) and section 0. This file repeats that list and adds nothing to it (readiness minor 8 of the v18 review).

**Fact first.** DB-3 (a held file, tested on 16.15 only, author-run) would stop a hostile runtime role from lowering totals or switching the kill switch off, but only together with a change of `GRANTS` and a function-grant step in `migrate()`, because `migrate()` hands the runtime role INSERT and UPDATE on those tables at every start. Nothing applies without the owner's yes. **Changed since v18:** the DB-2 and DB-3 files have new hashes (so a yes given to the v18 hashes covers nothing); the guard is a real allow-list; a plain `CREATE VIEW` slipped through the v18 guard and an independent runner found it, so no one has yet read v19 independently.

## OWNER-OPEN
- **L22** | DB-3 `spend_guarded_writes.sql` (sha256 3aa7ed7048a5b939...10cc, changed in v20: the agent id is an ASCII allow-list, `NOT VALID` is gone, the settle needs the month row) is NOT built or applied | the runtime role would hold SELECT on three tables and EXECUTE on three functions (`spend_reserve`, `spend_settle`, `kill_switch_engage`); only the operator role gets `kill_switch_release`; needs PG 14+, the `GRANTS` change, the function-grant step and new store code (the store must treat an empty function result as an error) | owner.
- **L7** | the Infinity clause is NOT applied; default file stays (5d765255...c1093); variant bd0409c9...9fe84 and upgrade fafa71fa...f041f each need their own yes | owner.
- **L9** | DB-2 (changed in v19, sha256 c0c4913e...daf2: it now also records the INSERT of a missing switch row) is NOT applied | needs PG 14+ | owner.
- **L16** | no delete path | owner. **L17** | Q27 not assumed | owner. **D5** | not a gate | owner. **O1** as its text.

## NEEDS-LEAD
- **L23** | DB-3 not applied until you name the operator role and who holds its credential; the operator role has no table right, so how the operator reads the switch is also your choice | lead.
- **L18** | default (one place): PG 14+ for the upgrade file, DB-2 and DB-3; an independent runner repeats `run_pg_v20.sh` (twice: `pg_v20.py` and `pg_v16_regress.py`) and `run_secrets_v20.sh` on 14 and 17; exact commands in section 5.6 L18 | lead.
- **L20** | PR gates compare with the recorded baseline of two failing guard tests; v19 gives the comparator `compare_gate4.py` (test names and counts; it does not compare the message text, a person reads the two messages once) | lead.
- **L21** | S-1 is not split (14 ids); if you accept the split (S-1a, S-1b: 15 ids) the E0-S1 rows divide as the table in 7.2 says | lead.
- **L13** | nobody named: operator runs `limits status --check` weekly | lead. **L19** | the operator runs `REVOKE TEMPORARY ... FROM PUBLIC` once per database; the start-up check is a `ConfigError` in `prod`, a warning in `pilot`, nothing in `demo`, and runs whenever the audit-reader role exists (v20 fixes the v19 contradiction) | lead.
- **L24** | the decrease record gets two rows per ordinary settle (measured: 135 bytes a row, 2000 rows for 1000 settles); default keep as built and alert only on kill-switch records; alternative is a DB-2 change (new review round) | lead.
- **L25** | agent-id characters `A-Z a-z 0-9 . _ : @ / + -`, 1 to 200, first a letter or digit (my choice, not an answer of yours): do your real agent ids fit | lead.
- **L2, L3, L4, L5, L6, L8, L10, L11, L14, L15** | defaults as in section 10 (L4 matters more now: one login per agent closes the cross-agent settle of DB-3) | lead.
- **New for you, not numbered (they are my numbers):** `spend.kill_switch_alert_minutes` default 60 (5.6c item 5), the day window 2020-01-01 to 2099-12-31 and the 60 s `statement_timeout` in DB-3, and the 1,000,000,000,000 ceiling; change them or say they stand.
- Also yours: run the EGM review of v20 (I could not); an independent evidence run of v20 (v19's independent run found F1 to F6; all are in v20); run `gate4_v20.sh` on the current tree (I ran its five commands one by one, section 0-v20); find out who emptied the folder at about 18:45 UTC (section 0-v20 item 3); save the files the reviewers write.
