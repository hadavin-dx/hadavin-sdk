# EGM LEDGER of core-a (rewritten for task A8; replaces the 12:15 IST version)

Sources read: handover/core-a/reviews/*.md (all 47 files), inputs/review-door-1.md (the lead's fresh review of the door), ESCALATIONS.md, DECISIONS.md, OPEN-ITEMS.md, REPORT.md, STATUS-BOARD.md, ANSWERS-1612/1700.md, T1-MERGE.md, DOCS-FOR-C.md, `git log --oneline` and `git rev-parse` of the wip branches (read-only).

**Rules used in this ledger (no review is invented):**
- A "fresh review" counts ONLY if its result file exists under handover/core-a/reviews/ (or the lead's file in inputs/). A board line that says "reviewed fresh" with no file is NOT counted: such an item is **NEEDS REVIEW**.
- Clean round = no Blocker and no Major. Converged = two consecutive clean rounds, as files show. Cap = 3 rounds per item, then ESCALATIONS.md (step E got more rounds by a lead ruling).
- Resolve decisions: FIX = PROPOSE FIX applied, DECLINE = declined with a reason, ESCALATE = sent to the lead or owner, CONTEST = disputed (none in any file: 0 contests).
- `reviews/rev-b-*`, `rev-c-*`, `rev-lead-*`, `xreview-*` (31 files) are core-a's reviews of OTHER lanes' code (core-b, core-c, the lead). They are not reviews of anything core-a built and are not used below.
- There is no per-fix commit. D and E fix rounds sit inside the branch's "code D+E: WIP snapshot ..." commits (15:58 to 17:01Z, head 61044c90a) between the named tested commits; the wip branches carry the single-purpose commits.

## NEEDS REVIEW (no fresh review file exists): 15 items, exact files to review

| # | item | review these files (branch / path) |
|---|---|---|
| 9 | d-fix17 | `src/hadavin_sdk/triggers/server.py`, `worker.py`, `endpoint.py` as changed by d-fix17; tests in `tests/triggers/` (d-fix17 diff is inside WIP snapshots; board says rev-dfix17 "no Blocker, no Major", no file) |
| 10 | d-fix18 (431 header cap, memory store only on demo, G36 mutants) | `src/hadavin_sdk/triggers/server.py`, `worker.py`, `tests/triggers/test_d_fix18_door_fixes.py`, `tests/endpoint_mutants.py` (G36a-h) (board: rev-dfix18-server and rev-dfix18-worker, no files) |
| 11 | d-fix22 (max_running from core-b settings) and d-fix24 (conflict_events_per_minute setting) | `src/hadavin_sdk/triggers/worker.py`, `tests/triggers/test_d_fix22_max_running.py`, `tests/triggers/test_d_fix24_conflict_setting.py`, `handover/core-a/pr/README-trigger-postmerge.md` (board: rev-dfix22, d-fix24 "no Blocker/Major", no files) |
| 16 | README text: `n8n/README-trigger.md` poll section (E-door-1), `requests/002-readme-security-text.md`, `pr/` door sections (B8-text, A4) | `n8n/README-trigger.md`, `handover/core-a/requests/002-readme-security-text.md`, `handover/core-b/requests/from-core-a-B8-text.md` (board: poll section "reviewed fresh", no file) |
| 17 | Crash matrix part 1 | `tests/triggers/test_t5_crash_matrix.py`, `tests/triggers/crash_launcher.py`, `handover/core-a/CRASH-MATRIX.md` (part 1) |
| 18 | Crash matrix part 2 | `tests/triggers/test_t5_crash_matrix_paths.py`, `handover/core-a/CRASH-MATRIX.md` (part 2) |
| 19 | Test support patch 1 (door on the merged tree) | `handover/core-a/pr/door-merged-support.patch`, `handover/core-a/INTEGRATION-DOOR-FIX.md`, branch `wip/core-a-door-merged` (126e4fefc; note the board says that branch is STALE and `cloud/core-a` crash_launcher.py is the right one) |
| 20 | Test support patch 2 (money end state per crash point) | `handover/core-a/pr/door-merged-support-2.patch`, `tests/triggers/crash_money.py` (board: rev-door gave 2 Majors that patch 2 was built to fix; the patch itself has no review file) |
| 21 | contract-fix | branch `wip/core-a-contract-fix` (c545aaef1): `tests/contracts/test_meter.py`, `tests/contracts/test_store_spend_reservations.py` |
| 22 | grant tests | branch `wip/core-a-for-grant-tests` (3ffb442f1): `tests/test_grants_negative_roles.py`; and `wip/core-a-grant-fix2` (c47b08bec): `tests/test_grants_negative_0007.py` (new 'release' role) |
| 23 | T1 merge | branch `wip/core-a-t1-merge` (e4b0c2331): `tests/contracts/test_t1_reserve_cap.py`; write-up `handover/core-a/T1-MERGE.md` |
| 24 | CI python agreement test | branch `wip/core-a-for-ci` (3ed2a8ca9): `tests/test_ci_python_matrix.py` (108 tests, about 900 lines) |
| 25 | docs for core-c | branch `wip/core-a-for-c-docs` (8df581d45): `CHANGELOG.md` lines 114, 120, 139; `handover/core-a/DOCS-FOR-C.md` |
| 26 | PR package | `handover/core-a/pr/PR-DESCRIPTION.md`, `CHANGELOG-lines.md`, `SECURITY-door-section.md`, `README-n8n-queue-mode.md`, `README-trigger-postmerge.md` |
| 27 | this ledger | `handover/core-a/EGM-LEDGER.md` (written by the same session that built the items; a fresh reader should spot-check the table against reviews/) |

## OPEN (reviewed, but NOT converged: a fresh pass on the fixed state is missing): 4 items

| # | item | missing |
|---|---|---|
| 12 | D tests | round 2 on the fixes of D-tests-result-review-1 (fresh file) |
| 13 | tests/endpoint_mutants.py | round 2 on d-fix2's fixes and on G21-G36 added since (lead's run 6, 120 of 120, is evidence, not a review) |
| 14 | testing/crash.py + tests/test_testing_crash.py | file for round 7 (REPORT says "round 7 found no Blocker/Major"; `reviews/E-result-review-7.md` does not exist) |
| 15 | n8n template (2 JSON files + README) | the reviewer outputs of the later rounds (only round 1 is a reviewer file; rounds 2 to 7 in n8n-result-review-1.md are BUILDER fix tables) |

## Ledger (27 items)

Review files are in handover/core-a/reviews/. "r" = round.

| # | item | commit / branch | fresh review file(s): who, round, verdict, open Blocker/Major | resolved? (egm-resolve decisions) | repeat state |
|---|---|---|---|---|---|
| 1 | Door D build: `triggers/endpoint.py`, `worker.py`, `server.py` | tested commits 70feef2c5 (3 review rounds), dfbcdbdd0, 48dc30064, 3b39df08f, 7f24c8c99 (one-write); cloud/core-a | code-D-design-review-1 (egm-design, r0: 0 Blocker, 3 Major, 16 Nit); D-code-result-review-1 (codebase-details, r1: 0 B, 3 M); -2 (r2: 0 B, 1 M ticket text); -3 (zoom-out, r3 = cap: 0 B, 4 M); -4 (extra pass: 0 B, 5 M); lead's fresh review inputs/review-door-1.md (1 Blocker, 6 Major) | design-1: 15 FIX, 3 DECLINE, 3 ESCALATE (resolved by me in the main session, not through the Skill tool). r1: 11 FIX, 2 DECLINE. r2: 8 FIX. r3: 7 FIX, 4 DECLINE, ESCALATE R3-1 to E7: lead said keep the stdlib server (closed). r4: 8 FIX, 1 DECLINE. Lead review: B1 reworded in CRASH-MATRIX.md and ESCALATIONS E-door-1 (guarantee-class: OWNER decision A or B still open, default A); M1, M3, M4, M6 via d-fix18; M2 and M5 text. Open Blocker/Major in files: none unresolved except E-door-1 | cap of 3 passed at r3 (escalated, decided). Converged at the d-fix16 head by E1 r4 + d-fix16 review (two consecutive clean, rows 7 and 8) |
| 2 | d-fix1: DC1-1..DC1-10 (r1 findings) | WIP snapshots after 70feef2c5 | D-code-result-review-1 found them; read again by r2, r3, E1 r4 | see row 1 | converged (inside row 1 sequence) |
| 3 | d-fix2: ORDER 020 rest + test and mutant review fixes (code part) | WIP snapshots; tested 70feef2c5 | D-code-result-review-2 (r2: 0 B, 1 M) | 8 FIX | converged (code); the tests and mutant script parts are rows 12 and 13 |
| 4 | d-fix3: round 2 nits (ConfigError, slot release, WARNING on cap, logger scope) | dfbcdbdd0 (tested, mutants 90 of 90) | D-code-result-review-3 (r3, cap: 0 B, 4 M) | see row 1 | converged (inside row 1 sequence) |
| 5 | d-fix4: round 3 fixes (config text, log time and level, --host '', start/stop lines) | 48dc30064 | D-code-result-review-4 (extra pass: 0 B, 5 M) | 8 FIX, 1 DECLINE | converged (inside row 1 sequence) |
| 6 | d-fix5: R4-1..R4-5 + E-nits | 3b39df08f | read by E1 r1..r4 | see row 7 | converged (inside row 1 sequence) |
| 7 | E1 (conflict audit event with per-sender cap, GET /health, in-process recovery) + d-fix9 (e1-fix2), e1-fix3, e1-fix4 | 3b39df08f; later WIP snapshots | D-code-result-review-5: r1 (0 B, 4 M, 2 test gaps), r2 egm-design (0 B, 1 M arguable), r3 codebase-details (0 B, 1 M arguable, CHURN), r4 zoom-out (0 B, 0 M: "THE E1 REVIEW ENDS") | r1 all FIXED (d-fix9); r2 FIX; r3 resolved by DELETING the fatal-after-5 machinery (churn rule; lead's E1b verdict asks only for /health 503 + counter), 7 DECLINE overall; deletions ranked for the lead | 4 rounds; r4 clean; converged jointly with row 8 (two consecutive clean) |
| 8 | d-fix13/14 (one write per answer), d-fix15/16, FIX-signed_post, S-nits | 7f24c8c99 and later WIP snapshots | D-code-result-review-5 "d-fix16 review" (codebase-details: 0 B, 0 M, 4 nits S-1..S-4) | 4 nits PROPOSE FIX, queued until the lead's mutant run (done: run 6, 120 of 120) | 1 clean round after E1 r4: converged |
| 9 | d-fix17 | WIP snapshots | NONE on disk | n/a | NEEDS REVIEW |
| 10 | d-fix18 (M1 431 cap, M4 memory store demo-only, M6 mutants G36) | WIP snapshots; fixes for inputs/review-door-1 | NONE on disk | the lead's review is the input; its fixes are unreviewed | NEEDS REVIEW |
| 11 | d-fix22 + d-fix24 | WIP snapshots (head 61044c90a) | NONE on disk | n/a | NEEDS REVIEW |
| 12 | D tests (T5 cases, wsgiref, fuzz, crash matrix files as tests, NUL, process, postgres) | cloud/core-a | D-tests-result-review-1 (egm-design r1: 0 B, 6 Major incl. T-5c needing real Windows) | 8 FIX, 1 DECLINE, ESCALATE T-5c to WINDOWS-NOTES.md; fixes queued d-fix2 | 1 of 3 rounds; OPEN. D-code-result-review-4 also hit 5 test gaps (fixed d-fix5). Windows: not run anywhere |
| 13 | `tests/endpoint_mutants.py` | cloud/core-a (lead's run 6: 824b39824, 120 of 120) | D-mutants-result-review-1 (egm-design r1: 1 Blocker verified (G7a anchor), 5 Major) | 9 FIX, 1 DECLINE; anchor and G33d fixed (8d643fca2) | 1 of 3 rounds; OPEN. Runs 17-20 are evidence only |
| 14 | E: `src/hadavin_sdk/testing/crash.py` + `tests/test_testing_crash.py` | 5ff155b46 (MARKER), 3b39df08f | E-result-review-1 (codebase-details + design, r1: 0 B, 5 M); -2 (codebase-details + zoom-out, r2: 0 B, 4 M, CHURN); -3 (r3 = cap: 0 B, 2 M); -4 (extra pass granted by lead E5: 0 B, 0 M, 7 nits); -5 (nits only: 7 nit decisions, no Major listed); -6 (1 Major: Windows directory flag PermissionError, 6 nits) | r1: 9 FIX groups, 5 DECLINE. r2: 6 FIX, 3 DECLINE (delete unused opt-ins). r3: 13 FIX groups, ESCALATE E5 (lead: yes, one more pass, then no cap for shipped helper code). r4: 6 FIX, 1 DECLINE. r5 7 FIX. r6 6 accepted, all fixed | 6 file rounds; r4 and r5 were clean, then r6 found a Major, so the clean count reset. REPORT says r7 clean but no file: OPEN |
| 15 | n8n template (`n8n/hadavin-trigger.json`, `hadavin-trigger-error.json`) | cloud/core-a (lead ran an earlier version in n8n 2.47.7: evidence-n8n-1..4) | n8n-result-review-1 (egm-comprehension + egm-design, r1: 1 Blocker NC-1, 14 Major, 10 Nit) | 19 FIX, 2 DECLINE, 3 ESCALATE; E6 settled by the lead's evidence-n8n-3 | 1 fresh review file; rounds 2 to 7 are builder tables; OPEN. Still UNVERIFIED in n8n: 45 s timeout, 3xx, 502/503/504 with body, 520 to 524, Retry-After, 45 rounds exhausted |
| 16 | README text (n8n README poll section, requests/002, B8-text) | cloud/core-a; requests to core-b | NONE on disk (n8n README was in the target of row 15 r1 only, before the poll section existed) | n/a | NEEDS REVIEW |
| 17 | Crash matrix part 1 (43 kill points on PG16, 39 on memory) | tests committed in 7e8df90e6 / 3b39df08f | NONE on disk (the lead's review-door-1 B1 touched only CRASH-MATRIX.md:99 wording) | n/a | NEEDS REVIEW |
| 18 | Crash matrix part 2 (171 kill points per store; 4 gaps for the plan) | 3b39df08f | NONE on disk (ANSWERS-1612 says "earlier builder + review": no file) | n/a | NEEDS REVIEW |
| 19 | Test support patch 1 (door on merged tree; 144 failed to 1374 passed) | wip/core-a-door-merged 126e4fefc (stale); applied on cloud/core-a | NONE on disk | n/a | NEEDS REVIEW |
| 20 | Test support patch 2 (`crash_money.py`, money end state per crash point) | cloud/core-a (applied 16:58Z) | NONE on disk (rev-door was on patch 1; board 17:35) | n/a | NEEDS REVIEW |
| 21 | contract-fix | wip/core-a-contract-fix c545aaef1 | NONE on disk (board 16:30: "reviewed fresh, no Blocker/Major") | n/a | NEEDS REVIEW |
| 22 | grant tests | wip/core-a-for-grant-tests 3ffb442f1; wip/core-a-grant-fix2 c47b08bec | NONE on disk (board 14:10: "no Blocker/Major"; grant-fix2 unreviewed) | n/a | NEEDS REVIEW |
| 23 | T1 merge | wip/core-a-t1-merge e4b0c2331 (276365373 superseded) | NONE on disk (board: rev-t1 one Major, fixed) | n/a | NEEDS REVIEW |
| 24 | CI python matrix test | wip/core-a-for-ci 3ed2a8ca9 | NONE on disk (board: 3 rounds, last "no Blocker/Major", reviewer says over-built; lead default A = take as is) | n/a | NEEDS REVIEW |
| 25 | docs for core-c | wip/core-a-for-c-docs 8df581d45 | NONE on disk (board: rev-docs-c found one real problem, restored) | n/a | NEEDS REVIEW |
| 26 | PR package | handover/core-a/pr/ | NONE on disk (board: rev-docs) | n/a | NEEDS REVIEW |
| 27 | EGM ledger | handover/core-a/EGM-LEDGER.md | NONE | n/a | NEEDS REVIEW |

## Totals

27 items: 8 converged (1 to 8), 4 open (12, 13, 14, 15), 15 NEEDS REVIEW (9, 10, 11, 16 to 27).
Open escalations tied to these items: E-door-1 (owner: store the cut-off document and notify, A default or B), WINDOWS-NOTES.md (16 rows, nothing run on Windows). No drift report has been run after the last code change (DRIFT-REPORT-2.md items R2-25 to R2-28 were waiting on edits).
Not checked: the full reviewer text behind reviews files (read headers, tables and counts only); the contents of handover/core-b and core-c request files.
