# EGM review round 3 of 3 (the last): tickets/F-install.md section "RESOLUTION of lead order 017(B)" (Y1 to Y6) (egm:egm-implementation-readiness, model sonnet; 2026-11-20 06:50 to 06:58 UTC). The second reviewer of this round (egm:egm-codebase-details, model sonnet) reported at 06:58 UTC: 1 Blocker, 10 Majors, 4 Nits; see the second table. Both reviewers ran; the round is NOT clean.
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

## Second reviewer (egm-codebase-details), same round, against the working tree of cloud/core-b
| # | sev | finding (short) | answer |
|---|---|---|---|
| F1 | Blocker | Y1 says the built code already passes the map at three sites; none exists in cloud/core-b (the install is on branch wip/cloud-core-b/F-install) | Z9 (state line); Z7 |
| F2 | Major | models.py:103 is Run.cost_usd and stays Decimal; the Reply field is at about 299 | Z10 |
| F3 | Major | incomplete reader list of cost_usd (k1b/loop.py Budget.charge, the demo pipeline, tests); Y2 must land with the install (charge lines deleted) | Z3, Z4, Z6 (as built in one integration branch) |
| F4 | Major | judge "pass 0" breaks tests that compare the judge cost | Z3 (as built: reply cost, 0 only when None) |
| F5 | Major | Y3 mechanism and where it works (openai_compat needs an edit to merge two requests) | Z1 (as built: the same mechanism, openai_compat edited) |
| F6 | Major | falsy tests read a genuine 0 as missing; openai_compat sum under-books; gemini turns a blocked answer's 0 output tokens into unknown | Z2 (as built: `is not None`; per-request None poisons the call); the gemini case is over-conservative (stated) |
| F7-F12 | Major | Y4: contradicts invariant 3, 4 and ii-meter point 10; the reconciliation claim is not true; a late settle after release is lost; adding the method to Store makes every custom store fail at start; cli.py dispatch: a release action would fall through to limits.reset and CLEAR THE KILL SWITCH unless branched before; the audit event has no numeric field | ESCALATIONS E6 (Y4 on hold); the cli.py fall-through is a design requirement for whoever builds it |
| F13 | Major | Y1 plumbing: _screen, _shadow and _submit take no map; None meaning; NO_MAP must be a sentinel compared by identity, not a truthiness test (an empty RunMap is falsy); Y1 overrides U2 | Z7 and Z11 |
| F14-F17 | Nit | consequences of Y2 for the CHANGELOG; Reply.attempts has no audit carrier; damaged-row behaviour; statement order for the release (row, spend, month, same as settle; claim with status recheck) | Z8, Z10; the statement order goes to E6 |
Checked, no defect: the grants and CHECK constraints for "expired -> settled with settled_usd = 0" would pass the migration guards (Y4 stays on hold for the reasons above); Y5 and Y6 verified.
