# REPORT from core-a (newest on top, UTC and IST)

## ORDERS 002 to 012, INTERIM report. 2026-11-20 05:52 UTC / 11:22 IST. Head at writing: 6aa8cce (the board carries the newest head)

Not final: 2 agents still run (database and kill tests; contract tests for core-b's interface). This block is rewritten when they land.

**What failed, what is weak, what was not run (first):**
1. Whole-suite run (once, python 3.13, no database variable): 2 failed, 10723 passed, 527 skipped. Failure 1 is NOT from my code: tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked fails on handover/BRIEF-PREAMBLE.md (the lead's file names vendor products). Failure 2 was NEW and mine: a T5 test got 503 on a retry right after the pool freed (a real race, slot freed a moment after the run's final state). Fixed in code; passed in the 2 runs since; not proven gone.
2. The whole suite has NOT been re-run after the lead-review fixes (owner rule: one batch). Since then only my own files ran.
3. Database: only PostgreSQL 16.15 exists here. Step E's file passed on it (73 of 73). The step D database and kill tests are being written and run now; no log yet. PostgreSQL 17 and Docker: NOT possible here.
4. `python -m hadavin_sdk.triggers.worker` cannot start today: it needs `Config.triggers` and `App.trigger_resolve` from core-b (requests/001, DRAFT 3). It exits with code 2 and a clear message (tested). Everything past that check in main is tested through its parts, not through main.
5. n8n files are an OUTLINE, not run in n8n. 19 node parameters are guesses marked UNVERIFIED.
6. Ticket D's review found 3 Blockers and 20 Majors in the ticket TEXT; all 33 accepted fixes are in the text, 4 went to ESCALATIONS (now decided by ORDER 009). The review report holds my condensed copy of the findings, not the reviewers' full texts.
7. The step D code was built BEFORE the ticket was checked and reviewed, on the lead's order (code first). 'GO BUILD D' is not written in ORDERS.md.
8. Mutant script: 17 of 17 on the final code, but 6 mutants rest on bare asserts, and the newer code (server.py, secret count and whitespace checks, back-off, SIGTERM) has hand mutants only.
9. Two points of ORDER 012 I did differently and logged for a verdict: no crash= hook parameter in the worker (kill tests wrap the store), and a backed-off wait instead of 503 at once when no slot is free.
10. Not checked at all: Python 3.12 runs, the wheel contents, Windows, a slow-drip client, a real second process against one database (being written), timing of the secret comparison.
11. Snapshot commits named "code D+E: WIP snapshot" hold files mid-edit (some hold a deliberately broken file from a mutant check). They exist because the session must push every change at once. The tested state is the working tree at the newest "board" commit, not any single snapshot.

**What was done, with evidence (all under handover/core-a/ unless a path says otherwise):**
| item | result | evidence |
|---|---|---|
| Q1 capability probe | done | CAPABILITY.md, raw/capability-raw*.txt, raw/pg16-start-probe.txt |
| Q2 lane map | done (tests column from a name search only) | LANE-MAP.md |
| Q3 to Q7 baselines | skipped on the lead's order | inputs/lead-baselines-SUMMARY.md (lead) |
| T1 plan read-back | done | PLAN-READBACK.md, QUESTIONS.md (10, answered by ORDER 006) |
| Ticket E | done, no review needed | tickets/E-test-helpers.md |
| Ticket D | done, reviewed once, text repaired | tickets/D-signed-endpoint.md, tickets/D-review-1.md, ESCALATIONS.md |
| Step H | CUT (no delta once the payload hash is in trigger_ref) | ticket D section 4 |
| Requests to core-b | 001 config and wiring (DRAFT 3), 002 README and SECURITY text | requests/ |
| Step E code | src/hadavin_sdk/testing/crash.py + tests/test_testing_crash.py: 73 passed incl. PostgreSQL 16; 4 mutants caught | raw/E-tests.log, raw/E-tests-pg16.log, raw/E-guards.log, raw/E-mutants.log |
| Step D endpoint | src/hadavin_sdk/triggers/endpoint.py: 265 passed, 2 skipped | raw/D-endpoint-tests-2.log, raw/D-endpoint-mutants.log |
| Step D worker and server | triggers/worker.py, triggers/server.py: all tests/triggers files 385 passed, 68 skipped (database cases) | raw/E2-triggers-all.log, raw/E2-wsgiref-before.log, raw/E2-wsgiref-after.log, raw/E2-mutants.log |
| T5 tests | tests/triggers/test_t5_cases.py, test_t5_wsgiref.py | same logs |
| n8n outline | n8n/ (3 files) + 24 checks that need no n8n | tests/triggers/test_n8n_template.py |
| Mutant script (ORDER 008) | tests/endpoint_mutants.py: 17 of 17 good | raw/endpoint-mutants-run-2.log |
| Batch | lint and format clean (331 files), bandit -ll no finding, whole suite once | raw/BATCH-*.log |
| Lead code review (ORDER 012) | Majors 1, 2, 3 fixed; Major 4 (missing tests) in work; minors 1, 3, 5, 7, 14 fixed, 8 partly, 6 and 12 not, rest written as stated limits | DECISIONS.md, board |

**Real findings worth the lead's eye:** (a) the standard web server leaked before the fix: HTML error bodies, the request line echoed, a 500 with text, tracebacks with the client address on stderr, a header with the Python version (raw/E2-wsgiref-before.log); (b) a run ended by the tick as NEEDS_PERSON "interrupted" gets no card to a person; (c) spend is charged after the model call, so parallel runs can overshoot a budget: max_running defaults to 1 until step F; (d) a NUL byte inside a document is accepted.

**Rules used:** preamble 2, 3, 4 (no spend, no live model call: none made), 5, 6, 7, 11 (the worker reads only the named sender secrets and run rows by id; no new role, table or grant), 13 (EGM: ticket D review-loop and resolve through the Skill tool; code review by the lead's reviewer), 19 (no loops; processes stopped: PostgreSQL is owned by one test agent until it ends), 20 to 23 (rung tables and needed-checks are in the two tickets), R456, MODEL-ROUTING (every Agent call set model fable). Bible R-numbers beyond those quoted in handover/ could not be looked up from the cloud.
**Token use (agents only, as reported by the harness):** about 2.9 million tokens over 17 agent runs so far; the main session is not metered here.
**Clock:** GO at about 05:17 UTC; this block at 05:52 UTC.

### FILE-INDEX
- Tickets: tickets/E-test-helpers.md, tickets/D-signed-endpoint.md, tickets/D-review-1.md
- Requests: requests/001-config-triggers.md, requests/002-readme-security-text.md
- Logs: DECISIONS.md, ESCALATIONS.md, QUESTIONS.md, STATUS-BOARD.md, raw/
- Code (commits starting "code"): src/hadavin_sdk/testing/crash.py; src/hadavin_sdk/triggers/__init__.py, endpoint.py, worker.py, server.py; tests/test_testing_crash.py; tests/endpoint_mutants.py; tests/triggers/; n8n/

## ORDER 001 proof: EGM IS VISIBLE. 2026-11-20 04:11 UTC / 09:41 IST

**What failed or is not proven (first):**
- The dry run is one round only and is not converged: 2 Major findings stay open on the throwaway paragraph. No resolve step, no fixes, no round 2.
- Only 2 of 10 EGM agents were actually started (style, comprehension). The other 8 are listed by the Agent tool but were not run.
- I chose the reviewer set myself; the skill wants a person to confirm it. Nobody was present.
- Commit trailer: this session's harness requires "Co-Authored-By: Claude Fable 5.2", not the "Claude Sonnet 5.5" line of preamble rule 9. I used the Fable line because Fable did the work. Lead: say if you want it otherwise.
- The session's configured push branch for this repo is claude/pensive-cannon-alwylt; the push to cloud/core-a was done on the order of the person who started the session. Result of the push is in the status block below.
- Studio files on the laptop (bible\RULES.md, memory index) cannot be read from the cloud, so no R-numbers were looked up beyond those quoted in handover/.

**1. EGM skills in the Skill tool (8):**
egm:egm-bootstrap, egm:egm-brainstorm, egm:egm-draft, egm:egm-drift-report, egm:egm-lite, egm:egm-resolve, egm:egm-review, egm:egm-review-loop

**2. EGM agents in the Agent tool (10, exact names):**
egm:egm-bootstrap-orchestrator, egm:egm-codebase-details, egm:egm-comprehension, egm:egm-design, egm:egm-implementation-readiness, egm:egm-inventive-catalyst, egm:egm-structural, egm:egm-style, egm:egm-synthesizer, egm:egm-zoom-out

**3. Model lines:**
```
$ grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c
     72 model: claude-fable-5-2
```
Only claude-fable-5-2. No opus, no sonnet, no haiku. Same result when the whole ~/.claude/plugins folder is searched without case.
Plugin: egm@egm 0.1.1, commit 70406c4d, installed 2026-11-20T04:09:10Z.

**4. Session model:** configured claude-fable-5-2, last served claude-fable-5-2 (from the session record).

**5. Dry run:** egm:egm-review-loop started through the Skill tool; 2 reviewers, both with Agent model 'fable', both completed. Round 1: 0 Blocker, 2 Major, 6 Nit. Full output: handover/core-a/egm-dryrun.md. Target: handover/core-a/egm-dryrun-target.md.

**Rules used:** MODEL-ROUTING (all Fable, model set on every Agent call), preamble 4 (no spend, no live product model call), 6 (honest report), 13 (EGM skipped for the order itself: status check), 19 (no loops, no background process left), 23 RIGHT-SIZE (this is a manual one-off step, about 3 minutes of clock), R456.
CODE-LAST n/a: proof step, no component created.
Token use: 2 reviewer agents, 20,311 tokens together; main session not metered here.
Files changed: handover/core-a/REPORT.md, egm-dryrun.md, egm-dryrun-target.md. Nothing outside handover/core-a/.

### Status block 04:11 UTC / 09:41 IST
Push: proof commit 484172c pushed to cloud/core-a at 04:11 UTC, accepted by GitHub (fd9d08d..484172c).
ORDER: 001. STATE: WAITING-LEAD (waiting for GO). Agents running: 0 language-model agents, 0 script lanes (2 started, 2 finished, none lost). Background processes: none. Next: nothing until ORDERS.md has a line starting with GO.
Note: a cloud session only acts when it receives a message, so the "status block every 10 minutes" rule cannot run while it waits; no timer was set (no unbounded loops, rule 19). Send GO as a message or as a new order plus a message.
