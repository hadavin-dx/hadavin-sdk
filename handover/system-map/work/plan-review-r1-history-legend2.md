# PLAN-002 review round 1 (egm:egm-zoom-out and egm:egm-implementation-readiness, sonnet). Both completed.
## zoom-out: 0 Blocker, 3 Major, 4 Nit
Z-1 Major: "take repo not visible" row missing from MASTER-MAP and ONE-PLACE-TABLE (only a parenthesis under patches/).
Z-2 Major: DECISION-one-store not wired into lanes; add its store rows as seed list; flag "CONFLICT WITH DECISION" with decision lines.
Z-3 Major: five lanes too many, L5 overloaded; job-by-job grep (store, log, filter, counter, retry engine, notice) should be one cross-cutting pass over all folders; core hadavin_sdk is a different system: one row "core, out of take scope", not mapped module by module.
Z-4 Nit: citation checker: keep to ~30 lines, fix match rule (exact substring after whitespace trim). Z-5 Nit: full 8 fields only for workflows, stores, jobs, credentials; short row (name, purpose, evidence) for docs/tests/folders. Z-6 Nit: add claim type to SWEEP (duplicate/dead/idle/inconsistent/unverified/security/ops); every checklist hunt needs a home; fix plan, exceptions, claims check inside SWEEP.md; ledger rows as patch file. Z-7 Nit: wording of stop rules ("review, resolve, repeat up to 3"); agents at once "5".
Also: add preamble line + MUST-NOT list, register-before-start, 10-minute status block, FINAL block. Lead must run one directory listing and give lanes real file lists; 660 KB REPORT read in slices.
## implementation-readiness: 5 Blocker, 7 Major, 4 Nit
B1 no per-lane manifest or coverage rule (READ / SKIMMED / NOT-READ, chunking >2000 lines, what to write at minute 60).
B2 lanes not partition: gaps (demo3 FREEZE, WINDOWS-RUN-1, questions-for-lead, MATRIX-1 name; handover top files; demo/semgrep-pr-diff-lead.patch; repo-root files; .claude; desk/portal docs; system-map own files) and overlaps (L1/L4, L2/L3). Need exact path lists + remainder rule + union check.
B3 lane output template undefined (columns, id scheme L<n>-<kind>-<nnn>, job keys, define filter/counter/notice, checkpoint note path).
B4 citation checker unspecified (path, citation grammar, match rule, drift, output schema, 4-6 tests).
B5 missing deliverables/process: fix plan, exceptions, claims check, lessons, cut list; ledger; reviewer lenses per area; register/10-min status/preamble+MUST-NOT.
M1 verdict and severity criteria undefined. M2 DECISION baseline not given to lanes; cited sources not in box = NOT VISIBLE. M3 minute-60 end state; sequencing of stages. M4 acceptance checks per output (scripted). M5 cut/archive proposal shape; where the take-repo row lives. M6 secret/personal-data control (file:line and type, never value; scan outputs). M7 tool boundary per lane brief (Read/Grep/Glob + one write path; lead creates work/).
N1 explain jargon (rung, KEEP-CODE). N2 split patches/ and not-visible lines. N3 clarify EGM reviewers = egm:* Agent calls, resolve = Skill. N4 add order time.
