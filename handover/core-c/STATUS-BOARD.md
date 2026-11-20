UPDATED_UTC: 2026-11-20T06:14:40Z
SESSION: core-c
ORDER: 004 (with 002 and 003 standing)
STATE: WORKING
BOOT_ID: 70253298
ITEMS_TOTAL: 18
ITEMS_OPEN: 8
PERCENT: 87
AGENTS_RUNNING: 3
CAPACITY: load 4.9 of 4 cores, mem 0/15 GB, disk 60G free, 14% used, light agents 3, heavy agents 0
DISK: / 60G free, 14% used; git worktrees 4; 58M	/tmp/claude-0;397M	/root/.cache/uv;
SESSION_RESTARTS: 0
CONTAINER_RESTARTS: 0
INTERRUPTED: none
FAILED: combined tree: producers registry test (SPINE patch); stage-name test (sample word in a gate test, fix sent). G2: fix verification running
NEXT: resolve ticket G review; pick the builders' work into "code F:" and "code G:" commits; then G2, G3
PUSHED_UTC: 2026-11-20T06:13:26+00:00

(11:44 IST. Header numbers are measured by the board script; table rows are written by the session and can be up to one tool batch old.)

## AGENTS
| id | role | model | what exactly it is doing | started UTC | expected end | percent | state | review round n of cap | retries | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| ad708163 | builder | fable | code G7 (ORDER 012): re-runs the context patterns after the sweep in redact() so one pass masks a bank account beside a bank code; mirror shapes, timing test; traces every caller of redact_untrusted; writes tickets/G7-context-after-sweep.md | 05:59 | 06:25 | 85 | running | n/a | 0 | G7 main part DONE and verified: one pass masks the account (28 of 42 new tests failed before, all pass now; timing 0.204 s -> 0.263 s on 100,000 characters, linear). Now the follow-up of ORDER 012 item 2: the tool error path feeds redact_untrusted its own output; about 4 lines in redact._mask |
| aa4ceadd | builder | fable | applies the lead's code review round 1 of the gate (ORDER 011): new settle rule, map write without clear(), ast-based guard test, mutants, stated limits; main checkout | 05:56 | 06:20 | 70 | running | 1 of 3 (lead review) | 0 | ORDER 011 fixes, seen in the files: enforce rework present; settle rule with the refused_before_response predicate present; clear() removed from redact_text; gate_mutants.py being extended; also switching to core-b ii_meter.py. NOT yet verified by its final test run |
| a7728368 | builder | fable | ORDER 010: changes the one test clause to the stricter has_mixed_script rule, pins it, writes the Unicode 15.1.0 requirement into README/CHANGELOG/ticket G; main checkout, other files than the gate agent | 05:56 | 06:10 | 100 | done | n/a | 0 | finished: ORDER 010 applied (commit 9cb56b5). textnorm batch 939 passed, 0 failed; 2 mutants for the rule run and killed. Unicode: the shipped tables cannot remove the interpreter dependency (normalize, category, name still come from unicodedata). Not run: real Python 3.12, 238 of 240 mutants |
| aa070de5 | builder | fable | code G3: ports the fold scan of core/P2d-1 (its own 14 files) onto the fold in its own worktree /tmp/core-c-g3, branch wip-g3-p2d cut from wip-g1-fold; adds the redactor action counter asked by the review; one test batch with 2 workers | 05:47 | 06:40 | 100 | done | n/a | 0 | finished: port on wip/cloud-core-c/g3-p2d-port (tip ef09bf5, 6 commits). Final batch 8237 passed, 1 failed (the fold test already fixed on cloud/core-c by ORDER 010), 19 skipped, 4 xfailed. One of P2d-1 tests edited and one rule change beyond a port (QUESTIONS 9-11). NOT RUN: both mutant runners, Python 3.12, full suite |
| aed773ca | builder | fable | code G2: cherry-picks core/P1d-a (6875f27) onto main in its own worktree /tmp/core-c-g2 (local branch wip-g2-p1d-a), checks every approval path redacts before defang, adds path tests, runs its test batch with at most 2 workers | 05:43 | 06:15 | 90 | running | n/a | 0 | fix try 1: two fix commits exist (73d624c gate/redact fix; 22d2e0d channel.py fix, SPINE-owned file, separate). Pushed to wip/cloud-core-c/g2-p1d-a. Waiting for its test batch and mutant run: NOT verified yet |
| a9910106 | evidence runner | fable | P1c probe: runs base64, host-name and bare-number inputs against main's redactor from a clean export in /tmp/core-c-p1c; writes evidence/P1c-probe.md | 05:34 | 05:50 | 100 | done | n/a | 0 | finished: base64 52 of 142 cases leak (no decoded view; blobs under 40 characters pass unchanged), host names 28 of 44 (4 kept on purpose), bare numbers 24 of 43 not masked (accepted property). evidence/P1c-probe.md |
| a2bfa183 | builder | fable | code G0 (runmap._scan split + is_masked) and code F (guard/model_gate.py) with their two test files, in the main checkout; ruff and the tests of those files only | 05:32 | 06:05 | 100 | done | n/a | 0 | finished: G0 + gate wrapper committed (c035b85, 45156c1). 140 tests pass, 2 strict xfail (E3), mutants 12 of 12, ruff and bandit clean. tests/test_k5_producers.py red as expected (SPINE patch). Confirmed by run: one redact pass leaves a bank account readable |
| a7a352c6 | builder | fable | code G1: folds rebase/P1b-o140 + fix rounds 1 and 2 of core/P1b-fixwip onto main in its OWN git worktree, local branch wip-g1-fold; re-pins; runs the textnorm tests once | 05:32 | 06:30 | 100 | done | n/a | 0 | finished: fold built, 5 commits, pushed as wip/cloud-core-c/g1-fold. 1 test FAILS (two heads give has_mixed_script opposite rules, E4). Batch: 1 failed, 8616 passed, 17 skipped. Not run: Python 3.12, mutant runner, bandit, full suite |
| a04f3d03 | reviewer | fable | EGM plan review of tickets/G-text-deltas.md, implementation readiness | 05:32 | 05:40 | 100 | done | 1 of 1 | 0 | finished: ticket G NOT READY: 3 Blockers, 14 Majors, 6 Nits. Blocker 1 is a fail-open in the planned is_masked rule (count of placeholders misses a swap): sent to the builder at once |
| aceaf250 | reviewer | fable | EGM plan review of ticket G, code facts on main and on the input heads through git objects only | 05:32 | 05:42 | 100 | done | 1 of 1 | 1 | finished at try 2: 4 Blockers, 7 Majors, 5 Nits, nothing executed. Claims redact_text is not idempotent in two shapes (being run by the builder) and that my proposed gate.py docstring sentence was false (fixed) |
| a5098f29 | builder (tests only) | fable | writes NEW tests/test_grants_negative_roles.py and tickets/B-mutant-cases.md for step B; may try once to start PostgreSQL 16 as the postgres user under /tmp/core-c-pg | 05:28 | 05:45 | 100 | done | n/a | 0 | finished: tests/test_grants_negative_roles.py (566 lines, 33 tests). No database: 19 passed, 13 skipped, 1 xfailed. Local PostgreSQL 16: 31 passed, 2 xfailed. Server stopped, data folder removed; one zombie postgres pid 4036 of its own remains |
| a8830db0 | reviewer | fable | EGM plan review of tickets/F-gate-wrapper-body.md against the implementation-readiness standard (egm:egm-implementation-readiness) | 05:24 | 05:32 | 100 | done | 1 of 1 | 0 | finished: ticket F NOT READY, 6 Blockers, 6 Majors, 5 Nits; all opened line citations accurate |
| a112f9c8 | reviewer | fable | EGM plan review of ticket F: checks every cited file:line and code reuse (egm:egm-codebase-details) | 05:24 | 05:34 | 100 | done | 1 of 1 | 0 | finished: ticket F NOT CLEAN, 2 Blockers, 9 Majors, 5 Nits; one is a real design conflict (E2) |
| a0321052 | lookup | fable | Q2: reads repo docs and src/hadavin_sdk layout, writes LANE-MAP.md | 05:20 | 05:30 | 100 | done | n/a | 0 | finished 05:22, LANE-MAP.md written (48 lines, 16 modules); guard/textnorm* does not exist on main |
| aa61ba5c | lookup | fable | T1: reads plan-v2, v3, v4-final and the two round-3 reviews, writes PLAN-READBACK.md | 05:20 | 05:35 | 100 | done | n/a | 0 | finished 05:24, PLAN-READBACK.md written (164 lines); one cited fact DIFFERS (Runtime built in 7 test files by literal grep, review said 17) |
| a33582f6 | lookup | fable | reads input heads core/P1a, rebase/P1a, core/P1b, P1b-fixwip, rebase/P1b-o140 with git diff only; writes tickets/G-survey-P1a-P1b.md | 05:24 | 05:40 | 100 | done | n/a | 0 | finished; tickets/G-survey-P1a-P1b.md (157 lines). Best head rebase/P1b-o140 (851ad92) but it lacks the two fix rounds of core/P1b-fixwip; nothing was executed |
| aeb4ebd0 | lookup | fable | reads core/P2d-1, core/P1d-a, finds what P1c is in the plans, checks runmap/redact/gate lines; writes tickets/G-survey-P2d-P1d-P1c.md | 05:24 | 05:40 | 100 | done | n/a | 0 | finished: survey file written (199 lines); P1c has no code, ticket or corpus on any ref |
| a39c0f8b | reviewer | fable | ORDER 001 dry run, style review of the 3-line paragraph | 04:11 | 04:11 | 100 | done | 1 of 1 | 0 | proof only, finished |
| a997db3c | reviewer | fable | ORDER 001 dry run, comprehension review of the 3-line paragraph | 04:11 | 04:12 | 100 | done | 1 of 1 | 0 | proof only, finished |

