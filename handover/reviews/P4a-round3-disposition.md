# P4a round 3 disposition (applied in P4a.md revision 4)

Written 2026-11-05 about 18:30 UTC (00:00 IST 2026-11-06). Nothing was run; text only.

| Finding | Status | Ticket location (P4a.md) | Note |
|---|---|---|---|
| ADV-R3-1 | applied | Answer first 8; Interfaces `request_bound` row; P4a-2 interface (k1b charge); C13(c1,c2); C15; mutants a2-24a/b, a2-30; PL28; V17 | Abandoned-call charge = request_bound*getattr(llm,"max_attempts",1); reservation stays request_bound with exposure stated; sentence "unanswered request is not billed" removed. |
| ADV-R3-2 | applied (cut) | What changed; Answer first 4/L25; Notes for P4b1; Lead merge-time checklist item 1; a1 mutants note | X1 removed; a1-2/a1-13 stay attributed to U1/U9; wrapper row belongs to P4b1-b, checked by lead. |
| ADV-R3-3 | applied | C13 rows (a)-(e); Verified facts | Expected values 0.015660 / 0.031320 / 0.093960 computed with Fraction in the test, not via the function under test. |
| ADV-R3-4 | applied | Interfaces `REQUESTS_PER_CHAT` row; P4a-2 interface/files; C14(a,b,c); mutants a2-23, a2-27, a2-27b, a2-28 | Every kind declares it; request_bound raises TypeError; openai_compat uses range(self.REQUESTS_PER_CHAT). |
| ADV-R3-5 | applied (cut) | What changed; Interfaces (Rates row deleted); P4a-2 interface/files; V16 | Rates/rates/highest_prompt cut. |
| ADV-R3-6 | applied | Interfaces Reply.usage row; C9b; mutant a2-13c | ValueError documented, one row. |
| ADV-R3-7 | applied | C8 price rows; Verified facts probe 4; E0(c); a2-11e | NaN/sNaN/Infinity rows relabelled regression pins; real fail-before rows named; probe in E0. |
| COR-R3-1 | applied | Answer first 3; Notes for P4d; PL29; U14b | cost_usd deviation confirmed as a lead decision; U14b AST guard widened. |
| COR-R3-2 | applied | C7(f); mutant a2-9 | Absolute literal 0.015660 row; second half of a2-9 killed only by C7(f). |
| COR-R3-3 | applied | Answer first 3; Notes for P4d; Verified facts | "P4d on disk is rev 6" removed; helper home llm/common.py; P4d lines (rev 7: 66, 259; rev 8 on disk: 71, 264, 244) listed. |
| COR-R3-4 | applied | Lead merge-time checklist; Notes for P4b1/P4b2/P4c; Answer first 4 | Rows on disk in P4b1, P4c, P4b2, P4d, P6b1 and stacked-review rule. |
| COR-R3-5 | applied | Answer first 4; Notes for P6b1; PL27 | P6b1 after P4b1-b. |
| COR-R3-6 | applied | P4a-1 Interface cache-class wording; Interfaces | Cache-class line reworded: cache prices are v1.1 V11. |
| COR-R3-7 | applied | U14; mutant a1-16; Rules (context line) | U14 no longer claims to observe decimal flags; a1-16 = arithmetic leaves Decimal. |
| COR-R3-8 | applied | C14(a); C14(b) | Registry test (fails closed) and wire-stub row. |
| COR-R3-9 | applied | Answer first 6; P4a-1 docs bullet; files list; CHANGELOG bullet | Local-server line in CHANGELOG; openai_compat docstring/comment and table.py:73 comment (lead may drop the last). |
| COR-R3-10 | applied (narrowed) | Rules (no raw ValueError, admitted inputs); U14c; a1-18; Unverified | Rule scoped to admitted inputs; bypassed route gives loud ValueError (P4d row 72 stands); sNaN/Infinity behaviour UNVERIFIED until U14c runs. |
| COR-R3-11 | applied | C8; E0(c) | Same as ADV-R3-7 (pins vs fail-before). |
| COR-R3-12 | applied | P4a-1 Done and Rollback fields; evidence field | U1/U2/U5 named as loud-failure stand-in; Done without later merges; X1 removed from evidence. |
| COR-R3-13 | applied | Verified facts; lead check cite list | Stale cites fixed (registry.py:105/106/117, test_meter:30/32, agent_loop:432-439, k1b/loop 166-172). |
| COR-R3-14 | applied | Test ids, mutant ids, C9 mutant | Ids aligned U1..U14c, C9b, a1-18/19, a2-24a/b/c. |

Counts: 21 findings (ADV-R3-1..7 = 7, COR-R3-1..14 = 14). Applied 21 (of which 2 as cuts, 1 narrowed). Contested 0. Declined 0.

Disagreements and notes:
1. The resolve is silent on the UsageMissing-branch charge; I kept `request_bound(llm)` without the attempt multiple (the answer arrived).
2. The `backends/table.py:73` comment edit adds a hot-file touch; the lead may drop it.
3. Constant renamed to `MAX_ROUTE_PRICE_USD_PER_MTOK` (P4d's name); value stays PENDING LEAD 26.
4. sNaN/Infinity behaviour through `cost_usd` and the helper is UNVERIFIED until row U14c runs.
5. New PENDING LEAD: 28 (retry exposure), 29 (cost_usd reading); 27 changed.
