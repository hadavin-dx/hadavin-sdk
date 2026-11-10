# PARALLEL PLAN 2026-11-10 (ORDER 231; cloud session; one round of EGM review, then frozen)
Why this file is long: one row per open core item (24 rows), each with the fields the lead asked for. Terms are defined once in section 1.

## 1. Words used (defined once)
- **head**: the newest commit on a branch. A report about an older head does not count for the new head.
- **stack**: a pull request whose base is another pull request's branch (it cannot merge before its base). A stacked PR stays DRAFT until its base merges (lead only).
- **heavy run**: a full test run, mutant run or Postgres run. Only 3 run at once on this machine (4 cores, about 15 GB) through the queue; agents themselves are not limited.
- **builder / evidence runner / reviewer**: the builder changes code; the EVIDENCE RUNNER (general-purpose agent) runs tests and saves raw output and never judges; the reviewer is an `egm:*` agent that reads a snapshot, the ticket and the evidence.
- **UNCAPPED**: money, redaction or security path: repeat fresh reviews until one finds nothing real. Other paths: 2 review rounds.
- **READY-NOW**: no unmet dependency, the agent can start at once. **QUEUED-BEHIND x**: starts the minute x lands.
- **Meter tests**: 4 tests that fail on purpose until P4b1 lands (known; not a bug).

## 2. Facts I did not re-read (honest limits of this plan)
The "what is left" column is built from the pull-request heads read from GitHub at 16:5xZ today and from the newest reports in `handover/` (q-entries, CLOUD-RESUME-2026-11-09, STATUS). I did NOT re-open each branch for this plan; each builder's first step is to read its own branch and write its real list into its checkpoint note. Heads that moved since the last evidence: PR73 (2b0941b -> c727453), PR72 (d15e53a -> 0ae044b), PR63 (bf955e9 -> 27ae996). Evidence on the old heads is void for the new heads.

## 3. Model map (ORDER 232)
Opus 5.5 only through the Skill tool (egm-brainstorm, egm-draft, egm-resolve). Builders, fix batches, evidence runners and all reviewers: Sonnet 5.5 (`claude-sonnet-5-5`). Plain lookups: Haiku 5.5. Every brief starts with the preamble markers STUDIO-PREAMBLE v1, EGM-GATE v1, CODE-LAST v1. Every ticket has a rung table (missing = Major).

## 4. Items
Columns: id | what is left (from reads above) | depends on | lane | agent kind and MODEL | heavy runs | owner/lead-only | est. agent-hours | status. UNCAPPED marked U.

