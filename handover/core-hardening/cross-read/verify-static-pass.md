# Verification of STATIC-PASS-real-v5.md (independent read-only agent, condensed copy, 2026-11-16)
Not checkable here: every flow-file cite (mf-form, mf-hook, mf-recovery, mf-sub-crm-mail, mf_leads.sql, V5-README, the patch defaults). The flow files are not on this branch. Settle with `git show origin/cloud/flows-audit:<path>` (commands in the agent report).
## Failures first
1. Major: plan:288 is a denied INSERT test (N5). The count read is plan:289 (P-C2, database postgres, table mf_leads). Claim holds, cite wrong.
2. Major: "re-smoke does not run real-v5" is not undisclosed: plan:493 lists "real-v5 at run time" under "will NOT prove". Real gap: the same-id-twice evidence the owner post relies on comes from film-v5. Reframe.
3. Major: the report cites OWNER-STEPS v3 only; v4+ replace v3 (decision 10). Line cites :23, :92, :97, :121 must be re-checked against v9.
4. Major: "holds by construction in the SQL" overreaches. Only the claim step dedupes. End-to-end once-ness depends on recovery (up to 3 re-runs), MailClaim, the stage journal and the CRM upsert; none run. Missing id gives a NULL insert error with unknown caller-visible behaviour.
5. Minor: drive.py and fill_flows.py are glue copies made by sed (plan:223, :248), not repo files. "Not found" is expected.
6. Nit: "only a new take id is required" is stronger than OWNER-STEPS:97/:112; nothing says mf_leads is cleared.
## Matches
plan:298 (film-v5 fill), plan:341 cases A and B, plan:335-336 B2, plan:284, plan:248, plan:420, plan:525 (120 s health wait), OWNER-STEPS:97, :121, :23, :92, DECISIONS:10. "20/45/120": only 120 confirmed.
## Action
Fix the static-pass report (items 1-4) and ask the lead to run the git-show commands. Open question for lead: where is same-id-twice tested in the real take?
