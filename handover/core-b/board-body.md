## BACKLOG OF STANDING ORDER 016, state per item (so nobody has to ask again)
| # | item | state | where |
|---|---|---|---|
| 1 | requests/001.answer.md with the reader bound to the sender names; trigger-config fixes | DONE and pushed 06:17 UTC | requests/001.answer.md DRAFT 2; commit "code D-config: fix round 1"; core-a's test file against it: 92 passed, 17 failed (16 are its expected-failure marks now passing, 1 a changed refusal text) |
| 2 | requests/003.answer.md and corrected interfaces | DONE and pushed 06:08 UTC | requests/003.answer.md; interfaces/README.md 2.3; ii-meter.md (six reasons) |
| 3 | F-store build with review round 2 | DONE | source 8db9c29, fix round 1 (caps, sweep age), review-2 answered; core-a's 187 contract and T1 tests against it: 183 passed, 4 expected failures |
| 4 | ORDER 011: A-1, B-2, B role tests and mutants | DONE | A fix 15c86e5 with tests; B fix round 3 358361e with tests 6fb410a (also covers lead AB-1, AB-2: stop_state_mutants.py updated, 40 of 40 killed alone; CLI tests for still-ON and same-secret) |
| 5 | ORDER 013 refused-before-response mark | DONE | commits "code F: providers mark ..." (two) and tests/test_refused_before_response.py; request to core-c open (its gate ignores the mark on exhausted retries) |
| 6 | F-install review round and build | RUNNING | review rounds 1 and 2 answered (V and W sections); builder a70b774c on a local merge of core-c |
| 7 | reserve_mutants.py, stop_state_mutants.py | DONE, re-run on the head RUNNING | tests/reserve_mutants.py 31 of 31 and 26 of 26 by hand; agent ae79ea4d re-runs all four scripts on the head |
| 8 | docs for A, B, C, F | DONE for A, B, C, F-store; F-install's sentences come with its build | README.md, SECURITY.md, CHANGELOG.md, docs/stop-state-runbook.md |
| 9 | ONE batch whole-suite run when 1 to 7 are coded | NOT YET (batch run 2 at 06:00 covered A, B, C, F-store source) | batch run 3 after F-install lands, on a tree with core-c's gate |
| 10 | hostile re-read of A, B, C code | DONE; B findings with the lead (ESCALATIONS E5), A findings in A's fix round 3 (queued behind the running A agent) | tickets/ABC-hostile-review-1.md |
Lead review items of ORDER 016b: F-1 tests exist (tests/test_limits_reserve.py, contracts/test_store_spend.py, contracts/test_t1_reserve_cap.py, test_spend_reservations_pg.py incl. settle racing expire); F-2 and F-3 done (caps and sweep age validated); F-4, F-5, AB-5 done (docs); AB-4 running (ae79ea4d); AB-3 is the lead's.

## AGENTS (RESTART on the normal models after the Fable limit, 06:45 UTC; model set explicitly on every call; none on fable)
| id | role | model | what | started UTC | expected end | % | state | review round | retries | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| (starting) | builder | sonnet | F-store fix round 2: reservation id validated in both stores (the random-sequence test found: memory stores an id with a NUL, PostgreSQL raises DataError); worktree F4 | 06:46 | +15 min | 0 | starting | none | 0 | finding from tests/contracts/test_store_spend_model.py |
| (starting) | builder | sonnet | step A fix round 3 (last): outage narrowed to connection-level errors; unwritable list retried once per reconcile; worktree A3 | 06:46 | +15 min | 0 | starting | none | 0 | hostile re-read findings 7 and 8 |
| (starting) | builder (tests) | sonnet | F-install tests: test_model_gate_install.py, contracts/test_meter.py, gate_install_mutants.py; worktree FI-tests on the wip branch | 06:46 | +40 min | 0 | starting | none | 0 | F-install built, no tests of its own |
| (starting) | reviewer (egm-codebase-details) | sonnet | hostile re-read of built F-store, provider mark, trigger config (the Fable one was cut off by the limit, no report) | 06:46 | +15 min | 0 | starting | 1 of 1 | 1 | restart |
| a5f7551d, ae79ea4d, a439a627 | Fable agents | fable | cut off by the Fable limit at 06:44; their commits were recovered (A fix 2 and its tests, the random-sequence test); a439a627 produced no report | | | | KILLED (limit) | | | see RESUME-NOTE |
| 40 earlier Fable agents | | fable | done before the limit | | | 100 | done | | | |

