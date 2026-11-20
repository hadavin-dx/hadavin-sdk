# EGM LEDGER of core-c (owner order 12:15 IST: every item through EGM in sequence; list every item built without a step and run the missing step now). Updated 2026-11-20 ~06:50 UTC.
Sequence: brainstorm, draft, plan review, resolve, build, evidence runner, result review by a fresh reviewer, resolve + fix, repeat until a fresh pass finds none, drift report. Models: opus brainstorm/draft/resolve; sonnet the rest.
HONEST STATE: brainstorm and draft were NOT run through the egm skills for any ticket (I wrote tickets F, G, G4, G7 myself, as the lead's orders asked for tickets with a plan review round). egm-drift-report has been run for NOTHING. The evidence runner was in most cases the builder agent's own test run; the lead's batch run is the independent one. The Elephant's resolve step was done by me in prose, not through egm-resolve.
| item | plan review | build | evidence (who ran) | result review | drift report | missing step, started |
|---|---|---|---|---|---|---|
| F gate wrapper | ticket F-review-1.md (2 reviewers, sonnet/fable) | done | builder's own runs + tests/gate_mutants.py | round 1 on f16d48e: tickets/F-result-review-1.md (2 reviewers); round 2 of the lead's and the reviews' findings is being built | NOT RUN | result review round 2 after the build; drift report after round 2; independent evidence run = the lead's batch |
| G0 enforce_map / is_masked | ticket G reviewed (G-review-1.md) | done | builder | covered by the gate result review | NOT RUN | drift after the gate round 2 |
| G1 fold (P1a+P1b) | ticket G reviewed (readiness + code reviewers) | done | builder (939 + 8,616 tests) | NOT RUN | NOT RUN | result review: STARTED 06:50 (tickets/G1-result-review-1.md) |
| G2 P1d-a | ticket G reviewed | done on its branch | builder (7879 passed, mutants 48/51) | NOT RUN | NOT RUN | result review: STARTED 06:50 (tickets/G2-result-review-1.md) |
| G3 P2d-1 port | ticket G reviewed (cb-1-1 etc.) | done on its branch | builder (8237 passed) | NOT RUN | NOT RUN | after the integration (it changes the code again) |
| G7 redactor class fix | NONE: built from the lead's order (E3, E5, ORDER 013), ticket written after the build | done (4864984) | builder + property test (1,835 inputs) | round 1: design reviewer done (no Blocker, 6 Majors, 2 Nits: tickets/G7-result-review-1.md), code reviewer running | NOT RUN | plan review after the fact: run egm-review-loop on tickets/G7-context-after-sweep.md after the result review |
| G4 P1c gaps | ticket written; NOT reviewed | NOT BUILT | probe by an evidence-runner agent | - | - | plan review before any build |
| G6 wording | ticket text only | not built | - | - | - | after the lead's OK |
| step B grants tests (code B) | none (test file, written from the plan) | done | agent's own run, local PostgreSQL 16 | NOT RUN | NOT RUN | result review of the test files: queued |
| T1 + 0007 tests (code F) | none | done | agent's own run | NOT RUN | NOT RUN | result review of the test files: queued |
| EGM dry run (ORDER 001) | - | - | - | style + comprehension | - | done |
