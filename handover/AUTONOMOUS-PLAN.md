# Autonomous plan for the core-modules cloud session (written 2026-11-11 ~14:40Z / 20:10 IST by the lead; the lead is now away)
Purpose: the cloud session works alone on core modules for days (target: a week, restartable at any time). It follows this file, writes every major decision into `handover/AUTONOMOUS-DECISIONS.md`, and logs progress in `handover/AUTONOMOUS-LOG.md`. Prompt to start it: `handover/CLOUD-AUTONOMOUS-PROMPT.md`.

## 1. Rhythm (every day, repeat)
- Start of a work block: Step 0 of the prompt (pull, read state, EGM check, register, log line).
- Work: take the first unblocked item in section 3; start every other unblocked item in parallel (agents are not core-limited; at most 3 heavy test runs at once).
- Every 10 min: HEARTBEAT line; every 30 min and at each package boundary: checkpoint in AUTONOMOUS-LOG.md + commit + push to `core/cloud-handover`.
- 00:00 UTC: `handover/DAILY-<date>.md` (moved / failed / READY with head SHA and evidence path / needs a human / disk and token use).
- If disk is under 8 GB free: clean only your own pushed evidence worktrees and Postgres folders first.

## 2. Definition of READY (what "done" means for a pull request; you never merge unless the prompt says MERGE ALLOWED)
All of: rung table in the PR body (R447/R448/R450); every fix has a test that fails on the old code (proof pasted in the evidence file); independent EVIDENCE agent output saved under `handover/evidence/<pkg>/<sha>/`; fresh `egm:*` reviewers (diff + spec + evidence, no author verdict) report no Blocker/Major on the SAME head; blocker ledger rows FIXED-VERIFIED (`handover/ledger.md`); real GitHub check list green on that exact head (unit tests, ruff check, ruff format --check, bandit -ll, guard tests, CodeQL, SonarCloud, CodeRabbit); `egm:egm-drift-report` clean; STATUS.md line (package, PR, head, evidence, rounds, open rows).
Round caps: money, redaction and security paths: none (repeat until a fresh pass finds nothing real); other paths: 2 fix batches, then only Blockers/Majors get another pass.

## 3. Queue (first unblocked item wins; log any skip with the reason)
Q1 Housekeeping (30 min max): disk, register, worktree list saved, `git worktree repair` before any prune.
Q2 PR89 `core/mutation-runner-keywords`: independent evidence re-run on db0d9eb; fresh reviews; fix; its redaction rows stay open until the `security` CI job clears (that job fails any PR whose history holds `handover/(reviews|tickets|evidence)` paths: the fix is a clean-history branch, see Q6).
Q3 PR77 `core/P2d-1` (redaction): continue from `wip/P2d-1-w6` (b6f3b8dd). Class fix: one gap-tolerant match, not one fix per hiding trick; property/fuzz tests; mutation checks; hostile inputs (tab-run views, one ANSI mode per line, marks, bidi, zero-width, split tokens); uncapped rounds.
Q4 PR74 `core/P5a`: after Q3 is clean: rebase, evidence, fresh reviews (textnorm Major c01 depends on PR77).
Q5 PR85 `core/P5b2`: reviews/evidence valid on bd33cc9. Its base is `core/P5b1`, so GitHub checks never run. Decide (section 4 protocol) how to get real checks: recommended = a NEW branch from main with the same commits rebased, new PR, full checks; never retarget or force the old one.
Q6 PR73 / P3a-2 history: compare `core/P3a-2` and `core/P3a-2-rewritten` (8382bdd: 67 commits, gitleaks clean, no handover review paths); write the memo `handover/decisions/P3a2-history-memo.md`; the recommended choice is implemented only as NEW branches/PRs (e.g. `core/P3a-2-clean`), never a rewrite of an existing remote branch.
Q7 Remaining BULK packages in the order of `handover/studio-notes/plan-v3.md` section 7 (P1, P3a, P2a, P2d, P4d, P4a, P6b, P4b, P4c, P5a, P5b1-P5b5, P5c, P6a), then v1.1 packages (P7a, P7b, P7e, P7h, P4e, P3b, ...) per `handover/CLOUD-PROMPT.md`. Per package: rung table, ticket, fresh plan review (`egm:egm-review-loop` small / `egm:egm-review` big) + `egm:egm-resolve`, ONE builder, EVIDENCE agent, fresh result reviewers, resolve, repeat, drift report.
Q8 If everything is blocked or waiting: hostile-test sweeps and class-level sibling searches on merged modules, mutation runs on modules with weak kill rates, README/runbook accuracy, the `core_sync_check` tool design (core modules must stay identical in all demo repos), dependency audit (single-dependency/lock-in) of every kind module.

## 4. Decision protocol (the owner delegated ALL decisions, including major ones, to you)
You decide yourself; you never wait. For every major decision (architecture, order change, how to fix a history problem, which of two branches to use, scope cuts, tool/library/licence choices, anything a human lead would normally decide):
1. Write an entry in `handover/AUTONOMOUS-DECISIONS.md` BEFORE acting: id (D-NNN), date UTC/IST, the question, 2-3 options with cost, risk and what breaks if wrong, the RECOMMENDED option, why, reversible? (prefer reversible and additive; implement on NEW branches), evidence (file/test/source with date), what would make you revisit it.
2. Choose the recommended option. After acting, update the entry (outcome, link to commit/PR).
3. Where several options are close, pick the one that is safer, more reversible and keeps no-single-dependency and least privilege; say so.
4. Research live (dated sources) before tool/version/licence/price decisions; no GPL/AGPL/SSPL/BUSL/unknown licences in the product; log the licence check.
Owner-safety items are NOT yours to decide, whatever the recommendation: spending money or live model calls; secrets or credentials; merging into `main` (unless the prompt line `MERGE ALLOWED` is present); changing repository, branch-protection, ruleset, environment, visibility or scanning settings; deleting or force-pushing remote branches; rewriting an existing remote branch's history; DNS/deploys; putting demo or client material in this public repo. For these write the question in `handover/questions-for-lead.md` with the safe default you took (the default is always "do nothing irreversible") and continue.

## 5. Honest limits (read these)
- A cloud session can end (context, budget, platform limit). Everything is built so that pasting the prompt again resumes from the files. Never rely on chat memory.
- You cannot see the laptop. Demo work (duplicate-proof-lead-desk) is not your job and its code must never appear in this public repo.
- Subagent reports are unverified until you reproduce a Major yourself.
- Failures first in every report; never say passed/verified without the command and its output.
