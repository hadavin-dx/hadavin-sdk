# REPORT from core-hardening (newest on top, UTC and IST)

## STATUS 07:59 UTC / 13:29 IST: ORDER 005 task A, ORDER 006 parallel; plan v4 fixed; evidence A1-A3 landed; reviewers running
- Plan round 2 done: 0 Blockers (design 12 Major, readiness 7 Major); all applied as v3/v4 rulings (plan-resolve-2.md). No plan round 3.
- Done: evidence-A1 (17 findings), A2 (8 flows), A3 (patches apply and rebuild). Early facts, unjudged: F-002 and F-008 patches apply cleanly; cumulative rebuild changes saveData settings in all 8 files vs committed (baseline not yet separated).
- Agents running (all sonnet): A2b flow supplement (runner), A3b baseline and pristine patch checks (runner), A4 pair diffs and referrers (runner), R1 egm-codebase-details (citations, spot-check, missed items), R4 egm-comprehension (wording).
- Critical path: A2b+A3b -> R2 egm-design (idempotency, patches vs take); A4 -> R3 egm-zoom-out (cut list, one place per job). Then resolve, REVIEW.md, CORRECTIONS.md, LEDGER-ROWS.md, FINAL, push. Container load low (4 cores, 14 GB free).
- Task B waits for A to be pushed.

## STATUS 07:56 UTC / 13:26 IST: plan round 1 resolved; REVIEW-PLAN v2 written; plan round 2 next
- Plan reviewers P1a (egm-design: 2 Blocker, 10 Major) and P1b (egm-implementation-readiness: 0 Blocker, 6 Major) are CLOSED. Findings saved as plan-review-1a.md, 1b.md. Plan v2 applies them (pinned sha 35235ac, 17 CHECK findings named, patch checks run in a copy, 3 evidence runners that only record, verdict rubric).
- Register: no agent running now. Next: plan round 2 (egm-review-loop), then E1-E3 evidence runners.

## STATUS 07:51 UTC / 13:21 IST: plan review round 1 running
- Register (sonnet, read-only egm reviewers, expected end +15 min): P1a egm-design on REVIEW-PLAN.md; P1b egm-implementation-readiness on REVIEW-PLAN.md. Last check: just started.
- Next: resolve, then E1 evidence runner.

## STATUS 07:51 UTC / 13:21 IST: ORDER 005 task A started (flows-audit cross-review); task B waits for A
- Done: fetched origin/cloud/flows-audit into a scratch copy (git archive, outside the repo); REVIEW-PLAN.md written in reviews-of-flows-audit/.
- Register: (none running yet). Next: P1 plan review (egm-review-loop, sonnet reviewers), then E1 evidence runner, then 4 result reviewers.
- Old register closed: all ORDER 002 agents stopped.

## FINAL 07:34 UTC / 13:04 IST: ORDER 002 part 1 (static architecture audit) written; part 2 not started
FAILURES AND GAPS FIRST
- Nothing was run: no test, no program, no network. Every statement is from reading code; anything needing a runtime is UNVERIFIED.
- About 125 of 150 findings were checked by nobody against the code. Checked: 5 by me, the 6 biggest by a second builder, 16 + 14 by two reviewers (all supported; small fact and line slips fixed).
- NOT-AUDITED parts (lists in AUDIT-FINDINGS.md section 0): for example the secret-pattern table in guard/redact.py. We do not know if those patterns catch what they claim.
- Builders finished in 10-12 min of a 60 min box, so depth differs by lane. Lanes D1 and D2 are condensed re-typed text, not verbatim. Plan v4 rulings were never re-reviewed. The seeded sampler found 0 findings (format mismatch), so spot-checks were chosen by hand.
- The round 2 rewrite was NOT read by a fresh reviewer (cap of 2 result rounds reached). Patches (patches/C-01-and-A-02.patch) pass `git apply --check` and ruff; tests were NOT run.
- No severity was changed. The lead must decide the Blocker set (builders 5; reviewers about 3; list 1 is in force) and 12 questions (section 10).
- Extra verdict words used: FIX-NEEDED, UNVERIFIED. No CRM-COULD-DO assessment was made. Ledger rows use 7 columns, the checklist asks 9: lead, say which.
DELIVERED: MASTER-MAP.md, AUDIT-FINDINGS.md (150 findings, about 120 distinct), patches/, result-review-1a..1d, 2a..2c, result-resolve-1/2.
AGENTS/SHELLS: all agents I started are closed (plan reviewers, evidence runner, 6 lane builders, cross builder, 7 result reviewers); no shells left running.
PART 2 (r7u/r7v hygiene) is NOT started; it needs a new GO. Stopping and waiting.

