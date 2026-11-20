# EGM review round 3 of 3 (the last): tickets/F-install.md section "RESOLUTION of lead order 017(B)" (Y1 to Y6) (egm:egm-implementation-readiness, model sonnet; 2026-11-20 06:50 to 06:58 UTC). The second reviewer of this round (egm:egm-codebase-details, started at the same time) had NOT reported when this file was written: NOT RUN so far, so the round is not clean by the rule.
Result: NOT READY. Blockers 3, Majors 7, Nits 5. Y1 mostly fine (one Major), Y5 and Y6 fine; Y2 to Y4 leave decisions to the builder on a money path. Round 1 and 2 answers: all HOLD except the file list (stale for the Y changes).
Note: the reviewer read the tree of cloud/core-b, which does not yet contain the Y2 and Y3 BUILD (it is on the integration branch wip/cloud-core-b/F-install, commit d8d76ff and the merge 28abb73); several findings are about the ticket text, and the built code answers some of them (see Z).
| # | sev | finding (short) | answer |
|---|---|---|---|
| 1 | Blocker | Y3: how the per-attempt record travels from with_retry to reply() is not specified; the per-attempt predicate (does a 429 attempt cost 0?) is missing | Z1 (as built) |
| 2 | Blocker | Y2/Y3: the sum rule under-books for openai_compat (request 1 billed without usage, request 2 with usage) and a falsy test reads a genuine 0 as missing; what the token fields hold when usage is unknown | Z2 (as built) |
| 3 | Blocker | Y4: the release command's audit contract is incomplete (about 15 decisions left to the builder) | Z5: ON HOLD, ESCALATIONS E6 |
| 4 | Major | Y4 contradicts invariant 4 and ii-meter point 10 (booked never goes down); a release can drop real spend (timed-out calls may have been billed); a late settle after release is dropped; the reconciliation statement is not true after purge | E6 |
| 5 | Major | Y4: table-level rights on three money tables; the exact-rights test and several texts would break; cli.py belongs to the lead's builder (ORDER 017A) | E6 |
| 6 | Major | Y2: readers not named (the demo pipeline, tests), "judge: pass 0" ambiguous, evals None stop has no exception type, 25 test doubles | Z3, Z4 |
| 7 | Major | Y1: _screen and _shadow take no map; bind has no mapping parameter in the carrier | Z7 |
| 8 | Major | the file list is stale for the Y changes | Z6 |
| 9 | Major | the CHANGELOG behaviour list does not cover Y2/Y3 (calls without usage, retried calls stay booked; local servers omitting usage) | Z8 |
| 10 | Major | header state text contradicts itself (NO source code before GO BUILD, versus built) | Z9 |
| 11-15 | Nit | stale lines; attempts field has no consumer; "ten points" text; same-refusal wording; Y6 core-c dependency | Z6, Z10 |