## SHELLS AND PROCESSES
| pid | command in short | started by | since | state | reason |
|---|---|---|---|---|---|
| 4036 | postgres (defunct zombie) | agent a5098f29 | 05:30 | defunct | left by the stopped test server; holds no resources; not killed by pattern |

## TESTS
| suite or file | branch and SHA | run number | passed / failed / errors | first failing line | state | reason |
|---|---|---|---|---|---|---|
| tests/test_grants_negative_roles.py | cloud/core-c working tree on 51c9fc4 source | 1 (no database) | 19 passed / 0 failed / 13 skipped, 1 xfailed | none | done | pure-Python layer |
| tests/test_grants_negative_roles.py | same, local PostgreSQL 16.15 as user postgres | 2 | 31 passed / 0 failed, 2 xfailed (strict, step B gap) | first PG run: 3 failures in the new tests themselves (unqualified table names), fixed | done | PostgreSQL 17 (CI version) NOT RUN |
| evidence/p1c_probe.py (probe, not a test suite) | clean export of main 51c9fc4 | 2 (identical) | 229 cases: 80 leak a protected value, 24 bare numbers unmasked by decision | base64 of a short secret line passes unchanged | done | evidence for ticket G4 |
| 67 files: textnorm, evidence, runmap, injection users | wip/cloud-core-c/g1-fold 8e4d234 | 1 | 8616 passed / 1 failed / 0 errors, 17 skipped | tests/test_textnorm_round1.py::test_m16_... assert (True is False) | done | NEW failure, cause known (E4); skip reasons not listed |
| tests/test_textnorm_perf.py (serial) | same | 1 | 17 passed / 0 failed | none | done | wall-clock ceilings |
| 56 files: approvals and redact users + tests/test_p1d_a_paths.py | wip/cloud-core-c/g2-p1d-a 4bd78f6 | 1 | 7866 passed / 2 failed / 0 errors, 20 skipped | tests/test_p1d_a_rows.py::test_no_link_outside_code_on_card | done | both failures INHERITED: same two fail on input head 6875f27 (run separately) |
| tests/p1d_a_mutants.py | same | 1 | 0 of 50 judged | the unmutated copy does not pass its tests | BLOCKED | baseline red because of the 2 failures above |
| 13 files: G0, gate, fold meta/scan/round tests, producers, grants | cloud/core-c 84b46d1 (G0 + F + fold combined) | 1 | 422 passed / 2 failed / 0 errors, 13 skipped, 3 xfailed | tests/test_k5_producers.py (module not registered) and test_m16 (E4) | done | both failures known and with their owner; ruff check clean on src tests tools |
| tests/gate_mutants.py | working tree before commit 45156c1 | 1 | 12 of 12 good; problems: [] | none | done | ORDER 008 item 1 |
| tests/test_textnorm*.py + notices + no_hardcoded_values | cloud/core-c working tree after ORDER 010 (now 9cb56b5) | 2 | 939 passed / 0 failed | none | done | E4 closed by the lead's decision |
| 42 files that use redact + tests/test_redact_context_after_sweep.py | cloud/core-c working tree at 0b617c1 | 1 | 7162 passed / 2 failed, 32 skipped, 1 xfailed | tests/test_stage_names.py::test_the_old_stage_word_is_gone (literal in tests/test_runmap_enforce_map.py:231) | done | both failures are outside G7; the stage-name one is being fixed by the gate agent |
| redact, textnorm and runmap users (G3 batch) + 3 perf | wip/cloud-core-c/g3-p2d-port ef09bf5 | 2 | 8237 passed / 1 failed, 19 skipped, 4 xfailed | tests/test_textnorm_round1.py::test_m16 (known from the fold, fixed on cloud/core-c) | done | first batch had 6 new failures, all closed in the builder's commit 6 |

