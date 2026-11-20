> **MODEL CHECK 13:46:55Z 2026-11-20 (get_session on session_014pRo39MRxnYCnugNxyoaw6, lead order 13:50):** configured_model = claude-fable-5-2 (the value stored when the session was created; it cannot be changed from inside the session); session_context.model = claude-sonnet-5-5; external_metadata.model = claude-sonnet-5-5; external_metadata.last_served_model = claude-sonnet-5-5; user_switched_model = claude-sonnet-5-5 (the owner's /model). So the model that SERVED the latest turn is sonnet, not fable. Session cost counter (cumulative since 04:09): 345.95 USD, which includes the early hours before the switch. Running agents (every Agent call sets model explicitly): wipci-fix2 sonnet, c-e14nits sonnet, c-e19 sonnet, grant-tests sonnet, max-running sonnet. No fable agent is running. Not provable from here: what the earlier (pre-switch) hours were billed as; ask the owner to check the usage page for the session id.

# REPORT from core-a (newest on top, UTC and IST)

## UPDATE 11:31 UTC (head 98e0fd3a5): pg-kill defect closed; final independent batch BATCH10
- The empty-body 2xx of BATCH9 (test_pg_kill_at_point[read31-audit.write_outcome-4-after]): CAUSE (found by reading the stdlib and our server; NOT reproduced in 60 serial runs): wsgiref sent each answer as 4 separate writes (wbufsize 0); a worker killed between two of them left the client a bare status line (http.client then reports 2xx with an empty body, no exception). The guarantee 'a complete 2xx implies the run row exists' was never broken (row before answer). FIX: d-fix13 one write per answer (49 tests: exactly one write for 16 answer types, golden bytes equal to the old server, 29 of 49 fail on the old code) + d-fix14 (the send-failure path, 8 more cases) + the test client treats a truncated 2xx as no complete ack (final-fix). After the fix the pg-kill id: 20 of 20 PASS. FINDINGS-flake-pg-kill.md (written 11:19: an earlier agent reported writing it but had not; my ticket cited a missing file for 3 minutes).
- BATCH10 (independent, after the fix, head 6e61005db): lint clean (458 files), bandit 0 medium/high; whole suite REQUIRE_PG=1 -n 3: 12 failed / 12366 passed / 458 skipped / 75 xfailed; the 12 = 10 strict-mode by design + dblink (needs PostgreSQL on the default socket) + the brand-string rule test (the lead's handover/BRIEF-PREAMBLE.md); combined tree core-b 1e5791345 + my files + n8n/: 1437 passed, 4 skipped, 0 failed. The pg-kill test passed in the suite.
- STILL OPEN: (1) the mutant script: BLOCKED (the G33d anchor line 1251 `now - last_warned` -> `at - last_warned` and a re-run: denied by the permission classifier for my builder; I do not route around it: owner's go-ahead). G34 (one write) and the d-fix14 mutant are NOT in a full run. Last complete run 18: 109 of 109 before the rename and before G34. (2) Windows and the n8n cases not yet run (see below). (3) PostgreSQL 16 on 55433 still running on this box.

## FINAL STATE of core-a, 11:05 UTC (head f18af73cb); honest list, nothing hidden
**Done and tested (my own runs and independent evidence runners):**
- Step D (signed trigger endpoint + worker + E1: trigger.conflict audit event with per-sender cap, GET /health 503 + counter, in-process recovery when the store is down, no exit code 4): tested commits 70feef2c5 (09:08), 48dc30064 (09:24), 3b39df08f (09:50); later code only by builders (fix commits are the board's 'code D+E: WIP snapshot' commits: the tree at head is the tested one: tests/triggers + crash + k5 = 1399 passed, 5 skipped, raw/D-fix12-tests.log). 4 fresh code review rounds + 4 E1 rounds + 3 test/mutant reviews; E7 decided by the lead (keep the stdlib server).
- Step E (testing/crash.py): 7 fresh review rounds, round 7 found no Blocker/Major (lead ruling: no cap for shipped helper code).
- n8n template: three review rounds + 2 on new evidence; run in real n8n 2.47.7 by the lead (evidence-n8n-4.md): works; README marks SEEN only where evidence shows; 92 tests.
- T4 contract tests for core-b/core-c (tests/contracts/*): green on their newest heads at my last run.
- Drift report (DRIFT-REPORT.md): 26 drifts, fixed in the documents.
**Independent evidence (BATCH9, head 32eae7c17, before the last cosmetic edits):** whole suite REQUIRE_PG=1 -n 3: 13 failed / 12305 passed / 458 skipped / 75 xfailed; 10 failures are strict-mode by design (tree lacks core-b's trigger config; they pass on the combined tree core-b d2920f552 + my files: 1377 passed, 0 failed); the other 3: dblink test (needs PostgreSQL on the default socket), the vendor-brand rule test (the lead's handover/BRIEF-PREAMBLE.md contains the string), and ONE crash-matrix test that is a TEST RACE (truncated answer of a killed worker): fixed in the test client afterwards (signed_post), not re-run in a whole-suite batch.
**NOT done / open (exact):**
1. BLOCKED: complete mutant run 19: needs tests/endpoint_mutants.py line 1251 `now - last_warned` -> `at - last_warned` (a cosmetic rename of mine moved the G33d anchor) and `uv run python tests/endpoint_mutants.py`: my builder's attempt was denied by the permission classifier; not worked around; waits for the owner. Evidence on the previous code: run 18 = 109 of 109 as expected (raw/endpoint-mutants-run-18.log).
2. No independent whole-suite run after the last edits (signed_post fix, 3 nits, n8n pins): builder runs only (tests 1399 passed).
3. Nothing was run on Windows (WINDOWS-NOTES.md has 16 rows to run on the laptop). The 45 s timeout, 3xx, 502/503/504 with body, 520-524, Retry-After, 45 rounds exhausted, states other than NO_ACTION, lone surrogate, null values, an execution lost in a restart: UNVERIFIED in n8n.
4. worker.main cannot start on THIS branch (core-b's Config.triggers is not merged here): expected; it starts on core-b's head + my files (tests pass there).
5. Optional deletions the last E1 reviewer listed (not needed for the lead's verdict): _ack_wait_of 18 lines, _warn_no_audit 11, the 5-minute warning limit 10, drop-warning throttle 8, parameter validation 7.
6. Left on this box: PostgreSQL 16 on port 55433 (mine; stop when the owner says the mutant run is not needed), scratch folders under the scratchpad.

## OWN SESSION MODEL: NOT FABLE, proof 07:22 UTC / 12:52 IST
Output of get_session for this session (own id), after the owner's /model claude-sonnet-5-5 typed in this session: session_context.model = claude-sonnet-5-5; external_metadata.model = claude-sonnet-5-5; external_metadata.last_served_model = claude-sonnet-5-5; user_switched_model = claude-sonnet-5-5. configured_model = claude-fable-5-2 is only the value stored at creation and cannot be edited by me. The owner's switch was done before this lead message; no action by me was needed. Agents started since: sonnet (haiku for lookups; opus only inside brainstorm/draft/resolve skill files).

## EGM MODEL LINES REVERTED, 06:41 UTC / 12:11 IST. Done on the owner's own instruction typed in THIS session ("change the egm and others and continue with the reverted models only"). Supersedes the "NOT done" block below.

Command output, run in my container after the edit:
```
$ grep -rh '^model:' ~/.claude/plugins/*/egm* | sort | uniq -c
      6 model: claude-opus-5-5
     66 model: claude-sonnet-5-5
```
Zero fable lines. What was changed: 72 lines in 72 files, every copy (marketplace copy, cache copy, skills, agents, .claude-plugin/agents, .cursor-plugin/agents): all set to claude-sonnet-5-5, then claude-opus-5-5 on egm-brainstorm, egm-draft and egm-resolve (SKILL.md, both copies = 6 files). The feature_proposal issue template (both copies) has NO model line, so there was nothing to change in it. The files were changed with sed only; no fable patch tool was used.
Not proven: that a newly started egm:* agent really runs on sonnet (I have not started one since the edit; the next one will be checked through the harness's served-model field). The EGM skills run inside my own session, which the owner set to claude-sonnet-5-5.
**No fable agent is running:** all agents of this session since the limit were started with model 'sonnet' set explicitly; the older fable agents all ended (4 by the usage limit, 5 on my stop order). The Sonnet restart is running; its brief is RESUME-NOTE-2026-11-20.md.

## MODEL SWITCH after the Fable limit, status at 06:38 UTC / 12:08 IST (ORDER 018 and the lead's later message)

**What I did NOT do, and why (first):** I did NOT edit the egm plugin files in my container (the sed on the 'model:' lines). The instruction came only in a session message from the lead; ORDER 018 in ORDERS.md (the file I was told to follow) asks for the restart on normal models and says nothing about editing plugin files. Changing what my own plugin definitions run on is a change to my own configuration, so I do not do it on a peer's message alone: the owner can say yes here, or run the sed himself. The plugin files therefore STILL say fable:
```
$ grep -rh '^model:' ~/.claude/plugins/*/egm* | sort | uniq -c
     72 model: claude-fable-5-2
```
**Update (a second relay quoted the owner's own words):** unchanged. The relay still arrives as a session message that I cannot tell from anyone else's, and the edit changes my own plugin configuration: the owner says it in this session or runs it himself. The ready command is on the board under LEAD ACTIONS.
**What protects against fable instead:** every Agent call I make sets the model explicitly (the tool documents that this wins over the agent definition's own model line): builders and EGM reviewers 'sonnet', lookups 'haiku', brainstorm/draft/resolve work 'opus'. Not proven by me: that an egm:* agent type really obeys the explicit model on this harness (I have not started one since the switch). The EGM skills run inside my own session, which is now claude-sonnet-5-5; I cannot move my session to opus.
**Timing, said plainly:** at 06:38 UTC, before the lead's message 'no new agents until the setup is reverted and proven' reached me, I had already started 6 agents, all general-purpose with model 'sonnet' (finish server fixes, finish worker fixes, n8n test fixes, crash matrix part 2, concurrent fuzz, findings for the meter and redaction tests). None is an EGM agent. I started nothing after that message. If the owner wants them stopped, say so.
**State of the work:** RESUME-NOTE-2026-11-20.md has the stop point and next step per open item. The tree is half edited (section 0 of the note): the last tested state is about the 06:05 board commit.

## ORDER 013 report. 2026-11-20 06:09 UTC / 11:39 IST. Head at writing: 05b1b7a. STATE: WAITING-LEAD, 0 agents running

**What failed, what is weak, what was not run (first):**
1. The whole suite was NOT run again after ORDER 013 (owner rule: batches only). Batch 3 ran my own files and 6 rule files on PostgreSQL 16.15: 899 passed, 105 skipped, 0 failed (raw/BATCH3-own-files-pg16.log, test ids). The last whole-suite run is batch 2 (1 inherited failure from handover/BRIEF-PREAMBLE.md).
2. Three of my new test files only SKIP on my branch, because the code they test lives on other branches: tests/test_trigger_config.py (core-b), tests/contracts/test_model_gate_contract.py (core-c), the two spend contract files (core-b, no code yet). The first two were run against scratch copies of those branches by the agents that wrote them; I did not re-run them.
3. ORDER 013 item 3 (switch the worker to core-b's final names) is NOT done: against core-b's code as it is (commit 2b086c2) my worker refuses to start, because core-b hands out the whole secret store and no reader limited to the sender names. I did not build on that (finding F3). Waiting for core-b's answer.
4. One agent repeated its test file 5 times against the no-loop rule. No harm; said here.
5. Still not run anywhere here: PostgreSQL 17, python 3.12, a real n8n, real model clients.
6. The gate contract test landed after batch 3, so it is not in that batch; in my checkout it skips.

**Done (evidence under handover/core-a/):**
| item | result | evidence |
|---|---|---|
| 1 mutant script extended | 30 of 30 good; 13 new mutants for the quiet server, secret count and whitespace, clock boundary, back-off and slot take-over, bind check, 409 log line, SIGTERM | tests/endpoint_mutants.py, raw/endpoint-mutants-run-3.log |
| 2 tests for core-b's trigger config | 93 passed, 16 strict expected-failures (7 findings), 20 skipped on core-b's code | tests/test_trigger_config.py, raw/trigger-config-tests-on-core-b.log, FINDINGS-core-b-trigger-config.md |
| NUL character in a document | pinned: accepted and safe today (the redactor removes it; no document text is stored); U+0001 and U+001F are not removed | tests/triggers/test_t5_nul_document.py (29), raw/D-nul-document-pg16.log, ticket D lines 241 and 293 |
| Ticket D line on kill tests | added (why the store is wrapped, what a hook would add) | tickets/D-signed-endpoint.md line 241 |
| Batch of my own files | 899 passed, 105 skipped, lint and format clean (342 files) | raw/BATCH3-own-files-pg16.log |
| Contract test for core-c's gate | 201 passed, 0 findings, 1 skipped on core-c's code (619a3e5); 7 planted mutants caught | tests/contracts/test_model_gate_contract.py, raw/gate-contract-tests-on-core-c.log |

**Findings on other sessions' code (expected-failures listed, as ORDER 013 asks):** tests/test_trigger_config.py marks 16 cases in 7 findings: F2 shared platform secret name not refused (1); F3 no name-limited secrets reader (1); F4a a value typed as a secret name is echoed at start (1); F4b unclear refusal for a clash with an action secret (1); F5 blank or whitespace names and ids load (8); F8 booleans load as numbers (3); F7 body cap equals the document cap (1). Details and the 6 differences from request 001: FINDINGS-core-b-trigger-config.md. core-c's gate: none; two notes (no shipped worst-case formula for tools, documents and retries; stale ticket text on settle).

**Rules used:** preamble 4 (no live model call: fake clients only), 6, 7 (mutants for each new guard), 11 (finding F3 is a least-privilege finding), 13 (tests written by a different agent than the builder; no plan or design made in this order, so no new EGM round: "EGM skipped: test writing against existing tickets"), 19, R456, MODEL-ROUTING (model fable on every Agent call). CODE-LAST n/a: tests and one mutant script, no new component.
**Token use:** about 0.75 million agent tokens for this order (5 agent runs); about 4.7 million over 27 agent runs in total. **Clock:** ORDER 013 at 05:58 UTC, done 06:09 UTC.
**Files changed:** tests/endpoint_mutants.py, tests/test_trigger_config.py, tests/triggers/test_t5_nul_document.py, tests/contracts/test_model_gate_contract.py, tickets/D-signed-endpoint.md (2 lines), FINDINGS-core-b-trigger-config.md, raw/ logs, DECISIONS.md, STATUS-BOARD.md.

## ORDERS 002 to 012, END OF ROUND report. 2026-11-20 05:57 UTC / 11:27 IST. Head at writing: a7c3063

This block REPLACES points 1, 2, 3 and 8 of the interim block below; the rest of that block still holds. STATE: WAITING-LEAD, 0 agents running.

**What failed, what is weak, what was not run (first):**
1. Whole suite, second and last run for this round (after the lead-review fixes): **1 failed, 10865 passed, 640 skipped in 100 s** (raw/BATCH2-full-suite.log). The 1 failure is INHERITED from the handover folder: handover/BRIEF-PREAMBLE.md (lead's file) names vendor products and trips tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked. No NEW failure. The first run (before the review fixes) had one more, a timing race of mine, fixed in code.
2. That run had no database variable, so database tests are among the 640 skips (also the 102 contract tests waiting for core-b). My own files ran separately on **PostgreSQL 16.15 only**: 13 of 13 database and kill tests (raw/D-tests-pg16.log, with test ids), all of tests/triggers plus the step E file 578 passed, 4 skipped (raw/D-E-all-tests-pg16.log). PostgreSQL 17, python 3.12, Docker, a real n8n: NOT run here, they are the lead's evidence run.
3. One test agent could not start the database (the session scratch folder is not readable by the postgres user); it reported that and did not work around it. I started the server from the postgres user's own folder and ran the tests myself. The server is stopped.
4. ORDER 012, what is NOT done or done differently: no crash= hook points in the worker (kill tests wrap the store instead); a backed-off wait (10 store reads) instead of "503 at once"; minor 8 strict only for foreign errors; minor 6 (literal defaults) waits for core-b; minor 12 (NUL byte inside a document) not fixed. Each is on the board under LEAD ACTIONS.
5. The mutant script (17 of 17 on the final endpoint and worker code) does not yet cover server.py, the secret count and whitespace checks, the back-off and the SIGTERM drain: those have hand mutants only (raw/E2-mutants.log, raw/D-endpoint-mutants.log).
6. Contract tests for core-b's interface (i) are written but have never run against real code (none exists): 102 skipped. Against a throwaway fake outside the repo: 47 of 47, and 11 seeded bugs all caught. The interface has 3 contradictions and 10 gaps (requests/003).
7. Two database data folders are left on disk (the session's safety check refuses folder deletes): /tmp/claude-0/pgprobe1 and /var/lib/postgresql/core-a-test.

**Added since the interim block (evidence):**
| item | result | evidence |
|---|---|---|
| Lead review Major 1 | backed-off no-slot wait; a waiting request takes a freed slot; n8n loop for 503 with re-sign | raw/E2-tests.log, n8n/, tests/triggers/test_n8n_template.py |
| Lead review Major 2 | SIGTERM drains and exits 0 (child process test on worker.serve) | tests/triggers/test_t5_process.py |
| Lead review Major 3 | n8n guard node before hashing (outline, not run in n8n) | n8n/hadavin-trigger.json |
| Lead review Major 4 | database, kill, two-process, start-refusal, oversize, two-sender tests | tests/triggers/test_t5_postgres.py, test_t5_process.py, crash_launcher.py |
| ESCALATION E2 | the standard server leaked; fixed by src/hadavin_sdk/triggers/server.py | raw/E2-wsgiref-before.log, raw/E2-wsgiref-after.log |
| Queue item T4 | 2 contract test files, 102 tests, skip until step F | tests/contracts/test_store_spend_reservations.py, tests/contracts/test_t1_reserve_cap.py, raw/T4-contract-tests.log |
| Requests | 002 (README and SECURITY text), 003 (interface questions) | requests/ |

**Token use:** about 3.9 million agent tokens over 22 agent runs (harness figures); main session not metered here. **Clock:** GO about 05:17 UTC, this block 05:57 UTC.
**Files changed in this round:** see FILE-INDEX of the block below, plus src/hadavin_sdk/triggers/server.py, tests/triggers/test_t5_wsgiref.py, test_t5_postgres.py, test_t5_process.py, crash_launcher.py, test_n8n_template.py, tests/contracts/test_store_spend_reservations.py, tests/contracts/test_t1_reserve_cap.py, requests/002 and 003.

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
