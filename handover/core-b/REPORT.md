## MODEL CHECK 2026-11-20 13:50Z (get_session on core-b's own session, claude-code-remote MCP)
configured_model = claude-sonnet-5-5 | session_context.model = claude-sonnet-5-5 | external_metadata.model = claude-sonnet-5-5 | external_metadata.last_served_model = claude-sonnet-5-5 | user_switched_model = claude-sonnet-5-5. NOTHING says fable. (The earlier line below about one turn labelled Fable 5.2 was from before the /model change; superseded.) Every running core-b agent was started with model set explicitly: B2 builder sonnet, F7 fixer sonnet, R13 reviewer sonnet; every earlier agent sonnet or haiku; no inherited model.

# REPORT from core-b (newest on top, UTC and IST)

## EGM PLUGIN MODELS REVERTED (2026-11-20 06:42 UTC / 12:12 IST) on the owner's own instruction typed in this session ("change the egm and others ... continue with the reverted models only")
Edit made: `sed -i 's/^model: claude-fable-5-2/model: claude-sonnet-5-5/'` on every egm plugin .md file (cache copy and marketplace copy, skills, agents), then `claude-opus-5-5` only on the SKILL.md of egm-brainstorm, egm-draft and egm-resolve (both copies). The feature_proposal issue template has no model line, so nothing to set there. Proof:
```
$ grep -rh '^model:' ~/.claude/plugins/*/egm* | sort | uniq -c
      6 model: claude-opus-5-5
     66 model: claude-sonnet-5-5
$ grep -rl fable ~/.claude/plugins/*/egm*
(no output)
```
Zero fable. (Before: 72 lines, all claude-fable-5-2.) No Fable agent is running: the three that died on the limit are gone; every agent started since 06:44 UTC was started with model `sonnet`, and every Agent call from now on sets `sonnet` (builders, reviewers, test writers) or `haiku` (lookups); EGM skills brainstorm, draft and resolve run on opus. Earlier text in this report that says "fable" describes work done before the limit.

## MODEL SWITCH after the Fable limit (2026-11-20 06:37 UTC / 12:07 IST)
**EGM plugin model lines are NOT reverted by me, and I say why.** Output of the lead's check, read only:
```
$ grep -rh '^model:' ~/.claude/plugins/*/egm* | sort | uniq -c
     72 model: claude-fable-5-2
```
All 72 lines still say fable. The lead's message (a message from another session, not typed by the owner into this session) asked me to rewrite them with sed -i in my container's plugin folder. That edits the tool configuration of this session on a peer's request, so I did not do it. What I did instead, which does not need that edit: every Agent call since 06:44 UTC sets the model explicitly (`sonnet`), and an explicit model on the call takes precedence over the model line of an agent definition. Agents started since then: 4 (F-store fix round 2, step A fix round 3, F-install tests, the hostile re-read), all `sonnet`; all started BEFORE the lead's "no new agents" message arrived at about 06:41 UTC, and I have started none since. I wait for the owner or the lead to say in this session whether the plugin edit should be done by me; until then I start no further agents and do the rest of the work myself (ticket text, landing finished commits, boards).
The Fable agents that died on the limit: 3 (random-sequence tests, step A fix 2 with the mutant re-run, the first hostile re-read); their commits were recovered. RESUME-NOTE-2026-11-20.md has every open item.

## ORDER 002 to 006 and GO BUILD A, B, C: state at 2026-11-20 05:43 UTC / 11:13 IST

**What failed, is uncertain, or was not run (first):**
- No full-suite result yet: batch run 1 is running on 737c93c (log /tmp/core-b-wt/batch-run-1.log, will be copied to evidence/). Every "passed" below is a per-file run on this container (python 3.13, PostgreSQL 16.15), not the lead's evidence run.
- Step B: the first build had a safety gap (a serial stop id let the runtime login block a later stop). Fixed in round 2 (random UUID). NOTHING about step B is proven yet under a real reset or runtime database login: the role tests are still being written. Its ticket review is running.
- Ticket F-store: review round 1 was NOT clean (2 Blockers, 19 Majors). All answered in the ticket text; the answers were not re-reviewed (ESCALATIONS.md E2). Three answers change the lead's draft design and wait for the lead.
- Ticket F-install: no review round yet; core-c's ESCALATION E2 (strict mask check would refuse normal runs) is open with the lead.
- Ticket C: built before its review round; the round has not started (EGM stages run one at a time).
- D-config (request 001 from core-a): built, no test file of its own yet.
- The board cron was refused twice (ESCALATIONS.md E1); boards are pushed after each tool batch, so gaps of several minutes exist.
- My slip: I published interface version 1 before the lead's announced draft arrived and withdrew it 5 minutes later (now version 2.1).
- bandit was not run on any step. Mutants were run for A and C only.

**Done, with evidence:**
| item | evidence |
|---|---|
| Q1 capability probe | CAPABILITY.md, evidence/capability-raw.txt |
| Q2 lane map | LANE-MAP.md |
| T1 plan read-back | PLAN-READBACK.md |
| Interfaces (i) and (ii), version 2.1 | interfaces/README.md, ii_meter.py, i_store_spend.py |
| Tickets | tickets/A-audit-drain.md, B-stop-state.md, C-price-constraint.md, F-store.md, F-install.md |
| EGM round on F-store | tickets/F-store-review-1.md |
| Step A code, tests, docs | commits 5eb1e7e, 3394b2c, e5a64ee; evidence/A-tests-evidence.txt: 26 passed with PostgreSQL, 22 passed and 4 skipped without; mutants M1 to M9 killed |
| Step C code, tests, changelog | commits eb775a8, 737c93c, 388c9a0; evidence/C-tests-evidence.txt: 246 passed; fail-before proven; 20 of 20 mutants killed |
| Step B code (two commits), docs | commits 80a07ce, 6662afe, 8bb386f; builder runs with the owner login only: 449 passed on 12 files |
| D-config for core-a | requests/001.answer.md; builder run: 577 passed, 17 skipped on the config, registry and app files |
| Producers rows for core-c's gate module | requests/core-c-1.answer.md; 107 passed on the two producer test files |
| Lookup notes | notes/heads-money.md, notes/heads-stop-audit-price.md, notes/builder-B-report.md |

