# ARCHITECTURE AUDIT CHECKLIST (bible R460; owner HARD rule 2026-11-15; applies to EVERY project, demo, real build and existing/continuing project)
Terms (added 16 Nov 2026): the bible = the studio's rulebook of numbered rules (R-numbers); the rule that makes this checklist mandatory is R460. EGM = Elephant-Goldfish Model, the studio's review method: one author session plus fresh reviewer agents (`egm:*` types) that each read the page cold. Blocker = a finding that stops the work until fixed; Major = a finding to fix before delivery; Nit = a small wording or style point. Ledger = the blocker ledger file `egm/BLOCKER-LEDGER.md` in the studio's private notes (not in this repository), one row per Blocker or Major. Owner = the human who owns the studio. Round cap: Blockers in security, money or redaction paths are reviewed until a round finds none; every other path gets at most 2 review rounds.
Copy this file into `egm\<project>\architecture-audit\` and fill it. A project without a filled, reviewed audit is not ready for a demo, take, pilot or delivery.

## 0. When
At design; at every milestone; before demo/take/pilot/delivery; at the start of every new work phase on an existing project; the moment one inconsistency is noticed (then sweep its whole class).

## 1. Master map (ONE file, no part left out)
List: components and processes; EVERY store/database/file that holds state or logs (engine, path, schema, who writes, who reads, retention); every workflow with every node/step/stage; scripts; jobs, schedules and loops (interval, owner, what stops them); agents and sessions; credentials and identities (name only, never values); ports and hosts; external systems; docs and specs; tests; repos and branches; folders. For each: purpose in one line, owner of the job, inputs, outputs, failure path, retry, timeout, idempotency, where it logs, identity it runs as, where it is tested, who uses it.

## 2. Hunt (each hit needs evidence: file:line, raw output, dated source)
- DUPLICATES: two places for one job (stores, counters, filters, search, retry/recovery engines, pages, scripts, specs, flow/model/schema versions, docs). One place per job (NEEDED-CHECK R454).
- DEAD / IDLE: unused flows and old versions, scripts no one calls, tests for removed code, idle processes, loops, crons, agents, stale docs, unused config, unused dependencies.
- INCONSISTENT: names, numbers, ports, versions, counts and claims that differ between code, docs, evidence and video script.
- UNVERIFIED / NEVER RUN END TO END: every claim and every step that no raw evidence supports.
- STORE RULE: one store, one log place, one source of truth per job; any exception is written with reason, owner and removal trigger.
- WORKFLOW WALK (node by node, stage by stage): trigger, every branch, every error path, every retry and timeout, what happens on kill/restart/duplicate/out-of-order/empty/huge input, what is written where, what a person sees, what is logged, which identity acts, least privilege, human approval points, loops and their stop conditions.
- SECURITY: secrets paths, scopes, egress (outbound calls), least privilege, redaction, retention, personal data.
- OPS: start, stop, restart, kill, clean-up, resource limits, what stays running, what a new person must know.

## 3. Method
EGM in order: plan, plan review, read-only inventory, at least TWO independent `egm:*` reviewers per area with different lenses (codebase-details, design, zoom-out for duplicates and dead things, comprehension), resolve, fix, evidence run, re-review until a fresh pass finds no Blocker or Major (security, money, mail, redaction: no round cap). Reviewers get files and evidence, never the author's verdict. Raw outputs saved. Findings into `egm\BLOCKER-LEDGER.md` (9 columns). Several independent checks, not one.

## 4. Output
(a) master map; (b) findings table with severity; (c) fix plan in order; (d) CUT LIST (what to remove, merge or archive; owner yes before any removal, move to `archive\`, never delete); (e) list of exceptions with reason and trigger; (f) claims check; (g) lessons added to checklist, memory, brain, brief preamble.

## 5. Exit
No open Blocker or Major; every exception written; cut list decided by the owner; master map committed; handoff updated.