## QUEUE ITEMS
| item | state | percent | evidence file | tries | reason |
|---|---|---|---|---|---|
| Q1 capability probe | DONE | 100 | CAPABILITY.md | 1 | raw command output saved |
| Q2 lane map | DONE | 100 | LANE-MAP.md | 1 | agent finished; tests column is a name search, not measured coverage |
| Q3-Q9 baselines | SKIPPED-BY-LEAD | 100 | none | 0 | GO message item 4: the lead runs these on the laptop and puts results in inputs/ |
| T1 plan read-back | DONE | 100 | PLAN-READBACK.md | 1 | agent finished; branch heads and old plans not read by it |
| T2 prep: survey of input heads for step G | DONE | 100 | tickets/G-survey-*.md | 1 | both survey files written; nothing was executed on any head |
| T2 ticket G text deltas | DONE (draft) | 100 | tickets/G-text-deltas.md | 0 | six parts G0-G6; G4 (P1c) blocked on inputs that are not in this repository; 7 lead decisions inside |
| T2 ticket F gate wrapper body | DONE (draft) | 100 | tickets/F-gate-wrapper-body.md | 0 | written by the session itself while 3 agents run; 5 open questions inside; EGM round is next |
| T3 EGM review of ticket G | DONE | 100 | tickets/G-review-1.md | 1 | NOT CLEAN after the one round: 6 Blockers, 16 Majors, 8 Nits merged; tickets/G-review-1.md; 5 points go to the lead |
| T3 EGM review of ticket F | DONE | 100 | tickets/F-review-1.md | 1 | NOT CLEAN after the one round: 6 Blockers, 9 Majors, 7 Nits merged; resolved or assumed in tickets/F-review-1.md; one escalated (E2) |
| T4 step B grants negative tests + mutant cases | DONE | 100 | tests/test_grants_negative_roles.py, tickets/B-mutant-cases.md | 1 | committed as "code B:"; PostgreSQL 17 not run; mutants 11, 14, 15, 16 not applied; 12 cases wait for step B names |
| BUILD G0 + F (check-only function, gate wrapper) | DONE | 100 | evidence/F-G0-1.md | 1 | committed and pushed as "code G: G0" and "code F:"; as-built differences listed at the end of ticket F |
| BUILD G1 fold | DONE | 100 | evidence/G1-fold.md | 1 | fold on cloud/core-c, ORDER 010 clause changed and pinned, textnorm batch green (939 passed). Not run: Python 3.12, full mutant list, full suite |
| BUILD G2 P1d-a | RUNNING (fix try 1) | 90 | evidence/G2-p1d-a.md | 1 | P1d-a DECISION: option (a) of ORDER 009, fix with regression tests; two fix commits on wip/cloud-core-c/g2-p1d-a, verification running; NOT on cloud/core-c until green; if not green after try 2, left out (option b) |
| BUILD G3 P2d-1 port | DONE on its branch; WAIT pick | 90 | evidence/G3-p2d-port.md | 1 | verified on its own branch; picking onto cloud/core-c waits for the gate-fix and G7 follow-up agents to leave guard/runmap.py and guard/redact.py (conflicts expected there); 3 confirmations asked (QUESTIONS 9-11) |
| BUILD G4 P1c (base64 scan, whole host names) | WAIT gate fixes | 35 | evidence/P1c-probe.md, tickets/G4-P1c-redactor-gaps.md | 1 | both edit guard/runmap.py in the main checkout; starts when the ORDER 011 fix agent ends |
| BUILD G6 wording (docstrings) | WAIT lead OK | 0 | tickets/G-review-1.md (text revision 2) | 0 | two docstring edits; text needs the lead's OK |
| Gate: lead code review round 1 fixes (ORDER 011) | RUNNING | 70 | evidence/F-G0-1.md | 1 | B1 enforce rework: DONE (commit 45156c1, mutants 12 of 12 then). Settle rule (ORDER 011): coded, not verified. Map clear() fix: coded (redact_text has no clear() now), thread test not verified. gate_mutants.py: exists, being extended. Switch to ii_meter.py: in progress |
| BUILD G7 context patterns after the sweep (E3) | RUNNING | 85 | evidence/G7-1.md, tickets/G7-context-after-sweep.md | 1 | main fix verified (new file 42 + 3 perf passed; 22 existing redactor perf tests pass). Follow-up fix running. Its batch showed 2 red tests from other files: producers registry (SPINE patch) and a stage-name test tripped by a sample word in a gate test (sent to that agent) |

## RESTARTS
| time UTC | what | what was running | restarted | still missing |
|---|---|---|---|---|
| none | | | | |

## LOOPS
| item | tries | review rounds | last error | reason it keeps failing |
|---|---|---|---|---|
| step B PG tests | 2 | 0 | UndefinedTable in the agent's own tests | fixed at try 2 by schema-qualifying |
| EGM codebase review of ticket G | 2 | 1 | reviewer could not run git show (tools: Read, Grep, Glob only) | my brief error; fixed by exporting snapshots; this is the one allowed retry |
| G2 two failing property tests | 1 | 0 | see TESTS | defects of the input head; fix try 1 running |
| G3 test batch | 2 | 0 | 6 failures after the first batch (fold5 folds dashes and quotes) | closed at try 2 by a rule adaptation and test edits, listed for the lead |

## LOST OR INTERRUPTED
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|
| none | | | | |

## LEAD ACTIONS NEEDED
QUESTIONS 9-12 (new): G3 rule change for dashes and quotes, one P2d-1 test edited, record-test exemption, E5. SECURITY-WORDING-draft.md. Ticket F AS BUILT; requests/1 and 2 for SPINE; G4 3 decisions; G6 text rev 2. E1 cron denied.
