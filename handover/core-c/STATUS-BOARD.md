UPDATED_UTC: 2026-11-20T09:31:17Z
SESSION: core-c
ORDER: 004 (with 002 and 003 standing)
STATE: WORKING
BOOT_ID: 1e29cf8a
ITEMS_TOTAL: 41
ITEMS_OPEN: 25
PERCENT: 78
AGENTS_RUNNING: 8
CAPACITY: load 2.6 of 4 cores, mem 1/15 GB, disk 58G free, 17% used, light agents 8, heavy agents 0
DISK: / 58G free, 17% used; git worktrees 19; 988M	/tmp/claude-0;280M	/root/.cache/uv;
SESSION_RESTARTS: 0
CONTAINER_RESTARTS: 1
INTERRUPTED: all agents of the earlier tier were stopped at ~06:36 UTC; everything restarted on claude-sonnet-5-5 / claude-opus-5-5; none uses the retired tier
FAILED: none in merged-tree batch 4 (15 files: 2672 passed, 2 skipped, 5 xfailed). Not run: whole suite, perf on this tree, mutants, Python 3.12, PostgreSQL 17.
NEXT: LIVE only. ORDER 023 (09:30Z): E9(1) done (docstrings; redact.py module docstring in G7 r5, gate.py a4b2ce2), E9(3) is_masked: no consumer -> every promise withdrawn (Amendment 2), E9(2) builder running; E10 ticket G9 drafting then plan review; E11 ticket G10 + Latin split running; E12 Q9 builder runs both mutant lists; Q16 DONE (349e6ca0c: MIT licence checked, lock regenerated). 09:55Z target: E9 (1)-(3) done and E10 plan review started.
PUSHED_UTC: 2026-11-20T09:30:17+00:00

(15:01 IST. Header numbers are measured by the board script; table rows are written by the session and can be up to one tool batch old.)

