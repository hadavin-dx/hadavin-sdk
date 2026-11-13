# rv18 review: no-demo v2 (narrow guard, optional hygiene, isort, CI job)
Fresh reviewer. Scratch /tmp/work/rv18-1 (clone of hadavin-dx/duplicate-proof-lead-desk-n8n at db54e13, read-only; stack P1v3 + P2v2 + P3v3, then the four nodemo patches; all applied cleanly with git apply). Python 3.13 venv and a 3.12.3 venv, both from requirements-dev.txt with --require-hashes. gitleaks 8.30.1, DPLD_REQUIRE_SCAN=1, files `git add`ed. One pytest at a time. Nothing pushed, no network writes. Studio rules used: R3 (no hardcoding), R6 (failures first), R7 (class-level, mutants), R11 (least privilege: workflow permissions), R19 (one process, stop what I start). The bible/handoff files named in R1 are Windows studio paths that do not exist here: not read.

## FAILURES FIRST

### MAJOR 1: the CI gate can pass when a chunk dies without a summary line (reproduced green)
nodemo.yml keeps only `tail -n 1` of each chunk and ignores pytest's exit code (`| tee ... || true`). It then checks (a) 9 lines, (b) no "failed/error" word, (c) total passed >= 800. A chunk that ends without the pytest summary line is invisible if the other chunks still pass 800.
Measured:
- Real run of the job's test step (driver = the YAML run: block under `bash -e`), extra file tests/test_zz7.py containing `os._exit(0)`, placed so it lands in chunk 8 (the last chunk): `TOTAL {'passed': 884,'failed': 0,'error': 0}`, summaries.txt has 8 summary lines plus an unterminated progress line as the 9th ("ss....ssssss"), job exit 0 = GREEN. Chunk 8 normally holds 60 tests; they were never reported.
- The same crash in a non-last chunk was caught only by accident: the unterminated progress line fuses with the next chunk's line, so the line count is 8. Not by design.
- Extracted gate script fed crafted summary files (exit code of the gate): "no tests ran in 0.01s" in a small chunk -> 0 (green); a progress line `....s....  [ 40%]` as last line -> 0; `!!!! _pytest.outcomes.Exit: ... !!!!` -> 0. A line "1 error in 0.20s" -> 1 (caught); "1 failed" -> 1; empty tail -> 1; 10 lines -> 1.
Cause: the gate trusts any last line and never looks at pytest's return code. Fix (class level): `python -u -m pytest ... | tee chunk.txt; rc=${PIPESTATUS[0]}`; accept a chunk only if rc is 0 and the last line matches `^[0-9]+ .* in [0-9.]+s` (pytest's real summary shape), write `rc` next to it, and make the Python step require exactly 9 well-formed lines. Add `shell: bash` explicitly if pipefail is wanted (see Nit 4).

