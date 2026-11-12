# RESOLVE-1: resolution of REVIEW-1 on CORE-TO-DEMO.md
Resolver (elephant role). Inputs: REVIEW-1.md, demo clone /tmp/work/ro-clone (initial-code, 43110e7, 202 tracked files), core exports /tmp/work/core-export/core_*, core main read with `git show origin/main:` in /home/user/hadavin-sdk (no checkout, no fetch). Only CORE-TO-DEMO.md was edited; no severity changed; no verdict changed.
Not done: no EGM skill run (lead runs EGM), no R-numbers (studio bible not read), no tests run. Refs are as of the last fetch made by the author; I did not fetch.

## Part 1: findings
| # | Finding | Category | What changed, or why contested |
|---|---|---|---|
| 1 | MAJOR: "117 hits in 53 tracked files" wrong file count | PROPOSE FIX (main point) + CONTEST (two sub-points) | FIXED: 46 files, not 53 (53 = path-rule pairs). Evidence: core's own `_check_suppressions` (core_ci-scan-config-guard/tools/scan_repo.py:43-50, 126-148), loaded and run over `git ls-files` of the demo: 118 hits = 117 marker hits + 1 `.gitleaks.toml`, in 47 files incl. .gitleaks.toml, 54 (path, rule) pairs. Per rule: nosec 11 lines / 7 files, noqa-security 106 lines / 46 files; the 11 nosec lines all also carry noqa (106 distinct lines). Baseline "about 54" made exact. Also FIXED an error the reviewer missed: section 9 said "21 in scripts/run_real_check.py"; only 2 are guard hits (S404 :48, S603 :740), the other 19 are style codes. CONTESTED: "several hits are text about suppressions: tools/hygiene.py (4), tests/test_hygiene.py (7), test_mutants.py, test_mutation_guards.py": checkable with `git grep -nE '(#|//|--|/\*)\s*(noqa|nosec)' -- tools/hygiene.py tests/test_hygiene.py tests/test_mutants.py tests/test_mutation_guards.py`: every hit there is a real `# noqa: S603/S607/S102/S608` on a subprocess, exec or SQL line (e.g. tools/hygiene.py:57-58, test_hygiene.py:136, test_mutants.py:108, test_mutation_guards.py:36). Only tests/test_lead_owner_assignment.py:135 is a string; doc now says so and the verdict reads "116 real suppression comments". CONTESTED: "core's guard would flag all of them depends on the unread regex": regex read and run (above); verified. |
| 2 | MAJOR: "demo REJECTS look-alikes at the door" wrong | PROPOSE FIX | Reviewer is right (identity.py:15, 39-41, 58-71, 78-82, 85-93 read). Section 2 DIFFERS rewritten: rejects only lower-case-to-ASCII characters and control/invisible characters; Cyrillic/Greek look-alikes are accepted and keyed separately. Also corrected my own overreach found while verifying: P1b textnorm.py:62-63 says a dedupe should use `identity_key` equality, so the header does NOT forbid folding a dedupe key; the doc now marks "email must not be folded" as my reading. Verdict NO unchanged (behaviour change either way). |
| 3 | NIT: Python 3.13 vs 3.12; tests-py312 job omitted; pycache weak | PROPOSE FIX | Added: core main ci.yml:102-153 `tests-py312` job; P1b textnorm.py:119 (pilot/prod must run 3.13, 3.12 for demos). "ships __pycache__" changed to "untracked, git-ignored (.gitignore:6) cpython-313 caches in the local clone" (`git ls-files | grep -c pycache` = 0; 11 cpython-313 files on disk). "Not yet required" for tests-py312 not verifiable from files; not added. |
| 4 | NIT: "FOUR files" vs main docstring "two"; line counts unverified | PROPOSE FIX (citation) + CONTEST (substance) | The doc describes PR 89: core_mutation-runner-keywords/tools/mutation_runner.py:24 says "copies FOUR files byte for byte"; main's lines 9-10 say two. Doc now cites both. Line counts VERIFIED: runner 2017 (PR 89) / 586 (main), mutation.py 243 / 107, keywords tests 5862. `conftest=` keyword VERIFIED at runner :79-82. "Not trialled" caveat already in the doc; no further change (not adding context to satisfy). |
| 5 | Say which meter | PROPOSE FIX | Section 7 now names src/hadavin_sdk/meter.py on core/P4b1 and distinguishes demos/ask-your-data/askdata/meter.py on main (a JSON-file meter; its header read). |

## Part 2: scope failure closed (core-branch claims)
Branch state (`git merge-base --is-ancestor origin/core/<b> origin/main`): P1a 27ae996b, P1b e3f946fa, P2d-1 76adadb3, P6a ec76c739, P4a 4a0976ff, P4b1 8cc2021f, P2a-1 7f323491, mutation-runner-keywords 4cc427b5, ci-scan-config-guard 61cf2bea: all unmerged. VERIFIED. PR 90 2742c1bf is an ancestor of origin/main (head 2a8c2aac). VERIFIED.

| Claim | Status | Evidence |
|---|---|---|
| (a) P1a alg fold4, P1b fold5 | VERIFIED | P1a textnorm.py:330 `_ALG = "fold4"`; P1b textnorm.py:50, 65 |
| (a) line counts textnorm 1138 (P1b), 725 (P2d-1), _confusables 871, _scripts 933 (P1b only) | VERIFIED | wc -l on exports |
| (a) P2d-1 carries own textnorm copy plus the redact change | VERIFIED | P2d-1 guard/redact.py and k1b/redaction.py; guard/redact.py imports textnorm (grep) |
| (a) fold steps NFKD/drops/NFKC/digits-dashes-quotes/UTS #39 table; up to 3 spelling variants | VERIFIED | P1b textnorm.py:31-48, 50-58 |
| (a) functions identity_key, identity_keys, could_be_same_person, allow_equal (EQUAL/VARIANT/LOOKALIKE/DIFFERENT), scan_holds, names_equal, has_mixed_script | VERIFIED | P1b textnorm.py:826, 846, 854, 864-877, 891, 1021, 1101 |
| (a) header: fold for DENY, WRONG for ALLOW | VERIFIED | P1b textnorm.py:18-21 |
| (a) "never a unique index, a dedupe or a group-by: use identity_key equality there" | VERIFIED (quote); doc's inference CORRECTED | P1b textnorm.py:61-63, 849; header permits identity_key equality for dedupe |
| (a) identity_key "stable and idempotent ... to keep and to index" | VERIFIED | P1b textnorm.py:828 |
| (a) 3.13 pin, U+E000 tag on other versions | VERIFIED | P1b textnorm.py:117-127, 807-815 |
| (a) imports `hadavin_sdk.defaults`; Unicode License v3 notice; tools/gen_confusables.py + 2 data files | VERIFIED | textnorm.py:228-230; THIRD-PARTY-NOTICES.md:3, 28; tools/data/confusables.txt, Scripts.txt |
| (a) ~2.9k lines source; tests ~5k | VERIFIED 2942; tests CORRECTED to 5615 | wc -l |
| (b) runner/judge stdlib, imports only hadavin_sdk.testing.mutation; verdict list | VERIFIED | runner :310-334; mutation.py:19-31, 37-43 |
| (b) manifest of 4 sha256 | VERIFIED | tests/fixtures/mutation_manifest.json |
| (b) --noconftest + empty ini; conftest keyword; not run on Windows/macOS; mutmut reason | VERIFIED | runner :74-82, :45, :18 |
| (b) branch = PR 89 | VERIFIED | commit subjects "PR89 round 20/22" in origin/main..origin/core/mutation-runner-keywords |
| (c) SUPPRESSIONS rules and config names; path:rule:value:reason list; stale/wrong lines are hits; BANNED read from core test | VERIFIED | scan_repo.py:1-12, 41-64, 100-148 |
| (c) +107 scan_repo, 65-line list, test_scan_repo +152, test_ci_toolpath_step 225, golden, ci.yml +23 | VERIFIED; list INCOMPLETE, added test_ci_gitleaks_scope.py +180 | git diff --stat origin/main...origin/core/ci-scan-config-guard |
| (c) "BASELINE ... taken mechanically ... NOT reviewed one by one" | VERIFIED | scan_suppressions.txt:4-5 |
| (c) core regex flags the demo's markers | VERIFIED by running it | Part 1 item 1 |
| (c) branch = PR 91 | UNVERIFIED | no PR number in the single commit 61cf2bea or CHANGELOG; needs `gh pr view 91` (GraphQL failed earlier) |
| (e) P6a app.py +56, config.py +47, table.py +4, client_profile_mutants.py 1082 | VERIFIED | diffstat |
| (e) build refuses test doubles when is_live unless allow_test_doubles=True, logs names; _LIVE_HOOKS; new keywords fail closed | VERIFIED | P6a app.py:62-67, 72-85, 112-127 |
| (e) made_up_data_only StrictBool; demo naming real services refused without it; pilot/prod setting it refused | VERIFIED | P6a config.py:376, 408-430 |
| (e) three stages | VERIFIED | P6a stages.py:8 |
| (e) demo has no stage model | VERIFIED | `git grep -niE '\b(pilot|prod|production|staging)\b' -- src` in demo: no hit |
| (f) meter.py on P4b1 not P4a; Caps day/month/run; OverBudget, MeterUnavailable; fail closed; no DB import test | VERIFIED | P4b1 meter.py:1-9, 57-104; tests/test_meter_no_db_import.py:1, 21; P4a has no meter.py |
| (f) meter requires the store's 4 methods | VERIFIED | P4b1 meter.py:49-54, 184-186; store/protocol.py:252-281 |
| (f) memory + Postgres stores; migration 0006; 0007 kill switch on P4a | VERIFIED | store/memory.py, postgres.py; P4a store/migrations/0006, 0007 |
| (f) money micro-USD ints | VERIFIED | money.py:1-4, 21-25 |
| (f) "pydantic through config" | CORRECTED to "through models" | meter.py:22-32, models.py:16 |
| (f) "store contract tests need Postgres" | PARTLY VERIFIED | tests/test_meter_processes.py references postgres; full contract suite not read |
| P2a-1 stop_state probe OK/FAILED/INCONCLUSIVE via store.guard_report, named roles | VERIFIED | P2a-1 runtime/stop_state.py:1-13, 27-47 |
| P2a-1 runbook, migration 0007, cli stop/reset, agent_loop and tick wiring | VERIFIED | diffstat origin/main...origin/core/P2a-1; cli.py:5, 98-99 |
| P2a-1 "needs a database with roles" | VERIFIED with nuance added | memory.py:466-470 returns an empty report |

## Open items
- PR 91 = core/ci-scan-config-guard: UNVERIFIED (needs GitHub access).
- PR 89/91 GitHub state (open, reviews): UNVERIFIED; git only shows the branches unmerged.
- Demo-side items the reviewer listed as not checked (live_claude.py, config.py ranges, needs.js:112, desk.py lines, test_mode_safety.py) were out of this brief and not re-checked here, except config.py:420-426, 490-495 and the no-stage grep.
- Processes: only short python/git commands; none left running.
