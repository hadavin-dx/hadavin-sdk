# REVIEW.md round 16, design reviewer (agent a044860; words unverified; no Blocker). Saved condensed by flows-audit. Read: REVIEW.md, the 3 patches, README, DEAD-MAN-CHECK.md, 7 files of /tmp/smfull. Did not open /tmp/core-b4p, evidence-13.md, heavy-lane SUMMARY.md.
Major
1 Missed risk: C-01 hunk 2 (`llm.kind != "fake"` and min(price)<=0 -> ValueError) makes a self-hosted/local model (openai_compat, no key, backends/table.py:73 and :529) with price 0 fail to load; lock-in vs no-single-dependency. REVIEW has no "self-host/local/ollama" text; C-6 covers demo prices only. Needed: state exemption is only kind==fake; decide if local model needs positive notional price; README rollout note + test.
2 C-7 row (line ~43) says "Severity stays Major..." and also "ROUND 15 RATING Major to Minor"; table says Minor. Delete the stale sentence.
3 "Major needs a shown defect" rule applied unevenly: C-3 stays Major with no failing test; A-2 and A-3 Major though about a deferred patch. Apply to all or state a second rule; the 7-Major headline and "3 + 1 + 3 = 7" depend on it.
4 "0 Blocker" count line vs "BLOCKER FOR THE PROPOSAL AND FOR PILOT AND PRODUCTION: 2 (X-5, X-6)" read as a disagreement; put the line directly under the script output or add a column.
5 Strangers cannot follow: X-6 one cell ~15,000 words (X-5, C-3 similar); unexplained labels (ROUND 14 POINT 3, design B1/M1..M7, codebase Nit 3, F4, (c)(i), choice (5)(g), fact 5); first 6 lines are process log; Short answer ~10 paragraphs assuming C-01/A-01/G5 known. Fix: 10-line plain summary and one-line-per-row index first; history to fix-review files; split X-6 into sub-rows (what is wrong, who can do it, cost).
Minor
6 A-4 says all five A-01 tests build audit.ChainAudit(audit._Db.memory()): per A-01.patch 141-185 test_the_step_is_in_the_tick_list builds no sink, test_a_kind_without_reconcile_is_skipped uses object(); say three of five.
7 Stale text in current parts: line 12 "earlier text said NOT on disk"; line 110 "not available to me then"; line 99 8 rounds of count history interleaved with the current count.
8 G-1 "understates": same-patterns comparison not done (channel final redact_text pass channel.py:29,:36; slack_channel.py:81 confirmed); soften or compare.
9 G2 ("unverifiable claims NOT built") wording not recorded as checked (no hedge in gate.py confirmed by reviewer).
10 D-1 vs D-3 coherent edit list for DEAD-MAN-CHECK.md (warning fires at write time only; A-01.patch 10-16).
Nit 11 C-6 "or max_tokens above the ceiling" moot like X-1. 12 keep Postgres statements marked unverified when splitting X-6. 13 X-4 Major rests on missing caller, not measured loss; say so.
