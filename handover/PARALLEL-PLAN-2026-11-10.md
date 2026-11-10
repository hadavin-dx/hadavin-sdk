# PARALLEL PLAN 2026-11-10 rev 2 (ORDER 231/232; cloud session). EGM plan review round 1 done and resolved (handover/egm/parallel-plan/). FROZEN: no more plan rounds; changes only by lead order.
Why this file is over 250 lines of reading: one row per open core item (30 rows) with the fields the lead asked for. Terms are defined once in section 1.

## 1. Words used (defined once)
- **head**: newest commit of a branch. A report on an older head does not count for the new head.
- **stack**: a pull request whose base is another pull request's branch. It stays DRAFT until its base merges (lead only).
- **lands** (QUEUED-BEHIND x): x's head is stable (no open fix) and its fresh review found nothing real. It does NOT mean merged: only the lead merges, and rows must not wait for a human.
- **heavy run**: full test run, mutant run or Postgres run. 3 at once (4 cores, about 15 GB). Agents are not limited; heavy runs are. Clock estimates are in heavy-slot-hours (hs) beside agent-hours (ah).
- **builder / EVIDENCE RUNNER / reviewer**: the builder changes code; the EVIDENCE RUNNER (general-purpose, brief says so) runs tests and saves raw output and never judges; the reviewer is an `egm:*` agent reading a snapshot, the ticket and the evidence.
- **U (UNCAPPED)**: money, redaction, security or least-privilege path: repeat fresh reviews until one finds nothing real. Others: 2 rounds, then only blockers/majors get another pass.
- **lane**: a group of items that share files or a base. **pulse**: the one-line status in handover/PULSE.md, rewritten every minute. **meter tests**: 4 tests that fail on purpose until P4b1 (PR79). q365/q367: questions to the lead about missing mutant scripts.
- **READY-NOW**: no unmet dependency. **READY-NOW (partial)**: only the parts not blocked. **QUEUED-BEHIND x**: starts when x lands.
- Ladder line (operations plan, nothing is built here): rung 1, reuse the existing runner, queue and EGM tools; no new code.

## 2. Facts not re-read, and moved heads
"What is left" comes from GitHub PR heads read today and the newest reports in handover/; I did NOT open each branch. Before wave 1 one Haiku 5.5 lookup per branch fills the "files touched" column (`git diff --name-only` against base) and the real head; rows are re-labelled if it shows a conflict. Heads that moved since their last evidence: PR63 (bf955e9 -> 27ae996), PR72 (d15e53a -> 0ae044b), PR73 (2b0941b -> c727453), PR75 (f8b9056 -> a8abba0), PR76 (e323ac7 -> 7f32349), PR84 (8a677ad -> 69b69c6). Evidence on the old heads is void. PR70 (e3f946f) unchanged.

## 3. Rules for every row
1. Models (ORDER 232): Opus 5.5 only through the Skill tool (egm-brainstorm, egm-draft, egm-resolve). Builders, fix batches, EVIDENCE RUNNERS, every reviewer: Sonnet 5.5. Plain lookups: Haiku 5.5. Reviewer types are `egm:*` only (egm-design, egm-codebase-details, egm-implementation-readiness, egm-zoom-out, egm-comprehension). Every brief starts with STUDIO-PREAMBLE v1, EGM-GATE v1, CODE-LAST v1. A ticket has a rung table (missing = Major).
2. Every row ends with the same tail: egm:egm-resolve (Skill, Opus 5.5) -> Sonnet 5.5 fix batch -> fresh review on a snapshot (U: repeat until one fresh pass is clean; others: max 2) -> egm:egm-drift-report. The row list below names only what is special.
3. Proof table (agent id, role, subagent_type, model, package, EGM step) is kept in handover/cloud-register.md with a MODEL column; a wrong-model agent is stopped and restarted.
4. Ledger: handover/ledger.md; the cloud session appends rows the same turn as each review; the lead copies to egm/BLOCKER-LEDGER.md. A4 row BL-hadavin-sdk-cilint-001.
5. Restart tolerance (the sandbox restarted 7 times in 7 hours): checkpoint note to handover/checkpoints/<id>.md every 10-15 minutes (done / next / blockers / head SHA); heavy runs in chunks (per Python, per module, per mutant batch) and each finished chunk writes a done-file under /home/user/build/chunks/<id>/ so a restart reruns only the unfinished chunk; after a restart the cloud session reads cloud-register.md and respawns every RUNNING row from its checkpoint note; 60-minute time box = stop, commit, a fresh agent resumes from the note; push every checkpoint.
6. Evidence on a stacked head is marked "void if the base head changes". NOT RUN is never counted as pass; reviewers are told which runs are NOT RUN.
7. Defaults: A1 `noqa: S603` = refused, the code is fixed; A2 FIXTURE ERROR change = reviewed as-is and flagged to the lead (no builder waits for it); missing scripts (q365, q367) = NOT RUN, and the lead is asked again with this default.
8. Round rule for A1 (PR84, already past round 5): only blockers and majors get another pass; minors are fixed in the same push and listed in the ledger.
9. "Files touched" conflicts: CI rows A1, A20, A24 edit `.github/workflows/ci.yml`/`pyproject.toml` and are serialised (A1, then A24, then A20); redaction rows A4, A7, A8, A11 share the text-folding files and are serialised by base (A8, A7, A11, A4).

