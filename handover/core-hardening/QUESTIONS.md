# QUESTIONS from core-hardening (lead-only; I keep working meanwhile; none blocks me)
Source: steps-edits/EDITS.md "NOT DECIDED" (round 2) and c6-skip-audit/REPORT.md.
1. HubSpot app 1: give it the delete right for the end-of-take removal of contacts, or have the owner remove leftovers by hand? (EDITS item 1)
2. Confirm decision 7 ("no real keys, mailboxes or client data") applies to agents, the loopback re-smoke and cloud sessions only, not to the owner's throwaway Gmail accounts, HubSpot test account and model key. (EDITS item 2, confirmation only)
3. Postgres logins for the real take: three logins or one; where n8n's database password lives. (item 3)
4. Which port the real take's n8n uses (rehearsal 5690; 5678/5679 are the owner's own). (item 4)
5. Is the real-account smoke (checks a to f) still planned, and in what order with the loopback re-smoke? (item 5)
6. Who does n8n's first-visit owner setup and switches the flows on at the real take. (item 6)
7. Confirm P14 (Windows browser reaches n8n inside WSL) from the first smoke evidence; EDITS rows E-07 and E-08 are held until then. (item 7)
8. Proof screen for the counts in the video: owner choice. (item 8)
9. Wording "one database" vs one Postgres server with two databases; fix DECISION-one-store line 14 too? (item 10)
10. Cut Phase 0 steps 1-7 and 9 out of OWNER-STEPS v3 (v4 already does; confirm v4 replaces v3). (item 12)
11. Scene 5: cut it or keep the stand-in (run sheet :56, :78); and run sheet :90 caption number "60.1 to 61.9 s" is unmeasured/unread: read the lane3 raw or drop the number (c6-skip-audit M1, F-006).
12. Mutation survivors: ceiling 200_000 for max_tokens needs the studio head's yes or a number from the provider page (patches-ready README).

13. (ORDER 019, lead only) The two baseline test failures are real defects in the tracked tree, not a scratch artefact (proof: patch-test-runs/FAIL-CAUSE.md, two fresh clones). Both are in files outside handover/core-hardening/, which this session may not edit: (a) the banned vendor word is in handover/BRIEF-PREAMBLE-studio-2026-11-06.md line 17 and handover/demo/portal/portal-design-v2.md line 234, and handover/reviews/P1a-idempotence-probe.txt is not UTF-8 text; (b) 10 licence problems under handover/promotion-inputs/ (7 LICENSE copies, 3 pyproject fields). Question: do you fix them (reword, convert to UTF-8, drop or re-license the copies) or do I get written permission to edit those paths? Note: my own raw logs also quoted the banned word; I redacted them (see report).

## Q14 (2026-11-16 core-hardening): scope of the C5 patches for the take
A necessity review (patches-ready/review/necessity-r1.md) says none of C-01, A-01, G5-wording is needed for the take's narrow claim; it recommends deferring A-01 and cutting C-01 to a minimal price/max_tokens check (only if the model program loads the Route config, which nobody has traced). We keep building C5 v3 as ordered. Please answer: (a) keep all three patches for the core regardless of the take, or (b) cut/defer A-01 and the C-01 extras for now? (c) Does the take's model program load Route? Also: A-01 makes the tick exit 1 while the audit outbox has rows left; does anything in the take watch the tick exit code?
