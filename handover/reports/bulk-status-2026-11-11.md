# Bulk status table, 2026-11-11 (EVIDENCE RUNNER output: facts only, no judging)

Written by an evidence runner on the cloud machine. origin/main = 2a8c2aac (after `git fetch origin`). Times UTC.

## 0. What I could not check (read first)
- GitHub is not reachable for me. PR numbers and "open / draft / merged" state come from the handover notes only (PARALLEL-PLAN-2026-11-10.md, CLOUD-RESUME-2026-11-11.md). Where a PR number is not named in those files the cell says UNKNOWN. Whether a PR is open, draft or closed is UNKNOWN for every row except where CLOUD-RESUME says "draft" (PR85).
- The ledger (handover/ledger.md, 2549 lines) has no single package column format: 391 open Major/Blocker rows carry labels like "A15 PR74 21ca680", "AK2a", "lookalike" that I did not map to a package. The counts below are only rows whose package cell starts with the package id (or PR number listed). Status words are taken as written; most rows are ticket-review rows still marked OPEN although later rounds may have superseded them. A row count is NOT a count of real open defects.
- P0b, P0d, P0e and the S0 report (`s0-report.md`) are laptop-lead work. No file for them exists in this repo. State: UNKNOWN.
- Ticket file lists in section 3 are paths found in the ticket text by pattern, not branch diffs; they are incomplete.
- I did not run any test. "Evidence" below means a file or folder exists under handover/evidence/, not that it passed.
- `core/P8a` on origin is NOT P8a work: its head 1e4752f2 is the already merged commit "gitleaks: ignore second commit of throwaway test-gateway key hash (#69)". Same name, different thing.

## 1. v1 packages (plan-v3 section 6)
Columns: pushed branch head (git ls-remote) | PR (per notes) | merged into origin/main | ticket | reviews (files/folders named for the package) | evidence (names under handover/evidence/) | open Major/Blocker ledger rows (OPEN or FIXED-UNVERIFIED) | Depends on (plan) | NEXT per start order (section 7), as the notes show it.