| id | what is left | depends on | lane | agent kind / MODEL | heavy | lead/owner-only | h | status |
|---|---|---|---|---|---|---|---|---|
| A1 PR84 `core/ci-evidence` 69b69c6 | red head: round-5 findings (1B/3M), one `noqa: S603` question, fix batch, independent evidence, round reviewers, real GitHub check list | none | CI | builder Sonnet; evidence runner Sonnet; reviewers egm-design + egm-codebase-details Sonnet | 1 | accept/refuse the `noqa` (owner via lead); merge | 3 | READY-NOW |
| A2 PR89 `core/mutation-runner-keywords` 6706e67 | real check list; independent evidence on both Pythons; mutants at old and new head; fresh reviewers; decision on always-on FIXTURE ERROR | none | tools | evidence runner Sonnet; reviewers Sonnet | 2 | decision (default behaviour change) | 2 | READY-NOW |
| A3 PR75 `core/P4d-a2` a8abba0 U | evidence at a8abba0 (3.12+3.13, Postgres, a1 mutants), round 3 reviewers (money), fixes | base PR66 (core/P4d) for merge only | money | evidence runner Sonnet; reviewers egm-design + egm-codebase-details + egm-implementation-readiness Sonnet; fix builder Sonnet | 3 | merge | 4 | READY-NOW |
| A4 P1d-a build U | redaction hole in `approvals.channel.clean`; ticket `tickets/P1d-a.md` plus P1d rev 5/11 reports; build, fail-before tests, mutants; ledger row BL-hadavin-sdk-cilint-001 | text views of P1a/P1b (builds on `core/P1b-fixwip`) | redaction | builder Sonnet (own branch from P1b-fixwip); evidence runner Sonnet; reviewers Sonnet | 2 | none | 5 | READY-NOW (stacked on P1b-fixwip; rebases if P1b changes) |
| A5 PR73 `core/P3a-2` c727453 | evidence at the NEW head; P3a-2 66-mutant script was missing (ask the lead, q367); fail-before not run; reviewers | none | migrations | evidence runner Sonnet; reviewers Sonnet | 2 | the missing script | 3 | READY-NOW |
| A6 P4a rev 7 (`tickets/P4a.md`) U | plan review round on rev 7 (money), resolve, then PR78 builder pass | PR76 for code (plan review needs none) | money | egm-review-loop (Skill, Sonnet reviewers); egm-resolve (Skill, Opus 5.5) | 0 | none | 2 | READY-NOW (plan only) |
| A7 P1b `core/P1b-fixwip` (0d843b4 at last read) U | head re-read; r7 evidence on both Pythons (last run: 1 env failure dblink); fresh reviewers; resolve | PR63 base for merge | redaction | evidence runner Sonnet; reviewers egm-design + egm-codebase-details Sonnet; resolve Opus (Skill) | 3 | merge | 4 | READY-NOW |
| A8 PR63 `core/P1a` 27ae996 + PR70 `core/P1b` e3f946f U | both heads moved; evidence on new heads; reviewers | none | redaction | evidence runner; reviewers Sonnet | 2 | merge order | 3 | READY-NOW |
| A9 PR66 `core/P4d` da08ce2 U | contract harness; evidence + review at head | none | money | evidence runner; reviewers Sonnet | 1 | merge | 2 | READY-NOW |
| A10 PR76 `core/P2a-1` 7f32349 U | stacked on PR75; review at head | PR75 | money | reviewers Sonnet | 1 | merge after 75 | 2 | QUEUED-BEHIND A3 (review can start on the head now; fixes wait) |
| A11 PR77 `core/P2d-1` 8b2b716 U | stacked on PR63; fold scan for look-alike text | PR63 | redaction | evidence runner; reviewers | 1 | merge after 63 | 2 | READY-NOW for evidence, QUEUED-BEHIND A8 for fixes |
| A12 PR78 `core/P4a` 4a0976f U | stacked on PR76 | PR76 and A6 | money | builder (fix batch) | 1 | merge after 76 | 3 | QUEUED-BEHIND A10, A6 |
| A13 PR79 `core/P4b1` 8cc2021 U | Meter; stacked on PR75; the 4 meter tests turn green here | PR75 | money | builder, evidence, reviewers | 2 | merge after 75 | 3 | QUEUED-BEHIND A3 |
| A14 PR72 `core/P6a` 0ae044b | evidence at the new head; P6a-1 62 hand mutants (script missing); gen_evidence hygiene cell | none | profile | evidence runner; reviewers | 2 | missing scripts | 3 | READY-NOW |
| A15 PR74 `core/P5a` 21ca680 | review at head; diagnostics R1 | none | diagnostics | reviewers | 1 | merge | 2 | READY-NOW |
| A16 PR80 `core/P5b1` 4003672 | stacked on PR74; carries the dblink fix | PR74 | diagnostics | evidence runner; reviewers | 1 | merge after 74 | 2 | QUEUED-BEHIND A15 |
| A17 PR85 `core/P5b2` 4b1b3f9 | stacked on PR80 | PR80 | diagnostics | reviewers | 1 | merge after 80 | 1 | QUEUED-BEHIND A16 |
| A18 PR86 `core/P6b1` 8f6b032 | stacked on PR78; laptop runs its evidence (order 155) | PR78 | llm kind | reviewers | 0 | laptop evidence | 1 | QUEUED-BEHIND A12 |
| A19 PR83 `core/P0t-followup` 7f24178 | laptop runs its evidence (order 155); cloud reviews only | none | tests | reviewers | 0 | laptop evidence | 1 | READY-NOW (review) |
| A20 `core/ci-lint-set` (draft; last head da40870) | batch 2: pyright or mypy, import-linter, actionlint, deptry, vulture; SPDX line per tool; zero suppressions; findings fixed or ledger rows | none | CI | builder Sonnet; evidence runner; reviewers | 1 | lead opens draft PR | 4 | READY-NOW |
| A21 T1/T2 `core/T1-T2-tests` (85b613a) | own-meter 50-parallel test; ledger replay 6 min / 25 h / 31 d with fake clock | the Meter (PR79) for T1 real run | tests | builder Sonnet | 2 | none | 3 | READY-NOW for T2; T1 QUEUED-BEHIND A13 |
| A22 Plan A8 (plan-v4.1) | write from `studio-notes/plan-v4-1-resolve-round1.md`; then 3 fresh reviewers into `reviews/plan-v4-round2/` | none | planning | egm-draft (Skill, Opus 5.5); reviewers egm-design + egm-implementation-readiness + egm-comprehension Sonnet | 0 | owner approval of the plan | 3 | READY-NOW |
| A23 Ledger rows + ledger check | append every finding the same turn; list OPEN blockers | each review | bookkeeping | Haiku for counts; me for rows | 0 | lead writes `egm/BLOCKER-LEDGER.md` | 1 | continuous |
| A24 PR91 `core/ci-scan-config-guard` 61cf2be | review at head | none | CI | reviewers | 1 | merge | 1 | READY-NOW |
| Not started on purpose | AK-G15/G1/G16 (deferred), JG-3 (paused), demo tree edits (ORDER 227/230) | | | | | | | |
| Old PRs 41, 43, 47, 48, 49, 50 | no instruction in orders 230/231; left alone | | | | | | | |

