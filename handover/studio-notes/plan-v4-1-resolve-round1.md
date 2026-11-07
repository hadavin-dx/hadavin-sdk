# Plan v4 round-1 resolve (lead, 2026-11-07 10:20Z / 15:50 IST) -> plan v4.1 = AMENDMENT A8 to frozen plan-v3

Inputs: five reports in handover/reviews/plan-v4-round1/ (structural 17, comprehension 18 + 8 contradictions, zoom-out 15, readiness 26, design 2 Blocker + 18 Major + 6 Nit), q319, q320. I read q319/q320 summaries, not every line of the five reports (state: PARTLY READ). Round 2 reviewers must read v4.1 fresh.

## Rulings (each answers a finding named by 3+ reviewers or a Blocker)
1. FORM: v4 is NOT a replacement. It becomes AMENDMENT A8 to plan-v3 (v3 stays frozen). A8 uses v3 package ids (P1a, P1b, P4b1, P4b2, P2d ...) and AK ticket ids; "verdict" words = ADOPT/WRAP/KEEP-CODE/DROP, "rung" = R447 ladder rung 1..5; the A8 header defines both.
2. P2d: stays ON as owner orders 11 and 19E say. Delete "off by default". Built code stays, no extension.
3. AK-G2: NO pg-boss/Graphile in the core (Node in a Python core; ignores ticket rev 3 lease design). Claim/lease/retry stays our code per the ticket. pg-boss/Graphile only as a named OUTLINE for a client who already runs one (trigger: client asks).
4. Door contracts: inbound and outbound contract text = AK-G2 ticket rev 3 verbatim (no new wording). "One transaction" claim stays exactly as the ticket states. The hop before the door (client tool -> door) is out of the guarantee; say so in plain words.
5. n8n licence: statement is OUR READING of the Sustainable Use text, not legal advice; quote/contract wording: "the client runs n8n in the client's own account; Hadavin does not host or resell n8n". Owner confirms or a lawyer checks before first quote.
6. Cost table: split n8n Cloud (EUR 20/50 per month, Business EUR 667 is SELF-HOSTED only) from self-hosted; add yearly totals per tier; add Postgres hosting; flag execution caps (Starter 2.5K) against expected volume; Make stays UNREAD.
7. T1: the core meter test is the existing gateway-check evidence (order 35) plus one new 50-parallel test on our own meter. LiteLLM cap test done by the lead 2026-11-07 (egm/hadavin-sdk/core-complete/captest-1.md). Default "no" removed: T1 is no longer an owner gate.
8. Presidio: OPTIONAL redactor backend behind the kind (alternative), NOT the default. v3 s5 default (pattern backend) and order 35 (13 of 30 hostile inputs missed) stand.
9. AK-G15, AK-G1, AK-G16: stay DEFERRED (order 57.2). A8 does not lift them; lifting needs the owner's yes. A8's "BUILD NEXT: AK-G2" is also subject to that: AK-G2 starts only after the open chain merges AND a lead order lifts the deferral.
10. T2: replay-after-31-days tests the ledger layer directly (signature timestamp tolerance is a separate test).
11. P5b2/P5b5/P6b1: unchanged (HOLD for owner, keep as built).
12. Section 7 estimates: removed until the open chain merge order is clear.

## Next
Cloud writes plan-v4-1 from this file (order 140), commits to handover/studio-notes/, then round 2 = 3 fresh reviewers (design, readiness, comprehension) on v4.1 only; stop rule: 2 clean rounds or the third round freezes (max 3).