## STATUS 07:32 UTC / 13:02 IST: round 2 comprehension + codebase-details applied; zoom-out pending
- Done: result-review-2a.md (codebase: 16 of 16 supported, small fact slips fixed in the text), 2c.md (naive reader: summary rewritten, one reconciled list of worst items, question labels, 36-use and line fixes). AUDIT-FINDINGS.md rebuilt (571 lines), banned-string check clean.
- Register: a1ffa3792b4edc893 egm-zoom-out round 2 (sonnet, read-only) running. a6b1ec9d26c8cfa2f and a43eefe25fb9f16f9 closed.
- Next: collect zoom-out, egm-resolve round 2, FINAL block. Hard stop part 1: 09:15 UTC.

## STATUS 07:45 UTC / 13:15 IST: round 1 of result review applied; round 2 running
Failed or weak first: (1) Round 1 reviewers read only parts of the documents (design and zoom-out did not read Parts II to VI; codebase-details read about half). (2) Round 1 found one wrong finding (D1-03, narrowed), 5 wrong line numbers, 7 missing items and wording that a non-engineer could not follow; all applied except two: no hygiene bucket column, and the section 9b items are not judged by a builder. (3) Reviewers proposed 5 severity re-ratings; I did NOT change any lane severity: they are in AUDIT-FINDINGS.md section 2b for the lead. (4) Part IV text for D1-03 is still the builder's original; section 9d overrides it. (5) Plan v4 not re-reviewed.
Delivered so far: MASTER-MAP.md (800 lines), AUDIT-FINDINGS.md (571 lines), patches/C-01-and-A-02.patch (applies with git apply --check; ruff check and format pass on the two files; tests NOT run, so a test fixture with a zero price route could break: UNVERIFIED), patches/ledger-rows.md, result-review-1a..1d.md, result-resolve-1.md.
Register (sonnet, read-only egm reviewers, started 07:40 UTC, expected end 07:55):
- a6b1ec9d26c8cfa2f egm-codebase-details round 2: 16 more findings at file:line | running
- a1ffa3792b4edc893 egm-zoom-out round 2: reads ALL parts, misses and over-claims | running
- a43eefe25fb9f16f9 egm-comprehension round 2: fresh naive read of the top | running
Next: collect, resolve, FINAL block. Hard stop part 1: 09:15 UTC.

## STATUS 07:35 UTC / 13:05 IST: MASTER-MAP.md and AUDIT-FINDINGS.md merged; result review running
Failed or weak first: (1) the seeded sampler returned finding pool=0 (it does not parse the merged AUDIT-FINDINGS format), only the map sample worked (173 ids; picked M-A-13, M-A-19, M-A-25, M-A-39, M-B-17, M-B-28, M-B-36, M-D2-17, M-D2-34, M-D2-89); I chose 14 findings by hand for the reviewer, which is not a seeded random sample. (2) Merged files are concatenations of builder text; lane D1 and D2 are condensed. (3) Still no verdict from any reviewer. (4) Plan v4 not re-reviewed.
Register (all sonnet, read-only egm reviewers, started about 07:34 UTC, expected end about 07:50 UTC):
- a897cb99650866572 egm-codebase-details: spot-check 14 findings and 10 map rows at file:line | running | collect, save as result-review-1a.md
- a73d1e8b6643ed555 egm-zoom-out: what the audit missed | running | save result-review-1b.md
- a4e4513613713fd61 egm-design: fix plan vs rules, choke point | running | save result-review-1c.md
- a265765b029af4dbf egm-comprehension: can a non-engineer read it | running | save result-review-1d.md
Next: collect reviews, egm-resolve (opus via Skill), fix blockers/majors in the two files, patches/, ledger rows, FINAL block. Hard stop part 1: 09:15 UTC.

