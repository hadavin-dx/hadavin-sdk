# fix-patchcopies5: fixer log for patch-copies code round 5 (M1-M3 + Minors) and reader round 1 (M1-M7)
Date 2026-11-16. Fixer session (assistant run). Files edited: `reviews-of-core-patches/patch-copies/README.md`, `reviews-of-core-patches/patch-copies/DEAD-MAN-CHECK.md`, this log. Patch files not changed (no finding needed it). `REVIEW.md` NOT edited. Nothing committed.

## What I did NOT verify (first)
- No database was started: the four-name SQL, PGPASSFILE, `PGSSLMODE=verify-full`, the grants and D5 text are unverified against Postgres (the four-name SQL differs from the earlier tested one only by one deleted `VALUES` entry).
- `perf` tests; ruff and bandit on a copy patched with `C-01.patch` (lint and bandit were run on the default pair only); an empty-`uv`-cache run; ORDER 009 text (not found under `handover/`, so what README says about it is marked UNVERIFIED); the text of system-map "Decision B" (not found).
- Full runs were made in single-commit repositories built from `git archive b4cce5b` (plus `git add -A`), not in clones; the recipe's clone, check, apply and `git add -A` steps were run separately on a clone of the local checkout.
- REVIEW.md still quotes older figures in places (for example "13 new tests" at later lines); a49a0a0 owns it. Its line 64 already says a price-only file exists, so code M3's first half is already fixed there.

## Findings, verified by me, and fixes
| Finding | Verified? | Fix |
|---|---|---|
| code M1 (vendor-name test blind spot) | yes: the test scans untracked files and prints one joined message; the baseline log lists THREE offending files | recipe clause (d2): path-only offender list from both logs, must be non-empty and equal; command run, `(d2) ok` |
| code M2 (clause d vacuous) | yes | clause (d1): grep prints `Left contains 10 more items` in each log; empty string is a failure; run, `(d1) ok` |
| code M3 (REVIEW.md contradicts price-only) | partly: line 64 already fixed; other old counts remain | README "Not checked" says REVIEW.md may quote older figures and that this folder's tables are current |
| code Minor: recipe applied C-01 (+32) while default is price-only (+30) | yes | recipe variable `C=C-01-price-only.patch` default, `C-01.patch` alternative; check loop covers both |
| code Minor: price-only at head not listed | yes: rc 1 | one head table (see below) |
| code Minor: README:10 vs 157-158 contradiction; "104 files" vs "301" | yes | results section rewritten; format scope is whole repository: 299 unpatched, 301 patched |
| code Minor: new files invisible to `git ls-files` guards | yes (patches applied uncommitted) | `git add -A` in the recipe and the proof step |
| code Minor: DEAD-MAN shipped five names | yes | four-name SQL ships; fifth name is one separate add-after-A-01 line |
| code Minor: PGPASSWORD first, no sslmode | yes | PGPASSFILE first, PGPASSWORD second; `PGSSLMODE=verify-full` plus `PGSSLROOTCERT` |
| code Minor: row 3 database-wide REVOKEs in a read-only identity | yes | removed from the identity table (rows renumbered 1-8), moved to separate decision D5, with the Postgres 14 caveat |
| reader M1 (which patch) | yes | status block: default price-only, C-01 alternative, "no applicable A-01 today" until rows 5 and 6 are decided |
| reader M2 (pass rule) | yes | three named verdicts PASSED / ADDS NO NEW FAILURE / NOT PASSED; guard tests defined (99 tests in three named files; the two red ones named); CodeQL, SonarCloud, CodeRabbit dropped from the local rule; one table of expected exit codes; ruff and bandit explicitly in |
| reader M3 (test counts) | yes: C-01 file has 26 cases = 6+1+16+1+2 (two `max_tokens` TESTS, one holding two assertions); the reviewer's 27 and the "three max_tokens cases" were a wording error in README | count table, collected with `pytest --collect-only`: 24/26 in the C-01 file, 6 in the A-01 file, 30/32 total; 12/18 and 13/19 on old code, re-run |
| reader M4 (copy of head) | yes | one section "Which commit these patches fit" with the head result of all three patches |
| reader M5 (dead-man five names) | yes | as above |
| reader M6 (database owner) | yes | words box: migrations login (the login) vs database administrator (the human); bare "owner" and "database owner" removed everywhere |
| reader M7 (references, narrator) | yes | words box rows: I/my, REVIEW.md row ids, Decisions 18/19/23, ORDER 012 path, ORDER 009 (not found, UNVERIFIED), Decision B (not found, meaning stated), BRIEF-PREAMBLE rules 9 and 20; fix-patchcopies1.md path given |
Extra finding of mine: README said two files fail `test_no_vendor_brand_string_is_tracked`; the baseline lists three (the third is `handover/reviews/P1a-idempotence-probe.txt`, "not UTF-8 text"). Corrected. Also "head" was `f05790e42` in the text, real head is `5b5b8933a`; `src/` and `tests/` are identical between them (empty `git diff --stat`), so results hold for both.

## Printed outputs
`git apply --check`, fresh `git archive b4cce5b`: C-01 rc=0, C-01-price-only rc=0, A-01 rc=0.
`git apply --check`, `git archive HEAD` (5b5b8933a): C-01 rc=1 (`error: patch failed: src/hadavin_sdk/config.py:362`), C-01-price-only rc=1 (same), A-01 rc=0.
Recipe literal on a local clone: `check C-01-price-only.patch exit=0`, `check A-01.patch exit=0`, `apply exit=0`, 7 staged paths, both new test files in `git ls-files`.
pytest summary lines (all `-m "not live and not perf"`, `env -i`, `uv run --offline`):
- baseline: `2 failed, 9364 passed, 454 skipped, 26 deselected in 286.64s (0:04:46)`, exit 1
- price-only + A-01: `2 failed, 9394 passed, 454 skipped, 26 deselected in 286.29s (0:04:46)`, exit 1
- C-01 + A-01: `2 failed, 9396 passed, 454 skipped, 26 deselected in 233.17s (0:03:53)`, exit 1
- new tests on old code, price-only: `12 failed, 18 passed in 12.34s`, exit 1; C-01: `13 failed, 19 passed in 6.91s`, exit 1
- collect-only: price-only copy 6 + 24 + 41 (`test_a01`, `test_c01`, `test_p7_tick`); C-01 copy 6 + 26 + 41
Clause checks: failed lists identical (a); `Left contains 10 more items` in all three logs (d1); offenders identical, three paths (d2).
Gates: `ruff check` rc 0 both copies; `ruff format --check` rc 0 (299 files unpatched, 301 patched); `bandit -q -r src demos -ll` rc 0 both (one nosec warning), also rc 0 with `tools`.
From `handover/flows-audit`: `python3 -I tools/check_secrets.py` -> `PASS 0 hits in 2018 files`; `python3 -I tools/check_refs.py` -> `PASS 5176 references`; `ruff format --check .` -> `732 files already formatted`.