### MAJOR 2: the narrowness of the guard (the whole point of v2 over v1) has no test and the CI floor does not catch its loss
There is no test of `_present` itself. Mutants of nodemo-fix-v2 measured with the repo's own suite (demo present with DPLD_REQUIRE_DEMO=1 / demo deleted; table in /tmp/work/rv18-1/mut-guard.txt):
| mutant | demo present | demo deleted | killed by the suite? |
|---|---|---|---|
| G1 skip product rows too (drop `startswith`) | 49 passed | 5 passed, 44 skipped, 0 failed | NO: green |
| G2 `demo_gone = True` always | 43 passed, 6 SKIPPED with demo present | same | NO: green (even in lint.yml with DPLD_REQUIRE_DEMO=1) |
| G3 `or` instead of `and` | 43 passed, 6 skipped | 5 passed, 44 skipped | NO: green |
| G7 `.is_file()` on the folder | 43 passed, 6 skipped | same | NO: green |
| G4 never skip | 49 passed | 6 failed | yes |
| G5 wrong folder name | 49 passed | 6 failed | yes |
| G6 prefix without "/" , G8 probe a file instead of folder | equivalent today | equivalent | n/a |
G1 is exactly the v1 hole the earlier reviewer closed; with it the no-demo job still passes: 938-38 = 900 >= 800 (floor is 138 below today's 938). The typo probe (product row misspelled) only fails with G4/G5-type mutants, i.e. it is a one-time measurement, not a regression test. Fix: make `_present(rows, demo_gone: bool | None = None)` and add a test that for both values of demo_gone only `demo_only/...` rows carry a skip mark and only when demo_gone is true; run it against the G1/G2/G3 mutants (they must fail).

## MINOR
1. Floor 800 vs 938 measured (876 without the optional patch): up to 138 (14 %) silently skipped tests still pass; it never tightens as tests are added. Prefer an explicit floor per chunk or floor = measured minus a small margin, updated with the PR that adds tests. Not a hard-coded-file-group problem: chunking is by `git ls-files 'tests/test_*.py'` round robin, so new files are picked up automatically (checked: 83 files, 9 chunks of 9-10; adding 7 files moved them in). Gap: pytest's default also collects `*_test.py`; a future `tests/foo_test.py` would run in the normal suite but in no chunk. No file exists today. Cheap guard: compare `pytest --collect-only -q` file count with the chunked file list.
2. Optional patch mutants O1 (no skip), O2 (_git without helper), O3 (scan test without helper), O5 (wrong REPO), O6 (inverted) are all killed (no-git copy: 5/4/1/8/5 failed). O4 (`.git` must be a directory: a git worktree or submodule has a `.git` FILE and would be skipped wrongly) and O7 (helper also skips for the temp repos the tests build, hiding 2 tests) survive; the patch itself uses `.exists()` (correct) and `cwd == REPO` (correct), but nothing pins either. Nit-level because current code is right.
3. No-git copy: the planted `169.254.169.254` literal is not caught (named skip). Stated trade in the notes; confirmed. In a git copy (demo deleted) and with demo present it fails test_hygiene_scan_public (caught).
4. The notes and evidence say the job's blocks were run under `bash -e -o pipefail`. On GitHub a `run:` without `shell:` uses `bash -e {0}` (no pipefail). I ran with `-e` only: outcome identical (the `|| true` makes it moot), but the evidence driver is not the real shell. Say so, or add `shell: bash`.
5. A leftover `demo_only/__pycache__` (a cut made after running tests, `git rm` leaves untracked files) leaves the folder present: conftest then imports it as a namespace package and fails at collection (ModuleNotFoundError demo_only.fakes). Pre-existing behaviour, loud not silent; CI checkout is fresh so unaffected.
6. The gate passes the printed total only; a test printing a number after pytest's summary (atexit) could fool `tail -n 1`. Contrived (a PR author can edit the workflow anyway); closed by the rc + regex fix in Major 1.

## What I measured and confirmed (the six claims)
1. Row ids identical: `pytest --collect-only` 49 ids vs 49 ids on the stack without/with nodemo-fix-v2, `diff` empty. CONFIRMED.
2. Demo present (DPLD_REQUIRE_DEMO=1): 49 passed. Demo deleted (`git rm` + rm of leftover cache): 43 passed, 6 skipped, 6 named reasons "demo_only/ was removed". CONFIRMED.
3. Typo in a product row path: with demo present 12 failed (my sed hit more rows than the notes' 3; same 12 failed on the stack without the patch); with demo deleted 12 failed, 31 passed, 6 skipped. One demo file moved away while the folder exists: 3 failed. CONFIRMED.
4. No `.git` (demo deleted): hygiene + no_placeholders = 56 passed, 6 skipped (5 + 1 named), 0 failed. CONFIRMED. Planted literal: git copy fails (caught), demo present fails (caught), no-git skipped. CONFIRMED.
5. Ruff: demo deleted without isort patch 27 fixable errors; with it `All checks passed!`, format clean (141 files deleted / 150 present). `ruff check --show-settings` diff: one setting, `isort.known_modules` gains `demo_only => Known(FirstParty)` (3 output lines). CONFIRMED.
6. Gates on the final stack (A, demo present) and B (demo deleted): ruff check/format clean; mypy --platform linux and win32 "no issues in 28 files" in both; bandit -ll Medium 0 / High 0; scripts/check_schema.py ALL PASS in both; except_hierarchy + hygiene + no_placeholders + gitleaks_exceptions + workflow_files_parse = 168 passed (DPLD_REQUIRE_DEMO=1, DPLD_REQUIRE_SCAN=1, gitleaks 8.30.1). CONFIRMED. gitleaks dir scan of the clean tree: no leaks (27 hits only in my __pycache__/.mypy_cache after test runs, same reason lint.yml scans first).

## CI job (nodemo-ci-job.patch)
- YAML: yaml.safe_load OK (keys name, on, permissions, jobs); repo workflow tests 13 passed with the file present; test_workflows_are_pinned_and_limited passes in the job run. actionlint is not installed here (not run).
- Pins/checksum: checkout 3d3c42e5.. v7.0.1 and setup-python 6d4fd22b.. v7.1.0 are byte-identical to lint.yml; gitleaks 8.30.1 sha 551f6fc8.. same as lint.yml; curl flags same. permissions `contents: read`, persist-credentials false, no secrets, no PR text in run steps. OK.
- Triggers: pull_request branches [main] and push [main], same as lint.yml and codeql.yml; sonar.yml runs on every PR (with its own fork `if:`). No shared state or secrets between them; nodemo has no `concurrency` (same as lint). No collision of check names (workflow and job both `no-demo`).
- Full local run of the YAML run: blocks (driver /tmp/work/rv18-1/drv/run_step.py), Python 3.13 and Python 3.12.3: Delete step exit 0, ruff clean, `TOTAL {'passed': 938, 'failed': 0, 'error': 0, 'skipped': 80}` exit 0, 78 s. Chunks: 71, 13, 13, 20, 6, 0 (9 skipped files), 608, 147, 60 passed; chunk 6 alone carries 65 % of the passes, so skipping it is caught by the floor, skipping a small chunk is not.
- `git rm -r -q demo_only` in a CI checkout: sound (index-only deletion, working tree emptied, step then asserts `-e demo_only` false). Does it delete things the product needs? Product code references demo_only only optionally (loader.py has a missing-demo path, tested by test_loader_missing_demo, passing). mypy (both platforms), bandit, check_schema also pass on the deleted tree; the job itself runs only ruff + tests (it does not run mypy/bandit/schema: fine, lint.yml does with demo).
- Shell: `mapfile`, quoting, `${chunk[@]}` fine for paths without spaces; `|| true` on pytest is intentional but is the root of Major 1.
- rv14 findings closed? Major 1 (broad skip): yes, v2 narrow guard measured. Major 2 (hygiene fails without .git): yes, named skip. Minor 1 (27 I001): yes. Minor 2 (no CI job): yes, but see Major 1/2 above (gate weaknesses). Nit 3 (reason text): yes.

## Not checked
A real GitHub runner, actionlint, a real Windows run (Windows safety is by reading: forward-slash strings are used only as text and pathlib joins, `Path(__file__).resolve().parent.parent`, `.exists()`, mypy --platform win32 clean), browser tests (skip), the content of P1/P2/P3 beyond how they interact, EGM steps (lead's), full suite with demo present (not requested; 168 affected tests only).

## Verdict
Guard, optional hygiene and isort: take, but add the guard unit test (Major 2). CI job: do not merge until the gate checks pytest's exit code and the summary-line shape per chunk (Major 1). Head SHA reviewed: db54e13 + stack (local tags stack/nodemo in /tmp/work/rv18-1/A). Processes: all pytest runs finished, none left. Files: /tmp/work/rv18-report.md, /tmp/work/rv18-1/mut-guard.txt, mut-opt.txt, drv/.