## STATUS 07:25 UTC / 12:55 IST: all 6 lane builders and the cross-lane pass have reported; merge starting
Failed or weak first: (1) Builders' own Writes were refused for A, B, C, D1, D2, D3, so I saved their returned text (A, B, C, D3 verbatim by script; D1 and D2 re-typed condensed, not verbatim). The cross-lane builder's Write worked. (2) My own audit files contained 3 banned vendor-brand strings (quoted from the repo) which would make the repo guard test fail; I replaced them with "[vendor-inspired name removed]" in findings-D3, claims-D3, handback-D3 (script check: 0 left in handover/core-hardening). (3) Coverage is partial: NOT-AUDITED lists per lane (A redact.py pattern table, B parts of k1b, C parts of tools.py, D2 validate.py rule bodies, D3 almost all of handover/ = 16,308 files). (4) No independent reviewer has read anything yet. Plan v4 rulings were not re-reviewed.
Counts (builder claims, unverified): A 2 Blocker/8 Major/15 Nit; B 1/11/10; C 1/15/10; D1 0/3/9; D2 1/17/6; D3 0/12/13; cross X 0/14/2. The cross builder re-read the code for A-01, A-02, A-03, B-01, C-01, D2-01: all CONFIRMED on the facts (B-01 needs a runtime to know whether tick and agent are one process: UNVERIFIED). It found that lane C's limits.py line numbers are wrong (X-13) and 4 of 17 cites checked were off.
Agents running: none. Closed: all 6 lane builders, cross-lane builder, evidence runner, plan reviewers. Next: merge into MASTER-MAP.md and AUDIT-FINDINGS.md, then result reviewers (codebase-details, zoom-out, design, comprehension; sonnet). Next block about 07:35 UTC. Hard stop for part 1: 09:15 UTC.

## STATUS 07:14 UTC / 12:44 IST: 5 of 6 lane builders reported, cross-lane pass started
Failed or weak first: (1) the harness refused every builder's Write of findings, claims and walk files, so I saved their returned text by script from the transcripts (verbatim, not edited; D2 and D1 I re-typed in condensed form from the message, so those two are NOT verbatim). (2) Builders finished in about 10 to 12 minutes of this box's clock, far under the 60 minute box, and several lists say NOT-AUDITED (A: guard/redact.py lines 40-700 and 890-1050, the whole pattern table, and runmap 240-340; B: parts of k1b; C: parts of tools.py; D2: validate.py rule bodies). Coverage is therefore partial; the NOT-AUDITED lists are the gap. (3) None of the findings has had a reviewer yet. (4) Plan v4 rulings were not re-reviewed.
Counts (builder claims): A 2 Blocker / 8 Major / 15 Nit; B 1 / 11 / 10; C 1 / 15 / 10; D1 0 / 3 / 9; D2 1 / 17 / 6; D3 not yet reported.
My own spot check: I opened the cited code for 5 findings: A-01 (no production caller of the audit outbox reconcile: grep of src finds none), A-02 (G5 leak check named in gate.py:42,63 but no code), B-04 (trigger_ref stored, never read), C-01 (Route prices unchecked; only the replay refuses a zero price), C-09 (config.py:317 still accepts "dev"): all 5 match the builders' quotes. That is 5 of about 150 findings, not a verification of the rest.
Agents running: 2 language-model: lane D3 builder (still writing), cross-lane builder (started 07:14Z, box 30 min, expected end 07:44Z). 0 script lanes.
Register: builder D3 (sonnet) | docs/CI/hooks/root lane | 07:03Z | 08:03Z | running (map-D3 partial: checkpoint and claims files exist) | collect, save text if Write refused. cross-lane builder (sonnet) | parts/cross.md T1-T9 and X- findings | 07:14Z | 07:44Z | running | collect. Closed: builders A, B, C, D1, D2 (reported, files saved).
Next block: 07:24 UTC. Hard stop for part 1: 09:15 UTC.

