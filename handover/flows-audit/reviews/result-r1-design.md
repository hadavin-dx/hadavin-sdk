# Result review round 1 - design lens (agent a737211799b7fc972, Sonnet 5.5, read-only)
Saved by the lead session (the reviewer cannot write files). Reviewer text condensed; every finding kept.
Verdict: no Blocker left unaddressed by the findings; 3 Majors in the deliverables (patches, cut list).

## Major
- D-M1 Patches F-003 and F-004 leave the sheets contradicting themselves. F-004 rewrites statement 17 only; the Tag line after it still says "45 s: NOT RUN". F-003 leaves: scene 4/5 "NO NUMBER measured for 45 s" cells, "45 s UNMEASURED" lines (RUNSHEET:22, 23, 47), risk 2 (:51), risk 8 (:57, "lease not settled"), and claims S2, S8, S12 (only worded in F-006/F-007, no patch). The patched caption inserts a relayed number (60.1 to 61.9 s) with no "relayed, not seen by us" marker. Fix: extend both patches to every line listed, or mark the numbers pending in the caption.
- D-M2 Patch F-002: verdict "not_stored" is false when the INSERT succeeded but errored on the way back (ON CONFLICT DO NOTHING makes a retry safe; recovery would also finish the row). Rename to "retry"/"not_confirmed" and say "retry with the same key is safe". No test covers the new 422/503 replies (mf.py checks only new/done/review). Sender contract needed: 422 never retry, 503 retry same key. The "3 added nodes, 5 edges" rebuild claim is NOT in evidence-1.md (lead-asserted until an evidence runner records it). Minor: KeyOk trims only inside the IF test, Claim stores the untrimmed key: trim in Valid. Minor: document n8n_error false (422) vs true (503).
- D-M3 CUT-LIST ordering can destroy the only correct table definition: v3/v4 hold the only mf_leads.sql with alert columns; n8n-table-screen-v2/README.md:27 points at "DDL in n8n-flows-v4". Add ordering: apply F-001, repoint README, then archive v3/v4. The n8n-flows row must say the folder itself stays (holds mf_leads.sql, N8N-START.md, DESIGN-A-README.md, PAGE-STATEMENTS-V4.md).

## Checked and agreed
- F-001 Blocker defensible (n8n-flows/mf_leads.sql 0 alert columns; mf.py:45-47 inline copy has them). Patched comment should name real-v5 and film-v5 (Nit). Patch does not ALTER existing databases: add a one-line migration note.
- F-002 premise confirmed (Claim has no onError). Wording overstated: n8n answers a bare 500, the lead is not "without an answer".
- F-012 confirmed (ClaimStuck LIMIT 5, one 45 s lease; later rows burn an attempt untried). Near Blocker; suggest LIMIT 1; keep Major only if said why (RunSub is serial).
- F-011 confirmed (N8N-START.md:4 n8n uses SQLite). F-014 wording wrong: alert repeat is at most every 720 s, or after the 60-300 s backoff; still uncapped. Reword.
- F-005, F-013, F-015, F-016, F-017, F-018 plausible, not re-read.

## Claims verdicts (L3-claims.md)
- Run sheet S8: labelled NOT BACKED, should be BACKED (real CrmUpsert is the HubSpot node; the defect is the omission, S2 stays INCONSISTENT).
- Run sheet S17 ("L plus 16 hex" key): UNVERIFIED rather than NOT BACKED (rule lives in an absent take script).
- Run sheet S5 (caption dropped): UNVERIFIED/N/A, not BACKED.
- Tally shift: BACKED 28 -> 27, NOT BACKED 6 -> 4, UNVERIFIED 34 -> 36. File 1 sums to 31 rows (correct).

## Stores (L3-stores.md)
- Table has 14 rows (11 stores, 2 external, 1 portal "none"), not 13 (FINDINGS F-019 says 13). Nit.
- "portal: none found" rests on a grep limited to flows, scripts, claims files: say so.
- Name three database roles: intake writer, recovery writer, read-only screen reader (F-010).

## Missed or under-rated (add)
1. Placeholders in take flows (FROM_ADDRESS_PLACEHOLDER, INTAKE_ADDRESS_PLACEHOLDER, SUB_WORKFLOW_ID) are not a gate: if left, every mail node fails. Add a Major with a check.
2. Alert channel is the same SMTP as lead mail: one channel dies together. Single-dependency item, trigger "second channel after the take".
3. HubSpot hard-wired in real-v5 (film uses an HTTP stand-in): one line of lock-in.
4. $env use: DESK_ALERT_TO unset makes AlertSend fail silently and loop uncapped (F-014). Startup check in the take sequence.
5. Invalid-email leads end in state "review" with no alert and nothing re-reads them: Major or a stated stop condition.
6. mf_leads keeps name and e-mail with no expiry: Nit for the take, Major for a client build.

## Patch safety
F-001 safe for new tables (migration note). F-002 no double-apply or lost lead; verdict word, sender contract, test and rebuild evidence missing. F-003 and F-004 apply cleanly but leave contradictions.

## Not verified by reviewer
Tier B tables, lanes findings, F-013/15/16/17/21-27 beyond cited files, all runtime behaviour, absent take scripts and DECISION-one-store.md.