## 5. Critical path
PR66 (A9) -> PR75 (A3) -> PR76 (A10) -> PR78 (A12, needs A6) -> PR86 (A18); PR75 -> PR79 (A13, 4 meter tests green) -> T1 (A21). The money chain is the longest: five reviews in series, each UNCAPPED, about 14 agent-hours but about 8 hours on the clock if evidence and review of later heads run in parallel with fixes of earlier ones. Second path: PR63 -> PR70/P1b -> P1d-a (A4).

## 6. First batch (all READY-NOW, started at once; each its own branch or snapshot, 60-minute time box with a checkpoint note every 30 minutes)
A1, A2, A3, A4, A5, A6, A7, A8, A9, A11 (evidence), A14, A15, A19, A20, A21 (T2), A22, A24. Reviewers wait for their evidence runner only where the order says reviewers read the evidence; otherwise they start at once on the snapshot (rule: reviewer starts in parallel with the evidence runner).
Heavy-run budget: 3 at once. Order in the queue: A3, A7, A8 (UNCAPPED first), then A9, A4, A5, A14, A1, A2, A20, A11, A21, A15, A24.

## 7. Risks
1. The machine restarted 7 times in 7 hours (about every 35-40 minutes while the session was idle). A restart kills agents and the queue. Mitigation: pulse every minute, checkpoint note every 30 minutes, push every checkpoint, rerun only the killed run.
2. RAM: 17 builders plus 3 heavy runs may exceed 15 GB. Mitigation: start agents in two waves (A3, A4, A7, A8, A9 first), watch free memory at each pulse.
3. Agents that read the same worktree: each builder gets its own worktree and Postgres port range (55400 + 10 x item number).
4. Missing scripts (P6a-1 mutants, P3a-2 66 mutants, gen_evidence): asked in q365 and q367; builders list them as NOT RUN, never replace them with a placeholder.