## SHELLS AND PROCESSES
| pid | command | started by | since | state | reason |
|---|---|---|---|---|---|
| background shell brworijga | batch run 1: full test suite, 3 workers, worktree /tmp/core-b-wt/batch at 737c93c | me | 05:41 to 05:44 | ended, exit 1 (3 failed) | the ONE batch run after A, B and C are coded (lead order); step B role tests are not in it yet |
| background shell bqt7v34iq | batch run 2: full suite, 3 workers, worktree /tmp/core-b-wt/batch at 21c869b | me | 06:00 to 06:03 | ended, exit 1 | lead: one batch run when A, B, C and F-store are coded; F-store tests and B fix 3 tests are not in it yet |
| 4886 | PostgreSQL 16.15 server, 127.0.0.1 port 55439, data in /tmp/core-b-pg, trust login, test data only | me | 05:31 | running | per-file tests of the builders (ORDER 005 item 4); I stop it when the builds end |

## TESTS
| suite | branch and SHA | run | passed / failed / errors | first failing line | state | reason |
|---|---|---|---|---|---|---|
| 4 existing files (test_p7_tick, warden_port/test_audit_chain, test_s2_audit, contracts/test_capabilities) | local/code-A 5b92c43 (now 5eb1e7e on cloud/core-b) | 1 | 127 passed / 0 failed / 5 skipped | none | done | step A builder's per-file check; Postgres cases skipped in that run |
| 6 files (k2_migrations, p2_postgres, p7_store, k5_round10_postgres, migration_numbers_guards, migration_numbers) | local/code-B 79f0d7f (80a07ce on cloud/core-b) | 1 | 304 passed / 0 / 0 | none | done | step B builder, PostgreSQL 16, owner login only |
| 14 files around config and pilot fixtures | local/code-C cbb9c2f (eb775a8) | 2 | 725 passed / 0 failed / 4 skipped | run 1: 24 failed, pilot fixture lacked prices_as_of | done | step C builder; one fixture line added |
| tests/test_audit_drain.py (new, 26 tests) | local/code-A-tests cdc5c9b (3394b2c) | 1 | 26 passed / 0 / 0 with PostgreSQL; 22 passed, 4 skipped without | none | done | evidence/A-tests-evidence.txt; E6 uses two threads, not two processes; invariant 8 has no test |
| 12 files around migrations, store, stop state | local/code-B 8f2fa9e (6662afe) | 1 | 449 passed / 0 / 0 | none | done | step B fix builder, PostgreSQL 16, owner login only |
| test_k5_producers, test_k5_round9 | cloud/core-b a1c1013 | 1 | 107 passed / 0 / 0 | none | done | producers rows for core-c's gate module |
| tests/test_price_constraint.py (new, 246 tests) | local/code-C-tests 35304a2 (737c93c) | 1 | 246 passed / 0 / 0 | none | done | evidence/C-tests-evidence.txt |
| test_stop_state_roles, test_stop_state_loop, test_stage_names, test_no_hardcoded_values | cloud/core-b 7afdab2 | 1 | 218 passed / 0 / 0 | none | done | evidence/B-tests-after-fix.txt; real non-superuser logins on PostgreSQL 16; before the fix: 5 failed, 99 passed (evidence/B-tests-evidence-before-fix.txt) |
| step B mutants by hand (tests/stop_state_mutants.py --hand) | cloud/core-b 2110ab3 | 2 | 17 killed / 1 SURVIVED | reset: ON CONFLICT is removed | done | evidence/B-mutants-after-fix.log; the survivor needs a two-resets test with the flag row missing (ticket S6); 2 pending mutants (serial id, loop hunk) still not in the list |
| 8 audit and tick files | local/code-A2 b90e368 (15c86e5) | 1 | 248 passed / 0 / 0 | none | done | step A fix builder, PostgreSQL 16 |
| tests/test_audit_drain.py after fix round 1 (150 tests) | local/code-A-tests2 929b5d5 | 1 | 150 passed / 0 / 0 | none | done | evidence/A-fix1-tests-evidence.txt |
| F-store builder's list (14 files) | local/code-F 9473bb2 (8db9c29) | 1 | 673 passed / 0 / 0 | none | done | PostgreSQL 16 |
| tests/audit_drain_mutants.py on the fixed code | 0b0b150 | 1 | 11 of 13 good | M4, M5: SNIPPET NOT FOUND | being re-anchored | the source fix changed the lines |
| tests/price_mutants.py | cad5069 | 1 | 20 of 20 good, 1 hole listed | routes-not-sorted mutant survives | being closed | |
| landed test files together (stop state, audit drain, price), -n 3 | f40f369 | 1 | 475 passed / 2 failed / 1 error | ConfigError: roles other than the reset role could clear a stop ...: sb_mo_... | done | evidence/landed-tests-run-1.txt. Cause: the step B who-else check reads every role of the server and trips over roles other tests create at the same moment (ESCALATIONS E4, step B is at its 3-try cap). Serial run: 175 passed, 1 failed (a stale pin, fixed) |
| tests/audit_drain_mutants.py, tests/price_mutants.py | f40f369 | 2 | 18 of 19 good; 22 of 22 good | M1 the STEPS row is removed | open | M1's killer now ends differently on the head (two test commits met); to be re-pinned with the F-store mutant work |
| F-store test files (contract, T1 with 50 connections, limits, crash and roles) | local/code-F-tests 92aabbd | 1 | 471 passed / 0 / 0 | none | done | evidence/F-store-tests-evidence.txt; written before the cap validation fix |
| mark and cap validation tests | local/code-F3 3aa3ba7 | 1 | 425 passed / 0 / 0, 1 skipped | none | done | |
| core-a's tests/test_trigger_config.py against my fixed config code | cloud/core-b b2547a2 with their file copied in, not committed | 1 | 92 passed / 17 failed, 20 skipped | Regex pattern did not match: 'secret names used by both' | done | 16 are their expected-failure marks that now pass; 1 is a refusal text I changed; told core-a in requests/001.answer.md |
| core-a's tests/contracts/test_store_spend_reservations.py and test_t1_reserve_cap.py against my store code | cloud/core-b 20bc17d with their two files copied in, not committed | 1 | 183 passed / 0 failed, 4 expected failures | none | done | their file, my code; PostgreSQL 16 |
| full suite, batch run 2 | 21c869b | 1 | 11249 passed / 13 failed / 1 error, 1 skipped, 193 s | tests/test_audit_drain.py f2: assert 0 == 1 | done | evidence/batch-run-2.log (last 120 lines). NEW, mine: 11 failures in tests/test_audit_drain.py (the fix-round tests picked the LAST tick step, and F-store added a step after audit_drain): fixed by selecting the step by name, re-run 150 of 150. 1 ERROR in tests/test_stop_state_roles.py::test_h2: passes when run alone; cause NOT established (the shared test database had two other agents creating roles at the same time). Not from my code: demo dblink test (needs a server on the default socket), vendor-name guard on handover/BRIEF-PREAMBLE.md |
| full suite, batch run 1 | cloud/core-b 737c93c | 1 | 11129 passed / 3 failed / 0 errors, 1 skipped, 208 s | psycopg SqlclientUnableToEstablishSqlconnection (dblink to socket port 5432) | done | evidence/batch-run-1.log. 1 NEW in my file: test_stage_names flagged the parameter name in tests/test_price_constraint.py, fixed and re-run (343 passed on the two files). 2 not from my code: demo dblink test needs a PostgreSQL on the default socket (this container's runs on port 55439); test_no_reference_material flags a vendor name in handover/BRIEF-PREAMBLE.md (the lead's file on this handover branch) |

