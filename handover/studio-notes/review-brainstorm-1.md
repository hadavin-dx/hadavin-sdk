# Brainstorm review 1: core completion plan (concepts_brief.md)

Mode: BRAINSTORM. Date: 2026-11-05 (UTC). Lenses: design, codebase-details, zoom-out, comprehension, implementation-readiness, structural. Reviewers read the brief, the inventories, the mission and WORK-PACKAGES; none ran code. The codebase reviewer had no shell and checked the local tree (6608146) plus the inventories and `s0-merge-probe.md`. Several reviewers did not read all of inventory-A..D (comprehension skipped B and D; structural skipped A-D detail; readiness grep-read A only). Treat their file-level claims as unverified until S0 re-measures.

Bottom line: the S0-S9 order is workable only after five fixes. (1) The money chain C2/C3/C4a/C17 and about 9 other WP ids are missing from the plan. (2) S1/S2/S3 contradict each other on merge order and money base. (3) There is no "client-ready" stop line, so the plan is a complete-core plan, not a first-client plan. (4) S0 has no procedure or output. (5) Several brief facts are wrong or stale.

## BLOCKER

**B1. WP coverage gap (all six lenses).** C2, C3, C4a, C5, C6, C8, C9, C18b, C1d, C1f and KERNEL-1 appear in no step. The brief names only C17, C18a and C1a/b/c.
Fix: add a matrix of every WP id (C1-C22, KERNEL-1) to an S-step, or "in branch", "moved", "Intake-only" or "deferred with trigger and reason". Put C2 -> C3 -> C4a -> C17 -> C8 inside the money package (S2), because the reserve/settle meter must be designed on the final five-class Usage and Route shapes. Define the id schemes in a glossary (C-ids are WORK-PACKAGES; S-ids are this plan; R-ids are design-v3).

**B2. S1/S2/S3 order is contradictory and merge order conflicts with the inventory.**
- S3 merges #48 first. Inventory-A line 145 gives the conflict-forced order #50, #49 (drop its textnorm, renumber), #48, #43, #41, with C1a after #50. #48-first makes #50/#49 rebase over llm/common, config, extract and migrate.
- S1 rebases #49 onto #50's textnorm, but #50 is unmerged, large, has 8 open majors in round 3 and an unpushed local head.
- S2 picks the money base "from code" while S3 already merges #48.
Fix: make the money-base memo an S0 output (checklist in M3 below). Write one merge-order table, justified from `s0-merge-probe.md`. Split textnorm, confusables and tools/gen_confusables.py out of #50 into a small PR that merges first; #49 then drops its own copy. Fold S1/S2/S3 into ordered sub-steps with one merge target each.

**B3. S0 has no procedure, output, criteria or owner (comprehension, readiness, structural, design).**
Fix: S0 ticket and output file `core-complete/s0-report.md`, one row per branch: true diff size against ce70eb5, conflict files (reuse `s0-merge-probe.md`), test result on a clean throwaway worktree off ce70eb5, CI/Sonar/CodeRabbit state (`gh pr checks`), verdict plus reason. Rules: merge only if clean and tests pass; rebase if few conflicts; split on file collision; retire only with a ledger disposition per open row. S0 agents use read-only network access and never touch live worktrees (pr50b3-wt, core-c18a, core-c1a). S0 ends with a go/no-go table and the first measured estimate. No other step starts before S0 exits. First S0 task: push the unpushed local #50 head (748849c, 6 commits) to a backup branch.

**B4. No "client-ready" definition or stop line (zoom-out).** Every lane ends with "promote more"; S5/S6/S7 have no exit test. Demos also do not import `hadavin_sdk` in src today (byte copies pinned at 6608146), so most promotions change nothing a prospect sees.
Fix: define Core v1 = client-ready in the first paragraph: base moved and PR set merged in order; C1 redaction blocker closed; money chain done (C2, C3, C4a, C17, C8); re-pin, sync check, `ledger_check --topic core` passing; thin proof pack. Everything else is v1.1, started on a named client or second-consumer need, written as a one-page outline with trigger (the no-single-dependency rule allows outline plus trigger). Owner decision needed: v1-first versus full core (the mission says full; recommend v1 first, then the second plan).

