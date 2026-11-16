# Round 7 review (reviewer, egm-codebase-details persona)

## NOT CHECKED / NOT RUN (read first)
- Full suite not run (brief: no full suite). Only the r7 tests, my own fuzz scripts and a mutation subset.
- Mutation matrix stopped early: 18 mutants run (M04a/b, M18a/b/c, M20, M23, M29, M30, F1a-c, F2, F2b, F2c, F3 x2, F4), all KILLED. The rest of the matrix NOT run.
- r6 closure items F1-F14, S1 and mail F1-F6, G1-G4: only the ones listed CLOSED-with-proof below were run against hostile input. The rest were read in code only and are marked READ-ONLY, not proven.
- IMAP/SMTP slow trickle inside a single read: not tested.
- Changed old tests: only partly compared (about half). The out/R7/RESULTS.md was NOT read (I did not reach the cross-check).
- "At least 15 new tests fail on r6": I did NOT reach a complete named run of 15. The list of tests shown failing on r6 is partial; see below. This brief item is OPEN.
- No live service, no spend, loopback only, no prompt answered, no /dev touched.

## Closure table (r6 findings)
| Item | Status | Proof |
|---|---|---|
| burst.py loopback-only --url | CLOSED | real run refused non-loopback |
| start_all.sh ownership checks / fail_start exit 3 | CLOSED | real runs in sa.sh |
| run_real_check 429 config shapes | CLOSED | fuzz_rrc.py: no traceback, echo or class name |
| Mail F1 (IMAP user quoting/ASCII), F2 (secret ASCII trim), F3 (repr in stats/CA), F4 (TLS 1.2 floor) | CLOSED | mutants F1a-c, F2, F2b, F2c, F3x2, F4 all killed by r7 tests |
| Remaining F-numbers, S1, mail F5-F6, G1-G4 | READ-ONLY (not proven by a run) | code read only |

## New findings
| ID | Severity | Where | Failing input | Fix |
|---|---|---|---|---|
| N1 | Major | demo_only/bad_request.py BAD_REQUEST_ERRORS; demo_only/fake_hubspot.py _json (json.loads at ~233); also fakes_server._parse, fake_model_server /control and /v1/messages | request body of about 100000 nested `[` : json.loads raises RecursionError, not in the tuple, so a traceback is printed and no 400 is sent (reproduced with hs_fuzz.py) | add RecursionError to BAD_REQUEST_ERRORS and catch it where each parser catches only ValueError; add a nested-body test for every fake |
| N2 | Major | same family (fakes_server / fake_model_server / http_guard) | slow header drip: 81 s hold of a handler thread (drip.py) beyond the 20 s body deadline; the deadline covers the body only, not the headers | apply a total deadline to header reading too, or a per-connection timer that closes the socket |
| N3 | Minor (doc contradicts code) | docs/limits.md:112 and contract.md:151 say exit 1 = demo servers unreachable; server.py:1171 exits EXIT_ADAPTERS_UNREACHABLE = 7 (constants.py:275). docs/settings.md run_real_check text uses 6 and 1 correctly | n/a | change both sentences to 7 and keep 1 only for a traceback |
| N4 | Minor | tests/test_n8n_api_url.py `_message` helper is weaker than before (changed old test) | n/a | restore the old exact-text assertion |

Both N1 and N2 are in the defect class named in the brief (traceback / hang on bad input), so I rate them Major.

## New tests that fail on r6 (partial)
Run in tree-REV7-r6x (r6 code plus the r7 tests plus inert shims). Examples seen failing on r6 and passing on r7: the tests killed by the mutants listed above (exit_codes, mail_context, class_names, no_replace_of_special families). A full named list of 15 was not produced. Some r7 tests pass on both r6 and r7 (they pin nothing new); I did not finish listing them.

## Exit-code table versus docs
Table (constants.py): 1 check failed, 2 refused, 3 unreachable, 4 bad setting or path, 5 port, 6 stopped by the person, 7 adapters unreachable. Docs agree except N3.

## Verdict
Blockers: 0. Majors: 2 (N1, N2). Minors: 2 (N3, N4). Not clean: round 8 needed for N1/N2, plus the unfinished items above.