## AGENTS
| id | role | model | what exactly it is doing | started UTC | expected end | percent | state | review round n of cap | retries | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| (new) q9 | builder | claude-sonnet-5-5 | Q9 mutants and tests (after the 240-mutant run) | Q9: a test and a mutant for each of the 30 code points; fix  | 09:11 | 09:50 | 1 | running | 1 | 0 | ORDER 022 Q9; evidence G1-mutants-run.md |
| (new) g7fix6 | builder | claude-sonnet-5-5 | G7 fix round 6 (after result review round 5) | G7 fix round 6 (bank_near hole in redact(), P x S walk, raw  | 09:17 | 09:55 | 1 | running | 6 | 0 | from G7-result-review-5.md |
| (new) g4v5 | drafter | claude-opus-5-5 | G4 v5 ticket (after plan review round 4: card-path detection loss, stale G7 anchors, G8 order, TB fixes) | review round: 4 done, 5 next | 09:22 | 09:55 | 1 | running | 5 | 0 | EGM draft step |
| (new) g8v3 | drafter | claude-opus-5-5 | G8 v3 ticket (after plan review round 2: IBAN opaque-token leak measured first, mutants run, G4 order) | review round: 2 done, 3 next | 09:27 | 10:00 | 1 | running | 3 | 0 | EGM draft step |
| (new) own | builder | claude-sonnet-5-5 | E9(2): _OWN_OUTPUT restricted to SECRET tokens only (test + 3 mutants) | EGM: build now, review after | 09:36 | 10:00 | 1 | running | 1 | 0 | ORDER 023 E9 |
| (new) g9 | drafter | claude-opus-5-5 | ticket G9: spelled sweep to a fixed point, bound 4, refuse if not converged | EGM plan review round 1 next (max 3) | 09:36 | 10:05 | 1 | running | 1 | 0 | ORDER 023 E10 |
| (new) g10 | drafter | claude-opus-5-5 | ticket G10: deadline in the text fold + published false-hit rates | EGM plan review round 1 next | 09:36 | 10:05 | 1 | running | 1 | 0 | ORDER 023 E11 |
| (new) split | evidence runner | claude-sonnet-5-5 | E11(c): split of Latin false hits (whole word / inside word / across spaces), low-load only | 09:36 | 10:00 | 1 | running | 1 | 0 | ORDER 023 E11 |

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
| gate, runmap users (ORDER 011 final batch) | cloud/core-c f16d48e | 3 | 6688 passed / 1 failed, 1 skipped | tests/test_k5_producers.py (module not registered: SPINE patch) | done | tests/gate_mutants.py: 27 of 27 good |
| 56 files approvals/redact users (P1d-a after fix) | wip/cloud-core-c/g2-p1d-a a3bae9b | 2 | 7879 passed / 0 failed, 20 skipped | none | done | mutants 48 of 51 good; 3 survived (2 inherited, A43 from the fix) |
| tests/contracts/test_t1_reserve_cap.py + tests/test_grants_negative_0007.py | core-b code 576f292 (worktree), PostgreSQL 16.15, Python 3.13 | 1 | 49 passed / 0 failed / 0 skipped | none | done | without a DSN: 9 passed, 40 skipped; PostgreSQL 17 NOT RUN |
| redact users + 3 new G7 files + warden_port | cloud/core-c 4864984 | 1 | 9663 passed / 1 failed, 35 skipped, 3 xfailed | tests/test_k5_producers.py (SPINE patch) | done | 25 perf-marked redactor tests pass serially (70 s); 100,000 characters: 0.206 s before, 0.484 s now |
| tests/test_grants_negative_roles.py + 0007 file | core-b 576f292 (worktree) and main, PostgreSQL 16.15 | 3 | 106 passed (core-b, DSN); 54 passed 52 skipped (core-b, no DSN); main: 37 passed 2 xfailed (DSN) | none | done | PostgreSQL 17 NOT RUN |
| undo/injection/app + textnorm + tools users (G1 fix batch) | cloud/core-c working tree (committed after) | 1 | 7707 passed / 0 failed | none | done | perf 19 passed; Python 3.12 NOT RUN |
| 135 files (pick worktree, before merge) | wip-pick cfda4d0 | 1 | 12392 passed / 2 failed, 108 skipped, 7 xfailed | tests/test_redact_fold_budget.py::test_dm_2_257 (fixed by the last commit); producers registry | done | perf 64 passed; gate mutants 66 of 66; ruff format --check fails on 2 files already unformatted on the base (runmap.py:123 nfkc, tests/test_undo_composes.py:21) |
| tests/test_k5_producers.py | cloud/core-c working tree after the producers commit | 1 | 25 passed / 0 failed | none | done | the lead's F-R3-C red is closed: guard/model_gate.py registered in guard/producers.py |

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
| BUILD G1 fold | DONE (fix round 1 verified) | 100 | evidence/G1-fold.md | 1 | B1, B2, M8 fixed and committed; open: M3-M7, M9-M10 of the fold review (time bound, over-matching, grounding widening for the lead, mutants not run) |
| BUILD G2 P1d-a | DONE and merged | 100 | evidence/G2-p1d-a.md | 1 | on cloud/core-c as d95a727 |
| BUILD G3 P2d-1 port | DONE and merged | 100 | evidence/G3-p2d-port.md | 1 | on cloud/core-c as d95a727 |
| BUILD G4 P1c (base64 scan, whole host names) | WAIT integration | 35 | evidence/P1c-probe.md, tickets/G4-P1c-redactor-gaps.md | 1 | P1c edits the same two files; it is built on the integrated tree |
| BUILD G6 wording (docstrings) | WAIT lead OK | 0 | tickets/G-review-1.md (text revision 2) | 0 | two docstring edits; text needs the lead's OK |
| Gate: lead code review round 2 fixes (ORDER 015) | DONE (built) | 100 | evidence/F-G0-1.md | 2 | committed in the WIP snapshots (verified by the builder: 66 of 66 mutants, 8596 passed); EGM result review round 2 running; lead review round 3 can start |
| BUILD G7 context patterns after the sweep (E3) | DONE, fixes running | 100 | evidence/G7-1.md, tickets/G7-context-after-sweep.md | 1 | fix round 1 (own-output hole) running now; fail-closed second pass, tail, budget, property corpus after the integration |
| Backlog 7: T1 reserve cap test + grants 0007 tests for core-b | DONE | 100 | evidence/T1-reserve-cap.md | 1 | committed as "code F: T1 ..."; 49 passed on core-b code + PostgreSQL 16; skips in this tree until core-b code is merged; PostgreSQL 17 not run |
| Backlog 4c: cross-lane read | DONE | 100 | CROSS-LANE.md | 1 | CROSS-LANE.md written; 5 mismatches listed for the lead |
| Backlog 9: SECURITY and README wording | RUNNING (session) | 50 | SECURITY-WORDING-draft.md | 1 | draft pushed; final list after the gate and G7 agents report their stated limits |
| Backlog 10: ONE whole-suite batch | WAIT items 1-6 | 0 | none | 0 | runs once when F, G0-G7 are coded and on one tree |
| Integration of G2 + G3 onto cloud/core-c | DONE | 100 | evidence/INT-g2-g3.md | 1 | verified in the worktree (11,542 passed); pick onto cloud/core-c running |
| EGM result review of the gate code (round 1) | DONE | 100 | tickets/F-result-review-1.md | 1 | NOT CLEAN: 1 Blocker, 14 Majors, 14 Nits merged; tickets/F-result-review-1.md; in-file findings with the builder, 6 escalated (E6), per-site install list for core-b written |
| Rework tests/test_grants_negative_roles.py against core-b's step B grant map | DONE | 100 | evidence/B-grants-rework.md | 1 | committed "code B:"; evidence/B-grants-rework.md; 6 findings about core-b grants in E7 |
| EGM result review of the G7 redactor change (round 1) | DONE (round 1) | 100 | tickets/G7-result-review-1.md | 2 | design + code reviewers: no Blocker, 10 Majors merged; one leak reproduced and being fixed; the rest after the integration |
| EGM sequence (owner order 12:15 IST): items built without a review step | RUNNING | 20 | EGM-LEDGER.md | 1 | ledger written; missing steps: result review of the fold (G1) and P1d-a (G2) started now; G7 plan review after its result review; drift reports for everything; result review of the test files (B, T1) |
| EGM result reviews of the fold (G1) and P1d-a (G2) | DONE (round 1) | 100 | tickets/G1-result-review-1.md, G2-result-review-1.md | 1 | fold: 2 Blockers, 8 Majors; P1d-a: 7 Majors; records tickets/G1-result-review-1.md, G2-result-review-1.md; fix rounds running |
| EGM result review round 2 of the gate | DONE (round 2) | 100 | tickets/F-result-review-2.md | 1 | NOT CLEAN: 1 Blocker + 10 Majors; fix agent running |
| Gate fix round for review round 2 | DONE (built) | 100 | evidence/F-G0-1.md | 1 | committed c9478a9; EGM round 3 review running |
| EGM plan review of ticket G4 (P1c) | DONE (round 1) | 100 | tickets/G4-review-1.md | 1 | NOT READY: 6 distinct Blockers, 12 Majors; ticket v2 being drafted on opus |
| Fold false-hit and cost measurement | RUNNING | 2 | evidence/G1-false-hits-and-cost.md | 1 | evidence runner, no code |
| SECURITY and README wording final | v2 reviewed (round 2): NOT CLEAN; v3 (last round) on opus next | 85 | SECURITY-README-final.md | 1 | tickets/SEC-wording-review-2.md |
| Pick of the integration onto cloud/core-c | DONE | 100 | evidence/PICK-int-onto-core-c.md | 1 | merged d95a727; verified in the worktree |
| Glued-rest gap of IPv4, phone, IBAN, UUID, host name (from the integration probe) | READY (needs a ticket + plan review) | 0 | evidence/INT-g2-g3.md | 0 | ORDER 016c item 15 asked for a look at the other kinds: listed, not fixed |
| ORDER 020 (lead review round 3): MJ-A, MJ-D, minors | DONE (built); fresh review running | 90 | tickets/F-result-review-2.md, evidence/F-G0-1.md | 1 | MJ-A fixed; MJ-D wording done; late-value cap + budget done; empty map accepted and marked (contested); duplicate TEXTNORM_PINNED_PYTHON with G7 round 2 |
| ORDER 020 MJ-B: redactor fixed-point loop with cap + RedactionError (G7 fix round 2) | RUNNING | 5 | none | 0 | builder on the merged tree |
| ORDER 020 MJ-C, m-4, mutants pickup: test files | DONE | 100 | evidence/TW-order020.md | 1 | committed; the mutants pickup test FAILS today on purpose until the gate fix agent re-syncs its mutants (told) |
| ORDER 020 m-3: duplicate TEXTNORM_PINNED_PYTHON in defaults.py | RUNNING (with MJ-B) | 0 | none | 0 | one-line change |
| Ticket G4 v2 (opus draft) then plan review round 2 | RUNNING | 10 | tickets/G4-P1c-redactor-gaps-v2.md | 1 | drafter on opus |
| EGM result review round 3 of the gate | DONE (reviews in) | 100 | tickets/F-result-review-3.md | 1 | design 0B/4M/5N, codebase 0B/5M/7N; round 4 fix running |

## RESTARTS
| time UTC | what | what was running | restarted | still missing |
|---|---|---|---|---|
| 2026-11-20T06:38:11Z | container restart: BOOT_ID 70253298 -> 1e29cf8a | see AGENTS | not yet | to be checked by the session |

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
| (new) g7D EGM RESULT review of the G7 redactor change at 4864984 (egm: | EGM RESULT review of the G7 redactor change at 4864984 (egm:egm-design): can the | earlier-model usage limit (HTTP 429), resets Nov 24 03:00 UTC | restart on Sonnet/Haiku under way |  |
| (new) g7C EGM RESULT review of the G7 change and its tests (egm:egm-co | EGM RESULT review of the G7 change and its tests (egm:egm-codebase-details): eve | earlier-model usage limit (HTTP 429), resets Nov 24 03:00 UTC | restart on Sonnet/Haiku under way |  |
| ae03e30a lead review round 2 of the gate (ORDER 015): enforce_map mad | lead review round 2 of the gate (ORDER 015): enforce_map made idempotent (identi | earlier-model usage limit (HTTP 429), resets Nov 24 03:00 UTC | restart on Sonnet/Haiku under way |  |
| a4bfb7dd reworks tests/test_grants_negative_roles.py so it is correct | reworks tests/test_grants_negative_roles.py so it is correct on main AND on core | earlier-model usage limit (HTTP 429), resets Nov 24 03:00 UTC | restart on Sonnet/Haiku under way |  |
| ad457b53 integration: cherry-picks P1d-a (5 commits) and the P2d-1 po | integration: cherry-picks P1d-a (5 commits) and the P2d-1 port (6 commits) onto  | earlier-model usage limit (HTTP 429), resets Nov 24 03:00 UTC | restart on Sonnet/Haiku under way |  |
| (new) r-g7D | restart: EGM RESULT review of the G7 redactor change (egm:egm-design) | container restart 06:37 UTC | to be restarted on sonnet after the EGM proof |  |
| (new) r-g7C | restart: EGM RESULT review of the G7 change and tests (egm:egm-codebas | container restart 06:37 UTC | to be restarted on sonnet after the EGM proof |  |
| (new) r-gate | restart: gate round 2 findings + ORDER 017 (mapping required with NO_M | container restart 06:37 UTC | to be restarted on sonnet after the EGM proof |  |
| (new) r-int | restart: integration of P1d-a + P2d-1 port + G7 in /tmp/core-c-int, th | container restart 06:37 UTC | to be restarted on sonnet after the EGM proof |  |
| (new) r-grants | restart: grants negative tests reworked for core-b step B map, local P | container restart 06:37 UTC | to be restarted on sonnet after the EGM proof |  |
| (new) g7D | EGM RESULT review of the G7 redactor change at 4864984 (egm:egm-design | container restart 06:37 UTC | to be restarted on sonnet after the EGM proof |  |
| (new) g7C | EGM RESULT review of the G7 change and its tests (egm:egm-codebase-det | container restart 06:37 UTC | to be restarted on sonnet after the EGM proof |  |

## LEAD ACTIONS NEEDED
Producers registry red (F-R3-C) CLOSED by one small commit in guard/producers.py (core-b file; a revert is one commit; DECISIONS 07:40). Wording v2 review round 2 done, v3 (last round) running on opus. Integration merged d95a727. G7 round 2 (capped loop) and gate round 2 fixes running. P1c plan v2 drafting on opus.
