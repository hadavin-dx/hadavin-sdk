# Summary of ROLES-PROPOSAL.md (reader note, 2026-11-16)

File read in full (434 lines): /home/user/hadavin-sdk/handover/flows-audit/ROLES-PROPOSAL.md (version 4, status line 3: parked, client build / after the video; line 5: Part C has a known blocker, B1).

## What it proposes
It is NOT a design for the core runtime identities. It proposes separate database logins for the n8n lead-intake flows only (table mf_leads, 14 statements S1-S14, lines 36-52). Five logins (lines 61-69): mf_tableowner (no login, owns table), mf_door (insert and read-state; S1-S4), mf_sub (record CRM id, mail sent, final state; S5-S9), mf_recover (take over stuck leads, close exhausted; S10-S11), mf_alert (alert bookkeeping; S12-S14). Rights are column-level grants (lines 120-140), no superuser, connection limits, expiry date. SQL in three guarded parts A (add), B (change owner, remove PUBLIC rights), C (retire old shared login). Each n8n node gets its own credential.

## Conflict with the REVIEW.md identity table
No name overlaps: drain, agent, tick, operator, receiver, signer, portal, purge, dead-man reader (REVIEW.md lines 222-229) are core-store logins on audit/approval/run tables; ROLES-PROPOSAL names only mf_* logins on mf_leads. So no direct conflict. The real problem is a wrong pointer: REVIEW.md lines 240, 245, 335, 365 say the breakglass, CI deploy and human identities would be "designed from ../ROLES-PROPOSAL.md". They are not. The file says (line 400) a human read-only login and a backup login are not covered; "breakglass", "CI deploy", "passkey" do not appear. Decision 22 as worded in REVIEW.md rests on a false premise. (REVIEW.md line 335 itself admits the file was not read.)

## Missing against least-privilege rule (CLAUDE.md)
- Breakglass, CI deploy, human viewer/operator/approver/admin: absent (REVIEW.md lines 240, 245 say so too).
- Agents holding no approver/executor credentials: not addressed (flows are n8n, not the agent runtime).
- Per-action reason: present per statement (Reason column, lines 36-52). Negative tests: present (section 5, groups MX, WS), but never run (line 7).
- Short-lived credentials: not met; logins have expiry date (VALID UNTIL) but are static passwords typed into n8n.
- Part C unsafe (line 5); all Postgres/n8n behaviour from memory, UNVERIFIED (section 8, line 368).

## Size
File gives one (line 366): about 3 hours agent time (1 SQL and tests, 1 throwaway server, 1 for 8 flow-file edits and re-test), about one working day with owner waiting; its own estimate, not measured. That covers only the five mf_* logins, not the three missing identities.

## Owner
Written by an agent in the flows-audit work; decisions belong to the lead/owner (section 11, lines 424+; QUESTIONS.md Q11, line 3). Running the SQL needs the database administrator's login, by hand, with the owner present (line 353). Un-parking: Decision 22 (studio head).

## Found at
/home/user/hadavin-sdk/handover/flows-audit/ROLES-PROPOSAL.md (also copies under /tmp scratch folders, not read).
