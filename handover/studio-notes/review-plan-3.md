# Review of plan-v3.md, round 3 of 3 (EGM consolidated)
Target: <studio>/egm\hadavin-sdk\core-complete\plan-v3.md. Date 2026-11-05. Synthesizer: egm-synthesizer. Reviewers (fresh, parallel, read-only): comprehension, design, structural, style, implementation-readiness, codebase-details, then zoom-out last. Per-reviewer files in the same folder: plan3-comprehension.md, plan3-design.md, plan3-structural.md, plan3-style.md, plan3-readiness.md, plan3-codebase.md, plan3-zoom-out.md. The per-reviewer files are the synthesizer's summaries of each reviewer's final report (reviewers are read-only and cannot write).

## VERDICT: FREEZE-WITH-LISTED-AMENDMENTS, on one condition
No blocker-class design flaw remains and v1 is the right size. But 16 small text defects (section C) would mislead or stall a builder as written. Condition: the lead applies MF1-MF16 in one text-only edit pass to plan-v3 as the resolve step (each is a sentence, a blank line or a table row; none changes scope, order or tiers), then freezes. No fourth review round is needed; the lead should re-check the edits against this list. Everything in section D is handled during S0 or by written amendment.
Counts after deduplication: 16 MUST-FIX-BEFORE-FREEZE, about 30 AMENDMENT-LATER, 0 new blockers in the round-2 sense.

## A. Resolution of round-2 items (5 BLOCKER, 22 MAJOR)
| Item | Status in plan-v3 | Open point |
|---|---|---|
| B1 table headers | RESOLVED | one table, header line 87 |
| B2 push/token/protection | RESOLVED in form (rule 9) | new defects MF10, MF11, MF12 |
| B3 cloud review path | RESOLVED (line 52, reviews/ files, handover folder) | none |
| B4 section 9 runnable | PARTLY | MF6, MF7, MF9 |
| B5 ticket template | PARTLY (file exists on core/cloud-handover, line 55 names it) | MF5 |
| M1 stop rule | RESOLVED | lines 19-21, 60-61 |
| M2 P0c thresholds | RESOLVED | 0-conflict-but-suite-fails case is covered by "anything else" (amend) |
| M3 P0b | RESOLVED | line 93 |
| M4 P8a cycle, v1.1 rows | NOT RESOLVED for P8a | MF2 |
| M5 prose under tables | NOT RESOLVED | MF1 (comprehension reviewer said blank lines exist; synthesizer checked lines 144-145, 183-184, 197-198: none) |
| M6 glossary | MOSTLY | MF8; rest D |
| M7 v1 definition | RESOLVED | |
| M8, M9, M10 | RESOLVED | verified in code (section E) |
| M11 money rule | RESOLVED, with defect | MF15 |
| M12 kinds table | RESOLVED | |
| M13, M14, M16, M17, M18 | RESOLVED | |
| M15 rule 9 enforcement | NOT RESOLVED | MF12, MF13 |
| M19, M20 | RESOLVED (explained lead decisions) | zoom-out A1 |
| M21 | RESOLVED | |
| M22 dense cells | MOSTLY | P5b1-P5b5 bare codes: amend (D) |

## B. Structural checks (done by synthesizer and structural reviewer)
Contents match H2s. Every table has header and separator. Section 2 list (25 ids) equals the v1 rows of section 6. All Depends-on ids exist. No cycle except the P8a wording (MF2). Section 7 order respects every edge. Hot-file order P3a, P4d, P4a, P4b matches section 7. Cross-references correct.

