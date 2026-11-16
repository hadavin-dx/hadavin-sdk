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