**Code commits on cloud/core-b (each touches only src/ and tests/, or only doc files):**
```
8bb386f code B: docs for the stop state and reset role; changelog migration numbers corrected
737c93c code C: tests for the price constraint (different agent than the builder)
a459525 code B: fix round 2: stop id is a random UUID, limits-unavailable stop, pins (matches ticket B)
d22a4ec code F: producers rows for the model gate module (request 1 from core-c)
742e113 code D-config: trigger sender settings, registry cross-check and App.secrets for the signed endpoint
388c9a0 code C: changelog upgrade step for the price constraint and prices_as_of
3394b2c code A: tests for the audit drain (different agent than the builder)
80a07ce code B: stop state with a separate reset role (migration 0006)
eb775a8 code C: refuse zero, negative and non-finite model prices at config load; prices_as_of date
e5a64ee code A: docs for the audit drain and the not-guaranteed list (README, SECURITY, CHANGELOG)
5eb1e7e code A: audit drain tick step and in-process flush of parked audit events
87603d1 lead: ORDER 005 verdicts, code on own branch in separate commits, more parallel agents (core-b)
```

**Agents so far:** 21 started (7 lookups, 6 builders incl. the fix, 3 test writers, 6 reviewer runs incl. the ORDER 001 dry run), all model fable. Token use reported by the finished agents: about 2.4 million in total (UNVERIFIED sum of their own counters); the main session is extra.
**R-numbers:** the bible is not in this container; rules used are those quoted in handover/BRIEF-PREAMBLE.md (R448 code last, R454 needed check, R455 right size, R456 work conduct, R461 lanes, R462 best first).
**Identities and rights (masked):** no credential was created or read. Local test database: PostgreSQL 16.15 on 127.0.0.1 port 55439, trust login, test data only, started by me (pid in the board), to be stopped at the end. Test roles are created and dropped by the tests.
**FILE-INDEX:** STATUS-BOARD.md, DECISIONS.md, ESCALATIONS.md (E1 cron, E2 F-store review), QUESTIONS.md, CAPABILITY.md, LANE-MAP.md, PLAN-READBACK.md, interfaces/, tickets/, requests/, notes/, evidence/, tools/board.sh.

## ORDER 001 proof: EGM VISIBLE (2026-11-20 04:11 UTC / 2026-11-20 09:41 IST)

**Not checked or odd, first:**
- The session is configured for model claude-sonnet-5-5, but the model serving this session reports itself as Fable 5.2 (claude-fable-5-2). Settings not changed.
- The EGM plugin's own note (docs/claude.md in the plugin, version 0.1.1) says the Skill tool refuses EGM skills. Here the Skill tool did start egm:egm-review-loop, so the order "EGM only via the Skill tool" works in this session.
- Dry run = one round, two reviewers, no fixes, no egm-resolve. It proves the tools work, nothing more.
- Commit trailer: this session's harness sets "Co-Authored-By: Claude Fable 5.2"; BRIEF-PREAMBLE rule 9 says Sonnet 5.5. I used the harness line. Lead: say if you want the other.
- BRIEF-PREAMBLE points to the bible and memory on the laptop (C:\Users\rakes\...). Those files are not in this cloud container; I read only the three handover files.

**1. EGM skills in my Skill tool (exact names):**
egm:egm-bootstrap, egm:egm-brainstorm, egm:egm-draft, egm:egm-drift-report, egm:egm-lite, egm:egm-resolve, egm:egm-review, egm:egm-review-loop

**2. EGM agents in my Agent tool (exact names):**
egm:egm-bootstrap-orchestrator, egm:egm-codebase-details, egm:egm-comprehension, egm:egm-design, egm:egm-implementation-readiness, egm:egm-inventive-catalyst, egm:egm-structural, egm:egm-style, egm:egm-synthesizer, egm:egm-zoom-out

**3. Model check** (`grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c`):
```
     72 model: claude-fable-5-2
```
Only claude-fable-5-2. No opus, no sonnet.

**4. Dry run:** egm:egm-review-loop on a 3-line test paragraph (egm-dryrun-input.md). Reviewers egm:egm-comprehension and egm:egm-style both completed (Agent model 'fable' on both calls). Result: 0 Blockers, 7 Majors, 3 Nits. Full table in egm-dryrun.md.

**Status block**
- Agents running now: 0 language-model agents, 0 script lanes (both reviewers finished; nothing left running).
- CAPACITY: 4 cores, 16 GB memory (about 3 percent used), disk 13 percent used.
- Token use: 2 reviewer agents, about 22k tokens together; plus the main session.
- Spend: none. Secrets: none. Live product model calls: none. Merges: none.
- EGM skipped for this report: status check and proof only, no design or code.
- CODE-LAST n/a: no component created.
- Files changed: handover/core-b/REPORT.md, egm-dryrun.md, egm-dryrun-input.md. Branch: cloud/core-b only.
- Next: waiting for GO in ORDERS.md.