**B5. Ledger facts and exit are wrong or undefined.**
- The brief says no ledger rows exist for #41, #43, #47, #48, #49. Inventory-A shows #49 has `BL-demos-refunds-*` (31 rows) and #41 has `k6-egm-review-2026-11-01.md`. No `BL-core-*` rows exist.
- 51 of the 83 open rows are c18a (superseded); the rest are c1a (43 per zoom-out, 27 per structural) and pr50 (19); counts differ across reviewers, so S0 must re-count.
- inventory-A says the ledger check errors; the brief says repaired. A newline-in-row bug broke it.
Fix: S0 re-runs `ledger_check` and records command, output and timestamp. Map existing refunds rows and the k6 review to their PRs. Close c18a rows as SUPERSEDED with pointer to the redesign test, or carry into the redesign list; each retire needs a per-row disposition (carried / obsolete with reason / fixed elsewhere). Re-topic #41/#43/#47/#48/#49 rows as BL-core-* with a .py script. Add a ledger writer/lint that rejects raw newlines. Define "passing" = zero unresolved BLOCKER/MAJOR or an owner waiver.

**B6. Migration numbering is a three-way collision and unresolved.** 0005_evidence is on main (#42); #41 has 0005_measure; #49 has 0005_reservations. The inventory lists no migration number for #50, so the brief's "both use 0005" is unsupported.
Fix: rule: main's numbers never change; migrations renumber in merge order at merge time (e.g. #49 and #41 take next free numbers); each is additive and forward-only; each renumber has a migrate test from the prior head; CI fails on duplicate or out-of-order numbers. Check whether any demo/pilot DB ever ran a branch-numbered 0005.

**B7. Unclean promotion inputs (design B4, readiness).** S5 promotes scan/workqueue/inbox/WP3 from Intake lanes whose own result reviews are open (6b has failing evidence; the same file exists in 5 sizes).
Fix: nothing is promoted from a lane until that lane's result review is closed. Until then S5 covers only clean items (inbox ledger plus terminal-state decision, RateCap, ReadLog, data-source loader, test helpers, tenant namespace). "Clean" = zero open BLOCKER/MAJOR rows for the lane topic.

## MAJOR

**M1. Redaction priority conflict (structural, readiness).** WORK-PACKAGES: C1 and C18a first and "no client use of core until merged". The brief puts redaction at S4 after money/merges. Fix: state the override and why (PR #50 owns redact.py; C1a waits). Run a redaction lane parallel to the money lane, with R1/R1P design check against ce70eb5 starting during S0. Make "C1 merged" a gate for any client use.

**M2. Textnorm base chosen by review rounds, not evidence (design).** Three-plus variants (#49 c1f9a177, #50 576b4cba and 954ae52c, Intake copies). Fix: choose by differential test on the union of all demos' fixtures plus the attack corpus; the base must be a superset. Version the fold (`FOLD_VERSION`, in identity key) because stored identity keys derive from fold output; no client is deployed, so change it now. Pin Unicode data version and test `unicodedata.unidata_version` across the Python matrix. Ship named views (identity key, display, scan) so dealdesk's wrapper and the kit's casefold are deleted. Do not call #50 "reviewed/clean" until its open majors are dispositioned.

**M3. Money design criteria missing (design, readiness, codebase, zoom-out).** Four implementations exist; note `askdata/meter.py` is a demo module that landed with #42, not core. Default bias: #48 (WP C17 names it), checked against R214. Checklist for the selection memo: atomic reservation across processes; integer micro-USD per 1M tokens, rounded up per call; worst-case reserve; UsageMissing settles at worst case; release in finally; expiry sweep; idempotent settle; N-thread race test at the cap; clock-back refusal; one counter shared with `limits.py` budgets (no two spend counters). Memory backend refused in multi-worker/client config. Spend (micro-USD) and business amounts (minor units, exponent table, `allow_negative`) are separate types. Parity tests against Intake `budget.py` on shared fixtures (identical settled amounts, boundary cases). Drop #49's reservations unless refunds is the first client (then this is an S0 decision). One contract suite across store backends (pattern: `tests/contracts/test_store.py`).

**M4. SQLite store kind is a hidden dependency (design).** Intake's budget, workqueue (BEGIN IMMEDIATE, CAS), inbox and rowstore need a durable store; core has Postgres only, so "Intake becomes a consumer" is impossible without it. It is also the cheapest answer to the single-backend gap. Fix: move it from S7 into S2/S3 behind one store-protocol design note (reservations, inbox, queue, tenant namespace) run against memory, sqlite and postgres with the shared contract suite. Also, psycopg is imported in `store/migrate.py`, `store/postgres.py`, `store/protocol.py` and `runtime/tick.py` (codebase reviewer): move dialect behind the store kind; the lock-in guard gap is wider than the inventory states.

**M5. Estimate dishonest (all).** 150-250 agent-hours has no basis; S4 (50-70) is itself unmeasured; there are more than 45 packages each with builder, evidence, two reviewers and uncapped rounds; round 3 of #50 still had 8 majors. Fix: no date and no total until S0 exits. Report per step: package count, builder hours, expected review rounds (3-5 observed on money/redaction), reviewer-slots and wall-clock days. Add a WP table (id, S-step, source branch, depends-on, path class, reviewers, heavy slots, estimate, exit artifact) in `wp-table.md`.

**M6. Scope over-reach vs the plan's own non-goal (design, zoom-out).** No consuming demo for: autonomy levels B3, passkeys B11, edge_auth B12, MCP B15, codec B17, Temporal G1, killswitch framework integrations, Helios, nameindex. Intake uses a passphrase approver. Fix: each promoted module needs one named consumer and a fails-on-old-code test, otherwise an outline with trigger and no code. Cut or defer those items. Keep S6 batch A (new files, many consumers). Keep batch B breaker/limits merge only if the money chain needs it. Batch C (quarantine, vault, webhook/read scope) only if Intake's PII/untrusted path names it. These are uncapped-review packages; each listed separately.

**M7. Four stop/kill designs already exist (design, zoom-out):** `limits.KillSwitch`, #50 `stop_gate.py`, apexc/dealdesk variants, agent-killswitch package. D-killswitch default should be: do not copy the package; absorb needed behaviour (scoped kill, audited reset, breaker) into one stop-state module; PyPI kind only if a client asks. Stop_gate review rows r2-005/007/022 flag restore-without-audit; fix there first.

**M8. Capacity not planned (zoom-out, design, readiness).** Slot count conflicts (brief 5, inventory-B 3; heavy_slot commits suggest it is changing). Fix: confirm in S0, state one WIP limit (suggest at most 2-3 concurrent builders and 2 reviewer pairs; max 2 concurrent money/redaction/security packages). Split #50 into slices (textnorm; stop_gate/rowstore/config_view; testing/mutation; egress_text) so reviews converge. Do not run evidence on worktrees a builder is editing. Schedule S2/S4 away from S0 probes. Use idle time for new-file-only packages (S6 batch A, loader, RateCap, ReadLog, namespace).

**M9. Uncapped rounds have no stop rule (comprehension, readiness).** Fix: stop when two consecutive rounds from independent reviewers have zero new BLOCKER/MAJOR plus lead-run evidence; escalate to the lead after N rounds (propose 5). Uncapped applies to new/changed code, not unchanged code after a rebase. List the uncapped packages by name (money, all of redaction, signed approvals, quarantine/passkeys/vault, canonical JSON). Choose one rule for S6 batch B (uncapped in brief, not in WORK-PACKAGES).

**M10. Rebase invalidates reviews (design, brief risk 2).** Fix: record reviewed sha in every ledger row and evidence file; after rebase review the range-diff plus full evidence re-run; carry a row only if its files are untouched by the conflict set.

**M11. Brief facts wrong or stale (codebase, structural).**
- Rebase conflicts: `s0-merge-probe.md` already measured. #50 (local and pushed) and #47 merge clean; #41 conflicts in 10 files, #43 in 4, #48 in 15, #49 in `store/memory.py` plus 3 tests; C18a-old in config/extract/injection/tick; C1a in CHANGELOG/config/redact/registry. Pushed #50 already contains ce70eb5. Restate facts, cite the probe, narrow S0 to tests/CI/verdict.
- "No redactor kind on main": redact.py and registry exist; only the kind registry lacks a redactor.
- Add a date to each fact (several are pre-ce70eb5).
- PR #50 is no longer simply "promote-apexc"; it carries K5 files already in main.

**M12. Dependabot #51-#56 (all).** Merge green routine bumps once, as a batch, before S0 rebases and before #48 (pyproject/ci edits). State the exemption from review-before-merge for green, non-major bumps; majors (pytest 9, sqlglot 30) need the migration-regex and parser tests rerun. A bump landing mid-rebase forces a probe re-run. Split #48's ci.yml/pyproject edits into a separately reviewed commit.

**M13. Re-pin timing (design, comprehension).** Re-pin only at S8 lets drift accumulate; S1 also says "re-pin early". Fix: one measuring pin to ce70eb5 in S0 (`check_core_copies` once, no commit to live lanes), one real re-pin per demo at S8, never into a worktree a builder edits. Add core version tag and CHANGELOG per merge, and a `core_copies.json` update in every promotion.

**M14. Security / least-privilege gaps.**
- Dev-only kinds (hmac_v0 signer, env secrets, memory meter, fake channel) must be unselectable in a client profile; add a config-validation test.
- No-training lock as a gate in the llm kind before any non-fake call, not a helper.
- Test that only the executor reads the secrets kind.
- Redactor kind has no second backend: name an alternative (NER or judge detector) with trigger, or the rule is broken on the most important security kind.
- S0 agents: read-only network token, no push, no merge; only the lead merges.
- Canonical JSON ASCII form as an option, default unchanged, uncapped review; do it now (no deployed data).
- Refresh Warden before copying (3 merges behind GitHub; redaction PR open). Promote from `reference\warden`, strip names.
- Probe outputs and promotion reports carry no real client data.

**M15. Owner-only decisions scattered.** One table: decision, blocks which step, lead default, rule if unanswered (default applies at S4 start; later change is a replan). D-licence: core `pyproject` says `LicenseRef-Proprietary`; Warden is owner-authored Apache-2.0; reduce the question to confirming no third-party files or NOTICE obligations (one grep, done in S0); third-party parts in reference\ (killswitch, helios, temporal sample) need separate licence checks. D-kit default (separate package) and D-killswitch (M7) as above. Live model calls need the owner's yes with numbers (budget US$189 until 2026-11-23); none in this plan.

**M16. Missing evidence per step.** Each step needs: FAIL-BEFORE test, evidence file `evidence-<n>.md`, mutant summary read by row not pass count. #50 has a failing test and a BAD mutant row: fix before S3.

**M17. Parallel lanes and serial points not named (structural).** Lane R (redaction), Lane M (money plus sqlite store), Lane P (promotions), Lane D (docs and ledger, throughout). Strictly serial: S0, merges into main, re-pin, drift report. Proof pack depends on re-pin.

## MINOR

- m1. Split S8 into S8a (sync check, re-pin) and S8b (docs, drift report, `ledger_check`). Make S9 pass criterion: every kind run on made-up data with fake LLM, no model call, no real names or PII; start a thin proof pack right after v1 merges rather than last.
- m2. Add headings: Success Measures, Rollback, Exit Artifacts, Owner-only Steps, Glossary (EGM, Goldfish, kind, choke point, FAIL-BEFORE, heavy slot, re-pin, sync check, drift report, proof pack, promote, K-ids, R-ids).
- m3. Rollback: tag pre-step main; one PR per package so revert is one commit; keep old branches until the replacement passes; migrations additive so a code revert leaves the schema.
- m4. Define "promote" = rewrite behind core Protocols with names stripped; verbatim copy only with Apache header/NOTICE; `test_lockin_guard` and `test_no_reference_material` stay green.
- m5. "Reuse before new code": check `hashing.py`, `k1b/atomic.py`, `stats.py`, `evals.py`, `store/memory.py` first. Mutation runner: adopt Intake's KILLED/CRASH split, delete duplicate runners, mutant lists stay in demos. Take only `evalcore.py` from the kit, merged with C9.
- m6. S7: outline plus trigger for executor and channel (a second channel such as email is the only likely early demand); code only store sqlite (M4) and the redactor alternative on demand.
- m7. Cheap duplicate deletions (secrets reader, strict_json, time seam, freeze) only when a PR already touches that file.
- m8. Link the brief to plan-v1 (3 review rounds then freeze); add the missing input docs (core-and-portal-v4, core-v5-pilot-kernel, core-only-amendment, core-hardening-1, core-sync-check) to Inputs; use `s0-merge-probe.md`.
- m9. Public API stability (`__all__`, deprecation note) and Python-version matrix not in the plan.
- m10. Name one source branch per promoted capability as a precondition.
- m11. Jagrat incident kinds and WP3 payment checks: ensure not silently dropped; list them as deferred-with-trigger if so.

## Suggested revised order

S0 (backup push; Dependabot batch; measure table; ledger fix; licence grep; measuring pin; money/textnorm memos) -> textnorm slice -> store/meter design note -> #50 slices -> #49 -> meter chain C2/C3/C4a/C17/C8 plus sqlite store -> redaction lane (parallel from S0 on design) -> clean S5 items -> S6 batch A in parallel -> re-pin and sync -> thin proof pack -> v1.1 on demand.

## Questions for the owner

1. v1-first (recommended) or full core in one plan?
2. Confirm the defaults: kit separate package; killswitch absorbed, not copied; no autonomy/passkey/MCP/Temporal now.