## 4. Step 0 (before any agent in wave 1; cloud session, 15 minutes)
(a) confirm the queue tool: /home/user/build/heavy.sh (3 flock slots) and pgstart.sh, recreate from CLOUD-RESUME-2026-11-09 if gone; (b) start ONE shared Postgres 16 cluster, UTF8, with a database per builder (not a cluster per builder); the dblink-connect test needs a cluster at /var/run/postgresql port 5432: that one cluster serves dblink runs one at a time, and a dblink failure elsewhere is compared with the base before it counts; (c) pulse watchdog and register rows in place; (d) Haiku lookups for the "files touched" column; (e) write handover/checkpoints/ and /home/user/build/chunks/.

## 5. Items
Columns: id | what is left | depends on (lands rule) | files touched | agent kinds, MODEL | class (U + reason) | est. ah / hs | lead/owner-only | status. Tail of section 3 rule 2 is implied.

| id | what is left | depends on | files touched | agents / MODEL | class | ah / hs | lead/owner | status |
|---|---|---|---|---|---|---|---|---|
| A9 PR66 `core/P4d` da08ce2 | contract harness; evidence + review at head | none | fill in step 0 | EVIDENCE RUNNER Sonnet; egm-design + egm-codebase-details Sonnet | U: money (spend helpers) | 2 / 1 | merge | READY-NOW, wave 1, FIRST heavy slot |
| A7 P1b `core/P1b-fixwip` (0d843b4 at last read) | re-read head; r7 evidence both Pythons; reviews | PR63 for merge only | step 0 | EVIDENCE RUNNER Sonnet; egm-design + egm-codebase-details Sonnet; resolve Opus (Skill) | U: redaction | 4 / 3 | merge | READY-NOW, wave 1 |
| A8 PR63 `core/P1a` 27ae996 + PR70 `core/P1b` e3f946f | both: evidence on new heads; reviews | none | step 0 | EVIDENCE RUNNER; reviewers Sonnet | U: redaction | 3 / 2 | merge order | READY-NOW, wave 1 |
| A3 PR75 `core/P4d-a2` a8abba0 | evidence at a8abba0 (3.12+3.13, Postgres, a1 mutants); round 3 reviews; fixes | PR66 stable for merge; evidence marked "void if A9 head changes" | step 0 | EVIDENCE RUNNER; egm-design + egm-codebase-details + egm-implementation-readiness Sonnet; fix builder Sonnet | U: money (spend reservations) | 4 / 3 | merge | READY-NOW, wave 1, conditional on A9's base |
| A6 P4a plan review (`tickets/P4a.md`, newest revision read at start) | plan review round, resolve | none (plan only) | tickets | egm-review-loop (Skill, Sonnet reviewers), resolve (Skill, Opus) | U: money | 2 / 0 | none | READY-NOW, wave 1 |
| P1d-a-plan: plan review of `tickets/P1d-a.md` (+ P1d rev 5/11 reports) | egm-design + egm-implementation-readiness on the ticket, resolve; rung table check | none | tickets | egm-review-loop (Skill, Sonnet), resolve (Skill, Opus) | U: redaction | 2 / 0 | none | READY-NOW, wave 1 |
| A4 P1d-a build, branch `core/P1d-a` (fresh build; `reports/P1d-a-builder-report.md` read first) | redaction hole in `approvals.channel.clean`; fail-before tests, mutants; BL-hadavin-sdk-cilint-001 | P1d-a-plan lands; P1b head stable (rebase once on the final A7 head; evidence waits for it) | step 0 (expects approvals + text folding files) | builder Sonnet; EVIDENCE RUNNER; reviewers | U: redaction | 5 / 2 | none | QUEUED-BEHIND P1d-a-plan and A7 |
| A1 PR84 `core/ci-evidence` 69b69c6 | round-5 findings 1B/3M; fix batch; evidence; real GitHub check list | none | ci.yml, tools/evidence_step.py | builder Sonnet; EVIDENCE RUNNER; egm-design + egm-codebase-details | not U (CI tooling); round rule 8 | 3 / 1 | owner: noqa (default refused) | READY-NOW, wave 1 (builder) |
| A15 PR74 `core/P5a` 21ca680 | review at head | none | step 0 | egm-design + egm-codebase-details Sonnet | U: redaction exposure of diagnostic text until a reviewer says otherwise | 2 / 1 | merge | READY-NOW, wave 1 (review only; evidence in wave 2) |
| A19 PR83 `core/P0t-followup` 7f24178 | review only (laptop runs its evidence) | none | step 0 | egm-design Sonnet | not U (tests only) | 1 / 0 | laptop evidence | READY-NOW, wave 1 |
| A24 PR91 `core/ci-scan-config-guard` 61cf2be | review at head (kept: it protects the scanners every other PR relies on) | after A1 on ci.yml | ci.yml | egm-design + egm-codebase-details | U: security (scan hygiene) | 1 / 1 | merge | READY-NOW, wave 1 (review only) |
| P8 plan-v4.1 | egm-draft from `studio-notes/plan-v4-1-resolve-round1.md`; 3 fresh reviewers into `reviews/plan-v4-round2/` | none | studio-notes | egm-draft (Skill, Opus 5.5); egm-design + egm-implementation-readiness + egm-comprehension Sonnet | not U | 3 / 0 | owner approval of plan | READY-NOW, wave 1 |
| A2 PR89 `core/mutation-runner-keywords` 6706e67 | real check list; evidence both Pythons; mutants old+new head; reviews | none | tools/mutation runner | EVIDENCE RUNNER; reviewers | not U (test tool) | 2 / 2 | decision on FIXTURE ERROR (default rule 7) | READY-NOW, wave 2 |
| A5 PR73 `core/P3a-2` c727453 | evidence at the new head; reviews | none | migrations | EVIDENCE RUNNER; reviewers | U: migrations touch the money ledger | 3 / 2 | missing 66-mutant script (default NOT RUN) | READY-NOW (partial), wave 2 |
| A14 PR72 `core/P6a` 0ae044b | evidence at the new head; reviews | none | profile/config files | EVIDENCE RUNNER; reviewers | U: least privilege (client profile gate) | 3 / 2 | missing 62 hand-mutant script, gen_evidence (default NOT RUN) | READY-NOW (partial), wave 2 |
| A11a PR77 `core/P2d-1` 8b2b716 evidence+review | review/evidence marked "void if PR63 head changes" | none | text folding files | EVIDENCE RUNNER; reviewers | U: redaction | 2 / 1 | merge after 63 | wave 2 |
| A11b PR77 fixes | fix batch | A8 lands | same | builder Sonnet | U | 2 / 1 | | QUEUED-BEHIND A8 |
| A20 `core/ci-lint-set` (da40870) | batch 2: pyright or mypy, import-linter, actionlint, deptry, vulture; SPDX line each; zero suppressions | after A24 on ci.yml | ci.yml, pyproject | builder Sonnet; EVIDENCE RUNNER; reviewers | not U | 4 / 1 | lead opens draft PR | wave 2 |
| A21a T2 `core/T1-T2-tests` (85b613a) | ledger replay 6 min / 25 h / 31 d, fake clock | none | tests | builder Sonnet | U: money ledger time rules | 2 / 1 | | wave 2 |
| A21b T1 own-meter 50-parallel | real run on the Meter | A13 lands | tests | builder; EVIDENCE RUNNER | U: money (meter) | 2 / 1 | | QUEUED-BEHIND A13 |
| A10a PR76 `core/P2a-1` 7f32349 review | review at head, "void if PR75 head changes" | none | step 0 | egm-design + egm-codebase-details | U: money | 1 / 1 | | wave 2 |
| A10b PR76 fixes | fix batch | A3 lands | | builder | U | 2 / 1 | merge after 75 | QUEUED-BEHIND A3 |
| A12 PR78 `core/P4a` 4a0976f | fix batch | A10b lands and A6 lands | | builder Sonnet | U: money | 3 / 1 | merge after 76 | QUEUED-BEHIND A10b, A6 |
| A13 PR79 `core/P4b1` 8cc2021 | Meter; the 4 meter tests turn green here | A3 lands | | builder; EVIDENCE RUNNER; reviewers | U: money | 3 / 2 | merge after 75 | QUEUED-BEHIND A3 |
| A16 PR80 `core/P5b1` 4003672 | evidence (carries the dblink fix) | A15 lands | | EVIDENCE RUNNER; reviewers | U (as A15) | 2 / 1 | merge after 74 | QUEUED-BEHIND A15 |
| A17 PR85 `core/P5b2` 4b1b3f9 | review | A16 lands | | reviewers | U (as A15) | 1 / 0 | | QUEUED-BEHIND A16 |
| A18 PR86 `core/P6b1` 8f6b032 | review (laptop runs evidence) | A12 lands | | reviewers | U: model cost caps, stacked on money PR78 | 1 / 0 | laptop evidence | QUEUED-BEHIND A12 |
| A22 PR71 `core/P0a` 151d3e1 | review at head (guard: pglast GPL never reaches src) | none | tests | egm-design | not U | 1 / 0 | merge | READY-NOW, wave 2 |
| A23 ledger rows + ledger check | append findings the same turn; list OPEN blockers | each review | handover/ledger.md | cloud session; Haiku for counts | bookkeeping | 1 / 0 | lead copies to egm/BLOCKER-LEDGER.md | continuous |
| A25 hourly handoff cross-check | compare STATUS.md with reality every hour (STANDING-ORDERS 6f) | none | handover/STATUS.md | Haiku lookup + cloud session | bookkeeping | 0.2 each / 0 | | continuous |
| Not started on purpose | AK-G1/G15/G16 (deferred), AK-G2 (waits for P1b and P4d merge), JG-3 (paused), demo tree edits (ORDER 227/230), old PRs 41, 43, 47, 48, 49, 50 (no instruction) | | | | | | | |