## QUEUE ITEMS
| # | state | % | evidence file | tries | reason |
|---|---|---|---|---|---|
| Q1 capability probe | DONE | 100 | CAPABILITY.md, evidence/capability-raw.txt | 1 | no Docker service, no PostgreSQL 14 or 17, gh login invalid; PostgreSQL 16 works |
| Q2 lane map | DONE | 100 | LANE-MAP.md | 1 | test names come from a text search, not a run; some modules marked UNVERIFIED in the file |
| Q3 to Q9 baselines | SKIPPED BY LEAD | 0 | none | 0 | lead runs them on the laptop |
| T1 plan read-back | DONE | 100 | PLAN-READBACK.md | 1 | 4 conflicts between inputs and 4 questions listed there |
| INTERFACES (i) store methods, (ii) reserve/settle API | DONE | 100 | interfaces/README.md, ii_meter.py, i_store_spend.py | 2 | VERSION 2 = the lead's smaller shape; version 1 (mine, from the branches) withdrawn after 5 minutes: my slip, see DECISIONS.md; not reviewed, not run |
| T2 tickets (A, B, C, F-store, F-install) | RUNNING | 70 | tickets/A-audit-drain.md, F-store.md, F-install.md done; B, C by agents | 1 | F tickets = lead drafts plus my checks and decisions |
| REQUEST 003 from core-a (interface (i) questions) | DONE | 100 | requests/003.answer.md; one real defect found by it (caps not validated), fix running | 1 | |
| REQUEST 002 from core-a (README and SECURITY text for the endpoint) | READY | 0 | | 0 | next for me |
| ORDER 013 refused-before-response mark | RUNNING | 10 | | 1 | |
| REQUEST 001 from core-a (config for step D), ORDER 012 fixes | RUNNING (fix round 1) | 70 | requests/001.answer.md (names and refusal texts), code D-config commit | 1 | test file for the block not written yet (core-a offered it) |
| BUILD A audit drain | DONE except mutant script and batch run 2 | 95 | commits 5eb1e7e (source), e5a64ee (docs), 3394b2c (tests); evidence/A-tests-evidence.txt | 1 | full suite not run yet (one batch run for A, B, C) |
| BUILD F-install | RUNNING | 5 | none yet | 1 | lead GO; built on a local merge of core-c (not pushed): its commits may not apply to cloud/core-b alone |
| BUILD F-store | DONE except batch run 3 | 95 | source 8db9c29, fix round 1, tests and mutants; evidence/F-store-tests-evidence.txt | 1 | lead GO BUILD F-store |
| BUILD B stop state | LEAD TOOK OVER the who-else check (ORDER 015); rest done | 92 | commits 80a07ce, 6662afe, 8bb386f (docs), 7afdab2 (role tests, mutants); evidence/B-tests-after-fix.txt | 2 | review round half done; 2 mutants not run after the fix; not in a full-suite run yet |
| BUILD C price constraint | DONE except batch run 2 | 97 | commits eb775a8 (source), 388c9a0 (changelog), 737c93c (tests); evidence/C-tests-evidence.txt | 1 | ticket review round and the batch run not done |
| T3 EGM review rounds | DONE (all ordered rounds run; none clean; all answered in text) | 100 | tickets/F-install-review-1.md; | tickets/C-review-1.md (0 Blockers, answered); F-install round running; | tickets/F-store-review-1.md, B-review-1.md (NOT clean, answered); F-store round 2 running; C and F-install not started (one stage at a time) | 1 | tickets/F-store-review-1.md (NOT clean: 2 Blockers, 19 Majors; all answered in the ticket, answers not re-reviewed; ESCALATIONS.md E2) | 1 | next: ticket B, then C, then F-install, one after the other |
| T4 test files for other sessions | WAIT | 0 | | 0 | starts when interfaces are published; owner allowed wip/cloud-core-b/* at 05:21 |

## RESTARTS
| time | kind | what was running | lost | restarted | missing |
|---|---|---|---|---|---|
| none | | | | | |

## LOOPS
| item | tries | review rounds | last error | reason |
|---|---|---|---|---|
| tests/test_audit_drain.py fix-round tests | 2 | 0 | picked the last tick step by position | two agents changed the step list and its tests in parallel; my instruction to the test writer did not warn about it |
| tests/test_price_constraint.py | 2 | 0 | stage-word guard flagged a parameter name | the test writer did not run the guard test; fixed by a rename |
| step B source | 2 | 0 | serial stop id lets the runtime login block a later stop; test pin test_k5_fixes2 missed; limits-unavailable hunk skipped | built from the lead draft before the ticket check finished (lead order: build at once) |
| interfaces | 2 | 0 | none | version 1 published before the lead's draft arrived, then replaced by the lead's shape |

## LOST OR INTERRUPTED
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|
| none | | | | |

## LEAD ACTIONS NEEDED
- E1: the session cron was refused twice (second time after the owner's GO). Owner: allow it in the cloud session settings, or accept a board at the end of each tool batch.
- QUESTIONS.md 1 to 4 (cron fallback, which baseline test fails, step A build without extra GO, local PostgreSQL 16 for my lane run).
- core-c ESCALATION E2 (strict mask check would refuse normal runs): needs the lead's ruling before ticket F-install can be final.
- Lead: handover/BRIEF-PREAMBLE.md contains a vendor name that tests/test_no_reference_material.py refuses (rule 15 text). It fails the suite on every cloud branch that carries the handover folder; it is your file, I did not touch it.
- ESCALATIONS.md E5: the hostile re-read found 1 Blocker and 5 Majors in built step B code (search path decoy, reset command steering an operator to erase a fresh stop, reset secret readable by the runtime, PostgreSQL 17 table lock). B is at its 3-try cap: the lead decides and builds.
- ESCALATIONS.md E4: step B's who-else-can-clear check refuses healthy set-ups on a shared server and makes the role tests interfere in parallel; B is at its 3-try cap, so I stopped. Lead: decide the one-clause fix or take it over. Until then run tests/test_stop_state_roles.py with -n 1 on its own server.
- requests/to-core-c-1-exhausted-mark.md: core-c's gate ignores the unbilled mark on errors that used up their retries (429, refused connections).
- requests/002.answer.md: two points for the lead (default runs at a time 1 or 4; comparing the approvals secret with trigger secrets).
- My slip: I missed ORDER 012, ORDER 013 and core-a requests 002 and 003 for about 12 minutes (I searched the orders file for the wrong heading). 003 is answered (requests/003.answer.md, interface README 2.3); 012 and 013 are being built; 002 is next.
- Duplicate work: core-a wrote 102 contract tests and a T1 file for interface (i) while my own test writer does the same. Lead: say which T1 file is kept.
- ESCALATIONS.md E2: F-store ticket review was not clean; three of my answers change the lead's draft design (settle returns row and applied; expired rows are always claimed by the first settle; expiry age from the stuck-run age). Lead: OK or CHANGE before GO BUILD F.
- interfaces/README.md is now version 2.1 (the gate's two calls are unchanged).
- inputs/request-from-core-a-001-config-triggers.md: seen; I build it after step C lands (both edit config.py), answer follows in requests/.
- PLAN-READBACK.md section 4: four conflicts between the inputs; I follow the later file in each.
