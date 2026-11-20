## AGENTS
| id | role | model | what | started UTC | expected end | % | state | review round | retries | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| abc08a01 | builder | fable | F-store: migration 0007, store reserve/settle/expire/purge, Limits.reserve and settle, sweep tick step; worktree F | 05:50 | +30 min | UNVERIFIED | running | round 2 alongside | 0 | lead ORDER 010 GO BUILD F-store |
| a52e1b89 | builder (fix) | fable | step B fix round 3 (LAST): schema-qualified stop state, who-else-can-clear check, reset reports the real state, lead findings B-2 B-4 B-8; worktree B | 05:50 | +20 min | UNVERIFIED | running | none | 2 | ticket B review Blocker (temporary tables) and lead ORDER 011 |
| a71d4b00 | builder (tests) | fable | tests for the step A fix (incl. INSERT revoked from a real runtime login) and 6 mutants; worktree A-tests | 05:53 | +15 min | UNVERIFIED | running | none | 0 | the fix builder did not prove A-1 on a real role |
| ade5688d | builder (fix) | fable | step A fix round 1: commit 15c86e5 (chain.py, SECURITY.md) | 05:50 | done | 100 | done | none | 0 | 248 passed on 8 audit test files; A-1 on a real role NOT proven by the builder |
| adbe69e5 | builder (tests) | fable | tests/audit_drain_mutants.py and tests/price_mutants.py in the runner format; worktree M | 05:50 | +20 min | UNVERIFIED | running | none | 0 | lead ORDER 008: a guarantee with no mutant script counts as not run |
| a9de240c | reviewer (egm-implementation-readiness) | fable | EGM round 2 of 3 on the RESOLUTION section of tickets/F-store.md | 05:51 | +6 min | UNVERIFIED | running | 2 of 3 | 0 | lead ORDER 010 item 5 |
| a3b14e25 | reviewer (egm-codebase-details) | fable | same round: checks the changed settle design for deadlocks and replay | 05:51 | +8 min | UNVERIFIED | running | 2 of 3 | 0 | same stage |
| a0f43330, ac4fc2b1 | reviewers (egm) | fable | ticket B round 1: 1 Blocker, 18 Majors, 15 Nits; report tickets/B-review-1.md | 05:43 | done | 100 | done | 1 of 1 | 0 | answered in the ticket (S1 to S12) and in fix round 3 |
| a86831dc | builder (tests) | fable | step B role tests and mutants: 7afdab2 | 05:38 | done | 100 | done | none | 0 | 218 passed on the fixed code; mutants on the fixed code: 17 killed, 1 survived (ON CONFLICT removed) |
| a87e21e9, a86102dd | builders (tests) | fable | step C tests 737c93c (246), step A tests 3394b2c (26) | 05:32 | done | 100 | done | none | 0 | |
| a6122910, a5a79255, a862ea5f, a64fad56, a27419bd | builders | fable | B fix 2, B, C, A, D-config source commits | 05:27 | done | 100 | done | | | |
| a5de8cd7, adaa7521 | reviewers (egm) | fable | F-store round 1: tickets/F-store-review-1.md | 05:33 | done | 100 | done | 1 | 0 | |
| 5 lookups, 2 dry-run reviewers | | fable | notes, lane map, tickets B and C, ORDER 001 | 04:10 | done | 100 | done | | | |

## SHELLS AND PROCESSES
| pid | command | started by | since | state | reason |
|---|---|---|---|---|---|
| background shell brworijga | batch run 1: full test suite, 3 workers, worktree /tmp/core-b-wt/batch at 737c93c | me | 05:41 to 05:44 | ended, exit 1 (3 failed) | the ONE batch run after A, B and C are coded (lead order); step B role tests are not in it yet |
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
| REQUEST 001 from core-a (config for step D) | DONE except tests | 80 | requests/001.answer.md (names and refusal texts), code D-config commit | 1 | test file for the block not written yet (core-a offered it) |
| BUILD A audit drain | RUNNING (fix round 1) | 85 | commits 5eb1e7e (source), e5a64ee (docs), 3394b2c (tests); evidence/A-tests-evidence.txt | 1 | full suite not run yet (one batch run for A, B, C) |
| BUILD F-store | RUNNING | 5 | none yet | 1 | lead GO BUILD F-store |
| BUILD B stop state | RUNNING | 80 | commits 80a07ce, 6662afe, 8bb386f (docs), 7afdab2 (role tests, mutants); evidence/B-tests-after-fix.txt | 2 | review round half done; 2 mutants not run after the fix; not in a full-suite run yet |
| BUILD C price constraint | DONE except review and batch run | 90 | commits eb775a8 (source), 388c9a0 (changelog), 737c93c (tests); evidence/C-tests-evidence.txt | 1 | ticket review round and the batch run not done |
| T3 EGM review rounds | RUNNING | 55 | tickets/F-store-review-1.md, B-review-1.md (NOT clean, answered); F-store round 2 running; C and F-install not started (one stage at a time) | 1 | tickets/F-store-review-1.md (NOT clean: 2 Blockers, 19 Majors; all answered in the ticket, answers not re-reviewed; ESCALATIONS.md E2) | 1 | next: ticket B, then C, then F-install, one after the other |
| T4 test files for other sessions | WAIT | 0 | | 0 | starts when interfaces are published; owner allowed wip/cloud-core-b/* at 05:21 |

## RESTARTS
| time | kind | what was running | lost | restarted | missing |
|---|---|---|---|---|---|
| none | | | | | |

## LOOPS
| item | tries | review rounds | last error | reason |
|---|---|---|---|---|
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
- ESCALATIONS.md E2: F-store ticket review was not clean; three of my answers change the lead's draft design (settle returns row and applied; expired rows are always claimed by the first settle; expiry age from the stuck-run age). Lead: OK or CHANGE before GO BUILD F.
- interfaces/README.md is now version 2.1 (the gate's two calls are unchanged).
- inputs/request-from-core-a-001-config-triggers.md: seen; I build it after step C lands (both edit config.py), answer follows in requests/.
- PLAN-READBACK.md section 4: four conflicts between the inputs; I follow the later file in each.
