# result-resolve-1: resolution of result review round 1 (Status: resolved for round 1). Done by the session in the main context (egm:egm-resolve invoked through the Skill tool; headless, auto-accept). Target: AUDIT-FINDINGS.md (rebuilt by parts/ script) and MASTER-MAP.md line 2 and lane D3 map.
Counts: 20 findings from 4 reviewers. PROPOSE FIX applied: 17. CONTEST: 0. ESCALATE (given to the lead as proposals, no lane severity changed): 5 re-ratings (B-01, D2-01, A-02, X-02+X-03+X-16 merge, A-18), listed in AUDIT-FINDINGS.md section 2b. DECLINE (Nits not worth a fix): 3 (llm file rows to confirm, Vault error text wording, CI export path note: the last two are in 9b and 9e as notes, the first is open).
| finding | category | what changed |
|---|---|---|
| RC-1 D1-03 wrong in part | PROPOSE FIX | narrowed in section 9d; Part IV text is left as the builder wrote it with a pointer in the Part title |
| line-number Nits (A-04, B-07, B-11, M-B-17, M-B-28) | PROPOSE FIX | section 9a |
| RZ-1, RZ-2 structural issue under-weighted | PROPOSE FIX (as a proposal) | plain summary at top, section 2b, section 3 note, section 4 step 1 |
| RZ-3 a-i evidence section 9 items | PROPOSE FIX | section 9b (from the reviewer's grep, not yet judged by a builder: said so) |
| RZ-4 A-18 | ESCALATE | section 2b and 9c |
| RZ-5 over-claimed Blockers | ESCALATE | section 2b; section 3 retitled; count 5 vs 6 explained |
| RZ-6 hygiene vs money buckets | PROPOSE FIX | note under section 2 counts; no new bucket column yet (not applied: would need re-rating every finding) |
| RZ-7 dead chain counted twice | PROPOSE FIX | section 5 |
| RD-1..RD-3 order, missing items, tick prerequisite | PROPOSE FIX | section 4 |
| RD-4 demo meter becomes a file store | PROPOSE FIX | section 4 |
| RD-5, RD-6 choke point, failure settle | PROPOSE FIX | section 4 |
| RD-7 lock-in items | PROPOSE FIX | section 9e |
| RC (comprehension) 1 to 6 | PROPOSE FIX | plain summary, glossary before section 0, section 3 title, section 4 explanations, section 10 questions, CRM legend, Part VI newline repair (the D3 files contained escaped newlines from the extraction; decoded) |
Not done: new "hygiene" and "audit-process" buckets (RZ-6); judging section 9b items by a builder; reading Parts II-VI by the design and zoom-out reviewers (they read only part of the file). Round 2 of the result review has not been run; the time left to the hard stop is the reason to choose which Blocker/Major paths get a second pass (security, money and redaction paths are uncapped by rule).