## C. MUST-FIX-BEFORE-FREEZE (one edit pass)
MF1. Blank line before prose directly under tables: lines 145-147 (v1.1 notes, course packages, cut order vanish into the table), 184, 198; also after lines 86 and 124. (structural)
MF2. P8a Depends-on (line 111) "all other v1 rows" includes P8b/P8c, which depend on P8a. Write "every v1 row except P8a, P8b, P8c". (structural, comprehension)
MF3. Cut order (line 147) breaks edges: P5c needs P5b5, P4d needs P3a. State that a cut also rewrites the dependents' Depends-on (P4d and the rollback test if P3a is cut; P5c if P5b2-P5b5 are cut) in the same written amendment. (structural, style, design)
MF4. Line 171 "`git stash`-free: run in a throwaway worktree at ce70eb5": delete "git stash-free" and give the command (`git worktree add <dir> ce70eb5`). (style, comprehension, readiness)
MF5. B5 residual: add to the S0 exit (line 117) "TICKET-TEMPLATE.md present on `core/cloud-handover` at commit X, recorded in s0-report.md"; and P0a amends the template or the plan states the mapping: template says "Path class ... Extended review" and "additive migrations", plan says Tier A/B and forward-only; Tier B "template checklist" has no checklist section. (readiness, comprehension)
MF6. proof_pack (lines 31, 113, 182): list the v1 kinds it must run (textnorm, stop_state, meter, redactor, store, diagnostic) and fail if any ran zero times. (readiness)
MF7. `check_core_copies` (line 181): P0e records the path and invocation (exists only in demo snapshots, e.g. tools/check_core_copies.py); P8a copies it into a demo that lacks it (apexc, refunds). (readiness)
MF8. Glossary row: S0-S5 are phases, M = money lane, R = diagnostics lane; section 7 "step" -> "stage". (comprehension)
MF9. Section 9 gaps: add rows for P2d and for rule 9 (a)-(d), (h) (branch protection, token scope, tags, scan job); use the `uv run --all-extras --group test pytest` prefix in every row; "one merge per code row" -> "one merge per PR of each row (N-PR rows have N)"; say P5a creates `tests/test_diagnostics_hostile.py` and later PRs append rows. (comprehension, readiness)
MF10. Rule 9(d) "read-only, no secrets" contradicts rule 6 (CodeQL needs security-events write, SonarCloud needs a token): state the exceptions and which job holds the token; say who edits `.github/workflows` (the cloud token cannot). (design)
MF11. Rule 9(d) "no network for tests" conflicts with Postgres tests and the 8-process race test: reword to "no internet, no real secrets; a local database is allowed". (design)
MF12. Rule 9 (e), (f), (g) have no owning package and no section 9 row; P6a's dev-only refusal depends on (g). Assign (e)-(g) to a package (P0e lists, P6b builds, or P0a), add a done row. Note for the lint ticket: os.environ/getenv is used today in cli.py:80,128,315, audit/signer.py:127, store/postgres.py:54, so the lint needs an allow-list or code changes. (design, comprehension, codebase)
MF13. Secret-read boundary is stated three ways (9e "outside the secrets kind"/"inside the executor package"; P6b "only the executor"; test_secrets_import.py). Pick one. (design)
MF14. Line 198 "at the end only main exists" can destroy unmerged v1.1 sources (#49, #41, #43, #47, rest of #50) and P0a backup branches, and conflicts with line 187. Define "the end" as after v1.1, or after each branch has a ledger disposition or an archive tag. (design)
MF15. Section 8: gate 6 (shared counter with limits.py) and the Postgres part of gate 1 are P4b's own build target, not something #48 or askdata/meter.py pass unchanged: move them to "P4b must achieve", judge candidates on gates 2-5; justify or zero the "one worst-case call" overshoot; note 6 "Reuse askdata/meter.py" -> "the section 8 winner". (design)
MF16. Tier B has no exit after 2 fix batches: add "a surviving major escalates to the lead as in Tier A". P3a carries the migration rule and the downgrade-read test but is Tier B: make it Tier A or give the reason. (design)

## D. AMENDMENT-LATER (handle in S0 or by written amendment)
- Wording: P5b1-P5b5 cells are bare codes (add one plain sentence each); undefined terms (CodeQL, SonarCloud, CodeRabbit, squash, range-diff, hostile corpus, mutant, Dependabot, client profile, consumer, dev_only, REGEX_VERSION, F10, split/retire, CI, UTC, product and demo names); "package" has three meanings; lane/step overloading; "earlier course" vague; IST sentence without times; B/M/m legend; "merges cleanly" vs "clean round"; template says pre-<package>, plan says pre-<P-id>.
- Process: 0-conflict-but-suite-fails verdict in P0c; P0d re-topics old ledger rows to core/...; banned-name list location in a public repo; measurement method for "first measured package"; rule 3 "no round cap" vs "escalate after round 5" wording; stop rule per PR for N-PR rows; hot-file order omits P2a, P4c, P5c (P0e overlap table covers); section 7 step 3 (P0b first) not derivable from Depends-on; `usage` kind outline has no trigger; section 8 scored items have no weights; "previous release code" source for the downgrade test unnamed.
- Scope/cost: record "owner re-confirmed Lane R with cost" after S0; serial Lane R sits in front of P5c/P6a (lead may split or retire); rule 9 heavy for P0a; when EGM is missing in the cloud the lead's laptop review should replace the second cloud round; expect weeks of lead time, not days; copy plan-v3 to `handover/studio-notes/plan-v3.md` at freeze; P4d ticket states the lock-in guard does not scan demo pgsource.py.

## E. Spot-check of factual claims (16 by codebase reviewer; 13 TRUE, 1 TRUE-with-gap, 2 FALSE)
TRUE: psycopg importers (migrate.py:15, postgres.py:23-27, pgsource.py:33; protocol.py and tick.py only name it); AgentRecord.max_run_usd registry.py:45; limits.py:27 "daily_budget" reason string; heavy_slot TOTAL=5 (tools/heavy_slot.py:8,34, studio root); rule 7 reuse files exist; test_lockin_guard.py:67 allow-list; note 5 tests exist; P3b 7-file surface = s0-merge-probe.md:58-65; six hot files exist; ci.yml:17-18 contents: read and a gitleaks job; TICKET-TEMPLATE.md and WORK-PACKAGES.md exist in the handover worktree; pyproject test group so the uv command is valid; CHANGELOG.md has Unreleased.
FALSE: os.environ outside the secrets kind (MF12); handover/studio-notes/plan-v3.md absent (expected until freeze).

## F. Reviewer disagreement
Readiness read P8a "all other v1 rows" as cycle-free; structural and comprehension read it as a cycle. Treated as must-fix because it is a one-phrase change. Comprehension said blank lines precede prose under tables; structural and the synthesizer found none.