| Id | Branch and pushed head | PR | Merged | Ticket | Reviews | Evidence | Ledger M/B open | Depends on | Next action |
|---|---|---|---|---|---|---|---|---|---|
| P0a | core/P0a 977c214fd0c7 (5 ahead of main, 1 file) | PR71 (head then 151d3e1; moved) | no | tickets/P0a.md | 3 | evidence/P0a, P0a-report-note.md | 10 (+3 PR71) | none | S0 step 1; lead item. Review of PR71 head was READY-NOW (A22) |
| P0c | none | none | no | tickets/P0c.md | 1 (round 1 single reviewer) | evidence/P0c | 6 | none | Lead runs it (laptop). State UNKNOWN |
| P0d | none | none | no | none | none | none | 0 | P0c | Lead lane; ORDER 84 says cloud builds none. UNKNOWN |
| P0e | none | none | no | none | none | none | 0 | P0c | Lead lane. UNKNOWN |
| P0b | none | none | no | none | none | none | 0 | P0c, P0d, P0e | Lead lane. UNKNOWN |
| P1 | core/P1a 27ae996bf770 (19 ahead, 32 files); core/P1b e3f946fa5644 (26 ahead); core/P1b-o140 0d843b4183be; core/P1b-fixwip 4bf610e6b2c0 | PR63 (P1a), PR70 (P1b) | no (both) | tickets/P1.md (P1a, P1b have no own ticket file) | 50 | evidence/P1a, P1a-fix1, P1b, P1b-fix1, PR63 | 135 (+3 P1m) | P0e | Step 4. Evidence on new heads then reviews (A8/A7). Merge order is lead's. P1m (mutation runner) is merged on main (#61, #62) |
| P3a | P3a-1 merged (#68). core/P3a-2 ac94d18fb1cf (45 ahead, 237 files); core/P3a-2-rewritten 8382bdd5b0e3 (48 ahead, 29 files); core/P3a-2-wip 7ed4c1043d27 | PR73 (P3a-2) | P3a-1 yes; P3a-2 no | tickets/P3a.md | 39 | evidence/P3a-2, PR73, probes | 86 (+11 PR73) | P0e | Lead decides which branch PR73 uses (CLOUD-RESUME q1); rewritten branch has no review |
| P2a | core/P2a-1 7f323491f919 (11 ahead, 66 files) | PR76 | no | tickets/P2a.md | 35 | evidence/PR76; P2a-*-probes files | 99 (+8 PR76) | P1 | Step 5. Review at head (A10a); fixes wait for PR75 (A10b) |
| P2d | core/P2d-1 76adadb31321 (22 ahead, 34 files); wip/P2d-1-w6 b6f3b8dd0ab8; fix/P2d-1-w7 f25ed5f5be2d (empty WIP commit) | PR77 | no | tickets/P2d.md | 23 | evidence/P2d, P2d-1, P77 | 50 (+1 PR77) | P1 | CLOUD-RESUME: PR77 NOT clean, 6 Majors, resume from wip/P2d-1-w6; redaction path uncapped |
| P4d | core/P4d da08ce2e240f (10 ahead, 13 files); core/P4d-a2 a8abba0f9ca9 (15 ahead, 39 files) | PR66 (P4d), PR75 (P4d-a2) | no | tickets/P4d.md | 38 | evidence/P4d, P4d-a2, PR66, PR75 | 85 | P3a, P0e | Step 5. PR66 first heavy slot (A9); PR75 then |
| P4a | core/P4a 4a0976ffdbda (16 ahead, 74 files) | PR78 | no | tickets/P4a.md | 69 | none under P4a*; PR78 has no evidence folder | 95 (+ "P4a BN-17/18" rows) | P0e, P4d | Queued behind A10b and A6 (fix batch) |
| P6b | P6b1: core/P6b1 8f6b032b2ad0 (21 ahead, 76 files). P6b2: no branch | PR86 (P6b1) | no | tickets/P6b1.md, tickets/P6b2.md | P6b1 11, P6b2 9 | evidence/P6b1, PR86 (P6b1 only) | P6b1 7, P6b2 16 | P4a | P6b1 review queued behind A12 (PR78). P6b2: ticket only, needs P5c, P5b4, P2a-1 |
| P4b | P4b1: core/P4b1 8cc2021f74c8 (14 ahead, 37 files). P4b2: no branch | PR79 (P4b1) | no | tickets/P4b1.md, tickets/P4b2.md | P4b1 13, P4b2 10 | no P4b1 evidence folder; PR79 none | P4b1 21, P4b2 23 | P4a, P4d | P4b1 queued behind PR75 (A13). P4b2 ticket only |
| P4c | none | none | no | tickets/P4c.md | 10 | none | 18 | P4b | Ticket only; its ticket needs P4d, P2a-1, P4a, P4b1 merged first |
| P5a | core/P5a f5231ee26d04 (26 ahead, 43 files); core/P5a-fix1 f09a7f07c307 | PR74 | no | tickets/P5a.md | 19 | evidence/PR74 | 16 (+6 PR74) | P0d, P1 | CLOUD-RESUME: waits for PR77 merge, then rebase, fresh reviews, evidence |
| P5b1 | core/P5b1 400367238cc9 (35 ahead, 77 files) | PR80 | no | tickets/P5b1.md | 16 | evidence/P5b1, PR80 | 12 | P5a | Queued behind PR74 (A16) |
| P5b2 | core/P5b2 bd33cc9ec4b8 (42 ahead, 87 files) | PR85 (draft per CLOUD-RESUME; base is core/P5b1) | no | tickets/P5b2.md | 10 | evidence/P5b2, A17, PR85 | 5 | P5b1 | CLOUD-RESUME: reviews no Major, evidence valid on bd33cc9; lead decides retarget or merge P5b1 first |
| P5b3 | none | none | no | tickets/P5b3.md | 9 | none | 16 | P5b2 | Ticket only (rev 2 per its own text; not clean) |
| P5b4 | none | none | no | tickets/P5b4.md | 9 | none | 16 | P5b3 | Ticket only |
| P5b5 | none | none | no | tickets/P5b5.md | 9 | none | 5 | P5b4 | Ticket only |
| P5c | none (old local heads only: handover-src/c1a-8460813, backup/core/c1a-redactor-kind 8460813d93d2) | none | no | tickets/P5c.md | 9 | none | 24 | P2d, P5b5 | Ticket only; needs PR77 and P5b5 |
| P6a | core/P6a ec76c73900fa (23 ahead, 19 files); core/P6a-wip e6a4220b52bd | PR72 (head 0ae044b at last read; moved) | no | tickets/P6a.md | 19 | evidence/P6a, PR72 | 9 (+2 PR72) | P4b, P5c | Evidence at new head (A14, "partial": 62 hand-mutant script missing, NOT RUN) |
| P8a | no work branch (`core/P8a` = merged commit, see section 0) | none | no | tickets/P8a.md | 9 | none | 17 | every v1 row | Last; step 8 |
| P8b | none | none | no | tickets/P8b.md | 9 | none | 7 | P8a | Step 8 |
| P8c | none | none | no | tickets/P8c.md | 3 | none | 0 | P8a | Step 8 |

## 2. v1.1 packages named in CLOUD-PROMPT.md
None of these has a branch on origin, a ticket in handover/tickets/, a review file or an evidence file (searched by name). Ledger rows: none found by package id. PR: none known. Merged: no.

| Id | What (plan-v3 second table) | Trigger (plan) | Depends | Next action per notes |
|---|---|---|---|---|
| P7a | inbound message ledger, one terminal state for a reused message id | a second consumer | none stated | Not started. AK-G2 ticket mentions it (AK line of work, not a v1.1 build) |
| P7b | tenant namespace, rate cap, read log, loader, test helpers | a second consumer | none stated | Not started. LEAD-ORDERS order 109 says AK1 "absorbs P7b" |
| P7e | money parsing in minor units | refunds or an invoice export | none stated | Not started; mentioned in tickets/P4b1.md |
| P7h | Jagrat/Warden batch A | a consumer names one | none stated | Not started; mentioned in tickets/AK0.md |
| P4e | per-call log sink (JSONL default) | after P4b | P4b | Not started; mentioned in tickets/P4b2.md |
| P3b | PR #49 rebase onto the new base | a client needs signed approvals | P1, P2a, P3a | Not started |
| P2b | egress text check from PR #50 | a second consumer | none stated | Not started |
| P2c | mutation-runner cleanup | before the next mutation-heavy package | none stated | Not started under that id. UNKNOWN whether PR89 (core/mutation-runner-keywords db0d9eb49f16) is meant to cover it: the notes call PR89 "mutation runner keywords", not P2c |

## 3. Next 5 packages that could start now in parallel (ranked)
Reading of "could start now": strictly by the Depends-on column NONE of the remaining v1 packages can start, because none of P1, P3a-2, P2a, P2d, P4d, P4a, P4b1, P5a is merged into origin/main (only P3a-1, P1m and P0t are). The list below is therefore ranked by: ticket exists, the branches it stacks on exist with evidence or reviews, and few shared files. All five stack on unmerged branches; the lead must accept that. File overlap uses paths found in each ticket text (incomplete).

| Rank | Package | Stacks on (branch / PR, state) | Why ranked here | Files (from ticket) | Overlap flags |
|---|---|---|---|---|---|
| 1 | P4b2 | P4d: core/P4d (PR66) and core/P4d-a2 (PR75); evidence exists for both | Only dependency in its ticket is P4d; money path (uncapped) | store/*, store/migrations, runtime/tick.py, tests/contracts/*, test_p7_tick, test_p2_postgres, test_k2_migrations | Overlaps open PR75 and PR73 (migrations) in store files; shares 4 test files with P4c, 2 with P5b3, 3 with P5b5 (incl. src/runtime/tick.py), 4 with P6b2 |
| 2 | P5b3 | P5b2: core/P5b2 (PR85, no open Major per notes); ticket also names P4b1 and P4c as merge-first | Longest redesign chain (P5b3 -> P5b4 -> P5b5) is on the critical path | src/hadavin_sdk/**, tests/data/c18a_*, test_diagnostics_*, test_k5_*, test_llm_text_channels | Shares 7 test files with P4c, 6 with P5b4, 8 with P5b5 (they are serial anyway); 2 with P4b2. Blocked in its own ticket by P4b1 and P4c merging first |
| 3 | P5c | needs P2d (PR77, NOT clean) and P5b5 (no branch) | Redaction kind; old heads exist locally; ticket revised | guard/redactor.py, guard/runmap.py, llm/masked.py, src/intake/mask.py, tests/p5c_*, test_c1* | Shares guard/runmap.py with P5b5; redact.py with PR77/P1d-a. Cannot be built before PR77 and P5b5: ranked third only because its files barely overlap P4b2/P5b3 (1 file each: tests/test_k5_producers.py or test_lockin_guard.py) |
| 4 | P4c | P4d, P2a-1, P4a, P4b1 (all unmerged, all have branches) | Ticket exists; loud-wall alert | limits.py, registry.py, runtime/agent_loop.py, app.py, tests/contracts/test_store_wall_alert*.py | 4 test files shared with P4b2; 7 with P5b3. Needs four unmerged bases |
| 5 | P6b2 | P5c, P5b4, P2a-1 | Ticket exists | backends/table.py, cli.py, config.py, app.py, tests/test_training_lock.py | Hot files (table.py, cli.py, app.py) are shared with P4b2-b, P4c, P5b4, P5c by the ticket's own hot-file order. Cannot start before P5c and P5b4 |

Non-overlapping subset by ticket file lists: P4b2 with P5b3 and P5c (shared files: only test_p2_postgres/test_p7_tick between P4b2 and P5b3, test_lockin_guard between P4b2 and P5c, test_k5_producers between P5b3 and P5c). P4c and P6b2 each overlap P4b2 on 4 files.

Ready now per PARALLEL-PLAN but NOT section 6 rows (listed so the lead sees them): A4 P1d-a build (queued behind PR84, PR89, PR75; files approvals/channel.py, approvals/gate.py, guard/redact.py, guard/runmap.py; overlaps PR77 and P5c), A20 ci-lint-set (ci.yml, pyproject; waits for A24 on ci.yml), A21a T1-T2 tests (tests only).

## 4. Commands used (footer)
- Branch heads and existence: `git ls-remote origin 'refs/heads/*'`
- Merged into main: `git fetch origin -q; git merge-base --is-ancestor origin/core/<x> origin/main` (all "no" except core/P8a); `git branch -r --merged origin/main` lists only origin/claude/busy-brahmagupta-2run0a, origin/core/P8a, origin/main
- Ahead and files: `git rev-list --left-right --count origin/main...origin/core/<x>`; `git diff --name-only origin/main...origin/core/<x> | wc -l`
- What is on main: `git log origin/main --oneline | grep -E 'P[0-9]|#6[0-9]|#[789][0-9]'`
- PR numbers and wave state: handover/PARALLEL-PLAN-2026-11-10.md section 5 and handover/CLOUD-RESUME-2026-11-11.md sections (a)-(e)
- Tickets: `ls handover/tickets`; reviews: `ls handover/reviews` (file/folder count by name prefix); evidence: `ls handover/evidence`
- Ledger counts: a small Python script reading handover/ledger.md rows with 5+ cells, severity (cell 3) starting with major/blocker (any case), status (cell 5) starting OPEN or FIXED-UNVERIFIED, package (cell 2) normalised by prefix P<digits><letter?><digit?> or PR<digits>
- Depends-on, tiers and start order: handover/studio-notes/plan-v3.md sections 6 and 7; v1.1 list: handover/CLOUD-PROMPT.md
- Ticket file lists and hot-file orders: pattern search of paths in handover/tickets/<id>.md; overlaps computed by set intersection