## STATUS 07:11 UTC / 12:41 IST: builders in progress, lane D2 reported
Failed first: lane D2's Write of findings-D2.md was refused by the harness ("Subagents should return findings as text"); I saved its returned rows to parts/findings-D2.md myself (not edited, not yet spot-checked). Expect the same for other lanes: I will save returned text. D2 reported 24 findings (1 Blocker D2-01: demo `ask` command skips kill switch, meter, audit and ledger although README presents them as controls; 17 Major) and a NOT-AUDITED list (validate.py rule bodies and more). These are the builder's claims; none verified by me or an egm reviewer yet.
Agents running: 5 language-model builders (A, B, C, D1, D3), 0 script lanes. Closed: builder D2 (reported).
Register: builders A, B, C, D1, D3 (sonnet) | lane audits | started 07:03Z | expected end 08:03Z | running (map/checkpoint/walk files appearing in parts/) | collect reports, save findings text if Write refused.
Next block: 07:21 UTC.

## STATUS 07:03 UTC / 12:33 IST: T+3 approx. Evidence done, 6 lane builders running
Failed or weak first (evidence runner's own list, parts/evidence-1.md): registry-string matching resolves only exact names, so short kind names (for example "aws") are listed as candidates only; method-level dead code under-reported; sections 5 and 6 are broad (words like token match plain identifiers); credential, port and external-system rows are not generated and builders must add them; the sampler was only tested on an empty pool. I have NOT yet checked the evidence myself beyond its headline counts (16780 tracked files, 472 in scope, 289 python files parsed, 0 parse failures; 88 of 102 src modules reachable, 14 reached only by tests). The 5 weak points above are builder-visible.
Agents running: 6 language-model builders (lanes A, B, C, D1, D2, D3), 0 script lanes. Each is read-only except its parts/ files.
Register (id | purpose | start | expected end | state | next):
- builder A (sonnet) | security lane + approval-path walk | 07:03Z | 08:03Z | running | read report, check files exist
- builder B (sonnet) | state/runtime lane + agent-loop walk | 07:03Z | 08:03Z | running | same
- builder C (sonnet) | models/top-level lane + llm and k1b walks | 07:03Z | 08:03Z | running | same
- builder D1 (sonnet) | tests lane | 07:03Z | 08:03Z | running | same
- builder D2 (sonnet) | demos vs core lane | 07:03Z | 08:03Z | running | same
- builder D3 (sonnet) | docs/CI/hooks/root files/claims lane | 07:03Z | 08:03Z | running | same
Closed: evidence runner (reported; outputs in parts/).
Next: checkpoint files at +30 min (07:33Z); then cross-lane builder. Next block: 07:13 UTC.

## STATUS 06:55 UTC / 12:25 IST: BUILD START (T+0). ORDER 002 step 2, evidence runner starting
Failed or open first: plan rounds hit the cap of 3 with findings still coming (round 3: 1 Blocker, 17 Major combined); all were written into AUDIT-PLAN.md "Rulings v4" but v4 was NOT re-reviewed by a fresh egm pass (cap reached). Plan took about 45 min, more than I budgeted. Result review will also judge plan fitness. No audit finding exists yet. Hard stop for part 1: T+135 = 09:10 UTC.
Agents running: 1 language-model (evidence runner), 0 script lanes.
Register (id | purpose | start | expected end | state | next):
- EVIDENCE RUNNER (general-purpose, sonnet) | write and run parts/evidence-1.py, save parts/evidence-1.md | 06:55Z | 07:10Z | running | read output, start 6 builders
Closed: round 3 egm-implementation-readiness and egm-design (reported).
Next block: 07:05 UTC.

## STATUS 06:52 UTC / 12:22 IST: ORDER 002, plan review round 3 of max 3 (last)
Failed/open: round 2 found 2 Blocker and 15 Major (plan-review-2.md); all valid and fixed in plan v3 (plan-resolve-1b.md). Not yet known whether v3 is clean. Still no audit finding exists; build has not started (about 30 min spent on plan rounds so far; plan rounds are slower than expected).
Agents running: 2 language-model (round 3 reviewers), 0 script lanes.
Register: egm:egm-implementation-readiness (sonnet), egm:egm-design (sonnet) | round 3 review of plan v3 | 06:52Z | +10 min | running | read, resolve, then start evidence runner. Closed: round 2 readiness and zoom-out (reported).
Next block: 07:02 UTC.

## STATUS 06:50 UTC / 12:20 IST: ORDER 002, plan review round 2 of max 3
Done: round 1 found 6 Blocker and 15 Major (two reviewers, overlapping; plan-review-1.md); all valid; AUDIT-PLAN.md rewritten to v2 (plan-resolve-1.md). Nothing built yet, no audit finding exists yet.
Agents running: 2 language-model (round 2 reviewers), 0 script lanes.
Register (id | purpose | start | expected end | state | next):
- egm:egm-implementation-readiness (sonnet) | round 2 review of plan v2 | 06:50Z | +10 min | running | read, resolve
- egm:egm-zoom-out (sonnet) | round 2 simplicity/scope review of plan v2 | 06:50Z | +10 min | running | read, resolve
- (closed) egm:egm-design, egm:egm-implementation-readiness round 1: reported, closed.
Next block: 07:00 UTC.

## STATUS 06:47 UTC / 12:17 IST: ORDER 002, step 1 plan review (round 1 of max 3)
Done: AUDIT-PLAN.md written (4 lanes A-D, evidence runner, 4 builders, result reviewers). Nothing failed yet. Nothing built yet; no audit finding exists yet.
Agents running: 2 language-model (plan reviewers), 0 script lanes.
Agent register (id | purpose | start | expected end | state | next):
- egm:egm-design (sonnet) | review AUDIT-PLAN.md design | 06:47Z | +10 min | running | read report, resolve
- egm:egm-implementation-readiness (sonnet) | review AUDIT-PLAN.md readiness | 06:47Z | +10 min | running | read report, resolve
Next block: 06:57 UTC.

## ORDER 001 proof: EGM VISIBLE (2026-11-16 06:44 UTC, 12:14 IST)
Status block: agents running 0 language-model agents, 0 script lanes (both reviewers finished). Branch cloud/core-hardening. No secrets, no spend, no live product model calls, no merges, no other branch.

### 1. egm:egm-* skills in my Skill tool (exact names)
egm:egm-bootstrap, egm:egm-brainstorm, egm:egm-draft, egm:egm-drift-report, egm:egm-resolve, egm:egm-review, egm:egm-review-loop

### 2. egm:* agents in my Agent tool (exact names)
egm:egm-bootstrap-orchestrator, egm:egm-codebase-details, egm:egm-comprehension, egm:egm-design, egm:egm-implementation-readiness, egm:egm-inventive-catalyst, egm:egm-structural, egm:egm-style, egm:egm-synthesizer, egm:egm-zoom-out

### 3. Model count
Command: grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c
Output:
```
      6 model: claude-opus-5-5
     64 model: claude-sonnet-5-5
```
Matches the expected 6 opus-5-5 and 64 sonnet-5-5. I did not run the patch script (not needed).

### 4. Dry run
egm:egm-review-loop on a 3-line made-up paragraph, reviewers structural + style (both model sonnet). Saved to handover/core-hardening/egm-dryrun.md. Result: structural 0 Blocker / 0 Major / 4 Nit; style 0 Blocker / 3 Major / 4 Nit. Only round 1; egm-resolve not run, nothing fixed, not converged (dry run proves reviewers work only).

### Not checked / notes
- I read RULE-R456, BRIEF-PREAMBLE (rules 1-21) and MODEL-ROUTING; did not grep the bible (no real work yet, so no R-numbers used).
- The skill's confirm-configuration step was skipped because ORDER 001 gave all inputs.
- The 10-minute status block rule: this was one short run, so one block.
- Now waiting for GO in ORDERS.md.