## 6. Waves and clock
Real agent count: builders 6 (A1, A4, A20, A21a, A10b/A12/A11b/A13 later), EVIDENCE RUNNERS about 10, reviewers and plan reviewers about 20, one lookup per branch (Haiku). Not 17 builders.
Wave 1 (start after step 0; about 11 agents, heavy-bound items first): A9 (first heavy slot), A7, A8, A3 (conditional), A6, P1d-a-plan, A1 builder, A15 review, A19, A24 review, P8. Heavy queue order: A9, A7, A8, A3, then A1.
Wave 2 (start as slots free): A5, A14, A2, A11a, A21a, A10a, A22, A20, A15 evidence.
Queued rows start the minute their base lands (checked every pulse).
Heavy-slot clock: wave 1 about 12 hs, wave 2 about 17 hs; at 3 slots about 4 h and 6 h on the clock if no restart wastes a run. Money chain (A9 -> A3 -> A10b -> A12 -> A18, plus A3 -> A13 -> A21b): rows add to 12 ah; the clock depends on how many fix rounds each UNCAPPED review needs, which cannot be predicted; no "8 hours" claim is made.
Critical path: A9 -> A3 -> A10b -> A12 -> A18; A3 -> A13 -> A21b; redaction: A8 -> A7 -> A4.

## 7. Risks
1. Restarts: see section 3 rule 5 (chunks, 10-15 minute checkpoints, respawn from register).
2. RAM about 15 GB: one shared Postgres cluster plus a database per builder; free RAM is read at every pulse; if low, wave 2 waits.
3. Voided evidence on stacked bases and moved heads: marked "void if base changes"; A9 goes first.
4. Missing scripts: NOT RUN, asked again with a default.
5. Shared files: serialisation rule 9.
